# Uçtan uca sıhhi tesisat denemesi — karşılaştırma (new_block.dxf) — R1 / R2 / R3 / R4

Tarih: 14.10.2026. R1: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME.dxf`; **R2 (14.10.2026 kullanıcı kuralları):** `proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R2.dxf` (`motor/deneme/uctan_uca/nb.py` + `r2.py`).
Referans: kullanıcının aynı dosyadaki MTY çizimi (MTY-* katmanları). Kullanıcı çizimi tanımaya **girmedi**; yalnız burada okundu.
Koordinatlar zemin kat mimari kaynak koordinatıdır (cm). Kullanıcının kolon konumu = "MTY-KOLON NO" bloğunun yerleştirme noktası (P1, P3, P4, P6, P8, P9 için kullanıcının pis su borusunun ucuyla 8 cm içinde çakışıyor; yani gerçek kolon yeri).

## R4 — new_block sıhhi düzeltmeleri (`nb4.py` + `sema4.py` + `cikti4.py` + `etiket4.py`)

Çıktı: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R4.dxf` (AC1032). Özet: `ozet_r4.json`. Önizlemeyle (zemin planı, ıslak hacim yakın
görünüşü, giriş holü, kolon şeması depo/sayaç bölgesi, lejant paftası) kontrol edildi.

