#!/usr/bin/env python3
"""Track 2 rerun, step 2 of 2: detection on the FROZEN matched-landcover control set.

Preregistration: omega/reports/track2_landcover_prereg.md (+ amendment 1).
Control sets: evidence_vault/08_SATELLITE_ANOMALIES/track2_lc_control_set_{A,B}.json,
committed with sha256 before this script first ran. The hash is checked here.

Per case, on the identical pre/post scene pair:
  S1  LOSS = fraction of clear pixels with dNDVI < -0.20 (session 5 statistic)
  S2  largest 8-connected cluster of loss pixels, m^2
  S1w (tier B) control LOSS reweighted per WorldCover class to the case's class mix
Rank of the case among case + first 20 controls that are >=50% clear in both.
Combined: sum of rank fractions vs Monte Carlo permutation null, one-sided.
Power: inject an NDVI drop of 0.40 in a disc into the case's real dNDVI.

Usage:  python3 -I omega/track2_lc_detect.py A|B
Writes: evidence_vault/08_SATELLITE_ANOMALIES/track2_lc_detect_{A,B}.json
"""
import hashlib
import json
import math
import os
import random
import sys
import time
import urllib.request

import numpy as np
import rasterio
from rasterio.warp import transform as wtransform
from rasterio.windows import from_bounds
from scipy import ndimage

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = os.path.join(ROOT, "evidence_vault/08_SATELLITE_ANOMALIES")
TIER = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
CS = os.path.join(V8, f"track2_lc_control_set_{TIER}.json")
S5 = os.path.join(V8, "track2_nuforc_s2.json")
OUT = os.path.join(V8, f"track2_lc_detect_{TIER}.json")
STAC = "https://earth-search.aws.element84.com/v1/search"
UA = "omega-research/1.0 (academic UAP data study; non-commercial)"
WC = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
      "ESA_WorldCover_10m_2021_v200_{t}_Map.tif")
WC_CLASSES = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
HALF = 1000.0
KEEP_SCL = [4, 5, 6, 7, 11]
MIN_CLEAR, N_CTRL, MIN_CTRL = 0.5, 20, 10
THR = -0.20
AREAS = [100, 400, 1600, 6400, 25600]          # preregistered
AREAS_EXT = [102400, 409600]                   # beyond prereg, labelled
N_INJ, INJ_DROP = 50, 0.40
STRUCT8 = np.ones((3, 3), int)


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


def feature(lon, lat, day, tile):
    """Session 5's product rule, exactly: scene cloud < 40%, then newest baseline.

    The control-set file records the newest-baseline product id WITHOUT the
    cloud filter. Where an acquisition has two processings (e.g. Shelby
    2020-06-25: baseline 02.14 at 35.8% and 05.00 at 47.9%), that picks a
    different product from session 5. The assert against session 5's LOSS
    caught it. Product choice is metadata; control locations are unaffected.
    """
    body = {"collections": ["sentinel-2-l2a"], "intersects": {"type": "Point", "coordinates": [lon, lat]},
            "datetime": f"{day}T00:00:00Z/{day}T23:59:59Z", "query": {"eo:cloud_cover": {"lt": 40.0}},
            "limit": 20}
    fs = [f for f in post(body)["features"]
          if (f["properties"].get("s2:mgrs_tile") or f["id"].split("_")[1]) == tile]
    fs.sort(key=lambda f: float(f["properties"].get("s2:processing_baseline", "0") or 0))
    return fs[-1]


class Scene:
    """Open red/NIR/SCL once; read many 2 km boxes."""
    def __init__(self, feat):
        a, p = feat["assets"], feat["properties"]
        self.r = rasterio.open(a["red"]["href"])
        self.n = rasterio.open(a["nir"]["href"])
        self.s = rasterio.open(a["scl"]["href"])
        bl = float(p.get("s2:processing_baseline", "0") or 0)
        self.off = 0.0 if p.get("earthsearch:boa_offset_applied") else (1000.0 if bl >= 4.0 else 0.0)

    def box(self, lon, lat):
        xs, ys = wtransform("EPSG:4326", self.r.crs, [lon], [lat])
        x, y = xs[0], ys[0]
        b = (x - HALF, y - HALF, x + HALF, y + HALF)
        win = from_bounds(*b, self.r.transform)
        red = self.r.read(1, window=win, boundless=True, fill_value=0).astype("f4")
        nir = self.n.read(1, window=win, boundless=True, fill_value=0).astype("f4")
        scl = self.s.read(1, window=from_bounds(*b, self.s.transform), boundless=True, fill_value=0,
                          out_shape=red.shape, resampling=rasterio.enums.Resampling.nearest)
        r, n = (red - self.off) / 1e4, (nir - self.off) / 1e4
        with np.errstate(divide="ignore", invalid="ignore"):
            v = (n - r) / (n + r)
        return v, np.isin(scl, KEEP_SCL), (x, y)


