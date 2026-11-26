"""Shared loading for the taxonomy scripts: binary feature matrix X (non-duration features)
and the categorical duration item C (0..3, -1 = missing)."""
import gzip, json, os, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = f'{ROOT}/data/processed/taxonomy'
D = json.load(gzip.open(f'{P}/records.json.gz'))
DUR = ['dur_lt1m', 'dur_1_5m', 'dur_5_30m', 'dur_gt30m']
FB = [f for f in D['features'] if f not in DUR]          # binary items
L = len(DUR)
COLS = FB + DUR                                           # display/matching columns
_IB = {f: i for i, f in enumerate(FB)}
_ID = {f: i for i, f in enumerate(DUR)}


def matrix(rs):
    X = np.zeros((len(rs), len(FB)), np.float32)
    C = np.full(len(rs), -1, int)
    for n, r in enumerate(rs):
        for f in r['feats']:
            if f in _IB:
                X[n, _IB[f]] = 1
            elif f in _ID:
                C[n] = _ID[f]
    return X, C


def marginal(X, C):
    obs = C >= 0
    return np.concatenate([X.mean(0), np.bincount(C[obs], minlength=L) / max(1, obs.sum())])
