# -*- coding: utf-8 -*-
"""Adapeker — YERDEN ISITMA kat planları + kolon şeması + kombi kesiti (+ ısı kaybı modeli).

Standart (15.10.2026 onaylı): serpantin yerden2 (serpantin.py / tasarim.py, 15 cm meander), kullanıcının blokları
(ROTAS-YI-ETIKET / MAHAL / şema blokları, kutuphane/yerden), holde yerden ısıtma yok, ayaklar holden kollektöre,
35 kcal/h·m, devre ≤ 80 m, Sakarya 3. bölge (TS 825:2024 / İZODER U), hazırlayan teknik ressam.
Çalıştırma: python3 motor/adapeker/yerden_ad.py
"""
import os, sys, math, json
BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
from ortak_ad import yeni_doc, T, PL, mimari_altlik, kat_basligi, antet, KOK, CIKIS, PROJE, M
sys.path.insert(0, os.path.join(KOK, 'motor', 'yerden2'))
import tasarim as TS  # noqa
import serpantin as S  # noqa
import yi_bloklar as YB  # noqa
import isi_kaybi as IK  # noqa
from shapely.geometry import box, Polygon, Point, LineString
from shapely.ops import unary_union, substring

KCAL_M = 35.0                     # kcal/h · m (kullanıcı 15.10.2026)
L_PEX, L_ET, L_MAH, L_MASK = 'ROTAS-ISITMA-PEX', 'ROTAS-ISITMA-ETIKET', 'ROTAS-ISITMA-MAHAL-ETIKET', 'ROTAS-ISITMA-MASKE'
L_KOL, L_KG, L_KD, L_YAZI = 'ROTAS-ISITMA-KOLLEKTOR', 'ROTAS-ISITMA-GIDIS-BORU', 'ROTAS-ISITMA-DONUS-BORU', 'ROTAS-ISITMA-YAZI'
KAT = {L_PEX: (1, 'Continuous'), L_ET: (2, 'Continuous'), L_MAH: (2, 'Continuous'), L_MASK: (7, 'Continuous'),
       L_KOL: (4, 'Continuous'), L_KG: (10, 'Continuous'), L_KD: (30, 'Continuous'), L_YAZI: (7, 'Continuous'),
       'ROTAS-ISITMA-CAP': (41, 'Continuous'), 'ROTAS-ISITMA-SEMA-DETAY': (7, 'Continuous'), 'ROTAS-SEMA-KAT-BANDI': (7, 'Continuous'),
       'ROTAS-SEMA-KAT-YAZI': (1, 'Continuous'), 'ROTAS-ISITMA-DAIRE-NO': (6, 'Continuous'), 'ROTAS-PAFTA': (144, 'Continuous'),
       'ROTAS-PAFTA-YAZI': (7, 'Continuous'), 'ROTAS-PAFTA-BASLIK': (7, 'Continuous'), 'ROTAS-LEJANT': (7, 'Continuous'),
       'ROTAS-NOT': (7, 'Continuous'), 'ROTAS-DETAY': (7, 'Continuous'), 'ROTAS-DETAY-YAZI': (7, 'Continuous')}

# tip daire (D1 zemin) — ısıtılmayan alanlar (tefriş, vitrifiye) ve ayak çıkış yönleri
YASAK = {('MUTFAK', 9.50): [box(-419, -2590, -259, -2528), box(-322, -2868, -259, -2528)],
         ('BANYO-WC', 4.33): [box(-304, -2352, -262, -2243), box(-316, -2223, -262, -2188), box(-410, -2095, -335, -2056)],
         ('BANYO-WC', 2.60): [box(-264, -2033, -229, -1933), box(-190, -2132, -138, -2088)]}
# ayak çıkışı: (hol tarafındaki kapı noktası, yön L/R/U/D, ayağın odaya girdiği nokta (kapı/duvar), tercih köşe)
CIKIS_YON = {('YATAK ODASI', 10.28): ('L', (-549, -1983)), ('YATAK ODASI', 10.07): ('L', (-549, -2093)),
             ('ODA', 12.91): ('U', (-479, -1923)), ('BANYO-WC', 2.60): ('R', (-262, -2030)),
             ('BANYO-WC', 4.33): ('R', (-409, -2298)), ('SALON', 23.08): ('L', (-549, -2463)),
             ('MUTFAK', 9.50): ('D', (-479, -2528))}
