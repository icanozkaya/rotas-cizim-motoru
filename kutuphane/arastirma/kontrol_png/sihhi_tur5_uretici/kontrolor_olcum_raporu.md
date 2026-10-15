# KONTROLÖR RAPORU — NB_SIHHI_PAFTA_DENEME.dxf

Üretildi: 15.10.2026 11:55 — `python3 motor/kontrolor/kontrolor.py proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf --mimari ornekler/new_block.dxf.xz --rapor /tmp/claude-0/s2/rapor5.md`

## SONUÇ: **RED — 107 madde**

Düzeltme listesi (üreten ajana geri):
1. [T01 Z] balkon süzgeci (balkon) PİS SU kolonuna bağlanmış (P9) — kural: yalnız balkondaki yağmur inişine, kısa hatla @ (252746, -441887)
2. [T01 Z] pis su hattı balkon içinden geçiyor (balkon, 20 cm) @ (252861, -441971)
3. [T01 1] balkon süzgeci (balkon) PİS SU kolonuna bağlanmış (P9) — kural: yalnız balkondaki yağmur inişine, kısa hatla @ (254780, -441887)
4. [T01 2] balkon süzgeci (balkon) PİS SU kolonuna bağlanmış (P9) — kural: yalnız balkondaki yağmur inişine, kısa hatla @ (256828, -441887)
5. [T02 Z] WC (banyo) → P5 branşmanı: uzun: 321 cm > 300 @ (253291, -442577)
6. [T02 Z] WC (banyo) → P2 branşmanı: uzun: 307 cm > 300 @ (253839, -442540)
7. [T02 Z] DUS (banyo) → P2 branşmanı: uzun: 375 cm > 300 @ (253858, -442414)
8. [T02 Z] DUS (banyo) → P5 branşmanı: uzun: 375 cm > 300 @ (253273, -442414)
9. [T02 Z] BM (mutfak) → P1 branşmanı: mahal dışından dolaşıyor: 253 cm (ortak alan/dış) @ (253502, -443181)
10. [T02 1] WC (banyo) → P5 branşmanı: uzun: 316 cm > 300 @ (255326, -442560)
   … T02 için toplam 18 bulgu (ayrıntı aşağıda)
11. [T03 Z] pis su hattı banyo içinden, duvardan > 30 cm uzakta 105 cm geçiyor (ÇAPRAZ UZUN HAT) @ (253380, -442513)
12. [T03 1] pis su hattı banyo içinden, duvardan > 30 cm uzakta 105 cm geçiyor (ÇAPRAZ UZUN HAT) @ (255414, -442507)
13. [T03 1] pis su hattı wc-banyo içinden, duvardan > 30 cm uzakta 103 cm geçiyor (ÇAPRAZ UZUN HAT) @ (255181, -442125)
14. [T03 2] pis su hattı wc-banyo içinden, duvardan > 30 cm uzakta 103 cm geçiyor (ÇAPRAZ UZUN HAT) @ (257230, -442125)
15. [T03 2] pis su hattı banyo içinden, duvardan > 30 cm uzakta 143 cm geçiyor (ÇAPRAZ UZUN HAT) @ (257838, -442545)
16. [T07 Z] etiket mimari yazı üstüne: "P3" / "Döş.Mermer" @ (253641, -442648)
17. [T07 Z] etiket mimari yazı üstüne: "P5" / "15" @ (253495, -442758)
18. [T07 Z] etiket mimari yazı üstüne: "P6" / "13" @ (253495, -442691)
19. [T07 Z] etiket mimari yazı üstüne: "P6" / "12" @ (253495, -442668)
20. [T07 Z] etiket hat üstüne biniyor: "Ø50" (15 cm hat yazı kutusunda) @ (252779, -441950)
21. [T07 Z] etiket hat üstüne biniyor: "4 SB" (18 cm hat yazı kutusunda) @ (252791, -441963)
   … T07 için toplam 63 bulgu (ayrıntı aşağıda)
22. [T10 Z] kolon P1 ıslak hacim dışında (ortak alan / dış) — kural: kolon ıslak hacmin köşesinde @ (253578, -443414)
23. [T10 Z] kolon P2 banyo köşesinde değil (en yakın köşe 48 cm) @ (253716, -442662)
24. [T10 Z] kolon P1 ıslak hacim dışında (ortak alan / dış) — kural: kolon ıslak hacmin köşesinde @ (253553, -443414)
25. [T10 Z] kolon P5 banyo köşesinde değil (en yakın köşe 48 cm) @ (253414, -442662)
26. [T10 Z] kolon P7 ıslak hacim dışında (antre-kor.) — kural: kolon ıslak hacmin köşesinde @ (253765, -441812)
27. [T10 1] kolon P4 ıslak hacim dışında (ortak alan / dış) — kural: kolon ıslak hacmin köşesinde @ (255587, -443414)
   … T10 için toplam 16 bulgu (ayrıntı aşağıda)
28. [T11] yazı-yazı çakışması (denetle %2): 13 — ROTAS-MIMARI-YAZI "12" / 0 "P6" (253495, -442666), ROTAS-MIMARI-YAZI "13" / 0 "P6" (253495, -442696), ROTAS-MIMARI-YAZI "15" / 0 "P5" (253495, -442758), ROTAS-MIMARI-YAZI "Döş.Mermer" / 0 "P3" (253628, -442645)

## Özet

