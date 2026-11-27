import re, json, sys, collections
t = open(sys.argv[1]).read()
t = t.replace('­', '')
MON = {'январ':1,'феврал':2,'март':3,'апрел':4,'ма':5,'июн':6,'июл':7,'август':8,'сентябр':9,'октябр':10,'ноябр':11,'декабр':12}
mon_re = r'(январ[яь]|феврал[яь]|марта?|апрел[яь]|ма[яй]|июн[яь]|июл[яь]|августа?|сентябр[яь]|октябр[яь]|ноябр[яь]|декабр[яь])'
# header: optional day, month, year, optional ', time' then ';' place '.'
hdr = re.compile(r'(?m)^\s*(?:(?P<day>[0-9|lI]{1,2}(?:\s*[-–]\s*[0-9]{1,2})?)\s+)?(?:(?P<mon>' + mon_re + r')\s+)?(?:(?P<season>весна|лето|осень|зима|начало|середина|конец)\w*\s+)?(?P<year>1[0-9]{3}|20[0-2][0-9]|[1-9][0-9]{2})\s*(?:г\.?|года?)?\s*(?:\((?:или|по другим)[^)]*\))?\s*(?:,\s*(?P<time>[^;\n]{1,40}))?;\s*(?P<place>[^\n]{2,160})$')
ents = []
ms = list(hdr.finditer(t))
for i, m in enumerate(ms):
    end = ms[i+1].start() if i+1 < len(ms) else len(t)
    body = t[m.end():end].strip()
    day = m.group('day')
    if day:
        day = day.replace('|','1').replace('l','1').replace('I','1')
    mon = m.group('mon')
    mnum = None
    if mon:
        for k,v in MON.items():
            if mon.startswith(k): mnum = v; break
    y = int(m.group('year'))
    ents.append(dict(n=i, year=y, month=mnum, day=day, season=m.group('season'), time=(m.group('time') or '').strip(), place=m.group('place').strip(), body=body[:4000], offset=m.start()))
print(len(ents), file=sys.stderr)
c = collections.Counter((e['year']//10)*10 for e in ents if e['year']>=1900)
print(sorted(c.items()), file=sys.stderr)
print('with day:', sum(1 for e in ents if e['day'] and e['month']), file=sys.stderr)
json.dump(ents, open(sys.argv[2],'w'), ensure_ascii=False, indent=0)
