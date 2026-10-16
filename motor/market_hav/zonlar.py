# -*- coding: utf-8 -*-
"""market_hav/zonlar.py — temiz mimarinin A-AREA mahal sınırlarından KS-1..KS-4 bölgelerinin alan/hacim/kabuk
ölçülerini çıkarır (Excel hesabının girdisi). Kotlar KES_TLER.dxf'ten: ±0.00, tavan (makas altı) +6.00,
dükkan/koridor üstü 1. kat-teras döşemesi +4.50."""
import json
import lzma
import os
import shutil

import ezdxf
from shapely.geometry import Point, Polygon, box

BURASI = os.path.dirname(os.path.abspath(__file__))
DEPO = os.path.abspath(os.path.join(BURASI, '..', '..'))
TEMIZ = os.path.join(DEPO, 'proje', 'market_havalandirma', 'girdi', 'temiz_mimari.dxf')
CIKTI = os.path.join(DEPO, 'proje', 'market_havalandirma', 'girdi', 'zonlar.json')

# KS hizmet bantları (plan x, cm) — kanal sistemlerinin ortaları
BANT = {'KS-1': (52612, 57100), 'KS-2': (57100, 61350), 'KS-3': (61350, 65900), 'KS-4': (65900, 70734)}
DUKKAN_KS = {'A-Z-05': 'KS-1', 'A-Z-06': 'KS-2', 'A-Z-09': 'KS-3', 'A-Z-11': 'KS-4'}   # kanal dalı giren işyerleri
H_MARKET, H_ALT = 6.00, 4.50


def oku():
    if not os.path.exists(TEMIZ):
        with lzma.open(TEMIZ + '.xz') as f, open(TEMIZ, 'wb') as g:
            shutil.copyfileobj(f, g)
    m = ezdxf.readfile(TEMIZ).modelspace()
    pol = [Polygon([tuple(q) for q in e.get_points('xy')]).buffer(0)
           for e in m.query('LWPOLYLINE[layer=="A-AREA"]') if len(e) >= 3]
    yaz = []

    def it(es):
        for e in es:
            if e.dxftype() == 'INSERT':
                yield from e.attribs
                try:
                    yield from it(e.virtual_entities())
                except Exception:
                    pass
            else:
                yield e
    for e in it(m):
        if e.dxftype() in ('TEXT', 'ATTRIB', 'MTEXT'):
            t = e.dxf.text if e.dxftype() != 'MTEXT' else e.plain_text()
            yaz.append((t.strip(), e.dxf.insert[0], e.dxf.insert[1]))
    return pol, yaz


def main():
    pol, yaz = oku()
    mahal = []
    for P in pol:
        ic = [t for t, x, y in yaz if P.contains(Point(x, y))]
        kod = next((t for t in ic if t.startswith('A-Z-') and '.' not in t[4:]), None)
        if kod:
            ad = ic[0] if not ic[0].startswith('A-Z') else ''
            mahal.append(dict(kod=kod, ad=ad, P=P, yazilar=ic))
    # pazar holü A-Z-13 (en büyük), koridor A-Z-02
    sonuc = []
    for m in mahal:
        if m['kod'] in ('A-Z-13', 'A-Z-02'):
            tip = 'MARKET' if m['kod'] == 'A-Z-13' else 'KORİDOR'
            ad = 'MARKET SATIŞ ALANI' if tip == 'MARKET' else 'KORİDOR'
            h = H_MARKET if tip == 'MARKET' else H_ALT
            for ks, (x0, x1) in BANT.items():
                p = m['P'].intersection(box(x0, -1e6, x1, 1e6))
                if p.area < 1e4:
                    continue
                b = p.bounds
                dis_duvar = 0.0
                if tip == 'MARKET':
                    dis_duvar += (b[2] - b[0])          # kuzey cephe
                    if ks == 'KS-4':
                        dis_duvar += (b[3] - b[1])      # doğu cephe
                sonuc.append(dict(ks=ks, kod=m['kod'], ad=ad, tip=tip, alan=round(p.area / 1e4, 1), h=h,
                                  cati=round(p.area / 1e4, 1), duvar_boy=round(dis_duvar / 100, 1), cam_boy=0.0))
        elif m['kod'] in DUKKAN_KS:
            p = m['P']
            b = p.bounds
            sonuc.append(dict(ks=DUKKAN_KS[m['kod']], kod=m['kod'], ad='İŞYERİ', tip='İŞYERİ',
                              alan=round(p.area / 1e4, 1), h=H_ALT, cati=round(p.area / 1e4, 1),
                              duvar_boy=round((b[2] - b[0]) / 100, 1), cam_boy=round((b[2] - b[0]) / 100, 1)))
    sonuc.sort(key=lambda d: (d['ks'], d['tip'] != 'MARKET', d['kod']))
    json.dump(sonuc, open(CIKTI, 'w'), ensure_ascii=False, indent=1)
    for s in sonuc:
        print(s)


if __name__ == '__main__':
    main()
