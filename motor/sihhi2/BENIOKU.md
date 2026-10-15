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

## Tur 4 (15.10.2026) — kontrolör tur 3 RED (KONTROL_SIHHI_TUR3.md, R1–R4 + K1) düzeltmeleri
- **R1 her pis su parçası etiketli**: etiket birimi artık çizgi SEGMENTİ (omurga birleşimlerinde ve köşelerde bölünür;
  ≥ 20 cm her segment kendi etiketi; < 20 cm uçlar isteğe bağlı). Kısa / kalabalık parçalar önce yer seçer.
  Etiket boyu değişmedi (h 10, kullanıcı bloğu). Sıra: (1) hat üstünde, kanca hatta, başka hat kesmez; (2) başka
  boru yazının altından geçebilir, etiket parçanın ucuna/uzantısına kayabilir (t 0…1); (3) kısa kılavuz ≤ 45 cm,
  yazı parçaya ≤ 30 cm, aynı dairenin mahallerinde (kılavuz en çok bir ara duvar ≤ 25 cm keser); (4) sığmayan: kılavuz
  ≤ 60 cm. **Sahiplik**: etiketin 'n SB' satırı (kontrolör ölçüsü) kendi parçasına en yakın pis su parçası olmalı.
  **Yasaklar** (`Engel.pis_yasak`): yazı / sembol / mimari yazı / armatür / beton taraması / asansör / ortak alan /
  başka daire; duvar çizgisi üstüne en çok yarısı binebilir (kullanıcı wc-lvb. etiketini duvara bindiriyor).
  Mutfak tezgâhı (duvar katısı sanılan kalın parça, mutfak yanında) etiket yasağından çıkarıldı (kullanıcı mutfak
  etiketlerini tezgâh üstüne koyuyor). Armatür kutusu tanınmayan klozet/lavabo: mimari çizgi poligonundan kutu
  (`dus_tekneleri`). MTEXT mahal yazısı sütunda kayıyorsa kutu yüksekliği kayan satırları da kapsar.
  Ölçüm: `python3 motor/sihhi2/etiketsiz_say.py [dxf ...] [--liste]` (parça ≥ 20 cm, 30 cm içinde 'n SB';
  "sıkı" = etiket yalnız en yakın parçaya sayılır; kılavuzlu etiket ayrıca sayılır).
- **R2 daire girişi şaftsız**: `saft_poligonlari` = havalandırma şaftları + 'k.bac.'/'en. odası' yazılı duvarla
  çevrili < 1 m² hücre (1./2. kat k.bac. antre-kor. poligonuna karışıyordu) -> temiz su maliyeti sonsuz. Kapı yanı
  dolu duvar adayı şafta < 25 cm ise **kapıdan giriş** (`kapi_girisi`): düşey merdiven holünde, şaftın uzak
  tarafındaki kasanın 10 cm içinde (açıklık duvar katısından ölçülür), hat kapı açıklığından antreye (kullanıcının
  1./2. kat D5/D8 yeri). Diğer dairelerin girişi değişmedi.
- **R3 aspiratör notu**: debi kullanıcınınki gibi mahal adından — banyo 160, wc-banyo / wc+banyo / wc-duş 80
  (`m3/h-50 pa`, Ø150 mm); model `hav_saftlari` debisi aynı değerden (Ş3 = 480). Tek tip h 15, sığmazsa h 12
  (h 10/8 ve 2 satır kalktı). Not hat / yazı / sembol / duş teknesi (`tekne` yasağı: armatür kutusu ya da mimari
  dikdörtgen + köşegen) üstüne binmez. Kendi ıslak hacmine sığmazsa kullanıcı gibi ıslak hacim duvarına ≤ 30 cm
  bitişik aynı dairenin hol / kuru mahaline, kılavuzsuz (1. kat D5 wc-banyo -> oda, D6 wc-duş -> hol). 1. kat D6
  wc-duş notu artık var.
- **R4 BM görünür branşman** (`makine_bransmani`): omurga BM/ÇM kutusunun kenarından geçip ucunda bitiyorsa kutunun
  omurgadan uzak yarısında bağlantı noktası + 45° kısa branşman (kullanıcının B.M. dairesi gibi); omurga o düğümde
  biter. Z D2, 1. kat D4, 2. kat D7.
- **K1 küçük duş (D3/D5/D8, P9)**: lavabo tezgâhı mahal poligonundan kesik olduğu için duvar dibi aday cezalıydı;
  armatüre son 40 cm yaklaşım cezasız -> hat P9'dan duvar dibinden iner, alt duvar boyunca lavaboya (süzgeç
  hattın üstünde, çapraz yok; Z duş doğrulaması da artık geçiyor).
