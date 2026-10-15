# -*- coding: utf-8 -*-
"""2750/7 A-B blok SIHHİ TESİSAT — pafta birleştirme (yalnız DXF, R2010/AC1024, cm).

    python3 motor/ab2750/sihhi_proje.py          # tasarım (model_A/B.pkl)
    python3 motor/ab2750/sihhi_pafta.py          # -> proje/ab2750/AB2750_SIHHI_TESISAT.dxf

Her blok bir pafta sırası (B blok üstte, A blok altta); sıra (soldan sağa): ROTAŞ anteti, YERLEŞİM PLANI, ALTYAPI
(TEMEL) PLANI, kat planları (mimari koordinatında, A blok bodrum dahil), ÇATI PLANI, AÇILIMLI KOLON ŞEMASI (+ rögar
şeması, yağmur şeması), HESAPLAR, SIHHİ DETAYLAR (+ WC havalandırma izometrisi). Planlarda mimari altlık ROTAS-MIMARI,
betonarme kolon/perde ROTAS-MIMARI-KOLON (kullanıcı hizalama için)."""
import json
import math
import os
import pickle
import sys
import time

import networkx as nx
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

BURASI = os.path.dirname(os.path.abspath(__file__))
DEPO = os.path.abspath(os.path.join(BURASI, '..', '..'))
sys.path.insert(0, BURASI)
sys.path.insert(0, os.path.join(BURASI, '..', 'sihhi2'))
import sihhi_cizim as C        # noqa: E402
import sihhi_tasarim as T      # noqa: E402
import sihhi_plan as PL        # noqa: E402
import sihhi_sema as SE        # noqa: E402
import sihhi_mimari as MM      # noqa: E402

CIKTI = os.path.join(DEPO, 'proje', 'ab2750', 'AB2750_SIHHI_TESISAT.dxf')
SERIT = {'B': (-28350.0, -25100.0), 'A': (-36150.0, -31900.0)}
KAT_DX = {'A': 8655.0, 'B': 6000.0}
VAZ_PENCERE = (20900.0, 24700.0, -28150.0, -25600.0)
VAZ_MERKEZ = {'B': (22938.5, -26264.5), 'A': (23058.5, -27099.5)}      # vaziyetteki blok dış hattı merkezi
VAZ_OLCEK = 0.25


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ====================================================================== hesaplar
IC_CAP = {'Ø20': 13.2, 'Ø25': 16.6, 'Ø32': 21.2, 'Ø40': 26.6, 'Ø50': 33.4, 'Ø63': 42.0, 'Ø75': 50.0, 'Ø90': 60.0,
          'Ø110': 73.4}


def hw_kayip(Q_ls, cap, L_m, Cc=140.0):
    d = IC_CAP[cap] / 1000.0
    Q = Q_ls / 1000.0
    if Q <= 0:
        return 0.0, 0.0
    j = 10.67 * Q ** 1.852 / (Cc ** 1.852 * d ** 4.87)
    v = Q / (math.pi * d * d / 4)
    return j * L_m, v


def _graf(hatlar):
    G = nx.Graph()
    for h in hatlar:
        for a, b in zip(h['yol'][:-1], h['yol'][1:]):
            A = (round(a[0], 1), round(a[1], 1))
            B = (round(b[0], 1), round(b[1], 1))
            G.add_edge(A, B, w=math.dist(a, b), h=h)
    return G


def _en_yakin_dugum(G, p):
    return min(G.nodes, key=lambda n: math.dist(n, p))


def kritik_devre(M):
    """depo -> soğuk dağıtım kolonu -> en üst kat koridor hattı -> en uzak daire dolabı -> en uzak armatür"""
    Fs = M['Fs']
    F = Fs['2']
    kr = F.koridor
    Gk = _graf(kr['hatlar'])
    r0 = _en_yakin_dugum(Gk, kr['riser'])
    best = None
    for no, d in F.dol.items():
        if d is None:
            continue
        n1 = _en_yakin_dugum(Gk, d['c'])
        try:
            L = nx.shortest_path_length(Gk, r0, n1, weight='w')
        except nx.NetworkXNoPath:
            continue
        D = F.daire[no]
        t = D.get('temiz', {})
        if not t.get('soguk'):
            continue
        Gd = _graf(t['soguk'])
        k0 = _en_yakin_dugum(Gd, t['kok'])
        for mu in t['musluk']:
            if mu['arm']['tip'] != 'DUS':
                continue
            n2 = _en_yakin_dugum(Gd, mu['arm']['musluk'])
            try:
                L2 = nx.shortest_path_length(Gd, k0, n2, weight='w')
            except nx.NetworkXNoPath:
                continue
            if best is None or L + L2 > best[0]:
                best = (L + L2, no, L, L2)
    _, no, Lk, Ld = best
    ys_bina = sum(Fq.koridor['yb_s'] for Fq in Fs.values()) + (M['bodrum']['yb_s'] if M.get('bodrum') else 0)
    if M['blok'] == 'A':
        ys_bina += 0
    ys_kat = kr['yb_s']
    D = F.daire[no]
    ys_d = D['temiz']['yb_s']
    satir = []
    # 1: depo çıkışı -> 2. kat tavanı (kolon), 2: kat koridor hattı, 3: daire içi, 4: armatür bağlantısı
    parcalar = [('DEPO ÇIKIŞI - S KOLONU (ÇATI -> 2. KAT TAVANI)', 6.0, ys_bina),
                ('2. KAT DAĞITIM HATTI (KORİDOR ASMA TAVAN)', Lk / 100.0, ys_kat),
                ('D%d SAYAÇ DOLABI - EN UZAK ISLAK HACİM' % no, Ld / 100.0 * 0.7, ys_d),
                ('ISLAK HACİM İÇİ (DUŞ BAĞLANTISI)', Ld / 100.0 * 0.3, 1.0)]
    top = 0.0
    for ad, L, yb in parcalar:
        cap = T.temiz_cap(yb)
        Q = T.debi_yb(yb)
        h, v = hw_kayip(Q, cap, L)
        top += h
        satir.append((ad, '%.1f' % L, '%g' % yb, '%.2f' % Q, cap, '%.2f' % v, '%.2f' % h))
    lokal = top * 0.30
    cikis = 5.0
    gerek = top + lokal + cikis
    # statik: depo tabanı çatı döşemesinden +1,0 m kaide; en üst kat armatür (duş) döşemeden +2,1 m
    statik = 3.0 + 1.0 - 2.1
    return dict(satir=satir, kayip=top, lokal=lokal, cikis=cikis, gerek=gerek, statik=statik, daire=no,
                kule=max(0.0, gerek - statik))


