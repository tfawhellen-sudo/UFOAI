"""STARGATE (CIA-RDP96 series) -- were non-human 'contact' targets ever operational?

Input: archive.org advancedsearch JSON for identifier:CIA-RDP96* (identifier + title, 12,234 rows).
Series in the titles: 3-digit target numbers ('238 MARS (TRAINING)') are the training-target
series; 4-digit numbers 78xx-95xx ('8808 CRV SESSION ...') are operational project numbers.
Counts ET/UFO/Mars-titled records in each series and the binomial tail of the training share
against the base rate.  Titles are a proxy: a record whose title does not name its target is
invisible here, so 0 operational ET titles bounds, not proves, the operational count.
Usage: python -I stargate_et.py rdp96.json out.json
"""
import json, re, sys
from math import comb

def title(x):
    t = x.get("title", ""); return " ".join(t) if isinstance(t, list) else t

ET = re.compile(r"\bUFO'?S?\b|EXTRATERRESTRIAL|\bALIENS?\b|\bMARS\b|\bMARTIAN|\bE\.?T\.?\b|CHANNELED|MIDWAYER")
def is_et(t): return "AVENIR" not in t and not re.search(r"\bET AL\b", t) and bool(ET.search(t))
def is_train(t): return bool(re.search(r"\bTRAINING\b", t, re.I))

def tail(n, k, p): return sum(comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))

def main(src, out):
    T = [(x["identifier"], title(x)) for x in json.load(open(src))["response"]["docs"]]
    three = [(i, t) for i, t in T if re.match(r"^\d{3}\s", t)]
    four = [(i, t) for i, t in T if re.match(r"^(7[89]|8\d|9[0-5])\d{2}\b", t)]
    et = [(i, t) for i, t in T if is_et(t)]
    p_all = sum(is_train(t) for _, t in T) / len(T)
    k = sum(is_train(t) for _, t in et)
    res = {"records": len(T), "training_share_all_titles": round(p_all, 4),
           "series_3digit": {"records": len(three), "training": sum(is_train(t) for _, t in three), "et_titled": sum(is_et(t) for _, t in three)},
           "series_4digit_operational": {"records": len(four), "training": sum(is_train(t) for _, t in four), "et_titled": sum(is_et(t) for _, t in four),
                                         "project_numbers": len({t[:4] for _, t in four})},
           "et_titled": [{"id": i, "title": t, "training": is_train(t)} for i, t in et],
           "et_training": k, "binomial_tail_vs_all_titles": tail(len(et), k, p_all)}
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "et_titled"}, indent=1))
    for r in res["et_titled"]: print(" ", "T" if r["training"] else "-", r["id"], r["title"])

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
