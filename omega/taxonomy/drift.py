"""UAP craft taxonomy - step 3: do report features drift with pop-culture milestones?

Each test is a pre-stated prediction: if culture shapes reports, feature X's SHARE of all
reports steps up after milestone M. Shares, not counts, so publicity-driven volume swings
(Art Bell 1997, 2017 NYT, 2019-21 media wave) do not create effects on their own.

Two positive controls with a KNOWN PHYSICAL stimulus and a sharp onset calibrate the method:
  Starlink first train (24 May 2019) -> 'formation' / 'line of lights'
  sky-lantern craze (~2008-2013)     -> orange fireball (GEIPAN identifies lanterns by name)
A cultural milestone that moves a feature as sharply as Starlink did is a strong result;
one that moves it no more than arbitrary dates do is a null.

Statistic: share in a window after M vs the same-length window before (odds ratio, Wald 95% CI
on the log scale). Placebo-in-time null: the same statistic at every other break date in the
series; reported as the percentile of |log OR| at M among all placebo dates.

NUFORC uses only reports POSTED within 365 days of the event (retrospective reports carry the
culture of their posting date, not the event date). Hatch and GEIPAN have no posting date;
GEIPAN cases flagged as late testimony ('témoignage récent', 'observation ancienne') are dropped.
Output: data/processed/taxonomy/drift.json
"""
import gzip, json, os, re, sys, datetime, collections, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = f'{ROOT}/data/processed/taxonomy'
D = json.load(gzip.open(f'{P}/records.json.gz'))
R = D['records']


