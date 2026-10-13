# -*- coding: utf-8 -*-
"""Şemalar: sıhhi (temiz/sıcak/sirkülasyon) kolon şeması, pis su kolon şeması, ısıtma kolon şeması, kazan dairesi
tesisat şeması, havalandırma şeması; lejantlar, notlar, hesap özet tabloları."""
import math
from veri import *
from tlib import *
from isitma import R
from sihhi import inch, sirk_cap, YB_S, YB_H, PIS_KOL
from hesap import dn_isitma

HT = 12.0     # şema yazı yüksekliği


def band(x0, x1, ys, names, title, ty):
    T(x0, ty, title, 40, TSEMA, TA.BOTTOM_LEFT)
    for y, n in zip(ys, names):
        PL([(x0, y), (x1, y)], TSEMA)
        T(x0 + 10, y + 12, n, 16, TSEMA, TA.BOTTOM_LEFT)


def lab(p, s, h=HT, lay=TY, al=TA.BOTTOM_LEFT, rot=0.0):
    T(p[0], p[1], s, h, lay, al, rot, mask=True)


def vlab(a, b, s, h=10.0, lay=TCAP):
    """düşey hat yanında yazı"""
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    T(m[0] - 8, m[1], s, h, lay, TA.BOTTOM_CENTER, 90, mask=True)


def hlab(a, b, s, h=10.0, lay=TCAP, f=0.5):
    m = (a[0] + (b[0] - a[0]) * f, a[1])
    T(m[0], m[1] + 6, s, h, lay, TA.BOTTOM_CENTER, 0, mask=True)


def box(x0, y0, x1, y1, lay, t=None, h=HT):
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, closed=True)
    if t:
        for k, s in enumerate(t.split('\n')):
            T((x0 + x1) / 2, (y0 + y1) / 2 + (len(t.split('\n')) / 2 - k - 0.5) * h * 1.4, s, h, lay, TA.MIDDLE_CENTER)