- Geliştirme: `S2_ADIM=kaydet|yukle` kat çizimi sonrası durumu `/tmp/claude-0/s2/adim.*`'a yazar / oradan yalnız
  etiketleri yeniden çalıştırır. Karşılaştırma kırpımları: `python3 motor/sihhi2/kars_png.py` ->
  `kutuphane/arastirma/kontrol_png/sihhi_tur4_uretici/`.

## Tur 3 (15.10.2026) — kontrolör tur 2 RED (KONTROL_SIHHI_TUR2.md, Y1–Y5) düzeltmeleri
- **Y1** `_pis_omurga`: omurgaya bağlanamayan armatür artık adayı geçersiz kılar (+100000; eskiden +1000 ceza ile armatür
  SESSİZCE düşüyordu → 1./2. kat D5/D8 wc-banyo lavabosu bağlantısızdı). Lavabo 45° + dik branşmanla omurgaya bağlı;
  P8 SB 25/25/25 = 75 (eski 25/23/23), şema bloğu modelden. `S2_DEBUG_OMURGA=1` aday dökümü.
- **Y2 etiket**: pis su `Ø/SB` önce hattın üstünde (parça ortası, hat yönünde); sığmazsa yine hattın üstünde ama başka
  boru yazının altından geçebilir (`gevsek`, kullanıcı çiziminde de var); sonra `etiket_kisa`: yazı KENDİ mahallinde,
  kılavuz ≤ 60 cm (`KIL_MAX`), duvar/kapı/başka hat/sembol kesmez; o da olmazsa parça etiketsiz kalır (uyarı). Eski uzun
  halka araması (35–300 cm) kat planında kullanılmıyor. Balkon içine etiket yok (hat balkonda değilse).
  Temiz su `inç/MB` yatay; yatay hatta kanca hatta dik (31/22/14/40), düşey hatta kanca hat boyunca + 8 cm çentik
  (kullanıcı bloğu döndürülmez). Kanca duvar/kapı kesmez; yazı başka daire/ortak/balkona girmez.
- **Y2 balon**: P balonu önce kullanıcı ofsetinde (`tasarim_new_block.json` balon_ofset; mimari yazı ve merdiven basamağı
  "duvarı" engel sayılmaz — kullanıcı P3/P5/P6'yı merdivende yazıların üstüne koyuyor), kılavuz ıslak hacimde ≤ 30 cm
  (P9 duşu kesmez); yedek aramalar en çok 115–130 cm.
- **Kılavuz rengi**: `ROTAS-SEMBOL-KILAVUZ` ACI 9 (açık gri; yağmur ACI 3 ile karışmaz). `pafta.py` birleştirmede
  katman rengini sabitler (önce detay lejantı ACI 3 ile tanımlıyordu).
- **Y3 aspiratör**: metin her yerde `Wc Aspiratörü / 160 m3/h-50 pa / Ø150 mm` (model debisi 80 × hacim değişmedi,
  izometri için). Not YALNIZ kendi ıslak hacminde, hat/yazı/sembol kesmeden (h 15 → 12 → 10 → 8, 3 satır; sonra 2 satır);
  olmazsa şaft grubundaki diğer ıslak hacim; o da olmazsa aynı dairenin bitişik HOL/antre'si, sembolden ≤ 60 cm kılavuz
  (kapı/başka ıslak hacim kesmez; yatak odası yok). Kalan: 1. kat D6 wc-duş (komşusu yalnız yatak odası/merdiven) notsuz.
- **Y4**: ıslak hacme giren temiz su çiftinin etiketi giriş noktasından ±15–70 cm'de, hattın üstünde.
- Engel ekleri: küresel vana sembolü (6×6) ve kontrolörün eviye/BM/ÇM kutusu etiket engeli.
- Ölçüm (tam şerit): kılavuz Z 26 / 1. kat 23 / 2. kat 25 (9 P + 9 YB balonu + 5–7 kısa etiket + 1 aspiratör), > 60 cm: 0,
  en uzun 59,5. etiket_kontrol E1–E5 kat planında 0 / 8 (E2 = P3/P5/P6 balonu basamak no / "Döş.Mermer" üstünde,
  kullanıcı ofseti) / 0 / 0 / 0. Kontrolör: T07 etiket–armatür 0, etiket–etiket 0; etiketsiz pis su parçası 26/29/27.

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
- Renkler: kılavuz 9 (birleşik şeritte de 9, pafta.py), pafta yazısı 7 (ACI 250–255 / 8 yazı yok).
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
