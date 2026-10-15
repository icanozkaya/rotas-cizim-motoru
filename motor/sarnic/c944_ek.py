# -*- coding: utf-8 -*-
"""944 Ada 343 Parsel (Güngören B1-B2-B3) — EK çizim:
  1) Yağmur suyu sarnıcı (toprak altı betonarme, bahçe sulama) — 1. bodrum sıhhi planı + kesit + hesap + şema
  2) Otopark duman tahliyesi (10 hava değişimi) — havalandırma paftası 1. bodrum planı + hesap + şema
Koordinatlar kullanıcının 944-343_PARSEL_B1-B2-B3_BLOK_MEKANİK.dwg dosyasıyla aynıdır (birim cm).
Yerleştirme: bu DXF açılır, tümü seçilip COPYCLIP → mekanik dosyada PASTEORIG.
"""
import math, sys
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

OUT = sys.argv[1] if len(sys.argv) > 1 else '944-343_YAGMUR_SARNICI_DUMAN_TAHLIYE_EK.dxf'

doc = ezdxf.new('R2010', setup=True)
doc.units = 5
STY = 'ROTAS-ARIAL'
doc.styles.new(STY, dxfattribs={'font': 'arial.ttf'})
LAY = {
    # yağmur / sarnıç
    'MTY-YAGMUR-BORUSU': (3, 'DASHED'), 'MTY-YAGMUR-BORUSU-CAP': (3, None), 'MTY-YAGMURSU-KOLON NO': (3, None),
    'YS-SARNIC': (11, None), 'YS-SARNIC-TARAMA': (8, None), 'YS-CIHAZ': (135, None), 'YS-VANA': (1, None),
    'YS-KULLANMA': (200, None), 'YS-TASMA': (34, 'DASHED'), 'YS-YAZI': (7, None), 'YS-KOT': (7, None),
    'YS-ELEKTRIK': (8, 'DASHED2'), 'MTY-ROGAR': (5, None), 'YS-TOPRAK': (8, None),
    # duman tahliye
    'MTY-DUMAN-EGZOZ-KANALI': (1, None), 'MTY-DUMAN-EGZOZ-CAP': (1, None), 'MTY-DUMAN-MENFEZ': (1, None),
    'MTY-DUMAN-FAN': (30, None), 'MTY-TAZE-HAVA': (5, 'DASHED'), 'MTY-HAVALANDIRMA-SEMA': (7, None),
    # tablolar
    'ROTAS-HESAP-CERCEVE': (7, None), 'ROTAS-HESAP-CIZGI': (8, None), 'ROTAS-HESAP-YAZI': (7, None), 'ROTAS-HESAP-BASLIK': (2, None),
}
for n, (c, lt) in LAY.items():
    a = {'color': c}
    if lt: a['linetype'] = lt
    doc.layers.add(n, **a)
msp = doc.modelspace()

# ------------------------------------------------------------------ yardımcılar
def L(a, b, lay, w=0):
    if w: return msp.add_lwpolyline([a, b], dxfattribs={'layer': lay, 'const_width': w})
    return msp.add_line(a, b, dxfattribs={'layer': lay})
def PL(pts, lay, close=False, w=0, lts=None):
    a = {'layer': lay, 'const_width': w}
    if lts: a['ltscale'] = lts
    return msp.add_lwpolyline(pts, close=close, dxfattribs=a)
def REC(x1, y1, x2, y2, lay, w=0):
    return PL([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], lay, True, w)
def C(c, r, lay):
    return msp.add_circle(c, r, dxfattribs={'layer': lay})
def T(s, x, y, h, lay='YS-YAZI', al='MIDDLE_LEFT', rot=0, col=None):
    a = {'layer': lay, 'style': STY, 'width': 0.9, 'rotation': rot}
    if col is not None: a['color'] = col
    t = msp.add_text(s, height=h, dxfattribs=a); t.set_placement((x, y), align=TA[al]); return t
def ARROW(a, b, lay, s=12):
    """a->b doğrultusunda ok ucu b'de"""
    L(a, b, lay)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    p1 = (b[0] - s * math.cos(ang) + s * 0.35 * math.sin(ang), b[1] - s * math.sin(ang) - s * 0.35 * math.cos(ang))
    p2 = (b[0] - s * math.cos(ang) - s * 0.35 * math.sin(ang), b[1] - s * math.sin(ang) + s * 0.35 * math.cos(ang))
    msp.add_solid([b, p1, p2], dxfattribs={'layer': lay})
def HATCH_REC(x1, y1, x2, y2, lay='YS-SARNIC-TARAMA', step=10):
    """beton tarama: 45° çizgiler (dikdörtgen içinde)"""
    w, h = x2 - x1, y2 - y1
    k = -h
    while k < w:
        # y = x - k doğrusu
        pts = []
        for xx in (x1 + max(k, 0), x1 + min(k + h, w)):
            pts.append((xx, y1 + (xx - x1 - k)))
        if pts[0][0] < pts[1][0]: L(pts[0], pts[1], lay)
        k += step
def LEADER(pts, lay):
    PL(pts, lay)

def f(v, d=2):
    return f'{v:,.{d}f}'.replace(',', '#').replace('.', ',').replace('#', '.')

# --- semboller (gerçek çizim)
def VANA(c, ang, lay='YS-VANA', s=7):
    """küresel vana: papyon + mil"""
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda u, v: (c[0] + u * ca - v * sa, c[1] + u * sa + v * ca)
    PL([P(-s, -s * .6), P(s, s * .6), P(s, -s * .6), P(-s, s * .6)], lay, True)
    L(P(0, 0), P(0, s * 1.2), lay); L(P(-s * .5, s * 1.2), P(s * .5, s * 1.2), lay)
def CEKVALF(c, ang, lay='YS-VANA', s=7):
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda u, v: (c[0] + u * ca - v * sa, c[1] + u * sa + v * ca)
    PL([P(-s, -s * .6), P(s, s * .6), P(s, -s * .6), P(-s, s * .6)], lay, True)
    msp.add_solid([P(-s, -s * .6), P(0, 0), P(-s, s * .6)], dxfattribs={'layer': lay})
def POMPA(c, r=12, ang=0, lay='YS-CIHAZ'):
    C(c, r, lay)
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda u, v: (c[0] + u * ca - v * sa, c[1] + u * sa + v * ca)
    PL([P(-r * .55, -r * .7), P(r * .85, 0), P(-r * .55, r * .7)], lay, True)
def TANK(c, w=22, h=34, lay='YS-CIHAZ'):
    x, y = c
    PL([(x - w / 2, y - h / 2 + w / 2), (x - w / 2, y + h / 2 - w / 2)], lay)
    PL([(x + w / 2, y - h / 2 + w / 2), (x + w / 2, y + h / 2 - w / 2)], lay)
    msp.add_arc((x, y + h / 2 - w / 2), w / 2, 0, 180, dxfattribs={'layer': lay})
    msp.add_arc((x, y - h / 2 + w / 2), w / 2, 180, 360, dxfattribs={'layer': lay})
    L((x - w / 2, y), (x + w / 2, y), lay)  # membran
def MANOMETRE(c, r=5, lay='YS-CIHAZ'):
    C(c, r, lay); L(c, (c[0] + r * .6, c[1] + r * .6), lay)
def FILTRE_Y(c, ang=0, lay='YS-CIHAZ', s=8):
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda u, v: (c[0] + u * ca - v * sa, c[1] + u * sa + v * ca)
    L(P(-s, 0), P(s, 0), lay); PL([P(-s * .3, 0), P(s * .4, -s * 1.1), P(s * .9, -s * .8)], lay)
def GIRDAP(c, r=16, lay='YS-CIHAZ'):
    C(c, r, lay); C(c, r * .55, lay)
    for k in range(4):
        a = k * math.pi / 2
        msp.add_arc((c[0] + r * .3 * math.cos(a), c[1] + r * .3 * math.sin(a)), r * .45, math.degrees(a) + 90, math.degrees(a) + 200, dxfattribs={'layer': lay})
def FAN(c, r=45, lay='MTY-DUMAN-FAN'):
    C(c, r, lay); C(c, r * .18, lay)
    for k in range(4):
        a = k * math.pi / 2 + .3
        p = (c[0] + r * .85 * math.cos(a), c[1] + r * .85 * math.sin(a))
        q = (c[0] + r * .85 * math.cos(a + .55), c[1] + r * .85 * math.sin(a + .55))
        PL([(c[0] + r * .18 * math.cos(a), c[1] + r * .18 * math.sin(a)), p, q, (c[0] + r * .18 * math.cos(a + .6), c[1] + r * .18 * math.sin(a + .6))], lay)
