# kanal — havalandırma kanal güzergâhı, boyutlandırma ve plan çizimi (deneme modülü)

## Ne yapar
Menfez noktaları ve debileri ile fan/cihaz ağzından:
1. **Ağaç güzergâh (ortogonal, tarak tipi):** cihaz ağzı → öncü parça → gövde → her menfez sütununa branşman. Gövde ekseni (x/y), gövde konumu (menfez sıraları arası / dışı), branşman tarafı ve öncü boyu adayları denenir. Seçilen aday çakışmasızdır ve en az sac alanlıdır. Kolon, duvar boyunca yürüme, bina dışı, diğer ağın kanal ve menfezleri ile kendi içindeki çakışmalar elenir. Kalan çakışmada branşman tarafı sütun sütun çevrilir (onarım). Üfleme ve emiş ağları birlikte seçilir: en iyi 16 üfleme adayının her biri için emiş çözülür, toplam maliyeti en düşük çakışmasız çift alınır.
2. **Boyutlandırma:** dikdörtgen kanal, 50 mm adımlı. w ≥ h, w/h ≤ 4, h ≤ asma tavan boşluğu (`hmax`).
   - Eşit sürtünme yöntemi: R ≤ hedef Pa/m ve v ≤ v_ana / v_brans.
   - Hız yöntemi: yalnız v ≤ v_max.
   - Seçim en küçük sac çevresine göre yapılır. Sürtünme Darcy + Swamee-Jain ile hesaplanır (galvaniz ε = 0,15 mm).
   - Menfez ölçüsü serbest kesit hızından seçilir (tercihen 1,5–3 en/boy). Flex çapı v ≤ 3,5 m/s'ye göre alınır.
3. **Çift çizgi plan:**
   - Redüksiyon: branşman ağzından sonra trapez + ek yeri çizgileri.
   - Dirsek: eşit genişlikte yuvarlatılmış (dış R = kanal genişliği).
   - T ayrım: kanal poligonları birleştirilerek çizilir, böylece çizgi üst üste binmez.
   - Akış okları içi dolu üçgendir; emiş/egzozda yön terstir.
4. **Etiketler:**
   - Kanal: `450x300` / `2.400 m³/h [Ü1]`. Köşeli parantezdeki no basınç tablosu satırıdır.
   - Menfez: `Q=200 m³/h` / `300x150`.
   - Hepsi çakışmasız yerleşir, altları WIPEOUT maskelidir. Uzaktaki yazıya kılavuz çizgi çekilir.
5. **Semboller** (`kutuphane/arastirma/03_SEMBOLLER.md` geometrisi; MTY kütüphanesinde havalandırma bloğu yok):
   - çift sıra kanatlı tavan menfezi ve kanal yanağı menfezi
   - izoleli flex (akordeon çizgili)
   - VD ayar damperi: her branşman başında
   - FD yangın damperi: yangın duvarı kesişiminde otomatik
   - BDD geri akış damperi
   - taze hava / atık hava panjuru, IGK (plakalı), aksiyel fan, jet fan
6. **Tablolar:**
   - kanal basınç kaybı (R·L + Σζ·ρv²/2; kritik hat; cihaz dışı basınç +%10)
   - galvaniz sac metrajı: ölçü, uzunluk, çevre, m², kalınlık, kg; flex, menfez ve damper adetleri
   - lejant ve notlar
7. **Teslim öncesi kontrol (`kontrol_raporu`):** ağlar arası kanal çakışması, kolon kesişimi, yazı-yazı ve yazı-kanal çakışmasına bakar. İki test çıktısında da sonuç "temiz".

## Çalıştırma
```
cd motor/deneme/kanal
python3 calistir.py ornek_ofis.json    ../../../proje/denemeler/kanal/ofis_kanal_R2.dxf     # ~30 s
python3 calistir.py ornek_otopark.json ../../../proje/denemeler/kanal/otopark_jetfan_R2.dxf # ~2 s
python3 onizle.py <dxf> <png> [x0 y0 x1 y1]     # kontrol önizlemesi (PNG depoya konmaz)
```
Çıktı yalnız DXF'tir (R2018/AC1032, ezdxf). Birim cm, ölçek 1/50. Tüm katmanlar `ROTAS-` önekli. Tasarım değerleri JSON'dadır; `"deneme": true` olduğunda pafta üstüne DENEME başlığı yazılır.

