#!/usr/bin/env python3
"""Track 2 rerun, step 1 of 2: build and FREEZE the matched-landcover control set.

Preregistration: omega/reports/track2_landcover_prereg.md (committed first).
This step reads ESA WorldCover 2021, Copernicus DEM GLO-90, the NUFORC catalogue
and Sentinel-2 STAC *metadata* (scene footprints). It reads no red, NIR or SCL
pixel anywhere, so the control choice cannot be tuned to the outcome.

For each case with a session 5 event pair: candidate centres on a 2 km grid,
10-80 km out, whose 2 km box sits inside both scene footprints (shrunk 1.5 km).
Keep if WorldCover class-fraction L1 <= 0.30, DEM mean within +-150 m, no NUFORC
record within 5 km, centre >= 4 km from every kept control. Rank by L1 then
distance; freeze the first 30.

WorldCover is read from its 4x overview (~37 m) and the DEM at 90 m. Matching
on class fractions at 37 m is ample for 2 km boxes; recorded as a choice.

Usage:  python3 -I omega/track2_lc_controls.py A|B   (A preregistered, B amendment 1)
Writes: evidence_vault/08_SATELLITE_ANOMALIES/track2_lc_control_set_{A,B}.json (+ sha256)
"""
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import sys
import time
import urllib.request

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import box as sbox, shape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = os.path.join(ROOT, "evidence_vault/08_SATELLITE_ANOMALIES")
S5 = os.path.join(V8, "track2_nuforc_s2.json")
NUF = os.path.join(ROOT, "evidence_vault/06_NUFORC_MODERN_ARM/nuforc_unified.json.gz")
TIER = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
assert TIER in ("A", "B"), TIER
OUT = os.path.join(V8, f"track2_lc_control_set_{TIER}.json")
STAC = "https://earth-search.aws.element84.com/v1/search"
UA = "omega-research/1.0 (academic UAP data study; non-commercial)"
WC = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
      "ESA_WorldCover_10m_2021_v200_{t}_Map.tif")
DEM = ("https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_{t}_DEM/"
       "Copernicus_DSM_COG_30_{t}_DEM.tif")
WC_CLASSES = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]

HALF = 1000.0                       # 2 km box
R_MIN, R_MAX, STEP = 10e3, 80e3, 2e3
DZ_MAX, SEP = 150.0, 4e3
# Tier A = preregistered; Tier B = amendment 1, exploratory
L1_MAX, NUF_EXCL = {"A": (0.30, 5e3), "B": (0.50, 2e3)}[TIER]
N_FREEZE = 30
SHRINK_DEG = 1500.0 / 111320.0
WC_RES = 1 / 3000.0                 # 4x overview of 1/12000 deg
DEM_RES = 1 / 1200.0


def post(body):
    req = urllib.request.Request(STAC, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"STAC failed: {last!r}")


def scene(lon, lat, day, tile, col="sentinel-2-l2a"):
    body = {"collections": [col], "intersects": {"type": "Point", "coordinates": [lon, lat]},
            "datetime": f"{day}T00:00:00Z/{day}T23:59:59Z", "limit": 20}
    fs = [f for f in post(body)["features"]
          if (f["properties"].get("s2:mgrs_tile") or f["id"].split("_")[1]) == tile]
    fs.sort(key=lambda f: float(f["properties"].get("s2:processing_baseline", "0") or 0))
    return fs[-1]   # same newest-baseline rule as session 5


def tname_wc(la, lo):
    return f"{'N' if la >= 0 else 'S'}{abs(la):02d}{'E' if lo >= 0 else 'W'}{abs(lo):03d}"


def tname_dem(la, lo):
    return f"{'N' if la >= 0 else 'S'}{abs(la):02d}_00_{'E' if lo >= 0 else 'W'}{abs(lo):03d}_00"


