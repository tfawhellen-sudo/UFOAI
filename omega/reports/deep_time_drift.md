# 2,000 years of UAP descriptions: drift, technology tracking, a description tree, and the ancient-astronaut tests

Abyss Protocol Tasks 2.1, 2.2, 2.3 and -3.1. Project Omega, 2026-11-27.
Code: `omega/deeptime/` (run order in its README). Every number: `omega/reports/deep_time_tables.md`.
Result files: `evidence_vault/13_DEEP_TIME/`. Figures: `omega/reports/figures/deeptime_*.png`.

## Bottom line

1. **Descriptions track their era.** Within the same compiler and adjusted for text length, reports from before 1800
   use the analogies of their world 5 to 12 times more often than modern reports: stars and suns, shields and armies,
   crosses and omens, dragons, ships, torches, wheels. Modern reports use geometry and machines instead. Discs are 5x
   rarer before 1800 (OR 0.20), triangles 9x (0.11), metallic surfaces 5x (0.21), formations 4x (0.26), flashing
   lights 6x (0.18), occupants 3x (0.30).
2. **Technology words switch on the year the technology appears.** I estimated change points blind from the data,
   with no dates supplied. "Saucer" steps up in 1947, the year of the Arnold sighting. "Satellite" steps up in
   1956 (90% interval 1955-58), and Sputnik flew in 1957. "Drone" steps up in 2012 in the catalogs and in 2014
   (2012-15) in NUFORC witness text, against consumer quadcopters in 2013. "Starlink" or "satellite train" steps up
   in 2019 in NUFORC, the year of the first launch. Shapes move with the era too: cigars and searchlights in the
   1896-1913 airship wave, discs from 1947, triangles in the 1980s-90s, orbs in the 2010s, and lines of lights in the
   2020s. From 1700 to 1946, 57.5% of reports that compare the thing to a vehicle pick the newest vehicle of their
   year, against 40.6% when the years are shuffled (p = 0.0005).
3. **What stays the same is generic.** The descriptors that are stable over 2,000 years are round or glowing lights,
   cylinders, large size, erratic motion and sudden vanishing. Before 1800, they occur at the same rates in reports
   that name a comet, meteor, aurora or halo as in "unexplained" ones: vanishing 6.9% vs 6.9%, cylinder 3.4% vs
   3.8%, sphere 12.6% vs 14.1%, hovering 8.0% vs 8.6%. In GEIPAN, round, glowing and white lights are identified
   stimuli 68-69% of the time. The invariance is that of luminous natural phenomena and of human perception. It is
   not the signature of one constant craft.
