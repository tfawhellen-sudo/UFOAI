# Track 2 rerun: matched-landcover controls. PREREGISTRATION

*Project Omega, 2026-11-26. Written and committed before any control-site
imagery is read. The scripts are `omega/track2_lc_controls.py` (builds the
control set; reads no Sentinel-2 data) and `omega/track2_lc_detect.py` (runs
detection on the frozen set).*

## What this adds to session 5

Session 5 compared each site with itself in other years (temporal control).
That rules out "this place always loses vegetation in this season". It does not
rule out "this event year was a bad year for every field like this one in the
region" (drought, harvest timing, a regional storm). A spatial control on the
**same scene pair** removes that: same acquisition dates, same tile, same
atmosphere, same land cover, same elevation band, no reports.

Honest status before the run: the case LOSS values at the 10 sites are already
known from session 5. The control selection below uses only ESA WorldCover
2021, Copernicus DEM and the NUFORC catalogue, none of which carries NDVI
information, so selection cannot be tuned to the outcome.

## Cases

The 18 ground-contact claims fixed in `track2_nuforc_s2.py` (`KEEP`). A case is
tested if it has a clear pre/post pair under the session 5 rules (pre within 60
days, post within 40 days, >=50% clear in both). If a case has no pair in
`sentinel-2-l2a`, the same rules are tried once in `sentinel-2-c1-l2a`. Nothing
else is widened.

## Control set (built first, frozen, hashed)

For each case, candidate centres on a 2 km grid within 10 to 80 km, inside the
MGRS tile footprint of the case's event pair (so the control sits in the
identical pre and post scenes). A candidate is kept only if:

1. **Land cover.** The L1 distance between its WorldCover 2021 class-fraction
   vector in the 2 km box and the case's is <= 0.30 (the class mix overlaps by
   at least 85%).
2. **Elevation.** Mean Copernicus DEM (90 m) elevation in the box is within
   ±150 m of the case.
3. **No reports.** No NUFORC record, any year, within 5 km of its centre.
4. **Independent.** Its centre is >= 4 km from every control already chosen
   (boxes don't overlap).

Ranked by L1 distance, then distance to the case. The first 30 are frozen as the
ordered list. Detection uses the first 20 of those 30 that are >=50% clear in
both scenes. A case with fewer than 10 usable controls is reported as
uncontrollable and dropped from the test. It is not imputed.

## Statistics, fixed now

LOSS is unchanged from session 5: the fraction of clear pixels whose NDVI drops
by more than 0.20 between pre and post. Clear pixels are SCL 4, 5, 6, 7 and 11.
Earth Search COGs are already offset-harmonised, so no 1000 DN is subtracted.

- **Primary (S1).** The case's mid-rank of LOSS among the case plus its controls
  on the same scene pair, giving a rank fraction in (0, 1). Combined over cases
  by the sum of rank fractions against its exact permutation null. The test is
  one-sided (the event shows more loss).
- **Secondary (S2).** The same, using the area of the largest 8-connected
  cluster of loss pixels (m²) in place of LOSS. A burn mark or landing ring is
  compact, and a fraction dilutes it.
- **Alpha.** 0.05 family-wise, Bonferroni-split as 0.025 each.
- **Effect size.** Case LOSS minus the median control LOSS, with a bootstrap 95%
  CI over cases.
- **Combined with session 5 (reported, not tested).** Each case's spatial and
  temporal rank fractions, side by side.

## Power, by injection (run on the same arrays)

Into the case's real post-scene NDVI, insert a disc where NDVI falls by 0.40.
Use areas of 100, 400, 1,600, 6,400 and 25,600 m² at a random clear location,
with 50 draws per area per case. Rerun S1 and S2 against the unchanged
controls. **Minimum detectable effect (MDE):** the smallest area at which the
case ranks first among its controls in at least 80% of draws, for each
statistic. This turns "underpowered" into a number.

## Decision rules, written before the result

- S1 or S2 with P < 0.025: a positive. It would be followed by a pixel-level
  check of each top-ranked case and a hunt for an artefact (cloud-edge, field
  harvest, construction) before anything is claimed.
- Both P >= 0.025: a null. Its meaning is bounded by the MDE. Any trace smaller
  than the MDE is untested, not absent.
- No result is reported without the MDE beside it.
