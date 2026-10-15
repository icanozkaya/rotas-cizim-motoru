# -*- coding: utf-8 -*-
"""sihhi2/detay.py — SIHHİ DETAYLAR bloğu (2000 × 1500, saf geometri) + WC havalandırma izometrisi.

Referans: new_block.dxf son paftası (`SIHHİ DETAYLAR` bloğu 1998,6 × 1500; sol alt 268157,4 / −444026,6) — içerik ve
düzen kullanıcının bloğundan ölçüldü: sol sütun 4 tablo (TS 1258 çap, TS EN 12056-2 SB, pis su çap, TS 1258 YB/debi),
orta sütun PİSSU / TEMİZ SU TESİSATI LEJANTI (+ ADET), sağda montaj detayları (boru montajı, dirsek-branşman,
kör tapa, döşeme/duvardan geçiş, havalık, alaturka hela, yer süzgeci, tipik eviye, alafranga hela).
MTY bloğu YOK (14.10.2026 B): semboller `motor/deneme/semboller2` (ROTAS saf geometri), detaylar LINE/LWPOLYLINE/ARC.

API
    sihhi_detaylar(msp, x0, y0, adet=None)           2000 × 1500 blok; (x0, y0) sol alt. adet: {blok adı: n} (yoksa sayılır)
    wc_izometri(msp, x0, y0, w_max, h_max, girdi)    wc_havalandirma modülüyle izometri (blok + ölçekli INSERT)
    detay_paftasi(msp, x0, y0, w, h, girdi=None)      üstte izometri, altta SIHHİ DETAYLAR (referans pafta düzeni)
"""
import json
import math
import os
import sys

import ezdxf
from ezdxf import bbox as _bbox

BURASI = os.path.dirname(os.path.abspath(__file__))
DEPO = os.path.abspath(os.path.join(BURASI, '..', '..'))
sys.path.insert(0, BURASI)
sys.path.insert(0, os.path.join(DEPO, 'motor', 'deneme', 'semboller2'))
sys.path.insert(0, os.path.join(DEPO, 'motor', 'deneme', 'wc_havalandirma'))
import sembol2 as S                      # noqa: E402
from antet import Ciz, hazirla, STIL      # noqa: E402

DETAY_W, DETAY_H = 2000.0, 1500.0
KAT = 'ROTAS-DETAY'
KAT_Y = 'ROTAS-DETAY-YAZI'
KAT_T = 'ROTAS-DETAY-TARAMA'
KAT_TAB = 'ROTAS-TABLO'
KAT_TAB_Y = 'ROTAS-TABLO-YAZI'
KATMANLAR = {KAT: 7, KAT_Y: 7, KAT_T: 8, KAT_TAB: 7, KAT_TAB_Y: 7, 'ROTAS-DETAY-BORU': 6, 'ROTAS-DETAY-SU': 5,
             'ROTAS-DETAY-OLCU': 3}

# ------------------------------------------------------------------ tablolar (kullanıcının bloğundan birebir)
TAB_TEMIZ_CAP = (['TEMİZ SU BORULARI ÇAP BELİRLEME TABLOSU', '(TS 1258, BÖLÜM 3.1)'],
                 [('YÜKLEME\nBİRİMİ', 120), ('MAKS. KULLANMA\nDEBİSİ (lt/sn)', 140), ('PPRC BORU\nNOM. ÇAP', 120)],
                 [('0-2.25', '0.38', 'DN20'), ('2.25-7.84', '0.70', 'DN25'), ('7.84-19.36', '1.01', 'DN32'),
                  ('19.36-46.24', '1.70', 'DN40'), ('46.24-108.4', '2.60', 'DN50'), ('108.4-256', '4.00', 'DN63'),
                  ('256-784', '7.00', 'DN75'), ('784-1444', '9.50', 'DN90'), ('1444-4096', '16.00', 'DN110')])
TAB_SB = (['BELİRLİ KULLANMA YERLERİ İÇİN VERİLEN', 'STANDART PİSSU YÜK BİRİMLERİ (SB) DEĞERLERİ', '(TS EN 12056-2:2000, TABLO 2)'],
          [('KULLANMA NOKTASI', 280), ('SB', 100)],
          [('LAVABO', '0.5'), ('WC', '2'), ('DUŞ', '0.7'), ('KÜVET', '0.7'), ('PİSUVAR', '0.8'), ('EVİYE', '4'),
           ('ÇAMAŞIR VE BULAŞIK MAKİNASI', '4'), ('BAHÇE VE GARAJ MUSLUĞU', '5'), ('YER SÜZGECİ', '2'), ('OTOPARK SÜZGECİ', '2')])
TAB_PIS_CAP = (['PİSSU BORULARI ÇAP BELİRLEME TABLOSU', '(TS EN 12056-2:2000, TABLO-4,6,9)'],
               [('YÜKLEME BİRİMİ', 190), ('PP BORU ÇAPI (mm)', 190)],
               [('0-0.8', 'Ø50'), ('0.81-5', 'Ø70'), ('5.1-14', 'Ø100'), ('14.1-17', 'Ø125'), ('17.1-60', 'Ø150'),
                ('61-200', 'Ø200'), ('201-720', 'Ø250'), ('721-2300', 'Ø300')])
TAB_YB = (['BELİRLİ KULLANMA YERLERİ İÇİN VERİLEN STANDART', 'TEMİZ SU YÜK BİRİMLERİ (YB) VE KARŞILIĞI DEBİ DEĞERLERİ',
           '(TS 1258, ÇİZELGE 15)'],
          [('KULLANMA NOKTASI', 220), ('YÜK BİRİMİ', 80), ('DEBİ (lt/sn)', 80)],
          [('LAVABO', '0.5', '0.175'), ('KÜVETLİ BANYO DN15mm', '2.5', '0.40'), ('KÜVETLİ BANYO DN20mm', '16', '1'),
           ('PİSUVAR', '0.25', '0.125'), ('HELA REZERVUARI', '0.5', '0.125'), ('TAHARET MUSLUĞU', '0.25', '-'),
           ('EVİYE (1 GÖZLÜ)', '0.5', '-'), ('EVİYE (2 GÖZLÜ)', '1', '-'), ("ŞOFBEN (10 lt/dk'ya kadar)", '0.5', '0.175'),
           ("ŞOFBEN (16 lt/dk'ya kadar)", '1', '0.25'), ("ŞOFBEN (26 lt/dk'ya kadar)", '3', '0.43'),
           ('TERMOSİFON', '2.5', '0.40'), ('ÇAMAŞIR BULAŞIK MAKİNASI', '1', '0.40')])

