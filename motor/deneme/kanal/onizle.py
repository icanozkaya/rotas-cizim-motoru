# -*- coding: utf-8 -*-
"""DXF -> PNG önizleme (kontrol için; PNG depoya konmaz). Kullanım: python3 onizle.py girdi.dxf cikti.png [x0 y0 x1 y1]"""
import sys
import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy


def onizle(dxf, png, pencere=None, dpi=200, boy=(30, 18)):
    doc = ezdxf.readfile(dxf)
    if pencere:
        boy = (24, 24 * (pencere[3] - pencere[1]) / (pencere[2] - pencere[0]))
    fig = plt.figure(figsize=boy)
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(doc.modelspace(), finalize=True)
    if pencere:
        ax.set_xlim(pencere[0], pencere[2]); ax.set_ylim(pencere[1], pencere[3])
    fig.savefig(png, dpi=dpi)
    plt.close(fig)


if __name__ == "__main__":
    w = [float(x) for x in sys.argv[3:7]] if len(sys.argv) >= 7 else None
    onizle(sys.argv[1], sys.argv[2], w)
