"""Follow-up to contact_signature.py: are the site-specific periods annual seasonality?

For every place with >= 40 report-days (1995-2023): annual resultant length R (day-of-year
phase concentration), peak day-of-year, and share of report-days in June-August.  Tests the
mundane reading that summer-peaked towns (beach resorts, high latitude) beat the national
profile's annual cycle.  Usage: python -I contact_signature_annual.py nuforc.json.gz signature.json out.json
"""
import gzip, json, sys, datetime, collections
import numpy as np
from scipy.stats import spearmanr

def main(src, sig, out):
    recs = json.load(gzip.open(src)); recs = recs[list(recs)[0]] if isinstance(recs, dict) else recs
    places = collections.defaultdict(set)
    for r in recs:
        if r.get("prec") != "day" or r.get("lat") is None or not r.get("year"): continue
        if not 1995 <= r["year"] <= 2023: continue
        try: dt = datetime.date(r["year"], r["month"], r["day"])
        except Exception: continue
        places[(round(r["lat"], 2), round(r["lon"], 2))].add(dt)
    S = json.load(open(sig))["rows"]; flagged = {(r["lat"], r["lon"]) for r in S if r["q_periodic"] < 0.05}
    rows = []
    for r in S:
        ds = places[(r["lat"], r["lon"])]
        doy = np.array([d.timetuple().tm_yday for d in ds], float)
        z = np.exp(2j * np.pi * doy / 365.25).mean()
        summer = np.mean([d.month in (6, 7, 8) for d in ds])
        jul4 = np.mean([(d.month, d.day) in ((7, 4), (7, 5)) for d in ds])
        rows.append({"place": r["place"], "lat": r["lat"], "lon": r["lon"], "n_days": r["n_days"], "R_annual": float(abs(z)),
                     "peak_doy": float((np.angle(z) % (2 * np.pi)) * 365.25 / (2 * np.pi)), "share_JJA": float(summer),
                     "share_jul4_5": float(jul4), "flag_periodic": (r["lat"], r["lon"]) in flagged})
    R = np.array([x["R_annual"] for x in rows]); lat = np.array([x["lat"] for x in rows])
    rho, p = spearmanr(lat, R)
    fl = [x for x in rows if x["flag_periodic"]]; nf = [x for x in rows if not x["flag_periodic"]]
    summ = {"spearman_lat_vs_R_annual": [float(rho), float(p)],
            "median_share_JJA_flagged": float(np.median([x["share_JJA"] for x in fl])),
            "median_share_JJA_others": float(np.median([x["share_JJA"] for x in nf])),
            "median_share_jul4_5_flagged": float(np.median([x["share_jul4_5"] for x in fl])),
            "median_share_jul4_5_others": float(np.median([x["share_jul4_5"] for x in nf]))}
    json.dump({"summary": summ, "rows": rows}, open(out, "w"), indent=1)
    print(json.dumps(summ, indent=1))
    for x in sorted(fl, key=lambda x: -x["R_annual"]):
        d = datetime.date(2001, 1, 1) + datetime.timedelta(days=int(x["peak_doy"]))
        print(x["place"].ljust(24), "R=%.3f peak %s JJA=%.2f Jul4-5=%.3f" % (x["R_annual"], d.strftime("%d %b"), x["share_JJA"], x["share_jul4_5"]))

if __name__ == "__main__":
    main(*sys.argv[1:4])