SIRA_UST = [('YATAK ODASI', 10.07), ('YATAK ODASI', 10.28), ('ODA', 12.91), ('BANYO-WC', 2.60), ('BANYO-WC', 4.33)]
SIRA_ALT = [('MUTFAK', 9.50), ('SALON', 23.08)]          # en derin yatay şerit ilk
KOL_Y = -2367.0           # kollektör dolabının alt yüzü (banyo 4,33 alt duvarının hol tarafı)
PORT_X0 = -318.0          # en sağdaki ağız
ADIM_P = 13.0
Y_DERIN = -2516.0         # en derin yatay şerit (hol alt ucu -2528)
LANE_X0 = -537.0          # hol şeridi (x -548..-412) ilk düşey şerit
KOMBI_X = (-300.0, -294.0)   # kombi gidiş / dönüş düşeyi (mutfakta tezgâh altından)


def tip_tasarim():
    """tip dairede (D1 zemin) her ısıtılan mahalin serpantini; diğer daire/katlar aynalama + öteleme ile"""
    odalar = []
    for t in M._tip_mahaller():
        if not t['isit']:
            continue
        key = (t['ad'], t['alan'])
        P = t['poly']
        H = P.difference(unary_union(YASAK[key])) if key in YASAK else P
        if H.geom_type != 'Polygon':
            H = max(H.geoms, key=lambda g: g.area)
        R = H.buffer(-S.KENAR)
        yon, kapi = CIKIS_YON[key]
        r = TS.oda_tasarla(dict(area=t['alan'], poly=P), H, R, kapi, Polygon(), cep_ac=False,
                           islak=(t['tip'] == 'banyo'), kapi_zorla=True)
        if r is None:
            print('UYARI tasarım yok', key)
            continue
        odalar.append(dict(t, key=key, H=H, tas=r, yon=yon, kapi=kapi))
    return odalar


def _halka_yolu(poly, a, b, o):
    """poly içinde, duvardan o cm içeride, a -> b en kısa çevre yolu (noktalar)"""
    ring = poly.buffer(-o, join_style=2).exterior
    sa, sb = ring.project(Point(a)), ring.project(Point(b))
    L = ring.length
    if sa <= sb:
        d1, d2 = sb - sa, L - (sb - sa)
    else:
        d1, d2 = L - (sa - sb), sa - sb
    if d1 <= d2:
        if sa <= sb:
            g = substring(ring, sa, sb)
        else:
            g = LineString(list(substring(ring, sa, L).coords) + list(substring(ring, 0, sb).coords)[1:])
    else:
        if sb <= sa:
            g = substring(ring, sb, sa)
        else:
            g = LineString(list(substring(ring, sb, L).coords) + list(substring(ring, 0, sa).coords)[1:])
        g = LineString(list(g.coords)[::-1])
    return [tuple(p) for p in g.coords]


def _ayak_geom(o, c, k, n_ust_idx, rev, swap):
    xp = PORT_X0 - ADIM_P * k
    yg = Y_DERIN + ADIM_P * k
    yon, kapi = o['yon'], o['kapi']
    ust = o['key'] in SIRA_UST
    lx = LANE_X0 + ADIM_P * n_ust_idx if ust else None
    g, d = [(xp, KOL_Y), (xp, yg)], [(xp - 6, KOL_Y), (xp - 6, yg + 6)]
    if yon == 'L':
        if ust:
            ye = kapi[1] - 10
            g += [(lx, yg), (lx, ye), (kapi[0], ye)]; d += [(lx + 6, yg + 6), (lx + 6, ye + 6), (kapi[0], ye + 6)]
        else:
            g.append((kapi[0], yg)); d.append((kapi[0], yg + 6))
    elif yon == 'U':
        g += [(lx, yg), (lx, kapi[1])]; d += [(lx + 6, yg + 6), (lx + 6, kapi[1])]
    elif yon == 'R':
        ye = kapi[1] + 3
        g += [(lx, yg), (lx, ye), (kapi[0], ye)]; d += [(lx + 6, yg + 6), (lx + 6, ye - 6), (kapi[0], ye - 6)]
    elif yon == 'D':
        lx2 = -470.0 - ADIM_P * (k % 2)
        g += [(lx2, yg), (lx2, kapi[1])]; d += [(lx2 - 6, yg + 6), (lx2 - 6, kapi[1])]
    P = o['poly']
    pts = list(c['pts'])
    if rev:
        pts = [(x, y, -b) for x, y, b in pts[::-1]]
        # bulge yön değiştirir: ters sırada her segmentin bulge'u bir önceki noktaya taşınır
        pts = [(pts[i][0], pts[i][1], -c['pts'][::-1][i + 1][2] if i + 1 < len(pts) else 0.0) for i in range(len(pts))]
    a_g, a_d = (pts[0][0], pts[0][1]), (pts[-1][0], pts[-1][1])
    og, od = (2.5, 5.0) if not swap else (5.0, 2.5)
    ig = _halka_yolu(P, g[-1], a_g, og)
    idd = _halka_yolu(P, d[-1], a_d, od)
    g += ig if Point(ig[0]).distance(Point(g[-1])) > 0.5 else ig[1:]
    d += idd if Point(idd[0]).distance(Point(d[-1])) > 0.5 else idd[1:]
    tam = [(x, y, 0.0) for x, y in g] + [(x, y, b) for x, y, b in pts] + [(x, y, 0.0) for x, y in d[::-1]]
    t2 = [tam[0]]
    for p in tam[1:]:
        if math.hypot(p[0] - t2[-1][0], p[1] - t2[-1][1]) > 0.5:
            t2.append(p)
        else:
            t2[-1] = (t2[-1][0], t2[-1][1], p[2])
    return t2


