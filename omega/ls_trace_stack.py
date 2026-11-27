#!/usr/bin/env python3
"""Tier 2.3 (session 7): Landsat stacks +-30 days around the 20 GEIPAN
physical-trace (lab-analysis) cases, 1981-2025, self-controlled.

Source: Landsat Collection 1 L1 on Google's public bucket
(storage.googleapis.com/gcp-public-data-landsat), the same USGS product as the
requester-pays usgs-landsat bucket, which returns 403 here. Collection 1 ends
in 2021; later cases are not testable from this mirror.

Same design as track2_nuforc_s2.py: for each case, LOSS = fraction of clear
pixels in a 2 km box whose NDVI drops by > 0.2 from the last clear scene in the
30 days before to the first clear scene in the 30 days after; compared with
the same box, same sensor, same season (+-20 d) and similar gap in other years.
Under H0 the event's rank among its pseudo-events is uniform.

GEIPAN classes give a built-in control: A/B cases were EXPLAINED (lamps,
ordinary causes), C/D were not. If traces were real surface events, C/D should
rank higher than A/B.

POWER: commune-level geocodes (0.01 deg, ~1 km), 30 m (TM/ETM/OLI) or 60 m
(MSS) pixels, and reported traces of 1-10 m. A single trace is far below one
pixel. Only a disturbance of thousands of m^2 inside the box could register.
A null here says nothing about metre-scale traces.

DN-based NDVI (no TOA conversion); every comparison is within one sensor family.
"""
import csv, datetime as dt, json, os, sys
import numpy as np, rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform as wt

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://storage.googleapis.com/"
OUT = os.path.join(ROOT, "evidence_vault/08_SATELLITE_ANOMALIES/ls_trace_stack.json")
BANDS = {"LANDSAT_8": ("B4", "B5"), "LANDSAT_7": ("B3", "B4"), "LANDSAT_5": ("B3", "B4"),
         "LANDSAT_4": ("B3", "B4")}
MSS = {"LANDSAT_1": ("B5", "B7"), "LANDSAT_2": ("B5", "B7"), "LANDSAT_3": ("B5", "B7")}


def family(r):
    sc = r["SPACECRAFT_ID"]
    if r["SENSOR_ID"] == "MSS":
        return "MSS", MSS.get(sc, ("B2", "B4"))
    return sc, BANDS[sc]


def load_index(path, lat, lon):
    rows = []
    for r in csv.DictReader(open(path)):
        try:
            if not (float(r["SOUTH_LAT"]) + .05 < lat < float(r["NORTH_LAT"]) - .05 and
                    float(r["WEST_LON"]) + .05 < lon < float(r["EAST_LON"]) - .05):
                continue
            if float(r["CLOUD_COVER"]) > 60 or r["COLLECTION_CATEGORY"] == "RT":
                continue
        except ValueError:
            continue
        r["date"] = dt.date.fromisoformat(r["DATE_ACQUIRED"]); rows.append(r)
    return rows


def box(r, lat, lon):
    fam, (red, nir) = family(r)
    url = BASE + r["BASE_URL"][5:] + "/" + r["PRODUCT_ID"]
    try:
        with rasterio.open(f"{url}_{red}.TIF") as s:
            (x,), (y,) = wt("EPSG:4326", s.crs, [lon], [lat])
            w = from_bounds(x - 1000, y - 1000, x + 1000, y + 1000, s.transform)
            R = s.read(1, window=w, boundless=True, fill_value=0).astype(np.float32)
        with rasterio.open(f"{url}_{nir}.TIF") as s:
            N = s.read(1, window=w, boundless=True, fill_value=0).astype(np.float32)
        with rasterio.open(f"{url}_BQA.TIF") as s:
            q = s.read(1, window=w, boundless=True, fill_value=1)
    except Exception as e:
        return None
    cloud = (q & 1).astype(bool) | ((q >> 4) & 1).astype(bool)
    ok = ~cloud & (R > 0) & (N > 0)
    nd = np.where(ok, (N - R) / np.maximum(N + R, 1), np.nan)
    return nd


def pair_loss(a, b):
    if a is None or b is None or a.shape != b.shape:
        return None
    d = b - a; ok = np.isfinite(d)
    if ok.mean() < 0.6:
        return None
    return dict(loss=float((d[ok] < -0.2).mean()), clear=float(ok.mean()))


