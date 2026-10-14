# uctan_uca — new_block.dxf üzerinde uçtan uca sıhhi tesisat denemesi (14.10.2026, R4)

## R4 — new_block sıhhi düzeltmeleri (`nb4.py`, `sema4.py`, `cikti4.py`, `etiket4.py`, `ykontrol4.py`)
Çıktı: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R4.dxf` (R1-R3 korunur). Karşılaştırma: `KARSILASTIRMA.md` "R4"; özet `ozet_r4.json`.
```bash
cd /tmp/claude-0/uu4 && python3 /home/claude/rotas-cizim-motoru/motor/deneme/uctan_uca/nb4.py   # ~5 dk (R3 + R4 yamaları)
python3 /home/claude/rotas-cizim-motoru/motor/deneme/uctan_uca/cikti4.py    # yalnız son işlem (emit sonrası) tekrar
python3 /home/claude/rotas-cizim-motoru/motor/deneme/uctan_uca/ykontrol4.py <dxf>   # yazı-yazı çakışması
```
- `nb4.py`: `nb3` (R3) aynen çalışır, değişenler yama: çap etiketi ölçeği 10 (`k_cap`); `r3.Alan` → `AlanR4` (temiz su maliyetine pis su
  hattının ±4 cm bandı cezası `R4_PIS_CEZA`=30; ceza ile bir dairede kendini kesen öteleme / bağlanamayan armatür çıkarsa o daire cezasız
  yeniden çizilir); `zemin_sebeke4`: şebeke bina girişinden giriş holü ORTASINDAN (cepheden 60-180 cm içeride ortogonal duvar ışınlarıyla
  hol orta kotu) A* ile DBK'ya; daire mahalleri (salon / oda / antre-kor. / ıslak hacim / balkon) etiketten duvarlara dikdörtgenle kapalı
  (oda tanımada salon giriş holüyle birleşiyordu), duvar delme pahalı (kapıdan geçer), bina dışı kapalı, giriş basamakları duvar sayılmaz.
- `sema4.py` (sema3 kopyası): `sihhi_sema4` — çatı deposu → çatı dağıtım hattı (kolon havalıklarının üstünden) → her daire konumu için ADK
  inişi → her katta T → vana + DAİRE SAYACI + çek valf + giriş vanası (planla aynı: sayaç daire kapısında). Zeminde toplu sayaç YOK; şebeke
  ana (SASKİ) sayacı bina girişinde tek. `sayac_kesisme`: sayaç / ADK / dağıtım hatlarının diğer borularla kesişmesi (sonuç 0).
  SIHHİ DETAYLAR çerçevesi `kayit_kutusu` ile içerikten.
- `etiket4.py`: emit sonrası DXF'te yazı yerleşimi. Engel: bütün yazılar (mahal adı / alanı dahil) + plan sembolleri. Çap etiketi (öznitelikli
  INSERT) önce boru ekseninde kaydırılır, olmazsa boruya dik + kılavuz; serbest yazılar (aspiratör, şaft adı, EK süzgeç, kombi, ADK/DBK) grup
  halinde halka aramasıyla, maskesiyle birlikte taşınır, uzaklaşınca kılavuz çizgisi (`ROTAS-SEMBOL-KILAVUZ`).
- `cikti4.py`: cikti3 akışı + `etiket4` + pafta sonu lejant (`lejant4`: kendi ROTAS saf geometri bloklarımız, açıklama semboller2,
  PLAN ADET / ŞEMA ADET, boru çizgi örnekleri) + armatür adet + vana/sayaç/süzgeç/fan adet + boru metrajı; çerçeve içerikten.
  pafta_bitir'e dokunulmadı (semboller v1/MTY bağımlılığı burada semboller2 ile çözüldü).
R4 sonuç: yazı-yazı çakışması 0 (R3: 404), MTY 0, temiz su / pis su kesişmesi 0, köprü 0, yasak bölge 0, kolon-şaft 0, süzgeç 27/27, 45° dışı 0,
şemada sayaç hattı kesişmesi 0, pis su–temiz su planda üst üste 176 → 112, AUDIT 0.

## R3 — 14.10.2026 (B) revizyon talimatı (`nb3.py`, `r3.py`, `semb3.py`, `sema3.py`, `cikti3.py`)
Çıktı: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R3.dxf` (R1/R2 korunur). Karşılaştırma: `KARSILASTIRMA.md` "R3" bölümü; özet `ozet_r3.json`.
```bash
cd /tmp/claude-0/uu && python3 /home/claude/rotas-cizim-motoru/motor/deneme/uctan_uca/nb3.py   # ~4 dk
```
- `nb3.py`: R2 tanıma / kolon / rögar altyapısını (`nb.py`, `r2.py`) import eder, değişen adımları kendisi yapar: çift ıslak hacim etiketi birleştirme,
  "mek. havl." şaft poligonu, kolonu şafttan kendi mahalline öteleme, ıslak hacim başına tam 1 yer süzgeci (fazlası çıkar, yoksa EK),
  balık sırtı pis su, kesişmesiz temiz su, kat planında aspiratör + Ø150 + şaft, kontroller (`kontroller()`), `reg.pkl` (kesişme girdisi).
