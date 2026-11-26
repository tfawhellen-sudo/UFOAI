"""Latent class analysis by EM, numpy only: J binary items plus, optionally, ONE categorical
item (duration, L levels; -1 = missing, which contributes nothing to the likelihood).

fit(X, K, seeds, C=..., L=...) -> best-loglik model over random restarts.
Model: pi (K,), theta (K, J) item probabilities (clipped to [1e-4, 1-1e-4]), phi (K, L).
Why the categorical item: coding duration as four 0/1 items counts each observation four
times and makes the mutually exclusive bins the dominant 'structure' (a first Hatch run
returned classes defined by duration bin at 100%). Rejected; recorded here.
"""
import numpy as np

EPS = 1e-4


def _estep(X, pi, th, C=None, ph=None):
    lt, l1t = np.log(th), np.log1p(-th)
    ll = X @ lt.T + (1 - X) @ l1t.T + np.log(pi)
    if C is not None:
        lp = np.vstack([np.log(ph).T, np.zeros((1, len(pi)))])   # row L = missing -> 0
        ll = ll + lp[np.where(C < 0, ph.shape[1], C)]
    m = ll.max(1, keepdims=True)
    p = np.exp(ll - m)
    s = p.sum(1, keepdims=True)
    return p / s, float((np.log(s) + m).sum())


def fit_once(X, K, rng, iters=500, tol=1e-7, C=None, L=0):
    """Init: each class seeded from the marginal blended with one random record (soft
    Dirichlet-responsibility init was tried first and stalled at near-identical classes;
    split-half r ~0 on NUFORC; rejected). Stops when mean per-record ll gain < tol."""
    n, J = X.shape
    marg = X.mean(0)
    th = np.clip(0.5 * marg + 0.5 * X[rng.choice(n, K, replace=False)], 0.02, 0.98)
    pi = np.full(K, 1.0 / K)
    ph = None
    if C is not None:
        obs = C >= 0
        cm = np.bincount(C[obs], minlength=L) / max(obs.sum(), 1)
        ph = np.clip(cm[None, :] * rng.uniform(0.7, 1.3, (K, L)), 1e-3, None)
        ph /= ph.sum(1, keepdims=True)
        OH = np.zeros((n, L), np.float32); OH[np.nonzero(obs)[0], C[obs]] = 1
    prev = -np.inf
    for it in range(iters):
        R, ll = _estep(X, pi, th, C, ph)
        nk = R.sum(0) + 1e-9
        pi = nk / n
        th = np.clip((R.T @ X) / nk[:, None], EPS, 1 - EPS)
        if C is not None:
            ph = R.T @ OH + 1e-6
            ph = np.clip(ph / ph.sum(1, keepdims=True), EPS, 1)
            ph /= ph.sum(1, keepdims=True)
        if it > 20 and (ll - prev) / n < tol:
            break
        prev = ll
    R, ll = _estep(X, pi, th, C, ph)
    o = np.argsort(-pi)
    return dict(pi=pi[o], theta=th[o], phi=None if ph is None else ph[o], ll=ll, K=K, n=n, J=J, L=L)


def fit(X, K, seeds=5, seed=0, C=None, L=0):
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(seeds):
        m = fit_once(X, K, rng, C=C, L=L)
        if best is None or m['ll'] > best['ll']:
            best = m
    k = K - 1 + K * X.shape[1] + (K * (L - 1) if C is not None else 0)
    best['bic'] = -2 * best['ll'] + k * np.log(X.shape[0])
    return best


def posterior(X, m, C=None):
    return _estep(X, m['pi'], m['theta'], C, m.get('phi') if C is not None else None)[0]


def assign(X, m, C=None):
    return posterior(X, m, C).argmax(1)


def profile(m):
    """theta with the categorical item appended as L columns (for matching and display)."""
    return m['theta'] if m.get('phi') is None else np.hstack([m['theta'], m['phi']])


def match(thA, thB, margA=None, margB=None):
    """Hungarian match of classes by correlation of CENTRED profiles (theta - marginal).
    Centring removes what two subsets share just by having similar feature frequencies,
    so a column-permuted null scores near 0. Returns (pairs, r per pair)."""
    from scipy.optimize import linear_sum_assignment
    a = thA - (margA if margA is not None else thA.mean(0))
    b = thB - (margB if margB is not None else thB.mean(0))
    a = (a - a.mean(1, keepdims=True)); b = (b - b.mean(1, keepdims=True))
    a /= np.linalg.norm(a, axis=1, keepdims=True) + 1e-12
    b /= np.linalg.norm(b, axis=1, keepdims=True) + 1e-12
    C = a @ b.T
    i, j = linear_sum_assignment(-C)
    return list(zip(i, j)), C[i, j]


def ari(a, b):
    from collections import Counter
    from math import comb
    n = len(a)
    ct = Counter(zip(a, b))
    sa = sum(comb(v, 2) for v in Counter(a).values())
    sb = sum(comb(v, 2) for v in Counter(b).values())
    sij = sum(comb(v, 2) for v in ct.values())
    e = sa * sb / comb(n, 2)
    mx = (sa + sb) / 2
    return (sij - e) / (mx - e) if mx != e else 1.0
