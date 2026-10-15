# KONTROL — YERDEN ISITMA, TUR 2 (bağımsız kontrolör)

- İncelenen: `proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf` (3 kat planı + kolon şeması) ve `NB_YERDEN_ISITMA.xlsx` (15.10.2026 02:50 sürümü)
- Referans: kullanıcının `new_block.dxf` ısıtma seti. Plan kayması dx = +22 761,9 cm (üç katta da aynı, m² yazılarıyla eşlendi), şema kayması dx = +22 568 cm. Ayrıca `YERDEN_ISITMA_ALTIN_REFERANS.md` §7, `referans/yerden/*.png`, README yerden ısıtma maddeleri ve tur 1 raporu kullanıldı.
- Yöntem: Üreticinin kodu okunmadı.
  - `motor/kontrolor/kontrolor.py --tur yerden` çalıştırıldı. Araç raporu: `kontrol_png/yerden_tur2/kontrolor_arac_raporu.md`.
  - Her kat 3×4 pencereye kırpıldı (36 kırpım). Ayrıca ıslak hacimler, etiketler ve şema kırpıldı. Her kırpım ezdxf drawing ile referansın ısıtma setiyle yan yana konup gözle incelendi.
  - Devre boyları, etiket değerleri ve etiket–mimari yazı örtüşmesi (`kutu.py` ile gerçek yazı kutusu) DXF'ten ölçüldü.
  - Excel LibreOffice ile yeniden hesaplatıldı ve paket XML'i tarandı.
- Kanıt PNG'leri `kutuphane/arastirma/kontrol_png/yerden_tur2/` klasöründe (yan yana olanlarda sol taraf kontrol edilen, sağ taraf kullanıcının ısıtma seti).

## KARAR: **RED** (4 madde, hepsi küçük ve yerel)

Tur 1'e göre büyük ilerleme var. Mahaller dolu, etiket cepleri kalktı, etiketler kendi mahalinde ve kılavuz çizgisi yok. W değeri plan, şema ve Excel'de tek kaynaktan geliyor. Kollektör artık gerçek manifold. Excel'de dış bağlantı yok. Yan yana bakıldığında kuru mahaller kullanıcının çizimiyle aynı tarzda görünüyor.

Onay protokolü FAIL bırakmıyor. Araç 11 FAIL verdi ve bunların hepsini çizimde gözle doğruladım. Ayrıca araç dışında bir görsel madde buldum: banyolarda etiket maskesi vitrifiyeyi gizliyor. Aşağıdaki 4 madde düzeltilince ONAY beklenir.

---

## Tur 1 maddeleri — KAPANDI / AÇIK

