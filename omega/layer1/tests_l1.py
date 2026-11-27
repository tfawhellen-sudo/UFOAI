"""Layer 1 tests against null models (Tasks 1.1-1.5 of the Abyss Protocol, polyglot drill).

T5  Launch lock: are Soviet-territory reports date-locked to Soviet orbital launches?
    Platov & Sokolov (2000) say >90% of the state programme's anomalous phenomena were rocket
    effects plus balloons. This tests that claim on an independent, non-state catalogue
    (Chernobrov / Kosmopoisk) and on the English-language Hatch catalogue.
T1  Cross-catalogue simultaneity: do Soviet reports fall on the same days as US (NUFORC) or
    French (GEIPAN) reports more than date-shifted copies of themselves do?
T2  English-filter coverage: what share of native Russian entries reach the English catalogue
    (Hatch), and vice versa, above chance?
T3  Descriptor frameworks: shape/descriptor class shares, Russian text vs English text,
    stratified by decade.
T4  Nuclear-site proximity: ex-USSR and Chinese reports vs reactors, test sites and weapons
    cities, against a population-weighted null.

Null models are date shifts (T1, T2, T5: the whole event set is moved by k days, which keeps
its internal clustering) and population-weighted placement (T4). Positive controls are run
for T5 (GEIPAN cases officially explained as launches/re-entries; NUFORC near Vandenberg) and
T1 (Hatch Canada vs NUFORC US).
"""
import collections
import datetime as dt
import json
import math
import os
import random
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalogs as C  # noqa: E402

OUT = os.path.join(C.ROOT, "evidence_vault", "13_POLYGLOT_LAYER1")
os.makedirs(OUT, exist_ok=True)
D0 = dt.date(1900, 1, 1)


def dnum(iso):
    return (dt.date.fromisoformat(iso) - D0).days


def shift_null(event_days, hit_fn, shifts):
    """hit_fn(days)->statistic. Returns observed, null array."""
    obs = hit_fn(event_days)
    null = np.array([hit_fn(event_days + k) for k in shifts])
    return obs, null


def summarise(obs, null):
    mu = float(null.mean())
    p_hi = (1 + int((null >= obs).sum())) / (1 + len(null))
    lo, hi = np.percentile(null, [2.5, 97.5])
    return dict(obs=round(float(obs), 4), null_mean=round(mu, 4), null_2_5=round(float(lo), 4),
                null_97_5=round(float(hi), 4), ratio=round(float(obs) / mu, 3) if mu > 0 else None,
                p_upper=round(p_hi, 4), n_shifts=len(null))


SHIFTS_DAY = np.array([k for k in range(-30, 31) if abs(k) >= 2])           # keeps month-scale waves
SHIFTS_WAVE = np.array([k for k in range(-365, 366) if abs(k) >= 31])      # decorrelates waves too
SHIFTS_LAUNCH = np.array([k for k in range(-180, 181) if abs(k) >= 7])

PLUME_RU = re.compile(r"медуз|серп|полумесяц|спирал|веер|ореол|облак|туманн|купол|шлейф|расширяющ\w* (?:обол|кольц|шар)|"
                      r"газов|сияни", re.I)
PLUME_EN = re.compile(r"jellyfish|medusa|crescent|spiral|fan[- ]shaped|halo|cloud|mist|plume|glowing gas|gaseous|"
                      r"expanding (?:sphere|ring|shell)|contrail|vapou?r trail", re.I)


def launch_days(launches, groups):
    s = set()
    for x in launches:
        if x["group"] in groups:
            s.add(dnum(x["date"]))
    return s


def frac_in_window(days, lset, window=(-1, 0)):
    """share of event days d with a launch on d+w for some w in window (UTC launch dates)."""
    if len(days) == 0:
        return float("nan")
    hit = 0
    for d in days:
        if any((d + w) in lset for w in range(window[0], window[1] + 1)):
            hit += 1
    return hit / len(days)


