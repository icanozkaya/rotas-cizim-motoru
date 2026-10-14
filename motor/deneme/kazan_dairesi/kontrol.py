# -*- coding: utf-8 -*-
"""Bağımsız teslim denetimi (DXF'i okur) — R2 (14.10.2026 (B) talimatı):
1. MTY: kullanılan MTY bloğu / MTY katmanı sayısı (0 olmalı)
2. KÖPRÜ: boru katmanlarında kavisli (bulge) atlatma sayısı (0 olmalı)
3. KESİŞME: boru-boru iç kesişmesi (uç / T bağlantısı hariç) (0 olmalı)
4. ETİKET: her cihaz numarasının (ROTAS-*-ETIKET katmanı) en yakın sembolü, XDATA 'ROTAS' NO=... değeri aynı olan
   kendi sembolü mü; numara tek mi (eşleşme %100 olmalı)
5. ELEKTRİK: SINYAL / ELEKTRIK katmanında nesne (0 olmalı)
6. Çakışma: üst üste çizgi, boru-sembol, yazı-çizgi, yazı-yazı.
Kullanım: python3 kontrol.py cikti.dxf [--ozet]"""
import math
import os
import sys
from collections import Counter

import ezdxf
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geometri as GM                       # noqa: E402
from kazan_dairesi import BORU_KATMAN       # noqa: E402

TABLO = ('ROTAS-HESAP-', 'ROTAS-PAFTA', 'ROTAS-LEJANT', 'ROTAS-ISITMA-BOLGE', 'ROTAS-KAT-BANDI', 'ROTAS-TABLO',
         'ROTAS-MIMARI')        # temsili mimari (duvar/tefriş) çakışma denetimine girmez
BORU_EK = {'ROTAS-ISITMA-GIDIS', 'ROTAS-ISITMA-DONUS'}


def _xno(e):
    try:
        for code, v in e.get_xdata('ROTAS'):
            if code == 1000 and str(v).startswith('NO='):
                return str(v)[3:]
    except Exception:
        return None
    return None


def mty_say(doc):
    msp = doc.modelspace()
    kul = Counter()

    def tara(e, d=0):
        n = e.dxf.name
        if 'MTY' in n.upper():
            kul[n] += 1
        if d < 6 and n in doc.blocks:
            for c in doc.blocks.get(n):
                if c.dxftype() == 'INSERT':
                    tara(c, d + 1)
    for e in msp.query('INSERT'):
        tara(e)
    lay = sum(1 for e in msp if e.dxf.layer.upper().startswith('MTY'))
    return kul, lay


def kopru_say(msp, boru):
    k = 0
    for e in msp.query('LWPOLYLINE'):
        if e.dxf.layer in boru:
            k += sum(1 for p in e.get_points('xyb')[:-1] if abs(p[2]) > 1e-9)
    return k


def etiket_esles(msp, etk_on='-ETIKET'):
    sem = []
    for e in msp.query('INSERT'):
        kay = []
        GM._ent_geo(e, kay, 0, 'sembol')
        if kay:
            sem.append((e, unary_union([k[2] for k in kay]), _xno(e)))
    if not sem:
        return 0, 0, []
    agac = STRtree([g for _, g, _ in sem])
    top, ok, hata = 0, 0, []
    say = Counter()
    for t in msp.query('TEXT'):
        if not t.dxf.layer.endswith(etk_on):
            continue
        s = t.dxf.text.strip()
        if not s:
            continue
        top += 1
        say[(s, round(t.dxf.insert.x / 400), round(t.dxf.insert.y / 400))] += 0
        al, p1, p2 = t.get_placement()
        p = p2 if p2 is not None and al.name not in ('LEFT', 'ALIGNED', 'FIT') else p1
        kutu = GM.yazi_kutusu((p.x, p.y), s, t.dxf.height, al, t.dxf.get('rotation', 0), t.dxf.get('width', 1.0))
        i = agac.nearest(kutu)
        e, g, no = sem[i]
        d = kutu.distance(g)
        if no == s:
            ok += 1
        else:
            hata.append((s, no, round(p.x, 1), round(p.y, 1), round(d, 1)))
    return top, ok, hata


def denetle(dxf, ayrinti=8, etk_on='-ETIKET', boru=None):
    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()
    boru = boru or (BORU_KATMAN | BORU_EK)
    ents = list(msp)
    kay = GM.model_kayit(msp, boru)
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
                if ii.geom_type == 'Point':
                    p = (ii.x, ii.y)
                    uc_i = min(math.dist(p, gi.coords[0]), math.dist(p, gi.coords[-1])) < 0.3
                    uc_j = min(math.dist(p, gj.coords[0]), math.dist(p, gj.coords[-1])) < 0.3
                    if not uc_i and not uc_j:
                        if ti == 'boru' and tj == 'boru':
                            kaydet('BORU KESİŞMESİ', i, j)
                        elif 'boru' in (ti, tj):
                            kaydet('boru-sembol kesişimi', i, j)
                        else:
                            kaydet('sembol-sembol kesişimi', i, j)
            elif ii.area > 0.5 and 'boru' in (ti, tj):
                kaydet('boru-dolu sembol', i, j)
    kul, mlay = mty_say(doc)
    kop = kopru_say(msp, boru)
    top, ok, hata = etiket_esles(msp, etk_on)
    elek = sum(1 for e in msp if any(k in e.dxf.layer.upper() for k in ('SINYAL', 'ELEKTRIK')))
    ozet = dict(MTY_blok=sum(kul.values()), MTY_katman=mlay, kopru=kop, kesisme=sorun.get('BORU KESİŞMESİ', 0),
                etiket=f'{ok}/{top}' + (f' (%{100 * ok / top:.1f})' if top else ''), elektrik=elek)
    return ozet, sorun, ornek, hata


if __name__ == '__main__':
    oz, s, o, h = denetle(sys.argv[1])
    print('ÖZET:', oz)
    print('ÇAKIŞMA:', dict(s) or 'yok')
    for k, v in o.items():
        print(' ', k, v)
    for x in h[:20]:
        print('  ETİKET EŞLEŞMEDİ:', x)
