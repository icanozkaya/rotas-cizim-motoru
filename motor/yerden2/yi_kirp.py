"""yerden2 — kontrolör tarzı yan yana kırpımlar: üretilen DXF (solda) / kullanıcının new_block çizimi (sağda).

    python3 motor/yerden2/yi_kirp.py [çıkış_klasörü]

Kontrolörün kaydırmaları: plan dx = +22 762 cm, şema dx = +22 568 cm (KONTROL_YERDEN_TUR1.md).
Pencereler model json'daki mahal kutularından (zon listesi) kurulur; zon numaraları üretimden okunur.
"""
import json
import os
import sys

import ezdxf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from ezdxf import bbox as BB  # noqa: E402
from ezdxf.addons.drawing import RenderContext, Frontend  # noqa: E402
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend  # noqa: E402
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
DXF = KOK + '/proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf'
MODEL = KOK + '/proje/denemeler/yerden2/NB_YERDEN_ISITMA_model.json'
REF = '/tmp/claude-0/y2/new_block.dxf'
DX_PLAN = 22762.0
DX_SEMA = 22568.0


class Cizici:
    def __init__(self, yol):
        self.doc = ezdxf.readfile(yol)
        self.ent = []
        cache = BB.Cache()
        for e in self.doc.modelspace():
            try:
                b = BB.extents([e], cache=cache)
                if b.has_data:
                    self.ent.append((e, (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)))
            except Exception:
                pass

    def png(self, w, yol, en_px=1600):
        x0, y0, x1, y1 = w
        sec = [e for e, b in self.ent if b[2] >= x0 and b[0] <= x1 and b[3] >= y0 and b[1] <= y1
               and (b[2] - b[0]) < 3 * (x1 - x0) + 5000]
        fig = plt.figure(figsize=(10, 10 * (y1 - y0) / (x1 - x0)))
        ax = fig.add_axes([0, 0, 1, 1])
        cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR,
                            lineweight_scaling=0.6)
        ctx = RenderContext(self.doc)
        try:
            ctx.current_layout_properties.set_colors('#ffffff')     # WIPEOUT = beyaz zemin (AutoCAD'deki gibi)
        except Exception:
            pass
        Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_entities(sec)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect('equal')
        ax.axis('off')
        fig.savefig(yol, dpi=en_px / 10, facecolor='white')
        plt.close(fig)


def yan_yana(a, b, yol, bas):
    A, B = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    H = 1200
    A = A.resize((int(A.width * H / A.height), H))
    B = B.resize((int(B.width * H / B.height), H))
    out = Image.new('RGB', (A.width + B.width + 30, H + 50), 'white')
    out.paste(A, (0, 50))
    out.paste(B, (A.width + 30, 50))
    d = ImageDraw.Draw(out)
    try:
        f = ImageFont.truetype('DejaVuSans.ttf', 22)
    except Exception:
        f = ImageFont.load_default()
    d.text((20, 12), bas[0], fill='black', font=f)
    d.text((A.width + 50, 12), bas[1], fill='black', font=f)
    out.save(yol)
    os.remove(a)
    os.remove(b)


def pencereler(model):
    bb = {}
    for kat in model['katlar']:
        for d in kat['daireler'].values():
            for m in d['mahaller']:
                bb[m['zon']] = m.get('bbox')

    def w(*zon, pay=60):
        bs = [bb[z] for z in zon if bb.get(z)]
        return (min(b[0] for b in bs) - pay, min(b[1] for b in bs) - pay,
                max(b[2] for b in bs) + pay, max(b[3] for b in bs) + pay)
    return bb, w


