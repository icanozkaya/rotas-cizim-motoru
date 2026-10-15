# -*- coding: utf-8 -*-
"""2750/7 A-B blok SIHHİ — mimari model (kat JSON'u + düz mimari kayıtlardan).

Kat JSON'ları (mimari.py) mahal / daire / kapı / betonarme verir; burada eklenenler:
  * armatürler (patlatılmış vitrifiye çizgileri kümelenir, sınıflanır): WC, LV, DUS (duş gideri), EV (eviye),
    OCAK, ABDEST; bağlantı noktası + armatür kutusu + bağlı olduğu duvarın iç normali
  * balkon süzgeci (mimar: rtm-plan katmanı-05 r5/2,5) ve yağmur inişi (B: rtm-plan katmanı-04 r5; A: tasarım)
  * küçük kapalı hücreler (şaft / kablo bacası / ısıtma şaftı) — boru ve kolon yasağı
  * asansör ve enerji odası yasak bölgeleri
Birim cm, mimari koordinatı.
"""
import json
import math
import os
import pickle
import re

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box, MultiPolygon
from shapely.ops import unary_union, nearest_points
from shapely.strtree import STRtree

AB = '/tmp/claude-0/ab'
FL_PKL = AB + '/mim_fl.pkl'
VIT = ('rtm-tefris vitrifiye', 'sbl-tefris vitrifiye')
DUVAR_KATMAN = {'rtm-duv tugla', 'rtm-tas_betonarme', 'rtm-sıva', 'rtm-pen-ahsap', 'rtm-cam', 'rtm-beton',
                'rtm-ylt-sürme', 'sbl-merdiven'}
# kat pafta pencereleri (mimari.py KATLAR ile aynı) + çatı
KATLAR = {
    ('B', 'Z'): (25300, 30210, -27560, -26000, 0.75), ('B', '1'): (31300, 36210, -27560, -26000, 3.75),
    ('B', '2'): (37300, 42210, -27560, -26000, 6.75), ('B', 'C'): (43300, 48210, -27650, -25900, 9.75),
    ('A', 'B'): (16930, 24760, -35300, -32250, -2.20), ('A', 'Z'): (25590, 33410, -35300, -32250, 0.80),
    ('A', '1'): (34245, 42065, -35300, -32250, 3.80), ('A', '2'): (42900, 50720, -35300, -32250, 6.80),
    ('A', 'C'): (51555, 59375, -35400, -32150, 9.80),
}
KAT_DX = {'A': 8655.0, 'B': 6000.0}           # katlar arası x ötelemesi
KAT_SIRA = {'A': ['B', 'Z', '1', '2'], 'B': ['Z', '1', '2']}
KAT_AD = {'B': 'BODRUM KAT', 'Z': 'ZEMİN KAT', '1': '1. KAT', '2': '2. KAT', 'C': 'ÇATI'}

_FL = None


def fl():
    global _FL
    if _FL is None:
        _FL = pickle.load(open(FL_PKL, 'rb'))
    return _FL


def temiz(s):
    s = re.sub(r'\\[A-Za-z][^;]*;', '', s)
    return s.replace('{', '').replace('}', '').replace('\\P', ' ').strip()


def zx(blok, kat):
    """kat penceresinin zemin kata göre x ötelemesi (çatı dahil)"""
    return KATLAR[(blok, kat)][0] - KATLAR[(blok, 'Z')][0]


def icinde(p, w, pad=0):
    return w[0] - pad <= p[0] <= w[1] + pad and w[2] - pad <= p[1] <= w[3] + pad


# ====================================================================== armatür tanıma
def _kumeler(w):
    gs, recs = [], []
    for r in fl():
        if r[1] not in VIT:
            continue
        t, d = r[0], r[2]
        if t == 'C':
            if not icinde(d[:2], w):
                continue
            g = Point(d[0], d[1]).buffer(d[2], 12).exterior
        elif t in 'LP':
            pts = list(d)
            if len(pts) < 2 or not all(icinde(p, w) for p in pts):
                continue
            g = LineString(pts)
        else:
            continue
        gs.append(g)
        recs.append(r)
    if not gs:
        return []
    U = unary_union([g.buffer(1.5, 4) for g in gs])
    parts = list(getattr(U, 'geoms', [U]))
    tr = STRtree(gs)
    out = []
    for p in parts:
        idx = tr.query(p, predicate='intersects')
        cs = [recs[i][2] for i in idx if recs[i][0] == 'C']
        geo = unary_union([gs[i] for i in idx])
        out.append(dict(poly=p, b=p.bounds, cs=cs, geo=geo, n=len(idx)))
    return out