# ------------------------------------------------------------------ lejantlar (referans bloğun listesi + ROTAS sembolü)
# (açıklama, sembol: 'boru:<katman>' | ROTAS blok adı | None)
LEJANT_PIS = [
    ('PİSSU BORUSU', 'boru:ROTAS-SIHHI-PIS-SU'),
    ('PİSSU KOLON NUMARASI (P1, P2 ...)', 'ROTAS-SB-KOLON-NO'),
    ('PİSSU KOLONU (İNİŞ) — PLAN', 'ROTAS-SB-KOLON-PIS'),
    ('PİSSU RÖGARI 70x70', 'ROTAS-SB-ROGAR'),
    ('YAĞMUR SUYU BORUSU', 'boru:ROTAS-SIHHI-YAGMUR'),
    ('YAĞMUR SUYU KOLON NUMARASI (YB1 ...)', 'ROTAS-SB-KOLON-YAGMUR'),
    ('ISLAK HACİM SÜZGECİ (PİK DÖKÜM IZGARALI)', 'ROTAS-SB-YER-SUZGECI'),
    ('BALKON SÜZGECİ (YAĞMUR HATTINA)', 'ROTAS-SB-BALKON-SUZGECI'),
    ('TEMİZLEME KAPAĞI (T.K.)', 'ROTAS-SB-TEMIZLEME-KAPAGI'),
    ('PİSSU HAVALIK VE ŞAPKASI', 'ROTAS-SB-HAVALIK'),
    ('KEND. REZERVUARLI ALAFRANGA HELA VE TES.', 'ROTAS-KS-KLOZET'),
    ('ALATURKA HELA TAŞI VE REZERVUARI', 'ROTAS-KS-HELA'),
    ('LAVABO', 'ROTAS-KS-LAVABO'),
    ('EVİYE', 'ROTAS-KS-EVIYE'),
    ('DUŞ TESİSATI', 'ROTAS-KS-DUS'),
    ('KÜVET', 'ROTAS-KS-KUVET'),
    ('ÇAMAŞIR MAKİNESİ', 'ROTAS-KS-CAMASIR-MAKINESI'),
    ('BULAŞIK MAKİNESİ', 'ROTAS-KS-BULASIK-MAKINESI'),
    ('PVC ÇATAL 45°', 'ROTAS-KS-PVC-CATAL'),
    ('PİSSU ÇUKURU VE PİSSU (DALGIÇ) POMPASI', 'ROTAS-DH-DALGIC-POMPA'),
]
LEJANT_TEMIZ = [
    ('SOĞUK SU BORUSU', 'boru:ROTAS-SIHHI-SOGUK-SU'),
    ('SICAK SU BORUSU', 'boru:ROTAS-SIHHI-SICAK-SU'),
    ('SİRKÜLASYON SU BORUSU', 'boru:ROTAS-SIHHI-SIRKULASYON'),
    ('TEMİZ SU KOLONU / NUMARASI', 'ROTAS-SB-KOLON-TEMIZ'),
    ('SOĞUK SU MUSLUĞU - ARA MUSLUK (ARMATÜR BAĞLANTISI)', 'ROTAS-SB-ARMATUR-SU'),
    ('KÜRESEL VANA', 'ROTAS-SB-KURESEL-VANA'),
    ('ÇEK VALF', 'ROTAS-SB-CEKVALF'),
    ('PİSLİK TUTUCU', 'ROTAS-SB-PISLIK-TUTUCU'),
    ('SOĞUK SU SAYACI', 'ROTAS-SB-SU-SAYACI'),
    ('BASINÇ DÜŞÜRÜCÜ VANA', 'ROTAS-SB-BASINC-DUSURUCU'),
    ('SAYAÇ GRUBU (VANA-SAYAÇ-ÇEKVALF-VANA)', 'ROTAS-KS-SAYAC-GRUBU'),
    ('ŞAMANDIRALI VANA (DEPO GİRİŞİ)', 'ROTAS-DH-SAMANDIRALI-VANA'),
    ('KULLANMA SUYU DEPOSU', 'ROTAS-KS-SU-DEPOSU'),
    ('HİDROFOR GRUBU', 'ROTAS-DH-HIDROFOR'),
    ('MEMBRANLI TANK', 'ROTAS-DH-MEMBRANLI-TANK'),
    ('KOMBİ (SICAK SU ÜRETİCİ)', 'ROTAS-KS-KOMBI'),
    ('TERMOSİFON', 'ROTAS-KS-TERMOSIFON'),
    ('WC ASPİRATÖRÜ (MEKANİK HAVALANDIRMA)', 'ROTAS-HV-ASPIRATOR'),
    ('MEKANİK HAVALANDIRMA ŞAFTI', 'ROTAS-HV-SAFT'),
    ('ÇATI TİPİ FAN', 'ROTAS-HV-CATI-FANI'),
]


def katmanlar(doc):
    hazirla(doc)
    S.katmanlar(doc)
    for ad, renk in KATMANLAR.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk)


# ============================================================================= adet + eşdeğer semboller
# plan.py (sihhi2) kendi ROTAS-S2-* bloklarını kullanır; lejant satırı semboller2 adıyla tutulur, sayım ve lejant
# görünümü için eşdeğeri kullanılır (lejantta çizimdeki sembolün aynısı).
ESDEGER = {
    'ROTAS-S2-KURESEL-VANA': 'ROTAS-SB-KURESEL-VANA',
    'ROTAS-S2-PIS-KOLON': 'ROTAS-SB-KOLON-PIS',
    'ROTAS-S2-YER-SUZGECI': 'ROTAS-SB-YER-SUZGECI',
    'ROTAS-S2-BALKON-SUZGECI': 'ROTAS-SB-BALKON-SUZGECI',
    'ROTAS-S2-KOLON-NO': 'ROTAS-SB-KOLON-NO',
    'ROTAS-S2-KOLON-NO-YAGMUR': 'ROTAS-SB-KOLON-YAGMUR',
    'ROTAS-S2-ASPIRATOR': 'ROTAS-HV-ASPIRATOR',
    # 15.10 (D) planda sayaç grubu / şebeke girişi (besleme.py)
    'ROTAS-S2-CEKVALF': 'ROTAS-SB-CEKVALF',
    'ROTAS-S2-PISLIK-TUTUCU': 'ROTAS-SB-PISLIK-TUTUCU',
    'ROTAS-S2-SU-OLCER': 'ROTAS-SB-SU-SAYACI',
}
# numara balonu: adet = farklı numara sayısı (aynı kolon her katta tekrar eder)
NUMARALI = {'ROTAS-SB-KOLON-NO', 'ROTAS-SB-KOLON-YAGMUR', 'ROTAS-SB-KOLON-TEMIZ'}
_HARIC_KAT = ('ROTAS-LEJANT', 'ROTAS-DETAY', 'ROTAS-TABLO')