def main(cikis=None):
    cikis = cikis or KOK + '/proje/denemeler/yerden2/onizleme/kirp'
    os.makedirs(cikis, exist_ok=True)
    model = json.load(open(MODEL))
    bb, w = pencereler(model)
    zon_ad = {m['zon']: m['ad'] for k in model['katlar'] for d in k['daireler'].values() for m in d['mahaller']}

    def bul(kat, *anahtar):
        """kat + daire + ad parçası -> zon"""
        out = []
        for k in model['katlar']:
            if k['kat'] != kat:
                continue
            for d in k['daireler'].values():
                for m in d['mahaller']:
                    for dn, ad in anahtar:
                        if d['no'] == dn and ad in m['ad']:
                            out.append(m['zon'])
        return out
    # kontrolörün kırpımlarıyla aynı mahal grupları (zon numaraları üretimden)
    gruplar = [
        ('01_Z_D3_yatak_oda_wcbanyo', bul('Z', ('D3', 'yatak'), ('D3', 'oda'), ('D3', 'wc'))),
        ('02_Z_D3_mutfak_hol', bul('Z', ('D3', 'mutfak'), ('D3', 'antre'))),
        ('03_Z_D3_salon', bul('Z', ('D3', 'salon'))),
        ('04_Z_D2_yatak_hol', bul('Z', ('D2', 'yatak'), ('D2', 'antre'))),
        ('05_Z_banyolar_D1_D2', bul('Z', ('D1', 'banyo'), ('D2', 'banyo'))),
        ('06_Z_D1_yatak_hol', bul('Z', ('D1', 'yatak'), ('D1', 'antre'))),
        ('07_Z_D2_salon', bul('Z', ('D2', 'salon'))),
        ('08_Z_mutfaklar_D1_D2', bul('Z', ('D1', 'mutfak'), ('D2', 'mutfak'))),
        ('09_Z_D1_salon', bul('Z', ('D1', 'salon'))),
        ('10_1kat_D6_banyo_yatak', bul('1', ('D6', 'banyo'), ('D6', 'yatak'))),
        ('10b_1kat_D5_wcbanyo_hol', bul('1', ('D5', 'wc'), ('D5', 'antre'))),
    ]
    A = Cizici(DXF)
    R = Cizici(REF)
    for ad, zs in gruplar:
        if not zs:
            print('[kirp] boş grup', ad)
            continue
        x0, y0, x1, y1 = w(*zs)
        A.png((x0, y0, x1, y1), cikis + '/_a.png')
        R.png((x0 + DX_PLAN, y0, x1 + DX_PLAN, y1), cikis + '/_b.png')
        yan_yana(cikis + '/_a.png', cikis + '/_b.png', '%s/%s.png' % (cikis, ad),
                 ('MOTOR: ' + ' '.join(zs), 'REFERANS (kullanıcı)'))
        print('[kirp]', ad, zs)
    # şema
    sys.path.insert(0, BURASI)
    import yi_sema as SE
    xs = [p[0] for e in A.doc.modelspace().query('LWPOLYLINE[layer=="ROTAS-PAFTA"]') for p in e.get_points('xy')]
    X1 = max(xs)
    A.png((SE.X0, SE.PY0, X1, SE.PY1), cikis + '/_a.png', 3000)
    R.png((SE.X0 + DX_SEMA, SE.PY0, SE.X0 + DX_SEMA + 6693, SE.PY1), cikis + '/_b.png', 3000)
    yan_yana(cikis + '/_a.png', cikis + '/_b.png', cikis + '/13_sema_genel.png',
             ('MOTOR şema (genişlik %.0f)' % (X1 - SE.X0), 'REFERANS şema (6693)'))
    w2 = (SE.X0 + 60, SE.BANT0 - 200, SE.X0 + 1200, SE.BANT0 + 420)
    A.png(w2, cikis + '/_a.png', 2000)
    R.png((w2[0] + DX_SEMA, w2[1], w2[2] + DX_SEMA, w2[3]), cikis + '/_b.png', 2000)
    yan_yana(cikis + '/_a.png', cikis + '/_b.png', cikis + '/15_sema_kombi_kollektor.png', ('MOTOR', 'REFERANS'))
    w3 = (SE.X0 + 150, SE.BANT0 - 40, SE.X0 + 420, SE.BANT0 + 120)
    A.png(w3, cikis + '/_a.png', 2000)
    R.png((w3[0] + DX_SEMA, w3[1], w3[2] + DX_SEMA, w3[3]), cikis + '/_b.png', 2000)
    yan_yana(cikis + '/_a.png', cikis + '/_b.png', cikis + '/16_kollektor_yakin.png', ('MOTOR', 'REFERANS'))
    print('[kirp]', cikis)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
