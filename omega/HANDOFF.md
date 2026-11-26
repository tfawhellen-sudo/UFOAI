# PROJECT OMEGA — session handoff

*Updated 2026-11-26 (session 5 consolidation). §1.16–1.17 and the rewritten
§2–§6 are from the session-5 merge; §1.14–1.15 from session 4; §1.12–1.13 from
session 3; §1.9–1.11 from session 2; §1.1–1.8 from session 1.*

Current branch: **`claude/nice-ritchie-j1ve90`** in `tfawhellen-sudo/UFOAI` —
the consolidated line, and the only branch holding all of sessions 1–5. Five
earlier branches are superseded; see §2 before you branch from anything.
Read this file first in a new session.

**Later sections correct earlier ones in their own voice.** Precedence, highest
first: **§1.16 › §1.14 › §1.12 › §1.9 › §1.1–§1.8.** Specifically: §1.4's ladder
is superseded by §1.14's seed-averaged table; §1.5's label for D182 and §1.14
item 3's area-coverage claim are superseded by §1.16; §1.2's anti-ionising
argument is split by §1.16 item 3 — the γ-benchmark stands, the pattern argument
does not.

---

## 0. Standing constraints (carry these forward verbatim)

- FOIA / declassified / public data only. No stolen or classified material.
- No connecting to classified systems.
- No fabricated results. A negative result is reported negative.
- Do not file FOIA requests — draft them only.
- No noise with physics words attached.
- **No user-agent spoofing, no routing around proxy blocks.** The honest UA in
  use throughout is `omega-research/1.0 (academic UAP data study;
  non-commercial)`. Locating the same public data on a different host is
  research and is in scope; circumventing an access control is not.

---

## 1. What each session added (cumulative — read §1.16 first for what it overrides)

### 1.1 GEIPAN — the French state case file (the big acquisition)

`/fr/cnes/export/cas` on `www.geipan.fr` is a published bulk-export endpoint
linked from GEIPAN's own case-search page. It returns the complete French state
UAP case file.

- **3,404 cases**, 19 fields, **coordinates on every record**, 1937–2026.
- Official disposition on every case: **A 955 / B 1323 / C 1020 / D 106**.
- A = identified certain, B = probably identified, **C = unidentified for lack
  of information, D = unidentified despite adequate information.**
- Blue Book conflated C and D. GEIPAN separates them → **first ground-truth
  denominator in the project.**
- Saved: `data/raw/geipan/geipan_cases.json` (committed).

### 1.2 GEPAN Note Technique No. 16 — acquired, read, quoted

`CT/GEPAN-00013`, `ENQUETE 81/01`, *ANALYSE D'UNE TRACE*, 1 March 1983,
ISSN 0750-6694, **67 pp, 109,615 chars of extractable text**. Case
`1981-01-00849` TRANS-EN-PROVENCE (83) 8 Jan 1981, classified **D**.
Full dossier: 10 files, 177 pages, 14.4 MB (corrected 2026-11-26; earlier "11 documents, 172 pages" did not match the files). Write-up and replication: `omega/reports/nt16_writeup_and_replication.md`.

Two findings in the primary document that the secondary literature omits:

1. GEPAN's own lab table gives the spark-mass-spec reading as
   « Trace laissée sur le sol pouvant provenir d'un revêtement primaire
   (peinture) ayant été frotté » — **rubbed paint from "un corps de masse
   importante"**. Mechanically sufficient for every soil finding — but §1.16
   item 3 shows the lab's two plates of the same soil disagree by a median factor
   of **23**, so this rests on the lab's prose, not on a reproducible measurement.
2. The INRA author **tested and rejected an ionising-radiation mechanism**:
   10⁶ rads of γ needed on *Arabidopsis* for equal-or-lesser pigment damage,
   and « L'action du rayonnement nucléaire ne présente donc pas d'analogie avec
   celle de la source énergétique impliquée ». Proposes **Mg²⁺ loss under an
   electric field** instead. Bears directly on Phase 2 and on the
   fallout-fogging alternative to arXiv:2604.00056.
   **Amended by §1.16 item 3: the γ-benchmark stands as INRA's own text, but the
   carotenoid-over-chlorophyll *pattern* argument does not — within analytical
   noise in series 1, and it reverses at the centre in series 2.**

Pigment loss: **30–50% active forms at 40 days**, β-carotene −57%,
violaxanthine −80%, correlated with distance from centre. GEPAN §8 explicitly
declines to treat any of it as confirming the witness.

Full quotes with section refs: `omega/reports/geipan_acquisition_and_disposition.md`

### 1.3 Two disposition results

**The unexplained residue fell 3.78×.** D-rate 0.0543 (≤1988) → 0.0144 (2007+),
z=+6.119, **p=9.4e-10**. C-rate 0.4955 → 0.2076. A+B 0.4502 → 0.7780. Not
caseload dilution (Spearman −0.1295, p=0.360, 52 years). Cause is in the data:
top modern identified cause is **sky lanterns (417)**, a product absent from
France before ~2005; then aircraft (93), **ISS (79)**. The toolkit changed, not
the sky.

