"""Dik açılı (rektilineer) poligon için karşı akışlı (bifilar / salyangoz) yerden ısıtma serpantini.

poly : boru bölgesinin dış sınırı (duvardan kenar mesafesi zaten düşülmüş), saat yönünün tersine köşe listesi
entry: giriş köşesi indeksi (dışbükey köşe)
first: 'a' -> girişten sonra köşeden çıkan ilk kenar boyunca ilerle (poligon sırası), 'b' -> ters yön
s    : boru aralığı (gidiş ile dönüş arası)
Dönüş: (gidiş yolu, dönüş yolu) -- gidiş[0] ve dönüş[-1] giriş köşesinde; bağlantı ayakları -v yönünde çıkar.
"""
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
import math


def _largest(g):
    if g is None or g.is_empty:
        return None
    if isinstance(g, MultiPolygon):
        g = max(g.geoms, key=lambda p: p.area)
    if not isinstance(g, Polygon):
        return None
    return g


def _ring(poly):
    c = list(poly.exterior.coords)[:-1]
    # ardışık eşdoğrusal noktaları temizle
    out = []
    n = len(c)
    for i in range(n):
        a, b, d = c[i - 1], c[i], c[(i + 1) % n]
        cr = (b[0] - a[0]) * (d[1] - b[1]) - (b[1] - a[1]) * (d[0] - b[0])
        if abs(cr) > 1e-6:
            out.append((round(b[0], 3), round(b[1], 3)))
    if Polygon(out).exterior.is_ccw is False:
        out = out[::-1]
    return out


def _unit(p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    l = math.hypot(dx, dy) or 1.0
    return (dx / l, dy / l)


def _spiral_from(base, corner, first_dir, d, mitre=True):
    """base poligon halkalarından (ofset d adımlı) tek yönlü salyangoz üret."""
    pts = []
    k = 0
    cur_corner = corner
    while True:
        g = _largest(base.buffer(-k * d, join_style=2, mitre_limit=10)) if k else base
        if g is None or g.area < 1.0:
            break
        ring = _ring(g)
        # köşeye en yakın tepe
        j = min(range(len(ring)), key=lambda i: math.hypot(ring[i][0] - cur_corner[0], ring[i][1] - cur_corner[1]))
        if math.hypot(ring[j][0] - cur_corner[0], ring[j][1] - cur_corner[1]) > d * 1.6:
            break
        n = len(ring)
        # yön: first_dir ile en uyumlu komşu
        nxt, prv = ring[(j + 1) % n], ring[j - 1]
        un, up = _unit(ring[j], nxt), _unit(ring[j], prv)
        if un[0] * first_dir[0] + un[1] * first_dir[1] >= up[0] * first_dir[0] + up[1] * first_dir[1]:
            seq = [ring[(j + i) % n] for i in range(n)]
        else:
            seq = [ring[(j - i) % n] for i in range(n)]
        u = _unit(seq[0], seq[-1])          # köşeye son kenarla gelen yönün tersi (köşeden 'son kenar' boyunca)
        v = _unit(seq[0], seq[1])
        # halka: köşe -> ... -> son kenarda köşeye d kala dur
        stop = (seq[0][0] + u[0] * d, seq[0][1] + u[1] * d)
        L_last = math.hypot(seq[-1][0] - seq[0][0], seq[-1][1] - seq[0][1])
        if L_last < d * 1.05 or math.hypot(seq[1][0] - seq[0][0], seq[1][1] - seq[0][1]) < d * 1.05:
            # halka çok küçük: köşeden ilk kenar boyunca kısa bir parça ile bitir
            if not pts:
                pts = [seq[0], seq[1]]
            else:
                pts += [seq[0], seq[1]] if pts[-1] != seq[0] else [seq[1]]
            break
        loop = seq + [stop]
        if pts and math.hypot(pts[-1][0] - loop[0][0], pts[-1][1] - loop[0][1]) < 1e-6:
            loop = loop[1:]
        pts += loop
        cur_corner = (seq[0][0] + (u[0] + v[0]) * d, seq[0][1] + (u[1] + v[1]) * d)
        # bir sonraki halkanın köşesine dik in: stop -> next corner (v yönünde d)
        k += 1
        if k > 60:
            break
    # ardışık eşdoğrusal noktaları sadeleştir
    return _simplify(pts)


def _simplify(pts):
    out = []
    for p in pts:
        if out and math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) < 1e-6:
            continue
        out.append(p)
        while len(out) >= 3:
            a, b, c = out[-3], out[-2], out[-1]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            dot = (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])
            if abs(cr) < 1e-6 and dot > 0:
                out.pop(-2)
            else:
                break
    return out


