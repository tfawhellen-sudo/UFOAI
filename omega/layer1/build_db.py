"""Layer 1 bilingual database (SQLite + CSV) for the polyglot drill.

Tables
  sources  every corpus or document Layer 1 used, with host, identifier and how it was read
  events   dated reports from non-English sources:
             RU_CH       Chernobrov / Kosmopoisk chronicle (Russian original; English gist for
                         the 419 ex-USSR entries, machine translation, unreviewed)
             PLATOV2000  episodes named by Platov & Sokolov (2000), the Soviet state programme's
                         own summary, with the programme's explanation
             JPRS77236   dated cases of the 1980 Ziran Zazhi survey of Chinese sightings
                         (FBIS/JPRS English translation, 1981; Chinese original not on file)
  links    event -> Hatch entry and event -> event links (day offset, distance)
  lexicon  UAP vocabulary in Russian, Chinese, Arabic and Sanskrit, with origin notes and counts
           in the corpora on disk
  claims   the Abyss Protocol's Layer 1 claims, each with a verdict and the evidence

Every derived field is computed here from files on disk; nothing is typed in by hand except
the PLATOV2000 and JPRS77236 rows (transcribed from the named documents) and the sources,
lexicon notes and claims tables. Run:  python3 -I omega/layer1/build_db.py
"""
import csv
import datetime as dt
import glob
import json
import os
import re
import sqlite3
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalogs as C  # noqa: E402
import tests_l1 as T  # noqa: E402

DB_DIR = os.path.join(C.ROOT, "evidence_vault", "13_POLYGLOT_LAYER1", "db")
TR_DIR = os.path.join(DB_DIR, "tr_parts")
# The committed database carries a 300-character excerpt of each Russian entry (the chronicle is a
# copyrighted 2002 compilation; full texts would republish ~90% of it). Derived fields (shape, plume,
# flags) are computed from the full text at build time. For a local full-text copy run with
# L1_EXCERPT=0 L1_DB_OUT=data/raw/layer1/db_full (that folder is gitignored).
EXCERPT = int(os.environ.get("L1_EXCERPT", "300"))
OUT_DIR = os.path.join(C.ROOT, os.environ["L1_DB_OUT"]) if os.environ.get("L1_DB_OUT") else DB_DIR
SU_LAUNCH = {"SU_PLESETSK", "SU_BAIKONUR", "SU_KAPUSTIN", "SU_DOMBAROVSKY", "RU_SVOBODNY", "RU_VOSTOCHNY"}
CN_LAUNCH = {"CN_JIUQUAN", "CN_TAIYUAN", "CN_XICHANG", "CN_WENCHANG"}
TRANSLATOR_RU = "Claude (machine translation of the first ~160 characters, unreviewed)"

