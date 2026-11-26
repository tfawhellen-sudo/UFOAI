# GEIPAN official case file: Phases 1 to 3 re-run

**Status:** complete. **Date:** 2026-11-26.
**Input:** `data/raw/geipan/geipan_cases.json`, the CNES/GEIPAN bulk export, **3,404 cases**
(A 955 / B 1,323 / C 1,020 / D 106). No other case data used. No records invented.
**Code:** `omega/geipan_to_ufo_data.py` (schema converter), `omega/geipan_phase123.py` (all tests).
**Output:** `evidence_vault/11_GEIPAN_PHASE123/geipan_phase123.json` (every number below).
Seeded RNG (20261126), 10,000 permutations. Runtime about 50 s.

Data hygiene: one export record has an impossible date (`2000-09-01556`, 31/09/2000). It is
treated as month precision, not corrected. 3,305 cases are day-precise, 3,192 are in metropolitan France.

## 0. Loading into ufo_data / ufo_data_search

`geipan_to_ufo_data.py` writes `ufo_data/bin/geipan.json` in the ufo_data catalog schema
(`date`, `location`, `desc`, `ref`, `source_id`, `key_vals.LatLong`, plus the GEIPAN class,
phenomenon and identification in `key_vals`). `omega/corpus.py` loads it cleanly (3,404 records,
3,401 with coordinates) once it is registered in `CATALOG_META`. The analysis deliberately does
**not** register it, so GEIPAN is never matched against itself. ufo_data_search is a WASM search
index compiled from ufo_data output. Rebuilding that index needs the C++/emscripten build and was
not done. The schema file is the part that matters.

---

## Phase 1: provenance

### 1a. Internal collapse: ~1.00x. GEIPAN's case unit is already the event.

Cases on the same day are unioned if they are within *r* km of each other.

| linkage | events | collapse | D cases in a multi-case cluster |
|---|---|---|---|
| same day, ≤30 km | 3,379 | **1.007×** | 0 / 106 |
| same day, ≤100 km | 3,336 | **1.020×** | 3 / 106 |

The largest cluster has 4 cases, and every multi-case cluster resolves to an identified stimulus
(ISS passes, Sirius plus a re-entry, lantern releases). The biggest same-day, same-explanation sets
are lantern releases (25/12/2014: 5 cases). **This result is true by construction (Habit 4).**
GEIPAN files multiple witnesses under one case (`T1`/`T2` témoignages), so near-zero collapse
says how GEIPAN counts things. It is not evidence that the reports are independent.

### 1b. GEIPAN against the 26-catalog literature: the two records barely overlap

Link rule: date ±1 day, **and** either a geocoded literature record within 30 km or the GEIPAN
commune name appearing in the literature text. Literature records must be France-located.

**Hand audit of 25 random links: 23 correct, 2 wrong** (Nice 1997: a different event. Roussillon 1978:
GEIPAN logs Venus seen by gendarmes, while Hatch's same-date record is an entity with antennae, so it is
probably not the same report). **Precision 92% (Wilson 95% CI 75 to 98%). Recall is unmeasured.**

| | value |
|---|---|
| GEIPAN cases (1950–99, day-precise) found in the literature | **113 / 1,053 (10.7%)** |
| French literature records (1950–99, day-precise) found in GEIPAN | **175 / 8,197 (2.1%)** |
| GEIPAN cases after 2000 found in the literature | 0 / 2,252 (the literature corpus effectively ends around 2002) |
| linking catalogs | Hatch 98, Johnson 21, Overmeire 15, Magonia 7, Eberhart 6, rr0 6, NICAP 4 |

**The literature over-samples GEIPAN's unexplained cases:**

| class | in literature | rate (95% CI) |
|---|---|---|
| A | 17 / 951 | 1.8% (1.1–2.8) |
| B | 24 / 1,311 | 1.8% (1.2–2.7) |
| C | 52 / 939 | 5.5% (4.3–7.2) |
| **D** | **20 / 104** | **19.2% (12.8–27.9)** |

D vs A+B: crude OR 12.9 (7.2–23.0) is **confounded by era**, because D cases are mostly pre-2000
and the literature stops around 2002. **Decade-stratified Mantel-Haenszel OR = 4.0 (2.1–7.6), p = 1.8e-5.**
C+D vs A+B: MH OR 1.6 (1.06–2.43), p = 0.031.

