# -*- coding: utf-8 -*-
"""Adapeker mimari DXF'ini düzleştir: tüm blokları (iç içe) patlat, (katman, tip, geometri, ek) kayıtları pickle'a yaz.
Kayıt: ('L',lay,[p,q]) ('P',lay,pts,kapali) ('C',lay,c,r) ('A',lay,pts) ('T',lay,(x,y),metin,h,rot) ('H',lay,pts,desen)"""
import sys, pickle, math
import ezdxf
from ezdxf import path as ep
from ezdxf.disassemble import recursive_decompose

def duzlestir(yol, cik):
    doc = ezdxf.readfile(yol)
    msp = doc.modelspace()
    K = []
    def lay_of(e):
        return e.dxf.get('layer', '0')
    n = 0
    for e in recursive_decompose(msp):
        t = e.dxftype()
        lay = lay_of(e)
        try:
            if t == 'LINE':
                K.append(('L', lay, [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]]))
            elif t in ('LWPOLYLINE', 'POLYLINE', 'ARC', 'ELLIPSE', 'SPLINE'):
                pts = [(v.x, v.y) for v in ep.make_path(e).flattening(1.0)]
                kap = t in ('LWPOLYLINE', 'POLYLINE') and e.is_closed
                K.append(('A' if t in ('ARC', 'ELLIPSE') else 'P', lay, pts, kap))
            elif t == 'CIRCLE':
                K.append(('C', lay, tuple(e.dxf.center)[:2], e.dxf.radius))
            elif t == 'TEXT':
                K.append(('T', lay, tuple(e.dxf.insert)[:2], e.dxf.text, e.dxf.height, e.dxf.rotation))
            elif t == 'MTEXT':
                K.append(('T', lay, tuple(e.dxf.insert)[:2], e.plain_text(), e.dxf.char_height, e.dxf.get('rotation', 0)))
            elif t == 'HATCH':
                for p in ep.from_hatch(e):
                    K.append(('H', lay, [(v.x, v.y) for v in p.flattening(1.0)], e.dxf.pattern_name))
            elif t in ('ATTRIB',):
                K.append(('T', lay, tuple(e.dxf.insert)[:2], e.dxf.text, e.dxf.height, e.dxf.rotation))
        except Exception as ex:
            n += 1
    pickle.dump(K, open(cik, 'wb'))
    return K, n

if __name__ == '__main__':
    K, n = duzlestir(sys.argv[1], sys.argv[2])
    from collections import Counter
    print(len(K), 'hata', n)
    print(Counter(k[1] for k in K).most_common(50))
