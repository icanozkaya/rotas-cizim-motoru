# -*- coding: utf-8 -*-
"""Temsili daire tipik planı (DENEME – mimari yok) + KOLEKTÖRLÜ daire içi dağıtım (R2).

Koordinatlar cm. A dairesi x∈[0,1200], merdiven holü x∈[1200,1600] (y≥420), B dairesi A'nın aynası x∈[1600,2800].

Akış (her daire):
  merkezi : kolon (hol köşesi) → KALORİMETRE SETİ (hol duvarında sayaç dolabı) → daire kapısı → KOLEKTÖR DOLABI (antre)
  kombi   : kombi (mutfak dış duvarı) → KOLEKTÖR DOLABI (antre)
  kolektör → her radyatöre ayrı PEX gidiş-dönüş çifti (duvar boyu, kapıdan girer).

Radyatör yerleşimi: önce pencere altı (radyatör boyu ≤ pencere genişliği), olmazsa pencereye en yakın boş duvar
(kapı açılımı, tefriş, kolektör dolabı ve diğer radyatörler dışında).

Devre güzergâhı: antrede şeritler (kuzey odalara giden devreler kuzey şeritlerde, güneydekiler güney şeritlerde; ilk
ayrılan en dış şeritte), odada kapıdan girip duvar boyu (duvara en yakın iz ilk biten devrenin) → çizgiler kesişmez."""
import math
import copy
from shapely.geometry import LineString, Point, box as sbox, Polygon

GEN, DER = 1200.0, 1000.0
YA0, YA1 = 420.0, 580.0          # antre şeridi
GENIS_TOP = 2800.0
CEK = 5.0                        # radyatör duvar boşluğu
D0 = 20.0                        # ilk iz (devre eksen çizgisi) duvar uzaklığı
P = 14.0                         # iz / şerit / kolektör ağız aralığı (eksenler arası)
HP = 3.0                         # PEX gidiş-dönüş yarı aralığı (çizgiler eksen ±3)
HF = 8.0                         # besleme hattı (kolon/kombi → kolektör) yarı aralığı
KOL_D = 16.0                     # kolektör dolabı derinliği (antre güney duvarında, oda tarafı)
LANE_LO, LANE_HI = 458.0, 562.0  # antre şerit bandı
KAPI_PAY = 14.0                  # kapı kasası payı (giriş noktaları)
OFF = D0                         # geriye uyum
H = HP


def ayna(x):
    return GENIS_TOP - x


# ------------------------------------------------------------------ duvar çerçevesi
def duvarlar(r):
    """oda dikdörtgeninin duvarları, CCW: S, E, N, W. t = duvar yönü, n = oda içi normal"""
    x0, y0, x1, y1 = r
    k = [((x0, y0), (x1, y0), 'S'), ((x1, y0), (x1, y1), 'E'), ((x1, y1), (x0, y1), 'N'), ((x0, y1), (x0, y0), 'W')]
    out = {}
    for p0, p1, ad in k:
        L = math.dist(p0, p1)
        t = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
        n = (-t[1], t[0])
        out[ad] = dict(ad=ad, p0=p0, p1=p1, t=t, n=n, L=L)
    return out


def nokta(w, s, b=0.0):
    return (w['p0'][0] + s * w['t'][0] + b * w['n'][0], w['p0'][1] + s * w['t'][1] + b * w['n'][1])


def s_of(w, p):
    return (p[0] - w['p0'][0]) * w['t'][0] + (p[1] - w['p0'][1]) * w['t'][1]


def _rad_boy(m):
    return m['boy'] * 100.0


def _uc_payi(m):
    """radyatör bağlantı uçlarının gövde merkezinden uzaklığı (vana tarafı, rakor tarafı) — MTY blok ölçüleri"""
    L = _rad_boy(m)
    if m['tip'] == 'Banyopan':
        s = L / 32.0
        return 16.0 * s, 16.0 * s
    s = L / 100.0
    return 54.7 * s, 50.7 * s