# =================================================================== SIHHİ TEMİZ SU ŞEMASI (S sırası)
def sihhi_sema(X0=258900.0, YT=-440500.0):
    yb, yz, y1, y2, yc = YT - 3200, YT - 2600, YT - 2000, YT - 1400, YT - 800
    band(X0 - 100, 276500, [yb, yz, y1, y2, yc], ["BODRUM KAT -3,50", "ZEMİN KAT ±0,00", "1. KAT +3,50", "2. KAT +6,50", "ÇATI +9,50"],
         "TEMİZ SU / SICAK SU / SİRKÜLASYON KOLON ŞEMASI (3 BORULU MERKEZİ SICAK SU)", YT - 200)
    # --- kazan dairesi
    k0 = X0 + 200
    box(k0 - 100, yb - 80, k0 + 2900, yb + 520, CHZ)
    lab((k0 - 80, yb + 530), "KAZAN DAİRESİ (SIĞINAK İÇİ)", 14, CHZ)
    ys = yb + 120
    PL([(k0 - 300, ys), (k0 + 700, ys)], SS)
    lab((k0 - 300, ys + 8), "ŞEBEKEDEN Ø50", 11, TCAP)
    VANA((k0 - 150, ys), 0, 'DN40', 1.6); PISLIK((k0 - 80, ys), 0, 'DN40', 1.6); SAYAC((k0 + 0, ys), 0, 'DN40', 1.8)
    CEKV((k0 + 80, ys), 0, 'DN40', 1.6)
    lab((k0 - 40, ys - 40), "ANA SAYAÇ DN40", 10, SAY)
    dv = R['depo']['Vsec'] // 2
    for i, x in enumerate((k0 + 250, k0 + 500)):
        box(x - 90, yb + 20, x + 90, yb + 300, CHZ, f"DEPO-{i + 1}\n{dv} m³")
        PL([(x - 60, ys), (x - 60, yb + 300 - 10)], SS) if False else None
    PL([(k0 + 160, ys), (k0 + 160, yb + 330), (k0 + 590, yb + 330)], SS)
    for x in (k0 + 250, k0 + 500):
        PL([(x, yb + 330), (x, yb + 300)], SS)
        VANA((x, yb + 315), 90, 'DN40', 1.2)
    lab((k0 + 170, yb + 340), "ŞAMANDIRALI DOLUM", 9, TCAP)
    # hidrofor
    PL([(k0 + 590, yb + 40), (k0 + 820, yb + 40)], SS)
    for x in (k0 + 680, k0 + 760):
        INS("T-POMPA", (x, yb + 40), 0, 2.0, lay=CHZ)
    box(k0 + 640, yb - 40, k0 + 800, yb + 5, CHZ, "HİDROFOR", 9)
    lab((k0 + 620, yb - 70), f"{R['hidrofor']['tip']}", 9, CHZ)
    lab((k0 + 620, yb - 85), f"Q={R['hidrofor']['Q']} m³/h  Hbas={R['hidrofor']['Halt']}/{R['hidrofor']['Hust']} mSS  2x{R['hidrofor']['P']} kW", 9, CHZ)
    INS("T-GENLESME", (k0 + 880, yb + 90), 0, 1.6, lay=CHZ); lab((k0 + 900, yb + 120), f"{R['hidrofor']['Vn']} L", 9, CHZ)
    PL([(k0 + 820, yb + 40), (k0 + 880, yb + 40), (k0 + 880, yb + 60)], SS)
    # SS ana dağıtım
    YSS = yb + 220
    PL([(k0 + 820, yb + 40), (k0 + 950, yb + 40), (k0 + 950, YSS), (X0 + 3400 + 2 * 300 + 14 * 260 + 600 + 4 * 260 + 10, YSS)], SS, 2.0)
    yb_top = 28 * YB_S + 5
    hlab((k0 + 950, YSS), (k0 + 1300, YSS), f"{inch(yb_top)} {yb_top:.1f} MB", 11)
    # yumuşatma + boyler
    bx = k0 + 1800
    PL([(k0 + 1300, YSS), (k0 + 1300, yb + 160), (bx - 150, yb + 160)], SS)
    box(k0 + 1380, yb + 120, k0 + 1480, yb + 200, CHZ, "YUMUŞ.", 9)
    box(bx - 120, yb - 20, bx + 120, yb + 450, CHZ, f"BOYLER\n{R['boyler']['Vsec']} L\nÇİFT SERP.", 12)
    PL([(bx - 150, yb + 160), (bx - 150, yb + 20), (bx - 120, yb + 20)], SS)
    # serpantin (kazandan)
    for k in range(5):
        PL([(bx - 60, yb + 80 + k * 30), (bx + 60, yb + 95 + k * 30)], IG)
    lab((bx + 130, yb + 100), f"SERPANTİN {R['boyler']['P_serp']} kW (kazandan 75/55)", 9, ICAP)
    YSIS, YSIRK = yb + 250, yb + 280
    PL([(bx, yb + 450), (bx, yb + 480), (bx + 200, yb + 480), (bx + 200, YSIS), (X0 + 3400 + 300 + 6 * 260 + 300 + 40, YSIS)], SIS, 2.0)
    hlab((bx + 200, YSIS), (bx + 600, YSIS), f"{inch(28 * YB_H)} {28 * YB_H:.0f} MB", 11, TCAP)
    PL([(X0 + 3400 + 300 + 6 * 260 + 300 + 70, YSIRK), (bx + 260, YSIRK), (bx + 260, yb + 380), (bx + 120, yb + 380)], SIRK, 1.5)
    INS("T-POMPA", (bx + 260, yb + 340), -90, 1.6, lay=CHZ); CEKV((bx + 260, yb + 305), -90, 'DN25', 1.2)
    lab((bx + 280, yb + 330), "SİRKÜLASYON POMPASI (zaman saatli, termostatlı)", 9, CHZ)
    lab((bx + 280, yb + 315), "Q=0,8 m³/h H=4 mSS", 9, CHZ)
    INS("T-GENLESME", (bx - 230, yb + 380), 0, 1.4, lay=CHZ); lab((bx - 260, yb + 420), "SIHHİ GENL. 50 L", 9, CHZ)
    lab((bx - 120, yb + 470), "TERMOSTATİK KARIŞIM VANASI 55 °C, LEJYONELLA: haftada 1 kez 70 °C", 9, CHZ)
    # --- kolonlar
    def kolon_grubu(xr, offs, sh):
        n = len(offs)
        yb_s = 2 * n * YB_S; yb_h = 2 * n * YB_H
        cols = {'SS': (xr, YSS, SS), 'SIS': (xr + 30, YSIS, SIS), 'SIRK': (xr + 60, YSIRK, SIRK)}
        for key, (x, y0, lay) in cols.items():
            PL([(x, y0), (x, y2 + 60)], lay, 2.0 if key != 'SIRK' else 1.5)
        vlab((xr, yz), (xr, y1), f"{inch(yb_s)} {yb_s:.0f} MB", 10)
        vlab((xr + 30, yz), (xr + 30, y1), f"{inch(yb_h)} {yb_h:.0f} MB", 10, TCAP)
        vlab((xr + 60, yz), (xr + 60, y1), sirk_cap(2 * n), 10, TCAP)
        lab((xr - 20, y2 + 80), f"Ş{sh[1]}: SS / SıS / SİRK", 12, SFT)
        VANA((xr, yb + 260 + 0), 90, 'DN50', 1.2); VANA((xr + 30, yb + 300), 90, 'DN50', 1.2)
        for kat, yf in ((2, y1), (3, y2)):
            yr = yf + 60
            xe = xr + 200 + n * 260
            PL([(xr, yr), (xe, yr)], SS); PL([(xr + 30, yr + 25), (xe, yr + 25)], SIS); PL([(xr + 60, yr + 50), (xe, yr + 50)], SIRK)
            hlab((xr, yr), (xr + 200, yr), f"{inch(n * YB_S)} {n * YB_S:.1f} MB", 9)
            for i, k in enumerate(offs):
                xo = xr + 260 + i * 260
                box(xo - 70, yr + 90, xo + 70, yr + 210, SAY)
                lab((xo - 68, yr + 215), f"SD-{kat - 1}{k}", 10, SAY)
                PL([(xo - 40, yr), (xo - 40, yr + 130)], SS); SAYAC((xo - 40, yr + 130), 90, 'DN20', 1.2)
                PL([(xo + 10, yr + 25), (xo + 10, yr + 130)], SIS); SAYAC((xo + 10, yr + 130), 90, 'DN20', 1.2)
                PL([(xo + 50, yr + 50), (xo + 50, yr + 110)], SIRK)
                VANA((xo + 50, yr + 85), 90, 'DN15', 0.8)
                PL([(xo - 40, yr + 145), (xo - 40, yr + 280)], SS); PL([(xo + 10, yr + 145), (xo + 10, yr + 280)], SIS)
                lab((xo - 70, yr + 290), f"{YB_S} MB 1\" / {YB_H:.0f} MB 3/4\"", 8, TCAP)
                lab((xo - 70, yr + 275), "OFİS", 8, TY)
            lab((xe - 40, yr + 54), "SİRK. DOLAPTA (SAYAÇ ÖNCESİ) BİTER, TERMOSTATİK DENGE VANALI", 8, TCAP, TA.BOTTOM_RIGHT)
    xS1 = k0 + 3200
    offs1 = [k for k in OFIS_S1 if SAFT_OF[k] == 'S1']
    offs2 = [k for k in OFIS_S1 if SAFT_OF[k] == 'S2']
    kolon_grubu(xS1, offs1, 'S1')
    xS2 = xS1 + 300 + len(offs1) * 260 + 300
    kolon_grubu(xS2, offs2, 'S2')
    # dükkânlar
    xd = xS2 + 300 + len(offs2) * 260 + 300
    for i, nm in enumerate(DUKKAN_S):
        x = xd + i * 260
        PL([(x, YSS), (x, yz + 150)], SS)
        SAYAC((x, yz + 150), 90, 'DN20', 1.2)
        box(x - 70, yz + 90, x + 70, yz + 210, SAY)
        PL([(x, yz + 165), (x, yz + 300)], SS); VANA((x, yz + 260), 90, 'DN20', 1.0)
        lab((x - 68, yz + 215), f"SD-Z{nm[-1]}", 10, SAY)
        lab((x - 68, yz + 310), f"{nm} 3/4\" BEKLEME", 8, TCAP)


