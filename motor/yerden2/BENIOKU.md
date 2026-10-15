# yerden2 — yerden ısıtma kat planları + kolon şeması (new_block)

```
python3 motor/yerden2/yerden.py [--png] [--cep] [--ayaklar] [--yenile]
python3 motor/yerden2/yi_kirp.py            # kontrolör tarzı yan yana kırpımlar (motor | kullanıcı) -> onizleme/kirp/
python3 motor/yerden2/yi_onizleme.py        # yalnız önizleme (DXF üretilmişse)
python3 motor/deneme/denetim/denetle.py proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf
python3 motor/yerden2/yi_bloklar.py --cikar     # kullanıcının bloklarından ROTAS-YI- kütüphanesini yeniden üret
python3 motor/yerden2/yi_blok_karsilastir.py    # blok başına kullanıcı | bizim yan yana + piksel F1
python3 motor/yerden2/yi_kirp_kollektor.py      # her daire kollektör+ayak, şema kombi/kollektör/panel kırpımları
```
| Seçenek | Ne yapar |
|---|---|
| `--png` | `proje/denemeler/yerden2/onizleme/` içine kat planı, şema ve referansla yan yana PNG'ler |
| `--cep` | (eski, tur 1) devre etiketi için serpantinde cep bırakır. **Varsayılan (tur 2): etiket serpantinin üstünde, altı WIPEOUT maskeli** (kullanıcının çizimi gibi) |
| `--ayaklar` | (eski seçenek, etkisiz) 15.10 (D) itibarıyla planda kollektör + kombi + ayaklar HER ZAMAN çizilir (`ayak.py`) |
| `--yenile` | Mimari tanıma önbelleğini (`/tmp/claude-0/y2/onbellek`) yeniden kurar |

Çıktılar `proje/denemeler/yerden2/` içinde: `NB_YERDEN_ISITMA.dxf` (AC1032, cm; 3 kat planı kaynak koordinatında, kolon
şeması x 258 850'de), `NB_YERDEN_ISITMA.xlsx`, `NB_YERDEN_ISITMA_model.json`, `KONTROL.json` (tüm kontroller, yoğunluk
tablosu, MMO yüzey sıcaklıkları). Bir koşu ≈ 30 s, `--png` ile ≈ 70 s, `yi_kirp.py` ≈ 75 s.

