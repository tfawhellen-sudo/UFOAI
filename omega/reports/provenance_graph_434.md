# Provenance graph for the 434-event list

*Project Omega, session 5, 2026-11-26. Closes handoff §5 item 6. Script:
`omega/provenance_graph_434.py`. Graph and per-event classes:
`evidence_vault/07_PERIODICALS_PRIMARY/provenance_graph_434.json` (434 nodes, 187
issue→event edges). Corpus: the 860 vaulted periodical issues. 844 are dated, and
16 IUR issues carry only a volume number and are skipped.*

## Bottom line

- **43 of the 310 testable events (13.9%) have a contemporaneous primary root.**
  A root here is a bulletin issue that names the place and the event's month and
  year, printed no more than 24 months after the event. 18 of the 43 were in
  print within 3 months.
- **That's far above coincidence.** Shuffling event dates across events (200×,
  place tokens fixed) gives a null rooted rate of 1.2% (95% range 0.3–2.3%).
  None of the 200 shuffles reached 13.9%, so P < 0.005. The effect over the null
  is **+12.7 points, bootstrap 95% CI +8.8 to +16.5.**
- **The built-in false-positive probe is low.** In 1.3% of testable events the
  rule "corroborates" in an issue printed *before* the event, which is
  impossible. That matches the shuffle null, so the rule's coincidence rate is
  about 1%.
- **86% of testable events have no root in this corpus.** 230 are ABSENT and 37
  are LATE_ONLY, first appearing more than 24 months later (median lag for all
  corroborated events: 18 months).
- **Catalogue count predicts having a root, and the trend is monotone.** The
  rooted rate is 6.7% for 1-catalogue events, then 10.5%, 12.5%, 25%, 18%, and
  **44% for 6 or more catalogues.** Mean catalogues are 3.98 rooted vs 2.33 not
  rooted, permutation P = 0.0001. Within this list, the heavily catalogued events
  are mostly the ones with a real contemporaneous report under them. The echo
  chamber is concentrated in the thinly catalogued tail. The session-3 finding
  still stands for its own 12 named events, which are absent here too.

## Classes

| class | n | meaning |
|---|---|---|
| ROOTED | 43 | earliest corroborating issue 0–24 months after the event |
| LATE_ONLY | 37 | corroborated, but first more than 24 months after |
| ABSENT | 230 | in coverage, place token usable, no corroborating issue |
| NO_TOKEN | 93 | blank location (88 rows) or only generic words |
| OUT_OF_COVERAGE | 29 | before Jul 1952 or after Dec 2008 |
| NO_DATE | 2 | unparseable date |

By decade, the rooted rate among testable events is 3% in the 1950s (APRO only),
16% in the 1960s, 16% in the 1970s, 27% in the 1980s, and 11% in the 1990s.
**Coverage drives this as much as the events do.** MUFON/Skylook starts in 1967
and is US-centred, so a 1950s or a non-US event has fewer chances to be found.

The top of the priority list does well. Socorro (1 month), Delphos (0), Eagle
River (1), Cherry Creek (3), Falcon Lake (0) and Galt (2) are all ROOTED.
**Trans-en-Provence is LATE_ONLY (38 months).** It's a positive control in
session 3's looser test. The strict rule needs the month *name* near the place,
and the 1981 bulletins evidently don't print it that way. So the strict rule
undercounts, which makes the 13.9% a floor.

## Red team

1. **The detection rule is strict on purpose, and that costs recall.** Dates
   written `8/1/81` or `8 Jan.` without the full or 3-letter month are missed.
   TEP shows the cost. ROOTED is a lower bound.
2. **A common place name can root by coincidence.** London, Portsmouth, Hampton,
   Alice and Jenkins are among the 43. The shuffle null prices this in on
   average (about 1%), but any single ROOTED edge for a common name should be
   read by eye before it's quoted. Every edge carries an `example_context`.
3. **The corpus is three bulletins.** NICAP's *UFO Investigator*, *Flying Saucer
   Review*, local newspapers and CUFOS case files are absent. ABSENT means
   "absent from these 844 issues", not "no primary source exists".
4. **Catalogue count and coverage may share a cause.** An event a US bulletin
   covered is also more likely to be picked up by later US catalogues. The +1.65
   association is not evidence that catalogues verify anything. It may only mean
   the catalogues drew on these same bulletins.
5. **Tokens are machine-extracted** from the `named_case` and `location` fields,
   with country-only and generic words removed. 93 events have no usable token,
   and they're excluded, not counted as absent.
