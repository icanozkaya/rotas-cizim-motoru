"""yerden2 — MAHAL ISI KAYBI HESABI (kullanıcının "ZEMİN / 1 NK" ısı kaybı sayfası biçiminde; TS 825 / TS 2164 yöntemi).

Kullanıcı 15.10.2026: "ısı kaybı ve yerden ısıtma hesaplarını yap, mahalleri numaralandır ona göre hesaplara işle,
kat yüksekliği 3 m al". Holler (antre-kor.) yerden ısıtılmaz.

Mimariden okunanlar (kat planı, cm):
  * dış duvar: mahal poligonu kenarlarından bina dış yüzüne (K.bina) ≤ 25 cm olanlar; balkona bakan duvar dış duvardır.
    Yön, kenarın dış normalinden (plan kuzeyi yukarı kabul): K / G / D / B.
  * pencere / balkon kapısı: mimari ölçü yazısı çiftleri ("160" üstte genişlik, "230" altta yükseklik, cm),
    en yakın dış duvarlı mahale atanır. Kapı yazısı (90/220 MTEXT) balkona açılıyorsa camlı balkon kapısıdır.
  * iç duvar: ısıtılmayan / farklı sıcaklıktaki komşu mahale (merdiven-asansör 10 °C, hol 15 °C, banyo 24 °C).
  * zemin kat tabanı toprağa oturan döşeme (toprak 6 °C), en üst kat tavanı çatı arasına (dış hava).
Sızıntı: Qs = a · Σl · R · H · ΔT · Ze (şablondaki gibi a 2, R 0,9, H 0,67, Ze 1,2), l = pencere çevresi.
"""
import math
import re

from shapely.geometry import Point, LineString
from shapely.ops import unary_union

KAT_H = 3.00            # m — kullanıcı: kat yüksekliği 3 m
T_DIS = -3.0            # °C — Sakarya / Adapazarı dış tasarım sıcaklığı (TS 2164); TS 825:2024 3. bölge (kullanıcı)
T_TOPRAK = 6.0
T_ORTAK = 10.0          # merdiven / asansör (ısıtılmaz)
T_HOL = 15.0            # daire içi hol (yerden ısıtma yok)
# TS 825:2024 tavsiye edilen (aşılmayacak) U değerleri, W/m²K — İZODER il sayfaları (izoder.org.tr/ts825/<il>.pdf).
# Kullanıcı 15.10.2026: Sakarya 3. bölge; U değerleri bu sınırları AŞMAYACAK. Projenin İZODER hesabı varsa oradaki
# (daha küçük) değerler kullanılır: u_sec(proje_U) -> min(proje, sınır).
TS825_2024 = {1: dict(DD=0.45, Ta=0.35, Dö=0.40, ÇP=1.8), 2: dict(DD=0.40, Ta=0.30, Dö=0.35, ÇP=1.8),
              3: dict(DD=0.40, Ta=0.30, Dö=0.35, ÇP=1.8), 4: dict(DD=0.35, Ta=0.25, Dö=0.30, ÇP=1.8),
              5: dict(DD=0.25, Ta=0.20, Dö=0.25, ÇP=1.8), 6: dict(DD=0.25, Ta=0.20, Dö=0.25, ÇP=1.8)}
BOLGE = 3               # Sakarya (kullanıcı)


def u_sec(bolge=BOLGE, proje=None):
    """bölge sınırları; proje (İZODER) değerleri verilirse her eleman için min(proje, sınır)"""
    s = TS825_2024[bolge]
    u = {'DD': s['DD'], 'ÇP': s['ÇP'], 'BK': s['ÇP'], 'Dö': s['Dö'], 'Ta': s['Ta'], 'İD': 0.814}
    for k, v in (proje or {}).items():
        if k in u and v:
            u[k] = min(v, u.get(k, v)) if k != 'İD' else v
    return u


U = u_sec()
# 15.10.2026 onaylı dosyada kullanılan (şablon) değerler — yalnız kayıt için:
U_15_10 = {'DD': 0.479, 'ÇP': 2.40, 'BK': 2.40, 'Dö': 0.269, 'Ta': 0.30, 'İD': 0.814}
AD = {'DD': 'Dış duvar', 'ÇP': 'Pencere (PVC çift cam)', 'BK': 'Balkon kapısı (camlı)', 'Dö': 'Döşeme (toprak)',
      'Ta': 'Tavan (çatı arası)', 'İD': 'İç duvar'}