def t5_launch_lock(ru, hatch, launches, geipan, nuforc):
    res = {}
    su_l = launch_days(launches, {"SU_PLESETSK", "SU_BAIKONUR", "SU_KAPUSTIN"})
    ples = launch_days(launches, {"SU_PLESETSK"})
    pc = C.SITE_COORD["SU_PLESETSK"]

    def ev_days(rows):
        return np.array(sorted({dnum(r["date"]) for r in rows}))

    sets = {}
    ru_su = [r for r in ru if r["region"] in ("SU", "SU?") and r["prec"] == "day" and 1957 <= r["year"] <= 2002]
    sets["RU_native_SU_all"] = ru_su
    sets["RU_native_SU_plume"] = [r for r in ru_su if PLUME_RU.search(r["text_ru"][:1500])]
    sets["RU_native_SU_noplume"] = [r for r in ru_su if not PLUME_RU.search(r["text_ru"][:1500])]
    near = [r for r in ru_su if r["lat"] is not None and C.hav_km(r["lat"], r["lon"], *pc) <= 1500]
    sets["RU_native_SU_within1500km_Plesetsk"] = near
    sets["RU_native_SU_within1500km_Plesetsk_plume"] = [r for r in near if PLUME_RU.search(r["text_ru"][:1500])]
    h_su = [x for x in hatch if x["group"] == "SU" and x["prec"] == "day" and 1957 <= x["year"] <= 2002]
    sets["Hatch_SU_all"] = h_su
    sets["Hatch_SU_plume"] = [x for x in h_su if PLUME_EN.search((x["hatch_desc"] or "") + " " + (x["text_en"] or ""))]
    sets["Hatch_SU_noplume"] = [x for x in h_su if not PLUME_EN.search((x["hatch_desc"] or "") + " " + (x["text_en"] or ""))]
    for name, rows in sets.items():
        days = ev_days(rows)
        lset = ples if "Plesetsk" in name else su_l
        lab = "Plesetsk" if "Plesetsk" in name else "SU (Plesetsk+Baikonur+Kapustin Yar)"
        out = {"n_event_days": int(len(days)), "launch_set": lab}
        for wname, win in (("W[-1,0]", (-1, 0)), ("W[0,0]", (0, 0))):
            obs, null = shift_null(days, lambda d: frac_in_window(d, lset, win), SHIFTS_LAUNCH)
            out[wname] = summarise(obs, null)
        res[name] = out
    # Positive control 1: GEIPAN cases whose official identification is a launch / re-entry
    rx_launch = re.compile(r"lancement|lanceur|fus[ée]e|soyouz|falcon|ariane|missile|tir de", re.I)
    # "rentrée atmosphérique" is also used for meteors; keep only artificial objects
    rx_reentry = re.compile(r"rentr[ée]e.{0,120}(?:satellite|d[ée]bris|[ée]tage|fus[ée]e|lanceur|cosmos|starlink|centaur|"
                            r"falcon|soyouz|ariane|rocket|spatial|module|capsule|progress)", re.I)
    g = [x for x in geipan if x["date"] and x["date"] >= "1957-10-04" and x["date"] <= "2025-06-30"]
    all_l = launch_days(launches, set(C.SITE_GROUP.values()) | {x["group"] for x in launches})
    decays = set()
    with open(os.path.join(C.RAW, "satcat", "satcat.csv")) as f:
        import csv
        for r in csv.DictReader(f):
            if r["DECAY_DATE"] and r["OBJECT_TYPE"] in ("R/B", "PAY") and r["DECAY_DATE"] >= "1957":
                try:
                    big = float(r["RCS"] or 0) >= 9.47      # median RCS of decayed rocket bodies
                except ValueError:
                    big = False
                if big:
                    try:
                        decays.add(dnum(r["DECAY_DATE"]))
                    except ValueError:
                        pass
    for nm, rows, lset in (
        ("GEIPAN_ident_launch_vs_all_launches", [x for x in g if rx_launch.search(x["ident"] + " " + x["phen"])], all_l),
        ("GEIPAN_ident_reentry_vs_decays", [x for x in g if rx_reentry.search(x["ident"] + " " + x["phen"])], decays),
        ("GEIPAN_class_D_vs_all_launches", [x for x in g if x["cls"] == "D"], all_l),
        ("GEIPAN_class_A_B_other_vs_all_launches", [x for x in g if x["cls"] in ("A", "B") and not rx_launch.search(x["ident"] + " " + x["phen"]) and not rx_reentry.search(x["ident"] + " " + x["phen"])], all_l),
    ):
        days = ev_days(rows)
        o = {"n_event_days": int(len(days))}
        for wname, win in (("W[-1,0]", (-1, 0)), ("W[0,0]", (0, 0)), ("W[-1,+1]", (-1, 1))):
            obs, null = shift_null(days, lambda d: frac_in_window(d, lset, win), SHIFTS_LAUNCH)
            o[wname] = summarise(obs, null)
        res[nm] = o
    # Known positives: launch-caused mass sightings named by Platov & Sokolov (2000)
    platov = [("1977-09-20", "Kosmos-955 (Petrozavodsk)"), ("1980-06-14", "Kosmos-1188"), ("1981-05-14", "Meteor-2 (Platov: 15 May)"),
              ("1982-08-27", "Molniya (Platov: 27/28 Aug)"), ("1984-07-03", "Kosmos-1581")]
    ru_by_day = collections.defaultdict(list)
    for r in ru:
        if r["prec"] == "day":
            ru_by_day[r["date"]].append(r)
    h_by_day = collections.defaultdict(list)
    for x in hatch:
        if x["prec"].startswith("day") and x["group"] == "SU":
            h_by_day[x["date"]].append(x)
    kp = []
    for iso, lab in platov:
        d = dt.date.fromisoformat(iso)
        win = [(d + dt.timedelta(days=k)).isoformat() for k in (-1, 0, 1)]
        kp.append(dict(date=iso, launch=lab, in_satcat=any(x["date"] == iso and x["group"] == "SU_PLESETSK" for x in launches),
                       chernobrov_entries=[(r["date"], r["place_ru"][:60]) for w in win for r in ru_by_day.get(w, [])],
                       hatch_entries=[(x["date"], x["place"]) for w in win for x in h_by_day.get(w, [])]))
    res["KNOWN_POSITIVES_Platov2000"] = kp
    # Positive control 2: NUFORC reports in CA/AZ/NV on Vandenberg launch days (count statistic)
    vb = launch_days(launches, {"US_VANDENBERG"})
    cnt = collections.Counter()
    for x in nuforc:
        loc = x.get("location") or ""
        if re.search(r",\s*(CA|AZ|NV)\b", loc) and x["date"] >= "1990-01-01":
            cnt[dnum(x["date"])] += 1
    lv = np.array(sorted(d for d in vb if d >= dnum("1990-01-01") and d <= dnum("2023-12-31")))

    def mean_cnt(days):
        return float(np.mean([cnt.get(int(d), 0) for d in days]))
    obs, null = shift_null(lv, mean_cnt, np.array([k for k in range(-60, 61) if abs(k) >= 2]))
    res["NUFORC_CA_AZ_NV_count_on_Vandenberg_launch_days_1990_2023"] = dict(n_launch_days=int(len(lv)), **summarise(obs, null))
    # Positive control 3 (known effect): NUFORC "line of lights" reports vs Starlink launches,
    # window = launch day .. +3 days, May 2019 - Dec 2021. Statistic: share of such reports in window.
    sl = sorted({dnum(x["date"]) for x in launches if x["name"].startswith("STARLINK") and "2019-05-01" <= x["date"] <= "2021-12-31"})
    sls = set(sl)
    rx_train = re.compile(r"line of (?:lights|objects)|string of|in a (?:straight )?line|single file|train|row of lights|starlink", re.I)
    tr = np.array(sorted(dnum(x["date"]) for x in nuforc if "2019-05-01" <= x["date"] <= "2021-12-31" and x["country"] == "United States" and rx_train.search(x["text"] or "")))
    other = np.array(sorted(dnum(x["date"]) for x in nuforc if "2019-05-01" <= x["date"] <= "2021-12-31" and x["country"] == "United States" and not rx_train.search(x["text"] or "")))

    def share_after(days):
        return float(np.mean([1.0 if any((int(d) - w) in sls for w in range(0, 4)) else 0.0 for d in days]))
    sh = np.array([k for k in range(-60, 61) if abs(k) >= 5])
    for nm, days in (("POSITIVE_CONTROL_NUFORC_line_of_lights_vs_Starlink_0_to_3d", tr),
                     ("NUFORC_other_reports_vs_Starlink_0_to_3d", other)):
        obs, null = shift_null(days, share_after, sh)
        res[nm] = dict(n_reports=int(len(days)), n_starlink_launches=len(sl), **summarise(obs, null))
    return res