**The D arm is the least documented arm, and it survives stratification.**
Document-attachment share D 0.4528 vs A+B 0.9794 (z=−25.83). Within-era,
D-weighted **−0.5351** vs marginal −0.5265 — no Simpson reversal. 1977–1988:
**0.152 vs 0.993, p=3.5e-58.** The cases the French state calls genuinely
unexplained are the cases whose documents are not published. → CADA request
target (France's FOIA analogue), naming case IDs.

### 1.4 Failure mode #7 — criterion-definitional confounding

The C-vs-D narrative test needed five decontamination tiers to interpret:

**SEED-AVERAGED IN SESSION 4 — use these, not the single draws.**
(`omega/reports/geipan_tier_seed_stability.md`)

| Tier | removed | **seed-averaged effect** | range | old single draw |
|---|---|---|---|---|
| L0 | nothing | **+0.3387 ± 0.0229** | 0.094 | +0.3494 |
| L1 | sentences naming GEIPAN/class | **+0.2771 ± 0.0300** | 0.109 | +0.3019 |
| L2 | + verdict lexicon | **+0.2628 ± 0.0318** | 0.109 | +0.3113 |
| L3 | + analyst-reasoning sentences | **+0.2333 ± 0.0308** | 0.113 | +0.2643 |
| L4 | + conjugated forms, length-matched | **+0.2135 ± 0.0276** | 0.109 | +0.2176 |
| L5 | + all numerals and quantity words | **+0.1972 ± 0.0271** | 0.104 | +0.1795 |

24 joint seeds per tier. **24/24 significant at every tier.** Adjacent tiers are
NOT distinguishable: within-tier range 0.094–0.113 vs tier steps of 0.016–0.020.

**The leak changes form at every tier**: verdict sentence (« Le GEIPAN classe ce
cas en D : Phénomène étrange à très étrange ») → verdict lexicon → conjugated
verb (`manquons` 163/1017 C vs **0/106** D) → cause noun → measurement density
(`mètres`, `secondes`, `environ` — which *is* the operational meaning of
"adequate information") → narrative length (0.6321 alone).

**42% ± 9% of the effect is identifiable leakage. The residual +0.1972 ± 0.0271
is reported as an UPPER BOUND, not as content** — not because the gradient has
not plateaued (that argument is WITHDRAWN; tier steps sit below seed noise) but
because the C/D criterion *is* informational adequacy, so no stripping rule can
remove from the text a property defined on the text.

**A+B-vs-D is withdrawn as circular by construction**: top discriminators are
the *names of the explanations* — `lanternes` 254/2271 vs **0/106**, `bolide`
87 vs 0, `iss` 72 vs 0, `vénus` 121 vs 1. A resolved narrative states its
cause; an unresolved one cannot. Unrepairable, not fixable.

This **explains rather than contradicts Blue Book T3**: T3's compiler-prose
effect of +0.2504 sits inside the GEIPAN leakage range.

### 1.5 PURSUE Release_07/08 OCR'd — 1.9 MB newly machine-readable

Neither Release_07 nor Release_08 has archive.org text derivatives, which put
the most loaded documents in the corpus out of reach. **All 40 now OCR'd**
(tesseract 5.3.4, 300 dpi grayscale, `--psm 1`), committed to
`data/raw/pursue_ocr/txt/`:

- **`DOW-UAP-D172-BAASS_Ten_Month_Report_July-2009` — 1,086,965 chars.** The
  major AAWSAP deliverable. **Not yet analysed.**
- `DOW-UAP-D182` FedBizOpps Combined Synopsis/Solicitation HHM40208R0211,
  18 Aug 2008 (20,114). **NOT the Statement of Work — the SOO is `D110`, and
  D110's copy is the readable one. Corrected in §1.16 item 2.**
- `DOW-UAP-D183` Correspondence from Senator Harry Reid, 24 June 2009
- `DOW-UAP-D184–D188` Reid engagement papers, SAP request review, DIA
  AATIP/AAWSAP memo, contract-deliverables review (21,024)
- `CIA-UAP-D024–D029`, all 1952: Approval in Principle; **Proposal to Consider
  Psychological Warfare Implications of UFO Related Issues** (25,683, memo to
  Director, Psychological Strategy Board, SECRET/Security Information,
  "Approved for Release 2026"); Summary Assessment of Flying Saucers; OSI
  Briefing; Assessment of National Security Issues; Official Diary Entry
- ~25 Air Intelligence Information Reports 1956–57 and Unresolved UAP Reports
  1949–66

### 1.6 Codename extraction — honest version

49 codenames, each with an attestation tier (OFFICIAL / CONTRACTOR / ALLEGED /
FABRICATED / GENERIC). **13 present, 36 absent and reported as zero.**
`data/processed/codenames/codename_index.json`.

Corrections made: **Condign is 1996–2000**, not 1950–53. **Teaball was a
Vietnam MiG-warning weapons-control centre**, not a UAP programme.
**"glimmer glass" has no primary document.** **"santa clause" was never
provided by the user and is not searched.** The ~800 `senior <noun>` entries
were fabricated and are not in the list.

Methodological correction: **AAWSAP appears in 43 filenames and 0 document
bodies** — the documents spell the programme out. Not a gap.

Real absences: **`moon dust` 0 docs**, `uaptf` 0, `aatip` 0 (acronym),
`kona blue` 0, `looking glass` 0, all `senior *` 0, `serpo`/`majestic` 0 —
while **`AARO` appears in 44**. Codename *discovery* found **nothing**; top
hits are OCR artefacts of `BOOSTER COMMAND`.

### 1.7 Redaction and gap audit

**Redaction is invisible in PURSUE text**: zero `[REDACTED]` markers, but **964
FOIA exemption citations across 48 documents** — (b)(1)=461 (classified
national defence), (b)(6)=401 (privacy), (b)(3)=81. Withholdings are applied to
the page image, so OCR returns nothing with no marker. **Detecting extent needs
JP2 page-image analysis, not text search** — `_jp2.zip` exists for all 298.

**Three of my first four gap findings were artefacts of my own ID parser** (a
trailing `\b` failing on `_`; CIA's mid-series convention change
`CIA-UAP-018`→`CIA-UAP-D020`; NASA's two parallel series `D1–D7` and
`D015–D032`; `DOW-UAP-PR` being sparse parallel numbering). Fixed in
`omega/scrubbed.py`. Surviving real gaps:

- **`DOW-UAP-D66`–`D73`** — eight consecutive, sitting inside a continuous
  block of 2020 Middle East mission reports (D60–D65 Persian Gulf / Strait of
  Hormuz / Iran; D74 Syria 2023, D75 Gulf of Aden 2024). **The single most
  specific, checkable gap in the release.** A gap is a gap, not a suppression —
  but it is nameable in a request.
- `NASA-UAP-D3`; `NASA-UAP-D23`–`D29`
- DOW-UAP-D: 32 missing of 211, density 0.848

**The archive holds 8 releases while its own description documents 6.**

### 1.8 NUFORC schema — corrected

Path (ephemeral scratchpad, see §3):
`.../scratchpad/uap/nuforc_dl/x/drastimehta-nuforc-ufo-event-sightings-csv/data/ufo_sightings.csv`

- **134,906 records**, not 137,094 (the higher figure is line count; quoted
  fields contain embedded newlines).
- Columns: `month_year_of_event, event_date_time, city, state_provinces, shape,
  duration, summary, posted`. **No latitude, no longitude, no country.**
- Country is parenthetical inside `city` (`Lachute (Canada)`) for 18,188 rows.
- **33,976 distinct `city|state` pairs.** Coverage curve: top 2,000 pairs = 53%
  of records, 4,000 = 65%, 8,000 = 77%.
- `corpus.Rec` has **no `state` and no `id`**. Fields are `uid, catalog,
  source, source_id, date_raw, year, month, day, prec, date_uncertain, lat,
  lon, location, country, desc, norm, refs, etype, attrs, credibility,
  duration, kv, summary, places`.

---

### 1.9 BAASS Ten Month Report — independent 2009 corroboration of the D-reclassification

`DOW-UAP-D172`, 30 July 2009, the AAWSAP deliverable to DIA under contract
`HHM402-08-C-0072`. 497 pp, 1,086,965 chars. Archive.org still has **no text
derivative for D172**, so our OCR remains the only machine-readable copy.

**The result.** p283 ¶50 states the then-current public GEIPAN breakdown as
BAASS's own translation-triage count: « D cases: 205 cases for 23 regions.
C cases: 323 cases for 23 regions. » p219 confirms GEIPAN's own definition of D.

| | BAASS mid-2009 | 2026 ≤2007 | 2026 **full 1937–2026** |
|---|---|---|---|
| C | 323 | 588 | 1,020 |
| **D** | **205** | **75** | **106** |

**The D count fell in absolute terms, 205 → 106, a deficit of 99 measured
against the whole 90-year archive.** §1.3's D-rate result (3.78×, p=9.4e-10) is
a *rate* and so admits a denominator objection; **an absolute decrease cannot be
produced by adding cases.** GEIPAN added 2,104 post-2007 cases, of which only 31
were D. Independent third party, 17 years earlier, counting for an unrelated
purpose.

**Unresolved and reported as such:** the report's "over 1,650 investigations
1977–2007" does not reconcile with 1,155 (window) / 1,300 (≤2007). A
case-vs-testimony unit mismatch was tested and rejected, but weakly — the field
holds a title string, not a list. The D result is window-free and does not
depend on it. BAASS itself documented press inflation of a release size in the
same section (Danish Air Force: press said 15,000 reports, actual release 329
pages).

**Two defects found in the document.** "Entity Events ≈3,988" (23.1% of the
17,281-record MUFON CMS) is contradicted by its own facing-page table: CE total
2,233, CE3–5 = 333. And the classification percentages are computed on 8,753
classified records (50.65% of the database) without disclosing the base, showing
CE as 25.5% where it is 12.9%.

**Northern Tier is NOT a usable independent nuclear-proximity test set.** p315
states the method: UFOCAT/NIDS catalogue events "within 300 miles of an NT
location", no control set, no base rate. That is failure mode #3 and the design
already falsified for ICBM proximity. Not re-run. Its quantities are inside
chart images anyway (OCR recovered only "MA1, 41", "CE5, 4").

**Project Oral History is non-evidence by construction** — sources "warned that
unauthorized disclosure… would be vigorously denied."

**Keyword trap logged:** "3418 cases" is a private collection in a house in
Fortaleza, Brazil (p423), **not** GEIPAN's 3,404.

**OCR validation.** The cross-derivation check against archive.org's new
Release_07 derivatives **cannot run** — the sets are exactly complementary, zero
overlap, because D165 and D172 are the two files its deriver still fails on.
Reported null. Two validations do hold: the 20-cell MUFON table sums to a total
reproducing two independently-printed percentages to within 0.07 pp, and the
load-bearing `205` is attested twice, 64 pages apart (p219, p283).

Full report: `omega/reports/baass_ten_month_report.md`

### 1.10 The undisclosed D cases are the re-examined ones

`omega/geipan_revisit_disclosure.py`. Crossing `Document pour cas` with
`Cas revisité` **inside class D** localises §1.3's marginal finding:

| | revisited | not revisited | total |
|---|---|---|---|
| dossier published | 8 | 42 | **50** |
| **no dossier published** | **55** | **1** | **56** |

Revisit-rate 0.9821 undisclosed vs 0.1600 disclosed, **z = +8.605**, RR 6.14×.
**Not an era artefact** — holds inside every decade 1970s–2010s, and the
**Mantel-Haenszel OR stratified by decade is 209.10.** Stratification
*strengthens* it, the opposite of failure mode #6.

Supplies the mechanism tying §1.3 to §1.9: GEIPAN reopened D cases,
reclassified ~99 out of D, and among those still in D the reopened ones are the
unpublished ones.

**DIRECTION OF CAUSATION UNDETERMINED.** "You reopen the case you cannot resolve
from the file you have" fits the data exactly as well as "reopening withdraws
the file". The metadata cannot separate them; separating them needs the
documents, which is what is missing. `Cas revisité` semantics are undocumented,
n=106, one cell holds a single case.

Also **explains the power ceiling on the witness-level C-vs-D test**: the 56
absent D dossiers are not missing at random.

56 IDs with date/department/region/coordinates:
`data/processed/geipan/cada_targets.json`. CADA letters drafted (asking for
occulted versions from the outset, conceding privacy in full):
`omega/reports/cada_request_draft.md`. **Drafted, not filed.**

### 1.11 Operational lessons that cost real time this session

- **`except Exception: return None` cost a whole session.** It turned a
  persistent HTTP 504 into a generic "FAILED" (§2.2).
- **A pipeline reporting "0 failures" is claiming its error detection works,
  not that the data is good.** Two provinces came back with ZERO rows and were
  counted as successes, because HTTP 200 with no bindings is not an error. Wrong
  Q-ids: BC was Q1974 (correct **Q1973**), PE was Q1979 (correct **Q1978**).
  BC alone holds 47,585 places. Consistent with §1.7, where three of four gap
  findings were artefacts of our own ID parser.
- **Tesseract spawns an OpenMP thread per core by default.** N worker processes
  therefore put N×cores threads on `cores` cores. Measured on one 2480×3507 page
  of the GEIPAN corpus: **31,647 ms/page at the default, 2,090 ms/page with
  `OMP_THREAD_LIMIT=1`, byte-identical output.** 15×, i.e. 8.3 h → ~35 min.
  **Always set `OMP_THREAD_LIMIT=1` and parallelise at the process level.**
- **Wikidata's `mul` label code.** Labels identical across languages live under
  `mul`, and `FILTER(LANG(?l)="en")` excludes them. San Antonio and Arizona
  carry their names **only** under `mul`. Tiny in count (+25 on Texas) but it is
  exactly the big city names. Use `FILTER(LANG(?l) IN ("en","mul"))`.
- **`wdt:P625` returns only truthy coordinate statements.** San Antonio has
  none; its coordinate exists only as a statement node, so
  `p:P625/psv:P625` is required. That construct was **never** the timeout cause.
- **Generalising a timing test from a small case was an error.**
  `gazetteer_settlements.py` was built on a Rhode Island box that returned in
  8.3 s; a province-sized box answers 504. Recorded negative, not in pipeline.

### 1.12 Session 3 — the evidence vault, and four results

**`evidence_vault/` (145 MB, NOT gitignored, binaries force-added).** `archive/`
was merged into it so there is ONE durable tree. `evidence_vault/VAULT_MANIFEST.md`
is the living index and states for every empty section *why* it is empty.

Size rule: **a vault that cannot be pushed is not durable.** The 37 DIRD PDFs
are 1,779.6 MB and are NOT stored — the texts are, plus
`01_PURSUE_PRIMARY/FETCH_MANIFEST.json` with URLs, sizes and upstream SHA-1s.
Durable corpora now inside: periodicals 860 texts (29.9 MB gz), PURSUE server
OCR 286 (7.0 MB gz), TEP dossier (14 MB), trace controls (69 MB), NUFORC
unified (11.6 MB gz).

#### Result A — the 37 DIRDs are open-literature surveys

`omega/dird_analysis.py` · `omega/reports/dird_corpus.md`

| | |
|---|---|
| DIRDs mentioning UAP/UFO **at all** | **1 of 37** |
| open-literature citation markers | **1,541** |
| closed/internal citation markers | **56** |
| **ratio** | **27.5 : 1** |

**"The government funded NHI-level technology research" deflates to "a
threat-assessment office paid contractors to survey the open journals."** The
DIRDs are programme-scope evidence, not capability evidence. Authors are
anonymised `AAP Person N`, 31 distinct IDs in a block (1, 57, 58, 63–90).

**The exception, D128** *Anomalous Acute and Subacute Field Effects on Human
Biological Tissues* — 14 UAP refs, **14 closed citations (highest of any
DIRD)**, Appendix A is the **Schuessler Catalog of UFO-Related Human
Physiological Effects**. It concludes, verbatim, that injury patterns are
« congruent with the anomalous vehicle reports » and attributable to
**"real-world (although current and likely advanced beyond public information)
technologies"** — terrestrial RF/microwave energy deposition. A prosaic
conclusion reached inside the programme on its own data.

Its one exotic alternative is falsifiable: a craft's blackbody spectrum
**gravitationally blue-shifted** under spacetime manipulation → exposure up to
**soft X-rays**, i.e. an **ionising** signature.

**The structural gap, which is itself a finding.** TEP is the only
physical-trace case with full lab chemistry, and INRA **rejected** an ionising
mechanism there — but the TEP telex records `AUCUN EFFET RESSENTI PAR LE
TEMOIN`, no effect felt. **The project's two best evidence bases do not
overlap**: the case with trace chemistry had no human exposure; the document
with a human-exposure model has no trace chemistry. Re-analysis of either cannot
close it.

**Two new FOIA targets named in primary text:** `Technical Study 10.0 Human
Effects` (cited in D128, absent from the release, the only internal Technical
Study referenced in all 37); the AAWSAP-held Schuessler Catalog.

#### Result B — echo chamber re-grounded in primary publication

`omega/periodical_provenance.py` · `evidence_vault/07_PERIODICALS_PRIMARY/`

**860 issues, 72,057,926 chars, zero fetch failures.** MUFON/Skylook 485
(1967–2008), APRO Bulletin 260 (from Vol 1 No 1, 1952), CUFOS IUR 115. This
**lifts Phase 1's biggest stated limitation.**

Strict test (place + year + month within ±320 chars): **CONTROLS 4/4,
TARGETS 0/4.** Socorro 52 corroborated, Kecksburg 41, TEP 5, Exeter 4 —
Wright-Patterson 1951, Dallas 1965, Galesburg 1967 all **zero**. The three
apparent "Texas" hits were read individually and are all coincidence.

Relaxed test (year only, 400 chars): controls beat targets **10× to 127×**.
Weakest control is a *French* case in *US* bulletins (10 hits); strongest target
is Wright-Patterson, named 291 times across 147 issues, year-proximity ≈ 0.

**The corroboration is circular — six catalogues citing each other with nothing
underneath.** And "a small town in Texas" is **untestable by construction**: a
state plus an indefinite article is not a locus.

*Not nonexistence:* NICAP's *UFO Investigator*, *Flying Saucer Review*, CUFOS
case files and local newspapers are absent from the corpus.

#### Result C — redaction extent measured; §1.7 corrected

`omega/redaction_inline.py` · `omega/jp2_redaction.py` ·
`evidence_vault/05_SCRUBBED_CONTENT/README.md`

**§1.7 was incomplete.** It searched for the literal token `[REDACTED]` (6
occurrences in 326 docs) and concluded redaction is invisible in text. The
release **substitutes the exemption code in place of the withheld span**:
`AT 0823Z, (b)(1)1.4a TOOK OFF FROM OJMS VIA SLR`.

| mechanism | measurable from | count |
|---|---|---|
| inline exemption substitution | **text** | **982** across 55 of 326 docs |
| solid black bars in page image | JP2 only | **148** over 112 pages |

`DOW-UAP-D3` Arabian Gulf 2020 uses **both** — 104 inline at 17.10/1,000 chars
across all 10 deciles, plus 66 bars over 5.87% of page area.

**The stated reason is the finding.** E.O. 13526 §1.4: **1.4(a) military
plans/weapons/operations = 224**; 1.4(g) = 19; **1.4(c) intelligence
sources/methods = 1**. The withholdings are military operational detail, not
intelligence tradecraft.

White-out redaction was **tested and ruled out**. Numbering gaps, agency union:
**CIA-UAP 29/29, zero gaps** (the earlier CIA gaps were the `018`→`D020`
convention change); DOW-UAP 174, 37 missing, **D66–D73 reproduced**; NASA is
**two parallel series** (D1–D7 missing D3; D15–D32 missing D23–D29) and the 8–14
span is a boundary, not a gap. **D60/D63/D65 flanking the D66–D73 gap are
image-only**, and measure 0.48–0.97% dark with **zero bars** — clean scans.

#### Result D — Track 2 control set, and 4 of 10 sites cannot be controlled

`omega/track2_controls.py` · `evidence_vault/08_SATELLITE_ANOMALIES/README.md`

Control set built, **detection deliberately NOT run** — §5 item 5 makes the
order a design constraint and §6 records five claims falsified by absent
controls.

**TESTABLE:** Réunion 1.00, Rendlesham 0.73, Socorro 0.62, Trans-en-Provence
0.57, Saint-Mathias 0.50, Valensole 0.50.
**NOT CONTROLLABLE:** Cherry Creek 0.24, Cash-Landrum 0.20, Lavonia 0.13,
Newark Valley 0.12.

**Controllability is inversely proportional to local sighting density.** Newark
Valley has 658 sightings within 100 km and yields 2 clean controls from 17.
**This is the mechanism behind §6's falsified proximity claims, made
measurable:** in the US sighting field a candidate's neighbourhood already has
reports, so there is no comparison ground.

**TRACK 2 ON HISTORICAL SITES IS TEMPORALLY IMPOSSIBLE.** Sentinel-2 launched
June 2015; the candidates are 1964–1981 events — a **34–51 year gap**. TEP's
trace was visible at 40 days. Repoint Track 2 at the **34,898 geocoded
Sentinel-2-era NUFORC records**.

#### Result E — Tracks A–D: the "impossible" claims return clean nulls

`omega/deep_terms.py` · `evidence_vault/10_HIDDEN_BURIED/deep_terms.json`.
617 documents, context + frame recorded per hit (QUOTED_FICTION / HYPOTHETICAL /
THIRD_PARTY / PHYSICS_TERM / DIRECT).

**ZERO occurrences:** non-human personnel/employee/staff/officer/official ·
human-looking · indistinguishable from human · breakaway civilisation · shadow
government · organic robot · pseudo-human · security-clearance+non-human ·
**non-human biologic** · **crash retrieval** · simulation hypothesis · majestic ·
serpo · **glimmer glass** · kona blue · looking glass · **teaball** · **moon
dust** · immaculate constellation.

`MJ-12`: one hit, a citizen's letter *asking* a congressman about it.
What IS present is DIRD physics vocabulary (metamaterial 419, antigravity 236,
traversable wormhole 185) — a literature survey — plus Utah Ranch 64,
Skinwalker 40, Socorro 68, Cash-Landrum 15.

#### Codename index corrected

29 present of 58, over 559 docs. Two traps removed by reading **every**
occurrence: `aurora` 28→**3** (the rest are aurora borealis, a satellite
"AURORA II", NASA's Fast Auroral Snapshot Explorer, Gemini astronauts
describing auroras; the 3 survivors are all hedged — "alleged", "rumored",
"supposed"); `stargate` 27→**0** (the DIA wormhole paper, a URL, and a GEIPAN
witness naming a TV series). Three mechanisms: REQUIRE whitelist, VETO
blacklist, **DOC_VETO** at document scope. `project pounce` re-tiered
ALLEGED→OFFICIAL.

### 1.13 Operational lessons from session 3

- **`except Exception: return None` cost a session** (§2.2). A generic reason
  hides a persistent 504.
- **"0 failures" is a claim about error detection, not data.** Two provinces
  returned zero rows and counted as successes.
- **`\b` fails on `_`.** §1.7 documented this and it was **reproduced anyway** —
  zero hits for 37 DIRDs that are plainly there. Use `(?![0-9])`.
- **Zero-padding is a series marker; magnitude is not.**
- **Overlapping ranges = convention change (merge). Disjoint = parallel series
  (do not).**
- **`OMP_THREAD_LIMIT=1`** for tesseract: 31,647 ms/page → 2,090 ms/page,
  byte-identical. Always.
- **Memoise `toks()`** — permutation nulls re-tokenised unchanged text ~63,000
  times. 12,412× warm.
- **Significance ≠ power.** MDD here is 2.485σ (80% power); significance is
  1.645σ. An effect between them is *significant but underpowered*, not null.
- **Matched tiers vary ±0.1 across matcher seeds.** A single draw is not a point
  estimate.
- **A control screen whose coverage tracks the geography being screened is not a
  screen** (NUFORC alone passed French sites by absence of coverage).
- **Never pipe a background job through `head`** — SIGPIPE kills it.
- **A file can be tracked AND gitignored.** `git add` then silently refuses
  without `-f`, and the committed copy goes stale.

### 1.14 Session 4 — the debt paid, and two audits

**Environment first: the setup script WORKS. This was the open question.**
`UFOAI Omega research` (`env_018sxdcbBHMGqCRwh6KXDi6D`) was `is_current: true`,
and tesseract 5.3.4 + `fra` + poppler 24.02 + scipy 1.18.1 + sklearn 1.9.1 were
all present. Attributed, not assumed: scipy's `dist-info` was created 05:23
against a container boot of 05:21, so pip ran two minutes after boot. `fra` is
installed (its `traineddata` mtime is the upstream package's 2019 date, which is
not evidence either way — the dist-info timestamp is). `archive.org` and
`www.geipan.fr` both answer 200. **Start future sessions on this environment and
stop re-verifying the toolchain.**

#### 1. §1.4 seed-averaging — PAID
`omega/geipan_tier_seed_stability.py`, `omega/reports/geipan_tier_seed_stability.md`,
`evidence_vault/09_SEED_STABILITY/`.

The debt was **larger than §5 stated**. §5 named one seed (the length matcher,
`seed=5`). There are two: `balanced_cv_acc(seed=11)` downsamples the 1,020-case
C arm to 106, so **all six tiers** rested on a single draw, not just the two
matched ones. Both were swept, 24 seeds each; because the published value is a
low draw on both axes, L4/L5 also got a **joint** sweep varying both together —
neither marginal mean is the estimate.

| tier | was | **now** |
|---|---|---|
| L0 | +0.3494 | **+0.3387 ± 0.0229** |
| L1 | +0.3019 | **+0.2771 ± 0.0300** |
| L2 | +0.3113 | **+0.2628 ± 0.0318** |
| L3 | +0.2643 | **+0.2333 ± 0.0308** |
| L4 | +0.2176 | **+0.2135 ± 0.0276** (42nd pctile — that draw was fine) |
| L5 | **+0.1795** | **+0.1972 ± 0.0271** (38th pctile — a low draw) |

- **The residual ROSE.** The upper bound was understated, not inflated.
- **"51% is identifiable leakage" → 42% ± 9%.**
- **The L1 > L2 inversion was noise.** Seed-averaged the ladder is monotone;
  there was never anything to explain.
- **Adjacent tiers are NOT distinguishable.** Within-tier range 0.094–0.113;
  tier steps 0.016–0.020. Only the endpoints separate.
- **"The gradient has not plateaued" is WITHDRAWN** as the reason the residual
  is an upper bound. The real reason is stronger: the C/D criterion *is*
  informational adequacy, so no stripping rule can remove from the text a
  property defined on the text.
- **24/24 seeds significant at every tier.** Existence was never seed-dependent.

§5's inventory of affected documents was itself wrong — it named the BAASS,
Trans-en-Provence and DIRD reports, **none of which cite the number.** The real
list (tree-wide search for `0.1795|0.2176|0.6795|0.7176`) is `HANDOFF.md`,
`HANDOVER_PROMPT.md`, `geipan_acquisition_and_disposition.md`,
`geipan_cd_witness.md`, `geipan_cd_witness.py`. All corrected.

#### 2. Redaction slot analysis — what is withheld, not how much
`omega/redaction_slots.py`, `omega/reports/redaction_slots.md`,
`evidence_vault/05_SCRUBBED_CONTENT/redaction_slots.json`.

**The route in was structure, not grammar.** §5 proposed inferring the withheld
token's class from surrounding syntax. Unnecessary: the DOW mission reports are
**MISREP forms**, so a redaction sits in a **named field that states what was
removed**. 167 labels recur across ≥3 of 33 parsed forms.

| slot | withheld | released | rate |
|---|---|---|---|
| **CALLSIGN** | 98 | 10 | **0.91** |
| PERSONNEL | 131 | 78 | 0.63 |
| NARRATIVE | 79 | 115 | 0.41 |
| GEO | 40 | 105 | 0.28 |
| OPERATION | 42 | 119 | 0.26 |
| UNIT_ORG | 48 | 370 | 0.11 |
| TIME | 29 | 288 | 0.09 |

Never once released: Email 52, Full Name 33, Aircraft Callsign 33, Callsign 32,
Phone 28, Asset Type (Aircraft) 8, Number of Aircraft 4.
Released essentially always: Country Tasked 0/24, Activity Description 0/22,
Service 2/70, Rank 4/62, Wing 7/52, Takeoff Time 1/21, MAJCOM 1/20.

**The release gives which country, service, wing, rank, mission type and times,
and never which aircraft, under what callsign, how many, or who by name.** That
is ordinary OPSEC on force composition, **not concealment of phenomenon data** —
`Gentext`, which carries the UAP description, is released 115 times against 37
withheld. **Reported as a negative: it cuts against a suppression reading.**

Validated against the releasing authority's own exemption code (an independent
label): **443/575 = 77.0% agreement.** That is a FLOOR — 83% of the largest
disagreement class ((b)(6) on unit fields) is OCR field-absorption, a lost
bullet separator making a unit field swallow the next personnel field.

