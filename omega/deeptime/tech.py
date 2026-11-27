"""Task 2.3 - do descriptions track each era's technology (culture) or stay invariant (signal)?
Also the ancient-astronaut claims, restated as predictions the data can fail.

A  technology frames vs the year each technology entered public view (t0):
   rate per 1,000 records before/after t0, change-point year, and every pre-t0 use classified
   (context entry / compiler comparison / quoted period word / bare compiler wording)
B  tech-congruent PHYSICAL descriptors by decade inside one compiler (Hatch) and in witness text (NUFORC)
C  newest-technology share among vehicle-framed reports vs a year-shuffled null
D  invariant primitives vs identified stimuli (GEIPAN A/B, catalog reports naming a natural phenomenon)
E  ancient-astronaut hypotheses AA1-AA5
Writes tech.json.
"""
import collections, math, random, re, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, CATALOGS, ERA_NAMES, wilson, mh_or, dump  # noqa: E402
from lexicon import FRAMES, PHYS  # noqa: E402

FEATS, R = load()
CAT = [r for r in R if r['cat'] in CATALOGS and not r['natural']]
NUF = [r for r in R if r['cat'] == 'NUFORC_MODERN']
GEI = [r for r in R if r['cat'] == 'GEIPAN_MODERN']
rng = random.Random(11)
RX = {f: re.compile(p, re.I) for f, p in FRAMES}
out = {}

# A ---------------------------------------------------------------- technology frames vs t0
TECH = {  # frame: (t0, what happened that year)
    'f_balloon':   (1783, 'Montgolfier hot-air balloon, Annonay and Paris'),
    'f_airship':   (1852, 'Giffard powered dirigible (popular "airship" press: 1896-97 wave)'),
    'f_aircraft':  (1903, 'Wright Flyer (public demonstrations 1908)'),
    'f_saucer':    (1947, '24 June 1947 Arnold sighting; press coins "flying saucer"'),
    'f_space':     (1957, 'Sputnik 1; spaceflight era (Martians in fiction from 1877-1898)'),
    'f_satellite': (1957, 'Sputnik 1'),
    'f_drone':     (2013, 'consumer quadcopters (DJI Phantom, Jan 2013)'),
    'f_starlink':  (2019, 'first Starlink launch, 24 May 2019'),
}
# rockets (fireworks in Europe since the 14th c.) and lanterns (centuries old) have no usable t0.
CONTEXT = re.compile(r"\b(built|invent\w*|patent\w*|constructed|ascent|ascension|experiment\w*|demonstrat\w*|model|"
                     r"memo|writes|published|novel|book|article|newspaper|journal)\b", re.I)
COMPARE = re.compile(r"(resembl\w*|akin|reminiscent|similar to|like (a|an|the) (modern|contemporary)|modern|contemporary|"
                     r"today|nowadays|would (now )?be called|what we (now )?call|precursor|forerunner|early (use|form)|"
                     r"potentially|possibly)", re.I)


def classify(r, f):
    t = r['text']
    m = RX[f].search(t)
    if not m:
        return 'regex-only'
    win = t[max(0, m.start() - 120): m.end() + 60]
    qs = [q.span() for q in re.finditer(r'["“”«»]([^"“”«»]{1,200})["“”«»]', t)]
    if any(a <= m.start() < b for a, b in qs):
        return 'quoted period word'
    if CONTEXT.search(win):
        return 'context entry (not a sighting)'
    if COMPARE.search(win):
        return 'compiler comparison'
    return 'bare compiler wording'


def change_point(years, hits, lo, hi, boot=0):
    """Max-likelihood single step in a Bernoulli rate, on per-year counts (cumulative sums, O(years)).
    boot > 0 also returns a parametric-bootstrap 90% interval (years resampled multinomially, hits binomially)."""
    ys = np.arange(int(years.min()), int(years.max()) + 1)
    n = np.bincount(years - ys[0], minlength=len(ys)).astype(float)
    k = np.bincount(years - ys[0], weights=hits.astype(float), minlength=len(ys))

    def best(n, k):
        cn, ck = np.cumsum(n), np.cumsum(k)
        N, K = cn[-1], ck[-1]
        top = None
        for cp in range(lo, hi + 1):
            i = cp - ys[0]
            if i <= 0 or i >= len(ys):
                continue
            n1, k1 = cn[i - 1], ck[i - 1]
            n2, k2 = N - n1, K - k1
            if n1 < 20 or n2 < 20:
                continue
            p1, p2 = (k1 + .5) / (n1 + 1), (k2 + .5) / (n2 + 1)
            ll = k1 * math.log(p1) + (n1 - k1) * math.log(1 - p1) + k2 * math.log(p2) + (n2 - k2) * math.log(1 - p2)
            if top is None or ll > top[1]:
                top = (cp, ll)
        return top[0] if top else None
    cp = best(n, k)
    if not boot:
        return cp
    nr = np.random.default_rng(5)
    pr = np.where(n > 0, k / np.maximum(n, 1), 0)
    bs = []
    for _ in range(boot):
        nb = nr.multinomial(int(n.sum()), n / n.sum()).astype(float)
        kb = nr.binomial(nb.astype(int), pr).astype(float)
        c = best(nb, kb)
        if c: bs.append(c)
    return cp, ([float(np.percentile(bs, 5)), float(np.percentile(bs, 95))] if bs else None)


