# -*- coding: utf-8 -*-
"""Radyatör modülü R3: SAF GEOMETRİ bloklar (MTY bloğu YOK — 14.10.2026 (B) talimatı).

Plan: panel radyatör + termostatik vana + dönüş rakoru, havlupan, kolon (gidiş+dönüş) plan sembolü, kombi, mahal etiketi.
Şema: panel radyatör / havlupan (TRV'li, bağlantı uçları sabit), kolektör dolabı (gidiş kolektörü üstte ağızlar YUKARI,
dönüş kolektörü altta ağızlar AŞAĞI → devreler iç içe, kesişmesiz), küresel vana, pislik tutucu, kalorimetre (sağ/sol akış),
boşaltma vanası, otomatik hava purjörü, kombi.
Bağlantı noktaları (yerel):
- ROTAS-RADYATOR-PLAN : gidiş (0, 12), dönüş (105.4, 7.3); x ölçeği = L/100, y ölçeği 1 (ag.py/plan.py uçlarıyla aynı)
- ROTAS-HAVLUPAN-PLAN : gidiş (-4, 3), dönüş (28, 3); ölçek L/32
- ROTAS-RADYATOR-SEMA / ROTAS-HAVLUPAN-SEMA : gövde (0,0)-(110,40), gidiş (0, 50) üstten, dönüş (110, -10) alttan
- ROTAS-KOLEKTOR-SEMA-n : dolap (0,0)-(W,40), besleme gidiş (0,30), dönüş (0,10); k. gidiş ağzı (14+14k, 40) ↑,
  k. dönüş ağzı (14+14k, 0) ↓
- ROTAS-KOMBI-SEMA : gövde (-46,-10)-(0,50), gidiş ucu (0, 30), dönüş ucu (0, 10)
"""
import math
import os
import sys

_KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_KOK, '..', 'semboller'))
import sembol as S          # noqa: E402  (yalnız geometri yardımcıları ve lejant kaydı; MTY kaynaklı anahtarlar kullanılmaz)

L = S.L
RAD_W, RAD_H = 110.0, 40.0
KOL_H, KOL_YG, KOL_YD, KOL_ADIM, KOL_X0 = 40.0, 30.0, 10.0, 14.0, 14.0


def kolektor_genislik(n):
    return KOL_X0 + (n - 1) * KOL_ADIM + 14.0


# ----------------------------------------------------------------------------- hat sembolleri (ATTRIB 'NO' üstte)
def g_kuresel(b):
    S._papyon(b); S._dolu_daire(b, (0, 0), 0.12 * L); S._ln(b, (0, 0.12 * L), (0, 0.42 * L))
    S._ln(b, (-0.18 * L, 0.42 * L), (0.18 * L, 0.42 * L)); S._no(b, 0.55 * L)


def g_pislik(b):
    S._ln(b, (-0.5 * L, 0), (0.5 * L, 0))
    S._pl(b, [(-0.25 * L, 0), (0.05 * L, -0.4 * L), (0.35 * L, -0.4 * L), (0.05 * L, 0)])
    S._ln(b, (-0.1 * L, 0), (0.2 * L, -0.4 * L))
    S._no(b, 0.25 * L)


def _kalorimetre(b, yon):
    w, h = 0.6 * L, 0.4 * L
    S._rect(b, 0, 0, w, h)
    S._yz(b, 'Q', (0, 0), 0.5 * h)
    x0, x1 = (-w / 2 + 1.0, w / 2 - 1.0) if yon > 0 else (w / 2 - 1.0, -w / 2 + 1.0)
    S._ln(b, (x0, -h / 2 - 2.5), (x1, -h / 2 - 2.5)); S._ok(b, (x1, -h / 2 - 2.5), 0 if yon > 0 else 180, 3.0)
    S._dolu_daire(b, (yon * 0.55 * L, 0), 0.06 * L)          # dönüş sıcaklık sensörü
    S._no(b, h / 2 + 3)


def g_kalorimetre_sag(b):
    _kalorimetre(b, 1)


def g_kalorimetre_sol(b):
    _kalorimetre(b, -1)


def g_bosaltma(b):             # boşaltma (kosva) vanası: papyon + hortum rakoru (aşağı)
    S._papyon(b, 0.8 * L); S._ln(b, (0.4 * L, 0), (0.55 * L, 0)); S._ln(b, (0.55 * L, 0), (0.55 * L, -0.35 * L))
    S._ln(b, (0.45 * L, -0.35 * L), (0.65 * L, -0.35 * L))


def g_ohac(b):                 # otomatik hava purjörü, orijin boru ucu, gövde +Y
    S._ln(b, (0, 0), (0, 5)); S._pl(b, [(-4, 5), (4, 5), (4, 17), (-4, 17)], True); S._ci(b, (0, 10), 2.4)
    S._pl(b, [(-1.6, 17), (-1.6, 20), (1.6, 20), (1.6, 17)])


