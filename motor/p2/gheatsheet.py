"""Isıtma / klima paftası elemanları: yerden ısıtma kolon şeması, devre çizelgesi, klima hesap tablosu, U tablosu."""
import math, sys
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import cad
from cad import L, PL, C, T, RECT, RRECT, ARC
import mtyblk
import gp
from gp import YZ, CD, PEX, HGL, HDL, HCAP
import gheat as GH
import gklima as GK

RED = 'MTY-KAT-ADI'
KOL = 'MTY-KOLLETOR'


def _daire_blok(x, y, side_nm, circ, tot, step=200):
    kx = x
    RRECT(kx, y + 150, kx + 70, y + 270, 5, CD); C((kx + 35, y + 215), 14, CD)
    L((kx + 25, y + 215), (kx + 45, y + 215), CD); L((kx + 35, y + 205), (kx + 35, y + 225), CD)
    T((kx + 35, y + 285), 'H. KOMBİ 24 kW', 9, CD, 'C')
    T((kx + 35, y + 300), side_nm, 12, YZ, 'C')
    n = len(circ)
    c0 = kx + 200
    c1 = c0 + n * step
    RECT(c0 - 15, y + 160, c1 + 15, y + 210, KOL)
    L((c0 - 10, y + 198), (c1 + 10, y + 198), HGL)
    L((c0 - 10, y + 172), (c1 + 10, y + 172), HDL)
    T(((c0 + c1) / 2, y + 128), 'KOLLEKTÖR %d AĞIZLI (DEBİMETRELİ, VANALI, PURJÖRLÜ)' % n, 7, KOL, 'C')
    PL([(kx + 70, y + 240), (c0 - 30, y + 240), (c0 - 30, y + 198), (c0 - 10, y + 198)], HGL, w=2.0)
    PL([(kx + 70, y + 180), (c0 - 40, y + 180), (c0 - 40, y + 172), (c0 - 10, y + 172)], HDL, w=2.0)
    T((kx + 76, y + 246), '%dW-DN20' % round(tot), 7, HCAP, 'L')
    T((kx + 76, y + 184), 'DÖNÜŞ DN20', 6, HCAP, 'L')
    for j, d in enumerate(circ):
        px = c0 + step / 2 + j * step
        PL([(px - 6, y + 198), (px - 6, y + 400)], PEX, w=1.2)
        PL([(px + 6, y + 172), (px + 6, y + 400)], PEX, w=1.2)
        ARC((px, y + 400), 6, 0, 180, PEX)
        C((px - 6, y + 198), 2, KOL); C((px + 6, y + 172), 2, KOL)
        T((px, y + 145), 'P%d' % d['port'], 9, KOL, 'C')
        T((px - 14, y + 215), 'ISIKAYBI %d / %dW / %.2f m / Z%s' % (d['port'], round(d['W']), d['L'], d['zone']), 6.5,
          'MTY-ISIKAYBIMAHAL', 'L', 90)
        T((px + 22, y + 215), '%d°C / PEX 16x2.0 / %d cm / %s' % (d['ti'], d['s'], d['room']), 6.5, HCAP, 'L', 90)
        T((px + 36, y + 215), '%dW-DN15 (DÖNÜŞ)' % round(d['W']), 6.5, HCAP, 'L', 90)
    return c1 + 15


def isitma_sema(ox, oy, HEAT, floors):
    """HEAT: {kat: {'a': (circ, calc), 'b': ...}}; floors: [(kat, ad, daire_a, daire_b)] alttan üste"""
    top = oy + 60 + len(floors) * 540 + 60
    T((ox + 1850, top + 30), 'YERDEN ISITMA KOLON ŞEMASI', 26, YZ, 'C')
    T((ox + 1850, top + 2), '(HER DAİREDE 1 ADET 24 kW HERMETİK YOĞUŞMALI KOMBİ - KOLLEKTÖR - PEX 16x2,0 DEVRELER, 45/35 °C)', 9,
      YZ, 'C')
    for i, fl in enumerate(floors):
        k, ad, names = fl[0], fl[1], fl[2:]
        y = oy + 60 + i * 540
        L((ox + 60, y), (ox + 3700, y), 'MTY-SEMA')
        T((ox + 3720, y + 20), ad, 15, RED, 'L', 90)
        xa = ox + 130
        for side, nm in zip(('a', 'b'), names):
            circ, calc = HEAT[k][side]
            tot = sum(c['W'] for c in circ)
            xa = _daire_blok(xa, y, nm, circ, tot) + 160


