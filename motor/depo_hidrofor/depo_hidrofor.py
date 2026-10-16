"""TOPRAK ALTI BETONARME KULLANMA SUYU DEPOSU + HİDROFOR GRUBU — plan (1/50), kesit A-A (1/50), hidrofor grubu
plan + görünüş (1/25), hesap tablosu ve cihaz listesi. Birim cm, saf geometri, ROTAS- katmanları (MTY bloğu yok).

Girdi: kullanıcının mimari ekran görüntüsü (16.10.2026): "KULLANMA SUYU DEPOSU B-B-02, 25,0 m², +20.90 (−5.85) /
+20.85 (−5.90)", sağdan şebeke girişi DN65, solda hidrofor odası. Vitrifiye adetleri kullanıcının sıhhi lejantından.
Bina: 2 kat, kat yüksekliği 6,00 m.
python3 depo_hidrofor.py CIKIS.dxf
"""
import math
import sys
import os

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK + '/deneme/kazan_dairesi')
import bloklar_onayli as BO   # noqa: E402  (onaylı saf geometri vana sembolleri)

# ------------------------------------------------------------------ tasarım verileri
IC_X, IC_Y = 500.0, 500.0          # depo iç ölçüsü (25 m²)
DUV = 40.0                         # betonarme perde (mimari 40)
PERDE = 20.0                       # göz ayırma perdesi
SIFIR = 2675.0                     # ±0.00 = +26.75 (mimari)
TABAN_K = -590.0                   # taban (döşeme) üst kotu −5.90 (+20.85) — mimari C BLOK SU DEPOSU
TAVAN_ALT = -250.0                 # depo tavanı alt kotu (tavan üstü −2.10 = +24.65, mimari kesit)
TAVAN_T = 40.0
RADYE = 60.0                       # radye alt −6.50 (+20.25)
SU_MAX = TABAN_K + 270.0           # maks. su (−3.20)
SU_MIN = TABAN_K + 40.0            # min. su (emiş üstü)
ARM = [('Duş teknesi', 8, 1.0), ('Termosifon', 16, 2.5), ('Eviye', 1, 0.5), ('Bulaşık makinesi', 1, 1.0),
       ('Klozet (rezervuarlı)', 20, 0.5), ('Lavabo', 24, 0.5), ('Engelli lavabo', 2, 0.5), ('Engelli klozet', 2, 0.5),
       ('Pisuar', 4, 0.25)]
KAT_SAY, KAT_H = 2, 6.0

L = dict(DUVAR='ROTAS-DEPO-BETONARME', TARAMA='ROTAS-DEPO-TARAMA', SU='ROTAS-DEPO-SU', TS='ROTAS-TEMIZSU-BORU',
         EMIS='ROTAS-HIDROFOR-EMIS', BASMA='ROTAS-HIDROFOR-BASMA', TASMA='ROTAS-DEPO-TASMA-BOSALTMA',
         CIHAZ='ROTAS-HIDROFOR-CIHAZ', YAZI='ROTAS-YAZI', OLCU='ROTAS-OLCU', BASLIK='ROTAS-PAFTA-BASLIK',
         CERCEVE='ROTAS-PAFTA-CERCEVE', TABLO='ROTAS-HESAP-TABLO', KOT='ROTAS-KOT', ESKI='ROTAS-MIMARI')
RENK = dict(DUVAR=8, TARAMA=8, SU=5, TS=5, EMIS=4, BASMA=1, TASMA=6, CIHAZ=3, YAZI=7, OLCU=8, BASLIK=7, CERCEVE=8,
            TABLO=7, KOT=2, ESKI=8)


# ------------------------------------------------------------------ hesap
def ks(k):
    """kot yazısı: −5.90 (+20.85)"""
    return ('%+.2f (%+.2f)' % (k / 100.0, (k + SIFIR) / 100.0)).replace('-', '−')


def hesap():
    T = sum(n * y for _, n, y in ARM)
    q = 0.25 * math.sqrt(T)
    Qh = q * 3.6
    stat = -TABAN_K / 100.0 + KAT_H * (KAT_SAY - 1) + 2.20           # hidrofor (−5.85) → üst kat duş başlığı (+6,00 + 2,20)
    kayip = 60 * 350 * 1.3 / 9807                         # kritik devre ≈ 60 m × 350 Pa/m × 1,3 (özel dirençler)
    akma, sayac, kol = 10.0, 5.0, 2.0
    Hm = stat + kayip + akma + sayac + kol
    Halt = math.ceil(Hm / 5) * 5
    Hust = Halt + 10
    Qsec = math.ceil(Qh)
    P = Qsec * Halt / (367 * 0.60)
    motor = next(m for m in (0.75, 1.1, 1.5, 2.2, 3.0, 4.0) if m >= P * 1.2)
    Vtank = 100
    goz = (IC_X - PERDE) / 2 / 100 * IC_Y / 100
    hsu = (SU_MAX - TABAN_K) / 100
    V = 2 * goz * hsu
    return dict(T=T, q=q, Qh=Qh, stat=stat, kayip=kayip, akma=akma, sayac=sayac, kol=kol, Hm=Hm, Halt=Halt, Hust=Hust,
                Qsec=Qsec, P=P, motor=motor, Vtank=Vtank, goz=goz, hsu=hsu, V=V, p0=0.9 * Halt / 10)


