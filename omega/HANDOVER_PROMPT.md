# HANDOVER PROMPT — paste this into the next session

---

Continue PROJECT OMEGA. Read `/home/user/UFOAI/omega/HANDOFF.md` first — it has
the full state, the standing constraints, every established result so you don't
re-derive them, and the operational lessons in §1.13, §1.15 and §1.17 that have
each already cost this project real time.

**Branch:** `claude/nice-ritchie-j1ve90` in `tfawhellen-sudo/UFOAI` — the
**consolidated** line, and the only branch holding all of sessions 1–5. Working
tree was clean; nothing was in flight.

## Restore first (3 minutes)

1. **Check for sibling branches BEFORE anything else.** This is new, and it is
   the lesson of session 5:

   ```
   git ls-remote --heads origin
   ```

   Session 5 ran as **three sessions at once off the same tip**, none aware of the
   others. Nothing was lost only because they touched disjoint files. **Any
   `claude/*` branch carrying commits the consolidated line lacks is session work
   this handoff does not know about** — read its reports before trusting §1, merge
   it `--no-ff`, and rewrite §1 and §6 before doing new analysis. Two of the three
   session-5 threads *modified* session 4's conclusions. §2 has the procedure.

   Superseded, do not branch from and do not read their copies of HANDOFF.md:
   `claude/gallant-lamport-0tu52r`, `claude/magical-gauss-wzgdqd`,
   `claude/project-thread-noala8`, `claude/project-thread-het5pi`,
   `claude/project-thread-eck2kl`.

2. `git fetch origin claude/nice-ritchie-j1ve90 && git checkout claude/nice-ritchie-j1ve90`
   (If your assigned development branch differs, **fast-forward it to this tip**
   rather than branching from `main`. Sessions 4 and 5 both did exactly that.)

3. **The environment is settled. Do not re-litigate it.** `UFOAI Omega research`
   (`env_018sxdcbBHMGqCRwh6KXDi6D`) and its setup script were verified working in
   sessions 4 and 5 — tesseract 5.3.4 + `fra`, poppler 24.02, scipy, sklearn,
   installed ~2 min after boot. A one-line sanity check is fine; a re-verification
   campaign is waste. §4 lists what is blocked and the two hosts worth asking the
   user for.

4. **Almost nothing needs re-fetching.** `evidence_vault/` holds the 860
   periodical texts, the 286 PURSUE server-OCR texts, the 37 DIRD texts, the TEP
   dossier plus its page-by-page OCR, the trace controls, NUFORC unified, the
   seed-stability sweeps, the redaction slot analysis, the contract audit, the
   DIRD area assignment and the GEIPAN Phase 1–3 output. §3 lists the handful of
   ephemeral items and what each costs.

   **One gotcha:** `omega/redaction_slots.py` and `omega/aawsap_contract_audit.py`
   read the PURSUE texts from `$OMEGA_PURSUE_TXT`. Untar
   `evidence_vault/01_PURSUE_PRIMARY/pursue_server_ocr_286.tar.gz` into a scratch
   directory and point that variable at the `djvu/` folder inside it.

## What session 5 did, so you don't redo it

Three threads, all merged, all in §1.16:

- **§5 item 1 is CLOSED and it withdrew a claim.** The 37 DIRDs now have one area
  each, read from each report's own framing (37/37 framing strings verified
  against the vaulted text). Session 4's keyword map was inflated 1.41×. **"No
  contracted area went undelivered" is withdrawn as a firm claim** — nine of
  twelve areas hold under every reading; lift, control and configuration each
  rest on one contested report; control has no FY2009 report. κ=0.517 against a
  keyword rater, which says the reading can't be reproduced by keywords, not that
  it's right.
- **FOIA Letter 14 is drafted** (Integrated Threat Assessment, CLIN 0004/1004,
  contract HHM402-08-C-0072). **Drafted, not filed.** Drafting it produced seven
  corrections, two of which matter: **D182 is the solicitation, not the Statement
  of Objectives — that is D110**; and **two due conditions were reached, not one**
  (30 Sep 2009 as well as 21 Dec 2010). Plus: BAASS called a threat assessment
  *future work* on 23 Nov 2010, which fits "never produced" at least as well as
  "withheld", and **DIA says twelve FY2010 reports were delivered where the
  release holds eleven.**
