#!/usr/bin/env python3
"""Track 2, repointed: Sentinel-2 surface change at Sentinel-2-era NUFORC
ground-contact reports, against SELF-CONTROLLED pseudo-events (session 5).

WHY THIS DESIGN
---------------
Session 3 showed Track 2 on the 1964-81 historical sites is temporally
impossible (Sentinel-2 launched 23 Jun 2015). The handoff repointed it at the
"34,898 geocoded Sentinel-2-era NUFORC records". Two facts reshape that:

  1. 34,898 is year>=2015 and includes Jan-Jun 2015, before launch. The count
     from 2015-07 on is 32,260.
  2. Almost none of those records predicts anything Sentinel-2 can see.
     A light in the night sky leaves no surface signature, and Sentinel-2
     passes over at ~10:30 local time, so it cannot image a night event at
     the time it happens. The only falsifiable prediction is a post-event SURFACE
     CHANGE where a report claims ground contact.

So: (a) filter the 32,260 to explicit ground-contact claims, by keyword then
by reading each hit (the list and the reason for every exclusion is below);
(b) for each, measure NDVI change across the event in a 2 km box at the
geocoded point; (c) compare it with the SAME box, SAME pre/post gap and SAME
season in other years (pseudo-events). Under H0 (the event date is not special)
the event's rank among its own pseudo-events is uniform, whatever the land
cover. That is a stronger control than distant matched pixels, because each
site is its own control.

Statistic per scene pair, clear pixels only (SCL 4,5,6,7,11 kept; cloud,
shadow, cirrus, saturated and no-data dropped):
  LOSS = fraction of pixels with NDVI(post) - NDVI(pre) < -0.20
A burn mark, landing ring or flattened area is a local vegetation LOSS.

POWER, stated before the result: NUFORC is geocoded to SETTLEMENT centroids
(wikidata/nominatim), not to the field. A 2 km box (40,000 px of 10 m) around
a centroid may not contain the reported spot at all, and a 5 m trace is under
one pixel. A positive here would need a change of many hundred m^2 inside the
box. A null here is NOT evidence that the reported events left no trace.

Usage:  python3 -I omega/track2_nuforc_s2.py
Writes: evidence_vault/08_SATELLITE_ANOMALIES/track2_nuforc_s2.json
"""
import datetime as dt
import gzip
import json
import math
import os
import random
import re
import sys
import time
import urllib.request

import numpy as np
import rasterio
from rasterio.warp import transform as wtransform
from rasterio.windows import from_bounds

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUF = os.path.join(ROOT, "evidence_vault/06_NUFORC_MODERN_ARM/nuforc_unified.json.gz")
OUT = os.path.join(ROOT, "evidence_vault/08_SATELLITE_ANOMALIES/track2_nuforc_s2.json")
STAC = "https://earth-search.aws.element84.com/v1/search"
UA = "omega-research/1.0 (academic UAP data study; non-commercial)"

S2_START = (2015, 7)
KW = re.compile(r"\b(land(ed|ing)|touch(ed)? ?down|on the ground|burn(ed|t)? "
                r"(mark|spot|ring|grass)|scorch|trace|imprint|crop circle|flattened|"
                r"depression in|hovering (just )?above the (ground|field|trees))\b", re.I)

# Read every keyword hit (100). Kept: an object reported ON the ground at a
# spot near the witness, with a settlement-level geocode that is not ambiguous.
KEEP = {
 "NUFORC#1815": "ball 'landed in wooded area'",
 "NUFORC#3543": "'Burned spot on ground' (explicit trace claim)",
 "NUFORC#3610": "craft 'landed on Maxwell Avenue'",
 "NUFORC#5111": "'landed in my Garden ... leaving landing impressions' (trace claim)",
 "NUFORC#7938": "'object on the ground'",
 "NUFORC#11237": "'Crashed ... object in a neighbors yard'",
 "NUFORC#11346": "'landed in the field next to us'",
 "NUFORC#14341": "three craft 'when the landed'",
 "NUFORC#15284": "'10 lights scattered on the ground throughout the forest'",
 "NUFORC#17624": "'saucer like on the ground'",
 "NUFORC#22452": "'landed at Heil Ranch'",
 "NUFORC#22711": "'landed in field near home'",
 "NUFORC#24078": "'disc. landing in the oilfield'",
 "NUFORC#25704": "'landed 50 feet from me'",
 "NUFORC#28127": "'landed in the SW corner of our field'",
 "NUFORC#28387": "'spheres ... on the ground at 11 am'",
 "NUFORC#29366": "'landed super quick in front of vehicle'",
 "NUFORC#30486": "'UFO on the ground, next to power pole'",
}
EXCLUDE_REASONS = {
 "aircraft landing lights / airport / place-name hit": "the keyword matched aircraft, a staircase landing, or a place name (Moss Landing, Knights Landing, Weymouth Landing, Navy Landing)",
 "NUFORC flags HOAX or IFO": "Utica 2019, Zebulon 2016, Shrewsbury 2015, Moab 2015 (Navy missile), space-debris notes",
 "no ground contact": "'vanished without a trace', 'hovering above the trees', meteors that 'may have landed'",
 "ambiguous geocode": "Telford (geocoded to Australia), Peru (country or Peru IL), Wood Ranch (event at Firebaugh)",
 "no spot": "Watertown video link, Clarks Summit, Las Vegas 'appears to be landed'",
}