def _ls(pts):
    return S.cizgi([(x, y, b) for x, y, b in pts])


def _ceza(ls, digerleri):
    from shapely.geometry import MultiLineString
    n = 0 if ls.is_simple else 5
    for o in digerleri:
        if ls.intersects(o):
            n += 1
    return n


def tip_ayaklar(odalar):
    """her devre için tam polyline (ağız → gidiş ayağı → serpantin → dönüş ayağı → ağız), tip daire koordinatında.
    Kollektör (banyo 4,33 alt duvarı, hol) ağızlarından aşağı; yatay şeritler; hol şeridinde düşey şeritler; kapılar.
    Devre sırası / yönü / ayak ofseti kesişmesiz olacak biçimde aranır."""
    import itertools
    out = []
    k = 0
    n_ust = 0
    yerlesik = []
    for key in SIRA_ALT + SIRA_UST:
        o = next(o for o in odalar if o['key'] == key)
        devs = o['tas']['devreler']
        en = None
        for perm in itertools.permutations(range(len(devs))):
            for secim in itertools.product((False, True), repeat=2 * len(devs)):
                geo = []
                for i, ci in enumerate(perm):
                    geo.append(_ayak_geom(o, devs[ci], k + i, n_ust + i, secim[2 * i], secim[2 * i + 1]))
                lss = [_ls(g) for g in geo]
                ceza = sum(_ceza(l, yerlesik + lss[:j]) for j, l in enumerate(lss))
                if en is None or ceza < en[0]:
                    en = (ceza, perm, geo, lss)
                if ceza == 0:
                    break
            if en[0] == 0:
                break
        if en[0]:
            print('UYARI ayak kesişmesi', key, en[0])
        for i, ci in enumerate(en[1]):
            t2 = en[2][i]
            L = S.uzunluk(t2) / 100.0
            out.append(dict(oda=o, c=devs[ci], pts=t2, L_ser=devs[ci]['L'] / 100.0, L=L, port=(PORT_X0 - ADIM_P * (k + i), KOL_Y), k=k + i))
        yerlesik += en[3]
        k += len(devs)
        if key in SIRA_UST:
            n_ust += len(devs)
    return out


def _tr_pts(pts, daire, k):
    out = []
    for x, y, b in pts:
        X, Y = M.donustur((x, y), daire, k)
        out.append((X, Y, -b if daire == 'D2' else b))
    return out


