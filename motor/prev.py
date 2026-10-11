import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon as MPoly

ACI = {1: '#ff0000', 2: '#d4c400', 3: '#00a000', 4: '#00b0b0', 5: '#0000ff', 6: '#d000d0', 7: '#000000', 8: '#9a9a9a',
       10: '#ff3030', 11: '#ff8080', 15: '#806060', 30: '#ff7f00', 31: '#ff9f40', 41: '#c08000', 101: '#00a060',
       135: '#4060a0', 211: '#8040a0', 9: '#c0c0c0'}


def render(recs, layers, win, out, w=20, dpi=100, minh=0, top=None):
    x0, y0, x1, y1 = win
    segs, cols = [], []
    tsegs, tcols = [], []
    top = top or set()
    fig = plt.figure(figsize=(w, w * (y1 - y0) / (x1 - x0)))
    ax = fig.add_axes([0, 0, 1, 1])
    ppu = w * dpi / (x1 - x0)
    inside = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    for r in recs:
        k, lay = r[0], r[1]
        NREC = {'L': 4, 'P': 5, 'C': 4, 'S': 5, 'T': 7, 'W': 99}
        ci = r[NREC[k]] if len(r) > NREC[k] else layers.get(lay, (7,))[0]
        if k == 'W':
            if any(inside(p) for p in r[2]):
                ax.add_patch(MPoly(r[2], closed=True, facecolor='white', edgecolor=ACI.get(ci, '#000000') if r[3] else 'none',
                                   lw=0.6 if r[3] else 0, zorder=2))
            continue
        c = ACI.get(ci, '#000000')
        SG, CO = (tsegs, tcols) if id(r) in top else (segs, cols)
        if k == 'L':
            if inside(r[2]) or inside(r[3]):
                SG.append([r[2], r[3]]); CO.append(c)
        elif k == 'P':
            pts = r[2] + ([r[2][0]] if r[3] else [])
            if any(inside(p) for p in pts):
                SG.append(pts); CO.append(c)
        elif k == 'C':
            if inside(r[2]):
                cx, cy = r[2]; rr = r[3]
                SG.append([(cx + rr * math.cos(t / 16 * math.pi), cy + rr * math.sin(t / 16 * math.pi)) for t in range(33)]); CO.append(c)
        elif k == 'S':
            if inside(r[2]):
                ax.add_patch(MPoly([r[2], r[3], r[4]], closed=True, color=c, lw=0, zorder=2.5 if id(r) in top else 1))
        elif k == 'T':
            p, s, h, rot, al = r[2], r[3], r[4], r[5], r[6]
            if inside(p) and h * ppu > 2 and h >= minh:
                ha = {'L': 'left', 'C': 'center', 'R': 'right'}[al[-1]] if al[-1] in 'LCR' else 'left'
                va = 'center' if al.startswith('M') else ('top' if al.startswith('T') else ('bottom' if al.startswith('B') else 'baseline'))
                ax.text(p[0], p[1], s, fontsize=max(2, h * ppu * 0.72), color=c, rotation=rot, ha=ha, va=va, rotation_mode='anchor', zorder=3)
    ax.add_collection(LineCollection(segs, colors=cols, linewidths=0.35, zorder=1))
    ax.add_collection(LineCollection(tsegs, colors=tcols, linewidths=0.35, zorder=2.5))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off')
    fig.savefig(out, dpi=dpi); plt.close(fig)
