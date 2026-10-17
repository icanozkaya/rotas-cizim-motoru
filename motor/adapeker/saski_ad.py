# -*- coding: utf-8 -*-
"""Adapeker — SASKİ ALTYAPI (pis su) PLANI + VAZİYET.

Mantık (STANDART_KURALLAR_ALTYAPI_SARNIC.md, SASKİ 16.10.2026): pis su kolonları zemin kat planından; rögarlar BİNA
DIŞINDA cepheye paralel hat üzerinde (cepheden ~1,5 m); kolon → rögar branşmanı cepheye dik düz hat (komşu kolonlar tek
branşmanda); rögarlar ana hatla PB'ye; PB en yakın yola (güney, 10,00 m yol — parsel girişi). Etiketler "70x70 / h:-70cm",
"Ø150 / %1 EĞİM"; kanal bağlantı kotu belediyeden (yol kotu −80 cm notu).
Altyapı planı zemin kat koordinatında (kolonlar dosyada); vaziyet mimarinin yerleşim planı koordinatında (ölçek 0,5).
"""
import os, sys, math, json
BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
from ortak_ad import yeni_doc, T, PL, mimari_altlik, antet, KOK, CIKIS, M
from shapely.geometry import Polygon

KAT = {'ROTAS-ALTYAPI-PIS-SU': (6, 'Continuous'), 'ROTAS-ALTYAPI-ROGAR': (5, 'Continuous'), 'ROTAS-ALTYAPI-YAZI': (7, 'Continuous'),
       'ROTAS-ALTYAPI-OK': (6, 'Continuous'), 'ROTAS-ALTYAPI-PARSEL': (3, 'Continuous'), 'ROTAS-ALTYAPI-YOL': (8, 'Continuous'),
       'ROTAS-ALTYAPI-BINA': (7, 'Continuous'), 'ROTAS-ALTYAPI-KANAL': (1, 'Continuous'), 'ROTAS-PAFTA': (144, 'Continuous'),
       'ROTAS-PAFTA-YAZI': (7, 'Continuous'), 'ROTAS-SIHHI-KOLON': (6, 'Continuous')}
LP, LR, LY, LO = 'ROTAS-ALTYAPI-PIS-SU', 'ROTAS-ALTYAPI-ROGAR', 'ROTAS-ALTYAPI-YAZI', 'ROTAS-ALTYAPI-OK'


# vaziyet (mimari yerleşim planı, 1 birim = 2 cm) <-> zemin kat planı (cm)
def v2p(p):
    return (-554 + 2 * (p[0] + 2932), -1572 + 2 * (p[1] + 2310))


def p2v(p):
    return ((p[0] + 554) / 2 - 2932, (p[1] + 1572) / 2 - 2310)


PARSEL_V = [(-3262, -2181), (-2352, -2223), (-2173, -2231), (-2182, -3290), (-2361, -3287), (-3304, -3273)]
PARSEL = [v2p(p) for p in PARSEL_V]
Y_ROG = -3210.0            # rögar hattı (balkon / giriş cephesinden ~1,5 m)
Y_PB = -3470.0             # parsel bacası (güney sınırından ~0,5 m içeride)
Y_ROG_K = -1440.0          # kuzey rögar hattı (ODA cephesi -1578'den ~1,4 m; kuzey bahçe dar → orta baca PB2)
Y_PB_K = -1395.0           # kuzey parsel bacası (kuzey sınırından ~0,3 m içeride)


def ag():
    S = json.load(open(os.path.join(CIKIS, 'sihhi_model.json')))['kolonlar']
    kol = {v['gno']: tuple(v['xy']) for d in S.values() for v in d.values()}
    # İki ağ (kolon hangi cepheye yakınsa): banyo kolonları P1/P2 - P4/P5 kuzey cepheye (~6 m), mutfak kolonları P3/P6
    # güney cepheye (~2,5 m). Her ağ kendi parsel bacasına: kuzey PB2 → 7,00 m yol, güney PB1 → 10,00 m yol.
    # yön -1: güney (rögar hattı y < bina), +1: kuzey
    aglar = [dict(ad='AĞ-1 (GÜNEY)', yon=-1, y_rog=Y_ROG, pb=('PB1', (-124.0, Y_PB)),
                  gruplar=[('R1', ['P3'], -305.0), ('R2', [], -124.0), ('R3', ['P6'], 57.0)]),
             dict(ad='AĞ-2 (KUZEY)', yon=1, y_rog=Y_ROG_K, pb=('PB2', (-124.0, Y_ROG_K)), pb_orta=True,
                  gruplar=[('R4', ['P1', 'P2'], -305.0), ('PB2', [], -124.0), ('R5', ['P4', 'P5'], 57.0)])]
    return kol, aglar


