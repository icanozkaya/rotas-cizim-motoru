#!/usr/bin/env python3
"""sihhi2 — DAİRE BESLEMELERİ VE SAYAÇ GRUBU (kat planlarında), 15.10.2026 (D) kullanıcı geri bildirimi.

Kurgu (kolon şeması ile AYNI mantık, sema.py `sebeke_sayac_depo`):
    şebeke girişi (bina girişinden, döşeme altından) -> vana – pislik tutucu – çek valf – vana -> DEPO DOLUM kolonu ↑
    (çatı deposu) ; by-pass çek valf ; DEPO DÖNÜŞ kolonu ↓ -> sayaç kollektörü -> 9 sıra
    (vana – pislik tutucu – sayaç – çek valf – vana) -> her daireye AYRI besleme hattı.
    Zemin kat daireleri sayaçtan doğrudan kapı yanındaki giriş işaretine; üst kat daireleri merdiven holündeki
    TEMİZ SU KOLON KUTUSU'ndaki kendi kolonuyla (her katta aynı nokta) katına çıkar, oradan kapı yanına.

Yerleşim (zemin kat koordinatı; her kat aynı: kat ofseti eklenir) `tasarim_new_block.json` -> "temiz_su_besleme".
Hatlar paralel şeritlerde, birbirini kesmez; kapı açılım alanından, duvar/betonarmeden geçmez (kontrol()).
"""
import math

import ezdxf
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

L_SOG = 'ROTAS-SIHHI-SOGUK-SU'
L_SEB = 'ROTAS-SIHHI-SEBEKE'
L_SAY = 'ROTAS-SIHHI-SAYAC'
L_TCAP = 'ROTAS-SIHHI-TEMIZ-SU-CAP'
L_KIL = 'ROTAS-SEMBOL-KILAVUZ'
B_KOLON = 'ROTAS-S2-TS-KOLON'
B_OLCER = 'ROTAS-S2-SU-OLCER'          # su sayacı (plan). Blok adında 'SAYAC' yok: kontrolör şema paftasını sayaç
B_PISLIK = 'ROTAS-S2-PISLIK-TUTUCU'    # sembolü sayısıyla da bulabiliyor; plan sayaçları şemayla karışmasın
B_CEK = 'ROTAS-S2-CEKVALF'
B_VANA = 'ROTAS-S2-KURESEL-VANA'

VARSAYILAN = {
    'not': 'zemin kat koordinatı (cm). Kolon kutusu merdiven holünde doğu duvarında S10 kolonunun yanında; sayaç grubu '
           'hemen altında (bina girişi kapısından ~1,5 m). Şebeke bina girişinden döşeme altından girer.',
    'kolon_x': 253672.0, 'kolon_y0': -442262.0, 'kolon_aralik': 8.0, 'kolon_r': 2.5,
    'kolektor_x': 253678.5,
    'sayac_y0': -442335.0, 'sayac_aralik': 10.0, 'sayac_bitis_x': 253623.0,
    'serit_x0': 253617.0, 'serit_aralik': 6.0,
    'duvar_serit': {'dogu': 253678.5, 'bati': 253672.5},
    'dirsek_y': {'dogu': -442440.0, 'bati': -442446.0},
    'ust_serit': {'dogu': 253661.0, 'bati': 253655.0},
    'sebeke': [[254262.0, -442078.0], [253580.0, -442078.0], [253580.0, -442252.0], [253672.0, -442252.0]],
    'sebeke_armatur_y': [-442112.0, -442130.0, -442148.0, -442166.0],
    'kapi_yasak_Z': [{'merkez': [253683.0, -442083.0], 'r': 100.0, 'aci': [180.0, 270.0]},
                     {'merkez': [253683.0, -442233.0], 'r': 50.0, 'aci': [90.0, 180.0]}],
}


def dad(x):
    """daire adı: 3 -> 'D3' (kolon adları DOLUM/DONUS olduğu gibi)"""
    return 'D%d' % x if isinstance(x, int) else str(x)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def ayar(TASARIM):
    c = dict(VARSAYILAN)
    c.update(TASARIM.get('temiz_su_besleme', {}))
    return c