def daily_counts(rows):
    c = collections.Counter()
    for r in rows:
        if r.get("date"):
            c[dnum(r["date"])] += 1
    return c


def t1_simultaneity(ru, hatch, nuforc, geipan):
    res = {}
    us = daily_counts([x for x in nuforc if x["country"] == "United States"])
    fr = daily_counts([x for x in geipan if x["date"]])
    ru_su = sorted({dnum(r["date"]) for r in ru if r["region"] in ("SU", "SU?") and r["prec"] == "day" and r["year"] >= 1947})
    h_su = sorted({dnum(x["date"]) for x in hatch if x["group"] == "SU" and x["prec"] == "day" and x["year"] >= 1947})
    h_ca = sorted({dnum(x["date"]) for x in hatch if x["group"] == "CA" and x["prec"] == "day" and x["year"] >= 1947})
    h_cn = sorted({dnum(x["date"]) for x in hatch if x["group"] == "CN" and x["prec"] == "day" and x["year"] >= 1947})

    def any_hit(B):
        return lambda days: float(np.mean([1.0 if B.get(int(d), 0) > 0 else 0.0 for d in days]))

    for nm, A, B in (("RU_native_SU_vs_NUFORC_US", ru_su, us), ("Hatch_SU_vs_NUFORC_US", h_su, us),
                     ("RU_native_SU_vs_GEIPAN_FR", ru_su, fr), ("Hatch_CN_vs_NUFORC_US", h_cn, us),
                     ("POSITIVE_CONTROL_Hatch_CA_vs_NUFORC_US", h_ca, us),
                     ("RU_native_SU_vs_Hatch_CN", ru_su, daily_counts([{"date": x["date"]} for x in hatch if x["group"] == "CN" and x["prec"] == "day"]))):
        A = np.array(A)
        o = {"n_A_days": int(len(A))}
        for sname, sh in (("day_level_shifts_2_30", SHIFTS_DAY), ("wave_level_shifts_31_365", SHIFTS_WAVE)):
            obs, null = shift_null(A, any_hit(B), sh)
            o[sname] = summarise(obs, null)
        res[nm] = o
    return res


