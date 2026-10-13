import sys, pickle, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
from ezdxf import bbox as _bb

S = None


def under(ax, win, lays=('MKDU0',), src='/tmp/claude-0/vy/sih.pkl', extra=()):
    global S
    if S is None: S = pickle.load(open(src, 'rb'))
    x0, y0, x1, y1 = win
    segs = []
    for r in list(S) + list(extra):
        if r[1] not in lays and r[1] != '__': continue
        if r[0] == 'L': q = [r[2][0], r[2][1]]
        elif r[0] == 'P': q = list(r[2])
        else: continue
        if any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in q):
            segs += [(a[:2], b[:2]) for a, b in zip(q[:-1], q[1:])]
    ax.add_collection(LineCollection(segs, colors='#b0b0b0', linewidths=0.35))


def render(dxf, win, out, w=16, dpi=110, lays=('MKDU0',), extra=(), frozen=('MTY-SPRINKLER-KORUMA',)):
    D = ezdxf.readfile(dxf) if isinstance(dxf, str) else dxf
    x0, y0, x1, y1 = win
    fig = plt.figure(figsize=(w, w * (y1 - y0) / (x1 - x0)))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off'); ax.set_aspect('equal')
    under(ax, win, lays, extra=extra)
    C = _bb.Cache()

    def inw(e):
        try:
            b = _bb.extents([e], fast=True, cache=C)
        except Exception:
            return True
        if not b.has_data: return False
        return not (b.extmax.x < x0 or b.extmin.x > x1 or b.extmax.y < y0 or b.extmin.y > y1)
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR, lineweight_scaling=0.6)
    Frontend(RenderContext(D), MatplotlibBackend(ax), config=cfg).draw_layout(
        D.modelspace(), finalize=False, filter_func=lambda e: e.dxf.get('layer', '0') not in frozen and inw(e))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    fig.savefig(out, dpi=dpi, facecolor='white'); plt.close(fig)
    print(out)


if __name__ == '__main__':
    a = sys.argv
    render(a[1], tuple(float(v) for v in a[2:6]), a[6], float(a[7]) if len(a) > 7 else 16)