SOURCES = [
    dict(source_id="RU_CH", title="V. Chernobrov, 'Khroniki vizitov NLO' (Kosmopoisk chronicle, state 2.09.2002)",
         lang="ru", kind="catalogue (non-state, compiled by an ufological association)", host="archive.org",
         identifier="hroniki_vizitov_nlo", access="/stream/<id>/<file>_djvu.txt OCR text",
         notes="624 parsed entries, 419 ex-USSR; compiler is himself a witness in some entries (flag)."),
    dict(source_id="PLATOV2000", title="Yu.V. Platov, B.A. Sokolov, 'History of the state UFO research in the USSR', "
         "Herald of the Russian Academy of Sciences 70(6), 2000 (Vestnik RAN 70(6):507-515)",
         lang="en (translation of ru)", kind="state programme's own summary", host="noufors.com",
         identifier="https://noufors.com/Documents/Platov.pdf", access="web-fetch (container proxy blocks host)",
         notes="Programme 1978-1990, Defence Ministry + Academy of Sciences; ~3,000 communications, >300 anomalous events, "
               ">90% rockets plus balloons, balloons 10-12%."),
    dict(source_id="GINDILIS_MEMOIR", title="L.M. Gindilis, memoir pages on the Academy working group and Petrozavodsk 1977",
         lang="ru", kind="participant memoir", host="astronet.ru", identifier="https://www.astronet.ru/db/msg/1169491/1_6.htm; /2_1.htm",
         access="web-fetch", notes="Several dozen reports by end of 1977; meteorological radar data on other dates."),
    dict(source_id="GINDILIS1979", title="L.M. Gindilis, D.A. Men'kov, I.G. Petrovskaya, 'Observations of anomalous atmospheric "
         "phenomena in the USSR: statistical analysis' (Academy of Sciences preprint Pr-473, 1979)",
         lang="ru (NASA TM-75665 English translation)", kind="academic statistical study", host="NTRS / CUFOS",
         identifier="NASA-TM-75665; NASA-TM-75761", access="record only; full text not reached (CUFOS PDF 4xx)",
         notes="Existence verified from the NASA record; counts not read."),
    dict(source_id="OLEKSIUK2013", title="R.P. Oleksiuk, 'Nekotorye itogi issledovanii NLO v SSSR i SNG', Kosmichna nauka i "
         "tekhnolohiya 19(1):78-79, 2013 (letters section)", lang="ru", kind="secondary retrospective (academic journal letter)",
         host="mao.kiev.ua", identifier="https://www.mao.kiev.ua/biblio/jscans/knit/2013-19/knit-2013-19-1-10.pdf",
         access="web-fetch", notes="Names the topics 'Setka MO' and 'Setka AN'; cites Platov & Sokolov 2000."),
    dict(source_id="JPRS77236", title="JPRS 77236, China Report: Science and Technology No. 79 (26 Jan 1981): Cha Leping & "
         "Lin Hongjing, 'Preliminary survey of unidentified aerial phenomena in China', Ziran Zazhi 1980 No. 9 pp. 685-686",
         lang="en (FBIS translation of zh)", kind="academic survey (Wuhan University)", host="CIA CREST (cia.gov reading room)",
         identifier="CREST doc 0005516652 (C00174701)", access="CREST OCR text on disk", notes="~100 accounts from 15 provinces; "
         "~80% disc/globe 'frequently accompanied by a white smoke cloud'."),
    dict(source_id="XINHUA_CURO", title="Xinhua English wire, 7 December (FBIS transcript): CURO chairman Wang Changting",
         lang="en", kind="state media", host="CIA CREST", identifier="CREST text on disk (see src/cia_ufo_collection_titles.txt)",
         access="CREST OCR", notes=">5,000 mainland sightings; CURO set up 1978, member of the China Association for "
               "Science and Technology."),
    dict(source_id="ZH_BOOKS", title="Chinese-language UFO books and Hong Kong newspapers on archive.org (5 items)",
         lang="zh", kind="popular books / newspapers", host="archive.org",
         identifier="04_20240511_20240511; 20240629_20240629_1319; 20250509_20250509_1555; NPWK19631216; NPKSE19580818",
         access="OCR text", notes="Vertical traditional-script OCR is mostly unusable; counted for vocabulary only."),
    dict(source_id="AR_BOOK", title="Raji Enayat, 'Sirr al-atbaq al-ta'ira' (Egypt), two archive.org copies",
         lang="ar", kind="popular book", host="archive.org", identifier="BBib-Alex-12868; mind-library-siri-alatbaq-alttayira",
         access="OCR text", notes="Compilation of Western cases; no native Arab-world case found."),
    dict(source_id="VS1973", title="Vyamaanika Shastra, Sanskrit version (Mar 1973 edition)", lang="sa", kind="text claimed ancient",
         host="archive.org", identifier="sanskrit-version-vyamaanika-shastra-mar-1973", access="OCR text", notes=""),
    dict(source_id="IISC1974", title="H.S. Mukunda et al., 'A critical study of the work Vymanika Shastra', Scientific Opinion "
         "1974, pp. 5-12 (Indian Institute of Science)", lang="en", kind="academic critique", host="cgpl.iisc.ac.in",
         identifier="https://cgpl.iisc.ac.in/oldwebcontent/site/Portals/0/Publications/ReferedJournal/ACriticalStudyOfTheWorkVaimanikaShastra.pdf",
         access="web-fetch", notes="Composed 1900-1922 by Pandit Subbaraya Shastry; 'cannot be dated earlier than 1904'; "
               "none of the craft could fly."),
    dict(source_id="RU_MAGS", title="Soviet popular-science magazine runs on archive.org (Znanie-sila, Nauka i zhizn', Khimiya i "
         "zhizn', Izobretatel' i ratsionalizator, Vokrug sveta, Ogonyok, Tekhnika-molodezhi, Yunyi tekhnik, Zemlya i Vselennaya) "
         "plus ufological periodicals", lang="ru", kind="periodicals", host="archive.org",
         identifier="see src/ru_inventory.json (384 items)", access="OCR text, keyword windows",
         notes="Zemlya i Vselennaya: only 2 issues on archive.org (1972-05, 1978 No.4), 0 UFO keyword hits."),
    dict(source_id="HATCH", title="Larry Hatch *U* database (English summaries, compiled ~1994-2002)", lang="en",
         kind="catalogue (English-language secondary)", host="tfawhellen-sudo/ufo_data", identifier="bin/hatch_udb.json",
         access="repo file", notes="Link target for cross-catalogue matches."),
    dict(source_id="SATCAT", title="CelesTrak SATCAT snapshot (to end June 2025)", lang="en", kind="launch catalogue",
         host="archive.org", identifier="satcat_2025_07_10_cutToEndJune", access="CSV",
         notes="Orbital launches only; suborbital missile tests are absent."),
    dict(source_id="NUCLEAR", title="GeoNuclearData power reactors + ufo_data nuclear_tests.json + Natural Earth weapons-city "
         "matches", lang="en", kind="site lists", host="raw.githubusercontent.com / ufo_data",
         identifier="cristianst85/GeoNuclearData; ufo_data/bin/nuclear_tests.json", access="CSV/JSON",
         notes="Closed Soviet weapons cities are mostly absent from Natural Earth (3 of 14 found)."),
]

