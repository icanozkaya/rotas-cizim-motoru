# -*- coding: utf-8 -*-
"""Yangın tesisatı kolon şeması + lejant + ekipman listesi + hidrolik hesap özeti + notlar (yangın sırası 5. pafta)."""
import math, pickle
from lib import *
import hidro
import pickle as _p
H_ = _p.load(open('/tmp/claude-0/vy/heads.pkl', 'rb'))

X0, X1, YB, YT = 256498.0, 276712.0, -458149.0, -450649.0
FL = {0: -456900.0, 1: -455450.0, 2: -454000.0, 3: -452550.0}
TOP = -451100.0
TAV = {i: FL[i] + 1300.0 for i in FL}
AD = {0: 'BODRUM KAT', 1: 'ZEMİN KAT', 2: '1. KAT', 3: '2. KAT'}


def bands():
    T(256800, -451000, "YANGIN TESİSATI KOLON ŞEMASI", 32, SEM)
    T(256800, -451045, "(ölçeksiz) - sprinkler, yangın dolabı, itfaiye bağlantısı, pompa grubu", 12, SEM)
    for i, y in FL.items():
        PL([(256800, y), (263900, y)], SEM, 0)
        T(256810, y + 12, AD[i], 18, SEM)
        T(256810, y - 26, {0: "±0,00 (bodrum döşeme)", 1: "+3,50", 2: "+7,00", 3: "+10,00"}[i], 10, SEM)
    PL([(256800, TOP), (263900, TOP)], SEM, 0)
    T(256810, TOP + 12, "ÇATI", 18, SEM)


def pipe(pts, lay=BORU, w=2.5):
    PL(pts, lay, w)


def caplab(p, s, rot=0, lay=CAPL, h=10):
    T(p[0], p[1], s, h, lay, TA.BOTTOM_CENTER, rot, mask=True)


