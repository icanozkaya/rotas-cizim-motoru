# 01 — Türkiye'de Mekanik Tesisat Projesi Hazırlama Kuralları (MMO / mevzuat / idare esasları)

Hazırlanma: 2026-10-14 · Kapsam: sıhhi, ısıtma, yangın, havalandırma-klima, sığınak, otopark
Amaç: ROTAŞ çizim motorunun ürettiği paftaların belediye, yapı denetim ve MMO mesleki denetiminden geçmesi için gereken **pafta içeriği, ölçek, not, antet, lejant ve hesap raporu** kurallarını tek yerde toplamak.

## 0. Kaynak durumu (önce okuyun)

- **MMO'nun "Sıhhi / Kalorifer / Yangın / Havalandırma Tesisatı Proje Hazırlama Esasları" kitapçıklarının tam metni web'de bulunamadı.** Bu kitapçıklar MMO yayınları ve şube içi genelgelerdir; açık PDF'leri arama sonuçlarında çıkmadı. Bu yüzden "MMO esası" diye verilen maddelerin çoğu **doğrulanmadı**. Kullanıcının şubesindeki (MMO Sakarya İl Temsilciliği / Kocaeli Şube) güncel proje kontrol formu alınıp bu dosyaya işlenmeli.
- Erişilebilen ve aynı işi gören **resmî ya da kamu kaynakları** şunlar. Bu dosyadaki maddelerin dayanağı bunlardır:
  1. **MEB İnşaat ve Emlak GM — "Eğitim Yapılarında Mekanik Proje Hazırlanması Genel İlkeleri"** (2025). Pafta, ölçek, kolon şeması, lejant notu ve hesap raporu içeriğini ayrıntılı veren en kapsamlı açık belge. MEB projelerine özgü maddeler (okul armatür yükseklikleri gibi) ayıklandı. <https://iegm.meb.gov.tr/meb_iys_dosyalar/2025_08/04151916_egitimyapilarindamekanikprojehazirlanmasigenelilkeleri.pdf>
  2. **ÇŞB — Mekanik tesisat genel teknik şartname taslakları** (Bölüm 3 Isıtma, Bölüm 12 Yangın; 31.12.2018 taslak). Tasarım kuralları içeriyor; pafta/ölçek içermiyor.
     <https://webdosya.csb.gov.tr/db/yfk/icerikler/taslak-uk-isitma-tes-sati-31.12.12018-20190610153814.pdf> · <https://webdosya.csb.gov.tr/db/yfk/icerikler/taslak-uk-yanginla-mucadele-31.12.2018-20190610154051.pdf>
  3. **Binaların Yangından Korunması Hakkında Yönetmelik (BYKHY)**, RG 19.12.2007/26735, son değişiklik 20.11.2021. Resmî metin (mevzuat.gov.tr) robots nedeniyle okunamadı; madde değerleri tesisat.org derlemesinden alındı → **ikincil kaynak**, resmî metinden teyit edilmeli. <https://www.tesisat.org/binalarin-yangindan-korunmasi-hakkinda-yonetmelik-2015.html>
  4. **Sığınak Yönetmeliği** (RG 25.08.1988), son değişiklik **07.11.2025, RG 33070** (Madde 7 ve 8 yeniden düzenlendi). <https://www.lexpera.com.tr/mevzuat/yonetmelikler/siginak-yonetmeligi>
  5. **Otopark Yönetmeliği** (RG 22.02.2018/30340). Havalandırma maddesi yok; BYKHY'ye atıf yapıyor (Madde 4/ğ). <https://aile.gov.tr/eyhgm/mevzuat/ulusal-mevzuat/yonetmelikler/otopark-yonetmeligi/>
  6. **Mimarlık ve Mühendislik Projelerinin Dijital Olarak Hazırlanması Hakkında Yönetmelik** (RG 05.08.2026/33331, **yürürlük 01.09.2027**). Dosya formatı, katman ve pafta kuralları. <https://www.hakedis.org/wp-content/uploads/2026/08/mimarlik_muhendislik_projelerinin_dijital_hazirlanmasi_hakkinda_yonetmelik_20260805.pdf>
  7. **Planlı Alanlar İmar Yönetmeliği** Madde 55 ve 57: mekanik projenin ruhsat ekindeki yeri (ikincil kaynak üzerinden). <https://www.hukukihaber.net/yapi-uygulamatatbikat-projesi-nedir-imar-mevzuatina-gore-ne-zaman-ve-nasil-hazirlanir-nasil-onaylanir>
  8. İstanbul Bilgi Üniv. Kuştepe mekanik projelendirme şartnamesi: avan, uygulama ve detay ölçekleri. <https://defjam.bilgi.edu.tr/media/ihaleler/2019/04/19/kustepe-mekanik-projelendirme-sartnamesi.doc>
  9. KTÜ sıhhi tesisat ders notu: pis su planı, kolon şeması, SB tabloları. <https://ebaydar.ktu.edu.tr/files/sihhi_4.pdf>
- **Güven etiketi:** **[R]** resmî metinden okundu · **[İ]** kamu idaresi esası veya şartname (MEB, ÇŞB) · **[2]** ikincil derleme (tesisat.org, ders notu) · **[B]** ROTAŞ `tesisat-hesap-kutuphanesi` becerisindeki değer, web'de bu oturumda doğrulanmadı · **[D] doğrulanmadı** (uygulama pratiği ya da beklenen MMO kuralı; kaynağı bulunamadı).