# ------------------------------------------------------------------ temsili mimari: odalar, kapılar, pencereler, tefriş
def odalar_kur(mahaller):
    odalar_list = [m for m in mahaller if m['ad'] == 'ODA']
    sal = [m for m in mahaller if m['ad'] == 'SALON'][0]
    mut = [m for m in mahaller if m['ad'] == 'MUTFAK'][0]
    ant = [m for m in mahaller if m['ad'] == 'ANTRE'][0]
    ban = [m for m in mahaller if m['ad'] == 'BANYO'][0]
    oda_s = odalar_list[-1]
    oda_n = odalar_list[:-1]
    odalar = []
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
    for o in odalar:
        o['duvar'] = duvarlar(o['r'])
        x0, y0, x1, y1 = o['r']
        if o['sira'] == 'N':
            o['kapi'] = (x1 - 110.0, x1 - 20.0, YA1); o['kapi_duvar'] = 'S'; o['mente'] = x1 - 110.0
        elif o['sira'] == 'S':
            o['kapi'] = (x0 + 20.0, x0 + 110.0, YA0); o['kapi_duvar'] = 'N'; o['mente'] = x0 + 110.0
        else:
            o['kapi'] = None
    return odalar


def pencereler_kur(odalar, MP):
    """MP: parametre mimari.pencere {MAHAL: [genişlik | 'B<genişlik>' (balkon kapısı)]} – dış cephe duvarına"""
    for o in odalar:
        x0, y0, x1, y1 = o['r']
        o['pencere'] = []
        if o['sira'] == 'A':
            continue
        lst = MP.get(o['m']['ad'], [])
        yy = DER if o['sira'] == 'N' else 0.0
        W = x1 - x0
        n = len(lst)
        if n == 1:
            fr = [0.5]
        elif n == 2:
            fr = [0.33, 0.77]
        else:
            fr = [(i + 1) / (n + 1) for i in range(n)]
        for f, v in zip(fr, lst):
            tip = 'B' if isinstance(v, str) and v.upper().startswith('B') else 'P'
            w = float(str(v)[1:]) if tip == 'B' else float(v)
            c = x0 + W * f
            o['pencere'].append(dict(a=c - w / 2, b=c + w / 2, y=yy, tip=tip, w=w, duvar='N' if o['sira'] == 'N' else 'S'))
    return odalar


def tefris_kur(odalar, sistem):
    """temsili tefriş (yalnız radyatör yerleşiminde engel + planda ince çizgi)"""
    for o in odalar:
        x0, y0, x1, y1 = o['r']
        ad = o['m']['ad']
        cy = (y0 + y1) / 2
        T = []
        if ad == 'MUTFAK':
            T += [(x0, y0, x0 + 60, y0 + 300, 'TEZGAH'), (x0 + 60, y0, x0 + 220, y0 + 60, 'TEZGAH')]
            if sistem == 'kombi':
                T += [(x1 - 48, y0 + 40, x1, y0 + 70, 'KOMBİ')]
        elif ad == 'BANYO':
            T += [(x0, y0, x0 + 70, y0 + 170, 'KÜVET'), (x1 - 45, y0 + 210, x1, y0 + 265, 'LAVABO'),
                  (x1 - 60, y0 + 70, x1, y0 + 110, 'KLOZET')]
        elif ad == 'ODA':
            if o['sira'] == 'N':
                T += [(x0, y0 + 100, x0 + 60, y1 - 30, 'GARDIROP'), (x1 - 200, cy - 80, x1, cy + 80, 'YATAK')]
            else:
                T += [(x1 - 60, y0 + 20, x1, y0 + 290, 'GARDIROP'), (x0, cy - 80, x0 + 200, cy + 80, 'YATAK')]
        elif ad == 'SALON':
            T += [(x0, cy - 90, x0 + 45, cy + 90, 'TV ÜNİTESİ'), (x1 - 90, y0 + 120, x1, y1 - 70, 'KANEPE')]
        elif ad == 'ANTRE':
            T += [(GEN - 220, YA1 - 35, GEN - 120, YA1, 'VESTİYER')]
        o['tefris'] = T
    return odalar


