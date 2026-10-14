"""R3 (14.10.2026 B talimatı) güzergâh yardımcıları.

Temiz su (atlatmasız, kesişmesiz kurgu):
  * Düzlemde "sıcak + soğuk paralel çift hattın" bir T ile dallanması kesişmesiz çizilemez (topolojik zorunluluk:
    üç kolun her birinde S ve SC yan yana ise çevre sırasında S/SC dönüşümlü gelir). Bu yüzden R3 kurgusu:
      - SICAK SU TEK HAT (dallanmasız): kombiden başlar, sıcak su alan armatürleri SIRAYLA dolaşır (armatür bağlantısı
        hat üzerinde, düşey çıkış),
      - SOĞUK SU bu hattın tamamı boyunca 10 cm PARALEL yürür (çift hat, aynı eksenin iki yanında ±5 cm),
      - yalnız soğuk alan armatürler (klozet, ÇM, BM) ve daire girişi soğuk hatta SOĞUK TARAFTAN tek branşmanla bağlanır;
        A* ızgarasında sıcak hat engel (geçilemez) olduğundan kesişme oluşmaz, köprü/atlatma çizilmez.
  * Maliyet alanı: duvardan uzaklık arttıkça ucuz (koridor ve ıslak hacim ORTASI), yatak odası / salon pahalı ve orada
    duvara yakın bant ucuz (ebeveyn banyosu geçişi), duvar delme cezası, betonarme / asansör / enerji odası yasak,
    başka dairenin mahalleri kapalı (kapılardan yürüme mesafesiyle daire etiketi).
Pis su: kolondan en uzak armatüre 45° kırıklı ana hat (balık sırtı omurgası), diğer armatürler omurgaya 45° tekil
  branşmanla (seri zincir yok); branşmanlar aynı yanda paralel olduğundan kesişmez, kesişirse doğrudan kolona bağlanır.
"""
import math
import numpy as np
from shapely.geometry import LineString, Point, Polygon, box, MultiLineString
from shapely.ops import unary_union, nearest_points

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def plen(pts):
    return sum(_d(a, b) for a, b in zip(pts[:-1], pts[1:]))


