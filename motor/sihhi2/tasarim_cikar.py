#!/usr/bin/env python3
"""sihhi2 — KULLANICININ TASARIM SEÇİMLERİ (new_block.dxf, kullanıcının kendi MTY çizimi) -> tasarim_new_block.json

    python3 motor/sihhi2/tasarim_cikar.py

Kullanıcı kuralı: tasarım seçimleri (kolon sayısı/yeri, rögar ataması, ÇM/BM yeri) kafaya göre değiştirilmez.
Bu betik yalnız kullanıcının KARARLARINI okur (güzergâh/etiket değil):
  - pis su kolonları P1..P9 (dinamik kolon bloğu, öznitelik K) — zemin çerçevesinde; katlarda aynı eksen
  - çatı planındaki P / YB konumları (çatı paftası kendi çerçevesinde, mutlak x)
  - ÇM / BM bağlantı blokları (blok içi yazı C.M. / B.M.) — kat bazında
  - rögar ataması (temel planı / rögar şeması: R1<-P7,P9; R2<-P8; R3<-P2,P3,P5,P6; R4<-P1,P4) ve temel rögar konumları
"""
import json
import os

import ezdxf
from ezdxf import bbox

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KAYNAK = '/tmp/claude-0/uu/new_block.dxf'
CIKIS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasarim_new_block.json')
PAFTA = {'T': (250042, 252513, -2629), 'Z': (252513, 254578, 0), '1': (254578, 256617, 2034),
         '2': (256617, 258656, 4082), 'C': (258656, 260714, 0)}


def main():
    if not os.path.exists(KAYNAK):
        import lzma
        os.makedirs(os.path.dirname(KAYNAK), exist_ok=True)
        with lzma.open(KOK + '/ornekler/new_block.dxf.xz') as f, open(KAYNAK, 'wb') as g:
            g.write(f.read())
    doc = ezdxf.readfile(KAYNAK)
    msp = doc.modelspace()
    kolon = {}
    cati = {}
    makine = {'Z': [], '1': [], '2': []}
    for e in msp.query('INSERT'):
        x, y = e.dxf.insert[0], e.dxf.insert[1]
        if not -444050 < y < -441150:
            continue
        k = next((k for k, (a, b, o) in PAFTA.items() if a < x < b), None)
        if k is None:
            continue
        at = {a.dxf.tag: a.dxf.text for a in e.attribs}
        if 'K' in at:
            if k == 'Z' and at['K'].startswith('P'):
                kolon[at['K']] = [round(x, 1), round(y, 1)]
            if k == 'C':
                cati[at['K']] = [round(x, 1), round(y, 1)]
            continue
        if k not in makine:
            continue
        ts = [q.dxf.text for q in doc.blocks[e.dxf.name] if q.dxftype() == 'TEXT']
        if ts and ts[0].strip() in ('C.M.', 'B.M.'):
            b = bbox.extents([e])
            o = PAFTA[k][2]
            makine[k].append(dict(tip='CM' if ts[0].startswith('C') else 'BM', x=round(x - o, 1), y=round(y, 1),
                                  kutu=[round(b.extmin.x - o, 1), round(b.extmin.y, 1), round(b.extmax.x - o, 1),
                                        round(b.extmax.y, 1)]))
    rogar = {'R1': ['P7', 'P9'], 'R2': ['P8'], 'R3': ['P2', 'P3', 'P5', 'P6'], 'R4': ['P1', 'P4']}
    # temel planı rögarları (SIHHI_ALTIN_REFERANS §6; temel çerçevesi -2629 -> zemin çerçevesi)
    rogar_xy = {'R1': [254519.9, -441847.9], 'R2': [254519.9, -442334.6], 'R3': [254519.9, -442841.4],
                'R4': [254519.9, -443366.5], 'PB': [255025.8, -443366.5]}
    out = dict(kaynak='ornekler/new_block.dxf (kullanıcı çizimi, MTY katmanları)',
               kolonlar={k: kolon[k] for k in sorted(kolon, key=lambda s: int(s[1:]))},
               balon_ofset={'P1': [26, -53], 'P2': [-94, 16], 'P3': [-75, 9], 'P4': [-26, -76], 'P5': [96, -13],
                            'P6': [75, -13], 'P7': [48, -11], 'P8': [-11, -48], 'P9': [49, 88]},
               cati=cati, makineler=makine, rogar_atama=rogar, rogar_konum=rogar_xy,
               cati_fan=[[253237, -442726], [253740, -442712], [253048, -442263]])
    with open(CIKIS, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(CIKIS, len(kolon), 'kolon', sum(len(v) for v in makine.values()), 'makine')


if __name__ == '__main__':
    main()