def YB_SYM(c, tag, lay='MTY-YAGMURSU-KOLON NO', ldir=(1, 1), off=(34, 30)):
    C(c, 7, 'MTY-YAGMUR-BORUSU'); C(c, 4, 'MTY-YAGMUR-BORUSU')
    tx, ty = c[0] + ldir[0] * off[0], c[1] + ldir[1] * off[1]
    L((c[0] + ldir[0] * 7, c[1] + ldir[1] * 6), (tx - ldir[0] * 16, ty - ldir[1] * 9), lay)
    C((tx, ty), 16, lay); C((tx, ty), 13, lay)
    T(tag, tx, ty, 7.5, lay, 'MIDDLE_CENTER')

# ------------------------------------------------------------------ TABLO
def TABLO(x0, y0, baslik, cols, rows, h=11, rh=26, bold_rows=(), title_h=15, alt=None):
    X = [x0]
    for w in cols: X.append(X[-1] + w)
    T(baslik, x0 + 8, y0 - 22, title_h, 'ROTAS-HESAP-BASLIK')
    y = y0 - 40
    for i, r in enumerate(rows):
        hdr = (i == 0)
        for j in range(len(cols)):
            REC(X[j], y - rh, X[j + 1], y, 'ROTAS-HESAP-CIZGI')
            s = str(r[j]) if j < len(r) else ''
            if not s: continue
            al = 'MIDDLE_CENTER' if (hdr or j == 0 or cols[j] < 110) else 'MIDDLE_LEFT'
            xx = (X[j] + X[j + 1]) / 2 if al == 'MIDDLE_CENTER' else X[j] + 6
            T(s, xx, y - rh / 2, h, 'ROTAS-HESAP-BASLIK' if (hdr or i in bold_rows) else 'ROTAS-HESAP-YAZI', al)
        y -= rh
    if alt:
        for k, s in enumerate(alt):
            T(s, x0 + 4, y - 18 - k * 20, h * 0.95, 'ROTAS-HESAP-YAZI')
        y -= 18 + len(alt) * 20
    REC(x0 - 12, y - 10, X[-1] + 12, y0 + 6, 'ROTAS-HESAP-CERCEVE', 1.2)
    return y - 10

# =================================================================================
# 1) YAĞMUR SUYU SARNICI — sıhhi tesisat 1. BODRUM KAT PLANI (B3–B2 arası ön bahçe)
# =================================================================================
# Bloklar (asansör kuyusu ile zemin kat planından aktarıldı)
BL = {'B3': (248020, 249775), 'B2': (250729, 252484), 'B1': (253089, 254844)}
YN, YS_ = -499080.0, -500250.0          # blok kuzey / güney cephe
YB = {}
for b, (x1, x2) in BL.items():
    YB[b + '-YB1'] = (x1 - 15, YN + 15)     # kuzey-batı
    YB[b + '-YB2'] = (x2 + 15, YN + 15)     # kuzey-doğu
    YB[b + '-YB3'] = (x2 + 15, YS_ - 15)    # güney-doğu
    YB[b + '-YB4'] = (x1 - 15, YS_ - 15)    # güney-batı
# blok sırası B3 (sol) - B2 - B1 (sağ); etiket yönleri
for k, c in YB.items():
    d = (-1 if k.endswith(('YB1', 'YB4')) else 1, 1 if k.endswith(('YB1', 'YB2')) else -1)
    off = (34, 30) if d[1] > 0 else (40, 78)
    if k == 'B3-YB3': d = (-1, -1)
    if k == 'B2-YB4': d, off = (1, -1), (125, 78)
    YB_SYM(c, k, ldir=d, off=off)

# Sarnıç (dış ölçü 760 x 190, perde 20 cm) — kullanıcının işaretlediği yer, B3-B2 arası bahçe
SX1, SX2, SY1, SY2 = 249840.0, 250600.0, -500530.0, -500340.0
IX1, IX2, IY1, IY2 = SX1 + 20, SX2 - 20, SY1 + 20, SY2 - 20      # iç 720 x 150
REC(SX1, SY1, SX2, SY2, 'YS-SARNIC', 1.5); REC(IX1, IY1, IX2, IY2, 'YS-SARNIC')
# perde tarama (plan) — sadece duvar bantları
for (a, b, c_, d) in ((SX1, SY1, SX2, IY1), (SX1, IY2, SX2, SY2), (SX1, IY1, IX1, IY2), (IX2, IY1, SX2, IY2)):
    HATCH_REC(a, b, c_, d, step=12)
# rögar kapakları 60x60 (M1 pompa ucu, M2 giriş/taşma ucu)
M1 = (IX1 + 70, (IY1 + IY2) / 2); M2 = (IX2 - 80, (IY1 + IY2) / 2)
for m in (M1, M2):
    REC(m[0] - 30, m[1] - 30, m[0] + 30, m[1] + 30, 'YS-SARNIC'); REC(m[0] - 26, m[1] - 26, m[0] + 26, m[1] + 26, 'YS-SARNIC')
T('M1', M1[0], M1[1] + 38, 9, 'YS-YAZI', 'MIDDLE_CENTER'); T('M2', M2[0], M2[1] + 38, 9, 'YS-YAZI', 'MIDDLE_CENTER')
T('YAĞMUR SUYU SARNICI (TOPRAK ALTI BETONARME)', (SX1 + SX2) / 2, (IY1 + IY2) / 2 + 12, 11, 'YS-YAZI', 'MIDDLE_CENTER')
T('İç 7,20 x 1,50 m - faydalı h = 1,90 m - V = 20,5 m³', (SX1 + SX2) / 2, (IY1 + IY2) / 2 - 8, 9, 'YS-YAZI', 'MIDDLE_CENTER')
T('A', SX1 - 40, (SY1 + SY2) / 2, 14, 'YS-YAZI', 'MIDDLE_CENTER'); T('A', SX2 + 250, (SY1 + SY2) / 2, 14, 'YS-YAZI', 'MIDDLE_CENTER')
L((SX1 - 28, (SY1 + SY2) / 2), (SX1 - 6, (SY1 + SY2) / 2), 'YS-YAZI', 2)

# F1 girdap filtre + toplama bacası (150 x 150)
FX1, FX2, FY1, FY2 = 250620.0, 250770.0, -500430.0, -500280.0
REC(FX1, FY1, FX2, FY2, 'YS-SARNIC', 1.5); REC(FX1 + 12, FY1 + 12, FX2 - 12, FY2 - 12, 'YS-SARNIC')
FC = ((FX1 + FX2) / 2, (FY1 + FY2) / 2 + 5)
GIRDAP(FC, 22)
T('F1', FX2 + 8, FY2 + 14, 11, 'YS-YAZI');

# --- toplama hatları (yağmur)
YC = -500310.0        # ön cephe toplama hattı (bodrum perdesi önü, gerçek toprak)
YR = -499010.0        # arka cephe toplama hattı (bahçe dolgusu)
XG1 = 250680.0        # B3-B2 arası iniş bacağı (F1'e üstten girer)
XG2 = 252786.0        # B2-B1 arası iniş bacağı
LY = 'MTY-YAGMUR-BORUSU'
def YH(pts): PL(pts, LY, lts=0.6)
# arka-batı: B3-YB1 → B3-YB2 → B2-YB1 → aşağı → F1 üst
YH([(YB['B3-YB1'][0], YB['B3-YB1'][1]), (YB['B3-YB1'][0], YR), (XG1, YR), (XG1, FY2)])
L(YB['B3-YB2'], (YB['B3-YB2'][0], YR), LY)
L(YB['B2-YB1'], (YB['B2-YB1'][0], YR), LY); L((YB['B2-YB1'][0], YR), (XG1, YR), LY)
L(YB['B2-YB4'], (XG1, YB['B2-YB4'][1]), LY)          # B2 güney-batı inişi doğrudan bacağa
# ön-batı: B3-YB4 → B3-YB3 → sarnıç ile perde arasından → F1 batı yüzü
YH([(YB['B3-YB4'][0], YB['B3-YB4'][1]), (YB['B3-YB4'][0], YC), (FX1, YC)])
L(YB['B3-YB3'], (YB['B3-YB3'][0], YC), LY)
# ön-doğu: B1-YB3 → B1-YB4 → (XG2) → B2-YB3 → F1 doğu yüzü
YH([(YB['B1-YB3'][0], YB['B1-YB3'][1]), (YB['B1-YB3'][0], YC), (FX2, YC)])
L(YB['B1-YB4'], (YB['B1-YB4'][0], YC), LY)
L(YB['B2-YB3'], (YB['B2-YB3'][0], YC), LY)
# arka-doğu: B1-YB2 → B1-YB1 → XG2 ; B2-YB2 → XG2 ; XG2 aşağı → ön hat
YH([(YB['B1-YB2'][0], YB['B1-YB2'][1]), (YB['B1-YB2'][0], YR), (XG2, YR), (XG2, YC)])
L(YB['B1-YB1'], (YB['B1-YB1'][0], YR), LY)
YH([(YB['B2-YB2'][0], YB['B2-YB2'][1]), (YB['B2-YB2'][0], YR), (XG2, YR)])
# akış okları + çap etiketleri
def YETK(x, y, s, rot=0, al='BOTTOM_CENTER'):
    T(s, x, y, 9, 'MTY-YAGMUR-BORUSU-CAP', al, rot)
