"""Contact-signature indicator 1: scheduled recurrence at fixed sites (NUFORC 1995-2023).

If contact were being maintained at particular sites, reports there should recur more
REGULARLY (low local CV) or with a site-specific PERIOD that the national reporting profile
does not have.  Mundane reporting is bursty (flaps, media, launches, fireworks).

Unit   : a geocoded place (lat/lon rounded to 0.01 deg; NUFORC geocodes are town centroids).
Events : distinct report-days per place (collapses many reports of one event).
Stats  : CV2 = mean 2|I(k+1)-I(k)|/(I(k+1)+I(k)) on inter-event intervals (Holt 1996; 1 = Poisson,
         <1 regular, >1 bursty; robust to slow rate change);
         Zmax = max over P in [2, 400] days of |sum exp(2 pi i t/P)|^2 / n (Rayleigh power).
Null   : n distinct days drawn from the NATIONAL report-day profile (keeps the weekly cycle, July 4,
         seasonality and the 2010s boom).  Stage 1: 200 draws per place; places with p <= 0.01
         get 4,000 more.  Benjamini-Hochberg across places.
Usage  : python -I contact_signature.py nuforc_unified.json.gz out.json
"""
import gzip, json, sys, datetime, collections
import numpy as np

MIN_DAYS = 40
PER = np.geomspace(2, 400, 300)
rng = np.random.default_rng(20261126)

def cv2(days):
    I = np.diff(np.sort(days)).astype(float)
    return float(np.mean(2 * np.abs(I[1:] - I[:-1]) / (I[1:] + I[:-1])))

def zmax(days):
    ph = np.exp(2j * np.pi * np.asarray(days, float)[:, None] / PER[None, :])
    z = np.abs(ph.sum(0)) ** 2 / len(days)
    k = int(np.argmax(z)); return float(z[k]), float(PER[k])

def null_stats(n, w, draws):
    c, z = np.empty(draws), np.empty(draws)
    for b in range(draws):
        d = rng.choice(len(w), size=n, replace=False, p=w)
        c[b] = cv2(d); z[b] = zmax(d)[0]
    return c, z

def bh(p):
    p = np.asarray(p); m = len(p); o = np.argsort(p)
    q = p[o] * m / (np.arange(m) + 1); q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(m); out[o] = np.minimum(q, 1); return out

def main(src, out):
    recs = json.load(gzip.open(src))
    recs = recs[list(recs)[0]] if isinstance(recs, dict) else recs
    d0 = datetime.date(1995, 1, 1).toordinal(); d1 = datetime.date(2023, 12, 31).toordinal()
    places = collections.defaultdict(set); names = {}
    for r in recs:
        if r.get("prec") != "day" or r.get("lat") is None or not r.get("year"): continue
        try: o = datetime.date(r["year"], r["month"], r["day"]).toordinal()
        except Exception: continue
        if not d0 <= o <= d1: continue
        key = (round(r["lat"], 2), round(r["lon"], 2))
        places[key].add(o - d0); names.setdefault(key, r.get("location", ""))
    nat = np.zeros(d1 - d0 + 1)
    for s in places.values():
        for o in s: nat[o] += 1
    w = nat / nat.sum()
    big = {k: np.array(sorted(v)) for k, v in places.items() if len(v) >= MIN_DAYS}
    print("places", len(places), "with >=%d report-days" % MIN_DAYS, len(big))
    rows = []
    for k, days in big.items():
        c_obs = cv2(days); z_obs, p_at = zmax(days)
        cn, zn = null_stats(len(days), w, 200)
        p_reg = (1 + np.sum(cn <= c_obs)) / (1 + len(cn)); p_per = (1 + np.sum(zn >= z_obs)) / (1 + len(zn))
        if min(p_reg, p_per) <= 0.01:
            cn2, zn2 = null_stats(len(days), w, 4000)
            cn, zn = np.concatenate([cn, cn2]), np.concatenate([zn, zn2])
            p_reg = (1 + np.sum(cn <= c_obs)) / (1 + len(cn)); p_per = (1 + np.sum(zn >= z_obs)) / (1 + len(zn))
        rows.append({"place": names[k], "lat": k[0], "lon": k[1], "n_days": int(len(days)),
                     "cv2": round(c_obs, 3), "cv2_null_median": round(float(np.median(cn)), 3),
                     "zmax": round(z_obs, 2), "zmax_null_median": round(float(np.median(zn)), 2),
                     "best_period_days": round(p_at, 1), "p_regular": float(p_reg), "p_periodic": float(p_per),
                     "n_null": int(len(cn))})
    qr = bh([r["p_regular"] for r in rows]); qp = bh([r["p_periodic"] for r in rows])
    for r, a, b in zip(rows, qr, qp): r["q_regular"] = float(a); r["q_periodic"] = float(b)
    allcv = np.array([r["cv2"] for r in rows])
    summ = {"places_tested": len(rows), "min_report_days": MIN_DAYS,
            "cv2_median": float(np.median(allcv)), "frac_cv2_below_1": float(np.mean(allcv < 1)),
            "frac_cv2_below_null_median": float(np.mean([r["cv2"] < r["cv2_null_median"] for r in rows])),
            "n_q_regular_lt_0.05": int(np.sum(qr < 0.05)), "n_q_periodic_lt_0.05": int(np.sum(qp < 0.05))}
    rows.sort(key=lambda r: min(r["p_regular"], r["p_periodic"]))
    json.dump({"summary": summ, "rows": rows}, open(out, "w"), indent=1)
    print(json.dumps(summ, indent=1))
    for r in rows[:15]:
        print(r["place"][:28].ljust(28), r["n_days"], "cv2", r["cv2"], "(null", r["cv2_null_median"], ") pR", round(r["p_regular"], 4),
              "qR", round(r["q_regular"], 3), "| Z", r["zmax"], "(null", r["zmax_null_median"], ") P", r["best_period_days"],
              "pP", round(r["p_periodic"], 4), "qP", round(r["q_periodic"], 3))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