# ------------------------------------------------------------------ çizim yardımcıları
class C:
    def __init__(self, doc):
        self.doc = doc
        self.m = doc.modelspace()
        for k, n in L.items():
            if n not in doc.layers:
                doc.layers.add(n, color=RENK[k])
        if 'ROTAS' not in doc.styles:
            doc.styles.add('ROTAS', font='arial.ttf')
        BO.hazirla(doc)

    def pl(self, pts, k, kapali=False, w=0.0, lt=None):
        a = {'layer': L[k]}
        if lt:
            a['linetype'] = lt
        e = self.m.add_lwpolyline(pts, close=kapali, dxfattribs=a)
        if w:
            e.dxf.const_width = w
        return e

    def ln(self, a, b, k, lt=None):
        d = {'layer': L[k]}
        if lt:
            d['linetype'] = lt
        return self.m.add_line(a, b, dxfattribs=d)

    def tx(self, s, p, h, k='YAZI', al=TA.MIDDLE_LEFT, rot=0.0):
        return self.m.add_text(s, height=h, rotation=rot, dxfattribs={'layer': L[k], 'style': 'ROTAS'}).set_placement(p, align=al)

    def mtx(self, s, p, h, k='YAZI', w=None):
        e = self.m.add_mtext(s, dxfattribs={'layer': L[k], 'char_height': h, 'style': 'ROTAS', 'attachment_point': 1})
        e.dxf.insert = p
        if w:
            e.dxf.width = w
        return e

    def tara(self, pts, k='TARAMA', desen='ANSI31', olcek=8.0):
        h = self.m.add_hatch(dxfattribs={'layer': L[k]})
        h.set_pattern_fill(desen, scale=olcek)
        h.paths.add_polyline_path(pts, is_closed=True)

    def blok(self, ad, p, rot=0.0, s=1.0, k='CIHAZ'):
        return self.m.add_blockref(ad, p, dxfattribs={'layer': L[k], 'rotation': rot, 'xscale': s, 'yscale': s})

    def olcu(self, a, b, d, s=None, h=9.0):
        """basit ölçü: a-b doğrultusu, d kadar dışarıda"""
        ux, uy = b[0] - a[0], b[1] - a[1]
        Ln = math.hypot(ux, uy)
        ux, uy = ux / Ln, uy / Ln
        nx, ny = -uy, ux
        a2 = (a[0] + nx * d, a[1] + ny * d)
        b2 = (b[0] + nx * d, b[1] + ny * d)
        self.ln(a, (a2[0] + nx * 5, a2[1] + ny * 5), 'OLCU')
        self.ln(b, (b2[0] + nx * 5, b2[1] + ny * 5), 'OLCU')
        self.ln(a2, b2, 'OLCU')
        for p in (a2, b2):
            self.ln((p[0] - (ux + nx) * 4, p[1] - (uy + ny) * 4), (p[0] + (ux + nx) * 4, p[1] + (uy + ny) * 4), 'OLCU')
        ang = math.degrees(math.atan2(uy, ux))
        if ang > 90 or ang <= -90:
            ang += 180
        m = ((a2[0] + b2[0]) / 2 + nx * 3, (a2[1] + b2[1]) / 2 + ny * 3)
        self.tx(s or '%d' % round(Ln), m, h, 'OLCU', TA.BOTTOM_CENTER, ang)

    def kot(self, p, s, h=9.0):
        x, y = p
        self.pl([(x - 6, y + 6), (x, y), (x + 6, y + 6)], 'KOT')
        self.ln((x - 6, y + 6), (x + 70, y + 6), 'KOT')
        self.tx(s, (x + 2, y + 9), h, 'KOT', TA.BOTTOM_LEFT)

    def balon(self, n, p, hedef, r=9.0):
        self.ln(hedef, p, 'YAZI')
        self.m.add_circle(p, r, dxfattribs={'layer': L['YAZI']})
        self.tx(str(n), p, r, 'YAZI', TA.MIDDLE_CENTER)

    def boru(self, pts, k, etiket=None, h=7.0):
        self.pl(pts, k)
        if etiket:
            a, b = max(zip(pts[:-1], pts[1:]), key=lambda s: math.dist(*s))
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            if ang > 90 or ang <= -90:
                ang += 180
            nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
            self.tx(etiket, ((a[0] + b[0]) / 2 + nx * 4, (a[1] + b[1]) / 2 + ny * 4), h, k, TA.BOTTOM_CENTER, ang)

    def baslik(self, s, alt, p, w):
        self.tx(s, p, 22, 'BASLIK', TA.BOTTOM_LEFT)
        self.ln((p[0], p[1] - 5), (p[0] + w, p[1] - 5), 'BASLIK')
        self.tx(alt, (p[0], p[1] - 10), 12, 'BASLIK', TA.TOP_LEFT)


def pompa_gorunus(c, x, z, k='CIHAZ', S=1.0):
    """dikey çok kademeli pompa görünüşü: kaide 0..10, gövde, motor; emiş/basma flanşları z+25 (in-line)"""
    def P(pts):
        return [(x + (a - x) * S, z + (b - z) * S) for a, b in pts]
    _pl, _ln = c.pl, c.ln
    c = type('S', (), {'pl': lambda self, pts, k_, kap=False: _pl(P(pts), k_, kap),
                       'ln': lambda self, a, b, k_: _ln(P([a])[0], P([b])[0], k_)})()
    c.pl([(x - 22, z), (x + 22, z), (x + 22, z + 8), (x - 22, z + 8)], k, True)           # kaide
    c.pl([(x - 16, z + 8), (x + 16, z + 8), (x + 16, z + 40), (x - 16, z + 40)], k, True)  # pompa ayağı (in-line flanşlar)
    c.pl([(x - 10, z + 40), (x + 10, z + 40), (x + 10, z + 95), (x - 10, z + 95)], k, True)  # kademeler
    for zz in range(48, 95, 9):
        c.ln((x - 10, z + zz), (x + 10, z + zz), k)
    c.pl([(x - 13, z + 95), (x + 13, z + 95), (x + 13, z + 140), (x - 13, z + 140)], k, True)  # motor
    c.pl([(x - 9, z + 140), (x + 9, z + 140), (x + 9, z + 147), (x - 9, z + 147)], k, True)
    for zz in range(100, 140, 6):
        c.ln((x - 13, z + zz), (x - 9, z + zz), k)


