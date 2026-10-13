# -*- coding: utf-8 -*-
"""Ofis yerden ısıtma - onaylı Emine Tunçel (p3/et.py) yöntemi: mahal başına karşı akışlı salyangoz (spiral3.bifilar),
devre ≤ 72 m (ayaklar dahil ≤ 80 m), ayaklar kollektörden hol/giriş + kendi oda kapısından A* ile (başka mahalden geçmez),
hiçbir çizgi üst üste binmez; giriş holü ayaklardan sonra kalan boş alanda ısıtılır.
Isı kaybı mahal bazında gheat.calc_room (TS 2164 / örnek şablon yöntemi).
S çerçevesinde hesap, H sırasına (+30343) çizilir."""
import sys, math, pickle
import numpy as np
from scipy import ndimage
from skimage.segmentation import watershed
from shapely.geometry import Polygon, Point, LineString, box, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import translate
sys.path.append('/home/claude/nb'); sys.path.append('/home/claude/nb/p2')
import spiral3
import gheat as GH
from router import Grid, _collinear
from veri import *
import mahal, odaplan as RM, izgara, yerlesim
from hesap import kenar_sinif, IS1, IS2

GH.KAT_H = 3.00; GH.T_DIS = -3.0; GH.T_CATI = -3.0; GH.T_HOL = 10.0
T_KOMSU = 15.0
HX = ROW['H'][0] - ROW['S'][0]
_K = None


def kat_seg():
    """1. kat mahal bileşenleri; birden çok etiketli bileşen havza (watershed) ile bölünür"""
    global _K
    if _K is not None: return _K
    K = mahal.kat1()
    lab = K.lab.copy()
    names = {}
    nxt = lab.max() + 1
    by = {}
    for l in K.labels:
        if l['ad'] in ('IŞIKLIK',): continue
        c = K.comp_at(l['p'])
        if c: by.setdefault(c, []).append(l)
    for c, ls in by.items():
        if len(ls) == 1:
            names[c] = ls[0]; continue
        m = lab == c
        mk = np.zeros_like(lab)
        ids = []
        for l in ls:
            i, j = K.ij(l['p'])
            mk[max(0, i - 2):i + 3, max(0, j - 2):j + 3] = nxt; ids.append(nxt); names[nxt] = l; nxt += 1
        dist = ndimage.distance_transform_edt(m)
        ws = watershed(-dist, mk, mask=m)
        lab[m] = ws[m]
    K.lab = lab
    K.names = names
    _K = K
    return K


def ofis_mahalleri(k):
    """ofis k'nin mahalleri (1. kat S): [dict(poly, name, A, labeled)]"""
    K = kat_seg()
    op = Polygon(OFIS_S1[k]['poly'])
    out = []
    for c in np.unique(K.lab):
        if c == 0: continue
        m = K.lab == c
        n = m.sum()
        if n * mahal.ST ** 2 < 1.4e4: continue                  # < 1,4 m² (tezgah, vitrifiye)
        ii, jj = np.nonzero(m)
        p = K.xy(ii.mean(), jj.mean())
        try:
            pl = K.poly(c)
        except Exception:
            continue
        if pl.is_empty: continue
        rp = pl.representative_point()
        if not op.contains(rp): continue
        if pl.intersection(op).area < 0.85 * pl.area:                 # ofis dışına taşan (koridor) bileşen: kırp
            pl = pl.intersection(op.buffer(-3))
            if pl.geom_type != 'Polygon': pl = max(getattr(pl, 'geoms', [pl]), key=lambda q: q.area) if not pl.is_empty else pl
            if pl.is_empty or pl.area < 1.4e4: continue
        if pl.area > op.area * 0.95: continue
        l = K.names.get(c)
        nm = l['ad'] if l else 'GİRİŞ HOLÜ'
        A = (l['m2'] if l and l.get('m2') else pl.area / 1e4)
        out.append(dict(poly=pl, name=nm, A=round(A, 2), labeled=l is not None, comp=c))
    return out