def adet_say(doc):
    """{semboller2 blok adı: adet} — modelspace INSERT'leri (lejant/detay katmanları hariç), ROTAS-S2 eşdeğerleri dahil.
    Kolon/YB numara balonları farklı numara sayısıyla; pis su kolonu adedi = farklı P numarası (varsa)."""
    adet, numara = {}, {}
    for (_, n), v in S.kullanim_say(doc).items():
        adet[n] = adet.get(n, 0) + v
    for e in doc.modelspace().query('INSERT'):
        if e.dxf.layer.startswith(_HARIC_KAT):
            continue
        ad = ESDEGER.get(e.dxf.name, e.dxf.name)
        if ad in NUMARALI:
            no = next((x.dxf.text.strip() for x in e.attribs if x.dxf.tag == 'NO' and x.dxf.text.strip()), None)
            if no:
                numara.setdefault(ad, set()).add(no)
        if e.dxf.name in ESDEGER:
            adet[ad] = adet.get(ad, 0) + 1
    for ad, k in numara.items():
        adet[ad] = len(k)
    if numara.get('ROTAS-SB-KOLON-NO'):
        adet['ROTAS-SB-KOLON-PIS'] = len(numara['ROTAS-SB-KOLON-NO'])
    return adet


def kullanilan_esdeger(doc, sem):
    """sem (semboller2 adı) çizimde ROTAS-S2 eşdeğeriyle kullanılıyorsa o blok adı."""
    for s2, sb in ESDEGER.items():
        if sb == sem and s2 in doc.blocks and len(doc.modelspace().query('INSERT[name=="%s"]' % s2)):
            return s2
    return None


