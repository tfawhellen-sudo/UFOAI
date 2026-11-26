"""Power analysis for the preregistered 434-event assay protocol.

Project Omega, 2026-11-26. Companion to omega/reports/assay_protocol_434.md.
Deterministic (seeded). numpy only. Runs in about a minute.

Four designs, one per protocol arm:
  A1  documentary claim drift (McNemar, paired earliest-root vs latest catalogue)
  A2  blinded lab assay with decoys (one-sided Fisher exact on flag rates)
  A3  site revisit, exposed vs same-day sham centre (sign-flip over sites,
      site effects drawn with between-site heterogeneity)
  A4  dendro superposed-epoch (event-year ring index, site vs control trees)

Alpha per primary hypothesis is 0.01 (Holm over five primaries, family 0.05).
"""
import json
import math
import sys

import numpy as np

RNG = np.random.default_rng(434)
ALPHA = 0.01
NSIM = 2000


def binom_pmf(k, n, p):
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)


def mcnemar_exact_p(b, c):
    """One-sided exact McNemar: P(X >= b | b+c, 0.5), b = claim added later."""
    n = b + c
    if n == 0:
        return 1.0
    return sum(binom_pmf(k, n, 0.5) for k in range(b, n + 1))


def a1_power(n_pairs, p_add, p_drop):
    """Probability the drift test rejects when later sources add the anomaly
    claim at rate p_add and drop it at rate p_drop."""
    hits = 0
    for _ in range(NSIM):
        u = RNG.random(n_pairs)
        b = int((u < p_add).sum())
        c = int(((u >= p_add) & (u < p_add + p_drop)).sum())
        hits += mcnemar_exact_p(b, c) < ALPHA
    return hits / NSIM


def fisher_one_sided_p(a, n1, c, n0):
    """P(real flags >= a) under the hypergeometric with fixed margins."""
    k = a + c
    N = n1 + n0
    tot = math.comb(N, k)
    return sum(math.comb(n1, x) * math.comb(n0, k - x) for x in range(a, min(n1, k) + 1)) / tot


def a2_power(n_real, decoy_ratio, p_false, p_true):
    n0 = n_real * decoy_ratio
    hits = 0
    for _ in range(NSIM):
        a = RNG.binomial(n_real, p_true)
        c = RNG.binomial(n0, p_false)
        hits += fisher_one_sided_p(a, n_real, c, n0) < ALPHA
    return hits / NSIM


def signflip_p(x, nperm=4000):
    n = len(x)
    obs = x.mean()
    if n <= 12:
        signs = np.array([[1 if (i >> j) & 1 else -1 for j in range(n)] for i in range(2**n)])
    else:
        signs = RNG.choice([-1, 1], size=(nperm, n))
    null = (signs * x).mean(axis=1)
    return (np.sum(null >= obs) + 1) / (len(null) + 1)


def a3_power(n_sites, d, tau, m_cores=5, nsim=600):
    """d = mean standardized exposed-minus-sham effect; tau = between-site SD of
    the true effect (same units). Within-site core SD = 1, m cores per arm."""
    hits = 0
    for _ in range(nsim):
        theta = RNG.normal(d, tau, n_sites)
        se = math.sqrt(2 / m_cores)
        site_diff = theta + RNG.normal(0, se, n_sites)
        hits += signflip_p(site_diff) < ALPHA
    return hits / nsim


def a4_power(n_sites, d_ring, trees_per_arm=10, nsim=600):
    """Event-year ring-width index; site trees vs control trees at each site.
    Ring index residual SD = 1 per tree after detrending."""
    hits = 0
    for _ in range(nsim):
        se = math.sqrt(2 / trees_per_arm)
        site_diff = RNG.normal(d_ring, se, n_sites) + RNG.normal(0, 0.3, n_sites)
        hits += signflip_p(-site_diff) < ALPHA  # suppression predicted
    return hits / nsim


def tost_halfwidth(n_sites, tau, m_cores=5):
    """Approximate 90% CI half-width on the mean effect: the equivalence bound
    a null result can certify."""
    sd = math.sqrt(tau**2 + 2 / m_cores)
    return 1.645 * sd / math.sqrt(n_sites)


def main():
    out = {"alpha_per_primary": ALPHA, "nsim": NSIM}

    out["A1_claim_drift"] = {
        f"n={n}": {f"add{pa}_drop{pd}": a1_power(n, pa, pd) for pa, pd in [(0.15, 0.03), (0.25, 0.05), (0.35, 0.05)]}
        for n in (20, 43, 80)
    }
    out["A2_blind_decoy"] = {
        f"n_real={n}": {f"p_true={pt}": a2_power(n, 2, 0.10, pt) for pt in (0.3, 0.5, 0.7, 0.9)}
        for n in (3, 5, 10, 20, 40)
    }
    out["A3_site_revisit"] = {
        f"tau={tau}": {
            f"n_sites={n}": {f"d={d}": a3_power(n, d, tau) for d in (0.5, 0.8, 1.2)} for n in (6, 10, 15, 25, 40)
        }
        for tau in (0.3, 0.8)
    }
    out["A3_equivalence_halfwidth"] = {
        f"tau={tau}": {f"n_sites={n}": round(tost_halfwidth(n, tau), 3) for n in (6, 10, 15, 25, 40)} for tau in (0.3, 0.8)
    }
    out["A4_dendro"] = {
        f"n_sites={n}": {f"d={d}": a4_power(n, -d) for d in (0.3, 0.5, 0.8)} for n in (5, 10, 20)
    }
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
