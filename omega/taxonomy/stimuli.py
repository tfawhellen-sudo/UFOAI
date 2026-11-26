"""UAP craft taxonomy - step 5: what is inside each class?

The decisive test for 'stable classes = real craft types': GEIPAN investigators explained most
of their cases and say WHAT the stimulus was (field 'Phenomenon'). If a class is a craft type,
its unexplained (D) cases should not share the class with explained aircraft, lanterns and
planets. If D cases spread across classes like the explained ones, the classes describe what
people see (stimulus appearance), not what is there.

GEIPAN: per class, the mix of stimulus families and of A/B/C/D; chi-square of D vs A/B across
        classes, with Cramer's V.
Hatch:  per class, rates of the compiler's own flags (MID likely misidentification, HOX hoax,
        HQO high-quality observer, RDR radar, PHT photo, EME, TRC traces) and mean strangeness.
NUFORC: per class, share of summaries that name a conventional explanation.
Output: data/processed/taxonomy/stimuli.json
"""
import gzip, json, os, re, sys, collections, numpy as np
from scipy.stats import chi2_contingency

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = f'{ROOT}/data/processed/taxonomy'

FAMILY = [
    ('lantern', r'lanterne'),
    ('satellite/ISS', r'\biss\b|satellite|iridium|starlink'),
    ('meteor/re-entry', r'bolide|rentr[ée]e|m[ée]t[ée]or'),
    ('astronomical', r'v[ée]nus|lune|sirius|jupiter|mars|saturne|[ée]toile|astre|astronom|plan[eè]te|soleil|arcturus|capella|v[ée]ga'),
    ('aircraft/drone', r'avion|a[ée]ronef|h[ée]licopt|escadrille|drone|tra[iî]n[ée]e|planeur|ulm|parapente'),
    ('balloon', r'ballon'),
    ('ground light/laser', r'laser|sky|animation|projecteur|lumi[eè]re \(sol\)|phare'),
    ('bird/insect', r'oiseau|insecte'),
    ('hoax', r'canular|montage|trucage'),
    ('strange (unexplained)', r'ph[ée]nom[eè]ne [ée]trange'),
    ('insufficient info', r"manque d'information|impr[ée]cis"),
    ('identified, type not given', r'identifi[ée] non indiqu'),
]
FAM_RX = [(n, re.compile(p, re.I)) for n, p in FAMILY]


def family(phen):
    for n, rx in FAM_RX:
        if rx.search(phen or ''):
            return n
    return 'other identified'


NUF_EXPL = re.compile(r'starlink|satellite|\biss\b|space station|lantern|venus|jupiter|planet|\bstar\b|airplane|aircraft|'
                      r'\bplane\b|jet|helicopter|drone|balloon|flare|rocket launch|meteor|chinese lantern', re.I)


def cramers_v(t):
    chi2, p, dof, _ = chi2_contingency(t)
    n = t.sum(); k = min(t.shape) - 1
    return float(np.sqrt(chi2 / (n * k))), float(chi2), float(p), int(dof)