# ================================================================== ızgara maliyet alanı
class Alan:
    """kat penceresi üzerinde 4 cm ızgara: taban maliyeti, yasak, daire etiketi"""

    def __init__(self, RT, M, d, k, rooms, step=4.0):
        from scipy import ndimage
        from skimage.draw import line as skl, polygon as skp
        self.RT, self.step = RT, step
        w = M.win(k)
        self.w = w
        g = RT.Grid((w[0], w[1], w[2], w[3]), step=step)
        nx, ny = g.nx, g.ny
        self.nx, self.ny = nx, ny
        x0, y0 = w[0], w[1]
        ij = lambda p: (int(round((p[0] - x0) / step)), int(round((p[1] - y0) / step)))

        def raster_lines(lines):
            img = np.zeros((nx, ny), bool)
            for ls in lines:
                cs = list(ls.coords)
                for a, b in zip(cs[:-1], cs[1:]):
                    ia, ja = ij(a); ib, jb = ij(b)
                    rr, cc = skl(ia, ja, ib, jb)
                    ok = (rr >= 0) & (rr < nx) & (cc >= 0) & (cc < ny)
                    img[rr[ok], cc[ok]] = True
            return img

        def raster_poly(pg):
            m = np.zeros((nx, ny), bool)
            for g1 in (pg.geoms if hasattr(pg, 'geoms') else [pg]):
                xs, ys = g1.exterior.coords.xy
                rr, cc = skp([(x - x0) / step for x in xs], [(y - y0) / step for y in ys], (nx, ny))
                m[rr, cc] = True
            return m
        self.raster_poly = raster_poly
        self.raster_lines = raster_lines
        wall = raster_lines(d['W'].ls)
        dist = ndimage.distance_transform_edt(~wall) * step
        base = 1.0 + 2.2 * np.exp(-dist / 18.0)                 # orta tercihli (koridor / mahal ortası)
        base += 20.0 * (dist < 3.0)                               # duvar delme cezası
        self.oda = np.zeros((nx, ny), bool)
        for r in rooms:
            nm = r['name'].split()[0]
            if nm in ('yatak', 'oda', 'salon') and r['area'] <= 40:
                m = raster_poly(r['poly'].buffer(-3))
                self.oda |= m
        # yatak odası / salon: pahalı, duvara yakın (12-30 cm) bant ucuz -> ebeveyn banyosu beslemesi duvar dibinden
        odab = 4.0 + 1.6 * np.clip((dist - 14.0) / 25.0, 0, 1) + 20.0 * (dist < 3.0)
        base = np.where(self.oda, odab, base)
        block = np.zeros((nx, ny), bool)
        for z in d['YASAK']:
            block |= raster_poly(z['g'].buffer(6))
        for sh in d.get('SAFT', []):                   # mekanik havalandırma şaftından temiz su geçmez
            block |= raster_poly(sh['g'].buffer(2))
        self.base, self.block, self.dist = base.astype(np.float32), block, dist
        # daire etiketi: kapılardan yürüme mesafesi (gerçek duvar + betonarme engel)
        from skimage.graph import MCP_Geometric
        gw = raster_lines(d['W'].ls)
        for c in d['cols']:
            gw |= raster_poly(c)
        gw = ndimage.binary_dilation(gw, iterations=1)
        if d.get('HULL') is not None:                 # bina dışı kapalı (dış cepheden sızma yok)
            gw |= ~raster_poly(d['HULL'].buffer(10))
        cost = np.where(gw, 1e6, 1.0)
        best, lab = None, None
        self.dno = []
        for p, n in d['digits']:
            cum, _ = MCP_Geometric(cost).find_costs([ij(p)])
            if best is None:
                best, lab = cum, np.full((nx, ny), n, np.int16)
            else:
                m = cum < best
                lab[m] = n
                best = np.minimum(best, cum)
            self.dno.append(n)
        self.lab = lab
        self.ij = ij

    def grid(self, mask_ok=None, bounds=None, yumusak=6.0):
        """alt ızgara (RT.Grid) - mask_ok dışı hücreler yasak"""
        RT, s = self.RT, self.step
        if bounds is None:
            i0, j0, i1, j1 = 0, 0, self.nx - 1, self.ny - 1
        else:
            i0, j0 = self.ij((bounds[0], bounds[1])); i1, j1 = self.ij((bounds[2], bounds[3]))
            i0, j0 = max(0, i0), max(0, j0); i1, j1 = min(self.nx - 1, i1), min(self.ny - 1, j1)
        x0, y0 = self.w[0] + i0 * s, self.w[1] + j0 * s
        g = RT.Grid((x0, y0, x0 + (i1 - i0) * s, y0 + (j1 - j0) * s), step=s)
        sl = (slice(i0, i0 + g.nx), slice(j0, j0 + g.ny))
        g.base = self.base[sl].copy()
        g.block = self.block[sl].copy()
        if mask_ok is not None:                     # başka daire / ortak alan: yasak değil, pahalı (sızıntılı etiket)
            g.base += np.where(mask_ok[sl], 0.0, yumusak).astype(np.float32)
        g._sl = sl
        return g


def blok_cizgi(g, lines, r):
    """ızgarada çizgilerin r (cm) yakınını yasakla; dönüş: maske"""
    from shapely.geometry import MultiLineString as MLS
    m = np.zeros_like(g.block)
    for ls in lines:
        if ls is None or ls.is_empty:
            continue
        pg = ls.buffer(r, cap_style=2 if r > 0 else 1)
        from skimage.draw import polygon as skp
        for g1 in (pg.geoms if hasattr(pg, 'geoms') else [pg]):
            xs, ys = g1.exterior.coords.xy
            rr, cc = skp([(x - g.x0) / g.s for x in xs], [(y - g.y0) / g.s for y in ys], (g.nx, g.ny))
            m[rr, cc] = True
    return m


def disk(g, p, r):
    ii, jj = np.mgrid[0:g.nx, 0:g.ny]
    return (g.x0 + ii * g.s - p[0]) ** 2 + (g.y0 + jj * g.s - p[1]) ** 2 <= r * r


# ================================================================== paralel öteleme (ortogonal / genel çoklu çizgi)
def otele(pts, dd):
    """çoklu çizgiyi sol normali yönünde dd kadar ötele (miter birleşim)"""
    pts = [p for i, p in enumerate(pts) if i == 0 or _d(p, pts[i - 1]) > 0.05]
    if len(pts) < 2:
        return pts
    ns = []
    for a, b in zip(pts[:-1], pts[1:]):
        L = _d(a, b)
        ns.append((-(b[1] - a[1]) / L, (b[0] - a[0]) / L))
    out = [(pts[0][0] + ns[0][0] * dd, pts[0][1] + ns[0][1] * dd)]
    for j in range(1, len(pts) - 1):
        n1, n2 = ns[j - 1], ns[j]
        c = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]
        if c < 0.2:                                   # neredeyse geri dönüş: iki nokta
            out.append((pts[j][0] + n1[0] * dd, pts[j][1] + n1[1] * dd))
            out.append((pts[j][0] + n2[0] * dd, pts[j][1] + n2[1] * dd))
        else:
            out.append((pts[j][0] + dd * (n1[0] + n2[0]) / c, pts[j][1] + dd * (n1[1] + n2[1]) / c))
    out.append((pts[-1][0] + ns[-1][0] * dd, pts[-1][1] + ns[-1][1] * dd))
    return out


