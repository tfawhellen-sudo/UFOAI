# omega/taxonomy — data-driven UAP craft taxonomy and its geography

Report: `omega/reports/craft_taxonomy.md` (narrative) and `omega/reports/craft_taxonomy_tables.md`
(every number, generated). Figures: `omega/reports/figures/`.

## Run order (from the repo root, Python 3.13; needs numpy, scipy, pandas, statsmodels,
## scikit-learn, rasterio, matplotlib)

| step | command | what it does | time (4 cores) |
|---|---|---|---|
| 1 | `python3 -I omega/taxonomy/features.py` | code 33 features for NUFORC + Hatch + GEIPAN | 30 s |
| 2 | `python3 -I omega/taxonomy/pop_grid.py usa` | stream Meta HRSL US population to a 0.05° grid | 3 min, ~1 GB download |
| 3 | `python3 -I omega/taxonomy/dem_grid.py` | Copernicus GLO-90 elevation/relief on the same grid | 2 min |
| 4 | download the three site files into `data/raw/taxo_geo/` (URLs in `sites.py`, SHA-1s in `evidence_vault/12_CRAFT_TAXONOMY/FETCH_MANIFEST.md`) | airports, reactors, coastline | seconds |
| 5 | `python3 -I omega/taxonomy/select_k.py SRC KMAX KMIN` for GEIPAN (7 2), HATCH (9 2), NUFORC (9 2) | number of classes | 5 / 25 / 60 min |
| 6 | `python3 -I omega/taxonomy/stability.py SRC` for each source, then `stability.py merge`, then `stability.py diag` | final classes, stability, cross-source match; the NUFORC US East diagnostic | 1 / 15 / 12 min with `TAXO_WORKERS=3` |
| 7 | `python3 -I omega/taxonomy/drift.py` | pop-culture milestone tests with physical controls | 1 min |
| 8 | `python3 -I omega/taxonomy/geo.py` (`geo.py hatch` redoes only the Hatch and GEIPAN parts) | population-null geography | 5 min |
| 9 | `python3 -I omega/taxonomy/stimuli.py` and `stimuli.py dvsab` | what the classes contain; GEIPAN D vs A/B; GEIPAN by era | 3 min |
| 10 | `python3 -I omega/taxonomy/figures.py` then `report.py` | figures and the tables file | 1 min |

Hatch is read from the sibling checkout `../ufo_data/bin/hatch_udb.json` (override with `OMEGA_HATCH`).
`Hatch` = Larry Hatch's *U* database (18,116 cases). The ufo_data README records that his family gave verbal
permission for its use; used here non-commercially.

Set `OMP_NUM_THREADS` when running several steps at once; the EM is BLAS-bound.
Outputs go to `data/processed/taxonomy/` (gitignored; everything there is rebuildable from the steps above).
The result files, class assignments and the two US grids are also copied to `evidence_vault/12_CRAFT_TAXONOMY/`.
