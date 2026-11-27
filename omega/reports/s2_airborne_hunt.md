# Satellite hunt: moving objects in Sentinel-2, and Landsat trace stacks

*Project Omega, session 7, 2026-11-27. Branch `claude/project-thread-xia29r`.
Scripts: `omega/s2_movers.py`, `omega/s2_coincidence.py`, `omega/s2_sites.py`,
`omega/s2_hunt.py`, `omega/s2_hunt_analysis.py`, `omega/ls_trace_stack.py`.
Data and image sheets: `evidence_vault/08_SATELLITE_ANOMALIES/`.*

## Bottom line

**No unexplained object was found, and no site shows an excess of objects in the sky.**

- **Coverage.** 341 Sentinel-2 scenes went through a moving-object detector. After
  removing duplicate copies of the same overpass, 171 scenes had clean open water,
  about 254,000 km² in total.
- **Airborne objects.** The detector found 223 objects moving at 60 to 400 m/s, the
  speed range of aircraft. The sheets show textbook airliner silhouettes.
- **Fast objects.** 57 objects measured above 400 m/s. **I inspected every one by eye,
  and all 57 are explained:**
  - 39 are surf, breakwater spray, whitecaps or shoreline.
  - 8 are ship wakes or linear streaks.
  - 6 are cloud edges, which shift between bands because of height parallax.
  - 4 are airliners with contrails, where the contrail's height parallax inflates
    the measured speed.
- **Sites versus random points.** Nuclear, military, UAP-encounter, sacred and "lore"
  sites were compared with 30 random disks in the same scene, at the same instant
  and in the same weather. Across all 119 site-scenes the mean rank was 0.51, where
  chance gives 0.50 (P = 0.35). No category stands out; the closest is
  UAP-encounter areas at P = 0.30.
- **Reports made during an overpass.** 70 UAP reports (NUFORC and GEIPAN) were filed
  within 30 minutes of a Sentinel-2 pass and are in the analysed set. 27 have some
  open water nearby. 3 have enough water (10 km² or more) to test. 2 of those 3 have
  one aircraft in the disk: an airliner at 364 m/s (with contrail) near Ocean City,
  MD, and one at 295 m/s near South Haven, MI. Both are ordinary traffic (P = 0.11).
- **Landsat, Tier 2.3.** 20 GEIPAN cases with lab-analysed physical traces
  (1981–2025) were checked; 6 could be tested. Result: null (mean rank 0.54,
  P = 0.35). Trans-en-Provence had no clear pair of scenes. The 3 cases from 2025
  fall after Collection 1 ends.

## The method, and why it is falsifiable

Sentinel-2 does not image all its bands at the same instant. B02, B08, B03 and B04
see a given point about 0, 0.26, 0.53 and 1.0 s apart. Anything moving leaves four
coloured copies in a straight line, and their spacing gives the ground speed.

The band-timing ratios were **fitted from the data, not assumed**: 0.524 and 0.263,
matching Heiselberg (2019). This turns "UFOs in satellite imagery that humans
missed" into a test anyone can repeat. Every moving object in the scene is found,
each gets a speed, and anything faster than any aircraft would be an anomaly with a
number attached.

Two controls run on every scene:

1. **False-alarm rate.** The B04 peak set is shifted to a random offset 10 times and
   matching is rerun. On the validation tile (Channel, 2024-08-05), the detector found
   exactly the 5 airliners confirmed by eye, with 0 scrambled false hits.
2. **Matched random locations.** The 10 km disk at a site is compared with 30 random
   10 km disks in the same 60 km window. They are at the same instant, under the same
   sky and over the same sea, which rules out weather, season and date as causes.
   Disks with less than 25% of the site's usable water are dropped.

## Three failure modes found on the way (each one would have produced a false "discovery")

