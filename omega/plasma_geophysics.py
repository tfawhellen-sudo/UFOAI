#!/usr/bin/env python3
"""Plasma hypothesis: do ORB / LIGHT reports behave like geophysical plasma?

Ball lightning and earthquake lights (EQL) are real, if poorly understood.
If a fraction of "orb" UAP reports were EQL-like or geomagnetically driven,
orb reports should, RELATIVE TO OTHER REPORTS FROM THE SAME SYSTEM:
  T1  sit closer to active faults,
  T2  be over-represented on geomagnetic storm days (Kp >= 5),
  T3  be over-represented in the days just before nearby earthquakes, and
  T3b rise in Oklahoma when induced seismicity rose ~100x (2009-2014),
      against neighbouring states (difference-in-differences).

THE NULL THAT MATTERS
---------------------
Raw report counts track population, sky-watching habits and media.  So every
test has a WITHIN-SYSTEM control class drawn from the same reporters, places
and years:
  NUFORC  orb   = shape in {light, fireball, sphere, flash}
          craft = shape in {triangle, disk, cigar, cylinder, chevron,
                            rectangle, diamond, cone, cross, delta}
  GEIPAN  orb   = Details mention boule/sphere/globe/orbe/lumiere/point
                  lumineux and NO craft word; craft = craft word, no orb word.
          Unexplained (C/D) orbs are also compared with IDENTIFIED (A/B)
          orbs, which are mostly Thai lanterns, Venus and aircraft. A/B orbs
          went through the same reporting pipe but are NOT plasma, so any
          geophysical association they share is a reporting artifact.
A population-weighted null (GeoNames places >= 1,000 inhabitants, weighted by
population) and a calendar null (same year-month) are reported alongside.

Uncertainty: cluster bootstrap (clusters = report date for time tests,
location for space tests; 2,000 reps).  Effect sizes are odds ratios (OR) or
observed/expected ratios with 95% CIs.

DATA (hosts reached and their provenance are in plasma_geophysics_manifest
inside the output JSON; USGS, GFZ, NOAA, OSM, BRGM and the French seismic
catalogue servers were all refused by this environment's proxy):
  GEIPAN   data/raw/geipan/geipan_cases.json (3,404 cases, project copy)
  NUFORC   planetsig/ufo-reports geocoded+time-standardised scrub
           (80,332 records, 1910 - May 2014), GitHub raw
  Faults   GEM Global Active Faults, harmonised GeoJSON, GitHub raw
  Kp       CelesTrak SW-All.txt (Kp from GFZ Potsdam), bundled in PyPI
           package spaceweather 0.4.2
  Quakes   liveatlasearth/earthquake-catalogs (USGS ComCat extractions,
           frozen 2026-10-29), GitHub raw
  People   all-the-cities 3.1.0 (GeoNames cities1000), npm registry

Usage: OMEGA_GEO=<dir with the fetched files> python3 -I omega/plasma_geophysics.py
Writes: evidence_vault/11_PLASMA_GEOPHYSICS/plasma_geophysics.json
"""
import csv, datetime as dt, hashlib, json, math, os, re, sys, collections
import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.environ.get("OMEGA_GEO")
if not GEO:
    sys.exit("set OMEGA_GEO to the fetch directory (see evidence_vault/11_PLASMA_GEOPHYSICS/FETCH_MANIFEST.json)")
OUT = os.path.join(ROOT, "evidence_vault", "11_PLASMA_GEOPHYSICS", "plasma_geophysics.json")
RNG = np.random.default_rng(20261126)
NBOOT = 2000
R_EARTH = 6371.0

# ---------------------------------------------------------------- utilities
def xyz(lat, lon):
    lat = np.radians(np.asarray(lat, float)); lon = np.radians(np.asarray(lon, float))
    return np.c_[np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)]

def chord_to_km(c):
    return 2 * R_EARTH * np.arcsin(np.clip(c / 2, 0, 1))

