"""PROJECT OMEGA -- Phases 1-3 re-run on the GEIPAN official case file.

Phase 1  provenance: (a) internal event clustering (one stimulus -> many cases),
         (b) linkage of GEIPAN cases into the 26-catalog ufo_data literature,
             and whether the literature over-samples unexplained cases.
Phase 2  nuclear-site proximity with two nulls:
         N1 case-control: unexplained (C, D) vs identified (A, B) cases share
            the same observer/reporting geography, so identified cases ARE the
            spatial null. Region x decade stratified label permutation.
         N2 commissioning: per site, share of nearby cases dated after the site
            entered service vs the national share after that date.
Phase 3  descriptor drift: witness-portion lexicon, logistic slope per decade
         controlling for text length; class and explanation mix over time.

Only the official export is used as case data. The nuclear-site layer is a
hand-entered table (see SITES) and is flagged as such in the report.
"""
import json, re, sys, math, unicodedata, collections as C
import numpy as np
from scipy import stats

sys.path.insert(0, "omega")
SRC = "data/raw/geipan/geipan_cases.json"
OUT = "evidence_vault/11_GEIPAN_PHASE123/geipan_phase123.json"
RNG = np.random.default_rng(20261126)
NPERM = 10000


# ---------------------------------------------------------------- helpers
def strip_acc(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))


def normtok(s):
    s = strip_acc(s).lower().replace("'", " ").replace("-", " ")
    return re.sub(r"[^a-z0-9 ]+", " ", re.sub(r"\s+", " ", s)).strip()


