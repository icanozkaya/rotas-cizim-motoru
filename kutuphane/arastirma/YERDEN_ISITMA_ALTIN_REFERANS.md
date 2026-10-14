# YERDEN ISITMA — ALTIN REFERANS (kullanıcının KENDİ çizimi, `ornekler/new_block.dxf`)

Kaynak: `ornekler/new_block.dxf.xz` (Metra Mimarlık, Tekeler 4739/4, Z+2, 9 daire), model uzayında **ISITMA TESİSATI PROJESİ** seti
(x ≈ 272 600 … 288 111, y ≈ −444 050 … −441 150; birim **cm**, 1/50). Bütün sayılar DXF'ten ezdxf ile ölçüldü (14.10.2026).
Kırpılmış görüntüler: `kutuphane/arastirma/referans/yerden/01…15_*.png`.

> Bu belge motorun (`motor/yerden2/`) TEK tarz referansıdır. Çıktı bu çizimle yan yana konduğunda aynı görünmelidir.
> Belgenin sonundaki "MOTOR İÇİN KURAL LİSTESİ" test edilebilir biçimde yazılmıştır.

---

## 1. Pafta dizilimi (ısıtma seti, soldan sağa)

| Sıra | İçerik | x başlangıcı (cm) | Not |
|---|---|---|---|
| 1 | ROTAŞ anteti, "ISITMA TESİSATI PROJESİ" (h 25) | 272 611 | Sıhhi antetle birebir aynı, yalnız başlık farklı |
| 2 | YERLEŞİM PLANI ÖLÇEK 1/250 + vaziyet + proje bilgi kutusu | 273 722 | Sıhhideki ile aynı |
| 3 | ZEMİN KAT PLANI..........ÖLÇEK: 1 / 50 (yerden ısıtma) | 275 300 | başlık h 40, plan altında, y = −444 011 |
| 4 | 1. KAT PLANI (yerden ısıtma) | +2 078 | plan–plan adım ≈ **2 080 cm** (bina ≈ 1 950 + boşluk) |
| 5 | 2. KAT PLANI (yerden ısıtma) | +2 086 | |
| 6 | Yerden ısıtma kolon şeması (tek geniş pafta) | 281 418 … 288 111 | çerçeve **6 693 × 2 900 cm** (ANTED katmanı) |

Isıtma setinde **temel planı ve çatı planı YOK**; her katın yerden ısıtma planı ayrı pafta; sonda kolon şeması.
Kat planlarında mimari (MKDU0 katmanı: duvar, kapı, pencere, tefriş, vitrifiye, mahal adı + m², kapı/pencere ölçüleri, "kombi" yazısı,
"yağmur inişi") **hiç silinmeden** kopyalanır; üstüne yalnız serpantinler + 2 etiket bloğu eklenir.

## 2. Katmanlar / renkler / kalınlıklar (ölçülen)

| Katman | Renk (ACI) | Kalınlık | Çizgi tipi | Kullanım |
|---|---|---|---|---|
| `MTY-PEX-BORU` | 1 (kırmızı) | lw 30 (0,30 mm) | CONTINUOUS | plandaki serpantin (LWPOLYLINE, const_width 0, renk BYLAYER) |
| `MTY-VANA` | 1 | lw 30 | — | **etiket blokları** (MTY-ETIKET, MTY-RADYATOR MAHAL) ve şema blokları bu katmanda INSERT |
| `MTY-RADYATÖR` | 2 (sarı) | default | — | blok içi tablo çizgileri/yazıları (BYLAYER → sarı) |
| `MTY-ISIKAYBIMAHAL` | 2 | default | — | mahal etiketi blok içi (cyan 4 ve kırmızı 1 renkler blok içinde sabit) |
| `MTY-ISITMA-GIDIS-BORU` | 10 (kırmızı) | lw 0 | CONTINUOUS | şema gidiş hatları |
| `MTY-ISITMA-DONUS-BORU` | 30 (turuncu) | lw 0 | `ISITMA DONUS HATTI` (uzun çizgi–nokta: 1,57 / −0,02 / −0,07, desen boyu 1,66; LTSCALE 1) | şema dönüş hatları |
| `MTY-ISITMA-CAP` | 41 (açık turuncu) | default | — | şema hat etiketleri "W-Ø" |
| `MTY-BORU` | 7 | default | — | şema kat bantları ve "ZEMİN. KAT" yazıları (renk 1 ile) |
| `MKDU0` | 50 | — | — | mimari (dokunulmaz) |
| Yazı stili | `MTYCAPLT` = arial.ttf, öznitelik genişlik çarpanı 0,65 | | | |

