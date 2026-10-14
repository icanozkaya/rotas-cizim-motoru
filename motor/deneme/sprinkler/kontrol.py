# -*- coding: utf-8 -*-
"""Üretilen DXF'in bağımsız kontrolü (dosyadan yeniden okunur):
1) katman adları ROTAS- (MTY blok iç katmanları hariç); 2) boru-boru çakışma / ara noktada kesişme;
3) boru ve başlık betonarme kolonu kesmez (gungoren/kolon_kontrol.py mantığı); 4) yazı-yazı, yazı-boru,
yazı-başlık, yazı-duvar çakışması; 5) her boru zincirinde DN etiketi (sayım); 6) başlıklar arası ≥ 2 m."""
import math, re
import ezdxf
from shapely.geometry import LineString, Polygon, Point, box
from shapely.strtree import STRtree
from shapely.ops import unary_union
from cizim import tw, th

PLAN_YAZI = ('ROTAS-YANGIN-SPR-CAP', 'ROTAS-YANGIN-DUGUM', 'ROTAS-MIMARI-MAHAL', 'ROTAS-YANGIN-HIDROLIK-ALAN',
             'ROTAS-YANGIN-VANA', 'ROTAS-YANGIN-KOLON')


def yazi_kutu(t):
    h = t.dxf.height
    s = t.dxf.text
    p = t.dxf.align_point if t.dxf.halign or t.dxf.valign else t.dxf.insert
    w, hh = tw(s, h) - h * 0.4, h * 1.1        # maske payı olmadan net kutu
    if abs(t.dxf.rotation) < 1:
        return box(p.x - w / 2, p.y - hh / 2, p.x + w / 2, p.y + hh / 2)
    return box(p.x - hh / 2, p.y - w / 2, p.x + hh / 2, p.y + w / 2)


def kontrol(dosya, plan_kutu, zincir_sayisi):
    d = ezdxf.readfile(dosya)
    msp = d.modelspace()
    rap = {}
    px0, py0, px1, py1 = plan_kutu
    ici = lambda g: g.intersects(box(px0 - 50, py0 - 50, px1 + 50, py1 + 50))
    # 1) katmanlar
    kullanilan = {e.dxf.layer for e in msp} | {e.dxf.layer for b in d.blocks for e in b}
    rap['yanlis_katman'] = sorted(l for l in kullanilan if l not in ('0', 'Defpoints') and not l.startswith('ROTAS-'))
    # 2) borular
    bor = []
    for e in msp.query('LWPOLYLINE[layer=="ROTAS-YANGIN-SPR-BORU"]'):
        pts = [(p[0], p[1]) for p in e.get_points()]
        g = LineString(pts)
        if ici(g):
            bor.append((g, pts))
    geo = [b[0] for b in bor]
    tree = STRtree(geo)
    cak, kes = [], []
    for i, g in enumerate(geo):
        for j in tree.query(g.buffer(0.6)):
            j = int(j)
            if j <= i:
                continue
            h = geo[j]
            x = g.intersection(h.buffer(0.3))
            if x.is_empty:
                continue
            if x.length > 1.0:
                cak.append((i, j, round(x.length, 1)))
                continue
            uclar = [Point(bor[i][1][0]), Point(bor[i][1][-1]), Point(bor[j][1][0]), Point(bor[j][1][-1])]
            c = x.centroid
            ui = min(c.distance(uclar[0]), c.distance(uclar[1]))
            uj = min(c.distance(uclar[2]), c.distance(uclar[3]))
            if ui > 1.0 or uj > 1.0:
                kes.append((i, j, (round(c.x), round(c.y))))
    rap['boru_cakisma'] = cak
    rap['boru_kesisme'] = kes
    # 3) kolonlar
    kol = []
    for e in msp.query('LWPOLYLINE[layer=="ROTAS-MIMARI-KOLON"]'):
        q = [(p[0], p[1]) for p in e.get_points()]
        if len(q) >= 4:
            g = Polygon(q)
            if ici(g):
                kol.append(g)
    K = unary_union(kol)
    rap['boru_kolon'] = [(round(g.intersection(K).length, 1)) for g in geo if g.intersection(K).length > 0.5]
    bas = [Point(e.dxf.insert.x, e.dxf.insert.y) for e in msp.query('INSERT[layer=="ROTAS-YANGIN-SPRINKLER"]')
           if ici(Point(e.dxf.insert.x, e.dxf.insert.y))]
    rap['bas_kolon'] = [(round(p.x), round(p.y)) for p in bas if p.buffer(12.5).intersects(K)]
    dmin = min((a.distance(b) for i, a in enumerate(bas) for b in bas[i + 1:]), default=0)
    rap['bas_min_aralik_cm'] = round(dmin, 1)
    # 4) yazılar
    yaz = []
    for t in msp.query('TEXT'):
        if t.dxf.layer not in PLAN_YAZI:
            continue
        k = yazi_kutu(t)
        if ici(k):
            yaz.append((k, t.dxf.text, t.dxf.layer))
    yy = [y[0] for y in yaz]
    yt = STRtree(yy)
    yc = []
    for i, k in enumerate(yy):
        for j in yt.query(k):
            j = int(j)
            if j > i and k.intersection(yy[j]).area > 1.0:
                yc.append((yaz[i][1], yaz[j][1]))
    rap['yazi_yazi'] = yc
    rap['yazi_boru'] = [y[1] for y in yaz for g in geo if y[0].intersects(g)]
    rap['yazi_bas'] = [y[1] for y in yaz for p in bas if y[0].intersects(p.buffer(12.5))]
    duv = [LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
           for e in msp.query('LINE[layer=="ROTAS-MIMARI-DUVAR"]')]
    rap['yazi_duvar'] = [y[1] for y in yaz for g in duv if y[0].intersects(g)]
    # 5) etiket sayısı
    dn = [t for t in msp.query('TEXT[layer=="ROTAS-YANGIN-SPR-CAP"]') if re.fullmatch(r'DN\d+', t.dxf.text)
          and ici(yazi_kutu(t))]
    rap['dn_etiket'] = len(dn)
    rap['boru_zinciri'] = zincir_sayisi
    rap['wipeout'] = len(msp.query('WIPEOUT'))
    rap['yazi_sayisi'] = len(msp.query('TEXT'))
    rap['dxf_surum'] = d.dxfversion
    hatalar = sum(len(rap[k]) for k in ('yanlis_katman', 'boru_cakisma', 'boru_kesisme', 'boru_kolon', 'bas_kolon',
                                         'yazi_yazi', 'yazi_boru', 'yazi_bas', 'yazi_duvar'))
    if rap['dn_etiket'] < zincir_sayisi:
        hatalar += 1
    if dmin < 199.9:
        hatalar += 1
    rap['HATA'] = hatalar
    return rap
