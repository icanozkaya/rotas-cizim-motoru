# -*- coding: utf-8 -*-
"""market_hav/ks_cizim.py — ısı geri kazanımlı klima santrali (KS) + DX dış ünite (DÜ) çizimleri.

  ks_plan(...)            planda KS gövdesine bölme/geri kazanım/batarya sembolleri, DÜ'ler ve soğutucu akışkan hatları
  ks_kesit_paftasi(...)   KS yatay kesit, A-A boyuna kesit, B-B enine kesit, DÜ görünüşleri, teknik tablo (1/25)
  kesitler_paftasi(...)   kullanıcının AA / BB kesitleri + santral, dış ünite, kanal ve menfez yerleşimi (1/100)

Santral düzeni (kullanıcının plandaki 830 × 545 cm gövdesi korunur): yan yana iki bölme. Kuzey bölme ÜFLEME
(taze hava sağ panjurdan girer, sol ağızdan ana kanala çıkar), güney bölme DÖNÜŞ/EGZOZ (sol ağızdan girer, sağ
panjurdan atılır). Ortada çapraz akışlı plakalı ısı geri kazanım eşanjörü, önünde karışım (by-pass) damperi.
"""
import math

from ezdxf.enums import TextEntityAlignment as TA

import detaylar as DT

K_CIHAZ = 'MTY-CIHAZ'
K_SOG = 'MTY-SOGUTUCU-HAT'
K_U, K_D = 'MTY-UFLEME-KANALI', 'MTY-DONUS-KANALI'
K_KU, K_KD = 'ROTAS-KESIT-KANAL-UFLEME', 'ROTAS-KESIT-KANAL-DONUS'
K_Y = 'ROTAS-HAV-DETAY-YAZI'
K_M = 'ROTAS-MIMARI-KESIT'
STIL = 'ROTAS'

# modül sınırları (santral sol yüzünden, cm)
UFLEME = [(0, 30, 'ÇIKIŞ'), (30, 100, 'SUSTURUCU'), (100, 250, 'ÜFLEME FANI'), (250, 300, 'DX ISITMA'),
          (300, 380, 'DX SOĞUTMA'), (380, 450, 'F7 FİLTRE'), (450, 530, 'KARIŞIM'), (530, 730, 'ISI GERİ KAZANIM'),
          (730, 790, 'G4 FİLTRE'), (790, 830, 'TAZE HAVA')]
DONUS = [(0, 30, 'DÖNÜŞ'), (30, 90, 'G4 FİLTRE'), (90, 240, 'DÖNÜŞ FANI'), (240, 330, 'SUSTURUCU'),
         (330, 450, 'SERVİS'), (450, 530, 'KARIŞIM'), (530, 730, 'ISI GERİ KAZANIM'), (730, 790, 'SERVİS'),
         (790, 830, 'EGZOZ')]
L_KS, W_KS, H_KS, H_KAIDE = 830.0, 545.0, 220.0, 15.0
DU_L, DU_W, DU_H = 240.0, 110.0, 190.0


def katmanlar(doc):
    for ad, renk, lt in ((K_SOG, 6, 'DASHED'), (K_M, 8, 'Continuous'), (K_KU, 20, 'Continuous'), (K_KD, 4, 'Continuous')):
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk, linetype=lt if lt in doc.linetypes else 'Continuous')


def _yazi(m, s, x, y, h, al='MC', kat=K_CIHAZ, rot=0.0, kutular=None, w=0.85):
    t = m.add_text(s, height=h, rotation=rot, dxfattribs={'layer': kat, 'style': STIL, 'width': w})
    t.set_placement((x, y), align=DT.AL[al])
    if kutular is not None:
        gw = DT.genislik(s, h, w)
        ax = {'L': 0, 'C': 0.5, 'R': 1}[al[1]]
        ay = {'B': 0, 'M': 0.5, 'T': 1}[al[0]]
        if rot % 180 == 0:
            kutular.append((x - ax * gw, y - ay * h, x + (1 - ax) * gw, y + (1 - ay) * h, s))
        else:
            kutular.append((x - (1 - ay) * h, y - ax * gw, x + ay * h, y + (1 - ax) * gw, s))
    return t


def _rect(m, x0, y0, x1, y1, kat=K_CIHAZ):
    return m.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': kat})