def depo_hesap(n):
    return 3.0 + 0.5 * max(0, n - 10)


def yagmur_hesap(M):
    fp = M['altyapi']['ayak_izi']
    P = fp.area / 1e4
    f = len(M['yagmur'])
    S = P * 0.75
    A = S / f
    D = 1.13 * math.sqrt(A)
    if D < 7.0:
        cap, sonuc = 'Ø70', 'D = %.2f cm < 7 cm -> Ø70 lik Boru UYGUNDUR.' % D
    elif D < 10.0:
        cap, sonuc = 'Ø100', 'D = %.2f cm < 10 cm -> Ø100 lük Boru UYGUNDUR.' % D
    else:
        cap, sonuc = 'Ø125', 'D = %.2f cm -> Ø125 lik Boru UYGUNDUR.' % D
    return dict(P=P, S=S, f=f, A=A, D=D, cap=cap, sonuc=sonuc)


def pompa_hesap(M):
    B = M['bodrum']
    du = {'WC': 2.0, 'LV': 0.5, 'EV': 0.8, 'ABD': 0.5}
    sdu = sum(du.get(a['tip'], 0.5) * a.get('adet', 1) for a in B['armatur'])
    Qww = 0.5 * math.sqrt(sdu)
    Q = max(Qww * 3.6, 6.0)
    Hg = 2.20 + 1.20 + 0.50 - 0.70          # bodrum döşemesi + çukur derinliği + tavan/çıkış - rögar giriş derinliği
    Hk = 1.5
    H = Hg + Hk + 1.0
    V = 1.0 * 1.0 * 1.2
    return dict(sdu=sdu, Qww=Qww, Q=Q, Hg=Hg, Hk=Hk, H=H, V=V)


def boyler_hesap(n_daire):
    kisi = n_daire * 3.5
    gun = kisi * 50.0                       # 60 °C kullanım, l/gün
    pik = gun / 4.0                          # depolama (pik saat payı)
    return dict(kisi=kisi, gun=gun, hacim=pik, secim='2 x 1500 lt ÇİFT SERPANTİNLİ BOYLER (3000 lt)')


# ====================================================================== yardımcılar
def cerceve(msp, x0, x1, y0, y1, baslik=None):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': 'ROTAS-PAFTA'})
    if baslik:
        C.yazi(msp, baslik, (x0 + 300, y0 + 45), 40, 'ROTAS-PAFTA-YAZI', 'BL', w=0.9)


def tablo(msp, x0, y_ust, baslik, kolonlar, satirlar, genis, h=10.0, rh=24.0):
    """basit tablo; dönüş: alt y"""
    W = sum(genis)
    m = msp
    y = y_ust
    m.add_lwpolyline([(x0, y), (x0 + W, y), (x0 + W, y - 30), (x0, y - 30)], close=True, dxfattribs={'layer': 'ROTAS-HESAP-TABLO'})
    C.yazi(m, baslik, (x0 + W / 2, y - 15), 12, 'ROTAS-HESAP-YAZI', 'MC')
    y -= 30
    rows = [kolonlar] + satirlar
    for i, r in enumerate(rows):
        m.add_lwpolyline([(x0, y), (x0 + W, y), (x0 + W, y - rh), (x0, y - rh)], close=True, dxfattribs={'layer': 'ROTAS-HESAP-TABLO'})
        x = x0
        for j, (c, g) in enumerate(zip(r, genis)):
            if j:
                m.add_line((x, y), (x, y - rh), dxfattribs={'layer': 'ROTAS-HESAP-TABLO'})
            s = str(c)
            hh = h
            while C.yazi_gen(s, hh) > g - 6 and hh > 6:
                hh -= 0.5
            C.yazi(m, s, (x + g / 2, y - rh / 2), hh, 'ROTAS-HESAP-YAZI', 'MC')
            x += g
        y -= rh
    return y


def notlar(msp, x0, y_ust, baslik, satir, h=11.0, w_max=2400):
    C.yazi(msp, baslik, (x0, y_ust), 14, 'ROTAS-NOT', 'TL')
    y = y_ust - 28
    for i, s in enumerate(satir, 1):
        C.yazi(msp, '%d- %s' % (i, s), (x0, y), h, 'ROTAS-NOT', 'TL')
        y -= h * 1.7
    return y


