# -*- coding: utf-8 -*-
"""Kazan dairesi şeması: yol geometrisi, boru kesme/köprü, yazı kutusu ve model geometrisi (çakışma denetimi)."""
import math

import ezdxf
from ezdxf import path as zpath
from ezdxf.enums import TextEntityAlignment as TA
from shapely.affinity import rotate as srotate
from shapely.geometry import LineString, Polygon, box as sbox


# ----------------------------------------------------------------------------- yol
def segmentler(pts):
    out, s = [], 0.0
    for a, b in zip(pts, pts[1:]):
        out.append((s, a, b))
        s += math.dist(a, b)
    return out


def uzunluk(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def konum(pts, at):
    """noktanın yol üzerindeki uzaklığı ve o parçanın açısı"""
    best = None
    for s, a, b in segmentler(pts):
        L = math.dist(a, b)
        if L < 1e-9:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        t = (at[0] - a[0]) * ux + (at[1] - a[1]) * uy
        d = abs((at[0] - a[0]) * uy - (at[1] - a[1]) * ux)
        if -0.01 <= t <= L + 0.01 and (best is None or d < best[0]):
            best = (d, s + t, math.degrees(math.atan2(uy, ux)))
    if best is None or best[0] > 0.05:
        raise ValueError(f'nokta boru üzerinde değil: {at}')
    return best[1], best[2]


def nokta(pts, s):
    for s0, a, b in segmentler(pts):
        L = math.dist(a, b)
        if s <= s0 + L + 1e-9 or (a, b) == (pts[-2], pts[-1]):
            t = min(max((s - s0) / L, 0.0), 1.0) if L else 0.0
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    return pts[-1], 0.0


def dik_kesisim(pa, qa, pb, qb, m):
    """biri düşey biri yatay iki parçanın iç kesişimi (uçlardan m uzakta)"""
    va, vb = abs(pa[0] - qa[0]) < 1e-6, abs(pb[0] - qb[0]) < 1e-6
    ha, hb = abs(pa[1] - qa[1]) < 1e-6, abs(pb[1] - qb[1]) < 1e-6
    if va and hb:
        x, y = pa[0], pb[1]
        ya, xb = sorted((pa[1], qa[1])), sorted((pb[0], qb[0]))
    elif ha and vb:
        x, y = pb[0], pa[1]
        ya, xb = sorted((pb[1], qb[1])), sorted((pa[0], qa[0]))
    else:
        return None
    if ya[0] + m < y < ya[1] - m and xb[0] + m < x < xb[1] - m:
        return (x, y)
    return None


def parcala(pts, kes, kopru, r):
    """kesilen aralıklar dışındaki görünür parçalar; köprüler yarım daire (bulge) olarak, boru tek polyline kalır"""
    L = uzunluk(pts)
    iv = sorted((max(0.0, a), min(L, b)) for a, b in kes if b > 0 and a < L)
    birles = []
    for a, b in iv:
        if birles and a <= birles[-1][1] + 1e-6:
            birles[-1] = (birles[-1][0], max(birles[-1][1], b))
        else:
            birles.append((a, b))
    gor, s = [], 0.0
    for a, b in birles:
        if a > s:
            gor.append((s, a))
        s = max(s, b)
    if s < L:
        gor.append((s, L))
    kose = [s0 for s0, _, _ in segmentler(pts)][1:]
    out = []
    for a, b in gor:
        if b - a < 0.5:
            continue
        ev = [(a, 0)] + [(k, 0) for k in kose if a + 1e-6 < k < b - 1e-6]
        for h in kopru:
            if a + r < h < b - r:
                ev += [(h - r, 1), (h + r, 0)]
        ev.append((b, 0))
        ev.sort()
        v = []
        for s1, bul in ev:
            p, _ = nokta(pts, s1)
            if v and math.dist(v[-1][:2], p) < 1e-6:
                continue
            v.append((p[0], p[1], float(bul)))
        if len(v) >= 2:
            out.append(v)
    return out


# ----------------------------------------------------------------------------- yazı kutusu
def yazi_kutusu(p, s, h, al, rot, wf, pay=0.0):
    w = len(s) * h * 0.66 * wf
    name = al.name if hasattr(al, 'name') else str(al)
    if name.endswith('LEFT') or name in ('LEFT', 'ALIGNED', 'FIT'):
        x0 = 0.0
    elif name.endswith('RIGHT'):
        x0 = -w
    else:
        x0 = -w / 2
    if name.startswith('MIDDLE'):
        y0, y1 = -h / 2, h / 2
    elif name.startswith('TOP'):
        y0, y1 = -h, 0.0
    elif name.startswith('BOTTOM'):
        y0, y1 = 0.0, h
    else:                               # taban çizgisi hizası
        y0, y1 = -0.22 * h, h
    g = sbox(x0 - pay, y0 - pay, x0 + w + pay, y1 + pay)
    if rot:
        g = srotate(g, rot, origin=(0, 0))
    from shapely.affinity import translate
    return translate(g, p[0], p[1])


def aday_yonler(boru_aci, yon, tercih):
    d8 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]
    if yon is not None:              # branşman cihazı: cihaz ucunun yanı
        ux, uy = round(math.cos(math.radians(yon))), round(math.sin(math.radians(yon)))
        pre = [(ux, uy), (ux - uy if ux else 1, uy + ux if uy else 1), (ux + uy if ux else -1, uy - ux if uy else 1)]
    elif boru_aci is not None and abs(math.sin(math.radians(boru_aci))) > 0.7:
        pre = [(1, 0), (-1, 0)]
    elif boru_aci is not None:
        pre = [(0, 1), (0, -1)]
    else:
        pre = []
    out = []
    for d in (tercih or []) + pre + d8:
        d = (int(d[0]), int(d[1]))
        if d not in out and d != (0, 0):
            out.append(d)
    return out


