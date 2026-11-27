#!/usr/bin/env python3
"""Session 7 hunt: moving objects in Sentinel-2 at (a) report/overpass coincidences
and (b) sensitive and sacred sites. Resume-safe: one JSON line per job.

Each job = one scene + one centre point. A 60 km window around the point is read.
Two detector modes (see s2_movers.py):
  water: aircraft over open water (land/cloud blobs masked, 300 m coast buffer).
         Validated on the Channel: false-alarm rate ~0.3 per half tile by scrambling.
  land : all three visible peaks must be colour-exclusive, threshold 250 DN.
         Its false-alarm rate is measured per job by scrambling B04 10 times.
NULL MODEL (within scene, same instant, same weather): movers within R_KM of the
centre vs within R_KM of 30 random centres in the same window, rates per usable
pixel. For sites, H1 = more movers or more fast movers at the site than at random
points of the same scene.
Usage: python3 -I omega/s2_hunt.py jobs.json out.jsonl [workers]
"""
import json, os, sys, traceback, multiprocessing as mp
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s2_movers as M
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform as wtransform
from scipy import ndimage

HALF = 3000      # px -> 60 km window
R_KM = 10.0
NRAND = 30
VFAST = 400.0    # m/s
CHIPDIR = os.environ.get("S2H_CHIPS", "")


def big(m, r):
    return ndimage.binary_opening(m, structure=np.ones((r, r)))