def isi_kaybi_hesapla(katlar_odalar):
    """isi_kaybi.hesapla (kullanıcının ZEMİN / 1 NK sayfa yöntemi), Sakarya 3. bölge U (TS 825:2024 / İZODER)"""
    IK.KAT_H = PROJE['kat_h']
    IK.U = IK.u_sec(3)

    class K:
        pass
    sonuc = {}
    ortak = [m for m in M.mahaller('1') if m['daire'] is None and m['alan_olc'] < 30]
    for k, odalar in katlar_odalar.items():
        Kk = K()
        Kk.bina = M.donustur_geom(M.bina_poly('Z'), 'D1', k)
        rooms = []
        for d in ('D1', 'D2'):
            for t in M._tip_mahaller():
                rooms.append(dict(poly=M.donustur_geom(t['poly'], d, k), tip=t['tip'], daire=d))
        from shapely.affinity import translate
        for m in ortak:
            rooms.append(dict(poly=translate(m['poly'], M.OFS[k] - M.OFS['1'], 0), tip='ortak', daire=None))
        Kk.rooms = rooms
        Kk.yazilar = []
        IK.pencereler = _pencereler_ad(k)
        IK.hesapla(Kk, odalar, ust_kat=(k == '2'), zemin_kat=(k == 'Z'))
    return sonuc


def _pencereler_ad(k):
    """mimari pencere yazıları ('P' işaretli 'g\\nh' MTEXT): balkona açılan yüksek (≥ 240) olan balkon kapısı"""
    import re
    w = M.win(k, 80)
    P = []
    for r in M.kayit():
        if r[0] == 'T' and M.icinde(r[2], w):
            m = re.fullmatch(r'(\d{2,3})\s*\n\s*(\d{3})', r[3].strip())
            if m and r[4] < 9:
                g, h = int(m.group(1)) / 100.0, int(m.group(2)) / 100.0
                P.append(((r[2][0] + 8, r[2][1] - 8), g, h, 'KAPI' if h >= 2.4 else 'ÇP'))

    def f(K):
        return P
    return f