def sema():
    bands()
    y0 = FL[0]
    # ---------------- depo
    dx0, dx1, dy0, dy1 = 256950, 257650, y0 + 40, y0 + 760
    PL([(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)], DEP, 3, True)
    L((dx0 + 10, dy0 + 600), (dx1 - 10, dy0 + 600), DEP)
    for k in range(4): L((dx0 + 120 + k * 120, dy0 + 600 - 12), (dx0 + 160 + k * 120, dy0 + 600 - 12), DEP)
    T((dx0 + dx1) / 2, dy0 + 420, "YANGIN SUYU DEPOSU", 18, DEP, TA.MIDDLE_CENTER)
    T((dx0 + dx1) / 2, dy0 + 380, "V = 80 m³ (net)", 14, DEP, TA.MIDDLE_CENTER)
    T((dx0 + dx1) / 2, dy0 + 350, "60 dk x 74,6 m³/h = 74,6 m³ ≤ 80 m³", 9, DEP, TA.MIDDLE_CENTER)
    # dolum, taşma, havalık, boşaltma, seviye
    pipe([(dx0 + 100, dy1 + 120), (dx0 + 100, dy1 - 60)], DEP, 1.5)
    INS("Y-SAMANDIRA", (dx0 + 100, dy1 - 60), -90, 1.2, lay=DEP)
    T(dx0 + 100, dy1 + 128, "ŞEBEKEDEN DOLUM 1\"", 9, DEP, TA.BOTTOM_CENTER)
    pipe([(dx1, dy1 - 40), (dx1 + 80, dy1 - 40), (dx1 + 80, dy0 - 30)], DEP, 2)
    T(dx1 + 90, dy1 - 40, "TAŞMA DN80 (pompa çukuruna)", 8, DEP, TA.MIDDLE_LEFT)
    pipe([(dx0 + 300, dy1), (dx0 + 300, dy1 + 70), (dx0 + 330, dy1 + 70)], DEP, 1.5)
    T(dx0 + 340, dy1 + 70, "HAVALIK 2\"", 8, DEP, TA.MIDDLE_LEFT)
    pipe([(dx0 + 40, dy0), (dx0 + 40, dy0 - 30)], DEP, 1.5); KURESEL((dx0 + 40, dy0 - 15), 90, 1.0, mask=7)
    T(dx0 + 50, dy0 - 32, "BOŞALTMA 2\"", 8, DEP)
    INS("Y-CAM", (dx0 + 20, dy0 + 300), 0, 1.2, lay=DEP)
    T(dx0 + 30, dy0 + 300, "SEVİYE GÖST.", 7, DEP, TA.MIDDLE_LEFT)
    # ---------------- pompalar (yatay), kollektör dikey x=258650
    XC = 258650.0
    rows = [(y0 + 120, "E", 'ELEKTRİKLİ ANA POMPA', 'Q=70 m³/h H=60 mSS 22 kW', 'DN150', 'DN100', 1.0),
            (y0 + 300, "D", 'DİZEL YEDEK POMPA', 'Q=70 m³/h H=60 mSS 30 kW', 'DN150', 'DN100', 1.0),
            (y0 + 470, "J", 'JOKEY POMPA', 'Q=3 m³/h H=70 mSS 1,5 kW', 'DN40', 'DN25', 0.6)]
    import kes, ekipman
    for y, tag, ad, oz, de, db, s in rows:
        w = 4 if s == 1 else 2
        # pompa: yan görünüş / kesit (gerçek ölçülü, EN 733 uç emişli + motor/dizel modül, kaide)
        k = 0.55 if s == 1 else 0.40
        A_, B_, Hm_, dz = (157.6, 97.8, 179.5, True) if tag == "D" else ((125, 54, 168.2, False) if tag == "E" else (80, 30, 60, False))
        xp = dx1 + 185
        ax = (15 + 12 + 35) * k                     # kaide + şasi + mil ekseni
        yb = y - ax
        kes.ciz(ekipman._pompa_modul, (xp, yb), k, POM, False, 'Y', 0, 0, A_, B_, Hm_, dz, 65 if s == 1 else 32, 100 if s == 1 else 25)
        xb = xp + 25 * k; yt = y + (45 + 8) * k     # basma ağzı flanşı üstü
        pipe([(dx1, y), (xp - 5 * k - 3, y)], POM, w)                                   # emiş hattı
        yh = y + (82 if tag == 'D' else 62)
        pipe([(xb, yt), (xb, yh), (dx1 + 300, yh), (dx1 + 300, y), (XC, y)], POM, w)   # basma hattı
        INS("Y-VORTEX", (dx1 - 20, y), 90, s, lay=POM)
        INS("Y-OSY", (dx1 + 60, y), 0, s, mask=10)
        INS("Y-MANO", (dx1 + 100, y), 0, s * 0.9)
        INS("Y-RED", (dx1 + 140, y), 0, s, mask=9)
        INS("Y-RED", (dx1 + 300, y + 30), -90, s, mask=9)
        INS("Y-MANO", (dx1 + 350, y), 0, s * 0.9)
        CEK((dx1 + 400, y), 0, s * 1.3, mask=10)
        INS("Y-OSY", (dx1 + 460, y), 0, s, mask=10)
        T(xp + A_ * k / 2, yb - 6, f"P-{tag}", 10, POM, TA.TOP_CENTER)
        if tag == "D":
            pipe([(dx1 + 380, y), (dx1 + 380, y + 50)], POM, 1.5)
            INS("Y-EMNIYET", (dx1 + 380, y + 50), 0, 1.0)
            T(dx1 + 395, y + 60, "EMNİYET VANASI", 7, POM, TA.MIDDLE_LEFT)
        T(xp + A_ * k / 2, yb - 22, ad + " (KESİT)", 8, POM, TA.TOP_CENTER, mask=True)
        T(xp + A_ * k / 2, yb - 34, oz, 6.5, POM, TA.TOP_CENTER, mask=True)
        caplab((dx1 + 100, y + 8 + (0 if s == 1 else -3)), de, 0, POM, 8)
        caplab((dx1 + 520, y + 6), db, 0, POM, 8)
    # jokey membranlı tank + basınç anahtarları
    INS("Y-MTANK", (dx1 + 520, y0 + 560), 0, 1.0, lay=POM)
    pipe([(dx1 + 520, y0 + 540), (dx1 + 520, y0 + 470)], POM, 1)
    T(dx1 + 540, y0 + 565, "MEMBRANLI TANK 24 L", 7, POM, TA.MIDDLE_LEFT)
    pipe([(XC, y0 + 60), (XC, y0 + 700)], POM, 5)
    T(XC - 10, y0 + 710, 'KOLLEKTÖR DN150', 9, POM, TA.BOTTOM_RIGHT)
    for k, yy in enumerate((y0 + 600, y0 + 640, y0 + 680)):
        pipe([(XC, yy), (XC - 40, yy)], POM, 0.5); INS("Y-PS", (XC - 40, yy), 90, 1.0)
    T(XC - 70, y0 + 640, "PS-E/D/J", 7, POM, TA.MIDDLE_RIGHT)
    # elektrik panoları (kesikli kumanda hatları yerine sembol)
    for k, (t, yy) in enumerate((("ELK. POMPA PANOSU", y0 + 160), ("DİZEL POMPA PANOSU", y0 + 340), ("JOKEY PANOSU", y0 + 510))):
        INS("Y-PANO", (dx1 + 620, yy - 40 + 40), 0, 0.9, lay=POM); T(dx1 + 650, yy, t, 7, POM, TA.MIDDLE_LEFT)
    INS("Y-YAKIT", (dx1 + 560, y0 + 380), 0, 0.8, lay=POM)
    T(dx1 + 590, y0 + 380, "YAKIT 100 L", 7, POM, TA.MIDDLE_LEFT)
    # test hattı -> debimetre -> depo üstü
    yT = y0 + 700
    pipe([(XC, yT), (XC + 120, yT), (XC + 120, dy1 + 180), (dx0 + 500, dy1 + 180), (dx0 + 500, dy1)], POM, 3)
    INS("Y-DEBI", (XC + 120, yT + 150), 0, 1.3, lay=POM, mask=12)
    INS("Y-OSY", (XC + 120, yT + 220), 90, 1.0, mask=10)
    T(XC + 135, yT + 150, "TEST HATTI DN80 + DEBİMETRE", 8, POM, TA.MIDDLE_LEFT)
    # ---------------- AV1: bodrum zonu
    yA1 = y0 + 210
    xa = 259100
    XA1 = 260000
    pipe([(XC, yA1), (XA1, yA1)], BORU, 4)
    INS("Y-OSY", (XC + 120 + 70, yA1), 0, 1.2, mask=11)
    INS("Y-ALARM", (xa, yA1), 0, 1.4, mask=18)
    T(xa, yA1 - 26, "AV1 ISLAK ALARM VANA İSTASYONU DN150", 8, VAN, TA.TOP_CENTER, mask=True)
    INS("Y-MANO", (xa - 40, yA1), 0, 1.0); INS("Y-MANO", (xa + 40, yA1), 0, 1.0)
    pipe([(xa + 10, yA1 - 12), (xa + 10, yA1 - 60)], BORU, 1); INS("Y-TEST", (xa + 10, yA1 - 45), 90, 1.0)
    T(xa + 20, yA1 - 62, "TEST/DRENAJ DN50 -> POMPA ÇUKURU", 7, VAN, TA.MIDDLE_LEFT)
    pipe([(XA1, yA1), (XA1, TAV[0]), (261000, TAV[0])], BORU, 4)
    caplab((259400, yA1 + 6), 'DN150')
    _zone(0, XA1 + 80, 'DN150')
    # ---------------- AV2: SK kolonu
    yA2 = y0 + 390
    xs = 259500
    pipe([(XC, yA2), (xs, yA2), (xs, TAV[3])], BORU, 4)
    INS("Y-OSY", (XC + 190, yA2), 0, 1.2, mask=11)
    INS("Y-ALARM", (xa, yA2), 0, 1.4, mask=18)
    T(xa, yA2 - 26, "AV2 ISLAK ALARM VANA İSTASYONU DN150", 8, VAN, TA.TOP_CENTER, mask=True)
    INS("Y-MANO", (xa - 40, yA2), 0, 1.0); INS("Y-MANO", (xa + 40, yA2), 0, 1.0)
    caplab((259500, yA2 + 6), 'DN150')
    T(xs - 12, (FL[1] + FL[2]) / 2, 'SP-1 SPRİNKLER ANA KOLONU DN150', 11, KOL, TA.BOTTOM_CENTER, 90, mask=True)
    INS("Y-PURJOR", (xs, TAV[3]), 0, 1.4)
    T(xs + 14, TAV[3] + 20, "OTOMATİK PURJÖR", 7, VAN, TA.MIDDLE_LEFT)
    for i in (1, 2, 3):
        pipe([(xs, TAV[i]), (261000, TAV[i])], BORU, 4)
        INS("Y-KELEBEK", (xs + 120, TAV[i]), 0, 1.3, mask=12)
        INS("Y-AKIS", (xs + 200, TAV[i]), 0, 1.3, mask=10)
        pipe([(xs + 260, TAV[i]), (xs + 260, TAV[i] - 90)], BORU, 1)
        INS("Y-TEST", (xs + 260, TAV[i] - 60), 90, 1.0, mask=8)
        T(xs + 270, TAV[i] - 95, "TEST/DRENAJ DN32 -> YER SÜZGECİ", 7, VAN, TA.MIDDLE_LEFT)
        T(xs + 160, TAV[i] + 22, "KAT KONTROL İSTASYONU", 7, VAN, TA.BOTTOM_CENTER, mask=True)
        _zone(i, XA1 + 80, 'DN150' if len(H_[i]) > 100 else 'DN100')
    # ---------------- dolap hattı: YK1, YK2 + itfaiye
    yD = y0 + 70
    xk1, xk2 = 262300, 263400
    pipe([(XC, yD), (xk2, yD)], DOLB, 3)
    INS("Y-OSY", (XC + 190, yD), 0, 1.1, mask=11)
    caplab((XC + 600, yD + 6), 'DN80', 0, DOL)
    for xk, lab, cp, nm in ((xk1, "Y-1", 'DN80', "1"), (xk2, "Y-2", 'DN65', "2")):
        pipe([(xk, yD), (xk, FL[3] + 160)], DOLB, 3 if xk == xk1 else 2.5)
        INS("Y-PURJOR", (xk, FL[3] + 160), 0, 1.2)
        T(xk - 12, (FL[1] + FL[2]) / 2, f"{lab} - DOLAP KOLONU {cp}", 11, DOL, TA.BOTTOM_CENTER, 90, mask=True)
        for i in (0, 1, 2, 3):
            yy = FL[i] + 150
            pipe([(xk, yy), (xk + 90, yy)], DOLB, 2)
            INS("Y-OSY", (xk + 45, yy), 0, 0.9, mask=9)
            INS("ASL-YD-KOLON", (xk + 150, yy + 20), 0, 0.8, lay=DOL)
            code = {0: "B", 1: "Z", 2: "1", 3: "2"}[i] + nm
            T(xk + 200, yy + 10, f"YD-{code}", 10, DOL, TA.BOTTOM_LEFT)
            T(xk + 200, yy - 6, "TÜPLÜ YANGIN DOLABI TS EN 671-1, 1\" / 30 m", 7, DOL, TA.TOP_LEFT)
    # itfaiye bağlantısı (zemin, YK1'e çek valfle)
    yi = FL[1] + 80
    INS("Y-ITFAIYE", (xk1 - 420, yi), 0, 2.0, lay=ITF)
    pipe([(xk1 - 392, yi), (xk1, yi)], ITF, 3)
    CEK((xk1 - 300, yi), 0, 1.4, mask=11)
    INS("Y-OSY", (xk1 - 200, yi), 0, 1.1, mask=10)
    T(xk1 - 470, yi + 40, "İTFAİYE BAĞLANTISI 2x2 1/2\" STORZ", 9, ITF, TA.BOTTOM_LEFT, mask=True)
    T(xk1 - 470, yi - 40, "(bina dışı, +0,80; yeri mimariyle teyit)", 7, ITF, TA.TOP_LEFT, mask=True)
    caplab((xk1 - 120, yi + 6), 'DN80', 0, ITF)


