# Ada Hayat — AVM + Belediye Hizmet Binası Mekanik Projeleri (Adapazarı, 09.06.2026 / metraj 10.06.2026)

Kaynak: kullanıcının gönderdiği Ada Hayat AVM–Belediye mekanik proje seti (GÖK-AY Proje Mühendislik). Gelen DWG'ler: ısıtma-soğutma planları, havalandırma planları ve 9 kolon/akım şeması. **Temiz su, pis su ve yangın kat planı DWG'leri sette yok** (pafta listesinde 100/200/500 serisi var; plan DWG'lerinde ilgili katmanlar dondurulmuş halde mevcut, ör. `-M-YNGN-ZON1-SPR`, `Y-SPRINKLER-UPRIGHT-Standart`).

Pafta düzeni: model uzayında yan yana paftalar; dış çerçeve 25000×20000 (katman `1-BASLIK`, blok `UP_ANTET_01`), çizim alanı 21900×19600, sağda 2500×19600 dikey antet sütunu, antet altında 2300×1200 pafta no kutusu. Kolon şemalarında çerçeve genişliği değişken (30 234–61 291 × 8200 veya 49 034–57 324 × 20000). Pafta numaralandırma (Mekanik_Pafta_Listesi.xls): 100 temiz su, 200 pis su, 300 ısıtma-soğutma, 400 havalandırma, 500 yangın; her seride x00 vaziyet, x01 çatı, x02 3. kat, x03 2A kat, x04 2. kat, x05 1. kat, x06 zemin, x07 1. bodrum, x08 2. bodrum; şemalar 109-110, 209-210, 309-312, 509. CTB: GOKAY-BLACK.ctb, GOKAY-COLOURED.ctb.

## Klasör yapısı
- `dwg/` orijinal DWG'ler (değiştirilmeden, okunur adla)
- `belge/` orijinal XLS/DOC (+ .doc'lardan çıkarılmış `_metin.txt`)
- `onizleme/<dosya>_<n>.png` her pafta / içerik grubu için önizleme (≤3000 px)
- `lejant/<dosya>_lejant_<n>.png` + `.txt` lejant/sembol tabloları ve satır metinleri
- `sema/<dosya>_sema_<n>.png` kolon/akım şeması, izometri içeren paftalar (≤4000 px)
- `hesap/` XLS sayfalarının CSV dökümü + `<dosya>_notlar.txt` (DWG içi not/hesap metinleri)

Önizlemeler model uzayından yeniden çizilmiştir (LibreDWG→DXF→düzleştirme); kapalı/dondurulmuş katmanlar gizlenmiştir, yazılar sola hizalı basitleştirilmiş gösterimdir, tarama (hatch) ve çizgi tipleri yoktur. Ölçü için her zaman orijinal DWG kullanılmalıdır.

## Dosyalar

| DWG | Boyut | Orijinal ad | Pafta/grup | Lejant | Şema |
|---|---|---|---|---|---|
| `dwg/01_Isitma_Sogutma_Tesisat_Planlari.dwg` | 30.1 MB | ISITMA - SOĞUTMA TESİSAT PLANLARI.dwg | 16 | 3 | 0 |
| `dwg/02_Havalandirma_Tesisat_Planlari.dwg` | 29.5 MB | HAVALANDIRMA TESİSAT PLANLARI.dwg | 13 | 2 | 0 |
| `dwg/10_AVM_Isitma_Sogutma_Kolon_Semasi.dwg` | 0.7 MB | AVM Isıtma-Soğutma Kolon Şeması.dwg | 1 | 1 | 1 |
| `dwg/11_Belediye_Isitma_Sogutma_Kolon_Semasi.dwg` | 0.7 MB | Belediye Isıtma-Soğutma Kolon Şeması.dwg | 1 | 1 | 1 |
| `dwg/12_AVM_Belediye_Isitma_Sogutma_Akim_Semasi.dwg` | 1.2 MB | Avm - Belediye Isıtma-Soğutma Akım Seması.dwg | 1 | 1 | 1 |
| `dwg/13_WSHP_Kolon_Semasi.dwg` | 0.6 MB | WSHP Kolon Şeması.dwg | 2 | 1 | 2 |
| `dwg/14_AVM_Temizsu_Kolon_Semasi.dwg` | 0.6 MB | AVM Temizsu Kolon Şeması.dwg | 2 | 1 | 1 |
| `dwg/15_Belediye_Temizsu_Kolon_Semasi.dwg` | 43.6 MB | Belediye Temizsu Kolon Şeması.dwg | 2 | 1 | 1 |
| `dwg/16_AVM_Pissu_Kolon_Semasi.dwg` | 0.8 MB | AVM Pissu Kolon Şeması.dwg | 2 | 1 | 1 |
| `dwg/17_Belediye_Pissu_Kolon_Semasi.dwg` | 40.8 MB | Belediye Pissu Kolon Şeması.dwg | 2 | 1 | 1 |
| `dwg/18_Yangin_Tesisati_Kolon_Semasi.dwg` | 0.7 MB | Yangın Tesisatı Kolon Şeması.dwg | 1 | 1 | 1 |

Belgeler:

- `belge/01_Kapak_Ihale_Dosyasi.doc` (0.0 MB)
- `belge/01_Kapak_Ihale_Dosyasi_metin.txt` (0.0 MB)
- `belge/02_Icmal_On_Sayfa.xls` (0.2 MB)
- `belge/03_Sihhi_Tesisat_Metraji_AVM_Belediye.xls` (0.1 MB)
- `belge/04_Yangin_Tesisati_Metraji_AVM_Belediye.xls` (0.1 MB)
- `belge/05_Isitma_Sogutma_Metraji_AVM.xls` (0.2 MB)
- `belge/05_Isitma_Sogutma_Metraji_Belediye.xls` (0.1 MB)
- `belge/06_Havalandirma_Metraji_AVM.xls` (0.2 MB)
- `belge/06_Havalandirma_Metraji_Belediye.xls` (0.1 MB)
- `belge/10_Kapak_Teknik_Sartname.doc` (0.0 MB)
- `belge/10_Kapak_Teknik_Sartname_metin.txt` (0.0 MB)
- `belge/11_Teknik_Sartname.doc` (0.2 MB)
- `belge/11_Teknik_Sartname_metin.txt` (0.1 MB)
- `belge/GOKAY-BLACK.ctb` (0.0 MB)
- `belge/GOKAY-COLOURED.ctb` (0.0 MB)
- `belge/Mekanik_Pafta_Listesi.xls` (0.0 MB)

Hesap CSV dökümleri (8 adet): `02_Icmal_On_Sayfa__ON_SAYFA.csv`, `03_Sihhi_Tesisat_Metraji_AVM_Belediye__METRAJ.csv`, `04_Yangin_Tesisati_Metraji_AVM_Belediye__METRAJ.csv`, `05_Isitma_Sogutma_Metraji_AVM__METRAJ.csv`, `05_Isitma_Sogutma_Metraji_Belediye__METRAJ.csv`, `06_Havalandirma_Metraji_AVM__METRAJ.csv`, `06_Havalandirma_Metraji_Belediye__METRAJ.csv`, `Mekanik_Pafta_Listesi__ADA_HAYAT.csv`

### Metraj / teknik şartnameden önemli değerler (belge/*.xls → hesap/*.csv)
| Konu | Değer |
|---|---|
| Elektrikli yangın pompası YNP-01-A/B | 2 adet, Q = 750 GPM (170 m³/h), H = 12,0 bar (174 PSI), split-case, NFPA 20, UL/FM |
| Jokey pompa YNP-02 | Q = 15 GPM (3,4 m³/h), H = 12,5 bar |
| Yangın su depoları | Galvaniz modüler: Yangın Su Deposu-1 13,5 m³ + Yangın Su Deposu-2 97,5 m³ (toplam 111 m³) |
| Kullanma suyu deposu | Paslanmaz AISI 304 modüler, 108 m³ |
| Islak alarm vanası | 8", 20,5 bar — 5 adet |
| Zon kontrol vanası (süpervizyon switchli, F1-A detayı) | DN80: 2, DN100: 5, DN125: 1, DN150: 13, DN200: 15 → toplam 36 zon; 36 test-drenaj vanası (1", drenaj 1/2"); aynı sayıda akış anahtarı |
| Sprinkler | Upright std 5144 + upright hızlı cevap 28 + pendent gizli 4284 + kafesli pendent 141 °C 10 + sidewall (K=115) 14; K=80, 1/2", 12,1 bar; 4294 flex bağlantı |
| Yangın dolabı | 108 adet; dolapta basınç ≤ 9 bar (aşılırsa orifis); itfaiye hortum vanası (basınç sınırlayıcı) 31 adet |
| Yangın boru metrajı | DN25 9262 m, DN32 3445, DN40 1365, DN50 3175, DN65 1784, DN80 939, DN100 550, DN125 432, DN150 383, DN200 902 m |
| Hidrofor HID-01 (AVM) / HID-02 (Belediye) | Toplam 15 m³/h, 60 mSS ±5; 1 asıl + 1 yedek, frekans invertörlü, 200 L tank |
| KSS sirkülasyon | 5,0 m³/h, 6,0 mSS, 1+1 |
| Pis su | PSP-01-A/B 10 m³/h–18 mSS dalgıç; PSU-01..03 transfer üniteleri 10 m³/h–12 mSS |
| AVM ısıtma | 2 × 920 kW yoğuşmalı kazan, 80/60 °C |
| AVM soğutma | 1 × 620 kW hava soğutmalı chiller, 6/11 °C %20 glikol; 2 × 1400 kW kapalı soğutma kulesi 35/30 °C (Adapazarı, 35 °C KT) |
| AVM pompalar | PH-01 A/B/C 44 m³/h–15 mSS (2+1); kule devresi PWSHP-01 A..H 72 m³/h–30 mSS (7+1) |
| AVM WSHP | WSHP-03 ×1, -07 ×20, -09 ×9, -11 ×14, -15 ×19, -22 ×18, -30 ×11 (toplam 92) |
| Belediye ısıtma/soğutma | 1 × 740 kW kazan; 1 × 1000 kW chiller; PH-01 A/B 35 m³/h–15 mSS; primer PC-01 198 m³/h–16 mSS; sekonder PC-02 A..E 48 m³/h–25 mSS (4+1) |

## 02-Yangın: sprinkler boru çapı ↔ beslenen başlık sayısı (ölçülmüş tespit)
Aselsan 02 Yangın DWG'sinde (`BORUYUK` = `-M-YNGN-BORUYUK` katmanı, 2802 yük yazısı — boru etiketinin üstündeki yük; başlık yanı yükler `-M-YNGN-SPR-YUK`, 5775 yazı) boru çapı ile o borunun beslediği sprinkler başlık sayısı karşılaştırıldı:

| Boru | Beslenen başlık sayısı |
|---|---|
| DN25 | 1–2 |
| DN32 | 3 |
| DN40 | 4–5 |
| DN50 | 6–10 |
| DN65 | 11–20 |
| DN80 | 21–40 |
| DN100 | 41–100 |
| DN125 | (kullanılmamış) |
| DN150 | 100 üstü |

Ada Hayat yangın kolon şemasında (18_Yangin_Tesisati_Kolon_Semasi) kat zon besleme çapları (zon başına sprinkler sayısı → çap): SP56–58 → DN80, SP41–98 → DN100, SP114 → DN125, SP180–275 → DN150, SP279 ve üstü → DN200 (istisna: SP256 → DN150).

Çizim dili (Aselsan 02):
- Sprinkler başlık sembolü: dik tip (upright) **tek daire Ø25**; pendent **iç içe çift daire**. Başlık yanında "25 / 1 / UP" yazıları (çap / başlık yükü / tip).
- Kolon numaraları **çift daire içinde**: SP-1, SP-2 … (sprinkler kolonu), D-1 … (drenaj kolonu).
- Boru etiketi: "DN25" biçiminde; etiketin üstünde boru yükü (beslenen başlık sayısı).
- Lejantta: sprinkler borusu, drenaj borusu, kelebek vana, izlenebilir kelebek vana, yükselen milli vana, çek vana, pislik tutucu, kompansatör, test drenaj seti, flow switch, itfaiye bağlantı ağzı 2×2 1/2", W.A.V./P.A.V./D.A.V. alarm vana istasyonları, basınç düşürücü dengeleme vanası, manometre, post indikatör vana, N.K. (normalde kapalı), tüplü yangın dolabı (TS EN 671-1, 1"/30 m yarı-sert hortum).


---
## 01_Isitma_Sogutma_Tesisat_Planlari

Orijinal: `ISITMA - SOĞUTMA TESİSAT PLANLARI.dwg` — 2338550 çizgi parçası, 13115 daire, 55520 metin; 447 katman, 228 farklı blok (model uzayı).
Kapalı/dondurulmuş katman: 229 (ör. `-M-HV-KANAL-TEXT-MM`, `-M-HVAC-E-EF-01-KNLTXT`, `-M-HVAC-E-MNF2B`, `-M-HVAC-E-MNFTXT`, `-M-HVAC-E-WC-EF-KNL2B`, `-M-HVAC-R-05-NUMARALI-RESTORAN-KNL2B`, `-M-HVAC-R-05-NUMARALI-RESTORAN-KNL2B-KNT`, `-M-HVAC-R-05-NUMARALI-RESTORAN-KNLTXT`).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_01.png` | ZEMIN KAT PLANI; (0.00 KOTU); AVM GIRIS; TERAS SIRKULASYON ALANI; AVM GIRISI; Engelli WC 4.80 m2; Engelli WC 00 m2; Merdiven Holü 00 m2; Kat Elektrik Odası 3.45 m2; Bebek Bakım O. 6.95 m2 |
| 2 | pafta | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_02.png` | (-5.00 KOTU); -1. KAT PLANI; BASKANLIK OTOPARK; TAVANDA YIRTIK; 240*200; DÖŞEMEDE YIRTIK; 200*100; TAVANDA VE DÖŞEMEDE YIRTIK; MÜZE UST KAT; ÇİFT KAT-ÇİFT YÜZ KIRMIZI ALÇIPAN VEYA A1 SINIFI ALÇIPAN +MİNERAL YÜN (EI120) |
| 3 | pafta | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_03.png` | TAZE HAVA GİRİŞİ: 65 000 m3/h; TAZE HAVA GİRİŞİ: 175 000 m3/h; -2. KAT PLANI; (-10.00 KOTU); MEYDAN; 120*40; 200*100; TAVANDA YIRTIK; digital muze kapsamında yapılacak tefrislere göre planlanmalıdır. Onay alınmaldıır.; ÇİFT KAT-ÇİFT YÜZ KIRMIZI ALÇIPAN VEYA A1 SINIFI ALÇIPAN +MİNERAL YÜN (EI120) |
| 4 | pafta | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_04.png` | D-1; D-4; VAZIYET PLANI; D-3; D-2; GEMICI MERDIVENI; VAZİYET PLANI; Mekanik; ÇİZİM SEMBOLLERİ |
| 5 | pafta | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_05.png` | D-4; D-1; ÇATI KAT PLANI; (+22.00 /+21.00 KOTU); D-3; D-2; KAZAN DAİRESİ 67.05 m²; ÖZEL KALEM DEPO; KAT OFİSİ; ÇİZİM SEMBOLLERİ |
| 6 | pafta | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_06.png` | D-1; 3. KAT PLANI; (+18.00 /+21.00 KOTU); ELEKTRİK DOLABI; D-2; D-3; JENERATÖR; Süzgeç; Kat Holü 000 m2; Kat Holü 380.95 m2 |
| 7 | pafta | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_07.png` | (+14.00 /+15.00 KOTU); TERAS; Kat Holü 000 m2; Süzgeç; BASKAN YARD. ODASI; DINLENME O.; SEKRETERYA; HUKUK ISLERI; ÇİFT KAT-ÇİFT YÜZ KIRMIZI ALÇIPAN VEYA A1 SINIFI ALÇIPAN +MİNERAL YÜN (EI120); TOPLANTI ODASI |
| 8 | pafta | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_08.png` | 2. KAT PLANI; (+10.00 KOTU); GEZILEMEYEN TERAS; TERAS 75 M2; Süzgeç; Kat Holü 000 m2; Kat Holü 285.20 m2; ERKEK WC; ARŞİV KAT İRTİFAK/MÜLKİYET ODASI; ÇİFT KAT-ÇİFT YÜZ KIRMIZI ALÇIPAN VEYA A1 SINIFI ALÇIPAN +MİNERAL YÜN (EI120) |
| 9 | pafta | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_09.png` | 1. KAT PLANI; (+5.00 KOTU); TERAS SIRKULASYON ALANI; TERAS; Süzgeç; Merdiven Holü 00 m2; Yangın Kaçıs ^JHolü 00 m2; Yangın Kaçıs Holü 00 m2; Bebek Bakım O. 10.60 m2; Kat Pano Dolabı |
| 10 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_10.png` | ÇİZİM SEMBOLLERİ; WSHP; GİZLİ TAVAN TİPİ FAN-COIL; ISITMA GİDİŞ BORUSU; KÜRESEL VANA; CEKVALF; PİSLİK TUTUCU; KELEBEK VANA |
| 11 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_11.png` | ÇİZİM SEMBOLLERİ; WSHP; GİZLİ TAVAN TİPİ FAN-COIL; ISITMA GİDİŞ BORUSU; KÜRESEL VANA; CEKVALF; PİSLİK TUTUCU; KELEBEK VANA |
| 12 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_12.png` | ÇİZİM SEMBOLLERİ; WSHP; GİZLİ TAVAN TİPİ FAN-COIL; ISITMA GİDİŞ BORUSU; KÜRESEL VANA; CEKVALF; PİSLİK TUTUCU; KELEBEK VANA |
| 13 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_13.png` | — |
| 14 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_14.png` | — |
| 15 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_15.png` | — |
| 16 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisat_Planlari_16.png` | — |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/01_Isitma_Sogutma_Tesisat_Planlari_lejant_01.png`, `lejant/01_Isitma_Sogutma_Tesisat_Planlari_lejant_01.txt`

> KÜRESEL VANA · KELEBEK VANA · CEKVALF · PİSLİK TUTUCU · ISITMA GİDİŞ BORUSU · ISITMA DÖNÜŞ BORUSU · SOĞUTMA GİDİŞ BORUSU · SOĞUTMA DÖNÜŞ BORUSU · WSHP SOĞUTMA GİDİŞ BORUSU · WSHP SOĞUTMA DÖNÜŞ BORUSU · DRENAJ BORUSU · BRANŞMAN · GİZLİ TAVAN TİPİ FAN-COIL · WSHP \| WATER SOURCE HEAT PUMP

**ÇİZİM SEMBOLLERİ** — `lejant/01_Isitma_Sogutma_Tesisat_Planlari_lejant_02.png`, `lejant/01_Isitma_Sogutma_Tesisat_Planlari_lejant_02.txt` (aynı lejant 6 kez daha tekrar ediyor)

> ÇİZİM SEMBOLLERİ · 0.3 · KÜRESEL VANA · 140.00 \| 500 \| 0.00 \| 15.00 \| 3D-MN1-2510 \| 0.00 · KELEBEK VANA · 60 \| 13.5 \| 13.5 \| 7 \| 0 \| 3D-NZ1-135 \| CEKVALF · PİSLİK TUTUCU · ISITMA GİDİŞ BORUSU · 1 \| 0.3 · ISITMA DÖNÜŞ BORUSU · P1 · SOĞUTMA GİDİŞ BORUSU · 0.3 · SOĞUTMA DÖNÜŞ BORUSU · WSHP SOĞUTMA GİDİŞ BORUSU · WSHP SOĞUTMA DÖNÜŞ BORUSU · DRENAJ BORUSU · BRANŞMAN · GİZLİ TAVAN TİPİ FAN-COIL · WSHP \| WATER SOURCE HEAT PUMP

**ÇİZİM SEMBOLLERİ** — `lejant/01_Isitma_Sogutma_Tesisat_Planlari_lejant_03.png`, `lejant/01_Isitma_Sogutma_Tesisat_Planlari_lejant_03.txt`

> ÇİZİM SEMBOLLERİ · 0.3 · KÜRESEL VANA · 140.00 \| 500 \| 0.00 \| 15.00 \| 3D-MN1-2510 \| 0.00 · KELEBEK VANA · 60 \| 13.5 \| 13.5 \| 7 \| 0 \| 3D-NZ1-135 \| CEKVALF · PİSLİK TUTUCU · ISITMA GİDİŞ BORUSU · 1 \| 0.3 · ISITMA DÖNÜŞ BORUSU · SOĞUTMA GİDİŞ BORUSU · 0.3 · SOĞUTMA DÖNÜŞ BORUSU · WSHP SOĞUTMA GİDİŞ BORUSU · WSHP SOĞUTMA DÖNÜŞ BORUSU · DRENAJ BORUSU · BRANŞMAN · GİZLİ TAVAN TİPİ FAN-COIL · WSHP \| WATER SOURCE HEAT PUMP


### Boru/kanal çapı yazım biçimi

- Øxx: 2251 metin — ör. "D-Ø32 PPRC", "I-1639 W-Ø20", "I-2283 W-Ø20", "D-Ø50 PPRC", "S-2458 W-Ø20", "D-Ø40 PPRC", "S-2826 W-Ø20", "I-1330 W-Ø20"
- xx/yy (kanal ölçüsü): 1369 metin — ör. "80/80", "1800x150", "1400x150", "1200x150", "300x150", "90/90", "120/80", "900x150"
- xx" (inç): 19 metin — ör. "8"", "P9""
- PE/PPR dxx: 3 metin — ör. "B-C-PE-01", "AVM-C-PE-01", "AVM-H-PE-01"

Not/hesap metinleri: `hesap/01_Isitma_Sogutma_Tesisat_Planlari_notlar.txt` (102 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `T-FC-TAVAN` (237132), `H-FC-TAVAN` (222370), `-M-HVAC-S-MNF2B` (170497), `PEYZAJ_YESIL_OYARC` (158700), `TEFRIS_OYARC` (137775), `H-CIHAZ` (99577), `OYARC_Tefris` (86727), `1-CIHAZ` (86514), `DNY_TEFRIS` (69967), `TEFRIS` (56992), `DNY REV DUVAR SAFT` (32562), `H-FC-VM` (31720), `YOL_OYARC` (24766), `ANA_CIZGI-1` (22560), `YAZI_OYARC` (21671), `METAL_OYARC` (18774), `TARAMA_OYARC` (15233), `ST-BATARYA` (12642), `Y-TEXT` (12225), `M_Yazı_3` (10971), `0` (10366), `CAM_OYARC` (9330), `-M-HV-MNF-TIP` (8968), `-M-HV-KANAL-TEXT` (8078), `UP_KAPI` (7286), `A_Tefrıs` (7102), `M_Kiriş_3` (7018), `SP-SUZGEC` (6270), `Y-VANA` (6177), `SLAD-THINLINE` (5796), `YURUYENMERD_OYARC` (5173), `-M-HVAC-R-MNF2B` (4996), `M_Kolon_3` (4770), `ARAC_OYARC` (4654), `Y-SPRINKLER-UPRIGHT-Standart` (4360), `SPRKDATA` (4029), `-M-SPRINKLER-CAPCIZGISI` (4025), `SPRKDAT1` (3995), `Y1-KORUMAALANI` (3963), `H-FC-V-FLEXIBLE` (3631)

Bloklar (model uzayı INSERT sayısı): `DEBI001` (1125), `DEBI110` (973), `*U` (596), `Z1` (244), `ZA1` (228), `YTF7Y` (222), `A$C017C623E` (212), `TEFRİŞ_dwg_622_UYG_1_bodrum kat plan$0$A$C9aefd69a-1352686-BASEMENT` (205), `A$C6589735B` (184), `UKFYUK` (160), `2D-LDB-20-8-4-1250` (159), `A$C4E3078E5` (144), `2D-LDB-20-8-4-500` (129), `2D-LDB-20-8-4-1500` (128), `DDFGHVJ K` (112), `A$C6F6E1246` (110), `A$C6DCA0322` (110), `A$C7f0dea59` (94), `PN-2` (89), `2D-EM5-030015` (81), `ÖMDSZEGSDFDGH` (78), `KN` (75), `2D-EM5-140015` (63), `2D-EM5-180015` (61), `2D-EM5-120015` (54), `KURESEL_VANA` (48), `TYRETWRS` (44), `YTFHDSALKŞLKJHGF` (44), `2D-LDB-20-8-4-750` (39), `2D-EM5-090015` (38), `SN` (33), `0_tefris_ayna_wc_belediye_80R` (28), `Kesme` (23), `ES-MDVTB-00` (22), `2D-LDB-20-8-4-2000` (22), `A$C0B325108` (21), `Spot Elevations - M_Spot Elevation - Target Filled-23738-TEKNOKENT 3_ KAT` (18), `2D-LDB-20-8-4-1000` (17), `A$Ca4e1aa19` (17), `A$C9e01fd04` (15)
</details>


---
## 02_Havalandirma_Tesisat_Planlari

Orijinal: `HAVALANDIRMA TESİSAT PLANLARI.dwg` — 2725430 çizgi parçası, 16140 daire, 56719 metin; 447 katman, 227 farklı blok (model uzayı).
Kapalı/dondurulmuş katman: 98 (ör. `-M-HV-KANAL-TEXT-MM`, `-M-YNGN-SPR`, `-M-YNGN-ZON1`, `-M-YNGN-ZON1-CAP`, `-M-YNGN-ZON1-SPR`, `-M-YNGN-ZON2`, `-M-YNGN-ZON2-CAP`, `-M-YNGN-ZON2-SPR`).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/02_Havalandirma_Tesisat_Planlari_01.png` | ZEMIN KAT PLANI; (0.00 KOTU); AVM GIRIS; TERAS SIRKULASYON ALANI; AVM GIRISI; Engelli WC 4.80 m2; Engelli WC 00 m2; Merdiven Holü 00 m2; Kat Elektrik Odası 3.45 m2; Bebek Bakım O. 6.95 m2 |
| 2 | pafta | `onizleme/02_Havalandirma_Tesisat_Planlari_02.png` | (-5.00 KOTU); -1. KAT PLANI; BASKANLIK OTOPARK; TAVANDA YIRTIK; 240*200; DÖŞEMEDE YIRTIK; 200*100; TAVANDA VE DÖŞEMEDE YIRTIK; MÜZE UST KAT; ÇİFT KAT-ÇİFT YÜZ KIRMIZI ALÇIPAN VEYA A1 SINIFI ALÇIPAN +MİNERAL YÜN (EI120) |
| 3 | pafta | `onizleme/02_Havalandirma_Tesisat_Planlari_03.png` | TAZE HAVA GİRİŞİ: 65 000 m3/h; TAZE HAVA GİRİŞİ: 175 000 m3/h; -2. KAT PLANI; (-10.00 KOTU); MEYDAN; 120*40; 200*100; TAVANDA YIRTIK; digital muze kapsamında yapılacak tefrislere göre planlanmalıdır. Onay alınmaldıır.; ÇİFT KAT-ÇİFT YÜZ KIRMIZI ALÇIPAN VEYA A1 SINIFI ALÇIPAN +MİNERAL YÜN (EI120) |
| 4 | pafta | `onizleme/02_Havalandirma_Tesisat_Planlari_04.png` | D-1; D-4; VAZIYET PLANI; D-3; D-2; GEMICI MERDIVENI; VAZİYET PLANI; Mekanik |
| 5 | pafta | `onizleme/02_Havalandirma_Tesisat_Planlari_05.png` | D-4; D-1; ÇATI KAT PLANI; (+22.00 /+21.00 KOTU); D-3; D-2; KAZAN DAİRESİ 67.05 m²; ÖZEL KALEM DEPO; KAT OFİSİ; ÇİZİM SEMBOLLERİ |
| 6 | pafta | `onizleme/02_Havalandirma_Tesisat_Planlari_06.png` | D-1; 3. KAT PLANI; (+18.00 /+21.00 KOTU); ELEKTRİK DOLABI; D-2; D-3; JENERATÖR; Süzgeç; Kat Holü 000 m2; Kat Holü 380.95 m2 |
| 7 | pafta | `onizleme/02_Havalandirma_Tesisat_Planlari_07.png` | (+14.00 /+15.00 KOTU); TERAS; Kat Holü 000 m2; Süzgeç; BASKAN YARD. ODASI; DINLENME O.; SEKRETERYA; HUKUK ISLERI; ÇİFT KAT-ÇİFT YÜZ KIRMIZI ALÇIPAN VEYA A1 SINIFI ALÇIPAN +MİNERAL YÜN (EI120); ÇİZİM SEMBOLLERİ |
| 8 | pafta | `onizleme/02_Havalandirma_Tesisat_Planlari_08.png` | 2. KAT PLANI; (+10.00 KOTU); GEZILEMEYEN TERAS; TERAS 75 M2; Süzgeç; Kat Holü 000 m2; Kat Holü 285.20 m2; ERKEK WC; ARŞİV KAT İRTİFAK/MÜLKİYET ODASI; ÇİFT KAT-ÇİFT YÜZ KIRMIZI ALÇIPAN VEYA A1 SINIFI ALÇIPAN +MİNERAL YÜN (EI120) |
| 9 | pafta | `onizleme/02_Havalandirma_Tesisat_Planlari_09.png` | 1. KAT PLANI; (+5.00 KOTU); TERAS SIRKULASYON ALANI; TERAS; Süzgeç; Merdiven Holü 00 m2; Yangın Kaçıs ^JHolü 00 m2; Yangın Kaçıs Holü 00 m2; Bebek Bakım O. 10.60 m2; Kat Pano Dolabı |
| 10 | serbest grup | `onizleme/02_Havalandirma_Tesisat_Planlari_10.png` | — |
| 11 | serbest grup | `onizleme/02_Havalandirma_Tesisat_Planlari_11.png` | — |
| 12 | serbest grup | `onizleme/02_Havalandirma_Tesisat_Planlari_12.png` | — |
| 13 | serbest grup | `onizleme/02_Havalandirma_Tesisat_Planlari_13.png` | — |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/02_Havalandirma_Tesisat_Planlari_lejant_01.png`, `lejant/02_Havalandirma_Tesisat_Planlari_lejant_01.txt` (aynı lejant 6 kez daha tekrar ediyor)

> 140.00 \| 500 \| 0.00 \| 15.00 \| 3D-MN1-2510 \| 0.00 \| EMİCİ LİNEER MENFEZ \| 1 \| 0.3 · P1 · 0.3 · 60 \| 13.5 \| 13.5 \| 7 \| 0 \| 3D-NZ1-135 \| GEMİCİ ANEMOSTATI · VD \| VOLUM DAMPERİ · YANGIN DAMPERİ · EMİCİ FLEXIBLE · Sp1 · TD1

**ÇİZİM SEMBOLLERİ** — `lejant/02_Havalandirma_Tesisat_Planlari_lejant_02.png`, `lejant/02_Havalandirma_Tesisat_Planlari_lejant_02.txt`

> 140.00 \| 500 \| 0.00 \| 15.00 \| 3D-MN1-2510 \| 0.00 \| EMİCİ LİNEER MENFEZ \| 1 \| 0.3 · 0.3 · 60 \| 13.5 \| 13.5 \| 7 \| 0 \| 3D-NZ1-135 \| GEMİCİ ANEMOSTATI · VD \| VOLUM DAMPERİ · YANGIN DAMPERİ · EMİCİ FLEXIBLE · Sp1 · TD1


### Boru/kanal çapı yazım biçimi

- Øxx: 1565 metin — ör. "Ø20", "Ø15.2", "Ø300", "Ø11.2", "Ø31.5", "Ø12.7", "Ø200", "Ø25.4"
- xx/yy (kanal ölçüsü): 1369 metin — ör. "80/80", "1800x150", "1400x150", "1200x150", "300x150", "90/90", "120/80", "900x150"
- PE/PPR dxx: 5 metin — ör. "Ø100 HDPE BORU", "Ø63 HDPE", "B-C-PE-01", "AVM-C-PE-01", "AVM-H-PE-01"
- xx" (inç): 3 metin — ör. "P9""

Not/hesap metinleri: `hesap/02_Havalandirma_Tesisat_Planlari_notlar.txt` (102 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `T-FC-TAVAN` (229113), `H-FC-TAVAN` (222343), `-M-HVAC-S-MNF2B` (170497), `PEYZAJ_YESIL_OYARC` (158700), `TEFRIS_OYARC` (137775), `H-CIHAZ` (99577), `OYARC_Tefris` (86727), `1-CIHAZ` (86514), `DNY_TEFRIS` (69967), `TEFRIS` (56992), `DNY REV DUVAR SAFT` (32562), `H-FC-VM` (31720), `YOL_OYARC` (24766), `ANA_CIZGI-1` (22560), `YAZI_OYARC` (21671), `METAL_OYARC` (18774), `TARAMA_OYARC` (15233), `ST-BATARYA` (12642), `Y-TEXT` (12225), `M_Yazı_3` (10971), `0` (10366), `CAM_OYARC` (9330), `-M-HV-MNF-TIP` (8968), `-M-HV-KANAL-TEXT` (8078), `UP_KAPI` (7286), `A_Tefrıs` (7102), `M_Kiriş_3` (7018), `SP-SUZGEC` (6270), `Y-VANA` (6177), `SLAD-THINLINE` (5796), `YURUYENMERD_OYARC` (5173), `-M-HVAC-R-MNF2B` (4996), `M_Kolon_3` (4770), `ARAC_OYARC` (4654), `Y-SPRINKLER-UPRIGHT-Standart` (4360), `SPRKDATA` (4029), `-M-SPRINKLER-CAPCIZGISI` (4025), `SPRKDAT1` (3995), `Y1-KORUMAALANI` (3963), `H-FC-V-FLEXIBLE` (3631)

Bloklar (model uzayı INSERT sayısı): `DEBI001` (1125), `DEBI110` (973), `*U` (596), `Z1` (244), `ZA1` (228), `YTF7Y` (222), `A$C017C623E` (212), `TEFRİŞ_dwg_622_UYG_1_bodrum kat plan$0$A$C9aefd69a-1352686-BASEMENT` (205), `A$C6589735B` (184), `UKFYUK` (160), `2D-LDB-20-8-4-1250` (159), `A$C4E3078E5` (144), `2D-LDB-20-8-4-500` (129), `2D-LDB-20-8-4-1500` (128), `DDFGHVJ K` (112), `A$C6F6E1246` (110), `A$C6DCA0322` (110), `A$C7f0dea59` (94), `PN-2` (89), `2D-EM5-030015` (81), `ÖMDSZEGSDFDGH` (78), `KN` (75), `2D-EM5-140015` (63), `2D-EM5-180015` (61), `2D-EM5-120015` (54), `KURESEL_VANA` (48), `TYRETWRS` (44), `YTFHDSALKŞLKJHGF` (44), `2D-LDB-20-8-4-750` (39), `2D-EM5-090015` (38), `SN` (33), `0_tefris_ayna_wc_belediye_80R` (28), `Kesme` (23), `ES-MDVTB-00` (22), `2D-LDB-20-8-4-2000` (22), `A$C0B325108` (21), `Spot Elevations - M_Spot Elevation - Target Filled-23738-TEKNOKENT 3_ KAT` (18), `2D-LDB-20-8-4-1000` (17), `A$Ca4e1aa19` (17), `A$C9e01fd04` (15)
</details>


---
## 10_AVM_Isitma_Sogutma_Kolon_Semasi

Orijinal: `AVM Isıtma-Soğutma Kolon Şeması.dwg` — 11592 çizgi parçası, 22 daire, 2381 metin; 27 katman, 18 farklı blok (model uzayı).
Kapalı/dondurulmuş katman: 1 (ör. `H-FC-TAVAN`).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/10_AVM_Isitma_Sogutma_Kolon_Semasi_01.png` | ISITMA - SOĞUTMA KOLON ŞEMASI; Mekanik; ÇİZİM SEMBOLLERİ; FANCOIL; A DETAYI; TİPİK FANCOIL BORU BAĞLANTI DETAYI; (GİZLİ TAVAN TİPİ); GİZLİ TAVAN TİPİ FAN-COIL; 1.BODRUM KAT; ZEMİN KAT |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/10_AVM_Isitma_Sogutma_Kolon_Semasi_lejant_01.png`, `lejant/10_AVM_Isitma_Sogutma_Kolon_Semasi_lejant_01.txt`

> KÜRESEL VANA · KELEBEK VANA · CEKVALF · PİSLİK TUTUCU · ISITMA GİDİŞ BORUSU · ISITMA DÖNÜŞ BORUSU · SOĞUTMA GİDİŞ BORUSU · SOĞUTMA DÖNÜŞ BORUSU · WSHP SOĞUTMA GİDİŞ BORUSU · WSHP SOĞUTMA DÖNÜŞ BORUSU · DRENAJ BORUSU · BRANŞMAN · GİZLİ TAVAN TİPİ FAN-COIL


### Şemalar

- `sema/10_AVM_Isitma_Sogutma_Kolon_Semasi_sema_01.png` — ISITMA - SOĞUTMA KOLON ŞEMASI; AKIM ŞEMASINA BAKINIZ. Sık metinler: D-Ø32 PPRC, I-2283 W, I-1639 W, FCU-641, S-2458 W, D-Ø50 PPRC, FCU-741, S-3165 W, I-2283 W-Ø20, I-2719 W, S-3485 W, FCU-831, I-1639 W-Ø20, S-2826 W, FCU-731, S-2458 W-Ø20, S-3165 W-Ø20, 2M17, I-2719 W-Ø20, I-1330 W, S-3485 W-Ø20, S-2826 W-Ø20, I-4566 W-Ø20, FCU-431, I-2882 W

### Boru/kanal çapı yazım biçimi

- Øxx: 1008 metin — ör. "D-Ø32 PPRC", "D-Ø50 PPRC", "I-2283 W-Ø20", "I-1639 W-Ø20", "S-2458 W-Ø20", "S-3165 W-Ø20", "I-2719 W-Ø20", "S-3485 W-Ø20"
- xx" (inç): 10 metin — ör. "-BAĞLANTIDA KULLANILAN 21/2" v", "-BAĞLANTIDA KULLANILAN 2" ve A", "21/2" ve ÜSTÜ ÇAPLARDAKİ VANAL", "- 2" ve ALTI ÇAPLARDAKİ VANALA"

Not/hesap metinleri: `hesap/10_AVM_Isitma_Sogutma_Kolon_Semasi_notlar.txt` (2 tekil metin, 3 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `T-FC` (5581), `T-ISITMA` (928), `T-SOGUTMA` (891), `T-SOGUTMA-TOPLAMA` (784), `T-DTEXT` (707), `T-ISITMA-TOPLAMA` (695), `T-FC-TAVAN` (677), `T-VANA` (473), `T-DRENAJ` (431), `T-STEXT` (352), `T-ITEXT` (325), `T-MAHAL` (310), `T-FC-NUMARA` (310), `T-TEXT` (149), `T-GIDIS-ITEXT-TOPLAMA` (132), `T-SOGUTMA-VANA` (41), `T-ISITMA-VANA` (38), `T-LEGEND-TURKCE` (32), `T-CIHAZ` (13), `1-BASLIK` (9), `0` (8), `T-SUZGEC` (3), `1-CIHAZ-NO` (3), `T-CIHAZ-NO` (3), `T-BASLIK` (2), `T-WSHP-BORUSU` (2), `T-BRANSMAN` (1)

Bloklar (model uzayı INSERT sayısı): `FANCOIL-DWD` (310), `A$C116709ED` (18), `A$C58602E55` (12), `Kesme` (8), `A$C66D47B88` (6), `A$C6A526119` (6), `A$C22F205D8` (5), `ym dtfn` (5), `A$C5A364F84` (4), `A$C71446B59` (4), `A$C7F461CA1` (3), `A$C52EE5F1D` (3), `A$C20EE622A` (3), `A$C58656B13` (3), `A$C08A77AC0` (3), `SUZ` (1), `logo` (1), `A$C7b35566f` (1)
</details>


---
## 11_Belediye_Isitma_Sogutma_Kolon_Semasi

Orijinal: `Belediye Isıtma-Soğutma Kolon Şeması.dwg` — 12126 çizgi parçası, 24 daire, 2515 metin; 27 katman, 20 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/11_Belediye_Isitma_Sogutma_Kolon_Semasi_01.png` | ISITMA - SOĞUTMA KOLON ŞEMASI; Mekanik; ÇİZİM SEMBOLLERİ; FANCOIL; A DETAYI; TİPİK FANCOIL BORU BAĞLANTI DETAYI; (GİZLİ TAVAN TİPİ); GİZLİ TAVAN TİPİ FAN-COIL; 1.BODRUM KAT; ZEMİN KAT |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/11_Belediye_Isitma_Sogutma_Kolon_Semasi_lejant_01.png`, `lejant/11_Belediye_Isitma_Sogutma_Kolon_Semasi_lejant_01.txt`

> KÜRESEL VANA · KELEBEK VANA · CEKVALF · PİSLİK TUTUCU · ISITMA GİDİŞ BORUSU · ISITMA DÖNÜŞ BORUSU · SOĞUTMA GİDİŞ BORUSU · SOĞUTMA DÖNÜŞ BORUSU · WSHP SOĞUTMA GİDİŞ BORUSU · WSHP SOĞUTMA DÖNÜŞ BORUSU · DRENAJ BORUSU · BRANŞMAN · GİZLİ TAVAN TİPİ FAN-COIL


### Şemalar

- `sema/11_Belediye_Isitma_Sogutma_Kolon_Semasi_sema_01.png` — ISITMA - SOĞUTMA KOLON ŞEMASI; AKIM ŞEMASINA BAKINIZ. Sık metinler: D-Ø32 PPRC, I-1639 W, I-2283 W, S-2458 W, FCU-641, I-1639 W-Ø20, I-1330 W, S-2826 W, I-2283 W-Ø20, FCU-731, FCU-531, FCU-631, S-1679 W, S-2047 W, S-2458 W-Ø20, D-Ø50 PPRC, S-2826 W-Ø20, S-3165 W, FCU-741, I-1330 W-Ø20, D-Ø40 PPRC, S-1679 W-Ø20, I-2719 W, S-3485 W, FCU-831

### Boru/kanal çapı yazım biçimi

- Øxx: 1041 metin — ör. "D-Ø32 PPRC", "I-1639 W-Ø20", "I-2283 W-Ø20", "S-2458 W-Ø20", "D-Ø50 PPRC", "S-2826 W-Ø20", "I-1330 W-Ø20", "D-Ø40 PPRC"
- xx" (inç): 10 metin — ör. "-BAĞLANTIDA KULLANILAN 21/2" v", "-BAĞLANTIDA KULLANILAN 2" ve A", "21/2" ve ÜSTÜ ÇAPLARDAKİ VANAL", "- 2" ve ALTI ÇAPLARDAKİ VANALA"

Not/hesap metinleri: `hesap/11_Belediye_Isitma_Sogutma_Kolon_Semasi_notlar.txt` (2 tekil metin, 3 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `T-FC` (5941), `T-ISITMA` (928), `T-SOGUTMA-TOPLAMA` (895), `T-SOGUTMA` (891), `T-ISITMA-TOPLAMA` (831), `T-DTEXT` (750), `T-FC-TAVAN` (677), `T-VANA` (473), `T-DRENAJ` (433), `T-STEXT` (382), `T-ITEXT` (342), `T-MAHAL` (329), `T-FC-NUMARA` (328), `T-TEXT` (163), `T-SOGUTMA-VANA` (41), `T-ISITMA-VANA` (38), `T-LEGEND-TURKCE` (32), `T-CIHAZ` (23), `T-GIDIS-ITEXT-TOPLAMA` (12), `0` (9), `1-BASLIK` (9), `T-CIHAZ-NO` (7), `T-SUZGEC` (6), `1-CIHAZ-NO` (3), `T-BASLIK` (2), `T-WSHP-BORUSU` (2), `T-BRANSMAN` (1)

Bloklar (model uzayı INSERT sayısı): `FANCOIL-DWD` (330), `Kesme` (20), `A$C116709ED` (18), `A$C58602E55` (12), `A$C66D47B88` (6), `A$C6A526119` (6), `A$C22F205D8` (5), `ym dtfn` (5), `A$C5A364F84` (4), `A$C71446B59` (4), `A$C7F461CA1` (3), `A$C52EE5F1D` (3), `A$C20EE622A` (3), `A$C58656B13` (3), `A$C08A77AC0` (3), `KN` (2), `SUZ` (2), `DR1` (2), `logo` (1), `A$C7b35566f` (1)
</details>


---
## 12_AVM_Belediye_Isitma_Sogutma_Akim_Semasi

Orijinal: `Avm - Belediye Isıtma-Soğutma Akım Seması.dwg` — 21552 çizgi parçası, 265 daire, 591 metin; 21 katman, 39 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/12_AVM_Belediye_Isitma_Sogutma_Akim_Semasi_01.png` | BELEDİYE; AVM; ISITMA - SOĞUTMA AKIM ŞEMASI; Mekanik; B-K-01; B-H-GK-01; B-H-EMV-01; B-H-KIV-01; ÇATI KATI ( +21.00 KOTU ); ÇATI KATI ( +22.00 KOTU ) |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/12_AVM_Belediye_Isitma_Sogutma_Akim_Semasi_lejant_01.png`, `lejant/12_AVM_Belediye_Isitma_Sogutma_Akim_Semasi_lejant_01.txt`

> KÜRESEL VANA · KELEBEK VANA · BALANS VANASI · ÖZEL KİLİTLİ VANA · CEKVALF · PİSLİK TUTUCU · T · TERMOMETRE (0-120°C-ISITMA DEVRESİ) · T · TERMOMETRE (0-50°C-SOĞUTMA DEVRESİ) · M · MANOMETRE · KOLLEKTÖR BOŞALTMA · İKİ YOLLU VANA · ÜÇ YOLLU VANA · S · SOLENOİD VANA · AŞIRI BASINÇ VANASI · EMNİYET VENTİLİ · OTOMATİK HAVA ATMA CİHAZI · REDÜKSİYON · TİTREŞİM ABSORBERİ · SU SAYACI · SABİT NOKTA · SİRKÜLASYON POMPASI · KOLLEKTÖR · ISITMA GİDİŞ BORUSU · ISITMA DÖNÜŞ BORUSU · SOĞUTMA GİDİŞ BORUSU · SOĞUTMA DÖNÜŞ BORUSU · DRENAJ BORUSU


### Şemalar

- `sema/12_AVM_Belediye_Isitma_Sogutma_Akim_Semasi_sema_01.png` — ISITMA - SOĞUTMA AKIM ŞEMASI; KOLON ŞEMASINA BAKINIZ.. Sık metinler: Ø15, Ø40, Ø150, Ø200, EMNİYET VENTİLİ, GENLEŞME KABI, KİLİTLİ VANA, Ø300, SU SAYACI, KARTUŞ FİLTRE, GERİ AKIŞ ÖNLEYİCİ, OTOMATİK, Ø20, BESLEME CİHAZI - Ø15, Ø125, I-738545 W-Ø100, Ø25, S-1000000 W-Ø200, S-620000 W-Ø150, SOĞUTMA TESİSATI SU DOLUM, SOĞUTMA POMPALARI, S-1008875 W-Ø200, ( Armatürler : Ø125 ), S-655998 W-Ø150, I-912461 W-Ø125

### Boru/kanal çapı yazım biçimi

- Øxx: 233 metin — ör. "Ø15", "Ø40", "Ø150", "Ø200", "Ø300", "Ø20", "BESLEME CİHAZI - Ø15", "Ø125"
- PE/PPR dxx: 3 metin — ör. "B-C-PE-01", "AVM-C-PE-01", "AVM-H-PE-01"
- DNxx: 3 metin — ör. "DN125", "DN250", "DN32"

Not/hesap metinleri: `hesap/12_AVM_Belediye_Isitma_Sogutma_Akim_Semasi_notlar.txt` (4 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `T-CIHAZ` (8719), `T-VANA` (5995), `T-TEXT` (355), `T-SOGUTMA` (215), `T-ISITMA` (163), `T-VANA-TEXT` (158), `T-WSHP-BORUSU` (132), `ST-SU` (88), `T-CIHAZ-NO` (58), `T-LEGEND-TURKCE` (56), `T-STEXT` (40), `0` (38), `T-ITEXT` (28), `T-WSHPTEXT` (19), `1-BASLIK` (7), `T-SIRK` (5), `T-SICAK` (4), `T-ST-SU` (4), `T-ORTAK-CIHAZ` (3), `T-BASLIK` (2), `T-DRENAJ` (1)

Bloklar (model uzayı INSERT sayısı): `KELEBEK` (87), `Kesme` (84), `VANA` (73), `trmmtr` (45), `A$C52EE5F1D` (42), `uymtryduf` (42), `gfdbfcg vf` (40), `Z1` (39), `RSYJUHJHFGHGFBDSVFG` (21), `GTNZSDFGSDF` (14), `YTDBTF` (14), `A$C577C0CD0` (14), `A$C0B54677A` (14), `A$C538C06E0` (11), `A$C7E5C2832` (11), `JHMNBDFYGNHNGFTDNF` (8), `A$C2E7A051A` (8), `A$C107B4E94` (7), `A$C1EB272A8` (6), `Kuresel` (4), `UITNRXDTFYESER` (4), `A$C031019F5` (4), `UÖGYYNDBFGDVS` (3), `JNESRT` (3), `MBSDFG` (2), `BXCVBNMHGFDSAD` (2), `A$C21441314` (2), `A$C76972F96` (2), `HYJDTJ` (2), `HM DXFB SEVD` (2), `ym dtfn` (2), `BHETRBRTD` (2), `UP_ANTET_01` (1), `logo` (1), `NYXVERE` (1), `YTNGZDBFGHFB FDSS` (1), `YXRND` (1), `A$C22abf7af` (1), `A$C0B0C5AF2` (1)
</details>


---
## 13_WSHP_Kolon_Semasi

Orijinal: `WSHP Kolon Şeması.dwg` — 12836 çizgi parçası, 746 daire, 756 metin; 25 katman, 21 farklı blok (model uzayı).
Kapalı/dondurulmuş katman: 1 (ör. `H-FC-TAVAN`).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/13_WSHP_Kolon_Semasi_01.png` | SİFON İLE GİDERE BAĞLANACAKTIR.; ÇİZİM SEMBOLLERİ; A DETAYI; WSHP; TİPİK WATER SOURCE HEAT PUMP ÜNİTESİ BORU BAĞLANTI DETAYI; (YATAY, GİZLİ TAVAN TİPİ); SU SOĞUTMALI ROOFTOP KLİMA CİHAZI; BORU BAĞLANTI DETAYI; 1.BODRUM KAT; ZEMİN KAT |
| 2 | pafta | `onizleme/13_WSHP_Kolon_Semasi_02.png` | WATER SOURCE HEAT PUMP; KOLON ŞEMASI; Mekanik |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/13_WSHP_Kolon_Semasi_lejant_01.png`, `lejant/13_WSHP_Kolon_Semasi_lejant_01.txt`

> KÜRESEL VANA · KELEBEK VANA · CEKVALF · PİSLİK TUTUCU · ISITMA GİDİŞ BORUSU · ISITMA DÖNÜŞ BORUSU · SOĞUTMA GİDİŞ BORUSU · SOĞUTMA DÖNÜŞ BORUSU · WSHP SOĞUTMA GİDİŞ BORUSU · WSHP SOĞUTMA DÖNÜŞ BORUSU · DRENAJ BORUSU · BRANŞMAN · GİZLİ TAVAN TİPİ FAN-COIL · WSHP \| WATER SOURCE HEAT PUMP · SU SOĞUTMALI ROOFTOP KLİMA CİHAZI · BORU BAĞLANTI DETAYI · OTOMATİK HAVA TAHLİYE CİHAZI · PİSLİK TUTUCU · T \| M · M · BY PASS VANASI · İKİ YOLLU MOTORLU VANA \| (Normalde kapalı) · ( ON / OFF ) \| DİNAMİK BALANS VANASI · M · T · SÖKÜLEBİLİR BAĞLANTI · (Flanş veya Rakor) · SSRT · AĞZI TAPALI BOŞALTMA


### Şemalar

- `sema/13_WSHP_Kolon_Semasi_sema_01.png` — ( SOĞUTMA AKIM ŞEMASINA BAKINIZ ). Sık metinler: SİFON İLE GİDERE BAĞLANACAKTIR., D-Ø40 PPRC, D-Ø50 PPRC, S-18837 W-Ø40, S-7953 W-Ø32, S-27419 W-Ø50, S-7953 W, WSHP-07, S-18837 W, WSHP-15, S-27419 W, WSHP-22, S-14023 W-Ø40, S-14023 W, WSHP-11, S-10465 W-Ø32, S-10465 W, WSHP-09, S-36000 W, WSHP-30, S-36000 W-Ø50, S-32860 W-Ø50, DRENAJ BORUSU, S-2425569 W-Ø250, PİS SU BORUSUNA
- `sema/13_WSHP_Kolon_Semasi_sema_02.png` — KOLON ŞEMASI. Sık metinler: Mekanik, GÖK-AY PROJE MÜHENDİSLİK TİC. LTD. ŞTİ. Fener Kalamış Cad. Körfez Apt. No:17 Daire:1 Kadıköy, İst. Tel: 0216 338 84 94, WATER SOURCE HEAT PUMP, 311, KOLON ŞEMASI

### Boru/kanal çapı yazım biçimi

- Øxx: 309 metin — ör. "D-Ø40 PPRC", "D-Ø50 PPRC", "S-18837 W-Ø40", "S-7953 W-Ø32", "S-27419 W-Ø50", "S-14023 W-Ø40", "S-10465 W-Ø32", "S-36000 W-Ø50"
- xx" (inç): 6 metin — ör. "21/2" ve ÜSTÜ ÇAPLARDAKİ VANAL", "- 2" ve ALTI ÇAPLARDAKİ VANALA", "-BAĞLANTIDA KULLANILAN 21/2" v", "-BAĞLANTIDA KULLANILAN 2" ve A"

Not/hesap metinleri: `hesap/13_WSHP_Kolon_Semasi_notlar.txt` (1 tekil metin, 1 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `T-CIHAZ` (3637), `T-WSHP` (1476), `T-FC-TAVAN` (891), `T-SOGUTMA-TOPLAMA` (568), `T-VANA` (532), `T-WSHP-BORUSU` (450), `T-DTEXT` (359), `T-SOGUTMA` (214), `T-DRENAJ` (183), `T-STEXT` (107), `T-FC-NUMARA` (92), `T-FC` (91), `T-MAHAL` (85), `T-TEXT` (74), `SY-YAGMUR-SUYU-VANA` (48), `T-SOGUTMA-VANA` (41), `T-LEGEND-TURKCE` (34), `T-ISITMA` (10), `1-CIHAZ-NO` (9), `1-BASLIK` (6), `0` (4), `T-BASLIK` (3), `H-FC-TAVAN` (3), `T-CIHAZ-NO` (1), `T-BRANSMAN` (1)

Bloklar (model uzayı INSERT sayısı): `Z1` (166), `Kesme` (89), `FANCOIL-DWD` (87), `A$C0B325108` (16), `A$C116709ED` (7), `A$Cd0d47da3` (4), `A$C58602E55` (4), `A$C71446B59` (4), `A$C66D47B88` (2), `A$C6A526119` (2), `A$C22F205D8` (2), `UITNRXDTFYESER` (2), `A$C031019F5` (2), `A$C5A364F84` (2), `A$C7F461CA1` (1), `A$C52EE5F1D` (1), `A$C20EE622A` (1), `A$C58656B13` (1), `A$C08A77AC0` (1), `logo` (1), `A$C7b35566f` (1)
</details>


---
## 14_AVM_Temizsu_Kolon_Semasi

Orijinal: `AVM Temizsu Kolon Şeması.dwg` — 40581 çizgi parçası, 716 daire, 935 metin; 19 katman, 21 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/14_AVM_Temizsu_Kolon_Semasi_01.png` | ÇATI KAT PLANI; 3.KAT PLANI; 2A. KAT PLANI; 2. KAT PLANI; 1. KAT PLANI; ZEMİN KAT PLANI; 1. BODRUM KAT; 2. BODRUM KAT; 3 KAT, 78 ad x 1.25 m3 = 97.5 m3; 3 KAT, 29 ad x 1.25 m3 = 108.0 m3 |
| 2 | pafta | `onizleme/14_AVM_Temizsu_Kolon_Semasi_02.png` | AVM TEMİZ SU KOLON ŞEMASI; Mekanik; ÇİZİM SEMBOLLERİ; Ss1; KÜRESEL VANA; SICAK SU BORUSU; SOĞUK SU BORUSU; CEKVALF |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/14_AVM_Temizsu_Kolon_Semasi_lejant_01.png`, `lejant/14_AVM_Temizsu_Kolon_Semasi_lejant_01.txt`

> KÜRESEL VANA · KELEBEK VANA · CEKVALF · BASINÇ DÜŞÜRÜCÜ VANA · SU SAYACI · SOĞUK SU BORUSU · SICAK SU BORUSU · SİRKÜLASYON BORUSU · S1 \| TEMİZ SU KOLON NUMARASI · SICAK SU-SİRKÜLASYON · Ss1 · KOLON NUMARASI


### Şemalar

- `sema/14_AVM_Temizsu_Kolon_Semasi_sema_02.png` — AVM TEMİZ SU KOLON ŞEMASI. Sık metinler: Mekanik, GÖK-AY PROJE MÜHENDİSLİK TİC. LTD. ŞTİ. Fener Kalamış Cad. Körfez Apt. No:17 Daire:1 Kadıköy, İst. Tel: 0216 338 84 94, AVM TEMİZ SU KOLON ŞEMASI, 109, KÜRESEL VANA, SICAK SU BORUSU, SOĞUK SU BORUSU, ÇİZİM SEMBOLLERİ, CEKVALF, KELEBEK VANA, TEMİZ SU KOLON NUMARASI, SICAK SU-SİRKÜLASYON, Ss1, KOLON NUMARASI, SİRKÜLASYON BORUSU, BASINÇ DÜŞÜRÜCÜ VANA, SU SAYACI

### Boru/kanal çapı yazım biçimi

- xx" (inç): 13 metin — ör. "2"", "4"", "SU GİRİŞİ-2""

Not/hesap metinleri: `hesap/14_AVM_Temizsu_Kolon_Semasi_notlar.txt` (8 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `ST-ARMATUR-TEMİZSU` (11516), `ST-CIHAZ` (1441), `ST-TEMIZ-SOGUKSU-YUKBIRIMI` (1035), `ST-SU` (723), `ST-TEMIZ-CAP` (438), `ST-VANA` (304), `ST-ARMATÜR-TEMIZ-YUKBİRİMİ` (270), `ST-ARMATUR` (189), `ST-TEXT` (56), `ST-BASLIK-TEMİZSU` (35), `0` (12), `ST-CIHAZ-NO` (12), `ST-SUZGEC` (9), `1-BASLIK` (8), `ST-TEMİZSU-KOLON-NO` (5), `ST-KOLON-NO` (1), `ST-SICAK` (1), `ST-LEGEND` (1), `ST-SIRK` (1)

Bloklar (model uzayı INSERT sayısı): `LAVABO-KS` (145), `Z1` (88), `KLOZET-KS` (84), `A$Cda913a58` (40), `C10` (37), `KOT-KESIT` (8), `A$C353D6097` (5), `A$C2B514568` (4), `A$C2E285E9311111` (3), `SN` (3), `A$C0B325108` (3), `Kesme` (1), `PN123` (1), `T7FT` (1), `T6DT` (1), `TD` (1), `A$C73265755` (1), `A$C71446B59` (1), `UP_ANTET_01` (1), `logo` (1), `LEGEND TEMİZSU` (1)
</details>


---
## 15_Belediye_Temizsu_Kolon_Semasi

Orijinal: `Belediye Temizsu Kolon Şeması.dwg` — 21975 çizgi parçası, 363 daire, 764 metin; 21 katman, 35 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/15_Belediye_Temizsu_Kolon_Semasi_01.png` | 1.BODRUM KAT; ZEMİN KAT; 1. KAT; 2. KAT; 3. KAT; ÇATI; 2.BODRUM KAT; 2.A KAT; 3 KAT, 78 ad x 1.25 m3 = 97.5 m3; 3 KAT, 29 ad x 1.25 m3 = 108.0 m3 |
| 2 | pafta | `onizleme/15_Belediye_Temizsu_Kolon_Semasi_02.png` | TEMİZ SU KOLON ŞEMASI; BELEDİYE; Mekanik; ÇİZİM SEMBOLLERİ; Ss1; KÜRESEL VANA; SICAK SU BORUSU; SOĞUK SU BORUSU |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/15_Belediye_Temizsu_Kolon_Semasi_lejant_01.png`, `lejant/15_Belediye_Temizsu_Kolon_Semasi_lejant_01.txt`

> KÜRESEL VANA · KELEBEK VANA · CEKVALF · BASINÇ DÜŞÜRÜCÜ VANA · SU SAYACI · SOĞUK SU BORUSU · SICAK SU BORUSU · SİRKÜLASYON BORUSU · S1 \| TEMİZ SU KOLON NUMARASI · SICAK SU-SİRKÜLASYON · Ss1 · KOLON NUMARASI


### Şemalar

- `sema/15_Belediye_Temizsu_Kolon_Semasi_sema_02.png` — TEMİZ SU KOLON ŞEMASI. Sık metinler: Mekanik, GÖK-AY PROJE MÜHENDİSLİK TİC. LTD. ŞTİ. Fener Kalamış Cad. Körfez Apt. No:17 Daire:1 Kadıköy, İst. Tel: 0216 338 84 94, TEMİZ SU KOLON ŞEMASI, 110, KÜRESEL VANA, SICAK SU BORUSU, SOĞUK SU BORUSU, ÇİZİM SEMBOLLERİ, CEKVALF, KELEBEK VANA, TEMİZ SU KOLON NUMARASI, SICAK SU-SİRKÜLASYON, Ss1, KOLON NUMARASI, SİRKÜLASYON BORUSU, BASINÇ DÜŞÜRÜCÜ VANA, SU SAYACI, BELEDİYE

### Boru/kanal çapı yazım biçimi

- xx" (inç): 14 metin — ör. "2"", "4"", "SU GİRİŞİ-2""
- Øxx: 7 metin — ör. "Ø15", "Ø25"
- x/x" (kesirli inç): 1 metin — ör. "1/2""

Not/hesap metinleri: `hesap/15_Belediye_Temizsu_Kolon_Semasi_notlar.txt` (9 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `ST-ARMATUR-TEMİZSU` (4827), `ST-CIHAZ` (1443), `ST-VANA` (661), `ST-TEMIZ-SOGUKSU-YUKBIRIMI` (611), `ST-SU` (469), `ST-TEMIZ-CAP` (410), `ST-TEMIZ-SICAKSU-YUKBIRIMI` (347), `ST-ARMATUR` (309), `ST-ARMATÜR-TEMIZ-YUKBİRİMİ` (200), `ST-SICAK` (117), `ST-SIRK` (116), `ST-BASLIK-TEMİZSU` (36), `ST-TEXT` (15), `ST-SIRK-TEXT` (14), `ST-SUZGEC` (12), `ST-CIHAZ-NO` (12), `1-BASLIK` (8), `0` (5), `ST-TEMİZSU-KOLON-NO` (4), `ST-KOLON-NO` (1), `ST-LEGEND` (1)

Bloklar (model uzayı INSERT sayısı): `Z1` (62), `LAVABO-KS` (59), `KLOZET-KS` (59), `A$Cda913a58` (40), `C10` (13), `A$C2B514568` (12), `A$C353D6097` (5), `A$C2E285E9311111` (4), `A$C119C6B35` (4), `A$C5F1E4A45` (4), `A$C0B325108` (3), `SN` (2), `A$C105B5B3A` (2), `A$C05AF55CE` (2), `A$C6DAC0416` (2), `A$C3C576301` (2), `A$C09605995` (2), `A$C71446B59` (2), `UP_ANTET_01` (1), `logo` (1), `Kesme` (1), `PN123` (1), `EV1` (1), `BOILER` (1), `A$C52EE5F1D` (1), `A$C538C06E0` (1), `A$C622B0F86` (1), `A$C66241EC0` (1), `A$C2853174D` (1), `BALANS VANASI` (1), `T7FT` (1), `T6DT` (1), `TD` (1), `A$C73265755` (1), `LEGEND TEMİZSU` (1)
</details>


---
## 16_AVM_Pissu_Kolon_Semasi

Orijinal: `AVM Pissu Kolon Şeması.dwg` — 39262 çizgi parçası, 685 daire, 1384 metin; 30 katman, 15 farklı blok (model uzayı).
Kapalı/dondurulmuş katman: 2 (ör. `ST-CIHAZ`, `ST-SU`).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/16_AVM_Pissu_Kolon_Semasi_01.png` | R01; R03; R04; R05; PSU-02-A/B; PSU-03-A/B; PİS SU TRANSFER ÜNİTESİ; 0.5 DU; 3. KAT; 2A. KAT |
| 2 | pafta | `onizleme/16_AVM_Pissu_Kolon_Semasi_02.png` | AVM PİSSU KOLON ŞEMASI; Mekanik; ÇİZİM SEMBOLLERİ; PİS SU KOLON NUMARASI; DEMİR BORU; TAVANDA PİS SU BORUSU; PİS SU BORUSU; ALT KAT TAVAN PİS SU BORUSU |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/16_AVM_Pissu_Kolon_Semasi_lejant_01.png`, `lejant/16_AVM_Pissu_Kolon_Semasi_lejant_01.txt`

> PİS SU BORUSU · DEMİR BORU · ALT KAT TAVAN PİS SU BORUSU · TAVANDA PİS SU BORUSU · KLOZET PİS SU BORUSU · GARAJ PİS SU BORUSU · P1 \| PİS SU KOLON NUMARASI


### Şemalar

- `sema/16_AVM_Pissu_Kolon_Semasi_sema_02.png` — AVM PİSSU KOLON ŞEMASI. Sık metinler: Mekanik, GÖK-AY PROJE MÜHENDİSLİK TİC. LTD. ŞTİ. Fener Kalamış Cad. Körfez Apt. No:17 Daire:1 Kadıköy, İst. Tel: 0216 338 84 94, AVM PİSSU KOLON ŞEMASI, 209, PİS SU KOLON NUMARASI, DEMİR BORU, ÇİZİM SEMBOLLERİ, TAVANDA PİS SU BORUSU, PİS SU BORUSU, ALT KAT TAVAN PİS SU BORUSU, KLOZET PİS SU BORUSU, GARAJ PİS SU BORUSU

### Boru/kanal çapı yazım biçimi

- Øxx: 964 metin — ör. "Ø70", "Ø100", "0.5 DU-Ø70", "1.5 DU-Ø70", "2.5 DU-Ø100", "1 DU-Ø70", "4 DU-Ø100", "2 DU-Ø70"
- xx" (inç): 9 metin — ör. "DEMİR BORU-3""

Not/hesap metinleri: `hesap/16_AVM_Pissu_Kolon_Semasi_notlar.txt` (2 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `SP-ARMATUR-PİSSU` (11570), `SP-PIS-YUKBIRIMI` (1781), `SP-CIHAZ` (825), `SP-PIS-CAP` (738), `SP-PIS` (452), `SP-PIS-ALT KAT TAVANINDA` (365), `SP-ARMATUR-PIS-YUKBIRIMI` (353), `SP-PISSU` (324), `SP-SUZGEC` (267), `ST-SU` (252), `SP-PISSU-DOSEME` (108), `SP-IZGARA` (70), `SP-PISSU-TAVAN` (67), `sembol_no_TUR` (42), `SP-DEMIR-BORU-TEXT` (25), `SP-BASLIK-PİSSU` (23), `SP-DEMIR-BORU` (17), `0` (14), `SP-PİSSU-VANA` (14), `SP-PISSU-KOLON-NO` (12), `SP-CIHAZ-NO` (9), `SP-HAVALIK` (8), `SP-PISSU-CAP` (7), `SP-PISSU-TEXT` (5), `1-BASLIK` (5), `ST-CIHAZ` (2), `SP-TEXT` (2), `SP-PISSU-ALTKAT` (1), `SP-PISSU-KLOZET` (1), `SP-GARAJ-PİSSU` (1)

Bloklar (model uzayı INSERT sayısı): `LAVABO-KS` (142), `SUZ` (86), `KLOZET-KS` (84), `C10` (37), `dgfdgdfg` (14), `PN-2` (11), `A$C5cdce70e` (5), `SÜZGEÇLİ DUŞ` (3), `A$C71446B59` (2), `A$C66241EC0` (2), `A$C6FA149A7` (2), `EV1` (1), `-PISSU POMPA` (1), `logo` (1), `PN1` (1)
</details>


---
## 17_Belediye_Pissu_Kolon_Semasi

Orijinal: `Belediye Pissu Kolon Şeması.dwg` — 18594 çizgi parçası, 353 daire, 704 metin; 31 katman, 12 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/17_Belediye_Pissu_Kolon_Semasi_01.png` | 1.BODRUM KAT; ZEMİN KAT; 1. KAT; 2. KAT; 3. KAT; ÇATI; 2.BODRUM KAT; 2.A KAT; Ø100 - alt kat tavandan; Ø70 - alt kat tavandan |
| 2 | pafta | `onizleme/17_Belediye_Pissu_Kolon_Semasi_02.png` | BELEDİYE PİSSU KOLON ŞEMASI; Mekanik; ÇİZİM SEMBOLLERİ; PİS SU KOLON NUMARASI; DEMİR BORU; TAVANDA PİS SU BORUSU; PİS SU BORUSU; ALT KAT TAVAN PİS SU BORUSU |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/17_Belediye_Pissu_Kolon_Semasi_lejant_01.png`, `lejant/17_Belediye_Pissu_Kolon_Semasi_lejant_01.txt`

> PİS SU BORUSU · DEMİR BORU · ALT KAT TAVAN PİS SU BORUSU · TAVANDA PİS SU BORUSU · KLOZET PİS SU BORUSU · GARAJ PİS SU BORUSU · P1 \| PİS SU KOLON NUMARASI


### Şemalar

- `sema/17_Belediye_Pissu_Kolon_Semasi_sema_02.png` — BELEDİYE PİSSU KOLON ŞEMASI. Sık metinler: Mekanik, GÖK-AY PROJE MÜHENDİSLİK TİC. LTD. ŞTİ. Fener Kalamış Cad. Körfez Apt. No:17 Daire:1 Kadıköy, İst. Tel: 0216 338 84 94, BELEDİYE PİSSU KOLON ŞEMASI, 210, PİS SU KOLON NUMARASI, DEMİR BORU, ÇİZİM SEMBOLLERİ, TAVANDA PİS SU BORUSU, PİS SU BORUSU, ALT KAT TAVAN PİS SU BORUSU, KLOZET PİS SU BORUSU, GARAJ PİS SU BORUSU

### Boru/kanal çapı yazım biçimi

- Øxx: 434 metin — ör. "Ø70", "Ø100", "1.5 DU-Ø70", "0.5 DU-Ø70", "1 DU-Ø70", "6 DU-Ø100", "4 DU-Ø100", "2 DU-Ø70"
- xx" (inç): 3 metin — ör. "DEMİR BORU-3""

Not/hesap metinleri: `hesap/17_Belediye_Pissu_Kolon_Semasi_notlar.txt` (1 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `SP-ARMATUR-PİSSU` (5451), `SP-PIS-CAP` (699), `SP-PIS` (425), `SP-ARMATUR-PIS-YUKBIRIMI` (222), `ST-SU` (180), `SP-SUZGEC` (174), `SP-CIHAZ` (163), `SP-PISSU-TAVAN` (81), `SP-PISSU-TAV-CAP` (79), `SP-PIS-ALT KAT TAVANINDA-TEXT` (60), `SP-PIS-ALT KAT TAVANINDA` (51), `SP-PIS-YUKBIRIMI` (40), `SP-BASLIK-PİSSU` (23), `SP-PISSU` (19), `SP-PISSU-KOLON-NO` (15), `SP-PİSSU-VANA` (14), `ST-SUZGEC` (12), `SP-DEMIR-BORU` (12), `0` (11), `SP-PISSU-CAP` (9), `SP-DEMIR-BORU-TEXT` (8), `ST-CIHAZ` (6), `SP-PISSU-DOSEME` (6), `SP-PISSU-DÖŞ-CAP` (6), `1-BASLIK` (5), `SP-HAVALIK` (4), `SP-PISSU-TEXT` (4), `SP-CIHAZ-NO` (4), `SP-PISSU-ALTKAT` (1), `SP-PISSU-KLOZET` (1), `SP-GARAJ-PİSSU` (1)

Bloklar (model uzayı INSERT sayısı): `A$C1C745B7E` (62), `KL1` (60), `SUZ` (58), `ST-CıHAZ-1` (13), `PIK-NO-1` (8), `A$C2E285E9311111` (4), `EV1` (3), `A$C71446B59` (2), `A$C66241EC0` (2), `-PISSU POMPA` (1), `logo` (1), `PN1` (1)
</details>


---
## 18_Yangin_Tesisati_Kolon_Semasi

Orijinal: `Yangın Tesisatı Kolon Şeması.dwg` — 18592 çizgi parçası, 214 daire, 531 metin; 19 katman, 28 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/18_Yangin_Tesisati_Kolon_Semasi_01.png` | YANGIN KOLON ŞEMASI; Mekanik; ÇİZİM SEMBOLLERİ; İB1; Sp1; TD1; Sp2; TD2; 2. BODRUM KAT; ZEMİN KAT |

### Lejantlar

**ÇİZİM SEMBOLLERİ** — `lejant/18_Yangin_Tesisati_Kolon_Semasi_lejant_01.png`, `lejant/18_Yangin_Tesisati_Kolon_Semasi_lejant_01.txt`

> KÜRESEL VANA · KELEBEK VANA · ISLAK ALARM VANASI · CEKVALF · YÜKSELEN MİLLİ VANA · AKIŞ ANAHTARI (FLOW SWITCH) · BASINÇ DÜŞÜRÜCÜ VANA · OTOMATİK PRUJÖR · SPRİNKLER BORUSU · YANGIN BORUSU · TEST DRENAJ BORUSU · YANGIN DOLABI - Sıva üstü · Kırılmaz Hortum · Hortum çapı : 1", Hortum boyu : 30 m, · Kesme Vanası : 2" · El Söndürme Tüpü : ABC tipi, 6 kg · YANGIN DOLABI - Sıva Altı · Kırılmaz Hortum · Hortum çapı : 1", Hortum boyu : 30 m, · Kesme Vanası : 2" · El Söndürme Tüpü : ABC tipi, 6 kg · İTFAİYE BAĞLANTI ELEMANI · BASINÇ SINIRLAYICI · İTFAİYE BAĞLANTI VANASI · Y1 \| YANGIN DOLABI KOLON NUMARASI · Sp1 \| SPRİNKLER KOLON NUMARASI · TD1 \| TEST DRENAJ KOLON NUMARASI · İTFAİYE BİNA BAĞLANTI AĞZI · İB1 \| KOLON NUMARASI · ZON KONTROL DETAYI ( F1-A DETAYI ) · ANA YANGIN KOLONU · İZLEME ANAHTARLI ZON KONTROL VANASI · GERİ TEPME VENTİLİ · MANOMETRE · AKIŞ ANAHTARI (FLOW SWITCH) · KAT ANA BESLEME BORUSU · 1" · DRAIN \| TEST \| OFF · 1/2" · 2" · GÖZETLEME CAMLI · TEST VE DRENAJ VANASI-Ø25 · DRENAJ KOLONU · EN YAKIN GİDERE


### Şemalar

- `sema/18_Yangin_Tesisati_Kolon_Semasi_sema_01.png` — YANGIN KOLON ŞEMASI. Sık metinler: 21/2", F1-A, DN200, DN150, DN100, UYGUN SÜZGECE, ZEMİN KAT, ±0.00, 1. KAT, 2. KAT, 2. ARA KAT, 3. KAT, +21.00, +15.00, +10.00, +5.00, +25.50, ÇATI, 12", Ø15, Hortum çapı : 1", Hortum boyu : 30 m,, Kırılmaz Hortum, Kesme Vanası : 2", El Söndürme Tüpü : ABC tipi, 6 kg, AKIŞ ANAHTARI (FLOW SWITCH)

### Boru/kanal çapı yazım biçimi

- xx" (inç): 294 metin — ör. "2"", "21/2"", "8"", "6"", "4"", "12"", "5"", "Hortum çapı : 1", Hortum boyu "
- DNxx: 36 metin — ör. "DN200", "DN150", "DN100", "DN80", "DN125"
- Øxx: 3 metin — ör. "Ø15", "TEST VE DRENAJ VANASI-Ø25"
- x/x" (kesirli inç): 1 metin — ör. "1/2""

Not/hesap metinleri: `hesap/18_Yangin_Tesisati_Kolon_Semasi_notlar.txt` (5 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `Y-VANA` (6468), `Y-YANGINDOLABI-BORU` (2381), `Y-TEXT` (1149), `Y-CIHAZ` (341), `Y-SPRINKLER-BORU` (197), `Y-YANGINDOLABI-TEXT` (196), `Y-TEST-DRAIN-BORU` (98), `Y-LEGEND-TURKCE` (85), `Y-SP-ADET` (36), `Y-SU` (27), `1-CIHAZ` (16), `0` (14), `Y-KOLON-NO` (10), `1-BASLIK` (7), `Y-CIHAZ NO` (6), `Y-ZON-TEXT` (6), `T-VANA-TEXT` (2), `Y-BASLIK` (2), `Y-DRENAJ` (1)

Bloklar (model uzayı INSERT sayısı): `A$C325C500B` (111), `Kesme` (43), `ZONE-F1` (36), `A$Cd15443be` (32), `A$Cda913a58` (18), `A$C0B325108` (15), `PN` (9), `VANA` (7), `A$C3DDA2012` (6), `A$C534F1FFE` (6), `A$C5BF36ED3` (5), `PN-2` (5), `A$C7E5C2832` (4), `Z1` (2), `A$C353D6097` (2), `A$C3BAF248B` (2), `A$Cb32f9aa1` (2), `GYFTNSDFCG` (1), `A$C55921D76` (1), `A$C75B759AB` (1), `Test&Drenaj Vanası` (1), `A$C136E24A5` (1), `A$C71446B59` (1), `A$C66241EC0` (1), `A$C52EE5F1D` (1), `BASINÇDÜŞÜRÜCÜ` (1), `UP_ANTET_01` (1), `logo` (1)
</details>

