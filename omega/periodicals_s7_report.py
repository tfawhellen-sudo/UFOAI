#!/usr/bin/env python3
"""Tables for omega/reports/periodicals_expansion_s7.md, generated from the vault
JSON so the write-up and the data cannot drift apart. Prints Markdown to stdout.

Inputs (evidence_vault/07_PERIODICALS_PRIMARY/): provenance_graph_v2.json,
echo_targets_v2.json, provenance_pages.json, corpus_summary_s7.json, and
omega/periodicals_s7/edge_verdicts.json: by-eye verdicts on every ROOTED edge,
both the 43 corpus-A strict roots (cell "A|strict") and every edge that is ROOTED
in A+B|recall but not in A|strict (cell "A+B|recall").

Usage: python3 -I omega/periodicals_s7_report.py > /tmp/tables.md
"""
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "evidence_vault/07_PERIODICALS_PRIMARY")
g = json.load(open(os.path.join(V, "provenance_graph_v2.json")))
echo = json.load(open(os.path.join(V, "echo_targets_v2.json")))["targets"]
pages = {(r["event_id"], r["issue"]): r for r in
         json.load(open(os.path.join(V, "provenance_pages.json")))["rows"]}
corp = json.load(open(os.path.join(V, "corpus_summary_s7.json")))
verd = json.load(open(os.path.join(ROOT, "omega/periodicals_s7/edge_verdicts.json")))
COUNTS_AS_ROOT = {"GENUINE", "GENUINE_DAY"}
ORDER = {"GENUINE": 0, "GENUINE_DAY": 1, "PLAUSIBLE": 2, "DATE_CONFLICT": 3, "COINCIDENCE": 4}
NTEST = sum(o["A|strict"]["cls"] in ("ROOTED", "ABSENT", "LATE_ONLY") for o in g["nodes"])


def pct(x):
    return f"{100 * x:.1f}%"


def v_of(o, cell):
    """the verdict read for this event's edge in this cell, or {}"""
    x = verd.get(o["event_id"], {})
    return x if x.get("cell") == cell else {}


def counts(o):
    """True if the event has a verified contemporaneous root"""
    if o["A|strict"]["cls"] == "ROOTED":
        return v_of(o, "A|strict").get("verdict") in COUNTS_AS_ROOT
    if o["A+B|recall"]["cls"] == "ROOTED":
        x = v_of(o, "A+B|recall")
        return x.get("verdict") in COUNTS_AS_ROOT and "LATE not ROOTED" not in x.get("note", "")
    return False


def a_roots():
    return [o for o in g["nodes"] if o["A|strict"]["cls"] == "ROOTED"]


def new_edges():
    return [o for o in g["nodes"] if o["A+B|recall"]["cls"] == "ROOTED" and o["A|strict"]["cls"] != "ROOTED"]


def unread():
    return [o["event_id"] for o in a_roots() if not v_of(o, "A|strict")] + \
           [o["event_id"] for o in new_edges() if not v_of(o, "A+B|recall")]


def page_cell(eid, c):
    p = pages.get((eid, c["earliest"]), {})
    if p.get("page_status") == "located":
        s = f"[scan {p['scan_page']}/{p['scan_pages']}]({p['viewer']})"
        return s + (f", p.{p['printed_page']}" if p.get("printed_page") else "")
    return p.get("page_status", "n/a")


def summary():
    a, n = a_roots(), new_edges()
    va = Counter(v_of(o, "A|strict").get("verdict", "UNREAD") for o in a)
    vn = Counter(v_of(o, "A+B|recall").get("verdict", "UNREAD") for o in n)
    ok_a = sum(counts(o) for o in a)
    ok_n = sum(counts(o) for o in n)
    return dict(a=len(a), new=len(n), va=dict(va), vn=dict(vn), ok_a=ok_a, ok_n=ok_n,
                total=ok_a + ok_n, ntest=NTEST, unread=unread())


