"""sihhi2 — mimari okuma (kat planı üreticisi için): duvar katısı, mahal poligonları, daire grupları, ıslak hacimler,
armatürler, kapılar, şaftlar, yağmur inişleri.

Yalnız mimari TANIMA için `motor/kontrolor/mimari_bilgi.py` ve `motor/deneme/uctan_uca/mimari.py` kullanılır (görev izni);
güzergâh / çizim kodu bu modülde yoktur.

Duvar katısı: mimari çizgilerden 7–36 cm aralıklı PARALEL çiftlerin arası (duvar, pencere, perde) + taramalı betonarme.
Tek çizgiler (armatür, tezgâh, duş teknesi kenarı) duvar sayılmaz → mahal poligonu armatür çizgileriyle bölünmez.
"""
import math
import os
import sys

import numpy as np
import cv2
from scipy import ndimage as ndi
from skimage.segmentation import watershed
from shapely import STRtree
from shapely.geometry import LineString, Point, Polygon, box, MultiPolygon
from shapely.ops import unary_union

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in (KOK + '/motor/kontrolor', KOK + '/motor/deneme/uctan_uca', KOK + '/motor'):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import mimari_bilgi as MB  # noqa: E402
M = MB.M

KAYNAK = KOK + '/ornekler/new_block.dxf.xz'
RES = 2.0


def kayitlar():
    return MB.kaynak_oku(KAYNAK)


def pencere(k, pad=0.0):
    return M.win(k, pad)


# ------------------------------------------------------------------ duvar katısı
def segmentler(R, en_az=12.0):
    out = []
    for a in R:
        if a[0] == 'L':
            ps = [a[1]]
        elif a[0] == 'P':
            xs = [p[0] for p in a[1]]
            ys = [p[1] for p in a[1]]
            kapali = math.hypot(a[1][0][0] - a[1][-1][0], a[1][0][1] - a[1][-1][1]) < 1.0
            if kapali and max(max(xs) - min(xs), max(ys) - min(ys)) < 130:   # armatür / tefriş kapalı şekli: duvar değil
                continue
            ps = list(zip(a[1][:-1], a[1][1:]))
        else:
            continue
        for p, q in ps:
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            if L >= en_az:
                out.append((p, q, L))
    return out


def duvar_katisi(R, cols):
    seg = segmentler(R)
    ls = [LineString([p, q]) for p, q, L in seg]
    tree = STRtree(ls)
    quads = []
    for i, (p, q, L) in enumerate(seg):
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        for j in tree.query(ls[i].buffer(36)):
            if j <= i:
                continue
            p2, q2, L2 = seg[j]
            vx, vy = (q2[0] - p2[0]) / L2, (q2[1] - p2[1]) / L2
            if abs(ux * vy - uy * vx) > 0.03:
                continue
            d = (p2[0] - p[0]) * (-uy) + (p2[1] - p[1]) * ux
            if not (7 <= abs(d) <= 36):
                continue
            t1 = (p2[0] - p[0]) * ux + (p2[1] - p[1]) * uy
            t2 = (q2[0] - p[0]) * ux + (q2[1] - p[1]) * uy
            a0, a1 = max(0, min(t1, t2)), min(L, max(t1, t2))
            if a1 - a0 < 10:
                continue
            P = [(p[0] + ux * a0, p[1] + uy * a0), (p[0] + ux * a1, p[1] + uy * a1)]
            Q = [(x - uy * d, y + ux * d) for x, y in P]
            quads.append(Polygon([P[0], P[1], Q[1], Q[0]]).buffer(0.5))
    return unary_union(quads + list(cols))


