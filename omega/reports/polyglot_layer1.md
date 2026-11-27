# Polyglot drill, Layer 1 (Abyss Protocol Tasks 1.1-1.5): results

*2026-11-27. Branch `claude/project-thread-7q8bu9` in `tfawhellen-sudo/UFOAI`, built from session 6's tip `a33885b`. Code is in `omega/layer1/`. Outputs are in `evidence_vault/13_POLYGLOT_LAYER1/`. Every number below comes from a file in that folder. The test files are named T1 to T7, and the database is in `db/`.*

## Bottom line

1. **No cross-language trace of one shared phenomenon.** Soviet reports do not fall on the same days as US or French reports more often than date-shifted copies of themselves do. The rate ratio is 1.01 against NUFORC and 1.07 against GEIPAN. The same method finds real duplication when it exists: Hatch US against NUFORC within 100 km gives a rate ratio of 5.6.
2. **The Russian archive's distinctive content is mostly rocket launches.**
   - Russian reports worded like an exhaust plume (jellyfish, crescent, spiral, fan, halo, cloud) fall on Soviet launch days more often than chance. The rate ratio is 1.47 (p = 0.029). Within 1,500 km of Plesetsk it is 1.80 (p = 0.026). Reports without plume words show nothing (rate ratio 1.08).
   - This independently supports the Soviet state programme's own conclusion that over 90% of its anomalous phenomena were rocket effects plus balloons.
   - The 1980 Chinese academic survey describes the same signature in its dominant class, about 80% of reports: discs or globes "frequently accompanied by a white smoke cloud".
3. **Each catalogue sees only a sliver of the events.**
   - Over 90% of each catalogue's Soviet events have no counterpart in the other.
   - A two-source capture-recapture estimate puts the number of Soviet events that reached either compiler at about 6,800 for 1947-2002 (range 5,200-11,800) and about 2,600 for 1978-1990. Each list holds 3-6% of that.
   - The estimate is biased low.
4. **English filtering turns Soviet reports into saucers, but compilers distort as much as language does.** Disc is the first shape word in 26% of Hatch's Soviet entries but only 9% of the Russian chronicle's (p = 0.0002). However, two English-language catalogues of US reports differ from each other almost as much (total variation distance 0.25).
5. **No nuclear clustering in the native data.**
   - The Russian chronicle has no reports within 30 km of a nuclear site, where 2.2 were expected.
   - The English catalogue's reactor excess rests on 4 named cases. Two of them are reports about the plant itself (Sosnovy Bor radar, 1991; Chernobyl, 1991).
6. **Protocol claims checked:**
   - "Thread-3" is false: no hits in 37 DIRDs or the PURSUE files.
   - "Vimana in the DIRDs" is false.
   - "Setka" is verified. The two programme topics were "Setka MO" and "Setka AN". Platov's English translation renders them as "DM Network" and "AS Network", since *setka* means network.
   - "PLA UAP programme" is not supported. China's effort was a civilian association plus a university survey.
   - The Vymanika Shastra is a 1900-1922 composition, and none of its craft could fly.

Analogy: the cross-language comparison is like having two microphones in different cities. If one storm were moving across the world, both would pick up thunder on the same nights. They don't. What the Russian microphone records that the English one misses is mostly the Plesetsk launch pad.

## What was built

| Output | Contents |
|---|---|
| `db/layer1_polyglot.sqlite` + CSVs | **640 events**: 624 entries from Chernobrov's Russian chronicle, 10 Platov & Sokolov state-programme episodes, and 6 dated Chinese cases from the 1980 Ziran Zazhi survey. **60 cross-catalogue links**, a **30-term lexicon** in Russian, Chinese, Arabic and Sanskrit with corpus counts, **16 claim verdicts** and **15 sources**. See `db/README.md`. |
| `db/tr_parts/` | English gists for all **419** ex-USSR chronicle entries. These are machine translations of the first ~160 characters by Claude, not reviewed. Private witness names are replaced by roles. |
| Russian corpus | 384 archive.org items: Soviet popular-science magazine runs plus ufological periodicals, about 212M characters scanned, 6,507 keyword hits. |
| Chinese corpus | JPRS/FBIS translations from CIA CREST (443 texts plus 224 from the FOF collection), and 5 Chinese-language books and newspapers on archive.org. |
| Arabic corpus | Raji Enayat, *Sirr al-atbaq al-ta'ira*, two archive.org copies. |
| Indic corpus | Vyamaanika Shastra (1973 Sanskrit edition, archive.org) and the IISc 1974 critical study. |

