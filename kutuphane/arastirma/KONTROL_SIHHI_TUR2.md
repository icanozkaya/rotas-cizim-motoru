# KONTROL — SIHHİ TAM ŞERİT, TUR 2 (15.10.2026)

- Dosya: `proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf` (commit 48151d2): antet, yerleşim, temel, zemin/1./2. kat, çatı, kolon şeması + rögar + yağmur, WC havalandırma izometrisi + sıhhi detaylar.
- Kontrolör bağımsız çalıştı. Üretenin kodu (`motor/sihhi2/*.py`) ve açıklamaları okunmadı; yalnız DXF ölçüldü ve gözle incelendi.
- Ölçütler:
  - README (C), (B) ve 14.10 kuralları,
  - `onay_protokolu.md`,
  - `SIHHI_ALTIN_REFERANS.md`, `KOLON_SEMASI_TARZI.md`,
  - 4 RED görüntüsü,
  - kullanıcının kendi çizimi `new_block.dxf`.
- Araç: `motor/kontrolor/kontrolor.py --mimari ornekler/new_block.dxf.xz`. Ölçüm raporu ve kanıtları: `kontrol_png/sihhi_tur2/kontrolor_olcum_raporu.md` + `olcum_png/`.
- Yan yana PNG'ler `kutuphane/arastirma/kontrol_png/sihhi_tur2/` klasöründe. Her PNG'de solda kontrol edilen çizim, sağda kullanıcının new_block'u var; aynı model penceresi, siyah zemin, ezdxf. Önekler: `Z_`, `K1_`, `K2_` = kat planları; `S_` = şema; `P_` = paftalar.

## KARAR: **RED** (ONAY'a yakın; kısa düzeltme listesi)

Tur 1'e göre büyük ilerleme var:
- 9 kolon, kullanıcının çiziminde olduğu gibi aynı yerde ve aynı numarayla, üç katta sürekli.
- ÇM/BM mimarideki yerinde.
- Etiket üstüne binen etiket kalmadı.
- Aspiratörler penceresiz bütün ıslak hacimlerde var.
- Sıcak su daire içinde ve kombiden başlıyor.
- Balkon süzgeci yeşil hatla, 31 cm'den yağmur inişine bağlı.
- Şema ve rögar dağılımı kullanıcınınkiyle aynı. Pafta genişlikleri ve sırası aynı. Çatı planı ve iki şaftlı izometri var.

Kullanıcı şemaya, temele, çatıya ve detay paftasına bakınca "bu benim düzenim" der.

**Ancak iki engel var:**
1. Gerçek bir tesisat hatası var: 1. ve 2. katta D5/D8 lavabosunun pis su bağlantısı yok.
2. Kat planlarında yeni bir karmaşa kaynağı var: yağmur borusuyla aynı yeşilde, 1–1,5 m'lik çapraz kılavuz çizgileri. Bu çizgiler etiketleri oda dışına taşıyor ve odaları, kapıları kesiyor.
   - D3 duşta bir kılavuz çizgi balkondan duşa uzanıyor ve balkon süzgecinin hizasında bitiyor. Bu, RED-2 görüntüsüyle ("balkon süzgeci banyo kolonuna bağlı") aynı izlenimi veriyor. Otomatik araç da bunu T01 FAIL olarak yakaladı.
   - Kullanıcı planı kendi çizimiyle yan yana koyunca ıslak hacimlerde "bu yeşil çizgiler ne" diye sorar.

## Tur 1 maddelerinin durumu