ZD = 7                  # işletme zammı %
ZH = {'K': 5, 'D': 0, 'G': -5, 'B': 0}
SIZ = dict(a=2.0, R=0.9, H=0.67, Ze=1.2)


def _yon(n):
    nx, ny = n
    if abs(ny) >= abs(nx):
        return 'K' if ny > 0 else 'G'
    return 'D' if nx > 0 else 'B'


def _kenarlar(poly):
    out = []
    c = list(poly.exterior.coords)
    for p, q in zip(c[:-1], c[1:]):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L < 8:
            continue
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        n = (uy, -ux)
        if poly.contains(Point(m[0] + n[0] * 5, m[1] + n[1] * 5)):
            n = (-n[0], -n[1])
        out.append(dict(p=p, q=q, L=L, m=m, n=n))
    return out


def _dis_boy(e, bina, adim=10.0, derin=80.0):
    """kenarın dış duvar boyu (cm): kenar boyunca 10 cm'de bir, dış normal yönünde 80 cm ilerisi bina dışında
    (dış hava / balkon) kalan noktalar"""
    n = max(1, int(e['L'] // adim))
    say = 0
    for i in range(n):
        t = (i + 0.5) / n
        x = e['p'][0] + (e['q'][0] - e['p'][0]) * t + e['n'][0] * derin
        y = e['p'][1] + (e['q'][1] - e['p'][1]) * t + e['n'][1] * derin
        if not bina.contains(Point(x, y)):
            say += 1
    return e['L'] * say / n


def _sayi(t):
    return re.fullmatch(r'\d{2,3}', t.strip()) is not None


def pencereler(K):
    """mimari ölçü yazısı çiftleri -> [(merkez, genişlik m, yükseklik m, tür)]"""
    Y = [y for y in K.yazilar]
    tek = [(y[4], y[1].strip(), y[3]) for y in Y if _sayi(y[1]) and int(y[1]) >= 40]
    kul = set()
    out = []
    for i, (c1, t1, r1) in enumerate(tek):
        if i in kul:
            continue
        en = None
        for j, (c2, t2, r2) in enumerate(tek):
            if j == i or j in kul or abs(r1 - r2) > 1:
                continue
            dx, dy = c2[0] - c1[0], c2[1] - c1[1]
            if abs(r1) < 1:
                ok = abs(dx) < 8 and 8 <= abs(dy) <= 18
            else:
                ok = abs(dy) < 8 and 8 <= abs(dx) <= 18
            if ok and (en is None or math.hypot(dx, dy) < en[0]):
                en = (math.hypot(dx, dy), j)
        if en is None:
            continue
        j = en[1]
        c2, t2, _ = tek[j]
        # genişlik: 0° yazıda üstteki, 90° yazıda soldaki
        if abs(r1) < 1:
            g, h = (t1, t2) if c1[1] > c2[1] else (t2, t1)
        else:
            g, h = (t1, t2) if c1[0] < c2[0] else (t2, t1)
        kul.update((i, j))
        out.append(((
            (c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2), int(g) / 100.0, int(h) / 100.0, 'ÇP'))
    # kapı yazıları (MTEXT "90\n220"): balkona açılan kapı camlı balkon kapısı
    for y in Y:
        m = re.fullmatch(r'(\d{2,3})\s*\n\s*(\d{3})', y[1].strip())
        if m:
            out.append((y[4], int(m.group(1)) / 100.0, int(m.group(2)) / 100.0, 'KAPI'))
    return out


def hesapla(K, odalar, ust_kat, zemin_kat, holler=()):
    """odalar: ısıtılan mahaller (poly, sic, ad, zon, tur). Her mahale o['isi_kaybi'] yazar, toplam W döner."""
    dis = K.bina.exterior
    tum = [r for r in K.rooms]
    balkon = [r['poly'] for r in tum if r['tip'] == 'balkon']
    P = pencereler(K)
    DIS = unary_union([dis.buffer(25)] + [b.buffer(35) for b in balkon])
    # pencere -> mahal (dış duvarı olan, en yakın; balkon kapısı balkon + mahal arasında)
    atama = {}
    for pi, (c, g, h, tur) in enumerate(P):
        pt = Point(c)
        if tur == 'KAPI':
            yb = [b for b in balkon if b.distance(pt) < 45]
            if not yb:
                continue
            aday = [o for o in odalar if o['poly'].distance(pt) < 45]
            if not aday:
                continue
            o = min(aday, key=lambda o: o['poly'].distance(pt))
            atama.setdefault(id(o), []).append((pt, g, h, 'BK'))
            continue
        en = None
        for o in list(odalar) + [dict(poly=r['poly'], _yok=True) for r in tum if r['tip'] in ('ortak', 'hol')]:
            for e in _kenarlar(o['poly']):
                if _dis_boy(e, K.bina) < 20:
                    continue
                d = LineString([e['p'], e['q']]).distance(pt)
                if d < 90 and (en is None or d < en[0]):
                    en = (d, o, e)
        if en is None or en[1].get('_yok'):
            continue
        atama.setdefault(id(en[1]), []).append((pt, g, h, 'ÇP'))
    toplam = 0.0
    for o in odalar:
        Ti = o['sic']
        sat = []          # (işaret, yön, uzunluk m, yükseklik m, adet, U, ΔT, ZH, pencere satır indeksleri)
        pen = atama.get(id(o), [])
        dis_kenar = {}
        ic_kenar = []
        for e in _kenarlar(o['poly']):
            seg = LineString([e['p'], e['q']])
            Ld = _dis_boy(e, K.bina)
            if Ld >= 20:
                y = _yon(e['n'])
                dis_kenar[y] = dis_kenar.get(y, 0.0) + Ld / 100.0
            if e['L'] - Ld < 20:
                continue
            # komşu mahal (dış normal yönünde 15–35 cm)
            q = Point(e['m'][0] + e['n'][0] * 25, e['m'][1] + e['n'][1] * 25)
            kom = next((r for r in tum if r['poly'].buffer(12).contains(q) and r['poly'] is not o['poly']), None)
            if kom is None:
                continue
            if kom['tip'] == 'ortak' or kom.get('daire') is None:
                Tk = T_ORTAK
            elif kom['tip'] == 'hol':
                Tk = T_HOL
            else:
                ko = next((x for x in odalar if x['poly'].equals(kom['poly']) or x['poly'].buffer(5).contains(kom['poly'].representative_point())), None)
                Tk = ko['sic'] if ko else T_HOL
            if Ti - Tk > 0.5:
                ic_kenar.append((e['L'] / 100.0, Ti - Tk))
        # pencereleri yönlerine dağıt
        pen_y = {}
        for pt, g, h, tur in pen:
            en = None
            for e in _kenarlar(o['poly']):
                d = LineString([e['p'], e['q']]).distance(pt)
                if en is None or d < en[0]:
                    en = (d, _yon(e['n']))
            pen_y.setdefault(en[1], []).append((g, h, tur))
            if en[1] not in dis_kenar:
                dis_kenar[en[1]] = g
        dT = Ti - T_DIS
        for y in ('K', 'D', 'G', 'B'):
            if y not in dis_kenar:
                continue
            i_dd = len(sat)
            sat.append(['DD', y, round(dis_kenar[y], 2), KAT_H, 1, U['DD'], dT, ZH[y], []])
            for g, h, tur in pen_y.get(y, []):
                sat[i_dd][8].append(len(sat))
                sat.append([tur, y, g, h, 1, U[tur], dT, ZH[y], []])
        ic_top = {}
        for L, d in ic_kenar:                       # aynı ΔT'li iç duvar parçaları tek satır
            ic_top[round(d, 1)] = ic_top.get(round(d, 1), 0.0) + L
        for d, L in sorted(ic_top.items(), key=lambda x: -x[0]):
            if L >= 0.3:
                sat.append(['İD', '', round(L, 2), KAT_H, 1, U['İD'], d, 0, []])
        A = round(o['poly'].area / 1e4, 2)
        if zemin_kat:
            sat.append(['Dö', '', A, 1.0, 1, U['Dö'], Ti - T_TOPRAK, 0, []])
        if ust_kat:
            sat.append(['Ta', '', A, 1.0, 1, U['Ta'], dT, 0, []])
        # hesap (Excel formülleriyle aynı)
        Q0 = 0.0
        for s in sat:
            F = s[2] * s[3]
            Hc = sum(sat[j][2] * sat[j][3] * sat[j][4] for j in s[8])
            Ia = F * s[4] - Hc
            Q0 += Ia * s[5] * s[6] * (1 + (ZD + s[7]) / 100.0)
        l = sum((s[2] + s[3]) * 2 * s[4] for s in sat if s[0] in ('ÇP', 'BK'))
        Qs = SIZ['a'] * l * SIZ['R'] * SIZ['H'] * dT * SIZ['Ze']
        Q = Q0 + Qs
        o['isi_kaybi'] = dict(satirlar=sat, l=round(l, 2), dT=dT, Qs=round(Qs, 1), Q0=round(Q0, 1), Q=round(Q, 1))
        toplam += Q
    return toplam