def bloklar(doc):
    B = doc.blocks
    if B_KOLON in B:
        return
    b = B.new(B_KOLON)                    # temiz su kolonu (plan): r 2,5 + nokta
    b.add_circle((0, 0), 2.5)
    b.add_circle((0, 0), 0.8)
    b = B.new(B_OLCER)                    # su sayacı: daire + içinden geçen hat + 'M' çizgisi (r 3)
    b.add_circle((0, 0), 3.0)
    b.add_lwpolyline([(-1.6, -1.2), (-1.6, 1.4), (0, 0), (1.6, 1.4), (1.6, -1.2)])
    b = B.new(B_PISLIK)                   # pislik tutucu (Y): gövde + eğik sepet
    b.add_lwpolyline([(-3, 0), (3, 0)])
    b.add_lwpolyline([(-1.5, 0), (1.0, -2.8), (2.8, -1.0), (0.5, 0)])
    b = B.new(B_CEK)                      # çek valf: üçgen + bar
    b.add_lwpolyline([(-3, -2.2), (-3, 2.2), (2, 0)], close=True)
    b.add_line((2.6, -2.4), (2.6, 2.4))


def katmanlar(doc):
    lts = doc.linetypes
    if 'ROTAS_SEBEKE' not in lts:
        lts.add('ROTAS_SEBEKE', pattern=[30.0, 20.0, -6.0, 2.0, -6.0], description='ŞEBEKE (DÖŞEME ALTI) -- . --')
    for ad, renk, lt, lw in ((L_SEB, 5, 'ROTAS_SEBEKE', 30), (L_SAY, 5, 'Continuous', 18)):
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk, linetype=lt, lineweight=lw)


def temiz_yol(pts):
    out = []
    for p in pts:
        p = (float(p[0]), float(p[1]))
        if out and dist(out[-1], p) < 0.05:
            continue
        out.append(p)
    i = 1
    while i < len(out) - 1:
        a, b, c = out[i - 1], out[i], out[i + 1]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) < 1e-6:
            out.pop(i)
        else:
            i += 1
    return out


def yon_sinifi(G, cfg):
    """daire girişi (zemin koordinatı) -> 'kuzey' (kolon kutusunun üstü) / 'bati' / 'dogu'"""
    if G[1] > cfg['kolon_y0']:
        return 'kuzey'
    return 'dogu' if G[0] > cfg['kolon_x'] - 60 else 'bati'


def kurgu(Ks, katlar, KATLAR, cfg, mb_fmt, inc):
    """tüm katların hat / sembol / etiket planı (zemin koordinatında, kat ofseti sonra eklenir).
    Dönüş: dict(kat -> dict(hatlar=[(pts, katman, ad)], semboller=[(blok, p, rot, katman)], kolonlar=[(ad, p)],
                etiketler=[...]), kolon_sira=[...], daireler={dno: dict(kat, yon, G, mb)})"""
    daireler = {}
    for K in Ks:
        kat = katlar[K.k]
        for dno, ts in kat['temiz'].items():
            G = (ts['G'][0] - K.off, ts['G'][1])
            daireler[dno] = dict(kat=KATLAR.index(K.k), k=K.k, G=G, yon=yon_sinifi(G, cfg), mb=ts['toplam'])
    ust = sorted({d['kat'] for d in daireler.values() if d['kat'] > 0})
    sira = ['DOLUM', 'DONUS']
    for yon in ('kuzey', 'bati', 'dogu'):
        for kt in ust:
            sira += sorted(dn for dn, d in daireler.items() if d['kat'] == kt and d['yon'] == yon)
    kx, ky0, ka = cfg['kolon_x'], cfg['kolon_y0'], cfg['kolon_aralik']
    kr = cfg['kolon_r']
    kol_y = {ad: ky0 - ka * i for i, ad in enumerate(sira)}
    toplam = sum(d['mb'] for d in daireler.values())
    plan = {}
    for K in Ks:
        ki = KATLAR.index(K.k)
        P = dict(hatlar=[], semboller=[], kolonlar=[], etiketler=[], kutu=None)
        plan[K.k] = P
        burada = [ad for ad in sira if ad in ('DOLUM', 'DONUS') or daireler[ad]['kat'] >= ki]
        if ki > 0:
            burada = [ad for ad in burada if ad in ('DOLUM', 'DONUS') or daireler[ad]['kat'] >= ki]
        else:
            burada = list(sira)
        for ad in burada:
            P['kolonlar'].append((ad, (kx, kol_y[ad])))
        ys = [kol_y[a] for a in burada]
        P['kutu'] = (kx - kr - 4.0, min(ys) - kr - 4.0, cfg['kolektor_x'] + 2.5, max(ys) + kr + 4.0)
        kat_dn = sorted(dn for dn, d in daireler.items() if d['kat'] == ki)
        if ki == 0:
            _zemin(P, cfg, daireler, sira, kol_y, kat_dn, toplam, mb_fmt, inc)
        else:
            for dn in kat_dn:
                d = daireler[dn]
                y = kol_y[dn]
                G = d['G']
                if d['yon'] == 'kuzey':
                    pts = [(kx - kr, y), (G[0], y), G]
                else:
                    xs = cfg['ust_serit'][d['yon']]
                    xw = cfg['duvar_serit'][d['yon']]
                    yj = cfg['dirsek_y'][d['yon']]
                    pts = [(kx - kr, y), (xs, y), (xs, yj), (xw, yj), (xw, G[1]), G]
                P['hatlar'].append((temiz_yol(pts), L_SOG, dn))
                P['etiketler'].append(dict(tur='daire', ad=dn, hat=dn, satir={'C1': inc(d['mb']), 'M1': mb_fmt(d['mb'])}))
    return dict(plan=plan, sira=sira, kol_y=kol_y, daireler=daireler, toplam=toplam, cfg=cfg)