### Plan (KONTROL_SIHHI_PLAN_TUR1)
| # | Madde | Durum | Kanıt |
|---|---|---|---|
| 1 | 1. kat D6'da P2/P3 yok, P10/P11 fazla | **KAPANDI**: T12 ✓ (9 kolon, her katta ± 5 cm, yeni numara yok); 1. katta P2/P3 kullanıcının yerinde | `K1_13`, `P_temel` |
| 2 | ÇM mimariden taşınmış | **KAPANDI**: T13 ✓; Ç.M. nişte | `Z_11`, `K1_11`, `K2_11` |
| 3 | P7 BM yerinde, BM oda ortasında | **KAPANDI**: P7 kullanıcının noktasında (253765, −441812), T13 ✓ | `Z_16` |
| 4 | Etiket üstüne etiket | **KAPANDI**: T07 etiket–etiket 0 (üç kat); gözle de görülmedi | `K2_13`, `Z_14` |
| 5 | Etiket duvar taraması, kapı yazısı veya armatür üstünde | **KAPANDI**: tarama 0, armatür/sembol 0, asansör 0. Etiketler bu kez uzun kılavuzla oda dışına taşınmış; bu, yeni madde **Y2** | `Z_13`, `Z_15` |
| 6 | Aspiratör notu yanlış yerde | **KISMEN**: merdivendeki not kalktı, T14 ✓. 1. kat D6 ve 2. kat D9 banyo notu yatak odasında, K2 kapısının üstünde; D2/D4/D7 banyo notu duvarın dışında. Yeni madde **Y3** | `K1_13`, `K2_13`, `Z_15` |
| 7 | Penceresiz banyoda havalandırma yok | **KAPANDI**: T15 ✓ | `Z_15` |
| 8 | Kolon ıslak hacim köşesinde değil | **KAPANDI**: P1…P9 kullanıcının koordinatlarında (fark < 1 cm). T10'un 16 FAIL'i aynı noktalarda veriliyor; araç sınırı | `Z_13`, `Z_14`, `P_temel` |
| 9 | D3 duş temiz suyu iki yatak odasından geçiyor | **KAPANDI**: çift holden gelip yalnız "oda"nın üst kenarından duşa giriyor | `Z_12`, `P_zemin_genel` |
| 10 | T04 sıcak su daire dışında; "C.M." yazısı yok | **KAPANDI**: T04 ✓ (üç kat); "Ç.M." yazısı var | ölçüm raporu |

### Şema ve şerit (KONTROL_SIHHI_SEMA_TUR1)
| # | Madde | Durum | Kanıt |
|---|---|---|---|
| 1 | Fazladan kolon/rögar | **KAPANDI**: 9 kolon, R1–R4 + PB. Dağılım kullanıcınınkiyle aynı (R3 ← P2,P3,P5,P6; R4 ← P1,P4 …). Temel kolon yerleri aynı | `S_rogar`, `P_temel` |
| 2 | Pafta boyu ve sırası | **KAPANDI**: T17 ✓, şema 7418 | ölçüm raporu |
| 3 | Çatı planı yok | **KAPANDI**: P1…P9, YB1…YB9, 3 çatı tipi fan | `P_cati` |
| 4 | Armatür sırası | **KAPANDI**: banyo lavabo–klozet–süzgeç–duş–ÇM; mutfak BM–eviye–kombi | `S_armatur_D1_banyo`, `S_D1_zemin` |
| 5 | Duş sembolü hatta biniyor | **KAPANDI** | `S_armatur_D1_banyo` |
| 6 | ACI 250 yazılar | **KAPANDI**: T16 ✓; hesap kutusu okunuyor | `S_yagmur` |
| 7 | Kural metni sızıntısı / şemada lejant | **KAPANDI**: T16 ✓; şemada lejant yok | `S_genel` |
| 8 | Bant çizgileri yağmur bölmesinde yok | **KAPANDI** | `S_yagmur` |
| 9 | İzometride 4 şaft | **KAPANDI**: 2 şaft (D3-5-8 240 m³/h; D1-2-4-6-7-9 480 m³/h) | `P_detay` |
| 10 | Temel etiket boyu | **KAPANDI**: h 20 | `P_temel` |
| 11 | Akış okları, depo flanşı/flatör | **KISMEN**: flatör ve şebeke oku var; depo doldurma ve dağıtım düşeylerinde ↑/↓ okları yok. Yeni madde **Y5** | `S_depo`, `S_sebeke_sayac` |
| 12 | Sembol dolguları, D balonu, kolon–balon kopukluğu | **KAPANDI** | `S_kolon_ust`, `S_kolon_dibi` |
| 13 | PVC muf, iniş etiketi | **KAPANDI** | `S_kolon_dibi` |
| 14 | T04 | **KAPANDI** | — |
| 15 | Şema başlığı (bilgi) | **KAPANDI**: başlık yok, kullanıcıdaki gibi | `S_genel` |

