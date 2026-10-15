#!/usr/bin/env python3
"""yerden2 — kullanıcının blokları ile bizim ROTAS-YI- bloklarının yan yana / piksel karşılaştırması.

    python3 motor/yerden2/yi_blok_karsilastir.py [çıkış_klasörü]

Her blok için kullanıcının new_block'taki örnek yerleşimi YALNIZ o INSERT çizilerek (çevresindeki boru vb. olmadan)
ve bizim bloğumuz aynı öznitelik değerleriyle, aynı pencere/ölçekte siyah zeminde (AutoCAD görünüşü) çizilir.
Ölçü: çizili piksel kümelerinin örtüşmesi (1 px toleransla; F1 = 2·|A∩B| / (|A|+|B|)) ve renk uyumu.
"""
import os
import sys

import ezdxf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from ezdxf import bbox as BB  # noqa: E402
from ezdxf.addons.drawing import RenderContext, Frontend  # noqa: E402
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend  # noqa: E402
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import yi_bloklar as YB  # noqa: E402

KOK = YB.KOK
CIK = KOK + '/kutuphane/arastirma/kontrol_png/yerden_tur5_uretici'


def _ciz(doc, ents, w, yol, px=1400):
    x0, y0, x1, y1 = w
    fig = plt.figure(figsize=(10, 10 * (y1 - y0) / (x1 - x0)), dpi=px / 10)
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.BLACK, color_policy=ColorPolicy.COLOR,
                        lineweight_scaling=0.0, min_lineweight=0.5)
    ctx = RenderContext(doc)
    try:
        ctx.current_layout_properties.set_colors('#000000')
    except Exception:
        pass
    Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_entities(ents)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.savefig(yol, facecolor='black')
    plt.close(fig)
    return Image.open(yol).convert('RGB')


def _maske(im):
    a = np.asarray(im).astype(int)
    return a.sum(axis=2) > 90


def _f1(A, B):
    Ai = Image.fromarray((A * 255).astype('uint8')).filter(ImageFilter.MaxFilter(3))
    Bi = Image.fromarray((B * 255).astype('uint8')).filter(ImageFilter.MaxFilter(3))
    Ad, Bd = np.asarray(Ai) > 0, np.asarray(Bi) > 0
    tp_a = (A & Bd).sum()
    tp_b = (B & Ad).sum()
    if A.sum() + B.sum() == 0:
        return 1.0
    return (tp_a + tp_b) / float(A.sum() + B.sum())


def karsilastir(cik=CIK):
    os.makedirs(cik, exist_ok=True)
    src = ezdxf.readfile(YB.KAYNAK)
    msp = src.modelspace()
    sonuc = []
    for ad, kaynak_ad, sec, (dx, dy), eslem, sag, gizli in YB.TANIM:
        ins = msp.query('INSERT[name=="%s"]' % kaynak_ad)[sec]
        I = ins.dxf.insert
        b = BB.extents([ins])
        pay = 0.06 * max(b.extmax.x - b.extmin.x, b.extmax.y - b.extmin.y)
        w = (b.extmin.x - pay, b.extmin.y - pay, b.extmax.x + pay, b.extmax.y + pay)
        im_k = _ciz(src, [ins], w, cik + '/_k.png')
        # bizim: aynı noktaya (ek kaydırma geri alınarak) aynı öznitelik değerleriyle
        doc = ezdxf.new('R2018', setup=True)
        doc.styles.add(YB.STIL, font='arial.ttf')
        doc.layers.add(YB.G_KAT, color=10)
        doc.layers.add(YB.D_KAT, color=30, linetype='DASHDOT')
        YB.hazirla(doc)
        m2 = doc.modelspace()
        attr = {}
        for a in ins.attribs:
            t = eslem.get(a.dxf.tag)
            if t and not a.is_invisible and not a.dxf.get('invisible', 0):
                attr[t] = a.dxf.text
        e = YB.yerlestir(m2, ad, (I[0] - dx, I[1] - dy), '0', attr)
        im_b = _ciz(doc, [e], w, cik + '/_b.png')
        A, B = _maske(im_k), _maske(im_b)
        f1 = _f1(A, B)
        f1_not = ''
        if ad == YB.ETIKET:
            # kullanıcının sabit yazıları aynalı yerleşimde ters görünüyor; bizde okunur (aynı kutuda) —
            # sol sütun (yazı hücreleri) dışarıda bırakılarak ölçü de verilir
            W_, H_ = im_k.size
            fx = lambda x: int((x - w[0]) / (w[2] - w[0]) * W_)  # noqa: E731
            fy = lambda y: int((w[3] - y) / (w[3] - w[1]) * H_)  # noqa: E731
            x0_, x1_ = fx(I[0] - 70 + 2), fx(I[0] - 70 + 95)
            y0_, y1_ = fy(I[1] - 1), fy(I[1] - 79)
            A2, B2 = A.copy(), B.copy()
            A2[y0_:y1_, x0_:x1_] = False
            B2[y0_:y1_, x0_:x1_] = False
            f1_not = ' (sol yazı sütunu hariç F1 %.3f)' % _f1(A2, B2)
        # renk uyumu: ortak piksellerde renk farkı
        ak, ab = np.asarray(im_k).astype(int), np.asarray(im_b).astype(int)
        ort = A & B
        renk = float((np.abs(ak[ort] - ab[ort]).sum(axis=1) < 90).mean()) if ort.any() else 0.0
        sonuc.append((ad, kaynak_ad, f1, renk, f1_not))
        # yan yana
        W_, H_ = im_k.size
        yan = Image.new('RGB', (2 * W_ + 20, H_ + 60), 'white')
        yan.paste(im_b, (0, 60))
        yan.paste(im_k, (W_ + 20, 60))
        dr = ImageDraw.Draw(yan)
        dr.text((10, 10), 'BİZİM: %s' % ad, fill='black')
        dr.text((W_ + 30, 10), 'KULLANICI: %s (new_block)   piksel F1 %.3f  renk %.3f%s' % (kaynak_ad, f1, renk, f1_not),
                fill='black')
        yan.save('%s/blok_%s.png' % (cik, ad.replace('ROTAS-YI-', '').lower()))
        # fark görüntüsü: kırmızı = yalnız bizde, yeşil = yalnız kullanıcıda
        fark = np.zeros(ak.shape, dtype='uint8')
        fark[A & B] = (200, 200, 200)
        fark[B & ~A] = (255, 0, 0)
        fark[A & ~B] = (0, 255, 0)
        Image.fromarray(fark).save('%s/blok_%s_fark.png' % (cik, ad.replace('ROTAS-YI-', '').lower()))
    for f in ('_k.png', '_b.png'):
        try:
            os.remove(cik + '/' + f)
        except OSError:
            pass
    for r in sonuc:
        print('[blok] %-28s <- %-20s F1 %.3f renk %.3f%s' % r)
    return sonuc


if __name__ == '__main__':
    karsilastir(sys.argv[1] if len(sys.argv) > 1 else CIK)
