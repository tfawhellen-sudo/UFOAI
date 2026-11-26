# Track 2 rerun: Sentinel-2 at ground-contact reports, matched-landcover controls

*Project Omega, 2026-11-26. Preregistration: `omega/reports/track2_landcover_prereg.md`
(commit 5a9efb4, amendment 1 in aefc373). Control sets frozen with sha256 in 5d40a79,
before any control pixel was read. Scripts: `omega/track2_lc_controls.py`,
`omega/track2_lc_detect.py`. Data: `evidence_vault/08_SATELLITE_ANOMALIES/track2_lc_*`.*

## Bottom line

**Null again. The bigger result is that the method is blind below roughly 10 to 40
hectares.** Settlement-geocoded reports can't be matched on land cover, can't be
powered, and the one outlier is a construction site.

| | Tier A (preregistered) | Tier B (exploratory, amendment 1) |
|---|---|---|
| Cases tested | 1 (Benton TN) | 4 (Shelby NC, Olympia WA, Cottage Grove MN, Benton TN) |
| S1 LOSS, mean rank (H0 0.50), one-sided P | 0.26, P = 0.76 | 0.42, P = 0.70 |
| S2 largest loss cluster, mean rank, P | 0.21, P = 0.81 | 0.53, P = 0.41 |
| S1w class-reweighted LOSS, mean rank, P | 0.26, P = 0.76 | 0.41, P = 0.73 |
| Case LOSS minus control median | −0.0021 | +0.0004 (bootstrap 95% CI −0.013 to +0.014) |

Preregistered alpha was 0.025 per statistic. Nothing comes close.

## What the control build showed (the real finding)

The 2 km boxes sit on settlement centroids, and they are 30% to 71% built-up
(WorldCover class 50). Within 80 km, inside the same Sentinel-2 tile, almost no
other box has the same mix. The rule that bound was **land cover** (950 to 2,400
candidates rejected per case). It wasn't reports or elevation. Under the
preregistered rules (L1 ≤ 0.30, NUFORC exclusion 5 km), 2 of 10 cases had ≥10
controls. Clouds on the event dates then cut Essex MT to 9, which left n = 1.
Loosening L1 to 0.50 and the exclusion to 2 km (Tier B) raised it to 4.

Analogy: we wanted to compare a downtown block with other downtown blocks that
nobody ever reported a UFO over. In this catalogue those barely exist, because
reports come from where people are.

Edmonds WA, the only no-pair case with scenes in `sentinel-2-c1-l2a`, gains
nothing. The 82 scenes are the same acquisitions reprocessed, so the clouds that
blocked session 5 still block it. The other 7 no-pair cases have no c1 coverage
at all (2016 to 2017).

## Power: minimum detectable trace, by injection into real imagery

An NDVI drop of 0.40 was inserted as a disc into each case's real post-scene, 50
random placements per size. The table gives the area at which the case ranks
first among its controls in ≥80% of draws.

| Case | S1 LOSS | S2 cluster |
|---|---|---|
| Shelby NC | 41 ha | 41 ha |
| Olympia WA | 41 ha | > 41 ha |
| Cottage Grove MN | 10 ha | already first without injection (see below) |
| Benton TN | > 41 ha | > 41 ha |

**At every preregistered size (100 m² to 2.56 ha), the detection rate is 0%
everywhere.** A landing trace of a few metres to a few tens of metres is
untested, not absent. Two reasons:

1. **Control variability is large.** Normal farming, mowing and building
   produce LOSS up to 5% and loss clusters up to 11 ha in the controls on the
   same dates.
2. **The fixed −0.20 threshold fights the season.** At Benton (March to May
   green-up), the median dNDVI is +0.20, so a −0.40 trace nets out at about −0.20
   and only half its pixels cross the threshold. This affects session 5 too.

## The one outlier: Cottage Grove MN is a construction site

S2 ranks Cottage Grove 0.97 (largest loss cluster 3.8 ha against a control
median of 0.3 ha). It was checked before anything was claimed, as the
preregistration requires.

- **Where.** The cluster is about 800 m from the geocoded centroid, 290 × 290 m
  in extent. By WorldCover 2021 it is grass 43%, bare 29% and built 25%.
- **Time series of the same pixels** (summer scenes under 10% cloud):

  | Year | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 |
  |---|---|---|---|---|---|---|
  | Patch NDVI | 0.76 → 0.37 | 0.62 → **0.17** | 0.19 | 0.22 | 0.18 | 0.19 |
  | Rest of box | 0.59 | 0.60 | 0.61 | 0.59 | 0.51 | 0.50 |

  The patch had already been stripped once in August 2017. It was cleared
  again between 4 June and 6 July 2018 and stayed bare for 4 years. By 2021,
  WorldCover classes it as bare and built.
- **Reading.** A scorch or landing mark regreens within one season. Ground that
  stays at NDVI ~0.2 for four years and turns into "built" is earthworks, a
  suburban development on the Cottage Grove fringe. The report (8 June 2018,
  "saucer like on the ground") falls inside that grading window. It doesn't
  explain it. **Conventional explanation, not a lead.**

## What this closes, and what would actually work

- Track 2 on NUFORC is now closed twice over: temporally self-controlled
  (session 5, P = 0.65) and spatially land-cover-controlled (this run). Both
  are null, and the MDE is tens of hectares. Don't run it a third time on
  settlement geocodes.
- The test needs **field-level coordinates plus a post-2015 date**. Two sources
  could give that: (a) MUFON CMS case files, which often carry investigator GPS
  points, and (b) GEIPAN 2016+ cases with site visits (the PV extracts). Either
  turns a 2 km box into a ~100 m box. That cuts control variability about
  400-fold in area and pulls the MDE down toward the 0.1 to 1 ha range, where
  a real ground trace lives.
- Fix before reuse: replace the fixed −0.20 threshold with a dNDVI z-score
  against the same-date controls. That removes the season offset seen at
  Benton.

## Method record

- Session 5's product rule (scene cloud < 40%, then newest baseline) is
  reproduced exactly. The detection script asserts that every case's LOSS
  equals the session 5 value. That assert caught a product mismatch at
  Shelby: on 2020-06-25 there are two processings (02.14 at 35.8% cloud, 05.00
  at 47.9%), and the control-set file had recorded the unfiltered newest one.
  Fixed in the detection step. Product choice is metadata, so the control
  locations are unchanged.
- WorldCover 2021 v200 is used at its 4× overview (~37 m) for matching and at
  native 10 m for S1w. Elevation is Copernicus GLO-90. Hosts:
  esa-worldcover.s3.eu-central-1.amazonaws.com and
  copernicus-dem-90m.s3.amazonaws.com, both reachable from the Default
  environment.
- The 102,400 and 409,600 m² injection sizes go beyond the preregistration and
  are labelled as such in the JSON.
