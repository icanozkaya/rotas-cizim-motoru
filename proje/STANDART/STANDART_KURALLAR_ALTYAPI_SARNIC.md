# STANDART ek kurallar — altyapı/rögar, vaziyet, yağmur sarnıcı, merkezi sistem (kullanıcı kaydı 15.10.2026 21:27)

Kaynak: "Yağmur sarnıcı ve havalandırma tasarımı" konuşması (944-343 ve 318-319 Güngören sarnıçları, otopark duman tahliyesi,
2750 ada 7 parsel A-B blok — motor/ab2750, proje/ab2750) + bu oturumun sihhi2/yerden2 standardı. Kullanıcı: "oradaki rögarları
dikkate al, temel yerleşimleri, vaziyete işleme vesaire hepsini dikkate al ... tekrar sisteme kayıt et bunlarla beraber".

## Altyapı (temel) planı ve rögarlar
- Altyapı planı sıhhi paftasının EN SOLUNDA; mimariden yalnız betonarme kolonlar + bina dış hattı, rögarlar, hatlar.
- Rögarlar R1..Rn BİNA DIŞINDA, cephe boyunca; ölçü notu "70x70 h:-70cm" (veya projeye göre); rögar arası eğim %1;
  hat etiketi "L=… / Q=Ø… / %1"; kolon→rögar Ø125 %1 (45° pahlı köşe), rögar arası Ø150 %1; son rögardan PARSEL BACASI (PB).
- PB en yakın yola bağlanır (blok başına ya da tek PB — en makul olanı seçilir, raporlanır); SASKİ / İSKİ şartları gözetilir;
  bağlantı kotu belediyeden alınır notu.
- Bodrum varsa üst kat kolonları zemin katta biter (temele inmez), zemin kotundan doğrudan bina dışı rögara; bodrum ıslak
  hacimleri pis su çukuru + dalgıç pompa (1 asıl + 1 yedek) ile AYRI rögara (pompa basma hattı kolon hatlarına bağlanmaz);
  pompaya havalık gösterilmez.
- Kolonlar çatıya havalık (çatıdan 50 cm).

## Vaziyet (yerleşim) planı
- Vaziyette (1/200–1/250): bina dış hatları, rögarlar ve PB, PB'den yola bağlantı hattı, yağmur suyu bağlantı rögarı (YSR)
  ve sarnıç (varsa), "YAĞMUR SUYU KANALINA GİDER" / pis su kanal bağlantısı yazıları; yol genişlikleri mimariden.
- Planlar mimari koordinatında (kullanıcı COPYCLIP → PASTEORIG ile oturtur); mimari altlık ROTAS-MIMARI (renk 8),
  betonarme kolon/perdeler ROTAS-MIMARI-KOLON — kolonlar DOSYADA KALIR (hizalama için, ZORUNLU).

## Yağmur suyu ve sarnıç
- Yağmur suyu altyapısı kullanıcı istemedikçe çizilmez; yağmur iniş kolonları mimarideki yerlerinde, cepheye yaslı, zemin katta
  biter; hesap S = P×0,75, A = S/f, D = 1,13√A (Ø70 < 7 cm UYGUNDUR); plan + şema + "YAĞMUR SUYU BORU ÇAPI HESABI" kutusu.
- Balkon süzgeci yalnız balkon yağmur inişine kısa hatla; yağmur hatları HİÇBİR ŞEKİLDE pis su hattına / PB'ye bağlanmaz.
- YAĞMUR SUYU SARNICI (istenirse; PAİY m.57/7-a, TS EN 16941-1): kullanıcının kabataslak gösterdiği yerde, en/boy/yükseklik
  yere göre; V = 0,06 × E (E = A·h/1000·e·η); YB'ler toprak altı PVC ile F1 girdap filtre → sakinleştirici giriş → sarnıç;
  yüzer emiş + sulama hidroforu (yalnız bahçe sulama, içilmez etiketi); TAŞMA sarnıç içindeki taşma sifonundan F1 kirli suyu ile
  birlikte CAZİBEYLE YSR (yağmur suyu bağlantı rögarı, bina dışı, 60x60) üzerinden yağmur suyu kanalına (taşma pompası yok);
  şebeke takviyesi yalnız TS EN 1717 AB hava boşluklu; pafta: plan + kesit + hesap tablosu + ekipman listesi + şema + notlar.
- Depo taşma/boşaltma uçları açık bırakılmaz, yağmur inişine/YSR'ye bağlanır.

## Kullanım suyu, sayaç, merkezi sistem
- Mimaride depo yeri yoksa çatıda depo varmış gibi kurgulanır (depo çatıda → hidrofor yok); 10 daireye kadar 3 m³, sonrası
  daire başına +0,5 m³; bodrumda depo/ıslak hacim varsa hidrofor.
- Kombili konut: su sayaçları bina girişinde TOPLU (zemin, şebeke girişi; şemada zemin bandının solunda); sayaçlardan daire
  beslemeleri ortak alandan düşeyle, daire kapısı yanından girer — planlarda gösterilir.
