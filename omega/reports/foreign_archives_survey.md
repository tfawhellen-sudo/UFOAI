# Foreign government UAP archives: survey, ranking, first analysis

Session date 2026-11-26. Branch `claude/project-thread-j9gkki`, cut from `claude/project-thread-eck2kl` (2c859c0).
Code: `omega/canada_nrc_venus.py`. Evidence: `evidence_vault/12_FOREIGN_ARCHIVES/`.

## Bottom line

1. **Nine national UFO collections are mirrored as OCR text on archive.org** (collection `ufo-files`). From this container that is the only way in, because every official host is blocked. Brazil, Canada, Australia, New Zealand, Spain, Denmark, Sweden, France and Ireland are now on disk (about 45 MB of text). The UK set is mirrored only as 232 scanned PDFs (5.7 GB) with no OCR, and those sit on blocked archive.org data nodes.
2. **Brazil 1986 "official UFO night": no sortie got all three sensors to agree in a sustained way.** Of 5 interceptor sorties, 4 got some presentation. Only one (JB 17) had a ground plot, a visual and an airborne radar paint, and the paint happened once. The Air Force's own same-night summary says the plots "nao chegaram a constituir pistas" (never formed tracks). It also says the Anápolis radar did not agree with the Gama radars.
3. **Canada 1967-78: report-days go up when Venus is high in the evening sky.** The rate ratio is RR 1.22 per 10° of Venus altitude after sunset (95% CI 1.07-1.40). The placebo, pre-dawn Venus, is flat: RR 1.02 (0.89-1.18). The permutation p is 0.053, so this is borderline. It is consistent with Venus misidentification inflating the official file, and it does not exclude anything else.
4. **Ranking by usefulness:** Brazil, then UK, Canada, Australia and Sweden (ghost-rocket debris). Chile, Argentina, Uruguay, Peru, Denmark, Japan and Ireland are thin.

## 1. Access: what was blocked and what worked

| Host | Result from container |
|---|---|
| discovery / cdn.nationalarchives.gov.uk, gov.br, sian.an.gov.br, recordsearch.naa.gov.au, bac-lac / canada.ca, nzdf.mil.nz, archives.govt.nz, riksarkivet.se, defensa.gob.es, mod.go.jp, argentina.gob.ar, sefaa.cl, fau.mil.uy, fap.mil.pe, forsvaret.dk, theblackvault.com, wikipedia, google | **blocked** (proxy 403). Content not guessed. |
| archive.org (metadata, advancedsearch, `/stream/`) | works |
| archive.org `/download/` → `ia*.us.archive.org`, `dn*.ca.archive.org` | **blocked** (data nodes) |
| web-fetch agent | can read the government PDFs above, but only as text, one at a time |

Workaround used: `https://archive.org/stream/<ID>/<file>_djvu.txt` returns the OCR text inside HTML. **Limitation:** page breaks are lost that way, so the citations below are by archival document and grep-verified line, **not by page**. Allowlisting the archive.org data nodes would bring back page-level text and the UK PDFs.

## 2. Survey and ranking

Mirror statistics come from `mirror_inventory.json`. The keyword "docs" columns are crude regex counts over noisy OCR. They show where to look, not how much evidence there is.

| Rank | Archive | Openness | Size reachable here | Radar / sensor | Physical trace | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Brazil**, Arquivo Nacional fund ARX (BR_AN_BSB_ARX_*, SIOANI 1969-72, CENDOC envelopes 1978-89) | Open (SIAN, free) | 231 docs, 6.3 MB text (mirror `BrazilianUFOFiles`) | **Yes**: ATC logs, ground radar plots, interceptor airborne radar, 1986 | Operação Prato injury claims (keyword: 18 docs) | Best mix of sensor and official chain of custody |
| 2 | **UK**, TNA DEFE 24 / DEFE 31 / AIR 2 | Open (free downloads) | 232 PDFs, 5.7 GB, **no OCR, blocked** | Some | Few | Biggest single release, but unreachable as text. Needs data-node allowlist plus tesseract |
| 3 | **Canada**, LAC RG 77 (NRC "non-meteoritic sightings"), DND, RCMP, CIRVIS 2010-19 | Open | 30 docs, 8,759 pp, 9.9 MB text (`CanadaUFO`) | Some (CIRVIS aircrew reports) | Falcon Lake, Shag Harbour are in LAC per the canada.ca guide (not checked here) | Largest clean time series, used below |
| 4 | **Australia**, NAA A9755, A703 580/1/1 series | Open (RecordSearch digitised) | 82 docs, **13.9 MB** text (`AustralianUFOFiles`) | radar: 62 docs | trace: 51 docs | Largest text body. Next target |
| 5 | **Sweden**, 1946 ghost rockets (FOA) | Open | 1,779 small files, 1.8 MB (`SwedishGhostRockets`) | 11 docs | **Impact and debris reports**: "trace" regex hits 129 docs, Swedish "spår/nedslag" is noisy | Only corpus where fragments were reportedly examined. Worth a dedicated pass |
| 6 | **New Zealand**, NZDF 2010 release | Open | 9 docs, 3.2 MB | radar: 8 of 9 docs (Kaikoura 1978) | few | Small but radar-dense |
| 7 | **Spain**, Ejército del Aire desclasificados | Open (Biblioteca Virtual Defensa) | 80 docs, 1.9 MB | radar: 40 docs | 12 docs | Manises 1979 class cases. Small |
| 8 | **Chile** CEFAA/SEFAA | Case-by-case press releases | not mirrored | Navy 2014 helicopter IR video (Black Vault case file, not fetched) | none found | No bulk archive |
| 9 | **Argentina** CEFAE (2011) → CIAE (2019) | Annual PDF reports online | not mirrored | none stated | none stated | CIAE 2024 report (via web-fetch): 36 cases analysed and 9 rejected. All 36 are resolved as known causes. Photo/video only. No raw data |
| 10 | Uruguay CRIDOVNI, Peru OIFAA | Press statements only | none | none found | none found | No public case archive located |
| 11 | Denmark (Flyvevåbnet 2009), Ireland | Open | 1 doc each | low | low | Thin |
| 12 | Japan MOD | Reporting procedure only (2020) | none | none | none | No case release found |

