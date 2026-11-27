"""Hand-coding of every contact / power hit (contact_claims.py output + the deep_terms B and C
tracks).  The codes below were assigned by reading each context in full; the rules only map
those readings back onto the hits so the result is reproducible and auditable.  Any hit the
rules do not cover is printed as UNCODED and must be read before the table is quoted.

Codes
  ORDINARY_USAGE   radio/visual contact, points of contact, FBI Liaison Section, agency contacted
                   someone, an object 'contacted earth' (landing), resin infiltration ...
  SETI_THEORY      communicating-civilisation statistics / CETI signalling theory
  CLAIM_RELAY      a contactee's, abductee's or advocate's claim, or contactee literature, held in a file
  PRESS_RELAY      a newspaper item held in a file
  TYPOLOGY         a scenario list or typology ('States that have entered into contact ...')
  CATALOGUE_LABEL  a database category count
  TRAINING_SESSION a STARGATE remote-viewing session filed as TRAINING
  OWN_VOICE_CLAIM  the record itself asserts contact with, or power held by, non-human intelligence
Usage: python -I contact_handcode.py claims.json deep_terms.json out.json
"""
import json, re, sys, collections

RULES = [  # (code, doc regex, context regex)
    ("TRAINING_SESSION", r"CIA-RDP96", r"."),
    ("TYPOLOGY", r"UFO's_and_Defense", r"States that have entered|official and peaceful|contacts presuppose|Are they seeking to make contact|technology transfers were supposedly"),
    ("ORDINARY_USAGE", r"UFO's_and_Defense", r"infiltrated1? by the CIA"),
    ("ORDINARY_USAGE", r"Flying-Discs-1949", r"contacted earth"),
    ("CLAIM_RELAY", r"62-HQ-83894|Newark", r"contactee|Space Beings|SPACE PEOPLE|space people|Van Tassel|VAN TASSEL|ADAMSKI|Swan|channel contacts|we have infiltrated your|Monka|communicate rel ation|communication .{0,6}with extraterrestrial"),
    ("CLAIM_RELAY", r"62-HQ-83894", r"JANAP|Keyhoe"),
    ("PRESS_RELAY", r"62-HQ-83894|Newark", r"Bateman|have had contact with our Earth|Cosmic Reminiscences"),
    ("ORDINARY_USAGE", r"62-HQ-83894", r"radt?\s?i?o contact|LIAISON|Liaison|liaison"),
    ("ORDINARY_USAGE", r"Gemini|USG-UAP-D001|Air-Materiel|D144|FD-1057|CIA-UAP-003|D143|D172|D117|D119|D120", r"."),
    ("SETI_THEORY", r"D127|D167", r"communicat|SETI|CETI|contact with potential"),
    ("TYPOLOGY", r"D167", r"repeated contact"),
    ("CATALOGUE_LABEL", r"D169", r"Contact Events"),
    ("CLAIM_RELAY", r"D171", r"abducted"),
    ("ORDINARY_USAGE", r".", r"\bliaison\b|Liaison|LIAISON"),
]

def code(doc, ctx):
    for c, rd, rc in RULES:
        if re.search(rd, doc) and re.search(rc, ctx, re.I):
            return c
    return "UNCODED"

def main(claims_p, deep_p, out):
    rows = []
    cl = json.load(open(claims_p))
    for h in cl["hits"]:
        if h["frame"] in ("PHYSICS_TERM",): c = "ORDINARY_USAGE"
        else: c = code(h["doc"], h["ctx"])
        rows.append({"source": "contact_claims", "corpus": h["corpus"], "doc": h["doc"], "kind": h["kind"],
                     "auto_frame": h["frame"], "hand_code": c, "ctx": h["ctx"][60:420]})
    dt = json.load(open(deep_p))["hits"]
    for key, items in dt.items():
        if not key.startswith(("B_maintained_contact", "C_entities_in_power")): continue
        for x in items:
            ctx = x.get("context", "")
            c = code(x.get("doc", ""), ctx)
            rows.append({"source": "deep_terms", "corpus": x.get("corpus"), "doc": x.get("doc"), "kind": key,
                         "auto_frame": x.get("frame"), "hand_code": c, "ctx": re.sub(r"\s+", " ", ctx)[100:460]})
    tab = collections.Counter((r["source"], r["kind"].split("||")[0], r["hand_code"]) for r in rows)
    auto = collections.Counter((r["source"], r["kind"].split("||")[0], r["auto_frame"]) for r in rows)
    json.dump({"table_hand": {"|".join(k): v for k, v in sorted(tab.items())},
               "table_auto": {"|".join(k): v for k, v in sorted(auto.items())}, "rows": rows}, open(out, "w"), indent=1)
    for k, v in sorted(tab.items()): print("\t".join(k), v)
    unc = [r for r in rows if r["hand_code"] == "UNCODED"]
    print("UNCODED", len(unc))
    for r in unc[:40]: print("  ?", r["doc"][:60], "|", r["kind"][:40], "|", r["ctx"][:260])

if __name__ == "__main__":
    main(*sys.argv[1:4])
