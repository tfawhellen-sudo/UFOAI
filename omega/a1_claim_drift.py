"""A1 claim drift: build the blind coding package and score the coders.

Protocol: omega/reports/assay_protocol_434.md §3.1. Deviations D1-D6:
omega/reports/assay_protocol_434_deviations.md.

  OMEGA_PERIODICALS=<dir of the 860 txt> python3 -I omega/a1_claim_drift.py build <outdir>
      -> <outdir>/coding_items.json (shuffled, masked, random ids; given to coders)
         <outdir>/key.json          (id -> event, R/C, SA1 flag; never given to coders)
  python3 -I omega/a1_claim_drift.py score <outdir> <coderA.json> <coderB.json> [adjudicated.json]

Coder output format: {"<item id>": {"1":0/1, ..., "9":0/1, "10":"0|1|2-5|>5",
"quotes": {"<item>": "..."}}}.
"""
import hashlib
import json
import math
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "omega"))
import provenance_graph_434 as pg  # noqa: E402

SEED = 4340
PRIOR = os.path.join(ROOT, "evidence_vault/03_RETAINED_SAMPLES/priority_434.json")
GRAPH = os.path.join(ROOT, "evidence_vault/07_PERIODICALS_PRIMARY/provenance_graph_434.json")
PHYS = [str(i) for i in range(1, 8)]
ITEMS = [str(i) for i in range(1, 10)]

MASKS = [
    (re.compile(r"\]\((https?://[^)]*)\)"), "]"),                  # markdown link targets
    (re.compile(r"https?://\S+"), " "),
    (re.compile(r"\b(" + "|".join(pg.MONTHS) + r"|" + "|".join(m[:3] for m in pg.MONTHS) + r")\.?\b", re.I), "[MONTH]"),
    (re.compile(r"(?<!\d)(1[89]\d\d|20\d\d)(?!\d)"), "[YEAR]"),
    (re.compile(r"\b(APRO|MUFON|Skylook|IUR|International UFO Reporter|CUFOS|NICAP|A\.P\.R\.O\.|Bulletin|Journal)\b", re.I), "[SOURCE]"),
]


def mask(t):
    for rx, rep in MASKS:
        t = rx.sub(rep, t)
    return re.sub(r"\s+", " ", t).strip()


def earliest_windows(ev, node, issues_dir):
    """All windows in the earliest corroborating issue meeting the rule."""
    f = node["earliest_issue"]
    txt = open(os.path.join(issues_dir, f), encoding="utf-8", errors="replace").read()
    y, m = int(ev["date"][:4]), int(ev["date"][5:7])
    spans = []
    for t in node["tokens"]:
        for mt in pg.tok_rx(t).finditer(txt):
            a, b = max(0, mt.start() - pg.WIN), mt.end() + pg.WIN
            if pg.corroborates(txt[a:b], y, m):
                spans.append((a, b, mt.start(), mt.end()))
    spans.sort()
    merged = []
    for a, b, s, e in spans:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b, s, e])
    full = " … ".join(txt[a:b] for a, b, _, _ in merged)
    a, b, s, e = merged[0]
    c = (s + e) // 2
    sa1 = txt[max(0, c - 200): c + 200]
    return f, full, sa1


def build(outdir):
    pd = os.environ.get("OMEGA_PERIODICALS")
    if not pd:
        sys.exit("set OMEGA_PERIODICALS")
    evs = {e["event_id"]: e for e in json.load(open(PRIOR))["samples"]}
    nodes = [n for n in json.load(open(GRAPH))["nodes"] if n["cls"] in ("ROOTED", "LATE_ONLY")]
    rng = random.Random(SEED)
    items, key = [], {}
    used = set()

    def new_id():
        while True:
            i = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
            if i not in used:
                used.add(i)
                return i

    for n in sorted(nodes, key=lambda n: n["event_id"]):
        ev = evs[n["event_id"]]
        f, full, sa1 = earliest_windows(ev, n, pd)
        for kind, text in (("R", full), ("R_SA1", sa1), ("C", ev.get("description") or "")):
            i = new_id()
            items.append({"id": i, "text": mask(text)})
            key[i] = {"event_id": n["event_id"], "kind": kind, "cls": n["cls"],
                      "issue": f if kind != "C" else None, "lag": n["earliest_lag_months"],
                      "raw_len": len(text)}
    rng.shuffle(items)
    # calibration set: the 20 events with the lowest sha256(event_id + seed)
    ev_ids = sorted({k["event_id"] for k in key.values()},
                    key=lambda e: hashlib.sha256(f"{e}{SEED}".encode()).hexdigest())
    os.makedirs(outdir, exist_ok=True)
    json.dump(items, open(os.path.join(outdir, "coding_items.json"), "w"), ensure_ascii=False, indent=0)
    json.dump({"seed": SEED, "calibration_events": ev_ids[:20], "key": key},
              open(os.path.join(outdir, "key.json"), "w"), indent=1)
    h = hashlib.sha256(open(os.path.join(outdir, "key.json"), "rb").read()).hexdigest()
    print(f"items {len(items)}  events {len(ev_ids)}  key sha256 {h}")