def main():
    doc = yeni_doc(KAT)
    YB.hazirla(doc)
    m = doc.modelspace()
    mimari_altlik(m)
    odalar = tip_tasarim()
    tip = tip_ayaklar(odalar)
    # ------------------------------------------------ mahaller, ısı kaybı (kat × daire)
    model = dict(proje=dict(ad=PROJE['ad']), katlar=[])
    katlar_odalar = {}
    zon_say = {'Z': 0, '1': 0, '2': 0}
    TUM = []
    for k in ('Z', '1', '2'):
        kat = dict(kat=k, ad=M.KAT_ADI[k], daireler={})
        lst = []
        for d in ('D1', 'D2'):
            dno = M.daire_no(d, k)
            mah = []
            for o in odalar:
                zon_say[k] += 1
                zon = ('Z%02d' if k == 'Z' else k + '%02d') % zon_say[k]
                mm = dict(ad=o['ad'], zon=zon, sic=o['sic'], alan=o['alan'], tur=o['tip'], tip=o['tip'],
                          poly=M.donustur_geom(o['poly'], d, k), key=o['key'], daire=dno, d=d, kat=k, devreler=[])
                mah.append(mm)
                lst.append(mm)
            kat['daireler'][dno[1:]] = dict(no=dno, mahaller=mah)
        model['katlar'].append(kat)
        katlar_odalar[k] = lst
    isi_kaybi_hesapla(katlar_odalar)
    # ------------------------------------------------ çizim
    no_devre = 0
    ozet = []
    for kat in model['katlar']:
        k = kat['kat']
        for dno, dd in kat['daireler'].items():
            d = 'D1' if int(dno) % 2 == 1 else 'D2'
            devs_daire = []
            for mm in dd['mahaller']:
                ilgili = [t for t in tip if t['oda']['key'] == mm['key']]
                Ltop = sum(t['L'] for t in ilgili)
                Q = mm['isi_kaybi']['Q'] / 1.163 if mm.get('isi_kaybi') else 0.0     # kcal/h
                for t in ilgili:
                    no_devre += 1
                    pts = _tr_pts(t['pts'], d, k)
                    m.add_lwpolyline(pts, format='xyb', dxfattribs={'layer': L_PEX})
                    kc = KCAL_M * t['L']
                    dv = dict(no=no_devre, L_m=round(t['L'], 2), W=round(kc, 1), kcal=round(kc, 1), q_mahal=round(Q * t['L'] / Ltop, 1))
                    mm['devreler'].append(dv)
                    devs_daire.append(dv)
                    # devre etiketi: serpantin üstünde, altı maskeli
                    c = t['c']
                    ser = Polygon([(x, y) for x, y, b in _tr_pts(c['pts'], d, k)]).buffer(0) if len(c['pts']) > 3 else None
                    lp = mm['poly'].buffer(-25)
                    lc = lp.representative_point() if not lp.is_empty else mm['poly'].representative_point()
                    ilk = [x for x in ilgili].index(t)
                    sc = 1.0 if mm['poly'].area > 60000 else 0.6
                    x0, y1 = lc.x - 75 * sc + (0 if len(ilgili) == 1 else (ilk - 0.5) * 160 * sc), lc.y - 30 * sc
                    m.add_wipeout([(x0 - 2, y1 - 80 * sc - 2), (x0 + 150 * sc + 2, y1 + 2)], dxfattribs={'layer': L_MASK})
                    e = m.add_blockref('ROTAS-YI-ETIKET', (x0, y1), dxfattribs={'layer': L_ET, 'xscale': sc, 'yscale': sc})
                    e.add_auto_attribs({'UZ': '%.2f m' % t['L'], 'AR': '15.0', 'YER': '%.0f' % kc, 'NO1': str(no_devre),
                                        'MAHAL': mm['ad'], 'NO': mm['zon'], 'DERECE': '%d%%%%DC' % mm['sic'],
                                        'ALAN': '%.2f' % mm['alan'], 'BORU': 'PEX BORU, 16 x 2.0'})
                # mahal etiketi
                q = mm['poly'].buffer(-30).representative_point() if not mm['poly'].buffer(-30).is_empty else mm['poly'].centroid
                mx, my = q.x, q.y + (60 if mm['poly'].area > 60000 else 45)
                sc = 1.0 if mm['poly'].area > 60000 else 0.7
                m.add_wipeout([(mx - 45 * sc, my - 22 * sc), (mx + 45 * sc, my + 22 * sc)], dxfattribs={'layer': L_MASK})
                e = m.add_blockref('ROTAS-YI-MAHAL', (mx, my), dxfattribs={'layer': L_MAH, 'xscale': sc, 'yscale': sc})
                e.add_auto_attribs({'DERECE': '%d%%%%DC' % mm['sic'], 'NO': mm['zon'], 'MAHAL': mm['ad'], 'ALAN': '%.2f' % mm['alan']})
                kap = KCAL_M * Ltop
                ozet.append(dict(kat=k, daire=dd['no'], zon=mm['zon'], ad=mm['ad'], sic=mm['sic'], alan=mm['alan'],
                                 Q_W=round(mm['isi_kaybi']['Q'], 1), Q_kcal=round(Q, 1), L=round(Ltop, 2),
                                 n=len(ilgili), kap_kcal=round(kap, 1), yeter=kap >= Q))
            # kollektör dolabı + kombi hattı
            n = len(devs_daire)
            xs = [PORT_X0 - ADIM_P * i for i in range(n)]
            kx0, kx1 = min(xs) - 14, PORT_X0 + 10
            a = M.donustur((kx0, KOL_Y), d, k); b = M.donustur((kx1, KOL_Y + 15), d, k)
            PL(m, [(a[0], a[1]), (b[0], a[1]), (b[0], b[1]), (a[0], b[1])], L_KOL, True, 1.5)
            for yy in (KOL_Y + 5, KOL_Y + 10):
                p1, p2 = M.donustur((kx0 + 3, yy), d, k), M.donustur((kx1 - 3, yy), d, k)
                m.add_line(p1, p2, dxfattribs={'layer': L_KOL})
            t0 = M.donustur(((kx0 + kx1) / 2, KOL_Y + 30), d, k)
            T(m, t0[0], t0[1], 'KOLLEKTÖR DOLABI (%d AĞIZLI)' % n, 9, 'BC', L_YAZI)
            tq = sum(v['kcal'] for v in devs_daire)
            T(m, t0[0], t0[1] + 13, '%.0f kcal/h - Ø26 (1")' % tq, 8, 'BC', 'ROTAS-ISITMA-CAP')
            # kombi -> kollektör (gidiş / dönüş), mutfak tezgâh altından
            for xx, lay, dy in ((KOMBI_X[0], L_KG, 0), (KOMBI_X[1], L_KD, 0)):
                yol = [M.donustur(p, d, k) for p in ((xx, M.KOMBI_KUTU[3]), (xx, KOL_Y))]
                m.add_lwpolyline(yol, dxfattribs={'layer': lay, 'const_width': 1.5})
            kp = M.donustur(M.KOMBI, d, k)
            T(m, kp[0], kp[1] - 32, 'H. KOMBİ 24 kW', 9, 'TC', L_YAZI)
            dd['kombi_kw'] = 24
        kat_basligi(m, k, 'YERDEN ISITMA TESİSAT PLANI')
    # ------------------------------------------------ kolon şeması (kullanıcının şema blokları)
    import yi_sema as YS
    YS.X0 = M.W0[0]
    YS.PY0, YS.PY1 = -5650.0, -3900.0
    YS.BANT0 = -5300.0 + 0
    YS.BANT_H = 400.0
    YS.BANT0 = -5200.0
    os.environ['YI_HOL_YOK'] = '1'
    os.environ['YI_ISI_KAYBI'] = ''
    # şema ağız / panel değerleri kcal/h: şema bloğu 'W' yazar -> kcal/h olarak gönder
    for kat in model['katlar']:
        for dd in kat['daireler'].values():
            for mm in dd['mahaller']:
                for dv in mm['devreler']:
                    dv['W'] = dv['kcal']
    YS.PY0 = YS.BANT0 - 450
    YS.PY1 = YS.BANT0 + 3 * YS.BANT_H + 120
    YS.ciz(doc, m, model)
    for e in m.query('TEXT'):
        if e.dxf.layer in ('ROTAS-NOT', 'ROTAS-PAFTA-BASLIK', 'ROTAS-LEJANT'):
            s = e.dxf.text
            s = s.replace('35 W/m × hat uzunluğu', '35 kcal/h·m × hat uzunluğu').replace('ısıl güç', 'ısıl güç (kcal/h)')
            e.dxf.text = s
    for e in m.query('INSERT'):
        for a in e.attribs:
            if a.dxf.tag in ('CAP', 'YER') and a.dxf.text.endswith('W') or ('W-' in a.dxf.text and a.dxf.tag == 'CAP'):
                a.dxf.text = a.dxf.text.replace('W-', 'kcal/h-').replace(' W', ' kcal/h')
    kombi_kesiti(m, M.W0[0] + 6900, -3650)
    ozet_tablosu(m, ozet, M.W0[0] + 8100, -3700)
    antet(m, M.W0[0] + 8100, -5250, 'YERDEN ISITMA TESİSATI')
    os.makedirs(CIKIS, exist_ok=True)
    yol = os.path.join(CIKIS, 'ADAPEKER_YERDEN_ISITMA.dxf')
    doc.saveas(yol)
    json.dump(dict(ozet=ozet, devre_sayisi=no_devre,
                   model=[dict(kat=kt['kat'], daireler={n: dict(no=v['no'], mahaller=[{x: mm[x] for x in ('ad', 'zon', 'sic', 'alan', 'devreler', 'isi_kaybi', 'tur')} for mm in v['mahaller']]) for n, v in kt['daireler'].items()}) for kt in model['katlar']]),
              open(os.path.join(CIKIS, 'yerden_model.json'), 'w'), ensure_ascii=False, indent=1, default=str)
    print('kaydedildi', yol, 'devre', no_devre)
    for r in ozet[:16]:
        print(r)
    return yol


