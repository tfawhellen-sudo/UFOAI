#!/usr/bin/env python3
"""One-area-per-report assignment of the 37 AAWSAP DIRDs (session 5).

Replaces the title-keyword coverage map in aawsap_contract_audit.py section 3,
which put 37 reports into 52 area slots and is flagged "not to be quoted".

Area list: the SOO itself, D110 section 3(a), 18 July 2008, which is readable
(D182's copy of the same list is OCR-destroyed):
  1 lift  2 propulsion  3 control  4 power generation
  5 spatial/temporal translation  6 materials  7 configuration, structure
  8 signature reduction (optical, IR, RF, acoustic)  9 human interface
  10 human effects  11 armament (RF and DEW)
  12 other peripheral areas in support of (1-11)
D186 p.1 (Dec 2010) renames area 12 "technology integration".

Method
------
* PRIMARY area is read from each report's own statement of purpose (its
  Summary / Introduction / Preface / scope sentence), not from its title.
* Each assignment carries the framing sentence it rests on.  The script
  VERIFIES that string is present in the vaulted text (whitespace-normalised),
  so no assignment rests on a quote that is not in the document.
* ALT records the one competing area where the framing genuinely supports two.
  Counts are reported as primary, plus the [min, max] each area can reach if
  every contested report is flipped to its ALT.  That range is the honest
  uncertainty of a single-reader assignment.
* Rater B, fully mechanical and independent of the reading: argmax of the
  session-4 area regexes over each report's first 15,000 characters of body
  text.  Cohen's kappa between reading and rater B, with a bootstrap 95% CI
  over reports, measures how much of the assignment a keyword rule reproduces.

Usage:  python3 -I omega/dird_area_assignment.py
Writes: evidence_vault/01_PURSUE_PRIMARY/dird_area_assignment.json
"""
import glob
import json
import os
import random
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIRD = os.path.join(ROOT, "evidence_vault/01_PURSUE_PRIMARY/AAWSAP_DIRDs")
OUT = os.path.join(ROOT, "evidence_vault/01_PURSUE_PRIMARY/dird_area_assignment.json")

AREAS = ["lift", "propulsion", "control", "power generation",
         "spatial/temporal translation", "materials", "configuration/structure",
         "signature reduction", "human interface", "human effects", "armament",
         "other peripheral"]

