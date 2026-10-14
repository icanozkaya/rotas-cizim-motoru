# sihhi2 / plan.py — SIHHİ KAT PLANLARI (zemin, 1, 2)

```
python3 motor/sihhi2/plan.py          # ~85 s
python3 motor/kontrolor/kontrolor.py proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf \
        --mimari ornekler/new_block.dxf.xz --rapor /tmp/claude-0/s2/rapor.md
```
Çıktı: `proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf` (kat paftaları yan yana, mimari altlık `ROTAS-MIMARI*`,
başlık `ZEMİN KAT PLANI.........ÖLÇEK: 1 / 50`) + `sihhi_model.json` (`MODEL.md`; şema/temel/pafta bunu okur).
Sıfırdan yazıldı; eski `uctan_uca` tarz olarak kullanılmaz. Mimari tanıma: `mimari2.py` (+ kontrolörün `mimari_bilgi`
sonucu `K.kb`; kolon/köşe doğrulaması kontrolörle aynı ölçüyle yapılır). Semboller saf geometri (MTY 0).

## Akış
1. Katlar **Z → 2 → 1** sırasıyla işlenir; her kat önceki katların kolon eksenlerini (`onceki`) alır → kolonlar düşey
   süreklidir (P1–P9 üç katta aynı eksen). Eksen ring noktasına ≤ 25 cm ise kolon eksene taşınır, kola dik/L ayak eklenir.
2. **Pis su** (`pis_su_oda`): iki mahal poligonu varyantı denenir (eski poligon / armatür çentikleri kapatılmış mitre
   kapanış). Duvardan 4 cm halka; aday kolon = dışbükey köşe ±40 cm + kontrolörün ıslak hacim köşeleri + diğer kat kolonları;
   kapıya < 15 cm, şaft, betonarme hariç. Kollar halka boyunca (duvar dibi), köşelerde 45° pah (8–20 cm), 0/45/90 dışı
   parçalar `oktal` ile bölünür. Branşman = 5 cm 45° + kola dik; hattın üstündeki armatür kol düğümüne bağlanır.
   Doğrulama (`pis_dogrula`): kolon kontrolör ıslak hacminde ve köşesine ≤ 43 cm, balkona taşma yok, armatür→kolon yolu
   ≤ 282 cm (kontrolör sınırı 300), pis–pis kesişme 0. Her ıslak hacimde 1 süzgeç (yoksa EK), ÇM/BM yoksa EK.
3. **Temiz su** (`temiz_su_daire`): 5 cm ızgarada dönüş cezalı (30) Dijkstra ağacı; maliyet mahal ortasını sever
   (60/(d+3)), kapı açıklığı yasak, kapı kanadı süpürme alanı (+30), başka daire/ortak alan yasak; aynı dairenin kuru
   mahalleri yalnız gerekirse (duvar dibi, ör. odadan girilen duş); balkondaki kombiye duvar dibinden. Basamaklı yollar
   `merdiven_duzelt` ile tek dönüşlü L'ye çevrilir. Sıcak hat = kombiden sıcak armatürlere giden alt ağaç, 5 cm paralel.
   Giriş daire kapısı yanında (r 2 işaret) + `1 1/4" / n MB`.
4. **Balkon süzgeci** yalnız balkondaki yağmur inişine (~30 cm), yeşil hat; YB = mimarın çift dairesi.
5. **Etiketler** (`kat_etiketle`): pis su `Ø / SB` hattın üstünde, parça ortasında, hat yönünde (h 10), her parça 1;
   sığmazsa parça boyunca 5 noktadan kılavuzlu halka araması (24 yön, 35–300 cm). Temiz su 4 satır yatay, hat çifti başına 1.
   P/YB balonları ıslak hacim dışında, kılavuzlu. Penceresiz ıslak hacimde aspiratör yazısı (turuncu; şaft başına 80 m³/h ×
   bağlı ıslak hacim, new_block'taki gibi 80 / 160).

## Son kontrolör sonucu (15.10.2026)
T01–T11: yalnız **T04 ×1** (1. kat daire 6 wc-duş, sıcak su 217 cm "daire dışı"). Aynı FAIL kullanıcının kendi
new_block çiziminde de çıkıyor (246 cm, aynı mahal): kontrolörün daire ataması wc-duş'u daire 5'e veriyor; kapısı
daire 6'ya açılıyor. Kontrolör sınırı, çizim hatası değil.

## Bilinen sınırlar / açık sorular
- 1. katta sağ blokta mimari farklı (wc-duş + banyo, wc-lvb yerine yüklük): P2/P3 o katta bağlantısız geçer
  (`gecis_katlari`), wc-duş P10, banyo P11 ayrı kolon. P3 ekseni 1. katta wc-duş duş teknesi köşesine düşüyor.
- Banyolarda (5,36 m²) omurga halka boyunca üç duvarı dolaşır (kontrolörün 300 cm / 0-45-90 sınırları içinde);
  kullanıcının çiziminde tek eğik omurga var (kontrolör T02 bunu FAIL sayıyor).
- Mutfak kolonu tezgâh altında duvar dibine konamıyor: kontrolör mutfak ıslak alanını tezgâh önünde bitiriyor.