- **NT-16 replicated end to end.** The biochemistry reproduces (9/11 correlations
  to ±0.01) and the distance gradient survives every available null at the
  design's floor, **P=0.0028**. But NT-16's P-values are one-sided and one is 50×
  too small; the chlorophyll losses don't clear analytical noise; **the soil
  mass-spec's two plates of the same soil disagree by a median factor of 23**, so
  the "rubbed paint" reading is not a reproducible measurement. Eight corrections
  to our own earlier records, worst being a telex mark width of **10 cm** that we
  had written as 14 cm — manufacturing a discrepancy that does not exist.
- **GEIPAN Phases 1–3 re-run on the state file.** Nuclear proximity **null
  again, independently** (12/12 statistics). Descriptor drift replicated and it
  **survives inside the unexplained subset**. Third independent confirmation of
  the D-collapse (OR 0.69/decade, p=8e-12). And: the enthusiast literature holds
  only 2.1% of the state file's French events while over-sampling its unexplained
  cases ~4× within a decade.

## Run this next — §5 item 1

**Re-run GEIPAN Phase 2 against an authoritative nuclear-site layer.** The
28-site layer was **hand-entered from general knowledge** (±1–3 km, ±1 yr; only 4
of 28 cross-checked) because Wikidata and ASN were unreachable in that thread.
The report flags itself as not quotable — which is correct behaviour and is still
a debt. §1.4's seed debt sat unpaid for three sessions and paying it changed the
published number.

**`query.wikidata.org` IS on the environment allowlist**, so use it, with the
`p:P625/psv:P625` statement-node construct from §1.11 (`wdt:P625` returns only
truthy statements and misses sites) and `FILTER(LANG(?l) IN ("en","mul"))`.
Re-run, then either confirm the twelve nulls or report what changed.

Then §5 item 2: **confirm the two OCR-only session-5 claims on the page images** —
D186's "Twelve additional reports were produced and delivered" against a release
holding eleven, and D186's twelve-area list. If the first holds, one FY2010 DIRD
is unaccounted for, which is a third nameable gap alongside D66–D73 and the
capstone.

## Standing constraints — carry verbatim

Public/FOIA/declassified data only. No UA spoofing, no routing around proxy
blocks; reading `robots.txt` to respect it is in scope, fetching what it
disallows is not. Negatives reported as negatives. FOIA and CADA letters
**drafted, not filed**. No noise with physics words attached. If a test comes
back null, say so plainly and move on. **Do not resolve the release's author
pseudonyms to real people** — that numbering was applied under the (b)(6) privacy
exemption, and session 4 declined to defeat it after finding it could.

## Habits that keep paying off — keep them

1. **When a tool reports something surprising, check the tool before acting on
   the report.** Session 4's tally was four instruments wrong in one session;
   session 5 added a fifth — an exact-match regex returned "4 hits" because the
   page actually reads `Asscsmient`.
2. **Verify a background job by process state and output mtime**, never by the
   harness's "completed, exit 0". To block: `until [ ! -d /proc/<pid> ]; do sleep 5; done`.
3. **`OMP_THREAD_LIMIT=1`** for tesseract. 15×, byte-identical.
4. **A single seed is not a point estimate.** Sweep it, report the mean and
   spread, and say which seeds exist before claiming one was swept.
5. **Hand-entered reference data is a debt the moment it is used.** Log it in §5
   or it becomes a quoted number.
6. **Never read a catalogue against itself.** Make the exclusion explicit, in
   code, with a comment — `geipan_to_ufo_data.py` is the model.
7. **Report bounds, not invented probabilities**, when a judgement is genuinely
   contested.
8. **Store the sentence a judgement rests on**, and make the script fail if it
   is not in the source text. That is what makes a reading auditable later.