- `semb3.py`: `mtyblk.insert` / `mtyblk.find` yaması — motorun her MTY sembol çağrısı `ROTAS-` saf geometri bloğuna gider (iç katman 0).
  Geometri öncelikle `motor/deneme/semboller2/sembol2.py` (ortak MTY'siz kütüphane) bloklarından, eski yerleşim kutusuna oranla sığdırılarak;
  karşılığı olmayan (çap etiketleri: yalnız öznitelik, PVC dirsek) kendi çizimimiz. Eski bloktan yalnız sınır kutusu ve öznitelik yuvası okunur.
- `r3.py`: maliyet alanı `Alan` (koridor / mahal ortası tercihi, yatak odasında duvar dibi bandı, duvar delme cezası, yasak + şaft engel,
  kapılardan yürüme mesafesiyle daire etiketi, bina dışı kapalı), `otele` (miter öteleme), `duzelt` (Z-kırık temizliği), `agacta_kes`,
  `balik_sirti` (45° omurga + 45° tekil branşman), `kesisimler` (aynı ağ T-birleşimi serbest, diğer her temas kesişme).
- Temiz su kurgusu: sıcak su kombiden TEK hat, sıcak alan armatürleri sırayla; soğuk su ona 10 cm paralel; soğuk-alan armatürler ve daire girişi
  soğuk taraftan branşman (sıcak hat ızgarada engel). Kapalı kalan soğuk-alan armatür olursa çift hat oraya da uğrar. Paralel çift hattın T ile
  dallanması düzlemde kesişmesiz olamayacağından sıcak hat dallandırılmaz.
- `sema3.py`: `sema.py` kopyası; kolon şemasının sağına havalandırma kolonları (katlarda aspiratör, çatıda çatı tipi fan), SIHHİ DETAYLAR saf
  geometri tablolar (MTY detay bloğu yok), antet "DENEME R3", R3 notları.
- `cikti3.py`: köprü (xcheck.hops) YOK; ROTAS- katman öneki, blok içleri katman 0, MTY temizliği + `mty_kontrol` (sonuç 0 olmalı),
  kullanılan ROTAS sembolleri lejantı (örnek + adet) + armatür adet tablosu + boru metrajı.
R3 sonuç: kesişme/atlatma 0, MTY 0, yasak bölge 0, kolon-şaft 0, ıslak hacim başına süzgeç 27/27 = 1, boşta uç 0.
Sınırlar: `KARSILASTIRMA.md` R3 bölümü (sıcak hat dallanmaz, pis su - temiz su plan üst üste görünmesi sayılır ama kural değil, yazı yoğunluğu).

## R2 — 14.10.2026 kullanıcı standart talimatı revizyonu (`r2.py` + `nb.py`)
Çıktı: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R2.dxf` (R1 `NB_SIHHI_DENEME.dxf` önce/sonra için korunur). Karşılaştırma: `KARSILASTIRMA.md` §0.
- YB / SB yöntemi MTY ile aynı kaldı (MB / inç'e geçilmedi). Kolon–rögar çapı hesapla (`dn_sb`, zemin altı en az Ø100): kolon başı ≤ 75 SB → Ø100;
  kullanıcı Ø125 çizmiş (hesap gerektirmiyor, fark raporda).
- Kolon yeri (`r2.kolon_yeri2`): yalnız köşe adayları — her armatürden en yakın **gerçek duvara** (eksen çizgileri aynı doğruda birleştirilir, ≥ 100 cm;
  tezgâh / eviye / tekne çizgileri sayılmaz), sonra duvar boyunca köşeye. Puan: SB ağırlıklı boru boyu (mutfakta yalnız eviye), "mek. havl." şaftı
  (≤ 70 cm) ve komşu ıslak hacim bonusu, yasak bölgeye ceza; betonarmeden ≥ 15 cm. Numara kullanıcı biçimi P1.. ve kullanıcı sırası
  (daire → mutfak / wc / banyo / duş). Kullanıcı kolonlarına ortalama fark 115 → 58 cm.
- Kat planı farklılığı: üst kattaki `wc-banyo`, `wc-duş` tanınır; ıslak hacim → daire ataması kapılardan yürüme mesafesiyle (`r2.geodezik_daire`);
  zeminde karşılığı olmayan ıslak hacme o katta yeni köşe kolonu (P10), alt katlardan temele iner.
- Eksik ÇM / BM (`r2.ek_makineler`): banyo (yoksa wc+banyo / wc-banyo / wc-duş / duş) boş köşesine ÇM, mutfakta eviye yanına BM; planda "C'W' / B'M' (EK)".
- Balkon süzgeçleri (`r2.balkon_suzgecleri`): balkon etiketinden ortogonal dikdörtgen, en yakın yağmur inişine bakan köşe; Ø50 ayrı hat yağmur inişine
  (pis su ağına bağlanmaz).
- Temiz su: merdiven holünde daire kapılarının yanında ADK kolonları (giriş numaraları 300 cm içinde kümelenir: ADK-1 D1/D2, ADK-2 D3), her katta kolon →
  sayaç + küresel vana → kapı; ana hat yalnız ortak alan ızgarasında (tüm daire mahalleri kapalı). DBK ADK-2 yanında, şebeke bina girişinden düz.
  Daire içi: soğuk A* ağacı (kombi dahil) → `networkx` grafı; sıcak = kombiden sıcak armatürlere soğuk ağaç yolları, (±7, ±7) öteleme (duvar / yasak
  kesişimi en az olan yön) → yan yana paralel. Etiket (`MTY-TEMIZ SU CAP MB`) dal başına bir tane, ekleme noktası boru ekseninde, SO soğuk / SC sıcak.
- Yasak bölgeler (`r2.yasak_bolgeler`, `nb.yasak_kontrol`): betonarme kolon / perde, asansör boşluğu, enerji odası (etiketten ortogonal ışınla dikdörtgen);
  router'da yasak, pis su doğrudan hattı keserse dik kırık; sonda tüm hatlar 3 katta kontrol + ana hattın daire mahallerine girişi. Sonuç `ozet_r2.json` `yasak`.
- Depo kararı (`depo_karari`): mimaride bodrum + depo yeri → bodrum + hidrofor; yoksa çatı deposu (bu projede çatı).
- Pafta sonu "LEJANT VE MALZEME LİSTESİ": `semboller/sembol.py otomatik_lejant` (SIHHİ DETAYLAR bloğu eklenmeden önce sayılır) + armatür adet tablosu +
  boru metrajı (plandan ölçülen + kolon boyları).
- Rögar gruplaması: grup boyu ≤ 450 cm (kullanıcının 4 rögar dizilimi).
- Kolon no balonu (`kolon_etiketleri`): 16 yön × 5 mesafe arama, kat kayıtlarına (mimari + boru + yazı) değmeyen ilk konum, gerekirse kısa kılavuz çizgi.

R2 sınırları: D3 mutfak kolonu cephe köşesine düşüyor (kullanıcı tezgâh ucu); şema (p2 gsheet) sayaç grubunu hâlâ zemin bandında gösteriyor
(planda kat sayaçları); çatı planı, WC havalandırma izometrisi, kesit / görünüşler yok; çap etiket ölçeği 8 (kullanıcı 10).
`ozet_r1.json` / `ozet_r2.json`: karşılaştırmanın girdileri (nb.py `/tmp/claude-0/uu/nb_ozet_r2.json` yazar, karsilastir.py kopyalar).

## R1 (ilk deneme)

## Ne yapar
1. `mimari.py`: `ornekler/new_block.dxf.xz` -> `/tmp/claude-0/uu/new_block.dxf`; yalnız **MKDU0** (mimari) okunur,
   `MTY-*`, `M-*`, `RAST-*`, `TEM.SU` süzülerek `/tmp/claude-0/uu/new_block_mimari.dxf` yazılır.
   Tanıma (05_ALGORITMALAR §1, kural tabanlı):
   - kat pencereleri: zemin penceresi + kat kaydırmaları (oda etiketlerinden ölçüldü: 1. kat +2034, 2. kat +4082; temel -2629),
   - mahal etiketleri (MTEXT hizası dikkate alınarak merkez), ıslak hacim dikdörtgeni = etiketten 4 yöne ışın (duvar çizgileri),
   - armatürler geometri imzasıyla: klozet (birbirine değen yaylardan elips), lavabo (3 küçük daire: 2 batarya + gider),
     duş (gider + kare tekne / köşegen), eviye (mutfakta r≤3,5 gider), alaturka (r≈5 gider), yer süzgeci (kısa yatay+dikey çizgi
     ızgarası), çamaşır mak. (banyoda 50-72 cm boş kare), bulaşık mak. / kombi (mimari yazılarından),
   - betonarme kolon/perde: ANSI35 taramalı poligonlar, daire no: 1-9 rakam yazıları (giriş kapısı yanı).
2. `nb.py`: pis su kolonu = çapa armatürün (klozet / eviye / duş) en yakın duvarı boyunca köşe, betonarme dışına ötelenir;
   zeminde bulunur, üst katlarda aynı hizada. Kat içi pis su: kolondan başlayan en yakın-ağaç (eğik, armatürden kolona doğrudan,
   kullanıcı tarzı) + her parçada `MTY-PIS SU CAP SB` (Ø/SB, akış yukarısı toplamı). Temiz/sıcak su: merdiven holünde
   9 kolonlu kolon kutusu -> daire girişi -> armatürler (p2 `router.py` A*, odalar kapalı, betonarme yasak), kombiden sıcak su.
   Temel planı: bina dış hattı (duvarlardan morfolojik kapama) + kolonlar + kolon dipleri -> doğu cephesindeki rögarlar
   (kolon y kümelerine göre R1..Rn, A* ile kolon kesmeden) -> PB.
3. `sema.py`: p2 `gsheet.sihhi_sema` ile tek açılımlı kolon şeması (3 daire konumu x 3 kat, D1..D9), rögar şeması,
   `gsheet.yagmur_sema` (9 iniş), antet / notlar / lejant, `MTY-SIHHİ DETAYLAR` bloğu, pafta çerçeveleri.
4. `cikti.py`: kolon çakışma / boşta uç kontrolü (`gp.check`), köprü / yazı maskesi / tekrar temizliği (`xcheck`), p2 `emit.py`
   ile DXF, sonra model uzayı katmanlarına `ROTAS-` öneki (MTY blok tanımlarının iç katmanları korunur), sürüm AC1032.
5. `karsilastir.py`: kullanıcının aynı dosyadaki MTY çizimi ile karşılaştırma -> `KARSILASTIRMA.md`.

## Çalıştırma
```bash
cd /tmp/claude-0/uu   # çalışma klasörü (önbellek: mk.pkl, nb_ozet.json)
python3 /home/claude/rotas-cizim-motoru/motor/deneme/uctan_uca/nb.py [params.json]   # ~2 dk
python3 /home/claude/rotas-cizim-motoru/motor/deneme/uctan_uca/karsilastir.py
```
Gereken: `/home/claude/nb` (motor kopyası, kurulum.sh), `/tmp/claude-0/blk` MTY blokları, ezdxf / shapely / cv2 / scipy / skimage.
Parametreler (`params.json`): `rogar_cephe`, `depo`, `depo_V`, `kombi_kw`, `cikti`.
Çıktı: R2 `proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R2.dxf` (antette "DENEME R2"); R1 için `params.json` ile `cikti` verilebilir.

## Sınırlar
- Armatür imzaları bu mimarın çizim tarzına göre ayarlı; başka dosyada eşikler gözden geçirilmeli. Mimaride işaretli olmayan
  cihaz (3. daire bulaşık mak., wc+banyo çamaşır mak.) bulunamaz.
- Yük birimi / çap tablosu p2 `gp` değerleri (YB, Ø mm); kullanıcının MB / inç tablosu değil.
- Kolon yeri kuralı (klozet duvarı köşesi) kullanıcının şaft / ortak duvar tercihinden ~1-1,5 m farklı.
- Çatı planı, balkon yer süzgeçleri, WC havalandırma izometrisi ve ısıtma sırası yapılmadı. DWG / Excel üretilmedi (deneme kuralı: yalnız DXF).
- Kolon şeması tüm katlarda zemin kat armatür dizisini kullanır (1. kattaki yüklük farkı şemada görünmez).
