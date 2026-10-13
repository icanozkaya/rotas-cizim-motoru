# -*- coding: utf-8 -*-
"""Kolon kontrolü: tesisat boruları betonarme kolon/perde poligonlarını kesmemeli (README kalıcı kuralı)."""
import sys, pickle
import ezdxf
from shapely.geometry import LineString
from shapely.affinity import translate
from shapely.strtree import STRtree
sys.path.insert(0, '/home/claude/voyap/tes')
from veri import ROW

GEO = pickle.load(open('/tmp/claude-0/vy/geo.pkl', 'rb'))
LAYS = {"MTY-SOGUKSU-BORU", "MTY-SICAKSU-BORU", "MTY-SIRKULASYON-BORU", "MTY-PISSU-BORU", "MTY-ISITMA-GIDIS-BORU",
        "MTY-ISITMA-DONUS-BORU", "MTY-PEX-BORU", "MTY-SPRINKLER-BORU", "MTY-YANGIN-DOLAP-BORU", "MTY-BACA"}
cols = []
for row in ('Y', 'S', 'H'):
    for i in range(4):
        c = translate(GEO[i]['cols'], *ROW[row])
        cols += [g.buffer(-1.0) for g in getattr(c, 'geoms', [c]) if g.area > 400]
tree = STRtree(cols)


def kontrol(path):
    D = ezdxf.readfile(path)
    hata = []
    for e in D.modelspace().query('LWPOLYLINE'):
        if e.dxf.layer.replace("SCOTT-", "", 1) not in LAYS: continue
        pts = [p[:2] for p in e.get_points()]
        if len(pts) < 2: continue
        ls = LineString(pts)
        for j in tree.query(ls):
            g = cols[j]
            if ls.intersects(g):
                x = ls.intersection(g)
                if x.length > 2.0:
                    hata.append((e.dxf.layer, round(g.centroid.x), round(g.centroid.y), round(x.length)))
    return hata


if __name__ == '__main__':
    H = kontrol(sys.argv[1])
    import collections
    print('KOLON KESEN BORU:', len(H))
    print(collections.Counter(h[0] for h in H))
    for h in H[:40]: print(h)