BOX_M = 1000.0          # half-width: 2 km box
PRE_DAYS, POST_DAYS = 60, 40
MAX_CC = 40.0           # scene cloud; pixel-level SCL masking does the real work
MIN_CLEAR = 0.5         # pair kept only if >=50% of box pixels clear in both
K_PSEUDO = 8
YEARS = range(2016, 2025)
KEEP_SCL = {4, 5, 6, 7, 11}


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception as e:  # report, do not swallow
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"STAC failed after 4 tries: {last!r}")


def scenes(lon, lat, t0, t1, tile=None):
    body = {"collections": ["sentinel-2-l2a"],
            "intersects": {"type": "Point", "coordinates": [lon, lat]},
            "datetime": f"{t0.isoformat()}T00:00:00Z/{t1.isoformat()}T23:59:59Z",
            "query": {"eo:cloud_cover": {"lt": MAX_CC}}, "limit": 100}
    fs = post(STAC, body)["features"]
    out = {}
    for f in fs:
        p = f["properties"]
        t = p.get("s2:mgrs_tile") or f["id"].split("_")[1]
        if tile and t != tile:
            continue
        d = p["datetime"][:10]
        # duplicate processings of one acquisition: keep the newest baseline
        key = (t, d)
        bl = float(p.get("s2:processing_baseline", "0") or 0)
        if key not in out or bl > out[key][0]:
            out[key] = (bl, f)
    return sorted(((k[1], k[0], v[0], v[1]) for k, v in out.items()))


def read_box(feat, lon, lat):
    a = feat["assets"]
    with rasterio.open(a["red"]["href"]) as r:
        xs, ys = wtransform("EPSG:4326", r.crs, [lon], [lat])
        x, y = xs[0], ys[0]
        win = from_bounds(x - BOX_M, y - BOX_M, x + BOX_M, y + BOX_M, r.transform)
        red = r.read(1, window=win, boundless=True, fill_value=0).astype("f4")
    with rasterio.open(a["nir"]["href"]) as r:
        nir = r.read(1, window=win, boundless=True, fill_value=0).astype("f4")
    with rasterio.open(a["scl"]["href"]) as r:   # 20 m: read same bounds, upsample
        w2 = from_bounds(x - BOX_M, y - BOX_M, x + BOX_M, y + BOX_M, r.transform)
        scl = r.read(1, window=w2, boundless=True, fill_value=0,
                     out_shape=red.shape, resampling=rasterio.enums.Resampling.nearest)
    return red, nir, scl


def ndvi(feat, red, nir):
    # Baseline >=04.00 products carry BOA_ADD_OFFSET=-1000 in the raw DN. Earth
    # Search's COGs flag `earthsearch:boa_offset_applied: True` and their DN
    # are already harmonised: checked 2026-11-26 on tile 16SBF, red-band 1st
    # percentile 109-266 DN across baselines 05.00 and 05.09, impossible if a
    # +1000 offset were still in the data. Subtract only when not applied.
    p = feat["properties"]
    bl = float(p.get("s2:processing_baseline", "0") or 0)
    off = 0.0 if p.get("earthsearch:boa_offset_applied") else (1000.0 if bl >= 4.0 else 0.0)
    r = (red - off) / 10000.0
    n = (nir - off) / 10000.0
    with np.errstate(divide="ignore", invalid="ignore"):
        v = (n - r) / (n + r)
    return v


def pair_stat(lon, lat, ev, tile=None):
    pre = scenes(lon, lat, ev - dt.timedelta(days=PRE_DAYS), ev - dt.timedelta(days=1), tile)
    pst = scenes(lon, lat, ev + dt.timedelta(days=1), ev + dt.timedelta(days=POST_DAYS), tile)
    if tile is None and pre:
        tile = pre[-1][1]
        pst = [s for s in pst if s[1] == tile]
    # nearest clear scene each side
    for a in reversed(pre):
        A = read_box(a[3], lon, lat)
        ca = np.isin(A[2], list(KEEP_SCL))
        if ca.mean() >= MIN_CLEAR:
            break
    else:
        return None, tile
    for b in pst:
        B = read_box(b[3], lon, lat)
        cb = np.isin(B[2], list(KEEP_SCL))
        if (ca & cb).mean() >= MIN_CLEAR:
            break
    else:
        return None, tile
    m = ca & cb
    d = ndvi(b[3], B[0], B[1]) - ndvi(a[3], A[0], A[1])
    d = d[m & np.isfinite(d)]
    return dict(pre=a[0], post=b[0], tile=tile, clear=float(m.mean()),
                loss=float((d < -0.20).mean()), mean_d=float(d.mean())), tile


