# -*- coding: utf-8 -*-
"""sihhi2/antet.py — ROTAŞ anteti + yerleşim planı paftası (saf geometri, MTY'siz, referans ölçülerinde).

Referans: kullanıcının kendi çizimi ornekler/new_block.dxf (kutuphane/arastirma/SIHHI_ALTIN_REFERANS.md §1,
referans/sihhi/20_antet_yerlesim.png). Bütün ölçüler new_block'tan ezdxf ile ÖLÇÜLDÜ; birim cm.

API
    hazirla(doc)                                   stil + katmanlar
    antet_ciz(msp, x0, y0, bilgi, baslik)          958 × 1428 ROTAŞ anteti; (x0, y0) antet kutusunun sol altı
    yerlesim_ciz(msp, x0, y0, w, h, bilgi, ...)    "YERLEŞİM PLANI ÖLÇEK: 1 / 250" paftası (bilgi kutuları + altlık)
    vaziyet_altlik(doc, kaynak_dxf, bolge, hedef)  mimari vaziyet planını (ör. new_block) altlık olarak alır
    BILGI_VARSAYILAN                               new_block (Metra Mimarlık 4739/4) antet değerleri

Katmanlar: ROTAS-ANTET (çizgi), ROTAS-ANTET-INCE (ara çizgi; referans TARAMA), ROTAS-ANTET-YAZI, ROTAS-ANTET-LOGO,
ROTAS-YERLESIM, ROTAS-YERLESIM-YAZI, ROTAS-MIMARI-VAZIYET (altlık), ROTAS-PAFTA / ROTAS-PAFTA-YAZI.
"""
import math
import os

import ezdxf
from ezdxf import bbox as _bbox
from ezdxf.addons import Importer
from ezdxf.enums import TextEntityAlignment as TA
from ezdxf.math import Matrix44

STIL = 'ROTAS'
KATMAN = {  # ad: (renk, çizgi tipi)
    'ROTAS-PAFTA': (144, 'Continuous'),          # pafta ayraçları (referans ANTED 144)
    'ROTAS-PAFTA-YAZI': (7, 'Continuous'),       # pafta başlıkları (h 40)
    'ROTAS-ANTET': (7, 'Continuous'),
    'ROTAS-ANTET-INCE': (4, 'Continuous'),
    'ROTAS-ANTET-YAZI': (7, 'Continuous'),
    'ROTAS-ANTET-LOGO': (5, 'Continuous'),
    'ROTAS-YERLESIM': (7, 'Continuous'),
    'ROTAS-YERLESIM-YAZI': (7, 'Continuous'),
    'ROTAS-MIMARI-VAZIYET': (8, 'Continuous'),
    'ROTAS-YER-TUTUCU': (1, 'DASHED'),
}
AL = {'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER,
      'MR': TA.MIDDLE_RIGHT, 'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER, 'BR': TA.BOTTOM_RIGHT}

ANTET_W, ANTET_H = 958.0, 1428.0          # referans: 247352…248310 × −444050…−442622
SERIT_H = 2900.0                           # pafta şeridi yüksekliği (−444050…−441150)
BASLIK_H = 40.0                            # pafta başlığı yazı boyu
BASLIK_DX, BASLIK_DY = 538.0, 39.0         # başlık: pafta solu + 538, alt çerçeveden 39 yukarı

BILGI_VARSAYILAN = {
    'proje_turu': 'SIHHİ TESİSAT PROJESİ',
    'il': 'SAKARYA', 'ilce': 'ADAPAZARI', 'belediye': 'ADAPAZARI', 'mahalle': 'TEKELER',
    'pafta': 'G24B23B2B', 'ada': '4739', 'parsel': '4', 'proje_no': '-', 'emsal': '1.05',
    'yapi_sahibi': 'METRA MİMARLIK YAPI SANAYİ VE TİCARET LİMİTED ŞİRKETİ',
    'yapi_sahibi_adres': '',
    'cizen': 'İ.CAN ÖZKAYA',
    'yapi_sistemi': 'BA', 'yapi_sinifi': '3/A', 'bina_maliyeti': '-', 'bagimsiz_bolum': '9', 'kat_sayisi': '3',
    'insaat_alani': '1037,25', 'yapim_suresi': '-', 'kullanma_amaci': 'KONUT',
    'arsa_alani': '761,27m²', 'yapi_cinsi': 'BA.', 'yapi_sinifi_kisa': '3A', 'kat_adedi': '3',
    'alan_hesabi': [('ZEMİN KAT', '304,08 +41,67m² =345,75'), ('1. KAT', '304,08 +41,67m² =345,75'),
                    ('2. KAT', '304,08 +41,67m² =345,75')],
    'alan_toplam': '1037,25m²',
    'muellif': 'BAYRAM GENÇ', 'muellif_oda_no': '56858', 'muellif_buro_no': '',
    'muellif_unvan': 'BAYRAM GENÇ MAKİNA MÜHENDİSİ',
    'firma': 'ROTAŞ', 'firma_ek': 'MÜHENDİSLİK.PROJE.MÜŞAVİRLİK',
    'iletisim': 'rotasmuhendislik@gmail.com / 0264 272 00 49 / 0532 728 37 54 / 0532 378 37 54',
    'kimlik': 'TC:15799549784',
    'adres': 'SEMERCİLER MAH. SAİT FAİK SK. NO:22/C Z01  ADAPAZARI / SAKARYA',
}
NOT_DIKKAT = ['DİKKAT:', 'MİMARİ PROJENİN ONAY AŞAMASINDA', 'YAPILACAK DEĞİŞİKLİKTEN FEN İŞLERİ MD.', 'BİLGİLENDİRİLMESİ']
NOT_ONAY = ['NOT:', '14.06.1999 TARİH 23725 SAYILI ve 08.05.2000 TARİH', '24043 SAYILI RESMİ GAZETEDE KONU İLE İLGİLİ',
            'YAYINLANAN YÖNETMELİKLERE UYULMASI KAYDIYLA', 'ONAYLANMIŞTIR.']


# ============================================================================= ortak çizim yardımcıları
def hazirla(doc):
    """ROTAS yazı stili, çizgi tipleri ve bu modülün katmanları."""
    if STIL not in doc.styles:
        doc.styles.add(STIL, font='arial.ttf')
    try:
        if 'DASHED' not in doc.linetypes:
            ezdxf.setup_linetypes(doc)
    except Exception:
        pass
    for ad, (renk, lt) in KATMAN.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk, linetype=lt if lt in doc.linetypes else 'Continuous')
    if '$INSUNITS' in doc.header and doc.header['$INSUNITS'] == 0:
        doc.header['$INSUNITS'] = 5


