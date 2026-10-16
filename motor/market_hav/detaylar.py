# -*- coding: utf-8 -*-
"""market_hav/detaylar.py — HAVALANDIRMA TESİSATI DETAYLARI (saf geometri, ROTAŞ standardı §5 detay listesi).

Her detay kendi çerçevesi içinde (kullanıcı kuralı: tüm detaylar kare içine alınır). Pafta 1/100 basılır;
detaylar gerçek ölçünün K katı çizilir (K=10 → ÖLÇEK 1/10, K=20 → 1/5, K=50 → 1/2).

API: detay_paftasi(msp, x0, y0, w, h)  — (x0, y0) pafta sol alt; dönüş: yazı kutuları listesi (çakışma kontrolü için)
"""
import math

from ezdxf.enums import TextEntityAlignment as TA

KAT = 'ROTAS-HAV-DETAY'
KAT_Y = 'ROTAS-HAV-DETAY-YAZI'
KAT_T = 'ROTAS-HAV-DETAY-TARAMA'
KAT_K = 'ROTAS-HAV-DETAY-KANAL'
KAT_I = 'ROTAS-HAV-DETAY-YALITIM'
KAT_C = 'ROTAS-HAV-CERCEVE'
KATMANLAR = {KAT: (7, 'Continuous'), KAT_Y: (7, 'Continuous'), KAT_T: (8, 'Continuous'),
             KAT_K: (20, 'Continuous'), KAT_I: (3, 'DASHED'), KAT_C: (7, 'Continuous')}
