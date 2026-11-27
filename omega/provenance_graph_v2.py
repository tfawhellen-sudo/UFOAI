#!/usr/bin/env python3
"""Provenance graph v2: expanded periodical corpus + higher-recall date rule.

Session 7. Re-runs the session-5 provenance graph for the 434-event list
(omega/provenance_graph_434.py) with two changes, each measured separately so
neither can hide behind the other:

CORPUS
  A  = the 860 vaulted issues (MUFON/Skylook, APRO Bulletin, IUR)
  A+B = A plus the session-7 expansion fetched by
        omega/periodicals_expand_fetch.py: Flying Saucer Review (246 issues,
        1955-) and the Archives for the Unexplained `ufonewsletters`
        collection on archive.org (UFO Newsclipping Service = newspaper
        clippings 1969-, LDLN, BUFORA, Australian UFO Bulletin, Stendek ...)

RULE
  strict  = session-5 rule: place token within +-320 chars of the event year
            AND the English month name / 3-letter abbreviation.
  recall  = strict, OR the month in French / Spanish / German / Italian /
            Portuguese, OR a numeric date d/m/yy, m/d/yy, d.m.yyyy, yyyy-mm-dd
            that matches the event's full date (year, month AND day, either
            field order). The day is required because 1.5.77 is ambiguous
            between 1 May and 5 Jan: a month-only numeric match fired by
            coincidence in the trial run (Bridlington, BUFORA Journal 1977).

Every (corpus, rule) cell gets its own 200x date-shuffle null, bootstrap CI and
pre-event false-positive probe. Issues dated to the year only are placed at
mid-year and counted; ROOTED edges that rest on a year-only issue are flagged.

Usage:
  OMEGA_PERIODICALS=<860 txt dir> OMEGA_EXPANSION=<fetch OUTDIR> \
      python3 -I omega/provenance_graph_v2.py
Writes evidence_vault/07_PERIODICALS_PRIMARY/provenance_graph_v2.json
"""
import csv
import importlib.util
import json
import multiprocessing
import os
import random
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "pg1", os.path.join(ROOT, "omega/provenance_graph_434.py"))
pg1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pg1)

PD = os.environ.get("OMEGA_PERIODICALS", "")
XD = os.environ.get("OMEGA_EXPANSION", "")
EV = pg1.EV
OUT = os.environ.get("OMEGA_OUT") or os.path.join(ROOT, "evidence_vault/07_PERIODICALS_PRIMARY/provenance_graph_v2.json")
WIN, ROOT_LAG, NSHUF = pg1.WIN, pg1.ROOT_LAG, int(os.environ.get("OMEGA_NSHUF", "200"))
MONTHS = pg1.MONTHS

# month names, index 1..12, non-English forms (accents optional)
ML = {
    "fr": "janvier fevrier mars avril mai juin juillet aout septembre octobre novembre decembre",
    "es": "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre",
    "de": "januar februar marz april mai juni juli august september oktober november dezember",
    "it": "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre",
    "pt": "janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro",
}
FOLD = str.maketrans("éèêëàâäîïôöûüùçñ", "eeeeaaaiioouuucn")
EN = {m.lower(): i + 1 for i, m in enumerate(MONTHS)}
EN.update({m[:3].lower(): i + 1 for i, m in enumerate(MONTHS)})
XL = {}
for lang, s in ML.items():
    for i, w in enumerate(s.split()):
        XL.setdefault(w, set()).add(i + 1)
EN_RX = re.compile(r"\b(" + "|".join(sorted(EN, key=len, reverse=True)) + r")\b", re.I)
XL_RX = re.compile(r"\b(" + "|".join(sorted(XL, key=len, reverse=True)) + r")\b")
YR_RX = re.compile(r"(?<!\d)(1[89]\d\d|20\d\d)(?!\d)")
NUM_RX = re.compile(r"(?<![\d/.\-])(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4}|\d{2})(?![\d/])")
ISO_RX = re.compile(r"(?<!\d)(19[4-9]\d|200\d)-(\d{2})-(\d{2})(?!\d)")
NAMEDATE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|"
    r"December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?"
    r"(?:\s*[-/&]\s*\w+\.?)?,?\s+(19[4-9]\d|200\d)", re.I)


