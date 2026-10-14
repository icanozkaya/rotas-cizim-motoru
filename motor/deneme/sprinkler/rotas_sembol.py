# -*- coding: utf-8 -*-
"""ROTAŞ saf geometri sembolleri (yangın R2, 14.10.2026 (B) talimatı: MTY BLOĞU YOK).

Bütün semboller yalnız LINE / CIRCLE / ARC / LWPOLYLINE / HATCH ile çizilir; blok adları 'ROTAS-SMB-' önekli,
blok içi katman '0' (INSERT katmanını alır). Yazı, öznitelik, iç içe blok yoktur.
Birim cm. Orijin sembol merkezi (hat üstü semboller) veya bağlantı noktası; boru / akış yönü +X.
Yönlü semboller (çek valf, akış oku, emniyet, ıslak alarm) akışı +X yönünde gösterir: INSERT açısı = akış yönü.

Kullanım (sprinkler şeması, plan, pompa_grubu kesiti ortak):
    import rotas_sembol as RS
    RS.hazirla(doc)                                  # (isteğe bağlı) tüm blokları tanımla
    RS.ciz(msp, 'cekvalf', x, y, aci=-90, olcek=1, katman='ROTAS-YANGIN-SEMBOL')
    RS.hat(msp, p0, p1, [(0.5, 'izlenebilir_kelebek')], 'ROTAS-YANGIN-SPR-BORU', sembol_katmani=..., genislik=3)
    RS.lejant(doc, x, y)                             # kullanılan ROTAS-SMB bloklarının lejantı + adet tablosu
"""
import math
from ezdxf.enums import TextEntityAlignment as TA

ONEK = 'ROTAS-SMB-'


# ------------------------------------------------------------------ çizim yardımcıları (blok içi, katman 0)
def _a():
    return {'layer': '0'}


def _ln(b, p, q):
    b.add_line(p, q, dxfattribs=_a())


def _pl(b, pts, kapali=False):
    b.add_lwpolyline(pts, close=kapali, dxfattribs=_a())


def _ci(b, c, r):
    b.add_circle(c, r, dxfattribs=_a())


def _arc(b, c, r, a0, a1):
    b.add_arc(c, r, a0, a1, dxfattribs=_a())


def _dolu(b, pts):
    h = b.add_hatch(color=256, dxfattribs=_a())
    h.set_solid_fill(color=256)
    h.paths.add_polyline_path(pts, is_closed=True)


def _dolu_daire(b, c, r, n=20):
    _dolu(b, [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)])
    _ci(b, c, r)


def _papyon(b, l=10.0, h=6.0, dx=0.0):
    _pl(b, [(dx - l, -h), (dx - l, h), (dx, 0)], True)
    _pl(b, [(dx + l, -h), (dx + l, h), (dx, 0)], True)


def _ok(b, x0, x1, y, bas=3.0):
    """akış oku x0 -> x1 (y düzeyinde), dolu uç"""
    _ln(b, (x0, y), (x1 - bas * 1.6, y))
    _dolu(b, [(x1, y), (x1 - bas * 1.6, y + bas * 0.6), (x1 - bas * 1.6, y - bas * 0.6)])


# ------------------------------------------------------------------ semboller
def g_kelebek(b):
    _papyon(b)
    _ln(b, (0, -7), (0, 7))
    _ln(b, (0, 7), (0, 13))
    _ln(b, (-5, 13), (5, 13))


def g_izlenebilir_kelebek(b):
    _papyon(b)
    _ln(b, (0, -7), (0, 7))
    _ln(b, (0, 7), (0, 11))
    _pl(b, [(-5, 11), (5, 11), (5, 19), (-5, 19)], True)          # sinyal (izleme) anahtarı kutusu
    _ln(b, (-5, 11), (5, 19))


def g_cekvalf(b):
    """çek valf: +X yönünü gösteren dolu üçgen + oturma çubuğu + üstte akış oku"""
    _pl(b, [(-10, -6), (-10, 6), (10, 6), (10, -6)], True)
    _dolu(b, [(-8, -5), (-8, 5), (6, 0)])
    _ln(b, (7.5, -6), (7.5, 6))
    _ok(b, -8, 9, 10.0, 2.5)


def g_kuresel(b):
    _papyon(b)
    _dolu_daire(b, (0, 0), 3.0)
    _ln(b, (0, 3), (0, 11))
    _ln(b, (0, 11), (8, 11))


