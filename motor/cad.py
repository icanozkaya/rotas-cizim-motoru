"""Kayıt tabanlı çizim çekirdeği + MTY/ROTAŞ gerçek semboller (birim cm)."""
import math

R = []                      # kayıtlar
_TF = [(1, 0, 0, 0, 1, 0)]  # afin dönüşüm yığını (a,b,c,d,e,f): x'=a x+b y+c


def tf():
    return _TF[-1]


def push(m):
    a, b, c, d, e, f = tf()
    A, B, C, D, E, F = m
    _TF.append((a * A + b * D, a * B + b * E, a * C + b * F + c, d * A + e * D, d * B + e * E, d * C + e * F + f))


def pop():
    _TF.pop()


def P(p):
    a, b, c, d, e, f = tf()
    return (a * p[0] + b * p[1] + c, d * p[0] + e * p[1] + f)


def mirrored():
    a, b, c, d, e, f = tf()
    return a * e - b * d < 0


def SCALE(o, k):
    return (k, 0, o[0] * (1 - k), 0, k, o[1] * (1 - k))


def MOVE(dx, dy):
    return (1, 0, dx, 0, 1, dy)


def MX(x0):
    return (-1, 0, 2 * x0, 0, 1, 0)


def MY(y0):
    return (1, 0, 0, 0, -1, 2 * y0)


def ROT(c, ang):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    return (ca, -sa, c[0] - ca * c[0] + sa * c[1], sa, ca, c[1] - sa * c[0] - ca * c[1])


# ------------------------------------------------------------------ ilkel
def L(a, b, lay):
    R.append(('L', lay, P(a), P(b)))


def PL(pts, lay, closed=False, w=0):
    if len(pts) > 1:
        R.append(('P', lay, [P(p) for p in pts], closed, w))


def SC():
    a, b, c, d, e, f = tf()
    return math.sqrt(abs(a * e - b * d))


def C(c, r, lay):
    R.append(('C', lay, P(c), r * SC()))


def SOL(p1, p2, p3, lay):
    R.append(('S', lay, P(p1), P(p2), P(p3)))


def T(p, s, h, lay, al='L', rot=0):
    """al: L, C, R, ML, MC, MR, TL, TC"""
    if mirrored() and al in ('L', 'R', 'ML', 'MR'):
        pass
    R.append(('T', lay, P(p), str(s), h * SC(), rot, al))


def ARC(c, r, a0, a1, lay, n=None):
    if n is None:
        n = max(6, int(abs(a1 - a0) / 10))
    PL([(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
         c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)], lay)


def ELL(c, rx, ry, lay, a0=0, a1=360, n=36):
    PL([(c[0] + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
         c[1] + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)], lay)


def RECT(x0, y0, x1, y1, lay):
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, closed=True)