#### 3. AAWSAP contract audit — the capstone deliverable is absent
`omega/aawsap_contract_audit.py`, `omega/reports/aawsap_contract_audit.md`,
`evidence_vault/01_PURSUE_PRIMARY/aawsap_contract_audit.json`.

**All 26 FY2009 deliverables are present.** D188 records 26 delivered; D117–D142
is exactly 26. Title matching cannot prove it (DIA retitled on publication) and a
square assignment matches everything by construction. The proof is that **the
release pseudonymised authors consistently across documents** — D188's Enclosure
1 gives `MP Person NN` per title, each DIRD names `AAP Person NN`, one namespace,
assigned by the government. **Author ID agrees 26/26, zero disagreements**, and
resolves the three pairs titles could not (D121=64, D132=57, D119=65).

**THE CAPSTONE IS MISSING.** (§11(d) is cited from **D110**, the SOO, not D182 —
see §1.16 item 2. The SOO calls it *Integrated* Threat Assessment; only the CLIN
tables add *Comprehensive*.) The Comprehensive Integrated Threat
Assessment has its own CLIN and money in both years — **0004 at $240,000, 1004
at $220,200, $460,200 contracted.** A corpus-wide search returns 4 hits, *all in
the contract documents themselves*. No report, no briefing, and D188's review of
deliverables to the DIRECTOR, DIA never mentions it. **Its due condition was
reached**: D116/P00005 extends the contract under FAR 52.217-8 to **21 Dec
2010**, and D150–D153 were published either side of that date. Most specific
checkable gap since D66–D73, and nameable by CLIN.