## Otomatik ölçüm özeti (kontrolor.py, 15.10.2026)
| Test | Sonuç | Kontrolör yorumu |
|---|---|---|
| T01 ✗ 6 | Balkon süzgeci → pis su (Z/1/2 D3-5-8 duş balkonu) | **Geometride bağlantı yok.** Süzgeç (252746, −441887) → YB8 (252744, −441856) arasında 31 cm yeşil `ROTAS-SIHHI-YAGMUR` hattı var; pis suyla ortak düğüm yok. P9 kolonu (252778, −441881) süzgece 32 cm uzakta; kullanıcıda da aynı yerde. "Balkon içinde pis su" bulgusu, duş poligonunun bozuk algılanmasından geliyor (T15: duş 0,34 m², gerçekte 1,48 m²). Araç sınırı. **Ancak** görsel sinyal gerçek: madde **Y2a** |
| T02 ✗ 18 | Branşman > 300 cm, mahal dışından dolaşma | Kullanıcının çizimi aynı ölçümde 59 FAIL veriyor (wc-duş → banyo → P3 yolu kullanıcıda da var), tarz olarak sayılmadı. **İstisna:** 1. ve 2. katta "LV (wc-banyo) hatta bağlı değil" bulgusu GERÇEK, madde **Y1** |
| T03 ✗ 4 | Banyo içinde 105–143 cm iç bölge | Kullanıcının omurgası da banyoyu çaprazlıyor (21 BİLGİ). Gözle karışık görünmüyor; BİLGİ |
| T07 ✗ 66 | Etiket ↔ mimari yazı 18–23 / kat; etiket ↔ hat 7 | Kullanıcının çiziminde aynı ölçüm 80 + 128 veriyor; MTEXT kutusu sütun genişliğiyle ölçülüyor (bilinen sınır). Gözle doğrulanan yalnız biri var: Z D1 banyo aspiratör notunu temiz su düşeyi kesiyor, madde **Y3** |
| T10 ✗ 16 | Kolon köşede değil | Kolonlar kullanıcının koordinatlarında; araç sınırı |
| T11 ✗ 1 | Yazı çakışması 60 | T07 ile aynı kaynak |
| T04, T05, T08, T09, T12–T17 | ✓ | — |

## YENİ / AÇIK MADDELER (üreten ajana)

**Y1 — [1. kat D5, 2. kat D8, wc-banyo] Lavabonun pis su bağlantısı yok.** Engel.
- Konum: lavabo (255186, −442031) ve (257235, −442031). Zemin katta D3 (253152, −442031) bağlı.
- K1/K2'de omurga P8'den süzgece ve klozete gidiyor; tezgâhtaki lavaboya hiç hat gitmiyor. Üstüne yalnız soğuk ve sıcak su geliyor.
- Kullanıcıda: P8 omurgası lavaboya kadar uzanıyor (`Ø50 / 2 SB`).
- Düzeltme: zemin kattaki gibi lavabo → omurga branşmanı (45° + dik). Yük toplamları güncellenmeli; şema bloğu D5/D8 zaten lavabolu.
- PNG: `K1_11_wcbanyo_D3_P8.png`, `K2_11_wcbanyo_D3_P8.png`, `olcum_png/T02_1_03.png`, `T02_2_02.png`.

**Y2 — [Bütün katlar, ıslak hacimler] Uzun yeşil kılavuz çizgileri. Karmaşa kaynağı.**
- Ölçüm: `ROTAS-SEMBOL-KILAVUZ` katmanının rengi ACI 3 ve çizgisi sürekli. Bu, `ROTAS-SIHHI-YAGMUR` ile aynı görünüm.
- Kat başına 51–54 kılavuz var, 8'i 1 m'den uzun (en uzun 147 cm).
- Kullanıcıda kılavuz yalnız kolon balonlarında var (49–101 cm). Boru etiketleri hattın üstünde, kancalı: Ø/SB hat yönünde, inç/MB yatay. §3.3 ve §4.1.

**a)** D3/D5/D8 duşu: `Ø50 / 2 SB` etiketi balkonda.
- Kılavuz (252854, −441956) → (252746, −441956) balkon süzgecinin x hizasında bitiyor; süzgeç duşa bağlıymış gibi okunuyor. Bu, RED-2 görüntüsü.
- Aynı odada `Ø70 / 11 SB` dışarıda; P9 balonunun kılavuzu (252780, −441897) → (252796, −442017) 121 cm ve duşu boydan boya kesiyor.
- PNG: `Z_12`, `K1_12`, `K2_12`, `olcum_png/T01_Z_01.png`.

**b)** Z D1 banyo ve wc-lvb (253590…253980, −442880…−442370):
- `1" 5.25 MB / 1" 3.25 MB` yatak odasında; kılavuz ~2 m, K3 kapısını kesiyor.
- `Ø100 / 10 SB`, `1" 3 MB / 1" 4 MB` antrede; kılavuzlar wc-lvb'yi çapraz kesiyor.
- PNG: `Z_13`, `Z_31`.

**c)** Z D2 banyo ve wc-lvb (253170…253560):
- Üstten inen 3 m'lik kılavuz (~253260, −442400 yukarısı).
- wc-lvb içinde birbirini kesen iki kılavuz.
- PNG: `Z_15`.

