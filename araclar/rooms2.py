import pickle,re,sys
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
def detect(fn,win):
    flat=pickle.load(open(fn,'rb'))
    x0,y0,x1,y1=win
    lays=('YLZ-DUVAR','YLZ-KOLON','YLZ-PENCERE','YLZ-KAPI','YLZ-PERDE','YLZ-KORKULUK','YLZ-MERDİVEN','YLZ-VERANDA-BALKON','YLZ-ISLAK HACİMLER')
    ins=lambda p: x0-5<=p[0]<=x1+5 and y0-5<=p[1]<=y1+5
    segs=[]
    for r in flat:
        if r[1] not in lays: continue
        if r[0]=='L' and ins(r[2][0]) and ins(r[2][1]): segs.append(LineString(r[2]))
        elif r[0]=='P' and all(ins(p) for p in r[2]): segs.append(LineString(r[2]))
    U=unary_union([s.buffer(3) for s in segs])
    free=box(x0,y0,x1,y1).difference(U)
    polys=list(free.geoms) if hasattr(free,'geoms') else [free]
    out=[]
    for r in flat:
        if r[0]=='T' and 'ALAN' in r[2][1] and ins(r[2][0]):
            t=re.sub(r'\\[A-Za-z][^;]*;|[{}]','',r[2][1]).replace('\\P',' ')
            t=re.sub(r'\\U\+([0-9A-F]{4})',lambda m:chr(int(m.group(1),16)),t)
            m=re.search(r'(.+?)\s*ALAN\s*:\s*([0-9]+,[0-9]+)',t)
            if not m: continue
            p=Point(r[2][0])
            c=sorted([q for q in polys if q.distance(p)<40 and q.area<400000],key=lambda q:q.distance(p))
            out.append((m.group(1).strip(),float(m.group(2).replace(',','.')),tuple(round(v) for v in r[2][0]),[(round(q.area/1e4,2),[round(v) for v in q.bounds]) for q in c[:2]]))
    return out
if __name__=='__main__':
    for o in detect(sys.argv[1],tuple(map(float,sys.argv[2:6]))): print(o)