def _kapi_alani(o):
    """kapı kanadı açılım çeyreği (oda içinde) – dikdörtgen yaklaşık"""
    if not o.get('kapi'):
        return None
    a, b, yy = o['kapi']
    w = b - a
    if o['sira'] == 'N':
        return (a, yy, b, yy + w)
    return (a, yy - w, b, yy)


# ------------------------------------------------------------------ radyatör yerleşimi
def _engeller(o, duvar_ad, ek=()):
    """duvar boyunca dolu aralıklar (s0, s1)"""
    w = o['duvar'][duvar_ad]
    ara = []
    DER_ = 18.0                                              # radyatör + vana derinliği
    rects = [(r[0], r[1], r[2], r[3]) for r in o.get('tefris', [])]
    ka = _kapi_alani(o)
    if ka:
        rects.append(ka)
    rects += list(ek)
    wl = LineString([w['p0'], w['p1']])
    for x0, y0, x1, y1 in rects:
        q = sbox(x0, y0, x1, y1)
        if q.distance(wl) <= DER_:
            s = sorted([s_of(w, (x0, y0)), s_of(w, (x1, y0)), s_of(w, (x0, y1)), s_of(w, (x1, y1))])
            ara.append((s[0] - 8.0, s[-1] + 8.0))
    # kapı boşlukları (her iki taraftaki odalar için de duvar dolu)
    if o.get('kapi') and o['kapi_duvar'] == duvar_ad:
        a, b, _ = o['kapi']
        s = sorted([s_of(w, (a, o['kapi'][2])), s_of(w, (b, o['kapi'][2]))])
        ara.append((s[0] - 10, s[1] + 10))
    for p in o.get('pencere', []):
        if p['duvar'] == duvar_ad and (p['tip'] == 'B' or p.get('dolu')):
            s = sorted([s_of(w, (p['a'], p['y'])), s_of(w, (p['b'], p['y']))])
            ara.append((s[0] - 10, s[1] + 10))
    ara.append((-1e9, 50.0)); ara.append((w['L'] - 50.0, 1e9))      # köşe payı (iz + bağlantı)
    return ara


def _bos_araliklar(ara, L):
    ara = sorted(ara)
    bos, cur = [], -1e9
    for a, b in ara:
        if a > cur:
            bos.append((cur, a))
        cur = max(cur, b)
    bos.append((cur, 1e9))
    return [(max(a, 0.0), min(b, L)) for a, b in bos if min(b, L) - max(a, 0.0) > 1.0]


def rad_kaydi(o, m, k, w, sc, neden):
    L = _rad_boy(m)
    c = nokta(w, sc)
    return dict(oda=o, m=m, sira_no=k + 1, L=L, tip=m['tip'], ver=m['ver'], model=m['model'], boy=m['boy'],
                duvar=w['ad'], c=c, t=w['t'], n=w['n'], s=sc, yer=neden, wref=w)


