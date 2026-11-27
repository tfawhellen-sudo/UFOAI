"""Deep-time corpus: every pre-1947 aerial-phenomenon record in the project, plus modern comparators.

Historical catalogs (all already in ../ufo_data/bin, nothing new fetched except Obsequens):
  WITS      ancient.json          478  Vallee & Aubeck, Wonders in the Sky (2009), AD 34-1879.
                                       TEXT IS AN LLM PARAPHRASE made by the ufo_data author, not the book's words.
  PREROS    pre_roswell_chap1-2   107  Rife, It Didn't Start with Roswell (2001); LLM paraphrase too.
  HATCH     hatch_udb.json             Larry Hatch *U* database; his own terse summaries (one compiler, AD 840-2003).
  EBERHART  eberhart.json              Eberhart, UFOs and Intelligence (CUFOS); compiler prose with sources.
  OVERMEIRE overmeire.json             Overmeire's chronology; mostly translated from French (Naud 1977 etc.).
  RR0       rr0.json                   Jerome Beau's rr0.org chronology, translated from French.
  JOHNSON   johnson.json               ufoinfo.com 'on this day' (Johnson).
  MAGONIA   magonia.json               Vallee's Magonia catalogue (1868-1968).
  NICAP     nicap_db.json              NICAP listing.
Primary text (no ufologist in between):
  OBSEQUENS Julius Obsequens, Liber prodigiorum (4th c. AD compilation of Livy's prodigy lists, 191-12 BC),
            French translation, Nisard ed. 1850, archive.org corneliusneposq00nepogoog. Sky clauses only.
Every catalog is loaded for ALL its years (most run to 2000-2022), so drift can be measured inside one
compiler's voice. Modern comparators (craft-taxonomy records file, data/processed/taxonomy/records.json.gz):
  NUFORC 1947+ (witness-written), GEIPAN (A/B = identified with a stimulus, D = unexplained).

Each historical record keeps its catalog; the same event in several catalogs is linked into one
'event': same year; if both give a month (and day), these must agree and the texts share >=0.12 word
overlap or a place word; if either lacks a month, the texts must share >=0.3 word overlap.
Output: data/processed/deeptime/corpus.json.gz
"""
import gzip, json, os, re, sys, collections, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lexicon import code, split_explanation, ALL, PHYS  # noqa: E402

PHYS_SET = set(PHYS)
AER = re.compile(r"\b(sky|skies|air|aerial|heavens?|clouds?|flew|fly|flying|flies|overhead|aloft|descend\w*|hover\w*|ascend\w*|"
                 r"rose|soar\w*|horizon|sighted|appeared|luminous|globe|disc|disk|star|ciel|airship|craft|object)\b", re.I)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UFOD = os.environ.get('OMEGA_UFODATA', os.path.join(os.path.dirname(ROOT), 'ufo_data', 'bin'))
OUT = os.path.join(ROOT, 'data', 'processed', 'deeptime')
OBSEQ = os.path.join(ROOT, 'data', 'raw', 'deeptime', 'corneliusneposq00nepogoog.txt')

CATALOGS = [('WITS', 'ancient.json', True), ('PREROS', 'pre_roswell_chap1.json', True), ('PREROS', 'pre_roswell_chap2.json', True),
            ('HATCH', 'hatch_udb.json', False), ('EBERHART', 'eberhart.json', False), ('OVERMEIRE', 'overmeire.json', False),
            ('RR0', 'rr0.json', False), ('JOHNSON', 'johnson.json', False), ('MAGONIA', 'magonia.json', False),
            ('NICAP', 'nicap_db.json', False)]

