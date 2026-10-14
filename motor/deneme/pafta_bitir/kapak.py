# -*- coding: utf-8 -*-
"""Kullanıcının kapak şablonundan (kutuphane/asansor/kapak_sablon.json) basit proje kapağı DXF'i üretir.

    kapak_uret(cikis.dxf, metin={eski: yeni}, konum={"x,y": yeni}, sablon=...)

Şablon geometrisi aynen çizilir; yazılar ya metin eşleşmesiyle ya da (yuvarlanmış) konum anahtarıyla değiştirilir.
Değer None ise yazı çizilmez. Katmanlar: ROTAS-KAPAK (çizgi), ROTAS-KAPAK-YAZI (yazı)."""
import json
import os

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

DEPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
SABLON = os.path.join(DEPO, 'kutuphane', 'asansor', 'kapak_sablon.json')
HIZA = {'TL': TA.TOP_LEFT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER, 'BL': TA.BOTTOM_LEFT}


def kapak_uret(cikis, metin=None, konum=None, sablon=SABLON, cizgi='ROTAS-KAPAK', yazi='ROTAS-KAPAK-YAZI'):
    d = json.load(open(sablon, encoding='utf-8'))
    metin, konum = metin or {}, konum or {}
    doc = ezdxf.new('R2018', setup=True)
    doc.header['$INSUNITS'] = 5
    if 'ROTAS' not in doc.styles:
        doc.styles.add('ROTAS', font='arial.ttf')
    doc.layers.add(cizgi, color=7)
    doc.layers.add(yazi, color=7)
    m = doc.modelspace()
    for r in d['kayitlar']:
        if r[0] == 'L':
            m.add_line(r[2], r[3], dxfattribs={'layer': cizgi})
        elif r[0] == 'P':
            m.add_lwpolyline(r[2], close=bool(r[3]), dxfattribs={'layer': cizgi})
        elif r[0] == 'C':
            m.add_circle(r[2], r[3], dxfattribs={'layer': cizgi})
        elif r[0] == 'T':
            anahtar = '%d,%d' % (round(r[2][0]), round(r[2][1]))
            s = konum.get(anahtar, metin.get(r[3], r[3]))
            if s is None or s == '':
                continue
            t = m.add_text(s, height=r[4], rotation=r[5], dxfattribs={'layer': yazi, 'style': 'ROTAS', 'width': 0.85})
            t.set_placement(r[2], align=HIZA.get(r[6], TA.BOTTOM_LEFT))
    doc.saveas(cikis)
    return d['gen'], d['yuk']