---

## 1. Ortak kurallar (tüm mekanik paftalar)

### 1.1 Proje seti ve ruhsat
- Mekanik tesisat projesi; sıhhi tesisat, kalorifer/kat kaloriferi, ısıtma, soğutma, havalandırma projeleri ve **ısı yalıtım (TS 825) raporu**ndan oluşur. Asansör projesi makina ve elektrik mühendisince birlikte hazırlanır. Kaynak: Planlı Alanlar İmar Yön. md. 57 **[2]**
- Projeler mimari projeye uygun hazırlanır. Ruhsat aşamasında mimari proje 6 takım, diğer projeler ve hesaplar 5 takım basılı olarak verilir; ayrıca elektronik kopya sunulur. **[2]**
- Proje müellifi sicil durum taahhütnamesi verir (Ek-1, Ek-8). Yapı denetim kapsamındaki yapılarda yapı denetçisinin uygun görüşü gerekir (4708 s. Kanun). **[2]**
- MMO mesleki denetim (proje vizesi) şubeye göre istenir. Vize öncesinde SMM belgesi, oda sicil no ve uzmanlık belgesi kontrol edilir. Mekanik Tesisat Uzman Mühendis Belgesi kapsamı: RG 22.11.2001/24591, değişiklik RG 21.06.2018/30455 **[R]**. Vize kontrol listesinin içeriği **[D]**.

### 1.2 Ölçekler
| Pafta | Ölçek | Kaynak |
|---|---|---|
| Uygulama kat planları (tüm tesisatlar) | **1/50** | MEB **[İ]**, Bilgi Ü. **[İ]** |
| Avan / ön proje planları | 1/100 | Bilgi Ü. **[İ]** |
| Belediye ruhsat projesi, konut planları | 1/50 (küçük yapı) veya 1/100 (büyük kat alanı) | **[D]**: uygulamada belediyeler 1/50 ister, 1/100 kabulü idareye göre değişir |
| Vaziyet planı (altyapı, rögar, şebeke bağlantısı) | 1/200 – 1/500 | **[D]** |
| Kazan dairesi / ısı merkezi, pompa odası, su deposu planı | 1/20 – 1/25 (1/50 kabul görür) | **[D]**, MEB detay ölçeği 1/20 **[İ]** |
| Şaft kesitleri, cihaz detayları | **1/20, 1/10, 1/5, 1/1** | MEB **[İ]**, Bilgi Ü. (şaftlar 1/20) **[İ]** |
| Kolon şemaları | Ölçeksiz (şematik); kat yükseklikleri orantılı | **[D]** |

### 1.3 Pafta, antet, dosya
- Pafta boyutu A4 ve katları (TS EN ISO 216, TS 5734 ISO 9961). Kaynak: Dijital Proje Yön. md. 8/1 **[R]**. Bu hüküm 01.09.2027'de yürürlüğe girer, ama bugünkü pratikle aynıdır.
- **Her pafta ayrı dosya olur; paftalar tek dosyada birleştirilmez. Her pafta kendi detay ve hesap tablolarını içerir.** Kaynak: md. 8/2 **[R]**, 01.09.2027'den sonra.
- 2B çizimler **PDF/A** olarak, BIM modeli IFC olarak teslim edilir. Kaynak: md. 4/2, 4/5, 9/1 **[R]**. Geçişler: büyükşehirlerde 5.000 m² altı binalarda PDF/A zorunluluğu 01.03.2029'a kadar uygulanmaz. IFC zorunluluğu 2029–2032 arasında kademeli gelir. Konut dışı binalar için 01.09.2033'e kadar ertelenir. **DWG/DXF yönetmelikte geçmez.**
- Katman, sembol, çizgi tipi, yazı ve ölçü gösterimi Dijital Proje Yön. **EK-4**'e göre yapılır. Mahal numarası kat + fonksiyon + sıra no ile verilir (EK-3). Kaynak: md. 7 **[R]**. EK metinleri okunamadı **[D]**. → **ROTAŞ eylemi:** EK-4 yayımlanınca MTY katman adları eşleştirilecek.
- Tüm ölçüler SI birimiyle yazılır. Kaynak: md. 9/2 **[R]**
- **Antet içeriği** **[D]** (resmî şablon bulunamadı; belediye ve MMO pratiği):
  - İş sahibi
  - İl / ilçe / mahalle, pafta-ada-parsel
  - Yapının cinsi ve kullanım amacı, yapı inşaat alanı, kat adedi
  - Projenin cinsi (ör. "Sıhhi Tesisat Projesi – Bodrum Kat Planı")
  - Ölçek, tarih, pafta no / toplam pafta
  - Proje müellifi: ad-soyad, unvan, **oda sicil no**, SMM belge no, imza
  - Varsa ilgili belediye ve yapı denetim onay kutuları, MMO vize alanı, revizyon tablosu
