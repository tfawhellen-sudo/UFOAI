# Preregistered assay protocol for the 434-event retained-sample list

*Project Omega, 2026-11-26. Status: **DRAFT FOR REGISTRATION**. Nothing in §2–§8
has been run on outcome data. Power code: `omega/assay_protocol_power.py`
(seeded, numpy only). Output: `omega/reports/assay_protocol_power_out.json`.
Inputs: `evidence_vault/03_RETAINED_SAMPLES/priority_434.{csv,json}` and
`evidence_vault/07_PERIODICALS_PRIMARY/provenance_graph_434.json`.*

---

## 0. Bottom line

1. **No sample is in hand.** All 434 rows are `extant_status = UNVERIFIED`.
   232 list the sample type as "unspecified" and 397 mention no analysis at all.
   An assay of "the 434" is not possible. What is possible is a staged design in
   which each stage decides whether the next one runs.
2. **Five arms, five primary hypotheses.** A0 is a custody census, which
   decides which samples exist. A1 is a documentary claim-drift test, which can
   run now. A2 is a blinded lab assay of extant samples against decoys. A3 is a
   site revisit with same-day sham centres. A4 is tree-ring analysis.
3. **Power sets hard floors.** A1 needs the ROOTED and LATE_ONLY events together
   (80 pairs, not 43). A2 needs at least 10 extant samples, and 20 to detect a
   moderate effect. A3 and A4 need **at least 7 sites before any result can
   reach α = 0.01**, because a sign-flip test on 6 sites cannot go below
   P = 1/64. A3 needs 15–25 sites to be adequate. Below those floors an arm runs
   as a pilot and makes no confirmatory claim.
4. **NT-16's failures are written in as requirements.** Controls are collected
   the same day with the same procedure. Sham centres sit on the same landform.
   Every arm includes a positive control (a site with a known cause) and a
   negative-control outcome. Labs are blind and get decoys. Chain of custody is
   hash-committed.
5. **What a positive result would and would not mean.** A2 is the only arm that
   bears directly on whether material is non-terrestrial (an isotope ratio
   outside every terrestrial array, replicated blind in two labs). A positive in
   A3 or A4 means "a physical event happened at this spot". It does not mean
   NHI. A positive in A1 means the physical-trace literature grew after the
   fact. It does not mean the events didn't happen.

---

## 1. What the sample is

| quantity | value | source |
|---|---|---|
| events | 434 | `priority_434.csv` |
| extant sample confirmed | 0 | `extant_status` column |
| sample type "unspecified" | 232 | `sample_types` |
| vegetation / metal-residue / oily / soil | 105 / 64 / 45 / 31 | `sample_types` (multi-label) |
| radiation reading / tissue / photo / water | 18 / 17 / 15 / 6 | `sample_types` |
| any analysis mentioned in the record | 37 | `analysis_mentioned` |
| event year ≥ 1984 | 54 | `date` |
| provenance class ROOTED / LATE_ONLY / ABSENT | 43 / 37 / 230 | `provenance_graph_434.json` |
| custodian candidates: CUFOS, NICAP, FSR, APRO, MUFON | 167, 108, 93, 68, 46 | `custodian_candidates` |
| police/gendarmerie, LDLN, university/lab | 44, 43, 34 | same |
| Blue Book, USAF/military, GEPAN/SEPRA/GEIPAN | 17, 13, 6 | same |
| no custodian anywhere in the citation chain | 109 | same |

**Coordinates are not site locations.** All 434 rows carry 5- or 6-decimal
coordinates, but they come from the geocoder, not from field records. The
project's persistence artefact came from settlement centroids agreeing with
each other across pipelines (`HANDOFF §6`). No coordinate in this file may be
used to place a sampling point (§3.4, gate G3).

**What the analyst has already seen.** Provenance classes, catalogue counts and
the `example_context` snippets for the 187 issue→event edges are already known.
The **content of the anomaly claims** in the earliest root and in the latest
catalogue has **not** been coded. A1 is preregistered on that basis.

---