YETK(249450, YR + 6, 'Ø160 PVC %0,5 - 3 YB - 5,33 l/s (BAHÇE DOLGUSU İÇİNDE)')
YETK(XG1 - 8, -499650, 'Ø160 PVC %0,5 - 4 YB - 7,11 l/s', 90)
YETK(248900, YC - 22, 'Ø110 PVC %0,5 - 2 YB - 3,55 l/s', 0, 'TOP_CENTER')
YETK(251600, YC - 22, 'Ø160 PVC %0,5 - 6 YB - 10,67 l/s', 0, 'TOP_CENTER')
YETK(253900, YC - 22, 'Ø110 PVC %0,5 - 2 YB', 0, 'TOP_CENTER')
YETK(253930, YR + 6, 'Ø110 PVC %0,5 - 2 YB')
YETK(XG2 - 8, -499650, 'Ø160 PVC %0,5 - 3 YB - 5,33 l/s', 90)
for a, b in (((248600, YR), (248680, YR)), ((XG1, -499900), (XG1, -499980)), ((249200, YC), (249280, YC)),
             ((252100, YC), (252020, YC)), ((254300, YC), (254220, YC)), ((XG2, -499900), (XG2, -499980)), ((254400, YR), (254320, YR))):
    ARROW(a, b, LY, 14)

# F1 → sarnıç (süzülmüş su, sakinleştirici giriş)
L((FX1, -500375), (IX2 - 60, -500375), LY); L((IX2 - 60, -500375), (IX2 - 60, IY1 + 25), LY)
C((IX2 - 60, IY1 + 18), 7, 'YS-CIHAZ')
# taşma sifonu (sarnıç içi, doğu duvar dibi) → F1 bacası → F1 kirli su ile → YSR
XT = IX2 - 25
C((XT, -500420), 6, 'YS-CIHAZ')
PL([(XT + 6, -500420), (250740.0, -500420)], 'YS-TASMA', lts=0.6)
YSR = (250740.0, -500760.0)
PL([(YSR[0], -500420), (YSR[0], YSR[1] + 30)], 'YS-TASMA', lts=0.6)
REC(YSR[0] - 30, YSR[1] - 30, YSR[0] + 30, YSR[1] + 30, 'MTY-ROGAR'); REC(YSR[0] - 24, YSR[1] - 24, YSR[0] + 24, YSR[1] + 24, 'MTY-ROGAR')
T('YSR', YSR[0], YSR[1], 12, 'MTY-ROGAR', 'MIDDLE_CENTER')
ARROW((YSR[0] + 30, YSR[1]), (YSR[0] + 160, YSR[1]), 'YS-TASMA', 16)
T('YAĞMUR SUYU KANALINA GİDER', YSR[0] + 170, YSR[1] + 9, 11, 'YS-YAZI')
T('(pis su kanalına bağlanmaz)', YSR[0] + 170, YSR[1] - 11, 9, 'YS-YAZI')
T('TAŞMA + F1 KİRLİ SU Ø200 PVC %1 (CAZİBE)', YSR[0] + 8, -500600, 9, 'YS-YAZI', 'MIDDLE_LEFT', 0)

# dalgıç pompa (M1 altında) + yüzer emiş + vana bacası (VB) + sulama hattı
P1 = (M1[0] + 40, M1[1] + 15); POMPA(P1, 11, -math.pi / 2)
T('P', P1[0] + 15, P1[1] + 12, 9, 'YS-YAZI')
LT = (M1[0] - 45, M1[1] + 18); C(LT, 6, 'YS-CIHAZ'); T('LT', LT[0] - 9, LT[1] + 10, 8, 'YS-YAZI', 'MIDDLE_RIGHT')
PL([(P1[0] + 9, P1[1] - 7), (P1[0] + 70, P1[1] - 30)], 'YS-KULLANMA')  # yüzer emiş hortumu
C((P1[0] + 75, P1[1] - 31), 5, 'YS-CIHAZ')
VBX1, VBX2, VBY1, VBY2 = 249860.0, 250040.0, -500700.0, -500570.0
REC(VBX1, VBY1, VBX2, VBY2, 'YS-SARNIC', 1.5); REC(VBX1 + 10, VBY1 + 10, VBX2 - 10, VBY2 - 10, 'YS-SARNIC')
T('VB - SULAMA VANA BACASI', VBX2 + 8, VBY1 + 8, 9, 'YS-YAZI')
xk = P1[0]
PL([(xk, P1[1] - 11), (xk, VBY2 - 25), (VBX1 + 30, VBY2 - 25), (VBX1 + 30, -500655), (VBX1 - 260, -500655)], 'YS-KULLANMA', w=1.2)
CEKVALF((xk, SY1 - 20), -math.pi / 2)
TANK((VBX2 - 35, VBY2 - 70), 18, 30)
L((xk, VBY2 - 25), (VBX2 - 35, VBY2 - 25), 'YS-KULLANMA')
L((VBX2 - 35, VBY2 - 55), (VBX2 - 35, VBY2 - 25), 'YS-KULLANMA')
MANOMETRE((VBX1 + 60, VBY2 - 45))
L((VBX1 + 60, VBY2 - 40), (VBX1 + 60, VBY2 - 25), 'YS-KULLANMA')
VANA((VBX1 + 30, -500640), -math.pi / 2)
FILTRE_Y((VBX1 - 40, -500655), math.pi)
VANA((VBX1 - 100, -500655), 0)
ARROW((VBX1 - 200, -500655), (VBX1 - 260, -500655), 'YS-KULLANMA', 14)
T('YSK Ø32 PE100 → BAHÇE SULAMA DAĞITIMINA', VBX1 - 270, -500640, 10, 'YS-YAZI', 'BOTTOM_RIGHT')
T('(YAĞMUR SUYU - İÇİLEMEZ)', VBX1 - 270, -500668, 9, 'YS-YAZI', 'TOP_RIGHT')
# ekipman numaraları (yuvarlak etiket)
def ENO(n, at, to):
    C(to, 11, 'YS-YAZI'); T(str(n), to[0], to[1], 10, 'YS-YAZI', 'MIDDLE_CENTER')
    d = math.hypot(at[0] - to[0], at[1] - to[1])
    L(at, (to[0] + (at[0] - to[0]) * 11 / d, to[1] + (at[1] - to[1]) * 11 / d), 'YS-YAZI')
ENO(1, (FC[0] + 10, FC[1] + 10), (FX2 + 60, FY2 + 60))
ENO(2, (IX2 - 60, IY1 + 18), (IX2 - 60, SY1 - 50))
ENO(3, (SX1 + 200, SY2), (SX1 + 230, SY2 + 85))
ENO(4, (XT, -500420), (XT - 120, SY2 + 85))
ENO(5, (P1[0] + 75, P1[1] - 31), (P1[0] + 130, SY2 + 85))
ENO(6, LT, (LT[0] - 30, SY2 + 85))
ENO(7, P1, (P1[0] + 70, SY2 + 85))
ENO(8, (VBX2 - 35, VBY2 - 70), (VBX2 + 40, VBY2 - 10))
ENO(9, (VBX1 - 40, -500660), (VBX1 - 40, -500720))
ENO(10, YSR, (YSR[0] - 70, YSR[1] - 40))
# plan notu
T('YAĞMUR SUYU SARNICI - A+B: B1-B2-B3 BLOK 12 ADET YB - YALNIZ BAHÇE SULAMA', 248020, -500880, 13, 'YS-YAZI')
T('Ön cephe hatları perde önünde toprak altında, arka cephe hatları bodrum tavan döşemesi üzerindeki bahçe dolgusu içinde döşenecektir.', 248020, -500905, 9.5, 'YS-YAZI')
T('Sarnıç A-A kesiti, hesaplar ve prensip şeması bu planın altında verilmiştir.', 248020, -500925, 9.5, 'YS-YAZI')

