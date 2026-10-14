# -*- coding: utf-8 -*-
"""Kontrol önizlemesi (PNG, depoya konmaz): python3 onizle.py girdi.dxf cikti.png [dpi] [x0 y0 x1 y1]"""
import sys, ezdxf, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy
from ezdxf import bbox

src, out = sys.argv[1], sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150
d = ezdxf.readfile(src)
msp = d.modelspace()
if len(sys.argv) > 7:
    x0, y0, x1, y1 = map(float, sys.argv[4:8])
else:
    e = bbox.extents(msp); x0, y0, x1, y1 = e.extmin.x, e.extmin.y, e.extmax.x, e.extmax.y
W = 20
fig = plt.figure(figsize=(W, W * (y1 - y0) / (x1 - x0)))
ax = fig.add_axes([0, 0, 1, 1])
Frontend(RenderContext(d), MatplotlibBackend(ax), config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(msp, finalize=False)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
fig.savefig(out, dpi=dpi)
