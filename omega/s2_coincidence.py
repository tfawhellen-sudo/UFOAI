#!/usr/bin/env python3
"""Find UAP reports made while Sentinel-2 was overhead (session 7).

For every NUFORC (2017-03+, after Sentinel-2B) and GEIPAN (2017+) report with a
clock time and a geocode, convert the local time to UTC, ask Earth Search for
Sentinel-2 L2A scenes over the point on that date, and keep the report if a
scene was acquired within +-WIN minutes of the reported time.

Report clock times are witness estimates, often rounded to the hour. WIN = 30
min is generous on purpose; a looser window only adds pairs, and every pair is
tested against its own scene's random boxes, so loose pairs dilute, not bias.

Writes evidence_vault/08_SATELLITE_ANOMALIES/s2_coincidence_pairs.json
"""
import datetime as dt, gzip, json, os, re, sys, time, urllib.request
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "evidence_vault/08_SATELLITE_ANOMALIES/s2_coincidence_pairs.json")
STAC = "https://earth-search.aws.element84.com/v1/search"
UA = "omega-research/1.0 (academic UAP data study; non-commercial)"
WIN = 30
TF = TimezoneFinder()


def reports():
    d = json.load(gzip.open(os.path.join(ROOT, "evidence_vault/06_NUFORC_MODERN_ARM/nuforc_unified.json.gz")))["nuforc"]
    for r in d:
        if r.get("lat") is None or not r.get("year") or (r["year"], r["month"] or 0) < (2017, 3):
            continue
        m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2}):(\d\d)", r.get("date_raw", ""))
        if not m:
            continue
        mo, da, yr, hh, mi = map(int, m.groups())
        yr = yr + 2000 if yr < 100 else yr
        if not 8 <= hh <= 15:          # S2 overpass is ~10:30 solar; clock 9-14 incl. DST
            continue
        yield dict(uid=r["uid"], cat="NUFORC", lat=r["lat"], lon=r["lon"], y=yr, mo=mo, d=da, hh=hh, mi=mi,
                   loc=r.get("location"), desc=(r.get("desc") or "")[:600], shape=r.get("etype"),
                   duration=r.get("duration"))
    g = json.load(open(os.path.join(ROOT, "data/raw/geipan/geipan_cases.json")))
    for r in g:
        if (r.get("Année") or 0) < 2017 or not r.get("Latitude"):
            continue
        m = re.match(r"(\d\d)/(\d\d)/(\d{4})", r.get("Observation date") or "")
        t = re.search(r"\b(?:à|a|vers|entre)\s+(\d{1,2})\s?h\s?(\d{2})?", r.get("Détails") or "")
        if not m or not t:
            continue
        hh = int(t.group(1)); mi = int(t.group(2) or 0)
        if not 8 <= hh <= 15:
            continue
        try:
            lat, lon = float(str(r["Latitude"]).replace(",", ".")), float(str(r["Longitude"]).replace(",", "."))
        except ValueError:
            continue
        yield dict(uid="GEIPAN#" + r["ID Etude de Cas"], cat="GEIPAN", lat=lat, lon=lon, y=int(m.group(3)),
                   mo=int(m.group(2)), d=int(m.group(1)), hh=hh, mi=mi, loc=r.get("Titre du Cas"),
                   desc=(r.get("Détails") or "")[:600], shape=r.get("Phenomenon"), cls=r.get("Classification"))


def stac(lat, lon, day):
    body = {"collections": ["sentinel-2-l2a"], "intersects": {"type": "Point", "coordinates": [lon, lat]},
            "datetime": f"{day}T00:00:00Z/{day}T23:59:59Z", "limit": 10}
    for k in range(4):
        try:
            rq = urllib.request.Request(STAC, json.dumps(body).encode(), {"Content-Type": "application/json", "User-Agent": UA})
            return json.load(urllib.request.urlopen(rq, timeout=60))["features"]
        except Exception as e:
            time.sleep(2 * (k + 1))
    return None


def main():
    R = list(reports())
    print("candidate reports", len(R), flush=True)
    pairs, nq, nfail = [], 0, 0
    for r in R:
        tzn = TF.timezone_at(lat=r["lat"], lng=r["lon"])
        if not tzn:
            continue
        try:
            loc = dt.datetime(r["y"], r["mo"], r["d"], r["hh"], r["mi"], tzinfo=ZoneInfo(tzn))
        except ValueError:
            continue
        utc = loc.astimezone(dt.timezone.utc)
        feats = stac(r["lat"], r["lon"], utc.date().isoformat()); nq += 1
        if feats is None:
            nfail += 1; continue
        for f in feats:
            st = dt.datetime.fromisoformat(f["properties"]["datetime"].replace("Z", "+00:00"))
            gap = (st - utc).total_seconds() / 60
            if abs(gap) <= WIN:
                a = f["assets"]
                pairs.append(dict(r, tz=tzn, utc=utc.isoformat(), scene=f["id"], scene_utc=st.isoformat(),
                                  gap_min=round(gap, 1), cloud=f["properties"].get("eo:cloud_cover"),
                                  assets={"B02": a["blue"]["href"], "B03": a["green"]["href"], "B04": a["red"]["href"],
                                          "B08": a["nir"]["href"], "scl": a["scl"]["href"], "tci": a["visual"]["href"]}))
        if nq % 100 == 0:
            print(nq, len(pairs), flush=True)
    json.dump(dict(n_candidates=len(R), n_queried=nq, n_failed=nfail, win_min=WIN, pairs=pairs),
              open(OUT, "w"), indent=1, ensure_ascii=False)
    print("pairs", len(pairs), "failed", nfail)


if __name__ == "__main__":
    main()