# ====================================================================== temel (altyapı) planı
def temel_plani(msp, M, dx, dy=0.0):
    AY = M['altyapi']
    F = M['Fs']['Z']
    E = C.Engel()
    off = lambda p: (p[0] + dx, p[1] + dy)
    fp = AY['ayak_izi']
    msp.add_lwpolyline([off(p) for p in fp.exterior.coords], dxfattribs={'layer': 'ROTAS-MIMARI'})
    for g in getattr(F.beton, 'geoms', [F.beton]):
        if g.area < 200:
            continue
        pts = [off(p) for p in g.exterior.coords]
        msp.add_lwpolyline(pts, dxfattribs={'layer': 'ROTAS-MIMARI-KOLON'})
        h = msp.add_hatch(color=8, dxfattribs={'layer': 'ROTAS-MIMARI-KOLON'})
        h.set_pattern_fill('ANSI31', scale=3.0)
        h.paths.add_polyline_path(pts, is_closed=True)
        E.ekle(Polygon(pts), 'beton')
    P = PL.Plan(msp, F, M, 'T')
    P.E = E
    # bağlantılar
    for b in AY['baglar']:
        yol = [off(p) for p in b['yol']]
        L = LineString(yol)
        # rögar içine girmesin, kolon simgesinin içine girmesin
        P.pl(yol, 'ROTAS-ALTYAPI-PIS', 'pis')
    for k in M['kolonlar']:
        p = off(k['p'])
        C.blok(msp, 'ROTAS-PL-PIS-KOLON', p, 'ROTAS-PISSU-KOLON')
        E.ekle(Point(p).buffer(11), 'sembol')
    R = {r['no']: r for r in AY['rogarlar']}
    for r in AY['rogarlar']:
        p = off(r['p'])
        C.blok(msp, 'ROTAS-PL-ROGAR', p, 'ROTAS-ROGAR')
        E.ekle(box(p[0] - 36, p[1] - 36, p[0] + 36, p[1] + 36), 'sembol')
    pb = off(AY['pb']['p'])
    C.blok(msp, 'ROTAS-PL-PB', pb, 'ROTAS-ROGAR')
    E.ekle(box(pb[0] - 41, pb[1] - 41, pb[0] + 41, pb[1] + 41), 'sembol')
    for h in AY['zincir']:
        a, b = off(h['yol'][0]), off(h['yol'][1])
        L = LineString([a, b])
        ra = 36
        rb = 41 if h['b'] == 'PB' else 36
        d = L.length
        if d < ra + rb + 1:
            continue
        u = ((b[0] - a[0]) / d, (b[1] - a[1]) / d)
        # kare kutu kenarı (eksene paralel hatlarda tam kenar)
        P.pl([(a[0] + u[0] * ra, a[1] + u[1] * ra), (b[0] - u[0] * rb, b[1] - u[1] * rb)], 'ROTAS-ALTYAPI-PIS', 'zincir')
        h['_cizim'] = [(a[0] + u[0] * ra, a[1] + u[1] * ra), (b[0] - u[0] * rb, b[1] - u[1] * rb)]
    # PB -> yol (SASKİ)
    fpb = fp.bounds
    if M['blok'] == 'B':
        yol = [(pb[0], pb[1] + 41), (pb[0], pb[1] + 300)]
        txt = (pb[0] + 20, pb[1] + 250)
    else:
        yol = [(pb[0], pb[1] - 41), (pb[0], pb[1] - 300)]
        txt = (pb[0] + 20, pb[1] - 260)
    P.pl(yol, 'ROTAS-ALTYAPI-PIS', 'zincir')
    C.yazi(msp, 'SASKİ ATIKSU KANALINA (YOL) Ø200', txt, 14, 'ROTAS-ALTYAPI-YAZI', 'BL')
    E.ekle(C.yazi_kutusu('SASKİ ATIKSU KANALINA (YOL) Ø200', txt, 14), 'yazi')
    # pompa rögarı (A)
    if M.get('rp'):
        rp = off(M['rp']['p'])
        C.blok(msp, 'ROTAS-PL-ROGAR', rp, 'ROTAS-ROGAR')
        E.ekle(box(rp[0] - 36, rp[1] - 36, rp[0] + 36, rp[1] + 36), 'sembol')
        P.pl([off(p) for p in M['rp']['basma']], 'ROTAS-POMPA', 'basma')
        P.pl([off(p) for p in M['rp']['hat']], 'ROTAS-ALTYAPI-PIS', 'rp')
    # yazılar: rögar no + ölçü, hat etiketleri, kolon balonları
    for r in AY['rogarlar']:
        p = off(r['p'])
        C.yazi(msp, r['no'], p, 20, 'ROTAS-ROGAR', 'MC', renk=5)
        P.not_yaz(['%s / h:-%d cm' % (r['olcu'], r['h'])], (p[0], p[1] - 60), 10, 'ROTAS-ALTYAPI-YAZI', r_max=120)
    C.yazi(msp, 'PB', pb, 22, 'ROTAS-ROGAR', 'MC', renk=5)
    P.not_yaz(['PARSEL BACASI 80x80 / h:-%d cm' % AY['pb']['h']], (pb[0] + 150, pb[1]), 11, 'ROTAS-ALTYAPI-YAZI', r_max=200)
    if M.get('rp'):
        C.yazi(msp, 'RP', rp, 18, 'ROTAS-ROGAR', 'MC', renk=5)
        P.not_yaz(['RP: POMPA BASMA RÖGARI 70x70 / h:-70 cm', '(BASMA HATTI Ø63, PB YE AYRI HAT Ø150)'],
                  (rp[0] + 170, rp[1]), 10, 'ROTAS-ALTYAPI-YAZI', r_max=260)
    for h in AY['zincir']:
        if '_cizim' in h:
            P.etiket_temiz(h['_cizim'], ['L=%.2f m / Q=Ø%d / %%1' % (h['L'] / 100, h['cap'])], 'ROTAS-ALTYAPI-YAZI',
                           min_boy=60, kanca=20)
    for b in AY['baglar']:
        yol = [off(p) for p in b['yol']]
        P.etiket_temiz(yol, ['Ø%d / %%1' % b['cap']], 'ROTAS-ALTYAPI-YAZI', min_boy=60, kanca=18)
    for k in M['kolonlar']:
        P.balon(off(k['p']), k['no'])
    # yağmur inişleri (zemin katta biter) + şebeke girişi
    FZ = M['Fs']['Z']
    for y in FZ.yagmur:
        p = off((y['inis'][0] - FZ.dx, y['inis'][1]))
        C.blok(msp, 'ROTAS-PL-YAGMUR-INIS', p, 'ROTAS-YAGMUR')
    return P