PLATOV_EVENTS = [
    # (date, prec, place, lat, lon, text_en, explanation, launch name to look up in SATCAT)
    ("1977-09-20", "day", "Petrozavodsk, Karelia (and wide area; photographed at Sodankyla, Finland)", 61.79, 34.36,
     "'At about 4 a.m., a huge star flared up suddenly on the dark sky', spreading 'in the form of an enormous jellyfish'; "
     "10-12 minutes (Izvestiya 23.9.1977, quoted).", "launch: Kosmos-955 from Plesetsk; footnote adds a failed ballistic "
     "missile test in the same region at practically the same time", "COSMOS 955"),
    ("1980-06-14", "day", "European Russia (then South America about an hour later)", None, None,
     "'Dirigible-shaped object' seen over a large part of European Russia.", "launch: Kosmos-1188 from Plesetsk", "COSMOS 1188"),
    ("1981-05-15", "day", "USSR (not specified)", None, None, "Launch-type phenomena observed.", "launch: Meteor-2 satellite",
     "METEOR 2"),
    ("1982-08-28", "day", "Plesetsk region (photo)", 62.93, 40.58,
     "'The streams of combustion products issuing from the engine form a cloud resembling a jellyfish' (figure caption gives 27 Aug).",
     "launch: Molniya-1 from Plesetsk (SATCAT lists the 27 Aug Plesetsk Molniya as MOLNIYA 3-19)", "MOLNIYA"),
    ("1984-07-03", "day", "USSR (not specified)", None, None, "Launch-type phenomena observed.", "launch: Kosmos-1581",
     "COSMOS 1581"),
    ("1982-06-03", "day", "near Chita, east of Lake Baikal (border with China)", 52.03, 113.50,
     "Border-patrol aircraft detected 'an unusual object of spherical shape' at about 17 km.",
     "balloon: sounding balloon from the nearby weather station (last telemetered altitude 16 km)", None),
    ("1982-09-13", "day", "Gulf of Anadyr, Chukotka", 64.5, 178.0, "Similar spherical-object episode.",
     "balloon (telemetry failed at launch)", None),
    ("1983-10-05", "day", "Khmelnitsky, Ukraine (strategic rocket forces division)", 49.42, 26.98,
     "Object 'whose shape resembled that of a dirigible' (source also gives 5 Oct 1982 for the flares).",
     "flares parachuted from aircraft at ~10 km over a 26th Air Army range in Polesye, ~400 km away", None),
    ("1984", "range 1984-1987", "Borisoglebsk, Voronezh oblast", 51.37, 42.08,
     "Several aircraft accidents with unknown objects seen on radar and visually.",
     "unexplained: 'these events will have to be regarded as unidentified'", None),
    ("1977", "year", "Baltic republics", None, None, "Triangular object caused 'a real panic among eyewitnesses' (filmed).",
     "balloon: high-altitude tetrahedral balloon", None),
]

JPRS_EVENTS = [
    # (date, time, place, lat, lon, text_en (short JPRS excerpts and paraphrase))
    ("1978-11-13", "21:00", "Wuhan University, Hubei", 30.54, 114.36,
     "Students saw in the west, 40 deg up, a round object ~1 deg across, orange-red, slightly dimmer than a full Moon; its top "
     "'covered with a slowly curling cloud mass'; flew slowly west by north for ~10 min. More than 10 similar reports from "
     "nine other provinces; two describe the object flying into a cloud and lighting it up."),
    ("1976-09-09", "18:00", "Yichun, Jiangxi", 27.80, 114.38,
     "Chemical-plant staff saw a silvery object 'shaped like a pair of cymbals', rotating, that 'constantly spurted out a "
     "silvery vapor', ~2,000 m up, flying east to north-west for 5 min; many street witnesses."),
    ("1979-09-09", "21:30", "Dayuan farm, Jianli county, Hubei", 29.82, 112.88,
     "Two technicians saw a round object emitting red-yellow light, front circled with blue, with an 'awl-shaped tail' four "
     "times the head; NE to SW, then a right-angle turn; ~1 min."),
    ("1979-09-09", "21:40", "Hunan Diesel Engine Plant, Zhangmuqiao, Changde county, Hunan", 29.03, 111.70,
     "Outdoor-film audience saw an oval object brighter than the full Moon, orange-red head and a bright tail 'which seemed "
     "to be emitting a gas', silent, north to south-west, 3 min. Authors: possibly the same object as at Jianli, 145 km away."),
    ("1978-10-23", "20:40", "a certain airfield, Gansu (Hatch: Lintiao AB)", None, None,
     "Air-force pilots and ground crew at an outdoor film saw a huge long object with two bright lights at front and tail, "
     "east to west, 30-35 deg apparent length, 'covered half the sky'."),
    ("1977-07-26", "23:00", "Chengdu, Sichuan", 30.66, 104.07,
     "Yunnan Observatory staff member saw a 'spiral nebula' type object ~5 deg across; many people saw it for 180 km north "
     "and south at the same time; similar objects seen in Chengdu and Anhui."),
]

