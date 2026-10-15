#!/usr/bin/env python3
"""Etiketsiz pis su parçası sayımı (kontrolör tur 3 R1 ölçüsü): kat planlarında her pis su parçası (polyline
segmenti, >= 20 cm) için 30 cm içinde bir 'n SB' etiketi var mı.

    python3 motor/sihhi2/etiketsiz_say.py [cizim.dxf ...] [--liste]

Varsayılan: proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf ve kullanıcının /tmp/claude-0/uu/new_block.dxf.
Kat pencereleri plan.py PAFTA (kullanıcı çizimiyle aynı koordinatlar)."""
import os
import re
import sys

import ezdxf
from shapely.geometry import LineString, Point, box
from shapely import STRtree

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
sys.path.insert(0, KOK + '/motor/kontrolor')
sys.path.insert(0, KOK + '/motor/deneme/denetim')
import kutu as KUTU  # noqa: E402
import denetle as D  # noqa: E402

PAFTA = {'Z': (252513.0, 254578.0), '1': (254578.0, 256617.0), '2': (256617.0, 258656.0)}
PY0, PY1 = -444050.0, -441150.0
SB_RE = re.compile(r'^\s*\d+(\.\d+)?\s*SB\s*$', re.I)


def segmentler(msp):
    out = []
    for e in msp:
        lay = e.dxf.get('layer', '0')
        if e.dxftype() not in ('LINE', 'LWPOLYLINE', 'POLYLINE') or not D.pis_su_katmani(lay):
            continue
        if e.dxftype() == 'LINE':
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif e.dxftype() == 'LWPOLYLINE':
            pts = [tuple(p) for p in e.get_points('xy')]
            if e.closed:
                pts.append(pts[0])
        else:
            pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        for a, b in zip(pts[:-1], pts[1:]):
            out.append(LineString([a, b]))
    return out


def sb_kutulari(msp):
    out = []
    for e in msp:
        t = e.dxftype()
        if t == 'TEXT' and SB_RE.match(e.dxf.text or ''):
            out.append(e)
        elif t == 'MTEXT' and SB_RE.match(e.plain_text() or ''):
            out.append(e)
        elif t == 'INSERT':
            for a in e.attribs:
                if SB_RE.match(a.dxf.text or ''):
                    out.append(a)
    gs = []
    for e in out:
        g = KUTU.yazi_kutusu(e)
        if g is None or g.is_empty:
            p = e.dxf.insert
            g = Point(p.x, p.y).buffer(5)
        gs.append(g)
    return gs


def say(yol, liste=False):
    doc = ezdxf.readfile(yol)
    msp = doc.modelspace()
    segs = segmentler(msp)
    kut = sb_kutulari(msp)
    agac = STRtree(kut) if kut else None
    sonuc = {}
    for k, (x0, x1) in PAFTA.items():
        w = box(x0, PY0, x1, PY1)
        ps = [s for s in segs if s.length >= 20 and w.contains(s.centroid)]
        # sıkı ölçü: etiket yalnız EN YAKIN parçasını kapsar (30 cm içinde)
        kapsanan = set()
        for g in kut:
            if not w.intersects(g):
                continue
            ds = [(g.distance(s), i) for i, s in enumerate(ps)]
            ds = [d for d in ds if d[0] <= 30]
            if ds:
                dm = min(ds)[0]
                kapsanan.update(i for d, i in ds if d <= dm + 1.0)
        siki = [s for i, s in enumerate(ps) if i not in kapsanan]
        yok = []
        for s in ps:
            ok = False
            if agac is not None:
                for i in agac.query(s.buffer(30)):
                    if kut[i].distance(s) <= 30:
                        ok = True
                        break
            if not ok:
                yok.append(s)
        sonuc[k] = (len(ps), yok, siki)
    print(os.path.basename(yol))
    for k, (n, yok, siki) in sonuc.items():
        print('  kat %s: parça %d, etiketsiz %d (>= 50 cm: %d); sıkı (etiket yalnız en yakın parçayı kapsar): %d' % (
            k, n, len(yok), sum(1 for s in yok if s.length >= 50), len(siki)))
        if liste:
            for s in siki:
                print('      %.0f cm @ (%.0f, %.0f)' % (s.length, s.centroid.x, s.centroid.y))
    return sonuc


if __name__ == '__main__':
    argv = [a for a in sys.argv[1:] if not a.startswith('--')]
    liste = '--liste' in sys.argv
    if not argv:
        argv = [KOK + '/proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf', '/tmp/claude-0/uu/new_block.dxf']
    for y in argv:
        say(y, liste)