# ---------------------------------------------------------------- A-A KESİTİ (1/50) - sayfa altı
KX0, KY0 = 251000.0, -500930.0      # zemin (bahçe) kotu -0,20 bu y'de
def KY(k):  # kot (m) → y
    return KY0 + (k + 0.20) * 100
T('A-A KESİTİ  -  YAĞMUR SUYU SARNICI.........ÖLÇEK: 1 / 50', KX0, KY(-0.20) + 75, 15, 'YS-YAZI')
# toprak çizgisi
L((KX0 - 120, KY(-0.20)), (KX0 + 1000, KY(-0.20)), 'YS-TOPRAK')
for i in range(0, 1100, 40): L((KX0 - 120 + i, KY(-0.20)), (KX0 - 105 + i, KY(-0.20) + 12), 'YS-TOPRAK')
w = 760; ox = KX0
outer = (ox, KY(-3.65), ox + w, KY(-0.20))
inner = (ox + 20, KY(-3.40), ox + w - 20, KY(-0.40))
# betonarme kesit: dış - iç arasında tarama
for (a, b, c_, d) in ((ox, KY(-3.65), ox + w, KY(-3.40)), (ox, KY(-0.40), ox + w, KY(-0.20)),
                      (ox, KY(-3.40), ox + 20, KY(-0.40)), (ox + w - 20, KY(-3.40), ox + w, KY(-0.40))):
    REC(a, b, c_, d, 'YS-SARNIC'); HATCH_REC(a, b, c_, d, step=10)
REC(*outer, 'YS-SARNIC', 1.5)
# grobeton
REC(ox - 10, KY(-3.75), ox + w + 10, KY(-3.65), 'YS-SARNIC')
# kapaklar (M1, M2) boyun
for mx in (ox + 90, ox + w - 100):
    REC(mx - 30, KY(-0.40), mx + 30, KY(-0.20), 'YS-SARNIC')
    L((mx - 36, KY(-0.20) + 3), (mx + 36, KY(-0.20) + 3), 'YS-SARNIC', 2)
    T('60x60 DÖKME DEMİR KAPAK (KİLİTLİ)', mx, KY(-0.20) + 10, 7.5, 'YS-YAZI', 'BOTTOM_CENTER')
# su seviyeleri
for k, s in ((-1.35, 'TAŞMA SEVİYESİ (MAKS. SU) -1,35'), (-3.25, 'POMPA DURMA (MİN. SU) -3,25')):
    PL([(ox + 20, KY(k)), (ox + w - 20, KY(k))], 'YS-TASMA', lts=0.4)
    T(s, ox + w / 2, KY(k) + 4, 8, 'YS-YAZI', 'BOTTOM_CENTER')
# giriş: F1'den, sakinleştirici
fx = ox + w + 70
REC(fx - 40, KY(-1.70), fx + 40, KY(-0.20), 'YS-SARNIC')
T('F1', fx, KY(-0.20) + 10, 9, 'YS-YAZI', 'BOTTOM_CENTER')
GIRDAP((fx, KY(-0.95)), 14)
L((fx, KY(-0.60)), (fx, KY(-0.81)), 'MTY-YAGMUR-BORUSU')
T('← giriş -0,90', fx + 44, KY(-0.90), 7.5, 'YS-YAZI')
L((fx - 14, KY(-1.05)), (fx - 25, KY(-1.20)), 'MTY-YAGMUR-BORUSU'); L((fx - 25, KY(-1.20)), (ox + w - 70, KY(-1.20)), 'MTY-YAGMUR-BORUSU')
L((ox + w - 70, KY(-1.20)), (ox + w - 70, KY(-3.25)), 'MTY-YAGMUR-BORUSU')
T('süzülmüş su -1,20', ox + w - 66, KY(-1.20) + 4, 7, 'YS-YAZI', 'BOTTOM_LEFT')
PL([(ox + w - 90, KY(-3.20)), (ox + w - 50, KY(-3.20))], 'YS-CIHAZ', w=2)
T('Sakinleştirici giriş', ox + w - 95, KY(-3.15), 7.5, 'YS-YAZI', 'BOTTOM_RIGHT')
# taşma sifonu
tx = ox + w - 45
PL([(tx - 10, KY(-1.30)), (tx - 5, KY(-1.35)), (tx + 5, KY(-1.35)), (tx + 10, KY(-1.30))], 'YS-TASMA')
PL([(tx, KY(-1.35)), (tx, KY(-1.65)), (fx - 40, KY(-1.65))], 'YS-TASMA')
PL([(fx, KY(-1.10)), (fx, KY(-1.65)), (fx + 40, KY(-1.65)), (fx + 150, KY(-1.66))], 'YS-TASMA')
T('Taşma sifonu + kemirgen kapanı', tx - 14, KY(-1.48), 7.5, 'YS-YAZI', 'MIDDLE_RIGHT')
T('Ø200 %1 → YSR', fx + 48, KY(-1.65) + 4, 7.5, 'YS-YAZI', 'BOTTOM_LEFT')
T('F1 kirli su', fx + 6, KY(-1.30), 7, 'YS-YAZI')
# dalgıç pompa + yüzer emiş
px = ox + 90
POMPA((px, KY(-3.05)), 13, math.pi / 2)
PL([(px + 13, KY(-3.05)), (px + 80, KY(-1.65))], 'YS-KULLANMA')
C((px + 84, KY(-1.60)), 6, 'YS-CIHAZ'); T('Yüzer emiş', px + 92, KY(-1.60), 7.5, 'YS-YAZI')
L((px, KY(-2.92)), (px, KY(-0.40)), 'YS-KULLANMA', 1.2)
T('Dalgıç pompa', px + 16, KY(-3.15), 7.5, 'YS-YAZI')
lx = ox + 45
L((lx, KY(-0.40)), (lx, KY(-3.30)), 'YS-ELEKTRIK'); C((lx, KY(-3.32)), 4, 'YS-CIHAZ')
T('LT', lx - 6, KY(-3.32), 7.5, 'YS-YAZI', 'MIDDLE_RIGHT')
# havalık
hx = ox + w / 2
PL([(hx, KY(-0.20)), (hx, KY(+0.40)), (hx - 15, KY(+0.40)), (hx - 15, KY(+0.30))], 'YS-CIHAZ')
T('Havalık Ø100 (sinek telli)', hx + 6, KY(+0.30), 7.5, 'YS-YAZI')
# kotlar
def KOT(x, k, s=None):
    y = KY(k)
    PL([(x, y), (x - 6, y + 9), (x + 6, y + 9), (x, y)], 'YS-KOT', True); L((x, y), (x + 60, y), 'YS-KOT')
    T(s or (f'{k:+.2f}'.replace('.', ',') if k else '±0,00'), x + 8, y + 3, 8, 'YS-KOT', 'BOTTOM_LEFT')
KOT(ox - 70, -0.20, '-0,20 bahçe'); KOT(ox - 70, -0.40); KOT(ox - 70, -3.40, '-3,40 iç taban'); KOT(ox - 70, -3.65)
# ölçü çizgisi
def OLCU(a, b, off, s):
    y = a[1] + off
    L((a[0], y), (b[0], y), 'YS-KOT'); L((a[0], a[1]), (a[0], y + 4), 'YS-KOT'); L((b[0], b[1]), (b[0], y + 4), 'YS-KOT')
    for xx in (a[0], b[0]): L((xx - 4, y - 4), (xx + 4, y + 4), 'YS-KOT', 0.8)
    T(s, (a[0] + b[0]) / 2, y + 3, 8, 'YS-KOT', 'BOTTOM_CENTER')
OLCU((ox, KY(-3.75)), (ox + w, KY(-3.75)), -22, '760 (iç 720)')
L((ox + w + 160, KY(-3.25)), (ox + w + 160, KY(-1.35)), 'YS-KOT')
T('h faydalı = 1,90 m (min. su ile taşma arası)', ox + w + 168, KY(-2.30), 8, 'YS-KOT')
T('Bodrum perdesi (mevcut) sarnıcın kuzey yüzüne bitişiktir; sarnıç bağımsız radye üzerinde, su yalıtımlı (TS EN 1504 / kristalize katkı) yapılacaktır.', ox - 120, KY(-3.75) - 52, 8, 'YS-YAZI')

