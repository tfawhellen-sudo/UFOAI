#!/usr/bin/env python3
"""Provenance graph for the 434-event retained-sample list (session 5).

Handoff section 5 item 6: trace each of the 434 events in
evidence_vault/03_RETAINED_SAMPLES/priority_434.csv to its earliest primary
source in the 860 vaulted periodical issues (APRO Bulletin 1952-, MUFON /
Skylook 1967-2008, CUFOS IUR).

DETECTION RULE: session 3's strict rule, which found 4/4 positive controls.
A place token for the event occurs within +-320 chars of BOTH the event year
and the event month name. Each corroborating issue is an edge
issue -> event, dated by the issue.

CLASSES per event
  OUT_OF_COVERAGE  event month earlier than the first issue (Jul 1952) or
                   later than the last issue in the corpus
  NO_TOKEN         no usable place token (blank location, or only generic words)
  ROOTED           earliest corroborating issue dated 0-24 months after the event
  LATE_ONLY        corroborated, but only more than 24 months after the event
  ABSENT           in coverage, token usable, no corroborating issue

BUILT-IN FALSE-POSITIVE PROBE: a "corroborating" issue dated BEFORE the event
cannot be a source for it. Pre-event hits are counted separately and estimate
how often the rule fires by coincidence.

NULL MODEL: date shuffle. Each event keeps its place token and contexts but
takes the date of a random other in-coverage event. The rule is re-applied.
200 shuffles give the ROOTED rate expected from place frequency alone. The
effect is observed ROOTED minus null ROOTED, with a bootstrap CI over events.

Usage:  OMEGA_PERIODICALS=<dir of the 860 *_djvu.txt> python3 -I omega/provenance_graph_434.py
        (untar evidence_vault/07_PERIODICALS_PRIMARY/periodicals_860_texts.tar.gz)
Writes: evidence_vault/07_PERIODICALS_PRIMARY/provenance_graph_434.json
"""
import ast
import csv
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PD = os.environ.get("OMEGA_PERIODICALS", "")
EV = os.path.join(ROOT, "evidence_vault/03_RETAINED_SAMPLES/priority_434.csv")
OUT = os.path.join(ROOT, "evidence_vault/07_PERIODICALS_PRIMARY/provenance_graph_434.json")
WIN = 320
ROOT_LAG = 24
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MON = {m.lower(): i + 1 for i, m in enumerate(MONTHS)}
MON.update({m[:3].lower(): i + 1 for i, m in enumerate(MONTHS)})

# words that are not a locus on their own
GENERIC = set("""near between north south east west northern southern eastern western
upper lower central county state province region district city town village river
lake mount mountain island islands highway route road farm ranch base air force afb
national park forest valley canyon creek beach bay coast desert usa united states
america france brazil argentina canada spain italy england britain great australia
mexico russia ussr japan chile peru venezuela germany new the and of de la le los las
del saint san santa sea ocean gulf indian pacific atlantic""".split())


def issue_date(name):
    n = name.replace("-", "_")
    m = re.search(r"(19[5-9]\d|200\d)_(\d{2})", n)
    if m and 1 <= int(m.group(2)) <= 12:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(January|February|March|April|May|June|July|August|September|"
                  r"October|November|December)[_ ]+(?:\w+[_ ]+)?(19[5-9]\d|200\d)", name)
    if m:
        return int(m.group(2)), MON[m.group(1).lower()]
    m = re.search(r"(19[5-9]\d|200\d)", n)
    if m:
        return int(m.group(1)), 6        # year only: mid-year, flagged below
    return None


