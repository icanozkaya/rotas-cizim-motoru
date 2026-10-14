# kazan_dairesi — parametrik KAZAN DAİRESİ PRENSİP ŞEMASI (deneme)

## Ne yapar
JSON girdiden ölçeksiz kazan dairesi prensip şeması + cihaz listesi + notlar üretir (yalnız DXF, R2018/AC1032, birim cm).
Akış: kaskad kazanlar (her kazanda emniyet ventili, termometre, manometre, otomatik purjör, kazan pompası, çek valf, vana)
→ kazan gidiş kollektörü → hava ayırıcı → denge kabı → gidiş kollektörü → zon pompaları (asıl + yedek paralel bacak:
vana-pompa-çek valf-vana, ortak pislik tutucu) → zon; dönüşler kesikli (DASHED) → dönüş kollektörü → denge kabı → tortu
ayırıcı → kazan dönüş kollektörü. Kazan altı: yoğuşma (opsiyonel nötralizasyon), doğalgaz hattı (ana kesme vanası,
selenoid + gaz/CO alarm, filtre, opsiyonel regülatör, manometre, kollektör vanası, kazan başına vana + esnek bağlantı),
dönüş. Kapalı genleşme tankı dönüşe kilitlenebilir vanayla; sistem doldurma (vana, pislik tutucu, otomatik dolum, çek
valf). Ortak baca kollektörü + baca. Opsiyonel boyler (şarj pompası, soğuk su + emniyet ventili, sıcak su, sirkülasyon).

- Semboller: kullanıcının MTY blokları gerçek blok olarak (patlatılmadan, iç katmanlarıyla) — küresel/kelebek vana,
  çek valf, pislik tutucu, emniyet ventili, manometre, termometre, O.H.A.C, otomatik dolum, kilitlenebilir vana, esnek
  bağlantı, denge kabı, hava ayırıcı, tortu ayırıcı, genleşme tankı. MTY'de olmayanlar 03_SEMBOLLER geometrisiyle blok:
  ROTAS-KAZAN-DUVAR, ROTAS-POMPA (MTY pompa çiziminden), ROTAS-BOYLER, ROTAS-SELENOID, ROTAS-REGULATOR,
  ROTAS-GAZ-ALARM, ROTAS-NOTRALIZASYON, ROTAS-OK. MTY 'CAP' özniteliği DN değeriyle doldurulur (gizli; MTY'de güncellenebilir).
- DN65 ve üzeri vanalar kelebek, altı küresel (Aselsan notu). Çaplar: su v ≤ 1,0 m/s (≤DN50) / 1,5 m/s; gaz
  Hu=9,59 kWh/m³, η=0,97, v ≤ 5-6 m/s (300 mbar regülatör öncesi 15 m/s) — ön boyut.
- Numaralandırma: K, P, DK, HA, TA, GT, KL, BY, NU, B, EV, HP, M, TM, V, GF, GR, SV, GA; aynı tip+özellik ardışık
  numaralı ve listede tek satır (NO | CİHAZ | TEKNİK ÖZELLİKLERİ, yangın pompa cihaz listesi tarzı).
- Etiketler (V-01, DN..) boş yere otomatik yerleşir; yazı altına ROTAS-MASKE katmanında wipeout.
- Kesişmeler köprülü (boru tek LWPOLYLINE, bulge yarım daire). Katmanlar ROTAS- önekli (MTY blok iç katmanları hariç).

## Çalıştırma
```
python3 kazan_dairesi.py ornekler/gungoren.json proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_SEMA.dxf
python3 kontrol.py <cikti.dxf>        # üst üste çizgi, köprüsüz kesişim, boru-sembol, yazı-çizgi, yazı-yazı
python3 onizleme.py <cikti.dxf> <png> [x0,y0,x1,y1 dpi genişlik]   # yalnız kontrol için, depoya konmaz
```
JSON alanları (bkz. `ornekler/`): proje, deneme, rejim{gidis,donus}, kazan{adet,kapasite_kw,tip,pompa{ad,debi,basma}},
denge_kabi{cap}, genlesme{hacim_l,on_basinc,maks_bar}, emniyet{ventil_bar,ventil_cap},
zonlar[{ad,aciklama,debi,basma,yedek,adet}], boyler{hacim_l,tip,cap,ev_bar,sarj_pompa{debi,basma}}|null,
sirkulasyon{debi,basma,cap}|null, notralizasyon bool, baca{cap,tip},
dogalgaz{vana,filtre,selenoid,alarm,regulator{giris,cikis}|null, kazan_cap,kollektor_cap,giris_cap}, doldurma, notlar[].

## Sınırlar
- Yerden ısıtma karışım (3 yollu) vanalı zon, eşanjör, akümülasyon tankı, yumuşatma yok.
- Kazan bloğu duvar tipi; döküm/yer tipi kazan (MTY 'aKAZAN ŞEMA.') seçeneği eklenmedi.
- Baca kollektörü kazan gidiş kollektörünü, gaz/dönüş dişleri yoğuşma ve gaz kollektörlerini köprüyle keser
  (tek sıra kaskadda kaçınılmaz).
- Hesap (genleşme hacmi, denge kabı çapı, baca) yapılmaz; değerler JSON'dan gelir.