# ====================================================================== çatı planı
def cati_plani(msp, M):
    blok = M['blok']
    w = MM.KATLAR[(blok, 'C')]
    dxC = MM.zx(blok, 'C')
    E = C.Engel()
    C.mimari_altlik(msp, w[:4], engel=E)
    F = M['Fs']['Z']
    P = PL.Plan(msp, F, M, 'C')
    P.E = E
    for k in M['kolonlar']:
        p = (k['p'][0] + dxC, k['p'][1])
        C.blok(msp, 'ROTAS-PL-HAVALIK', p, 'ROTAS-PISSU-KOLON')
        E.ekle(Point(p).buffer(17), 'sembol')
    for y in F.yagmur:
        p = (y['inis'][0] - F.dx + dxC, y['inis'][1])
        C.blok(msp, 'ROTAS-PL-YAGMUR-INIS', p, 'ROTAS-YAGMUR')
        E.ekle(Point(p).buffer(7), 'sembol')
    # depo: temiz su kolon kutusu üzerinde
    rz = M['riser']
    V = depo_hesap(M['daire_sayisi'])
    a = math.sqrt(V / 1.5) * 100            # 1,5 m yükseklik, kare taban
    c = (rz[0] + dxC, rz[1])
    kb = box(c[0] - a / 2, c[1] - a / 2, c[0] + a / 2, c[1] + a / 2)
    msp.add_lwpolyline(list(kb.exterior.coords), dxfattribs={'layer': 'ROTAS-DEPO'})
    msp.add_lwpolyline(list(kb.buffer(-8, join_style=2).exterior.coords), dxfattribs={'layer': 'ROTAS-DEPO'})
    E.ekle(kb, 'sembol')
    P.not_yaz(['KULLANIM SU DEPOSU (ÇATI) V=%g m³' % V, '%.0fx%.0fx150 cm, BETONARME KAİDE ÜZERİNDE' % (a, a),
               'TAŞMA + BOŞALTMA EN YAKIN YAĞMUR İNİŞİNE'], (c[0], c[1] - a / 2 - 60), 12, 'ROTAS-DEPO', r_max=300)
    # çatı fanları (şaftlar)
    for s in M['hav']:
        p = (s['p'][0] + dxC, s['p'][1])
        C.blok(msp, 'ROTAS-PL-CATI-FAN', p, 'ROTAS-HAVALANDIRMA')
        E.ekle(Point(p).buffer(31), 'sembol')
    for s in M['hav']:
        p = (s['p'][0] + dxC, s['p'][1])
        P.not_yaz(['%s ÇATI TİPİ FAN' % s['no'], '%d m³/h - Ø150' % s['debi']], (p[0], p[1] + 70), 10,
                  'ROTAS-HAVALANDIRMA-YAZI', r_max=180)
    for k in M['kolonlar']:
        P.balon((k['p'][0] + dxC, k['p'][1]), k['no'], r_min=40, r_max=180)
    for y in F.yagmur:
        if y.get('no'):
            P.balon((y['inis'][0] - F.dx + dxC, y['inis'][1]), y['no'], blok='ROTAS-PL-BALON-YAGMUR', renk_yazi=3,
                    kat='ROTAS-YAGMUR-NO', r_min=40)
    return P


# ====================================================================== yerleşim
def vaz(M, p):
    """blok plan (Z) koordinatı -> vaziyet planı koordinatı"""
    x0, y0, x1, y1 = M['altyapi']['ayak_izi'].bounds
    c = ((x0 + x1) / 2, (y0 + y1) / 2)
    v = VAZ_MERKEZ[M['blok']]
    return (v[0] + (p[0] - c[0]) * VAZ_OLCEK, v[1] + (p[1] - c[1]) * VAZ_OLCEK)


def yerlesim(msp, MS, x0, y0, w, h, bilgi):
    vx0, vx1, vy0, vy1 = VAZ_PENCERE
    dx = x0 + w / 2 - (vx0 + vx1) / 2
    dy = y0 + h / 2 + 100 - (vy0 + vy1) / 2
    C.mimari_altlik(msp, VAZ_PENCERE, dx, dy, haric=('rtm-aks', 'DEFPOINTS', 'Defpoints'))
    o = lambda p: (p[0] + dx, p[1] + dy)
    for M in MS:
        AY = M['altyapi']
        for hh in AY['zincir']:
            msp.add_lwpolyline([o(vaz(M, q)) for q in hh['yol']], dxfattribs={'layer': 'ROTAS-YERLESIM-EK'})
        for r in AY['rogarlar']:
            p = o(vaz(M, r['p']))
            msp.add_lwpolyline([(p[0] - 9, p[1] - 9), (p[0] + 9, p[1] - 9), (p[0] + 9, p[1] + 9), (p[0] - 9, p[1] + 9)],
                               close=True, dxfattribs={'layer': 'ROTAS-YERLESIM-EK'})
        pb = o(vaz(M, AY['pb']['p']))
        msp.add_lwpolyline([(pb[0] - 12, pb[1] - 12), (pb[0] + 12, pb[1] - 12), (pb[0] + 12, pb[1] + 12), (pb[0] - 12, pb[1] + 12)],
                           close=True, dxfattribs={'layer': 'ROTAS-YERLESIM-EK'})
        yon = 1 if M['blok'] == 'B' else -1
        msp.add_line((pb[0], pb[1] + yon * 12), (pb[0], pb[1] + yon * 140), dxfattribs={'layer': 'ROTAS-YERLESIM-EK'})
        C.yazi(msp, '%s BLOK PB -> SASKİ ATIKSU KANALI' % M['blok'], (pb[0] + 15, pb[1] + yon * 70), 12,
               'ROTAS-YERLESIM-EK', 'ML')
    # A kazan dairesi -> B blok sıcak su hattı (toprak altı)
    MA = [M for M in MS if M['blok'] == 'A'][0]
    MB = [M for M in MS if M['blok'] == 'B'][0]
    kd = MA.get('kazan_z')
    if kd:
        a = o(vaz(MA, kd))
        b = o(vaz(MB, MB['riser']))
        m1 = (a[0], (a[1] + b[1]) / 2 + 0)
        yol = [a, (a[0] - 0, a[1]), (b[0], a[1])] if False else [a, (a[0], b[1] - 0), b]
        e = msp.add_lwpolyline(yol, dxfattribs={'layer': 'ROTAS-SICAKSU'})
        e.dxf.ltscale = 0.3
        C.yazi(msp, 'A BLOK KAZAN DAİRESİ -> B BLOK: SICAK SU + SİRKÜLASYON (TOPRAK ALTI, İZOLELİ)', (a[0] + 10, (a[1] + b[1]) / 2),
               10, 'ROTAS-SICAKSU', 'ML')
    C.yazi(msp, 'YERLEŞİM PLANI  ÖLÇEK: 1 / 200', (x0 + 300, y0 + 45), 40, 'ROTAS-PAFTA-YAZI', 'BL', w=0.9)
    # bilgi kutusu
    sat = [('İLİ', bilgi['il']), ('İLÇESİ', bilgi['ilce']), ('MAHALLESİ', bilgi['mahalle']), ('ADA NO', bilgi['ada']),
           ('PARSEL NO', bilgi['parsel']), ('BLOKLAR', 'A BLOK (B+Z+2, 48 D.) / B BLOK (Z+2, 30 D.)')]
    bx, by = x0 + 120, y0 + h - 120
    for i, (a, b) in enumerate(sat):
        C.yazi(msp, a, (bx, by - 28 * i), 14, 'ROTAS-NOT', 'BL')
        C.yazi(msp, ': ' + b, (bx + 170, by - 28 * i), 14, 'ROTAS-NOT', 'BL')


