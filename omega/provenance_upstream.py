#!/usr/bin/env python3
"""One hop further upstream: what does the earliest bulletin say ITS source was?

Session 7. For every event that the v2 provenance graph roots in a
contemporaneous periodical issue, read the text around the earliest
corroborating hit (+-700 chars) and extract the source that issue itself
names: a newspaper ("(Antioch Ledger, 03-29-75)", "the Denver Post reported"),
a wire service (AP, UPI, Reuters), or a named investigator / organisation
("investigator, David Miller", "NICAP", "GEPAN"). This turns
catalogue -> bulletin into catalogue -> bulletin -> named upstream source.

It is pattern extraction, not reading. Each extracted source carries the
snippet it came from, so a human can check it. A miss means the pattern found
nothing, not that the bulletin cites nothing.

Usage:
  OMEGA_PERIODICALS=<860 txt dir> OMEGA_EXPANSION=<fetch OUTDIR> \
      python3 -I omega/provenance_upstream.py [graph_v2.json] [cell]
Writes evidence_vault/07_PERIODICALS_PRIMARY/provenance_upstream.json
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PD = os.environ.get("OMEGA_PERIODICALS", "")
XD = os.environ.get("OMEGA_EXPANSION", "")
GRAPH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, "evidence_vault/07_PERIODICALS_PRIMARY/provenance_graph_v2.json")
CELL = sys.argv[2] if len(sys.argv) > 2 else "A+B|recall"
OUT = os.environ.get("OMEGA_OUT") or os.path.join(
    ROOT, "evidence_vault/07_PERIODICALS_PRIMARY/provenance_upstream.json")
W = 700

PAPER = (r"Ledger|Times|News|Post|Herald|Gazette|Journal|Tribune|Star|Chronicle|Courier|"
         r"Press|Register|Sun|Examiner|Record|Daily|Dispatch|Telegraph|Mirror|Express|"
         r"Inquirer|Observer|Globe|Enquirer|Democrat|Republican|Leader|Bee|Advertiser|"
         r"Sentinel|Times-Union|Free Press|Mail|Standard|Eagle|Argus|Banner|Citizen|"
         r"Clarion|Statesman|Review|Bulletin|Messenger|Picayune|Plain Dealer|Constitution")
CAP = r"(?:[A-Z][a-zA-Z.'&-]+\s+){0,4}"
RX = [
    ("newspaper_paren", re.compile(r"\((" + CAP + r"(?:" + PAPER + r"))[,;]?\s*([^)]{0,40})\)")),
    ("newspaper_named", re.compile(r"\b(?:the\s+)?(" + CAP + r"(?:" + PAPER + r"))\s+"
                                   r"(?:reported|said|carried|stated|story|article|of\s+[A-Z])")),
    ("newspaper_named", re.compile(r"\b(?:according to|reported (?:by|in)|appeared in|"
                                   r"clipping from|source:)\s+(?:the\s+)?(" + CAP + r"(?:" + PAPER + r"))")),
    ("wire", re.compile(r"\b(UPI|AP|Reuters?|Associated Press|United Press(?: International)?|"
                        r"Agence France[- ]Presse|AFP)\b")),
    ("investigator", re.compile(r"\b(?:investigat(?:or|ed by|ors?)|field investigator|"
                                r"State Director|reported by|source:)\W{0,3}"
                                r"((?:[A-Z][a-z]+\s){1,2}[A-Z][a-z]+)")),
    ("organisation", re.compile(r"\b(NICAP|APRO|MUFON|CUFOS|GEPAN|SEPRA|GEIPAN|BUFORA|"
                                r"Project Blue Book|Blue Book|NORAD|Air Force|police|sheriff|"
                                r"gendarmerie|Gendarmerie|RCMP|state police|highway patrol)\b",
                                re.I)),
]
NOT_PAPER = re.compile(r"UFO|Saucer|BUFORA|MUFON|APRO|NICAP|CUFOS|FSR|Skylook|LDLN|"
                       r"^(?:The )?(?:Journal|Bulletin|Review|News|Times|Post|Star|Sun|Mail)$", re.I)


def text_of(key):
    corpus, name = key.split("/", 1)
    base = PD if corpus == "A" else os.path.join(XD, "txt")
    return open(os.path.join(base, name), encoding="utf-8", errors="replace").read()


def upstream(snippet):
    found = []
    for kind, rx in RX:
        for m in rx.finditer(snippet):
            v = " ".join(m.group(1).split()).strip(" ,.;")
            if kind.startswith("newspaper") and (NOT_PAPER.search(v) or len(v) < 5):
                continue
            if kind == "wire" and m.group(1) == "AP" and not re.search(r"\(AP\)|AP\b[^a-z]{0,3}(?:reported|story|dispatch|wire)", snippet):
                continue                       # bare "AP" is usually "APRO" OCR or a word fragment
            found.append(dict(kind=kind, source=v,
                              snippet=" ".join(snippet[max(0, m.start() - 120): m.end() + 80].split())))
    return found


def main():
    g = json.load(open(GRAPH))
    rows, kinds = [], Counter()
    for o in g["nodes"]:
        c = o.get(CELL, {})
        if c.get("cls") != "ROOTED":
            continue
        t = text_of(c["earliest"])
        off = c["char_offset"]
        snip = t[max(0, off - W): off + W]
        ups = upstream(snip)
        best = {}
        for u in ups:
            best.setdefault(u["kind"], u)
        for k in best:
            kinds[k] += 1
        rows.append(dict(event_id=o["event_id"], named_case=o["named_case"], date=o["date"],
                         tokens=o["tokens"], earliest=c["earliest"], issue_date=c["issue_date"],
                         lag_months=c["lag_months"], char_offset=off, source=c.get("source"),
                         upstream=ups[:12]))
    n = len(rows)
    named = sum(1 for r in rows if any(u["kind"] in ("newspaper_paren", "newspaper_named", "wire")
                                       for u in r["upstream"]))
    inv = sum(1 for r in rows if any(u["kind"] == "investigator" for u in r["upstream"]))
    print(f"{CELL}: ROOTED {n}; earliest issue names a newspaper or wire within +-{W} chars: "
          f"{named}; names an investigator: {inv}")
    print("kinds:", dict(kinds))
    json.dump(dict(cell=CELL, window=W, rooted=n, names_press=named, names_investigator=inv,
                   kinds=dict(kinds), rows=rows), open(OUT, "w"), indent=1, ensure_ascii=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