# =========================================================================================== plan sembolü
def ks_plan(m, b, no, deger, kutular):
    """b = santral gövdesi (x0, y0, x1, y1), kuzey yarı üfleme bölmesi. deger: dict(qs, qi, du_qs, du_qi).
    Dönüş: DÜ dikdörtgenleri listesi."""
    x0, y0, x1, y1 = b
    ym = (y0 + y1) / 2
    m.add_line((x0, ym), (x1, ym), dxfattribs={'layer': K_CIHAZ})                 # bölme ayırıcı
    # plakalı eşanjör: iki bölmeyi kaplayan baklava
    a0, a1 = x0 + 530, x0 + 730
    m.add_lwpolyline([((a0 + a1) / 2, y0 + 15), (a1, ym), ((a0 + a1) / 2, y1 - 15), (a0, ym)], close=True,
                     dxfattribs={'layer': K_CIHAZ})
    m.add_line((a0, ym), (a1, ym), dxfattribs={'layer': K_CIHAZ})
    # karışım damperi (ayırıcı üzerinde)
    for i in range(4):
        xx = x0 + 460 + i * 18
        m.add_line((xx, ym - 12), (xx + 12, ym + 12), dxfattribs={'layer': K_CIHAZ})
    # modül çizgileri (üfleme bölmesi)
    for s0, s1, ad in UFLEME[1:]:
        m.add_line((x0 + s0, ym), (x0 + s0, y1), dxfattribs={'layer': K_CIHAZ})
    for s0, s1, ad in DONUS[1:]:
        if ad == 'ISI GERİ KAZANIM' or ad == 'SERVİS':
            continue
        m.add_line((x0 + s0, y0), (x0 + s0, ym), dxfattribs={'layer': K_CIHAZ})
    # batarya taramaları (DX soğutma / ısıtma)
    for s0, s1 in ((250, 300), (300, 380)):
        for k in range(int((s1 - s0) / 10)):
            xx = x0 + s0 + 5 + k * 10
            m.add_line((xx, ym + 10), (xx, y1 - 10), dxfattribs={'layer': K_CIHAZ})
    # fan daireleri
    for cx, cy in ((x0 + 175, (ym + y1) / 2), (x0 + 165, (y0 + ym) / 2)):
        m.add_circle((cx, cy), 55, dxfattribs={'layer': K_CIHAZ})
    # dış üniteler (kuzeyde, gövdeden 250 cm sonra) + soğutucu akışkan hatları
    du = []
    yd0 = y1 + 250
    cx = (x0 + x1) / 2
    for i, xa in enumerate((cx - 30 - DU_L, cx + 30)):
        r = (xa, yd0, xa + DU_L, yd0 + DU_W)
        du.append(r)
        _rect(m, *r)
        for f in (0.27, 0.73):
            m.add_circle((xa + DU_L * f, yd0 + DU_W / 2), 42, dxfattribs={'layer': K_CIHAZ})
            m.add_circle((xa + DU_L * f, yd0 + DU_W / 2), 8, dxfattribs={'layer': K_CIHAZ})
        _yazi(m, f'DÜ-{no}.{i + 1}', xa + DU_L / 2, yd0 + DU_W + 30, 32, 'BC', kutular=kutular)
        # gaz + sıvı hattı: DÜ alt yüzünden santral üst yüzüne (soğutma/ısıtma bataryası hizası)
        xb = x0 + (300 if i == 0 else 270)
        for dxh in (0, 18):
            xs = xa + DU_L / 2 - 9 + dxh
            pts = [(xs, yd0), (xs, yd0 - 120 + dxh), (xb + dxh, yd0 - 120 + dxh), (xb + dxh, y1)]
            m.add_lwpolyline(pts, dxfattribs={'layer': K_SOG, 'ltscale': 0.5})
    _yazi(m, 'SOĞUTUCU AKIŞKAN HATLARI (GAZ + SIVI)', x0 + 240, y1 + 150, 24, 'MR', K_SOG, kutular=kutular)
    return du


# =========================================================================================== santral kesitleri
def _filtre(c, x0, x1, y0, y1, n=6):
    """zikzak (torba/panel) filtre sembolü, yerel cm."""
    pts = []
    for i in range(n + 1):
        yy = y0 + (y1 - y0) * i / n
        pts.append((x0 if i % 2 == 0 else x1, yy))
    c.P(pts)


def _batarya(c, x0, x1, y0, y1):
    c.R(x0, y0, x1, y1)
    k = 0
    xx = x0 + 4
    while xx < x1 - 2:
        c.L(xx, y0, xx, y1, DT.KAT_T)
        xx += 6
        k += 1
    c.L(x0, y0, x1, y1)
    c.L(x0, y1, x1, y0)


def _fan(c, xc, yc, r):
    c.C(xc, yc, r)
    c.C(xc, yc, r * 0.25)
    for a in range(0, 360, 45):
        t = math.radians(a)
        c.L(xc + r * 0.25 * math.cos(t), yc + r * 0.25 * math.sin(t),
            xc + r * 0.9 * math.cos(t + 0.5), yc + r * 0.9 * math.sin(t + 0.5))


def _susturucu(c, x0, x1, y0, y1, n=4):
    w = (x1 - x0)
    for i in range(n):
        yy0 = y0 + (y1 - y0) * (i + 0.2) / n
        yy1 = y0 + (y1 - y0) * (i + 0.8) / n
        c.R(x0 + 5, yy0, x1 - 5, yy1)
        c.tara([(x0 + 5, yy0), (x1 - 5, yy0), (x1 - 5, yy1), (x0 + 5, yy1)], 'AR-SAND', 1.5)


def _damper(c, x0, x1, y0, y1, n=5):
    c.R(x0, y0, x1, y1)
    for i in range(n):
        yy = y0 + (y1 - y0) * (i + 0.5) / n
        c.L(x0 + 3, yy - 6, x1 - 3, yy + 6)


