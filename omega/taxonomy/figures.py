"""Figures for omega/reports/craft_taxonomy.md (static PNG; every number in them is also in
the report's tables). Palette: the dataviz reference palette (validated: blue/orange pass
CVD and normal-vision checks; orange is under 3:1 on white, so every orange mark is also
direct-labelled or shape-coded).
"""
import gzip, json, os, sys, re, collections, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = f'{ROOT}/data/processed/taxonomy'
OUT = f'{ROOT}/omega/reports/figures'
os.makedirs(OUT, exist_ok=True)

BLUE, ORANGE, GRAY = '#257de0', '#f47230', '#8a8a8a'
INK, INK2, GRID, AXIS = '#191919', '#666666', '#e7e7e7', '#c2c2c2'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9, 'text.color': INK, 'axes.labelcolor': INK2,
    'axes.edgecolor': AXIS, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.grid': True,
    'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.titleweight': 'bold', 'axes.titlesize': 10, 'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'savefig.dpi': 200, 'savefig.bbox': 'tight'})


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan, np.nan
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def fig_drift_forest():
    d = json.load(open(f'{P}/drift.json'))
    keep = [
        ('CONTROL Starlink 2019-05: NUFORC shape=formation', 'Starlink trains, May 2019: "formation" (NUFORC)'),
        ('CONTROL lanterns ~2008: GEIPAN orange/red ball or light', 'Sky lanterns, ~2008: orange ball/light (GEIPAN)'),
        ('CONTROL lanterns ~2008: NUFORC orange/red ball or light', 'Sky lanterns, ~2008: orange ball/light (NUFORC)'),
        ('Arnold 1947: Hatch disc among NON-cigar reports (composition removed)', 'Arnold "flying saucer", 1947: disc (Hatch)'),
        ('NYT Tic Tac 2017-12: NUFORC reporter-chosen shape cigar|cylinder', 'NYT "Tic Tac" story, Dec 2017: cigar (NUFORC)'),
        ('NYT 2017-12: NUFORC metallic', 'NYT story, Dec 2017: metallic (NUFORC)'),
        ('Close Encounters 1977-11: Hatch large/"mothership"', 'Close Encounters, 1977: very large (Hatch)'),
        ('Close Encounters 1977-11: Hatch multicolour or beam', 'Close Encounters, 1977: colours or beam (Hatch)'),
        ('Belgian wave / F-117+B-2 reveal 1989: Hatch triangle', 'Belgian wave / stealth jets, 1989: triangle (Hatch)'),
        ('Belgian wave / F-117+B-2 reveal 1989: GEIPAN triangle', 'Belgian wave / stealth jets, 1989: triangle (GEIPAN)'),
        ('Phoenix Lights 1997-03: NUFORC triangle (prompt reports)', 'Phoenix Lights, 1997: triangle (NUFORC)'),
    ]
    T = {t['name']: t for t in d['tests'] if 'OR' in t}
    rows = [(lab, T[n]) for n, lab in keep if n in T]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for i, (lab, t) in enumerate(rows):
        y = len(rows) - 1 - i
        ctrl = t['kind'].startswith('control')
        col = BLUE if ctrl else ORANGE
        beats = (t.get('placebo_pct_abs') or 0) >= 0.95
        ax.plot([t['lo'], t['hi']], [y, y], color=col, lw=2, solid_capstyle='round', zorder=2)
        ax.scatter([t['OR']], [y], s=46, marker='o' if ctrl else 'D', zorder=3,
                   facecolor=col if beats else 'white', edgecolor=col, linewidth=1.6)
        from report import trend_status
        st = {'holds': 'net of trend: holds', 'not separable from trend': 'net of trend: gone',
              'too noisy to adjust': 'net of trend: too noisy'}.get(trend_status(t), '')
        ax.text(t['hi'] * 1.08, y, 'OR %.2f   %s' % (t['OR'], st), va='center', fontsize=7.5, color=INK2)
    ax.axvline(1, color=AXIS, lw=1, zorder=1)
    ax.set_xscale('log')
    ax.set_xticks([0.25, 0.5, 1, 2, 4, 8]); ax.set_xticklabels(['0.25', '0.5', '1', '2', '4', '8'])
    ax.set_xlim(0.2, 40)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([lab for lab, _ in rows][::-1])
    ax.grid(axis='y', visible=False)
    ax.set_xlabel('Odds ratio, share of reports after vs before the date (95% CI, log scale)')
    ax.set_title('Controls show real changes; of the pop-culture dates only 1947 "disc" is clear', loc='left')
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker='o', ls='', mfc=BLUE, mec=BLUE, label='Control: known new physical stimulus'),
         Line2D([], [], marker='D', ls='', mfc=ORANGE, mec=ORANGE, label='Pop-culture date'),
         Line2D([], [], marker='o', ls='', mfc='white', mec=INK2, label='Hollow: no bigger than at 95% of placebo dates')]
    ax.legend(handles=h, loc='upper left', bbox_to_anchor=(-0.02, -0.13), ncol=3, fontsize=7.5, frameon=False)
    fig.savefig(f'{OUT}/drift_forest.png'); plt.close(fig)