# ====================================================================== ana
def bilgi_sozluk(blok):
    return {'proje_turu': 'SIHHİ TESİSAT PROJESİ', 'il': 'SAKARYA', 'ilce': 'ADAPAZARI', 'belediye': 'ADAPAZARI',
            'mahalle': 'KARAPINAR', 'pafta': '-', 'ada': '2750', 'parsel': '7', 'emsal': '-',
            'yapi_sahibi': 'ENGİN KABA VE HİSSEDARLARI', 'bagimsiz_bolum': '48' if blok == 'A' else '30',
            'kat_sayisi': '4' if blok == 'A' else '3', 'kat_adedi': '4' if blok == 'A' else '3',
            'insaat_alani': '-', 'arsa_alani': '-', 'yapi_sinifi': '3/B', 'yapi_sinifi_kisa': '3B',
            'alan_hesabi': [], 'alan_toplam': '-'}


def model_tamamla(M):
    blok = M['blok']
    M['daire_sayisi'] = 48 if blok == 'A' else 30
    M['yagmur_hesap'] = yagmur_hesap(M)
    M['yagmur_cap'] = M['yagmur_hesap']['cap']
    if blok == 'A':
        # kazan dairesi (Z çerçevesi) + pompa rögarı
        FB = M['bodrum']['F']
        kd = None
        for x, y, s, h, L in FB.K.yazilar:
            if s.upper().startswith('KAZAN DA'):
                kd = (x - FB.dx, y)
        M['kazan_z'] = kd
        AY = M['altyapi']
        x0, y0, x1, y1 = AY['ayak_izi'].bounds
        c = M['bodrum']['cukur']
        cz = (c[0] - FB.dx, c[1])
        D_R = AY['D_R']
        yy = cz[1]
        for _ in range(40):
            if all(math.dist((x1 + D_R, yy), r['p']) > 140 for r in AY['rogarlar']):
                break
            yy -= 20
        rp = (x1 + D_R, yy)
        pb = AY['pb']['p']
        v2 = D_R + 85
        hat = [(rp[0] + 36, rp[1]), (x1 + v2, rp[1]), (x1 + v2, y0 - v2), (pb[0] + 60, y0 - v2), (pb[0] + 60, pb[1]),
               (pb[0] + 41, pb[1])]
        basma = [cz, (cz[0], rp[1]), (rp[0] - 36, rp[1])] if abs(cz[1] - rp[1]) > 1 else [cz, (rp[0] - 36, rp[1])]
        M['rp'] = dict(p=rp, hat=hat, basma=basma)
    return M


def uret(cikti=CIKTI):
    MS = []
    for b in ('B', 'A'):
        M = pickle.load(open(f'{T.ONB}/model_{b}.pkl', 'rb'))
        MS.append(model_tamamla(M))
    doc = C.belge()
    SE.hazirla(doc)
    import detay as DT
    import antet as AN
    AN.hazirla(doc)
    DT.katmanlar(doc)
    msp = doc.modelspace()
    rapor = {}
    for M in MS:
        b = M['blok']
        ya, yu = SERIT[b]
        H_ = yu - ya
        dx = KAT_DX[b]
        bilgi = bilgi_sozluk(b)
        kat_sira = ['B', 'Z', '1', '2'] if b == 'A' else ['Z', '1', '2']
        # kat paftaları (mimari koordinatında)
        pafta = {}
        for k in kat_sira + ['C']:
            w = MM.KATLAR[(b, k)]
            pafta[k] = (w[0] - (dx - (w[1] - w[0])) / 2, w[1] + (dx - (w[1] - w[0])) / 2)
        RP = {}
        for k in kat_sira:
            t0 = time.time()
            P = PL.kat_plani(msp, M, k)
            RP[k] = dict(say=P.say, uyari=P.uyari)
            cerceve(msp, pafta[k][0], pafta[k][1], ya, yu, '%s PLANI.........ÖLÇEK: 1 / 50' % SE.KAT_YAZI[k])
            log(b, k, 'plan', round(time.time() - t0, 1), P.say)
        P = cati_plani(msp, M)
        cerceve(msp, pafta['C'][0], pafta['C'][1], ya, yu, 'ÇATI PLANI.........ÖLÇEK: 1 / 50')
        # temel (altyapı): ilk plan paftasının solunda
        ilk = pafta[kat_sira[0]][0]
        tdx = ilk - dx - pafta['Z'][0] + 0
        tx0 = ilk - dx
        PT = temel_plani(msp, M, tx0 - pafta['Z'][0])
        cerceve(msp, tx0, ilk, ya, yu, 'ALTYAPI (TEMEL) PLANI.........ÖLÇEK: 1 / 50')
        # yerleşim + antet
        yw = 4400.0
        yx0 = tx0 - yw
        yerlesim(msp, MS, yx0, ya, yw, H_, bilgi)
        cerceve(msp, yx0, tx0, ya, yu)
        ax0 = yx0 - 1060
        AN.antet_ciz(msp, ax0 + 50, ya + 25, bilgi)
        cerceve(msp, ax0, yx0, ya, yu)
        # şema
        sx0 = pafta['C'][1]
        sy0 = ya + 900 if b == 'A' else ya + 750
        S = SE.Sema(msp, M, sx0 + 150, sy0)
        R = S.ciz()
        sx1 = R['x1'] + 150
        cerceve(msp, sx0, sx1, ya, yu, 'AÇILIMLI KOLON ŞEMASI (MERKEZİ SİSTEM) VE RÖGAR ŞEMASI')
        # hesaplar
        hx0 = sx1
        hx1 = hesaplar(msp, M, hx0 + 100, yu - 150) + 150
        cerceve(msp, hx0, hx1, ya, yu, 'HESAPLAR, LEJANT VE NOTLAR')
        # detay
        dx0 = hx1
        wc = wc_girdi(M)
        try:
            DT.detay_paftasi(msp, dx0, ya, 2065.0, H_, girdi=wc)
        except Exception as e:
            log('detay paftası hata', e)
            DT.sihhi_detaylar(msp, dx0 + 25, ya + 23)
        cerceve(msp, dx0, dx0 + 2065, ya, yu)
        rapor[b] = RP
        log(b, 'pafta bitti')
    doc.saveas(cikti)
    return doc, MS, rapor


