# -*- coding: utf-8 -*-
"""Kazan dairesi prensip şeması: sembol blokları.

Öncelik (DENEME_KURALLARI §5): kullanıcının MTY blok kütüphanesi (/tmp/claude-0/blk) -> blok OLDUĞU GİBİ
(iç katmanlarıyla, patlatılmadan) içe alınır. MTY'de karşılığı olmayanlar (duvar tipi kazan, pompa, boyler,
selenoid, regülatör, gaz alarm, nötralizasyon, ok) kutuphane/arastirma/03_SEMBOLLER.md geometrisiyle
gerçek sembol olarak çizilir; pompa geometrisi MTY 'KOLLEKTOR POMPA ŞEMA' içindeki pompa çiziminden alınmıştır.
Blok orijini boru ekseni üzerinde, boru +X yönünde (akış +X).
"""
import glob
import math
import os
import subprocess
import tarfile

import ezdxf
from ezdxf import recover
from ezdxf.addons import Importer
from ezdxf.enums import TextEntityAlignment as TA

DEPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MTY_DIR = '/tmp/claude-0/blk'
MTY_TAR = os.path.join(DEPO, 'kutuphane', 'ROTAS_2_MTY_BLOKLARI_2026-10-11.tar.xz')
R = 'RADYATOR TESISATI__VANALAR__'

# ad -> (kaynak dosya, kaynak içindeki blok adı veya None = dosyanın model uzayı)
MTY = {
    'MTY-KURESEL VANA': (R + 'MTY-KURESEL VANA.dxf', None),
    'MTY-KELEBEK VANA': (R + 'MTY-KELEBEK VANA.dxf', None),
    'MTY-CEKVALF VANA': (R + 'MTY-CEKVALF VANA.dxf', None),
    'MTY-PISLIK TUTUCU': (R + 'MTY-PISLIK TUTUCU.dxf', None),
    'MTY-EMNİYET VENTİLİ': (R + 'MTY-EMNİYET VENTİLİ.dxf', None),
    'MTY-MANOMETRE': (R + 'MTY-MANOMETRE.dxf', None),
    'MTY-TERMOMETRE': (R + 'MTY-TERMOMETRE.dxf', None),
    'MTY-O.H.A.C': (R + 'MTY-O.H.A.C.dxf', None),
    'MTY-OTOMATIK DOLUM VANASI': (R + 'MTY-OTOMATIK DOLUM VANASI.dxf', None),
    'MTY-KITLENEBILIR VANA': (R + 'MTY-KITLENEBILIR VANA.dxf', None),
    'MTY-ESNEK BAGLANTI': (R + 'MTY-ESNEK BAGLANTI.dxf', None),
    'MTY-DENGE KABI ŞEMADA': (R + 'MTY-DENGE KABI.dxf', 'MTY-DENGE KABI ŞEMADA'),
    'MTY-HAVA AYIRICI': (R + 'MTY-DENGE KABI.dxf', 'MTY-HAVA AYIRICI'),
    'MTY-TORTU &PİSLİK AYIRICI': (R + 'MTY-DENGE KABI.dxf', 'MTY-TORTU &PİSLİK AYIRICI'),
    'MTY-GENLEŞME TANKI KOLON': (R + 'MTY-KOLLEKTÖR POMPA KOLON.dxf', 'MTY-GENLEŞME TANKI KOLON'),
}

# yerleşim bilgisi (blok yerel koordinatı, ölçek 1): yarım boy (boru kesme), bağlantı noktaları
YARIM = {'MTY-KURESEL VANA': 10.5, 'MTY-KELEBEK VANA': 10.5, 'MTY-CEKVALF VANA': 11.5, 'MTY-PISLIK TUTUCU': 10.5,
         'MTY-OTOMATIK DOLUM VANASI': 10.5, 'MTY-KITLENEBILIR VANA': 10.5, 'MTY-ESNEK BAGLANTI': 11.0,
         'ROTAS-POMPA': 12.5, 'ROTAS-SELENOID': 10.5, 'ROTAS-REGULATOR': 10.5}
