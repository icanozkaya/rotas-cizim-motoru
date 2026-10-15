#!/usr/bin/env python3
"""sihhi2 — tur 6 (15.10.2026 (D) kullanıcı geri bildirimi) bağımsız ölçümleri.

    python3 motor/sihhi2/kontrol_tur6.py [DXF] [--onbellek Ks.pkl] [--json cikti.json]

DXF: kat planları ya da birleşik şerit (varsayılan proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf).
K1  hat–kolon çemberi: her pis su kolon sembolünün dış çemberi (r 10) içine giren boru (pis / temiz / sıcak) boyu = 0
    (her kolon, her kat); ayrıca pis su hattının kolona çember üstünde (≤ 1 cm) değdiği kontrol edilir.
K2  kolon merkezi betonarme kolon/perde ve havalandırma şaftı içinde değil (mimari tanıma: plan.py ile aynı).
K3  mutfakta yer süzgeci 0.
K4  daire beslemesi: zemin kattaki sayaç grubunda sayaç adedi = daire adedi = kolon şemasındaki sayaç adedi;
    her daire girişi (temiz su giriş işareti) besleme hattı + kolon (her katta aynı nokta) üzerinden sayaç grubuna bağlı;
    besleme hatları birbirini kesmez/üst üste binmez, kapı açılım alanından ve duvar/betonarmeden geçmez, ortak alanda.
"""
import json
import math
import os
import pickle
import sys
from collections import defaultdict

import ezdxf
import networkx as nx
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
KOK = os.path.dirname(os.path.dirname(BURASI))

PAFTA = {'Z': (252513.0, 254578.0), '1': (254578.0, 256617.0), '2': (256617.0, 258656.0)}
OFF = {'Z': 0.0, '1': 2034.0, '2': 4082.0}
PY0, PY1 = -444050.0, -441150.0
KOLON_R = 10.0


def kat_of(x):
    for k, (a, b) in PAFTA.items():
        if a <= x < b:
            return k
    return None


def oku(dxf):
    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()
    hat = defaultdict(list)             # kat -> [(katman, LineString)]
    ins = defaultdict(list)             # kat -> [(blok, p, e)]
    for e in msp:
        t = e.dxftype()
        if t in ('LWPOLYLINE', 'LINE', 'POLYLINE'):
            lay = e.dxf.layer.upper()
            if 'SIHHI' not in lay or 'CAP' in lay or 'YAZI' in lay or 'SEMBOL' in lay or 'NO' in lay.split('-')[-1:]:
                continue
            try:
                pts = [(p[0], p[1]) for p in (e.get_points('xy') if t == 'LWPOLYLINE' else
                                              ([e.dxf.start, e.dxf.end] if t == 'LINE' else e.points()))]
            except Exception:
                continue
            if len(pts) < 2 or not (PY0 < pts[0][1] < PY1):
                continue
            k = kat_of(pts[0][0])
            if k:
                hat[k].append((lay, LineString(pts)))
        elif t == 'INSERT':
            p = (e.dxf.insert[0], e.dxf.insert[1])
            if not (PY0 < p[1] < PY1):
                continue
            k = kat_of(p[0])
            if k:
                ins[k].append((e.dxf.name.upper(), p, e))
    return doc, hat, ins


def k1_kolon_cember(hat, ins):
    out = {}
    for k in PAFTA:
        kol = [p for ad, p, e in ins[k] if 'PIS-KOLON' in ad]
        ic, temas, toplam = [], 0, 0
        for c in kol:
            cc = Point(c).buffer(KOLON_R - 0.1, resolution=32)
            pis_deg = False
            for lay, g in hat[k]:
                if not g.intersects(Point(c).buffer(KOLON_R + 40)):
                    continue
                L = g.intersection(cc).length
                if L > 0.01:
                    ic.append(dict(kolon=[round(c[0], 1), round(c[1], 1)], katman=lay, boy=round(L, 2)))
                if 'PIS' in lay and min(Point(q).distance(Point(c)) for q in (g.coords[0], g.coords[-1])) <= KOLON_R + 1.0:
                    pis_deg = True
            temas += 1 if pis_deg else 0
            toplam += 1
        out[k] = dict(kolon=toplam, pis_cemberde_biten=temas, ic_kesisme=len(ic), ic_boy=round(sum(q['boy'] for q in ic), 2),
                      ornek=ic[:6])
    return out


def kat_bilgisi(onbellek=None):
    import plan as P
    import mimari2 as M2
    if onbellek and os.path.exists(onbellek):
        with open(onbellek, 'rb') as f:
            return P, pickle.load(f)
    A = M2.kayitlar()
    Ks = {}
    for k in PAFTA:
        K = M2.Kat(A, k)
        K.kb = M2.MB.kat_analiz(A, M2.pencere(k), k)
        Ks[k] = K
    return P, Ks


