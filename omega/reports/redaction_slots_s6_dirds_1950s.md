# Redaction slots, part 2: the AAWSAP DIRDs and the 1940s–1950s scans

*Project Omega, session 6 (2026-11-26). HANDOFF §5 item 3. Script: `omega/redaction_boxes.py`.
Data: `evidence_vault/05_SCRUBBED_CONTENT/redaction_boxes_s6.json`.*

## Why a new instrument

The session-4 slot reader (`redaction_slots.py`) works on MISREP forms, where the 2026 release
prints an exemption code inside each redaction box, so the OCR shows it. Neither corpus here
works that way:

- **DIRDs.** The OCR of all 37 shows no exemption code anywhere. The only withheld tokens are
  the pseudonyms `AAP Person NN`, one or two per document (author, plus the DWO-3 point of
  contact `AAP Person 1`, plus co-authors on D138 and D146). Four apparent code hits were page
  ranges in references (`pp. 4549-4552`).
- **1940s–1950s scans.** Every apparent `b6`/`b7` hit in the OCR is the typewriter word "by"
  misread as `b7` (for example `submitted b7 Mr.`). There are **no real exemption codes** in
  the OCR of these 73 documents.

So if anything is withheld, it would be an **uncoded black box**, which leaves no trace in
text. `redaction_boxes.py` looks for those on the page images. It renders each page at 50 dpi,
removes text strokes with a 3×3 morphological opening, and keeps solid near-black components
that are at least 0.30 × 0.10 in and at most 3 in tall, have a fill of 0.92 or more and are
uniformly dark (σ ≤ 25 gray levels).

**Positive control.** I drew three black boxes on the D186 page image (one word, one line that
overlaps text, one paragraph). The scan found **3 of 3**, but only after the opening step was
added; before it, the line box merged with the text and was missed. **Negative controls:** D186
(white outlined boxes with codes) gave 0, and FBI D011 (no redactions) gave 0.

## Result

| corpus | docs | pages | black components | inspected as | content redactions |
|---|---|---|---|---|---|
| DIRDs FY2009 (D117–D142) | 26 | 962 | 58 | 26 cover-template bars + 32 figure/table/photo elements | **0** |
| DIRDs FY2010 (D143–D153) | 11 | 511 | 17 | 11 cover-template bars + 6 figure elements | **0** |
| 1940s–1950s scans | 73 | 3,160 | 30 | 21 dark photos (CIA-UAP-003, U-2/OXCART history), 1 photo (D093), 2 film-strip photos + 2 struck `RESTRICTED` stamps (D102), 1 headline glyph (FBI D013), **2 blackout bars on D102 pp.71–72** | **0 confirmed; 2 ambiguous** |

Every component was classified by eye from crop sheets. D128's full-width bars (pp.37–38) are
the shaded section-header rows of a symptom table; I checked the page image at 70 dpi.

**D102 pp.71–72** (U.S. Naval Photographic Interpretation Center, Tremonton film report,
4 May 1953) carry real hand blackouts. There are two lines above the `From:` line and two lines
at the foot, right next to the `DOWNGRADED AT 3 YEAR INTERVALS; DECLASSIFIED AFTER 12 YEARS.
DOD DIR 5200.10` stamp, with `UNCLASSIFIED` stamped over them. Their position (header and footer)
and the downgrade stamp beside them fit **cancelled classification markings** (for example
`CONFIDENTIAL / SECURITY INFORMATION`). That is my reading from position, not a recovery of the
text, and I did not try to read under the bars.

## Tests against the hypotheses

1. **H1: the FY2010 wave is redacted more heavily than FY2009, because D185 says four to six
   reports would be expanded with classified data.** Content redactions: 0/962 pages for FY2009
   and 0/511 for FY2010. The difference is 0, and the 95% upper bound on the FY2010 per-page
   rate is 3/511 = 0.59% (rule of three). **H1 is not supported.** The DIRDs are published
   whole. If classified FY2010 work exists, it was withheld as whole documents, not redacted
   inside these. That fits Letter 15 item 4 (the twelfth report) better than "redacted in place".
2. **H2: the 1950s releases hide content behind uncoded blackouts.** 0 confirmed in 3,160 pages
   (95% upper bound 0.095% per page). The only blackouts sit in marking positions.
   **H2 is not supported.**

## Red team

- **Recall is not 100%.** Whiteout, cut-out, or grey (not black) redactions are invisible to
  this detector. Boxes thinner than 0.10 in (a struck-through single line) are below the
  threshold. The positive control used clean black boxes; a hand-inked blackout on a 1950s
  scan is noisier, and the D102 hits show the detector does find those.
- **Dark photos make noise but do not hide anything.** The 21 CIA-003 hits are photographs. A
  redaction box that sits inside a photograph would be missed.
- **The page denominators are archive.org's rendered PDFs.** Pages removed from a release before
  scanning (whole-page withholding) are invisible here by construction. That is the FOIA
  letters' job, not this scan's.
- **The DIRD pseudonymisation is the one withholding, and it is (b)(6).** I did not attempt to
  resolve any pseudonym.

## Verdict

Neither corpus withholds content inside its pages. The AAWSAP DIRDs withhold names only, and
the 1940s–1950s scans withhold nothing detectable beyond cancelled markings. Any gap is at the
**document level**: missing enclosures, months and CLIN deliverables. Letters 14–18 target
exactly those.
