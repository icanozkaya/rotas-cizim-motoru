# -*- coding: utf-8 -*-
"""Radyatör modülünün sembol köprüsü: motor/deneme/semboller/sembol.py import edilir (dosyaya DOKUNULMAZ).
- MTY'de bloğu olmayan semboller 03_SEMBOLLER.md geometrisiyle tanımlanır: BALANS VANASI, KALORİMETRE (debi ölçer +
  dönüş sıcaklık sensörü), GİDİŞ SICAKLIK SENSÖRÜ, KOLEKTÖR DOLABI (plan, n ağızlı), KOLEKTÖR (şema).
- Çizimde kullanılan MTY / kazan dairesi blokları otomatik lejantın tanıması için çalışma anında SEMBOL kaydına eklenir."""
import os
import sys
import math

_KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_KOK, '..', 'semboller'))
import sembol as S          # noqa: E402

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
    ('radyator_kolon', ('ISITMA',), 'PANEL RADYATÖR (KOLON ŞEMASI)', 'MTY', 'RADYATOR TESISATI__KOLON ŞEMASI__MTY-RADYATOR KOLON', {}),
    ('banyopan_plan', ('ISITMA',), 'HAVLUPAN (BANYOPAN) – PLAN', 'MTY', 'RADYATOR TESISATI__KAT PLANI__MTY-RADYATOR Banyopan', {}),
    ('banyopan_kolon', ('ISITMA',), 'HAVLUPAN (BANYOPAN) – KOLON ŞEMASI', 'MTY',
     'RADYATOR TESISATI__KOLON ŞEMASI__MTY-RADYATÖR BANYOPAN KOLON', {}),
    ('isitma_kolonu', ('ISITMA',), 'ISITMA KOLONU (GİDİŞ + DÖNÜŞ)', 'MTY', 'RADYATOR TESISATI__KOLON ŞEMASI__MTY-BORU KOLON', {}),
    ('ohac_kolon', ('ISITMA',), 'OTOMATİK HAVA ATMA CİHAZI (O.H.A.C)', 'MTY', 'RADYATOR TESISATI__VANALAR__MTY-O.H.A.C', {}),
    ('hava_ayirici', ('ISITMA',), 'HAVA AYIRICI', 'MTY', 'x', {'blok': 'MTY-HAVA AYIRICI'}),
    ('tortu_ayirici', ('ISITMA',), 'TORTU VE PİSLİK AYIRICI', 'MTY', 'x', {'blok': 'MTY-TORTU &PİSLİK AYIRICI'}),
    ('denge_kabi_sema', ('ISITMA',), 'DENGE KABI (HİDROLİK AYIRICI)', 'MTY', 'x', {'blok': 'MTY-DENGE KABI ŞEMADA'}),
    ('genlesme_tanki_kolon', ('ISITMA',), 'KAPALI GENLEŞME TANKI (MEMBRANLI)', 'MTY', 'x', {'blok': 'MTY-GENLEŞME TANKI KOLON'}),
    ('kazan_duvar', ('ISITMA',), 'DUVAR TİPİ YOĞUŞMALI KAZAN', '03', None, {'blok': 'ROTAS-KAZAN-DUVAR'}),
    ('selenoid_gaz', ('DOGALGAZ',), 'GAZ SELENOİD VANASI', '03', None, {'blok': 'ROTAS-SELENOID'}),
    ('gaz_alarm', ('DOGALGAZ',), 'GAZ ALARM CİHAZI + CO DEDEKTÖRÜ', '03', None, {'blok': 'ROTAS-GAZ-ALARM'}),
    ('ok_isareti', ('ISITMA',), 'AKIŞ YÖNÜ OKU', '03', None, {'blok': 'ROTAS-OK'}),
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


def kolektor_sema(doc, n, aralik, gen_bas=24.0):
    """kolon şeması: kolektör dolabı görünüşü – üst gövde gidiş, alt gövde dönüş; ağızlar alt kenardan çıkar.
    Gidiş ağzı (sağ) dönüş gövdesinin önünden geçer (gizli çizgi kuralı: gövde önünde kesik). Taban (0,0) = sol alt köşe."""
    ad = f'ROTAS-KOLEKTOR-SEMA-{n}'
    W = gen_bas + n * aralik + 10.0
    Hd = 56.0
    if ad in doc.blocks:
        return ad, W, Hd, 40.0, 22.0
    S.hazirla(doc)
    b = doc.blocks.new(ad)
    S._pl(b, [(0, 0), (W, 0), (W, Hd), (0, Hd)], True)                       # dolap
    S._pl(b, [(3, 3), (W - 3, 3), (W - 3, Hd - 3), (3, Hd - 3)], True)
    yg, yd = 40.0, 22.0                                                       # gövde eksenleri
    for y in (yg, yd):
        S._pl(b, [(10, y - 3), (W - 6, y - 3), (W - 6, y + 3), (10, y + 3)], True)
    for i in range(n):
        xd = gen_bas + i * aralik
        xg = xd + 6.0
        S._ln(b, (xd, yd - 3), (xd, 0))                     # dönüş ağzı
        S._ln(b, (xg, yg - 3), (xg, yd + 3))                # gidiş ağzı (dönüş gövdesi önünde kesik)
        S._ln(b, (xg, yd - 3), (xg, 0))
        S._ci(b, (xg, yg - 9), 1.6)                         # gidiş debimetresi / ayar
        S._ci(b, (xd, yd - 9), 1.6)                         # dönüş vanası
    key = f'kolektor_sema_{n}'
    if key not in S.SEMBOL:
        S.SEMBOL[key] = dict(ad=key, gruplar=('ISITMA',), aciklama=f'KOLEKTÖR DOLABI ({n} AĞIZLI) – KOLON ŞEMASI',
                             kaynak='03', src=None, ek={'blok': ad})
    return ad, W, Hd, yg, yd


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