**d)** wc+banyo D3/D5/D8:
- `Ø100 / 12 SB` (K2) odanın solunda; 1,4 m'lik kılavuz aspiratör sembolünün ve ÇM'nin üstünden geçiyor.
- `1" / 3.25 MB` K3 kapısının üstünden kılavuzlu.
- PNG: `K2_11`, `K1_11`.

**e)** 2. kat D9 banyo:
- İki `Ø50 / 2 SB` odanın ortasında, kılavuzları çapraz.
- PNG: `K2_13`.

**Düzeltme:**
- Etiketi hattın üzerine koy (parça ortası, mesafe 0). Ø/SB hat yönünde, inç/MB yatay, kullanıcının kancasıyla.
- Kılavuzu yalnız gerçekten sığmayan dar hacimde kullan: ≤ 60 cm, hiçbir boru, kapı veya oda çaprazından geçmeyen. Rengi yağmurla karışmasın: etiketin rengi (211/101) ya da ince gri.
- Kolon balonu kılavuzu kullanıcı ofsetinde olsun (49–101 cm). P9 balonu kullanıcıdaki gibi duşun üstünde/dışında, kılavuz duşu kesmeden.

**Y3 — [Aspiratör notları] Islak hacmin dışında ya da hatla kesişiyor.**
- 1. kat D6 banyo notu yaklaşık (255930…256014, −442510…−442570); 2. kat D9 aynı yerde +2048. Not yatak odasında, K2 kapı sembolünün üstünde.
- D2/D4/D7 banyo notu yaklaşık (253170…253240, −442520…−442570), sol duvarın dışında.
- Z D1 banyoda (253796–253801, −442645…−442695) temiz su düşeyi "Wc Aspiratörü / 160 m3/h / Ø150 mm" yazısının içinden geçiyor.
- Kullanıcıda not banyonun içinde, boş alanda, hatsız (§7).
- Ayrıca plan notlarının debisi tutarsız: D3/D5/D8 ve D6 notu "80 m3/h", D1/D2 notu "160 m3/h". Kullanıcının planında hepsi "160 m3/h" (ALTIN §7), izometride kat başına 80. Kullanıcının biçimine uyulsun ya da ona sorulsun.
- PNG: `K1_13`, `K2_13`, `Z_15`, `Z_13`.

**Y4 — [Temiz su etiketleri] Islak hacim girişi etiketi hattın üstünde değil, oda dışında.** (Y2 ile aynı düzeltme.)
- Kullanıcıda her ıslak hacme giren çiftin etiketi girişte, hattın üstünde, kanca 31 + 8,3 (`Z_13` sağ, `Z_15` sağ).

**Y5 — [Şema, depo/şebeke] Düşey dağıtımda akış okları yok.** (küçük)
- Kullanıcıda şebeke girişinde → var; depo doldurma düşeyinde ↑, dağıtım düşeyinde ↓ var (§5.4).
- Bizde yalnız şebeke oku var.
- PNG: `S_sebeke_sayac`, `S_depo`.

## Değiştirilmeyecekler (doğru bulundu)
- Kolon yerleri ve numaraları, rögar dağılımı, temel planı.
- Sayaç grubu: zemin bandının solunda 5 + 4 = 9; kat bantlarında sayaç yok.
- Depo sol üstte, flatörlü.
- Daire blokları ve armatür sırası. Kombi ve D balonu. T.K. → dirsek → R.
- Yağmur şeması ve hesap kutusu.
- Çatı planı. İki şaftlı izometri. SIHHİ DETAYLAR.
- Antet ve yerleşim. Pafta genişlikleri.
- Plan: sıcak su kombiden ve daire içinde; soğukla 5 cm paralel; köprü yok; ÇM/BM mimaride gösterilen yerde.
- Mutfaklar (`Z_14`) ve daire girişleri okunaklı; bu bölgelerde kullanıcı çizimine yakın.

## Araç notu (kontrolör geliştirme)
- T01: "bağlı ağ" toleransı. Süzgeç ile kolon arasında 32 cm olduğu hâlde bağlı sayıyor. Duş poligonunun 0,34 m² algılanması ise "balkon içinde pis su" yanlış pozitifini üretiyor.
- T10: kullanıcının koordinatlarındaki kolonları da FAIL sayıyor. Referans karşılaştırması `_cizim` kolon konumlarıyla yapılmalı.
- Ölçülmeyen ama bu turda belirleyici olan bir durum var: kılavuz uzunluğu/rengi, ve bir kılavuzun boru ya da kapıyla kesişmesi. Bunun için yeni bir test (T18) önerilir.