What is inferred: the ranking weights are my judgement (sensor data > physical traces > size > openness). Case counts for TNA, Denmark and Chile are not stated, because I could not verify them from a primary source here.

## 3. Brazil: the night of 19-20 May 1986

### Source
Mirror `BrazilianUFOFiles`, file "CENDOC ENVELOPE 08 1986", saved as `evidence_vault/12_FOREIGN_ARCHIVES/src/BR_CENDOC_ENVELOPE_08_1986.txt`. The core document is a CONFIDENCIAL Parte by 1° Ten Esp CTA Francisco Hugo Nunes Freitas to the Chief of Information of COpM I. It covers "19 MAI 86 23:15Z para o dia 20 MAI 86 03:32Z". It is filed with the pilots' own reports (Cap Av Márcio Brisolla Jordão and 1° Ten Av Kleber Caldas Marinho, both dated 28 May 1986) and raw telexes.

### Sortie table (`br1986_sorties.csv`)

| Callsign | Ground plot | Airborne radar | Visual | All three |
|---|---|---|---|---|
| JB 17 (Santa Cruz) | Y | Y, **once**, 10-12 NM | Y, white light | Y, single paint |
| JB 07 (Santa Cruz) | Y | not stated | Y, red light went out | N |
| JG 116 (Anápolis) | Y, Anápolis TA-10 only | Y, "JUDITE" on all 5 presentations | **N** | N |
| JG 98 (Anápolis) | – | – | – | no presentation |
| JG 107 (Anápolis) | Y | N | N | N |

Concordance: 1 of 4 sorties with a presentation got all three sensors together (Wilson 95% CI 5-70%). n is tiny, so this is a description, not a test.

### Verified quotes (all grep -F matched, `quotes.txt`, 24/24)
- Conclusion: `"PLOTS", nao chegaram a constituir pistas. Houve um grande numero de`
- Radar disagreement: `as dos radares do Gama, os acionamentos portanto, basearam-se mais` (the preceding line reads "As informagdes do radar de Anapolis nao coincidiram com").
- Count: `de vinte "PLOTS" o maior numero em Sdo José dos Campos.`
- JG 116: `Féz cinco apresentagdes, em todas obteve "JUDITE" mas nenhum conta[to visual]`
- JB 17: `"radar de bordo" entre 10 e 12 NM. O "objeto" aparentava um ponto`
- JB 07: `missao foi o aparecimento de treze '"'PLOTS''na cauda do JB 07 que fez uma cur[va de 180°] … mas nao visualizou nem detetou nada.`
- Data loss: `2) O video de SH Roque nao foi gravado por problemas técnicos .` Also the JB 17 visual time and JG 116 radar time "foram estimados", because the recorder did not log times.
- Jordão: `tava clara, sem nuvens e com uma lua cheia. Nao obtive contato visual`

### Other 1986 entries in the same envelopes
- Memo dated 24 Jun 1986 (Env. 08): JBAZ reported a contact, `"THOR" nao tinha contato radar com o objeto informado,`. Both aircraft then had visual and `to no radar de bordo. Informaram ter contato a cerca de 08 NM.` They chased to Mach 1.2 and the target left airborne-radar range. **This is the strongest airborne-radar-plus-visual entry found**, but ground radar did not see it. The event date is not in the extracted lines.
- 27 May 1986 (Env. 07): ACC BS `captava um plote primario com velocidade de 813KT` while TF 402 saw a strong light. On the same night, for RG 256A's following lights, `O ACC BS nada captou no radar, nem tampouco o APP BH.` FAB 2177 near Belo Horizonte reported `dois baloes`.
- 12 Jun 1986 (Env. 07): fighters saw coloured lights and the Gama LP-23 `tetou nenhum movimento anormal`.