def _zemin(P, cfg, daireler, sira, kol_y, kat_dn, toplam, mb_fmt, inc):
    kx, kr = cfg['kolon_x'], cfg['kolon_r']
    xk = cfg['kolektor_x']
    # ---- şebeke: bina girişinden döşeme altından, armatürler (vana – pislik tutucu – çek valf – vana), DOLUM kolonuna
    seb = [tuple(p) for p in cfg['sebeke']]
    P['hatlar'].append((temiz_yol(seb + [(kx, kol_y['DOLUM'] + kr)]), L_SEB, 'SEBEKE'))
    xa = seb[1][0]
    for y, b in zip(cfg['sebeke_armatur_y'], (B_VANA, B_PISLIK, B_CEK, B_VANA)):
        P['semboller'].append((b, (xa, y), -90.0, L_SAY))
    # by-pass (çek valf) şebeke -> kollektör; DÖNÜŞ kolonu -> kollektör
    yb = seb[-1][1]
    satirlar = [dn for dn in sira[::-1] if dn not in ('DOLUM', 'DONUS')]          # en alttaki kolon en üst sırada
    kuzey0 = [dn for dn in kat_dn if daireler[dn]['yon'] == 'kuzey']
    bati0 = [dn for dn in kat_dn if daireler[dn]['yon'] == 'bati']
    dogu0 = [dn for dn in kat_dn if daireler[dn]['yon'] == 'dogu']
    satirlar += kuzey0 + bati0 + dogu0
    ys = [cfg['sayac_y0'] - cfg['sayac_aralik'] * i for i in range(len(satirlar))]
    P['hatlar'].append((temiz_yol([(kx, yb), (xk, yb), (xk, ys[-1])]), L_SOG, 'KOLLEKTOR'))
    P['semboller'].append((B_CEK, (xk, (yb + kol_y['DONUS']) / 2.0), -90.0, L_SAY))      # by-pass çek valf
    P['hatlar'].append((temiz_yol([(kx + kr, kol_y['DONUS']), (xk, kol_y['DONUS'])]), L_SOG, 'DONUS'))
    # ---- sayaç sıraları: kollektör -> vana – pislik tutucu – sayaç – çek valf – vana -> uç
    xb = cfg['sayac_bitis_x']
    for dn, y in zip(satirlar, ys):
        for dx, b in ((6.0, B_VANA), (14.0, B_PISLIK), (23.0, B_OLCER), (31.0, B_CEK), (39.0, B_VANA)):
            P['semboller'].append((b, (xk - dx, y), 180.0 if b in (B_CEK, B_PISLIK) else 0.0, L_SAY))
    P['sayac'] = dict(adet=len(satirlar), satirlar=satirlar, ys=ys,
                      kutu=(xb - 1.0, ys[-1] - 5.0, xk + 2.5, ys[0] + 5.0))
    # ---- sıra uçlarından şeritlere
    x0, sa = cfg['serit_x0'], cfg['serit_aralik']
    j = 0
    for dn, y in zip(satirlar, ys):
        d = daireler[dn]
        G = d['G']
        if d['kat'] > 0:                            # üst kat kolonuna
            xj = x0 - sa * j
            j += 1
            pts = [(xk, y), (xj, y), (xj, kol_y[dn]), (kx - kr, kol_y[dn])]
        elif d['yon'] == 'kuzey':
            pts = [(xk, y), (G[0], y), G]
        else:
            xs = x0 if d['yon'] == 'dogu' else x0 - sa
            xw = cfg['duvar_serit'][d['yon']]
            yj = cfg['dirsek_y'][d['yon']]
            pts = [(xk, y), (xs, y), (xs, yj), (xw, yj), (xw, G[1]), G]
        P['hatlar'].append((temiz_yol(pts), L_SOG, dn))
        if d['kat'] == 0:
            P['etiketler'].append(dict(tur='daire', ad=dn, hat=dn, satir={'C1': inc(d['mb']), 'M1': mb_fmt(d['mb'])}))
    P['etiketler'].append(dict(tur='sebeke', ad='SEBEKE', hat='SEBEKE', satir={'C1': inc(toplam), 'M1': mb_fmt(toplam)}))
    P['etiketler'].append(dict(tur='sayac_grubu', ad='SAYAC'))


