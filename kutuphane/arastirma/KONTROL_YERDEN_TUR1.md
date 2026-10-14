# KONTROL — YERDEN ISITMA, TUR 1 (bağımsız kontrolör)

- İncelenen: `proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf` (3 kat planı + kolon şeması), `NB_YERDEN_ISITMA.xlsx`
- Referans: kullanıcının `new_block.dxf` ısıtma seti (`/tmp/claude-0/y2/new_block.dxf`), `YERDEN_ISITMA_ALTIN_REFERANS.md` §7 (26 kural), `referans/yerden/*.png`, README yerden ısıtma maddeleri, `10_YERDEN_ISITMA_BORULAMA.md` §0
- Yöntem: Üreticinin kodu okunmadı. Çizimi ezdxf drawing eklentisiyle kırptım ve kullanıcının çizimindeki aynı mahallerle yan yana koydum (plan kayması dx = +22 762 cm, şema dx = +22 568 cm). Görüntüleri tek tek gözle inceledim. Ölçümleri DXF'ten ve model JSON'dan aldım. Excel'i LibreOffice ile yeniden hesaplattım.
- Kanıt PNG'leri: `kutuphane/arastirma/kontrol_png/yerden_tur1/` (01–10 ve 13–15 yan yana; solda kontrol edilen, sağda referans)
- `denetle.py`: **geçti** (MTY 0, önek 0, köprü 0, kesişme 0, yazı 0, audit 0). Üreticinin `KONTROL.json` dosyasında da kesişme, tefriş, 80 m ve uç aralığı listeleri boş. Ancak bu testler aşağıdaki hataları **yakalamıyor**: yoğunluk, etiketin mahal dışında olması, kılavuz çizgi ve şema sembolü.

## KARAR: **RED**

Geometri temiz: kesişme yok, ≤80 m sağlanıyor (L_max 59,5 m), uçlar 15 cm, dönüşler bulge 0,4142, parmaklar yatay. Buna karşılık çizim kullanıcının çizimiyle yan yana konduğunda aynı görünmüyor. Mahaller boş kalıyor, etiketlerin üçte biri mahal dışında ve uzun kılavuz çizgilerle bağlanmış, ıslak hacimler yarım. Plan ile Excel W değerleri de tutarsız.

---

## Düzeltme listesi (madde madde)

### R1 — Serpantin mahali doldurmuyor (etiket cebi yüzünden yoğunluk düşük). Kabul EDİLMEZ.
- Ölçüm (boru m / mimari m²): yatak ve salonlarda **3,45–5,3**, ortalama 4,1. Referansta yatak ve salonda **5,9–6,5** var (Z05 99,8/15,44 = 6,46; Z04 6,29; Z02 salon 5,85). 15 cm aralıkta teorik tam kaplama 6,67'dir.
- Aynı mahalin yan yana karşılaştırması:

| Kontrol edilen | Referanstaki karşılığı | Kontrol L (m) | Referans L (m) | Oran |
|---|---|---|---|---|
| Z16 yatak 15,44 m² | Z05 | 57,5 (30,33 + 27,13) | 99,83 | %58 |
| Z18 salon 22,31 | Z02 | 97,3 | 130,47 | %75 |
| Z17 yatak 9,05 | Z04 | 42,99 | 56,90 | %76 |
| Z20 antre 11,00 | Z06 | 45,08 | 57,41 | %79 |
| Z09 yatak 14,25 | Z12 | 69,87 | 89,31 | %78 |
| Z12 salon 21,18 | Z09 | 112,38 | 128,25 | %88 |
| Z15 mutfak 10,11 | Z01 | 33,66 | 39,19 | %86 |

- Görsel (PNG 01, 03, 04, 06, 09): her devre etiketinin olduğu yerde parmaklar kesilmiş ve 1–1,5 m'lik boş "cep" kalmış. Z16'da sağ üst köşe ve orta-sağ, Z18'de sol üst, Z02/Z03/Z04/Z09/Z10'da etiket arkası, Z19 odasında sağ şerit (≈35 cm) boş. Referansta etiket serpantinin **üstüne** biner ve boru altından kesintisiz geçer.
- Düzeltme: Etiket cebi kaldırılmalı. Mahal, referanstaki gibi 7,5 cm kenar payıyla tam doldurulmalı. Etiketin altı README gereği WIPEOUT ile maskelenmeli (maske yalnız görüntüdür, boru altından devam eder). Hedef: oda, salon ve hol ≥ 6,0 m/m² (ısıtılan net alan). Uzayan devre 80 m'yi aşarsa referanstaki gibi 2'ye, gerekirse 3'e bölünmeli.

