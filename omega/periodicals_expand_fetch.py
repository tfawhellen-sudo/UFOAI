#!/usr/bin/env python3
"""Fetch OCR text for the periodical corpus expansion (session 7).

The 860-issue corpus (MUFON/Skylook, APRO Bulletin, IUR) is three US
bulletins. Its red team names the missing runs: Flying Saucer Review and
local newspapers. archive.org holds both kinds:

  * the-flying-saucer-review-ultimate-collection   246 FSR issues, 1955-
  * collection:ufonewsletters (Archives for the Unexplained uploads)
    ~10k items: UFO Newsclipping Service (newspaper clippings, 1969-),
    LDLN, BUFORA Journal, Australian UFO Bulletin, Stendek, Inforespace ...

Only archive.org/stream is reachable from the cloud container (the data
nodes are blocked), so text comes from the <pre> block of
https://archive.org/stream/<id>/<file>_djvu.txt. Page breaks are not
preserved; citations are by issue + character offset.

Usage: python3 -I omega/periodicals_expand_fetch.py OUTDIR
Writes OUTDIR/txt/<series>__<id>.txt and OUTDIR/manifest.jsonl
"""
import html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

OUT = sys.argv[1]
UA = {"User-Agent": "omega-research/1.0 (periodical provenance study)"}


def get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None                  # wrong file name guess: no retry
            err = e
        except Exception as e:
            err = e
        time.sleep(2 * (k + 1))
    raise err


def pre_text(raw):
    if raw is None:
        return None
    m = re.search(rb"<pre>(.*?)</pre>", raw, re.S)
    return html.unescape(m.group(1).decode("utf-8", "replace")) if m else None


def series(title):
    t = re.sub(r"\b(1[89]|20)\d\d\b.*", "", title or "")
    t = re.sub(r"\b(vol|no|issue|v\d|n\d).*", "", t, flags=re.I)
    t = re.sub(r"^AFU\s*", "", t).strip(" -_")
    return re.sub(r"\W+", "_", t).strip("_")[:40] or "misc"


def items():
    out = []
    md = json.loads(get("https://archive.org/metadata/the-flying-saucer-review-ultimate-collection"))
    for f in md["files"]:
        if f["name"].endswith("_djvu.txt"):
            out.append(dict(id="the-flying-saucer-review-ultimate-collection",
                            file=f["name"], series="FSR", title=f["name"], date=None))
    q = urllib.parse.urlencode(dict(q="collection:ufonewsletters",
                                    fields="identifier,title,date", count=10000))
    cursor, n = None, 0
    while True:
        u = "https://archive.org/services/search/v1/scrape?" + q + (f"&cursor={cursor}" if cursor else "")
        d = json.loads(get(u))
        for x in d["items"]:
            out.append(dict(id=x["identifier"], file=None, series=series(x.get("title")),
                            title=x.get("title"), date=x.get("date")))
        cursor = d.get("cursor")
        if not cursor:
            break
    return out


# Series that print dated case reports, fetched first so a partial run is
# still the useful part. Everything else that is datable to 1947-2010 follows.
PRIORITY = ["UFO_Newsclipping_Service", "LDLN", "BUFORA", "Australian_UFO_Bulletin",
            "Flying_Saucer_Digest", "Saucers_Space", "Flying_Saucer_News", "Saucer_Scoop",
            "UFO_Research_Newsletter", "Stendek", "Inforespace", "UFOIC", "TUFOIC",
            "Topside", "UFO_Information", "Phenomena", "Magonia", "Merseyside", "UFO_Times",
            "UFO_Review", "Lantern", "ACUFOS", "Awareness", "The_UFO_Enigma", "Ouranos",
            "Saucer_News", "Space_Probe", "Flying_Saucers", "Interplanetary", "Panorama"]


def year_of(it):
    s = " ".join(filter(None, [it["id"], it.get("title")])).replace("-", "_")
    m = re.search(r"(?<!\d)(19[4-9]\d|20[0-2]\d)(?!\d)", s) or \
        re.search(r"(?<!\d)(19[4-9]\d|20[0-2]\d)", s)
    if m:
        return int(m.group(1))
    d = it.get("date") or ""
    return int(d[:4]) if d[:4].isdigit() else None


# Runs with no date in their metadata that are worth dating from the cover
# text instead (LDLN = Lumieres dans la Nuit, the main French bulletin, 1958-).
DATE_FROM_TEXT = re.compile(r"^LDLN_No_")


def plan(its):
    """FSR always; others only if datable to 1947-2010 (or dated from text
    later); priority series first. OMEGA_FETCH_ONLY=<regex> restricts by id."""
    only = os.environ.get("OMEGA_FETCH_ONLY")
    if only:
        its = [it for it in its if re.search(only, it["id"])]
    keep = [it for it in its if it["series"] == "FSR" or DATE_FROM_TEXT.search(it["id"]) or
            (year_of(it) is not None and 1947 <= year_of(it) <= 2010)]
    def rank(it):
        if it["series"] == "FSR":
            return 0
        for i, p in enumerate(PRIORITY):
            if it["series"].startswith(p) or p in it["id"]:
                return 1 + i
        return 1 + len(PRIORITY)
    return sorted(keep, key=rank), len(its) - len(keep)


def fetch(it):
    name = f'{it["series"]}__{it["id"]}' + (f'__{it["file"].split("_djvu")[0]}' if it["file"] else "")
    name = re.sub(r"[^\w.\-]+", "_", name) + ".txt"
    path = os.path.join(OUT, "txt", name)
    if os.path.exists(path):
        return dict(it, path=name, status="cached", chars=os.path.getsize(path))
    f = it["file"] or f'{it["id"]}_djvu.txt'
    base = f"https://archive.org/stream/{it['id']}/"
    try:
        t = pre_text(get(base + urllib.parse.quote(f)))
        if not t:
            md = json.loads(get(f"https://archive.org/metadata/{it['id']}") or b"{}")
            fs = [x["name"] for x in md.get("files", []) if x["name"].endswith("_djvu.txt")]
            t = "\n\n".join(filter(None, (pre_text(get(base + urllib.parse.quote(x))) for x in fs)))
        if not t or not t.strip():
            return dict(it, path=None, status="no_ocr", chars=0)
        open(path, "w", encoding="utf-8").write(t)
        return dict(it, path=name, status="ok", chars=len(t))
    except Exception as e:
        return dict(it, path=None, status=f"error:{type(e).__name__}", chars=0)


def main():
    os.makedirs(os.path.join(OUT, "txt"), exist_ok=True)
    its, dropped = plan(items())
    print("items:", len(its), "dropped (undatable or after 2010):", dropped, flush=True)
    with open(os.path.join(OUT, os.environ.get("OMEGA_MANIFEST", "manifest.jsonl")), "w") as man, ThreadPoolExecutor(int(os.environ.get("OMEGA_FETCH_THREADS", "6"))) as ex:
        for k, r in enumerate(ex.map(fetch, its)):
            man.write(json.dumps(r) + "\n")
            if k % 250 == 0:
                print(k, r["status"], r["path"], flush=True)


if __name__ == "__main__":
    main()
