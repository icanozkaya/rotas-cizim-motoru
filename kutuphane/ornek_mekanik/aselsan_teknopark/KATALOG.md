# ASELSAN Akyurt-1 Yerleşkesi — OPAK Binası (Ana Bina) Mekanik Uygulama Projesi

Kaynak: kullanıcının gönderdiği ASELSAN Teknopark / OPAK Binası Ana Bina mekanik uygulama proje seti (8 DWG + opak cihaz listesi XLS). Antet: "ASELSAN AKYURT-1 YERLEŞKESİ — OPAK BİNASI PROJE YAPIM İŞİ — UYGULAMA PROJE TESLİMİ — ANA BİNA". Kotlar: ±0.00 = 978.90, 1. kat +7.00, teras +13.50, çatı +18.35.

Pafta düzeni: tüm paftalar model uzayında **yatay ozalit şeridi** halinde dizilmiş (şerit yüksekliği 9000 birim, iç paftalar 8800 yükseklikte, genişlik 10 000–41 600 arası). Antet şeridin sağ ucunda dikey sütun (1990×8800, katman `0-KRCN-Z-ANTET`). Katman öneki: `0-KRCN-…` (mimari/ortak), `0-MEK-…`, `-M-…` (mekanik).

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
| `dwg/01_Isitma_Sogutma_Tesisati_Ana_Bina.dwg` | 22.1 MB | 8ad37f7b-01-Is_tma_So_utma_Tesisat_-Ana_Bina.dwg | 12 | 2 | 3 |
| `dwg/02_Yangin_Tesisati_Ana_Bina.dwg` | 10.6 MB | 1d55e2db-02-Yang_n_Tesisat_-Ana_Bina.dwg | 7 | 2 | 1 |
| `dwg/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina.dwg` | 2.2 MB | 01c4b0ba-03-Azot_ve_Bas_n_l__Hava_Tesisat_-Ana_Bina.dwg | 6 | 3 | 0 |
| `dwg/04_Pis_Su_Tesisati_Ana_Bina.dwg` | 1.9 MB | 26640225-04-Pis_Su_Tesisat_-Ana_Bina.dwg | 11 | 1 | 2 |
| `dwg/05_Temiz_Su_Tesisati_Ana_Bina.dwg` | 7.8 MB | f88e2f09-05-Temiz_Su_Tesisat_-Ana_Bina.dwg | 6 | 1 | 1 |
| `dwg/06_Havalandirma_Tesisati_Ana_Bina.dwg` | 23.2 MB | de5e0301-06-Havaland_rma_Tesisat_-Ana_Bina.dwg | 15 | 1 | 0 |
| `dwg/07_Vinc_Ana_Bina.dwg` | 5.6 MB | 8d1b0d2d-07-Vin_-Ana_Bina.dwg | 12 | 0 | 0 |
| `dwg/08_XREF_Mimari_Altlik_Ana_Bina.dwg` | 20.4 MB | b6a6df42-XREF.dwg | 4 | 0 | 0 |

Belgeler:

- `belge/Aselsan_Opak_Cihaz_Listesi_Ana_Bina.xls` (3.7 MB)

Hesap CSV dökümleri (25 adet): `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__AHU.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__BOYLER.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__DEIYONIZE.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__DK.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__EHP.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__ESANJOR.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__FAN.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__FCU.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__FILTRE.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__GT-BT-BFT.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__HASSAS_KLIMA.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__HIDROFOR.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__KAZAN.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__KOMPRESOR.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__MENFEZ.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__PIS_SU_POMPASI.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__POMPA.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__SOG_GRUBU.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__SU_DEPOSU.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__SU_YUMUSATMA.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__ULTRAVIYOLET.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__VAV.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__VRF_DIS.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__VRF_IC.csv`, `Aselsan_Opak_Cihaz_Listesi_Ana_Bina__YAG_BUHARI.csv`

### Cihaz listesi (Aselsan_Opak_Cihaz_Listesi_Ana_Bina.xls → hesap/*.csv, 25 sayfa)
Sayfalar: AHU, FAN, HASSAS KLİMA, YAĞ BUHARI, VAV, MENFEZ, FCU, EHP, EŞANJÖR, SOĞ. GRUBU, GT-BT-BFT, KAZAN, DK, POMPA, VRF İÇ/DIŞ, HİDROFOR, PİS SU POMPASI, BOYLER, SU DEPOSU, KOMPRESÖR, ULTRAVİYOLE, FİLTRE, SU YUMUŞATMA, DEİYONİZE.

| Cihaz | Değer |
|---|---|
| Soğutma grubu CH-10 | Hava soğutmalı, 1000 kW, R-134a, 6/11 °C, %40 antifriz, free-cooling, 425,5 kW elektrik, 3 asıl + 1 yedek (Aselsan temini) |
| Chiller primer pompa P-15 | 96 m³/h, 35 mSS, 8 asıl + 4 yedek (19,3 kW×8) |
| Temiz oda AHU soğutma P-22 | 106,3 m³/h, 25 mSS, 3+1 |
| Genel oda AHU soğutma P-21 | 59 m³/h, 18 mSS, 2+1 |
| Fancoil soğutma P-20 | 59 m³/h, 15 mSS; fancoil ısıtma P-06: 10 m³/h, 9 mSS (80/60) |
| AHU ısıtma P-07 / P-08 | 26 m³/h–15 mSS / 54 m³/h–10 mSS (80/60) |
| Proses suyu pompaları | P-19 41 m³/h–13 mSS (7/12), P-26 78 m³/h–22 mSS (20/25), P-31 5 m³/h–16 mSS (10/22), P-38 kompresör soğutma 27 m³/h–10 mSS |
| Radyatör / boyler / KSS pompaları | P-04 3 m³/h–5 mSS, P-05 3 m³/h–8 mSS, P-39 KSS sirkülasyon 5 m³/h–6,5 mSS |
| Elektrikli kombi K-47 | 20 kW, 80/60, 6 bar |
| Boyler B-09 | 600 L çelik tek serpantinli, 80/60 → 10/60, 2 adet |
| Su depoları | SD-11 glikol doldurma 7,5 m³ GRP; SD-27/SD-32 proses 6 m³ GRP; SD-42 deiyonize 0,5 m³ PE |
| Hidroforlar | HD-12 glikol 3 m³/h–25 mSS; HD-41 deiyonize 5 m³/h–40-60 mSS, 1+1 |
| Pis su pompaları | PSP-01..03 asansör çukuru 2 m³/h–10 mSS, vorteks |
| Kompresörler | KOMP.-1 yangın kuru zon 8 bar, 500 L, 5,2 m³/h; VS-1 basınçlı hava 13 bar, 5000 L, 1500 m³/h, 3 adet (Aselsan temini) |

Yangın: bina mevcut yangın hattından beslenir ("MEVCUT YANGIN HATTINDAN"), set içinde yangın pompası/depo yok. Sprinkler 1/2" NPT, upright, K=80, 68 °C. Islak (W.A.V.), tek kilitlemeli kuru (P.A.V.) ve çift kilitlemeli kuru (D.A.V.) alarm vana istasyonu sembolleri lejantta tanımlı; kuru zon için KOMP.-1 kompresörü.
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
## 01_Isitma_Sogutma_Tesisati_Ana_Bina

