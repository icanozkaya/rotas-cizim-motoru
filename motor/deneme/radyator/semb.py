# -*- coding: utf-8 -*-
"""Radyatör modülünün sembol köprüsü: motor/deneme/semboller/sembol.py import edilir (dosyaya DOKUNULMAZ).
- MTY'de bloğu olmayan semboller 03_SEMBOLLER.md geometrisiyle tanımlanır: BALANS VANASI, KALORİMETRE (debi ölçer +
  dönüş sıcaklık sensörü), GİDİŞ SICAKLIK SENSÖRÜ, KOLEKTÖR DOLABI (plan, n ağızlı), KOLEKTÖR (şema).
- R3 (14.10.2026 B): MTY bloğu KULLANILMAZ; radyatör, termostatik vana, kolektör, kalorimetre, vana vb. saf geometri
  (geo.py). Kazan dairesi blokları (bloklar_r2) lejant kaydına geo.py'de eklenir."""
import os
import sys
import math

_KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_KOK, '..', 'semboller'))
import sembol as S          # noqa: E402
import geo                  # noqa: E402,F401  (R3 saf geometri blokları + lejant kaydı)

L = S.L


def g_balans(b):
    """03 §2 vana gövdesi (papyon) + ayarlanabilirlik oku (çapraz) + iki ölçüm nipeli (üstte küçük daire) – STAD tipi"""
    S._papyon(b)
    S._okcizgi(b, (-0.45 * L, -0.45 * L), (0.45 * L, 0.45 * L), 0.18 * L)
    for x in (-0.3 * L, 0.3 * L):
        S._ln(b, (x, 0.3 * L), (x, 0.42 * L))
        S._ci(b, (x, 0.47 * L), 0.05 * L)
    S._no(b, 0.6 * L)


def g_kalorimetre_km(b):
    """03 §3 kalorimetre: dönüş hattında dikdörtgen 0,6L×0,4L içinde 'Q'; dönüş sıcaklık sensörü (içi dolu daire r=0,06L)"""
    w, h = 0.6 * L, 0.4 * L
    S._rect(b, 0, 0, w, h)
    S._yz(b, 'Q', (0, 0), 0.5 * h)
    S._ok(b, (w / 2 - 1.0, -h / 2 - 2.5), 0, 3.0)           # akış yönü (debi ölçer)
    S._ln(b, (-w / 2 + 1.0, -h / 2 - 2.5), (w / 2 - 1.0, -h / 2 - 2.5))
    S._dolu_daire(b, (0.55 * L, 0), 0.06 * L)                # dönüş sensörü
    S._no(b, h / 2 + 3)


def g_sensor(b):
    """kalorimetre gidiş sıcaklık sensörü: içi dolu daire r = 0,06L + daldırma kovanı"""
    S._dolu_daire(b, (0, 0), 0.06 * L)
    S._ln(b, (0, 0.06 * L), (0, 0.2 * L))
    S._ln(b, (-0.08 * L, 0.2 * L), (0.08 * L, 0.2 * L))
    S._no(b, 0.3 * L)


EK = [
    # anahtar, gruplar, açıklama, kaynak, src, ek
    ('balans_vanasi', ('ISITMA',), 'BALANS (DENGELEME) VANASI – ÖLÇÜM NİPELLİ', '03', g_balans, {}),
    ('kalorimetre_km', ('ISITMA',), 'KALORİMETRE (DEBİ ÖLÇER + DÖNÜŞ SENSÖRÜ)', '03', g_kalorimetre_km, {}),
    ('kalorimetre_sensor', ('ISITMA',), 'KALORİMETRE GİDİŞ SICAKLIK SENSÖRÜ', '03', g_sensor, {}),
]


def kaydet():
    for k in EK:
        if k[0] not in S.SEMBOL:
            S.SEMBOL[k[0]] = dict(ad=k[0], gruplar=k[1], aciklama=k[2], kaynak=k[3], src=k[4], ek=k[5])


kaydet()


def tanimla(doc, ad):
    return S.blok_tanimla(doc, ad)


def kolektor_dolabi(doc, W, n):
    """plan: sıva altı kolektör dolabı (W × 16 cm), içinde gidiş ve dönüş kolektör gövdeleri; n ağızlı"""
    ad = f'ROTAS-KOLEKTOR-DOLABI-{n}'
    if ad in doc.blocks:
        return ad
    S.hazirla(doc)
    b = doc.blocks.new(ad)
    S._rect(b, W / 2, 8.0, W, 16.0)
    S._rect(b, W / 2, 11.0, W - 10.0, 3.0)        # gidiş kolektörü
    S._rect(b, W / 2, 5.0, W - 10.0, 3.0)         # dönüş kolektörü
    for x in (3.0, W - 3.0):                      # kör tapa / hava purjörü
        S._ln(b, (x, 3.0), (x, 13.0))
    key = f'kolektor_dolabi_{n}'
    if key not in S.SEMBOL:
        S.SEMBOL[key] = dict(ad=key, gruplar=('ISITMA',), aciklama=f'KOLEKTÖR DOLABI ({n} AĞIZLI GİDİŞ + DÖNÜŞ) – PLAN',
                             kaynak='03', src=None, ek={'blok': ad})
    return ad


def ciz(msp, ad, p, rot=0.0, olcek=1.0, kat='ROTAS-ISITMA-SEMBOL', no=None, sx=None):
    bn = S.blok_tanimla(msp.doc, ad) if ad in S.SEMBOL else ad
    e = msp.add_blockref(bn, p, dxfattribs={'layer': kat, 'rotation': rot, 'xscale': sx if sx is not None else olcek,
                                            'yscale': olcek})
    bd = msp.doc.blocks.get(bn)
    ats = [a for a in bd if a.dxftype() == 'ATTDEF']
    if ats:
        vals = {a.dxf.tag: '' for a in ats}
        if no is not None and 'NO' in vals:
            vals['NO'] = no
        e.add_auto_attribs(vals)
        for a in e.attribs:
            if a.dxf.tag == 'NO':
                a.dxf.rotation = 0.0
                a.dxf.height = 4.0 * olcek
            else:
                a.is_invisible = True
    return e


def lejant(doc, x, y):
    return S.otomatik_lejant(doc, x, y)
