"""boru kesişme kontrolü + köprü (atlama) çizimi: farklı borular üst üste binmez, kesişenlerde alttaki boru köprü ile kesilir"""
import math
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree
import cad
import gp

RANK = {gp.PS: 9, gp.PST: 9, 'MTY-PIS SU-BASMA': 8, gp.YL: 8, gp.CS: 6, gp.CH: 5, gp.HGL: 4, gp.HDL: 4, gp.PEX: 3}


def crossings(net=None, tol=1.0):
    net = net if net is not None else gp.NET
    items = [n for n in net if len(n['pts']) > 1]
    geoms = [LineString(n['pts']) for n in items]
    tree = STRtree(geoms)
    rep = []
    for i, g in enumerate(geoms):
        for j in tree.query(g):
            j = int(j)
            if j <= i or g.distance(geoms[j]) > 0.8:
                continue
            h = geoms[j]
            inter = g.buffer(0.5).intersection(h)
            if inter.is_empty:
                continue
            ends = [Point(p) for p in (items[i]['pts'][0], items[i]['pts'][-1], items[j]['pts'][0], items[j]['pts'][-1])]
            parts = list(inter.geoms) if hasattr(inter, 'geoms') else [inter]
            for p in parts:
                c = p.centroid
                if p.length > 2.0:
                    if items[i]['sys'] == items[j]['sys'] and items[i]['lay'] == items[j]['lay'] and \
                            any(c.distance(e) < 1.5 + p.length / 2 for e in ends) and p.length < 3.0:
                        continue
                    rep.append(('ÇAKIŞIK', items[i], items[j], (c.x, c.y), p.length))
                    continue
                if any(c.distance(e) < tol + 1.0 for e in ends):
                    continue
                rep.append(('KESİŞME', items[i], items[j], (c.x, c.y), 0))
    return rep


def summary(rep):
    out = []
    for k, a, b, p, l in rep:
        out.append((k, a['lay'], b['lay'], (round(p[0]), round(p[1])), round(l, 1)))
    return out


def _protected():
    return {id(r) for b in cad.BLK for r in b['recs']}


def hops(rep, g=4.0):
    """KESİŞME'lerde düşük öncelikli boruya köprü (yarım daire) çiz - boru PARÇALANMAZ, köprü aynı polyline içine eklenir"""
    cuts = {}
    prot = _protected()
    for k, a, b, p, l in rep:
        if k != 'KESİŞME':
            continue
        ra, rb = RANK.get(a['lay'], 5), RANK.get(b['lay'], 5)
        lo = b if rb <= ra else a
        cuts.setdefault(id(lo), (lo, []))[1].append(p)
    n = 0
    for lo, pts in cuts.values():
        rec = cad.R[lo['ri']]
        if rec is None or rec[0] != 'P' or id(rec) in prot:
            continue
        ls = LineString(lo['pts'])
        ss = sorted(set(round(ls.project(Point(p)), 2) for p in pts))
        ss = [s_ for s_ in ss if g < s_ < ls.length - g]
        merged = []
        for s_ in ss:
            if merged and s_ - merged[-1] < 2.5 * g:
                continue
            merged.append(s_)
        if not merged:
            continue
        out, s0 = [], 0.0
        for s_ in merged:
            seg = _substring(ls, s0, s_ - g)
            out += seg if not out else seg[1:]
            c = ls.interpolate(s_)
            q = ls.interpolate(max(0.0, s_ - 0.5)); r = ls.interpolate(min(ls.length, s_ + 0.5))
            ang = math.degrees(math.atan2(r.y - q.y, r.x - q.x))
            out += [(c.x + g * math.cos(math.radians(ang + 180 - t)), c.y + g * math.sin(math.radians(ang + 180 - t)))
                    for t in range(15, 181, 15)]
            s0 = s_ + g
        out += _substring(ls, s0, ls.length)[1:]
        cad.R[lo['ri']] = ('P', rec[1], out, False, rec[4]) + tuple(rec[5:])
        n += 1
    return n