| Test | Ne ölçer | Sonuç | FAIL | INFO | Referans new_block FAIL/INFO (aynı ölçüm) |
|---|---|---|---|---|---|
| T01 | Balkon süzgeci bağlantı hedefi (yağmur inişi, kısa hat; pis su kolonuna ASLA) | ✗ FAIL | 4 | 0 | 0 / 0 |
| T02 | Pis su branşmanı: uzunluk ≤ 300 cm, açı {0,45,90}, mahal dışından dolaşmaz, her armatür bağlı | ✗ FAIL | 18 | 0 | 59 / 3 — kullanıcı branşmanı serbest açılı çiziyor (kural C 45° ister) |
| T03 | Oda içi çapraz pis su hattı (duvardan > 30 cm iç bölge) | ✗ FAIL | 5 | 13 | 0 / 21 |
| T04 | Sıcak su daire dışı uzunluk = 0, kombiden başlar | ✓ PASS | 0 | 0 | 0 / 0 — kapı komşuluğuyla daire ataması: 0 (önceki 1 FAIL 1. kat wc-duş D5→D6 eşleme hatasıydı) |
| T05 | Sıcak–soğuk paralellik (sabit ofset) ve kesişme | ✓ PASS | 0 | 0 | 0 / 6 |
| T06 | Koridor hatları koridor ortasında | bilgi | 0 | 32 | 0 / 39 |
| T07 | Etiket–etiket / etiket–mimari yazı / etiket–hat çakışması, etiket boyu | ✗ FAIL | 63 | 3 | 208 / 5 — 208 = etiket–mimari yazı 80 + etiket–hat 128 (kullanıcı tarzı); yeni alt testler: etiket–etiket 0, tarama 0, eviye/BM/kombi/makine yeri 0, asansör 0 |
| T08 | Kolon şeması: sayaçlar zemin bandında, şebeke girişinde (solda); kat bantlarında sayaç yok | ✓ PASS | 0 | 0 | 0 / 1 |
| T09 | Islak hacim başına yer süzgeci = 1 | ✓ PASS | 0 | 0 | 16 / 0 — mutfak/wc-lvb.de süzgeç yok (B kuralı ister) |
| T10 | Pis su kolonu ıslak hacim köşesinde (betonarme dışında) | ✗ FAIL | 16 | 0 | 0 / 3 |
| T11 | denetle.py: MTY 0, ROTAS- öneki, köprü 0, kesişme 0, elektrik 0, yazı çakışması 0, lejant, audit | ✗ FAIL | 1 | 1 | 34 / 1 — MTY katmanları (beklenen) |
| T12 | Kolon düşey sürekliliği: aynı numara her katta aynı eksende (± 5 cm); referansta olmayan yeni numara yok | ✓ PASS | 0 | 0 | 0 / 0 |
| T13 | Ç.M./B.M. mimarideki yerinde (± 40 cm); kolon/aspiratör o yeri işgal etmiyor | ✓ PASS | 0 | 0 | 0 / 0 |
| T14 | Aspiratör notu kendi ıslak hacminde (≤ 60 cm), ortak alanda değil; kılavuz başka mahali kesmiyor | ✓ PASS | 0 | 0 | 0 / 0 |
| T15 | Penceresiz her ıslak hacimde aspiratör / mekanik havalandırma notu | ✓ PASS | 0 | 3 | 0 / 3 — BİLGİ: duş kabini (< 1 m²) havalandırma aranmadı |
| T16 | Paftada iç kural metni sızıntısı ("(EK)", "new_block", "otomatik", kural cümleleri) yok; ACI 250–255 renk yok | ✓ PASS | 0 | 0 | 0 / 0 |
| T17 | Pafta genişlikleri ve sırası ORNEK_DUZEN / ALTIN_REFERANS §1 ile (± %5) | ✓ PASS | 0 | 1 | 0 / 1 |

Referans sütunu: kullanıcının kendi `new_block.dxf` çizimi aynı testlerden geçirildiğinde çıkan sayılar (15.10.2026). Referansın kendisinde de görülen türden bulgular (ör. T07 etiket-hat, T02 serbest açı) tarz farkı değil kural C ihlali olarak listelenir; T11 MTY sayıları referans için beklenen durumdur.

## Dosya ve mimari eşleme

- dosya: proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf — çerçeve 11, kat paftası ['1', '2', 'Z'], şema paftası var
- mimari kaynak: ornekler/new_block.dxf.xz (30942 kayıt)
- kat Z: öteleme (0.0, 0.0) 260 yazı eşleşmesi; mahal 32 (ıslak 9, ortak 2, balkon 4), daire [1, 2, 3], armatür 29, betonarme 32 — 3.3 s
- kat 1: öteleme (0.0, 0.0) 255 yazı eşleşmesi; mahal 32 (ıslak 9, ortak 2, balkon 4), daire [4, 5, 6], armatür 29, betonarme 32 — 2.8 s
- kat 2: öteleme (0.0, 0.0) 255 yazı eşleşmesi; mahal 32 (ıslak 9, ortak 2, balkon 4), daire [7, 8, 9], armatür 28, betonarme 32 — 2.7 s
- kat 1: kapı komşuluğuyla daire ataması düzeltildi: wc-duş D5→D6
- kat 2: kapı komşuluğuyla daire ataması düzeltildi: yüklük D8→D9

Süre 185 s.

## Ayrıntı (koordinatlar çizim birimi, cm)

### T01 — Balkon süzgeci bağlantı hedefi (yağmur inişi, kısa hat; pis su kolonuna ASLA)

- **FAIL** [Z]: balkon süzgeci (balkon) PİS SU kolonuna bağlanmış (P9) — kural: yalnız balkondaki yağmur inişine, kısa hatla @ (252746, -441887)  
  ![T01](rapor5_png/T01_Z_01.png)
- **FAIL** [Z]: pis su hattı balkon içinden geçiyor (balkon, 20 cm) @ (252861, -441971)  
  ![T01](rapor5_png/T01_Z_02.png)