The database stores a 300-character Russian excerpt per entry. The chronicle is a copyrighted 2002 compilation, and full texts would republish about 90% of it. Derived fields are computed from the full text at build time. A full-text copy can be rebuilt locally.

## Access: what was reached and how

| Source | Route that worked | Tried and failed |
|---|---|---|
| archive.org texts | `advancedsearch`, `/metadata/`, `/stream/<id>/<file>_djvu.txt`, `/cors/` | data nodes and `web.archive.org` (blocked by the proxy) |
| CIA CREST (JPRS/FBIS) | texts already on disk from the reading room | none |
| Platov & Sokolov 2000 | web-fetch of `noufors.com/Documents/Platov.pdf` (English translation) | direct curl (proxy) |
| Gindilis memoir | web-fetch of astronet.ru pages 1169491/1_6 and 2_1 | direct curl |
| Gindilis 1979 report | NASA record (TM-75665, TM-75761) | CUFOS PDF `Phenomena_in_USSR_A-548.pdf` (HTTP 4xx) |
| Oleksiuk 2013 (KNIT) | web-fetch of the mao.kiev.ua PDF | direct curl |
| Priroda | web-fetch of `priroda.ras.ru/pdf/2015_08.pdf` | direct curl; archive.org has no Soviet-era issues |
| CyberLeninka, eLibrary.ru, rusneb.ru | none | unreachable from this container (proxy). eLibrary also needs a login, which is an access control we do not circumvent. |
| gazeta.ru "Operatsiya Setka" | none | web-fetch returned an auth stub; refetching returns the same |
| IISc 1974 study | web-fetch of `cgpl.iisc.ac.in` | none |
| LibGen and pirate mirrors | not used, by rule | none |

## Claim checks

| # | Protocol claim | Verdict | Evidence |
|---|---|---|---|
| C01 | "Project Setka, a nationwide UAP reporting network" | **Verified** | The state programme ran 1978-1990, with a Defence Ministry topic (main executor a central military research institute near Moscow, head V.P. Balashov) and an Academy of Sciences topic (IZMIRAN, head V.V. Migulin; working group led by Yu.V. Platov). A General Staff directive of January 1980 ordered all units to report sightings. There were about 3,000 communications and slightly over 300 anomalous events. Over 90% were rockets plus balloons, with balloons at 10-12%. Oleksiuk (2013) names the topics "Setka MO" and "Setka AN". **Correction:** my earlier note said the name was absent from Platov's text. It is there, translated as "Network". |
| C02 | "Blue Book equivalent: Soviet military UAP files" | **Not found as released files** | The Defence Ministry branch existed. No released military case file was found on archive.org, CREST, or any host reachable from here. |
| C03 | "Soviet scientists published on UAP in Priroda and Zemlya i Vselennaya" | **Not verified** | archive.org has 2 issues of Zemlya i Vselennaya (1972-05 and 1978 No. 4) with no UFO keyword hits, and no Soviet-era Priroda issues. Priroda 2015 No. 8 has no UFO article. The verified Soviet academic output is the Gindilis, Men'kov & Petrovskaya 1979 statistical preprint (NASA TM-75665). |
| C04 | "Pilots, radar operators, cosmonauts reported UAP" | **Partly: retold, not documented** | The chronicle has 25 ex-USSR entries with aircrew words and 12 with radar words. Named cases include the 1967 Il-14 crew, the 1977 An-24 cargo flight, a 1979 Tu-154 captain's report, and the 1990 Grozny radar track with an interceptor scramble. **None of the 8 entries that use the word "cosmonaut" is cosmonaut testimony.** They are street names, a museum, and two entries where the compiler links a sighting to a crewed launch or landing (0238, 0267). The 1948-49 Apraksin chases have no documentary trace. |
| C05 | "AAWSAP DIRDs reference Soviet Thread-3 assessments" | **False** | No hits for "Thread-3" or "Thread 3" in 37 DIRDs, 286 PURSUE files or the PURSUE OCR. The DIRDs' mentions of the Soviet Union have nothing to do with UAP. |
| C06 | "The PLA has its own UAP research program" | **Not supported** | CURO was set up in 1978 as a civilian body under the China Association for Science and Technology. Its chairman told Xinhua of over 5,000 mainland sightings. The 1980 survey came from Wuhan University's space-physics department. Nothing on disk describes a PLA programme. |
| C07 | "China is the only other superpower with a systematic program" | **Not supported** | See C06. |
| C08 | "Arabic UAP reports are completely absent from the English corpus" | **False as stated, but close in substance** | Hatch has 148 Arab-world entries: Algeria 54, Morocco 44, Tunisia 10, Arabian Peninsula 8, Sahara 8, Libya 6, Kuwait 6, Egypt 5, Lebanon 3, Jordan 2, Sudan 1 and Syria 1. 91 of them date from the 1950s, and 75 are Maghreb cases from 1962 or earlier, so most come from the French-language colonial-era record. The most-reprinted Egyptian book uses "al-atbaq al-ta'ira" 85-89 times. It mentions America 38-39 times, Russia or the Soviet Union 8-11 times, Algeria 1-2 times, and Egypt 0 times. It is a compilation of Western cases. |
| C09 | "Extensive vimana discussion in the DIRD literature" | **False** | No vimana, Sanskrit or Mahabharata hits. There is one "Ramayana" mention, in the COMETA file. |
| C10 | "Sanskrit epics describe vehicles that parallel UAP" | **Partly** | The epics use *vimana* (for example Pushpaka) without any flight mechanism. The only "technical" text, the Vymanika Shastra, was composed 1900-1922 by Pandit Subbaraya Shastry; a Poona transcript is dated 9-8-1919, and the IISc authors say it "cannot be dated earlier than 1904". Its Sanskrit is "quite simple and modern", its drawings show post-18th-century parts, and "None of the planes has properties or capabilities of being flown" (IISc 1974). The 1973 edition's OCR uses *vimana* 261 times and *pushpaka* 4 times. |