- Her paftada lejant ve semboller tek tip olur. **Semboller ve kısaltmalar paftada liste halinde verilir.** Katmanlar her tesisat için ayrı tanımlanır (temiz su, pis su, ısıtma, soğutma, havalandırma, yangın…). Çizgi tipi ve kalınlıkları tüm paftalarda aynıdır. Yazı yüksekliği ölçeğe uygundur. Çizimler meslek odasının "Proje Çizim ve Sunuş Standartları"na uyar. Kaynak: MEB **[İ]**
- Isıtmada gidiş hattı **kırmızı**, dönüş hattı **mavi** çizilebilir. Kaynak: MEB **[İ]**

### 1.4 Kat planı ve kolon şeması ortak kuralları (MEB **[İ]**)
- Kat planları her tesisat çeşidinin anlaşılmasına yetecek ölçü, tanım ve açıklamayı içerir.
- Kolon şemalarında cihaz kapasiteleri, boru çapları, kolon ve branşman yükleri yazılır. Her katın **adı ve kotu** yazılır; kotlar su basman kotundan itibaren mimari projeden alınır.
- **Kat planı ile kolon şeması birbiriyle birebir uyumlu olur** (kolon adları, çaplar, yükler).
- Plan yetmiyorsa kesit, montaj detayı ve perspektif verilir.
- Asma tavan süperpoze paftası çizilir. Koridorda elektrik tavası ile havalandırma, yangın, ısıtma, VRF ve pis/temiz su hatlarının çakışma ve atlatma detayları kotlarıyla verilir.
- Ana elektrik odası ve trafo üzerinden su, yangın, ısıtma, doğalgaz, VRF drenaj ve bakır boru geçirilmez. Radyatör ve kolektör dolabının üstüne pano ya da priz gelmez.
- Şaftlar, bacalar, menfezler ve dış cephe menfezleri mimari projeye işlenir. Su deposu ve cihaz kaideleri statik projede hesaplanır.
- Dış bağlantı kotları (kanalizasyon, yağmur kanalı, temiz su parsel girişi, doğalgaz) belediye ve dağıtım şirketinden alınıp projeye yazılır.

### 1.5 Hesap raporu ortak içeriği
- Proje raporu tüm hesap esaslarını kısaca içerir. Konular: ısı kaybı/kazancı, havalandırma, sıhhi, yangın, klima santrali, boyler, gri su ve yağmur suyu deposu. **Yangın raporu diğer tesisat raporlarından ayrı hazırlanır.** Kaynak: MEB **[İ]**
- TS 825 ısı yalıtım raporu ve BEP-TR / NSEB ön hesap formu verilir. Yalıtım kalınlıkları mimari projeye işlenir. Kaynak: MEB **[İ]**, Planlı Alanlar **[2]**
- Rapor kapağında proje bilgileri ve müellif imzası bulunur; her hesabın kabul ettiği değerler (iç/dış sıcaklık, rejim, katsayılar) yazılır **[D]**.

---

## 2. Sıhhi tesisat projesi

### 2.1 Pafta içeriği
1. **Vaziyet planı**: parsel sınırı ve bina oturumu; temiz su abone/sayaç girişi ve şebeke kotu; belediye kanalizasyon ve yağmur suyu bağlantı noktaları ve kotları; rögarlar (numaralı, ölçülü, kapak ve dip kotlu); varsa fosseptik, terfi istasyonu, yağ ayırıcı ve yağmur suyu deposu. Kaynak: MEB **[İ]**, KTÜ **[2]**
2. **Kat planları (1/50)**: temiz soğuk su, sıcak su, sirkülasyon, pis su ve yağmur suyu hatları. Her hatta çap; pis su yatayında **eğim (% veya 1/50)** ve akış yönü; kolon adları (TS1, PS1, YS1 vb.); vitrifiye ve armatür yerleri; yer süzgeçleri, temizleme kapakları ve havalıklar. Kaynak: MEB **[İ]**, KTÜ **[2]**
3. **Temiz su kolon şeması**: kat kotları ve adları; kolon ve branşman çapları; vana, sayaç, hidrofor ve depo; kat başı yük (YB/SB). **Kritik devre parçaları numaralı** olur **[D]**; MEB bunu ısıtma için açıkça ister **[İ]**.
4. **Pis su kolon şeması**: kolon yükleri (SB/DU), çaplar, havalandırma kolonları ve havalıklar. Her kolonun en alt erişilebilir noktasında temizleme kapağı bulunur. Bodrumda pis su çukuru ve pompa yer alır. Kaynak: KTÜ **[2]**, MEB **[İ]**
5. **Yağmur suyu planı ve şeması**: oluk/süzgeç, iniş boruları, çatı alanı ve çaplar. **Yağmur suyu pis suya bağlanmaz.** İniş borusunda yaklaşık 100 cm yükseklikte temizleme kapağı konur. Kaynak: MEB **[İ]**, KTÜ **[2]**
6. **Hidrofor / su deposu / pompa odası detayı**: 1 asıl + 1 yedek hidrofor; depo bağlantıları, vorteks plakası, adam deliği, merdiven ve kaide. Kaynak: MEB **[İ]**
7. **Detaylar**: rögar, yağ ayırıcı, pis su çukuru ve pompa, sayaç, temel içinden pis su geçişi, ses yalıtımı, boru askı ve konsol, yangın geçiş (sızdırmazlık) ve dilatasyon kompansatörü detayları. Kaynak: MEB **[İ]**
8. Bodrum kotu kanalizasyonu kurtarmıyorsa **pis su terfi istasyonu** kurulur; pompa kapasitesi yazılır. Kaynak: MEB **[İ]**

