"""UAP craft taxonomy - step 4: where does each class fall, against a proper null for where
people are?

A. NUFORC, contiguous US, 0.05 deg grid (~5 km).
   Null = people: Meta/CIESIN HRSL 2019 population per cell (pop_usa_005.npz).
   Model: quasi-Poisson GLM of report counts per populated cell,
      log E[count] = log(pop) + density decile + region (4 longitude bands) + distance bands
   -> rate ratios (RR) per capita, adjusted for density (a dark-sky / rural-reporting proxy)
      and region. Reference band: >= 100 km from the site type.
   Class enrichment: same GLM on one class's counts with offset log(all reports in the cell),
      cells with >= 1 report -> does the class sit nearer sites than other reports do?
   Terrain: same per-capita GLM with elevation and relief bands (Copernicus GLO-90).
B. Hatch, worldwide: no global population layer here, so case-control only: each class vs all
   other Hatch reports, near (<= 50 km) vs far, logistic with region dummies AND 5-year bins.
   The year bins matter: reactors came on line through the 1970s-80s while the class mix also
   changed (triangles rose in the 1980s), so a region-only model reads the shared trend as
   'near reactors' (kept in the output as 'crude'). Two sensitivity runs: (i) without the two
   big triangle waves that sat near reactors (Hudson Valley NY/CT 1982-87, Belgium 1989-91),
   (ii) one record per class x 0.5 deg cell x year, so a wave's repeat reports count once.
   Hatch's own 'Locale' field gives terrain by class.
C. GEIPAN, France: D (unexplained) vs A/B (explained) by distance to the nearest nuclear plant
   from GeoNuclearData (replaces the hand-entered 28-site layer of geipan_phase123.py).

Geocodes are settlement centroids (NUFORC, GEIPAN) or Hatch's own coordinates, so nothing
under ~10 km is resolvable; the nearest band is 0-25 km.
Output: data/processed/taxonomy/geo.json
"""
import gzip, json, os, sys, collections, re, numpy as np
import statsmodels.api as sm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sites

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = f'{ROOT}/data/processed/taxonomy'
BANDS = [(0, 25), (25, 50), (50, 100)]          # reference: >= 100 km
BAND_NAMES = ['0-25 km', '25-50 km', '50-100 km']


def load():
    D = json.load(gzip.open(f'{P}/records.json.gz'))
    A = json.load(gzip.open(f'{P}/assign.json.gz')) if os.path.exists(f'{P}/assign.json.gz') else {}
    S = json.load(open(f'{P}/stability.json')) if os.path.exists(f'{P}/stability.json') else {'models': {}}
    return D, A, S


def band_dummies(d):
    return np.column_stack([(d >= a) & (d < b) for a, b in BANDS]).astype(float)


class _Fit:
    pass


def glm(y, X, offset, iters=50):
    """Quasi-Poisson GLM by IRLS (own implementation: statsmodels held ~0.5 GB per fit on
    255k cells and the run was OOM-killed at 13.7 GB). Scale = Pearson X2 / (n - p)."""
    from scipy.stats import norm
    X = np.column_stack([np.ones(len(y)), X])
    b = np.zeros(X.shape[1]); b[0] = np.log(max(y.sum(), 1e-9) / np.exp(offset).sum())
    for _ in range(iters):
        eta = np.clip(X @ b + offset, -50, 50); mu = np.exp(eta)
        z = eta - offset + (y - mu) / mu
        XtW = X.T * mu
        H = XtW @ X
        bn = np.linalg.solve(H + 1e-10 * np.eye(len(b)), XtW @ z)
        if np.max(np.abs(bn - b)) < 1e-8:
            b = bn; break
        b = bn
    mu = np.exp(np.clip(X @ b + offset, -50, 50))
    phi = float(((y - mu) ** 2 / mu).sum() / max(len(y) - len(b), 1))
    cov = phi * np.linalg.inv((X.T * mu) @ X)
    f = _Fit(); f.params = b; f.bse = np.sqrt(np.diag(cov)); f.scale = phi
    f.pvalues = 2 * norm.sf(np.abs(b / f.bse))
    return f