# ----------------------------------------------------------------------------- plan
def g_radyator_plan(b):
    S._pl(b, [(4.7, 0), (104.7, 0), (104.7, 10), (4.7, 10)], True)
    S._ln(b, (4.7, 5), (104.7, 5))
    S._pl(b, [(-1.8, 12), (1.8, 12), (0, 9.5)], True); S._pl(b, [(-1.8, 7), (1.8, 7), (0, 9.5)], True)   # TRV gövdesi
    S._pl(b, [(-6, 8.3), (-2.5, 8.3), (-2.5, 10.7), (-6, 10.7)], True)                              # termostatik kafa
    S._ln(b, (0, 7), (0, 2.5)); S._ln(b, (0, 2.5), (4.7, 2.5))
    for k in (0, 1):
        S._dolu(b, [(104.4, 7.3 - 2.2 * k), (106.4, 7.3 - 2.2 * k), (105.4, 6.2)])                  # dönüş rakoru
    S._ln(b, (105.4, 5.1), (105.4, 3.0)); S._ln(b, (105.4, 3.0), (104.7, 3.0))


def g_havlupan_plan(b):
    S._pl(b, [(-3, 0), (0, 0), (0, 3), (-3, 3)], True); S._pl(b, [(24, 0), (27, 0), (27, 3), (24, 3)], True)
    for y in (0.6, 1.5, 2.4):
        S._ln(b, (0, y), (24, y))
    S._ln(b, (-4, 3), (-4, 1.5)); S._ln(b, (-4, 1.5), (-3, 1.5))
    S._ln(b, (28, 3), (28, 1.5)); S._ln(b, (28, 1.5), (27, 1.5))


def g_kolon_plan(b):           # ısıtma kolonu (plan): gidiş dolu, dönüş boş daire; eksen (0,±8) — besleme ±HF
    S._dolu_daire(b, (0, 8), 4.0); S._ci(b, (0, -8), 4.0); S._ci(b, (0, -8), 1.2)


def g_kombi(b):                # hermetik kombi (plan/şema), orijin sağ kenar ortası; gidiş (0,30) dönüş (0,10)
    S._pl(b, [(-46, -10), (0, -10), (0, 50), (-46, 50)], True)
    S._pl(b, [(-40, 34), (-6, 34), (-6, 44), (-40, 44)], True)
    S._pl(b, [(-30, 4), (-16, 4), (-23, 22)], True)
    S._ln(b, (-46, 40), (-56, 40)); S._ln(b, (-46, 46), (-56, 46))      # hermetik baca (dışarı)


def g_kombi_plan(b):           # hermetik kombi (plan): 48 × 30, orijin sol alt; baca duvara (−y)
    S._pl(b, [(0, 0), (48, 0), (48, 30), (0, 30)], True)
    S._pl(b, [(17, 6), (31, 6), (24, 22)], True)
    S._ln(b, (8, 0), (8, -14)); S._ln(b, (14, 0), (14, -14))


def g_mahal(b):                # mahal etiketi (ısı kaybı): sekizgen + öznitelikler (MTY etiketinin yerine)
    S._pl(b, [(-34.2, 18.4), (-34.2, -18.4), (-28.2, -24.4), (28.2, -24.4), (34.2, -18.4), (34.2, 18.4),
              (28.2, 24.4), (-28.2, 24.4)], True)
    S._ln(b, (-34.2, 0), (34.2, 0))
    from ezdxf.enums import TextEntityAlignment as TA
    for tag, p in (('MAHAL_001', (0, 32)), ('NO_001', (0, 9)), ('DERECE_001', (0, -9)), ('ISIKAYBI_001', (0, -36)),
                   ('ALAN', (0, -52))):
        S._attdef(b, tag, p, 12.0, TA.MIDDLE_CENTER)


# ----------------------------------------------------------------------------- şema
def g_radyator_sema(b):
    S._pl(b, [(0, 0), (RAD_W, 0), (RAD_W, RAD_H), (0, RAD_H)], True)
    for x in range(6, int(RAD_W) - 2, 6):                         # konvektör kanatları (üst/alt şerit)
        S._ln(b, (x, 0), (x, 7)); S._ln(b, (x, RAD_H - 7), (x, RAD_H))
    S._ln(b, (0, 7), (RAD_W, 7)); S._ln(b, (0, RAD_H - 7), (RAD_W, RAD_H - 7))
    _trv_rakor(b)