def _ok(c, x0, y0, x1, y1, kat=DT.KAT):
    c.L(x0, y0, x1, y1, kat)
    a = math.atan2(y1 - y0, x1 - x0)
    for s in (2.6, -2.6):
        c.L(x1, y1, x1 - 12 * math.cos(a + s * 0.15), y1 - 12 * math.sin(a + s * 0.15), kat)


def ks_kesit_paftasi(m, x0, y0, w, h, deger, kutular):
    """deger: dict KS-n → (qs_sec, qi_sec, taze, du_qs, du_qi). (x0, y0) pafta sol alt."""
    K = 4.0
    # ------------------------------------------------- YATAY KESİT (plan) — sol üst
    bx, by = x0 + 800, y0 + h - 3100
    DT._cerceve(m, bx - 650, by - 450, bx + L_KS * K + 900, by + W_KS * K + 700, 11,
                'KLİMA SANTRALİ YATAY KESİTİ', '1/25', kutular)
    c = DT.Cz(m, bx, by, K, kutular)
    c.R(0, 0, L_KS, W_KS)
    c.R(-3, -3, L_KS + 3, W_KS + 3)
    ym = W_KS / 2
    c.L(0, ym, L_KS, ym)
    # üfleme bölmesi (üst)
    for s0, s1, ad in UFLEME:
        c.L(s0, ym, s0, W_KS)
        if ad == 'ÜFLEME FANI':
            _fan(c, (s0 + s1) / 2, (ym + W_KS) / 2, 70)
        elif ad in ('DX ISITMA', 'DX SOĞUTMA'):
            _batarya(c, s0 + 8, s1 - 8, ym + 12, W_KS - 12)
        elif 'FİLTRE' in ad:
            _filtre(c, s0 + 15, s1 - 15, ym + 10, W_KS - 10, 8)
        elif ad == 'SUSTURUCU':
            for k in range(4):
                yy = ym + 20 + k * 62
                c.R(s0 + 8, yy, s1 - 8, yy + 35)
        elif ad in ('ÇIKIŞ', 'TAZE HAVA'):
            _damper(c, s0 + 5, s1 - 5, ym + 20, W_KS - 20, 6)
    for s0, s1, ad in DONUS:
        if ad != 'ISI GERİ KAZANIM':
            c.L(s0, 0, s0, ym)
        if ad == 'DÖNÜŞ FANI':
            _fan(c, (s0 + s1) / 2, ym / 2, 70)
        elif 'FİLTRE' in ad:
            _filtre(c, s0 + 15, s1 - 15, 10, ym - 10, 8)
        elif ad == 'SUSTURUCU':
            for k in range(4):
                yy = 20 + k * 62
                c.R(s0 + 8, yy, s1 - 8, yy + 35)
        elif ad in ('DÖNÜŞ', 'EGZOZ'):
            _damper(c, s0 + 5, s1 - 5, 20, ym - 20, 6)
    # plakalı eşanjör
    c.P([(630, 10), (730, ym), (630, W_KS - 10), (530, ym)], kapali=True)
    c.L(530, ym, 730, ym)
    c.L(630, 10, 630, W_KS - 10)
    # karışım damperi
    for k in range(5):
        xx = 460 + k * 14
        c.L(xx, ym - 10, xx + 10, ym + 10)
    # hava akış okları
    _ok(c, L_KS + 120, W_KS * 0.75, L_KS + 10, W_KS * 0.75)
    _ok(c, -10, W_KS * 0.75, -120, W_KS * 0.75)
    _ok(c, -120, W_KS * 0.25, -10, W_KS * 0.25)
    _ok(c, L_KS + 10, W_KS * 0.25, L_KS + 120, W_KS * 0.25)
    _ok(c, 490, ym - 60, 490, ym + 60)
    c.T('TAZE HAVA', L_KS + 70, W_KS * 0.75 + 12, al='BC')
    c.T('EGZOZ', L_KS + 70, W_KS * 0.25 + 12, al='BC')
    c.T('ÜFLEME', -65, W_KS * 0.75 + 12, al='BC')
    c.T('DÖNÜŞ', -65, W_KS * 0.25 + 12, al='BC')
    # modül adları (bölmelerin dışına, üst ve alt)
    for s0, s1, ad in UFLEME:
        c.T(ad, (s0 + s1) / 2, W_KS + 18, h=24, al='ML', rot=90)
    for s0, s1, ad in DONUS:
        if ad in ('SERVİS',):
            continue
        c.T(ad, (s0 + s1) / 2, -18, h=24, al='MR', rot=90)
    c.T('ÜFLEME BÖLMESİ', 160, W_KS - 30, h=26, al='TL')
    c.T('DÖNÜŞ / EGZOZ BÖLMESİ', 300, 30, h=26, al='BL')
    c.olcu(0, W_KS + 102, L_KS, W_KS + 102, f'{L_KS:.0f}', ofs=0)
    c.olcu(L_KS + 165, 0, L_KS + 165, W_KS, f'{W_KS:.0f}', ofs=0)
    # ------------------------------------------------- A-A BOYUNA KESİT (üfleme bölmesi)
    ax, ay = bx, y0 + 3350
    DT._cerceve(m, ax - 650, ay - 550, ax + L_KS * K + 900, ay + (H_KS + H_KAIDE) * K + 450, 12,
                'KLİMA SANTRALİ A-A KESİTİ (ÜFLEME BÖLMESİ)', '1/25', kutular)
    c = DT.Cz(m, ax, ay, K, kutular)
    c.R(-10, 0, L_KS + 10, H_KAIDE)
    c.tara([(-10, 0), (L_KS + 10, 0), (L_KS + 10, H_KAIDE), (-10, H_KAIDE)], 'AR-CONC', 0.5)
    z0, z1 = H_KAIDE, H_KAIDE + H_KS
    c.R(0, z0, L_KS, z1)
    c.R(0, z0 + 10, L_KS, z1 - 10)
    for s0, s1, ad in UFLEME:
        c.L(s0, z0, s0, z1)
        mid = (s0 + s1) / 2
        if ad == 'ÜFLEME FANI':
            _fan(c, mid, (z0 + z1) / 2, 75)
            c.R(s0 + 20, z0 + 10, s1 - 20, z0 + 25)
        elif ad in ('DX ISITMA', 'DX SOĞUTMA'):
            _batarya(c, s0 + 8, s1 - 8, z0 + 30, z1 - 15)
        elif 'FİLTRE' in ad:
            _filtre(c, s0 + 15, s1 - 15, z0 + 15, z1 - 15, 8)
        elif ad == 'SUSTURUCU':
            _susturucu(c, s0, s1, z0 + 15, z1 - 15, 3)
        elif ad in ('ÇIKIŞ', 'TAZE HAVA'):
            _damper(c, s0 + 5, s1 - 5, z0 + 25, z1 - 25, 6)
        elif ad == 'ISI GERİ KAZANIM':
            c.P([(mid, z0 + 12), (s1 - 10, (z0 + z1) / 2), (mid, z1 - 12), (s0 + 10, (z0 + z1) / 2)], kapali=True)
        c.T(ad, mid, z1 + 15, h=24, al='ML', rot=90)
    # damla tavası + sifon (soğutma bataryası ve eşanjör altı)
    for s0, s1 in ((300, 380), (530, 730)):
        c.P([(s0 + 4, z0 + 26), (s0 + 4, z0 + 18), (s1 - 4, z0 + 18), (s1 - 4, z0 + 26)])
        xd = s1 - 20
        c.P([(xd, z0 + 18), (xd, z0 - 8), (xd + 10, z0 - 8), (xd + 10, z0 - 22), (xd - 10, z0 - 22),
             (xd - 10, z0 - 14), (xd + 30, z0 - 14)])
    _ok(c, L_KS + 120, (z0 + z1) / 2, L_KS + 10, (z0 + z1) / 2)
    _ok(c, -10, (z0 + z1) / 2, -120, (z0 + z1) / 2)
    c.etiket('DAMLA TAVASI + SİFONLU YOĞUŞMA DRENAJI', 360, z0 - 12, 420, -55)
    c.etiket('BETON KAİDE + TİTREŞİM TAKOZU', 60, 8, 90, -55)
    c.olcu(0, -100, L_KS, -100, f'{L_KS:.0f}', ofs=0)
    c.olcu(L_KS + 165, 0, L_KS + 165, z1, f'{z1:.0f}', ofs=0)
    # ------------------------------------------------- B-B ENİNE KESİT (batarya hizası) + DÜ görünüşleri
    ex, ey = bx, y0 + 650
    DT._cerceve(m, ex - 650, ey - 300, ex + W_KS * K + 1000, ey + (H_KS + H_KAIDE) * K + 450, 13,
                'KLİMA SANTRALİ B-B KESİTİ', '1/25', kutular)
    c = DT.Cz(m, ex, ey, K, kutular)
    c.R(-10, 0, W_KS + 10, H_KAIDE)
    c.tara([(-10, 0), (W_KS + 10, 0), (W_KS + 10, H_KAIDE), (-10, H_KAIDE)], 'AR-CONC', 0.5)
    c.R(0, z0, W_KS, z1)
    c.L(W_KS / 2, z0, W_KS / 2, z1)
    _batarya(c, W_KS / 2 + 12, W_KS - 12, z0 + 30, z1 - 15)
    _susturucu(c, 12, W_KS / 2 - 12, z0 + 15, z1 - 15, 3)
    c.T('ÜFLEME BÖLMESİ', W_KS * 0.75, z1 + 15, h=26, al='BC')
    c.T('DÖNÜŞ BÖLMESİ', W_KS * 0.25, z1 + 15, h=26, al='BC')
    c.etiket('DX SOĞUTMA BATARYASI', W_KS * 0.75, z0 + 60, W_KS + 40, z0 + 40)
    c.etiket('PANEL: 50 mm TAŞ YÜNÜ, ÇİFT CİDARLI', W_KS, z1 - 40, W_KS + 40, z1 - 20)
    c.olcu(0, -60, W_KS, -60, f'{W_KS:.0f}', ofs=0)
    # DÜ görünüşleri
    gx = ex + W_KS * K + 1500
    DT._cerceve(m, gx - 250, ey - 300, gx + 2900, ey + (DU_H + H_KAIDE) * K + 450, 14,
                'DX DIŞ ÜNİTE GÖRÜNÜŞLERİ', '1/25', kutular)
    c = DT.Cz(m, gx, ey, K, kutular)
    c.R(-10, 0, DU_L + 10, H_KAIDE)
    c.R(0, H_KAIDE, DU_L, H_KAIDE + DU_H)
    for k in range(1, 12):
        yy = H_KAIDE + 15 + k * 12
        if yy < H_KAIDE + DU_H - 30:
            c.L(10, yy, DU_L - 10, yy, DT.KAT_T)
    for f in (0.27, 0.73):
        c.R(DU_L * f - 45, H_KAIDE + DU_H, DU_L * f + 45, H_KAIDE + DU_H + 12)
    c.T('ÖN GÖRÜNÜŞ', DU_L / 2, -30, al='TC')
    c.olcu(0, -55, DU_L, -55, f'{DU_L:.0f}', ofs=0)
    c.olcu(-40, H_KAIDE, -40, H_KAIDE + DU_H, f'{DU_H:.0f}', ofs=0)
    sx = DU_L + 120
    c.R(sx - 10, 0, sx + DU_W + 10, H_KAIDE)
    c.R(sx, H_KAIDE, sx + DU_W, H_KAIDE + DU_H)
    for k in range(1, 12):
        yy = H_KAIDE + 15 + k * 12
        if yy < H_KAIDE + DU_H - 30:
            c.L(sx + 8, yy, sx + DU_W - 8, yy, DT.KAT_T)
    c.T('YAN GÖRÜNÜŞ', sx + DU_W / 2, -30, al='TC')
    c.olcu(sx, -55, sx + DU_W, -55, f'{DU_W:.0f}', ofs=0)
    c.etiket('EKSENEL FAN (ÜSTTEN ATIŞ)', DU_L * 0.73, H_KAIDE + DU_H + 12, DU_L * 0.73 + 20, H_KAIDE + DU_H + 60)
    c.etiket('KONDENSER / EVAPORATÖR SERPANTİNİ', DU_L - 10, H_KAIDE + 100, sx + DU_W + 30, H_KAIDE + 150)
    c.etiket('GAZ + SIVI BAĞLANTISI', sx + DU_W, H_KAIDE + 30, sx + DU_W + 30, H_KAIDE + 60)
    # ------------------------------------------------- TEKNİK TABLO (sağ)
    tx, ty = bx + L_KS * K + 1300, y0 + h - 500
    sut = [700, 1300, 900, 900, 900, 900]
    satir = [('', 'ÖZELLİK', 'KS-1', 'KS-2', 'KS-3', 'KS-4')]
    keys = ['KS-1', 'KS-2', 'KS-3', 'KS-4']
    satir.append(('KS', 'Üfleme / dönüş debisi (m³/h)', *['40.000'] * 4))
    satir.append(('', 'Taze hava / egzoz (m³/h)', *[f'{deger[k]["taze"]:,.0f}'.replace(',', '.') for k in keys]))
    satir.append(('', 'Isı geri kazanım (plakalı) verimi', *['%75'] * 4))
    satir.append(('', 'DX soğutma bataryası (kW)', *[f'{deger[k]["qs"]:.0f}' for k in keys]))
    satir.append(('', 'DX ısıtma bataryası (kW)', *[f'{deger[k]["qi"]:.0f}' for k in keys]))
    satir.append(('', 'Üfleme fanı EC (kW)', *['17,0'] * 4))
    satir.append(('', 'Filtre taze / dönüş / üfleme', *['G4/G4/F7'] * 4))
    satir.append(('', 'Ölçü U×G×Y (cm)', *['830×545×220'] * 4))
    satir.append(('DÜ', 'Adet', *['2'] * 4))
    satir.append(('', 'Modül soğutma (kW, en az)', *[f'{deger[k]["du_qs"]:.0f}' for k in keys]))
    satir.append(('', 'Modül ısıtma nominal (kW, en az)', *[f'{deger[k]["du_qi"]:.0f}' for k in keys]))
    satir.append(('', 'Ölçü U×G×Y (cm)', *['240×110×190'] * 4))
    W = sum(sut)
    sh = 150
    DT._cerceve(m, tx - 150, ty - len(satir) * sh - 900, tx + W + 150, ty + 250, 15,
                'KLİMA SANTRALİ VE DIŞ ÜNİTE TEKNİK ÖZELLİKLERİ', None, kutular)
    y = ty
    for i, row in enumerate(satir):
        _rect(m, tx, y - sh, tx + W, y, DT.KAT)
        xx = tx
        for j, (wd, s) in enumerate(zip(sut, row)):
            if j:
                m.add_line((xx, y), (xx, y - sh), dxfattribs={'layer': DT.KAT})
            if s:
                hh = 34 if i else 36
                al = 'ML' if j == 1 else 'MC'
                px = xx + 25 if j == 1 else xx + wd / 2
                gw = DT.genislik(s, hh)
                if gw > wd - 40:
                    hh = hh * (wd - 40) / gw
                _yazi(m, s, px, y - sh / 2, hh, al, K_Y, kutular=kutular)
            xx += wd
        y -= sh
    notlar = ['Batarya kapasiteleri ISI_KAZANCI_VE_KLIMA_SANTRALI_HESABI.xlsx dosyasından alınmıştır.',
              'Dış ünite ısıtma kapasitesi −3 °C dış havada sağlanacak şekilde seçilecektir.',
              'Plakalı eşanjöre donma koruması için by-pass damperi konulacaktır.',
              'Cihaz ölçüleri yaklaşık olup üretici seçimine göre kesinleşecektir.']
    for k, s in enumerate(notlar):
        _yazi(m, f'{k + 1}. {s}', tx, y - 120 - k * 90, 34, 'ML', K_Y, kutular=kutular)


