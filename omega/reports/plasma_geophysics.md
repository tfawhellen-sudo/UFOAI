# Orb reports vs plasma geophysics (faults, geomagnetic storms, earthquakes)

Session 6 thread, 2026-11-26. Code: `omega/plasma_geophysics.py` (tests),
`omega/plasma_geophysics_plot.py` (figure). Output:
`evidence_vault/11_PLASMA_GEOPHYSICS/plasma_geophysics.json`. Inputs, frozen:
`evidence_vault/11_PLASMA_GEOPHYSICS/inputs/plasma_inputs.tar.gz`.

## Bottom line

**The plasma hypothesis fails as a general explanation for orb reports in both
national datasets.** Orb and light reports are no closer to active faults, no
more common on geomagnetic storm days, and no more common before nearby
earthquakes than "structured craft" reports from the same reporters, places
and years. Out of ~40 inferential comparisons, three were nominally
significant, two in the hypothesis's direction and one against it. That
pattern is what noise looks like, and both positive hits fall apart when
they're probed (§5).

What this does **not** rule out: a small minority of reports being genuine
EQL or ball lightning. The tests bound how large that minority can be (§6).

![forest plot](plasma_geophysics_forest.png)
(Figure is in the project files at `omega/plasma_geophysics_forest.png`. `*.png` is gitignored here; regenerate with the plot script.)

## 1. Design: why every test compares orbs with other UAP reports

Raw report counts follow population, sky-watching habits, media waves and
reporting infrastructure. Comparing orb reports with a map of faults or a
calendar of storms would mostly measure those things. So every headline test
compares two classes from the same system:

| dataset | orb class | control class |
|---|---|---|
| NUFORC (US, 1910 to May 2014, 64,508 CONUS records with city geocodes) | shape ∈ {light, fireball, sphere, flash}: 24,030 | shape ∈ {triangle, disk, cigar, cylinder, chevron, rectangle, diamond, cone, cross, delta}: 16,594 |
| GEIPAN (France, 3,404 cases, 1937 to 2026) | Details mention boule/sphère/globe/orbe/lumière/point lumineux and no craft word: 1,776 | craft word and no orb word: 257 |
| GEIPAN, second control | **unexplained** orbs (class C/D): 505 | **identified** orbs (class A/B, mostly Thai lanterns, Venus, aircraft): 1,271 |

The GEIPAN A/B orbs work as a negative control. They went through the same
witness → gendarmerie → GEIPAN pipeline, but they are lanterns and planets,
not plasma. Any geophysical association they share is a reporting artifact.

Effect sizes are odds ratios: Mantel-Haenszel stratified by **year** for time
tests and by **state/department** for space tests. 95% CIs come from a
cluster bootstrap with 2,000 reps for the unstratified tests and 500 for the
stratified ones. Clusters are report dates for time tests and locations for
space tests, so one flap night or one town can't pose as many independent
data points.

Two further nulls are reported alongside: a **population-weighted** null
(GeoNames places of 1,000 people or more, weighted by population) and a
**calendar** null (the share of storm days in the same year-month).

## 2. T1: are orbs nearer active faults?

Faults are the GEM Global Active Faults harmonised traces (13,696 traces,
densified to about 1 km).

| comparison | ≤25 km OR [95% CI] |
|---|---|
| US, orb vs craft, by state | **0.94 [0.85, 1.02]** |
| US west of 104°W (where fault mapping is dense), by state | 0.94 [0.84, 1.04] |
| France, orb vs craft, by department | 1.98 [0.90, 4.91] |
| France, unexplained vs identified orbs, by department | 1.30 [0.66, 2.49] |

10 km and 50 km thresholds give the same picture (see JSON). Against the
population null, every NUFORC report class sits slightly nearer faults than
population does: 21% of orbs and 21% of all reports are within 25 km,
against 18.5% for population. That is a **reporting geography** effect (the
West reports more per head). It is not orb-specific.

## 3. T2: are orbs more common on geomagnetic storm days?

Kp is from GFZ via CelesTrak, 1957-10 to 2025-07. A storm day is a day whose
daily max Kp is 5 or more (G1+).

