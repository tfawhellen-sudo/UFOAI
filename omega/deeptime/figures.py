"""Figures for the deep-time report (static PNG, light surface). Reads drift.json and tech.json from
data/processed/deeptime and the corpus for the decade series. Colours: categorical slots 1-2 of the
validated default palette (blue #257de0, orange #f47230), sequential/ordinal blue ramp; checked with the
dataviz validator. Orange sits below 3:1 on white, so every orange series is also labelled in the legend.
"""
import collections, json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, P, ROOT, ERA_NAMES, CATALOGS  # noqa: E402
from lexicon import PHYS, OLD_FRAMES, TECH_FRAMES, ENTITY_F  # noqa: E402

BLUE, ORANGE, INK, INK2, GRID = '#257de0', '#f47230', '#191919', '#666666', '#e6e6e6'
SEQ = LinearSegmentedColormap.from_list('blue', ['#ffffff', '#cce3fd', '#84b9f3', '#338ced', '#2370cd', '#1757ac', '#0e3d7e'])
FIG = os.path.join(ROOT, 'omega', 'reports', 'figures')
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({'font.size': 8, 'axes.edgecolor': INK2, 'axes.labelcolor': INK, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.titlesize': 9, 'axes.titlecolor': INK, 'legend.frameon': False})
drift = json.load(open(os.path.join(P, 'drift.json')))
tech = json.load(open(os.path.join(P, 'tech.json')))
LABEL = {'f_celestial': 'like a star/moon/sun', 'f_comet': 'comet', 'f_martial': 'shields/swords/armies', 'f_religious': 'cross/angel/omen',
         'f_creature': 'dragon/serpent/bird', 'f_maritime': 'ship/boat/vessel', 'f_torch': 'torch/firebrand', 'f_wheel': 'wheel/chariot',
         'f_balloon': 'balloon', 'f_airship': 'airship/searchlight', 'f_aircraft': 'aircraft/plane', 'f_rocket': 'rocket',
         'f_saucer': 'saucer', 'f_space': 'spaceship/alien', 'f_satellite': 'satellite', 'f_starlink': 'Starlink/satellite train',
         'f_drone': 'drone', 'f_lantern': 'lantern', 'e_occupant': 'occupants/beings', 'e_effect': 'heat/smell/paralysis',
         'size_large': 'large', 'size_small': 'small', 'red_orange': 'red/orange', 'green_blue': 'green/blue'}


def lab(f):
    return LABEL.get(f, f)


FEATS, R = load()
CAT = [r for r in R if r['cat'] in CATALOGS and not r['natural']]
NUF = [r for r in R if r['cat'] == 'NUFORC_MODERN']
NERA = collections.Counter(r['era'] for r in CAT)

# 1 ---------------------------------------------------------------- temporal convergence map
rows = (['f_celestial', 'f_religious', 'f_martial', 'f_creature', 'f_maritime', 'f_torch', 'f_wheel', 'fireball'] +
        ['f_balloon', 'f_airship', 'f_aircraft', 'f_saucer', 'f_space'] +
        ['disc', 'cigar', 'sphere', 'oval', 'triangle', 'metallic', 'formation'] +
        ['light', 'glow', 'beam', 'flashing', 'red_orange', 'white', 'hover', 'fast', 'erratic', 'vanish', 'silent', 'landing', 'e_occupant'])
std = drift['standardised_prevalence']
eras = [e for e in ERA_NAMES if e in std['disc']]
M = np.array([[std[f][e] for e in eras] for f in rows])
Mn = M / M.max(1, keepdims=True)
fig, ax = plt.subplots(figsize=(8.6, 9.2))
ax.imshow(Mn, cmap=SEQ, aspect='auto', vmin=0, vmax=1)
for i in range(len(rows)):
    for j in range(len(eras)):
        v = 100 * M[i, j]
        ax.text(j, i, f'{v:.0f}' if v >= 1 else f'{v:.1f}', ha='center', va='center', fontsize=6.5,
                color='#ffffff' if Mn[i, j] > 0.6 else INK)
ax.set_xticks(range(len(eras)))
ax.set_xticklabels([e.replace(' ', '\n', 1) + f'\nn={NERA[e]:,}' for e in eras], fontsize=7)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([lab(f) for f in rows], fontsize=7.5)
for y in (7.5, 12.5, 19.5):
    ax.axhline(y, color='#ffffff', lw=3)
ax.set_title('Temporal convergence map: % of unexplained reports using each descriptor, by era\n'
             '(standardised to the same mix of nine catalogs; shading = share of the row\'s maximum)', loc='left')
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'deeptime_convergence_map.png'), dpi=150)
plt.close(fig)

# 2 ---------------------------------------------------------------- ancient vs modern odds ratios (forest)
ORu = drift['ancient_vs_modern_adjusted_OR']['OR']
ORn = drift['ancient_vs_modern_MH_OR']['natural']
feats = [f for f in PHYS + OLD_FRAMES + ['f_balloon', 'f_airship', 'f_aircraft', 'f_saucer'] + ENTITY_F
         if ORu.get(f) and ORu[f][0] == ORu[f][0]]