def wc_girdi(M):
    katlar = [dict(kod=k, ad=SE.KAT_YAZI[k], kot=v, h=3.0) for k, v in
              (('Z', 0.0), ('1', 3.0), ('2', 6.0))]
    mah = []
    for k, F in M['Fs'].items():
        for no, D in F.daire.items():
            for W in D['islak']:
                if W['tip'] == 'banyo' and W.get('hav', {}).get('no'):
                    mah.append(dict(kat=k, daire='D%d' % no, ad='banyo', tip='BANYO', saft=W['hav']['no'], brans_m=1.0,
                                    alan_m2=round(W['poly'].area / 1e4, 2)))
    return dict(proje='2750/7 %s BLOK' % M['blok'], katlar=katlar, cati_kot=9.0, cati_ustu=1.0,
                kabul=dict(q_oda=80, kademeler=[80, 160], asp_basinc=50, baglanti_cap=150, oda_basina_aspirator=True),
                saftlar=[dict(ad=s['no'], baglanti_yuk=2.6) for s in M['hav']], mahaller=mah)


def hesaplar(msp, M, x0, y_ust):
    b = M['blok']
    n = M['daire_sayisi']
    y = y_ust
    # 1) depo
    V = depo_hesap(n)
    y = tablo(msp, x0, y, 'KULLANIM SU DEPOSU HESABI (%s BLOK)' % b, ['BAĞIMSIZ BÖLÜM', 'KURAL', 'HACİM', 'YERİ'],
              [[str(n), '≤10 BB 3 m³ + her ek BB 0,5 m³', '%g m³' % V, 'ÇATI (HİDROFOR GEREKMEZ)']], [200, 380, 160, 360]) - 40
    # 2) kritik devre
    K = kritik_devre(M)
    rows = [list(r) for r in K['satir']]
    rows.append(['TOPLAM SÜRTÜNME KAYBI', '', '', '', '', '', '%.2f' % K['kayip']])
    rows.append(['YEREL KAYIPLAR (%30)', '', '', '', '', '', '%.2f' % K['lokal']])
    rows.append(['EN UZAK ARMATÜR ÇIKIŞ BASINCI', '', '', '', '', '', '%.2f' % K['cikis']])
    rows.append(['GEREKLİ BASMA YÜKSEKLİĞİ (mSS)', '', '', '', '', '', '%.2f' % K['gerek']])
    rows.append(['DEPO TABANI - EN ÜST KAT DUŞ STATİK FARK (mSS)', '', '', '', '', '', '%.2f' % K['statik']])
    y = tablo(msp, x0, y, 'TEMİZ SU KRİTİK DEVRE HESABI (TS 1258, PPRC PN20, HAZEN-WILLIAMS C=140) - D%d' % K['daire'],
              ['HAT', 'L (m)', 'ΣYB', 'Q (l/s)', 'ÇAP', 'v (m/s)', 'h (mSS)'], rows, [520, 90, 90, 90, 90, 90, 100]) - 20
    yaz = ['Q = 0,25 x √ΣYB (l/s); çap TS 1258 Bölüm 3.1 YB aralıklarından seçilmiştir.',
           'Depo tabanı en üst kat en uzak duş bağlantısından %.1f m yukarıda olacak şekilde (kule / kaide) yapılacaktır.' % K['gerek']
           if K['kule'] > 0 else 'Depo kotu yeterli basıncı sağlamaktadır.']
    for s in yaz:
        C.yazi(msp, s, (x0, y), 10, 'ROTAS-HESAP-YAZI', 'TL')
        y -= 20
    y -= 30
    M['kritik'] = K
    # 3) daire temiz su yükleri
    rows = []
    for k in ('Z', '1', '2'):
        F = M['Fs'][k]
        for no in sorted(F.daire):
            t = F.daire[no].get('temiz', {})
            rows.append(['D%d' % no, SE.KAT_YAZI[k], '%g' % t.get('yb_s', 0), T.temiz_cap(t.get('yb_s', 0)),
                         '%g' % t.get('yb_h', 0), T.temiz_cap(t.get('yb_h', 0))])
    half = (len(rows) + 1) // 2
    y1 = tablo(msp, x0, y, 'DAİRE SAYAÇ DOLABI ÇIKIŞLARI (1)', ['DAİRE', 'KAT', 'S ΣYB', 'S ÇAP', 'H ΣYB', 'H ÇAP'],
               rows[:half], [90, 110, 80, 70, 80, 70], h=9, rh=20)
    y2 = tablo(msp, x0 + 560, y, 'DAİRE SAYAÇ DOLABI ÇIKIŞLARI (2)', ['DAİRE', 'KAT', 'S ΣYB', 'S ÇAP', 'H ΣYB', 'H ÇAP'],
               rows[half:], [90, 110, 80, 70, 80, 70], h=9, rh=20)
    y = min(y1, y2) - 40
    # 4) pis su kolon yükleri
    rows = []
    for k in M['kolonlar']:
        kk = k['katlar']
        rows.append([k['no'], k['tip'].upper(), ', '.join('%s:%g' % (q, kk[q]['sb']) for q in ('Z', '1', '2') if q in kk),
                     '%g' % k['sb'], 'Ø%d' % k['cap']])
    half = (len(rows) + 1) // 2
    xR = x0 + 1150
    yy = y_ust
    y1 = tablo(msp, xR, yy, 'PİS SU KOLON YÜKLERİ (1)', ['KOLON', 'MAHAL', 'KAT SB', 'ΣSB', 'ÇAP'], rows[:half],
               [70, 90, 180, 60, 60], h=9, rh=20)
    y2 = tablo(msp, xR + 480, yy, 'PİS SU KOLON YÜKLERİ (2)', ['KOLON', 'MAHAL', 'KAT SB', 'ΣSB', 'ÇAP'], rows[half:],
               [70, 90, 180, 60, 60], h=9, rh=20)
    yy = min(y1, y2) - 40
    # 5) rögar / hat tablosu
    AY = M['altyapi']
    rows = []
    for hh in AY['zincir']:
        rows.append(['%s-%s' % (hh['a'], hh['b']), '%.2f' % (hh['L'] / 100), '%g' % hh['sb'], 'Ø%d' % hh['cap'], '%1'])
    yy = tablo(msp, xR, yy, 'RÖGAR ARASI HATLAR (BİNA DIŞI, PVC SN8)', ['HAT', 'L (m)', 'ΣSB', 'ÇAP', 'EĞİM'], rows,
               [140, 90, 90, 80, 70], h=9, rh=20) - 40
    rows = [[r['no'], ', '.join(r['kolonlar']) or '-', r['olcu'], '-%d' % r['h']] for r in AY['rogarlar']]
    rows.append(['PB', 'PARSEL BACASI', '80x80', '-%d' % AY['pb']['h']])
    yy = tablo(msp, xR, yy, 'RÖGAR LİSTESİ', ['NO', 'BAĞLANAN KOLONLAR', 'ÖLÇÜ', 'DERİNLİK (cm)'], rows,
               [70, 300, 90, 120], h=9, rh=20) - 40
    # 6) yağmur
    Hy = M['yagmur_hesap']
    yy = tablo(msp, xR, yy, 'YAĞMUR SUYU BORU ÇAPI HESABI', ['P (m²)', 'S=Px0,75 (cm²)', 'f', 'A=S/f (cm²)', 'D=1,13√A (cm)', 'SONUÇ'],
               [['%.1f' % Hy['P'], '%.1f' % Hy['S'], str(Hy['f']), '%.2f' % Hy['A'], '%.2f' % Hy['D'], Hy['cap'] + ' UYGUNDUR']],
               [100, 130, 50, 110, 130, 150]) - 40
    # 7) havalandırma şaftları
    rows = [[s['no'], str(len(s['bag'])), '%d' % s['debi'], 'Ø150 / 80 m³/h-50 Pa'] for s in M['hav']]
    yy = tablo(msp, xR, yy, 'WC/BANYO MEKANİK HAVALANDIRMA (PENCERESİZ ISLAK HACİMLER)', ['ŞAFT', 'BANYO', 'ÇATI FANI m³/h', 'ASPİRATÖR'],
               rows, [80, 80, 140, 220], h=9, rh=20) - 40
    xE = xR + 1000
    ye = y_ust
    if b == 'A':
        Pm = pompa_hesap(M)
        ye = tablo(msp, xE, ye, 'PİS SU POMPASI HESABI (BODRUM)', ['BÜYÜKLÜK', 'DEĞER'],
                   [['ΣDU (TS EN 12056-2)', '%.1f' % Pm['sdu']], ['Qww = 0,5√ΣDU', '%.2f l/s' % Pm['Qww']],
                    ['SEÇİLEN DEBİ', '%.1f m³/h' % Pm['Q']], ['GEOMETRİK YÜKSEKLİK', '%.2f m' % Pm['Hg']],
                    ['BORU KAYIPLARI', '%.2f m' % Pm['Hk']], ['BASMA YÜKSEKLİĞİ', '%.1f mSS' % Pm['H']],
                    ['ÇUKUR', '100x100x120 cm (%.1f m³)' % Pm['V']], ['POMPA', '2 AD. DALGIÇ (1 ASIL + 1 YEDEK), Ø63 BASMA']],
                   [260, 300]) - 40
        Bh = boyler_hesap(n + 30)
        ye = tablo(msp, xE, ye, 'MERKEZİ SICAK SU (BOYLER) HESABI - A + B BLOK', ['BÜYÜKLÜK', 'DEĞER'],
                   [['DAİRE SAYISI', '%d (A 48 + B 30)' % (n + 30)], ['KİŞİ (3,5 kişi/daire)', '%.0f' % Bh['kisi']],
                    ['GÜNLÜK SICAK SU (50 l/kişi, 60 °C)', '%.0f l' % Bh['gun']], ['DEPOLAMA (1/4)', '%.0f l' % Bh['hacim']],
                    ['SEÇİM', Bh['secim']]], [260, 300]) - 40
    # lejant + notlar
    ye = lejant(msp, xE, ye) - 40
    nt = ['Sıhhi tesisat TS 1258 ve TS EN 12056 standartlarına uygun yapılacaktır.',
          'Temiz su boruları PPRC PN20 (sıcak ve sirkülasyon PPRC-AL PN20, izoleli) olarak yapılacaktır.',
          'Sıcak su merkezi sistemden (A blok bodrum kazan dairesi boylerleri) 3 borulu (soğuk / sıcak / sirkülasyon) dağıtılacaktır.',
          'Sirkülasyon hattı her dairenin sayaç dolabı önünde sonlandırılacaktır.',
          'Her daire girişinde koridor duvarına gömme sayaç dolabı (soğuk + sıcak su sayacı; ısıtma kalorimetresi ısıtma projesinde) yapılacaktır.',
          'Kat dağıtım hatları ortak alan asma tavanından, temiz su kolonları her katta aynı hizada kolon kutusu içinden geçirilecektir.',
          'Pis su boruları PVC (kolonlar ses yalıtımlı) olarak yapılacak ve yatay hatlar en az %2 eğimle döşenecektir.',
          'Pis su kolonları çatıdan 50 cm yükseltilerek havalık şapkası ile sonlandırılacaktır.',
          'Mutfak ve WC giderleri döşeme içinde birleştirilmeyecek, her ıslak hacim kendi kolonuna bağlanacaktır.',
          'Kolon diplerine temizleme kapağı konulacak ve kolonlar zemin kotundan bina dışındaki rögarlara bağlanacaktır.',
          'Rögar arası hatlar %1 eğimle döşenecek ve parsel bacasından SASKİ atıksu kanalına bağlanacaktır.',
          'Bodrum ıslak hacim giderleri pis su çukuruna toplanacak ve dalgıç pompa basma hattı ayrı rögardan parsel bacasına verilecektir.',
          'Balkon süzgeçleri yalnız yağmur iniş borusuna bağlanacaktır.',
          'Yağmur iniş boruları zemin kotunda sonlandırılacaktır.',
          'Su deposu taşma ve boşaltma hatları en yakın yağmur inişine bağlanacaktır.',
          'Penceresiz banyolara 80 m³/h-50 Pa Ø150 mm WC aspiratörü konulacak ve şaft üzerinden çatı fanına bağlanacaktır.',
          'Borular betonarme kolon ve perdelerden geçirilmeyecek, döşeme ve duvar geçişlerinde kovan kullanılacaktır.',
          'Tesisat sızdırmazlık için 10 bar basınçla test edilecektir.']
    ye = notlar(msp, xE, ye, 'NOTLAR', nt)
    return max(xE + 900, xR + 1000)