# ------------------------------------------------------------------ PLAN 1/50
def plan(c, H, ox, oy):
    x0, y0 = ox, oy
    X1, Y1 = x0 + IC_X, y0 + IC_Y
    # betonarme perdeler (taramalı)
    dis = [(x0 - DUV, y0 - DUV), (X1 + DUV, y0 - DUV), (X1 + DUV, Y1 + DUV), (x0 - DUV, Y1 + DUV)]
    ic = [(x0, y0), (X1, y0), (X1, Y1), (x0, Y1)]
    c.pl(dis, 'DUVAR', True)
    c.pl(ic, 'DUVAR', True)
    for a, b in ((dis[0], ic[0]), (dis[1], ic[1]), (dis[2], ic[2]), (dis[3], ic[3])):
        pass
    h = c.m.add_hatch(dxfattribs={'layer': L['TARAMA']})
    h.set_pattern_fill('ANSI31', scale=8.0)
    h.paths.add_polyline_path(dis, is_closed=True, flags=1)
    h.paths.add_polyline_path(ic, is_closed=True, flags=16)
    # göz ayırma perdesi + alttan haberleşme vanası
    px = x0 + (IC_X - PERDE) / 2
    per = [(px, y0), (px + PERDE, y0), (px + PERDE, Y1), (px, Y1)]
    c.pl(per, 'DUVAR', True)
    c.tara(per)
    # su yalıtımı (iç yüzey) — kesikli
    c.pl([(x0 + 3, y0 + 3), (px - 3, y0 + 3), (px - 3, Y1 - 3), (x0 + 3, Y1 - 3)], 'SU', True, lt='DASHED')
    c.pl([(px + PERDE + 3, y0 + 3), (X1 - 3, y0 + 3), (X1 - 3, Y1 - 3), (px + PERDE + 3, Y1 - 3)], 'SU', True, lt='DASHED')
    c.tx('1. GÖZ', ((x0 + px) / 2, y0 + 250), 16, al=TA.MIDDLE_CENTER)
    c.tx('2. GÖZ', ((px + PERDE + X1) / 2, y0 + 250), 16, al=TA.MIDDLE_CENTER)
    gx1, gx2 = (x0 + px) / 2, (px + PERDE + X1) / 2
    for gx, nm in ((gx1, 'V≈%.0f m³' % (H['goz'] * H['hsu'])), (gx2, 'V≈%.0f m³' % (H['goz'] * H['hsu']))):
        c.tx(nm, (gx, y0 + 228), 10, al=TA.MIDDLE_CENTER)
    # menholler 70x70 (paslanmaz kapaklı) + merdiven
    for mx in (x0 + 20, px + PERDE + 20):
        m = [(mx, Y1 - 95), (mx + 70, Y1 - 95), (mx + 70, Y1 - 25), (mx, Y1 - 25)]
        c.pl(m, 'CIHAZ', True)
        c.ln(m[0], m[2], 'CIHAZ')
        c.ln(m[1], m[3], 'CIHAZ')
        for yy in range(int(Y1 - 90), int(Y1 - 25), 15):
            c.ln((mx + 10, yy), (mx + 60, yy), 'CIHAZ')
    c.tx('MENHOL 70x70 (sızdırmaz paslanmaz kapak) + paslanmaz merdiven', (x0 + 20, Y1 - 105), 7, al=TA.TOP_LEFT)
    # dip (emiş) çukurları 60x60x30
    cuk = []
    for cx in (x0 + 35, px + PERDE + 35):
        q = [(cx, y0 + 30), (cx + 60, y0 + 30), (cx + 60, y0 + 90), (cx, y0 + 90)]
        c.pl(q, 'CIHAZ', True, lt='DASHED')
        cuk.append((cx + 30, y0 + 60))
    c.tx('dip çukuru 60x60x30', (x0 + 100, y0 + 60), 7)
    # haberleşme (perde altı) vanalı geçiş DN80
    c.boru([(px - 40, y0 + 140), (px + PERDE + 40, y0 + 140)], 'EMIS')
    c.blok(BO.KELEBEK, (px - 25, y0 + 140), 0, 1.0, 'CIHAZ')
    c.tx('DN80 göz haberleşme (kapalı tutulur)', (px - 40, y0 + 150), 7, al=TA.BOTTOM_RIGHT)
    # şebeke girişi DN65 sağdan, her göze şamandıralı vana
    ys = Y1 - 50
    c.boru([(X1 + DUV + 220, ys), (X1 + DUV, ys)], 'TS', 'DN65 ŞEBEKEDEN')
    c.blok(BO.KURESEL, (X1 + DUV + 150, ys), 0, 1.0)
    c.blok(BO.PISLIK, (X1 + DUV + 115, ys), 0, 1.0)
    c.blok(BO.CEKVALF, (X1 + DUV + 80, ys), 180, 1.0)
    c.blok(BO.KURESEL, (X1 + DUV + 45, ys), 0, 1.0)
    c.boru([(X1, ys), (gx1 + 60, ys)], 'TS')
    for gx in (gx1 + 60, gx2 + 60):
        c.boru([(gx, ys), (gx, ys - 60)], 'TS', 'DN50')
        c.m.add_circle((gx, ys - 72), 12, dxfattribs={'layer': L['CIHAZ']})      # şamandıra
        c.tx('şamandıralı vana DN50', (gx + 15, ys - 72), 7)
    # emiş: her gözden dip çukuruna inen DN65 → sol duvardan su tutucu flanşla hidrofor odasına
    ye = y0 + 60
    c.boru([cuk[1], (cuk[1][0], y0 + 110), (x0 + 60, y0 + 110), (x0 + 60, ye)], 'EMIS')
    c.boru([cuk[0], (x0 - DUV, ye)], 'EMIS', 'DN65 EMİŞ')
    c.pl([(x0 - DUV + 6, ye - 12), (x0 - DUV + 6, ye + 12)], 'CIHAZ', w=3)       # su tutucu flanş
    c.tx('su tutucu flanşlı duvar geçişi', (x0 + 5, ye - 18), 6, al=TA.TOP_LEFT)
    for p in cuk:
        c.m.add_circle(p, 8, dxfattribs={'layer': L['CIHAZ']})                 # çan ağızlı emiş
    # taşma Ø100 (sifonlu) + dip boşaltma DN50 → hidrofor odasında drenaj çukuruna
    yt = Y1 - 160
    c.boru([(gx2 + 40, yt), (gx1, yt), (x0 - DUV, yt)], 'TASMA', 'Ø100 TAŞMA')
    c.boru([(cuk[0][0] - 20, y0 + 40), (x0 - DUV, y0 + 40)], 'TASMA', 'DN50 BOŞALTMA')
    c.boru([(cuk[1][0] + 20, y0 + 40), (cuk[1][0] + 20, y0 + 20), (x0 + 20, y0 + 20), (x0 + 20, y0 + 40)], 'TASMA')
    # havalık
    for gx in (gx1 - 60, gx2 - 60):
        c.m.add_circle((gx, Y1 - 60), 7, dxfattribs={'layer': L['CIHAZ']})
        c.tx('Ø100 havalık', (gx + 9, Y1 - 60), 6)
    # seviye
    c.m.add_circle((X1 - 40, y0 + 160), 6, dxfattribs={'layer': L['CIHAZ']})
    c.tx('seviye elektrodu', (X1 - 32, y0 + 160), 6)
    # ölçüler
    c.olcu((x0, Y1 + DUV), (X1, Y1 + DUV), 40, '%d' % IC_X)
    c.olcu((x0 - DUV, y0), (x0 - DUV, Y1), 40, '%d' % IC_Y)
    c.olcu((x0, y0 - DUV), (px, y0 - DUV), -40, '%d' % (px - x0))
    c.olcu((px + PERDE, y0 - DUV), (X1, y0 - DUV), -40, '%d' % (X1 - px - PERDE))
    c.kot((px + PERDE + 20, y0 + 195), 'Taban üst ' + ks(TABAN_K), 8)
    # kesit çizgisi A-A
    yk = y0 + 300
    for xx, yon in ((x0 - DUV - 60, 1), (X1 + DUV + 60, -1)):
        c.pl([(xx, yk), (xx + 40 * yon, yk)], 'BASLIK', w=3)
        c.tx('A', (xx, yk + 8), 14, 'BASLIK', TA.BOTTOM_CENTER)
    c.ln((x0 - DUV - 20, yk), (X1 + DUV + 20, yk), 'BASLIK', lt='DASHDOT')
    hid_plan(c, H, x0 - DUV, y0, ye, yt)
    c.baslik('KULLANMA SUYU DEPOSU PLANI', 'ÖLÇEK: 1/50   (toprak altı betonarme, 2 gözlü)', (x0 - DUV, y0 - DUV - 150), 600)
    return dict(px=px, ye=ye, yt=yt)