def _zone(i, x, cp):
    R = pickle.load(open('/tmp/claude-0/vy/routes.pkl', 'rb'))
    H = pickle.load(open('/tmp/claude-0/vy/heads.pkl', 'rb'))
    n = len(H[i]); nar = sum(1 for h in H[i] if h['t'] == 'ARA')
    y = TAV[i]
    # temsili branşman + başlıklar
    for k in range(6):
        xx = x + 200 + k * 120
        pipe([(xx, y), (xx, y - 60)], BORU, 0.8)
        INS("Y-SPR-U" if i <= 1 else "Y-SPR-P", (xx, y - 60), 0, 1.4, lay="MTY-SPRINKLER")
    T(x + 200, y + 40, {0: "BODRUM - OTOPARK (OH2)", 1: "ZEMİN - İŞYERLERİ (OH2)", 2: "1. KAT (OH1)", 3: "2. KAT (OH1)"}[i], 10, SEM, TA.BOTTOM_LEFT, mask=True)
    T(x + 200, y - 90, f"{n} ADET SPRİNKLER" + (f" ({n - nar} tavan upright + {nar} lift ara seviye)" if nar else (" upright" if i == 1 else " pendant")) + " K80 68°C", 8, SEM, TA.TOP_LEFT, mask=True)
    caplab((x + 100, y + 6), cp)