# id: (primary, alt or None, framing string that must occur in the text)
A = {
 "D117": ("materials", None, "In structural applications, therefore, metallic glasses"),
 "D118": ("materials", None, "Programmable Matter smart materials"),
 "D119": ("materials", "human interface", "Biomaterials are metals, ceramics, polymers, glasses, carbons, and composite materials intended to interface with biological systems"),
 "D120": ("materials", "configuration/structure", "a more concise discussion of materials advances, challenges, and opportunities"),
 "D121": ("armament", None, "overview of the major types of high-power microwave (HPM) sources"),
 "D122": ("signature reduction", None, "Invisibility cloaking has recently become a subject of science and technology"),
 "D123": ("propulsion", None, "extremely attractive fuel for aerospace propulsion"),
 "D124": ("configuration/structure", "propulsion", "The remainder of this report will focus on the characteristics of t his class of lifting body"),
 "D125": ("power generation", "propulsion", "on the route to fusion power"),
 "D126": ("propulsion", "power generation", "spaceships driven by deuterium thermonuclear reactions"),
 "D127": ("other peripheral", None, "Search for Extraterrestrial Intelligence"),
 "D128": ("human effects", None, "they suffered medical signs and symptoms"),
 "D129": ("other peripheral", "materials", "A promising nanoscale technology known as spintronics"),
 "D130": ("human interface", None, "eliminating required electromechanical human-machine interfaces"),
 "D131": ("lift", "propulsion", "laboratory-scale manipulation of gravity"),
 "D132": ("propulsion", "spatial/temporal translation", "might be engineered to provide energy/thrust for future space vehicles"),
 "D133": ("other peripheral", "spatial/temporal translation", "could be used for sending observer-to"),
 "D134": ("other peripheral", None, "the solitary maverick inventor"),
 "D135": ("propulsion", "lift", "for the purpose of aerospace propulsion"),
 "D136": ("human interface", "human effects", "Biomedical sensors and implantable devices"),
 "D137": ("armament", None, "no deployment of any high-energy weapons"),
 "D138": ("propulsion", "spatial/temporal translation", "a dramatic shift in the traditional approach to spacecraft propulsion is necessary"),
 "D139": ("spatial/temporal translation", None, "faster-than-light (FTL) interstellar travel via traversable wormholes"),
 "D140": ("other peripheral", None, "high-frequency gravitational wave (HFGW) generators"),
 "D141": ("materials", "signature reduction", "this study will be on electromagnetic and optical metamaterials"),
 "D142": ("power generation", None, "the electromagnetic quantum vacuum"),
 "D143": ("propulsion", "lift", "we envision a Lightcraft Earth-to-Orbit (ETO) transportation system"),
 "D144": ("human interface", "control", "Lessons of human-machine interface"),
 "D145": ("propulsion", None, "Space exploration is limited by existing propulsion technology"),
 "D146": ("propulsion", None, "applying fusion to propulsion"),
 "D147": ("power generation", None, "are energy storage devices capable of extremely rapid charge and discharge"),
 "D148": ("signature reduction", "other peripheral", "Explore the Detection of Vehicles Designed To Be Undetectable"),
 "D149": ("propulsion", "lift", "novel propulsion concepts utilizing plasmas"),
 "D150": ("other peripheral", "control", "Powerful onboard computing hardware is a desired option"),
 "D151": ("control", "human interface", "Piloting these multiple craft"),
 "D152": ("propulsion", None, "their use for propulsion by reducing the inertia of matter"),
 "D153": ("propulsion", "spatial/temporal translation", "Future aerospace vehicles could have an advanced propulsion system"),
}

# session-4 regexes (aawsap_contract_audit.py AREAS), renamed to the SOO labels
RX = {
 "lift": r"lift|lightcraft|magnetohydro|mhd|air.?breathing",
 "propulsion": r"propulsion|positron|fusion.*propuls|nuclear propuls|warp|negative mass|aneutronic",
 "control": r"control|cockpit|cognitive limits|automation|unmanned spacecraft",
 "power generation": r"power|energy|ultracapacitor|vacuum energy|extracting energy|fusion",
 "spatial/temporal translation": r"wormhole|stargate|space.?time|spacetime|metric engineering|extra.?dimension|teleport",
 "materials": r"material|metallic glass|programmable matter|metamaterial|biomaterial|spintronic",
 "configuration/structure": r"structur|configurat|platform",
 "signature reduction": r"invisibilit|cloak|signature|stealth|detection and high.?resolution",
 "human interface": r"human interface|limb.?operated|controlling external|cockpit|biosensor|biomems",
 "human effects": r"human biological|biological tissue|field effects|acute and subacute",
 "armament": r"laser|weapon|microwave|high.?energy laser|pulsed.?high.?power|directed energy",
 "other peripheral": r"drake|maverick|quantum comput|quantum tomography|entanglement|gravitational wave|gravity",
}
RX = {k: re.compile(v, re.I) for k, v in RX.items()}


def norm(s):
    return re.sub(r"\s+", " ", s)


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n / n
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po


