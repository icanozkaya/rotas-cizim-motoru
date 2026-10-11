import pickle, sys, re
sys.path.insert(0,'/home/claude/nb')
from clean import clean
from shapely.geometry import Polygon, Point
from collections import defaultdict
flat=pickle.load(open('/tmp/claude-0/nb_flat.pkl','rb'))
SHEETS={'A-BOD':(74217,-11094,78667,-8094),'A-ZEM':(78667,-11094,83117,-8094),'A-K1':(83117,-11094,87567,-8094),
        'A-K2':(87567,-11094,92017,-8094),'A-CATI':(92017,-11094,96467,-8094),
        'B-ZEM':(73267,-14594,77717,-11594),'B-K1':(77717,-14594,82167,-11594),'B-K2':(82167,-14594,86617,-11594),'B-CATI':(86617,-14594,91067,-11594),
        'VAZ':(71102,-11094,74217,-8094)}
def sheet_of(x,y):
    for k,(a,b,c,d) in SHEETS.items():
        if a<x<c and b<y<d: return k
def pt(k,d): return (d[0],d[1]) if k=='C' else (d[0][0],d[0][1]) if k in('L','T') else d[0]
rooms=defaultdict(list); texts=defaultdict(list); marks=defaultdict(list)
for k,l,d,p in flat:
    x,y=pt(k,d); s=sheet_of(x,y)
    if not s: continue
    if l=='A-FLOR' and k=='P' and len(d)>=4:
        try:
            pg=Polygon(d)
            if pg.is_valid and pg.area>5000: rooms[s].append(pg)
        except Exception: pass
    elif k=='T':
        t=clean(d[1])
        if l=='A-AREA-IDEN': texts[s].append((x,y,t,d[2]))
        elif l in('YAZI S',): marks[s].append((t,x,y))
        elif re.match(r'(?i)da[iİı]re\s*\d',t): marks[s].append((t,x,y))
    if l=='Y.İ.B' and k=='C': marks[s].append(('YIB',d[0],d[1]))
NAMES=re.compile(r'(?i)^(SALON|ODA|E\. YATAK|YATAK|BANYO|WC|HOL|BALKON|MUTFAK|ANTRE|KORİDOR|GİRİŞ|EBEVEYN|ÇAMAŞIR|KİLER|DEPO|TERAS|KAT HOLÜ|MERDİVEN|ASANSÖR|SIĞINAK|OTOPARK|KAZAN|DUŞ|LAVABO|SOYUNMA|GİYİNME|DAİRE|TEKNİK|OFİS|DÜKKAN)')
out={}
for s in SHEETS:
    R=[]
    for pg in rooms[s]:
        nm=[t for t in texts[s] if pg.contains(Point(t[0],t[1]))]
        names=[t[2] for t in nm if NAMES.match(t[2])]
        al=[t[2] for t in nm if t[2].startswith('Alan')]
        R.append(dict(poly=pg, name=names[0] if names else '?', alan=al[0] if al else '', area=pg.area/1e4))
    out[s]=dict(rooms=R, marks=marks[s])
    from collections import Counter
    print(s, len(R), Counter(r['name'] for r in R).most_common(), 'marks:', Counter(m[0] for m in marks[s]).most_common(12))
pickle.dump((SHEETS,out),open('/tmp/claude-0/nb_model.pkl','wb'))
