"""MEKANİK EKİPMAN BLOK KÜTÜPHANESİ — gerçek ölçü (cm), 1/50 paftaya uygun.
Her ekipman üç görünüşle çizilir:
  'P' plan (x: genişlik/boy, y: derinlik)
  'O' ön görünüş (x: genişlik, y: yükseklik; y=0 bitmiş döşeme/kaide üstü)
  'Y' yan görünüş / kesit (x: derinlik, y: yükseklik)
Ölçü kaynakları DATA sözlüğünde: V = üretici verisi, T = tahmini/tipik (projede üretici çizimiyle teyit).
"""
import math
from cad import L, PL, C, T, ARC, RECT, RRECT, SOL, ARROW, push, pop, MOVE

EQ = 'MEK-EKIPMAN'
GZ = 'MEK-EKIPMAN-GIZLI'
BA = 'MEK-BAKIM-ALANI'
KD = 'MEK-KAIDE'
OL = 'MEK-OLCU'
YZ = 'MEK-YAZI'
BG = 'MTY-ISITMA-GIDIS-BORU'
BD = 'MTY-ISITMA-DONUS-BORU'
YB = 'MEK-YANGIN-BORU'
SB = 'MTY-SOGUKSU-BORU'
DV = 'MEK-DUVAR'
TR = 'MEK-TARAMA'
LAYERS = {EQ: (4, 'CONTINUOUS'), GZ: (4, 'DASHED'), BA: (8, 'DASHDOT'), KD: (8, 'CONTINUOUS'),
          OL: (2, 'CONTINUOUS'), YZ: (7, 'CONTINUOUS'), YB: (1, 'CONTINUOUS'), DV: (7, 'CONTINUOUS'),
          TR: (8, 'CONTINUOUS'), BG: (10, 'CONTINUOUS'), BD: (30, 'ISITMA DONUS HATTI'), SB: (5, 'CONTINUOUS')}

# ------------------------------------------------------------------ veri (cm)
DATA = {
    'KOMBI24': dict(ad='DUVAR TİPİ YOĞUŞMALI KOMBİ 24 kW', W=42.5, D=31, H=74, baca='Ø60/100', kay='V: DemirDöküm nitromiX P24 (740x425x310 mm, 32 kg)'),
    'KOMBI35': dict(ad='DUVAR TİPİ YOĞUŞMALI KOMBİ 35 kW', W=42.5, D=34, H=74, baca='Ø60/100', kay='V: DemirDöküm nitromiX P35'),
    'DKAZAN48': dict(ad='DUVAR TİPİ YOĞUŞMALI KAZAN 48 kW', W=44, D=40.5, H=72, baca='Ø80/125', kay='V: Vaillant ecoTEC plus VU 486/5-5 (ön ≥50, yan ≥18, üst ≥27,5 cm)'),
    'DKAZAN65': dict(ad='DUVAR TİPİ YOĞUŞMALI KAZAN 65 kW', W=44, D=47.3, H=72, baca='Ø80/125', kay='V: Vaillant ecoTEC plus VU 656/5-5'),
    'DKAZAN100': dict(ad='DUVAR TİPİ YOĞUŞMALI KAZAN 100 kW', W=52, D=46, H=98, baca='Ø110/160', kay='V/T: Buderus GB162-100 / Vaillant VU 1206 (ölçü teyit)'),
    'YKAZAN285': dict(ad='YER TİPİ YOĞUŞMALI KAZAN 170–285 kW', L=179, W=91.6, H=145, baca='Ø200', brulor=0, kay='V: Viessmann Vitocrossal 200 CM2 (1790x916x1450, 388 kg); baca Ø T'),
    'YKAZAN130': dict(ad='YER TİPİ YOĞUŞMALI KAZAN 80–130 kW', L=176, W=81.5, H=135, baca='Ø150', brulor=0, kay='V: Vitocrossal 200 CM2 80–130 kW (1760x815x1350)'),
    'YKAZAN800': dict(ad='YER TİPİ YOĞUŞMALI KAZAN 800 kW', L=254.5, W=96, H=201.4, baca='Ø253', brulor=0, kay='V: Buderus SB745-800 (1540 kg, gidiş DN100)'),
    'CKAZAN235': dict(ad='ÇELİK SICAK SU KAZANI 235 kW (+BRÜLÖR)', L=176, W=80, H=93, baca='Ø250', brulor=55, kay='V: Baymak YAKUT tip 20 (A1760 B800 C930, DN80); brülör boyu T'),
    'CKAZAN465': dict(ad='ÇELİK SICAK SU KAZANI 465 kW (+BRÜLÖR)', L=207, W=102, H=110.5, baca='Ø300', brulor=65, kay='V: Baymak YAKUT tip 40 (DN100, 1087 kg); brülör T'),
    'BOYLER300': dict(ad='BOYLER 300 L (ÇİFT SERPANTİN)', D=74.4, H=173.4, kay='V: Viessmann Vitocell 100-V 300 L (devirme 182,5)'),
    'BOYLER500': dict(ad='BOYLER 500 L', D=92.3, H=194.8, kay='V: Vitocell 100-V 500 L (yalıtımlı)'),
    'BOYLER1000': dict(ad='BOYLER 1000 L', D=114.5, H=216.6, kay='V: Vitocell 100-V 1000 L (yalıtımlı, 367 kg)'),
    'AKUM2000': dict(ad='AKÜMÜLASYON (BUFFER) TANKI 2000 L', D=134, H=227, kay='V: Hargassner SP 2000 (Ø1340 yalıtımlı, devirme 2270)'),
    'GEN50': dict(ad='KAPALI GENLEŞME TANKI 50 L', D=44.1, H=48.7, kay='V: Reflex N 50 (R3/4)'),
    'GEN100': dict(ad='KAPALI GENLEŞME TANKI 100 L', D=51.2, H=66.9, kay='V: Reflex N 100 (R1)'),
    'GEN300': dict(ad='KAPALI GENLEŞME TANKI 300 L', D=63.4, H=106, kay='V: Reflex N 300 (1")'),
    'GEN500': dict(ad='KAPALI GENLEŞME TANKI 500 L', D=74, H=129, kay='V: Reflex N 500 (1")'),
    'GEN1000': dict(ad='KAPALI GENLEŞME TANKI 1000 L', D=74, H=241, kay='V: Reflex N 1000 (118 kg)'),
    'DENGE65': dict(ad='DENGE KABI (HİDROLİK AYIRICI) DN65', D=16, H=144, dn=65, kay='V: Reflex 160/80 (10 m³/h, 233 kW ΔT20)'),
    'DENGE100': dict(ad='DENGE KABI DN100', D=27.3, H=170, dn=100, kay='T: Caleffi 548 DN100 (56 m³/h) — ölçü teyit'),
    'POMPA50': dict(ad='SİRKÜLASYON POMPASI DN50 (ISLAK ROTOR)', Lf=28, H=38, W=22, kay='V: Wilo Stratos 50/1-12 yapı boyu 280; gövde/motor ölçüsü T'),
    'POMPA80': dict(ad='SİRKÜLASYON POMPASI DN80', Lf=36, H=46, W=26, kay='V: Wilo Stratos 80/1-12 yapı boyu 360; diğer T'),
    'ESANJOR': dict(ad='LEHİMLİ PLAKALI EŞANJÖR ~250 kW', W=19.3, D=19.1, H=61.6, kay='V/T: CB110-36M (ölçü yorumu teyit)'),
    'YANGIN_SET': dict(ad='YANGIN POMPA SETİ EN 12845 (ELEKTRİK+DİZEL) + JOKEY', kay='V: DAB 1 KDN 40-250/240 E+D: 1576(Amax 2170) x 2143(Bmax 2369) x 1795 mm, DN100, 1006 kg; modül eksen aralığı 800'),
    'JOKEY': dict(ad='JOKEY POMPA (DİKEY ÇOK KADEMELİ)', D=20, H=91.3, B=25, kay='V: Grundfos CR 10-9 (B1+B2 913 mm, 3 kW)'),
    'PANO': dict(ad='YANGIN POMPA KUMANDA PANOSU', W=80, D=40, H=200, kay='T: tipik 600–800 x 1800–2000 x 400–500'),
    'ALARM': dict(ad='ISLAK ALARM VANA İSTASYONU DN150', W=80, D=40, H=150, kay='V/T: Viking DN150 gövde; trim zarfı T'),
    'DOLAP': dict(ad='YANGIN DOLABI (TS EN 671-1)', W=80, D=25, H=70, kay='T: piyasa 800x700x250; makara ≤800, DN50 vana'),
    'HIDRANT': dict(ad='YER ÜSTÜ YANGIN HİDRANTI DN100', D=22, H=100, kay='V: İBB şartnamesi H1≥700, H3≥1000, 1900 l/dk 7 bar'),
    'GRP': dict(ad='GRP PANEL SU DEPOSU (1x1 m PANEL)', kay='V: dış = iç + ~15 cm; menhol 83x83; 1x1x2 → 115x115x255'),
    'HIDROFOR2': dict(ad='HİDROFOR 2 POMPALI (FREKANS KONV.)', W=84.7, D=60, H=120.3, kay='V: Wilo COR-2 MHIE 803 (R3", 102 kg)'),
    'MTANK300': dict(ad='MEMBRANLI BASINÇ TANKI 300 L', D=63, H=143, kay='V: Zilmet 300 LV 10 bar'),
    'MTANK500': dict(ad='MEMBRANLI BASINÇ TANKI 500 L', D=75, H=161, kay='V: Zilmet 500 LV 10 bar'),
    'PISSU_IST': dict(ad='PİS SU TERFİ İSTASYONU (TANKLI)', W=60, D=55, H=71, kay='V/T: Grundfos Multilift MOG 93 L; dış ölçü T, giriş DN100 kotu 18/25/31,5'),
    'VRF10': dict(ad='VRF DIŞ ÜNİTE 8–12 HP', W=93, D=76, H=169, kay='V: LG Multi V5 ARUM080-120 (930x1690x760)'),
    'VRF20': dict(ad='VRF DIŞ ÜNİTE 14–22 HP', W=124, D=76, H=169, kay='V: LG ARUM140-220 (1240x1690x760)'),
    'AHU14': dict(ad='KLİMA SANTRALİ (ROTORLU ISI GERİ KAZANIM) ~8.000 m³/h', L=226.4, W=148.2, H=148.2, kay='V: Systemair Geniox 14 (yaklaşık; kaide +10–15 cm)'),
    'KASET': dict(ad='4 YOLLU KASET FANCOIL', W=84, D=84, H=26, kay='T: panel 840x840, gövde 570x570x260'),
}