### R2 — Islak hacimler yarım ısıtılmış veya anlamsız devre var
- Z07 banyo (5,36 m²) 13,29 m, Z14 banyo 11,02 m. Referansta aynı banyolarda **23,53 m** var. Z21, 114 ve 214 wc+banyo (4,37 m²) 7,1 m, referansta **13,80 m**. Banyonun üst yarısı (duş teknesi ve klozet çevresi dışı) boş kalmış. Uzun boş besleme hatları ve kısa "omega" parmaklar var (PNG 05, 01).
- **1. kat D6 "wc-duş" 2,65 m² (121): 1,66 m'lik tek parmaklı devre, 58,1 W** (PNG 10). Ayrıca 122 banyo yalnız 7,13 m. Referansta bu ikili tek banyo devresi olarak çözülmüş (121, 23,53 m). Duş/wc ≤ 2 m² mahal ısıtılmaz. 1,66 m'lik devre şemada da ayrı bir kollektör ağzı ve panel olarak duruyor ve bu kabul edilemez.
- Düzeltme: Banyoları referanstaki gibi kapı tarafından tam doldur. Yalnız klozet, lavabo ve duş teknesi poligonlarını hariç tut. wc-duş + banyo çiftinde ya tek banyo devresi kur ya da wc-duşu ısıtma. 1,66 m devresini kaldır.

### R3 — 16 devre etiketi kendi mahalinin DIŞINDA; ortak alana veya bina dışına konmuş
Bunlar her katta antre-koridor ve banyo/wc etiketleri (`etiket = disari`):
- **Bina dışında, balkon tarafında**: Z13 (43,48 m) ve Z21 (7,13 m) zemin sol dış cephede, 106/114/206/214 aynı yerde, 120/220 sağ dış cephede. Etiketin bir kısmı pafta dışına taşıyor (PNG 00, 07, 11, 12).
- **Merdiven ve asansör holünde (ortak alan)**: Z06 (43,41 m), Z07 (13,29 m), Z14 (11,02 m), 107, 121 (1,66 m), 122, 207, 221 (PNG 05, 08, 10). Z14 etiketi asansör boşluğunun üstünde, Z07 etiketi merdiven basamaklarının üstünde.
- Referansta her hol ve banyo etiketi kendi mahalinin içinde, uç köşesinin yanında (hol Z13/Z20: hol içinde kapı yanı; banyo Z14/Z21: banyonun içinde, gerekirse serpantin ve vitrifiyenin üstüne binerek).
- Düzeltme: Etiketi kendi mahalinin içine koy, gerekirse serpantinin üstüne bindir (WIPEOUT ile). Dar holde etiket 150×80 sığmıyorsa referanstaki gibi hol boyunca yatay yerleştir. Kılavuz çizgisi kullanma.

### R4 — Uzun ve zayıf kılavuz çizgiler (16 adet, 3,1–3,8 m)
- Katman `ROTAS-ISITMA-ETIKET` LINE uzunlukları 347, 376, 314, 378, 341, 378, 376, 347, 378, 376 cm… Sarı ince çizgiler duvarları, kapıları, duş ve oda mahallerini **çapraz** keserek geçiyor. Örnekler: zemin sol üstten wc+banyoya inen çizgi duş ve odayı kesiyor (PNG 01); merdivenden banyoya giden çizgi basamakları kesiyor (PNG 05); dış cepheden yatak odasından geçerek hole giden çizgi (PNG 07).
- Referansta kılavuz çizgisi **hiç yok**.
- Düzeltme: R3 uygulanınca kılavuzların tümü kalkmalı.

### R5 — Mahal etiketleri vitrifiye ve duvar üstünde (ıslak hacimler)
- Z07, Z21, 107, 122, 207, 221 mahal etiketleri duş teknesi veya küvet çizgisinin üstüne oturuyor. Z14'ün etiketi banyonun sol duvarını kesiyor (PNG 05, 10). README ET-6 kuralı: etiket mimari yazıya/çizime binmez.
- Düzeltme: Islak hacimde mahal etiketini serbest zemine (serpantin üstüne) koy.

### R6 — Plan W ↔ Excel W tutarsız (2 kat fark)
- Planda ve şemada W = 35,0 W/m × L (Z01 45,84 m → **1604,4 W**). Excel `PETEK LİST`/`YERDEN ISITMA` sayfalarında N = 17,5 × L (**802,2 W**). Daire toplamları da farklı: şemada D3 için "11182.5W-Ø32", Excel'de bunun yarısı.
- Ayrıca Excel'deki "Mahal ısı ihtiyacı Q" (D sütunu) gerçek bir ısı kaybı değil. Değer **17,5 × boru boyu** olarak elle yazılmış, bu yüzden Q/A, modül ve MMO hesapları döngüsel. Şablondaki ZEMİN ve 1 NK ısı kaybı sayfaları silinmiş. Teknik raporda U değerleri duruyor ama arkasında hesap yok.
- MMO sayfasında Z01 ve Z08 mutfakta yüzey sıcaklığı **29,25 / 29,64 °C**. Bu değer 29 °C yaşam alanı sınırının üstünde ve uyarı verilmemiş.
- Düzeltme: Plan, şema ve Excel'de tek W kaynağı kullanılmalı. Ya şablonun 17,5 W/m'si plana yazılmalı ya da 35 W/m Excel'e girilmeli. Hangisinin seçildiği teknik rapora yazılmalı (Altın ref. §6). Isı kaybı yoksa Q sütunu "boru boyundan" diye açıkça işaretlenmeli ya da kullanıcıdan ısı kaybı istenmeli.

