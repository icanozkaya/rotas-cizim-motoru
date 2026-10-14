# kontrolor — KONTROLÖR (onay) sistemi

```
python3 motor/kontrolor/kontrolor.py <dxf> --mimari ornekler/new_block.dxf.xz --rapor <rapor.md> [--png-ust 12] [--png-yok]
        [--pencere '{"Z":[x0,y0,x1,y1],...}'] [--katman AD,AD] [--referans-yok] [--referans-kaydet]
        [--tur sihhi|yerden] [--kat-pencere '{"Z":[...],...}'] [--excel hesap.xlsx]
# yerden ısıtma (tur 1 dosyası; kat paftası çerçevesiz -> kaynak pencereleri):
python3 motor/kontrolor/kontrolor.py proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf --mimari ornekler/new_block.dxf.xz \
        --tur yerden --excel proje/denemeler/yerden2/NB_YERDEN_ISITMA.xlsx --rapor <rapor.md>
# kullanıcının kendi ısıtma şeridi (referans kalibrasyonu):
python3 motor/kontrolor/kontrolor.py /tmp/claude-0/uu/new_block.dxf --mimari ornekler/new_block.dxf.xz --tur yerden \
        --kat-pencere '{"Z":[275281,-444050,277340,-441150],"1":[277340,-444050,279379,-441150],"2":[279379,-444050,281418,-441150]}' \
        --rapor <rapor.md> [--referans-kaydet]
```
Çıktı: `<rapor>.md` (SONUÇ: ONAY / RED + düzeltme listesi, özet tablo, ayrıntı, eşikler) + `<rapor>_png/`
(her FAIL için `Tnn_kat_nn.png`: kontrol edilen | referans new_block yan yana, bulgu sarı halka; `GENEL_KAT_*.png`,
`GENEL_SEMA.png`). R4 örneği: `kutuphane/arastirma/KONTROLOR_R4_RAPORU.md`. Protokol: `onay_protokolu.md`.
Süre: R4 (3 kat + şema) ~15 s ölçüm, PNG'lerle ~80 s.

## Dosyalar
| Dosya | Ne yapar |
|---|---|
| `kontrolor.py` | CLI, kat eşleme, test çalıştırma, PNG, rapor |
| `mimari_bilgi.py` | mimari tanıma: `uctan_uca/mimari.py` (mahal poligonu `rooms.detect`, ıslak hacim, armatür imzaları, betonarme) + daire grupları (daire no yazıları tohum, duvar rasterinde yürüme mesafesi `MCP_Geometric`, ulaşılamayan mahal komşuluktan), ortak alan, koridor, balkon, mimarın yağmur inişi (eş merkezli çift daire) |
| `cizim.py` | kontrol edilen DXF: çerçeveler, kat paftaları (başlık "ZEMİN KAT ... PLANI"), şema paftası ("KOLON ŞEMASI"), katman sınıfları (`denetle.boru_katmani` üstüne pis/sıcak/soğuk/yağmur), semboller (SUZGEC, PIS-SU-KOLON, KOLON-NO, SAYAC, yağmur daireleri), etiketler (çap blok öznitelikleri + etiket katmanı yazıları), mimari yazılar; **kat eşleme**: kaynak kat penceresi yazıları ↔ pafta yazıları metin eşitliğiyle öteleme kipi (R4: 77-78 eşleşme) |
| `testler.py` | T01–T11 (aşağıda) ve eşikler (üst blok) |
| `testler2.py` | T12–T17 (15.10.2026, tur 1 kontrolör raporlarının "araç ölçmüyor" dediği hatalar) |
| `yerden.py` | `--tur yerden` takımı Y01–Y06 (+ T11, T16, T17) |
| `kutu.py` | gerçek yazı kutusu: `ezdxf.tools.text_size` (yazı tipi genişliği, büyük harf + alt uzantı), halign/valign, döndürme; MTEXT `mtext_size` + attachment point + text_direction |
| `kirp.py` | ezdxf drawing + matplotlib ile pencere kırpımı (siyah zemin), PIL yan yana |
| `referans_new_block.json` | aynı testlerin kullanıcının kendi `new_block.dxf` çiziminde verdiği sayılar (raporda "Referans" sütunu); `--referans-kaydet` ile yenilenir. `_cizim`: kullanıcının kolon numara/konumları ve Ç.M./B.M. yerleri (kat yerel koordinatı; T12 "yeni numara", T13 makine yeri referansı). `_yerden`: `--tur yerden` sayıları. `_aciklama` / `_aciklama_yerden`: referans sütunundaki açıklamalar (elle) |