- **FAIL** [1]: balkon süzgeci (balkon) PİS SU kolonuna bağlanmış (P9) — kural: yalnız balkondaki yağmur inişine, kısa hatla @ (254780, -441887)  
  ![T01](rapor5_png/T01_1_01.png)
- **FAIL** [2]: balkon süzgeci (balkon) PİS SU kolonuna bağlanmış (P9) — kural: yalnız balkondaki yağmur inişine, kısa hatla @ (256828, -441887)  
  ![T01](rapor5_png/T01_2_01.png)

### T02 — Pis su branşmanı: uzunluk ≤ 300 cm, açı {0,45,90}, mahal dışından dolaşmaz, her armatür bağlı

- **FAIL** [Z]: WC (banyo) → P5 branşmanı: uzun: 321 cm > 300 @ (253291, -442577)  
  ![T02](rapor5_png/T02_Z_01.png)
- **FAIL** [Z]: WC (banyo) → P2 branşmanı: uzun: 307 cm > 300 @ (253839, -442540)  
  ![T02](rapor5_png/T02_Z_02.png)
- **FAIL** [Z]: DUS (banyo) → P2 branşmanı: uzun: 375 cm > 300 @ (253858, -442414)  
  ![T02](rapor5_png/T02_Z_03.png)
- **FAIL** [Z]: DUS (banyo) → P5 branşmanı: uzun: 375 cm > 300 @ (253273, -442414)  
  ![T02](rapor5_png/T02_Z_04.png)
- **FAIL** [Z]: BM (mutfak) → P1 branşmanı: mahal dışından dolaşıyor: 253 cm (ortak alan/dış) @ (253502, -443181)  
  ![T02](rapor5_png/T02_Z_05.png)
- **FAIL** [1]: WC (banyo) → P5 branşmanı: uzun: 316 cm > 300 @ (255326, -442560)  
  ![T02](rapor5_png/T02_1_01.png)
- **FAIL** [1]: WC (wc-duş) → P3 branşmanı: uzun: 440 cm > 300; mahal dışından dolaşıyor: 212 cm (banyo) @ (255861, -442394)  
  ![T02](rapor5_png/T02_1_02.png)
- **FAIL** [1]: LV (wc-duş) → P9 branşmanı: mahal dışından dolaşıyor: 112 cm (ortak alan/dış) @ (254909, -441971)  
  ![T02](rapor5_png/T02_1_03.png)
- **FAIL** [1]: LV (wc-duş) → P3 branşmanı: uzun: 529 cm > 300; mahal dışından dolaşıyor: 212 cm (banyo) @ (255845, -442292)  
  ![T02](rapor5_png/T02_1_04.png)
- **FAIL** [1]: DUS (banyo) → P3 branşmanı: uzun: 317 cm > 300 @ (255892, -442459)  
  ![T02](rapor5_png/T02_1_05.png)
- **FAIL** [1]: DUS (banyo) → P5 branşmanı: uzun: 375 cm > 300 @ (255307, -442414)  
  ![T02](rapor5_png/T02_1_06.png)
- **FAIL** [1]: DUS (wc-duş) → P3 branşmanı: uzun: 324 cm > 300; mahal dışından dolaşıyor: 212 cm (banyo) @ (255752, -442413)  
  ![T02](rapor5_png/T02_1_07.png)
- **FAIL** [1]: BM (mutfak) → P4 branşmanı: mahal dışından dolaşıyor: 253 cm (ortak alan/dış) @ (255536, -443181)  
  ![T02](rapor5_png/T02_1_08.png)
- **FAIL** [2]: WC (banyo) → P5 branşmanı: uzun: 359 cm > 300 @ (257374, -442560)  
  ![T02](rapor5_png/T02_2_01.png)
- **FAIL** [2]: DUS (banyo) → P2 branşmanı: uzun: 364 cm > 300 @ (257941, -442414)  
  ![T02](rapor5_png/T02_2_02.png)
- **FAIL** [2]: DUS (banyo) → P5 branşmanı: uzun: 375 cm > 300 @ (257355, -442414)  
  ![T02](rapor5_png/T02_2_03.png)
- **FAIL** [2]: BM (mutfak) → P4 branşmanı: mahal dışından dolaşıyor: 252 cm (ortak alan/dış) @ (257584, -443181)  
  ![T02](rapor5_png/T02_2_04.png)
- **FAIL** [2]: YS (banyo) → P5 branşmanı: uzun: 312 cm > 300 @ (257350, -442485)  
  ![T02](rapor5_png/T02_2_05.png)

### T03 — Oda içi çapraz pis su hattı (duvardan > 30 cm iç bölge)

- **INFO** [Z]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 92 cm geçiyor (kısa çapraz, bilgi) @ (253751, -442502)
- **INFO** [Z]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 40 cm geçiyor (kısa çapraz, bilgi) @ (253839, -442507)
- **FAIL** [Z]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 105 cm geçiyor (ÇAPRAZ UZUN HAT) @ (253380, -442513)  
  ![T03](rapor5_png/T03_Z_01.png)
- **INFO** [Z]: pis su hattı wc+banyo içinden, duvardan > 30 cm uzakta 73 cm geçiyor (kısa çapraz, bilgi) @ (253162, -442110)
- **FAIL** [1]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 105 cm geçiyor (ÇAPRAZ UZUN HAT) @ (255414, -442507)  
  ![T03](rapor5_png/T03_1_01.png)
- **FAIL** [1]: pis su hattı wc-banyo içinden, duvardan > 30 cm uzakta 103 cm geçiyor (ÇAPRAZ UZUN HAT) @ (255181, -442125)  
  ![T03](rapor5_png/T03_1_02.png)
