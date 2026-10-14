"""yerden2 — çıktı kontrolleri (YERDEN_ISITMA_ALTIN_REFERANS §7 testleri + denetle.py).

  PEX-1  devre = tek açık LWPOLYLINE; etiket sayısı = devre sayısı
  PEX-2/3 pitch 15 / dönüş yayları |bulge| = 0,4142 (90°, r 7)
  PEX-4  uzun segmentlerin tamamı yatay
  PEX-5  iki uç 15 cm aralıkta
  PEX-7  L ≤ 80 m
  PEX-8  devre kendini kesmez; devre–devre kesişme yok, min aralık
  PEX-9/10 ısıtılmayan mahal ve tefriş engeli ile kesişme yok
  taşma  boru mahal (ısıtma alanı) dışına çıkmaz
  ET     etiket–etiket, etiket–mimari yazı çakışması; cepli etiket–boru çakışması
  MTY / ROTAS- öneki / yazı / kesişme: motor/deneme/denetim/denetle.py
"""
import json
import math
import os

from shapely import STRtree
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

import serpantin as S
import yerden as Y

RAPOR = Y.CIKIS + '/KONTROL.json'


def calistir(KTS, dxf_yol):
    sonuc = {}
    hatalar = []
    tum = []
    for KT in KTS:
        for o in KT['odalar']:
            for c in o['tasarim']['devreler']:
                tum.append((KT['kat'], o, c, S.cizgi(c['pts'], 8)))
    n = len(tum)
    # PEX-1/7/5/3/4
    uzun = [(k, c['no'], c['L_m']) for k, o, c, g in tum if c['L_m'] > 80.0]
    uc = [(k, c['no']) for k, o, c, g in tum
          if abs(math.hypot(c['pts'][0][0] - c['pts'][-1][0], c['pts'][0][1] - c['pts'][-1][1]) - 15.0) > 0.2]
    bulge = [(k, c['no']) for k, o, c, g in tum if any(abs(b) > 1e-6 and abs(abs(b) - S.BULGE) > 1e-3 for _, _, b in c['pts'])]
    dikey_uzun = 0
    for k, o, c, g in tum:
        p = c['pts']
        for i in range(len(p) - 1):
            if abs(p[i][2]) > 1e-6:
                continue
            dx, dy = abs(p[i + 1][0] - p[i][0]), abs(p[i + 1][1] - p[i][1])
            if dx > 1e-3 and dy > 1e-3:
                hatalar.append('eğik segment kat %s devre %d' % (k, c['no']))
    # PEX-8 kendi kendini kesme
    kendi = [(k, c['no']) for k, o, c, g in tum if not g.is_simple]
    # devre-devre
    geo = [g for _, _, _, g in tum]
    tree = STRtree(geo)
    kes, yakin = [], []
    for i, g in enumerate(geo):
        for j in tree.query(g.buffer(10)):
            if j <= i:
                continue
            if tum[i][0] != tum[j][0]:
                continue
            if g.intersects(geo[j]):
                kes.append((tum[i][0], tum[i][2]['no'], tum[j][2]['no']))
            elif g.distance(geo[j]) < 10.0 - 1e-6:
                yakin.append((tum[i][0], tum[i][2]['no'], tum[j][2]['no'], round(g.distance(geo[j]), 1)))
    # PEX-9/10 + taşma
    tefris, isitmasiz, tasma = [], [], []
    for KT in KTS:
        isz = unary_union([q['poly'].buffer(-2) for q in KT['isitmasiz']]) if KT['isitmasiz'] else None
        for o in KT['odalar']:
            for c in o['tasarim']['devreler']:
                g = S.cizgi(c['pts'], 8)
                if not o['eng'].is_empty and g.intersects(o['eng'].buffer(-1)):
                    p = g.intersection(o['eng'].buffer(-1)).centroid
                    tefris.append((KT['kat'], c['no'], o['zon'], round(p.x), round(p.y)))
                if isz is not None and g.intersects(isz):
                    isitmasiz.append((KT['kat'], c['no'], o['zon']))
                if not o['poly'].buffer(-3).covers(g):
                    dd = g.difference(o['poly'].buffer(-3))
                    tasma.append((KT['kat'], c['no'], o['zon'], round(dd.length, 1), round(dd.centroid.x), round(dd.centroid.y)))
    # etiketler
    et = []
    for KT in KTS:
        for o in KT['odalar']:
            for c in o['tasarim']['devreler']:
                if c.get('etiket') is not None:
                    et.append((KT['kat'], 'devre %d' % c['no'], c['etiket'], c['cep'] is not None))
            if o.get('etiket') is not None:
                et.append((KT['kat'], 'mahal %s' % o['zon'], o['etiket'], False))
    et_cak = []
    for i in range(len(et)):
        for j in range(i + 1, len(et)):
            if et[i][2].intersects(et[j][2]) and et[i][2].intersection(et[j][2]).area > 1:
                et_cak.append((et[i][1], et[j][1]))
    yaz = unary_union([q for KT in KTS for q in KT['yazi']]) if KTS else None
    et_yazi = [(k, ad) for k, ad, q, cep in et if yaz is not None and q.intersection(yaz).area > 1]
    boru_u = unary_union(geo)
    cep_boru = [(k, ad) for k, ad, q, cep in et if cep and q.intersects(boru_u)]
    maskeli = sum(1 for k, ad, q, cep in et if ad.startswith('devre') and not cep)
    devre_et = sum(1 for k, ad, q, cep in et if ad.startswith('devre'))
    # denetle.py
    import denetle as D
    try:
        import pathlib
        dn = D.denetle(pathlib.Path(dxf_yol))
    except Exception as ex:      # pragma: no cover
        dn = {'hata': str(ex)}
    ozet = dict(dn) if isinstance(dn, dict) else {}
    sonuc = {
        'devre_sayisi': n,
        'etiketli_devre': devre_et,
        'etiket_cepte': devre_et - maskeli,
        'etiket_maskeli_veya_disarida': maskeli,
        'L_max_m': max((c['L_m'] for _, _, c, _ in tum), default=0),
        'L_gt_80': uzun,
        'uc_aralik_15_degil': uc,
        'bulge_90_degil': bulge,
        'kendini_kesen': kendi,
        'devre_devre_kesisme': kes,
        'devre_devre_10cm_alti': yakin,
        'tefris_kesisme': tefris,
        'isitilmayan_kesisme': isitmasiz,
        'mahal_disina_tasma': tasma,
        'etiket_etiket_cakisma': et_cak,
        'etiket_mimari_yazi_cakisma': et_yazi,
        'cepli_etiket_boru_cakisma': cep_boru,
        'diger': hatalar[:20],
        'denetle': ozet,
    }
    sonuc['yogunluk'] = yogunluk(KTS)
    sonuc['yogunluk_6_alti'] = [y for y in sonuc['yogunluk'] if y['tur'] in ('oda', 'hol') and y['m_m2_mimari'] < 6.0]
    sonuc['devre_3m_alti'] = [(k, c['no'], c['L_m']) for k, o, c, g in tum if c['L_m'] < 3.0]
    sonuc['etiket_mahal_disi'] = [(KT['kat'], o['zon'], c['no']) for KT in KTS for o in KT['odalar']
                                  for c in o['tasarim']['devreler']
                                  if c.get('etiket') is not None and not o['poly'].buffer(1).contains(c['etiket'])]
    sonuc['mahal_etiketi_mahal_disi'] = [(KT['kat'], o['zon']) for KT in KTS for o in KT['odalar']
                                         if o.get('etiket') is not None and not o['poly'].buffer(1).contains(o['etiket'])]
    sonuc['mahal_etiketi_vitrifiye_ustu'] = [(KT['kat'], o['zon']) for KT in KTS for o in KT['odalar']
                                             if o.get('etiket') is not None and not o['eng'].is_empty
                                             and o['etiket'].intersection(o['eng']).area > 1]
    json.dump(sonuc, open(RAPOR, 'w'), ensure_ascii=False, indent=1, default=str)
    kisa = {k: (len(v) if isinstance(v, list) else v) for k, v in sonuc.items() if k not in ('denetle', 'yogunluk')}
    print('[kontrol]', json.dumps(kisa, ensure_ascii=False))
    print('[denetle]', json.dumps(ozet, ensure_ascii=False, default=str)[:1500])
    return sonuc


def yogunluk(KTS):
    """mahal başına boru yoğunluğu: m boru / mimari m² (kontrolörün ölçüsü) ve m / net ısıtma alanı"""
    out = []
    for KT in KTS:
        for o in KT['odalar']:
            L = sum(c['L_m'] for c in o['tasarim']['devreler'])
            Am = o.get('alan_mimari') or o['alan']
            out.append(dict(kat=KT['kat'], zon=o['zon'], daire='D%d' % o['daire'], ad=o['ad'], tur=o['tur'],
                            alan_mimari=Am, alan_poligon=o['alan'], alan_net=round(o['H'].area / 1e4, 2),
                            L_m=round(L, 2), devre=[c['L_m'] for c in o['tasarim']['devreler']],
                            m_m2_mimari=round(L / Am, 2), m_m2_poligon=round(L / o['alan'], 2),
                            m_m2_net=round(L / (o['H'].area / 1e4), 2)))
    return out