# ----------------------------------------------------------------------------- model geometrisi
def _yol_geo(e, out, sahip, tur):
    try:
        p = zpath.make_path(e)
    except Exception:
        return
    w = e.dxf.get('const_width', 0) if e.dxftype() == 'LWPOLYLINE' else 0
    if e.dxftype() == 'LWPOLYLINE' and any(abs(v[4]) > 1e-9 for v in e.get_points('xyseb')):
        # kavisli parçalar (köprü / kollektör ucu) ayrı işaretlenir
        pts = e.get_points('xyb')
        if e.closed:
            pts = list(pts) + [pts[0]]
        for a, b in zip(pts, pts[1:]):
            if abs(a[2]) > 1e-9:
                from ezdxf.math import bulge_to_arc, ConstructionArc
                c, sa, ea, r = bulge_to_arc((a[0], a[1]), (b[0], b[1]), a[2])
                arc = ConstructionArc(c, r, math.degrees(sa), math.degrees(ea))
                ps = [(v.x, v.y) for v in arc.flattening(0.3)]
                out.append((sahip, tur, LineString(ps), True))
            else:
                out.append((sahip, tur, LineString([(a[0], a[1]), (b[0], b[1])]), False))
        return
    vs = [(v.x, v.y) for v in p.flattening(0.3)]
    for a, b in zip(vs, vs[1:]):
        if math.dist(a, b) > 1e-6:
            g = LineString([a, b])
            out.append((sahip, tur, g, False))


def _ent_geo(e, out, sahip, tur):
    t = e.dxftype()
    if t in ('ATTDEF', 'WIPEOUT', 'POINT', 'VIEWPORT'):
        return
    if t == 'LINE':
        a, b = e.dxf.start, e.dxf.end
        if (a - b).magnitude > 1e-6:
            out.append((sahip, tur, LineString([(a.x, a.y), (b.x, b.y)]), False))
    elif t in ('LWPOLYLINE', 'POLYLINE'):
        _yol_geo(e, out, sahip, tur)
    elif t in ('CIRCLE', 'ARC', 'ELLIPSE', 'SPLINE'):
        vs = [(v.x, v.y) for v in e.flattening(0.3)]
        for a, b in zip(vs, vs[1:]):
            if math.dist(a, b) > 1e-6:
                out.append((sahip, tur, LineString([a, b]), False))
    elif t in ('SOLID', 'TRACE'):
        v = [e.dxf.vtx0, e.dxf.vtx1, e.dxf.vtx3 if e.dxf.hasattr('vtx3') else e.dxf.vtx2, e.dxf.vtx2]
        g = Polygon([(q.x, q.y) for q in v]).buffer(0)
        if not g.is_empty:
            out.append((sahip, tur, g, False))
    elif t == 'HATCH':
        for pp in zpath.from_hatch(e):
            vs = [(v.x, v.y) for v in pp.flattening(0.3)]
            if len(vs) >= 3:
                g = Polygon(vs).buffer(0)
                if not g.is_empty:
                    out.append((sahip, tur, g, False))
    elif t in ('TEXT', 'ATTRIB'):
        if t == 'ATTRIB' and e.is_invisible:
            return
        s = e.dxf.text
        if not s.strip():
            return
        al, p1, p2 = e.get_placement()
        p = p1 if al in (TA.LEFT, TA.ALIGNED, TA.FIT) else (p2 if p2 is not None else p1)
        out.append((sahip, 'yazi' if tur != 'sembol' else tur,
                    yazi_kutusu((p.x, p.y), s, e.dxf.height, al, e.dxf.get('rotation', 0),
                                e.dxf.get('width', 1.0)), False))
    elif t == 'MTEXT':
        p = e.dxf.insert
        s = e.plain_text()
        out.append((sahip, 'yazi', sbox(p.x, p.y - e.dxf.char_height, p.x + len(s) * e.dxf.char_height * 0.6, p.y), False))
    elif t == 'INSERT':
        for v in e.virtual_entities():
            _ent_geo(v, out, sahip, 'sembol')
        for a in e.attribs:
            _ent_geo(a, out, sahip, 'sembol')


def model_kayit(msp, boru_katman=()):
    """(sahip no, tür, geometri, kavis mi) listesi; tür: boru / sembol / yazi / diger"""
    out = []
    for i, e in enumerate(msp):
        lay = e.dxf.get('layer', '0')
        tur = 'boru' if lay in boru_katman and e.dxftype() == 'LWPOLYLINE' else \
            ('yazi' if e.dxftype() in ('TEXT', 'MTEXT') else ('sembol' if e.dxftype() == 'INSERT' else 'diger'))
        _ent_geo(e, out, i, tur)
    return out


def model_geometri(msp):
    return [g for _, _, g, _ in model_kayit(msp)]