## 2. Primary hypotheses

Each has a stated prediction, a null, and a decision rule. Family-wise α is
0.05, Holm-adjusted over the five primaries, which gives α = 0.01 for the
smallest P. Every test is one-sided in the stated direction.

| # | arm | hypothesis (the direction that counts as "anomaly real" is marked †) | null model | primary statistic |
|---|---|---|---|---|
| H1 | A1 | Physical-anomaly claims are **added** after the earliest contemporaneous source more often than they are dropped (narrative accretion). † is the null result: claims are as old as the event. | Additions and drops equally likely among discordant pairs | Exact one-sided McNemar, b vs c |
| H2 | A2 | † Blind labs flag retained event samples as outside the terrestrial reference range more often than matched decoys | Flag rate is equal in event and decoy samples | One-sided Fisher exact on flag counts |
| H3 | A3 | † The trace centre shows a durable heating signature against same-day sham centres (higher χlf and χfd%, and a TL/OSL equivalent-dose deficit in the top 0–2 cm) | Exposed minus sham is symmetric around 0 across sites | Sign-flip permutation on site means, composite z |
| H4 | A3 | † The trace centre shows excess gamma activity in non-fallout nuclides against sham centres | Same as H3 | Sign-flip on site means of the summed non-fallout activity |
| H5 | A4 | † Trees within the trace radius show ring-width suppression in the event year against control trees in the same stand | Superposed-epoch index equals the placebo-year distribution | Sign-flip on site means, placebo years as a second null |

**Decision rules.**
- **Confirmed** needs all of: Holm-adjusted P < 0.05; the same direction in a
  second lab analysing the retained blind aliquot; survival when any single
  site or sample is dropped; and a clean negative-control outcome (§5.3).
- **Null** is claimed only through equivalence. The 90% CI of the mean effect
  must lie inside the bound stated in §6. A non-significant result above the
  floor of §6 that misses the bound is reported as **inconclusive**, not null.
- **No outcome-conditioned subsetting.** Subsets ("only heating-claimed cases",
  "only ROOTED") are secondary and declared in §2.1. A subset chosen after
  seeing the data is exploratory and labelled so. This is withdrawn null #3 in
  `HANDOFF §6`.

### 2.1 Declared secondary analyses
- S1 (A1): drift separately for each claim type (residue, radiation, burn,
  vegetation, animal effect, injury).
- S2 (A1): drift against lag. Does the addition rate rise with years since the
  event?
- S3 (A3): H3 restricted to cases where the earliest root reports heat, burn or
  scorch.
- S4 (A2): per sample type (metal/residue, soil, vegetation, oily).
- E1 (A0, exploratory): Do custody outcomes (extant, lost, refused, no reply)
  differ by custodian sector (government, police, civilian, university), after
  stratifying by decade? This is the falsifiable version of "the government
  keeps the samples". It is low-powered and exploratory by declaration.

---

## 3. The arms

### 3.0 A0 — custody census (runs first; decides A2)
- **Unit.** Event × custodian candidate.
- **Procedure.** One written enquiry for each custodian holding at least 3
  events, listing those events and asking for the accession number, storage
  conditions, the amount left and the transfer history. Targets, by count:
  CUFOS (167), NICAP holdings now at CUFOS (108), FSR archive (93), APRO
  remnants (68), MUFON (46), gendarmerie archives via GEIPAN/CADA, LDLN, named
  university labs (34), and NARA RG 341 for Blue Book (17). Drafted alongside
  the existing FOIA/CADA drafts. **Not sent without the owner's approval.**
- **Outcome coding.** EXTANT_ACCESSIONED, EXTANT_UNACCESSIONED, CONSUMED,
  LOST, REFUSED, NO_REPLY_90D, NEVER_HELD.
- **Preregistered expectation, for calibration only:** fewer than 10% of
  events will have an EXTANT sample. If the number of extant samples is under
  10, A2 runs as a pilot.

