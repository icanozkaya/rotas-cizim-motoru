# -*- coding: utf-8 -*-
"""Bağımsız çakışma denetimi (DXF'i okur): üst üste binen çizgiler, köprüsüz boru kesişimi, boru-sembol kesişimi,
yazı-çizgi ve yazı-yazı çakışması. Kullanım: python3 kontrol.py cikti.dxf"""
import os
import sys
from collections import Counter

import ezdxf
from shapely.geometry import LineString
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geometri as GM                       # noqa: E402
from kazan_dairesi import BORU_KATMAN       # noqa: E402

TABLO = ('ROTAS-HESAP-', 'ROTAS-PAFTA')


def denetle(dxf, ayrinti=8):
    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()
    ents = list(msp)
    kay = GM.model_kayit(msp, BORU_KATMAN)
    lay = [ents[s].dxf.layer for s, _, _, _ in kay]
    geos = [g for _, _, g, _ in kay]
    agac = STRtree(geos)
    sorun = Counter()
    ornek = {}

    def kaydet(tur, i, j):
        sorun[tur] += 1
        ornek.setdefault(tur, [])
        if len(ornek[tur]) < ayrinti:
            c = geos[i].intersection(geos[j]).centroid if geos[i].intersects(geos[j]) else geos[i].centroid
            ornek[tur].append((lay[i], lay[j], round(c.x, 1), round(c.y, 1)))

    for i, (si, ti, gi, ai) in enumerate(kay):
        if lay[i].startswith(TABLO):
            continue
        for j in agac.query(gi):
            if j <= i:
                continue
            sj, tj, gj, aj = kay[j]
            if si == sj or lay[j].startswith(TABLO) or not gi.intersects(gj):
                continue
            ii = gi.intersection(gj)
            yazi_i, yazi_j = ti == 'yazi', tj == 'yazi'
            if yazi_i or yazi_j:
                if ii.area > 0.5 or (not (yazi_i and yazi_j) and ii.length > 0.5):
                    kaydet('yazı-yazı' if yazi_i and yazi_j else 'yazı-çizgi', i, j)
                continue
            if isinstance(gi, LineString) and isinstance(gj, LineString):
                if ii.length > 0.5:
                    kaydet('üst üste çizgi', i, j)
                    continue
                if ai or aj:              # köprü kavsi
                    continue
                if ii.geom_type == 'Point':
                    p = (ii.x, ii.y)
                    uc_i = min(GM.math.dist(p, gi.coords[0]), GM.math.dist(p, gi.coords[-1])) < 0.3
                    uc_j = min(GM.math.dist(p, gj.coords[0]), GM.math.dist(p, gj.coords[-1])) < 0.3
                    if not uc_i and not uc_j:
                        if ti == 'boru' and tj == 'boru':
                            kaydet('köprüsüz boru kesişimi', i, j)
                        elif 'boru' in (ti, tj):
                            kaydet('boru-sembol kesişimi', i, j)
                        else:
                            kaydet('sembol-sembol kesişimi', i, j)
            elif ii.area > 0.5 and 'boru' in (ti, tj):
                kaydet('boru-dolu sembol', i, j)
    return sorun, ornek


if __name__ == '__main__':
    s, o = denetle(sys.argv[1])
    print('SORUN:', dict(s) or 'yok')
    for k, v in o.items():
        print(' ', k, v)
