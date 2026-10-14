# -*- coding: utf-8 -*-
"""R3 teslim denetimi (14.10.2026 (B) talimatı) — kazan_dairesi/kontrol.py ortak denetleyicisini kullanır:
MTY bloğu / katmanı 0, köprü (bulge) 0, boru-boru kesişmesi 0, etiket–sembol eşleşmesi %100 (kazan dairesi numaraları),
elektrik (SINYAL) katmanı 0. Temsili mimari (ROTAS-MIMARI-*) çakışma sayımına girmez.
Kullanım: python3 kontrol.py proje/denemeler/radyator/*_R3.dxf"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kazan_dairesi'))
import kontrol as KK        # noqa: E402


def denetle(yol):
    oz, sorun, ornek, hata = KK.denetle(yol)
    print(yol)
    print('  ÖZET:', oz)
    print('  diğer çakışma (bilgi):', dict(sorun) or 'yok')
    for x in hata[:10]:
        print('  ETİKET EŞLEŞMEDİ:', x)
    return oz


if __name__ == '__main__':
    for y in sys.argv[1:]:
        if os.path.basename(os.path.dirname(os.path.abspath(__file__))) == 'radyator' and y.endswith('.dxf'):
            denetle(y)
