# -*- coding: utf-8 -*-
"""2750/7 A-B blok SIHHİ — iki blok için tasarım (kat tasarımı, kolon numaralandırma, koridor dağıtımı,
bodrum, altyapı / rögarlar / parsel bacası, havalandırma şaftları, hesaplar). Çıktı: model pickle.

    python3 motor/ab2750/sihhi_proje.py            # ~3 dk -> /tmp/claude-0/sh/model_A.pkl, model_B.pkl
"""
import math
import os
import pickle
import sys
import time

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import sihhi_tasarim as T          # noqa: E402

ONB = T.ONB

BLOK = {
    'B': dict(sira=['Z', '1', '2'], ref='Z', ipucu=(27470, -26722), daire=30),
    'A': dict(sira=['1', '2', 'Z'], ref='1', ipucu=(32270, -34462), daire=48),
}
KAT_AD = {'B': 'BODRUM KAT', 'Z': 'ZEMİN KAT', '1': '1. KAT', '2': '2. KAT', 'C': 'ÇATI'}
KOT = {'A': {'B': -2.20, 'Z': 0.80, '1': 3.80, '2': 6.80, 'C': 9.80},
       'B': {'Z': 0.75, '1': 3.75, '2': 6.75, 'C': 9.75}}


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ====================================================================== kolon numaralandırma
def kolon_numarala(blok, Fs):
    """tüm katlardaki pis su kolonları Z çerçevesinde kümelenir (≤ 10 cm) -> P1..Pn (batıdan doğuya, kuzeyden güneye)"""
    noktalar = []
    for k, F in Fs.items():
        for no, D in F.daire.items():
            for W in D['islak']:
                if W.get('kolon'):
                    noktalar.append(((W['kolon'][0] - F.dx, W['kolon'][1]), k, no, W))
    kum = []
    for p, k, no, W in noktalar:
        for c in kum:
            if math.dist(c['p'], p) < 10:
                c['uye'].append((k, no, W))
                break
        else:
            kum.append(dict(p=p, uye=[(k, no, W)]))
    kum.sort(key=lambda c: (round(c['p'][0] / 50), -c['p'][1]))
    out = []
    for i, c in enumerate(kum, 1):
        ad = 'P%d' % i
        katlar = {}
        for k, no, W in c['uye']:
            W['kolon_no'] = ad
            katlar[k] = dict(daire=no, tip=W['tip'], sb=W.get('pis_sb', 0), mahal=W['mahal']['ad'])
        tip = 'mutfak' if all(v['tip'] == 'mutfak' for v in katlar.values()) else 'banyo'
        out.append(dict(no=ad, p=c['p'], katlar=katlar, tip=tip, sb=sum(v['sb'] for v in katlar.values())))
    for c in out:
        wc = c['tip'] == 'banyo'
        c['cap'] = T.pis_cap(c['sb'], wc)
    return out


# ====================================================================== yağmur inişleri (blok bazında numara)
def yagmur_numarala(blok, Fs):
    ref = Fs['Z']
    lst = []
    for y in ref.yagmur:
        lst.append(dict(inis=(y['inis'][0] - ref.dx, y['inis'][1]), mimari=y['mimari']))
    lst.sort(key=lambda q: (round(q['inis'][0] / 50), -q['inis'][1]))
    for i, q in enumerate(lst, 1):
        q['no'] = 'YB%d' % i
    for k, F in Fs.items():
        for y in getattr(F, 'yagmur', []):
            p = (y['inis'][0] - F.dx, y['inis'][1])
            best = min(lst, key=lambda q: math.dist(q['inis'], p))
            y['no'] = best['no'] if math.dist(best['inis'], p) < 15 else None
    return lst


# ====================================================================== ayak izi
def ayak_izi(F):
    pol = T.maske_poligon(F.ayak_izi_m, F.x0, F.y1, min_alan=1e6)
    g = max(pol, key=lambda q: q.area)
    return g.simplify(4)


