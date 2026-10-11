"""Duvar çizgilerinden mahal bölgelerini raster yöntemiyle çıkarır (kapılar kapatılarak)."""
import numpy as np
import cv2
from scipy import ndimage as ndi
from skimage.segmentation import watershed
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union


class Grid:
    def __init__(self, x0, y0, x1, y1, res=2.0):
        self.x0, self.y0, self.res = x0, y0, res
        self.W = int((x1 - x0) / res) + 1
        self.H = int((y1 - y0) / res) + 1

    def px(self, p):
        return (int(round((p[0] - self.x0) / self.res)), int(round((self.H - 1) - (p[1] - self.y0) / self.res)))

    def w(self, c, r):
        return (self.x0 + c * self.res, self.y0 + ((self.H - 1) - r) * self.res)


def raster_walls(g, ents):
    img = np.zeros((g.H, g.W), np.uint8)
    for k, d in ents:
        if k == 'L':
            cv2.line(img, g.px(d[0]), g.px(d[1]), 255, 1)
        elif k == 'P':
            pts = np.array([g.px(p) for p in d], np.int32)
            cv2.polylines(img, [pts], False, 255, 1)
        elif k == 'C':
            cv2.circle(img, g.px((d[0], d[1])), max(1, int(d[2] / g.res)), 255, 1)
    return img


def detect(ents, labels, bbox, res=2.0, door=55.0, fill_holes=True, disc=60.0):
    """ents: [(kind,data)] duvar/kolon/pencere; labels: [(x,y,name)]; bbox: (x0,y0,x1,y1)
    dönüş: {i: dict(name, mask, poly, area_m2)}"""
    g = Grid(*bbox, res=res)
    wall = raster_walls(g, ents)
    wall = cv2.dilate(wall, np.ones((2, 2), np.uint8))
    free = wall == 0
    # kapıları kapat: duvarları door/2 kadar şişir
    r = int(door / 2 / res)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    closed = cv2.dilate(wall, k) == 0
    lab, n = ndi.label(closed)
    # dış bölge (kenara değen) etiketleri
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
            l = -(j + 1)          # kendi disk işaretçisi
        elif l in border:
            continue
        comp.setdefault(l, []).append((x, y, nm, c, rr))
    mid = 0
    yy, xx = np.mgrid[0:g.H, 0:g.W]
    for l, items in comp.items():
        if len(items) == 1 and l > 0:
            x, y, nm, c, rr = items[0]
            mid += 1
            markers[lab == l] = mid
            names[mid] = (nm, l, (x, y))
        else:
            rad = int((disc if l > 0 else 12.0) / res)
            for x, y, nm, c, rr in items:
                mid += 1
                r0, r1, c0, c1 = max(0, rr - rad), rr + rad + 1, max(0, c - rad), c + rad + 1
                sub = ((yy[r0:r1, c0:c1] - rr) ** 2 + (xx[r0:r1, c0:c1] - c) ** 2 <= rad * rad)
                sub &= (lab[r0:r1, c0:c1] == l) if l > 0 else free[r0:r1, c0:c1]
                markers[r0:r1, c0:c1][sub] = mid
                names[mid] = (nm, l, (x, y))
    ext = np.isin(lab, list(border - {0}))
    markers[ext] = mid + 1
    # geodesik geri büyütme: watershed serbest alan içinde
    dist = ndi.distance_transform_edt(free)
    ws = watershed(-dist, markers, mask=free)
    out = {}
    for i, (nm, l, xy) in names.items():
        m = (ws == i)
        if fill_holes:
            m = ndi.binary_fill_holes(m)
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        polys = []
        for cnt in cs:
            if len(cnt) < 3:
                continue
            pts = [g.w(p[0][0], p[0][1]) for p in cnt]
            pg = Polygon(pts).buffer(0)
            if pg.area > 100:
                polys.append(pg)
        if not polys:
            continue
        poly = unary_union(polys)
        out[i] = dict(name=nm, mask=m, poly=poly, area=poly.area / 1e4, xy=xy)
    return out, g


def rects_in(mask, g, inset=10.0, minw=50.0, cover=0.92, maxn=4):
    """Rektilineer maskeyi (içeriden inset) en büyük dikdörtgenlerle kapla."""
    r = max(1, int(inset / g.res))
    m = cv2.erode(mask.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
    total = m.sum()
    rects = []
    if total == 0:
        return rects
    rs, cs = np.where(m)
    R0, C0 = rs.min(), cs.min()
    work = m[R0:rs.max() + 1, C0:cs.max() + 1].copy()
    while work.sum() > total * (1 - cover) and len(rects) < maxn:
        rr = _max_rect(work)
        if rr is None:
            break
        r0, c0, r1, c1 = rr
        if (c1 - c0) * g.res < minw or (r1 - r0) * g.res < minw:
            break
        work[r0:r1, c0:c1] = False
        x0, y1 = g.w(c0 + C0, r0 + R0)
        x1, y0 = g.w(c1 + C0, r1 + R0)
        rects.append((x0, y0, x1, y1))
    return rects


def _max_rect(m):
    """en büyük dolu dikdörtgen (histogram yöntemi). dönüş (r0,c0,r1,c1) yarı açık"""
    H, W = m.shape
    h = np.zeros(W, int)
    best = (0, None)
    for r in range(H):
        h = np.where(m[r], h + 1, 0)
        st = []
        for c in range(W + 1):
            cur = h[c] if c < W else 0
            s = c
            while st and st[-1][1] >= cur:
                s, hh = st.pop()
                a = hh * (c - s)
                if a > best[0]:
                    best = (a, (r - hh + 1, s, r + 1, c))
            st.append((s, cur))
    return best[1]


def circ3(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy


def door_closures(arcs, rmin=55, rmax=125):
    """kapı yay polilinlerinden menteşe->iki uç yarıçap çizgileri (kapalı kapı + açık kanat)."""
    out = []
    for pts in arcs:
        if len(pts) < 5:
            continue
        c = circ3(pts[0], pts[len(pts) // 2], pts[-1])
        if c is None:
            continue
        r = ((pts[0][0] - c[0]) ** 2 + (pts[0][1] - c[1]) ** 2) ** 0.5
        if not (rmin <= r <= rmax):
            continue
        out.append(('L', (c, pts[0])))
        out.append(('L', (c, pts[-1])))
    return out