def mosaic(w, s, e, n, res, step, url, namer, dtype, fill):
    """Mosaic tiles of `step` degrees onto a north-up grid of `res` degrees."""
    W, H = int(round((e - w) / res)), int(round((n - s) / res))
    arr = np.full((H, W), fill, dtype=dtype)
    for la in range(int(math.floor(s / step) * step), int(math.ceil(n)), step):
        for lo in range(int(math.floor(w / step) * step), int(math.ceil(e)), step):
            tw, ts, te, tn = max(w, lo), max(s, la), min(e, lo + step), min(n, la + step)
            if te <= tw or tn <= ts:
                continue
            try:
                with rasterio.open(url.format(t=namer(la, lo))) as r:
                    win = from_bounds(tw, ts, te, tn, r.transform)
                    c0, r0 = int(round((tw - w) / res)), int(round((n - tn) / res))
                    c1, r1 = int(round((te - w) / res)), int(round((n - ts) / res))
                    arr[r0:r1, c0:c1] = r.read(1, window=win, out_shape=(r1 - r0, c1 - c0),
                                               resampling=rasterio.enums.Resampling.nearest)
            except rasterio.errors.RasterioIOError:
                pass   # tile absent (open ocean): stays at fill, recorded via coverage
    return arr


def boxsl(lon, lat, w, n, res):
    dla = HALF / 111320.0
    dlo = HALF / (111320.0 * math.cos(math.radians(lat)))
    r0, r1 = int((n - (lat + dla)) / res), int(math.ceil((n - (lat - dla)) / res))
    c0, c1 = int((lon - dlo - w) / res), int(math.ceil((lon + dlo - w) / res))
    return slice(r0, r1), slice(c0, c1)


def lc_vec(a):
    v = np.array([(a == c).sum() for c in WC_CLASSES], dtype=float)
    return v / v.sum() if v.sum() else v


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    d = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371000.0 * np.arcsin(np.sqrt(d))