def geipan_d_vs_explained(D):
    """Do GEIPAN's unexplained (D) cases DESCRIBE something different from explained (A/B) ones?
    Per feature: rates, odds ratio adjusted for log text length (D cases are, by GEIPAN's rule,
    the most consistent testimonies, so they are longer and code more features), Wald p, BH q.
    Whole profile: 5-fold cross-validated AUC of an L2 logistic model (features + log length),
    against 200 label permutations; and the same model with log length alone."""
    import statsmodels.api as sm
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.metrics import roc_auc_score
    F = D['features']
    ge = [r for r in D['records'] if r['src'] == 'GEIPAN' and r['gclass'] in ('A', 'B', 'D')]
    X = np.array([[f in r['feats'] for f in F] for r in ge], float)
    y = np.array([r['gclass'] == 'D' for r in ge], float)
    ln = np.log1p([len(r['text'] or '') for r in ge])
    rows = []
    for j, f in enumerate(F):
        a, c = X[y == 1, j].sum(), X[y == 0, j].sum()
        if a + c < 10:
            continue
        try:
            m = sm.GLM(y, sm.add_constant(np.column_stack([ln, X[:, j]])), family=sm.families.Binomial()).fit()
            b, se, p = m.params[2], m.bse[2], m.pvalues[2]
        except Exception:
            continue
        rows.append(dict(feature=f, D_rate=float(a / y.sum()), AB_rate=float(c / (len(y) - y.sum())),
                         OR_len_adj=float(np.exp(b)), lo=float(np.exp(b - 1.96 * se)), hi=float(np.exp(b + 1.96 * se)), p=float(p)))
    ps = np.array([r['p'] for r in rows]); o = np.argsort(ps); m_ = len(ps)
    q = np.empty(m_); run = 1.0
    for rank, i in reversed(list(enumerate(o, 1))):
        run = min(run, ps[i] * m_ / rank); q[i] = run
    for r, qq in zip(rows, q):
        r['q_BH'] = float(qq)
    rows.sort(key=lambda r: r['p'])
    Xf = np.column_stack([X, ln])
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    clf = LogisticRegression(C=0.5, max_iter=2000, class_weight='balanced')
    auc = roc_auc_score(y, cross_val_predict(clf, Xf, y, cv=cv, method='predict_proba')[:, 1])
    auc_len = roc_auc_score(y, cross_val_predict(clf, ln[:, None], y, cv=cv, method='predict_proba')[:, 1])
    rng = np.random.default_rng(1); null = []
    for _ in range(200):
        yp = rng.permutation(y)
        null.append(roc_auc_score(yp, cross_val_predict(clf, Xf, yp, cv=cv, method='predict_proba')[:, 1]))
    null = np.array(null)
    # do features add anything beyond length? permute feature rows within length deciles
    dec = np.digitize(ln, np.quantile(ln, np.linspace(0.1, 0.9, 9)))
    null_len = []
    for _ in range(200):
        Xp = X.copy()
        for d_ in np.unique(dec):
            ii = np.nonzero(dec == d_)[0]
            Xp[ii] = X[rng.permutation(ii)]
        null_len.append(roc_auc_score(y, cross_val_predict(clf, np.column_stack([Xp, ln]), y, cv=cv, method='predict_proba')[:, 1]))
    null_len = np.array(null_len)
    out = dict(n_D=int(y.sum()), n_AB=int(len(y) - y.sum()), features=rows, cv_auc=float(auc), cv_auc_length_only=float(auc_len),
               within_length_perm_auc_mean=float(null_len.mean()), within_length_perm_auc_95=float(np.quantile(null_len, 0.95)),
               within_length_perm_p=float((1 + (null_len >= auc).sum()) / (1 + len(null_len))),
               perm_null_auc_mean=float(null.mean()), perm_null_auc_95=float(np.quantile(null, 0.95)),
               perm_p=float((1 + (null >= auc).sum()) / (1 + len(null))))
    print('GEIPAN D vs A/B: CV AUC %.3f (length only %.3f; permutation null mean %.3f, 95%% %.3f, p %.3f)' % (
        auc, auc_len, null.mean(), np.quantile(null, 0.95), out['perm_p']))
    print('   features beyond length: within-length-decile permutation AUC mean %.3f, 95%% %.3f, p %.3f' % (
        null_len.mean(), np.quantile(null_len, 0.95), out['within_length_perm_p']))
    # per primary shape: how much of each shape GEIPAN explained, and as what
    shapes = ['disc', 'sphere', 'light', 'triangle', 'cigar', 'oval', 'fireball', 'rectangle', 'formation']
    allg = [r for r in D['records'] if r['src'] == 'GEIPAN']
    by = {}
    for sh in shapes:
        rs = [r for r in allg if sh in r['feats']]
        g = collections.Counter(r['gclass'] for r in rs)
        fam = collections.Counter(family(r.get('phen')) for r in rs if r['gclass'] in ('A', 'B'))
        by[sh] = dict(n=len(rs), gclass=dict(g), explained_share=(g['A'] + g['B']) / max(1, len(rs)), D_share=g['D'] / max(1, len(rs)),
                      explained_as=dict(fam.most_common(6)))
        print('   shape %-9s n=%4d  explained %.0f%%  D %.1f%%  as: %s' % (sh, len(rs), 100 * by[sh]['explained_share'], 100 * by[sh]['D_share'],
              ', '.join('%s %d' % kv for kv in fam.most_common(4))))
    out['by_shape'] = by
    for r in rows[:12]:
        print('   %-11s D %.1f%%  A/B %.1f%%  OR(len-adj) %.2f (%.2f-%.2f)  q %.3f' % (
            r['feature'], 100 * r['D_rate'], 100 * r['AB_rate'], r['OR_len_adj'], r['lo'], r['hi'], r['q_BH']))
    return out