def wc_classes(crs, xy, shape):
    """WorldCover class at the centre of each 10 m S2 pixel of the box."""
    x0, y0 = xy[0] - HALF, xy[1] + HALF
    h, w = shape
    cx = x0 + (np.arange(w) + 0.5) * (2 * HALF / w)
    cy = y0 - (np.arange(h) + 0.5) * (2 * HALF / h)
    gx, gy = np.meshgrid(cx, cy)
    lon, lat = wtransform(crs, "EPSG:4326", gx.ravel().tolist(), gy.ravel().tolist())
    lon, lat = np.array(lon), np.array(lat)
    out = np.zeros(lon.size, np.uint8)
    tiles = {(int(math.floor(a / 3) * 3), int(math.floor(o / 3) * 3)) for a, o in zip(lat, lon)}
    for la, lo in tiles:
        t = f"{'N' if la >= 0 else 'S'}{abs(la):02d}{'E' if lo >= 0 else 'W'}{abs(lo):03d}"
        sel = (np.floor(lat / 3) * 3 == la) & (np.floor(lon / 3) * 3 == lo)
        with rasterio.open(WC.format(t=t)) as r:
            win = from_bounds(lon[sel].min() - 1e-3, lat[sel].min() - 1e-3,
                              lon[sel].max() + 1e-3, lat[sel].max() + 1e-3, r.transform).round_offsets().round_lengths()
            a = r.read(1, window=win)
            tr = r.window_transform(win)
            cols = ((lon[sel] - tr.c) / tr.a).astype(int).clip(0, a.shape[1] - 1)
            rows = ((lat[sel] - tr.f) / tr.e).astype(int).clip(0, a.shape[0] - 1)
            out[sel] = a[rows, cols]
    return out.reshape(shape)


def stats(d, m):
    lossmask = m & np.isfinite(d) & (d < THR)
    valid = m & np.isfinite(d)
    loss = float(lossmask.sum() / valid.sum())
    lab, k = ndimage.label(lossmask, structure=STRUCT8)
    clus = float(np.bincount(lab.ravel())[1:].max() * 100.0) if k else 0.0
    return loss, clus


def per_class(d, m, cls):
    valid = m & np.isfinite(d)
    lm = valid & (d < THR)
    return {c: (int(lm[cls == c].sum()), int(valid[cls == c].sum())) for c in WC_CLASSES
            if valid[cls == c].sum() > 0}


def rank_frac(x, ctrl):
    gt = sum(c < x for c in ctrl)
    eq = sum(c == x for c in ctrl)
    return (gt + 0.5 * eq + 0.5) / (len(ctrl) + 1)