def _uclu_daire(cs, r0, tol=0.25):
    """aynı yarıçaplı (≈r0) üç daire, sıralı (eviye batarya delikleri)"""
    c = [q for q in cs if abs(q[2] - r0) < tol]
    out = []
    used = set()
    for i in range(len(c)):
        for j in range(len(c)):
            for k in range(len(c)):
                if len({i, j, k}) < 3 or i in used or j in used or k in used:
                    continue
                a, b, e = c[i], c[j], c[k]
                d1, d2 = math.dist(a[:2], b[:2]), math.dist(b[:2], e[:2])
                if 6 < d1 < 14 and 6 < d2 < 14 and abs(math.dist(a[:2], e[:2]) - d1 - d2) < 1.0:
                    out.append(((a[0] + b[0] + e[0]) / 3, (a[1] + b[1] + e[1]) / 3))
                    used |= {i, j, k}
    return out


def armaturler_bul(w):
    """-> list dict(tip, p (bağlantı/merkez), kutu (Polygon), ...)"""
    A = []
    for k in _kumeler(w):
        x0, y0, x1, y1 = k['b']
        W, H = x1 - x0, y1 - y0
        cs = k['cs']
        rs = sorted(round(c[2], 1) for c in cs)
        kutu = box(x0, y0, x1, y1)
        # eviye: 3'lü batarya deliği r3,0
        evs = _uclu_daire(cs, 3.0)
        for e in evs:
            A.append(dict(tip='EV', p=e, kutu=box(e[0] - 30, e[1] - 30, e[0] + 30, e[1] + 30), kume=kutu))
        if min(W, H) > 50 and max(W, H) > 250 and len(cs) >= 10:
            # ocaklı tezgâh: ocak = büyük daireler (r>=4,6) merkezi
            br = [c for c in cs if c[2] >= 4.5]
            if br:
                ox = sum(c[0] for c in br) / len(br)
                oy = sum(c[1] for c in br) / len(br)
                A.append(dict(tip='OCAK', p=(ox, oy), kutu=box(ox - 35, oy - 35, ox + 35, oy + 35)))
            A.append(dict(tip='TEZGAH', p=((x0 + x1) / 2, (y0 + y1) / 2), kutu=kutu))
            continue
        if evs:
            continue
        if 35 <= min(W, H) <= 46 and 55 <= max(W, H) <= 66 and rs[:2] == [0.8, 0.8]:
            A.append(dict(tip='WC', p=((x0 + x1) / 2, (y0 + y1) / 2), kutu=kutu))
        elif 45 <= min(W, H) <= 62 and 110 <= max(W, H) <= 160 and 3.6 in rs:
            dr = [c for c in cs if abs(c[2] - 3.6) < 0.2][0]
            A.append(dict(tip='LV', p=(dr[0], dr[1]), kutu=kutu))
        elif max(W, H) <= 14 and 4.2 in rs:
            for c in cs:
                if abs(c[2] - 4.2) < 0.2:
                    A.append(dict(tip='DUS', p=(c[0], c[1]), kutu=Point(c[0], c[1]).buffer(6)))
        elif 30 <= min(W, H) <= 42 and 33 <= max(W, H) <= 45 and len(cs) == 3:     # bodrum WC hücre lavabosu
            dr = max(cs, key=lambda c: c[2])
            A.append(dict(tip='LV', p=(dr[0], dr[1]), kutu=kutu))
        elif 40 <= min(W, H) <= 52 and 44 <= max(W, H) <= 55 and not cs:            # bodrum klozet (alafranga)
            A.append(dict(tip='WC', p=((x0 + x1) / 2, (y0 + y1) / 2), kutu=kutu))
        elif min(W, H) >= 45 and max(W, H) >= 190 and not cs:                     # abdest tezgâhı (bodrum)
            A.append(dict(tip='ABDEST_TEZGAH', p=((x0 + x1) / 2, (y0 + y1) / 2), kutu=kutu))
    # abdest muslukları (bodrum r0,7 tekil) -> tezgâh başına musluk noktaları
    return A