# =========================================================================================== bina kesitleri
def _kes_kopyala(msp, kaynak_msp, bolge, dx, dy):
    """kaynak kesit çiziminden bölgeyi (INSERT patlatılarak) tek gri katmana kopyalar."""
    from ezdxf import bbox as _bb
    x0, y0, x1, y1 = bolge
    n = 0

    def it(es, derin=0):
        for e in es:
            if e.dxftype() == 'INSERT' and derin < 4:
                try:
                    yield from it(e.virtual_entities(), derin + 1)
                except Exception:
                    pass
            else:
                yield e
    for e in it(kaynak_msp):
        t = e.dxftype()
        if t not in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE', 'TEXT', 'MTEXT', 'SPLINE', 'ELLIPSE', 'HATCH'):
            continue
        try:
            b = _bb.extents([e], fast=True)
        except Exception:
            continue
        if not b.has_data or b.extmin.x < x0 or b.extmax.x > x1 or b.extmin.y < y0 or b.extmax.y > y1:
            continue
        try:
            c = e.copy()
        except Exception:
            continue
        c.dxf.layer = K_M
        if c.dxf.hasattr('linetype'):
            c.dxf.linetype = 'BYLAYER'
        if c.dxf.hasattr('color'):
            c.dxf.color = 256
        if t in ('TEXT', 'MTEXT'):
            c.dxf.style = STIL
        if t == 'HATCH' and c.dxf.hasattr('associative'):
            c.dxf.associative = 0
        c.translate(dx, dy, 0)
        msp.add_entity(c)
        n += 1
    return n