def RRECT(x0, y0, x1, y1, r, lay):
    pts = []
    for cx, cy, a in ((x1 - r, y0 + r, 270), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(5):
            t = math.radians(a + 90 * i / 4)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    PL(pts, lay, closed=True)


def ARROW(p, ang, lay, s=15):
    a = math.radians(ang)
    b1 = (p[0] - s * math.cos(a) + 0.35 * s * math.sin(a), p[1] - s * math.sin(a) - 0.35 * s * math.cos(a))
    b2 = (p[0] - s * math.cos(a) - 0.35 * s * math.sin(a), p[1] - s * math.sin(a) + 0.35 * s * math.cos(a))
    SOL(p, b1, b2, lay)


def plen(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


# yönlü yerleşim: yerel (u: duvar boyunca, v: duvardan içeri) -> dünya
DIRS = {'N': 0, 'E': -90, 'S': 180, 'W': 90}   # v ekseninin yönü: N = +y


class Local:
    def __init__(self, o, d):
        self.o, self.a = o, DIRS[d] if isinstance(d, str) else d

    def __enter__(self):
        push((1, 0, self.o[0], 0, 1, self.o[1]))
        push(ROT((0, 0), self.a))
        return self

    def __exit__(self, *e):
        pop(); pop()


# ------------------------------------------------------------------ armatürler (plan)
def WC(o, d, lay):
    """Alafranga klozet + gömme/dış rezervuar; o: duvar üzerindeki orta nokta, d: duvardan içeri yön."""
    with Local(o, d):
        RRECT(-21, 0, 21, 17, 3, lay)                 # rezervuar
        RRECT(-17, 3, 17, 14, 2, lay)
        C((0, 8.5), 2.2, lay)                          # basma butonu
        PL([(-17, 17), (-18, 30)], lay); PL([(17, 17), (18, 30)], lay)
        ELL((0, 40), 18, 26, lay, 180, 360 + 180, 40)  # dış hazne (oval)
        ELL((0, 41), 12.5, 19, lay)                    # iç hazne
        L((-18, 30), (-18, 40), lay); L((18, 30), (18, 40), lay)


def LAVABO(o, d, lay, w=55, dp=45):
    with Local(o, d):
        RRECT(-w / 2, 0, w / 2, dp, 4, lay)
        ELL((0, dp * 0.55), w * 0.33, dp * 0.3, lay)
        C((0, dp * 0.5), 1.8, lay)
        RRECT(-3, 3, 3, 10, 1, lay)                    # batarya
        L((0, 10), (0, 15), lay)
        C((-9, 7), 2, lay); C((9, 7), 2, lay)


def DUS(x0, y0, x1, y1, lay):
    RRECT(x0, y0, x1, y1, 3, lay)
    RRECT(x0 + 5, y0 + 5, x1 - 5, y1 - 5, 6, lay)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    C((cx, cy), 4.5, lay); C((cx, cy), 2, lay)
    for px, py in ((x0 + 5, y0 + 5), (x1 - 5, y0 + 5), (x1 - 5, y1 - 5), (x0 + 5, y1 - 5)):
        L((cx + (px - cx) * 0.18, cy + (py - cy) * 0.18), (px + (cx - px) * 0.05, py + (cy - py) * 0.05), lay)


def EVIYE(o, d, lay, w=80, dp=50):
    with Local(o, d):
        RECT(-w / 2, 0, w / 2, dp, lay)
        RRECT(-w / 2 + 5, 7, -1, dp - 6, 4, lay)       # hazne
        C(((-w / 2 + 4) / 2, dp / 2 + 1), 2.5, lay)
        for i in range(5):                              # damlalık
            x = 6 + i * (w / 2 - 12) / 4
            L((x, 10), (x, dp - 9), lay)
        RRECT(-4, 2, 2, 7, 1, lay)                      # batarya
        L((-1, 7), (-6, 18), lay)


def MAKINE(c, lay, kind='CM', s=60):
    x, y = c
    RRECT(x - s / 2, y - s / 2, x + s / 2, y + s / 2, 3, lay)
    if kind == 'CM':
        C((x, y - 2), s * 0.33, lay); C((x, y - 2), s * 0.25, lay)
        L((x - s / 2 + 3, y + s / 2 - 9), (x + s / 2 - 3, y + s / 2 - 9), lay)
        C((x + s / 2 - 10, y + s / 2 - 5), 2, lay)
    else:
        RRECT(x - s / 2 + 5, y - s / 2 + 5, x + s / 2 - 5, y + s / 2 - 14, 2, lay)
        L((x - s / 2 + 3, y + s / 2 - 9), (x + s / 2 - 3, y + s / 2 - 9), lay)
        for i in range(3):
            C((x - 10 + i * 10, y + s / 2 - 5), 1.5, lay)
        T((x, y - 6), 'BM', 9, lay, 'MC')


def YER_SUZGECI(c, lay, s=15):
    x, y = c
    RECT(x - s / 2, y - s / 2, x + s / 2, y + s / 2, lay)
    C(c, s * 0.35, lay)
    for i in (-1, 0, 1):
        L((x + i * s * 0.18, y - s * 0.3), (x + i * s * 0.18, y + s * 0.3), lay)


def KOMBI_PLAN(o, d, lay, txt=True):
    """Duvara asılı hermetik kombi (plan): gövde + ön panel + baca."""
    with Local(o, d):
        RRECT(-20, 0, 20, 32, 2, lay)
        RECT(-17, 25, 17, 31, lay)                      # ön panel
        C((0, 13), 6, lay); C((0, 13), 3.5, lay)        # koaksiyel baca
        for i in range(4):
            L((-14 + i * 9.3, 3), (-14 + i * 9.3, 0), lay)
    if txt:
        pass


def KOLLEKTOR_PLAN(o, d, n, lay):
    """Yerden ısıtma kollektör dolabı (plan): dolap + gidiş/dönüş barası + ağızlar."""
    w = 20 + 9 * n
    with Local(o, d):
        RECT(-w / 2, 0, w / 2, 14, lay)
        L((-w / 2 + 4, 5), (w / 2 - 4, 5), lay)
        L((-w / 2 + 4, 10), (w / 2 - 4, 10), lay)
        for i in range(n):
            x = -w / 2 + 14 + i * 9
            C((x, 5), 1.6, lay); C((x, 10), 1.6, lay)
    return w


def port(o, d, n, i, which):
    """kollektör ağzının dünya koordinatı (yerel)"""
    w = 20 + 9 * n
    x = -w / 2 + 14 + i * 9
    with Local(o, d):
        return P((x + (1.5 if which == 'R' else -1.5), 14))


# ------------------------------------------------------------------ vana vb.
def VANA(c, k=1.0, ang=0, lay='MTY-VANA'):
    push(ROT(c, ang))
    w, h = 6 * k, 3.6 * k
    PL([(c[0] - w, c[1] + h), (c[0] + w, c[1] - h), (c[0] + w, c[1] + h), (c[0] - w, c[1] - h)], lay, closed=True)
    L(c, (c[0], c[1] + 6 * k), lay)
    L((c[0] - 3.5 * k, c[1] + 6 * k), (c[0] + 3.5 * k, c[1] + 6 * k), lay)
    pop()


def CEKVALF(c, k=1.0, ang=0, lay='MTY-VANA'):
    push(ROT(c, ang))
    w, h = 6 * k, 3.6 * k
    PL([(c[0] - w, c[1] + h), (c[0] + w, c[1] - h), (c[0] + w, c[1] + h), (c[0] - w, c[1] - h)], lay, closed=True)
    SOL((c[0] + w, c[1] + h), (c[0] + w, c[1] - h), c, lay)
    pop()


def PISLIK_TUTUCU(c, k=1.0, ang=0, lay='MTY-VANA'):
    push(ROT(c, ang))
    w, h = 6 * k, 3.6 * k
    PL([(c[0] - w, c[1] + h), (c[0] + w, c[1] - h), (c[0] + w, c[1] + h), (c[0] - w, c[1] - h)], lay, closed=True)
    PL([(c[0], c[1]), (c[0] + 4 * k, c[1] - 7 * k)], lay)
    PL([(c[0] + 2 * k, c[1] - 9 * k), (c[0] + 6 * k, c[1] - 5 * k)], lay)
    pop()


def SAYAC(c, k=1.0, ang=0, lay='MTY-VANA'):
    """Su sayacı: gövde + kadran."""
    push(ROT(c, ang))
    RECT(c[0] - 7 * k, c[1] - 3 * k, c[0] + 7 * k, c[1] + 3 * k, lay)
    C(c, 4.5 * k, lay)
    L((c[0] - 2.5 * k, c[1] - 1.5 * k), (c[0] + 2.5 * k, c[1] + 1.5 * k), lay)
    pop()


def POMPA(c, r=10.0, ang=0, lay='MTY-CIHAZ'):
    C(c, r, lay)
    push(ROT(c, ang))
    PL([(c[0] + r * 0.75, c[1]), (c[0] - r * 0.45, c[1] + r * 0.55), (c[0] - r * 0.45, c[1] - r * 0.55)], lay, closed=True)
    pop()


def MANOMETRE(c, k=1.0, lay='MTY-CIHAZ'):
    L(c, (c[0], c[1] + 6 * k), lay)
    C((c[0], c[1] + 10.5 * k), 4.5 * k, lay)
    L((c[0], c[1] + 10.5 * k), (c[0] + 3 * k, c[1] + 13.5 * k), lay)


def TERMOMETRE(c, k=1.0, lay='MTY-CIHAZ'):
    L(c, (c[0], c[1] + 6 * k), lay)
    RRECT(c[0] - 2 * k, c[1] + 6 * k, c[0] + 2 * k, c[1] + 18 * k, 1.5 * k, lay)
    C((c[0], c[1] + 6 * k), 2.6 * k, lay)


def MEMBRANLI_TANK(c, w, h, lay='MTY-CIHAZ'):
    x, y = c; r = w / 2
    PL([(x - r, y - h / 2 + r), (x - r, y + h / 2 - r)], lay)
    PL([(x + r, y - h / 2 + r), (x + r, y + h / 2 - r)], lay)
    ARC((x, y + h / 2 - r), r, 0, 180, lay)
    ARC((x, y - h / 2 + r), r, 180, 360, lay)
    ARC((x, y + h * 0.05), r * 0.95, 200, 340, lay, 10)
    L((x - r * 0.7, y - h / 2 + r * 0.3), (x - r * 0.9, y - h / 2 - r * 0.25), lay)
    L((x + r * 0.7, y - h / 2 + r * 0.3), (x + r * 0.9, y - h / 2 - r * 0.25), lay)


def DALGIC_POMPA(c, k=1.0, lay='MTY-CIHAZ'):
    x, y = c
    PL([(x - 8 * k, y), (x + 8 * k, y), (x + 8 * k, y + 22 * k), (x - 8 * k, y + 22 * k)], lay, closed=True)
    for i in range(4):
        L((x - 8 * k, y + 5 * k + i * 4.5 * k), (x - 11 * k, y + 5 * k + i * 4.5 * k), lay)
        L((x + 8 * k, y + 5 * k + i * 4.5 * k), (x + 11 * k, y + 5 * k + i * 4.5 * k), lay)
    PL([(x - 10 * k, y), (x + 10 * k, y), (x + 7 * k, y - 7 * k), (x - 7 * k, y - 7 * k)], lay, closed=True)
    L((x, y + 22 * k), (x, y + 30 * k), lay)


def SAMANDIRALI_VANA(c, k=1.0, lay='MTY-VANA'):
    x, y = c
    PL([(x - 6 * k, y + 3.6 * k), (x + 6 * k, y - 3.6 * k), (x + 6 * k, y + 3.6 * k), (x - 6 * k, y - 3.6 * k)], lay, closed=True)
    L((x, y), (x + 4 * k, y - 16 * k), lay)
    C((x + 8 * k, y - 22 * k), 6 * k, lay)


def YB_PLAN(c, r=7.0, lay='MTY-YAGMUR-BORUSU'):
    C(c, r, lay); C(c, r * 0.45, lay)
    L((c[0] - r * 0.7, c[1] - r * 0.7), (c[0] + r * 0.7, c[1] + r * 0.7), lay)


def KOLON(c, r, lay, kind='pis'):
    C(c, r, lay)
    if kind == 'pis':
        L((c[0] - r * 0.7, c[1] - r * 0.7), (c[0] + r * 0.7, c[1] + r * 0.7), lay)
        L((c[0] - r * 0.7, c[1] + r * 0.7), (c[0] + r * 0.7, c[1] - r * 0.7), lay)
    else:
        C(c, r * 0.35, lay)


def ROGAR_PLAN(c, s, lay='MTY-ROGAR'):
    x, y = c
    RECT(x - s, y - s, x + s, y + s, lay)
    RECT(x - s + 7, y - s + 7, x + s - 7, y + s - 7, lay)
    C(c, s * 0.55, lay)
    L((x - s * 0.4, y), (x + s * 0.4, y), lay)


def TEMIZLEME_KAPAGI(c, k=1.0, lay='MTY-PIS-SU-BORUSU'):
    x, y = c
    RECT(x - 5 * k, y - 2 * k, x + 5 * k, y + 2 * k, lay)
    L((x - 7 * k, y + 2 * k), (x + 7 * k, y + 2 * k), lay)


def HAVALIK_SAPKA(c, k=1.0, lay='MTY-PIS-SU-BORUSU'):
    """Havalık şapkası (şema): boru ucu + şapka."""
    x, y = c
    PL([(x - 10 * k, y + 4 * k), (x, y + 12 * k), (x + 10 * k, y + 4 * k)], lay)
    L((x - 6 * k, y + 2 * k), (x + 6 * k, y + 2 * k), lay)
    L((x - 6 * k, y + 2 * k), (x - 6 * k, y + 4.5 * k), lay)
    L((x + 6 * k, y + 2 * k), (x + 6 * k, y + 4.5 * k), lay)


def HEXTAG(c, lay, zone, temp='20°C', h=10):
    """Isı kaybı mahal etiketi: altıgen + sıcaklık + zon."""
    x, y = c
    w, hh = 34, 20
    PL([(x - w, y), (x - w + 10, y + hh), (x + w - 10, y + hh), (x + w, y), (x + w - 10, y - hh), (x - w + 10, y - hh)], lay, closed=True)
    L((x - w, y), (x + w, y), lay)
    T((x, y + hh / 2), temp, h * 0.85, lay, 'MC')
    T((x, y - hh / 2), zone, h * 0.85, lay, 'MC')


# ------------------------------------------------------------------ serpantin
def _spiral(L, B, Rr, Tp, d):
    pts = [(L, B)]
    while Rr - L > d * 0.9 and Tp - B > d * 0.9:
        pts += [(L, Tp), (Rr, Tp), (Rr, B)]
        if Rr - (L + d) < d * 0.5 or Tp - d - (B + d) < 0:
            break
        pts.append((L + d, B))
        L, Rr, B, Tp = L + d, Rr - d, B + d, Tp - d
    return pts


def spiral(x0, y0, x1, y1, s=15.0, corner=(0, 0), m=10.0):
    """Karşı akışlı salyangoz: gidiş saat yönünde içeri, dönüş gidişin s kadar içine paralel."""
    from shapely.geometry import LineString
    d = 2 * s
    a = _spiral(x0 + m, y0 + m, x1 - m, y1 - m, d)
    if len(a) < 3:
        return a
    def nrm(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]
        l = math.hypot(dx, dy) or 1.0
        return (dy / l, -dx / l)          # sağ taraf (iç)
    b = []
    for i, p in enumerate(a):
        ns = []
        if i > 0:
            ns.append(nrm(a[i - 1], p))
        if i < len(a) - 1:
            ns.append(nrm(p, a[i + 1]))
        ox = sum(n[0] for n in ns) * s if len(ns) == 2 else ns[0][0] * s
        oy = sum(n[1] for n in ns) * s if len(ns) == 2 else ns[0][1] * s
        b.append((p[0] + ox, p[1] + oy))
    # son parçayı s kadar kısalt (merkez dönüşü)
    if len(a) >= 2:
        p, q = b[-2], b[-1]
        l = math.hypot(q[0] - p[0], q[1] - p[1])
        if l > 2 * s:
            b[-1] = (q[0] - (q[0] - p[0]) / l * s, q[1] - (q[1] - p[1]) / l * s)
            p, q = a[-2], a[-1]
            a[-1] = (q[0] - (q[0] - p[0]) / l * s, q[1] - (q[1] - p[1]) / l * s) if False else a[-1]
    path = a + list(reversed(b))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if corner[0]:
        path = [(2 * cx - x, y) for x, y in path]
    if corner[1]:
        path = [(x, 2 * cy - y) for x, y in path]
    return path
