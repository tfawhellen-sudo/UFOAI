"""Task -3.1 - a 'phylogenetic' tree of UAP descriptions, and what organises it.

Descriptions do not reproduce, so a tree here is a map of similarity between description POPULATIONS,
not proof of descent. What a tree can test is which factor its branching follows:
  time     (neighbouring eras on neighbouring branches = cultural transmission / drift),
  compiler (one catalog's eras on one branch = the compiler's voice),
  stimulus (reports naming a natural phenomenon on their own branch = the descriptions encode the stimulus),
  text     (witness-written NUFORC/GEIPAN vs compiler-written catalogs).

Taxa: catalog x era cells with >= 40 unexplained records; Obsequens (191-12 BC primary text); NUFORC by era;
GEIPAN identified (A/B) and unexplained (D); catalog reports naming a natural phenomenon, pooled into three
periods. Characters: prevalence of the physical, frame and entity features (compiler-voice features and the
three features the natural-phenomenon regex itself feeds are left out). Distance: Euclidean on arcsine-sqrt
prevalence (a chord distance). Tree: neighbour joining, midpoint rooted. Support: 200 bootstrap replicates
(records resampled inside each taxon).
Tests: (1) multiple regression on distance matrices (MRM) with 999 permutations; (2) Blomberg's K for time,
compiler type and stimulus class on the tree, 999 tip permutations; (3) delta score (Holland et al. 2002) for
tree-likeness vs a null with each character shuffled across taxa; (4) nearest-neighbour composition.
Writes tree.json and the figure omega/reports/figures/deeptime_tree.png.
"""
import collections, itertools, math, random, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, CATALOGS, ERAS, ERA_NAMES, NAMING, dump, ROOT  # noqa: E402
from lexicon import PHYS, OLD_FRAMES, TECH_FRAMES, ENTITY_F  # noqa: E402

FEATS, R = load()
CH = [f for f in PHYS + OLD_FRAMES + TECH_FRAMES + ENTITY_F if f not in NAMING]
rng = random.Random(3)
nrng = np.random.default_rng(3)
MID = {n: (max(a, -200) + min(b, 2023)) / 2 for n, a, b in ERAS}

# ---------------------------------------------------------------- taxa
taxa = collections.OrderedDict()
for c in CATALOGS:
    for e in ERA_NAMES:
        rs = [r for r in R if r['cat'] == c and r['era'] == e and not r['natural']]
        if len(rs) >= 40:
            taxa[f'{c}|{e.split()[0]}'] = dict(recs=rs, mid=MID[e], kind='catalog', cat=c, natural=0)
obs = [r for r in R if r['cat'] == 'OBSEQUENS']
taxa['OBSEQUENS|BC'] = dict(recs=obs, mid=-100, kind='primary', cat='OBSEQUENS', natural=0)
for e in ('M1 1947-1973', 'M2 1974-1999', 'M3 2000-2025'):
    rs = [r for r in R if r['cat'] == 'NUFORC_MODERN' and r['era'] == e]
    if len(rs) > 3000:
        rs = rng.sample(rs, 3000)
    taxa[f'NUFORC|{e.split()[0]}'] = dict(recs=rs, mid=MID[e], kind='witness', cat='NUFORC', natural=0)
g = [r for r in R if r['cat'] == 'GEIPAN_MODERN']
taxa['GEIPAN-D|all'] = dict(recs=[r for r in g if r.get('gclass') == 'D'], mid=1990, kind='witness', cat='GEIPAN', natural=0)
for e in ('M1 1947-1973', 'M2 1974-1999', 'M3 2000-2025'):
    rs = [r for r in g if r.get('gclass') in ('A', 'B') and r['era'] == e]
    if len(rs) >= 40:
        taxa[f'GEIPAN-AB|{e.split()[0]}'] = dict(recs=rs, mid=MID[e], kind='witness', cat='GEIPAN', natural=1)
for lab, a, b in (('NATURAL|<1800', -300, 1800), ('NATURAL|1800-1946', 1800, 1947), ('NATURAL|1947+', 1947, 2030)):
    rs = [r for r in R if r['cat'] in CATALOGS and r['natural'] and a <= r['year'] < b]
    taxa[lab] = dict(recs=rs, mid=(max(a, 500) + min(b, 2010)) / 2, kind='catalog', cat='NATURAL', natural=1)
names = list(taxa)
N = len(names)
print('taxa:', N, {k: len(v['recs']) for k, v in taxa.items()})


def profile(rs):
    return np.array([sum(f in r['fs'] for r in rs) / len(rs) for f in CH])


