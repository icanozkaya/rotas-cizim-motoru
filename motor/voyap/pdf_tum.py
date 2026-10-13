import sys, os, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
from ezdxf import bbox as _bb
from PIL import Image
VY = '/tmp/claude-0/vy/'
t0 = time.time()
D = ezdxf.readfile(sys.argv[1] if len(sys.argv) > 1 else VY + 'MEKANIK_TAM.dxf')
print('okundu', round(time.time() - t0))
FROZEN = {'MTY-SPRINKLER-KORUMA', 'MTY-SPRINKLER-ALAN', 'MTY-SPRINKLER-ALAN-1'}
C = _bb.Cache()
ENTS = []
for e in D.modelspace():
    if e.dxf.get('layer', '0') in FROZEN: continue
    if e.dxftype() == 'INSERT' and e.dxf.name not in D.blocks: continue
    try:
        b = _bb.extents([e], fast=True, cache=C)
    except Exception:
        continue
    if not b.has_data: continue
    ENTS.append((e, b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
print('bbox', len(ENTS), round(time.time() - t0))


def render(win, out, w=15, dpi=120, title=None):
    x0, y0, x1, y1 = win
    sel = {id(e) for e, a, b, c, d in ENTS if not (c < x0 or a > x1 or d < y0 or b > y1)}
    fig = plt.figure(figsize=(w, w * (y1 - y0) / (x1 - x0)))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off'); ax.set_aspect('equal')
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR, lineweight_scaling=0.5)
    Frontend(RenderContext(D), MatplotlibBackend(ax), config=cfg).draw_layout(D.modelspace(), finalize=False, filter_func=lambda e: id(e) in sel)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    if title: ax.text(x0 + (x1 - x0) * 0.01, y1 - (y1 - y0) * 0.01, title, fontsize=14, va='top', color='#333')
    fig.savefig(out, dpi=dpi, facecolor='white'); plt.close(fig)
    return out


S = [(250242, 252393), (252393, 254534), (254534, 256625), (256625, 258701)]
H = [(280585, 282737), (282737, 284877), (284877, 286969), (286969, 289044)]
Y = [(250190, 252331), (252331, 254422), (254422, 256498)]
K = ['BODRUM', 'ZEMİN', '1. KAT', '2. KAT']
pages = []
for (a, b), k in zip(S, K):
    pages.append(render((a, -447827, b, -440327), VY + f'pp_s{k}.png', 15, 120, f'SIHHİ TESİSAT - {k} KAT PLANI'))
pages.append(render((258701, -444100, 276712, -440327), VY + 'pp_s_sema1.png', 30, 110))
pages.append(render((258701, -447827, 276712, -444000), VY + 'pp_s_sema2.png', 30, 110))
for (a, b), k in zip(H, K):
    pages.append(render((a, -447827, b, -440327), VY + f'pp_h{k}.png', 15, 120, f'ISITMA TESİSATI - {k} KAT PLANI'))
pages.append(render((289044, -444100, 315152, -440327), VY + 'pp_h_sema1.png', 30, 110))
pages.append(render((289044, -447827, 302000, -444000), VY + 'pp_h_sema2.png', 30, 110))
pages.append(render((248039, -468471, 250190, -460971), VY + 'pp_v_b.png', 15, 120, 'HAVALANDIRMA - BODRUM KAT'))
pages.append(render((250190, -468471, 252331, -460971), VY + 'pp_v_z.png', 15, 120, 'HAVALANDIRMA - ZEMİN KAT'))
pages.append(render((252400, -468471, 266000, -460971), VY + 'pp_v_sema.png', 30, 110))
pages.append(render((266000, -468471, 276712, -460971), VY + 'pp_v_tab.png', 30, 110))
for (a, b), k in zip([(248039, 250190)] + Y, K):
    pages.append(render((a, -458149, b, -450649), VY + f'pp_y{k}.png', 15, 120, f'YANGIN TESİSATI - {k} KAT PLANI'))
pages.append(render((256650, -457200, 264000, -450900), VY + 'pp_y_sema.png', 30, 110))
pages.append(render((264200, -455000, 270800, -450700), VY + 'pp_y_tab.png', 30, 110))
ims = [Image.open(p).convert('RGB') for p in pages]
out = sys.argv[2] if len(sys.argv) > 2 else VY + 'out/VOYAP_MEKANIK_ONIZLEME.pdf'
ims[0].save(out, save_all=True, append_images=ims[1:], resolution=120)
print('pdf ok', out, round(time.time() - t0))