### 3.1 A1 — documentary claim drift (can run now)
- **Pairs.** Every event in ROOTED (43) and LATE_ONLY (37), so 80 events. For
  each one, the **earliest** corroborating issue is paired with the **latest**
  catalogue description (`description` in `priority_434.json`).
- **Coding.** Each text is coded on the codebook in §4.2 for the presence of
  each physical claim type. A pair is concordant or discordant on "any physical
  claim". b counts claims added in the later text, c counts claims dropped.
- **Blinding.** Texts go to the coders stripped of the source name, the issue
  date and the event date where possible. Coders don't know which text is the
  earlier one. Pair order is randomised with a committed seed.
- **Coders.** Two independent passes (two separate model runs with no shared
  context, or one model and one human). A human adjudicates disagreements.
  Cohen's κ must reach 0.70 or more on the first 20 pairs before the rest are
  coded. If it doesn't, the codebook is revised and the 20 are re-coded. Those
  20 are then excluded from the confirmatory test.
- **Why this matters for the rest.** If H1 is confirmed, the "sample types"
  column of the 434 is partly a later literary product. Gate G1 (§3.4) then
  restricts A2–A4 to events whose physical claim appears in the earliest root.

### 3.2 A2 — blinded lab assay of extant samples
- **Eligibility.** EXTANT samples from A0 with documented custody tier C2 or
  higher (§4.1).
- **Decoys.** Two decoys for every event sample, matched on material, decade
  and custodian where possible. Examples are soil or vegetation from the same
  archive's non-UFO holdings, slag and foundry residue for metal, and
  roadside or agricultural soil of the same region and decade from
  soil-survey archives. Decoys are repackaged into identical containers.
- **Measurements, fixed per material before shipment.**
  - Metal/residue: major and trace elements (ICP-MS); isotope ratios for
    Mg (²⁵Mg/²⁴Mg, ²⁶Mg/²⁴Mg), Fe, Ti and Pb (MC-ICP-MS); SEM-EDS for
    morphology.
  - Soil: χlf and χfd%; TL/OSL equivalent dose on quartz from the top 0–2 cm;
    organic content; gamma spectrometry.
  - Vegetation: pigments have not survived decades in storage and are not
    measured. Elemental and isotopic composition and SEM are.
- **Flag rule, written before unblinding.** A sample is FLAGGED when any
  primary measurement falls outside the 99.9% envelope of the published
  terrestrial reference array for that material. For isotopes this is the
  terrestrial mass-fractionation line ± the lab's 2σ. The labs report raw
  values; the flag is computed by script, not by the lab's judgement.
- **Replication.** Each sample is split into three aliquots: lab A, lab B, and
  an archived reserve. Lab B gets its aliquot only after lab A's raw values are
  hash-committed.

### 3.3 A3 — site revisit with same-day sham centres
- **Eligibility.** Gate G3 (location precision L3) and gate G4 (site not
  substantially altered, judged from historical aerial imagery against current
  imagery before the visit).
- **Layout per site.** One exposed centre at the documented trace. Two sham
  centres placed by a seeded random draw inside the same landform and
  land-cover polygon, 15–100 m from the trace, and not on paths, tracks or the
  vehicle access. From every centre, the same sampling plan: 5 cores at 0 m,
  and 5 at 1.5, 3 and 6 m on a transect whose bearing is drawn at random. Each
  core is split 0–2 cm and 2–10 cm.
- **Same day, same crew, same tools,** in an order randomised across centres.
  This is the NT-16 failure (controls taken 14 days later on the opposite side,
  §4.7–4.9 of the NT-16 write-up), turned into a requirement.
- **Matched-landcover off-site control.** One further centre 1–5 km away on
  the same land-cover class (shared with the Track 2 control builder,
  `omega/track2_controls.py`). It tests whether the trace site differs from its
  terrain, which the sham centres alone cannot.
- **Measurements.** As for A2 soil, plus field χ with a portable meter at
  every core point before coring.

