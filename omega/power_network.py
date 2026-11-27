"""Task 4.3 power network: PUBLIC programmes, organisations and funding records only.

No person is a node.  Two edge layers:
  co_doc   : two organisations named in the same released document (530 docs: PURSUE 286,
             CIA UFO collection 223, STARGATE ET-titled sessions 17, Kona Blue release 2,
             AIR 1995 STARGATE evaluation 1).  Weight = documents; association = PMI.
  record   : a relationship a primary record states, with the record cited (contract CLINs,
             AARO's Kona Blue note, D188 DIRD affiliations, AIR 1995).
Questions it answers:
  Q1 which organisations bridge otherwise separate clusters (betweenness on the co_doc layer)?
  Q2 do the documents that use the 2023 insider vocabulary in their own voice (contact_terms)
     sit in one community or spread across independent agencies?  'Circular reporting' (AARO)
     predicts one community; a coordinated multi-agency programme predicts several.
Usage: python -I power_network.py OUT.json AIR_TXT NAME=DIR [NAME=DIR ...]
"""
import os, re, sys, json, math, itertools, collections
import networkx as nx

ORG = {
 "DIA": r"Defense\s+Intelligence\s+Agency|\bDIA\b", "CIA": r"Central\s+Intelligence\s+Agency|\bCIA\b",
 "FBI": r"Federal\s+Bureau\s+of\s+Investigation|\bFBI\b", "NSA": r"National\s+Security\s+Agency|\bNSA\b",
 "NRO": r"National\s+Reconnaissance\s+Office|\bNRO\b", "NGA": r"National\s+Geospatial|\bNGA\b",
 "DHS": r"Homeland\s+Security|\bDHS\b", "DOE/AEC": r"Department\s+of\s+Energy|\bDOE\b|Atomic\s+Energy\s+Commission|\bAEC\b",
 "NASA": r"\bNASA\b|National\s+Aeronautics", "USAF": r"\bU\.?\s?S\.?\s?A\.?\s?F\.?\b|Air\s+Force",
 "US Army": r"\bArmy\b|INSCOM", "US Navy": r"\bNavy\b|\bONR\b|Office\s+of\s+Naval\s+Research",
 "OSD/DoD": r"Department\s+of\s+Defense|\bDoD\b|\bOSD\b|Secretary\s+of\s+Defense",
 "AARO": r"\bAARO\b|All-?\s?[Dd]omain\s+Anomaly", "UAPTF": r"\bUAPTF\b|UAP\s+Task\s+Force",
 "Congress": r"\bCongress(?:ional)?\b|\bSenate\b|House\s+of\s+Representatives",
 "Bigelow Aerospace": r"Bigelow", "BAASS": r"\bBAASS\b|Bigelow\s+Aerospace\s+Advanced\s+Space\s+Studies",
 "AAWSAP/AATIP": r"\bAAWSAP\b|\bAATIP\b|Advanced\s+Aerospace\s+Weapon|Advanced\s+Aerospace\s+Threat",
 "NIDS": r"\bNIDS\b|National\s+Institute\s+for\s+Discovery\s+Science", "MUFON": r"\bMUFON\b|Mutual\s+UFO\s+Network",
 "NICAP": r"\bNICAP\b|National\s+Investigations\s+Committee", "APRO": r"\bAPRO\b|Aerial\s+Phenomena\s+Research",
 "CUFOS": r"\bCUFOS\b|Center\s+for\s+UFO\s+Studies", "SRI": r"\bSRI\b|Stanford\s+Research\s+Institute",
 "SAIC": r"\bSAIC\b|Science\s+Applications\s+International", "AIR": r"American\s+Institutes\s+for\s+Research",
 "Sandia": r"Sandia", "Los Alamos": r"Los\s+Alamos|\bLANL\b", "Lockheed": r"Lockheed", "Boeing": r"Boeing",
 "Northrop": r"Northrop|Northrup", "Raytheon": r"Raytheon", "Battelle": r"Battelle", "EarthTech": r"Earth\s*Tech",
 "Skinwalker/Utah ranch": r"Skinwalker|Utah\s+[Rr]anch", "Project Blue Book": r"Blue\s+Book",
 "GEPAN/GEIPAN/CNES": r"\bGE(?:I)?PAN\b|\bCNES\b", "COMETA": r"\bCOMETA\b",
 "Robertson Panel": r"Robertson\s+Panel", "Condon/Colorado": r"Condon|University\s+of\s+Colorado",
}
# Relationships stated by primary records (source cited on every edge).
RECORD_EDGES = [
 ("DIA", "BAASS", "contract", "AAWSAP base year CLINs 0001-0004 $8,827,000; option year 1 CLINs 1001-1005 $9,435,900 (D111, D113 P00002; omega/reports/aawsap_contract_audit.md)"),
 ("Congress", "AAWSAP/AATIP", "funding", "AARO 'History and Origin of KONA BLUE': AAWSAP/AATIP 'funded through congressional earmarks'"),
 ("Bigelow Aerospace", "AAWSAP/AATIP", "prime contractor", "AARO Kona Blue note: 'Bigelow Aerospace ... served as the primary contractor executing funds'"),
 ("Bigelow Aerospace", "BAASS", "parent", "BAASS = Bigelow Aerospace Advanced Space Studies (D168 PMP letterhead)"),
 ("DIA", "AAWSAP/AATIP", "managed / terminated", "AARO Kona Blue note: managed by DIA 2009-2012; 'DIA terminated the program due to a cited lack of merit'"),
 ("AAWSAP/AATIP", "DHS", "proposed successor (KONA BLUE)", "AARO Kona Blue note: AAWSAP/AATIP individuals 'advocated for DHS to take the effort over'; PSAP 2011, disapproved six months later; 'never received any materials or funding'"),
 ("AARO", "DHS", "joint declassification", "AARO Kona Blue note: declassified 'in partnership between DoD and DHS'"),
 ("MUFON", "BAASS", "reports prepared for", "D166 'MUFON Reports Prepared for BAASS', November 2008"),
 ("BAASS", "Skinwalker/Utah ranch", "site investigation", "D174 'Utah Ranch Investigation Report', April 2010"),
 ("EarthTech", "AAWSAP/AATIP", "DIRD authorship (4 of 26 listed)", "D188 list of DIRD titles and affiliations (aawsap_contract_audit.json d188_reconciliation)"),
 ("Northrop", "AAWSAP/AATIP", "DIRD authorship (1 of 26 listed)", "D188 (affiliation printed 'Northrup')"),
 ("SRI", "STAR GATE", "research contractor (1970s-1980s)", "AIR 1995 evaluation: 'government sponsored research conducted at Stanford Research Institute, later known as SRI International'"),
 ("SAIC", "STAR GATE", "research contractor (later era)", "AIR 1995: '... and at Science Applications International Corporation, known as SAIC'"),
 ("AIR", "STAR GATE", "evaluation (1995)", "AIR 1995: remote viewing 'failed to produce actionable intelligence'; 'continued use ... is not warranted'"),
 ("CIA", "STAR GATE", "custodian / release", "STAR GATE records released in the CIA-RDP96 series (12,234 items on archive.org)"),
]

