# sihhi2 — açılımlı kolon şeması, rögar şeması, yağmur şeması, temel planı

Kat planı üreticisinin (`plan.py`) yazdığı `sihhi_model.json` dosyasını okur. Şema, kullanıcının `new_block`
şemasındaki düzenle çizilir. Ölçüler `KOLON_SEMASI_TARZI.md` §3 ve `SIHHI_ALTIN_REFERANS.md` §5–6'dan alındı.
MTY bloğu kullanılmaz. Bütün semboller saf geometridir (`ROTAS-SEMA-*` / `ROTAS-TEMEL-*` blokları) ve bütün
katmanlar `ROTAS-` önekiyle başlar.

```
python3 motor/sihhi2/sema.py [--model YOL] [--cikis KLASOR] [--ad NB_SIHHI] [--kolon-birlestir] [--png]
python3 motor/sihhi2/sema_kontrol.py [--png-yok]      # T07/T08/T11 ölçümü + referansla yan yana PNG
```
Çıktılar (`proje/denemeler/sihhi2/`):
- `NB_SIHHI_SEMA.dxf`: kolon şeması, altında rögar şeması, sağında yağmur şeması, hesap kutusu ve lejant
  bulunur. Pafta x 260714'ten başlar. Bu, new_block'taki şema paftasının yeridir.
- `NB_SIHHI_TEMEL.dxf`: temel planı. Pafta 250042…252513 aralığındadır. Zemin kat koordinatı + `temel_ofset` (−2629).
- `NB_SIHHI_sema_ozet.json`: yığınlar, kolon x'leri, kat SB değerleri, daire MB/çap değerleri, rögar ataması ve
  çatı alanı (`pafta.py` bu dosyayı okuyabilir).
- `sema_png/*_YANYANA.png`: motor çıktısı ile referans kırpımı yan yana.

## Dosyalar
| Dosya | İş |
|---|---|
| `sema_ortak.py` | Modeli okur. Çap tablolarını tutar (plan.py ile aynı). Daire yığınlarını kurar ve yığınların, kolonların sırasını belirler. `kolon_birlestir` burada. |
| `sema_sembol.py` | Saf geometri bloklarını tanımlar: armatürler yan görünüşte (lavabo + ayna, gömme rezervuarlı klozet, duş, eviye, ÇM/BM, süzgeç, kombi). Ayrıca vana, pislik tutucu, sayaç, çek valf, T.K., havalık, rögar, balonlar ve öznitelikli etiketler (MB4/MB2/SB/iki satır/dikme) burada. |
| `sema.py` | Yerleşimi ve şema çizimini yapar (bant, sayaç grubu, depo, daire blokları, kolonlar, yağmur, rögar şeması, lejant). |
| `sema_temel.py` | Temel planını çizer: bina dış hattı ve betonarme (mimari2.Kat 'Z'), rögar kümeleme, Ø125/Ø150 hatlar. |
| `sema_kontrol.py` | Kontrolörün T07, T08 ve T11 testlerini şema ve temel paftasında çalıştırır, yan yana PNG üretir. |

## Yerleşim kuralları (birim cm; X0 = 260820 bant iç solu, Y0 = −443249 zemin döşemesi)
- Kat bandı 400 cm'dir. Her iki uçta 50 cm'lik kat yazısı sütunu vardır (h 25, 90°, kırmızı). Üst bant çizgisi çatıdır.
- **Yığın:** aynı plan konumundaki daireler bir yığındır (kombi konumu < 80 cm; örnek D3/D5/D8). Yığınlar soldan sağa
  kolon x ortalamasına göre artan sırada dizilir (D3, D2, D1). Yığın içinde ıslak hacim kolonları kuzeyden güneye
  dizilir, mutfak kolonları en sağda, kombinin yanındadır. Bu kural new_block'taki P9…P1 sırasını birebir verir.
- Daire dikmesi yığının solundadır, ilk kolonun 38 cm solunda, döşemeden +250'ye çıkar. Etiketi sola bakan kancayla
  +125'tedir (`1 1/4" / 9.5 MB`).