# =================================================================== PİS SU ŞEMASI (S sırası alt yarı)
def pis_sema(X0=258900.0, YT=-444150.0):
    yb, yz, y1, y2, yc = YT - 3200, YT - 2600, YT - 2000, YT - 1400, YT - 800
    band(X0 - 100, 276500, [yb, yz, y1, y2, yc], ["BODRUM KAT -3,50", "ZEMİN KAT ±0,00", "1. KAT +3,50", "2. KAT +6,50", "ÇATI +9,50"],
         "PİS SU KOLON ŞEMASI (TS EN 12056-2)", YT - 200)
    n = len(PIS_KOL)
    dx = (275500 - X0 - 400) / n
    from alt import OUTA
    K = {k['no']: k for k in OUTA['bodrum']['drops']}
    lane = {}
    for j, pk in enumerate(PIS_KOL):
        x = X0 + 400 + j * dx
        no = f"P{j + 1}"
        sb = float((pk['sb'] or ('21 SB' if pk['cap'] == 'Ø100' else '4 SB')).split()[0])
        PL([(x, yz + 50), (x, yc + 120)], PS, 2.0 if pk['cap'] == 'Ø100' else 1.0)
        INS("T-YER-SUZGECI", (x, yc + 150), 0, 1.2, lay=PS)
        lab((x + 8, yc + 130), "HAVALIK", 8, PSC)
        for kat, yf in ((2, y1), (3, y2)):
            PL([(x, yf + 80), (x + dx * 0.55, yf + 140)], PS)
            lab((x + 6, yf + 145), f"{pk['cap']} {sb:.0f} SB", 8, PSC)
        vlab((x, yz + 60), (x, y1), f"{pk['cap']} {2 * sb:.0f} SB", 9, PSC)
        MTYB("MTY-TEMIZLEME KAPAGI KOLON", (x, yz + 120), 0, 1.0, PS, {'TK': 'T.K.'})
        C((x, yc + 60), 22, PSN); T(x, yc + 60, no, 12, PSN, TA.MIDDLE_CENTER)
        if K[no]['yol']:
            lab((x + 6, yz + 160), "zeminde tavanda ötelenir", 7, PSC)
        lx = K[no]['b'][0] - ROW['S'][0]
        rn = 'R1' if lx < 248700 else ('R2' if lx < 249250 else 'R3')
        lane.setdefault(rn, []).append((x, 2 * sb))
    # bodrum tavanı kollektörleri
    yk = {'R1': yb + 330, 'R2': yb + 260, 'R3': yb + 190}
    xr = {'R1': X0 + 200, 'R2': X0 + 1800, 'R3': X0 + 3400}
    for rn, L_ in lane.items():
        xs = [x for x, _ in L_]
        y = yk[rn]
        for x, _ in L_:
            PL([(x, yz + 50), (x, y)], PS)
        PL([(max(xs), y), (xr[rn], y), (xr[rn], yb + 40)], PS, 2.0)
        top = sum(s for _, s in L_)
        cap = 'Ø100' if top <= 160 else ('Ø125' if top <= 300 else 'Ø150')
        hlab((xr[rn], y), (min(xs), y), f"{cap} {top:.0f} SB %1 BODRUM TAVANINDA ASKILI", 10, PSC, 0.5)
        MTYB("PVC ROGAR", (xr[rn] - 36, yb - 40), 0, 1.4, ROG, {'R': rn})
    lab((X0 + 150, yb - 120), "R1 / R2 / R3 → PB (PARSEL BACASI) → ŞEHİR KANALI.  POMPA BASMA HATTI AYRI RÖGARA (R4) BAĞLANIR.", 11, PSC)