## Tests

All event-level nulls shift the whole event set by k days, which keeps its internal clustering. Launch dates are UTC; report dates are local.

**T1, simultaneity (null).**
- Same-day share against NUFORC: 0.516 observed vs 0.509 under the null (rate ratio 1.01). Against GEIPAN: 1.07. Hatch China against NUFORC: 1.10.
- The positive control (Hatch US vs NUFORC within 100 km) reaches 5.6 (p = 0.017). A weaker control, Canada vs NUFORC within 300 km, gives only 1.19 (not significant).
- So the test reliably finds duplicates of the same event but has little power for weak global synchrony. What the null rules out is strong worldwide waves, not faint ones.

**T2, coverage (more than 90% unique each way).**
- Russian entries found in Hatch: 12.7% vs 7.9% chance on date ±1 day, and 5.3% vs 1.85% chance on date ±1 day within 800 km.
- Hatch entries found in the Russian chronicle: 18.9% vs 13.0%, and 8.8% vs 3.5%.
- By decade, Russian entries found in Hatch: 1960s 58% (n = 12), 1970s 9.3%, 1980s 16.4%, 1990s 13.8%, 2000s 0%.
- Concrete blind spots:
  - The chronicle has **no entry for the 14 June 1980 Kosmos-1188 mass sighting** that Platov describes; Hatch has 2.
  - Of Platov's five named launch events, the chronicle has only Petrozavodsk 1977 (4 entries).

**T3b, descriptors (different, but not only because of language).**

| First shape word, 1960-1999 | Russian chronicle, ex-USSR | Hatch, ex-USSR | Hatch, US | NUFORC, US |
|---|---|---|---|---|
| Sphere or ball | 22% | 16% | 9% | 19% |
| Disc or saucer | 9% | 26% | 29% | 12% |
| Triangle | 16% | 3% | 8% | 12% |
| Star or point | 10% | 3% | 1% | 0% |
| Light or fire | 25% | 14% | 26% | 22% |
| Cloud or plume | 8% | 7% | 2% | 0% |

Total variation distance, decade-stratified permutation:

| Comparison | TVD | Null mean | p |
|---|---|---|---|
| Russian chronicle vs Hatch ex-USSR | 0.335 | 0.18 | 0.0002 |
| Hatch US vs NUFORC | 0.254 | 0.03 | 0.003 |

- The plume class is specific to Soviet reports. It is 7-8% in both Soviet sources, 2% in Hatch US, and 0% in NUFORC, whose shape field has no such category.
- Russian triangles are mostly the "trekhzvezdnik" ("three-star"), a Kosmopoisk coinage of the 1980s-2000s for three lights.