def isitma_tablo(x, y, HEAT, floors):
    T((x, y), 'YERDEN ISITMA DEVRE ÇİZELGESİ VE KONTROLLER', 16, YZ, 'L')
    T((x, y - 20), 'Devre yükü = mahal ısı kaybı x (devre alanı / mahal boru alanı).  EN 1264: θF = θi + (q/8,92)^0,91 ;  '
      'sınır θF ≤ 29 °C (oturma), ≤ 33 °C (banyo).  Devre boyu bağlantı boruları dahil ≤ 80 m.', 7, YZ, 'L')
    hdr = ['KAT', 'DAİRE', 'P', 'MAHAL', 'ZON', 'θi', 'ARALIK', 'L (m)', 'YÜK (W)', 'q (W/m²)', 'θF (°C)', 'KONTROL']
    cx = [0, 50, 110, 140, 290, 350, 390, 450, 510, 580, 650, 720]
    yy = y - 45
    for c, s in zip(cx, hdr):
        T((x + c, yy), s, 7.5, YZ, 'L')
    L((x, yy - 5), (x + 860, yy - 5), YZ)
    yy -= 18
    for fl in floors:
        k, ad, names = fl[0], fl[1], fl[2:]
        for side, nm in zip(('a', 'b'), names):
            circ, calc = HEAT[k][side]
            for d in circ:
                q = d['W'] / d['Ar']
                tf = d['ti'] + (q / 8.92) ** 0.91
                lim = 33.0 if d['room'] == 'BANYO' else 29.0
                ok = 'UYGUN' if tf <= lim and d['L'] <= 80 else 'KONTROL'
                vals = [ad.replace(' KAT', ''), nm, 'P%d' % d['port'], d['room'], 'Z' + d['zone'], '%d' % d['ti'],
                        '%d cm' % d['s'], '%.1f' % d['L'], '%d' % round(d['W']), '%.0f' % q, '%.1f' % tf, ok]
                for c, s in zip(cx, vals):
                    T((x + c, yy), s, 7, YZ, 'L')
                yy -= 14
            tot = sum(c['W'] for c in circ)
            T((x + 140, yy), '%s TOPLAMI : %d W (%d kcal/h)  -  24 kW KOMBİ YETERLİ' % (nm, round(tot), round(tot * 0.86)), 7.5,
              YZ, 'L')
            yy -= 20
    return yy


def klima_tablo(x, y, KL):
    T((x, y), 'ZEMİN KAT İŞ YERLERİ - DUVAR TİPİ SPLİT KLİMA ISI KAZANCI VE SEÇİMİ', 16, YZ, 'L')
    T((x, y - 20), 'Dış: %d °C KT / %d °C YT (Sakarya), iç: %d °C %%%d.  Duvar U=%.2f, cam U=%.2f W/m²K, SC=%.2f, CLF=%.2f, '
      '%d m²/kişi, aydınlatma %d W/m², cihaz %d W/m², taze hava %d l/s.kişi, emniyet %%10.' %
      (GK.T_YAZ_DIS, GK.T_YAZ_YAS, GK.T_YAZ_IC, GK.RH_IC, GK.U_DUVAR, GK.U_CAM, GK.SC_CAM, GK.CLF_CAM, GK.KISI_M2,
       GK.AYD_W, GK.CIH_W, GK.TAZE_LS), 7, YZ, 'L')
    yy = y - 45
    cx = [0, 170, 220, 300, 380, 460]
    for r in KL:
        k = r['kaz']
        T((x, yy), '%s  (A = %.2f m², %d kişi)' % (r['S']['name'], r['S']['A'], k['n']), 9, YZ, 'L')
        yy -= 16
        for c, s in zip(cx, ['KALEM', 'YÖN', 'A / ADET', 'U / KATSAYI', 'ΔT / q', 'Q (W)']):
            T((x + c, yy), s, 7, YZ, 'L')
        L((x, yy - 4), (x + 540, yy - 4), YZ)
        yy -= 14
        for row in k['rows'] + k['gl']:
            vals = [row[0], row[1], '%.2f' % row[2], '%.3g' % row[3], '%.4g' % row[4], '%.0f' % row[5]]
            for c, s in zip(cx, vals):
                T((x + c, yy), s, 6.5, YZ, 'L')
            yy -= 12
        T((x, yy), 'Duyulur %.0f W + gizli %.0f W, x1,10 = TOPLAM ISI KAZANCI %.0f W (SHR %.2f)' %
          (k['Qd'], k['Qg'], k['Q'], k['SHR']), 7.5, YZ, 'L')
        yy -= 13
        T((x, yy), 'ISI KAYBI (TS 825, -6 °C) = %.0f W  →  SEÇİM: %d ADET %d BTU/h (%.2f kW soğutma, %.2f kW ısıtma) '
          'İNVERTER DUVAR TİPİ SPLİT KLİMA' % (r['kay']['Q'], r['adet'], r['btu'], r['adet'] * r['kw'], r['adet'] * r['kw'] * 1.1),
          7.5, YZ, 'L')
        yy -= 22
    return yy


def u_tablo(x, y):
    T((x, y), 'TS 825 U DEĞERLERİ (HESAPTA KULLANILAN)', 14, YZ, 'L')
    yy = y - 24
    for k, v in GH.ASSY.items():
        lim = v[4]
        st = ('≤ %.2f UYGUN' % lim) if lim else '(ısıtılan hacimler arası)'
        T((x, yy), '%-5s U = %.3f W/m²K  %s  -  %s' % (k, GH.U[k], st, v[0]), 7, YZ, 'L')
        yy -= 13
    T((x, yy), 'ÇP    U = 1.80 W/m²K  ≤ 1.80 UYGUN  -  PVC doğrama + Low-E ısıcam', 7, YZ, 'L')
    return yy - 13
