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
import hashlib
import multiprocessing
import pickle
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


def _interpolate(rows):
    """rows: [order, key, anchor (y, m) or None, strong]. A weak anchor that
    breaks publication order by more than 3 months against both neighbours is
    dropped; a strong anchor (a masthead read off the cover) is never dropped,
    because the FSR collection is not strictly in publication order (its
    July/August issues sit out of sequence). Unanchored rows get a linear
    interpolation in months between the nearest anchors (month_known False).
    Returns key -> date."""
    rows = sorted(rows)
    mon = lambda d: d[0] * 12 + d[1] - 1
    good = [(i, mon(r[2]), bool(r[3]) if len(r) > 3 else False) for i, r in enumerate(rows) if r[2]]
    while True:                          # drop weak outliers until the anchors are consistent
        keep = []
        for j, (i, v, strong) in enumerate(good):
            pv = good[j - 1][1] if j > 0 else None
            nv = good[j + 1][1] if j + 1 < len(good) else None
            if strong:
                bad = False
            elif pv is not None and nv is not None:
                bad = (v < pv - 3 and v < nv - 3) or (v > pv + 3 and v > nv + 3)
            else:
                bad = abs(v - (pv if pv is not None else nv)) > 24 if (pv is not None or nv is not None) else False
            if not bad:
                keep.append((i, v, strong))
        if len(keep) == len(good):
            break
        good = keep
    good = [(i, v) for i, v, _ in good]
    out = {}
    gi = dict(good)
    for i, r in enumerate(rows):
        if i in gi:
            out[r[1]] = (gi[i] // 12, gi[i] % 12 + 1, True)
            continue
        lo = max((g for g in good if g[0] < i), default=None)
        hi = min((g for g in good if g[0] > i), default=None)
        if lo and hi:
            v = lo[1] + (hi[1] - lo[1]) * (i - lo[0]) / (hi[0] - lo[0])
        elif lo or hi:
            continue                       # outside the anchored span: leave undated
        else:
            continue
        v = int(round(v))
        out[r[1]] = (v // 12, v % 12 + 1, False)
    return out


def build_fsr_dates(recs, xd):
    """file -> (year, month, month_known). Anchor = a cover date within 120 chars
    of the "Vol N No M" masthead that agrees with the volume year (+-1); other
    issues are interpolated between anchors in publication order."""
    rows = []
    for r in recs:
        n = int(re.search(r"^(\d+)\.FSR", r["file"]).group(1))
        t = open(os.path.join(xd, "txt", r["path"]), encoding="utf-8", errors="replace").read()[:5000]
        anchor, strong = None, False
        for v in FSR_VOL.finditer(t):
            vy = fsr_vol_year(_ocr_int(v.group(1)))
            if vy is None:
                continue
            no = _ocr_int(v.group(2))
            w = t[max(0, v.start() - 120): v.end() + 120]
            cands = [(int(y), EN[mo.lower()[:3]], mm.start()) for mm in NAMEDATE.finditer(w)
                     for mo, y in [mm.groups()]]
            # "Vol. 36, No. 4 (Winter, 1991)" is the last issue of 1991, not January
            cands += [(int(y), 12 if se.lower() == "winter" and no == 4 else SEASON_M[se.lower()], mm.start())
                      for mm in SEASON.finditer(w) for se, y in [mm.groups()]]
            cands = [c for c in cands if abs(c[0] - vy) <= 1]
            if cands:
                c = min(cands, key=lambda c: abs(c[2] - 120))
                anchor, strong = (c[0], c[1]), v.start() <= 1000   # a masthead, not a citation
                break
        if anchor is None:                  # early covers print the date with no volume
            m0 = NAMEDATE.search(t[:300])
            v0 = next((fsr_vol_year(_ocr_int(v.group(1))) for v in FSR_VOL.finditer(t)
                       if fsr_vol_year(_ocr_int(v.group(1)))), None)
            if m0 and (v0 is None or abs(int(m0.group(2)) - v0) <= 1):
                anchor = (int(m0.group(2)), EN[m0.group(1).lower()[:3]])
        if anchor is None:
            # derive from Vol/No where FSR's schedule was regular (read off the
            # dated covers in this collection): bimonthly vol 1-19 (vol 1 started
            # Mar-Apr 1955, vol v>=2 No k = month 2k-1 of 1954+v); quarterly from
            # vol 33 (1988), No k = month 3k of 1955+v. Vol 20-32 ran late and
            # irregular, so those are left to interpolation.
            for v in FSR_VOL.finditer(t):
                vol, no = _ocr_int(v.group(1)), _ocr_int(v.group(2))
                if not vol or not no:
                    continue
                if vol == 1 and 1 <= no <= 6:
                    anchor = (1955, min(12, 2 * no + 1))
                elif 2 <= vol <= 19 and 1 <= no <= 6:
                    anchor = (1954 + vol, 2 * no - 1)
                elif 33 <= vol <= 60 and 1 <= no <= 4:
                    anchor = (1955 + vol, 3 * no)
                if anchor:
                    strong = v.start() <= 400          # the cover's own volume mark
                    break
        rows.append([n, r["file"], anchor, strong])
    FSR_DATES.update(_interpolate(rows))


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
    """path -> date. Anchor = the French month-year nearest the "N° <n>" mark on
    the cover (within 80 chars), else a "<n> - <mois> <annee>" masthead; others
    interpolated by issue number. (Taking the first date in the text, as the
    first version did, read LDLN 120 = Oct 1972 as Jan 1971 from a photo caption.)"""
    rows = []
    for r in recs:
        m = re.search(r"LDLN_No_(\d+)", r["id"])
        if not m:
            continue
        n = int(m.group(1))
        t = open(os.path.join(xd, "txt", r["path"]), encoding="utf-8", errors="replace").read()[:6000]
        tl = t.lower()
        anchor = None
        for h in re.finditer(r"(?:n\W{0,3}\s*|^|\s)%d\b" % n, tl):
            w0 = max(0, h.start() - 80)
            w = tl[w0: h.end() + 80]
            cands = [(int(mm.group(2)), _fr_month(mm.group(1)), abs(w0 + mm.start() - h.start()))
                     for mm in FR_MONTH.finditer(w)]
            cands = [c for c in cands if c[1]]
            if cands:
                c = min(cands, key=lambda c: c[2])
                anchor = (c[0], c[1])
                break
        rows.append([n, r["path"], anchor])
    LDLN_DATES.update(_interpolate(rows))


# ---- month, season or quarter named in an archive.org id/title (AFU items).
# The month usually comes BEFORE the year ("Nov_1983", "maj_juni_1971",
# "3e_trim_1957", "Summer_1964"), in English, French, Italian, Spanish,
# Portuguese, German, Dutch or Scandinavian. A range gives its first month.
TM = {}
for _i, _ws in enumerate((
        "january jan janvier janv gennaio enero ene janeiro januar januari janner",
        "february feb febr fevrier fev fevr febbraio febrero fevereiro februar februari",
        "march mar mars marzo marco marz maerz marts maart",
        "april apr avril avr avri aprile abril abr",
        "may mai maggio mayo maio maj mei",
        "june jun juin giugno giu junio junho juni",
        "july jul juillet juil luglio lug julio julho juli",
        "august aug aout agosto ago augusti augustus",
        "september sep sept septembre settembre set septiembre setiembre setembro",
        "october oct octobre ottobre ott octubre outubro oktober okt",
        "november nov novembre noviembre novembro",
        "december dec decembre dicembre dic diciembre dezembro dezember dez desember"), 1):
    for _w in _ws.split():
        TM[_w] = _i
# winter -> December of the named year (BUFORA "Winter 1968(9)"), flagged as approximate
TSEASON = {"spring": 4, "printemps": 4, "primavera": 4, "fruhling": 4, "summer": 7, "ete": 7,
           "verano": 7, "sommer": 7, "zomer": 7, "autumn": 10, "fall": 10, "automne": 10,
           "autunno": 10, "otono": 10, "herbst": 10, "herfst": 10, "winter": 12, "hiver": 12,
           "inverno": 12, "invierno": 12}
UNAMBIG = {"spring", "summer", "autumn", "winter", "printemps", "automne", "hiver"} | \
    {w for w in TM if len(w) >= 5 and w not in ("march", "mars", "august", "marzo")}
QN = re.compile(r"^([1-4])(?:er|e|eme|st|nd|rd|th)?$")
YEAR = r"(19[4-9]\d|200\d|2010)"


def _tok(s):
    out = []
    for t in re.split(r"[^0-9a-z]+", s.lower().translate(FOLD)):
        m = re.fullmatch(r"([a-z]+)(\d{4})|(\d{4})([a-z]+)", t)     # "oct1993", "janv1979"
        out += [x for x in m.groups() if x] if m else ([t] if t else [])
    return out


def _word_month(t, j):
    """(month, known) if token j names a month, season or quarter."""
    w = t[j]
    if w in TM:
        return TM[w], True
    for k in range(3, len(w) - 2):               # "mayjune", "septoct", "novdec"
        if w[:k] in TM and w[k:] in TM:
            return TM[w[:k]], True
    if w in TSEASON:
        return TSEASON[w], TSEASON[w] != 12
    if re.fullmatch(r"q[1-4]", w):
        return 3 * int(w[1]) - 1, True
    if w in ("trim", "trimestre") and j > 0 and QN.match(t[j - 1]):
        return 3 * int(QN.match(t[j - 1]).group(1)) - 1, True
    return None


def title_month(s, year):
    """(month, known) from the id/title words next to the year, or None."""
    t = _tok(s)
    yy = str(year)
    skip = {"and", "et", "y", "og", "och", "und", "to", "a", "i", "ii", "iii"}
    for yi in [i for i, w in enumerate(t) if w == yy or (w == yy[2:] and i > 0 and t[i - 1] in TM)]:
        found, j = None, yi - 1                    # contiguous run before the year
        while j >= 0 and yi - j <= 5:
            wm = _word_month(t, j)
            if wm:
                found = wm
            elif t[j] in skip or (t[j].isdigit() and 1 <= int(t[j]) <= 31 and found is None and yi - j == 1) \
                    or QN.match(t[j]):
                pass
            else:
                break
            j -= 1
        if found:
            return found
        for j in range(yi + 1, min(len(t), yi + 3)):   # or right after it
            wm = _word_month(t, j)
            if wm:
                return wm
    hits = [(j, _word_month(t, j)) for j, w in enumerate(t) if w in UNAMBIG or re.fullmatch(r"q[1-4]", w)]
    if hits and len({m for _, (m, _) in hits}) == 1:
        return hits[0][1]
    if len(hits) > 1 and all(b[0] - a[0] == 1 for a, b in zip(hits, hits[1:])):
        return hits[0][1]                          # a contiguous range: its first month
    return None


def expansion_date(rec, text):
    s = " ".join(filter(None, [rec.get("id"), rec.get("title")])).replace("-", "_")
    m = re.search(r"(?<!\d)" + YEAR + r"(0[1-9]|1[0-2])\d{2}(?!\d)", s)  # AFU_19520715_
    if m:
        return int(m.group(1)), int(m.group(2)), True
    for m in re.finditer(r"(?<!\d)" + YEAR + r"[_ .](0[1-9]|1[0-2])(?!\d)", s):
        y, mm = int(m.group(1)), int(m.group(2))
        if mm == (y + 1) % 100 and re.search(rf"{y}-{m.group(2)}[_ ]Vol", rec.get("id") or ""):
            continue                                # "Awareness_2010-11_Vol_31": a volume year span
        return y, mm, True
    if rec.get("series") == "FSR":
        return FSR_DATES.get(rec.get("file"))
    if rec.get("path") in LDLN_DATES:
        return LDLN_DATES[rec["path"]]
    m = re.search(r"(?<!\d)" + YEAR + r"(?!\d)", s) or re.search(r"^" + YEAR, rec.get("date") or "")
    if m:
        y = int(m.group(1))
        tm = title_month(s, y)
        if tm:
            return y, tm[0], tm[1]
        return y, 6, False
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
    # The scan reads only the issue texts, never their dates, so a re-dating run can
    # reuse it: OMEGA_SCAN_CACHE=<file> stores it, keyed by the issue set and tokens.
    cache = os.environ.get("OMEGA_SCAN_CACHE")
    sig = hashlib.sha256(json.dumps([sorted(issues), [(e["event_id"], e["tokens"]) for e in todo],
                                     WIN]).encode()).hexdigest()
    got = {}
    if cache and os.path.exists(cache):
        with open(cache, "rb") as fh:
            c = pickle.load(fh)
        if c.get("sig") == sig:
            got = c["scan"]
            print("scan cache hit:", len(got), "events", flush=True)
    if not got:
        with multiprocessing.get_context("fork").Pool(int(os.environ.get("OMEGA_PROCS", "4"))) as pool:
            for i, (eid, ym) in enumerate(pool.imap_unordered(
                    scan_event, [(e["event_id"], e["tokens"]) for e in todo], chunksize=2)):
                got[eid] = ym
                if i % 50 == 0:
                    print("scanned", i, "/", len(todo), flush=True)
        if cache:
            with open(cache, "wb") as fh:
                pickle.dump(dict(sig=sig, scan=got), fh)
    for e in todo:
        e["ym"], e["ymd"] = got[e["event_id"]]

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