| İstek | R3 (önce) | R4 (sonra) |
|---|---|---|
| 1. Dar ıslak hacimde çap etiketi / aspiratör yazısı mahal adına / başka yazıya binmesin; çap etiket yüksekliği 10 | yazı-yazı çakışması **404** (mimari-mimari hariç; mahal adı dahil); çap etiketi 8 | **0** (`ykontrol4`, tüm DXF). Etiket yüksekliği **10**. 156 çap etiketi taşındı (87'si boru ekseni boyunca, gerisi boruya dik + kılavuz), 76 serbest yazı grubu (aspiratör, şaft adı, EK süzgeç, ADK/DBK) taşındı, 592 yerinde; yerleşemeyen 0 |
| 2. Şebeke hattı bina girişinden ortak alandan, hol ORTASINDAN; daire içinden / salondan geçmesin | giriş holü ile salon arasındaki duvar dibi boyunca | giriş holünün orta kotundan (hol ortası y = −442157), DBK'ya A*; daire mahali içinde **0 cm**, duvara ortalama **48 cm** (uçlardaki 60 cm hariç; DBK duvar köşesinde olduğu için son parça duvara yakın). Boy 9,2 m, 6 nokta. Yasak bölge / daire içi ana hat ihlali 0 |
| 3. Sayaç düzeni planla şema aynı; zeminde toplu sayaç kalmasın; şemada sayaç hatlarında kesişme 0 | planda daire kapısında sayaç, şemada zemin bandında 9'lu toplu sayaç grubu | şemada çatı deposu → çatı dağıtım hattı (kolon havalıklarının üstünden) → her daire konumu için ADK inişi → her katta vana + SAYAÇ + çek valf + giriş vanası (daire kapısında). Toplu sayaç grubu **yok**; bina girişinde yalnız şebeke ana sayacı (planda da öyle). Sayaç / ADK / dağıtım hattı (13 parça) kesişmesi **0** |
| 4. SIHHİ DETAYLAR çerçevesi içerikten | sabit genişlik (R1'de 518 095 birimlik hata) | içerik kutusundan: **994** birim (x 28780–29774) |
| 5. Pis su – temiz su planda üst üste görünme (köprü yok) | **176** nokta | **112** nokta (PIS-SO 52, PIS-SC 60); temiz su güzergâhında pis su hattının ±4 cm bandı ceza 30. Z kat D3'te cezalı güzergâh soğuk hat ötelemesini kendine kestirdiği için bu daire cezasız (R3) çizildi. Köprü 0 |
| 6. Pafta sonu kendi sembollerimizle lejant + armatür / malzeme adet + boru metrajı; MTY 0 | ROTAS blok lejantı (blok adlarıyla) | "LEJANT, MALZEME / ARMATÜR ADET TABLOSU VE BORU METRAJI" paftası: 24 sembol satırı (kendi saf geometri bloklarımız, açıklamalar semboller2), PLAN ADET / ŞEMA ADET ayrı, 6 boru çizgi örneği; armatür / cihaz adet; vana / sayaç / süzgeç / fan adetleri; boru metrajı. Çerçeve içerikten. **MTY 0** |

R3 kontrolleri (R4): temiz su kesişmesi 0 · pis su kesişmesi 0 · köprü/atlatma 0 · MTY 0 · yasak bölge 0 · kolon-şaft 0 · ıslak hacim başına
süzgeç 27/27 = 1 · 45° dışı pis su parçası 0 · balkon-pis su teması 0 · boşta uç 0 · kolon çakışması 0 · AUDIT 0/0 · yazı-yazı çakışması 0.

R4 sınırları / sorulacaklar:
- Şemada her daire konumunun kendi ADK inişi var (plan: ADK-1 D1/D2 konumları, ADK-2 D3); iniş etiketleri planın ADK adıyla. Tek ADK'dan iki
  konuma kat başında ayrılan yatay çizilirse pis su kolonlarını keserdi; bu yüzden şemada konum başına iniş. Onay gerekir.
- Şemada daire içi dağıtım hattı (giriş vanasından armatürlere) kendi dairesinin pis su kolonunu düşeyde keser (şema geleneği, farklı düzlem);
  sayaç hatlarında kesişme yok.
- Etiketlerin bir kısmı (145) boru ekseninden dik kaydırıldı ve kılavuzla bağlandı (dar ıslak hacimlerde eksende yer yok).
- Pis su – temiz su üst üste görünme 112'ye indi, 0 değil (armatür bağlantı noktalarında kaçınılmaz temaslar; köprü çizilmez).

## R3 — 14.10.2026 (B) revizyon talimatı (`nb3.py` + `r3.py` + `semb3.py` + `sema3.py` + `cikti3.py`)

Çıktı: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R3.dxf` (AC1032; R1 / R2 dosyaları önce/sonra karşılaştırması için korunur). Özet: `ozet_r3.json`.

| Kural (14.10 B) | R2 (önce) | R3 (sonra) |
|---|---|---|
| MTY bloğu kullanılmaz; semboller saf geometri | MTY adı geçen: 21 blok tanımı, 35 katman, 666 INSERT, 109 blok içi katman, 3 yazı (toplam 834); `MTY-SIHHİ DETAYLAR` bloğu içe aktarılıyordu | **0** (blok / katman / çizgi tipi / INSERT / blok içi katman / yazı; `cikti3.mty_kontrol`). 35 `ROTAS-` blok, hepsi saf geometri (LINE / CIRCLE / LWPOLYLINE / HATCH), iç katman 0. Geometri: 32 sembol `semboller2/sembol2.py` kütüphanesinden (eski yerleşim kutusuna oranla sığdırılır), 3 sembol (pis su / temiz su çap etiketi yalnız öznitelik, PVC dirsek) `semb3.py`. SIHHİ DETAYLAR saf geometri tablolarla (SB/YB değerleri, pis su ve temiz su çap tabloları, yer süzgeci ve havalık kesiti) |
| Boru atlatma (köprü/jumper) yok; sıcak-soğuk kesişmez | xcheck köprüsü 36, çakışık 22 | çizilen köprü **0** (`xcheck.hops` çağrılmaz); temiz su kesişmesi (soğuk-soğuk, soğuk-sıcak, sıcak-sıcak, ana hat, şebeke) **0**; pis su-pis su **0** (`r3.kesisimler`, 3 kat) |
| Koridorda hat koridor ORTASINDAN; ıslak hacimde mahal ortasından | A* duvar dibini tercih ediyordu | maliyet alanı (`r3.Alan`): duvardan uzaklaştıkça ucuz (1 + 2,2·e^(-d/18)), duvar delme +20, yatak odası/salon pahalı ve orada duvar dibi bandı (14-40 cm) ucuz (ebeveyn banyosu geçişi), betonarme / asansör / enerji odası / havalandırma şaftı yasak; başka dairenin hacimleri +6 (kapılardan yürüme mesafesiyle daire etiketi, bina dışı kapalı) |
| Sıcak-soğuk paralel | sıcak = soğuk ağacının 7 cm ötelemesi (dallanmalarda kesişme) | sıcak su kombiden **tek hat** (dallanmasız), sıcak su alan armatürleri sırayla dolaşır; soğuk su bu hattın tamamı boyunca **10 cm paralel** (eksenin ±5 cm iki yanı). Klozet / ÇM / BM ve daire girişi soğuk hatta soğuk taraftan tek branşmanla (sıcak hat ızgarada engel). Not: paralel çift hattın T ile dallanması düzlemde kesişmesiz çizilemez (topolojik zorunluluk), bu yüzden sıcak hat dallanmaz |
| Pis su: kolona en kısa yoldan, 45° dirsek; dallı (balık sırtı), seri yok; birbirini kesmez | en yakın ağaç, eğik doğrudan hatlar (armatürden armatüre zincir oluşabiliyordu) | her ıslak hacimde kolondan en uzak armatüre 45° kırıklı omurga; diğer armatürler omurgaya 45° **tekil** branşmanla (73 branşmanın 15'i doğrudan kolona, omurgaya 45° bağlanamayan konumda). 45°/90° dışı açılı parça **0**; pis su kesişmesi **0** |
| Kolon mekanik havalandırma şaftı içinde değil | P2, P5, P8 şaft ("mek. havl.") içinde | şaft poligonu mimariden (yazı yanındaki Ø kanal dairesi → ortogonal duvarlarla kapalı dikdörtgen); P2 +18 cm, P5 −18 cm, P8 +32 cm kendi mahalline doğru ötelendi → kolon-şaft **0** (3 kat) |
| Her ıslak hacimde tam 1 yer süzgeci | mimarideki süzgeçler (mutfak / bazı wc'lerde yok) | 27 ıslak hacmin hepsinde **1** (17 EK süzgeç: 9 mutfak, 5 wc-lvb., 2 wc-banyo, 1 wc-duş; fazla süzgeç yok). Süzgeç pis su ağına 45° branşmanla bağlı |
| Balkon süzgeci ayrı hat | 15, yağmur inişine | aynı (15, Ø50 → yağmur inişi); balkon hattı-pis su teması **0** |
| ÇM mimarideki konumda | mimari ÇM konumu / EK | aynı: mimaride gösterilen ÇM'nin bağlantısı kendi konumunda; mimaride yoksa R2 "EK" kuralı (D3/D5/D8 wc+banyo ÇM, D3/D5/D8 mutfak BM) |
| WC/banyo havalandırması kat planında + kolon şemasının sonunda | yok (yalnız ayrı izometri modülü) | kat planlarında 15 aspiratör (ROTAS-ASPIRATOR) + şafta Ø150 bağlantı + "WC ASPİRATÖRÜ 80 m³/h - 50 Pa / Ø150 → Ş4 (D1-6-9)" + şaft çerçevesi "Ş1..Ş4 MEK. HAVL. ŞAFTI"; kolon şemasının sağında (aynı pafta) 4 havalandırma kolonu, katlarda aspiratör branşmanları, çatıda çatı tipi fan (Ş1 240 m³/h 13 Pa, Ş2 80 m³/h 2 Pa, Ş3 480 m³/h 50 Pa, Ş4 400 m³/h 35 Pa, ÇF-200). Hesap `wc_havalandirma` (algila + hesap, hacim başına aspiratör) |
| Elektrik kalemi yok | yok | yok |
| Yasak bölge (betonarme / asansör / enerji odası) | 0 | **0**; boşta uç 0; kolon çakışması 0 |

Kontrol özeti (R3): kesişme/atlatma 0 · MTY 0 · yasak bölge 0 · kolon-şaft 0 · ıslak hacim başına süzgeç = 1 (27/27).
Bilgi: planda pis su hatları ile temiz su hatları 176 noktada üst üste görünür (pis su tavan/döşeme altı, temiz su şap içi: farklı
düzlem; köprü çizilmedi). İstenirse bu sayı da kural haline getirilip güzergâh buna göre aranabilir.

R3 sınırları / sorulacaklar:
- Sıcak su dallanmadığı için sıcak hat bazı dairelerde ıslak hacimden çıkıp bir sonrakine gider (D1/D2'de kombi balkonda: balkon → mutfak →
  hol → wc → banyo). Kullanıcının alıştığı "sıcak + soğuk birlikte dallanan" çizim kesişmesiz olamaz; bu kurgu onaylanmalı.
- Soğuk-alan armatür branşmanları (klozet, ÇM) bazı ıslak hacimlerde çift hattan ayrı bir güzergâhla gelir (sıcak tarafından kesmeden dolaşır).
- Daire etiketi kapılardan yürüme mesafesiyle; kombi balkonda olan dairelerde balkon komşu daireye etiketlenebiliyor (yumuşak ceza ile çözüldü).
- Şebeke hattı (bina girişi → DBK) giriş holü ile salon arasındaki duvar boyunca; aday güzergâhlardan en az ceza seçilir.
- Havalandırma: hacim başına aspiratör (80 m³/h); R2 izometrisindeki "banyo + wc tek aspiratör 160" kabulü için `oda_basina_aspirator` False yapılabilir.
- Yazı yoğunluğu: dar ıslak hacimlerde çap etiketleri ve aspiratör yazısı mahal adına binebiliyor (maske var, konum ayarı yapılmadı).

## 0. 14.10.2026 kuralları — önce / sonra

| Kural | R1 (önce) | R2 (sonra) |
|---|---|---|
| YB/SB yöntemi MTY ile aynı (MB/inç'e geçilmez) | YB / SB, Ø mm | aynı (değişmedi): YB / SB, Ø mm |
| Kolon–rögar bağlantı çapı | Ø100 (kolon çapından) | hesap: kolon toplam SB P1 24, P2 24, P3 75, P4 24, P5 36, P6 75, P7 24, P8 71, P9 33, P10 19 → Ø100 yeterli (≤160 SB, zemin altı en az Ø100); kullanıcı Ø125 çizmiş → hesap Ø125 GEREKTİRMİYOR, Ø100 yazıldı. Fark: kullanıcı bir kademe büyük seçmiş (emniyet/tercih) |
| Her dairede ÇM + BM hattı | mimaride yoksa yok (3. daire konumunda ÇM ve BM eksik) | eklendi: Z kat: CM D3, BM D3; 1 kat: CM D5, BM D5; 2 kat: CM D8, BM D8 ("EK" işaretli, pis su + soğuk su bağlı) |
| Balkon süzgeci pis suya bağlanmaz | balkon süzgeci yok | 15 balkon süzgeci (kat başına 5), Ø50 ayrı süzgeç hattı ile en yakın yağmur inişine; pis su ağına bağlı süzgeç: 0 |
| Daire içi sıcak + soğuk yan yana | sıcak kombiden ayrı A* ile (paralel oran %36) | sıcak = soğuk ağacında kombi→sıcak armatür yolları, 7 cm paralel öteleme (zemin kat sıcak hattın %100'i soğuğa ≤12 cm paralel) |
| Kolonlar mahal köşesinden; şaft/ortak duvar | klozet duvarında en yakın köşe; kullanıcıya ort. 115 cm | yalnız köşe adayları (gerçek duvar = birleşik ≥100 cm eksen çizgisi), SB ağırlıklı boru boyu + "mek. havl." şaftı + komşu ıslak hacim puanı; kullanıcıya ort. **58 cm** (tablo 1) |
| Kolon numarası P1.. (kullanıcı biçimi), sembol yanında, çakışmasız | P1.. (sıra daire→banyo/wc/mutfak), 45° sabit ofset; çizgiye binen balon 9/9 | P1.. kullanıcı sırası (daire→mutfak/wc/banyo/duş = kullanıcının P1..P9 ile aynı); 16 yön × 5 mesafe aramayla boş yer; çizgiye binen balon 0/10 |
| YB/SB etiketi boru ekseninde | pis su ekleme noktası–boru ort. 0.0 cm; temiz su 1.4 cm (23/26 eksende) | pis su ort. 0.0 cm; temiz su ort. 0.0 cm (26/26 eksende); blok boru doğrultusunda döndürülmüş, ölçek 8 |
| Taşıyıcı kolon / asansör / şaft / enerji odası | yalnız betonarme kontrolü (0 çakışma) | geometrik kontrol (`nb.yasak_kontrol`): betonarme + asansör boşluğu + enerji odası, tüm hatlar, 3 kat → 0 ihlal; router bunları yasak alan sayar |
| Ana besleme / kolektör daire içinden geçmez | merdiven holünde 9'lu kolon kutusu, 3. daireye hol boyunca ~9 m dikey hat; şebeke hattı daire duvarı boyunca | ADK kolonları daire kapılarının yanında, holde (ADK-1: D1/2, ADK-2: D3); kolon→kapı hatları yalnız ortak alan ızgarasında (daire mahalleri kapalı), toplam 9.8 m / 9 daire; daire içine giren ana hat: 0 |
| Alt/üst kat planı farklı → geçiş uyarlanır, tüm kolonlar numaralı | üst katta farklı adlı ıslak hacimler (1. kat wc-banyo, wc-duş) tanınmıyordu; 1. kat D6 wc-duş tesisatsızdı | wc-banyo / wc-duş tanınır; ıslak hacim → daire ataması kapılardan yürüme mesafesiyle; zeminde karşılığı olmayan 1. kat wc-duş için yeni köşe kolonu P10 (alt katlardan temele iner, çatıya çıkar, rögar R2) |
| Depo: bodrumda hidrofor, yoksa çatı | parametre: çatı | otomatik karar: cati (mimaride bodrum / depo yeri yok (Z+2, temel) -> çatı deposu kurgusu, hidroforsuz) |
| Pafta sonu lejant + adet tablosu | antet yanında sabit lejant | "LEJANT VE MALZEME LİSTESİ" paftası: sembol.otomatik_lejant (kullanılan 14 sembol türü, adetli) + armatür adet + boru metrajı |


## 1. Pis su kolonları (zemin kat)

Kolon sayısı: kullanıcı **9** (zemin 9 / 1. kat 9 / 2. kat 9 / temel 9 etiket), motor **10** (her katta aynı hizada).

| Kullanıcı | Islak hacim | Kullanıcı konum | R1 kolon / konum | R1 fark (cm) | R2 kolon / konum | R2 fark (cm) |
|---|---|---|---|---|---|---|
| P1 | mutfak | 253578, -443414 | P3 253617, -443305 | 116 | P1 253588, -443431 | 20 |
| P2 | wc-lvb. | 253735, -442737 | P2 253742, -442795 | 59 | P2 253731, -442739 | 5 |
| P3 | banyo | 253716, -442662 | P1 253862, -442622 | 151 | P3 253732, -442703 | 44 |
| P4 | mutfak | 253553, -443414 | P6 253513, -443305 | 116 | P4 253542, -443431 | 20 |
| P5 | wc-lvb. | 253394, -442737 | P5 253388, -442795 | 58 | P5 253399, -442739 | 6 |
| P6 | banyo | 253414, -442662 | P4 253268, -442622 | 152 | P6 253400, -442703 | 43 |
| P7 | mutfak | 253765, -441812 | P9 253723, -441692 | 128 | P7 253752, -441547 | 266 |
| P8 | wc+banyo | 253066, -442255 | P7 253202, -442168 | 161 | P8 253048, -442246 | 20 |
| P9 | duş | 252778, -441881 | P8 252783, -441978 | 97 | P9 252765, -441978 | 98 |


Ortalama fark: R1 **115 cm** → R2 **58 cm**. R2 numaralandırması kullanıcınınkiyle aynı (P1 D1 mutfak, P2 D1 wc-lvb, P3 D1 banyo, ... P9 duş). Kalan büyük farklar: D3 mutfak (R2 eviyeye en yakın köşe = cephe köşesi, kullanıcı tezgâh ucu salon duvarı; o duvar parçaları <100 cm olduğu için köşe adayı çıkmadı), duş (R2 tekne köşesi, kullanıcı balkon tarafı süzgeç köşesi), banyolar ~45 cm (aynı duvar, bölme duvarı ucu yerine ıslak hacim köşesi).

## 2. Islak hacim armatürleri ve yükler (zemin kat)

| Mahal | Etiket konumu | Kullanıcı armatürleri | Motorun tanıdığı (mimari) | SB kull. | SB motor R1 | MB kull. (SO+SC) | YB motor (SO+SC) |
|---|---|---|---|---|---|---|---|
| banyo | 253356,-442520 | LV/YS(2 SB, 1.5 MB), WC(10 SB, 0.5 MB), LV/YS(2 SB, 0 MB), DUŞ(7 SB, 5 MB), ÇM/EV/BM(4 SB, 1.5 MB) | WC, LV, DUS, YS, CM | 25 | 25 | 8.5 | 4.5 |
| banyo | 253802,-442561 | LV/YS(2 SB, 1.5 MB), WC(10 SB, 0.5 MB), LV/YS(2 SB, 0 MB), DUŞ(7 SB, 5 MB), ÇM/EV/BM(4 SB, 1.5 MB) | WC, LV, DUS, YS, CM | 25 | 25 | 8.5 | 4.5 |
| duş | 252827,-441927 | LV/YS(2 SB, 0 MB), LV/YS(2 SB, 1.5 MB), DUŞ(7 SB, 5 MB), LV/YS(2 SB, 0 MB) | LV, DUS, YS | 13 | 11 | 6.5 | 3 |
| mutfak | 253412,-443179 | ÇM/EV/BM(4 SB, 1.5 MB), ÇM/EV/BM(4 SB, 2 MB) | BM, EV | 8 | 8 | 3.5 | 2 |
| mutfak | 253600,-441690 | ÇM/EV/BM(4 SB, 2 MB), ÇM/EV/BM(4 SB, 1.5 MB) | EV | 8 | 4 | 3.5 | 1 |
| mutfak | 253748,-443179 | ÇM/EV/BM(4 SB, 1.5 MB), ÇM/EV/BM(4 SB, 2 MB) | BM, EV | 8 | 8 | 3.5 | 2 |
| wc+banyo | 253134,-442100 | ÇM/EV/BM(4 SB, 1.5 MB), DUŞ(7 SB, 5 MB), WC(10 SB, 0.5 MB), LV/YS(2 SB, 0 MB), LV/YS(2 SB, 1.5 MB) | WC, LV, DUS, YS | 25 | 21 | 8.5 | 3.5 |
| wc-lvb. | 253323,-442780 | WC(10 SB, 0.5 MB), LV/YS(2 SB, 1.5 MB) | LV, WC(alaturka) | 12 | 12 | 2 | 1.5 |
| wc-lvb. | 253847,-442783 | WC(10 SB, 0.5 MB), LV/YS(2 SB, 1.5 MB) | LV, WC(alaturka) | 12 | 12 | 2 | 1.5 |


R2: 3. daire mutfağına **BM (EK, 4 SB)** ve wc+banyoya **ÇM (EK, 4 SB)** eklendi → mutfak 8 SB, wc+banyo 25 SB (kullanıcıyla aynı). Kullanıcı balkon / ıslak hacim dışı **5 adet yer süzgeci** (SUZGEC1) çizmiş; R2 zemin katta **5** balkon süzgeci (ayrı yağmur hattı).

## 3. Rögarlar (temel planı)

|  | Kullanıcı | Motor R2 |
|---|---|---|
| Rögar sayısı | 4 + PB | 4 + PB |
| Cephe | doğu (x≈254520) | doğu (x≈254518) |
| R1 konumu / kolonlar | 254520, -441848 / P7, P9 | 254518, -441762 / P7, P9 |
| R2 konumu / kolonlar | 254520, -442335 / P8 | 254518, -442332 / P8, P10 |
| R3 konumu / kolonlar | 254520, -442841 / P2, P3, P5, P6 | 254518, -442721 / P3, P6, P2, P5 |
| R4 konumu / kolonlar | 254520, -443366 / P1, P4 | 254518, -443431 / P1, P4 |
| PB konumu / kolonlar | 255026, -443366 /  | 254738, -443431 /  |
| Kolon→rögar boru çapı | Ø150 x8, Ø125 x8 | hesap Ø100 (kolon başı en çok 75 SB ≤ 160); rögarlar arası Ø150 %1 |
| Şemadaki rögar blokları | 5 (MTY-ROGAR KAT) | rögar şeması: R1..R4 + PB (PVC ROGAR bloğu) |


## 4. Çap etiketleri (zemin kat planı)

### Pis su (Ø / SB)

| Etiket | Kullanıcı adet | R1 adet | R2 adet |
|---|---|---|---|
| Ø100 / 10 SB | 7 | 0 | 2 |
| Ø100 / 14 SB | 0 | 1 | 0 |
| Ø100 / 21 SB | 0 | 0 | 1 |
| Ø100 / 23 SB | 2 | 1 | 2 |
| Ø100 / 25 SB | 3 | 2 | 3 |
| Ø50 / 2 SB | 6 | 7 | 5 |
| Ø50 / 4 SB | 8 | 5 | 6 |
| Ø50 / 7 SB | 3 | 1 | 1 |
| Ø50 / 8 SB | 2 | 0 | 3 |
| Ø70 / 11 SB | 0 | 2 | 2 |
| Ø70 / 13 SB | 2 | 2 | 2 |


### Temiz su (çap / yük)

| Hat | Çap | Yük | Kullanıcı adet | R1 adet | R2 adet |
|---|---|---|---|---|---|
| sıcak | 1" | 3.25 MB | 4 | 0 | 0 |
| sıcak | 1" | 4 MB | 4 | 0 | 0 |
| sıcak | 1" | 6.5 MB | 1 | 0 | 0 |
| sıcak | 1/2" | 0.5 MB | 3 | 0 | 0 |
| sıcak | 1/2" | 0.75 MB | 2 | 0 | 0 |
| sıcak | 3/4" | 1.5 MB | 3 | 0 | 0 |
| sıcak | Ø20 | 0.5 YB | 0 | 0 | 3 |
| sıcak | Ø20 | 1.0 YB | 0 | 0 | 4 |
| sıcak | Ø20 | 1.5 YB | 0 | 0 | 2 |
| sıcak | Ø20 | 2.0 YB | 0 | 0 | 6 |
| sıcak | Ø25 | 2.5 YB | 0 | 0 | 2 |
| sıcak | Ø25 | 3.0 YB | 0 | 0 | 2 |
| sıcak | Ø25 | 3.5 YB | 0 | 0 | 1 |
| soğuk | 1 1/4" | 11.5 MB | 1 | 0 | 0 |
| soğuk | 1 1/4" | 9.5 MB | 2 | 0 | 0 |
| soğuk | 1" | 3 MB | 3 | 0 | 0 |
| soğuk | 1" | 3.25 MB | 1 | 0 | 0 |
| soğuk | 1" | 5.25 MB | 3 | 0 | 0 |
| soğuk | 1" | 6.5 MB | 4 | 0 | 0 |
| soğuk | 1" | 8.5 MB | 1 | 0 | 0 |
| soğuk | 1/2" | 0.5 MB | 3 | 0 | 0 |
| soğuk | 3/4" | 1.25 MB | 2 | 0 | 0 |
| soğuk | Ø20 | 0.5 YB | 0 | 13 | 3 |
| soğuk | Ø20 | 1.0 YB | 0 | 7 | 4 |
| soğuk | Ø20 | 1.5 YB | 0 | 0 | 1 |
| soğuk | Ø20 | 2.0 YB | 0 | 3 | 1 |
| soğuk | Ø25 | 2.5 YB | 0 | 0 | 5 |
| soğuk | Ø25 | 3.5 YB | 0 | 0 | 1 |
| soğuk | Ø25 | 4.0 YB | 0 | 0 | 5 |
| soğuk | Ø25 | 4.5 YB | 0 | 0 | 2 |
| soğuk | Ø25 | 5.0 YB | 0 | 0 | 1 |
| soğuk | Ø25 | D1 5.5 YB | 0 | 1 | 1 |
| soğuk | Ø25 | D2 5.5 YB | 0 | 1 | 1 |
| soğuk | Ø25 | D3 4.0 YB | 0 | 1 | 0 |
| soğuk | Ø25 | D3 6.0 YB | 0 | 0 | 1 |


Yöntem kararı (14.10.2026): YB ve SB yöntemi MTY ile aynı kalır, **MB / inç'e geçilmedi**. Kullanıcının bu dosyadaki çiziminde temiz su MB / inç ile yazılmış (lavabo 0,75 / duş 2,5 / çamaşır 1,5 / bulaşık 1,5 / eviye 1 MB); motor YB (gp.YB) + Ø mm. R2'de sıcak hat soğukla aynı etikette (SO üstte, SC altta) yazılır. Daire ana hattı: kullanıcı 9,5 / 9,5 / 11,5 MB (1 1/4"), R1 D1 5.5 / D2 5.5 / D3 4 YB, R2 D1 5.5 / D2 5.5 / D3 6 YB.

## 5. YB / SB toplamları

|  | Kullanıcı | R1 | R2 |
|---|---|---|---|
| Bina toplam temiz su yükü | - | 44 YB | 52 YB |
| Yağmur inişi | 9 (YB1..YB9) | 9 | 9 (+ balkon süzgeç bağlantıları) |
| Yağmur hesabı | - | P=404.5 m², D=6.56 cm → Ø100 | P=404.5 m², D=6.56 cm → Ø100 |


## 6. Pafta düzeni

| # | Kullanıcı (soldan sağa, sıhhi sıra) | Motor R2 |
|---|---|---|
| 1 | YERLEŞİM  PLANI   ÖLÇEK: 1 / 250 | ANTET, NOTLAR VE LEJANT |
| 2 | TEMEL PLANI..........ÖLÇEK: 1 / 50 | YERLEŞİM PLANI |
| 3 | ZEMİN KAT PLANI..........ÖLÇEK: 1 / 50 | TEMEL PLANI |
| 4 | 1. KAT PLANI..........ÖLÇEK: 1 / 50 | ZEMİN KAT SIHHİ TESİSAT PLANI |
| 5 | 2. KAT PLANI..........ÖLÇEK: 1 / 50 | 1. KAT SIHHİ TESİSAT PLANI |
| 6 | ÇATI PLANI..........ÖLÇEK: 1 / 50 | 2. KAT SIHHİ TESİSAT PLANI |
| 7 |  | SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI + RÖGAR ŞEMASI |
| 8 |  | YAĞMUR SUYU ŞEMASI VE HESABI |
| 9 |  | SIHHİ DETAYLAR |
| 10 |  | LEJANT VE MALZEME LİSTESİ |


## 7. Kontroller (motor)

| Kontrol | R1 | R2 |
|---|---|---|
| kolon_cakisma | 0 | 0 |
| bosta_uc | 0 | 0 |
| kopru | 14 | 36 |
| cakisik | 13 | 22 |
| yazi_maskesi | 120 | 133 |
| dedupe | 20 | 23 |
| yasak bölge (betonarme/asansör/enerji odası) ihlali | - | 0 |
| daire içine giren ana hat | - | 0 |
| kolon no balonu çizgiye biniyor (zemin) | 9 / 9 | 0 / 10 |


## 8. Açık kalanlar / kullanıcıya sorulacaklar

| Konu | Durum |
|---|---|
| Kolon–rögar çapı | Hesap Ø100 diyor, kullanıcı Ø125 çizmiş. Kullanıcı tercihi olarak Ø125'e sabitlensin mi? (PRM ile tek satır) |
| ADK / sayaç kurgusu | Çatı deposundan iki ADK kolonu (D1/D2 grubu, D3 grubu) + kat sahanlığında daire sayacı. Kullanıcının alıştığı "zemin katta toplu sayaç" tercihi mi? |
| 1. kat sağ wc-lvb → yüklük | Mimaride 1. katta bu mahal yüklük; P2 kolonu o katta armatürsüz geçer. |
| 1. kat D6 wc-duş (P10) | Kullanıcı çiziminde 1. katta 9 kolon etiketi var; motor bu wc-duş için ayrı P10 açtı (zeminde D1 banyosunun köşesinden geçer). Kullanıcı bu hacmi mevcut bir kolona (P3) yatay bağlamayı mı tercih eder? |
| D3 mutfak kolonu | Eviyeye en yakın köşe cephe köşesi seçildi (kombinin yanı); kullanıcı tezgâh ucunu (salon duvarı) seçmiş. |
| Çatı planı, WC havalandırma izometrisi, kesit/görünüşler | Bu revizyonda yapılmadı (R1'den beri eksik). |
| Etiket ölçeği | Çap/yük etiketleri ölçek 8 (kullanıcı 10); kalabalık mahallerde 10 çakışma üretir. |