# ====================================================================== kat modeli
class Kat:
    def __init__(self, blok, kat):
        self.blok, self.kat = blok, kat
        w = KATLAR[(blok, kat)]
        self.w = w[:4]
        self.kot = w[4]
        J = json.load(open(f'{AB}/kat_{blok}_{kat}.json'))
        self.J = J
        self.mahal = []
        for m in J['mahaller']:
            g = Polygon(m['poligon']).buffer(0)
            if g.geom_type != 'Polygon':
                g = max(g.geoms, key=lambda q: q.area)
            ad = m['ad'].strip()
            tip = 'diger'
            u = ad.upper()
            if u.startswith('BANYO') or u.startswith('WC') or u.startswith('DUŞ'):
                tip = 'banyo'
            elif 'MUTFAK' in u and 'NİŞ' not in u:
                tip = 'mutfak' if u == 'MUTFAK' else 'salon_mutfak'
            elif u.startswith('HOL'):
                tip = 'hol'
            elif u.startswith('YATAK') or u == 'SALON':
                tip = 'oda'
            self.mahal.append(dict(no=m['no'], ad=ad, poly=g, daire=m['daire'], ortak=m['ortak'], tip=tip,
                                   alan=m['alan_mimari'] or m['alan_cizim'], xy=tuple(m['xy'])))
        self.beton = [Polygon(p) for p in J['betonarme']]
        self.beton_u = unary_union(self.beton)
        self.kapilar = J['kapilar']
        self.daireler = {int(k): v for k, v in J['daireler'].items()}
        self.giris = {int(k): v for k, v in J['daire_giris'].items()}
        self._yazilar()
        self._yasaklar()
        self._armatur()
        self._yagmur()

    # ------------------------------------------------------------------
    def _yazilar(self):
        self.yazilar = []          # (x, y, metin, h, katman) — etiket çakışma engeli
        for r in fl():
            if r[0] == 'T' and icinde(r[2][0], self.w):
                s = temiz(r[2][1])
                if s:
                    self.yazilar.append((r[2][0][0], r[2][0][1], s, r[2][2], r[1]))

    def _yasaklar(self):
        Y = []
        for x, y, s, h, L in self.yazilar:
            u = s.upper()
            if u.startswith('ASANSÖR'):
                Y.append(('asansor', box(x - 105, y - 105, x + 105, y + 105)))
            elif u.startswith('ENERJİ ODASI'):
                Y.append(('enerji', box(x - 70, y - 70, x + 70, y + 70)))
        # mahal poligonu olan enerji odası / asansör
        for m in self.mahal:
            if m['ad'].upper().startswith('ENERJİ') or (m['ad'].upper().startswith('ASANSÖR') and m['poly'].area < 9e4):
                Y.append(('enerji' if 'ENERJ' in m['ad'].upper() else 'asansor', m['poly'].buffer(5)))
        # küçük kapalı hücreler: şaft yazıları (ISITMA ŞAFTI, KABLO BACASI) + izdüşüm daireleri
        self.saft_yazi = [(x, y, s) for x, y, s, h, L in self.yazilar if 'ŞAFT' in s.upper() or 'BACASI' in s.upper()]
        self.yasak = Y
        self.saftlar = self._hucreler()

    def _hucreler(self):
        """duvar çizgileriyle kapalı, mahal olmayan küçük (< 1,6 m²) hücreler = şaft / kablo bacası"""
        import cv2
        from scipy import ndimage as ndi
        x0, x1, y0, y1 = self.w
        RES = 2.0
        Wp, Hp = int((x1 - x0) / RES) + 2, int((y1 - y0) / RES) + 2
        img = np.zeros((Hp, Wp), np.uint8)
        px = lambda p: (int(round((p[0] - x0) / RES)), int(round((y1 - p[1]) / RES)))
        for r in fl():
            if r[1] not in DUVAR_KATMAN:
                continue
            if r[0] == 'L' and (icinde(r[2][0], self.w) or icinde(r[2][1], self.w)):
                cv2.line(img, px(r[2][0]), px(r[2][1]), 255, 2)
            elif r[0] == 'P' and any(icinde(p, self.w) for p in r[2]):
                cv2.polylines(img, [np.array([px(p) for p in r[2]], np.int32)], False, 255, 2)
        for g in self.beton:
            cv2.fillPoly(img, [np.array([px(p) for p in g.exterior.coords], np.int32)], 255)
        lab, n = ndi.label(img == 0)
        areas = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1)) * RES * RES
        out = []
        mahal_u = unary_union([m['poly'] for m in self.mahal])
        for i, a in enumerate(areas, 1):
            if 400 < a < 16000:
                ys, xs = np.where(lab == i)
                g = box(x0 + xs.min() * RES, y1 - ys.max() * RES, x0 + xs.max() * RES, y1 - ys.min() * RES)
                if g.intersection(mahal_u).area > 0.5 * g.area:
                    continue
                # armatür / tezgâh içi değil, yalnız şaft benzeri: kısa kenar ≥ 20
                bx = g.bounds
                if min(bx[2] - bx[0], bx[3] - bx[1]) < 18:
                    continue
                out.append(g)
        return out

    def _armatur(self):
        A = armaturler_bul(self.w)
        polys = [m['poly'] for m in self.mahal]
        tr = STRtree(polys)
        for a in A:
            pt = Point(a['p'])
            i = tr.nearest(pt)
            m = self.mahal[i]
            a['mahal'] = m['no'] if m['poly'].distance(pt) < 30 else None
            a['daire'] = m['daire'] if a['mahal'] is not None else None
            # duvar normali: armatür kutusuna en yakın mahal kenarı
            mm = self.mahal[i]['poly']
            q = nearest_points(mm.exterior, pt)[0]
            dx, dy = pt.x - q.x, pt.y - q.y
            L = math.hypot(dx, dy) or 1
            a['duvar_mesafe'] = L
            a['normal'] = (dx / L, dy / L)       # duvardan içeri
            a['duvar'] = (q.x, q.y)
            a['ek'] = False
        self.armatur = [a for a in A if a['tip'] not in ('TEZGAH',)]
        self.tezgah = [a for a in A if a['tip'] == 'TEZGAH']

    def _yagmur(self):
        x0, x1, y0, y1 = self.w
        self.balkon_suzgec, self.inis_mimari = [], []
        for r in fl():
            if r[0] != 'C' or not icinde(r[2][:2], self.w):
                continue
            if r[1] == 'rtm-plan katmanı-05' and abs(r[2][2] - 5.0) < 0.3:
                self.balkon_suzgec.append((r[2][0], r[2][1]))
            elif r[1] == 'rtm-plan katmanı-04' and abs(r[2][2] - 5.0) < 0.3:
                self.inis_mimari.append((r[2][0], r[2][1]))

    # ------------------------------------------------------------------
    def mahal_no(self, no):
        for m in self.mahal:
            if m['no'] == no:
                return m

    def mahal_at(self, p, tol=5):
        pt = Point(p)
        best = None
        for m in self.mahal:
            d = m['poly'].distance(pt)
            if d <= tol and (best is None or d < best[0]):
                best = (d, m)
        return best[1] if best else None

    def daire_poly(self, no):
        return unary_union([self.mahal_no(i)['poly'] for i in self.daireler[no]])

    def ortak_poly(self):
        return unary_union([m['poly'] for m in self.mahal if m['ortak'] and m['daire'] is None])


_CACHE = {}


def kat(blok, k):
    key = (blok, k)
    if key not in _CACHE:
        pk = f'/tmp/claude-0/sh/kat_{blok}_{k}.pkl'
        if os.path.exists(pk) and os.path.getmtime(pk) > os.path.getmtime(__file__):
            _CACHE[key] = pickle.load(open(pk, 'rb'))
        else:
            K = Kat(blok, k)
            os.makedirs('/tmp/claude-0/sh', exist_ok=True)
            pickle.dump(K, open(pk, 'wb'))
            _CACHE[key] = K
    return _CACHE[key]


if __name__ == '__main__':
    from collections import Counter
    import sihhi_mimari as _M
    for b, ks in KAT_SIRA.items():
        for k in ks:
            K = _M.kat(b, k)
            c = Counter(a['tip'] for a in K.armatur)
            print(b, k, dict(c), 'saft', len(K.saftlar), 'yasak', len(K.yasak), 'balkon', len(K.balkon_suzgec),
                  'inis', len(K.inis_mimari), 'atanmamis', sum(1 for a in K.armatur if a['mahal'] is None))
