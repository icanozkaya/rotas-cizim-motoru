# yerden2 — yerden ısıtma kat planları + kolon şeması (new_block)

```
python3 motor/yerden2/yerden.py [--png] [--etiket-ust] [--ayaklar] [--yenile]
python3 motor/yerden2/yi_onizleme.py          # yalnız önizleme (DXF üretilmişse)
python3 motor/deneme/denetim/denetle.py proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf
```
| Seçenek | Ne yapar |
|---|---|
| `--png` | `proje/denemeler/yerden2/onizleme/` içine kat planı, şema ve referansla yan yana PNG'ler |
| `--etiket-ust` | Devre etiketi için cep bırakılmaz; tablo serpantinin üstüne maskeli olarak konur (kullanıcının kendi çizimindeki gibi) |
| `--ayaklar` | Varsayılan olarak kapalı. Henüz uygulanmadı, yalnız uyarı verir. Kullanıcının çiziminde planda ayak yok, bağlantı yalnız şemada gösteriliyor |
| `--yenile` | Mimari tanıma önbelleğini (`/tmp/claude-0/y2/onbellek`) yeniden kurar |

Çıktılar `proje/denemeler/yerden2/` içinde:
- `NB_YERDEN_ISITMA.dxf`: AC1032 biçiminde, birimi cm. Zemin, 1. ve 2. kat planları kaynak koordinatlarında, kolon şeması 2. katın sağında (x 258 850). Ayrıca lejant ve notlar var.
- `NB_YERDEN_ISITMA.xlsx`: `sablon/ornek_yi.xlsx` kopyası, formüller korunuyor.
- `NB_YERDEN_ISITMA_model.json`: mahal ve devre verisi. Şema ve Excel bu dosyadan okunuyor.
- `KONTROL.json`: kontrol sonuçları.

Bir koşu yaklaşık 25 s sürüyor, `--png` ile yaklaşık 60 s.

