# -*- coding: utf-8 -*-
"""new_block bodrum: sığınak bölgesi, WC hücreleri, betonarme (taramalı) poligonlarını çıkarır -> JSON"""
import ezdxf, math, json, sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import LineString, Polygon, box, mapping
from shapely.ops import unary_union
KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
GIR = os.path.join(KOK, 'proje', 'new_block_siginak', 'new_block_mimari.dxf')
CIK = os.path.join(KOK, 'proje', 'new_block_siginak', 'nb_mimari.json')
d = ezdxf.readfile(GIR); m = d.modelspace()
X0, Y0, X1, Y1 = 357780, -614700, 359240, -609900; S = 2.0
W = int((X1 - X0) / S); H = int((Y1 - Y0) / S)
img = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(img)
P = lambda p: ((p[0] - X0) / S, (Y1 - p[1]) / S)
diag = []
for e in m:
    t = e.dxftype()
    if t == 'LINE':
        pts = [(e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1])]
        dx = pts[1][0] - pts[0][0]; dy = pts[1][1] - pts[0][1]
        if math.hypot(dx, dy) > 1:
            a = math.degrees(math.atan2(dy, dx)) % 180
            if abs(a - 45) < 3 or abs(a - 135) < 3:
                diag.append(LineString(pts))
    elif t == 'LWPOLYLINE':
        pts = [(q[0], q[1]) for q in e.get_points()]
        if e.closed: pts.append(pts[0])
    elif t in ('ARC', 'CIRCLE'):
        c = e.dxf.center; r = e.dxf.radius
        a0, a1 = (0, 360) if t == 'CIRCLE' else (e.dxf.start_angle, e.dxf.end_angle)
        if a1 < a0: a1 += 360
        pts = [(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 30)]
    else:
        continue
    if len(pts) > 1:
        dr.line([P(p) for p in pts], fill=255, width=2)
a = np.array(img) > 0
lab, n = ndimage.label(~a)


def bolge(x, y):
    l = lab[int((Y1 - y) / S), int((x - X0) / S)]
    msk = ndimage.binary_dilation(lab == l, iterations=1)       # çizgi kalınlığını geri al
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
    return Polygon(g.exterior)


sig = bolge(358321, -610650)
WC = {}
for e in m.query('TEXT'):
    s = e.dxf.text
    if 'WC' in s:
        p = e.dxf.insert
        WC[f"{s.replace('%%U', '').strip()}@{round(p[0])}"] = bolge(p[0] + 15, p[1] - 30)
# betonarme: tarama çizgisi kümeleri; yakın kümeler (aynı kolonun alt/üst taraması) birleşir
U = unary_union([g.buffer(3.5, cap_style=2) for g in diag]).buffer(4).buffer(-4)
ps = [p for p in (U.geoms if hasattr(U, 'geoms') else [U]) if p.area > 150]
bet = []
for p in ps:
    b = p.envelope if p.area < 6000 else p          # kolonlar: zarf; uzun perdeler: kendisi
    bet.append(b)
# aynı kolonun iki şerit taraması (60/60 gibi) -> zarfları birleştir
birles = True
while birles:
    birles = False
    for i in range(len(bet)):
        for j in range(i + 1, len(bet)):
            if bet[i].area < 6000 and bet[j].area < 6000 and bet[i].distance(bet[j]) < 40:
                bx = bet[i].union(bet[j]).envelope
                if bx.area < 6000:
                    bet[i] = bx; bet.pop(j); birles = True; break
        if birles: break
json.dump(dict(sig=list(sig.exterior.coords), sig_alan=sig.area / 1e4,
               wc={k: list(v.exterior.coords) for k, v in WC.items()},
               betonarme=[list(b.exterior.coords) for b in bet]), open(CIK, 'w'))
print('sığınak (raster) alanı', round(sig.area / 1e4, 2), 'm²; WC', {k: round(v.area / 1e4, 2) for k, v in WC.items()}, 'betonarme', len(bet))
