# -*- coding: utf-8 -*-
"""Teslim öncesi denetim: (1) aynı/farklı sistem boru çizgileri üst üste binmesi, (2) köprüsüz gidiş-dönüş kesişmesi,
(3) katman öneki (ROTAS-, MTY blok iç katmanları hariç), (4) patlatılmış MTY bloğu yok (INSERT sayısı)."""
import sys
import ezdxf
from shapely.geometry import LineString
from shapely.strtree import STRtree


def segler(e):
    pts = list(e.get_points('xyb'))
    out = []
    for i in range(len(pts) - 1):
        if abs(pts[i][2]) > 1e-9:
            continue                      # köprü yayı
        a, b = pts[i][:2], pts[i + 1][:2]
        if a != b:
            out.append(LineString([a, b]))
    return out


def denetle(yol):
    d = ezdxf.readfile(yol)
    msp = d.modelspace()
    S = {'G': [], 'D': []}
    for e in msp.query('LWPOLYLINE'):
        k = {'ROTAS-ISITMA-GIDIS': 'G', 'ROTAS-ISITMA-DONUS': 'D'}.get(e.dxf.layer)
        if k:
            S[k] += [(s, e.dxf.handle) for s in segler(e)]
    hepsi = S['G'] + S['D']
    geo = [s for s, _ in hepsi]
    tree = STRtree(geo)
    ust_uste, kesisme = 0, 0
    for i, (s, h) in enumerate(hepsi):
        for j in tree.query(s):
            if j <= i:
                continue
            t, h2 = hepsi[j]
            g = s.intersection(t)
            if g.is_empty:
                continue
            if g.length > 0.5:
                ust_uste += 1
                continue
            ayni = (i < len(S['G'])) == (j < len(S['G']))
            if not ayni:
                # uç noktada değmesi de kabul edilmez (farklı sistem); iç kesişme köprüsüz demektir
                kesisme += 1
    katman = sorted({e.dxf.layer for e in msp if not e.dxf.layer.startswith('ROTAS-')})
    ins = len(msp.query('INSERT'))
    print(f'{yol}\n  üst üste binen boru parçası: {ust_uste}\n  köprüsüz gidiş-dönüş kesişmesi: {kesisme}\n'
          f'  ROTAS- dışı model katmanı: {katman}\n  MTY blok referansı (INSERT): {ins}')
    a = d.audit()
    print(f'  ezdxf audit hata: {len(a.errors)}  düzeltme: {len(a.fixes)}')
    return ust_uste, kesisme, katman


if __name__ == '__main__':
    for y in sys.argv[1:]:
        denetle(y)