def ctx_info(c):
    """years, English months, all-language months, and full numeric dates in a context."""
    ys = {int(x) for x in YR_RX.findall(c)}
    ms = {EN[x.lower()] for x in EN_RX.findall(c)}
    ymd = set()                          # (year, month, day) from numeric dates, both orders
    for a, b, yy in NUM_RX.findall(c):
        a, b = int(a), int(b)
        y = int(yy) + (1900 if len(yy) == 2 else 0)
        if len(yy) == 2 and y < 1940:
            y += 100
        for mm, dd in ((a, b), (b, a)):
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                ymd.add((y, mm, dd))
    for y, mm, dd in ISO_RX.findall(c):
        ymd.add((int(y), int(mm), int(dd)))
    xm = set()
    for w in XL_RX.findall(c.lower().translate(FOLD)):
        xm |= XL[w]
    return ys, ms, ms | xm, ymd


def pairs(info, rule):
    """(year, month) pairs a context supports by month NAME under a rule."""
    ys, ms, xms, _ = info
    if rule == "recall":
        return {(y, m) for y in ys for m in xms}
    return {(y, m) for y in ys for m in ms}


def index_event(e):
    """e['ym'][rule][(y, m)] = {issue key: offset of first supporting hit} (month names);
    e['ymd'][(y, m, d)] = {issue key: offset} (numeric dates, recall rule only).
    A numeric date must match the event's DAY as well: 1.5.77 is ambiguous between
    1 May and 5 Jan, so a month-only numeric match would fire by coincidence."""
    e["ym"] = {}
    for rule in ("strict", "recall"):
        d = {}
        for k, off, info in e["info"]:
            for ym in pairs(info, rule):
                d.setdefault(ym, {}).setdefault(k, off)
        e["ym"][rule] = d
    e["ymd"] = {}
    for k, off, info in e["info"]:
        for t in info[3]:
            e["ymd"].setdefault(t, {}).setdefault(k, off)


def supporting(e, rule, y, m, d):
    """issue key -> offset of the first hit that supports date (y, m[, d]) under rule."""
    out = dict(e["ym"][rule].get((y, m), {}))
    if rule == "recall" and d:
        for k, off in e["ymd"].get((y, m, d), {}).items():
            out.setdefault(k, off)
    return out


_ISSUES = {}


def scan_event(arg):
    eid, toks = arg
    e = {"info": []}
    rxs = [pg1.tok_rx(t) for t in toks]
    for k, iv in _ISSUES.items():
        txt = iv["text"]
        for rx in rxs:
            for mt in rx.finditer(txt):
                c = txt[max(0, mt.start() - WIN): mt.end() + WIN]
                e["info"].append((k, mt.start(), ctx_info(c)))
    index_event(e)
    return eid, (e["ym"], e["ymd"])


# ---------------------------------------------------------------- dating
def date_from_text(t):
    m = NAMEDATE.search(t[:4000])
    if m:
        return int(m.group(2)), EN[m.group(1).lower()[:3]], True
    return None


# ---- Flying Saucer Review: one archive.org item, 246 files numbered in
# publication order, no dates in the file names. Cover OCR is noisy (85.FSR's
# cover reads "1953" for Vol.15 No.1 = Jan 1969), so a cover date is accepted
# only when it agrees within a year with the date implied by the volume number.
# Volume -> first year, read off the covers in this collection.
FSR_VOL_YEAR = {21: 1975, 22: 1976, 23: 1977, 24: 1978, 25: 1979, 26: 1980,
                27: 1981, 28: 1983, 29: 1984, 30: 1984, 31: 1985, 32: 1986}
FSR_VOL = re.compile(r"\bVol(?:ume|\.)?\s*([0-9lIOi]{1,2})\s*(?:[,.]?\s*(?:No|Number|Nos?)\.?\s*|/)"
                     r"([0-9lIOi]{1,2})\b", re.I)
