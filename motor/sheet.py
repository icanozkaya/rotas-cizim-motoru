import sys, os, glob, math
import ezdxf, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
files = sorted(glob.glob(sys.argv[2]))
n = len(files); cols = 4; rows = math.ceil(n / cols)
fig = plt.figure(figsize=(cols * 4, rows * 4.4))
for i, f in enumerate(files):
    ax = fig.add_subplot(rows, cols, i + 1)
    try:
        doc = ezdxf.readfile(f)
        Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace(), finalize=True)
    except Exception as e:
        ax.text(0.1, 0.5, str(e)[:40])
    ax.set_title(os.path.basename(f).split('__')[-1][:28], fontsize=7)
    ax.set_facecolor('black')
fig.savefig(sys.argv[1], dpi=90, facecolor='#303030')