# =================================================================== ISITMA KOLON ŞEMASI (H sırası)
def isitma_sema(X0=289400.0, YT=-440500.0):
    yb, yz, y1, y2, yc = YT - 3200, YT - 2600, YT - 2000, YT - 1400, YT - 800
    band(X0 - 100, 314900, [yb, yz, y1, y2, yc], ["BODRUM KAT -3,50", "ZEMİN KAT ±0,00", "1. KAT +3,50", "2. KAT +6,50", "ÇATI +9,50"],
         "ISITMA TESİSATI KOLON ŞEMASI (OFİS YERDEN ISITMA 45/35 °C - DÜKKÂN RADYATÖR 70/50 °C)", YT - 200)
    k0 = X0 + 200
    box(k0 - 100, yb - 80, k0 + 1500, yb + 480, CHZ)
    lab((k0 - 80, yb + 490), "KAZAN DAİRESİ - AYRINTI: KAZAN DAİRESİ TESİSAT ŞEMASI", 12, CHZ)
    YG, YD = yb + 300, yb + 260
    PL([(k0, YG), (k0 + 1300, YG)], IG, 3.0); PL([(k0, YD), (k0 + 1300, YD)], ID, 3.0)
    lab((k0, YG + 10), "GİDİŞ KOLLEKTÖRÜ", 10, ICAP); lab((k0, YD - 22), "DÖNÜŞ KOLLEKTÖRÜ", 10, ICAP)
    Qo, Qd = R['Q_ofis'], R['Q_dukkan']
    dof = R['devre']['OFİS YERDEN ISITMA (45/35 °C, karışım vanalı)']
    ddk = R['devre']['DÜKKÂN RADYATÖR (70/50 °C)']
    # ofis devresi
    xo = k0 + 400
    n1 = sum(1 for k in OFIS_S1 if SAFT_OF[k] == 'S1')
    xend = k0 + 1900 + 30
    PL([(xo, YG), (xo, yb + 420), (xend, yb + 420)], IG, 2.0)
    PL([(xo + 40, YD), (xo + 40, yb + 390), (xend, yb + 390)], ID, 2.0)
    INS("T-POMPA", (xo, yb + 360), 90, 1.6, lay=CHZ)
    lab((xo + 15, yb + 340), f"P1 {dof['q']} m³/h {dof['H']} mSS", 9, CHZ)
    hlab((xo + 40, yb + 420), (xo + 900, yb + 420), f"{dof['dn']} {Qo} kW 45/35 °C (3 YOLLU KARIŞIM)", 11, ICAP)
    # dükkân devresi
    xd = k0 + 800
    PL([(xd, YG), (xd, yb + 180), (k0 + 1600, yb + 180)], IG, 2.0)
    PL([(xd + 40, YD), (xd + 40, yb + 140), (k0 + 1600, yb + 140)], ID, 2.0)
    INS("T-POMPA", (xd, yb + 220), -90, 1.6, lay=CHZ)
    lab((xd + 15, yb + 200), f"P2 {ddk['q']} m³/h {ddk['H']} mSS", 9, CHZ)
    import yi as _yi
    YD = {k: _yi.ofis_k(2, k, None) for k in OFIS_S1}
    ow = lambda k: 150 + len(YD[k]['circ']) * 42

    def grup(xr, offs, sh):
        n = len(offs)
        kw = sum(R['ofis'][(kat, k)]['Q'] for kat in (2, 3) for k in offs) / 1000.0
        PL([(xr, yb + 420), (xr, y2 + 60)], IG, 2.0); PL([(xr + 30, yb + 390), (xr + 30, y2 + 60)], ID, 2.0)
        vlab((xr, yz), (xr, y1), f"{dn_isitma(kw, 10)[0]} {kw:.1f} kW", 10, ICAP)
        lab((xr - 20, y2 + 80), f"Ş{sh[1]} ISITMA G/D", 12, SFT)
        xe = xr + 200 + sum(ow(k) for k in offs)
        for kat, yf in ((2, y1), (3, y2)):
            yr = yf + 40
            kwk = sum(R['ofis'][(kat, k)]['Q'] for k in offs) / 1000.0
            PL([(xr, yr), (xe, yr)], IG); PL([(xr + 30, yr + 20), (xe, yr + 20)], ID)
            hlab((xr, yr), (xr + 200, yr), f"{dn_isitma(kwk, 10)[0]} {kwk:.1f} kW", 9, ICAP)
            x = xr + 230
            for k in offs:
                Yk = _yi.ofis_k(kat, k, None)
                q = R['ofis'][(kat, k)]
                cs = sorted(Yk['circ'], key=lambda c: c['pidx'])
                nd = len(cs)
                # kalorimetre dolabı (gidiş: vana + pislik tutucu, dönüş: kalorimetre + vana)
                box(x - 45, yr + 50, x + 45, yr + 175, SAY)
                lab((x - 43, yr + 180), f"SD-{kat - 1}{k}", 8, SAY)
                PL([(x - 20, yr), (x - 20, yr + 250)], IG); PL([(x + 20, yr + 20), (x + 20, yr + 230)], ID)
                VANA((x - 20, yr + 70), 90, 'DN20', 0.7); PISLIK((x - 20, yr + 115), 90, 'DN20', 0.7)
                INS("T-KALORIMETRE", (x + 20, yr + 110), 90, 1.2, lay=KAL); lab((x + 30, yr + 100), f"KM-{kat - 1}{k}", 6, KAL)
                VANA((x + 20, yr + 150), 90, 'DN20', 0.7)
                # kollektör (gidiş üstte, dönüş altta) + devreler
                k0x = x + 60; k1x = x + 60 + nd * 42
                PL([(x - 20, yr + 250), (k1x, yr + 250)], IG, 2.5); PL([(x + 20, yr + 230), (k1x, yr + 230)], ID, 2.5)
                lab((k0x, yr + 205), f"KL-{kat - 1}{k} {nd} AĞIZ {q['Q']} W DN25", 6.5, KLT)
                for jj, c in enumerate(cs):
                    px = k0x + 15 + jj * 42
                    PL([(px, yr + 250), (px, yr + 470), (px + 14, yr + 470), (px + 14, yr + 230)], PEX)
                    T(px + 7, yr + 476, f"P{jj + 1}", 6, KLT, TA.BOTTOM_CENTER)
                    zn = (' ' + c['user']['zon']) if c.get('user') and c['user'].get('zon') else ''
                    T(px - 4, yr + 262, f"{kat - 1}{k}.{c['pidx'] + 1}{zn} {c['room']['name'][:8]} {c.get('W', 0):.0f}W {c['L']:.1f}m", 5.5, PEX, TA.BOTTOM_LEFT, 90)
                    T(px + 23, yr + 262, f"PEX 16x2,0 a={c['s']:.0f} {c.get('W', 0):.0f}W-DN15", 5.0, ICAP, TA.BOTTOM_LEFT, 90)
                x += ow(k)
    offs1 = [k for k in OFIS_S1 if SAFT_OF[k] == 'S1']
    offs2 = [k for k in OFIS_S1 if SAFT_OF[k] == 'S2']
    x1 = k0 + 1900
    grup(x1, offs1, 'S1')
    x2 = x1 + 300 + 230 + sum(ow(k) for k in offs1) + 300
    grup(x2, offs2, 'S2')
    # dükkânlar
    xs = x2 + 300 + 230 + sum(ow(k) for k in offs2) + 300
    PL([(k0 + 1600, yb + 180), (xs + 5 * 300, yb + 180)], IG, 2.0); PL([(k0 + 1600, yb + 140), (xs + 5 * 300, yb + 140)], ID, 2.0)
    hlab((k0 + 1600, yb + 180), (xs, yb + 180), f"{ddk['dn']} {Qd} kW 70/50 °C BODRUM TAVANINDAN", 11, ICAP, 0.8)
    for i, nm in enumerate(DUKKAN_S):
        x = xs + i * 300
        q = R['dukkan'][nm]; rd = q['rad']
        PL([(x, yb + 180), (x, yz + 120)], IG); PL([(x + 30, yb + 140), (x + 30, yz + 120)], ID)
        box(x - 50, yz + 60, x + 80, yz + 150, SAY); lab((x - 48, yz + 155), f"SD-Z{nm[-1]}", 10, SAY)
        INS("T-KALORIMETRE", (x + 30, yz + 100), 90, 1.4, lay=KAL)
        PL([(x, yz + 150), (x, yz + 220), (x + 230, yz + 220)], IG); PL([(x + 30, yz + 150), (x + 30, yz + 200), (x + 230, yz + 200)], ID)
        for r in range(rd['adet']):
            INS("T-RAD-SEMA", (x + 70 + r * 45, yz + 230), 0, 1.0, lay=RAD); lab((x + 60 + r * 45, yz + 300), f"R{r + 1}", 6, RAD)
        lab((x - 48, yz + 280), f"{nm}", 9, TY)
        lab((x - 48, yz + 265), f"{rd['adet']}x{rd['tip']}/{int(rd['boy'] * 100)} {q['Q']} W", 8, RAD)