def hid_plan(c, H, xw, y0, ye, yt):
    """hidrofor odası (deponun solunda): emiş kollektörü, 2 pompa, basma kollektörü, membranlı tank, pano, drenaj çukuru"""
    xe = xw - 20
    # emiş kollektörü: duvardan sola
    c.boru([(xw, ye), (xw - 300, ye)], 'EMIS')
    c.blok(BO.KURESEL, (xw - 30, ye), 0, 0.8)
    c.blok(BO.PISLIK, (xw - 60, ye), 0, 0.8)
    pxs = [xw - 120, xw - 200]
    for i, px_ in enumerate(pxs):
        c.boru([(px_, ye), (px_, ye + 60)], 'EMIS')
        c.blok('ROTAS-POMPA', (px_, ye + 75), 90, 1.0)
        c.boru([(px_, ye + 88), (px_, ye + 150)], 'BASMA')
        c.blok(BO.CEKVALF, (px_, ye + 112), 90, 0.7)
        c.blok(BO.KURESEL, (px_, ye + 135), 90, 0.7)
        c.tx('P%d' % (i + 1), (px_ + 16, ye + 75), 8, 'CIHAZ')
    c.boru([(pxs[0] + 30, ye + 150), (pxs[-1] - 60, ye + 150), (pxs[-1] - 60, ye + 260)], 'BASMA', 'DN50 BASMA → BİNAYA')
    c.m.add_circle((pxs[0] + 30, ye + 180), 22, dxfattribs={'layer': L['CIHAZ']})
    c.boru([(pxs[0] + 30, ye + 150), (pxs[0] + 30, ye + 158)], 'BASMA')
    c.tx('%d lt' % H['Vtank'], (pxs[0] + 30, ye + 180), 7, 'CIHAZ', TA.MIDDLE_CENTER)
    pn = [(xw - 290, ye + 200), (xw - 230, ye + 200), (xw - 230, ye + 225), (xw - 290, ye + 225)]
    c.pl(pn, 'CIHAZ', True)
    c.tx('PANO', (xw - 260, ye + 212), 7, 'CIHAZ', TA.MIDDLE_CENTER)
    # drenaj çukuru + dalgıç pompa (taşma + boşaltma buraya)
    dc = [(xw - 95, yt - 30), (xw - 35, yt - 30), (xw - 35, yt + 30), (xw - 95, yt + 30)]
    c.pl(dc, 'CIHAZ', True)
    c.m.add_circle((xw - 65, yt), 12, dxfattribs={'layer': L['CIHAZ']})
    c.boru([(xw, yt), (xw - 35, yt)], 'TASMA')
    c.boru([(xw, y0 + 40), (xw - 65, y0 + 40), (xw - 65, yt - 30)], 'TASMA')
    c.boru([(xw - 95, yt), (xw - 160, yt), (xw - 160, yt + 80)], 'TASMA', 'basma → yağmur/pis su')
    c.tx('DRENAJ ÇUKURU 60x60x80', (xw - 95, yt + 36), 7, al=TA.BOTTOM_LEFT)
    c.tx('+ dalgıç pompa', (xw - 95, yt + 48), 7, al=TA.BOTTOM_LEFT)
    c.tx('HİDROFOR ODASI', (xw - 250, ye - 40), 12, al=TA.MIDDLE_LEFT)
    c.tx('(1 asıl + 1 yedek, frekans konvertörlü)', (xw - 250, ye - 56), 7, al=TA.MIDDLE_LEFT)