STIL = 'ROTAS'
AL = {'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER,
      'MR': TA.MIDDLE_RIGHT, 'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER, 'BR': TA.BOTTOM_RIGHT}
H_YAZI = 30.0          # detay yazı boyu (1/100 baskıda 3 mm)
H_BASLIK = 45.0


def genislik(s, h, w=0.85):
    try:
        from ezdxf.fonts import fonts
        f = fonts.make_font('arial.ttf', h, w)
        return f.text_width(str(s))
    except Exception:
        return len(str(s)) * h * 0.6 * w


class Cz:
    """Yerel çizici: (ox, oy) dünya orijini, k ölçek (gerçek cm → model)."""

    def __init__(self, m, ox, oy, k=10.0, kutular=None):
        self.m, self.ox, self.oy, self.k = m, ox, oy, k
        self.kutular = kutular if kutular is not None else []

    def p(self, x, y):
        return (self.ox + x * self.k, self.oy + y * self.k)

    def L(self, x0, y0, x1, y1, kat=KAT):
        return self.m.add_line(self.p(x0, y0), self.p(x1, y1), dxfattribs={'layer': kat})

    def P(self, pts, kat=KAT, kapali=False):
        return self.m.add_lwpolyline([self.p(x, y) for x, y in pts], close=kapali, dxfattribs={'layer': kat})

    def R(self, x0, y0, x1, y1, kat=KAT):
        return self.P([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], kat, True)

    def C(self, x, y, r, kat=KAT):
        return self.m.add_circle(self.p(x, y), r * self.k, dxfattribs={'layer': kat})

    def A(self, x, y, r, a0, a1, kat=KAT):
        return self.m.add_arc(self.p(x, y), r * self.k, a0, a1, dxfattribs={'layer': kat})

    def tara(self, pts, desen='ANSI31', olcek=None, kat=KAT_T):
        h = self.m.add_hatch(color=256, dxfattribs={'layer': kat})
        h.set_pattern_fill(desen, scale=olcek or max(2.0, self.k * 0.5))
        h.paths.add_polyline_path([self.p(x, y) for x, y in pts], is_closed=True)
        return h

    def taraR(self, x0, y0, x1, y1, desen='ANSI31', olcek=None):
        return self.tara([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], desen, olcek)

    def dolu(self, pts, kat=KAT):
        h = self.m.add_hatch(color=256, dxfattribs={'layer': kat})
        h.paths.add_polyline_path([self.p(x, y) for x, y in pts], is_closed=True)
        return h

    # yazı: konum yerel (gerçek cm), boy model biriminde
    def T(self, s, x, y, h=H_YAZI, al='BL', kat=KAT_Y, rot=0.0, w=0.85):
        X, Y = self.p(x, y)
        t = self.m.add_text(str(s), height=h, rotation=rot, dxfattribs={'layer': kat, 'style': STIL, 'width': w})
        t.set_placement((X, Y), align=AL[al])
        gw = genislik(s, h, w)
        ax = {'L': 0, 'C': 0.5, 'R': 1}[al[1]]
        ay = {'B': 0, 'M': 0.5, 'T': 1}[al[0]]
        if rot % 180 == 0:
            self.kutular.append((X - ax * gw, Y - ay * h, X + (1 - ax) * gw, Y + (1 - ay) * h, str(s)))
        else:
            self.kutular.append((X - (1 - ay) * h, Y - ax * gw, X + ay * h, Y + (1 - ax) * gw, str(s)))
        return t

    def etiket(self, s, px, py, tx, ty, h=H_YAZI, sag=True):
        """Kanca çizgili etiket: (px,py) gösterilen nokta, (tx,ty) yazı başlangıcı (yerel cm). Uçta nokta."""
        X0, Y0 = self.p(px, py)
        X1, Y1 = self.p(tx, ty)
        gw = genislik(s, h)
        self.m.add_line((X0, Y0), (X1, Y1), dxfattribs={'layer': KAT_Y})
        X2 = X1 + (gw + 10) * (1 if sag else -1)
        self.m.add_line((X1, Y1), (X2, Y1), dxfattribs={'layer': KAT_Y})
        hh = self.m.add_hatch(color=256, dxfattribs={'layer': KAT_Y})
        hh.paths.add_edge_path().add_arc((X0, Y0), 6, 0, 360)
        xs = X1 + 5 if sag else X2 + 5
        t = self.m.add_text(str(s), height=h, dxfattribs={'layer': KAT_Y, 'style': STIL, 'width': 0.85})
        t.set_placement((xs, Y1 + 6), align=TA.BOTTOM_LEFT)
        self.kutular.append((xs, Y1 + 6, xs + gw, Y1 + 6 + h, str(s)))

    def olcu(self, x0, y0, x1, y1, yazi, ofs=0.0, h=H_YAZI):
        """Basit ölçü çizgisi (yatay ya da düşey), eğik tik uçlu; ofs yerel cm."""
        if abs(y1 - y0) < 1e-6:            # yatay
            yy = y0 + ofs
            self.L(x0, yy, x1, yy, KAT_Y)
            for x in (x0, x1):
                self.L(x, y0, x, yy + (1.5 if ofs >= 0 else -1.5) * 10 / self.k, KAT_Y)
                X, Y = self.p(x, yy)
                self.m.add_line((X - 12, Y - 12), (X + 12, Y + 12), dxfattribs={'layer': KAT_Y})
            X, Y = self.p((x0 + x1) / 2, yy)
            t = self.m.add_text(yazi, height=h, dxfattribs={'layer': KAT_Y, 'style': STIL, 'width': 0.85})
            t.set_placement((X, Y + 8), align=TA.BOTTOM_CENTER)
            gw = genislik(yazi, h)
            self.kutular.append((X - gw / 2, Y + 8, X + gw / 2, Y + 8 + h, yazi))
        else:                               # düşey
            xx = x0 + ofs
            self.L(xx, y0, xx, y1, KAT_Y)
            for y in (y0, y1):
                self.L(x0, y, xx + (1.5 if ofs >= 0 else -1.5) * 10 / self.k, y, KAT_Y)
                X, Y = self.p(xx, y)
                self.m.add_line((X - 12, Y - 12), (X + 12, Y + 12), dxfattribs={'layer': KAT_Y})
            X, Y = self.p(xx, (y0 + y1) / 2)
            t = self.m.add_text(yazi, height=h, rotation=90, dxfattribs={'layer': KAT_Y, 'style': STIL, 'width': 0.85})
            t.set_placement((X - 8, Y), align=TA.BOTTOM_CENTER)
            gw = genislik(yazi, h)
            self.kutular.append((X - 8 - h, Y - gw / 2, X - 8, Y + gw / 2, yazi))

    def zikzak(self, x0, y0, x1, y1, n=8, gen=1.5, kat=KAT):
        """(x0,y0)-(x1,y1) doğrultusunda zikzak (brandi)."""
        dx, dy = (x1 - x0) / n, (y1 - y0) / n
        L = math.hypot(x1 - x0, y1 - y0) or 1
        nx, ny = -(y1 - y0) / L * gen, (x1 - x0) / L * gen
        pts = [(x0, y0)]
        for i in range(1, n):
            s = 1 if i % 2 else -1
            pts.append((x0 + dx * i + nx * s, y0 + dy * i + ny * s))
        pts.append((x1, y1))
        return self.P(pts, kat)


def _cerceve(m, x0, y0, x1, y1, no, baslik, olcek, kutular):
    m.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': KAT_C})
    m.add_line((x0, y1 - 110), (x1, y1 - 110), dxfattribs={'layer': KAT_C})
    s = f'DETAY-{no}  {baslik}'
    t = m.add_text(s, height=H_BASLIK, dxfattribs={'layer': KAT_Y, 'style': STIL, 'width': 0.85})
    t.set_placement((x0 + 40, y1 - 55), align=TA.MIDDLE_LEFT)
    gw = genislik(s, H_BASLIK)
    kutular.append((x0 + 40, y1 - 55 - H_BASLIK / 2, x0 + 40 + gw, y1 - 55 + H_BASLIK / 2, s))
    if not olcek:
        return
    o = f'ÖLÇEK : {olcek}'
    t = m.add_text(o, height=H_YAZI, dxfattribs={'layer': KAT_Y, 'style': STIL, 'width': 0.85})
    t.set_placement((x1 - 40, y1 - 55), align=TA.MIDDLE_RIGHT)
    gw2 = genislik(o, H_YAZI)
    kutular.append((x1 - 40 - gw2, y1 - 55 - H_YAZI / 2, x1 - 40, y1 - 55 + H_YAZI / 2, o))


# ----------------------------------------------------------------------------------------------- detaylar
def d1_aski(c):
    """Kanal askı detayı (kesit), K=10: 100x80 kanal, trapez askı."""
    # tavan / çatı aşığı (çelik profil) bandı
    c.R(-130, 95, 130, 110)
    c.taraR(-130, 95, 130, 110, 'ANSI31', 4)
    c.T('ÇELİK ÇATI AŞIĞI / TAVAN', -128, 112, al='BL')
    # dişli çubuklar
    for x in (-62, 62):
        c.L(x, 95, x, -52)
        c.R(x - 3, 92, x + 3, 95)              # kiriş kelepçesi
        for yy in (-46, -50):                  # somun + rondela
            c.R(x - 2.5, yy - 1.5, x + 2.5, yy + 1.5)
    # yalıtım (19 mm) ve kanal (100 x 80)
    c.R(-52, -42, 52, 42, KAT_I)
    c.R(-50, -40, 50, 40, KAT_K)
    c.L(-50, -40, 50, 40, KAT_K)               # sac kanal kesit işareti (çapraz)
    c.L(-50, 40, 50, -40, KAT_K)
    # titreşim kauçuğu + L profil (trapez)
    c.R(-60, -44, 60, -42)
    c.P([(-68, -44), (68, -44), (68, -48), (-64, -48), (-64, -52), (-68, -52)], kapali=True)
    c.etiket('KİRİŞ KELEPÇESİ', -62, 93, -120, 75, sag=True)
    c.etiket('M10 DİŞLİ ÇUBUK', 62, 60, 72, 75)
    c.etiket('GALVANİZ SAC KANAL', 20, 20, 72, 30)
    c.etiket('19 mm ELASTOMERİK KAUÇUK YALITIM', 51, -10, 72, 0)
    c.etiket('TİTREŞİM SÖNÜMLEYİCİ KAUÇUK', 30, -43, 72, -30)
    c.etiket('L 40x40x4 PROFİL', 0, -48, 20, -72)
    c.etiket('SOMUN + RONDELA', -62, -50, -125, -72, sag=True)
    c.olcu(-50, 40, 50, 40, 'B', ofs=12)
    c.olcu(-50, -40, -50, 40, 'H', ofs=-18)
    c.T('ASKI ARALIĞI EN FAZLA 2,40 m', 0, -100, al='BC')
    c.T('B > 1000 mm KANALLARDA L 50x50x5 PROFİL', 0, -112, al='BC')


def d2_flans(c):
    """Flanşlı kanal bağlantısı, K=20 (1/5): yan kesit + flanş çerçevesi görünüşü."""
    # yan kesit (üst duvar), kanal duvarları yatay
    for sgn in (1,):
        y = 30
        c.L(-60, y, -1.5, y, KAT_K)
        c.L(1.5, y, 60, y, KAT_K)
        # flanş profilleri 30 mm (3 cm) yukarı
        c.P([(-1.5, y), (-1.5, y + 3), (-4.5, y + 3), (-4.5, y + 0.4), (-9, y + 0.4), (-9, y)], kapali=True)
        c.P([(1.5, y), (1.5, y + 3), (4.5, y + 3), (4.5, y + 0.4), (9, y + 0.4), (9, y)], kapali=True)
        c.R(-1.5, y + 0.3, 1.5, y + 2.8)                 # conta
        c.R(-6, y + 3, 6, y + 3.6)                        # mandal / klips
        c.L(-0.4, y + 1.5, 0.4, y + 1.5)
    c.T('YAN KESİT', 0, 45, al='BC')
    c.etiket('30 mm FLANŞ PROFİLİ', -6, 32, -58, 40, sag=True)
    c.etiket('SIZDIRMAZLIK CONTASI', 0, 31.5, 14, 40)
    c.etiket('KANAL MANDALI (KLİPS)', 3, 33.5, 20, 24)
    c.etiket('GALVANİZ SAC KANAL', -40, 30, -58, 22, sag=True)
    # flanş çerçevesi görünüşü (köşe parçalı), 50x40 kanal ölçekli küçük
    x0, y0, x1, y1 = -40, -50, 40, 5
    c.R(x0, y0, x1, y1)
    c.R(x0 + 3, y0 + 3, x1 - 3, y1 - 3)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1)):
        c.P([(cx, cy), (cx + 8 * sx, cy), (cx + 8 * sx, cy + 3 * sy), (cx + 3 * sx, cy + 3 * sy),
             (cx + 3 * sx, cy + 8 * sy), (cx, cy + 8 * sy)], kapali=True)
        c.C(cx + 1.6 * sx, cy + 1.6 * sy, 0.5)
    for x in (-20, 0, 20):
        c.R(x - 1.5, y1 - 0.5, x + 1.5, y1 + 0.6)
        c.R(x - 1.5, y0 - 0.6, x + 1.5, y0 + 0.5)
    c.T('FLANŞ GÖRÜNÜŞÜ', 0, -58, al='TC')
    c.etiket('KÖŞE PARÇASI', x1 - 4, y1 - 4, 44, 12)
    c.etiket('M8 CIVATA-SOMUN', x1 - 1.6, y0 + 1.6, 44, -44)
    c.etiket('KLİPS ARALIĞI ≤ 150 mm', 20, y1 + 0.6, 44, -8)