def g_havlupan_sema(b):
    S._pl(b, [(0, 0), (6, 0), (6, RAD_H), (0, RAD_H)], True)
    S._pl(b, [(RAD_W - 6, 0), (RAD_W, 0), (RAD_W, RAD_H), (RAD_W - 6, RAD_H)], True)
    for y in (2.5, 5.0, RAD_H - 5.0, RAD_H - 2.5):
        S._ln(b, (6, y), (RAD_W - 6, y))
    _trv_rakor(b)


def _trv_rakor(b):
    # termostatik vana (gidiş, üstte, düşey) + kafa
    S._pl(b, [(-2.5, 50), (2.5, 50), (0, 46)], True); S._pl(b, [(-2.5, 42), (2.5, 42), (0, 46)], True)
    S._pl(b, [(-8, 44.5), (-2.8, 44.5), (-2.8, 47.5), (-8, 47.5)], True)
    S._ln(b, (0, 42), (0, RAD_H))
    # dönüş rakoru (altta, düşey, dolu)
    S._dolu(b, [(RAD_W - 2.2, -10), (RAD_W + 2.2, -10), (RAD_W, -6.5)]); S._dolu(b, [(RAD_W - 2.2, -3), (RAD_W + 2.2, -3), (RAD_W, -6.5)])
    S._ln(b, (RAD_W, -3), (RAD_W, 0))


def kolektor_sema(doc, n):
    ad = f'ROTAS-KOLEKTOR-SEMA-{n}'
    W = kolektor_genislik(n)
    if ad not in doc.blocks:
        S.hazirla(doc)
        b = doc.blocks.new(ad)
        S._pl(b, [(0, 0), (W, 0), (W, KOL_H), (0, KOL_H)], True)
        for y in (KOL_YG, KOL_YD):
            S._pl(b, [(6, y - 2.5), (W - 4, y - 2.5), (W - 4, y + 2.5), (6, y + 2.5)], True)
            S._ln(b, (0, y), (6, y))
        for k in range(n):
            x = KOL_X0 + k * KOL_ADIM
            S._ln(b, (x, KOL_YG + 2.5), (x, KOL_H)); S._ci(b, (x, KOL_YG + 6), 1.4)     # gidiş ağzı + debimetre
            S._ln(b, (x, KOL_YD - 2.5), (x, 0)); S._ci(b, (x, KOL_YD - 6), 1.4)         # dönüş ağzı + vana
        for y in (KOL_YG, KOL_YD):                                                     # purjör / boşaltma
            S._ln(b, (W - 4, y), (W - 1.5, y))
        key = f'kolektor_sema_{n}'
        if key not in S.SEMBOL:
            S.SEMBOL[key] = dict(ad=key, gruplar=('ISITMA',), aciklama=f'KOLEKTÖR DOLABI ({n} AĞIZLI) – KOLON ŞEMASI',
                                 kaynak='03', src=None, ek={'blok': ad})
    return ad, W


