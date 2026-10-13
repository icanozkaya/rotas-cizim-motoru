# -*- coding: utf-8 -*-
"""Termosifon iptali: kullanıcının MTY sıhhi planında termosifona gelen soğuk/sıcak su uç parçaları (silinecek tutamaçlar)
ve sıcak su ağının yeni başı (merkezi sıcak su bağlantı noktası). S çerçevesi, kat 2 ve 3."""
import math, pickle, os
from veri import *

_C = '/tmp/claude-0/vy/termo.pkl'


def tara():
    if os.path.exists(_C): return pickle.load(open(_C, 'rb'))
    import ezdxf
    d = ezdxf.readfile('/tmp/claude-0/vy/sih.dxf'); m = d.modelspace()
    pts = []
    for kat in (2, 3):
        for k in OFIS_S1:
            pts.append((kat, k, ofis_pt(k, 'isitici', kat)))
    segs = []
    for e in m.query('LINE LWPOLYLINE'):
        if e.dxf.layer not in ('MTY-SOGUKSU-BORU', 'MTY-SICAKSU-BORU'): continue
        q = [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]] if e.dxftype() == 'LINE' else [tuple(v[:2]) for v in e.get_points()]
        segs.append((e.dxf.handle, e.dxf.layer, q))
    from shapely.geometry import LineString, Point
    rm = set(); head = {}; trim = {}
    for kat, k, p in pts:
        for hd, lay, q in segs:
            for qq in (q, q[::-1]):
                if math.dist(qq[0], p) < 20:
                    rm.add(hd)
                    if lay == 'MTY-SICAKSU-BORU':
                        if len(qq) > 2: trim[hd] = (lay, qq[1:])
                        head[(kat, k)] = qq[1]
                    else:
                        # soğuk: termosifona giden parça, ağın geri kalanına bağlandığı ilk noktaya kadar tamamen silinir
                        others = [LineString(o) for h2, l2, o in segs if h2 != hd and l2 == lay and len(o) > 1]
                        cut = None
                        for i in range(1, len(qq)):
                            if any(o.distance(Point(qq[i])) < 2.0 for o in others):
                                cut = i; break
                        if cut is not None and cut < len(qq) - 1:
                            trim[hd] = (lay, qq[cut:])
                    break
        if (kat, k) not in head: head[(kat, k)] = p
    out = dict(rm=rm, head=head, trim=trim)
    pickle.dump(out, open(_C, 'wb'))
    return out


if __name__ == '__main__':
    T = tara()
    print(len(T['rm']), 'uç silinecek'); print(T['head'])