def kappa(x, y):
    n = len(x)
    po = sum(a == b for a, b in zip(x, y)) / n
    p1, p2 = sum(x) / n, sum(y) / n
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def mcnemar_one_sided(b, c):
    n = b + c
    return sum(math.comb(n, k) for k in range(b, n + 1)) / 2**n if n else 1.0


def score(outdir, fa, fb, fadj=None):
    K = json.load(open(os.path.join(outdir, "key.json")))
    key, calib = K["key"], set(K["calibration_events"])
    A, B = json.load(open(fa)), json.load(open(fb))
    adj = json.load(open(fadj)) if fadj else {}
    out = {"n_items": len(key)}

    def val(i, it):
        a, b = int(A[i][it]), int(B[i][it])
        if a == b:
            return a
        return int(adj.get(i, {}).get(it, 0))

    # agreement
    kap = {}
    for it in ITEMS:
        ids = [i for i in key if i in A and i in B]
        kap[it] = round(kappa([int(A[i][it]) for i in ids], [int(B[i][it]) for i in ids]), 3)
    anyA = [int(any(int(A[i][p]) for p in PHYS)) for i in key]
    anyB = [int(any(int(B[i][p]) for p in PHYS)) for i in key]
    out["kappa_items"] = kap
    out["kappa_any_physical_all"] = round(kappa(anyA, anyB), 3)
    cal_ids = [i for i in key if key[i]["event_id"] in calib and key[i]["kind"] in ("R", "C")]
    out["kappa_any_physical_calibration"] = round(kappa(
        [int(any(int(A[i][p]) for p in PHYS)) for i in cal_ids],
        [int(any(int(B[i][p]) for p in PHYS)) for i in cal_ids]), 3)
    out["n_disagree_items"] = sum(int(A[i][it]) != int(B[i][it]) for i in key for it in ITEMS)

    # pairs
    by_ev = {}
    for i, k in key.items():
        by_ev.setdefault(k["event_id"], {})[k["kind"]] = i

    def test(rkind, items, subset=None):
        b = c = conc1 = conc0 = 0
        for e, d in by_ev.items():
            if subset and not subset(key[d["C"]]):
                continue
            r = int(any(val(d[rkind], p) for p in items))
            q = int(any(val(d["C"], p) for p in items))
            if q and not r:
                b += 1
            elif r and not q:
                c += 1
            elif r:
                conc1 += 1
            else:
                conc0 += 1
        return {"n": b + c + conc1 + conc0, "added_b": b, "dropped_c": c, "both": conc1,
                "neither": conc0, "p_one_sided": round(mcnemar_one_sided(b, c), 5)}

    out["H1_primary"] = test("R", PHYS)
    out["SA1_short_root"] = test("R_SA1", PHYS)
    out["S1_by_claim"] = {p: test("R", [p]) for p in PHYS}
    out["S2_by_lag"] = {"lag<=24": test("R", PHYS, lambda k: k["cls"] == "ROOTED"),
                        "lag>24": test("R", PHYS, lambda k: k["cls"] == "LATE_ONLY")}
    out["item9_anomalous_lab_result"] = test("R", ["9"])
    out["coverage_R_any"] = sum(int(any(val(d["R"], p) for p in PHYS)) for d in by_ev.values())
    out["coverage_C_any"] = sum(int(any(val(d["C"], p) for p in PHYS)) for d in by_ev.values())
    out["len_R_median"] = sorted(key[d["R"]]["raw_len"] for d in by_ev.values())[len(by_ev) // 2]
    out["len_C_median"] = sorted(key[d["C"]]["raw_len"] for d in by_ev.values())[len(by_ev) // 2]
    # leave-one-event-out on the primary
    ps = []
    for drop in by_ev:
        keep = {e: d for e, d in by_ev.items() if e != drop}
        b = sum(1 for d in keep.values() if any(val(d["C"], p) for p in PHYS) and not any(val(d["R"], p) for p in PHYS))
        c = sum(1 for d in keep.values() if any(val(d["R"], p) for p in PHYS) and not any(val(d["C"], p) for p in PHYS))
        ps.append(mcnemar_one_sided(b, c))
    out["H1_leave_one_out_max_p"] = round(max(ps), 5)
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(sys.argv[2])
    else:
        score(*sys.argv[2:])