COUNTRIES = set("""usa united states america france brazil argentina canada spain italy
england britain great britain uk united kingdom scotland wales ireland australia
new zealand mexico russia ussr japan chile peru venezuela germany sweden finland
norway denmark belgium netherlands holland portugal poland austria switzerland
south africa rhodesia zimbabwe india china iran iraq turkey greece romania
hungary czechoslovakia yugoslavia uruguay paraguay bolivia colombia ecuador
cuba puerto rico philippines indonesia malaysia egypt morocco algeria
madagascar reunion""".replace("\n", " ").split("  ")) if False else None
_C = ["usa", "united states", "america", "france", "brazil", "argentina", "canada",
      "spain", "italy", "england", "great britain", "britain", "uk", "united kingdom",
      "scotland", "wales", "ireland", "australia", "new zealand", "mexico", "russia",
      "ussr", "japan", "chile", "peru", "venezuela", "germany", "west germany", "sweden",
      "finland", "norway", "denmark", "belgium", "netherlands", "holland", "portugal",
      "poland", "austria", "switzerland", "south africa", "rhodesia", "india", "china",
      "iran", "iraq", "turkey", "greece", "romania", "hungary", "czechoslovakia",
      "yugoslavia", "uruguay", "paraguay", "bolivia", "colombia", "ecuador", "cuba",
      "puerto rico", "philippines", "indonesia", "malaysia", "egypt", "morocco",
      "algeria", "madagascar", "reunion", "réunion", "indian ocean"]
COUNTRY = set(_C)


def _clean(t):
    t = t.split(" / ")[-1]                # "NORTHEAST / PAARL" -> "PAARL"
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"^(near|between|outside|north of|south of|east of|west of)\s+", "",
               t.strip(), flags=re.I)
    t = t.strip(" .'\"")
    if t.lower() in COUNTRY:
        return None                       # a country is not a locus
    words = [w for w in re.findall(r"[A-Za-zÀ-ÿ'-]+", t) if w.lower() not in GENERIC]
    if not words or max(len(w) for w in words) < 4:
        return None
    return t


def tokens(row):
    """Place tokens, most specific first. Every candidate passes _clean()."""
    cands = []
    nc = (row["named_case"] or "").strip()
    if nc:
        cands.append(re.split(r"\s*[/(]", nc)[0])
    loc = (row["location"] or "").strip()
    if loc.startswith("["):
        try:
            L = ast.literal_eval(loc)
        except Exception as e:
            print("unparsed location", row["event_id"], repr(e), file=sys.stderr)
            L = []
        for el in L:                       # first element that yields a locus
            el = str(el).split(",")[0]
            if _clean(el):
                cands.append(el)
                break
    elif loc:
        parts = [p.strip() for p in loc.split(",") if p.strip()]
        for pt in parts:                   # skip a leading country, any case
            if _clean(pt):
                cands.append(pt)
                break
    good = [c for c in (_clean(x) for x in cands) if c]
    return list(dict.fromkeys(good))


def tok_rx(t):
    # tolerate hyphen/space variation (Trans-en-Provence / Trans en Provence)
    parts = [re.escape(p) for p in re.split(r"[\s\-]+", t) if p]
    return re.compile(r"\b" + r"[\s\-]+".join(parts) + r"\b", re.I)


def corroborates(ctx, y, m):
    if str(y) not in ctx:
        return False
    return bool(re.search(rf"\b({MONTHS[m-1]}|{MONTHS[m-1][:3]}\.?)\b", ctx, re.I))


