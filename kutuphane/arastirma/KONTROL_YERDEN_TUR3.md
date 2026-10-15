# KONTROL — YERDEN ISITMA, TUR 3 (son tur, bağımsız kontrolör)

- İncelenen dosyalar: `proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf` ve `NB_YERDEN_ISITMA.xlsx` (15.10.2026 05:00 sürümü).
- Referans: kullanıcının `new_block.dxf` dosyasındaki ısıtma seti. Plan kayması dx = +22 761,9 cm. 1. ve 2. kat, referansın zemin katıyla karşılaştırıldı (kat kayması +2 034 / +4 082 cm).
- Ayrıca kullanılanlar: README kalıcı kuralları, `YERDEN_ISITMA_ALTIN_REFERANS.md`, `onay_protokolu.md`, tur 2 raporu.
- Yöntem:
  - Üreticinin kodu okunmadı.
  - `kontrolor.py --tur yerden --excel` çalıştırıldı. Araç raporu: `kontrol_png/yerden_tur3/kontrolor_arac_raporu.md`.
  - Tur 2 pencereleri yeniden kırpıldı ve referansla yan yana kondu (`kontrol_png/yerden_tur3/01–11`). Sol taraf kontrol edilen dosya, sağ taraf kullanıcının çizimi.
  - Vitrifiye altındaki boru, maske altında kalan mimari çizgi ve etiket yazı boyu DXF'ten ölçüldü (shapely).

## KARAR: **RED**: 3 FAIL kaldı (Y02, aynı neden). Protokole göre dosya kullanıcıya gönderilmez.

Tur 2'deki 4 maddeden 3'ü kapandı. Kalan madde tek bir nedene bağlı: üç adet 4,37 m²'lik wc+banyo.

Bu madde bir kural çelişkisinden doğuyor, üreticinin ihmali değil. Çelişki şu:
- Motor şartnamesi (ALTIN §3.4 / PEX-10) "klozet ve lavabo altına girilmez" diyor.
- Kullanıcının kendi çizimi klozet altından geçiyor.

