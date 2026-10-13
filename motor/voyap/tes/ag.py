# -*- coding: utf-8 -*-
"""Dağıtım ağı: A* ile ağaç kurma ve aşağı-akış yüküne göre parçalara (run) ayırma."""
import math
import numpy as np
import networkx as nx
from shapely.geometry import LineString, Point, MultiLineString
from shapely.ops import unary_union


def route_tree(g, src, targets, sysn, turn=40.0, max_exp=6_000_000, yk=1.0, first_to=None, wsys=None):
    """src'den başla; hedefleri yakından uzağa ağaca bağla. targets: [(p, yük, ad)]"""
    lines = []
    todo = sorted(targets, key=lambda t: math.dist(t[0], src))
    p0 = todo.pop(0)
    pts = g.route(src, p0[0], sysn=sysn, turn=turn, max_exp=max_exp, wsys=wsys, yk=yk)
    if not pts:
        pts = g.route(src, p0[0], sysn=sysn, turn=turn, max_exp=max_exp, wsys=wsys, yk=yk, free_end=40.0)
    if not pts:
        raise RuntimeError(('ilk hat yok', sysn, src, p0))
    g.add_line(pts, sysn); lines.append(pts)
    fail = []
    while todo:
        # ağaca en yakın hedef
        tree = MultiLineString([LineString(l) for l in lines])
        todo.sort(key=lambda t: tree.distance(Point(t[0])))
        t = todo.pop(0)
        pts = g.route(t[0], None, sysn=sysn, to_tree=True, turn=turn, free_end=8.0, max_exp=max_exp, wsys=wsys, yk=yk)
        if not pts:
            pts = g.route(t[0], src, sysn=sysn, turn=turn, max_exp=max_exp, wsys=wsys, yk=yk, free_end=40.0)
        if not pts:
            fail.append(t); continue
        g.add_line(pts, sysn); lines.append(pts)
    return lines, fail


def runs(src, lines, targets, cap_fn):
    """ağaç -> aynı çaplı zincirler: dict(pts, yuk, n, cap)"""
    U = unary_union([LineString(l) for l in lines])
    segs = []
    for ls in getattr(U, 'geoms', [U]):
        c = list(ls.coords); segs += list(zip(c[:-1], c[1:]))
    R = lambda p: (round(p[0], 2), round(p[1], 2))
    G = nx.Graph()
    for a, b in segs:
        if R(a) != R(b): G.add_edge(R(a), R(b), L=math.dist(a, b))
    nodes = list(G.nodes); na = np.array(nodes)
    near = lambda p: nodes[int(np.argmin(np.hypot(na[:, 0] - p[0], na[:, 1] - p[1])))]
    root = near(src)
    T = nx.bfs_tree(nx.minimum_spanning_tree(G, weight='L'), root)
    yuk = {n: 0.0 for n in T.nodes}; cnt = {n: 0 for n in T.nodes}
    for p, w, _ in targets:
        n = near(p); yuk[n] += w; cnt[n] += 1
    for n in reversed(list(nx.topological_sort(T))):
        for c in T.successors(n): yuk[n] += yuk[c]; cnt[n] += cnt[c]
    E = {}
    for a, b in T.edges:
        E[(a, b)] = dict(yuk=yuk[b], n=cnt[b], cap=cap_fn(yuk[b], cnt[b]))
    out = []
    starts = [(root, c) for c in T.successors(root)]
    seen = set()
    while starts:
        a, b = starts.pop()
        if (a, b) in seen: continue
        e = E[(a, b)]; pts = [a, b]; seen.add((a, b)); cur = b
        while True:
            ch = list(T.successors(cur))
            if len(ch) == 1 and E[(cur, ch[0])]['cap'] == e['cap']:
                seen.add((cur, ch[0])); pts.append(ch[0]); cur = ch[0]
            else:
                for c in ch: starts.append((cur, c))
                break
        out.append(dict(pts=_simp(pts), yuk=e['yuk'], n=e['n'], cap=e['cap']))
    return out


def _simp(pts):
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[i], pts[i + 1]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) < 1e-6: continue
        out.append(b)
    out.append(pts[-1])
    return out


def offset(pts, d):
    """ortogonal çoklu çizgiyi d kadar sola kaydır (pozitif sol)"""
    ls = LineString(pts)
    try:
        o = ls.offset_curve(d, join_style=2, mitre_limit=5.0)
    except Exception:
        o = ls.parallel_offset(abs(d), 'left' if d > 0 else 'right', join_style=2)
    if o.geom_type == 'MultiLineString':
        o = max(o.geoms, key=lambda g: g.length)
    return list(o.coords)