def t1b_local_simultaneity(hatch, nuforc):
    """Spatially local version used as a positive control for the date-shift method:
    does an event in catalogue A have a NUFORC US report within R km on the same date?"""
    by_day = collections.defaultdict(list)
    for x in nuforc:
        if x["country"] == "United States" and x.get("lat") is not None:
            by_day[dnum(x["date"])].append((x["lat"], x["lon"]))
    res = {}
    for nm, rows, R in (("POSITIVE_CONTROL_Hatch_US_vs_NUFORC_100km", [x for x in hatch if x["group"] == "US"], 100),
                        ("POSITIVE_CONTROL_Hatch_CA_vs_NUFORC_US_300km", [x for x in hatch if x["group"] == "CA"], 300)):
        ev = [(dnum(x["date"]), x["lat"], x["lon"]) for x in rows if x["prec"] == "day" and x["lat"] is not None and x["year"] >= 1947]

        def stat(shift):
            hit = 0
            for d, la, lo in ev:
                for (a, b) in by_day.get(d + shift, []):
                    if abs(a - la) < R / 100 and C.hav_km(la, lo, a, b) <= R:
                        hit += 1
                        break
            return hit / len(ev)
        obs = stat(0)
        null = np.array([stat(int(k)) for k in SHIFTS_DAY])
        res[nm] = dict(n_events=len(ev), **summarise(obs, null))
    return res


