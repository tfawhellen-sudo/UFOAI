"""Task 4.4 linguistic archaeology: acronyms, codename candidates and corpus embeddings.

1. ACRONYMS   every 'Long Form (ACR)' / 'ACR (Long Form)' expansion, and acronyms used in >= 3
              documents that are never expanded anywhere in the corpus.
2. CODENAMES  DoD unclassified nicknames are two ordinary words written in capitals (KONA BLUE,
              GRILL FLAME).  Candidate = an ALL-CAPS word pair whose words both occur in lower
              case elsewhere (ordinary words), whose pair is written in capitals >= 80% of the
              time, outside a stoplist of markings/headers.  Plus 'Project/Operation/Program X'.
              Candidates are compared with the 29-entry codename index.  A candidate is a LEAD:
              it is read before it is called a programme.
3. EMBEDDINGS PPMI (context-distribution smoothing 0.75, window 4) + truncated SVD (k=150) on the
              same corpus; nearest neighbours of seed terms.  ~3.5M OCR tokens is small and noisy:
              neighbours are leads, not findings.
Usage: python -I terminology_mining.py OUT.json CODENAME_INDEX.json TITLES.json NAME=DIR [...]
"""
import os, re, sys, json, collections
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import svds

STOP = set("""UNCLASSIFIED SECRET CONFIDENTIAL TOP OFFICIAL USE ONLY FOUO NOFORN REL FVEY ORCON CUI
APPROVED RELEASE PAGE PAGES DEPARTMENT DEFENSE AIR FORCE ARMY NAVY MARINE CORPS UNITED STATES
FEDERAL BUREAU INVESTIGATION INTELLIGENCE AGENCY CENTRAL OFFICE FLYING SAUCER SAUCERS UNIDENTIFIED
OBJECT OBJECTS AERIAL ANOMALOUS PHENOMENA PHENOMENON REPORT REPORTS MEMORANDUM SUBJECT FROM DATE THE
AND FOR WITH NOT THIS THAT ARE WAS WERE HAS HAVE BEEN OF TO IN ON BY AT AS OR AN IS IT BE NO YES
INFORMATION RECORD RECORDS FILE FILES DOCUMENT DOCUMENTS REFERENCE TABLE FIGURE SECTION CHAPTER
JANUARY FEBRUARY MARCH APRIL MAY JUNE JULY AUGUST SEPTEMBER OCTOBER NOVEMBER DECEMBER NEW YORK
CALIFORNIA TEXAS WASHINGTON VIRGINIA FLORIDA MEXICO NEVADA UTAH OHIO COLORADO ARIZONA NATIONAL
SECURITY SCIENCE SCIENTIFIC TECHNICAL TECHNOLOGY RESEARCH PROGRAM PROJECT PROGRAMS PROJECTS
COMMAND HEADQUARTERS BASE FIELD DIVISION SQUADRON WING GROUP STATION CENTER CENTRE LABORATORY
SYSTEM SYSTEMS ANALYSIS SUMMARY CONTENTS INTRODUCTION CONCLUSION CONCLUSIONS APPENDIX ANNEX
ENCLOSURE ATTACHMENT DIRECTOR SPECIAL AGENT CHARGE ATTENTION ROUTINE PRIORITY IMMEDIATE ACTION
MESSAGE CABLE SENT RECEIVED COPY COPIES FORM STANDARD GOVERNMENT PRINTING HONORABLE SENATOR HOUSE
REPRESENTATIVES CONGRESS COMMITTEE SENATE BLUE BOOK SIGN GRUDGE NORTH SOUTH EAST WEST AMERICA
AMERICAN SOVIET UNION RUSSIA RUSSIAN FRENCH FRANCE BRITISH ENGLAND TIME LOCAL ZULU HOURS MINUTES
DESCRIPTION LOCATION SIGHTING SIGHTINGS WITNESS WITNESSES OBSERVER OBSERVERS OBSERVATION""".split())

def norm(t):
    t = re.sub(r"non[\s-]+human", "nonhuman", t, flags=re.I)
    return t

def tokens(t):
    return re.findall(r"[a-z][a-z\-]{1,24}", norm(t).lower())

