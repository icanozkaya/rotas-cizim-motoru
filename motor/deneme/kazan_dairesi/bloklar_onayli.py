# -*- coding: utf-8 -*-
"""ONAYLI kazan dairesi plan / kesit / kısmi görünüş paftası (plan_kesit.py) için kendi sembol bloklarımız — R2 (14.10.2026).

MTY bloğu YOK. Onaylı çizimde (14.10.2026 16:39) kullanılan 14 sembolün görünüşü (biçim, ölçü, renk) saf geometri
ROTAS-KD- bloklarıyla aynen verilir: LINE / CIRCLE / ARC / LWPOLYLINE / HATCH (dolu). Blok içinde TEXT/MTEXT/INSERT
yoktur (purjör "O.H.A.C", termometre "T", manometre "M" harfleri çizgi harftir); yalnız gizli CAP özniteliği (çap) vardır.
Geometri `semboller_onayli_veri.py` içindedir (çalışma anında dış kütüphane / MTY dosyası gerekmez). Blok içi nesneler
katman 0'dadır; renkler onaylı görünüş birebir korunsun diye nesne bazında sabittir (vana kırmızı, purjör yazısı sarı,
denge kabı BYBLOCK = yerleştirildiği katmanın rengi ...).
Hat içi sembollerde orijin boru ekseninde, boru +X; branşman sembollerinde (EV, M, TM, HP) orijin bağlantı noktası, +Y.
"""
import bloklar as BL0                      # ROTAS-POMPA, ROTAS-KAZAN-DUVAR, ROTAS-SELENOID ... (zaten saf geometri)
from semboller_onayli_veri import ACIKLAMA, TANIM

KURESEL, KELEBEK, CEKVALF = 'ROTAS-KD-KURESEL-VANA', 'ROTAS-KD-KELEBEK-VANA', 'ROTAS-KD-CEKVALF'
PISLIK, KILITLI, ESNEK = 'ROTAS-KD-PISLIK-TUTUCU', 'ROTAS-KD-KILITLI-VANA', 'ROTAS-KD-ESNEK-BAGLANTI'
EMNIYET, MANOMETRE, TERMOMETRE = 'ROTAS-KD-EMNIYET-VENTILI', 'ROTAS-KD-MANOMETRE', 'ROTAS-KD-TERMOMETRE'
PURJOR = 'ROTAS-KD-PURJOR'
DENGE_PLAN, GT_PLAN, BOYLER_PLAN = 'ROTAS-KD-DENGE-KABI-PLAN', 'ROTAS-KD-GENLESME-TANKI-PLAN', 'ROTAS-KD-BOYLER-PLAN'
YER_SUZGECI = 'ROTAS-KD-YER-SUZGECI'

# hat içi semboller: boru kesme yarım boyu (ölçek 1)
YARIM = {KURESEL: 10.5, KELEBEK: 10.5, CEKVALF: 11.5, PISLIK: 10.5, KILITLI: 10.5, ESNEK: 11.0, DENGE_PLAN: 20.0}


def _a(renk):
    return {'layer': '0', 'color': renk}


def blok_ciz(b, ilkel):
    for p in ilkel:
        t = p[0]
        if t == 'L':
            b.add_line(p[2:4], p[4:6], dxfattribs=_a(p[1]))
        elif t == 'C':
            b.add_circle(p[2:4], p[4], dxfattribs=_a(p[1]))
        elif t == 'A':
            b.add_arc(p[2:4], p[4], p[5], p[6], dxfattribs=_a(p[1]))
        elif t == 'P':
            e = b.add_lwpolyline(p[4], format='xyb', close=p[2], dxfattribs=_a(p[1]))
            if p[3]:
                e.dxf.const_width = p[3]
        elif t == 'H':
            h = b.add_hatch(color=p[1], dxfattribs={'layer': '0'})
            h.paths.add_polyline_path(p[2], is_closed=True)
        elif t == 'CAP':
            a = b.add_attdef('CAP', (p[1], p[2]), dxfattribs={'layer': '0', 'height': p[3], 'rotation': p[4],
                                                               'style': 'ROTAS'})
            a.is_invisible = True


def hazirla(doc):
    """ROTAS yazı stili + kendi bloklar (pompa, kazan, selenoid, regülatör, gaz alarm, boyler, nötralizasyon, ok) +
    onaylı paftanın 14 ROTAS-KD- sembolü. MTY dosyası okunmaz."""
    if 'ROTAS' not in doc.styles:
        doc.styles.add('ROTAS', font='arial.ttf')
    if 'ROTAS' not in doc.appids:
        doc.appids.new('ROTAS')
    BL0.kendi_bloklar(doc)
    for ad, ilkel in TANIM.items():
        if ad not in doc.blocks:
            blok_ciz(doc.blocks.new(ad), ilkel)


__all__ = ['hazirla', 'YARIM', 'ACIKLAMA', 'TANIM']
