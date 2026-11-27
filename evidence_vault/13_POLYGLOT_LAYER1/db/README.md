# Layer 1 bilingual database

Built by `omega/layer1/build_db.py` (run `python3 -I omega/layer1/build_db.py` from the repo root). The same five tables are in `layer1_polyglot.sqlite` and as CSV files.

| Table | Rows | What it holds |
|---|---|---|
| `events` | 640 | 624 Russian chronicle entries (`RU_CH`), 10 Soviet state-programme episodes (`PLATOV2000`), 6 dated Chinese cases from the 1980 Ziran Zazhi survey (`JPRS77236`) |
| `links` | 60 | event to Hatch entry, and Platov episode to chronicle entry, with day offset and distance |
| `lexicon` | 30 | UAP vocabulary in Russian, Chinese, Arabic and Sanskrit, with origin notes and counts in the corpora on disk |
| `claims` | 16 | the Abyss Protocol's Layer 1 claims, each with a verdict and the evidence |
| `sources` | 15 | every corpus and document used, with host, identifier and how it was read |

## Event fields

- `text_orig` is a 300-character excerpt of the Russian entry. The chronicle (Chernobrov, Kosmopoisk, 2002) is a copyrighted compilation, and full texts would republish about 90% of it. `text_orig_chars` gives the full length and `src_offset` gives the entry's character offset in the archive.org OCR file `hroniki_vizitov_nlo`. A full-text copy can be built locally with `L1_EXCERPT=0 L1_DB_OUT=data/raw/layer1/db_full` (gitignored).
- `text_en` is an English gist of the first ~160 characters of each ex-USSR entry (419 rows). It is a machine translation by Claude and has not been reviewed by a Russian speaker. Witness names of private persons are replaced by roles. The other 205 entries (156 foreign, 49 unplaced) have no English gist.
- `primary_shape`, `plume_flag` and `flags` are computed from the full Russian text at build time.
  - `primary_shape` is the class of the first shape word, as in test T3b.
  - `plume_flag` uses the T5 plume vocabulary (jellyfish, crescent, spiral, fan, halo, cloud, plume and similar words).
- `launch_utc_same_day` and `launch_utc_prev_day` list Soviet and Russian orbital launches in SATCAT on the report's date and the day before. Report dates are local; launch dates are UTC. Suborbital missile tests are not in SATCAT.
- `nuclear_km` and `nuclear_site` give the nearest nuclear site that existed in the report's year (time-aware site list from T4). Closed weapons cities are mostly missing from the gazetteer.
- `hatch_links` counts Hatch entries in the same country group within ±1 day and within 800 km. Where either side has no coordinates, the date alone is used. Expect chance links: about 8% of the chronicle's day-dated entries match Hatch on date alone, and about 2% on date plus 800 km, when the dates are shifted (T2).
- `flags` are heuristic regex flags. Check them before relying on them.
  - `parser_merge`: the entry's body includes the next chronicle entry, because the header could not be split.
  - `compiler_witness`: V. Chernobrov, the compiler, is named as a witness.
  - `duplicate_of`: the same text appears in an earlier entry.
  - `aircrew`, `radar` and `cosmonaut_word`: the matching words occur in the text.

## Known limits

- Geocoding works at city level at best. `geo_how` records the method: exact, alias, stem, region capital or district centre.
- The chronicle is Kosmopoisk's own archive as of 2 September 2002. It misses major events, for example the Kosmos-1188 mass sighting of 14 June 1980 that Platov & Sokolov describe.
- The Chinese rows are FBIS English translations. The Chinese originals are not on file, and archive.org's OCR of the Chinese books is mostly unusable, so the Chinese lexicon counts are floors.
- Arabic counts use NFKC-normalised text, because the OCR mixes Persian and Arabic letter forms.