def saft_hucreleri(doc, K):
    """havalandırma şaftının GERÇEK hücresi: mimari çizgilerin (ROTAS-MIMARI*) poligonlaştırılmasından, kanal
    dairesini içeren en küçük kapalı hücre (mimari tanımanın 38x38 sentetik kutusu değil)"""
    from shapely.ops import polygonize
    msp = doc.modelspace()
    out = []
    for s in K.saftlar:
        c = s['c']
        W = box(c[0] - 70, c[1] - 70, c[0] + 70, c[1] + 70)
        segs = []
        for e in msp.query('LINE LWPOLYLINE'):
            if not e.dxf.layer.upper().startswith('ROTAS-MIMARI'):
                continue
            try:
                pts = [(p[0], p[1]) for p in (e.get_points('xy') if e.dxftype() == 'LWPOLYLINE' else [e.dxf.start, e.dxf.end])]
                if e.dxftype() == 'LWPOLYLINE' and e.closed:
                    pts.append(pts[0])
            except Exception:
                continue
            g = LineString(pts) if len(pts) > 1 else None
            if g is not None and g.intersects(W):
                segs.append(g.intersection(W))
        u = unary_union(segs)
        hs = [g for g in polygonize(u) if g.contains(Point(c)) and g.area > math.pi * s.get('r', 5) ** 2 * 1.2]
        # poligonlaşmazsa: kullanıcının şaft hücresi ölçüsü (bulunan hücreler 20x20 / 20x15) kadar kare
        out.append(min(hs, key=lambda g: g.area) if hs else Point(c).buffer(10.0, cap_style=3))
    return out


def k2_kolon_konum(P, Ks, ins, doc=None):
    out = {}
    for k, K in Ks.items():
        hucre = saft_hucreleri(doc, K) if doc is not None else [s['poly'] for s in K.saftlar]
        saft = unary_union(hucre or [Point(0, 0).buffer(0.01)])
        cols = unary_union(K.cols)
        kol = [p for ad, p, e in ins[k] if 'PIS-KOLON' in ad]
        satir = []
        for c in kol:
            pt = Point(c)
            cc = pt.buffer(KOLON_R)
            no = min(P.KOLON_MERKEZ, key=lambda n: math.dist(P.kolon_merkezi(n, K.off), c))
            satir.append(dict(no=no, merkez_saftta=bool(saft.contains(pt)), merkez_betonda=bool(cols.contains(pt)),
                              cember_saft_cm2=round(cc.intersection(saft).area, 1),
                              cember_beton_cm2=round(cc.intersection(cols).area, 1),
                              kullanici_merkezi_sapma=round(math.dist(P.kolon_merkezi(no, K.off), c), 1)))
        out[k] = dict(kolon=len(satir), merkez_saft=sum(s['merkez_saftta'] for s in satir),
                      merkez_beton=sum(s['merkez_betonda'] for s in satir), satir=satir)
    return out


def k3_mutfak_suzgec(P, Ks, ins):
    out = {}
    for k, K in Ks.items():
        mut = [r for r in K.rooms if P.mutfak_mi(r)]
        n = 0
        for ad, p, e in ins[k]:
            if 'SUZGEC' in ad and 'BALKON' not in ad and any(r['poly'].buffer(3).contains(Point(p)) for r in mut):
                n += 1
        out[k] = dict(mutfak=len(mut), mutfak_suzgec=n)
    return out


def main(argv):
    dxf = KOK + '/proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf'
    onb, cik = None, None
    i = 0
    while i < len(argv):
        if argv[i] == '--onbellek':
            onb = argv[i + 1]
            i += 2
        elif argv[i] == '--json':
            cik = argv[i + 1]
            i += 2
        else:
            dxf = argv[i]
            i += 1
    doc, hat, ins = oku(dxf)
    sonuc = dict(dxf=dxf, K1=k1_kolon_cember(hat, ins))
    P, Ks = kat_bilgisi(onb)
    sonuc['K2'] = k2_kolon_konum(P, Ks, ins, doc)
    sonuc['K3'] = k3_mutfak_suzgec(P, Ks, ins)
    try:
        import besleme as B
        sonuc['K4'] = B.kontrol(dxf, Ks, hat, ins)
    except ImportError:
        pass
    for t in ('K1', 'K2', 'K3', 'K4'):
        if t not in sonuc:
            continue
        for k, v in sonuc[t].items():
            ozet = {a: b for a, b in v.items() if a not in ('ornek', 'satir', 'detay')} if isinstance(v, dict) else v
            print(t, k, json.dumps(ozet, ensure_ascii=False))
    if cik:
        with open(cik, 'w', encoding='utf-8') as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=1)
    return sonuc


if __name__ == '__main__':
    main(sys.argv[1:])
