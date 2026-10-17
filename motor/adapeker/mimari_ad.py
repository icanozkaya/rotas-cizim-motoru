# -*- coding: utf-8 -*-
"""Adapeker mimari tanıma: kat pencereleri, akslar, betonarme kolonlar, mahal poligonları (etiketten taşma dolgusu).
Duvar engeli: YLZ-DUVAR, YLZ-KOLON, YLZ-PENCERE, YLZ-BACA, YLZ-HAVALANDIRMA + kapı yaylarının kapalı konum çizgileri."""
import pickle, math, re, os
import numpy as np
import cv2
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

FLAT = '/tmp/claude-0/ad/flat.pkl'
OFS = {'Z': 0.0, '1': 2350.0, '2': 4700.0}
KAT_ADI = {'Z': 'ZEMİN KAT', '1': '1. KAT', '2': '2. KAT'}
W0 = (-1000.0, -3120.0, 760.0, -1500.0)          # zemin kat bina penceresi (cm)
AKS_X = {'1': -924, '2': -874, '3': -549, '4': -244, '5': -124, '6': -4, '7': 301, '8': 626, '9': 676}
AKS_Y = {'A': -1583, 'B': -1683, 'C': -2173, 'D': -2368, 'E': -2873, 'F': -3048}
SIMETRI_X = -124.0                              # iki daire aks 5'e göre simetrik
RES = 2.0
ENGEL = ('YLZ-DUVAR', 'YLZ-KOLON', 'YLZ-PENCERE', 'YLZ-BACA', 'YLZ-HAVALANDIRMA')

_K = None


def kayit():
    global _K
    if _K is None:
        _K = pickle.load(open(FLAT, 'rb'))
    return _K


def win(k, pad=0.0):
    o = OFS[k]
    return (W0[0] + o - pad, W0[1] - pad, W0[2] + o + pad, W0[3] + pad)


def icinde(p, w):
    return w[0] <= p[0] <= w[2] and w[1] <= p[1] <= w[3]


def kat_kayit(k, pad=60):
    w = win(k, pad)
    out = []
    for r in kayit():
        if r[0] in 'LPAH':
            if all(icinde(p, w) for p in r[2]):
                out.append(r)
        elif icinde(r[2], w):
            out.append(r)
    return out


def kolonlar(k):
    ps = []
    for r in kat_kayit(k):
        if r[1] == 'YLZ-KOLON' and r[0] == 'P' and len(r[2]) >= 4:
            p = Polygon(r[2]).buffer(0)
            if p.area > 300:
                ps.append(p)
    return ps


def etiketler(k):
    out = []
    for r in kat_kayit(k):
        if r[0] == 'T' and 'ALAN' in r[3] and r[4] >= 5:
            s = r[3].split('\n')
            ad = s[0].strip()
            m = re.search(r'ALAN\s*:\s*([\d,\.]+)', r[3])
            if not m:
                continue
            out.append(dict(ad=ad, alan=float(m.group(1).replace(',', '.')), p=(r[2][0] + 25, r[2][1] - 12)))
    return out


