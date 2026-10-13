# -*- coding: utf-8 -*-
"""Pis su kolonları (rev): kullanıcının MTY 'tavandan' pis su ağlarında her bağlı ağ için TEK kolon.
Kolon = ağın en büyük yüklü (Ø / SB) çap etiketinin işaret ettiği boru parçasından, akış yönündeki (az düğümlü taraf) uç."""
import math
import networkx as nx
from shapely.geometry import LineString, Point
from odaplan import S
WIN1 = (254422, -447800, 256498, -440300)


def pis_kolonlar(win=WIN1):
    inw = lambda p: win[0] < p[0] < win[2] and win[1] < p[1] < win[3]
    R = lambda p: (round(p[0], 1), round(p[1], 1))
    G = nx.Graph()
    for r in S:
        if r[1] == 'MTY-PISSU-BORU-TAVANDAN' and r[0] in 'LP':
            q = [p[:2] for p in (r[2] if r[0] == 'P' else r[2][:2])]
            if not inw(q[0]): continue
            for a, b in zip(q[:-1], q[1:]):
                if R(a) != R(b): G.add_edge(R(a), R(b))
    labs = []
    for r in S:
        if r[0] == 'T' and r[1] == 'MTY-PISSU-CAP' and inw(r[2][0]):
            t = r[2][1].replace('%%C', 'Ø')
            sb = [q for q in S if q[0] == 'T' and q[1] == 'MTY-YUK-BIRIMI' and abs(q[2][0][0] - r[2][0][0]) < 3 and -16 < q[2][0][1] - r[2][0][1] < -8]
            labs.append(dict(p=r[2][0][:2], cap=t, sb=sb[0][2][1] if sb else ''))
    out = []
    for comp in nx.connected_components(G):
        H = G.subgraph(comp)
        edges = list(H.edges())
        # bileşene ait etiketler (en yakın kenar ≤ 60)
        mine = []
        for lb in labs:
            d, e = min((LineString(e).distance(Point(lb['p'])), e) for e in edges)
            if d < 60: mine.append((lb, e, d))
        if not mine: continue
        def w(m):
            lb = m[0]
            c = int(''.join(ch for ch in lb['cap'] if ch.isdigit()) or 0)
            s = float(lb['sb'].split()[0]) if lb['sb'] else 0.0
            return (c, s, -m[2])
        lb, e, d = max(mine, key=w)
        # e kenarını çıkar: küçük taraf akış yönü
        H2 = nx.Graph(H); H2.remove_edge(*e)
        ca = nx.node_connected_component(H2, e[0]); cb = nx.node_connected_component(H2, e[1])
        side, start = (ca, e[0]) if len(ca) <= len(cb) else (cb, e[1])
        leaves = [n for n in side if H.degree(n) == 1]
        if not leaves: leaves = [start]
        kol = max(leaves, key=lambda n: nx.shortest_path_length(H2.subgraph(side), start, n)) if len(side) > 1 else start
        # betonarme kolon içine/yanına düşerse ağ boyunca geri çek (kolondan ≥15 cm)
        try:
            import izgara
            CC = izgara.cols_S(2)
            if CC.distance(Point(kol)) < 15:
                path = nx.shortest_path(H2.subgraph(side), kol, start) if len(side) > 1 else [kol]
                ls = LineString(path + [e[0] if start == e[1] else e[1]]) if len(path) > 0 else None
                for t in range(5, int(ls.length), 5):
                    q = ls.interpolate(t)
                    if CC.distance(q) >= 15:
                        kol = (round(q.x, 1), round(q.y, 1)); break
        except Exception as ex:
            print('kolon geri çekme', ex)
        out.append(dict(lb, kol=kol, d=round(d), n_lab=len(mine)))
    return out


if __name__ == '__main__':
    import piscol
    old = piscol.pis_kolonlar()
    new = pis_kolonlar()
    print(len(old), len(new))
    for k in new: print(k)
