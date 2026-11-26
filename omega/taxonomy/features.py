"""UAP craft taxonomy - step 1: one harmonised feature coding across three report sets.

Sources (all already in the project, nothing re-fetched):
  NUFORC  evidence_vault/06_NUFORC_MODERN_ARM/nuforc_unified.json.gz  (134,906; reporter shape
          field + one-line summary + duration text; geocoded to settlement)
  HATCH   ../ufo_data/bin/hatch_udb.json  (Larry Hatch *U* database, 18,116 worldwide cases,
          1 compiler; coded attributes + terse description + duration in minutes)
  GEIPAN  data/raw/geipan/geipan_cases.json  (3,404 French official cases, investigator text
          in French, A/B/C/D classification and an 'Identification' explanation; only the
          witness-side text is coded, see geipan_witness_text)

MUFON's case database (CMS) is not public and is NOT used. That is a gap, not a choice.

Coding is a transparent keyword lexicon (EN + FR), not a learned model, so every feature
can be audited. Features are binary. Lexicon hits in free text are noisy: a one-line
NUFORC summary under-reports features compared to a GEIPAN investigator text. That is why
all clustering is done WITHIN a source and only profiles are compared across sources.

Output: data/processed/taxonomy/records.json.gz  (one dict per report, features as list)
"""
import gzip, json, re, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HATCH = os.environ.get('OMEGA_HATCH', os.path.join(os.path.dirname(ROOT), 'ufo_data', 'bin', 'hatch_udb.json'))
OUT = os.path.join(ROOT, 'data', 'processed', 'taxonomy')

