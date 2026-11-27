import sys, json, urllib.request, urllib.parse, re, html, os, time
UA = "omega-research/1.0 (academic UAP data study; non-commercial)"
def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(3):
        try:
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as e:
            err = e; time.sleep(2*(i+1))
    raise err
def search(q, rows=50, fields=("identifier","title","date","language","mediatype")):
    p = [("q", q), ("rows", str(rows)), ("output", "json")] + [("fl[]", f) for f in fields]
    d = json.loads(get("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(p)))
    return d["response"]["numFound"], d["response"]["docs"]
def files(ident):
    d = json.loads(get("https://archive.org/metadata/" + urllib.parse.quote(ident)))
    return d.get("files", []), d.get("metadata", {})
def stream_text(ident, fname):
    t = get("https://archive.org/stream/%s/%s" % (urllib.parse.quote(ident), urllib.parse.quote(fname))).decode("utf-8", "replace")
    m = re.search(r"<pre>(.*?)</pre>", t, re.S)
    return html.unescape(m.group(1)) if m else ""
if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "search":
        n, docs = search(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 50)
        print("N=", n)
        for x in docs:
            if x.get("mediatype") != "texts": continue
            print(" ", x["identifier"], "|", str(x.get("title"))[:100], "|", str(x.get("date", ""))[:10], "|", x.get("language"))
    elif cmd == "txt":  # list djvu txt files with sizes for identifiers
        for ident in sys.argv[2:]:
            try:
                fs, md = files(ident)
                t = [(f["name"], f.get("size")) for f in fs if f["name"].endswith("_djvu.txt")]
                print(ident, "|", str(md.get("title"))[:70], "|", md.get("language"), "|", t[:5])
            except Exception as e:
                print(ident, "ERR", e)
