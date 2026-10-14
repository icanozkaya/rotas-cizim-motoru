#!/usr/bin/env python3
"""sihhi2 — kat planı ETİKET denetimi (gerçek yazı tipi ölçüsüyle; ezdxf text2path, döndürme dahil).

    python3 motor/sihhi2/etiket_kontrol.py [dxf] [--ayrinti]

Sayılanlar (sıhhi katmanları, ROTAS-MIMARI* dışı yazılar):
  E1 etiket–etiket   : iki farklı INSERT/yazının glif kutuları kesişir (alan > 0,5 cm²)
  E2 etiket–mimari   : sıhhi yazı, mimari yazının (mahal adı, m², kapı/pencere ölçüsü) kutusunu keser
  E3 etiket–duvar    : sıhhi yazı, mimari tarama (HATCH: duvar/kolon taraması) alanını keser (> 1 cm²)
  E4 etiket–sembol   : sıhhi yazı, armatür/kolon/süzgeç sembol kutusunu keser
  E5 renk            : siyah ekranda görünmeyen renk (ACI 250–255, 8, 0/7 dışı koyu gri)
"""
import sys
import ezdxf
from ezdxf.addons import text2path
from shapely.geometry import MultiPoint, Polygon, box
from shapely import STRtree

KOK = __file__.rsplit('/motor/', 1)[0]
VARSAYILAN = KOK + '/proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf'
KOYU = set(range(250, 256)) | {8, 9, 18, 19, 248, 249}


def glif_kutusu(e):
    try:
        ps = text2path.make_paths_from_entity(e)
        v = [(p.x, p.y) for pa in ps for p in pa.flattening(0.5)]
        if len(v) >= 3:
            r = MultiPoint(v).minimum_rotated_rectangle
            if r.area > 0:
                return r
    except Exception:
        pass
    return None


def yazilar(msp):
    out = []
    for e in msp:
        t = e.dxftype()
        if t in ('TEXT', 'MTEXT'):
            out.append((e, e, e.dxf.layer))
        elif t == 'INSERT':
            for a in e.attribs:
                if not a.is_invisible and (a.dxf.text or '').strip():
                    out.append((a, e, e.dxf.layer))
    return out


def sembol_kutusu(e):
    from ezdxf import bbox
    try:
        b = bbox.extents([e])
        if b.has_data:
            return box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)
    except Exception:
        pass
    return None


SEMBOL = ('ROTAS-S2-PIS-KOLON', 'ROTAS-S2-YER-SUZGECI', 'ROTAS-S2-BALKON-SUZGECI', 'ROTAS-S2-KURESEL-VANA',
          'ROTAS-S2-ASPIRATOR', 'ROTAS-S2-MAKINE', 'ROTAS-S2-KOLON-YAGMUR')


def denetle(yol, ayrinti=False, pencere=None):
    doc = ezdxf.readfile(yol)
    msp = doc.modelspace()
    sih, mim = [], []
    for y, sahip, lay in yazilar(msp):
        g = glif_kutusu(y)
        if g is None:
            continue
        if pencere is not None and not g.intersects(pencere):
            continue
        (mim if lay.startswith('ROTAS-MIMARI') else sih).append((y, sahip, lay, g))
    tar = []
    for h in msp.query('HATCH'):
        if not h.dxf.layer.startswith('ROTAS-MIMARI'):
            continue
        for p in h.paths:
            try:
                vs = [(v[0], v[1]) for v in p.vertices] if hasattr(p, 'vertices') else \
                     [(ed.start[0], ed.start[1]) for ed in p.edges if hasattr(ed, 'start')]
                if len(vs) >= 3:
                    pg = Polygon(vs).buffer(0)
                    if pg.area > 50:
                        tar.append(pg)
            except Exception:
                pass
    sem = []
    for e in msp.query('INSERT'):
        if e.dxf.name.startswith(SEMBOL):
            b = sembol_kutusu(e)
            if b is not None:
                sem.append((e, b.buffer(-0.5)))
    bul = {'E1': [], 'E2': [], 'E3': [], 'E4': [], 'E5': []}
    for i in range(len(sih)):
        for j in range(i + 1, len(sih)):
            a, b = sih[i], sih[j]
            if a[1] is b[1]:
                continue
            if a[3].intersects(b[3]) and a[3].intersection(b[3]).area > 0.5:
                bul['E1'].append((a[0].dxf.text if a[0].dxftype() != 'MTEXT' else a[0].plain_text()[:20],
                                  b[0].dxf.text if b[0].dxftype() != 'MTEXT' else b[0].plain_text()[:20],
                                  tuple(round(c) for c in a[3].centroid.coords[0])))
    tm = STRtree([m[3] for m in mim]) if mim else None
    tt = STRtree(tar) if tar else None
    for y, sahip, lay, g in sih:
        s = y.dxf.text if y.dxftype() != 'MTEXT' else y.plain_text()[:20]
        if lay.startswith('ROTAS-PAFTA') or lay.startswith('ROTAS-LEJANT'):
            continue
        if tm is not None:
            for k in tm.query(g):
                if mim[k][3].intersection(g).area > 0.5:
                    bul['E2'].append((s, mim[k][0].dxf.text if mim[k][0].dxftype() != 'MTEXT' else mim[k][0].plain_text()[:15],
                                      tuple(round(c) for c in g.centroid.coords[0])))
        if tt is not None:
            for k in tt.query(g):
                if tar[k].intersection(g).area > 1.0:
                    bul['E3'].append((s, tuple(round(c) for c in g.centroid.coords[0])))
                    break
        for e, b in sem:
            if e is sahip:
                continue
            if b.intersects(g) and b.intersection(g).area > 0.5:
                bul['E4'].append((s, e.dxf.name, tuple(round(c) for c in g.centroid.coords[0])))
    for e in msp:
        if e.dxf.get('layer', '').startswith('ROTAS-MIMARI'):
            continue
        c = e.dxf.get('color', 256)
        if c in KOYU:
            bul['E5'].append((e.dxftype(), e.dxf.layer, c))
    for ad, l in doc.layers.items() if hasattr(doc.layers, 'items') else []:
        pass
    for L in doc.layers:
        if not L.dxf.name.startswith('ROTAS-MIMARI') and abs(L.dxf.color) in KOYU:
            bul['E5'].append(('LAYER', L.dxf.name, L.dxf.color))
    return bul


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    b = denetle(a[0] if a else VARSAYILAN)
    for k, v in b.items():
        print('%s: %d' % (k, len(v)))
        if '--ayrinti' in sys.argv:
            for q in v[:60]:
                print('   ', q)