# ---------------------------------------------------------------- lexicon (v2)
# (feature, regex). Applied to lower-cased text. French and English together.
# v2 fixes, each found by reading hits (v1 -> v2):
#   'sound' fired on 'sans bruit'/'aucun bruit' (25% of GEIPAN). Negated noise/light phrases
#     are now stripped before matching (NEG below).
#   'fireball' fired on 'meteorological'/'meteorologique' (weather balloons, weather reports).
#   'fast' fired on bare 'speed'/'vitesse' ('a vitesse lente'); 'vanish' on any 'disparait'
#     (out of view behind trees); 'beam' on 'dans un rayon de' (= within a radius of);
#     'triangle' on 'croissant' (= increasing); 'changing' on 'changing colours';
#     'landing' on 'landing lights'; 'erratic' on 'brusquement' (= suddenly).
SHAPE = [
    ('disc',       r"\b(dis[ck]s?|saucers?|soucoupes?|disques?|plate[- ]shaped|pie[- ]plate)\b"),
    ('sphere',     r"\b(spheres?|spherical|orbs?|balls?(?! of fire)|globes?|boules?(?! de feu)|sph[eè]res?|round object|circle|circular|cercle|rond)\b"),
    ('light',      r"\b(lights?|star[- ]like|like a star|points? of light|points? lumineux|lumi[eè]res?|[ée]toiles?|flare)\b"),
    ('triangle',   r"\b(triang\w*|delta|boomerang|chevron|v[- ]shaped?|forme de v|wedge|crescent|forme de croissant|en croissant)\b"),
    ('cigar',      r"\b(cigars?|cylind\w*|tubes?|tic[- ]?tacs?|cigares?|rod|torpedo|cylindre)\b"),
    ('oval',       r"\b(ovals?|ovoid|ova[l]e?s?|eggs?|ellips\w*|oeufs?|œufs?|teardrop|lenticul\w*|lentille)\b"),
    ('fireball',   r"\b(fire ?balls?|ball of fire|boules? de feu|flames?|flamme\w*|burning|en feu|comets?|com[eè]tes?|meteors?|meteorites?|m[ée]t[ée]ores?|m[ée]t[ée]orites?|bolides?)\b"),
    ('rectangle',  r"\b(rectang\w*|squares?|carr[ée]s?|box|cube)\b"),
    ('diamond',    r"\b(diamonds?|losanges?|rhomb\w*)\b"),
    ('cone',       r"\b(cones?|c[oô]nes?|pyramid\w*|bell[- ]shaped)\b"),
    ('formation',  r"\b(formation|line of lights|row of|string of|in a line|en ligne|train of|chain of|several objects|plusieurs objets|cluster)\b"),
    ('changing',   r"\b(chang(ed|ing|es) (its )?shape|shape[- ]?shift\w*|morph\w*|chang\w* de forme)\b"),
]
SIZE = [
    ('size_large', r"\b(huge|enormous|massive|gigantic|giant|immense|[ée]norme|gigantesque|football field|size of a house|mother ?ship|very large|tr[eè]s grand)\b"),
    ('size_small', r"\b(small|tiny|petite?s?|minuscule)\b"),
]
MOTION = [
    ('hover',     r"\b(hover\w*|stationary|motionless|still in the sky|immobile|stationnaire|suspended|sur place)\b"),
    ('fast',      r"\b(fast|rapid\w*|high speed|great speed|incredible speed|tremendous speed|shot (off|away|up)|zoom\w*|streak\w*|grande vitesse|vitesse (tr[eè]s )?([ée]lev[ée]e|importante|vertigineuse|fulgurante|folle|incroyable)|tr[eè]s vite|rapide\w*)\b"),
    ('erratic',   r"\b(zig[- ]?zag\w*|erratic\w*|erratique\w*|dart\w*|changed direction|sharp turn|90 degree|angles? droits?|changements? (brusques? )?de direction|change brusquement de direction|mouvements? (d[ée]sordonn[ée]s|saccad[ée]s)|bizarre movements?)\b"),
    ('silent',    r"\b(silent\w*|no sound|no noise|noiseless|silenc\w*|sans (aucun )?bruit|aucun bruit|pas de bruit)\b"),
    ('sound',     r"\b(hum(m(ing|ed))?|buzz\w*|roar\w*|whir\w*|bruit\w*|sifflement|vrombissement|rumbl\w*)\b"),
    ('landing',   r"\b(land(ed|ing)(?! lights?)|touch(ed)? (the )?ground|on the ground|atterr\w*|pos[ée]e? au sol)\b"),
    ('vanish',    r"\b(vanish\w*|blinked out|winked out|went out|(suddenly|instantly|just) disappeared|disappeared (suddenly|instantly|into thin air)|s'?[ée]teint\w*|s'est [ée]teint\w*|(soudainement|brusquement|instantan[ée]ment|d'un coup) dispar\w*|dispar\w* (soudainement|brusquement|instantan[ée]ment|d'un coup))\b"),
]
LIGHTB = [
    ('flashing',   r"\b(blink\w*|flash\w*|puls\w*|strob\w*|flicker\w*|clignot\w*|scintill\w*|twinkl\w*)\b"),
    ('multicolor', r"\b(multi[- ]?colou?r\w*|changing colou?rs?|colou?rs? chang\w*|rainbow|multicolore|couleurs changeantes)\b"),
    ('red_orange', r"\b(red|orange|reddish|amber|rouge\w*|orang[ée]e?s?)\b"),
    ('white',      r"\b(white|blanc\w*|blanche\w*|silver\w*|argent\w*)\b"),
    ('green_blue', r"\b(green\w*|blue\w*|verte?s?|bleu\w*)\b"),
    ('beam',       r"\b(beams?|searchlight|spotlight|ray|rays|faisceau\w*|projecteur\w*|rayons? lumineux|rai de lumi[eè]re)\b"),
    ('glow',       r"\b(glow\w*|luminous|lumineu\w*|incandescent|halo|brillant\w*|bright)\b"),
    ('metallic',   r"\b(metal\w*|m[ée]tal\w*|chrome|shiny|reflect\w*)\b"),
]
# negated mentions are removed before matching ('no lights', 'sans aucun bruit')
NEG = re.compile(r"\b(no|without|sans|aucune?s?|pas de|ni|not? any)\s+(\w+\s+){0,2}(sounds?|noises?|bruits?|hum\w*|buzz\w*|lights?|lumi[eè]res?)\b", re.I)
LEX = [(f, re.compile(p, re.I)) for f, p in SHAPE + SIZE + MOTION + LIGHTB]
SILENT_RX = dict(LEX)['silent']
SHAPE_F = [f for f, _ in SHAPE]
DUR_F = ['dur_lt1m', 'dur_1_5m', 'dur_5_30m', 'dur_gt30m']
FEATURES = [f for f, _ in LEX] + DUR_F

# NUFORC's own shape vocabulary -> our shape features (reporter-chosen)
NUFORC_SHAPE = {
    'light': 'light', 'flash': 'light', 'flare': 'light',
    'circle': 'sphere', 'sphere': 'sphere', 'round': 'sphere',
    'triangle': 'triangle', 'triangular': 'triangle', 'chevron': 'triangle', 'delta': 'triangle', 'crescent': 'triangle',
    'fireball': 'fireball', 'disk': 'disc', 'oval': 'oval', 'egg': 'oval', 'teardrop': 'oval',
    'cigar': 'cigar', 'cylinder': 'cigar', 'rectangle': 'rectangle', 'diamond': 'diamond',
    'cone': 'cone', 'formation': 'formation', 'changing': 'changing', 'cross': 'diamond',
}
# Hatch coded attributes -> features (the compiler's own coding; used as a cross-check
# and OR-ed with text). SCR lumps disc+sphere, so it is NOT mapped to either.
HATCH_CODE = {'CIG': 'cigar', 'DLT': 'triangle', 'NLT': 'light', 'FBL': 'fireball', 'RAY': 'beam',
              'SND': 'sound', 'LND': 'landing'}