| Madde | Konu | Durum | Kanıt |
|---|---|---|---|
| R1 | Serpantin mahali doldurmuyor, etiket cebi var | **KAPANDI** | Etiket cebi yok; etiket WIPEOUT ile serpantinin üstünde ve boru altından kesintisiz geçiyor. Kuru mahallerde boru boyu referansın **%84–99**'u. Örnekler: Z16 (yatak 15,44) 86,6 / 99,8 m; Z18 (salon 22,31) 126,8 / 130,5; Z20 (hol 11,00) 57,1 / 57,4; Z15 (mutfak) 39,16 / 39,19. Tur 1'de bu oranlar %58–88'di. Yoğunluk 5,4–6,15 m/m² (ölçüm: Y01, 0 FAIL). Tur 1'deki "≥ 6,0" hedefi her mahalde tutmuyor, ama aynı ölçümle kullanıcının kendi çiziminde de 24 mahal 5,38–5,98 çıkıyor. Bu yüzden hata sayılmadı. PNG 01–05 |
| R2 | Islak hacimler yarım; 1,66 m'lik wc-duş devresi | **KISMEN** — wc-duş devresi kaldırıldı. ≤ 2,65 m² wc-duş/duş ısıtılmıyor. < 3 m devre yok (en kısa 11,99 m). Banyolarda doluluk hâlâ düşük → **Y-2** | PNG 10–13 |
| R3 | 16 etiket mahal dışında | **KAPANDI** — 81/81 devre etiketi kendi mahalinde (Y03). Hol etiketleri hol içinde, banyo etiketleri banyo içinde | PNG 05, 20–22 |
| R4 | Uzun kılavuz çizgiler | **KAPANDI** — `ROTAS-ISITMA-ETIKET` katmanında 0 çizgi (Y04) | — |
| R5 | Mahal etiketi vitrifiye/duvar üstünde | **KAPANDI** (mahal etiketi) — 146 etiket ile 818 mimari yazı arasında örtüşme 0, etiketler arası örtüşme 0. **Ancak** devre etiketinin maskesi küvet/duş teknesini gizliyor → **Y-4** (yeni) | PNG 14, 15 |
| R6 | Plan W ↔ Excel W tutarsız | **KAPANDI** — Tek esas her yerde 35 W/m × L: plan 81/81 = şema; Excel 63 zonun hepsinde plan ile aynı (Y06). Esas teknik rapor §1.3'te yazılı. Q sütununda "boru boyundan" diye işaretli. Yüzey sıcaklığı aşımı için MMO sayfasında uyarı var → kullanıcı sorusu **K-1** | — |
| R7 | Şemada temsili kollektör kutusu | **KAPANDI** — Gerçek manifold çizilmiş: gidiş ve dönüş barı, ağız başına vana/rekor, iki uçta küresel vana. Kombi bağlantısı referanstaki gibi: dönüşte vana var, gidiş kollektörün sol yanına iniyor | PNG 18 |
| R8 | Şema düzeni | **KAPANDI** — Pafta 6 692 (ref 6 693). Bant iç genişliği 6 540 (ref 6 490). Kat yazıları dikey kırmızı. Daire sırası D3-D2-D1. Paneller devre no'ya göre büyükten küçüğe. Kısa paneller kalktı. Lejant ve notlar alt boşlukta | PNG 16, 17, 19 |
| R9 | Excel: yazdırma alanı, dış bağlantı | **KAPANDI** — 7 sayfanın hepsinde `Print_Area` var. `externalLinks` yok, "dcm" izi yok, logo/çizim nesnesi yok. LibreOffice yeniden hesabında 1 981 formül var ve **#hata yok** | — |
| R10 | Z14 lavabo altı; Z19 sağ şerit; mutfak etiket cebi | **KAPANDI** — Lavabo ve klozet altında boru yok. Z19 dolu (46,26 / 46,80 m). Mutfakta cep yok | PNG 02, 03, 10 |

---

## RED maddeleri (tur 3'te yalnız bunlar düzeltilecek; tasarım seçimleri değişmez)

### Y-1 — 1. ve 2. katta yatak odası serpantini yüklüğe giriyor (PEX-9; dosyanın kendi notu 3 de "yüklük ısıtılmaz" diyor)
- 1. kat D4: 102 (yatak 14,25) üst devresi (45,98 m) yüklüğün kapısından (80/220) içeri giriyor. Yüklük içinde **6,4 m** boru var, devrenin sağ ucu x = 255 452. Konum ≈ (255 374, −442 288). PNG 06.
- 2. kat D7: aynı durum (202), yüklük içinde **4,6 m** boru. Konum ≈ (257 377, −442 337). PNG 07.
- Zemin kat (D2) ve referansın üç katı doğru: yüklükte boru yok.
- Düzeltme: Parmaklar yüklük kapısının önünde, yatak odası iç yüzünden 7,5 cm geride bitmeli. Devre boyu bu kadar kısalır (102 için yaklaşık 87,7 → 81 m).

### Y-2 — Islak hacim doluluğu eşiğin altında (Y02, 5 FAIL)
Ölçüm, mahal poligonu içindeki boru boyunun mimari m²'ye oranıdır. Kullanıcının çiziminde Y02'den 0 FAIL çıkıyor.

| Mahal | Mahal içi boru / alan | Oran | Gerekli (≥ 3,0 m/m²) | Kullanıcı çizimi |
|---|---|---|---|---|
| Zemin D2 banyo Z14 (5,36) | 15,6 m (devre 16,03) | 2,92 | ≥ 16,1 m | 23,53 m |
| Zemin D3 wc+banyo Z21 (4,37) | 9,9 m (devre 11,99) | 2,27 | ≥ 13,1 m | 13,80 m |
| 1. kat D5 wc-banyo 114 (4,37) | 9,9 m | 2,27 | ≥ 13,1 m | 13,80 m |
| 1. kat D6 banyo 121 (4,37) | 11,8 m (devre 12,17) | 2,69 | ≥ 13,1 m | — |
| 2. kat D8 wc-banyo 214 (4,37) | 9,9 m | 2,27 | ≥ 13,1 m | 13,80 m |

