"""UAP craft taxonomy - step 2: final classes per source, and their stability across
countries, decades and sources.

Stability test for one subset S of a source (leave-subset-out design):
  fit LCA(K) on S, fit LCA(K) on the complement C (independent data), Hungarian-match classes by
  correlation of CENTRED item profiles (each model centred on its own data's marginals).
  ceiling: a random draw from C of the same size as S, vs the rest of C (same culture, pure
           sampling noise)
  floor:   S with every column permuted independently (keeps each feature's frequency, destroys
           co-occurrence), vs C. 3 permutations.
  score per class: r_S. Reported with ceiling and floor; a class "replicates in S" if r_S >= 0.7
  and r_S exceeds the floor's max.
Duration enters every model as one categorical item (lca.py); profiles used for matching
are the binary item probabilities plus the duration distribution.
Output: data/processed/taxonomy/stability_<SRC>.json, assign_<SRC>.json.gz; 'merge' builds
stability.json (+ cross-source matching) and assign.json.gz
"""
import gzip, json, os, sys, collections, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lca
from tdata import D, matrix, marginal, L, COLS, P

F = COLS
SEEDS = 8   # restarts per fit in the stability comparisons (see select_k.py on local optima)
CAP = int(os.environ.get('TAXO_CAP', '30000'))


def choose_k(src):
    sel = json.load(open(f'{P}/selectk_{src}.json'))
    ok = [s['K'] for s in sel if min(s['split_min_r_each']) >= 0.7 and s['split_min_r'] >= 0.8]
    return (max(ok) if ok else 2), sel


def label(theta, marg, top=4):
    lift = theta / np.maximum(marg, 1e-3)
    out = []
    for j in np.argsort(-(theta - marg)):
        if theta[j] >= 0.2 and lift[j] >= 1.3:
            out.append('%s %.0f%%' % (F[j], 100 * theta[j]))
        if len(out) == top:
            break
    if not out:
        # residual class: nothing reaches 1.3x the average; name what is most raised and say so
        j = [j for j in np.argsort(-(theta - marg)) if theta[j] - marg[j] > 0.02][:2]
        return 'residual, no dominant feature (most raised: %s)' % ', '.join(
            '%s %.0f%% vs %.0f%% avg' % (F[i], 100 * theta[i], 100 * marg[i]) for i in j)
    return ', '.join(out)


def region_hatch(c):
    LAT = {'Brazil', 'Argentina', 'Venezuela', 'Chile', 'Mexico', 'Peru', 'Uruguay', 'Colombia', 'Bolivia', 'Costa Rica',
           'Guatemala', 'Panama', 'Honduras', 'Ecuador', 'Caribbean area', 'Guyanas (all 3 of them)'}
    EUR = {'Italy', 'Scandanavian and Finland', 'Spain', 'Belgium, Netherlandsand Luxembourg', 'Russia', 'Romania',
           'Portugal', 'Germany', 'Switzerland', 'Greece and Island nations', 'Poland', 'Former Yugoslavia', 'Ukraine',
           'Austria', 'Estonia, Latvia& Lithuania', 'Hungary', 'Czech and Slovak Republics', 'Bulgaria', 'Belorus', 'Georgia'}
    if c == 'USA': return 'USA'
    if c == 'France': return 'France'
    if c == 'Great Britain and Ireland': return 'UK+Ireland'
    if c in ('Canada', 'Australia', 'New Zealand'): return 'Canada+Aus+NZ'
    if c in LAT: return 'Latin America'
    if c in EUR: return 'Europe (other)'
    return 'Asia/Africa/oceans/other'


def region_nuforc(r):
    c = r['country']
    if c == 'United States':
        lon = r['lon']
        if lon is None: return None
        return 'US West' if lon < -114 else 'US Mountain/Plains' if lon < -95 else 'US Midwest/South' if lon < -82 else 'US East'
    if c == 'Canada': return 'Canada'
    if c in ('United Kingdom',): return 'UK'
    if c in ('Australia', 'New Zealand'): return 'Aus+NZ'
    return 'other countries'


def decade_hatch(y):
    if y is None or y < 1900: return None
    return 'pre-1950' if y < 1950 else '1950s' if y < 1960 else '1960s' if y < 1970 else '1970s' if y < 1980 else '1980s+'


def decade_nuforc(y):
    if y is None: return None
    return 'pre-1990' if y < 1990 else '1990s' if y < 2000 else '2000s' if y < 2010 else '2010s' if y < 2020 else '2020s'


def decade_geipan(y):
    if y is None: return None
    return 'pre-1980' if y < 1980 else '1980-99' if y < 2000 else '2000-09' if y < 2010 else '2010+'