def main():
    recs = json.load(gzip.open(NUF))["nuforc"]
    era = [r for r in recs if r["lat"] is not None and r["year"]
           and (r["year"], r["month"] or 0) >= S2_START]
    hits = [r for r in era if KW.search(r["desc"] or "")]
    keep = [r for r in hits if r["uid"] in KEEP]
    assert len(keep) == len(KEEP), set(KEEP) - {r["uid"] for r in keep}
    print(f"Sentinel-2-era geocoded records (>= 2015-07): {len(era)}")
    print(f"keyword hits: {len(hits)}; read and kept as ground-contact claims: {len(keep)}\n")

    rng = random.Random(20261126)
    rows = []
    for r in keep:
        ev = dt.date(r["year"], r["month"], r["day"])
        lon, lat = r["lon"], r["lat"]
        res, tile = pair_stat(lon, lat, ev)
        row = dict(uid=r["uid"], location=r["location"], date=ev.isoformat(),
                   lat=lat, lon=lon, claim=KEEP[r["uid"]], event=res, pseudo=[])
        if res:
            yrs = [y for y in YEARS if y != ev.year]
            rng.shuffle(yrs)
            for y in yrs:
                if len(row["pseudo"]) >= K_PSEUDO:
                    break
                try:
                    pe = dt.date(y, ev.month, min(ev.day, 28)) + dt.timedelta(days=rng.randint(-15, 15))
                except ValueError:
                    continue
                pr, _ = pair_stat(lon, lat, pe, tile)
                if pr:
                    row["pseudo"].append(pr)
            ps = [p["loss"] for p in row["pseudo"]]
            if ps:
                # mid-rank of the event among event+pseudo (1 = smallest LOSS)
                gt = sum(p < res["loss"] for p in ps)
                eq = sum(p == res["loss"] for p in ps)
                row["rank_frac"] = (gt + 0.5 * eq + 0.5) / (len(ps) + 1)
        rows.append(row)
        e = row["event"]
        print(f"  {r['uid']:13s} {r['location'][:18]:18s} {ev}  "
              + (f"LOSS={e['loss']:.4f} clear={e['clear']:.2f} pseudo n={len(row['pseudo'])} "
                 f"rank={row.get('rank_frac', float('nan')):.2f}" if e else "no clear pair"))

    tested = [r for r in rows if "rank_frac" in r]
    n = len(tested)
    # H0: rank_frac ~ U(0,1). Test the one-sided "event has MORE loss" direction
    # by the sum of ranks against its permutation distribution.
    obs = sum(r["rank_frac"] for r in tested)
    sims = []
    for _ in range(20000):
        s = 0.0
        for r in tested:
            k = len(r["pseudo"]) + 1
            s += (rng.randrange(k) + 0.5) / k
        sims.append(s)
    p_one = (sum(x >= obs for x in sims) + 1) / (len(sims) + 1)
    top = sum(1 for r in tested if r["rank_frac"] > 1 - 1 / (len(r["pseudo"]) + 1))
    exp_top = sum(1 / (len(r["pseudo"]) + 1) for r in tested)
    # paired effect: event LOSS minus median pseudo LOSS, bootstrap CI
    eff = [r["event"]["loss"] - float(np.median([p["loss"] for p in r["pseudo"]])) for r in tested]
    bs = sorted(float(np.mean([rng.choice(eff) for _ in eff])) for _ in range(10000)) if eff else []
    summary = dict(era_records=len(era), keyword_hits=len(hits), kept=len(keep),
                   with_event_pair=sum(1 for r in rows if r["event"]),
                   tested=n, mean_rank_frac=obs / n if n else None,
                   p_one_sided=p_one if n else None,
                   event_is_max=top, expected_max=exp_top,
                   effect_loss_minus_median_pseudo=float(np.mean(eff)) if eff else None,
                   effect_ci95=(bs[249], bs[9749]) if bs else None)
    print("\n" + json.dumps(summary, indent=1))
    json.dump(dict(summary=summary, design=dict(box_m=2 * BOX_M, pre_days=PRE_DAYS,
                   post_days=POST_DAYS, loss_threshold=-0.20, k_pseudo=K_PSEUDO,
                   keep_scl=sorted(KEEP_SCL), min_clear=MIN_CLEAR),
                   exclusions=EXCLUDE_REASONS, rows=rows), open(OUT, "w"), indent=1)
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