def main(out, idx_p, titles_p, specs):
    docs = {}
    for spec in specs:
        name, d = spec.split("=", 1)
        for f in sorted(os.listdir(d)):
            if f.endswith(".txt"): docs[name + "/" + f] = open(os.path.join(d, f), errors="ignore").read()
    known = {k.lower() for k in json.load(open(idx_p))["codenames"]}
    titles = json.load(open(titles_p))
    # ---------------------------------------------------------------- 1 acronyms
    exp = collections.defaultdict(collections.Counter); used = collections.Counter()
    rx1 = re.compile(r"((?:[A-Z][a-zA-Z\-]+[ ,&/]+(?:of |and |for |the |on |to )*){1,7}[A-Z][a-zA-Z\-]+)\s*\(([A-Z][A-Z0-9&/\-]{1,8})\)")
    for k, t in docs.items():
        t1 = re.sub(r"\s+", " ", t)
        for m in rx1.finditer(t1):
            long, ac = m.group(1).strip(), m.group(2)
            initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", long) if w.lower() not in ("of", "and", "for", "the", "on", "to")).upper()
            if initials.endswith(re.sub(r"[^A-Z]", "", ac)[:len(initials)]) or re.sub(r"[^A-Z]", "", ac) in initials:
                exp[ac][long] += 1
        for ac in set(re.findall(r"\b[A-Z]{3,6}\b", t)): used[ac] += 1
    undefined = [(a, n) for a, n in used.most_common() if n >= 3 and a not in exp and a not in STOP][:120]
    acr = {"expanded": {a: c.most_common(3) for a, c in sorted(exp.items(), key=lambda x: -sum(x[1].values()))[:400]},
           "undefined_used_in_3plus_docs": undefined}
    # ---------------------------------------------------------------- 2 codenames
    lower_words = collections.Counter(w for t in docs.values() for w in re.findall(r"\b[a-z]{3,12}\b", t))
    up = collections.Counter(); updocs = collections.defaultdict(set)
    pair = re.compile(r"\b(?=([A-Z]{3,12})[ \t]+([A-Z]{3,12})\b)")
    srcs = list(docs.items()) + [("stargate_titles/" + str(i), t) for i, t in enumerate(titles)]
    for k, t in srcs:
        for m in pair.finditer(t):
            a, b = m.group(1), m.group(2)
            if a in STOP or b in STOP: continue
            if lower_words[a.lower()] < 3 or lower_words[b.lower()] < 3: continue
            up[(a, b)] += 1; updocs[(a, b)].add(k.split("/")[0] if k.startswith("stargate_titles") else k)
    alltext = ("\n".join(docs.values()) + "\n" + "\n".join(titles)).lower()
    anycase = collections.Counter((m.group(1), m.group(2)) for m in re.finditer(r"\b(?=([a-z]{3,12})[ \t]+([a-z]{3,12})\b)", alltext))
    cands = []
    for (a, b), n in up.items():
        if n < 2: continue
        tot = anycase[(a.lower(), b.lower())]
        ratio = n / max(tot, 1)
        if ratio < 0.8: continue
        nm = (a + " " + b).lower()
        cands.append({"pair": a + " " + b, "upper_count": n, "any_case": tot, "upper_ratio": round(ratio, 2),
                      "docs": len(updocs[(a, b)]), "in_index": nm in known, "example_docs": sorted(updocs[(a, b)])[:3]})
    cands.sort(key=lambda c: (-c["docs"], -c["upper_count"]))
    proj = collections.Counter()
    for k, t in srcs:
        for m in re.finditer(r"\b(?:Project|PROJECT|Operation|OPERATION|Program|PROGRAM|Programme)\s+([A-Z][A-Za-z\-]{2,20}(?:\s+[A-Z][A-Z\-]{2,20})?)", t):
            proj[m.group(1).strip()] += 1
    # ---------------------------------------------------------------- 3 embeddings
    vocab = collections.Counter(); seqs = []
    for t in docs.values():
        s = tokens(t); seqs.append(s); vocab.update(s)
    words = [w for w, c in vocab.items() if c >= 15]; wid = {w: i for i, w in enumerate(words)}; V = len(words)
    rows, cols = [], []
    for s in seqs:
        ids = np.array([wid[w] for w in s if w in wid], dtype=np.int64)
        for off in range(1, 5):
            if len(ids) > off:
                rows.append(ids[:-off]); cols.append(ids[off:]); rows.append(ids[off:]); cols.append(ids[:-off])
    r = np.concatenate(rows); c = np.concatenate(cols)
    key, cnt = np.unique(r * V + c, return_counts=True)
    M = coo_matrix((cnt.astype(float), (key // V, key % V)), shape=(V, V)).tocsr()
    tot = M.sum(); rs = np.asarray(M.sum(1)).ravel(); cs = np.asarray(M.sum(0)).ravel() ** 0.75; cs = cs / cs.sum()
    Mc = M.tocoo(); pmi = np.log((Mc.data / tot) / ((rs[Mc.row] / tot) * cs[Mc.col])); keep = pmi > 0
    P = coo_matrix((pmi[keep], (Mc.row[keep], Mc.col[keep])), shape=(V, V)).tocsr()
    U, Sg, _ = svds(P, k=150); E = U * np.sqrt(Sg); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
    seeds = ["kona", "biologics", "nonhuman", "retrieval", "crash", "legacy", "reverse", "exploitation", "consciousness",
             "telepathy", "contact", "communication", "liaison", "compartment", "unacknowledged", "codeword", "nickname",
             "implants", "hitchhiker", "anomalous", "ufo", "uap"]
    nbrs = {}
    for sd in seeds:
        if sd in wid:
            sims = E @ E[wid[sd]]; o = np.argsort(-sims)[1:13]
            nbrs[sd] = [(words[i], round(float(sims[i]), 3), int(vocab[words[i]])) for i in o]
    res = {"n_docs": len(docs), "n_titles": len(titles), "acronyms": acr, "codename_candidates": cands[:300],
           "project_operation_names": proj.most_common(150), "embedding": {"vocab": V, "tokens": int(sum(vocab.values())), "dim": 150, "neighbours": nbrs}}
    json.dump(res, open(out, "w"), indent=1)
    print("docs", len(docs), "titles", len(titles), "acronyms expanded", len(exp), "undefined(3+ docs)", len(undefined))
    print("codename candidates", len(cands), "of which in index", sum(c["in_index"] for c in cands))
    for c in cands[:70]: print("  ", c["pair"].ljust(28), c["docs"], c["upper_count"], c["upper_ratio"], "IDX" if c["in_index"] else "", c["example_docs"][:2])
    print("project/operation names:", proj.most_common(60))
    print("vocab", V)
    for k, v in nbrs.items(): print(" ", k, "->", ", ".join(w for w, s, n in v))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