- MERKEZİ SİSTEM (kazan dairesi + boyler): sıcak su 3 borulu (soğuk/sıcak/sirkülasyon), sirkülasyon daire sayaç dolabı öncesinde
  biter; her daire girişinde ortak koridorda SAYAÇ DOLABI (soğuk + sıcak su sayacı + ısıtma kalorimetresi); daire içinde
  kombi/termosifon yok; beslemeler ortak alandan (koridor asma tavanı/şaft), kolonlar her katta aynı hizada.
- Kazan dairesi yalnız onaylı `motor/deneme/kazan_dairesi/plan_kesit.py`.

## Havalandırma
- Penceresiz banyo/WC: WC aspiratörü (wc 80, banyo 160 m³/h-50 Pa Ø150) şafta/çatı fanına; planlarda + kolon şemasının sonunda.
- Otopark: duman tahliyesi 10 hava değişimi (m² × kat yüksekliği), çıkış mimarın gösterdiği yerden, yoksa uygun yerden; şema eklenir.
- Sığınak: taze = net alan × yükseklik × 4, egzoz %10 aşağı, >100 m² duman tahliyesi 10/h, perde geçiş ölçüsü (v=2,5 m/s).

## Referans çıktılar
- `proje/STANDART/STANDART_SIHHI_new_block.dxf`, `STANDART_YERDEN_ISITMA_new_block.dxf/.xlsx` (sihhi2 / yerden2).
- Sarnıç: `proje/.../318-319_GUNGOREN_YAGMUR_SUYU_SARNICI_EK.dxf` (motor/gungoren/ys_ciz2.py), 944-343 sarnıç + otopark duman
  ek DXF (motor/sarnic/c944_ek.py). Sığınak: `proje/ab2750/AB2750_SIGINAK_HAVALANDIRMA.dxf` (motor/ab2750/siginak_hav.py).
- AB2750 sıhhi taslağı (`proje/ab2750/AB2750_SIHHI_TESISAT.dxf`) KONTROLSÜZ taslaktır; standart değildir — sihhi2 motoruyla
  yeniden üretilecek (kalan iş: motor/ab2750/BENIOKU.md İLERLEME NOTU).

## SASKİ / ALTYAPI VAZİYET MANTIĞI — kullanıcı kaydı 16.10.2026 ("istediğim mantık buydu")
Onaylı örnek: `proje/STANDART/STANDART_SASKI_ALTYAPI_VAZIYET_korucuk_3346_13.dxf` (Korucuk 3346/13, A-B-C-D blok),
görseller `kutuphane/arastirma/geri_bildirim/ONAYLI_saski_altyapi_*.png`.
YANLIŞ yapılan (16.10 ilk teslim): SASKİ çizimi blok blok temel paftalarına taşındı, kolon bağlantısı kurulmadı — REDDEDİLDİ.

DOĞRU MANTIK:
1. Taban çizim SASKİ (onaylı vaziyet) — kendi koordinatında ve ölçeğinde kalır. Kullanıcının TEMEL planındaki
   bloklar (yalnız dış hat + pis su kolonları) "X BLOK GİRİŞ" yazılarıyla hizalanıp SASKİ vaziyetine TAŞINIR
   (temel cm → SASKİ birimi; bu projede SASKİ 1 birim = 4 cm, temel ×0,25).
2. Pis su KOLONLARI temel planından gelir; SASKİ'deki eski rögar dizisi esas alınmaz, ağ kolonlara göre YENİDEN kurulur.
3. Rögarlar BİNA DIŞINDA, cepheye paralel bir hat üzerinde (cepheden ~1,5–2 m); her kolon branşmanının cepheden
   çıktığı noktada bir rögar; köşe/yön değişiminde rögar. Rögar arası ~1,6–3 m (çıkış sıklığına göre), en çok ~10 m.
4. Kolon → rögar branşmanı: kolondan kısa 45° ile cepheye DİK düz hat; iki komşu kolon tek branşmanda birleşip aynı
   rögara iner. Kolon hangi cepheye yakınsa o cephedeki rögara bağlanır (orta kolonlar en yakın cepheye). Hatlar
   yalnız dik ve 45° (yatay/düşey + 45° dirsek); hat üst üste binmez.
5. Rögarlar cephe boyunca ana hatla birbirine bağlanır; ağ en yakın yol tarafındaki PARSEL BACASI (PB)'na akar;
   PB SASKİ ana kanal bacasına (Ø200) bağlanır. Gerekirse birden fazla ağ / birden fazla PB (bu projede 2 PB).
6. Numaralama: R1..Rn her ağda (PB'ye akan her dizide) ayrı; PB etiketi "PB".
7. Etiketler: her rögarda "70x70 / h:-70cm"; her hat parçasında akış oku + "Ø150 / %1 EĞİM"; ana hat Ø150, %1.
8. Bodrum ıslak hacmi / sığınak olan blokta PİS SU POMPASI (pompa rögarı) çizilir ve en yakın rögara basma hattıyla
   bağlanır (D blokta 2 pompa).
9. Kanal durum belgesi bilgileri (PB bağlantı kotu = yol kotu −80 cm, baca no, Ø200) vaziyette not olarak kalır.
