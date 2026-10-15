# -*- coding: utf-8 -*-
"""ONAYLI kazan dairesi paftası (plan_kesit.onayli_kazan_dairesi) + boyler kullanım suyu 3 borulu bağlantısı
(soğuk su girişi / sıcak su çıkışı / sirkülasyon dönüşü) planda; uçlar kazan dairesi dışına AÇIK bırakılır.
Numaralar prensip şeması sırasından (cihaz listesiyle aynı): TM-11 sıcak su; V-22, V-49, V-08, EV-05 soğuk su;
V-23, P-08, V-09, V-24 sirkülasyon. Zon (IP-2) gidiş/dönüş uçları da açık (kullanıcının projesinde birleştirilecek).

Kullanım: python3 boyler_3boru.py girdi.json cikti.dxf [oda_genisligi_cm]
"""
import json
import sys

import ezdxf
from ezdxf import bbox
from ezdxf.enums import TextEntityAlignment as TA

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import plan_kesit as PK  # noqa: E402

SOG, SIC, SIR = 'ROTAS-SIHHI-SOGUK-SU', 'ROTAS-SIHHI-SICAK-SU', 'ROTAS-SIHHI-SIRKULASYON'
RENK = {SOG: (5, 'Continuous'), SIC: (1, 'Continuous'), SIR: (31, 'DASHDOT')}
VANA, POMPA, ETK, YAZ = 'ROTAS-ISITMA-VANA', 'ROTAS-ISITMA-POMPA', 'ROTAS-ISITMA-ETIKET', 'ROTAS-ISITMA-YAZI'


