# SIHHİ TESİSAT — ALTIN REFERANS (kullanıcının kendi çizimi `ornekler/new_block.dxf`)

Tarih: 14.10.2026. Kaynak: `ornekler/new_block.dxf.xz` (AC1027, birim cm, 23,5 MB). Bütün sayılar DXF'ten ezdxf ile ÖLÇÜLDÜ
(betik: `kutuphane/arastirma/referans/sihhi/_kirp.py` kırpmaları üretir; ölçüm betikleri aynı yöntemle entity koordinatlarını okur).
Kırpılmış PNG'ler: `kutuphane/arastirma/referans/sihhi/NN_*.png` (beyaz zemin, ezdxf drawing addon; `%%C` → Ø, `%%%` → %).
Kullanıcının REDDETTİĞİ çıktılarımız: `kutuphane/arastirma/geri_bildirim/RED_sihhi_*.png` (NE YAPILMAYACAĞINI gösterir, §9).

Koordinat çerçevesi: zemin kat mimarisi penceresi x 252600…254410, y −443700…−441460 (cm). 1. kat = zemin + 2034 (x), 2. kat = +4082,
temel planı = −2629, çatı planı = +6143 (plan paftaları aynı y aralığında yan yana).

---

## 0. PNG dizini (`kutuphane/arastirma/referans/sihhi/`)

