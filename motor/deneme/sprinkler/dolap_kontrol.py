# -*- coding: utf-8 -*-
"""Dolaplı planın bağımsız kontrolü (DXF dosyadan yeniden okunur). sprinkler kontrol.py'ye ek olarak:
1) dolap borusu: betonarme kolon / duvar kesmez; sprinkler borusu ile üst üste binmez ve KESİŞMEZ (R2: köprü/atlatma yok, kesişme 0)
2) dolap gövdesi kolon ve kapı açıklığına binmez
3) dolap yazıları (çap, YD no, YG balon, merdiven) diğer yazı / boru / başlık / duvar / dolap sembolü ile çakışmaz
4) her dolap boru zincirinde DN etiketi
5) KAPSAMA YENİDEN HESABI: dolap konumları DXF'teki INSERT'lerden okunur, yürüme yolu ile yeniden ölçülür
6) dolaplar arası en fazla mesafe"""
import math
import re
import numpy as np
import ezdxf
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union
from kontrol import yazi_kutu
from dolap import Plan, kapsama_raporu
from dolap_cizim import DOLAP_BLOK

DOLAP_YAZI = ('ROTAS-YANGIN-DOLAP-CAP', 'ROTAS-YANGIN-DOLAP-YAZI', 'ROTAS-YANGIN-DOLAP-KOLON')
TUM_YAZI = DOLAP_YAZI + ('ROTAS-YANGIN-SPR-CAP', 'ROTAS-YANGIN-DUGUM', 'ROTAS-MIMARI-MAHAL', 'ROTAS-YANGIN-HIDROLIK-ALAN',
                         'ROTAS-YANGIN-VANA', 'ROTAS-YANGIN-KOLON')


def _boru_oku(msp, lay, ici):
    out = []
    for e in msp.query(f'LWPOLYLINE[layer=="{lay}"]'):
        v = [(p[0], p[1], p[2]) for p in e.get_points('xyb')]
        pts = [(p[0], p[1]) for p in v]
        g = LineString(pts)
        if ici(g):
            kopru = []
            for a, b in zip(v[:-1], v[1:]):
                if abs(a[2]) > 1e-6:
                    kopru.append(box(min(a[0], b[0]) - 1, min(a[1], b[1]) - 1, max(a[0], b[0]) + 1, max(a[1], b[1]) + 1)
                                 .buffer(0.5))
            out.append((g, pts, kopru))
    return out