def maske(k):
    w = win(k, 30)
    W, H = int((w[2] - w[0]) / RES) + 1, int((w[3] - w[1]) / RES) + 1
    img = np.zeros((H, W), np.uint8)

    def px(p):
        return (int(round((p[0] - w[0]) / RES)), int(round((w[3] - p[1]) / RES)))
    for r in kat_kayit(k):
        if r[1] in ENGEL and r[0] in 'LP':
            pts = np.array([px(p) for p in r[2]], np.int32)
            cv2.polylines(img, [pts], False, 255, 2)
        if r[1] == 'YLZ-KOLON' and r[0] in 'PH':
            pts = np.array([px(p) for p in r[2]], np.int32)
            cv2.fillPoly(img, [pts], 255)
        if r[1] == 'YLZ-KAPI' and r[0] == 'A' and len(r[2]) > 3:
            # kapı yayı: merkez = yayın iki ucundan eşit uzaklıktaki menteşe; kapalı konum çizgisi merkez→uçlar
            a, b, m = r[2][0], r[2][-1], r[2][len(r[2]) // 2]
            c = _merkez(a, m, b)
            if c:
                for q in (a, b):
                    cv2.line(img, px(c), px(q), 255, 2)
    return img, w


def _merkez(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return (ux, uy)


def mahaller(k):
    img, w = maske(k)
    H, W = img.shape
    out = []
    for e in etiketler(k):
        # etiket kutusu çizgileri engel değil; tohum etiket noktası çevresinde boş piksel
        sx, sy = int((e['p'][0] - w[0]) / RES), int((w[3] - e['p'][1]) / RES)
        tohum = None
        for r in range(0, 40):
            for dx in range(-r, r + 1):
                for dy in (-r, r):
                    x, y = sx + dx, sy + dy
                    if 0 <= x < W and 0 <= y < H and img[y, x] == 0:
                        tohum = (x, y); break
                if tohum: break
            if tohum: break
        if not tohum:
            continue
        ff = img.copy()
        msk = np.zeros((H + 2, W + 2), np.uint8)
        cv2.floodFill(ff, msk, tohum, 128)
        reg = (ff == 128).astype(np.uint8)
        reg = cv2.dilate(reg, np.ones((3, 3), np.uint8))
        cs, _ = cv2.findContours(reg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cs:
            continue
        c = max(cs, key=cv2.contourArea)
        c = cv2.approxPolyDP(c, 1.5, True)
        pts = [(w[0] + q[0][0] * RES, w[3] - q[0][1] * RES) for q in c]
        if len(pts) < 3:
            continue
        P = Polygon(pts).buffer(0)
        e2 = dict(e, poly=P, alan_olc=P.area / 1e4, kat=k)
        e2['daire'] = None if any(s in e['ad'] for s in ('MERDİVEN', 'KAT HOL', 'ASANSÖR', 'MEKAN')) else \
            ('D1' if P.centroid.x - OFS[k] < SIMETRI_X else 'D2')
        out.append(e2)
    return out


if __name__ == '__main__':
    for k in 'Z12':
        ms = mahaller(k)
        print(k, len(ms), 'kolon', len(kolonlar(k)))
        for m in ms:
            print('  ', m['daire'], m['ad'][:18].ljust(18), m['alan'], round(m['alan_olc'], 2), [round(v) for v in m['poly'].bounds])


# ====================================================================== TİP DAİRE (D1, zemin koordinatı) — mimari okumasından
# Mahal poligonları taşma dolgusundan; hol/çamaşır, mutfak, balkon kapı/tezgâh çizgileri yüzünden elle düzeltildi.
def _tip_mahaller():
    from shapely.geometry import box
    ms = {m['ad']: m for m in mahaller('Z') if m['daire'] == 'D1' and m['alan_olc'] < 30}
    cam = box(-419, -2041, -276, -1935)
    hol = [m for m in mahaller('Z') if m['daire'] == 'D1' and m['ad'] == 'HOL'][0]['poly'].difference(cam.buffer(9, join_style=2))
    if hol.geom_type != 'Polygon':
        hol = max(hol.geoms, key=lambda g: g.area)
    out = []

    def ek(ad, tip, poly, sic, alan, kapi, isit=True):
        out.append(dict(ad=ad, tip=tip, poly=poly, sic=sic, alan=alan, kapi=kapi, isit=isit))
    yat = sorted([m for m in mahaller('Z') if m['daire'] == 'D1' and m['ad'] == 'YATAK ODASI'], key=lambda m: -m['poly'].centroid.y)
    ek('YATAK ODASI', 'oda', yat[0]['poly'], 20, 10.28, (-549, -1983))
    ek('YATAK ODASI', 'oda', yat[1]['poly'], 20, 10.07, (-549, -2093))
    ek('ODA', 'oda', ms['ODA [MKA 11,05 M²]']['poly'], 20, 12.91, (-479, -1923))
    ek('SALON', 'salon', ms['SALON']['poly'], 20, 23.08, (-549, -2463))
    ek('MUTFAK', 'mutfak', box(-539, -2868, -259, -2528), 20, 9.50, (-479, -2528))
    ek('BANYO-WC', 'banyo', ms['BANYO-WC']['poly'] if ms['BANYO-WC']['alan'] > 4 else None, 24, 4.33, (-409, -2298))
    b = [m for m in mahaller('Z') if m['daire'] == 'D1' and m['ad'] == 'BANYO-WC']
    b = sorted(b, key=lambda m: -m['alan'])
    out[-1]['poly'] = b[0]['poly']
    ek('BANYO-WC', 'banyo', b[1]['poly'], 24, 2.60, (-262, -1990))
    ek('HOL', 'hol', hol, 15, 5.49, None, isit=False)
    ek('ÇAMAŞIR ODASI', 'islak', cam, 15, 1.60, (-419, -1990), isit=False)
    ek('BALKON', 'balkon', box(-539, -3043, -254, -2878), -3, 4.67, None, isit=False)
    return out


# armatürler (D1 zemin): tip, x, y, (pis su gider noktası), ek (mimaride çizili değil, kuralla)
TIP_ARMATUR = [
    dict(mahal=5, tip='WC', x=-290, y=-2206, gider=(-276, -2206)),
    dict(mahal=5, tip='DUS', x=-283, y=-2298, gider=(-282, -2298)),
    dict(mahal=5, tip='LV', x=-372, y=-2072, gider=(-372, -2066), ek=True),
    dict(mahal=5, tip='YS', x=-340, y=-2262, gider=(-340, -2262), ek=True),
    dict(mahal=6, tip='WC', x=-164, y=-2108, gider=(-164, -2124)),
    dict(mahal=6, tip='LV', x=-247, y=-1983, gider=(-252, -1983)),
    dict(mahal=8, tip='CM', x=-307, y=-1988, gider=(-282, -1988)),
    dict(mahal=4, tip='EV', x=-290, y=-2670, gider=(-280, -2670)),
    dict(mahal=4, tip='BM', x=-292, y=-2728, gider=(-275, -2728)),
]
# pis su kolonları (D1): ıslak hacim köşesinde, betonarme / M.H. şaftı dışında
TIP_KOLON = {'P1': (-272, -2236), 'P2': (-147, -2121), 'P3': (-268, -2648)}
KOMBI = (-304, -2898)            # mimaride balkonda 'KOMBİ' (duvar dibinde 50x30)
KOMBI_KUTU = (-329, -2913, -279, -2883)
MH_SAFT = [(-294, -2153, -274, -2113)]
DAIRE_KAPI = (-259, -2458)
KOLLEKTOR = (-544, -2300)        # hol sol duvarı (yatak / salon kapıları arasındaki dolu duvar)


def ayna_x(x, k='Z'):
    return 2 * SIMETRI_X - x


def donustur(p, daire, k):
    """D1 zemin noktası -> (daire 'D1'/'D2', kat) noktası"""
    x, y = p
    if daire == 'D2':
        x = ayna_x(x)
    return (x + OFS[k], y)


def donustur_geom(g, daire, k):
    from shapely.affinity import scale, translate
    if daire == 'D2':
        g = scale(g, xfact=-1, yfact=1, origin=(SIMETRI_X, 0))
    return translate(g, OFS[k], 0)


def daire_no(daire, k):
    i = {'Z': 0, '1': 1, '2': 2}[k]
    return 'D%d' % (2 * i + (1 if daire == 'D1' else 2))


def bina_poly(k='Z'):
    """bina dış hattı (balkonlar dahil değil): duvar maskesinde dışarıdan taşma dolgusu, kalan alanın dış zarfı"""
    img, w = maske(k)
    img = cv2.dilate(img, np.ones((5, 5), np.uint8))
    H, W = img.shape
    ff = img.copy()
    msk = np.zeros((H + 2, W + 2), np.uint8)
    cv2.floodFill(ff, msk, (0, 0), 128)
    ic = (ff != 128).astype(np.uint8)
    cs, _ = cv2.findContours(ic, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cs, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, 2.0, True)
    P = Polygon([(w[0] + q[0][0] * RES, w[3] - q[0][1] * RES) for q in c]).buffer(0)
    return P