def ok(m, a, b, t=0.5):
    x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    h = m.add_hatch(color=6, dxfattribs={'layer': LO})
    h.set_solid_fill(color=6)
    h.paths.add_polyline_path([(x + ux * 10, y + uy * 10), (x - ux * 8 - uy * 6, y - uy * 8 + ux * 6),
                               (x - ux * 8 + uy * 6, y - uy * 8 - ux * 6)], is_closed=True)


def rogar(m, c, ad, olcu='70x70', h='h:-70cm', s=1.0):
    r = 35 * s
    PL(m, [(c[0] - r, c[1] - r), (c[0] + r, c[1] - r), (c[0] + r, c[1] + r), (c[0] - r, c[1] + r)], LR, True, 1.5 * s)
    m.add_circle(c, 25 * s, dxfattribs={'layer': LR})
    T(m, c[0], c[1], ad, 18 * s, 'MC', LY)
    T(m, c[0] - r - 6 * s, c[1] - r - 4 * s, olcu, 11 * s, 'TR', LY)
    T(m, c[0] - r - 6 * s, c[1] - r - 20 * s, h, 11 * s, 'TR', LY)


def etiket(m, a, b, s1, s2, sc=1.0):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    yatay = abs(b[0] - a[0]) >= abs(b[1] - a[1])
    if yatay:
        T(m, mx, my + 8 * sc, s1, 10 * sc, 'BC', LY)
        T(m, mx, my - 8 * sc, s2, 10 * sc, 'TC', LY)
    else:
        T(m, mx - 8 * sc, my, s1, 10 * sc, 'BC', LY, rot=90)
        T(m, mx + 8 * sc, my, s2, 10 * sc, 'TC', LY, rot=90)