Also established:
- **The contract ran two of five anticipated years.** The SOO planned base + four
  option years to 30 Sep 2013. Actual: base, option year 1, then a three-month
  FAR 52.217-8 service extension to 21 Dec 2010. Options 2–4 never exercised.
- **What was released is DIA's published version, not the contractor's.** Each
  DIRD carries a DIA control number and `ICOD: 1 December 2009`; D188 predates
  the earliest by six weeks. The as-delivered BAASS research reports, and the
  §11(c) executive summaries, are unreleased.
- **The 60-day overview papers cost more than the reports they preview.** CLIN
  1002 ($4.76M) is 1.66× CLIN 1003 ($2.87M) and the contract's largest item.
  The only deliverable stating a threat judgement is 2.7% of the base year.
- Year one was **unclassified only**; 5 of 26 reports had outside review,
  including **three Sandia National Laboratories** staff; all reviews positive.
  FY2010 intent included "classified experimental verification by BAASS".

### 1.15 Operational lessons from session 4

1. **A background job's "completed, exit 0" was wrong three times.** With
   `nohup … &`, the harness notification fires when the *wrapper* exits, not the
   work. Each time, the python process was still running at 100% CPU and the
   result file was a stale copy from an earlier smoke test. **Verify with
   `ps -eo pid,etime,cmd` and the output file's mtime before reading a result.**
   To block properly: `until [ ! -d /proc/<pid> ]; do sleep 5; done`.
2. **Check the instrument before believing a negative.** An affiliation
   cross-check returned 0/8 "unconfirmed", which looked like a failed
   reconciliation. The DIRDs carry **no institution line at all** — the metric
   was impossible, not failing. Replacing it with the author-pseudonym check
   gave 26/26.