Orijinal: `8ad37f7b-01-Is_tma_So_utma_Tesisat_-Ana_Bina.dwg` — 254923 çizgi parçası, 6555 daire, 11589 metin; 240 katman, 121 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_01.png` | A BLOK (EK); A BLOK; Altta Tünel; GIRIS 1 Teknik / İdari Personel; GIRIS 2 Üretim Personeli; *Havai hat taşıma çelik konstrüksiyonu uygulamada detay projesi hazırlanacaktır.; *Toprak altında ön izoleli boru.; *Havai hat. |
| 2 | pafta | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_02.png` | TERAS KATI PLANI (+13.50 = 992.40) ÖLÇEK 1/100; HASSAS KLİMA DIŞ ÜNİTELERİ; SOĞUTMA GRUPLARI; Not:VRF sistemi 3 borulu ve -15°C de çalışır olmalıdır.; (SATIN ALIMINI ASELSAN YAPACAKTIR. MONTAJ VE; DEVREYE ALMA YÜKLENİCİ KAPSAMINDADIR.); elk.odaları soğutma dış üniteleri; mevcut sundurma |
| 3 | pafta | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_03.png` | 1. KAT PLANI (+7.00 = 985.90) ÖLÇEK 1/100; Not:VRF sistemi 3 borulu ve -15°C de çalışır olmalıdır.; KS-; YANGIN MERDİVENİ; ELK. OD.; MEKANİK TEKNİK HACİM - 2; MEKANİK TEKNİK HACİM - 1; TEM. OD.; TOPLANTI OD. 2; TOPLANTI OD. 1 |
| 4 | pafta | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_04.png` | ZEMİN KAT PLANI (±0.00 = 978.90) ÖLÇEK 1/100; *Toprak altından ön izoleli boru ile dağıtım yapılacaktır.; Not:VRF sistemi 3 borulu ve -15°C de çalışır olmalıdır.; Z-46; ELK. OD.; Z-45; TEM. OD.; Z-44; BAKIM ODASI; KAT HOLÜ |
| 5 | pafta | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_05.png` | ELEKTRİKLİ KOMBİ AKIŞ ŞEMASI; RADYATÖR TESİSATI KOLON ŞEMASI; SANTRAL BAĞLANTI ŞEMASI; GENEL SANTRAL BAĞLANTI ŞEMASI; ISITMA VE SOĞUTMA TESİSATI AKIŞ ŞEMASI; ÇATI KATI; 1. KAT; ZEMİN KATI; ISITMA SOĞUTMA TESİSATI SEMBOLLERİ; ÇATI |
| 6 | pafta | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_06.png` | FCU İZOMETRİ ŞEMASI; Kw.; " likid; " gaz |
| 7 | pafta | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_07.png` | BORULAMA DETAY; PROSES SOĞUTMA SİSTEM ŞEMASI; TİPİK KLİMA SANTRALLERİ ISITMA/SOĞUTMA SERPANTİN BAĞLANTI DETAYI; EŞANJÖR BAĞLANTI DETAYI; HSSG BAĞLANTI DETAYI; TİPİK PROSES SOĞUTMA BAĞLANTI DETAYI; TİPİK FAN-COIL BAĞLANTI DETAYI; H-HEX-01; SEMBOL |
| 8 | pafta | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_08.png` | ISITMA / SOĞUTMA DETAY |
| 9 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_09.png` | KOLLEKTÖRE; FCU-4; FCU-3; FCU-1; FCU-2; FCU-7; FCU-6; FCU-5 |
| 10 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_10.png` | YILDIRIM BEYAZIT CADDESİ; Altta Tünel; KUVVET MERKEZI; GIRIS 1 Teknik / İdari Personel; GIRIS 2 Üretim Personeli; GIRIS 3 Ambar / Depo; BETON KAİDE; AZOT TANKI |
| 11 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_11.png` | ÇANKIRI BULVARI; Servis Girişi |
| 12 | serbest grup | `onizleme/01_Isitma_Sogutma_Tesisati_Ana_Bina_12.png` | KAT PLANLARI; ISITMA / SOĞUTMA TESİSATI; UYGULAMA PROJE TESLİMİ; OPAK BİNASI PROJE YAPIM İŞİ; ASELSAN AKYURT-1 YERLEŞKESİ; ANA BİNA; İNŞAAT ve EMLAK DİREKTÖRLÜĞÜ ONAYI; BAŞLIK; KULLANICI KOORDİNESİ / MUTABAKAT |

### Lejantlar

**ISITMA SOĞUTMA TESİSATI SEMBOLLERİ** — `lejant/01_Isitma_Sogutma_Tesisati_Ana_Bina_lejant_01.png`, `lejant/01_Isitma_Sogutma_Tesisati_Ana_Bina_lejant_01.txt`

> ISITMA GİDİŞ BORUSU · ISITMA DÖNÜŞ BORUSU · SOĞUTMA GİDİŞ BORUSU · SOĞUTMA DÖNÜŞ BORUSU · RADYATÖR GİDİŞ BORUSU · RADYATÖR DÖNÜŞ BORUSU · KLİMA GAZ BORUSU · HEAT TRACING · KİLİTLİ VANA · KÜRESEL VANA · PİSLİK TUTUCU · ÇEKVALF · KOMPANSATÖR · EMNİYET VANASI · M \| KOMBİNE ON-OFF İKİ YOLLU MOTORLU VANA · M \| DİJİTAL AKTÜATÖRLÜ BASINÇTAN BAĞIMSIZ VANA · RADYATÖR - FANCOİL KESME VANASI · BOŞALTMA - OTOMATİK BESLEME VANASI · KOLON BOŞALTMA VANASI (KOSVA VANA) · HAVALIK TÜPÜ · POMPA TEKLİ / FREKANS KONVERTÖRLÜ · T \| TERMOMETRE · M \| MANOMETRE · MİKRON FİLTRE · . m. PKKP600 \| RADYATÖR PANEL · OHAC · OTOMATİK HAVA ATMA CİHAZI · IST · ISITMA KOLON NUMARASI · SGT · SOĞUTMA KOLON NUMARASI · VRF-0 \| KLİMA KOLON NUMARASI · PRS · PROSES KOLON NUMARASI · KRİTİK HAT NUMARASI · T \| TERMOSTAD · 238 \| 478 \| 984 \| FCU-5 \| 750 m3/h · TAVAN TİPİ GİZLİ FAN-COIL · TAVAN TİPİ KASETLİ FANCOİL

**SEMBOL** — `lejant/01_Isitma_Sogutma_Tesisati_Ana_Bina_lejant_02.png`, `lejant/01_Isitma_Sogutma_Tesisati_Ana_Bina_lejant_02.txt`

> BASINÇTAN BAĞIMSIZ · R12 \| KONTROL VANASI · N8 · 2 \| R12 · 1 · ISITMA DÖNÜŞ \| N4 \| N4 \| NO \| SEMBOL \| EKIPMAN LISTESI \| MIKTAR · 1 \| KURESEL VANA \| 4 · 2-YOLLU (ON-OFF) BASINCTAN · 2 \| 2 · DN15 MİNİ KÜRESEL VANA \| BAGIMSIZ KONTROL VANASI · 1 \| 3 · 3 \| PISLIK TUTUCU \| 2 · ISITMA GİDİŞ · R12 \| RAKOR \| 6 · N8 \| R12 · N8 \| N4 \| REDUKSIYON · 4 · BASINÇTAN BAĞIMSIZ · KONTROL VANASI \| FAN-COIL · N8 \| NIPEL \| 6 · R12 · N8 · 2 · 1 \| R12 · SOĞUTMA DÖNÜŞ \| N4 \| N4 · DN15 MİNİ KÜRESEL VANA \| 3/4" \| 3/4" · 3 · 1 · SOĞUTMA GİDİŞ · N8 \| N8 \| R12 · FLEXIBLE BORU 3/4"x3/4" · ESNEK HORTUM · DRENAJ BORUSU


### Şemalar

- `sema/01_Isitma_Sogutma_Tesisati_Ana_Bina_sema_05.png` — ELEKTRİKLİ KOMBİ AKIŞ ŞEMASI; RADYATÖR TESİSATI KOLON ŞEMASI; SANTRAL BAĞLANTI ŞEMASI; GENEL SANTRAL BAĞLANTI ŞEMASI; ISITMA VE SOĞUTMA TESİSATI AKIŞ ŞEMASI. Sık metinler: 3/4", 1 1/4", 1/2", mahal no:, Watt, m.-PKKP-, 1000000 W, DN25, 900, EN YAKIN GİDERE, 1 1/2", 3265 W, DN200, SOĞUTMA HATTI, Balans Vanası, Oransal Kombine, 2 1/2", KİLİTLİ VANA, 3265, 1,5, HAVA TUPU:10 LT., ISI EŞANJÖRÜ, 12", YEDEK AĞIZ-8"
- `sema/01_Isitma_Sogutma_Tesisati_Ana_Bina_sema_06.png` — FCU İZOMETRİ ŞEMASI. Sık metinler: Kw., " likid, " gaz, 3/8, 5/8, 14,0, 3/4, 1 1/8, 3,6, 1/2, 1 5/8, 98,0, 5,6, 9,2, 12,8, 7/8, 28,0, 42,0, 42,4, 34,8, 7,2, 18,4, 24,0, FCU İZOMETRİ ŞEMASI, 16,4
- `sema/01_Isitma_Sogutma_Tesisati_Ana_Bina_sema_07.png` — PROSES SOĞUTMA SİSTEM ŞEMASI. Sık metinler: DN100, DN150, KÜRESEL VANA, DN125, SUPPORTING, POINT, DN25, R12, MANOMETRE, 1/2", F/C, 100 Mikron Filtre, KELEBEK VANA, Balans Vanası, Oransal Kombine, DN20, DN200, DN65, TERMOMETRE, KELEBEK, VANA, DRENAJ, SANTRAL SERPANTİNİ, OTOMATİK PURJÖR, C-HEX-02

### Boru/kanal çapı yazım biçimi

- x/x" (kesirli inç): 816 metin — ör. "3/4"", "3972 W-3/4"", "3163 W-3/4"", "3550 W-3/4"", "1/2"", "1 1/4"", "1450 W-3/4"", "2150 W-3/4""
- xx" (inç): 780 metin — ör. "1"", "5900 W-1"", "5"", "6"", "1 1/4"", "8"", "4"", "1 1/2""
- DNxx: 257 metin — ör. "DN25", "DN100", "DN150", "DN250", "DN125", "DN300", "DN200", "DN15"
- Øxx: 197 metin — ör. "Ø25", "Ø50", "Ø32", "Ø40", "Ø65", "Ø50 mm FLANŞLI SÖKÜLEBİLİR PİS", "4 m³/h Ø114, DN50 FLANŞLI DENG", "mevcut ısı merkezindenki Ø150 "
- mm: 11 metin — ör. "YAYLI EMNİYET VENTİLİ DN : 50 ", "YAYLI EMNİYET VENTİLİ DN : 32 ", "Ø50 mm FLANŞLI SÖKÜLEBİLİR PİS", "DN 50 mm FLANŞLI HAVA AYIRICI", "DN 50 mm FLANŞLI TORTU VE PİSL", "YAYLI EMNİYET VENTİLİ DN : 20 ", "YAYLI EMNİYET VENTİLİ DN : 100", "202.70mm"
- xx/yy (kanal ölçüsü): 3 metin — ör. "20x20"
- PE/PPR dxx: 3 metin — ör. "DN65 HDPE BORU"

Not/hesap metinleri: `hesap/01_Isitma_Sogutma_Tesisati_Ana_Bina_notlar.txt` (110 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `0-KRCN-HVL-SANTRAL` (20192), `AS_TES_SUZGEC` (19764), `0-KRCN-IST-FANCOİL ZON-1` (16375), `-M-MAHAL-ETIKET-NOT` (12240), `0-KRCN-IST-KÜRESEL VANA` (11724), `0-MEK-IST-KÜRESEL VANA` (9937), `P-PIPE` (9130), `0-MEK-VRF-ICUNITE` (4676), `T-IST-EKIPMAN` (3666), `-M-DETAIL VALVE` (3008), `0-KRCN-IST-04RAD` (2574), `0-MEK-IST-POMPA` (2452), `0-KRCN-TESİSAT` (2428), `-M-DETAIL` (1455), `0-KRCN-IST-02CIHAZ` (1453), `-M-ISSO-FCU-SO-CAP` (1369), `0` (1365), `-M-ISSO-FCU-SOD-ZON1` (1343), `-M-ISSO-FCU-IS-CAP` (1275), `0-MEK-IST-MANOMETRE` (1260), `AS_PRFL_CELIK` (1214), `-M-MAHAL-ETK-` (1200), `-M-ISSO--ETIKET-TEXT-NOT` (1197), `0-KRCN-DSD-ICUNITE` (1032), `0-MEK-IST-KOLLEKTÖR` (1029), `0-KRCN-IST-04CIHAZ` (954), `0-MEK-IST-YAZI-ÇAP` (944), `0-KRCN-IST-03CIHAZ` (874), `0-KRCN-IST-YAZI-ÇAP` (852), `0-KRCN-DSD-BORULAMA` (849), `0-KRCN-DSD-ELEKTRİK OD.-CAP` (840), `0-KRCN-DONUT` (834), `HH_DUVAR` (774), `0-KRCN-IST-BORU-SGT-DÖNÜŞ` (764), `0-MEK-IST-CHILLER` (700), `-M-ISSO--CAP-BILGI` (686), `0-KRCN-PLATE` (664), `0-MEK-IST-04CIHAZ` (658), `0-MEK-IST-BÜZÜŞMETANKI` (588), `ISI MRK CHZ` (588)

Bloklar (model uzayı INSERT sayısı): `*U` (635), `NOKTA001` (467), `0-MEK-IST-KÜRESEL VANA-1` (459), `fancoil motorluvana` (168), `DONUT` (144), `M-MHLETK-ISI` (120), `K` (88), `0-MEK-IST-KOMPANSATÖR` (87), `0-MEK-IST-MANOMETRE` (78), `TERMOSTAS` (69), `DSD ÇAP` (67), `SE2` (57), `G$C6415B704` (57), `0-MEK-IST-ÇEKVALF` (51), `OK` (47), `0-MEK-IST-POMPA` (44), `0-MEK-IST-PİSLİK TUTUCU` (40), `TERMOSTAT` (40), `KESME` (40), `0-MEK-IST-TERMOMETRE` (36), `JOINT` (24), `0-MEK-IST-KÜRESEL VANA 1-2` (23), `KO` (22), `ISETKP04-04` (22), `FCU-GT-TIP-06` (21), `ISETKP04-06` (21), `0-KRCN-DSD-KASETTIPI1` (15), `A$C75A43FCA` (15), `ISETKP04-03` (14), `SPR-RISERNO` (13), `ISETKP04-01` (12), `M12` (12), `Mikron Filtre` (12), `A$C6A0D62E9` (12), `0-MEK-IST-EMNİYET VENTİLİ` (11), `A$C6A0D5AC5` (11), `EX-T1500` (10), `1.5-PKKP900` (10), `FCU-GT-TIP-05` (10), `FCU-GT-TIP-03` (9)
</details>


---
## 02_Yangin_Tesisati_Ana_Bina

Orijinal: `1d55e2db-02-Yang_n_Tesisat_-Ana_Bina.dwg` — 403420 çizgi parçası, 10984 daire, 19964 metin; 239 katman, 52 farklı blok (model uzayı).
Kapalı/dondurulmuş katman: 2 (ör. `-M-SPR-KORUMA`, `-M-YNGN-FHC-KORUMA`).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/02_Yangin_Tesisati_Ana_Bina_01.png` | Klima santralleri odası altndaki mahal; DİK TİP (UPRIGHT) SPRINKLER; PENDENT SPRINKLER; PENDENT / UPRIGHT SPRINKLER; SPRİNKLER GÖSTERİMİ |
| 2 | pafta | `onizleme/02_Yangin_Tesisati_Ana_Bina_02.png` | D-1; SP-1; T-03; MEKANİK TEKNİK HACİM; T-02; OPTİK ATIŞ PLATFORMU; TÜPLÜ YANGIN DOLABI; DN100 |
| 3 | pafta | `onizleme/02_Yangin_Tesisati_Ana_Bina_03.png` | SP-2; SP-3; ELK. OD.; MEKANİK TEKNİK HACİM - 2; MEKANİK TEKNİK HACİM - 1; TEM. OD.; Y.G.H; MUTFAK; TOPLANTI OD. 2; TOPLANTI OD. 1 |
| 4 | pafta | `onizleme/02_Yangin_Tesisati_Ana_Bina_04.png` | MEVCUT YANGIN HATTINDAN; DİK TİP (UPRIGHT) SPRINKLER; PENDENT SPRINKLER; PENDENT / UPRIGHT SPRINKLER; SPRİNKLER GÖSTERİMİ; SP-2; SP-1; SP-3; BAKIM ODASI; KAT HOLÜ |
| 5 | pafta | `onizleme/02_Yangin_Tesisati_Ana_Bina_05.png` | A-BLOK; TADİLAT ALANI; A-A KESİT; TV 2 Kabini; TV 1 Kabini; THA 1 Kabini; Büyük cihazlara ait giriş-çıkış kapısı; min. 1.070 mm; YANGIN SÖNDÜRME TESİSATI SEMBOLLERİ; 1.KAT |
| 6 | pafta | `onizleme/02_Yangin_Tesisati_Ana_Bina_06.png` | YANGIN DETAY |
| 7 | serbest grup | `onizleme/02_Yangin_Tesisati_Ana_Bina_07.png` | KAT PLANLARI; YANGIN SÖNDÜRME TESİSATI; OPAK BİNASI PROJE YAPIM İŞİ; ASELSAN AKYURT-1 YERLEŞKESİ; UYGULAMA PROJE TESLİMİ; ANA BİNA; İNŞAAT ve EMLAK DİREKTÖRLÜĞÜ ONAYI; BAŞLIK; KULLANICI KOORDİNESİ / MUTABAKAT |

