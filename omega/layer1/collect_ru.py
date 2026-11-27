import sys, json, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ia import search, files, stream_text
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
queries = [
 ('ZS',  'title:(Знание сила) AND date:[1970-01-01 TO 1993-12-31]'),
 ('NiZ', 'title:(Наука и жизнь) AND date:[1970-01-01 TO 1993-12-31]'),
 ('HiZ', 'title:(Химия и жизнь)'),
 ('IR',  'title:(Изобретатель и рационализатор)'),
 ('VS',  'title:(Вокруг света) AND date:[1970-01-01 TO 1993-12-31]'),
 ('OG',  'title:(Огонёк) AND date:[1975-01-01 TO 1993-12-31]'),
 ('TM',  'title:(Техника молодёжи) OR title:(Техника - молодёжи) OR title:(Техника-молодежи)'),
 ('UT',  'title:(Юный техник)'),
 ('UFO', 'title:(НЛО) AND mediatype:texts'),
 ('UFO2','title:(аномальн) AND mediatype:texts'),
 ('UFO3','identifier:(03-03-1990 OR 1992-03-04-28-29 OR 5-69-02-02-99 OR esli_1993_09)'),
 ('ZiV', 'title:(Земля и Вселенная)'),
]
inv = []
for tag, q in queries:
    n, docs = search(q, 400)
    docs = [d for d in docs if d.get('mediatype') == 'texts']
    print(tag, n, len(docs), flush=True)
    for d in docs:
        inv.append((tag, d['identifier'], str(d.get('title')), str(d.get('date', ''))[:10]))
seen = set(); inv2 = []
for r in inv:
    if r[1] in seen: continue
    seen.add(r[1]); inv2.append(r)
json.dump(inv2, open(os.path.join(OUT, 'inventory.json'), 'w'), ensure_ascii=False, indent=0)
print('items', len(inv2))