def km_to_chord(k):
    return 2 * np.sin(k / (2 * R_EARTH))

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def odds_ratio(a, b):
    """a, b: boolean arrays (exposed?) for case and control groups."""
    a1, a0 = a.sum(), (~a).sum(); b1, b0 = b.sum(), (~b).sum()
    return ((a1 + .5) * (b0 + .5)) / ((a0 + .5) * (b1 + .5))

def cluster_boot(fn, groups, n=NBOOT):
    """groups: list of (values, cluster_ids). fn(*resampled_values) -> stat.
    Each group is resampled by cluster independently."""
    idx = []
    for v, c in groups:
        u, inv = np.unique(c, return_inverse=True)
        members = [np.flatnonzero(inv == k) for k in range(len(u))] if len(u) < 5000 else None
        idx.append((v, inv, len(u), members))
    stats = []
    for _ in range(n):
        res = []
        for v, inv, k, members in idx:
            pick = RNG.integers(0, k, k)
            if members is not None:
                sel = np.concatenate([members[p] for p in pick]) if k else np.array([], int)
            else:
                w = np.bincount(pick, minlength=k)[inv]
                sel = np.repeat(np.arange(len(inv)), w)
            res.append(v[sel])
        stats.append(fn(*res))
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return float(lo), float(hi)

def or_test(a, ca, b, cb):
    """OR of exposure a (case) vs b (control) with cluster-bootstrap CI."""
    est = odds_ratio(a, b)
    lo, hi = cluster_boot(odds_ratio, [(a, ca), (b, cb)])
    return {"n_case": int(len(a)), "n_ctrl": int(len(b)),
            "p_case": round(float(a.mean()), 4) if len(a) else None,
            "p_ctrl": round(float(b.mean()), 4) if len(b) else None,
            "OR": round(float(est), 3), "CI95": [round(lo, 3), round(hi, 3)]}

def mh_or(z):
    """Mantel-Haenszel OR. z columns: exposure, is_case, stratum."""
    num = den = 0.0
    for st in np.unique(z[:, 2]):
        m = z[:, 2] == st
        e, c = z[m, 0].astype(bool), z[m, 1].astype(bool)
        n = m.sum()
        a = (e & c).sum(); b = (e & ~c).sum(); cc = (~e & c).sum(); d = (~e & ~c).sum()
        num += a * d / n; den += b * cc / n
    return num / den if den else float("nan")

def mh_test(exp_case, exp_ctrl, strat_case, strat_ctrl, clus_case, clus_ctrl):
    """Stratified (e.g. by year) OR, cluster bootstrap over the pooled set."""
    z = np.c_[np.r_[exp_case, exp_ctrl].astype(float),
              np.r_[np.ones(len(exp_case)), np.zeros(len(exp_ctrl))],
              np.r_[strat_case, strat_ctrl].astype(float)]
    cl = np.r_[clus_case, clus_ctrl]
    est = mh_or(z)
    lo, hi = cluster_boot(mh_or, [(z, cl)], n=500)
    return {"MH_OR": round(float(est), 3), "CI95": [round(lo, 3), round(hi, 3)]}

# ---------------------------------------------------------------- loaders
def load_faults():
    g = json.load(open(os.path.join(GEO, "faults", "gem.geojson")))
    pts = []
    for f in g["features"]:
        c = np.asarray(f["geometry"]["coordinates"], float)[:, :2]
        for (x0, y0), (x1, y1) in zip(c[:-1], c[1:]):
            seg = math.hypot((x1 - x0) * math.cos(math.radians(y0)), y1 - y0) * 111.2
            k = max(1, int(seg))          # <= ~1 km spacing
            t = np.linspace(0, 1, k + 1)
            pts.append(np.c_[y0 + (y1 - y0) * t, x0 + (x1 - x0) * t])
    p = np.vstack(pts)
    return cKDTree(xyz(p[:, 0], p[:, 1])), len(g["features"])

