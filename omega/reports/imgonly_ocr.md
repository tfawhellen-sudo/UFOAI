# OCR of the 23 image-only PURSUE documents

*Project Omega, session 5, 2026-11-26. Closes handoff §5 item 4. Texts:
`evidence_vault/01_PURSUE_PRIMARY/imgonly_ocr/` (23 files, plus `SOURCES.tsv`
with URL, size and upstream SHA-1). Method: `pdftoppm -r 300 -gray`, then
`tesseract 5.3.4 -l eng --psm 1` with `OMP_THREAD_LIMIT=1`, 4 processes. All 23
PDFs matched the archive's SHA-1 before OCR.*

## What the 23 are

The archive labels them itself, with an `_imgonly_pdfmeta.json` derivative.
**17 of the 23 have no text to recover.** They are photographs and renderings:
FBI-Photo-B1/B5/B6/B11/B12/B15/B16/B18/B19/B21, the 2024-04-30 composite
sketch, and FBI-UAP-D003/D027/D038/D039/D041/D042. Each yields 3 to 64
characters of OCR noise. That's a negative, and it's reported as one. Nothing
is hidden in them as text.

**6 carry text, 41,378 characters in all:**

| document | pp | chars | content |
|---|---|---|---|
| DOW-UAP-D60 Persian Gulf, Aug 2020 | 6 | 6,656 | MISREP: `OBSERVED 1X UAP` in Gentext |
| DOW-UAP-D63 Strait of Hormuz, Oct 2020 | 8 | 9,092 | MISREP: `BSERVED 1X UAP, SEE OBSERVATION LINE 1` |
| DOW-UAP-D65 Persian Gulf, Jul 2020 | 8 | 8,451 | MISREP: three `OBSERVED AN UNIDENTIFIED AERIAL PHENOMENON` lines; `Observed Activity Description: UAP` |
| CIA-UAP-010, conversations with Soviet scientists (1967 report) | 2 | 4,406 | unevaluated information report on Soviet astronomers' views of UFOs |
| NASA-UAP-D4, Apollo 11 technical crew debriefing | 11 | 10,776 | debriefing excerpt |
| NASA-UAP-D6, Apollo 17 technical crew debriefing | 2 | 1,997 | light-flash discussion (`light flashes just about continuously … when we were dark adapted`) |

## The three mission reports that flank the D66–D73 gap

These are the three forms session 3 flagged as image-only (`D60/D63/D65 flanking the D66–D73 gap are image-only`).
They now feed `omega/redaction_slots.py`. That needed one parser fix: local tesseract renders the form bullet as
`*`, `¢`, `«` or `-` where archive.org's OCR gives `•`. So line-leading glyphs before a `Label:` are normalised
for this directory only. The other 33 forms are untouched: their 582 withheld instances reproduce exactly.

| | session 4 (33 forms) | with D60/D63/D65 (36 forms) |
|---|---|---|
| withheld / decidable | 582 / 2,229 = 0.261 | 639 / 2,458 = 0.260 |
| CALLSIGN withheld | 0.91 | 0.88 |
| PERSONNEL | 0.63 | 0.63 |
| NARRATIVE | 0.41 | 0.41 |
| TIME | 0.09 | 0.09 |
| agreement with the government's own exemption code | 77.0% | 77.3% |

**The three gap-flanking forms behave like the other 33.** They add 57 withheld field instances in the same
slots: callsign, personnel, unit, operation. In all three, the line stating a UAP was observed is **released**.
That replicates session 4's negative on new documents: the release withholds force composition and identity,
not the observation. It says nothing about what D66–D73 contain.

## Limits

- Single-pass OCR at 300 dpi. The inline classification markers come through degraded (`_14a`, `44a`, `1,48`
  for `1.4a`). The slot reader's tolerant regex catches most of them, and the rest fall into UNREADABLE (+23).
- The six text documents haven't been read in full for new findings. Only their UAP lines were checked.
