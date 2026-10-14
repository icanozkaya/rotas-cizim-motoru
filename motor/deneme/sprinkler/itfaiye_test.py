# -*- coding: utf-8 -*-
"""İtfaiye bağlantısı yön testi (R2, 14.10.2026 B): çek valf akışı DIŞARIDAN (storz) TESİSATA doğru olmalı.

DXF dosyası yeniden okunur. Katmanı `katman_on` ile başlayan INSERT'ler incelenir:
- ROTAS-SMB-CEKVALF : blok +X yönü akış yönüdür (rotation + xscale işareti). Akış vektörü tesisat bağlantı noktasına
  (hedef) doğru, storz ağızlarından uzağa bakmalı:  d·(hedef - c) > 0  ve  d·(storz_ort - c) < 0.
- ROTAS-SMB-AKIS-OKU: aynı koşul (oklar tesisata doğru).
- ROTAS-SMB-STORZ   : rakor dışarı bakar (hedeften uzağa): d·(s - hedef) > 0.
En az bir çek valf ve en az bir storz bulunmalı; aksi halde hata.

Kullanım: python3 itfaiye_test.py <dxf> <hedef_x> <hedef_y> [katman_on]
"""
import math
import sys
import ezdxf

CV, OK, ST = 'ROTAS-SMB-CEKVALF', 'ROTAS-SMB-AKIS-OKU', 'ROTAS-SMB-STORZ'


def _yon(e):
    a = math.radians(e.dxf.rotation)
    sx = 1.0 if e.dxf.get('xscale', 1.0) >= 0 else -1.0
    return (math.cos(a) * sx, math.sin(a) * sx)


def _icinde(e, katman_on):
    if e.dxf.layer.startswith(katman_on):
        return True
    return False


def kontrol(dosya, hedef, katman_on='ROTAS-YANGIN-ITFAIYE', msp=None):
    if msp is None:
        msp = ezdxf.readfile(dosya).modelspace()
    ins = [e for e in msp.query('INSERT') if _icinde(e, katman_on)]
    cv = [e for e in ins if e.dxf.name == CV]
    ok = [e for e in ins if e.dxf.name == OK]
    st = [e for e in ins if e.dxf.name == ST]
    hata = []
    if not cv:
        hata.append('itfaiye hattında çek valf yok')
    if not st:
        hata.append('itfaiye bağlantı ağzı (storz) yok')
    if st:
        so = (sum(e.dxf.insert.x for e in st) / len(st), sum(e.dxf.insert.y for e in st) / len(st))
    else:
        so = None
    sonuc = []
    for tur, liste in (('çek valf', cv), ('akış oku', ok)):
        for e in liste:
            c = (e.dxf.insert.x, e.dxf.insert.y)
            d = _yon(e)
            h = (hedef[0] - c[0], hedef[1] - c[1])
            iyi = d[0] * h[0] + d[1] * h[1] > 0
            if so is not None:
                s = (so[0] - c[0], so[1] - c[1])
                iyi = iyi and (d[0] * s[0] + d[1] * s[1] < 0)
            sonuc.append((tur, round(c[0]), round(c[1]), 'tesisata doğru' if iyi else 'TERS'))
            if not iyi:
                hata.append(f'{tur} @({c[0]:.0f},{c[1]:.0f}) akış yönü ters (tesisata doğru olmalı)')
    for e in st:
        c = (e.dxf.insert.x, e.dxf.insert.y)
        d = _yon(e)
        if d[0] * (c[0] - hedef[0]) + d[1] * (c[1] - hedef[1]) <= 0:
            hata.append(f'storz @({c[0]:.0f},{c[1]:.0f}) içe bakıyor (dışarı bakmalı)')
    return dict(cekvalf=len(cv), ok=len(ok), storz=len(st), yonler=sonuc, hata=hata)


def _oz_test():
    """sembol yön sözleşmesinin kendi testi: doğru ve ters yerleştirilmiş çek valf ayırt edilmeli"""
    import rotas_sembol as RS
    d = ezdxf.new('R2018')
    m = d.modelspace()
    RS.ciz(m, 'storz', 100, 0, aci=0, katman='ROTAS-YANGIN-ITFAIYE-SEMBOL')
    RS.ciz(m, 'cekvalf', 50, 0, aci=180, katman='ROTAS-YANGIN-ITFAIYE-SEMBOL')     # storz (x=100) -> hedef (x=0)
    assert not kontrol(None, (0, 0), msp=m)['hata'], 'doğru yön hata verdi'
    RS.ciz(m, 'cekvalf', 30, 0, aci=0, katman='ROTAS-YANGIN-ITFAIYE-SEMBOL')       # ters
    r = kontrol(None, (0, 0), msp=m)
    assert len(r['hata']) == 1 and 'ters' in r['hata'][0], r
    return True


if __name__ == '__main__':
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    if len(sys.argv) == 1:
        print('öz test:', _oz_test())
    else:
        r = kontrol(sys.argv[1], (float(sys.argv[2]), float(sys.argv[3])), *(sys.argv[4:5]))
        print(r)
        sys.exit(1 if r['hata'] else 0)
