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

---

# PLAN + KESİT A-A + GÖRÜNÜŞ B (`plan_kesit.py`, 14.10.2026)

Kural: "tüm projelerde gerekli kesit ve görünüşler". Aynı JSON'a `plan` bloğu eklenir; tek DXF'te:
1. **KAZAN DAİRESİ PLANI 1/50** — EI 120 taramalı duvarlar (oda poligonu + `duvar` kalınlığı), duvar tipi kaskad
   kazanlar kazan duvarında (üst kenar), gaz / yoğuşma / dönüş / gidiş başlıkları (kazan önünden 12 / 24 / 40 / 100 cm),
   kazan bağlantıları köprülü, kazan pompası + vanası, hava ayırıcı, tortu ayırıcı, denge kabı, genleşme tankı
   (kilitlenebilir vana), sekonder gidiş/dönüş kollektörü, zon pompaları (asıl + yedek), boyler, nötralizasyon,
   yer süzgeci, baca + tavandaki baca kollektörü, gaz girişi (ana vana + selenoid DIŞARIDA, filtre/regülatör/manometre/
   kollektör vanası içeride), gaz alarm, alt/üst menfez (açıklık + ızgara + ölçü/kot etiketi), kapılar (dışa açılır,
   EI2 90-C; ΣQ > 350 kW veya A > 100 m² ise 2. kapı yoksa otomatik eklenir + uyarı), bakım alanı (≥1,00 m), ölçü
   zincirleri, A-A kesit ve B görünüş işaretleri, ±0,00 kotu.
2. **KESİT A-A** (1. kazan ekseninden): döşeme/tavan/duvar kesiti, kazan yan görünüşü, başlık kesitleri (daire) ve
   kotları, baca kollektörü kesiti, menfez açıklıkları (kesite izdüşürülmüş) ve kotları, düşey ölçüler, kazan önü serbest
   mesafe kontrolü.
3. **GÖRÜNÜŞ B (kazan duvarı)**: kazan ön görünüşleri, her kazanın gidişinde EV, HP, TM, M, pompa, çek valf, vana;
   dönüş vanası, gaz vanası + esnek bağlantı, yoğuşma; başlıklar köprülü; baca kollektörü (çift çizgi) + baca (tavandan
   çatıya), gaz alarm (tavanda, üst menfezden yüksek), kot kolonu.
4. **Lejant + kontrol kutusu** (menfez hesabı §5.4, kapı sayısı, bakım mesafesi, EI 120) + **cihaz listesi** + notlar.

**Numara senkronu:** `numara_haritasi()` prensip şemasını (`kazan_dairesi.ciz`) bellekte üretip numaraları rollerine
göre alır; cihaz listesi şemanınkiyle birebir aynıdır (K-, P-, V-, DK-, HA-, TA-, GT-, KL-, GF-, GR-, SV-, GA-, B-, BY-,
NU-, EV-, M-, TM-, HP-). Şema çıktısı bu çalışmayla değişmedi.

Menfez: ΣQ < 1000 kW `S_A = F·a·2,25·(ΣQ+70)` cm², ≥ 1000 kW `ΣQ/3600` m²; üst `S_Ü = max(180 cm²; oran·S_A)`
(`ust_menfez_orani`, varsayılan 0,6 — İGDAŞ >1000 kW oranı; <1000 kW için yerel dağıtım şirketiyle TEYİT). Ölçü 5 cm
modüllü, kenar oranı ≤ 1,5 (F = 1).

```
python3 plan_kesit.py ornekler/gungoren.json proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_PLAN_KESIT.dxf
python3 kontrol.py proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_PLAN_KESIT.dxf
```
`plan` alanları: `temsili` (true → "DENEME – temsili oda"), `oda` [[x,y]...] (cm, dik açılı), `duvar`, `doseme`,
`ic_yukseklik`, `kazan_olcu`{g,d,h,ara,alt_kot,baca_cap}, `baca` [x,y] (y kazan baca eksenine çekilir),
`kapilar` [{duvar: alt|ust|sol|sag, konum, genislik}], `menfez`{alt{duvar,konum,alt_kot}, ust{duvar,konum,tavandan}},
`menfez_F`, `menfez_a`, `ust_menfez_orani`, `kazan_baslangic` (ops.).

Sınırlar: kazan duvarı odanın üst (max y) kenarı olmalı (oda poligonu buna göre döndürülerek verilir); görünüş kısmi
(denge kabı / genleşme tankı planda); sistem doldurma ve kullanım suyu bağlantıları yalnız şemada; görünüşte kazan
araları 40 cm iken etiketler sık; ölçüler kendi bloklarıyla (AutoCAD DIMENSION değil).