_NUM = r'(\d+(?:[.,]\d+)?)'
DUR_UNITS = [(r'sec|seconde|s\b', 1), (r'min', 60), (r'h(ou)?r|heure', 3600)]
WORDNUM = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'ten': 10, 'few': 3, 'several': 5,
           'couple': 2, 'a': 1, 'an': 1, 'une': 1, 'un': 1, 'quelques': 3, 'deux': 2, 'trois': 3,
           'quatre': 4, 'cinq': 5, 'dix': 10, 'quinze': 15, 'vingt': 20, 'trente': 30,
           'dizaine': 10, 'quinzaine': 15, 'vingtaine': 20, 'trentaine': 30, 'plusieurs': 5}


def parse_duration(s):
    """Return seconds or None. Takes the first number+unit in the string."""
    if not s:
        return None
    s = s.lower()
    m = re.search(_NUM + r'\s*(?:-|to|à|a)?\s*(?:\d+(?:[.,]\d+)?)?\s*\+?\s*(seconds?|secs?|secondes?|s\b|minutes?|mins?|hours?|hrs?|heures?|h\b)', s)
    if not m:
        m2 = re.search(r'\b(one|two|three|four|five|ten|few|several|couple|a|an|une|un|quelques|deux|trois|quatre|cinq|dix|quinze|vingt|trente|dizaine|quinzaine|vingtaine|trentaine|plusieurs)\s+(?:of\s+|de\s+|d\'\s*)?(seconds?|minutes?|hours?|secondes?|heures?)', s)
        if not m2:
            return None
        n, u = WORDNUM[m2.group(1)], m2.group(2)
    else:
        n, u = float(m.group(1).replace(',', '.')), m.group(2)
    for pat, mult in DUR_UNITS:
        if re.match(pat, u):
            return n * mult
    return None


def dur_bin(sec):
    """Bins: <=1 min, (1,5], (5,30], >30 min. Upper edges are inclusive because Hatch stores
    whole minutes with a floor of 1 ('1' = a minute or less); NUFORC/GEIPAN '1 minute' joins it.
    The four bins enter the class model as ONE categorical item (lca.py), not four binaries."""
    if sec is None:
        return None
    if sec <= 60: return 'dur_lt1m'
    if sec <= 300: return 'dur_1_5m'
    if sec <= 1800: return 'dur_5_30m'
    return 'dur_gt30m'


def code_text(text):
    raw = (text or '').lower()
    t = NEG.sub(' ', raw)
    out = {f for f, rx in LEX if f != 'silent' and rx.search(t)}
    if SILENT_RX.search(raw):          # 'silent' is itself a negation ('no sound'): match on raw text
        out.add('silent')
    return out


def load_nuforc():
    d = json.load(gzip.open(os.path.join(ROOT, 'evidence_vault/06_NUFORC_MODERN_ARM/nuforc_unified.json.gz')))['nuforc']
    out = []
    for r in d:
        txt = r.get('desc') or ''
        if txt.startswith('MADAR'):          # automated sensor node posts, not witness reports
            continue
        feats = code_text(txt)
        sh = (r['kv'].get('Shape') or '').strip().lower()
        if sh in NUFORC_SHAPE:
            feats.add(NUFORC_SHAPE[sh])
        sec = parse_duration(r.get('duration') or r['kv'].get('Duration'))
        b = dur_bin(sec)
        if b: feats.add(b)
        hour = None
        m = re.search(r'\s(\d{1,2}):\d\d', r.get('date_raw') or '')
        if m: hour = int(m.group(1))
        out.append(dict(uid=r['uid'], src='NUFORC', country=r.get('country') or '', lat=r.get('lat'), lon=r.get('lon'),
                        year=r.get('year'), month=r.get('month'), hour=hour, dur_s=sec, shape_field=sh,
                        text=txt, feats=sorted(feats)))
    return out


def _hatch_year(ds):
    m = re.match(r'\s*(\d{1,2})?/?(\d{1,2})?/?(\d{2,4})', ds or '')
    if not m:
        return None, None
    y = m.group(3)
    y = int(y)
    if y < 100:          # Hatch uses 2-digit years for some early-20th c. entries; ambiguous
        return None, None
    mo = int(m.group(1)) if m.group(1) and m.group(2) else None
    return y, mo