# =================================================================== KAZAN DAİRESİ ŞEMASI (H sırası alt yarı)
def kazan_sema(X0=289400.0, YT=-444150.0):
    T(X0 - 100, YT - 200, "KAZAN DAİRESİ TESİSAT ŞEMASI", 40, TSEMA, TA.BOTTOM_LEFT)
    y0 = YT - 2600
    n = R['kazan']['adet']
    # kazanlar
    import kes, ekipman as EQP
    u = R['kazan']['birim']
    kk = 'DKAZAN48' if u <= 48 else ('DKAZAN65' if u <= 65 else 'DKAZAN100')
    for i in range(n):
        x = X0 + 300 + i * 450
        kes.ciz(EQP.duvar_kazan, (x, y0 - 140 * 4.5), 4.5, CHZ, False, 'O', (0, 0), kk, 1)
        lab((x - 100, y0 - 40), f"K-0{i + 1} {u} kW YOĞUŞMALI", 11, CHZ)
        PL([(x - 60, y0 + 400), (x - 60, y0 + 900)], IG, 2.0)
        PL([(x + 60, y0 + 400), (x + 60, y0 + 820)], ID, 2.0)
        INS("T-POMPA", (x - 60, y0 + 480), 90, 1.6, lay=CHZ); lab((x - 140, y0 + 470), f"KP-0{i + 1}", 9, CHZ)
        CEKV((x - 60, y0 + 540), 90, 'DN32', 1.2); VANA((x - 60, y0 + 600), 90, 'DN32', 1.2); VANA((x + 60, y0 + 600), 90, 'DN32', 1.2)
        PL([(x - 60, y0 + 400), (x - 60, y0 + 380)], IG)
        PL([(x, y0 + 400), (x, y0 + 1500)], BACA, 1.5)
    xe = X0 + 300 + (n - 1) * 450
    PL([(X0 + 240, y0 + 900), (xe + 500, y0 + 900)], IG, 3.0)
    PL([(X0 + 360, y0 + 820), (xe + 500, y0 + 820)], ID, 3.0)
    PL([(X0 + 300, y0 + 1500), (xe + 100, y0 + 1500), (xe + 100, y0 + 1800)], BACA, 2.0)
    lab((xe + 120, y0 + 1700), f"ORTAK BACA Ø{R['baca']['Dsec']} PP → Ş1 BACA ŞAFTI → ÇATI +1,00", 11, BACA)
    lab((X0 + 240, y0 + 1520), "KASKAD BACA KOLLEKTÖRÜ (klapeli)", 9, BACA)
    # denge kabı
    xdk = xe + 650
    kes.ciz(EQP.denge_kabi, (xdk, y0 + 680), 2.4, CHZ, False, 'O', (0, 0), 'DENGE65')
    lab((xdk + 50, y0 + 1060), "DK-01 DENGE KABI DN65", 10, CHZ)
    PL([(xe + 500, y0 + 900), (xdk - 40, y0 + 900)], IG, 3.0); PL([(xe + 500, y0 + 820), (xdk - 40, y0 + 820)], ID, 3.0)
    # kollektörler
    xk0, xk1 = xdk + 200, xdk + 2200
    PL([(xdk + 40, y0 + 1000), (xk0, y0 + 1000), (xk1, y0 + 1000)], IG, 4.0)
    PL([(xdk + 40, y0 + 760), (xk0, y0 + 760), (xk1, y0 + 760)], ID, 4.0)
    lab((xk0, y0 + 1010), "GİDİŞ KOLLEKTÖRÜ DN80", 11, ICAP); lab((xk0, y0 + 735), "DÖNÜŞ KOLLEKTÖRÜ DN80", 11, ICAP)
    for j, (t, x) in enumerate((("M-01 MANOMETRE", xk0 + 50), ("TM-01 TERMOMETRE", xk0 + 150))):
        PL([(x, y0 + 1000), (x, y0 + 1020)], IG)
        kes.ciz(EQP.MANO if j == 0 else EQP.TERMO, (x, y0 + 1030), 1.6, CHZ, False, (0, 0)); lab((x - 20, y0 + 1055), t, 7, CHZ)
    devs = [("P1 OFİS YERDEN ISITMA", R['devre']['OFİS YERDEN ISITMA (45/35 °C, karışım vanalı)'], True),
            ("P2 DÜKKÂN RADYATÖR", R['devre']['DÜKKÂN RADYATÖR (70/50 °C)'], False),
            ("P3 BOYLER SERPANTİNİ", R['devre']['BOYLER SERPANTİNİ (75/55 °C)'], False)]
    for i, (ad, d, mix) in enumerate(devs):
        x = xk0 + 400 + i * 550
        PL([(x, y0 + 1000), (x, y0 + 1700)], IG, 2.5); PL([(x + 80, y0 + 760), (x + 80, y0 + 1700)], ID, 2.5)
        INS("T-POMPA", (x, y0 + 1300), 90, 1.8, lay=CHZ); lab((x + 30, y0 + 1290), f"P-0{i + 1}", 10, CHZ)
        CEKV((x, y0 + 1380), 90, d['dn'], 1.2); VANA((x, y0 + 1450), 90, d['dn'], 1.2); VANA((x + 80, y0 + 1450), 90, d['dn'], 1.2)
        PISLIK((x + 80, y0 + 1150), 90, d['dn'], 1.2)
        if mix:
            PL([(x + 80, y0 + 1200), (x, y0 + 1200)], ID)
            UCYOL((x, y0 + 1200), 90, 1.6, no=False)
            lab((x + 20, y0 + 1220), "3YV-01 3 YOLLU KARIŞIM VANASI (dış hava kompanzasyonlu)", 8, CHZ)
        lab((x - 20, y0 + 1720), ad, 11, CHZ)
        lab((x - 20, y0 + 1740), f"{d['kw']} kW  {d['dn']}  Q={d['q']} m³/h  H={d['H']} mSS", 9, ICAP)
    # genleşme + emniyet + dolum
    xg = xk1 + 300
    PL([(xk1, y0 + 760), (xg, y0 + 760), (xg, y0 + 600)], ID)
    INS("T-GENLESME", (xg, y0 + 560), 0, 2.4, lay=CHZ)
    lab((xg + 50, y0 + 560), f"GT-01 KAPALI GENLEŞME TANKI {R['genlesme']['Vsec']} L (Po={R['genlesme']['Po']} bar)", 10, CHZ)
    lab((xg + 50, y0 + 540), "EMNİYET VENTİLİ 3 bar (her kazanda)", 9, CHZ)
    lab((xg + 50, y0 + 520), "OTOMATİK DOLUM + GERİ AKIŞ ÖNLEYİCİ (yumuşak su)", 9, CHZ)
    # gaz
    lab((X0 + 200, y0 - 120), f"DOĞALGAZ: {R['gaz']['Q']} m³/h (ayrı doğalgaz projesi). Kazan dairesi alt menfez {R['kd_hava']['alt']} cm², üst menfez {R['kd_hava']['ust']} cm².", 11, CHZ)
    lab((X0 + 200, y0 - 145), "Kazan kontrol: kaskad yönetim paneli + dış hava sensörü; ofis devresi 45/35 °C dış hava kompanzasyonlu karışım; boyler öncelikli değil.", 11, CHZ)


