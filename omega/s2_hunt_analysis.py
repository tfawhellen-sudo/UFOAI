#!/usr/bin/env python3
"""Score the session-7 Sentinel-2 hunt.

Scene gate: a scene counts only if its scrambled-B04 false-alarm count averages
<= 1 (glinty or rough-sea scenes make 'movers' from noise at the same rate as
real ones; see the README). Within clean scenes:
  airborne = 60-400 m/s (aircraft envelope), fast = >= 400 m/s.
Site/report test: rate per usable km^2 in the 10 km disk at the site vs the 30
random disks of the same scene. Per scene, the site's mid-rank among disks
with >= 25% of the site's usable area. Under H0 the ranks are uniform; the mean
rank is tested by simulation, one-sided (site has MORE).
"""
import json, os, sys, collections
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "evidence_vault/08_SATELLITE_ANOMALIES/s2_hunt_results.jsonl")
OUT = os.path.join(ROOT, "evidence_vault/08_SATELLITE_ANOMALIES/s2_hunt_summary.json")
rows = [json.loads(l) for l in open(IN)]
rows = [r for r in rows if "error" not in r]
# De-duplicate: Earth Search lists the same overpass up to 4 times (two processing
# baselines _0/_1, and adjacent overlapping MGRS tiles). Counting each copy
# pseudo-replicates one aircraft four times. Keep ONE scene per (point, date),
# the first in file order.
_seen, _dd = set(), []
for r in rows:
    key = (round(r["lat"], 3), round(r["lon"], 3), r["scene"].split("_")[2])
    if key in _seen:
        continue
    _seen.add(key); _dd.append(r)
rows = _dd
jobs = {j["job_id"]: j for j in json.load(open(os.path.join(ROOT, "evidence_vault/08_SATELLITE_ANOMALIES/s2_site_jobs.json")))}
S = dict(n_jobs=len(rows), skipped=sum("skip" in r for r in rows))
clean, noisy, nowater = [], [], 0
for r in rows:
    m = r.get("modes", {}).get("water")
    if not m or "fa" not in m:
        nowater += 1; continue
    (clean if np.mean(m["fa"]) <= 1 else noisy).append(r)
S.update(no_water=nowater, clean=len(clean), noisy=len(noisy))
air = sum(sum(60 <= x["v"] < 400 for x in r["modes"]["water"]["movers"]) for r in clean)
fast = [dict(job=r["job_id"], **x) for r in clean for x in r["modes"]["water"]["movers"] if x["v"] >= 400]
slow = sum(sum(x["v"] < 60 for x in r["modes"]["water"]["movers"]) for r in clean)
S.update(clean_airborne=air, clean_fast=len(fast), clean_slow=slow,
         clean_fa_total=float(sum(np.mean(r["modes"]["water"]["fa"]) for r in clean)),
         clean_usable_km2=float(sum(r["modes"]["water"]["usable"] * r["win"][2] * r["win"][3] / 1e4 for r in clean)))
S["fast_list"] = fast


def rank_test(rs, key):
    ranks, ks = [], []
    for r in rs:
        d = r["modes"]["water"]["disks"]; s = d[0]
        if s["usable_px"] < 1e6:          # < 10 km^2 of water at the site
            continue
        rate = lambda x: x[key] / x["usable_px"]
        ref = [rate(x) for x in d[1:] if x["usable_px"] >= 0.25 * s["usable_px"]]
        if len(ref) < 5:
            continue
        v = rate(s)
        ranks.append((sum(v > x for x in ref) + 0.5 * sum(v == x for x in ref) + 0.5) / (len(ref) + 1)); ks.append(len(ref) + 1)
    if not ranks:
        return dict(n=0)
    rng = np.random.default_rng(0)
    sims = np.array([np.mean([(rng.integers(0, k) + 0.5) / k for k in ks]) for _ in range(5000)])
    return dict(n=len(ranks), mean_rank=float(np.mean(ranks)), p_more=float(np.mean(sims >= np.mean(ranks))),
                site_count=int(sum(r["modes"]["water"]["disks"][0][key] for r in rs)))


groups = collections.defaultdict(list)
for r in clean:
    cat = jobs.get(r["job_id"], {}).get("category") if r["kind"] == "site" else "coincidence"
    groups[cat or r["kind"]].append(r)
groups["ALL_SITES"] = [r for r in clean if r["kind"] == "site"]
S["tests"] = {g: dict(airborne=rank_test(v, "n_air"), any=rank_test(v, "n")) for g, v in groups.items()}
S["per_site"] = {}
for r in clean:
    k = r.get("label"); d = r["modes"]["water"]["disks"][0]
    e = S["per_site"].setdefault(k, dict(scenes=0, site_air=0, site_fast=0))
    e["scenes"] += 1; e["site_air"] += d["n_air"]; e["site_fast"] += d["n_fast"]
json.dump(S, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in S.items() if k not in ("fast_list", "per_site")}, indent=1))
print("fast:", [(f["job"][:50], f["v"], f.get("chip")) for f in fast])
