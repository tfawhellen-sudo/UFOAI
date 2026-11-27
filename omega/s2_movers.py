#!/usr/bin/env python3
"""Sentinel-2 moving-object detector (inter-band parallax), Project Omega session 7.

PHYSICS
-------
Sentinel-2 MSI does not image all bands at once. Its bands sit in a line on the
focal plane, so a ground point is seen by B02, then B08, then B03, then B04, at
offsets of roughly 0, 0.26, 0.53 and 1.0 s (Heiselberg 2019, Remote Sens.
11:1-?; the exact ratios are re-fitted from the data below, not assumed).
Anything that moves in that second appears at a different place in each band:
an aircraft at 250 m/s leaves a blue, a near-infrared, a green and a red copy
of itself in a straight line, ~25 px long. Stationary ground features do not.

That gives a falsifiable kinematic test of "objects in the sky that nobody
noticed": every compact moving object in a scene can be found, and its ground
speed measured from the B02 -> B04 displacement.

DETECTOR
--------
1. Each band: high-pass = band - 15x15 box mean. Robust sigma from the MAD.
2. Peaks: local maxima (5x5) above K sigma, outside cloud / cirrus / saturated
   / no-data in the scene classification (SCL), dilated 3 px.
3. A MOVER is a B02 peak p0 with a B04 peak p4 at 3..RMAX px such that
   B03 has a peak within TOL px of p0 + r3 (p4 - p0) AND B08 has a peak within
   TOL px of p0 + r8 (p4 - p0). r3, r8 are the band-time ratios. Four
   collinear peaks in the right order with the right spacing; noise does not
   do this (the false-alarm rate is measured by scrambling, see `scramble`).
4. Apparent speed v = |p4 - p0| * 10 m / dt04.

KNOWN BIAS
----------
Parallax: B02 and B04 look at the ground from angles that differ by ~0.5 deg
along-track. An object at height h is displaced by ~h * 0.0085 even if it does
not move. At 11 km that is ~90 m (9 px): a 1-sigma-ish speed error of ~90 m/s
for cruise traffic, along the orbit direction. A stationary balloon at 30 km
would appear as a ~250 m/s 'mover' heading along the ground track. Headings
are therefore reported, and along-track 'movers' are flagged.
"""
import json
import os
import sys
import time

import numpy as np
import rasterio
from rasterio.enums import Resampling
from scipy import ndimage
from scipy.spatial import cKDTree

K = float(os.environ.get("S2M_K", "6"))
RMAX = 220          # px; 2.2 km in ~1 s, i.e. up to ~Mach 6.5
TOL = 1.8           # px
R3, R8 = 0.524, 0.263   # nominal; refitted in analysis
DT04 = 1.005        # s, nominal B02->B04
BAD_SCL = (0, 1, 3, 8, 9, 10)   # nodata, saturated, cloud shadow, cloud med/high, cirrus
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")


def read(href, window=None, out_shape=None):
    with rasterio.open(href) as s:
        if out_shape is not None:
            return s.read(1, window=window, out_shape=out_shape,
                          resampling=Resampling.nearest)
        return s.read(1, window=window), s.transform if window is None else s.window_transform(window), s.crs


THR = float(os.environ.get("S2M_THR", "150"))   # DN (reflectance x 1e4) above local mean


def _hp(a):
    f = a.astype(np.float32)
    return f - ndimage.uniform_filter(f, 15)


def _peaks(E, bad, thr):
    mx = ndimage.maximum_filter(E, 5)
    ys, xs = np.nonzero((E >= mx) & (E > thr) & ~bad)
    return np.column_stack([ys, xs]).astype(np.float32)


def subpix(hp, p):
    """3x3 centroid refinement."""
    out = []
    H, W = hp.shape
    for y, x in p.astype(int):
        y0, y1, x0, x1 = max(y - 1, 0), min(y + 2, H), max(x - 1, 0), min(x + 2, W)
        w = np.clip(hp[y0:y1, x0:x1], 0, None)
        if w.sum() <= 0:
            out.append((y, x)); continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        out.append(((w * yy).sum() / w.sum(), (w * xx).sum() / w.sum()))
    return np.array(out, np.float32).reshape(-1, 2)