**Reading.** The enthusiast literature is not a sample of French reports. Within the same decade,
a case GEIPAN could not explain is about 4× more likely to appear in a catalog. 98% of the French
events in the literature have no GEIPAN counterpart at all. Any "French UAP pattern" computed from
the literature therefore runs on a population the state file barely touches.

---

## Phase 2: nuclear-site proximity

### Site layer: read this first

28 sites: 19 EDF power plants, plus Brennilis, Creys-Malville, La Hague, Marcoule, Cadarache,
Valduc, Saclay, Île Longue and the Plateau d'Albion silos. **These coordinates and first-service
years were entered by hand from general knowledge.** Wikidata and ASN are unreachable from this
container. Expect errors of about 1 to 3 km in position and ±1 year in dates. The check against
GEIPAN's own commune coordinates was possible for only 4 sites (Golfech 0.5 km, Crozon 6.5 km,
Beaumont-Hague 10.9 km; Saint-Christol matched a different commune of the same name). Radii start
at 10 km for this reason. **Before anyone quotes Phase 2, rerun it against an authoritative layer.**

### Session 6 update (2026-11-26): site layer replaced, result unchanged

The 22 reactor sites (19 EDF plants, Brennilis EL-4, Creys-Malville Superphénix, Marcoule
G-2/G-3/Phénix) now come from **GeoNuclearData** (WNA / IAEA PRIS, reactor-mean coordinates,
year = earliest commercial operation, IAEA ids in the CSV). For all 19 EDF plants they agree
with the independent **WRI Global Power Plant Database** to within **0.74 km** (median 0.17 km).
The hand-entered positions were already within about 1 km. Six non-reactor sites (La Hague,
Cadarache, Valduc, Saclay, Île Longue, Albion) have no authoritative source reachable from this
container (Wikidata, ASN, data.gouv and Wikipedia are all blocked) and stay hand-entered. The
layer is `data/raw/nuclear_sites/fr_nuclear_sites.csv`.

| contrast, radius | old (hand) MH OR, perm p | new (22 sourced + 6 hand) | sourced 22 only |
|---|---|---|---|
| D vs AB, 30 km | 0.90 (0.47–1.75), 0.68 | 0.89 (0.46–1.71), 0.70 | 0.77 (0.32–1.82), 0.79 |
| D vs AB, 50 km | 1.29 (0.74–2.25), 0.23 | 1.29 (0.74–2.25), 0.23 | 1.01 (0.55–1.84), 0.54 |
| C+D vs AB, 30 km | 1.11 (0.88–1.42), 0.21 | 1.10 (0.87–1.40), 0.24 | 1.19 (0.89–1.59), 0.13 |
| C+D vs AB, 50 km | 1.16 (0.95–1.42), 0.09 | 1.16 (0.94–1.41), 0.09 | 1.12 (0.90–1.39), 0.18 |
| N2 commissioning O/E | 0.987, p = 0.21 | 0.988, p = 0.25 | 0.975, p = 0.23 |

Smallest one-sided permutation p on the sourced-only layer is 0.098 (C+D nearest distance).
**Phase 2 stays null, and the coordinate caveat is lifted for the reactor sites.** It can be
quoted with one remaining caveat: six non-reactor sites are hand-entered, and dropping them does
not change the verdict. Outputs: `evidence_vault/11_GEIPAN_PHASE123/geipan_phase123.json` (full
layer) and `…_sourced_sites.json` (`OMEGA_SITES=sourced`).

### N1: case-control null

Identified cases (A+B) come from the same observers, the same reporting system and the same
geography as unexplained cases. That makes them the spatial null: population, media and observer
density are matched by construction. Labels were permuted within region × decade strata, with
Mantel-Haenszel stratified on the same strata. Metropolitan France only. Bonferroni α = 0.005 across 10 tests.

| contrast | r | unexplained near | identified near | crude OR (95% CI) | MH OR (95% CI) | perm p (one-sided) |
|---|---|---|---|---|---|---|
| D vs AB | 10 km | 2/100 | 56/2128 | 0.76 (0.18–3.14) | 0.43 (0.06–3.05) | 0.91 |
| D vs AB | 20 km | 9/100 | 171/2128 | 1.13 (0.56–2.29) | 1.48 (0.66–3.32) | 0.23 |
| D vs AB | 30 km | 15/100 | 377/2128 | 0.82 (0.47–1.44) | 0.90 (0.47–1.75) | 0.68 |
| D vs AB | 50 km | 34/100 | 744/2128 | 0.96 (0.63–1.46) | 1.29 (0.74–2.25) | 0.22 |
| C+D vs AB | 10 km | 19/1064 | 56/2128 | 0.67 (0.40–1.14) | 0.61 (0.34–1.07) | 0.97 |
| C+D vs AB | 20 km | 90/1064 | 171/2128 | 1.06 (0.81–1.38) | 1.12 (0.83–1.52) | 0.25 |
| C+D vs AB | 30 km | 195/1064 | 377/2128 | 1.04 (0.86–1.26) | 1.11 (0.88–1.42) | 0.21 |
| C+D vs AB | 50 km | 373/1064 | 744/2128 | 1.00 (0.86–1.17) | 1.16 (0.95–1.42) | 0.09 |