# ====================================================================== altyapı (kolon dipleri -> rögarlar -> PB)
def _yerel(cephe):
    """cephe: dict(eksen='x'|'y', deger, yon(+1/-1)) -> (u, v) <-> (x, y) dönüşümleri; v dışarı (bina dışı +)"""
    if cephe['eksen'] == 'y':          # yatay cephe (y = deger), dışarısı yon*y
        f = lambda u, v: (u, cephe['deger'] + cephe['yon'] * v)
        g = lambda x, y: (x, (y - cephe['deger']) * cephe['yon'])
    else:
        f = lambda u, v: (cephe['deger'] + cephe['yon'] * v, u)
        g = lambda x, y: (y, (x - cephe['deger']) * cephe['yon'])
    return f, g


def altyapi_tasarla(blok, Fs, kolonlar, beton):
    """kolon dibi bağlantıları + rögar zinciri. Dönüş: dict(rogarlar, baglantilar, zincir, pb)"""
    FZ = Fs['Z']
    fp = ayak_izi(FZ)
    x0, y0, x1, y1 = fp.bounds
    D_R = 135.0            # rögar ekseni cepheden dışarı (cm)
    if blok == 'B':
        cepheler = {'K': dict(eksen='y', deger=y1, yon=1)}
        ata = lambda p: 'K'
    else:
        cepheler = {'B': dict(eksen='x', deger=x0, yon=-1), 'G': dict(eksen='y', deger=y0, yon=-1),
                    'D': dict(eksen='x', deger=x1, yon=1)}
        xw, xe = x0 + 1600, x1 - 1600
        yk = y0 + 900                      # kanat bölgesi (gövdenin kuzeyi)

        def ata(p):
            if p[0] < xw and p[1] > yk:
                return 'B'
            if p[0] > xe and p[1] > yk:
                return 'D'
            return 'G'
    kolon_engel = [Point(k['p']) for k in kolonlar]
    rogarlar, baglar, isler = [], [], []
    for ck, cf in cepheler.items():
        f, g = _yerel(cf)
        ks = sorted([k for k in kolonlar if ata(k['p']) == ck], key=lambda k: g(*k['p'])[0])
        # aynı hizadaki (|Δu| < 15) aynı tip kolonlar: uzaktaki, cepheye yakın olanın dibine bağlanır
        birles = []
        for k in ks:
            ku, kv = g(*k['p'])
            ara = [j for j in ks if j is not k and abs(g(*j['p'])[0] - ku) < 15 and kv < g(*j['p'])[1]]
            if ara:
                j = min(ara, key=lambda j: g(*j['p'])[1] - kv)
                if j['tip'] == k['tip'] and LineString([k['p'], j['p']]).intersection(beton.buffer(4)).length < 0.5:
                    birles.append((k, j))
        for k, j in birles:
            baglar.append(dict(kolon=k['no'], kolona=j['no'], yol=[k['p'], j['p']], cap=k['cap'] if k['cap'] >= 100 else 100))
            j.setdefault('ust_kolonlar', []).append(k['no'])
        ks = [k for k in ks if k not in [a for a, b in birles]]
        # kümeler: açıklık ≤ 420, en çok 2+2
        kumeler = []
        for k in ks:
            u = g(*k['p'])[0]
            if kumeler and u - g(*kumeler[-1][0]['p'])[0] <= 420 and len(kumeler[-1]) < 4:
                kumeler[-1].append(k)
            else:
                kumeler.append([k])
        for kum in kumeler:
            us = [g(*k['p'])[0] for k in kum]
            ur = (min(us) + max(us)) / 2
            # rögar betonarme/balkon kolonuna denk gelmesin
            for dd in (0, 30, -30, 60, -60, 90, -90):
                c = f(ur + dd, D_R)
                if not box(c[0] - 45, c[1] - 45, c[0] + 45, c[1] + 45).intersects(beton):
                    ur = ur + dd
                    break
            R = dict(cephe=ck, u=ur, p=f(ur, D_R), kolonlar=[k['no'] for k in kum])
            rogarlar.append(R)
            sol = sorted([k for k in kum if g(*k['p'])[0] < ur - 20], key=lambda k: -g(*k['p'])[0])
            sag = sorted([k for k in kum if g(*k['p'])[0] > ur + 20], key=lambda k: g(*k['p'])[0])
            orta = [k for k in kum if abs(g(*k['p'])[0] - ur) <= 20]
            ust = D_R - 35
            for grup, sg in ((sol, -1), (sag, 1)):
                for i, k in enumerate(grup):        # i=0 en yakın: yüksek seviye (binaya yakın)
                    isler.append(dict(k=k, f=f, g=g, giris_u=ur + sg * (8 + 20 * i), lvl=30 + 25 * i, ust=ust,
                                      rogar=len(rogarlar) - 1))
            for k in orta:
                isler.append(dict(k=k, f=f, g=g, giris_u=ur, lvl=None, ust=ust, rogar=len(rogarlar) - 1))
    # güzergâhlar: önce geometrik (dik + yatay), olmazsa ızgara (betonarme, kolon, rögar ve önceki hatlar yasak)
    yollar = [b['yol'] for b in baglar]
    rog_kutu = unary_union([box(r['p'][0] - 36, r['p'][1] - 36, r['p'][0] + 36, r['p'][1] + 36) for r in rogarlar])
    isler.sort(key=lambda j: abs(j['g'](*j['k']['p'])[1]) + abs(j['g'](*j['k']['p'])[0] - j['giris_u']))
    G = None
    for j in isler:
        k = j['k']
        ku, kv = j['g'](*k['p'])
        yol = _kolon_yolu(j['f'], ku, kv, j['giris_u'], j['lvl'], j['ust'], beton, kolon_engel, k, yollar, rog_kutu)
        if yol is None:
            if G is None:
                G = _altyapi_izgara(fp, beton, kolon_engel, rog_kutu)
            yol = _izgara_yolu(G, k['p'], j['f'](j['giris_u'], j['ust']), j['f'](j['giris_u'], j['ust'] - 30), yollar)
        if yol is None:          # kendi rögarı: cephe boyunca boş bir yere yeni rögar
            ck = rogarlar[j['rogar']]['cephe']
            for dd in (0, 60, -60, 100, -100, 140, -140, 180, -180, 240, -240):
                ur2 = ku + dd
                c = j['f'](ur2, D_R)
                kb = box(c[0] - 45, c[1] - 45, c[0] + 45, c[1] + 45)
                if kb.intersects(beton) or any(math.dist(c, r['p']) < 130 for r in rogarlar):
                    continue
                if any(LineString(y).distance(Point(c)) < 50 for y in yollar if len(y) > 1):
                    continue
                rogarlar.append(dict(cephe=ck, u=ur2, p=c, kolonlar=[k['no']]))
                rogarlar[j['rogar']]['kolonlar'].remove(k['no'])
                j['rogar'] = len(rogarlar) - 1
                rog_kutu = unary_union([rog_kutu, box(c[0] - 36, c[1] - 36, c[0] + 36, c[1] + 36)])
                G = _altyapi_izgara(fp, beton, kolon_engel, rog_kutu)
                yol = _kolon_yolu(j['f'], ku, kv, ur2, None if abs(dd) < 12 else 30, j['ust'], beton, kolon_engel, k,
                                  yollar, rog_kutu)
                if yol is None:
                    yol = _izgara_yolu(G, k['p'], j['f'](ur2, j['ust']), j['f'](ur2, j['ust'] - 30), yollar)
                break
        if yol is None:
            print('  UYARI altyapı güzergâhı bulunamadı', k['no'])
            yol = [k['p'], j['f'](ku, j['ust']), j['f'](j['giris_u'], j['ust'])]
        yollar.append(yol)
        cap = 125 if k['tip'] == 'banyo' else 100
        baglar.append(dict(kolon=k['no'], rogar=j['rogar'], yol=yol, cap=cap))
    for b_ in baglar:
        if 'rogar' in b_:
            b_['rogar_ref'] = rogarlar[b_['rogar']]
    rogarlar = [r for r in rogarlar if r['kolonlar']]
    for b_ in baglar:
        if 'rogar_ref' in b_:
            b_['rogar'] = rogarlar.index(b_.pop('rogar_ref'))
    return dict(rogarlar=rogarlar, baglar=baglar, ayak_izi=fp, cepheler=cepheler, D_R=D_R)


