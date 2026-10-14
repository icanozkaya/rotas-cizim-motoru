"""Doğalgaz sembolleri.

Öncelik kullanıcının MTY blok kütüphanesi (/tmp/claude-0/blk): MTY-KURESEL VANA, MTY-ESNEK BAGLANTI, MTY-KOMBİ
gerçek blok olarak (patlatılmadan, iç katmanlarıyla) aktarılır.
MTY kütüphanesinde karşılığı olmayanlar kutuphane/arastirma/03_SEMBOLLER.md §7 geometrisiyle blok olarak tanımlanır:
  ROTAS-DG-SAYAC      körüklü gaz sayacı (dikdörtgen gövde, üstten giriş/çıkış saplaması, içinde tip "G4")
  ROTAS-DG-REGULATOR  basınç düşürücü (içi dolu papyon + diyafram kubbesi + çıkışa kesikli algılama hattı + "R")
  ROTAS-DG-OCAK       4 gözlü ocak (gövde + 4 bek + düğmeler)
"""
import glob
import math
import os

from ezdxf import recover
from ezdxf.addons import Importer

BLKDIR = '/tmp/claude-0/blk'
C30, S30 = math.cos(math.radians(30)), 0.5

MTY = {
    'MTY-KURESEL VANA': 'SIHHI TESISAT__VANALAR__MTY-KURESEL VANA.dxf',
    'MTY-ESNEK BAGLANTI': 'RADYATOR TESISATI__VANALAR__MTY-ESNEK BAGLANTI.dxf',
    'MTY-KOMBİ': 'RADYATOR TESISATI__VANALAR__MTY-KOMBİ.dxf',
}

MTY_KUTUPHANE_TAR = '/home/claude/rotas-cizim-motoru/kutuphane/ROTAS_2_MTY_BLOKLARI_2026-10-11.tar.xz'


def _kutuphane_hazir():
    if not glob.glob(os.path.join(BLKDIR, '*MTY-KURESEL VANA.dxf')):
        os.system(f'tar -xJf "{MTY_KUTUPHANE_TAR}" -C / 2>/dev/null')


def mty_aktar(doc):
    """WBLOCK biçimindeki MTY blok dosyalarını hedef çizime aynı adla blok tanımı olarak aktarır."""
    _kutuphane_hazir()
    for ad, fn in MTY.items():
        if ad in doc.blocks:
            continue
        src, _ = recover.readfile(os.path.join(BLKDIR, fn))
        blk = doc.blocks.new(ad)
        im = Importer(src, doc)
        im.import_entities(list(src.modelspace()), blk)
        im.finalize()


def tanimla(doc, lay_sem):
    """ROTAS-DG-* bloklarını tanımla (blok içi katman 0 / BYLAYER; ekleme katmanı lay_sem)."""
    if 'ROTAS-DG-SAYAC' not in doc.blocks:
        # İzometride ön yüz (xz düzlemi) - gövde 40 x 40, x ekseni 30° eğik; taban noktası alt orta
        b = doc.blocks.new('ROTAS-DG-SAYAC', base_point=(0, 0))

        def iso(u, v):
            return (u * C30, u * S30 + v)
        b.add_lwpolyline([iso(-20, 0), iso(20, 0), iso(20, 40), iso(-20, 40)], close=True)
        b.add_lwpolyline([iso(-16, 4), iso(16, 4), iso(16, 36), iso(-16, 36)], close=True)
        # körük ayrım çizgisi (sayaç sayaç gövdesinin üst bölmesi - numaratör penceresi)
        b.add_lwpolyline([iso(-9, 24), iso(9, 24), iso(9, 32), iso(-9, 32)], close=True)
        a = b.add_attdef('TIP', insert=iso(0, 13), height=8, dxfattribs={'style': 'ROTAS'})
        a.dxf.halign, a.dxf.valign = 1, 2
        a.dxf.align_point = iso(0, 13)
        a.dxf.text = 'G4'
    if 'ROTAS-DG-REGULATOR' not in doc.blocks:
        b = doc.blocks.new('ROTAS-DG-REGULATOR', base_point=(0, 0))
        L, H = 12, 7
        for sx in (-1, 1):
            b.add_lwpolyline([(sx * L, H), (sx * L, -H), (0, 0)], close=True)
            h = b.add_hatch()
            h.paths.add_polyline_path([(sx * L, H), (sx * L, -H), (0, 0)], is_closed=True)
        b.add_line((0, 0), (0, 12))
        b.add_arc((0, 12), 8, 0, 180)
        b.add_line((-8, 12), (8, 12))
        # çıkış tarafına algılama (impuls) hattı - kesikli
        b.add_lwpolyline([(8, 15), (22, 15), (22, 4)], dxfattribs={'linetype': 'DASHED', 'ltscale': 0.15})
        t = b.add_text('R', height=7, dxfattribs={'style': 'ROTAS'})
        t.set_placement((-14, 18))
    if 'ROTAS-DG-OCAK' not in doc.blocks:
        # Taban: üst orta (gaz bağlantısı). Gövde 60 x 44, 4 bek (2 büyük 2 küçük), ön panelde 4 düğme
        b = doc.blocks.new('ROTAS-DG-OCAK', base_point=(0, 0))
        b.add_lwpolyline([(-30, 0), (30, 0), (30, -44), (-30, -44)], close=True)
        b.add_line((-30, -36), (30, -36))
        for (x, y, r) in ((-14, -11, 7.5), (14, -11, 6), (-14, -26, 6), (14, -26, 7.5)):
            b.add_circle((x, y), r)
            b.add_circle((x, y), r * 0.45)
        for x in (-18, -6, 6, 18):
            b.add_circle((x, -40), 2.2)