### 2.2 Zorunlu / beklenen notlar
- Pis su yatay boruları en az %2 eğimle döşenir; kat boruları kolona 45° ile bağlanır; borular muflu birleşimlidir. Kaynak: KTÜ **[2]**
- Tüm pis su çıkışları sifonlu çizilir; tezgâh altı da buna dahildir. Kaynak: MEB **[İ]**
- Kazan dairesi, şaft ve bodrumdaki galvaniz borular kauçuk esaslı yalıtılır. **Bu not lejanta yazılır.** Kaynak: MEB **[İ]**
- Temizleme kapakları bitmiş yüzeyle aynı hizada olur. Kaynak: MEB **[İ]**
- Çatı havalıkları en yakın şafttan çıkar ve şapkalı olur. Kaynak: MEB **[İ]**
- Boru malzemesi, test basıncı (ör. işletme basıncının 1,5 katı) ve dezenfeksiyon notu yazılır **[D]**.

### 2.3 Hesap raporu
- Temiz su: armatür yük birimleri (YB), eş zamanlı debi, boru çapları, **kritik devre basınç kaybı**, hidrofor debisi ve basıncı, membranlı tank hacmi, depo hacmi. Standart: TS EN 806-3 / DIN 1988 **[D]**. MEB temiz su, hidrofor, depo ve pompa hesaplarını ister **[İ]**.
- Sıcak su: boyler/akümülasyon hacmi, ısıtıcı kapasitesi, sirkülasyon pompası; varsa güneş kolektörü. Kaynak: MEB **[İ]**
- Pis su: SB/DU yükleri, kolon ve ana boru çapları, eğimler; varsa pis su pompası (TS EN 12056). Kaynak: KTÜ Tablo 4.2–4.3 **[2]**
- Yağmur suyu: alan × yağış şiddeti × akış katsayısı; oluk ve iniş çapları. Kaynak: KTÜ Tablo 4.4–4.6 **[2]**
- Varsa fosseptik / gri su / yağmur suyu deposu hesapları. Kaynak: MEB **[İ]**

---

## 3. Isıtma (kalorifer) projesi

### 3.1 Pafta içeriği
1. **Kat planları (1/50)** (MEB **[İ]**):
   - Her mahalde kat numarası ve mahal kısaltması/no, iç sıcaklık ve **ısı kaybı** değeri yazılır.
   - Radyatörün üstüne tip, ısı yükü ve boy; içine mahal no ve sıcaklık yazılır.
   - Gidiş ve dönüş hatlarının yanına sıcaklık, ısı yükü ve çap yazılır.
   - 100 cm ve üzeri radyatörlerde bağlantı çapraz yapılır.
   - Kolektörlü sistemde kolektör dolabı detayı verilir.
2. **Kolon şeması** (MEB **[İ]**):
   - Kat kotları ve kat adları
   - Her kolon ve branşmanda taşınan **enerji (W/kcal/h)** ve çap
   - **Kritik devrenin boru parçaları numaralı**
   - En alt katta kolon diplerinde kosva ve boşaltma vanası; hava alma (purjör)
3. **Kazan dairesi / ısı merkezi planı ve tesisat şeması** (MEB **[İ]**, ÇŞB 3.3 **[İ]**):
   - Kazan, brülör, kolektörler, vana grupları (2 ve 3 yollu, küresel, kosva), pompalar, genleşme tankı, emniyet vanaları, boyler ve eşanjör
   - Bağlantı çapları
   - **Alt ve üst havalandırma menfezleri**; baca ve duman kanalı yeri ölçülü ve mimari projeye işlenmiş
   - Kazan önü servis mesafesi en az **kazan boyu + 1,00 m** (ÇŞB **[İ]**)
4. **Baca detayı**: baca kesiti; çatıda mahyayı geçen yükseklik (MEB: mahyadan yaklaşık 80 cm yukarı, şapkalı); her katta kuşak detayı; temizleme kapağı. Gazlı kazanda **drenaj ve nötralizasyon** detayı eklenir. Kaynak: MEB **[İ]**. Baca TS EN 13384-1 ve -2'ye göre hesaplanır; baca plakası sınıfı TS EN 1443'e göre yazılır. Kaynak: ÇŞB 3.4 **[İ]**
5. **Detaylar**: genleşme tankı bağlantısı (tank ile kazan arasında vana olmaz), boru askıları, yalıtım, kolektör dolabı (lento), radyatör bağlantısı (H-vana), yerden ısıtma kesiti. Kaynak: MEB **[İ]**, ÇŞB 3.5 **[İ]**

### 3.2 Zorunlu / beklenen notlar
- Sistem kabulleri yazılır: sıcaklık rejimi (90/70, 80/60 vb.), dış tasarım sıcaklığı (TS 825 bölge), iç sıcaklıklar. Kaynak: MEB **[İ]**
- Lejant notları (MEB **[İ]**):
  - Teşhin merkezindeki hatlar etiketlenir, akış yönleri okla gösterilir.
  - Çap değişimlerinde redüksiyon kullanılır.
  - Geçici kabulden önce **flushing** yapılır.
  - Kazan dairesindeki vanalara yalıtım ceketi takılır.