def load_kp():
    rows = {}
    on = False
    for line in open(os.path.join(GEO, "kp", "spaceweather", "data", "SW-All.txt")):
        if line.startswith("BEGIN OBSERVED"):
            on = True; continue
        if line.startswith("END OBSERVED"):
            break
        if not on:
            continue
        f = line.split()
        d = dt.date(int(f[0]), int(f[1]), int(f[2]))
        kp = [int(x) for x in f[5:13]]           # Kp*10, 3-hour slots from 00 UT
        rows[d] = (kp, int(f[21]))               # daily Ap
    return rows

def load_cities(cc):
    lat, lon, pop = [], [], []
    for line in open(os.path.join(GEO, "pop", "cities.tsv"), encoding="utf8"):
        f = line.rstrip("\n").split("\t")
        if f[2] == cc and int(f[5]) > 0:
            lat.append(float(f[6])); lon.append(float(f[7])); pop.append(int(f[5]))
    return np.array(lat), np.array(lon), np.array(pop, float)

FR_BOX = (41.2, 51.2, -5.5, 9.8)
US_BOX = (24.0, 49.5, -125.0, -66.5)
def inbox(lat, lon, b):
    return (lat >= b[0]) & (lat <= b[1]) & (lon >= b[2]) & (lon <= b[3])

ORB_FR = re.compile(r"\b(boules?|sph[eè]res?|sph[ée]riques?|globes?|orbes?|points? lumineux|lumi[eè]res?|boules? de feu)\b", re.I)
CRAFT_FR = re.compile(r"\b(triangles?|triangulaires?|disques?|soucoupes?|cigares?|engins?|hublots?|rectangulaires?|losanges?|structures?|c[ôo]nes?|cylindres?|chevrons?)\b", re.I)

def load_geipan():
    d = json.load(open(os.path.join(ROOT, "data", "raw", "geipan", "geipan_cases.json")))
    out = []
    for r in d:
        t = r["Détails"] + " " + r["Identification"]
        o, k = bool(ORB_FR.search(t)), bool(CRAFT_FR.search(t))
        m = re.match(r"(\d\d)/(\d\d)/(\d{4})$", r["Observation date"])
        date = None
        if m:
            try: date = dt.date(int(m[3]), int(m[2]), int(m[1]))
            except ValueError: date = None
        out.append(dict(id=r["ID Etude de Cas"], lat=r["Latitude"], lon=r["Longitude"],
                        cls=r["Classification"], dept=r["Department"], date=date,
                        kind="orb" if o and not k else "craft" if k and not o else "other",
                        hour=None))
    return out

ORB_US = {"light", "fireball", "sphere", "flash"}
CRAFT_US = {"triangle", "disk", "cigar", "cylinder", "chevron", "rectangle",
            "diamond", "cone", "cross", "delta"}

def load_nuforc():
    out = []
    with open(os.path.join(GEO, "nuforc", "scrubbed.csv"), encoding="utf8", errors="replace") as f:
        for r in csv.reader(f):
            if len(r) < 11 or r[3] != "us":
                continue
            try:
                lat, lon = float(r[9]), float(r[10])
                ds, ts = r[0].split()
                mo, da, yr = map(int, ds.split("/"))
                hh = int(ts.split(":")[0])
                date = dt.date(yr, mo, da)
            except (ValueError, IndexError):
                continue
            if hh == 24:
                hh = 0; date = date + dt.timedelta(days=1)
            s = r[4].strip().lower()
            out.append(dict(lat=lat, lon=lon, date=date, hour=hh, state=r[2].upper(),
                            city=r[1], shape=s,
                            kind="orb" if s in ORB_US else "craft" if s in CRAFT_US else "other"))
    return out

def load_quakes(name):
    q = []
    with open(os.path.join(GEO, "eq", name + ".csv")) as f:
        for r in csv.DictReader(f):
            try:
                t = dt.datetime.strptime(r["time"][:19], "%Y-%m-%dT%H:%M:%S")
                q.append((t, float(r["latitude"]), float(r["longitude"]), float(r["magnitude"])))
            except (ValueError, KeyError):
                continue
    return q