def _kolon_yolu(f, ku, kv, giris_u, lvl, ust, beton, kolon_engel, k, yollar=(), rog_kutu=None):
    """kolon (ku, kv<0) -> dik (cepheye doğru) -> lvl seviyesinde yatay -> rögar üst kenarına (giris_u, ust)"""
    adaylar = [0, 20, -20, 35, -35, 50, -50, 70, -70]
    onceki = [LineString(y) for y in yollar if len(y) > 1]
    for jog in adaylar:
        uu = ku + jog
        if lvl is None:
            if abs(uu - giris_u) > 12:
                continue
            pts_uv = [(ku, kv)] + ([(uu, kv)] if jog else []) + [(uu, ust)]
        else:
            pts_uv = [(ku, kv)] + ([(uu, kv)] if jog else []) + [(uu, lvl), (giris_u, lvl), (giris_u, ust)]
        pts = [f(u, v) for u, v in pts_uv]
        L = LineString(pts)
        if L.intersection(beton.buffer(4)).length > 0.5:
            continue
        if any(L.distance(q) < 12 for q in kolon_engel if q.distance(Point(pts[0])) > 1):
            continue
        if any(L.distance(o) < 8 for o in onceki):
            continue
        if rog_kutu is not None and len(pts) > 2 and LineString(pts[:-1]).intersection(rog_kutu).length > 0.5:
            continue
        return pts
    return None