- Isı merkezinin işletme rejimi, min/max basınçlar ve emniyet ventili açma değerleri levhaya yazılıp asılır. Kaynak: ÇŞB 3.5 **[İ]**
- Gazlı ısı merkezi (ÇŞB 3.3.3 **[İ]**):
  - Bina diğer bölümlerinden **120 dk** dayanımlı bölmeyle ayrılır.
  - 50–350 kW için ≥1 kapı, >350 kW için ≥2 kapı.
  - Gaz alarm cihazı ve solenoid vana bulunur.
  - Alt ve üst menfez açılır.
  - LPG'li ısı merkezi tabii zemin altına yapılamaz.

### 3.3 Hesap raporu (MEB **[İ]**, ÇŞB **[İ]**)
- Mahal mahal **ısı kaybı tablosu** (TS 2164 / TS EN 12831): yüzey, U, ΔT, artırımlar, emniyet katsayıları
- Radyatör / yerden ısıtma seçim tablosu
- **Boru çapı ve basınç kaybı tablosu** (kritik devre)
- Kazan kapasitesi, brülör, baca kesit ve yükseklik hesabı (TS EN 13384)
- Kapalı genleşme tankı hacmi ve ön basıncı (TS EN 12828), emniyet ventili ve emniyet boruları
- Sirkülasyon pompası debisi, basma yüksekliği ve motor gücü
- Boyler / sıcak su ihtiyacı
- TS 825 ısı yalıtım raporu (ayrı belge)

---

## 4. Yangın tesisatı projesi

### 4.1 Pafta içeriği (MEB **[İ]**; BYKHY **[2]**)
1. **Kat planları**:
   - Yangın dolapları; dolap aralığı en fazla **30 m**, sprinklerli binada en fazla **45 m** (BYKHY 94/b-2)
   - Sprinkler başlıkları ve dağıtım boruları; **sprinkler zonları ayrı katman ve renkte**
   - Zon vanaları: akış anahtarı, izlemeli vana, test ve drenaj
   - İtfaiye bağlantı ağızları yangın merdiveni veya yangın güvenlik holünde; her noktaya en fazla **60 m** (94/a)
   - Yangın söndürücü tüpleri
2. **Yangın kolon şeması**: kolonlar **YG1, YG2…** diye numaralı; her katta boru çapı, sprinkler sayısı ve yük; dolaplar ve sprinkler hatları; akış yönleri, kolektör vanaları, alarm vanası, akış anahtarları, izleme vanaları ve drenaj bağlantıları.
3. **Pompa dairesi ve yangın suyu deposu planı/şeması**: asıl + yedek pompa, jokey pompa, her pompa için ayrı pano ve basınç anahtarı (93/6-7); emiş hattı, test hattı; depo hacmi ve bağlantıları (vorteks plakası, seviye göstergesi, taşma).
4. **Vaziyet planı**: hidrantlar (binadan 5–15 m, aralık riske göre 50/100/125/150 m; 95/3-4), itfaiye su verme bağlantısı (DN100, 2 × 65 mm storz; md. 97), itfaiye yaklaşım yolu (BYKHY 22: araç–bina en uzak dış nokta en fazla 45 m) **[2]**.
5. **Detaylar**:
   - Yangın dolabı montajı (gömme dolapta lento)
   - Sprinkler başlığı
   - Alarm vanası istasyonu
   - Deprem askısı: 1. ve 2. derece deprem bölgesinde 4 yönlü destek; ≥65 mm borularda esnek bağlantı (96/6)
   - Duvar/döşeme geçişlerinde yangın sızdırmazlığı
   - Islak alarm vanası gongu en yakın koridora getirilir
   - Test-drenaj hattı yağmur suyuna bağlanır
6. Enerji, sistem ve arşiv odalarında gazlı söndürme kullanılır: kat planı ve izometrik şema çizilir (MEB **[İ]**).
7. 2.000 m²'den büyük katların **tahliye projesi** mimariden ayrı hazırlanır (BYKHY 6/4). 10.000 m²'yi aşan binalarda tahliye projesinde dolap, itfaiye ağzı, pompa ve jeneratör yerleri işaretlenir (7/4) **[R]**.