# ---------------------------------------------------------------- T1 faults
def t1_faults(tree, recs, box, cc, label, groups):
    lat = np.array([r["lat"] for r in recs]); lon = np.array([r["lon"] for r in recs])
    ok = inbox(lat, lon, box)
    recs = [r for r, k in zip(recs, ok) if k]
    lat, lon = lat[ok], lon[ok]
    d, _ = tree.query(xyz(lat, lon))
    dist = chord_to_km(d)
    loc = np.round(lat, 2) * 1000 + np.round(lon, 2)
    # population-weighted null
    clat, clon, pop = load_cities(cc)
    m = inbox(clat, clon, box); clat, clon, pop = clat[m], clon[m], pop[m]
    cd = chord_to_km(tree.query(xyz(clat, clon))[0])
    res = {"label": label, "n_in_box": int(len(recs)),
           "median_km": {}, "tests": {}}
    for R in (10, 25, 50):
        w = pop / pop.sum()
        res.setdefault("pop_null_share_within", {})[f"{R}km"] = round(float((w * (cd <= R)).sum()), 4)
    for gname, (ga, gb) in groups.items():
        ia = np.array([ga(r) for r in recs]); ib = np.array([gb(r) for r in recs])
        res["median_km"][gname] = [round(float(np.median(dist[ia])), 1), round(float(np.median(dist[ib])), 1)]
        for R in (10, 25, 50):
            res["tests"][f"{gname}|{R}km"] = or_test(dist[ia] <= R, loc[ia], dist[ib] <= R, loc[ib])
        reg = np.array([hash(r.get("state") or r.get("dept")) % 100003 for r in recs])
        for R in (10, 25, 50):
            res["tests"][f"{gname}|{R}km|MH_by_region"] = mh_test(dist[ia] <= R, dist[ib] <= R, reg[ia], reg[ib], loc[ia], loc[ib])
        if cc == "US":
            w = lon < -104   # GEM/USGS fault mapping is dense only in the West
            for R in (10, 25, 50):
                res["tests"][f"{gname}|{R}km|west_of_104W|MH_by_state"] = mh_test(
                    dist[ia & w] <= R, dist[ib & w] <= R, reg[ia & w], reg[ib & w], loc[ia & w], loc[ib & w])
    allm = np.array([r["kind"] == "orb" for r in recs])
    for R in (10, 25, 50):
        res.setdefault("orb_share_within_vs_pop", {})[f"{R}km"] = {
            "orb_share": round(float((dist[allm] <= R).mean()), 4),
            "all_reports_share": round(float((dist <= R).mean()), 4),
            "pop_null_share": res["pop_null_share_within"][f"{R}km"]}
    return res, dist, recs