def dist(P):
    A = np.arcsin(np.sqrt(np.clip(P, 0, 1)))
    return np.sqrt(((A[:, None, :] - A[None, :, :]) ** 2).sum(-1))


P = np.array([profile(taxa[n]['recs']) for n in names])
Dm = dist(P)


# ---------------------------------------------------------------- neighbour joining
def nj(D, labels):
    """Returns edges [(parent, child, length)] of an unrooted NJ tree; internal nodes are ints >= len(labels)."""
    D = D.copy().astype(float); act = list(range(len(labels))); nxt = len(labels); edges = []
    node_d = {i: {j: D[i, j] for j in range(len(labels))} for i in range(len(labels))}

    def d(i, j):
        return 0.0 if i == j else node_d[i][j]
    while len(act) > 2:
        n = len(act)
        r = {i: sum(d(i, k) for k in act) for i in act}
        best = None
        for i, j in itertools.combinations(act, 2):
            q = (n - 2) * d(i, j) - r[i] - r[j]
            if best is None or q < best[0]:
                best = (q, i, j)
        _, i, j = best
        li = 0.5 * d(i, j) + (r[i] - r[j]) / (2 * (n - 2)); lj = d(i, j) - li
        u = nxt; nxt += 1
        node_d[u] = {}
        for k in act:
            if k not in (i, j):
                v = 0.5 * (d(i, k) + d(j, k) - d(i, j))
                node_d[u][k] = v; node_d[k][u] = v
        edges += [(u, i, max(li, 0.0)), (u, j, max(lj, 0.0))]
        act = [k for k in act if k not in (i, j)] + [u]
    i, j = act
    edges.append((i, j, max(d(i, j), 0.0)))
    return edges


def adjacency(edges):
    adj = collections.defaultdict(list)
    for a, b, l in edges:
        adj[a].append((b, l)); adj[b].append((a, l))
    return adj


def splits(edges, n):
    """Set of leaf bipartitions (frozenset of the side not containing leaf 0) for internal edges."""
    adj = adjacency(edges); out = set()
    for a, b, _ in edges:
        # leaves reachable from b without crossing a
        seen = {a}; stack = [b]; leaves = set()
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            if x < n: leaves.add(x)
            stack += [y for y, _ in adj[x] if y not in seen]
        if 1 < len(leaves) < n - 1:
            s = frozenset(leaves) if 0 not in leaves else frozenset(set(range(n)) - leaves)
            out.add(s)
    return out


def midpoint_root(edges, n):
    """Root at the midpoint of the longest leaf-to-leaf path. Returns (children dict, branch length dict, root)."""
    adj = adjacency(edges)

    def far(src):
        best = (src, 0.0, [src]); stack = [(src, None, 0.0, [src])]
        while stack:
            x, par, dd, path = stack.pop()
            if x < n and dd > best[1]:
                best = (x, dd, path)
            for y, l in adj[x]:
                if y != par:
                    stack.append((y, x, dd + l, path + [y]))
        return best
    a, _, _ = far(0)
    b, L, path = far(a)
    half, acc = L / 2, 0.0
    for x, y in zip(path, path[1:]):
        l = dict(adj[x])[y]
        if acc + l >= half:
            root = 'R'
            cut = half - acc
            new = [(p, q, w) for p, q, w in edges if {p, q} != {x, y}] + [(root, x, cut), (root, y, l - cut)]
            break
        acc += l
    adj = adjacency(new)
    children, blen = collections.defaultdict(list), {}
    stack = [('R', None)]
    while stack:
        x, par = stack.pop()
        for y, l in adj[x]:
            if y != par:
                children[x].append(y); blen[y] = l; stack.append((y, x))
    return children, blen, 'R'


edges = nj(Dm, names)
obs_splits = splits(edges, N)
# bootstrap support
cnt = collections.Counter()
B = 200
for _ in range(B):
    Pb = np.array([profile([rs[i] for i in nrng.integers(0, len(rs), len(rs))]) for rs in (taxa[n]['recs'] for n in names)])
    for s in splits(nj(dist(Pb), names), N) & obs_splits:
        cnt[s] += 1
support = {s: cnt[s] / B for s in obs_splits}
children, blen, root = midpoint_root(edges, N)

# phylogenetic covariance (shared root-to-MRCA path) for Blomberg's K
depth, anc = {root: 0.0}, {root: []}
stack = [root]
while stack:
    x = stack.pop()
    for y in children.get(x, []):
        depth[y] = depth[x] + blen[y]; anc[y] = anc[x] + [x]; stack.append(y)
