"""Bir flat.pkl'den pencere render et: win.py flat.pkl out.png x0 y0 x1 y1 [genislik_inch]"""
import sys, math, pickle, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


def clean(t):
    t = re.sub(r'\\U\+([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1), 16)), t)
    t = re.sub(r'\\[AaCcFfHhQqTtWwp][^;]*;', '', t)
    return t.replace('\\P', ' ').replace('{', '').replace('}', '').replace('%%c', 'Ø').replace('%%C', 'Ø').replace('%%d', '°').replace('%%D', '°').replace('%%U', '').replace('%%u', '').replace('$', r'\$')


flat = pickle.load(open(sys.argv[1], 'rb'))
x0, y0, x1, y1 = map(float, sys.argv[3:7])
W = float(sys.argv[7]) if len(sys.argv) > 7 else 24
H = W * (y1 - y0) / (x1 - x0)
fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1])
ins = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
segs = []
for r in flat:
    if r[0] == 'L':
        if ins(r[2][0]) or ins(r[2][1]): segs.append([r[2][0], r[2][1]])
    elif r[0] == 'P':
        if any(ins(p) for p in r[2]): segs.append(r[2])
    elif r[0] == 'C':
        cx, cy, rr = r[2]
        if ins((cx, cy)): segs.append([(cx + rr * math.cos(t / 12 * math.pi), cy + rr * math.sin(t / 12 * math.pi)) for t in range(25)])
ax.add_collection(LineCollection(segs, colors='k', linewidths=0.3))
ppu = W * 100 / (x1 - x0)
for r in flat:
    if r[0] == 'T':
        p, s, h = r[2]
        if ins(p) and h * ppu > 3:
            ax.text(p[0], p[1], clean(s)[:80], fontsize=max(2.5, h * ppu * 0.62), color='#0030c0')
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off')
fig.savefig(sys.argv[2], dpi=100); plt.close(fig)