# =================================================================== LEJANT + NOTLAR + TABLOLAR
def lejant(x, y, kind):
    T(x, y, {'S': "SIHHİ TESİSAT LEJANTI", 'H': "ISITMA TESİSATI LEJANTI", 'V': "HAVALANDIRMA LEJANTI"}[kind], 18, TTAB, TA.TOP_LEFT)
    yy = y - 50
    rows = []
    if kind == 'S':
        rows = [('L', SS, "SOĞUK SU BORUSU (PPRC PN20)"), ('L', SIS, "SICAK SU BORUSU (PPRC-AL PN20)"), ('L', SIRK, "SİRKÜLASYON BORUSU"),
                ('L', PS, "PİS SU BORUSU (PVC, %1 eğim)"), ('B', "T-KOLON-T", "TEMİZ SU KOLONU"), ('B', "T-KOLON-P", "PİS SU KOLONU"),
                ('M', "MTY-SU SAYACI", "SU SAYACI"), ('M', "MTY-KURESEL VANA", "KÜRESEL VANA"), ('M', "MTY-CEKVALF VANA", "ÇEK VALF"),
                ('M', "MTY-PISLIK TUTUCU", "PİSLİK TUTUCU"), ('B', "T-DOLAP", "SAYAÇ DOLABI (SD)"), ('B', "T-YER-SUZGECI", "YER SÜZGECİ"),
                ('B', "T-POMPA", "POMPA")]
    elif kind == 'H':
        rows = [('L', IG, "ISITMA GİDİŞ BORUSU (siyah çelik / PPRC-AL)"), ('L', ID, "ISITMA DÖNÜŞ BORUSU"), ('L', PEX, "PEX 16x2,0 YERDEN ISITMA"),
                ('B', "T-KALORIMETRE", "KALORİMETRE (ısı pay ölçer)"), ('B', "T-KOLLEKTOR", "YERDEN ISITMA KOLLEKTÖRÜ"), ('B', "T-DOLAP", "SAYAÇ DOLABI (SD)"),
                ('B', "T-KAZAN", "YOĞUŞMALI KAZAN"), ('B', "T-POMPA", "SİRKÜLASYON POMPASI"), ('B', "T-GENLESME", "GENLEŞME TANKI"),
                ('M', "MTY-KURESEL VANA", "KÜRESEL VANA"), ('M', "MTY-CEKVALF VANA", "ÇEK VALF"), ('L', RAD, "PANEL RADYATÖR"), ('L', BACA, "BACA")]
    else:
        rows = [('L', EGZ, "EGZOZ / DUMAN TAHLİYE KANALI"), ('L', UFL, "TAZE HAVA KANALI"), ('B', "T-MENFEZ", "MENFEZ (600x300)"),
                ('B', "T-FAN", "FAN"), ('B', "T-DAMPER", "YANGIN DAMPERİ"), ('B', "T-GAZKAPAK", "GAZ SIZDIRMAZ BASINÇ KAPAĞI"),
                ('L', SFT, "ŞAFT / BACA (betonarmede boşluk)")]
    for t, a, s in rows:
        if t == 'L': PL([(x + 10, yy), (x + 110, yy)], a, 2.0)
        elif t == 'B': INS(a, (x + 60, yy), 0, 1.4 if a not in ("T-FAN", "T-KAZAN") else 0.6, lay=TTAB)
        else: MTYB(a, (x + 60, yy), 0, 1.6, TTAB, {'CAP': ''})
        T(x + 150, yy, s, 11, TTAB, TA.MIDDLE_LEFT)
        yy -= 42
    return yy