A = {}
for f, (t0, what) in TECH.items():
    res = dict(t0=t0, event=what)
    for name, rs in (('catalogs', CAT), ('nuforc', NUF)):
        rs = [r for r in rs if r['year'] >= 1500]
        if not rs:
            continue
        pre = [r for r in rs if r['year'] < t0]; post = [r for r in rs if r['year'] >= t0]
        kp = sum(f in r['fs'] for r in pre); kq = sum(f in r['fs'] for r in post)
        w1 = [r for r in rs if t0 - 50 <= r['year'] < t0]; w2 = [r for r in rs if t0 <= r['year'] < t0 + 50]
        k1 = sum(f in r['fs'] for r in w1); k2 = sum(f in r['fs'] for r in w2)
        res[name] = dict(n_pre=len(pre), hits_pre=kp, per1000_pre=1000 * kp / max(1, len(pre)),
                         n_post=len(post), hits_post=kq, per1000_post=1000 * kq / max(1, len(post)),
                         window50=dict(n_before=len(w1), hits_before=k1, per1000_before=1000 * k1 / max(1, len(w1)),
                                       n_after=len(w2), hits_after=k2, per1000_after=1000 * k2 / max(1, len(w2))))
        yrs = np.array([r['year'] for r in rs], int); hit = np.array([f in r['fs'] for r in rs])
        if hit.sum() >= 15:
            lo, hi = max(int(yrs.min()) + 1, t0 - 150), min(int(yrs.max()) - 1, t0 + 80)
            cp, ci = change_point(yrs, hit, lo, hi, boot=300)
            res[name]['change_point'] = cp
            res[name]['change_point_90ci'] = ci
        if name == 'catalogs':
            cl = collections.Counter(classify(r, f) for r in pre if f in r['fs'])
            res['pre_t0_classes'] = dict(cl)
            res['pre_t0_examples'] = [dict(cat=r['cat'], year=r['year'], cls=classify(r, f), text=r['text'][:220])
                                      for r in pre if f in r['fs']][:60]
            res['pre_t0_by_catalog'] = dict(collections.Counter(r['cat'] for r in pre if f in r['fs']))
    A[f] = res
out['A_tech_frames'] = A
print('A  technology frames: rate per 1,000 unexplained records before / after t0; change point (90% CI)')
for f, x in A.items():
    c = x['catalogs']; nline = ''
    if 'nuforc' in x and x['nuforc']['n_pre']:
        n = x['nuforc']; nline = f" | NUFORC {n['per1000_pre']:.2f} -> {n['per1000_post']:.2f} cp {n.get('change_point')} {n.get('change_point_90ci')}"
    w = c['window50']
    print(f"  {f:12s} t0 {x['t0']}: catalogs 50y before/after {w['per1000_before']:.1f} -> {w['per1000_after']:.1f} (n {w['n_before']}/{w['n_after']}); "
          f"all before/after {c['per1000_pre']:.2f} -> {c['per1000_post']:.2f} (pre hits {c['hits_pre']}) "
          f"cp {c.get('change_point')} {c.get('change_point_90ci')}{nline}")
    print('      pre-t0 uses:', x['pre_t0_classes'], x['pre_t0_by_catalog'])