Nearest-site distance, median: A 67.8 km, B 66.5, C 69.0, **D 66.3**. D vs AB Mann-Whitney
p(less) = 0.59, rank-biserial −0.01. C+D vs AB p = 0.50, rank-biserial 0.00.

**Power (one-sided α = 0.05, 80%).** At 30 km the D contrast can detect only OR ≥ 1.8. The C+D
contrast can detect OR ≥ 1.27. So the result excludes a strong association. It does not exclude a small one.

### N2: commissioning null

For each site, take the cases within 30 km and compare the share dated after the site entered
service with the national (metropolitan) share after the same year. **Observed 567, expected 574.4,
ratio 0.99, z = −1.26, p = 0.21.** Sites commissioned in 1983 or later, the only ones with real
before/after leverage: observed 117, expected 121.7. No site shows a post-commissioning surge.

### Framing contamination (the C3 analogue)

44 metropolitan cases mention a power plant, reactor, CEA or EDF: A 17, B 16, C 11, **D 0**.
None of them supports a reactor-linked unexplained case.

> **Phase 2 verdict: null.** On the official French file, unexplained cases are no closer to
> nuclear facilities than identified ones at any radius. Their nearest-site distance is
> indistinguishable. Report rates near sites did not rise after commissioning. Twelve of twelve
> statistics are null (smallest one-sided p = 0.09). This replicates the decontaminated Phase 2
> result on the multi-catalog corpus, using an independent data source.

---

## Phase 3: descriptor drift (1937–2026)

Descriptors come from a French regex lexicon applied to the **witness portion** of each case text,
meaning the text before GEIPAN's analysis begins (found on 64% of cases; the full text is used otherwise).
Model: logistic regression of presence on decade, controlling for log text length. BH-FDR across descriptors.

| descriptor | OR / decade, all cases (95% CI) | q | OR / decade, C+D only | q | 1937–79 → 2010–26 |
|---|---|---|---|---|---|
| photo/video | **2.58 (2.36–2.82)** | 3e-93 | **1.94 (1.68–2.24)** | 5e-18 | 3.3% → 44.5% |
| formation/several | 1.28 (1.16–1.41) | 4e-6 | 1.30 (1.09–1.56) | 0.009 | 1.9% → 8.6% |
| point lumineux | 1.21 (1.14–1.29) | 2e-8 | 1.19 (1.07–1.32) | 0.003 | 9.1% → 20.2% |
| **triangle** | 1.15 (1.06–1.26) | 0.002 | **1.33 (1.18–1.51)** | 6e-5 | 3.1% → 8.4% |
| **disque/soucoupe** | **0.77 (0.70–0.86)** | 4e-6 | 0.75 (0.63–0.88) | 0.002 | 6.4% → 2.5% |
| cigare/cylindre | 0.81 (0.73–0.89) | 7e-5 | 0.76 (0.65–0.89) | 0.002 | 5.5% → 2.8% |
| **landing/ground trace** | **0.68 (0.60–0.76)** | 4e-10 | 0.70 (0.58–0.83) | 6e-4 | 6.9% → 1.1% |
| rouge | 0.87 (0.83–0.92) | 4e-7 | 0.88 (0.81–0.95) | 0.006 | 28.2% → 17.4% |
| sphere/boule | 0.90 (0.85–0.94) | 5e-5 | 0.92 (0.85–1.01) | 0.11 | 21.2% → 19.0% |
| metallic | 0.84 (0.73–0.97) | 0.03 | 0.81 (0.65–1.02) | 0.11 | 3.3% → 1.3% |
| silent, orange, bleu, losange | ns | — | ns | — | — |

**The disc-to-triangle shift survives inside the unexplained subset**, so it is not explained away
by lanterns and satellites dominating the identified cases. The morphology of "the unexplained" moves
with the decade, in the direction the culture moved. A fixed physical population of craft does not
predict that. Landing and trace reports fell about sixfold, while the camera rate rose more than tenfold.

