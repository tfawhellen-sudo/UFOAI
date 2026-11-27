"""Proximity search for CONTACT and POWER claims in declassified government records.

C2 'government maintains contact with NHI' and C3 'NHI hold or influence positions of
power' both predict that SOME internal record says so in its own voice.  This counts every
place where a contact word or a power word sits within +-WIN chars of a non-human term, and
frames each hit with deep_terms.frame() (QUOTED_FICTION / HYPOTHETICAL / THIRD_PARTY /
PHYSICS_TERM / DIRECT).  STARGATE files whose title says TRAINING are framed TRAINING first.
DIRECT hits are then read by hand; the script does not decide what they mean.

Usage: python -I contact_claims.py OUT.json NAME=DIR [NAME=DIR ...]
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deep_terms import frame  # noqa: E402

WIN = 90
NH = r"(?:non[\s-]?human|\bNHI\b|extra[\s-]?terrestrial|\baliens?\b|\bE\.?T\.?s?\b(?!\s+al)|" \
     r"\bentit(?:y|ies)\b|\bbeings\b|\boccupants?\b|space\s+(?:people|brothers)|humanoids?)"
CONTACT = r"(?:\bcontact\w*|communicat\w*|telepath\w*|channel(?:ed|ing|er)\b|messages?\s+from|" \
          r"\bliaison|\btreat(?:y|ies)\b|\bambassador)"
POWER = r"(?:positions?\s+of\s+(?:power|authority)|infiltrat\w*|hybrids?\b|among\s+us|" \
        r"(?:control|run|influenc)\w*\s+(?:the\s+|our\s+)?(?:government|congress|white\s+house|pentagon)|" \
        r"(?:elected|government)\s+officials?|world\s+leaders?|disguised\s+as\s+humans?)"

def scan(text, rx_a, rx_b):
    out = []
    for m in re.finditer(rx_a, text, re.I):
        lo, hi = max(0, m.start() - WIN), m.end() + WIN
        if re.search(rx_b, text[lo:hi], re.I):
            out.append(re.sub(r"\s+", " ", text[max(0, m.start() - 220):m.end() + 220]))
    # collapse overlapping duplicates
    seen, uniq = set(), []
    for c in out:
        k = c[200:260]
        if k not in seen:
            seen.add(k); uniq.append(c)
    return uniq

def main(out, specs):
    res = {"window_chars": WIN, "corpora": {}, "hits": []}
    for spec in specs:
        name, d = spec.split("=", 1)
        files = [f for f in sorted(os.listdir(d)) if f.endswith(".txt")]
        res["corpora"][name] = {"docs": len(files), "Mchars": 0.0}
        for fn in files:
            t = open(os.path.join(d, fn), errors="ignore").read()
            res["corpora"][name]["Mchars"] += len(t) / 1e6
            training = name == "stargate_et" and "TRAINING" in fn.upper()
            for kind, ra in (("contact", CONTACT), ("power", POWER)):
                for ctx in scan(t, ra, NH):
                    fr = "TRAINING" if training else frame(ctx)
                    res["hits"].append({"corpus": name, "doc": fn, "kind": kind, "frame": fr, "ctx": ctx})
        res["corpora"][name]["Mchars"] = round(res["corpora"][name]["Mchars"], 2)
    tab = collections.Counter((h["corpus"], h["kind"], h["frame"]) for h in res["hits"])
    res["table"] = {"|".join(k): v for k, v in sorted(tab.items())}
    json.dump(res, open(out, "w"), indent=1)
    for k, v in sorted(tab.items()):
        print("\t".join(k), v)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