def radyator_yerlestir(o, hedef=None, ek_engel=(), duvar_sec=None):
    """odanın radyatörlerini yerleştirir. Dönüş: radyatör kayıtları. 1) pencere altı (L ≤ cam), 2) en yakın boş duvar."""
    m = o['m']
    adet = int(m['adet'])
    L = _rad_boy(m)
    out = []
    kullanilan = []
    for k in range(adet):
        yer = None
        # 1) pencere altı
        for p in o.get('pencere', []):
            if p['tip'] != 'P' or p.get('dolu'):
                continue
            if L <= p['w'] - 10.0 + 1e-6:
                w = o['duvar'][p['duvar']]
                sc = s_of(w, ((p['a'] + p['b']) / 2, p['y']))
                yer = (w, sc, 'pencere altı (cam %.0f cm ≥ radyatör %.0f cm)' % (p['w'], L))
                p['dolu'] = True
                break
        if yer is None:
            # 2) en yakın boş duvar: hedef = sığmayan / en yakın pencere ortası, yoksa verilen hedef
            pen = [p for p in o.get('pencere', []) if p['tip'] == 'P']
            if pen:
                hp = ((pen[0]['a'] + pen[0]['b']) / 2, pen[0]['y'])
                neden = 'pencere yok / sığmadı → pencereye en yakın boş duvar'
                if all(p.get('dolu') for p in pen):
                    neden = 'pencereler dolu → pencereye en yakın boş duvar'
                elif any(L > p['w'] - 10 for p in pen):
                    neden = 'radyatör pencere camından uzun → en yakın boş duvar'
            else:
                hp = hedef or ((o['r'][0] + o['r'][2]) / 2, (o['r'][1] + o['r'][3]) / 2)
                neden = 'pencere yok → en yakın boş duvar'
            best = None
            for wa in (duvar_sec or ('S', 'E', 'N', 'W')):
                w = o['duvar'][wa]
                ara = _engeller(o, wa, ek_engel) + [(r['s'] - r['L'] / 2 - 25, r['s'] + r['L'] / 2 + 25) for r in out + kullanilan
                                                     if r['duvar'] == wa]
                ic, dis = _uc_payi(m)
                for a, b in _bos_araliklar(ara, w['L']):
                    lo, hi = a + max(ic, dis) + 4, b - max(ic, dis) - 4
                    if hi < lo:
                        continue
                    sh = min(max(s_of(w, hp), lo), hi)
                    d = math.dist(nokta(w, sh), hp)
                    if best is None or d < best[0]:
                        best = (d, w, sh)
            if best is None:
                raise ValueError(f"{m['ad']} {m['no']}: radyatör için boş duvar bulunamadı")
            yer = (best[1], best[2], neden)
        r = rad_kaydi(o, m, k, yer[0], yer[1], yer[2])
        out.append(r)
    return out


# ------------------------------------------------------------------ iç çevre yürüyüşü (oda içinde duvar boyu iz)
def _cevre(r, d):
    x0, y0, x1, y1 = r[0] + d, r[1] + d, r[2] - d, r[3] - d
    W, Hh = x1 - x0, y1 - y0
    kose = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return kose, W, Hh, 2 * (W + Hh)


def _u(r, d, p):
    kose, W, Hh, Pe = _cevre(r, d)
    x0, y0 = kose[0]; x1, y1 = kose[2]
    x, y = p
    if abs(y - y0) < 1e-6:
        return x - x0
    if abs(x - x1) < 1e-6:
        return W + (y - y0)
    if abs(y - y1) < 1e-6:
        return W + Hh + (x1 - x)
    return 2 * W + Hh + (y1 - y)


def _yuru(r, d, ua, ub, yon):
    """ua'dan ub'ye yon (+1 CCW, -1 CW) yürü; ara köşe noktaları"""
    kose, W, Hh, Pe = _cevre(r, d)
    ku = [0.0, W, W + Hh, 2 * W + Hh]
    pts = []
    if yon > 0:
        L = (ub - ua) % Pe
        for i, k in enumerate(ku):
            dd = (k - ua) % Pe
            if 1e-6 < dd < L - 1e-6:
                pts.append((dd, kose[i]))
    else:
        L = (ua - ub) % Pe
        for i, k in enumerate(ku):
            dd = (ua - k) % Pe
            if 1e-6 < dd < L - 1e-6:
                pts.append((dd, kose[i]))
    pts.sort()
    return [p for _, p in pts], L


def _iz_noktasi(r, wref, s, d):
    """duvar üzerindeki s konumunun d izindeki karşılığı"""
    return nokta(wref, s, d)


