"""Layer 1 (polyglot drill): normalised event catalogues.

Builds date/place-normalised tables from sources that are already on disk:

  RU_NATIVE   Chernobrov, "Хроники визитов НЛО" (Kosmopoisk archive, state 2.09.2002),
              archive.org item hroniki_vizitov_nlo, Russian original text.
  HATCH       Larry Hatch *U* database (ufo_data/bin/hatch_udb.json), English summaries
              compiled 1994-2002 from Western books and periodicals.
  NUFORC      evidence_vault/06_NUFORC_MODERN_ARM/nuforc_unified.json.gz (US reports).
  GEIPAN      data/raw/geipan/geipan_cases.json (French state file, 3,404 cases).
  LAUNCHES    CelesTrak SATCAT snapshot (archive.org satcat_2025_07_10_cutToEndJune), one row
              per international designator (orbital launch attempts that catalogued an object).
  NUCLEAR     GeoNuclearData power reactors (IAEA PRIS/WNA) + ufo_data nuclear_tests.json.
  POP         Natural Earth 10m populated places (population proxy and gazetteer, has NAME_RU,
              NAME_ZH, NAME_AR).

Everything here is deterministic. Geocoding of the Russian catalogue is a gazetteer
lookup against Natural Earth names (Russian), with a short table of Soviet-era city
names; it is city-level at best and every row records how it was geocoded.
"""
import csv
import collections
import datetime as dt
import gzip
import json
import math
import os
import re