def fig_drift_series():
    import drift
    nu, ha, ge = drift.prompt_records()
    has = drift.has
    orange_ball = drift.allf(has('red_orange'), drift.anyf(has('sphere'), has('fireball'), has('light')))
    panels = [
        ('Disc share of Hatch reports', ha, has('disc'), 1935, 1965, 1947, 'Arnold, Jun 1947'),
        ('Cigar/cylinder share of NUFORC reports', nu, lambda r: r['shape_field'] in ('cigar', 'cylinder'), 2005, 2021, 2017.96, 'NYT, Dec 2017'),
        ('"Formation" share of NUFORC reports (control)', nu, lambda r: r['shape_field'] == 'formation', 2005, 2021, 2019.4, 'Starlink, May 2019'),
        ('Orange ball/light share of GEIPAN cases (control)', ge, orange_ball, 1995, 2022, 2008, 'Lanterns, ~2008'),
    ]
    fig, axs = plt.subplots(2, 2, figsize=(8, 5.4))
    for ax, (title, rs, pred, y0, y1, ym, lab) in zip(axs.flat, panels):
        n = collections.Counter(); k = collections.Counter()
        for r in rs:
            if r.get('year') and y0 <= r['year'] <= y1:
                n[r['year']] += 1; k[r['year']] += pred(r)
        ys = [y for y in range(y0, y1 + 1) if n[y] >= 15]
        p = np.array([wilson(k[y], n[y]) for y in ys])
        ax.fill_between(ys, 100 * p[:, 1], 100 * p[:, 2], color=BLUE, alpha=0.15, lw=0)
        ax.plot(ys, 100 * p[:, 0], color=BLUE, lw=2)
        ax.axvline(ym, color=INK2, lw=1, ls=(0, (3, 3)))
        ax.text(ym, ax.get_ylim()[1] * 0.98, ' ' + lab, fontsize=7.5, color=INK2, va='top')
        ax.set_title(title, loc='left', fontsize=9)
        ax.set_ylabel('% of reports')
        ax.set_ylim(bottom=0)
    fig.text(0.01, -0.02, 'Bands: 95% Wilson interval. Years with fewer than 15 reports omitted. NUFORC: only reports posted '
             'within a year of the event. Hatch has no data after ~2000.', fontsize=7, color=INK2)
    fig.tight_layout()
    fig.savefig(f'{OUT}/drift_series.png'); plt.close(fig)


