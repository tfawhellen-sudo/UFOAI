# A1 — claim drift on the 80 corroborated events

*Project Omega, 2026-11-27. Arm A1 of `omega/reports/assay_protocol_434.md`
(preregistration commit `480a1fa`). Deviations D1–D7 were logged before any
coder output was seen: `omega/reports/assay_protocol_434_deviations.md`.
Code: `omega/a1_claim_drift.py`. Everything is in this folder: the coding
package, the key (sha256 `48bf6d3c…b611190`, matching D6), both coders' raw
output, the adjudication file, and `a1_results.json`.*

## Bottom line

- **H1 is not confirmed.** Of 80 events, the compiled catalogue adds a
  physical claim missing from the earliest bulletin text in **16**, and drops
  one that the bulletin had in **14**. One-sided exact McNemar **P = 0.43**.
  The net drift is +2.5 points, 95% CI −10.9 to +15.9.
- **That isn't a certified null.** The protocol set no equivalence bound for
  A1, and the CI can't exclude a drift of up to about 16 points. The correct
  label is **inconclusive, with no evidence of accretion**. The physical-trace
  claims in this subset are, on balance, already in the first printed report.
- **Gate G1 does not apply.** Because H1 isn't confirmed, A2–A4 keep every
  event, not only those whose claim is in the earliest root.
- **Coding is reliable.** Coder agreement on "any physical claim" was κ = 0.918
  over all 240 texts, and κ = 0.886 on the 20-event calibration set (threshold
  0.70). 18 of 2,160 item codes disagreed. All 18 were adjudicated by checking
  the quote, with the reason for each recorded in `adjudication.json`.

## Results

| test | n | added (b) | dropped (c) | both | neither | P (one-sided) |
|---|---|---|---|---|---|---|
| **H1, primary** | 80 | 16 | 14 | 15 | 35 | **0.43** |
| SA1, root cut to 400 characters (D3) | 80 | 21 | 12 | 10 | 37 | 0.081 |
| S2, ROOTED (lag ≤ 24 months) | 43 | 6 | 10 | 11 | 16 | 0.89 |
| S2, LATE_ONLY (lag > 24 months) | 37 | 10 | 4 | 4 | 19 | 0.090 |
| Item 9, anomalous lab result | 80 | 2 | 0 | 0 | 78 | 0.25 |

Leave-one-event-out: the largest primary P is 0.50, and no single event
moves the result.

**S1 by claim type** (added / dropped): ground mark 3/7, burn 4/6, residue
5/1, radiation 1/1, vegetation 4/3, animal 5/2, injury 3/7. None is
significant (smallest P = 0.11, residue). The only types leaning toward
accretion are residue (5 to 1) and animal effects (5 to 2). They are small
counts, and this is a secondary analysis.

**Coverage.** 29 earliest-root texts and 31 catalogue texts carry at least one
physical claim. The catalogue median length is 400 characters (truncated,
D2). The root median is 649.

## Reading it

1. **The direction flips with lag, though not significantly.** For events in
   print within 24 months, the catalogue drops more claims than it adds
   (6 vs 10, net −9 points). For events first in print after 24 months, it
   adds more (10 vs 4, net +16 points, CI −3 to +35). That fits a story in
   which retellings far from the event accrete detail. It is a secondary
   result at P = 0.09 and is **not a finding**. It's a hypothesis for the next
   corpus: NICAP's *UFO Investigator* and FSR, when they're acquired.
2. **SA1 moves toward accretion.** Cutting the root text to the same 400
   characters as the catalogue removes root claims (c falls from 14 to 12) and
   adds to b (16 to 21). Part of the 14 "drops" in the primary is the
   catalogue's 400-character cut removing claims, not historians removing
   them. That's the bias D2 predicted. SA1 shows that matching lengths does not
   produce significant accretion either (P = 0.08, CI −2.6 to +25).
3. **What A1 can't tell.** A claim "added" later can come from a later field
   investigation, not invention (protocol §9, item 6). Every addition can be traced through `key.json` and the coders' quotes,
   and read by eye.

## Red team

- **The catalogue text is truncated at 400 characters,** and the compile date
  of each catalogue entry is unknown (D2). A full-text rerun needs
  `master_catalog_inclusive.json`, which is not in the repository. Rebuilding
  it from `ufo_data/bin` through `omega/dedupe.py` is the fix.
- **The earliest-root text is a ±320-character window,** not the whole
  article. A claim further down the article is invisible. This biases b
  upward, against the null result, so it makes the null conservative.
- **The coders are two runs of one model family.** κ measures their agreement
  with each other, not their accuracy. No human checked a sample of codes
  beyond the 18 adjudicated items.
- **Masking was by regex.** OCR style alone tells bulletin text from catalogue
  prose, so coders could in principle tell R from C. They weren't told texts
  were paired, and the shuffle mixed all 240.
- **The analyst was not blind during adjudication** (D4). The 18 adjudicated
  codes moved the primary from 16/13 to 16/14. Unadjudicated, P was 0.36. The
  conclusion doesn't depend on them.

## Reproduce

```
OMEGA_PERIODICALS=<dir of the 860 txt> python3 -I omega/a1_claim_drift.py build <outdir>   # key sha256 must be 48bf6d3c…
python3 -I omega/a1_claim_drift.py score omega/reports/a1_claim_drift \
  omega/reports/a1_claim_drift/coder_A.json omega/reports/a1_claim_drift/coder_B.json \
  omega/reports/a1_claim_drift/adjudication.json
```