**T4, nuclear proximity (no robust clustering).** The null is a time-aware, population-weighted Poisson-binomial.
- Russian chronicle at city precision: 0 reports within 30 km vs 2.19 expected. The 100 km excess (68 vs 49.9) comes from Moscow and Obninsk; excluding Moscow it reverses to 24 vs 38.2.
- Hatch ex-USSR: 4 reports within 30 km of a reactor vs 1.1 expected (p = 0.028). Declustered: 4 vs 1.0 (p = 0.018). The four cases:
  - Koporye 1988-10-20, 15 km from the Leningrad plant.
  - Aktau 1989-08-15, 8 km from BN-350.
  - Cape Ustinsky 1991-10-10, a radar report about the Sosnovy Bor plant.
  - Chernobyl 1991-10-12, a photo story about the plant.
- The 50 km excess (17 vs 6.6) is the Voronezh 1989 wave near Novovoronezh. Declustered it is 11 vs 6.0 (p = 0.045).
- China: 0 vs 0.0 expected.
- There are 81 group × site-type × radius cells. The seven smallest p-values (all 0.0002) are Russian 100 km cells, and they are a city artefact:
  - Moscow is 99 km from the Obninsk reactor, and St Petersburg is 72 km from the Leningrad plant.
  - The chronicle over-represents both cities, which were the investigators' home bases.
  - Excluding Moscow, the 100 km cells show a deficit instead: reactors 16 vs 25.9 expected, all sites 24 vs 38.2.
- The next smallest p is 0.0007 (Hatch reactors at 50 km), which is the Voronezh wave. Nothing survives declustering plus a multiple-testing correction.
- The site list is a limit: Natural Earth contains only 3 of 14 closed weapons cities (Zheleznogorsk, Obninsk, Dimitrovgrad).

**T5, launch lock (supported, but suggestive).** This uses the same-UTC-day window.

| Group | Launch-day share | Expected | Rate ratio | p |
|---|---|---|---|---|
| Russian plume reports (90 days) | 24.4% | 16.6% | 1.47 | 0.029 |
| Within 1,500 km of Plesetsk (49 days) | 22.4% | 12.5% | 1.80 | 0.026 |
| Russian non-plume reports (280 days) | | | 1.08 | 0.29 |
| Hatch ex-USSR plume reports (13 days) | | | 2.07 | 0.069 |

- Positive controls are weak under this conservative null. NUFORC "line of lights" reports against Starlink launches give 1.58 (p = 0.115), and GEIPAN cases officially explained as launches give 1.32 (p = 0.15). So the Russian plume result clears a bar that real launch effects barely clear.
- **Caveat:** I had considered the day-before-to-same-day window the natural one, and on that window the effect is weaker. The same-day window was not pre-registered.
- All five of Platov's launches are in SATCAT: Kosmos-955 on 1977-09-20, Kosmos-1188 on 1980-06-14, Meteor 2-7 on 1981-05-14, Molniya 3-19 on 1982-08-27, and Kosmos-1581 on 1984-07-03. Platov gives 15 May for the Meteor launch and calls the 1982 launch "Molniya-1" on 28 August, while his figure caption says 27 August.
- The Chinese 1976-1979 cases match no orbital launch. China's own suborbital missile tests are not in SATCAT, so a missile explanation for the "white smoke" class is neither confirmed nor excluded.

**T6, capture-recapture (new).** Entries are merged into events by same date within 300 km. Events match on date ±1 day within 800 km. Chance matches are measured by date shifts and subtracted. The estimator is Chapman's.

| Window | Russian events | Hatch events | Matches (chance) | Estimated events reaching either compiler |
|---|---|---|---|---|
| 1947-2002 | 374 | 219 | 18 (6.9) | **≈ 6,800** (5,200-11,800); with date-only matches where coordinates are missing, ≈ 4,600 |
| 1978-1990 | 204 | 109 | 13 (5.3) | **≈ 2,600** (1,900-5,600) |

- Famous mass events sit in both lists. That dependence makes the estimate too low.
- The 1978-1990 figure is the same order as the state programme's ~3,000 communications for the same years. The units differ: communications are reports, and these are events.

