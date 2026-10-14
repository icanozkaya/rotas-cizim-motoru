"""sihhi2 — kolon şeması / temel planı sembolleri (SAF GEOMETRİ, MTY bloğu YOK; README 14.10 B).

Görünüş kullanıcının new_block şemasındaki KOLON bloklarından ölçüldü (kutuphane/arastirma/kolon_semasi_ref/*.jpg,
referans/sihhi/29_*.png): armatürler yan görünüş, döşeme çizgisine (y=0) oturur; blok orijini armatür ekseni.
Blok içi varlıklar katman 0, renkler sabit (armatür cyan 4, aksesuar sarı 2, vana kırmızı 1 + koyu dolgu).
Blok adlarında 'SEMA' geçer: kontrolör plan süzgeç / kolon sayımına karışmaz.

Bağlantı yükseklikleri (y, cm) — boru motoru bunları kullanır:
    BAG[tip] = (sıcak_y, soğuk_y)  (None: o hat yok)
"""
import math

import ezdxf
from ezdxf.enums import TextEntityAlignment

ETIKET_H = 10.0
YAZI_STIL = 'ROTAS-YAZI'
YAZI_EN = 0.8

# armatür bağlantı noktası: (dx, y) sıcak / soğuk; tek hatlılarda soğuk dx = 0
BAG = {
    'LV': ((-5, 100), (5, 100)),
    'DUS': ((-5, 106), (5, 106)),
    'EV': ((-5, 112), (5, 112)),
    'WC': (None, (0, 116)),
    'CM': (None, (0, 88)),
    'BM': (None, (0, 88)),
    'YS': (None, None),
}
# armatür yarı genişliği (etiket / yerleşim için)
# sembol dolgusu: renk 8 (orta gri 128: siyah ekranda da beyaz kâğıtta da DOLU görünür; 250 siyah ekranda kaybolur)
DOLGU = 8
YARI = {'LV': 32, 'DUS': 42, 'EV': 50, 'WC': 24, 'CM': 31, 'BM': 31, 'YS': 13}


def _pl(b, pts, renk, kapali=False, **kw):
    a = {'color': renk}
    a.update(kw)
    return b.add_lwpolyline(pts, close=kapali, dxfattribs=a)


def _ln(b, p, q, renk):
    return b.add_line(p, q, dxfattribs={'color': renk})


def _dolgu(b, pts, renk):
    h = b.add_hatch(color=renk)
    h.paths.add_polyline_path(pts, is_closed=True)
    return h


def _daire_dolgu(b, c, r, renk):
    h = b.add_hatch(color=renk)
    h.paths.add_edge_path().add_arc(c, r, 0, 360)
    return h


def _attdef(b, tag, p, h=ETIKET_H, renk=256, hiza='L'):
    a = b.add_attdef(tag, p, dxfattribs={'height': h, 'style': YAZI_STIL, 'width': YAZI_EN, 'color': renk})
    if hiza == 'R':
        a.set_placement(p, align=TextEntityAlignment.BOTTOM_RIGHT)
    elif hiza == 'C':
        a.set_placement(p, align=TextEntityAlignment.MIDDLE_CENTER)
    return a


# ====================================================================== ARMATÜRLER (yan görünüş)
def _lavabo(B):
    b = B.new('ROTAS-SEMA-LAVABO')
    C, Y = 4, 2
    # tezgah / hazne
    _pl(b, [(-30, 86), (30, 86), (30, 82), (-30, 82)], C, True)
    b.add_arc((0, 98), 30.0, 220, 320, dxfattribs={'color': C})       # hazne alt yayı
    _ln(b, (-30, 82), (-23, 79), C)
    _ln(b, (30, 82), (23, 79), C)
    # konsollar
    for s in (-1, 1):
        _pl(b, [(s * 27, 82), (s * 27, 74), (s * 24, 74)], C)
    # sifon + gider (döşemeye)
    _pl(b, [(-3, 70), (-3, 58), (3, 58), (3, 70)], C)
    b.add_arc((0, 52), 6.0, 180, 360, dxfattribs={'color': C})
    _ln(b, (-6, 52), (-6, 58), C)
    _ln(b, (6, 52), (6, 58), C)
    _ln(b, (-2.5, 46), (-2.5, 0), C)
    _ln(b, (2.5, 46), (2.5, 0), C)
    # batarya (lavabo bataryası, iki giriş)
    _pl(b, [(-6, 86), (-6, 92), (6, 92), (6, 86)], C)
    _pl(b, [(-1.5, 92), (-1.5, 98), (8, 104), (16, 104)], C)
    for s in (-1, 1):
        _ln(b, (s * 5, 92), (s * 5, 100), C)
        b.add_circle((s * 5, 100), 1.6, dxfattribs={'color': C})
    # ayna (sarı)
    _pl(b, [(-28, 192), (28, 192), (28, 236), (-28, 236)], Y, True)
    _ln(b, (-10, 202), (6, 224), Y)
    _ln(b, (-4, 200), (12, 222), Y)
    for x in (-24, 24):
        b.add_circle((x, 236), 1.8, dxfattribs={'color': Y})
        b.add_circle((x, 192), 1.8, dxfattribs={'color': Y})