def hav(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 12742.0 * np.arcsin(np.sqrt(a))


def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def or_ci(a, b, c, d):
    """odds ratio a*d/(b*c) with Haldane correction if any cell is 0, Woolf CI."""
    if 0 in (a, b, c, d): a, b, c, d = a + .5, b + .5, c + .5, d + .5
    o = a * d / (b * c); se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return o, o * math.exp(-1.96 * se), o * math.exp(1.96 * se)


def mantel_haenszel(tables):
    """tables: list of (a,b,c,d). Returns OR_MH, RGB 95% CI, MH chi2 p."""
    R = S = 0.0; PR = PSQR = QS = 0.0; num = var = 0.0
    for a, b, c, d in tables:
        n = a + b + c + d
        if n < 2: continue
        r, s = a * d / n, b * c / n
        P, Q = (a + d) / n, (b + c) / n
        R += r; S += s; PR += P * r; PSQR += P * s + Q * r; QS += Q * s
        m1, n1, m0 = a + b, a + c, c + d
        e = m1 * n1 / n; v = m1 * m0 * n1 * (n - n1) / (n * n * (n - 1))
        num += a - e; var += v
    if R == 0 or S == 0: return float("nan"), float("nan"), float("nan"), float("nan")
    o = R / S
    se = math.sqrt(PR / (2 * R * R) + PSQR / (2 * R * S) + QS / (2 * S * S))
    chi = (abs(num) - .5) ** 2 / var if var > 0 else float("nan")
    return o, o * math.exp(-1.96 * se), o * math.exp(1.96 * se), float(stats.chi2.sf(chi, 1))


def logit_fit(X, y, iters=50):
    """IRLS logistic regression; returns beta, se."""
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = np.clip(X @ b, -30, 30); p = 1 / (1 + np.exp(-eta)); w = p * (1 - p) + 1e-9
        H = X.T @ (X * w[:, None]); g = X.T @ (y - p)
        step = np.linalg.solve(H + 1e-8 * np.eye(len(b)), g); b += step
        if np.max(np.abs(step)) < 1e-8: break
    cov = np.linalg.inv(H + 1e-8 * np.eye(len(b)))
    return b, np.sqrt(np.diag(cov))


def bh(ps):
    ps = np.asarray(ps, float); n = len(ps); o = np.argsort(ps)
    q = np.empty(n); prev = 1.0
    for rank, i in reversed(list(enumerate(o, 1))):
        prev = min(prev, ps[i] * n / rank); q[i] = prev
    return q


# ---------------------------------------------------------------- load
cases = json.load(open(SRC, encoding="utf-8-sig"))
for c in cases:
    m = re.fullmatch(r"(\S\S)/(\S\S)/(\S{4})", c["Observation date"])
    d, mo, y = m.groups()
    c["y"] = int(y) if y.isdigit() else None
    c["m"] = int(mo) if mo.isdigit() else None
    c["d"] = int(d) if d.isdigit() else None
    c["dayprec"] = c["d"] is not None and c["m"] is not None and c["y"] is not None
    if c["dayprec"]:
        try: __import__("datetime").date(c["y"], c["m"], c["d"])
        except ValueError: c["d"] = None; c["dayprec"] = False   # e.g. 31/09/2000 in the export
    c["yr"] = c["y"] if c["y"] else int(c["Année"])
    c["lat"], c["lon"] = float(c["Latitude"]), float(c["Longitude"])
    c["metro"] = c["Region"] not in ("Outre-Mer", "Autre") and 41 <= c["lat"] <= 51.6 and -5.5 <= c["lon"] <= 10
    mt = re.match(r"^(.*?)\s*(\((LE|LA|LES|L')\))?\s*\(\w{1,3}\)", c["Titre du Cas"])
    c["commune"] = normtok(mt.group(1) if mt else c["Titre du Cas"].split(" (")[0])
    c["cls"] = c["Classification"]
    c["ord"] = __import__("datetime").date(c["y"], c["m"], c["d"]).toordinal() if c["dayprec"] else None
N = len(cases)
print(f"GEIPAN cases: {N}; day-precise {sum(c['dayprec'] for c in cases)}; metropolitan {sum(c['metro'] for c in cases)}")
R = {"n_cases": N, "class_counts": dict(C.Counter(c["cls"] for c in cases))}


# ================================================================ PHASE 1a
# Internal clustering: cases on the same day within r km are candidate copies of
# one stimulus. Separately: same day + same identified explanation (reentries,
# lantern releases) regardless of distance.
class UF:
    def __init__(s, n): s.p = list(range(n))
    def f(s, x):
        while s.p[x] != x: s.p[x] = s.p[s.p[x]]; x = s.p[x]
        return x
    def u(s, a, b): s.p[s.f(a)] = s.f(b)


byday = C.defaultdict(list)
for i, c in enumerate(cases):
    if c["dayprec"]: byday[c["ord"]].append(i)

p1a = {}
for r_km in (30, 100):
    uf = UF(N)
    for ids in byday.values():
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                i, j = ids[a], ids[b]
                if hav(cases[i]["lat"], cases[i]["lon"], cases[j]["lat"], cases[j]["lon"]) <= r_km: uf.u(i, j)
    comp = C.defaultdict(list)
    for i in range(N): comp[uf.f(i)].append(i)
    sizes = sorted((len(v) for v in comp.values()), reverse=True)
    byc = {}
    for k in "ABCD":
        idx = [i for i in range(N) if cases[i]["cls"] == k]
        roots = {uf.f(i) for i in idx}
        multi = sum(1 for i in idx if len(comp[uf.f(i)]) > 1)
        byc[k] = dict(cases=len(idx), events=len(roots), collapse=round(len(idx) / len(roots), 3),
                      in_multicase_cluster=multi, frac_multi=round(multi / len(idx), 3))
    big = sorted(comp.values(), key=len, reverse=True)[:8]
    p1a[f"{r_km}km"] = dict(events=len(comp), collapse=round(N / len(comp), 3), largest=sizes[:10], by_class=byc,
                            top_clusters=[dict(n=len(v), date=cases[v[0]]["Observation date"],
                                               classes=dict(C.Counter(cases[i]["cls"] for i in v)),
                                               phen=C.Counter(cases[i]["Phenomenon"] for i in v).most_common(2))
                                          for v in big])
# same day + same specific identification, any distance
generic = {"Manque d'informations fiables", "Phénomène identifié non indiqué", "Avion", "Vénus", "Etoile", "Lune"}
same_expl = C.Counter()
for ids in byday.values():
    cnt = C.Counter(cases[i]["Phenomenon"] for i in ids if cases[i]["cls"] in "AB" and cases[i]["Phenomenon"] not in generic)
    for ph, n in cnt.items():
        if n >= 3: same_expl[(cases[ids[0]]["Observation date"], ph)] = n
p1a["same_day_same_explanation_ge3"] = [dict(date=k[0], phen=k[1], n=v) for k, v in same_expl.most_common(12)]
R["phase1a_internal"] = p1a
print("P1a", {k: (v["events"], v["collapse"]) for k, v in p1a.items() if k.endswith("km")})

# ================================================================ PHASE 1b
import corpus
lit, _ = corpus.load_all()          # geipan.json is NOT in CATALOG_META -> excluded
print(f"literature records: {len(lit)}")
FR = re.compile(r"\bfrance\b|\bfrench\b|\bfrancia\b|\bfrankreich\b")
lit_by_day = C.defaultdict(list)
for r in lit:
    if r.prec != "day" or r.year is None or r.year < 1937: continue
    txt = normtok(f"{r.location} {r.country} {r.desc}")
    geo_fr = r.lat is not None and 41 <= r.lat <= 51.6 and -5.5 <= r.lon <= 10
    if not (geo_fr or FR.search(txt)): continue
    try: o = __import__("datetime").date(r.year, r.month, r.day).toordinal()
    except Exception: continue
    refs = " ".join(map(str, r.refs)).lower()
    lit_by_day[o].append((r, " " + txt + " ", "geipan" in refs or "gepan" in refs or "geipan" in txt or "gepan" in txt))

STOP = {"paris", "saint", "sainte", "le", "la", "les"}
links = {}
for i, c in enumerate(cases):
    if not c["dayprec"]: continue
    com = c["commune"]
    hits = []
    for o in (c["ord"] - 1, c["ord"], c["ord"] + 1):
        for r, txt, cites in lit_by_day.get(o, []):
            how = None
            if r.lat is not None and hav(c["lat"], c["lon"], r.lat, r.lon) <= 30: how = "geo30"
            elif len(com) >= 4 and com not in STOP and f" {com} " in txt: how = "commune"
            if how: hits.append((r.catalog, how, cites, r.uid))
    if hits: links[i] = hits
dp = [i for i, c in enumerate(cases) if c["dayprec"]]
in_lit = {i: 1 if i in links else 0 for i in dp}

# hand-audit sample of 25 links (printed for the report)
audit_ids = RNG.choice(sorted(links), size=min(25, len(links)), replace=False)
lit_index = {r.uid: r for r in lit}
audit = []
for i in audit_ids:
    cat, how, cites, uid = links[int(i)][0]
    r = lit_index[uid]
    audit.append(dict(geipan=cases[int(i)]["Titre du Cas"], cls=cases[int(i)]["cls"], how=how, catalog=cat,
                      lit_date=r.date_raw, lit_loc=r.location[:60], lit_desc=r.desc[:160]))

p1b = {"day_precise_cases": len(dp), "linked": len(links)}
p1b["by_class"] = {}
for k in "ABCD":
    idx = [i for i in dp if cases[i]["cls"] == k]; kk = sum(in_lit[i] for i in idx)
    p1b["by_class"][k] = dict(n=len(idx), in_literature=kk, rate=round(kk / len(idx), 4), ci95=[round(x, 4) for x in wilson(kk, len(idx))])
p1b["catalogs"] = C.Counter(cat for h in links.values() for cat in {x[0] for x in h}).most_common()
p1b["linked_records_citing_geipan"] = sum(1 for h in links.values() if any(x[2] for x in h))
p1b["link_method"] = C.Counter(min(x[1] for x in h) for h in links.values())


def strata_tables(idx_case, idx_ctrl, key, outcome):
    t = C.defaultdict(lambda: [0, 0, 0, 0])
    for i in idx_case: t[key(i)][0 if outcome(i) else 1] += 1
    for i in idx_ctrl: t[key(i)][2 if outcome(i) else 3] += 1
    return [tuple(v) for v in t.values()]


dec = lambda i: min(cases[i]["yr"] // 10 * 10, 2020)
for lab, case_set in (("D_vs_AB", "D"), ("CD_vs_AB", "CD"), ("C_vs_AB", "C")):
    ca = [i for i in dp if cases[i]["cls"] in case_set]; co = [i for i in dp if cases[i]["cls"] in "AB"]
    a = sum(in_lit[i] for i in ca); b = len(ca) - a; c_ = sum(in_lit[i] for i in co); d_ = len(co) - c_
    crude = or_ci(a, b, c_, d_)
    mh = mantel_haenszel(strata_tables(ca, co, dec, lambda i: in_lit[i]))
    p1b[lab] = dict(crude_OR=[round(x, 3) for x in crude], fisher_p=float(stats.fisher_exact([[a, b], [c_, d_]])[1]),
                    MH_OR_decade=[round(x, 3) for x in mh[:3]], MH_p=mh[3])
p1b["by_decade"] = {}
for dd in sorted({dec(i) for i in dp}):
    idx = [i for i in dp if dec(i) == dd]
    p1b["by_decade"][dd] = {k: f"{sum(in_lit[i] for i in idx if cases[i]['cls']==k)}/{sum(1 for i in idx if cases[i]['cls']==k)}" for k in "ABCD"}
p1b["audit_sample"] = audit
lit_fr = [(o, r.uid) for o, v in lit_by_day.items() for r, _, _ in v if 1950 <= r.year <= 1999]
matched = {x[3] for h in links.values() for x in h}
p1b["reverse"] = dict(lit_french_dayprec_1950_1999=len(lit_fr), linked_to_geipan=sum(1 for _, u in lit_fr if u in matched),
                      geipan_dayprec_1950_1999=sum(1 for i in dp if 1950 <= cases[i]["yr"] <= 1999),
                      geipan_linked_1950_1999=sum(1 for i in links if 1950 <= cases[i]["yr"] <= 1999))
R["phase1b_literature"] = p1b
print("P1b", p1b["linked"], p1b["by_class"], p1b["D_vs_AB"], p1b["CD_vs_AB"])

# ================================================================ PHASE 2
# Nuclear-site layer. HAND-ENTERED from general knowledge: site coordinates
# (~1-3 km) and first-service year (first unit / first operation). NOT pulled
# from an authoritative source in this run (Wikidata/ASN unreachable from this
# container). Coordinates are cross-checked below against GEIPAN's own commune
# coordinates where a case is filed under the host commune.
SITES = [  # name, kind, lat, lon, first-service year, host commune (normtok)
    ("Belleville", "NPP", 47.510, 2.875, 1987, "belleville sur loire"),
    ("Blayais", "NPP", 45.256, -0.693, 1981, "braud et saint louis"),
    ("Bugey", "NPP", 45.798, 5.271, 1972, "saint vulbas"),
    ("Cattenom", "NPP", 49.416, 6.218, 1986, "cattenom"),
    ("Chinon", "NPP", 47.230, 0.170, 1963, "avoine"),
    ("Chooz", "NPP", 50.090, 4.789, 1967, "chooz"),
    ("Civaux", "NPP", 46.457, 0.653, 1997, "civaux"),
    ("Cruas", "NPP", 44.633, 4.757, 1983, "cruas"),
    ("Dampierre", "NPP", 47.733, 2.517, 1980, "dampierre en burly"),
    ("Fessenheim", "NPP", 47.903, 7.563, 1977, "fessenheim"),
    ("Flamanville", "NPP", 49.536, -1.882, 1985, "flamanville"),
    ("Golfech", "NPP", 44.107, 0.845, 1990, "golfech"),
    ("Gravelines", "NPP", 51.015, 2.136, 1980, "gravelines"),
    ("Nogent", "NPP", 48.515, 3.518, 1987, "nogent sur seine"),
    ("Paluel", "NPP", 49.858, 0.636, 1984, "paluel"),
    ("Penly", "NPP", 49.977, 1.212, 1990, "saint martin en campagne"),
    ("Saint-Alban", "NPP", 45.404, 4.755, 1985, "saint alban du rhone"),
    ("Saint-Laurent", "NPP", 47.720, 1.578, 1969, "saint laurent nouan"),
    ("Tricastin", "NPP+fuel", 44.330, 4.732, 1980, "saint paul trois chateaux"),
    ("Brennilis", "research reactor", 48.355, -3.870, 1967, "brennilis"),
    ("Creys-Malville", "fast breeder", 45.758, 5.472, 1986, "creys mepieu"),
    ("La Hague", "reprocessing", 49.678, -1.879, 1966, "beaumont hague"),
    ("Marcoule", "military/reprocessing", 44.143, 4.709, 1956, "chusclan"),
    ("Cadarache", "CEA research", 43.687, 5.761, 1963, "saint paul lez durance"),
    ("Valduc", "CEA weapons", 47.580, 4.870, 1957, "salives"),
    ("Saclay", "CEA research", 48.710, 2.150, 1952, "saclay"),
    ("Ile Longue", "SSBN base", 48.307, -4.508, 1970, "crozon"),
    ("Plateau d'Albion", "IRBM silos (1971-96)", 44.030, 5.490, 1971, "saint christol"),
]
lat_s = np.array([s[2] for s in SITES]); lon_s = np.array([s[3] for s in SITES])
xcheck = []
for s in SITES:
    hits = [c for c in cases if c["commune"] == s[5]]
    if hits:
        dkm = float(hav(s[2], s[3], hits[0]["lat"], hits[0]["lon"]))
        xcheck.append(dict(site=s[0], commune=s[5], n_cases=len(hits), km_site_to_commune_coord=round(dkm, 1)))
metro = [i for i in range(N) if cases[i]["metro"]]
lat_c = np.array([cases[i]["lat"] for i in metro]); lon_c = np.array([cases[i]["lon"] for i in metro])
D = hav(lat_c[:, None], lon_c[:, None], lat_s[None, :], lon_s[None, :])        # (n_metro, n_sites)
dmin = D.min(1)
cls_m = np.array([cases[i]["cls"] for i in metro])
reg_m = np.array([cases[i]["Region"] for i in metro]); dec_m = np.array([dec(i) for i in metro])
strata = np.array([f"{a}|{b}" for a, b in zip(reg_m, dec_m)])
p2 = {"n_metro": len(metro), "sites": len(SITES), "site_xcheck": xcheck,
      "median_nearest_km": {k: round(float(np.median(dmin[cls_m == k])), 1) for k in "ABCD"}}


def strat_perm(labels, stat_fn, strata, nperm=NPERM):
    obs = stat_fn(labels); cnt = 0; groups = [np.where(strata == s)[0] for s in np.unique(strata)]
    null = np.empty(nperm)
    for k in range(nperm):
        lab = labels.copy()
        for g in groups:
            if len(g) > 1: lab[g] = labels[g][RNG.permutation(len(g))]
        null[k] = stat_fn(lab)
    return obs, null


tests = []
for case_set in ("D", "CD"):
    sel = np.isin(cls_m, list(case_set + "AB"))
    lab = np.isin(cls_m[sel], list(case_set)).astype(int)
    dm, st = dmin[sel], strata[sel]
    for r_km in (10, 20, 30, 50):
        near = dm <= r_km
        a = int((near & (lab == 1)).sum()); b = int(((~near) & (lab == 1)).sum())
        c_ = int((near & (lab == 0)).sum()); d_ = int(((~near) & (lab == 0)).sum())
        o = or_ci(a, b, c_, d_)
        tabs = strata_tables([k for k in range(len(lab)) if lab[k]], [k for k in range(len(lab)) if not lab[k]],
                             lambda k: st[k], lambda k: near[k])
        mh = mantel_haenszel(tabs)
        f = lambda L: L[near].mean()
        obs, null = strat_perm(lab, f, st)
        p = (1 + (null >= obs).sum()) / (1 + NPERM)
        tests.append(dict(contrast=f"{case_set}_vs_AB", r_km=r_km, case_near=a, case_n=a + b, ctrl_near=c_, ctrl_n=c_ + d_,
                          case_rate=round(a / (a + b), 4), case_rate_ci=[round(x, 4) for x in wilson(a, a + b)],
                          ctrl_rate=round(c_ / (c_ + d_), 4), crude_OR=[round(x, 3) for x in o],
                          MH_OR_region_decade=[round(x, 3) for x in mh[:3]], MH_p=mh[3], perm_p_one_sided=float(p)))
    # continuous: nearest distance, rank test + stratified permutation of median-difference
    u = stats.mannwhitneyu(dm[lab == 1], dm[lab == 0], alternative="less")
    obs, null = strat_perm(lab, lambda L: np.median(dm[L == 0]) - np.median(dm[L == 1]), st)
    tests.append(dict(contrast=f"{case_set}_vs_AB", r_km="nearest-distance", MWU_p_less=float(u.pvalue),
                      median_case_km=round(float(np.median(dm[lab == 1])), 1), median_ctrl_km=round(float(np.median(dm[lab == 0])), 1),
                      perm_p_one_sided=float((1 + (null >= obs).sum()) / (1 + NPERM)),
                      rank_biserial=round(1 - 2 * u.statistic / ((lab == 1).sum() * (lab == 0).sum()), 3)))
p2["case_control"] = tests
p2["bonferroni_alpha"] = 0.05 / len(tests)

# N2 commissioning before/after. For site s, cases within 30 km with day/year
# known: observed share after first-service year vs national (metropolitan)
# share after that year. Sum over sites, exact binomial-sum via Poisson-binomial
# normal approx + per-site detail.
yr_m = np.array([cases[i]["yr"] for i in metro])
n2 = []; O = E = V = 0.0
for j, s in enumerate(SITES):
    idx = D[:, j] <= 30
    n = int(idx.sum())
    if n == 0: continue
    p_nat = float((yr_m >= s[4]).mean()); obs_after = int((yr_m[idx] >= s[4]).sum())
    O += obs_after; E += n * p_nat; V += n * p_nat * (1 - p_nat)
    n2.append(dict(site=s[0], first_service=s[4], n_within_30km=n, obs_after=obs_after, exp_after=round(n * p_nat, 2)))
z = (O - E) / math.sqrt(V) if V > 0 else float("nan")
p2["commissioning"] = dict(per_site=n2, O=O, E=round(E, 2), ratio=round(O / E, 4), z=round(z, 3),
                           p_two_sided=float(2 * stats.norm.sf(abs(z))),
                           note="Nearly all sites predate most of the GEIPAN record; the test has power only for post-1980 sites.")
late = [x for x in n2 if x["first_service"] >= 1983]
Ol = sum(x["obs_after"] for x in late); El = sum(x["exp_after"] for x in late)
p2["commissioning"]["late_sites_O_E"] = [Ol, round(El, 2)]
# framing contamination: case text that mentions nuclear facilities
FRAME = re.compile(r"centrale|nucl[eé]aire|r[eé]acteur|\bCEA\b|\bEDF\b", re.I)
fr_idx = [i for i in metro if FRAME.search(cases[i]["Détails"] + " " + cases[i]["Identification"])]
p2["framing_mentions"] = dict(n=len(fr_idx), by_class=dict(C.Counter(cases[i]["cls"] for i in fr_idx)),
                              examples=[cases[i]["Titre du Cas"] for i in fr_idx[:12]])
R["phase2_nuclear"] = p2
print("P2", [(t["contrast"], t["r_km"], t.get("crude_OR"), t["perm_p_one_sided"]) for t in tests])
print("P2 N2", p2["commissioning"]["ratio"], p2["commissioning"]["z"])

# ================================================================ PHASE 3
# Witness portion: text before GEIPAN's analysis begins.
SPLIT = re.compile(r"(Le GEIPAN|L'enquête|L'enquete|L'analyse|Analyse|Hypoth[eè]se|Cette observation|"
                   r"L'hypoth|compatible avec|conforme|correspond|L'étude|Les enquêteurs|Conclusion)", re.I)
for c in cases:
    t = c["Détails"]; m = SPLIT.search(t)
    c["wit"] = t[:m.start()] if (m and m.start() > 40) else t
    c["wit_split"] = bool(m and m.start() > 40)
LEX = {
    "sphere/boule/globe": r"\bboules?\b|\bsph[eè]r|\bglobes?\b|\bballe\b",
    "disque/soucoupe": r"\bdisques?\b|\bsoucoupe",
    "triangle": r"triang",
    "cigare/cylindre": r"\bcigare|\bcylind|\btube\b|\btubulaire",
    "losange": r"\blosange",
    "ovale/oeuf": r"\bovale?s?\b|\bovo[iï]d|\boeuf\b|\bœuf\b|\bellips",
    "rectangle/carre": r"\brectang|\bcarr[ée]",
    "point lumineux": r"\bpoints? lumineux|\bpoints? brillants?",
    "orange": r"\borang",
    "rouge": r"\brouge",
    "vert": r"\bverte?s?\b",
    "bleu": r"\bbleu",
    "metallique": r"m[ée]tall",
    "silencieux": r"silenc|aucun bruit|sans bruit",
    "stationnaire": r"stationnaire|immobile|fixe dans le ciel",
    "formation/plusieurs": r"\bformation\b|\bplusieurs (objets|lumi[eè]res|points|boules)|en file|alignés?",
    "zigzag/manoeuvre": r"zigzag|zig-zag|virage|changement[s]? de direction|brusque",
    "atterrissage/trace": r"atterri|pos[ée] au sol|traces? (au|sur le) sol|traces? d'atterr",
    "occupant/entite": r"\boccupants?\b|\bentit[ée]s?\b|\bhumano[iï]de|\bpersonnages? (étrange|bizarre)|\bpetits? (hommes|êtres)",
    "flamme/scintillement": r"\bflamme|scintill|vacill",
    "photo/video": r"\bphoto|\bvid[ée]o|\bfilm",
}
yrs = np.array([c["yr"] for c in cases], float)
L = np.log(np.array([max(len(c["wit"]), 20) for c in cases], float))
Xb = np.column_stack([np.ones(N), (yrs - 2000) / 10, L - L.mean()])
p3 = {"witness_split_frac": round(np.mean([c["wit_split"] for c in cases]), 3), "descriptors": []}
pv = []
for name, rx in LEX.items():
    y = np.array([1.0 if re.search(rx, c["wit"], re.I) else 0.0 for c in cases])
    if y.sum() < 15: continue
    b, se = logit_fit(Xb, y)
    zz = b[1] / se[1]; p = float(2 * stats.norm.sf(abs(zz)))
    per = {}
    for lo_, hi_ in ((1937, 1979), (1980, 1999), (2000, 2009), (2010, 2026)):
        sel = (yrs >= lo_) & (yrs <= hi_); k, n = int(y[sel].sum()), int(sel.sum())
        per[f"{lo_}-{hi_}"] = [k, n, round(k / n, 3)]
    p3["descriptors"].append(dict(descriptor=name, n=int(y.sum()), OR_per_decade=round(math.exp(b[1]), 3),
                                  ci95=[round(math.exp(b[1] - 1.96 * se[1]), 3), round(math.exp(b[1] + 1.96 * se[1]), 3)],
                                  p=p, by_period=per))
    pv.append(p)
for d_, q in zip(p3["descriptors"], bh(pv)): d_["q_BH"] = float(q)
# same drift inside the unexplained (C+D) subset only: removes the shift in
# identified-stimulus mix (lanterns, ISS, satellites) as an explanation
cd = np.array([c["cls"] in "CD" for c in cases]); sub = []
for name, rx in LEX.items():
    y = np.array([1.0 if re.search(rx, c["wit"], re.I) else 0.0 for c in cases])[cd]
    if y.sum() < 15: continue
    b, se = logit_fit(Xb[cd], y)
    sub.append(dict(descriptor=name, n=int(y.sum()), OR_per_decade=round(math.exp(b[1]), 3),
                    ci95=[round(math.exp(b[1] - 1.96 * se[1]), 3), round(math.exp(b[1] + 1.96 * se[1]), 3)],
                    p=float(2 * stats.norm.sf(abs(b[1] / se[1])))))
for d_, q in zip(sub, bh([x["p"] for x in sub])): d_["q_BH"] = float(q)
p3["descriptors_CD_only"] = sub
# class mix over time (Cochran-Armitage-style trend on D share; logistic slope)
for k in ("D", "C"):
    y = np.array([1.0 if c["cls"] == k else 0.0 for c in cases])
    b, se = logit_fit(Xb[:, :2], y)
    per = {}
    for lo_, hi_ in ((1937, 1979), (1980, 1999), (2000, 2009), (2010, 2026)):
        sel = (yrs >= lo_) & (yrs <= hi_); kk, n = int(y[sel].sum()), int(sel.sum())
        per[f"{lo_}-{hi_}"] = [kk, n, round(kk / n, 4), [round(x, 4) for x in wilson(kk, n)]]
    p3[f"share_{k}"] = dict(OR_per_decade=round(math.exp(b[1]), 3),
                            ci95=[round(math.exp(b[1] - 1.96 * se[1]), 3), round(math.exp(b[1] + 1.96 * se[1]), 3)],
                            p=float(2 * stats.norm.sf(abs(b[1] / se[1]))), by_period=per)
# explanation mix by period (identified cases)
pm = {}
for lo_, hi_ in ((1937, 1979), (1980, 1999), (2000, 2009), (2010, 2026)):
    idx = [c for c in cases if lo_ <= c["yr"] <= hi_ and c["cls"] in "AB"]
    pm[f"{lo_}-{hi_}"] = dict(n=len(idx), top=C.Counter(c["Phenomenon"] for c in idx).most_common(6))
p3["explanation_mix"] = pm
# D vs AB descriptor profile (does 'unexplained' have a distinct morphology?)
prof = []
ab = np.array([c["cls"] in "AB" for c in cases]); dd_ = np.array([c["cls"] == "D" for c in cases])
for name, rx in LEX.items():
    y = np.array([bool(re.search(rx, c["wit"], re.I)) for c in cases])
    a, b_ = int((y & dd_).sum()), int((~y & dd_).sum()); c_, d__ = int((y & ab).sum()), int((~y & ab).sum())
    o = or_ci(a, b_, c_, d__)
    mh = mantel_haenszel(strata_tables([i for i in range(N) if dd_[i]], [i for i in range(N) if ab[i]], dec, lambda i: y[i]))
    prof.append(dict(descriptor=name, D=f"{a}/{a+b_}", AB=f"{c_}/{c_+d__}", OR=[round(x, 2) for x in o],
                     fisher_p=float(stats.fisher_exact([[a, b_], [c_, d__]])[1]),
                     MH_OR_decade=[round(x, 2) for x in mh[:3]], MH_p=mh[3]))
for d_, q in zip(prof, bh([x["MH_p"] for x in prof])): d_["q_BH_MH"] = float(q)
p3["D_vs_AB_profile"] = prof
R["phase3_drift"] = p3
print("P3", [(d["descriptor"], d["OR_per_decade"], round(d["q_BH"], 4)) for d in p3["descriptors"]])

import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(R, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("wrote", OUT)