def _maxrect(m):
    """ikili maskede en büyük eksen hizalı dikdörtgen (histogram yöntemi): (i0, j0, i1, j1) dahil"""
    nx, ny = m.shape
    h = np.zeros(ny, int); best = (0, None)
    for i in range(nx):
        h = np.where(m[i], h + 1, 0)
        st = []
        for j in range(ny + 1):
            cur = h[j] if j < ny else 0
            start = j
            while st and st[-1][1] >= cur:
                s0, hh = st.pop()
                a = hh * (j - s0)
                if a > best[0]: best = (a, (i - hh + 1, s0, i, j - 1))
                start = s0
            st.append((start, cur))
    return best[1]


def oda_dikdortgenleri(r, ent=False, min_m2=2.5):
    """mahal bileşen maskesinden (duvardan 10 cm) en büyük dikdörtgen(ler)"""
    K = kat_seg()
    full = K.lab == r['comp']
    ii, jj = np.nonzero(full)
    a0, a1, b0, b1 = ii.min(), ii.max() + 1, jj.min(), jj.max() + 1
    from skimage.draw import polygon as _skp
    pm = np.zeros_like(full)
    xs, ys = r['poly'].exterior.coords.xy
    rr, cc = _skp([(x - K.x0) / mahal.ST for x in xs], [(y - K.y0) / mahal.ST for y in ys], full.shape)
    pm[rr, cc] = True
    full = full & pm
    m = ndimage.binary_erosion(full[a0:a1, b0:b1], iterations=1)
    if 'extra_block' in r:
        m &= ~r['extra_block'][a0:a1, b0:b1]
    out = []
    for _ in range(6):
        if len(out) >= 3: break
        rc = _maxrect(m)
        if rc is None: break
        i0, j0, i1, j1 = rc
        a = (i1 - i0 + 1) * (j1 - j0 + 1) * mahal.ST ** 2 / 1e4
        if a < (min_m2 if not out else max(2.0, min_m2)): break
        if min(i1 - i0 + 1, j1 - j0 + 1) * mahal.ST < 55:          # dar şerit: salyangoz olmaz
            m[i0:i1 + 1, j0:j1 + 1] = False
            continue
        x0, y0 = K.xy(i0 + a0, j0 + b0); x1, y1 = K.xy(i1 + a0, j1 + b0)
        out.append(box(x0 + 5, y0 + 5, x1 - 5, y1 - 5))
        m[max(0, i0 - 2):i1 + 3, max(0, j0 - 2):j1 + 3] = False
        if ent: break
    return out


def ortho_poly(pl, d=10.0):
    """duvardan d içeri; dik açılı sadeleştirme (salyangoz için)"""
    g = pl.buffer(-d, join_style=2)
    if g.is_empty: return None
    if g.geom_type == 'MultiPolygon': g = max(g.geoms, key=lambda q: q.area)
    g = g.simplify(6)
    # eksene oturt: kenarları yatay/dikey yap (küçük eğimler)
    c = list(g.exterior.coords)[:-1]
    out = [c[0]]
    for p in c[1:]:
        q = out[-1]
        if abs(p[0] - q[0]) < 8: p = (q[0], p[1])
        elif abs(p[1] - q[1]) < 8: p = (p[0], q[1])
        out.append(p)
    try:
        g2 = Polygon(out).buffer(0)
        if g2.geom_type == 'MultiPolygon': g2 = max(g2.geoms, key=lambda q: q.area)
        return g2 if g2.area > 0.6 * g.area else g
    except Exception:
        return g


def split_poly(g, maxL=72.0, s=15.0):
    """tahmini devre boyu ≤ maxL olana dek uzun eksen boyunca ikiye böl"""
    parts = [g]
    while True:
        big = max(parts, key=lambda q: q.area)
        est = big.area / s / 100.0 + 12.0
        if est <= maxL or len(parts) > 6: break
        parts.remove(big)
        x0, y0, x1, y1 = big.bounds
        if x1 - x0 >= y1 - y0:
            xm = (x0 + x1) / 2
            a = big.intersection(box(x0 - 1, y0 - 1, xm - 4, y1 + 1)); b = big.intersection(box(xm + 4, y0 - 1, x1 + 1, y1 + 1))
        else:
            ym = (y0 + y1) / 2
            a = big.intersection(box(x0 - 1, y0 - 1, x1 + 1, ym - 4)); b = big.intersection(box(x0 - 1, ym + 4, x1 + 1, y1 + 1))
        for q in (a, b):
            if q.geom_type == 'MultiPolygon': q = max(q.geoms, key=lambda z: z.area)
            if q.area > 0.3e4: parts.append(q)
    return parts