3. **An OCR-legibility proxy ranked clean text as damaged.** Scoring by share of
   all-alphabetic tokens penalised `0823Z`, `SECRET//REL` and `432 AEW` —
   correct military format. It called the modern mission reports worse than
   degraded 1950s FBI scans.
4. **A non-hit in garbage is not evidence of disclosure.** The first marker
   regex matched only clean `(b)(n)`, so `(b}(6)`, `(bl(6}` and bare `! 1.4a`
   were scored as RELEASED — fabricating "categorically protected fields: 0".
   Habit #2's complement: an explicit **UNREADABLE** class is required.
5. **A greedy best-match is not an assignment.** It gave D135 to two different
   titles and D123 to two more, inflating the match count while the true
   counterparts went unclaimed. Use `scipy.optimize.linear_sum_assignment`, and
   remember a square assignment matches everything by construction — the count
   is then structural and proves nothing without an independent identifier.
6. **Two FOIA targets were withdrawn before they stood.** "No PMP and no monthly
   status reports were released" was false: D168 is a consolidated PMP and
   D169/D170/D171/D173 are monthly reports. Check filenames before asserting a
   gap.
7. **`data/processed/` is gitignored (`.gitignore:6`).** Session 2's lesson
   recurred live — the seed-stability JSON would have been lost. It is in
   `evidence_vault/09_SEED_STABILITY/`.

---

### 1.16 Session 5 — three parallel threads, and what they withdraw

**Session 5 ran as three sessions at once, off the same tip, not knowing about
each other.** All three pushed. Nothing was lost and nothing conflicted, but for
about an hour the project had no single authoritative state file and this handoff
did not know any of it. §2 records how that was resolved and what to do instead.

Precedence: **where §1.16 disagrees with §1.1–§1.15, §1.16 wins.**

#### 1. Per-area assignment of the 37 DIRDs — §5 item 1 CLOSED, and it withdraws a claim
`omega/dird_area_assignment.py` · `omega/reports/dird_area_assignment.md` ·
`evidence_vault/01_PURSUE_PRIMARY/dird_area_assignment.json`

Area list read from the **SOO itself, D110 §3(a)** (readable), not from D188's
restatement. Primary area read from each report's own statement of purpose, not
its title — D124 is titled *Space Access* but its text says "The remainder of
this report will focus on the characteristics of this class of lifting body",
so it is a configuration report. **Every assignment carries the framing sentence
it rests on and the script verifies that sentence is present in the vaulted
text; 37/37 verified, a missing string exits non-zero.**

- **Session 4's keyword map was inflated 1.41×** — 52 area slots for 37 reports.
- **One area per report is not cleanly possible for 20 of the 37.** Their own
  framing supports two. Counts are reported as a primary value plus the range
  reachable when contested reports flip.
- **Nine of twelve areas are covered under every reading**: propulsion, power
  generation, spatial/temporal translation, materials, signature reduction,
  human interface, human effects, armament, other peripheral.
- **Lift, control and configuration/structure each rest on ONE contested
  report.** Flip it and the area has none.
- **In FY2009, control has no report at all** under the primary reading; the
  only control report is D151, FY2010.
- **Propulsion dominates at 11/37 under the primary reading** (P=0.0019 Monte
  Carlo against the contract's uniform one-per-area design, look-elsewhere
  included; overall χ²=32.1, P=0.0012) — **but if every contested propulsion
  report flips away it falls to 4, indistinguishable from uniform (P=0.37).**
  Real under one reading, not robust across readings. Do not quote without that.
- Agreement with a mechanical keyword rater: 0.568 exact, **Cohen's κ=0.517**
  (CI 0.343–0.687), 0.703 if the rater may hit primary *or* alternate. 7 of 11
  hard disagreements are the rater calling a report *power generation* off
  `power|energy` in body text about what a propulsion system needs — the same
  failure that inflated session 4's map. **κ≈0.5 says the reading cannot be
  reproduced by keyword counting. It does not validate the reading.**

**WITHDRAWN:** §1.14 item 3's "no contracted area went undelivered" is no longer
a firm claim. It is true under the primary reading and false under an equally
defensible one. The per-area counts in `aawsap_contract_audit.json` remain
unquotable; use `dird_area_assignment.md`'s table with its ranges.

**Red-team caveat carried forward:** one reader chose every primary. κ against a
keyword rule is not inter-rater reliability. A second blind reader on the 20
contested reports is the real test, and is expected to land well below κ=1.

#### 2. FOIA Letter 14, and seven corrections to the contract audit
`omega/reports/foia_request_drafts.md` (Letter 14) ·
`omega/reports/aawsap_contract_audit.md` (session-5 addendum)

Found by re-grepping every citation before drafting. Each checked against the
release text, not against the report.

**Corrections that supersede §1.5 and §1.14 item 3:**

1. **D182 is NOT the Statement of Work/Objectives.** D182 is the FedBizOpps
   **Combined Synopsis/Solicitation HHM40208R0211**, posted 18 Aug 2008. The SOO
   is **D110**, `STATEMENT OF OBJECTIVES … 18 July 2008`. Both carry the same §11
   text; **D110 is the readable copy.** §1.5's label for D182 is wrong.
   The SOO calls the deliverable *Integrated Threat Assessment*; only the CLIN
   tables add *Comprehensive*.
2. **"4 hits, all in the contract documents" undercounted.** Fuzzy search finds
   it in **D110, D111, D112, D113, D116 and D175** — D110 and D116 were missed
   because their OCR reads `Asscsmient` and `ln!$graled`. The first five are
   contract documents, so **the finding stands**: no report, no briefing.
3. **Two due conditions were reached, not one.** CLIN 0004 has its own base-year
   period of performance `09/22/2008 to 09/21/2009` (D111), extended to
   **30 Sep 2009** by P00001 (D112) — a month *before* D188 (30 Oct 2009)
   reviewed the FY2009 deliverables without mentioning it. The option-year
   condition (21 Dec 2010, P00005) is the second. §1.14 framed only the second.

**New findings:**