def t2_coverage(ru, hatch):
    res = {}
    ru_su = [r for r in ru if r["region"] in ("SU", "SU?") and r["prec"] == "day" and 1947 <= r["year"] <= 2002]
    h_su = [x for x in hatch if x["group"] == "SU" and x["prec"].startswith("day") and 1947 <= x["year"] <= 2002]
    # Chernobrov's archive runs to 2002, Hatch to ~2002; compare on the common window
    hd = collections.defaultdict(list)
    for x in h_su:
        hd[dnum(x["date"])].append(x)
    rd = collections.defaultdict(list)
    for r in ru_su:
        rd[dnum(r["date"])].append(r)

    def cov(src, idx, shift, need_geo):
        hit = 0
        n = 0
        for r in src:
            d = dnum(r["date"]) + shift
            cands = idx.get(d, []) + idx.get(d - 1, []) + idx.get(d + 1, [])
            n += 1
            ok = False
            for c in cands:
                if not need_geo:
                    ok = True
                    break
                if r.get("lat") is not None and c.get("lat") is not None and C.hav_km(r["lat"], r["lon"], c["lat"], c["lon"]) <= 800:
                    ok = True
                    break
            hit += ok
        return hit / n if n else float("nan"), n

    shifts = [k for k in range(-60, 61) if abs(k) >= 7]
    for nm, src, idx in (("native_RU_found_in_Hatch", ru_su, hd), ("Hatch_SU_found_in_native_RU", h_su, rd)):
        for need_geo in (False, True):
            obs, n = cov(src, idx, 0, need_geo)
            null = np.array([cov(src, idx, k, need_geo)[0] for k in shifts])
            key = nm + ("_date±1_and_800km" if need_geo else "_date±1")
            s = summarise(obs, null)
            s["n"] = n
            s["excess_over_chance"] = round(obs - float(null.mean()), 4)
            lo, hi = C.wilson(round(obs * n), n)
            s["obs_wilson95"] = [round(lo, 4), round(hi, 4)]
            res[key] = s
    # coverage by decade (date±1 only)
    byd = {}
    for dec in (1940, 1950, 1960, 1970, 1980, 1990, 2000):
        sub = [r for r in ru_su if dec <= r["year"] < dec + 10]
        if len(sub) < 5:
            continue
        o, n = cov(sub, hd, 0, False)
        nl = np.mean([cov(sub, hd, k, False)[0] for k in shifts])
        byd[str(dec)] = dict(n=n, found=round(o, 3), chance=round(float(nl), 3))
    res["native_RU_found_in_Hatch_by_decade"] = byd
    return res


CLASSES = [
    ("sphere_ball", r"шар|сфер|круглый|кругл\w+ (?:объект|тел)|глобус", r"\bball|sphere|spher|orb\b|orbs|globe|round"),
    ("disc_saucer", r"диск|тарел|блюдц", r"disc|disk|saucer|plate|\bSCR\b"),
    ("cigar_cylinder", r"сигар|цилиндр|веретен|труб\w* (?:формы|образн)", r"cigar|cylind|tube|\bCGR\b|\bCYL"),
    ("triangle", r"треугол|трехзвезд|трёхзвезд", r"triang|delta|boomerang|chevron|\bTRI\b"),
    ("star_point", r"звезд|точк", r"\bstar|point of light|\bNLT\b"),
    ("light_fire", r"огон|огн[иея]|свечени|светящ", r"\blight|lights|glow|fire|\bBRITE|\bBRT"),
    ("cloud_plume", PLUME_RU.pattern, PLUME_EN.pattern),
    ("entity", r"гуманоид|существ|пришел|пришельц|инопланет|человечк", r"humanoid|entity|being|alien|occupant|\bOID\b|\bFIG\b"),
    ("landing_trace", r"приземл|посадк|сел[аио]? на землю|след[ыа]? на (?:земле|грунте)|опор", r"\bland|landing|trace|\bLND\b|\bTRC\b"),
    ("beam_ray", r"луч", r"\bbeam|\bray"),
    ("sound", r"звук|гул|шум|свист", r"sound|noise|hum\b|buzz|roar|\bSND\b"),
    ("radar_instrument", r"радар|локатор|РЛС|прибор", r"radar|\bRDR\b|instrument"),
]