LEXICON = [
    # lang, term, translit, gloss, origin, regex
    ("ru", "НЛО", "NLO", "UFO (неопознанный летающий объект)", "calque of English 'UFO'", r"\bНЛО\b"),
    ("ru", "летающая тарелка", "letayushchaya tarelka", "flying saucer", "calque of English 'flying saucer' (1947)",
     r"летающ\w*\s+тарел\w*"),
    ("ru", "тарелка", "tarelka", "plate, saucer", "short form of the calque", r"тарел\w*"),
    ("ru", "АЯ / аномальные явления", "AYa", "anomalous phenomena", "official Soviet Academy / Defence Ministry term (programme 1978-1990)",
     r"\bАЯ\b|аномальн\w*\s+(?:атмосферн\w*\s+)?явлени\w*"),
    ("ru", "шар", "shar", "ball, sphere", "native everyday word; the commonest primary shape in the Russian chronicle",
     r"\bшар\w*"),
    ("ru", "медуза", "meduza", "jellyfish", "press image from Petrozavodsk 1977 (Izvestiya); Platov uses it for a Plesetsk launch cloud",
     r"медуз\w*"),
    ("ru", "серп / полумесяц", "serp / polumesyats", "crescent / sickle", "native; typical description of a launch plume",
     r"\bсерп\w*|полумесяц\w*"),
    ("ru", "сигара", "sigara", "cigar", "shared with English usage", r"сигар\w*"),
    ("ru", "трехзвездник", "trekhzvezdnik", "'three-star' (triangle of three lights)", "Kosmopoisk coinage, 1980s-2000s",
     r"тр[её]хзв[её]здн\w*"),
    ("ru", "гантель", "gantel'", "dumbbell", "Molebka ('M-triangle') expedition term", r"гантел\w*"),
    ("ru", "аномальная зона", "anomal'naya zona", "anomalous zone", "Russian-specific concept (Molebka, Medveditskaya ridge)",
     r"аномальн\w*\s+зон\w*"),
    ("ru", "гуманоид", "gumanoid", "humanoid", "loan", r"гуманоид\w*"),
    ("ru", "инопланетянин", "inoplanetyanin", "alien, 'other-planet person'", "native compound", r"инопланет\w*"),
    ("ru", "контактер", "kontakter", "contactee", "loan + Russian suffix", r"контакт[её]р\w*"),
    ("zh", "飛碟 / 飞碟", "feidie", "flying saucer ('flying dish')", "calque of English 'flying saucer'", r"飛碟|飞碟"),
    ("zh", "不明飛行物 / 不明飞行物", "buming feixingwu", "unidentified flying object", "calque of English 'UFO'",
     r"不明飛行物|不明飞行物"),
    ("zh", "幽浮", "youfu", "UFO (phonetic; 'faint floating')", "phonetic loan of 'UFO', Taiwan usage", r"幽浮"),
    ("zh", "外星人", "waixingren", "alien ('outer-star person')", "native compound", r"外星人"),
    ("zh", "宇宙人", "yuzhouren", "space people", "Japanese-influenced compound (book title)", r"宇宙人"),
    ("ar", "الأطباق الطائرة", "al-atbaq al-ta'ira", "the flying plates (saucers)", "calque of English 'flying saucers'",
     r"[اأإآ]?ل?[اأإآ]طباق\s+[اأ]?ل?طائر[ةه]"),
    ("ar", "أطباق (any context)", "atbaq", "plates, saucers (plural)", "everyday word used for the calque", r"[اأإآ]?ل?[اأإآ]طباق"),
    ("ar", "طبق طائر", "tabaq ta'ir", "flying plate (saucer), singular", "calque", r"طبق\s+طائر"),
    ("ar", "الأجسام الطائرة المجهولة", "al-ajsam al-ta'ira al-majhula", "unknown flying objects", "calque of 'UFO'",
     r"[اأ]ل[اأ]?جسام\s+[اأ]?ل?طائر[ةه]\s+[اأ]?ل?مجهول[ةه]"),
    ("ar", "مخلوقات / كائنات فضائية", "makhluqat / ka'inat fada'iya", "space creatures / beings", "native compound",
     r"(?:مخلوقات|كائنات)\s+فضائي[ةه]"),
    ("ar", "أمريكا / أمريكي", "Amrika", "America / American (stem)", "place name: where the book's cases come from",
     r"[أاإ]مري[كک]"),
    ("ar", "روسيا / السوفيت", "Rusiya / al-Sufyat", "Russia / Soviet", "place name", r"روسيا|السوفي[يت]"),
    ("ar", "مصر", "Misr", "Egypt", "place name (native-case check)", r"مصر"),
    ("ar", "الجزائر", "al-Jaza'ir", "Algeria", "place name (native-case check)", r"الجزائر"),
    ("sa", "विमान", "vimana", "aerial car; also temple tower", "native Sanskrit; epics use it without mechanism", r"विमान"),
    ("sa", "पुष्पक", "pushpaka", "Pushpaka, the aerial car of the Ramayana", "epic proper name", r"पुष्पक"),
]