# ====================================================================== ÇİZİM
def ciz(doc, eng, Ks, katlar, KATLAR, TASARIM, P_):
    """kat planlarına besleme hatları, kolon kutusu, sayaç grubu. P_: plan modülü (yardımcılar)."""
    cfg = ayar(TASARIM)
    bloklar(doc)
    katmanlar(doc)
    msp = doc.modelspace()
    kur = kurgu(Ks, katlar, KATLAR, cfg, P_.fmt_mb, P_.inc)
    for K in Ks:
        P = kur['plan'][K.k]
        o = K.off
        tr = lambda p: (p[0] + o, p[1])
        P['dunya'] = []
        for pts, lay, ad in P['hatlar']:
            w = [tr(p) for p in pts]
            msp.add_lwpolyline(w, dxfattribs={'layer': lay})
            eng.ekle_cizgi(LineString(w))
            P['dunya'].append((w, lay, ad))
        for b, p, rot, lay in P['semboller']:
            P_.ekle_insert(msp, b, tr(p), lay, rot=rot)
            eng.ekle_alan(Point(tr(p)).buffer(3.5))
        for ad, p in P['kolonlar']:
            P_.ekle_insert(msp, B_KOLON, tr(p), L_SOG)
            eng.ekle_alan(Point(tr(p)).buffer(cfg['kolon_r'] + 0.5))
        x0, y0, x1, y1 = P['kutu']
        msp.add_lwpolyline([tr((x0, y0)), tr((x1, y0)), tr((x1, y1)), tr((x0, y1))], close=True,
                           dxfattribs={'layer': L_SAY})
        if 'sayac' in P:
            sx0, sy0, sx1, sy1 = P['sayac']['kutu']
            msp.add_lwpolyline([tr((sx0, sy0)), tr((sx1, sy0)), tr((sx1, sy1)), tr((sx0, sy1))], close=True,
                               dxfattribs={'layer': L_SAY, 'linetype': 'ROTAS_BASMA'})
    return kur


def _hat_parcalari(pts):
    return [(a, b) for a, b in zip(pts[:-1], pts[1:]) if dist(a, b) > 0.5]


def etiketle(doc, eng, Ks, kur, P_):
    """besleme hattı etiketleri (kullanıcı bloğu TS-CAP2 '1 1/4"' / '9.5 MB'), sayaç sırası daire adı, sayaç grubu
    tablosu, şebeke. Her hat TEK etiket; yazı hiçbir hatta / yazıya / sembole binmez, kanca başka hattı kesmez."""
    msp = doc.modelspace()
    uyari = []
    for K in Ks:
        P = kur['plan'][K.k]
        o = K.off
        hatlar = {ad: w for w, lay, ad in P['dunya']}
        for et in sorted(P['etiketler'], key=lambda q: q['tur'] != 'sayac_grubu'):
            if et['tur'] == 'sira':                     # sayaç sırası: daire adı (h 6) sıra ucunun üstünde
                t = msp.add_text(dad(et['ad']), dxfattribs={'layer': L_TCAP, 'height': 6.0, 'style': 'ROTAS-YAZI',
                                                       'width': 0.8})
                t.dxf.insert = (et['p'][0] + o, et['p'][1])
                for pg in P_.yazi_kutulari(t):
                    eng.ekle_alan(pg)
                continue
            if et['tur'] == 'sayac_grubu':
                if not _sayac_tablosu(msp, eng, K, P, kur, P_):
                    uyari.append('kat %s sayaç grubu tablosu yerleşmedi' % K.k)
                continue
            w = hatlar.get(et['hat'])
            if w is None:
                continue
            sat = dict(et['satir'])
            if et['tur'] == 'sebeke':
                ok = _etiket(msp, eng, K, w, sat, P_, oncelik='bas', blok='ROTAS-S2-TS-CAP2', on_ek='ŞEBEKEDEN ')
            else:
                ok = _etiket(msp, eng, K, w, sat, P_, on_ek=dad(et['ad']) + ': ')
            if not ok:
                uyari.append('kat %s %s besleme etiketi yerleşmedi' % (K.k, dad(et['ad'])))
    return uyari