def ciz(m, donus=None, sc=1.0, tam=True):
    f = donus or (lambda p: p)
    kol, aglar = ag()
    KANAL = {}
    # parsel, yollar
    PL(m, [f(p) for p in PARSEL], 'ROTAS-ALTYAPI-PARSEL', True, 2 * sc)
    alt_a, alt_b = PARSEL[5], PARSEL[3]
    ust_a, ust_b = PARSEL[0], PARSEL[2]
    for (a, b, gen, ad, isaret) in ((alt_a, alt_b, 1000, 'YOL 10,00 m (SASKİ ANA KANALI Ø200)', -1), (ust_a, ust_b, 700, 'YOL 7,00 m (SASKİ ANA KANALI Ø200)', 1)):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * isaret, dx / L * isaret
        if ny * isaret < 0:
            nx, ny = -nx, -ny
        a2 = (a[0] + nx * gen, a[1] + ny * gen); b2 = (b[0] + nx * gen, b[1] + ny * gen)
        m.add_lwpolyline([f((a[0] - dx / L * 300, a[1] - dy / L * 300)), f((b[0] + dx / L * 300, b[1] + dy / L * 300))], dxfattribs={'layer': 'ROTAS-ALTYAPI-YOL'})
        m.add_lwpolyline([f((a2[0] - dx / L * 300, a2[1] - dy / L * 300)), f((b2[0] + dx / L * 300, b2[1] + dy / L * 300))], dxfattribs={'layer': 'ROTAS-ALTYAPI-YOL'})
        c = ((a[0] + b[0] + a2[0] + b2[0]) / 4, (a[1] + b[1] + a2[1] + b2[1]) / 4)
        T(m, *f((c[0] + 350, c[1])), ad, 22 * sc, 'MC', LY)
        ka, kb = (a[0] + nx * gen / 2, a[1] + ny * gen / 2), (b[0] + nx * gen / 2, b[1] + ny * gen / 2)
        m.add_lwpolyline([f(ka), f(kb)], dxfattribs={'layer': 'ROTAS-ALTYAPI-KANAL', 'const_width': 3 * sc})
        KANAL[isaret] = (ka, kb)
    # bina dış hattı
    B = M.bina_poly('Z').simplify(4)
    PL(m, [f(p) for p in B.exterior.coords], 'ROTAS-ALTYAPI-BINA', True, 1.5 * sc)
    if not tam:
        T(m, *f((-124, -2300)), '3 KATLI BETONARME MESKEN\n±0,00 = +30,00', 18 * sc, 'MC', LY)
    rog = {}
    for A in aglar:
        yon = A['yon']
        for rn, ks, x in A['gruplar']:
            rc = (x, A['y_rog'])
            rog[rn] = rc
            ys = []
            for kn in ks:
                c = kol[kn]
                m.add_circle(f(c), 10 * sc, dxfattribs={'layer': 'ROTAS-SIHHI-KOLON'})
                T(m, *f((c[0] + 14, c[1] + 14)), kn, 14 * sc, 'BL', LY)
                if abs(c[0] - x) > 90:                       # uzak kolon: kolondan dik yatay ile branşmana
                    m.add_lwpolyline([f(c), f((x, c[1]))], dxfattribs={'layer': LP})
                    ok(m, f(c), f((x, c[1])), 0.5)
                    ys.append(c[1])
                elif abs(c[0] - x) > 1:                     # kolondan kısa 45°
                    d = abs(c[0] - x)
                    yy = c[1] + yon * d
                    m.add_lwpolyline([f(c), f((x, yy))], dxfattribs={'layer': LP})
                    ys.append(yy)
                else:
                    ys.append(c[1])
            if ys:
                y0 = min(ys) if yon > 0 else max(ys)
                y_bit = rc[1] - yon * 35
                m.add_lwpolyline([f((x, y0)), f((x, y_bit))], dxfattribs={'layer': LP, 'const_width': 2 * sc})
                ok(m, f((x, y0)), f((x, y_bit)), 0.85)
                ym = y_bit - yon * 120
                etiket(m, f((x, ym + 40)), f((x, ym - 40)), 'Ø125', '%1 EĞİM', sc)
            if not (A.get('pb_orta') and rn == A['pb'][0]):
                rogar(m, f(rc), rn, s=sc)
        # ana hat: kenar rögarlar → orta toplayıcı → PB
        g = A['gruplar']
        orta = rog[g[1][0]]
        for rn in (g[0][0], g[2][0]):
            a_ = rog[rn]
            a2 = (a_[0] + (35 if a_[0] < orta[0] else -35), a_[1]); b2 = (orta[0] + (-35 if a_[0] < orta[0] else 35), orta[1])
            m.add_lwpolyline([f(a2), f(b2)], dxfattribs={'layer': LP, 'const_width': 3 * sc})
            ok(m, f(a2), f(b2))
            etiket(m, f(a2), f(b2), 'Ø150', '%1 EĞİM', sc)
        pbn, pb = A['pb']
        if not A.get('pb_orta'):
            a2, b2 = (orta[0], orta[1] + yon * 35), (pb[0], pb[1] - yon * 35)
            m.add_lwpolyline([f(a2), f(b2)], dxfattribs={'layer': LP, 'const_width': 3 * sc})
            ok(m, f(a2), f(b2))
        rogar(m, f(pb), pbn, '70x70', 'h:-100cm', s=sc)
        # PB → yol kanalı
        k0, k1 = KANAL[yon]
        t = (pb[0] - k0[0]) / (k1[0] - k0[0])
        ky = k0[1] + (k1[1] - k0[1]) * t
        m.add_lwpolyline([f((pb[0], pb[1] + yon * 35)), f((pb[0], ky))], dxfattribs={'layer': LP, 'const_width': 3 * sc})
        ok(m, f((pb[0], pb[1] + yon * 35)), f((pb[0], ky)))
        etiket(m, f((pb[0] + 0, (pb[1] + ky) / 2 + 40)), f((pb[0], (pb[1] + ky) / 2 - 40)), 'Ø150', '%2 EĞİM', sc)
        m.add_circle(f((pb[0], ky)), 30 * sc, dxfattribs={'layer': 'ROTAS-ALTYAPI-KANAL'})
        T(m, *f((pb[0] + 40, ky + yon * 45)), 'SASKİ ANA KANAL BACASI (Ø200) - bağlantı kotu ve izni SASKİ\'den', 11 * sc, 'BL' if yon > 0 else 'TL', LY)
        T(m, *f((pb[0] + 260, pb[1] + yon * 10)), '%s → %s: PARSEL BACASI (bağlantı kotu = yol kotu −80 cm)' % (A['ad'], pbn), 10 * sc, 'ML', LY)
    T(m, *f((-1100, -3420)), 'KK +29,80 [−0,20] (parsel girişi)', 11 * sc, 'BL', LY)
    return rog