- **INFO** [1]: pis su hattı wc-banyo içinden, duvardan > 30 cm uzakta 56 cm geçiyor (kısa çapraz, bilgi) @ (255186, -442120)
- **INFO** [1]: pis su hattı wc-duş içinden, duvardan > 30 cm uzakta 98 cm geçiyor (kısa çapraz, bilgi) @ (255845, -442395)
- **INFO** [1]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 93 cm geçiyor (kısa çapraz, bilgi) @ (255794, -442582)
- **INFO** [1]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 81 cm geçiyor (kısa çapraz, bilgi) @ (255799, -442577)
- **INFO** [1]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 36 cm geçiyor (kısa çapraz, bilgi) @ (255843, -442538)
- **INFO** [2]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 47 cm geçiyor (kısa çapraz, bilgi) @ (257379, -442485)
- **INFO** [2]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 77 cm geçiyor (kısa çapraz, bilgi) @ (257374, -442490)
- **FAIL** [2]: pis su hattı wc-banyo içinden, duvardan > 30 cm uzakta 103 cm geçiyor (ÇAPRAZ UZUN HAT) @ (257230, -442125)  
  ![T03](rapor5_png/T03_2_01.png)
- **INFO** [2]: pis su hattı wc-banyo içinden, duvardan > 30 cm uzakta 55 cm geçiyor (kısa çapraz, bilgi) @ (257235, -442120)
- **FAIL** [2]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 143 cm geçiyor (ÇAPRAZ UZUN HAT) @ (257838, -442545)  
  ![T03](rapor5_png/T03_2_02.png)
- **INFO** [2]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 85 cm geçiyor (kısa çapraz, bilgi) @ (257843, -442540)
- **INFO** [2]: pis su hattı banyo içinden, duvardan > 30 cm uzakta 76 cm geçiyor (kısa çapraz, bilgi) @ (257843, -442502)

### T04 — Sıcak su daire dışı uzunluk = 0, kombiden başlar

- **PASS** [Z]: 3 sıcak su ağı daire içinde, kombiden
- **PASS** [1]: 3 sıcak su ağı daire içinde, kombiden
- **PASS** [2]: 3 sıcak su ağı daire içinde, kombiden

### T05 — Sıcak–soğuk paralellik (sabit ofset) ve kesişme

- **PASS** [Z]: 39 sıcak parçası soğukla sabit ofsetli paralel, kesişme yok
- **PASS** [1]: 39 sıcak parçası soğukla sabit ofsetli paralel, kesişme yok
- **PASS** [2]: 35 sıcak parçası soğukla sabit ofsetli paralel, kesişme yok

### T06 — Koridor hatları koridor ortasında

- **INFO** [Z]: 5 koridor parçası ortada, 10 duvar dibinde (BİLGİ: kullanıcının kendi new_block çiziminde antre hatları duvar dibinde; B kuralı koridor ortası — karar kullanıcıda)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 68 cm, koridor 314 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (253376, -442936)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 63 cm, koridor 314 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (253381, -442932)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 149 cm, koridor 724 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (253615, -441924)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 75 cm, koridor 734 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (253105, -441994)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 65 cm, koridor 724 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (253105, -441922)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 144 cm, koridor 724 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (253620, -441921)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 80 cm, koridor 734 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (253110, -441989)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 70 cm, koridor 724 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (253110, -441919)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 61 cm, koridor 314 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (253751, -442934)
- **INFO** [Z]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 66 cm, koridor 314 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (253756, -442933)
- **INFO** [1]: 6 koridor parçası ortada, 10 duvar dibinde (BİLGİ: kullanıcının kendi new_block çiziminde antre hatları duvar dibinde; B kuralı koridor ortası — karar kullanıcıda)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 68 cm, koridor 314 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (255410, -442936)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 63 cm, koridor 314 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (255415, -442932)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 164 cm, koridor 734 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (255634, -441986)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 65 cm, koridor 724 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (255139, -441916)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 75 cm, koridor 734 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (255139, -441989)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 164 cm, koridor 724 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (255634, -441918)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 70 cm, koridor 724 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (255144, -441914)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 80 cm, koridor 734 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (255144, -441984)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 26 cm, koridor 310 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (255750, -442962)
- **INFO** [1]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 31 cm, koridor 320 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (255755, -442960)
- **INFO** [2]: 2 koridor parçası ortada, 9 duvar dibinde (BİLGİ: kullanıcının kendi new_block çiziminde antre hatları duvar dibinde; B kuralı koridor ortası — karar kullanıcıda)
- **INFO** [2]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 78 cm, koridor 314 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (257448, -442936)
- **INFO** [2]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 73 cm, koridor 314 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (257453, -442933)
- **INFO** [2]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 139 cm, koridor 746 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (257719, -441984)
- **INFO** [2]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 31 cm, koridor 166 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (257767, -441919)
- **INFO** [2]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 47 cm, koridor 757 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (257169, -441935)
- **INFO** [2]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 26 cm, koridor 168 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (257772, -441914)
- **INFO** [2]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 52 cm, koridor 758 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (257174, -441932)
- **INFO** [2]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 58 cm, koridor 314 cm (ROTAS-SIHHI-SOGUK-SU) — kural: koridorda hatlar ORTADAN @ (257830, -442933)
- **INFO** [2]: antre-kor. içinde temiz su hattı duvar dibinde: duvara 63 cm, koridor 314 cm (ROTAS-SIHHI-SICAK-SU) — kural: koridorda hatlar ORTADAN @ (257835, -442933)

### T07 — Etiket–etiket / etiket–mimari yazı / etiket–hat çakışması, etiket boyu