**Class mix over time.** The D share fell from 6.4% (1937–79) and 6.1% (1980–99) to 1.8% (2000–09)
and **1.5% (2010–26)**: OR 0.69 per decade (0.62–0.77), p = 8e-12. The C share fell from 55.6% to 17.0%.
The explanations changed with the era: "unspecified" dominates before 2000, Chinese lanterns appear
from 2000 to 2009 and lead from 2010 to 2026 (366 cases), with ISS, aircraft and bolides behind them.

**What D cases look like** (D vs A+B, decade-stratified MH): triangle **OR 4.9 (2.7–9.0)**, stationary
2.7 (1.6–4.3), silent 2.2 (1.5–3.2), cigar 3.0 (1.4–6.4), sphere 0.48 (0.27–0.85). See red team point 9 before reading anything into this.

---

## Red team

1. ~~**The Phase 2 site layer is hand-entered.**~~ *Session 6: the 22 reactor sites are now from
   IAEA PRIS / WNA via GeoNuclearData, cross-checked with WRI GPPD (≤0.74 km). The result is
   unchanged. Six non-reactor sites are still hand-entered; the verdict holds without them.*
2. **GEIPAN coordinates are commune centroids of the witness, not of the phenomenon.** A light seen
   from 15 km away gets the witness's commune. This blurs every radius below about 20 km toward the null.
3. **N1 assumes classification is independent of proximity.** If investigators near plants have
   better resources (EDF security, gendarmerie, airspace logs), cases there get identified more often.
   That biases toward OR < 1 and could hide a real excess. The 10 km ORs of 0.6 to 0.8 point that way, though they are not significant.
4. **Power.** D has n = 100, so only OR ≥ 1.8 is detectable. "Null" here means no large effect.
5. **N2 has little leverage.** 21 of 28 sites predate 1986. GEIPAN's caseload is dominated by the
   2010s, so nearly every nearby case is post-commissioning under the null as well. Only the late sites (117 vs 121.7) say anything.
6. **Phase 1b recall is unknown, and the matching favours Hatch.** Geocoded Hatch records can match
   by distance. Other catalogs need the commune string. The 2.1% and 10.7% overlap figures are lower bounds.
7. **Reverse causation in 1b.** Some cases are D *because* they were famous and heavily investigated
   (Valensole, Trans-en-Provence). The literature-D association runs in both directions.
8. **Labels change over time.** GEIPAN's revisit programme has moved former D cases to A or B (two
   of them appear in the audit sample: Nay-Bourdettes 1983 and Saint-Hilaire 1981). Every class in
   this file is the *current* class, not the class at the time a catalog copied the case.
9. **The D morphology profile is partly circular.** GEIPAN assigns D when a description fails to fit
   known stimuli. A stationary, silent triangle fits no lantern or airliner, so "D cases are triangles"
   is partly the definition of D speaking. It is not a discovery about the phenomenon.
10. **Phase 3 reads GEIPAN's summaries, not verbatim testimony.** Old cases were rewritten during the
    2010s revisits (the revisit boilerplate appears in the text), so 1970s records carry some 2010s
    staff vocabulary. The witness/analysis split works on only 64% of cases. The regexes are a hand
    lexicon (an earlier draft caught the verb « être » as "entity" and was fixed).
11. **Selection.** The file is what CNES published, not every report received. Cases before 1977
    (when GEPAN was founded) are retrospective and sparse (419 cases before 1980).
12. **Not tested:** military airbases, nuclear-weapons transport routes, plants under construction,
    overseas sites (CEP Moruroa/Fangataufa, where GEIPAN's Polynesia coverage is too thin to test).

## Bottom line

- **Phase 1:** GEIPAN is close to collapse-free internally (1.007×), but that holds by construction.
  It is almost disjoint from the enthusiast literature (2.1% of the literature's French events are in it),
  and the literature over-selects GEIPAN's D cases about 4× within the same decade.
- **Phase 2:** null on an independent state dataset. No proximity excess at 10 to 50 km, and no
  commissioning effect. Strong associations are excluded. Weak ones are not testable at n(D) = 100.
  **The site layer must be swapped for an authoritative one before this is quoted.**
- **Phase 3:** strong cultural drift. Discs fall, triangles rise, landings collapse and cameras surge,
  and this persists inside the unexplained subset. D's share of GEIPAN's file has fallen about fourfold since 2000.