def _substring(ls, a, b):
    coords = list(ls.coords)
    out = [ls.interpolate(a).coords[0]]
    acc = 0.0
    for p, q in zip(coords[:-1], coords[1:]):
        seg = math.hypot(q[0] - p[0], q[1] - p[1])
        if a < acc + seg < b:
            out.append(q)
        acc += seg
    out.append(ls.interpolate(b).coords[0])
    return out


def mask_texts(pad=1.0):
    """ESKİ: boruları yazı altında keserdi - artık kullanılmaz (borular patlatılmaz). wipe_texts kullan."""
    return wipe_texts(pad)


def wipe_texts(pad=1.0):
    """altından boru geçen serbest yazılara maske (WIPEOUT) koy: boru kesilmez, yazı okunur"""
    import tcheck
    R = cad.R
    prot = _protected()
    pipes = []
    for r in R:
        if r and r[0] == 'P' and r[1] in tcheck.PIPE_LAYERS:
            pipes.append(LineString(list(r[2]) + ([r[2][0]] if r[3] else [])))
        elif r and r[0] == 'L' and r[1] in tcheck.PIPE_LAYERS:
            pipes.append(LineString([r[2], r[3]]))
    if not pipes:
        return 0
    tree = STRtree(pipes)
    have = [Polygon(r[2]) for r in R if r and r[0] == 'W']
    n = 0
    for r in list(R):
        if not r or r[0] != 'T' or not r[3].strip() or id(r) in prot:
            continue
        bx = tcheck.tbox(r)
        if any(h.contains(bx) for h in have):
            continue
        if not any(pipes[int(j)].intersects(bx) for j in tree.query(bx)):
            continue
        g = bx.buffer(pad, join_style=2)
        R.append(('W', r[1], [tuple(c) for c in list(g.exterior.coords)[:-1]], False))
        n += 1
    return n


def dedupe(extra=('MTY-PVC',)):
    """eşdoğrusal üst üste binen boru çizgilerinde düşük öncelikli olanın çakışan kısmını sil"""
    import tcheck
    from shapely.ops import unary_union
    R = cad.R
    prot = _protected()
    lays = set(tcheck.PIPE_LAYERS) | set(extra)
    idx, geo = [], []
    for i, r in enumerate(R):
        if not r or r[1] not in lays:
            continue
        if r[0] == 'L':
            g = LineString([r[2], r[3]])
        elif r[0] == 'P':
            g = LineString(list(r[2]) + ([r[2][0]] if r[3] else []))
        else:
            continue
        if g.length > 0:
            idx.append(i); geo.append(g)
    tree = STRtree(geo)
    cut = {}
    for a, g in enumerate(geo):
        for b in tree.query(g):
            b = int(b)
            if b <= a:
                continue
            h = geo[b]
            if g.distance(h) > 0.05:
                continue
            it = g.intersection(h.buffer(0.05))
            if it.length <= 1.0:
                continue
            ra, rb = RANK.get(R[idx[a]][1], 5), RANK.get(R[idx[b]][1], 5)
            lo = b if rb <= ra else a
            hi = a if lo == b else b
            if id(R[idx[lo]]) in prot:             # blok çizgisine dokunulmaz: diğerini kes
                lo, hi = hi, lo
                if id(R[idx[lo]]) in prot:
                    continue
            cut.setdefault(lo, []).append(geo[hi].buffer(0.05))
    new = []
    for k, polys in cut.items():
        r = R[idx[k]]
        rest = geo[k].difference(unary_union(polys))
        parts = list(rest.geoms) if hasattr(rest, 'geoms') else ([rest] if not rest.is_empty else [])
        R[idx[k]] = None
        for p in parts:
            if p.length < 0.3:
                continue
            cs = list(p.coords)
            if r[0] == 'L':
                for q0, q1 in zip(cs[:-1], cs[1:]):
                    new.append(('L', r[1], q0, q1) + tuple(r[4:]))
            else:
                new.append(('P', r[1], cs, False, r[4]) + tuple(r[5:]))
    R.extend(new)
    R[:] = [r for r in R if r is not None]
    return len(cut)