def t3_descriptors(ru, hatch, nuforc):
    comp = [(nm, re.compile(r_ru, re.I), re.compile(r_en, re.I)) for nm, r_ru, r_en in CLASSES]

    def shares(rows, field, lang):
        n = len(rows)
        out = {}
        for nm, rr, re_ in comp:
            rx = rr if lang == "ru" else re_
            k = sum(1 for r in rows if rx.search(field(r) or ""))
            lo, hi = C.wilson(k, n)
            out[nm] = dict(k=k, n=n, share=round(k / n, 3) if n else None, ci=[round(lo, 3), round(hi, 3)])
        return out

    res = {}
    for dec in (1960, 1970, 1980, 1990):
        rsu = [r for r in ru if r["region"] in ("SU", "SU?") and dec <= r["year"] < dec + 10]
        hsu = [x for x in hatch if x["group"] == "SU" and x["year"] and dec <= x["year"] < dec + 10]
        hus = [x for x in hatch if x["group"] == "US" and x["year"] and dec <= x["year"] < dec + 10]
        nus = [x for x in nuforc if x["country"] == "United States" and dec <= int(x["date"][:4]) < dec + 10]
        res[str(dec)] = {
            "RU_native_SU (Russian text, first 1500 chars)": shares(rsu, lambda r: r["text_ru"][:1500], "ru"),
            "Hatch_SU (English summary)": shares(hsu, lambda x: (x["hatch_desc"] or "") + " " + (x["text_en"] or ""), "en"),
            "Hatch_US (English summary)": shares(hus, lambda x: (x["hatch_desc"] or "") + " " + (x["text_en"] or ""), "en"),
            "NUFORC_US (shape field + summary)": shares(nus, lambda x: (x["shape"] or "") + " " + (x["text"] or ""), "en"),
        }
    return res