# ------------------------------------------------------------------ ana kurulum
def daire_plani(mahaller, sistem, MP=None):
    MP = MP or {}
    pen = MP.get('pencere', {'ODA': [150], 'SALON': [200, 'B100'], 'MUTFAK': [120], 'BANYO': [60], 'ANTRE': []})
    odalar = odalar_kur(mahaller)
    pencereler_kur(odalar, pen)
    tefris_kur(odalar, sistem)
    oant = [o for o in odalar if o['sira'] == 'A'][0]
    n_rad = sum(int(o['m']['adet']) for o in odalar)

    # ---- besleme hattı ve kolektör konumu
    if sistem == 'merkezi':
        kolon = (GEN + 35.0, DER - 35.0)                     # hol kuzey-batı köşesi
        xf = GEN - 15.0
        besleme = [kolon, (GEN + 35.0, 525.0), (xf, 525.0), (xf, YA0 + KOL_D)]
        set_y = [DER - 80.0, DER - 130.0, DER - 180.0, DER - 230.0, DER - 280.0]   # set elemanları (kolondan daireye)
        kombi = None
    else:
        kolon = None
        kombi = dict(p=(GEN - 48.0, 40.0), rot=0.0)
        xf = GEN - 29.0
        besleme = [(xf, 70.0), (xf, YA0 + KOL_D)]
        set_y = []
    kol_x1 = xf + HF + 6.0
    kol_x0 = (xf - HF) - 12.0 - (n_rad - 1) * P - 10.0
    kolektor = dict(x0=kol_x0, x1=kol_x1, y0=YA0, y1=YA0 + KOL_D, n=n_rad, xf=xf)

    # ---- radyatörler
    radyatorler = []
    for o in odalar:
        if o['sira'] == 'A':
            continue
        o['rads'] = radyator_yerlestir(o)
        radyatorler += o['rads']
    # antre: pencere yok → kolektöre en yakın boş duvar (kuzey/güney), kolektörün batısında
    kol_engel = [(kol_x0 - 30.0, YA0, GEN, YA0 + KOL_D + 5.0)]
    hedef = (kol_x0 - 60.0, YA0)
    oant['rads'] = radyator_yerlestir(oant, hedef=hedef, ek_engel=kol_engel, duvar_sec=('S', 'N'))
    radyatorler += oant['rads']
    for r in oant['rads']:
        if r['c'][0] + r['L'] > kol_x0:
            raise ValueError('antre radyatörü kolektörün doğusunda kaldı')

    # ---- oda içi yön ve iz sırası
    devreler = []
    for o in odalar:
        if o['sira'] == 'A':
            continue
        rads = o['rads']
        kw = o['duvar'][o['kapi_duvar']]
        a, b, yy = o['kapi']
        ec = (a + b) / 2
        r_ = o['r']
        best = None
        for yon in (1, -1):
            uz = []
            for r in rads:
                ic, dis = _uc_payi(r['m'])
                # yaklaşma ucu: CCW yürüyüşte duvar t yönü artar → yakın uç küçük s
                s_n = r['s'] - (max(ic, dis) + 2) * yon
                pa = _iz_noktasi(r_, kw, s_of(kw, (ec, yy)), D0)
                pb = _iz_noktasi(r_, r['wref'], s_n, D0)
                _, L = _yuru(r_, D0, _u(r_, D0, pa), _u(r_, D0, pb), yon)
                uz.append(L)
            sk = max(uz)
            # kombi beslemesi mutfaktan geçer → kesişen yön elenir
            if best is None or sk < best[0]:
                best = (sk, yon, uz)
        cand = [best]
        alt = 1 if best[1] == -1 else -1
        cand.append((None, alt, None))
        o['_yon_aday'] = [c[1] for c in cand]
        o['yon'] = best[1]
        sira = sorted(range(len(rads)), key=lambda i: best[2][i])
        for k, i in enumerate(sira):
            r = rads[i]
            r['k'] = k
            devreler.append(dict(rad=r, oda=o, k=k, d=D0 + k * P, taraf='N' if o['sira'] == 'N' else 'S'))
    for r in oant['rads']:
        devreler.append(dict(rad=r, oda=oant, k=0, d=None, taraf='N' if r['duvar'] == 'N' else 'S', antre=True))

    def oda_girisleri(o):
        """kapı açıklığındaki giriş x'leri (k=0 yürüme yönü tarafında)"""
        a, b, yy = o['kapi']
        kw = o['duvar'][o['kapi_duvar']]
        v = kw['t'][0] * o['yon']                           # yürüme yönünün x bileşeni (+1 doğu / -1 batı)
        ds = [dv for dv in devreler if dv['oda'] is o]
        n = len(ds)
        pk = min(P, (b - a - 2 * KAPI_PAY) / max(1, n - 1)) if n > 1 else P
        for dv in ds:
            e0 = (b - KAPI_PAY) if v > 0 else (a + KAPI_PAY)
            dv['e'] = e0 - v * dv['k'] * pk

    for o in odalar:
        if o['sira'] != 'A':
            oda_girisleri(o)
    for dv in devreler:
        if dv.get('antre'):
            r = dv['rad']
            ic, dis = _uc_payi(r['m'])
            dv['e'] = r['c'][0] + max(ic, dis) + 2          # antre: doğudan gelinir, yakın uç doğu ucu

    # ---- şeritler
    def seritle():
        N = sorted([d for d in devreler if d['taraf'] == 'N'], key=lambda d: -d['e'])
        S = sorted([d for d in devreler if d['taraf'] == 'S'], key=lambda d: -d['e'])
        nt = len(N) + len(S)
        pl = min(P, (LANE_HI - LANE_LO) / max(1, nt - 1))
        for i, d in enumerate(N):
            d['serit'] = LANE_HI - i * pl
        for i, d in enumerate(S):
            d['serit'] = LANE_LO + i * pl
        return pl
    pl = seritle()
    # ---- kolektör ağızları (batıdan doğuya şerit yüksekliği artar)
    sirali = sorted(devreler, key=lambda d: d['serit'])
    for i, d in enumerate(sirali):
        d['port'] = kol_x0 + 10.0 + i * P
        d['no'] = i + 1
    # kapı ağız hizasındaysa giriş = ağız (doğuya geri dönüş olmasın)
    for o in odalar:
        if o['sira'] == 'A':
            continue
        a, b, yy = o['kapi']
        ds = [d for d in devreler if d['oda'] is o]
        if any(d['e'] > d['port'] + 1e-6 for d in ds):
            if all(a + 6 <= d['port'] <= b - 6 for d in ds):
                for d in ds:
                    d['e'] = d['port']
            else:
                raise ValueError(f"{o['m']['ad']} {o['m']['no']}: kapı kolektör ağzının doğusunda – güzergâh kurulamadı")

    # ---- güzergâhlar (eksen çizgileri)
    def oda_yolu(dv, yon):
        o = dv['oda']; r = dv['rad']; d = dv['d']
        a, b, yy = o['kapi']
        kw = o['duvar'][o['kapi_duvar']]
        ic, dis = _uc_payi(r['m'])
        s_n = r['s'] - (max(ic, dis) + 2) * yon
        pa = nokta(kw, s_of(kw, (dv['e'], yy)), d)
        pb = nokta(r['wref'], s_n, d)
        ara, _ = _yuru(o['r'], d, _u(o['r'], d, pa), _u(o['r'], d, pb), yon)
        return [(dv['port'], kolektor['y1']), (dv['port'], dv['serit']), (dv['e'], dv['serit']), (dv['e'], yy), pa] + ara + [pb]

    bes_ls = LineString(besleme)
    for o in odalar:
        if o['sira'] == 'A':
            continue
        ds = [d for d in devreler if d['oda'] is o]
        for yon in o['_yon_aday']:
            ok = True
            for dv in ds:
                pts = _tekil(oda_yolu(dv, yon))
                if LineString(pts).distance(bes_ls) < HF + HP + 2:
                    ok = False
                dv['pts'] = pts
            if ok:
                if yon != o['yon']:
                    # yön değişti: iz sırası ve girişler yeniden
                    o['yon'] = yon
                    uz = []
                    for dv in ds:
                        uz.append(LineString(dv['pts']).length)
                    for k, dv in enumerate(sorted(ds, key=lambda z: LineString(z['pts']).length)):
                        dv['k'] = k; dv['d'] = D0 + k * P; dv['rad']['k'] = k
                    oda_girisleri(o)
                    for dv in ds:
                        dv['pts'] = _tekil(oda_yolu(dv, yon))
                break
        else:
            raise ValueError(f"{o['m']['ad']}: besleme hattıyla kesişmeyen güzergâh yok")
    for dv in devreler:
        if dv.get('antre'):
            dv['pts'] = _tekil([(dv['port'], kolektor['y1']), (dv['port'], dv['serit']), (dv['e'], dv['serit'])])
            dv['d'] = abs(dv['serit'] - dv['rad']['c'][1])
    # şerit/ağız değişmiş olabilir → yeniden kontrol
    sorun = _kesisme_kontrol(devreler, besleme)
    for dv in devreler:
        dv['rad']['devre'] = dv['no']
    pl_ = dict(odalar=odalar, radyatorler=radyatorler, devreler=sorted(devreler, key=lambda d: d['no']), kolektor=kolektor,
               besleme=besleme, kolon=kolon, kombi=kombi, set_y=set_y, sistem=sistem,
               kapilar=[o['kapi'] for o in odalar if o.get('kapi')], sorun=sorun)
    return pl_