def nuforc_posted():
    v = json.load(gzip.open(f'{ROOT}/evidence_vault/06_NUFORC_MODERN_ARM/nuforc_unified.json.gz'))['nuforc']
    out = {}
    for r in v:
        p = (r.get('kv') or {}).get('Posted') or ''
        m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', p)
        if not m:
            continue
        y = int(m.group(3)); y = y + (2000 if y < 50 else 1900) if y < 100 else y
        try:
            out[r['uid']] = datetime.date(y, int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass
    return out


def event_date(r):
    if not r.get('year') or not r.get('month'):
        return None
    try:
        return datetime.date(r['year'], r['month'], 15)
    except ValueError:
        return None


def prompt_records():
    post = nuforc_posted()
    nu, ha, ge = [], [], []
    late = re.compile(r"t[ée]moignage r[ée]cent|observation ancienne|des ann[ée]es plus tard|bien des ann[ée]es", re.I)
    for r in R:
        if r['src'] == 'NUFORC':
            e = event_date(r); p = post.get(r['uid'])
            if e and p and 0 <= (p - e).days <= 365:
                nu.append(r)
        elif r['src'] == 'HATCH':
            if r.get('year'):
                ha.append(r)
        else:
            if r.get('year') and not late.search(r['text'] or ''):
                ge.append(r)
    return nu, ha, ge


def has(f):
    return lambda r: f in r['feats']


def txt(rx):
    c = re.compile(rx, re.I)
    return lambda r: bool(c.search(r.get('text') or ''))


def anyf(*preds):
    return lambda r: any(p(r) for p in preds)


def allf(*preds):
    return lambda r: all(p(r) for p in preds)


def tindex(r, unit):
    if unit == 'month':
        return r['year'] * 12 + (r['month'] - 1) if r.get('month') else None
    return r['year']


def series(rs, pred, unit):
    n = collections.Counter(); k = collections.Counter()
    for r in rs:
        t = tindex(r, unit)
        if t is None:
            continue
        n[t] += 1
        if pred(r):
            k[t] += 1
    return n, k


def step(n, k, t0, w, gap=0):
    pre = range(t0 - w, t0); post = range(t0 + gap, t0 + gap + w)
    a = sum(k[t] for t in post); b = sum(n[t] for t in post) - a
    c = sum(k[t] for t in pre); d = sum(n[t] for t in pre) - c
    if min(a + c, b + d) == 0 or sum(n[t] for t in pre) < 30 or sum(n[t] for t in post) < 30:
        return None
    a_, b_, c_, d_ = a + .5, b + .5, c + .5, d + .5
    lor = np.log(a_ * d_ / (b_ * c_)); se = np.sqrt(1 / a_ + 1 / b_ + 1 / c_ + 1 / d_)
    return dict(pre_share=c / (c + d), post_share=a / (a + b), pre_n=c + d, post_n=a + b, pre_k=c, post_k=a,
                OR=float(np.exp(lor)), lo=float(np.exp(lor - 1.96 * se)), hi=float(np.exp(lor + 1.96 * se)), logor=float(lor))


def its(n, k, t0, w):
    """Segmented (interrupted time series) binomial regression over [t0-w, t0+w):
    logit share = a + b*(t-t0) + c*post + d*(t-t0)*post. exp(c) = level change at t0 NET of the
    pre-existing trend (the plain before/after OR cannot separate the two). Quasi-binomial scale."""
    import statsmodels.api as sm
    ts = [t for t in range(t0 - w, t0 + w) if n[t] > 0]
    if len(ts) < 6:
        return None
    tt = np.array(ts, float) - t0; post = (tt >= 0).astype(float)
    X = sm.add_constant(np.column_stack([tt, post, tt * post]))
    yk = np.array([k[t] for t in ts], float); yn = np.array([n[t] for t in ts], float)
    if yk.sum() == 0 or (yn - yk).sum() == 0:
        return None
    try:
        # proportions + var_weights: the 2-column endog form returned a Pearson scale of ~0.01
        # (CIs ~30x too narrow); this form gives the correct overdispersed scale
        m = sm.GLM(yk / yn, X, family=sm.families.Binomial(), var_weights=yn).fit(scale='X2')
    except Exception:
        return None
    b, se = m.params[2], m.bse[2]
    return dict(its_OR=float(np.exp(b)), its_lo=float(np.exp(b - 1.96 * se)), its_hi=float(np.exp(b + 1.96 * se)),
                its_logor=float(b), its_slope_change=float(m.params[3]))


def test(name, rs, pred, unit, t0, w, gap=0, prediction='up', kind='cultural', note=''):
    n, k = series(rs, pred, unit)
    s = step(n, k, t0, w, gap)
    if s is None:
        return dict(name=name, status='insufficient data')
    ts = sorted(n)
    plac = []
    for t in range(ts[0] + w, ts[-1] - w - gap + 1):
        if abs(t - t0) < w:          # placebo dates must not overlap the real windows
            continue
        q = step(n, k, t, w, gap)
        if q:
            plac.append(q['logor'])
    plac = np.array(plac)
    it = its(n, k, t0, w)
    iplac = []
    if it:
        for t in range(ts[0] + w, ts[-1] - w + 1):
            if abs(t - t0) < w:
                continue
            q = its(n, k, t, w)
            if q:
                iplac.append(q['its_logor'])
        iplac = np.array(iplac)
        it['its_placebo_n'] = len(iplac)
        it['its_placebo_pct_abs'] = float((np.abs(iplac) < abs(it['its_logor'])).mean()) if len(iplac) else None
    pct = float((np.abs(plac) < abs(s['logor'])).mean()) if len(plac) else None
    pct_dir = float((plac < s['logor']).mean()) if len(plac) else None
    fmt = (lambda t: '%d-%02d' % (t // 12, t % 12 + 1)) if unit == 'month' else str
    out = dict(name=name, kind=kind, prediction=prediction, unit=unit, break_at=fmt(t0), window=w, gap=gap, note=note,
               placebo_n=len(plac), placebo_pct_abs=pct, placebo_pct_signed=pct_dir, **s, **(it or {}))
    print('%-58s %s  %5.2f%% -> %5.2f%%  OR %.2f (%.2f-%.2f)  n %d/%d  placebo |pct| %s  signed %s' % (
        name, out['break_at'], 100 * s['pre_share'], 100 * s['post_share'], s['OR'], s['lo'], s['hi'],
        s['pre_n'], s['post_n'], 'na' if pct is None else '%.2f' % pct, 'na' if pct_dir is None else '%.2f' % pct_dir), flush=True)
    if it:
        print('%-58s    ITS level change net of trend: OR %.2f (%.2f-%.2f)  placebo |pct| %s' % (
            '', it['its_OR'], it['its_lo'], it['its_hi'],
            'na' if it.get('its_placebo_pct_abs') is None else '%.2f' % it['its_placebo_pct_abs']), flush=True)
    return out


def yearly(rs, pred, y0, y1):
    n, k = series(rs, pred, 'year')
    return {y: [k[y], n[y]] for y in range(y0, y1 + 1)}


def M(y, m):
    return y * 12 + m - 1


def main():
    nu, ha, ge = prompt_records()
    print('prompt NUFORC', len(nu), 'Hatch dated', len(ha), 'GEIPAN contemporaneous', len(ge))
    res = []
    # ---- positive controls (physical stimulus, sharp onset)
    res.append(test('CONTROL Starlink 2019-05: NUFORC "starlink|line/string/train of lights"', nu,
                    txt(r'starlink|line of lights|lights in a (straight )?line|string of lights|train of lights|single file|in a row'),
                    'month', M(2019, 5), 18, kind='control-physical'))
    res.append(test('CONTROL Starlink 2019-05: same, WITHOUT the word "starlink"', nu,
                    allf(txt(r'line of lights|lights in a (straight )?line|string of lights|train of lights|single file|in a row'),
                         lambda r: not re.search(r'starlink', r.get('text') or '', re.I)),
                    'month', M(2019, 5), 18, kind='control-physical', note='the description itself, not the label'))
    res.append(test('CONTROL Starlink 2019-05: NUFORC shape=formation', nu, lambda r: r['shape_field'] == 'formation',
                    'month', M(2019, 5), 18, kind='control-physical'))
    res.append(test('CONTROL lanterns ~2008: NUFORC orange/red fireball', nu, allf(has('fireball'), has('red_orange')),
                    'year', 2008, 4, kind='control-physical', note='onset year approximate (UK/US lantern sales ~2007-09)'))
    orange_ball = allf(has('red_orange'), anyf(has('sphere'), has('fireball'), has('light')))
    res.append(test('CONTROL lanterns ~2008: GEIPAN orange/red fireball', ge, allf(has('fireball'), has('red_orange')),
                    'year', 2008, 5, kind='control-physical'))
    res.append(test('CONTROL lanterns ~2008: GEIPAN orange/red ball or light', ge, orange_ball,
                    'year', 2008, 5, kind='control-physical'))
    res.append(test('CONTROL lanterns ~2008: NUFORC orange/red ball or light', nu, orange_ball,
                    'year', 2008, 4, kind='control-physical'))
    # ---- cultural milestones
    res.append(test('Arnold/"flying saucer" 1947-06: Hatch disc', ha, has('disc'), 'year', 1947, 6,
                    note='yearly; the window 1941-46 vs 1947-52 includes the 1947 wave itself'))
    res.append(test('Arnold/"flying saucer" 1947-06: Hatch disc (gap: 1948-53 vs 1941-46)', ha, has('disc'), 'year', 1947, 6, gap=1))
    res.append(test('Arnold 1947: Hatch cigar (1946 ghost rockets sit in the pre window)', ha, has('cigar'), 'year', 1947, 6,
                    prediction='down if the pre-1947 base is ghost-rocket heavy', kind='composition check'))
    res.append(test('Arnold 1947: Hatch light/nightlight (WWII foo fighters in the pre window)', ha, has('light'), 'year', 1947, 6,
                    prediction='down if the pre-1947 base is foo-fighter heavy', kind='composition check'))
    res.append(test('Arnold 1947: Hatch disc among NON-cigar reports (composition removed)', [r for r in ha if 'cigar' not in r['feats']],
                    has('disc'), 'year', 1947, 6, kind='composition check'))
    res.append(test('Arnold 1947: Hatch triangle/crescent (his own description)', ha, has('triangle'), 'year', 1947, 6,
                    prediction='up if witnesses copied Arnold rather than the press'))
    res.append(test('Close Encounters 1977-11: Hatch large/"mothership"', ha, has('size_large'), 'year', 1978, 4))
    res.append(test('Close Encounters 1977-11: Hatch multicolour or beam', ha, anyf(has('multicolor'), has('beam')), 'year', 1978, 4))
    res.append(test('Close Encounters 1977-11: GEIPAN multicolour or beam', ge, anyf(has('multicolor'), has('beam')), 'year', 1978, 4))
    res.append(test('Belgian wave / F-117+B-2 reveal 1989: Hatch triangle', ha, has('triangle'), 'year', 1990, 6,
                    note='confounded: stealth aircraft unveiled Nov 1988 are a real triangular stimulus'))
    res.append(test('Belgian wave / F-117+B-2 reveal 1989: GEIPAN triangle', ge, has('triangle'), 'year', 1990, 8))
    res.append(test('Phoenix Lights 1997-03: NUFORC triangle (prompt reports)', nu, has('triangle'), 'year', 1998, 2,
                    note='NUFORC prompt-posting data only start 1995; short window'))
    res.append(test('Phoenix Lights 1997-03: NUFORC formation (prompt reports)', nu, has('formation'), 'year', 1998, 2))
    res.append(test('NYT Tic Tac 2017-12: NUFORC cigar/cylinder/tic-tac', nu, has('cigar'), 'month', M(2018, 1), 24))
    res.append(test('NYT Tic Tac 2017-12: NUFORC reporter-chosen shape cigar|cylinder', nu,
                    lambda r: r['shape_field'] in ('cigar', 'cylinder'), 'month', M(2018, 1), 24,
                    note='witness-side field only; summaries are edited by NUFORC staff'))
    res.append(test('NYT Tic Tac 2017-12: NUFORC literal "tic tac"', nu, txt(r'tic[- ]?tac'), 'month', M(2018, 1), 24))
    res.append(test('NYT 2017-12: NUFORC metallic', nu, has('metallic'), 'month', M(2018, 1), 24))
    res.append(test('"orb" word: NUFORC literal "orb" 2008 (digital-camera orbs era)', nu, txt(r'\borbs?\b'), 'year', 2008, 6))
    # ---- yearly share tables for the write-up
    tables = {}
    for nm, rs, pred, a, b in [('hatch_disc', ha, has('disc'), 1935, 2000), ('hatch_triangle', ha, has('triangle'), 1935, 2000),
                               ('hatch_light', ha, has('light'), 1935, 2000), ('geipan_triangle', ge, has('triangle'), 1970, 2022),
                               ('geipan_disc', ge, has('disc'), 1970, 2022), ('geipan_fireball_orange', ge, allf(has('fireball'), has('red_orange')), 1970, 2022),
                               ('nuforc_disc', nu, has('disc'), 1995, 2021), ('nuforc_triangle', nu, has('triangle'), 1995, 2021),
                               ('nuforc_fireball_orange', nu, allf(has('fireball'), has('red_orange')), 1995, 2021),
                               ('nuforc_cigar', nu, has('cigar'), 1995, 2021), ('nuforc_formation', nu, has('formation'), 1995, 2021),
                               ('nuforc_light', nu, has('light'), 1995, 2021)]:
        tables[nm] = yearly(rs, pred, a, b)
    # GEIPAN: how many orange-fireball cases does GEIPAN itself explain as lanterns, by era
    lant = collections.Counter(); tot = collections.Counter()
    orange_ball = allf(has('red_orange'), anyf(has('sphere'), has('fireball'), has('light')))
    for r in ge:
        if orange_ball(r):
            e = 'pre-2008' if r['year'] < 2008 else '2008+'
            tot[e] += 1
            if re.search(r'lanterne|lampion', (r.get('ident') or ''), re.I):
                lant[e] += 1
    gl = {e: [lant[e], tot[e]] for e in tot}
    print('GEIPAN orange ball/light cases explained as lanterns:', gl)
    gly = collections.Counter(r['year'] for r in ge if re.search(r'lanterne', r.get('phen') or '', re.I))
    gall = collections.Counter(r['year'] for r in ge)
    lantern_by_year = {y: [gly[y], gall[y]] for y in range(1995, 2025)}
    print('GEIPAN cases explained as lanterns, by year:', {y: v[0] for y, v in lantern_by_year.items() if v[0]})
    # how retrospective is early NUFORC? (events before 1990 vs the year they were posted)
    post = nuforc_posted()
    pre = [r for r in R if r['src'] == 'NUFORC' and r.get('year') and r['year'] < 1990]
    retro = dict(n=len(pre), posted_1995_or_later=sum(1 for r in pre if post.get(r['uid']) and post[r['uid']].year >= 1995),
                 posted_within_a_year=sum(1 for r in pre if event_date(r) and post.get(r['uid'])
                                          and 0 <= (post[r['uid']] - event_date(r)).days <= 365))
    print('NUFORC events before 1990:', retro)
    json.dump(dict(tests=res, tables=tables, geipan_lantern=gl, geipan_lantern_by_year=lantern_by_year, nuforc_pre1990=retro,
                   n=dict(nuforc_prompt=len(nu), hatch=len(ha), geipan=len(ge))), open(f'{P}/drift.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