# ------------------------------------------------------------------ KESİT A-A 1/50
def kesit(c, H, ox, oy):
    """yatay x = plan x; düşey z: oy + (kot - TABAN_K)"""
    def Z(k):
        return oy + (k - TABAN_K)
    x0, X1 = ox, ox + IC_X
    px = x0 + (IC_X - PERDE) / 2
    taban_alt = Z(TABAN_K - RADYE)
    tavan_ust = Z(TAVAN_ALT + TAVAN_T)
    # dış kabuk
    dis = [(x0 - DUV, taban_alt), (X1 + DUV, taban_alt), (X1 + DUV, tavan_ust), (x0 - DUV, tavan_ust)]
    ic = [(x0, Z(TABAN_K)), (X1, Z(TABAN_K)), (X1, Z(TAVAN_ALT)), (x0, Z(TAVAN_ALT))]
    c.pl(dis, 'DUVAR', True)
    c.pl(ic, 'DUVAR', True)
    h = c.m.add_hatch(dxfattribs={'layer': L['TARAMA']})
    h.set_pattern_fill('ANSI31', scale=8.0)
    h.paths.add_polyline_path(dis, is_closed=True, flags=1)
    h.paths.add_polyline_path(ic, is_closed=True, flags=16)
    # grobeton + yalıtım + koruma
    c.pl([(x0 - DUV - 15, taban_alt - 10), (X1 + DUV + 15, taban_alt - 10), (X1 + DUV + 15, taban_alt), (x0 - DUV - 15, taban_alt)], 'DUVAR', True)
    c.tx('10 cm grobeton + bitümlü membran su yalıtımı (dış), drenaj', (X1 + DUV + 25, taban_alt - 5), 7)
    # perde
    per = [(px, Z(TABAN_K)), (px + PERDE, Z(TABAN_K)), (px + PERDE, Z(TAVAN_ALT)), (px, Z(TAVAN_ALT))]
    c.pl(per, 'DUVAR', True)
    c.tara(per)
    # su seviyeleri
    for xa, xb in ((x0, px), (px + PERDE, X1)):
        c.ln((xa, Z(SU_MAX)), (xb, Z(SU_MAX)), 'SU')
        for i in range(1, 4):
            c.ln((xa + 20 + i * 10, Z(SU_MAX) - i * 4), (xa + 50 - i * 2, Z(SU_MAX) - i * 4), 'SU')
        c.ln((xa, Z(SU_MIN)), (xb, Z(SU_MIN)), 'SU', lt='DASHED')
    c.tx('MAKS. SU', (x0 + 60, Z(SU_MAX) + 3), 8, 'SU', TA.BOTTOM_LEFT)
    c.tx('MİN. SU', (x0 + 60, Z(SU_MIN) + 3), 8, 'SU', TA.BOTTOM_LEFT)
    # dip çukurları
    for cx in (x0 + 35, px + PERDE + 35):
        c.pl([(cx, Z(TABAN_K)), (cx, Z(TABAN_K - 30)), (cx + 60, Z(TABAN_K - 30)), (cx + 60, Z(TABAN_K))], 'DUVAR')
    # menholler + merdiven
    for mx in (x0 + 20, px + PERDE + 20):
        c.pl([(mx, tavan_ust), (mx, tavan_ust + 15), (mx + 70, tavan_ust + 15), (mx + 70, tavan_ust)], 'CIHAZ')
        c.pl([(mx + 5, tavan_ust + 15), (mx + 65, tavan_ust + 15), (mx + 65, tavan_ust + 19), (mx + 5, tavan_ust + 19)], 'CIHAZ', True)
        for xx in (mx + 15, mx + 55):
            c.ln((xx, tavan_ust), (xx, Z(TABAN_K) + 10), 'CIHAZ')
        for zz in range(int(Z(TABAN_K) + 30), int(tavan_ust), 30):
            c.ln((mx + 15, zz), (mx + 55, zz), 'CIHAZ')
    c.tx('paslanmaz merdiven', (x0 + 95, Z(TABAN_K) + 150), 7)
    # şebeke girişi + şamandıralı vanalar
    zs = Z(TAVAN_ALT) - 20
    c.boru([(X1 + DUV + 150, zs), (x0 + 120, zs)], 'TS', 'DN65 ŞEBEKEDEN')
    for gx in ((x0 + px) / 2 + 60, (px + PERDE + X1) / 2 + 60):
        c.boru([(gx, zs), (gx, Z(SU_MAX) + 10)], 'TS')
        c.m.add_circle((gx + 18, Z(SU_MAX) + 2), 9, dxfattribs={'layer': L['CIHAZ']})
        c.ln((gx, Z(SU_MAX) + 10), (gx + 18, Z(SU_MAX) + 2), 'CIHAZ')
    c.tx('şamandıralı vana', ((px + PERDE + X1) / 2 + 90, Z(SU_MAX) + 6), 7)
    # emiş: çan ağızlı, dip çukurundan
    cx = x0 + 65
    ze = Z(TABAN_K - 15)
    c.boru([(cx, ze + 5), (cx, Z(TABAN_K) + 40), (x0 - DUV - 80, Z(TABAN_K) + 40)], 'EMIS', 'DN65 EMİŞ → HİDROFOR')
    c.pl([(cx - 12, ze), (cx + 12, ze), (cx + 5, ze + 8), (cx - 5, ze + 8)], 'CIHAZ', True)
    c.pl([(x0 - DUV + 6, Z(TABAN_K) + 28), (x0 - DUV + 6, Z(TABAN_K) + 52)], 'CIHAZ', w=3)
    # taşma (sifonlu, hava boşluklu) + boşaltma
    zt = Z(SU_MAX) + 15
    c.boru([(x0 + 30, zt), (x0 + 10, zt), (x0 + 10, zt - 25), (x0 - DUV - 80, zt - 25)], 'TASMA', 'Ø100 TAŞMA')
    c.boru([(x0 + 40, Z(TABAN_K - 25)), (x0 - DUV - 80, Z(TABAN_K - 25))], 'TASMA', 'DN50 DİP BOŞALTMA')
    # havalık
    hx = (px + PERDE + X1) / 2 - 60
    c.boru([(hx, Z(TAVAN_ALT)), (hx, tavan_ust + 60), (hx + 15, tavan_ust + 75)], 'CIHAZ')
    c.tx('Ø100 havalık (sineklikli, dış havaya)', (hx + 18, tavan_ust + 75), 7)
    # kotlar
    c.kot((X1 + DUV + 20, Z(TAVAN_ALT + TAVAN_T)), 'Depo tavanı üst ' + ks(TAVAN_ALT + TAVAN_T))
    c.kot((X1 + DUV + 20, Z(TAVAN_ALT)), 'Depo tavanı alt ' + ks(TAVAN_ALT))
    c.kot((X1 + DUV + 20, Z(SU_MAX)), 'Maks. su ' + ks(SU_MAX))
    c.kot((X1 + DUV + 20, Z(SU_MIN)), 'Min. su ' + ks(SU_MIN))
    c.kot((X1 + DUV + 20, Z(TABAN_K)), 'Taban üst ' + ks(TABAN_K))
    c.kot((X1 + DUV + 20, Z(TABAN_K - RADYE)), 'Radye alt ' + ks(TABAN_K - RADYE))
    # ölçüler
    c.olcu((X1 + DUV, Z(TABAN_K)), (X1 + DUV, Z(TAVAN_ALT)), -150, '%d' % (TAVAN_ALT - TABAN_K))
    c.olcu((X1 + DUV, Z(TABAN_K)), (X1 + DUV, Z(SU_MAX)), -110, '%d' % (SU_MAX - TABAN_K))
    c.olcu((x0, taban_alt - 10), (X1, taban_alt - 10), -40, '%d' % IC_X)
    c.mtx('NOTLAR:\\P'
          '1- Depo C30/37 su geçirimsiz betonarme olarak, statik projesine göre yapılacaktır.\\P'
          '2- Dış yüzeyde bitümlü membran su yalıtımı ve drenaj, iç yüzeyde içme suyuna uygun sertifikalı kaplama yapılacaktır.\\P'
          '3- Depo 2 gözlü yapılacak, gözler ayrı ayrı boşaltılıp temizlenebilecektir.\\P'
          '4- Taşma ve dip boşaltma hatları hava boşluklu olarak drenaj çukuruna bağlanacak, çukur dalgıç pompa ile boşaltılacaktır.\\P'
          '5- Duvar geçişleri su tutucu flanşlı yapılacaktır.\\P'
          '6- Menhol kapakları sızdırmaz, kilitli ve paslanmaz çelik olacaktır.',
          (x0 - DUV, taban_alt - 110), 8, w=700)
    c.baslik('KESİT A-A', 'ÖLÇEK: 1/50', (x0 - DUV, tavan_ust + 140), 400)


