# -*- coding: utf-8 -*-
"""pafta_bitir deneme çalıştırıcısı.
    python3 motor/deneme/pafta_bitir/calistir.py [--png KLASOR]
deneme_param.json: giriş, ekler (@KAPAK = şablondan üretilen kapak), kapak yazıları."""
import json
import os
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
DEPO = os.path.abspath(os.path.join(BURASI, '..', '..', '..'))
sys.path.insert(0, BURASI)
import pafta_bitir as PB  # noqa: E402
import kapak  # noqa: E402


def onizleme(yol, klasor, pencereler):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy
    doc = ezdxf.readfile(yol)
    os.makedirs(klasor, exist_ok=True)
    for ad, (x0, y0, x1, y1), dpi in pencereler:
        fig = plt.figure(figsize=(max(4, min(40, (x1 - x0) / (y1 - y0) * 8)), 8))
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        Frontend(ctx, MatplotlibBackend(ax), config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(
            doc.modelspace(), finalize=True,
            filter_func=lambda e: _gor(e, (x0, y0, x1, y1)))
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        fig.savefig(os.path.join(klasor, ad + '.png'), dpi=dpi)
        plt.close(fig)


def _gor(e, r):
    from ezdxf import bbox
    try:
        b = bbox.extents([e], fast=True)
    except Exception:
        return True
    return not b.has_data or not (b.extmax.x < r[0] or b.extmin.x > r[2] or b.extmax.y < r[1] or b.extmin.y > r[3])


def main():
    P = json.load(open(os.path.join(BURASI, 'deneme_param.json'), encoding='utf-8'))
    d = lambda p: os.path.join(DEPO, p)
    os.makedirs(os.path.dirname(d(P['cikis'])), exist_ok=True)
    kapak.kapak_uret(d(P['kapak_cikis']), P.get('kapak_metin'), P.get('kapak_konum'))
    ekler = []
    for ek in P['ekler']:
        ek = dict(ek)
        ek['yol'] = d(P['kapak_cikis']) if ek['yol'] == '@KAPAK' else d(ek['yol'])
        ekler.append(ek)
    R = PB.bitir(d(P['giris']), d(P['cikis']), ekler=ekler)
    PB.rapor_yaz(R)
    if '--png' in sys.argv:
        k = sys.argv[sys.argv.index('--png') + 1]
        s = R['sinir_son']
        lp = R['lejant_pafta']
        e0 = R['ekler'][0] if R['ekler'] else None
        pen = [('genel', (s[0] - 200, s[1] - 200, s[2] + 200, s[3] + 200), 150),
               ('lejant_metraj', (lp[0] - 300, lp[1] - 100, lp[2] + 100, lp[3] + 100), 200)]
        if e0:
            pen.append(('ekler_sol_alt', (e0['x0'] - 100, min(e['y0'] for e in R['ekler']) - 100,
                                           R['paftalar'][0][2] + 3000, max(e['y1'] for e in R['ekler']) + 100), 150))
        onizleme(d(P['cikis']), k, pen)
    return R


if __name__ == '__main__':
    main()