def rr_table(m, names, first):
    out = {}
    for i, nm in enumerate(names):
        b = m.params[first + i]; se = m.bse[first + i]
        out[nm] = dict(RR=float(np.exp(b)), lo=float(np.exp(b - 1.96 * se)), hi=float(np.exp(b + 1.96 * se)), p=float(m.pvalues[first + i]))
    return out


def nuforc_us(D, A, S, L, agg=1):
    """agg=1: 0.05 deg cells. agg=5: 0.25 deg (~25 km) cells, closer to the precision of a
    settlement-centroid geocode (a town's reports all land in its centroid cell while its people
    spread over several 5 km cells). Results that hold at both scales are the robust ones."""
    g = np.load(f'{P}/pop_usa_005.npz'); dem = np.load(f'{P}/dem_usa_005.npz')
    pop, LAT0, LON0, RES = g['grid'], float(g['lat0']), float(g['lon0']), float(g['res'])
    elev, relief = dem['elev'], dem['relief']
    if agg > 1:
        h, w = pop.shape[0] // agg, pop.shape[1] // agg
        blk = lambda a: a[:h * agg, :w * agg].reshape(h, agg, w, agg)
        pop = blk(pop).sum((1, 3))
        with np.errstate(all='ignore'):
            elev = np.nanmean(blk(elev), (1, 3)); relief = np.nanmean(blk(relief), (1, 3))
        RES = RES * agg
    ny, nx = pop.shape
    iy, ix = np.nonzero(pop > 0)
    clat = LAT0 + (iy + 0.5) * RES; clon = LON0 + (ix + 0.5) * RES
    conus = (clat > 24) & (clat < 50) & (clon > -125) & (clon < -66)
    iy, ix, clat, clon = iy[conus], ix[conus], clat[conus], clon[conus]
    cid = {(a, b): n for n, (a, b) in enumerate(zip(iy, ix))}
    cpop = pop[iy, ix]
    area = (RES * 111.32) ** 2 * np.cos(np.radians(clat))
    dens = cpop / area
    dec = np.digitize(np.log10(dens + 1e-3), np.quantile(np.log10(dens + 1e-3), np.linspace(0.1, 0.9, 9)))
    region = np.digitize(clon, [-114, -95, -82])
    dist = {k: L[k].km(clat, clon) for k in ('airport_civil', 'military_airfield', 'nuclear_plant', 'coast')}
    # reports -> cells
    recs = [r for r in D['records'] if r['src'] == 'NUFORC' and r['country'] == 'United States' and r['lat'] is not None]
    ass = A.get('NUFORC', {})
    K = S['models'].get('NUFORC', {}).get('K', 0)
    labels = S['models'].get('NUFORC', {}).get('labels', [])
    groups = {'ALL': lambda r: True}
    for k in range(K):
        groups[f'class{k}'] = (lambda kk: (lambda r: ass.get(r['uid']) == kk))(k)
    for f in ('disc', 'sphere', 'light', 'triangle', 'cigar', 'fireball', 'formation'):
        groups[f'shape:{f}'] = (lambda ff: (lambda r: ff in r['feats']))(f)
    cnt = {g_: np.zeros(len(cpop)) for g_ in groups}
    miss = 0
    for r in recs:
        a = int((r['lat'] - LAT0) / RES); b = int((r['lon'] - LON0) / RES)
        n = cid.get((a, b))
        if n is None:
            miss += 1; continue
        for g_, fn in groups.items():
            if fn(r):
                cnt[g_][n] += 1
    allc = cnt['ALL']
    print('NUFORC US reports', len(recs), 'in populated CONUS cells', int(allc.sum()), 'outside/unpopulated', miss)
    out = dict(cell_deg=RES, n_reports=int(allc.sum()), n_unplaced=miss, n_cells=len(cpop), population=float(cpop.sum()), layers={})
    # crude population vs report shares within 25 km
    crude = {}
    for k in ('airport_civil', 'military_airfield', 'nuclear_plant'):
        near = dist[k] < 25
        crude[k] = dict(pop_share_lt25=float(cpop[near].sum() / cpop.sum()), report_share_lt25=float(allc[near].sum() / allc.sum()))
    out['crude_lt25km'] = crude
    Xbase = np.column_stack([np.eye(10)[dec][:, 1:], np.eye(4)[region][:, 1:]])
    nb = Xbase.shape[1]
    for k in ('airport_civil', 'military_airfield', 'nuclear_plant'):
        X = np.column_stack([Xbase, band_dummies(dist[k])])
        res = {}
        for g_ in groups:
            y = cnt[g_]
            if y.sum() < 200:
                continue
            m = glm(y, X, np.log(cpop))
            per_capita = rr_table(m, BAND_NAMES, 1 + nb)
            enrich = None
            if g_ != 'ALL':
                s = allc > 0
                me = glm(y[s], X[s], np.log(allc[s]))
                enrich = rr_table(me, BAND_NAMES, 1 + nb)
            res[g_] = dict(n=int(y.sum()), per_capita=per_capita, vs_other_reports=enrich)
        out['layers'][k] = res
        a = res['ALL']['per_capita']['0-25 km']
        print('  %-18s ALL per-capita RR 0-25km %.2f (%.2f-%.2f)' % (k, a['RR'], a['lo'], a['hi']))
        for g_ in res:
            if g_ == 'ALL':
                continue
            e = res[g_]['vs_other_reports']['0-25 km']
            print('     %-16s n=%6d  per-capita %.2f  vs other reports %.2f (%.2f-%.2f)' % (
                g_, res[g_]['n'], res[g_]['per_capita']['0-25 km']['RR'], e['RR'], e['lo'], e['hi']))
    # joint model: all three site types at once (they overlap: airports sit near cities and bases)
    Xj = np.column_stack([Xbase] + [band_dummies(dist[k])[:, :1] for k in ('airport_civil', 'military_airfield', 'nuclear_plant')])
    mj = glm(allc, Xj, np.log(cpop))
    out['joint_lt25km_ALL'] = rr_table(mj, ['airport_civil <25', 'military_airfield <25', 'nuclear_plant <25'], 1 + nb)
    print('  joint', {k: round(v['RR'], 2) for k, v in out['joint_lt25km_ALL'].items()})
    # terrain
    e = elev[iy, ix]; rl = relief[iy, ix]; ok = np.isfinite(e) & np.isfinite(rl)
    eb = np.digitize(e, [300, 1000, 2000]); rb = np.digitize(rl, [10, 50, 150])
    cb = np.digitize(dist['coast'], [10, 50, 200])
    terr = {}
    for nm, arr, names in [('elevation', eb, ['300-1000 m', '1000-2000 m', '>2000 m']),
                           ('relief', rb, ['10-50 m', '50-150 m', '>150 m']),
                           ('coast', cb, ['10-50 km', '50-200 km', '>200 km'])]:
        X = np.column_stack([Xbase, np.eye(4)[arr][:, 1:]])
        res = {}
        for g_ in groups:
            y = cnt[g_]
            if y.sum() < 200:
                continue
            m = glm(y[ok], X[ok], np.log(cpop[ok]))
            pc = rr_table(m, names, 1 + nb)
            en = None
            if g_ != 'ALL':
                s = ok & (allc > 0)
                en = rr_table(glm(y[s], X[s], np.log(allc[s])), names, 1 + nb)
            res[g_] = dict(n=int(y.sum()), per_capita=pc, vs_other_reports=en)
        terr[nm] = res
        print('  terrain', nm, 'ALL', {k: round(v['RR'], 2) for k, v in res['ALL']['per_capita'].items()})
    out['terrain'] = terr
    # density gradient itself (per-capita reporting by density decile, region-adjusted)
    m = glm(allc, np.column_stack([np.eye(10)[dec][:, 1:], np.eye(4)[region][:, 1:]]), np.log(cpop))
    out['density_decile_RR'] = [1.0] + [float(np.exp(b)) for b in m.params[1:10]]
    print('  per-capita RR by density decile (1=sparsest)', [round(x, 2) for x in out['density_decile_RR']])
    out['labels'] = labels
    return out


