# SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI — KESİN TARZ (14.10.2026)

Bu belge, konut sıhhi tesisatı **açılımlı kolon şemasının** motor tarafından nasıl çizileceğini tek yerde toplar.
Tek referans kullanıcının kendi çizimi `ornekler/new_block.dxf` (Metra Mimarlık, Z+2, 9 daire); ölçüler o dosyadan
ezdxf ile okunmuştur (birim cm, model uzayı). Referans kesitleri: `kutuphane/arastirma/kolon_semasi_ref/01..08_*.jpg`.
Reddedilen şemamız: `kutuphane/arastirma/geri_bildirim/RED_sihhi_kolon_semasi_sayac_kapida_yanlis_tarz.png`.

README "(C) SIHHİ RED" bloğu ve "(B) revizyon talimatı" ile birlikte okunur. Çelişki olursa README önce gelir
(özellikle: MTY blokları KULLANILMAZ; semboller saf geometriyle, kullanıcının KOLON blok görünümünde çizilir).

---

## 1. DOĞRU TARZ — new_block şemasının anatomisi (ölçülü)

### 1.1 Genel yerleşim
```
                 depo (çatı)        P9   P8   P7 ...                P1        YB1..YB9
   ┌─┐ ┌────────────────────────────────────────────────────────────────┐ ┌─┐ │ │ │ │
   │2│ │   D8 blok        D7 blok          D9 blok                      │ │2│ │ │ │ │
   ├─┤ ├────────────────────────────────────────────────────────────────┤ ├─┤
   │1│ │   D5 blok        D4 blok          D6 blok                      │ │1│
   ├─┤ ├────────────────────────────────────────────────────────────────┤ ├─┤
   │Z│ │ sayaç grubu  D3 blok   D2 blok   D1 blok                       │ │Z│  "YAĞMUR SUYU KANALINA GİDER"
   └─┘ └────────────────────────────────────────────────────────────────┘ └─┘
   Şebekeden   T.K.→R     T.K.→R    T.K.→R   (kolon dipleri band altında)
                        ─── rögar şeması: R1 ─ R2 ─ R3 ─ R4 ─ PB (altta, ayrı) ───
```
- **Kat bantları:** yükseklik **400**, tüm pafta boyunca kesintisiz yatay çizgiler (`MTY-BORU` katmanı, renk bylayer; şema çerçevesi 6629 genişlik).
  Alt bant ZEMİN. KAT, üstte 1. KAT, 2. KAT. Her iki uçta **50 genişliğinde kat etiketi sütunu**; "ZEMİN. KAT" / "1. KAT" / "2. KAT"
  yazısı **h=25, 90° döndürülmüş, kırmızı (renk 1)**, sütun ortasında.
- **Üst bant çizgisi = çatı döşemesi.** Depo, havalıklar ve kolon etiketleri bu çizginin ÜSTÜNDE.
- **Daire blokları** bantların içinde yan yana; aynı plan konumundaki daireler üst üste gelir (zemin D3-D2-D1, 1. kat D5-D4-D6, 2. kat D8-D7-D9).
  Daire etiketi mor çift daire **Ø110** (dış r=55, iç r=49; yazı h=40 mor) bloğun sağ üst kısmında, **band altından +268** (üstten −132).
  Kombi (yazı "DUVARA ASILABİLEN HERMETİK KOMBİ KAPASİTE: 24 kW", h≈5) daire etiketinin hemen sağında, band altından ≈+290.
- **Pis su kolonları P1..P9** daire bloklarının ıslak hacim köşelerinde; plan sırasına göre değişken aralık (≈400–1300).
  Kolon etiketi mor çift daire **Ø55** (r 27,5 / 24,5; yazı h=20) **üst bant çizgisinden +73** yukarıda, altında havalık şapkası.
- **Sağda** yağmur şeması: YB1..YB9 yeşil dikey hatlar, sağ etiket sütunundan 36 sonra başlar, **60 aralık**, band altından −20'den üst çizgi +10'a;
  etiket daireleri (Ø55, yeşil) üst çizgiden +37; altında kırmızı çerçeveli "YAĞMUR SUYU KANALINA GİDER" kutusu (549×66, band altı −58..−124).
- **Altta** rögar şeması, kolon diplerinden en az **350** aşağıda, ayrı grup (bkz. 1.7).