SEASON = re.compile(r"\b(Spring|Summer|Autumn|Winter|March Quarter|June Quarter|"
                    r"September Quarter|December Quarter)\W{0,3}(19[5-9]\d|200\d)", re.I)
SEASON_M = {"spring": 4, "summer": 7, "autumn": 10, "winter": 1, "march quarter": 3,
            "june quarter": 6, "september quarter": 9, "december quarter": 12}
FSR_DATES = {}


def _ocr_int(x):
    x = x.replace("l", "1").replace("I", "1").replace("i", "1").replace("O", "0")
    return int(x) if x.isdigit() else None


def fsr_vol_year(v):
    if v is None or not 1 <= v <= 60:
        return None
    if v <= 20:
        return 1954 + v
    return FSR_VOL_YEAR.get(v, 1955 + v)


def build_fsr_dates(recs, xd):
    """file -> (year, month, month_known). Cover date if it agrees with the
    volume; else volume year (month unknown); else interpolate from neighbours."""
    rows = []
    for r in recs:
        n = int(re.search(r"^(\d+)\.FSR", r["file"]).group(1))
        t = open(os.path.join(xd, "txt", r["path"]), encoding="utf-8", errors="replace").read()[:5000]
        v = FSR_VOL.search(t)
        vy = fsr_vol_year(_ocr_int(v.group(1))) if v else None
        covers = [(int(y), EN[mo.lower()[:3]]) for mo, y in NAMEDATE.findall(t)]
        covers += [(int(y), SEASON_M[se.lower()]) for se, y in SEASON.findall(t)]
        d = None
        for y, m in covers:
            if vy is None or abs(y - vy) <= 1:
                d = (y, m, vy is not None)   # a cover date with no volume is weak
                break
        if d is None and vy:
            d = (vy, 6, False)
        rows.append([n, r["file"], d])
    rows.sort()
    for i, (n, f, d) in enumerate(rows):
        if d is None:                         # neighbours in publication order
            prev = next((x[2] for x in reversed(rows[:i]) if x[2]), None)
            nxt = next((x[2] for x in rows[i + 1:] if x[2]), None)
            if prev and nxt and abs(nxt[0] - prev[0]) <= 1:
                d = (prev[0], 6, False)
        if d:
            FSR_DATES[f] = d


# ---- LDLN (Lumieres dans la Nuit, 1958-): ids carry only the issue number.
# Covers print "<n> - <mois> <annee>". Accept a cover date only if it agrees
# within a year with the rolling median of its neighbours' cover years.
FR_MONTH = re.compile(r"\b(janvier|f.vrier|mars|avril|mai|juin|juillet|ao.t|septembre|octobre|"
                      r"novembre|d.cembre)\W{0,3}(19[5-9]\d|20[01]\d)\b")
FR_M = {"jan": 1, "f": 2, "mar": 3, "avr": 4, "mai": 5, "juin": 6, "juil": 7, "ao": 8,
        "sep": 9, "oct": 10, "nov": 11, "d": 12}
LDLN_DATES = {}


def _fr_month(w):
    for k in sorted(FR_M, key=len, reverse=True):
        if w.startswith(k):
            return FR_M[k]
    return None