### Red team
- **Plots, not tracks.** Single primary returns that do not chain into tracks are the signature of clutter and anomalous propagation, not of a body moving through space. A real 813 kt object would make a track. This is inferred from radar practice, not stated in the file.
- **Sensors disagree.** Anápolis TA-10 and the Gama radars did not agree. JG 116 got airborne locks with no visual, and JB 07 got a visual with no lock. The Air Force said this itself.
- **Astronomical candidate for JB 17.** At 01:45Z on 20 May from Santa Cruz, Canopus (mag −0.6) was at azimuth about 210°, altitude 0-2° and setting (PyEphem). That matches "uma para duas horas baixo" on heading 180°, the scintillating green/red/white colours, and "no closure". **It fails on elevation**, because the pilot puts the object 10° above his plane as he climbed. So Canopus cannot be the whole story, and the single radar paint is not explained by it. Mars (−1.2, east) and Saturn (high) do not fit the bearing. The moon was 81% lit (Jordão: "lua cheia").
- **Missing data cuts both ways.** The tapes have no times, one video was not recorded, and the Gama video was delayed. No raw radar data from that night is in this archive.

## 4. Canada: Venus null model (1967-1978)

### Data
Mirror `CanadaUFO`, 29 "Canada - FOIA" parts (8,759 pp; NRC RG 77 with "RG 77" in 4,956 OCR lines; also DND and RCMP). Unit: a distinct calendar date in military short form (`24 NOV 79`). This gave 2,333 raw mentions and **896 distinct dates** for 1967-78. Peaks are in 1969 (149) and 1975 (107).

### Model
Negative binomial GLM of monthly distinct dates, with year and calendar-month fixed effects. The predictor is Venus altitude 1 h after sunset at Ottawa on the 15th of the month. Venus's 584-day synodic cycle decouples it from both seasons and years.

| Test | Result |
|---|---|
| Evening Venus, RR per 10° | **1.22 (95% CI 1.07-1.40)**, Wald p = 0.003 |
| Circular-shift permutation (133 shifts ≥ 6 months) | p = 0.053 |
| Placebo: Venus 1 h before sunrise | RR 1.02 (0.89-1.18), p = 0.75 |
| Minimum detectable RR at 80% power | 1.21 |
| Weekend share of dates | 24.6% (21.8-27.5%) vs 28.6% null |

### Reading
- The evening-not-morning pattern is what misidentification predicts, because people are outside in the evening. The permutation p of 0.053 is borderline, and the effect sits right at the detection limit. Treat it as **suggestive, needing replication**: the obvious test is the same model on Australia's NAA series.
- The **weekend deficit** says many of these dates are message or report dates, logged on office days, not sighting dates. That is fine at monthly resolution, but it rules out any day-level analysis on this extraction.
- Red team: OCR misreads days (for example 2→Z), and NRC staff filtered meteors out, so the file is not a random sample of sightings. Year fixed effects absorb the 1967 and 1969 waves but not media spikes within a year.

## 5. What this does and does not say about NHI
Nothing here needs a non-human explanation. The best Brazilian sensor cases are consistent with plots and visuals that do not agree, plus one or two airborne-radar episodes (JB 17, JBAZ) that remain unexplained in the record. Without raw radar tapes they cannot be tested further. The Canadian Venus signal accounts for part of a large official file. It says nothing about the residue.

## 6. Next steps (ranked)
1. Ask the owner to allowlist the archive.org data nodes (`*.us.archive.org`, `*.ca.archive.org`). That brings back page-level cites and the UK PDFs.
2. Replicate the Venus model on Australia (13.9 MB text) and Spain. A pre-registered RR > 1 with the same placebo would firm up finding 3.
3. Swedish ghost rockets: extract every impact or debris report and what FOA said the fragments were.
4. Brazil: FOIA-style request to the Arquivo Nacional or COMAER for the 19-20 May 1986 Gama and TA-10 video recordings mentioned in the Parte.

## Citations
- archive.org items: `CanadaUFO`, `BrazilianUFOFiles`, `AustralianUFOFiles`, `NewZealandUFO`, `SpanishUFOFiles`, `DanishUFOFiles`, `SwedishGhostRockets`, `FrenchUFOFiles`, `IrishUFOFiles`, `BritishUFOFiles` (collection `ufo-files`, uploader Mike Best, 2015).
- Argentina CIAE 2024 report, argentina.gob.ar/sites/default/files/2018/11/informe-ciae-2024.pdf, read through web-fetch, first ~25 pp verbatim.
- Survey pointers from web search (titles only, not opened): TNA UFO highlights guide 2013, canada.ca "Canada's UFOs: the search for the unknown", NAA A9755 items, gov.uk "UFO reports in the UK", Japan MOD White Paper 2020.
- Verify quotes: `cd evidence_vault/12_FOREIGN_ARCHIVES && while IFS=$'\t' read f q; do grep -qF -- "$q" "$f" || echo MISS; done < quotes.txt`