# ------------------------------------------------------------------------------------------- ağ özeti
def ag_ozeti(msp, sistem_no):
    """Plan kanallarından kesitler için özet: her sistem için ana kolon x/y aralıkları ve branşman sıraları."""
    from collections import defaultdict
    hat = {'MTY-UFLEME-KANALI': 'U', 'MTY-DONUS-KANALI': 'D'}
    dikey = defaultdict(list)      # (sis, sınıf) → [(x, y0, y1)]
    yatay = defaultdict(list)      # (sis, sınıf) → [(y, x0, x1)]
    menfez = defaultdict(list)     # (sis, sınıf) → [(x, y, r)]
    for e in msp.query('LWPOLYLINE CIRCLE'):
        k = hat.get(e.dxf.layer)
        if not k:
            continue
        if e.dxftype() == 'CIRCLE':
            x, y = e.dxf.center[0], e.dxf.center[1]
            if 50700 < x < 72000 and y < 7300:
                menfez[(sistem_no(x), k)].append((x, y, e.dxf.radius))
            continue
        p = [tuple(q) for q in e.get_points('xy')]
        for a, b in zip(p, p[1:]):
            if abs(a[0] - b[0]) < 1 and abs(a[1] - b[1]) > 300:
                dikey[(sistem_no(a[0]), k)].append((a[0], min(a[1], b[1]), max(a[1], b[1])))
            elif abs(a[1] - b[1]) < 1 and abs(a[0] - b[0]) > 50:
                yatay[(sistem_no(min(a[0], b[0])), k)].append((a[1], min(a[0], b[0]), max(a[0], b[0])))
    ozet = {}
    for (s, k), mm in menfez.items():
        # sıralar: menfez y'lerini 60 cm içinde grupla
        gr = []
        for x, y, r in sorted(mm, key=lambda t: t[1]):
            if gr and abs(gr[-1][-1][1] - y) < 60:
                gr[-1].append((x, y, r))
            else:
                gr.append([(x, y, r)])
        siralar = []
        for g in gr:
            if len(g) < 3:
                continue
            yc = sum(t[1] for t in g) / len(g)
            cand = [t for t in yatay[(s, k)] if yc - 70 < t[0] < yc + 5 and t[2] - t[1] > 300]
            xa = min([t[1] for t in cand] + [min(t[0] for t in g) - 60])
            xb = max([t[2] for t in cand] + [max(t[0] for t in g) + 60])
            siralar.append(dict(y=yc, x0=xa, x1=xb, menfez=sorted((t[0], t[2]) for t in g)))
        ozet.setdefault(s, {})[k + '_sira'] = siralar
    for (s, k), dd in dikey.items():
        uzun = sorted(dd, key=lambda t: -(t[2] - t[1]))[:2]
        if len(uzun) == 2:
            xs = sorted(t[0] for t in uzun)
            ozet.setdefault(s, {})[k + '_kolon'] = dict(x0=xs[0], x1=xs[1], y0=min(t[1] for t in dd if xs[0] - 1 <= t[0] <= xs[1] + 1),
                                                       y1=max(t[2] for t in uzun))
    return ozet