# ---------------------------------------------------------------- HESAPLAR
H_YAG = 659.4         # mm/yıl — İstanbul (MGM uzun yıllar), Güngören projesinde kullanılan değer
A_BLOK = 237.0        # m² — her blok çatı iz düşümü (saçak dahil, çatı planı)
A = 3 * A_BLOK
e, eta = 0.80, 0.90
E = A * H_YAG / 1000 * e * eta
Vmin = 0.06 * E
Ad = 7.20 * 1.50
hf = 1.90
Vm = Ad * hf
r_ = 0.030            # l/s·m² tasarım yağış şiddeti
Qr = A * r_
qYB = Qr / 12
Q_P = 1.5             # m³/h
Hgeo = 3.40 + 0.50
Hk = 6.0
Hc = 25.0
H_P = Hgeo + Hk + Hc
Pw = 1000 * 9.81 * Q_P / 3600 * H_P / 0.40 / 1000
Pd, Pk = 3.5, 4.9
Vt = 1000 * Q_P / (4 * 20) * (Pk + 1) / (Pk - Pd)
R = [
 ('NO', 'KALEM', 'FORMÜL / KAYNAK', 'DEĞER'),
 ('1', 'Yıllık yağış (İstanbul, MGM uzun yıllar)', 'h', f(H_YAG, 1) + ' mm'),
 ('2', 'Toplama alanı - B1+B2+B3 çatı iz düşümü (saçak dahil)', 'A = 3 x 237,0', f(A, 1) + ' m²'),
 ('3', 'Çatı verim katsayısı (kiremit kırma çatı) / filtre verimi', 'e / η', '0,80 / 0,90'),
 ('4', 'Yıllık toplanabilir su', 'E = A·h/1000·e·η', f(E) + ' m³/yıl'),
 ('5', 'Gerekli sarnıç hacmi (PAİY m.57/7-a: yıllık suyun %6\'sı)', 'V = 0,06·E', f(Vmin) + ' m³'),
 ('6', 'Sarnıç iç taban alanı (iç 7,20 x 1,50 m)', 'Ad', f(Ad) + ' m²'),
 ('7', 'Gerekli faydalı su yüksekliği', 'h = V / Ad', f(Vmin / Ad) + ' m'),
 ('8', 'Seçilen faydalı su yüksekliği / faydalı hacim', 'Vs = Ad · 1,90', f(Vm) + ' m³'),
 ('9', 'Kontrol', 'Vs ≥ V', f'{f(Vm)} ≥ {f(Vmin)} UYGUN'),
 ('10', 'Tasarım yağış debisi (r = 0,030 l/s·m², C = 1,0)', 'Qr = A·r·C', f(Qr) + ' l/s'),
 ('11', 'YB başına debi (12 adet iniş) / mevcut Ø100 iniş', 'q = Qr / 12', f(qYB) + ' l/s ✓'),
 ('12', 'Ø110 PVC %0,5 kapasitesi (Manning n=0,010) / 2 YB yükü', 'Q = 5,2 l/s', '5,2 ≥ 3,55 ✓'),
 ('13', 'Ø160 PVC %0,5 kapasitesi / en yüklü hat (6 YB)', 'Q = 14,1 l/s', '14,1 ≥ 10,67 ✓'),
 ('14', 'F1 girdap filtre (DN200, çatı ≤ 1.500 m²) giriş debisi', 'Qr', f(Qr) + ' l/s ✓'),
 ('15', 'Taşma + F1 kirli su Ø200 PVC %1 kapasitesi', 'Q = 36,3 l/s', f'36,3 ≥ {f(Qr)} ✓'),
 ('16', 'Sulama pompası debisi (1 zon, 6 rotor x 0,25 m³/h)', 'Q', f(Q_P, 1) + ' m³/h'),
 ('17', 'Basma yüksekliği: Hgeo 3,9 + kayıp 6,0 + rotor basıncı 25', 'H = Hg + Hk + Hç', f(H_P, 1) + ' mSS → 36 mSS'),
 ('18', 'Pompa gücü (η = 0,40)', 'P = ρ·g·Q·H / η', f(Pw) + ' kW → 0,55 kW'),
 ('19', 'Membranlı tank (Z=20 /h, Pd/Pk = 3,5 / 4,9 bar)', 'V = 1000·Q/(4Z)·(Pk+1)/(Pk-Pd)', f(Vt, 0) + ' L → 80 L'),
]
y_after = TABLO(252400, -500600, 'YAĞMUR SUYU SARNICI HESABI (PAİY m.57/7-a, TS EN 16941-1, TS EN 12056-3)',
                [40, 520, 230, 200], R, h=9.5, rh=22, bold_rows=(5, 9), title_h=13)

EKP = [
 ('NO', 'ADI', 'AD.', 'ÖZELLİĞİ'),
 ('1', 'F1 GİRDAP (VORTEX) FİLTRE + BACASI', '1', 'DN200, elek 0,35 mm, çatı ≤ 1.500 m², 150x150 baca'),
 ('2', 'SAKİNLEŞTİRİCİ GİRİŞ', '1', 'DN150, sarnıç dibinde yukarı dönük'),
 ('3', 'YAĞMUR SUYU SARNICI', '1', 'Betonarme, iç 7,20x1,50 m, h faydalı 1,90 m, 20,5 m³'),
 ('4', 'TAŞMA SİFONU + KEMİRGEN KAPANI', '1', 'DN200, cazibe ile YSR rögarına'),
 ('5', 'YÜZER EMİŞ', '1', 'Şamandıralı, süzgeçli, DN32'),
 ('6', 'HİDROSTATİK SEVİYE SENSÖRÜ (LT)', '1', '4-20 mA, kuru çalışma koruması'),
 ('7', 'DALGIÇ SULAMA POMPASI (P)', '1', '1,5 m³/h - 36 mSS - 0,55 kW, paslanmaz'),
 ('8', 'MEMBRANLI TANK + PRESOSTAT + MANOMETRE', '1', '80 L, PN10, ön basınç 3,3 bar (VB içinde)'),
 ('9', 'Y TİPİ FİLTRE + KÜRESEL VANA + ÇEK VALF', '1', 'DN32, VB içinde'),
 ('10', 'YSR YAĞMUR SUYU BAĞLANTI RÖGARI', '1', '60x60, yağmur suyu kanalına gider'),
]
TABLO(253800, -500600, 'EKİPMAN LİSTESİ (YAĞMUR SUYU SARNICI)', [40, 300, 40, 300], EKP, h=9, rh=21, title_h=13)

NOT = [
 '1. Yağmur suyu yalnız B1, B2, B3 blok çatılarından toplanacak ve YALNIZCA bahçe sulamasında kullanılacaktır.',
 '2. Toplanan su içme, yemek, kişisel temizlik amacıyla kullanılmayacak; YSK hattı mor veya "İÇİLEMEZ" etiketli olacaktır.',
 '3. 12 adet YB, toprak altı PVC hatlarla F1 girdap filtreye, oradan sakinleştirici girişle sarnıca bağlanacaktır.',
 '4. Taşma, sarnıç içindeki taşma sifonundan F1 kirli suyu ile birlikte cazibeyle YSR üzerinden yağmur suyu kanalına gidecektir.',
 '5. Yağmur suyu hatları hiçbir şekilde pis su hattına, PB1-PB2-PB3 bacalarına bağlanmayacaktır.',
 '6. Arka cephe toplama hatları bahçe dolgusu içinde, tavan döşemesi su yalıtımına zarar vermeden döşenecektir.',
 '7. Sarnıca şebeke takviyesi yapılmayacak, sarnıç boşaldığında pompa seviye sensörüyle durdurulacaktır.',
 '8. Sarnıç kapakları kilitli olacak, kapaklarda "YAĞMUR SUYU - İÇİLEMEZ" uyarısı bulunacaktır.',
 '9. Yağmur suyu kanal bağlantı kotu belediyeden (İSKİ) alınarak YSR çıkışı buna göre düzenlenecektir.',
]
yN = -501000
T('PROJE NOTLARI', 253800, yN, 13, 'ROTAS-HESAP-BASLIK')
for i, s in enumerate(NOT):
    T(s, 253800, yN - 24 - i * 18, 8.6, 'ROTAS-HESAP-YAZI')

