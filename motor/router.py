"""Izgara üzerinde A* boru güzergâh bulucu (genel, her projede kullanılabilir).

- Duvar dibini/duvar içini tercih eder (duvardan uzak hücreye ceza), dönüş cezası, başka sistemin borusunu kesme
  cezası (köprü gerekir), başka boruya çok yakın paralel gitme cezası; betonarme kolon / kolon sembolü yasak.
- Hedef bir nokta ya da aynı sistemin mevcut ağacı olabilir (branşman en yakın uygun noktadan ana hatta bağlanır).
- Sonuç ortogonal (yatay/dikey) nokta listesi; eşdoğrusal ara noktalar birleştirilir.
Fikir: red1oon/mep_engineering (A* + dik açıya çevirme) - kod alınmadı, yöntem uyarlandı.
"""
import heapq, math
import numpy as np
from scipy import ndimage
from skimage.draw import line as _sk_line, polygon as _sk_poly
from shapely.geometry import LineString, Point


class Grid:
    def __init__(self, bounds, step=2.0, walls=(), obstacles=(), wall_band=14.0, far_pen=1.0):
        self.x0, self.y0, x1, y1 = bounds
        self.s = step
        self.nx = int((x1 - self.x0) / step) + 1
        self.ny = int((y1 - self.y0) / step) + 1
        self.base = np.ones((self.nx, self.ny), dtype=np.float32)
        self.block = np.zeros((self.nx, self.ny), dtype=bool)
        self.occ = {}                       # sistem -> hücre sayacı
        self.lines = {}                     # sistem -> [LineString]
        if walls:
            img = np.zeros((self.nx, self.ny), dtype=bool)
            for w in walls:
                for a, b in zip(w[:-1], w[1:]):
                    ia, ja = self.ij(a); ib, jb = self.ij(b)
                    rr, cc = _sk_line(ia, ja, ib, jb)
                    ok = (rr >= 0) & (rr < self.nx) & (cc >= 0) & (cc < self.ny)
                    img[rr[ok], cc[ok]] = True
            d = ndimage.distance_transform_edt(~img) * step
            self.base += far_pen * np.clip((d - 4.0) / max(1.0, wall_band - 4.0), 0, 1)
        for ob in obstacles:
            self.add_block(ob)

    def ij(self, p):
        return int(round((p[0] - self.x0) / self.s)), int(round((p[1] - self.y0) / self.s))

    def xy(self, ij):
        return (self.x0 + ij[0] * self.s, self.y0 + ij[1] * self.s)

    def inside(self, ij):
        return 0 <= ij[0] < self.nx and 0 <= ij[1] < self.ny

    def add_block(self, geom, pad=1.0):
        g = geom.buffer(pad)
        xs, ys = g.exterior.coords.xy
        rr, cc = _sk_poly([(x - self.x0) / self.s for x in xs], [(y - self.y0) / self.s for y in ys], (self.nx, self.ny))
        self.block[rr, cc] = True

    def add_cost(self, geom, c):
        """bölgeye ek maliyet (ör. kapı önü / kapı kanadı: boru buradan geçmesin)"""
        xs, ys = geom.exterior.coords.xy
        rr, cc = _sk_poly([(x - self.x0) / self.s for x in xs], [(y - self.y0) / self.s for y in ys], (self.nx, self.ny))
        self.base[rr, cc] += c

    def rect_mask(self, r):
        m = np.zeros((self.nx, self.ny), dtype=bool)
        i0, j0 = self.ij((r[0], r[1])); i1, j1 = self.ij((r[2], r[3]))
        m[max(0, i0):max(0, i1 + 1), max(0, j0):max(0, j1 + 1)] = True
        return m

    def add_line(self, pts, sysn):
        o = self.occ.setdefault(sysn, np.zeros((self.nx, self.ny), dtype=np.int16))
        self.lines.setdefault(sysn, []).append(LineString(pts))
        for a, b in zip(pts[:-1], pts[1:]):
            ia, ja = self.ij(a); ib, jb = self.ij(b)
            rr, cc = _sk_line(ia, ja, ib, jb)
            ok = (rr >= 0) & (rr < self.nx) & (cc >= 0) & (cc < self.ny)
            o[rr[ok], cc[ok]] += 1

    def _other(self, sysn, w=None):
        tot = np.zeros((self.nx, self.ny), dtype=np.float32)
        for k, v in self.occ.items():
            if k != sysn:
                tot = tot + v * (1.0 if not w else w.get(k, 1.0))
        return tot

    def route(self, a, b=None, sysn='S', to_tree=False, turn=5.0, cross=80.0, close=6.0, near_r=5.0,
              free_end=10.0, max_exp=600000, wsys=None, mask=None, yk=1.0):
        """a -> b (nokta) veya a -> aynı sistemin mevcut hattı (to_tree). Ortogonal nokta listesi döner."""
        other = self._other(sysn, wsys)
        near = ndimage.binary_dilation(other > 0, iterations=max(1, int(near_r / self.s))) & ~(other > 0)
        tree = (self.occ.get(sysn) > 0) if (to_tree and sysn in self.occ) else None
        sa = self.ij(a)
        sb = self.ij(b) if b is not None else None
        ea = Point(a)
        eb = Point(b) if b is not None else None
        h = (lambda q: abs(q[0] - sb[0]) + abs(q[1] - sb[1])) if sb else (lambda q: 0)
        D = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        best, prev = {}, {}
        pq = [(h(sa), 0.0, sa, -1, None)]
        n = 0
        goal = None
        fe = free_end / self.s
        while pq:
            f, g, cur, d, par = heapq.heappop(pq)
            key = (cur, d)
            if key in best and best[key] <= g:
                continue
            best[key] = g
            prev[key] = par
            if (sb and cur == sb) or (tree is not None and tree[cur] and (abs(cur[0] - sa[0]) + abs(cur[1] - sa[1])) > 1):
                goal = key
                break
            n += 1
            if n > max_exp:
                return None
            for k, (di, dj) in enumerate(D):
                q = (cur[0] + di, cur[1] + dj)
                if not self.inside(q):
                    continue
                dz = min(abs(q[0] - sa[0]) + abs(q[1] - sa[1]), (abs(q[0] - sb[0]) + abs(q[1] - sb[1])) if sb else 1e9)
                endz = dz <= fe
                if (self.block[q] or (mask is not None and mask[q])) and not endz:
                    continue
                c = float(self.base[q]) * (yk if dj else 1.0)
                if not endz:
                    c += cross * other[q] + close * near[q]
                if d != -1 and k != d:
                    c += turn
                ng = g + c
                nk = (q, k)
                if nk in best and best[nk] <= ng:
                    continue
                heapq.heappush(pq, (ng + h(q), ng, q, k, key))
        if goal is None:
            return None
        cells = []
        k = goal
        while k is not None:
            cells.append(k[0])
            k = prev.get(k)
        cells.reverse()
        pts = [self.xy(c) for c in cells]
        if b is not None:
            end = b
        else:            # ağaca oturt: son hücreyi en yakın aynı sistem hattına izdüşür
            P = Point(pts[-1])
            ln = min(self.lines[sysn], key=lambda l_: l_.distance(P))
            q = ln.interpolate(ln.project(P))
            end = (q.x, q.y)
        return ortho([a] + pts[1:-1] + [end], prefer_end=True)


