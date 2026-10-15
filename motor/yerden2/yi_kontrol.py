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
from shapely.geometry import LineString, Point, box
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
    def _yazi_bolgesi(ad, q):
        # mahal etiketi: çerçeve mimari yazının üstüne binebilir (küçük ıslak hacim, kullanıcının Z07'si gibi; maske
        # yazıyı örtmez) — ölçülen, etiketin kendi yazıları (24°C / Zxx, h 12·k); devre etiketi: tüm tablo
        if not ad.startswith('mahal'):
            return q
        x0, y0, x1, y1 = q.bounds
        k = (x1 - x0) / 74.0
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        return unary_union([box(cx - 24 * k, cy + 4.5 * k, cx + 24 * k, cy + 20.5 * k),
                            box(cx - 24 * k, cy - 20.5 * k, cx + 24 * k, cy - 4.5 * k)])
    et_yazi = [(k, ad) for k, ad, q, cep in et if yaz is not None and _yazi_bolgesi(ad, q).intersection(yaz).area > 1]
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
    sonuc.update(ayak_kontrol(KTS))
    sonuc['yogunluk'] = yogunluk(KTS)
    try:
        import excel_yi
        sonuc['mmo_yuzey'] = list(excel_yi.YUZEY)
        sonuc['mmo_yuzey_asim'] = [y for y in excel_yi.YUZEY if y['Ty'] > y['sinir']]
    except Exception:
        pass
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
    kisa = {k: (len(v) if isinstance(v, list) else v) for k, v in sonuc.items() if k not in ('denetle', 'yogunluk', 'mmo_yuzey')}
    print('[kontrol]', json.dumps(kisa, ensure_ascii=False))
    print('[denetle]', json.dumps(ozet, ensure_ascii=False, default=str)[:1500])
    return sonuc


def ayak_kontrol(KTS):
    """15.10 (D) kollektör bağlantıları:
      AYAK-0  ayaklı devre / toplam (her devre kollektöre bağlı mı)
      AYAK-1  ayak–ayak, ayak–serpantin, ayak–kombi hattı kesişmesi (0 olmalı)
      AYAK-2  farklı hatlar arası 4 cm'den yakın (üst üste binme) — 0 olmalı
      AYAK-3  ayak duvarı yalnız kapı/geçişte keser (kapıdan geçiyor)
      AYAK-4  ayak ısıtılmayan mahal (merdiven, başka daire, ıslak hacim dışı) / başka mahalden geçmiyor
      AYAK-5  kombi–kollektör hattı var, kombi sıhhi plandaki yerde"""
    from shapely.geometry import LineString
    out = dict(ayak_bagli=0, ayak_toplam=0, ayak_kesisme=[], ayak_yakin=[], ayak_duvar=[], ayak_baska_mahal=[],
               kombi_hatti=[], kombi_hatti_yok=[])
    for KT in KTS:
        K = KT['K']
        kapilar = unary_union([q.buffer(12) for q in list(K.kapilar) + list(getattr(K, 'acikliklar', []))])
        cizgiler = []
        for o in KT['odalar']:
            for c in o['tasarim']['devreler']:
                out['ayak_toplam'] += 1
                tam = LineString([p[:2] for p in Y.tam_devre(c)])
                cizgiler.append(('devre %d' % c['no'], tam, o, c))
                if not c.get('ayak_g'):
                    continue
                out['ayak_bagli'] += 1
                hol = next((q for q in KT['odalar'] + KT.get('holler', []) if q['daire'] == o['daire'] and q['tur'] == 'hol'), None)
                ayak = unary_union([LineString(c['ayak_g']), LineString(c['ayak_d'])])
                izin = unary_union([o['poly'].buffer(1.5)] + ([hol['poly'].buffer(1.5)] if hol else []))
                dis = ayak.difference(izin)
                if dis.length > 0.5:
                    if not kapilar.covers(dis):
                        out['ayak_duvar'].append((KT['kat'], c['no'], o['zon'], round(dis.length, 1)))
                    # başka mahal / ısıtılmayan mahal
                    for r in K.rooms:
                        if r['poly'] is o['poly'] or (hol and r['poly'] is hol['poly']):
                            continue
                        if dis.intersection(r['poly'].buffer(-3)).length > 1.0:
                            out['ayak_baska_mahal'].append((KT['kat'], c['no'], o['zon'], r['name'].replace('\n', ' ')))
        for dno, son in (KT.get('kollektorler') or {}).items():
            if son and son.get('kombi_hat'):
                for h in (son['kombi_hat']['gidis'], son['kombi_hat']['donus']):
                    cizgiler.append(('kombi D%d' % dno, LineString(h), None, None))
                out['kombi_hatti'].append((KT['kat'], 'D%d' % dno))
            else:
                out['kombi_hatti_yok'].append((KT['kat'], 'D%d' % dno))
        for i in range(len(cizgiler)):
            for j in range(i + 1, len(cizgiler)):
                a, b = cizgiler[i], cizgiler[j]
                if a[1].distance(b[1]) > 6:
                    continue
                if a[1].intersects(b[1]):
                    # aynı kombi çiftinin ortak başlangıcı (kombi noktası) hariç
                    if a[0] == b[0] and a[0].startswith('kombi'):
                        kes = a[1].intersection(b[1])
                        if kes.geom_type == 'Point':
                            continue
                    out['ayak_kesisme'].append((KT['kat'], a[0], b[0]))
                elif a[1].distance(b[1]) < 4.0 - 1e-6:
                    out['ayak_yakin'].append((KT['kat'], a[0], b[0], round(a[1].distance(b[1]), 1)))
    return out


def yogunluk(KTS):
    """mahal başına boru yoğunluğu: m boru / mimari m² (kontrolörün ölçüsü) ve m / net ısıtma alanı"""
    out = []
    for KT in KTS:
        for o in KT['odalar']:
            # yoğunluk yalnız serpantin (ayaklar hariç)
            L = sum(S.uzunluk(c['pts']) / 100.0 for c in o['tasarim']['devreler'])
            Am = o.get('alan_mimari') or o['alan']
            out.append(dict(kat=KT['kat'], zon=o['zon'], daire='D%d' % o['daire'], ad=o['ad'], tur=o['tur'],
                            alan_mimari=Am, alan_poligon=o['alan'], alan_net=round(o['H'].area / 1e4, 2),
                            L_m=round(L, 2), devre=[c['L_m'] for c in o['tasarim']['devreler']],
                            m_m2_mimari=round(L / Am, 2), m_m2_poligon=round(L / o['alan'], 2),
                            m_m2_net=round(L / (o['H'].area / 1e4), 2)))
    return out
