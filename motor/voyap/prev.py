"""önizleme: kullanıcı mimarisi/başlıkları (gri) + EK (renkli, ezdxf drawing)"""
import pickle, sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy, LineweightPolicy
VY = '/tmp/claude-0/vy/'
S = pickle.load(open(VY + 'sih.pkl', 'rb'))
U = pickle.load(open(VY + 'heads_user.pkl', 'rb'))
EKD = ezdxf.readfile(sys.argv[1] if len(sys.argv) > 1 else VY + 'YANGIN_EK.dxf')

def bg(ax, win, skip_bodrum=False):
    x0, y0, x1, y1 = win; segs = []
    for r in S:
        if r[0] not in 'LP' or r[1] in ('MTY-SPRINKLER-NOZUL', 'MTY-SPRINKLER-ALAN', 'MTY-SPRINKLER-ALAN-1', 'ANTED'): continue
        if skip_bodrum and r[1] == 'MKDU0' and 248039 <= r[2][0][0] < 250190 and -458149 < r[2][0][1] < -450649: continue
        q = r[2] if r[0] == 'P' else r[2][:2]
        if any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in q): segs += [(a[:2], b[:2]) for a, b in zip(q[:-1], q[1:])]
    ax.add_collection(LineCollection(segs, colors='#c8c8c8', linewidths=0.25))
    for i in U:
        for x, y, n in U[i]:
            if x0 <= x <= x1 and y0 <= y <= y1 and not (248235 < x < 248640 and -451720 < y < -450860):
                ax.add_patch(plt.Circle((x, y), 4.2, fill=False, color='#d4a000', lw=0.5))
    for r in S:
        if r[0] == 'T' and r[1] in ('MKDU0', '0') and x0 <= r[2][0][0] <= x1 and y0 <= r[2][0][1] <= y1:
            pass

def render(win, out, w=20, skip_bodrum=False, dpi=110):
    x0, y0, x1, y1 = win
    fig = plt.figure(figsize=(w, w * (y1 - y0) / (x1 - x0)))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.axis('off'); ax.set_aspect('equal')
    bg(ax, win, skip_bodrum)
    ctx = RenderContext(EKD)
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR, lineweight_scaling=0.5)
    Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_layout(EKD.modelspace(), finalize=False)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    fig.savefig(out, dpi=dpi, facecolor='white'); plt.close(fig)
    print(out)

if __name__ == '__main__':
    win = tuple(float(v) for v in sys.argv[2:6]); out = sys.argv[6]; w = float(sys.argv[7]) if len(sys.argv) > 7 else 20
    render(win, out, w, skip_bodrum=win[0] < 250190)
