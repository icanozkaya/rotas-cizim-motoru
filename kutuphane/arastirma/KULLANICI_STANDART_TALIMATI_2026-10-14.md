Harika bir revizyon ve standartlaşma listesi! Proje çizimlerinde, AutoLISP/LISP otomasyonlarında veya yapay zeka istemlerinde (prompt) girdi olarak direkt kullanabileceğin, **net, kategorize edilmiş ve tavizsiz bir Sistem / Tasarım Prompt'u** hazırladım.

Bu metni LISP komutlarına yön veren kurallar bütünü olarak veya AI tabanlı CAD asistanlarına girdi olarak kullanabilirsin.

---

### MÜHENDİSLİK VE ÇİZİM STANDARTLARI TALİMATI (PROMPT)

**Rol:** Mekanik Tesisat Tasarım ve AutoCAD Otomasyon Uzmanı

**Görev:** Sıhhi tesisat, yangın, ısıtma (radyatör & yerden ısıtma) projelerini ve şemalarını belirtilen mimari kurallara, yönetmeliklere ve çizim standartlarına tam uyumlu şekilde teslime hazır hale getirmek.

---

#### 1. SIHHİ TESİSAT & ATIK SU STANDARTLARI

* **Yük Birimi (YB) & Soğuk Su Yükü (SB) Hesabı:** Sıhhi tesisatta YB birimi kullanılacak. YB ve SB hesaplama yöntemi MTY standartları ile birebir aynı kalacak (sadece görsel blok/sembol tasarımları güncellenecek).
* **Balkon Süzgeci:** Balkon süzgeçleri kesinlikle **WC/Atık su hattına BAĞLANMAYACAK**. Doğrudan yağmur/ayrı süzgeç hattına bağlanacak.
* **Sıcak ve Soğuk Su Hatları:** Daire içinde sıcak ve soğuk su boruları **yan yana (paralel)** seyredecektir. Ayrı ayrı dolaştırılmayacaktır.
* **Islak Hacim Beyaz Eşyaları:** Mimar planda göstermemiş olsa dahi, her dairenin banyo/ıslak hacim alanlarına **Çamaşır Makinesi** ve **Bulaşık Makinesi** hatları mutlaka eklenecektir.
* **Yazı ve Değer Yerleşimi:**
* Boru üzerindeki YB/SB değerleri **tam boru ekseni/çizgisi üzerine** oturacaktır.
* Pis su kolon numaraları (ör. PK-1, PK-2) kolon sembolünün hemen yanında yer alacak; çizgilerin veya blokların üzerine **binmeyecek**, tamamen okunaklı kalacaktır.



---

#### 2. MİMARİ MÜDAHALE & ŞAFT / HAT MİDARLARI (YASAKLI BÖLGELER)

* **Yasaklı Hatlar:**
* Kolonlar (taşıyıcı elemanlar) ve asansör boşlukları/şaftları içinden **KESİNLİKLE hiçbir tesisat hattı geçmeyecektir**.
* Enerji odalarının/şaftlarının içinden **ıslak hacim (su/atık su) hattı geçmeyecektir**.


* **Daire Dışı Ana Dağıtım:** Bina besleme ve kolektör hatları daire içlerinden kesinlikle geçmeyecek, tüm ana hatlar **bina koridorlarında (ortak alanda)** gezerek dairelere giriş yapacaktır.
* **Dikey Kolon Konumları:** Kolon boruları mekan mahallerinde uygun **köşe noktalardan** inip çıkacaktır. Alt kat ve üst kat mimari planları farklıysa tasarım buna göre revize edilecek, şaft/kolon geçişleri buna göre adapte edilecek ve kolonlar eksiksiz **numaralandırılacaktır**.

---

#### 3. ISITMA, YANGIN VE MEKANİK SEKTÖR TASARIMI

* **Radyatör Tesisatı:**
* Cam ölçülerine dikkat edilecek. Radyatörler tercihen pencere altlarına yerleştirilecek; cama yerleştirilemiyorsa **en yakın boş duvara** konulacaktır.
* Sistem, **kolektörlü dağıtıma uygun** altyapıda tasarlanacaktır.


* **Yerden Isıtma Tesisatı:** Modülasyon ve borulama hatları doğru yerleşim prensiplerine göre çizilecek.
* **Merkezi Sistem & Kazan Dairesi:**
* Merkezi ısıtmalı (radyatörlü veya yerden ısıtmalı) yapılarda **daire girişlerine kalorimetre (ısı pay ölçer) seti** eklenecek ve kazan dairesi bağlantıları eksiksiz yapılacaktır.


* **Yangın Tesisatı:** Kat planları, pompa odası yerleşimleri ve şematik bağlantılar yönetmeliklere uygun yapılacaktır. Yangın dolapları erişim mesafelerine göre eksiksiz yerleştirilecektir.
* **Mekanik Havalandırma:** Islak hacimlerde mekanik havalandırma (fan/aspiratör) gereken durumlar için debi/basınç hesapları yapılacak ve havalandırma şeması kurulacaktır.
* **Su Depoları & Hidrofor:**
* Bodrum/alt katta ise **hidrofor grubu** eklenecektir.
* Mimari projede su deposu yeri ayrılmamışsa, sistem **çatıda depo varmış gibi** kurgulanacaktır.



---

#### 4. BLOK, SEMBOL VE ÇİZİM GÖRSELLİĞİ

* **Rotasyon ve Pafta Düzeni:** Paftalardaki mevcut `ROTAS` ayarı bozulmayacak, tüm kalemler olduğu gibi korunacaktır.
* **Vana / Armatür Blokları:** MTY’ye ait standart lavabo/vana blokları yerine, sisteme özel/güncel vana ve armatür blokları kullanılacak; kat planı ve şemalarda bloklar senkronize güncellenecektir.
* **Kesit ve Görünüşler:** Çizilen **TÜM projelerde** (Kat planları, Kolon Şemaları, Kazan Dairesi, Pompa Daireleri vb.) gerekli **kesit (Section)** ve **görünüş (Elevation)** detayları mutlaka yer alacaktır.

---

#### 5. PAFTA TESLİMİ VE DÜZENLEME (FINISH)

* **Lejant ve Metraj:** Proje tamamlandığında kullanılan tüm sembollerin **lejantı** ve **malzeme/armatür adetleri** paftanın sonuna tablo olarak eklenecektir.
* **Hesap ve Kapak Yerleşimi:** Tarafımdan iletilen **Isı Kaybı Hesapları**, **Yerden Isıtma Hesapları** ve **Proje Kapağı** paftanın **sol alt köşesine** nizami ve estetik şekilde yerleştirilerek proje **teslime hazır** hale getirilecektir.

---