"""Teslim öncesi kontroller: kolon kesişimi, bina dışı boru, boru-boru kesişimi (farklı sistem)"""
import pickle, ezdxf, sys
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
VY = '/tmp/claude-0/vy/'
GM = pickle.load(open(VY + 'geo.pkl', 'rb'))
from geo import PAN
d = ezdxf.readfile(sys.argv[1] if len(sys.argv) > 1 else VY + 'YANGIN_EK.dxf')
PIPE = ('MTY-SPRINKLER-BORU', 'MTY-YANGIN-DOLAP-BORU', 'MTY-YANGIN-ITFAIYE', 'MTY-YANGIN-POMPA')
segs = []
for e in d.modelspace().query('LWPOLYLINE'):
    if e.dxf.layer not in PIPE: continue
    p = [q[:2] for q in e.get_points()]
    for a, b in zip(p[:-1], p[1:]):
        if abs(a[0]-b[0]) + abs(a[1]-b[1]) > 0.5: segs.append((e.dxf.layer, LineString([a, b])))
bad = 0
for i, (x0, x1) in enumerate(PAN):
    K = GM[i]['cols']
    for lay, s in segs:
        if not (x0 <= s.coords[0][0] <= x1 and -458149 < s.coords[0][1] < -450649): continue
        x = s.intersection(K)
        if x.length > 1.0:
            bad += 1; print('KOLON', i, lay, [round(v) for v in s.coords[0]], [round(v) for v in s.coords[1]], round(x.length, 1))
        if i > 0 or True:
            out = s.difference(GM[i]['foot'].buffer(2))
            if out.length > 1.0 and lay != 'MTY-YANGIN-ITFAIYE':
                bad += 1; print('DIŞARI', i, lay, [round(v) for v in s.coords[0]], round(out.length, 1))
# farklı sistem boru kesişimi (köprüsüz)
for k, (l1, s1) in enumerate(segs):
    for l2, s2 in segs[k + 1:]:
        if l1 == l2: continue
        if s1.crosses(s2):
            pt = s1.intersection(s2)
            print('KESİŞİM', l1, l2, [round(v) for v in pt.coords[0]] if pt.geom_type == 'Point' else pt.geom_type)
print('KOLON/DIŞARI HATA', bad)