def disc(shape, cy, cx, r):
    yy, xx = np.ogrid[:shape[0], :shape[1]]
    return (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r


def main():
    txt = open(CS).read()
    want = open(CS + ".sha256").read().split()[0]
    got = hashlib.sha256(txt.encode()).hexdigest()
    assert got == want, f"control set changed since freeze: {got} != {want}"
    cs = json.loads(txt)
    s5 = {r["uid"]: r for r in json.load(open(S5))["rows"]}
    rng = random.Random(20261126)
    np_rng = np.random.default_rng(20261126)
    rows = []
    for c in cs["cases"]:
        if c.get("status") != "ok":
            rows.append(dict(uid=c["uid"], location=c["location"], status=c.get("status"),
                             n_frozen=len(c.get("controls", []))))
            continue
        fa = feature(c["lon"], c["lat"], c["pre"], c["tile"])
        fb = feature(c["lon"], c["lat"], c["post"], c["tile"])
        A, B = Scene(fa), Scene(fb)
        va, ma, xy = A.box(c["lon"], c["lat"])
        vb, mb, _ = B.box(c["lon"], c["lat"])
        m = ma & mb
        d = vb - va
        loss, clus = stats(d, m)
        s5loss = s5[c["uid"]]["event"]["loss"]
        assert abs(loss - s5loss) < 1e-6, (c["uid"], loss, s5loss)   # same instrument as session 5
        ccls = wc_classes(A.r.crs, xy, d.shape)
        pc_case = per_class(d, m, ccls)
        tot = sum(v[1] for v in pc_case.values())
        w_case = {k: v[1] / tot for k, v in pc_case.items()}
        ctrl, skipped = [], 0
        for k in c["controls"]:
            if len(ctrl) >= N_CTRL:
                break
            ka, kma, kxy = A.box(k["lon"], k["lat"])
            kb, kmb, _ = B.box(k["lon"], k["lat"])
            km = kma & kmb
            if km.mean() < MIN_CLEAR:
                skipped += 1
                continue
            kd = kb - ka
            kl, kc = stats(kd, km)
            kcls = wc_classes(A.r.crs, kxy, kd.shape)
            ctrl.append(dict(lat=k["lat"], lon=k["lon"], l1=k["l1"], clear=float(km.mean()),
                             loss=kl, cluster_m2=kc, per_class=per_class(kd, km, kcls)))
        row = dict(uid=c["uid"], location=c["location"], tile=c["tile"], pre=c["pre"], post=c["post"],
                   pre_id=fa["id"], post_id=fb["id"],
                   clear=float(m.mean()), loss=loss, cluster_m2=clus, case_class_mix=w_case,
                   n_ctrl=len(ctrl), ctrl_skipped_cloud=skipped, controls=ctrl,
                   temporal_rank_s5=s5[c["uid"]].get("rank_frac"))
        if len(ctrl) < MIN_CTRL:
            row["status"] = "uncontrollable_after_cloud"
            rows.append(row)
            print(f"{c['uid']} {c['location']}: only {len(ctrl)} clear controls")
            continue
        row["status"] = "tested"
        cl = [k["loss"] for k in ctrl]
        cc = [k["cluster_m2"] for k in ctrl]
        # S1w: reweight each control's per-class LOSS to the case class mix
        pool = {}
        for k in ctrl:
            for cl_, (a, b) in k["per_class"].items():
                pa, pb = pool.get(cl_, (0, 0))
                pool[cl_] = (pa + a, pb + b)
        cw = []
        for k in ctrl:
            s = 0.0
            for cl_, w in w_case.items():
                a, b = k["per_class"].get(cl_, (0, 0))
                if b < 50:   # class absent or <0.5 ha in this box: use pooled rate
                    a, b = pool.get(cl_, (0, 0))
                s += w * (a / b if b else 0.0)
            cw.append(s)
        row.update(rank_S1=rank_frac(loss, cl), rank_S2=rank_frac(clus, cc), rank_S1w=rank_frac(loss, cw),
                   ctrl_loss_median=float(np.median(cl)), ctrl_cluster_median=float(np.median(cc)),
                   ctrl_loss_w_median=float(np.median(cw)), ctrl_loss_w=cw)
        # injection power
        clear_idx = np.argwhere(m & np.isfinite(d))
        inj = {}
        for area in AREAS + AREAS_EXT:
            r_px = math.sqrt(area / math.pi) / 10.0
            hit1 = hit2 = 0
            for _ in range(N_INJ):
                cy, cx = clear_idx[np_rng.integers(len(clear_idx))]
                dd = d.copy()
                dk = disc(d.shape, cy, cx, max(r_px, 0.5))
                dd[dk] = dd[dk] - INJ_DROP
                l2, c2 = stats(dd, m)
                hit1 += l2 > max(cl)
                hit2 += c2 > max(cc)
            inj[area] = dict(S1=hit1 / N_INJ, S2=hit2 / N_INJ)
        row["injection_first_rank_rate"] = inj
        rows.append(row)
        print(f"{c['uid']:13s} {c['location'][:15]:15s} LOSS={loss:.4f} (ctrl med {np.median(cl):.4f}, w {np.median(cw):.4f}) "
              f"clus={clus:.0f} (med {np.median(cc):.0f})  rank S1={row['rank_S1']:.2f} S2={row['rank_S2']:.2f} "
              f"S1w={row['rank_S1w']:.2f}  temporal={row['temporal_rank_s5']:.2f}  n={len(ctrl)} skip={skipped}")
        print("    inj first-rank rate:", {a: (v['S1'], v['S2']) for a, v in inj.items()})

    tested = [r for r in rows if r.get("status") == "tested"]
    summ = dict(tier=TIER, tested=len(tested), cases=[r["uid"] for r in tested])

    def combined(key):
        obs = sum(r[key] for r in tested)
        sims = []
        for _ in range(100000):
            s = 0.0
            for r in tested:
                k = r["n_ctrl"] + 1
                s += (rng.randrange(k) + 0.5) / k
            sims.append(s)
        return dict(mean_rank=obs / len(tested), p_one_sided=(sum(x >= obs for x in sims) + 1) / (len(sims) + 1))

    if tested:
        for key in ("rank_S1", "rank_S2", "rank_S1w"):
            summ[key] = combined(key)
        eff = [r["loss"] - r["ctrl_loss_median"] for r in tested]
        bs = sorted(float(np.mean([rng.choice(eff) for _ in eff])) for _ in range(10000))
        summ["effect_loss_minus_ctrl_median"] = float(np.mean(eff))
        summ["effect_ci95"] = (bs[249], bs[9749])
        mde = {}
        for st in ("S1", "S2"):
            per = {}
            for r in tested:
                ok = [a for a in AREAS + AREAS_EXT if r["injection_first_rank_rate"][a][st] >= 0.8]
                per[r["uid"]] = min(ok) if ok else None
            mde[st] = per
        summ["mde_m2_first_rank_80pct"] = mde
    print(json.dumps(summ, indent=1))
    json.dump(dict(summary=summ, control_set_sha256=got,
                   design=dict(n_ctrl=N_CTRL, min_ctrl=MIN_CTRL, min_clear=MIN_CLEAR, thr=THR,
                               areas_prereg=AREAS, areas_extension=AREAS_EXT, n_inj=N_INJ, drop=INJ_DROP),
                   rows=rows), open(OUT, "w"), indent=1, default=str)
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
