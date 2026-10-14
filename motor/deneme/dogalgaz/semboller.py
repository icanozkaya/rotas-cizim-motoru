"""Doğalgaz sembolleri — R2 (14.10.2026 B): MTY BLOĞU YOK.

Bütün semboller saf geometri (LINE / CIRCLE / ARC / LWPOLYLINE / HATCH) ROTAS- bloklarıdır; blok içi katman 0, BYLAYER.
Öznitelik yalnız CAP (görünmez; çap boru etiketinde) ve sayaçta TIP.
  ROTAS-DG-KURESEL-VANA  gaz küresel vanası (papyon + küre + kol), 20 x 13, taban orta (eski MTY-KURESEL VANA yerine)
  ROTAS-DG-ESNEK         esnek bağlantı (iki rakor + oluklu gövde), 21,5 x 13,4 (eski MTY-ESNEK BAGLANTI yerine)
  ROTAS-DG-KOMBI         kombi (C tipi, hermetik) gövde 48 x 30 + baca, gaz bağlantısı (23,9; 30) (eski MTY-KOMBİ yerine)
  ROTAS-DG-SAYAC         körüklü gaz sayacı (izometrik ön yüz, tip "G4")
  ROTAS-DG-REGULATOR     basınç düşürücü (içi dolu papyon + diyafram kubbesi + kesikli algılama hattı)
  ROTAS-DG-OCAK          4 gözlü ocak (gövde + 4 bek + düğmeler)
"""
import math

C30, S30 = math.cos(math.radians(30)), 0.5

LEJANT_AD = {
    'ROTAS-DG-KURESEL-VANA': 'Küresel vana (TS EN 331) - AKV / sayaç / daire / cihaz vanası',
    'ROTAS-DG-REGULATOR': 'Basınç düşürücü regülatör (servis kutusu)',
    'ROTAS-DG-SAYAC': 'Gaz sayacı G4 (körüklü)',
    'ROTAS-DG-ESNEK': 'Esnek bağlantı (kombi ≤60 cm, ocak ≤150 cm)',
    'ROTAS-DG-KOMBI': 'Kombi (C tipi, hermetik)',
    'ROTAS-DG-OCAK': 'Ocak (A tipi, bacasız)',
}


def _cap_attdef(b, pos):
    a = b.add_attdef('CAP', insert=pos, height=3, dxfattribs={'style': 'ROTAS'})
    a.dxf.text = ''
    a.is_invisible = True


def _ortak(doc):
    if 'ROTAS-DG-KURESEL-VANA' not in doc.blocks:
        b = doc.blocks.new('ROTAS-DG-KURESEL-VANA', base_point=(0, 0))
        b.add_lwpolyline([(-10, 5), (-10, -5), (0, 0)], close=True)
        b.add_lwpolyline([(10, 5), (10, -5), (0, 0)], close=True)
        b.add_circle((0, 0), 2.2)
        b.add_line((0, 2.2), (0, 8))
        b.add_line((0, 8), (8, 8))
        _cap_attdef(b, (-4, -1.5))
    if 'ROTAS-DG-ESNEK' not in doc.blocks:
        b = doc.blocks.new('ROTAS-DG-ESNEK', base_point=(0, 0))
        for sx in (-1, 1):
            b.add_lwpolyline([(sx * 10.75, 6.7), (sx * 8.1, 6.7), (sx * 8.1, -6.7), (sx * 10.75, -6.7)], close=True)
        for sy in (-1, 1):
            pts = [(-8.1, sy * 3.1)]
            x, k = -8.1, 0
            while x < 8.1 - 1e-6:
                x = min(8.1, x + 2.025)
                k += 1
                pts.append((x, sy * (6.7 if k % 2 else 3.1)))
            b.add_lwpolyline(pts)
        _cap_attdef(b, (-4, -1.5))
    if 'ROTAS-DG-KOMBI' not in doc.blocks:
        # gövde (0,0)-(47,8;30); gaz bağlantısı üst orta (23,9; 30); sağda eş eksenli baca (dış atmosfere)
        b = doc.blocks.new('ROTAS-DG-KOMBI', base_point=(0, 0))
        b.add_lwpolyline([(0, 0), (47.8, 0), (47.8, 30), (0, 30)], close=True)
        b.add_lwpolyline([(3.4, 3.4), (44.4, 3.4), (44.4, 26.6), (3.4, 26.6)], close=True)
        b.add_circle((23.9, 15), 6)                       # brülör / yanma odası
        # alev (iki yay) - çizgi harf yok
        b.add_arc((21.4, 15), 3.0, 300, 60)
        b.add_arc((26.4, 15), 3.0, 120, 240)
        b.add_lwpolyline([(8, 22), (16, 22), (16, 24.5), (8, 24.5)], close=True)   # gösterge
        # eş eksenli baca: dış boru + iç boru, uçta rüzgâr başlığı
        b.add_line((47.8, 20), (78, 20))
        b.add_line((47.8, 10), (78, 10))
        b.add_line((47.8, 17), (82, 17))
        b.add_line((47.8, 13), (82, 13))
        b.add_line((78, 20), (78, 10))
        b.add_lwpolyline([(82, 21), (90, 21), (90, 9), (82, 9)], close=True)
        for y in (12.5, 15, 17.5):
            b.add_line((90, y), (95, y))


def tanimla(doc, lay_sem):
    """ROTAS-DG-* bloklarını tanımla (blok içi katman 0 / BYLAYER; ekleme katmanı lay_sem)."""
    _ortak(doc)
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