def g_kompansator(b):
    """kauçuk körüklü kompansatör (flanşlı), boy 60 (ölçekle kısaltılır)"""
    _ln(b, (-30, -12), (-30, 12))
    _ln(b, (30, -12), (30, 12))
    _ln(b, (-27, -12), (-27, 12))
    _ln(b, (27, -12), (27, 12))
    n = 6
    up, dn = [], []
    for i in range(n * 2 + 1):
        x = -27 + 54 * i / (n * 2)
        yy = 10 if i % 2 == 0 else 6
        up.append((x, yy))
        dn.append((x, -yy))
    _pl(b, up)
    _pl(b, dn)


def g_esnek(b):
    """örgülü esnek bağlantı: flanşlar + çapraz taralı gövde"""
    _ln(b, (-10.8, -7), (-10.8, 7))
    _ln(b, (10.8, -7), (10.8, 7))
    _pl(b, [(-9, -5), (9, -5), (9, 5), (-9, 5)], True)
    for i in range(6):
        x = -9 + i * 3.6
        _ln(b, (x, -5), (min(x + 3.6, 9), 5))
        _ln(b, (x, 5), (min(x + 3.6, 9), -5))


def g_pislik_tutucu(b):
    """Y tipi pislik tutucu: gövde + eğik süzgeç cebi + tapa (boru gövdeden geçer)"""
    _ln(b, (-10, 0), (10, 0))
    _pl(b, [(-8, -5), (8, -5), (8, 5), (-8, 5)], True)
    _pl(b, [(-3, -5), (5, -14), (9, -10), (3, -5)])
    _ln(b, (4, -15), (10, -9))


def g_geri_akis(b):
    _pl(b, [(-10, -6), (-10, 6), (10, 6), (10, -6)], True)
    _dolu(b, [(-9, -4), (-9, 4), (-2, 0)])
    _dolu(b, [(1, -4), (1, 4), (8, 0)])
    _ln(b, (0, -6), (0, -12))
    _pl(b, [(-3, -12), (3, -12), (0, -16)], True)


def g_akis_anahtari(b):
    """paletli akış anahtarı: boru üstü gövde + palet"""
    _ln(b, (-10, 0), (10, 0))
    _ln(b, (0, 0), (0, 5))
    _pl(b, [(-7, 5), (7, 5), (7, 15), (-7, 15)], True)
    _ln(b, (-7, 15), (7, 5))
    _ln(b, (0, 0), (5, -6))
    _ok(b, -9, 9, -9.0, 2.0)


def g_islak_alarm(b):
    """ıslak alarm vanası: gövde dairesi + içinde çek klape + alarm (gong) hattı"""
    _ci(b, (0, 0), 10)
    _dolu(b, [(-6, -5), (-6, 5), (4, 0)])
    _ln(b, (5, -6), (5, 6))
    _ln(b, (0, 10), (0, 22))
    _arc(b, (0, 28), 6, 200, 340)
    _ln(b, (-6, 26), (6, 26))
    _ci(b, (0, 28), 1.5)


def g_test_drenaj(b):
    """test ve drenaj seti: küresel vana + gözetleme camı"""
    _papyon(b, 6, 5, -5)
    _dolu_daire(b, (-5, 0), 2.0)
    _ln(b, (1, 0), (4, 0))
    _pl(b, [(4, -5), (12, -5), (12, 5), (4, 5)], True)
    _ci(b, (8, 0), 3)


def g_basinc_dusurucu(b):
    _papyon(b)
    _ln(b, (0, 0), (0, 7))
    _arc(b, (0, 7), 6, 0, 180)
    _ln(b, (-6, 7), (6, 7))
    _ln(b, (-7, -9), (7, 9))
    _dolu(b, [(7, 9), (3.5, 7.5), (5.5, 5)])


def g_emniyet(b):
    """yaylı emniyet (basınç tahliye) ventili; giriş orijinde (+X yönüne akış), gövde (17,0), çıkış aşağı (17,-10)"""
    _ln(b, (0, 0), (9, 0))
    _pl(b, [(9, -5), (9, 5), (17, 0)], True)
    _pl(b, [(12, -10), (22, -10), (17, 0)], True)
    _ln(b, (17, 0), (17, 4))
    _pl(b, [(17, 4), (14, 6), (20, 8), (14, 10), (20, 12), (17, 14)])
    _ln(b, (13, 14), (21, 14))