def d3_kenet(c):
    """Kenet detayları, K=50 (1/2): Pittsburgh köşe kenedi, düz kenet, S sürgü, pim (perçin)."""
    # 1) köşe kenedi (Pittsburgh) — sol üst
    ox, oy = -8, 8
    c.P([(ox - 13, oy), (ox, oy), (ox, oy + 1.2), (ox - 1.6, oy + 1.2), (ox - 1.6, oy + 0.4), (ox - 0.4, oy + 0.4)], KAT_K)
    c.P([(ox - 0.8, oy + 12), (ox - 0.8, oy + 0.8), (ox - 1.2, oy + 0.8)], KAT_K)
    c.T('KÖŞE KENEDİ (PITTSBURGH)', ox - 6, oy - 2.5, al='TC')
    # 2) düz kenet — sağ üst
    ox, oy = 15, 12
    c.P([(ox - 11, oy), (ox, oy), (ox, oy + 1.4), (ox - 1.0, oy + 1.4), (ox - 1.0, oy + 0.4)], KAT_K)
    c.P([(ox + 11, oy + 0.8), (ox + 0.5, oy + 0.8), (ox + 0.5, oy + 1.9), (ox - 1.5, oy + 1.9), (ox - 1.5, oy - 0.5),
         (ox + 0.5, oy - 0.5)], KAT_K)
    c.T('DÜZ KENET', ox, oy - 2.5, al='TC')
    # 3) S sürgü — sol alt
    ox, oy = -15, -12
    c.L(ox - 11, oy, ox - 0.6, oy, KAT_K)
    c.L(ox + 0.6, oy, ox + 11, oy, KAT_K)
    c.P([(ox - 3, oy + 0.5), (ox + 3, oy + 0.5), (ox + 3, oy - 0.5), (ox - 3, oy - 0.5)], KAT, True)
    c.P([(ox - 3, oy + 0.5), (ox - 3, oy + 1.0), (ox + 3, oy + 1.0)], KAT)
    c.P([(ox + 3, oy - 0.5), (ox + 3, oy - 1.0), (ox - 3, oy - 1.0)], KAT)
    c.T('S SÜRGÜ BAĞLANTISI', ox, oy - 3, al='TC')
    # 4) pim (perçin) — sağ alt
    ox, oy = 15, -12
    c.L(ox - 11, oy + 0.4, ox + 3, oy + 0.4, KAT_K)
    c.L(ox - 3, oy - 0.4, ox + 11, oy - 0.4, KAT_K)
    for x in (ox - 1.5, ox + 1.5):
        c.R(x - 0.25, oy - 1.2, x + 0.25, oy + 1.2)
        c.P([(x - 0.6, oy + 1.2), (x + 0.6, oy + 1.2), (x, oy + 1.7)], KAT, True)
    c.T('PİM (POP PERÇİN) BAĞLANTISI', ox, oy - 3, al='TC')
    c.T('PİM ARALIĞI ≤ 150 mm', ox, oy - 4.5, al='TC')
    c.T('KENETLER SIZDIRMAZLIK MACUNU İLE KAPATILACAKTIR', 0, -22, al='TC')