def _etiket(msp, eng, K, w, sat, P_, oncelik='uzun', blok='ROTAS-S2-TS-CAP2', on_ek=''):
    """hat w üstünde bir nokta -> dik kanca -> TS-CAP2 yazısı. Adaylar: en uzun parçalar, parça boyunca."""
    parcalar = _hat_parcalari(w)
    if oncelik == 'bas':
        parcalar = parcalar[:1] + sorted(parcalar[1:], key=lambda ab: -dist(*ab))
    else:
        parcalar = sorted(parcalar, key=lambda ab: -dist(*ab))
    sat = dict(sat)
    if on_ek:
        sat['C1'] = on_ek + sat['C1']
    kendi = LineString(w)
    for a, b in parcalar[:4]:
        L = dist(a, b)
        if L < 12:
            continue
        yatay = abs(b[1] - a[1]) < abs(b[0] - a[0])
        for t in (0.5, 0.35, 0.65, 0.2, 0.8, 0.1, 0.9):
            A = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            for hk in (14, 20, 30, 42, 56):
                for s in (1, -1):
                    for s2 in (1, -1):
                        if yatay:
                            H = (A[0], A[1] + s * hk)
                        else:
                            H = (A[0] + s * hk, A[1])
                        e = P_.ekle_insert(msp, blok, (0, 0), L_TCAP, attr=sat)
                        kut = P_.yazi_kutulari(e)
                        if not kut:
                            msp.delete_entity(e)
                            return False
                        bx0 = min(k.bounds[0] for k in kut)
                        bx1 = max(k.bounds[2] for k in kut)
                        by0 = min(k.bounds[1] for k in kut)
                        by1 = max(k.bounds[3] for k in kut)
                        if yatay:
                            ix = H[0] + 2 if s2 > 0 else H[0] - 2 - (bx1 - bx0)
                            ix -= bx0
                            iy = H[1] + 2 - by0 if s > 0 else H[1] - 2 - by1
                        else:
                            ix = H[0] + 2 - bx0 if s > 0 else H[0] - 2 - bx1
                            iy = H[1] + (2 - by0 if s2 > 0 else -2 - by1)
                        msp.delete_entity(e)
                        e = P_.ekle_insert(msp, blok, (ix, iy), L_TCAP, attr=sat)
                        kut = P_.yazi_kutulari(e)
                        kanca = LineString([A, H])
                        ku = unary_union(kut)
                        sorun = (any(eng.carpar(k.buffer(1.5, join_style=2)) for k in kut)
                                 or eng.yasakta(ku, 'duvar', tol=2.0) or eng.yasakta(ku, 'asansor')
                                 or not K.bina.buffer(-2).contains(ku)
                                 or K.kapi_u.intersects(ku) or K.kapi_u.intersects(kanca)
                                 or K.S.intersection(kanca).length > 0.5)
                        if not sorun:
                            kk = LineString([A, H]).difference(Point(A).buffer(8.0))      # paralel eş hat (6 cm) kancanın dibinde geçebilir
                            if not kk.is_empty and eng.carpar(kk.buffer(0.3), cizgi_tol=0.5, haric=()):
                                # kanca kendi hattı dışında başka hatta değmesin
                                sorun = any(g.intersects(kk) and g.distance(kendi) > 0.1 for g in eng.cizgi
                                            if g.intersects(kk.buffer(0.3)))
                        if sorun:
                            msp.delete_entity(e)
                            continue
                        for k in kut:
                            eng.ekle_alan(k)
                        x_u0, x_u1 = min(k.bounds[0] for k in kut), max(k.bounds[2] for k in kut)
                        msp.add_lwpolyline([A, H], dxfattribs={'layer': L_TCAP})
                        if yatay:
                            msp.add_line(H, (x_u1 if s2 > 0 else x_u0, H[1]), dxfattribs={'layer': L_TCAP})
                        eng.ekle_cizgi(kanca)
                        return True
    return False