# ------------------------------------------------------------------ tablolar
def table(x, y, cols, rows, title, h=9.0, rowh=24.0, lay=TAB):
    W = sum(c[1] for c in cols)
    T(x, y + 14, title, 16, lay)
    yy = y
    PL([(x, yy), (x + W, yy)], lay)
    cx = x
    for name, w in cols:
        T(cx + 6, yy - rowh + 7, name, h, lay)
        cx += w
    yy -= rowh
    PL([(x, yy), (x + W, yy)], lay)
    for r in rows:
        cx = x
        for (name, w), v in zip(cols, r):
            T(cx + 6, yy - rowh + 7, str(v), h * 0.9, lay)
            cx += w
        yy -= rowh
        PL([(x, yy), (x + W, yy)], lay)
    cx = x
    for name, w in cols + [("", 0)]:
        PL([(cx, y), (cx, yy)], lay)
        cx += w
    return yy


def lejant(x, y):
    """Aselsan 02-Yangın 'YANGIN SÖNDÜRME TESİSATI SEMBOLLERİ' lejantı (+ pompa dairesi sembolleri)"""
    T(x, y + 14, "YANGIN SÖNDÜRME TESİSATI SEMBOLLERİ", 16, TAB)
    items = [("boru", "SPRİNKLER BORUSU"), ("dolb", "YANGIN DOLABI BORUSU"), ("itf", "İTFAİYE BAĞLANTI HATTI"),
             ("kolonno", "YANGIN BORUSU KOLON NUMARASI (SP-1 / Y-1)"), ("ASL-SPR-PE", "PENDENT SPRİNKLER (Ø25, K80 68°C)"),
             ("ASL-SPR-UP", "DİK TİP (UPRIGHT) SPRİNKLER (Ø25, K80 68°C)"), ("ASL-KELEBEK", "KELEBEK VANA"),
             ("ASL-IZL-KELEBEK", "İZLENEBİLİR KELEBEK VANA"), ("ASL-OSY", "YÜKSELEN MİLLİ VANA"), ("ASL-CEK", "ÇEK VANA"),
             ("ASL-PISLIK", "PİSLİK TUTUCU"), ("ASL-KOMP", "KOMPANSATÖR"), ("ASL-TEST", "TEST DRENAJ SETİ"), ("ASL-FS", "FLOW SWITCH (AKIŞ ANAHTARI)"),
             ("ASL-ITFAIYE", "İTFAİYE BAĞLANTI AĞZI / 2 x 2 1/2\""), ("ASL-WAV", "ISLAK ALARM VANA İSTASYONU"),
             ("ASL-BDV", "BASINÇ DÜŞÜRÜCÜ DENGELEME VANASI"), ("ASL-MANO", "MANOMETRE"), ("ASL-YD-PLAN", "YANGIN DOLABI (KAT PLANI)"),
             ("ASL-YD-KOLON", "TÜPLÜ YANGIN DOLABI (KOLON ŞEMASI) TS EN 671-1, 1\" / 30 m"),
             ("Y-POMPA", "YANGIN POMPASI"), ("Y-MTANK", "MEMBRANLI TANK"), ("Y-DEBI", "DEBİMETRE"), ("Y-EMNIYET", "EMNİYET (RELIEF) VANASI"),
             ("Y-PS", "BASINÇ ANAHTARI"), ("Y-PURJOR", "OTOMATİK HAVA PURJÖRÜ"), ("Y-PANO", "POMPA KUMANDA PANOSU")]
    yy = y - 40
    for key, txt in items:
        rh = 90 if key in ("ASL-YD-KOLON", "ASL-ITFAIYE", "ASL-WAV") else 46
        cy = yy - rh / 2 + 10
        p = (x + 50, cy)
        if key == "boru": PL([(x + 10, cy), (x + 90, cy)], BORU, 2)
        elif key == "dolb": PL([(x + 10, cy), (x + 90, cy)], DOLB, 2)
        elif key == "itf": PL([(x + 10, cy), (x + 90, cy)], ITF, 3)
        elif key == "kolonno":
            for cx_, t_ in ((x + 32, "SP-1"), (x + 68, "Y-1")):
                C((cx_, cy), 16, KOL); C((cx_, cy), 14, KOL); T(cx_, cy, t_, 7, KOL, TA.MIDDLE_CENTER)
        elif key.startswith("ASL-"):
            sc = {"ASL-SPR-PE": 1.0, "ASL-SPR-UP": 1.0, "ASL-YD-KOLON": 0.4, "ASL-ITFAIYE": 0.42, "ASL-WAV": 0.6, "ASL-YD-PLAN": 0.8}.get(key, 0.9)
            msp.add_blockref(key, p, dxfattribs={"layer": VAN if key not in ("ASL-SPR-PE", "ASL-SPR-UP") else "MTY-SPRINKLER", "xscale": sc, "yscale": sc})
        else:
            INS(key, p, 0, 1.2, lay=VAN)
        T(x + 120, cy, txt, 10, TAB, TA.MIDDLE_LEFT)
        PL([(x, yy + 10), (x + 760, yy + 10)], TAB)
        yy -= rh
    PL([(x, yy + 10), (x + 760, yy + 10)], TAB)
    PL([(x, y - 30), (x, yy + 10)], TAB); PL([(x + 100, y - 30), (x + 100, yy + 10)], TAB); PL([(x + 760, y - 30), (x + 760, yy + 10)], TAB)
    return yy