ROOT = os.environ.get("OMEGA_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
RAW = os.path.join(ROOT, "data", "raw", "layer1")
UFO_DATA = os.environ.get("UFO_DATA_BIN", os.path.join(os.path.dirname(ROOT), "ufo_data", "bin"))

SU_COUNTRIES_HATCH = {
    "Russia", "Ukraine", "Kazakh Republic", "Estonia, Latvia& Lithuania", "Georgia", "Belorus",
    "Uzbek Republic", "Turkmen Republic", "Armenia", "Tadzhik Republic", "Azerbaijan",
}
CN_COUNTRIES_HATCH = {"China", "Taiwan China"}
ARAB_COUNTRIES_HATCH = {
    "Algeria", "Morocco", "Tunisia", "Arabian Peninsula", "Libya", "Kuwait", "Egypt", "Lebanon",
    "Jordan", "Sudan", "Syria", "Sahara",
}
SASIA_COUNTRIES_HATCH = {"India", "Pakistan", "Himalayan states"}
SU_ISO2 = {"RU", "UA", "BY", "KZ", "UZ", "TM", "TJ", "KG", "AZ", "AM", "GE", "MD", "LV", "LT", "EE"}

# Soviet-era / alternative city names -> modern Natural Earth NAME_RU (well-known renamings only).
SOVIET_ALIASES = {
    "ленинград": "Санкт-Петербург", "петербург": "Санкт-Петербург", "горький": "Нижний Новгород",
    "горьк": "Нижний Новгород", "свердловск": "Екатеринбург", "куйбышев": "Самара",
    "калинин": "Тверь", "фрунзе": "Бишкек", "ворошиловград": "Луганск", "жданов": "Мариуполь",
    "загорск": "Сергиев Посад", "брежнев": "Набережные Челны", "андропов": "Рыбинск",
    "устинов": "Ижевск", "орджоникидзе": "Владикавказ", "днепропетровск": "Днепр",
    "кировабад": "Гянджа", "ленинакан": "Гюмри", "целиноград": "Астана", "алма-ата": "Алматы",
    "алма-аты": "Алматы", "гурьев": "Атырау", "шевченко": "Актау", "ленинабад": "Худжанд",
    "сталинабад": "Душанбе", "сталинград": "Волгоград", "молотов": "Пермь", "чкалов": "Оренбург",
    "кенигсберг": "Калининград", "тифлис": "Тбилиси", "ашгабат": "Ашхабад", "таллинн": "Таллин",
    "кишинев": "Кишинёв", "кишинёв": "Кишинёв", "николаев": "Николаев", "запорожье": "Запорожье",
}
COUNTRY_TOKENS_RU = [
    ("ссср", "SU"), ("россия", "RU"), ("рф", "RU"), ("украина", "UA"), ("казахстан", "KZ"),
    ("белоруссия", "BY"), ("беларусь", "BY"), ("латвия", "LV"), ("литва", "LT"), ("эстония", "EE"),
    ("грузия", "GE"), ("армения", "AM"), ("азербайджан", "AZ"), ("узбекистан", "UZ"),
    ("туркмения", "TM"), ("туркменистан", "TM"), ("таджикистан", "TJ"), ("киргизия", "KG"),
    ("кыргызстан", "KG"), ("молдавия", "MD"), ("молдова", "MD"), ("сша", "US"), ("америка", "US"),
    ("англия", "GB"), ("великобритания", "GB"), ("шотландия", "GB"), ("франция", "FR"),
    ("германия", "DE"), ("фрг", "DE"), ("гдр", "DE"), ("китай", "CN"), ("кнр", "CN"),
    ("япония", "JP"), ("италия", "IT"), ("испания", "ES"), ("бразилия", "BR"), ("аргентина", "AR"),
    ("мексика", "MX"), ("канада", "CA"), ("австралия", "AU"), ("польша", "PL"), ("болгария", "BG"),
    ("венгрия", "HU"), ("чехословакия", "CS"), ("чехия", "CZ"), ("румыния", "RO"),
    ("югославия", "YU"), ("финляндия", "FI"), ("швеция", "SE"), ("норвегия", "NO"), ("индия", "IN"),
    ("иран", "IR"), ("турция", "TR"), ("египет", "EG"), ("израиль", "IL"), ("бельгия", "BE"),
    ("монголия", "MN"), ("куба", "CU"), ("чили", "CL"), ("перу", "PE"), ("корея", "KR"),
    ("вьетнам", "VN"), ("афганистан", "AF"), ("антарктида", "AQ"), ("океан", "OC"), ("море", "SEA"),
    ("космос", "SPACE"), ("орбит", "SPACE"), ("луна", "SPACE"),
]


def hav_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(min(1.0, math.sqrt(a)))


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


# ---------------------------------------------------------------- gazetteer / population
def load_places():
    d = json.load(open(os.path.join(RAW, "ne", "ne_pp.geojson")))
    out = []
    for f in d["features"]:
        p = f["properties"]
        out.append(dict(
            name=p.get("NAME"), name_en=p.get("NAME_EN"), name_ru=p.get("NAME_RU"),
            name_uk=p.get("NAME_UK"), name_zh=p.get("NAME_ZH"), name_zht=p.get("NAME_ZHT"),
            name_ar=p.get("NAME_AR"), alt=p.get("NAMEALT"), iso2=p.get("ISO_A2"),
            adm0=p.get("ADM0NAME"), adm1=p.get("ADM1NAME"), lat=p.get("LATITUDE"),
            lon=p.get("LONGITUDE"), pop=p.get("POP_MAX") or 0,
            pop1980=p.get("POP1980") or 0,
        ))
    return out


_RU_INDEX = None


def ru_index():
    """lower-cased Russian/Ukrainian names -> list of places (largest population first)."""
    global _RU_INDEX
    if _RU_INDEX is None:
        idx = collections.defaultdict(list)
        for p in load_places():
            for nm in (p["name_ru"], p["name_uk"]):
                if nm:
                    idx[nm.lower().replace("ё", "е")].append(p)
        for k in idx:
            idx[k].sort(key=lambda p: -(p["pop"] or 0))
        _RU_INDEX = idx
    return _RU_INDEX


WORD = re.compile(r"[А-Яа-яЁёІіЇїЄє-]+")


def _cands(word):
    """Nominative candidates for an inflected Russian place word (cheap stemming)."""
    w = word.lower().replace("ё", "е").strip("-")
    out = [w]
    for suf, reps in (("ом", ["", "а"]), ("ем", ["ь", "", "е"]), ("ой", ["а", "ая", ""]),
                      ("ей", ["ь", "я"]), ("ах", ["и", "ы"]), ("ах", [""]), ("е", ["", "а", "ь", "о"]),
                      ("и", ["ь", "а", "я", ""]), ("ы", ["а", ""]), ("у", ["", "а"]), ("а", [""]),
                      ("я", ["ь", "й"]), ("ю", ["ь", "я"]), ("ого", ["ий", "ой", "ое"]),
                      ("ска", ["ск"]), ("ске", ["ск"]), ("ском", ["ск"]), ("ску", ["ск"]),
                      ("цка", ["цк"]), ("цке", ["цк"]), ("цком", ["цк"]), ("ова", ["ов"]),
                      ("ове", ["ов"]), ("овом", ["ов"]), ("ева", ["ев"]), ("еве", ["ев"]),
                      ("ина", ["ин"]), ("ине", ["ин"]), ("ино", ["ино"]), ("ске", ["ск"])):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            for r in reps:
                out.append(w[: len(w) - len(suf)] + r)
    return out


OBLAST = re.compile(r"([А-Яа-яЁё-]+?)(ск|цк)(ая|ой|ую|ий|ого|ом)\s+(обл|област|кра[йяю]|район|р-н|АССР|республик)", re.I)


REGION_CAPITALS = {  # region / republic stem -> administrative centre (Natural Earth NAME_RU)
    "московск": "Москва", "подмосков": "Москва", "калужск": "Калуга", "вологодск": "Вологда",
    "читинск": "Чита", "пензенск": "Пенза", "новгородск": "Великий Новгород",
    "нижегородск": "Нижний Новгород", "горьковск": "Нижний Новгород", "ростовск": "Ростов-на-Дону",
    "куйбышевск": "Самара", "запорожск": "Запорожье", "винницк": "Винница", "крымск": "Симферополь",
    "крым": "Симферополь", "приморск": "Владивосток", "алтайск": "Барнаул", "орловск": "Орёл",
    "башкир": "Уфа", "татар": "Казань", "карел": "Петрозаводск", "коми": "Сыктывкар",
    "якут": "Якутск", "бурят": "Улан-Удэ", "чуваш": "Чебоксары", "мордов": "Саранск",
    "удмурт": "Ижевск", "дагестан": "Махачкала", "чукот": "Анадырь", "камчат": "Петропавловск-Камчатский",
    "сахалин": "Южно-Сахалинск", "кабардино": "Нальчик", "осетия": "Владикавказ", "чечн": "Грозный",
    "тува": "Кызыл", "хакас": "Абакан", "калмык": "Элиста", "ярославск": "Ярославль",
    "тульск": "Тула", "марийск": "Йошкар-Ола", "адыге": "Майкоп", "закарпат": "Ужгород",
    "семипалатинск": "Семей", "свердловск": "Екатеринбург", "ленинградск": "Санкт-Петербург",
    "сталинградск": "Волгоград", "молотовск": "Пермь", "калининградск": "Калининград",
}
DISTRICT_NEXT = re.compile(r"^\s*(?:район|р-н|р-на|района|районе|сельсовет|улиц|шоссе|проспект|обл|област|кра[йяе]|АССР|ССР|республик)", re.I)
STOP_PLACE = {"восток", "запад", "север", "юг", "мир", "город", "река", "озеро", "поселок", "село",
              "деревня", "район", "область", "москва-река", "талька", "заря", "победа", "октябрь",
              "свобода", "дружба", "ссср", "россия", "украина", "союз"}


def _lookup(key, prefer_su, strict=False):
    idx = ru_index()
    key = key.lower().replace("ё", "е")
    if key not in idx:
        return None
    cands = idx[key]
    if prefer_su:
        su = [p for p in cands if p["iso2"] in SU_ISO2]
        if strict and not su:
            return None
        cands = su or cands
    return cands[0]


def geocode_ru(place, prefer_su=True):
    """Return (lat, lon, matched_name, how) or None.

    Priority: exact city name (or Soviet-era alias) > region/oblast administrative centre >
    stemmed (inflected) city name. Words directly followed by "район"/"р-н" are district
    names and are not matched as cities. City-level precision at best.
    """
    s = place.replace("ё", "е")
    tokens = [(m.group(0), m.end()) for m in WORD.finditer(s)]
    words = [w for w, _ in tokens]
    exact, stemmed = [], []
    for n in (3, 2, 1):
        for i in range(len(words) - n + 1):
            end = tokens[i + n - 1][1]
            if DISTRICT_NEXT.match(s[end:]):
                continue
            chunk = [w.lower() for w in words[i:i + n]]
            phrase = " ".join(chunk)
            if phrase.replace("ё", "е") in STOP_PLACE:
                continue
            al = SOVIET_ALIASES.get(phrase)
            p = _lookup(al or phrase, prefer_su)
            if p and (len(phrase) >= 4 or phrase in ("уфа", "орел", "ош")):
                exact.append(((n, p["pop"] or 0), p, ("alias:" if al else "exact:") + phrase))
                continue
            if n == 1:
                for c in _cands(chunk[0])[1:]:
                    al = SOVIET_ALIASES.get(c)
                    p = _lookup(al or c, prefer_su)
                    if p and len(c) >= 5:
                        stemmed.append(((n, p["pop"] or 0), p, "stem:" + c))
                        break
    if exact:
        sc, p, how = max(exact, key=lambda t: t[0])
        return (p["lat"], p["lon"], p["name_ru"] or p["name"], how)
    su_stem = [t for t in stemmed if t[1]["iso2"] in SU_ISO2 and len(t[2]) >= 11] if prefer_su else []
    if su_stem:
        sc, p, how = max(su_stem, key=lambda t: t[0])
        return (p["lat"], p["lon"], p["name_ru"] or p["name"], how)
    low = s.lower()
    # region / oblast / republic -> administrative centre
    ms = sorted(OBLAST.finditer(s), key=lambda m: (m.group(4).lower().startswith(("район", "р-н")), m.start()))
    for m in ms:
        stem = (m.group(1) + m.group(2)).lower()
        kind = "district-centre:" if m.group(4).lower().startswith(("район", "р-н")) else "region-capital:"
        for c in ([REGION_CAPITALS[stem]] if stem in REGION_CAPITALS else []) + [
                stem[:-2], stem[:-2] + "ь", stem[:-2] + "а", stem, stem[:-2] + "ы"]:
            if len(c) < 4:
                continue
            p = _lookup(SOVIET_ALIASES.get(c, c), prefer_su, strict=prefer_su)
            if p:
                return (p["lat"], p["lon"], p["name_ru"] or p["name"], kind + m.group(0))
    for k, v in REGION_CAPITALS.items():
        if re.search(r"(?:^|[^а-я])" + k, low):
            p = _lookup(v, prefer_su, strict=prefer_su)
            if p:
                return (p["lat"], p["lon"], p["name_ru"] or p["name"], "region-capital:" + k)
    if stemmed:
        sc, p, how = max(stemmed, key=lambda t: t[0])
        return (p["lat"], p["lon"], p["name_ru"] or p["name"], how)
    return None


def country_ru(place):
    s = " " + place.lower().replace("ё", "е") + " "
    hits = []
    for tok, iso in COUNTRY_TOKENS_RU:
        if re.search(r"[^а-я]" + tok, s):
            hits.append(iso)
    return hits


# ---------------------------------------------------------------- Russian native catalogue
MON = {"январ": 1, "феврал": 2, "март": 3, "апрел": 4, "мая": 5, "май": 5, "июн": 6, "июл": 7,
       "август": 8, "сентябр": 9, "октябр": 10, "ноябр": 11, "декабр": 12}
MON_RE = r"(январ[яь]|феврал[яь]|марта?|апрел[яь]|ма[яй]|июн[яь]|июл[яь]|августа?|сентябр[яь]|октябр[яь]|ноябр[яь]|декабр[яь])"
HDR = re.compile(
    r"(?m)^\s*(?:(?P<day>[0-9|lIЗ]{1,2}(?:\s*[-–]\s*[0-9]{1,2})?)\s+)?(?:(?P<mon>" + MON_RE +
    r")\s+)?(?:(?P<season>весна|лето|осень|зима|начало|середина|конец)\w*\s+)?(?P<year>1[0-9]{3}|20[0-2][0-9]|[1-9][0-9]{2})"
    r"\s*(?:г\.?|года?)?\s*(?:\((?:или|по другим)[^)]*\))?\s*(?:,\s*(?P<time>[^;\n]{1,40}))?;\s*(?P<place>[^\n]{2,200})$")


def parse_chernobrov(path):
    t = open(path, encoding="utf-8", errors="replace").read().replace("­", "")
    ms = list(HDR.finditer(t))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(t)
        body = t[m.end():end].strip()
        place = m.group("place").strip()
        # place may continue on the next line(s) until a full stop
        if not place.rstrip().endswith("."):
            lines = body.split("\n")
            add = []
            for ln in lines[:2]:
                if not ln.strip():
                    continue
                add.append(ln.strip())
                if ln.strip().endswith("."):
                    break
            if add and len(" ".join(add)) < 160:
                place = place + " " + " ".join(add)
                body = "\n".join(lines[len(add):]).strip() if len(add) < len(lines) else ""
        day = m.group("day")
        dnum = None
        if day:
            day = day.replace("|", "1").replace("l", "1").replace("I", "1").replace("З", "3")
            try:
                dnum = int(re.split(r"\s*[-–]\s*", day)[0])
            except ValueError:
                dnum = None
        mnum = None
        if m.group("mon"):
            for k, v in MON.items():
                if m.group("mon").startswith(k):
                    mnum = v
                    break
        y = int(m.group("year"))
        prec = "day" if (dnum and mnum) else ("month" if mnum else ("season" if m.group("season") else "year"))
        iso = None
        if prec == "day":
            try:
                iso = dt.date(y, mnum, dnum).isoformat()
            except ValueError:
                prec, iso = "month", None
        out.append(dict(
            uid="RU_CH#%04d" % i, catalog="RU_NATIVE", year=y, month=mnum, day=dnum if prec == "day" else None,
            date=iso, prec=prec, time_ru=(m.group("time") or "").strip(), place_ru=place,
            text_ru=body[:6000], src_offset=m.start(),
        ))
    return out


def load_ru_native():
    path = os.path.join(RAW, "ru", "whole", "hroniki_vizitov_nlo__hroniki_vizitov_nlo_djvu.txt")
    rows = parse_chernobrov(path)
    for r in rows:
        cs = country_ru(r["place_ru"])
        r["countries"] = cs
        su = [c for c in cs if c in SU_ISO2 or c == "SU"]
        foreign = [c for c in cs if c not in SU_ISO2 and c not in ("SU", "SEA", "OC", "SPACE")]
        r["region"] = "SU" if su and not foreign else ("FOREIGN" if foreign and not su else ("MIXED" if su else "UNK"))
        g = geocode_ru(r["place_ru"], prefer_su=(r["region"] != "FOREIGN"))
        if g:
            r["lat"], r["lon"], r["geo_name"], r["geo_how"] = g
        else:
            r["lat"] = r["lon"] = None
            r["geo_name"] = r["geo_how"] = None
        # an un-flagged place that geocodes inside the former USSR counts as SU
        if r["region"] == "UNK" and g:
            near = nearest_place(g[0], g[1])
            if near and near["iso2"] in SU_ISO2:
                r["region"] = "SU?"
    return rows


_PLACES = None


def nearest_place(lat, lon):
    global _PLACES
    if _PLACES is None:
        _PLACES = load_places()
    best, bd = None, 1e9
    for p in _PLACES:
        if abs(p["lat"] - lat) > 3 or abs(p["lon"] - lon) > 6:
            continue
        d = hav_km(lat, lon, p["lat"], p["lon"])
        if d < bd:
            best, bd = p, d
    return best


# ---------------------------------------------------------------- Hatch
HDATE = re.compile(r"^\s*(?:(\d{1,2})/)?(?:(\d{1,2})/)?(\d{1,4})\s*(.*)$")


def parse_hatch_date(s):
    s = (s or "").strip()
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        mo, d, y = map(int, m.groups())
        try:
            return y, mo, d, dt.date(y, mo, d).isoformat(), "day"
        except ValueError:
            return y, mo, None, None, "month"
    m = re.match(r"^(\d{1,2})/(\d{4})", s)
    if m:
        mo, y = map(int, m.groups())
        return y, mo, None, None, "month"
    m = re.match(r"^(\d{4})", s)
    if m:
        return int(m.group(1)), None, None, None, "year"
    return None, None, None, None, "none"


def load_hatch():
    L = json.load(open(os.path.join(UFO_DATA, "hatch_udb.json"), encoding="utf-8-sig"))["Hatch_UDB_Timeline"]
    out = []
    for x in L:
        kv = x.get("key_vals", {})
        y, mo, d, iso, prec = parse_hatch_date(x.get("date"))
        if "?" in (x.get("date") or "") or "approx" in (x.get("date") or ""):
            prec = prec + "?"
        try:
            lat, lon = map(float, kv.get("LatLong", "").split())
        except ValueError:
            lat = lon = None
        c = kv.get("Country", "?")
        grp = ("SU" if c in SU_COUNTRIES_HATCH else "CN" if c in CN_COUNTRIES_HATCH else
               "ARAB" if c in ARAB_COUNTRIES_HATCH else "SASIA" if c in SASIA_COUNTRIES_HATCH else
               "US" if c == "USA" else "CA" if c == "Canada" else "FR" if c == "France" else "OTHER")
        out.append(dict(
            uid=x.get("source_id"), catalog="HATCH", year=y, month=mo, day=d, date=iso, prec=prec,
            time=x.get("time"), place=x.get("location"), country=c, group=grp, lat=lat, lon=lon,
            text_en=x.get("desc"), hatch_desc=kv.get("HatchDesc"), attrs=[a.split(":")[0] for a in x.get("attributes", [])],
            strangeness=kv.get("Strangeness"), credibility=kv.get("Credibility"), ref=x.get("ref"),
        ))
    return out


# ---------------------------------------------------------------- NUFORC (US day counts)
def load_nuforc():
    d = json.load(gzip.open(os.path.join(ROOT, "evidence_vault", "06_NUFORC_MODERN_ARM", "nuforc_unified.json.gz"), "rt"))
    L = d[list(d)[0]] if isinstance(d, dict) else d
    out = []
    for x in L:
        if x.get("prec") != "day" or not x.get("year"):
            continue
        try:
            iso = dt.date(x["year"], x["month"], x["day"]).isoformat()
        except (ValueError, TypeError):
            continue
        out.append(dict(uid=x["uid"], date=iso, country=x.get("country"), lat=x.get("lat"), lon=x.get("lon"),
                        location=x.get("location"), shape=(x.get("kv") or {}).get("Shape") or x.get("etype"),
                        text=x.get("desc") or ""))
    return out


# ---------------------------------------------------------------- GEIPAN
def load_geipan():
    L = json.load(open(os.path.join(ROOT, "data", "raw", "geipan", "geipan_cases.json")))
    out = []
    for x in L:
        s = x.get("Observation date") or ""
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s)
        iso = None
        if m:
            d, mo, y = map(int, m.groups())
            try:
                iso = dt.date(y, mo, d).isoformat()
            except ValueError:
                iso = None
        out.append(dict(uid=x["ID Etude de Cas"], date=iso, cls=x.get("Classification"),
                        ident=x.get("Identification") or "", phen=x.get("Phenomenon") or "",
                        lat=x.get("Latitude"), lon=x.get("Longitude")))
    return out