def d4_duvar(c):
    """Kanalın duvardan geçişi (kesit), K=10."""
    # duvar 25 cm, kanal yüksekliği 80
    c.R(-12.5, -75, 12.5, 75)
    c.tara([(-12.5, -75), (12.5, -75), (12.5, -45), (-12.5, -45)], 'ANSI31', 5)
    c.tara([(-12.5, 45), (12.5, 45), (12.5, 75), (-12.5, 75)], 'ANSI31', 5)
    c.R(-12.5, -45, 12.5, 45, KAT)                      # kovan (boşluk)
    c.tara([(-12.5, -45), (12.5, -45), (12.5, -42), (-12.5, -42)], 'AR-SAND', 2.0)
    c.tara([(-12.5, 42), (12.5, 42), (12.5, 45), (-12.5, 45)], 'AR-SAND', 2.0)
    c.L(-90, 40, 90, 40, KAT_K)
    c.L(-90, -40, 90, -40, KAT_K)
    c.L(-90, 42, -14, 42, KAT_I)
    c.L(14, 42, 90, 42, KAT_I)
    c.L(-90, -42, -14, -42, KAT_I)
    c.L(14, -42, 90, -42, KAT_I)
    for x in (-15.5, 12.5):                              # kapatma çerçevesi
        c.R(x, 40, x + 3, 50)
        c.R(x, -50, x + 3, -40)
    c.etiket('DUVAR', 0, 60, 30, 78)
    c.etiket('ÇELİK KOVAN (25 mm BOŞLUK)', -12.5, 44, -88, 60, sag=True)
    c.etiket('MİNERAL YÜN DOLGU', 0, 43.5, 30, 62)
    c.etiket('KAPATMA ÇERÇEVESİ', 14, -45, 30, -62)
    c.etiket('GALVANİZ SAC KANAL', -60, 40, -88, 20, sag=True)
    c.etiket('KANAL YALITIMI', 60, -42, 30, -80)
    c.etiket('ELASTİK MASTİK', -12.5, -43.5, -88, -62, sag=True)
    c.T('YANGIN DUVARI GEÇİŞLERİNDE YANGIN DAMPERİ KONULACAKTIR', 0, -98, al='BC')