def kombi_kesiti(m, x, y):
    """KOMBİ BAĞLANTI KESİTİ (duvar tipi yoğuşmalı kombi — balkon dış duvarı): ölçeksiz tip detay, sol üst (x, y)"""
    L, LY = 'ROTAS-DETAY', 'ROTAS-DETAY-YAZI'
    T(m, x, y, 'KOMBİ BAĞLANTI KESİTİ', 28, 'BL', 'ROTAS-PAFTA-YAZI')
    T(m, x, y - 35, 'ÖLÇEKSİZ (balkon, mutfak dış duvarı)', 16, 'BL', 'ROTAS-PAFTA-YAZI')
    yz = y - 900
    PL(m, [(x, yz), (x + 900, yz)], L, w=3)
    PL(m, [(x + 80, yz), (x + 80, yz + 820), (x + 105, yz + 820), (x + 105, yz)], L, True)
    T(m, x + 92, yz + 830, 'DUVAR', 10, 'BC', LY)
    kx0, ky0 = x + 105, yz + 420
    PL(m, [(kx0, ky0), (kx0 + 45, ky0), (kx0 + 45, ky0 + 75), (kx0, ky0 + 75)], L, True, 1.5)
    T(m, kx0 + 22, ky0 + 37, 'KOMBİ', 9, 'MC', LY, rot=90)
    PL(m, [(kx0 + 15, ky0 + 75), (kx0 + 15, ky0 + 130), (x + 60, ky0 + 130), (x + 60, ky0 + 160)], L)
    T(m, x + 20, ky0 + 170, 'BACA (hermetik, Ø60/100 dış ortama)', 9, 'BL', LY)
    etik = [('ISITMA GİDİŞ → KOLLEKTÖR Ø20 (3/4")', 'ROTAS-ISITMA-GIDIS-BORU'), ('ISITMA DÖNÜŞ ← KOLLEKTÖR Ø20', 'ROTAS-ISITMA-DONUS-BORU'),
            ('SICAK KULLANMA SUYU (1/2")', 'ROTAS-DETAY'), ('SOĞUK SU GİRİŞİ (1/2")', 'ROTAS-DETAY'), ('DOĞALGAZ (vanalı)', 'ROTAS-DETAY')]
    for i, (s, lay) in enumerate(etik):
        xx = kx0 + 6 + i * 8
        PL(m, [(xx, ky0), (xx, ky0 - 120 - i * 40), (x + 420, ky0 - 120 - i * 40)], lay, w=1.0)
        m.add_circle((xx, ky0 - 60), 3.5, dxfattribs={'layer': L})
        T(m, x + 430, ky0 - 120 - i * 40, s, 10, 'ML', LY)
    T(m, kx0 + 70, ky0 - 60, 'küresel vanalar', 8, 'ML', LY)
    PL(m, [(kx0 + 50, ky0 + 10), (kx0 + 90, ky0 + 10)], L)
    T(m, kx0 + 95, ky0 + 10, 'EMNİYET VENTİLİ TAHLİYESİ → YER SÜZGECİNE / GİDERE', 8, 'ML', LY)
    T(m, x, yz - 30, 'Kombi duvar tipi, yoğuşmalı 24 kW; yoğuşma suyu nötralizatörle en yakın pis su giderine bağlanacaktır.', 10, 'TL', LY)
    T(m, x, yz - 50, 'Kombi gidiş-dönüş hatları kollektör dolabına PPR/PEX Ø20 ile, yalıtımlı olarak götürülecektir.', 10, 'TL', LY)