### Lejantlar

**LEJAND / LEGEND** — `lejant/02_Yangin_Tesisati_Ana_Bina_lejant_01.png`, `lejant/02_Yangin_Tesisati_Ana_Bina_lejant_01.txt`

> KONVANSIYONEL YANGIN KONTROL PANELİ · BOŞALTMA BUTONU · FLAŞÖRLÜ SİREN · SİREN · (A) \| OPTIK DUMAN DEDEKTÖRÜ · P \| (ASMA TAVAN ICI) · (O) \| OPTIK DUMAN DEDEKTÖRÜ · P \| (ODA ICI) · (Y) \| OPTIK DUMAN DEDEKTÖRÜ · P \| (YUK. DOSEME ALTI) · 1/2" NPT , UPRIGHT , K:80 , 68 C SPRINKLER · E · BORU ASKI ELEMANI · PRE-ACTION VANA · FLAŞÖRLÜ SİREN · B · H · D

**YANGIN SÖNDÜRME TESİSATI SEMBOLLERİ** — `lejant/02_Yangin_Tesisati_Ana_Bina_lejant_02.png`, `lejant/02_Yangin_Tesisati_Ana_Bina_lejant_02.txt`

> SPRİNKLER BORUSU · DRENAJ BORUSU · D-1 \| SP-1 \| YANGIN BORUSU KOLON NUMARASI · PENDENT SPRINKLER · DİK TİP (UPRIGHT) SPRINKLER · PU \| 25 \| 1 \| PENDENT / UPRIGHT SPRINKLER VE DİK TİP (PENDENT) SPRINKLER · KELEBEK VANA · İZLENEBİLİR KELEBEK VANA · YÜKSELEN MİLLİ VANA · ÇEK VANA · PISLIK TUTUCU · KOMPANSATÖR · TEST DRENAJ SETİ · F \| F.S \| FLOW SWITCH · İTFAİYE BAĞLANTI AĞZI / 2 x 2 1/2" · W.A.V. · ISLAK ALARM VANA ISTASYONU · P.A.V. · TEK KİTLEMELİ KURU ALARM VANA ISTASYONU · D.A.V. · ÇİFT KİTLEMELİ KURU ALARM VANA ISTASYONU · BASINÇ DÜŞÜRÜCÜ DENGELEME VANASI · M · MANOMETRE · POST İNDİKATÖR VANA · N.K. \| NORMAL KOŞULDA KAPALI · KOMPANSATÖR · YANGIN DOLABI (KAT PLANI) · YANGIN DOLABI (KOLON SEMASI) · Y · TÜPLÜ YANGIN DOLABI · TS EN 671-1'e uygun · 1" / 30m.yarı-sert hortumlu


### Şemalar

- `sema/02_Yangin_Tesisati_Ana_Bina_sema_05.png` — YANGIN TESİSATI KOLON ŞEMASI; YANGIN DOLABI (KOLON SEMASI). Sık metinler: 90x160cm, Üretim masası, Dolap, 50x50cm, Yeniden işlem masası, Rack, 110x110cm, N-gaz, Bank (ayakkabılık), 120x70x46cm, 1700kg, Test masası, +2.00 Kotu, DN100, DN150, Alt takım, Servis masası, 60x200cm, 500m³/h, Ø160 HDPE 100 PN16 BORU, Sistem, STORZ TİP 65mm, İTFAİYE SU ALMA AĞZI, DN65, 110x110x190cm

### Boru/kanal çapı yazım biçimi

- DNxx: 2884 metin — ör. "DN25", "DN100", "DN40", "DN50", "DN32", "DN150", "DN65", "DN80"
- PE/PPR dxx: 65 metin — ör. "Ø160 HDPE 100 PN16 BORU", "PE", "Ø110 HDPE 100 PN16 BORU", "HDPE-çelik geçiş parçası"
- xx" (inç): 49 metin — ör. "6"", "4"", "1" / 30m.yarı-sert hortumlu", "2"", "2 x 2 1/2"", "İTFAİYE BAĞLANTI AĞZI 4"", "İTFAİYE BAĞLANTI AĞZI / 2 x 2 ", "2 x 21/2" Üst Çıkışlı"
- Øxx: 45 metin — ör. "Ø160 HDPE 100 PN16 BORU", "Ø110 HDPE 100 PN16 BORU", "Ø25"
- xx/yy (kanal ölçüsü): 34 metin — ör. "300x150", "300x300", "450x200", "250x200", "550x200"
- mm: 22 metin — ör. "STORZ TİP 65mm", "300x300mm", "min. 1.070 mm"
- x/x" (kesirli inç): 13 metin — ör. "1/2"", "3/4"", "2 x 2 1/2"", "1/2" NPT , UPRIGHT , K:80 , 68", "İTFAİYE BAĞLANTI AĞZI / 2 x 2 ", "R 2 1/2""