def _klozet(B):
    b = B.new('ROTAS-SEMA-KLOZET')
    C, Y = 4, 2
    # klozet gövdesi (yan görünüş, döşemeye oturur)
    _pl(b, [(-12, 0), (12, 0), (14, 14), (22, 30), (22, 38), (-22, 38), (-22, 30), (-14, 14)], Y, True)
    _ln(b, (-24, 41), (24, 41), Y)
    _ln(b, (-24, 38), (-24, 41), Y)
    _ln(b, (24, 38), (24, 41), Y)
    # bağlantı borusu + gömme rezervuar
    _ln(b, (-3, 41), (-3, 72), Y)
    _ln(b, (3, 41), (3, 72), Y)
    _pl(b, [(-22, 72), (22, 72), (22, 114), (-22, 114)], Y, True)
    _pl(b, [(-15, 90), (15, 90), (15, 108), (-15, 108)], Y, True)       # basma plakası
    _pl(b, [(-4, 99), (4, 99), (4, 104), (-4, 104)], Y, True)
    # ara musluk (soğuk girişi)
    _pl(b, [(-3, 114), (3, 114), (3, 118), (-3, 118)], C, True)


def _dus(B):
    """duş teknesi + duvar bataryası (bağlantı +106) + el duşu askısı; sembolün tamamı +124'ün altında
    (dağıtım hattı +130 ve MB etiketleri kesilmez)"""
    b = B.new('ROTAS-SEMA-DUS')
    C, Y = 4, 2
    # duş teknesi
    _pl(b, [(-42, 0), (42, 0), (42, 7), (-42, 7)], C, True)
    _ln(b, (-38, 7), (-38, 10), C)
    _ln(b, (38, 7), (38, 10), C)
    # duvar bataryası (iki giriş üstte +106)
    _pl(b, [(-12, 92), (12, 92), (12, 98), (-12, 98)], C, True)
    for s_ in (-1, 1):
        b.add_circle((s_ * 9, 88), 3.0, dxfattribs={'color': C})
        _ln(b, (s_ * 5, 98), (s_ * 5, 106), C)
    _pl(b, [(-2, 92), (-2, 86), (6, 80), (14, 80)], C)                 # el duşu çıkışı
    # el duşu askısı + başlık (batarya hizasında, yukarı çıkmaz)
    _ln(b, (24, 74), (24, 116), C)
    _pl(b, [(20, 116), (32, 122), (34, 118), (22, 112)], C, True)
    _pl(b, [(14, 80), (18, 70), (24, 74)], C)                           # hortum
    # sabunluk (sarı)
    _pl(b, [(-36, 104), (-22, 104), (-22, 114), (-36, 114)], Y, True)
    _ln(b, (-36, 107), (-22, 107), Y)


def _eviye(B):
    b = B.new('ROTAS-SEMA-EVIYE')
    C, Y = 4, 2
    # tezgah altı dolabı + tezgah
    _pl(b, [(-46, 0), (46, 0), (46, 84), (-46, 84)], Y, True)
    _ln(b, (0, 6), (0, 78), Y)
    for x in (-40, 6):
        _pl(b, [(x, 6), (x + 34, 6), (x + 34, 78), (x, 78)], Y, True)
    _pl(b, [(-52, 84), (52, 84), (52, 90), (-52, 90)], C, True)
    # hazne (kesit) + gider
    _pl(b, [(-26, 90), (-24, 70), (24, 70), (26, 90)], C)
    _ln(b, (-2, 70), (-2, 52), C)
    _ln(b, (2, 70), (2, 52), C)
    b.add_arc((0, 48), 4.0, 180, 360, dxfattribs={'color': C})
    # batarya
    _pl(b, [(-6, 90), (-6, 96), (6, 96), (6, 90)], C)
    _pl(b, [(0, 96), (0, 108), (10, 114), (18, 106)], C)
    for s in (-1, 1):
        _ln(b, (s * 5, 96), (s * 5, 112), C)
        b.add_circle((s * 5, 112), 1.6, dxfattribs={'color': C})