def ortho(pts, prefer_end=True):
    """ızgara yolunu temizle: gerçek uçlar korunur, çapraz kalan kısa parçalar dik açıya çevrilir"""
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 0.05:
            out.append(p)
    pts = _collinear(out)
    # uçlara yakın kısa kırıkları (ızgara yuvarlaması) gider
    if len(pts) >= 3:
        a, b, c = pts[0], pts[1], pts[2]
        if abs(a[0] - b[0]) > 0.05 and abs(a[1] - b[1]) > 0.05:
            pts[1] = (a[0], b[1]) if abs(b[0] - c[0]) < 0.05 or abs(b[1] - c[1]) > 0.05 else (b[0], a[1])
    fin = [pts[0]]
    for i, p in enumerate(pts[1:], 1):
        q = fin[-1]
        if abs(p[0] - q[0]) > 0.05 and abs(p[1] - q[1]) > 0.05:
            # sonraki parçanın yönüne göre köşe seç
            if i + 1 < len(pts):
                r = pts[i + 1]
                horiz_next = abs(r[1] - p[1]) < 0.05
                fin.append((q[0], p[1]) if horiz_next else (p[0], q[1]))
            else:
                prevh = len(fin) >= 2 and abs(fin[-2][1] - q[1]) < 0.05
                fin.append((q[0], p[1]) if prevh else (p[0], q[1]))
        fin.append(p)
    return _collinear(fin)


def _collinear(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 0.05:
            out.append(p)
    if len(out) < 3:
        return out
    res = [out[0]]
    for i in range(1, len(out) - 1):
        a, b, c = res[-1], out[i], out[i + 1]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) < 1e-6 and \
                (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) >= 0:
            continue
        res.append(b)
    res.append(out[-1])
    return res