### 3.4 Gates
| gate | condition | consequence of failing |
|---|---|---|
| G1 | The physical claim is in the earliest root (applies only if H1 is confirmed) | The event leaves A2–A4 |
| G2 | Custody tier C2 or higher | The sample leaves A2 and is reported descriptively |
| G3 | Location precision L3 (≤ 25 m from a primary sketch, photo, survey or official report) | The event leaves A3–A4 |
| G4 | No disturbance since the event (no ploughing, building, grading or fill) visible in aerial imagery | The event leaves A3 |
| G5 | At least 7 eligible sites (A3/A4) or 10 samples (A2) | The arm runs as a pilot with no confirmatory claim |

### 3.5 A4 — tree rings
- **Eligibility.** G3 sites with trees reported inside the trace radius in the
  earliest root, or visible in imagery from the event year.
- **Sampling.** Two increment cores per tree. Up to 10 trees inside the radius
  and 10 control trees of the same species in the same stand, chosen by seeded
  random draw from a tree list made before coring.
- **Measurements.** Ring width and latewood blue intensity, cross-dated
  against the regional chronology.
- **Null.** The event-year index is compared with placebo years (event year
  −10 to +10, excluding ±1) at the same trees. A local drought or frost shows
  up in both site and control trees, and the stand-level difference removes it.

---

## 4. Coding scheme

### 4.1 Event and sample codebook (A0, A2, A3)
| field | levels |
|---|---|
| `loc_precision` | L0 country/region; L1 settlement centroid; L2 ≤ 500 m (named farm, road junction); L3 ≤ 25 m (sketch with measured offsets, photo with landmarks, survey) |
| `collect_delay_days` | integer; NA if unknown |
| `collector_role` | witness, police, investigator (civilian), military, scientist, unknown |
| `control_collected` | none; later date; same day, other location; same day, same landform |
| `custody_tier` | C0 none; C1 the custodian says it is held; C2 accession number; C3 accession plus transfer log; C4 C3 plus seals or photographs at each transfer |
| `storage` | sealed glass, plastic, paper, open, unknown; temperature known (Y/N) |
| `prior_consumption` | fraction of the sample used in earlier analyses, if known |
| `custody_outcome` | A0 levels (§3.0) |
| `custodian_sector` | government, police, civilian, university, private individual |

### 4.2 Claim codebook (A1)
Each text is coded 0/1 on each item. "Any physical claim" is the OR of items
1–7.
1. Ground mark or depression
2. Burn, scorch or heating
3. Residue, deposit or material recovered
4. Radiation reading
5. Vegetation effect (wilting, dehydration, growth change)
6. Animal effect
7. Human injury or physiological effect
8. Laboratory analysis stated (yes/no)
9. Laboratory result stated as anomalous (yes/no)
10. Number of distinct quantitative values given (0, 1, 2–5, >5)

Coders also record a quote of at most 30 words for every positive item, so the
adjudicator can check it against the text.

---

## 5. Null models and controls

### 5.1 Nulls used
- **A1.** Exact McNemar on discordant pairs. A secondary date-shuffle null, as
  in `provenance_graph_434.py`, checks that the earliest-root match is not a
  place-name coincidence. Every pair keeps its `example_context` for reading by
  eye.
- **A2.** Hypergeometric on flag counts with fixed margins.
- **A3/A4.** Sign-flip permutation **within site** (exposed vs sham), then
  across sites. It is exact for up to 12 sites and drawn from 4,000 random
  flips above that. Placebo years for A4.