def build_ldln_dates(recs, xd):
    rows = []
    for r in recs:
        m = re.search(r"LDLN_No_(\d+)", r["id"])
        if not m:
            continue
        t = open(os.path.join(xd, "txt", r["path"]), encoding="utf-8", errors="replace").read()[:4000]
        cands = [(int(y), _fr_month(mo)) for mo, y in FR_MONTH.findall(t.lower())]
        rows.append([int(m.group(1)), r["path"], cands])
    rows.sort()
    firsts = [c[0][0] if c else None for _, _, c in rows]
    for i, (n, path, cands) in enumerate(rows):
        nb = sorted(y for y in firsts[max(0, i - 8): i + 9] if y)
        if not nb:
            continue
        exp_y = nb[len(nb) // 2]
        d = next(((y, mo, True) for y, mo in cands if abs(y - exp_y) <= 1), None)
        LDLN_DATES[path] = d or (exp_y, 6, False)


def expansion_date(rec, text):
    s = " ".join(filter(None, [rec.get("id"), rec.get("title")])).replace("-", "_")
    m = re.search(r"(?<!\d)(19[4-9]\d|200\d)(0[1-9]|1[0-2])\d{2}(?!\d)", s)  # AFU_19520715_
    if m:
        return int(m.group(1)), int(m.group(2)), True
    m = re.search(r"(?<!\d)(19[4-9]\d|200\d)[_ ](0[1-9]|1[0-2])(?!\d)", s)
    if m:
        return int(m.group(1)), int(m.group(2)), True
    m = re.search(r"(?<!\d)(19[4-9]\d|200\d)[_ ]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", s, re.I)
    if m:
        return int(m.group(1)), EN[m.group(2).lower()], True
    if rec.get("series") == "FSR":
        return FSR_DATES.get(rec.get("file"))
    if rec.get("path") in LDLN_DATES:
        return LDLN_DATES[rec["path"]]
    m = re.search(r"(?<!\d)(19[4-9]\d|200\d)(?!\d)", s) or \
        re.search(r"^(19[4-9]\d|200\d)", rec.get("date") or "")
    if m:
        return int(m.group(1)), 6, False
    return None


def load():
    issues = {}
    for f in sorted(os.listdir(PD)):
        if not f.endswith(".txt"):
            continue
        d = pg1.issue_date(f)
        if d is None:
            continue
        ym = not bool(re.search(r"(19|20)\d\d_00", f.replace("-", "_"))) and \
            bool(re.search(r"(19[5-9]\d|200\d)_(0[1-9]|1[0-2])|January|February|March|April|"
                           r"May|June|July|August|September|October|November|December", f))
        issues["A/" + f] = dict(date=d, month_known=ym, corpus="A", src=f.split("__")[0],
                                text=open(os.path.join(PD, f), encoding="utf-8", errors="replace").read())
    nA = len(issues)
    skipped = Counter()
    if XD:
        man, seen = [], set()
        for mf in ("manifest.jsonl", "manifest_ldln.jsonl"):
            if os.path.exists(os.path.join(XD, mf)):
                for line in open(os.path.join(XD, mf)):
                    r = json.loads(line)
                    if r.get("path") and r["path"] in seen:
                        continue
                    seen.add(r.get("path"))
                    man.append(r)
        build_fsr_dates([r for r in man if r.get("series") == "FSR" and r.get("path")], XD)
        build_ldln_dates([r for r in man if r["id"].startswith("LDLN_No_") and r.get("path")], XD)
        for r in man:
            if not r.get("path"):
                skipped["no_text"] += 1
                continue
            if re.search(r"APRO_Bulletin|Skylook|MUFON_UFO_Journal|International_UFO_Reporter",
                         r["path"]):
                skipped["duplicate_of_A"] += 1   # same runs as corpus A
                continue
            t = open(os.path.join(XD, "txt", r["path"]), encoding="utf-8", errors="replace").read()
            d = expansion_date(r, t)
            if d is None:
                skipped["undated"] += 1
                continue
            y, m, known = d
            if not (1947 <= y <= 2010):
                skipped["outside_1947_2010"] += 1
                continue
            issues["B/" + r["path"]] = dict(date=(y, m), month_known=known, corpus="B",
                                            src=r["series"], text=t, ia_id=r["id"],
                                            ia_file=r.get("file") or f'{r["id"]}_djvu.txt')
    return issues, nA, skipped


# ---------------------------------------------------------------- graph
def run(issues, events, keys, rule, rng):
    sub = {k: issues[k] for k in keys}
    first = min(v["date"] for v in sub.values())
    last = max(v["date"] for v in sub.values())
    testable = []
    for e in events:
        if e["base_cls"] is not None:
            continue
        if (e["y"], e["m"]) < first or (e["y"], e["m"]) > last:
            continue
        testable.append(e)

    def classify(e, y, m, d):
        post, pre = [], []
        for k, off in supporting(e, rule, y, m, d).items():
            if k not in sub:
                continue
            iy, im = sub[k]["date"]
            lag = (iy - y) * 12 + (im - m)
            (pre if lag < 0 else post).append((k, lag, off))
        post.sort(key=lambda x: x[1])
        if not post:
            return "ABSENT", post, pre
        return ("ROOTED" if post[0][1] <= ROOT_LAG else "LATE_ONLY"), post, pre

    res = {}
    for e in testable:
        res[e["event_id"]] = classify(e, e["y"], e["m"], e["d"])
    n = len(testable)
    obs = sum(res[e["event_id"]][0] == "ROOTED" for e in testable) / n
    pre_rate = sum(bool(res[e["event_id"]][2]) for e in testable) / n
    dates = [(e["y"], e["m"], e["d"]) for e in testable]
    null = []
    for _ in range(NSHUF):
        sh = dates[:]
        rng.shuffle(sh)
        k = 0
        for e, (y, m, d) in zip(testable, sh):
            if (y, m) == (e["y"], e["m"]):
                y, m, d = rng.choice(dates)
            k += classify(e, y, m, d)[0] == "ROOTED"
        null.append(k / n)
    null.sort()
    nm = sum(null) / len(null)
    p = (sum(x >= obs for x in null) + 1) / (len(null) + 1)
    ind = [1.0 if res[e["event_id"]][0] == "ROOTED" else 0.0 for e in testable]
    bs = sorted(sum(rng.choice(ind) for _ in ind) / n - nm for _ in range(5000))
    cls = Counter(v[0] for v in res.values())
    lo, hi = int(0.025 * NSHUF), int(0.975 * NSHUF) - 1
    summary = dict(issues=len(sub), span=["%04d-%02d" % first, "%04d-%02d" % last],
                   testable=n, classes=dict(cls), rooted=cls["ROOTED"], rooted_rate=obs,
                   null_mean=nm, null_ci95=[null[lo], null[hi]], p=p,
                   effect=obs - nm, effect_ci95=[bs[124], bs[4874]], pre_event_rate=pre_rate)
    return summary, res


def main():
    if not os.path.isdir(PD):
        sys.exit("set OMEGA_PERIODICALS")
    issues, nA, skipped = load()
    keysA = [k for k in issues if k.startswith("A/")]
    keysAB = list(issues)
    print(f"corpus A {nA} issues; B {len(issues) - nA} issues; skipped {dict(skipped)}", flush=True)
    print("B by series (top 25):", Counter(v["src"] for v in issues.values()
                                         if v["corpus"] == "B").most_common(25), flush=True)

    events = []
    for r in csv.DictReader(open(EV, encoding="utf-8")):
        try:
            y, m = int(r["date"][:4]), int(r["date"][5:7])
        except ValueError:
            y = m = None
        try:
            d = int(r["date"][8:10]) or None
        except ValueError:
            d = None
        toks = pg1.tokens(r)
        base = "NO_DATE" if not (y and m) else ("NO_TOKEN" if not toks else None)
        events.append(dict(event_id=r["event_id"], rank=int(r["rank"]),
                           named_case=r["named_case"], date=r["date"], y=y, m=m, d=d,
                           tokens=toks, n_catalogs=int(r["n_catalogs"] or 0), base_cls=base))
    # one scan of the whole corpus per event (forked workers share the corpus)
    global _ISSUES
    _ISSUES = issues
    todo = [e for e in events if not e["base_cls"]]
    with multiprocessing.get_context("fork").Pool(int(os.environ.get("OMEGA_PROCS", "4"))) as pool:
        for i, (eid, ym) in enumerate(pool.imap_unordered(
                scan_event, [(e["event_id"], e["tokens"]) for e in todo], chunksize=2)):
            ev = next(e for e in todo if e["event_id"] == eid)
            ev["ym"], ev["ymd"] = ym
            if i % 50 == 0:
                print("scanned", i, "/", len(todo), flush=True)

    cells = {}
    results = {}
    for cname, keys in (("A", keysA), ("A+B", keysAB)):
        for rule in ("strict", "recall"):
            s, res = run(issues, events, keys, rule, random.Random(20261126))
            cells[f"{cname}|{rule}"] = s
            results[f"{cname}|{rule}"] = res
            print(f"{cname:4s} {rule:6s} testable {s['testable']} rooted {s['rooted']} "
                  f"({s['rooted_rate']:.3f}) null {s['null_mean']:.3f} "
                  f"[{s['null_ci95'][0]:.3f},{s['null_ci95'][1]:.3f}] p {s['p']:.4f} "
                  f"effect {s['effect']:+.3f} CI [{s['effect_ci95'][0]:+.3f},{s['effect_ci95'][1]:+.3f}] "
                  f"pre {s['pre_event_rate']:.3f}  {s['classes']}", flush=True)

    def ctx_of(k, off):
        t = issues[k]["text"]
        return " ".join(t[max(0, off - WIN): off + WIN].split())[:500]

    nodes = []
    for e in events:
        o = {x: e[x] for x in ("event_id", "rank", "named_case", "date", "tokens", "n_catalogs")}
        for cell, res in results.items():
            if e["event_id"] not in res:
                o[cell] = dict(cls=e["base_cls"] or "OUT_OF_COVERAGE")
                continue
            c, post, pre = res[e["event_id"]]
            d = dict(cls=c, n_post=len(post), n_pre=len(pre))
            if post:
                k, lag, off = post[0]
                iv = issues[k]
                d.update(earliest=k, lag_months=lag, char_offset=off,
                         issue_date="%04d-%02d" % iv["date"], month_known=iv["month_known"],
                         source=iv["src"], ia_id=iv.get("ia_id"), ia_file=iv.get("ia_file"),
                         context=ctx_of(k, off))
            o[cell] = d
        nodes.append(o)

    # what moved, A|strict -> A+B|recall, and by which step
    moves = Counter()
    for o in nodes:
        moves[(o["A|strict"]["cls"], o["A+B|recall"]["cls"])] += 1
    first_src = Counter(o["A+B|recall"].get("source") for o in nodes
                        if o["A+B|recall"]["cls"] == "ROOTED")
    yo = sum(1 for o in nodes if o["A+B|recall"]["cls"] == "ROOTED"
             and not o["A+B|recall"].get("month_known"))
    # catalogue count vs rooted, expanded cell
    tst = [o for o in nodes if o["A+B|recall"]["cls"] in ("ROOTED", "ABSENT", "LATE_ONLY")]
    by_cat = {}
    for o in tst:
        b = min(o["n_catalogs"], 6)
        by_cat.setdefault(b, [0, 0])
        by_cat[b][0] += o["A+B|recall"]["cls"] == "ROOTED"
        by_cat[b][1] += 1
    print("moves A|strict -> A+B|recall:", {f"{a}->{b}": v for (a, b), v in moves.items() if a != b})
    print("first-root source (A+B|recall):", first_src.most_common())
    print("ROOTED resting on a year-only issue:", yo)
    same = [o for o in nodes if o["A|strict"]["cls"] in ("ROOTED", "ABSENT", "LATE_ONLY")]
    same_set = {c: sum(o[c]["cls"] == "ROOTED" for o in same) for c in results}
    print(f"rooted on the {len(same)} A-testable events only:", same_set)
    print("rooted by catalogue count:", {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_cat.items())})
    json.dump(dict(cells=cells, skipped=dict(skipped),
                   corpus_B_series=Counter(v["src"] for v in issues.values() if v["corpus"] == "B"),
                   moves={f"{a}->{b}": v for (a, b), v in moves.items()},
                   first_root_source=dict(first_src), rooted_on_year_only_issue=yo,
                   rooted_by_catalogs={str(k): v for k, v in sorted(by_cat.items())},
                   nodes=nodes), open(OUT, "w"), indent=1, ensure_ascii=False)
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