- Gözle bakınca boş kalan yerler (PNG 10–12):
  - Z14: "banyo 5,36 m²" yazısının çevresinde ≈ 1 × 1 m boşluk var. Besleme hattı klozetin çevresini dolaşıyor ve parmaklar ancak x ≈ +130 cm'den başlıyor.
  - 121: lavabo ile sağdaki besleme hattı arasında ≈ 1,5 × 0,8 m boşluk var.
  - 4,37 m²'lik wc+banyolar: devre boyunun ≈ 2 m'si mahal dışında (kapı/besleme). Klozetin solu ve üst şerit kısa.
- Klozet, lavabo ve duş teknesi altı boş kalmalı (PEX-10, değişmez). Kalan serbest zemin referanstaki gibi doldurulmalı. Eşikler: 4,37 m² için mahal içinde ≥ 13,1 m, 5,36 m² için ≥ 16,1 m.
- Not (engelleyici değil): wc+banyoda bir ilmek Ç.M. kutusunun altından geçiyor. Referansta Ç.M. altında boru yok (PNG 12). Doldururken Ç.M. altı yerine serbest zemin tercih edilmeli.

### Y-3 — İki devreli mahallerde bir etiket öbür devrenin üstünde (Y05, 4 FAIL; ET-3)
- 102 ve 202 (yatak 14,25): "Isıtma Devresi-No.: 3 / 45,98 m" etiketi alttaki 41,72 m'lik devrenin (no 2) parmaklarının üstünde duruyor. Kendi devresi (45,98) mahalin üst yarısında. Devreleri ayrı renkle çizdim (PNG 08): kırmızı = 41,72, yeşil = 45,98.
- 111 ve 211 (salon 22,31): 61,93 m etiketi 60,90 m'lik devrenin üstünde (PNG 09).
- Referansta iki devreli mahalde her etiket kendi devresinin uç köşesinin yanında durur ve iki etiket aynı x hizasında alt alta gelir (altın ref. §4.1). Etiketler kendi devrelerinin üstüne taşınmalı. Değerler doğru, yalnız konum yanlış.

### Y-4 — Banyolarda devre etiketinin maskesi küveti ve duş teknesini tamamen gizliyor (yeni; tefriş silinmez kuralı)
- Altı banyoda (Z07, Z14, 107, 121, 207, 221) devre etiketi küvetin tam üstünde. Etiketin WIPEOUT'u küvetin dış çizgisini, iç çizgisini ve süzgecini görünmez yapıyor. Her etikette 5,7–7,0 m mimari çizgi maskeleniyor (PNG 14).
- Üç wc+banyoda (Z21, 114, 214) etiket duş teknesini (köşegen ve süzgeç) maskeliyor. 214'te mahal etiketi Ç.M. kutusunun üst kenarını da örtüyor (PNG 15).
- Kullanıcının çiziminde etiket de küvetin üstüne gelir, ama maske olmadığı için küvet görünür kalır. README'ye göre yerden ısıtma paftasında tefriş ve vitrifiye **silinmez**. Maske onları baskıda siler.
- Düzeltme (yöntem üreticinin seçimi): Etiket serbest zemine, yani serpantinin üstüne konmalı. 4,37 m² mahalde sığmıyorsa vitrifiyenin üstünde maskesiz bırakılmalı. Ölçüt: hiçbir etiket kutusunun altında vitrifiye/tefriş çizgisi maskelenmemeli. Bu kontrolde 17 etiket kutusunun içinde mimari çizgi kalıyor. Bunların 9'u banyo/wc+banyo devre etiketi (195–695 cm çizgi) ve 2'si mahal etiketi (214 ve 114). Hol etiketlerindeki 6 durum kabul edilir: Z13/106/206'da etiket alt kenarı duvar çizgisine teğet (PNG 05 ile `ETK` kırpımı), Z06/120/220'de örtülen 34 cm'lik kapı kasası kenarı.