- +250 soğuk hattı ve +245 sıcak hattı kullanılır. Her grup kolon+24 (soğuk) ve kolon+29 (sıcak) noktasından iner.
  Dağıtım +130 (soğuk) ve +135 (sıcak) kotundadır.
- Sıcak su yalnız kombiden başlar. Kombi yığının sağ ucundadır (+175); gerekirse son kolon + 300'e kaydırılır.
  Mutfak grubunda sıcak hat +135'ten sola akar ve kolon+29'da +245'e çıkar.
- Armatürler kolondan 154 cm, birbirlerinden 130 cm uzaktadır. Sıra modeldeki `armatur_sirasi_sema` listesine
  göredir (kolondan dışa). Branşmanlar sıcakta x−5, soğukta x+5 noktasındadır. Armatür etiketi `Ø20 / 0.75 MB`
  biçimindedir.
- Hat etiketi armatürün 80 cm solundadır. Kanca yukarı bakar. Etiket 4 satırdır (`1" / 5.25 MB / 1" / 3.25 MB`);
  yalnız bir hat varsa 2 satırdır. Her hat parçasında tek etiket bulunur. Üst hat etiketi her iki iniş arasındaki
  parçaya konur.
- **Pis su:** iniş döşemeden −35'e iner, 45° çatalla toplayıcıya bağlanır. Toplayıcı −50 kotundadır ve kolona 45°
  ile girer. Borular PVC görünümündedir: çift dış hat (43) ve muf halkaları. İniş etiketi `Ø50 / 2 SB`, inişin sağındadır.
  Toplayıcı etiketi armatürün 80 cm solundadır, kümülatif değeri gösterir ve kancası hatta iner.
- **Kolon:** kat bağlantısının altında, kolonun solunda kolon etiketi vardır (o kattan aşağı kümülatif SB; zemin
  etiketi kolon toplamıdır). T.K. zemin +24'tedir. Dipte −88'de 45° dirsek, ok ve "R" bulunur. Üstte havalık
  şapkası (+28) ve P balonu (+80) vardır.
- **Daire balonu:** r 55, h 40. Konumu kombi −197, döşeme +268'dir.
- **Şebeke ve sayaç grubu:** yalnız zemin bandının solundadır. "Şebekeden" yazısı vardır. Giriş hattı +15
  kotundadır: vana – pislik tutucu – çek valf – vana. Bunun ardından depo dolum dikmesi gelir (X0+125). Dolum ile dönüş
  dikmesi arasında by-pass çek valf vardır. Dağıtım dikmesi X0+158'dedir. Kollektörler X0+173 ve +161'er aralıktadır.
  Her kollektörde 5 sıra bulunur, sıra aralığı 20'dir. Bir sıranın dizilimi: vana(27) – pislik tutucu(52) – sayaç(74) –
  çek valf(96) – vana(121), uç tırnağı 148'de. **Kat bantlarında ve dairelerde sayaç yoktur.**
- **Depo:** çatıdadır, X0+285, 200×200, 30 cm taralı kaide üzerinde. Havalık, taşma 2", boşaltma (vanalı, huni),
  seviye göstergesi ve şamandıralı dolum (vana) bulunur. Çıkışta vana ve pislik tutucu vardır. Dikmelerde her
  katta akış oku konur.
- **Yağmur şeması:** x1+86+60·i konumunda, −20 ile üst+10 arasında uzanır. Balon üst+37,5'tedir. Her katta +170'te
  Ø70 işareti ve dipte deşarj oku vardır. Altında "YAĞMUR SUYU KANALINA GİDER" kutusu ve 500×280 hesap kutusu bulunur.
  Hesap: bina alanı / iniş sayısı × 0,03 l/s·m². Kapasite TS EN 12056-3 Wyly-Eaton denklemiyle bulunur
  (f = 0,33, di 66 mm).
