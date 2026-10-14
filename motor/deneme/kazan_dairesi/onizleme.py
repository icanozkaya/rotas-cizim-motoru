# -*- coding: utf-8 -*-
"""Kendi kontrolüm için PNG önizleme (depoya konmaz). Koyu zemin (AutoCAD görünümü)."""
import sys

import ezdxf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                   # noqa: E402
from ezdxf.addons.drawing import RenderContext, Frontend          # noqa: E402
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend     # noqa: E402
from ezdxf.addons.drawing.config import Configuration, LineweightPolicy  # noqa: E402


def png(dxf, out, pencere=None, dpi=200, gen=40):
    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()
    fig = plt.figure(figsize=(gen, gen * 0.5))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(lineweight_policy=LineweightPolicy.RELATIVE)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp, finalize=True)
    if pencere:
        x0, y0, x1, y1 = pencere
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        fig.set_size_inches(gen, gen * (y1 - y0) / (x1 - x0))
    fig.savefig(out, dpi=dpi, facecolor='#212830')
    plt.close(fig)


if __name__ == '__main__':
    pen = tuple(map(float, sys.argv[3].split(','))) if len(sys.argv) > 3 else None
    png(sys.argv[1], sys.argv[2], pen, dpi=int(sys.argv[4]) if len(sys.argv) > 4 else 100,
        gen=float(sys.argv[5]) if len(sys.argv) > 5 else 40)