def lejant(msp, x0, y_ust):
    sat = [('ROTAS-SOGUKSU', 'SOĞUK SU BORUSU (PPRC PN20)', 'line'), ('ROTAS-SICAKSU', 'SICAK SU BORUSU (PPRC-AL PN20)', 'line'),
           ('ROTAS-SIRKULASYON', 'SİRKÜLASYON BORUSU', 'line'), ('ROTAS-SEBEKE', 'ŞEBEKE / DEPO DOLUM HATTI', 'line'),
           ('ROTAS-PISSU', 'PİS SU BORUSU (PVC)', 'line'), ('ROTAS-ALTYAPI-PIS', 'BİNA DIŞI PİS SU HATTI (PVC SN8)', 'line'),
           ('ROTAS-YAGMUR', 'YAĞMUR SUYU BORUSU', 'line'), ('ROTAS-HAVALANDIRMA', 'ASPİRATÖR KANALI Ø150', 'line'),
           ('ROTAS-PL-PIS-KOLON', 'PİS SU KOLONU', 'blok'), ('ROTAS-PL-PIS-KOLON-GECIS', 'BU KATTAN GEÇEN PİS SU KOLONU', 'blok'),
           ('ROTAS-PL-YER-SUZGECI', 'YER SÜZGECİ', 'blok'), ('ROTAS-PL-BALKON-SUZGECI', 'BALKON SÜZGECİ', 'blok'),
           ('ROTAS-PL-YAGMUR-INIS', 'YAĞMUR İNİŞ BORUSU', 'blok'), ('ROTAS-PL-ASPIRATOR', 'WC ASPİRATÖRÜ 80 m³/h-50 Pa', 'blok'),
           ('ROTAS-PL-SAYAC', 'SU SAYACI', 'blok'), ('ROTAS-PL-VANA', 'KÜRESEL VANA', 'blok'), ('ROTAS-PL-CEKVALF', 'ÇEK VALF', 'blok'),
           ('ROTAS-PL-PISLIK-TUTUCU', 'PİSLİK TUTUCU', 'blok'), ('ROTAS-PL-ROGAR', 'RÖGAR 70x70', 'blok'),
           ('ROTAS-PL-PB', 'PARSEL BACASI 80x80', 'blok'), ('ROTAS-PL-POMPA', 'DALGIÇ POMPA', 'blok'),
           ('ROTAS-PL-BOYLER', 'BOYLER', 'blok'), ('ROTAS-PL-HAVALIK', 'HAVALIK (ÇATI)', 'blok'), ('ROTAS-PL-CATI-FAN', 'ÇATI TİPİ FAN', 'blok')]
    C.yazi(msp, 'LEJANT', (x0, y_ust), 14, 'ROTAS-LEJANT', 'TL')
    y = y_ust - 40
    for kat, ad, tip in sat:
        if tip == 'line':
            msp.add_line((x0, y), (x0 + 120, y), dxfattribs={'layer': kat})
        else:
            C.blok(msp, kat, (x0 + 60, y), 'ROTAS-LEJANT', olcek=0.8 if kat not in ('ROTAS-PL-BOYLER',) else 0.35)
        C.yazi(msp, ad, (x0 + 160, y), 11, 'ROTAS-LEJANT', 'ML')
        y -= 42
    # kısaltmalar
    for s in ('S: SOĞUK  H: SICAK  R: SİRKÜLASYON  DD: DEPO DOLUM  TSK: TEMİZ SU KOLON KUTUSU',
              'SD: SAYAÇ DOLABI  P: PİS SU KOLONU  YB: YAĞMUR İNİŞİ / YÜK BİRİMİ  SB: PİS SU YÜK BİRİMİ',
              "Ç'M': ÇAMAŞIR MAKİNESİ  B'M': BULAŞIK MAKİNESİ  T.K.: TEMİZLEME KAPAĞI  R: RÖGAR  PB: PARSEL BACASI"):
        C.yazi(msp, s, (x0, y), 10, 'ROTAS-LEJANT', 'ML')
        y -= 22
    return y


if __name__ == '__main__':
    t = time.time()
    doc, MS, rapor = uret()
    log('yazıldı', CIKTI, round(time.time() - t), 's')
    json.dump(rapor, open('/tmp/claude-0/sh/pafta_rapor.json', 'w'), ensure_ascii=False, indent=1, default=str)
