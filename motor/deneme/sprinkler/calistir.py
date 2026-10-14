# -*- coding: utf-8 -*-
"""Kullanım:  python3 motor/deneme/sprinkler/calistir.py GIRDI.json [CIKTI.dxf] [--png ONIZLEME.png]
Girdi biçimi: BENIOKU.md. Çıktı: tek DXF (R2018) — plan + çap/başlık etiketleri + hidrolik en uzak alan +
hesap özeti + düğüm tablosu + ekipman listesi + lejant + notlar."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ag import tasarla
from hidrolik import hesapla
from cizim import ciz
from kontrol import kontrol


def calistir(girdi, cikti, png=None):
    P = json.load(open(girdi))
    net = tasarla(P)
    hes = hesapla(net, P)
    c, van = ciz(P, net, hes, cikti)
    rap = kontrol(cikti, P['dis_hat'], len(c.Z) + 1)      # +1: kolon (riser) etiketi
    rap['etiketsiz'] = c.etiketsiz
    if png:
        onizle(cikti, png)
    return P, net, hes, rap


def onizle(dxf, png, kutu=None, dpi=200):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import ezdxf
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
    d = ezdxf.readfile(dxf)
    # yalnız önizleme: matplotlib arka ucu sabit genişlikli polyline'ları birleşik dolguda kaybedebiliyor;
    # genişlik çizgi kalınlığına çevrilir (DXF dosyası değişmez)
    for e in d.modelspace().query('LWPOLYLINE'):
        w = e.dxf.get('const_width', 0)
        if w:
            e.dxf.const_width = 0
            e.dxf.lineweight = min(211, int(w * 12))
    if kutu is None:
        from ezdxf import bbox
        e = bbox.extents(d.modelspace())
        kutu = (e.extmin.x, e.extmin.y, e.extmax.x, e.extmax.y)
    asp = (kutu[3] - kutu[1]) / (kutu[2] - kutu[0])
    fig = plt.figure(figsize=(20, 20 * asp))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE)
    Frontend(RenderContext(d), MatplotlibBackend(ax), config=cfg).draw_layout(d.modelspace())
    ax.set_aspect('equal')
    if kutu:
        ax.set_xlim(kutu[0], kutu[2])
        ax.set_ylim(kutu[1], kutu[3])
    fig.savefig(png, dpi=dpi)
    plt.close(fig)


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    png = sys.argv[sys.argv.index('--png') + 1] if '--png' in sys.argv else None
    if png in a:
        a.remove(png)
    girdi = a[0]
    cikti = a[1] if len(a) > 1 else os.path.splitext(girdi)[0] + '.dxf'
    P, net, hes, rap = calistir(girdi, cikti, png)
    o = hes['ozet']
    print(f"{P.get('proje')}: {o['toplam_bas']} başlık, en uzak alan {o['mahal']} ({o['N']} başlık), "
          f"Q={o['Qs']:.0f} l/dk, P_kolon={o['P_kolon']:.2f} bar, pompa {o['Qp_m3h']:.1f} m³/h @ {o['Hp']:.1f} mSS, "
          f"depo {o['V']:.1f} m³, vmax {o['vmax']:.2f} m/s")
    for k, v in rap.items():
        print(f'  {k}: {v}')
    print('ÇIKTI:', cikti)