| Dosya | Bölge (x1,y1,x2,y2) | Ne gösterir |
|---|---|---|
| 01_zemin_plan_genel | 252513,−444050,254578,−441150 | Zemin kat paftası tamamı (antet hariç) |
| 02_sema_genel | 260714,−444050,268132,−441150 | Açılımlı kolon şeması paftası tamamı |
| 03_sema_sayac_grubu_sebeke | 260760,−443330,261420,−443100 | Şebeke girişi + 9'lu sayaç grubu (zemin bandı solu) |
| 04_sema_depo | 260900,−442110,261460,−441720 | Kullanım su deposu 3 m³ (şemanın sol üstü) |
| 05_sema_daire_D1_zemin | 265150,−443400,267520,−442830 | Bir daire bloğu (D1, zemin bandı): 3 ıslak hacim grubu, kombi, D etiketi |
| 06_sema_daire_D3_zemin | 261480,−443400,263420,−442830 | D3 bloğu (wc+banyo / duş / mutfak) |
| 07_sema_kolon_ust_etiketler | 261400,−442480,267520,−441900 | Kolon etiketleri P1…P9 en üstte, 2. kat bandı |
| 08_rogar_semasi | 264000,−443980,265400,−443600 | Rögar şeması R1-R2-R3-R4-PB |
| 09_yagmur_semasi | 267460,−443720,268100,−441940 | Yağmur şeması YB1…YB9 + kanal + hesap kutusu |
| 10_temel_plan_genel | 250042,−444050,252513,−441150 | Temel planı (kolon dipleri, rögarlar, Ø125/Ø150 hatlar) |
| 11_z_wcbanyo_D3_P8 | 252960,−442340,253270,−441980 | **RED-1 bölgesi**: D3 wc+banyo (D3-5-8), kolon P8, mek. havl. şaftı |
| 12_z_dus_balkon_P9_YB8 | 252600,−442090,252960,−441810 | **RED-2 bölgesi**: duş + balkon süzgeci → YB8 |
| 13_z_banyo_wclvb_D1_P2_P3 | 253590,−442880,253980,−442370 | **RED-4 bölgesi**: merdiven yanı banyo + wc-lvb (D1), P2/P3, temiz su girişi |
| 14_z_mutfak_kombi_D1_D2_P1_P4 | 253270,−443710,253890,−442990 | İki mutfak + balkondaki kombiler, P1/P4 ortak duvarda |
| 15_z_banyo_wclvb_D2_P5_P6 | 253170,−442880,253560,−442370 | D2 banyo + wc-lvb (D1'in aynası) |
| 16_z_giris_hol_D3_ana_hat | 252960,−442150,253840,−441490 | D3 antre-kor. içinden geçen ana hat, P7 mutfak, kombi |
| 17_z_balkon_suzgec_YB2_YB3 | 253000,−443700,254120,−443400 | Ön balkonlar: süzgeç → YB2 / YB3 |
| 18_cati_plan_genel | 258656,−444050,260714,−441150 | Çatı planı (havalıklar, YB çıkışları, çatı tipi fanlar) |
| 19_detay_paftasi_genel | 268132,−444050,270197,−441150 | Son pafta: WC havalandırma izometrisi + SIHHİ DETAYLAR bloğu |
| 20_antet_yerlesim | 247352,−444050,250042,−441150 | ROTAŞ anteti + yerleşim planı |
| 21_1kat_plan_genel / 24_2kat_plan_genel | kat paftaları | 1. ve 2. kat |
| 22_1kat_merdiven_yani_banyo_D4_P2_P3 | 255590,−442900,256020,−442350 | **RED-4 bölgesinin 1. kattaki hâli** (banyo 4,37 m², yüklük, P2/P3) |
| 23_1kat_wcbanyo_D5_P8 | 254994,−442340,255304,−441980 | RED-1 bölgesinin 1. kattaki hâli (D5) |
| 25_etiket_yakin_pissu_O100_23SB | 253715,−442640,253835,−442520 | Pis su etiketi kancası yakın plan |
| 26_etiket_yakin_temizsu_1inc_MB | 253030,−442090,253150,−441970 | Temiz su etiketi (4 satır) yakın plan |
| 27_kolon_no_yakin_P8_ve_kolon | 253020,−442330,253120,−442230 | Kolon sembolü + P8 balonu + kılavuz |
| 28_sema_kombi_D_etiketi_yakin | 267050,−443060,267480,−442900 | Şemada D1 balonu ve kombi yazısı |
| 29_sema_armatur_grubu_yakin_D1_banyo | 265180,−443340,265980,−442980 | Şema armatür dizisi (P3 kolonu, T.K., lavabo-klozet-süzgeç-duş-ÇM) |
| 30_sema_kolon_dibi_TK_rogar_yakin | 266850,−443400,267020,−443180 | Kolon dibi: T.K., dirsek, "R" rögar |
| 31_1kat_D4_giris_ve_temizsu_hol | 255600,−443200,256300,−442350 | 1. kat daire girişi + holdeki temiz su çifti |

---

## 1. Pafta düzeni (model uzayı, ANTED katmanındaki düşey ayraç çizgileri)

Pafta yüksekliği: y −444050 … −441150 = **2900 cm** (1/50 → 580 mm). Düşey ayraçlar (x):

| Pafta | x aralığı | Genişlik (cm) | İçerik |
|---|---|---|---|
| Antet | 247352…248310 (çerçeve 247352…248310 × −444050…−442622, iç çerçeve 9 cm içeride) | 958 × 1428 | ROTAŞ anteti **yalnız alt yarıda** (satır çizgileri y: −444041, −444002, −443948, −443915, −443860, −443804, −443776, −443771, −443725, −443720, −443530, −443170, −443030, −442631) |
| Yerleşim | 248360…250042 | 1682 | "YERLEŞİM PLANI ÖLÇEK: 1 / 250" (h 40) |
| Temel | 250042…252513 | 2471 | "TEMEL PLANI..........ÖLÇEK: 1 / 50" |
| Zemin | 252513…254578 | 2065 | mimari pencere 252600…254410 → sol boşluk 87, sağ 168; alt boşluk 350, üst 310 |
| 1. kat | 254578…256617 | 2039 | |
| 2. kat | 256617…258656 | 2039 | |
| Çatı | 258656…260714 | 2058 | |
| Kolon şeması | 260714…268132 | **7418** | şema + rögar şeması + yağmur şeması |
| Detay | 268132…270197 | 2065 | WC havalandırma izometrisi (üst) + SIHHİ DETAYLAR bloğu (alt, 1998,6 × 1500, sol kenar 268157) |
| ISITMA sırası | 272590… | | aynı düzen |

- Plan başlığı MTEXT h **40**, x = pafta solu + 538, y = −444011 (alt çerçeveden 39 yukarı), biçim `ZEMİN KAT PLANI..........ÖLÇEK: 1 / 50`.
- Antet yazıları: "ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK" h 30 (247686, −443558); logo "R" h 63 (GOR2, 247535,−443571); "SIHHİ TESİSAT PROJESİ" h 25 (YAZI katmanı, times.ttf, 247607,−443733); adres/telefon h 9,7–11,3.

---

## 2. Katmanlar, renkler, çizgi tipleri, kalınlıklar (DXF LAYER tablosu)

| Katman | Renk (ACI) | Çizgi tipi (LTSCALE 1, entity ltscale **50**) | lw | Kullanım |
|---|---|---|---|---|
| MTY-PISSU-BORU-TAVANDAN | 6 (magenta) | PISSU HATTI (desen 0,9 → ×50 = 45 cm: 25 çizgi + "(" sembolü) | 30 | planda ve temel planında pis su hatları (LWPOLYLINE, genişlik 0) |
| MTY-PISSU-CAP | 211 (açık mor) | CONTINUOUS | 30 | Ø/SB etiket bloğu `MTY-PIS SU CAP SB` |
| MTY-YUK-BIRIMI | 7 | CONTINUOUS | | etiket içindeki "n SB" / "n MB" yazısı (öznitelik rengi 211 pis, 101 temiz) |
| MTY-PISSU-KOLONNO / MTY-KOLLETÖR | 211 / 7 | | | kolon balonu çizgileri / "P8" yazısı (renk 6) |
| STM-PISSU-KOLON | 211 | DASHED | | kolon sembolü (içi dolu daire r 10) |
| MTY-SOGUKSU-BORU | 5 (mavi) | (sürekli) | 30 | soğuk su; LWPOLYLINE/LINE genişlik 0 |
| MTY-SICAKSU-BORU | 1 (kırmızı) | BASMA HATTI (0,375 → ×50 = 18,75 cm: 12,5 çizgi + 6,25 boşluk) | 30 | sıcak su |
| MTY-TEMIZSU-CAP | 101 (yeşil) | CONTINUOUS | 30 | inç/MB etiket bloğu `MTY-TEMIZ SU CAP MB` |
| MTY-YAGMUR-BORUSU | 3 (yeşil) | YAGMUR HATTI (0,9 → 45 cm, "(((" sembolü) | 30 | balkon süzgeci → yağmur inişi, şemada YB hatları |
| MTY-YAGMURSU-KOLON NO | 3 | | | YB balonları |
| MTY-VANA | 1 | CONTINUOUS | 30 | bütün armatür/vana/kolon blokları (INSERT) |
| MTY-TEFRIS | 15 | | | armatür görünüş çizgileri (blok içi) |
| MTY-PVC | 43 | | | şemadaki PVC boru/çatal/dirsek çizgileri (blok içi) |
| MTY-ROGAR | 5 | | | rögar bloğu çizgileri, yağmur kanalı |
| MTY-BORU | 7 | | 0 | şema kat bantları (çerçeve) ve "ZEMİN. KAT" yazısı (renk 1, h 25, rot 90) |
| MTY-HESAP | 1 | | 20 | yağmur hesabı kutusu |
| TEM.SU | 5 | | 35 | şebeke–sayaç–depo hatları (şema) |
| M-ANNO-TEXT | 41 (turuncu) | | 9 | "Wc Aspiratörü / 160 m3/h-50 pa / Ø150 mm" (h 15, stil Arial_23) |
| MKDU0 | 50 | | | mimari (patlatılmış, tek katman) |
| ANTED / çizgi / YAZI / GOR2 / TARAMA | 144 / 7 / 7 / 2 / 4 | | | pafta ayraçları, antet |

Yazı stilleri: etiketler `MTY_CAP` (wturkce.SHX, genişlik 0,65); kolon balonu `ANOTATIVO`/`MENFEZ` (arial / romanstw); aspiratör `Arial_23` (arial, genişlik 0,8).

---

## 3. Kat planı — PİS SU (zemin kat ölçümleri)

### 3.1 Kolon (P) konumları ve duvara mesafe
Kolon = dinamik blok (`MTY-BORU KOLON PİS SU` türevi, MTY-VANA katmanı) yerleştirme noktası; içinde STM-PISSU-KOLON katmanında **içi dolu daire r = 10 cm (Ø20)**. Pis su polyline'ı kolon noktasından 7–8 cm içeride başlar.

| Kolon | Islak hacim | Konum (x, y) | En yakın duvar çizgisine mesafe | Yeri |
|---|---|---|---|---|
| P1 | D1 mutfak | 253577,6 −443414,3 | 0,6 | iki mutfağın ORTAK duvarı, tezgâh ucu (P4 ile 24,7 cm arayla aynı duvar) |
| P4 | D2 mutfak | 253552,9 −443414,3 | 0,6 | aynı |
| P2 | D1 wc-lvb. | 253735,2 −442736,9 | 8,7 | wc-lvb üst-sol köşesi, mek. havl. şaftının yanı, merdiven duvarı |
| P3 | D1 banyo | 253716,4 −442662,3 | 1,2 | banyo sol duvarı (merdiven tarafı), alt köşeden 48 yukarı; P2 ile 77 cm arayla aynı duvar |
| P5 / P6 | D2 wc-lvb / banyo | 253393,7 −442736,9 / 253414,1 −442662,3 | 8,2 / 1,2 | D1'in aynası |
| P7 | D3 mutfak | 253765,1 −441812,4 | 0,1 | mutfak köşesi (salon duvarı) |
| P8 | D3 wc+banyo | 253066,4 −442254,8 | 1,0 | wc+banyo alt-sol köşesi, "mek. havl." nişinin yanında |
| P9 | D3 duş | 252778,2 −441881,0 | 2,8 | duş üst-sol köşesi, S03 betonarme kolonunun yanı |

→ Kural: kolon merkezi duvar yüzü çizgisinden **≤ 9 cm** (fiilen duvar içinde/yüzünde), ıslak hacmin bir **köşesinde**; iki ıslak hacim bitişikse iki kolon aynı duvarda 25–77 cm arayla.

Kolon balonu: blok `MTY-KOLON NO PIS SU`: çift daire **r 27,5 / r 24,5**, "P8" yazısı h **20** (renk 6 mor, daire kırmızı). Balon merkezi kolona göre ofset: P1 (+26, −53), P2 (−94, +16), P3 (−75, +9), P4 (−26, −76), P5 (+96, −13), P6 (+75, −13), P7 (+48, −11), P8 (−11, −48), P9 (+49, +88) → **49–101 cm**, daima ıslak hacmin DIŞINDA (merdiven, hol, balkon, salon) ve kolondan balona ince kılavuz çizgisi (PNG 27).

### 3.2 Hat topolojisi: "OMURGA + DİK KISA BRANŞMAN"
Her ıslak hacimde kolondan en uzak armatüre kadar **tek doğru omurga** (düz, eğik olabilir), armatürler omurgaya **dik** kısa branşmanla bağlanır; her branşman omurgadan **7,07 cm'lik 45° parça** (5×5) ile ayrılır, sonra omurgaya dik düz gider (PNG 11, 13, 25).

| Islak hacim | Omurga açısı | Omurga parçaları (cm) | Omurga toplam | Branşmanlar (45° 7,07 + dik parça) | Omurganın duvara mesafesi |
|---|---|---|---|---|---|
| D3 wc+banyo (P8) | 68,8° | 31,6 + 39,9 + 78,0 + 67,8 + 19,8 | 237 | ÇM 18,0; duş 100,3; WC 57,7; süzgeç 64,3 | 0–60 (oda içinden çapraz) |
| D1 banyo (P3) | 60,8° | 44,0 + 106,5 + 51,1 + 19,0 + 37,6 | 258 | lavabo 15,6; WC 23,3 (45° parçayla doğrudan); süzgeç 36,1; duş/ÇM 85,1 | 6–67 |
| D1 wc-lvb (P2) | 74,1° / 0° | 68,3 (lavabo) ; 49,8 (hela) | 118 | hela 5,5; lavabo 15 | 0–20 |
| D1 mutfak (P1) | 90° (duvar dibi) | 130,5 + 126,9 | 257 | eviye 2,7; BM 4,7 | 1–7 |
| D3 mutfak (P7) | 0° / 90° | 115,4 + 136,6 | 252 | eviye 30,4; BM 1,9 | 0–17 |
| D3 duş (P9) | 90° + 0° | 91,0 + (7,07 45°) + 21,9 + 35,1 + 29,7 | 185 | lavabo 17,1; süzgeç 6,9; duş 4,1 | 2–5 (duvar dibi) |

Açı histogramı (zemin, 78 parça): 0/90° = 22, 45/135° = 14, diğer eğik (60,8°, 68,8°, 74°, 119°, 150°, 158°) = 42 → **omurga eğik olabilir; branşman omurgaya göre 45° + 90°**. Banyoda omurga odanın ortasından çapraz geçer (duvara 67 cm'e kadar). Pis su – pis su kesişmesi: **0** (üç katta).

Etiket adetleri: zemin 33, 1. kat 24, 2. kat 33 pis su etiketi; her parça (omurga parçası ve branşman) etiketli.

### 3.3 Ø / SB etiketi (`MTY-PIS SU CAP SB`, ölçek 10)
- Blok geometrisi (birim ×10): kanca = pipe'a **dik 11,7 cm** + hatta paralel **8,3 cm**; "Ø50" kancanın üst tarafında, "2 SB" alt tarafında; öznitelik yüksekliği **10**, stil MTY_CAP, sol hizalı.
- Yerleştirme noktası **hattın üzerinde (mesafe 0,0)**, parçanın **ortasında (oran 0,50; branşmanlarda 0,26–0,58)**; döndürme = hat açısı (okunur olsun diye 180° çevrilmiş/x'te aynalanmış olabilir: sx = ±10). Zeminde 33/33 etiket bu kurala uyar.
- Biçim: `Ø50 / 2 SB`, `Ø70 / 13 SB`, `Ø100 / 25 SB`. Yükler: lavabo 2, klozet 10, duş 7, süzgeç 2, ÇM 4, BM 4, eviye 4 SB. Çap: ≤8 SB Ø50 (tek klozet Ø100), 11–13 SB Ø70, ≥21 SB Ø100; kolon→rögar Ø125, rögarlar arası Ø150.
- Etiketler mahal adı/m² yazısına yer yer değer (PNG 25: "23 SB" ile "banyo"), ama **etiket etiket üstüne hiç binmez**.

### 3.4 Islak hacim süzgeci ve balkon süzgeci
- Islak hacim süzgeci (SUZGEC1, 2 SB Ø50) duvar dibinde (0,8–11 cm), omurgaya 45°+dik branşmanla bağlı; mutfakta süzgeç YOK (kullanıcı çizimi).
- **Balkon süzgeci yalnız yağmur inişine**: SUZGEC1 ↔ YB mesafesi **26–34 cm** (YB2 33, YB3 34, YB5 34, YB6 26, YB8 31, YB9 31); bağlantı `MTY-YAGMUR-BORUSU` yeşil polyline **11,6–33,5 cm** (PNG 12, 17). Süzgeç duvardan 6–10 cm.
- Yağmur inişi (YB) cephe köşesinde, duvara 0,1–1 cm; balonu (`MTY-KOLON NO YAGMUR`, r 27,5, h 20, yeşil) inişten 28–75 cm dışarıda (bina dışı).

---

## 4. Kat planı — TEMİZ SU (zemin)

- Soğuk (mavi, sürekli) ve sıcak (kırmızı BASMA HATTI) **5,0 cm paralel** (ölçülen çiftler: x 253808/253813, y −442878/−442873, −442787/−442792, x 253671/253666).
- Sıcak su **daire içinden, kombiden başlar**: D1/D2 kombi balkonda (253588,−443641 → mutfak → hol → wc-lvb → banyo), D3 kombi mutfak nişinde (253770,−441569). Sıcak hat dallanır (klozet/ÇM/BM hariç her armatüre); kombi etiketi `1/2" 0,5 MB` (Ø20).
- Güzergâh **duvar dibinden DEĞİL, mahal ortasından**: D1 mutfak düşey hattı x 253671 = mutfak genişliğinin tam ortası (366/2 = 183); banyo düşey hattı x 253808 = sol duvara 100, sağ duvara 66; antre-kor. boyunca duvara 13–61; D3 holünde 490 cm'lik ana hat duvara 29–53. Ölçülen duvar mesafesi histogramı: mutfak 17–30, banyo 23–64, hol 13–61, wc-lvb 0–27.
- Armatür branşmanları çiftten **dik** ayrılır; branşman ucunda armatüre 5 cm'lik son parça + küresel vana sembolü (blok içinde).
- **Daire girişi**: soğuk ana hat merdiven holündeki daire kapısının hemen yanında başlar (r 2 cm daire işareti: D1 253616,8 −443000,4; D2 253513,7 −443000,4; D3 253601,6 −442069,7), etiket `1 1/4" / 9,5 MB` (D1/D2), `1 1/4" / 11,5 MB` (D3). Planda **sayaç yok** (sayaçlar şemada zemin bandında). Ana hat kapıdan hol ortasına girip (D1: 120 cm düşey, 203 cm yatay) ıslak hacimlere dağılır.
- Kesişmeler (zemin, ölçüldü): soğuk×soğuk **0**, sıcak×sıcak **0**, **soğuk×sıcak 27** (çiftten ayrılan dik branşman, eşinin hattını köprüsüz keser — kullanıcı bunu KABUL eder), pis×soğuk 22, pis×sıcak 15 (farklı düzlem, işaret yok). **Köprü/atlatma sembolü hiç yok.**
- Toplam boy (zemin): soğuk 79,2 m, sıcak 61,3 m, pis su 27,9 m.

### 4.1 inç / MB etiketi (`MTY-TEMIZ SU CAP MB`, ölçek 10)
- Kanca: hatta dik **31 cm** + paralel 8,3; dört satır (yukarıdan): `1"` (soğuk çap), `5.25 MB` (soğuk yük), `1"` (sıcak çap), `3.25 MB` (sıcak yük); satır aralığı 15; yazı h **10**, renk yeşil (101), stil MTY_CAP.
- Yerleştirme noktası hattın üzerinde (mesafe 0,0), **döndürme daima 0 veya 180 (yazı yatay)**, hat düşey olsa bile. Parça üzerindeki konum 0,05–0,84 (etiket boş yere kaydırılır). Yalnız soğuk hatta (klozet, ÇM, BM, daire girişi) 2 satır: `3/4" / 1.25 MB`.
- Zeminde 20 temiz su etiketi; her ıslak hacme giren çift için 1, daire girişi için 1, kombi için 1.
- Çap tablosu (kullanıcı): 0,5–0,75 MB 1/2"; 1,25–2,5 MB 3/4"; 3–8,5 MB 1"; 9,5–11,5 MB 1 1/4". Armatür MB: lavabo 0,75/0,75, duş 2,5/2,5, klozet 0,5 (S), ÇM 1,5 (S), BM 1,5 (S), eviye 1/1, kombi 0,5/0,5.

---

## 5. AÇILIMLI KOLON ŞEMASI (pafta 260714…268132)

### 5.1 Bant düzeni (MTY-BORU polyline'ları)
- Kat bandı: x 260820…267449 (**6629 cm** iç genişlik), yükseklik **400 cm/kat**: zemin −443249…−442849, 1. kat −442849…−442449, 2. kat −442449…−442049. Sol ve sağ kenarda 50 cm'lik etiket kutuları (260770…260820; 267449…267499); yağmur şeması bölmesi sağda 267499…268070 (571 cm), aynı kat çizgileriyle.
- Kat yazısı "ZEMİN. KAT / 1. KAT / 2. KAT" h **25**, rot 90, kırmızı, x = 260808 (sol kutu ortası) ve 267486 (sağ kutu), y = bant altı + 52.
- **Kat döşeme çizgisi = bant alt çizgisi**; armatür blokları bu çizgiye oturur (zemin y −443248,7).

### 5.2 Daire bloğu (PNG 05, 06, 29)
- Daire içindeki armatürler tek sırada, **merkezden merkeze 130 cm** (ör. D1 zemin: kombi 267348,6; eviye 267218,6; BM 267088,6; kolon-kat ucu 266958,6 (P1 kolonu 266934,6 + 24); lavabo 266832; klozet 266702; kolon ucu 266572 (P2 + 24); … banyo grubu: ÇM 265927,5; duş 265797,5; süzgeç 265667,5; klozet 265537,5; lavabo 265407,5; kolon ucu 265277,5 (P3 265253,6 + 24)).
- Her ıslak hacim grubu kendi kolonuna gider; grubun son armatürü ile kolon ekseni arası **154 cm**; grup kolonun SAĞINDA, pis su yatay toplayıcı soldan sağa.
- Sıra (kolona göre dıştan içe): mutfak **kombi – eviye – BM**; wc **lavabo – klozet**; banyo **ÇM – duş – süzgeç – klozet – lavabo**. Yani kolona en yakın armatür lavabo (wc/banyo) veya BM (mutfak).
- Pis su yatay toplayıcı (PVC BORU SAG / PVC CATAL SAG blokları) döşeme çizgisinin **50 cm altında** (y −443298,7); her armatürden 47 cm'lik düşey iniş + çatal (PVC CATAL SAG, 27×55); toplayıcı etiketi `Ø100 / 25 SB` (MTY-PIS SU CAP SB, ölçek 10) toplayıcı üzerinde, **x = armatür − 80** (iki armatür arasında), y −443298,7; armatür iniş etiketi (`Ø50 / 2 SB`) blok özniteliği, inişin sağında.
- Kolon (PVC BORU INIS SAG, 70 × 445): kolon ekseninde düşey çift çizgi; **T.K.** (temizleme kapağı, `MTY-TEMIZLEME KAPAGI KOLON`, 40×22) zemin döşemesinin 24 cm üstünde (y −443224,9); kolon döşemenin 77 cm altında PVC DIRSEK (−443326,3) ile yatay dönüp 20 cm sağda **"R"** (PVC ROGAR, öznitelik h 20, y −443346,4) ile biter (PNG 30). Kolon etiketi (`Ø100 / 46 SB`, kolon toplamı; öznitelik h **15**) kolon bloğunun özniteliği, kat içinde kolonun solunda düşey; armatür iniş etiketleri (`Ø50 / 2 SB`) de h 15. T.K. yazısı h 10 (kırmızı).
- Kolon üst ucu: en üst banttan **73 cm yukarıda** balon (`MTY-KOLON NO PIS SU`, r 27,5, h 20, x = kolon ekseni, y −441975,8); kolon çizgisi balon altına değer (−442003). 9 kolon x: P9 261562,6; P8 262184,6; P7 262914,1; P6 263522,2; P5 264272,5; P4 264659,0; P3 265253,6; P2 266548,1; P1 266934,6 (planın soldan sağa sırası: D3, D2, D1).
- Temiz su: daire ana hattı (riser) daire bloğunun **sol ucunda** döşemeden **250 cm** yukarı (x D1 265211,6; D2 263480,3; D3 261524,9), etiketi `1 1/4" / 9,5 MB` düşey hat üzerinde yatay; y −442998,7'de yatay ana hat bloğun sağ ucuna (kombiye) kadar; her ıslak hacim grubu için kolon-ucu hizasından (x = kolon + 24) **120 cm aşağı inip** döşemeden **130 cm** yükseklikte (y −443118,7) armatürler üzerinden yatay dağıtım; armatür branşmanları bu hattan aşağı. Sıcak hat **5 cm içeriden paralel** (y −443113,7 / −443003,7, x +5), kombiden başlar (267333,6).
- Temiz su etiketleri (`MTY-TEMIZ SU CAP MB`, ölçek 10) dağıtım hattı üzerinde, **x = armatür − 80**, kanca yukarı, 4 satır yukarıda (PNG 29): `1" 5.25 MB / 1" 3.25 MB`. Armatür YB etiketleri (`Ø20 0.75 YB`) blok özniteliği, musluk altında.
- **D balonu**: `MTY-KOLON NO PIS SU` ölçek **2** (r 55, yazı h 40, mor), x = kombiden **197 cm solda** (267151,3), y = döşemeden **268 yukarı** (−442981,1; bant üstünden 132 aşağı). Kombi yazısı MTEXT h 5 "DUVARA ASILABİLEN HERMETİK KOMBİ KAPASİTE : 24 kw" (267366, −442962) kombi sembolünün (TERMOSIFON1 KOLON türevi, 73×268) üstünde. D etiketleri: D1/D2/D3 zemin, D4/D5/D6 1. kat, D7/D8/D9 2. kat (soldan sağa D3-D2-D1 blok sırası).
- Blok genişlikleri (riser → kombi): D1 ≈ 2140, D2 ≈ 1600, D3 ≈ 1800; bloklar arası boşluk ≈ 140.

### 5.3 Şebeke + SAYAÇ GRUBU (zemin bandı SOLU, PNG 03)
- "Sebekeden" (MTY-TEFRIS, h 16,6, x 260832, y −443287 = döşemenin 38 altı); şebeke hattı (TEM.SU, mavi) y **−443233,8** (döşemeden 15 yukarı), x 260837,7 → 261153,6; üzerinde sırayla küresel vana (260856) – pislik tutucu (260881,6) – çek valf (260907,3) – küresel vana (260932,3) – çek valf (260961,3), hepsi **DN25**, aralık **25 cm**.
- Sayaç grubu: iki kolon; 1. kolon x 260992,8…261140,8, **5 satır** y −443137, −443157, −443177, −443197, −443217 (**20 cm aralık**); 2. kolon x 261153,6…261301,6, 4 satır (−443157…−443217). Her satır (uzunluk 148): küresel vana (+26,8) – pislik tutucu (+51,8) – **su sayacı** (+73,8) – çek valf (+95,8) – küresel vana (+120,8); satır sonu kolektör düşeyine 5'er cm'lik çentikle. Toplam 9 sayaç = 9 daire. Daire hatları sayaçtan sonra çizilmez (örtük).
- Sayaç grubu bant içinde döşemenin 32–112 cm üstünde, ilk daire bloğundan (D3 riser 261524,9) **220 cm solda**. **Kapı önünde/kat bandında sayaç YOK.**

### 5.4 DEPO (şemanın sol üstü, PNG 04)
- "KULLANIM SU DEPOSU V=3m3" (h 15); depo kutusu **200 × 200** (261104,8…261304,8 × −442018,7…−441818,7), altında taralı betonarme kaide **215 × 30**; sol üstte 2" havalık+taşma (kaz boynu), solda "Boşaltma" (vana + huni), sağda "Su Seviye Göstergesi".
- Doldurma: şebeke hattından (y −443233,8) x **260945,1**'de düşey yukarı (TEM.SU) depo üstünün 62 cm üstüne (−441756,1), sağa x 261257,4, aşağı depoya (küresel vana rot 90, −441781; şamandıra). Depo çıkışı: alt sağ flanştan (261260) aşağı −442036 → sağa (küresel vana 261346, pislik tutucu 261371) x 261405 → aşağı −442082 → sola x **260977,7** → düşey aşağı şebeke/sayaç hattına. İki düşeyde her katta akış okları (SOLID üçgen; doldurma ↑, dağıtım ↓).
- Yani: depo çatıda, şebeke → depo → sayaç grubu; hidrofor YOK (bodrum yok).

### 5.5 RÖGAR ŞEMASI (şemanın altında, PNG 08)
- Rögar bloğu `MTY-ROGAR KAT` (89 × 90): üst kare 89 × 48,5 içinde "R1" (mavi, öznitelik h 31,5), altında 73 × 32,5 küçük dikdörtgen; y −443875,6 (zemin döşemesinin 627 altı), x **R1 264122,7 → R2 264361,8 → R3 264600,8 → R4 264839,8 → PB 265078,9 (aralık 239)**.
- Rögarlar arası boru `MTY-PISSU-BORU-TAVANDAN` y −443831 (rögar üstünün 44 üstü), uzunluk 150; etiketi dinamik `MTY-EGIM YAZISI` (*U67) "Ø150 / % 1 EĞİM" (iki öznitelik h 20, sarı) + akış oku (SOLID), ortada, borunun 29 cm üstünde.
- Her rögarın üstünde 50 cm'lik düşey kılavuz (−443786…−443736), üstünde ona bağlanan kolonların balonları (r 27,5, h 20): yan yana **55 cm** aralıkla, 2'den fazlaysa 2. satır 55 yukarı (R3: P2 P3 / P5 P6). Dağılım: R1 ← P7,P9; R2 ← P8; R3 ← P2,P3,P5,P6; R4 ← P1,P4; PB.
- "70x70 / h:-70cm" MTEXT h 9,6 (renk 8) her rögarın sağ altında (x +185, y −443912); PB "80x80 / h:-80cm".

### 5.6 YAĞMUR ŞEMASI (şemanın sağında, PNG 09)
- 9 düşey yeşil hat x = 267534,8 + 60·i (**60 cm aralık**), y −443268,7 (zemin döşemesinin 20 altı) … −442038,7; üstte balon `MTY-KOLON NO YAGMUR` (r 27,5, h 20, yeşil) y −442011,2 (2. kat bant üstünün 38 üstü).
- Her katta hat üzerinde kat branşmanı sembolü + `Ø70` (MTY-YAĞMUR SUYU CAP türevi, ölçek 13,9) y = döşeme + 170 (−443078,2 / −442678,2 / −442278,2).
- Her hattın alt ucunda 18 × 24 cm'lik deşarj ok sembolü (MTY-ROGAR katmanı, y −443290…−443266); kanal çizgisi yok; "YAĞMUR SUYU KANALINA GİDER" MTEXT h 19,9 (267524, −443352) etrafında çerçeve 549 × 66 (267485…268034 × −443372…−443306).
- Kırmızı çerçeveli **"YAĞMUR SUYU BORU ÇAPI HESABI"** kutusu (MTY-HESAP, lw 20) 267517…268017 × −443690…−443410 (**500 × 280**), MTEXT h 10, son satırı "Ø70 lik Boru UYGUNDUR."

---

## 6. TEMEL PLANI (pafta 250042…252513, PNG 10)
- Bina dış hattı + betonarme kolonlar (mimari); kolon dipleri plandaki konumda, aynı dinamik blokla P1…P9 balonlu (balon ofseti plandaki gibi).
- Rögarlar **doğu cephesinde, bina dışına 110 cm** (x 251890,9; cephe x ≈ 251781): R1 y −441847,9; R2 −442334,6; R3 −442841,4; R4 −443366,5 (aralıklar 487 / 507 / 525); PB R4'ün 506 sağında (252396,8). Rögar çizimi: `MTY-ROGAR KAT` rot 180 + iki iç içe dikdörtgen 89×48,5 ve 73×32,5; yazı "70x70 h:-70cm" h 9,6 rögarın sağ üstünde (x +185, y +37…−101).
- Rögarlar arası düşey hat x 251891 (rögar ekseni), `Ø150 / % 1 EĞİM` etiketi hattın 34 cm sağında (rot 90).
- Kolon → rögar hatları **Ø125 / %1 EĞİM**: yatay hat rögar kutusunun sol kenarından (251846) kolona kadar; iki kolon aynı hatta (P2+P3: y −442886 → x 251093'te yukarı −442662; P1+P4: y −443411). Köşelerde **5 cm'lik 45° pah** ((250785,−442886)→(250780,−442881)). Etiket (*U67) hattın 29–34 cm altında/yanında, yatay hatlar için rot 0.
- Hat uzunlukları: R4 hattı 926 + 417 (PB), R3 hattı 748 + 313, R2 hattı 1404, R1 hattı 1694.

## 7. ÇATI PLANI ve DETAY PAFTASI
- Çatı: P1…P9 havalık uçları (aynı blok, P balonları) ve YB1…YB9 başlangıçları + 3 adet "Çatı Tipi Fan / Ø150 mm" (M-ANNO-TEXT h 15) şaft konumlarında.
- Detay paftası: üstte WC havalandırma izometrisi (M-HVAC-DUCT çizgileri, 268309…268950 × −442458…−441257; "Wc Aspiratörü 80 m3/h-50 pa Ø150 mm" ×3 kat, "MEKANİK HAVALANDIRMA 240 m³/h" D3-5-8 şaftı, "480 m³/h" D1-2-4-6-7-9 şaftı; kanal "150x150", "Çatı Tipi Fan"), altta `MTY-SIHHİ DETAYLAR` → `SIHHİ DETAYLAR` bloğu (1998,6 × 1500; sol alt 268157,4, −444026,6): TS 1258 çap tablosu, SB/YB tabloları, lejant, hela/havalık/süzgeç/eviye montaj detayları.
- Planda penceresiz ıslak hacimlerde "Wc Aspiratörü / 160 m3/h-50 pa / Ø150 mm" (3 satır, h 15, turuncu, satır aralığı 20) mahal içinde boş alanda; "mek. havl." nişi mimaride.

## 8. Diğer semboller / adetler (zemin)
- Her ıslak hacim armatür bloğu (KLOZET1, LAVABO1, DUS TEKNESI1, EVIYE1, BULASIK/CAMASIR MAKINASI1, SUZGEC1, 1-2 MUSLUK1) MTY-VANA katmanında, ölçek 1, armatürün üstüne; içinde gizli SB/MB öznitelikleri (h 2,5) ve küresel vana görünüşü. Kombi: `TERMOSIFON1`/dinamik blok + MTEXT h 5.
- ÇM "C'M'" / BM "B'M'" yazıları mimaride (MKDU0, koyu kırmızı). Zeminde 9 P kolonu, 9 YB, 10 SUZGEC1 (6 balkon: YB2/3/5/6/8/9 yanı + 4 ıslak hacim: wc+banyo, iki banyo, duş; wc-lvb ve mutfakta süzgeç yok), 3 kombi.

---

## 9. RED görüntüleri ↔ kullanıcı çizimi (aynı bölge)

| RED dosyası | Bizim hata | Kullanıcının aynı yerdeki çizimi (PNG) |
|---|---|---|
| RED_sihhi_wcbanyo_capraz_pissu_etiket_ust_uste | D3 wc+banyo: odayı çaprazlayan kalın 45° pis su, "Y.S. Ø50 (EK)", etiketler üst üste (Ø20 1.5 YB … 10'dan fazla), kalın mavi/kırmızı duvar boyu dolaşım, aspiratör yazısı hatların üstünde | PNG 11: P8 köşede, ince omurga 68,8° ile lavaboya, 4 dik branşman (18–100 cm), 7 etiket (her parça 1), hatlar ince (lw 30), temiz su çifti oda ortasından 5 cm paralel, aspiratör yazısı boş alanda |
| RED_sihhi_balkon_suzgeci_banyo_kolonuna_bagli | balkon süzgeci duştan pis su hattına; yeşil hat "yağmur inişi" yazılı ama süzgeç kolona | PNG 12 / 17: süzgeç inişin 26–34 cm yanında, 12–34 cm'lik yeşil hatla YB'ye; duşun pis suyu P9'a duvar dibinden |
| RED_sihhi_sicak_su_daire_disindan | merdiven holünden kalın kırmızı sıcak hat, banyoyu çaprazlayan kalın mor hat, P10 | PNG 13 / 22 / 31: sıcak+soğuk çifti daire holünden (K2 kapısı tarafı) banyoya girer, kombiden gelir; pis su omurgası + dik branşman; 9 kolon |
| RED_sihhi_kolon_semasi_sayac_kapida_yanlis_tarz | "D6 SAYAÇ (KAPIDA)" kat bandında, kalın mor kolonlar, internet tarzı şema, rögar şeması başlığı | PNG 02 / 03 / 05: sayaçlar zemin bandının solunda 9'lu grup, depo sol üstte, D balonu r 55, armatürler 130 aralıkla, toplayıcı döşemenin 50 altında, kolon balonları üstte 73 yukarıda |

---

## 10. MOTOR İÇİN KURAL LİSTESİ (test edilebilir; birim cm; tolerans belirtilmedikçe ±10 %)

**Katman / stil**
1. Katman adları ROTAS- önekli; renk/çizgi tipi/lw: pis su 6 / dash+"(" deseni (45 cm periyot) / 30; soğuk 5 / sürekli / 30; sıcak 1 / kesikli (12,5+6,25) / 30; yağmur 3 / 30; etiket pis 211, temiz 101; kolon balonu dairesi kırmızı, yazısı mor (pis) / yeşil (YB). Polyline genişliği 0 (kalınlık lw'den).
2. Yazı yükseklikleri: Ø/SB ve inç/MB etiketi **10**; kolon balonu yazısı **20**, daire r 27,5 (+ iç daire 24,5); D balonu r 55 / h 40; mahal aspiratör notu 15; şema kat yazısı 25; plan başlığı 40; kolon toplamı/şema etiketleri 10.

**Pis su (plan)**
3. Kolon ıslak hacim köşesinde, merkezi duvar yüzüne ≤ 9 cm; bitişik iki ıslak hacim aynı duvarda 25–80 cm arayla; balon ıslak hacmin dışında, kolondan 45–105 cm, kılavuz çizgili; balon hiçbir çizgi/yazıya binmez.
4. Her ıslak hacimde tek düz omurga (kolon → en uzak armatür; eğik olabilir, 150–260 cm), diğer armatürler omurgaya **7,07 cm 45° + dik** branşmanla (3–100 cm); zincir/seri bağlantı yok; pis su parçaları birbirini kesmez (0).
5. Mutfakta omurga tezgâh duvarı dibinde (duvara ≤ 7), branşmanlar ≤ 5; duşta duvar dibinden (≤ 5).
6. Her omurga parçası ve her branşman etiketli: etiket hattın ÜZERİNDE (mesafe 0), parça ortasında, hat yönünde döndürülmüş, kanca 11,7 + 8,3; biçim `Ø50 / 2 SB`; etiket-etiket çakışması 0; aynı parçaya tek etiket.
7. Çap: ≤ 8 SB Ø50; klozet branşmanı Ø100; 11–16 SB Ø70; ≥ 21 SB Ø100; kolon→rögar Ø125 %1; rögar-rögar Ø150 %1. Yükler: LV 2, WC 10, DUŞ 7, YS 2, ÇM 4, BM 4, EV 4 SB.
8. Balkon süzgeci: yalnız balkondaki yağmur inişine, süzgeç inişten ≤ 35 cm, hat ≤ 35 cm, yeşil; pis su ağına temas 0. Islak hacim süzgeci duvar dibinde (≤ 11), omurgaya branşmanlı.

**Temiz su (plan)**
9. Soğuk+sıcak çifti **5 cm** paralel, aynı güzergâh; sıcak kombiden/termosifondan daire içinde başlar; daire dışından sıcak su 0 m.
10. Hatlar mahal ortasından: ıslak hacim ve mutfakta düşey/yatay ana parça duvara ≥ 15 cm (ölçülen 17–64); koridorda ≥ 13; duvar dibi (< 10) yalnız giriş/çıkış parçalarında.
11. Daire girişi: merdiven holündeki daire kapısının yanında başlangıç işareti (r 2) + `1 1/4" / n MB` etiketi; planda sayaç çizilmez.
12. Branşmanlar çiftten dik ayrılır; branşmanın eş hattı kesmesi serbest (köprü/jumper sembolü yok); soğuk-soğuk ve sıcak-sıcak kesişmesi 0.
13. Temiz su etiketi hattın üzerinde, **daima yatay** (rot 0/180), kanca 31 + 8,3, 4 satır (soğuk Ø, soğuk MB, sıcak Ø, sıcak MB; satır aralığı 15); yalnız soğuk hatta 2 satır; her ıslak hacim girişi, daire girişi ve kombi için 1 etiket.
14. Çap: ≤ 0,75 MB 1/2"; 1,25–2,5 3/4"; 3–8,5 1"; 9,5–11,5 1 1/4"; depo 2"; şebeke/sayaç DN25.

**Kolon şeması**
15. Kat bandı 400 yüksek; döşeme = bant alt çizgisi; sol/sağ 50 cm kat-yazısı kutusu, kat yazısı h 25 rot 90; bant iç genişliği daire bloklarına göre (örnekte 6629).
16. Daire blokları yan yana (planın soldan sağa sırası), bloklar arası ≈ 140; armatür aralığı **130**; grup sırası kolondan dışa: mutfak BM-EV-kombi, wc LV-WC, banyo LV-WC-YS-DUŞ-ÇM; son armatür–kolon ekseni 154.
17. Pis su toplayıcı döşemenin 50 altında; her armatürde iniş + çatal; toplayıcı etiketi x = armatür − 80; kolon düşey çift çizgi, T.K. döşemenin 24 üstünde, dirsek 77 altında, "R" 20 sağında; kolon üst balonu en üst bantın 73 üstünde, kolon çizgisi balona değer; kolon etiketi (toplam SB) kolonun solunda düşey.
18. Temiz su: riser blok sol ucunda döşemeden 250 yukarı (etiket `1 1/4"`), yatay ana hat 250'de, her ıslak hacim grubu için kolon-ucu hizasında 120 iniş, dağıtım 130'da; sıcak 5 içeriden paralel, kombiden; temiz su etiketi x = armatür − 80, kanca yukarı, yatay.
19. D balonu (r 55, h 40) kombinin 197 solunda, döşemeden 268 yukarı; kombi blok sağ uçta, üstünde h 5 MTEXT.
20. Sayaç grubu zemin bandının SOLUNDA (ilk bloktan ≥ 200 solda), döşemenin 15 üstünde şebeke hattı (vana-pislik-çekvalf-vana-çekvalf, 25 aralık), sayaç satırları 20 aralıkla 5+4; satır: vana-pislik tutucu-sayaç-çek valf-vana (uzunluk 148). Kat bandında/kapı önünde sayaç 0.
21. Depo sol üstte (2. kat bant üstünün üstünde): 200×200 + 215×30 kaide, V yazısı, havalık+taşma 2", boşaltma, seviye göstergesi, şamandıralı doldurma (vana), çıkışta vana + pislik tutucu; şebekeden depoya ve depodan sayaç grubuna iki düşey hat sol kenarda, her katta akış oku.
22. Rögar şeması şemanın altında (döşemenin ≈ 630 altı): rögar 89×90 bloğu, aralık 239, arada Ø150 %1 + ok etiketi (yukarıda 29), kolon balonları rögar üstünde 55 aralıklı (2'den fazlası 2. satır), "70x70 h:-70cm" h 9,6; sıra planın sırası, PB sonda.
23. Yağmur şeması sağda: YB hatları 60 aralık, balon üstte, her katta Ø70 işareti (döşeme + 170), her hattın altında deşarj oku + "YAĞMUR SUYU KANALINA GİDER" (h 20, çerçeveli) + kırmızı çerçeveli 500×280 "YAĞMUR SUYU BORU ÇAPI HESABI" kutusu (h 10).

**Temel / çatı / pafta**
24. Temel planı: rögarlar bina dışında bir cephe boyunca (cepheden ≈ 110), aralık ≈ 500, aynı eksende Ø150 %1; kolon→rögar Ø125 %1, köşelerde 5 cm 45° pah; kolon dipleri P balonlu; PB son rögarın ≈ 500 ötesinde.
25. Pafta: 2900 yüksek şerit; antet 958 (alt yarı), yerleşim 1682, temel 2471, kat 2039–2065, çatı 2058, şema 7418, detay 2065; başlık h 40 alt çerçeveden 39 yukarı; detay paftasında üstte WC havalandırma izometrisi, altta 2000×1500 SIHHİ DETAYLAR.
26. MTY blokları KULLANILMAZ (14.10 B kuralı) — bu belgedeki blok adları yalnız geometri ölçüsü içindir; aynı ölçülerde saf geometri sembolleri çizilir.