def d5_doseme(c):
    """Kanalın döşeme / çatıdan geçişi, K=10."""
    c.R(-90, -10, -45, 10)
    c.R(45, -10, 90, 10)
    c.taraR(-90, -10, -45, 10, 'ANSI31', 5)
    c.taraR(45, -10, 90, 10, 'ANSI31', 5)
    # bordür 15 cm
    c.R(-45, 10, -38, 25)
    c.R(38, 10, 45, 25)
    c.taraR(-45, 10, -38, 25, 'AR-CONC', 0.3)
    c.taraR(38, 10, 45, 25, 'AR-CONC', 0.3)
    # kanal düşey (60 genişlik)
    c.L(-30, -80, -30, 85, KAT_K)
    c.L(30, -80, 30, 85, KAT_K)
    c.L(-32, -80, -32, 85, KAT_I)
    c.L(32, -80, 32, 85, KAT_I)
    # dolgu
    c.tara([(-38, 10), (-32, 10), (-32, 25), (-38, 25)], 'AR-SAND', 2.0)
    c.tara([(32, 10), (38, 10), (38, 25), (32, 25)], 'AR-SAND', 2.0)
    c.tara([(-45, -10), (-32, -10), (-32, 10), (-45, 10)], 'AR-SAND', 2.0)
    c.tara([(32, -10), (45, -10), (45, 10), (32, 10)], 'AR-SAND', 2.0)
    # su yalıtım kapağı (flashing)
    c.P([(-50, 26), (-44, 26), (-44, 33), (-31, 33), (-31, 40)], KAT)
    c.P([(50, 26), (44, 26), (44, 33), (31, 33), (31, 40)], KAT)
    c.L(-90, 10.5, -45, 10.5, KAT_I)
    c.L(45, 10.5, 90, 10.5, KAT_I)
    c.etiket('DÖŞEME / ÇATI', -70, 0, -88, -30, sag=True)
    c.etiket('BETON BORDÜR h=15 cm', 41, 20, 48, 50)
    c.etiket('SU YALITIM KAPAĞI (FLASHING)', -40, 33, -88, 58, sag=True)
    c.etiket('MİNERAL YÜN DOLGU', 38, 0, 48, -30)
    c.etiket('GALVANİZ SAC KANAL', 30, -60, 48, -60)
    c.etiket('SU YALITIMI', 70, 10.5, 48, 30)