def temizle(pts):
    """kısa (<1,5 cm) parçaları ve geri dönüşleri at, eşdoğrusalları birleştir"""
    if len(pts) < 2:
        return pts
    pts = collinear(pts)
    for _ in range(5):
        out = [pts[0]]
        for p in pts[1:]:
            if _d(p, out[-1]) < 1.5 and p is not pts[-1]:
                continue
            if len(out) >= 2:
                a, b = out[-2], out[-1]
                if (b[0] - a[0]) * (p[0] - b[0]) + (b[1] - a[1]) * (p[1] - b[1]) < 0 and \
                        abs((b[0] - a[0]) * (p[1] - b[1]) - (b[1] - a[1]) * (p[0] - b[0])) < 1e-6:
                    out[-1] = p if _d(a, p) > 0.05 else out[-1]
                    continue
            out.append(p)
        if len(out) < 2:
            break
        pts = collinear(out)
    return pts


def duzelt(pts, sabit=(), min_len=12.0):
    """ortogonal eksende Z-kırıklarını (iki paralel parça arasında < min_len dik parça) kaldır: kırığın bir yanındaki parça
    kırık kadar kaydırılır (sabit noktalar - armatür bağlantıları - kaydırılmaz). Öteleme (±5 cm) ilmek yapmasın diye."""
    pts = temizle(list(pts))
    fix = lambda p: any(_d(p, q) < 0.5 for q in sabit)
    for _ in range(60):
        ch = False
        n = len(pts)
        for i in range(1, n - 2):
            a, b, c, e = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
            if _d(b, c) >= min_len:
                continue
            d0 = (b[0] - a[0], b[1] - a[1]); d2 = (e[0] - c[0], e[1] - c[1])
            if d0[0] * d2[0] + d0[1] * d2[1] <= 0:
                continue
            j = (c[0] - b[0], c[1] - b[1])
            if not fix(a) and not fix(b) and i - 1 > 0:
                pts[i - 1] = (a[0] + j[0], a[1] + j[1]); pts[i] = c
            elif not fix(c) and not fix(e) and i + 2 < n - 1:
                pts[i + 2] = (e[0] - j[0], e[1] - j[1]); pts[i + 1] = b
            else:
                continue
            pts = temizle(pts); ch = True
            break
        if not ch:
            break
    return pts


def agacta_kes(pth, agac):
    """branşmanı ağaca İLK değdiği noktada bitir (uç yuvarlamasıyla ağacı kesip geçmesin)"""
    if not agac or len(pth) < 2:
        return pth
    from shapely.ops import unary_union
    U = unary_union(agac)
    for i, (a, b) in enumerate(zip(pth[:-1], pth[1:])):
        seg = LineString([a, b])
        it = seg.intersection(U)
        if it.is_empty:
            continue
        pts = []
        for g in (it.geoms if hasattr(it, 'geoms') else [it]):
            pts += list(g.coords)
        pts = [p for p in pts if not (i == 0 and _d(p, a) < 0.3)]
        if not pts:
            continue
        p = min(pts, key=lambda p_: _d(p_, a))
        return collinear(pth[:i + 1] + [p]) if _d(p, pth[i]) > 0.05 else pth[:i + 1]
    return pth