# ------------------------------------------------------------------ raster mahal tanıma
class Izgara:
    def __init__(self, w, res=RES):
        self.x0, self.y0, self.res = w[0], w[1], res
        self.W = int((w[2] - w[0]) / res) + 1
        self.H = int((w[3] - w[1]) / res) + 1

    def px(self, p):
        return (int(round((p[0] - self.x0) / self.res)), int(round((self.H - 1) - (p[1] - self.y0) / self.res)))

    def w(self, c, r):
        return (self.x0 + c * self.res, self.y0 + ((self.H - 1) - r) * self.res)

    def doldur(self, geom, deger=255, img=None):
        img = np.zeros((self.H, self.W), np.uint8) if img is None else img
        gs = geom.geoms if hasattr(geom, 'geoms') else [geom]
        for g in gs:
            if g.is_empty or g.geom_type != 'Polygon':
                continue
            ext = np.array([self.px(p) for p in g.exterior.coords], np.int32)
            cv2.fillPoly(img, [ext], deger)
            for h in g.interiors:
                cv2.fillPoly(img, [np.array([self.px(p) for p in h.coords], np.int32)], 0)
        return img

    def poligon(self, mask, min_alan=100):
        cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ps = []
        for c in cs:
            if len(c) < 3:
                continue
            pg = Polygon([self.w(p[0][0], p[0][1]) for p in c]).buffer(0)
            if pg.area > min_alan:
                ps.append(pg)
        return unary_union(ps) if ps else Polygon()


def mahal_tani(S, labels, w, kapi=100.0, disk=40.0):
    g = Izgara(w)
    wall = g.doldur(S)
    free = wall == 0
    r = int(kapi / 2 / g.res)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    closed = cv2.dilate(wall, k) == 0
    lab, n = ndi.label(closed)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    markers = np.zeros_like(lab)
    names = {}
    comp = {}
    for j, (x, y, nm) in enumerate(labels):
        c, rr = g.px((x, y))
        if not (0 <= c < g.W and 0 <= rr < g.H):
            continue
        l = lab[rr, c]
        if l == 0:
            l = -(j + 1)
        elif l in border:
            l = -(j + 1)
        comp.setdefault(l, []).append((x, y, nm, c, rr))
    mid = 0
    yy, xx = np.mgrid[0:g.H, 0:g.W]
    for l, items in comp.items():
        if len(items) == 1 and l > 0:
            x, y, nm, c, rr = items[0]
            mid += 1
            markers[lab == l] = mid
            names[mid] = (nm, (x, y))
        else:
            rad = int((disk if l > 0 else 12.0) / g.res)
            for x, y, nm, c, rr in items:
                mid += 1
                r0, r1, c0, c1 = max(0, rr - rad), rr + rad + 1, max(0, c - rad), c + rad + 1
                sub = ((yy[r0:r1, c0:c1] - rr) ** 2 + (xx[r0:r1, c0:c1] - c) ** 2 <= rad * rad)
                sub &= (lab[r0:r1, c0:c1] == l) if l > 0 else free[r0:r1, c0:c1]
                markers[r0:r1, c0:c1][sub] = mid
                names[mid] = (nm, (x, y))
    ext = np.isin(lab, list(border - {0}))
    markers[ext & (markers == 0)] = mid + 1
    dist = ndi.distance_transform_edt(free)
    ws = watershed(-dist, markers, mask=free)
    out = []
    for i, (nm, xy) in names.items():
        m = ndi.binary_fill_holes(ws == i)
        pg = g.poligon(m)
        if pg.is_empty:
            continue
        if pg.geom_type == 'MultiPolygon':          # etiketin bulunduğu parça + büyükler
            pg = max(pg.geoms, key=lambda q: (q.buffer(5).contains(Point(xy)), q.area))
        out.append(dict(name=nm, poly=pg.simplify(1.0), xy=xy, area=pg.area / 1e4))
    return out


# ------------------------------------------------------------------ yardımcı sınıflama
def tip(ad):
    a = MB.norm(ad)
    if 'balkon' in a or 'teras' in a:
        return 'balkon'
    if 'mutfak' in a:
        return 'mutfak'
    if MB.islak_mi(ad):
        return 'islak'
    if a.startswith('antre') or a.startswith('hol') or 'koridor' in a:
        return 'hol'
    if MB.ortak_mi(ad):
        return 'ortak'
    return 'kuru'