### 1.2 Teknik merkez — şebeke girişi, ana sayaç, depo, daire sayaç grubu (sol alt, ZEMİN bandı)
Kesit: `02_new_block_sol_sebeke_sayac_depo.jpg`, `03_new_block_sayac_grubu.jpg`, `04_new_block_depo_kolon_ustu.jpg`.
- **"Şebekeden"** yazısı (h 16,6) zemin band altının 38 altında, sol etiket sütununun hemen sağında; hat band altından **+15** yükseklikte yatay girer.
- Giriş sırası (soldan sağa, aralık 25): **küresel vana → ana sayaç → çek valf → küresel vana** → dikey hat **depoya çıkar** (x=sol sütun+125, çatı üstündeki depoya; depo girişinde vana + flatör).
- **Depo çatıda** (üst bant çizgisi üstünde, sol): "KULLANIM SU DEPOSU V=3m3" (yeşil, h 15), havalık, taşma 2", boşaltma (vanalı), su seviye göstergesi,
  betonarme kaide taralı. Depo çıkışı altta: **küresel vana + çek valf**, sonra ikinci dikey hat (ilkinin 32 sağında, yanında akış okları ↓) **zemine iner**.
- İnen hat zeminde **çek valf**ten geçip **+15 hattına** döner; x=sol sütun+173'te **kollektör dikmesi** yukarı çıkar (+15 → +112).
- **Daire sayaç grubu** (kollektör üzerinde, 9 daire = 5 + 4 sıra):
  - Sıra aralığı **20** (y = band altı +32, +52, +72, +92, +112), sıra boyu **148**, ikinci grup kollektörü 161 sağda (ilk grubun uçlarını geçtikten sonra).
  - Her sırada kollektörden itibaren: **küresel vana (+27) → pislik tutucu (+52) → su sayacı (+74, Ø14 daire + 45° ok) → çek valf (+96) → küresel vana (+121)**;
    uçta 10 uzunluğunda dikey "çıkış" tırnağı. Sembol genişlikleri ≈20, yükseklik ≈10–15; hepsi kırmızı (`MTY-VANA` tarzı, renk 1).
  - Sayaç grubu **yalnız zemin bandında**; kat bantlarında ve daire kapılarında sayaç YOK. Daire kolonları (D hattı) her dairenin kendi bloğunda band altından yukarı çıkar.
- Şebeke/ana hat çapı ve "DBK/YB" yazısı dikey hat üzerine YAZILMAZ; sadece depo ve sayaç yazıları.

### 1.3 Daire bloğu — temiz su
Kesit: `05_new_block_banyo_armatur_mb.jpg`.
- **Daire besleme dikmesi** (soğuk, mavi `MTY-SOGUKSU-BORU`): bloğun sol kenarında band altından **+250**'ye çıkar; üzerinde **+125**'te
  etiket "1 1/4\" / 13.5 MB" (sola açılan kanca, yazı h 10, 4 satır: çap / MB — daire toplamı).
- **+250** kotunda yatay dağıtım (soğuk); ıslak hacim grubunun üstünde **+130** kotuna iner ve armatür sırası boyunca yatay gider.
- **Sıcak su** (kırmızı kesikli `MTY-SICAKSU-BORU`) **kombiden başlar** (bloğun sağında), soğuğa **paralel, 5 cm yukarıda/yanında** (+135 ve +245 kotları);
  mutfaktan banyoya kadar aynı güzergâh; iki hat hiç kesişmez. Daire dışından sıcak su gelmez.
- **Armatür branşmanları**: +130 hattından aşağı dikey (soğuk mavi düz, sıcak kırmızı kesikli, yan yana ≈5 aralık), armatürün batarya noktasına iner.
  Lavabo/eviye/duş: iki branşman (soğuk+sıcak); rezervuar, çamaşır/bulaşık makinesi: yalnız soğuk.
- **MB etiketi** (`MTY-TEMIZ SU CAP MB` görünümü, ölçek 10): branşmanın **80 solunda**, hat kotunda (+130) duran kanca; yazılar hattın ÜSTÜNDE,
  4 satır (h 10, satır aralığı 15): `1"` / `3.25 MB` (soğuk) / `1"` / `3.25 MB` (sıcak); yalnız soğuk varsa 2 satır. Her hat parçasına **bir** etiket.
  Branşman uçlarında armatür yanında ayrıca "Ø20 / 0.75 MB" (h 10, yeşil) — armatür bağlantı değeri, armatürün iki yanında.