C = np.zeros((N, N))
for i in range(N):
    for j in range(N):
        if i == j:
            C[i, j] = depth[i]
        else:
            common = set(anc[i]) & set(anc[j])
            C[i, j] = max(depth[x] for x in common)
C += np.eye(N) * 1e-6
Ci = np.linalg.inv(C)
one = np.ones(N)


def blomberg_k(x):
    a = (one @ Ci @ x) / (one @ Ci @ one)
    e = x - a
    mse0 = e @ e / (N - 1); mse = e @ Ci @ e / (N - 1)
    expct = (np.trace(C) - N / (one @ Ci @ one)) / (N - 1)
    return float((mse0 / mse) / expct)


traits = dict(time=np.array([taxa[n]['mid'] for n in names], float),
              natural_stimulus=np.array([taxa[n]['natural'] for n in names], float),
              witness_text=np.array([taxa[n]['kind'] == 'witness' for n in names], float),
              llm_paraphrase_share=np.array([np.mean([r.get('llm', False) for r in taxa[n]['recs']]) for n in names], float))
K = {}
for t, x in traits.items():
    k = blomberg_k(x)
    nul = [blomberg_k(nrng.permutation(x)) for _ in range(999)]
    K[t] = dict(K=k, p=float((1 + sum(v >= k for v in nul)) / 1000), null_median=float(np.median(nul)))
print('Blomberg K:', {t: (round(v['K'], 2), v['p']) for t, v in K.items()})


# ---------------------------------------------------------------- MRM on distance matrices
def lower(M):
    i, j = np.tril_indices(N, -1)
    return M[i, j]


tv = traits['time']
X_time = np.abs(tv[:, None] - tv[None, :]) / 100.0
cat = [taxa[n]['cat'] for n in names]
X_samecat = np.array([[float(cat[i] == cat[j]) for j in range(N)] for i in range(N)])
nat = traits['natural_stimulus']
X_class = (nat[:, None] != nat[None, :]).astype(float)
wit = traits['witness_text']
X_text = (wit[:, None] != wit[None, :]).astype(float)
Xs = [('centuries apart', X_time), ('same compiler', X_samecat), ('natural vs unexplained', X_class), ('witness vs compiler text', X_text)]


def mrm(Dy):
    y = lower(Dy)
    X = np.column_stack([np.ones_like(y)] + [lower(M) for _, M in Xs])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    r2 = 1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return beta, r2


beta, r2 = mrm(Dm)
nb, nr2 = [], []
for _ in range(999):
    p = nrng.permutation(N)
    b, rr = mrm(Dm[p][:, p])
    nb.append(b); nr2.append(rr)
nb = np.array(nb)
MRM = dict(R2=float(r2), p_R2=float((1 + sum(v >= r2 for v in nr2)) / 1000),
           terms={nm: dict(beta=float(beta[k + 1]), p=float((1 + (np.abs(nb[:, k + 1]) >= abs(beta[k + 1])).sum()) / 1000))
                  for k, (nm, _) in enumerate(Xs)})
print('MRM R2', round(r2, 3), 'p', MRM['p_R2'], {k: (round(v['beta'], 3), v['p']) for k, v in MRM['terms'].items()})


# ---------------------------------------------------------------- delta score (tree-likeness)
def delta_mean(D, nq=20000, seed=0):
    rr = np.random.default_rng(seed)
    q = np.array([rr.choice(N, 4, replace=False) for _ in range(nq)])
    x, y, u, v = q.T
    s = np.stack([D[x, y] + D[u, v], D[x, u] + D[y, v], D[x, v] + D[y, u]], 1)
    s.sort(1)
    m3, m2, m1 = s[:, 0], s[:, 1], s[:, 2]
    ok = m1 > m3
    return float(np.mean((m1[ok] - m2[ok]) / (m1[ok] - m3[ok])))


dobs = delta_mean(Dm)
dnull = []
for k in range(100):
    Pn = P.copy()
    for c in range(P.shape[1]):
        Pn[:, c] = nrng.permutation(Pn[:, c])
    dnull.append(delta_mean(dist(Pn), nq=5000, seed=k))
DELTA = dict(observed=dobs, null_mean=float(np.mean(dnull)), null_p025=float(np.percentile(dnull, 2.5)),
             p_lower=float((1 + sum(v <= dobs for v in dnull)) / 101))
print('delta score', round(dobs, 3), 'null', round(float(np.mean(dnull)), 3), 'p', DELTA['p_lower'])

