"""Task 2.1 - the 2,000-year descriptor drift test.

1. catalog x era counts
2. catalog-standardised prevalence of every feature in every era (binomial GLM, era + catalog, on
   aggregated cells with proportions + var_weights; 0.25 pseudo-count per cell against separation)
3. ancient (<1800) vs modern (1947+) Mantel-Haenszel odds ratio per feature, stratified by catalog,
   separately for unexplained reports and for reports that name a natural phenomenon (the mundane null)
4. era boundaries: adjacent-era divergence inside single-compiler series vs a split-half noise null
5. compiler effect: agreement between catalogs that describe the same event (Cohen's kappa)
6. LLM-paraphrase check: Wonders-in-the-Sky paraphrase vs other catalogs on the same events
7. primary text: Obsequens (191-12 BC, no ufologist in between) vs catalog antiquity
Writes drift.json.
"""
import collections, itertools, math, random, re, sys, os
import numpy as np
import statsmodels.api as sm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, ERA_NAMES, CATALOGS, LLM_CATS, NAMING, wilson, mh_or, jsd, prev, dump  # noqa: E402
from lexicon import PHYS, FRAME_F, ENTITY_F, VOICE_F, TECH_FRAMES, OLD_FRAMES  # noqa: E402

FEATS, R = load()
CAT = [r for r in R if r['cat'] in CATALOGS]
rng = random.Random(7)
out = {}

# 1 ---------------------------------------------------------------- counts
cnt = collections.Counter((r['cat'], r['era']) for r in R)
out['counts'] = {c: {e: cnt[(c, e)] for e in ERA_NAMES} for c in CATALOGS + ['OBSEQUENS', 'NUFORC_MODERN', 'GEIPAN_MODERN']}
out['n_natural_by_era'] = {e: sum(1 for r in CAT if r['era'] == e and r['natural']) for e in ERA_NAMES}
print('records per era (catalogs):', {e: sum(cnt[(c, e)] for c in CATALOGS) for e in ERA_NAMES})
print('natural-named per era:', out['n_natural_by_era'])

# 2 ---------------------------------------------------------------- standardised prevalence (unexplained only)
UNX = [r for r in CAT if not r['natural']]
cells = collections.defaultdict(lambda: [0, collections.Counter()])
for r in UNX:
    c = cells[(r['era'], r['cat'])]
    c[0] += 1
    c[1].update(r['fs'])
keys = sorted(cells)
eras_present = sorted({k[0] for k in keys}, key=ERA_NAMES.index)
Xd = []
for e, c in keys:
    row = [1.0] + [float(e == x) for x in eras_present[1:]] + [float(c == x) for x in CATALOGS[1:]]
    Xd.append(row)
Xd = np.array(Xd)
keep_cols = Xd.sum(0) > 0
Xd = Xd[:, keep_cols]
n_cell = np.array([cells[k][0] for k in keys], float)
std = {}
lr = {}
for f in FEATS:
    k = np.array([cells[kk][1][f] for kk in keys], float)
    y = (k + 0.25) / (n_cell + 0.5)
    m = sm.GLM(y, Xd, family=sm.families.Binomial(), var_weights=n_cell + 0.5).fit()
    # standardise: predict each era for the pooled catalog mix (weights = catalog totals)
    wcat = collections.Counter(r['cat'] for r in UNX)
    vals = {}
    for e in eras_present:
        tot = 0.0
        for c in CATALOGS:
            row = np.array([1.0] + [float(e == x) for x in eras_present[1:]] + [float(c == x) for x in CATALOGS[1:]])[keep_cols]
            tot += wcat[c] * float(m.predict(row[None, :])[0])
        vals[e] = tot / sum(wcat.values())
    std[f] = vals
    m0 = sm.GLM(y, Xd[:, [0] + list(range(len(eras_present), Xd.shape[1]))], family=sm.families.Binomial(),
                var_weights=n_cell + 0.5).fit()
    lr[f] = float(m0.deviance - m.deviance)
out['standardised_prevalence'] = std
out['era_LR_chi2'] = lr
out['era_LR_df'] = len(eras_present) - 1


# 3 ---------------------------------------------------------------- ancient vs modern MH odds ratios
def strata(rs, f, feat_exposed):
    s = []
    for c in CATALOGS:
        a = b = cc = d = 0
        for r in rs:
            if r['cat'] != c:
                continue
            if r['year'] < 1800:
                if f in r['fs']: a += 1
                else: b += 1
            elif r['year'] >= 1947:
                if f in r['fs']: cc += 1
                else: d += 1
        s.append((a, b, cc, d))
    return s


ORS = {}
for cls, rs in (('unexplained', UNX), ('natural', [r for r in CAT if r['natural']])):
    ORS[cls] = {}
    for f in FEATS:
        ORS[cls][f] = mh_or(strata(rs, f, True))
