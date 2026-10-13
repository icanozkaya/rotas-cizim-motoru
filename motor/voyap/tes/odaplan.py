"""VOYAP tesisat: 1. kat (sıhhi sırası) mahal poligonları. Kapı boşlukları kapatılır, etiketli yüzler mahal olur."""
import pickle, math, re, collections
import numpy as np
from shapely.geometry import LineString, Point, Polygon, MultiPoint
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree
VY = '/tmp/claude-0/vy/'
S = pickle.load(open(VY + 'sih.pkl', 'rb'))

def clean(s):
    s = re.sub(r'\\[A-Za-z][^;]*;', '', s); s = s.replace('{', '').replace('}', '').replace('\\P', '\n')
    return s.strip()

def segs_in(win, lays=('MKDU0',)):
    x0, y0, x1, y1 = win
    out = []
    for r in S:
        if r[0] not in 'LP' or r[1] not in lays: continue
        q = [p[:2] for p in (r[2] if r[0] == 'P' else r[2][:2])]
        if not any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in q): continue
        for a, b in zip(q[:-1], q[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 0.3: continue
            ang = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))) % 180
            diag = 20 < ang < 70 or 110 < ang < 160
            if diag and L < 150: continue      # kapı yayı parçaları
            out.append((a, b))
    return out

def labels(win):
    x0, y0, x1, y1 = win
    L = []
    for r in S:
        if r[0] == 'T' and r[1] == 'MKDU0' and x0 < r[2][0][0] < x1 and y0 < r[2][0][1] < y1:
            t = clean(r[2][1])
            L.append((r[2][0][:2], t))
    # isim + m² birleştir
    names = []
    for p, t in L:
        if 'm²' in t and '\n' not in t: continue
        nm = t.split('\n')[0].strip()
        if not nm or 'PLANI' in nm: continue
        m2 = None
        if '\n' in t: m2 = t.split('\n')[1]
        else:
            c = [(math.hypot(q[0] - p[0], q[1] - p[1]), tt) for q, tt in L if 'm²' in tt and '\n' not in tt and q[1] < p[1] and abs(q[1] - p[1]) < 40 and abs(q[0] - p[0]) < 60]
            if c: m2 = min(c)[1]
        a = None
        if m2:
            mm = re.search(r'([\d.,]+)', m2)
            if mm: a = float(mm.group(1).replace(',', '.'))
        names.append(dict(p=p, ad=nm, m2=a))
    return names

def door_closers(segs, lo=55, hi=135):
    """serbest uç çiftleri (kapı/boşluk) birleştirilir"""
    R = lambda p: (round(p[0], 1), round(p[1], 1))
    deg = collections.Counter()
    for a, b in segs: deg[R(a)] += 1; deg[R(b)] += 1
    ends = [p for p, d in deg.items() if d == 1]
    E = np.array(ends) if ends else np.zeros((0, 2))
    out = []
    used = set()
    for i, p in enumerate(ends):
        d = np.hypot(E[:, 0] - p[0], E[:, 1] - p[1])
        for j in np.argsort(d):
            if j <= i or d[j] < lo: continue
            if d[j] > hi: break
            q = ends[j]
            ang = abs(math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))) % 90
            if 8 < ang < 82: continue
            out.append((p, q)); break
    return out

def rooms(win):
    segs = segs_in(win)
    cl = door_closers(segs)
    U = unary_union([LineString(s) for s in segs + cl])
    faces = [g for g in polygonize(U) if g.area > 1.5e4]
    return faces, cl

if __name__ == '__main__':
    import sys
    sys.path.insert(0, VY + 's'); from v import view
    win = (254422, -447800, 256498, -440300)
    faces, cl = rooms(win)
    N = labels(win)
    print(len(faces), 'yüz', len(cl), 'kapatıcı', len(N), 'etiket')
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(8, 29)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_aspect('equal'); ax.axis('off')
    cm = plt.get_cmap('tab20')
    for k, f in enumerate(faces):
        xs, ys = f.exterior.xy; ax.fill(xs, ys, color=cm(k % 20), alpha=0.5)
        nm = [n['ad'] for n in N if f.contains(Point(n['p']))]
        c = f.representative_point(); ax.text(c.x, c.y, (','.join(nm) or '?') + f"\n{f.area/1e4:.1f}", fontsize=5)
    for a, b in cl: ax.plot([a[0], b[0]], [a[1], b[1]], 'r-', lw=1)
    ax.set_xlim(win[0], win[2]); ax.set_ylim(win[1], win[3])
    fig.savefig(VY + 'inv/rooms1.png', dpi=110)