def _altyapi_izgara(fp, beton, kolon_engel, rog_kutu):
    import sihhi_izgara as IZ
    x0, y0, x1, y1 = fp.bounds
    G = IZ.Izgara.kutu(x0 - 400, y0 - 400, x1 + 400, y1 + 400, 4.0)
    G.maliyet[:] = 1.0
    m = T.maske(G, [beton], 6)
    G.maliyet[m] = np.inf
    m = T.maske(G, [rog_kutu], 2)
    G.maliyet[m] = np.inf
    G.kolon_m = T.maske(G, [unary_union([q.buffer(14) for q in kolon_engel])])
    return G


def _izgara_yolu(G, a, giris, onu, yollar):
    cost = G.maliyet.copy()
    ka = G.hucre(a)
    km = G.kolon_m.copy()
    # başlangıç kolonu serbest
    km &= ~T.maske(G, [Point(a).buffer(16)])
    cost[km] = np.inf
    if yollar:
        cost[T.maske(G, [LineString(y).buffer(7) for y in yollar if len(y) > 1])] = np.inf
    serbest = T.maske(G, [Point(a).buffer(13)]) & np.isfinite(G.maliyet)
    cost[serbest] = 1.0
    for c in (ka, G.hucre(onu)):
        cost[c[1], c[0]] = 1.0
    yol = G.yol([ka], [G.hucre(onu)], donus=300.0, maliyet=cost)
    if yol is None:
        return None
    pts = [(float(x), float(y)) for x, y in G.koseler(yol)]
    pts[0] = a
    return pts + [giris]