def split_rect(rect, wall, s, maxL=70.0, dd=0.0):
    x0, y0, x1, y1 = rect.bounds
    est = rect.area / s / 100.0 + 2 * dd / 100.0 + 4.0
    n = max(1, math.ceil(est / maxL))
    if True:       # kapı tarafında ayak şeridi (ayaklar salyangoz üstünden geçmesin)
        lane = 6 + 10 * n if n > 1 else 14
        if wall == 'S': y0 += lane
        elif wall == 'N': y1 -= lane
        elif wall == 'W': x0 += lane
        else: x1 -= lane
    out = []
    for i in range(n):
        if wall in 'NS':
            a = x0 + (x1 - x0) * i / n + (3 if i else 0); b = x0 + (x1 - x0) * (i + 1) / n - (3 if i < n - 1 else 0)
            out.append(box(a, y0, b, y1))
        else:
            a = y0 + (y1 - y0) * i / n + (3 if i else 0); b = y0 + (y1 - y0) * (i + 1) / n - (3 if i < n - 1 else 0)
            out.append(box(x0, a, x1, b))
    return out


def side_of(rect, p):
    x0, y0, x1, y1 = rect.bounds
    d = {'S': abs(p[1] - y0), 'N': abs(p[1] - y1), 'W': abs(p[0] - x0), 'E': abs(p[0] - x1)}
    return min(d, key=d.get)


def oda_isi(room, k, kat, others):
    """gheat.calc_room girdisi: dış duvar/pencere (cephe, ışıklık), komşu bina, ısıtılmayan koridor"""
    foot = translate(GEO_FOOT(), 0, 0)
    ext, intl = [], []
    rp = room['poly'].simplify(12).buffer(0)
    if rp.geom_type == 'MultiPolygon': rp = max(rp.geoms, key=lambda q: q.area)
    for kk, Lm in kenar_sinif(rp, foot, others):
        if kk[0] in ('dis', 'isiklik'):
            w = round(min(Lm * 0.55, 3.0), 2)
            ext.append((kk[1], round(Lm, 2), [(w, 1.50, 1, 'ÇP')] if Lm > 0.8 else []))
        elif kk[0] == 'komsu':
            intl.append(('İDM', round(Lm, 2), T_KOMSU, None))
        elif kk[0] == 'kor':
            intl.append(('İDM', round(Lm, 2), GH.T_HOL, None))
    ti = 24 if 'BANYO' in room['name'] else 20
    R = dict(name=room['name'], ti=ti, A=room['A'], ext=ext, int=intl)
    return GH.calc_room(R, 'ust' if kat == 3 else 'ara'), R


_FOOT = None


def GEO_FOOT():
    global _FOOT
    if _FOOT is None: _FOOT = izgara.foot_S(2)
    return _FOOT