# ------------------------------------------------------------------ HİDROFOR GRUBU 1/25 (plan + görünüş, ölçek 2x çizim)
def hidrofor(c, H, ox, oy):
    """HİDROFOR GRUBU GÖRÜNÜŞÜ 1/25 — çizim 2 kat büyük (1/50 paftada 1/25 görünür)"""
    S = 2.0
    z0 = oy
    W = 900
    c.pl([(ox - 20, z0), (ox + W, z0)], 'DUVAR')
    c.tara([(ox - 20, z0 - 16), (ox + W, z0 - 16), (ox + W, z0), (ox - 20, z0)], desen='AR-CONC', olcek=0.8)
    xs = [ox + 300, ox + 520]
    ze = z0 + 25 * S                    # emiş ekseni (pompa emiş flanşı)
    zb = z0 + 330                       # basma kollektörü
    # depo duvarı (sol)
    c.pl([(ox - 80, z0), (ox - 20, z0), (ox - 20, z0 + 520), (ox - 80, z0 + 520)], 'DUVAR', True)
    c.tara([(ox - 80, z0), (ox - 20, z0), (ox - 20, z0 + 520), (ox - 80, z0 + 520)])
    c.tx('DEPO', (ox - 50, z0 + 540), 10, al=TA.BOTTOM_CENTER)
    c.boru([(ox - 20, ze), (xs[-1] - 70, ze)], 'EMIS', 'DN65 EMİŞ KOLLEKTÖRÜ')
    c.pl([(ox - 14, ze - 22), (ox - 14, ze + 22)], 'CIHAZ', w=4)
    c.blok(BO.KURESEL, (ox + 60, ze), 0, S)
    c.blok(BO.PISLIK, (ox + 150, ze), 0, S)
    for i, x in enumerate(xs):
        pompa_gorunus(c, x, z0, 'CIHAZ', S)
        # emiş: kollektörden pompaya küresel + esnek (kollektör pompa emiş flanşı hizasında)
        c.blok(BO.KURESEL, (x - 75, ze), 0, S * 0.8)
        c.blok(BO.ESNEK, (x - 45, ze), 0, S * 0.8)
        # basma: pompa çıkışı (sağ flanş) → yukarı: esnek, çek valf, küresel → kollektör
        bx = x + 75
        c.boru([(x + 16 * S, ze), (bx, ze), (bx, zb)], 'BASMA')
        c.blok(BO.ESNEK, (bx, ze + 60), 90, S * 0.8)
        c.blok(BO.CEKVALF, (bx, ze + 130), 90, S * 0.8)
        c.blok(BO.KURESEL, (bx, ze + 200), 90, S * 0.8)
        c.tx('P%d' % (i + 1), (x, z0 + 150 * S + 10), 14, 'CIHAZ', TA.BOTTOM_CENTER)
    xm = xs[-1] + 210
    c.boru([(xs[0] + 75, zb), (ox + W - 20, zb)], 'BASMA', 'DN50 BASMA KOLLEKTÖRÜ → BİNAYA')
    c.blok(BO.MANOMETRE, (xm - 40, zb), 0, S)
    c.ln((xm, zb), (xm, zb + 30), 'CIHAZ')
    c.m.add_circle((xm, zb + 42), 12, dxfattribs={'layer': L['CIHAZ']})
    c.tx('PT', (xm, zb + 42), 9, 'CIHAZ', TA.MIDDLE_CENTER)
    c.blok(BO.KURESEL, (ox + W - 60, zb), 0, S * 0.8)
    # membranlı tank
    tx_ = xm + 40
    c.boru([(tx_, zb), (tx_, z0 + 190)], 'BASMA')
    c.blok(BO.KURESEL, (tx_, z0 + 240), 90, S * 0.7)
    c.pl([(tx_ - 45, z0 + 20), (tx_ + 45, z0 + 20), (tx_ + 45, z0 + 150), (tx_ - 45, z0 + 150)], 'CIHAZ', True)
    c.m.add_arc((tx_, z0 + 150), 45, 0, 180, dxfattribs={'layer': L['CIHAZ']})
    for dx in (-30, 30):
        c.ln((tx_ + dx, z0), (tx_ + dx, z0 + 20), 'CIHAZ')
    c.tx('%d lt' % H['Vtank'], (tx_, z0 + 90), 12, 'CIHAZ', TA.MIDDLE_CENTER)
    # pano (duvarda)
    pnx = ox + 40
    c.pl([(pnx, z0 + 260), (pnx + 110, z0 + 260), (pnx + 110, z0 + 420), (pnx, z0 + 420)], 'CIHAZ', True)
    c.tx('FREKANS', (pnx + 55, z0 + 350), 10, 'CIHAZ', TA.MIDDLE_CENTER)
    c.tx('KONV. PANO', (pnx + 55, z0 + 330), 10, 'CIHAZ', TA.MIDDLE_CENTER)
    # balonlar (üst sırada, düzenli)
    zbal = z0 + 500
    bal = [(1, (xs[0] + 16 * S, z0 + 220), xs[0] - 20), (2, (ox + 60, ze + 12), ox + 60), (3, (ox + 150, ze + 12), ox + 150),
           (4, (xs[0] + 75, ze + 130), xs[0] + 110), (5, (xm - 40, zb + 30), xm - 60), (6, (tx_ + 45, z0 + 120), tx_ + 70),
           (7, (pnx + 110, z0 + 400), pnx + 200), (8, (xs[-1] - 45, ze + 12), xs[-1] - 45)]
    for n, h_, bx_ in bal:
        c.balon(n, (bx_, zbal if n % 2 else zbal + 40), h_, 11)
    c.kot((ox + W - 120, z0), ks(TABAN_K), 9)
    c.baslik('HİDROFOR GRUBU GÖRÜNÜŞÜ', 'ÖLÇEK: 1/25', (ox - 80, z0 + 640), 600)
    satir = [('NO', 'CİHAZ', 'ADET', 'TEKNİK ÖZELLİKLER'),
             ('1', 'Hidrofor pompası (dikey çok kademeli)', '2', 'Q=%d m³/h, H=%d mSS, %s kW, 1 asıl + 1 yedek' % (H['Qsec'], H['Halt'], ('%.1f' % H['motor']).replace('.', ','))),
             ('2', 'Küresel vana', '7', 'DN65 / DN40 / DN50, PN16'),
             ('3', 'Pislik tutucu', '1', 'DN65, PN16'),
             ('4', 'Çek valf', '2', 'DN40, PN16, yaylı'),
             ('5', 'Manometre + basınç transmitteri (PT)', '1+1', '0-10 bar, 4-20 mA'),
             ('6', 'Membranlı basınç tankı', '1', '%d lt, 10 bar, ön basınç %s bar' % (H['Vtank'], ('%.1f' % H['p0']).replace('.', ','))),
             ('7', 'Frekans konvertörlü kumanda panosu', '1', 'kuru çalışma + depo seviye korumalı'),
             ('8', 'Esnek bağlantı (kompansatör)', '4', 'DN65 / DN40'),
             ('9', 'Drenaj çukuru dalgıç pompası', '1', 'Q=5 m³/h, H=8 mSS, şamandıralı')]
    tablo(c, satir, (ox + W + 80, z0 + 600), [30, 250, 50, 330], 20, 9)


