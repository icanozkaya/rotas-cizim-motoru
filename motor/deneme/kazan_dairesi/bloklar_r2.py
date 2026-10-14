# -*- coding: utf-8 -*-
"""Kazan dairesi prensip şeması R2: SAF GEOMETRİ semboller (MTY bloğu YOK — 14.10.2026 (B) talimatı).

Tüm semboller LINE / CIRCLE / ARC / LWPOLYLINE / HATCH ile ROTAS- adlı kendi bloklarımızdır.
Kural: hat içi (inline) sembollerde orijin boru ekseninde, boru +X yönünde; YARIM[ad] = boru kesme yarım boyu.
Branşman cihazlarında (termometre, manometre, emniyet ventili, purjör) orijin boru bağlantı noktası, cihaz +Y yönüne.
Ağızlı cihazların (denge kabı, hava/tortu ayırıcı) bağlantı noktaları AGIZ sözlüğündedir.
"""
import math

from ezdxf.enums import TextEntityAlignment as TA

import bloklar as BL0          # ROTAS-POMPA, ROTAS-KAZAN-DUVAR, ROTAS-SELENOID, ... (zaten saf geometri)

# hat içi semboller: boru kesme yarım boyu
YARIM = {'ROTAS-KURESEL-VANA': 10.5, 'ROTAS-KELEBEK-VANA': 10.5, 'ROTAS-CEKVALF': 11.5, 'ROTAS-PISLIK-TUTUCU': 10.5,
         'ROTAS-OTOMATIK-DOLUM': 10.5, 'ROTAS-KILITLI-VANA': 10.5, 'ROTAS-ESNEK-BAGLANTI': 11.0,
         'ROTAS-POMPA': 12.5, 'ROTAS-SELENOID': 10.5, 'ROTAS-REGULATOR': 10.5}
# ağızlı cihazlar (ölçek 1, yerel)
DENGE_SAG_X = 85.0             # denge kabı sağ ağızları x
DENGE_ALT_Y = -153.0           # denge kabı alt ağızları y (üst ağızlar y = 0)
HAVA_AYIRICI = (0.0, 50.0)     # giriş / çıkış ağzı x (y = 0)
TORTU = (0.0, 50.0)


def _a():
    return {'layer': '0'}


def _ln(b, p, q):
    b.add_line(p, q, dxfattribs=_a())


def _pl(b, pts, kapali=False):
    b.add_lwpolyline(pts, close=kapali, dxfattribs=_a())


def _ci(b, c, r):
    b.add_circle(c, r, dxfattribs=_a())


def _dolu(b, pts):
    h = b.add_hatch(dxfattribs=_a())
    h.paths.add_polyline_path(pts, is_closed=True)