class Ciz:
    """Bir düzleme (msp ya da blok) saf geometri + yazı çizer. (ox, oy) yerel sıfır; bütün koordinatlar yereldir."""

    def __init__(self, layout, ox=0.0, oy=0.0, kat='ROTAS-ANTET', kat_yazi='ROTAS-ANTET-YAZI'):
        self.m, self.ox, self.oy, self.kat, self.kat_yazi = layout, ox, oy, kat, kat_yazi
        self.yazilar = []      # (x0, y0, x1, y1, metin) dünya koordinatlı yazı kutuları (çakışma raporu)

    def p(self, x, y):
        return (self.ox + x, self.oy + y)

    def line(self, x0, y0, x1, y1, kat=None):
        return self.m.add_line(self.p(x0, y0), self.p(x1, y1), dxfattribs={'layer': kat or self.kat})

    def pl(self, pts, kat=None, kapali=False, genislik=0.0):
        e = self.m.add_lwpolyline([self.p(x, y) for x, y in pts], close=kapali, dxfattribs={'layer': kat or self.kat})
        if genislik:
            e.dxf.const_width = genislik
        return e

    def rect(self, x0, y0, x1, y1, kat=None, genislik=0.0):
        return self.pl([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], kat, True, genislik)

    def circle(self, x, y, r, kat=None):
        return self.m.add_circle(self.p(x, y), r, dxfattribs={'layer': kat or self.kat})

    def arc(self, x, y, r, a0, a1, kat=None):
        return self.m.add_arc(self.p(x, y), r, a0, a1, dxfattribs={'layer': kat or self.kat})

    def solid(self, pts, kat=None):
        h = self.m.add_hatch(color=256, dxfattribs={'layer': kat or self.kat})
        h.paths.add_polyline_path([self.p(x, y) for x, y in pts], is_closed=True)
        return h

    def tarama(self, x0, y0, x1, y1, adim=6.0, kat=None, aci=45.0):
        """Dikdörtgen içini 45° çizgilerle tarar (beton / duvar kesiti) — saf LINE."""
        kat = kat or self.kat
        w, h = x1 - x0, y1 - y0
        t = math.tan(math.radians(aci))
        d = -h / t if t else 0
        s = x0 + d
        while s < x1:
            # çizgi: (s, y0) -> (s + h/t, y1), dikdörtgene kırpılmış
            xa, ya, xb, yb = s, y0, s + h / t, y1
            if xa < x0:
                ya = y0 + (x0 - xa) * t
                xa = x0
            if xb > x1:
                yb = y0 + (x1 - s) * t
                xb = x1
            if ya < yb and xa <= xb:
                self.line(xa, ya, xb, yb, kat)
            s += adim
        return None

    def text(self, s, x, y, h, al='BL', kat=None, rot=0.0, w=0.85):
        s = str(s)
        if not s.strip():
            return None
        t = self.m.add_text(s, height=h, rotation=rot, dxfattribs={'layer': kat or self.kat_yazi, 'style': STIL, 'width': w})
        t.set_placement(self.p(x, y), align=AL[al])
        # yaklaşık kutu (çakışma raporu için)
        gw = len(s) * h * 0.62 * w
        ax = {'L': 0, 'C': 0.5, 'R': 1}[al[1]]
        ay = {'B': 0, 'M': 0.5, 'T': 1}[al[0]]
        if rot % 180 == 0:
            self.yazilar.append((self.ox + x - ax * gw, self.oy + y - ay * h, self.ox + x + (1 - ax) * gw, self.oy + y + (1 - ay) * h, s))
        else:
            self.yazilar.append((self.ox + x - ay * h, self.oy + y - ax * gw, self.ox + x + (1 - ay) * h, self.oy + y + (1 - ax) * gw, s))
        return t

    def satirlar(self, liste, x, y, h, al='TL', kat=None, aralik=None, w=0.85):
        """Çok satırlı yazı: ilk satır (x, y)'de, sonrakiler aralık kadar aşağıda."""
        aralik = aralik or h * 1.6
        for i, s in enumerate(liste):
            self.text(s, x, y - i * aralik, h, al, kat, w=w)
        return y - len(liste) * aralik


