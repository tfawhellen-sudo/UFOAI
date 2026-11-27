# omega/deeptime: 2,000-year descriptor drift, technology tracking, description tree

Report: `omega/reports/deep_time_drift.md`; every number: `omega/reports/deep_time_tables.md`;
figures: `omega/reports/figures/deeptime_*.png`; result JSONs: `evidence_vault/13_DEEP_TIME/`.

Run from the repo root with `../ufo_data` checked out beside it (Python 3.13; numpy, scipy, statsmodels, matplotlib).

| step | command | what it does | time |
|---|---|---|---|
| 0 | `python3 -I omega/taxonomy/features.py` | craft-taxonomy records (NUFORC, GEIPAN) the corpus reuses | 30 s |
| 1 | put the Obsequens text in `data/raw/deeptime/` (see `evidence_vault/13_DEEP_TIME/FETCH_MANIFEST.md`) | primary-text control | - |
| 2 | `python3 -I omega/deeptime/corpus.py` | 10 catalogs (all years) + Obsequens + NUFORC + GEIPAN, coded; same-event linking | 40 s |
| 3 | `python3 -I omega/deeptime/drift.py` | Task 2.1: ORs, standardised prevalence, era boundaries, compiler agreement, LLM check | 20 s |
| 4 | `python3 -I omega/deeptime/tech.py` | Task 2.3: technology change points, shapes by decade, newest-vehicle share, invariance, AA1-AA5 | 15 s |
| 5 | `python3 -I omega/deeptime/tree.py` | Task -3.1: NJ tree, bootstrap, Blomberg's K, MRM, delta score, tree figure | 90 s |
| 6 | `python3 -I omega/deeptime/figures.py` then `report.py` | remaining figures; tables file | 60 s |

`lexicon.py` holds every regex (physical descriptors are imported unchanged from `omega/taxonomy/features.py`).
Outputs go to `data/processed/deeptime/` (gitignored) and are copied to `evidence_vault/13_DEEP_TIME/`.
