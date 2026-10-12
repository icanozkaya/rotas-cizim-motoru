import sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
D = ezdxf.readfile(sys.argv[1])
FROZEN = {'MTY-SPRINKLER-KORUMA', 'MTY-SPRINKLER-ALAN'}
from ezdxf import bbox as _bb
_C = _bb.Cache()
def _in(e, win):
    try:
        b = _bb.extents([e], fast=True, cache=_C)
    except Exception:
        return True
    if not b.has_data: return False
    return not (b.extmax.x < win[0] or b.extmin.x > win[2] or b.extmax.y < win[1] or b.extmin.y > win[3])
def render(win, out, w=20, dpi=110, frozen=FROZEN):
    x0, y0, x1, y1 = win
    fig = plt.figure(figsize=(w, w * (y1 - y0) / (x1 - x0)))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off'); ax.set_aspect('equal')
    ctx = RenderContext(D)
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR, lineweight_scaling=0.5)
    msp = D.modelspace()
    Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_layout(msp, finalize=False, filter_func=lambda e: e.dxf.get('layer', '0') not in frozen and _in(e, win))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    fig.savefig(out, dpi=dpi, facecolor='white'); plt.close(fig); print(out)
if __name__ == '__main__':
    win = tuple(float(v) for v in sys.argv[2:6]); render(win, sys.argv[6], float(sys.argv[7]) if len(sys.argv) > 7 else 20)
