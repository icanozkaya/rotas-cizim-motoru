# -*- coding: utf-8 -*-
"""Kullanıcının kendi MTY yerden ısıtma devreleri (H sırası 1.-2. kat ofisleri): MTY-ETIKET dinamik blok örneklerinden
(ulabel) devre listesi -> (kat, ofis) -> [dict(no, zon, L, W, mahal, malzeme, ti, p)]  (p: S sırası, kat çerçevesinde)"""
import re
from shapely.geometry import Point
from veri import *
import ulabel

HX = ROW['H'][0] - ROW['S'][0]
_D = None


def _num(s):
    m = re.search(r'[-+]?\d+(?:[.,]\d+)?', s or '')
    return float(m.group(0).replace(',', '.')) if m else None


def devreler():
    global _D
    if _D is not None: return _D
    U = ulabel.oku()
    _D = {}
    for u in U:
        tags = {a['tag']: a['txt'] for a in u['att']}
        if 'BORU_001' not in tags or 'UZ_001' not in tags: continue
        x, y = u['p']
        if not (284700 < x < 289200 and -447827 < y < -440327): continue
        for kat in (2, 3):
            hit = None
            for k in OFIS_S1:
                if ofis_poly(k, kat, 'S').buffer(5).contains(Point(x - HX, y)):
                    hit = k; break
            if hit:
                d = dict(no=tags.get('NO1_001', ''), zon=tags.get('NO_001', ''), L=_num(tags.get('UZ_001')) or 0.0,
                         W=_num(tags.get('YER_001')), mahal=tags.get('MAHAL', '') or tags.get('MAHAL_001', ''),
                         malzeme=tags.get('MALZEMECINSI_001', ''), ti=_num(tags.get('DERECE_001')) or 20.0,
                         s=_num(tags.get('AR_001')) or 15.0, p=(x - HX - (D12[0] if kat == 3 else 0.0), y))
                _D.setdefault((kat, hit), []).append(d)
                break
    for key in _D:
        _D[key].sort(key=lambda d: (-d['p'][1], d['p'][0]))
    return _D


if __name__ == '__main__':
    D = devreler()
    for key in sorted(D): print(key, len(D[key]), [(d['no'], d['zon'], d['L'], d['W']) for d in D[key]][:3])