DENGE_OLCEK = 0.25            # MTY örneğindeki ölçek
DENGE_SAG_X = 340.0           # sağ ağız (yerel)
DENGE_ALT_Y = -613.25         # alt ağızlar (yerel)
HAVA_AYIRICI = (56.6, 316.6)  # giriş / çıkış ağzı x (yerel, y=0)
TORTU = (0.0, 65.0)


def mty_hazirla():
    if glob.glob(os.path.join(MTY_DIR, '*.dxf')):
        return
    os.makedirs(MTY_DIR, exist_ok=True)
    with tarfile.open(MTY_TAR) as t:
        t.extractall(MTY_DIR)


def _a(lay='0'):
    return {'layer': lay}


def _dolu(b, pts):
    h = b.add_hatch(dxfattribs=_a())
    h.paths.add_polyline_path(pts, is_closed=True)


def _papyon(b, l=20.0, h=12.0, dolu=False):
    for s in (-1, 1):
        pts = [(s * l / 2, h / 2), (s * l / 2, -h / 2), (0, 0)]
        b.add_lwpolyline(pts, close=True, dxfattribs=_a())
        if dolu:
            _dolu(b, pts)


def _yaz(b, s, p, h):
    t = b.add_text(s, height=h, dxfattribs={'layer': '0', 'style': 'ROTAS'})
    t.set_placement(p, align=TA.MIDDLE_CENTER)


