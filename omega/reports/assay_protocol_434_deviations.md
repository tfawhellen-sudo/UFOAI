# Deviations log: 434-event assay protocol

Protocol: `omega/reports/assay_protocol_434.md`. Entries are written **before**
the affected data are looked at (protocol §7.2 step 6).

## Preregistration timestamp
- Protocol commit: `480a1fa2a989f04c3b928d436f05fcde5cf5cddd`, committed
  2026-11-26T22:10:59Z.
- First pushed to `github.com/tfawhellen-sudo/UFOAI`, branch
  `claude/project-thread-q3u58m`, on 2026-11-27 at about 00:21Z.
- Nothing else in this repository had coded any A1 claim content before that
  commit.

## D1 (2026-11-27, before A1 coding). Registration is git-only.
Protocol §7.2 step 1 calls for posting the commit hash publicly (OSF or a
dated gist). The owner has not approved any public post. The commit hash and
the GitHub push time are the only timestamp. The repository is private and
under the analyst's control, so this is weaker than an independent registry.
A reader has to trust that history was not rewritten. The hash is quoted above
so a later public posting can be checked against it.

## D2 (2026-11-27, before A1 coding). Exact definition of the A1 texts.
The protocol names the earliest corroborating issue and the `description`
field. Operationally:
- **Earlier text (R).** Every context window in the earliest corroborating
  issue that satisfies the provenance rule (place token, plus the event's year
  and month within ±320 characters, `provenance_graph_434.py`), merged in file
  order. Overlapping windows are joined.
- **Later text (C).** `description` in `priority_434.json`. **This field is
  truncated at 400 characters** by `track1_samples.py`. The full master
  catalogue (`data/processed/provenance/master_catalog_inclusive.json`) is not
  in the repository. The catalogue's compile date is not recorded per row. It
  is a compiled catalogue, later than the bulletin for practically every
  event, but "latest catalogue" in the protocol should be read as "the
  compiled-catalogue text on file".
- **Consequence.** The 400-character cut can only *remove* claims from C. It
  biases A1 against finding additions, which is conservative for H1.

## D3 (2026-11-27, before A1 coding). Declared sensitivity analysis on text length.
R can be longer than C when several windows match. Sensitivity analysis SA1:
R is replaced by the first matching window only, cut to 400 characters centred
on the place token. Then H1 is re-tested. SA1 is secondary.

## D4 (2026-11-27, before A1 coding). Coders.
Two independent model coders, each a separate subagent run with no shared
context and no access to the repository. Each sees all 160 texts in one
shuffled list, under random IDs, with source names, issue dates and event dates
masked where a regex can find them. Coders aren't told which texts pair up or
which is earlier. The analyst adjudicates disagreements from the coders'
quotes. **The analyst is not blind** (OCR bulletin text and catalogue prose are
easy to tell apart, and the analyst built the pairs). Adjudication is
therefore restricted to checking each coder's quote against the text. If the
coders still disagree after that, the item is scored 0. That's conservative
for "claim present" in both texts and so neutral between b and c.
- κ check: the 20 pairs with the lowest random key form the calibration set
  and are excluded from the confirmatory test if the codebook has to be
  revised. If κ ≥ 0.70 on the first pass, they stay in.

## D5 (2026-11-27, before A1 coding). OCR quality.
Bulletin texts are OCR (djvu text layers). Masking and coding operate on the
text as it is, with no OCR correction.

## D6 (2026-11-27, after building the package, before any coding).
- Seeds were not in the protocol commit. They are fixed in
  `omega/a1_claim_drift.py`: `SEED = 4340` drives the item IDs and the shuffle.
  The calibration set is the 20 events with the lowest sha256(event_id + seed).
- The package has **240 texts**, not 160: for each of the 80 events, R (full
  earliest-issue windows), R_SA1 (the 400-character root for D3) and C. All
  three are shuffled together, so coders can't pair them by position.
- Key file `key.json`: sha256
  `48bf6d3c3b8219a73eb190ef679f709e3fbdaa69cd11898dacc03cd28b611190`,
  committed here before coding. The key itself is committed with the results.
- Masked text, median 399 characters. Masking is regex-only. Some OCR
  variants of month names and source names will survive.