def main():
    files = {re.search(r"D1\d\d", os.path.basename(f)).group(0): f
             for f in glob.glob(os.path.join(DIRD, "*"))}
    assert sorted(files) == sorted(A), (sorted(set(files) ^ set(A)))
    bad = []
    rows = []
    for d in sorted(A):
        prim, alt, quote = A[d]
        assert prim in AREAS and (alt is None or alt in AREAS), d
        t = norm(open(files[d], errors="replace").read())
        ok = norm(quote) in t
        if not ok:
            bad.append(d)
        # rater B: keyword argmax over body text (skip the first 1,500 chars of
        # DIA boilerplate / title page)
        body = t[1500:16500]
        sc = {k: len(rx.findall(body)) for k, rx in RX.items()}
        top = max(sc.values())
        b = [k for k in AREAS if sc[k] == top][0] if top else "other peripheral"
        rows.append(dict(id=d, primary=prim, alt=alt, framing=quote,
                         framing_verified=ok, raterB=b, raterB_scores=sc,
                         fy="FY2009" if d <= "D142" else "FY2010",
                         file=os.path.basename(files[d])))
    if bad:
        print("FRAMING STRINGS NOT FOUND:", bad)
        sys.exit(1)

    prim = Counter(r["primary"] for r in rows)
    lo, hi = {}, {}
    for a in AREAS:
        fixed = sum(1 for r in rows if r["primary"] == a and not r["alt"])
        lose = sum(1 for r in rows if r["primary"] == a and r["alt"])
        gain = sum(1 for r in rows if r["alt"] == a)
        lo[a], hi[a] = fixed, fixed + lose + gain
    contested = [r["id"] for r in rows if r["alt"]]

    ka, po = kappa([r["primary"] for r in rows], [r["raterB"] for r in rows])
    # agreement allowing rater B to hit either primary or alt
    po_alt = sum(r["raterB"] in (r["primary"], r["alt"]) for r in rows) / len(rows)
    rng = random.Random(20261126)
    boots = []
    for _ in range(10000):
        s = [rng.choice(rows) for _ in rows]
        boots.append(kappa([r["primary"] for r in s], [r["raterB"] for r in s])[0])
    boots.sort()
    ci = (boots[249], boots[9749])

    # session-4 title map, for the inflation figure
    old = json.load(open(os.path.join(ROOT, "evidence_vault/01_PURSUE_PRIMARY/aawsap_contract_audit.json")))["area_coverage"]
    old_n = sum(len(v) for v in old.values())

    by_fy = {fy: Counter(r["primary"] for r in rows if r["fy"] == fy) for fy in ("FY2009", "FY2010")}

    print(f"37 DIRDs, framing strings verified: {sum(r['framing_verified'] for r in rows)}/37")
    print(f"contested (two-area) reports: {len(contested)}  {' '.join(contested)}\n")
    print(f"{'area (SOO D110 s3(a))':32s} {'primary':>7s} {'range':>8s} {'FY09':>5s} {'FY10':>5s}")
    for a in AREAS:
        print(f"{a:32s} {prim[a]:7d}   [{lo[a]},{hi[a]}] {by_fy['FY2009'][a]:5d} {by_fy['FY2010'][a]:5d}")
    print(f"\nsession-4 title map: {old_n} area slots for 37 reports ({old_n/37:.2f} per report)")
    print(f"rater B (keyword argmax) vs reading: agreement {po:.3f}, "
          f"kappa {ka:.3f} (95% bootstrap CI {ci[0]:.3f} to {ci[1]:.3f}); "
          f"agreement counting ALT {po_alt:.3f}")
    dis = [(r["id"], r["primary"], r["raterB"]) for r in rows
           if r["raterB"] not in (r["primary"], r["alt"])]
    print(f"rater B disagreements outside primary/alt: {len(dis)}")
    for x in dis:
        print("   ", *x)
    json.dump(dict(
        areas_source="D110 SOO s3(a), 18 Jul 2008; area 12 renamed 'technology integration' in D186 p.1",
        rows=rows, primary_counts=dict(prim), range_min=lo, range_max=hi,
        contested=contested, by_fy={k: dict(v) for k, v in by_fy.items()},
        raterB=dict(agreement=po, kappa=ka, kappa_ci95=ci, agreement_with_alt=po_alt,
                    disagreements=dis),
        session4_title_map_slots=old_n),
        open(OUT, "w"), indent=1)
    print("\nwrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
