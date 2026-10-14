"""R4 yazı-yazı çakışma kontrolü: bütün TEXT / MTEXT / görünür ATTRIB (mimari dahil). Sayılmayan: mimari-mimari çifti
(kaynak mimari dosya) ve aynı INSERT'in kendi öznitelikleri. Eşik: küçük yazının alanının %2'si.
Kullanım: python3 ykontrol4.py dosya.dxf"""
import sys
import ezdxf
from ezdxf import disassemble
from shapely.geometry import Polygon
from shapely.strtree import STRtree


def polys(msp):
    out = []
    for e in msp:
        t = e.dxftype()
        ys = []
        if t in ('TEXT', 'MTEXT'):
            ys = [e]
        elif t == 'INSERT':
            ys = [a for a in e.attribs if not a.is_invisible]
        for y in ys:
            s = (y.dxf.text if y.dxftype() != 'MTEXT' else y.plain_text()).strip()
            if not s:
                continue
            try:
                v = [(p.x, p.y) for p in disassemble.make_primitive(y).vertices()]
                pg = Polygon(v) if len(v) >= 4 else None
            except Exception:
                pg = None
            if pg is not None and pg.is_valid and pg.area > 0:
                out.append((y.dxf.layer, s, pg, e.dxf.handle))
    return out


def cakisma(msp, oran=0.02):
    ys = polys(msp)
    tr = STRtree([y[2] for y in ys])
    out = []
    mi = lambda x: 'MIMARI' in x.upper()
    for i, (l, s, pg, h) in enumerate(ys):
        for j in tr.query(pg):
            j = int(j)
            if j <= i:
                continue
            l2, s2, p2, h2 = ys[j]
            if h == h2 or (mi(l) and mi(l2)):
                continue
            a = pg.intersection(p2).area
            if a > oran * min(pg.area, p2.area):
                out.append((l, s[:25], l2, s2[:25], (round(pg.centroid.x), round(pg.centroid.y))))
    return out


if __name__ == '__main__':
    doc = ezdxf.readfile(sys.argv[1])
    r = cakisma(doc.modelspace())
    import collections
    print(len(r))
    print(collections.Counter((a[0], a[2]) for a in r).most_common(20))
    for x in r[:60]:
        print(x)
