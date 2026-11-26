# 12_CRAFT_TAXONOMY — fetch manifest

Everything the craft-taxonomy study (`omega/reports/craft_taxonomy.md`, code `omega/taxonomy/`)
downloaded, with the honest UA `omega-research/1.0 (academic UAP data study; non-commercial)`.
Raw downloads live in `data/raw/taxo_geo/` (gitignored). The SHA-1s pin the copies used, because the
upstream files are moving `main`/`master` paths.

| file | URL | bytes | SHA-1 | licence |
|---|---|---|---|---|
| `airports.csv` | https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv | 12,764,821 | 132525b5c0230c1ca402e9dec61f898775df4b1c | public domain (OurAirports) |
| `nuclear_power_plants.csv` | https://raw.githubusercontent.com/cristianst85/GeoNuclearData/master/data/csv/denormalized/nuclear_power_plants.csv | 108,458 | 760bcbe0f8f1208411414d0cea8d2ba1c18e3218 | ODbL (GeoNuclearData; WNA / IAEA PRIS derived) |
| `ne_10m_coastline.geojson` | https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_coastline.geojson | 10,110,735 | 8755f67032f04942dcf114f9830fb0581d843636 | public domain (Natural Earth) |

Streamed, not stored:

- **Population**: Meta / CIESIN High Resolution Settlement Layer, US total population, 2019 release
  (CC BY 4.0): `https://dataforgood-fb-data.s3.amazonaws.com/csv/month=2019-06/country=USA/type=total_population/USA_total_population.csv.gz`
  (961,907,956 bytes, tab-separated 30 m points). `pop_grid.py usa` bins it to `pop_usa_005.npz`.
  Do **not** use the `hrsl-cogs` overviews for this: they average settled pixels only and inflate sparse
  cells about 3,000 times.
- **Terrain**: Copernicus GLO-90 DEM COGs, `https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_{N|S}{lat}_00_{E|W}{lon}_00_DEM/...tif`,
  only 1° tiles that hold population; ocean tiles don't exist upstream. `dem_grid.py` writes `dem_usa_005.npz`.

Inputs already in the project (not re-fetched): `evidence_vault/06_NUFORC_MODERN_ARM/nuforc_unified.json.gz`,
`data/raw/geipan/geipan_cases.json`, and the sibling checkout `ufo_data/bin/hatch_udb.json`
(Larry Hatch *U* database; the ufo_data README records verbal permission from his family).

## Contents of this folder (derived; all rebuildable with `omega/taxonomy/README.md`)

| file | what it is | SHA-1 |
|---|---|---|
| `selectk_{HATCH,NUFORC,GEIPAN}.json` | number-of-classes runs (BIC, half-split replication per K) | db5c1e556350d00c6e404ff360b4778371b35984 / 1192cda8b327e98df9663f62f9f8b6a93e1c36d5 / bcc4298453a0c7043a8b58634fca6379331feb46 |
| `stability.json` | final models (class profiles, shares, labels), stability per subset, cross-source matching | f5373e7c87fb79840f269906040e647d402ae9ef |
| `stability_diag.json` | NUFORC US East vs rest, K = 5 side by side (post-hoc) | ede728ea60a3ebd30c5896f4865a49c612cf7b00 |
| `assign.json.gz` | class of every report, by source and report uid | c5dc963b545c30b696c21908396ad9f83d371f69 |
| `drift.json` | pop-culture and control tests, yearly tables, GEIPAN lantern counts | 756bf6383c4446a376db686acd83408a8279ac7b |
| `geo.json` | US per-person rate ratios (0.05° and 0.25°), per class; Hatch world; GEIPAN France | 19ce7c9127db9a3be4ff59d5d9767ee1395579ae |
| `geipan_d_vs_ab.json` | GEIPAN unexplained vs explained: features, AUC, explanations by shape | dffbabba7d4ec4cdac8dd6f74fd14f420841a2c6 |
| `stimuli.json` | what each class contains (GEIPAN explanations, Hatch flags, NUFORC mentions; GEIPAN by era) | 9a2ceafa830cd408aebe20807f767f2b5729644c |
| `pop_usa_005.npz` | HRSL 2019 people per 0.05° cell, US (grid, lat0, lon0, res) | 7388e5a488320172b2ee89bbd3d5ab11fbc666c1 |
| `dem_usa_005.npz` | Copernicus GLO-90 mean elevation and relief per 0.05° cell, populated US tiles | c0bc66fc390439452ae384166a03c5c25ca132d1 |

`records.json.gz` (the coded reports, 10 MB) is not stored: `features.py` rebuilds it in 30 seconds from
inputs already in the project.