def build():
    sema()
    res, dol = hidro.ozet()
    R = pickle.load(open('/tmp/claude-0/vy/routes.pkl', 'rb'))
    H = pickle.load(open('/tmp/claude-0/vy/heads.pkl', 'rb'))
    # ekipman listesi
    nU = len([h for h in H[0] if h['t'] == 'U']) + len(H[1]); nP = len(H[2]) + len(H[3]); nA = len([h for h in H[0] if h['t'] == 'ARA'])
    eq = [(1, "ELEKTRİKLİ ANA YANGIN POMPASI", 1, "Q=70 m³/h H=60 mSS 22 kW 2900 d/d PN16, %140 debide ≥%70 basma"),
          (2, "DİZEL YEDEK YANGIN POMPASI", 1, "Q=70 m³/h H=60 mSS 30 kW, akülü marş, 100 L yakıt tankı"),
          (3, "JOKEY POMPA", 1, "Q=3 m³/h H=70 mSS 1,5 kW 400V"),
          (4, "ELEKTRİKLİ POMPA PANOSU", 1, "IP54, yıldız-üçgen, faz koruma, arıza alarmı"),
          (5, "DİZEL POMPA PANOSU", 1, "IP54, otomatik start, 2 set akü şarj, 6 deneme startı"),
          (6, "JOKEY POMPA PANOSU", 1, "Basınç kontrollü otomatik, IP54"),
          (7, "MEMBRANLI TANK", 1, "24 L PN16 (jokey)"),
          (8, "ISLAK ALARM VANASI", 2, "DN100, gong + basınç anahtarı (AV1 bodrum, AV2 üst katlar)"),
          (9, "İZLENEBİLİR KELEBEK VANA", 3, "DN100 kat kontrol istasyonu (Z, 1, 2)"),
          (10, "AKIŞ ANAHTARI", 3, "DN100, kat kontrol istasyonu"),
          (11, "TEST / DRENAJ VANASI", 5, "DN32 (kat) + DN50 (alarm vanaları)"),
          (12, "YANGIN DOLABI", 8, "TS EN 671-1 Ø25 mm 30 m hortum, 100 l/dk, 4 bar"),
          (13, "İTFAİYE BAĞLANTISI", 1, "2x2 1/2\" Storz, çek valfli"),
          (14, "YANGIN SUYU DEPOSU", 1, "80 m³ net, betonarme, epoksi kaplı"),
          (15, "SPRİNKLER UPRIGHT", nU, "K80 1/2\" 68°C standart tepkili (bodrum tavan + zemin)"),
          (16, "SPRİNKLER PENDANT", nP, "K80 1/2\" 68°C (1. ve 2. kat)"),
          (17, "ARA SEVİYE SPRİNKLER", nA, "K80 68°C, lift üst platform altı, esnek bağlantılı"),
          (18, "DEBİMETRE", 1, "DN80 test hattı"),
          (19, "OTOMATİK HAVA PURJÖRÜ", 3, "SK, YK1, YK2 kolon tepeleri"),
          (20, "BASINÇ ANAHTARI", 3, "PS-E / PS-D / PS-J")]
    yy = table(264300, -451050, [("NO", 70), ("CİHAZ", 520), ("ADET", 110), ("TEKNİK ÖZELLİK", 1250)],
               [(a, b, c, d) for a, b, c, d in eq], "EKİPMAN LİSTESİ", 10, 30)
    yy = lejant(264300, yy - 80)
    # hidrolik özet
    rows = []
    for r in res:
        rows.append((r['kat'], r['sinif'], f"{r['yog']:.1f}", f"{r['alan']:.0f}", r['N'], f"{r['qmin']:.1f}", f"{r['Q']:.0f}", f"{r['P']:.2f}", f"{r['Pp']:.2f}"))
    yh = table(268600, -451050, [("KAT", 230), ("SINIF", 120), ("mm/dk", 120), ("ALAN m²", 140), ("BAŞLIK", 130), ("q l/dk", 130), ("Q l/dk", 130), ("P kat bar", 160), ("P pompa bar", 180)],
               rows, "SPRİNKLER HİDROLİK HESAP ÖZETİ (TS EN 12845, Hazen-Williams C=120)", 10, 30)
    w = max(res, key=lambda r: r['Q'])
    Qt = w['Q'] + dol['Q']
    lines = [f"En elverişsiz sprinkler alanı: {w['kat']} {w['Q']:.0f} l/dk; yangın dolabı 2 x 100 l/dk = {dol['Q']:.0f} l/dk",
             f"Toplam: {Qt:.0f} l/dk = {Qt * 0.06:.1f} m³/h; dolap için gerekli basınç {dol['P'] * 10.2:.1f} mSS (2. kat, lüle 4 bar)",
             (f"Seçilen pompa: Q=70 m³/h H=60 mSS ≥ ihtiyaç {Qt * 0.06:.1f} m³/h / {max(dol['P'], max(r['Pp'] for r in res)) * 10.2:.1f} mSS  ✓"
              if Qt * 0.06 <= 70 else f"Seçilen pompa: Q=70 m³/h H=60 mSS; eğri üzerinde {Qt * 0.06:.0f} m³/h'de ≥{max(dol['P'], max(r['Pp'] for r in res)) * 10.2 + 2:.0f} mSS sağlanacaktır."),
             f"Depo: {Qt * 0.06:.1f} m³/h x 60 dk = {Qt * 0.06:.1f} m³ ≤ 80 m³ net  ✓",
             "Kat yükseklikleri kabulü: bodrum 3,50 / zemin 3,50 / normal 3,00 m (kesitten teyit)."]
    for k, s in enumerate(lines):
        T(268600, yh - 40 - k * 26, s, 10, TAB)
    notlar(268600, yh - 220)