FLANGE = {65: (17, 4.6, 19), 80: (18, 4.9, 21), 100: (19, 5.4, 22.9), 125: (20, 5.6, 25), 150: (21, 5.7, 26.7), 200: (23, 6.2, 29.2)}
# DN: (OS&Y sürgülü boy, kelebek boy, çek valf boy) cm — EN 558 tipik (T)
FL_OD = {25: 11.5, 32: 14, 40: 15, 50: 16.5, 65: 18.5, 80: 20, 100: 22, 125: 25, 150: 28.5, 200: 34}


# ------------------------------------------------------------------ yardımcılar
def DIM(a, b, off, lay=OL, h=7.5, txt=None):
    """a-b arası ölçü çizgisi; off: kaydırma (sola/aşağı negatif)"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    Lg = math.hypot(dx, dy)
    if Lg < 1e-6:
        return
    ux, uy = dx / Lg, dy / Lg
    nx, ny = -uy, ux
    a2 = (a[0] + nx * off, a[1] + ny * off)
    b2 = (b[0] + nx * off, b[1] + ny * off)
    L(a, (a2[0] + nx * 3 * (1 if off > 0 else -1), a2[1] + ny * 3 * (1 if off > 0 else -1)), lay)
    L(b, (b2[0] + nx * 3 * (1 if off > 0 else -1), b2[1] + ny * 3 * (1 if off > 0 else -1)), lay)
    L(a2, b2, lay)
    for p in (a2, b2):
        L((p[0] - 2.5 * (ux - nx), p[1] - 2.5 * (uy - ny)), (p[0] + 2.5 * (ux - nx), p[1] + 2.5 * (uy - ny)), lay)
    ang = math.degrees(math.atan2(dy, dx))
    if ang > 90.1 or ang < -89.9:
        ang += 180
    m = ((a2[0] + b2[0]) / 2 + nx * 2, (a2[1] + b2[1]) / 2 + ny * 2)
    T(m, txt if txt else ('%g' % round(Lg, 1)).replace('.', ','), h, lay, 'BC', ang)


def KOT(p, txt, lay=OL, h=7.5):
    """kot işareti (üçgen + yazı)"""
    x, y = p
    PL([(x - 5, y + 7), (x + 5, y + 7), (x, y), (x - 5, y + 7)], lay)
    L((x - 5, y + 7), (x + 40, y + 7), lay)
    T((x + 7, y + 9), txt, h, lay, 'L')


def ETIKET(p, q, txt, lay=YZ, h=10):
    """ok + kırık çizgi + yazı"""
    L(p, q, lay)
    ARROW(p, math.degrees(math.atan2(p[1] - q[1], p[0] - q[0])), lay, 6)
    d = 1 if q[0] >= p[0] else -1
    L(q, (q[0] + d * 15, q[1]), lay)
    T((q[0] + d * 17, q[1] - 3.5), txt, h, lay, 'L' if d > 0 else 'R')


def HATCH(x0, y0, x1, y1, s=10, lay=TR):
    """45° tarama (beton/duvar kesiti)"""
    w, h = x1 - x0, y1 - y0
    k = -h
    while k < w:
        pts = []
        for t in (0, 1):
            pass
        ax, ay = x0 + max(k, 0), y0 + max(-k, 0)
        bx = x0 + min(k + h, w)
        by = y0 + (bx - x0 - k)
        if bx > ax:
            L((ax, ay), (bx, by), lay)
        k += s


def BAKIM(x0, y0, x1, y1, txt='BAKIM ALANI'):
    RECT(x0, y0, x1, y1, BA)
    T(((x0 + x1) / 2, y0 + 3), txt, 6, BA, 'BC')


def FLANS(c, dn, ang=0, lay=EQ):
    """flanş (kesitte iki dik çizgi)"""
    od = FL_OD.get(dn, dn / 10 * 1.8) / 2
    a = math.radians(ang)
    nx, ny = -math.sin(a), math.cos(a)
    ux, uy = math.cos(a), math.sin(a)
    for s in (-1.0, 1.0):
        p = (c[0] + ux * s, c[1] + uy * s)
        L((p[0] - nx * od, p[1] - ny * od), (p[0] + nx * od, p[1] + ny * od), lay)


def BORU2(a, b, dn, lay):
    """çift çizgi boru (gerçek dış çap)"""
    r = {15: 1.07, 20: 1.35, 25: 1.7, 32: 2.1, 40: 2.4, 50: 3.0, 65: 3.8, 80: 4.45, 100: 5.7, 125: 7.0, 150: 8.4, 200: 10.95, 250: 13.65}.get(dn, dn / 20)
    dx, dy = b[0] - a[0], b[1] - a[1]
    Lg = math.hypot(dx, dy) or 1
    nx, ny = -dy / Lg * r, dx / Lg * r
    L((a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), lay)
    L((a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny), lay)


# ------------------------------------------------------------------ armatürler (gerçek ölçü, ön görünüş, yatay boru)
def VANA_OSY(c, dn, ang=0, acik=True):
    l = FLANGE.get(dn, (20, 5, 22))[0]
    od = FL_OD.get(dn, 20) / 2
    push(MOVE(c[0], c[1])); push(_rot(ang))
    RECT(-l / 2, -od, -l / 2 + 2, od, EQ); RECT(l / 2 - 2, -od, l / 2, od, EQ)
    PL([(-l / 2 + 2, -od * 0.7), (0, 0), (-l / 2 + 2, od * 0.7)], EQ, True)
    PL([(l / 2 - 2, -od * 0.7), (0, 0), (l / 2 - 2, od * 0.7)], EQ, True)
    hs = od * 2.6 + (dn * 0.35 if acik else 0) / 2
    L((0, od * 0.7), (0, hs), EQ); RECT(-od * 0.8, hs, od * 0.8, hs + 2, EQ)
    L((-od * 0.9, hs + 1), (od * 0.9, hs + 1), EQ)
    pop(); pop()


def VANA_KELEBEK(c, dn, ang=0):
    l = FLANGE.get(dn, (20, 5, 22))[1]
    od = FL_OD.get(dn, 20) / 2
    push(MOVE(c[0], c[1])); push(_rot(ang))
    RECT(-l / 2, -od, l / 2, od, EQ); L((-l / 2, -od), (l / 2, od), EQ)
    L((0, od), (0, od + 12), EQ); RECT(-6, od + 12, 6, od + 14, EQ)
    pop(); pop()


def CEK_VALF(c, dn, ang=0):
    l = FLANGE.get(dn, (20, 5, 22))[2]
    od = FL_OD.get(dn, 20) / 2
    push(MOVE(c[0], c[1])); push(_rot(ang))
    RECT(-l / 2, -od, l / 2, od, EQ)
    PL([(-l / 2 + 3, -od * 0.6), (l / 2 - 3, 0), (-l / 2 + 3, od * 0.6)], EQ, True)
    L((l / 2 - 3, -od * 0.6), (l / 2 - 3, od * 0.6), EQ)
    pop(); pop()


def EKS_RED(c, dn1, dn2, ang=0, ust_duz=True):
    """eksantrik redüksiyon (düz taraf üstte) dn1 -> dn2"""
    l = 20.0
    r1, r2 = FL_OD.get(dn1, 20) / 2 * 0.8, FL_OD.get(dn2, 15) / 2 * 0.8
    push(MOVE(c[0], c[1])); push(_rot(ang))
    PL([(-l / 2, r1), (l / 2, r1), (l / 2, r1 - 2 * r2), (-l / 2, -r1)], EQ, True)
    pop(); pop()


def _rot(ang):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return (ca, -sa, 0, sa, ca, 0)


def MANO(c):
    L(c, (c[0], c[1] + 10), EQ); C((c[0], c[1] + 15), 5, EQ); L((c[0], c[1] + 15), (c[0] + 3, c[1] + 18), EQ)


def TERMO(c):
    L(c, (c[0], c[1] + 8), EQ); RECT(c[0] - 2, c[1] + 8, c[0] + 2, c[1] + 22, EQ); C((c[0], c[1] + 8), 2.5, EQ)


# ------------------------------------------------------------------ ısıtma ekipmanları
def kombi(view, o, key='KOMBI24'):
    d = DATA[key]; W, D, H = d['W'], d['D'], d['H']
    x, y = o
    if view == 'P':      # duvar y=o[1], cihaz +y yönünde
        RECT(x - W / 2, y, x + W / 2, y + D, EQ)
        C((x, y + D / 2), 5, GZ)                      # baca Ø100 (gizli)
        L((x - W / 2 + 4, y + D - 3), (x + W / 2 - 4, y + D - 3), EQ)
        BAKIM(x - W / 2 - 18, y + D, x + W / 2 + 18, y + D + 50, 'ÖN BAKIM 50')
    elif view == 'O':    # alt kenar döşemeden 130 cm (tipik montaj)
        y0 = y + 130
        RRECT(x - W / 2, y0, x + W / 2, y0 + H, 3, EQ)
        RECT(x - 8, y0 + 12, x + 8, y0 + 20, EQ)      # ekran
        for i, dx in enumerate((-15, -7.5, 0, 7.5, 15)):
            L((x + dx, y0), (x + dx, y0 - 12), EQ)
            L((x + dx - 1.2, y0 - 12), (x + dx + 1.2, y0 - 12), EQ)
        RECT(x - 5, y0 + H, x + 5, y0 + H + 15, EQ)   # baca adaptörü Ø100
        T((x, y0 - 22), 'KG  SG  GAZ  SC  KD', 4.5, YZ, 'TC')
        BAKIM(x - W / 2 - 18, y0 - 30, x + W / 2 + 18, y0 + H + 27.5, 'SERVİS ZARFI')
    else:                # yan: duvar x=o[0]
        y0 = y + 130
        RECT(x, y0, x + D, y0 + H, EQ)
        PL([(x + D / 2 - 5, y0 + H), (x + D / 2 - 5, y0 + H + 10), (x - 25, y0 + H + 10 + 25 * 0.05)], EQ)
        PL([(x + D / 2 + 5, y0 + H), (x + D / 2 + 5, y0 + H + 20), (x - 25, y0 + H + 20 + 25 * 0.05)], EQ)
        T((x - 27, y0 + H + 14), 'BACA ' + d['baca'] + ' (%3 DIŞA EĞİM)', 5, YZ, 'R')


def duvar_kazan(view, o, key='DKAZAN65', n=1, ara=5):
    """duvar tipi yoğuşmalı kazan, n adet kaskad (aralık ara cm)"""
    d = DATA[key]; W, D, H = d['W'], d['D'], d['H']
    x, y = o
    tot = n * W + (n - 1) * ara
    for i in range(n):
        xi = x - tot / 2 + i * (W + ara) + W / 2
        if view == 'P':
            RECT(xi - W / 2, y, xi + W / 2, y + D, EQ); C((xi, y + D / 2), 6.25, GZ)
        elif view == 'O':
            y0 = y + 140
            RRECT(xi - W / 2, y0, xi + W / 2, y0 + H, 3, EQ); RECT(xi - 9, y0 + 10, xi + 9, y0 + 18, EQ)
            for dx in (-12, -4, 4, 12):
                L((xi + dx, y0), (xi + dx, y0 - 20), EQ)
            RECT(xi - 6.25, y0 + H, xi + 6.25, y0 + H + 20, EQ)
        else:
            if i == 0:
                y0 = y + 140
                RECT(x, y0, x + D, y0 + H, EQ)
                RECT(x + D / 2 - 6.25, y0 + H, x + D / 2 + 6.25, y0 + H + 20, EQ)
    if view == 'P':
        BAKIM(x - tot / 2 - 18, y + D, x + tot / 2 + 18, y + D + 50, 'ÖN BAKIM ≥50')
    if view == 'O' and n > 1:
        y0 = y + 140
        RECT(x - tot / 2, y0 + H + 20, x + tot / 2 + 30, y0 + H + 33, EQ)   # ortak baca kollektörü Ø130
        T((x, y0 + H + 36), 'ORTAK KASKAD BACASI Ø130 (%3 EĞİM)', 5, YZ, 'BC')
        RECT(x - tot / 2, y0 - 55, x + tot / 2, y0 - 35, EQ)                 # kaskad hidrolik kollektör
        T((x, y0 - 62), 'KASKAD KOLLEKTÖRÜ + DENGE KABI', 5, YZ, 'TC')


def yer_kazan(view, o, key='YKAZAN285', kaide=10):
    """yer tipi kazan; P: x boyunca kazan boyu (ön = o[0] tarafı), y genişlik merkezli"""
    d = DATA[key]; Lk, W, H, br = d['L'], d['W'], d['H'], d.get('brulor', 0)
    x, y = o
    if view == 'P':
        RECT(x - 10, y - W / 2 - 10, x + Lk + 10, y + W / 2 + 10, KD)          # kaide
        RECT(x, y - W / 2, x + Lk, y + W / 2, EQ)
        L((x + 8, y - W / 2), (x + 8, y + W / 2), EQ)                           # ön kapak
        if br:
            RECT(x - br, y - 15, x, y + 15, EQ); C((x - br / 2, y), 12, EQ)
        C((x + Lk - 25, y), float(d['baca'][1:]) / 20, EQ)                       # baca çıkışı
        for s in (-1, 1):
            C((x + Lk - 50, y + s * W / 4), 4, EQ)                              # gidiş/dönüş
        BAKIM(x - br - 100, y - W / 2 - 60, x - br, y + W / 2 + 60, 'ÖN: KAZAN BOYU+100')
        BAKIM(x + Lk, y - W / 2, x + Lk + 70, y + W / 2, 'ARKA ≥70')
    elif view == 'Y':     # yan görünüş (x boyunca)
        RECT(x - 10, y, x + Lk + 10, y + kaide, KD); HATCH(x - 10, y, x + Lk + 10, y + kaide, 8)
        y0 = y + kaide
        RECT(x, y0 + 5, x + Lk, y0 + H, EQ)
        for xx in (x + 10, x + Lk - 20):
            RECT(xx, y0, xx + 10, y0 + 5, EQ)
        RECT(x - 2, y0 + 15, x + 8, y0 + H - 15, EQ)                           # ön kapak
        if br:
            RECT(x - br, y0 + H * 0.45, x - 2, y0 + H * 0.45 + 30, EQ); RECT(x - br * 0.6, y0 + H * 0.45 - 15, x - br * 0.3, y0 + H * 0.45, EQ)
        bd = float(d['baca'][1:]) / 10
        RECT(x + Lk - 25 - bd / 2, y0 + H, x + Lk - 25 + bd / 2, y0 + H + 25, EQ)
        for k, xx in enumerate((x + Lk - 60, x + Lk - 45)):
            RECT(xx - 3, y0 + H, xx + 3, y0 + H + 15, EQ)
        RECT(x + Lk * 0.3, y0 + H, x + Lk * 0.55, y0 + H + 18, EQ)              # kumanda paneli
        T((x + Lk / 2, y0 + H / 2), d['ad'].split(' (')[0], 6, YZ, 'MC')
    else:                 # ön görünüş (W x H)
        RECT(x - W / 2 - 10, y, x + W / 2 + 10, y + kaide, KD); HATCH(x - W / 2 - 10, y, x + W / 2 + 10, y + kaide, 8)
        y0 = y + kaide
        RECT(x - W / 2, y0 + 5, x + W / 2, y0 + H, EQ)
        RECT(x - W / 2 + 8, y0 + 15, x + W / 2 - 8, y0 + H - 15, EQ)
        if br:
            C((x, y0 + H * 0.45 + 15), 15, EQ)
        RECT(x - W * 0.3, y0 + H, x + W * 0.3, y0 + H + 18, EQ)


def boyler(view, o, key='BOYLER500', serp=2):
    d = DATA[key]; Dm, H = d['D'], d['H']
    x, y = o
    r = Dm / 2
    if view == 'P':
        C((x, y), r, EQ); C((x, y), r - 5, GZ)
        for a in (0, 180):
            L((x + r * math.cos(math.radians(a)), y), (x + (r + 10) * math.cos(math.radians(a)), y), EQ)
        BAKIM(x - r - 50, y - r, x - r, y + r, 'BAKIM 50')
    else:
        for xx in (x - r * 0.6, x + r * 0.6):
            L((xx, y), (xx, y + 10), EQ)
        RRECT(x - r, y + 10, x + r, y + H, r * 0.25, EQ)
        RRECT(x - r + 5, y + 15, x + r - 5, y + H - 5, r * 0.22, GZ)       # iç gövde (yalıtım)
        # serpantinler (kesit)
        zs = [(y + H * 0.12, y + H * 0.35)] + ([(y + H * 0.45, y + H * 0.65)] if serp == 2 else [])
        for (a, b) in zs:
            n = 6; pts = []
            for i in range(n + 1):
                yy = a + (b - a) * i / n
                pts.append((x - r * 0.55 if i % 2 == 0 else x + r * 0.55, yy))
            PL(pts, GZ)
            for yy in (a, b):
                L((x + r, yy), (x + r + 12, yy), EQ)
        for yy, t in ((y + 18, 'SG'), (y + H - 12, 'SÇ'), (y + H * 0.75, 'SİRK')):
            L((x - r, yy), (x - r - 12, yy), EQ); T((x - r - 14, yy), t, 5, YZ, 'MR')
        L((x, y + H), (x, y + H + 8), EQ)                                   # anot / hava
        T((x, y + H / 2 + 20), 'V=' + key.replace('BOYLER', '').replace('AKUM', '') + ' L', 7, YZ, 'MC')


def genlesme(view, o, key='GEN300'):
    d = DATA[key]; Dm, H = d['D'], d['H']
    x, y = o; r = Dm / 2
    if view == 'P':
        C((x, y), r, EQ)
    else:
        for xx in (x - r * 0.6, x + r * 0.6):
            L((xx, y), (xx, y + 8), EQ)
        RRECT(x - r, y + 8, x + r, y + H, r * 0.35, EQ)
        ARC((x, y + 8 + H * 0.45), r * 0.95, 200, 340, GZ)                  # membran
        L((x, y + 8), (x, y - 5), EQ); L((x, y - 5), (x + r + 15, y - 5), EQ)
        VANA_KILITLI = (x + r + 8, y - 5)
        C(VANA_KILITLI, 2, EQ)
        L((x, y + H), (x, y + H + 5), EQ)                                    # azot ventili


def denge_kabi(view, o, key='DENGE65'):
    d = DATA[key]; Dm, H, dn = d['D'], d['H'], d['dn']
    x, y = o; r = Dm / 2
    if view == 'P':
        C((x, y), r, EQ)
        for s in (-1, 1):
            L((x + s * r, y), (x + s * (r + 20), y), EQ)
    else:
        RECT(x - r, y, x + r, y + H, EQ)
        for yy, s, t in ((y + H * 0.75, -1, 'KAZAN GİDİŞ'), (y + H * 0.25, -1, 'KAZAN DÖNÜŞ'), (y + H * 0.75, 1, 'TESİSAT GİDİŞ'), (y + H * 0.25, 1, 'TESİSAT DÖNÜŞ')):
            L((x + s * r, yy), (x + s * (r + 20), yy), BG if 'GİDİŞ' in t else BD)
            FLANS((x + s * (r + 20), yy), dn, 0)
        L((x, y + H), (x, y + H + 8), EQ); C((x, y + H + 10), 2, EQ)         # purjör
        L((x, y), (x, y - 10), EQ)                                            # boşaltma/çamur


def pompa_inline(view, o, key='POMPA50', ang=0, dn=50):
    d = DATA[key]; Lf, H, W = d['Lf'], d['H'], d['W']
    x, y = o
    push(MOVE(x, y)); push(_rot(ang))
    if view == 'P':
        RECT(-Lf / 2, -W / 2 * 0.6, Lf / 2, W / 2 * 0.6, EQ)
        C((0, 0), W / 2, EQ); RECT(-W / 2 * 0.7, -W / 2 * 0.7, W / 2 * 0.7, W / 2 * 0.7, GZ)
    else:
        RECT(-Lf / 2, -FL_OD.get(dn, 16) / 2, -Lf / 2 + 2, FL_OD.get(dn, 16) / 2, EQ)
        RECT(Lf / 2 - 2, -FL_OD.get(dn, 16) / 2, Lf / 2, FL_OD.get(dn, 16) / 2, EQ)
        PL([(-Lf / 2 + 2, -6), (-6, -9), (6, -9), (Lf / 2 - 2, -6), (Lf / 2 - 2, 6), (6, 9), (-6, 9), (-Lf / 2 + 2, 6)], EQ, True)
        RECT(-W / 2 * 0.6, 9, W / 2 * 0.6, H - 10, EQ)                     # motor
        RECT(-W / 2, H - 10, W / 2, H, EQ)                                   # elektronik modül
        ARROW((Lf / 2 + 8, 0), 0, YZ, 6)
    pop(); pop()


def kollektor(view, o, n=3, dn=80, ara=40, pdn=50, uzun=None):
    """ısıtma gidiş/dönüş kollektörü (ön görünüş): üst gidiş, alt dönüş, n çıkış"""
    x, y = o
    Lk = uzun or (n + 1) * ara
    rr = {50: 3.0, 65: 3.8, 80: 4.45, 100: 5.7, 125: 7.0, 150: 8.4}.get(dn, 5)
    rr = rr * 1.6   # kollektör borusu bir üst çap görünümü
    for yy, lay, t in ((y + 60, BG, 'GİDİŞ KOLLEKTÖRÜ'), (y, BD, 'DÖNÜŞ KOLLEKTÖRÜ')):
        if view == 'O':
            RECT(x, yy - rr, x + Lk, yy + rr, EQ)
            PL([(x, yy - rr), (x - 5, yy - rr * 0.6), (x - 5, yy + rr * 0.6), (x, yy + rr)], EQ)
            T((x + Lk + 6, yy), t, 6, YZ, 'ML')
            for i in range(n):
                xi = x + ara * (i + 1)
                L((xi, yy + (rr if yy > y else -rr)), (xi, yy + (40 if yy > y else -40)), lay)
                if yy > y:
                    VANA_KELEBEK((xi, yy + 25), pdn, 90)
                else:
                    VANA_KELEBEK((xi, yy - 25), pdn, 90)
            TERMO((x + 8, yy + rr)); MANO((x + Lk - 8, yy + rr))
        elif view == 'P' and yy == y:
            RECT(x, y - rr, x + Lk, y + rr, EQ)
            RECT(x, y + 25 - rr, x + Lk, y + 25 + rr, EQ)
    if view == 'O':
        for xx in (x + 10, x + Lk - 10):
            L((xx, y - rr), (xx, y - 50), EQ); L((xx, y + 60 - rr), (xx, y - 50), GZ)
            RECT(xx - 6, y - 52, xx + 6, y - 50, EQ)                        # konsol ayağı


def esanjor(view, o, key='ESANJOR'):
    d = DATA[key]; W, D, H = d['W'], d['D'], d['H']
    x, y = o
    if view == 'P':
        RECT(x - W / 2, y - D / 2, x + W / 2, y + D / 2, EQ)
        for i in range(1, 6):
            L((x - W / 2 + W * i / 6, y - D / 2), (x - W / 2 + W * i / 6, y + D / 2), GZ)
    else:
        RECT(x - W / 2, y, x + W / 2, y + H, EQ)
        for yy in (y + 6, y + H - 6):
            for dx in (-W / 4, W / 4):
                C((x + dx, yy), 2.5, EQ)


def yerden_kollektor(view, o, n=8):
    """yerden ısıtma kollektörü (50 mm çıkış aralığı) + sıva altı dolap"""
    x, y = o
    Lk = 5 * (n - 1) + 9.8
    dW = 40 if n <= 3 else (50 if n <= 5 else (70 if n <= 8 else (85 if n <= 10 else 100)))
    if view == 'O':
        RECT(x - dW / 2, y + 30, x + dW / 2, y + 30 + 75, EQ)   # dolap (alt kenar döşeme+30)
        RECT(x - Lk / 2, y + 85, x + Lk / 2, y + 89, EQ); RECT(x - Lk / 2, y + 60, x + Lk / 2, y + 64, EQ)
        for i in range(n):
            xi = x - Lk / 2 + 4.9 + 5 * i
            L((xi, y + 85), (xi, y + 30), BG); L((xi + 1.5, y + 60), (xi + 1.5, y + 30), BD)
            C((xi, y + 92), 1.5, EQ)
        T((x, y + 112), 'YERDEN ISITMA KOLLEKTÖRÜ %d AĞIZ (dolap %d cm)' % (n, dW), 5, YZ, 'BC')
    else:
        RECT(x - dW / 2, y, x + dW / 2, y + 11, EQ)


# ------------------------------------------------------------------ yangın ekipmanları
def _pompa_modul(view, x, y, A, B, H, dizel=False, dn_e=65, dn_b=100, kaide=15):
    """EN 733 uç emişli pompa + motor/dizel modül. P: x boyunca A (emiş tarafı x), y boyunca B"""
    if view == 'P':
        RECT(x - 10, y - B / 2 - 10, x + A + 10, y + B / 2 + 10, KD)
        RECT(x, y - B / 2, x + A, y + B / 2, EQ)                             # şasi
        C((x + 25, y), 22, EQ)                                                # salyangoz
        RECT(x + 47, y - 8, x + 62, y + 8, EQ)                                # kaplin
        if dizel:
            RECT(x + 62, y - B / 2 + 10, x + A - 45, y + B / 2 - 10, EQ)       # motor
            RECT(x + A - 45, y - B / 2 + 5, x + A - 5, y + B / 2 - 5, EQ)      # radyatör
            for i in range(1, 6):
                L((x + A - 45 + 8 * i, y - B / 2 + 5), (x + A - 45 + 8 * i, y + B / 2 - 5), GZ)
            C((x + A * 0.6, y + B / 2 - 18), 6, EQ)                           # egzoz çıkışı
        else:
            RECT(x + 62, y - B / 2 * 0.55, x + A - 15, y + B / 2 * 0.55, EQ)
            RECT(x + 80, y + B / 2 * 0.55, x + 100, y + B / 2 * 0.55 + 10, EQ)  # klemens
    else:   # yan görünüş (x boyunca A)
        RECT(x - 10, y, x + A + 10, y + kaide, KD); HATCH(x - 10, y, x + A + 10, y + kaide, 8)
        y0 = y + kaide
        RECT(x, y0, x + A, y0 + 12, EQ)                                       # şasi
        ax = y0 + 12 + 35                                                     # mil ekseni
        C((x + 25, ax), 26, EQ); L((x + 25, ax + 26), (x + 25, ax + 45), EQ)  # salyangoz + basma ağzı
        FLANS((x + 25, ax + 45), dn_b, 90)
        L((x - 5, ax), (x + 5, ax), EQ); FLANS((x - 5, ax), dn_e, 0)          # emiş ağzı
        RECT(x + 40, y0 + 12, x + 50, ax - 20, EQ)                            # gövde ayağı
        RECT(x + 51, ax - 6, x + 64, ax + 6, EQ)                              # kaplin koruma
        if dizel:
            RECT(x + 64, y0 + 12, x + A - 45, H + y0 - 35, EQ)
            RECT(x + A - 45, y0 + 12, x + A - 5, H + y0 - 15, EQ)
            for i in range(1, 6):
                L((x + A - 45, y0 + 12 + i * (H - 27) / 6), (x + A - 5, y0 + 12 + i * (H - 27) / 6), GZ)
            RECT(x + A * 0.55, H + y0 - 35, x + A * 0.55 + 12, H + y0 - 5, EQ)  # egzoz manifoldu
        else:
            RECT(x + 64, ax - 30, x + A - 15, ax + 30, EQ)
            for i in range(1, 8):
                L((x + 64 + (A - 79) * i / 8, ax - 30), (x + 64 + (A - 79) * i / 8, ax + 30), GZ)
            RECT(x + 80, ax + 30, x + 100, ax + 40, EQ)


def yangin_seti(view, o, kaide=15):
    """DAB 1 KDN 40-250/240 E+D + jokey: elektrik modül 125x54, dizel 157,6x97,8, eksen aralığı 80 (V)"""
    x, y = o
    if view == 'P':
        _pompa_modul('P', x, y, 125, 54, 168.2, False)
        _pompa_modul('P', x, y + 80 + (97.8 - 54) / 2, 157.6, 97.8, 179.5, True)
        T((x + 70, y - 45), 'ELEKTRİKLİ ASIL POMPA', 7, YZ, 'TC')
        T((x + 80, y + 80 + 22 + 60), 'DİZEL YEDEK POMPA', 7, YZ, 'BC')
    elif view == 'Y':
        _pompa_modul('Y', x, y, 157.6, 97.8, 179.5, True, kaide=kaide)
    else:   # ön görünüş (emiş tarafından): salyangoz önde, motor/dizel arkada (gizli)
        for i, (B, H, dz) in enumerate(((54, 168.2, False), (97.8, 179.5, True))):
            xc = x + i * 120
            RECT(xc - B / 2 - 10, y, xc + B / 2 + 10, y + kaide, KD); HATCH(xc - B / 2 - 10, y, xc + B / 2 + 10, y + kaide, 8)
            y0 = y + kaide
            RECT(xc - B / 2, y0, xc + B / 2, y0 + 12, EQ)
            ax = y0 + 47
            C((xc, ax), 26, EQ); FLANS((xc, ax), 100, 0)
            L((xc, ax + 26), (xc, ax + 45), EQ); FLANS((xc, ax + 45), 100, 90)
            if dz:
                RECT(xc - B / 2 + 8, y0 + 12, xc + B / 2 - 8, y0 + H - 35 - kaide + 15, GZ)
            else:
                RECT(xc - 30, ax - 30, xc + 30, ax + 30, GZ)
        T((x, y - 12), 'ELEKTRİKLİ', 6, YZ, 'TC'); T((x + 120, y - 12), 'DİZEL', 6, YZ, 'TC')


def jokey(view, o):
    d = DATA['JOKEY']; Dm, H, Bp = d['D'], d['H'], d['B']
    x, y = o
    if view == 'P':
        RECT(x - Bp / 2, y - Bp / 2, x + Bp / 2, y + Bp / 2, EQ); C((x, y), Dm / 2, EQ)
    else:
        RECT(x - Bp / 2, y, x + Bp / 2, y + 4, EQ)
        RECT(x - 7, y + 4, x + 7, y + H * 0.45, EQ)
        for i in range(1, 6):
            L((x - 7, y + 4 + i * (H * 0.45 - 4) / 6), (x + 7, y + 4 + i * (H * 0.45 - 4) / 6), GZ)
        RECT(x - Dm / 2, y + H * 0.45, x + Dm / 2, y + H, EQ)
        L((x - 7, y + 12), (x - 18, y + 12), EQ); L((x + 7, y + 12), (x + 18, y + 12), EQ)


def pano(view, o, key='PANO'):
    d = DATA[key]; W, D, H = d['W'], d['D'], d['H']
    x, y = o
    if view == 'P':
        RECT(x - W / 2, y, x + W / 2, y + D, EQ)
        BAKIM(x - W / 2, y + D, x + W / 2, y + D + 100, 'PANO ÖNÜ ≥100')
    else:
        RECT(x - W / 2, y, x + W / 2, y + 10, KD)
        RECT(x - W / 2, y + 10, x + W / 2, y + H, EQ); L((x, y + 15), (x, y + H - 5), EQ)
        for i in range(3):
            C((x - 20 + 20 * i, y + H - 30), 3, EQ)


def alarm_vana(view, o, dn=150):
    x, y = o
    if view == 'P':
        RECT(x - 40, y, x + 40, y + 40, EQ); C((x, y + 20), FL_OD[dn] / 2, EQ)
    else:
        BORU2((x, y), (x, y + 200), dn, YB)
        VANA_OSY((x, y + 45), dn, 90)
        RECT(x - 13, y + 90, x + 13, y + 125, EQ); T((x + 30, y + 107), 'ALARM VANASI', 5, YZ, 'ML')
        MANO((x - 13, y + 95)); MANO((x - 13, y + 120))
        L((x + 13, y + 100), (x + 35, y + 100), EQ); RECT(x + 35, y + 95, x + 50, y + 105, EQ)   # gecikme odası
        L((x + 50, y + 100), (x + 60, y + 100), EQ); L((x + 60, y + 100), (x + 60, y + 30), EQ)   # test-drenaj
        T((x + 63, y + 30), 'TEST/DRENAJ', 4.5, YZ, 'L')


def yangin_dolabi(view, o):
    d = DATA['DOLAP']; W, D, H = d['W'], d['D'], d['H']
    x, y = o
    if view == 'P':
        RECT(x - W / 2, y, x + W / 2, y + D, EQ); ARC((x - W / 2, y + D), W, 0, 90, GZ)
    else:
        y0 = y + 80
        RECT(x - W / 2, y0, x + W / 2, y0 + H, EQ); RECT(x - W / 2 + 4, y0 + 4, x + W / 2 - 4, y0 + H - 4, EQ)
        C((x, y0 + H / 2), 28, EQ); C((x, y0 + H / 2), 10, EQ)
        T((x, y0 + H + 4), 'YANGIN DOLABI', 6, YZ, 'BC')


def hidrant(view, o):
    d = DATA['HIDRANT']; x, y = o
    if view == 'P':
        C((x, y), 11, EQ); L((x - 22, y), (x + 22, y), EQ)
    else:
        RECT(x - 11, y, x + 11, y + 95, EQ); RRECT(x - 13, y + 95, x + 13, y + 110, 4, EQ)
        for s in (-1, 1):
            RECT(x + s * 11, y + 70, x + s * 24, y + 82, EQ)
        RECT(x - 3, y + 110, x + 3, y + 116, EQ)
        L((x - 40, y), (x + 40, y), DV); T((x + 30, y + 72), 'ÇIKIŞ ≥70', 5, YZ, 'L')
        RECT(x - 8, y - 140, x + 8, y, GZ); T((x + 12, y - 70), 'DN100 GÖVDE (TOPRAK ALTI)', 5, YZ, 'L')


def grp_depo(view, o, nx=3, ny=2, nz=2, kaide=20):
    """1x1 m panel GRP depo: nx,ny,nz panel adedi (m); dış ~+15 cm"""
    x, y = o
    W, D, H = nx * 100 + 15, ny * 100 + 15, nz * 100 + 55 * 0 + 15
    if view == 'P':
        RECT(x, y, x + W, y + D, EQ)
        for i in range(1, nx):
            L((x + 7.5 + 100 * i, y), (x + 7.5 + 100 * i, y + D), EQ)
        for j in range(1, ny):
            L((x, y + 7.5 + 100 * j), (x + W, y + 7.5 + 100 * j), EQ)
        RECT(x + 20, y + 20, x + 103, y + 103, GZ); T((x + 61, y + 61), 'MENHOL 83x83', 5, YZ, 'MC')
        T((x + W / 2, y + D / 2), 'V=%d m³' % (nx * ny * nz), 9, YZ, 'MC')
    else:
        RECT(x - 10, y, x + W + 10, y + kaide, KD); HATCH(x - 10, y, x + W + 10, y + kaide, 8)
        y0 = y + kaide
        RECT(x, y0, x + W, y0 + H, EQ)
        n = nx if view == 'O' else ny
        for i in range(1, n):
            L((x + 7.5 + 100 * i, y0), (x + 7.5 + 100 * i, y0 + H), EQ)
        for j in range(1, nz):
            L((x, y0 + 7.5 + 100 * j), (x + W, y0 + 7.5 + 100 * j), EQ)
        L((x + 3, y0 + H - 20), (x + W - 3, y0 + H - 20), GZ)                # maks. su seviyesi
        T((x + W - 5, y0 + H - 18), 'MAKS. SU SEVİYESİ', 5, YZ, 'BR')


def hidrofor(view, o, key='HIDROFOR2'):
    d = DATA[key]; W, D, H = d['W'], d['D'], d['H']
    x, y = o
    if view == 'P':
        RECT(x - W / 2, y - D / 2, x + W / 2, y + D / 2, EQ)
        for dx in (-W / 4, W / 4):
            C((x + dx, y + 5), 10, EQ)
        L((x - W / 2, y - D / 2 + 8), (x + W / 2, y - D / 2 + 8), EQ)
        RECT(x - 15, y + D / 2 - 5, x + 15, y + D / 2 + 15, EQ)
    else:
        RECT(x - W / 2, y, x + W / 2, y + 6, EQ)
        for dx in (-W / 4, W / 4):
            RECT(x + dx - 8, y + 6, x + dx + 8, y + H * 0.45, EQ)
            RECT(x + dx - 10, y + H * 0.45, x + dx + 10, y + H * 0.85, EQ)
        RECT(x - W / 2, y + 22, x + W / 2, y + 30, EQ); RECT(x - W / 2, y + H * 0.55, x + W / 2, y + H * 0.55 + 8, EQ)
        RECT(x - 15, y + H * 0.6, x + 15, y + H, EQ)


def membranli(view, o, key='MTANK300'):
    d = DATA[key]; Dm, H = d['D'], d['H']
    x, y = o; r = Dm / 2
    if view == 'P':
        C((x, y), r, EQ)
    else:
        for xx in (x - r * 0.6, x + r * 0.6):
            L((xx, y), (xx, y + 10), EQ)
        RRECT(x - r, y + 10, x + r, y + H, r * 0.4, EQ)
        L((x - r * 0.8, y + H * 0.5), (x + r * 0.8, y + H * 0.5), GZ)


def pissu_istasyon(view, o, key='PISSU_IST'):
    d = DATA[key]; W, D, H = d['W'], d['D'], d['H']
    x, y = o
    if view == 'P':
        RRECT(x - W / 2, y - D / 2, x + W / 2, y + D / 2, 6, EQ); C((x - W / 4, y), 8, EQ); C((x + W / 4, y), 8, EQ)
    else:
        RRECT(x - W / 2, y, x + W / 2, y + H * 0.6, 6, EQ)
        RECT(x - W / 2 + 5, y + H * 0.6, x - 5, y + H, EQ); RECT(x + 5, y + H * 0.6, x + W / 2 - 5, y + H, EQ)
        L((x - W / 2, y + 25), (x - W / 2 - 20, y + 25), EQ); T((x - W / 2 - 22, y + 25), 'GİRİŞ DN100', 4.5, YZ, 'MR')


def vrf(view, o, key='VRF10'):
    d = DATA[key]; W, D, H = d['W'], d['D'], d['H']
    x, y = o
    if view == 'P':
        RECT(x - W / 2, y, x + W / 2, y + D, EQ)
        n = 1 if W < 100 else 2
        for i in range(n):
            C((x - W / 2 + W * (2 * i + 1) / (2 * n), y + D / 2), min(D, W / n) * 0.38, EQ)
        BAKIM(x - W / 2, y + D, x + W / 2, y + D + 50, 'ÖN ≥50 (ÜRETİCİ)')
    else:
        RECT(x - W / 2 - 10, y, x + W / 2 + 10, y + 15, KD)
        RECT(x - W / 2, y + 15, x + W / 2, y + 15 + H, EQ)
        n = 1 if W < 100 else 2
        for i in range(n):
            C((x - W / 2 + W * (2 * i + 1) / (2 * n), y + 15 + H - 25), 20, EQ)
        for k in range(1, 10):
            L((x - W / 2 + 4, y + 15 + k * 12), (x + W / 2 - 4, y + 15 + k * 12), GZ)


def ahu(view, o, key='AHU14'):
    d = DATA[key]; Lk, W, H = d['L'], d['W'], d['H']
    x, y = o
    secs = [('F', 0.12), ('ISI GERİ KAZ.', 0.30), ('FAN', 0.20), ('BATARYA', 0.14), ('FAN', 0.24)]
    if view == 'P':
        RECT(x, y, x + Lk, y + W, EQ)
        xx = x
        for t, f in secs:
            xx += Lk * f; L((xx, y), (xx, y + W), EQ)
        BAKIM(x, y + W, x + Lk, y + W + W, 'SERVİS (ÇEKMECE) = SANTRAL GENİŞLİĞİ')
    else:
        RECT(x - 5, y, x + Lk + 5, y + 15, KD)
        RECT(x, y + 15, x + Lk, y + 15 + H, EQ); L((x, y + 15 + H / 2), (x + Lk, y + 15 + H / 2), EQ)
        xx = x
        for t, f in secs:
            T((xx + Lk * f / 2, y + 15 + H * 0.25), t, 5, YZ, 'MC')
            xx += Lk * f; L((xx, y + 15), (xx, y + 15 + H), EQ)


def kaset(view, o, key='KASET'):
    d = DATA[key]; W, D, H = d['W'], d['D'], d['H']
    x, y = o
    if view == 'P':
        RECT(x - W / 2, y - D / 2, x + W / 2, y + D / 2, EQ); RECT(x - 28.5, y - 28.5, x + 28.5, y + 28.5, GZ)
        for a in range(4):
            ar = math.radians(90 * a)
            cx, cy = x + 34 * math.cos(ar), y + 34 * math.sin(ar)
            RECT(cx - (4 if a % 2 == 0 else 20), cy - (20 if a % 2 == 0 else 4), cx + (4 if a % 2 == 0 else 20), cy + (20 if a % 2 == 0 else 4), EQ)
    else:
        RECT(x - 28.5, y - H, x + 28.5, y, EQ); RECT(x - W / 2, y - H - 3, x + W / 2, y - H, EQ)


VIEWS = {
    'KOMBI24': (kombi, dict(key='KOMBI24')), 'DKAZAN65': (duvar_kazan, dict(key='DKAZAN65')),
    'DKAZAN65x3': (duvar_kazan, dict(key='DKAZAN65', n=3)), 'YKAZAN285': (yer_kazan, dict(key='YKAZAN285')),
    'CKAZAN235': (yer_kazan, dict(key='CKAZAN235')), 'YKAZAN800': (yer_kazan, dict(key='YKAZAN800')),
    'BOYLER500': (boyler, dict(key='BOYLER500')), 'BOYLER1000': (boyler, dict(key='BOYLER1000')),
    'AKUM2000': (boyler, dict(key='AKUM2000', serp=0)), 'GEN300': (genlesme, dict(key='GEN300')),
    'GEN100': (genlesme, dict(key='GEN100')), 'DENGE65': (denge_kabi, dict(key='DENGE65')),
    'POMPA50': (pompa_inline, dict(key='POMPA50')), 'ESANJOR': (esanjor, dict()),
    'YANGIN_SET': (yangin_seti, dict()), 'JOKEY': (jokey, dict()), 'PANO': (pano, dict()),
    'ALARM': (alarm_vana, dict()), 'DOLAP': (yangin_dolabi, dict()), 'HIDRANT': (hidrant, dict()),
    'GRP': (grp_depo, dict(nx=2, ny=2, nz=2)), 'HIDROFOR2': (hidrofor, dict()), 'MTANK300': (membranli, dict()),
    'PISSU_IST': (pissu_istasyon, dict()), 'VRF10': (vrf, dict(key='VRF10')), 'VRF20': (vrf, dict(key='VRF20')),
    'AHU14': (ahu, dict()), 'KASET': (kaset, dict()),
}