REGION = [
    ('East Asia', r"china|chinese|japan|japanese|korea|korean|peking|beijing|kyoto|edo|tokyo|manchuria|mongol|formosa|taiwan"),
    ('South/West Asia & Africa', r"india|persia|iran|iraq|baghdad|syria|turkey|constantinople|istanbul|arabia|egypt|cairo|"
                                 r"palestine|jerusalem|israel|africa|morocco|algeria|ethiopia|ceylon|afghan|pakistan|bengal|madras"),
    ('Americas', r"america|usa|u\.s\.|united states|canada|mexico|brazil|argentin|chile|peru|colombia|cuba|"
                 r"california|texas|nebraska|iowa|kansas|illinois|ohio|michigan|indiana|new york|missouri|wisconsin|"
                 r"minnesota|kentucky|tennessee|arkansas|oklahoma|colorado|washington|oregon|massachusetts|"
                 r"pennsylvania|virginia|carolina|georgia|alabama|mississippi|louisiana|florida|maine|vermont|"
                 r"connecticut|new jersey|maryland|dakota|montana|wyoming|utah|nevada|arizona|new mexico|idaho|"
                 r"ontario|quebec|nova scotia|newfoundland|manitoba|british columbia"),
    ('Oceania', r"australia|new zealand|tasmania|victoria, au|queensland|new south wales"),
    ('Europe', r"england|britain|scotland|ireland|wales|london|france|paris|germany|german|italy|rome|spain|portugal|"
               r"belgium|holland|netherlands|switzerland|austria|hungary|poland|russia|moscow|sweden|norway|denmark|"
               r"finland|iceland|greece|bohemia|prussia|bavaria|saxony|flanders|brabant|silesia|czech|yugoslav|"
               r"serbia|croatia|romania|bulgaria|ukraine|lithuania|latvia|estonia|europe|scandinavia|sicily|sardinia|"
               r"corsica|malta|cyprus|byzant|lyon|basel|nuremberg|hamburg|vienna|venice|florence|naples|milan|"
               r"geneva|zurich|madrid|lisbon|amsterdam|brussels|copenhagen|stockholm|oslo|dublin|edinburgh|"
               r"york|kent|essex|yorkshire|cornwall|devon|norfolk|suffolk|sussex|lancashire|cheshire|"
               r"normandy|brittany|burgundy|provence|alsace|lorraine|picardy|champagne|gaul|frankish|saxon"),
]
_REG = [(n, re.compile(p, re.I)) for n, p in REGION]


def region(*texts):
    t = ' '.join(x for x in texts if x)
    for n, rx in _REG:
        if rx.search(t):
            return n
    return 'Unknown'


def parse_date(ds):
    """'4/34' -> (34,4,None); '5/21/70' -> (70,5,21); 'Late 10/1945' -> (1945,10,None); '1880's' -> 1880."""
    ds = str(ds or '')
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{1,4})", ds)
    if m:
        return int(m.group(3)), int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d{1,2})/(\d{1,4})\b", ds)
    if m:
        return int(m.group(2)), int(m.group(1)), None
    nums = re.findall(r"\d{1,4}", ds)
    if nums:
        return int(max(nums, key=len)), None, None
    return None, None, None


def load_catalogs():
    out = []
    for cat, fn, llm in CATALOGS:
        d = json.load(open(os.path.join(UFOD, fn), encoding='utf-8-sig'))
        d = d[list(d)[0]] if isinstance(d, dict) else d
        for i, r in enumerate(d):
            y, mo, dy = parse_date(r.get('date'))
            if y is None or y < 1 or y > 2025:
                continue
            raw = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', str(r.get('desc') or ''))   # markdown links -> text
            raw = re.sub(r'\\([()\[\]])', r'\1', raw).replace('(Translated from French)', '')
            wit, mund = split_explanation(raw)
            feats = code(wit)
            # general Fortean chronologies (Eberhart, Overmeire, RR0) also list context entries (Newton's third
            # law, test-pilot records, births). Keep a record only if it describes something seen.
            if cat != 'HATCH' and not (AER.search(raw) or feats & PHYS_SET):
                continue
            loc = r.get('location') or (r.get('key_vals') or {}).get('Country') or ''
            if isinstance(loc, list): loc = ' '.join(map(str, loc))
            out.append(dict(uid=f"{cat}:{r.get('source_id', i)}", cat=cat, llm=llm, year=y, month=mo, day=dy,
                            loc=str(loc), region=region(str(loc), raw if not loc else ''), text=wit, raw=raw,
                            mundane=mund, feats=sorted(feats),
                            hatch_codes=[a.split(':')[0] for a in r.get('attributes', [])] if cat == 'HATCH' else None))
    return out


_W = re.compile(r"[a-z]{4,}")
_STOP = set('that this with from were they their there which when what have been into over then them than also about '
            'object objects light lights seen saw observed appeared sky witnesses event'.split())


def words(t):
    return {w for w in _W.findall((t or '').lower()) if w not in _STOP}


def link_events(recs):
    """Union-find over records of the same year whose dates and words agree."""
    by_year = collections.defaultdict(list)
    for i, r in enumerate(recs):
        by_year[r['year']].append(i)
    par = list(range(len(recs)))

    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    W = [words(r['raw'] + ' ' + r['loc']) for r in recs]
    L = [words(r['loc']) for r in recs]
    for y, idx in by_year.items():
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                i, j = idx[a], idx[b]
                ri, rj = recs[i], recs[j]
                if ri['cat'] == rj['cat']:
                    continue
                if ri['month'] and rj['month'] and ri['month'] != rj['month']:
                    continue
                if ri['day'] and rj['day'] and ri['day'] != rj['day']:
                    continue
                jac = len(W[i] & W[j]) / max(1, len(W[i] | W[j]))
                both_md = bool(ri['month'] and rj['month'])
                if (both_md and (jac >= 0.12 or L[i] & L[j])) or jac >= 0.3:
                    par[f(i)] = f(j)
    for i, r in enumerate(recs):
        r['event'] = 'E%d' % f(i)


