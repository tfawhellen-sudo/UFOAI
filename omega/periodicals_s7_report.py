#!/usr/bin/env python3
"""Tables for omega/periodicals_expansion_s7.md, generated from the vault JSON so
the write-up and the data cannot drift apart. Prints Markdown to stdout.

Inputs (evidence_vault/07_PERIODICALS_PRIMARY/): provenance_graph_v2.json,
echo_targets_v2.json, provenance_pages.json, corpus_summary_s7.json, and
omega/periodicals_s7/edge_verdicts.json (by-eye verdicts on every edge that is
ROOTED in A+B|recall but not in A|strict).

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


def pct(x):
    return f"{100 * x:.1f}%"


def cells_table():
    print("| corpus | rule | issues | ROOTED / 310 | rate | shuffle null (95%) | effect over null (95% CI) | pre-event probe |")
    print("|---|---|---|---|---|---|---|---|")
    for key in ("A|strict", "A|recall", "A+B|strict", "A+B|recall"):
        c = g["cells"][key]
        corpus, rule = key.split("|")
        print(f"| {corpus} | {rule} | {c['issues']:,} | {c['rooted']} | {pct(c['rooted_rate'])} | "
              f"{pct(c['null_mean'])} ({pct(c['null_ci95'][0])}–{pct(c['null_ci95'][1])}) | "
              f"{100 * c['effect']:+.1f} pts ({100 * c['effect_ci95'][0]:+.1f} to {100 * c['effect_ci95'][1]:+.1f}) | "
              f"{pct(c['pre_event_rate'])} |")


def new_edges():
    rows = []
    for o in g["nodes"]:
        a, b = o["A|strict"], o["A+B|recall"]
        if b["cls"] == "ROOTED" and a["cls"] != "ROOTED":
            rows.append((o, a, b))
    return rows


def verified():
    base = sum(o["A|strict"]["cls"] == "ROOTED" for o in g["nodes"])
    new = new_edges()
    vc = Counter(verd.get(o["event_id"], {}).get("verdict", "UNREAD") for o, _, _ in new)
    # an edge read as GENUINE whose correct issue date is >24 months is not a root
    late = sum(1 for o, _, b in new if verd.get(o["event_id"], {}).get("verdict") in COUNTS_AS_ROOT
               and "LATE not ROOTED" in verd[o["event_id"]]["note"])
    good = sum(vc[k] for k in COUNTS_AS_ROOT) - late
    return base, new, vc, good, late


def edge_table():
    _, new, _, _, _ = verified()
    print("| event | date | earliest issue | lag (mo) | page | verdict | upstream the issue names |")
    print("|---|---|---|---|---|---|---|")
    order = {"GENUINE": 0, "GENUINE_DAY": 1, "PLAUSIBLE": 2, "DATE_CONFLICT": 3, "COINCIDENCE": 4}
    for o, a, b in sorted(new, key=lambda t: (order.get(verd.get(t[0]["event_id"], {}).get("verdict"), 9),
                                              t[0]["date"])):
        v = verd.get(o["event_id"], {})
        p = pages.get((o["event_id"], b["earliest"]), {})
        src = b.get("source", "")
        name = b["earliest"].split("/", 1)[1]
        if p.get("page_status") == "located":
            pg = f"[scan {p['scan_page']}/{p['scan_pages']}]({p['viewer']})"
            if p.get("printed_page"):
                pg += f", p.{p['printed_page']}"
        else:
            pg = p.get("page_status", "n/a")
        label = (o["named_case"] or o["tokens"][0]).replace("|", "/")
        mk = "" if b.get("month_known") else " (yr)"
        print(f"| {label} ({o['event_id'][-6:]}) | {o['date']} | {src} {b['issue_date']}{mk} | "
              f"{b['lag_months']} | {pg} | **{v.get('verdict', 'UNREAD')}** | "
              f"{(v.get('upstream') or '—').replace('|', '/')} |")


def echo_table():
    print("| event | role | A: dated mentions (any time) | A: within 0–24 mo | B: dated mentions | B: within 0–24 mo, by source |")
    print("|---|---|---|---|---|---|")
    for tid, r in echo.items():
        out = []
        for c in ("A", "B"):
            L = r[c]["strict"] + r[c]["recall_only"]
            win = [x for x in L if 0 <= x["lag_months"] <= 24]
            out.append((len(L), win))
        src = Counter(x["issue"].split("__")[0][2:] for x in out[1][1])
        print(f"| {tid} | {r['kind']} | {out[0][0]} | {len(out[0][1])} | {out[1][0]} | "
              f"{len(out[1][1])} {dict(src) if src else ''} |")


def gradient():
    print("| catalogues | A|strict rooted | A+B|recall rooted, verified |")
    print("|---|---|---|")
    rows = {}
    for o in g["nodes"]:
        if o["A|strict"]["cls"] not in ("ROOTED", "ABSENT", "LATE_ONLY"):
            continue
        b = min(o["n_catalogs"], 6)
        r = rows.setdefault(b, [0, 0, 0])
        r[2] += 1
        r[0] += o["A|strict"]["cls"] == "ROOTED"
        ok = o["A|strict"]["cls"] == "ROOTED" or (
            o["A+B|recall"]["cls"] == "ROOTED" and verd.get(o["event_id"], {}).get("verdict") in COUNTS_AS_ROOT
            and "LATE not ROOTED" not in verd[o["event_id"]]["note"])
        r[1] += ok
    for k in sorted(rows):
        a, v, n = rows[k]
        print(f"| {k if k < 6 else '6+'} | {a}/{n} ({pct(a / n)}) | {v}/{n} ({pct(v / n)}) |")


def corpus_table(n=25):
    print("| series | issues | span | chars | month known |")
    print("|---|---|---|---|---|")
    for r in corp["series"][:n]:
        print(f"| {r['series']} | {r['issues']} | {r['first']} – {r['last']} | {r['chars'] / 1e6:.1f}M | {r['month_known']} |")


if __name__ == "__main__":
    base, new, vc, good, late = verified()
    print(f"<!-- verified: base {base}, new {len(new)}, verdicts {dict(vc)}, counted {good}, late {late} -->\n")
    print("### Four cells\n"); cells_table()
    print("\n### New edges\n"); edge_table()
    print("\n### Echo targets\n"); echo_table()
    print("\n### Gradient\n"); gradient()
    print("\n### Corpus\n"); corpus_table()