- **INFO** [Z]: etiket-etiket 0, etiket-mimari yazı 4, etiket-hat 15, etiket-tarama 0, etiket-armatür/sembol 0, etiket-asansör boşluğu 0 (toplam 157 etiket)
- **FAIL** [Z]: etiket mimari yazı üstüne: "P3" / "Döş.Mermer" @ (253641, -442648)  
  ![T07](rapor5_png/T07_Z_01.png)
- **FAIL** [Z]: etiket mimari yazı üstüne: "P5" / "15" @ (253495, -442758)  
  ![T07](rapor5_png/T07_Z_02.png)
- **FAIL** [Z]: etiket mimari yazı üstüne: "P6" / "13" @ (253495, -442691)  
  ![T07](rapor5_png/T07_Z_03.png)
- **FAIL** [Z]: etiket mimari yazı üstüne: "P6" / "12" @ (253495, -442668)  
  ![T07](rapor5_png/T07_Z_04.png)
- **FAIL** [Z]: etiket hat üstüne biniyor: "Ø50" (15 cm hat yazı kutusunda) @ (252779, -441950)  
  ![T07](rapor5_png/T07_Z_05.png)
- **FAIL** [Z]: etiket hat üstüne biniyor: "4 SB" (18 cm hat yazı kutusunda) @ (252791, -441963)  
  ![T07](rapor5_png/T07_Z_06.png)
- **FAIL** [Z]: etiket hat üstüne biniyor: "Ø50" (18 cm hat yazı kutusunda) @ (253075, -442196)  
  ![T07](rapor5_png/T07_Z_07.png)
- **FAIL** [Z]: etiket hat üstüne biniyor: "4 SB" (13 cm hat yazı kutusunda) @ (253066, -442211)  
  ![T07](rapor5_png/T07_Z_08.png)
- **FAIL** [Z]: etiket hat üstüne biniyor: "Ø50" (13 cm hat yazı kutusunda) @ (253296, -442710)  
  ![T07](rapor5_png/T07_Z_09.png)
- **FAIL** [Z]: etiket hat üstüne biniyor: "Ø50" (13 cm hat yazı kutusunda) @ (253301, -442710)  
  ![T07](rapor5_png/T07_Z_10.png)
- **FAIL** [Z]: etiket hat üstüne biniyor: "2 SB" (13 cm hat yazı kutusunda) @ (253296, -442725)  
  ![T07](rapor5_png/T07_Z_11.png)
- **FAIL** [Z]: etiket hat üstüne biniyor: "2 SB" (13 cm hat yazı kutusunda) @ (253301, -442725)  
  ![T07](rapor5_png/T07_Z_12.png)
- **FAIL** [Z]: etiket hat üstüne biniyor: "Ø50" (13 cm hat yazı kutusunda) @ (253796, -442706)
- **FAIL** [Z]: etiket hat üstüne biniyor: "Ø50" (13 cm hat yazı kutusunda) @ (253801, -442706)
- **FAIL** [Z]: etiket hat üstüne biniyor: "2 SB" (13 cm hat yazı kutusunda) @ (253796, -442721)
- **FAIL** [Z]: etiket hat üstüne biniyor: "2 SB" (13 cm hat yazı kutusunda) @ (253801, -442721)
- **FAIL** [Z]: etiket hat üstüne biniyor: "Ø100" (18 cm hat yazı kutusunda) @ (253105, -442136)
- **FAIL** [Z]: etiket hat üstüne biniyor: "Ø100" (18 cm hat yazı kutusunda) @ (253110, -442131)
- **FAIL** [Z]: etiket hat üstüne biniyor: "14 SB" (18 cm hat yazı kutusunda) @ (253110, -442151)
- **INFO** [1]: etiket-etiket 0, etiket-mimari yazı 3, etiket-hat 18, etiket-tarama 0, etiket-armatür/sembol 0, etiket-asansör boşluğu 0 (toplam 174 etiket)
- **FAIL** [1]: etiket mimari yazı üstüne: "P5" / "15" @ (255529, -442758)  
  ![T07](rapor5_png/T07_1_01.png)
- **FAIL** [1]: etiket mimari yazı üstüne: "P6" / "13" @ (255529, -442691)  
  ![T07](rapor5_png/T07_1_02.png)
