# -*- coding: utf-8 -*-
"""motor/deneme/pompa_grubu yangın pompa grubu kesitinin cihaz numaralarını okur (kolon şeması ile senkron numara).
Ayrı süreçte çalışır (pompa_grubu/semboller.py ile sprinkler/semboller.py ad çakışmasın diye):
    python3 dolap_pompa_no.py <pompa_girdi.json> <gecici_cikti.dxf>   ->  stdout JSON [[no, ad, adet, [özellik]], ...]
pompa_grubu modülüne dokunulmaz; yalnız Cizim.tablo çağrısı yakalanır."""
import json
import os
import sys

DEPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
PG = os.path.join(DEPO, 'motor', 'deneme', 'pompa_grubu')


def oku(girdi, gecici):
    sys.path.insert(0, PG)
    import yangin                                   # noqa: E402  pompa_grubu/yangin.py
    yakalanan = []
    asil = yangin.Cizim.tablo

    def tablo(self, x, y, baslik, liste, *a, **kw):
        if 'CİHAZ LİSTESİ' in baslik:
            yakalanan.extend(liste)
        return asil(self, x, y, baslik, liste, *a, **kw)
    yangin.Cizim.tablo = tablo
    g = json.load(open(girdi, encoding='utf-8'))
    yangin.ciz(g, gecici)
    return [[str(r[0]), str(r[1]), r[2], [str(x) for x in r[3]]] for r in yakalanan]


if __name__ == '__main__':
    print(json.dumps(oku(sys.argv[1], sys.argv[2]), ensure_ascii=False))