- **Armatür sembolleri — yan görünüş, kullanıcının KOLON blok görünümü** (cyan/sarı ince çizgi, band altı çizgisine oturur):
  lavabo (konsol + sifon + batarya), ayna (sarı, +250..+290), rezervuarlı klozet, duş bataryası (duvar bataryası + hortum, sarı sabunluk),
  eviye (tezgâh altı kesit), çamaşır/bulaşık makinesi (kare gövde, yuvarlak kapak). Armatür aralığı **130** (ıslak hacim içinde), hacimler arası boşluk ≈200.
  Kutucuk/plan görünüşü, "T" şeklinde lavabo, klozet tankı üstte ayrı kutu gibi gösterimler YASAK.

### 1.4 Daire bloğu — pis su
Kesit: `06_new_block_pissu_toplama_sb.jpg`.
- **Yatay toplama hattı** band altı çizgisinin **50 altında** (döşeme içinde), **çift çizgili PVC** görünümü (dış hat kahverengi 43 / eksen mor 211),
  parça boyu 100, muf halkaları; soldan sağa kolona doğru akar.
- Her armatürden **dikey iniş** (çift çizgi) band çizgisinden toplama hattına; toplama hattına **45° PVC çatal** ile bağlanır (çatal 37×55).
  Yer süzgeci: sarı ızgara sembolü band çizgisi üstünde + kısa iniş.
- **Branşman SB etiketi** her inişin sağında, inişe bitişik: `Ø50` / `2 SB` (h 10, mor, iki satır) — armatür SB değeri.
- **Hat SB etiketi** (`MTY-PIS SU CAP SB` görünümü): her toplama parçasının üstünde, parçanın **çatal öncesi 80 solunda**, kanca hatta iner:
  `Ø70` / `13 SB` (kümülatif). Yazılar hattın ÜSTÜNDE, hattın ve çatalın üstüne BİNMEZ.
- Toplama hattı kolona **45° çatal** ile girer; kolon çift çizgili dikey PVC, mor eksen.

### 1.5 Kolon dibi (ZEMİN bandı altı)
Kesit: `07_new_block_kolon_dibi_tk_rogar.jpg`.
- **T.K. (temizleme kapağı)**: band altından **+24** yukarıda, kolon ekseninin **24 solunda** kırmızı daire r=10 (iki küçük vida dairesi, üst-alt 20 boyunda çizgiler),
  yazı "T.K." h 10 kırmızı dairenin solunda. Kolonun üzerinde, bantların İÇİNDE; yatay hattın ucunda DEĞİL.
- Kolon band altını geçer, **−78**'de 45°/90° PVC dirsek ile sağa döner, **−98**'de sarı ok sembolü + mavi "R" (h 25) — rögara gider.
- Kolon toplam etiketi `Ø100` / `25 SB` (h 10, mor) kolon ekseninin **70 solunda, −80 kotunda**, kanca dirseğe.
- Dip çizgisi: kolon alt ucu band altından en fazla −110; rögar şeması bu kotun çok altında (≥ −350).

### 1.6 Kolon üstü
- Kolon üst bant çizgisini **+60** geçer, havalık şapkası (kahverengi, h≈20), üstünde kolon etiketi dairesi (merkez +73).
- Depo ve kolon etiketleri aynı şeritte; etiketler yan yana gelince aralarında ≥ 20 boşluk.

### 1.7 Rögar şeması (ayrı, altta)
Kesit: `08_new_block_rogar_semasi.jpg`.
- Rögarlar **R1 → R2 → R3 → R4 → PB** yatay sırada, kare kutu (dış 50×50 mavi, iç 40×40 sarı), içinde "R1" mavi h≈25; altında kesit kutusu ve
  "70x70 / h:-70cm" (gri h 8). Aralık ≈ 290.
- Rögarlar arası mor düz hat; üstünde sarı ok ve "%1 EĞİM / Ø150" (sarı h 12).
- Her rögarın üstünde ona bağlanan kolon etiketleri (Ø55 daire, P1..P9) ince mor hatla rögara iner; etiketler yan yana/alt alta dizilir (2+2 dizilim), üst üste gelmez.
- Başlık yok (bu paftada "RÖGAR ŞEMASI" yazılmıyor); yazılacaksa şemanın ALTINA, kolon diplerinden uzağa.

