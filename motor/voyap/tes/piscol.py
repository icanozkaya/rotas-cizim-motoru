"""Kullanıcının MTY pis su (tavandan) ağlarından kolon noktalarını bul (1. kat sıhhi sırası)."""
from rooms import *
import networkx as nx
WIN1 = (254422, -447800, 256498, -440300)

def pis_kolonlar(win=WIN1):
    inw = lambda p: win[0] < p[0] < win[2] and win[1] < p[1] < win[3]
    segs = []
    for r in S:
        if r[1] == 'MTY-PISSU-BORU-TAVANDAN' and r[0] in 'LP':
            q = [p[:2] for p in (r[2] if r[0] == 'P' else r[2][:2])]
            if inw(q[0]): segs += list(zip(q[:-1], q[1:]))
    R = lambda p: (round(p[0], 1), round(p[1], 1))
    G = nx.Graph()
    for a, b in segs:
        if R(a) != R(b): G.add_edge(R(a), R(b))
    labs = []
    for r in S:
        if r[0] == 'T' and r[1] == 'MTY-PISSU-CAP' and inw(r[2][0]):
            t = r[2][1].replace('%%C', 'Ø')
            sb = [q for q in S if q[0] == 'T' and q[1] == 'MTY-YUK-BIRIMI' and abs(q[2][0][0] - r[2][0][0]) < 3 and -16 < q[2][0][1] - r[2][0][1] < -8]
            labs.append(dict(p=r[2][0][:2], cap=t, sb=sb[0][2][1] if sb else ''))
    comps = [c for c in nx.connected_components(G)]
    out = []
    for lb in labs:
        best = None
        for c in comps:
            for n in c:
                if G.degree(n) != 1: continue
                d = math.dist(n, lb['p'])
                if best is None or d < best[0]: best = (d, n)
        out.append(dict(lb, kol=best[1], d=round(best[0])))
    return out

if __name__ == '__main__':
    for k in pis_kolonlar(): print(k)