def masks(A, win):
    w20 = Window(win.col_off // 2, win.row_off // 2, (win.width + 1) // 2 + 1, (win.height + 1) // 2 + 1)
    with rasterio.open(A["scl"]) as s:
        scl = s.read(1, window=w20, boundless=True, fill_value=0)
    nod = scl == 0
    cloud = big(np.isin(scl, (3, 8, 9, 10)), 9)
    land = big(np.isin(scl, (2, 4, 5, 7)), 5)
    oy, ox = int(win.row_off) % 2, int(win.col_off) % 2
    up = lambda m: np.kron(m, np.ones((2, 2), bool)).astype(bool)[oy:oy + int(win.height), ox:ox + int(win.width)]
    badw = up(ndimage.binary_dilation(land | cloud | nod, iterations=15))   # 300 m coast/cloud buffer
    badl = up(ndimage.binary_dilation(cloud | nod | (scl == 6) | (scl == 1), iterations=3))
    return badw, badl, float((scl == 6).mean())


def detect(HP, bad, mode):
    P = {}
    thr = 100 if mode == "water" else 250
    vis = ("B02", "B03", "B04")
    for b in vis:
        if mode == "water" and b == "B04":
            P["B04"] = M.subpix(HP[b], M._peaks(HP[b], bad, thr)); continue
        o = np.maximum.reduce([HP[j] for j in vis if j != b])
        E = HP[b] - ndimage.maximum_filter(o, 3); del o
        P[b if b == "B04" else b + "x"] = M.subpix(HP[b], M._peaks(E, bad, thr)); del E
    P["B08"] = M.subpix(HP["B08"], M._peaks(HP["B08"], bad, thr))
    m = M.match(P)
    rng = np.random.default_rng(0); fa = []
    for _ in range(10):
        Q = dict(P); Q["B04"] = P["B04"] + rng.uniform(-400, 400, 2).astype(np.float32)
        fa.append(len(M.match(Q)))
    return m, fa, {k: len(v) for k, v in P.items()}


def chip(HP, y, x, path):
    from PIL import Image
    r = 40; H, W = HP["B02"].shape
    y, x = int(min(max(y, r), H - r)), int(min(max(x, r), W - r))
    rgb = np.stack([HP[k][y - r:y + r, x - r:x + r] for k in ("B04", "B03", "B02")], -1)
    rgb = (np.clip((rgb + 100) / 700, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(rgb).resize((240, 240), Image.NEAREST).save(path)


def run(job):
    A = job["assets"]
    with rasterio.open(A["B02"]) as s:
        (cx,), (cy,) = wtransform("EPSG:4326", s.crs, [job["lon"]], [job["lat"]])
        r, c = s.index(cx, cy)
        r0, c0 = max(r - HALF, 0), max(c - HALF, 0)
        r1, c1 = min(r + HALF, s.height), min(c + HALF, s.width)
        if r1 - r0 < 1000 or c1 - c0 < 1000:
            return dict(job_id=job["job_id"], skip="point near tile edge / outside")
        win = Window(c0, r0, c1 - c0, r1 - r0); tr = s.window_transform(win); crs = s.crs
    badw, badl, water = masks(A, win)
    HP = {}
    for b in ("B02", "B03", "B04", "B08"):
        with rasterio.open(A[b]) as s:
            HP[b] = M._hp(s.read(1, window=win))
    py, px = r - r0, c - c0
    H, W = HP["B02"].shape
    rng = np.random.default_rng(abs(hash(job["job_id"])) % 2**32)
    cen = [(py, px)] + [(rng.uniform(0, H), rng.uniform(0, W)) for _ in range(NRAND)]
    RP = R_KM * 100
    yy, xx = np.mgrid[0:H:10, 0:W:10]
    out = dict(job_id=job["job_id"], kind=job["kind"], label=job.get("label"), scene=job["scene"],
               lat=job["lat"], lon=job["lon"], water_frac=water, win=[r0, c0, H, W], modes={})
    for mode, bad in (("water", badw), ("land", badl)):
        usable = ~bad[::10, ::10]
        if usable.mean() < 0.02:
            out["modes"][mode] = dict(skip="no usable pixels"); continue
        m, fa, npk = detect(HP, bad, mode)
        movers = []
        for k in m:
            yc, xc = k["y0"] + k["dy"] / 2, k["x0"] + k["dx"] / 2
            X, Y = tr * (xc + 0.5, yc + 0.5)
            (lo,), (la,) = wtransform(crs, "EPSG:4326", [X], [Y])
            v = k["dpx"] * 10 / M.DT04
            hd = float(np.degrees(np.arctan2(k["dx"], -k["dy"])) % 360)
            dc = float(np.hypot(yc - py, xc - px) / 100)
            movers.append(dict(lat=la, lon=lo, v=round(v, 1), hd=round(hd, 1), d_km=round(dc, 2),
                               f3=round(k["f3"], 3), f8=round(k["f8"], 3), y=round(yc), x=round(xc)))
        disks = []
        for (cy_, cx_) in cen:
            dm = (yy - cy_) ** 2 + (xx - cx_) ** 2 <= RP ** 2
            upx = int((dm & usable).sum()) * 100
            pts = [mv for mv in movers if (mv["y"] - cy_) ** 2 + (mv["x"] - cx_) ** 2 <= RP ** 2]
            disks.append(dict(usable_px=upx, n=len(pts), n_air=sum(p["v"] >= 60 for p in pts),
                              n_fast=sum(p["v"] >= VFAST for p in pts)))
        if CHIPDIR:
            os.makedirs(CHIPDIR, exist_ok=True)
            sel = [mv for mv in movers if mv["v"] >= VFAST] + [mv for mv in movers if mv["d_km"] <= R_KM and 60 <= mv["v"] < VFAST][:20]
            for i, mv in enumerate(sel[:40]):
                fn = f"{job['job_id']}_{mode}_{i}_v{int(mv['v'])}.png".replace("#", "_").replace("/", "_")
                chip(HP, mv["y"], mv["x"], os.path.join(CHIPDIR, fn)); mv["chip"] = fn
        out["modes"][mode] = dict(usable=float(usable.mean()), peaks=npk, n=len(movers), fa=fa,
                                  disks=disks, movers=movers)
    return out


def safe(job):
    try:
        return run(job)
    except Exception as e:
        return dict(job_id=job["job_id"], error=repr(e)[:300], tb=traceback.format_exc()[-600:])


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1])); outp = sys.argv[2]
    nw = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    done = set()
    if os.path.exists(outp):
        for l in open(outp):
            try:
                d = json.loads(l)
                if "error" not in d: done.add(d["job_id"])
            except Exception:
                pass
    todo = [j for j in jobs if j["job_id"] not in done]
    print("todo", len(todo), "done", len(done), flush=True)
    with mp.Pool(nw, maxtasksperchild=1) as pool, open(outp, "a") as f:
        for i, res in enumerate(pool.imap_unordered(safe, todo)):
            f.write(json.dumps(res) + "\n"); f.flush()
            print(i, res["job_id"], res.get("error") or res.get("skip") or
                  {k: v.get("n") for k, v in res.get("modes", {}).items()}, flush=True)