### 4.2 BYKHY sayısal kuralları (çizim/hesap kontrolü) **[2]**
| Konu | Kural | Madde |
|---|---|---|
| Yangın dolabı zorunlu | Yüksek binalar; >1.000 m² imalat, depo, konaklama, sağlık, toplanma ve eğitim yapıları; >600 m² kapalı otopark; >350 kW kazan dairesi | 94/b-1 |
| Hortum TS EN 671-1 | Ø25 mm, en fazla 30 m; 100 l/dk; 400 kPa; lüle girişinde >900 kPa ise basınç düşürücü | 94/b-4,5 |
| Hortum TS EN 671-2 (yassı) | ≤50 mm, en fazla 20 m; 400 l/dk; ≥400 kPa | 94/b-6 |
| Sprinkler zorunlu | Konut dışı >30,50 m; konut >51,50 m; >600 m² kapalı otopark veya asansörle >10 araç alan otopark; >100 oda, >200 yatak veya >21,50 m yataklı tesis; >2.000 m² ticaret; >1.000 m² kolay alevlenen madde | 96/2 |
| Sprinkler tasarımı | TS EN 12845; düşük ve OH-1 sınıfında başlık başına ≤21 m² | 96/5 |
| Zon | Her zonda akış anahtarı, test/drenaj vanası, izlemeli vana; basınç düşürücünün önünde ve arkasında manometre | 96/7, 96/10 |
| İtfaiye su verme bağlantısı | Yüksek bina, >1.000 m² oturma alanı veya >75 m cephe; DN100, 2 × 65 storz, çek valf, boşaltma | 97 |
| Hidrant | ≥1.900 l/dk, 700 kPa; >5.000 m² taban alanlı yerleşimde dış hidrant zorunlu | 95 |
| Su rezervi süresi | Düşük 30 dk, orta 60 dk, yüksek 90 dk; yalnız hidrant varsa 1.900 l/dk × 90 dk | 92/3, 92/7 |
| Pompa eğrisi | Kapalı vanada ≤%140 basma yüksekliği; %150 debide ≥%65 | 93/1 |
| Pompa yedeği | Tek pompada eşdeğer yedek; birden fazla pompada toplam kapasitenin ≥%50'si | 93/2 |
| Pompa odası | Elektrikli pompada ≥+4 °C, dizelde ≥+10 °C; acil aydınlatma; eğimli drenaj | 93/9-11 |
| Söndürücü | Düşük tehlikede her 500 m²'ye, orta/yüksek tehlikede her 250 m²'ye 1 adet 6 kg KKT | 99/2 |
| Kazan dairesi | Diğer bölümlerden 120 dk ayrılır; kapı kaçış merdivenine açılmaz; >350 kW veya >100 m² ise 2 kapı (90 dk, kendiliğinden kapanır); sıvı yakıtta ≥0,25 m³ çukur; 1 × 6 kg KKT | 54 |

### 4.3 Notlar ve hesap raporu
- Lejant notları (MEB **[İ]**):
  - "Yangın sistemlerine ait tüm tesisatlarda geçici kabul öncesi ön yıkama (flushing) yapılacaktır."
  - Geçişlerde yangın sızdırmazlığı sağlanır; taş yünü kullanılır.
  - **Ekipman kapasite ve ölçüleri lejanta yazılır.**
- Hesap raporu **ayrı dosya** olur. İçeriği:
  - Tehlike sınıfı (TS EN 12845; ör. OH-1…OH-4, HH)
  - Tasarım yoğunluğu ve alanı
  - En olumsuz alan hidrolik hesabı (Hazen-Williams)
  - Dolap ve hidrant debileri
  - Toplam debi × süre = depo hacmi
  - Pompa debi ve basma yüksekliği, jokey pompa
  - Kaynaklar: MEB **[İ]**, BYKHY 92 **[2]**
- Jokey pompa: debi ana pompanın yaklaşık %1'i, basınç yaklaşık 0,5 bar üstü. Dizel yakıt tankı: düşük tehlikede 3 saat, orta tehlikede 4 saat, yüksek tehlikede 6 saat. Kaynak: ÇŞB 12.3 **[İ]**

---

## 5. Havalandırma / klima projesi

### 5.1 Pafta içeriği (MEB **[İ]**)
- Kat planlarında kanal ebatları, debi ve hız; menfez tipi, debisi ve üfleme/emiş yönleri; branşman damperleri; **kat geçişlerinde yangın damperi ve servo motor**.
- **Havalandırma izometrik şeması**: menfez tipleri, debiler, akış yönleri, taze ve egzoz miktarları, panjur ölçüleri, kanal ebatları.
- Kanal ve şaft yerleşimleri ölçülü çizilir; atlatma detayları verilir.
- Klima santrali / IGK tesisat şeması ve otomasyon senaryosu. Marka, tip ve kapasite lejanta yazılır.
- Detaylar:
  - Kanal flanşı (en az 25 mm)
  - Redüksiyon, dirsek, S-parça, pantolon branşman (saplama kullanılmaz)
  - Fleks en fazla 1 m
  - Plenum kutusu (sac ≥0,8 mm, galvaniz ≥275 g/m²)
  - Çatı aspiratörü kaidesi, panjur tel kafesi (≥1 mm)
  - Duman tahliye kanalında yanmaz ve contalı birleşim
- Lejant notu: "Yangın alarmı çaldığında servo motorlar kat geçişlerine hava akımını kapatmalıdır." Yangın duvarı veya döşeme geçişindeki kanal çevresi, duvarın dayanım süresi kadar yalıtılır (BYKHY 25/2, 26/5 **[R]**).

### 5.2 Hesap raporu (MEB **[İ]**)
- Mahal debi tablosu (kişi ve alan ya da hava değişimi), kanal boyutlandırma ve basınç kaybı
- Fan, aspiratör, susturucu ve batarya seçimleri
- Klima santralinin Eurovent sertifikası, katalog ve fan eğrileri
- Isıl yük (kazanç) hesabı
- VRF dış ünite kapasiteleri
- Otomasyon senaryosu