def d6_menfez(c):
    """Yuvarlak kanal menfezi montajı (kanal altı), K=10."""
    # kanal 60x45 kesit
    c.R(-30, 10, 30, 55, KAT_K)
    c.R(-32, 8, 32, 57, KAT_I)
    c.L(-30, 10, 30, 55, KAT_K)
    c.L(-30, 55, 30, 10, KAT_K)
    # yaka Ø50 (boğaz) + damper
    c.L(-25, 10, -25, -8)
    c.L(25, 10, 25, -8)
    c.L(-26, 10, -26, -8, KAT_I)
    c.L(26, 10, 26, -8, KAT_I)
    c.L(-22, 4, 22, -2)                                 # kelebek damper kanadı
    c.C(0, 1, 1.2)
    c.L(25, 1, 33, 1)
    c.R(33, -1, 38, 3)
    # menfez gövdesi (swirl) Ø70
    c.P([(-25, -8), (-35, -14), (-35, -17), (35, -17), (35, -14), (25, -8)], kapali=True)
    for x in range(-30, 31, 6):
        c.L(x, -17, x + 3, -14)
    # tavan seviyesi yok (açık tavan) — kanal altı montaj
    c.etiket('GALVANİZ SAC KANAL', 20, 45, 45, 60)
    c.etiket('YAKA (BOĞAZ) – PERÇİN + MASTİK', -25, 5, -90, 20, sag=True)
    c.etiket('KELEBEK AYAR DAMPERİ', -10, 2.5, -90, -2, sag=True)
    c.etiket('AYAR KOLU', 36, 3, 45, 20)
    c.etiket('YUVARLAK KANAL MENFEZİ', 30, -16, 45, -30)
    c.T('PLANDA: KANAL ALTI YUVARLAK MENFEZ (2850 m³/h)', 0, -62, al='BC')
    c.T('MENFEZLER BALANS AYARI YAPILARAK DEVREYE ALINACAKTIR', 0, -74, al='BC')


