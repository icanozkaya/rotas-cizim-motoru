"""Kırpılmış PNG kanıt: kontrol edilen çizimden pencere (siyah zemin, kullanıcının ekran görüntüleri gibi), bulgu
noktaları sarı halka ile işaretli; isteğe bağlı sağda aynı pencerenin REFERANS (new_block, kullanıcının kendi MTY
çizimi) görünümü. Çizim ezdxf drawing eklentisi (matplotlib) ile; pencereye giren varlıklar bbox dizininden seçilir."""
import math
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from ezdxf import bbox
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy


class Cizici:
    def __init__(self, doc, ad=''):
        self.doc = doc
        self.ad = ad
        self.ctx = RenderContext(doc)
        cache = bbox.Cache()
        self.bb = []
        for e in doc.modelspace():
            try:
                b = bbox.extents([e], fast=True, cache=cache)
                if b.has_data:
                    self.bb.append((e, b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
            except Exception:
                pass

    def varliklar(self, w):
        x0, y0, x1, y1 = w
        return [e for e, a, b, c, d in self.bb if c >= x0 and a <= x1 and d >= y0 and b <= y1]

    def kirp(self, w, png, isaretler=(), baslik='', genislik_in=6.5, dpi=100, beyaz=False):
        x0, y0, x1, y1 = w
        W = genislik_in
        H = max(2.0, W * (y1 - y0) / (x1 - x0))
        fig = plt.figure(figsize=(W, H + 0.35))
        ax = fig.add_axes([0, 0, 1, H / (H + 0.35)])
        cfg = Configuration(background_policy=BackgroundPolicy.WHITE if beyaz else BackgroundPolicy.BLACK)
        be = MatplotlibBackend(ax, adjust_figure=False)
        fe = Frontend(self.ctx, be, config=cfg)
        try:
            fe.draw_entities(self.varliklar(w))
        except Exception:
            pass
        be.finalize()
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        r = max(12.0, 0.02 * (x1 - x0))
        for p in isaretler:
            ax.add_patch(Circle((p[0], p[1]), r, fill=False, edgecolor='yellow', linewidth=2.0, zorder=50))
            ax.add_patch(Circle((p[0], p[1]), r * 1.6, fill=False, edgecolor='yellow', linewidth=0.8, zorder=50, linestyle='--'))
        fig.patch.set_facecolor('black' if not beyaz else 'white')
        import textwrap
        fig.text(0.01, 1 - 0.02, '\n'.join(textwrap.wrap(baslik, 95)[:2]), color='white' if not beyaz else 'black',
                 fontsize=7.5, va='top', ha='left', family='DejaVu Sans')
        fig.savefig(png, dpi=dpi, facecolor=fig.get_facecolor())
        plt.close(fig)
        kucult(png)
        return png


def kucult(png, renk=96):
    """PNG'yi paletli (96 renk) kaydeder: depoya giren kanıt dosyaları ~1/3 boyuta iner"""
    try:
        from PIL import Image
        im = Image.open(png).convert('RGB').quantize(colors=renk, method=Image.Quantize.MEDIANCUT)
        im.save(png, optimize=True)
    except Exception:
        pass


def yan_yana(sol_png, sag_png, out, sol_ad='KONTROL EDİLEN', sag_ad='REFERANS (new_block, kullanıcı çizimi)'):
    from PIL import Image, ImageDraw, ImageFont
    try:
        import matplotlib
        font = ImageFont.truetype(os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data', 'fonts', 'ttf', 'DejaVuSans.ttf'), 13)
    except Exception:
        font = None
    a = Image.open(sol_png).convert('RGB')
    b = Image.open(sag_png).convert('RGB')
    h = max(a.height, b.height) + 22
    im = Image.new('RGB', (a.width + b.width + 12, h), (40, 40, 40))
    im.paste(a, (0, 22))
    im.paste(b, (a.width + 12, 22))
    d = ImageDraw.Draw(im)
    d.text((6, 3), sol_ad, fill=(255, 255, 0), font=font)
    d.text((a.width + 18, 3), sag_ad, fill=(0, 255, 255), font=font)
    im.save(out)
    kucult(out)
    return out