feats.sort(key=lambda f: ORu[f][0])
fig, ax = plt.subplots(figsize=(6.4, 0.2 * len(feats) + 1.4))
ys = np.arange(len(feats))
for k, (src, col, off, name) in enumerate(((ORu, BLUE, -0.15, 'unexplained reports (length-adjusted, within catalog)'),
                                          (ORn, ORANGE, 0.15, 'reports naming a natural phenomenon (Mantel-Haenszel)'))):
    xs, lo, hi, yy = [], [], [], []
    for i, f in enumerate(feats):
        o = src.get(f)
        if o and o[0] == o[0] and o[1] > 0 and math.isfinite(o[2]):
            xs.append(o[0]); lo.append(o[1]); hi.append(min(o[2], 200)); yy.append(i + off)
    ax.hlines(yy, lo, hi, color=col, lw=1.4)
    ax.plot(xs, yy, 'o', color=col, ms=4.5, label=name, markeredgecolor='#ffffff', markeredgewidth=0.8)
ax.axvspan(0.5, 2.0, color='#f2f2f2', zorder=0)
ax.axvline(1, color=INK2, lw=0.8)
ax.set_xscale('log')
ax.set_xlim(0.02, 60)
ax.set_yticks(ys); ax.set_yticklabels([lab(f) for f in feats])
ax.set_xlabel('odds ratio, before 1800 vs after 1947 (log scale; grey band 0.5-2 = "stable")')
ax.set_title('Which descriptors drifted over 2,000 years?\nleft of 1 = more common in modern reports, right = more common before 1800', loc='left')
ax.grid(axis='x', color=GRID, lw=0.6)
ax.legend(loc='lower right', fontsize=7)
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'deeptime_ancient_vs_modern.png'), dpi=150)
plt.close(fig)

# 3 ---------------------------------------------------------------- technology words vs the year the technology appeared
# balloon (1783) is left out: ~100 catalog records before 1783 and the 1780s hits are balloon-ascent context entries.


def series(rs, f, y0, y1, step):
    by = collections.defaultdict(lambda: [0, 0])
    for r in rs:
        if y0 <= r['year'] < y1:
            b = by[(r['year'] - y0) // step * step + y0]
            b[0] += 1; b[1] += f in r['fs']
    xs = sorted(k for k, v in by.items() if v[0] >= 30)
    return xs, [1000 * by[x][1] / by[x][0] for x in xs]


panels = [('f_airship', 1800, 1960, 10, 'C'), ('f_aircraft', 1850, 2010, 10, 'C'), ('f_saucer', 1900, 2010, 5, 'C'),
          ('f_satellite', 1930, 2024, 5, 'CN'), ('f_drone', 2000, 2023, 1, 'N'), ('f_starlink', 2008, 2023, 1, 'N')]
fig, axs = plt.subplots(len(panels), 1, figsize=(6.4, 1.5 * len(panels) + 0.6))
for ax, (f, y0, y1, st, which) in zip(axs, panels):
    t0 = tech['A_tech_frames'][f]['t0']
    if 'C' in which:
        x, y = series(CAT, f, y0, y1, st)
        ax.plot([v + st / 2 for v in x], y, '-', color=BLUE, lw=2, label='compiled catalogs')
    if 'N' in which:
        x2, y2 = series(NUF, f, max(y0, 1950), y1, st)
        ax.plot([v + st / 2 for v in x2], y2, '-', color=ORANGE, lw=2, label='NUFORC witness reports')
    ax.axvline(t0, color=INK, lw=0.9, ls='--')
    ax.text(t0, ax.get_ylim()[1] * 0.95, f' {t0}', fontsize=7, color=INK, va='top')
    ax.set_ylabel('per 1,000', fontsize=7)
    src = {'C': 'compiled catalogs', 'N': 'NUFORC witness reports', 'CN': 'both'}[which]
    ax.set_title(f'"{lab(f)}" ({src}): first public appearance {t0}, '
                 f'{tech["A_tech_frames"][f]["event"].split(";")[0].split("(")[0].split(",")[0].strip()}', loc='left', fontsize=8)
    ax.grid(axis='y', color=GRID, lw=0.6)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    if which == 'CN':
        ax.legend(loc='upper left', fontsize=7)
fig.suptitle('Technology words in UAP reports switch on when the technology appears', x=0.02, ha='left', fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'deeptime_tech_frames.png'), dpi=150)
plt.close(fig)

# 4 ---------------------------------------------------------------- shapes by decade, one compiler vs witnesses
B = tech['B_congruent_by_decade']
shp = [('cigar', 'cigar/cylinder'), ('beam', 'beam/searchlight'), ('disc', 'disc/saucer'), ('triangle', 'triangle'),
       ('sphere', 'sphere/orb'), ('formation', 'formation/line')]
fig, axs = plt.subplots(2, 3, figsize=(8.6, 4.6), sharex=True)
for ax, (f, name) in zip(axs.flat, shp):
    for src, col, nm in (('HATCH', BLUE, 'Hatch database (one compiler)'), ('NUFORC', ORANGE, 'NUFORC (witness text)')):
        xs = [int(d) + 5 for d in B[src]]; v = [100 * B[src][d][f][0] for d in B[src]]
        lo = [100 * B[src][d][f][1] for d in B[src]]; hi = [100 * B[src][d][f][2] for d in B[src]]
        ax.fill_between(xs, lo, hi, color=col, alpha=0.15, lw=0)
        ax.plot(xs, v, '-o', color=col, lw=2, ms=3.5, label=nm)
    ax.set_title(name, loc='left')
    ax.grid(axis='y', color=GRID, lw=0.6)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
for ax in axs[:, 0]:
    ax.set_ylabel('% of reports')
axs[0, 0].legend(loc='upper right', fontsize=6.5)
fig.suptitle('Shapes follow the era: airship-wave cigars and searchlights, 1947 discs, 1980s-90s triangles, 2010s orbs and lines',
             x=0.02, ha='left', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'deeptime_shapes_by_decade.png'), dpi=150)
plt.close(fig)
print('figures written to', FIG)
