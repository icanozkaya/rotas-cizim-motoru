# -*- coding: utf-8 -*-
"""SI_INAK (market zemin kat) : sığınak A-Z-16 poligonu + betonarme kolon (ANSI33) / duvar (ANSI31) poligonları -> JSON"""
import ezdxf, math, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PRJ = os.path.join(KOK, 'proje', 'si_inak_siginak')
GIR = os.path.join(PRJ, 'si_mimari.dxf'); CIK = os.path.join(PRJ, 'si_mimari.json')
d = ezdxf.readfile(GIR); m = d.modelspace()
X0, Y0, X1, Y1 = 259700, -698600, 262200, -693900; S = 2.0
W = int((X1 - X0) / S); H = int((Y1 - Y0) / S)
img = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(img)
P = lambda p: ((p[0] - X0) / S, (Y1 - p[1]) / S)


def it(es):
    for e in es:
        if e.dxftype() == 'INSERT':
            try:
                yield from it(e.virtual_entities())
            except Exception:
                pass
        else:
            yield e


for e in it(m):
    if e.dxf.layer == 'MTY-BORU':
        continue
    t = e.dxftype(); pts = []
    try:
        if t == 'LINE':
            pts = [e.dxf.start[:2], e.dxf.end[:2]]
        elif t == 'LWPOLYLINE':
            pts = [(q[0], q[1]) for q in e.get_points()]
            if e.closed: pts.append(pts[0])
        elif t == 'POLYLINE':
            pts = [(v.dxf.location[0], v.dxf.location[1]) for v in e.vertices]
            if e.is_closed: pts.append(pts[0])
        elif t in ('ARC', 'CIRCLE'):
            c = e.dxf.center; r = e.dxf.radius
            a0, a1 = (0, 360) if t == 'CIRCLE' else (e.dxf.start_angle, e.dxf.end_angle)
            if a1 < a0: a1 += 360
            pts = [(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 30)]
    except Exception:
        continue
    if len(pts) > 1:
        dr.line([P(p) for p in pts], fill=255, width=2)
a = np.array(img) > 0
lab, n = ndimage.label(~a)
l = lab[int((Y1 - -696300) / S), int((260431 - X0) / S)]
msk = ndimage.binary_dilation(lab == l, iterations=1)
polys = []
for r in range(msk.shape[0]):
    row = msk[r]; c = 0
    while c < len(row):
        if row[c]:
            c0 = c
            while c < len(row) and row[c]: c += 1
            polys.append(box(X0 + c0 * S, Y1 - (r + 1) * S, X0 + c * S, Y1 - r * S))
        else:
            c += 1
g = unary_union(polys).buffer(1.5).buffer(-1.5).simplify(2.0)
if g.geom_type == 'MultiPolygon':
    g = max(g.geoms, key=lambda q: q.area)
sig = Polygon(g.exterior)
kol, duv = [], []
for e in m.query('HATCH'):
    if e.dxf.pattern_name not in ('ANSI33', 'ANSI31'):
        continue
    for p in e.paths:
        vs = [(v[0], v[1]) for v in p.vertices] if hasattr(p, 'vertices') else [(ed.start[0], ed.start[1]) for ed in p.edges if hasattr(ed, 'start')]
        if len(vs) < 3: continue
        pg = Polygon(vs).buffer(0)
        if not box(X0, Y0, X1, Y1).intersects(pg): continue
        (kol if e.dxf.pattern_name == 'ANSI33' else duv).append(pg)
json.dump(dict(sig=list(sig.exterior.coords), sig_alan=sig.area / 1e4, bounds=sig.bounds,
               betonarme=[list(b.exterior.coords) for b in kol], duvar=[list(b.exterior.coords) for b in duv]), open(CIK, 'w'))
print('sığınak raster alanı', round(sig.area / 1e4, 2), 'm²', [round(v) for v in sig.bounds], 'kolon', len(kol), 'duvar', len(duv))