def main():
    doc = yeni_doc(KAT)
    m = doc.modelspace()
    # ---- altyapı planı (zemin kat koordinatı, 1/50): mimariden yalnız kolonlar + bina dış hattı
    mimari_altlik(m, katlar=('Z',), sadece=('YLZ-KOLON', 'YLZ-AKS'), yazi=False, pad=150)
    ciz(m, tam=True)
    x0 = -1400
    T(m, -124, -3700, 'ALTYAPI (PİS SU) PLANI', 34, 'MC', 'ROTAS-PAFTA-YAZI')
    T(m, -124, -3745, 'ÖLÇEK : 1 / 50', 22, 'MC', 'ROTAS-PAFTA-YAZI')
    notlar = ['NOTLAR:',
              '1- Pis su kolonları (P1..P6) temel seviyesinde temizleme kapaklı olarak Ø125 %1 eğimle en yakın cephedeki rögarlara bağlanacaktır (banyolar kuzey AĞ-2, mutfaklar güney AĞ-1).',
              '2- Rögarlar 70x70 cm iç ölçülü, betonarme, pis su geçirmez, dökme demir kapaklı yapılacaktır.',
              '3- Rögarlar arası Ø150 PVC (SN8) %1 eğimle döşenecek, parsel bacası SASKİ ana kanalına bağlanacaktır.',
              '4- Parsel bacası bağlantı kotu ve izni SASKİ Genel Müdürlüğü\'nden alınacak, kanal durum belgesine uyulacaktır.',
              '5- Yağmur suyu hatları pis su rögarlarına ve parsel bacasına bağlanmayacaktır.']
    for i, s in enumerate(notlar):
        T(m, x0, -3820 - i * 26, s, 13 if i else 16, 'BL', 'ROTAS-PAFTA-YAZI')
    rogar_tablo(m, 300, -3800)
    # ---- vaziyet (mimarinin yerleşim planı koordinatında, 1/100 — çizim birimi 2 cm)
    ciz(m, donus=p2v, sc=0.5, tam=False)
    vx, vy = p2v((-124, -3740))
    T(m, vx, vy, 'VAZİYET - ALTYAPI BAĞLANTI PLANI', 17, 'MC', 'ROTAS-PAFTA-YAZI')
    T(m, vx, vy - 22, 'ÖLÇEK : 1 / 100', 11, 'MC', 'ROTAS-PAFTA-YAZI')
    antet(m, 900, -4250, 'SASKİ ALTYAPI (PİS SU) VE VAZİYET PLANI')
    yol = os.path.join(CIKIS, 'ADAPEKER_SASKI_ALTYAPI_VAZIYET.dxf')
    doc.saveas(yol)
    print('kaydedildi', yol)


def rogar_tablo(m, x, y):
    sat = [('R1', 'P3 (D1-D3-D5 mutfak)', '70x70', '-70', 'Ø150 %1 → R2'),
           ('R2', 'R1 + R3 toplayıcı', '70x70', '-75', 'Ø150 %1 → PB1'),
           ('R3', 'P6 (D2-D4-D6 mutfak)', '70x70', '-70', 'Ø150 %1 → R2'),
           ('PB1', 'parsel bacası (güney)', '70x70', '-100', 'Ø150 → 10 m yol Ø200'),
           ('R4', 'P1+P2 (D1-D3-D5 banyolar, ÇM)', '70x70', '-70', 'Ø150 %1 → PB2'),
           ('R5', 'P4+P5 (D2-D4-D6 banyolar, ÇM)', '70x70', '-70', 'Ø150 %1 → PB2'),
           ('PB2', 'parsel bacası (kuzey, R4+R5)', '70x70', '-100', 'Ø150 → 7 m yol Ø200')]
    gen = [80, 420, 100, 100, 260]
    X = [x]
    for g in gen:
        X.append(X[-1] + g)
    T(m, x, y + 15, 'RÖGAR ÇİZELGESİ', 16, 'BL', 'ROTAS-PAFTA-YAZI')
    yy = y
    for row in [('NO', 'BAĞLANAN', 'ÖLÇÜ', 'h (cm)', 'ÇIKIŞ')] + sat:
        m.add_line((x, yy), (X[-1], yy), dxfattribs={'layer': 'ROTAS-PAFTA-YAZI'})
        for i, s in enumerate(row):
            T(m, (X[i] + X[i + 1]) / 2, yy - 15, s, 11, 'MC', 'ROTAS-PAFTA-YAZI')
        yy -= 30
    m.add_line((x, yy), (X[-1], yy), dxfattribs={'layer': 'ROTAS-PAFTA-YAZI'})
    for xx in X:
        m.add_line((xx, y), (xx, yy), dxfattribs={'layer': 'ROTAS-PAFTA-YAZI'})


if __name__ == '__main__':
    main()