def ofis(kat, k, Dd, log=True):
    """ofis yerden ısıtma tasarımı (1. kat S koordinatında; çizimde kat ve H kaydırması uygulanır)"""
    rooms = ofis_mahalleri(k)
    op = Polygon(OFIS_S1[k]['poly'])
    # kollektör: dolabın arkası (ofis içi)
    ux, uy = Dd['u']; nx_, ny_ = Dd['n']; w = Dd['wall']
    dk = D12[0] if kat == 3 else 0.0
    w = (w[0] - dk, w[1])
    # giriş mahalli: kollektörün olduğu mahal
    kc0 = (w[0] - nx_ * 30, w[1] - ny_ * 30)
    hol = [r for r in rooms if any(t in r['name'] for t in ('HOL', 'GİRİŞ', 'KARŞILAMA'))]
    inside = [r for r in rooms if r['poly'].buffer(25).contains(Point(kc0))]
    cand = [r for r in inside if r in hol] or hol or inside or rooms
    ent = min(cand, key=lambda r: r['poly'].distance(Point(kc0)))
    # ısı kaybı
    allp = [r['poly'] for r in rooms]
    calc = {}
    for r in rooms:
        oth = [q for q in allp if q is not r['poly']] + [ofis_poly(j, 2, 'S') for j in OFIS_S1 if j != k] + [op.buffer(-15)]
        calc[r['comp']] = oda_isi(r, k, kat, oth)
    # devreler (giriş hariç): en büyük dikdörtgen(ler); kapı tarafına dik şeritler (her şerit kapıya değer)
    from shapely.ops import nearest_points
    circ = []
    for r in rooms:
        if r is ent: continue
        q = calc[r['comp']][0]['Q']
        s = 10.0 if (q / max(r['A'], 0.5) > 75 or 'BANYO' in r['name']) else 15.0
        dp = nearest_points(r['poly'], ent['poly'])[0]; dp = (dp.x, dp.y)
        for rc in oda_dikdortgenleri(r, min_m2=1.0 if any(t in r['name'] for t in ('BANYO', 'WC', 'MUTFAK')) else 2.0):
            wall = side_of(rc, dp)
            parts = split_rect(rc, wall, s, 70.0, math.dist(dp, kc0))
            for j, p in enumerate(parts):
                circ.append(dict(room=r, rpoly=p, s=s, ipart=j, npart=len(parts), dp=dp, wall=wall))
    n = len(circ) + 1                                    # +1: giriş holü devresi (sonra)
    # kollektör + ağızlar (duvara paralel, 10 cm aralık)
    Wk = 12 + n * 10
    kc = (w[0] - nx_ * 22 + ux * 0, w[1] - ny_ * 22 + uy * 0)
    ports = []
    for i in range(n):
        t = -Wk / 2 + 8 + i * 10
        pa = (kc[0] + ux * t - nx_ * 6, kc[1] + uy * t - ny_ * 6)
        pb = (kc[0] + ux * (t + 4) - nx_ * 6, kc[1] + uy * (t + 4) - ny_ * 6)
        ports.append((pa, pb))
    stub = lambda p: (p[0] - nx_ * 12, p[1] - ny_ * 12)
    # ızgara: ofis içi, duvarlar kapalı (kapı boşlukları açık), kolonlar kapalı
    g = izgara.grid_ofis(2, op, 4.0, far_pen=0.6)
    kbox = Polygon([(kc[0] + sx * ux * Wk / 2 + sy * nx_ * 9, kc[1] + sx * uy * Wk / 2 + sy * ny_ * 9) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    g.add_block(kbox, pad=0.5)
    # yedek: iç duvardan (kılıflı) geçiş — yalnız kapısı ofis içine açılmayan mahaller için
    segs_ = [s_ for s_ in izgara.walls_S(2) if LineString(s_).intersects(op)]
    wm = izgara.raster_walls(g, segs_, 1) & izgara.poly_mask(g, op.buffer(-12)) & g.block
    # salyangozlar
    for c in circ:
        cs = list(c['rpoly'].exterior.coords)[:-1]
        # giriş köşesi: şeridin kapıya en yakın köşesi
        ci = min(range(len(cs)), key=lambda j: math.dist(cs[j], c['dp']))
        try:
            c['full'] = spiral3.bifilar(cs, ci, 'a', c['s'])[0]
        except Exception:
            c['full'] = None
    circ = [c for c in circ if c['full'] and len(c['full']) > 3]
    for i, c in enumerate(circ):
        g.add_line(c['full'], f'SP{i}')
    rmask = {}
    for r in rooms:
        if r is ent: continue
        rmask[id(r)] = izgara.poly_mask(g, r['poly'].buffer(2))
    # ağız ataması: kollektör ekseni üzerindeki izdüşüm sırası
    order = sorted(range(len(circ)), key=lambda i: (circ[i]['full'][0][0] - kc[0]) * ux + (circ[i]['full'][0][1] - kc[1]) * uy)
    for p_i, ci in enumerate(order): circ[ci]['pidx'] = p_i
    import copy
    base_occ = {k_: v.copy() for k_, v in g.occ.items()}
    base_lines = {k_: list(v) for k_, v in g.lines.items()}
    dist = lambda c: math.dist(c['full'][0], kc)

    def _yerles(seq):
        g.occ = {k_: v.copy() for k_, v in base_occ.items()}
        g.lines = {k_: list(v) for k_, v in base_lines.items()}
        res = {}; bad = 0
        for c in seq:
            sid = f"L{c['pidx']}"
            mk = None
            for rid, m_ in rmask.items():
                if rid != id(c['room']): mk = m_.copy() if mk is None else (mk | m_)
            pa, pb = ports[c['pidx']]
            legs = []
            for port, end, sx in ((pa, c['full'][0], 'a'), (pb, c['full'][-1], 'b')):
                pts = g.route(stub(port), end, sid + sx, turn=6.0, free_end=3.0, near_r=4.0, mask=mk, max_exp=700_000)
                if not pts:
                    pts = g.route(stub(port), end, sid + sx, turn=6.0, free_end=3.0, near_r=4.0, max_exp=700_000)
                if not pts:
                    g.block &= ~wm; g.base[wm] += 600.0
                    pts = g.route(stub(port), end, sid + sx, turn=6.0, free_end=3.0, near_r=4.0, mask=mk, max_exp=1_500_000)
                    g.block |= wm; g.base[wm] -= 600.0
                if not pts:
                    pts = [stub(port), end]; bad += 1
                pts = [port] + pts
                g.add_line(pts, sid + sx)
                legs.append(_collinear(pts))
            res[id(c)] = legs
        return _kesisim2(circ, res) + 50 * bad, res

    best = None
    for it in range(4):
        for seq in (sorted(circ, key=lambda c: -dist(c)), sorted(circ, key=lambda c: c['pidx'])):
            nx, res = _yerles(seq)
            if best is None or nx < best[0]:
                best = (nx, res, {id(c): c['pidx'] for c in circ})
        if best[0] == 0 or it == 3: break
        # ağız sırasını, en iyi çözümde ayakların kollektörden 60 cm sonraki izdüşümüne göre yenile
        for c in circ: c['pidx'] = best[2][id(c)]
        def _key(c):
            la = LineString(best[1][id(c)][0])
            q = la.interpolate(min(60.0, la.length * 0.5))
            return (q.x - kc[0]) * ux + (q.y - kc[1]) * uy
        new = sorted(circ, key=_key)
        if [best[2][id(c)] for c in new] == sorted(best[2][id(c)] for c in new): break
        for p_i, c in enumerate(new): c['pidx'] = p_i
    for c in circ: c['pidx'] = best[2][id(c)]
    ayir_legs(circ, best[1])
    for c in circ:
        a_, b_ = best[1][id(c)]
        c['legs'] = (a_, b_)
        c['path'] = a_[:-1] + c['full'] + list(reversed(b_))[1:]
        c['L'] = LineString(c['path']).length / 100.0
    # giriş holü devresi: ayaklar + kollektör dışındaki en büyük boş dikdörtgen
    K = kat_seg()
    occ = np.zeros_like(K.lab, dtype=bool)
    gb = unary_union([LineString(p).buffer(14) for c in circ for p in c['legs']] + [kbox.buffer(20)])
    from skimage.draw import polygon as _skp
    for gg in getattr(gb, 'geoms', [gb]):
        xs, ys = gg.exterior.coords.xy
        rr, cc = _skp([(x - K.x0) / mahal.ST for x in xs], [(y - K.y0) / mahal.ST for y in ys], K.lab.shape)
        occ[rr, cc] = True
    ent2 = dict(ent, extra_block=occ)
    rects = oda_dikdortgenleri(ent2, ent=True, min_m2=2.0)
    if rects:
        fr = rects[0]
        cs = list(fr.exterior.coords)[:-1]
        ci = min(range(len(cs)), key=lambda j: math.dist(cs[j], kc))
        try:
            full = spiral3.bifilar(cs, ci, 'a', 15.0)[0]
        except Exception:
            full = None
        if full and len(full) > 3:
            for c in circ:
                for p in c['legs']: g.add_line(p, 'X')
            pidx = len(circ)
            pa, pb = ports[pidx]
            legs = []
            for port, end, sx in ((pa, full[0], 'a'), (pb, full[-1], 'b')):
                pts = g.route(stub(port), end, 'E' + sx, turn=6.0, free_end=3.0, near_r=4.0, max_exp=700_000) or [stub(port), end]
                pts = [port] + pts; g.add_line(pts, 'E' + sx); legs.append(_collinear(pts))
            ent_c = dict(room=ent, rpoly=fr, s=15.0, ipart=0, npart=1, full=full, pidx=pidx, legs=tuple(legs))
            ent_c['path'] = legs[0][:-1] + full + list(reversed(legs[1]))[1:]
            ent_c['L'] = LineString(ent_c['path']).length / 100.0
            circ.append(ent_c)
    # W dağıtımı
    for r in rooms:
        cs_ = [c for c in circ if c['room'] is r]
        if not cs_: continue
        Ar = sum(c['rpoly'].area for c in cs_)
        for c in cs_:
            c['W'] = calc[r['comp']][0]['Q'] * c['rpoly'].area / Ar
            c['ti'] = calc[r['comp']][0]['ti']
            c['Ar'] = c['rpoly'].area / 1e4
    if log:
        print('  YI', kat, k, 'devre', len(circ), 'max L', round(max(c['L'] for c in circ), 1), 'kesişme', best[0])
    return dict(rooms=rooms, calc=calc, circ=circ, ports=ports, kc=kc, Wk=Wk, u=(ux, uy), n=(nx_, ny_), ent=ent)


def _ust_uste(s1, s2, tol=1.5):
    (a, b), (c, d) = s1, s2
    if abs(a[1] - b[1]) < 0.01 and abs(c[1] - d[1]) < 0.01 and abs(a[1] - c[1]) < tol:
        lo, hi = max(min(a[0], b[0]), min(c[0], d[0])), min(max(a[0], b[0]), max(c[0], d[0]))
        return hi - lo > 2.0
    if abs(a[0] - b[0]) < 0.01 and abs(c[0] - d[0]) < 0.01 and abs(a[0] - c[0]) < tol:
        lo, hi = max(min(a[1], b[1]), min(c[1], d[1])), min(max(a[1], b[1]), max(c[1], d[1]))
        return hi - lo > 2.0
    return False


def ayir_legs(circ, res, step=5.0, it=80):
    """üst üste binen ayak parçalarını (farklı devre / kendi salyangozu) yanal kaydırarak ayır"""
    legs = []
    for c in circ:
        for li in (0, 1):
            legs.append((id(c), li))
    def segs_of(pts):
        return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    fulls = {id(c): segs_of(c['full']) for c in circ}
    for _ in range(it):
        moved = False
        allseg = []
        for cid, li in legs:
            for si, sg in enumerate(segs_of(res[cid][li])):
                allseg.append((cid, li, si, sg))
        for cid, li, si, sg in allseg:
            pts = res[cid][li]
            if si == 0: continue                                     # kollektör ağız ucu
            son = si >= len(pts) - 2                                 # salyangoza giriş parçası: kaydır + dik bağlantı
            conf = [o for o in allseg if (o[0], o[1]) != (cid, li) and _ust_uste(sg, o[3])]
            conf += [f for k_, fs in fulls.items() for f in fs if _ust_uste(sg, f)]
            if not conf: continue
            a, b = sg
            hor = abs(a[1] - b[1]) < 0.01
            best = None
            for dd in (step, -step, 2 * step, -2 * step, 3 * step, -3 * step):
                na = (a[0], a[1] + dd) if hor else (a[0] + dd, a[1])
                nb = (b[0], b[1] + dd) if hor else (b[0] + dd, b[1])
                n_conf = sum(1 for o in allseg if (o[0], o[1]) != (cid, li) and _ust_uste((na, nb), o[3]))
                n_conf += sum(1 for fs in fulls.values() for f in fs if _ust_uste((na, nb), f))
                if best is None or n_conf < best[0]: best = (n_conf, na, nb)
                if n_conf == 0: break
            if best[0] < len(conf):
                pts = list(pts)
                if son:
                    pts = pts[:si] + [best[1], best[2], pts[si + 1]]
                else:
                    pts[si] = best[1]; pts[si + 1] = best[2]
                res[cid][li] = _collinear(pts) if len(pts) > 2 else pts
                moved = True
                break
        if not moved: break


def _kesisim2(circ, res):
    """farklı devre ayakları arası kesişme sayısı"""
    L = [(id(c), LineString(p)) for c in circ for p in res[id(c)] if len(p) > 1]
    F = [(id(c), LineString(c['full'])) for c in circ]
    n = 0
    for i in range(len(L)):
        for j in range(i + 1, len(L)):
            if L[i][0] != L[j][0] and L[i][1].crosses(L[j][1]): n += 1
        for cid, f in F:
            if cid != L[i][0] and L[i][1].crosses(f): n += 3
    return n


def _kesisim(paths):
    ls = [LineString(p) for p in paths if len(p) > 1]
    n = 0
    for i in range(len(ls)):
        for j in range(i + 1, len(ls)):
            if ls[i].crosses(ls[j]): n += 1
    return n


_CACHE = '/tmp/claude-0/vy/yi_cache.pkl'


def ofis_k(kat, k, Dd):
    """kat 2 tasarımı önbellekten; kat 3 aynı yerleşim (çatı altı ısı kaybı yeniden hesaplanır)"""
    import os
    C = pickle.load(open(_CACHE, 'rb')) if os.path.exists(_CACHE) else {}
    if k not in C:
        Dd2 = dict(Dd, wall=(Dd['wall'][0] - (D12[0] if kat == 3 else 0.0), Dd['wall'][1]))
        C[k] = ofis(2, k, Dd2)
        pickle.dump(C, open(_CACHE, 'wb'))
    R = C[k]
    if kat == 3:
        import copy
        R = copy.copy(R)
        op = Polygon(OFIS_S1[k]['poly'])
        allp = [r['poly'] for r in R['rooms']]
        calc = {}
        for r in R['rooms']:
            oth = [q for q in allp if q is not r['poly']] + [ofis_poly(j, 2, 'S') for j in OFIS_S1 if j != k] + [op.buffer(-15)]
            calc[r['comp']] = oda_isi(r, k, 3, oth)
        circ = [dict(c) for c in R['circ']]
        for r in R['rooms']:
            cs_ = [c for c in circ if c['room']['comp'] == r['comp']]
            if not cs_: continue
            Ar = sum(c['rpoly'].area for c in cs_)
            for c in cs_:
                c['W'] = calc[r['comp']][0]['Q'] * c['rpoly'].area / Ar
        R['circ'] = circ
        R['calc3'] = calc
    # kullanıcının kendi MTY devreleri (planda onlar çizili): devre listesi + kollektör ağız sayısı onlardan
    try:
        import ukat
        UD = ukat.devreler().get((kat, k))
    except Exception:
        UD = None
    if UD:
        import copy
        R = copy.copy(R)
        calc = R['calc3' if 'calc3' in R else 'calc']
        circ = []
        for i, d in enumerate(UD):
            pt = Point(d['p'])
            r = min(R['rooms'], key=lambda q: q['poly'].distance(pt))
            c = dict(room=r, rpoly=r['poly'], s=d['s'], ipart=0, npart=1, full=None, pidx=i, legs=(), path=None,
                     L=d['L'], W=(d['W'] if d['W'] else calc[r['comp']][0]['Q']), ti=calc[r['comp']][0]['ti'],
                     Ar=r['poly'].area / 1e4, user=d)
            circ.append(c)
        n = len(circ)
        ux, uy = R['u']; nx_, ny_ = R['n']; kc = R['kc']
        Wk = 12 + n * 10
        ports = []
        for i in range(n):
            t = -Wk / 2 + 8 + i * 10
            ports.append(((kc[0] + ux * t - nx_ * 6, kc[1] + uy * t - ny_ * 6), (kc[0] + ux * (t + 4) - nx_ * 6, kc[1] + uy * (t + 4) - ny_ * 6)))
        R['circ'] = circ; R['ports'] = ports; R['Wk'] = Wk; R['user'] = True
    return R


def oda_calc(R, r):
    return R['calc3' if 'calc3' in R else 'calc'][r['comp']]


def ozet(kat, k):
    """önbellekten ofis mahal ısı kayıpları: [(ad, A, ti, Q)], toplam Q (W)"""
    import os
    if not os.path.exists(_CACHE): return None
    C = pickle.load(open(_CACHE, 'rb'))
    if k not in C: return None
    R = ofis_k(kat, k, None)
    out = []
    for r in R['rooms']:
        c = oda_calc(R, r)[0]
        out.append((r['name'], r['A'], c['ti'], round(c['Q'])))
    return out, sum(q for *_, q in out)
