"""Terminology-over-time test on the PURSUE declassified release (286 OCR docs).

H_vocab: if the insider vocabulary of 2023 ("non-human intelligence", "biologics",
"crash retrieval", "legacy program", "technologies of unknown origin") names a long-running
internal programme, some internal documents dated BEFORE the public coinage should use it.
Falsifier for "long-running internal vocabulary": zero pre-2017 occurrences in the document's
own voice across the released internal record.  (Weak falsifier: a secret programme's own
papers would not be in a release. The power of the test is reported, not assumed.)

Document date = year in the filename if any, else the modal year 1940-2026 in the first
4,000 chars after stripping 'Approved For Release' stamps.  Date source is recorded.
Usage: python -I contact_terms.py <djvu_dir> <out_json>
"""
import json, os, re, sys, collections

TERMS = {
  # legacy public vocabulary
  "flying saucer": r"flying\s+saucers?|flying\s+discs?",
  "UFO": r"\bU\.?F\.?O\.?s?\b|unidentified\s+flying\s+objects?",
  # modern official vocabulary
  "UAP": r"\bUAPs?\b|unidentified\s+a(?:erial|nomalous)\s+phenomen",
  # insider-claim vocabulary (2017-2023 public coinage)
  "non-human": r"non[\s-]?human|\bNHI\b",
  "biologics": r"\bbiologics\b",
  "reverse engineering": r"reverse[\s-]engineer",
  "crash retrieval": r"crash[\s-]+retriev|crash\s+recover",
  "legacy program": r"legacy\s+program",
  "unknown origin": r"(?:technolog\w*|material\w*)\s+of\s+unknown\s+origin",
  "trans-medium": r"trans[\s-]?medium",
  # contact vocabulary
  "extraterrestrial": r"extra[\s-]?terrestrials?|\bE\.?T\.?s?\b(?!\s+al)",
  "contact": r"\bcontact(?:ee|ed)?\s+(?:with\s+)?(?:the\s+)?(?:alien|extra|being|entit|occupant|non)",
  "telepathy/psi": r"telepath\w*|\bpsi\b|remote\s+view\w*|psychic\w*",
  "consciousness": r"consciousness",
  "entity/being": r"\b(?:entit(?:y|ies)|beings|occupants?|humanoids?)\b",
}
STAMP = re.compile(r"approved\s+for\s+release[^\n]*", re.I)
YR = re.compile(r"\b(19[4-9]\d|20[0-2]\d)\b")

def doc_year(name, text):
    m = YR.findall(name.replace("_", " ").replace("-", " "))
    if m:
        return int(m[-1]), "filename"
    head = STAMP.sub(" ", text[:4000])
    ys = [int(y) for y in YR.findall(head) if 1940 <= int(y) <= 2026]
    if ys:
        return collections.Counter(ys).most_common(1)[0][0], "text_modal"
    return None, "undated"

def era(y):
    if y is None: return "undated"
    if y < 1970: return "1940-69"
    if y < 2000: return "1970-99"
    if y < 2017: return "2000-16"
    if y < 2023: return "2017-22"
    return "2023-26"

def main(d, out):
    docs = []
    for fn in sorted(os.listdir(d)):
        t = open(os.path.join(d, fn), errors="ignore").read()
        name = fn.replace("_djvu.txt", "")
        y, src = doc_year(name, t)
        hits = {}
        for k, rx in TERMS.items():
            ms = list(re.finditer(rx, t, re.I if k not in ("UAP",) else 0))
            if ms:
                hits[k] = {"n": len(ms), "ctx": [re.sub(r"\s+", " ", t[max(0, m.start()-160):m.end()+160]) for m in ms[:4]]}
        docs.append({"doc": name, "year": y, "date_src": src, "era": era(y), "chars": len(t), "hits": hits})
    eras = ["1940-69", "1970-99", "2000-16", "2017-22", "2023-26", "undated"]
    table = {}
    for e in eras:
        ds = [x for x in docs if x["era"] == e]
        row = {"docs": len(ds), "Mchars": round(sum(x["chars"] for x in ds)/1e6, 2)}
        for k in TERMS:
            row[k] = sum(1 for x in ds if k in x["hits"])
        table[e] = row
    json.dump({"table_docs_containing": table, "docs": docs}, open(out, "w"), indent=1)
    hdr = ["era", "docs", "Mchars"] + list(TERMS)
    print("\t".join(hdr))
    for e in eras:
        print("\t".join([e] + [str(table[e][h]) for h in hdr[1:]]))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