def g_manometre(b):
    _ln(b, (0, 0), (0, 5))
    _ln(b, (-2, 3), (2, 3))
    _ln(b, (0, 5), (0, 8))
    _ci(b, (0, 13), 5)
    _ln(b, (0, 13), (3, 16))


def g_storz(b):
    """storz rakor DN65 + kör kapak (orijin boru ucu, rakor +X)"""
    _ln(b, (0, -6), (0, 6))
    _pl(b, [(0, -7), (6, -7), (6, 7), (0, 7)], True)
    _pl(b, [(6, 5), (9, 5), (9, 8), (6, 8)], True)
    _pl(b, [(6, -8), (9, -8), (9, -5), (6, -5)], True)
    _arc(b, (6, 0), 7, -90, 90)
    _ln(b, (8, 0), (13, 0))


def g_yangin_dolabi_kolon(b):
    """yangın dolabı (şema): kabin + hortum makarası + lüle; bağlantı orijinde (sağ kenar ortası)"""
    _pl(b, [(-40, -25), (0, -25), (0, 25), (-40, 25)], True)
    _pl(b, [(-38, -23), (-2, -23), (-2, 23), (-38, 23)], True)
    _ci(b, (-20, 2), 13)
    _ci(b, (-20, 2), 4)
    _ln(b, (-20, -11), (-30, -18))
    _pl(b, [(-30, -18), (-34, -21), (-31, -16)], True)
    _papyon(b, 3, 2.5, -4)


def g_yangin_pompa_seti(b):
    """yangın pompa grubu (şema): elektrikli + dizel + jokey; emiş (-57.6,-10.7), basma (57.6,14.3)"""
    for x, r, dizel in ((-30, 9, False), (0, 9, True), (30, 6, False)):
        _ci(b, (x, 0), r)
        _pl(b, [(x - r * 0.6, -r * 0.8), (x + r * 0.95, 0), (x - r * 0.6, r * 0.8)])
        _ln(b, (x, -r), (x, -10.7))
        if dizel:                                                 # dizel: motor gövdesi pompanın yanında
            _pl(b, [(x + r + 2, -5), (x + r + 12, -5), (x + r + 12, 5), (x + r + 2, 5)], True)
            _ln(b, (x + r, 0), (x + r + 2, 0))
        _ln(b, (x, r), (x, 14.3))
    _ln(b, (-57.6, -10.7), (30, -10.7))
    _ln(b, (-30, 14.3), (57.6, 14.3))
    _ln(b, (-45, -20), (45, -20))                               # ortak kaide


def g_kolon_no(b):
    _ci(b, (0, 0), 27)
    _ci(b, (0, 0), 24)


def g_akis_oku(b):
    _dolu(b, [(6, 0), (-6, 4.5), (-6, -4.5)])


def g_kor_tapa(b):
    _ln(b, (0, -7), (0, 7))
    _ln(b, (2.5, -7), (2.5, 7))


# ad -> (çizim fonksiyonu, açıklama, hat üstü yarı boy (boru kesimi; 0: kesilmez), yönlü mü)
TANIM = {
    'kelebek': (g_kelebek, 'KELEBEK VANA', 10.0, False),
    'izlenebilir_kelebek': (g_izlenebilir_kelebek, 'İZLENEBİLİR (SİNYAL ANAHTARLI) KELEBEK VANA', 10.0, False),
    'cekvalf': (g_cekvalf, 'ÇEK VALF (ok: akış yönü)', 10.0, True),
    'kuresel': (g_kuresel, 'KÜRESEL VANA', 10.0, False),
    'kompansator': (g_kompansator, 'KOMPANSATÖR (KAUÇUK KÖRÜKLÜ)', 30.0, False),
    'esnek': (g_esnek, 'ESNEK BAĞLANTI', 10.8, False),
    'pislik_tutucu': (g_pislik_tutucu, 'PİSLİK TUTUCU (Y TİPİ)', 10.0, False),
    'geri_akis': (g_geri_akis, 'GERİ AKIŞ ÖNLEYİCİ', 10.0, True),
    'akis_anahtari': (g_akis_anahtari, 'AKIŞ ANAHTARI (FLOW SWITCH)', 10.0, True),
    'islak_alarm': (g_islak_alarm, 'ISLAK ALARM VANA İSTASYONU', 10.0, True),
    'test_drenaj': (g_test_drenaj, 'TEST VE DRENAJ SETİ', 12.0, False),
    'basinc_dusurucu': (g_basinc_dusurucu, 'BASINÇ DÜŞÜRÜCÜ VANA', 10.0, True),
    'emniyet': (g_emniyet, 'EMNİYET (BASINÇ TAHLİYE) VENTİLİ', 0.0, True),
    'manometre': (g_manometre, 'MANOMETRE (MUSLUKLU)', 0.0, False),
    'storz': (g_storz, 'İTFAİYE BAĞLANTI AĞZI - STORZ DN65 (KÖR KAPAKLI)', 0.0, True),
    'yangin_dolabi_kolon': (g_yangin_dolabi_kolon, 'YANGIN DOLABI TS EN 671-1 (ŞEMA)', 0.0, False),
    'yangin_pompa_seti': (g_yangin_pompa_seti, 'YANGIN POMPA GRUBU (ELEKTRİKLİ + DİZEL + JOKEY)', 0.0, True),
    'kolon_no': (g_kolon_no, 'KOLON NUMARASI', 0.0, False),
    'akis_oku': (g_akis_oku, 'AKIŞ YÖNÜ', 0.0, True),
    'kor_tapa': (g_kor_tapa, 'KÖR TAPA (KOLON SONU)', 0.0, False),
}