# ---------------------------------------------------------------- PRENSİP ŞEMASI + LEJANT (sol alt)
SX0, SY0 = 248000.0, -500990.0
T('YAĞMUR SUYU SARNICI PRENSİP ŞEMASI', SX0, SY0, 13, 'YS-YAZI')
by = SY0 - 70
for i, b in enumerate(('B3', 'B2', 'B1')):
    bx = SX0 + 40 + i * 120
    for k in range(4):
        x = bx + k * 18
        L((x, by), (x, by - 60), 'MTY-YAGMUR-BORUSU')
        C((x, by), 3, 'MTY-YAGMUR-BORUSU')
    T(f'{b} (4 YB)', bx + 27, by + 12, 8.5, 'YS-YAZI', 'BOTTOM_CENTER')
    L((bx, by - 60), (bx + 54, by - 60), 'MTY-YAGMUR-BORUSU')
    L((bx + 27, by - 60), (bx + 27, by - 90), 'MTY-YAGMUR-BORUSU')
L((SX0 + 67, by - 90), (SX0 + 307, by - 90), 'MTY-YAGMUR-BORUSU')
ARROW((SX0 + 307, by - 90), (SX0 + 360, by - 90), 'MTY-YAGMUR-BORUSU', 10)
GIRDAP((SX0 + 380, by - 90), 18); T('F1', SX0 + 380, by - 60, 9, 'YS-YAZI', 'BOTTOM_CENTER')
REC(SX0 + 440, by - 230, SX0 + 640, by - 100, 'YS-SARNIC', 1.2)
T('SARNIÇ 20,5 m³', SX0 + 540, by - 118, 9, 'YS-YAZI', 'MIDDLE_CENTER')
PL([(SX0 + 398, by - 90), (SX0 + 610, by - 90), (SX0 + 610, by - 215)], 'MTY-YAGMUR-BORUSU')
PL([(SX0 + 380, by - 108), (SX0 + 380, by - 270), (SX0 + 700, by - 270)], 'YS-TASMA')
PL([(SX0 + 625, by - 150), (SX0 + 660, by - 150), (SX0 + 660, by - 270)], 'YS-TASMA')
ARROW((SX0 + 700, by - 270), (SX0 + 740, by - 270), 'YS-TASMA', 10)
T('YSR → YAĞMUR SUYU KANALINA', SX0 + 745, by - 270, 8.5, 'YS-YAZI')
POMPA((SX0 + 470, by - 205), 10, math.pi / 2)
PL([(SX0 + 470, by - 195), (SX0 + 470, by - 75), (SX0 + 700, by - 75)], 'YS-KULLANMA')
TANK((SX0 + 560, by - 45), 14, 24); L((SX0 + 560, by - 57), (SX0 + 560, by - 75), 'YS-KULLANMA')
CEKVALF((SX0 + 520, by - 75), 0); VANA((SX0 + 640, by - 75), 0); MANOMETRE((SX0 + 600, by - 62))
ARROW((SX0 + 700, by - 75), (SX0 + 740, by - 75), 'YS-KULLANMA', 10)
T('YSK → BAHÇE SULAMA', SX0 + 745, by - 75, 8.5, 'YS-YAZI')
# lejant
LG = [('MTY-YAGMUR-BORUSU', 'Yağmur suyu toplama hattı (PVC, toprak altı, eğimli)'),
      ('YS-TASMA', 'Taşma / F1 kirli su hattı (cazibe, yağmur suyu kanalına)'),
      ('YS-KULLANMA', 'Sulama hattı YSK (PE100, İÇİLEMEZ)'),
      ('YS-ELEKTRIK', 'Seviye / kumanda kablosu')]
ly = by - 320
T('LEJANT', SX0, ly, 12, 'YS-YAZI')
for i, (lay, s) in enumerate(LG):
    yy = ly - 26 - i * 20
    PL([(SX0, yy), (SX0 + 80, yy)], lay, lts=0.5); T(s, SX0 + 95, yy, 8.5, 'YS-YAZI')
syms = [('vana', 'Küresel vana'), ('cek', 'Çek valf'), ('pompa', 'Dalgıç pompa'), ('tank', 'Membranlı tank'),
        ('girdap', 'F1 girdap filtre'), ('mano', 'Manometre'), ('yb', 'Yağmur iniş borusu (YB)')]