def load_hatch():
    d = json.load(open(HATCH, encoding='utf-8-sig'))
    d = d[list(d)[0]]
    out = []
    for i, r in enumerate(d):
        kv = r.get('key_vals', {})
        txt = (r.get('desc') or '')
        feats = code_text(txt)
        codes = [a.split(':')[0] for a in r.get('attributes', [])]
        for c in codes:
            if c in HATCH_CODE: feats.add(HATCH_CODE[c])
        try:
            sec = float(kv.get('Duration')) * 60
        except (TypeError, ValueError):
            sec = None
        b = dur_bin(sec)
        if b: feats.add(b)
        lat = lon = None
        if kv.get('LatLong'):
            try:
                lat, lon = map(float, kv['LatLong'].split())
            except ValueError:
                pass
        y, mo = _hatch_year(r.get('date'))
        hour = None
        m = re.search(r'(\d{1,2}):\d\d', r.get('time') or '')
        if m: hour = int(m.group(1))
        out.append(dict(uid=r.get('source_id', 'Hatch_%d' % i), src='HATCH', country=kv.get('Country') or '',
                        lat=lat, lon=lon, year=y, month=mo, hour=hour, dur_s=sec, codes=codes,
                        locale=kv.get('Locale'), strange=kv.get('Strangeness'), cred=kv.get('Credibility'),
                        text=txt, feats=sorted(feats)))
    return out


# GEIPAN 'Details' mixes the witness account with the investigators' analysis ("l'hypothese
# d'une meprise avec un bolide", "le projecteur d'atterrissage"...), which would leak the
# explanation into the features. Coding uses only (a) the part of 'Identification' before its
# colon (the standard one-line description of what was seen; the explanation follows the colon)
# and (b) the sentences of 'Details' before the first analysis sentence.
_PREAMBLE = re.compile(r"geipan continue|dans ses publications|gr[aâ]ce [aà] de nouveaux moyens|ce cas d'observation fait partie|"
                       r"r[ée]examen|class[ée]s? [«\"]?\s*c", re.I)
_ANALYSIS = re.compile(r"geipan|sepra|gepan|enqu[eê]te|hypoth[eè]se|consistan|[ée]tranget[ée]|s'av[eè]re|m[ée]prise|compatible|"
                       r"coh[ée]ren|probab|explication|explique|identifi|il s'agit|carte astro|voir (le|la|l')|classe|class[ée]|"
                       r"conclu|analyse|semble[nt]? correspondre|correspond ([àa]|bien)|n'a pas pu|aucun autre t[ée]moignage|"
                       r"un seul t[ée]moignage|t[ée]moignages? (est|sont|sera|seront) recueilli", re.I)


def geipan_witness_text(r):
    ident = (r.get('Identification') or '').split(':')[0]
    sents = re.split(r'(?<=[.!?])\s+', (r.get('Détails') or '').strip())
    keep, started = [], False
    for x in sents:
        if not started and _PREAMBLE.search(x):
            continue
        if _ANALYSIS.search(x):
            if started:
                break
            continue
        keep.append(x); started = True
    return ident + ' . ' + ' '.join(keep)


def load_geipan():
    d = json.load(open(os.path.join(ROOT, 'data/raw/geipan/geipan_cases.json')))
    out = []
    for r in d:
        # witness-side text only (see geipan_witness_text); the explanation must not leak in
        wtxt = geipan_witness_text(r)
        feats = code_text(wtxt)
        # duration: first number/word-number + unit within 50 chars after 'dur', 'pendant', 'durant'
        det = wtxt.lower()
        sec = None
        for mm in re.finditer(r"(dur[ée]e?|pendant|durant)", det):
            sec = parse_duration(det[mm.end():mm.end() + 50])
            if sec is not None:
                break
        b = dur_bin(sec)
        if b: feats.add(b)
        mo = None
        md = re.match(r'(\d\d|--)/(\d\d|--)/(\d{4})', r.get('Observation date') or '')
        if md and md.group(2) != '--': mo = int(md.group(2))
        out.append(dict(uid=r['ID Etude de Cas'], src='GEIPAN', country='France', lat=r.get('Latitude'), lon=r.get('Longitude'),
                        year=r.get('Année'), month=mo, hour=None, dur_s=sec, gclass=r.get('Classification'),
                        ident=r.get('Identification'), phen=r.get('Phenomenon'), text=wtxt, feats=sorted(feats)))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    recs = load_nuforc() + load_hatch() + load_geipan()
    with gzip.open(os.path.join(OUT, 'records.json.gz'), 'wt') as f:
        json.dump(dict(features=FEATURES, shape_features=SHAPE_F, records=recs), f)
    by = collections.defaultdict(list)
    for r in recs: by[r['src']].append(r)
    for s, rs in by.items():
        c = collections.Counter(f for r in rs for f in r['feats'])
        none = sum(1 for r in rs if not set(r['feats']) & set(SHAPE_F))
        print(s, len(rs), 'no-shape %.1f%%' % (100 * none / len(rs)))
        print('  ', ', '.join('%s %.1f' % (f, 100 * c[f] / len(rs)) for f in FEATURES))


if __name__ == '__main__':
    main()
