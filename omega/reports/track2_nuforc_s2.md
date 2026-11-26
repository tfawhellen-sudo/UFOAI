# Track 2, repointed: Sentinel-2 at modern ground-contact reports

*Project Omega, session 5, 2026-11-26. Closes handoff §5 item 5. Script:
`omega/track2_nuforc_s2.py`. Data: `evidence_vault/08_SATELLITE_ANOMALIES/track2_nuforc_s2.json`.*

## Bottom line

**Null, and underpowered by construction.** Ten reports could be tested. The
event-date NDVI loss ranks at a mean of 0.47 among each site's own pseudo-events
(H0 expects 0.50), one-sided P = 0.65. No event was the maximum of its own set
(1.45 expected by chance). The paired effect, event LOSS minus median pseudo
LOSS, is +0.004 (bootstrap 95% CI −0.006 to +0.015). Nothing to explain.

## Two corrections to the handoff

1. **"34,898 Sentinel-2-era records" is year ≥ 2015.** That includes January to
   June 2015, before Sentinel-2A launched on 23 June 2015. From July 2015 on, the
   geocoded count is **32,260.**
2. **Almost none of the 32,260 predicts anything Sentinel-2 can see.** A light
   in the sky leaves no surface signature, and Sentinel-2's ~10:30 local overpass
   can't image a night event as it happens. The only testable claim is a
   post-event surface change where a report claims ground contact.

## Selection

A keyword screen (landed, on the ground, burn mark, trace, imprint…) gives 100
hits. Every one was read. **18 are explicit ground-contact claims** with a
settlement-level geocode that isn't ambiguous. Two are explicit trace claims:
Dyersburg TN 2020, "Burned spot on ground", and Shelby NC 2020, "landing
impressions". The other 82 are excluded, and the script records the reason
classes: aircraft landing lights or place names, NUFORC HOAX/IFO flags, no
ground contact, ambiguous geocode, or no spot named. 8 of the 18 had no clear
pre/post scene pair within 60/40 days, mostly 2015–2017, before Sentinel-2B
(March 2017) halved the revisit. **10 were tested.**

## Design

- **Self-controlled.** Each site is compared with itself: same 2 km box, same
  pre/post gap and same season (±15 days) in up to 8 other years, 2016–2024.
  Under H0 the event's rank among its own pseudo-events is uniform, whatever
  the land cover, so no land-cover raster is needed. That removes the blocked
  landcover-host dependency.
- **Statistic:** the fraction of clear pixels whose NDVI drops by more than 0.20.
  Clouds, shadow, cirrus, saturated and no-data pixels are masked with the L2A
  scene classification. A pair is used only if at least 50% of the box is clear
  in both scenes.
- **Offset check, recorded because it nearly produced a false positive.** The
  first run subtracted the baseline-04.00 BOA offset of −1000 DN and got NDVI > 1
  and a 52% "loss" at Dyersburg. Earth Search's COGs are already harmonised. The
  red-band 1st percentile is 109–266 DN on baselines 05.00 and 05.09, which is
  impossible if the offset were still in the data. With the correct handling,
  Dyersburg is 2.7%, rank 0.69. **That's habit #1 again: check the instrument
  before believing the reading.**

## Power, stated plainly

NUFORC is geocoded to settlement centroids, not to the field. The 2 km box may
not contain the reported spot, and a trace of a few metres is under one 10 m
pixel. A detectable signal would need several hundred m² of vegetation loss
inside the box, beyond what the same place shows in the same season of other
years. **This null does not show that the reported events left no trace.** It
shows that settlement-geocoded citizen reports can't carry a Sentinel-2 test.
A real test needs field-level coordinates, which only investigator case files
(GEIPAN-style) provide, and those are pre-2015.

## Blocked, not pending

Nothing. Imagery was reachable once archive.org, earth-search.aws.element84.com
and sentinel-cogs.s3.us-west-2.amazonaws.com were allowed on 2026-11-26.
