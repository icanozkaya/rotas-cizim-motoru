# -*- coding: utf-8 -*-
"""Sembol kütüphanesi DXF'ini ve otomatik lejant deneme DXF'ini üretir.
    python3 motor/deneme/semboller/olustur.py [--png KLASOR]
Çıktılar: proje/denemeler/semboller/SEMBOL_KUTUPHANESI.dxf, OTOMATIK_LEJANT_DENEME.dxf
PNG önizleme yalnız kontrol içindir; depoya konmaz (--png ile depo dışı klasöre yazılır)."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ezdxf                                   # noqa: E402
from ezdxf.enums import TextEntityAlignment as TA   # noqa: E402
import sembol as S                             # noqa: E402

CIKTI = os.path.join(S.DEPO, 'proje', 'denemeler', 'semboller')
PARAM = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deneme_param.json')


def png(doc, yol, dpi=110, kutu=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy, LineweightPolicy
    from ezdxf import bbox
    msp = doc.modelspace()
    b = bbox.extents(msp, fast=True)
    x0, y0, x1, y1 = kutu or (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)
    w, h = x1 - x0, y1 - y0
    fig = plt.figure(figsize=(max(4, w / 120), max(4, h / 120)), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR,
                        lineweight_policy=LineweightPolicy.RELATIVE, min_lineweight=0.15)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    fig.savefig(yol)
    plt.close(fig)


def deneme_semasi(yol):
    """Otomatik lejant testi için örnek (DENEME) şema: kazan dairesi + hidrofor + gaz + yangın + havalandırma parçaları."""
    P = json.load(open(PARAM, encoding='utf-8'))
    doc = ezdxf.new('R2018', setup=True)
    doc.header['$INSUNITS'] = 5
    S.hazirla(doc)
    m = doc.modelspace()
    S._metin(m, 'DENEME — OTOMATİK LEJANT TESTİ (örnek değerler)', (0, 520), 25, S.LEJ_BAS, TA.BOTTOM_LEFT, 0.9)
    # ısıtma gidiş hattı: kazan -> kelebek -> pislik tutucu -> pompa -> çekvalf -> küresel
    gid, don = 'ROTAS-ISITMA-GIDIS', 'ROTAS-ISITMA-DONUS'
    S.ciz(m, 'kazan', 60, 260, no='K-01')
    S.hat(m, (60 + 12.5, 302.5), (900, 302.5), [(0.12, 'kelebek_vana', 'V-01'), (0.27, 'pislik_tutucu', 'V-02'),
                                           (0.45, 'pompa', 'P-01'), (0.62, 'cekvalf', 'V-03'), (0.80, 'kuresel_vana', 'V-04')], gid, 'ROTAS-ISITMA-SEMBOL')
    S.hat(m, (900, 217.5), (47.5, 217.5), [(0.2, 'kuresel_vana', 'V-05'), (0.5, 'kalorimetre', 'KM-01')], don, 'ROTAS-ISITMA-SEMBOL')
    S.ciz(m, 'genlesme_kapali', 600, 120, no='GT-01')
    S.ciz(m, 'manometre', 150, 302.5, no='M-01', katman='ROTAS-ISITMA-SEMBOL')
    S.ciz(m, 'termometre', 520, 302.5, no='T-01', katman='ROTAS-ISITMA-SEMBOL')
    S.ciz(m, 'emniyet_ventili', 100, 302.5, katman='ROTAS-ISITMA-SEMBOL')
    # sıhhi: şebeke -> sayaç -> küresel -> hidrofor tankı
    ss = 'ROTAS-SIHHI-SOGUK-SU'
    S.hat(m, (0, 0), (700, 0), [(0.1, 'kuresel_vana', 'V-06'), (0.25, 'su_sayaci', 'SS-01'), (0.4, 'cekvalf', 'V-07'),
                                (0.55, 'basinc_dusurucu', 'V-08'), (0.7, 'pompa_fk', 'P-02')], ss, 'ROTAS-SIHHI-SEMBOL')
    S.ciz(m, 'membranli_tank', 760, 40, no='MT-01')
    for i in range(P['dalgic_pompa_adedi']):
        S.ciz(m, 'dalgic_pompa', 900 + i * 80, -60, no='DP-%02d' % (i + 1))
    # doğalgaz
    S.hat(m, (0, -200), (600, -200), [(0.15, 'gaz_kesme_vanasi', 'V-09'), (0.4, 'regulator', 'R-01'), (0.65, 'gaz_sayaci', 'GS-01'),
                                      (0.85, 'gaz_cihaz_vanasi', 'V-10')], 'ROTAS-DOGALGAZ-BORU', 'ROTAS-DOGALGAZ-SEMBOL')
    # yangın: kolon zon vanası seti + sprinkler dizisi
    yb = 'ROTAS-YANGIN-SPRINKLER-BORU'
    S.hat(m, (0, -400), (1100, -400), [(0.08, 'izlenebilir_kelebek', 'V-11'), (0.18, 'cekvalf', 'V-12'), (0.28, 'akis_anahtari', 'FS-01')], yb, 'ROTAS-YANGIN-SEMBOL')
    for i in range(P['sarkik_sprinkler_adedi']):
        S.ciz(m, 'sprinkler_sarkik', 420 + i * 110, -400)
    for i in range(P['dik_sprinkler_adedi']):
        S.ciz(m, 'sprinkler_dik', 420 + i * 110, -520)
    m.add_lwpolyline([(420, -400), (420, -520)], dxfattribs={'layer': yb})
    S.ciz(m, 'yangin_dolabi_plan', 1250, -400, no='YD-01')
    # havalandırma
    for i in range(P['difuzor_adedi']):
        S.ciz(m, 'difuzor_4', 1300 + i * 150, 200)
    S.ciz(m, 'yangin_damperi', 1300, 50)
    S.ciz(m, 'cati_fani', 1600, 50, no='F-01')
    # kullanıcı tarzı grup blok içinde iç içe sembol (özyinelemeli sayım testi)
    grp = doc.blocks.new('DENEME-RADYATOR-GRUBU')
    S.ciz(grp, 'radyator_panel', 0, 0)
    S.ciz(grp, 'termostatik_vana', -15, 10)
    S.ciz(grp, 'rakorlu_donus', 120, 10)
    for i in range(P['radyator_grubu_adedi']):
        m.add_blockref('DENEME-RADYATOR-GRUBU', (1100 + i * 180, 400), dxfattribs={'layer': 'ROTAS-ISITMA-SEMBOL'})
    sayim = S.otomatik_lejant(doc)
    doc.saveas(yol)
    return doc, sayim


if __name__ == '__main__':
    os.makedirs(CIKTI, exist_ok=True)
    pngdir = sys.argv[sys.argv.index('--png') + 1] if '--png' in sys.argv else None
    d1 = S.kutuphane_dxf(os.path.join(CIKTI, 'SEMBOL_KUTUPHANESI.dxf'))
    print('kütüphane bloğu:', sum(1 for b in d1.blocks if not b.name.startswith('*')))
    d2, say = deneme_semasi(os.path.join(CIKTI, 'OTOMATIK_LEJANT_DENEME.dxf'))
    print('sayım:', say)
    if pngdir:
        os.makedirs(pngdir, exist_ok=True)
        png(d1, os.path.join(pngdir, 'kutuphane.png'), dpi=60)
        png(d2, os.path.join(pngdir, 'deneme.png'), dpi=70)
