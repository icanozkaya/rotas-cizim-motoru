# -*- coding: utf-8 -*-
"""Ofis/dükkân girişinde sayaç dolabı (koridor tarafı) ve ofis içi kollektör yerleşimi (S çerçevesi)."""
import math
from shapely.geometry import Polygon, Point, LineString
from veri import *
from izgara import walls_S

DOL_W, DOL_D = 90.0, 18.0          # dolap boyu (duvar boyunca) x derinlik
KOL_W, KOL_D = 70.0, 14.0


def _edge_near(poly, p):
    c = list(poly.exterior.coords)
    best = None
    for a, b in zip(c[:-1], c[1:]):
        s = LineString([a, b]); d = s.distance(Point(p))
        if best is None or d < best[0]: best = (d, a, b, s)
    return best


def dolap(poly, besleme, kapi=None):
    """besleme noktasına en yakın dış kenar: dolap kenar üzerinde, dışarı doğru; kapı kanadına girmez"""
    d, a, b, s = _edge_near(poly, besleme)
    L = s.length
    t = s.project(Point(besleme))
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    # dış normal: çokgen dışına bakan
    nx_, ny_ = -uy, ux
    m = s.interpolate(t)
    if poly.contains(Point(m.x + nx_ * 5, m.y + ny_ * 5)): nx_, ny_ = -nx_, -ny_
    if kapi is not None:
        tk = s.project(Point(kapi))
        if abs(t - tk) < 70:          # kapı önündeyse kapıdan uzağa kaydır
            t = tk + (75 if t >= tk else -75) * (1 if 0 < tk + (75 if t >= tk else -75) < L else -1)
    t = min(max(t, DOL_W / 2 + 10), L - DOL_W / 2 - 10)
    m = s.interpolate(t)
    c = (m.x + nx_ * (DOL_D / 2 + 9), m.y + ny_ * (DOL_D / 2 + 9))
    ang = math.degrees(math.atan2(uy, ux))
    return dict(c=c, ang=ang, u=(ux, uy), n=(nx_, ny_), wall=(m.x, m.y), t=t, edge=(a, b))


def dolap_port(D, k):
    """dolap bağlantı noktaları (koridor tarafı yüz): sıhhi solda, ısıtma sağda"""
    off = {'SS': -33, 'SIS': -18, 'SIRK': -3, 'IG': 15, 'ID': 30}[k]
    ux, uy = D['u']; nx_, ny_ = D['n']
    return (D['c'][0] + ux * off + nx_ * DOL_D / 2, D['c'][1] + uy * off + ny_ * DOL_D / 2)


def dolap_ic(D, k):
    """dolaptan ofis içine geçiş noktası (duvar iç yüzü)"""
    off = {'SS': -33, 'SIS': -18, 'IG': 15, 'ID': 30}[k]
    ux, uy = D['u']; nx_, ny_ = D['n']
    w = D['wall']
    return (w[0] + ux * (off + (D['t'] - D['t'])) + (D['c'][0] - nx_ * (DOL_D / 2 + 9) - w[0]) - nx_ * 16,
            w[1] + uy * off + (D['c'][1] - ny_ * (DOL_D / 2 + 9) - w[1]) - ny_ * 16)


def kollektor(D):
    """kollektör: dolabın tam arkası, ofis içi duvar yüzünde"""
    ux, uy = D['u']; nx_, ny_ = D['n']
    w = D['wall']
    c = (w[0] - nx_ * (KOL_D / 2 + 10) + ux * 22, w[1] - ny_ * (KOL_D / 2 + 10) + uy * 22)
    return dict(c=c, ang=D['ang'], u=(ux, uy), n=(-nx_, -ny_))