## Testler
| Test | Ölçüm | FAIL eşiği |
|---|---|---|
| T01 | balkon süzgeci (balkon poligonunda SUZGEC sembolü) → bağlı ağ: pis su katmanı/kolonu var mı; yağmur inişine (yağmur dairesi / YB balonu / mimarın çift dairesi) yol boyu | pis suya bağlı; inişe ulaşmıyor; yol > 300 cm; balkon içinden pis su hattı |
| T02 | pis su ağı (graf): her parça açısı; her armatür (mimari imza) → en yakın kolon yolu | açı {0,45,90} ± 4° dışı (≥ 25 cm parça); yol > 300 cm; yol armatür+kolon mahalleri (+30 cm) dışında > 40 cm; WC/LV/DUŞ/EVİYE 50 cm içinde hat yok |
| T03 | pis su hattının mahal iç bölgesinde (poligon −30 cm) kalan boyu; 0/90 dışı tek parça boyu | iç bölge ≥ 100 cm (30–100 BİLGİ; referansta en çok 97); eğik parça ≥ 150 cm |
| T04 | sıcak su bağlı ağı: en çok örtüştüğü daire; ortak alan (−10) ∪ başka daire (balkonsuz, −45) ∪ bina dışı (+100) içindeki boyu; kombiye yakınlık | > 15 cm; kombiye 80 cm içinde başlamıyor |
| T05 | sıcak ↔ soğuk kesişme; sıcak parçası (≥ 60) boyunca soğuğa mesafe | kesişme (uçtan 15 cm / armatüre 60 cm / köşe yan değiştirme hariç → köşe BİLGİ); eşlenen (3–30 cm) oran < %80; ofset std > 6 |
| T06 | koridor (antre-kor./merdiven/hol) içindeki temiz su parçasının duvara oranı | **yalnız BİLGİ**: kullanıcının kendi çiziminde antre hatları duvar dibinde, B kuralı "koridor ortası" — karar kullanıcıda |
| T07 | etiket (çap blok öznitelikleri, CIHAZ/KOLONNO/HAVALANDIRMA-YAZI/YAZI katmanı) kutuları (ezdxf yazı ölçüsü) | etiket–etiket örtüşme > 0,2 cm² (aynı bloğun kendi öznitelikleri hariç); etiket–mimari yazı örtüşme; hat yazı kutusundan ≥ 8 cm geçiyor; çap etiketi yüksekliği ortanca 8–12 dışı |
| T08 | şema paftası: ZEMİN KAT / n. KAT yazılarından bantlar; SAYAC sembolleri; D1.. daire etiketleri | sayaç y ≥ 1. kat çizgisi; sayaç x daire bloklarının solunda değil; "SAYAÇ ... KAPI" yazısı; zemin solunda sayaç yok |
| T09 | ıslak mahal poligonunda süzgeç sembolü (çizim SUZGEC blokları + mimari ızgara, 15 cm kümeli) | ≠ 1; süzgeç kuru mahalde |
| T10 | PIS-SU-KOLON sembolü: ıslak mahal (+40 cm) içinde mi, betonarme içinde mi, en yakın köşe | dışında / betonarme / köşe > 45 cm |
| T11 | `denetle.denetle()` | MTY, önek, köprü, kesişme, elektrik, yazı (%2), lejant, audit, "yetersiz" |
| T12 | kolon numaraları (`Cizim.kolon_numaralari`: kullanıcının dinamik `KOLON PİS SU` bloğu özniteliği P<n> ya da kolon sembolü + en yakın balon ≤ 130) her katta, kat yerel koordinatında | aynı numara bir katta eksik; eksenden > 5 cm kaçık; referans new_block'ta olmayan yeni numara; numarasız kolon |
| T13 | çizilen Ç.M./B.M. (CAMASIR/BULASIK/MAKINE blokları + "Ç.M."/"B.M." tesisat yazıları) ↔ mimari Ç.M./B.M. (mimari sembol/yazı + new_block'ta kullanıcının makine blokları) | aynı mahal/daire içindeki yerine > 40 cm (taşınmış); kolon (r 8) / aspiratör kutusu makine yerine < 15 cm (işgal) |
| T14 | aspiratör notu ("Aspiratör" geçen tesisat yazısı + alt satırları) → sahibi: kılavuzla bağlı aspiratör sembolü → en yakın sembol → en yakın ıslak hacim | not kutusu sahibine > 60 cm; not ortak alanda / başka dairede; kılavuz başka mahal içinde > 15 cm |
| T15 | ıslak hacim (mutfak hariç) pencere etiketi (S/P nn, ≤ 30 cm, en yakın mahal) | penceresiz ve 40 cm içinde aspiratör sembolü / 60 cm içinde (ortak alanda olmayan) not yok; < 1 m² duş kabini BİLGİ |
| T16 | tüm yazılar (model, öznitelik, blok içi): `SIZINTI` kalıpları; renkler BYLAYER/BYBLOCK çözülerek | "(EK)", new_block, otomatik, dosya adı, kural cümlesi; ACI 250–255 ya da çok koyu true color (WIPEOUT hariç; mimari katman hariç) |
| T17 | paftalar: çerçeve (PAFTA/CERCEVE/ANTET, yükseklik ≥ 1000) ya da ANTED düşey ayraçları (üst/alt çizgiyle örtülü); başlık yazısından tür | genişlik referansın ± %5 dışı; tam şeritte (≥ 5 pafta) eksik pafta (çatı, detay ...), tanımsız sayfa, sıra hatası |
| T07 ek | gerçek yazı kutusu (`kutu.py`); etiket ↔ mimari tarama (duvar/betonarme), ↔ eviye / B.M. / mimari Ç.M. / kombi / hela / makine / aspiratör sembolü, ↔ asansör boşluğu | kutunun > %25'i taramada / sembolde, > %30'u asansör boşluğunda (merdiven holü BİLGİ) |
| T04 düzeltme | daire ataması: yürüme mesafesi + **kapı kuralı** (mahal hangi dairenin kapısına açılıyorsa o daire): kapı ölçü yazısının (60–120 / ≥ 180) iki yanındaki mahaller komşu; mahalin kapı komşularının hepsi tek bir daireyse o daire | (eşik aynı) |

### Yerden ısıtma (`--tur yerden`, `yerden.py`)
| Test | Ölçüm | FAIL eşiği |
|---|---|---|
| Y01 | oda/salon/yatak/hol: PEX boyu (mahal + 5 cm) / mimari "xx.xx m²" yazısı; borusuz cep = mahal(−20) − boru(+12), 15 cm açma | yoğunluk < 5,3 m/m² ya da cep > 0,6 m²; 5,3–6,0 BİLGİ (hedef 6,0); ısıtılmayan mahalin iç bölgesinde > 100 cm boru |
| Y02 | banyo / wc+banyo yoğunluğu; devre boyları; ≤ 2,65 m² duşlu mahal | banyo < 3,0 m/m²; devre < 3 m; ≤ 2,65 m² wc-duş/duş için ayrı devre |
| Y03 | devre etiketi (UZ/YER öznitelikli blok; görünen öznitelik kutuları) → bindiği devre (≤ 30 cm) ya da hat uzunluğu eşit devre → devrenin mahali | etiket merkezi o mahalde değil (mahal poligonuna girmeyen nişte ≤ 50 cm kabul) |
| Y04 | kılavuz (KILAVUZ / ISITMA-ETIKET katmanı çizgileri, kapalı çerçeve hariç) | > 100 cm ya da başka mahal içinden > 15 cm |
| Y05 | etiketteki hat uzunluğu ↔ bindiği devre | fark > 0,6 m |
| Y06 | plan etiket W ↔ şema "NNNN.NW-Ø20" yazıları ↔ Excel (PETEK LİST ısı kaybı, yoksa YERDEN ISITMA devre satırları) zon toplamı | plan W şemada yok; zon W farkı > %1 |

## Doğrulama (14.10.2026)
- **R4** (`proje/denemeler/_arsiv/uctan_uca/NB_SIHHI_DENEME_R4.dxf`): RED 237 madde. Kullanıcının 4 RED görüntüsündeki
  hata türlerinin tamamı yakalandı: balkon süzgeci → P9 (T01 ×3 kat), sayaç kat bandında/daire bloğunda (T08 ×17),
  sıcak su merdiven holünden (T04 daire 6: 716 cm, ortak alanda 384 cm; daire 9), wc-banyo çapraz uzun pis su (T03),
  etiket hat üstüne (T07 ×180). Rapor: `kutuphane/arastirma/KONTROLOR_R4_RAPORU.md`.
- **R3** (RED görüntülerinin 4.'sü R3'ten): etiket–etiket 91, etiket–mimari yazı 59, etiket–hat 131 (1. kat) → yakalanıyor.
- **new_block (referans, kullanıcının çizimi)**: T01/T03/T05/T06/T08/T10 geçer; T02 59 (serbest açılı branşman — kural C
  45° ister), T04 1 (daire ataması sınırı), T07 175 (kullanıcının etiketleri de başka hatların üstünden geçiyor),
  T09 16 (mutfak/wc-lvb.'de süzgeç yok — B kuralı ister), T11 34 (MTY, beklenen). Bu sayılar raporda "Referans" sütunu.

## Doğrulama (15.10.2026) — yeni testler
- **Kalibrasyon, kullanıcının new_block çizimi** (`--referans-kaydet`; sayılar `referans_new_block.json`):
  sıhhi T12 ✓ (9 kolon 3 katta ± 1,5 cm), T13 ✓ (6 makine/kat), T14 ✓ (3–4 not/kat), T15 ✓ (duş kabini BİLGİ), T16 ✓, T17 ✓
  (yerleşim 1682, temel 2471, Z 2065, 1/2 2039, çatı 2058, şema 7418, detay 2065), T04 ✓ (önceki 1 FAIL: 1. kat wc-duş D5'e
  atanıyordu; kapı kuralıyla D6). T07 yeni alt testler 0 (etiket–etiket 0, tarama 0, eviye/makine 0, asansör 0); T07 toplamı 208 =
  etiket–mimari yazı 80 + etiket–hat 128 (gerçek kutu daha büyük; kullanıcı tarzı, referans sütununda).
  Yerden: Y01–Y04, Y06 ✓ (Y01 24 BİLGİ: 5,38–5,98 m/m²), Y05 6 = kullanıcının kendi etiket hatası (Z01 39,19 ↔ 40,66; Z03
  Z04'ten kopya; 3 katta), T17 ✓ (yerleşim 1682, Z 2059, 1/2 2039, şema 6693).
- **Kalibrasyon kararları**: T07 armatür alt testi yalnız eviye, B.M., mimari Ç.M., kombi, hela, makine, aspiratör üstünde
  (kullanıcı pis su iniş etiketini klozet/lavabo/duş/süzgeç/çamaşır makinesi bloğu üstüne yazıyor — 52+ kez, tarzı);
  merdiven holündeki etiket BİLGİ (kullanıcı 1. katta "Ø100 / 46 SB"yi kılavuzla merdiven holüne almış); kolon no balonu
  (P/YB) ortak alan denetimine girmez. Y01 sert sınırı 5,3 + cep ölçütü (kullanıcıda cep 0, tur 1'de 1,0–1,6 m²).
- **Tur 1 dosyaları (commit 7d8d896 / yerden2 HEAD) — raporların gözle bulduğu hatalar artık ölçülüyor**:
  - `NB_SIHHI_KAT_PLANLARI.dxf`: T12 8 (P2/P3 1. katta yok, P10/P11 yeni + zemin/2. katta yok), T13 19 (Ç.M. (EK) 95/67/73 cm,
    B.M. (EK) 211 cm taşınmış; P3/P6 banyo Ç.M. nişinde, P7 B.M. yerinde, aspiratör D3 Ç.M. nişinde), T14 3 (merdiven holündeki
    not 252 cm kılavuzla; 1. kat yatak odasındaki not), T15 6 (D2/D4/D7 banyo + wc-lvb. aspiratörsüz), T16 10 ("(EK)", lejant kural
    cümleleri), T07 55 (tarama 25, eviye/B.M./Ç.M. 27, asansör 3). T04 artık geçer (tur 1'deki tek FAIL eşleme hatasıydı).
  - `NB_SIHHI_PAFTA_DENEME.dxf`: + T16 28 (izometride "new_block.dxf", "(otomatik)"; ACI 250 lejant/hesap yazıları ve sembol
    dolguları), T17 3 (şema 9817 ≠ 7418, çatı paftası yok, LEJANT sayfası tanımsız).
  - `NB_YERDEN_ISITMA.dxf` + xlsx: Y01 39 (cep 1,0–1,6 m², 3,7–5,1 m/m²), Y02 11 (banyo 1,6–2,6 m/m², 1,66 m devre, 2,65 m² wc-duş
    devresi), Y03 13 (merdiven/asansör/bina dışı etiketler), Y04 11 (314–378 cm kılavuz), Y06 26 (plan W = 2 × Excel W), T17 1
    (şema 7145 ≠ 6693).
- Süre: kat planları ~25 s, new_block (tam şerit) ~70 s, `--tur yerden` ~30–65 s (PNG'siz).

## Sınırlar
- Mahal tanıma kural tabanlı (`mimari.py`): etiketleri ROOM_WORDS + burada eklenen adlar; başka mimaride ad listesi
  (`mimari_bilgi._etiketler`) genişletilmeli. Daire grupları daire numarası yazısı (h ≥ 15, 1–40) ister; yoksa T04 yalnız
  ortak alan/bina dışı ölçer.
- Kat eşleme yazı eşitliğiyle (en az 6 eşleşme); mimari yazıları değiştirilmiş çıktıda `oteleme_bul_cizgi` (duvar çizgisi
  histogramı) yedeği denenir.
- Armatür bağlantı noktası mimari imzadan (klozet elipsi merkezi, lavabo gideri ...) alınır; motor hattı armatürün 50 cm
  dışından başlıyorsa "bağlı değil" sayılır.
- Şema tarzı (new_block şemasına benzerlik) ölçülmez; kontrolör GENEL_SEMA.png'yi `ornekler/new_block_onizleme/` ile
  göz ile karşılaştırır (protokol §2-3).
- T07 yazı kutuları yazı tipine bağlıdır (ezdxf `text_size`; yazı tipi bulunamazsa ezdxf'in yedek yazı tipi). Kaynak
  mimariden gelen (çizimde mimari yazı katmanı yoksa) yazılar hâlâ karakter tahminiyle.
- T13 mimari Ç.M. yalnız banyodaki 50–72 cm kare + "bul. mak"/"Ç.M." yazılarından tanınır; new_block'ta eksikleri kullanıcının
  makine blokları (`_cizim`) tamamlar. Başka mimaride makine tanınmazsa bulgu BİLGİ ("ölçülemedi").
- T15 pencere = mimari pencere etiketi (S01 / P01 ...); etiketsiz mimaride her ıslak hacim penceresiz sayılır.
- T12 "yeni numara" ve T13 referans makineleri yalnız `--mimari new_block` ile (kullanıcı referansı yalnız orada var).
- Y01/Y02 mahal alanı mimari "xx.xx m²" yazısından; yazı yoksa mahal poligonu (kaba). Poligon m²'nin 1,25 katından büyükse
  cep ölçülmez (new_block zemin D3 salonu).