CLAIMS = [
    ("C01", "Project 'Setka': a nationwide UAP reporting network", "1.1", "VERIFIED (name and network)",
     "A state programme ran 1978-1990 with a Defence Ministry topic and an Academy of Sciences topic; a General Staff "
     "directive of January 1980 told all military units to report sightings. Platov & Sokolov's English text calls the two "
     "topics 'DM Network' and 'AS Network'; Oleksiuk (2013) gives the Russian names 'Setka MO' and 'Setka AN' (setka = "
     "network). Correction to the earlier note that the name was absent: it is there, translated.",
     "PLATOV2000; OLEKSIUK2013"),
    ("C02", "The 'Blue Book' equivalent: Soviet military UAP files", "1.1", "NOT FOUND (as released files)",
     "The Defence Ministry branch existed (main executor a central military research institute near Moscow). No released "
     "military case file was found on archive.org, CREST or the hosts reachable from here; the programme's own summary is "
     "the best open source.", "PLATOV2000; archive.org searches"),
    ("C03", "Soviet scientists published on UAP in Priroda and Zemlya i Vselennaya", "1.1", "NOT VERIFIED",
     "archive.org holds 2 Zemlya i Vselennaya issues (1972-05, 1978 No.4) with 0 UFO keyword hits and no Soviet-era "
     "Priroda issues; priroda.ras.ru, cyberleninka.ru and elibrary.ru are unreachable from this container; Priroda 2015 "
     "No.8 has no UFO article; the academic-journal piece found (Oleksiuk 2013) cites only Vestnik RAN 2000. The Soviet "
     "academic output that is verified is the Gindilis et al. 1979 preprint (NASA TM-75665).",
     "RU_MAGS; OLEKSIUK2013; GINDILIS1979"),
    ("C04", "Soviet pilots, radar operators and cosmonauts reported UAP", "1.1", "PARTLY (retold, not documented)",
     "The native chronicle has aircrew, radar and missile-range entries (counts in the report), all as retellings without "
     "primary documents; no cosmonaut testimony was found in it. The 1948-49 Apraksin chases have no documentary trace here.",
     "RU_CH"),
    ("C05", "AAWSAP DIRDs reference Soviet 'Thread-3' technology assessments", "1.1", "FALSE",
     "0 hits for 'Thread-3'/'Thread 3' in 37 DIRDs, 286 PURSUE server files and the PURSUE OCR; DIRD mentions of the "
     "Soviet Union are unrelated to UAP.", "DIRD/PURSUE text search (session 6 files)"),
    ("C06", "The PLA has its own UAP research program", "1.2", "NOT SUPPORTED",
     "Open sources show a civilian association, CURO (set up 1978, member of the China Association for Science and "
     "Technology), and a 1980 Wuhan University survey. Nothing in CREST/JPRS or Xinhua texts on disk describes a PLA "
     "programme.", "XINHUA_CURO; JPRS77236"),
    ("C07", "China is the only other superpower with a systematic UAP research program", "1.2", "NOT SUPPORTED",
     "See C06; the Chinese effort found is civilian and amateur-academic.", "XINHUA_CURO; JPRS77236"),
    ("C08", "Arabic-language UAP reports are completely absent from the English-language corpus", "1.3",
     "FALSE as stated", "Hatch has entries for Arab-world countries (count in the report). The most-reprinted Egyptian book "
     "is a compilation of Western cases with no native case.", "HATCH; AR_BOOK"),
    ("C09", "The deep term search found extensive discussion of vimana in the DIRD literature", "1.4", "FALSE",
     "0 hits for vimana/Sanskrit/Mahabharata in DIRDs and PURSUE; one 'Ramayana' mention in the COMETA report file.",
     "DIRD/PURSUE text search"),
    ("C10", "Sanskrit epics describe aerial vehicles that parallel modern UAP descriptions", "1.4", "PARTLY",
     "The epics use vimana (e.g. Pushpaka) with no flight mechanism. The only 'technical' vimana text, the Vymanika "
     "Shastra, was composed 1900-1922 (IISc 1974: 'cannot be dated earlier than 1904') and none of its craft could fly.",
     "IISC1974; VS1973"),
    ("C11", "Simultaneous sightings: the same event in Russian and US databases", "1.1", "TESTED: NULL",
     "Russian native vs NUFORC same-day rate ratio 1.01; vs GEIPAN 1.07 (date-shift null); positive control Hatch US vs "
     "NUFORC same day within 100 km gives 5.6.", "T1_simultaneity.json"),
    ("C12", "Unique Soviet reports exist (events only in the Russian corpus)", "1.1", "TESTED: YES",
     "Over 90% of each catalogue's Soviet events have no counterpart in the other (date +-1 day, <=800 km).",
     "T2_coverage.json"),
    ("C13", "Soviet and American observers use different descriptive frameworks", "1.1", "TESTED: YES, WITH CAVEAT",
     "Disc is 26% of first shapes in English Hatch SU entries vs 9% in the Russian chronicle (p=0.0002); plume words are "
     "Soviet-specific. But Hatch US vs NUFORC differ by TVD 0.25, so compiler effects are as large as language effects.",
     "T3b_primary_shape.json"),
    ("C14", "Soviet UAP cluster near Soviet nuclear facilities", "1.1", "TESTED: WEAK, NOT ROBUST",
     "Russian chronicle: no excess within 30 km. Hatch SU declustered: reactors 4 vs 1.0 expected at 30 km (p=0.018); "
     "the Natural Earth site list misses most closed weapons cities.", "T4_nuclear.json"),
    ("C15", "Platov & Sokolov: over 90% of anomalous phenomena were rocket effects plus balloons", "(context)",
     "SUPPORTED ON AN INDEPENDENT CATALOGUE", "Plume-worded Russian reports fall on Soviet launch days (UTC) more than "
     "date-shifted copies do (RR 1.47, p=0.029; within 1,500 km of Plesetsk RR 1.80, p=0.026); non-plume reports do not "
     "(RR 1.08). Window W0 was not pre-registered, so this is suggestive.", "T5_launch_lock.json"),
    ("C16", "Gindilis Academy report exists", "(context)", "VERIFIED (record)",
     "NASA TM-75665 (translation of Pr-473, 1979) and TM-75761 records found; full text not reached.", "GINDILIS1979"),
]