def load_obsequens():
    """Sky clauses of Obsequens (French). Chapters are delimited by '(An de R. NNN.)'; Latin columns are
    interleaved by the OCR, so only lines that score as French are kept."""
    lines = open(OBSEQ, encoding='utf-8').read().split('\n')[125540:128300]
    txt = '\n'.join(lines)
    marks = [(m.start(), int(m.group(1))) for m in re.finditer(r'An\s+de\s+R\.?\s*(\d{3})', txt)]
    FR = re.compile(r"\b(le|la|les|des|une|un|du|dans|fut|vit|on|qui|que|sur|au|aux|pendant|il|elle|furent|parut|aper[cç]ut)\b")
    LA = re.compile(r"\b(est|sunt|cum|quod|visa|visus|visum|coelo|caelo|ad|ab|ex|per|esse|fuit|nocte|tempore|apparuit|lapidibus)\b")
    SKY = re.compile(r"ciel|dans l'air|soleil|lune|[ée]toile|torche|flambeau|globe|bouclier|navire|armes|feu|lumi[eè]re|"
                     r"astre|com[eè]te|clart[ée]|nuit|jour|flamme|poutre|disque|cercle|arc", re.I)
    NOTSKY = re.compile(r"foudre|frapp|tomba sur|naqu|enfant|androgyne|mule|truie|bœuf|boeuf|pluie de|plut|sang|lait|"
                        r"pierres|vesta|terre trembl|tremblement|statue|temple|loup|rat|abeilles|essaim|serpent n", re.I)
    out = []
    for k, (pos, auc) in enumerate(marks):
        seg = txt[pos:marks[k + 1][0] if k + 1 < len(marks) else len(txt)]
        fr = [l for l in seg.split('\n') if len(FR.findall(l.lower())) > len(LA.findall(l.lower()))]
        body = re.sub(r'-\s*\n\s*', '', '\n'.join(fr)).replace('\n', ' ')
        for c, cl in enumerate(re.split(r'[;.:]', body)):
            cl = cl.strip()
            if len(cl) < 15 or not SKY.search(cl) or NOTSKY.search(cl):
                continue
            if not re.search(r"ciel|air|soleil|lune|[ée]toile|torche|flambeau|globe|bouclier|navire|astre|com[eè]te|clart|poutre|arc|cercle|disque", cl, re.I):
                continue
            out.append(dict(uid=f'OBSEQUENS:{auc}:{c}', cat='OBSEQUENS', llm=False, year=auc - 753 - 1 if auc < 754 else auc - 753,
                            month=None, day=None, loc='Italy', region='Europe', text=cl, raw=cl, mundane=False,
                            feats=sorted(code(cl)), hatch_codes=None, event=f'O{auc}:{c}'))
    return out


def load_modern():
    D = json.load(gzip.open(os.path.join(ROOT, 'data/processed/taxonomy/records.json.gz')))['records']
    out = []
    for r in D:
        try:
            y = int(r.get('year'))
        except (TypeError, ValueError):
            continue
        if r['src'] == 'HATCH' or (r['src'] == 'NUFORC' and y < 1947):
            continue                                  # Hatch (all years) comes from the catalog loader above
        cls = None
        if r['src'] == 'GEIPAN':
            cls = r.get('gclass')
        out.append(dict(uid=r['uid'], cat=r['src'] + '_MODERN', llm=False, year=y, region='Americas' if r['src'] == 'NUFORC' and
                        r.get('country') in ('United States', 'USA', 'Canada') else ('Europe' if r['src'] == 'GEIPAN' else region(r.get('country'))),
                        text=r['text'], mundane=(cls in ('A', 'B')) if cls else False, gclass=cls, phen=r.get('phen'),
                        feats=sorted(code(r['text']))))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    hist = load_catalogs()
    link_events(hist)
    obs = load_obsequens()
    mod = load_modern()
    recs = obs + hist + mod
    json.dump(dict(features=ALL, records=recs), gzip.open(os.path.join(OUT, 'corpus.json.gz'), 'wt'))
    c = collections.Counter(r['cat'] for r in recs)
    print('records by catalog:', dict(c))
    print('historical events (linked):', len({r['event'] for r in hist}), 'from', len(hist), 'records')
    print('historical mundane-flagged:', sum(r['mundane'] for r in hist))
    print('regions (hist):', collections.Counter(r['region'] for r in hist))
    print('obsequens sky clauses:', len(obs))
    for r in obs[:8]:
        print('  ', r['year'], r['text'][:120], r['feats'])


if __name__ == '__main__':
    main()