| comparison | result |
|---|---|
| NUFORC orbs, observed/expected storm days (calendar null) | **O/E 0.97 [0.89, 1.06]**, n = 23,965 |
| NUFORC craft, O/E | 0.99 [0.91, 1.06] |
| NUFORC orb vs craft, by year | OR 0.94 [0.88, 1.01] |
| NUFORC ≥45°N only (aurora belt), by year | OR 0.88 [0.72, 1.11]; orb O/E 0.89 [0.76, 1.02] |
| GEIPAN orbs O/E | 1.01 [0.86, 1.16] |
| GEIPAN unexplained vs identified orbs, by year | OR 0.88 [0.58, 1.32] |

**Red team catch:** the raw, unstratified NUFORC OR was 0.81 [0.71, 0.93],
which suggests orbs *avoid* storms. That is an era artifact. Orb reports peak
in 2008 to 2013 (the lantern boom, during a deep solar minimum), while craft
reports are spread over decades with more storms. Stratifying by year removes
it. Not even aurora shows up as an excess of "light" reports at northern
latitudes. Aurora watchers report to aurora networks, not to NUFORC.

## 4. T3: do orbs come in the 1 to 14 days before nearby quakes?

Quakes are USGS ComCat regional extractions (a third-party freeze, see the
manifest). A report is "exposed" if a quake at or above the stated magnitude
occurs within the radius 1 to 14 days later.

| region | M, radius | orb vs craft, by year |
|---|---|---|
| Cascadia (1970+) | M3+, 100 km | **1.33 [1.05, 1.71]** |
| Oklahoma (2000+) | M3+, 100 km | **0.49 [0.28, 0.91]** (opposite direction) |
| New Madrid (1974+) | M2.5+, 100 km | 0.82 [0.49, 1.42] |
| California (1900+) | M5+, 150 km | 0.71 [0.44, 1.12] |
| Yellowstone | M2.5+, 50 km | 19 reports, untestable |

The post-quake window (0 to 3 days after) is null everywhere.

**T3b, Oklahoma natural experiment.** Wastewater injection raised Oklahoma M3+
quakes about 21-fold, from roughly 3 a year in 2000 to 2008 to roughly 60 a
year in 2010 to 2013. If quakes make orbs, Oklahoma's orb share should rise
relative to its neighbours (KS, AR, MO, NE, IA, NM, CO). Ratio of odds ratios
**1.23 [0.77, 1.97]**. Orb/craft counts: OK 94/97 → 91/51, neighbours
880/748 → 717/410. So orbs rose about as much in the neighbours, which reflects
the national lantern era. The upper bound rules out a doubling of orb odds
caused by a 21× rise in quakes.

## 5. The two positive hits, probed

**Cascadia pre-quake OR 1.33.** It survives dropping 1980 (Mount St Helens
swarm): 1.35 [1.09, 1.74]. It does not survive changes to the window
or magnitude:

| variant | OR [CI] |
|---|---|
| 7-day window | 1.27 [0.96, 1.81] |
| 30-day window | 1.09 [0.92, 1.32] |
| 200 km radius | 1.09 [0.93, 1.29] |
| 50 km radius | 1.32 [0.91, 2.02] |
| **M4+ instead of M3+** | **0.77 [0.32, 1.61]** |

EQL physics predicts a stronger effect for bigger quakes. Here it reverses at
M4+, and Oklahoma goes the opposite way at M3+. Read as a chance hit among
many tests. It could be retested on a fresh dataset (post-2014 NUFORC, full
ComCat) as a pre-registered single test.

**France, unexplained orbs within 10 km of a fault.** Region-stratified OR
3.17 [1.54, 6.68], or 1.93 [1.04, 3.50] stratified by decade. This rests on
22 cases: Alpes-Maritimes 7, Pyrénées-Orientales 6, Alpes-de-Haute-Provence 3,
Bouches-du-Rhône 3, plus 3 others. It vanishes at 25 km (0.99) and 50 km
(0.81), and France has only 38 SHARE fault traces in GEM. A real fault-driven
light source should show a distance gradient, not a 10 km spike. Fragile.
The 22 case files are worth reading individually (IDs can be pulled from the
JSON pipeline). They are a reading list, not a finding.

## 6. What the nulls bound (the useful part)

- Storms: the US orb O/E upper bound is 1.06. So no more than about 6% of US
  orb reports can be extra storm-day events. Most of any storm-linked
  phenomenon would show up there.
- Faults: in the US West the OR upper bound is 1.04 at 25 km. Orbs are not
  even mildly enriched near mapped faults.
- Induced quakes: a 21× quake rise produced no orb rise above about 2× (upper
  CI).