def blok_adi(ad):
    return ONEK + ad.upper().replace('_', '-')


def blok_tanimla(doc, ad):
    n = blok_adi(ad)
    if n not in doc.blocks:
        b = doc.blocks.new(n)
        TANIM[ad][0](b)
    return n


def hazirla(doc, adlar=None):
    for ad in (adlar or TANIM):
        blok_tanimla(doc, ad)


def yari(ad):
    return TANIM[ad][2]


def kutu(doc, ad):
    """yerel sınır kutusu (x0, y0, x1, y1)"""
    from ezdxf import bbox
    n = blok_tanimla(doc, ad)
    e = bbox.extents(doc.blocks[n], fast=True)
    return (e.extmin.x, e.extmin.y, e.extmax.x, e.extmax.y)


def _bb(doc, blokadi):
    from ezdxf import bbox
    if blokadi not in doc.blocks:
        return None
    e = bbox.extents(doc.blocks[blokadi], fast=True)
    return (e.extmin.x, e.extmin.y, e.extmax.x, e.extmax.y) if e.has_data else None


def ciz(msp, ad, x, y, aci=0.0, olcek=1.0, katman='ROTAS-YANGIN-SEMBOL', sx=None, **_):
    doc = msp.doc
    n = blok_tanimla(doc, ad)
    if katman not in doc.layers:
        doc.layers.add(katman, color=1)
    return msp.add_blockref(n, (x, y), dxfattribs={'layer': katman, 'rotation': aci, 'xscale': sx if sx is not None else olcek,
                                                    'yscale': olcek})


def hat(msp, p0, p1, sem, lay, sembol_katmani='ROTAS-YANGIN-SEMBOL', genislik=0.0, olcek=1.0):
    """düz boru p0->p1; sem: [(t, ad) veya (t, ad, _)]; boru hat üstü sembolün yarı boyu kadar kesilir.
    Sembol açısı boru yönüdür (p0 -> p1 = akış yönü)."""
    L = math.dist(p0, p1)
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    aci = math.degrees(math.atan2(uy, ux))
    kes = []
    for s in sem:
        t, ad = s[0], s[1]
        x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
        ciz(msp, ad, x, y, aci=aci, olcek=olcek, katman=sembol_katmani)
        h = yari(ad) * olcek
        if h > 0:
            kes.append((t * L - h, t * L + h))
    kes.sort()
    s0 = 0.0
    parcalar = []
    for a, b in kes:
        if a > s0 + 0.01:
            parcalar.append((s0, a))
        s0 = max(s0, b)
    if s0 < L - 0.01:
        parcalar.append((s0, L))
    for a, b in parcalar:
        e = msp.add_lwpolyline([(p0[0] + ux * a, p0[1] + uy * a), (p0[0] + ux * b, p0[1] + uy * b)], dxfattribs={'layer': lay})
        if genislik:
            e.dxf.const_width = genislik
    return parcalar


def kullanim_say(doc):
    say = {}
    for e in doc.modelspace().query('INSERT'):
        if e.dxf.name.startswith(ONEK):
            say[e.dxf.name] = say.get(e.dxf.name, 0) + 1
    return say