def pafta_basligi(ciz, x0, y0, metin, kat='ROTAS-PAFTA-YAZI'):
    """'ZEMİN KAT PLANI..........ÖLÇEK: 1 / 50' — h 40, pafta solu + 538, alt çerçeveden 39 yukarı (referans)."""
    return ciz.text(metin, x0 + BASLIK_DX, y0 + BASLIK_DY, BASLIK_H, 'BL', kat, w=0.9)


# ============================================================================= antet
# Kutular (antet sol altına göre; ölçüler new_block'tan)
_XI0, _XI1 = 9.0, 949.0            # iç çerçeve x
_XM0, _XM1 = 476.5, 481.5          # orta ayraç (5 cm boşluk)
_KUTULAR = [                        # (y alt, y üst, bölünmüş mü)
    (9.2, 274.0, False),            # B1 arsa + yapı bilgileri
    (279.0, 325.4, False),          # B2 proje adı
    (330.4, 520.4, False),          # B3 logo + firma
    (525.4, 875.4, True),           # B4 inceleyen / uygundur / onaylanır
    (880.4, 1019.6, False),         # B5 onay notu
    (1024.6, 1277.9, True),         # B6 müellif / yapı denetim kaşe alanı
    (1282.9, 1366.9, True),         # B7 adı soyadı / oda no / büro tescil
    (1371.9, 1418.9, True),         # B8 PROJE MÜELLİFİ / YAPI DENETİM FİRMASI
]
_B1_COL_ALT = [9.0, 107.7, 234.1, 346.6, 459.1, 557.7, 721.3, 796.6, 949.0]       # yapının özellikleri sütunları
_B1_COL_UST = [9.0, 123.6, 257.3, 408.0, 526.6, 659.4, 744.6, 824.1, 949.0]       # arsanın özellikleri sütunları


def _orta(c, i):
    return (c[i] + c[i + 1]) / 2


