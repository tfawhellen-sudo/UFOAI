"""Convert the GEIPAN bulk export (data/raw/geipan/geipan_cases.json) into the
ufo_data catalog schema, so ufo_data / ufo_data_search tooling can ingest it.

Output: <ufo_data>/bin/geipan.json  ({"GEIPAN": [ {date, location, desc, type,
ref, source_id, source, key_vals{LatLong, Country, GEIPANClass, ...}} ]})

Records are transcribed field-for-field from the official export. Nothing is
inferred except the date string format (dd/mm/yyyy -> m/d/yyyy, '--' -> dropped).
"""
import json, re, sys, os

SRC = "data/raw/geipan/geipan_cases.json"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/user/ufo_data/bin/geipan.json"


def ufo_date(s):
    m = re.fullmatch(r"(\S\S)/(\S\S)/(\S{4})", s.strip())
    if not m: return s
    d, mo, y = m.groups()
    if not y.isdigit(): return y.replace("-", "0")[:3] + "0"   # '197-' -> decade only
    if not mo.isdigit(): return y
    if not d.isdigit(): return f"{int(mo)}/{y}"
    return f"{int(mo)}/{int(d)}/{y}"


def main():
    cases = json.load(open(SRC, encoding="utf-8-sig"))
    out = []
    for c in cases:
        cid = c["ID Etude de Cas"]
        out.append({
            "date": ufo_date(c["Observation date"]),
            "location": f'{c["Titre du Cas"].split(" (")[0].title()}, {c["Department"]}, France',
            "desc": c["Détails"],
            "type": "ufo sighting",
            "ref": f"[GEIPAN case {cid}](https://www.geipan.fr/fr/cas/{cid})",
            "source_id": f"GEIPAN_{cid}",
            "source": "GEIPAN",
            "key_vals": {
                "LatLong": f'{c["Latitude"]} {c["Longitude"]}',
                "Country": "France",
                "GEIPANClass": c["Classification"],
                "GEIPANPhenomenon": c["Phenomenon"],
                "GEIPANIdentification": c["Identification"],
                "Region": c["Region"],
                "CaseType": c["Type de cas"],
            },
        })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"GEIPAN": out}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {len(out)} records -> {OUT}")


if __name__ == "__main__":
    main()