def _sayac_tablosu(msp, eng, K, P, kur, P_):
    """sayaç grubunun altında (hatsız boş yerde, merdiven holü) tablo: 'SU SAYAÇ GRUBU (9 AD.)' + her sıra
    'Dn  çap / MB' + depo kolonları. Kılavuz yok (her kılavuz besleme şeritlerini keserdi); tablo grubun hemen altında."""
    o = K.off
    sat = ['SAYAÇ GRUBU %d AD. (üstten)' % P['sayac']['adet']]
    for dn in P['sayac']['satirlar']:
        d = kur['daireler'][dn]
        sat.append('%s %s / %s' % (dad(dn), P_.inc(d['mb']), P_.fmt_mb(d['mb'])))
    sat.append('DEPO KOL. %s' % P_.inc(kur['toplam']))
    h, ara = 8.0, 12.0
    sx0, sy0, sx1, sy1 = P['sayac']['kutu']
    for dy in (-45, -55, -65, -80, -95, -110, -130, -160, -200, -240, -280, -320):
        for x in (sx0 - 40, sx0 - 45, sx0 - 35, sx0 - 50, sx0 - 30, sx0 - 60, sx0 - 80, sx0 - 100):
            y_ust = sy0 + dy
            ents = []
            for i, s in enumerate(sat):
                t = msp.add_text(s, dxfattribs={'layer': L_TCAP, 'height': h, 'style': 'ROTAS-YAZI', 'width': 0.8})
                t.dxf.insert = (x + o, y_ust - ara * i)
                ents.append(t)
            kut = [pg for t in ents for pg in P_.yazi_kutulari(t)]
            ku = unary_union(kut)
            sorun = (any(eng.carpar(k.buffer(1.5, join_style=2)) for k in kut) or eng.yasakta(ku, 'duvar', tol=2.0)
                     or K.kapi_u.intersects(ku) or eng.yasakta(ku, 'asansor'))
            if sorun:
                for t in ents:
                    msp.delete_entity(t)
                continue
            for k in kut:
                eng.ekle_alan(k)
            return True
    return False