def bifilar(poly_pts, entry, first='a', s=15.0):
    """Karşı akışlı salyangoz. Dönüş: (gidiş, dönüş) yol listeleri; ikisi de giriş köşesinde başlar/biter."""
    P = Polygon(poly_pts)
    if not P.exterior.is_ccw:
        P = Polygon(poly_pts[::-1])
    ring = _ring(P)
    c = poly_pts[entry]
    j = min(range(len(ring)), key=lambda i: math.hypot(ring[i][0] - c[0], ring[i][1] - c[1]))
    n = len(ring)
    a_dir = _unit(ring[j], ring[(j + 1) % n])
    b_dir = _unit(ring[j], ring[j - 1])
    v = a_dir if first == 'a' else b_dir
    u = b_dir if first == 'a' else a_dir
    d = 2 * s
    sup = _spiral_from(P, ring[j], v, d)
    Pr = _largest(P.buffer(-s, join_style=2, mitre_limit=10))
    c2 = (ring[j][0] + (u[0] + v[0]) * s, ring[j][1] + (u[1] + v[1]) * s)
    ret = _spiral_from(Pr, c2, v, d) if Pr is not None else []
    # dönüş ayağı: dönüş spiralinin başı c2'den u ters yönünde değil, -v yönünde dışarı çıkacak:
    # c2 -> (c2 - v*s) noktası gidişin ilk kenarıyla çakışmaz (gidiş c'den başlıyor, dönüş c+u*s hizasında)
    ret_out = (c2[0] - v[0] * s, c2[1] - v[1] * s)
    ret = [ret_out] + ret
    # merkez bağlantısı: gidiş sonu -> dönüş sonu (dik L)
    if sup and ret:
        a_end, r_end = sup[-1], ret[-1]
        if abs(a_end[0] - r_end[0]) > 1e-6 and abs(a_end[1] - r_end[1]) > 1e-6:
            # son gidiş kenarı yönünde mi dik mi? -> önce son kenara dik, sonra paralel
            dlast = _unit(sup[-2], sup[-1]) if len(sup) > 1 else v
            if abs(dlast[0]) > 0.5:   # yatay geliyordu -> dikey in, sonra yatay
                mid = (a_end[0], r_end[1])
            else:
                mid = (r_end[0], a_end[1])
            link = [mid]
        else:
            link = []
        sup_path = sup + link + [r_end]
    else:
        sup_path = sup
    ret_path = list(reversed(ret))
    # tam yol: gidiş + dönüş (merkezde birleşik)
    full = _simplify(sup_path + ret_path[1:])
    return full, dict(start=sup[0] if sup else None, end=ret_out, u=u, v=v)


def check_self(path, s):
    """kendi kendini kesme / çok yaklaşma kontrolü"""
    ls = LineString(path)
    return ls.is_simple


if __name__ == '__main__':
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    tests = [([(0, 0), (300, 0), (300, 200), (0, 200)], 3, 'a'),
             ([(0, 0), (400, 0), (400, 110), (150, 110), (150, 240), (0, 240)], 4, 'b'),
             ([(0, 0), (150, 0), (150, 63), (0, 63)], 3, 'a')]
    fig, axs = plt.subplots(1, 3, figsize=(18, 6))
    for ax, (pp, e, f) in zip(axs, tests):
        full, info = bifilar(pp, e, f, 15)
        xs, ys = zip(*(pp + [pp[0]]))
        ax.plot(xs, ys, 'k--', lw=0.5)
        ax.plot([p[0] for p in full], [p[1] for p in full], 'r-', lw=0.8)
        ax.plot(*full[0], 'go'); ax.plot(*full[-1], 'bo')
        ax.set_aspect('equal'); ax.set_title('simple=%s L=%.1f' % (LineString(full).is_simple, LineString(full).length / 100))
    fig.savefig('/tmp/claude-0/rv/sp_test.png', dpi=80)
