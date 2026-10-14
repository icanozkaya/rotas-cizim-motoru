# -*- coding: utf-8 -*-
"""Temsili daire tipik planı (DENEME – mimari yok) ve çift borulu radyatör boru ağı (yol = merkez çizgisi ağacı).
Koordinatlar cm. A dairesi x∈[0,1200], merdiven holü x∈[1200,1600] (y≥420), B dairesi A'nın aynası x∈[1600,2800]."""
import math
from shapely.geometry import LineString, Point

OFF = 30.0          # boru çifti merkez çizgisinin duvara uzaklığı
H = 5.0             # gidiş/dönüş yarı aralığı (çizgiler OFF±H)
GEN, DER = 1200.0, 1000.0
YA0, YA1 = 420.0, 580.0          # antre (hol) şeridi
CEK = 5.0           # radyatör duvar boşluğu
GENIS_TOP = 2800.0


def ayna(x):
    return GENIS_TOP - x


def _rad_boy(m):
    return m['boy'] * 100.0


def daire_plani(mahaller, sistem):
    """mahaller: veri.model daire mahal listesi. Dönüş: dict(odalar, radyatorler, yollar, kok, kombi, kapilar, pencereler)"""
    by = {}
    odalar_list = [m for m in mahaller if m['ad'] == 'ODA']
    sal = [m for m in mahaller if m['ad'] == 'SALON'][0]
    mut = [m for m in mahaller if m['ad'] == 'MUTFAK'][0]
    ant = [m for m in mahaller if m['ad'] == 'ANTRE'][0]
    ban = [m for m in mahaller if m['ad'] == 'BANYO'][0]
    oda_s = odalar_list[-1]                 # en son numaralı oda güney sırada
    oda_n = odalar_list[:-1]
    odalar = []
    # kuzey sıra
    if len(oda_n) >= 2:
        w = 380.0
        x = 0.0
        for m in oda_n:
            odalar.append(dict(m=m, r=(x, YA1, x + w, DER), sira='N')); x += w
        odalar.append(dict(m=sal, r=(x, YA1, GEN, DER), sira='N'))
    else:
        x = 0.0
        for m in oda_n:
            odalar.append(dict(m=m, r=(0.0, YA1, 500.0, DER), sira='N')); x = 500.0
        odalar.append(dict(m=sal, r=(x, YA1, GEN, DER), sira='N'))
    odalar.append(dict(m=oda_s, r=(0.0, 0.0, 500.0, YA0), sira='S'))
    odalar.append(dict(m=ban, r=(500.0, 0.0, 760.0, YA0), sira='S'))
    odalar.append(dict(m=mut, r=(760.0, 0.0, GEN, YA0), sira='S'))
    odalar.append(dict(m=ant, r=(0.0, YA0, GEN, YA1), sira='A'))

    kapilar, pencereler, radyatorler, yollar = [], [], [], []

    def rad_yerlestir(oda, duvar_y, ic_yon, merkezler, yaklasma):
        """oda radyatörleri: duvar_y duvarında, ic_yon (+1 yukarı/-1 aşağı oda içi), yaklasma (+1 doğuya/-1 batıya akış)"""
        m = oda['m']
        L = _rad_boy(m) if m['tip'] != 'Banyopan' else _rad_boy(m)
        out = []
        for k, cx in enumerate(merkezler):
            yak = cx - yaklasma * L / 2          # yaklaşma tarafı uç (yakın uç)
            uzak = cx + yaklasma * L / 2
            r = dict(oda=oda, m=m, sira_no=k + 1, cx=cx, L=L, duvar_y=duvar_y, ic=ic_yon, yakin=yak, uzak=uzak,
                     tip=m['tip'], ver=m['ver'], model=m['model'], boy=m['boy'])
            radyatorler.append(r); out.append(r)
            pw = max(100.0, L + 40.0) if m['tip'] != 'Banyopan' else 60.0
            if oda['sira'] != 'A':
                pencereler.append((cx - pw / 2, cx + pw / 2, duvar_y))
        return out

    # kapılar (kuzey odalar sağda, güney odalar solda)
    for o in odalar:
        x0, y0, x1, y1 = o['r']
        if o['sira'] == 'N':
            o['kapi'] = (x1 - 110.0, x1 - 20.0, YA1); o['xb'] = x1 - 65.0
        elif o['sira'] == 'S':
            o['kapi'] = (x0 + 20.0, x0 + 110.0, YA0); o['xb'] = x0 + 65.0
        else:
            o['kapi'] = None
        if o['kapi']:
            kapilar.append(o['kapi'])

    def oda_yolu(o):
        """odaya kapıdan girip duvar boyunca radyatörlere giden yol (antre ana hattındaki J noktasından)"""
        x0, y0, x1, y1 = o['r']; xb = o['xb']; ym = YA0 + OFF
        m = o['m']; adet = m['adet']
        if o['sira'] == 'N':
            merk = [x0 + (x1 - x0) * (k + 1) / (adet + 1) for k in range(adet)][::-1]
            rs = rad_yerlestir(o, DER, -1, merk, -1)
            son = min(r['uzak'] for r in rs)
            pts = [(xb, ym), (xb, YA1 + OFF), (x1 - OFF, YA1 + OFF), (x1 - OFF, DER - OFF), (son, DER - OFF)]
        else:
            merk = [x0 + (x1 - x0) * (k + 1) / (adet + 1) for k in range(adet)]
            rs = rad_yerlestir(o, 0.0, +1, merk, +1)
            son = max(r['uzak'] for r in rs)
            pts = [(xb, ym), (xb, YA0 - OFF), (x0 + OFF, YA0 - OFF), (x0 + OFF, OFF), (son, OFF)]
        return pts, rs

    ym = YA0 + OFF
    kn = [o for o in odalar if o['sira'] == 'N']
    ks = [o for o in odalar if o['sira'] == 'S']
    o13 = [o for o in ks if o['m'] is oda_s][0]
    omut = [o for o in ks if o['m'] is mut][0]
    oant = [o for o in odalar if o['sira'] == 'A'][0]

    # antre radyatörü: antre kuzey duvarında kapılar arası en geniş boşluk
    bos, x = [], 0.0
    for a, b, _ in sorted(o['kapi'] for o in kn):
        bos.append((x, a)); x = b
    bos.append((x, GEN - 60.0))
    ga, gb = max(bos, key=lambda t: t[1] - t[0])
    Lant = _rad_boy(ant)
    cxa = (ga + gb) / 2
    xj_ant = cxa - Lant / 2 - 40.0
    rs_ant = rad_yerlestir(oant, YA1, -1, [cxa], +1)
    ant_pts = [(xj_ant, ym), (xj_ant, YA1 - OFF), (rs_ant[0]['uzak'], YA1 - OFF)]

    # ana yol: kökten en uzak odaya (güney-batı oda)
    p13, rs13 = oda_yolu(o13)
    kombi = None
    if sistem == 'merkezi':
        kok = (GEN + 70.0, ym)
        ana = [kok] + p13
        yollar.append(dict(ad='ANA', pts=ana, rads=rs13))
        diger = [o for o in odalar if o['sira'] in 'NS' and o is not o13]
        for o in diger:
            pts, rs = oda_yolu(o)
            yollar.append(dict(ad=o['m']['ad'] + ' ' + o['m']['no'], pts=pts, rads=rs))
        yollar.append(dict(ad='ANTRE ' + ant['no'], pts=ant_pts, rads=rs_ant))
    else:
        # kombi mutfakta, dış cepheye bitişik doğu duvarında (bina girintisi), baca doğrudan dışarı
        x0, y0, x1, y1 = omut['r']
        ky0 = 40.0
        kombi = dict(p=(x1 - 47.8, ky0), on=(x1 - 47.8, ky0 + 15.0))
        pm, rsm = oda_yolu(omut)                      # J→...→mutfak radyatörü (ters çevrilecek)
        xb = omut['xb']
        kok = kombi['on']
        ana = [kok, (kok[0] - 32.0, kok[1]), (kok[0] - 32.0, OFF), (x0 + OFF, OFF), (x0 + OFF, YA0 - OFF),
               (xb, YA0 - OFF), (xb, ym)] + p13[0:1][1:] + [(p13[0][0], ym)] + p13[1:]
        # mutfak radyatörü ana yol üzerinde (geçerken T)
        for r in rsm:                                  # akış batıya: yakın uç doğuda
            r['yakin'], r['uzak'] = r['cx'] + r['L'] / 2, r['cx'] - r['L'] / 2
        yollar.append(dict(ad='ANA', pts=_tekil(ana), rads=rsm + rs13))
        dogu = [o for o in odalar if o['sira'] in 'NS' and o is not o13 and o is not omut]
        bati_x = xb
        dogu_kol = None
        for o in dogu:
            pts, rs = oda_yolu(o)
            if o['xb'] > bati_x:
                if dogu_kol is None:
                    dogu_kol = []
                dogu_kol.append((o, pts, rs))
            else:
                yollar.append(dict(ad=o['m']['ad'] + ' ' + o['m']['no'], pts=pts, rads=rs))
        if dogu_kol:
            # doğu kolu: J=(xb,ym) → en doğudaki odaya; diğer doğu odaları bu koldan ayrılır
            dogu_kol.sort(key=lambda t: t[0]['xb'])
            o, pts, rs = dogu_kol[-1]
            yollar.append(dict(ad='DOĞU KOLU ' + o['m']['ad'] + ' ' + o['m']['no'], pts=[(xb, ym)] + pts, rads=rs))
            for o, pts, rs in dogu_kol[:-1]:
                yollar.append(dict(ad=o['m']['ad'] + ' ' + o['m']['no'], pts=pts, rads=rs))
        yollar.append(dict(ad='ANTRE ' + ant['no'], pts=ant_pts, rads=rs_ant))
    for y in yollar:
        y['pts'] = _tekil(y['pts'])
    agac_kur(yollar)
    return dict(odalar=odalar, radyatorler=radyatorler, yollar=yollar, kapilar=kapilar, pencereler=pencereler,
                kombi=kombi, kok=yollar[0]['pts'][0])


