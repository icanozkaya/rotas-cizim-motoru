# -*- coding: utf-8 -*-
"""R3/R4/R5 teslim denetimi (14.10.2026 (B) talimatı) — kazan_dairesi/kontrol.py ortak denetleyicisini kullanır:
MTY bloğu / katmanı 0, köprü (bulge) 0, boru-boru kesişmesi 0, etiket–sembol eşleşmesi %100 (kazan dairesi numaraları),
elektrik (SINYAL) katmanı 0. Temsili mimari (ROTAS-MIMARI-*) çakışma sayımına girmez.
R4: ONAYLI kazan dairesi paftası (plan_kesit.onayli_kazan_dairesi, çerçevesinde XDATA 'ONAYLI_KAZAN_DAIRESI') kullanıcı
onaylı çizimdir; MTY / atlatma / etiket kuralları ona uygulanmaz → o bölge ana denetimden çıkarılır, ayrıca bilgi verilir.
Kullanım: python3 kontrol.py proje/denemeler/radyator/*_R5.dxf"""
import os
import sys
import tempfile

import ezdxf
from ezdxf import bbox

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kazan_dairesi'))
import kontrol as KK        # noqa: E402


def onayli_bolgeler(doc):
    out = []
    for e in doc.modelspace().query('LWPOLYLINE'):
        try:
            if any(v == 'ONAYLI_KAZAN_DAIRESI' for _, v in e.get_xdata('ROTAS')):
                b = bbox.extents([e], fast=True)
                out.append((b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
        except Exception:
            pass
    return out


def ayir(yol):
    """onaylı bölge dışını (ana denetim) ve içini (bilgi) iki geçici DXF olarak yazar"""
    doc = ezdxf.readfile(yol)
    bol = onayli_bolgeler(doc)
    if not bol:
        return yol, None, []

    def icinde(e):
        b = bbox.extents([e], fast=True)
        if not b.has_data:
            return False
        cx, cy = (b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2
        return any(x0 - 1 <= cx <= x1 + 1 and y0 - 1 <= cy <= y1 + 1 for x0, y0, x1, y1 in bol)
    ic = {e.dxf.handle for e in doc.modelspace() if icinde(e)}
    td = tempfile.mkdtemp(prefix='radk_')
    yollar = []
    for ad, sil in (('dis', lambda h: h in ic), ('ic', lambda h: h not in ic)):
        d = ezdxf.readfile(yol)
        m = d.modelspace()
        for e in list(m):
            if sil(e.dxf.handle):
                m.delete_entity(e)
        y = os.path.join(td, ad + '.dxf')
        d.saveas(y)
        yollar.append(y)
    return yollar[0], yollar[1], bol


def denetle(yol):
    dis, ic, bol = ayir(yol)
    oz, sorun, ornek, hata = KK.denetle(dis)
    print(yol)
    if bol:
        print('  (onaylı kazan dairesi paftası ana denetim dışında:', [tuple(round(v) for v in b) for b in bol], ')')
    print('  ÖZET:', oz)
    print('  diğer çakışma (bilgi):', dict(sorun) or 'yok')
    for x in hata[:10]:
        print('  ETİKET EŞLEŞMEDİ:', x)
    if ic:
        d = ezdxf.readfile(ic)
        mty, mlay = KK.mty_say(d)
        print('  ONAYLI KAZAN DAİRESİ paftası (bilgi, kurala tabi değil): MTY blok', sum(mty.values()),
              '- nesne', len(d.modelspace()))
    return oz


if __name__ == '__main__':
    for y in sys.argv[1:]:
        if y.endswith('.dxf'):
            denetle(y)