4. **The tree follows time and authorship, not the stimulus.** On a neighbour-joining tree of 49 description
   populations, date has strong phylogenetic signal (Blomberg's K 1.99, p = 0.001). So does "written by a witness or
   by a compiler" (K 1.97, p = 0.001). "Names a natural phenomenon or not" has none (K 0.78, p = 0.08). The 1896-1913
   reports from six different compilers form one clade (98% bootstrap support). GEIPAN's unexplained cases sit
   inside the clade of GEIPAN's identified cases (100%).
5. **The ancient-astronaut predictions fail wherever this data can test them.** Structured craft seen close (a shape
   plus a landing or occupants) appear in 1.8% of pre-1800 reports and 11.3% of post-1947 reports. Within catalog,
   the odds ratio is 0.07 (0.03-0.15), and that holds in catalogs compiled by ufologists who were looking for such
   cases. Occupants wear the era's mythology: angels, saints and dragons before 1500; airship inventors in 1896-1913;
   space visitors after 1947. The one untouched ancient source, Obsequens' Roman prodigy list, has 62 sky omens and
   no landings, no occupants and no craft. It is all torches, suns and shields.

In plain terms, the 2,000-year record does not show one phenomenon described the same way across the ages. It
shows one human habit: a light in the sky gets described with the newest analogy to hand. That does not rule out an
anomalous residue. It says descriptive language cannot find one, because any signal lies under three layers of noise:
the era's vocabulary, the compiler's voice and natural phenomena.

## What was tested, and against which null

| question | test | null | result |
|---|---|---|---|
| Do descriptors drift over 2,000 years? (2.1) | per-descriptor OR, before 1800 vs after 1947, within catalog, length-adjusted | same OR in reports that name a natural phenomenon | strong drift; the drift pattern matches the natural-phenomenon reports (r = 0.66) |
| Where are the era breaks? (2.1) | divergence between adjacent eras inside one compiler, at equal n | split-half noise at the same n | 1896 and 1914 breaks about 2x noise; 1947 only 1.2-1.6x |
| Is a description the witness's or the compiler's? (2.2) | the same event in different catalogs; LLM paraphrase vs other catalogs | none (agreement) | firm-link kappa 0.78, but mostly shared upstream sources; the LLM paraphrase adds occupants and "mysterious" |
| Do descriptions track technology? (2.3) | change points of technology words vs the year each technology appeared; newest-vehicle share | year-shuffled within catalog | change points land on t0 (1947, 1956/57, 2012-14/2013, 2019/2019); newest-vehicle share 57.5% vs 40.6% |
| Is anything invariant? (2.3) | stable descriptors vs reports that name a natural phenomenon; vs GEIPAN identified | natural-phenomenon reports; GEIPAN A/B | stable descriptors are as common in natural-phenomenon reports as in unexplained ones |
| Is there phylogenetic structure? (-3.1) | NJ tree, bootstrap, Blomberg's K, distance regression, delta score | tip permutations; shuffled characters | tree-like (delta 0.36 vs 0.45); organised by date and author, not stimulus |
| Ancient astronauts (2.3) | five predictions, AA1-AA5 below | modern rates; primary text | AA1-AA3 fail; AA4 fails; AA5 cannot be tested with these catalogs |

## Data (Task 2.2: the pre-industrial corpus)

Nothing was scraped. Everything was already in the project, except one public-domain primary text.

- **Ten catalogs in `ufo_data/bin`, loaded for all their years** (43,719 records, 3,927 of them before 1947, back to
  AD 34). The catalogs are Wonders in the Sky (`ancient.json`, 478 records), It Didn't Start with Roswell
  (pre_roswell), Hatch, Eberhart, Overmeire, rr0, Johnson, Magonia and NICAP. Loading every year matters. Five
  compilers (Hatch, Eberhart, Overmeire, rr0, Johnson) cover both ancient and modern cases, so drift can be measured
  inside one voice. Cross-compiler comparisons would mix style with era.
- **Primary text control.** Julius Obsequens, *Liber prodigiorum* (Roman prodigy lists, 191-12 BC), in Nisard's
  1850 French translation from archive.org, `corneliusneposq00nepogoog`. From it I extracted 62 sky clauses with no
  ufologist in between.
- **Modern comparators.** NUFORC (133,161 witness reports) and GEIPAN (3,404 French official cases, with the A/B =
  identified and D = unexplained classes).
- **Records naming a natural phenomenon** are a built-in mundane class: comet, meteor, aurora, halo, mock suns, ball
  lightning. That gives 87 before 1800 and 743 after 1947. Where a compiler adds an identification ("probably a
  meteor", "[IN REALITY: Halley's comet]"), that sentence is flagged and removed before coding. This is the rule the
  craft taxonomy used for GEIPAN, so the explanation cannot leak into the descriptors.
- **Coding.** Coding uses the craft taxonomy's audited lexicon for 29 physical descriptors, reused unchanged. On top
  of that sit 18 analogy "frames" (star, shield, cross, dragon, ship, torch, wheel, balloon, airship, aircraft,
  rocket, saucer, spaceship, satellite, Starlink, drone, lantern...), 2 entity features and 2 compiler-voice markers
  ("object/craft/UFO", "mysterious/strange"). The coding is in English and French, all regex, all auditable in
  `lexicon.py`.

**Three data problems found, and how each was handled:**

- **`ancient.json` is not Vallee and Aubeck's text.** It is an LLM paraphrase made by the ufo_data author, and so is
  pre_roswell. I checked 94 events that also appear in other catalogs. The paraphrase adds occupants (20 events vs 3
  in the other catalogs), "object/craft" wording (53 vs 29), "mysterious" wording (36 vs 11) and vanishing (12 vs 2).
  Neither catalog has post-1947 records, so neither enters the within-catalog drift tests. The tree flags the
  paraphrase share. AA1 holds without them (1.6% before 1800).
- **Same-event agreement looks high (kappa 0.78 on 322 firm pairs) because the catalogs copy each other.** Johnson,
  NICAP and Magonia largely descend from Vallee's Magonia list, and Overmeire and rr0 from the same French sources.
  Agreement is shared provenance, not independent confirmation. A looser linking rule chained unrelated reports and
  gave kappa 0.08, so only firm links (same full date, word overlap of at least 0.2) are used.
- **Dates like "Late 10/1945" had been read as AD 10.** The parser was fixed; the earlier run put 1940s reports in
  antiquity.

## Task 2.1: the descriptor drift test

**Drift exists, it is large, and it has a direction** (`deeptime_ancient_vs_modern.png`, table T2). Of the 42
features with an estimable length-adjusted odds ratio (before 1800 vs after 1947, within catalog), 27 have a 95%
interval that excludes 1, and 22 lie beyond the 0.5-2 band. Before 1800
the frames dominate: torch 12.5x, wheel or chariot 8.8x, dragon or serpent 7.7x, cross or omen 6.9x, ship 5.1x,
shields and armies 5.0x, star or sun 4.8x, fireball 6.2x. After 1947, geometry and machines dominate: saucer 0.07,
triangle 0.11, oval 0.18, flashing 0.18, disc 0.20, metallic 0.21, formation 0.26, occupants 0.30, sound 0.30.

**Stable dimensions, where the 95% interval covers 1:** sphere 1.00, glow 0.87, cylinder or cigar 0.74, rectangle
0.87, cone 1.55, large 0.76, small 0.68, erratic 0.79, vanish 0.62, multicoloured 2.0, and physical effects (heat,
smell, paralysis) 1.21. These are the "potential signal" dimensions the protocol asks for. The next section tests
them.

**The mundane null drifts the same way.** Reports that name a natural phenomenon show the same pattern of change
across the 17 features both classes can estimate (r = 0.66), with at least as much drift (mean |log OR| 0.98 vs
0.85). If the unexplained reports had a constant stimulus behind them, their descriptors should drift less than the
descriptors of known phenomena described in the same changing language. They don't.

**Era boundaries** (table T4, equal n of 40 per era). Inside single compilers, the largest breaks are the 1896 airship
wave (2.0-2.1x noise in Hatch and Eberhart) and 1914 (2.1-2.3x). 1947 is a smaller break (1.2-1.6x). Once sample
size is held equal, 1947 is a vocabulary event (the word "saucer") more than a change in the whole descriptor
profile. The table form of the protocol's "temporal convergence map" is `deeptime_convergence_map.png`.

**The primary text confirms the frames are period voice.** Obsequens' 62 sky prodigies use only celestial (35%),
torch (10%) and martial (10%) frames. They contain no "object" or "mysterious" wording, no occupants, no hovering and
no glow (T7). Catalog entries for AD 34-499 carry religious frames (26%), occupants (7%) and "mysterious" (22%). That
is the compiler's voice layered on the ancient sources.

## Task 2.3: culture or signal?

**Technology tracking** (`deeptime_tech_frames.png`, table T8):

- **Saucer:** the change point is 1947 [1947-1947]. Of 141 uses before 1947, 121 are the compiler's own wording,
  71 of them Larry Hatch's (he codes round objects as saucers in any century, for example "Silver saucer darts to
  and fro" for 1733). 13 sit inside quotation marks, and I did not check those against the originals.
- **Satellite:** the change point is 1956 [1955-58] in the catalogs. In NUFORC, the word surges again in 2019,
  which is Starlink.
- **Drone:** the change point is 2012 [2012-14] in the catalogs and 2014 [2012-15] in NUFORC. The 23 catalog uses
  before 2013 are mostly mid-century military target drones (Eberhart), plus Hatch using "drone" as a verb
  ("saucers drone north").
- **Starlink or satellite train:** the change point in NUFORC is 2019 [2019-19], the first launch year. NUFORC's
  rate goes from 0.3 to 103 per 1,000 reports.
- **Airship and aircraft:** both rose after their t0 but lagged it. "Airship" ran at 12 per 1,000 in the 50 years
  before 1852 and 310 per 1,000 in the 50 years after, with the rise at the 1896-97 press wave rather than at
  Giffard. "Aircraft" went from 12 to 124 per 1,000 across 1903. Their single biggest steps are a fall (airship,
  1932) and the post-war rise (aircraft, 1954), so the one-step model does not date their arrival.
- **Not testable:** balloon (about 100 catalog records before 1783, and the 1780s hits are ascent context entries),
  rocket (fireworks since the Middle Ages) and lantern (centuries old).

**Shapes track the era, not just the words** (`deeptime_shapes_by_decade.png`, table T9). In Hatch, cigars are 35% of
1900s reports during the airship wave and searchlight beams 15-17% in the 1890s-1900s. Discs jump to 56% in the 1940s
and fall to 24% by the 1990s. Triangles are 0% before the 1940s and 12-17% in the 1980s-90s. NUFORC witness text
shows the same arc on its own: discs fall from 18% in the 1950s to 2.4% in the 2010s, triangles peak at 10% in the
1980s-90s, orbs and spheres rise to 18% in the 2010s, and formations or lines rise to 8.7% in the 2020s, the
Starlink era. Each shape peak sits on a contemporaneous technology, stimulus or media template: dirigibles, the
"flying saucer" press, stealth aircraft and the Hudson Valley and Belgian waves, sky lanterns, satellite trains.

**Newest vehicle.** From 1700 to 1946, among 1,012 reports that compare the thing to a vehicle, 57.5% name the newest
vehicle of their year (ship or wheel, then balloon from 1783, airship from 1852, aircraft from 1903). The null is
40.6% (97.5th percentile 43.0%) when years are shuffled within catalog, p = 0.0005.

**The invariant core is the description of known phenomena** (tables T2, T10 and T10b). Before 1800, the stable
descriptors are equally common in reports that name a comet, meteor, aurora or halo: cylinder 3.4% vs 3.8%, large
4.6% vs 4.9%, vanish 6.9% vs 6.9%, erratic 2.3% vs 1.8%, hover 8.0% vs 8.6%, sphere 12.6% vs 14.1%. In GEIPAN (base:
67% identified, 3.1% unexplained), sphere, glow and white lights are 68-69% identified and 2.7-2.8% unexplained.

**The one residue worth naming:** cylinder or cigar (10.2% unexplained), large size (10.7%), sudden vanishing (7.3%),
hovering (7.2%), triangle (6.7%) and erratic motion (6.1%) are over-represented in GEIPAN's D class against the 3.1%
base. Four of these (cylinder, large, vanish, erratic) are also stable over 2,000 years. That is the only place a
constant signal could still hide in descriptive data, and pre-modern comet and meteor reports carry the same four at
the same rates. A cylinder that is large and vanishes suddenly is also a bright meteor's train, or a fireball seen
end-on. Those descriptors are harder to explain because they are briefer and less specific, not because they are
anomalous. On this evidence I would not spend effort on them as a signal. If you want to, the test is GEIPAN D cases
with these four descriptors, checked against fireball networks and re-entry databases.

## Task -3.1: the evolutionary tree of UAP descriptions

`deeptime_tree.png`, table T12. Descriptions do not reproduce, so this tree maps similarity between description
populations. It is not proof of descent. What a tree can test is which factor its branching follows.

- **Taxa:** 49. These are every catalog x era cell with at least 40 unexplained reports, plus Obsequens, NUFORC in
  three eras, GEIPAN identified (two eras) and unexplained, and the natural-phenomenon reports in three periods.
- **Characters:** 46 descriptors (physical, frame, entity). Compiler-voice markers are left out, and so are the
  three features the natural-phenomenon regex feeds.
- **Method:** chord distance, neighbour joining, midpoint root, 200 bootstrap replicates.

**What organises the tree:**

| factor | Blomberg's K (p) | distance regression beta (p) |
|---|---|---|
| date | **1.99 (0.001)** | +0.035 per century apart **(0.001)** |
| same compiler | - | **-0.117 (0.001)** |
| witness-written vs compiled | **1.97 (0.001)** | +0.129 (0.07) |
| names a natural phenomenon | 0.78 (0.08) | -0.018 (0.81) |

The distance regression explains R² = 0.30 (p = 0.001). For 86% of taxa, the nearest neighbour is within 100 years,
and for 39% it is from the same compiler.

**Branching pattern.** All six pre-1800 catalog populations, Obsequens and the pre-1800 natural-phenomenon reports
fall in one clade, which also takes three 1800-1895 catalog cells (Hatch, rr0, Eberhart). Inside it, the pre-1800
natural-phenomenon reports are nested with Wonders in the Sky for 1000-1699 (62% support). There is an airship-era
clade of six compilers (98%) and a 1914-1946 clade of four (94%). Then come separate post-war clades for NUFORC
(99.5%), Hatch (99%) and GEIPAN (100%). GEIPAN-D sits inside the GEIPAN identified cases. Each natural-phenomenon
population sits with its own era's unexplained reports, not with the other natural populations. That is the
opposite of what a constant stimulus would produce. If something unchanging were behind the unexplained reports,
they would cluster together across eras, apart from the comets and meteors. Instead, every era's comets and UFOs
are described alike.

**Tree-likeness.** The delta score is 0.36, against 0.45 when each character is shuffled across taxa (p = 0.01). So
the populations are hierarchically structured, with a lot of reticulation, as expected when vocabulary is inherited
by period and catalogs borrow from each other. This is the protocol's "network phylogenetics" point: borrowing is
real, and the borrowing is between compilers.

**The answer to -3.1's question.** The "evolution" in UAP descriptions is cultural evolution of language, with
horizontal transfer between compilers. Description types do not show the branching you'd expect from a lineage of
craft, and the tree has no stimulus axis to evolve along.

## The ancient-astronaut hypotheses, as falsifiable predictions

| | prediction if ancient visitors were real and constant | result | verdict |
|---|---|---|---|
| AA1 | structured craft seen close are about as common before 1800 as after 1947 | 1.8% (1.1-3.2) vs 11.3% (11.0-11.7); within-catalog OR 0.07 (0.03-0.15); 1.6% without the LLM paraphrases | **fails.** The catalogs were compiled by ufologists hunting for such cases, a bias that favours the hypothesis |
| AA2 | occupants are described the same way in every era | religious or creature framing 30-55% before 1500, 2-4% after 1914; airship framing 52% of 1896-1913 occupant reports; space or alien framing never above about 5% | **fails.** Occupants wear each era's mythology |
| AA3 | an untouched ancient source shows craft features | Obsequens: 62 sky prodigies, 2 shape terms (both the sun's "disque"), 0 landings, 0 occupants; torches, suns, shields | **fails** for Rome, 191-12 BC |
| AA4 | the modern era is a "phase change": 1947 is the biggest break in the record | at equal sample size, 1896 and 1914 are bigger breaks than 1947 | **fails.** 1947 is a vocabulary event |
| AA5 | pre-1500 reports cluster where ancient-astronaut writers place contact (Egypt, Mesopotamia, India, Mesoamerica, Andes) | Europe 129, East Asia 75, South/West Asia and Africa 15, Americas 6 | **not testable here.** The distribution tracks where written chronicles survived, which is the catalogs' sampling, not contact |

The vimana texts often cited for this hypothesis cannot be used as ancient evidence. The *Vaimanika Shastra* was
written down in 1918-1923, and an Indian Institute of Science team (Mukunda et al., 1974) found its craft
aeronautically unworkable. No record in this corpus is a vimana account.

## Limits

- The catalogs are ufologists' selections and paraphrases, not the original witnesses. The within-compiler design
  and the Obsequens control limit this but do not remove it. The pre-1500 record is mostly European and East Asian,
  and the East Asian part comes through English summaries.
- The natural-phenomenon class is small before 1800 (87), so its intervals are wide.
- The ideal mundane null is Greg's 1860 *Catalogue of Meteorites and Fireballs, AD 2-1860* (BAAS Report 1860,
  archive.org `reportofbritisha61brit`). Its OCR is unusable (rotated tables), and the container has no tesseract to
  redo it.
- The coding is a keyword lexicon. That is auditable but noisy, and words are not perceptions.
- The tree is a similarity map. Phylogenetic statistics on it test organisation, not descent.

## What would move this forward

1. **Re-OCR Greg's 1860 fireball catalogue.** This needs tesseract or the PDF and gives a 1,800-year mundane null in
   period language.
2. **Add a non-European primary text.** The astronomical treatises of the Chinese dynastic histories (*tianwen zhi*)
   are dated sky records with no ufologist in between.
3. **Check the 13 quoted pre-1947 "saucer" uses** and the 12 quoted pre-1957 "Martian" or "alien" uses against
   their original newspapers.
4. **Run the GEIPAN D residue test from the invariance section:** cylinder, large, vanishing and erratic reports
   checked against fireball and re-entry databases.

## Reproduce

From the UFOAI repo root, with `../ufo_data` checked out beside it, run the craft taxonomy's
`omega/taxonomy/features.py` first. Then run `omega/deeptime/corpus.py`, `drift.py`, `tech.py`, `tree.py`,
`figures.py` and `report.py`, about 5 minutes in total. The Obsequens text goes in `data/raw/deeptime/` (source and
SHA-1 in `evidence_vault/13_DEEP_TIME/FETCH_MANIFEST.md`).