def cells_table():
    print(f"| corpus | rule | issues | ROOTED / {NTEST} | rate | shuffle null (95%) | effect over null (95% CI) | pre-event probe |")
    print("|---|---|---|---|---|---|---|---|")
    for key in ("A|strict", "A|recall", "A+B|strict", "A+B|recall"):
        c = g["cells"][key]
        corpus, rule = key.split("|")
        print(f"| {corpus} | {rule} | {c['issues']:,} | {c['rooted']} | {pct(c['rooted_rate'])} | "
              f"{pct(c['null_mean'])} ({pct(c['null_ci95'][0])}–{pct(c['null_ci95'][1])}) | "
              f"{100 * c['effect']:+.1f} pts ({100 * c['effect_ci95'][0]:+.1f} to {100 * c['effect_ci95'][1]:+.1f}) | "
              f"{pct(c['pre_event_rate'])} |")


def verified_table():
    s = summary()
    cA, cB = g["cells"]["A|strict"], g["cells"]["A+B|recall"]
    print("| | corpus A, strict rule | + corpus B, recall rule |")
    print("|---|---|---|")
    print(f"| machine ROOTED | {s['a']} | {s['a']} + {s['new']} new = {cB['rooted']} |")
    print(f"| read by eye | {s['a']}: {s['va']} | {s['new']} new: {s['vn']} |")
    print(f"| verified roots (GENUINE or GENUINE_DAY) | {s['ok_a']}/{NTEST} ({pct(s['ok_a'] / NTEST)}) | "
          f"{s['total']}/{NTEST} ({pct(s['total'] / NTEST)}) |")
    exp = [round(c["null_mean"] * NTEST, 1) for c in (cA, cB)]
    bad = [s["va"].get("COINCIDENCE", 0) + s["va"].get("DATE_CONFLICT", 0),
           s["va"].get("COINCIDENCE", 0) + s["va"].get("DATE_CONFLICT", 0) +
           s["vn"].get("COINCIDENCE", 0) + s["vn"].get("DATE_CONFLICT", 0)]
    print(f"| chance roots the shuffle null predicts | {exp[0]} | {exp[1]} |")
    print(f"| roots read as COINCIDENCE or DATE_CONFLICT | {bad[0]} | {bad[1]} |")


def edge_rows(objs, cell):
    for o in sorted(objs, key=lambda o: (ORDER.get(v_of(o, cell).get("verdict"), 9), o["date"])):
        v, c = v_of(o, cell), o[cell]
        label = (o["named_case"] or o["tokens"][0]).replace("|", "/")
        mk = "" if c.get("month_known") else " (approx)"
        src = c.get("source") or c["earliest"].split("/", 1)[1].split("__")[0]
        print(f"| {label} ({o['event_id'][-6:]}) | {o['date']} | {o['n_catalogs']} | {src} {c['issue_date']}{mk} | "
              f"{c['lag_months']} | {page_cell(o['event_id'], c)} | **{v.get('verdict', 'UNREAD')}** | "
              f"{(v.get('note') or '').replace('|', '/')} | {(v.get('upstream') or '—').replace('|', '/')} |")


def edge_table(cell):
    print("| event | date | cats | earliest issue | lag (mo) | page | verdict | what the issue says | source it names |")
    print("|---|---|---|---|---|---|---|---|---|")
    edge_rows(a_roots() if cell == "A|strict" else new_edges(), cell)


def kind_table():
    rows = Counter()
    n = 0
    for o in a_roots() + new_edges():
        if not counts(o):
            continue
        cell = "A|strict" if o["A|strict"]["cls"] == "ROOTED" else "A+B|recall"
        n += 1
        for k in v_of(o, cell).get("kind") or ["none"]:
            rows[k] += 1
    print(f"| source the bulletin names (an event can have more than one) | verified roots (of {n}) |")
    print("|---|---|")
    for k in ("press", "investigator", "official", "bulletin", "none"):
        print(f"| {k} | {rows[k]} |")


