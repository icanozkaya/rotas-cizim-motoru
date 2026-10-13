"""son R üzerinde üst üste binen çizgi kontrolü (boru/şema katmanları, mimari hariç)"""
import pickle, sys
from shapely.geometry import LineString
from shapely.strtree import STRtree
_pk = pickle.load(open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/p3/et_R.pkl', 'rb'))
R = _pk[0]; BLK = _pk[2] if len(_pk) > 2 else []
PROT = {id(q) for b in BLK for q in b['recs']}
PIPE = ('BORU', 'DRENAJ', 'PEX', 'KOLLETOR', 'SEMA')
SKIP = ('MIMARI', 'TARAMA', 'CERCEVE', 'ANTET', 'PAFTA')
segs, meta = [], []
for i, r in enumerate(R):
    if r[0] not in 'LP' or any(s in r[1].upper() for s in SKIP) or id(r) in PROT: continue
    pts = [r[2], r[3]] if r[0] == 'L' else list(r[2]) + ([r[2][0]] if r[3] else [])
    for a, b in zip(pts, pts[1:]):
        if a != b: segs.append(LineString([a, b])); meta.append((i, r[1]))
tree = STRtree(segs); out = []
for a, g in enumerate(segs):
    for b in tree.query(g.buffer(0.05)):
        b = int(b)
        if b <= a or meta[a][0] == meta[b][0]: continue
        it = g.intersection(segs[b].buffer(0.05))
        if it.length > 1.0 and (any(p in meta[a][1].upper() for p in PIPE) or any(p in meta[b][1].upper() for p in PIPE)):
            c = it.centroid; out.append((meta[a][1], meta[b][1], round(c.x), round(c.y), round(it.length, 1)))
import collections
print('ÜST ÜSTE BİNEN:', len(out)); print(collections.Counter((x[0], x[1]) for x in out).most_common(25))
for o in sorted(out, key=lambda t: -t[4])[:40]: print('  ', o)
