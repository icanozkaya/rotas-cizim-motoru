"""Sprinkler ağacı: A* ızgara güzergâhı (kolonlar yasak, bina dışı yasak, duvar boyu pahalı), çap = aşağı akış başlık sayısı."""
import pickle, math, sys, time
import numpy as np
sys.path.insert(0, '/home/claude/nb/p2')
from router import Grid, ortho
from scipy import ndimage
from skimage.draw import line as skl, polygon as skp
from shapely.geometry import LineString, Point, MultiLineString
from shapely.ops import unary_union
import networkx as nx
VY = '/tmp/claude-0/vy/'
from geo import OFF, KATAD
K1L = (248395.0, -452225.0)      # sprinkler/dolap kolonu (merdiven üst köşesi, ortak alan)
K2L = (248520.0, -456100.0)      # 2. dolap kolonu (alt merdiven)
SRC0 = (248905.0, -451955.0)     # bodrum: pompa dairesi AV1 çıkışı

# kat başına omurga hedefleri (yerel = bodrum çerçevesi)
SPINE = {   # zincirler: her zincir art arda noktadan noktaya (ilk zincir kaynaktan başlar)
    0: [[None, (249310.0, -451955.0), (249310.0, -456950.0)]],
    1: [[None, (248440.0, -452410.0), (249760.0, -452410.0)], [(248440.0, -452410.0), (248440.0, -452950.0), (248600.0, -453100.0), (248560.0, -454300.0), (249050.0, -454300.0), (249050.0, -457050.0)]],
    2: [[None, (248460.0, -452140.0), (249960.0, -452140.0)], [(248460.0, -452140.0), (248460.0, -453300.0), (248560.0, -453480.0), (248545.0, -455950.0)]],
    3: [[None, (248460.0, -452140.0), (249960.0, -452140.0)], [(248460.0, -452140.0), (248460.0, -453300.0), (248560.0, -453480.0), (248545.0, -455950.0)]],
}
# OH boru tablosu (EN 12845 / NFPA 13 ön hesaplı): çap -> max başlık
TABLO = [(2, '1"', 25), (3, '1 1/4"', 32), (5, '1 1/2"', 40), (10, '2"', 50), (20, '2 1/2"', 65), (40, '3"', 80), (100, '4"', 100)]   # 100 üstü: hidrolik hesapla DN100 yeterli (hız < 3 m/s)
def cap(n):
    for m, s, dn in TABLO:
        if n <= m: return s, dn
    return '4"', 100

def make_grid(G, st=5.0):
    x0, y0, x1, y1 = G['win']
    g = Grid((x0, y0, x1, y1), step=st)
    g.base[:] = 1.0
    wall = np.zeros_like(g.block)
    for a, b in G['walls']:
        ia, ja = g.ij(a); ib, jb = g.ij(b)
        rr, cc = skl(ia, ja, ib, jb)
        ok = (rr >= 0) & (rr < g.nx) & (cc >= 0) & (cc < g.ny)
        wall[rr[ok], cc[ok]] = True
    wall = ndimage.binary_dilation(wall, iterations=1)
    g.base += 7.0 * wall
    # bina dışı yasak
    fp = G['foot'].buffer(-6)
    xs, ys = fp.exterior.coords.xy
    rr, cc = skp([(x - x0) / st for x in xs], [(y - y0) / st for y in ys], (g.nx, g.ny))
    inside = np.zeros_like(g.block); inside[rr, cc] = True
    g.block |= ~inside
    cols = G['cols']
    for c in getattr(cols, 'geoms', [cols]):
        if c.bounds[2] < x0 or c.bounds[0] > x1: continue
        g.add_block(c, pad=5.0)
    return g

def route_floor(i, G, heads, st=5.0, log=True):
    t0 = time.time()
    g = make_grid(G, st)
    ox, oy = OFF[i]
    src = (SRC0[0], SRC0[1]) if i == 0 else (K1L[0] + ox, K1L[1] + oy)
    lines = []
    for ch in SPINE[i]:
        cur = src if ch[0] is None else (ch[0][0] + ox, ch[0][1] + oy)
        for tx, ty in ch[1:]:
            tp = (tx + ox, ty + oy)
            pts = g.route(cur, tp, sysn='S', turn=60.0, max_exp=3_000_000)
            assert pts, ('omurga', i, cur, tp)
            g.add_line(pts, 'S'); lines.append(pts); cur = tp
    todo = list(range(len(heads)))
    hp = [h['p'] for h in heads]
    fail = []
    spine = MultiLineString([LineString(l) for l in lines])
    todo.sort(key=lambda j: spine.distance(Point(hp[j])))
    YK = {0: 1.6, 1: 1.6, 2: 1.15, 3: 1.15}[i]
    while todo:
        k = todo.pop(0)
        pts = g.route(hp[k], None, sysn='S', to_tree=True, turn=30.0, free_end=6.0, max_exp=1_500_000, yk=YK)
        if not pts:
            fail.append(k); continue
        g.add_line(pts, 'S'); lines.append(pts)
    if log: print(KATAD[i], 'başlık', len(heads), 'bağlanamayan', len(fail), round(time.time() - t0, 1), 's')
    return src, lines, fail

def tree_sizes(src, lines, heads):
    U = unary_union([LineString(l) for l in lines])
    segs = []
    for ls in getattr(U, 'geoms', [U]):
        c = list(ls.coords)
        segs += list(zip(c[:-1], c[1:]))
    R = lambda p: (round(p[0], 2), round(p[1], 2))
    Gx = nx.Graph()
    for a, b in segs:
        Gx.add_edge(R(a), R(b), L=math.hypot(b[0] - a[0], b[1] - a[1]))
    nodes = list(Gx.nodes)
    na = np.array(nodes)
    def near(p):
        return nodes[int(np.argmin(np.hypot(na[:, 0] - p[0], na[:, 1] - p[1])))]
    root = near(src)
    hn = [near(h['p']) for h in heads]
    T = nx.bfs_tree(Gx, root) if nx.is_tree(Gx) else nx.bfs_tree(nx.minimum_spanning_tree(Gx, weight='L'), root)
    cnt = {n: 0 for n in T.nodes}
    for n in hn: cnt[n] += 1
    for n in reversed(list(nx.topological_sort(T))):
        for c in T.successors(n): cnt[n] += cnt[c]
    edges = []
    for a, b in T.edges:
        n = cnt[b]; s, dn = cap(n)
        edges.append(dict(a=a, b=b, n=n, cap=s, dn=dn, L=Gx[a][b]['L']))
    return dict(root=root, edges=edges, T=T, cnt=cnt, hn=hn, cyc=not nx.is_tree(Gx))

if __name__ == '__main__':
    Gm = pickle.load(open(VY + 'geo.pkl', 'rb'))
    H = pickle.load(open(VY + 'heads.pkl', 'rb'))
    out = {}
    floors = [int(a) for a in sys.argv[1:]] or [0, 1, 2, 3]
    try: out = pickle.load(open(VY + 'routes.pkl', 'rb'))
    except Exception: pass
    for i in floors:
        src, lines, fail = route_floor(i, Gm[i], H[i])
        ts = tree_sizes(src, lines, H[i])
        print('  döngü', ts['cyc'], 'kök başlık', ts['cnt'][ts['root']], 'çaplar', sorted(set(e['cap'] for e in ts['edges'])))
        out[i] = dict(src=src, lines=lines, fail=fail, ts=ts)
        pickle.dump(out, open(VY + 'routes.pkl', 'wb'))