def _tekil(pts):
    out = []
    for p in pts:
        p = (float(p[0]), float(p[1]))
        if out and math.dist(out[-1], p) < 1e-6:
            continue
        out.append(p)
    # doğrusal ara noktaları at
    k = [out[0]]
    for i in range(1, len(out) - 1):
        a, b, c = k[-1], out[i], out[i + 1]
        if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < 1e-6 and \
                (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) > 0:
            continue
        k.append(b)
    k.append(out[-1])
    return k


def agac_kur(yollar):
    """her yolun ebeveynini (başlangıç noktası hangi yolun iç noktasında) ve konumunu bul"""
    for i, y in enumerate(yollar):
        y['id'] = i
        y['ls'] = LineString(y['pts'])
        y['ebeveyn'] = None; y['s0'] = 0.0
    for i, y in enumerate(yollar):
        if i == 0:
            continue
        p = Point(y['pts'][0])
        best = None
        for j, z in enumerate(yollar):
            if j == i:
                continue
            d = z['ls'].distance(p)
            if d < 1e-3:
                s = z['ls'].project(p)
                if best is None or j < best[0]:
                    best = (j, s)
        if best is None:
            raise ValueError('yol bağlanamadı: ' + y['ad'])
        y['ebeveyn'], y['s0'] = best
    for y in yollar:
        for r in y['rads']:
            r['yol'] = y['id']
            r['s_yak'] = y['ls'].project(Point(r['yakin'], r['duvar_y'] + r['ic'] * OFF))
            r['s_uzak'] = y['ls'].project(Point(r['uzak'], r['duvar_y'] + r['ic'] * OFF))