### 1.8 Katman ve renkler (ROTAS- öneki ile yeniden adlandırılır, görünüm aynı kalır)
| Öğe | Katman (MTY adı → ROTAS adı) | Renk / çizgi |
|---|---|---|
| Kat bantları, etiket sütunları | MTY-BORU → ROTAS-SEMA-BANT | bylayer (7), kat yazısı 1 |
| Soğuk su | MTY-SOGUKSU-BORU → ROTAS-SOGUKSU | 5 düz |
| Sıcak su | MTY-SICAKSU-BORU → ROTAS-SICAKSU | 1, BASMA HATTI (kesikli) |
| Şebeke/depo hatları | TEM.SU → ROTAS-TEMIZSU-ANA | 5 |
| Vana/sayaç/çek valf/pislik tutucu | MTY-VANA → ROTAS-VANA | 1 |
| Pis su PVC (dış hat) | MTY-PVC → ROTAS-PVC | 43 |
| Pis su eksen / etiket | MTY-PISSU-CAP → ROTAS-PISSU-CAP | 211 |
| MB etiketi | MTY-TEMIZSU-CAP → ROTAS-TEMIZSU-CAP | 101 (yeşil) |
| Kolon/daire etiket dairesi | → ROTAS-KOLONNO | 6 dış, 7 iç |
| Armatür | MTY-TEFRIS → ROTAS-TEFRIS | 4 (cyan), aksesuar 2 (sarı) |
| Yağmur | MTY-YAGMUR-BORUSU → ROTAS-YAGMUR | 3 |
| Rögar | MTY-ROGAR → ROTAS-ROGAR | 5 / 2 |

---

## 2. YANLIŞ TARZ — reddedilen şemamızın hataları (madde madde)
Görüntü: `geri_bildirim/RED_sihhi_kolon_semasi_sayac_kapida_yanlis_tarz.png`.

| # | Hata (RED) | Doğrusu (new_block) |
|---|---|---|
| 1 | "D1 SAYAÇ (KAPIDA)", "D6 SAYAÇ (KAPIDA)": her katta, daire kapısında sayaç sembolü ve kırmızı yazı | Sayaçlar YALNIZ zemin bandında, şebeke girişinin yanında kollektör üzerinde toplu (1.2). Kat bandında/daire girişinde sayaç, vana, yazı YOK |
| 2 | Sol kenarda tek dikey ana kolon, her kata kapıdan branşman ("ŞEBEKEDEN (SASKİ) Ø32 – ANA SAYAÇ (BİNA GİRİŞİ)", "Ø32 DBK 52.0 YB" dikey yazı) | Sol kenarda yalnız şebeke→depo ve depo→sayaç grubu dikmeleri; daire besleme dikmesi her dairenin KENDİ bloğunda, sayaç grubundan çıkar; dikme üzerine DBK/YB yazısı yazılmaz |
| 3 | Kat bandında sayaç/besleme çizgisi: temiz su yatay hattı bant çizgisiyle aynı hizada, bant sınırı okunmuyor | Bantlar 400 yüksek, kesintisiz; temiz su dağıtımı band altından +130 ve +250 kotlarında, bant çizgisine binmez |
| 4 | Depo yok; çatı/üst bant kavramı yok | Depo çatıda, üst bant çizgisinin üstünde solda; kolon etiketleri ve havalıklar üst çizginin üstünde |
| 5 | Armatür sembolleri yanlış tarz: klozet = üstte ayrı kutu + gövde, lavabo = çift trapez, duş = batarya + boşta "L" çizgisi, çamaşır makinesi gövdesi ile "Ø20 10" etiketi iç içe | Yan görünüş, kullanıcının KOLON blok görünümü (1.3): lavabo+ayna, rezervuarlı klozet, duvar bataryası, kesit eviye, makine; bant çizgisine oturur |
| 6 | Etiket yığılması: her branşmanda "Ø20 / 0.5" + "Ø25 / 7.5 YB" + armatür altında ayrı sayılar; birim "YB" | Her hat parçasına TEK etiket (kanca + 2/4 satır), armatür yanında yalnız "Ø20 / 0.75 MB"; birim **MB** (temiz) ve **SB** (pis); yazılar hattın ÜSTÜNDE, birbirine ve hatta binmez |
| 7 | Pis su SB etiketleri ("Ø100 25 SB", "Ø70 15 SB") hattın ALTINDA, çatal ve iniş çizgileriyle çakışık; kolon etiketi "Ø100 / 50 SB" kolon boyunca 90° döndürülmüş | Hat etiketi hattın üstünde, çataldan 80 solda; iniş etiketi inişin sağında; kolon toplamı kolon dibinde, solda, döndürülmeden (1.4–1.5) |
| 8 | "T.K." yatay toplama hattının SAĞ UCUNDA (kolondan uzak), hat sonunda boşta | T.K. kolonun ÜZERİNDE, band altı +24'te, kolon ekseninin 24 solunda kırmızı daire (1.5) |
| 9 | Pis su tek çizgi mor kesikli; çatal yerine kısa eğik çizgi; armatür inişleri siyah | Çift çizgili PVC görünümü (kahverengi dış + mor eksen), 45° çatal/dirsek, muf halkaları |
| 10 | Rögar şeması başlığı ("RÖGAR ŞEMASI (BİNA DIŞI, DOĞU CEPHESİ) – KOLON DİPLERİ ZEMİN KOTUNDAN AYRI AYRI") kolon dipleri ve T.K. üzerine biniyor; rögar şeması kolon diplerine yapışık | Rögar şeması kolon diplerinden ≥350 aşağıda, ayrı grup; başlık yazılmaz (yazılacaksa şemanın altına) |
| 11 | Rögar sembolü küçük kutu, "R1" kutunun altında ayrı; kolon etiketleri rögara kesikli mor hatla iniyor; "%1" ve "Ø150 63 SB" hattın altında | Rögar 50×50 mavi kutu + içinde R1, altında kesit kutusu ve "70x70 h:-70cm"; P etiketleri ince düz hatla; hat üstünde sarı ok + "%1 EĞİM / Ø150" |
| 12 | Kat etiketi sütunu yok ("ZEMİN KAT" yazısı yok) | Her iki uçta 50 genişlik sütun, 90° döndürülmüş kırmızı kat adı |
| 13 | Siyah zemin önizleme, yazı boyları karışık (h 7–25) | Beyaz zemin, yazı boyları: etiket 10, kat adı 25, daire etiketi 40, kolon etiketi 20, R 25 |
| 14 | Yağmur şeması yok, "YAĞMUR SUYU KANALINA GİDER" yok | Sağda YB hatları + kutu (1.1) |