4. **The twelfth area is "technology integration".** D186 (Director DIA INFO
   MEMO U-10-2552/CE to USD(AT&L), Dec 2010) p.1 names twelve areas ending in
   `technology integration`; the SOO's own wording is `other peripheral area,:;
   in support of(1-11)`. DIA relabelled it between 2008 and 2010, and the one
   area D188 omits is the twelfth. *Whether the Integrated Threat Assessment was
   meant to serve it is inference, not finding.*
5. **DIA says twelve FY2010 reports were delivered; the release holds eleven.**
   D186 p.1: `Twelve additional reports were produced and delivered.` The FY2010
   DIRDs are D143–D153 = 11. D186's Enclosure 1 is not in the released copy.
   **One FY2010 report is unaccounted for.** OCR reading — confirm on the page
   image before quoting.
6. **BAASS described a threat assessment as FUTURE WORK four weeks before the
   contract end date.** D175, *Summary Report on BAASS UAP Analysis
   Capabilities*, 23 Nov 2010, p.98: `it is also BAASS's mission to produce a
   Threat Assessment of UAP and USO performance and capabilities. As a first
   step…`. The only non-contract mention in the release. **This fits "never
   produced" at least as well as "produced and withheld"** — and it names a
   different object (UAP/USO performance) from the SOO's foreign threat from
   advanced aerospace platforms. Reported as cutting against suppression.
7. **P00002's attachment on deliverable impacts is missing.** D113 (eff. 2 Feb
   2010): `b) Identify Impacts to deliverables as a result ofreduced funding for
   Option Year 1, (see attachment)`. The released copy ends at p.3 and holds no
   attachment. **If CLIN 1004 was descoped, that attachment is where it would be
   recorded.** P00002's $11,948,810 reconciles exactly with CLINs 1001–1009.
8. D185 (Nov 2009) p.1: in FY2010 `four to six of the original technical reports
   will be expanded to included classified data … derivatively classified at the
   secret level`. A classified assessment is live, so **Letter 14 asks for
   classification review rather than assuming release.**

Letter 14 names CLIN 0004 and CLIN 1004 under contract HHM402-08-C-0072.
**Drafted, not filed.** §5 item 2 is therefore partly closed; four targets remain.

#### 3. NT-16 replicated end to end — the biochemistry holds, the inferences don't
`omega/tep_nt16_replication.py` · `omega/geipan_trace_null.py` ·
`omega/reports/nt16_writeup_and_replication.md` ·
`evidence_vault/02_GEPAN_PHYSICAL_TRACES/.../tep_dossier_pageocr_2026-11-26.tar.gz`

Every number used was **read from the page image, not from OCR**. Anything not
read directly off a page is marked `[INFERRED]` in the report.

- **The biochemistry reproduces.** 9 of 11 of NT-16's correlations recovered to
  ±0.01 from its own tables. One NT-16 table cell is a transcription error
  (E-1 chlorophyll B printed `0,930`; INRA's handwritten original reads `0,030`)
  — **INRA computed from the correct value.**
- **The distance gradient survives every null the data allow.** 13 of 16 pigment
  and cofactor variables at |r| ≥ 0.811 against distance; under joint relabelling
  of the six distances the expected count is 1.7, **P = 0.0028** — which is the
  smallest P this design can produce (2/720). Survives dropping the centre
  sample and controlling for leaf size.
- **NT-16's reported significance is overstated.** Its P-values are one-sided
  parametric and NT-16 does not say so. **One is 50× too small**
  (ln PhA′/ΣChlA, N=5: reported 0.28×10⁻³, true one-sided 0.0145). With six
  plants on one transect **no honest P can be below 0.0028.**
- **The headline magnitudes carry ±50% analytical error and no biological
  replicate.** Of the series-1 losses, only **β-carotene (−57% young, −50% aged)
  and violaxanthine in young leaves (−80%)** clear analytical noise (CV 0.22).
  **The chlorophyll losses (−27 to −33%) do not.**
- **§1.2's anti-ionising argument needs splitting.** INRA's γ-benchmark (10⁶ rads
  on *Arabidopsis* for equal-or-lesser damage) is INRA's own text and **stands**.
  But the *pattern* argument — carotenoid-over-chlorophyll excess — is **weaker
  than this project previously stated**: in series 1 its 95% analytical interval
  includes no excess, and in series 2 it holds from 1.5 m outward but
  **reverses at the centre**. Quote the benchmark, not the pattern.
- **The soil mass spectrometry cannot support the zinc/phosphate "rubbed paint"
  reading.** The lab's two plates of the same soil **disagree by a median factor
  of 23**, and 23 of 24 elements fall outside the lab's own factor-3 tolerance.
  Phosphorus is the only element enriched on both plates, and **one such element
  is what chance gives** (null mean 1.16, P = 0.77). Zinc cannot be tested on the
  second plate. §1.2's mechanical-sufficiency reading of the spark-mass-spec
  quote rests on the lab's prose, not on a reproducible measurement.
- **Database level: finding a trace does not predict class D. LOOKING for one
  does.** Cases where a ground search found a trace and cases where a search
  found nothing have the same D-rate (OR 1.0–1.1, P=0.89). Searching vs not
  mentioning a search: era-adjusted **OR 2.7, P=0.015**. That is what "adequate
  information" means operationally. **It is not evidence that traces mark
  unexplained events.**
- **Eight corrections to this project's own earlier records**, the worst being
  the telex mark width: this project wrote **14 cm**; the PV reads
  `LARGEUER : 10 CM`. That error had manufactured a discrepancy with the
  gendarmerie sketch (0.10 m) **that does not exist.** Also: telex time 17H00
  not 17H08 (slashed zero misread); circular number 32.600 not 9.600; dossier
  is 10 files / 177 pages, not 11 / 172; pheophytin −31% aged but **−40% young**.

**What the data establish:** something produced a real, monotone biochemical
gradient along one six-plant transect, starting at that spot. **What they cannot
establish is the cause** — one transect in one direction, no comparison transect
from elsewhere on the platform, a control series collected 14 days later on the
opposite side, and 40 days of foot traffic before the main series.

#### 4. GEIPAN Phases 1–3 re-run on the state file — an independent replication
`omega/geipan_phase123.py` · `omega/geipan_to_ufo_data.py` ·
`omega/reports/geipan_phase123.md` ·
`evidence_vault/11_GEIPAN_PHASE123/geipan_phase123.json`

Seeded RNG (20261126), 10,000 permutations, ~50 s. One export record has an
impossible date (`2000-09-01556`, 31/09/2000) — treated as month precision, not
corrected. `geipan_to_ufo_data.py` writes the catalog-schema file;
**GEIPAN is deliberately NOT registered in `CATALOG_META`, so it is never matched
against itself.**

**Phase 1a — internal collapse ≈1.00×, and that is true by construction.**
Same-day ≤30 km: 3,379 events, 1.007×, 0/106 D in a multi-case cluster. GEIPAN
files multiple witnesses under one case (`T1`/`T2` témoignages), so near-zero
collapse **says how GEIPAN counts, not that the reports are independent.**

**Phase 1b — the state file and the enthusiast literature barely overlap, and the
literature over-samples the unexplained.** Hand audit of 25 random links: 23
correct, **precision 92%** (Wilson CI 75–98%); recall unmeasured.

| | value |
|---|---|
| GEIPAN cases 1950–99 found in the literature | **113 / 1,053 (10.7%)** |
| French literature records 1950–99 found in GEIPAN | **175 / 8,197 (2.1%)** |
| GEIPAN cases after 2000 found in the literature | 0 / 2,252 |

In-literature rate by class: A 1.8%, B 1.8%, C 5.5%, **D 19.2%**. Crude OR 12.9
is **era-confounded**; **decade-stratified Mantel-Haenszel OR = 4.0 (2.1–7.6),
p = 1.8e-5.** C+D vs A+B: MH OR 1.6 (1.06–2.43), p=0.031.
**Within the same decade a case the state could not explain is ~4× more likely to
appear in a catalogue, and 98% of the literature's French events have no GEIPAN
counterpart at all.** Any "French UAP pattern" computed from the literature runs
on a population the state file barely touches. Reverse causation is live: some
cases are D *because* they were famous and heavily investigated.

**Phase 2 — nuclear proximity NULL on an independent state dataset.** Identified
cases (A+B) are the spatial null: same observers, same reporting system, same
geography, so population/media/observer density are matched by construction.
Labels permuted within region × decade; MH stratified on the same strata;
Bonferroni α=0.005 across 10 tests. **Twelve of twelve statistics null, smallest
one-sided p = 0.09.** Nearest-site median distance A 67.8 / B 66.5 / C 69.0 /
**D 66.3 km**; D vs AB Mann-Whitney p=0.59, rank-biserial −0.01. Commissioning
null: observed 567 vs expected 574.4, ratio 0.99, z=−1.26, p=0.21; no site shows
a post-commissioning surge. Framing contamination check: 44 cases mention a
power plant/reactor/CEA/EDF — A 17, B 16, C 11, **D 0**.
**This replicates the decontaminated Phase 2 result on an independent source.**

> **DEBT — DO NOT QUOTE PHASE 2 YET.** The 28-site layer (19 EDF plants plus
> Brennilis, Creys-Malville, La Hague, Marcoule, Cadarache, Valduc, Saclay,
> Île Longue, Plateau d'Albion) was **entered by hand from general knowledge**
> because Wikidata and ASN are unreachable from this container. Expect ±1–3 km
> and ±1 yr. Only 4 sites could be cross-checked. **Re-run against Wikidata, ASN
> or IAEA PRIS coordinates before this result is quoted anywhere.** This is the
> session-5 analogue of §1.4's seed debt, and it is §5 item 1 now.

Power is the honest limit: at 30 km the D contrast detects only OR ≥ 1.8 (C+D:
OR ≥ 1.27). **"Null" here means no large effect, not no effect.** And GEIPAN
coordinates are the *witness's* commune centroid, not the phenomenon's, which
blurs every radius below ~20 km toward the null.

**Phase 3 — descriptor drift replicated, and it survives inside the unexplained
subset.** Logistic regression of descriptor presence on decade, controlling log
text length, BH-FDR, run on the **witness portion** of each case text (available
on 64% of cases).

| descriptor | OR/decade, all | q | OR/decade, C+D only | 1937–79 → 2010–26 |
|---|---|---|---|---|
| photo/video | **2.58** | 3e-93 | **1.94** | 3.3% → 44.5% |
| triangle | 1.15 | 0.002 | **1.33** | 3.1% → 8.4% |
| disque/soucoupe | **0.77** | 4e-6 | 0.75 | 6.4% → 2.5% |
| landing/ground trace | **0.68** | 4e-10 | 0.70 | 6.9% → 1.1% |
| cigare/cylindre | 0.81 | 7e-5 | 0.76 | 5.5% → 2.8% |

**Discs fall, triangles rise, landings collapse ~6×, cameras surge >10× — and
the disc-to-triangle shift holds inside the unexplained subset**, so it is not
lanterns and satellites dominating the identified cases. **A fixed physical
population of craft does not predict that.**

**Third independent confirmation of the §1.3 D-collapse.** D share 6.4%
(1937–79) → 6.1% (1980–99) → 1.8% (2000–09) → **1.5% (2010–26)**:
**OR 0.69 per decade (0.62–0.77), p = 8e-12.** C share 55.6% → 17.0%. Chinese
lanterns lead 2010–2026 at 366 cases. §1.3 (rate), §1.9 (BAASS absolute count),
and now this (per-decade logistic) agree.

**D morphology, and why it is partly circular.** D vs A+B, decade-stratified MH:
triangle **OR 4.9 (2.7–9.0)**, stationary 2.7, silent 2.2, cigar 3.0, sphere
0.48. **GEIPAN assigns D when a description fits no known stimulus, so "D cases
are stationary silent triangles" is partly the definition of D speaking.** Not a
discovery about the phenomenon.

Also untested and named as such: military airbases, nuclear-weapons transport
routes, plants under construction, overseas sites (Moruroa/Fangataufa — GEIPAN's
Polynesia coverage is too thin).

### 1.17 Operational lessons from session 5

1. **Three sessions off one tip is the costliest mistake available.** Nothing
   conflicted only because the three threads touched disjoint files, which was
   luck, not design. Two of the three produced results that **modify** session 4's
   conclusions, and neither updated this file — so for an hour the handoff was
   confidently stating a withdrawn claim. **Before starting work, check
   `git ls-remote --heads origin` for sibling `claude/*` branches newer than this
   file's recorded tip.** §2 has the merge procedure.
2. **A label on a document is not the document.** "D182 = Statement of Work" was
   carried for two sessions and used to cite §11(d). D182 is the solicitation;
   D110 is the SOO, and D110's copy is the readable one. The citation survived
   only because both carry the same §11 text — that was luck too.
3. **A clean regex on dirty OCR undercounts and reads as a finding.** The
   capstone search returned "4 hits" because `Asscsmient` and `ln!$graled` are
   what the page actually says. Session 4's lesson #4 again, from the other side:
   an exact-match miss in garbage is not an absence.
4. **Read the framing sentence, not the title — and store the sentence.** The
   DIRD assignment verifies all 37 framing strings against the vaulted text and
   exits non-zero on a miss. That turns a judgement call into something a later
   session can audit without re-reading 37 PDFs.
5. **κ against your own keyword rule is not inter-rater reliability.** It
   measures whether a cheap rater reproduces you, which is worth knowing and is
   not validation. Say which one you have.
6. **Report bounds, not invented probabilities.** 20 of 37 reports are
   genuinely two-area. The flip ranges are extreme bounds and are labelled as
   such, rather than a made-up per-flip probability.
7. **Hand-entered reference data is a debt the moment it is used.** The Phase 2
   site layer is honest about it and the report says "not quotable until rerun" —
   which is the right behaviour, and it is still a debt. Log it in §5, the way
   §1.4's seed debt was logged, or it becomes a quoted number.
8. **Reading a catalogue against itself is the default failure.** Phase 1b only
   means anything because `geipan_to_ufo_data.py` deliberately leaves GEIPAN out
   of `CATALOG_META`. Make that choice explicitly, in code, with a comment.

---

## 2. In flight when session 5 ended, and the branch fork

**NOTHING in flight.** Working tree clean, everything pushed.

**THE FORK, AND ITS RESOLUTION.** Session 4 ended at `49febcf` on
`claude/gallant-lamport-0tu52r`. Three session-5 threads then branched from that
same commit, within 13 minutes of each other, none aware of the others:

| branch | tip | content |
|---|---|---|
| `claude/project-thread-noala8` | `75cfd74` 06:27 | GEIPAN Phases 1–3 + red team |
| `claude/project-thread-het5pi` | `b24fb5b` 06:28 | NT-16 write-up and replication |
| `claude/project-thread-eck2kl` | `d9a92df` 06:40 | DIRD area assignment; FOIA Letter 14 |

All three were merged into **`claude/nice-ritchie-j1ve90`**, which was
fast-forwarded to `49febcf` first (it held no work of its own). Three `--no-ff`
merges, **zero conflicts** — the threads touched disjoint files apart from two
small edits to this file and the vault manifest. **That was luck, not design.**

**Current branch: `claude/nice-ritchie-j1ve90`** — the consolidated line, and
the only branch with all of sessions 1–5. The five older branches
(`gallant-lamport-0tu52r`, `magical-gauss-wzgdqd`, and the three
`project-thread-*`) are **superseded**. Do not branch from them and do not read
their copies of this file; they predate §1.16.

**Procedure for a new session, in this order:**

1. `git ls-remote --heads origin` and compare against the tip this file records.
   **Any `claude/*` branch with commits the consolidated line lacks is session
   work this file does not know about.** Read its reports before trusting §1.
2. Fast-forward your assigned development branch to the consolidated tip rather
   than branching from `main`.
3. If you find siblings, merge them (`--no-ff`), then **rewrite §1 and §6 before
   doing new analysis** — two of the three session-5 threads modified session 4's
   conclusions, and for an hour this file stated a claim that had been withdrawn.
4. If you are one of several parallel threads, say so at the top of your report
   and name the tip you branched from.

## 3. Ephemeral data — what is DURABLE, and what is not

**Everything expensive is in `evidence_vault/` (~145 MB, plus the session-4 and
session-5 additions, committed).**

| in the vault, no re-fetch needed | size |
|---|---|
| 860 periodical texts (MUFON/APRO/IUR) | 29.9 MB gz |
| PURSUE server OCR, 286 docs | 7.0 MB gz |
| 37 AAWSAP DIRD texts | in-tree |
| TEP dossier, 10 files / 177 pp | 14 MB gz |
| trace-control dossiers, 16 files | 69 MB gz |
| NUFORC unified, 134,906 recs | 11.6 MB gz |
| GEIPAN case DB, codename index, 434-list | in-tree |
| **seed-stability sweeps (session 4)** | `09_SEED_STABILITY/` |
| **GEIPAN Phases 1–3 (session 5)** | `11_GEIPAN_PHASE123/geipan_phase123.json` |
| **DIRD per-area assignment (session 5)** | `01_PURSUE_PRIMARY/dird_area_assignment.json` |
| **TEP page-by-page OCR (session 5)** | `02_GEPAN_PHYSICAL_TRACES/…/tep_dossier_pageocr_2026-11-26.tar.gz` |
| **redaction slot analysis (session 4)** | `05_SCRUBBED_CONTENT/redaction_slots.json` |
| **AAWSAP contract audit (session 4)** | `01_PURSUE_PRIMARY/aawsap_contract_audit.json` |

**Still ephemeral, and cheap to rebuild:**

| what | recovery | cost |
|---|---|---|
| the 286 PURSUE texts, unpacked | `tar xzf evidence_vault/01_PURSUE_PRIMARY/pursue_server_ocr_286.tar.gz` into a scratch dir, then pass it as `OMEGA_PURSUE_TXT` | seconds |
| `data/raw/pursue_ocr/txt` (40 OCR'd Release_07/08 docs) | re-OCR via `omega/pursue_ocr.sh` | ~40 min |
| NUFORC raw CSV | `archive.org/cors/data-world-snapshot-20260713-agent-drastimehta/nuforc-ufo-event-sightings-csv.zip` | 1 min |
| Wikidata gazetteer, 1.74 M entries | `python3 -I omega/gazetteer.py` | ~20 min |
| DIRD **PDFs** (1,779.6 MB — deliberately not stored) | `01_PURSUE_PRIMARY/FETCH_MANIFEST.json` | ~30 min |

**NOTE:** `omega/redaction_slots.py` and `omega/aawsap_contract_audit.py` read
the PURSUE texts from `$OMEGA_PURSUE_TXT` (falling back to
`data/raw/pursue_ocr/txt`). Untar the vault copy and set that variable.

## 4. Environment

**`UFOAI Omega research`** (`env_018sxdcbBHMGqCRwh6KXDi6D`), personal, 8 hosts:
`archive.org`, `www.geipan.fr`, `geipan.fr`, `cnes.fr`, `query.wikidata.org`,
`nominatim.openstreetmap.org`, `earth-search.aws.element84.com`,
`en.wikipedia.org`. Package managers and MCP hosts allowed.

**The setup script is VERIFIED WORKING as of sessions 4 and 5** — tesseract 5.3.4 with
`fra`, poppler 24.02, scipy 1.18.1, sklearn 1.9.1, installed ~2 min after boot.
Do not re-litigate this; just use it.

**Blocked, unchanged:**
- `web.archive.org` — proxy 403. The CDX API exists nowhere else, so **Wayback
  snapshot comparison cannot run.** `archive.org/cdx/...` 404s.
- `www.cnes-geipan.fr` — proxy 403.
- An `update_environment` request to add both was **rejected by the environments
  service.** Do not re-ask in chat.
- `war.gov`, `aaro.mil`, `nuforc.org`, CIA/FBI/NRO/NASA reading rooms,
  `arxiv.org`, ESA WorldCover.

**Worth asking the user for:** `arxiv.org` (to verify the VASCO/Doherty chain
from source rather than memory) and a landcover raster host (Track 2 matching is
currently a spectral proxy).

Note: combined remove+add `update_environment` calls are rejected — do them
separately.

---

## 5. Next, in priority order

**Session 5 closed old items 1 and 2.** Item 1 (per-area DIRD assignment) is done
and withdrew a claim; item 2 (CLIN-named FOIA requests) produced Letter 14 and
four remaining targets. The list below is renumbered.

### 1. **Re-run GEIPAN Phase 2 against an authoritative nuclear-site layer** — a debt, not an improvement
`omega/geipan_phase123.py`. The 28-site layer is **hand-entered from general
knowledge** (±1–3 km, ±1 yr; only 4 of 28 cross-checked) because Wikidata and ASN
were unreachable. The report flags itself as not quotable, which is correct and is
still a debt — §1.4's seed debt sat unpaid for three sessions and the fix changed
the published number. **`query.wikidata.org` IS on the environment allowlist**, so
the P625-with-statement-node construct from §1.11 will work; IAEA PRIS or ASN need
a host request. Re-run, then either confirm the twelve nulls or report the change.
Cheap, bounded, and it unlocks a result that is otherwise unusable.

### 2. **Confirm the two OCR-only session-5 claims on the page images**
Both are load-bearing and both carry an explicit "confirm before quoting":
**D186 p.1's "Twelve additional reports were produced and delivered"** against a
release holding eleven (§1.16 item 2, finding 5), and D186's twelve-area list
ending in `technology integration` (finding 4). The JP2 page images exist for all
298 documents. If finding 5 holds, **one FY2010 DIRD is unaccounted for** and that
is a second nameable gap alongside D66–D73 and the capstone.

### 3. **Draft the four remaining FOIA targets**
Letter 14 covers the capstone. Still undrafted: the **~24 per-area Project
Management Plans** (CLIN 1002, $4.76M, the contract's largest line item), the
**~20 missing monthly status reports**, the **as-delivered BAASS versions with
their §11(c) executive summaries**, and the **Sandia National Laboratories
reviews in D188 Enclosure 2**. Add a fifth if §5 item 2 confirms the twelfth
FY2010 report. Also now nameable: **P00002's missing deliverable-impacts
attachment** (§1.16 item 2, finding 7) — if CLIN 1004 was descoped, that is where
it is recorded. Add to `omega/reports/foia_request_drafts.md`. **Drafted, not filed.**

### 4. **A second blind reader on the 20 contested DIRDs**
`dird_area_assignment.md`'s own red team names this as the real test. The framing
sentences are stored in the JSON, so a second reader can work from those alone
without re-reading 37 PDFs. Expect κ well below 1. The flip ranges are designed
to absorb the disagreement; this measures whether they do.

### 5. **Redaction slots on the FY2010 DIRD wave and the 1950s scans**
`redaction_slots.py` covers 33 MISREP forms. 226 field instances are UNREADABLE
and carry no claim; the 1950s FBI scans (14 hits) were excluded by the spine gate.
Re-OCR the worst forms at higher dpi to make UNREADABLE decidable, and build a
prose-mode slot reader for the non-form documents.

### 6. **OCR the 23 declared image-only PURSUE docs** (`_imgonly`), including the
D60/D63/D65 mission reports flanking the D66–D73 gap. `tesseract -l eng`,
`OMP_THREAD_LIMIT=1`. Feeds straight into item 5 and into item 2's page-image work.

### 7. **Track 2, REPOINTED** — historical sites are temporally impossible (34–51 yr
gap vs Sentinel-2's June 2015 launch). Run the existing control methodology on the
**34,898 geocoded Sentinel-2-era NUFORC records**. Control code:
`omega/track2_controls.py`. A landcover raster host would move this off a spectral proxy.

### 8. **Remaining periodical work** — the 860 texts are vaulted. Build the full
provenance graph for the 434-event retained-sample list, tracing each to its
earliest primary source. §1.16 item 4's Phase 1b result sharpens the question:
the enthusiast literature over-samples unexplained cases ~4× within a decade, so
the graph should report that selection, not just the chains.

### 9. **NHI Proof Report** — write it last, from the vault. On current evidence it
is a null report with a short list of live threads. Writing it honestly is the
deliverable.

### Blocked, not pending
The retained-sample assay is blocked on **physical custody**, not chemistry —
CUFOS/APRO/GEPAN/university archives are unreachable. Wayback snapshot comparison
is blocked on `web.archive.org` (proxy 403; the CDX API exists nowhere else, and
an `update_environment` request was rejected by the environments service — do not
re-ask in chat).

---

## 6. Established results so far (do not re-derive)

**Falsified:** nuclear proximity (contamination — 0.6% of records produced 100%
of a 13× effect; **independently replicated as null on the GEIPAN state file,
12/12 statistics, §1.16 item 4 — subject to that section's site-layer debt**);
ICBM proximity (self-referential — the March 1967 Minot/Malmstrom cluster is the
claim's own founding data); sacred-site proximity (megalith ratio 1.004, p=0.56);
light-code entropy; solar-cycle periodicity; persistence (cross-pipeline
geocoding artefact — Nominatim and Hatch DMS agreeing on settlement centroids);
all 7 behavioural-intelligence tests T1–T7.

Blue Book T3: **null at adequate power**, p=0.2727, MDD 0.1169 vs 0.112 target.
Resolved arm itself significant (+0.0354, p=0.0017). **7× gradient from compiler
prose (+0.2504) to case record (+0.0354).**

**The French unexplained residue collapsed, confirmed three independent ways:**
rate 0.0543→0.0144, z=+6.119, **p=9.4e-10** (§1.3); BAASS's own mid-2009 count of
**205 D cases against today's 106** — an absolute decrease, immune to the
denominator objection (§1.9); and per-decade logistic **OR 0.69/decade
(0.62–0.77), p=8e-12** (§1.16 item 4). Top modern identified cause is sky
lanterns (417 / 366 depending on window), a product absent from France before
~2005. **The toolkit changed, not the sky.**

Undisclosed D cases are the re-examined ones: revisit rate 0.9821 vs 0.1600,
**z=+8.605**, decade-stratified **Mantel-Haenszel OR 209.10** — stratification
strengthens it. **Direction of causation undetermined and reported as such.**

Provenance collapse 1.39–1.46×, 77–80% single-sourced. Echo chamber 3.628 vs
null 5.130 (29% below chance, z≈−31); 12 events with 5–6 catalogues and zero
upstream roots. Strict periodical test: **controls 4/4, targets 0/4.**
**And the enthusiast literature is not a sample of French reports** — 2.1% of its
French events appear in the state file, and within a decade a case the state
could not explain is **~4× more likely to be catalogued** (MH OR 4.0, p=1.8e-5).

Descriptor drift: **replicated on the state file and it survives inside the
unexplained subset** — photo/video OR 2.58/decade (3.3%→44.5%), triangle 1.15
(1.33 in C+D), disc 0.77, landing/trace 0.68 (6.9%→1.1%). A fixed physical
population of craft does not predict that.

Occupant taxonomy: no spatial (p=0.52) or temporal (p=0.53) segregation; era
χ²=70.4 p=1.5e-07, pseudo-human 46.1%→13.6% vs Grey →63.2%.

**The C-vs-D narrative effect is capped, not content.** 42% ± 9% identifiable
leakage; residual **+0.1972 ± 0.0271 is an UPPER BOUND**, because the C/D
criterion *is* informational adequacy. A+B-vs-D withdrawn as circular by
construction. Adjacent tiers are not distinguishable; only the endpoints separate.

**The AAWSAP programme is a literature survey, not a capability programme.**
1 of 37 DIRDs mentions UAP at all; open:closed citations **27.5:1**. The one
exception (D128, human tissue effects) concludes injuries are attributable to
**"real-world … technologies"** — terrestrial RF/microwave.

**All 26 FY2009 deliverables are present** (26/26 via the release's own
author-pseudonym namespace). **The capstone is absent**: Integrated Threat
Assessment, **CLIN 0004 $240,000 / CLIN 1004 $220,200**, two due conditions
reached (30 Sep 2009 and 21 Dec 2010), no report and no briefing. **Nine of
twelve contracted areas are covered under every reading; lift, control and
configuration each rest on one contested report; control has no FY2009 report.**
BAASS itself called a threat assessment future work on 23 Nov 2010 — **which fits
"never produced" at least as well as "withheld".**

**Redaction protects force composition, not the observation.** Callsign withheld
0.91, personnel 0.63, time 0.09; never released: Email, Full Name, Aircraft
Callsign, Phone, Number of Aircraft. `Gentext` — the UAP description — released
115 vs 37 withheld. E.O. 13526: 1.4(a) military ops **224**, 1.4(c) intelligence
sources/methods **1**. 77.0% agreement with the government's own exemption codes.
**Reported as a negative: it cuts against a suppression reading.**

**Trans-en-Provence: the biochemistry replicates, the inference does not.** 9/11
correlations recovered to ±0.01; distance gradient survives every available null
at **P=0.0028** (the design's floor). But NT-16's P-values are one-sided and one
is **50× too small**; only β-carotene and young-leaf violaxanthine clear ±50%
analytical noise; the soil mass-spec's two plates of the same soil **disagree by
a median factor of 23**, so the "rubbed paint" reading is not a reproducible
measurement. **Finding a trace does not predict D (OR 1.0–1.1, p=0.89); looking
for one does (OR 2.7, p=0.015).**

**Hidden-term sweep, 617 documents: clean zeros** for non-human
personnel/biologic, crash retrieval, human-looking, breakaway civilisation,
shadow government, pseudo-human, majestic, serpo, glimmer glass, kona blue,
looking glass, teaball, moon dust, immaculate constellation. `MJ-12`: one hit, a
citizen's letter *asking* about it. `AARO` appears in 44.

**Track 2 on historical sites is temporally impossible** (Sentinel-2 launched
June 2015; candidates are 1964–1981). Controllability is inversely proportional
to local sighting density — Newark Valley yields 2 clean controls from 17.

**Three nulls withdrawn as invalid:** global class-label permutation across
disjoint footprints; density matching at the wrong scale; outcome-conditioned
subsetting.

**Two claims withdrawn in session 5:** "no contracted area went undelivered"
(true under one reading, false under another); and the carotenoid-over-chlorophyll
*pattern* as an anti-ionising argument (within analytical noise in series 1,
**reverses at the centre** in series 2). INRA's 10⁶-rad γ-benchmark itself stands.

**Seven failure modes documented** — contamination; underpowered artefact;
self-referential source events; narrative convention; cross-pipeline geocoding
convergence; marginal-to-stratified collapse; criterion-definitional confounding.

arXiv:2604.00056 (Doherty, 31 Mar 2026, POSS-I plate transients, IRR 1.80,
permutation p=0.006, Earth-shadow deficit) **verified real**; does not conflict
with Phase 2 (different instruments). Untested alternative: radioactive fallout
fogging photographic emulsion — the Earth-shadow deficit is the discriminating
measurement. **Note §1.2 as amended by §1.16: INRA's γ-benchmark argues against
an ionising mechanism at trace sites; the pattern argument does not.**

**14 FOIA letters and the French CADA request drafted, none filed:**
`omega/reports/foia_request_drafts.md`, `omega/reports/cada_request_draft.md`.
Targets: DOW-UAP-D66–D73; NASA-UAP-D3 and D23–D29; the 56 undisclosed French
D-case dossiers; and **Letter 14 — the Integrated Threat Assessment by CLIN.**
