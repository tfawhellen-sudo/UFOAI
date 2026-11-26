"""Choose K per source: BIC curve + split-half replicability.
For each K: fit on all records (12 restarts), then 3 random halvings, each half fitted
separately (12 restarts each), classes Hungarian-matched by centred-profile correlation.
Replicable K: every class matches at r >= 0.7 in every halving and mean(min r) >= 0.8.
NUFORC uses a fixed random 40k subsample here for speed (final fit uses all records).
Resumable: results are written after each K.
Diagnostic that set the restart count: Hatch K=5 on all data reaches the same best
log-likelihood in 7 of 16 restarts (identical classes, r = 1.00); with 5 restarts per half
the halvings sometimes landed in a worse optimum and looked 'unreplicable'."""
import gzip, json, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lca
from tdata import D, matrix, marginal, L, ROOT
RESTARTS = 12


if __name__ == '__main__':
    src = sys.argv[1]
    Ks = range(int(sys.argv[3]) if len(sys.argv) > 3 else 3, int(sys.argv[2]) + 1 if len(sys.argv) > 2 else 11)
    rs = [r for r in D['records'] if r['src'] == src]
    X, C = matrix(rs)
    if len(X) > 40000:
        sub = np.random.default_rng(7).choice(len(X), 40000, replace=False)
        X, C = X[sub], C[sub]
    path = f'{ROOT}/data/processed/taxonomy/selectk_{src}.json'
    out = json.load(open(path)) if os.path.exists(path) else []
    out = [o for o in out if o.get('restarts') == RESTARTS and o.get('duration') == 'categorical']
    done = {o['K'] for o in out}
    for K in Ks:
        if K in done:
            continue
        m = lca.fit(X, K, seeds=RESTARTS, C=C, L=L)
        rr, rall = [], []
        for s in range(3):
            rng = np.random.default_rng(100 + s); p = rng.permutation(len(X)); h = len(X) // 2
            a, b = p[:h], p[h:]
            mA = lca.fit(X[a], K, RESTARTS, s, C=C[a], L=L)
            mB = lca.fit(X[b], K, RESTARTS, s + 50, C=C[b], L=L)
            _, r = lca.match(lca.profile(mA), lca.profile(mB), marginal(X[a], C[a]), marginal(X[b], C[b]))
            rr.append(float(r.min())); rall.append([float(x) for x in r])
        out.append(dict(K=K, bic=float(m['bic']), ll=float(m['ll']), split_min_r=float(np.mean(rr)),
                        split_min_r_each=rr, split_r_all=rall, restarts=RESTARTS, n=len(X), duration='categorical'))
        out.sort(key=lambda o: o['K'])
        json.dump(out, open(path, 'w'), indent=1)
        print(src, K, round(m['bic']), 'split-half min r %.3f' % np.mean(rr), [round(x, 2) for x in rr], flush=True)