H_R = {22: 45, 28: 60, 34: 80}        # menfez yarıçapı (çizim) → kanal yüksekliği (cm): 600x450, 900x600, 1000x800


def _kanal_kesit(m, x0, x1, z0, z1, kat, gizli=False):
    e = m.add_lwpolyline([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], close=True, dxfattribs={'layer': kat})
    if not gizli:
        m.add_line((x0, z0), (x1, z1), dxfattribs={'layer': kat})
        m.add_line((x0, z1), (x1, z0), dxfattribs={'layer': kat})
    return e


def _menfez_kesit(m, xc, z, kat, w=50.0):
    m.add_lwpolyline([(xc - w / 2, z), (xc - w * 0.35, z - 12), (xc - w * 0.7, z - 18), (xc + w * 0.7, z - 18),
                      (xc + w * 0.35, z - 12), (xc + w / 2, z)], dxfattribs={'layer': kat})


def kesitler_paftasi(m, x0, y0, kes_msp, ozet, ks_b, du_b, kutular):
    """AA (kuzey–güney) ve BB (doğu–batı) kesitleri: mimari gri + santral, dış ünite, kanallar, menfezler."""
    # ---------------- AA: kaynak bölge, yerleşim
    AA_SRC = (77182.0, 21300.0, 89100.0, 23700.0)
    AA0 = 21935.0                                   # ±0.00
    aa_dx, aa_dy = x0 + 800 - AA_SRC[0], y0 + 5900 - AA0
    _kes_kopyala(m, kes_msp, AA_SRC, aa_dx, aa_dy)
    ax = lambda py: 81753.0 + (py - 1549.0) * 5701.0 / 5730.0 + aa_dx      # plan y → AA x
    az = lambda kot: AA0 + kot * 100.0 + aa_dy                            # kot (m) → y
    s = 1                                                                 # KS-1 / 1. sistem
    o = ozet.get(s, {})
    # ana kolonlar (üfleme + dönüş, aynı kotta yan yana): duvardan güney uçlarına kadar + dışarıda düşey
    for k, kat in (('D', K_KD), ('U', K_KU)):
        kol = o.get(k + '_kolon')
        if not kol:
            continue
        _kanal_kesit(m, ax(kol['y0']), ax(7300.0), az(4.80), az(6.00), kat, gizli=(k == 'D'))
    b = ks_b[0]
    # dış kısım: duvardan santral üstüne yatay + düşey
    xa, xb = ax(7300.0), ax(b[1] + (b[3] - b[1]) * 0.6)
    m.add_lwpolyline([(xa, az(4.80)), (xb - 160, az(4.80)), (xb - 160, az(2.35)), (xb, az(2.35)), (xb, az(6.00)),
                      (xa, az(6.00))], close=True, dxfattribs={'layer': K_KU})
    # santral (kaide + gövde) ve dış ünite
    xk0, xk1 = ax(b[1]), ax(b[3])
    _rect(m, xk0 - 10, az(-0.20), xk1 + 10, az(-0.05))
    _rect(m, xk0, az(-0.05), xk1, az(2.15))
    m.add_line(((xk0 + xk1) / 2, az(-0.05)), ((xk0 + xk1) / 2, az(2.15)), dxfattribs={'layer': K_CIHAZ})
    d = du_b[0][0]
    xd0, xd1 = ax(d[1]), ax(d[3])
    _rect(m, xd0 - 10, az(-0.20), xd1 + 10, az(-0.05))
    _rect(m, xd0, az(-0.05), xd1, az(1.85))
    m.add_lwpolyline([((xd0 + xd1) / 2 - 8, az(1.85)), ((xd0 + xd1) / 2 - 8, az(2.60)), (xk1 - 60, az(2.60)),
                      (xk1 - 60, az(2.15))], dxfattribs={'layer': K_SOG, 'ltscale': 0.5})
    # branşman kesitleri + menfezler
    for k, kat in (('U', K_KU), ('D', K_KD)):
        for sr in o.get(k + '_sira', []):
            if sr['x0'] > 56000 or sr['x1'] < 54000:
                continue
            h = 80
            x_0, x_1 = ax(sr['y'] - 50), ax(sr['y'] + 50)
            _kanal_kesit(m, x_0, x_1, az(6.00 - h / 100), az(6.00), kat)
            _menfez_kesit(m, (x_0 + x_1) / 2, az(6.00 - h / 100), kat)
    c = DT.Cz(m, 0, 0, 1.0, kutular)
    c.etiket('ÜFLEME VE DÖNÜŞ ANA KANALLARI 1600×1200 (YAN YANA)', ax(4300), az(5.40), ax(3300), az(7.40))
    c.etiket('BRANŞMAN KANALI 1000×800 + KANAL ALTI YUVARLAK MENFEZ', ax(5200), az(5.30), ax(4600), az(3.60))
    c.etiket('DUVAR GEÇİŞİ (DETAY-4)', ax(7300), az(5.40), ax(7500), az(7.70))
    c.etiket(f'KS-1 ISI GERİ KAZANIMLI KLİMA SANTRALİ (BETON KAİDE ÜZERİNDE)', (xk0 + xk1) / 2, az(1.50), ax(6100), az(1.20), sag=False)
    c.etiket('DX DIŞ ÜNİTE', (xd0 + xd1) / 2, az(1.50), xd1 + 120, az(3.00))
    c.etiket('SOĞUTUCU AKIŞKAN HATTI', (xd1 + xk1) / 2, az(2.60), xd1 + 120, az(3.60))
    for kot, s_ in ((6.00, 'KANAL ÜST KOTU +6.00 (MAKAS ALTI)'), (4.80, 'ANA KANAL ALT KOTU +4.80'),
                    (5.20, 'BRANŞMAN ALT KOTU +5.20')):
        m.add_line((ax(-2400), az(kot)), (ax(-1300), az(kot)), dxfattribs={'layer': K_Y})
        _yazi(m, s_, ax(-2400), az(kot) + 8, 26, 'BL', K_Y, kutular=kutular)
    _yazi(m, 'AA KESİTİ — CİHAZ VE KANAL YERLEŞİMİ  ÖLÇEK : 1/100', x0 + 800 + (AA_SRC[2] - AA_SRC[0]) / 2,
          y0 + 5900 - 950, 60, 'MC', 'ROTAS-PAFTA-YAZI', kutular=kutular)
    # ---------------- BB
    BB_SRC = (90200.0, 21300.0, 116200.0, 23700.0)
    BB0 = 21940.0
    bb_dx, bb_dy = x0 + 800 - BB_SRC[0], y0 + 1800 - BB0
    _kes_kopyala(m, kes_msp, BB_SRC, bb_dx, bb_dy)
    bx = lambda px: px + 41380.0 + bb_dx
    bz = lambda kot: BB0 + kot * 100.0 + bb_dy
    for s, o in sorted(ozet.items()):
        # ana kolon kesitleri
        for k, kat in (('U', K_KU), ('D', K_KD)):
            kol = o.get(k + '_kolon')
            if kol:
                _kanal_kesit(m, bx(kol['x0']), bx(kol['x1']), bz(4.80), bz(6.00), kat)
        # üfleme branşmanı görünüşü (5200 sırası; 4. sistemde iki taraflı en uzun sıra)
        sir = sorted(o.get('U_sira', []), key=lambda t: -(t['x1'] - t['x0']))
        if not sir:
            continue
        sr = min(sir[:2], key=lambda t: abs(t['y'] - 5200)) if s != 4 else sir[0]
        kol = o.get('U_kolon')
        mf = sr['menfez']
        sinir = [sr['x0']]
        for (xa_, ra), (xb_, rb) in zip(mf, mf[1:]):
            if kol and xa_ < kol['x0'] < xb_:
                sinir += [kol['x0'] - 40, kol['x1'] + 40]
            else:
                sinir.append((xa_ + xb_) / 2)
        sinir.append(sr['x1'])
        araliklar = [(a_, b_) for a_, b_ in zip(sinir, sinir[1:])
                     if not (kol and a_ >= kol['x0'] - 41 and b_ <= kol['x1'] + 41) and b_ - a_ > 5]
        for u, v in araliklar:
            ic = [(xm, r) for xm, r in mf if u <= xm <= v]
            r = ic[0][1] if ic else 28
            h = H_R.get(round(r), 60)
            m.add_lwpolyline([(bx(u), bz(6.00)), (bx(v), bz(6.00)), (bx(v), bz(6.00 - h / 100)),
                              (bx(u), bz(6.00 - h / 100))], close=True, dxfattribs={'layer': K_KU})
            for xm, _ in ic:
                _menfez_kesit(m, bx(xm), bz(6.00 - h / 100), K_KU)
    c = DT.Cz(m, 0, 0, 1.0, kutular)
    o1 = ozet.get(1, {})
    if o1.get('U_kolon'):
        k1 = o1['U_kolon']
        c.etiket('ÜFLEME / DÖNÜŞ ANA KANAL KESİTİ 1600×1200', bx(k1['x1']), bz(5.40), bx(k1['x1']) + 500, bz(7.60))
    c.etiket('ÜFLEME BRANŞMANI (1000×800 → 900×600 → 600×450) + MENFEZLER', bx(53300), bz(5.60), bx(52000), bz(3.40))
    for kot, s_ in ((6.00, 'KANAL ÜST KOTU +6.00'), (5.20, 'BRANŞMAN ALT KOTU +5.20 / +5.40 / +5.55')):
        m.add_line((bx(50900), bz(kot)), (bx(51900), bz(kot)), dxfattribs={'layer': K_Y})
        _yazi(m, s_, bx(50900), bz(kot) + 12, 30, 'BL', K_Y, kutular=kutular)
    _yazi(m, 'BB KESİTİ — CİHAZ VE KANAL YERLEŞİMİ  ÖLÇEK : 1/100', x0 + 800 + (BB_SRC[2] - BB_SRC[0]) / 2,
          y0 + 1800 - 900, 60, 'MC', 'ROTAS-PAFTA-YAZI', kutular=kutular)
