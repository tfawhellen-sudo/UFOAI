"""Canada NRC/DND/RCMP UFO files (LAC RG 77 via archive.org item CanadaUFO):
Venus null model and weekday test on distinct sighting-days, 1967-1978.

Input: the 29 'Canada - FOIA Part NN' OCR texts (archive.org /stream/ djvu.txt),
concatenated to one file. Path is argv[1]. Output JSON to argv[2].

Unit of analysis: a distinct calendar date that appears in the OCR in the
military/RCMP short form 'D MON YY' (e.g. '24 NOV 79'). One report repeats its
date many times, so counting distinct dates de-duplicates repeats. A date can be
a report or message date rather than the sighting date; these usually differ by
0-3 days, which does not matter at monthly resolution.
"""
import sys, re, json, datetime as dt, math
import numpy as np, ephem
import statsmodels.api as sm

src, out = sys.argv[1], sys.argv[2]
T = open(src, encoding='utf-8', errors='replace').read()
MON = dict(JAN=1, FEB=2, MAR=3, APR=4, MAY=5, JUN=6, JUL=7, AUG=8, SEP=9, OCT=10, NOV=11, DEC=12)
pat = re.compile(r'\b([0-3]?[0-9]) ?(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]* ?(?:19)?([6-7][0-9])\b')
dates = set()
raw = 0
for m in pat.finditer(T):
    raw += 1
    d, mo, y = int(m.group(1)), MON[m.group(2)], 1900 + int(m.group(3))
    if not (1967 <= y <= 1978):
        continue
    try:
        dates.add(dt.date(y, mo, d))
    except ValueError:
        pass
dates = sorted(dates)

# ---- monthly series
months = [(y, m) for y in range(1967, 1979) for m in range(1, 13)]
cnt = {k: 0 for k in months}
for d in dates:
    cnt[(d.year, d.month)] += 1

# Venus altitude 1 h after sunset at Ottawa, 15th of each month
obs = ephem.Observer(); obs.lat, obs.lon = '45.42', '-75.70'; obs.elevation = 70
def venus_alt(y, m):
    obs.date = ephem.Date(dt.datetime(y, m, 15, 12))
    ss = obs.next_setting(ephem.Sun())
    obs.date = ephem.Date(ss + ephem.hour)
    v = ephem.Venus(obs)
    return max(0.0, math.degrees(v.alt)), float(v.mag)
V = np.array([venus_alt(y, m)[0] for y, m in months])

def venus_alt_morning(y, m):
    obs.date = ephem.Date(dt.datetime(y, m, 15, 0))
    sr = obs.next_rising(ephem.Sun())
    obs.date = ephem.Date(sr - ephem.hour)
    return max(0.0, math.degrees(ephem.Venus(obs).alt))
VM = np.array([venus_alt_morning(y, m) for y, m in months])  # placebo: pre-dawn Venus, few observers
Y = np.array([cnt[k] for k in months], float)

def design(v):
    yr = np.array([y for y, m in months]); mo = np.array([m for y, m in months])
    cols = [v / 10.0]
    cols += [(yr == y).astype(float) for y in range(1968, 1979)]
    cols += [(mo == k).astype(float) for k in range(2, 13)]
    X = np.column_stack(cols)
    return sm.add_constant(X)

def fit(v):
    X = design(v)
    m0 = sm.GLM(Y, X, family=sm.families.Poisson()).fit()
    # NB2 with alpha from Pearson dispersion of Poisson fit (method of moments)
    mu = m0.mu
    alpha = max(1e-6, (((Y - mu) ** 2 - mu) / mu ** 2).mean())
    m = sm.GLM(Y, X, family=sm.families.NegativeBinomial(alpha=alpha)).fit()
    return m, alpha

m, alpha = fit(V)
beta, se = m.params[1], m.bse[1]
rr = math.exp(beta); lo, hi = math.exp(beta - 1.96 * se), math.exp(beta + 1.96 * se)

# permutation null: circular shifts of the Venus series (keeps its autocorrelation)
rng = np.random.default_rng(20261126)
shifts = [s for s in range(len(V)) if 6 <= s <= len(V) - 6]
null = []
for s in shifts:
    mm, _ = fit(np.roll(V, s))
    null.append(mm.params[1])
null = np.array(null)
p_perm = float((np.abs(null) >= abs(beta)).mean())

mp, _ = fit(VM)
placebo = dict(rr_per_10deg=math.exp(mp.params[1]), ci95=[math.exp(mp.params[1]-1.96*mp.bse[1]), math.exp(mp.params[1]+1.96*mp.bse[1])], p_wald=float(mp.pvalues[1]))

# power: smallest RR per 10 deg detectable ~80% given se
mde = math.exp(2.8 * se)

# ---- weekday test on distinct dates
wd = np.bincount([d.weekday() for d in dates], minlength=7)
# expected: number of calendar days of each weekday in 1967-1978 is ~equal
from scipy.stats import chisquare
chi = chisquare(wd)
weekend_share = (wd[5] + wd[6]) / wd.sum()
# Wilson CI
n = wd.sum(); k = wd[5] + wd[6]; z = 1.96
c = (k + z * z / 2) / (n + z * z); h = z * math.sqrt(k * (n - k) / n + z * z / 4) / (n + z * z)

res = dict(
    raw_date_mentions_all_years=raw, distinct_dates_1967_1978=len(dates),
    per_year={y: int(sum(cnt[(y, m)] for m in range(1, 13))) for y in range(1967, 1979)},
    venus=dict(model='NB2 GLM, year FE + calendar-month FE, predictor = Venus altitude 1h after sunset at Ottawa on the 15th, per 10 deg',
               alpha=alpha, rr_per_10deg=rr, ci95=[lo, hi], p_wald=float(m.pvalues[1]),
               p_perm_circular_shift=p_perm, n_shifts=len(null), mde_rr_80pct=mde,
               placebo_morning_venus=placebo),
    weekday=dict(counts_mon_to_sun=wd.tolist(), chi2=float(chi.statistic), p=float(chi.pvalue),
                 weekend_share=float(weekend_share), weekend_ci95=[c - h, c + h], null_weekend_share=2 / 7),
    venus_alt_by_month=[round(x, 1) for x in V], counts_by_month=Y.astype(int).tolist(),
)
json.dump(res, open(out, 'w'), indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k not in ('venus_alt_by_month', 'counts_by_month')}, indent=1, default=float))