for i, (k, s) in enumerate(syms):
    xx = SX0 + 520 + (i % 2) * 300; yy = ly - 26 - (i // 2) * 24
    c = (xx, yy)
    {'vana': lambda: VANA(c, 0), 'cek': lambda: CEKVALF(c, 0), 'pompa': lambda: POMPA(c, 9),
     'tank': lambda: TANK(c, 10, 18), 'girdap': lambda: GIRDAP(c, 9), 'mano': lambda: MANOMETRE(c),
     'yb': lambda: (C(c, 7, 'MTY-YAGMUR-BORUSU'), C(c, 4, 'MTY-YAGMUR-BORUSU'))}[k]()
    T(s, xx + 20, yy, 8.5, 'YS-YAZI')

# =================================================================================
# 2) OTOPARK DUMAN TAHLİYESİ — havalandırma paftası 1. BODRUM KAT PLANI
# =================================================================================
A_OT = 870.20       # m² net (mimari)
H_OT = 3.54         # m kat yüksekliği (mimari kesit -3,54 ↔ ±0,00; en elverişsiz)
V_OT = A_OT * H_OT
N_HD = 10
Q_REQ = N_HD * V_OT
Q_G = 1550          # m³/h menfez başı
N_G1, N_G2 = 12, 8
Q1, Q2 = N_G1 * Q_G, N_G2 * Q_G
HK = 40             # kanal yüksekliği cm
VMAX = 8.0
def kanal_w(q):
    w = q / 3600 / VMAX / (HK / 100)
    return max(40, int(math.ceil(w * 10)) * 10)
def vel(q, w):
    return q / 3600 / (w / 100 * HK / 100)

DY = -498930.0      # ana kanal ekseni
O1 = (352568.0, -499331.5); O2 = (355473.1, -499228.3); O3 = (357529.9, -498848.4)  # mimari 80x120 tavanda boşluklar
segs = []   # (a, b, q)
def SEG(a, b, q): segs.append((a, b, q))
# DT-1
g1 = []
tee = 352330.0
# batı ana kanal: 351900, 352150 menfezleri ; lobe kolu tee'den kuzeye 3 menfez
for xa, xb, q in ((351820, 351900, 0), (351900, 352150, 1), (352150, tee, 2), (tee, O1[0], 5)):
    if q: SEG((xa, DY), (xb, DY), q * Q_G)
g1 += [(351900, DY), (352150, DY)]
for ya, yb, q in ((-498050, -498350, 1), (-498350, -498650, 2), (-498650, DY, 3)):
    SEG((tee, ya), (tee, yb), q * Q_G)
g1 += [(tee, -498050), (tee, -498350), (tee, -498650)]
# doğu ana kanal: 353050..354550 (4)
xs = [354550, 354050, 353550, 353050]
for i in range(4):
    xa = xs[i]; xb = xs[i + 1] if i < 3 else O1[0]
    SEG((xa, DY), (xb, DY), (i + 1) * Q_G)
g1 += [(x, DY) for x in xs]
SEG((O1[0], DY), (O1[0], O1[1] + 40), 9 * Q_G)            # ana kanaldan fana
# güney (cep) kolu: 3 menfez
for ya, yb, q in ((-500050, -499830, 1), (-499830, -499600, 2), (-499600, O1[1] - 40, 3)):
    SEG((O1[0], ya), (O1[0], yb), q * Q_G)
g1 += [(O1[0], -500050), (O1[0], -499830), (O1[0], -499600)]
# DT-2
g2 = []
SEG((355000, DY), (O2[0], DY), 1 * Q_G); g2 += [(355000, DY)]
xs2 = [357150, 356750, 356300, 355850]
for i in range(4):
    xa = xs2[i]; xb = xs2[i + 1] if i < 3 else O2[0]
    SEG((xa, DY), (xb, DY), (i + 1) * Q_G)
g2 += [(x, DY) for x in xs2]
SEG((O2[0], DY), (O2[0], O2[1] + 40), 5 * Q_G)
for ya, yb, q in ((-500050, -499800, 1), (-499800, -499550, 2), (-499550, O2[1] - 40, 3)):
    SEG((O2[0], ya), (O2[0], yb), q * Q_G)
g2 += [(O2[0], -500050), (O2[0], -499800), (O2[0], -499550)]
STUBS = [((351900, DY), (351860, DY)), ((tee, -498050), (tee, -498010)), ((354550, DY), (354590, DY)),
         ((O1[0], -500050), (O1[0], -500090)), ((355000, DY), (354960, DY)), ((357150, DY), (357190, DY)),
         ((O2[0], -500050), (O2[0], -500090))]
for a, b in STUBS: segs.append((a, b, -Q_G))
assert len(g1) == N_G1 and len(g2) == N_G2, (len(g1), len(g2))

# kanalları çift çizgi çiz
KL = 'MTY-DUMAN-EGZOZ-KANALI'
def duct(a, b, wcm, ext_a=0, ext_b=0):
    dx, dy = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(dx, dy); ux, uy = dx / Ln, dy / Ln
    nx, ny = -uy * wcm / 2, ux * wcm / 2
    a2 = (a[0] - ux * ext_a, a[1] - uy * ext_a); b2 = (b[0] + ux * ext_b, b[1] + uy * ext_b)
    L((a2[0] + nx, a2[1] + ny), (b2[0] + nx, b2[1] + ny), KL)
    L((a2[0] - nx, a2[1] - ny), (b2[0] - nx, b2[1] - ny), KL)
    return a2, b2, (nx, ny)
LBL = []
from shapely.geometry import Polygon as _Poly
from shapely.ops import unary_union as _uu
_rects = []
for a, b, q in segs:
    w_ = kanal_w(abs(q))
    dx, dy = b[0] - a[0], b[1] - a[1]; Ln = math.hypot(dx, dy); ux, uy = dx / Ln, dy / Ln
    nx, ny = -uy * w_ / 2, ux * w_ / 2
    _rects.append(_Poly([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]))
    if q > 0: LBL.append((a, b, q, w_))
_U = _uu(_rects)
for g in (_U.geoms if hasattr(_U, 'geoms') else [_U]):
    PL(list(g.exterior.coords), KL, True)
    for r_ in g.interiors: PL(list(r_.coords), KL, True)
# menfezler (tavan tipi duman egzoz menfezi 600x300, kanal altında)
for (x, y) in g1 + g2:
    horiz = abs(y - DY) < 1
    if horiz: x1, y1, x2, y2 = x - 30, y - 15, x + 30, y + 15
    else:     x1, y1, x2, y2 = x - 15, y - 30, x + 15, y + 30
    REC(x1, y1, x2, y2, 'MTY-DUMAN-MENFEZ'); L((x1, y1), (x2, y2), 'MTY-DUMAN-MENFEZ'); L((x1, y2), (x2, y1), 'MTY-DUMAN-MENFEZ')
# menfez etiketleri (bir kısmına, diğerleri aynı) — ana kanal menfezleri kanal üstüne
for (x, y) in g1 + g2:
    horiz = abs(y - DY) < 1
    if horiz: T('M 600x300 / 1550 m³/h', x, y - 60, 7.5, 'MTY-DUMAN-EGZOZ-CAP', 'TOP_CENTER')
    else: T('M 600x300 / 1550 m³/h', x + 40, y, 7.5, 'MTY-DUMAN-EGZOZ-CAP', 'MIDDLE_LEFT')
# kanal etiketleri (her segmentin ortası)
for a, b, q, w_ in LBL:
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    v = vel(q, w_)
    s1 = f'{q:,} m³/h'.replace(',', '.'); s2 = f'{w_ * 10}x{HK * 10} - v={f(v, 1)} m/s'
    if abs(a[1] - b[1]) < 1:
        T(s1, mx, my + w_ / 2 + 22, 9, 'MTY-DUMAN-EGZOZ-CAP', 'BOTTOM_CENTER'); T(s2, mx, my + w_ / 2 + 8, 8, 'MTY-DUMAN-EGZOZ-CAP', 'BOTTOM_CENTER')
    else:
        T(s1, mx - w_ / 2 - 22, my, 9, 'MTY-DUMAN-EGZOZ-CAP', 'BOTTOM_CENTER', 90); T(s2, mx - w_ / 2 - 8, my, 8, 'MTY-DUMAN-EGZOZ-CAP', 'BOTTOM_CENTER', 90)
# fanlar
for tag, O, q, kw in (('DT-1', O1, Q1, '5,5'), ('DT-2', O2, Q2, '4,0')):
    FAN(O, 38)
    ARROW((O[0] + 70, O[1] - 20), (O[0] + 70, O[1] + 40), 'MTY-DUMAN-FAN', 14)
    bx, by_ = O[0] + 110, O[1] + 70
    REC(bx, by_ - 70, bx + 360, by_ + 22, 'MTY-DUMAN-FAN')
    T(f'{tag} DUMAN EGZOZ FANI (F400/120 dk)', bx + 8, by_ + 8, 10, 'MTY-DUMAN-FAN')
    T(f'Q = {q:,} m³/h - 450 Pa - {kw} kW'.replace(',', '.'), bx + 8, by_ - 12, 9, 'MTY-DUMAN-FAN')
    T('Mimari 80x120 tavanda boşluktan dış havaya atar', bx + 8, by_ - 32, 8.5, 'MTY-DUMAN-FAN')
    T('çift devirli: normal havalandırma / yangın', bx + 8, by_ - 52, 8.5, 'MTY-DUMAN-FAN')
    L((O[0] + 38, O[1] + 10), (bx, by_ - 24), 'MTY-DUMAN-FAN')
# taze hava (doğal): rampa + H3 boşluğu
T('TAZE HAVA GİRİŞİ (DOĞAL) - mimari 80x120 boşluk', O3[0] - 70, O3[1] + 70, 9, 'MTY-TAZE-HAVA', 'BOTTOM_RIGHT')
ARROW((O3[0] - 75, O3[1] + 62), (O3[0] - 5, O3[1] + 5), 'MTY-TAZE-HAVA', 14)
for yy in (-499350, -499650, -499950):
    ARROW((357640, yy), (357480, yy), 'MTY-TAZE-HAVA', 16)
T('TAZE HAVA (RAMPADAN, DOĞAL)', 357360, -500010, 9, 'MTY-TAZE-HAVA', 'TOP_RIGHT')
T('OTOPARK DUMAN TAHLİYESİ: 10 HAVA DEĞİŞİMİ - 2 FAN (DT-1 + DT-2) - TOPLAM 31.000 m³/h', 352380, -497760, 15, 'MTY-DUMAN-EGZOZ-CAP')

# ---------------------------------------------------------------- DUMAN TAHLİYE HESABI (tablo)
v1 = Q1 / 3600 / 0.96; v2 = Q2 / 3600 / 0.96
A_TH = 3.60 * 2.20 + 0.96
v_th = (Q1 + Q2) / 3600 / A_TH
P1k = Q1 / 3600 * 450 / 0.55 / 1000; P2k = Q2 / 3600 * 450 / 0.55 / 1000
RD = [
 ('NO', 'KALEM', 'FORMÜL / KAYNAK', 'DEĞER'),
 ('1', 'Otopark net alanı (mimari 1. bodrum planı)', 'A', f(A_OT) + ' m²'),
 ('2', 'Kat yüksekliği (kesit: döşeme -3,54 ↔ zemin ±0,00, en elverişsiz)', 'H', f(H_OT) + ' m'),
 ('3', 'Otopark hacmi', 'V = A · H', f(V_OT, 1) + ' m³'),
 ('4', 'Duman tahliye hava değişim sayısı', 'n', '10 1/h'),
 ('5', 'Gerekli duman egzoz debisi', 'Q = n · V', f(Q_REQ, 0) + ' m³/h'),
 ('6', 'Seçilen toplam debi (20 menfez x 1.550 m³/h)', 'DT-1 + DT-2', f'{Q1 + Q2:,}'.replace(',', '.') + ' m³/h ≥ ' + f(Q_REQ, 0)),
 ('7', 'DT-1 fanı (batı + kuzey cep + güney cep, 12 menfez)', 'Q1', f'{Q1:,}'.replace(',', '.') + ' m³/h'),
 ('8', 'DT-2 fanı (doğu + güney cep, 8 menfez)', 'Q2', f'{Q2:,}'.replace(',', '.') + ' m³/h'),
 ('9', 'Menfez yüz hızı (600x300 = 0,18 m²)', 'v = 1550/3600/0,18', f(1550 / 3600 / 0.18) + ' m/s ≤ 3'),
 ('10', 'Kanal boyutlandırma (yükseklik 400 mm sabit)', 'v ≤ 8 m/s', 'plandaki etiketler'),
 ('11', 'Fan atış hızı - mimari 80x120 boşluk (0,96 m²)', 'v = Q / 0,96', f'{f(v1)} / {f(v2)} m/s'),
 ('12', 'Taze hava girişi: rampa 3,60x2,20 + 80x120 boşluk', 'At', f(A_TH) + ' m²'),
 ('13', 'Taze hava giriş hızı (doğal)', 'v = Q / At', f(v_th) + ' m/s'),
 ('14', 'Fan statik basıncı (kanal + menfez + atış, kabul)', 'Δp', '450 Pa'),
 ('15', 'Motor gücü (η = 0,55)', 'P = Q·Δp / η', f'{f(P1k, 1)} → 5,5 / {f(P2k, 1)} → 4,0 kW'),
]
TABLO(352080, -500380, 'OTOPARK DUMAN TAHLİYE HESABI (10 HAVA DEĞİŞİMİ)', [36, 470, 190, 220], RD, h=9, rh=21, bold_rows=(5, 6), title_h=13)
NOT2 = [
 '1. Duman tahliye fanları F400 (400 °C / 120 dk) sınıfında, TS EN 12101-3 belgeli olacaktır.',
 '2. Fanlar yangın algılama paneli ve otopark CO/duman dedektörlerinden otomatik devreye girecektir.',
 '3. Fanlar mimarinin gösterdiği 80x120 tavanda boşluklardan dış havaya atacak; atış ağzı ızgaralı olacaktır.',
 '4. Atış ağzı pencere, kapı ve sığınak taze hava alışından en az 3 m uzakta olacaktır.',
 '5. Kanallar en az 1,0 mm galvaniz sac, flanşlı ve sızdırmaz olacak; askılar çelik olacaktır.',
 '6. Kanal alt kotunda otopark net yüksekliği en az 2,20 m korunacaktır.',
 '7. Taze hava rampadan ve rampa yanındaki 80x120 boşluktan doğal olarak alınacaktır.',
 '8. Fan besleme kabloları yangına dayanıklı (FE180) olacak, ayrı jeneratör hattından beslenecektir.',
]
T('PROJE NOTLARI (DUMAN TAHLİYE)', 352080, -500960, 12, 'ROTAS-HESAP-BASLIK')
for i, s in enumerate(NOT2):
    T(s, 352080, -500985 - i * 18, 8.3, 'ROTAS-HESAP-YAZI')

# ---------------------------------------------------------------- HAVALANDIRMA ŞEMASI (duman tahliye)
X0, Y0 = 355150.0, -500680.0
T('OTOPARK DUMAN TAHLİYE ŞEMASI', X0, Y0, 14, 'MTY-HAVALANDIRMA-SEMA')
yz = Y0 - 100       # zemin (±0,00 / bahçe)
yt = Y0 - 260       # 1. bodrum tavanı
yb = Y0 - 480       # 1. bodrum döşeme
for yy, s in ((yz, 'ZEMİN KAT / BAHÇE  ±0,00'), (yt, ''), (yb, '1. BODRUM KAT (OTOPARK)  -3,54')):
    PL([(X0, yy), (X0 + 2750, yy)], 'MTY-HAVALANDIRMA-SEMA', w=2 if s else 0)
    if s: T(s, X0, yy + 8, 9, 'MTY-HAVALANDIRMA-SEMA', 'BOTTOM_LEFT')
T('H = 3,54 m', X0 + 2700, (yz + yb) / 2, 9, 'MTY-HAVALANDIRMA-SEMA', 'MIDDLE_RIGHT')
def sema_dt(xa, tag, ns, q, xb):
    # kanal (tek çizgi kalın) + menfezler
    yk = yt - 30
    PL([(xa, yk), (xb, yk)], KL, w=8)
    step = (xb - xa) / (ns + 1)
    for i in range(ns):
        x = xa + step * (i + 1)
        REC(x - 14, yk - 18, x + 14, yk - 8, 'MTY-DUMAN-MENFEZ')
        ARROW((x, yk - 60), (x, yk - 20), 'MTY-DUMAN-MENFEZ', 10)
    T(f'{ns} x MENFEZ 600x300 - 1.550 m³/h', (xa + xb) / 2, yk - 80, 8.5, 'MTY-DUMAN-EGZOZ-CAP', 'TOP_CENTER')
    fx_ = xb + 60
    PL([(xb, yk), (fx_ - 28, yk)], KL, w=8)
    FAN((fx_, yk), 28)
    PL([(fx_, yk + 28), (fx_, yz + 40)], KL, w=8)
    REC(fx_ - 40, yz - 6, fx_ + 40, yz + 6, 'MTY-HAVALANDIRMA-SEMA')
    T('80x120 TAVANDA BOŞLUK (mimari)', fx_ + 48, yz - 14, 8, 'MTY-HAVALANDIRMA-SEMA', 'TOP_LEFT')
    PL([(fx_ - 50, yz + 40), (fx_ + 50, yz + 40)], 'MTY-HAVALANDIRMA-SEMA', w=3)
    for k in range(5): L((fx_ - 40 + k * 20, yz + 44), (fx_ - 30 + k * 20, yz + 54), 'MTY-HAVALANDIRMA-SEMA')
    ARROW((fx_, yz + 60), (fx_, yz + 110), 'MTY-DUMAN-FAN', 14)
    T('DIŞ HAVAYA ATIŞ (ızgaralı)', fx_ + 12, yz + 95, 8.5, 'MTY-HAVALANDIRMA-SEMA')
    T(f'{tag}', fx_ - 36, yk + 36, 11, 'MTY-DUMAN-FAN', 'BOTTOM_RIGHT')
    T(f'{q:,} m³/h - 450 Pa'.replace(',', '.'), fx_ + 36, yk - 36, 8.5, 'MTY-DUMAN-FAN', 'TOP_LEFT')
sema_dt(X0 + 60, 'DT-1', 12, Q1, X0 + 1060)
sema_dt(X0 + 1300, 'DT-2', 8, Q2, X0 + 1980)
# taze hava (rampa)
xr = X0 + 2300
PL([(xr, yz), (xr + 300, yb)], 'MTY-HAVALANDIRMA-SEMA')
T('RAMPA', xr + 170, (yz + yb) / 2 + 20, 9, 'MTY-HAVALANDIRMA-SEMA')
for k in range(3):
    ARROW((xr + 40 + k * 90, yz - 40 - k * 75), (xr + 0 + k * 90 - 40, yz - 70 - k * 75), 'MTY-TAZE-HAVA', 12)
T('TAZE HAVA (DOĞAL) - RAMPA + 80x120 BOŞLUK', xr - 30, yz + 14, 8.5, 'MTY-TAZE-HAVA', 'BOTTOM_LEFT')
# kumanda
T('Kumanda: yangın algılama paneli / duman dedektörü → DT-1 + DT-2 yüksek devir; CO dedektörü → düşük devir', X0, yb - 30, 8.5, 'MTY-HAVALANDIRMA-SEMA')
# lejant
lyy = yb - 55
T('LEJANT', X0, lyy, 11, 'MTY-HAVALANDIRMA-SEMA')
items = [('fan', 'Duman egzoz fanı (F400/120 dk)'), ('m', 'Duman egzoz menfezi 600x300 (tavan)'),
         ('k', 'Duman egzoz kanalı (galvaniz, h=400 mm)'), ('t', 'Taze hava (doğal) akış yönü')]
for i, (k, s) in enumerate(items):
    xx = X0 + 30 + (i % 2) * 700; yy = lyy - 30 - (i // 2) * 30
    if k == 'fan': FAN((xx, yy), 14)
    elif k == 'm': REC(xx - 20, yy - 10, xx + 20, yy + 10, 'MTY-DUMAN-MENFEZ'); L((xx - 20, yy - 10), (xx + 20, yy + 10), 'MTY-DUMAN-MENFEZ'); L((xx - 20, yy + 10), (xx + 20, yy - 10), 'MTY-DUMAN-MENFEZ')
    elif k == 'k': L((xx - 25, yy - 8), (xx + 25, yy - 8), KL); L((xx - 25, yy + 8), (xx + 25, yy + 8), KL)
    else: ARROW((xx - 25, yy), (xx + 25, yy), 'MTY-TAZE-HAVA', 10)
    T(s, xx + 40, yy, 8.5, 'MTY-HAVALANDIRMA-SEMA')

doc.saveas(OUT)
print('OK', OUT)
print(f'E={E:.2f} Vmin={Vmin:.2f} Vm={Vm:.2f} Qr={Qr:.2f} q={qYB:.2f} H={H_P:.1f} P={Pw:.3f} Vt={Vt:.1f}')
print(f'V_OT={V_OT:.1f} Q_REQ={Q_REQ:.0f} Q1={Q1} Q2={Q2} v1={v1:.2f} v2={v2:.2f} vth={v_th:.2f} P1={P1k:.2f} P2={P2k:.2f}')
for a, b, q, w_ in LBL: print(q, w_, round(vel(q, w_), 2))