def antet_ciz(msp, x0, y0, bilgi=None, baslik=None):
    """ROTAŞ anteti: 958 × 1428 kutu; (x0, y0) sol alt köşe. Dönüş: (genişlik, yükseklik)."""
    b = dict(BILGI_VARSAYILAN)
    b.update(bilgi or {})
    baslik = baslik or b.get('proje_turu', 'SIHHİ TESİSAT PROJESİ')
    c = Ciz(msp, x0, y0, 'ROTAS-ANTET', 'ROTAS-ANTET-YAZI')
    INCE = 'ROTAS-ANTET-INCE'
    # dış ve iç çerçeve
    c.rect(0, 0, ANTET_W, ANTET_H)
    for ya, yu, bol in _KUTULAR:
        if bol:
            c.rect(_XI0, ya, _XM0, yu)
            c.rect(_XM1, ya, _XI1, yu)
        else:
            c.rect(_XI0, ya, _XI1, yu)
    # ---- B1: yapının özellikleri (alt) + arsanın özellikleri (üst)
    for y in (102.0, 134.8, 190.5, 246.2):
        c.line(_XI0, y, _XI1, y)
    c.line(_XI0, 48.4, _XI1, 48.4, INCE)
    c.line(_XI0, 218.3, _XI1, 218.3, INCE)
    c.line(_XI0, 162.7, 257.3, 162.7, INCE)
    c.line(824.1, 162.7, _XI1, 162.7)
    for x in _B1_COL_ALT[1:-1]:
        c.line(x, 9.2, x, 102.0)
    for x in (257.3, 824.1):
        c.line(x, 134.8, x, 246.2)
    for x in (123.6, 408.0, 526.6, 659.4, 744.6):
        c.line(x, 190.5, x, 246.2)
    c.text('YAPININ ÖZELLİKLERİ', 479, 118.4, 15, 'MC')
    bas_alt = [['YAPININ', 'SİSTEMİ'], ['YAPININ', 'SINIFI'], ['BİNA', 'MALİYETİ', 'TL/m²'], ['TOPLAM', 'BAĞIMSIZ', 'BÖLÜM'],
               ['TOPLAM', 'KAT SAYISI'], ['TOPLAM', 'İNŞAAT', 'ALANI (m²)'], ['YAPIM', 'SÜRESİ'], ['KULLANMA', 'AMACI']]
    deg_alt = [b['yapi_sistemi'], b['yapi_sinifi'], b['bina_maliyeti'], b['bagimsiz_bolum'], b['kat_sayisi'],
               b['insaat_alani'], b['yapim_suresi'], b['kullanma_amaci']]
    for i, (sat, deg) in enumerate(zip(bas_alt, deg_alt)):
        xc = _orta(_B1_COL_ALT, i)
        yt = 75.2 + (len(sat) - 1) * 6.5
        for j, s in enumerate(sat):
            c.text(s, xc, yt - j * 13, 9, 'MC')
        c.text(deg, xc, 28.8, 9, 'MC')
    c.text('ARSANIN ÖZELLİKLERİ', 479, 260.1, 15, 'MC')
    bas_ust = ['İLİ', 'İLÇE', 'BELEDİYESİ', 'MAHALLESİ', 'PAFTA', 'ADA', 'PARSEL', 'PROJE NO']
    deg_ust = [b['il'], b['ilce'], b['belediye'], b['mahalle'], b['pafta'], b['ada'], b['parsel'], b['proje_no']]
    for i, (s, d) in enumerate(zip(bas_ust, deg_ust)):
        xc = _orta(_B1_COL_UST, i)
        c.text(s, xc, 232.2, 12, 'MC', w=0.8)
        c.text(d, xc, 204.4, 12, 'MC', w=0.8)
    c.text('YAPI SAHİBİNİN', 133.1, 176.6, 12, 'MC')
    c.text('Adı-Soyadı-Adresi', 133.1, 148.7, 11, 'MC')
    sahibi = b['yapi_sahibi']
    c.text(sahibi, 540.7, 176.6, 14.6 if len(sahibi) <= 46 else 11, 'MC', w=0.8)
    c.text(b.get('yapi_sahibi_adres', ''), 540.7, 148.7, 11, 'MC', w=0.8)
    c.text('ÇİZEN', 886.5, 176.6, 12, 'MC')
    c.text(b['cizen'], 886.5, 148.7, 12, 'MC', w=0.8)
    # ---- B2: proje adı
    c.text(baslik, 479, 302.2, 25, 'MC', w=0.9)
    # ---- B3: logo + firma
    L = 'ROTAS-ANTET-LOGO'
    c.circle(229.0, 431.8, 61.8, L)
    for i in range(-5, 6):               # logo dairesinde ince düşey tarama (referans görünüm)
        xx = 229.0 + i * 10.5
        dy = math.sqrt(max(61.8 ** 2 - (xx - 229.0) ** 2, 0)) - 2
        c.line(xx, 431.8 - dy, xx, 431.8 + dy, 'ROTAS-ANTET-INCE')
    c.text('R', 229.0, 431.8, 63, 'MC', 'ROTAS-ANTET-LOGO', w=1.0)
    c.rect(305.2, 366.2, 307.4, 495.0, L)
    c.solid([(305.2, 366.2), (307.4, 366.2), (307.4, 495.0), (305.2, 495.0)], L)
    c.text(b['firma'], 334.4, 465.0, 30, 'BL', w=0.9)
    c.text(b['firma_ek'], 334.4 + len(b['firma']) * 30 * 0.78 * 0.9 + 8, 465.0, 11.3, 'BL', w=0.85)
    c.text(b['muellif_unvan'], 335.9, 440.4, 11.3, 'TL')
    c.text(b['iletisim'], 336.5, 424.3, 10.8, 'TL', w=0.8)
    c.text(b['kimlik'], 336.4, 402.6, 9.7, 'TL')
    c.text(b['adres'], 335.7, 386.9, 9.7, 'TL', w=0.8)
    # ---- B4: inceleyen / uygundur / onaylanır (sağ kutu); sol kutu kaşe alanı
    c.text('İNCELEYEN', 535.5, 845.9, 15, 'TL')
    c.line(535.5, 826.0, 535.5 + 9 * 15 * 0.62, 826.0, INCE)
    c.text('UYGUNDUR', 773.9, 842.6, 15, 'TL')
    c.line(773.9, 822.7, 773.9 + 8 * 15 * 0.62, 822.7, INCE)
    c.text('ONAYLANIR', 715.2, 684.1, 15, 'TC')
    c.line(715.2 - 4.5 * 15 * 0.62, 664.2, 715.2 + 4.5 * 15 * 0.62, 664.2, INCE)
    # ---- B5: onay notu
    c.text('ONAY', 479, 1005.0, 15, 'MC')
    c.satirlar(NOT_DIKKAT, 19.8, 996.1, 9, 'TL', aralik=15)
    c.satirlar(NOT_ONAY, 538.3, 996.1, 9, 'TL', aralik=15)
    # ---- B7: adı soyadı / oda no / büro tescil (sol); yapı denetim (sağ boş)
    c.line(_XI0, 1324.9, _XM0, 1324.9, INCE)
    for x in (208.8, 299.8):
        c.line(x, 1282.9, x, 1366.9)
    for s, d, xc in (('ADI, SOYADI', b['muellif'], 108.9), ('ODA NO', b['muellif_oda_no'], 254.3),
                     ('BÜRO TESCİL NO', b['muellif_buro_no'], 388.2)):
        c.text(s, xc, 1345.9, 12, 'MC', w=0.8)
        c.text(d, xc, 1303.9, 12, 'MC', w=0.8)
    # ---- B8: başlıklar
    c.text('PROJE MÜELLİFİ', 242.7, 1395.4, 15, 'MC')
    c.text('YAPI DENETİM FİRMASI', 715.2, 1395.4, 15, 'MC')
    return ANTET_W, ANTET_H