## Dosyalar
- `kanal.py`: kütüphane (hesap, ağaç, güzergâh arama, geometri, semboller, etiket yerleşimi, tablolar, kontrol)
- `calistir.py`: senaryolar (`ofis`, `otopark`) ve lejant örnekleri
- `ornek_ofis.json`: 25×15 m ofis. 12 üfleme (200 m³/h) + 6 emiş (380 m³/h) menfezi. Koridor asma tavanında IGK-1 bulunur ve iki yangın damperi bu koridor duvarındadır. Taze hava ve atık hava panjurları cephededir.
- `ornek_otopark.json`: 30×20 m (600 m², h = 3 m) kapalı otopark.
  - ROTAŞ kuralı: normal havalandırma 4 h⁻¹ = 7.200 m³/h, duman tahliyesi 10 h⁻¹ = 18.000 m³/h.
  - 9 egzoz menfezi doğu duvarı boyunca duman egzoz kanalı yanağındadır. Kanal hız yöntemiyle boyutlanır (v ≤ 10 m/s), 850x600 → 450x450.
  - Fan odasında 2 aksiyel F300 fan (BDD'li) ve egzoz şaftı bulunur.
  - 4 jet fan (2 sıra × 2) yerleşimi yanal 10 m / atış 15 m kuralıyla yapılır.
  - Taze hava rampadan girer; hız kontrolü 0,33 m/s ≤ 2 m/s.
- `onizle.py`: PNG önizleme

## Sınırlar / bilinenler
- Güzergâh yalnız **tarak** topolojisidir: tek gövde ve gövdeye dik branşmanlar. L/U gövde, çok gövdeli ya da engel etrafında dolanan A* güzergâhı yoktur. Engel bloke ederse aday elenir; hiç aday kalmazsa hata verir.
- Kanal kesişmesinde köprü (bir ağın diğerinin altından geçmesi) çizilmez; kesişen aday elenir.
- Mimari, gerçek DWG'den değil JSON poligonlarından gelir. Kullanıcı planı üzerinde çalıştırmak için bir DXF okuyucu bağlanmalıdır (duvar/kolon katmanları → `mimari`).
- Yerel kayıp katsayıları (ζ) sabit tablodan alınır: T branş 1,0, düz geçiş 0,3, dirsek 0,3, VD/FD 0,2, cihaz ağzı 0,5. Menfez 25–30 Pa, flex 5 Pa, panjur 25 Pa, şaft/jetcap 60 Pa varsayımdır.
- Redüksiyonlar eş eksenlidir. Eksantrik (tek yanı düz) redüksiyon seçeneği yoktur. Kanal yüksekliği ağ boyunca sabit tutulmaz, her parça kendi en ekonomik ölçüsünü alır.
- Jet fan sayısı kapsama kuralıyla bulunur; itki/hız doğrulaması yapılmaz, çizimde de "CFD ile doğrulanacaktır" notu vardır. CO dedektörleri çizilmez, notta belirtilir.
- MTY bloğu kullanılmaz (14.10 B); semboller araştırma notu geometrisiyle saf çizgidir.
- Antet ve pafta çerçevesi yoktur; yalnız plan, başlık, tablolar, lejant ve notlar çizilir.

## R2 revizyonu (14.10.2026 (B) talimatı)
- Otomatik lejant + adet: sembol çizicileri (`menfez_tavan/yan`, `flex_ciz`, `vd/fd/bdd_ciz`, `panjur_ciz`, `fan_aksiyel`,
  `jetfan_ciz`, `igk_ciz`) `Cizim.adet()` ile sayar; `lejant()` adedi 0 olan satırı atlar, kanal satırlarına metraj (m) yazar.
  Lejant örnekleri `lejant_modu` ile sayılmaz. Ofis lejantına IGK cihazı eklendi.
- Kanal kesişmesi/köprü yok (kesişen aday elenir), elektrik kalemi yok; `calistir.py` sonunda `mty_kontrol()` (MTY 0).
- Çıktılar: `ofis_kanal_R2.dxf`, `otopark_jetfan_R2.dxf`; KONTROL temiz.