# ----------------------------------------------------------------------------- kayıt (lejant)
EK = [
    ('r_kuresel_vana', ('ISITMA',), 'KÜRESEL VANA', g_kuresel, 'ROTAS-R-KURESEL-VANA'),
    ('r_pislik_tutucu', ('ISITMA',), 'PİSLİK TUTUCU (Y TİPİ)', g_pislik, 'ROTAS-R-PISLIK-TUTUCU'),
    ('r_kalorimetre_sag', ('ISITMA',), 'KALORİMETRE (DEBİ ÖLÇER + DÖNÜŞ SENSÖRÜ)', g_kalorimetre_sag, 'ROTAS-R-KALORIMETRE-SAG'),
    ('r_kalorimetre_sol', ('ISITMA',), 'KALORİMETRE (DEBİ ÖLÇER + DÖNÜŞ SENSÖRÜ)', g_kalorimetre_sol, 'ROTAS-R-KALORIMETRE-SOL'),
    ('r_bosaltma', ('ISITMA',), 'BOŞALTMA (KOSVA) VANASI', g_bosaltma, 'ROTAS-R-BOSALTMA'),
    ('r_ohac', ('ISITMA',), 'OTOMATİK HAVA PURJÖRÜ (O.H.A.C)', g_ohac, 'ROTAS-R-OHAC'),
    ('r_radyator_plan', ('ISITMA',), 'PANEL RADYATÖR + TERMOSTATİK VANA + DÖNÜŞ RAKORU (PLAN)', g_radyator_plan, 'ROTAS-RADYATOR-PLAN'),
    ('r_havlupan_plan', ('ISITMA',), 'HAVLUPAN (PLAN)', g_havlupan_plan, 'ROTAS-HAVLUPAN-PLAN'),
    ('r_kolon_plan', ('ISITMA',), 'ISITMA KOLONU – GİDİŞ (DOLU) / DÖNÜŞ (BOŞ)', g_kolon_plan, 'ROTAS-ISITMA-KOLON-PLAN'),
    ('r_kombi', ('ISITMA',), 'HERMETİK KOMBİ (ŞEMA)', g_kombi, 'ROTAS-KOMBI'),
    ('r_kombi_plan', ('ISITMA',), 'HERMETİK KOMBİ (PLAN)', g_kombi_plan, 'ROTAS-KOMBI-PLAN'),
    ('r_mahal', ('ISITMA',), 'MAHAL ETİKETİ (AD / NO / SICAKLIK / ISI KAYBI)', g_mahal, 'ROTAS-MAHAL-ETIKET'),
    ('r_radyator_sema', ('ISITMA',), 'PANEL RADYATÖR + TERMOSTATİK VANA + DÖNÜŞ RAKORU (ŞEMA)', g_radyator_sema, 'ROTAS-RADYATOR-SEMA'),
    ('r_havlupan_sema', ('ISITMA',), 'HAVLUPAN + TERMOSTATİK VANA (ŞEMA)', g_havlupan_sema, 'ROTAS-HAVLUPAN-SEMA'),
    # kazan dairesi modülünün (bloklar_r2) saf geometri blokları — lejant tanısın diye
    ('kd_kelebek', ('ISITMA',), 'KELEBEK VANA', None, 'ROTAS-KELEBEK-VANA'),
    ('kd_kuresel', ('ISITMA',), 'KÜRESEL VANA', None, 'ROTAS-KURESEL-VANA'),
    ('kd_cekvalf', ('ISITMA',), 'ÇEK VALF', None, 'ROTAS-CEKVALF'),
    ('kd_pislik', ('ISITMA',), 'PİSLİK TUTUCU (Y TİPİ) / GAZ FİLTRESİ', None, 'ROTAS-PISLIK-TUTUCU'),
    ('kd_dolum', ('ISITMA',), 'OTOMATİK DOLUM VANASI', None, 'ROTAS-OTOMATIK-DOLUM'),
    ('kd_kilitli', ('ISITMA',), 'KİLİTLENEBİLİR (MÜHÜRLÜ) VANA', None, 'ROTAS-KILITLI-VANA'),
    ('kd_esnek', ('DOGALGAZ',), 'ESNEK BAĞLANTI', None, 'ROTAS-ESNEK-BAGLANTI'),
    ('kd_ev', ('ISITMA',), 'EMNİYET VENTİLİ', None, 'ROTAS-EMNIYET-VENTILI'),
    ('kd_man', ('ISITMA',), 'MANOMETRE', None, 'ROTAS-MANOMETRE'),
    ('kd_term', ('ISITMA',), 'TERMOMETRE', None, 'ROTAS-TERMOMETRE'),
    ('kd_ohac', ('ISITMA',), 'OTOMATİK HAVA PURJÖRÜ', None, 'ROTAS-OHAC'),
    ('kd_denge', ('ISITMA',), 'DENGE KABI (HİDROLİK AYIRICI)', None, 'ROTAS-DENGE-KABI'),
    ('kd_hava', ('ISITMA',), 'HAVA AYIRICI', None, 'ROTAS-HAVA-AYIRICI'),
    ('kd_tortu', ('ISITMA',), 'TORTU VE PİSLİK AYIRICI', None, 'ROTAS-TORTU-AYIRICI'),
    ('kd_genlesme', ('ISITMA',), 'KAPALI GENLEŞME TANKI (MEMBRANLI)', None, 'ROTAS-GENLESME-TANKI'),
    ('kd_baca', ('ISITMA',), 'BACA ŞAPKASI', None, 'ROTAS-BACA-SAPKA'),
    ('kd_kazan', ('ISITMA',), 'DUVAR TİPİ YOĞUŞMALI KAZAN', None, 'ROTAS-KAZAN-DUVAR'),
    ('kd_selenoid', ('DOGALGAZ',), 'GAZ SELENOİD VANASI', None, 'ROTAS-SELENOID'),
    ('kd_alarm', ('DOGALGAZ',), 'GAZ ALARM CİHAZI + CO DEDEKTÖRÜ', None, 'ROTAS-GAZ-ALARM'),
    ('kd_ok', ('ISITMA',), 'AKIŞ YÖNÜ OKU', None, 'ROTAS-OK'),
]


def kaydet():
    for k, gr, ac, f, bn in EK:
        S.SEMBOL[k] = dict(ad=k, gruplar=gr, aciklama=ac, kaynak='03', src=f, ek={'blok': bn})


def tanimla(doc, anahtar):
    S.hazirla(doc)
    s = S.SEMBOL[anahtar]
    bn = s['ek']['blok']
    if bn not in doc.blocks:
        if s['src'] is None:
            raise KeyError(f'{bn} tanımsız (kazan dairesi bloğu)')
        b = doc.blocks.new(bn)
        s['src'](b)
    return bn


kaydet()
