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

## Tur 2 (15.10.2026) — kontrolör RED (KONTROL_SIHHI_PLAN_TUR1.md) düzeltmeleri
- **Tasarım girdisi** `tasarim_new_block.json` (`tasarim_cikar.py` üretir, kullanıcının MTY çiziminden YALNIZ kararlar):
  P1–P9 kolon eksenleri (her katta aynı nokta), çatı P/YB konumları, ÇM/BM bağlantı kutuları (kat bazında),
  rögar ataması R1←P7,P9; R2←P8; R3←P2,P3,P5,P6; R4←P1,P4 + temel rögar konumları, balon ofsetleri.
  Kolon sayısı/yeri motor tarafından DEĞİŞTİRİLMEZ (P10/P11 yok). Islak hacim → en yakın P (poligon mesafesi);
  kolonu komşu ıslak hacimde kalan mahal (1. kat D6 wc-duş → P3) kendi halkasından duvar içinden kısa bağlantıyla
  komşu ağa `BAG` sözde-armatürü olarak katılır. O katta ıslak hacmi olmayan kolon (1. kat P2) sembol + balonla çizilir
  (`gecis_katlari`).
- **Pis su** `_pis_omurga`: kullanıcı topolojisi — kolondan en uzak armatüre tek omurga (0/45/90; L ya da 45°+düz),
  diğer armatürler dik + 5×5 cm 45° bağlantı; birleşim noktaları omurgaya köşe olarak eklenir (kontrolör ağ düğümü).
  Oda ortasından > 85 cm çapraz parça cezalı; doğrulanamazsa eski halka çözümü.
- **ÇM/BM** kullanıcının yerinde (mimari niş/tezgâh altı); mimari makineyi göstermiyorsa (EK) kutu + "Ç.M."/"B.M."
  yazısı. "(EK)" yazısı planda yok (yalnız modelde `ek: true`).
- **Aspiratör**: penceresiz (bina dış hattına 50 cm'de değmeyen) ya da şafta bitişik HER ıslak hacimde sembol;
  şaft grubu başına not (3 TEXT h 15, genişlik 0,8, satır 25): önce kendi mahallinde, sembol notun ≤ 25 cm yanında;
  sonra aynı dairenin bitişik hol/oda'sında (kılavuz ≤ 60 cm, başka ıslak hacmi kesmez); son çare kendi mahallinde.
- **Etiket engelleri** gerçek yazı kutusuyla: `etiket_kontrol.glif_kutusu` (TEXT/ATTRIB text2path, MTEXT yazı tipi
  satır genişliği) ∪ kontrolörün `kutu.yazi_kutusu` (TEXT alt uzantı); + duvar katısı / mimari tarama (merdiven
  basamakları hariç), asansör, merdiven (yalnız 2. turda kısa kılavuzlu pis su etiketi), armatür kutusu; marj 1,5 cm.
  Pis su etiketi 4 varyant (kanca sağa/sola × üst/alt); sığmazsa kılavuzlu halka (yatay/düşey, başka daireye girmez,
  kılavuz en çok 1 duvar keser). Bağımsız denetim: `python3 motor/sihhi2/etiket_kontrol.py` (E1–E5).
- **Temiz su** kuru mahaller önce kapalı; ulaşılamayan armatürün ıslak hacmine bitişik EN KÜÇÜK kuru mahal açılır
  (D3 duşu: 7,75 m² oda, yatak odası değil); kuru mahalde kapı açılım alanı +150 ceza; pis su hattına 14 cm yakın +6.
- **Çatı planı paftası** (258656…260714): mimari çatı altlığı + P havalıkları + YB inişleri/balonları + çatı tipi
  fanlar (şaftlar) + eğim okları + kullanım su deposu notu; "ÇATI PLANI.........ÖLÇEK: 1 / 50". Lejant paftası kalktı.
- Renkler: kılavuz 9, pafta yazısı 7 (ACI 250–255 / 8 yazı yok).
- Geliştirme: `S2_ONBELLEK=<pickle {kat: Kat}>` mimari tanımayı atlar (~45 s kazanç); `S2_DEBUG=1` red nedenleri.

## Bilinen sınırlar (tur 2)
- Kontrolör T10: kullanıcının P1/P4/P7 (tezgâh altı/duvar içi) ve P3/P6 (köşeden 48 cm) konumları kontrolörün ıslak
  hacim poligonuna göre "köşe dışı" sayılıyor — tasarım kullanıcınındır, değiştirilmedi.
- Kontrolör T07 mimari MTEXT kutusunu sütun genişliğiyle (≈ 238 cm) ölçüyor; satır genişliğiyle ölçülünce etiket–mimari
  yazı 0 (doğrulama betiği raporda).
- Kalabalık bölgelerde (mutfak tezgâhı içi eviye branşmanı, P3/P8 dibi, 1. kat D6) ~20 pis su parçası etiketsiz kalıyor
  (çakışma yerine etiketsiz bırakılır; `uyarilar`).

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