### R7 — Kolon şemasında kollektör temsili kutu
- Referansta kollektör gerçek bir manifold bloğu: gidiş ve dönüş barı, ağız başına vana ve rekor, iki uçta küresel vana (`*U127`). Kontrol edilen çizimde kırmızı dikdörtgenin içinde iki çubuk ve ağızlarda küçük daireler var, yani temsili bir şekil (PNG 15). README kuralı: "vana ve cihazlar gerçek gösterimleriyle (kutu, daire vb. temsili şekil yok)".
- Kombi bağlantısında da fark var: referansta yalnız dönüşte vana var ve hat kombi altından kollektör yanına iniyor. Kontrol edilende iki hatta vana var ve dönüş kesikli çizgisi sola kırılıp kollektörün altına dolanıyor.
- Düzeltme: Referanstaki kombi + kollektör bloğu geometrisi kullanılmalı (ağız adımı 10, gidiş-dönüş 5).

### R8 — Şema genel düzeni: kabul edilebilir, küçük farklar var
- Bantlar 400 cm, kat yazıları dikey kırmızı, daire sırası D3-D2-D1 / D6-D5-D4 / D9-D8-D7, paneller büyükten küçüğe, hat etiketi "W-Ø20" ve hatlar kesişmiyor. Bunlar referansla uyumlu (PNG 13, 14).
- Farklar: pafta 7145 cm (ref 6693), bant iç genişliği 6993 (ref 6490). Lejant ve notlar şema paftasının üst boşluğunda; referansta bu alan boş. Panel üstündeki "DEVRE n" yazısı referansta "ISIKAYBI n" (kabul edilebilir).
- R2 düzeltilince 1,66 m ve 7 m'lik paneller kalkacak ve devre sayıları değişecek. Şema yeniden üretilmeli.

### R9 — Excel teknik eksikler
- LibreOffice ile yeniden hesap: 7 sayfada 2008 formül var, **#hata yok**. Formüller şablonla aynı (F = D/E, G = 76,263 − 0,539F, K = J/80, L = CEILING).
- `kapak` ve `TEKNİK RAPOR` sayfalarında yazdırma alanı tanımlı değil (README: "yazdırma alanları ayarlı").
- Dosyada şablondan kalan bir **dış bağlantı** var: `xl/externalLinks/externalLink1` → `Users/user/Desktop/dcm/PROJE/MEKANİK HESAPLAR KOMBİ.xls`. Bu bağlantı Excel açılışında "bağlantıları güncelle" uyarısı çıkarıyor ve yabancı "dcm" izi taşıyor (README: dcm izleri temizlenir). Bağlantı kaldırılmalı.

### R10 — Diğer gözlemler (engelleyici değil, düzeltilmeli)
- Sol üstteki banyo (Z14) parmakları lavabonun altından geçiyor (PEX-10). Referansta da kısmen geçiyor, ama altın kural hariç tutulmasını istiyor.
- Z19 oda (zemin D3): besleme hattı odanın ortasından iniyor ve sağında ≈35 cm şerit boş kalıyor (PNG 01).
- Zemin Z15 ve 1. kat 108 mutfakta mahal etiketinin çevresinde parmaklar kısaltılmış ve cep oluşmuş (PNG 02). R1 ile birlikte düzelir.

---

## Olumlu bulgular (değişmesin)
- 82 devre: her biri tek açık LWPOLYLINE, uç aralığı 15,0, dönüş yayları referansla aynı, parmaklar yatay. En uzun devre 59,5 m (≤ 80).
- Tefriş: mutfak tezgahı ve buzdolabı altında boru yok. Isıtılmayan mahallerde (balkon, yüklük, wc-lvb, asansör, merdiven, en. odası) boru yok.
- Mimari yazılar, ölçüler ve tefriş silinmemiş. Katman önekleri `ROTAS-`. `denetle.py` geçti.
- Etiket blok biçimi (150×80 sarı tablo, 4 satır; mahal kutusu sarı-cyan halkalı, 20/15/24 °C) referansa benziyor ve okunur yönde.
- Sıcaklıklar doğru: oda/salon/mutfak 20, hol 15, banyo 24. Excel mahal alanları mimariyle aynı (11,07; 14,25; 9,31…).

## Tur 2 için kabul ölçütleri (kontrolör yeniden ölçecek)
1. Oda, salon ve hol yoğunluğu ≥ 6,0 m/m² (net ısıtılan alan). Banyo uzunlukları referansın ±%15'i içinde (zemin wc+banyo ≈ 13,8 m, banyo ≈ 23,5 m).
2. 82 etiketin tamamı kendi mahal poligonunun içinde. `ROTAS-ISITMA-ETIKET` katmanında 0 kılavuz çizgisi.
3. < 3 m devre yok. wc-duş ≤ 2,65 m² mahal için ayrı devre yok.
4. Plan, şema ve Excel W değerleri aynı kaynaktan ve teknik raporda belirtilmiş.
5. Şemada gerçek kollektör bloğu. Excel'de dış bağlantı yok, tüm sayfalarda yazdırma alanı var.
