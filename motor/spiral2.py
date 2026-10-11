"""Mahal poligonuna uyan karşı akışlı (salyangoz) yerden ısıtma serpantini."""
import math
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.ops import substring


def _largest(g):
    if g.is_empty:
        return None
    if isinstance(g, MultiPolygon):
        g = max(g.geoms, key=lambda p: p.area)
    return g


def _open_ring(poly, start, gap, ccw=True):
    ring = poly.exterior
    coords = list(ring.coords)[:-1]
    if (Polygon(coords).exterior.is_ccw) != ccw:
        coords = coords[::-1]
    ls = LineString(coords + [coords[0]])
    t0 = ls.project(Point(start))
    Lr = ls.length
    # halkayı t0'dan başlat
    a = substring(ls, t0, Lr)
    b = substring(ls, 0, t0)
    pts = list(a.coords) + list(b.coords)[1:]
    ls2 = LineString(pts)
    end = max(0.0, ls2.length - gap)
    s = substring(ls2, 0, end)
    return list(s.coords)


def spiral_poly(poly, entry, s=15.0, edge=10.0, mitre=True):
    """poly: mahal iç poligonu (cm). entry: giriş noktası. Dönüş: yol (gidiş+dönüş tek polilin)."""
    js = dict(join_style=2, mitre_limit=5.0) if mitre else {}
    base = _largest(poly.buffer(-edge, **js))
    if base is None:
        return []
    d = 2 * s
    sup, ret = [], []
    i = 0
    while True:
        g = _largest(base.buffer(-i * d, **js)) if i else base
        if g is None or g.area < (d * d) or min(g.bounds[2] - g.bounds[0], g.bounds[3] - g.bounds[1]) < s:
            break
        sup.append(g)
        h = _largest(base.buffer(-(i * d + s), **js))
        if h is not None and h.area > s * s and min(h.bounds[2] - h.bounds[0], h.bounds[3] - h.bounds[1]) > s * 0.6:
            ret.append(h)
        i += 1
        if i > 60:
            break
    if not sup:
        return []
    path = []
    for k, g in enumerate(sup):
        seg = _open_ring(g, entry, d, ccw=True)
        if path:
            path.append(seg[0])
        path += seg
    rrev = []
    for h in ret:
        seg = _open_ring(h, entry, d, ccw=False)
        rrev += seg
    rpath = rrev[::-1]
    return path + rpath


def split_poly(poly, parts):
    """poligonu uzun ekseni boyunca 'parts' eşit alana böl"""
    if parts <= 1:
        return [poly]
    x0, y0, x1, y1 = poly.bounds
    horiz = (x1 - x0) >= (y1 - y0)
    out = []
    tot = poly.area
    lo = x0 if horiz else y0
    hi = x1 if horiz else y1
    prev = lo
    for k in range(1, parts):
        target = tot * k / parts
        a, b = prev, hi
        for _ in range(40):
            m = (a + b) / 2
            cut = box(lo, y0, m, y1) if horiz else box(x0, lo, x1, m)
            if poly.intersection(cut).area < target:
                a = m
            else:
                b = m
        out.append(m)
        prev = m
    edges = [lo] + out + [hi]
    res = []
    for k in range(parts):
        cut = box(edges[k], y0, edges[k + 1], y1) if horiz else box(x0, edges[k], x1, edges[k + 1])
        g = _largest(poly.intersection(cut))
        if g is not None:
            res.append(g)
    return res