Not/hesap metinleri: `hesap/02_Yangin_Tesisati_Ana_Bina_notlar.txt` (7 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `0-KRCN-MİMARİ-220526` (28979), `G_0.09` (27007), `TF_Mobilya` (14044), `-M-MAHAL-ETIKET-NOT` (12240), `0-KRCN-YNG-CIHAZ` (10835), `0-KRCN-YNG-İTFAİYE-BAĞLANTI AĞZI` (6360), `DV_alçıpanel_duvar_yeni` (6194), `-M-YNGN-SPR-YUK` (5775), `0-MEK-YNG-CIHAZ` (3920), `-M-YNGN-SPR-CAPCIZGI` (2802), `-M-YNGN-BORUYUK` (2802), `-M-YNGN-BORUUZUN` (2802), `-M-YNGN-BORUID` (2802), `-M-YNGN-ZON4` (2677), `0-KRCN-TESİSAT` (2428), `0-MEK-YNG-YANGINDOLABI` (2350), `1轮廓线` (2260), `-M-YNGN-ZON3` (1888), `A_Betonarme_Tarama` (1386), `-M-YNGN-ZON4-SPR-` (994), `TF_Cihaz` (913), `D_Aluminyum` (899), `-M-YNGN-ZON5` (893), `-M-SPR-KORUMA` (782), `PN_Aluminyum` (779), `PV-3EC7` (757), `0-KRCN-PLATE` (664), `0-KRCN-YNG-BORU` (595), `A_Duvar-alçiplak` (577), `Em.K - FFU` (567), `A_celik` (539), `0-KRCN-YNG-KURESEL VANA` (512), `-M-ANTET` (500), `-M-MAHAL-DEBILER` (489), `A8-MATERIAALIT` (462), `2细实线` (416), `KP_Aksesuar` (408), `TF_Cihaz_yazı` (391), `-M-YNGN-ZON3-SPR-` (386), `A_Aks` (383)

Bloklar (model uzayı INSERT sayısı): `M-MHLETK-YNG` (120), `*U` (108), `SP-C-UP-12` (42), `G$C03FB175B` (40), `SPRYD01` (29), `SPRKL100` (23), `Z$W@#30031` (15), `-M-Yangın_not` (15), `G$CF1021D0B` (15), `YANGIN-YÜKSELEN MİLLİ VANA` (14), `G$CF070FE5B` (12), `M12` (12), `SAHRA TİPİ YANGIN DOLABI VE HİDRANTI` (11), `DONUT` (9), `0-MEK-IST-ÇEKVALF` (9), `SPR-RISERNO` (8), `YANGIN-İZLENEBİLİR KELEBEK VANA` (8), `A$C6AE706CD` (8), `0-MEK-YANGIN-YANGIN DOLABI-KOLON` (7), `-M-RISERNO` (7), `A$C63EA4463` (7), `plgbb.8612` (6), `0-MEK-IST-MANOMETRE` (5), `YANGIN-ISLAK ALARM VANASI` (4), `8265.4500` (4), `G$CD8BAFFAE` (3), `XREF` (3), `G$CC9847496` (2), `TEST-VALVE` (2), `KV1` (2), `A$C2B904562` (2), `A$C006E4229` (2), `VALVE-MANOMETER1` (2), `YANGIN-KURU ALARM VANASI` (2), `A$C68E50811` (1), `0-MEK-IST-KÜRESEL VANA 1-2` (1), `A$C66BCA59E` (1), `G$CE936221F` (1), `PLGBB_8612__33` (1), `A$C9e52caec` (1)
</details>


---
## 03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina

Orijinal: `01c4b0ba-03-Azot_ve_Bas_n_l__Hava_Tesisat_-Ana_Bina.dwg` — 97228 çizgi parçası, 1550 daire, 3387 metin; 169 katman, 23 farklı blok (model uzayı).
Kapalı/dondurulmuş katman: 1 (ör. `-M-HV-MNF-TIP`).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_01.png` | A BLOK (EK); A BLOK; Altta Tünel; GIRIS 1 Teknik / İdari Personel; GIRIS 2 Üretim Personeli; *Havai hat taşıma çelik konstrüksiyonu uygulamada detay projesi hazırlanacaktır.; *Toprak altında ön izoleli boru.; *Havai hat. |
| 2 | pafta | `onizleme/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_02.png` | BASINÇLI HAVA TESİSATI SEMBOLLERİ; (SATIN ALIMINI ASELSAN YAPACAKTIR. MONTAJ VE; DEVREYE ALMA YÜKLENİCİ KAPSAMINDADIR.); GAZ AZOT BORUSU; KÜRESEL VANA; PİSLİK TUTUCU; FLOWMETRE; SU TUTUCU FİLTRE |
| 3 | pafta | `onizleme/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_03.png` | BASINÇLI HAVA TESİSATI SEMBOLLERİ; BASINÇLI HAVA BORUSU; KÜRESEL VANA; PİSLİK TUTUCU; FLOWMETRE; SU TUTUCU FİLTRE; MANOMETRE; ELK. OD.; TOPLANTI OD. 2; TOPLANTI OD. 1 |
| 4 | pafta | `onizleme/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_04.png` | *Toprak altından ön izoleli boru ile dağıtım yapılacaktır.; BASINÇLI HAVA TESİSATI SEMBOLLERİ; BASINÇLI HAVA BORUSU; KÜRESEL VANA; PİSLİK TUTUCU; FLOWMETRE; SU TUTUCU FİLTRE; MANOMETRE; BAKIM ODASI; KAT HOLÜ |
| 5 | pafta | `onizleme/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_05.png` | A-A; DUVARDAN İNİŞ PRİZ DETAYI; DUVARDAN İNİŞ JAK DETAYI; 1.KAT; ZEMİN KAT; TERAS KAT; CİHAZ LİSTESİ; BASINÇLI HAVA TESİSATI SEMBOLLERİ |
| 6 | serbest grup | `onizleme/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_06.png` | VAZİYET PLANI (±0.00 = 978.90) ÖLÇEK 1/500; ÇANKIRI BULVARI; YILDIRIM BEYAZIT CADDESİ; Giriş Kapısı; Servis Girişi; A BLOK (EK); A BLOK; P.1; KAT PLANLARI; DUVARDAN İNİŞ PRİZ DETAYI |

### Lejantlar

**BASINÇLI HAVA TESİSATI SEMBOLLERİ** — `lejant/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_lejant_01.png`, `lejant/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_lejant_01.txt`

> BASINÇLI HAVA BORUSU · BASINÇLI HAVA BORUSU · BASINÇLI HAVA BORUSU · BASINÇLI HAVA BORUSU · HEAT TRACING · KÜRESEL VANA · PİSLİK TUTUCU · BASINÇ DÜŞÜRÜCÜ VANA · FLOWMETRE · SU TUTUCU FİLTRE · M \| MANOMETRE

**BASINÇLI HAVA TESİSATI SEMBOLLERİ** — `lejant/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_lejant_02.png`, `lejant/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_lejant_02.txt` (aynı lejant 1 kez daha tekrar ediyor)

> BASINÇLI HAVA BORUSU · BASINÇLI HAVA BORUSU · BASINÇLI HAVA BORUSU · BASINÇLI HAVA BORUSU · KÜRESEL VANA · PİSLİK TUTUCU · FLOWMETRE · SU TUTUCU FİLTRE · M \| MANOMETRE

**BASINÇLI HAVA TESİSATI SEMBOLLERİ** — `lejant/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_lejant_03.png`, `lejant/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_lejant_03.txt`

> GAZ AZOT BORUSU · SIVI AZOT BORUSU · BASINÇLI HAVA BORUSU · BASINÇLI HAVA BORUSU · KÜRESEL VANA · PİSLİK TUTUCU · FLOWMETRE · SU TUTUCU FİLTRE · M \| MANOMETRE


### Boru/kanal çapı yazım biçimi

- x/x" (kesirli inç): 749 metin — ör. "3/4"", "1 1/4"", "1 1/2""
- xx" (inç): 446 metin — ör. "1"", "1 1/4"", "1 1/2"", "3"", "2"", "4"", "6"", "REVİZE HAT-2""
- DNxx: 139 metin — ör. "DN250", "DN300", "DN100", "DN150", "DN125", "DN15", "DN25", "DN65"
- PE/PPR dxx: 3 metin — ör. "DN65 HDPE PN16 BORU"
- Øxx: 2 metin — ör. "Ø32", "mevcut ısı merkezindenki Ø150 "

Not/hesap metinleri: `hesap/03_Azot_ve_Basincli_Hava_Tesisati_Ana_Bina_notlar.txt` (12 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `AS_TES_SUZGEC` (19764), `-M-MAHAL-ETIKET-NOT` (12240), `RAKOR02` (5810), `0-KRCN-IST-KÜRESEL VANA` (5806), `_MDS_BORU_22.00X1.00_BASINÇLI HAVA` (3487), `-M-HV-MNF-TIP` (2076), `ANA ORTA` (1728), `0-KRCN-BAS HAVA` (1464), `AS_PRFL_CELIK` (1214), `0-MEK-MED-AZOT` (1083), `-M-HVAC-R-RA1-SHKS-KNL2B-` (975), `_MDS_0` (919), `HH_DUVAR` (774), `SEV_TARAMA` (709), `+MC SOGUTMA KOLLEKTÖR` (669), `YOL_IZGARA_TARAMA` (606), `B_SUNDURMA_TARAMA` (482), `-M-MAHAL-DEBILER` (480), `0-KRCN-SHT-ROGAR` (412), `MED.GAZ YAZI` (408), `_MDS_TEE` (394), `M_SIHHİ_GENEL_CİHAZ 2` (372), `-M-MAHAL-ETK-` (360), `M_GENEL_KÜRESEL VANA (ISITMA TESİSATI)` (328), `SINIR_IST_DUVARI` (288), `-M-MAHAL-HAVA-DEGISIM` (240), `M_GENEL_TİTREŞİM YUTUCU` (228), `Y_YOL_KOTU` (210), `---___EB_draft00_parselsiniri` (208), `0` (194), `B_BETON_ZEMIN` (180), `M_GENEL_MANOMETRE` (180), `++MC KELEBEK VANA` (177), `AS_GOR` (151), `0-KRCN-IST-YAZI` (146), `AS_TA_HIDDEN` (143), `B_MERDIVEN_TARAMA` (139), `---___EB_draft01_aks` (135), `0-KRCN-IST-04CIHAZ` (130), `IMAR_ADA` (128)

Bloklar (model uzayı INSERT sayısı): `TEE` (394), `0-MEK-SHT-KÜRESELVANA` (372), `G$C63E5540C` (322), `A$C6A0AA91C` (166), `M-MHLETK-YNG` (120), `G$C6C5B105C` (17), `*U` (11), `0-MEK-IST-KÜRESEL VANA-1` (10), `A$C69E75F44` (4), `0-MEK-IST-KÜRESEL VANA 1-2` (4), `0-MEK-IST-PİSLİK TUTUCU` (4), `G$C96861C69` (4), `0-MEK-IST-MANOMETRE` (4), `basınç düşürücü 2` (4), `G$C551180CD` (3), `KOMP.` (3), `G$CD316F46C` (2), `A$C69A19712` (1), `G$CDA5BA388` (1), `XREF` (1), `G$CF910E365` (1), `G$C19F67D48` (1), `VKR32-Y` (1)
</details>


---
## 04_Pis_Su_Tesisati_Ana_Bina

Orijinal: `26640225-04-Pis_Su_Tesisat_-Ana_Bina.dwg` — 131411 çizgi parçası, 2224 daire, 3349 metin; 67 katman, 36 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_01.png` | TERAS KATI PLANI (+13.50 = 992.40) ÖLÇEK 1/100; T-02; MEKANİK TEKNİK HACİM; T-01; OPTİK ATIŞ PLATFORMU; İNİŞ; Ø110; Elektrikli ısıtıcı uygulanacaktır. Bakınız: Elektrik Tesisat Paftaları |
| 2 | pafta | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_02.png` | 1. KAT PLANI (+7.00 = 985.90) ÖLÇEK 1/100; 02a; ELK. OD.; MEKANİK TEKNİK HACİM - 2; MEKANİK TEKNİK HACİM - 1; TEM. OD.; Y.G.H; MUTFAK; TOPLANTI OD. 2; TOPLANTI OD. 1 |
| 3 | pafta | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_03.png` | ZEMİN KAT PLANI (±0.00 = 978.90) ÖLÇEK 1/100; TÜM TEMEL ALTI BORULAMA KABA İŞLER YAPIM İŞİ KAPSAMINDA YAPILMIŞTIR; 03'; 01'; 02a; A-A KESITI; DEPO ŞERİT ISITICI UYGULAMA DETAYI; 08a; BAKIM ODASI; KAT HOLÜ |
| 4 | pafta | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_04.png` | 1.KAT; ZEMİN KAT; ÇATI KAT; PİSU SU KOLON ŞEMASI; PİS SU TESİSAT SEMBOLLERİ; PİS SU TESİSATI BORUSU; ÇEKVALF; PİS SU KOLON NUMARASI |
| 5 | pafta | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_05.png` | ÇATI PLANI ÖLÇEK 1/100; HASSAS KLİMA DIŞ ÜNİTELERİ; SOĞUTMA GRUPLARI; sifonik yğm.szgc.; EĞİM %1; KUVVET MERKEZI; Ø100; Elektrikli ısıtıcı uygulanacaktır. Bakınız: Elektrik Tesisat Paftaları |
| 6 | pafta | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_06.png` | TERAS KATI PLANI (+13.50 = 992.40) ÖLÇEK 1/100; ÇATIYA SERBEST BIRAKILACAKTIR; Ø100; Elektrikli ısıtıcı uygulanacaktır. Bakınız: Elektrik Tesisat Paftaları |
| 7 | pafta | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_07.png` | 1. KAT PLANI (+7.00 = 985.90) ÖLÇEK 1/100; Ø100; İNİŞ; Ø63; Ø75; Ø110; Ø90; Ø56 |
| 8 | pafta | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_08.png` | ZEMİN KAT PLANI (±0.00 = 978.90) ÖLÇEK 1/100; İNİŞ; Ø200; Ø160; Ø125; YAĞMUR SUYU RÖGARI; Toprak Dolgu altından çıkacaktır.; Ø100 |
| 9 | pafta | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_09.png` | YAGMUR SUYU KOLON ŞEMASI; SİFONİK SİSTEM KOLON ŞEMASI; 1.KAT; ZEMİN KAT; TERAS KAT; PİS SU TESİSAT SEMBOLLERİ; PİS SU TESİSATI BORUSU; ÇEKVALF; ÇATI KATI; ÇATIYA SERBEST BIRAKILACAKTIR |
| 10 | serbest grup | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_10.png` | 04/A; KAT PLANLARI; YAĞMUR SUYU TESİSATI; OPAK BİNASI PROJE YAPIM İŞİ; ASELSAN AKYURT-1 YERLEŞKESİ; UYGULAMA PROJE TESLİMİ; ANA BİNA; 1.KAT; ZEMİN KAT; TERAS KAT |
| 11 | serbest grup | `onizleme/04_Pis_Su_Tesisati_Ana_Bina_11.png` | KAT PLANLARI; PİS SU TESİSATI; OPAK BİNASI PROJE YAPIM İŞİ; ASELSAN AKYURT-1 YERLEŞKESİ; UYGULAMA PROJE TESLİMİ; ANA BİNA; 1.KAT; ZEMİN KAT; ÇATI KAT; KULLANICI KOORDİNESİ / MUTABAKAT |

### Lejantlar

**PİS SU TESİSAT SEMBOLLERİ** — `lejant/04_Pis_Su_Tesisati_Ana_Bina_lejant_01.png`, `lejant/04_Pis_Su_Tesisati_Ana_Bina_lejant_01.txt` (aynı lejant 1 kez daha tekrar ediyor)

> PİS SU TESİSATI BORUSU · YAĞMUR SU TESİSATI BORUSU · ÇEKVALF · PS \| X \| PİS SU KOLON NUMARASI · DPX \| YAĞMUR SU KOLON NUMARASI · YER SÜZGECİ · YER IZGARASI · RÖGAR


### Şemalar

- `sema/04_Pis_Su_Tesisati_Ana_Bina_sema_04.png` — PİSU SU KOLON ŞEMASI. Sık metinler: Ø110, ∅75, CİHAZ GİDERİNE BAĞLANACAKTIR., ∅50, Ø75, Klima drenajı, Ø125, Ø160, ∅110, ÇEKVALF, 1.KAT, ZEMİN KAT, ÇATI KAT, GİDER, Ø63 hdpe boru, BULAŞIK, MAKİNASI, Döşeme üstünde yerden 10 cm çıkan gider hattı bırakılacaktır., SOLVENT, PİSU SU KOLON ŞEMASI, 11,5 YB./ Ø110, 3,5 YB./ Ø75, Dalgıç Pompasına, Asansör kuyusu, 5,0 YB./ Ø75
- `sema/04_Pis_Su_Tesisati_Ana_Bina_sema_09.png` — YAGMUR SUYU KOLON ŞEMASI; SİFONİK SİSTEM KOLON ŞEMASI. Sık metinler: Ø100, Ø160, YAĞMUR SUYU RÖGARI, Ø110, ÇATIYA SERBEST BIRAKILACAKTIR, Ø125, Ø75, Ø63, Ø90, Ø56, Ø200, 1.KAT, ZEMİN KAT, TERAS KAT, ÇATI KATI, Ø50, YAGMUR SUYU KOLON ŞEMASI, PİS SU TESİSAT SEMBOLLERİ, PİS SU TESİSATI BORUSU, ÇEKVALF, PİS SU KOLON NUMARASI, YER SÜZGECİ, YAĞMUR SU TESİSATI BORUSU, DPX, YAĞMUR SU KOLON NUMARASI

### Boru/kanal çapı yazım biçimi

- Øxx: 1181 metin — ör. "Ø110", "Ø75", "Ø160", "Ø100", "Ø125", "25x25 cm - Ø110", "Ø90", "Ø63 hdpe boru"
- PE/PPR dxx: 30 metin — ör. "Ø63 hdpe boru", "NOT:MEVCUT PVC HATLARININ UYUM", "U-PVC BOŞALTMA HATLARI (DIŞ ÇA", "U-PVC GİDER TESİSATI BAĞLANTIS"
- mm: 4 metin — ör. "KİMYASAL ATIK DEPOSU (PP) - PO", "SOLVENT ATIK TANKI (AISI 304) ", "HAVALIK Ø32 mm,", "SOLVENT GİDER TESİSATI BAĞLANT"
- xx" (inç): 2 metin — ör. "HAVALIK, PASLANMAZ ÇELİK BORU ", "SOLVENT GİDER TESİSATI BAĞLANT"

Not/hesap metinleri: `hesap/04_Pis_Su_Tesisati_Ana_Bina_notlar.txt` (19 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `0-KRCN-HVL-SANTRAL` (20192), `AS_TES_SUZGEC` (19754), `-M-MAHAL-ETIKET-NOT` (12036), `0-KRCN-SHT-LAVABO` (7765), `0-KRCN-SHT-YAZI-ÇAP-PİSSU` (3178), `0-KRCN-SHT-ROGAR` (2308), `0-KRCN-SHT-PİSSU-BORU` (1963), `0-KRCN-SHT-SÜZGEÇBANYO` (1801), `0-KRCN-SHT-TUVALETKLOZET` (1114), `0-KRCN-SHT-DUŞTEKNESİKARE` (992), `0-MEK-SHT-aa YAĞMURSUYUBORUSU-100` (780), `0-KRCN-SHT-KOLADI-YAZIYAĞMURSUYU` (613), `0-KRCN-M_PİSSU` (568), `0-KRCN-SHT-TUVALETNORMAL` (528), `0-KRCN-SHT-05CIHAZ` (490), `0-KRCN-SHT-ÇEKVALF` (478), `-M-MAHAL-DEBILER` (472), `0-MEK-SHT-KOLADI-YAZIYAĞMURSUYU` (451), `-M-MAHAL-ETK-` (354), `0` (340), `0-KRCN-SHT-EVYEBİRGÖZLÜ` (299), `0-KRCN-MİMARİ-220526` (272), `AS_PRFL_CELIK` (250), `-M-MAHAL-HAVA-DEGISIM` (236), `0-KRCN--DELİK BORU` (212), `0-KRCN-SHT-PİSUAR` (180), `AS_SMB_KOT` (177), `0-KRCN-SHT-YAZI-KOLADI-PİSSU` (156), `0-KRCN-SHT-02CIHAZ` (138), `0-KRCN-SHT-YAĞMURSUYUBORUSU-100` (133), `0-KRCN-SHT-SOGUKSU` (132), `0-MEKANİK NOTLAR` (131), `-M-MAHAL-NO` (118), `-M-MAHAL-NOM` (118), `-M-MAHAL-ETIKET-NOTM` (118), `AS_YAZI_EGIM` (114), `0-KRCN-SHT-LAVABOÖZÜRLÜ` (88), `0-KRCN-SHT-CİHAZ NOTU` (78), `GEB-BEZUG` (76), `0-KRCN-SHT-SICAKSU` (64)

Bloklar (model uzayı INSERT sayısı): `0-MEK-SHT-ZKLN-SÜZGEÇ BANYO` (145), `M-MHLETK-YNG` (118), `A$C75464483-` (118), `DİKİŞLİ ÇELİK BORU-DN50` (106), `0-MEK-SHT-SÜZGEÇ BANYO-1` (71), `A$C599c51df` (57), `SE2` (57), `A$C354C280E` (39), `G$CADAFA931` (32), `0-MEK-SHT-ZKLN-KLOZET ASMA GİZLİ REZERVUAR` (24), `.CN.BACA` (18), `*U` (11), `G$CD316F46C` (11), `G$CAA6DA624` (11), `0-MEK-SHT-ZKLN-PİSUAR-1` (9), `0-MEK-SHT-ZKLN-ALATURKA TUVALET GIZLI` (8), `0-MEK-SHT-ZKLN-PİSUAR BÖLMESİ` (5), `0-MEK-SHT-ZKLN-MAKİNA BULAŞIK` (5), `G$C18012375` (5), `0-KRCN-SHT-LAV.YUV.BATARYALI-50` (4), `0-MEK-SHT-ZKLN-LAV.MUSLUKLU-60` (4), `A$C2C4C0CCB` (4), `0-MEK-SHT-ZKLN-LAV.TEZGAHALTI YEDİLİ` (3), `G$C5D3A4265` (2), `SUZGEC2` (2), `G$C1D0EB590` (2), `TEMİZLİK ODASI TEFRİŞİ` (2), `ENGELLİ ALAFRANGA KOLON` (2), `ENGELLİ LAVABO KOLON` (2), `0-MEK-SHT-ZKLN-LAV.TEZGAHALTI BEŞLİ` (2), `XREF` (2), `G$CC9077728` (2), `0-MEK-SHT-ZKLN-LAV.TEZGAHALTI DÖRTLÜ-1` (1), `A$C69D49E3A` (1), `A$C6A0DA56D` (1), `G$CBC016F8E` (1)
</details>


---
## 05_Temiz_Su_Tesisati_Ana_Bina

Orijinal: `f88e2f09-05-Temiz_Su_Tesisat_-Ana_Bina.dwg` — 418054 çizgi parçası, 12567 daire, 4532 metin; 215 katman, 49 farklı blok (model uzayı).
Kapalı/dondurulmuş katman: 1 (ör. `XREF|0-KRCN-AYDINLATMA-130426`).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/05_Temiz_Su_Tesisati_Ana_Bina_01.png` | TERAS KATI PLANI (+13.50 = 992.40) ÖLÇEK 1/100; T-02; MEKANİK TEKNİK HACİM; T-01; OPTİK ATIŞ PLATFORMU; İNİŞ; KULLANIM NOKTALARINA; 0,5 YB./∅25 |
| 2 | pafta | `onizleme/05_Temiz_Su_Tesisati_Ana_Bina_02.png` | 1. KAT PLANI (+7.00 = 985.90) ÖLÇEK 1/100; 01a; ELK. OD.; MEKANİK TEKNİK HACİM - 2; MEKANİK TEKNİK HACİM - 1; TEM. OD.; Y.G.H; MUTFAK; TOPLANTI OD. 2; TOPLANTI OD. 1 |
| 3 | pafta | `onizleme/05_Temiz_Su_Tesisati_Ana_Bina_03.png` | ZEMİN KAT PLANI (±0.00 = 978.90) ÖLÇEK 1/100; DETAY A-A; Asma Tavan; Z-42; ELK. OD.; Z-46; ELEKTRİK OD.; Z-45; BAKIM ODASI; KAT HOLÜ |
| 4 | pafta | `onizleme/05_Temiz_Su_Tesisati_Ana_Bina_04.png` | TADİLAT ALANI; A-BLOK; A-A KESİT; TV 2 Kabini; TV 1 Kabini; THA 1 Kabini; Büyük cihazlara ait giriş-çıkış kapısı; YALIN ÜRETİM HATLARI; ÇALDIRAN TOPLANTI ODASI; 1.KAT |
| 5 | pafta | `onizleme/05_Temiz_Su_Tesisati_Ana_Bina_05.png` | SIHHİ DETAY |
| 6 | serbest grup | `onizleme/05_Temiz_Su_Tesisati_Ana_Bina_06.png` | KAT PLANLARI; TEMİZSU TESİSATI; OPAK BİNASI PROJE YAPIM İŞİ; ASELSAN AKYURT-1 YERLEŞKESİ; UYGULAMA PROJE TESLİMİ; ANA BİNA; İNŞAAT ve EMLAK DİREKTÖRLÜĞÜ ONAYI; BAŞLIK; KULLANICI KOORDİNESİ / MUTABAKAT |

### Lejantlar

**TEMİZ SU TESİSAT SEMBOLLERİ** — `lejant/05_Temiz_Su_Tesisati_Ana_Bina_lejant_01.png`, `lejant/05_Temiz_Su_Tesisati_Ana_Bina_lejant_01.txt`

> CİHAZ LİSTESİ · NO \| CIHAZ ADI \| AD. \| CIHAZ OZELLIKLERI \| ELK.GÜCÜ · SOĞUK KULLANMA SUYU TESİSATI BORUSU · B-09 \| BOYLER \| 2 \| 600 Lt.HACİMLİ MİNİMUM SICAK SU ÇIKIŞ DEBİSİ 910 LT BAKIR BORULU TEK SERPANTİNLİ HIZLI BOYLER \| - · SICAK KULLANMA SUYU TESİSATI BORUSU · P-39 \| KULLANMA SUYU SİRKÜLASYON POMPASI \| 1 \| 5,0 m³/h - 6,5 mSS FREKANS KONVERTÖRLÜ TEKLİ TİP İNLINE POMPA (1 ADET YEDEK) \| 2 x 0,2 Kw · SICAK SU SİRKÜLASYON TESİSATI BORUSU · YUMUŞAK SU TESİSATI BORUSU · DRENAJ TESİSATI BORUSU · KÜRESEL VANA · PİSLİK TUTUCU \| DEİYONİZE SU SİSTEMİ CİHAZ LİSTESİ · ÇEKVALF \| NO \| CIHAZ ADI \| AD. \| CIHAZ OZELLIKLERI \| ELK.GÜCÜ · T \| 40 \| DEİYONİZASYON KOLON SETİ \| 4 \| 5,0 m³/h Deiyonize Su FRP Gövdeli, PLC RO Kontrollü (Kuvvetli Anyonik Exchanger Twin Set, Kuvvetli Katyonik Exchanger Twin Set) \| - · TERMOMETRE · M \| 41 \| HİDROFOR SETİ \| 1 \| Paket Tip İkiz Hidrofor - Debi: 5,0 m³/h Basıncı: 40-60 mSS \| 11,0 Kw · MANOMETRE · 42 \| SAF SU DEPOSU \| 2 \| 500 lt. Saf Su Tankı Plastik Mat \| - · KOMPANSATÖR · 43 \| DEİYONİZE SAF SU CİHAZI (ANA SİSTEM) \| 1 \| 2 m³/h Deiyonize Saf Su Cihazı \| - · EMNİYET VANASI \| 44 \| AKTİF KARBON FİLTRE \| 1 \| 5 m³/h 1200 IODIN Food Grade Aktif Karbon \| - · FK · POMPA TEKLİ / FREKANS KONVERTÖRLÜ \| 45 \| ULTRAVIYOLET DEZENFEKSİYON \| 2 \| 5 m³/h Ultraviyole Dezenfeksiyon Cihazı-100W Mikrokontrollü, Hidrofor Sinyal Otomasyonlu \| 2 x 0.1 Kw · TSX \| TEMİZ SU KOLONU NUMARASI \| 46 \| MOBİL ULTRA SAF SU CİHAZI (LABRATUVAR) \| 1 \| 0,06 m³/h Mobil Ultra Saf Su Cihazı -Depo Kapasitesi 150 lt \| - · KOMPANSATÖR


### Şemalar

- `sema/05_Temiz_Su_Tesisati_Ana_Bina_sema_04.png` — SIHHİ TESİSAT AKIŞ ŞEMASI; SIHHİ TESİSAT KOLON ŞEMASI; BKNZ AKIŞ ŞEMASI; DEVAMI İÇİN AKIŞ ŞEMASINA BAKINIZ. Sık metinler: 90x160cm, Ø32, Ø25, Üretim masası, Ø63, Dolap, KULLANIM, NOKTALARINA, 50x50cm, Yeniden işlem masası, Ø40, Rack, 110x110cm, N-gaz, HASSAS KLİMA, Bank (ayakkabılık), 120x70x46cm, 1700kg, Test masası, +2.00 Kotu, Ø50, Alt takım, 3,5 YB./∅32, Servis masası, 60x200cm

### Boru/kanal çapı yazım biçimi

- Øxx: 1027 metin — ör. "Ø32", "Ø25", "Ø63", "Ø40", "Ø50", "0,5 YB./ Ø25", "Ø100", "1,0 YB./ Ø25"
- xx" (inç): 50 metin — ör. "2"", "4"", "1"", "5"", "BORU NO AİT OLDUĞU YER ÇAPI 01"
- xx/yy (kanal ölçüsü): 34 metin — ör. "300x150", "300x300", "450x200", "250x200", "550x200"
- x/x" (kesirli inç): 10 metin — ör. "1/2"", "3/4""
- DNxx: 1 metin — ör. "DN50"

Not/hesap metinleri: `hesap/05_Temiz_Su_Tesisati_Ana_Bina_notlar.txt` (22 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `0-KRCN-MİMARİ-220526` (28979), `G_0.09` (27007), `0-KRCN-HVL-SANTRAL` (20192), `TF_Mobilya` (14044), `-M-MAHAL-ETIKET-NOT` (12036), `0-KRCN-IST-KÜRESEL VANA` (7786), `0-KRCN-SHT-LAVABO` (7777), `0-KRCN-SHT-HİDROFOR` (6480), `DV_alçıpanel_duvar_yeni` (6194), `0-KRCN-SHT-YAZI-ÇAP-TEMSU` (2826), `0-KRCN-TESİSAT` (2428), `0-KRCN-SHT-SOGUKSU` (2262), `1轮廓线` (2260), `0-KRCN-SHT YUMUŞAK SU ÇAP` (1448), `A_Betonarme_Tarama` (1386), `0-KRCN-SHT-PROSES-BORU` (1165), `0-KRCN-SHT-TUVALETKLOZET` (1116), `0-KRCN-SHT-DUŞTEKNESİKARE` (992), `TF_Cihaz` (913), `D_Aluminyum` (899), `0-KRCN-SHT-ŞOK DUŞ` (844), `PN_Aluminyum` (779), `0-KRCN-PLATE` (664), `A_Duvar-alçiplak` (577), `Em.K - FFU` (567), `0-KRCN-SHT-03CIHAZ` (540), `A_celik` (539), `0-KRCN-SHT-TUVALETNORMAL` (528), `0-MEK-SHT-YAZI-ÇAP-TEMSU` (519), `-M-MAHAL-DEBILER` (472), `A8-MATERIAALIT` (462), `2细实线` (416), `KP_Aksesuar` (408), `TF_Cihaz_yazı` (391), `A_Aks` (383), `实体` (360), `-M-MAHAL-ETK-` (355), `A_Arka` (345), `M00$0$KP_Aksesuar` (341), `0-KRCN-SHT-SICAKSU` (340)

Bloklar (model uzayı INSERT sayısı): `DONUT` (514), `0-MEK-SHT-KÜRESELVANA` (468), `0-MEK-SHT-ARAMUSLUK` (200), `M-MHLETK-YNG` (118), `*U` (73), `0-MEK-IST-KÜRESEL VANA-1` (62), `SE2` (57), `0-MEK-SHT-ZKLN-KLOZET ASMA GİZLİ REZERVUAR` (26), `0-MEK-IST-MANOMETRE` (15), `M12` (12), `0-MEK-SHT-ZKLN-PİSUAR-1` (9), `0-MEK-SHT-ZKLN-ALATURKA TUVALET GIZLI` (8), `0-MEK-SHT-ZKLN-SÜZGEÇ BANYO` (8), `A$C6AE706CD` (8), `A$C75464483` (7), `0-MEK-IST-ÇEKVALF` (6), `plgbb.8612` (6), `0-MEK-IST-PİSLİK TUTUCU` (5), `0-MEK-SHT-ZKLN-PİSUAR BÖLMESİ` (5), `0-MEK-SHT-ZKLN-MAKİNA BULAŞIK` (5), `0-KRCN-SHT-LAV.YUV.BATARYALI-50` (4), `0-MEK-IST-TERMOMETRE` (4), `0-MEK-IST-KOMPANSATÖR` (4), `0-MEK-SHT-ZKLN-LAV.MUSLUKLU-60` (4), `A$C660FDDFE` (4), `8265.4500` (4), `0-MEK-SHT-ZKLN-LAV.TEZGAHALTI YEDİLİ` (3), `K` (2), `0-MEK-IST-POMPA` (2), `G$C5D3A4265` (2), `TEMİZLİK ODASI TEFRİŞİ` (2), `ENGELLİ ALAFRANGA KOLON` (2), `ENGELLİ LAVABO KOLON` (2), `0-MEK-SHT-ZKLN-LAV.TEZGAHALTI BEŞLİ` (2), `EYE WASH & SHOWER` (2), `A$C69F6072A` (2), `G$CC571C566` (2), `G$CE20AE63A` (2), `G$CFC3FCC18` (2), `XREF` (2)
</details>


---
## 06_Havalandirma_Tesisati_Ana_Bina

Orijinal: `de5e0301-06-Havaland_rma_Tesisat_-Ana_Bina.dwg` — 511305 çizgi parçası, 3898 daire, 52957 metin; 205 katman, 329 farklı blok (model uzayı).
Kapalı/dondurulmuş katman: 4 (ör. `-M-HV-KANAL-TEXT-CM`, `-M-HV-KANAL-TEXT2`, `-M-HV-MNF-TIP`, `-M-HVAC-R-KS01-FLX-AKS-`).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_01.png` | DETAY-1; NOTLAR; CEPHEDEN TAZE HAVA PANJURU İLE HAVA GİRİŞİ; CEPHEDEN EGZOZ PANJURU İLE HAVA ATIŞI; ÇATI ÜST KOTUNUN 1 METRE ÜZERİNDEN JETCAP İLE ATIŞ (BKZ DETAY-1); ÇATI ÜST KOTUNUN 1,5 METRE ÜZERİNDEN JETCAP İLE ATIŞ (BKZ DETAY-1); PANJUR İLE SERBEST EMİŞ (PANJURDAKİ EFEKTİF HAVA HIZI 2,5m/s OLACAK ŞEKİLDE); DRENAJ BOĞAZI; ÇATI EN YÜKSEK NOKTA HİZASI |
| 2 | pafta | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_02.png` | DEPO BAKIM ALANI; NOT-1:YAĞ DUMAN TOPLAMA SİSTEMİ PAKET SİSTEM OLUP OTOMASYONA HABERLEŞME İÇİN UÇ VERİLECEKTİR.; HASSAS KLİMA CİHAZLARI PAKET SİSTEM OLUP,OTOMASYONA HABERLEŞME İÇİN UÇ VERİLECEKTİR.; BAKINIZ NOT-1'E; KS-; AS-; ELK. OD.; MEKANİK TEKNİK HACİM - 2; TOPLANTI OD. 2; TOPLANTI OD. 1 |
| 3 | pafta | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_03.png` | HASSAS KLİMA CİHAZLARI PAKET SİSTEM OLUP,OTOMASYONA HABERLEŞME İÇİN UÇ VERİLECEKTİR.; KARE PETEK MENFEZLER SÖKÜLEBİLİR FİLTRELİ TİP OLACAKTIR.; Z-46; ELK. OD.; Z-45; TEM. OD.; Z-44; KUVVET MERKEZİ; BAKIM ODASI; KAT HOLÜ |
| 4 | pafta | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_04.png` | KESİT - 2 ÖLÇEK 1/100; ZEMİN KAT (±0.00 978.90); 1. KAT (+7.00); ÇATI KATI (+13.50); ÇATI (+18.35) |
| 5 | pafta | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_05.png` | KESİT - 2 ÖLÇEK 1/100; A-A KESİTİ; D-D KESİTİ; HASSAS KLİMA KANAL KESİT; HAVALANDIRMA TESİSATI SEMBOLLERİ; ÜFLEME KANALI; EMİŞ KANALLARI; FLEX BAĞLANTI KANALI (İZOLELİ / İZOLESİZ); ÇATI TİPİ ASPİRATÖR; ZEMİN KAT (±0.00 978.90) |
| 6 | pafta | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_06.png` | KESİT - 2 ÖLÇEK 1/100; A-A KESİTİ; B-B KESİTİ; D-D KESİTİ; HASSAS KLİMA KANAL KESİT; MFD; BDD; -850x650; ÇATI TİPİ ASPİRATÖR; ÇATI (+18.35) |
| 7 | pafta | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_07.png` | KESİT - 2 ÖLÇEK 1/100; A-A KESİTİ; B-B KESİTİ; C-C KESİTİ; D-D KESİTİ; HASSAS KLİMA KANAL KESİT; HAVALANDIRMA TESİSATI SEMBOLLERİ; MFD; ÇATI TİPİ ASPİRATÖR; ZEMİN KAT (±0.00 978.90) |
| 8 | pafta | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_08.png` | KS-; AS-; 15500 m3/h; E.A.P.:2500x900 mm; EGZOZ ATIS PANJURU; 5000 m3/h; E.A.P.:2000x400 mm; 16450 m3/h |
| 9 | pafta | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_09.png` | HAVALANDIRMA DETAY |
| 10 | serbest grup | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_10.png` | KS-; m/h; 69000 m3/h; T.H.P.:7000x700 mm; TAZE HAVA PANJURU; 15850 m3/h; E.A.P.:2000x900 mm; EGZOZ ATIS PANJURU |
| 11 | serbest grup | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_11.png` | m/h; YEM; USW; ÇSM; Ø225; Ø180; Ø200; TİP-1 ( 800 kg) |
| 12 | serbest grup | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_12.png` | m/h; YEM; USW; TİP-1 ( 800 kg); 825x125; VAV; Ø250; HASSAS KLİMA |
| 13 | serbest grup | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_13.png` | m/h; USW; ÇSM; TİP-1 ( 800 kg); TİP-2 (400 kg); 610x610; VAV; Ø160 |
| 14 | serbest grup | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_14.png` | 10000 m3/h; E.A.P.:2000x700 mm; EGZOZ ATIS PANJURU; m/h; M.D.D.; MDD |
| 15 | serbest grup | `onizleme/06_Havalandirma_Tesisati_Ana_Bina_15.png` | KAT PLANLARI; HAVALANDIRMA TESİSATI; ANA BİNA; OPAK BİNASI PROJE YAPIM İŞİ; ASELSAN AKYURT-1 YERLEŞKESİ; UYGULAMA PROJE TESLİMİ; İNŞAAT ve EMLAK DİREKTÖRLÜĞÜ ONAYI; BAŞLIK; KULLANICI KOORDİNESİ / MUTABAKAT |

### Lejantlar

**HAVALANDIRMA TESİSATI SEMBOLLERİ** — `lejant/06_Havalandirma_Tesisati_Ana_Bina_lejant_01.png`, `lejant/06_Havalandirma_Tesisati_Ana_Bina_lejant_01.txt`

> +18.70 \| +18.95 · +18.60 \| +18.35 · ÇATI (+18.35) · HAVALANDIRMA TESİSATI SEMBOLLERİ · T-03 ATIŞ TERASI \| T-02 OPTİK ATIŞ PLATFORMU · +14.75 \| +14.75 · J \| I \| F \| D \| C \| ÜFLEME KANALI \| B · +13.85 \| +13.85 · ÇATI KATI (+13.50) \| +13.50 \| 5.14- \| 0.60 \| 3 \| +13.50 \| +13.50 \| EMİŞ KANALLARI · 3300 \| -650x300 \| -65x30 \| m/h · 550 \| x \| 350 \| 4.23- \| 0.61 \| 3 \| BUSBAR \| +18.95 \| +18.70 \| WC EMİŞ KANALLARI · 1500 \| -300x250 \| -30x25 \| m/h \| +18.60 · 350 \| x \| 300 \| YANGIN \| DN150 \| +18.35 · Ø25 \| Ø40 \| Ø40 \| Ø63 \| Ø40 \| 5.17- \| 0.58 \| 3 \| HASSAS KLİMA ÜFLEME KANALI · 3'' \| 2'' \| 2'' \| 1 1/4'' \| 1 1/4'' \| Ø50 \| 2'' \| 3600 \| -850x500 \| -85x50 \| m/h · 600 \| x \| 350 \| HASSAS KLİMA EMİŞ KANALLARI · FLEX BAĞLANTI KANALI (İZOLELİ / İZOLESİZ) · 1-04 A.13 AMBAR \| 1-08 ANA KORİDOR \| 1-02a A.6 KART ÜRETİM · KARDEX \| EGZOST HAVASI ATIŞ PANJURU · T-02 OPTİK ATIŞ PLATFORMU \| T-03 ATIŞ TERASI · +14.75 \| +14.75 · TAZE HAVA ALIŞ PANJURU · 5.48- \| 0.78 \| +13.85 \| +13.85 · +13.50 \| 2850 \| -500x250 \| -50x25 \| m/h \| 3 \| +13.50 \| +7.40 \| +13.50 · 650 \| x \| 250 \| +7.00 \| +7.10 \| +7.00 \| YUVARLAK KANAL ÜFLEME MENFEZİ · 1. KAT (+7.00) · 20300 \| 9.15- \| 0.85 \| 3 \| 12800 \| 7.72- \| 0.73 \| 3 · Ø25 \| Ø40 \| Ø50 \| Ø63 \| Ø40 \| YANGIN \| DN150 \| -1400x500 \| -140x50 \| m/h \| -850x350 \| -85x35 \| m/h · 1400 \| x \| 500 \| 1150 \| x \| 450 · 3'' \| 3/4'' \| 3/4'' \| Ø65 \| 1 1/4'' \| 1 1/4'' \| 2 1/2'' \| 2 1/2'' \| YUVARLAK KANAL EMİŞ MENFEZİ · 1-02a A.6 KART ÜRETİM \| 1-08 ANA KORİDOR \| 1-04 A.13 AMBAR \| ÜFLEME SLOT DİFÜZÖRÜ · KARDEX · Z-04 A.13 AMBAR \| Z-13 ANA KORİDOR \| Z-02 A.1 MEKANİK TALAŞLI İMALAT · EMİŞ SLOT DİFÜZÖRÜ · +7.40 · +7.00 \| +7.10 \| +7.00 · +0.10 \| 17.68- \| 17.68- \| 18.48 \| +0.10 \| GEMİCİ ANEMOSTADI · +0.10 \| 2000 \| X \| +0.10 \| m/h \| 3 · ZEMİN KAT (±0.00 978.90) \| Ø \| 200 \| 10 Pa \| 0 W \| 5.38- \| 0.63 \| 3 · 6.20- \| 6.20- \| 0.71 \| 3 \| VAV \| 3750 \| -600x350 \| -60x35 \| m/h · 5500 \| X \| m/h \| 6.01- \| 6.01- \| 0.77 \| 3 \| Ø250 \| 1250 \| 4.26- \| 0.69 \| 3 \| 600 \| x \| 350 · Ø \| 560 \| 4250 \| X \| m/h \| -350x250 \| -35x25 \| m/h \| MİFT SIRA MENFEZ DİFÜZÖRÜ · Ø \| 500 \| 350 \| x \| 250 · A \| B \| C \| D \| F \| 5.29- \| 0.56 \| 5500 \| 5.93- \| 0.63 \| 3 \| I \| J · 4250 \| m/h \| 3 \| -700x400 \| -70x40 \| m/h · 700 \| -700x350 \| -70x35 \| x \| 350 \| 700 \| x \| 400 \| SWIRL DİFÜZÖR · A-A KESİTİ \| Z-02 A.1 MEKANİK TALAŞLI İMALAT \| Z-13 ANA KORİDOR \| Z-04 A.13 AMBAR · +18.70 \| +18.95 · +18.60 \| +18.35 \| PERFORE MENFEZ · ÇATI (+18.35) · HASSAS KLİMA · +0.10 \| +0.10 \| +0.10 \| +0.10 · EMİŞ MENFEZİ (TEK SIRA KANATLI) · T-03 ATIŞ TERASI \| T-02 OPTİK ATIŞ PLATFORMU · +14.75 \| +14.75 \| DUVAR TİPİ ASPİRATÖR · +13.85 \| +13.85 · ÇATI KATI (+13.50) \| +13.50 \| 5.14- \| 0.60 \| 3 \| +13.50 \| +13.50 \| JET CAP · 3300 \| -650x300 \| -65x30 \| m/h · 550 \| x \| 350 \| 4.23- \| 0.61 \| 3 \| BUSBAR


### Boru/kanal çapı yazım biçimi

- xx/yy (kanal ölçüsü): 1081 metin — ör. "610x610", "825x125", "1225x125", "200x150", "310x310", "300x200", "150x150", "400x150"
- Øxx: 804 metin — ör. "Ø250", "Ø180", "Ø200", "Ø300", "Ø160", "Ø225", "Ø140", "Ø100"
- DNxx: 33 metin — ör. "DN25", "DN150", "DN40", "DN100", "DN50"
- xx" (inç): 28 metin — ör. "11/2"", "1"", "4"", "3"", "10"", "11/4"", "21/2"", "5""
- mm: 15 metin — ör. "T.H.P.:3500x700 mm", "T.H.P.:7000x700 mm", "E.A.P.:2000x900 mm", "E.A.P.:2000x400 mm", "E.A.P.:2500x900 mm", "E.A.P.:2000x700 mm", "E.A.P.:2000x1000 mm", "E.A.P.:2000x1100 mm"
- x/x" (kesirli inç): 14 metin — ör. "3/4""

Not/hesap metinleri: `hesap/06_Havalandirma_Tesisati_Ana_Bina_notlar.txt` (20 tekil metin, 1 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `0-KRCN-HVL-SANTRAL` (40409), `-M-HV-KANAL-TEXT` (35737), `AS_GOR_UZAK2` (25916), `T-DETAY-ASKI` (22376), `-ROT` (19110), `-M-HV-MNF-IC` (15498), `-M-MAHAL-ETIKET-NOT` (12138), `-M-HV-MNF-TIP` (11428), `0-KRCN-IST-FANCOİL ZON-1` (10000), `0` (7880), `-M-HVAC-S-SA1-KNL2B-` (7389), `-M-HV-MNF` (6030), `-M-HV-KANAL-TEXT-CM` (5830), `-M-HVAC-S-SA1-HK-KNL2B-` (5492), `-SOMUN+PUL` (4042), `-M-HVAC-R-RA1-HK-KNL2B-` (3254), `-M-HV-KANAL-TEXT-MM` (2938), `0-KRCN-KELEPÇE` (2843), `-M-HV-MNF-OK` (2640), `-M-HV-KANAL-TEXT1` (2420), `AS_PRFL_DEMIR` (2400), `-M-HVAC-S-SA1-HK-KNLTXT-` (2385), `-M-HV-KANAL-HIZ` (2259), `-M-HV-KANAL-PAM` (2259), `-M-HV-KANAL-HIZH` (2259), `-M-HVAC-S-MNF2B-` (1939), `-M-HVAC-S-SA1-CVAV-` (1856), `-M-HVAC-R-RA1-HK-KNLTXT-` (1745), `KELEPCE015` (1676), `-M-HVAC-E-PROSES-KNL2B-` (1649), `-M-HVAC-S-SA1-KNLTXT-` (1645), `-M-HVAC-S-SA1-FLX-TRM-` (1617), `-M-HV-MNF-KOD` (1616), `-M-HV-MNF-OLCU` (1612), `AS_PRFL_ALU` (1520), `-M-HVAC-S-FCU-FLX-TRM-` (1474), `-M-HVAC-E-PROSES-PP-KNL2B-` (1461), `-M-HVAC-E-WC-FLX-TRM-` (1350), `-M-HV-KANAL-TEXT2` (1210), `-M-HVAC-E-EF-KNL2B-` (1205)

Bloklar (model uzayı INSERT sayısı): `DEBI002` (1100), `DEBI110` (869), `DEBI001` (614), `2D-KND90002` (423), `FLEX100` (290), `2D-KND45010` (279), `2D-USWR1-600` (271), `2D-ÇSM1-610` (255), `*U` (252), `KNLKLP01` (181), `KNLAYR01` (170), `M-MHLETK-ISI` (119), `2D-UA1-610` (89), `2D-EM1-82.512.5` (77), `G$CC6CD354C` (62), `A$C67C6E213` (57), `SE2` (57), `2D-KND90010` (49), `2D-MD25` (47), `A$C696F6E2C` (38), `2D-MD12.5` (36), `2D-EM1-122.512.5` (33), `2D-GA3` (33), `2D-VD20` (29), `2D-VAV25` (27), `2D-KND90001` (26), `A$C0C357809` (25), `ISETKP04-04` (24), `A$C328B29EB-` (21), `FCU-GT-TIP-06` (21), `ISETKP04-06` (21), `2D-UM1-122.512.5` (19), `2D-USWR1-800` (18), `!-YAZI-AS` (17), `2D-UA1-310` (16), `ISETKP04-03` (15), `FLX-Krc2.430` (15), `FLX-Krc2.431` (15), `0-KRCN-DSD-KASETTIPI1` (14), `ISETKP04-01` (12)
</details>


---
## 07_Vinc_Ana_Bina

Orijinal: `8d1b0d2d-07-Vin_-Ana_Bina.dwg` — 1072901 çizgi parçası, 14909 daire, 354 metin; 51 katman, 38 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | pafta | `onizleme/07_Vinc_Ana_Bina_01.png` | ZEMİN KAT PLANI (±0.00 = 978.90) ÖLÇEK 1/100; VİNÇ 1; TKGKV 0,5 TON; 2 ADET ÇKGKV 1,5 TON; VİNÇ 4 - 5; VİNÇ 2 - 3; Z-42; ELK. OD.; BAKIM ODASI; KAT HOLÜ |
| 2 | pafta | `onizleme/07_Vinc_Ana_Bina_02.png` | KESİT - 2 ÖLÇEK 1/200; KESİT - 3 ÖLÇEK 1/200; ZEMİN KAT (978.90); 1. KAT (985.90); ÇATI KATI (992.40); ÇATI (997.25); TEMEL ÜST; TEKER YÜKLERİ |
| 3 | serbest grup | `onizleme/07_Vinc_Ana_Bina_03.png` | — |
| 4 | serbest grup | `onizleme/07_Vinc_Ana_Bina_04.png` | — |
| 5 | serbest grup | `onizleme/07_Vinc_Ana_Bina_05.png` | (BEKET 105) |
| 6 | serbest grup | `onizleme/07_Vinc_Ana_Bina_06.png` | (BEKET 105) |
| 7 | serbest grup | `onizleme/07_Vinc_Ana_Bina_07.png` | — |
| 8 | serbest grup | `onizleme/07_Vinc_Ana_Bina_08.png` | KAT PLANI; VİNÇ TESİSATI; UYGULAMA PROJE TESLİMİ; OPAK BİNASI PROJE YAPIM İŞİ; ASELSAN AKYURT-1 YERLEŞKESİ; VİNÇ 4 - 5; ÇKGKV 1,5 TON; İNŞAAT ve EMLAK DİREKTÖRLÜĞÜ ONAYI; KULLANICI KOORDİNESİ / MUTABAKAT |
| 9 | serbest grup | `onizleme/07_Vinc_Ana_Bina_09.png` | (BEKET 105) |
| 10 | serbest grup | `onizleme/07_Vinc_Ana_Bina_10.png` | (BEKET 105) |
| 11 | serbest grup | `onizleme/07_Vinc_Ana_Bina_11.png` | (BEKET 105) |
| 12 | serbest grup | `onizleme/07_Vinc_Ana_Bina_12.png` | (BEKET 105) |

### Boru/kanal çapı yazım biçimi


Not/hesap metinleri: `hesap/07_Vinc_Ana_Bina_notlar.txt` (4 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `1` (359230), `vinç` (197880), `S-COLS-CONC` (42809), `-M-MAHAL-ETIKET-NOT` (7038), `AAA_EKSEN` (5768), `AAA_LEVHA` (4762), `BARIŞ BABUR DESIGN.9` (2852), `0` (1700), `AS_PRFL_DEMIR` (686), `_04 Carding Invisible` (496), `AS_GOR_UZAK2` (429), `AAA_GÖRÜNMEZ` (316), `-M-MAHAL-DEBILER` (276), `BARIŞ BABUR-0019` (240), `-M-MAHAL-ETK-` (207), `BARIŞ BABUR-23` (192), `-M-MAHAL-HAVA-DEGISIM` (138), `AS_TAVK_TASYUNU` (133), `AS_TAVK_METAL` (105), `AS_DUV_ALCIPAN_BEYAZ` (74), `-M-MAHAL-NO` (69), `-M-MAHAL-NOM` (69), `-M-MAHAL-ETIKET-NOTM` (69), `BARIŞ BABUR DESIGN.8` (60), `_09 Elektrik Room Sıde Gırder` (48), `EKSEN` (40), `AS_GOR_UZAK1` (37), `S-COLS-STEL` (36), `AS_TAVK_ALÇIPAN (BEYAZ)` (33), `AS_NOT_MIMARI` (18), `BARIŞ BABUR DESIGN.7` (16), `AS_YAZI_MAHAL_ADI` (16), `AS_DOSK_SAP` (14), `AS_AKS_TA_BETONARME` (14), `AS_AKS_BALON` (14), `AS_AKS_YAZI` (14), `AS_YAZI` (12), `S_KESİT GÖRÜNÜŞ` (12), `AS_TA_BETONARME` (11), `AS_DUV_GAZBETON` (10)

Bloklar (model uzayı INSERT sayısı): `tavan kutu profil 40x40x2` (232), `*U` (143), `M-MHLETK-YNG` (69), `metal panel 60x60 clip-in` (35), `omega profil clip-in` (30), `vida metal` (24), `axis baloon` (14), `tyrmnjytk` (12), `DTYJGKFGD` (4), `LKŞLKLŞLKŞLK` (4), `EAWREWFWEFWEGWR` (3), `DHSETSRDJFDS` (3), `supurgelik aluminyum h 10 cm` (3), `KLJLKHŞKLJKŞJHIUHYGFRTDTRFJKLK` (2), `LŞOLİPOUTEFSTZDFDRSYUYIUGKJGKL` (2), `hrgefgfhgjtyrt` (2), `fewgrfebrvdc` (2), `jyhtjyrhtergrtyrjntb` (2), `treefgrf` (2), `rtrtjhrkıtyurjtyrkurjt` (2), `fhgdfsdfhgjgfhgd` (2), `tdfsdyutydstmfktnfchjtdhasr` (2), `XREF` (1), `XDGJKDJJKUDJTKDDRTDFGXTRSTYK` (1), `TUYTRIODGÖKÇŞLLYIGSSZŞIG` (1), `FDJFGJDFJGDH` (1), `htbgrenbterew` (1), `dsdfdgfdfsd` (1), `htretretgewev` (1), `tgrfegrvcx` (1), `terttthergwe` (1), `trdnrtyrtbnyjerret` (1), `FTDYHRTTDYH` (1), `TDTRSEUTHSEJTDD` (1), `UYTDRSRKLTŞYP89UFKHTZ` (1), `eswaaaaaaaaafaergw` (1), `cam bolme duvar kesit` (1), `K` (1)
</details>


---
## 08_XREF_Mimari_Altlik_Ana_Bina

Orijinal: `b6a6df42-XREF.dwg` — 496788 çizgi parçası, 12884 daire, 10601 metin; 212 katman, 7 farklı blok (model uzayı).

### Paftalar / içerik grupları

| No | Tür | Önizleme | Başlıklar (büyük yazılar + anahtar kelimeler) |
|---|---|---|---|
| 1 | serbest grup | `onizleme/08_XREF_Mimari_Altlik_Ana_Bina_01.png` | A BLOK (EK); A BLOK; ASKİ KULLANIM SUYU; DIŞ BAĞLANTI ASKİ; OG HATTI; GALERI; Deplase Edilecek Yağmur Suyu Borusu Ø400; GİYİNME; zemin kat döşeme izdüşümü |
| 2 | serbest grup | `onizleme/08_XREF_Mimari_Altlik_Ana_Bina_02.png` | A BLOK (EK); A BLOK; 1. KAT PLANI (+7.00 = 985.90) ÖLÇEK 1/200; TEST ODASI; AZOT TANKI; 20 m³ AZOT TANKI; Altta Tünel Hizası; ŞK1 60x180cm |
| 3 | serbest grup | `onizleme/08_XREF_Mimari_Altlik_Ana_Bina_03.png` | Altta Galeri; Altta Tünel Hizası; ACIK OFIS B 56 KISI; ACIK OFIS A 48 KISI; KUVVET MERKEZI; BETON KAİDE; AZOT TANKI; Yakıt Tankı / 30.000 L |
| 4 | serbest grup | `onizleme/08_XREF_Mimari_Altlik_Ana_Bina_04.png` | sifonik yğm.szgc.; YM02; YM05; PÜK; AS03 YÜK ASANSÖRÜ Kabin: 265-270x330cm Kapasite: 5000-5050kg; VAR; VAR?YOK?; K-PIVOT-TEK-MM |

### Boru/kanal çapı yazım biçimi

- mm: 26 metin — ör. "VERTIV VRLA AKÜ KABİNİ 2000KVA", "VERTIV UPS 2000 kVA / kW A 570", "VERTIV UPS 2000 kVA / kW B 570"
- xx/yy (kanal ölçüsü): 2 metin — ör. "221/392", "89/198"
- Øxx: 1 metin — ör. "Deplase Edilecek Yağmur Suyu B"

Not/hesap metinleri: `hesap/08_XREF_Mimari_Altlik_Ana_Bina_notlar.txt` (6 tekil metin, 0 NOT bloğu).

<details><summary>Katmanlar (en çok kullanılan 40) ve bloklar (en çok kullanılan 40)</summary>

Katmanlar: `0-KRCN-AYDINLATMA-130426` (90244), `AS_TES_SUZGEC` (20174), `PN_Aluminyum` (19820), `AS_TEFR_CIHAZ` (13203), `---___EB_draft03_cihazlar` (10423), `0-KRCN-MİMARİ-220526` (8300), `G_0.09` (5514), `AS_PYZ_BINA` (5408), `AS_TEFR_MEK` (4926), `0-KRCN-ASMATAVAN-130426` (4823), `1轮廓线` (3606), `AS_DOS_TERAS_UST` (3061), `AS_PRFL_CELIK` (2432), `M_TFR_vitrifiye` (1661), `AS_MER` (1498), `AS_TEFR_MOB` (1405), `AS_DUV` (1322), `AS_KAPI_POZ` (1111), `SALT` (1104), `AS_PRFL_ALU` (893), `AS_DUVK_AHSAP` (851), `HH_DUVAR` (774), `AS_TA_BETONARME` (766), `TF_Mobilya` (689), `AS_DUV_ALCIPAN_YANGINA-SUYA DAYANIMLI` (599), `AS_MER_HIDDEN` (485), `2细实线` (483), `AS_DUV_GAZBETON` (389), `AS_PRFL_CELIK AKS` (380), `İNCE` (378), `AS_GOR_UZAK2` (374), `0-DCS-3000.01.00` (337), `D_Aluminyum` (320), `A8-MATERIAALIT` (308), `AS_PRFL_CAM` (296), `M_TFR` (288), `4中心线` (280), `AS_GOR` (225), `---___EB_draft00_parselsiniri` (218), `AS_TEFR_CIHAZ TURNIKE` (216)

Bloklar (model uzayı INSERT sayısı): `G$C5610E2D8` (1), `G$C4A951D59` (1), `G$C27E741DA` (1), `G$C546873DE` (1), `A$C6A10209E` (1), `A$C6A10300A` (1), `A$C6A10306C` (1)
</details>