def d7_damper(c):
    """Hacim ayar damperi (karşıt kanatlı), K=10: görünüş + kesit."""
    x0, y0, x1, y1 = -80, -45, 10, 45
    c.R(x0, y0, x1, y1)
    c.R(x0 + 4, y0 + 4, x1 - 4, y1 - 4)
    n = 5
    hh = (y1 - y0 - 8) / n
    for i in range(n):
        yc = y0 + 4 + hh * (i + 0.5)
        c.R(x0 + 4, yc - hh * 0.35, x1 - 4, yc + hh * 0.35)
        c.C(x1 - 4, yc, 0.8)
    c.L(x1, -20, x1 + 8, -20)
    c.A(x1 + 8, -20, 10, -40, 40)                       # kadran
    c.L(x1 + 8, -20, x1 + 17, -14)
    c.T('GÖRÜNÜŞ', (x0 + x1) / 2, y0 - 6, al='TC')
    # kesit: karşıt kanatlar
    kx = 50
    c.L(kx - 10, y0, kx - 10, y1)
    c.L(kx + 10, y0, kx + 10, y1)
    for i in range(n):
        yc = y0 + 4 + hh * (i + 0.5)
        a = math.radians(35 if i % 2 else -35)
        dx, dy = 8 * math.cos(a), 8 * math.sin(a)
        c.L(kx - dx, yc - dy, kx + dx, yc + dy)
        c.C(kx, yc, 0.8)
    c.T('KESİT', kx, y0 - 6, al='TC')
    c.etiket('FLANŞLI ÇERÇEVE', x0 + 2, y1 - 2, -80, 62)
    c.etiket('KARŞIT HAREKETLİ KANATLAR', kx + 6, 20, 20, 62)
    c.etiket('KİLİTLİ AYAR KOLU', x1 + 15, -16, 20, -62)
    c.etiket('MİL + BURÇ', x1 - 4, y0 + 4 + hh * 0.5, -80, -62)


def d8_panjur(c):
    """Dış hava menfezi (yağmur panjuru), K=10: kesit."""
    c.R(-12.5, -80, 12.5, -40)
    c.R(-12.5, 40, 12.5, 80)
    c.taraR(-12.5, -80, 12.5, -40, 'ANSI31', 5)
    c.taraR(-12.5, 40, 12.5, 80, 'ANSI31', 5)
    # kasa
    c.R(-14.5, -40, -12.5, 40)
    c.R(12.5, -40, 14.5, 40)
    # kanatlar 45°
    for y in range(-34, 37, 8):
        c.L(-11, y - 4, 11, y + 4)
    c.L(-6, -40, -6, 40, KAT_I)                         # kuş teli
    # damlalık
    c.P([(-14.5, -40), (-24, -42), (-24, -44), (-14.5, -42)], kapali=True)
    # iç kanal bağlantısı
    c.L(14.5, 38, 60, 38, KAT_K)
    c.L(14.5, -38, 60, -38, KAT_K)
    c.R(14.5, 36, 17, 41)
    c.R(14.5, -41, 17, -36)
    c.T('DIŞ', -50, 0, al='MC')
    c.T('İÇ', 70, 0, al='MC')
    c.etiket('YAĞMUR PANJURU KANATLARI (45°)', 0, 10, -88, 62, sag=True)
    c.etiket('KUŞ TELİ (10x10 mm)', -6, -20, -88, -62, sag=True)
    c.etiket('DAMLALIK', -22, -43, -88, -85, sag=True)
    c.etiket('FLANŞLI KANAL BAĞLANTISI', 16, 39, 25, 62)
    c.etiket('DUVAR', 0, 60, 25, 85)
    c.T('PANJUR EFEKTİF HIZI ≤ 2,5 m/s', 30, -85, al='BL')


def d9_santral(c):
    """Klima santrali – kanal esnek bağlantısı ve kaide, K=10."""
    # santral gövdesi
    c.R(-90, -40, -20, 60)
    c.T('PAKET TİP', -55, 15, al='MC')
    c.T('KLİMA SANTRALİ', -55, 5, al='MC')
    # çıkış ağzı + brandi + kanal
    c.R(-20, 20, -16, 55)
    c.zikzak(-16, 55, 0, 55, 8, 1.2)
    c.zikzak(-16, 20, 0, 20, 8, 1.2)
    c.R(0, 18, 3, 57)
    c.L(3, 55, 80, 55, KAT_K)
    c.L(3, 20, 80, 20, KAT_K)
    c.L(3, 57, 80, 57, KAT_I)
    c.L(3, 18, 80, 18, KAT_I)
    # kaide + takoz
    for x in (-82, -28):
        c.R(x - 4, -46, x + 4, -40)
        c.dolu([(x - 4, -46), (x + 4, -46), (x + 4, -43), (x - 4, -43)])
    c.R(-95, -60, -15, -46)
    c.taraR(-95, -60, -15, -46, 'AR-CONC', 0.3)
    c.L(-110, -60, 90, -60)
    c.etiket('BRANDİ (ESNEK BAĞLANTI) 150 mm', -8, 55, -20, 80)
    c.etiket('FLANŞ', 1.5, 20, 25, 0)
    c.etiket('YALITIMLI GALVANİZ KANAL', 50, 55, 25, 72)
    c.etiket('TİTREŞİM TAKOZU', -28, -43, 0, -30)
    c.etiket('BETON KAİDE h=15 cm', -20, -55, 0, -52)
    c.T('TAZE HAVA VE ATIŞ AĞIZLARINA KUŞ TELİ TAKILACAKTIR', -10, -82, al='BC')