def _dolu_daire(b, c, r, n=20):
    pts = [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    _dolu(b, pts)
    _ci(b, c, r)


def _papyon(b, l=20.0, h=12.0, dolu=(False, False)):
    for k, s in enumerate((-1, 1)):
        pts = [(s * l / 2, h / 2), (s * l / 2, -h / 2), (0, 0)]
        _pl(b, pts, True)
        if dolu[k]:
            _dolu(b, pts)


def _yaz(b, s, p, h):
    t = b.add_text(s, height=h, dxfattribs={'layer': '0', 'style': 'ROTAS'})
    t.set_placement(p, align=TA.MIDDLE_CENTER)


# ----------------------------------------------------------------------------- hat içi
def g_kuresel(b):              # küresel vana: papyon + ortada dolu küre + kol
    _papyon(b)
    _dolu_daire(b, (0, 0), 2.6)
    _ln(b, (0, 2.6), (0, 9)); _ln(b, (-4, 9), (4, 9))


def g_kelebek(b):              # kelebek vana: papyon + disk (düşey çizgi) + redüktör volanı
    _papyon(b)
    _ln(b, (0, -7.5), (0, 7.5))
    _ln(b, (0, 7.5), (0, 10)); _ci(b, (0, 13), 3)


def g_cekvalf(b):              # çek valf: papyon, akış yönündeki üçgen dolu + akış oku
    _papyon(b, 23.0, 12.0, (False, True))
    _ln(b, (-7, 9), (7, 9)); _pl(b, [(4, 11), (7, 9), (4, 7)])


def g_pislik(b):               # Y tipi pislik tutucu: gövde boru + 45° elek cebi
    _ln(b, (-10.5, 0), (10.5, 0))
    _pl(b, [(-5, 0), (1, -8), (7, -8), (1, 0)])
    _ln(b, (1, -8), (7, -8))
    for k in range(1, 3):
        _ln(b, (-5 + 2 * k, 0), (1 + 2 * k, -8))


def g_otomatik_dolum(b):       # otomatik dolum (basınç düşürücü) vanası: papyon + ayar oku + diyafram kutusu
    _papyon(b)
    _pl(b, [(-8, -7), (8, 7)]); _pl(b, [(4, 7), (8, 7), (8, 3)])
    _ln(b, (0, 0), (0, 8)); _pl(b, [(-5, 8), (5, 8), (5, 14), (-5, 14)], True)


def g_kilitli(b):              # kilitlenebilir (mühürlü) vana: papyon + küre + asma kilit
    _papyon(b)
    _dolu_daire(b, (0, 0), 2.6)
    _ln(b, (0, 2.6), (0, 8)); _pl(b, [(-4, 8), (4, 8), (4, 14), (-4, 14)], True)
    b.add_arc((0, 14), 2.6, 0, 180, dxfattribs=_a())


def g_esnek(b):                # esnek bağlantı: flanşlar + körük dalgası
    for x in (-11, 11):
        _ln(b, (x, -5), (x, 5))
    pts = [(-11, 0)] + [(-9 + 3 * i, 4 if i % 2 == 0 else -4) for i in range(7)] + [(11, 0)]
    _pl(b, pts)


# ----------------------------------------------------------------------------- branşman (+Y)
def g_emniyet(b):              # yaylı emniyet ventili (köşe tip), çıkış +X
    _ln(b, (0, 0), (0, 8))
    _pl(b, [(-5, 8), (5, 8), (0, 15)], True)
    _pl(b, [(0, 15), (8, 10), (8, 20)], True)
    _pl(b, [(0, 15), (0, 18), (-3, 19.5), (3, 21.5), (-3, 23.5), (3, 25.5), (0, 27)])


def g_manometre(b):            # manometre: sap + kadran + ibre
    _ln(b, (0, 0), (0, 8))
    _ci(b, (0, 15), 7)
    _ln(b, (0, 15), (4.5, 19.5))
    _dolu_daire(b, (0, 15), 1.0, 10)


def g_termometre(b):           # daldırma termometre: sap + hazne + kılcal tüp
    _ln(b, (0, 0), (0, 5))
    _dolu_daire(b, (0, 8.5), 3.5)
    _ln(b, (-1.6, 11.6), (-1.6, 24)); _ln(b, (1.6, 11.6), (1.6, 24))
    b.add_arc((0, 24), 1.6, 0, 180, dxfattribs=_a())
    for y in (15, 18, 21):
        _ln(b, (1.6, y), (3.6, y))


def g_ohac(b):                 # otomatik hava purjörü: sap + gövde + şamandıra + tahliye
    _ln(b, (0, 0), (0, 8))
    _pl(b, [(-5, 8), (5, 8), (5, 22), (-5, 22)], True)
    _ci(b, (0, 13), 3)
    _pl(b, [(-2, 22), (-2, 26), (2, 26), (2, 22)])


# ----------------------------------------------------------------------------- ağızlı cihazlar
def g_denge(b):                # denge kabı: düşey gövde, 4 ağız, üstte hava atıcı, altta çamur tahliye
    x0, x1, y0, y1 = 27.5, 57.5, -183.0, 30.0
    _ln(b, (x0, y0 + 15), (x0, y1 - 15)); _ln(b, (x1, y0 + 15), (x1, y1 - 15))
    b.add_arc((42.5, y1 - 15), 15, 0, 180, dxfattribs=_a()); b.add_arc((42.5, y0 + 15), 15, 180, 360, dxfattribs=_a())
    for (p, q) in (((0, 0), (x0, 0)), ((x1, 0), (DENGE_SAG_X, 0)), ((0, DENGE_ALT_Y), (x0, DENGE_ALT_Y)),
                   ((x1, DENGE_ALT_Y), (DENGE_SAG_X, DENGE_ALT_Y))):
        _ln(b, p, q)
    for y in (-50, -76.5, -103):                                  # iç ayırıcı perdeler
        _ln(b, (x0 + 4, y), (x1 - 4, y))
    _ln(b, (42.5, y1), (42.5, y1 + 6)); _pl(b, [(38.5, y1 + 6), (46.5, y1 + 6), (46.5, y1 + 16), (38.5, y1 + 16)], True)
    _ln(b, (42.5, y0), (42.5, y0 - 6))
    _pl(b, [(36.5, y0 - 6), (48.5, y0 - 6), (42.5, y0 - 12)], True); _pl(b, [(36.5, y0 - 18), (48.5, y0 - 18), (42.5, y0 - 12)], True)


def g_hava_ayirici(b):         # mikro kabarcık hava ayırıcı: ağızlar (0,0)-(50,0), gövde + iç ağ + purjör
    _ln(b, (0, 0), (10, 0)); _ln(b, (40, 0), (50, 0))
    _ci(b, (25, 0), 15)
    for d in (-8, 0, 8):
        _ln(b, (25 + d - 6, -6), (25 + d + 6, 6))
    _ln(b, (25, 15), (25, 21)); _pl(b, [(21, 21), (29, 21), (29, 31), (21, 31)], True)


def g_tortu(b):                # tortu ve pislik ayırıcı: ağızlar (0,0)-(50,0), düşey gövde, mıknatıs çubuğu, blöf vanası
    _ln(b, (0, 0), (13, 0)); _ln(b, (37, 0), (50, 0))
    _pl(b, [(13, 12), (37, 12), (37, -38), (13, -38)], True)
    _ln(b, (25, 8), (25, -30)); _ln(b, (23, -30), (27, -30))
    _ln(b, (25, -38), (25, -42))
    _pl(b, [(20, -42), (30, -42), (25, -47)], True); _pl(b, [(20, -52), (30, -52), (25, -47)], True)


def g_genlesme(b):             # membranlı kapalı genleşme tankı: orijin alt bağlantı, gövde +Y
    _ln(b, (0, 0), (0, 8))
    r = 24.0
    _ln(b, (-r, 8 + r), (-r, 78 - r)); _ln(b, (r, 8 + r), (r, 78 - r))
    b.add_arc((0, 8 + r), r, 180, 360, dxfattribs=_a()); b.add_arc((0, 78 - r), r, 0, 180, dxfattribs=_a())
    pts = [(-r + 4 * i, 43 + (3 if i % 2 else -3)) for i in range(13)]
    _pl(b, pts)                                                                    # membran
    _ln(b, (0, 78), (0, 84)); _ln(b, (-4, 84), (4, 84))                             # gaz şarj ventili


def g_baca_sapka(b):           # baca şapkası (baca ucu): orijin baca ekseni ucu
    _pl(b, [(-22, 6), (0, 22), (22, 6)])
    _ln(b, (-10, 0), (10, 0)); _ln(b, (-10, 0), (-10, 6)); _ln(b, (10, 0), (10, 6))


TANIM = {
    'ROTAS-KURESEL-VANA': g_kuresel, 'ROTAS-KELEBEK-VANA': g_kelebek, 'ROTAS-CEKVALF': g_cekvalf,
    'ROTAS-PISLIK-TUTUCU': g_pislik, 'ROTAS-OTOMATIK-DOLUM': g_otomatik_dolum, 'ROTAS-KILITLI-VANA': g_kilitli,
    'ROTAS-ESNEK-BAGLANTI': g_esnek, 'ROTAS-EMNIYET-VENTILI': g_emniyet, 'ROTAS-MANOMETRE': g_manometre,
    'ROTAS-TERMOMETRE': g_termometre, 'ROTAS-OHAC': g_ohac, 'ROTAS-DENGE-KABI': g_denge,
    'ROTAS-HAVA-AYIRICI': g_hava_ayirici, 'ROTAS-TORTU-AYIRICI': g_tortu, 'ROTAS-GENLESME-TANKI': g_genlesme,
    'ROTAS-BACA-SAPKA': g_baca_sapka,
}


def kollektor(doc, L, h=18.0):
    """kollektör gövdesi (yarım daire uçlu), orijin sol uç ekseni, boy L — boya göre ayrı blok"""
    ad = f'ROTAS-KOLLEKTOR-{int(round(L))}'
    if ad not in doc.blocks:
        b = doc.blocks.new(ad)
        r = h / 2
        b.add_lwpolyline([(0, -r, 0), (L, -r, 1), (L, r, 0), (0, r, 1)], format='xyb', close=True, dxfattribs=_a())
    return ad


def hazirla(doc):
    if 'ROTAS' not in doc.styles:
        doc.styles.add('ROTAS', font='arial.ttf')
    if 'ROTAS' not in doc.appids:
        doc.appids.new('ROTAS')
    BL0.kendi_bloklar(doc)          # ROTAS-POMPA, KAZAN-DUVAR, SELENOID, REGULATOR, GAZ-ALARM, BOYLER, NOTRALIZASYON, OK
    for ad, f in TANIM.items():
        if ad not in doc.blocks:
            f(doc.blocks.new(ad))