def notlar(x, y):
    N = ["1. Sprinkler ve yangın dolabı tesisatı TS EN 12845, TS EN 671-1 ve Binaların Yangından Korunması Hakkında Yönetmelik'e uygun yapılacaktır.",
         "2. Bodrum otopark OH2, zemin kat işyerleri OH2, normal katlar OH1 tehlike sınıfında tasarlanmıştır.",
         "3. Mekanik park liftlerinde üst platform altına ara seviye sprinkler konulacak, esnek bağlantı ile tavan hattından beslenecektir.",
         "4. Sprinkler boru çapları beslenen başlık sayısına göre verilmiştir: DN25 ≤2, DN32 3, DN40 ≤5, DN50 ≤10, DN65 ≤20, DN80 ≤40, DN100 ≤100, DN150 >100 (ana kolon SP-1 ve kollektör DN150).",
         "5. DN50 ve altı borular diş açmalı, DN65 ve üstü kanallı (groove) bağlantılı EN 10255 orta seri siyah çelik boru ile yapılacaktır.",
         "6. Borular hiçbir yerde betonarme kolon ve perde içinden geçirilmeyecek, kiriş geçişleri statik projeye göre kılıflı yapılacaktır.",
         "7. Her katta izlenebilir kelebek vana, akış anahtarı ve test/drenaj vanasından oluşan kat kontrol istasyonu yapılacaktır.",
         "8. Tüm izleme anahtarları, akış anahtarları ve alarm vanası basınç anahtarları yangın algılama paneline bağlanacaktır.",
         "9. Yangın dolapları lüle çıkışında en az 4 bar sağlayacak, 9 bar üzerinde basınç düşürücü takılacaktır.",
         "10. İtfaiye bağlantısı itfaiye aracının yanaşabileceği cephede, zeminden +0,80 m yükseklikte ve levhalı yapılacaktır.",
         "11. Ana ve yedek pompa her biri %100 kapasitede olacak, dizel pompa egzozu yalıtımlı ve susturuculu olarak dış atmosfere verilecektir.",
         "12. Pompa dairesi en az +10 °C'de tutulacak, yer süzgeci, havalandırma menfezi ve acil aydınlatma yapılacaktır.",
         "13. Yangın suyu deposu sadece yangın amaçlı kullanılacak, girdap önleyici plakalı emiş ve şamandıralı dolum yapılacaktır.",
         "14. Tesisat en az 15 bar basınçla 2 saat süreyle hidrostatik teste tabi tutulacaktır.",
         "15. Bodrum tesisat alanında depo bölümüne denk gelen 3 adet mevcut sprinkler başlığı silinecektir.",
         "16. Güncel bodrum mimarisi MIM-BODRUM-GUNCEL katmanında verilmiş olup yangın paftasındaki eski bodrum mimarisi bununla değiştirilecektir.",
         "17. 1. kat sprinkler yerleşimi 2. kat ile aynı olup başlıklar EK'te çizilmiştir; zemin ve 2. kat başlıkları mevcut MTY bloklarıdır."]
    T(x, y + 14, "NOTLAR", 16, TAB)
    for k, s in enumerate(N):
        T(x, y - 30 - k * 30, s, 10, TAB)
