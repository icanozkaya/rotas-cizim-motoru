"""VOYAP yangın: kat geometrisi (sıhhi dosyasının yangın sırası paftalarında, dünya koordinatı cm)."""
import pickle, math
import numpy as np
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import polygonize, unary_union
from shapely.affinity import translate
VY = '/tmp/claude-0/vy/'
S = pickle.load(open(VY + 'sih.pkl', 'rb'))
OFF = [(0.0, 0.0), (2161.0, -10.0), (4262.0, -10.0), (6338.0, -10.0)]
PAN = [(248039, 250190), (250190, 252331), (252331, 254422), (254422, 256498)]
Y0, Y1 = -458149, -450649
KATAD = ['BODRUM KAT', 'ZEMİN KAT', '1. KAT', '2. KAT']

def _segs(F, lays, win):
    x0, y0, x1, y1 = win
    out = []
    for r in F:
        if r[0] not in 'LP' or r[1] not in lays: continue
        q = [p[:2] for p in (r[2] if r[0] == 'P' else r[2][:2])]
        if not (x0 <= q[0][0] <= x1 and y0 <= q[0][1] <= y1): continue
        for a, b in zip(q[:-1], q[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > 0.3: out.append((a, b))
    return out

def build():
    cols_det = pickle.load(open(VY + 'cols.pkl', 'rb'))
    M = pickle.load(open(VY + 'mimT.pkl', 'rb'))          # güncel bodrum (bodrum paftasına oturtulmuş)
    # kolonlar: bodrum(eski+güncel) ∪ zemin, yerel (bodrum) çerçevede; tüm katlarda aynı taşıyıcı ızgara
    loc = list(cols_det[0]) + [translate(g, -OFF[1][0], -OFF[1][1]) for g in cols_det[1]]
    for r in M:
        if r[0] == 'P' and r[1] == 'ARC_Duvar':
            q = [p[:2] for p in r[2]]
            if 5 <= len(q) <= 9 and abs(q[0][0] - q[-1][0]) + abs(q[0][1] - q[-1][1]) < 1:
                g = Polygon(q)
                if g.is_valid and 300 < g.area < 30000: loc.append(g)
    COLS_LOC = unary_union([g.buffer(0.5) for g in loc])
    K = {}
    for i in range(4):
        win = (PAN[i][0], Y0, PAN[i][1], Y1)
        if i == 0:
            segs = _segs(M, {'ARC_Duvar', '0'}, win)
        else:
            segs = _segs(S, {'MKDU0'}, win)
        walls = [s for s in segs if not (25 < abs(math.degrees(math.atan2(s[1][1] - s[0][1], s[1][0] - s[0][0]))) % 180 < 65
                                       or 115 < abs(math.degrees(math.atan2(s[1][1] - s[0][1], s[1][0] - s[0][0]))) % 180 < 155)
                 or math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]) > 120]
        faces = [g for g in polygonize(unary_union([LineString(s) for s in walls])) if g.area > 50]
        fp = unary_union(faces).buffer(3).buffer(-3)
        if fp.geom_type == 'MultiPolygon': fp = max(fp.geoms, key=lambda g: g.area)
        fp = Polygon(fp.exterior)
        cols = translate(COLS_LOC, OFF[i][0], OFF[i][1])
        K[i] = dict(walls=walls, foot=fp, cols=cols, off=OFF[i], win=win)
        print(KATAD[i], len(walls), 'duvar parçası, taban', round(fp.area / 1e4, 1), 'm²')
    return K

if __name__ == '__main__':
    K = build()
    pickle.dump(K, open(VY + 'geo.pkl', 'wb'))