- **Rögar şeması:** Y0−600'de, şema ortasına ortalanır. Rögar kutusu 89×64 ve altında 89×32 kesit kutusu vardır.
  Rögarlar arası 239 cm'dir. Aradaki hatta `%1 EĞİM / Ø150` (h 18) ve ok bulunur. Üstte 50 cm kılavuz ve P
  balonları vardır (yan yana 2'li, 55 aralıklı). "70x70 / h:-70cm" yazısı konur. Son kutu PB'dir. Başlık yoktur.

## Temel planı
- Bina dış hattı mimariden alınır (`mimari2.Kat('Z')`). Balkonsuz mahaller ve onlara 40 cm içindeki duvar katısı
  birleştirilir, dış kontur alınır. Betonarme olarak taramalı kolon ve perde poligonları kullanılır.
  Önbellek: `/tmp/claude-0/s2/temel_mimari_v3.pkl`.
- Rögarlar doğu cephesinin 110 cm dışındadır. Kolonlar kuzeyden güneye 1B DP ile kümelenir. Maliyet, iniş boyları
  ile rögar başına 350 cezanın toplamıdır; bir kümenin yayılımı en çok 520 cm olabilir. Ortak yatay hattı ya da
  inişi betonarmeye veya başka kümenin kolonuna değen küme olanaksız sayılır. Hat y'si medyana en yakın serbest
  y'dir (±300).
- Kolondan gelen hat Ø125 %1'dir. Batıdaki ilk kolonun L köşesinde 5 cm 45° pah vardır. Diğer kolonlar T ile
  bağlanır. Her 150 cm'den uzun parçaya `%1 EĞİM / Ø125` etiketi ve ok konur. Rögarlar arası Ø150 %1'dir (etiket 90°).
  PB son rögarın 506 cm doğusundadır.
- P balonları 55–120 cm içinde boş bir yere konur; gerekirse kılavuz çizilir.

## Kontrol (15.10.2026)
`sema_kontrol.py`: ŞEMA'da T07 PASS (1213 etiket; etiket–etiket 0, etiket–hat 0), T08 PASS, T11 PASS (MTY 0,
önek 0, köprü 0, kesişme 0, yazı 0, lejant, audit 0). TEMEL'de T07 PASS ve T11 PASS.
- `kontrolor.py` kat testlerini (T01–T06, T09, T10) yalnız kat paftasında anlamlı biçimde çalıştırır. Bu testlerin
  şema dosyasındaki sonucu dikkate alınmaz: örneğin T09 "süzgeç 0" bulgusu verir, çünkü dosyada plan yoktur.
  Kontrolör T07'yi şema paftasında ölçmez. Bu yüzden `sema_kontrol.py` T07'yi şema ve temel çerçevesiyle ayrıca çağırır.
- Kesişme 0 sonucunun nedeni: boru parçaları iniş ve branşman ağızlarında bölünür (her hat parçası ayrı varlıktır
  ve her parçada bir etiket vardır). Sıcak branşmanın soğuk dağıtım hattını kestiği yer, soğuk ağzından 10 cm
  uzaktadır. Denetimde bu bağlantı olarak sayılır (UC_TOL 15). Aynı geçiş kullanıcının şemasında da vardır;
  SIHHI_ALTIN §10 kural 12'ye göre "branşmanın eş hattı kesmesi serbest"tir.

## Bilinen farklar ve sınırlar
- Şema genişliği modeldeki kolon sayısına bağlıdır. new_block'taki 9 kolon için 6629 cm'dir; modelde fazladan kolon
  varsa pafta uzar. Katlarda aynı düşeyde, farklı numaralı kolon üreten plan çıktısı için `--kolon-birlestir`
  kullanılabilir (≤ 30 cm ve katları ayrık kolonlar birleşir). Bu seçenek kapalıdır, çünkü şemadaki numaralar
  plandakilerle aynı kalmalıdır.
- Kolon etiketleri, o kattan aşağıya kümülatif SB'yi gösterir; zemin etiketi kolon toplamıdır. Kullanıcının
  şemasında her kattaki kolon etiketi o katın değerini gösteriyor.
- `ornek_model.json` yazılmadı: `sihhi_model.json` mevcuttu. Dosya yoksa `model_oku` bu yolu dener.