## Modüller
| Dosya | Görev |
|---|---|
| `mimari_yi.py` | Mahal tanıma `sihhi2/mimari2.Kat` ile yapılıyor (kontrolörle aynı yöntem). Bu modül ısıtılan mahalleri ve sıcaklıklarını belirler, poligonu başka bir mahal etiketini içine alan odayı böler (yatak odasından açılan yüklük gibi), kapıları bulur ve tefriş engellerini çıkarır. Engeller, mahal içindeki çizgilerin kapattığı bölgelerdir: tezgâh, buzdolabı, klozet, lavabo, duş teknesi, çamaşır makinesi. Kapı kanadı ve süpürme yayı engel sayılmaz. Isıtma bölgesi de burada çıkarılır: duvardan 7,5 cm içeride, girinti ve çıkıntıları temizlenmiş alan |
| `serpantin.py` | Meander geometrisi kanonik çerçevede kurulur (uç köşesi sol altta), sonra aynalanarak yerine konur |
| `tasarim.py` | Köşe seçimi (kapıya en yakın köşe; kaplama en iyinin %93'ünden düşükse daha iyi kaplayan köşe), devre sayısı, bant bölmesi ve etiket cebi |
| `yerden.py` | Ana akış: mimari altlık, numaralama, etiket yerleşimi, DXF |
| `yi_sema.py` | Kolon şeması (saf geometri) |
| `excel_yi.py` | Excel girdileri |
| `yi_kontrol.py` | Kontroller ve `denetle.py` çağrısı |
| `yi_onizleme.py` | PNG önizlemeler |

## Uygulanan kurallar
Referans: `YERDEN_ISITMA_ALTIN_REFERANS.md` §7 ve README.
- **Serpantin:** Her devre tek bir açık LWPOLYLINE, katmanı `ROTAS-ISITMA-PEX` (renk 1, lw 30). Parmaklar X eksenine paralel, boru aralığı 15. U dönüşü r 7 yay + 1 cm düz + r 7 yay (bulge 0,4142). Besleme hattı dikey ve ilk dönüş tepesinin 15 cm dışında. İki uç aynı köşede, aralarında 15 cm. Kenar mesafesi 7,5.
- **Devre bölme:** 14 m² ve üstü mahaller en az 2 devre. Hedef devre boyu ≤ 70 m, kesin sınır ≤ 80 m. Bölme parmaklara paralel bantlarla yapılıyor. Uzak devrenin besleme ve dönüş ayağı köşeye kadar iniyor; yakın devrenin besleme hattı 30 cm içeride.
- **Isıtılan / ısıtılmayan mahaller:**
  - Isıtılır: oda, salon, mutfak 20 °C; antre-koridor 15 °C (ayrı devre); banyo, wc-banyo ve 2 m² üstü wc-duş 24 °C.
  - Isıtılmaz: balkon, yüklük, 2 m² altı wc-lvb ve duş, merdiven, asansör, ortak alanlar.
- **Numaralama:** Kat içinde daire sırasıyla, sonra mutfak, oda, hol, banyo sırasıyla gider. Zon kodları zeminde Z01…, 1. katta 101…, 2. katta 201…. Devre numarası her katta 1'den başlar.
- **Devre etiketi:** `ROTAS-YI-ETIKET` bloğu. Sarı tablo 150×80, 4 satır: Hat uzunluğu / Modülasyon Aralığı 15.0 / Kcal/h: W / Isıtma Devresi-No. Yazı yüksekliği 10, genişlik çarpanı 0,65. W = 35 W/m × L ve L yaylar dahil gerçek polyline boyu. Yerleşim sırası:
  1. **Cep:** Devrenin kendi bandında, uç köşesine yakın, besleme hattının 10 cm içinde. Parmaklar cebin 7,5 cm dışında kısalıyor, yani serpantin dışında boş bir alan kalıyor.
  2. Cep sığmazsa oda içinde boş bir yer; o da yoksa oda içinde maskeli (WIPEOUT).
  3. O da olmazsa oda dışında boş bir yer ve uca bir kılavuz çizgi. Bu yer yazı, etiket ve boru içermiyor, mimari çizgi üstüne binmesi cezalandırılıyor.
- **Mahal etiketi:** `ROTAS-YI-MAHAL` bloğu: yuvarlatılmış kutu ve 3 halka (sarı-cyan-cyan-sarı). Üstte cyan h12 "20°C", altta kırmızı h12 "Z05". Mahal adının üstünde duruyor, altı maskeli (README: "altı maskeli").
- **Planda olmayanlar:** Kollektör, kombi ve ayak yok (kullanıcının çiziminde de yok). Mimari (`ROTAS-MIMARI*`) hiç silinmiyor.
- **Şema:** Kat bantları 400 cm yüksekliğinde, sol sütunda dikey kırmızı h25 kat adı. Kombi ve kollektör çiziliyor, yanında "H. KOMBİ 24KW" (daire toplamı 20 kW'yi aşarsa 28). Daire balonu r 55/49, h40. Paneller kollektörden 290 cm sonra başlıyor, 200 cm adımla diziliyor, devre numarası büyükten küçüğe. Gidiş (Px−5) ve dönüş (Px) hatları döşeme altında kademeli iniyor, aralık 5/10. Hat etiketi "NNNN.NW-Ø20", kollektör etiketi "ΣW-Ø32". Değerler plan etiketleriyle aynı.

## Kontrol sonuçları (son koşu, 3 kat, 82 devre)
| Kontrol | Sonuç |
|---|---|
| Devre kendini kesiyor mu | 0 |
| Devre–devre kesişme | 0 |
| Devreler arası mesafe 10 cm'nin altında | 0 |
| Tefriş ile kesişme | 0 |
| Isıtılmayan mahal ile kesişme | 0 |
| Mahal dışına taşma | 0 |
| L > 80 m | 0 (en uzun 59,5 m) |
| Uç aralığı 15 değil | 0 |
| Bulge ≠ 90° | 0 |
| Etiket–etiket çakışma | 0 |
| Etiket–mimari yazı çakışma | 0 |
| Cepteki etiket–boru çakışma | 0 |
| `denetle.py` | MTY 0, önek 0, köprü 0, kesişme 0, yazı 0, audit 0, lejant var: GEÇTİ (mimarın kendi yazı çakışmaları 111, yalnız bilgi) |

Etiketlerin 46'sı cepte, 36'sı oda içinde maskeli ya da oda dışında kılavuzlu. Bu 36'nın çoğu banyo, hol, wc-banyo gibi küçük mahallerde.

## Referanstan farklar
- **Etiket cebi:** Kullanıcının çiziminde tablo serpantinin üstüne biniyor (maske yok). Görev tanımı "serpantin dışında boş alanda" dediği için burada cep bırakılıyor. Bunun bedeli devre başına yaklaşık 9 m daha az boru. Örneğin 9 m² oda cepsiz 51 m, cepli 42 m; 14 m² oda cepsiz 82 m, cepli 64 m. `--etiket-ust` kullanıcının çizim davranışına döner.
- **Etiket bloğu:** Etiket blokları ölçek 1, dönüş 0. Yazılar okunur, referanstaki aynalı INSERT yok.
- **Uç köşesi:** Kuralla seçiliyor (kapıya en yakın köşe). Kullanıcı köşeyi elle seçmiş.
- **Alt satır atlama:** Bazı odalarda köşe girintisi yüzünden alttaki 1–4 satır atlanıyor ve köşede küçük boşluk kalıyor.
- **Excel:** Isı kaybı sayfaları (ZEMİN, 1 NK) ve TEKNİK RAPOR (2) şablondaki başka bir projenin verisi, bu yüzden kaldırıldı. Bu projede ısı kaybı hesabı yok. PETEK LİST "D" ve MMO "qh" değerleri şablonun birim verimiyle (17,5 W/m × L) yazıldı. Plandaki etiket ise kullanıcının davranışına göre 35 W/m × L. 35 W/m ile q" yaklaşık 200 W/m² çıkıyor ve döşeme yüzeyi 37 °C oluyor, gerçekçi değil. Mahal m² değeri mimarın m² yazısından alınıyor. Formüller korunuyor; LibreOffice ile yeniden hesaplamada hata 0.

## Açık sorular
1. Etiket cebi mi kalsın, yoksa kullanıcının çizimindeki gibi üstte (maskeli) mi olsun? Cebin kaplamaya etkisi yukarıda.
2. Plan etiketindeki "Kcal/h" değeri 35 W/m × L mi kalsın? Excel'de şablonun 17,5 W/m'si kullanıldı.
3. Isı kaybı hesabı yapılacak mı (`motor/isitma_hesap`)? Excel'in D sütunu ona bağlanabilir.
4. Planda kollektör ayakları istenirse `--ayaklar` uygulanmalı (yalnız hol ve kapı üzerinden, 15 cm çift).
