# -*- coding: utf-8 -*-
"""2750/7 A-B blok SIHHİ TESİSAT — tasarım (kat modeli, ek armatür, pis su kolonu + ağı, temiz su ağacı,
koridor dağıtımı, sayaç dolabı, balkon süzgeci / yağmur inişi).  Birim cm, mimari koordinatı (her kat kendi penceresinde).

Kullanıcı kurgusu (15.10.2026): merkezi sistem — kazan dairesi + boyler A blok bodrumunda, B blok buradan; 3 borulu sıcak
su (soğuk / sıcak / sirkülasyon, sirkülasyon sayaç dolabında biter); her daire girişinde (koridorda kapı yanı) SAYAÇ
DOLABI (soğuk + sıcak su sayacı); daire içinde sıcak su sayaç dolabından başlar, soğuğa paralel; depo çatıda (hidrofor yok).
"""
import math
import os
import pickle
import sys

import numpy as np
import cv2
from scipy import ndimage as ndi
from shapely.geometry import LineString, Point, Polygon, box, MultiPolygon
from shapely.ops import unary_union, nearest_points

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import sihhi_mimari as M          # noqa: E402
import sihhi_izgara as IZ         # noqa: E402

ONB = '/tmp/claude-0/sh'
RES = 2.0
H = 4.0                            # güzergâh ızgarası (cm)

SB = {'WC': 10, 'DUS': 7, 'CM': 4, 'EV': 4, 'BM': 4, 'LV': 2, 'YS': 2, 'ABD': 2, 'PIS': 0}
# TS 1258 Çizelge 15 (ROTAŞ standardı) — yük birimi (YB): soğuk / sıcak
YB = {'LV': (0.5, 0.5), 'WC': (0.5, 0.0), 'DUS': (1.0, 1.0), 'EV': (0.5, 0.5), 'CM': (1.0, 0.0), 'BM': (1.0, 0.0),
      'ABD': (0.25, 0.0)}
SICAK = {'LV', 'DUS', 'EV'}


def pis_cap(sb, wc=False):
    c = 50 if sb <= 10 else 70 if sb <= 30 else 100 if sb <= 160 else 125 if sb <= 300 else 150
    if wc:
        c = max(c, 100)
    return c


TS_CAP = [(2.25, 'Ø20'), (7.84, 'Ø25'), (19.36, 'Ø32'), (46.24, 'Ø40'), (108.4, 'Ø50'), (256, 'Ø63'), (784, 'Ø75'),
          (1444, 'Ø90'), (4096, 'Ø110')]


def temiz_cap(yb):
    for s, c in TS_CAP:
        if yb <= s + 1e-9:
            return c
    return 'Ø110'


def debi_yb(yb):
    """TS 1258: Q = 0,25·√YB (l/s) (çap tablosu sınırlarıyla uyumlu)"""
    return 0.25 * math.sqrt(max(yb, 0.0))


# ====================================================================== raster / koridor
def raster(blok, kat):
    pk = f'{ONB}/ras_{blok}_{kat}.pkl'
    if not os.path.exists(pk):
        import mimari
        K = mimari.Kat(blok, kat)
        os.makedirs(ONB, exist_ok=True)
        pickle.dump(dict(img=K.img_duvar, acik=K.img_acik, k=K.k, adlar=K.adlar), open(pk, 'wb'))
    return pickle.load(open(pk, 'rb'))


def maske_poligon(mask, x0, y1, res=RES, min_alan=1e4):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cs:
        if len(c) < 3:
            continue
        c = cv2.approxPolyDP(c, 1.0, True)
        if len(c) < 3:
            continue
        g = Polygon([(x0 + q[0][0] * res, y1 - q[0][1] * res) for q in c]).buffer(0)
        if g.area >= min_alan:
            out.append(g)
    return out


def kapi_sektor(d):
    c = d['mentese']
    a1 = math.atan2(d['uc1'][1] - c[1], d['uc1'][0] - c[0])
    a2 = math.atan2(d['uc2'][1] - c[1], d['uc2'][0] - c[0])
    da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
    r = d['r']
    pts = [tuple(c)] + [(c[0] + r * math.cos(a1 + da * i / 12), c[1] + r * math.sin(a1 + da * i / 12)) for i in range(13)]
    return Polygon(pts).buffer(0)


