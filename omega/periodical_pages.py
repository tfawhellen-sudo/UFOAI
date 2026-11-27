#!/usr/bin/env python3
"""Page-level citations for provenance edges (session 7).

The vaulted periodical texts are archive.org `_djvu.txt` files, which lose page
breaks, so edges were cited by issue + character offset. archive.org's
`/cors/<item>/<file>` endpoint is reachable from the cloud container (the
`/download` redirect to the data nodes is not), and it serves each issue's
`_djvu.xml`, which keeps one <OBJECT> per scanned page, and
`_page_numbers.json`, which maps scan leaves to printed page numbers.

For every edge, this fetches the issue's djvu.xml, finds the scanned page whose
text best matches the words around the hit (shared 4-word shingles), and
records: scan page n of N, the printed page number when archive.org detected
one, and a BookReader deep link to that page image.

Usage:
  OMEGA_PERIODICALS=<860 txt dir> OMEGA_EXPANSION=<fetch OUTDIR> \
      python3 -I omega/periodical_pages.py graph_v2.json [cell ...]
Writes evidence_vault/07_PERIODICALS_PRIMARY/provenance_pages.json
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PD = os.environ.get("OMEGA_PERIODICALS", "")
XD = os.environ.get("OMEGA_EXPANSION", "")
OUT = os.environ.get("OMEGA_OUT_PAGES") or os.path.join(
    ROOT, "evidence_vault/07_PERIODICALS_PRIMARY/provenance_pages.json")
CACHE = os.environ.get("OMEGA_PAGE_CACHE", "")
UA = {"User-Agent": "omega-research/1.0 (periodical provenance study)"}
# corpus A issues come from three archive.org items
A_ITEMS = {"MUFON": "MUFON_UFO_Journal_-_Skylook", "APRO": "apro-bulletin",
           "IUR": "iur-vol.-31-no.-4"}


def get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            err = e
        except Exception as e:
            err = e
        time.sleep(3 * (k + 1))
    raise err


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower().replace("¬ ", "").replace("- ", "")).split()


def shingles(words, n=4):
    return {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


_A_FILES = {}


def a_file_map():
    """corpus-A text name -> (item, stem). Names were made by replacing spaces."""
    if _A_FILES:
        return _A_FILES
    for src, item in A_ITEMS.items():
        md = json.loads(get(f"https://archive.org/metadata/{item}"))
        for f in md.get("files", []):
            n = f["name"]
            if n.endswith("_djvu.txt"):
                key = re.sub(r"[^A-Za-z0-9]+", "_", n[:-len("_djvu.txt")]).strip("_").lower()
                _A_FILES[(src, key)] = (item, n[:-len("_djvu.txt")])
    return _A_FILES


def locate_source(key, node_cell):
    """(item, stem) of an issue key."""
    corpus, name = key.split("/", 1)
    if corpus == "B":
        f = node_cell.get("ia_file") or ""
        return node_cell["ia_id"], f[:-len("_djvu.txt")] if f.endswith("_djvu.txt") else f
    src, rest = name.split("__", 1)
    k = re.sub(r"[^A-Za-z0-9]+", "_", rest[:-len("_djvu.txt")] if rest.endswith("_djvu.txt") else rest).strip("_").lower()
    m = a_file_map()
    if (src, k) in m:
        return m[(src, k)]
    # MUFON texts were renamed to YYYY_MM; fall back to a date match
    hits = [v for (s, kk), v in m.items() if s == src and k in kk]
    return hits[0] if len(hits) == 1 else (None, None)


def text_of(key):
    corpus, name = key.split("/", 1)
    base = PD if corpus == "A" else os.path.join(XD, "txt")
    return open(os.path.join(base, name), encoding="utf-8", errors="replace").read()


def pages_of(item, stem):
    """list of page texts from <stem>_djvu.xml, plus printed page numbers."""
    tag = re.sub(r"[^\w.-]+", "_", f"{item}__{stem}")
    cp = os.path.join(CACHE, tag + ".json") if CACHE else None
    if cp and os.path.exists(cp):
        return json.load(open(cp))
    q = lambda p: urllib.parse.quote(p)
    raw = get(f"https://archive.org/cors/{q(item)}/{q(stem)}_djvu.xml")
    if not raw:
        return None
    x = raw.decode("utf-8", "replace")
    pages = []
    for obj in re.findall(r"<OBJECT\b.*?</OBJECT>", x, re.S):
        words = re.findall(r"<WORD\b[^>]*>(.*?)</WORD>", obj, re.S)
        pages.append(html.unescape(" ".join(words)))
    pn = get(f"https://archive.org/cors/{q(item)}/{q(stem)}_page_numbers.json")
    printed = None
    if pn:
        try:
            pj = json.loads(pn)
            printed = [p.get("pageNumber") or "" for p in pj.get("pages", [])]
        except ValueError:
            printed = None
    out = dict(pages=pages, printed=printed)
    if cp:
        os.makedirs(CACHE, exist_ok=True)
        json.dump(out, open(cp, "w"))
    return out


def find_page(pg, snippet, token):
    sh = shingles(norm(snippet))
    tok = norm(token)
    best, score = None, 0
    for i, p in enumerate(pg["pages"]):
        w = norm(p)
        s = len(sh & shingles(w))
        if tok and " ".join(tok) not in " ".join(w):
            s = s // 2                       # page lacks the token itself
        if s > score:
            best, score = i, s
    return best, score


def viewer_link(item, stem, i, single):
    base = f"https://archive.org/details/{item}" + ("" if single else f"/{urllib.parse.quote(stem)}")
    return f"{base}/page/n{i}/mode/1up"


def main():
    g = json.load(open(sys.argv[1]))
    cells = sys.argv[2:] or ["A+B|recall"]
    edges = {}
    for o in g["nodes"]:
        for cell in cells:
            c = o.get(cell, {})
            if c.get("cls") in ("ROOTED", "LATE_ONLY") and c.get("earliest"):
                edges[(o["event_id"], c["earliest"])] = (o, c)
    print("edges:", len(edges), flush=True)
    rows = []
    for (eid, key), (o, c) in sorted(edges.items()):
        item, stem = locate_source(key, c)
        r = dict(event_id=eid, named_case=o["named_case"], date=o["date"], issue=key,
                 issue_date=c["issue_date"], cls=c["cls"], lag_months=c["lag_months"],
                 char_offset=c["char_offset"], ia_id=item, ia_file_stem=stem)
        if not item:
            r["page_status"] = "item not mapped"
            rows.append(r)
            continue
        try:
            pg = pages_of(item, stem)
        except Exception as e:
            pg = None
            r["page_status"] = f"fetch error {type(e).__name__}"
        if pg:
            t = text_of(key)
            off = c["char_offset"]
            snip = t[max(0, off - 200): off + 200]
            i, score = find_page(pg, snip, o["tokens"][0] if o["tokens"] else "")
            if i is None or score < 3:
                r["page_status"] = f"not located (score {score})"
            else:
                printed = (pg["printed"][i] if pg["printed"] and len(pg["printed"]) == len(pg["pages"])
                           else "")
                r.update(page_status="located", scan_page=i + 1, scan_pages=len(pg["pages"]),
                         printed_page=printed or None, match_score=score,
                         viewer=viewer_link(item, stem, i, single=(stem == item)))
        elif "page_status" not in r:
            r["page_status"] = "no djvu.xml"
        rows.append(r)
        print(eid, key[:60], r.get("page_status"), r.get("scan_page"), r.get("printed_page"), flush=True)
    ok = sum(r["page_status"] == "located" for r in rows)
    print(f"located {ok}/{len(rows)}")
    json.dump(dict(cells=cells, located=ok, edges=len(rows), rows=rows), open(OUT, "w"),
              indent=1, ensure_ascii=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