def geipan_era_k2(D):
    """Post-hoc diagnostic (added after the 2010+ GEIPAN subset failed to replicate): fit the
    2-class model separately on cases before and from 2010, and say what each class was
    explained as. If the era's second class is a new stimulus (lanterns), the class follows the
    stimulus mix, not a fixed craft type."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lca
    from tdata import matrix, marginal, L
    from stability import label
    rs = [r for r in D['records'] if r['src'] == 'GEIPAN' and r['year']]
    out = {}
    for name, sel in (('pre-2010', lambda r: r['year'] < 2010), ('2010+', lambda r: r['year'] >= 2010)):
        sub = [r for r in rs if sel(r)]
        X, C = matrix(sub); m = lca.fit(X, 2, 12, 0, C=C, L=L); pr = lca.profile(m); mg = marginal(X, C)
        z = lca.assign(X, m, C)
        cl = []
        for k in range(2):
            ks = [r for r, zz in zip(sub, z) if zz == k]
            g = collections.Counter(r['gclass'] for r in ks)
            fam = collections.Counter(family(r.get('phen')) for r in ks if r['gclass'] in ('A', 'B'))
            cl.append(dict(share=float(m['pi'][k]), label=label(pr[k], mg), n=len(ks), gclass=dict(g),
                           explained_as=dict(fam.most_common(5))))
            print('  GEIPAN %-8s class %d %.1f%%  %s  | explained as %s' % (name, k, 100 * m['pi'][k], cl[-1]['label'],
                  ', '.join('%s %d' % kv for kv in fam.most_common(4))))
        out[name] = dict(n=len(sub), classes=cl)
    return out


def main():
    D = json.load(gzip.open(f'{P}/records.json.gz'))
    if len(sys.argv) > 1 and sys.argv[1] == 'dvsab':
        json.dump(geipan_d_vs_explained(D), open(f'{P}/geipan_d_vs_ab.json', 'w'), indent=1)
        return
    A = json.load(gzip.open(f'{P}/assign.json.gz'))
    S = json.load(open(f'{P}/stability.json'))
    out = {}
    # ---- GEIPAN
    ge = [r for r in D['records'] if r['src'] == 'GEIPAN']
    K = S['models']['GEIPAN']['K']; ass = A['GEIPAN']
    fam = collections.defaultdict(collections.Counter); gcl = collections.defaultdict(collections.Counter)
    for r in ge:
        k = ass[r['uid']]
        gcl[k][r['gclass']] += 1
        if r['gclass'] in ('A', 'B'):
            fam[k][family(r.get('phen'))] += 1
    tab = np.array([[gcl[k]['D'], gcl[k]['A'] + gcl[k]['B']] for k in range(K)])
    v, chi2, p, dof = cramers_v(tab)
    out['geipan'] = dict(
        K=K, labels=S['models']['GEIPAN']['labels'],
        classes=[dict(n=sum(gcl[k].values()), gclass=dict(gcl[k]),
                      D_share=gcl[k]['D'] / max(1, sum(gcl[k].values())),
                      explained_family=dict(fam[k].most_common())) for k in range(K)],
        D_vs_AB=dict(table=tab.tolist(), cramers_v=v, chi2=chi2, p=p, dof=dof))
    print('GEIPAN D vs A/B across classes: V=%.3f chi2=%.1f p=%.3g' % (v, chi2, p))
    for k in range(K):
        c = out['geipan']['classes'][k]
        print('  class %d n=%d  D %.1f%%  explained as: %s' % (k, c['n'], 100 * c['D_share'],
              ', '.join('%s %d' % kv for kv in list(c['explained_family'].items())[:6])))
    # ---- Hatch
    ha = [r for r in D['records'] if r['src'] == 'HATCH']
    K = S['models']['HATCH']['K']; ass = A['HATCH']
    flags = ['MID', 'HOX', 'HQO', 'RDR', 'PHT', 'EME', 'TRC', 'MIL', 'NUC', 'LND', 'OID']
    rows = []
    for k in range(K):
        rs = [r for r in ha if ass[r['uid']] == k]
        st = [float(r['strange']) for r in rs if (r.get('strange') or '').replace('.', '').isdigit()]
        cr = [float(r['cred']) for r in rs if (r.get('cred') or '').replace('.', '').isdigit()]
        rows.append(dict(n=len(rs), flags={f: sum(f in (r.get('codes') or []) for r in rs) / len(rs) for f in flags},
                         strangeness=float(np.mean(st)) if st else None, credibility=float(np.mean(cr)) if cr else None))
    base = {f: sum(f in (r.get('codes') or []) for r in ha) / len(ha) for f in flags}
    out['hatch'] = dict(K=K, labels=S['models']['HATCH']['labels'], classes=rows, base=base)
    for k, rw in enumerate(rows):
        print('  Hatch class %d n=%d strange %.1f cred %.1f  %s' % (k, rw['n'], rw['strangeness'] or -1, rw['credibility'] or -1,
              ' '.join('%s %.0f%%' % (f, 100 * rw['flags'][f]) for f in flags)))
    # ---- NUFORC
    nu = [r for r in D['records'] if r['src'] == 'NUFORC']
    K = S['models']['NUFORC']['K']; ass = A['NUFORC']
    rows = []
    for k in range(K):
        rs = [r for r in nu if ass[r['uid']] == k]
        rows.append(dict(n=len(rs), names_explanation=sum(bool(NUF_EXPL.search(r['text'] or '')) for r in rs) / len(rs)))
    out['nuforc'] = dict(K=K, labels=S['models']['NUFORC']['labels'], classes=rows,
                         base=sum(bool(NUF_EXPL.search(r['text'] or '')) for r in nu) / len(nu))
    for k, rw in enumerate(rows):
        print('  NUFORC class %d n=%d  summary names a conventional object %.1f%%' % (k, rw['n'], 100 * rw['names_explanation']))
    out['geipan_era_k2'] = geipan_era_k2(D)
    json.dump(out, open(f'{P}/stimuli.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