def dnum(iso):
    return (dt.date.fromisoformat(iso) - dt.date(1900, 1, 1)).days


def load_gists():
    out = {}
    for p in sorted(glob.glob(os.path.join(TR_DIR, "batch*.json"))):
        out.update(json.load(open(p, encoding="utf-8")))
    return out


COMPILER_WITNESS = re.compile(r"в том числе (?:и )?В\.?\s?Чернобров|\(В\.?\s?Чернобров\)|Автор обзора[^\]]{0,80}наблюдал|"
                              r"Кроме автора обзора", re.I)
CREW = re.compile(r"летчик|пилот|экипаж|командир корабля|штурман", re.I)
RADAR = re.compile(r"радар|локатор|РЛС", re.I)
COSMONAUT = re.compile(r"космонавт", re.I)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    gists = load_gists()
    ru = C.load_ru_native()
    hatch = C.load_hatch()
    launches = C.load_launches()
    sites, _weapons = T.nuclear_sites()

    by_day = {}
    for x in launches:
        by_day.setdefault(x["date"], []).append(x)
    h_by_day = {}
    for x in hatch:
        if x["prec"].startswith("day") and x["date"]:
            h_by_day.setdefault(x["date"], []).append(x)

    def launches_near(iso, groups):
        d = dt.date.fromisoformat(iso)
        w0 = [x for x in by_day.get(iso, []) if x["group"] in groups]
        wm1 = [x for x in by_day.get((d - dt.timedelta(days=1)).isoformat(), []) if x["group"] in groups]
        return w0, wm1

    def nearest_site(lat, lon, year, g):
        best = None
        for s in sites[g]:
            if s["year"] <= year:
                km = C.hav_km(lat, lon, s["lat"], s["lon"])
                if best is None or km < best[0]:
                    nm = s["name"] if s["kind"] != "test" else "test site %.1fN %.1fE (first test %d)" % (s["lat"], s["lon"], s["year"])
                    best = (km, nm, s["kind"])
        return best

    def hatch_links(iso, lat, lon, groups, max_km=800):
        d = dt.date.fromisoformat(iso)
        out = []
        for k in (-1, 0, 1):
            for x in h_by_day.get((d + dt.timedelta(days=k)).isoformat(), []):
                if x["group"] not in groups:
                    continue
                km = None
                if lat is not None and x["lat"] is not None:
                    km = C.hav_km(lat, lon, x["lat"], x["lon"])
                    if km > max_km:
                        continue
                out.append((x["uid"], k, km))
        return out

    events, links = [], []
    first_text = {}
    for r in ru:
        key = (r["text_ru"] or "")[:200]
        first_text.setdefault(key, r["uid"])
    for r in ru:
        cid = r["uid"].split("#")[-1]
        su = r["region"] in ("SU", "SU?")
        flags = []
        gist = gists.get(cid) if su else None
        if gist and "[Parser merge" in gist:
            flags.append("parser_merge")
        if COMPILER_WITNESS.search(r["text_ru"] or ""):
            flags.append("compiler_witness")
        dup = first_text.get((r["text_ru"] or "")[:200])
        if dup and dup != r["uid"]:
            flags.append("duplicate_of:" + dup)
        if CREW.search(r["text_ru"] or ""):
            flags.append("aircrew")
        if RADAR.search(r["text_ru"] or ""):
            flags.append("radar")
        if COSMONAUT.search(r["text_ru"] or ""):
            flags.append("cosmonaut_word")
        ev = dict(uid=r["uid"], catalogue="RU_CH", lang_orig="ru", date=r["date"], date_prec=r["prec"],
                  time_local=r["time_ru"], place_orig=r["place_ru"], countries=",".join(r["countries"]), region=r["region"],
                  lat=r["lat"], lon=r["lon"], geo_name=r["geo_name"], geo_how=r["geo_how"],
                  text_orig=(r["text_ru"] or "")[:EXCERPT] if EXCERPT else r["text_ru"], text_orig_chars=len(r["text_ru"] or ""),
                  src_offset=r["src_offset"],
                  text_en=gist, translator=TRANSLATOR_RU if gist else None,
                  primary_shape=T.primary_shape(r["text_ru"], "ru"), plume_flag=int(bool(T.PLUME_RU.search(r["text_ru"] or ""))),
                  explanation=None, launch_utc_same_day=None, launch_utc_prev_day=None, nuclear_km=None, nuclear_site=None,
                  hatch_links=0, flags=";".join(flags) or None, source_id="RU_CH")
        if r["prec"] == "day" and su:
            w0, wm1 = launches_near(r["date"], SU_LAUNCH)
            ev["launch_utc_same_day"] = "; ".join("%s %s" % (x["group"], x["name"]) for x in w0) or None
            ev["launch_utc_prev_day"] = "; ".join("%s %s" % (x["group"], x["name"]) for x in wm1) or None
            hl = hatch_links(r["date"], r["lat"], r["lon"], {"SU"})
            ev["hatch_links"] = len(hl)
            for uid, k, km in hl:
                links.append(dict(uid=r["uid"], link_uid=uid, link_type="hatch:date±1" + ("&<=800km" if km is not None else "(no geo)"),
                                  dt_days=k, km=round(km, 1) if km is not None else None))
        if su and r["lat"] is not None and r["year"] and r["year"] >= 1946:
            ns = nearest_site(r["lat"], r["lon"], int(r["year"]), "SU")
            if ns:
                ev["nuclear_km"] = round(ns[0], 1)
                ev["nuclear_site"] = "%s (%s)" % (ns[1], ns[2])
        events.append(ev)

    ru_by_day = {}
    for e in events:
        if e["date_prec"] == "day":
            ru_by_day.setdefault(e["date"], []).append(e)
    for i, (date, prec, place, lat, lon, text, expl, lname) in enumerate(PLATOV_EVENTS, 1):
        uid = "PLATOV2000#%02d" % i
        satcat = None
        if lname:
            hits = [x for x in launches if x["name"].startswith(lname) and x["group"] in SU_LAUNCH
                    and abs(dnum(x["date"]) - dnum(date)) <= 1]
            satcat = "; ".join("%s %s %s" % (x["date"], x["group"], x["launch"]) for x in hits) or "NOT FOUND near date"
        ev = dict(uid=uid, catalogue="PLATOV2000", lang_orig="ru", date=date, date_prec=prec, time_local=None,
                  place_orig=place, countries="SU", region="SU", lat=lat, lon=lon, geo_name=None,
                  geo_how="hand (source place)" if lat is not None else None, text_orig=None, text_orig_chars=None,
                  src_offset=None, text_en=text,
                  translator="published English translation (Herald RAS)", primary_shape=None, plume_flag=None,
                  explanation=expl + ((" | SATCAT: " + satcat) if satcat else ""), launch_utc_same_day=None,
                  launch_utc_prev_day=None, nuclear_km=None, nuclear_site=None, hatch_links=0, flags=None, source_id="PLATOV2000")
        if prec == "day":
            hl = hatch_links(date, lat, lon, {"SU"}, max_km=3000)
            ev["hatch_links"] = len(hl)
            for luid, k, km in hl:
                links.append(dict(uid=uid, link_uid=luid, link_type="hatch:date±1" + ("&<=3000km" if km is not None else "(no geo)"),
                                  dt_days=k, km=round(km, 1) if km is not None else None))
            d = dt.date.fromisoformat(date)
            for k in (-1, 0, 1):
                for e in ru_by_day.get((d + dt.timedelta(days=k)).isoformat(), []):
                    if e["region"] in ("SU", "SU?"):
                        links.append(dict(uid=uid, link_uid=e["uid"], link_type="ru_ch:date±1", dt_days=k, km=None))
        events.append(ev)

    for i, (date, tm, place, lat, lon, text) in enumerate(JPRS_EVENTS, 1):
        uid = "JPRS77236#%02d" % i
        w0, wm1 = launches_near(date, SU_LAUNCH | CN_LAUNCH)
        ev = dict(uid=uid, catalogue="JPRS77236", lang_orig="zh", date=date, date_prec="day", time_local=tm,
                  place_orig=place, countries="CN", region="CN", lat=lat, lon=lon, geo_name=None,
                  geo_how="hand (county seat)" if lat is not None else None, text_orig=None, text_orig_chars=None,
                  src_offset=None, text_en=text,
                  translator="FBIS/JPRS (US government translation, 1981)", primary_shape=T.primary_shape(text, "en"),
                  plume_flag=int(bool(T.PLUME_EN.search(text) or re.search(r"vapou?r|smoke|gas", text, re.I))),
                  explanation=None,
                  launch_utc_same_day="; ".join("%s %s" % (x["group"], x["name"]) for x in w0) or None,
                  launch_utc_prev_day="; ".join("%s %s" % (x["group"], x["name"]) for x in wm1) or None,
                  nuclear_km=None, nuclear_site=None, hatch_links=0, flags=None, source_id="JPRS77236")
        hl = hatch_links(date, None, None, {"CN"})
        ev["hatch_links"] = len(hl)
        for luid, k, km in hl:
            links.append(dict(uid=uid, link_uid=luid, link_type="hatch:date±1 (CN)", dt_days=k, km=None))
        if lat is not None:
            ns = nearest_site(lat, lon, int(date[:4]), "CN")
            if ns:
                ev["nuclear_km"] = round(ns[0], 1)
                ev["nuclear_site"] = "%s (%s)" % (ns[1], ns[2])
        events.append(ev)

    # lexicon counts over the corpora on disk
    corp = {
        "ru": [("RU_CH chronicle", [os.path.join(C.RAW, "ru", "whole", "hroniki_vizitov_nlo__hroniki_vizitov_nlo_djvu.txt")]),
               ("RU ufological periodicals + books (whole texts)", sorted(glob.glob(os.path.join(C.RAW, "ru", "whole", "*.txt"))))],
        "zh": [("ZH books/newspapers (OCR)", [os.path.join(C.RAW, "other", f) for f in
                                             ("04_20240511_20240511.txt", "20240629_20240629_1319.txt", "20250509_20250509_1555.txt",
                                              "NPWK19631216.txt", "NPKSE19580818.txt")])],
        "ar": [("AR book copy 1 (BBib-Alex-12868)", [os.path.join(C.RAW, "other", "BBib-Alex-12868.txt")]),
               ("AR book copy 2 (mind-library)", [os.path.join(C.RAW, "other", "mind-library-siri-alatbaq-alttayira.txt")])],
        "sa": [("Vyamaanika Shastra 1973 (OCR)", [os.path.join(C.RAW, "other", "sanskrit-version-vyamaanika-shastra-mar-1973.txt")])],
    }
    text_cache = {}

    def read(p):
        if p not in text_cache:
            raw = open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""
            text_cache[p] = unicodedata.normalize("NFKC", raw)
        return text_cache[p]
    lex = []
    for lang, term, tr, gloss, origin, rx in LEXICON:
        counts = {}
        for cname, files in corp[lang]:
            counts[cname] = sum(len(re.findall(rx, read(p), re.I)) for p in files)
        lex.append(dict(lang=lang, term=term, translit=tr, gloss_en=gloss, origin=origin, regex=rx,
                        counts=json.dumps(counts, ensure_ascii=False)))

    src = [dict(s) for s in SOURCES]
    claims = [dict(claim_id=c[0], claim=c[1], protocol_task=c[2], verdict=c[3], evidence=c[4], sources=c[5]) for c in CLAIMS]

    # write SQLite + CSV
    dbp = os.path.join(OUT_DIR, "layer1_polyglot.sqlite")
    if os.path.exists(dbp):
        os.remove(dbp)
    con = sqlite3.connect(dbp)
    tables = dict(sources=src, events=events, links=links, lexicon=lex, claims=claims)
    for name, rows in tables.items():
        cols = list(rows[0].keys())
        con.execute("CREATE TABLE %s (%s)" % (name, ", ".join('"%s"' % c for c in cols)))
        con.executemany("INSERT INTO %s VALUES (%s)" % (name, ",".join("?" * len(cols))), [[r[c] for c in cols] for r in rows])
        with open(os.path.join(OUT_DIR, name + ".csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    con.commit()
    con.close()

    summary = dict(
        events={c: sum(1 for e in events if e["catalogue"] == c) for c in ("RU_CH", "PLATOV2000", "JPRS77236")},
        ru_su_with_english=sum(1 for e in events if e["catalogue"] == "RU_CH" and e["text_en"]),
        links=len(links),
        flags={f: sum(1 for e in events if e["flags"] and f in e["flags"]) for f in
               ("parser_merge", "compiler_witness", "duplicate_of", "aircrew", "radar", "cosmonaut_word")},
        platov=[(e["uid"], e["date"], e["explanation"][-60:], e["hatch_links"]) for e in events if e["catalogue"] == "PLATOV2000"],
        platov_to_ru=[(lk["uid"], lk["link_uid"], lk["dt_days"]) for lk in links if lk["link_type"] == "ru_ch:date±1"],
        jprs=[(e["uid"], e["date"], e["hatch_links"], e["launch_utc_same_day"], e["launch_utc_prev_day"], e["nuclear_km"])
              for e in events if e["catalogue"] == "JPRS77236"],
        lexicon=[(x["lang"], x["term"], x["counts"]) for x in lex],
    )
    json.dump(summary, open(os.path.join(OUT_DIR, "build_summary.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