# B ---------------------------------------------------------------- tech-congruent physical descriptors by decade
CONG = ['cigar', 'beam', 'disc', 'metallic', 'triangle', 'light', 'sphere', 'hover', 'flashing', 'formation', 'fireball']
B = {}
for name, rs, d0, d1 in (('HATCH', [r for r in CAT if r['cat'] == 'HATCH'], 1800, 2010),
                         ('NUFORC', NUF, 1950, 2030)):
    dec = collections.defaultdict(list)
    for r in rs:
        if d0 <= r['year'] < d1:
            dec[(r['year'] // 10) * 10].append(r)
    B[name] = {str(d): dict(n=len(v), **{f: wilson(sum(f in r['fs'] for r in v), len(v)) for f in CONG})
               for d, v in sorted(dec.items()) if len(v) >= 25}
out['B_congruent_by_decade'] = B
print('\nB  share of reports by decade (%), Hatch (one compiler) and NUFORC (witness text)')
for name, tab in B.items():
    print('  ', name, 'decade  n   ' + '  '.join(f'{f[:6]:>6s}' for f in CONG))
    for d, v in tab.items():
        print(f'     {d}  {v["n"]:5d} ' + '  '.join(f'{100 * v[f][0]:6.1f}' for f in CONG))

# C ---------------------------------------------------------------- newest-technology share among vehicle frames
# 1700-1946 only, where the ladder is unambiguous: ships/wheels (ancient) < balloon 1783 < airship 1852 < aircraft 1903.
# A report 'uses the newest' if one of its vehicle frames is the newest technology of its year. Null: years shuffled
# among vehicle-framed reports inside each catalog (keeps each compiler's mix of eras and frames).
LADDER = [('f_maritime', -9999), ('f_wheel', -9999), ('f_balloon', 1783), ('f_airship', 1852), ('f_aircraft', 1903)]
VEH = {f for f, _ in LADDER}


def newest_available(y):
    tmax = max(t for f, t in LADDER if t <= y)
    return {f for f, t in LADDER if t == tmax}


vr = [r for r in CAT if r['fs'] & VEH and 1700 <= r['year'] < 1947]


def share(years):
    return float(np.mean([bool(r['fs'] & newest_available(y)) for r, y in zip(vr, years)]))


obs = share([r['year'] for r in vr])
bycat = collections.defaultdict(list)
for i, r in enumerate(vr):
    bycat[r['cat']].append(i)
nul = []
for _ in range(2000):
    ys = [r['year'] for r in vr]
    for c, idx in bycat.items():
        perm = [vr[i]['year'] for i in idx]; rng.shuffle(perm)
        for i, y in zip(idx, perm):
            ys[i] = y
    nul.append(share(ys))
by_period = {}
for a, b in ((1700, 1783), (1783, 1852), (1852, 1903), (1903, 1947)):
    rs = [r for r in vr if a <= r['year'] < b]
    by_period[f'{a}-{b - 1}'] = dict(n=len(rs), **{f: sum(f in r['fs'] for r in rs) for f, _ in LADDER})
out['C_newest_tech_share'] = dict(n=len(vr), observed=obs, null_mean=float(np.mean(nul)), null_p975=float(np.percentile(nul, 97.5)),
                                  p=float((1 + sum(x >= obs for x in nul)) / (1 + len(nul))), by_period=by_period)
print(f"\nC  vehicle-framed reports 1700-1946 (n={len(vr)}): {100 * obs:.1f}% use the newest technology of their year; "
      f"year-shuffled null {100 * np.mean(nul):.1f}% (97.5th pct {100 * np.percentile(nul, 97.5):.1f}%), p={out['C_newest_tech_share']['p']:.4f}")
for k, v in by_period.items():
    print('   ', k, v)

# D ---------------------------------------------------------------- invariant primitives vs identified stimuli
# GEIPAN classes: A identified, B probably identified, C not enough information, D unexplained after inquiry.
PRIM = ['sphere', 'glow', 'light', 'cigar', 'erratic', 'vanish', 'size_large', 'size_small', 'red_orange', 'white', 'fast', 'hover',
        'disc', 'triangle', 'metallic', 'landing', 'formation', 'flashing']
gc = collections.Counter(r.get('gclass') for r in GEI)
NG = sum(gc[k] for k in 'ABCD')
D = {}
for f in PRIM:
    k = collections.Counter(r.get('gclass') for r in GEI if f in r['fs'])
    n = sum(k[x] for x in 'ABCD')
    D[f] = dict(n=n, AB=wilson(k['A'] + k['B'], n), D=wilson(k['D'], n))
out['D_primitives_vs_identified'] = dict(base=dict(n=NG, AB=(gc['A'] + gc['B']) / NG, D=gc['D'] / NG), per_feature=D)
print(f"\nD  GEIPAN (n={NG}): base A+B {100 * (gc['A'] + gc['B']) / NG:.0f}%, D {100 * gc['D'] / NG:.1f}%. Per feature A+B% / D%:")
print('   ' + ', '.join(f"{f}:{100 * D[f]['AB'][0]:.0f}/{100 * D[f]['D'][0]:.1f}" for f in PRIM if D[f]['n'] >= 20))

# D2: before 1800, the same primitives in reports that name a natural phenomenon vs the rest (same catalogs, same era)
ANC = [r for r in R if r['cat'] in CATALOGS and r['year'] < 1800]
an, au = [r for r in ANC if r['natural']], [r for r in ANC if not r['natural']]
out['D2_pre1800_natural_vs_unexplained'] = dict(n=[len(an), len(au)], per_feature={
    f: dict(natural=wilson(sum(f in r['fs'] for r in an), len(an)), unexplained=wilson(sum(f in r['fs'] for r in au), len(au)))
    for f in PRIM + ['beam', 'f_martial', 'f_religious', 'e_occupant']})
print(f'\nD2 before 1800, natural-named (n={len(an)}) vs unexplained (n={len(au)}), %:')
print('   ' + ', '.join(f"{f}:{100 * v['natural'][0]:.1f}/{100 * v['unexplained'][0]:.1f}"
                        for f, v in out['D2_pre1800_natural_vs_unexplained']['per_feature'].items()))

# E ---------------------------------------------------------------- ancient-astronaut hypotheses
E = {}
CRAFT = {'disc', 'cigar', 'oval', 'triangle', 'rectangle', 'cone', 'diamond', 'metallic'}
CLOSE = {'landing', 'e_occupant'}


def is_craft(r):
    return bool(r['fs'] & CRAFT) and bool(r['fs'] & CLOSE)


strata = []
for c in CATALOGS:
    a = sum(1 for r in CAT if r['cat'] == c and r['year'] < 1800 and is_craft(r))
    b = sum(1 for r in CAT if r['cat'] == c and r['year'] < 1800 and not is_craft(r))
    cc = sum(1 for r in CAT if r['cat'] == c and r['year'] >= 1947 and is_craft(r))
    d = sum(1 for r in CAT if r['cat'] == c and r['year'] >= 1947 and not is_craft(r))
    strata.append((a, b, cc, d))
anc = [r for r in CAT if r['year'] < 1800]; mod = [r for r in CAT if r['year'] >= 1947]
E['AA1_structured_craft_close'] = dict(prediction='structured craft seen close (shape term + landing or occupants) as common before 1800 as after 1947',
                                       pre1800=wilson(sum(map(is_craft, anc)), len(anc)), post1947=wilson(sum(map(is_craft, mod)), len(mod)),
                                       MH_OR_within_catalog=mh_or(strata),
                                       pre1800_excluding_llm=wilson(sum(map(is_craft, [r for r in anc if not r['llm']])), sum(1 for r in anc if not r['llm'])))
occ = collections.defaultdict(lambda: collections.Counter())
for r in CAT + NUF:
    if 'e_occupant' in r['fs'] and r['era']:
        k = occ[r['era']]
        k['n'] += 1
        k['religious_or_creature'] += bool(r['fs'] & {'f_religious', 'f_creature'})
        k['space_alien'] += 'f_space' in r['fs']
        k['airship_aircraft'] += bool(r['fs'] & {'f_airship', 'f_aircraft', 'f_balloon'})
E['AA2_occupant_framing'] = dict(prediction='occupants described the same way in every era (visitors), not in the era\'s mythology',
                                 by_era={e: dict(occ[e]) for e in ERA_NAMES if occ[e]['n']})
obs_q = [r for r in R if r['cat'] == 'OBSEQUENS']
E['AA3_primary_text'] = dict(prediction='an untouched ancient source shows craft features', n=len(obs_q),
                             any_craft_shape=sum(bool(r['fs'] & CRAFT) for r in obs_q), landing_or_occupant=sum(bool(r['fs'] & CLOSE) for r in obs_q),
                             frames=dict(collections.Counter(f for r in obs_q for f in r['fs'] if f.startswith('f_'))))
reg = collections.Counter(r['region'] for r in CAT if r['year'] < 1500)
E['AA5_regions_pre1500'] = dict(prediction='pre-1500 aerial reports concentrate where ancient-astronaut writers place contact '
                                           '(Egypt, Mesopotamia, India, Mesoamerica, Andes)', counts=dict(reg))
out['E_ancient_astronaut'] = E
print('\nE  AA1 structured craft seen close: pre-1800', [round(x * 100, 1) for x in E['AA1_structured_craft_close']['pre1800']],
      'post-1947', [round(x * 100, 1) for x in E['AA1_structured_craft_close']['post1947']],
      'MH OR', [round(x, 2) for x in E['AA1_structured_craft_close']['MH_OR_within_catalog']],
      'pre-1800 without LLM paraphrase', [round(x * 100, 1) for x in E['AA1_structured_craft_close']['pre1800_excluding_llm']])
print('   AA2 occupant framing by era:')
for e, v in E['AA2_occupant_framing']['by_era'].items():
    print(f"     {e:22s} n={v['n']:5d} religious/creature {100 * v.get('religious_or_creature', 0) / v['n']:5.1f}%  "
          f"space/alien {100 * v.get('space_alien', 0) / v['n']:5.1f}%  airship/aircraft {100 * v.get('airship_aircraft', 0) / v['n']:5.1f}%")
print('   AA3 Obsequens:', E['AA3_primary_text'])
print('   AA5 regions pre-1500:', dict(reg))
dump('tech.json', out)
