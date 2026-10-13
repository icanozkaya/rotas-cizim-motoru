# -*- coding: utf-8 -*-
"""Kat ızgaraları (S çerçevesi): ortak alan ağı (ofis/dükkân içleri kapalı) ve ofis içi ağ (yalnız o ofis)."""
import sys, math, pickle
import numpy as np
from scipy import ndimage
from skimage.draw import line as skl, polygon as skp
from shapely.geometry import Polygon, Point, LineString, box
from shapely.affinity import translate
sys.path.insert(0, '/home/claude/nb/p2')
from router import Grid
from veri import *
import odaplan as rooms

VY = '/tmp/claude-0/vy/'
GEO = pickle.load(open(VY + 'geo.pkl', 'rb'))
PANS = {0: (250190, 252331), 1: (252331, 254422), 2: (254422, 256498), 3: (256498, 258574)}
YR = (-447800, -440300)
_W = {}


def walls_S(kat):
    """S çerçevesinde duvar parçaları"""
    if kat in _W: return _W[kat]
    if kat == 0:
        M = pickle.load(open(VY + 'mimT.pkl', 'rb'))
        dx, dy = ROW['S']
        out = []
        for r in M:
            if r[0] not in 'LP' or r[1] not in ('ARC_Duvar', '0'): continue
            q = [p[:2] for p in (r[2] if r[0] == 'P' else r[2][:2])]
            if not (247900 < q[0][0] < 250300): continue
            for a, b in zip(q[:-1], q[1:]):
                L = math.dist(a, b)
                if L < 0.3: continue
                ang = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))) % 180
                if (20 < ang < 70 or 110 < ang < 160) and L < 150: continue
                out.append(((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)))
    else:
        x0, x1 = PANS[kat]
        out = rooms.segs_in((x0, YR[0], x1, YR[1]))
    _W[kat] = out
    return out


def foot_S(kat):
    return translate(GEO[kat]['foot'], ROW['S'][0], ROW['S'][1])


def ofisler_S(kat):
    if kat in (2, 3):
        return {k: ofis_poly(k, kat, 'S') for k in OFIS_S1}
    if kat == 1:
        return {k: Polygon(d['poly']) for k, d in DUKKAN_S.items()}
    return {}


def raster_walls(g, segs, dil=1):
    m = np.zeros_like(g.block)
    for a, b in segs:
        ia, ja = g.ij(a); ib, jb = g.ij(b)
        rr, cc = skl(ia, ja, ib, jb)
        ok = (rr >= 0) & (rr < g.nx) & (cc >= 0) & (cc < g.ny)
        m[rr[ok], cc[ok]] = True
    if dil: m = ndimage.binary_dilation(m, iterations=dil)
    return m


def poly_mask(g, poly, pad=0.0):
    p = poly.buffer(pad) if pad else poly
    m = np.zeros_like(g.block)
    for gg in getattr(p, 'geoms', [p]):
        xs, ys = gg.exterior.coords.xy
        rr, cc = skp([(x - g.x0) / g.s for x in xs], [(y - g.y0) / g.s for y in ys], (g.nx, g.ny))
        m[rr, cc] = True
    return m


def cols_S(kat):
    cols = GEO[kat]['cols']
    return translate(cols, ROW['S'][0], ROW['S'][1])


def grid_ortak(kat, st=5.0, extra_block=()):
    """ortak alan ağı: bina içi, ofis/dükkân içleri ve duvarlar kapalı; kolonlar kapalı"""
    x0, x1 = PANS[kat]
    g = Grid((x0, YR[0], x1, YR[1]), step=st)
    fp = foot_S(kat)
    g.block |= ~poly_mask(g, fp.buffer(-8))
    g.base[raster_walls(g, walls_S(kat), 1)] += 80.0      # duvar / merdiven çizgisi: geçilebilir ama pahalı
    for k, p in ofisler_S(kat).items():
        g.block |= poly_mask(g, p, pad=4.0)
    for c in getattr(cols_S(kat), 'geoms', [cols_S(kat)]):
        if c.bounds[2] < x0 or c.bounds[0] > x1: continue
        g.add_block(c, pad=3.0)
    for b in extra_block: g.add_block(b, pad=2.0)
    return g


def grid_ofis(kat, poly, st=2.5, far_pen=1.5, soft=None):
    """ofis içi ağ: yalnız ofis çokgeni açık, iç duvarlar kapalı (kapı boşluklarından geçilir)"""
    x0, y0, x1, y1 = poly.buffer(60).bounds
    segs = [s for s in walls_S(kat) if LineString(s).intersects(poly.buffer(60))]
    g = Grid((x0, y0, x1, y1), step=st, walls=[list(s) for s in segs], wall_band=20.0, far_pen=far_pen)
    g.block |= ~poly_mask(g, poly.buffer(-3 if soft is None else 25))
    if soft is None:
        g.block |= raster_walls(g, segs, 1)
    else:
        g.base[raster_walls(g, segs, 1)] += soft
        g.base[~poly_mask(g, poly.buffer(-3))] += soft
    for c in getattr(cols_S(kat), 'geoms', [cols_S(kat)]):
        if c.intersects(poly.buffer(60)): g.add_block(c, pad=7.0)
    return g