def logit(y, X):
    m = sm.GLM(y, sm.add_constant(X, has_constant='add'), family=sm.families.Binomial()).fit()
    b, se = m.params[-1], m.bse[-1]
    return dict(OR=float(np.exp(b)), lo=float(np.exp(b - 1.96 * se)), hi=float(np.exp(b + 1.96 * se)), p=float(m.pvalues[-1]))


def hatch_world(D, A, S, L):
    from stability import region_hatch
    recs = [r for r in D['records'] if r['src'] == 'HATCH' and r['lat'] is not None and r['year'] and r['year'] >= 1945]
    ass = A.get('HATCH', {}); K = S['models'].get('HATCH', {}).get('K', 0)
    lat = np.array([r['lat'] for r in recs]); lon = np.array([r['lon'] for r in recs]); yr = np.array([r['year'] for r in recs])
    regs = sorted({region_hatch(r['country']) for r in recs})
    R = np.array([[region_hatch(r['country']) == g for g in regs[1:]] for r in recs], float)
    # nuclear: time-aware (plant operating in the event year)
    nuc = sites.nuclear()
    nlat = np.array([p[0] for p in nuc]); nlon = np.array([p[1] for p in nuc]); y0 = np.array([p[4] for p in nuc]); y1 = np.array([p[5] for p in nuc])
    dn = np.full(len(recs), np.inf)
    for y in np.unique(yr):
        s = yr == y; live = (y0 <= y) & (y1 >= y)
        if live.sum() == 0:
            continue
        dn[s] = sites.Nearest(nlat[live], nlon[live]).km(lat[s], lon[s])
    dm = L['military_airfield'].km(lat, lon)
    near = {'military_airfield<=50km': (dm <= 50).astype(float), 'nuclear_plant_operating<=50km': (dn <= 50).astype(float)}
    Y5 = np.eye(11)[np.minimum((yr - 1945) // 5, 10)][:, 1:]
    usa = np.array([r['country'] == 'USA' for r in recs]); bel = np.array([r['country'].startswith('Belgium') for r in recs])
    wave = {'Hudson Valley NY/CT 1982-87': usa & (yr >= 1982) & (yr <= 1987) & (lat > 40.7) & (lat < 42.2) & (lon > -74.5) & (lon < -72.5),
            'Belgium 1989-91': bel & (yr >= 1989) & (yr <= 1991)}
    nowave = ~np.any(list(wave.values()), axis=0)
    cls = np.array([ass.get(r['uid'], -1) for r in recs])
    first = {}
    for i, kk in enumerate(zip(cls, np.round(lat * 2), np.round(lon * 2), yr)):
        first.setdefault(kk, i)
    dedup = np.zeros(len(recs), bool); dedup[list(first.values())] = True
    out = dict(n=len(recs), near_rate={k: float(v.mean()) for k, v in near.items()}, classes={}, locale={},
               waves={nm: dict(n=int(w.sum()), near_nuclear=int((w & (dn <= 50)).sum()),
                               classes=dict(collections.Counter(int(c) for c in cls[w]))) for nm, w in wave.items()},
               n_dedup=int(dedup.sum()), adjust='region + 5-year bins')
    for k in range(K):
        y = (cls == k).astype(float)
        row = {}
        for nm, v in near.items():
            X = np.column_stack([R, Y5, v])
            row[nm] = logit(y, X)
            row[nm]['crude_region_only'] = logit(y, np.column_stack([R, v]))
            row[nm]['without_waves'] = logit(y[nowave], X[nowave])
            row[nm]['dedup'] = logit(y[dedup], X[dedup])
        out['classes'][f'class{k}'] = dict(n=int(y.sum()), **row)
        print('  Hatch class%d n=%5d  ' % (k, y.sum()) + '  '.join('%s OR %.2f (%.2f-%.2f) [crude %.2f, no waves %.2f, dedup %.2f]' % (
            nm, d['OR'], d['lo'], d['hi'], d['crude_region_only']['OR'], d['without_waves']['OR'], d['dedup']['OR']) for nm, d in row.items()))
    # Hatch's own NUC code (compiler flagged 'nuclear facility related') by class
    nucflag = np.array(['NUC' in (r.get('codes') or []) for r in recs])
    out['nuc_code_rate_by_class'] = {f'class{k}': float(nucflag[np.array([ass.get(r['uid']) == k for r in recs])].mean()) for k in range(K)}
    loc = collections.defaultdict(collections.Counter)
    for r in recs:
        loc[ass.get(r['uid'])][r.get('locale') or '?'] += 1
    tot = collections.Counter(r.get('locale') or '?' for r in recs)
    for k in range(K):
        n = sum(loc[k].values())
        out['locale'][f'class{k}'] = {l: dict(share=loc[k][l] / n, lift=(loc[k][l] / n) / (tot[l] / len(recs))) for l, _ in tot.most_common(12)}
    return out


def geipan_fr(D, A, S, L):
    recs = [r for r in D['records'] if r['src'] == 'GEIPAN' and r['lat'] is not None and r['gclass'] in 'ABCD' and r['year']]
    lat = np.array([r['lat'] for r in recs]); lon = np.array([r['lon'] for r in recs]); yr = np.array([r['year'] for r in recs])
    nuc = [p for p in sites.nuclear() if p[2] == 'FR']
    nlat = np.array([p[0] for p in nuc]); nlon = np.array([p[1] for p in nuc]); y0 = np.array([p[4] for p in nuc]); y1 = np.array([p[5] for p in nuc])
    dn = np.full(len(recs), np.inf)
    for y in np.unique(yr):
        s = yr == y; live = (y0 <= y) & (y1 >= y)
        if live.sum():
            dn[s] = sites.Nearest(nlat[live], nlon[live]).km(lat[s], lon[s])
    dm = L['military_airfield'].km(lat, lon)
    gc = np.array([r['gclass'] for r in recs])
    s = np.isin(gc, ['A', 'B', 'D'])
    out = dict(n_sites=len(nuc), n=int(s.sum()), n_D=int((gc == 'D').sum()), adjust='era (pre-1980, 1980-99, 2000-09, 2010+)')
    # era adjustment: D is commoner in older cases and fewer reactors ran then
    era = np.digitize(yr, [1980, 2000, 2010]); E = np.eye(4)[era][:, 1:]
    for nm, d in (('nuclear_plant_operating', dn), ('military_airfield', dm)):
        for km in (20, 30, 50):
            v = (d[s] <= km).astype(float); y = (gc[s] == 'D').astype(float)
            a = int(((y == 1) & (v == 1)).sum()); b = int(((y == 1) & (v == 0)).sum())
            c = int(((y == 0) & (v == 1)).sum()); dd = int(((y == 0) & (v == 0)).sum())
            r = logit(y, np.column_stack([E[s], v]))
            r['crude'] = logit(y, v[:, None])
            out[f'{nm}<={km}km'] = dict(D_near=a, D_far=b, AB_near=c, AB_far=dd, **r)
            print('  GEIPAN D vs A/B, %s <= %d km: D %d/%d near, A/B %d/%d near, OR %.2f (%.2f-%.2f) era-adjusted; crude %.2f' % (
                nm, km, a, a + b, c, c + dd, r['OR'], r['lo'], r['hi'], r['crude']['OR']))
    # per GEIPAN class: share D by class
    ass = A.get('GEIPAN', {})
    K = S['models'].get('GEIPAN', {}).get('K', 0)
    out['class_gclass'] = {}
    for k in range(K):
        c = collections.Counter(r['gclass'] for r in recs if ass.get(r['uid']) == k)
        out['class_gclass'][f'class{k}'] = dict(c)
    return out


def main():
    D, A, S = load()
    L, counts = sites.layers()
    print('site layers', counts)
    if len(sys.argv) > 1 and sys.argv[1] == 'hatch':      # recompute only the Hatch and GEIPAN parts
        out = json.load(open(f'{P}/geo.json'))
        out['hatch_world'] = hatch_world(D, A, S, L)
        out['geipan_fr'] = geipan_fr(D, A, S, L)
        json.dump(out, open(f'{P}/geo.json', 'w'), indent=1)
        return
    out = dict(layer_counts=counts)
    out['nuforc_us'] = nuforc_us(D, A, S, L)
    print('--- 0.25 deg sensitivity')
    out['nuforc_us_025'] = nuforc_us(D, A, S, L, agg=5)
    out['hatch_world'] = hatch_world(D, A, S, L)
    out['geipan_fr'] = geipan_fr(D, A, S, L)
    json.dump(out, open(f'{P}/geo.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