def _makine(B, ad, camasir):
    b = B.new(ad)
    C, Y = 4, 2
    _pl(b, [(-30, 0), (30, 0), (30, 84), (-30, 84)], C, True)
    _pl(b, [(-28, 2), (28, 2), (28, 82), (-28, 82)], C, True)
    _ln(b, (-28, 70), (28, 70), C)
    _pl(b, [(-24, 73), (-6, 73), (-6, 79), (-24, 79)], C, True)
    for x in (10, 14, 18, 22):
        _ln(b, (x, 73), (x, 79), Y)
    if camasir:
        b.add_circle((0, 36), 20.0, dxfattribs={'color': Y})
        b.add_circle((0, 36), 15.0, dxfattribs={'color': Y})
        _pl(b, [(-24, 28), (-21, 28), (-21, 44), (-24, 44)], Y, True)
    else:
        _pl(b, [(-24, 8), (24, 8), (24, 64), (-24, 64)], Y, True)
        _ln(b, (-24, 58), (24, 58), Y)
        _pl(b, [(-8, 60), (8, 60), (8, 62), (-8, 62)], Y, True)
    # ara musluk (üstte)
    _pl(b, [(-3, 84), (3, 84), (3, 88), (-3, 88)], C, True)


def _suzgec(B):
    b = B.new('ROTAS-SEMA-YER-SUZGECI')
    Y = 2
    _pl(b, [(-12, 0), (12, 0), (12, 6), (-12, 6)], Y, True)
    _pl(b, [(-9, 6), (9, 6), (9, 9), (-9, 9)], Y, True)
    for x in (-6, -2, 2, 6):
        _ln(b, (x, 0), (x, 6), Y)


def _kombi(B):
    b = B.new('ROTAS-SEMA-KOMBI')
    C, R = 4, 1
    _pl(b, [(-20, 0), (20, 0), (20, 66), (-20, 66)], C, True)
    _pl(b, [(-17, 3), (17, 3), (17, 63), (-17, 63)], C, True)
    _pl(b, [(-8, 50), (8, 50), (8, 56), (-8, 56)], C, True)
    for x in (-9, 0, 9):
        b.add_circle((x, 12), 3.5, dxfattribs={'color': C})
        _ln(b, (x, 12), (x + 2, 14), C)
    # bağlantı ağızları (alt): sıcak -5, soğuk +5
    for x in (-5, 5):
        _ln(b, (x, 0), (x, -4), R)


# ====================================================================== VANA / SAYAÇ (hat üstü, yatay, 20 genişlik)
def _vana_govde(b):
    _dolgu(b, [(-10, -5), (0, 0), (-10, 5)], DOLGU)
    _dolgu(b, [(10, -5), (0, 0), (10, 5)], DOLGU)
    _pl(b, [(-10, -5), (10, 5), (10, -5), (-10, 5)], 1, True)


def _vanalar(B):
    b = B.new('ROTAS-SEMA-KURESEL-VANA')
    _vana_govde(b)
    _pl(b, [(-4, 7), (-4, 12), (4, 12)], 1)                 # kol
    b = B.new('ROTAS-SEMA-CEKVALF')
    _vana_govde(b)
    _daire_dolgu(b, (-6, 8), 1.4, 1)
    _pl(b, [(-4, 8), (6, 8)], 1)
    _pl(b, [(3, 10), (6, 8), (3, 6)], 1)
    b = B.new('ROTAS-SEMA-PISLIK-TUTUCU')
    _vana_govde(b)
    _ln(b, (0, 0), (5, 9), 1)
    _ln(b, (3, 10), (7, 8), 1)
    b = B.new('ROTAS-SEMA-SU-SAYACI')
    _dolgu(b, [(-7, -7), (7, -7), (7, 7), (-7, 7)], DOLGU)
    _pl(b, [(-7, -7), (7, -7), (7, 7), (-7, 7)], 1, True)
    _ln(b, (-7, -7), (9, 9), 1)
    _dolgu(b, [(9, 9), (4, 7), (7, 4)], 1)