Çözüm aşağıda (Y-2'). Bu tur ONAY verilemez, çünkü protokol FAIL kalırken onaya izin vermiyor. Eşik gevşetmek de yalnızca kullanıcının kararıyla yapılabilir.

---

## Tur 2 maddeleri: KAPANDI / AÇIK

| Madde | Durum | Kanıt |
|---|---|---|
| Y-1 Yüklüğe giren serpantin (102, 202) | **KAPANDI**. Y01 üç katta 0 FAIL, ısıtılmayan mahalde boru yok. 102 devreleri 42,80 + 39,77 m, yüklük boş | `08_1kat_102_yukluk_iki_devre.png`, `09_2kat_202_…png` |
| Y-2 Islak hacim doluluğu (5 FAIL) | **KISMEN**. Z14 ve 121 banyoları geçti. Z21, 114 ve 214 wc+banyoda hâlâ 10,0 / 10,0 / 9,8 m var, gereken ≥ 13,1 m (2,25–2,28 m/m²). Ayrıntı Y-2'de | `01–03_*wcbanyo*_yan_yana.png`, `07_Z_banyo_Z14_yan_yana.png` |
| Y-3 İki devreli mahalde etiket öbür devrenin üstünde | **KAPANDI**. Y05 81/81 geçti: her etiketteki hat uzunluğu altındaki devreyle aynı. 111'de 61,93 m üst devrede, 60,92 m alt devrede | `10_1kat_111_salon_iki_devre.png`, `08_…png` |
| Y-4 Etiket maskesi vitrifiyeyi gizliyor | **KAPANDI**. Dosyada 150 WIPEOUT var. Bunların hiçbirinin altında `ROTAS-MIMARI` çizgisi yok (ölçülen 0 cm). Maskeler vitrifiyenin çevresinden kesik çizilmiş. Küvet, duş teknesi ve Ç.M. görünüyor | `04_Z_wcbanyo_Z21_etiketler_yakin.png`, `05_…png`, `11_…png` |
| K-1 35 W/m × L esası | **KULLANICI SORUSU** (değişmedi). Excel TEKNİK RAPOR B41–B47'de negatif MODÜL notu var. MMO uyarıları B38–B39'da. 7 sayfanın hepsinde yazdırma alanı var, hücre hatası yok, dış bağlantı yok | — |

---

## Kalan maddeler

### Y-2' Üretici düzeltecek: 4,37 m² wc+banyoda serpantin kullanıcının çizimindeki gibi klozetin önünün altından geçmeli (Z21, 114, 214)

Sorulan konu, ölçümlerle:

1. **README ne diyor?** "Kalıcı kurallar"da klozet ve lavabo alanı hariç tutulmuyor. Yalnızca "mutfak dolapları (tefriş) altına serpantin girmez" ve "tefriş ve mahal yazıları silinmez" yazıyor. "Klozet ve lavabo altına girilmez (Z07)" ifadesi README'de geçmiyor. Bu ifade `YERDEN_ISITMA_ALTIN_REFERANS.md` §3.4 ve PEX-10'da var. Bunlar türetilmiş şartname metinleri.
2. **Kullanıcının çizimi ne gösteriyor?** Bu ifade kullanıcının çizimiyle çelişiyor (ölçüm: borunun klozet ya da lavabo dış çizgisinin içinde kalan boyu):

| Mahal (kullanıcı çizimi) | Klozet içinde boru | Lavabo içinde boru | Devre |
|---|---|---|---|
| wc+banyo (bu dosyada Z21 konumu) | **1,27 m** (klozet çevresindeki 7,5 cm şerit dahil 2,05 m) | 0 | 13,79 m |
| banyo Z14 | **1,24 m** | **1,12 m** | 23,53 m |

   Kullanıcının çiziminde lavabo, duş teknesi ve Ç.M. altı boş. Klozetin ön kısmının altından ise ilmekler geçiyor (`04_…png` sağ taraf, `07_…png` sağ taraf).
3. **Klozet hariç tutulursa ne olur?** Kullanıcının kendi wc+banyo çiziminden klozet çevresindeki 7,5 cm şerit çıkarılırsa geriye 11,74 m kalıyor. Bu da Y02 eşiği olan 13,1 m'nin altında. Yani PEX-10 ile Y02 bu mahalde birlikte sağlanamıyor. Üreticinin "geometrik olarak sığmıyor" tespiti doğru.
4. **Karar:** README'ye göre tek referans kullanıcının kendi çizimi ("yan yana konduğunda aynı tarzda görünmeli"). Bu yüzden bu konu kullanıcı kararı olarak işaretlenmemeli. Üretici kullanıcının çizimini izlemeli:
   - İlmekler klozetin ön kısmının altından geçmeli (Z07'deki gibi, sağdaki dönüşler klozet çanağının içinde).
   - Lavabo, duş teknesi, Ç.M. ve mek. havl. altı boş kalmalı.
   - Mahal içinde ≥ 13,1 m olmalı. Kullanıcının çiziminde bu değer 13,80 m.
   - Bugünkü durum: devre 9,96 m, borular x = 253 043…253 207 ve y ≥ −442 154 arasında. Kullanıcının çizimi aynı bantta 6 sıra ilmek atıyor, bizim çizimde 4 sıra var (`01_…png`).
5. **Kullanıcıya yalnızca bilgi verilir** (soru sorulmaz): "wc+banyoda serpantin sizin çiziminizdeki gibi klozet önünün altından geçirildi."
   - Şartname metni de düzeltilmeli: ALTIN §3.4 "klozet ve lavabo altına girilmez (Z07)" ve PEX-10. Doğru ifade: "Lavabo, duş teknesi ve Ç.M. altı boş. Klozet ön kısmı ve banyo lavabosu kullanıcı çiziminde kısmen örtülüyor."
   - Bu metin düzeltmesi üreticinin ya da ana oturumun işi. Kontrolör eşik ve şartname değiştirmez.
6. **Z14 için:** Bu dosyada Z14 banyosu Y02'den geçti ve klozetin altında boru yok. Değişmesi gerekmiyor. Lavabo dış çizgisinin içine 0,29 m boru giriyor; bu kullanıcının çiziminde de var (1,12 m), kabul edilir.

### E-1 Üretici düzeltecek (Y-2' ile aynı üç mahalde): 0,7 ölçekli devre etiketleri baskıda okunur boyun altında
- Paftalar 1/50. Etiket yazı yüksekliği 10 birim. Buna göre:

| Etiket ölçeği | Yazı yüksekliği | Basılı boy | Nerede |
|---|---|---|---|
| ×1,0 (kullanıcı) | 10 cm | 2,0 mm | kullanıcının her yerinde |
| ×0,85 | 8,5 cm | 1,7 mm | 6 hol etiketi |
| ×0,7 | 7 cm | **1,4 mm** | Z21, 114, 214 |

- Ekranda okunuyor (`04_…png`). Ancak 1,4 mm, teknik resimdeki en küçük yazı boyu olan 1,8 mm'nin (ISO 3098) altında.
- Kullanıcı Z07'de etiketi tam boyda koymuş: duş teknesi ve "mek. havl." yazısının üstünde, maskesiz (`04_…png` sağ taraf).
- Düzeltme: Bu üç etiket ×1,0'a dönmeli. Kesik maske ya da maskesiz yerleşim (Y-4'te kapanan yöntem) korunmalı.
- ×0,85 hol etiketleri (1,7 mm) sınırda. Okunur (`11_…png`), engelleyici değil. Mümkünse ×1,0 olmalı.
- ×0,8 mahal etiketleri (9,6 cm → 1,9 mm) uygun.

### K-1 Kullanıcıya sorulacak (RED gerekçesi değil)
Soru: "Devre gücü sizin çiziminizdeki gibi 35 W/m × L mi kalsın, yoksa 17,5 W/m ya da ısı kaybı esasına mı geçilsin?"

35 W/m × L ile şu sonuçlar çıkıyor:
- Yüzey sıcaklığı ≈ 37,8 °C. Oturma alanı sınırı 29 °C.
- Basınç kaybı Δp ≈ 19–22 kPa, sınırın üstünde.
- Modülasyon sayfasında negatif değerler çıkıyor. Bunlar Excel'de not olarak açıklanmış.

Cevap gelene kadar esas değişmez.

## Engelleyici olmayan gözlemler
- İki devreli mahallerde (102, 111 vb.) iki etiket kendi devrelerinin üstünde, ama aynı x hizasında değil. Kullanıcının çiziminde aynı x'te alt alta duruyorlar (ET-3). Bu bir tarz farkı.
- Z21 mahal etiketinin çerçevesi Ç.M. kutusunun üst kenarına değiyor. Kenar maskelenmiyor. Kullanıcının etiketi de "wc+banyo" yazısının üstünde durduğu için kabul edilir.
- Y01'de 54 BİLGİ var: yoğunluk 5,3–5,98 m/m². Kullanıcının kendi çiziminde de 24 mahal bu aralıkta.

## Olumlu bulgular (değişmesin)
- T11, T16, T17, Y01, Y03, Y04, Y05 ve Y06 geçti.
  - 81 devrenin her biri tek polyline. Kesişme yok.
  - Plan W = şema W (81/81) = Excel W (63 zon).
- Yüklük, balkon, wc-lvb, wc-duş, asansör ve merdiven boş.
- Hiçbir maskenin altında mimari çizgi yok.
- Excel'de hücre hatası yok ve yazdırma alanları tanımlı.

## Bir sonraki tura (üretici düzeltmesinden sonra kontrolör) kabul ölçütleri
1. Y02 FAIL = 0. Z21, 114 ve 214'te mahal içinde ≥ 13,1 m boru olmalı. Klozetin ön kısmı kullanıcının çizimindeki gibi örtülmeli. Lavabo, duş teknesi ve Ç.M. altı boş kalmalı.
2. Bu üç mahalde devre etiketi ×1,0 olmalı ve hiçbir maskenin altında mimari çizgi kalmamalı.
3. Geri kalan her şey bu turdaki gibi kalmalı. W esası K-1 cevaplanana kadar değişmez.

Kanıt PNG'leri `kutuphane/arastirma/kontrol_png/yerden_tur3/` klasöründe:
- `01_Z_wcbanyo_Z21_yan_yana.png`
- `02_1kat_wcbanyo_114_yan_yana.png`
- `03_2kat_wcbanyo_214_yan_yana.png`
- `04_Z_wcbanyo_Z21_etiketler_yakin.png`
- `05_Z_banyo_Z07_etiket_kuvet.png`
- `06_1kat_banyo_121_yan_yana.png`
- `07_Z_banyo_Z14_yan_yana.png`
- `08_1kat_102_yukluk_iki_devre.png`
- `09_2kat_202_yukluk_iki_devre.png`
- `10_1kat_111_salon_iki_devre.png`
- `11_Z_hol_Z13_etiket_085.png`
- `kontrolor_arac_raporu.md` ve `kontrolor_arac_raporu_png/`