NOT_S = [
    "TEMİZ SU TESİSATI TS EN 806 VE TS 1258'E GÖRE, BORULAR PPRC PN20 (SICAK SU PPRC-AL) OLARAK YAPILACAKTIR.",
    "BİNA GİRİŞİNDE TEK ANA SAYAÇ, HER BAĞIMSIZ BÖLÜM GİRİŞİNDEKİ SAYAÇ DOLABINDA SOĞUK SU VE SICAK SU SAYACI BULUNACAKTIR.",
    "SICAK SU MERKEZİ BOYLERDEN 3 BORULU (SOĞUK - SICAK - SİRKÜLASYON) SİSTEMLE DAĞITILACAKTIR.",
    "SİRKÜLASYON HATTI HER KAT DAĞITIM HATTININ SONUNDA TERMOSTATİK SİRKÜLASYON VANASI (TSV) İLE SICAK SU HATTINA BAĞLANACAKTIR.",
    "SICAK SU 55 °C'DE DAĞITILACAK, LEJYONELLA İÇİN HAFTADA BİR KEZ 70 °C TERMAL DEZENFEKSİYON YAPILACAKTIR.",
    "KULLANIM SUYU DEPOLARI İLE YANGIN SUYU DEPOSU BİRLEŞTİRİLMEYECEKTİR.",
    "KOLONLAR Ş1 VE Ş2 TESİSAT ŞAFTLARINDA, ANA HATLAR ORTAK ALAN ASMA TAVANINDAN GEÇECEK; OFİSLERE KAPI DIŞINDAKİ DUVARDAN GİRİLECEKTİR.",
    "PİS SU KOLONLARI ZEMİN KATTA DÜKKÂN ASMA TAVANINDA EN YAKIN DUVARA ÖTELENECEKTİR.",
    "BİNA BİTİŞİK NİZAM VE BODRUM TÜM PARSELİ KAPLADIĞINDAN KOLON DİPLERİ BODRUM TAVANINDA ASKILI HATLARLA ÖN CEPHE RÖGARLARINA ALINACAKTIR.",
    "PİS SU YATAY HATLARI EN AZ %1 EĞİMLE DÖŞENECEK, KOLON DİPLERİNDE VE YÖN DEĞİŞTİRMELERDE TEMİZLEME KAPAĞI KONULACAKTIR.",
    "SIĞINAK, YANGIN DEPOSU VE KAZAN DAİRESİ TAVANINDAN PİS SU BORUSU GEÇİRİLMEYECEKTİR.",
    "OTOPARK YER SÜZGEÇLERİ PİS SU ÇUKURUNA, DALGIÇ POMPA BASMA HATTI AYRI RÖGARA (R4) BAĞLANACAKTIR.",
    "DÜKKÂNLARDA MİMARİDE ISLAK HACİM OLMADIĞINDAN SAYAÇLI VANALI SOĞUK SU BEKLEME UCU BIRAKILMIŞTIR.",
]
NOT_H = [
    "ISITMA MERKEZİ SİSTEM OLUP KAZAN DAİRESİ SIĞINAK İÇİNDE EI120 BÖLME İLE AYRILMIŞ HACİMDE TESİS EDİLECEKTİR.",
    "OFİSLER YERDEN ISITMA (45/35 °C), DÜKKÂNLAR PANEL RADYATÖR (70/50 °C) İLE ISITILACAKTIR.",
    "HER BAĞIMSIZ BÖLÜM GİRİŞİNDEKİ SAYAÇ DOLABINDA ULTRASONİK KALORİMETRE (M-BUS) VE KÜRESEL VANALAR BULUNACAKTIR.",
    "YERDEN ISITMA DEVRELERİ KULLANICININ MTY PROJESİNDEKİ GİBİ OLUP DEVRE AYAKLARI KAPILARDAN GEÇİRİLEREK KOLLEKTÖRE BAĞLANACAKTIR.",
    "KOLLEKTÖRLER DEBİMETRELİ, TERMOSTATİK AKTÜATÖRLÜ, HAVA ATICILI VE BOŞALTMALI OLACAKTIR; DEVRE BOYU 80 M'Yİ GEÇMEYECEKTİR.",
    "ISI KAYBI HESABI TS EN 12831 (TS 825 2. BÖLGE, Td=-3 °C) ESASLI YAPILMIŞTIR.",
    "KAZAN BACASI Ş1 BACA ŞAFTINDA ÇATI ÜZERİNE 1,00 M ÇIKARILACAK; BACA HESABI TS EN 13384'E GÖRE ÜRETİCİYE TEYİT ETTİRİLECEKTİR.",
    "ORTAK ALAN BORULARI 19 MM ELASTOMERİK KAUÇUK İLE YALITILACAKTIR.",
    "DOĞALGAZ TESİSATI AYRI PROJE KONUSUDUR; KAZAN DAİRESİ HAVALANDIRMASI GAZ DAĞITIM ŞİRKETİ ŞARTNAMESİNE UYGUN YAPILACAKTIR.",
]


def notlar(x, y, baslik, N, h=10.0, w=None):
    T(x, y, baslik, 18, TNOT, TA.TOP_LEFT)
    for k, n in enumerate(N):
        T(x, y - 45 - k * h * 2.0, f"{k + 1}. {n}", h, TNOT, TA.TOP_LEFT)
    return y - 45 - len(N) * h * 2.0


def tablo(x, y, baslik, head, rows, cw, h=9.0):
    T(x, y, baslik, 16, TTAB, TA.TOP_LEFT)
    y -= 35
    rh = h * 2.2
    W_ = sum(cw)
    def row(vals, yy, bold=False):
        xx = x
        for v, w in zip(vals, cw):
            T(xx + 4, yy - rh / 2, str(v), h, TTAB, TA.MIDDLE_LEFT)
            xx += w
    PL([(x, y), (x + W_, y)], TTAB)
    row(head, y); y -= rh; PL([(x, y), (x + W_, y)], TTAB)
    for r in rows:
        row(r, y); y -= rh
    PL([(x, y), (x + W_, y)], TTAB)
    xx = x
    for w in [0] + cw:
        xx += w; PL([(xx, y), (xx, y + rh * (len(rows) + 1))], TTAB)
    PL([(x, y), (x, y + rh * (len(rows) + 1))], TTAB)
    return y - 30


def ozet_tablolar(x, y):
    rows = []
    for (kat, k), o in sorted(R['ofis'].items()):
        rows.append((o['ad'], f"{o['A']}", f"{o['Q']}", f"{o['wm2']}", "YERDEN ISITMA", o['yi']))
    for nm, d in R['dukkan'].items():
        rows.append((d['ad'], f"{d['A']}", f"{d['Q']}", f"{d['wm2']}", f"{d['rad']['adet']}x{d['rad']['tip']}/{int(d['rad']['boy'] * 100)}", 'UYGUN'))
    y = tablo(x, y, "ISI KAYBI ÖZETİ (OFİS: TS 2164 MAHAL BAZLI - DÜKKÂN: TS EN 12831)", ("BAĞIMSIZ BÖLÜM", "ALAN m²", "Q (W)", "W/m²", "ISITICI", "KONTROL"), rows,
              [520, 160, 160, 140, 380, 160])
    k = R['kazan']; b = R['boyler']; g = R['genlesme']; bc = R['baca']
    rows2 = [("Ofis toplam ısı kaybı", f"{R['Q_ofis']} kW"), ("Dükkân toplam ısı kaybı", f"{R['Q_dukkan']} kW"),
             ("Boyler serpantin gücü", f"{b['P_serp']} kW"), ("Kazan hesap gücü (1,10 x ısıtma + 0,5 x boyler)", f"{R['Q_kazan_hesap']} kW"),
             ("Seçilen kazan", f"{k['adet']} x {k['birim']} kW = {k['top']} kW yoğuşmalı kaskad"),
             ("Boyler (Σ cihaz x φ=0,20 x 0,80)", f"{b['Qh']} l/h → {b['V']} l → {b['Vsec']} L çift serpantinli"),
             ("Genleşme tankı (Vs={0} l)".format(g['Vs']), f"Vn={g['Vn']} l → {g['Vsec']} L"),
             ("Baca (F=0,012·Q/√h)", f"F={bc['F']} cm² → Ø{bc['Dsec']}"), ("Doğalgaz tüketimi", f"{R['gaz']['Q']} m³/h"),
             ("Hidrofor", f"Q={R['hidrofor']['Q']} m³/h, H={R['hidrofor']['Halt']}/{R['hidrofor']['Hust']} mSS, {R['hidrofor']['Vn']} L tank"),
             ("Kullanım suyu deposu", f"{R['depo']['kisi']} kişi x {R['depo']['l']} l + 5 dük. → {R['depo']['Vsec']} m³ (1 ad.)")]
    y = tablo(x, y, "KAZAN / BOYLER / HİDROFOR ÖZETİ", ("KALEM", "DEĞER"), rows2, [700, 820])
    return y