# ============================================================================= yerleşim planı
def vaziyet_altlik(doc, kaynak_dxf, bolge, hedef, olcek=1.0, katman='ROTAS-MIMARI-VAZIYET', haric=(), kaynak_doc=None):
    """kaynak_dxf'in `bolge` (x1,y1,x2,y2) içindeki varlıklarını (merkezi bölgede olanlar; `haric` kutularındakiler
    atlanır) hedef belgeye kopyalar, bölge merkezini `hedef` noktasına taşır, `olcek` ile ölçekler; hepsi tek
    katmana (altlık) alınır. Dönüş: kopyalanan varlık sayısı."""
    src = kaynak_doc or ezdxf.readfile(kaynak_dxf)
    smsp = src.modelspace()
    x1, y1, x2, y2 = bolge
    secilen = []
    for e in smsp:
        try:
            bb = _bbox.extents([e], fast=True)
        except Exception:
            continue
        if not bb.has_data:
            continue
        cx, cy = (bb.extmin.x + bb.extmax.x) / 2, (bb.extmin.y + bb.extmax.y) / 2
        if not (x1 <= cx <= x2 and y1 <= cy <= y2):
            continue
        if any(hx1 <= cx <= hx2 and hy1 <= cy <= hy2 for hx1, hy1, hx2, hy2 in haric):
            continue
        if e.dxftype() in ('WIPEOUT', 'IMAGE', 'VIEWPORT'):
            continue
        secilen.append(e)
    if not secilen:
        return 0
    msp = doc.modelspace()
    once = {e.dxf.handle for e in msp}
    imp = Importer(src, doc)
    imp.import_entities(secilen, msp)
    imp.finalize()
    yeni = [e for e in msp if e.dxf.handle not in once]
    if katman not in doc.layers:
        doc.layers.add(katman, color=8)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    M = Matrix44.chain(Matrix44.translate(-mx, -my, 0), Matrix44.scale(olcek, olcek, 1), Matrix44.translate(hedef[0], hedef[1], 0))
    for e in yeni:
        try:
            e.transform(M)
        except Exception:
            pass
        e.dxf.layer = katman
        if e.dxftype() == 'INSERT':
            for a in e.attribs:
                a.dxf.layer = katman
        try:
            e.dxf.color = 256
        except Exception:
            pass
    return len(yeni)