---

## 3. MOTOR ÇİZİM KURALLARI (sihhi2 için; birim cm, y yukarı)

Değişkenler: `H=400` (bant yüksekliği), `y0_k` = k. katın bant alt çizgisi (zemin: `y0`, üst katlar `y0 + k·H`), `y_top = y0 + n_kat·H`.

1. **Çerçeve:** sol etiket sütunu `[x0-50, x0]`, sağ sütun `[x1, x1+50]`; bant çizgileri `x0-50 … x1+50` boyunca her `y0_k` ve `y_top`.
   Kat adı TEXT h 25, rot 90, renk 1, konum `(x0-12.5, y0_k + 52)`.
2. **Teknik merkez (zemin, sol):** "Şebekeden" h 16,6 `(x0+12, y0-38)`; giriş hattı `y0+15`, x: `x0+18 → x0+334`;
   semboller `x0+36` küresel, `x0+62` ana sayaç, `x0+87` çek valf, `x0+112` küresel; depo besleme dikmesi `x=x0+125` (y0+15 → depo girişi);
   depo dönüş dikmesi `x=x0+158` (depo çıkışı → y0+15), zeminde `x0+141` çek valf; kollektör dikmesi `x=x0+173`, `y0+15 → y0+112`.
   Sayaç sıraları: `y = y0+32+20·i` (i=0..4), kollektör dikmesinden 148 sağa; 2. grup kollektörü `x0+334`, sıralar i=0..3, `y0+32+20·i`.
   Sıra içi ofsetler (kollektörden): 27 küresel, 52 pislik tutucu, 74 sayaç, 96 çek valf, 121 küresel, 148 uç tırnağı (10 dikey). Daire sayısı > 10 ise 3. grup 161 sağa.
   Kat bantlarında, daire bloklarında, kapı önlerinde SAYAÇ/VANA/YAZI YASAK (kontrolör kuralı).