def _c3(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy


# ------------------------------------------------------------------ kat analizi
class Kat:
    """Bir katın mimari bilgisi (kaynak = çizim koordinatı; öteleme yok)."""

    def __init__(self, A, k, pad=110.0):
        self.k = k
        self.off = M.OFF[k]
        self.w = pencere(k, pad)
        self.w0 = pencere(k)
        self.R = M.recs_in(A, self.w)
        self.labs = MB._etiketler(self.R)
        self.cols = M.columns(self.R)
        self.S = duvar_katisi(self.R, self.cols)
        rooms = mahal_tani(self.S, self.labs, self.w)
        for r in rooms:
            r['tip'] = tip(r['name'])
        # daire grupları (kontrolörle aynı yöntem: daire numarası tohumları + duvar rasterinde yürüme)
        rr = [dict(name=r['name'], xy=r['xy'], poly=r['poly']) for r in rooms]
        d, self.tohum = MB._daire_gruplari(self.R, rr, self.w, self.cols)
        for i, r in enumerate(rooms):
            r['daire'] = d.get(i)
            r['i'] = i
        self.rooms = rooms
        self.bina = unary_union([r['poly'].buffer(30) for r in rooms if r['tip'] != 'balkon']).buffer(-10)
        self.yazilar = [((a[1][0][0], a[1][0][1]), a[2][0], a[2][1], a[2][2], a[1][1]) for a in self.R if a[0] == 'T']
        self._kapilar()
        self._daire_kapidan()
        self._armaturler()
        self._inisler()
        self._saftlar()

    # ---- armatürler: mimari.fixtures imzaları, mahal ataması YALNIZ poligon içi (+10 cm duvar payı)
    def _armaturler(self):
        wet_l = [(x, y, t) for x, y, t in self.labs if MB.islak_mi(t)]
        W = M.Walls(self.R)
        wet = [dict(name=t, xy=(x, y), rect=W.rect((x, y))) for x, y, t in wet_l]
        fx = M.fixtures(self.R, wet, W)
        out = []
        for f in fx:
            p = Point(f['c'])
            aday = [r for r in self.rooms if r['tip'] in ('islak', 'mutfak', 'balkon') and r['poly'].buffer(35).contains(p)]
            if not aday:
                aday = [r for r in self.rooms if r['poly'].buffer(12).contains(p)]
            r = min(aday, key=lambda q: (q['poly'].distance(p), q['poly'].area)) if aday else None
            if f['kind'] == 'KOMBI':
                if r is None:
                    r = min(self.rooms, key=lambda q: q['poly'].distance(p))
            out.append(dict(kind=f['kind'], c=tuple(f['c']), bb=f.get('bb'), oda=r, ek=False))
        # aynı mahalde aynı türden çift tanıma (örn. iki LV gideri 10 cm içinde) -> tek
        tek = []
        for f in out:
            if any(g['kind'] == f['kind'] and math.hypot(g['c'][0] - f['c'][0], g['c'][1] - f['c'][1]) < 15 for g in tek):
                continue
            tek.append(f)
        self.fx = tek

    def _inisler(self):
        cs = [(a[1][0], a[2]) for a in self.R if a[0] == 'C' and 3 <= a[2] <= 12]
        ins = []
        for i, (c, r) in enumerate(cs):
            if any(j != i and abs(c2[0] - c[0]) < 1.5 and abs(c2[1] - c[1]) < 1.5 and abs(r2 - r) > 1.5
                   for j, (c2, r2) in enumerate(cs)):
                if not any(abs(q[0] - c[0]) < 1.5 and abs(q[1] - c[1]) < 1.5 for q in ins):
                    ins.append(tuple(c))
        self.inisler = ins

    def _saftlar(self):
        """mekanik havalandırma şaftı: 'mek.' yazısının 60 cm yakınındaki daire (r 8–25) ve onu çevreleyen kare"""
        self.saftlar = []
        mek = [p for p, s, h, rot, c in self.yazilar if s.strip().lower().startswith('mek')]
        for p in mek:
            cs = [(a[1][0], a[2]) for a in self.R if a[0] == 'C' and 8 <= a[2] <= 25
                  and math.hypot(a[1][0][0] - p[0], a[1][0][1] - p[1]) < 70]
            if not cs:
                continue
            c, r = min(cs, key=lambda q: math.hypot(q[0][0] - p[0], q[0][1] - p[1]))
            kare = Point(c).buffer(r + 9, cap_style=3)
            self.saftlar.append(dict(c=tuple(c), r=r, poly=kare, yazi=p))

    def _kapilar(self):
        """kapı açıklıkları = duvar katısının kapanışı (dilate+erode 100 cm) eksi kendisi; büyük parçalar"""
        g = Izgara(self.w)
        wall = g.doldur(self.S)
        r = int(52 / g.res)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        cl = cv2.erode(cv2.dilate(wall, k), k)
        acik = (cl > 0) & (wall == 0)
        acik = cv2.morphologyEx(acik.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        pg = g.poligon(acik, min_alan=300)
        gs = pg.geoms if hasattr(pg, 'geoms') else ([pg] if not pg.is_empty else [])
        self.kapilar = []
        for q in gs:
            rr = q.minimum_rotated_rectangle
            cs = list(rr.exterior.coords)
            a_ = math.hypot(cs[1][0] - cs[0][0], cs[1][1] - cs[0][1])
            b_ = math.hypot(cs[2][0] - cs[1][0], cs[2][1] - cs[1][1])
            kisa, uzun = min(a_, b_), max(a_, b_)
            if 50 <= uzun <= 130 and kisa <= 50 and q.area > 0.35 * rr.area:
                self.kapilar.append(q)
        self.kapi_u = unary_union(self.kapilar) if self.kapilar else Polygon()

    def _daire_kapidan(self):
        """daire ataması kapı komşuluğuyla: daire no yazısına en yakın (ortak olmayan) mahal girişi; kapılardan BFS,
        ortak alandan geçilmez. Ulaşılamayanlar: yürüme mesafesi ataması (MB) korunur."""
        import collections
        n = len(self.rooms)
        kom = collections.defaultdict(set)
        self.kapi_oda = []
        for q in self.kapilar:
            yak = [r['i'] for r in self.rooms if r['poly'].distance(q) < 25]
            self.kapi_oda.append(yak)
            for a in yak:
                for b in yak:
                    if a != b:
                        kom[a].add(b)
        self.komsu = kom
        yeni = {}
        kuyruk = collections.deque()
        for p, no in self.tohum:
            aday = [r for r in self.rooms if r['tip'] not in ('ortak',) and r['poly'].distance(Point(p)) < 160]
            # giriş: tohuma en yakın, bir ortak mahalle kapı komşusu olan mahal
            aday2 = [r for r in aday if any(self.rooms[j]['tip'] == 'ortak' for j in kom[r['i']])] or aday
            if not aday2:
                continue
            r0 = min(aday2, key=lambda r: r['poly'].distance(Point(p)))
            if r0['i'] not in yeni:
                yeni[r0['i']] = no
                kuyruk.append(r0['i'])
        while kuyruk:
            i = kuyruk.popleft()
            for j in kom[i]:
                if j in yeni or self.rooms[j]['tip'] == 'ortak':
                    continue
                yeni[j] = yeni[i]
                kuyruk.append(j)
        for r in self.rooms:
            if r['i'] in yeni:
                r['daire_mb'] = r['daire']
                r['daire'] = yeni[r['i']]
        # kapısı tanınamayan mahal: kapıyla atanmış komşu mahallerden en uzun ortak duvarlı olanın dairesi
        for r in self.rooms:
            if r['i'] in yeni or r['tip'] == 'ortak':
                continue
            best, bl = None, 0.0
            for q in self.rooms:
                if q['i'] not in yeni:
                    continue
                L = r['poly'].buffer(18).intersection(q['poly'].buffer(18)).area / 36.0
                if L > bl:
                    best, bl = yeni[q['i']], L
            if best is not None and bl > 40:
                r['daire_mb'] = r['daire']
                r['daire'] = best

    # ---- sorgular
    def oda(self, p, tipler=None):
        pt = Point(p)
        aday = [r for r in self.rooms if (tipler is None or r['tip'] in tipler) and r['poly'].buffer(3).contains(pt)]
        return min(aday, key=lambda r: r['poly'].area) if aday else None

    def daire_odalari(self, d):
        return [r for r in self.rooms if r['daire'] == d]