# ---------------------------------------------------------------- nearest neighbours
NN = {}
for i, n in enumerate(names):
    j = int(np.argsort(Dm[i])[1])
    NN[n] = dict(nearest=names[j], d=float(Dm[i, j]), same_compiler=cat[i] == cat[j],
                 centuries_apart=float(abs(tv[i] - tv[j]) / 100))
share_same_cat = float(np.mean([v['same_compiler'] for v in NN.values()]))
share_within_century = float(np.mean([v['centuries_apart'] <= 1.0 for v in NN.values()]))
print(f'nearest neighbour: same compiler {100 * share_same_cat:.0f}%, within 100 years {100 * share_within_century:.0f}%')


# ---------------------------------------------------------------- figure
def draw(path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    order, ypos = [], {}

    def walk(x):
        if x in children and children[x]:
            for y in sorted(children[x], key=lambda z: -len(str(z))):
                walk(y)
        else:
            ypos[x] = len(order); order.append(x)
    walk(root)

    def yof(x):
        if x in ypos:
            return ypos[x]
        ys = [yof(c) for c in children[x]]
        ypos[x] = (min(ys) + max(ys)) / 2
        return ypos[x]
    yof(root)
    fig, ax = plt.subplots(figsize=(9, 0.32 * N + 1.6))
    # ordinal blue ramp, 5 era groups (validated: monotone lightness, visible steps), oldest lightest
    RAMP = ['#84b9f3', '#338ced', '#2370cd', '#1757ac', '#0e3d7e']
    GROUPS = [(-1e9, 1500, 'before 1500'), (1500, 1800, '1500-1799'), (1800, 1896, '1800-1895'), (1896, 1947, '1896-1946'), (1947, 1e9, '1947 on')]

    def era_col(t):
        for k, (a, b, _) in enumerate(GROUPS):
            if a <= t < b:
                return RAMP[k]
    for x in depth:
        for c in children.get(x, []):
            ax.plot([depth[x], depth[x]], [ypos[x], ypos[c]], color='#888', lw=0.8)
            ax.plot([depth[x], depth[c]], [ypos[c], ypos[c]], color='#888', lw=0.8)
            sp = None
            if c not in range(N):
                leaves = set()
                st = [c]
                while st:
                    z = st.pop()
                    if z in range(N): leaves.add(z)
                    st += children.get(z, [])
                s = frozenset(leaves) if 0 not in leaves else frozenset(set(range(N)) - leaves)
                sp = support.get(s)
            if sp is not None and sp >= 0.5:
                ax.text(depth[c], ypos[c] + 0.15, f'{int(round(100 * sp))}', fontsize=6, color='#555', ha='right')
    for i, n in enumerate(names):
        col = era_col(tv[i])
        mk = 's' if taxa[n]['natural'] else ('^' if taxa[n]['kind'] == 'witness' else 'o')
        ax.plot(depth[i], ypos[i], mk, color=col, ms=6)
        ax.text(depth[i] + 0.01, ypos[i], f' {n}  (n={len(taxa[n]["recs"])})', va='center', fontsize=7)
    ax.set_yticks([]); ax.set_xlabel(f'distance from midpoint root (chord distance on {len(CH)} description features)')
    ax.set_title('Neighbour-joining tree of UAP description populations (catalog|era); numbers = bootstrap support %', fontsize=9, loc='left')
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], marker='o', ls='', color=c, label=g[2]) for c, g in zip(RAMP, GROUPS)]
    hs += [Line2D([], [], marker='o', ls='', color='#999', label='compiled catalog'),
           Line2D([], [], marker='^', ls='', color='#999', label='witness-written text'),
           Line2D([], [], marker='s', ls='', color='#999', label='identified / names a natural phenomenon')]
    ax.legend(handles=hs, loc='lower right', fontsize=7, frameon=False)
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    xmax = max(depth.values())
    ax.set_xlim(-0.02, xmax * 1.6)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


figdir = os.path.join(ROOT, 'omega', 'reports', 'figures')
os.makedirs(figdir, exist_ok=True)
draw(os.path.join(figdir, 'deeptime_tree.png'))
dump('tree.json', dict(taxa={n: dict(n=len(taxa[n]['recs']), mid=taxa[n]['mid'], kind=taxa[n]['kind'], cat=taxa[n]['cat'],
                                     natural=taxa[n]['natural']) for n in names},
                       characters=CH, distance=Dm.tolist(), edges=[(str(a), str(b), l) for a, b, l in edges],
                       bootstrap_support={'|'.join(sorted(names[i] for i in s)): v for s, v in support.items()},
                       blomberg_K=K, MRM=MRM, delta=DELTA, nearest=NN,
                       nearest_summary=dict(same_compiler=share_same_cat, within_100y=share_within_century)))