def kendi_bloklar(doc):
    B = doc.blocks
    # pompa: MTY pompa çizimi (iç içe iki daire + içi dolu akış üçgeni), ölçek 0,5, akış +X
    b = B.new('ROTAS-POMPA')
    b.add_circle((0, 0), 10.35, dxfattribs=_a()); b.add_circle((0, 0), 12.45, dxfattribs=_a())
    tri = [(10.35, 0), (-4.95, 8.85), (-4.95, -8.85)]
    b.add_lwpolyline(tri, close=True, dxfattribs=_a()); _dolu(b, tri)
    # duvar tipi yoğuşmalı kazan (03 §3 kazan: gövde + alev üçgeni; bağlantı saplamaları altta/üstte)
    b = B.new('ROTAS-KAZAN-DUVAR')
    b.add_lwpolyline([(0, 0), (140, 0), (140, 180), (0, 180)], close=True, dxfattribs=_a())
    b.add_lwpolyline([(14, 138), (126, 138), (126, 166), (14, 166)], close=True, dxfattribs=_a())   # kontrol paneli
    for x in (30, 50, 70):
        b.add_circle((x, 152), 4, dxfattribs=_a())
    b.add_lwpolyline([(95, 146), (118, 146), (118, 158), (95, 158)], close=True, dxfattribs=_a())   # ekran
    alev = [(52, 92), (88, 92), (70, 128)]
    b.add_lwpolyline(alev, close=True, dxfattribs=_a())
    b.add_lwpolyline([(62, 96), (78, 96), (70, 114)], close=True, dxfattribs=_a())
    b.add_line((40, 88), (100, 88), dxfattribs=_a())                                          # brülör
    for x, y0, y1 in ((20, 0, -8), (60, 0, -8), (110, 0, -8), (110, 180, 188)):
        b.add_line((x - 4, y1), (x + 4, y1), dxfattribs=_a())                                 # rakor
    b.add_lwpolyline([(18, 180), (18, 192), (42, 192), (42, 180)], dxfattribs=_a())          # baca adaptörü
    # selenoid vana (gaz: dolu papyon) — 03 §2 / §7
    b = B.new('ROTAS-SELENOID')
    _papyon(b, dolu=True)
    b.add_line((0, 0), (0, 10), dxfattribs=_a())
    b.add_lwpolyline([(-5, 10), (5, 10), (5, 20), (-5, 20)], close=True, dxfattribs=_a())
    _yaz(b, 'S', (0, 15), 6)
    # basınç regülatörü (gaz) — 03 §7: dolu papyon + mil + diyafram kubbesi + kesikli algılama hattı
    b = B.new('ROTAS-REGULATOR')
    _papyon(b, dolu=True)
    b.add_line((0, 0), (0, 9), dxfattribs=_a())
    b.add_arc((0, 9), 6, 0, 180, dxfattribs=_a()); b.add_line((-6, 9), (6, 9), dxfattribs=_a())
    b.add_lwpolyline([(6, 11), (17, 11), (17, 4)], dxfattribs={'layer': '0', 'linetype': 'DASHED', 'ltscale': 0.15})
    # gaz alarm / CO dedektörü (tavan dedektörü: taban + kubbe)
    b = B.new('ROTAS-GAZ-ALARM')
    b.add_line((-12, 0), (12, 0), dxfattribs=_a())
    b.add_arc((0, 0), 9, 0, 180, dxfattribs=_a())
    b.add_line((-4, 9), (-6, 14), dxfattribs=_a()); b.add_line((0, 9), (0, 15), dxfattribs=_a())
    b.add_line((4, 9), (6, 14), dxfattribs=_a())
    _yaz(b, 'G', (0, 4), 5)
    # boyler (03 §3: dikey kapsül + alt yarıda serpantin), orijin alt orta; ağızlar:
    # soğuk su (0,0) alt, sıcak su (0,260) üst, serpantin giriş (-65,140) / çıkış (-65,60), sirkülasyon (65,170)
    b = B.new('ROTAS-BOYLER')
    b.add_line((-55, 55), (-55, 205), dxfattribs=_a()); b.add_line((55, 55), (55, 205), dxfattribs=_a())
    b.add_arc((0, 55), 55, 180, 360, dxfattribs=_a()); b.add_arc((0, 205), 55, 0, 180, dxfattribs=_a())
    z = [(-65, 140), (-38, 140)]
    for k, y in enumerate(range(130, 66, -12)):
        z.append((38 if k % 2 == 0 else -38, y))
    z += [(-38, 60), (-65, 60)]
    b.add_lwpolyline(z, dxfattribs=_a())
    b.add_line((55, 170), (65, 170), dxfattribs=_a())
    b.add_line((-40, 228), (40, 228), dxfattribs=_a())                 # izolasyon/manşon çizgisi
    # nötralizasyon ünitesi: yatay gövde, granül dolgu, giriş (0,0) çıkış (120,0)
    b = B.new('ROTAS-NOTRALIZASYON')
    b.add_lwpolyline([(6, -22, 0, 0, 0), (114, -22, 0, 0, 0.4142), (120, -16, 0, 0, 0), (120, 16, 0, 0, 0.4142),
                      (114, 22, 0, 0, 0), (6, 22, 0, 0, 0.4142), (0, 16, 0, 0, 0), (0, -16, 0, 0, 0.4142)],
                     format='xyseb', close=True, dxfattribs=_a())
    b.add_line((40, -22), (40, 8), dxfattribs=_a()); b.add_line((80, 22), (80, -8), dxfattribs=_a())
    for i, x in enumerate(range(48, 76, 7)):
        for j, y in enumerate(range(-16, 18, 7)):
            b.add_circle((x + (3 if j % 2 else 0), y), 1.3, dxfattribs=_a())
    # akış oku (dolu üçgen), uç orijinde, +X
    b = B.new('ROTAS-OK')
    tri = [(0, 0), (-14, 5), (-14, -5)]
    b.add_lwpolyline(tri, close=True, dxfattribs=_a()); _dolu(b, tri)


def mty_bloklar(doc):
    mty_hazirla()
    kaynak = {}
    for ad, (dosya, blok) in MTY.items():
        if ad in doc.blocks:
            continue
        yol = os.path.join(MTY_DIR, dosya)
        if yol not in kaynak:
            kaynak[yol] = recover.readfile(yol)[0]
        s = kaynak[yol]
        im = Importer(s, doc)
        if blok is None:
            hedef = doc.blocks.new(ad)
            im.import_entities(s.modelspace(), target_layout=hedef)
        else:
            im.import_block(blok, rename=False)
        im.finalize()


def hazirla(doc):
    if 'ROTAS' not in doc.styles:
        doc.styles.add('ROTAS', font='arial.ttf')
    kendi_bloklar(doc)
    mty_bloklar(doc)
