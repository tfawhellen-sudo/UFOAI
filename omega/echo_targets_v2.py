#!/usr/bin/env python3
"""Session-3 echo-chamber targets, re-tested on the expanded corpus (session 7).

omega/periodical_provenance.py found the four "unverifiable" multi-catalogue
events (Galesburg 1967, "a small town in Texas" 1966, Dallas 1965,
Wright-Patterson 1951) absent from the 860 MUFON/APRO/IUR issues, while four
positive controls of the same era were found (4/4). Its own caveat: Flying
Saucer Review, newspapers and other bulletins were not in the corpus.

This re-runs exactly that test on corpus B (FSR + the AFU ufonewsletters
collection, including the UFO Newsclipping Service), with the session-7
recall rule as well as the strict one. Every date-corroborated hit is listed
with issue, issue date and a context snippet, so each can be read by eye.

Usage:
  OMEGA_PERIODICALS=<860 txt dir> OMEGA_EXPANSION=<fetch OUTDIR> \
      python3 -I omega/echo_targets_v2.py
Writes evidence_vault/07_PERIODICALS_PRIMARY/echo_targets_v2.json
"""
import importlib.util
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v2 = _load("pg2", "omega/provenance_graph_v2.py")
pp = _load("pp1", "omega/periodical_provenance.py")
# days of month, from the session-3 docstring and the standard case dates
DAY = {"galesburg_1967": 9, "texas_town_1966": 5, "dallas_1965": 4, "wpafb_1951": 1,
       "socorro_1964": 24, "exeter_1965": 3, "kecksburg_1965": 9, "tep_1981": 8}
OUT = os.environ.get("OMEGA_OUT_TARGETS") or os.path.join(
    ROOT, "evidence_vault/07_PERIODICALS_PRIMARY/echo_targets_v2.json")


def main():
    issues, nA, skipped = v2.load()
    out = {}
    for t in pp.TARGETS:
        rx = re.compile(t["place"], re.I)
        y, m, dd = t["year"], t["month"], DAY.get(t["id"])
        row = dict(kind=t["kind"], note=t["note"], year=y, month=m)
        for corpus in ("A", "B"):
            keys = [k for k in issues if issues[k]["corpus"] == corpus]
            place_hits, place_issues = 0, set()
            strict, recall = [], []
            for k in keys:
                txt = issues[k]["text"]
                for mt in rx.finditer(txt):
                    place_hits += 1
                    place_issues.add(k)
                    c = txt[max(0, mt.start() - v2.WIN): mt.end() + v2.WIN]
                    info = v2.ctx_info(c)
                    p_s = v2.pairs(info, "strict")
                    p_r = v2.pairs(info, "recall") | {(a, b) for a, b, x in info[3] if x == dd}
                    iy, im = issues[k]["date"]
                    rec = dict(issue=k, issue_date="%04d-%02d" % (iy, im),
                               lag_months=(iy - y) * 12 + (im - m), offset=mt.start(),
                               context=" ".join(c.split())[:420])
                    if (y, m) in p_s:
                        strict.append(rec)
                    elif (y, m) in p_r:
                        recall.append(rec)
            # one entry per issue, earliest hit
            def dedupe(lst):
                seen, o = set(), []
                for r in sorted(lst, key=lambda r: (r["issue_date"], r["offset"])):
                    if r["issue"] not in seen:
                        seen.add(r["issue"])
                        o.append(r)
                return o
            strict, recall = dedupe(strict), dedupe(recall)
            row[corpus] = dict(place_hits=place_hits, place_issues=len(place_issues),
                               strict_issues=len(strict), recall_only_issues=len(recall),
                               strict=strict[:40], recall_only=recall[:40],
                               by_source=dict(Counter(issues[r["issue"]]["src"] for r in strict + recall)))
        out[t["id"]] = row
        a, b = row["A"], row["B"]
        print(f'{t["id"]:16s} {t["kind"]:7s} A: place {a["place_hits"]:5d} strict {a["strict_issues"]:3d} '
              f'+recall {a["recall_only_issues"]:3d} | B: place {b["place_hits"]:5d} '
              f'strict {b["strict_issues"]:3d} +recall {b["recall_only_issues"]:3d}  {b["by_source"]}')
    json.dump(dict(corpus=dict(A=nA, B=len(issues) - nA), targets=out), open(OUT, "w"),
              indent=1, ensure_ascii=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