def _kutu_satirlari(c, x0, y0, w, satirlar, h=20.0, aralik=30.0, ust_bosluk=20.0, etiket_w=230.0, kat=None, kat_yazi=None):
    """İçinde 'ETİKET ..... değer' satırları olan kutu; (x0, y0) sol üst. Dönüş: kutu yüksekliği."""
    H = ust_bosluk * 2 + aralik * (len(satirlar) - 1) + h
    c.rect(x0, y0 - H, x0 + w, y0, kat)
    y = y0 - ust_bosluk - h / 2
    for et, deg in satirlar:
        c.text(et, x0 + 25, y, h, 'ML', kat_yazi)
        n = max(2, int((etiket_w - len(et) * h * 0.62 * 0.85) / (h * 0.3)))
        c.text('.' * n, x0 + 25 + len(et) * h * 0.62 * 0.85 + 4, y, h, 'ML', kat_yazi, w=0.5)
        c.text(deg, x0 + 25 + etiket_w + 10, y, h, 'ML', kat_yazi)
        y -= aralik
    return H


def kuzey_oku(c, x, y, boy=60.0, kat=None, kat_yazi=None):
    c.pl([(x, y - boy / 2), (x + boy * 0.18, y - boy * 0.1), (x, y + boy / 2), (x - boy * 0.18, y - boy * 0.1)], kat, True)
    c.solid([(x, y - boy / 2), (x + boy * 0.18, y - boy * 0.1), (x, y + boy / 2)], kat)
    c.text('K', x, y + boy / 2 + 6, 20, 'BC', kat_yazi)