def ozet_tablosu(m, ozet, x, y):
    L = 'ROTAS-NOT'
    T(m, x, y + 20, 'ISI KAYBI - YERDEN ISITMA KARŞILAŞTIRMASI (Sakarya 3. bölge, TS 825:2024 / İZODER U, Tdış -3 °C)', 18, 'BL', L)
    bas = ['KAT', 'DAİRE', 'ZON', 'MAHAL', 'T °C', 'ISI KAYBI kcal/h', 'BORU m', 'DEVRE', 'KAPASİTE kcal/h (35×L)', 'DURUM']
    gen = [60, 70, 70, 190, 50, 140, 90, 70, 190, 90]
    X = [x]
    for g in gen:
        X.append(X[-1] + g)
    yy = y
    m.add_line((x, yy), (X[-1], yy), dxfattribs={'layer': L})
    for i, s in enumerate(bas):
        T(m, (X[i] + X[i + 1]) / 2, yy - 13, s, 8, 'MC', L)
    yy -= 26
    for r in ozet:
        m.add_line((x, yy), (X[-1], yy), dxfattribs={'layer': L})
        v = [r['kat'], r['daire'], r['zon'], r['ad'], str(r['sic']), '%.0f' % r['Q_kcal'], '%.2f' % r['L'], str(r['n']),
             '%.0f' % r['kap_kcal'], 'YETERLİ' if r['yeter'] else 'İLAVE*']
        for i, s in enumerate(v):
            T(m, (X[i] + X[i + 1]) / 2, yy - 11, s, 8, 'MC', L)
        yy -= 22
    m.add_line((x, yy), (X[-1], yy), dxfattribs={'layer': L})
    for xx in X:
        m.add_line((xx, y), (xx, yy), dxfattribs={'layer': L})
    T(m, x, yy - 18, '* kapasitenin yetmediği mahalde kombi devre debisi artırılır / ek ısıtıcı (havlupan) konur.', 9, 'TL', L)
    return yy


if __name__ == '__main__':
    main()