def compare(XS, CS, XC, CC, K, rng, fprof, fmarg, nperm=3):
    mS = lca.fit(XS, K, SEEDS, 1, C=CS, L=L); mC = lca.fit(XC, K, SEEDS, 2, C=CC, L=L)
    pairs, r = lca.match(lca.profile(mC), lca.profile(mS), marginal(XC, CC), marginal(XS, CS))
    # index results by FULL-model class: full class f <-> complement class c
    fpairs, _ = lca.match(fprof, lca.profile(mC), fmarg, marginal(XC, CC))
    c2f = {c: f for f, c in fpairs}
    # ceiling: same-size draw from the complement vs the rest of the complement
    p = rng.permutation(len(XC)); n = min(len(XS), len(XC) // 2)
    a, b = p[:n], p[n:]
    mA = lca.fit(XC[a], K, SEEDS, 3, C=CC[a], L=L); mB = lca.fit(XC[b], K, SEEDS, 4, C=CC[b], L=L)
    _, rc = lca.match(lca.profile(mB), lca.profile(mA), marginal(XC[b], CC[b]), marginal(XC[a], CC[a]))
    rf = []
    fl = np.full((nperm, K), np.nan)
    for k in range(nperm):
        Xp = XS.copy()
        for j in range(Xp.shape[1]):
            Xp[:, j] = Xp[rng.permutation(len(Xp)), j]
        Cp = CS[rng.permutation(len(CS))]
        mp = lca.fit(Xp, K, 3, 10 + k, C=Cp, L=L)
        pp, rp = lca.match(lca.profile(mC), lca.profile(mp), marginal(XC, CC), marginal(Xp, Cp))
        rf.append(rp)
        for n_, (i, j) in enumerate(pp):
            fl[k, c2f[i]] = rp[n_]
    rS = np.zeros(K)
    for n_, (i, j) in enumerate(pairs):
        rS[c2f[i]] = r[n_]
    # per-class floor: a class made of ONE dominant feature (e.g. 'cigar 100%') is re-created
    # from shuffled data, where nothing co-occurs; only r above that class's own floor counts
    return dict(r_by_class=rS.tolist(), floor_by_class=np.nanmax(fl, 0).tolist(), ceiling_mean=float(np.mean(rc)),
                ceiling_min=float(np.min(rc)), floor_mean=float(np.mean(rf)), floor_max=float(np.max(rf)), n=len(XS))


_JOB = None


def _work(a):
    """one subset comparison in a worker process (fork: _JOB is inherited)"""
    X, C, K, prof, marg = _JOB
    si, ci_, sd = a
    return compare(X[si], C[si], X[ci_], C[ci_], K, np.random.default_rng(sd), prof, marg)


def run_source(src, splitters, out):
    rs = [r for r in D['records'] if r['src'] == src]
    X, C = matrix(rs)
    K, sel = choose_k(src)
    m = lca.fit(X, K, 16, 0, C=C, L=L)
    prof = lca.profile(m); marg = marginal(X, C)
    z = lca.assign(X, m, C)
    model = dict(K=K, selectk=sel, pi=m['pi'].tolist(), theta=prof.tolist(), cols=F, bic=m['bic'], n=len(X),
                 labels=[label(prof[k], marg) for k in range(K)], marg=marg.tolist())
    out['models'][src] = model
    print('\n==', src, 'n', len(X), 'K', K)
    for k in range(K):
        print('  class %d  %.1f%%  %s' % (k, 100 * m['pi'][k], model['labels'][k]))
    rng = np.random.default_rng(11)
    tasks = []
    for name, fn in splitters:
        keys = [fn(r) for r in rs]
        groups = collections.Counter(k for k in keys if k)
        for g, n in sorted(groups.items()):
            if n < (300 if src == 'GEIPAN' else 500):
                continue
            S = np.array([k == g for k in keys]); Cm = np.array([k is not None and k != g for k in keys])
            # cap both sides at CAP records (random, fixed seed) to keep NUFORC tractable;
            # far above what a K <= 9 model needs for stable estimates
            si, ci_ = np.nonzero(S)[0], np.nonzero(Cm)[0]
            if len(si) > CAP: si = np.sort(rng.choice(si, CAP, replace=False))
            if len(ci_) > CAP: ci_ = np.sort(rng.choice(ci_, CAP, replace=False))
            tasks.append((f'{name}:{g}', int(S.sum()), si, ci_, int(rng.integers(1 << 30)), z[S]))
    global _JOB
    _JOB = (X, C, K, prof, marg)
    from concurrent.futures import ProcessPoolExecutor
    res = {}
    with ProcessPoolExecutor(int(os.environ.get('TAXO_WORKERS', '3'))) as ex:
        for (key, ntot, si, ci_, sd, zS), c in zip(tasks, ex.map(_work, [(t[2], t[3], t[4]) for t in tasks])):
            c['n_total'] = ntot
            c['share'] = (np.bincount(zS, minlength=K) / len(zS)).tolist()
            res[key] = c
            print('  %-28s n=%6d  r by class %s  ceiling %.2f  | class floors %s' % (
                key, ntot, ' '.join('%.2f' % x for x in c['r_by_class']), c['ceiling_mean'],
                ' '.join('%.2f' % x for x in c['floor_by_class'])), flush=True)
    out['stability'][src] = res
    out['assign'][src] = {r['uid']: int(k) for r, k in zip(rs, z)}


def cross_source(out):
    """Match the three full models on the shared feature space (each centred on its own
    marginals). Coding depth differs by source (one-line NUFORC summary vs long GEIPAN text),
    so this is the weakest of the comparisons and is labelled so."""
    M = out['models']; res = {}
    srcs = list(M)
    for a in range(len(srcs)):
        for b in range(a + 1, len(srcs)):
            A, B = M[srcs[a]], M[srcs[b]]
            pairs, r = lca.match(np.array(A['theta']), np.array(B['theta']), np.array(A['marg']), np.array(B['marg']))
            res[f'{srcs[a]}~{srcs[b]}'] = [dict(a=int(i), b=int(j), r=float(x), a_label=A['labels'][i], b_label=B['labels'][j])
                                          for (i, j), x in zip(pairs, r)]
            print('\n', srcs[a], '~', srcs[b])
            for d in res[f'{srcs[a]}~{srcs[b]}']:
                print('   r=%.2f  %s  <->  %s' % (d['r'], d['a_label'], d['b_label']))
    out['cross_source'] = res


SPLITTERS = {
    'HATCH': [('region', lambda r: region_hatch(r['country'])), ('era', lambda r: decade_hatch(r['year']))],
    'GEIPAN': [('era', lambda r: decade_geipan(r['year']))],
    'NUFORC': [('region', region_nuforc), ('era', lambda r: decade_nuforc(r['year']))],
}

def diag():
    """Post-hoc diagnostic (added after NUFORC's triangle class failed in 'US East' only): fit
    K=5 on US East and on the rest, same cap and restarts as the stability runs, and list both
    sets of classes side by side."""
    rs = [r for r in D['records'] if r['src'] == 'NUFORC']
    keys = [region_nuforc(r) for r in rs]
    rng = np.random.default_rng(5); out = {}
    for name, sel in (('US East', lambda k: k == 'US East'), ('rest', lambda k: k is not None and k != 'US East')):
        idx = np.array([i for i, k in enumerate(keys) if sel(k)])
        if len(idx) > CAP: idx = np.sort(rng.choice(idx, CAP, replace=False))
        X, C = matrix([rs[i] for i in idx]); m = lca.fit(X, 5, 12, 0, C=C, L=L)
        pr = lca.profile(m); mg = marginal(X, C)
        out[name] = [dict(share=float(m['pi'][k]), label=label(pr[k], mg)) for k in range(5)]
        print(name, len(idx)); [print('   %.1f%%  %s' % (100 * c['share'], c['label'])) for c in out[name]]
    json.dump(dict(nuforc_us_east_k5=out), open(f'{P}/stability_diag.json', 'w'), indent=1)


if __name__ == '__main__':
    # usage: stability.py SRC (one source; resumable per source) | stability.py merge | stability.py diag
    if sys.argv[1] == 'diag':
        diag()
    elif sys.argv[1] != 'merge':
        src = sys.argv[1]
        out = dict(models={}, stability={}, assign={})
        run_source(src, SPLITTERS[src], out)
        json.dump(dict(model=out['models'][src], stability=out['stability'][src]), open(f'{P}/stability_{src}.json', 'w'), indent=1)
        with gzip.open(f'{P}/assign_{src}.json.gz', 'wt') as f:
            json.dump(out['assign'][src], f)
    else:
        out = dict(models={}, stability={}, assign={})
        for src in ('HATCH', 'GEIPAN', 'NUFORC'):
            if os.path.exists(f'{P}/stability_{src}.json'):
                d = json.load(open(f'{P}/stability_{src}.json'))
                m = d['model']   # labels recomputed here so a label-rule change needs no refit
                m['labels'] = [label(np.array(t), np.array(m['marg'])) for t in m['theta']]
                out['models'][src] = m; out['stability'][src] = d['stability']
                out['assign'][src] = json.load(gzip.open(f'{P}/assign_{src}.json.gz'))
        if len(out['models']) > 1:
            cross_source(out)
        json.dump({k: v for k, v in out.items() if k != 'assign'}, open(f'{P}/stability.json', 'w'), indent=1)
        with gzip.open(f'{P}/assign.json.gz', 'wt') as f:
            json.dump(out['assign'], f)
