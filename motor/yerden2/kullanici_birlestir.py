"""yerden2 — motor çıktısını kullanıcının kendi yerden ısıtma dosyasına (aynı mimari, kaydırılmış koordinat) yerleştirir.

python3 kullanici_birlestir.py KULLANICI.dxf MOTOR.dxf CIKIS.dxf [--dx 22761.9 --dy 0]

  * kullanıcının mimarisi, çerçeveleri ve başlıkları aynen kalır (\\U+XXXX kaçışları Türkçe karaktere çevrilir);
  * kullanıcının bağlantısız serpantinleri (MTY-PEX-BORU) motorun kollektöre bağlı devreleriyle değiştirilir;
  * motorun mimari kopyası (ROTAS-MIMARI*) ve plan başlıkları alınmaz; kolon şeması planların sağına gelir.
dx/dy verilmezse iki dosyadaki mahal yazılarından (salon / merdiven) otomatik bulunur.
"""
import argparse
import re

import ezdxf
from ezdxf import xref
from ezdxf.math import Matrix44

KAC = re.compile(r'\\U\+([0-9A-Fa-f]{4})')


def coz(t):
    return KAC.sub(lambda m: chr(int(m.group(1), 16)), t)


def ofset_bul(ku, mo):
    def yaz(doc):
        out = {}
        for e in doc.modelspace().query('TEXT MTEXT'):
            t = e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()
            t = coz(t).strip()
            if t in ('salon', 'merdiven'):
                out.setdefault(t, []).append((e.dxf.insert.x, e.dxf.insert.y))
        return out
    a, b = yaz(ku), yaz(mo)
    m1 = min(b['merdiven'])
    k1 = min(a['merdiven'])
    return k1[0] - m1[0], k1[1] - m1[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('kullanici')
    ap.add_argument('motor')
    ap.add_argument('cikis')
    ap.add_argument('--dx', type=float)
    ap.add_argument('--dy', type=float)
    a = ap.parse_args()
    ku = ezdxf.readfile(a.kullanici)
    mo = ezdxf.readfile(a.motor)
    dx, dy = (a.dx, a.dy) if a.dx is not None else ofset_bul(ku, mo)
    print('ofset', round(dx, 2), round(dy, 2))
    from ezdxf import bbox
    plan_sinir = bbox.extents(mo.modelspace().query('*[layer=="ROTAS-MIMARI"]')).extmax.x + 50
    hedef = ezdxf.new('R2018', setup=True)
    hedef.header['$INSUNITS'] = 5
    # 1) kullanıcının dosyası (serpantinleri hariç)
    for e in ku.modelspace():
        if e.dxftype() in ('TEXT', 'MTEXT'):
            if e.dxftype() == 'TEXT':
                e.dxf.text = coz(e.dxf.text)
            else:
                e.text = coz(e.text)
    xref.load_modelspace(ku, hedef, filter_fn=lambda e: e.dxf.layer != 'MTY-PEX-BORU')
    n0 = len(hedef.modelspace())

    def al(e):
        lay = e.dxf.get('layer', '0')
        if lay.startswith('ROTAS-MIMARI'):
            return False
        if lay == 'ROTAS-PAFTA-BASLIK':
            p = e.dxf.get('insert', None)
            if p is not None and p[0] < plan_sinir:
                return False
        return True
    xref.load_modelspace(mo, hedef, filter_fn=al)
    T = Matrix44.translate(dx, dy, 0)
    for e in list(hedef.modelspace())[n0:]:
        e.transform(T)
    hedef.saveas(a.cikis)
    print('yazıldı', a.cikis, len(hedef.modelspace()), 'nesne')


if __name__ == '__main__':
    main()