### 5.2 Nulls not allowed, from this project's own failures
- Global permutation of class labels across footprints that don't overlap
  (withdrawn null #1).
- Density matching at a scale other than the sampling scale (withdrawn null #2).
- Choosing subsets by outcome (withdrawn null #3).
- Any control placed from a geocoded coordinate (the persistence artefact).

### 5.3 Positive and negative controls
- **Positive-control sites (A3).** At least two sites with a documented cause
  and date, sampled by the identical protocol before any event site. Candidates
  are a dated lightning strike or brush-fire scar and a dated vehicle-turning
  area on similar soil. If the protocol cannot detect a known heating event of
  similar age, H3 is untestable and is reported so.
- **Trampling control.** A site with documented heavy foot traffic and no
  claimed event. This tests the compaction alternative from NT-16 §4.9.
- **Negative-control outcome (A3/H4).** ¹³⁷Cs from fallout should be
  spatially uniform at the 10 m scale on undisturbed ground. If exposed and
  sham differ in ¹³⁷Cs at P < 0.05, the site was disturbed or the cores are not
  comparable. That site's H3/H4 values are excluded and the exclusion is
  reported.
- **Lab positive controls (A2).** Two blinded reference materials with
  certified values go in every batch. A lab that misses them gets no further
  samples.

---

## 6. Power

All values come from 2,000 simulations (600 for A3/A4) at α = 0.01 one-sided.
Effects are in within-site SD units unless stated.

**A1, claim drift** (P = probability of rejecting the null)

| pairs | add 15%, drop 3% | add 25%, drop 5% | add 35%, drop 5% |
|---|---|---|---|
| 20 | 0.01 | 0.10 | 0.28 |
| 43 (ROOTED only) | 0.18 | 0.42 | 0.80 |
| 80 (ROOTED + LATE_ONLY) | 0.50 | **0.83** | 0.99 |

ROOTED alone is underpowered for anything but a large drift. That's why A1
uses all 80 corroborated events.

**A2, blind decoys** (2 decoys per sample, decoy false-flag rate 10%)

| extant samples | flag rate 30% | 50% | 70% | 90% |
|---|---|---|---|---|
| 3 | 0.00 | 0.00 | 0.00 | 0.00 |
| 5 | 0.01 | 0.08 | 0.29 | 0.66 |
| 10 | 0.09 | 0.42 | **0.80** | 0.99 |
| 20 | 0.22 | **0.78** | 0.99 | 1.00 |
| 40 | 0.57 | 0.99 | 1.00 | 1.00 |

**A3, site revisit** (5 cores per arm, τ = SD of the true effect between sites)

| sites | τ = 0.3, d = 0.5 | d = 0.8 | d = 1.2 | τ = 0.8, d = 0.5 | d = 0.8 | d = 1.2 |
|---|---|---|---|---|---|---|
| 6 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 10 | 0.32 | 0.68 | 0.98 | 0.14 | 0.37 | 0.76 |
| 15 | 0.59 | **0.95** | 1.00 | 0.25 | 0.69 | 0.96 |
| 25 | 0.84 | 1.00 | 1.00 | 0.46 | **0.91** | 1.00 |
| 40 | 0.98 | 1.00 | 1.00 | 0.75 | 0.99 | 1.00 |

Power at 6 sites is zero by construction. The smallest sign-flip P with n
sites is 2⁻ⁿ, and 2⁻⁶ = 0.016 > 0.01. This is the same ceiling that limited
NT-16 to P ≥ 0.0028 with six plants.

**Equivalence bound for a null in A3** (90% CI half-width)

| sites | 6 | 10 | 15 | 25 | 40 |
|---|---|---|---|---|---|
| τ = 0.3 | 0.47 | 0.36 | 0.30 | 0.23 | 0.18 |
| τ = 0.8 | 0.69 | 0.53 | 0.43 | 0.34 | 0.27 |

The preregistered equivalence bound is **±0.5 SD**. A null can be certified
from about 10 sites if heterogeneity is low, and from about 15 if it is high.

**A4, tree rings** (10 trees per arm, suppression d in ring-index SD)

| sites | d = 0.3 | 0.5 | 0.8 |
|---|---|---|---|
| 5 | 0.00 | 0.00 | 0.00 |
| 10 | 0.20 | 0.52 | **0.94** |
| 20 | 0.52 | **0.94** | 1.00 |

---

## 7. Blinding and chain of custody

### 7.1 Roles that must be different people or processes
- **Custodian (K).** Holds the samples, assigns random 6-character IDs, mixes
  in decoys and reference materials, and holds the unblinding key.
- **Lab (L).** Sees only IDs and the material class.
- **Statistician (S).** Runs the frozen analysis script on the lab's raw
  values. A model run can do this, provided it never has the key.

### 7.2 Commitments, in this order
1. This protocol, the codebooks and the analysis scripts are committed to git,
   and the commit hash is posted publicly (OSF registration or a dated public
   gist) **before** any A1 coding or A0 enquiry.
2. The seeds for sham placement, transect bearings, tree draws and pair order
   are committed in the same commit.
3. K writes the unblinding key, and its SHA-256 is committed before samples
   ship.
4. L's raw results are committed (with their SHA-256) before S sees them.
5. S's results file is committed before the key is revealed.
6. Every deviation from this document goes in a dated log
   (`omega/reports/assay_protocol_434_deviations.md`) **before** the affected
   data are looked at.

### 7.3 Physical chain of custody (A2, A3, A4)
- One form per sample: ID, GNSS fix (RTK if possible) with the receiver's
  stated accuracy, time, collector, container type, seal number, and
  photographs of the sample in place, in the container, and sealed.
- Tamper-evident bags with serial numbers. Every transfer is signed and
  timed by both parties, and the seal number is checked and photographed.
- Temperature logger in every shipping box.
- Field crews cannot be blind to which centre is the trace. That's why the
  layout, tools and order are fixed and randomised, and why the blinding is
  done at the lab.

---

## 8. Analysis plan

- Scripts are written and tested on **simulated data** with the same schema
  before any real data exist. The simulations in `assay_protocol_power.py` set
  that schema.
- Holm over H1–H5. Secondaries get Benjamini–Hochberg at q = 0.10 and are
  labelled secondary.
- Leave-one-site-out and leave-one-sample-out for every confirmed result. One
  dominant site is the contamination failure mode (0.6% of records producing
  100% of an effect, `HANDOFF §6`).
- Results are reported for every eligible unit, including those that failed a
  gate, with the reason.
- **Stopping.** No interim tests on A2–A4. A1 runs once, on all 80 pairs after
  the κ check.

---

## 9. Red team

1. **Sample survival is the binding constraint.** If A0 finds fewer than 10
   extant samples, the most direct arm (A2) can't be confirmatory. That is
   likely, and the census is still worth running: it settles which archives
   hold anything, which the project currently cannot say.
2. **Decades of weathering.** Most of these events are 1950–1979 (339 of 434).
   Pigments, volatile residues and short-lived nuclides are gone. A3 measures
   only signals that could last decades (magnetic enhancement, TL/OSL,
   long-lived nuclides). A null in A3 says little about short-lived effects at
   the time.
3. **Location precision will eliminate most sites.** G3 needs an L3 location
   from a primary document. On current evidence (none of the 434 coordinates
   qualifies), the number of A3-eligible sites is unknown. It could be fewer
   than 7.
4. **Site disturbance since the event** is likely for farmland. G4 and the
   ¹³⁷Cs negative control address this. They can't fix it.
5. **Decoys can be recognised.** A lab may tell a decoy from container,
   labelling or condition. Repackaging into identical containers and the
   reference materials in every batch reduce this. They don't eliminate it.
6. **A1 confounds attention with invention.** A later source can add a claim
   because an investigator found something later, not only because the story
   grew. The S2 lag analysis and the quoted text for every claim let a reader
   separate the two by eye. The confirmatory test cannot.
7. **The "terrestrial array" flag in A2 is only as good as the reference set.**
   A residue from an unusual industrial process may fall outside it. Lab B
   replication and a decoy set that includes industrial residues are the
   protection.
8. **Contact with custodians is outward-facing.** The A0 letters are drafts.
   They go out only with the owner's approval.

---

## 10. Next actions, in order

1. Owner reviews and approves this document.
2. Commit, and register the commit hash publicly (OSF or a dated gist).
3. Run A1 on the 80 corroborated events (cheap, in this environment).
4. Draft the A0 enquiry letters next to the existing FOIA/CADA drafts.
   Not sent without approval.
5. While A0 is out, go through the earliest roots for L3 location evidence
   (gate G3) to count the A3-eligible sites.