def collinear(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if _d(p, out[-1]) > 0.05:
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


# ================================================================== kesişme sayımı
def kesisimler(items, uc_tol=0.6):
    """items: [(grup, tip, LineString)] - aynı ağ içinde (grup eşit) T birleşimi (bir hattın UCU diğerinin üstünde)
    serbest; diğer her temas kesişme sayılır. tip çiftine göre sözlük döner."""
    from shapely import STRtree
    geoms = [it[2] for it in items]
    tree = STRtree(geoms)
    out = []
    for i, (gi, ti, a) in enumerate(items):
        for j in tree.query(a):
            if j <= i:
                continue
            gj, tj, b = items[j]
            if a.distance(b) > 0.3:
                continue
            it = a.intersection(b)
            if it.is_empty:
                it = Point(nearest_points(a, b)[0])
            pts = []
            for g1 in (it.geoms if hasattr(it, 'geoms') else [it]):
                if g1.geom_type == 'Point':
                    pts.append(g1)
                elif g1.length > 0.5:
                    pts.append(None)                   # üst üste binme
                else:
                    pts.append(g1.centroid)
            ea = [Point(a.coords[0]), Point(a.coords[-1])]
            eb = [Point(b.coords[0]), Point(b.coords[-1])]
            for p in pts:
                if p is None:
                    out.append((ti, tj, gi, gj, None)); continue
                ucta = min(p.distance(e) for e in ea) < uc_tol
                uctb = min(p.distance(e) for e in eb) < uc_tol
                if gi == gj and ti == tj and (ucta or uctb):
                    continue                          # aynı ağ, T birleşimi / zincir ucu
                if ti == tj and ucta and uctb:
                    continue                          # ortak düğüm (ör. aynı ADK kolonundan çıkan iki ana hat)
                out.append((ti, tj, gi, gj, (round(p.x, 1), round(p.y, 1))))
    return out


# ================================================================== pis su: balık sırtı
def oktilineer(a, b, once='orto'):
    """a -> b: bir dik + bir 45° parça (45° dirsek)"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    m = min(abs(dx), abs(dy))
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    if abs(dx) >= abs(dy):
        orto = (sx * (abs(dx) - m), 0.0)
    else:
        orto = (0.0, sy * (abs(dy) - m))
    diag = (sx * m, sy * m)
    if once == 'orto':
        q = (a[0] + orto[0], a[1] + orto[1])
    else:
        q = (a[0] + diag[0], a[1] + diag[1])
    return collinear([a, q, b])


def balik_sirti(fx_pts, kp, maliyet):
    """fx_pts: [(anahtar, nokta)] ; kp: kolon. maliyet(pts)->sayı (duvar/yasak cezası).
    Dönüş: omurga noktaları (uçtan kolona), branşmanlar [(anahtar, [P, Q], parça_indeksi, s)], omurga anahtarı"""
    if not fx_pts:
        return None
    far = max(fx_pts, key=lambda t: _d(t[1], kp))
    cands = [oktilineer(far[1], kp, 'orto'), oktilineer(far[1], kp, 'diag')]
    spine = min(cands, key=lambda c: (maliyet(c), plen(c)))
    branches = []
    spl = LineString(spine)
    for key, P in sorted([t for t in fx_pts if t is not far], key=lambda t: _d(t[1], kp)):
        opts = []
        for i, (A, B) in enumerate(zip(spine[:-1], spine[1:])):
            L = _d(A, B)
            if L < 1e-6:
                continue
            u = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
            t = (P[0] - A[0]) * u[0] + (P[1] - A[1]) * u[1]
            h = abs((P[0] - A[0]) * u[1] - (P[1] - A[1]) * u[0])
            s = t + h
            if h < 2.0:
                s = t
            if 0.0 <= s <= L:
                Q = (A[0] + u[0] * s, A[1] + u[1] * s)
                br = [P, Q]
                opts.append((maliyet(br) + _d(P, Q), br, 'omurga'))
        for o in ('orto', 'diag'):
            br = oktilineer(P, kp, o)
            opts.append((maliyet(br) + plen(br) + 25.0, br, 'kolon'))
        opts.sort(key=lambda t: t[0])
        sec = None
        for sc, br, tip in opts:
            ls = LineString(br)
            bad = False
            for _, b2, _ in branches:
                l2 = LineString(b2)
                if ls.distance(l2) < 0.3:
                    it = ls.intersection(l2)
                    if not it.is_empty and not (it.geom_type == 'Point' and (_d((it.x, it.y), br[-1]) < 0.6)):
                        bad = True; break
            if not bad:
                # omurgayı yalnız ucunda değmeli
                it = ls.intersection(spl)
                if not it.is_empty:
                    pts = [g for g in (it.geoms if hasattr(it, 'geoms') else [it])]
                    if any(g.geom_type != 'Point' or _d((g.x, g.y), br[-1]) > 0.6 for g in pts):
                        bad = True
            if not bad:
                sec = (br, tip); break
        if sec is None:
            sec = (opts[0][1], opts[0][2])
        branches.append((key, sec[0], sec[1]))
    return spine, far[0], branches