def main():
    s5 = json.load(open(S5))
    nuf = json.load(gzip.open(NUF))["nuforc"]
    nl = np.array([[r["lat"], r["lon"]] for r in nuf if r["lat"] is not None], dtype=float)
    out = []
    for row in s5["rows"]:
        if not row["event"]:
            out.append(dict(uid=row["uid"], location=row["location"], status="no_event_pair"))
            continue
        lat, lon, ev = row["lat"], row["lon"], row["event"]
        fa = scene(lon, lat, ev["pre"], ev["tile"])
        fb = scene(lon, lat, ev["post"], ev["tile"])
        foot = shape(fa["geometry"]).intersection(shape(fb["geometry"])).buffer(-SHRINK_DEG)
        dla = R_MAX / 111320.0 + 0.05
        dlo = R_MAX / (111320.0 * math.cos(math.radians(lat))) + 0.05
        w, e, s, n = lon - dlo, lon + dlo, lat - dla, lat + dla
        wc = mosaic(w, s, e, n, WC_RES, 3, WC, tname_wc, np.uint8, 0)
        dem = mosaic(w, s, e, n, DEM_RES, 1, DEM, tname_dem, np.float32, np.nan)
        sl = boxsl(lon, lat, w, n, WC_RES)
        cv = lc_vec(wc[sl])
        cz = float(np.nanmean(dem[boxsl(lon, lat, w, n, DEM_RES)]))
        near = nl[(np.abs(nl[:, 0] - lat) < dla + 0.1) & (np.abs(nl[:, 1] - lon) < dlo + 0.1)]
        cands = []
        why = dict(grid=0, footprint=0, nodata=0, landcover=0, elevation=0, nuforc=0)
        m_per_dlo = 111320.0 * math.cos(math.radians(lat))
        for dy in np.arange(-R_MAX, R_MAX + 1, STEP):
            for dx in np.arange(-R_MAX, R_MAX + 1, STEP):
                r = math.hypot(dx, dy)
                if not (R_MIN <= r <= R_MAX):
                    continue
                why["grid"] += 1
                clat, clon = lat + dy / 111320.0, lon + dx / m_per_dlo
                bx = sbox(clon - HALF / m_per_dlo, clat - HALF / 111320.0,
                          clon + HALF / m_per_dlo, clat + HALF / 111320.0)
                if not foot.contains(bx):
                    why["footprint"] += 1
                    continue
                a = wc[boxsl(clon, clat, w, n, WC_RES)]
                if (a == 0).mean() > 0.01:
                    why["nodata"] += 1
                    continue
                v = lc_vec(a)
                l1 = float(np.abs(v - cv).sum())
                if l1 > L1_MAX:
                    why["landcover"] += 1
                    continue
                z = float(np.nanmean(dem[boxsl(clon, clat, w, n, DEM_RES)]))
                if not math.isfinite(z) or abs(z - cz) > DZ_MAX:
                    why["elevation"] += 1
                    continue
                dn = float(hav(clat, clon, near[:, 0], near[:, 1]).min()) if len(near) else 1e9
                if dn < NUF_EXCL:
                    why["nuforc"] += 1
                    continue
                cands.append(dict(lat=clat, lon=clon, dist_km=r / 1e3, l1=l1, dz=z - cz,
                                  nearest_nuforc_km=round(dn / 1e3, 2),
                                  lc=[round(x, 4) for x in v]))
        cands.sort(key=lambda c: (c["l1"], c["dist_km"]))
        kept = []
        for c in cands:
            if all(hav(c["lat"], c["lon"], k["lat"], k["lon"]) >= SEP for k in kept):
                kept.append(c)
            if len(kept) >= N_FREEZE:
                break
        rec = dict(uid=row["uid"], location=row["location"], lat=lat, lon=lon,
                   tile=ev["tile"], pre=ev["pre"], post=ev["post"],
                   pre_id=fa["id"], post_id=fb["id"], case_lc=[round(x, 4) for x in cv],
                   case_dem_m=cz, candidates_passing=len(cands), rejected=why, controls=kept,
                   status="ok" if len(kept) >= 10 else "uncontrollable")
        out.append(rec)
        top = sorted(zip(cv, WC_CLASSES), reverse=True)[:3]
        print(f"{row['uid']:13s} {row['location'][:16]:16s} lc={[(c, round(f, 2)) for f, c in top]} "
              f"z={cz:.0f} {why} pass={len(cands)} kept={len(kept)} "
              f"medL1={np.median([k['l1'] for k in kept]) if kept else float('nan'):.3f}")
    # c1-l2a fallback for cases without a pair (prereg): metadata check only
    fb_notes = {}
    for r in s5["rows"]:
        if r["event"]:
            continue
        ev = dt.date.fromisoformat(r["date"])
        body = {"collections": ["sentinel-2-c1-l2a"],
                "intersects": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                "datetime": f"{ev - dt.timedelta(days=60)}T00:00:00Z/{ev + dt.timedelta(days=40)}T23:59:59Z",
                "limit": 100}
        fb_notes[r["uid"]] = len(post(body)["features"])
    print("c1-l2a scenes in window for no-pair cases:", fb_notes)
    doc = dict(tier=TIER, prereg="omega/reports/track2_landcover_prereg.md",
               built=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds") + "Z",
               params=dict(box_m=2 * HALF, r_km=[R_MIN / 1e3, R_MAX / 1e3], grid_km=STEP / 1e3,
                           l1_max=L1_MAX, dz_max_m=DZ_MAX, nuforc_excl_km=NUF_EXCL / 1e3,
                           sep_km=SEP / 1e3, n_freeze=N_FREEZE, worldcover="2021 v200, 4x overview",
                           dem="Copernicus GLO-90"),
               c1_fallback_scene_counts=fb_notes, cases=out)
    txt = json.dumps(doc, indent=1)
    open(OUT, "w").write(txt)
    h = hashlib.sha256(txt.encode()).hexdigest()
    open(OUT + ".sha256", "w").write(f"{h}  {os.path.basename(OUT)}\n")
    print("wrote", os.path.relpath(OUT, ROOT), "sha256", h[:16])


if __name__ == "__main__":
    main()