- Scale caveat: EQL in the literature are rare, local and clustered around
  specific large events (L'Aquila 2009, Pisco 2007, Saguenay 1988; review: Thériault et al. 2014, Seismological Research Letters 85(1):159-178). A national
  report database can't see a phenomenon that produces a few dozen reports
  per decade. **These tests rule out "orbs in general are EQL/geomagnetic".
  They do not rule out "a few orbs are EQL".** The right tool for that is a
  case-crossover study around individual large quakes. That needs full
  ComCat or SI-Hex access, which is blocked (§8).

## 7. Geography: where orbs fall

Orb share of orb+craft by US state, compared with the national 59%. States
with BH q < 0.05:

| higher orb share | | lower orb share | |
|---|---|---|---|
| WA 66% (median 14 km to a fault) | OR 64% (14 km) | AR 49% | TN 53% |
| SC 67% (1,048 km) | FL 62% | KY 53% | TX 56% |
| WI 64% | MT 67% (47 km) | | |

Across states, orb share correlates with nearness to faults (Spearman ρ =
−0.38, p = 0.008). That is **ecological**: it is driven by WA/OR/MT. Two red
team points apply. First, NUFORC is run from Washington State, and local media
and reporting habits differ. Second, inside states the individual-level OR is
0.94. So the state pattern is about the states, not the faults. SC, FL and WI
are just as orb-heavy and nowhere near a fault.

France: no department departs from the national orb share after correction.
Department-level ρ = 0.21, p = 0.17. The unexplained near-fault cases sit in
Provence, the Alpes-Maritimes and the eastern Pyrenees, the most seismically
active parts of metropolitan France. These are also dense coastal tourist and
lantern zones.

**Not done (blocked hosts, reported rather than guessed):**
- Lithology / quartz-rich or piezoelectric rock: no geology server is
  reachable (Macrostrat, USGS mrdata/SGMC, BRGM InfoTerre, PANGAEA/GLiM). I
  did not hand-draw granite polygons. A hand-entered layer is exactly what
  memory flags as unquotable.
- Power lines: OpenStreetMap (Overpass, Geofabrik), HIFLD and the French
  grid operator RTE's open data were all refused.
- French seismicity catalogue (SI-Hex, BCSF-RéNaSS, EMSC, ISC): refused. So
  there is no pre-quake test for GEIPAN.

## 8. Red team

1. **Shape labels are self-reported.** "Light" in NUFORC is partly lanterns,
   satellites, Starlink-era trains (after 2019, outside this scrub) and
   planets. That dilutes any true EQL signal. It is the main reason a null
   here bounds "orbs in general" rather than "any orb".
2. **Geocodes are city centroids.** Fault distance error is roughly 5 to
   10 km, so the 10 km tests are the least reliable. The 25 to 50 km tests
   hold up.
3. **Third-party mirrors.** The NUFORC scrub (planetsig) and the quake
   extractions (liveatlasearth) are not primary sources. SHA-256 hashes are
   in the JSON and the files are frozen in the vault. Replace them with
   primary pulls when USGS/NUFORC are reachable.
4. **GEM coverage is uneven.** The eastern US has almost no traces, which is
   why the West-only test exists. France has only 38 traces.
5. **The NUFORC scrub ends May 2014.** It misses Oklahoma's 2015 peak (915
   M3+), the best years for T3b.
6. **Multiple testing.** About 40 comparisons gave 3 nominal hits, with
   about 2 expected by chance. No hit survives Bonferroni (α ≈ 0.00125).
7. **Time-shift null is biased in nonstationary catalogues.** In Oklahoma,
   shifting reports ±2 years moves them into the surge. That is why the
   orb-vs-craft OR, not the shift null, is the headline. Shift-null values
   are still in the JSON.

## 9. Next steps, ranked

1. **Case-crossover around big quakes**, which is the right test for rare
   EQL. Take every M≥6 shallow continental quake since 1990 and count all UAP
   reports within 200 km in the 30 days before. Compare with the same
   calendar window in other years. Needs full ComCat or the GEIPAN-era
   French catalogue, so earthquake.usgs.gov and franceseisme.fr would need
   adding to the network allowlist.
2. **Lithology and power lines** for the 22 French unexplained near-fault
   cases, once BRGM and OSM are reachable.
3. **Re-run with the post-2014 NUFORC export** (in the vault, no geocodes)
   plus the Wikidata gazetteer. This extends T3b through Oklahoma's 2015 peak
   and gives the Cascadia hint an independent sample.