def main(out, air, specs):
    docs = {}
    for spec in specs:
        name, d = spec.split("=", 1)
        for f in sorted(os.listdir(d)):
            if f.endswith(".txt"): docs[name + "/" + f] = open(os.path.join(d, f), errors="ignore").read()
    docs["air1995/" + os.path.basename(air)] = open(air, errors="ignore").read()
    mentions = {k: {o for o, rx in ORG.items() if re.search(rx, t)} for k, t in docs.items()}
    N = len(docs); df = collections.Counter(o for s in mentions.values() for o in s)
    co = collections.Counter()
    for s in mentions.values():
        for a, b in itertools.combinations(sorted(s), 2): co[(a, b)] += 1
    G = nx.Graph()
    for o, c in df.items():
        if c >= 3: G.add_node(o, docs=c)
    for (a, b), c in co.items():
        if a in G and b in G and c >= 2:
            pmi = math.log((c / N) / ((df[a] / N) * (df[b] / N)))
            if pmi > 0: G.add_edge(a, b, docs=c, pmi=round(pmi, 3), dist=1 / pmi)
    comms = nx.algorithms.community.greedy_modularity_communities(G, weight="pmi")
    comm_of = {o: i for i, cset in enumerate(comms) for o in cset}
    btw = nx.betweenness_centrality(G, weight="dist")
    # Q2 overlay: own-voice insider-vocabulary documents (hand-read in contact_terms / report)
    vocab_docs = [k for k in docs if re.search(r"D128|D166|D167|D168|D169|D175|kona_blue", k)]
    overlay = {k: sorted(mentions[k]) for k in vocab_docs}
    comm_hits = collections.Counter(comm_of.get(o) for k in vocab_docs for o in mentions[k] if o in comm_of)
    res = {"n_docs": N, "doc_freq": dict(df.most_common()),
           "nodes": [{"org": o, "docs": G.nodes[o]["docs"], "community": comm_of[o], "betweenness": round(btw[o], 4)} for o in G],
           "edges": [{"a": a, "b": b, **{k: v for k, v in d.items() if k != "dist"}} for a, b, d in G.edges(data=True)],
           "communities": [sorted(c) for c in comms], "record_edges": [dict(zip(("a", "b", "relation", "source"), e)) for e in RECORD_EDGES],
           "vocab_doc_orgs": overlay, "vocab_doc_community_mentions": {str(k): v for k, v in comm_hits.items()}}
    json.dump(res, open(out, "w"), indent=1)
    print("docs", N, "nodes", G.number_of_nodes(), "edges", G.number_of_edges())
    for i, c in enumerate(comms): print("community", i, sorted(c))
    print("top betweenness", sorted(((round(v, 3), k) for k, v in btw.items()), reverse=True)[:10])
    print("vocab-doc mentions by community", dict(comm_hits))
    for k, v in overlay.items(): print("  ", k[:70], v)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