def hava_tablo(x, y):
    o = R['otopark']; s = R['siginak']
    rows = [("Otopark net alanı", f"{o['A']} m²"), ("Otopark yüksekliği / hacmi", f"{o['h']} m / {o['V']} m³"),
            ("Normal egzoz (4 hava değişimi)", f"{o['Qn']} m³/h"), ("Duman tahliyesi (10 hava değişimi)", f"{o['Qd']} m³/h"),
            ("Taze hava (egzozun %85'i)", f"{o['Qt']} / {o['Qtd']} m³/h"),
            ("Sığınak alanı (ölçülen)", f"{s['A']} m²  ({s['kisi']} kişi, 1 m²/kişi)"), ("Sığınak hacmi", f"{s['V']} m³"),
            ("Sığınak normal havalandırma (4 hava değ.)", f"{s['Q_normal']} m³/h"), ("Sığınak koruma havası (3 m³/h·kişi)", f"{s['Q_koruma']} m³/h"),
            ("Sığınak egzozu (+50 Pa için %80)", f"{s['Q_egzoz']} m³/h"),
            ("Sığınak duman egzozu (alan > 100 m² → 10 hava değ.)", f"{s['Q_duman']} m³/h" if s['duman'] else "GEREKMEZ")]
    return tablo(x, y, "HAVALANDIRMA HESAP ÖZETİ", ("KALEM", "DEĞER"), rows, [900, 600])


def hava_sema(x, y):
    """otopark ve sığınak havalandırma şeması (akış)"""
    o = R['otopark']; s = R['siginak']
    T(x, y, "OTOPARK HAVALANDIRMA / DUMAN TAHLİYE ŞEMASI", 30, TSEMA, TA.BOTTOM_LEFT)
    y0 = y - 900
    box(x + 1500, y0, x + 4500, y0 + 600, TSEMA, f"KAPALI OTOPARK\n{o['A']} m²  V={o['V']} m³", 18)
    # taze hava
    PL([(x + 100, y0 + 450), (x + 1500, y0 + 450)], UFL, 3.0)
    INS("T-FAN", (x + 700, y0 + 450), 0, 1.5, lay=HCH); lab((x + 600, y0 + 520), "SF-1/2 TAZE HAVA", 12, HCH)
    box(x, y0 + 380, x + 100, y0 + 520, SFT, "IZG.", 9); lab((x, y0 + 540), "ÖN CEPHE TAZE HAVA BACASI (+2,00)", 10, TNOT)
    lab((x + 900, y0 + 460), f"{o['Qt']}/{o['Qtd']} m³/h", 11, KCAP)
    # egzoz
    PL([(x + 4500, y0 + 150), (x + 6000, y0 + 150), (x + 6000, y0 + 700)], EGZ, 3.0)
    INS("T-FAN", (x + 5200, y0 + 150), 0, 1.5, lay=HCH); lab((x + 5050, y0 + 220), "EF-1/2 EGZOZ (F300)", 12, HCH)
    lab((x + 4600, y0 + 160), f"{o['Qn']}/{o['Qd']} m³/h", 11, KCAP)
    box(x + 5930, y0 + 700, x + 6070, y0 + 850, SFT, "PANJ.", 9); lab((x + 6100, y0 + 760), "ÖN CEPHE EGZOZ BACASI (+3,00)", 10, TNOT)
    lab((x + 1500, y0 - 60), "Normal: CO dedektörüne göre düşük/yüksek hız (4 hava değişimi). Yangın: yangın algılama sinyaliyle yüksek hız (10 hava değişimi).", 11, TNOT)
    # sığınak
    y1 = y0 - 1100
    T(x, y1 + 650, "SIĞINAK HAVALANDIRMA ŞEMASI", 30, TSEMA, TA.BOTTOM_LEFT)
    box(x + 2500, y1, x + 4500, y1 + 500, TSEMA, f"SIĞINAK {s['A']} m²\n{s['kisi']} KİŞİ  +50 Pa", 16)
    xs = [x + 100, x + 600, x + 1100, x + 1700, x + 2500]
    PL([(xs[0], y1 + 250), (xs[-1], y1 + 250)], UFL, 3.0)
    box(xs[0] - 80, y1 + 200, xs[0], y1 + 300, SFT, "IZG.", 8)
    INS("T-GAZKAPAK", (xs[1], y1 + 250), 0, 2.0, lay=HCH); lab((xs[1] - 100, y1 + 300), "BASINÇ KAPAĞI", 10, HCH)
    box(xs[2] - 100, y1 + 200, xs[2] + 100, y1 + 300, HCH, "KUM FİLTRESİ", 10)
    INS("T-FAN", (xs[3], y1 + 250), 0, 1.2, lay=HCH); lab((xs[3] - 150, y1 + 320), f"SV-1 {s['Q_normal']}/{s['Q_koruma']} m³/h EL+ELEKTRİK", 10, HCH)
    PL([(x + 4500, y1 + 250), (x + 6000, y1 + 250)], EGZ, 3.0)
    INS("T-DAMPER", (x + 4700, y1 + 250), 0, 1.5, lay=HCH); lab((x + 4600, y1 + 300), "AŞIRI BASINÇ VALFİ", 10, HCH)
    INS("T-FAN", (x + 5300, y1 + 250), 0, 1.2, lay=HCH); lab((x + 5150, y1 + 320), f"EF-S {s['Q_egzoz']}/{s['Q_duman']} m³/h F400", 10, HCH)
    INS("T-GAZKAPAK", (x + 5800, y1 + 250), 0, 2.0, lay=HCH)
    box(x + 6000, y1 + 200, x + 6080, y1 + 300, SFT, "IZG.", 8)
    lab((x + 100, y1 - 60), "Taze hava ve egzoz arka cephe (sığınak tarafı) hava bacalarından; betonarme perdede Ø300 boşluk bırakılacaktır.", 11, TNOT)
    return y1 - 200