## 3. Plan: serpantin geometrisi (her sayı DXF'ten)

### 3.1 Boru aralığı ve dönüş
- **Boru aralığı (pitch) = 15,0 cm** her devrede (etikette "Modülasyon Aralığı: 15.0"). 24 °C banyoda da 15 (10'a inilmemiş).
- **U dönüşü**: iki adet 90° yay, **r = 7 cm**, aralarında **1 cm düz** parça → 7 + 1 + 7 = 15. Bulge = ±0,4142 (tan 22,5°). Köşe hiç keskin değil.
- Boru: "PEX BORU, 16 x 2.0" (etikette gizli öznitelik, şemada görünür).

### 3.2 Meander (gidiş-dönüş paralel) düzeni — **salyangoz DEĞİL**
- 81 devrenin **81'inde parmaklar (uzun paralel hatlar) plan X eksenine paralel (yatay)**; mahalin uzun/kısa kenarına bakılmaz
  (Z05 4,1×3,3 → yatay; Z04 2,5×3,3 → yatay; Z06 hol 7,1×1,1 → yatay; Z02 salon 4,0×4,7 → yatay). Besleme ("ayak") hattı daima **dikey**.
- Polyline yapısı (devre 0 / Z09 örneği): `uç A (x_f, y_u)` → **dikey besleme hattı** duvar boyunca (337 cm) → ilk parmak →
  … meander yukarı/aşağı … → son parmak **uç B (x_f + 15, y_u)**. Yani iki uç aynı y'de, **15 cm aralıkla, mahal köşesinde**.
- Besleme hattı, parmak dönüş tepelerinden **15 cm dışarıda** (x_f = ilk dönüş tepe çizgisi − 15). Böylece hiçbir çizgi kesişmez.
- Her devre **tek LWPOLYLINE** (açık, 33–150 köşe), hiçbir yerde kesilmez; etiket altından aynen geçer (**WIPEOUT yok**, dosyada hiç wipeout yok).

### 3.3 Kenar mesafesi (duvar iç yüzü → ilk boru ekseni)
| Yön | Ölçülen | Yorum |
|---|---|---|
| Parmak uçları (dönüş tepeleri → yan duvar) | **7,5 cm** (27 devrenin 20'sinde tam 7,5; diğerleri 5,5–12,5) | pitch/2 |
| Besleme hattı → duvar | 7,5 cm (yan duvarda hattın kendisi en dışta) veya 12,5–18,7 (kolon/kapı sıvası varsa) | |
| İlk/son parmak → üst/alt duvar (parmaklara dik yön) | **0 – 7,5 cm** (Z05: 1 ve 0; Z04: 4,5 ve 0; Z13 hol: 7,5/7,5; Z02 alt: 30 çünkü kapı+kolon) | Kullanıcı sınırı elle seçmiş; **motor için 7,5 cm standart** |
| İki devreli mahalde devreler arası | alt devrenin besleme hattı üst devrenin besleme hattından **30 cm içeride**; parmak sıraları arasında normal 15 | |

### 3.4 Mahal / tefriş kuralları (ölçülen)
- **Isıtılan**: salon, yatak odası, oda, mutfak, banyo / wc+banyo (24 °C), **antre-koridor (15 °C, her dairede ayrı devre)**.
- **Isıtılmayan**: balkon, yüklük, wc-lvb. (dar 1,9 m² WC), duş (üst daire D3'teki duş kabini mahali), asansör, merdiven, en. odası, bina girişi.
- **Mutfak**: tezgah (evye+ocak bandı) ve buzdolabı altına boru girmez; parmaklar tezgah önünde biter, buzdolabı yanında kısalır (`03_mutfak_Z01…png`).
- **Banyo**: klozet ve lavabo altına girilmez (Z07), duş teknesi/küvet kısmen örtülür (Z14) → motor: vitrifiye poligonları hariç.
- **Hol**: kapı önleri dâhil tamamı kaplanır; L biçimli holde tek polyline, parmak boyları değişerek L'yi doldurur (`07_hol_L_Z13…png`).
- **Kapı süpürme alanı hariç tutulmaz** (Z05, Z02: parmaklar kapı önünden geçer).
- Mahal yazıları, m², kapı/pencere ölçüleri, "kombi" yazısı, tefriş **aynen durur**.

### 3.5 Devre bölme ve uzunluklar (zemin kat, D1+D2+D3, 27 devre)
| Mahal | m² | Devre | Hat uzunluğu (etiket) | Ölçülen polyline (yaylı) | W (etiket) |
|---|---|---|---|---|---|
| Z01 mutfak | 10,11 | 1 | 39,19 m | 40,69 | 1371,8 |
| Z05 yatak od. | 15,44 | 4 + 2 | 53,37 + 46,46 | 53,37 / 46,46 | 1867,9 + 1626,1 |
| Z04 yatak od. | 9,05 | 5 | 56,90 | 56,90 | 1991,4 |
| Z03 oda | 7,75 | 6 | 56,90 (*) | 46,80 | 1991,4 |
| Z02 salon | 22,31 | 8 + 7 | 69,99 + 60,48 | ✓ | 2449,6 + 2116,8 |
| Z06 antre-kor. 15 °C | 11,00 | 9 | 57,41 | ✓ | 2009,3 |
| Z07 wc+banyo 24 °C | 4,37 | 10 | 13,80 | ✓ | 483,0 |
| Z12 yatak od. | 14,25 | 11 + 12 | 47,56 + 41,75 | ✓ | 1664,6 + 1461,2 |
| Z11 / Z10 yatak od. | 9,31 | 13 / 14 | 56,24 / 57,21 | ✓ | 1968,3 / 2002,3 |
| Z09 salon | 21,18 | 15 + 16 | 66,26 + 61,99 | ✓ | 2319,1 + 2169,8 |
| Z08 mutfak | 11,07 | 17 | 50,62 | ✓ | 1771,5 |
| Z13 antre-kor. (L) 15 °C | 7,77 | 18 | 46,44 | ✓ | 1625,5 |
| Z14 banyo 24 °C | 5,36 | 19 | 23,53 | ✓ | 823,6 |
| D2 (ayna) Z15–Z21 | | 20–28 | D1 ile aynı değerler | | |

(*) Z03 etiketi Z04'ten kopyalanmış (kullanıcı hatası); motor kendi ölçtüğü uzunluğu yazar.
- **Hat uzunluğu = plandaki polyline'ın yaylar dâhil gerçek uzunluğu** (kollektöre giden ayak eklenmemiş; planda ayak çizili değil).
- **W = 35,0 W/m × hat uzunluğu** (bütün devrelerde tam 35,0: 1867,9/53,37; 483,0/13,80; 2449,6/69,99). Isı kaybı hesabından değil, boru boyundan.
- **En uzun devre 69,99 m** → kullanıcının "devre ≤ 80 m" kuralı sağlanır; 15,44 m² ve üstü odalar (≈ > 65–70 m boru) **2 devreye** bölünür;
  bölme çizgisi parmaklara paralel (üst yarı / alt yarı), iki devrenin uçları aynı köşede.
- Devre numarası kat içinde 1'den başlar, daire sırasına göre artar (zeminde 1–28, biri atlanmış); zon kodu: zemin `Z01…Z21`, 1. kat `101…121`, 2. kat `201…221`.
  İki devreli mahalde her iki devre aynı zon kodunu taşır.
- Boru/alan oranı ≈ 6,5 m/m² (Z05: 99,8 m / 15,44 m²).

### 3.6 Uçların (ayak başlangıcının) konumu
- Uçlar daima mahalin **bir köşesinde** (WS/ES/EN/WN), besleme hattı o köşeden duvar boyunca uzar.
- Zemin D1: Z01 mutfak → kapının hemen yanı (WS); Z02 salon → kapı köşesi (WS); Z05 → WS (kapı aynı duvarda, öbür uçta);
  Z04 → ES (kapı aynı duvarda sol uçta); Z03 → EN; Z07 → EN (kapı yanı). Yani tutarlı bir "kapıya en yakın köşe" kuralı **yok** —
  kullanıcı MTY'de köşeyi elle seçmiş. **Motor kuralı: kapıya en yakın köşe** (hol tarafı), D2 aynalı dairede aynadaki köşe.
- **Planda kollektör, kombi sembolü ve kollektöre giden ayak hatları ÇİZİLMEMİŞ**; mutfaktaki "kombi" yazısı mimardan gelir.
  Kombi–kollektör–devre bağlantısı yalnız kolon şemasında gösterilir. (README'deki "ayaklar holden/kapıdan" kuralı ET projesinden; bu referansta ayak yok.
  Motor ayak çizecekse: yalnız kendi dairesinin holünden + kapıdan, hiçbir serpantini kesmeden, 15 cm paralel çift; çizmeyecekse referans gibi uçlar köşede biter.)

## 4. Plan: etiketler (blok, boy, konum)

### 4.1 Devre etiketi — blok `MTY-ETIKET` (katman MTY-VANA, 81 adet)
- INSERT: `xscale −10, yscale 10, rotation 180` → net dönüşüm **x' = ins.x + 10·u, y' = ins.y − 10·v** (y aynalı; sabit yazılar AutoCAD dışı
  görüntüleyicide ters çıkar, öznitelikler düz). Motor aynı görünümü **scale 10, rot 0** ile ve blok y'sini ters tanımlayarak üretir.
- Görünen kısım: **sarı tablo 150 × 80 cm**, ins noktasından aşağı (ins = tablonun üst kenarı, sol kenardan 70 cm sağda):
  sol sütun 96,9 cm (ins.x−70 … ins.x+26,9), sağ sütun 53,1 cm (… ins.x+80); 4 satır × 20 cm. Çizgiler BYLAYER (sarı), ince.
- Satırlar (yukarıdan): `Hat uzunluğu:` | `53.37 m` — `Modülasyon Aralığı:` | `15.0` — `Kcal/h:` | `1867.9 W` — `Isıtma Devresi-No.:` | `4`.
- Yazı: h **10 cm**, MTYCAPLT, genişlik 0,65, sarı. Etiket yazıları sol sütunda ins.x−65'ten; değerler: UZ (ins.x+42,8, ins.y−14,9), AR (+57,8, −34,9),
  YER (+28,0, −54,9), NO1 (+70 ±5, −75) → sağ sütunda **sağa yaslı** görünüm.
- Gizli (invisible=1) alt kısım: kırmızı 150×85 kutu + MAHAL/NO (Z05)/DERECE (20°C)/Kcal/ALAN/MALZEMECINSI öznitelikleri; BORU_001 = "PEX BORU, 16 x 2.0" gizli. Çizilmez.
- **Konum**: devrenin uç (besleme) tarafındaki köşeye yakın, **mahal içinde**: tablo sol kenarı = devre bbox sol + 8…10 cm (D1), tablo üstü = devre bbox üst − 30…65 cm.
  İki devreli mahalde iki tablo **aynı x hizasında alt alta** (Z05: üst devre üstten 60, alt devre kendi üstünden 30). Aynalı dairede sağ tarafta.
  Tablo serpantin üstüne biner (maske yok); referansta banyo etiketi m² yazısına da binmiş (`07_…png`) → motor: mimari yazıya binmez (README).

### 4.2 Mahal etiketi — blok `MTY-RADYATOR MAHAL` (katman MTY-VANA, 63 adet = ısıtılan mahal sayısı)
- INSERT: `xscale −1, yscale 1, rotation 180` → x' = ins.x + u, y' = ins.y − v. Motor: scale 1, rot 0, y ters.
- Geometri: yuvarlatılmış dikdörtgen **68,4 × 48,9 cm** (±34,21 × ±24,44), köşe yayı r ≈ 6; dışına 0,5 cm adımla 3 halka daha (69,4×49,9 / 70,4×50,9 / 71,4×51,9):
  renk sırası içten dışa **sarı(2) – cyan(4) – cyan(4) – sarı(2)**; ortada sarı dolu şerit 56,4 × 1,5 cm (y = 0).
- Öznitelikler h **12 cm**: `DERECE_001` "20%%DC" **cyan (4)**, ins'e göre (−12,1; +6,5) → şeridin üstünde ortalı; `NO_001` "Z05" **kırmızı (1)**, (−9,3; −18,6) → şeridin altında ortalı.
  MAHAL, ISIKAYBI, ALAN boş.
- **Konum**: mahalin **üst yarısı, orta/üst-orta**: Z05 (%57 x, %22 y), Z04 (%51, %6), Z09 (%56, %16), Z02 (%32, %18), Z01 mutfak (%60, %43 — "mutfak" yazısının üstüne binmiş),
  hol Z06 (%39, %54), hol Z13 (%19, %67). Çoğunda mahal adı MTEXT'inin 60–120 cm üstünde/solunda. Serpantin üstüne biner, maske yok.
  Motor: mahal adının üstünde ortalı, mimari yazıya ve devre etiketine binmeden.
- Sıcaklıklar: oda/salon/mutfak **20 °C**, hol **15 °C**, banyo **24 °C**.

## 5. Kolon şeması (x 281 418 … 288 111)

### 5.1 Bantlar
- Çerçeve ANTED: 6 693 × 2 900. Bant çerçeveleri `MTY-BORU` polyline: iç alan **x 281 532,4 … 288 022,6 (6 490 cm)**, her bant **400 cm** yüksek:
  ZEMİN −443 201,6 … −442 801,6; 1. KAT … −442 401,6; 2. KAT … −442 001,6. Bant alt çizgisi = o katın **döşeme çizgisi**.
- Sol etiket sütunu **50 cm** (281 482,4 … 281 532,4), içinde dikey (90°) kırmızı yazı h **25**: "ZEMİN. KAT", "1. KAT", "2. KAT" (bant ortasında).
- Bantlarda aşağıdan yukarı: zemin, 1, 2 (dairelerde D3-D2-D1 soldan sağa zeminde; D6-D5-D4; D9-D8-D7).

### 5.2 Daire bloğu (her kat 3 daire, blok genişliği ≈ 2 144 cm; daire adımı 2 144 / 2 129)
Daire bloğu referans noktası = kombi+kollektör bloğu (`*U127`, 1:1) insert'i, **döşeme çizgisi üstünde**, bant iç sol kenarından **146 cm** (281 678,5). İçerik, bu noktaya göre:
| Öğe | Konum (dx, dy cm) | Ölçü / yazı |
|---|---|---|
| Kombi (sarı dikdörtgen ≈ 51 × 102 cm, alt şeridinde 4 bağlantı dairesi) | (−92…−41, 118…220) | *U127 bbox −110…+150 × −25…+220 |
| "H. KOMBİ 24KW" | (33, 195) | h **20**, cyan (4), öznitelik |
| Daire etiketi `MTY-KOLON NO PIS SU` ×2 | (277,4; 213,6) | çift daire r 55/49 (mor 6 / beyaz 7), "D3" h **40** mor; D1…D9 |
| Kollektör dolabı (kırmızı kutu ≈ 123 × 60, içinde gidiş üst / dönüş alt manifold, devre sayısı kadar ağız, iki küresel vana) | kutu ≈ (−23…+100, 10…70) | ağız adımı **10 cm**; gidiş–dönüş ağız çifti 5 cm; ağızlar döşeme altına iner |
| Kombi→kollektör gidiş (kırmızı, sürekli) / dönüş (turuncu çizgi-nokta, üzerinde vana) | kombi altından kollektör sol yanına | |
| Kollektör toplam etiketi `*U111` | (0, 70) | "15907.3W-Ø32" (= daire devre W toplamı), h 10, renk 41, sola kısa kılavuz |
| 1. devre paneli `*U108` | (290, 0) | sonrakiler **+200 cm** adımla; panel bbox −20…+129 × −17…+120 |

### 5.3 Devre paneli `*U108` (döşeme kesiti sembolü, 1:1, döşeme çizgisine oturur)
- Sol duvar kesiti 10 cm (AR-CONC tarama), şap 10…124 cm × 0…20 (taralı), üstte döşeme çizgisi (−20…129, y 55/60).
- Boru ilmeği: gidiş (kırmızı) y 50'de 0→114, sağda 119'dan 45→30 iner, dönüş (turuncu) y 25'te 114→5, sol alt 0'dan 10→20 çıkar; yuvarlatılmış köşeler.
- Öznitelikler: `NO_001` "Z07" h **15** sarı (1,3; 31,9) ilmek içinde sol; `DERECE_001` "24%%DC" h 10 (94,4; 33,7) ilmek içinde sağ;
  `YER_001` "483.0 W" (15; 70); `UZ_001` "13.80 m" (62; 70); `ISIKAYBI_001` (14; 110) boş kalmış ("ISIKAYBI" yazar); `NO1_001` devre no (85; 110); `BORU_001` "PEX BORU, 16 x 2.0" (4,3; −14) panel altında.
- Panel sırası soldan sağa: daire devre numaraları **büyükten küçüğe** (10, 9, 8 … 1): en uzak devre kollektöre en yakın.

### 5.4 Şema hatları (her devre 4 köşeli LWPOLYLINE, gidiş + dönüş)
Devre i (0 = ilk panel), panel x = Px, döşeme y = Y0, kollektör ref x = Kx:
- **Gidiş** (MTY-ISITMA-GIDIS-BORU): (Px−5, Y0+57,5) ↓ (Px−5, Y0−20−10i) ← (Kx+85−10i, …) ↑ (Kx+85−10i, Y0+20).
- **Dönüş** (MTY-ISITMA-DONUS-BORU): (Px, Y0+22,5) ↓ (Px, Y0−25−10i) ← (Kx+80−10i, …) ↑ (Kx+80−10i, Y0+20).
- Yani döşeme altında yatay hatlar **5 cm aralıkla** gidiş/dönüş çiftleri, çiftler arası 10 cm; en uzak devre en altta (zeminde −20…−105 cm). Hatlar birbirini **kesmez**.
- Hat etiketi `*U110` (scale 10): gidiş dikeyinin döşeme altındaki köşesinde, (Px−15, Y0−20−10i), yazı sola **"2009.3W-Ø20"** h 10, renk 41, kısa "L" kılavuz.
  Tüm devreler **Ø20**, kombi–kollektör **Ø32**.

## 6. Hesap şablonu (`sablon/ornek_yi.xlsx`) ile ilişki
- Sayfalar: kapak, TEKNİK RAPOR (1-2), ZEMİN / 1 NK (ısı kaybı, Q17 sütunu), PETEK LİST, **YERDEN ISITMA** (modülasyon), **MMO YERDEN ISITMA**, YERDEN ISITMA- DEVAMI.
- YERDEN ISITMA: `F = D/E` (W/m²), `G = 76.263 − 0.539·F` (modül), `H = D/G`, `J = boru boyu` (PETEK LİST G), `K = J/80` (kollektör adedi — **80 m/devre**), `L = CEILING(K,1)`, `M = 17.5 W/m`, `N = J·M`.
- MMO: `q" = qh/A`, `Ty = Th1 + (q"/8.92)^0.91`, Tsg 50, Lr boru aralığı "kat planından", `Lç = A/Lr`, `m = q/(1.163·ΔTsg)`, ΔPs tablo, Δpö = 0.05·ΔPs, Δpmax 9828 Pa.
- Çizimdeki "Kcal/h: … W" (35 W/m × L) ile şablondaki 17,5 W/m farklıdır; motor Excel'de kullanıcı şablonunun formüllerini bozmadan **hat uzunluğunu** girer, W'yi şablon üretir;
  planda etikete yazılacak W için referans davranış (35 W/m × L) kullanılır ve raporda belirtilir. Şablondaki "dcmmakina" logosu/adı temizlenir.

---

## 7. MOTOR İÇİN KURAL LİSTESİ (test edilebilir)

**Plan — serpantin**
1. `PEX-1` Her devre tek açık LWPOLYLINE, katman `ROTAS-PEX-BORU` (renk 1, lw 30, const_width 0); kesilmez, patlatılmaz. Test: polyline sayısı = devre sayısı; etiket sayısı = polyline sayısı.
2. `PEX-2` Pitch 15,0 cm (ΔT ≥ 24 °C banyoda da 15; 10 yalnız kullanıcı isterse). Test: ardışık paralel parmak eksenleri 15,0 ± 0,1.
3. `PEX-3` Dönüş = 90° yay r 7 + 1 cm düz + 90° yay r 7 (bulge 0,4142). Test: köşe bulge'ları |0,4142|, yay yarıçapı 7.
4. `PEX-4` Parmaklar plan X eksenine paralel; besleme hattı dikey, ilk dönüş tepesinin 15 cm dışında. Test: uzun segmentlerin %100'ü yatay.
5. `PEX-5` İki uç aynı köşede, 15 cm aralıkla, mahal köşesinde (kapıya en yakın köşe). Test: |uçA−uçB| = 15 ± 0,1; uç, mahal poligon köşesine ≤ 30 cm.
6. `PEX-6` Kenar mesafesi: boru ekseni duvar iç yüzüne 7,5 cm (parmak uçları, ilk/son parmak, besleme hattı). Test: 5 ≤ d ≤ 12,5.
7. `PEX-7` Devre uzunluğu (yaylı polyline) ≤ 70 m hedef, kesinlikle ≤ 80 m; aşan mahal parmaklara paralel 2'ye bölünür; alt devrenin besleme hattı üst devreninkinden 30 cm içeride, uçlar aynı köşede. Test: her L ≤ 80; bölünmüş devre uçları arası x farkı 30.
8. `PEX-8` Hiçbir iki devre / çizgi kesişmez ve üst üste binmez (shapely crosses = False, min mesafe ≥ 10 cm; besleme hattı–parmak 15).
9. `PEX-9` Isıtılan: salon, oda, yatak odası, mutfak, banyo/wc+banyo (24), antre-koridor (15); ısıtılmayan: balkon, yüklük, wc-lvb ≤ 2 m², duş kabini, asansör, merdiven, ortak alan. Test: ısıtılmayan mahal poligonunda PEX yok.
10. `PEX-10` Mutfak tezgah + buzdolabı, klozet, lavabo, duş teknesi poligonları hariç tutulur (parmak uçları onlardan 7,5 cm uzakta); kapı süpürme alanı hariç tutulmaz; L mahal tek polyline. Test: PEX ∩ tefriş poligonu = ∅.
11. `PEX-11` Mimari (MKDU0) olduğu gibi kalır: mahal adı, m², kapı/pencere ölçüleri, tefriş, "kombi" yazısı. Test: ısıtma paftasındaki MKDU0 varlık sayısı = sıhhi paftadaki.
12. `PEX-12` Planda kollektör/kombi sembolü ve ayak çizilmez (referans davranışı). Ayak istenirse: 15 cm paralel çift, yalnız hol + kapı, hiçbir serpantini kesmez.

**Plan — etiketler**
13. `ET-1` Devre etiketi: 150×80 sarı tablo, 4 satır × 20, sütun 96,9/53,1, yazı h 10 (genişlik 0,65), satırlar "Hat uzunluğu: | NN.NN m", "Modülasyon Aralığı: | 15.0", "Kcal/h: | NNNN.N W", "Isıtma Devresi-No.: | n"; değerler sağ sütunda sağa yaslı. Blok adı `MTY-ETIKET`, scale 10, rot 0 (okunur yazı).
14. `ET-2` Hat uzunluğu = polyline'ın yaylı gerçek uzunluğu (2 ondalık); W = 35,0 × L (1 ondalık) [ya da Excel'den gelen değer — teslimde hangisiyse rapora yazılır].
15. `ET-3` Devre etiketi mahal içinde, uç köşesine yakın: tablo sol kenarı = devre bbox kenarı + 10, üstü = bbox üstü − 30…60; iki devreli mahalde aynı x'te alt alta; aynalı dairede aynalı.
16. `ET-4` Mahal etiketi: 68,4×48,9 yuvarlatılmış kutu + 3 halka (sarı-cyan-cyan-sarı), orta şerit 56,4×1,5; "20°C" cyan h 12 üstte, "Z05" kırmızı h 12 altta; blok `MTY-RADYATOR MAHAL` scale 1; mahalin üst yarısında, mahal adı MTEXT'inin üstünde ortalı. Her ısıtılan mahalde 1 adet (iki devreli mahalde de 1).
17. `ET-5` Zon kodu: zemin Z01…, 1. kat 101…, 2. kat 201…; devre no kat içinde 1'den; iki devreli mahalde aynı zon, farklı devre no. Sıcaklık: oda/salon/mutfak 20, hol 15, banyo 24.
18. `ET-6` Etiketler mimari yazıya, birbirine ve başka etikete binmez (README; referanstan daha sıkı); serpantin üstüne gelebilir, maske istenirse WIPEOUT.

**Kolon şeması**
19. `S-1` Bantlar 400 cm yüksek, iç genişlik 6 490, sol 50 cm etiket sütununda dikey kırmızı h 25 "ZEMİN. KAT / 1. KAT / 2. KAT"; bant altı = döşeme çizgisi; kat sırası aşağıdan yukarı. Çerçeve 6 693 × 2 900.
20. `S-2` Her daire: kombi+kollektör bloğu döşeme üstünde, bant solundan 146 (+ önceki daire genişliği), "H. KOMBİ 24KW" cyan h 20 (33,195); daire etiketi çift daire r 55/49 mor, "Dn" mor h 40, (277; 214); kollektör toplam etiketi "ΣW W-Ø32" (0; 70).
21. `S-3` Devre panelleri 1:1 `*U108` geometrisiyle (duvar kesiti + şap + yuvarlak ilmek), ilk panel ref+290, adım 200; içinde "Zxx" h 15 sarı sol, "20°C" h 10 sağ; üstte "W" (15;70) ve "m" (62;70), devre no (85;110); altta "PEX BORU, 16 x 2.0". Panel sırası devre no büyükten küçüğe.
22. `S-4` Gidiş: (Px−5, Y0+57,5)→(Px−5, Y0−20−10i)→(Kx+85−10i, …)→(…, Y0+20); dönüş: (Px, Y0+22,5)→(Px, Y0−25−10i)→(Kx+80−10i, …)→(…, Y0+20). Gidiş kırmızı sürekli (`ROTAS-ISITMA-GIDIS-BORU`, renk 10), dönüş turuncu çizgi-nokta (`…-DONUS-BORU`, renk 30, ISITMA DONUS HATTI). Test: hiçbir gidiş/dönüş kesişmez; yatay hat aralığı 5.
23. `S-5` Hat etiketi "NNNN.NW-Ø20" renk 41 h 10 her devrenin gidiş köşesinde (Px−15, Y0−20−10i) sola; kombi–kollektör "ΣW-Ø32".
24. `S-6` Daire etiketi, kombi gücü ve devre bilgileri plandaki etiketlerle birebir aynı değerler (test: plan etiket değer kümesi == şema değer kümesi).

**Teslim**
25. `T-1` Isıtma seti: antet (ISITMA TESİSATI PROJESİ) + yerleşim + her kat yerden ısıtma planı (başlık "N. KAT PLANI..........ÖLÇEK: 1 / 50", h 40, plan altında) + kolon şeması; plan adımı ≈ 2 080; temel/çatı paftası yok.
26. `T-2` Katman adları `ROTAS-` önekli (kullanıcı standardı); renk/kalınlık/çizgi tipi §2 tablosu; her şey Türkçe; DWG + DXF + önizleme PDF + Excel (şablon formülleri bozulmadan, logo temiz).