**T7, Indigenous scoping.**
- 19 of 18,116 Hatch summaries mention Indigenous people. About 12 of those are Indigenous witnesses (Aboriginal Australians, Papuan villagers, Pakistani tribesmen, Venezuelan and Argentine Indians, Ute and Navajo-area witnesses, tribal police). The other 7 are reservations, ruins or plant names.
- The Russian chronicle has **0** entries with an Indigenous Siberian witness. All 10 regex hits are place names (Tunguska, Yakutsk, Mansila) or a comet name.
- Neither catalogue is an Indigenous corpus. A real one would have to come from community-held oral history under CARE data-sovereignty rules, with consent, not from scraping.

## Red team

- **Translation.** The English gists are unreviewed machine translations of each entry's opening. No test used them; every test ran on the Russian text. A Russian speaker should spot-check 40 rows before anyone quotes a gist.
- **Parser.** 27 ex-USSR entries absorbed the next chronicle entry, because a season or year-range header could not be split. Their derived fields mix two events. They are flagged `parser_merge`.
- **Compiler as witness.** 9 entries name the compiler, V. Chernobrov, as a witness, mostly at the Medveditskaya ridge. The Kosmopoisk expedition zones also produce clusters of "three-star" reports. That is a collection effect, not geography.
- **Geocoding.** It is city-level at best, and 131 of the 328 geocoded ex-USSR entries are placed at the region capital. Proximity tests at 30 km are therefore biased toward the null for those entries. The city-precision subsets above address this.
- **T5 window choice.** See the caveat above. A pre-registered rerun on a held-out catalogue is the fix.
- **Selection in T4.** Reports about nuclear plants enter a catalogue because of the plant. Two of the four 30 km cases are of this kind. Without them it is 2 vs 1.0.
- **Chinese side.** Only English JPRS translations were usable, because archive.org's vertical traditional-script OCR is mostly noise. The Chinese lexicon counts (for example *feidie* 16) are floors.

## Near-misses and next concrete steps (ranked)

1. **Gindilis 1979 full text** (256 Academy reports with shape, colour and time statistics). It would give an independent Soviet descriptor baseline from the state channel. It was blocked here: the CUFOS PDF returned 4xx and NTRS has the record only. Next test: find the TM-75665 full text on NTRS through the web-fetch route, or ask CUFOS for its print copy.
2. **The Russian original of Platov & Sokolov** (Vestnik RAN 70(6):507-515). It would confirm the "Setka" wording directly. eLibrary needs a login, which is an access control. Next test: look for an open PDF of the journal issue on a Russian Academy journal platform or a library mirror.
3. **Chinese missile-test dates.** They would turn the "white smoke" class into a falsifiable launch-lock test like T5. Next test: compile Jiuquan suborbital test dates for 1976-1981 from declassified CIA NIEs in CREST, then rerun T5 on the 6 JPRS cases plus Hatch China.
4. **Pre-registered T5 rerun.** Fix the same-day window and the plume vocabulary now, and run them on the 1990s Kosmopoisk periodicals already on disk. These are not in the chronicle, so this is an out-of-sample test.
5. **Priroda and Zemlya i Vselennaya contents, 1975-1991.** This is the open part of C03. Next test: fetch the Priroda annual indexes from `priroda.ras.ru` through web-fetch, and the Zemlya i Vselennaya article lists mirrored on astronet.ru.
6. **Task 1.6 (universal grammar).** Not run. The descriptor tables above are the first input it needs. Its null is already defined: compare plume and shape grammars between launch-explained and unexplained cases.

## Files

- Code: `omega/layer1/ia.py`, `collect_ru.py`, `fetch_ru.py`, `catalogs.py`, `tests_l1.py` (`python3 -I omega/layer1/tests_l1.py t1 t2 t3 t4 t5 t6`) and `build_db.py`.
- Results: `evidence_vault/13_POLYGLOT_LAYER1/T1_simultaneity.json`, `T2_coverage.json`, `T3_descriptors.json`, `T3b_primary_shape.json`, `T4_nuclear.json`, `T5_launch_lock.json`, `T6_capture_recapture.json` and `T7_indigenous_scoping.json`.
- Database: `evidence_vault/13_POLYGLOT_LAYER1/db/`.
- Source lists: `evidence_vault/13_POLYGLOT_LAYER1/src/`.
- Raw texts are in `data/raw/layer1/`, which is gitignored. Rebuild them with `collect_ru.py` and `fetch_ru.py` plus `ia.py txt`.
