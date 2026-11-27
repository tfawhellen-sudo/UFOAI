"""Shared loading and helpers for the deep-time analyses."""
import gzip, json, os, re, math, collections
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'processed', 'deeptime')
VAULT = os.path.join(ROOT, 'evidence_vault', '13_DEEP_TIME')

ERAS = [('E0 antiquity <500', -300, 500), ('E1 500-999', 500, 1000), ('E2 1000-1499', 1000, 1500),
        ('E3 1500-1699', 1500, 1700), ('E4 1700-1799', 1700, 1800), ('E5 1800-1895', 1800, 1896),
        ('E6 airship 1896-1913', 1896, 1914), ('E7 1914-1946', 1914, 1947),
        ('M1 1947-1973', 1947, 1974), ('M2 1974-1999', 1974, 2000), ('M3 2000-2025', 2000, 2026)]
ERA_NAMES = [e[0] for e in ERAS]
CATALOGS = ['WITS', 'PREROS', 'HATCH', 'EBERHART', 'OVERMEIRE', 'RR0', 'JOHNSON', 'MAGONIA', 'NICAP']
LLM_CATS = {'WITS', 'PREROS'}

# a text that names a known natural phenomenon (or a compiler identification was stripped from it)
NATURAL = re.compile(r"\b(comets?|meteors?|meteorites?|bolides?|aurora\w*|northern lights|halos?|parhel\w*|mock suns?|"
                     r"sun ?dogs?|eclipse|ball lightning|com[eè]tes?|m[ée]t[ée]or\w*|aurores?|parh[ée]lies?)\b", re.I)
# features that the NATURAL regex itself feeds; excluded whenever mundane and unexplained are compared
NAMING = {'fireball', 'f_comet', 'f_celestial'}


def era_of(y):
    for n, a, b in ERAS:
        if a <= y < b:
            return n
    return None


def load():
    D = json.load(gzip.open(os.path.join(P, 'corpus.json.gz')))
    recs = D['records']
    for r in recs:
        r['era'] = era_of(r['year'])
        r['fs'] = set(r['feats'])
        r['natural'] = bool(r.get('mundane')) or bool(NATURAL.search(r.get('raw') or r.get('text') or ''))
    return D['features'], [r for r in recs if r['era']]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def mh_or(strata):
    """Mantel-Haenszel odds ratio over strata [(a,b,c,d)] with Robins-Breslow-Greenland 95% CI.
    a = exposed with feature, b = exposed without, c = unexposed with, d = unexposed without."""
    R = S = PR = PS_QR = QS = 0.0
    for a, b, c, d in strata:
        n = a + b + c + d
        if n == 0 or (a + b) == 0 or (c + d) == 0:
            continue
        r_, s_ = a * d / n, b * c / n
        p_, q_ = (a + d) / n, (b + c) / n
        R += r_; S += s_
        PR += p_ * r_; PS_QR += p_ * s_ + q_ * r_; QS += q_ * s_
    if R == 0 or S == 0:
        return float('nan'), float('nan'), float('nan')
    orr = R / S
    v = PR / (2 * R * R) + PS_QR / (2 * R * S) + QS / (2 * S * S)
    se = math.sqrt(v)
    return orr, math.exp(math.log(orr) - 1.96 * se), math.exp(math.log(orr) + 1.96 * se)


def jsd(p, q, eps=1e-9):
    """Jensen-Shannon divergence between two vectors of independent Bernoulli prevalences (mean over features, bits)."""
    p = np.clip(np.asarray(p, float), eps, 1 - eps); q = np.clip(np.asarray(q, float), eps, 1 - eps)
    m = (p + q) / 2

    def h(x):
        return -(x * np.log2(x) + (1 - x) * np.log2(1 - x))
    return float(np.mean(h(m) - (h(p) + h(q)) / 2))


def prev(rs, feats):
    if not rs:
        return np.full(len(feats), np.nan)
    return np.array([sum(f in r['fs'] for r in rs) / len(rs) for f in feats])


def dump(name, obj):
    os.makedirs(P, exist_ok=True); os.makedirs(VAULT, exist_ok=True)
    for d in (P, VAULT):
        json.dump(obj, open(os.path.join(d, name), 'w'), indent=1, default=float)