- **FAIL** [1]: etiket mimari yazı üstüne: "P6" / "12" @ (255529, -442668)  
  ![T07](rapor5_png/T07_1_03.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "Ø50" (13 cm hat yazı kutusunda) @ (255616, -443310)  
  ![T07](rapor5_png/T07_1_04.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "4 SB" (13 cm hat yazı kutusunda) @ (255616, -443325)  
  ![T07](rapor5_png/T07_1_05.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "Ø50" (13 cm hat yazı kutusunda) @ (255100, -442196)  
  ![T07](rapor5_png/T07_1_06.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "4 SB" (13 cm hat yazı kutusunda) @ (255100, -442211)  
  ![T07](rapor5_png/T07_1_07.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "Ø100" (13 cm hat yazı kutusunda) @ (255770, -442563)  
  ![T07](rapor5_png/T07_1_08.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "Ø100" (13 cm hat yazı kutusunda) @ (255775, -442563)  
  ![T07](rapor5_png/T07_1_09.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "44 SB" (13 cm hat yazı kutusunda) @ (255770, -442578)  
  ![T07](rapor5_png/T07_1_10.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "44 SB" (13 cm hat yazı kutusunda) @ (255775, -442578)  
  ![T07](rapor5_png/T07_1_11.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "Ø100" (27 cm hat yazı kutusunda) @ (255770, -442532)  
  ![T07](rapor5_png/T07_1_12.png)
- **FAIL** [1]: etiket hat üstüne biniyor: "Ø100" (27 cm hat yazı kutusunda) @ (255775, -442532)
- **FAIL** [1]: etiket hat üstüne biniyor: "Ø100" (13 cm hat yazı kutusunda) @ (255139, -442136)
- **FAIL** [1]: etiket hat üstüne biniyor: "Ø100" (13 cm hat yazı kutusunda) @ (255144, -442136)
- **FAIL** [1]: etiket hat üstüne biniyor: "14 SB" (13 cm hat yazı kutusunda) @ (255139, -442150)
- **FAIL** [1]: etiket hat üstüne biniyor: "14 SB" (13 cm hat yazı kutusunda) @ (255144, -442150)
- **FAIL** [1]: etiket hat üstüne biniyor: "Ø100" (11 cm hat yazı kutusunda) @ (255834, -442415)
- **FAIL** [1]: etiket hat üstüne biniyor: "32 SB" (18 cm hat yazı kutusunda) @ (255820, -442424)
- **FAIL** [1]: etiket hat üstüne biniyor: "7 SB" (22 cm hat yazı kutusunda) @ (255197, -442239)
- **FAIL** [1]: etiket hat üstüne biniyor: "7 SB" (22 cm hat yazı kutusunda) @ (255197, -442234)
- **INFO** [2]: etiket-etiket 0, etiket-mimari yazı 6, etiket-hat 17, etiket-tarama 0, etiket-armatür/sembol 0, etiket-asansör boşluğu 0 (toplam 165 etiket)
- **FAIL** [2]: etiket mimari yazı üstüne: "P5" / "15" @ (257577, -442758)  
  ![T07](rapor5_png/T07_2_01.png)
- **FAIL** [2]: etiket mimari yazı üstüne: "P6" / "13" @ (257577, -442691)  
  ![T07](rapor5_png/T07_2_02.png)
- **FAIL** [2]: etiket mimari yazı üstüne: "P6" / "12" @ (257577, -442668)  
  ![T07](rapor5_png/T07_2_03.png)
- **FAIL** [2]: etiket mimari yazı üstüne: "P3" / "Döş.Mermer" @ (257723, -442648)  
  ![T07](rapor5_png/T07_2_04.png)
- **FAIL** [2]: etiket mimari yazı üstüne: "Ø100" / "wc-lvb." @ (257807, -442775)  
  ![T07](rapor5_png/T07_2_05.png)
- **FAIL** [2]: etiket mimari yazı üstüne: "10 SB" / "wc-lvb." @ (257819, -442775)  
  ![T07](rapor5_png/T07_2_06.png)
- **FAIL** [2]: etiket hat üstüne biniyor: "Ø50" (20 cm hat yazı kutusunda) @ (257161, -442199)  
  ![T07](rapor5_png/T07_2_07.png)
- **FAIL** [2]: etiket hat üstüne biniyor: "Ø50" (15 cm hat yazı kutusunda) @ (256861, -441950)  
  ![T07](rapor5_png/T07_2_08.png)
- **FAIL** [2]: etiket hat üstüne biniyor: "4 SB" (18 cm hat yazı kutusunda) @ (256873, -441963)  
  ![T07](rapor5_png/T07_2_09.png)
- **FAIL** [2]: etiket hat üstüne biniyor: "Ø50" (20 cm hat yazı kutusunda) @ (257635, -443312)  
  ![T07](rapor5_png/T07_2_10.png)
- **FAIL** [2]: etiket hat üstüne biniyor: "14 SB" (18 cm hat yazı kutusunda) @ (257144, -442139)  
  ![T07](rapor5_png/T07_2_11.png)
- **FAIL** [2]: etiket hat üstüne biniyor: "14 SB" (12 cm hat yazı kutusunda) @ (257149, -442137)  
  ![T07](rapor5_png/T07_2_12.png)
- **FAIL** [2]: etiket hat üstüne biniyor: "Ø50" (13 cm hat yazı kutusunda) @ (257880, -442704)
- **FAIL** [2]: etiket hat üstüne biniyor: "Ø50" (13 cm hat yazı kutusunda) @ (257885, -442704)
- **FAIL** [2]: etiket hat üstüne biniyor: "2 SB" (13 cm hat yazı kutusunda) @ (257880, -442719)
- **FAIL** [2]: etiket hat üstüne biniyor: "2 SB" (13 cm hat yazı kutusunda) @ (257885, -442719)
- **FAIL** [2]: etiket hat üstüne biniyor: "Ø50" (20 cm hat yazı kutusunda) @ (257259, -442188)
- **FAIL** [2]: etiket hat üstüne biniyor: "Ø100" (13 cm hat yazı kutusunda) @ (257849, -442611)
- **FAIL** [2]: etiket hat üstüne biniyor: "Ø100" (13 cm hat yazı kutusunda) @ (257849, -442606)
- **FAIL** [2]: etiket hat üstüne biniyor: "23 SB" (13 cm hat yazı kutusunda) @ (257863, -442611)
- **FAIL** [2]: etiket hat üstüne biniyor: "23 SB" (13 cm hat yazı kutusunda) @ (257863, -442606)
- **FAIL** [2]: etiket hat üstüne biniyor: "Ø100" (16 cm hat yazı kutusunda) @ (257494, -442504)
- **FAIL** [2]: etiket hat üstüne biniyor: "19 SB" (13 cm hat yazı kutusunda) @ (257496, -442520)

### T08 — Kolon şeması: sayaçlar zemin bandında, şebeke girişinde (solda); kat bantlarında sayaç yok

- **PASS** [ŞEMA]: 9 sayaç zemin bandında, şebeke girişinde; kat bantlarında sayaç yok

### T09 — Islak hacim başına yer süzgeci = 1

- **PASS** [Z]: 9 ıslak hacimde 1 süzgeç
- **PASS** [1]: 9 ıslak hacimde 1 süzgeç
- **PASS** [2]: 9 ıslak hacimde 1 süzgeç

### T10 — Pis su kolonu ıslak hacim köşesinde (betonarme dışında)

- **FAIL** [Z]: kolon P1 ıslak hacim dışında (ortak alan / dış) — kural: kolon ıslak hacmin köşesinde @ (253578, -443414)  
  ![T10](rapor5_png/T10_Z_01.png)
- **FAIL** [Z]: kolon P2 banyo köşesinde değil (en yakın köşe 48 cm) @ (253716, -442662)  
  ![T10](rapor5_png/T10_Z_02.png)
- **FAIL** [Z]: kolon P1 ıslak hacim dışında (ortak alan / dış) — kural: kolon ıslak hacmin köşesinde @ (253553, -443414)  
  ![T10](rapor5_png/T10_Z_03.png)
- **FAIL** [Z]: kolon P5 banyo köşesinde değil (en yakın köşe 48 cm) @ (253414, -442662)  
  ![T10](rapor5_png/T10_Z_04.png)
- **FAIL** [Z]: kolon P7 ıslak hacim dışında (antre-kor.) — kural: kolon ıslak hacmin köşesinde @ (253765, -441812)  
  ![T10](rapor5_png/T10_Z_05.png)
- **FAIL** [1]: kolon P4 ıslak hacim dışında (ortak alan / dış) — kural: kolon ıslak hacmin köşesinde @ (255587, -443414)  
  ![T10](rapor5_png/T10_1_01.png)
- **FAIL** [1]: kolon P5 banyo köşesinde değil (en yakın köşe 48 cm) @ (255448, -442662)  
  ![T10](rapor5_png/T10_1_02.png)
- **FAIL** [1]: kolon P7 ıslak hacim dışında (antre-kor.) — kural: kolon ıslak hacmin köşesinde @ (255799, -441812)  
  ![T10](rapor5_png/T10_1_03.png)
- **FAIL** [1]: kolon P9 ıslak hacim dışında (yatak od.) — kural: kolon ıslak hacmin köşesinde @ (254812, -441881)  
  ![T10](rapor5_png/T10_1_04.png)
- **FAIL** [1]: kolon P4 ıslak hacim dışında (ortak alan / dış) — kural: kolon ıslak hacmin köşesinde @ (255612, -443414)  
  ![T10](rapor5_png/T10_1_05.png)
- **FAIL** [1]: kolon P3 banyo köşesinde değil (en yakın köşe 48 cm) @ (255750, -442662)  
  ![T10](rapor5_png/T10_1_06.png)
- **FAIL** [2]: kolon P4 ıslak hacim dışında (ortak alan / dış) — kural: kolon ıslak hacmin köşesinde @ (257635, -443414)  
  ![T10](rapor5_png/T10_2_01.png)
- **FAIL** [2]: kolon P5 banyo köşesinde değil (en yakın köşe 48 cm) @ (257496, -442662)  
  ![T10](rapor5_png/T10_2_02.png)
- **FAIL** [2]: kolon P7 ıslak hacim dışında (antre-kor.) — kural: kolon ıslak hacmin köşesinde @ (257847, -441812)  
  ![T10](rapor5_png/T10_2_03.png)
- **FAIL** [2]: kolon P4 ıslak hacim dışında (ortak alan / dış) — kural: kolon ıslak hacmin köşesinde @ (257660, -443414)  
  ![T10](rapor5_png/T10_2_04.png)
- **FAIL** [2]: kolon P2 banyo köşesinde değil (en yakın köşe 48 cm) @ (257798, -442662)  
  ![T10](rapor5_png/T10_2_05.png)

### T11 — denetle.py: MTY 0, ROTAS- öneki, köprü 0, kesişme 0, elektrik 0, yazı çakışması 0, lejant, audit

- **FAIL**: yazı-yazı çakışması (denetle %2): 13 — ROTAS-MIMARI-YAZI "12" / 0 "P6" (253495, -442666), ROTAS-MIMARI-YAZI "13" / 0 "P6" (253495, -442696), ROTAS-MIMARI-YAZI "15" / 0 "P5" (253495, -442758), ROTAS-MIMARI-YAZI "Döş.Mermer" / 0 "P3" (253628, -442645)
- **INFO**: pis su – temiz su üst üste geçiş (farklı düzlem, bilgi): 67

### T12 — Kolon düşey sürekliliği: aynı numara her katta aynı eksende (± 5 cm); referansta olmayan yeni numara yok

- **PASS**: 9 kolon her katta aynı eksende (± 5 cm), yeni numara yok

### T13 — Ç.M./B.M. mimarideki yerinde (± 40 cm); kolon/aspiratör o yeri işgal etmiyor

- **PASS** [Z]: 2 Ç.M./B.M. mimarideki yerinde (± 40 cm); kolon/aspiratör makine yerinde değil
- **PASS** [1]: 2 Ç.M./B.M. mimarideki yerinde (± 40 cm); kolon/aspiratör makine yerinde değil
- **PASS** [2]: 2 Ç.M./B.M. mimarideki yerinde (± 40 cm); kolon/aspiratör makine yerinde değil

### T14 — Aspiratör notu kendi ıslak hacminde (≤ 60 cm), ortak alanda değil; kılavuz başka mahali kesmiyor

- **PASS** [Z]: 3 aspiratör notu kendi ıslak hacminde (≤ 60 cm), kılavuz başka mahali kesmiyor
- **PASS** [1]: 4 aspiratör notu kendi ıslak hacminde (≤ 60 cm), kılavuz başka mahali kesmiyor
- **PASS** [2]: 3 aspiratör notu kendi ıslak hacminde (≤ 60 cm), kılavuz başka mahali kesmiyor

### T15 — Penceresiz her ıslak hacimde aspiratör / mekanik havalandırma notu

- **INFO** [Z]: duş D3 0.34 m² (duş kabini; ayrı havalandırma aranmadı)
- **PASS** [Z]: 5 penceresiz ıslak hacimde aspiratör var (0 pencereli)
- **INFO** [1]: wc-duş D5 0.48 m² (duş kabini; ayrı havalandırma aranmadı)
- **PASS** [1]: 4 penceresiz ıslak hacimde aspiratör var (1 pencereli)
- **INFO** [2]: duş D8 0.83 m² (duş kabini; ayrı havalandırma aranmadı)
- **PASS** [2]: 5 penceresiz ıslak hacimde aspiratör var (0 pencereli)

### T16 — Paftada iç kural metni sızıntısı ("(EK)", "new_block", "otomatik", kural cümleleri) yok; ACI 250–255 renk yok

- **PASS**: iç metin sızıntısı yok, ACI 250–255 / koyu renk yok

### T17 — Pafta genişlikleri ve sırası ORNEK_DUZEN / ALTIN_REFERANS §1 ile (± %5)

- **INFO** [PAFTA]: şerit (sihhi): antet 958, yerlesim 1682, temel 2471, Z 2065, kat:1 2039, kat:2 2039, cati 2058, sema 7418, detay 2065
- **PASS** [PAFTA]: 9 pafta genişliği referansla ± %5, sıra doğru

## Genel görünümler

- KAT Z: ![](rapor5_png/GENEL_KAT_Z.png)
- KAT 1: ![](rapor5_png/GENEL_KAT_1.png)
- KAT 2: ![](rapor5_png/GENEL_KAT_2.png)
- ŞEMA: ![](rapor5_png/GENEL_SEMA.png)

## Eşikler

- T01 balkon süzgeci–iniş hat boyu ≤ 300 cm; süzgecin bağlı olduğu ağda pis su katmanı/kolonu varsa FAIL.
- T02 armatür→kolon branşman yolu ≤ 300 cm; parça açıları {0,45,90} ± 4°; yol armatür mahalli + kolon mahalli (duvar payı 30 cm) dışına > 40 cm çıkarsa FAIL; WC/LV/DUŞ/EVİYE 50 cm içinde hat yoksa FAIL.
- T03 mahal poligonunun 30 cm içeri çekilmiş bölgesinde ≥ 30 cm pis su hattı → FAIL.
- T04 sıcak su bağlı ağı en çok örtüştüğü daire poligonu (mahaller + 20 cm duvar payı) dışında > 15 cm → FAIL; kombiye 80 cm içinde başlamıyorsa FAIL.
- T05 sıcak parçası (≥ 60 cm) boyunca soğuğa mesafe 3–30 cm olan örnek oranı ≥ %80; ofset std ≤ 6.0 cm; sıcak–soğuk kesişme (uçtan 15 cm dışı) FAIL.
- T06 koridor (antre-kor. / merdiven / hol) içindeki temiz su parçası: duvara mesafe / koridor genişliği < 0.25 → FAIL.
- T07 yazı kutuları ezdxf yazı tipi ölçüsüyle; herhangi örtüşme (> 0,2 cm²) FAIL; hat yazı kutusundan ≥ 3 cm geçiyorsa FAIL; çap etiketi yüksekliği ortanca 8–12.
- T08 sayaç sembolü y ≥ 1. kat bandı çizgisi → FAIL; x daire bloklarının (D1..) solunda değilse FAIL; "SAYAÇ (KAPIDA)" yazısı FAIL.
- T09 ıslak mahal poligonunda süzgeç sembolü (çizim + mimari ızgara, 15 cm kümeli) sayısı ≠ 1 → FAIL.
- T10 kolon sembolü ıslak mahal (20 cm pay) dışında / betonarme içinde / en yakın köşeye > 45 cm → FAIL.
- T11 `motor/deneme/denetim/denetle.py` ile aynı sayılar.
- T07 ek: gerçek yazı kutusu (`kutu.py`, ezdxf text_size; hizalama + döndürme, MTEXT mtext_size); etiket kutusunun > %25'i duvar/betonarme taramasında, > %25'i eviye/B.M./mimari Ç.M./kombi/makine/aspiratör sembolünde, > %30'i asansör boşluğunda → FAIL (merdiven holü BİLGİ).
- T12 aynı numaralı kolon katlar arasında ± 5 cm; bir katta eksik ya da referans new_block'ta olmayan numara → FAIL.
- T13 çizilen Ç.M./B.M. aynı mahal/daire içindeki mimari (+ referans) yerine > 40 cm → FAIL; kolon (r 8) / aspiratör mimari makine yerine < 15 cm → FAIL.
- T14 aspiratör notu kendi ıslak hacmine (kılavuz/sembolden) > 60 cm, ortak alanda ya da başka dairede → FAIL; kılavuz başka mahal içinde > 15 cm → FAIL.
- T15 pencere etiketi (S/P nn) olmayan ıslak hacimde (mutfak ve < 1 m² duş kabini hariç) aspiratör sembolü (40 cm) ya da not (60 cm) yok → FAIL.
- T16 "(EK)", new_block, otomatik, dosya adı, kural cümlesi kalıpları (`testler2.SIZINTI`); ACI 250–255 (BYLAYER/BYBLOCK çözülmüş) ya da çok koyu gerçek renk → FAIL (WIPEOUT hariç).
- T17 pafta genişliği referansın ± %5'i; tam şeritte (≥ 5 pafta) eksik / sırasız / tanımsız pafta → FAIL.