out['ancient_vs_modern_MH_OR'] = ORS
out['n_ancient_modern'] = {cls: [sum(1 for r in rs if r['year'] < 1800), sum(1 for r in rs if r['year'] >= 1947)]
                           for cls, rs in (('unexplained', UNX), ('natural', [r for r in CAT if r['natural']]))}
print('ancient/modern n:', out['n_ancient_modern'])


def stable(o):
    return o[1] >= 0.5 and o[2] <= 2.0


# length-adjusted version: logistic regression per feature, ancient (<1800) vs modern (1947+), with
# catalog fixed effects and log(words) - ancient entries could simply be shorter and so carry fewer features
BOTH = [c for c in CATALOGS if any(r['cat'] == c and r['year'] < 1800 for r in UNX) and any(r['cat'] == c and r['year'] >= 1947 for r in UNX)]
AM = [r for r in UNX if r['cat'] in BOTH and (r['year'] < 1800 or r['year'] >= 1947)]
Xa = np.array([[1.0, float(r['year'] < 1800), math.log1p(len((r['text'] or '').split()))] + [float(r['cat'] == c) for c in BOTH[1:]]
               for r in AM])
ADJ = {}
for f in FEATS:
    y = np.array([float(f in r['fs']) for r in AM])
    if y[Xa[:, 1] == 1].sum() < 3 or y[Xa[:, 1] == 0].sum() < 3:
        ADJ[f] = (float('nan'),) * 3
        continue
    try:
        m = sm.GLM(y, Xa, family=sm.families.Binomial()).fit()
        b, se = m.params[1], m.bse[1]
        ADJ[f] = (math.exp(b), math.exp(b - 1.96 * se), math.exp(b + 1.96 * se))
    except Exception:
        ADJ[f] = (float('nan'),) * 3
out['ancient_vs_modern_adjusted_OR'] = dict(catalogs=BOTH, n_ancient=int(Xa[:, 1].sum()), n_modern=int((1 - Xa[:, 1]).sum()), OR=ADJ)
out['stable_unexplained'] = [f for f in FEATS if not math.isnan(ORS['unexplained'][f][0]) and stable(ORS['unexplained'][f])]
print('\nfeature        MH OR unexpl (95% CI)  length-adj OR unexpl     MH OR natural (95% CI)')
for f in PHYS + OLD_FRAMES + TECH_FRAMES + ENTITY_F + VOICE_F:
    u, n, a = ORS['unexplained'][f], ORS['natural'][f], ADJ[f]
    print(f'{f:14s} {u[0]:6.2f} ({u[1]:.2f}-{u[2]:.2f})   {a[0]:6.2f} ({a[1]:.2f}-{a[2]:.2f})   {n[0]:6.2f} ({n[1]:.2f}-{n[2]:.2f})')
# does the unexplained drift pattern track the mundane drift pattern?
fs_cmp = [f for f in PHYS + ENTITY_F if f not in NAMING and all(np.isfinite(ORS[c][f][0]) and ORS[c][f][0] > 0 for c in ORS)]
lu = np.log([ORS['unexplained'][f][0] for f in fs_cmp]); ln = np.log([ORS['natural'][f][0] for f in fs_cmp])
out['drift_pattern_corr_unexpl_vs_natural'] = dict(features=fs_cmp, pearson_r=float(np.corrcoef(lu, ln)[0, 1]),
                                                     mean_abs_logOR_unexpl=float(np.mean(np.abs(lu))),
                                                     mean_abs_logOR_natural=float(np.mean(np.abs(ln))))
print('\nlog-OR pattern r(unexplained, natural) =', round(out['drift_pattern_corr_unexpl_vs_natural']['pearson_r'], 3),
      '| mean |logOR| unexpl', round(float(np.mean(np.abs(lu))), 3), 'natural', round(float(np.mean(np.abs(ln))), 3))

# 4 ---------------------------------------------------------------- era boundaries inside one compiler
# divergence grows with nothing but sample size if raw n is used, so every era is subsampled to the same n
# (NB records, 200 draws) and compared with the split-half null at that n.
DESC = [f for f in PHYS + OLD_FRAMES + TECH_FRAMES + ENTITY_F]
NB = 40
bound = {}
for c in ('HATCH', 'EBERHART', 'OVERMEIRE', 'JOHNSON', 'NICAP', 'RR0'):
    rs = [r for r in UNX if r['cat'] == c]
    by = collections.defaultdict(list)
    for r in rs:
        by[r['era']].append(r)
    es = [e for e in ERA_NAMES if len(by[e]) >= NB]
    res = []
    for e1, e2 in zip(es, es[1:]):
        obs, nul = [], []
        for _ in range(200):
            a = rng.sample(by[e1], NB); b = rng.sample(by[e2], NB)
            obs.append(jsd(prev(a, DESC), prev(b, DESC)))
            pool = a + b; rng.shuffle(pool)
            nul.append(jsd(prev(pool[:NB], DESC), prev(pool[NB:], DESC)))
        res.append(dict(pair=[e1, e2], n=[len(by[e1]), len(by[e2])], jsd=float(np.mean(obs)), null_mean=float(np.mean(nul)),
                        excess=float(np.mean(obs) / np.mean(nul)), p_gt_null=float(np.mean(np.array(obs) > np.percentile(nul, 95)))))
    bound[c] = res