# ====================================================================== ÇATI
def cati_ciz(doc, eng, kur, ofset, dep, P_, x_aralik=(258656.0, 260714.0)):
    """çatı planında DEPO DOLUM / DÖNÜŞ kolonları (kolon kutusu noktası, çatı çerçevesine ötelenmiş: P kolonlarıyla aynı
    öteleme) -> kullanım su deposu (mimarideki 'SU DEPOSU' kutusu). Şema: şebeke -> dolum ↑ depo, depo -> dönüş ↓ sayaç."""
    msp = doc.modelspace()
    ox, oy = ofset
    kx = VARSAYILAN['kolon_x'] if kur.get('cfg') is None else kur['cfg']['kolon_x']
    kr = VARSAYILAN['kolon_r']
    R = {ad: (kx + ox, kur['kol_y'][ad] + oy) for ad in ('DOLUM', 'DONUS')}
    for ad, p in R.items():
        P_.ekle_insert(msp, B_KOLON, p, L_SOG)
        eng.ekle_alan(Point(p).buffer(kr + 0.5))
    # depo kutusu: mimari kapalı çizgi, 'DEPO' yazısını içeren en küçük
    kutu = None
    if dep is not None:
        for e in msp.query('LWPOLYLINE'):
            if not e.dxf.layer.upper().startswith('ROTAS-MIMARI') or not e.closed:
                continue
            pts = [(q[0], q[1]) for q in e.get_points('xy')]
            if len(pts) < 4:
                continue
            pg = Polygon(pts)
            if pg.is_valid and pg.contains(Point(dep)) and 5.0e3 < pg.area < 8.0e4:
                if kutu is None or pg.area < kutu.area:
                    kutu = pg
    if kutu is None and dep is not None:          # kapalı çizgi yoksa: mimari çizgilerin poligonlaştırılması
        from shapely.ops import polygonize
        W = box(dep[0] - 200, dep[1] - 200, dep[0] + 200, dep[1] + 200)
        segs = []
        for e in msp.query('LINE LWPOLYLINE'):
            if not e.dxf.layer.upper().startswith('ROTAS-MIMARI'):
                continue
            try:
                pts = [(q[0], q[1]) for q in (e.get_points('xy') if e.dxftype() == 'LWPOLYLINE'
                                              else [e.dxf.start, e.dxf.end])]
                if e.dxftype() == 'LWPOLYLINE' and e.closed:
                    pts.append(pts[0])
            except Exception:
                continue
            if len(pts) > 1:
                g = LineString(pts)
                if g.intersects(W):
                    segs.append(g.intersection(W))
        hs = [g for g in polygonize(unary_union(segs)) if g.contains(Point(dep)) and 5.0e3 < g.area < 8.0e4]
        kutu = min(hs, key=lambda g: g.area) if hs else None
    if kutu is None:
        return None
    bx0, by0, bx1, by1 = kutu.bounds
    xd = bx1 if R['DOLUM'][0] > bx1 else bx0
    sg = 1 if xd == bx1 else -1
    xa = R['DOLUM'][0] - sg * 10.0
    xb = R['DOLUM'][0] - sg * 16.0
    hat = {'DOLUM': [(R['DOLUM'][0] - sg * kr, R['DOLUM'][1]), (xa, R['DOLUM'][1]), (xa, by1 - 25.0), (xd, by1 - 25.0)],
           'DONUS': [(R['DONUS'][0] - sg * kr, R['DONUS'][1]), (xb, R['DONUS'][1]), (xb, by0 + 25.0), (xd, by0 + 25.0)]}
    for ad, pts in hat.items():
        msp.add_lwpolyline(pts, dxfattribs={'layer': L_SOG})
        eng.ekle_cizgi(LineString(pts))
    P_.ekle_insert(msp, B_VANA, ((xa + xd) / 2.0, by1 - 25.0), L_SAY)
    P_.ekle_insert(msp, B_VANA, ((xb + xd) / 2.0, by0 + 25.0), L_SAY)
    # etiketler (kolon kutusunun yanında)
    toplam = kur['toplam']
    for ad, pts, metin in (('DOLUM', hat['DOLUM'], 'DEPO DOLUM %s (şebekeden)' % P_.inc(toplam)),
                           ('DONUS', hat['DONUS'], 'DEPO DÖNÜŞ %s (sayaçlara)' % P_.inc(toplam))):
        A = pts[1]
        for dy in ((-30, -50, -70, -95, 30, 50) if ad == 'DONUS' else (40, 60, 80, 100, 125, -60, -80, -115, -135)):
            t = msp.add_text(metin, dxfattribs={'layer': L_TCAP, 'height': 10.0, 'style': 'ROTAS-YAZI', 'width': 0.8})
            t.dxf.insert = (A[0] + 25.0, A[1] + dy)
            if eng.yasakta(unary_union(P_.yazi_kutulari(t)), 'duvar', tol=2.0):
                msp.delete_entity(t)
                continue
            ku = unary_union(P_.yazi_kutulari(t))
            if eng.carpar(ku.buffer(1.5, join_style=2)):
                msp.delete_entity(t)
                continue
            eng.ekle_alan(ku)
            q = (ku.bounds[0] - 1, ku.bounds[1] if dy > 0 else ku.bounds[3])
            msp.add_line(A, q, dxfattribs={'layer': L_KIL})
            break
    return dict(kolonlar=R, depo=kutu.bounds, hat=hat)