def blok_hucre(msp, ad, cx, cy, gen, yuk, katman, buyut_max=2.0, pay=0.8):
    """Herhangi bir bloğu hücreye sığdırarak ortalı koyar (ATTDEF hariç kapsam)."""
    b = _bbox.extents([e for e in msp.doc.blocks.get(ad) if e.dxftype() != 'ATTDEF'], fast=True)
    if not b.has_data:
        return None
    w, h = max(b.extmax.x - b.extmin.x, 1e-3), max(b.extmax.y - b.extmin.y, 1e-3)
    s = min(gen * pay / w, yuk * pay / h, buyut_max)
    mx, my = (b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2
    return msp.add_blockref(ad, (cx - mx * s, cy - my * s), dxfattribs={'layer': katman, 'xscale': s, 'yscale': s})


# ============================================================================= tablo
def tablo(c, x0, y_ust, basliklar, kolonlar, satirlar, rh=24.0, h_bas=12.0, h_sat=9.6, h_tit=11.1):
    """Referans tarzı tablo (sol üst x0, y_ust). Dönüş: alt y."""
    W = sum(w for _, w in kolonlar)
    y = y_ust
    for i, s in enumerate(basliklar):
        c.text(s, x0 + W / 2, y - 8, h_tit if i < len(basliklar) - 1 else h_tit * 0.9, 'TC', KAT_TAB_Y, w=0.8)
        y -= h_tit * 1.9
    y -= 4
    n_sat_bas = max(len(k.split('\n')) for k, _ in kolonlar)
    SA = h_bas * 1.45                                   # başlık satır aralığı (yazılar birbirine binmez)
    HB = 18 + SA * (n_sat_bas - 1)
    c.rect(x0, y - HB, x0 + W, y, KAT_TAB)
    x = x0
    for k, w in kolonlar:
        sat = k.split('\n')
        for j, s in enumerate(sat):
            c.text(s, x + w / 2, y - HB / 2 + (len(sat) - 1) * SA / 2 - j * SA, h_bas, 'MC', KAT_TAB_Y, w=0.8)
        x += w
        if x < x0 + W - 1:
            c.line(x, y - HB, x, y, KAT_TAB)
    y -= HB
    yt = y
    for r in satirlar:
        c.line(x0, y - rh, x0 + W, y - rh, KAT_TAB)
        x = x0
        for (k, w), v in zip(kolonlar, r):
            al = 'ML' if (len(str(v)) > 8 and k.startswith('KULLANMA')) else 'MC'
            c.text(v, (x + 6) if al == 'ML' else x + w / 2, y - rh / 2, h_sat, al, KAT_TAB_Y, w=0.8)
            x += w
        y -= rh
    c.line(x0, yt, x0, y, KAT_TAB)
    c.line(x0 + W, yt, x0 + W, y, KAT_TAB)
    x = x0
    for k, w in kolonlar[:-1]:
        x += w
        c.line(x, yt, x, y, KAT_TAB)
    return y


# ============================================================================= lejant (referans düzeni + ADET)
def lejant(c, x0, y_ust, baslik, satirlar, adet, W_S=60.0, W_A=200.0, W_N=42.0, rh=24.0):
    """SEMBOL | AÇIKLAMA | ADET tablosu; semboller semboller2 blokları / boru çizgisi. Dönüş: alt y."""
    msp = c.m
    W = W_S + W_A + W_N
    c.text(baslik, x0 + W / 2, y_ust - 8, 11.1, 'TC', KAT_TAB_Y, w=0.85)
    y = y_ust - 26
    c.rect(x0, y - 18, x0 + W, y, KAT_TAB)
    for s, xx in (('SEMBOL', x0 + W_S / 2), ('AÇIKLAMA', x0 + W_S + W_A / 2), ('ADET', x0 + W_S + W_A + W_N / 2)):
        c.text(s, xx, y - 9, 8, 'MC', KAT_TAB_Y)
    y -= 18
    yt = y
    for ac, sem in satirlar:
        c.line(x0, y - rh, x0 + W, y - rh, KAT_TAB)
        cy = y - rh / 2
        n = None
        if sem and sem.startswith('boru:'):
            kat = sem[5:]
            if kat not in msp.doc.layers:
                S.katmanlar(msp.doc)
            ln = msp.add_line(c.p(x0 + 8, cy), c.p(x0 + W_S - 8, cy), dxfattribs={'layer': kat})
            ln.dxf.ltscale = 8.0
        elif sem:
            esd = kullanilan_esdeger(msp.doc, sem)
            if esd:                          # çizimde kullanılan sembolün AYNISI (ör. plan.py ROTAS-S2-* bloğu)
                blok_hucre(msp, esd, *c.p(x0 + W_S / 2, cy), W_S, rh, katman=S.LEJ_SEM, buyut_max=2.0)
            else:
                S.ekle(msp.doc, [sem])
                S.sembol_hucre(msp, sem, *c.p(x0 + W_S / 2, cy), W_S, rh, katman=S.LEJ_SEM, buyut_max=2.0)
            n = adet.get(sem, 0) if adet is not None else None
        c.text(ac, x0 + W_S + 5, cy, 8 if len(ac) <= 40 else 6.8, 'ML', KAT_TAB_Y, w=0.8)
        c.text('-' if not n else str(n), x0 + W_S + W_A + W_N / 2, cy, 8, 'MC', KAT_TAB_Y)
        y -= rh
    for x in (x0, x0 + W_S, x0 + W_S + W_A, x0 + W):
        c.line(x, yt, x, y, KAT_TAB)
    return y


# ============================================================================= detay çizim yardımcıları
def _boru(c, p0, p1, d, kat='ROTAS-DETAY-BORU'):
    """Çift çizgili boru (eksen p0→p1, çap d)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1e-6:
        return
    nx, ny = -(y1 - y0) / L * d / 2, (x1 - x0) / L * d / 2
    c.line(x0 + nx, y0 + ny, x1 + nx, y1 + ny, kat)
    c.line(x0 - nx, y0 - ny, x1 - nx, y1 - ny, kat)


def _duvar(c, x0, y0, x1, y1):
    c.rect(x0, y0, x1, y1, KAT)
    c.tarama(x0, y0, x1, y1, 7.0, KAT_T)


def _kilavuz(c, metin, px, py, tx, ty, al='ML', h=6.0):
    """Kılavuz çizgili etiket: (px, py) gösterilen nokta, (tx, ty) yazı başlangıcı."""
    c.line(px, py, tx - (3 if al[1] == 'L' else -3), ty, 'ROTAS-DETAY-OLCU')
    c.text(metin, tx, ty, h, al, KAT_Y, w=0.8)


def _olcu(c, x0, y0, x1, y1, metin, ofset=10.0, h=5.5):
    """Basit ölçü çizgisi (yatay ya da düşey), yazı ortada."""
    k = 'ROTAS-DETAY-OLCU'
    if abs(y1 - y0) < 1e-6:
        c.line(x0, y0 + ofset, x1, y0 + ofset, k)
        for x in (x0, x1):
            c.line(x, y0, x, y0 + ofset + 4, k)
            c.line(x - 2, y0 + ofset - 2, x + 2, y0 + ofset + 2, k)
        c.text(metin, (x0 + x1) / 2, y0 + ofset + 2, h, 'BC', KAT_Y)
    else:
        c.line(x0 + ofset, y0, x0 + ofset, y1, k)
        for y in (y0, y1):
            c.line(x0, y, x0 + ofset + 4, y, k)
            c.line(x0 + ofset - 2, y - 2, x0 + ofset + 2, y + 2, k)
        c.text(metin, x0 + ofset - 2, (y0 + y1) / 2, h, 'BC', KAT_Y, rot=90)


def _baslik(c, metin, x, y, h=10.6):
    c.text(metin, x, y, h, 'BC', KAT_Y, w=0.85)


def _klemens(c, x, y, d, duvar_x, kat=KAT):
    """Contalı kelepçe: boru çevresinde halka + duvara dübel."""
    c.rect(x - d / 2 - 3, y - 4, x + d / 2 + 3, y + 4, kat)
    c.rect(duvar_x, y - 2.5, x - d / 2 - 3, y + 2.5, kat)
    c.rect(duvar_x - 10, y - 1.5, duvar_x, y + 1.5, kat)      # dübel


# ============================================================================= detaylar
def detay_boru_montaj(c):
    """BORU MONTAJ DETAYI: duvar + düşey pis su borusu + contalı kelepçe + dübel (alan 380 × 140)."""
    _duvar(c, 40, 10, 58, 120)
    _boru(c, (120, 8), (120, 122), 16)
    _klemens(c, 120, 45, 16, 58)
    _klemens(c, 120, 95, 16, 58)
    _kilavuz(c, 'DÜBEL', 48, 97, 150, 118, 'ML')
    _kilavuz(c, 'CONTALI KELEPÇE', 131, 95, 150, 100, 'ML')
    _kilavuz(c, 'PİSSU BORUSU', 128, 70, 150, 78, 'ML')
    _kilavuz(c, 'DUVAR', 49, 30, 150, 40, 'ML')
    _baslik(c, 'BORU MONTAJ DETAYI', 190, -14)


def detay_dirsek_bransman(c, tapa=False):
    """DİRSEK VE BRANŞMAN / KÖR TAPA BAĞLANTI DETAYI (alan 180 × 170)."""
    _duvar(c, 10, 5, 25, 160)
    xb = 90
    _boru(c, (xb, 5), (xb, 160), 16)
    # 45° çatal: gövdeden sağ yukarı
    bx, by = xb, 80
    ex, ey = bx + 46, by + 46
    _boru(c, (bx + 6, by + 6), (ex, ey), 12)
    c.line(bx + 8, by - 2, bx + 8, by + 14, KAT)          # çatal ağız çizgileri
    c.line(bx + 8, by + 14, bx + 14, by + 20, KAT)
    _klemens(c, xb, 40, 16, 25)
    _klemens(c, xb, 130, 16, 25)
    if tapa:
        # branşman ucu tapa + conta
        c.rect(ex - 6, ey - 6, ex + 8, ey + 8, KAT)
        c.line(ex - 3, ey + 1, ex + 3, ey - 5, KAT)
        c.line(ex - 1, ey + 3, ex + 5, ey - 3, KAT)
        _kilavuz(c, 'TAPA', ex + 8, ey + 4, 120, 150, 'ML')
        _kilavuz(c, 'CONTA', ex - 2, ey - 2, 120, 138, 'ML')
        _kilavuz(c, '45° ÇATAL', bx + 20, by + 18, 120, 60, 'ML')
        _kilavuz(c, 'PİSSU BORUSU', xb - 8, 60, 120, 48, 'ML')
        _baslik(c, 'KÖR TAPA BAĞLANTI DETAYI', 95, -14)
    else:
        _kilavuz(c, '45° ÇATAL', bx + 20, by + 18, 120, 150, 'ML')
        _kilavuz(c, 'CONTALI KELEPÇE', xb + 11, 130, 120, 118, 'ML')
        _kilavuz(c, 'DÜBEL', 20, 42, 120, 24, 'ML')
        _kilavuz(c, 'PİSSU BORUSU', xb + 8, 100, 120, 60, 'ML')
        _baslik(c, 'DİRSEK VE BRANŞMAN BAĞLANTI DETAYI', 95, -14)


def detay_doseme_duvar(c):
    """DÖŞEME VE DUVARDAN GEÇİŞ (alan 200 × 330): üstte döşeme, altta duvar geçişi."""
    # --- döşemeden geçiş (y 190..330)
    c.rect(20, 250, 180, 268, KAT)
    c.tarama(20, 250, 180, 268, 7.0, KAT_T)
    c.line(20, 272, 180, 272, KAT)         # kaplama
    c.line(20, 246, 180, 246, KAT)         # sıva (tavan)
    _boru(c, (100, 200), (100, 322), 16)
    _boru(c, (100, 240), (100, 282), 28)   # 2 boy büyük boru (kovan)
    _olcu(c, 118, 272, 118, 282, '10', 14, 4.5)
    _kilavuz(c, 'KAPLAMA', 60, 272, 130, 310, 'ML')
    _kilavuz(c, 'DÖŞEME', 50, 259, 130, 296, 'ML')
    _kilavuz(c, '2 BOY BÜYÜK BORU', 114, 276, 130, 240, 'ML')
    _kilavuz(c, 'SIVA', 50, 246, 130, 226, 'ML')
    _baslik(c, 'DÖŞEMEDEN GEÇİŞ', 100, 184, 7)
    # --- duvardan geçiş (y 10..170)
    _duvar(c, 90, 30, 110, 150)
    c.line(86, 30, 86, 150, KAT)
    c.line(114, 30, 114, 150, KAT)         # sıva
    _boru(c, (20, 90), (180, 90), 16)
    _boru(c, (80, 90), (120, 90), 28)
    _kilavuz(c, 'SIVA', 86, 120, 20, 150, 'ML')
    _kilavuz(c, 'DUVAR', 100, 140, 130, 150, 'ML')
    _kilavuz(c, '2 BOY BÜYÜK BORU', 110, 104, 120, 125, 'ML')
    _kilavuz(c, 'SIVA', 114, 60, 130, 50, 'ML')
    _baslik(c, 'DUVARDAN GEÇİŞ', 100, 6, 7)
    _baslik(c, 'DÖŞEME VE DUVARDAN GEÇİŞ', 100, -14)


def detay_havalik(c):
    """HAVALIK DETAYI (alan 300 × 330)."""
    # çatı döşemesi
    c.rect(20, 120, 280, 140, KAT)
    c.tarama(20, 120, 280, 140, 8.0, KAT_T)
    # betonarme parça (kaide)
    c.rect(120, 140, 180, 172, KAT)
    c.tarama(120, 140, 180, 172, 6.0, KAT_T)
    _boru(c, (150, 40), (150, 290), 16)          # havalık borusu
    _boru(c, (150, 172), (150, 262), 24)         # PVC güneşten koruma kaplaması
    # sızdırmaz boyun + mastik
    c.pl([(132, 172), (168, 172), (164, 186), (136, 186)], KAT, True)
    c.pl([(136, 186), (164, 186), (162, 192), (138, 192)], KAT, True)
    # havalık şapkası
    c.pl([(132, 290), (168, 290), (160, 304), (140, 304)], KAT, True)
    c.rect(140, 304, 160, 310, KAT)
    c.line(142, 296, 158, 296, KAT)
    _kilavuz(c, 'HAVALIK ŞAPKASI', 168, 298, 200, 310, 'ML')
    _kilavuz(c, 'PVC GÜNEŞTEN KORUMA KAPLAMASI', 162, 240, 200, 280, 'ML')
    _kilavuz(c, 'KENDİ YAPISINDAN PVC DOLGU PARÇASI', 162, 215, 200, 262, 'ML')
    _kilavuz(c, 'SIZDIRMAZ BOYUN', 164, 189, 200, 232, 'ML')
    _kilavuz(c, 'MASTİK PARÇA', 165, 177, 200, 214, 'ML')
    _kilavuz(c, 'BETONARME PARÇA', 175, 160, 200, 196, 'ML')
    _kilavuz(c, 'HAVALIK BORUSU', 158, 70, 200, 90, 'ML')
    _kilavuz(c, 'ÇATI DÖŞEMESİ', 60, 130, 20, 100, 'ML')
    c.text('* DİKKAT: BU DETAY PRENSİP OLARAK VERİLMİŞ OLUP ÇATI KESİTLERİ VE KAPLAMA', 150, 22, 5.2, 'BC', KAT_Y, w=0.8)
    c.text('DETAYINDA MİMARİ DETAYLAR ESAS ALINACAKTIR.', 150, 12, 5.2, 'BC', KAT_Y, w=0.8)
    _baslik(c, 'HAVALIK DETAYI', 150, -14)


def detay_alaturka(c):
    """ALATURKA HELA TAŞI DETAYI: yan görünüş + üst görünüş (alan 460 × 330)."""
    # --- yan görünüş
    c.rect(10, 120, 250, 136, KAT)                      # döşeme
    c.tarama(10, 120, 250, 136, 8.0, KAT_T)
    c.line(10, 138, 250, 138, KAT)                      # bitmiş döşeme
    _duvar(c, 250, 110, 268, 330)
    # hela taşı (döşemeye gömülü)
    c.pl([(70, 138), (170, 138), (160, 114), (80, 114)], KAT, True)
    c.arc(120, 118, 14, 180, 360, KAT)                  # sifon çanağı
    _boru(c, (120, 104), (120, 60), 20)                 # Ø100 iniş
    _boru(c, (120, 60), (40, 60), 20)                   # yatay pis su borusu
    c.line(100, 62, 120, 42, KAT)                       # 45° dirsek izi
    # yüksek rezervuar + yıkama borusu
    c.rect(200, 290, 248, 318, KAT)
    c.line(200, 310, 248, 310, KAT)
    _boru(c, (224, 290), (224, 150), 6)
    c.line(224, 150, 168, 140, KAT)
    # taharet musluğu
    c.circle(236, 175, 4, KAT)
    c.line(232, 175, 220, 160, KAT)
    _olcu(c, 268, 138, 268, 318, '1070', 22, 5)
    _olcu(c, 70, 114, 70, 138, '220', -30, 4.5)
    _olcu(c, 70, 138, 170, 138, '600', 160, 5)
    _kilavuz(c, 'REZERVUAR (YÜKSEK)', 248, 304, 280, 322, 'ML')
    _kilavuz(c, 'TAHARET MUSLUĞU', 240, 175, 280, 200, 'ML')
    _kilavuz(c, 'YUMUŞAK POLİETİLEN BORU', 226, 220, 280, 240, 'ML')
    _kilavuz(c, 'KÜRESEL VANA Ø20', 226, 270, 280, 280, 'ML')
    _kilavuz(c, 'HELA TAŞI', 150, 130, 180, 180, 'ML')
    _kilavuz(c, 'BİTMİŞ DÖŞEME', 40, 138, 20, 160, 'ML')
    _kilavuz(c, 'PİS SU BORUSU Ø100mm.', 60, 50, 20, 30, 'ML')
    _kilavuz(c, 'GEÇME MUFLU CONTALI BAĞLANTI', 130, 90, 180, 100, 'ML')
    _baslik(c, 'YAN GÖRÜNÜŞ', 130, 2, 7)
    # --- üst görünüş
    ox = 330
    c.rect(ox, 150, ox + 90, 300, KAT)
    c.pl([(ox + 15, 170), (ox + 75, 170), (ox + 70, 280), (ox + 20, 280)], KAT, True)
    c.m.add_ellipse(c.p(ox + 45, 215), major_axis=(0, 35), ratio=0.5, dxfattribs={'layer': KAT})
    c.circle(ox + 45, 265, 6, KAT)                       # yıkama girişi
    c.circle(ox + 85, 240, 3, KAT)                       # taharet musluğu
    _olcu(c, ox, 150, ox + 90, 150, '600', -16, 4.5)
    _olcu(c, ox + 90, 150, ox + 90, 300, '1070', 12, 4.5)
    _kilavuz(c, 'TAHARET MUSLUĞU', ox + 88, 240, ox + 110, 270, 'ML')
    _kilavuz(c, 'PİS SU BORUSU Ø100', ox + 45, 180, ox + 110, 120, 'ML')
    _baslik(c, 'ÜST GÖRÜNÜŞ', ox + 45, 104, 7)
    _baslik(c, 'ALATURKA HELA TAŞI DETAYI', 230, -14)


def detay_yer_suzgeci(c):
    """YER SÜZGECİ MONTAJ DETAYI (alan 380 × 290)."""
    c.rect(20, 120, 360, 150, KAT)
    c.tarama(20, 120, 360, 150, 8.0, KAT_T)
    c.line(20, 156, 150, 156, KAT)
    c.line(250, 156, 360, 156, KAT)                      # kaplama (süzgeç çevresinde kesik)
    c.line(20, 150, 150, 150, KAT)
    c.line(250, 150, 360, 150, KAT)
    # süzgeç gövdesi (huni) + ızgara çerçevesi
    c.pl([(150, 156), (250, 156), (230, 96), (170, 96)], KAT, True)
    c.rect(140, 156, 260, 164, KAT)                      # hareketli üst çerçeve
    for x in range(150, 251, 12):
        c.line(x, 157.5, x, 162.5, KAT)                  # ızgara
    c.pl([(176, 146), (224, 146), (216, 110), (184, 110)], KAT, True)   # koku önleyici (çan)
    c.circle(165, 140, 3, KAT)
    c.circle(235, 140, 3, KAT)                           # O-ring
    _boru(c, (230, 108), (330, 108), 10)                 # çıkış Ø50 (yana)
    c.line(230, 103, 230, 113, KAT)
    _olcu(c, 140, 164, 260, 164, 'A', 18, 6)
    _olcu(c, 150, 156, 250, 156, 'B', 40, 6)
    _olcu(c, 170, 96, 230, 96, 'C', -14, 6)
    _olcu(c, 260, 96, 260, 156, 'H', 60, 6)
    _olcu(c, 330, 103, 330, 113, 'Ø50', 14, 6)
    _olcu(c, 150, 96, 150, 110, 'h', -40, 6)
    _kilavuz(c, 'O-RİNG', 238, 140, 290, 180, 'ML')
    _kilavuz(c, 'KOKU ÖNLEYİCİ', 215, 128, 290, 200, 'ML')
    _kilavuz(c, 'PİK DÖKÜM IZGARA', 200, 163, 290, 220, 'ML')
    c.text('HAREKETLİ ÜST ÇERÇEVE', 40, 60, 7, 'ML', KAT_Y)
    c.text('DERZLERE AYARLANABİLİR.', 40, 48, 7, 'ML', KAT_Y)
    _baslik(c, 'YER SÜZGECİ MONTAJ DETAYI', 190, -14)


def detay_eviye(c):
    """TİPİK EVİYE MONTAJI (alan 540 × 600)."""
    _duvar(c, 440, 20, 460, 560)
    c.rect(10, 50, 440, 66, KAT)                         # döşeme
    c.tarama(10, 50, 440, 66, 8.0, KAT_T)
    c.line(10, 70, 440, 70, KAT)                         # bitmiş döşeme
    # tezgah + dolap + eviye
    c.rect(120, 300, 440, 312, KAT)
    c.rect(130, 70, 430, 300, KAT)
    c.rect(240, 232, 390, 300, KAT)                      # eviye teknesi
    c.line(240, 300, 390, 300, KAT)
    # armatür
    c.rect(405, 312, 413, 340, KAT)
    c.pl([(409, 340), (409, 352), (360, 352), (360, 342)], KAT)
    # sıcak / soğuk su besleme (duvardan)
    for yy, ad in ((380, 'SICAK'), (365, 'SOĞUK')):
        _boru(c, (440, yy), (409, yy), 5, 'ROTAS-DETAY-SU')
        c.line(409, yy, 409, 340, 'ROTAS-DETAY-SU')
        c.pl([(428, yy - 5), (436, yy), (428, yy + 5)], KAT, True)     # kapama vanası (papyon)
        c.pl([(420, yy - 5), (428, yy), (420, yy + 5)], KAT, True)
    # drenaj: P sifon + temizleme tapası + duvara
    _boru(c, (315, 232), (315, 180), 10)
    c.arc(330, 180, 15, 180, 360, KAT)
    c.arc(330, 180, 5, 180, 360, KAT)
    _boru(c, (345, 180), (345, 200), 10)
    _boru(c, (345, 200), (440, 200), 10)
    c.rect(322, 160, 338, 166, KAT)                      # temizleme tapası
    # ana drenaj + havalandırma borusu (duvar içinde)
    _boru(c, (450, 20), (450, 560), 10)
    c.line(445, 200, 455, 200, KAT)
    _kilavuz(c, 'EVİYE', 300, 260, 180, 280, 'MR')
    _kilavuz(c, 'ARMATÜR', 409, 352, 300, 400, 'MR')
    _kilavuz(c, 'SICAK VE SOĞUK SU BESLEME BORULARI', 424, 385, 300, 440, 'MR')
    _kilavuz(c, 'KAPAMA VANASI (DÜZ BORU VE VANA KROMAJLI)', 432, 360, 300, 420, 'MR')
    _kilavuz(c, 'HAVALANDIRMA BORUSU (PVC)', 455, 480, 480, 520, 'ML')
    _kilavuz(c, 'ANA DRENAJ', 455, 120, 480, 140, 'ML')
    _kilavuz(c, 'DRENAJ', 400, 200, 480, 300, 'ML')
    _kilavuz(c, 'TEMİZLEME TAPASI İLE P SİFONU', 330, 163, 180, 140, 'MR')
    _kilavuz(c, 'BİTMİŞ DÖŞEME', 60, 70, 60, 100, 'ML')
    c.satirlar(['TEMİZLEME TAPASI İLE P SİFONU, BESLEME', 'BORULARI, KESME VANALARI, DIŞARIDAKİ DREN',
                'BORULARI VE DUVAR ROZETLERİ KROM KAPLAMA', 'OLACAKTIR.'], 480, 260, 5.5, 'TL', KAT_Y, aralik=10)
    _baslik(c, 'TİPİK EVİYE MONTAJI', 270, -14)


def detay_alafranga(c):
    """ALAFRANGA HELA TAŞI DETAYI (alan 560 × 600)."""
    _duvar(c, 500, 20, 520, 560)
    c.rect(10, 80, 500, 100, KAT)
    c.tarama(10, 80, 500, 100, 8.0, KAT_T)
    c.line(10, 104, 500, 104, KAT)
    # klozet profili
    c.pl([(300, 104), (300, 150), (280, 160), (270, 200), (290, 220), (400, 220), (420, 200), (420, 104)], KAT, True)
    c.m.add_ellipse(c.p(335, 215), major_axis=(50, 0), ratio=0.18, dxfattribs={'layer': KAT})
    c.rect(400, 220, 450, 320, KAT)                      # rezervuar tankı
    c.rect(405, 320, 445, 326, KAT)                      # kapak
    c.arc(330, 150, 22, 0, 180, KAT)                     # sifon kıvrımı
    c.arc(330, 150, 10, 0, 180, KAT)
    # pis su: Ø100 döşeme altı -> 45° -> ana drenaj
    _boru(c, (352, 150), (352, 60), 20)
    _boru(c, (352, 60), (282, 60), 20)
    _boru(c, (282, 60), (230, 30), 20)
    _boru(c, (230, 30), (40, 30), 20)
    # soğuk su besleme (duvardan) + kapama vanası + rozet
    _boru(c, (500, 300), (450, 300), 5, 'ROTAS-DETAY-SU')
    c.pl([(474, 295), (482, 300), (474, 305)], KAT, True)
    c.pl([(466, 295), (474, 300), (466, 305)], KAT, True)
    c.rect(494, 292, 500, 308, KAT)
    # havalandırma borusu (duvar içinde, çatıya)
    _boru(c, (510, 40), (510, 560), 10)
    c.line(505, 60, 515, 60, KAT)
    c.pl([(505, 560), (515, 560), (518, 570), (502, 570)], KAT, True)
    _kilavuz(c, 'ÇATIDAN HAVALANDIRMA', 515, 540, 400, 500, 'MR')
    _kilavuz(c, 'HAVALANDIRMA BORUSU (PVC)', 505, 420, 400, 440, 'MR')
    _kilavuz(c, 'REZERVUAR TANKI', 425, 310, 300, 370, 'MR')
    _kilavuz(c, 'SOĞUK SU BESLEME', 460, 300, 300, 340, 'MR')
    _kilavuz(c, 'KAPAMA VANASI (DÜZ BORU VE VANA KROMAJLI)', 474, 305, 300, 400, 'MR')
    _kilavuz(c, 'ROZET', 494, 308, 400, 470, 'MR')
    _kilavuz(c, 'TUVALET TAŞI', 335, 200, 200, 250, 'MR')
    _kilavuz(c, 'DÖŞEME', 200, 90, 120, 130, 'MR')
    _kilavuz(c, 'ANA DRENAJ', 120, 30, 60, 50, 'MR')
    _kilavuz(c, 'PİS SU BORUSU Ø100', 352, 100, 250, 180, 'MR')
    _baslik(c, 'ALAFRANGA HELA TAŞI DETAYI', 280, -14)


# ============================================================================= SIHHİ DETAYLAR bloğu
def sihhi_detaylar(msp, x0, y0, adet=None, cerceve=True):
    """2000 × 1500 SIHHİ DETAYLAR bloğu (sol alt x0, y0). adet: {ROTAS blok adı: n}; None → belgeden sayılır.
    Dönüş: dict(w, h, yazilar)."""
    doc = msp.doc
    katmanlar(doc)
    if adet is None:
        adet = adet_say(doc)
    c = Ciz(msp, x0, y0, KAT, KAT_Y)
    if cerceve:
        c.rect(0, 0, DETAY_W, DETAY_H, KAT)
    c.text('SIHHİ DETAYLAR', DETAY_W / 2, DETAY_H - 6, 16, 'TC', KAT_Y, w=0.9)
    # ---- sol sütun: tablolar
    y = DETAY_H - 36
    for T in (TAB_TEMIZ_CAP, TAB_SB, TAB_PIS_CAP, TAB_YB):
        y = tablo(c, 14, y, *T) - 26
    # ---- orta sütun: lejantlar
    y = lejant(c, 420, DETAY_H - 36, 'PİSSU TESİSATI LEJANTI', LEJANT_PIS, adet) - 30
    lejant(c, 420, y, 'TEMİZ SU TESİSATI LEJANTI', LEJANT_TEMIZ, adet)
    # ---- sağ alan: montaj detayları
    c.text('MONTAJ DETAYLARI', 1000, DETAY_H - 455, 10.6, 'BC', KAT_Y, w=0.85)
    c.text('PVC GEÇME MUFLU PİSSU BORULARI', 1000, DETAY_H - 470, 9, 'BC', KAT_Y, w=0.85)
    detay_boru_montaj(Ciz(msp, x0 + 810, y0 + 870, KAT, KAT_Y))
    detay_dirsek_bransman(Ciz(msp, x0 + 800, y0 + 670, KAT, KAT_Y))
    detay_dirsek_bransman(Ciz(msp, x0 + 1010, y0 + 670, KAT, KAT_Y), tapa=True)
    detay_doseme_duvar(Ciz(msp, x0 + 1220, y0 + 665, KAT, KAT_Y))
    detay_alaturka(Ciz(msp, x0 + 790, y0 + 1085, KAT, KAT_Y))
    detay_havalik(Ciz(msp, x0 + 1300, y0 + 1085, KAT, KAT_Y))
    detay_yer_suzgeci(Ciz(msp, x0 + 1600, y0 + 670, KAT, KAT_Y))
    detay_eviye(Ciz(msp, x0 + 790, y0 + 30, KAT, KAT_Y))
    detay_alafranga(Ciz(msp, x0 + 1410, y0 + 30, KAT, KAT_Y))
    return dict(w=DETAY_W, h=DETAY_H, adet=adet)


# ============================================================================= WC havalandırma izometrisi
def _wc_girdi(girdi=None):
    """girdi: dict | json yolu | None (nb_algilanan.json → ornek_z2_9daire.json)."""
    if isinstance(girdi, dict):
        return girdi
    yollar = [girdi] if girdi else []
    yollar += [os.path.join(DEPO, 'motor', 'deneme', 'wc_havalandirma', 'nb_algilanan.json'),
               os.path.join(DEPO, 'motor', 'deneme', 'wc_havalandirma', 'ornek_z2_9daire.json')]
    for y in yollar:
        if y and os.path.exists(y):
            return json.load(open(y, encoding='utf-8'))
    return None


def saft_birlestir(g, gruplar):
    """WC havalandırma girdisinde şaftları kullanıcının şaft düzenine göre birleştirir.
    gruplar: daire listeleri, ör. [['D3','D5','D8'], ['D1','D2','D4','D6','D7','D9']] (new_block: iki şaft,
    240 ve 480 m³/h). Her daire o kattaki tek aspiratörle (q_oda) bağlanır: aynı kat + daire + şafttaki mahaller
    tek kayda indirgenir (kullanıcı: "Wc Aspiratörü 80 m3/h-50 pa Ø150 mm" kat başına). Girdi değiştirilmez."""
    import copy
    g = copy.deepcopy(g)
    ad = {}
    for i, grp in enumerate(gruplar):
        for d in grp:
            ad[d] = 'Ş%d' % (i + 1)
    eski = {s['ad']: s for s in g.get('saftlar', [])}
    yeni_mah, gor = [], {}
    for m in g.get('mahaller', []):
        sn = ad.get(m['daire'])
        if sn is None:
            continue
        k = (m['kat'], m['daire'], sn)
        if k in gor:
            gor[k]['ad'] += ' + ' + m['ad']
            gor[k]['brans_m'] = max(gor[k].get('brans_m', 1.0), m.get('brans_m', 1.0))
            continue
        m = dict(m, saft=sn)
        gor[k] = m
        yeni_mah.append(m)
    saft = []
    for i, grp in enumerate(gruplar):
        sn = 'Ş%d' % (i + 1)
        ref = next((eski[m0['saft']] for m0 in g.get('mahaller', []) if m0['daire'] in grp and m0['saft'] in eski), {})
        saft.append(dict(ad=sn, xy=ref.get('xy'), baglanti_yuk=ref.get('baglanti_yuk', 2.6)))
    g['saftlar'] = saft
    g['mahaller'] = yeni_mah
    g['kabul'] = dict(g['kabul'], oda_basina_aspirator=False)
    return g


def wc_izometri(msp, x0, y0, w_max, h_max, girdi=None, blok_adi='ROTAS-WC-HAV-IZOMETRI', lejant=False,
                saft_gruplari=None):
    """WC havalandırma izometrisini (motor/deneme/wc_havalandirma, R2 saf geometri) bir bloğa çizer ve
    (x0, y0) sol altına, w_max × h_max alanına sığacak ölçekle yerleştirir. Dönüş: dict(olcek, w, h, say, r) ya da None."""
    import ciz as WC                      # wc_havalandirma/ciz.py
    from hesap import hesapla
    g = _wc_girdi(girdi)
    if g is None:
        return None
    if saft_gruplari:
        g = saft_birlestir(g, saft_gruplari)
    doc = msp.doc
    for n, (cc, lt) in WC.KAT.items():
        if n not in doc.layers:
            doc.layers.add(n, color=cc, linetype=lt if lt in doc.linetypes else 'Continuous')
    if STIL not in doc.styles:
        doc.styles.add(STIL, font='arial.ttf')
    doc.set_wipeout_variables(frame=0)
    r = hesapla(g)
    if blok_adi in doc.blocks:
        doc.blocks.delete_block(blok_adi, safe=False)
    blk = doc.blocks.new(blok_adi, base_point=(0, 0))

    class _Cizim(WC.Cizim):               # mevcut belgeye / bloğa çizen sürüm
        def __init__(self, layout):
            self.doc, self.msp = doc, layout
            self.geo, self.yazi, self.kutular, self.say = [], [], [], {}

    cz = _Cizim(blk)
    bb = WC.izometri(cz, g, r, 0.0, 0.0)
    if lejant:
        WC.lejant(cz, bb[2] + 120, bb[3] - 120)
    cz.text((bb[0], bb[3] + 60), 'WC HAVALANDIRMA İZOMETRİSİ', 30, 'ROTAS-PAFTA-YAZI', 'BL', maske=False)
    nm, cak = cz.yazilari_bas()
    ext = _bbox.extents(blk, fast=True)
    bw, bh = ext.extmax.x - ext.extmin.x, ext.extmax.y - ext.extmin.y
    s = min(w_max / bw, h_max / bh, 1.0)
    msp.add_blockref(blok_adi, (x0 - ext.extmin.x * s, y0 - ext.extmin.y * s),
                     dxfattribs={'layer': 'ROTAS-WC-HAV-KANAL', 'xscale': s, 'yscale': s})
    return dict(olcek=s, w=bw * s, h=bh * s, say=dict(cz.say), r=r, yazi_cakisma=cak, maske=nm)


# ============================================================================= detay paftası
def detay_paftasi(msp, x0, y0, w=2065.0, h=2900.0, girdi=None, adet=None, bosluk=25.0, saft_gruplari=None):
    """Referans son pafta: üstte WC havalandırma izometrisi, altta SIHHİ DETAYLAR (sol kenar x0 + 25, alt y0 + 23)."""
    katmanlar(msp.doc)
    dx, dy = x0 + bosluk, y0 + 23.4
    D = sihhi_detaylar(msp, dx, dy, adet)
    ust_y = dy + DETAY_H + 40
    W = wc_izometri(msp, x0 + 60, ust_y, w - 120, (y0 + h) - ust_y - 60, girdi, saft_gruplari=saft_gruplari)
    return dict(detay=D, wc=W)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/detay_deneme.dxf'
    d = ezdxf.new('R2018', setup=True)
    d.header['$INSUNITS'] = 5
    katmanlar(d)
    m = d.modelspace()
    X0, Y0 = 268132.0, -444050.0
    m.add_lwpolyline([(X0, Y0), (X0 + 2065, Y0), (X0 + 2065, Y0 + 2900), (X0, Y0 + 2900)], close=True, dxfattribs={'layer': 'ROTAS-PAFTA'})
    R = detay_paftasi(m, X0, Y0)
    d.saveas(out)
    print(out, R['wc'] and {k: R['wc'][k] for k in ('olcek', 'w', 'h', 'yazi_cakisma')})