# ---------------------------------------------------------------- launches
SITE_GROUP = {
    "PLMSC": "SU_PLESETSK", "TYMSC": "SU_BAIKONUR", "KYMSC": "SU_KAPUSTIN", "SVOBO": "RU_SVOBODNY",
    "VOSTO": "RU_VOSTOCHNY", "DLS": "SU_DOMBAROVSKY",
    "AFETR": "US_CANAVERAL", "AFWTR": "US_VANDENBERG", "WLPIS": "US_WALLOPS", "KSCUT": "US_KSC",
    "JSC": "CN_JIUQUAN", "TAISC": "CN_TAIYUAN", "XICLF": "CN_XICHANG", "WSC": "CN_WENCHANG",
    "FRGUI": "FR_KOUROU", "SRILR": "IN_SRIHARIKOTA",
}
SITE_COORD = {  # launch-site coordinates (public, approximate to ~10 km)
    "SU_PLESETSK": (62.93, 40.58), "SU_BAIKONUR": (45.92, 63.34), "SU_KAPUSTIN": (48.57, 46.25),
    "US_CANAVERAL": (28.49, -80.58), "US_VANDENBERG": (34.73, -120.57),
    "CN_JIUQUAN": (40.96, 100.29), "CN_TAIYUAN": (38.85, 111.61), "CN_XICHANG": (28.25, 102.03),
}


