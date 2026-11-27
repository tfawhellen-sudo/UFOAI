import sys, json, os, re, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ia import files, stream_text
D = os.environ.get('L1_RU_DIR', 'data/raw/layer1/ru')
inv = json.load(open(os.path.join(D, 'inventory.json')))
KEEP_WHOLE = {'UFO', 'UFO3', 'TM'}
KW = re.compile(r'НЛО|неопознанн\w* летающ|летающ\w* тарел|аномальн\w* (?:атмосферн|явлен|аэрокосм)|гуманоид|пришельц|уфолог|Петрозаводск\w* (?:феномен|явлен)|медуз\w* в небе|НЛО', re.I)
os.makedirs(os.path.join(D, 'whole'), exist_ok=True)
os.makedirs(os.path.join(D, 'hits'), exist_ok=True)
def work(r):
    tag, ident, title, date = r
    try:
        fs, md = files(ident)
    except Exception as e:
        return (ident, 'ERRMETA', 0, 0)
    txts = [f['name'] for f in fs if f['name'].endswith('_djvu.txt')]
    nh = 0; tot = 0
    for i, fn in enumerate(txts[:60]):
        try:
            t = stream_text(ident, fn)
        except Exception:
            continue
        tot += len(t)
        safe = re.sub(r'[^\w.-]+', '_', ident + '__' + fn)[:180]
        if tag in KEEP_WHOLE or ident in ('hroniki_vizitov_nlo',) or 'fenid' in ident:
            open(os.path.join(D, 'whole', safe), 'w').write(t)
        hits = [m.start() for m in KW.finditer(t)]
        if hits:
            nh += len(hits)
            # merge windows
            spans = []
            for h in hits:
                a, b = max(0, h - 1500), min(len(t), h + 2500)
                if spans and a <= spans[-1][1]:
                    spans[-1][1] = b
                else:
                    spans.append([a, b])
            with open(os.path.join(D, 'hits', safe), 'w') as f:
                for a, b in spans:
                    f.write('@@ %s %s %d-%d\n' % (ident, fn, a, b))
                    f.write(t[a:b] + '\n')
    return (ident, len(txts), tot, nh)
# add the ufo catalog book and fenid explicitly
extra = [('UFO', 'hroniki_vizitov_nlo', 'Хроники визитов НЛО', '2002'),]
todo = inv + [e for e in extra if e[1] not in {x[1] for x in inv}]
res = []
with cf.ThreadPoolExecutor(6) as ex:
    for out in ex.map(work, todo):
        res.append(out)
json.dump(res, open(os.path.join(D, 'fetch_log.json'), 'w'), ensure_ascii=False)
print('items', len(res), 'with text', sum(1 for r in res if isinstance(r[1], int) and r[1] > 0), 'chars', sum(r[2] for r in res), 'hits', sum(r[3] for r in res))