def t4_nuclear(ru, hatch):
    places = C.load_places()
    reactors = C.load_reactors()
    tests = C.load_tests()
    weapons_ru = ["Саров", "Снежинск", "Озёрск", "Северск", "Железногорск", "Зеленогорск", "Новоуральск",
                  "Лесной", "Трёхгорный", "Заречный", "Курчатов", "Обнинск", "Димитровград", "Дубна"]
    idx = C.ru_index()
    weapons = []
    for nm in weapons_ru:
        key = nm.lower().replace("ё", "е")
        su = [p for p in idx.get(key, []) if p["iso2"] in C.SU_ISO2]
        if su:
            weapons.append(dict(name=nm, lat=su[0]["lat"], lon=su[0]["lon"], kind="weapons_or_nuclear_science_city"))
    su_sites = [r for r in reactors if r["iso2"] in C.SU_ISO2 and r["start"] and r["start"] <= "1991"]
    su_tests = [t for t in tests if (t["country"] or "").upper() in ("USSR", "SOVIET UNION", "RUSSIA")]
    cn_sites = [r for r in reactors if r["iso2"] == "CN"]
    cn_tests = [t for t in tests if (t["country"] or "").upper() in ("CHINA", "PRC")]

    def thin(pts, km=20):
        out = []
        for p in pts:
            if all(C.hav_km(p["lat"], p["lon"], q["lat"], q["lon"]) > km for q in out):
                out.append(p)
        return out
    site_sets = {
        "SU_reactors_pre1992": thin(su_sites), "SU_test_sites_and_PNEs": thin(su_tests),
        "SU_weapons_science_cities(NE coords)": weapons, "CN_reactors": thin(cn_sites), "CN_tests": thin(cn_tests),
    }
    site_sets["SU_all_nuclear"] = thin(site_sets["SU_reactors_pre1992"] + site_sets["SU_test_sites_and_PNEs"] + weapons)
    site_sets["CN_all_nuclear"] = thin(site_sets["CN_reactors"] + site_sets["CN_tests"])

    def min_d(lat, lon, sites):
        return min(C.hav_km(lat, lon, s["lat"], s["lon"]) for s in sites) if sites else 1e9

    rng = np.random.default_rng(20261127)

    def null_draw(pool, n, R, sites, reps=2000):
        w = np.array([max(p["pop1980"] or 0, p["pop"] or 0) for p in pool], dtype=float)
        w = w / w.sum()
        dists = np.array([min_d(p["lat"], p["lon"], sites) for p in pool])
        within = (dists <= R).astype(float)
        draws = rng.choice(len(pool), size=(reps, n), p=w)
        return within[draws].mean(axis=1)

    pool_su = [p for p in places if p["iso2"] in C.SU_ISO2]
    pool_cn = [p for p in places if p["iso2"] in ("CN",)]
    res = {"site_counts": {k: len(v) for k, v in site_sets.items()},
           "weapons_cities_found_in_NE": [w["name"] for w in weapons]}
    ru_pts = [r for r in ru if r["region"] in ("SU", "SU?") and r["lat"] is not None]
    groups = {
        "RU_native_SU_city_precision": [r for r in ru_pts if r["geo_how"].split(":")[0] in ("exact", "alias", "stem")],
        "RU_native_SU_incl_region_capitals": ru_pts,
        "Hatch_SU": [x for x in hatch if x["group"] == "SU" and x["lat"] is not None],
        "Hatch_CN": [x for x in hatch if x["group"] == "CN" and x["lat"] is not None and x["country"] == "China"],
    }
    for gname, pts in groups.items():
        sites_list = ["SU_all_nuclear", "SU_reactors_pre1992", "SU_test_sites_and_PNEs", "SU_weapons_science_cities(NE coords)"] if "SU" in gname else ["CN_all_nuclear", "CN_reactors", "CN_tests"]
        pool = pool_su if "SU" in gname else pool_cn
        gres = {"n": len(pts)}
        for sname in sites_list:
            sites = site_sets[sname]
            for R in (30, 50, 100):
                k = sum(1 for p in pts if min_d(p["lat"], p["lon"], sites) <= R)
                obs = k / len(pts)
                null = null_draw(pool, len(pts), R, sites)
                gres["%s_R%dkm" % (sname, R)] = dict(k=k, obs=round(obs, 4), null_mean=round(float(null.mean()), 4),
                                                    null_95=[round(float(np.percentile(null, 2.5)), 4), round(float(np.percentile(null, 97.5)), 4)],
                                                    ratio=round(obs / float(null.mean()), 3) if null.mean() > 0 else None,
                                                    p_upper=round((1 + int((null >= obs).sum())) / (1 + len(null)), 4),
                                                    p_lower=round((1 + int((null <= obs).sum())) / (1 + len(null)), 4))
        res[gname] = gres
    return res


def main():
    ru = C.load_ru_native()
    hatch = C.load_hatch()
    launches = C.load_launches()
    nuforc = C.load_nuforc()
    geipan = C.load_geipan()
    out = {}
    which = sys.argv[1:] or ["t5", "t1", "t2", "t3", "t4"]
    if "t5" in which:
        out["T5_launch_lock"] = t5_launch_lock(ru, hatch, launches, geipan, nuforc)
    if "t1" in which:
        out["T1_simultaneity"] = t1_simultaneity(ru, hatch, nuforc, geipan)
        out["T1_simultaneity"].update(t1b_local_simultaneity(hatch, nuforc))
    if "t2" in which:
        out["T2_coverage"] = t2_coverage(ru, hatch)
    if "t3" in which:
        out["T3_descriptors"] = t3_descriptors(ru, hatch, nuforc)
    if "t4" in which:
        out["T4_nuclear"] = t4_nuclear(ru, hatch)
    for k, v in out.items():
        json.dump(v, open(os.path.join(OUT, k + ".json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:20000])


if __name__ == "__main__":
    main()