# ====================================================================== PİS SU ŞEMA PARÇALARI
def _tk(B):
    b = B.new('ROTAS-SEMA-TEMIZLEME-KAPAGI')
    _dolgu(b, [(-10, -11), (10, -11), (10, 11), (-10, 11)], DOLGU)
    _pl(b, [(-10, -11), (10, -11), (10, 11), (-10, 11)], 1, True)
    b.add_circle((0, 0), 9.0, dxfattribs={'color': 1})
    for x in (-5, 5):
        b.add_circle((x, 0), 1.3, dxfattribs={'color': 1})


def _havalik(B):
    b = B.new('ROTAS-SEMA-HAVALIK')
    K = 43
    _pl(b, [(-12, 0), (-12, 6), (12, 6), (12, 0)], K)
    _pl(b, [(-9, 6), (-9, 12), (9, 12), (9, 6)], K)
    b.add_arc((0, 12), 9.0, 0, 180, dxfattribs={'color': K})


def _rogar_ok(B):
    b = B.new('ROTAS-SEMA-ROGAR-OK')
    Y = 2
    _pl(b, [(0, -6), (18, -4), (18, -9), (34, 0), (18, 9), (18, 4), (0, 6)], Y, True)


def _deşarj_ok(B):
    b = B.new('ROTAS-SEMA-DESARJ-OK')
    Y = 2
    _pl(b, [(-3, 0), (-3, -14), (-7, -14), (0, -24), (7, -14), (3, -14), (3, 0)], Y, True)


def _rogar(B):
    """rögar şeması kutusu (new_block MTY-ROGAR KAT ölçüsü): üst 89x64 (mavi) + iç (sarı) + alt kesit 89x32;
    orijin üst kutunun merkezi"""
    b = B.new('ROTAS-SEMA-ROGAR')
    _pl(b, [(-44.5, -32), (44.5, -32), (44.5, 32), (-44.5, 32)], 5, True)
    _pl(b, [(-38, -26), (38, -26), (38, 26), (-38, 26)], 2, True)
    _pl(b, [(-44.5, -32), (-44.5, -64), (44.5, -64), (44.5, -32)], 8)
    _pl(b, [(-37, -37), (37, -37), (37, -59), (-37, -59)], 8, True)
    _attdef(b, 'NO', (0, 0), h=31.5, renk=5, hiza='C')


def _rogar_plan(B):
    """temel planı rögarı (plan): 89x62 kutu + iç 73x48 + üstte kesit kutusu 89x34 (new_block temel), orijin merkez"""
    b = B.new('ROTAS-TEMEL-ROGAR')
    _pl(b, [(-44.5, -31), (44.5, -31), (44.5, 31), (-44.5, 31)], 5, True)
    _pl(b, [(-36.5, -24), (36.5, -24), (36.5, 24), (-36.5, 24)], 2, True)
    _pl(b, [(-44.5, 31), (-44.5, 65), (44.5, 65), (44.5, 31)], 8)
    _pl(b, [(-36.5, 38), (36.5, 38), (36.5, 58), (-36.5, 58)], 8, True)
    _attdef(b, 'NO', (0, 0), h=26.0, renk=5, hiza='C')


def _balonlar(B):
    for ad, rn, ry in (('ROTAS-SEMA-KOLON-NO', 6, 6), ('ROTAS-SEMA-KOLON-NO-YAGMUR', 3, 3)):
        b = B.new(ad)
        b.add_circle((0, 0), 27.5, dxfattribs={'color': rn})
        b.add_circle((0, 0), 24.5, dxfattribs={'color': DOLGU})
        _attdef(b, 'NO', (0, 0), h=20.0, renk=ry, hiza='C')
    b = B.new('ROTAS-SEMA-DAIRE-NO')
    b.add_circle((0, 0), 55.0, dxfattribs={'color': 6})      # dış mor + iç daire (kullanıcının ölçek 2 balonu)
    b.add_circle((0, 0), 49.0, dxfattribs={'color': DOLGU})
    _attdef(b, 'NO', (0, 0), h=40.0, renk=6, hiza='C')
    b = B.new('ROTAS-TEMEL-PIS-KOLON')
    b.add_circle((0, 0), 7.0, dxfattribs={'color': 6})
    _daire_dolgu(b, (0, 0), 7.0, 6)
    b.add_circle((0, 0), 10.0, dxfattribs={'color': 30})


