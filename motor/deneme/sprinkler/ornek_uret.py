# -*- coding: utf-8 -*-
"""Deneme girdileri (yapay mimari): ornek_girdi/kat_ofis_oh1.json, ornek_girdi/otopark_oh2.json"""
import json, os

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ornek_girdi')
os.makedirs(D, exist_ok=True)


def kol(cx, cy, a):
    return [cx - a / 2, cy - a / 2, cx + a / 2, cy + a / 2]


# ---------------------------------------------------------------- 1) 30x20 m ofis katı (OH1)
dis = [0, 0, 3000, 2000]
W = 25.0          # dış duvar
w = 20.0          # iç duvar
y_of1 = 1125.0
y_ko0, y_ko1 = y_of1 + w, y_of1 + w + 200.0          # koridor 2,00 m
y_od0 = y_ko1 + w
oda_w = (3000 - 2 * W - 3 * w) / 4
mahaller = [
    dict(ad='AÇIK OFİS', sinif='OH1', rect=[W, W, 3000 - W, y_of1], kapi=dict(p=[1300.0, y_of1 + w / 2], w=100.0)),
    dict(ad='KORİDOR', sinif='OH1', rect=[W, y_ko0, 3000 - W, y_ko1], dagitim=True),
]
for i in range(4):
    x0 = W + i * (oda_w + w)
    mahaller.append(dict(ad=f'ODA-{i + 1}', sinif='OH1', rect=[x0, y_od0, x0 + oda_w, 2000 - W],
                         kapi=dict(p=[x0 + 120.0, y_ko1 + w / 2], w=90.0)))
kolonlar = []
for x in (25.0, 1000.0, 2000.0, 2975.0):
    for y in (25.0, 575.0, y_of1 + w / 2, y_ko1 + w / 2, 1975.0):
        kolonlar.append(kol(x, y, 50.0))
ofis = dict(proje='DENEME — YAPAY OFİS KATI', kat_adi='1. KAT', deneme=True, tavan='asma',
            dis_hat=dis, mahaller=mahaller, kolonlar=kolonlar,
            kolon_hatti=dict(ad='SP-1', kose='sol-alt'),
            hidrolik=dict(C=120.0, statik_m=7.5, besleme_L_m=30.0, besleme_dn=100, vana_kaybi_bar=0.35,
                          ek_debi_lpm=0.0))
json.dump(ofis, open(os.path.join(D, 'kat_ofis_oh1.json'), 'w'), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 2) 40x25 m otopark (OH2)
W2 = 30.0
mahaller = [dict(ad='KAPALI OTOPARK', sinif='OH2', rect=[W2, W2, 4000 - W2, 2500 - W2], dagitim=True)]
kolonlar = []
xs = [30.0, 800.0, 1600.0, 2400.0, 3200.0, 3970.0]
ys = [30.0, 833.0, 1667.0, 2470.0]
for x in xs:
    for y in ys:
        kolonlar.append(kol(x, y, 60.0))
otopark = dict(proje='DENEME — YAPAY KAPALI OTOPARK', kat_adi='-1. BODRUM KAT', deneme=True, tavan='yok',
               dis_hat=[0, 0, 4000, 2500], mahaller=mahaller, kolonlar=kolonlar,
               kolon_hatti=dict(ad='SP-1', kose='sol-alt'),
               hidrolik=dict(C=120.0, statik_m=3.5, besleme_L_m=20.0, besleme_dn=150, vana_kaybi_bar=0.35,
                             ek_debi_lpm=0.0))
json.dump(otopark, open(os.path.join(D, 'otopark_oh2.json'), 'w'), ensure_ascii=False, indent=1)
print('girdiler yazıldı:', D)