def tablo(c, satirlar, p, gen, sh, h=8.0):
    x0, y0 = p
    W = sum(gen)
    for i, s in enumerate(satirlar):
        y = y0 - i * sh
        c.ln((x0, y), (x0 + W, y), 'TABLO')
        xx = x0
        for j, v in enumerate(s):
            c.tx(str(v), (xx + 4, y - sh / 2), h, 'TABLO', TA.MIDDLE_LEFT)
            xx += gen[j]
    yb = y0 - len(satirlar) * sh
    c.ln((x0, yb), (x0 + W, yb), 'TABLO')
    xx = x0
    for g in [0] + gen:
        xx += g
        c.ln((xx, y0), (xx, yb), 'TABLO')
    return yb


def hesap_tablolari(c, H, ox, oy):
    c.baslik('HİDROFOR VE DEPO HESABI', 'TS 1258 yük birimi yöntemi (ROTAŞ HESAPLAR şablonu)', (ox, oy + 40), 500)
    s = [('ARMATÜR', 'ADET', 'YB', 'TOPLAM YB')]
    for a, n, y in ARM:
        s.append((a, n, ('%.2f' % y).replace('.', ','), ('%.2f' % (n * y)).replace('.', ',')))
    s.append(('TOPLAM', sum(n for _, n, _ in ARM), '', ('%.2f' % H['T']).replace('.', ',')))
    yb = tablo(c, s, (ox, oy), [220, 60, 60, 90], 16)
    f = lambda v, d=2: ('%.*f' % (d, v)).replace('.', ',')
    r = [('HESAP ADIMI', 'DEĞER', 'BİRİM'),
         ('Debi Q = 0,25 x √ΣYB = 0,25 x √%s' % f(H['T']), f(H['q'], 3), 'l/s'),
         ('Debi', f(H['Qh']), 'm³/h'),
         ('Statik yükseklik (hidrofor %s → %d. kat duş +%s; %d kat, kat yük. %s m)' % (f(TABAN_K / 100.0), KAT_SAY, f(KAT_H * (KAT_SAY - 1) + 2.2), KAT_SAY, f(KAT_H)), f(H['stat']), 'mSS'),
         ('Kritik devre boru kayıpları (≈60 m x 350 Pa/m x 1,3)', f(H['kayip']), 'mSS'),
         ('Akma basıncı (duş) + sayaç kaybı', f(H['akma'] + H['sayac'], 1), 'mSS'),
         ('Hidrofor kollektörü / emme kayıpları', f(H['kol'], 1), 'mSS'),
         ('Gerekli basma yüksekliği Hm', f(H['Hm'], 1), 'mSS'),
         ('HİDROFOR ALT ÇALIŞMA BASINCI (seçilen)', '%d' % H['Halt'], 'mSS'),
         ('HİDROFOR ÜST ÇALIŞMA BASINCI (frekans konvertörlü, +1 bar)', '%d' % H['Hust'], 'mSS'),
         ('SEÇİLEN HİDROFOR (1 asıl + 1 yedek)', '%d m³/h - %d mSS' % (H['Qsec'], H['Halt']), ''),
         ('Pompa motor gücü P = Q·H/(367·η), η = 0,60', '%s → %s kW' % (f(H['P']), f(H['motor'], 1)), 'pompa başına'),
         ('Membranlı tank (frekans konvertörlü sistem), ön basınç 0,9·Halt', '%d lt / %s bar' % (H['Vtank'], f(H['p0'], 1)), ''),
         ('Depo: 2 göz x (%s x %s) m x %s m faydalı su' % (f((IC_X - PERDE) / 200.0), f(IC_Y / 100.0), f(H['hsu'])), '≈ %d' % round(H['V']), 'm³'),
         ('Depo / debi (tam kapasitede çalışma süresi)', f(H['V'] / H['Qh'], 1), 'saat')]
    tablo(c, r, (ox, yb - 30), [330, 110, 60], 16)


def cerceve(c, x0, y0, x1, y1):
    c.pl([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'CERCEVE', True)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'DEPO_HIDROFOR.dxf'
    doc = ezdxf.new('R2018', setup=True)
    doc.header['$INSUNITS'] = 5
    doc.header['$LTSCALE'] = 10
    c = C(doc)
    H = hesap()
    plan(c, H, 0, 0)
    kesit(c, H, 900, 0)
    hidrofor(c, H, 0, -1150)
    hesap_tablolari(c, H, 1750, 600)
    cerceve(c, -480, -1300, 2380, 780)
    doc.saveas(out)
    print('yazıldı', out, 'YB', H['T'], 'Q', round(H['Qh'], 2), 'Hm', round(H['Hm'], 1), 'V', round(H['V'], 1))


if __name__ == '__main__':
    main()