def _ok_dolu(B):
    b = B.new('ROTAS-SEMA-AKIS-OKU')          # +y yönünde dolu ok, 8x16
    _dolgu(b, [(-4, -8), (4, -8), (0, 8)], 5)
    b = B.new('ROTAS-SEMA-EGIM-OKU')          # +x yönünde sarı ok
    _dolgu(b, [(-10, 0), (6, 3), (6, -3)], 2)
    _pl(b, [(-26, 0), (-10, 0)], 2)
    _dolgu(b, [(10, 0), (-6, 3.5), (-6, -3.5)], 2)


# ====================================================================== ETİKETLER (öznitelikli, CAD'de düzenlenebilir)
def _etiketler(B):
    h = ETIKET_H
    # temiz su hat etiketi, kanca yukarı: dikey 12 + yatay 8; satırlar 15 aralıklı (alt satır +10)
    b = B.new('ROTAS-SEMA-ET-MB4')
    _ln(b, (0, 0), (0, 14), 256)
    _ln(b, (0, 14), (8, 14), 256)
    for i, t in enumerate(('C1', 'M1', 'C2', 'M2')):
        _attdef(b, t, (10, 55 - 15 * i), h=h)
    b = B.new('ROTAS-SEMA-ET-MB2')
    _ln(b, (0, 0), (0, 14), 256)
    _ln(b, (0, 14), (8, 14), 256)
    for i, t in enumerate(('C1', 'M1')):
        _attdef(b, t, (10, 25 - 15 * i), h=h)
    # pis su hat etiketi (toplayıcı üstü), kanca hatta iner
    b = B.new('ROTAS-SEMA-ET-SB')
    _ln(b, (0, 0), (0, 8), 256)
    _ln(b, (0, 8), (4, 8), 256)
    _attdef(b, 'CAP', (5, 21), h=h)
    _attdef(b, 'SB', (5, 7), h=h)
    # iki satırlı yalın etiket (sol / sağ hizalı): armatür bağlantısı, iniş, kolon
    for ad, hz in (('ROTAS-SEMA-ET2-SAG', 'L'), ('ROTAS-SEMA-ET2-SOL', 'R')):
        b = B.new(ad)
        _attdef(b, 'CAP', (0, 14), h=h, hiza=hz)
        _attdef(b, 'DEGER', (0, 0), h=h, hiza=hz)
    # daire besleme dikmesi etiketi (sola kanca)
    b = B.new('ROTAS-SEMA-ET-DIKME')
    _ln(b, (0, 0), (-8, 0), 256)
    _attdef(b, 'CAP', (-10, 3), h=h, hiza='R')
    _attdef(b, 'MB', (-10, -12), h=h, hiza='R')


def bloklar(doc):
    B = doc.blocks
    _lavabo(B)
    _klozet(B)
    _dus(B)
    _eviye(B)
    _makine(B, 'ROTAS-SEMA-CAMASIR-MAKINESI', True)
    _makine(B, 'ROTAS-SEMA-BULASIK-MAKINESI', False)
    _suzgec(B)
    _kombi(B)
    _vanalar(B)
    _tk(B)
    _havalik(B)
    _rogar_ok(B)
    _deşarj_ok(B)
    _rogar(B)
    _rogar_plan(B)
    _balonlar(B)
    _ok_dolu(B)
    _etiketler(B)


ARM_BLOK = {'LV': 'ROTAS-SEMA-LAVABO', 'WC': 'ROTAS-SEMA-KLOZET', 'DUS': 'ROTAS-SEMA-DUS', 'EV': 'ROTAS-SEMA-EVIYE',
            'CM': 'ROTAS-SEMA-CAMASIR-MAKINESI', 'BM': 'ROTAS-SEMA-BULASIK-MAKINESI', 'YS': 'ROTAS-SEMA-YER-SUZGECI'}


def ekle(msp, ad, p, katman, rot=0.0, attr=None, olcek=1.0):
    e = msp.add_blockref(ad, p, dxfattribs={'layer': katman, 'rotation': rot, 'xscale': olcek, 'yscale': olcek})
    if attr:
        e.add_auto_attribs(attr)
    return e
