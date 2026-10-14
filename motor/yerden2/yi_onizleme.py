"""yerden2 — önizleme PNG'leri (ezdxf drawing + matplotlib) ve referansla yan yana karşılaştırma.

    python3 motor/yerden2/yi_onizleme.py      (DXF zaten üretilmişse)
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
CIKIS = KOK + '/proje/denemeler/yerden2/onizleme'
REF = KOK + '/kutuphane/arastirma/referans/yerden'


def _ciz(dxf):
    import ezdxf
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
    doc = ezdxf.readfile(dxf)
    fig = plt.figure(figsize=(20, 20))
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR,
                        lineweight_scaling=0.6)
    Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_layout(doc.modelspace(), finalize=True)
    return fig, ax


def kaydet(fig, ax, lim, yol, en_px=2200):
    x0, y0, x1, y1 = lim
    w = x1 - x0
    h = y1 - y0
    fig.set_size_inches(10, 10 * h / w)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    fig.savefig(yol, dpi=en_px / 10, facecolor='white')


def yan_yana(a, b, yol, baslik=('ROTAŞ yerden2 (motor)', 'Kullanıcı çizimi (referans)')):
    A, B = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    H = 1400
    A = A.resize((int(A.width * H / A.height), H))
    B = B.resize((int(B.width * H / B.height), H))
    out = Image.new('RGB', (A.width + B.width + 30, H + 60), 'white')
    out.paste(A, (0, 60))
    out.paste(B, (A.width + 30, 60))
    try:
        from PIL import ImageDraw, ImageFont
        d = ImageDraw.Draw(out)
        try:
            f = ImageFont.truetype('DejaVuSans.ttf', 26)
        except Exception:
            f = ImageFont.load_default()
        d.text((20, 20), baslik[0], fill='black', font=f)
        d.text((A.width + 50, 20), baslik[1], fill='black', font=f)
    except Exception:
        pass
    out.save(yol)


def ciz(dxf, KTS=None):
    sys.path.insert(0, BURASI)
    import yerden as Y
    os.makedirs(CIKIS, exist_ok=True)
    fig, ax = _ciz(dxf)
    M = Y.M
    for k in Y.KATLAR:
        w = M.win(k)
        kaydet(fig, ax, (w[0] - 20, w[1] - 200, w[2] + 20, w[3] + 20), '%s/plan_%s.png' % (CIKIS, k))
    # yakın görünümler (referans kırpımlarıyla aynı bölgeler, zemin kat)
    w = M.win('Z')
    kaydet(fig, ax, (w[0] + 150, w[3] - 600, w[0] + 1000, w[3] - 50), '%s/yakin_Z_sol_ust.png' % CIKIS, 1800)
    kaydet(fig, ax, (w[0] + 600, w[1] + 400, w[0] + 1500, w[1] + 1100), '%s/yakin_Z_orta.png' % CIKIS, 1800)
    # şema
    import yi_sema as SE
    import ezdxf
    doc = ezdxf.readfile(dxf)
    xs = [p[0] for e in doc.modelspace().query('LWPOLYLINE[layer=="ROTAS-PAFTA"]') for p in e.get_points('xy')]
    x1 = max(xs) + 20 if xs else SE.X0 + 7000
    kaydet(fig, ax, (SE.X0, SE.PY0, x1, SE.PY1), '%s/kolon_semasi.png' % CIKIS, 3000)
    kaydet(fig, ax, (SE.X0 + 60, SE.BANT0 - 200, SE.X0 + 2400, SE.BANT0 + 420), '%s/kolon_semasi_daire.png' % CIKIS, 2400)
    plt.close(fig)
    yan_yana('%s/plan_Z.png' % CIKIS, REF + '/01_zemin_kat_plani_genel.png', '%s/KARSILASTIRMA_zemin.png' % CIKIS)
    yan_yana('%s/kolon_semasi_daire.png' % CIKIS, REF + '/12_kolon_semasi_daire_D3.png',
             '%s/KARSILASTIRMA_sema_daire.png' % CIKIS)
    yan_yana('%s/yakin_Z_sol_ust.png' % CIKIS, REF + '/02_yatak_odasi_Z05_iki_devre_Z04_tek_devre.png',
             '%s/KARSILASTIRMA_yatak_odasi.png' % CIKIS)
    print('[onizleme]', CIKIS)


if __name__ == '__main__':
    ciz(KOK + '/proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf')