## Modüller
| Dosya | Görev |
|---|---|
| `ayak.py` | **15.10 (D)** planda kollektör dolabı, kombi–kollektör gidiş/dönüş hattı, her devrenin gidiş/dönüş ayakları (aşağıda) |
| `mimari_yi.py` | Mahal tanıma (`sihhi2/mimari2.Kat`), ısıtılan mahal ve sıcaklık, yüklük bölme, kapılar, tefriş engelleri, ısıtma bölgesi. Kapı kanadına değen kısa çizgiler ve kapı etiket dairesi (K2, r≈8) kapı parçasıdır; süpürme alanı engel değildir. Islak hacimde duş teknesi/küvet, lavabo, Ç.M. gövdesi hariç tutulur; klozetin önü (çanak) hariç tutulmaz, yalnız duvar tarafındaki 12 cm arka şerit boş (tur 4). Lavabo, içinde batarya daireleri olan küçük kutudan tanınır |
| `serpantin.py` | Meander. `kur()` satır fazını (0–12,5 cm) ve uç tarafında atlanan satır sayısını (0–6) tarayıp en çok boru veren düzeni seçer. `kur_merdiven()` tek devreli mahallerde **basamaklı besleme** kurar: besleme hattı her satır grubunda sol sınıra yaslanır, gruplar arasında kısa yatay bir basamakla kayar (klozet/lavabo yanı, L hol, kapı girintisi) |
| `tasarim.py` | Köşe seçimi (kapıya en yakın köşe; kaplama en iyinin %97'sinden azsa daha iyi kaplayan köşe), devre sayısı, bant bölmesi. Tek devrede normal ve basamaklı düzenden uzun olanı alır |
| `yerden.py` | Ana akış, numaralama, etiket yerleşimi, DXF |
| `yi_sema.py` | Kolon şeması (saf geometri), gerçek kollektör çizimi |
| `excel_yi.py` | Excel (şablon formülleri korunur) |
| `yi_kontrol.py` | Kontroller, yoğunluk tablosu, `denetle.py` |
| `yi_onizleme.py`, `yi_kirp.py` | PNG önizlemeler, kontrolör tarzı yan yana kırpımlar |

## Uygulanan kurallar (tur 2)
- **Serpantin:** Her devre tek açık LWPOLYLINE (`ROTAS-ISITMA-PEX`). Parmaklar X eksenine paralel, aralık 15. U dönüşü r 7 + 1 + r 7 (bulge 0,4142). İki uç aynı köşede, 15 cm arayla. Kenar payı 7,5. Etiket için cep yok, mahal tam doldurulur.
- **Devre bölme:** 14 m² ve üstü mahal en az 2 devre. Hedef ≤ 70 m, kesin sınır ≤ 80 m (bu koşuda en uzun 65,76 m). 3 m'den kısa devre yok.
- **Isıtılan:** oda, salon, mutfak 20 °C; antre-koridor 15 °C; banyo ve wc-banyo 24 °C.
- **Isıtılmayan:** balkon, yüklük, merdiven, asansör, ortak alan. Adında "banyo" geçmeyen ve 2,7 m² ya da daha küçük ıslak hacimler de ısıtılmaz (wc-lavabo, duş, 1. kat D6 wc-duş 2,65 m²). Kullanıcı da bu katta yalnız yanındaki banyoyu ısıtmış ve ona 121 numarasını vermiş.
- **Devre etiketi** (`ROTAS-YI-ETIKET`, 150×80, W = 35 W/m × L): Yalnız kendi mahalinin içinde, serpantinin üstünde, altı WIPEOUT. Kılavuz çizgisi yok. Yer arama sırası:
  1. Serbest zemin (vitrifiye ve mimari çizgi dışı)
  2. Mimari çizgi üstü
  3. Mahal içinde her yer
  4. Sığmazsa ölçek sırasıyla: 0,85 / 0,75 → 90° (hol boyunca) → 0,7 / 0,65. Bu koşuda 90° hiç kullanılmadı, küçük ölçek kat başına 3 etikette var (2 hol, 1 wc-banyo).

  Küçük mahalde önce mahal etiketi, sonra devre etiketi yerleşir; sığmazsa sıra tersine çevrilir.
- **Mahal etiketi** (`ROTAS-YI-MAHAL`): Mahal içinde durur. Vitrifiye, duş teknesi, küvet, duvar ve yazı üstüne binmez. Gerekirse 0,8 ölçeğe iner, boru üstündeyse maskelenir.
- **Şema:** Pafta 6692 × 2900, bant içi 6490 (kullanıcının şemasında 6693 / 6490). Daire genişliği 290 + 200·(n−1) + 254.
  - **Kollektör** gerçek çizimle gösterilir: dolap ve kaide, gidiş/dönüş barı, ağız başına gidişte ayar vanası + rekor ve dönüşte debimetre + rekor, uç braketleri, sol uçlarda kelebek kollu küresel vana + rakor, hava pürjörleri. Ağız adımı 10, gidiş–dönüş kaydırması 5.
  - **Kombi bağlantısı** kullanıcının bloğundaki gibi: Gidiş kombinin sağından iner ve üst bara girer. Dönüş soldan iner, alt bara girer ve aşağıda küresel vanaya devam eder. Vana yalnız dönüşte.
  - Bantların üstü boş bırakılır. Başlık, lejant ve notlar bantların altındaki şeritte.
- **Isıl güç esası (R6):** Plan etiketi, şema ve Excel aynı esası kullanır: **35 W/m × L**. Excel'de bu PETEK LİST D/E/F, YERDEN ISITMA D/M/N ve MMO qh sütunlarına yazılır. Esas, teknik raporun 1.3 bölümünde belirtilir. Şablonda başka projeye ait U değerleri vardı, kaldırıldı.
- **MMO yüzey sıcaklığı:** Ty = Ti + (q"/8,92)^0,91. 35 W/m × L ve 15 cm aralıkta q" ≈ 160–220 W/m², Ty 30–40 °C çıkıyor. **81 devrenin tamamı sınırı aşıyor** (oturma 29 °C, banyo 33 °C).
  - Sınırda kalmak için q" ≤ 100 W/m² olmalı. 35 W/m ile bu yaklaşık 35 cm boru aralığı demek.
  - Bu aralık, R1 yoğunluk şartıyla (≥ 6 m/m²) ve kullanıcının 15 cm seçimiyle çelişiyor. Bu yüzden aralık değiştirilmedi.
  - MMO sayfalarında sınırı aşan hücreler kırmızı, altta UYARI satırı var.
  - Karar kullanıcıda: ısı kaybı hesabıyla qh girilmeli ya da W esası değişmeli.
- **Excel:**
  - Dış bağlantı (`…/dcm/PROJE/MEKANİK HESAPLAR KOMBİ.xls`) paketten silindi, "dcm" izi kalmadı.
  - Yazdırma alanları: kapak A1:I42, TEKNİK RAPOR A1:H40; ikisi de A4 dikey, sayfaya sığdır.
  - LibreOffice ile yeniden hesap: 1981 formül, hata 0.

## Boru yoğunluğu (son koşu)
- **m/m² mimari:** boru boyu / mimarın m² yazısı (kontrolörün ölçüsü)
- **m/m² net:** boru boyu / ısıtma alanı (mahal − tefriş/vitrifiye)

| Zon | Daire | Mahal | m² mimari | m² net | L (m) | Devreler | m/m² mimari | m/m² net |
|---|---|---|---|---|---|---|---|---|
| Z01 | D1 | mutfak | 11.07 | 7.83 | 48.24 | 48.24 | 4.36 | 6.16 |
| Z02 | D1 | yatak od. | 14.25 | 13.60 | 82.06 | 42.89 + 39.17 | 5.76 | 6.04 |
| Z03 | D1 | yatak od. | 9.31 | 8.78 | 52.88 | 52.88 | 5.68 | 6.03 |
| Z04 | D1 | yatak od. | 9.31 | 8.84 | 53.32 | 53.32 | 5.73 | 6.03 |
| Z05 | D1 | salon | 21.18 | 20.10 | 121.17 | 59.14 + 62.03 | 5.72 | 6.03 |
| Z06 | D1 | antre-kor. | 7.77 | 7.61 | 43.50 | 43.50 | 5.60 | 5.72 |
| Z07 | D1 | banyo | 5.36 | 3.38 | 17.03 | 17.03 | 3.18 | 5.04 |
| Z08 | D2 | mutfak | 11.07 | 7.87 | 48.40 | 48.40 | 4.37 | 6.15 |
| Z09 | D2 | yatak od. | 14.25 | 13.84 | 81.29 | 41.72 + 39.57 | 5.70 | 5.87 |
| Z10 | D2 | yatak od. | 9.31 | 8.76 | 52.88 | 52.88 | 5.68 | 6.04 |
| Z11 | D2 | yatak od. | 9.31 | 8.83 | 53.16 | 53.16 | 5.71 | 6.02 |
| Z12 | D2 | salon | 21.18 | 20.17 | 121.53 | 59.50 + 62.03 | 5.74 | 6.03 |
| Z13 | D2 | antre-kor. | 7.77 | 7.67 | 43.80 | 43.80 | 5.64 | 5.71 |
| Z14 | D2 | banyo | 5.36 | 3.29 | 16.03 | 16.03 | 2.99 | 4.88 |
| Z15 | D3 | mutfak | 10.11 | 7.23 | 39.16 | 39.16 | 3.87 | 5.41 |
| Z16 | D3 | yatak od. | 15.44 | 14.32 | 86.62 | 43.80 + 42.82 | 5.61 | 6.05 |
| Z17 | D3 | yatak od. | 9.05 | 8.64 | 53.12 | 53.12 | 5.87 | 6.15 |
| Z18 | D3 | salon | 22.31 | 20.95 | 126.78 | 65.76 + 61.02 | 5.68 | 6.05 |
| Z19 | D3 | oda | 7.75 | 7.31 | 46.26 | 46.26 | 5.97 | 6.33 |
| Z20 | D3 | antre-kor. | 11.00 | 10.28 | 57.11 | 57.11 | 5.19 | 5.56 |
| Z21 | D3 | wc+banyo | 4.37 | 2.36 | 11.99 | 11.99 | 2.74 | 5.08 |
| 101 | D4 | mutfak | 11.07 | 7.87 | 48.44 | 48.44 | 4.38 | 6.15 |
| 102 | D4 | yatak od. | 14.25 | 15.15 | 87.70 | 41.72 + 45.98 | 6.15 | 5.79 |
| 103 | D4 | yatak od. | 9.31 | 8.78 | 52.88 | 52.88 | 5.68 | 6.02 |
| 104 | D4 | yatak od. | 9.31 | 8.83 | 53.16 | 53.16 | 5.71 | 6.02 |
| 105 | D4 | salon | 21.18 | 20.13 | 121.02 | 59.10 + 61.92 | 5.71 | 6.01 |
| 106 | D4 | antre-kor. | 7.77 | 7.66 | 43.80 | 43.80 | 5.64 | 5.72 |
| 107 | D4 | banyo | 5.04 | 3.28 | 16.02 | 16.02 | 3.18 | 4.88 |
| 108 | D5 | mutfak | 10.11 | 7.11 | 38.32 | 38.32 | 3.79 | 5.39 |
| 109 | D5 | yatak od. | 15.44 | 14.31 | 86.62 | 43.80 + 42.82 | 5.61 | 6.05 |
| 110 | D5 | yatak od. | 9.05 | 8.64 | 53.12 | 53.12 | 5.87 | 6.15 |
| 111 | D5 | salon | 22.31 | 20.93 | 122.85 | 60.92 + 61.93 | 5.51 | 5.87 |
| 112 | D5 | oda | 7.75 | 7.29 | 46.14 | 46.14 | 5.95 | 6.33 |
| 113 | D5 | antre-kor. | 11.00 | 10.30 | 57.29 | 57.29 | 5.21 | 5.56 |
| 114 | D5 | wc-banyo | 4.37 | 2.36 | 11.99 | 11.99 | 2.74 | 5.08 |
| 115 | D6 | mutfak | 11.07 | 7.83 | 48.24 | 48.24 | 4.36 | 6.16 |
| 116 | D6 | yatak od. | 14.25 | 13.62 | 82.22 | 43.01 + 39.21 | 5.77 | 6.03 |
| 117 | D6 | yatak od. | 9.31 | 8.80 | 53.04 | 53.04 | 5.70 | 6.03 |
| 118 | D6 | yatak od. | 9.31 | 8.88 | 53.51 | 53.51 | 5.75 | 6.02 |
| 119 | D6 | salon | 21.18 | 20.14 | 121.33 | 59.22 + 62.11 | 5.73 | 6.03 |
| 120 | D6 | antre-kor. | 7.77 | 7.61 | 43.50 | 43.50 | 5.60 | 5.72 |
| 121 | D6 | banyo | 4.37 | 2.61 | 12.17 | 12.17 | 2.78 | 4.66 |
| 201 | D7 | mutfak | 11.07 | 7.57 | 45.65 | 45.65 | 4.12 | 6.03 |
| 202 | D7 | yatak od. | 14.25 | 15.15 | 87.35 | 41.48 + 45.87 | 6.13 | 5.76 |
| 203 | D7 | yatak od. | 9.31 | 8.76 | 52.80 | 52.80 | 5.67 | 6.03 |
| 204 | D7 | yatak od. | 9.31 | 8.83 | 53.12 | 53.12 | 5.71 | 6.02 |
| 205 | D7 | salon | 21.18 | 20.03 | 120.38 | 58.58 + 61.80 | 5.68 | 6.01 |
| 206 | D7 | antre-kor. | 7.77 | 7.64 | 43.61 | 43.61 | 5.61 | 5.71 |
| 207 | D7 | banyo | 5.04 | 3.33 | 17.75 | 17.75 | 3.52 | 5.32 |
| 208 | D8 | mutfak | 10.11 | 6.92 | 36.81 | 36.81 | 3.64 | 5.32 |
| 209 | D8 | yatak od. | 15.44 | 14.21 | 83.92 | 41.53 + 42.39 | 5.44 | 5.91 |
| 210 | D8 | yatak od. | 9.05 | 8.66 | 53.12 | 53.12 | 5.87 | 6.14 |
| 211 | D8 | salon | 22.31 | 20.82 | 122.53 | 60.72 + 61.81 | 5.49 | 5.88 |
| 212 | D8 | oda | 7.75 | 7.28 | 46.02 | 46.02 | 5.94 | 6.32 |
| 213 | D8 | antre-kor. | 11.00 | 10.51 | 57.31 | 57.31 | 5.21 | 5.45 |
| 214 | D8 | wc-banyo | 4.37 | 2.33 | 12.01 | 12.01 | 2.75 | 5.14 |
| 215 | D9 | mutfak | 11.07 | 7.80 | 47.99 | 47.99 | 4.34 | 6.15 |
| 216 | D9 | yatak od. | 14.25 | 13.58 | 81.84 | 42.80 + 39.04 | 5.74 | 6.03 |
| 217 | D9 | yatak od. | 9.31 | 8.77 | 52.80 | 52.80 | 5.67 | 6.02 |
| 218 | D9 | yatak od. | 9.31 | 8.85 | 53.28 | 53.28 | 5.72 | 6.02 |
| 219 | D9 | salon | 21.18 | 19.98 | 119.90 | 58.10 + 61.80 | 5.66 | 6.00 |
| 220 | D9 | antre-kor. | 7.77 | 8.07 | 44.15 | 44.15 | 5.68 | 5.47 |
| 221 | D9 | banyo | 5.04 | 3.35 | 17.93 | 17.93 | 3.56 | 5.35 |

Notlar:
- 100 cm'lik koridorda 7,5 cm kenar payı ve 15 cm aralıkla ulaşılabilecek en yüksek yoğunluk yaklaşık 5,7–6,0 m/m² (parmak boyu 85 cm).
- Banyolarda klozet, lavabo ve duş teknesi hariç tutulduğu için boru kullanıcınınkinden kısa. Kullanıcı boruyu klozet ve lavabonun altından geçiriyor (banyo 23,53 m).

## Tur 3 değişiklikleri (kontrolör tur 2 RED: Y-1..Y-4)
- **Y-1 yüklük:** `mimari_yi._yari_duzlem_parca` — yatak odası poligonu içindeki yüklük etiketinin çevresinde x/y kesitleri
  taranır (kesit ≤ 140 cm, parça 0,6–3,5 m², oda etiketini içermez) → en büyük parça yüklüğe verilir. Üç katta da
  yüklük 1,79–1,85 m² ayrılıyor; yüklükte boru 0 (Y01). Eski morfolojik açma yalnız yedek.
- **Y-2 ıslak hacim:** Ç.M. kutusu (fx `CM` ya da 40–85 cm kapalı kare kutu) engel; vitrifiye payı 3 cm daraltıldı
  (`ISLAK_PAY_AZALT`); ıslak hacimde köşe = en çok mahal içi boru; `yerden.islak_doldur` eşik (3,0 m/m² × mimari m² +
  0,8 m) tutmazsa duvar payı 6 / 5 cm denenir. Klozet, lavabo, duş teknesi/küvet ve Ç.M. altı boş.
  4,37 m² wc+banyolarda (Z21, 114, 214) eşik geometrik olarak tutmuyor: kontrolörün mahal poligonu 2,44–2,57 m²,
  klozet/duş/Ç.M. çıkınca 2,3–2,4 m² serbest zemin; 5 cm payla 15 cm aralıklı satırların toplamı en çok 12,6–13,2 m
  (besleme kolonu düşülmeden). Ulaşılan 9,8–10,0 m.
- **Y-3:** iki devreli mahalde devre etiketi yalnız kendi parmaklarının y bandında aranır; ikinci etiket ilkinin x'ine çekilir.
- **Y-4:** etiket önce hiçbir mimari çizgiye değmeyen serbest zeminde (1,0 → 0,9 → 0,85); olmazsa tam boy çizgi üstü,
  maske = kutu − (çizgiler + 3 cm) − vitrifiye alanı (`maske_ciz`, deliksiz parçalara bölünür). Maskelerin örttüğü
  mimari çizgi: 0 cm. İki yerleşim sırası denenir, en küçük ölçeği en büyük olan seçilir.
- **K-1:** esas değişmedi; TEKNİK RAPOR 1.4'te negatif MODÜL / m² hücrelerinin nedeni yazılı.

## Tur 4 değişiklikleri (kontrolör tur 3 RED: Y-2', E-1)
- **Y-2' klozet önü borulu (kullanıcının çizimi):** `mimari_yi.klozet_onleri()` ıslak hacimde klozet kutusundan (+6 cm)
  duvar tarafındaki `KLOZET_ARKA` = 12 cm şeridi dışındaki kısmı engelden çıkarır; ilmek dönüşleri çanağın içinde
  (kullanıcı: dönüş ekseni duvardan ≈ 17 cm). Lavabo, duş teknesi/küvet, Ç.M. gövdesi ve mek. havl. altı boş.
- **Klozet çentiği:** mahal tanıma klozet rezervuarı ile duş teknesi arasındaki 35 cm aralıklı paralel çizgileri duvar
  sanıp poligondan 24×70 cm çentik çıkarıyordu; `islak_genislet()` klozet çevresindeki (≥ 15 cm genişlikte) çentikleri
  mahale geri katar (kontrolörün mahal poligonu da bu zemini içeriyor).
- **Ç.M. ön panel şeridi:** `cm_on_seridi()` Ç.M. kutusunun mahale bakan kenarındaki 3–8 cm'lik iç çizgiyle ayrılmış
  şeridi engelden çıkarır (gövde çizgisinden 1,5 cm pay). Kullanıcının alt sırası da bu şeritten geçiyor (y −167,8,
  gövde −169).
- **Islak hacim payları:** kenar payı 7,5 → 6 / 5 / 4 / 3 / 2,5 cm denenir (kullanıcı banyoda 2,4–3,6 cm); `bolge()`
  duvar sınırı `min(4, kenar)`; ıslak hacimde satır fazı 0,5 cm adımla taranır (`serpantin.FAZ_ADIM`).
- **Sonuç (Y02, kontrolör poligonu):** Z21 13,27 m, 114 13,28 m, 214 13,14 m (eşik 13,11 m = 3,0 × 4,37). Klozet dış
  çizgisi içinde 1,27 m (kullanıcı 1,27 m); lavabo, duş teknesi, Ç.M. gövdesi içinde 0.
- **E-1 devre etiketi:** ıslak hacimde tam boy etiket vitrifiye / Ç.M. / duş teknesi üstüne binebilir (kesik maske,
  mimari çizgiler görünür; maske mimari yazıyı örtmez). Önce tablonun tamamı mimari yazıdan (mahal adı, m², mek. havl.)
  ayrı yer aranır; yoksa yalnız değer sütunu (ATTRIB) mimari yazıya değmez. **Z21 / 114 / 214 artık ×1,0 (h 10)**:
  eski ×0,7'nin nedeni denetle.py'nin (`yazi_poligonu`, ezdxf make_primitive) komşu asansör boşluğundaki
  "asansör boşluğu" MTEXT'ini sütun genişliğiyle 237,6 cm ölçmesiydi (kutu wc+banyonun içine 64 cm giriyordu). Ölçü
  artık `motor/kontrolor/kutu.py` `mtext_olcu` (satır satır gerçek genişlik, 97,5 cm) — denetle.py, kontrolör ve
  `mimari_altlik` yazı kutuları aynı fonksiyonu kullanır. Tablo kullanıcının Z07'si gibi mahal yazısının altında,
  Ç.M. ve duş teknesi üstünde; mimari yazıya değen etiket 0. Borular değişmedi (Y02: Z21 13,27 / 114 13,28 /
  214 13,14 m, eşik 13,11). Etiket ölçekleri: ×1,0 76, ×0,85 6 (holler), ×0,7 0 (önce ×1,0 73, ×0,85 6, ×0,7 3).
  Not: Z21 ve 114'te mahal etiketi (24 °C) kapı kanadı çizgisinin üstünde kalıyor (kesik maske, çizgi görünür); tam boy
  devre tablosu ortadaki serbest zemini aldığı için temiz yer yok.
- **Mahal etiketi:** önce vitrifiye / Ç.M. / kapı kanadı engelinden 6 cm uzak yer; küçük ıslak hacimde çerçeve mahal
  yazısının üstüne binebilir (kullanıcının Z07'si gibi), yalnız 24 °C / Zxx yazıları mimari yazıya değmez. Z21 etiketi
  artık Ç.M. kutusuna değmiyor.
- **İki devreli mahal:** etiketler aynı x hizasında alt alta (18/18 mahal), her biri kendi bandında.
- `yi_kirp.py`: tur 4 kırpımları 17–22 (`YI_KIRP_SADECE=17,18` ile yalnız seçilenler).

## Tur 5 — 15.10 (D) kullanıcı reddi: "Yerden ısıtmayı hiç ellememişsin, kollektör bağlantıları yok, bloklarımı bozmuşsun"
### Planda kollektör bağlantıları (`ayak.py`)
- **Kollektör yeri**: daire holünün (antre-kor.) duvarında; arkası aynı dairenin mahali (ortak alan / balkon / dış değil),
  önü kapı süpürme alanına değmez, hol ≥ 70 cm derin. Puan: devre uçlarına + kombiye Manhattan uzaklık toplamı (merkez).
  Planda dolap 10 cm derin, kullanılan ağızlar kadar geniş; iç iki çizgi gidiş/dönüş barı. Etiket iki satır, kullanıcının
  şema biçimi: `KOLLEKTÖR n AĞIZ` / `ΣW-Ø32` (holde boş yerde; dar holde 90°).
- **Kombi**: sıhhi modeldeki kombi noktası (`proje/denemeler/sihhi2/sihhi_model.json` daireler[].kombi, x + kat ofseti) —
  sıhhi planla aynı nokta; planda mimari kombi kutusu ROTAS-ISITMA-CIHAZ ile + "KOMBİ". Kombi–kollektör gidiş (kırmızı) /
  dönüş (turuncu kesikli) hattı mutfaktan (tezgâh altı tercihli) ve mutfak kapısının mutfak devresi uçlarından uzak
  yarısından hole geçer; mutfak serpantini bu hattın dışında yeniden kurulur.
- **Ayaklar**: 5 cm ızgarada ÇİFT A* (gidiş + dönüş birlikte, 5 cm paralel; aralarına başka hat giremez). Dik açılı,
  dönüş cezalı; serpantin ekseninden ≥ 7,6 cm (parmaklar arasına giremez), duvardan ≥ 4 cm.
  - Mahal içinde: kapı eşiğinden (kapı süpürme alanı + duvar boşluğu, hol tarafına 45 cm) uçlara. Erişim yoksa sırayla:
    besleme ucu yol boyunca 15/30 cm kısaltılır (köşedeki parmak ucuna kapıdan yol) → uçlar kapı köşesine alınır
    (şeritsiz yeniden kurulum) → kapı ağzından 60/120 cm / tam ayak şeridi ayrılıp serpantin şeridin dışında kurulur.
    Çok devreli mahalde erişim devrelerin hepsi BİRLİKTE (birbirini kesmeden) denetlenir; bulunan mahal içi yol sabitlenir.
  - Kapısız geçiş: kapı poligonu yoksa / hole uzaksa (duş kabini kapısı) iki mahal poligonu ≤ 3 cm olan ortak kenar
    (duvarsız açıklık) ya da mimari çizgi kesmeyen duvar boşluğu kullanılır.
  - Holde: **düzlemsel ağız ataması** — hol sınırı boyunca kapılar kollektörün bir ucundan öbürüne sıralanır, ağız
    çiftleri ters sırayla verilir (kesişmesiz kirişler). Yönlendirme önce bu sırayla tek tek, duvara / önceki çifte
    yaslanarak (duvar takibi, iki yönden); olmazsa müzakereli yönlendirme (PathFinder: çakışan düğüm cezası artırılarak
    yeniden), sonra kısmi çözüm + tek tek tamamlama. Hepsinin ardından 3 temizleme geçişi (yüksek dönüş cezası).
  - Hol devresi: demetin dışında kalan, ağız çiftine bitişik hol parçasında kurulur (en uzun kapısız sınır yayına sahte uç
    konarak demette ona koridor bırakılır; 1./2./3. en uzun yay ve sahte uçsuz değişkenler denenir, hol borusu uzun olan
    seçilir).
  - Adaylar (kollektör yeri × sahte hol ucu × kombi) puanlanır: tam bağlantı > kombi hattı > hol devresi uzunluğu.
- **Devre boyu** = ayaklar + serpantin (plan etiketi, şema, Excel aynı); > 80 m ise mahal bir devre fazla bölünür (bu
  koşuda gerek olmadı, en uzun 71,87 m). Planda her devre tek polyline: ağız → gidiş ayağı → serpantin → dönüş ayağı → ağız.
- **Kontroller** (`yi_kontrol.ayak_kontrol`, KONTROL.json): ayaklı devre 81/81; ayak–ayak / ayak–serpantin / ayak–kombi
  kesişmesi 0; farklı hatlar arası < 4 cm 0; ayak duvarı yalnız kapı/geçişte keser (0 ihlal); başka / ısıtılmayan mahalden
  geçen ayak 0; kombi hattı 8/9 daire (2. kat D7: kombi hattı mutfaktaki duvarsız geçişte devre ayaklarıyla kesişmeden
  yerleşemedi — açık madde).
- Hol devre etiketi: değer sütunu (UZ/AR/YER/NO1, tablonun sağ %15'i) kendi serpantininden ≤ 20 cm olacak şekilde
  yeniden yerleştirilir (gerekirse ×0,85); ayak demetindeki başka devreye bağlanmaz (kontrolör Y03/Y05 PASS).
- Son koşu: denetle geçti (kesişme 0, yazı 0); kontrolör yalnız Y01 15 FAIL (hollerde 0,86–1,18 m² borusuz cep — ayak
  demeti holü kaplıyor; salon/yatak D3/D5/D8/D9 5,17–5,29 m/m² < 5,3) — açık madde. Kırpımlar
  `proje/denemeler/yerden2/onizleme/kirp_tur5/` (9 daire kollektör+ayak, şema paneli yan yana 2 adet).
- Kontrolör (`motor/kontrolor/yerden.py`): devrenin mahali artık polyline'ın ORTA noktasını içeren mahal (ayaklar iki uçta
  simetrik); eskisi en çok boru içeren mahaldi (ayaklı küçük ıslak hacim devreleri hole sayılıyordu).
### Şema devre paneli = kullanıcının *U108 bloğu
- `yi_sema.panel`: kendi bloğumuz `ROTAS-YI-DEVRE-PANELI` (MTY bloğu değil) — kullanıcının *U108 geometrisi 1:1
  (duvarlar, beton ayak, şap AR-CONC, döşeme üstü ACAD_ISO08W100 bandı; tarama tanım satırları new_block'tan birebir),
  boru ilmeği (gidiş 50 / dönüş 25, r 5). Yazılar kullanıcının öznitelik yerlerinde/boylarında: Zxx h15 (1,26; 31,86),
  °C h10 (94,35; 33,73), W h10 (14,5; 70), m h10 (62,06; 70), ISIKAYBI h10 (14,15; 110) + devre no sağa dayalı (94,7; 110),
  "PEX BORU, 16 x 2.0" h10 (4,3; −14,1). Bizim eklediğimiz "DEVRE" yazısı kaldırıldı.
- Hat etiketi kullanıcının *U110'u: kılavuz (Px−15, yg) → 6 yukarı → 7,5 sola, "NNNN.NW-Ø20" h10 kılavuzun solunda.
- Gidiş Px−5'ten (57,5), dönüş Px'ten (22,5) iner (kullanıcının şeması).

## Tur 6 — 15.10 (D) ikinci ret: "Yerden ısıtmayı hiç ellememişsin, kollektör bağlantıları yok, bloklarımı bozmuşsun"
### Bloklar kullanıcının bloklarından BİREBİR (`yi_bloklar.py`, kazan dairesi `bloklar_onayli.py` yöntemi)
- `yi_bloklar.py --cikar` new_block'taki örnek yerleşimi okur; GÖRÜNEN nesneleri (invisible=1 nesneler ve gizli
  öznitelikler hariç, iç içe INSERT açılır) yerleşimdeki görünüşüyle cm cinsinden `kutuphane/yerden/ROTAS_YI_BLOKLAR.dxf`
  kütüphanesine yazar. Çalışma anında yalnız kütüphane okunur (MTY dosyası/adı/katmanı yok). Renkler çözülmüş sabit renk,
  katman 0; boru çizgileri ROTAS-ISITMA-GIDIS/DONUS-BORU. Taramalar kullanıcının desen satırlarıyla birebir (ezdxf
  HATCH.transform deseni kütüphaneden yeniden kurduğu için öteleme elle).
- Bloklar: `ROTAS-YI-DEVRE-PANELI` (*U108), `ROTAS-YI-KOMBI-KOLLEKTOR` (*U127; n ≠ 9 ağızda STRETCH: soldaki ağız
  birimleri silinir, sol uç kayar, kombi yerinde), `ROTAS-YI-MAHAL` (MTY-RADYATOR MAHAL), `ROTAS-YI-ETIKET`
  (MTY-ETIKET; değerler kullanıcıdaki gibi sağ sütunda sağa yaslı, "W" sütun başında), `ROTAS-YI-HAT-ETIKETI` (*U110),
  `ROTAS-YI-KOLLEKTOR-ETIKETI` (*U111). Şema paneli artık yalnız kullanıcının yazıları: Zxx, °C, W, m, ISIKAYBI, devre no,
  PEX BORU (eski "DEVRE nn" yazısı yok).
- Piksel karşılaştırma (`yi_blok_karsilastir.py`, siyah zemin, ±1 px; çıktı `kutuphane/arastirma/kontrol_png/yerden_tur5_uretici/blok_*.png`):
  panel F1 0,999, kombi+kollektör 0,999, mahal 1,000, hat/kollektör etiketi 1,000, devre etiketi 0,69 (sol yazı sütunu
  hariç 0,93): kullanıcının MTY-ETIKET'i aynalı yerleştirildiği için sabit yazıları ("Hat uzunluğu:" ...) ters görünür;
  bizde aynı hücrede okunur.
### Plan
- Kollektör etiketi `KOLLEKTÖR Kn — m AĞIZ` (n = daire no, m = devre sayısı) + `ΣW-Ø32`; dolapta her ağızda kısa çıkış
  çizgisi.
- Devre no: daire içinde PLANDAKİ KOLLEKTÖR AĞIZ SIRASIYLA (gidiş ağzı slotu artan) -> şemadaki panel sırası (no azalan,
  en büyük kollektöre en yakın) plandaki ağız sırasıyla aynı (model json `kollektor.plan_agiz_sirasi` / `sema_sirasi`).
- D7 (2. kat) kombi hattı: mutfağın hole açılan geçişi kapı poligonu olarak tanınmıyor (duvarsız geçiş), kombi balkonda;
  kombi çifti ile mutfak ayakları aynı geçişte düzlemsel sıraya giremiyor. Denenen ek adaylar (iki yönlü hol demeti,
  kombi hattı geçişin öbür yarısından; `YI_ADAY_EK=1`) çözmedi -> açık madde (planda kombi işaretli, hat yok).