def main(girdi, cikti, genislik=None):
    P = json.load(open(girdi, encoding='utf-8'))
    if genislik:
        P['plan'] = PK.varsayilan_plan(P, genislik=float(genislik))
        P['plan']['temsili'] = bool(P.get('deneme', False))   # teslim paftasında DENEME başlığı yok
    doc = ezdxf.new('R2018', setup=True)
    doc.header['$INSUNITS'] = 5
    k = PK.onayli_kazan_dairesi(doc, P, 0, 0)
    msp = doc.modelspace()
    for ad, (c, lt) in RENK.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=c, linetype=lt)
    boy = P['boyler']
    dn_b = boy.get('cap', 'DN40')
    dn_r = (P.get('sirkulasyon') or {}).get('cap', 'DN25')
    # --- planda boyler (en büyük ölçekli BOYLER-PLAN; lejanttakiler küçük ölçekli)
    by = max((e for e in msp.query('INSERT') if e.dxf.name.startswith('ROTAS-KD-BOYLER-PLAN')), key=lambda e: e.dxf.xscale)
    b = bbox.extents([by])
    cx = (b.extmin.x + b.extmax.x) / 2
    r = (b.extmax.x - b.extmin.x) / 2
    cy = b.extmax.y - r - 3                     # gövde dairesi (alt ayaklar hariç)
    # --- alt (güney) duvar iç/dış yüzü: boylerin altındaki yatay duvar parçaları
    xs = [cx + 80, cx + 125, cx + 170]
    ys = []
    for e in msp.query('LWPOLYLINE'):
        if not e.dxf.layer.startswith('ROTAS-MIMARI-DUVAR'):
            continue
        p = list(e.get_points('xy'))
        for (x1, y1), (x2, y2) in zip(p, p[1:] + p[:1]):
            if abs(y1 - y2) < 0.1 and y1 < cy - 50 and min(x1, x2) <= xs[-1] + 20 and max(x1, x2) >= xs[0] - 20:
                ys.append(y1)
    ys = sorted(set(round(v, 1) for v in ys), reverse=True)
    yb, yo = ys[0], ys[1]                       # iç yüz, dış yüz
    y_uc = yo - 45                              # açık uç

    def hat(lay, pts):
        msp.add_lwpolyline(pts, dxfattribs={'layer': lay})

    def blok(ad, x, y, rot, lay, cap=None, olcek=1.0):
        e = msp.add_blockref(ad, (x, y), dxfattribs={'layer': lay, 'rotation': rot, 'xscale': olcek, 'yscale': olcek})
        if cap:
            e.add_auto_attribs({'CAP': cap})
            for a in e.attribs:
                a.dxf.invisible = 1
        return e

    def etiket(s, x, y, al=TA.MIDDLE_LEFT, h=9.0):
        t = msp.add_text(s, height=h, dxfattribs={'layer': ETK, 'style': 'ROTAS', 'width': 0.85})
        t.set_placement((x, y), align=al)

    # dairenin sağ-alt çeyreğinden çıkış kotları (üstten alta: sıcak, sirkülasyon, soğuk) → kesişmesiz dönüş
    import math
    dy = {SIC: -14.0, SIR: -27.0, SOG: -40.0}
    xt = {SOG: xs[0], SIR: xs[1], SIC: xs[2]}
    for lay in (SIC, SIR, SOG):
        y = cy + dy[lay]
        x0 = cx + math.sqrt(max(r * r - dy[lay] ** 2, 0.0))
        hat(lay, [(x0, y), (xt[lay], y), (xt[lay], y_uc)])
    # soğuk su (akış yukarı): V-22 küresel vana, V-49 pislik tutucu, V-08 çek valf, EV-05 emniyet ventili
    x = xt[SOG]
    blok('ROTAS-KD-KURESEL-VANA', x, yb + 28, 90, VANA, dn_b); etiket('V-22', x + 12, yb + 30, h=8.5)
    blok('ROTAS-KD-PISLIK-TUTUCU', x, yb + 56, 90, VANA, dn_b); etiket('V-49', x + 12, yb + 56, h=8.5)
    blok('ROTAS-KD-CEKVALF', x, yb + 86, 90, VANA, dn_b); etiket('V-08', x + 9, yb + 86, h=8.5)
    ev = blok('ROTAS-KD-EMNIYET-VENTILI', x, yb + 124, -90, VANA, 'DN20', 0.8)
    etiket('EV-05', x + 4, yb + 141, h=8.5)
    # sirkülasyon dönüşü (akış yukarı, boylere): V-23, P-08, V-09, V-24
    x = xt[SIR]
    blok('ROTAS-KD-KURESEL-VANA', x, yb + 32, 90, VANA, dn_r); etiket('V-23', x + 12, yb + 34)
    blok('ROTAS-POMPA', x, yb + 80, 90, POMPA); etiket('P-08', x + 15, yb + 80)
    blok('ROTAS-KD-CEKVALF', x, yb + 112, 90, VANA, dn_r); etiket('V-09', x + 12, yb + 112)
    blok('ROTAS-KD-KURESEL-VANA', x, yb + 142, 90, VANA, dn_r); etiket('V-24', x + 12, yb + 144)
    # sıcak su çıkışı (akış aşağı): TM-11
    x = xt[SIC]
    blok('ROTAS-KD-TERMOMETRE', x, yb + 70, -90, VANA)
    etiket('TM-11', x + 30, yb + 72)
    # akış okları ve açık uç yazıları (kazan dairesi dışında, düşey)
    for lay, yon, s in ((SOG, 90, f'ŞEBEKEDEN SOĞUK SU {dn_b} - UÇ AÇIK, PROJEDE BAĞLANACAK'),
                        (SIR, 90, f'SİRKÜLASYON DÖNÜŞÜ {dn_r} - UÇ AÇIK, PROJEDE BAĞLANACAK'),
                        (SIC, -90, f'KULLANIM SICAK SUYU {dn_b} - UÇ AÇIK, PROJEDE BAĞLANACAK')):
        x = xt[lay]
        msp.add_blockref('ROTAS-OK', (x, y_uc + (14 if yon == 90 else 0)), dxfattribs={'layer': lay, 'rotation': yon})
        t = msp.add_text(s, height=8, rotation=90, dxfattribs={'layer': YAZ, 'style': 'ROTAS', 'width': 0.85})
        t.set_placement((x, y_uc - 8), align=TA.MIDDLE_RIGHT)
    # metin güncellemeleri
    for t in msp.query('TEXT'):
        if t.dxf.text == 'BAĞLANTILARI ŞEMAYA GÖRE':
            t.dxf.text = '3 BORULU: S.SU / SİRK. / SOĞUK SU'
        elif t.dxf.text == '(TAVANDAN ZONA)':
            t.dxf.text = '(UÇ AÇIK - PROJEDE BAĞLANACAK)'
        elif t.dxf.text.startswith('IP-2 DÖNÜŞ'):
            t.dxf.text = t.dxf.text + ' - UÇ AÇIK'
    doc.saveas(cikti)
    return k, (cx, cy, r, yb, yo, xt)


if __name__ == '__main__':
    print(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)[1])