# ---------------------------------------------------------------- T2 Kp
def t2_kp(kp, recs, label, groups):
    days = sorted(kp)
    storm_day = {d: max(kp[d][0]) >= 50 for d in days}
    # calendar null: storm-day fraction per (year, month)
    ym = collections.defaultdict(list)
    for d in days:
        ym[(d.year, d.month)].append(storm_day[d])
    ymp = {k: float(np.mean(v)) for k, v in ym.items()}
    recs = [r for r in recs if r["date"] is not None and r["date"] in kp]
    storm = np.array([storm_day[r["date"]] for r in recs])
    exp = np.array([ymp[(r["date"].year, r["date"].month)] for r in recs])
    # 3-hour slot (NUFORC only; local hour -> UT by longitude, +-1 slot slop)
    slot = []
    for r in recs:
        if r["hour"] is None:
            slot.append(np.nan); continue
        ut = r["hour"] - r["lon"] / 15.0
        d = r["date"]
        if ut >= 24: ut -= 24; d = d + dt.timedelta(days=1)
        if ut < 0: ut += 24; d = d - dt.timedelta(days=1)
        slot.append(kp[d][0][int(ut // 3)] / 10 if d in kp else np.nan)
    slot = np.array(slot)
    clus = np.array([r["date"].toordinal() for r in recs])
    res = {"label": label, "n_dated": int(len(recs)), "storm_def": "daily max Kp >= 5 (G1+)",
           "calendar_null": {}, "tests": {}}
    for gname, (ga, gb) in groups.items():
        ia = np.array([ga(r) for r in recs]); ib = np.array([gb(r) for r in recs])
        for nm, sel in (("case", ia), ("ctrl", ib)):
            o, e = storm[sel].sum(), exp[sel].sum()
            # bootstrap O/E jointly (clusters = dates)
            v = np.c_[storm[sel], exp[sel]]
            lo, hi = cluster_boot(lambda z: z[:, 0].sum() / max(z[:, 1].sum(), 1e-9), [(v, clus[sel])])
            res["calendar_null"][f"{gname}|{nm}"] = {"n": int(sel.sum()), "obs_storm": int(o),
                                                     "exp_storm": round(float(e), 1),
                                                     "O/E": round(float(o / e), 3) if e else None,
                                                     "CI95": [round(lo, 3), round(hi, 3)]}
        res["tests"][f"{gname}|storm_day"] = or_test(storm[ia], clus[ia], storm[ib], clus[ib])
        yr = np.array([r["date"].year for r in recs])
        res["tests"][f"{gname}|storm_day|MH_by_year"] = mh_test(storm[ia], storm[ib], yr[ia], yr[ib], clus[ia], clus[ib])
        if np.isfinite(slot).any():
            fa, fb = np.isfinite(slot) & ia, np.isfinite(slot) & ib
            res["tests"][f"{gname}|slot_Kp>=5"] = or_test(slot[fa] >= 5, clus[fa], slot[fb] >= 5, clus[fb])
            res["tests"][f"{gname}|slot_Kp>=7"] = or_test(slot[fa] >= 7, clus[fa], slot[fb] >= 7, clus[fb])
    return res

# ---------------------------------------------------------------- T3 quakes
def t3_quakes(recs, quakes, box, mmin, R, label, pre=14, post=3, nshift=200):
    recs = [r for r in recs if r["date"] and inbox(np.array(r["lat"]), np.array(r["lon"]), box)]
    q = [x for x in quakes if x[3] >= mmin]
    if not q or not recs:
        return {"label": label, "n": 0}
    qt0, qt1 = min(x[0] for x in q).date(), max(x[0] for x in q).date()
    recs = [r for r in recs if qt0 + dt.timedelta(days=post) <= r["date"] <= qt1 - dt.timedelta(days=pre)]
    qtree = cKDTree(xyz([x[1] for x in q], [x[2] for x in q]))
    qday = np.array([x[0].date().toordinal() for x in q])
    rx = xyz([r["lat"] for r in recs], [r["lon"] for r in recs])
    near = qtree.query_ball_point(rx, km_to_chord(R))
    rday = np.array([r["date"].toordinal() for r in recs])

    def flags(shift):
        pr = np.zeros(len(recs), bool); po = np.zeros(len(recs), bool)
        for i, nb in enumerate(near):
            if not nb: continue
            dd = qday[nb] - (rday[i] + shift[i])
            pr[i] = ((dd >= 1) & (dd <= pre)).any()
            po[i] = ((dd >= -post) & (dd <= 0)).any()
        return pr, po
    pr, po = flags(np.zeros(len(recs), int))
    orb = np.array([r["kind"] == "orb" for r in recs]); craft = np.array([r["kind"] == "craft" for r in recs])
    res = {"label": label, "M_min": mmin, "radius_km": R, "pre_days": pre, "post_days": post,
           "quakes": len(q), "quake_span": [str(qt0), str(qt1)], "n_reports": len(recs),
           "n_orb": int(orb.sum()), "n_craft": int(craft.sum()),
           "pre": or_test(pr[orb], rday[orb], pr[craft], rday[craft]),
           "post": or_test(po[orb], rday[orb], po[craft], rday[craft])}
    yr = np.array([r["date"].year for r in recs])
    res["pre_MH_by_year"] = mh_test(pr[orb], pr[craft], yr[orb], yr[craft], rday[orb], rday[craft])
    res["post_MH_by_year"] = mh_test(po[orb], po[craft], yr[orb], yr[craft], rday[orb], rday[craft])
    # time-shift null: move each report by a random +-60..730 days, keep place
    sh_pr, sh_po = [], []
    for _ in range(nshift):
        s = RNG.integers(60, 731, len(recs)) * RNG.choice([-1, 1], len(recs))
        a, b = flags(s)
        sh_pr.append(a[orb].mean() if orb.any() else np.nan); sh_po.append(b[orb].mean() if orb.any() else np.nan)
    res["orb_vs_timeshift"] = {"obs_pre": round(float(pr[orb].mean()), 4),
                               "null_pre_mean": round(float(np.nanmean(sh_pr)), 4),
                               "null_pre_95": [round(float(x), 4) for x in np.nanpercentile(sh_pr, [2.5, 97.5])],
                               "obs_post": round(float(po[orb].mean()), 4),
                               "null_post_mean": round(float(np.nanmean(sh_po)), 4),
                               "null_post_95": [round(float(x), 4) for x in np.nanpercentile(sh_po, [2.5, 97.5])]}
    return res

def t3b_oklahoma(nuf, okq):
    """Diff-in-diff: orb share of OK reports vs neighbours, before vs during
    the induced-seismicity surge.  NUFORC scrub ends May 2014."""
    yrs = collections.Counter(x[0].year for x in okq if x[3] >= 3)
    NEIGH = {"KS", "AR", "MO", "NE", "IA", "NM", "CO"}
    def cell(st_set, y0, y1):
        o = c = 0
        for r in nuf:
            if r["state"] in st_set and y0 <= r["date"].year <= y1:
                o += r["kind"] == "orb"; c += r["kind"] == "craft"
        return o, c
    pre, dur = (2000, 2008), (2010, 2013)
    a = cell({"OK"}, *pre); b = cell({"OK"}, *dur); c = cell(NEIGH, *pre); d = cell(NEIGH, *dur)
    lor = lambda x: math.log((x[0] + .5) / (x[1] + .5))
    did = (lor(b) - lor(a)) - (lor(d) - lor(c))
    se = math.sqrt(sum(1 / (v + .5) for cell_ in (a, b, c, d) for v in cell_))
    return {"ok_m3_quakes_per_year": {str(y): yrs.get(y, 0) for y in range(2000, 2015)},
            "neighbours": sorted(NEIGH), "pre_years": pre, "surge_years": dur,
            "orb_craft_counts": {"OK_pre": a, "OK_surge": b, "NB_pre": c, "NB_surge": d},
            "DiD_log_odds": round(did, 3), "ratio_of_OR": round(math.exp(did), 3),
            "CI95": [round(math.exp(did - 1.96 * se), 3), round(math.exp(did + 1.96 * se), 3)],
            "quake_increase_factor": round((sum(yrs.get(y, 0) for y in range(*dur[:1], dur[1] + 1)) / 4)
                                           / max(sum(yrs.get(y, 0) for y in range(pre[0], pre[1] + 1)) / 9, 1e-9), 1)}

# ---------------------------------------------------------------- hotspots
def hotspots(recs, key, dist, min_n=30):
    """Orb share per region vs dataset share, binomial z, BH-adjusted."""
    from scipy.stats import binomtest
    p0 = np.mean([r["kind"] == "orb" for r in recs if r["kind"] in ("orb", "craft")])
    by = collections.defaultdict(lambda: [0, 0, []])
    for r, dd in zip(recs, dist):
        if r["kind"] not in ("orb", "craft"): continue
        b = by[r[key]]; b[0] += r["kind"] == "orb"; b[1] += 1; b[2].append(dd)
    rows = []
    for k, (o, n, ds) in by.items():
        if n < min_n: continue
        p = binomtest(o, n, p0).pvalue
        rows.append([k, o, n, o / n, p, float(np.median(ds))])
    rows.sort(key=lambda x: x[4])
    m = len(rows)
    for i, r in enumerate(rows):
        r.append(min(1.0, r[4] * m / (i + 1)))
    # monotone BH
    for i in range(m - 2, -1, -1):
        rows[i][6] = min(rows[i][6], rows[i + 1][6])
    from scipy.stats import spearmanr
    rho = spearmanr([r[3] for r in rows], [r[5] for r in rows]) if len(rows) > 3 else None
    return {"orb_share_overall": round(float(p0), 4), "min_n": min_n,
            "spearman_orbshare_vs_median_fault_km": [round(float(rho[0]), 3), float(f"{rho[1]:.3g}")] if rho else None,
            "rows": [{"region": r[0], "orb": r[1], "n_orb_plus_craft": r[2], "orb_share": round(r[3], 3),
                      "p": float(f"{r[4]:.3g}"), "q_BH": float(f"{r[6]:.3g}"),
                      "median_fault_km": round(r[5], 1)} for r in rows]}

# ---------------------------------------------------------------- main
def main():
    tree, nf = load_faults()
    kp = load_kp()
    gei = load_geipan(); nuf = load_nuforc()
    out = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "inputs": {"geipan_cases": len(gei), "nuforc_us_parsed": len(nuf), "gem_fault_traces": nf,
                      "kp_days": len(kp), "kp_span": [str(min(kp)), str(max(kp))]},
           "class_counts": {"geipan": collections.Counter(f"{r['kind']}|{r['cls']}" for r in gei),
                            "nuforc": collections.Counter(r["kind"] for r in nuf)}}

    G_GEI = {"orb_vs_craft": (lambda r: r["kind"] == "orb", lambda r: r["kind"] == "craft"),
             "unexplainedCD_orb_vs_identifiedAB_orb": (lambda r: r["kind"] == "orb" and r["cls"] in "CD",
                                                      lambda r: r["kind"] == "orb" and r["cls"] in "AB")}
    G_NUF = {"orb_vs_craft": (lambda r: r["kind"] == "orb", lambda r: r["kind"] == "craft")}

    print("T1 faults ...", flush=True)
    t1g, dg, gei_in = t1_faults(tree, gei, FR_BOX, "FR", "GEIPAN metropolitan France", G_GEI)
    t1n, dn, nuf_in = t1_faults(tree, nuf, US_BOX, "US", "NUFORC CONUS", G_NUF)
    out["T1_faults"] = [t1g, t1n]

    print("T2 Kp ...", flush=True)
    G_NUF_LAT = dict(G_NUF)
    G_NUF_LAT["orb_vs_craft_lat>=45N"] = (lambda r: r["kind"] == "orb" and r["lat"] >= 45,
                                          lambda r: r["kind"] == "craft" and r["lat"] >= 45)
    G_NUF_LAT["orb_vs_craft_lat<40N"] = (lambda r: r["kind"] == "orb" and r["lat"] < 40,
                                         lambda r: r["kind"] == "craft" and r["lat"] < 40)
    out["T2_geomagnetic"] = [t2_kp(kp, gei, "GEIPAN all France incl. overseas", G_GEI),
                             t2_kp(kp, nuf, "NUFORC US", G_NUF_LAT)]

    print("T3 quakes ...", flush=True)
    regs = [("oklahoma_m3_plus_since_2000", (33.6, 37.1, -103.1, -94.4), 3.0, 100),
            ("cascadia_m2_5_plus_since_1970", (40, 50, -131, -120), 3.0, 100),
            ("new_madrid_m2_5_plus_since_1974", (34, 39, -92.5, -86.5), 2.5, 100),
            ("yellowstone_since_1973", (44.1, 45.15, -111.2, -109.8), 2.5, 50),
            ("california_m5_plus_since_1900", (32, 42.5, -126, -114), 5.0, 150)]
    out["T3_prequake"] = []
    for name, box, m, R in regs:
        qs = load_quakes(name)
        # report box = catalogue box grown by R so edge reports can see quakes
        g = R / 111.0
        rbox = (box[0] - g, box[1] + g, box[2] - g * 1.4, box[3] + g * 1.4)
        out["T3_prequake"].append(t3_quakes(nuf, qs, rbox, m, R, name))
        print("  ", name, out["T3_prequake"][-1].get("n_reports"), flush=True)
    out["T3b_oklahoma_DiD"] = t3b_oklahoma(nuf, load_quakes("oklahoma_m3_plus_since_2000"))

    print("hotspots ...", flush=True)
    out["geography"] = {"geipan_by_department": hotspots(gei_in, "dept", dg, 20),
                        "nuforc_by_state": hotspots(nuf_in, "state", dn, 100)}

    print("sensitivity ...", flush=True)
    sens = {}
    # (a) GEIPAN unexplained-vs-identified orb fault test, stratified by decade
    lat = np.array([r["lat"] for r in gei_in]); lon = np.array([r["lon"] for r in gei_in])
    ia = np.array([r["kind"] == "orb" and r["cls"] in "CD" for r in gei_in])
    ib = np.array([r["kind"] == "orb" and r["cls"] in "AB" for r in gei_in])
    dec = np.array([(r["date"].year // 10 if r["date"] else 0) for r in gei_in])
    loc = np.round(lat, 2) * 1000 + np.round(lon, 2)
    sens["geipan_CD_vs_AB_orb_fault_MH_by_decade"] = {
        f"{R}km": mh_test(dg[ia] <= R, dg[ib] <= R, dec[ia], dec[ib], loc[ia], loc[ib]) for R in (10, 25, 50)}
    sens["geipan_CD_orbs_within_10km_by_dept"] = collections.Counter(
        r["dept"] for r, x in zip(gei_in, dg) if r["kind"] == "orb" and r["cls"] in "CD" and x <= 10)
    # (b) Cascadia pre-quake hint: window, radius and magnitude sweeps
    qa = load_quakes("cascadia_m2_5_plus_since_1970"); g = 100 / 111
    box = (40 - g, 50 + g, -131 - g * 1.4, -120 + g * 1.4)
    sens["cascadia_sweep"] = []
    for m, pre, R in [(3, 7, 100), (3, 30, 100), (4, 14, 100), (3, 14, 50), (3, 14, 200)]:
        r = t3_quakes(nuf, qa, box, m, R, "cascadia", pre=pre, nshift=5)
        sens["cascadia_sweep"].append({"M_min": m, "pre_days": pre, "radius_km": R,
                                       "p_orb": r["pre"]["p_case"], "p_craft": r["pre"]["p_ctrl"],
                                       "pre_MH_by_year": r["pre_MH_by_year"]})
    r = t3_quakes([x for x in nuf if x["date"].year != 1980],
                  [x for x in qa if x[0].year != 1980], box, 3, 100, "cascadia_excl_1980", nshift=5)
    sens["cascadia_excl_1980_St_Helens"] = r["pre_MH_by_year"]
    out["sensitivity"] = sens

    out["manifest"] = {k: sha(os.path.join(GEO, p)) for k, p in {
        "nuforc_scrubbed.csv": "nuforc/scrubbed.csv", "gem.geojson": "faults/gem.geojson",
        "SW-All.txt": "kp/spaceweather/data/SW-All.txt", "cities.tsv": "pop/cities.tsv"}.items()}
    for f in sorted(os.listdir(os.path.join(GEO, "eq"))):
        out["manifest"]["eq/" + f] = sha(os.path.join(GEO, "eq", f))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1, default=lambda o: list(o) if isinstance(o, tuple) else str(o))
    print("wrote", OUT)

if __name__ == "__main__":
    main()
