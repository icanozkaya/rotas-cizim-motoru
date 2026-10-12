import pickle,ezdxf,sys
from shapely.geometry import LineString,Polygon
from shapely.ops import unary_union
F=pickle.load(open('mek.pkl','rb'))
polys=[]
for r in F:
    if r[0]=='P' and r[1] in ('MKDU0','KOLON','50 KOLON','RAST-MIM-BETONARME','MI-KOL'):
        q=[p[:2] for p in r[2]]
        if 5<=len(q)<=9 and abs(q[0][0]-q[-1][0])+abs(q[0][1]-q[-1][1])<1:
            g=Polygon(q)
            if g.is_valid and 400<g.area<80000: polys.append(g)
pickle.dump(polys,open('kolon_poly.pkl','wb'))
K=unary_union(polys)
d=ezdxf.readfile(sys.argv[1] if len(sys.argv)>1 else 'YS_EK2.dxf')
bad=[]
for e in d.modelspace():
    if e.dxftype()=='LWPOLYLINE': p=[q[:2] for q in e.get_points()]
    elif e.dxftype()=='LINE': p=[(e.dxf.start.x,e.dxf.start.y),(e.dxf.end.x,e.dxf.end.y)]
    else: continue
    lay=e.dxf.layer
    if lay not in ('MTY-YAGMUR-BORUSU','YS-KULLANMA','YS-TASMA','YS-TAKVIYE','YS-ELEKTRIK'): continue
    for a,b in zip(p[:-1],p[1:]):
        s=LineString([a,b])
        if s.length<0.5: continue
        x=s.intersection(K)
        if x.length>0.5: bad.append((lay,[round(v) for v in a],[round(v) for v in b],round(x.length,1)))
print(len(polys),'kolon')
for b in bad: print(b)
print('TOPLAM',len(bad))
