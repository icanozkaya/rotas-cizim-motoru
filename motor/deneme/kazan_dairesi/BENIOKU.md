> **ONAYLI (14.10.2026):** Kullanıcı `plan_kesit.py` çıktısını (plan + kesit + kısmi görünüş) doğru kazan dairesi olarak onayladı; kazan dairesi gereken her yerde bu kullanılır. Bu dosyada bundan sonra geçen "teslimde kullanılmaz / arşiv" ifadeleri İPTALDİR.

# kazan_dairesi — parametrik KAZAN DAİRESİ PRENSİP ŞEMASI — R2 (14.10.2026 (B) talimatı)

> **`plan_kesit.py` TESLİMDE KULLANILMAZ.** Merkezi sistem kesiti ve kazan dairesi yerleşimi için yalnız kullanıcının
> daha önce gönderdiği / onayladığı kesit ve yerleşim planı kullanılır. `plan_kesit.py` arşivdir; içe aktarılırsa hata
> verir (yalnız `ROTAS_PLAN_KESIT_ARSIV=1` ile elle çalışır). Radyatör modülü dahil hiçbir modül onu çağırmaz.

## R2 kuralları (kazan_dairesi.py)
- **MTY bloğu yok.** Tüm semboller saf geometri `ROTAS-` blokları: `bloklar_r2.py` (küresel / kelebek vana, çek valf,
  pislik tutucu, otomatik dolum, kilitli vana, esnek bağlantı, emniyet ventili, manometre, termometre, O.H.A.C, denge kabı,
  hava ayırıcı, tortu ayırıcı, genleşme tankı, baca şapkası, kollektör) + `bloklar.kendi_bloklar` (kazan, pompa, selenoid,
  regülatör, gaz alarm, boyler, nötralizasyon, ok). `motor/deneme/semboller2/` bu tarihte depoya işlenmemiş (yarım)
  olduğundan kullanılmadı; hazır olunca `bloklar_r2.TANIM` onunla değiştirilebilir.
- **Boru atlatma / köprü yok.** Ana hidrolik şemada yalnız iki toplayıcı vardır: kazan gidişleri üstte, dönüşleri altta.
  Kaskadda kaçınılmaz görünen kesişmeler (baca, doğalgaz, yoğuşma) **ayrı bölgede** çizilir: kazanın altında GAZ ve
  YOĞ., üstünde BACA bağlantı uçları (oklu kısa hat) bulunur; hatların kendisi alttaki **DOĞALGAZ BAĞLANTI ŞEMASI**
  (giriş → ana vana → selenoid → filtre → [regülatör] → manometre → kollektör vanası → kazan başına vana + esnek bağlantı,
  "K-01 KAZANINA"), **YOĞUŞMA DRENAJ ŞEMASI** (K-01..K-n → [nötralizasyon] → pis su) ve **BACA BAĞLANTI ŞEMASI**
  (K-01..K-n → baca kollektörü → baca + şapka) bölgelerindedir. `Sema.kesisim_denetle()` her çalışmada boru-boru iç
  kesişmesini sayar (0 olmalı).
- **Numara–sembol eşleşmesi:** her numara bir kez yazılır ve kendi sembolünün sınır kutusuna en çok 18 cm uzakta, başka
  hiçbir sembol kendi sembolünden 4 cm daha yakın olmayacak yere konur (bulunamazsa 28 cm / 2,5 cm). Numara DXF'te
  sembol INSERT'ine XDATA olarak (`ROTAS`, `NO=V-01`) yazılır; `kontrol.py` bağımsız olarak "etiketin en yakın sembolü
  kendi sembolü mü" testini yapar.
- **Elektrik kalemi yok:** gaz alarmı – selenoid sinyal hattı çizilmez (cihazlar kalır, notta "elektrik projesinde").
- Gömülü kullanım: `ciz(P, cikti, gomulu=True)` başlık / liste / notları çizmez, zon gidişini şemanın üstüne, zon dönüşünü
  altına uzatır (`S.baglanti`), cihaz listesi `S.satir`, notlar `S.notlar` (radyatör kolon şeması bunu kullanır).

## Çalıştırma
```
python3 kazan_dairesi.py ornekler/gungoren.json ../../../proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_SEMA_R2.dxf
python3 kontrol.py <cikti.dxf>   # ÖZET: MTY 0, köprü 0, kesişme 0, etiket %100, elektrik 0 + çakışma dökümü
python3 onizleme.py <cikti.dxf> <png> [x0,y0,x1,y1 dpi genişlik]   # yalnız kontrol için, depoya konmaz
```
Son çıktılar: `GUNGOREN_KAZAN_DAIRESI_SEMA_R2.dxf` (5×110 kW, etiket 102/102), `KUCUK_2x110_KAZAN_DAIRESI_SEMA_R2.dxf`
(2×110 kW + boyler + nötralizasyon, etiket 84/84); ikisinde de MTY 0, köprü 0, kesişme 0, çakışma yok.

JSON alanları (bkz. `ornekler/`): proje, deneme, rejim{gidis,donus}, kazan{adet,kapasite_kw,tip,pompa{ad,debi,basma}},
denge_kabi{cap}, genlesme{hacim_l,on_basinc,maks_bar}, emniyet{ventil_bar,ventil_cap},
zonlar[{ad,aciklama,debi,basma,yedek,adet}], boyler{hacim_l,tip,cap,ev_bar,sarj_pompa{debi,basma}}|null,
sirkulasyon{debi,basma,cap}|null, notralizasyon bool, baca{cap,tip},
dogalgaz{vana,filtre,selenoid,alarm,regulator{giris,cikis}|null, kazan_cap,kollektor_cap,giris_cap}, doldurma, notlar[].
(`plan` bloğu yalnız arşivdeki plan_kesit.py içindir; şema onu kullanmaz.)

## Sınırlar / sorulacaklar
- Baca, gaz ve yoğuşma ayrı bölgede (kazan numarasıyla eşlenmiş) gösterildi; kullanıcı bunları ana şemada görmek isterse
  kesişmesiz çizim mümkün değildir (kaskadda her kazanın 5 bağlantısı vardır, yalnız 2'si toplayıcıyla kesişmesiz kalır).
- Gaz alarm cihazı (dedektör) çizildi, kablosu çizilmedi — tamamen kaldırılması istenirse `dogalgaz.alarm=false`.
- Yerden ısıtma karışım (3 yollu) vanalı zon, eşanjör, akümülasyon tankı, yumuşatma yok; kazan bloğu duvar tipi.
- Hesap (genleşme hacmi, denge kabı çapı, baca) yapılmaz; değerler JSON'dan gelir.
- R1 çıktıları (`*_SEMA.dxf`, `*_PLAN_KESIT.dxf`) depoda duruyor; **teslimde R2 şema kullanılır, PLAN_KESIT kullanılmaz.**

---

# (ARŞİV — TESLİMDE KULLANILMAZ) PLAN + KESİT A-A + GÖRÜNÜŞ B (`plan_kesit.py`, 14.10.2026)

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