def fig_map():
    import sites
    D = json.load(gzip.open(f'{P}/records.json.gz'))
    g = np.load(f'{P}/pop_usa_005.npz')
    pop, LAT0, LON0, RES = g['grid'], float(g['lat0']), float(g['lon0']), float(g['res'])
    agg = 10                                     # 0.5 deg
    h, w = pop.shape[0] // agg, pop.shape[1] // agg
    P5 = pop[:h * agg, :w * agg].reshape(h, agg, w, agg).sum((1, 3))
    C = np.zeros_like(P5)
    for r in D['records']:
        if r['src'] == 'NUFORC' and r['country'] == 'United States' and r['lat'] is not None:
            a = int((r['lat'] - LAT0) / (RES * agg)); b = int((r['lon'] - LON0) / (RES * agg))
            if 0 <= a < h and 0 <= b < w:
                C[a, b] += 1
    lat = LAT0 + (np.arange(h) + 0.5) * RES * agg; lon = LON0 + (np.arange(w) + 0.5) * RES * agg
    conus = (lat[:, None] > 24) & (lat[:, None] < 50) & (lon[None, :] > -125) & (lon[None, :] < -66)
    m = conus & (P5 >= 5000)
    ratio = np.where(m, (C / C[m].sum()) / np.maximum(P5 / P5[m].sum(), 1e-12), np.nan)
    val = np.log2(np.clip(ratio, 1 / 16, 16))
    val[m & (C == 0)] = -4
    cmap = LinearSegmentedColormap.from_list('div', ['#0f4a96', '#519ced', '#efefef', '#f08a8a', '#b52a2b'])
    fig, ax = plt.subplots(figsize=(8.4, 4.9))
    im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(val), cmap=cmap, vmin=-4, vmax=4, shading='nearest')
    civ, mil = sites.airports()
    ml = np.array([(p[0], p[1]) for p in mil if p[2] == 'US'])
    nuc = np.array([(p[0], p[1]) for p in sites.nuclear() if p[2] == 'US' and p[5] >= 1995])
    ax.scatter(ml[:, 1], ml[:, 0], s=5, marker='o', facecolor='none', edgecolor=INK, linewidth=0.6, label='Military airfield (name-based proxy)')
    ax.scatter(nuc[:, 1], nuc[:, 0], s=14, marker='^', color=INK, linewidth=0, label='Nuclear power reactor (operating 1995 or later)')
    ax.set_xlim(-125, -66); ax.set_ylim(24, 50); ax.set_aspect(1 / np.cos(np.radians(37)))
    ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)
    cb = fig.colorbar(im, ax=ax, orientation='horizontal', fraction=0.05, pad=0.02, aspect=40)
    cb.set_ticks([-4, -2, 0, 2, 4]); cb.set_ticklabels(['1/16x or none', '1/4x', 'as population predicts', '4x', '16x'])
    cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7.5, colors=INK2)
    ax.set_title('NUFORC reports per person, relative to the US average (0.5 degree cells)', loc='left')
    ax.legend(loc='lower left', fontsize=7, frameon=False)
    fig.text(0.01, 0.0, 'Population: Meta/CIESIN HRSL 2019. Cells under 5,000 people left blank. Reports are geocoded to '
             'settlement centroids. Unadjusted; the adjusted rate ratios are in the report.', fontsize=6.8, color=INK2)
    fig.savefig(f'{OUT}/nuforc_per_capita_map.png'); plt.close(fig)


def fig_profiles():
    S = json.load(open(f'{P}/stability.json'))
    srcs = [s for s in ('HATCH', 'NUFORC') if s in S['models']]
    F = S['models'][srcs[0]]['cols']
    fig, axs = plt.subplots(1, len(srcs), figsize=(4.2 * len(srcs), 6.4), squeeze=False)
    cmap = LinearSegmentedColormap.from_list('seq', ['#ffffff', '#cce3fd', '#84b9f3', '#338ced', '#1b64be', '#0e3d7e'])
    for ax, s in zip(axs[0], srcs):
        th = np.array(S['models'][s]['theta']); pi = S['models'][s]['pi']
        ax.imshow(th.T, aspect='auto', cmap=cmap, vmin=0, vmax=1)
        ax.set_yticks(range(len(F))); ax.set_yticklabels(F, fontsize=7)
        labs = S['models'][s]['labels']
        short = ['other' if l.startswith('residual') else l.split()[0] for l in labs]
        ax.set_xticks(range(len(pi))); ax.set_xticklabels(['%s\n%.0f%%' % (n_, 100 * p) for n_, p in zip(short, pi)], fontsize=7)
        ax.grid(False)
        for k in range(th.shape[0]):
            for j in range(th.shape[1]):
                if th[k, j] >= 0.25:
                    ax.text(k, j, '%.0f' % (100 * th[k, j]), ha='center', va='center', fontsize=6,
                            color='white' if th[k, j] > 0.6 else INK)
        ax.set_title('%s classes (share of reports)' % (s if s == 'NUFORC' else s.title()), loc='left', fontsize=9)
    fig.text(0.01, -0.01, 'Cell = probability (%) that a report in the class has the feature; shown where 25% or more. '
             'Duration rows (dur_*) are shares among reports that state a duration.', fontsize=7, color=INK2)
    fig.tight_layout()
    fig.savefig(f'{OUT}/class_profiles.png'); plt.close(fig)


if __name__ == '__main__':
    which = sys.argv[1:] or ['forest', 'series', 'map', 'profiles']
    for w_ in which:
        {'forest': fig_drift_forest, 'series': fig_drift_series, 'map': fig_map, 'profiles': fig_profiles}[w_]()
        print('done', w_)