def yerlesim_ciz(msp, x0, y0, w=1682.0, h=SERIT_H, bilgi=None, vaziyet=None, bilgi_kutusu=True, olcek_yazi='1 / 250'):
    """Yerleşim planı paftası. (x0, y0) pafta sol altı. vaziyet: None (yer tutucu çerçeve) ya da
    dict(dxf=yol, bolge=(x1,y1,x2,y2), olcek=1.0, haric=[(x1,y1,x2,y2),...], doc=ezdxf belgesi (isteğe bağlı)).
    Dönüş: dict(altlik_varlik=n)."""
    b = dict(BILGI_VARSAYILAN)
    b.update(bilgi or {})
    c = Ciz(msp, x0, y0, 'ROTAS-YERLESIM', 'ROTAS-YERLESIM-YAZI')
    pafta_basligi(c, 0, 0, 'YERLEŞİM  PLANI   ÖLÇEK: %s' % olcek_yazi)
    # başlıklar
    if bilgi_kutusu:
        sahibi = b['yapi_sahibi']
        c.text("%s'ne AİT" % sahibi, w / 2, h - 915, 22 if len(sahibi) < 52 else 17, 'MC', w=0.8)
        c.text('İNŞAAT  PROJESİ', w / 2, h - 985, 30, 'MC')
        c.text('VAZİYET   PLANI', w / 2, h - 1055, 30, 'MC')
        # bilgi kutusu
        sat = [('İLİ', b['il']), ('İLÇESİ', b['ilce']), ('BELEDİYESİ', b['belediye']), ('MAHALLESİ', b['mahalle']),
               ('PAFTA NO', b['pafta']), ('ADA NO', b['ada']), ('PARSEL NO', b['parsel']), ('EMSAL', b['emsal'])]
        yk = h - 1120
        H1 = _kutu_satirlari(c, 100, yk, 560, sat)
        sat2 = [('ARSA ALANI', b['arsa_alani']), ('YAPI CİNSİ', b['yapi_cinsi']), ('YAPI SINIFI', b['yapi_sinifi_kisa']),
                ('KAT ADEDİ', b['kat_adedi'])]
        yk2 = yk - H1 - 25
        H2 = _kutu_satirlari(c, 100, yk2, 560, sat2)
        # alan hesabı tablosu
        yt = yk2 - H2 - 25
        rows = list(b['alan_hesabi']) + [('TOPLAM', b['alan_toplam'])]
        RH = 36.0
        c.rect(100, yt - 30 - RH * len(rows), 660, yt)
        c.text('YAPI İNŞAAT ALANI HESABI', 380, yt - 15, 12.5, 'MC')
        c.line(100, yt - 30, 660, yt - 30)
        c.line(300, yt - 30, 300, yt - 30 - RH * len(rows))
        y = yt - 30
        for ad, hes in rows:
            c.line(100, y - RH, 660, y - RH)
            c.text(ad, 200, y - RH / 2, 12.5, 'MC')
            c.text(hes, 480, y - RH / 2, 12.5, 'MC')
            y -= RH
        alt_sinir = y - 60
    else:
        alt_sinir = h - 150
    # kuzey oku + ölçek
    kuzey_oku(c, w - 150, h - 1250, 70)
    c.text('ÖLÇEK:%s' % olcek_yazi.replace(' ', ''), w - 150, h - 1250 - 50, 16, 'TC')
    # vaziyet altlığı
    n = 0
    bol = (100.0, 150.0, w - 60.0, min(alt_sinir, h - 1120.0))
    cx, cy = (bol[0] + bol[2]) / 2, (bol[1] + bol[3]) / 2
    if vaziyet and os.path.exists(vaziyet.get('dxf', '')) or (vaziyet and vaziyet.get('doc') is not None):
        bx1, by1, bx2, by2 = vaziyet['bolge']
        s = vaziyet.get('olcek', 1.0)
        # bölge hedef kutusuna sığsın (yalnız küçültme)
        s_fit = min((bol[2] - bol[0]) / max((bx2 - bx1) * s, 1e-6), (bol[3] - bol[1]) / max((by2 - by1) * s, 1e-6), 1.0)
        n = vaziyet_altlik(msp.doc, vaziyet.get('dxf'), vaziyet['bolge'], (x0 + cx, y0 + cy), s * s_fit,
                           vaziyet.get('katman', 'ROTAS-MIMARI-VAZIYET'), vaziyet.get('haric', ()), vaziyet.get('doc'))
    if n == 0:
        c.rect(*bol, kat='ROTAS-YER-TUTUCU')
        c.text('MİMARİ VAZİYET PLANI ALTLIĞI (mimari projeden 1/250 ölçekte alınır)', cx, cy + 20, 18, 'MC', 'ROTAS-YER-TUTUCU')
        c.text('A-A / B-B kesitleri ve parsel ölçüleri mimari vaziyet planındaki gibi', cx, cy - 20, 14, 'MC', 'ROTAS-YER-TUTUCU')
    return dict(altlik_varlik=n, yazilar=c.yazilar)


# ============================================================================= deneme
if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/antet_deneme.dxf'
    d = ezdxf.new('R2018', setup=True)
    d.header['$INSUNITS'] = 5
    hazirla(d)
    m = d.modelspace()
    X0, Y0 = 247352.0, -444050.0
    antet_ciz(m, X0, Y0, {})
    m.add_lwpolyline([(X0, Y0), (X0 + ANTET_W, Y0), (X0 + ANTET_W, Y0 + SERIT_H), (X0, Y0 + SERIT_H)], close=True,
                     dxfattribs={'layer': 'ROTAS-PAFTA'})
    yerlesim_ciz(m, X0 + ANTET_W + 50, Y0, 1682, SERIT_H, {}, None)
    d.saveas(out)
    print(out)