3. **Depo (çatı):** gövde 150×135 benzeri dikdörtgen, sol kenarı `x0+150`, tabanı `y_top+8` (taralı kaide `y_top..y_top+8`);
   yazı "KULLANIM SU DEPOSU / V=… m3" h 15 yeşil ortada; havalık+taşma sol üst, boşaltma sol alt (vanalı), seviye göstergesi sağ kenar,
   giriş üstten flatör + küresel vana, çıkış tabandan küresel vana + çek valf → dönüş dikmesi.
4. **Daire bloğu** (sol kenarı `xd`, sağ kenarı `xd+W`, W = ıslak hacim sayısına göre 1700–2300):
   - besleme dikmesi `x=xd`, `y0_k → y0_k+250`; etiket (*U160 tipi, sola kanca) `(xd, y0_k+125)`, satırlar daire toplam çap/MB.
   - soğuk ana hat `y0_k+250` (xd → ilk ıslak hacim), sonra `y0_k+130` armatür sırası boyunca; sıcak hat `+245 / +135`, kombi x'inden başlar.
   - armatür merkezleri `xa_j = xh + 130·j` (xh: ıslak hacim başlangıcı), hacimler arası ≥200; armatür tabanı `y0_k` üzerinde.
   - branşmanlar `xa_j±2.5` dikey `y0_k+130 → armatür bağlantı kotu` (new_block'tan ölçülen: lavabo ≈+80, duş bataryası ≈+90; eviye, klozet rezervuarı ve makine için armatür bloğunun bağlantı noktası esas alınır, ≈+90 / +40 / +60).
   - MB etiketi `(xa_j-80, y0_k+130)`, 4 satır h 10 yukarı; armatür bağlantı etiketi `Ø20 / 0.75 MB` `(xa_j±18, y0_k+45)`.
   - daire etiketi daire Ø110 merkez `(xd+W-230, y0_k+268)`; kombi dikdörtgen 25×45 `(xd+W-40, y0_k+230…275)`; kombi yazısı h 5 üstünde.
5. **Pis su:** toplama ekseni `y0_k-50`; iniş `xa_j`, `y0_k → y0_k-50` çift çizgi (genişlik Ø/10 ≈ 5–10); çatal 45° (`xa_j-27…xa_j+10`); parça 100'lük PVC boru blokları;
   iniş etiketi `(xa_j+12, y0_k-25)` 2 satır h 10; hat etiketi `(xa_j-80, y0_k-50)` kanca yukarı, 2 satır h 10, kümülatif SB.
   Kolon `xp` (ıslak hacim köşesi), toplama hattı kolona 45° çatal ile; kolon `y0_k-110 → y_top+60` çift çizgi.
6. **Kolon dibi:** T.K. daire r 10 `(xp-24, y0+24)` + "T.K." h 10 `(xp-54, y0+18)`; dirsek `(xp, y0-78)`; sarı ok + "R" h 25 `(xp+20, y0-98)`;
   kolon etiketi `(xp-70, y0-80)` 2 satır (`Ø100 / 25 SB`).
7. **Kolon üstü:** havalık şapkası `(xp, y_top+40)`; etiket dairesi Ø55 `(xp, y_top+73)` yazı h 20.
8. **Yağmur şeması:** YB_i hattı `x = x1+86+60·i`, `y0-20 → y_top+10`; etiket dairesi `(x, y_top+37)` yeşil; kutu `(x1+36 … x1+585, y0-58 … y0-124)` kırmızı çerçeve, yazı h 20.
9. **Rögar şeması:** sol üst `(xr, y0-450)`; rögar `k`: kutu 50×50 `(xr+290·k, …)`, iç 40×40, "R{k}" h 25 mavi ortada; kesit kutusu 50×35 altında, "70x70 / h:-70cm" h 8 gri solda;
   bağlantı hattı mor; "%1 EĞİM / Ø150" sarı h 12 üstte + sarı ok; P etiketleri Ø55 rögar üstünden +110 ve +190 kotlarında 2'li sütunlar, ince hatla rögara.
   Son kutu "PB". Başlık yazılmaz.
10. **Yazı çakışma kontrolü** (tcheck): tüm TEXT/ATTRIB kutuları birbirine, bant çizgilerine, hatlara ve sembollere binemez; ihlalde etiket kanca boyu 80→120 uzatılır veya satır sırası
    yukarı kaydırılır. Önizleme beyaz zeminde, kullanıcının çizimiyle yan yana karşılaştırılır (kontrolör ajan).
11. **Semboller saf geometri** (README-B): MTY INSERT kullanılmaz; her sembol LINE/ARC/CIRCLE/LWPOLYLINE ile, yukarıdaki görünüm ve ölçülerde kendi bloğumuza (`ROTAS-…`) çizilir.

---

## 4. WEB TEYİDİ (sayaç konumu ve şema düzeni)
- **İZSU Su Sayacı Düzenleme Esasları (2013)**: farklı aboneliklere ait sayaçlar **aynı yerde toplanır**; sayaç yeri bina giriş kapısının parsel sınırına en yakın noktasında /
  çok katlı binalarda bina girişinin sağı-solu (md. 3.1–3.2); ana kolon ortak alandan geçer, bağımsız bölümden geçemez (2.2); kollektör ana kolondan küçük olamaz (2.3);
  sıra: **giriş vanası – filtre – sayaç – çek valf – çıkış vanası** (1.4.4, Şekil 1.2); sayaç öncesi 10D, sonrası 5D düz boru; kollektörde uçlar arası düşey 22 cm.
  https://www.izsu.gov.tr/CKYuklenen/IZSU-SuSayacDuzenlemeEsaslari-2013.pdf
- **Çankırı Karatekin Üni. sıhhi tesisat ders notu**: soğuk su şematik çizimi şehir şebekesi girişinden başlar, **ana sayaç ve dağıtıcı (kollektör)** çizilir; çizim bodrum/zemin katta başlar;
  atık su kolonları soldan sağa numaralanır ve **çatıya kadar uzatılır**; bodrum hatları bina dışındaki rögarlara iletilir.
  https://websitem.karatekin.edu.tr/user_files/hdag/files/20241022_c6eb214b44dd4131b70a353d95795e0a.pdf
- **KTÜ sıhhi tesisat ders notu (sihhi_4.pdf)**: kat boruları kolonlara **45° dirseklerle** bağlanır; **her kolonun en alt erişilebilir noktasına temizleme borusu**;
  rögar 50×50×80; yatay borular eğimli; havalandırma yoksa kolon çatı üstüne çıkarılır (s. 41–46).
  https://ebaydar.ktu.edu.tr/files/sihhi_4.pdf
- **MEGEP Sıhhi Tesisat modülü (MEB)**: sayaç montajı rögar içine veya niş/sayaç kutusuna yapılır; atık su tesisatı ana boru–kolon–kat borusu–havalık yapısı; kolonlar rögara bağlanır.
  https://maol.meb.gov.tr/web/mem/alanlar/tesisat/dbf/sihhi_tesisat.pdf
- **Ticari örnek setler** (`kutuphane/ornek_mekanik/ada_hayat/sema/14_AVM_Temizsu_Kolon_Semasi_sema_02.png`, `16_AVM_Pissu…`, `aselsan_teknopark/sema/05_Temiz_Su…_sema_04.png`):
  aynı mantık — kat çizgileri solda kat adıyla, armatürler yan görünüş kat çizgisine oturur, besleme ve sayaç en altta (bodrum/zemin), kolonlar numaralı.
  Bu setler yalnız mantık teyidi içindir; **tarz new_block'tan alınır** (README-C).

Sonuç: kullanıcının "sayaçlar zemin bandında, şebeke girişinde toplu; daire kapısında sayaç yok" talimatı hem idare esasları (İZSU) hem ders kaynaklarıyla uyumludur.

---

## 5. Kontrolör kontrol listesi (şema)
- [ ] Sayaç grubu yalnız zemin bandı solunda; kat bantlarında sayaç/yazı yok.
- [ ] Depo üst çizgi üstünde solda; kolon etiketleri üst çizgi üstünde; her kolonda havalık.
- [ ] Her daire bloğunda: D etiketi + kombi sağda; sıcak su kombiden; hatlar kesişmiyor.
- [ ] Armatürler yan görünüş (kullanıcı görünümü), bant çizgisine oturuyor; aralık 130.
- [ ] MB/SB etiketleri hattın üstünde, kanca ile; parça başına tek etiket; birimler MB/SB.
- [ ] Pis su çift çizgi PVC, 45° çatal; T.K. kolon üzerinde band altı +24; dirsek + ok + R altta.
- [ ] Rögar şeması ≥350 aşağıda, başlıksız; P etiketleri üst üste değil.
- [ ] Yağmur şeması sağda, kutu ile.
- [ ] tcheck sıfır çakışma; beyaz zemin önizleme new_block ile yan yana.