def main():
    if not os.path.isdir(PD):
        sys.exit(f"set OMEGA_PERIODICALS to the periodical txt dir (got {PD!r})")
    files = sorted(f for f in os.listdir(PD) if f.endswith(".txt"))
    issues = {}
    yearonly = 0
    for f in files:
        d = issue_date(f)
        if d is None:
            print("undated issue, skipped:", f, file=sys.stderr)
            continue
        yearonly += bool(re.search(r"(19|20)\d\d_00", f.replace("-", "_")))
        issues[f] = dict(date=d, src=f.split("__")[0],
                         text=open(os.path.join(PD, f), encoding="utf-8", errors="replace").read())
    first = min(v["date"] for v in issues.values())
    last = max(v["date"] for v in issues.values())
    print(f"issues dated: {len(issues)}/{len(files)}  span {first}..{last}  (month unknown: {yearonly})")

    evs = list(csv.DictReader(open(EV, encoding="utf-8")))
    rows = []
    for r in evs:
        try:
            y, m = int(r["date"][:4]), int(r["date"][5:7])
        except ValueError:
            y = m = None
        toks = tokens(r)
        cls = None
        if not y or not m:
            cls = "NO_DATE"
        elif (y, m) < first or (y, m) > last:
            cls = "OUT_OF_COVERAGE"
        elif not toks:
            cls = "NO_TOKEN"
        ctxs = []
        if cls is None:
            rxs = [tok_rx(t) for t in toks]
            for f, iv in issues.items():
                txt = iv["text"]
                for rx in rxs:
                    for mt in rx.finditer(txt):
                        ctxs.append((f, txt[max(0, mt.start() - WIN): mt.end() + WIN]))
        rows.append(dict(event_id=r["event_id"], rank=int(r["rank"]),
                         named_case=r["named_case"], date=r["date"], y=y, m=m,
                         tokens=toks, n_catalogs=int(r["n_catalogs"] or 0),
                         provenance_depth=int(r["provenance_depth"] or 0),
                         cls=cls, ctxs=ctxs))

    YR = re.compile(r"(?<!\d)(1[89]\d\d|20\d\d)(?!\d)")
    MR = re.compile(r"\b(" + "|".join(MONTHS) + "|" + "|".join(x[:3] for x in MONTHS) + r")\b", re.I)
    for r in rows:   # precompute years/months present in each context once
        r["info"] = [(f, {int(x) for x in YR.findall(c)},
                      {MON[x.lower()[:3]] for x in MR.findall(c)}) for f, c in r["ctxs"]]

    def classify(row, y, m):
        hits = sorted({f for f, ys, ms in row["info"] if y in ys and m in ms},
                      key=lambda f: issues[f]["date"])
        post, pre = [], []
        for f in hits:
            iy, im = issues[f]["date"]
            lag = (iy - y) * 12 + (im - m)
            (pre if lag < 0 else post).append((f, lag))
        if not post:
            c = "ABSENT"
        elif post[0][1] <= ROOT_LAG:
            c = "ROOTED"
        else:
            c = "LATE_ONLY"
        return c, post, pre

    testable = [r for r in rows if r["cls"] is None]
    for r in testable:
        c, post, pre = classify(r, r["y"], r["m"])
        r["cls"], r["post"], r["pre"] = c, post, pre
    cnt = Counter(r["cls"] for r in rows)
    print("classes:", dict(cnt))

    obs_rooted = sum(r["cls"] == "ROOTED" for r in testable) / len(testable)
    pre_rate = sum(bool(r["pre"]) for r in testable) / len(testable)

    rng = random.Random(20261126)
    dates = [(r["y"], r["m"]) for r in testable]
    null = []
    for _ in range(200):
        sh = dates[:]
        rng.shuffle(sh)
        k = 0
        for r, (y, m) in zip(testable, sh):
            if (y, m) == (r["y"], r["m"]):
                # an own-date draw is not a shuffle; redraw once
                y, m = rng.choice(dates)
            k += classify(r, y, m)[0] == "ROOTED"
        null.append(k / len(testable))
    null.sort()
    null_mean = sum(null) / len(null)
    p_null = (sum(x >= obs_rooted for x in null) + 1) / (len(null) + 1)
    ind = [1.0 if r["cls"] == "ROOTED" else 0.0 for r in testable]
    bs = sorted(sum(rng.choice(ind) for _ in ind) / len(ind) - null_mean for _ in range(5000))
    eff_ci = (bs[124], bs[4874])

    # does catalogue count predict having a primary root?
    rooted = [r["n_catalogs"] for r in testable if r["cls"] == "ROOTED"]
    unrooted = [r["n_catalogs"] for r in testable if r["cls"] != "ROOTED"]
    diff = (sum(rooted) / len(rooted) - sum(unrooted) / len(unrooted)) if rooted and unrooted else None
    allc = rooted + unrooted
    perm = []
    for _ in range(10000):
        rng.shuffle(allc)
        a, b = allc[:len(rooted)], allc[len(rooted):]
        perm.append(sum(a) / len(a) - sum(b) / len(b))
    p_cat = (sum(abs(x) >= abs(diff) for x in perm) + 1) / (len(perm) + 1) if diff is not None else None

    lags = sorted(r["post"][0][1] for r in testable if r["post"])
    src_first = Counter(issues[r["post"][0][0]]["src"] for r in testable if r["cls"] == "ROOTED")

    print(f"\ntestable events: {len(testable)}")
    print(f"ROOTED (earliest corroboration <= {ROOT_LAG} months after): {obs_rooted:.3f}")
    print(f"null ROOTED (date shuffle, 200x): mean {null_mean:.3f}, 95% {null[4]:.3f}-{null[194]:.3f}; P(null >= obs) = {p_null:.4f}")
    print(f"effect over null: {obs_rooted - null_mean:+.3f}  bootstrap 95% CI {eff_ci[0]:+.3f} to {eff_ci[1]:+.3f}")
    print(f"pre-event 'corroboration' (impossible, false-positive probe): {pre_rate:.3f} of testable events")
    print(f"n_catalogs: rooted mean {sum(rooted)/max(1,len(rooted)):.2f} (n={len(rooted)}) vs "
          f"not rooted {sum(unrooted)/max(1,len(unrooted)):.2f} (n={len(unrooted)}); diff {diff:+.2f}, perm p={p_cat:.4f}")
    print(f"first-root source: {dict(src_first)}")
    if lags:
        print(f"lag to earliest corroboration, months: median {lags[len(lags)//2]}, "
              f"min {lags[0]}, max {lags[-1]}")

    edges = []
    for r in testable:
        for f, lag in r["post"]:
            edges.append(dict(src=f, dst=r["event_id"], lag_months=lag,
                              issue_date="%04d-%02d" % issues[f]["date"]))
    out_rows = []
    for r in rows:
        o = {k: r[k] for k in ("event_id", "rank", "named_case", "date", "tokens",
                               "n_catalogs", "provenance_depth", "cls")}
        if r.get("post") is not None:
            o["earliest_issue"] = r["post"][0][0] if r["post"] else None
            o["earliest_lag_months"] = r["post"][0][1] if r["post"] else None
            o["n_corroborating_issues"] = len(r["post"])
            o["pre_event_hits"] = len(r["pre"])
            o["example_context"] = next((" ".join(c.split())[:400] for f, c in r["ctxs"]
                                         if r["post"] and f == r["post"][0][0]
                                         and corroborates(c, r["y"], r["m"])), None)
        out_rows.append(o)
    json.dump(dict(
        corpus=dict(issues=len(issues), span=[first, last], month_unknown=yearonly),
        rule=dict(window_chars=WIN, root_lag_months=ROOT_LAG),
        classes=dict(cnt), testable=len(testable), rooted_rate=obs_rooted,
        null=dict(mean=null_mean, ci95=[null[4], null[194]], p=p_null),
        effect_over_null=obs_rooted - null_mean, effect_ci95=eff_ci,
        pre_event_rate=pre_rate,
        n_catalogs=dict(rooted_mean=sum(rooted) / max(1, len(rooted)),
                        unrooted_mean=sum(unrooted) / max(1, len(unrooted)),
                        diff=diff, perm_p=p_cat),
        first_root_source=dict(src_first),
        nodes=out_rows, edges=edges), open(OUT, "w"), indent=1, ensure_ascii=False)
    print("wrote", os.path.relpath(OUT, ROOT), f"({len(edges)} edges)")


if __name__ == "__main__":
    main()