def aynala(pl):
    """A dairesi planını B dairesine (x → 2800-x) çevir"""
    import copy
    q = copy.deepcopy({k: v for k, v in pl.items()})
    for o in q['odalar']:
        x0, y0, x1, y1 = o['r']; o['r'] = (ayna(x1), y0, ayna(x0), y1)
        if o.get('kapi'):
            a, b, yy = o['kapi']; o['kapi'] = (ayna(b), ayna(a), yy); o['xb'] = ayna(o['xb'])
    q['kapilar'] = [(ayna(b), ayna(a), yy) for a, b, yy in q['kapilar']]
    q['pencereler'] = [(ayna(b), ayna(a), yy) for a, b, yy in q['pencereler']]
    for r in q['radyatorler']:
        for k in ('cx', 'yakin', 'uzak'):
            r[k] = ayna(r[k])
    for y in q['yollar']:
        y['pts'] = [(ayna(x), yy) for x, yy in y['pts']]
        # rads listesi derin kopyada radyatorler ile aynı nesneler değil → yeniden eşle
    # yolların rads'ını radyatorler listesindeki kopyalarla eşle
    idmap = {}
    for r in q['radyatorler']:
        idmap[(r['m']['no'], r['sira_no'])] = r
    for y in q['yollar']:
        y['rads'] = [idmap[(r['m']['no'], r['sira_no'])] for r in y['rads']]
    if q['kombi']:
        k = q['kombi']; k['p'] = (ayna(k['p'][0]), k['p'][1]); k['on'] = (ayna(k['on'][0]), k['on'][1]); k['ayna'] = True
    agac_kur(q['yollar'])
    q['kok'] = q['yollar'][0]['pts'][0]
    return q