def load_launches():
    """One row per orbital launch (international designator YYYY-NNN), with site group and UTC date."""
    seen = {}
    with open(os.path.join(RAW, "satcat", "satcat.csv")) as f:
        for r in csv.DictReader(f):
            oid = r["OBJECT_ID"][:8]
            if not re.match(r"\d{4}-\d{3}", oid):
                continue
            if oid not in seen:
                seen[oid] = dict(launch=oid, date=r["LAUNCH_DATE"], site=r["LAUNCH_SITE"],
                                 group=SITE_GROUP.get(r["LAUNCH_SITE"], "OTHER:" + r["LAUNCH_SITE"]),
                                 owner=r["OWNER"], name=r["OBJECT_NAME"])
            elif r["OBJECT_TYPE"] == "PAY" and "R/B" in seen[oid]["name"]:
                seen[oid]["name"] = r["OBJECT_NAME"]
    return sorted(seen.values(), key=lambda x: x["date"])


# ---------------------------------------------------------------- nuclear sites
def load_reactors():
    out = []
    with open(os.path.join(RAW, "ne", "gnd_npp.csv")) as f:
        for r in csv.DictReader(f):
            try:
                lat, lon = float(r["Latitude"]), float(r["Longitude"])
            except ValueError:
                continue
            out.append(dict(name=r["Name"], iso2=r["CountryCode"], lat=lat, lon=lon, status=r["Status"],
                            start=r["ConstructionStartAt"][:4], op_from=r["OperationalFrom"][:4],
                            op_to=r["OperationalTo"][:4], kind="reactor"))
    return out


def load_tests():
    L = json.load(open(os.path.join(UFO_DATA, "nuclear_tests.json"), encoding="utf-8-sig"))
    L = L[list(L)[0]] if isinstance(L, dict) else L
    out = []
    for x in L:
        kv = x.get("key_vals", {})
        try:
            lat, lon = map(float, kv.get("LatLong", "").split())
        except ValueError:
            continue
        y, mo, d, iso, prec = parse_hatch_date(x.get("date"))
        out.append(dict(name=kv.get("NukeName"), country=kv.get("NukeCountry"), lat=lat, lon=lon,
                        date=iso, year=y, kind="test"))
    return out


if __name__ == "__main__":
    ru = load_ru_native()
    c = collections.Counter(r["region"] for r in ru)
    print("RU_NATIVE", len(ru), dict(c), "day-dated", sum(1 for r in ru if r["prec"] == "day"),
          "geocoded", sum(1 for r in ru if r["lat"] is not None))
    h = load_hatch()
    print("HATCH", len(h), collections.Counter(x["group"] for x in h))
    la = load_launches()
    print("LAUNCHES", len(la), collections.Counter(x["group"] for x in la).most_common(12))