def zincir_tasarla(blok, AY, pb_xy, ek_rogar=()):
    """rögarları cephe boyunca akış sırasına dizer, köşe rögarları ekler, PB'ye bağlar; aralık > 1500 ise ara rögar"""
    R = AY['rogarlar']
    D_R = AY['D_R']
    x0, y0, x1, y1 = AY['ayak_izi'].bounds
    hatlar = []
    if blok == 'B':
        kol = sorted([r for r in R if r['cephe'] == 'K'], key=lambda r: r['u'])
        yakin = [r for r in kol if abs(r['u'] - pb_xy[0]) < 150]
        if yakin:
            sonr = yakin[-1]
            pb_xy = (sonr['p'][0], pb_xy[1])
            diziler = [[r for r in kol if r['u'] <= sonr['u']]] + ([[r for r in kol if r['u'] > sonr['u']][::-1] + [sonr]]
                                                                 if any(r['u'] > sonr['u'] for r in kol) else [])
        else:
            son = dict(cephe='K', u=pb_xy[0], p=(pb_xy[0], y1 + D_R), kolonlar=[], kose=True)
            diziler = [kol + [son]]
            R.append(son)
            sonr = son
    else:
        kB = sorted([r for r in R if r['cephe'] == 'B'], key=lambda r: -r['u'])          # kuzeyden güneye
        kG = sorted([r for r in R if r['cephe'] == 'G'], key=lambda r: r['u'])            # batıdan doğuya
        kD = sorted([r for r in R if r['cephe'] == 'D'], key=lambda r: -r['u'])
        kBG = dict(cephe='BG', p=(x0 - D_R, y0 - D_R), kolonlar=[], kose=True)
        kDG = dict(cephe='DG', p=(x1 + D_R, y0 - D_R), kolonlar=[], kose=True)
        sonr = dict(cephe='G', u=pb_xy[0], p=(pb_xy[0], y0 - D_R), kolonlar=[], kose=True)
        R.extend([kBG, kDG, sonr])
        bat = [r for r in kG if r['u'] < pb_xy[0] - 50]
        dog = [r for r in kG if r['u'] > pb_xy[0] + 50][::-1]
        mid = sorted([r for r in kG if abs(r['u'] - pb_xy[0]) <= 160], key=lambda r: abs(r['u'] - pb_xy[0]))
        if mid:                          # PB önündeki rögar = son rögar
            R.remove(sonr)
            sonr = mid[0]
            pb_xy = (sonr['p'][0], pb_xy[1])
            bat = [r for r in kG if r['u'] < sonr['u']]
            dog = [r for r in kG if r['u'] > sonr['u']][::-1]
        diziler = [kB + [kBG] + bat + [sonr], kD + [kDG] + dog + [sonr]]
    # ara rögarlar (aralık > 1500)
    yeni = []
    for d in diziler:
        dd = [d[0]]
        for a, b in zip(d[:-1], d[1:]):
            L = math.dist(a['p'], b['p'])
            n = int(L // 1500)
            for i in range(1, n + 1):
                t = i / (n + 1)
                ara = dict(cephe='ara', p=(a['p'][0] + (b['p'][0] - a['p'][0]) * t, a['p'][1] + (b['p'][1] - a['p'][1]) * t),
                           kolonlar=[], ara=True)
                R.append(ara)
                dd.append(ara)
            dd.append(b)
        yeni.append(dd)
    diziler = yeni
    # numaralandırma: akış sırasıyla
    no = 1
    for d in diziler:
        for r in d:
            if 'no' not in r:
                r['no'] = 'R%d' % no
                no += 1
    pb = dict(no='PB', p=pb_xy)
    for d in diziler:
        for a, b in zip(d[:-1], d[1:]):
            hatlar.append(dict(a=a['no'], b=b['no'], yol=[a['p'], b['p']]))
    hatlar.append(dict(a=sonr['no'], b='PB', yol=[sonr['p'], pb_xy]))
    AY['diziler'] = [[r['no'] for r in d] for d in diziler]
    AY['zincir'] = hatlar
    AY['pb'] = pb
    AY['son'] = sonr['no']
    return AY


def rogar_hesap(AY, kolonlar):
    """her rögara akan SB (kolon + yukarı rögarlar), hat çapı, uzunluk, derinlik"""
    R = {r['no']: r for r in AY['rogarlar']}
    ks = {k['no']: k for k in kolonlar}
    for r in R.values():
        r['sb_kendi'] = sum(ks[k]['sb'] + sum(ks[u]['sb'] for u in ks[k].get('ust_kolonlar', [])) for k in r['kolonlar'])
    # akış grafı
    sonraki = {h['a']: h['b'] for h in AY['zincir']}
    sb = {n: R[n]['sb_kendi'] for n in R}
    sb['PB'] = 0
    sira = []
    gorulen = set()

    def topla(n):
        pass
    # topolojik: yaprak -> PB
    girdi = {}
    for a, b in sonraki.items():
        girdi.setdefault(b, []).append(a)

    def toplam(n):
        if n in gorulen:
            return sb[n]
        gorulen.add(n)
        s = (R[n]['sb_kendi'] if n in R else 0) + sum(toplam(a) for a in girdi.get(n, []))
        sb[n] = s
        return s
    toplam('PB')
    derin = {}

    def derinlik(n):
        if n in derin:
            return derin[n]
        ust = girdi.get(n, [])
        if not ust:
            derin[n] = 70.0
        else:
            derin[n] = max(derinlik(a) + 0.01 * math.dist(R[a]['p'], (R[n] if n in R else AY['pb'])['p']) + 2 for a in ust)
        return derin[n]
    derinlik('PB')
    for h in AY['zincir']:
        s = sb[h['a']]
        h['sb'] = s
        h['cap'] = max(150, T.pis_cap(s, True))
        h['L'] = math.dist(*h['yol'])
    for n, r in R.items():
        r['sb'] = sb[n]
        r['h'] = math.ceil(derin[n] / 5) * 5
        r['olcu'] = '70x70' if r['h'] <= 100 else '80x80'
    AY['pb']['h'] = math.ceil(derin['PB'] / 5) * 5 + 10
    AY['pb']['sb'] = sb['PB']
    return AY


# ====================================================================== havalandırma (penceresiz banyo)
def havalandirma(blok, Fs):
    """her banyo: tavanda aspiratör (80 m³/h-50 Pa, Ø150) -> en yakın şaft hücresi (merkezi ısıtma şaftı yanındaki
    kanal) ; yoksa banyo köşesinde düşey Ø150 kanal kutusu. Şaftlar kat bazında Z çerçevesinde birleştirilir."""
    saftlar = []
    for k, F in Fs.items():
        for no, D in F.daire.items():
            for W in D['islak']:
                if W['tip'] != 'banyo':
                    continue
                poly = W['poly']
                best = None
                for s in F.saft:
                    d = s['poly'].distance(poly)
                    if d < 30 and (best is None or d < best[0]):
                        best = (d, s['poly'])
                if best:
                    sp = best[1]
                    q1, q2 = None, None
                    from shapely.ops import nearest_points
                    a, b = nearest_points(poly, sp)
                    hedef = (sp.centroid.x, sp.centroid.y)
                    W['hav'] = dict(saft=hedef, duvar=(a.x, a.y), tip='saft')
                else:
                    W['hav'] = dict(saft=None, tip='kanal')
                    # kolon karşısı köşe kanal kutusu: kolon köşesine yakın, 20 cm içeride
                    W['hav']['saft'] = (W['kolon'][0], W['kolon'][1]) if W.get('kolon') else None
                if W['hav']['saft']:
                    hz = (W['hav']['saft'][0] - F.dx, W['hav']['saft'][1])
                    for s in saftlar:
                        if math.dist(s['p'], hz) < 40:
                            s['bag'].append((k, no, W))
                            break
                    else:
                        saftlar.append(dict(p=hz, bag=[(k, no, W)]))
    saftlar.sort(key=lambda s: (round(s['p'][0] / 50), -s['p'][1]))
    for i, s in enumerate(saftlar, 1):
        s['no'] = 'Ş%d' % i
        s['debi'] = 80 * len(s['bag'])
        for k, no, W in s['bag']:
            W['hav']['no'] = s['no']
    return saftlar


# ====================================================================== bodrum (A blok)
def bodrum_tasarla(FB, riser_z, kolonlar_Z_dx):
    """A blok bodrum: WC/lavabo hücreleri, abdest tezgâhları, mutfak nişi -> pis su çukuru (dalgıç pompa 1+1);
    temiz su riser dibinden ortak alan sayacıyla."""
    import sihhi_izgara as IZ
    K = FB.K
    T._izgara_katmanlari(FB)
    G = FB.G
    arm = []
    for a in K.armatur:
        if a['tip'] in ('WC', 'LV', 'EV'):
            r = T._armatur_kayit(a, None)
            arm.append(r)
        elif a['tip'] == 'ABDEST_TEZGAH':
            x0, y0, x1, y1 = a['kutu'].bounds
            L = max(x1 - x0, y1 - y0)
            if L < 150:                 # mutfak nişi tezgâhı (eviye ayrıca tanındı)
                continue
            n = a['normal']
            w = a['duvar']
            arm.append(dict(tip='ABD', p=a['p'], kutu=a['kutu'], n=n, w=w, ek=False, adet=max(2, int(L // 70)),
                            gider=(a['p'][0] + 0, a['p'][1]), musluk=(w[0] + n[0] * 6, w[1] + n[1] * 6)))
    # pis su çukuru: WC sırasının doğusunda hol (kat koordinatı)
    cuk = (24330.0, -34985.0)
    # pis su ağı: çukurdan ağaç (tüm bodrum serbest + duvar geçişi), dönüş cezalı; döşeme altı
    cost = np.where(FB.duvar4, 40.0, 2.0)
    cost[FB.beton4 | FB.yasak4] = np.inf
    kok = G.hucre(cuk)
    agac, kenar = {kok}, set()
    hed = {}
    for a in arm:
        hed.setdefault(G.hucre(a['gider']), []).append(a)
    kalan = dict(hed)
    while kalan:
        yol = G.yol(list(agac), list(kalan.keys()), donus=80.0, maliyet=cost)
        if yol is None:
            break
        for p, q in zip(yol[:-1], yol[1:]):
            kenar.add((p, q))
        agac.update(yol)
        for c in list(kalan):
            if c in agac:
                kalan.pop(c)
    par, cocuk, zin = T._agac_zincirleri(kenar, kok, list(hed.keys()))
    sbh = {}
    for c, lst in hed.items():
        s = sum(T.SB['ABD'] * a.get('adet', 1) if a['tip'] == 'ABD' else T.SB[a['tip']] for a in lst)
        wc = any(a['tip'] == 'WC' for a in lst)
        cc = c
        while cc is not None:
            v = sbh.get(cc, (0, False))
            sbh[cc] = (v[0] + s, v[1] or wc)
            cc = par.get(cc)
    pis = []
    for z in zin:
        pts = [(float(x), float(y)) for x, y in G.koseler(z)]
        s, wc = sbh.get(z[-1], (0, False))
        pis.append(dict(yol=pts[::-1], sb=s, cap=T.pis_cap(s, wc)))
    # temiz su: riser dibinden (bodrum holü) ortak alan sayacı -> armatürler
    rp = (riser_z[0] + FB.dx, riser_z[1])
    cost2 = np.where(FB.duvar4, 60.0, 1.0 + 6.0 * np.exp(-FB.dduvar / 20.0))
    cost2[FB.beton4 | FB.yasak4 | FB.saft4] = np.inf
    k2 = G.hucre(rp)
    agac, kenar = {k2}, set()
    hedm = {}
    for a in arm:
        hedm.setdefault(G.hucre(a['musluk']), []).append(a)
    kalan = dict(hedm)
    while kalan:
        yol = G.yol(list(agac), list(kalan.keys()), donus=60.0, maliyet=cost2)
        if yol is None:
            break
        for p, q in zip(yol[:-1], yol[1:]):
            kenar.add((p, q))
        agac.update(yol)
        for c in list(kalan):
            if c in agac:
                kalan.pop(c)
    par, cocuk, zin = T._agac_zincirleri(kenar, k2, list(hedm.keys()))
    ys, yh, sic = {}, {}, set()
    for c, lst in hedm.items():
        for a in lst:
            t = 'ABD' if a['tip'] == 'ABD' else a['tip']
            s_, h_ = T.YB[t]
            n = a.get('adet', 1)
            cc = c
            while cc is not None:
                ys[cc] = ys.get(cc, 0) + s_ * n
                if t in ('LV', 'EV', 'ABD'):
                    yh[cc] = yh.get(cc, 0) + (0.5 if t != 'ABD' else 0.25) * n
                    sic.add(cc)
                cc = par.get(cc)
    sog, sicak = [], []
    for z in zin:
        pts = [(float(x), float(y)) for x, y in G.koseler(z)]
        sog.append(dict(yol=pts, yb=round(ys.get(z[-1], 0), 2)))
        if z[-1] in sic:
            sicak.append(dict(yol=[(x + 5, y + 5) for x, y in pts], yb=round(yh.get(z[-1], 0), 2)))
    sb_top = sum(T.SB['ABD'] * a.get('adet', 1) if a['tip'] == 'ABD' else T.SB[a['tip']] for a in arm)
    return dict(armatur=arm, cukur=cuk, pis=pis, soguk=sog, sicak=sicak, sb=sb_top, riser=rp,
                yb_s=ys.get(k2, 0), yb_h=yh.get(k2, 0))


# ====================================================================== ana akış
def blok_tasarla(blok):
    cfg = BLOK[blok]
    Fs = {}
    for k in cfg['sira']:
        Fs[k] = T.Kat(blok, k)
    ref = Fs[cfg['ref']]
    for k in cfg['sira']:
        alt = [Fs[q] for q in cfg['sira'] if q != k]
        T.kat_tasarla(Fs[k], ref, alt)
        log(blok, k, 'kat tasarımı')
    riser = T.riser_bul(list(Fs.values()), cfg['ipucu'])
    log(blok, 'riser', riser)
    for k in cfg['sira']:
        T.koridor_tasarla(Fs[k], riser)
    kolonlar = kolon_numarala(blok, Fs)
    yb = yagmur_numarala(blok, Fs)
    beton = unary_union([F.beton for F in []] + [Fs['Z'].beton])
    # bodrum
    bod = None
    if blok == 'A':
        FB = T.Kat('A', 'B')
        bod = bodrum_tasarla(FB, riser, None)
        bod['F'] = FB
        log('A bodrum', len(bod['armatur']), 'armatür, SB', bod['sb'])
    AY = altyapi_tasarla(blok, Fs, kolonlar, Fs['Z'].beton)
    x0, y0, x1, y1 = AY['ayak_izi'].bounds
    if blok == 'B':
        pb = (x1 - 250, y1 + AY['D_R'] + 260)
    else:
        pb = (32100.0, y0 - AY['D_R'] - 260)
    zincir_tasarla(blok, AY, pb)
    rogar_hesap(AY, kolonlar)
    hav = havalandirma(blok, Fs)
    M = dict(blok=blok, Fs=Fs, riser=riser, kolonlar=kolonlar, yagmur=yb, altyapi=AY, bodrum=bod, hav=hav)
    return M


def kaydet(M):
    pickle.dump(M, open(f"{ONB}/model_{M['blok']}.pkl", 'wb'))


def yukle(blok):
    return pickle.load(open(f'{ONB}/model_{blok}.pkl', 'rb'))


if __name__ == '__main__':
    bl = sys.argv[1:] or ['B', 'A']
    for b in bl:
        t = time.time()
        M = blok_tasarla(b)
        kaydet(M)
        log(b, 'bitti', round(time.time() - t), 's', 'kolon', len(M['kolonlar']), 'rögar', len(M['altyapi']['rogarlar']))