class Kat:
    """bir katın sıhhi modeli (mimari + tasarım)"""

    def __init__(self, blok, kat):
        self.blok, self.kat = blok, kat
        self.K = K = M.kat(blok, kat)
        self.dx = M.zx(blok, kat)
        R = raster(blok, kat)
        self.img = R['img']
        self.x0, self.x1, self.y0, self.y1 = R['k'][2:6]
        self.beton = K.beton_u
        self.kapi_sek = [kapi_sektor(d) for d in K.kapilar]
        self.kapi_u = unary_union(self.kapi_sek)
        self._koridor()
        self._saftlar()
        self._daireler()

    # ------------------------------------------------------------------ koridor / ortak alan
    def _koridor(self):
        K, img = self.K, self.img
        x0, y1 = self.x0, self.y1
        mm = np.zeros(img.shape, np.uint8)
        mo = np.zeros(img.shape, np.uint8)
        px = lambda p: (int(round((p[0] - x0) / RES)), int(round((y1 - p[1]) / RES)))
        for m in K.mahal:
            pts = np.array([px(p) for p in m['poly'].exterior.coords], np.int32)
            cv2.fillPoly(mo if m['ortak'] else mm, [pts], 1)
        self.mm = mm
        solid = ((img > 0) | (mm > 0) | (mo > 0)).astype(np.uint8)
        cl = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))
        fp = ndi.binary_fill_holes(cl)
        self.ayak_izi_m = fp
        fp2 = cv2.erode(fp.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        cand = (img == 0) & (mm == 0) & fp2
        lab, n = ndi.label(cand)
        kenar = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
        best, ba = None, 0
        self.serbest = []          # (poligon, yazılar) daire içi adsız bölgeler adayı
        for i in range(1, n + 1):
            reg = lab == i
            a = reg.sum() * RES * RES / 1e4
            if a < 0.5 or i in kenar:
                continue
            if a > ba:
                best, ba = i, a
            self.serbest.append((i, a))
        kor = (lab == best) if best else np.zeros_like(cand)
        # ortak mahaller (merdiven holü, adsız asansör holü) — asansör kuyusu / enerji odası hariç
        orts = []
        for m in K.mahal:
            if m['ortak'] and not (m['ad'].upper().startswith('ENERJ') or (m['ad'].upper().startswith('ASANSÖR')
                                                                           and m['poly'].area < 9e4)):
                orts.append(m['poly'])
        kp = maske_poligon(kor, x0, y1)
        self.ortak = unary_union(kp + orts).buffer(2).buffer(-2)
        self.kor_lab, self.kor_id = lab, best
        self.yasak_u = unary_union([g for t, g in K.yasak])

    def _saftlar(self):
        """gerçek şaftlar: şaft / baca yazısı içeren küçük hücreler (+ yazısız küçük kapalı hücreler kolon yasağı)"""
        K = self.K
        self.saft = []
        for g0 in K.saftlar:
            g = self._hucre_poligon(g0)
            ad = None
            for x, y, s in K.saft_yazi:
                if g.buffer(25).contains(Point(x, y)):
                    ad = s
            b = g.bounds
            if ad is None and (min(b[2] - b[0], b[3] - b[1]) < 28 or g.area < 1000):
                continue            # duvar boşluğu / bölme arası (şaft değil)
            self.saft.append(dict(poly=g, ad=ad))
        self.saft_u = unary_union([s['poly'] for s in self.saft]) if self.saft else Polygon()
        self.isitma_saft = [s['poly'] for s in self.saft if s['ad'] and 'ISITMA' in s['ad'].upper()]

    def _hucre_poligon(self, g0):
        b = g0.bounds
        c0 = int((b[0] - self.x0) / RES) - 1
        c1 = int((b[2] - self.x0) / RES) + 2
        r0 = int((self.y1 - b[3]) / RES) - 1
        r1 = int((self.y1 - b[1]) / RES) + 2
        sub = self.img[max(r0, 0):r1, max(c0, 0):c1] == 0
        lab, n = ndi.label(sub)
        if n == 0:
            return g0
        i = np.argmax(ndi.sum(sub, lab, index=np.arange(1, n + 1))) + 1
        gs = maske_poligon(lab == i, self.x0 + max(c0, 0) * RES, self.y1 - max(r0, 0) * RES, min_alan=100)
        return max(gs, key=lambda q: q.area).buffer(1) if gs else g0

    # ------------------------------------------------------------------ daireler
    def _daireler(self):
        K = self.K
        self.daire = {}
        for no, idx in K.daireler.items():
            ms = [K.mahal_no(i) for i in idx]
            self.daire[no] = dict(no=no, mahal=ms, poly=unary_union([m['poly'] for m in ms]), giris=K.giris.get(no))
        # adsız serbest bölgeler (hol) -> en yakın daire
        lab = self.kor_lab
        for i, a in self.serbest:
            if i == self.kor_id or a < 0.8:
                continue
            reg = (lab == i)
            gs = maske_poligon(reg, self.x0, self.y1, min_alan=5000)
            if not gs:
                continue
            g = max(gs, key=lambda q: q.area)
            if any(g.buffer(20).contains(Point(x, y)) for x, y, s, h, L in K.yazilar if 'BALKON' in s.upper()):
                continue
            if g.intersection(self.saft_u).area > 0.3 * g.area:
                continue
            if g.buffer(-15).is_empty:
                continue                    # duvar arası ince boşluk
            best, bd = None, 1e9
            for no, D in self.daire.items():
                d = D['poly'].distance(g)
                if d < bd:
                    best, bd = no, d
            if best is not None and bd < 30:
                D = self.daire[best]
                D['mahal'].append(dict(no=-1000 - i, ad='HOL*', poly=g, daire=best, ortak=False, tip='hol', alan=a,
                                       xy=(g.centroid.x, g.centroid.y)))
                D['poly'] = unary_union([D['poly'], g])

    def __getstate__(self):
        d = dict(self.__dict__)
        d.pop('_ort8', None)
        d.pop('_kapi5', None)
        return d

    # ------------------------------------------------------------------ yardımcı
    def mahal_tip(self, p):
        for D in self.daire.values():
            for m in D['mahal']:
                if m['poly'].buffer(1).contains(Point(p)):
                    return m
        return None


# ====================================================================== armatürler
def _armatur_kayit(a, room):
    tip = a['tip']
    n = a['normal']
    t = (-n[1], n[0])
    p = a['p']
    w = a['duvar']
    rec = dict(tip=tip, p=tuple(p), kutu=a['kutu'], n=n, w=tuple(w), ek=False)
    if tip == 'WC':
        rec['gider'] = (w[0] + n[0] * 16, w[1] + n[1] * 16)
        rec['musluk'] = (w[0] + n[0] * 6 + t[0] * 14, w[1] + n[1] * 6 + t[1] * 14)
    elif tip in ('LV', 'EV'):
        rec['gider'] = (w[0] + n[0] * 12, w[1] + n[1] * 12)
        rec['musluk'] = (w[0] + n[0] * 6, w[1] + n[1] * 6)
    elif tip == 'DUS':
        rec['gider'] = tuple(p)
        rec['musluk'] = (w[0] + n[0] * 6, w[1] + n[1] * 6)
    return rec


def _duvar_kenarlari(poly):
    g = poly.simplify(3)
    c = list(g.exterior.coords)
    # saat yönünün tersine çevir
    if Polygon(c).exterior.is_ccw is False:
        c = c[::-1]
    out = []
    for a, b in zip(c[:-1], c[1:]):
        L = math.dist(a, b)
        if L < 30:
            continue
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        n = (-u[1], u[0])                 # içe normal (ccw)
        out.append((a, b, u, n, L))
    return out


def makine_yeri(poly, engel, dus_bolge, boyut=60, tercih=None, pay=6):
    """duvara yaslı boyut x boyut makine kutusu: poligon içinde, engellere değmez. tercih: yakın olması istenen nokta"""
    adaylar = []
    for a, b, u, n, L in _duvar_kenarlari(poly):
        s = boyut / 2 + pay
        while s <= L - boyut / 2 - pay:
            cx = a[0] + u[0] * s + n[0] * (boyut / 2 + 3)
            cy = a[1] + u[1] * s + n[1] * (boyut / 2 + 3)
            k = box(cx - boyut / 2, cy - boyut / 2, cx + boyut / 2, cy + boyut / 2)
            if poly.buffer(1).contains(k) and not k.intersects(engel) and not k.intersects(dus_bolge):
                d = math.dist((cx, cy), tercih) if tercih else 0
                adaylar.append((d, (cx, cy), k, n, (a[0] + u[0] * s, a[1] + u[1] * s)))
            s += 5
    if not adaylar:
        return None
    adaylar.sort(key=lambda q: q[0])
    return adaylar[0]


def islak_hacimler(F):
    """F.daire[no]['islak'] = [dict(tip='banyo'|'mutfak', mahal, poly, armatur=[...])]"""
    K = F.K
    for no, D in F.daire.items():
        D['islak'] = []
        for m in D['mahal']:
            arm = [a for a in K.armatur if a['mahal'] == m['no'] and a['tip'] in ('WC', 'LV', 'DUS', 'EV')]
            if m['tip'] == 'banyo':
                if m.get('alan') and m['poly'].area / 1e4 > 1.2 * m['alan'] and arm:
                    _banyo_kirp(F, D, m, arm)
                fx = [_armatur_kayit(a, m) for a in arm if a['tip'] in ('WC', 'LV', 'DUS')]
                D['islak'].append(dict(tip='banyo', mahal=m, poly=m['poly'], armatur=fx, daire=no))
            elif any(a['tip'] == 'EV' for a in arm):
                fx = [_armatur_kayit(a, m) for a in arm if a['tip'] == 'EV']
                ocak = [a for a in K.armatur if a['mahal'] == m['no'] and a['tip'] == 'OCAK']
                tez = [t for t in K.tezgah if t['kutu'].buffer(5).contains(Point(fx[0]['p']))]
                D['islak'].append(dict(tip='mutfak', mahal=m, poly=m['poly'], armatur=fx, daire=no,
                                       ocak=[o['kutu'] for o in ocak], tezgah=tez[0]['kutu'] if tez else None))
        ek_armatur(F, D)


def _banyo_kirp(F, D, m, arm):
    """mimar holü banyoyla tek mahal çizmiş (kapı tanınmamış): armatür kutusundan mimari m²'ye kadar büyüyen dikdörtgen
    banyo kalır, artan bölüm hol olur"""
    P = m['poly']
    x0, y0, x1, y1 = unary_union([a['kutu'] for a in arm]).bounds
    hedef = m['alan'] * 1e4 * 1.04
    adim = 2.0
    for _ in range(400):
        best = None
        for dx0, dy0, dx1, dy1 in ((-adim, 0, 0, 0), (0, -adim, 0, 0), (0, 0, adim, 0), (0, 0, 0, adim)):
            b = box(x0 + dx0, y0 + dy0, x1 + dx1, y1 + dy1)
            yeni = b.difference(box(x0, y0, x1, y1))
            if P.buffer(1).contains(yeni):
                if best is None:
                    best = (dx0, dy0, dx1, dy1)
        if best is None or (x1 - x0) * (y1 - y0) >= hedef:
            break
        # en çok duvara kadar: dört yön sırayla
        moved = False
        for dx0, dy0, dx1, dy1 in ((-adim, 0, 0, 0), (0, -adim, 0, 0), (0, 0, adim, 0), (0, 0, 0, adim)):
            b = box(x0 + dx0, y0 + dy0, x1 + dx1, y1 + dy1)
            if P.buffer(1).contains(b) and (b.area <= hedef):
                x0, y0, x1, y1 = x0 + dx0, y0 + dy0, x1 + dx1, y1 + dy1
                moved = True
        if not moved:
            break
    yeni = box(x0, y0, x1, y1).intersection(P)
    kalan = P.difference(yeni.buffer(2))
    m['poly'] = yeni
    m['kirpildi'] = True
    for g in getattr(kalan, 'geoms', [kalan]):
        if g.area > 5000 and not g.buffer(-15).is_empty:
            D['mahal'].append(dict(no=-2000 - len(D['mahal']), ad='HOL*', poly=g, daire=D['no'], ortak=False, tip='hol',
                                   alan=g.area / 1e4, xy=(g.centroid.x, g.centroid.y)))


def ek_armatur(F, D):
    """mutfağa bulaşık makinesi (banyo ÇM + yer süzgeci kolon seçiminden sonra: banyo_ek)"""
    for W in D['islak']:
        if W['tip'] == 'banyo':
            dus = [a for a in W['armatur'] if a['tip'] == 'DUS']
            W['dus_bolge'] = unary_union([Point(a['p']).buffer(55) for a in dus]) if dus else Polygon()
            continue
        _ek(F, W, None)


def banyo_ek(F, W, kolon, cm=True):
    _ek(F, W, kolon, cm)


def _ek(F, W, kolon, cm=True):
    if True:
        poly = W['poly']
        kut = unary_union([a['kutu'].buffer(4) for a in W['armatur']] + [F.kapi_u.buffer(3)])
        dus = [a for a in W['armatur'] if a['tip'] == 'DUS']
        dus_b = unary_union([Point(a['p']).buffer(55) for a in dus]) if dus else Polygon()
        W['dus_bolge'] = dus_b
        if W['tip'] == 'banyo':
            lv = [a for a in W['armatur'] if a['tip'] == 'LV']
            r = None if not cm else makine_yeri(poly, kut.union(F.beton.buffer(2)).union(Point(kolon).buffer(14)), dus_b, 60, tercih=kolon)
            if cm and r is None:       # ikinci deneme: duş bölgesi daraltılmış, kapı kanadı payı küçük
                kutk = unary_union([a['kutu'].buffer(2) for a in W['armatur']] + [F.kapi_u])
                dus2 = unary_union([Point(a['p']).buffer(30) for a in dus]) if dus else Polygon()
                r = makine_yeri(poly, kutk.union(F.beton.buffer(2)).union(Point(kolon).buffer(12)), dus2, 60,
                                tercih=kolon, pay=2)
            if r:
                d, c, k, n, w = r
                W['armatur'].append(dict(tip='CM', p=c, kutu=k, n=n, w=w, ek=True,
                                         gider=(w[0] + n[0] * 12, w[1] + n[1] * 12),
                                         musluk=(w[0] + n[0] * 6 + (n[1]) * 18, w[1] + n[1] * 6 - n[0] * 18)))
            elif cm:
                W['cm_yok'] = True
            # yer süzgeci: duvar dibinden 20 cm, armatürlere / kapıya / duşa değmeyen, banyo ortasına yakın
            kut2 = unary_union([a['kutu'].buffer(8) for a in W['armatur']] + [F.kapi_u.buffer(5), Point(kolon).buffer(30)])
            ic = poly.buffer(-18)
            best = None
            cen = poly.centroid
            if not ic.is_empty:
                bx = ic.bounds
                for x in np.arange(bx[0], bx[2] + 1, 4):
                    for y in np.arange(bx[1], bx[3] + 1, 4):
                        q = Point(x, y)
                        if not ic.contains(q) or kut2.contains(q) or dus_b.buffer(-10).contains(q):
                            continue
                        dd = poly.exterior.distance(q)
                        sk = abs(dd - 22) * 3 + q.distance(Point(kolon)) * 0.5
                        if best is None or sk < best[0]:
                            best = (sk, (x, y))
            if best:
                c = best[1]
                W['armatur'].append(dict(tip='YS', p=c, kutu=Point(c).buffer(8), n=(0, 0), w=c, ek=True, gider=c))
            else:
                W['ys_yok'] = True
        else:
            ev = [a for a in W['armatur'] if a['tip'] == 'EV'][0]
            n = ev['n']
            t = (-n[1], n[0])
            ocak = unary_union(W.get('ocak') or [Polygon()])
            yer = None
            for off in range(62, 300, 6):
                for s in (1, -1):
                    c = (ev['w'][0] + t[0] * s * off + n[0] * 33, ev['w'][1] + t[1] * s * off + n[1] * 33)
                    k = box(c[0] - 30, c[1] - 30, c[0] + 30, c[1] + 30)
                    from shapely.affinity import rotate
                    if not W['poly'].buffer(3).contains(k) or k.intersects(ocak.buffer(-1)) or \
                            k.intersects(ev['kutu'].buffer(-2)) or k.intersects(F.beton) or k.intersects(F.kapi_u):
                        continue
                    yer = (off, s, c, k)
                    break
                if yer:
                    break
            if yer:
                off, s, c, k = yer
                w = (ev['w'][0] + t[0] * s * off, ev['w'][1] + t[1] * s * off)
                W['armatur'].append(dict(tip='BM', p=c, kutu=k, n=n, w=w, ek=True,
                                         gider=(w[0] + n[0] * 12, w[1] + n[1] * 12),
                                         musluk=(w[0] + n[0] * 6 - t[0] * s * 12, w[1] + n[1] * 6 - t[1] * s * 12)))
                W['bm_yon'] = s
            else:
                eng = unary_union([a['kutu'].buffer(3) for a in W['armatur']] + [ocak.buffer(3), F.kapi_u.buffer(3),
                                                                                    F.beton.buffer(2)])
                r = makine_yeri(W['poly'], eng, Polygon(), 60, tercih=ev['p'])
                if r and r[0] < 400:
                    d, c, k, nn, w = r
                    tt = (-nn[1], nn[0])
                    W['armatur'].append(dict(tip='BM', p=c, kutu=k, n=nn, w=w, ek=True,
                                             gider=(w[0] + nn[0] * 12, w[1] + nn[1] * 12),
                                             musluk=(w[0] + nn[0] * 6 + tt[0] * 12, w[1] + nn[1] * 6 + tt[1] * 12)))
                else:
                    W['bm_yok'] = True


# ====================================================================== pis su kolonu
def kolon_adaylari(F, W):
    poly = W['poly']
    g = poly.simplify(3)
    c = list(g.exterior.coords)[:-1]
    ad = []
    n = len(c)
    for i in range(n):
        a, b, d = c[i - 1], c[i], c[(i + 1) % n]
        u1 = (a[0] - b[0], a[1] - b[1])
        u2 = (d[0] - b[0], d[1] - b[1])
        l1, l2 = math.hypot(*u1), math.hypot(*u2)
        if l1 < 20 or l2 < 20:
            continue
        u1 = (u1[0] / l1, u1[1] / l1)
        u2 = (u2[0] / l2, u2[1] / l2)
        for o in (12, 16, 22):
            p = (b[0] + (u1[0] + u2[0]) * o, b[1] + (u1[1] + u2[1]) * o)
            if poly.contains(Point(p)):
                ad.append(p)
                break
    # şaft / koridor duvarı boyunca noktalar (12 cm içeride)
    for a, b, u, nn, L in _duvar_kenarlari(poly):
        s = 15
        while s < L - 15:
            p = (a[0] + u[0] * s + nn[0] * 12, a[1] + u[1] * s + nn[1] * 12)
            q = Point(p)
            if (F.isitma_saft and min(sp.distance(q) for sp in F.isitma_saft) < 30) or F.ortak.distance(q) < 30:
                ad.append(p)
            s += 10
    return ad


def kolon_gecerli(F, p, W=None, r=12):
    q = Point(p)
    if F.beton.distance(q) < r or F.saft_u.distance(q) < 3 or F.yasak_u.distance(q) < r:
        return False
    if W is not None:
        if not W['poly'].buffer(-6).contains(q):
            return False
        for a in W['armatur']:
            if a['tip'] in ('WC', 'LV', 'CM', 'BM') and a['kutu'].distance(q) < 6:
                return False
    if F.kapi_u.buffer(4).contains(q):
        return False
    return True


def kolon_sec(F, W, diger_katlar=()):
    best = None
    for p in kolon_adaylari(F, W):
        if not kolon_gecerli(F, p, W):
            continue
        ok = True
        for G in diger_katlar:
            pp = (p[0] + G.dx - F.dx, p[1])
            q2 = Point(pp)
            if G.beton.distance(q2) < 12 or G.saft_u.distance(q2) < 3 or G.yasak_u.distance(q2) < 12:
                ok = False
        if not ok:
            continue
        q = Point(p)
        hat, sk = pis_ag(W, K=p)
        if F.isitma_saft and min(sp.distance(q) for sp in F.isitma_saft) < 30:
            sk -= 80
        if F.ortak.distance(q) < 30:
            sk -= 40
        if W.get('dus_bolge') is not None and W['dus_bolge'].buffer(-25).contains(q):
            sk += 60
        if best is None or sk < best[0]:
            best = (sk, p)
    return best[1] if best else None


def mutfak_kolon(F, W):
    ev = [a for a in W['armatur'] if a['tip'] == 'EV'][0]
    bm = [a for a in W['armatur'] if a['tip'] == 'BM']
    n = ev['n']
    t = (-n[1], n[0])
    s = W.get('bm_yon', 1)
    for off in (31, 25, 37, 20, 45, -31, -40, 55, 65):
        p = (ev['w'][0] + t[0] * s * off + n[0] * 9, ev['w'][1] + t[1] * s * off + n[1] * 9)
        if kolon_gecerli(F, p, None, r=11) and W['poly'].buffer(2).contains(Point(p)) and \
                not any(a['kutu'].buffer(-3).contains(Point(p)) for a in W['armatur']):
            return p
    return None


# ====================================================================== pis su ağı (duvar dibi kollar + 45° branşman)
from shapely.ops import substring


def halka(poly, ofs=12):
    g = poly.simplify(3).buffer(-ofs, join_style=2)
    if g.is_empty:
        return None
    if g.geom_type != 'Polygon':
        g = max(g.geoms, key=lambda q: q.area)
    r = LineString(list(g.exterior.coords))
    return r


def _yay(r, s0, s1):
    """halka üzerinde s0'dan s1'e (artan yön, sarmalı) parça noktaları"""
    L = r.length
    s0 %= L
    s1 %= L
    if s1 >= s0:
        g = substring(r, s0, s1)
        return list(g.coords) if g.geom_type == 'LineString' else [g.coords[0]]
    a = substring(r, s0, L)
    b = substring(r, 0, s1)
    return list(a.coords) + list(b.coords)[1:]


def _pah(pts, k=8.0):
    """köşelerde 45° pah (k cm)"""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        l1, l2 = math.dist(a, b), math.dist(b, c)
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        kk = min(k, l1 / 2.2, l2 / 2.2)
        u1 = ((b[0] - a[0]) / l1, (b[1] - a[1]) / l1)
        u2 = ((c[0] - b[0]) / l2, (c[1] - b[1]) / l2)
        if abs(u1[0] * u2[1] - u1[1] * u2[0]) < 0.05:
            out.append(b)
            continue
        out.append((b[0] - u1[0] * kk, b[1] - u1[1] * kk))
        out.append((b[0] + u2[0] * kk, b[1] + u2[1] * kk))
    out.append(pts[-1])
    return out


def pis_ag(W, K=None, cizme=False):
    """W['kolon'] (ya da K) noktasından duvar dibi halka boyunca kollar; armatürler dik + 45° branşmanla bağlanır.
    -> hatlar [dict(yol, sb, cap, tur)], toplam ağırlıklı boy W['pis_boy']"""
    K = K or W['kolon']
    pts = [a for a in W['armatur'] if 'gider' in a]
    r = halka(W['poly'], 12)
    if r is None or not pts:
        return [], 1e9
    L = r.length
    s0 = r.project(Point(K))
    kol = {1: [], -1: []}
    br = []
    for a in pts:
        g = Point(a['gider'])
        sf = r.project(g)
        dp = (sf - s0) % L
        dm = (s0 - sf) % L
        yon = 1 if dp <= dm else -1
        d_arc = dp if yon == 1 else dm
        Q = r.interpolate(sf)
        dperp = g.distance(Q)
        kol[yon].append((d_arc, a, sf, dperp))
    hatlar = []
    boy = 0.0
    for yon, lst in kol.items():
        if not lst:
            continue
        lst.sort(key=lambda q: q[0])
        dmax = lst[-1][0]
        # düğümler (kol üzerindeki branşman birleşimleri): yay mesafesi
        dug = []
        for d_arc, a, sf, dperp in lst:
            g = a['gider']
            if d_arc >= dmax - 0.5 and a is lst[-1][1]:
                # en uzak armatür: kol onun izdüşümünde biter, armatüre dik iniş
                dug.append((dmax, a, dperp))
                continue
            dj = max(d_arc - min(max(dperp, 3), 5), 14)
            dug.append((dj, a, dperp))
        ts = sorted(set([10.0] + [round(d, 2) for d, a, p in dug if d > 10.5] + [max(dmax, 10.5)]))
        for t0, t1 in zip(ts[:-1], ts[1:]):
            if t1 - t0 < 0.3:
                continue
            s_a = s0 + yon * t0
            s_b = s0 + yon * t1
            pp = _yay(r, s_a, s_b) if yon == 1 else _yay(r, s_b, s_a)[::-1]
            ust = [a for d, a, p in dug if d >= t1 - 0.01]
            sb = sum(SB[a['tip']] for a in ust)
            wc = any(a['tip'] == 'WC' for a in ust)
            hatlar.append(dict(yol=pp[::-1], sb=sb, cap=pis_cap(sb, wc), tur='omurga'))
            boy += (t1 - t0) * (1 + sb / 10)
        for dj, a, dperp in dug:
            g = a['gider']
            sj = s0 + yon * dj
            J = r.interpolate(sj % L)
            sf = r.project(Point(g))
            Q = r.interpolate(sf)
            if dperp > 6 and abs(dj - (dmax if a is lst[-1][1] else dj)) < 1e-9 and a is lst[-1][1]:
                yol = [g, (Q.x, Q.y)]
            elif dperp > 6:
                nx_, ny_ = (g[0] - Q.x) / dperp, (g[1] - Q.y) / dperp
                P1 = (Q.x + nx_ * 5, Q.y + ny_ * 5)
                yol = [g, P1, (J.x, J.y)]
            else:
                yol = [g, (J.x, J.y)]
            if math.dist(yol[0], yol[-1]) < 0.5:
                continue
            sb = SB[a['tip']]
            hatlar.append(dict(yol=yol, sb=sb, cap=pis_cap(sb, a['tip'] == 'WC'), tur='brans', arm=a['tip']))
            boy += sum(math.dist(p, q) for p, q in zip(yol[:-1], yol[1:])) * (1 + sb / 10)
    # en uzak armatürün dik inişi kolun ucuna bağlanır (yukarıda); omurga köşe pahları
    for h in hatlar:
        if h['tur'] == 'omurga':
            h['yol'] = _pah(h['yol'], 8)
    W['pis_sb'] = sum(SB[a['tip']] for a in pts)
    return hatlar, boy


# ====================================================================== temiz su: ızgara katmanları
def maske(G, geoms, buf=0.0):
    m = np.zeros((G.ny, G.nx), np.uint8)
    for g in geoms:
        if buf:
            g = g.buffer(buf)
        for q in getattr(g, 'geoms', [g]):
            if q.is_empty or q.geom_type != 'Polygon':
                continue
            pts = np.array([[(x - G.x0) / H, (y - G.y0) / H] for x, y in q.exterior.coords], np.int32)
            cv2.fillPoly(m, [pts], 1)
            for hole in q.interiors:
                pts = np.array([[(x - G.x0) / H, (y - G.y0) / H] for x, y in hole.coords], np.int32)
                cv2.fillPoly(m, [pts], 0)
    return m > 0

def _izgara_katmanlari(F):
    """F.G (Izgara 4 cm) + hücre maskeleri"""
    if getattr(F, 'G', None) is not None:
        return
    G = IZ.Izgara.kutu(F.x0, F.y0, F.x1, F.y1, H)
    ny, nx = G.ny, G.nx
    ix = np.arange(nx)
    iy = np.arange(ny)
    cols = np.clip(((G.x0 + ix * H - F.x0) / RES).astype(int), 0, F.img.shape[1] - 2)
    rows = np.clip(((F.y1 - (G.y0 + iy * H)) / RES).astype(int), 0, F.img.shape[0] - 2)
    R = raster(F.blok, F.kat)
    def ornek(im):
        a = im[rows][:, cols] > 0
        b = im[rows + 1][:, cols] > 0
        c = im[rows][:, cols + 1] > 0
        d = im[rows + 1][:, cols + 1] > 0
        return a | b | c | d
    F.duvar4 = ornek(F.img)
    F.acik4 = ornek(R['acik'])
    F.G = G

    poly_mask = lambda geoms, buf=0.0: maske(G, geoms, buf)
    F.beton4 = poly_mask([F.beton], 3)
    F.saft4 = poly_mask([F.saft_u], 1)
    F.yasak4 = poly_mask([F.yasak_u], 2)
    F.ortak4 = poly_mask([F.ortak])
    # kapı açıklıkları (kapalı kanat konumu) — yasak şerit
    F.kapi_acik = []
    m = np.zeros((ny, nx), np.uint8)
    m2 = np.zeros((ny, nx), np.uint8)
    girisler = [tuple(g['mentese']) for g in F.K.giris.values() if g]
    acik = R['acik']
    for d in F.K.kapilar:
        c = d['mentese']
        best = None
        for u in (d['uc1'], d['uc2']):
            v = (u[0] - c[0], u[1] - c[1])
            L = math.hypot(*v) or 1
            v = (v[0] / L, v[1] / L)
            say = 0
            for s in range(12, 42, 3):
                p = (c[0] - v[0] * s, c[1] - v[1] * s)
                cc = int((p[0] - F.x0) / RES)
                rr = int((F.y1 - p[1]) / RES)
                if 0 <= rr < acik.shape[0] and 0 <= cc < acik.shape[1] and acik[max(rr - 1, 0):rr + 2, max(cc - 1, 0):cc + 2].any():
                    say += 1
            if best is None or say > best[0]:
                best = (say, u)
        u = best[1]
        F.kapi_acik.append((tuple(c), tuple(u)))
        p0 = ((c[0] - G.x0) / H, (c[1] - G.y0) / H)
        p1 = ((u[0] - G.x0) / H, (u[1] - G.y0) / H)
        cv2.line(m, (int(round(p0[0])), int(round(p0[1]))), (int(round(p1[0])), int(round(p1[1]))), 1, 4)
        if any(math.dist(c, q) < 1 for q in girisler) or F.ortak.distance(Point(c)) < 30:
            cv2.line(m2, (int(round(p0[0])), int(round(p0[1]))), (int(round(p1[0])), int(round(p1[1]))), 1, 4)
    F.kapi4 = m > 0
    F.kapi4_giris = m2 > 0
    # duvara uzaklık (serbest hücrelerde, cm)
    serbest = ~F.duvar4
    F.dduvar = ndi.distance_transform_edt(serbest) * H


# ====================================================================== sayaç dolabı
def sayac_dolabi(F, no):
    """daire giriş kapısının yanında, koridor tarafında duvara gömme dolap. -> dict(c, kutu, n (koridora), giris (daire içi))"""
    _izgara_katmanlari(F)
    D = F.daire[no]
    g = D['giris']
    if not g:
        return None
    c = tuple(g['mentese'])
    # kapalı kanat ucu
    u = None
    for cc, uu in F.kapi_acik:
        if math.dist(cc, c) < 1:
            u = uu
    if u is None:
        u = g['uc2']
    # giriş kapısında kapalı kanat: bir yanı ortak alan, öbür yanı daire olmalı
    for uu in (u, tuple(g['uc1']), tuple(g['uc2'])):
        vv = (uu[0] - c[0], uu[1] - c[1])
        LL = math.hypot(*vv) or 1
        nn_ = (-vv[1] / LL, vv[0] / LL)
        mm_ = ((c[0] + uu[0]) / 2, (c[1] + uu[1]) / 2)
        a1 = Point(mm_[0] + nn_[0] * 30, mm_[1] + nn_[1] * 30)
        a2 = Point(mm_[0] - nn_[0] * 30, mm_[1] - nn_[1] * 30)
        o1, o2 = F.ortak.contains(a1), F.ortak.contains(a2)
        d1, d2 = D['poly'].buffer(3).contains(a1), D['poly'].buffer(3).contains(a2)
        if (o1 and d2) or (o2 and d1):
            u = uu
            break
    v = (u[0] - c[0], u[1] - c[1])
    L = math.hypot(*v) or 1
    v = (v[0] / L, v[1] / L)
    n = (-v[1], v[0])
    mid = ((c[0] + u[0]) / 2, (c[1] + u[1]) / 2)
    if F.ortak.distance(Point(mid[0] + n[0] * 30, mid[1] + n[1] * 30)) > F.ortak.distance(Point(mid[0] - n[0] * 30, mid[1] - n[1] * 30)):
        n = (-n[0], -n[1])
    # duvar yüzü: kanat çizgisinden koridora doğru ilk serbest ortak nokta
    face = 6
    for s in range(2, 40, 2):
        p = (mid[0] + n[0] * s, mid[1] + n[1] * s)
        if F.ortak.buffer(-1).contains(Point(p)):
            face = s
            break
    W_, D_ = 60.0, 20.0
    adaylar = []
    for yan, base, sgn in (('mentese', c, -1), ('uc', u, 1)):
        for ek in (14, 24, 40, 60):
            cx = base[0] + v[0] * sgn * (ek + W_ / 2) + n[0] * (face + D_ / 2 - 4)
            cy = base[1] + v[1] * sgn * (ek + W_ / 2) + n[1] * (face + D_ / 2 - 4)
            k = Polygon([(cx + v[0] * W_ / 2 + n[0] * D_ / 2, cy + v[1] * W_ / 2 + n[1] * D_ / 2),
                         (cx - v[0] * W_ / 2 + n[0] * D_ / 2, cy - v[1] * W_ / 2 + n[1] * D_ / 2),
                         (cx - v[0] * W_ / 2 - n[0] * D_ / 2, cy - v[1] * W_ / 2 - n[1] * D_ / 2),
                         (cx + v[0] * W_ / 2 - n[0] * D_ / 2, cy + v[1] * W_ / 2 - n[1] * D_ / 2)])
            if k.intersects(F.beton.buffer(2)) or k.intersects(F.saft_u) or k.intersects(F.yasak_u):
                continue
            if any(k.intersects(sk) for sk in F.kapi_sek if sk.distance(Point(c)) > 5) or F.ortak.distance(k.centroid) > 30 or k.intersection(D['poly']).area > 0.2 * k.area:
                continue
            # daire içi karşılığı (duvarın arkası) daire poligonunda olmalı
            arka = (cx - n[0] * (face + D_ / 2 + 14), cy - n[1] * (face + D_ / 2 + 14))
            adaylar.append((ek + (0 if yan == 'mentese' else 5), dict(c=(cx, cy), kutu=k, n=n, v=v, yan=yan, arka=arka,
                                                                       kapi=c, face=face)))
    if not adaylar:
        return None
    adaylar.sort(key=lambda q: q[0])
    return adaylar[0][1]


# ====================================================================== temiz su: daire içi ağaç
def _agac_zincirleri(kenarlar, kok, uclar):
    """kenarlar: set((a,b)) hücre çiftleri (yönsüz). -> (ebeveyn dict, zincirler [[hücre...]] kökten uca doğru)"""
    adj = {}
    for a, b in kenarlar:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    par = {kok: None}
    sira = [kok]
    i = 0
    while i < len(sira):
        a = sira[i]
        i += 1
        for b in adj.get(a, ()):
            if b not in par:
                par[b] = a
                sira.append(b)
    cocuk = {}
    for b, a in par.items():
        if a is not None:
            cocuk.setdefault(a, []).append(b)
    kirik = set(uclar) | {kok}
    for a, cs in cocuk.items():
        if len(cs) != 1:
            kirik.add(a)
    zin = []
    yigin = [kok]
    while yigin:
        a = yigin.pop()
        for b in cocuk.get(a, []):
            z = [a, b]
            while b not in kirik and len(cocuk.get(b, [])) == 1:
                b = cocuk[b][0]
                z.append(b)
            zin.append(z)
            yigin.append(b)
    return par, cocuk, zin


def daire_maliyet(F, no, kaynak_xy):
    _izgara_katmanlari(F)
    G = F.G
    D = F.daire[no]
    cost = np.full((G.ny, G.nx), np.inf)
    merkez = 1.0 + 6.0 * np.exp(-F.dduvar / 20.0)
    izin = np.zeros((G.ny, G.nx), bool)
    for m in D['mahal']:
        if m['tip'] in ('hol', 'banyo', 'mutfak'):
            izin |= maske(G, [m['poly']], 1)
    cost[izin] = merkez[izin]
    # odalar: yalnız zorunluysa (ebeveyn banyosu), duvara yakın şeritte, çok pahalı
    for m in D['mahal']:
        if m['tip'] == 'oda':
            om = maske(G, [m['poly']], 1) & (F.dduvar < 30) & ~np.isfinite(cost)
            cost[om] = 18.0
    # salonun dar (hol benzeri) kısımları: mimar holü salonla birlikte çizmiş -> 90 cm açılmada kalmayan bölge
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (45, 45))
    for m in D['mahal']:
        if m['tip'] in ('oda', 'salon_mutfak') and m['ad'].upper().startswith('SALON'):
            sm = maske(G, [m['poly']], 1)
            gen = cv2.morphologyEx(sm.astype(np.uint8), cv2.MORPH_OPEN, disk) > 0
            dar = sm & ~cv2.dilate(gen.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            cost[dar] = 1.5 * merkez[dar]
    # salon-mutfak: tezgâh / armatür bandı ucuz, salonun geri kalanı pahalı (yalnız gerekirse, duvara yakın)
    for W in D['islak']:
        if W['tip'] == 'mutfak' and W['mahal']['tip'] == 'salon_mutfak':
            sm = maske(G, [W['poly']], 1)
            uz = np.where(F.dduvar < 45, 6.0, 14.0)
            cost[sm] = (uz * merkez)[sm]
            band = unary_union([a['kutu'] for a in W['armatur']] + (W.get('ocak') or []) +
                               ([W['tezgah']] if W.get('tezgah') else [])).buffer(70).intersection(W['poly'])
            bm = maske(G, [band])
            cost[bm] = 2.0 * merkez[bm]
    # duvarlar: dairenin 25 cm çevresinde geçilebilir (delik), pahalı
    dbuf = maske(G, [D['poly']], 22)
    dv = F.duvar4 & dbuf
    cost[dv] = 60.0
    # kaynak (sayaç dolabı) çevresi koridor
    kd = maske(G, [Point(kaynak_xy).buffer(30)])
    cost[kd & ~F.duvar4] = 3.0
    cost[kd & F.duvar4] = 60.0
    # yasaklar
    cost[F.kapi4 & np.isfinite(cost)] = 45.0
    cost[F.beton4 | F.saft4 | F.yasak4 | F.kapi4_giris] = np.inf
    return cost


def daire_temiz(F, no):
    """sayaç dolabından daire içi armatürlere soğuk ağacı (sıcak = sıcak armatürlere giden alt ağaç, +5/+5 öteleme)"""
    _izgara_katmanlari(F)
    G = F.G
    D = F.daire[no]
    dol = F.dol.get(no)
    if dol is None:
        return dict(hata='dolap yok')
    src_xy = dol['c']
    cost = daire_maliyet(F, no, src_xy)
    kok = G.hucre(src_xy)
    cost[kok[1], kok[0]] = 1.0
    musluklar = []
    for W in D['islak']:
        for a in W['armatur']:
            if a['tip'] in YB and 'musluk' in a:
                c = G.hucre(a['musluk'])
                # hedef hücre geçilebilir değilse en yakın geçilebilir
                if not np.isfinite(cost[c[1], c[0]]):
                    best = None
                    for dx in range(-6, 7):
                        for dy in range(-6, 7):
                            q = (c[0] + dx, c[1] + dy)
                            if G.icinde(q) and np.isfinite(cost[q[1], q[0]]) and not F.duvar4[q[1], q[0]]:
                                d = dx * dx + dy * dy
                                if best is None or d < best[0]:
                                    best = (d, q)
                    if best:
                        c = best[1]
                musluklar.append(dict(arm=a, W=W, hucre=c))
    agac = {kok}
    kenar = set()
    kalan = list(musluklar)
    hatalar = []
    # ilk adım: dolaptan daireye dik giriş (yön sabit: duvardan içeri)
    while kalan:
        hed = {m['hucre']: m for m in kalan}
        yol = G.yol(list(agac), list(hed.keys()), donus=40.0, maliyet=cost)
        if yol is None:
            hatalar.extend(m['arm']['tip'] for m in kalan)
            break
        m = hed[yol[-1]]
        for a, b in zip(yol[:-1], yol[1:]):
            kenar.add((a, b))
        agac.update(yol)
        # ağaca dahil olan diğer musluklar
        for mm in list(kalan):
            if mm['hucre'] in agac:
                kalan.remove(mm)
        # aynı hatta paralel ikinci hat açılmasın: ağaç hücreleri ucuz
    uclar = [m['hucre'] for m in musluklar]
    par, cocuk, zin = _agac_zincirleri(kenar, kok, uclar)
    # yük birimleri (alt ağaç toplamı)
    yb_s = {}
    yb_h = {}
    sicak_hucre = set()
    for m in musluklar:
        c = m['hucre']
        t = m['arm']['tip']
        ys, yh = YB[t]
        while c is not None:
            yb_s[c] = yb_s.get(c, 0) + ys
            if yh > 0:
                yb_h[c] = yb_h.get(c, 0) + yh
                sicak_hucre.add(c)
            c = par.get(c)
    sog, sic = [], []
    for z in zin:
        pts = G.koseler(z)
        pts = [(float(x), float(y)) for x, y in pts]
        uc = z[-1]
        sog.append(dict(yol=pts, yb=round(yb_s.get(uc, 0), 2), hucreler=z))
        if uc in sicak_hucre:
            sic.append(dict(yol=[(x + 5, y + 5) for x, y in pts], yb=round(yb_h.get(uc, 0), 2), hucreler=z))
    D['temiz'] = dict(soguk=sog, sicak=sic, musluk=musluklar, kok=src_xy, yb_s=yb_s.get(kok, 0), yb_h=yb_h.get(kok, 0),
                      hata=hatalar)
    return D['temiz']


# ====================================================================== kat tasarımı (kolon tutarlılığı ile)
def _eslesen(Fref, F, W):
    """F katındaki ıslak hacmin referans kattaki karşılığı (ötelenmiş poligon IoU > 0.85)"""
    from shapely.affinity import translate
    g = translate(W['poly'], Fref.dx - F.dx)
    best = None
    for D in Fref.daire.values():
        for V in D['islak']:
            if V['tip'] != W['tip']:
                continue
            i = V['poly'].intersection(g).area
            if i <= 0:
                continue
            iou = i / V['poly'].union(g).area
            if iou > 0.8 and (best is None or iou > best[0]):
                best = (iou, V)
    return best[1] if best else None


def kat_tasarla(F, Fref=None, alt_katlar=()):
    islak_hacimler(F)
    for no, D in F.daire.items():
        cm_var = False
        for W in sorted(D['islak'], key=lambda W: (W['tip'] != 'banyo', -W['poly'].area)):
            kol = None
            V = _eslesen(Fref, F, W) if Fref is not None and Fref is not F else None
            if V is not None and V.get('kolon'):
                p = (V['kolon'][0] - Fref.dx + F.dx, V['kolon'][1])
                if kolon_gecerli(F, p, None, r=10) and W['poly'].buffer(2).contains(Point(p)):
                    kol = p
                W['ref'] = V
            if W['tip'] == 'banyo':
                if kol is None:
                    kol = kolon_sec(F, W, alt_katlar)
                W['kolon'] = kol
                if kol:
                    banyo_ek(F, W, kol, cm=not cm_var)
                    cm_var = cm_var or any(a['tip'] == 'CM' for a in W['armatur'])
            else:
                W['kolon'] = kol or mutfak_kolon(F, W)
            if W['kolon'] is not None:
                W['pis'], _ = pis_ag(W)
        D['cm_var'] = cm_var
    _izgara_katmanlari(F)
    F.dol = {no: sayac_dolabi(F, no) for no in F.daire}
    for no in F.daire:
        daire_temiz(F, no)
    balkon_yagmur(F)


# ====================================================================== balkon süzgeci / yağmur inişi
def balkon_yagmur(F):
    K = F.K
    inisler = list(K.inis_mimari)
    F.yagmur = []
    for s in K.balkon_suzgec:
        if inisler:
            i = min(inisler, key=lambda p: math.dist(p, s))
            if math.dist(i, s) < 90:
                a = (s[0], i[1]) if abs(i[1] - s[1]) >= abs(i[0] - s[0]) else (i[0], s[1])
                y1 = [tuple(s), a, tuple(i)]
                y2 = [tuple(s), (a[0] if a[0] != s[0] else i[0], a[1] if a[1] != s[1] else i[1])[::1], tuple(i)]
                yol = min((y1, [tuple(s), (i[0], s[1]), tuple(i)], [tuple(s), (s[0], i[1]), tuple(i)]),
                          key=lambda yy: LineString(yy).intersection(F.beton).length)
                F.yagmur.append(dict(suzgec=tuple(s), inis=tuple(i), mimari=True, yol=yol))
                continue
        # mimaride iniş yok: B blok düzeni (süzgeçten dışarı 45, yana 30 — köşe kolonu tarafı)
        q = Point(s)
        best = None
        for ang in range(0, 360, 90):
            d = (round(math.cos(math.radians(ang))), round(math.sin(math.radians(ang))))
            p = (s[0] + d[0] * 45, s[1] + d[1] * 45)
            r = int((F.y1 - p[1]) / RES)
            c = int((p[0] - F.x0) / RES)
            dis = not (0 <= r < F.ayak_izi_m.shape[0] and 0 <= c < F.ayak_izi_m.shape[1]) or not F.ayak_izi_m[r, c]
            if dis:
                best = d
                break
        if best is None:
            continue
        d = best
        t = (-d[1], d[0])
        yan = min((1, -1), key=lambda sg: F.beton.distance(Point(s[0] + t[0] * sg * 60, s[1] + t[1] * sg * 60)))
        i = (s[0] + d[0] * 45 + t[0] * yan * 30, s[1] + d[1] * 45 + t[1] * yan * 30)
        F.yagmur.append(dict(suzgec=tuple(s), inis=i, mimari=False,
                             yol=[tuple(s), (s[0] + d[0] * 45, s[1] + d[1] * 45), i]))


# ====================================================================== koridor dağıtımı (asma tavan)
def riser_gecerli(F, p, r=14):
    q = Point(p)
    if getattr(F, '_ort8', None) is None:
        from shapely.prepared import prep
        F._ort8 = prep(F.ortak.buffer(-8))
        F._kapi5 = prep(F.kapi_u.buffer(5))
    return (F._ort8.contains(q) and F.beton.distance(q) > 3 and F.yasak_u.distance(q) > r and
            F.saft_u.distance(q) > 3 and not F._kapi5.contains(q))


def riser_bul(Fs, ipucu, yaricap=200):
    """tüm katlarda (Z çerçevesinde ipucu) geçerli, duvara 10-20 cm yakın kolon kutusu noktası"""
    best = None
    for dx in range(-yaricap, yaricap + 1, 4):
        for dy in range(-yaricap, yaricap + 1, 4):
            p0 = (ipucu[0] + dx, ipucu[1] + dy)
            ok = True
            dmin = 1e9
            for F in Fs:
                p = (p0[0] + F.dx, p0[1])
                if not riser_gecerli(F, p):
                    ok = False
                    break
                _izgara_katmanlari(F)
                c = F.G.hucre(p)
                dmin = min(dmin, F.dduvar[c[1], c[0]])
            if not ok or not (12 <= dmin <= 22):
                continue
            sk = math.hypot(dx, dy)
            if best is None or sk < best[0]:
                best = (sk, p0)
    return best[1] if best else None


def koridor_tasarla(F, riser_z):
    """riser (Z çerçevesi) -> her daire sayaç dolabına soğuk / sıcak / sirkülasyon ağacı (koridor ortasından)"""
    _izgara_katmanlari(F)
    G = F.G
    rp = (riser_z[0] + F.dx, riser_z[1])
    cost = np.full((G.ny, G.nx), np.inf)
    om = F.ortak4 & ~F.acik4
    cost[om] = (1.0 + 8.0 * np.exp(-F.dduvar / 25.0))[om]
    cost[F.beton4 | F.yasak4 | F.saft4] = np.inf
    kok = G.hucre(rp)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            q = (kok[0] + dx, kok[1] + dy)
            if G.icinde(q) and not F.beton4[q[1], q[0]]:
                cost[q[1], q[0]] = min(cost[q[1], q[0]], 2.0) if np.isfinite(cost[q[1], q[0]]) else 2.0
    hed = {}
    for no, d in F.dol.items():
        if d is None:
            continue
        c = G.hucre(d['c'])
        hed[c] = no
        # dolap ağzı: koridora doğru 30 cm geçilebilir
        n = d['n']
        for s in range(0, 34, 2):
            q = G.hucre((d['c'][0] + n[0] * s, d['c'][1] + n[1] * s))
            if G.icinde(q) and not (F.beton4[q[1], q[0]] or F.yasak4[q[1], q[0]]):
                if not np.isfinite(cost[q[1], q[0]]):
                    cost[q[1], q[0]] = 3.0
    agac = {kok}
    kenar = set()
    kalan = dict(hed)
    hata = []
    while kalan:
        yol = G.yol(list(agac), list(kalan.keys()), donus=60.0, maliyet=cost)
        if yol is None:
            hata = list(kalan.values())
            break
        for a, b in zip(yol[:-1], yol[1:]):
            kenar.add((a, b))
        agac.update(yol)
        for c in list(kalan):
            if c in agac:
                kalan.pop(c)
    par, cocuk, zin = _agac_zincirleri(kenar, kok, list(hed.keys()))
    # her dolabın yükü (soğuk/sıcak YB) ağaçta toplanır
    yb_s, yb_h, nd = {}, {}, {}
    for c, no in hed.items():
        D = F.daire[no]
        t = D.get('temiz', {})
        cc = c
        while cc is not None:
            yb_s[cc] = yb_s.get(cc, 0) + t.get('yb_s', 0)
            yb_h[cc] = yb_h.get(cc, 0) + t.get('yb_h', 0)
            nd[cc] = nd.get(cc, 0) + 1
            cc = par.get(cc)
    hat = []
    for z in zin:
        pts = [(float(x), float(y)) for x, y in G.koseler(z)]
        uc = z[-1]
        hat.append(dict(yol=pts, yb_s=round(yb_s.get(uc, 0), 2), yb_h=round(yb_h.get(uc, 0), 2), daire=nd.get(uc, 0)))
    F.koridor = dict(riser=rp, hatlar=hat, hata=hata, yb_s=yb_s.get(kok, 0), yb_h=yb_h.get(kok, 0))
    return F.koridor
