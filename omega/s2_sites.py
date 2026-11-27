#!/usr/bin/env python3
"""Site list + Sentinel-2 scene picker for the session-7 water-mode survey.

Water mode only detects aircraft over open water, so the testable sites are
those with open water within 10 km. Coordinates are HAND-ENTERED (approximate,
~1 km) except the French reactors, which come from the PRIS/WNA layer.
Category tags drive the comparison; every site is compared with 30 random
disks in the same 60 km window of the same scene (same instant, same weather).
"""
import csv, json, os, sys, time, urllib.request, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAC = "https://earth-search.aws.element84.com/v1/search"
UA = "omega-research/1.0 (academic UAP data study; non-commercial)"

SITES = [
 # (label, category, lat, lon, why)
 ("Nimitz 2004 'Tic Tac' area", "uap_encounter", 31.30, -117.60, "USS Nimitz CSG encounter area SW of San Diego (approx)"),
 ("W-72 warning area (Roosevelt 2014-15)", "uap_encounter", 36.70, -75.30, "Navy pilots' 'Gimbal/GoFast' training area off Virginia (approx)"),
 ("Aguadilla 2013", "uap_encounter", 18.50, -67.15, "CBP thermal video, NW Puerto Rico coast"),
 ("Catalina channel", "uap_encounter", 33.45, -118.40, "frequent USO/UAP claims; Navy SCORE range nearby"),
 ("Shag Harbour 1967", "uap_encounter", 43.50, -65.72, "RCMP-documented water-entry case, Nova Scotia"),
 ("Lake Michigan 1994/2008", "uap_encounter", 42.40, -87.10, "mass-sighting claims over the lake (approx)"),
 ("Flamanville NPP", "nuclear", 49.536, -1.881, "PRIS"),
 ("Gravelines NPP", "nuclear", 51.015, 2.136, "PRIS"),
 ("Paluel NPP", "nuclear", 49.858, 0.636, "PRIS"),
 ("Penly NPP", "nuclear", 49.977, 1.212, "PRIS"),
 ("Blayais NPP", "nuclear", 45.256, -0.691, "PRIS (Gironde estuary)"),
 ("La Hague reprocessing", "nuclear", 49.678, -1.879, "hand-entered"),
 ("San Onofre NPP (closed)", "nuclear", 33.369, -117.555, "hand-entered"),
 ("Diablo Canyon NPP", "nuclear", 35.211, -120.856, "hand-entered"),
 ("Kings Bay SSBN base", "military", 30.80, -81.52, "hand-entered"),
 ("Naval Base Kitsap-Bangor", "military", 47.72, -122.72, "hand-entered (Hood Canal)"),
 ("Vandenberg SFB coast", "military", 34.74, -120.62, "hand-entered"),
 ("Point Mugu range", "military", 34.10, -119.12, "hand-entered"),
 ("Lockheed Martin Fort Worth", "contractor", 32.77, -97.44, "Eagle Mtn Lake/Lake Worth nearby"),
 ("Boeing Field Seattle", "contractor", 47.53, -122.30, "Elliott Bay/Lake Washington nearby"),
 ("Bermuda", "lore", 32.30, -64.78, "'Triangle' lore"),
 ("Lake Titicaca", "sacred", -15.90, -69.30, "Andean sacred lake"),
 ("Lake Tahoe", "lore", 39.10, -120.03, "frequent lake-UAP claims (control-ish)"),
 ("Hessdalen valley", "lore", 62.79, 11.19, "Hessdalen lights (small lakes only)"),
]


def search(lat, lon, years=range(2019, 2026), per_year=1, cloud=5):
    out = []
    for y in years:
        body = {"collections": ["sentinel-2-l2a"], "intersects": {"type": "Point", "coordinates": [lon, lat]},
                "datetime": f"{y}-04-01T00:00:00Z/{y}-09-30T23:59:59Z" if lat > -10 else f"{y}-01-01T00:00:00Z/{y}-12-31T23:59:59Z",
                "query": {"eo:cloud_cover": {"lt": cloud}}, "limit": 40, "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}]}
        for k in range(4):
            try:
                rq = urllib.request.Request(STAC, json.dumps(body).encode(), {"Content-Type": "application/json", "User-Agent": UA})
                feats = json.load(urllib.request.urlopen(rq, timeout=60))["features"]; break
            except Exception:
                time.sleep(3 * (k + 1)); feats = []
        seen = set()
        for f in feats:
            day = f["id"].split("_")[2]
            if day in seen:
                continue
            seen.add(day); a = f["assets"]
            out.append(dict(scene=f["id"], cloud=f["properties"]["eo:cloud_cover"],
                            assets={"B02": a["blue"]["href"], "B03": a["green"]["href"], "B04": a["red"]["href"],
                                    "B08": a["nir"]["href"], "scl": a["scl"]["href"]}))
            if len(seen) >= per_year:
                break
    return out


if __name__ == "__main__":
    jobs = []
    for lab, cat, la, lo, why in SITES:
        for s in search(la, lo):
            jobs.append(dict(job_id=f"S|{lab}|{s['scene']}", kind="site", category=cat, label=lab,
                             lat=la, lon=lo, why=why, **s))
        print(lab, sum(j["label"] == lab for j in jobs), flush=True)
    json.dump(jobs, open(sys.argv[1], "w"))
    print("jobs", len(jobs))