def first_clear(cands, lat, lon, cache):
    for r in cands:
        k = r["PRODUCT_ID"]
        if k not in cache:
            cache[k] = box(r, lat, lon)
        nd = cache[k]
        if nd is not None and np.isfinite(nd).mean() >= 0.6:
            return r, nd
    return None, None


def event_pair(rows, d0, lat, lon, cache, fam=None):
    pre = sorted([r for r in rows if d0 - dt.timedelta(30) <= r["date"] < d0 and (fam is None or family(r)[0] == fam)],
                 key=lambda r: (d0 - r["date"], float(r["CLOUD_COVER"])))
    post = sorted([r for r in rows if d0 < r["date"] <= d0 + dt.timedelta(30) and (fam is None or family(r)[0] == fam)],
                  key=lambda r: (r["date"] - d0, float(r["CLOUD_COVER"])))
    for p in pre[:4]:
        f = family(p)[0]
        rp, a = first_clear([p], lat, lon, cache)
        if a is None:
            continue
        rq, b = first_clear([q for q in post if family(q)[0] == f][:4], lat, lon, cache)
        if b is None:
            continue
        s = pair_loss(a, b)
        if s:
            return dict(s, pre=rp["PRODUCT_ID"], post=rq["PRODUCT_ID"], fam=f,
                        gap=(rq["date"] - rp["date"]).days)
    return None


def main(index):
    cases = json.load(open(os.path.join(ROOT, "evidence_vault/02_GEPAN_PHYSICAL_TRACES/lab_analysis_cases.json")))
    g = {r["ID Etude de Cas"]: r for r in json.load(open(os.path.join(ROOT, "data/raw/geipan/geipan_cases.json")))}
    res = []
    for c in cases:
        r0 = g.get(c["id"]); dd, mm, yy = r0["Observation date"].split("/")
        d0 = dt.date(int(yy), int(mm), int(dd)); lat, lon = float(c["lat"]), float(c["lon"])
        row = dict(id=c["id"], title=c["title"], cls=r0["Classification"], date=d0.isoformat(), lat=lat, lon=lon)
        if d0 > dt.date(2021, 12, 31):
            row["skip"] = "after Collection 1 end"; res.append(row); print(row, flush=True); continue
        rows = load_index(index, lat, lon); cache = {}
        ev = event_pair(rows, d0, lat, lon, cache)
        row["event"] = ev
        if ev:
            ps = []
            for y in range(1975, 2022):
                if y == d0.year:
                    continue
                try:
                    dp = d0.replace(year=y)
                except ValueError:
                    dp = d0.replace(year=y, day=28)
                cand = [r for r in rows if abs((r["date"] - dp).days) <= 20 and family(r)[0] == ev["fam"]]
                if not cand:
                    continue
                pe = event_pair(rows, dp, lat, lon, cache, fam=ev["fam"])
                if pe and abs(pe["gap"] - ev["gap"]) <= 24:
                    ps.append(dict(year=y, **pe))
                if len(ps) >= 8:
                    break
            row["pseudo"] = ps
            if ps:
                L = [p["loss"] for p in ps]
                gt = sum(ev["loss"] > x for x in L); eq = sum(ev["loss"] == x for x in L)
                row["rank_frac"] = (gt + 0.5 * eq + 0.5) / (len(L) + 1)
        res.append(row); print(row["id"], row["cls"], row.get("event") and round(row["event"]["loss"], 4),
                               len(row.get("pseudo", [])), row.get("rank_frac"), flush=True)
        json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
    t = [r for r in res if "rank_frac" in r]
    summ = dict(tested=len(t), mean_rank=float(np.mean([r["rank_frac"] for r in t])) if t else None,
                CD=[(r["id"], r["rank_frac"]) for r in t if r["cls"] in ("C", "D")],
                AB=[(r["id"], r["rank_frac"]) for r in t if r["cls"] in ("A", "B")])
    if t:
        rng = np.random.default_rng(0)
        n = [len(r["pseudo"]) + 1 for r in t]
        sims = [np.mean([(rng.integers(0, k) + 0.5) / k for k in n]) for _ in range(20000)]
        summ["p_one_sided"] = float(np.mean(np.array(sims) >= summ["mean_rank"]))
    json.dump(dict(summary=summ, cases=res), open(OUT, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(summ))


if __name__ == "__main__":
    main(sys.argv[1])