### 5.3 Merdiven / asansör basınçlandırma (BYKHY 89, 62/4) **[2]**
- Zorunlu olduğu durumlar: konut dışı binada merdiven yüksekliği >30,50 m; konutta >51,50 m; 4'ten fazla bodrum katında bodruma hizmet eden merdivenler; acil durum asansörü kuyusu.
- Değerler:
  - Kapılar kapalıyken ≥50 Pa, açık kapı durumunda ≥15 Pa
  - Kapı açma kuvveti ≤110 N
  - Açık kapıdan hava hızı ≥1 m/s; tasarımda 2 iç kapı + 1 dış kapı açık kabul edilir
- Üfleme dış havadan yapılır, egzozdan ≥5 m uzakta olur. 25 m'yi aşan merdivende çok noktadan, 51,50 m'yi aşan merdivende en çok 3 katta bir üflenir.
- Aşırı basınç damperi, frekans kontrollü fan, emişte duman dedektörü ve elle kumanda bulunur.
- Asansör kuyusunda en az 0,1 m² ve kuyu alanının 0,025 katı kadar duman bacası açılır ya da kuyu basınçlandırılır.

---

## 6. Sığınak havalandırması (Sığınak Yönetmeliği, 07.11.2025 değişikliği) **[R]**
- **Md. 7**: Serpinti sığınağı istisnalar dışında her türlü binada yapılır. İstisnalar: 10'dan az bağımsız bölümlü konutlar, küçük konut dışı yapılar, yerüstü otoparklar, depolar, akaryakıt/LPG istasyonları vb.
- **Md. 6**: Sığınak en alt bodrumda veya toprağa oturan kısımda yapılır; emsale dahil değildir.
- **Md. 10**: AVM ile bölge, genel ve ticari otoparkların zemin altı otopark alanları sığınak vasfında projelendirilir.
- **Md. 8**:
  - Kişi başı en az **1 m² net** alan ayrılır; WC, duş ve mutfak nişi bu alana dahil değildir.
  - Kişi sayısı: konutta oda sayısına göre; konaklama tesisinde yatak sayısı +%20; diğer yapılarda emsal alanı / 20; imalatta kişi başı 1 m², en az 20 m².
- **Md. 8/ç**:
  - Kapasiteye uygun **mekanik havalandırma tesisatı zorunludur**. Kişi başı minimum hava değerleri koruma süresine bağlı bir tabloda verilir; tablo görsel olduğu için okunamadı **[D]**.
  - Barış zamanında dış hava yalnızca **G4 kaba filtre**den geçirilir. Koruma zamanında nükleer tip **HEPA filtre** veya **kum havuzu** sistemi kullanılır.
  - Fan jeneratör veya UPS ile beslenir; jeneratör egzozu dışarı verilir. Enerji kesilirse fan **elle çevirmeli kolla** çalıştırılabilir.
  - Kanal ve menfez tasarımı mekanik proje müellifine bırakılmıştır; **TS 3419 / TS 3420** esas alınır.
- Giriş demir kapılı olur ve en az bir dik açı dönüşü içerir. Net alanı >100 m² olan sığınakta **2 çıkış** bulunur.
- Beceri değerleri **[B]**:
  - Koruma havası: ≤50 kişide 1,8 m³/h·kişi; 51–150 kişide 3 m³/h·kişi; >150 kişide 4,5 m³/h·kişi
  - İç basınç +50 Pa
  - WC'de 10 hava değişimi
  - >100 m²'de duman egzozu
  - Bu değerler 07.11.2025 tablosuyla karşılaştırılmalı. Kullanıcının kendi kuralları `/topics/siginak-havalandirma-hesabi` hafıza notundadır.
- Projede gösterilecekler **[D]**: sığınak planı, havalandırma cihazı (fan + filtre) yeri, taze hava girişi ve egzoz çıkışı (ayrı yönlerde), aşırı basınç klapesi, el kumandalı fan, kişi sayısı ve debi tablosu.

## 7. Kapalı otopark havalandırması
- **Otopark Yönetmeliği** (RG 22.02.2018/30340) havalandırma için sayısal kural koymaz. Md. 4/ğ ile **BYKHY ve TS standartlarına** uyumu zorunlu kılar **[R]**.
- BYKHY'nin otopark havalandırması ve duman tahliyesi maddesinin metnine ulaşılamadı **[D]**. Erişilebilen hükümler:
  - Otopark kompartıman duvarlarıyla ayrılır (24/2) **[R]**.
  - >600 m² kapalı otoparkta sprinkler (96/2-c) ve yangın dolabı (94/b-1) zorunludur **[2]**.
- Beceri kuralı **[B]** (TO kaynağı): aşağıdakilerden en büyüğü alınır:
  - 6 hava değişimi
  - CO seyreltme hesabı
  - 2.000 m² üstünde duman tahliyesi = alan × h × 10/h
  - Fanlar 200 °C'de 2 saat dayanımlı olur
  - → Resmî BYKHY metninden (Altıncı Kısım, duman kontrolü) teyit edilmeli.
- Projede gösterilecekler **[D]**: taze hava girişi ve egzoz kanal/fanları ya da jet fan yerleşimi; CO dedektörleri; duman tahliye fanı ve damperleri; egzoz atış noktası (pencere ve taze hava emişinden uzak); fanların yangın paneliyle senaryosu; debi hesap tablosu.