---

## Kullanıcıya soru (RED gerekçesi DEĞİL — tasarım seçimi kullanıcının)

**K-1 — 35 W/m × L esası ve MMO sınırları.** Plan, şema ve Excel, kullanıcının çizimindeki 35 W/m × L esasına göre tutarlı. Ancak 15 cm aralıkla bu esas q" ≈ 200–215 W/m² veriyor. Excel'de bunun sonuçları:
- MMO sayfası: döşeme yüzey sıcaklığı **≈ 37,8 °C** (oturma alanı sınırı 29 °C, banyoda 39,1 °C). Uyarı satırı (B38–B39) yazılmış.
- MMO sayfası: en büyük devre basınç kaybı ≈ 19 000–22 300 Pa. Bu, sayfanın Δpmax = 9 828 Pa değerinin üstünde.
- `YERDEN ISITMA` sayfasında şablon formülü G = 76,263 − 0,539·F negatif "MODÜL" (−5,95 … −32,4) ve negatif "m²" (H sütunu, −283,98 gibi) üretiyor. Şablon 17,5 W/m için kurulmuş. Bu sayfa bu hâliyle basılırsa okuyan mühendis tuhaf bulacaktır.

Kullanıcıya sorulacak: "Devre gücü 35 W/m × L (sizin çiziminizdeki gibi) mi kalsın, yoksa şablondaki 17,5 W/m ya da gerçek ısı kaybı mı esas alınsın? 35 W/m kalırsa MMO yüzey sıcaklığı ve basınç kaybı sınırları aşılıyor ve modülasyon sayfasında negatif değerler çıkıyor."

Karar gelene kadar üretici esası değiştirmemeli.

## Engelleyici olmayan gözlemler (isteğe bağlı)
- Dar mahallerde etiketler küçültülmüş: devre etiketi ×0,85 (6 hol) ve ×0,7 (3 wc+banyo), mahal etiketi ×0,8 (3 adet). Yazı 7–8,5 cm; kullanıcının çiziminde her yerde 10 cm. Okunur, ama tarz farkı sayılır. Y-4 düzeltilirken mümkünse tam boya dönülmeli.
- Şema paneli: "PEX BORU, 16 x 2.0" yazısı ve hat etiketi kılavuzu ("/" yerine referanstaki "┐") küçük farklar. Panel taraması referanstan seyrek. Kabul edilebilir.
- Zon numaralandırma sırası referanstan farklı (D1'den başlıyor). Kural ET-5'e uygun, hata değil.

## Olumlu bulgular (değişmesin)
- 81 devrenin her biri tek açık LWPOLYLINE. Uç aralığı 15,0. En uzun devre 65,76 m (≤ 80), en kısa 11,99 m. Kesişme yok (T11 / denetle.py geçti).
- Isıtılmayan mahaller (balkon, wc-lvb, wc-duş, duş, asansör, merdiven, en. odası, zemin yüklükleri) boş. Mutfak tezgâhı, buzdolabı, klozet ve lavabo altı boş.
- Mimari yazı, ölçü ve tefriş duruyor. Katmanlar `ROTAS-` önekli. Sızıntı yok (T16). Pafta genişliği referansla aynı (T17).
- Etiket biçimi 150×80, 4 satır, okunur yönde. Mahal etiketi halkalı. Sıcaklıklar 20 / 15 / 24 °C.
- Teknik raporda W esası, ısıtılmayan mahaller ve sınırlar açıkça yazılı.

## Tur 3 kabul ölçütleri (kontrolör yeniden ölçecek)
1. Hiçbir yüklükte boru yok (Y01 FAIL = 0).
2. Y02 FAIL = 0: 4,37 m² ıslak hacimde mahal içinde ≥ 13,1 m, 5,36 m² banyoda ≥ 16,1 m. Vitrifiye ve Ç.M. altı boş.
3. Y05 FAIL = 0: her devre etiketi kendi devresinin üstünde, uç köşesinin yanında.
4. Hiçbir etiketin maskesi küvet, duş teknesi, Ç.M. veya diğer vitrifiyeyi gizlemiyor.
5. Geri kalan her şey bu turdaki gibi kalmalı (W esası K-1 cevabı gelene kadar değişmez).