def _kesisme_kontrol(devreler, besleme):
    out = []
    ls = [(d['no'] if 'no' in d else i, LineString(d['pts'])) for i, d in enumerate(devreler)]
    for i in range(len(ls)):
        for j in range(i + 1, len(ls)):
            a, b = ls[i][1], ls[j][1]
            if a.distance(b) < 2 * HP + 2.0:
                # yalnız başlangıç (kolektör yüzü) dışında
                out.append(f'devre {ls[i][0]} ile {ls[j][0]} kesişiyor / çok yakın ({a.distance(b):.1f} cm)')
    b = LineString(besleme)
    for n, l in ls:
        if l.distance(b) < HF + HP + 1.0:
            out.append(f'devre {n} besleme hattına çok yakın')
    return out


def _tekil(pts):
    out = []
    for p in pts:
        p = (float(p[0]), float(p[1]))
        if out and math.dist(out[-1], p) < 1e-6:
            continue
        out.append(p)
    k = [out[0]]
    for i in range(1, len(out) - 1):
        a, b, c = k[-1], out[i], out[i + 1]
        if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < 1e-6 and \
                (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) > 0:
            continue
        k.append(b)
    k.append(out[-1])
    return k


def kose_sayisi(pts):
    return max(0, len(pts) - 2)