## 8. Yürürlükteki sıhhi/ısıtma tasarım standartları (rapor referansı) **[D]**
- Temiz su: TS EN 806 serisi
- Pis su: TS EN 12056
- Isı kaybı: TS 2164, TS EN 12831
- Baca: TS EN 13384
- Sprinkler: TS EN 12845; yangın dolabı: TS EN 671
- Sıcak su sistemleri: TS EN 12828
- Isı yalıtımı: TS 825
- Sığınak: TS 3419/3420
- Doğalgaz: dağıtım şirketinin teknik şartnamesi

---

## 9. ROTAŞ motoru için kontrol listesi (otomatik denetimde kullanılacak)

| # | Kontrol | Tesisat | Dayanak |
|---|---|---|---|
| K01 | Her paftada antet var: iş sahibi, ada/parsel, proje cinsi, ölçek, tarih, pafta no, müellif adı, oda sicil no, imza alanı | Hepsi | [D] |
| K02 | Her paftada lejant var; semboller ve kısaltmalar liste halinde | Hepsi | MEB [İ] |
| K03 | Uygulama planları 1/50; detaylar 1/20–1/1 | Hepsi | MEB [İ] |
| K04 | Kat planı ile kolon şeması birebir uyumlu (kolon adı, çap, yük) | Sıhhi, ısıtma, yangın | MEB [İ] |
| K05 | Kolon şemasında kat adları ve kotları (su basmanından) yazılı | Hepsi | MEB [İ] |
| K06 | Kolon şemasında kritik devre parçaları numaralı; kolon/branşman yükü ve çapı yazılı | Isıtma, temiz su | MEB [İ] |
| K07 | Pis su yataylarında eğim, akış yönü ve çap yazılı; temizleme kapakları ve havalıklar gösterilmiş | Sıhhi | KTÜ [2], MEB [İ] |
| K08 | Yağmur suyu ayrı; pis suya bağlanmamış | Sıhhi | MEB [İ] |
| K09 | Vaziyet planında şebeke bağlantıları ve kotları, numaralı rögarlar ve kotları | Sıhhi | MEB [İ] |
| K10 | Mahallerde ısı kaybı ve sıcaklık; radyatörde tip, boy ve kapasite | Isıtma | MEB [İ] |
| K11 | Kazan dairesinde alt/üst menfez, baca ölçülü, kapı sayısı (>350 kW → 2 kapı), 120 dk ayrım | Isıtma | BYKHY 54 [2], ÇŞB [İ] |
| K12 | Genleşme tankı ile kazan arasında vana yok; emniyet ventili gösterilmiş | Isıtma | ÇŞB 3.5 [İ] |
| K13 | Yangın dolabı aralığı ≤30 m (sprinklerli binada ≤45 m); kolonlar YG1… adlı, katta çap ve sprinkler sayısı yazılı | Yangın | BYKHY 94 [2], MEB [İ] |
| K14 | Sprinkler zonu başına akış anahtarı, izlemeli vana, test/drenaj; zonlar ayrı katman ve renkte | Yangın | BYKHY 96/7 [2], MEB [İ] |
| K15 | Yangın deposu = debi × süre (30/60/90 dk); asıl + yedek + jokey pompa, ayrı panolar | Yangın | BYKHY 92–93 [2] |
| K16 | İtfaiye bağlantısı (DN100, 2 × 65 storz) ve hidrant yerleri vaziyet planında | Yangın | BYKHY 95, 97 [2] |
| K17 | Kat geçişlerinde yangın damperi; lejantta servo motor/damper notu | Havalandırma | MEB [İ] |
| K18 | Havalandırma izometrisinde debi, menfez tipi, kanal ebadı, taze/egzoz miktarı | Havalandırma | MEB [İ] |
| K19 | Sığınak: kişi sayısı, 1 m²/kişi, mekanik havalandırma, G4 + HEPA/kum filtre, el kumandası, >100 m²'de 2 çıkış | Sığınak | Sığınak Yön. md. 8 [R] |
| K20 | Hesap raporu var; yangın raporu ayrı; kabul değerleri yazılı | Hepsi | MEB [İ] |
| K21 | Flushing notu (ısıtma ve yangın) ve galvaniz yalıtım notu lejantta | Isıtma, yangın, sıhhi | MEB [İ] |

## 10. Açık işler
- MMO Sakarya / Kocaeli şubesinden güncel **mekanik proje kontrol (mesleki denetim) formu** ve şube antet şablonu alınmalı. Kullanıcıdan istenmeli.
- BYKHY tam metni (özellikle Altıncı Kısım duman kontrolü ve otopark, Madde 55–60 baca ve yakıt) resmî kaynaktan okunmalı. mevzuat.gov.tr robots engeli nedeniyle bu oturumda okunamadı.
- Sığınak Yönetmeliği md. 8/ç havalandırma tablosu (görsel) RG 33070 PDF'inden okunmalı.
- Dijital Proje Yönetmeliği EK-1…EK-9 (özellikle **EK-4 katman/sembol**) bulunup MTY katmanlarıyla eşleştirilmeli; yürürlük 01.09.2027.