1. **On land, the detector manufactures Mach-5 objects.** Over the Denver suburbs,
   candidates appeared at the same rate as scrambled noise, even after subtracting a
   same-orbit reference scene. Rooftops, roads and field edges line up by chance, and
   chance alignments get more numerous as separation grows, so the fake objects come
   out "fastest". Land mode is switched off and used for no result
   (`s2_chips/land_mode_false_movers_denver.png`). **Any amateur "hypersonic object in
   satellite imagery" claim over land needs this control before anyone takes it
   seriously.**
2. **Sun glint and rough seas do the same over open ocean.** The first run gave 1,600
   to 44,000 "movers" per scene off San Diego and Virginia, matched by the scrambled
   false hits. The fix was thresholds that adapt to each scene's noise, plus a
   requirement that the three copies are about equally bright and correctly spaced.
   Scenes whose scrambled false-alarm rate is above 1 are excluded (7 scenes).
3. **Pseudo-replication.** Earth Search lists one overpass up to 4 times: two
   processing baselines, and overlapping tiles. Before de-duplication, the
   report-coincidence test gave **P = 0.0006**. That was two ordinary airliners each
   counted four times. After de-duplication, P = 0.11.

## Power: what a null here does and does not say

- **What it covers.** Sentinel-2 passes at about 10:30 local time and takes one frame
  per pass. Over open water it reliably catches objects about the size of an aircraft
  (one 10 m pixel or larger) that are bright against the sea.
- **What it misses.** It cannot see objects smaller than a pixel, objects dark against
  the background, objects at night, anything over land, or an object that is not in
  the frame during that one second.
- **The site test.** It asks whether something about these places brings more objects
  into the sky in daytime. The answer, at this sample size, is no.
- **The coincidence test.** It is weak by construction. A witness's sighting usually
  lasts minutes, and the satellite passes within a 30-minute window. Only 3 reports
  had enough water to test.
- **What would change the verdict.** One compact, colour-consistent object over clean
  water, faster than about 700 m/s or with no contrail-parallax explanation, that
  survives the scramble and an eyeball check. None did.

## Tier 2 scope notes

- **SKYWATCH 52-region pipeline:** it does not exist in any of the four repos
  (UFOAI, ufo_data, ufo_data_search, firecrawl). The session-3 vault README already
  recorded this. There is nothing to finish. A VIIRS, SAR or thermal build would be new
  work, not a completion.
- **Landsat:** `usgs-landsat` is requester-pays (403 without AWS credentials). The
  same USGS Collection 1 product is public on
  `storage.googleapis.com/gcp-public-data-landsat`, which covers 1972–2021. That is a
  mirror of the same public data, not a way around an access control.
- **Sentinel-1 SAR:** the `sentinel-s1-l1c` bucket answers. SAR sees ships and wakes
  well, but at roughly 10–20 m it cannot separate the parallax of airborne objects.
  The useful test would be ship tracks at UAP-encounter areas, not UAP.
- **Landsat trace stacks, power:** geocodes are at commune level (about 1 km) and
  pixels are 30 m (TM/ETM/OLI) or 60 m (MSS). A reported trace is 1–10 m across. Only a
  disturbance of thousands of m² inside the 2 km box could register.

## Files

| file | what |
|---|---|
| `s2_coincidence_pairs.json` | 255 report/overpass pairs within ±30 min (3,067 reports screened) |
| `s2_site_jobs.json` | 24 sites × up to 7 clear scenes, 2019–2025 |
| `s2_hunt_results.jsonl` | per-scene detections, scramble counts, site + 30 random disks |
| `s2_hunt_summary.json` | scores, plus every fast mover with its eyeball class |
| `ls_trace_stack.json` | Landsat trace-case event/pseudo-event results |
| `s2_chips/` | validation, airborne and fast-mover sheets, and the land-mode failure sheet |

Site coordinates are hand-entered to about 1 km, except the French reactors, which
come from the PRIS layer. Detections near shore include some surf; that is noise
shared equally by sites and random disks.
