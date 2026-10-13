# -*- coding: utf-8 -*-
"""Ofis mahalleri (yerden ısıtma için): kullanıcının MTY devrelerinden mahal dikdörtgeni, zon no, kapı (devre ucu) çıkarımı.
Koordinatlar S çerçevesi (1. kat); 2. kat = +D12."""
import math, pickle, re, collections
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union
from veri import *
import odaplan as RM

S = pickle.load(open('/tmp/claude-0/vy/sih.pkl', 'rb'))
HX = ROW['H'][0] - ROW['S'][0]
PEX = [r for r in S if r[0] == 'P' and r[1] == 'MTY-PEX-BORU']
RT = [r for r in S if r[0] == 'T' and r[1] == 'MTY-RADYATÖR']
WT = [(r[2][0][:2], float(re.match(r'([\d.]+)W', r[2][1].strip()).group(1))) for r in RT if re.match(r'^[\d.]+W$', r[2][1].strip())]
ZT = [(r[2][0][:2], r[2][1].strip()) for r in RT if re.match(r'^Z\d+$', r[2][1].strip())]
LAB1 = RM.labels((254422, -447800, 256498, -440300))


def devreler(kat):
    """S çerçevesinde (1. kat koordinatına indirgenmiş) devreler: ends, bbox, zon"""
    dx = HX + (D12[0] if kat == 3 else 0.0)
    out = []
    for r in PEX:
        q = [(p[0] - dx, p[1]) for p in r[2]]
        if not (254422 < q[0][0] < 256498): continue
        a, b = q[0], q[-1]
        g = LineString(q)
        bb = g.bounds
        # etiket: devre kutusundaki W yazısı -> en yakın Z yazısı
        cand = [(math.dist(((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2), (p[0] - dx, p[1])), p) for p, w in WT
                if bb[0] - 5 <= p[0] - dx <= bb[2] + 5 and bb[1] - 5 <= p[1] <= bb[3] + 5]
        zone = None
        if cand:
            wp = min(cand)[1]
            z = min(ZT, key=lambda t: math.dist(t[0], wp))
            if math.dist(z[0], wp) < 120: zone = z[1]
        out.append(dict(a=a, b=b, bb=bb, pts=q, zone=zone, L=g.length / 100.0))
    return out


def ofis_odalari(k):
    """1. kat koordinatında ofis k'nin mahalleri"""
    poly = Polygon(OFIS_S1[k]['poly'])
    dv = [c for c in devreler(2) if poly.buffer(10).contains(Point(((c['a'][0] + c['b'][0]) / 2, (c['a'][1] + c['b'][1]) / 2)))]
    byz = collections.defaultdict(list)
    for c in dv:
        byz[c['zone'] or ('?' + str(id(c)))].append(c)
    rooms = []
    for z, cs in byz.items():
        x0 = min(c['bb'][0] for c in cs) - 10; y0 = min(c['bb'][1] for c in cs) - 10
        x1 = max(c['bb'][2] for c in cs) + 10; y1 = max(c['bb'][3] for c in cs) + 10
        r = box(x0, y0, x1, y1)
        nm = [l for l in LAB1 if r.contains(Point(l['p'])) and l['ad'] not in ('IŞIKLIK',)]
        name = nm[0]['ad'] if nm else 'ODA'
        A = nm[0]['m2'] if nm and nm[0]['m2'] else r.area / 1e4
        # kapı: devre uçlarının ortası (MTY devre girişi kapı tarafında)
        ends = [((c['a'][0] + c['b'][0]) / 2, (c['a'][1] + c['b'][1]) / 2) for c in cs]
        e = ends[0]
        dists = {'S': e[1] - y0, 'N': y1 - e[1], 'W': e[0] - x0, 'E': x1 - e[0]}
        wall = min(dists, key=dists.get)
        door = (min(max(e[0], x0), x1), min(max(e[1], y0), y1), wall)
        rooms.append(dict(zone=z, name=name, rect=(x0, y0, x1, y1), A=A, door=door, n_mty=len(cs), ends=ends))
    return rooms


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/tmp/claude-0/vy/s')
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig = plt.figure(figsize=(12, 40)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_aspect('equal'); ax.axis('off')
    segs = RM.segs_in((254422, -447800, 256498, -440300))
    ax.add_collection(LineCollection(segs, colors='#aaa', linewidths=0.4))
    for k in OFIS_S1:
        R = ofis_odalari(k)
        for r in R:
            x0, y0, x1, y1 = r['rect']
            ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], 'r-', lw=0.8)
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, f"{k} {r['zone']} {r['name']}\n{r['A']:.1f} n={r['n_mty']}", fontsize=5)
            ax.plot(r['door'][0], r['door'][1], 'bo', ms=3)
        print(k, [(r['zone'], r['name'], round(r['A'], 1), r['door'][2]) for r in R])
    ax.set_xlim(254422, 256498); ax.set_ylim(-447800, -440300)
    fig.savefig('/tmp/claude-0/vy/inv/odalar.png', dpi=80)
