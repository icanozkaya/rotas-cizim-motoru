# 03 — Mekanik Tesisat Çizim Sembolleri (geometrik tarif kataloğu)

Hazırlanma: 2026-10-14 · Kapsam: sıhhi, kalorifer/ısıtma-soğutma, yangın, doğalgaz, havalandırma
Amaç: Her sembolü bir programcının **ezdxf** ile doğrudan çizebileceği netlikte tarif etmek.

## 0. Kaynak durumu ve güvenilirlik (önce okuyun)

- TS EN 806-1, DIN 1988, DIN 2429, ISO 14617-8/-9, ISO 4067, EN ISO 10628-2 ve NFPA 170 **ücretli standartlardır**. Tam metinlerine web üzerinden ulaşılamadı. Bu katalogdaki geometriler şu kaynaklardan derlendi:
  1. Bu standartlardan türetilmiş, yaygın kullanılan sembol biçimleri (P&ID ve ASPE/ASHRAE lejant pratiği; aşağıdaki web kaynakları).
  2. **Kullanıcının kendi örnek Türk projelerindeki lejantlar** (en güvenilir kaynak bunlar, çünkü ROTAŞ'ın çizim tarzı bunlara göre şekilleniyor):
     - `kutuphane/ornek_mekanik/aselsan_teknopark/lejant/01_Isitma_Sogutma_Tesisati_Ana_Bina_lejant_01.png` (ısıtma-soğutma sembolleri)
     - `kutuphane/ornek_mekanik/aselsan_teknopark/lejant/05_Temiz_Su_Tesisati_Ana_Bina_lejant_01.png` (temiz su)
     - `kutuphane/ornek_mekanik/aselsan_teknopark/lejant/06_Havalandirma_Tesisati_Ana_Bina_lejant_01.png` (havalandırma)
     - `kutuphane/ornek_mekanik/aselsan_teknopark/lejant/02_Yangin_Tesisati_Ana_Bina_lejant_01.png` (yangın algılama + sprinkler)
     - `kutuphane/ornek_mekanik/ada_hayat/lejant/18_Yangin_Tesisati_Kolon_Semasi_lejant_01.png` (yangın kolon şeması)
- Güven sütunu: **A** = TR örnek lejantta görüldü ve standart pratikle uyumlu · **B** = uluslararası yaygın biçim, TR örneğinde yok · **C** = standartlar arasında çelişki var, ROTAŞ tercihi önerildi (kullanıcıya teyit ettirilmeli).
- **README kuralı geçerlidir:** Planda ve şemada MTY bloğu varsa (`kutuphane/ROTAS_2_MTY_BLOKLARI_*.tar.xz`, örn. `MTY-MANOMETRE`, `MTY-KOSVA VANA`, `MTY-BOSALTMA VANA`, `MTY-RADYATOR Panel`, `MTY-ROGAR KAT`), **önce MTY bloğu kullanılır**. Bu katalog yalnızca MTY'de karşılığı olmayan semboller için ve blok üretimi için referanstır.

## 1. Ortak çizim kuralları (tüm semboller)

| Kural | Değer |
|---|---|
| Blok orijini | Sembol merkezi, boru ekseni üzerinde (0,0). Boru **+X** yönünde akar. Döndürme INSERT `rotation` ile yapılır. |
| Temel ölçü | **L** = sembol boyu (boru ekseni boyunca). **H = 0,6·L** (vana yüksekliği). Bloklar L = 1,0 birim çizilir, INSERT ölçeğiyle büyütülür. |
| Önerilen kağıt boyu | Vanalar L ≈ 4–5 mm kağıtta → 1/50'de model L = 200–250 mm, 1/100'de 400–500 mm. Kolon şemasında L = 5 mm × şema ölçeği. |
| Boru kesme | Sembol boru çizgisini **±L/2 aralığında keser**. Boru çizgisi sembolün içinden geçmez (ezdxf'te boru iki parça LINE olarak çizilir). |
| Papyon (temel vana) | İki üçgen. Sol: (−L/2, +H/2) – (−L/2, −H/2) – (0,0). Sağ: (+L/2, +H/2) – (+L/2, −H/2) – (0,0). Kapalı LWPOLYLINE (`close=True`). |
| Dolgu | "İçi dolu" ifadesi = SOLID hatch (`hatch.paths.add_polyline_path`). |
| Metin | Sembol içi harfler (M, T, S, G, FD…): yükseklik 0,25·L, `MTEXT`/`TEXT` orta-ortaya hizalı. |
| Katman/renk | Sistemin katmanında (MTY katmanları: temiz su mavi, sıcak su kırmızı, pis su, yangın, doğalgaz sarı vb.). Sembol bloğu içi **BYLAYER**. |
| Numaralandırma | README gereği her vana/cihaz V-01, P-01… etiketi alır (ATTRIB). |

ezdxf iskeleti (papyon):

```python
def papyon(blk, L=1.0, H=0.6):
    blk.add_lwpolyline([(-L/2, H/2), (-L/2, -H/2), (0, 0)], close=True)
    blk.add_lwpolyline([(L/2, H/2), (L/2, -H/2), (0, 0)], close=True)
```

## 2. Vanalar ve armatürler

| Sembol (TR) | Standart / kaynak türü | Geometri tarifi (L = boy, H = 0,6L, orijin merkez) | Güven | Kaynak |
|---|---|---|---|---|
| **Genel vana / sürgülü vana (şiber)** | ISO 14617-8, DIN 2429, ASPE | Papyon (bölüm 1). Sürgülü vanayı ayırt etmek için ISO/P&ID pratiğinde merkeze **dik bir çizgi** eklenir: (0,−H/2)→(0,+H/2). **Yükselen milli vana** (yangın, OS&Y): papyon + merkezden yukarı mil çizgisi (0,0)→(0,0,55L) + üstte yatay el çarkı çizgisi (−0,2L,0,55L)→(+0,2L,0,55L). Ada Hayat lejantında mil çizgisinin sol yanında kısa bir "+" işareti var. | A | ada_hayat 18 lejant; https://hardhatengineer.com/valve-symbols-pid-ball-relief-valve/ |
| **Küresel vana** | ISO 14617-8, TR pratiği | Papyon + merkezde **içi boş daire**, r = 0,15L. Aselsan lejantında papyonun üstünde kısa kol çizgisi de var: (0,0)→(0,0,4L). Armatür bağlantılarında (ORNEK_DUZEN) bu sembol kullanılır. **Dikkat:** ISA/ASPE'de merkezde **içi dolu** nokta = **glob (ventil) vana**. ROTAŞ'ta karışmasın diye küresel = boş daire, glob/ventil = dolu nokta (r = 0,1L). | C | aselsan 01 ve 05 lejant; hardhatengineer (globe = koyu daire) |
| **Kilitli vana** | TR pratiği (aselsan) | Küresel vana + mil (0,0)→(0,0,45L) + üstte kilit kolu: genişliği 0,4L olan yatay çizgi ve uçlarından 0,1L aşağı inen kısa çizgiler (ters U). | A | aselsan 01 lejant |
| **Kelebek vana** | ISO 14617-8, ISA | Flanş çizgileri x = ±0,25L'de, boyları H+0,2L olan iki dik çizgi. Disk: (−0,2L,−0,3L)→(+0,2L,+0,3L) eğik çizgi. Merkezde içi dolu nokta, r = 0,05L. Boru çizgisi flanşlarda kesilir. Ada Hayat lejantında biçim sadeleştirilmiş: iki dik çizgi, sağdakinin üstünde sağa kıvrılan kol ("ı⌐ı"). **İzlenebilir kelebek vana** (yangın): + üstte 0,25L kare, içinde "S" (supervisory switch). | B/A | ada_hayat 18 lejant; https://hardhatengineer.com/valve-symbols-pid-ball-relief-valve/ |
| **Çekvalf (geri tepme ventili)** | ASPE / TR pratiği | TR lejant biçimi (aselsan, ada_hayat): sol dik çizgi (−0,3L,−H/2)→(−0,3L,+H/2); eğik "klape" çizgisi (−0,3L,−H/2)→(+0,3L,+H/2); sağ dik çizgi (+0,3L,−H/2)→(+0,3L,+H/2). Altında akış oku: (−0,25L,−0,65L)→(+0,25L,−0,65L) çizgisi ve uçta 0,1L'lik açık ok başı. ISO/DIN alternatifi: papyonun **çıkış tarafındaki üçgeni içi dolu**. ROTAŞ'ta TR biçimini kullanın. | A | aselsan 01/05, ada_hayat 18 lejant |
| **Emniyet ventili (emniyet vanası)** | ISO 14617-8, DIN 2429, TR | Köşe vana: giriş üçgeni (−L/2,±H/2)–(0,0); çıkış üçgeni aşağı veya yana 90° dönük: (±H/2,−L/2)–(0,0). Üstte yay: (0,0,05L)'den (0,0,7L)'ye 4 dişli zigzag LWPOLYLINE, genliği ±0,12L. Aselsan lejantında dikey biçim var: alt giriş, yukarı bakan üçgen, üstünde zigzag yay. Kalorifer kolon şemasında kazan gidişine dik çıkar ve çıkışı açık boşaltmaya gider. | A | aselsan 01/05 lejant; https://en.wikipedia.org/wiki/Piping_and_instrumentation_diagram |
| **Basınç düşürücü vana** | ISA / ISO 14617-8 | Papyon + mil (0,0)→(0,0,45L) + diyafram kubbesi: düz kenarı altta, y = 0,45L'de duran yarım daire (ARC, r = 0,25L, 0°–180°) + kapama çizgisi. Basınç algılama hattı: kubbenin sağ ucundan çıkış tarafındaki boruya (+0,8L,0) giden kesikli (DASHED) çizgi. Ada Hayat lejantında yalnızca papyon + "BD" etiketi var. Dengeleme tipi için yanına "BDV" yazılır. | B | ada_hayat 18 lejant; hardhatengineer |
| **Selenoid vana** | ISA 5.1 | Papyon + mil (0,0)→(0,0,4L) + üstte kare 0,3L × 0,3L, merkezi (0,0,55L), içinde "S". | B | https://en.wikipedia.org/wiki/Piping_and_instrumentation_diagram |
| **Motorlu vana (on-off / PICV)** | TR pratiği (aselsan) | Papyon (veya küresel) + mil (0,0)→(0,0,35L) + daire, r = 0,15L, merkezi (0,0,5L), içinde veya sağ üstünde "M". Basınçtan bağımsız (PICV) için aynı sembol + "PICV" etiketi. | A | aselsan 01 lejant |
| **3 yollu vana** | ISO 14617-8 | Üç üçgen tepeleri merkezde: sol (−L/2,±H/2)–(0,0), sağ (+L/2,±H/2)–(0,0), alt (±H/2,−L/2)–(0,0). Motorlu ise üstte mil + "M" dairesi (motorlu vana gibi). Karışım vanasında **ortak (AB) çıkış** ucuna ok konur. | B | hardhatengineer (3-way); Wikipedia P&ID |
| **Pislik tutucu (Y tipi)** | ISO 10628, TR | Flanş çizgileri: x = ±0,3L'de, boyları 0,6L olan iki dik çizgi. Gövde: (−0,3L,0)→(+0,3L,0) arasındaki boru. Y bacağı: (−0,1L,0)'dan 45° aşağı-sağa 0,35L boyunda çizgi, ucunda bacağa dik 0,15L kapak çizgisi (süzgeç tapası). Aselsan ve ada lejantlarında görünüm "\|‾\|" + altta eğik kısa bacak. | A | aselsan 01/05 lejant |
| **Kompansatör** | TR pratiği | Uçları x = ±0,35L'de, boyları 0,6L olan iki dik çizgi. Arada 3 tam dalgalı zigzag (körük): genliği ±0,25L, 6 kırılma noktası. | A | aselsan 01/05 lejant |
| **Termostatik radyatör vanası** | EN 215 pratiği / TR | Radyatör giriş vanası: papyon (L = 0,6 standart) + mil (0,0)→(0,0,3L) + termostatik kafa: dikdörtgen 0,25L × 0,35L, merkezi (0,0,5L), içinde "T". Planda radyatörün **gidiş ucuna** konur. Dönüş ucuna rakorlu dönüş vanası çizilir: küçük papyon (0,5L), içi dolu. | B | aselsan 01 lejant ("Radyatör–fancoil kesme vanası": daire + mil) |
| **Radyatör/fancoil kesme vanası** | TR (aselsan) | Daire, r = 0,2L, boru üstünde merkezli + üstte mil (0,0,2L)→(0,0,45L) ve kısa yatay kol (±0,12L). | A | aselsan 01 lejant |
| **Boşaltma vanası / otomatik besleme** | TR (aselsan, MTY) | Boru üzerinde "⊥" biçimi: boru eksenine dik kısa çizgi (0,0)→(0,0,4L) + üstte yatay çizgi ±0,2L + çıkışta küçük papyon. MTY bloğu: `MTY-BOSALTMA VANA`. | A | aselsan 01 lejant; MTY blokları |
| **Kolon boşaltma vanası (kosva)** | TR (aselsan, MTY) | Kolon dibinde yan yana iki küçük daire (r = 0,15L) ve her birinden 45° aşağı eğik çıkış çizgisi. MTY bloğu: `MTY-KOSVA VANA`. | A | aselsan 01 lejant; MTY blokları |

## 3. Cihazlar: pompa, kazan, boyler, tanklar

| Sembol (TR) | Standart / kaynak türü | Geometri tarifi | Güven | Kaynak |
|---|---|---|---|---|
| **Pompa (santrifüj, genel)** | ISO 14617-9, EN ISO 10628-2 | Daire, r = R (önerilen R = 0,5L). İçine çizilmiş eşkenar üçgen: tepesi **akış yönünde** çember üstünde (R,0), taban köşeleri (−R/2, +R·√3/2) ve (−R/2, −R·√3/2). Üçgen içi boş; ISO'nun "akış yönü" işaretidir. Boru girişi (−R,0)'da, çıkışı (+R,0)'da. Aselsan biçimi: daire + iç içe ikinci daire (r = 0,6R) + üstte ve altta flanş/ayak çizgileri. | A/B | aselsan 01/05 lejant; https://knowledge.bsigroup.com/products/graphical-symbols-for-diagrams-valves-and-dampers; https://iteh.es/catalog/standards/iso/f1981f1f-05dd-4ee9-87b8-8b740ab59e8e/iso-14617-9-2002 |
| **Sirkülasyon pompası** | ISO 14617-9 + TR | Pompa sembolüyle aynı. Kolon şemasında yanına "P-xx" ve "SİRK." yazılır. Frekans konvertörlü ise sağ üst köşeye 0,4R × 0,4R kare ve içinde "FK" (aselsan). İkiz pompa: iki pompa paralel; girişte ve çıkışta çekvalf + küresel vana. | A | aselsan 05 lejant |
| **Dalgıç pompa** | TR pratiği | Depo/çukur dikdörtgeni içinde, tabandan 0,2R yukarıda pompa dairesi (r = R). Su seviyesi: depo içinde yatay çizgi ve üstünde içi boş ters üçgen ▽ (kenarı 0,3R). Basma borusu daire tepesinden yukarı çıkar, çekvalf ve vana dikey hatta çizilir. Etiket "DP". | B | Wikipedia P&ID (pump genel); TR pratiği |
| **Yangın pompası seti** | NFPA 20 pratiği / TR | Her pompa ISO pompa sembolüdür: ana elektrikli ("EP"), dizel ("DP"; motor tarafında 0,8R × 0,6R dikdörtgen içinde "D") ve jokey ("JP", r = 0,6R). Set kesikli-noktalı (DASHDOT) dikdörtgen içine alınır, "YANGIN POMPA GRUBU" etiketiyle. | B | NFPA 20 genel pratiği; https://open-exam-prep.com/study-guides/nicet-water-based/program-code-framework/plans-specifications-reading |
| **Kazan** | TR pratiği, EN ISO 10628 (ısıtıcı) | Dikdörtgen: genişlik 1,0B, yükseklik 1,4B (B = 1,0 birim). Ortada "K" veya alevi temsil eden üçgen: tepesi yukarıda, tabanı 0,4B, yüksekliği 0,5B. Gidiş çıkışı tepeden (+0,25B), dönüş girişi alttan veya arkadan (−0,25B) çıkan kısa boru saplamaları. Baca: tepeden çıkan 0,2B genişlikte çift çizgi. | B | Wikipedia P&ID (furnace/heater) |
| **Boyler (serpantinli)** | ISO 10628 (vessel) + TR | Dikey kapsül: dikdörtgen 0,8B × 1,6B, üstte ve altta r = 0,4B yarım daire (ARC) kapaklar. İçeride serpantin: 4 dişli zigzag LWPOLYLINE, genişliği 0,5B, alt yarıda. Serpantin uçları sol kenardan çıkan iki saplama (primer gidiş üstte, dönüş altta). Soğuk su girişi alttan, sıcak su çıkışı tepeden, sirkülasyon dönüşü orta yükseklikten. MTY bloğu: `MTY-BOYLER KAT- KOLON`. | A/B | MTY blokları; Wikipedia P&ID (vessel, coil) |
| **Genleşme tankı — kapalı (membranlı)** | ISO 10628 + TR | Daire (yatay şemada) veya dikey kapsül, r = 0,4B. Membran: içeride yatay çap çizgisi; ISO ayrımı için tankın **üst yarısı** (gaz tarafı) ANSI31 tarama ile taranabilir. Bağlantı: alt orta noktadan aşağı inen saplama (0,−r)→(0,−r−0,3B), üzerinde kilitli (mühürlü) vana. Etiket "KGT … lt / … bar". | B | Wikipedia P&ID (pressurized vessel); TR pratiği |
| **Genleşme deposu — açık** | TR (TS 2164 dönemi pratiği) | Üstü açık dikdörtgen: 3 kenar (sol, alt, sağ), genişlik 1,2B, yükseklik 0,8B, üst kenar **çizilmez** veya kesikli çizilir. Su seviyesi: 0,6 yükseklikte yatay çizgi ve ▽. Bağlantılar: emniyet gidiş (üstten içeri kıvrılan boru), emniyet dönüş (alttan), sirkülasyon (alttan), taşma (üst seviyeden yana, aşağı inen), boşaltma (alttan, vanalı). | B | TR pratiği (TS 2164) |
| **Membranlı tank (hidrofor tankı)** | ISO 10628 + TR | Dikey kapsül 0,6B × 1,2B + yarım daire kapaklar. Membran: orta yükseklikte aşağı sarkan ARC (kiriş = tank genişliği, sehim 0,15B). Alttan bağlantı saplaması + küresel vana. Etiket "MT … lt". | B | Wikipedia P&ID (vessel) |
| **Hidrofor (paket)** | TR pratiği | Kesikli-noktalı çerçeve içinde: emiş kollektörü (alt yatay çift çizgi) → N adet paralel pompa (pompa sembolü + her pompada emişte vana, basmada çekvalf + vana) → basma kollektörü (üst yatay) → membranlı tank + manometre + basınç şalteri (küçük kare + "PS"). Çerçeve etiketi: "HİDROFOR Q=… m³/h H=… mSS". | B | aselsan 05 cihaz listesi (hidrofor seti); tesisat-hesap-kutuphanesi |
| **Kollektör** | TR (MTY) | Boru eksenine paralel yatay dikdörtgen: boy N·0,5B + 0,4B, yükseklik 0,25B. Uçlar kapalı (kör flanş: uca 0,1B dışarıda dik kısa çizgi). Çıkışlar üst kenardan 0,5B aralıklı dik saplamalar, her birinde vana. Bir ucuna hava atıcı, alt uca boşaltma vanası. Daire kollektörü (radyatör): `MTY-RADYATOR KOLLEKTÖR` / `KOLON` blokları. | A | MTY blokları; ORNEK_DUZEN.md |
| **Manometre** | ISA / TR (aselsan) | Borudan dik kısa saplama (0,0)→(0,0,3L), üstünde daire r = 0,12L, merkezi (0,0,42L). İçinde ibre: merkezden 45° yukarı-sağa 0,1L çizgi. Dairenin üstünde "M" harfi (h = 0,15L). Saplamaya isteğe bağlı küçük musluk papyonu (L = 0,2). MTY: `MTY-MANOMETRE`. | A | aselsan 01/05 lejant; MTY blokları |
| **Termometre** | ISA / TR (aselsan) | Manometreyle aynı biçim, harf "T". Kalın sistemlerde daldırma kovanı: saplama boru içine 0,1L uzatılır. | A | aselsan 01/05 lejant |
| **Otomatik hava atıcı (purjör)** | TR (aselsan) | Borudan dik saplama (0,0)→(0,0,2L) + küçük dikey kapsül 0,15L × 0,3L (yuvarlatılmış dikdörtgen) + tepede 0,1L dik çizgi ve küçük "+" (tahliye ucu). | A | aselsan 01 lejant |
| **Havalık tüpü (hava tüpü)** | TR (aselsan) | Dikey kapsül 0,2L × 0,35L, üstte ve altta yarım daire. Tepe çıkışı yok. Kolonun en üst noktasında bulunur. | A | aselsan 01 lejant |
| **Radyatör (panel)** | TR (MTY, aselsan) | **Plan:** gerçek boyda dikdörtgen (boy = radyatör uzunluğu, derinlik ~0,1 m panel), duvara paralel. Gidiş ucunda termostatik vana, dönüş ucunda rakorlu dönüş vanası. Etiket: "n m. PKKP600" (boy/tip/yükseklik). **Şema:** yatay dikdörtgen 1,2B × 0,3B, içinde 0,1B aralıklı dik çizgiler (dilim görünümü). MTY: `MTY-RADYATOR Panel`. | A | aselsan 01 lejant; MTY blokları |
| **Su sayacı** | EN 806-1 pratiği / TR | Boru üstünde daire, r = 0,3L. Boru dairenin içinden geçmez, çevrede kesilir. Daire içinde "S" (veya "SS") harfi ya da ok. Sayaç girişinde küresel vana, çıkışında çekvalf + küresel vana (daire sayaçlı bağlantı detayı). | B | https://www.din.de/de/mitwirken/normenausschuesse/naw/wdc-beuth:din21:381816763/toc-3556095/download (EN 806 içerik) |
| **Kalorimetre (ısı sayacı)** | EN 1434 pratiği / TR | Dönüş hattında dikdörtgen 0,6L × 0,4L, içinde "Q" veya "KM". Gidiş ve dönüş hatlarında birer küçük içi dolu daire (r = 0,05L) sıcaklık sensörü. Sensörlerden sayaca kesikli sinyal çizgileri. | B | TR pay ölçer pratiği |

## 4. Sıhhi tesisat — pis su / drenaj

| Sembol (TR) | Standart / kaynak türü | Geometri tarifi | Güven | Kaynak |
|---|---|---|---|---|
| **Yer süzgeci** | ASPE (FD) / TR MTY | **Plan:** gerçek ölçüde kare 150 × 150 mm (veya Ø100 daire), içinde Ø100 daire ve 4–5 yatay ızgara çizgisi (daire içine kırpılmış). Etiket "YS Ø50/Ø70". **Kolon şeması:** üstte ters yamuk (üst kenar 0,4B, alt kenar 0,2B, yükseklik 0,15B) + altında U sifon (yarım daire r = 0,1B). MTY: `YER SUZGECI DN701 KOLON`, `SUZGEC1 KOLON`, `IZGARA1`. | A | MTY blokları; https://www.wbdg.org/FFC/AF/AFDP/THULE_DORM/PlumbingSheets_v1.0.pdf |
| **Temizleme kapağı (T.T.K.)** | ASPE (CO) / TR MTY | **Plan:** daire r = 0,1B, içinde "+" veya içi dolu yarım daire; yanında "TK". **Kolon şeması:** pis su kolonundan 45° çıkan 0,2B saplama + uçta saplamaya dik 0,1B kapak çizgisi. Döşeme üstü kapakta saplama yatay çizilir. MTY: `T.T.K. KOLON SAG`. | A | MTY blokları; https://blocks.draftsperson.net/download/piping-and-plumbing-symbols-list/ |
| **Havalık (pis su havalığı)** | TR MTY | **Kolon şeması:** pis su kolonu çatıdan +0,5 m yukarı uzatılır. Uçta "şapka": dikey borunun üzerinde ortalı, ağzı aşağıda yarım daire (ARC 180°–360°, r = boru çapı × 1,5) veya ters U. **Plan:** kolon dairesi yanında "H" veya kolon numarası balonu ("Ø100 HAVALIK"). MTY: `MTY-KOLON NO HAVALIK`, `MTY-KELEPCE HAVALIK`. | A | MTY blokları |
| **Rögar (muayene bacası)** | TR pratiği / MTY | **Plan:** gerçek ölçüde kare (60×60 / 80×80 / 100×100 cm iç ölçü) çift çizgi (duvar 10–15 cm), içinde Ø60 kapak dairesi. Yanında etiket kutusu: "R-xx / KK: … / TK: …" (kapak kotu / taban kotu). Giriş ve çıkış borusu eğim okuyla. MTY: `MTY-ROGAR KAT`. | A | MTY blokları |
| **Pis su kolonu / iniş** | TR MTY | Plan: daire, r = boru çapı ölçeğinde, + kolon numarası balonu (daire r = 0,25B, içinde "PS1"). İniş yönü oklu. MTY: `MTY-PIS-SU-INIS`, `MTY-KOLON NO PIS SU`. | A | MTY blokları |

## 5. Yangın tesisatı

| Sembol (TR) | Standart / kaynak türü | Geometri tarifi | Güven | Kaynak |
|---|---|---|---|---|
| **Sprinkler — dik (upright)** | TR örnek (ada_hayat) / NFPA pratiği | Tek daire **Ø25 mm** (plan ölçeğinde gerçek değil, sembolik), içi boş. Yanında 3 satır metin: "25 / 1 / UP" (çap / başlık yükü / tip). Aselsan örneğinde upright, **iç içe çift daire** (◎) olarak gösterilmiş. Proje bazında lejantla tutarlı tutun. | C | ada_hayat KATALOG.md; aselsan 02 lejant |
| **Sprinkler — sarkık (pendent)** | TR örnek (ada_hayat) | İç içe çift daire: dış Ø25, iç Ø12, ikisi de içi boş. Alternatif US pratiği: dış daire + içi dolu iç daire. ROTAŞ önerisi: **ada_hayat biçimi** (dik = tek daire, sarkık = çift daire). Gizli (concealed) sarkık: dış daire + içi dolu iç daire. | C | ada_hayat KATALOG.md; https://mcgis.massillonohio.gov/archives/SitePlan/2023/Massillon%20City%20Schools/West%20side%20school/West%20Elem%20Drawings-%20July%20Submission%20FINAL/Volume%202%20of%202/6%20-%20Fire%20Protection/2953%20-%20Massillon%20West%20Site%20-%20FP-000%20-%20FIRE%20PROTECTION%20SYMBOLS%20AND%20ABBREVIATIONS.pdf |
| **Sprinkler — yan duvar (sidewall)** | NFPA / US lejant pratiği | Yarım daire Ø25: düz kenar duvara yaslanır (ARC 0°–180°, kiriş duvar çizgisi üzerinde). İçeride, düz kenarın ortasından odaya doğru püskürtme oku (0,5r uzunluk, açık ok başı). Etiket "SW". | B | Massillon FP-000 lejantı (yukarıdaki URL) |
| **Yangın dolabı** | TS EN 671-1 / TR örnek | Dikdörtgen 0,6B × 0,45B; iki köşegeni çizili (X) ve merkezde daire (r = 0,12B). Bağlantı borusu sol kenarın ortasından girer. Sağında hortum işareti: kısa yatay çizgi + şimşek benzeri zigzag (3 kırılma) + ok ucu. **Sıva üstü:** dikdörtgen içi boş. **Sıva altı:** ada lejantında aynı biçim. Ayırt etmek için sıva altında dikdörtgen duvar içine gömülü çizilir veya ANSI31 ile taranır. Lejant metni: "Hortum Ø1" / 30 m, kesme vanası 2", ABC 6 kg". | A | ada_hayat 18 lejant |
| **İtfaiye bağlantı ağzı (bina)** | TR örnek / NFPA (FDC) | **TR (ada_hayat):** boru çizgisi bir köşeli parantezle biter: boru ucundan dik çizgi (yükseklik 0,5B), uçlarından borudan uzağa doğru 0,15B yatay kısa çizgiler ("[" biçimi). **İkiz ağız (2×2½")**: borunun ucunda ±45° açılı iki kısa kol (0,3B) ve uçlarında birer küçük daire (r = 0,06B) — "Y/siyam" biçimi. Kolon balonu "İB1". | A/B | ada_hayat 18 lejant; Massillon FP-000 |
| **Islak alarm vanası (W.A.V.)** | TR örnek (ada_hayat) | Papyon (L) + sağına bitişik üçüncü üçgen: tepesi solda (L/2,0), tabanı x = L'de dik çizgi (yükseklik H). Yani "⋈▷\|" biçimi (vana + çek klape). Kuru (D.A.V.) / ön tepkili (P.A.V.) için yanına harf etiketi konur. Aselsan pre-action vanası ise ayrıntılı blok olarak çizilmiş. | A | ada_hayat 18 lejant; aselsan 02 lejant |
| **Akış anahtarı (flow switch)** | TR örnek (ada_hayat) | Kare (kenar 0,5L) boru ekseninde ortalı; içinde papyon (köşeden köşeye çapraz iki üçgen) ve merkezde küçük daire (r = 0,08L). US pratiği: boru üzerinde dik saplama + bayrak üçgeni + "FS". | A | ada_hayat 18 lejant |
| **Basınç sınırlayıcı itfaiye bağlantı vanası** | TR örnek | Ayrıntılı vana bloğu (açılı vana + el çarkı). Basit gösterim: köşe vana (90° iki üçgen) + mil + el çarkı çizgisi + çıkışta kısa kaplin çizgisi. | A | ada_hayat 18 lejant |
| **Otomatik purjör (sprinkler hattı)** | TR örnek | Dik saplama üzerinde küçük papyon + üstte daire (r = 0,1L) + daireden 45° yukarı çıkan kısa ok çizgisi. | A | ada_hayat 18 lejant |
| **Hidrant (yer üstü)** | NFPA 170 / TR pratiği | Daire r = 0,25B, içinde "H" veya içi dolu küçük daire. Daireden 0°, 180° ve 90° yönlerinde 0,1B'lik çıkış saplamaları (ağızlar). Bağlantı borusu alttan. Etiket "YH-xx". | B | https://docs.dnv.org/documents/standard-fire-safety-plan-symbols.pdf; https://coquitlam.ca/DocumentCenter/View/199/Fire-Prevention-Symbols-PDF |
| **Test-drenaj seti / kolon balonları** | TR örnek | Kolon numarası balonları: daire, r = 0,25B, içinde "Y1" (yangın dolabı kolonu), "Sp1" (sprinkler), "TD1" (test drenaj), "İB1" (itfaiye bağlantı). Kat zon kontrolü: izlenebilir kelebek vana → çekvalf → manometre → akış anahtarı → test-drenaj vanası (ada_hayat F1-A detayı sırası). | A | ada_hayat 18 lejant |
| **Not: NFPA 170** | NFPA 170 | NFPA 170 asıl olarak **yangın güvenlik ve acil durum planı** sembollerini (kat planı tahliye/itfaiye planları) tanımlar. Sprinkler projesi çizim sembolleri ise genelde ofis lejantıyla belirlenir. Bu nedenle hidrant, FDC ve yangın dolabı için NFPA 170 biçimi referanstır, sprinkler başlıkları için proje lejantı esastır. | — | https://www.aacounty.org/sites/default/files/2025-06/signage-requirements.pdf |

## 6. Havalandırma

| Sembol (TR) | Standart / kaynak türü | Geometri tarifi | Güven | Kaynak |
|---|---|---|---|---|
| **Üfleme (besleme) kanal kesiti** | ASHRAE / SMACNA pratiği, TR | Kanal kesit dikdörtgeni (gerçek ölçü G × Y) + **iki köşegen (X)**. Yuvarlak kanalda daire + iki çapraz çap. | B | https://blocks.draftsperson.net/download/hvac-symbols-list/; https://mepacademy.com/?p=5725 |
| **Emiş / dönüş kanal kesiti** | ASHRAE pratiği | Dikdörtgen + **tek köşegen** (sol alttan sağ üste). Egzoz (atış) kanalında tek köşegen ters yönde (sol üstten sağ alta). Hangi köşegenin ne anlama geldiği lejantta mutlaka gösterilir. | B | aynı kaynaklar |
| **Kanal (planda)** | TR (aselsan) | Gerçek genişlikte çift çizgi. Üfleme, emiş ve WC emiş kanalları farklı katmanda/çizgi tipinde çizilir. Flex bağlantı: 0,05 m aralıklı dik çizgilerle (akordeon) taranmış çift çizgi. Kanal boyutu etiketi: "600×300". | A | aselsan 06 lejant |
| **Üfleme menfezi / difüzör (tavan, 4 yönlü)** | ASHRAE pratiği / TR | Kare (gerçek ölçü, örn. 600×600 tavan modülü) + iki köşegen (X) + her kenarın ortasından dışa doğru ok (0,3 × kenar, açık ok başı). 1/2/3 yönlü difüzörde ok sayısı yöne göre azalır. Kasetli fancoil de aynı mantıkla çizilir (aselsan: kare + 4 dış ok). | A/B | aselsan 01/06 lejant; https://www.archtoolbox.com/hvac-plan-symbols/ |
| **Emiş menfezi / dönüş ızgarası (tavan)** | ASHRAE pratiği | Kare + **tek köşegen**; ok yok veya oklar kareye doğru. Perfore menfez: kare + iç kare + X (aselsan "PERFORE MENFEZ"). | B | archtoolbox; aselsan 06 lejant |
| **Kanal üstü / yan menfez (tek veya çift sıra kanatlı)** | TR (aselsan) | Kanal kenarına bitişik dikdörtgen (menfez boyu × 0,1 m). Üflemede kanaldan dışa, emişte kanala doğru oklar. Yuvarlak kanal menfezi: kanal üstünde kısa dikdörtgen + 3 ok. | A | aselsan 06 lejant |
| **Slot difüzör** | TR (aselsan) | Uzun ince dikdörtgen (boy × 0,1 m) + slot sayısı kadar boyuna paralel çizgi. Üflemede dikdörtgenin üstüne 0,2 m aralıklı kısa ok çizgileri (aşağı), emişte yukarı. | A | aselsan 06 lejant |
| **Swirl difüzör / anemostat** | TR (aselsan) | Kare (veya daire) + eş merkezli daire + merkezden 6–8 eğri kanat (kısa ARC'ler). Anemostat: iç içe 3 eş merkezli daire. | A | aselsan 06 lejant |
| **Panjur (taze hava alış / egzoz atış)** | TR (aselsan) | Duvar boşluğunda dikdörtgen + 45° eğik paralel kanat çizgileri (4–5 adet). Taze havada dışarıdan içeri ok, egzozda içeriden dışarı ok. | A | aselsan 06 lejant |
| **Ayar damperi (volume damper)** | ASHRAE / ISO 14617-8 | Kanal çift çizgisi arasında, kanal eksenine 30° eğik tek çizgi (kanat). Ortasında pivot dairesi (r = 0,05 G). Kanal dışına uzanan kol çizgisi (0,2 G) + "VD". Aselsan: "KANAL AYIRMA KLAPE KOLU". | B | https://knowledge.bsigroup.com/products/graphical-symbols-for-diagrams-valves-and-dampers; aselsan 06 lejant |
| **Yangın damperi** | ASHRAE pratiği / TR | Kanal içinde, kanala dik dar dikdörtgen (genişlik = kanal genişliği, kalınlık 0,1 G) ve dikdörtgen içinde iki köşegen (X). Yanında "FD" (motorlu ise "MFD" + "M" dairesi). Aselsan lejantı: kısa çizgi + altta "FD". Duman damperi "SD", geri akış damperi "BDD" (aselsan). | A/B | aselsan 06 lejant; https://blocks.draftsperson.net/download/hvac-and-mechanical-services-symbols-legend/ |
| **Fan (radyal)** | ISO 14617-9 / EN ISO 10628 | Daire r = R + çıkış ağzı: dairenin üst noktasına teğet, akış yönüne uzanan dikdörtgen kanal (genişlik 0,6R, boy 0,8R). İçeride salyangoz için isteğe bağlı spiral ARC. | B | iteh ISO 14617-9; Wikipedia P&ID (radial fan) |
| **Fan (aksiyal / kanal tipi)** | ISO 14617-9 | Kanal içinde daire r = R, daire içinde merkezde birleşen iki üçgen kanat (papyon, eksene dik). Kanal tipi aspiratör (aselsan): dikdörtgen kutu + içinde daire + kanat. | B | Wikipedia P&ID (axial fan); aselsan 06 lejant |
| **Aspiratör — duvar tipi / WC** | TR (aselsan) | Duvar üzerinde dikdörtgen 0,3 × 0,15 m + içinde daire + "X" kanat. Etiket örneği: "Wc Aspiratörü 80/160 m³/h - 50 Pa - Ø150 mm" (ORNEK_DUZEN). | A | aselsan 06 lejant; ornekler/ORNEK_DUZEN.md |
| **Aspiratör — çatı tipi** | TR (aselsan) | Plan: daire + içte 4 radyal kanat çizgisi. Kesit: dikey kanal üzerinde mantar başlık (geniş yarım daire, ağzı aşağıda). | A | aselsan 06 lejant |
| **Jet fan (otopark)** | TR (aselsan "JET CAP") | Uzun dikdörtgen (gerçek boy) + bir ucunda daire + atış yönünde ok. | A | aselsan 06 lejant |
| **Fancoil (gizli tavan tipi)** | TR (aselsan) | Dikdörtgen gövde + emiş tarafında taranmış filtre şeridi + üfleme tarafında flanş. Gidiş-dönüş-drenaj saplamaları yanda. | A | aselsan 01 lejant |

## 7. Doğalgaz

| Sembol (TR) | Standart / kaynak türü | Geometri tarifi | Güven | Kaynak |
|---|---|---|---|---|
| **Gaz vanası (küresel, kesme)** | TS EN 331 vana + dağıtım şirketi şartname lejantı | Papyon, **iki üçgen de içi dolu** (SOLID hatch); su vanasından böyle ayrılır. Ana kesme vanasına kol çizgisi (0,0)→(0,0,4L) + "AKV". Cihaz vanası: aynı sembol, L = 0,6. Katman: doğalgaz (sarı). | C | Dağıtım şirketi teknik şartname lejant pratiği (İGDAŞ/AKSA vb.); proje bazında teyit edilmeli |
| **Gaz sayacı** | TR pratiği | Dikdörtgen 0,8L × 0,6L. Boru üst kenarın iki ucuna dikey saplamalarla bağlanır (körüklü sayaç, giriş solda, çıkış sağda). İçinde "G4" / "G6" (tip) veya "S". | B | Dağıtım şirketi lejant pratiği |
| **Basınç regülatörü** | ISO 14617-8 (basınç düşürücü) | Basınç düşürücü vana geometrisi (papyon + diyafram kubbesi + çıkışa kesikli algılama hattı), üçgenler içi dolu, etiket "R" ve kademe ("21 mbar"). Servis kutusunda (dikdörtgen kutu, kesikli çizgi): giriş vanası + regülatör + sayaç. | B | hardhatengineer (PRV mantığı) |
| **Selenoid / deprem vanası (gaz)** | ISA | Selenoid vana geometrisi, üçgenler içi dolu. Deprem vanasında kare içinde "D". | B | Wikipedia P&ID |

## 8. Çelişkiler ve teyit edilecek noktalar (kullanıcıya sorulmalı)

1. **Küresel vana ve glob vana:** ISA/ASPE pratiğinde papyon + içi dolu nokta = glob vana; TR lejantlarda küresel vana papyon + boş daire (kollu). Öneri: küresel = boş daire, ventil = dolu nokta.
2. **Sprinkler dik/sarkık:** ada_hayat lejantında dik = tek daire, sarkık = çift daire. Aselsan'da upright çift daire olarak gösterilmiş. Proje lejantına göre seçilmeli. Varsayılan öneri: ada_hayat biçimi.
3. **Çekvalf:** TR lejantlarında "|/|" + ok biçimi kullanılıyor (ISO'daki dolu üçgen biçimi değil). Öneri: TR biçimi.
4. **Gaz vanası (dolu papyon):** Bu ayrım dağıtım şirketine göre değişir. İlgili şirketin şartname lejantıyla teyit edilmeli.
5. Standart tam metinleri (DIN 2429-2, ISO 14617-8/-9, EN 806-1 Tablo sembolleri) satın alınırsa B/C dereceli satırlar ölçü oranlarıyla birlikte güncellenmelidir.

## 9. Web kaynakları

- ISO 14617-8 (vanalar ve damperler) — https://knowledge.bsigroup.com/products/graphical-symbols-for-diagrams-valves-and-dampers
- ISO 14617-9 (pompa, kompresör, fan) — https://iteh.es/catalog/standards/iso/f1981f1f-05dd-4ee9-87b8-8b740ab59e8e/iso-14617-9-2002
- ISO 01.080.30 grafik sembol standartları listesi — https://www.iso.org/ics/01.080.30.html
- P&ID (ISO 10628, ISO 14617, ISA 5.1 özeti) — https://en.wikipedia.org/wiki/Piping_and_instrumentation_diagram
- Vana sembolleri P&ID — https://hardhatengineer.com/valve-symbols-pid-ball-relief-valve/
- EN 806 / DIN içerik tablosu — https://www.din.de/de/mitwirken/normenausschuesse/naw/wdc-beuth:din21:381816763/toc-3556095/download
- DIN EN 806-1 sembol tartışması — https://www.bauexpertenforum.de/goto/post?id=1391422
- ASPE tarzı sıhhi lejant örneği (WBDG) — https://www.wbdg.org/FFC/AF/AFDP/THULE_DORM/PlumbingSheets_v1.0.pdf
- Sıhhi ve boru sembol listesi — https://blocks.draftsperson.net/download/piping-and-plumbing-symbols-list/
- HVAC sembol listesi — https://blocks.draftsperson.net/download/hvac-symbols-list/
- HVAC ve mekanik lejant — https://blocks.draftsperson.net/download/hvac-and-mechanical-services-symbols-legend/
- HVAC plan sembolleri — https://www.archtoolbox.com/hvac-plan-symbols/
- HVAC sembolleri (MEP Academy) — https://mepacademy.com/?p=5725
- Yangın koruma sembol/kısaltma paftası (FP-000) — https://mcgis.massillonohio.gov/archives/SitePlan/2023/Massillon%20City%20Schools/West%20side%20school/West%20Elem%20Drawings-%20July%20Submission%20FINAL/Volume%202%20of%202/6%20-%20Fire%20Protection/2953%20-%20Massillon%20West%20Site%20-%20FP-000%20-%20FIRE%20PROTECTION%20SYMBOLS%20AND%20ABBREVIATIONS.pdf
- Yangın güvenlik planı sembolleri (NFPA 170 tabanlı) — https://docs.dnv.org/documents/standard-fire-safety-plan-symbols.pdf, https://coquitlam.ca/DocumentCenter/View/199/Fire-Prevention-Symbols-PDF
- Plan okuma (NICET, sprinkler sembolleri) — https://open-exam-prep.com/study-guides/nicet-water-based/program-code-framework/plans-specifications-reading