# ====================================================================== KONTROL
def kontrol(dxf, Ks, hat, ins, TASARIM=None):
    """K4: sayaç adedi, bağlantı (daire girişi -> kolon -> sayaç), kesişme, kapı / duvar, ortak alan, kolon hizası."""
    import json
    import os
    import networkx as nx
    BURASI = os.path.dirname(os.path.abspath(__file__))
    if TASARIM is None:
        with open(BURASI + '/tasarim_new_block.json', encoding='utf-8') as f:
            TASARIM = json.load(f)
    cfg = ayar(TASARIM)
    out = {}
    kolon_konum = {}
    for K in sorted(Ks.values(), key=lambda K: K.off):
        k = K.k
        lines = [(lay, g) for lay, g in hat[k] if 'SOGUK' in lay or 'SEBEKE' in lay]
        ortak = unary_union([r['poly'] for r in K.rooms if r['tip'] == 'ortak'])
        kolonlar = [p for ad, p, e in ins[k] if ad == B_KOLON]
        olcer = [p for ad, p, e in ins[k] if ad == B_OLCER]
        girisler = [p for ad, p, e in ins[k] if ad == 'ROTAS-S2-TEMIZ-GIRIS']
        kolon_konum[k] = sorted((round(p[0] - K.off, 1), round(p[1], 1)) for p in kolonlar)
        # besleme hatları: ortak alanda (+5 cm) olan soğuk/şebeke hatları
        bes = [(lay, g) for lay, g in lines if g.intersection(ortak.buffer(5)).length > 0.6 * g.length or 'SEBEKE' in lay]
        # kesişme: uç noktada birleşme dışı
        kes = 0
        for i in range(len(bes)):
            for j in range(i + 1, len(bes)):
                a, b = bes[i][1], bes[j][1]
                if not a.intersects(b):
                    continue
                x = a.intersection(b)
                uclar = [Point(q) for q in (a.coords[0], a.coords[-1], b.coords[0], b.coords[-1])]
                pts = [x] if x.geom_type == 'Point' else list(getattr(x, 'geoms', []))
                if x.geom_type in ('LineString', 'MultiLineString') and x.length > 0.5:
                    kes += 1
                    continue
                for q in pts:
                    if q.geom_type == 'Point' and not any(q.distance(u) < 0.6 for u in uclar):
                        kes += 1
        # yakın paralel (üst üste binme): 2 cm'den yakın paralel parça
        bin_ = 0
        for i in range(len(bes)):
            for j in range(i + 1, len(bes)):
                a, b = bes[i][1], bes[j][1]
                if a.distance(b) < 2.0:
                    yak = a.intersection(b.buffer(1.5)).difference(a.intersection(b).buffer(3.0)).length
                    if yak > 2.0:
                        bin_ += 1
        # kapı açılım alanı + kat yasakları
        kapi = K.kapi_u
        for z in cfg.get('kapi_yasak_' + k, []):
            c, r, (a0, a1) = z['merkez'], z['r'], z['aci']
            pts = [c] + [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * t / 16.0)),
                          c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * t / 16.0))) for t in range(17)]
            kapi = kapi.union(Polygon([(p[0] + K.off, p[1]) for p in pts]))
        kapi_boy = sum(g.intersection(kapi).length for lay, g in bes if 'SEBEKE' not in lay)
        seb_kapi = sum(g.intersection(kapi).length for lay, g in bes if 'SEBEKE' in lay)
        duvar_boy = sum(g.intersection(K.S.buffer(-1.0)).length for lay, g in bes if 'SEBEKE' not in lay)
        seb_duvar = sum(g.intersection(K.bina.buffer(-1)).intersection(K.S.buffer(-1.0)).length
                        for lay, g in bes if 'SEBEKE' in lay)
        beton_boy = sum(g.intersection(unary_union(K.cols).buffer(-0.5)).length for lay, g in bes)
        ortak_disi = sum(g.difference(ortak.buffer(6)).length for lay, g in bes if 'SEBEKE' not in lay)
        # bağlantı: her giriş işareti, besleme ağı üzerinden bir kolona (üst kat) ya da sayaca (zemin)
        G = nx.Graph()
        nod = unary_union([g for lay, g in lines])          # T-birleşimlerde düğüm (noding)
        for g in getattr(nod, 'geoms', [nod]):
            cs = [(round(c[0], 1), round(c[1], 1)) for c in g.coords]
            for a, b in zip(cs[:-1], cs[1:]):
                G.add_edge(a, b)
        dugum = list(G.nodes)
        for i, a in enumerate(dugum):                       # 0,5 cm içindeki uçlar aynı düğüm
            for b in dugum[i + 1:]:
                if dist(a, b) < 0.5:
                    G.add_edge(a, b)

        def en_yakin(p, tol):
            best = min(dugum, key=lambda q: dist(q, p), default=None)
            return best if best is not None and dist(best, p) <= tol else None
        bagli = 0
        for p in girisler:
            n = en_yakin(p, 1.0)
            if n is None:
                continue
            comp = nx.node_connected_component(G, n)
            hedef = [q for q in kolonlar if any(dist(q, c) <= 3.0 for c in comp)]
            agc = unary_union([LineString([a, b]) for a, b in G.subgraph(comp).edges])
            hedef += [q for q in olcer if agc.distance(Point(q)) <= 1.0]
            if hedef:
                bagli += 1
        out[k] = dict(kolon_adet=len(kolonlar), sayac_adet=len(olcer), daire_girisi=len(girisler),
                      girisi_besleme_bagli=bagli, kesisme=kes, ust_uste=bin_, kapi_alani_cm=round(kapi_boy, 1),
                      sebeke_kapi_alani_cm=round(seb_kapi, 1), duvar_cm=round(duvar_boy, 1),
                      sebeke_duvar_gecisi_cm=round(seb_duvar, 1),
                      beton_cm=round(beton_boy, 1), ortak_disi_cm=round(ortak_disi, 1))
    # kolon hizası: her katın kolonları zemin kolonlarının alt kümesi (aynı nokta)
    z = set(kolon_konum.get('Z', []))
    for k, L in kolon_konum.items():
        out[k]['kolon_hiza_disi'] = sum(1 for q in L if not any(dist(q, p) < 0.5 for p in z))
    return out