def approx_table():
    """verified new roots on issues whose month is approximate, with the lag bounds"""
    print("| event | issue | dated as | lag used | lag if Jan | lag if Dec | still 0-24 either way? |")
    print("|---|---|---|---|---|---|---|")
    for o in new_edges():
        c = o["A+B|recall"]
        if not counts(o) or c.get("month_known"):
            continue
        ey, em = int(o["date"][:4]), int(o["date"][5:7])
        iy = int(c["issue_date"][:4])
        lo, hi = (iy - ey) * 12 + 1 - em, (iy - ey) * 12 + 12 - em
        how = "interpolated" if c.get("source") in ("FSR", "LDLN") else "year only"
        ok = "yes" if lo >= 0 and hi <= 24 else ("no: may predate" if lo < 0 else "no: may be >24")
        if how == "interpolated":
            ok = "interpolated between dated issues (about ±3 months)"
        print(f"| {(o['named_case'] or o['tokens'][0])} | {c['earliest'].split('/', 1)[1][:60]} | {how} | "
              f"{c['lag_months']} | {lo} | {hi} | {ok} |")


def echo_table():
    print("| event | role | A: dated mentions (any time) | A: within 0–24 mo | A+B: dated mentions | A+B: within 0–24 mo, by source |")
    print("|---|---|---|---|---|---|")
    for tid, r in echo.items():
        out = []
        for c in ("A", "B"):
            L = r[c]["strict"] + r[c]["recall_only"]
            win = [x for x in L if 0 <= x["lag_months"] <= 24]
            out.append((len(L), win))
        src = Counter(x["issue"].split("__")[0][2:] for x in out[1][1])
        print(f"| {tid} | {r['kind']} | {out[0][0]} | {len(out[0][1])} | {out[0][0] + out[1][0]} | "
              f"{len(out[0][1]) + len(out[1][1])} {dict(src) if src else ''} |")


def echo_window_hits():
    """every 0-24 month hit for the four targets, for reading by eye"""
    for tid, r in echo.items():
        if r["kind"] != "TARGET":
            continue
        for c in ("A", "B"):
            for x in r[c]["strict"] + r[c]["recall_only"]:
                if 0 <= x["lag_months"] <= 24:
                    print(f"- {tid} {x['issue'][:80]} lag {x['lag_months']}: "
                          f"{(x.get('context') or x.get('snippet') or '')[:300]!r}")


def gradient():
    print("| catalogues | events | A, strict: machine ROOTED | A, strict: verified | A+B, recall: verified |")
    print("|---|---|---|---|---|")
    rows = {}
    for o in g["nodes"]:
        if o["A|strict"]["cls"] not in ("ROOTED", "ABSENT", "LATE_ONLY"):
            continue
        b = min(o["n_catalogs"], 6)
        r = rows.setdefault(b, [0, 0, 0, 0])
        r[3] += 1
        r[0] += o["A|strict"]["cls"] == "ROOTED"
        r[1] += o["A|strict"]["cls"] == "ROOTED" and counts(o)
        r[2] += counts(o)
    for k in sorted(rows):
        a, va, v, n = rows[k]
        print(f"| {k if k < 6 else '6+'} | {n} | {a} ({pct(a / n)}) | {va} ({pct(va / n)}) | {v} ({pct(v / n)}) |")


def corpus_table(n=30):
    print("| series | issues | span | chars | month known |")
    print("|---|---|---|---|---|")
    for r in corp["series"][:n]:
        print(f"| {r['series']} | {r['issues']} | {r['first']} – {r['last']} | {r['chars'] / 1e6:.1f}M | {r['month_known']} |")


if __name__ == "__main__":
    print(f"<!-- {json.dumps(summary())} -->\n")
    print("### Four cells\n"); cells_table()
    print("\n### Verified\n"); verified_table()
    print("\n### Corpus-A strict roots, read by eye\n"); edge_table("A|strict")
    print("\n### New roots from corpus B, read by eye\n"); edge_table("A+B|recall")
    print("\n### Sources named\n"); kind_table()
    print("\n### Approximate issue dates\n"); approx_table()
    print("\n### Echo targets\n"); echo_table()
    print("\n### Echo target hits within 24 months\n"); echo_window_hits()
    print("\n### Gradient\n"); gradient()
    print("\n### Corpus\n"); corpus_table()