out['era_boundaries'] = dict(n_per_era=NB, by_catalog=bound)
print(f'\nadjacent-era divergence at n={NB} per era / split-half null at the same n (x times noise):')
for c, res in bound.items():
    print(' ', c, ' | '.join(f"{x['pair'][0].split()[0]}>{x['pair'][1].split()[0]}:{x['excess']:.2f}" for x in res))

# 5 ---------------------------------------------------------------- compiler effect on the same event
# Only firm links: same full date (year, month, day all given), different catalogs, word overlap >= 0.2.
# (Union-find events chain loosely; kappa on those pairs was 0.08, on firm links it is far higher.)
_W = re.compile(r"[a-z]{4,}")
_ST = set('that this with from were they their there which when what have been into over then them than also about '
          'object objects light lights seen saw observed appeared sky witnesses event'.split())


def _w(t):
    return {w for w in _W.findall((t or '').lower()) if w not in _ST}


ev = collections.defaultdict(list)
for r in CAT:
    if r['year'] < 1947:
        ev[r['event']].append(r)
byd = collections.defaultdict(list)
for r in CAT:
    if r['year'] < 1947 and r['month'] and r['day']:
        byd[(r['year'], r['month'], r['day'])].append(r)
pairs = []
for v in byd.values():
    for a, b in itertools.combinations(v, 2):
        if a['cat'] != b['cat']:
            wa, wb = _w(a['raw']), _w(b['raw'])
            if len(wa & wb) / max(1, len(wa | wb)) >= 0.2:
                pairs.append((a, b))
kap = {}
for f in DESC + VOICE_F:
    N = len(pairs)
    n11 = sum(1 for a, b in pairs if f in a['fs'] and f in b['fs'])
    n10 = sum(1 for a, b in pairs if (f in a['fs']) != (f in b['fs']))
    pa = sum((f in a['fs']) + (f in b['fs']) for a, b in pairs) / (2 * N)
    po = 1 - n10 / N
    pe = pa * pa + (1 - pa) * (1 - pa)
    kap[f] = dict(any=n11 + n10, both=n11, kappa=(po - pe) / (1 - pe) if pe < 1 else float('nan'))
out['compiler_agreement'] = dict(n_pairs=len(pairs), catalog_pairs=collections.Counter('|'.join(sorted((a['cat'], b['cat']))) for a, b in pairs),
                                 per_feature=kap)
good = [f for f in DESC + VOICE_F if kap[f]['any'] >= 20]
print(f'\nfirm same-event pairs: {len(pairs)}; median kappa over', len(good), 'features =',
      round(float(np.median([kap[f]['kappa'] for f in good])), 2))
print('  ', ', '.join(f"{f}:{kap[f]['kappa']:.2f}" for f in sorted(good, key=lambda f: -kap[f]['kappa'])))

# 6 ---------------------------------------------------------------- LLM paraphrase vs other catalogs, same events
llm = collections.Counter(); oth = collections.Counter(); npair = 0
for v in ev.values():
    w = [r for r in v if r['cat'] == 'WITS']; o = [r for r in v if r['cat'] not in LLM_CATS]
    if w and o:
        npair += 1
        for f in DESC + VOICE_F:
            llm[f] += any(f in r['fs'] for r in w)
            oth[f] += np.mean([f in r['fs'] for r in o])
out['llm_paraphrase_check'] = dict(n_events=npair, wits=dict(llm), others_mean=dict(oth))
print(f'\nWITS paraphrase vs other catalogs on {npair} shared events (events with feature):')
print('  ', ', '.join(f"{f}:{llm[f]}/{oth[f]:.0f}" for f in DESC + VOICE_F if llm[f] + oth[f] >= 8))

# 7 ---------------------------------------------------------------- Obsequens vs catalog antiquity
obs = [r for r in R if r['cat'] == 'OBSEQUENS']
e0 = [r for r in UNX if r['era'] == 'E0 antiquity <500']
po, pc = prev(obs, DESC + VOICE_F), prev(e0, DESC + VOICE_F)
out['obsequens_vs_catalog_antiquity'] = dict(n=[len(obs), len(e0)], feats=DESC + VOICE_F, obsequens=po.tolist(), catalogs=pc.tolist())
print(f'\nObsequens (n={len(obs)}) vs catalog antiquity (n={len(e0)}):')
print('  ', ', '.join(f"{f}:{a*100:.0f}/{b*100:.0f}" for f, a, b in zip(DESC + VOICE_F, po, pc) if a + b >= 0.05))
dump('drift.json', out)