def kontrol_dolap(dosya, P, D, k):
    d = ezdxf.readfile(dosya)
    msp = d.modelspace()
    x0, y0, x1, y1 = P['dis_hat']
    tum = [x0, y0, x1, y1]
    for s in D.get('merdivenler', []) + [e for e in D.get('cikislar', []) if e.get('rect')]:
        r = s['rect']
        tum = [min(tum[0], r[0]), min(tum[1], r[1]), max(tum[2], r[2]), max(tum[3], r[3])]
    PK = box(tum[0] - 60, tum[1] - 60, tum[2] + 60, tum[3] + 60)
    ici = lambda g: g.intersects(PK)
    rap = {}
    dol = _boru_oku(msp, 'ROTAS-YANGIN-DOLAP-BORU', ici)
    spr = _boru_oku(msp, 'ROTAS-YANGIN-SPR-BORU', ici)
    kol = unary_union([Polygon(q) for q in ([(c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3])] for c in P.get('kolonlar', []))])
    duv = [LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]) for e in msp.query('LINE[layer=="ROTAS-MIMARI-DUVAR"]')]
    # 1) borular
    rap['dolap_boru_kolon'] = [round(g.intersection(kol).length, 1) for g, _, _ in dol if g.intersection(kol).length > 0.5]
    rap['dolap_boru_duvar'] = [(round(x.centroid.x), round(x.centroid.y)) for g, _, _ in dol for w in duv
                               for x in [g.intersection(w)] if not x.is_empty]
    ust, kes, kes_spr = [], [], []
    rap['dolap_kopru_sayisi'] = sum(len(k_) for _, _, k_ in dol)
    for i, (g, pts, kop) in enumerate(dol):
        for h, pts2, _ in spr:
            x = g.intersection(h.buffer(0.3))
            if x.is_empty:
                continue
            if x.length > 1.0:
                ust.append((i, round(x.length, 1)))
                continue
            c = x.centroid
            kes_spr.append((round(c.x), round(c.y)))          # R2: köprü yok, her kesişme hatadır
        for j, (h, pts2, kop2) in enumerate(dol):
            if j <= i:
                continue
            x = g.intersection(h.buffer(0.3))
            if x.is_empty:
                continue
            if x.length > 1.0:
                ust.append((i, j, round(x.length, 1)))
                continue
            c = x.centroid
            uclar = [Point(pts[0]), Point(pts[-1]), Point(pts2[0]), Point(pts2[-1])]
            if min(c.distance(u) for u in uclar) > 1.0 and not any(b.contains(c) for b in kop + kop2):
                # T bağlantı: bir zincirin ucu diğerinin üzerinde olabilir
                if not (Point(pts[0]).distance(h) < 1 or Point(pts[-1]).distance(h) < 1 or
                        Point(pts2[0]).distance(g) < 1 or Point(pts2[-1]).distance(g) < 1):
                    kes.append((round(c.x), round(c.y)))
    rap['dolap_boru_ust_uste'] = ust
    rap['dolap_boru_kopru_disi_kesisme'] = kes
    rap['dolap_spr_kesisme'] = kes_spr
    # 2) dolap gövdeleri
    ins = [e for e in msp.query('INSERT') if e.dxf.name == 'ROTAS-YANGIN-DOLABI-PLAN' and ici(Point(e.dxf.insert.x, e.dxf.insert.y))]
    govde, orj = [], []
    for e in ins:
        a = math.radians(e.dxf.rotation)
        c, s = math.cos(a), math.sin(a)
        q = [(e.dxf.insert.x + x * c - y * s, e.dxf.insert.y + x * s + y * c) for x, y in ((-36, -32.8), (36, -32.8), (36, -12.8), (-36, -12.8))]
        govde.append(Polygon(q))
        n = (-s, c)
        orj.append((e.dxf.insert.x - n[0] * 2.8, e.dxf.insert.y - n[1] * 2.8))
    rap['dolap_kolon'] = [i for i, g in enumerate(govde) if g.intersection(kol).area > 1.0]
    kapi = []
    for m in P['mahaller'] + D.get('merdivenler', []):
        if m.get('kapi'):
            p, w = m['kapi']['p'], m['kapi'].get('w', 90.0)
            kapi.append(box(p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2))
    rap['dolap_kapi'] = [i for i, g in enumerate(govde) for b in kapi if g.intersection(b).area > 1.0]
    # 3) yazılar
    yaz = []
    for t in msp.query('TEXT'):
        if t.dxf.layer in TUM_YAZI:
            kb = yazi_kutu(t)
            if ici(kb):
                yaz.append((kb, t.dxf.text, t.dxf.layer))
    benim = [y for y in yaz if y[2] in DOLAP_YAZI or (y[2] == 'ROTAS-MIMARI-MAHAL' and
                                                      any(y[1] == s['ad'] for s in D.get('merdivenler', []) + D.get('cikislar', [])))]
    yc = []
    for i, a in enumerate(benim):
        for b in yaz:
            if b is a:
                continue
            if a[0].intersection(b[0]).area > 1.0:
                pair = tuple(sorted((a[1], b[1])))
                if pair not in yc:
                    yc.append(pair)
    rap['dolap_yazi_yazi'] = yc
    borular = [g for g, _, _ in dol] + [g for g, _, _ in spr]
    rap['dolap_yazi_boru'] = [y[1] for y in benim for g in borular if y[0].intersects(g)]
    bas = [Point(e.dxf.insert.x, e.dxf.insert.y).buffer(12.5) for e in msp.query('INSERT[layer=="ROTAS-YANGIN-SPRINKLER"]')]
    rap['dolap_yazi_bas'] = [y[1] for y in benim for p in bas if y[0].intersects(p)]
    rap['dolap_yazi_duvar'] = [y[1] for y in benim for g in duv if y[0].intersects(g)]
    rap['yazi_dolap_sembol'] = [y[1] for y in yaz for g in govde if y[0].intersection(g).area > 0.5]
    rap['boru_dolap_govde'] = [i for i, g in enumerate(govde) for h in [b[0] for b in spr] if h.intersects(g)]
    # 4) çap etiketleri
    dn = [t for t in msp.query('TEXT[layer=="ROTAS-YANGIN-DOLAP-CAP"]') if re.fullmatch(r'DN\d+', t.dxf.text)]
    rap['dolap_dn_etiket'] = len(dn)
    rap['dolap_boru_zinciri'] = len(dol)
    n_yg = len([t for t in msp.query('TEXT[layer=="ROTAS-YANGIN-DOLAP-KOLON"]') if re.fullmatch(r'YG\d+', t.dxf.text)
                and ici(yazi_kutu(t))])
    rap['dolap_dn_etiket'] -= n_yg          # YG balonlarındaki DN yazıları boru zinciri etiketi sayılmaz
    # 5) kapsama yeniden hesabı
    pl = Plan(P, D, k)
    R = (k['hortum_m'] + k['jet_m']) * 100.0
    dug = [pl.dugum(o) for o in orj]
    H = pl.hedef_dugum
    kap = np.zeros(len(H), bool)
    if dug and None not in dug:
        Dm = pl.mesafe(dug)
        for i in range(len(dug)):
            kap |= Dm[i, H] <= R
        nn = [min((Dm[i, dug[j]] for j in range(len(dug)) if j != i), default=0) / 100.0 for i in range(len(dug))]
    else:
        nn = []
    kr = kapsama_raporu(pl, kap)
    rap['dolap_sayisi'] = len(ins)
    rap['kapsama_orani'] = round(kr['oran'], 4)
    rap['kapsanmayan_m2'] = round(kr['kapsanmayan_m2'], 2)
    amax = k['aralik_sprinkler_m'] if D.get('sprinkler', True) else k['aralik_m']
    rap['dolap_arasi_max_m'] = round(max(nn), 1) if nn else 0.0
    hata = sum(len(rap[x]) for x in ('dolap_boru_kolon', 'dolap_boru_duvar', 'dolap_boru_ust_uste', 'dolap_boru_kopru_disi_kesisme',
                                       'dolap_kolon', 'dolap_kapi', 'dolap_yazi_yazi', 'dolap_yazi_boru', 'dolap_yazi_bas',
                                       'dolap_yazi_duvar', 'yazi_dolap_sembol', 'boru_dolap_govde', 'dolap_spr_kesisme'))
    hata += rap['dolap_kopru_sayisi']
    if rap['dolap_dn_etiket'] < rap['dolap_boru_zinciri']:
        hata += 1
    if nn and max(nn) > amax + 1e-6:
        hata += 1
    rap['DOLAP_HATA'] = hata
    rap['kapsama_eksik_uyari'] = kr['kapsanmayan_m2'] > 0     # rapor edilir (hata değil): kapsanmayan alan tablosu
    return rap
