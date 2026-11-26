# The 37 AAWSAP DIRDs, one area each

*Project Omega, session 5, 2026-11-26. Closes handoff §5 item 1. Script:
`omega/dird_area_assignment.py`. Data:
`evidence_vault/01_PURSUE_PRIMARY/dird_area_assignment.json`. Replaces the
title-keyword area map in `aawsap_contract_audit.md` §7. That map stays flagged
as not for quoting.*

---

## Bottom line

- **The old map was inflated 1.41×.** It filled 52 area slots for 37 reports.
- **One area per report is not cleanly possible for 20 of the 37.** Their own
  statements of purpose support two areas. I give a primary and an alternate
  for each, and report every count as a primary value plus the range it can
  reach when contested reports flip.
- **Nine of the twelve contracted areas are covered whichever way the contested
  reports flip.** Those are propulsion, power generation, spatial/temporal
  translation, materials, signature reduction, human interface, human effects,
  armament, and "other peripheral".
- **Lift, control and configuration/structure each rest on one contested
  report.** Flip it and the area has none. So the audit's §7 sentence, "no
  contracted area went undelivered", is **withdrawn as a firm claim**. It is
  true under my primary reading and false under an equally defensible one.
- **In FY2009, control has no report at all under the primary reading.** The
  only control report is D151, from FY2010.
- **Propulsion dominates under the primary reading**, with 11 of 37. The
  contract design implies one report per area per year (CLIN 0003/1003,
  "Research Report for Tasks 3.a.1 – 3.a.12", quantity 12). Under that uniform
  null, a cell of 11 or more has P = 0.0019 (Monte Carlo, 10⁵ draws,
  look-elsewhere included), and the overall χ² is 32.1, P = 0.0012. **But if
  every contested propulsion report flips away, propulsion falls to 4, which is
  indistinguishable from uniform** (binomial P = 0.37). So the concentration is
  real under one reading and not robust across readings. Don't quote it without
  that caveat.

## Area list used

This is the SOO itself, **D110 §3(a), 18 July 2008**, which is readable. D182's
copy of the same list is OCR-destroyed, which is why session 4 fell back on
D188's restatement.

> 1. lift 2. propulsion 3. control 4. power generation 5. spatial/temporal
> translation 6. materials 7. configuration, structure 8. signature reduction
> (optical, infrared, radiofrequency, acoustic) 9. human interface 10. human
> effects 11. annamcnt (RF and DE\V) 12. other peripheral area,:; in support
> of(1-11)

D186 p.1 (Director DIA to USD(AT&L), Dec 2010) lists the same twelve, with
area 12 renamed **"technology integration"**.

## Method

1. **Primary area** is read from each report's own statement of purpose (its
   Summary, Introduction, Preface or explicit scope sentence), not from its
   title. D124 shows why this matters. Its title is *Space Access*, but its own
   text says "The remainder of this report will focus on the characteristics of
   this class of lifting body". So it is a configuration report, not a
   propulsion one.
2. **Every assignment carries the framing sentence it rests on, and the script
   checks that each sentence is in the vaulted text.** 37 of 37 verified. A
   missing string makes the script exit non-zero.
3. **Alternate area.** Where the framing supports two areas, the second is
   recorded. Counts are given as primary plus [min, max] under flips.
4. **Rater B**, a mechanical check independent of my reading. It takes the
   argmax of session 4's area regexes over each report's first 15,000
   characters of body text.

## Result

| area (D110 §3(a)) | primary | range under flips | FY2009 | FY2010 |
|---|---|---|---|---|
| lift | 1 | [0, 4] | 1 | 0 |
| propulsion | **11** | [4, 14] | 5 | 6 |
| control | 1 | **[0, 3]** | **0** | 1 |
| power generation | 3 | [2, 4] | 2 | 1 |
| spatial/temporal translation | 1 | [1, 5] | 1 | 0 |
| materials | 5 | [2, 6] | 5 | 0 |
| configuration, structure | 1 | **[0, 2]** | 1 | 0 |
| signature reduction | 2 | [1, 3] | 1 | 1 |
| human interface | 3 | [1, 5] | 2 | 1 |
| human effects | 1 | [1, 2] | 1 | 0 |
| armament | 2 | [2, 2] | 2 | 0 |
| other peripheral / technology integration | 6 | [3, 7] | 5 | 1 |

Primary and alternate for each report, with the framing string, are in the
JSON. The contested 20 are D119, D120, D124, D125, D126, D129, D131, D132, D133,
D135, D136, D138, D141, D143, D144, D148, D149, D150, D151 and D153.

**The pattern in the contested set is itself informative.** Seven of the 20 sit
on the propulsion / spatial-temporal / lift boundary (D131, D132, D135, D138,
D143, D149, D153). The contract's twelve-area scheme separates "propulsion",
"lift" and "spatial/temporal translation", but the authors treat warp,
wormhole and antigravity work as one subject. That's a property of the
taxonomy, not of my reading.

## Agreement with the mechanical rater

| | value |
|---|---|
| exact agreement, reading vs rater B | 0.568 (21/37) |
| Cohen's κ | **0.517**, 95% bootstrap CI 0.343–0.687 (10⁴ resamples over reports) |
| agreement if rater B may hit primary or alternate | 0.703 (26/37) |

7 of the 11 hard disagreements are rater B calling a report **power
generation** (D121, D145, D146, D148, D149, D150, D153). Every one is the
`power|energy` regex firing on body text about the energy a propulsion or
weapon system needs. That is the same failure that inflated session 4's title
map ("power generation: 11"). κ ≈ 0.5 is moderate. It says the reading can't
be reproduced by keyword counting, which is the reason the reading was needed.
It doesn't validate the reading.

## Red team

1. **One reader.** Every primary was chosen by one reader, me. κ against a
   keyword rule is not inter-rater reliability. A second, blind human or model
   reader using only the framing sentences is the real test. Expect κ well
   below 1 on the 20 contested reports. The ranges are meant to absorb that.
2. **The ranges are extreme bounds.** They assume every contested report flips
   the same way at once. The realistic spread is narrower. I report bounds
   rather than a made-up probability per flip.
3. **"Framing sentence" is a choice.** Several reports open with history
   before stating scope (D124, D145). I took the explicit scope statement where
   one exists, and the opening summary otherwise. Another reader could pick a
   different sentence.
4. **The uniform null is contract-grounded but not exact.** CLIN 0003 is
   quantity 12 for the year, yet FY2009 delivered 26 reports. So DIA did not
   enforce one report per area. The null tests "was the contract's stated
   design followed", and it isn't a model of how authors were recruited.
5. **D186 says 12 FY2010 reports, but the release has 11.** If the missing one
   exists, every FY2010 column could change by one. See the audit addendum.

## What this changes in the audit

`aawsap_contract_audit.md` §7's qualitative claim, "no contracted area went
undelivered", becomes this: **nine of twelve areas are covered under every
reading. Lift, control and configuration/structure each rest on one report
whose own framing also supports another area. Control has no FY2009 report.**
The per-area counts in `aawsap_contract_audit.json` stay unquotable. Use this
table instead, with its ranges.