def match(P, r3=R3, r8=R8, rmax=RMAX, tol=TOL):
    """Anchor on the two colour-EXCLUSIVE peak sets (B02, B03): a mover is bright
    in blue where green/red are not, and vice versa. The B02->B03 vector d3 then
    predicts B04 at d3/r3 and B08 at d3*r8/r3; both must hold an ordinary peak."""
    p0, p3, p4, p8 = P["B02x"], P["B03x"], P["B04"], P["B08"]
    if min(len(p0), len(p3), len(p4), len(p8)) == 0:
        return []
    t3, t4, t8 = cKDTree(p3), cKDTree(p4), cKDTree(p8)
    lists = t3.query_ball_point(p0, rmax * r3)
    I = np.repeat(np.arange(len(lists)), [len(l) for l in lists])
    if I.size == 0:
        return []
    K3 = np.fromiter((j for l in lists for j in l), dtype=np.int64, count=I.size)
    D3 = p3[K3] - p0[I]
    k = np.hypot(D3[:, 0], D3[:, 1]) >= 3 * r3
    I, K3, D3 = I[k], K3[k], D3[k]
    D = D3 / r3
    e4, k4 = t4.query(p0[I] + D, distance_upper_bound=tol / r3 * 0.6 + tol)
    k = np.isfinite(e4)
    I, K3, D, e4, k4 = I[k], K3[k], D[k], e4[k], k4[k]
    e8, k8 = t8.query(p0[I] + r8 * D, distance_upper_bound=tol)
    k = np.isfinite(e8)
    rows = []
    for i, j3, j4, e4_, j8, e8_ in zip(I[k], K3[k], k4[k], e4[k], k8[k], e8[k]):
        a = p0[i]; d = p4[j4] - a; n = float(np.hypot(*d))
        if n < 3:
            continue
        rows.append(dict(i0=int(i), i4=int(j4), y0=float(a[0]), x0=float(a[1]),
                         dy=float(d[0]), dx=float(d[1]), dpx=n,
                         f3=float(np.dot(p3[j3] - a, d) / n / n),
                         f8=float(np.dot(p8[j8] - a, d) / n / n),
                         e4=float(e4_), e8=float(e8_)))
    rows.sort(key=lambda m: m["e4"] + m["e8"])
    s0, s4, keep = set(), set(), []
    for m in rows:
        if m["i0"] in s0 or m["i4"] in s4:
            continue
        s0.add(m["i0"]); s4.add(m["i4"]); keep.append(m)
    return keep


def scene(A, window=None, thr=THR):
    from rasterio.windows import Window
    with rasterio.open(A["B02"]) as s:
        if window is None:
            window = Window(0, 0, s.width, s.height)
        tr = s.window_transform(window); crs = s.crs
        shape = (int(window.height), int(window.width))
    with rasterio.open(A["scl"]) as s:
        w20 = Window(window.col_off / 2, window.row_off / 2, window.width / 2, window.height / 2)
        scl = s.read(1, window=w20, out_shape=shape, resampling=Resampling.nearest)
    bad = ndimage.binary_dilation(np.isin(scl, BAD_SCL), iterations=3)
    info = dict(clear=float((~bad).mean()), water=float((scl == 6).mean()))
    del scl
    HP = {}
    for b in ("B02", "B03", "B04", "B08"):
        with rasterio.open(A[b]) as s:
            HP[b] = _hp(s.read(1, window=window))
    P = {}
    for b in ("B02", "B03"):
        o = np.maximum.reduce([HP[j] for j in ("B02", "B03", "B04") if j != b])
        E = HP[b] - ndimage.maximum_filter(o, 3)
        del o
        P[b + "x"] = subpix(HP[b], _peaks(E, bad, thr))
        del E
    for b in ("B04", "B08"):
        P[b] = subpix(HP[b], _peaks(HP[b], bad, thr))
    return P, info, tr, crs, bad


if __name__ == "__main__":
    print("library module; see s2_hunt.py")