def uzunluk(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# ------------------------------------------------------------------ ayna (B dairesi)
def _ap(p):
    return (ayna(p[0]), p[1])


def _av(v):
    return (-v[0], v[1])


def aynala(pl):
    q = copy.deepcopy(pl)
    for o in q['odalar']:
        x0, y0, x1, y1 = o['r']; o['r'] = (ayna(x1), y0, ayna(x0), y1)
        o['duvar'] = duvarlar(o['r'])
        if o.get('kapi'):
            a, b, yy = o['kapi']; o['kapi'] = (ayna(b), ayna(a), yy); o['mente'] = ayna(o['mente'])
        for p in o.get('pencere', []):
            p['a'], p['b'] = ayna(p['b']), ayna(p['a'])
        o['tefris'] = [(ayna(r[2]), r[1], ayna(r[0]), r[3], r[4]) for r in o.get('tefris', [])]
        o['ayna'] = True
    for r in q['radyatorler']:
        r['c'] = _ap(r['c']); r['t'] = _av(r['t']); r['n'] = _av(r['n'])
        r['duvar'] = {'E': 'W', 'W': 'E'}.get(r['duvar'], r['duvar'])
    # radyator nesneleri devrelerde aynı (deepcopy bellek eşlemesi korunur)
    for d in q['devreler']:
        d['pts'] = [_ap(p) for p in d['pts']]
        d['port'] = ayna(d['port']); d['e'] = ayna(d['e'])
    k = q['kolektor']; k['x0'], k['x1'] = ayna(k['x1']), ayna(k['x0']); k['xf'] = ayna(k['xf'])
    q['besleme'] = [_ap(p) for p in q['besleme']]
    if q['kolon']:
        q['kolon'] = _ap(q['kolon'])
    if q['kombi']:
        q['kombi'] = dict(p=(ayna(q['kombi']['p'][0]), q['kombi']['p'][1]), rot=0.0, ayna=True)
    q['kapilar'] = [o['kapi'] for o in q['odalar'] if o.get('kapi')]
    q['ayna'] = True
    return q