def lejant(doc, x, y, haric=('kolon_no', 'akis_oku'), baslik='YANGIN TESİSATI SEMBOLLERİ (SAF GEOMETRİ)', h=9.0,
           katman='ROTAS-LEJANT', ek=None):
    """kullanılan ROTAS-SMB bloklarının lejantı + adet tablosu (SEMBOL | AÇIKLAMA | ADET). ek: [(blokadı, açıklama, adet)]"""
    msp = doc.modelspace()
    if katman not in doc.layers:
        doc.layers.add(katman, color=7)
    say = kullanim_say(doc)
    satir = []
    for ad, (f, acik, _, _) in TANIM.items():
        n = blok_adi(ad)
        if n in say and ad not in haric:
            satir.append((n, acik, say[n]))
    satir += list(ek or [])
    W = (110, 430, 70)
    rh = 46.0
    X = [x, x + W[0], x + W[0] + W[1], x + sum(W)]
    msp.add_text(baslik, height=h * 1.4, dxfattribs={'layer': katman, 'style': 'ROTAS', 'width': 0.8}) \
        .set_placement((x, y + 10), align=TA.BOTTOM_LEFT)
    yy = y
    msp.add_lwpolyline([(x, yy), (X[3], yy)], dxfattribs={'layer': katman})
    for i, s in enumerate(('SEMBOL', 'AÇIKLAMA', 'ADET')):
        msp.add_text(s, height=h, dxfattribs={'layer': katman, 'style': 'ROTAS', 'width': 0.8}) \
            .set_placement(((X[i] + X[i + 1]) / 2, yy - 12), align=TA.MIDDLE_CENTER)
    yy -= 24
    msp.add_lwpolyline([(x, yy), (X[3], yy)], dxfattribs={'layer': katman})
    for n, acik, adet in satir:
        cy = yy - rh / 2
        bb = _bb(doc, n)
        sc = 1.0
        if bb:
            w_, h_ = bb[2] - bb[0], bb[3] - bb[1]
            sc = min(1.4, (W[0] - 20) / max(w_, 1), (rh - 10) / max(h_, 1))
            cx0 = (bb[0] + bb[2]) / 2 * sc
            cy0 = (bb[1] + bb[3]) / 2 * sc
            msp.add_blockref(n, ((X[0] + X[1]) / 2 - cx0, cy - cy0), dxfattribs={'layer': katman, 'xscale': sc, 'yscale': sc})
        msp.add_text(acik, height=h, dxfattribs={'layer': katman, 'style': 'ROTAS', 'width': 0.8}) \
            .set_placement((X[1] + 6, cy), align=TA.MIDDLE_LEFT)
        msp.add_text(str(adet), height=h, dxfattribs={'layer': katman, 'style': 'ROTAS', 'width': 0.8}) \
            .set_placement(((X[2] + X[3]) / 2, cy), align=TA.MIDDLE_CENTER)
        yy -= rh
        msp.add_lwpolyline([(x, yy), (X[3], yy)], dxfattribs={'layer': katman})
    for xx in X:
        msp.add_line((xx, y), (xx, yy), dxfattribs={'layer': katman})
    # lejant satırlarındaki örnek INSERT'ler adet sayımına girmesin diye katmanı ayrıdır
    return yy, {n: a for n, _, a in satir}


def mty_kontrol(dosya):
    """DXF'te MTY geçen blok / katman / yazı / öznitelik var mı (ham metin taraması dahil). Dönüş: bulgular listesi"""
    import ezdxf
    d = ezdxf.readfile(dosya)
    bul = []
    for b in d.blocks:
        if 'MTY' in b.name.upper():
            bul.append(('blok', b.name))
    for l in d.layers:
        if 'MTY' in l.dxf.name.upper():
            bul.append(('katman', l.dxf.name))
    for e in d.modelspace():
        if e.dxftype() in ('TEXT', 'MTEXT', 'ATTRIB'):
            s = e.dxf.text if e.dxftype() != 'MTEXT' else e.text
            if 'MTY' in s.upper():
                bul.append(('yazi', s[:40]))
        if e.dxftype() == 'INSERT':
            for a in e.attribs:
                if 'MTY' in a.dxf.text.upper():
                    bul.append(('oznitelik', a.dxf.text))
    ham = open(dosya, encoding='utf-8', errors='ignore').read().upper().count('MTY')
    if ham and not bul:
        bul.append(('ham_metin', ham))
    return bul