SAC_TABLO = [('KANAL BÜYÜK KENARI (mm)', 'SAC KALINLIĞI (mm)', 'BAĞLANTI'),
             ('≤ 300', '0,50', 'S SÜRGÜ / DÜZ KENET'),
             ('301 – 750', '0,60', 'S SÜRGÜ / FLANŞ'),
             ('751 – 1200', '0,80', '30 mm FLANŞ'),
             ('1201 – 2000', '1,00', '30 mm FLANŞ + TAKVİYE'),
             ('> 2000', '1,20', '40 mm FLANŞ + TAKVİYE')]


def d10_tablo(c):
    """Galvaniz sac kalınlık tablosu (TS EN 1505 / 1507 uyarınca) — K=1 model birimi."""
    sut = [0, 1050, 1800, 2700]
    sat_h = 140
    y = 0
    for i, row in enumerate(SAC_TABLO):
        c.R(sut[0], y - sat_h, sut[-1], y)
        for j, s in enumerate(row):
            if j:
                c.L(sut[j], y - sat_h, sut[j], y)
            c.T(s, (sut[j] + sut[j + 1]) / 2, y - sat_h / 2, h=32 if i else 30, al='MC')
        y -= sat_h
    c.T('KANAL KÖŞELERİ PITTSBURGH KENETLE BİRLEŞTİRİLECEKTİR.', 0, y - 80, h=30, al='TL')
    c.T('KANALLAR TS EN 1505 / TS EN 1507 UYARINCA İMAL EDİLECEKTİR.', 0, y - 140, h=30, al='TL')
    c.T('B > 1000 mm KANALLARDA ÇAPRAZ BÜKÜM (KIRIM) YAPILACAKTIR.', 0, y - 200, h=30, al='TL')


DETAYLAR = [
    (d1_aski, 'KANAL ASKI DETAYI', 10, '1/10'),
    (d2_flans, 'FLANŞLI KANAL BAĞLANTISI', 20, '1/5'),
    (d3_kenet, 'KÖŞE / DÜZ KENET VE PİM DETAYLARI', 50, '1/2'),
    (d4_duvar, 'KANAL DUVAR GEÇİŞ DETAYI', 10, '1/10'),
    (d5_doseme, 'KANAL DÖŞEME / ÇATI GEÇİŞ DETAYI', 10, '1/10'),
    (d6_menfez, 'MENFEZ MONTAJ DETAYI', 10, '1/10'),
    (d7_damper, 'HACİM AYAR DAMPERİ', 10, '1/10'),
    (d8_panjur, 'DIŞ HAVA MENFEZİ (PANJUR)', 10, '1/10'),
    (d9_santral, 'KLİMA SANTRALİ BAĞLANTI DETAYI', 10, '1/10'),
    (d10_tablo, 'KANAL SAC KALINLIK TABLOSU', 1, None),
]


def katmanlar(doc):
    for ad, (renk, lt) in KATMANLAR.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk, linetype=lt if lt in doc.linetypes else 'Continuous')


def detay_paftasi(msp, x0, y0, sutun=4, hucre_w=3300.0, hucre_h=3000.0, ara=100.0):
    """Detayları sutun × satır ızgarada çizer; (x0, y0) ızgara sol alt. Dönüş: yazı kutuları."""
    kutular = []
    satir = math.ceil(len(DETAYLAR) / sutun)
    for i, (f, baslik, k, olcek) in enumerate(DETAYLAR):
        r, s = divmod(i, sutun)
        cx0 = x0 + s * (hucre_w + ara)
        cy0 = y0 + (satir - 1 - r) * (hucre_h + ara)
        _cerceve(msp, cx0, cy0, cx0 + hucre_w, cy0 + hucre_h, i + 1, baslik, olcek, kutular)
        if f is d10_tablo:
            c = Cz(msp, cx0 + 300, cy0 + hucre_h - 350, 1.0, kutular)
        else:
            c = Cz(msp, cx0 + hucre_w / 2, cy0 + (hucre_h - 110) / 2, k, kutular)
        f(c)
    return kutular
