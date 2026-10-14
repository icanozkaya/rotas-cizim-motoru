# 08 — Havalandırma, Duman Kontrolü ve Klima/VRF Proje Çizim Pratiği

> Araştırma notu (2026-10-14). Web kaynakları ile depodaki örnek setler (ASELSAN, Ada Hayat, `ornekler/ORNEK_DUZEN.md`) birlikte özetlenmiştir.
> **Öncelik sırası:** Kullanıcının kendi kuralları (README "Kalıcı kurallar", hafıza notları) > yürürlükteki yönetmelik > standart/kılavuz > bu nottaki genel değerler.
> "⚠ doğrula" işaretli değerler ikincil kaynaktan alınmıştır. Resmî metin (mevzuat.gov.tr) bu ortamdan açılamadı (proxy 403); proje teslimi öncesinde resmî metinle karşılaştırın.

---

## 0. ROTAŞ'a özel bağlayıcı kurallar (önce bunlar)

| Konu | Kural | Kaynak |
|---|---|---|
| Otopark normal havalandırma | **4 hava değişimi** (VOYAP standardı) | README.md "Kalıcı kurallar" |
| Otopark duman tahliyesi | **10 hava değişimi**. Egzoz çıkışı sığınağın karşı cephesinden verilir. Betonarmede boşluk notu yazılır | README.md |
| Sığınak taze hava | Net alan (hacim) × **4 hava değişimi** | hafıza: siginak-havalandirma-hesabi |
| Sığınak egzoz | Taze havanın **%10 altı** | aynı |
| Sığınak duman egzozu | Net alan **> 100 m²** ise eklenir; değilse taze hava + egzoz yeterli | aynı |
| Sığınak perde açıklığı | Duvarda açılacak ölçü yazılır (ör. "50x30") | aynı |
| Sığınak teslimi | Her sığınak için ayrı hesap, düzgün tablo | aynı |
| Penceresiz WC | "mek. havl." şaftı + turuncu yazı "Wc Aspiratörü 160 m3/h-50 pa Ø150 mm". Son paftaya WC havalandırma izometrisi: "Wc Aspiratörü 80/160 m³/h - 50 Pa - Ø150 mm", çatı tipi fan 240/480 m³/h | `ornekler/ORNEK_DUZEN.md` |
| Otopark hesabı | Kullanıcı bazı projelerde 6 hava değişimi yerine **araç egzozu (CO) yöntemi** istedi. Tabloya kısa hesap, kademeli çalışma ve ses notu yazılır | hafıza: otopark-havalandirma |
| Katmanlar | `MTY-UFLEME-KANALI` (20), `MTY-EGZOZ-KANALI` (4), `MTY-KANAL-CAP` (21), `MTY-DUMAN-EGZOZ` (1), `MTY-MENFEZ` (7), `MTY-HAVALANDIRMA-CIHAZ` (135), `MTY-TES-SAFT` (8), `MTY-TES-YAZI` (7), `MTY-TES-NOT`, `MTY-HESAP` | `motor/voyap/tes/tlib.py` |
| Klima katmanları | `MTY-KLIMA-IC UNITE`, `MTY-KLIMA-DIS UNITE`, `MTY-KLIMA-BAKIR BORU`, `MTY-KLIMA-DRENAJ` | `motor/p2/gklima.py` |

---

## 1. Kanal boyutlandırma

### 1.1 Yöntemler
| Yöntem | Mantık | Ne zaman |
|---|---|---|
| **Hız azaltma (velocity reduction)** | Her bölüm için tablodan hız seçilir, A = Q / v ile kesit bulunur, sonra sürtünme ve özel kayıplar eklenir | Basit egzoz ve WC hatları, el hesabı |
| **Eşit sürtünme (equal friction)** | Tüm şebekede sabit birim kayıp R (Pa/m) seçilir, debiye göre çap ya da eşdeğer çap okunur. Konfor sistemlerinde tipik R ≈ **0,8–1,0 Pa/m** (ACR-News örneğinde 800x400 kanal için 0,8 Pa/m). Fan basıncı, kritik (en uzun) hattın ΣR·L + Σζ·ρv²/2 değeridir | Ofis, AVM, otel üfleme ve emiş şebekeleri. Türk projelerinde en yaygın yöntem |
| **Statik geri kazanım (static regain)** | Hız düşüşüyle kazanılan statik basınç, bir sonraki bölümün kaybını karşılar | Uzun ana kanallar, yüksek hızlı sistemler |

ACR-News adımları: (1) menfez yerlerini belirle, (2) güzergâhı çiz, yuvarlak kanal tercih et, dikdörtgende en/boy oranını düşük tut, (3) önerilen hızlarla ön boyutlandır, (4) kayıpları hesapla ve yeniden boyutlandır, (5) tekrarla, (6) gürültüyü kontrol et, susturucu kaybını ekle, (7) imalat resmi, (8) fan seçimi.

Dikdörtgen kanalın eşdeğer çapı (Huebscher): De = 1,30·(a·b)^0,625 / (a+b)^0,25. Örnek: 800x400 → ≈ 609 mm. Pratikte en/boy oranı ≤ 4:1 tutulur.

### 1.2 Önerilen hızlar (m/s) — Engineering ToolBox
| Kanal | Konfor (konut/ticari) | Endüstriyel | Yüksek hızlı |
|---|---|---|---|
| Ana kanal | 4–7 | 8–12 | 10–18 |
| Ana branşman | 3–5 | 5–8 | 6–12 |
| Branşman | 1–3 | 3–5 | 5–8 |

Depo örneklerinden okunan değerler:
- ASELSAN etiketlerinde kanal hızları 4,2–9,2 m/s, birim kayıp 0,56–0,85 Pa/m.
- Taze hava/egzoz panjurlarında efektif hız **2,5 m/s** ("PANJUR İLE SERBEST EMİŞ (PANJURDAKİ EFEKTİF HAVA HIZI 2,5m/s OLACAK ŞEKİLDE)").
- Çatıdan atış: "ÇATI ÜST KOTUNUN 1 (1,5) METRE ÜZERİNDEN JETCAP İLE ATIŞ".

### 1.3 Motor için önerilen varsayılanlar
- Üfleme/emiş ana kanal 5–6 m/s, branşman 3–4 m/s, menfez boyun hızı 2–2,5 m/s.
- Eşit sürtünme hedefi R = 0,8–1,0 Pa/m.
- Egzoz ve duman kanalı 8–10 m/s (otopark duman kanalı 10–12 m/s).
- Ölçüleri 50 mm adımına yuvarla (kare/dikdörtgen: 200x150, 250x200, 300x200 … ). Yükseklik kat yüksekliği ve asma tavan boşluğuyla sınırlanır; genişlik buna göre büyütülür.

Kaynaklar: [Engineering ToolBox — Sizing ducts](https://www.engineeringtoolbox.com/amp/sizing-ducts-d_207.html) · [ACR-News — Equal friction method](https://www.acr-news.com/masterclass-ducting-equal-friction-method-part-30) · [Düzce Üni. — Kanal çapları ve basınç kayıpları](https://acikerisim.duzce.edu.tr/items/3874886d-f073-4c96-b28f-925767d06edb)

---

## 2. Kanal planı çizim kuralları (Türk proje pratiği)

### 2.1 Geometri
- Kanallar plan üzerinde **çift çizgi** ile ölçekli çizilir (1/50 ya da 1/100). Ada Hayat katmanlarında sonek `-KNL2B` ("2 boyut") kullanılır: `-M-HVAC-S-…-KNL2B` üfleme (S = supply), `-R-` dönüş, `-E-` egzoz, `-E-WC-` WC egzozu.
- Kanal ekseni ayrı katmanda kesik çizgi ile verilebilir. Redüksiyon, dirsek, T ve pantolon parçaları gerçek geometrisiyle gösterilir.
- Kesitlerde kanal alt kotu ve asma tavan kotu yazılır (ör. "+7,40 / +7,00").
- Flexible bağlantılar ayrı katmanda ve ayrı sembolle gösterilir (`…-FLX-TRM`, "FLEX BAĞLANTI KANALI (İZOLELİ / İZOLESİZ)").
- Döşeme ve perde geçişleri için not yazılır: "TAVANDA YIRTIK 240*200", "DÖŞEMEDE YIRTIK 200*100" (Ada Hayat örneği).

### 2.2 Ölçü etiketi biçimleri (depodaki gerçek örnekler)
| Biçim | Örnek | Kaynak |
|---|---|---|
| `GxY` (mm) | `500x300`, `1800x150`, `610x610` | Ada Hayat, ASELSAN |
| `G/Y` (cm) | `80/80`, `120/80` | Ada Hayat |
| Yuvarlak kanal | `Ø250`, `Ø150` | ASELSAN, ORNEK_DUZEN |
| Etiket bloğu (ASELSAN) | `3300 m³/h` / `650x300` (cm: `65x30`) / `5,14 m/s` / `0,60 Pa/m` | `-M-HV-KANAL-TEXT`, `-M-HV-KANAL-HIZ`, `-M-HV-KANAL-PAM` |

ROTAŞ motoru için önerilen etiket: üst satır **`500x300`**, alt satır **`2.400 m³/h`**. Ana kanalda hız da yazılabilir (`v=4,4 m/s`). Etiket kanala paralel ve kanalın üstüne yazılır.

### 2.3 Akış okları ve renk/çizgi ayrımı
- Akış yönü kanal ekseni üzerinde dolu üçgen okla gösterilir (ASELSAN katmanı `-M-HV-MNF-OK`).
- Üfleme, emiş ve egzoz ayrı katman ve renkle çizilir. MTY'de üfleme rengi 20, egzoz rengi 4, duman egzozu rengi 1 (kırmızı).
- Taze hava girişi ve egzoz atışı cephede panjur sembolüyle gösterilir ("TAZE HAVA ALIŞ PANJURU", "EGZOST HAVASI ATIŞ PANJURU"), yanına debi yazılır ("TAZE HAVA GİRİŞİ: 65 000 m3/h").

### 2.4 Menfez ve difüzör sembolleri ve etiketleri
Lejant sözlüğü (ASELSAN "HAVALANDIRMA TESİSATI SEMBOLLERİ" ve Ada Hayat "ÇİZİM SEMBOLLERİ"):
- ÜFLEME KANALI, EMİŞ KANALLARI, WC EMİŞ KANALLARI, HASSAS KLİMA ÜFLEME/EMİŞ KANALI
- FLEX BAĞLANTI KANALI (İZOLELİ / İZOLESİZ)
- YUVARLAK KANAL ÜFLEME MENFEZİ / YUVARLAK KANAL EMİŞ MENFEZİ
- ÜFLEME SLOT DİFÜZÖRÜ / EMİŞ SLOT DİFÜZÖRÜ, EMİCİ LİNEER MENFEZ
- GEMİCİ ANEMOSTADI, SWIRL DİFÜZÖR, PERFORE MENFEZ
- EMİŞ MENFEZİ (TEK SIRA KANATLI), ÇİFT SIRA MENFEZ
- VD (VOLUM DAMPERİ), YANGIN DAMPERİ, MFD (motorlu yangın damperi), BDD (basınç düşürücü/geri basınç damperi), VAV
- ÇATI TİPİ ASPİRATÖR, DUVAR TİPİ ASPİRATÖR, JET CAP
- TAZE HAVA ALIŞ PANJURU, EGZOST HAVASI ATIŞ PANJURU

Menfez etiketi: tip kodu, ölçü ve debi. ASELSAN'da kod, ölçü ve debi ayrı katmanlardadır (`-M-HV-MNF-KOD`, `-M-HV-MNF-OLCU`, `-M-HV-MNF-TIP`).
Önerilen ROTAŞ biçimi: `M1 · 400x200 · 250 m³/h` ya da iki satır (`M1` / `250 m³/h`). Anemostat için `A1 · 300x300 · 300 m³/h` veya `Ø200`.
Mahal etiketinde debi ve hava değişimi ayrı katmanda yazılır (ASELSAN: `-M-MAHAL-DEBILER`, `-M-MAHAL-HAVA-DEGISIM`).

### 2.5 Cihaz etiketi (Ada Hayat örneği)
```
KLİMA SANTRALİ KS-1
LxWxH : 440x280x190 cm - 30000 m3/h - 1500 kg
Cihaz Ne: 80.0 kW
```

---

## 3. WC ve banyo egzozu

- **DIN 18017-3 asgari egzoz debileri** (penceresiz mahal):

  | Mahal | Sürekli (≥ 12 h/gün) | Kesikli |
  |---|---|---|
  | Banyo | 40 m³/h | 60 m³/h |
  | WC | 20 m³/h | 30 m³/h |

  - Kapatmadan sonra 5 m³ ek emiş yapılır (zaman röleli aspiratör).
  - Kapıda 150 cm² sürekli açık transfer menfezi bırakılır.
  - Ortak şafta bağlanan aspiratörlerde fan çıkışına yangın damperi konur.
- **Türk pratiği:** Hela başına 50–100 m³/h ya da saatte 10–15 hava değişimi. Ortak WC'lerde klozet/pisuvar başına 50–100 m³/h. ROTAŞ örneği (ORNEK_DUZEN): **"Wc Aspiratörü 160 m³/h - 50 Pa - Ø150 mm"**, iki kademeli 80/160 m³/h.
- **Şaft sistemi:**
  - Her katta Ø100–150 bağlantı ve geri dönüşsüz klape.
  - Ana kolon şaftta yukarı çıkar, çatıda **çatı tipi fan** (ör. 240/480 m³/h) bulunur.
  - Çizimde "mek. havl." şaftı, kolon numarası (WC-E1 … ) ve izometri gösterilir. İzometride her kat bağlantısının debisi ve toplam debi yazılır.
- Mekânik egzoz yapılan mahalde besleme hava için kapı altı boşluğu ya da kapı menfezi notu yazılır.

Kaynaklar: [SBZ — DIN 18017-3 özeti (PDF)](https://www.sbz-online.de/sites/default/files/ulmer/de-sbz/document/file_186091.pdf) · [Baunetz Wissen — Mindestvolumenströme](https://www.baunetzwissen.de/bad-und-sanitaer/fachwissen/heizung---lueftung/geforderte-mindestvolumenstroeme-fuer-baeder-172824) · depo: `ornekler/ORNEK_DUZEN.md`

---

## 4. Mutfak davlumbaz egzozu

- **VDI 2052 yöntemi:** Her cihazın duyulur ısısına göre termal tüy debisi hesaplanır. Sonuç eşzamanlılık faktörü φ ve davlumbaz verimiyle düzeltilir.
  - Eşzamanlılık φ: okul/hastane 0,5–0,7; merkezi mutfak 0,8–1; ticari/endüstriyel 0,9–1.
  - Davlumbaz verimi: kanopi 0,7, duvar arkası (backshelf) 0,5.
  - Flushout faktörü 1,10–1,35 (tavan difüzörü 1,20, döşeme ızgarası 1,15).
- **Pratik kontrol (IMC/ASHRAE 154):** Listelenmemiş kanopi davlumbazda orta yükte asgari ~300 cfm/ft ≈ **1.670 m³/h·m**. Ada tipi çift davlumbazda ön ve yan taşma (overhang) ≥ 305 mm.
- **Yaygın Türk pratiği** ⚠ doğrula:
  - Davlumbaz yüz hızı 0,25–0,5 m/s.
  - Kanal hızı 7,5–10 m/s; NFPA 96'ya göre asgari 2,5 m/s (yağ çökmesin diye).
  - Taze hava (make-up) egzozun %80–90'ı, mutfak hafif negatif basınçta.
  - Labirent tip yağ filtresi kullanılır.
  - Kanal 1,25–1,5 mm siyah sac ve kaynaklı imal edilir, temizleme kapakları konur.
  - Fan F400 sınıfı ya da mutfak tipi (motor hava akışı dışında) seçilir.
  - Davlumbaz kanalı diğer kanallarla birleştirilmez. Egzoz çatıdan en az 1 m yukarıda, jetcap ile atılır.
- **Yönetmelik:** Binaların Yangından Korunması Hakkında Yönetmelik (BYKHY) **Bölüm 4.4 "Mutfaklar"** davlumbaz ve egzoz kanalı yangın şartlarını içerir. Madde içerikleri resmî metinden alınmalıdır.
- **Çizim:**
  - Davlumbaz dikdörtgen sembolle ve ölçüsüyle gösterilir (ör. "DAVLUMBAZ 3000x1200 - 5.000 m³/h").
  - Egzoz kanalı ayrı renkle çizilir, taze hava menfezleri mutfak içine yerleştirilir.
  - Yağ tutucu ve elektrostatik filtre (ESP) ya da karbon ünitesi varsa yazılır.

Kaynaklar: [xpair — VDI 2052 yöntemi](https://conseils.xpair.com/consulter_savoir_faire/ventilation-locaux-cuisine/methode_calcul_norme.htm) · [AirCondLounge — CKV exhaust calculation](https://aircondlounge.com/commercial-kitchen-ventilation-ckv-exhaust-calculation)

---

## 5. Otopark havalandırması ve duman tahliyesi

### 5.1 Sınıflandırma (TS 3419 / VDI 2053 aktarımı, tesisat.org)
- Kat alanının %5'inden küçük açıklık varsa otopark **kapalı** sayılır.
- Duvarların ≥ 1/3'ü açık ve karşılıklı mesafe ≤ 70 m ise **açık** sayılır.
- Karşılıklı açıklıklar kat alanının ≥ %2,5'i ise doğal ve mekanik havalandırma birlikte kullanılabilir. Bu oranın altında tam mekanik havalandırma gerekir.
- Otopark Yönetmeliği'nde araç başına **20 m²** park alanı esas alınır (manevra hariç). Kamyon ve otobüs için 50 m².

### 5.2 Debi kriterleri
| Durum | Değer | Kaynak |
|---|---|---|
| Günlük (kirletici) havalandırma | **6 h⁻¹** (İngiltere ADF/BS 7346-7). ROTAŞ: **4 h⁻¹** | Colt, CIBSE; README |
| Birim alan yöntemi | Konut 6 m³/h·m², AVM 12 m³/h·m² | VDI 2053 / TS 3419 (tesisat.org) |
| CO yöntemi | İç ortam sınırı 60 ppm (VDI 2053). İngiltere: 8 saat ortalaması 30 ppm, rampa ve çıkışta 15 dk ortalaması 90 ppm | tesisat.org, Colt |
| Duman tahliyesi (smoke clearance) | Sadece yangın katında **10 h⁻¹**. Her katta motorlu duman damperi | BS 7346-7, Colt; README |
| Türk yönetmeliği | 2.000 m²'den büyük kapalı otoparklarda 10 h⁻¹ ya da ısı/duman kontrol sistemi. Tercih edilen yangın bölgesi ≤ 5.000 m² ve her bölgeye en az bir duman şaftı ⚠ doğrula (madde no) | Yangın Sempozyumu 2019 |

### 5.3 Jet fan sistemi
- **Amaç türleri:** Duman temizleme (10 h⁻¹, korunan bölge yoktur), duman kontrolü (duman yangın bölgesinden çıkmaz, itfaiye rüzgâr üstünden 10 m'ye kadar yaklaşabilir) ve sadece CO seyreltme.
- **Duman kontrolü kesit hızı:**
  - Jet fansız kesitte 0,5–1,0 m/s.
  - Bölge genişliğine göre: 20 m → 0,96; 30 m → 0,83; 40 m → 0,76; 50 m → 0,70; 60 m → 0,65 m/s.
  - Sprinklerli otoparkta 40–50 m genişlikte 0,40–0,50 m/s kabul edilebilir.
  - Kaynak örneği: 6.000 m² taban alanında 10 h⁻¹ (180.000 m³/h) bazı mimarilerde yeterli kesit hızını sağlamıyor.
- **Tasarım kuralları (BS 7346-7):**
  - Kaçış yolu ve rampada hız ≤ 5 m/s, taze hava girişinde ≤ 2 m/s.
  - Taze hava debisi egzozun ≥ %70'i, yangın bölgesi negatif basınçta.
  - Jet fan debisi egzoz debisini aşmaz.
  - Yangın sinyalinde ana fanlar tam kapasiteye geçer, jet fanlar gecikmeli devreye girer.
  - Ana fanlarda %50 yedek bulunur.
  - Sprinkler başlıkları jet fan çıkışından uzak tutulur.
  - Çok katlı otoparkta şaft ağızlarına ve her fana motorlu damper konur.
- **Jet fan:**
  - İtki: impuls tipi ≈ 50 N, endüksiyon tipi ≈ 100 N (ör. 98/24 N tam/yarım hız).
  - Aralık tipik 10–15 m; 400 mm fan için 10 m aralık 15 m'den belirgin farklı hız profili verir.
  - Kesin yerleşim CFD ile doğrulanır.
- **Fan sıcaklık sınıfı:** EN 12101-3'e göre **F300 (300 °C / 60 dk)**. Kanal, askı ve bağlantıların ergime sıcaklığı > 800 °C olmalı.
- **Kademeli çalışma (CO):**
  - < 15 ppm: egzoz fanlarının yarısı düşük devirde.
  - 15–30 ppm: jet fanlar ve egzozun yarısı düşük devirde.
  - > 30 ppm: tüm egzoz fanları düşük devirde.
  - Yangın sinyalinde tüm fanlar tam devirde.
- **CO dedektörü:** Yaygın pratikte her ~400–600 m²'ye bir dedektör, yerden 1,5–1,8 m yükseklikte ⚠ doğrula (üretici kataloğu). Kullanıcı 536 m² otoparkta 14 araç için 14 dedektör kullanmıştı.
- **Taze hava:** Rampa ve cephe açıklıklarından alınır, tavandan değil duvardan girmelidir. Rampa yetmezse ayrı taze hava şaftı açılır.
- **Hesap formülleri (Yangın Sempozyumu 2019):**
  - Duman debisi V = M·(Ts+273) / [ρ·(To+273)]·3600
  - Kütle debisi M = 0,19·P·Y^1,5 (P: yangın çevresi, Y: duman tabakası yüksekliği)
  - Duman sıcaklığı Ts = Q/M + To
  - Jet fan itkisi N = V·Q·ρ
- **Çizim:**
  - Jet fan oklu dikdörtgen sembolle gösterilir, itki yönü ve "JF-1 50 N" yazılır.
  - Egzoz şaftı, fan odası ve egzoz fanı etiketi verilir ("EF-1 60.000 m³/h - 600 Pa - F300").
  - CO dedektörü sembolü ve duman bölgesi sınırları (kesik çizgi, "DUMAN BÖLGESİ-1") çizilir.
  - Taze hava girişi ok ve debi ile yazılır.

Kaynaklar: [Yangın Sempozyumu 2019 — Kapalı otoparklarda duman tahliye (PDF)](https://yanginsempozyumu.org/wp-content/uploads/2019/10/2019-005.pdf) · [tesisat.org — Çok katlı otopark havalandırma hesabı](https://www.tesisat.org/cok-katli-otopark-havalandirma-hesabi.html) · [Enerji ve Tesisat — Kapalı otopark havalandırması / duman kontrolü](https://www.enerjivetesisat.com/tesisat/hvac/1861-kapal-otopark-havalandrmas-makale?start=2) · [Colt — Car park ventilation (PDF)](https://www.coltinfo.sg/files/pdf/Singapore/Colt%20ventilation%20systems%20for%20car%20parks.pdf) · [CIBSE Journal — Driving home fire safety](https://www.cibsejournal.com/uncategorized/driving-home-fire-safety/) · [Lexpera — Otopark Yönetmeliği (mülga konsolide)](https://www.lexpera.com.tr/mevzuat/yonetmelikler/otopark-yonetmeligi-4)

---

## 6. Sığınak havalandırması

### 6.1 Sığınak Yönetmeliği (güncel, Madde 8)
- **Kapasite:**
  - Kişi başı ≥ **1 m² net alan**. WC, duş ve mutfak nişi bu alana dahil değildir.
  - Kişi sayısı: konutta daire tipine göre (1 odalı 2 kişi … 3+ odalı 4 kişi); konaklama tesisinde onaylı yatak sayısı + %20; diğer binalarda kat alanı / 20.
- **Fiziksel şartlar:**
  - Net yükseklik ≥ 2,40 m.
  - Net alanı **> 100 m²** olan sığınakta **iki çıkış** bulunur.
  - Girişte demir kapı ve en az bir dik açılı dönüş olur.
  - 100 kişiye bir WC ve lavabo (kadın/erkek ayrı).
  - 100 m² üstünde ≥ 2,30 m² mutfak nişi.
- **Havalandırma (8/b-ç):**
  - Mekanik havalandırma zorunludur.
  - Fan, motoruna uygun jeneratör veya UPS ile beslenir. Jeneratör arızasında **el ile (kollu) çalıştırma** düzeni bulunur.
  - Koruma döneminde emiş havası **nükleer tip HEPA filtre ya da kum havuzu (kum filtresi)** üzerinden alınır; bu elemanlar tehdit anında monte edilir.
  - Barış döneminde sadece **G4** kaba filtre kullanılır.
  - Debi tablosu yönetmelikte görsel tablo olarak verilir. Kanal güzergâhı, menfez sayısı ve yerleri mühendise bırakılmış, TS 3419 ve TS 3420'ye atıf yapılmıştır.

### 6.2 Kişi başı debi (MMO TESKON 2005 / kutmankaplan)
| Kapasite | Normal havalandırma | Koruma (filtreli) havalandırma |
|---|---|---|
| ≤ 50 kişi | 9 m³/h (EU3/G3 toz filtresi) | 1,8 m³/h |
| 51–150 kişi | 3 m³/h | 3 m³/h |
| > 150 kişi | 4,5 m³/h | 4,5 m³/h |

- **Hava kalitesi:** O₂ ≥ %19, CO₂ ≤ %2, kuru termometre sıcaklığı ≤ 29 °C. Kişi başı solunum ≥ 0,5 m³/h.
- **Aşırı basınç:** Sığınak içi dışarıya göre **+50 Pa** tutulur. Her kapı 50 Pa'da ≈ 216 m³/h sızdırır; besleme debisi egzozu kapı başına bu kadar aşmalıdır.
- **Filtre sırası:**
  - Yangın riski yüksek: kum filtresi → toz filtresi → aktif karbon.
  - Yangın riski düşük: toz → nükleer (HEPA) → aktif karbon.
  - Normal dönem: toz + aktif karbon (ya da kompakt KBRN filtre).
- **Kum filtresi:**
  - 1–25 kişi: 1,5 m³ kum, 1 m yükseklik.
  - 25–50 kişi: 3 m³ kum, 1 m yükseklik.
  - 50–150 kişi: 60 m³/h başına 1 m³ kum, 2 m yükseklik (2 m'de basınç kaybı 200 Pa).
  - Katmanlar: 2–5 mm çakıl (emiş ızgarasını 5 cm örter) + 0,4–0,8 mm kuvars kumu.
  - Dipte DN25 PVC yoğuşma drenajı bulunur.
- **Örnek basınç bütçesi (150 kişi, 450 m³/h):** emiş hücresi 22 + aktif karbon 50 + kanal/menfez 15 + iç basınç 50 + kum 200 = **337 Pa**. 400 Pa fan seçilmiştir.
- **Damper ve armatürler (lejant):**
  - AV: dış hava kapama damperi; ALV: egzoz (atık hava) damperi; UV: yüksek basınç (patlama/şok) valfi.
  - Dışa açılan tüm açıklıklar gaz sızdırmaz olmalıdır (gaz sızdırmaz kapak).
  - Egzoz WC ve duş üzerinden atılır.
  - 50 kişi üstünde havalandırma sistemi yangın yönetmeliğine göre duman tahliyesi olarak da kullanılabilir (BYKHY Madde 59 atfı) ⚠ doğrula.
- **Tipik hava yolu (şema sırası):** Dış hava bacası (korunaklı alandan) → patlama/şok valfi (UV) → kapama damperi (AV) → [kum filtresi] → toz filtresi → [HEPA] → aktif karbon → el/motorlu vantilatör → dağıtım kanalı ve menfezler → sığınak → aşırı basınç ventili → WC/duş → egzoz damperi (ALV) → egzoz bacası.
  - Patlama valfi, aşırı basınç ventili ve el vantilatörü için yönetmelikte ölçü verilmez; üretici kataloğundan seçilir.
- **ROTAŞ uygulaması:**
  - Hesap Bölüm 0'daki kurallarla yapılır (alan × 4 h⁻¹, egzoz %10 az, 100 m² üstünde duman egzozu).
  - Yukarıdaki kişi başı tablo **kontrol** olarak tabloya eklenebilir; kullanıcı kuralının yerine geçmez.
  - Perde açıklığı ölçüsü yazılır.

Kaynaklar: [Lexpera — Sığınak Yönetmeliği](https://www.lexpera.com.tr/mevzuat/yonetmelikler/siginak-yonetmeligi) · [MMO TESKON 2005 — Sığınaklarda havalandırma ve filtrasyon (PDF)](https://mmoteskon.org/wp-content/uploads/2014/12/2005-24.pdf) · [Sistem Havalandırma — Sığınak havalandırması](https://www.sistemhavalandirma.com/siginak-havalandirmasi/) · [kutmankaplan — 500 m² sığınak havalandırma](https://www.kutmankaplan.net/2019/12/500-m-sgnak-projesi-havalandrma-hesab.html) · [Alomaliye — 07.11.2025 Sığınak Yönetmeliği değişikliği](https://www.alomaliye.com/2025/11/07/siginak-yonetmeliginde-degisiklik-yapilmasina-dair-yonetmelik/)

---

## 7. Merdiven basınçlandırma (BYKHY Madde 89 + TS EN 12101-6)

### 7.1 Ne zaman zorunlu (BYKHY Md. 89, ikincil kaynak aktarımı)
- Konut dışı binalarda merdiven kovası yüksekliği **> 30,50 m** ise.
- **4'ten fazla bodrum katı** olan binada bodrum merdivenleri.
- Konutlarda yapı yüksekliği **> 51,50 m** ise.
- Acil durum asansörü kuyuları.
- Yangın güvenlik holü (Md. 34): yapı yüksekliği > 51,50 m olan ve acil asansörü bulunan binada zorunludur. Hol alanı 3–6 m², acil asansör holünde 6–10 m²; duvarlar ≥ 120 dk, kapılar ≥ 90 dk yangın dayanımlı.
- Yüksek bina tanımı: bina yüksekliği > 21,50 m ya da yapı yüksekliği > 30,50 m.

### 7.2 Performans kriterleri
| Kriter | BYKHY (Türk) | EN 12101-6 Sınıf B (itfaiye) |
|---|---|---|
| Kapılar kapalıyken basınç farkı | ≥ **50 Pa** | sınıfa göre |
| Kapı açıkken basınç farkı | ≥ **15 Pa** | — |
| Kapı açma kuvveti | ≤ **110 N** | ≤ **100 N** |
| Açık kapıda hava hızı | ort. ≥ **1 m/s** (çıkış kapısı + yangın katı + üst kat kapısı açık) | **2 m/s** (yangın bölgesi ile korunan alan arası) |
| Kaçak payı | — | +%15 |

- EN 12101-6 sınıfları: A (yerinde koruma/konut), B (itfaiye müdahalesi), C (eşzamanlı tahliye), D (uyuyan kişiler/oteller), E (kademeli tahliye), F (itfaiye + kaçış). Sınıf mimar ve yangın uzmanıyla seçilir.
- 2 m/s'de açık kapı direnci ≈ 6 Pa. Örnek: 2 m² kapı için 14.400 m³/h; tahliye yöntemine göre toplam 28.800–43.200 m³/h.
- Yangın katında havanın çıkacağı yol (duman penceresi ya da mekanik egzoz) yoksa basınçlar eşitlenir ve sistem çalışmaz.

### 7.3 Uygulama kuralları
- Emiş dış havadan, egzoz ağızlarına ≥ **5 m** mesafeden alınır. Fan emişinde duman dedektörü bulunur ve duman algılarsa fanı durdurur.
- Kova yüksekliği > 25 m ise birden fazla üfleme noktası kullanılır; iki nokta varsa aralarında kova yüksekliğinin yarısı kadar mesafe olur. Yapı yüksekliği > 51,50 m ise her katta ya da en çok 3 katta bir üfleme yapılır.
- Frekans kontrollü fan ve kova içi basınç sensörü kullanılır. **Aşırı basınç tahliye damperi** konur.
- Fan yangın alarmıyla otomatik başlar, elle aç/kapa anahtarı bulunur (BYKHY Md. 80 ve 82: izleme ve acil kontrol fonksiyonları).
- Basınçlandırma kanalına yangın damperi konmaz.
- **Hızlı kontrol:** 1,89 m² kapı × 3 açık kapı × 1 m/s = 20.412 m³/h, artı kat başına 0,09 m³/s kaçak. 20 katta toplam ≈ 26.900 m³/h, üstüne emniyet payı eklenir.
- **Çizim:**
  - Kat planında üfleme menfezi merdiven kovası duvarında gösterilir ("BASINÇLANDIRMA MENFEZİ 600x400 - 3.000 m³/h").
  - Şaft, çatıda fan ("MBF-1 28.000 m³/h - 600 Pa") ve şemada kat kat menfezler ile aşırı basınç damperi gösterilir.
  - Kullanıcının Bolu Özpolat 5* Otel projesinde basınçlandırma hesapları kendi güncellediği biçimde kullanılmaktadır.

Kaynaklar: [tesisat.org — Yangın merdiveni basınçlandırma fan seçimi](https://www.tesisat.org/yangin-merdiveni-basinclandirma-fan-secimi.html) · [Yangın Sempozyumu 2022 — Basınçlandırma bildirisi (PDF)](https://yanginsempozyumu.org/wp-content/uploads/2022/09/010.pdf) · [REHVA Journal — EN 12101-6 tasarım çözümleri](https://www.rehva.eu/rehva-journal/chapter/analysis-of-design-solutions-for-overpressure-systems-in-accordance-with-en-12101-6) · [EMO — BYKHY Md. 80/82 (PDF)](https://emo.org.tr/ekler/fc9643ef5d476da_ek.pdf) · [BYKHY metni (ayna, Md. 1–40)](https://www.abdurrahmanince.net/bykhy.pdf)

---

## 8. Duman tahliyesi (genel)

- BYKHY Bölüm 6 "Duman Kontrol Sistemleri": 6.2 duman tahliye ve kontrolü, 6.3 basınçlandırma. Md. 87 kanal malzemesine atıf yapar ⚠ doğrula.
- **Duman kontrol yaklaşımları:**
  - Doğal duman tahliyesi: kapaklar ve pencereler.
  - Mekanik duman egzozu: fanlar F300/F400, kanallar duman sızdırmaz.
  - Basınçlandırma.
  - Otopark ve sığınakta havalandırma sisteminin yangın modunda duman tahliyesine geçmesi.
- Yangın modunda otomatik kontrol (Md. 82): yangın kapılarının serbest bırakılması, basınçlandırmanın başlatılması, duman kontrol işlemleri, asansörlerin yönetimi.
- Duman kontrol cihazlarının izlenmesi yangın paneli üzerinden yapılır; bina otomasyonuna bırakılmaz. Damperler 24 V DC beslenir.
- **Çizim:** Duman egzoz kanalı `MTY-DUMAN-EGZOZ` katmanında kırmızı çizilir. Duman damperi (MFD), duman bölgesi sınırı ve duman fanı etiketi ("DEF-1 … m³/h - F400/120") gösterilir.

---

## 9. Klima / VRF kat planı ve şeması

### 9.1 Kat planı
- **İç üniteler:**
  - Gerçek boyutlu blokla çizilir (kaset 4 yönlü 570x570 ya da 840x840, gizli tavan, duvar tipi).
  - Etiket: `VRF-İÇ-1 · 4,5 kW` ya da depodaki örnek biçimi `FCU-5 · 750 m3/h`.
  - Kat bazında numaralandırılır.
- **Bakır borular:**
  - Gaz ve sıvı hattı tek çizgide (`MTY-KLIMA-BAKIR BORU`) çizilir, çap etiketi `Ø15,88/Ø9,52` biçiminde yazılır.
  - 3 borulu (ısı geri kazanımlı) sistemde BS kutusu (branch selector) gösterilir.
  - Kolon numarası: `VRF-0x` (ASELSAN lejantı "KLİMA KOLON NUMARASI", "KLİMA GAZ BORUSU").
- **Refnet:**
  - Y-branş sembolü ile çizilir, model kodu yazılır (ör. KHRQ22M29T).
  - Kurulum kuralı: yatay ya da düşey takılır. Header tipi yatay düzlemde olur.
  - Eşdeğer boy: refnet joint 0,5 m, header 1 m.
  - Tipik üretici kuralları: ilk branştan en uzak iç üniteye ≤ 40 m (koşullu 90 m); toplam ve eşdeğer boy limitleri, dış-iç ve iç-iç kot farkı limitleri üretici kataloğundan alınır ⚠ doğrula.
- **Drenaj:**
  - `MTY-KLIMA-DRENAJ` katmanında çizilir, en az **%1 (1/100) eğim** verilir.
  - Tipik çap PVC Ø32–40, toplayıcıda Ø50.
  - Pis su tesisatına sifonlu bağlanır.
  - Kaset ünitede drenaj pompası bulunur, kalkış ≤ 500–850 mm (üreticiye göre).
- **Dış ünite:**
  - Çatı ya da teras planında gösterilir, servis boşluğu ön 1.500 mm, emiş 500 mm.
  - Kaide ≥ 150 mm, kar bölgesinde alt şase kar seviyesinin 500 mm üstünde.
  - Etiket: `VRF-DIŞ-1 · 45 kW · 3 borulu · -15 °C` (ASELSAN notu: "VRF sistemi 3 borulu ve -15°C de çalışır olmalıdır").
- **Notlar:**
  - Bakır borular izoleli yapılır. Kaynak azot altında (≈ 0,02 MPa) yapılır.
  - Vakum 500 mikron, sızdırmazlık testi tasarım basıncında (3,3 MPa'ya kadar).
  - Sistem kapasite oranı %50–130 (bazı serilerde %200'e kadar).
  - Kullanıcının VRF merkezi kontrol projesi (CE52-24/F(C), 255 iç ünite) referans alınabilir.

### 9.2 VRF şeması (tek hat)
- Dış ünite en üstte ya da çatı kotunda çizilir, kolonlar dikey hatlarla iner, katlarda refnetlerden iç ünitelere dallanılır.
- Her boru parçasında gaz/sıvı çapı ve her iç ünitede model ve kapasite yazılır.
- Kumanda hattı (F1-F2 haberleşme) kesik çizgiyle çizilir; merkezi kumanda ve otomasyon arabirimi gösterilir.
- Boru çapları üretici yazılımından alınır. Daikin örneği (kapasite indeksine göre emme gazı):

  | Kapasite indeksi | Emme gazı çapı |
  |---|---|
  | < 54 | 15,9 mm |
  | < 72 | 19,1 mm |
  | < 111 | 22,2 mm |
  | < 230 | 28,6 mm |
  | < 300 | 34,9 mm |
  | > 300 | 41,3 mm |

  Sıvı hattı < 54 için 9,5 mm.

Kaynaklar: [Daikin VRV kurulum kılavuzu (PDF)](https://inspectapedia.com/heat/Daikin-VRV-Install-Manual.pdf) · [AirCondLounge — Home VRF design guide](https://aircondlounge.com/home-vrf-system-design-guide-with-example-and-diagram/) · depo: `kutuphane/ornek_mekanik/aselsan_teknopark/KATALOG.md` (lejant: KLİMA GAZ BORUSU, KLİMA KOLON NUMARASI, TAVAN TİPİ GİZLİ/KASETLİ FANCOİL)

---

## 10. Türk projelerinden lejant ve etiket örnekleri (birleşik sözlük)

**Kanallar:** ÜFLEME KANALI · EMİŞ KANALI · TAZE HAVA KANALI · EGZOZ KANALI · WC EMİŞ KANALI · MUTFAK DAVLUMBAZ EGZOZ KANALI · DUMAN EGZOZ KANALI · BASINÇLANDIRMA KANALI · FLEX BAĞLANTI KANALI (İZOLELİ / İZOLESİZ)

**Menfez/difüzör:** ÜFLEME MENFEZİ (ÇİFT SIRA KANATLI) · EMİŞ MENFEZİ (TEK SIRA KANATLI) · YUVARLAK KANAL ÜFLEME/EMİŞ MENFEZİ · KARE/YUVARLAK ANEMOSTAT · GEMİCİ ANEMOSTADI · SWIRL DİFÜZÖR · SLOT (LİNEER) DİFÜZÖR · PERFORE MENFEZ · KAPI TRANSFER MENFEZİ · DIŞ HAVA PANJURU (TAZE HAVA ALIŞ) · EGZOST HAVASI ATIŞ PANJURU · JET CAP

**Armatür:** VD VOLUM DAMPERİ · YANGIN DAMPERİ (FD) · MOTORLU YANGIN/DUMAN DAMPERİ (MFD) · GERİ BASINÇ DAMPERİ (BDD) · AŞIRI BASINÇ TAHLİYE DAMPERİ · VAV · SUSTURUCU · ESNEK BAĞLANTI (BREZENT)

**Cihaz:** KLİMA SANTRALİ (KS) · ISI GERİ KAZANIM CİHAZI (IGK) · ÇATI TİPİ ASPİRATÖR · DUVAR TİPİ ASPİRATÖR · KANAL TİPİ FAN · JET FAN · EGZOZ FANI (F300/F400) · BASINÇLANDIRMA FANI · WC ASPİRATÖRÜ · CO DEDEKTÖRÜ

**Sığınak:** PATLAMA (ŞOK) VALFİ · GAZ SIZDIRMAZ KAPAK · KUM FİLTRESİ · TOZ FİLTRESİ (G4) · AKTİF KARBON / KBRN FİLTRE · EL İLE ÇALIŞAN VANTİLATÖR · AŞIRI BASINÇ VENTİLİ · DIŞ HAVA KAPAMA DAMPERİ (AV) · EGZOZ DAMPERİ (ALV)

**Klima:** VRF DIŞ ÜNİTE · VRF İÇ ÜNİTE (KASET / GİZLİ TAVAN / DUVAR) · REFNET · BS KUTUSU · KLİMA GAZ BORUSU · KLİMA SIVI BORUSU · KLİMA DRENAJ BORUSU · KLİMA KOLON NUMARASI · KUMANDA HATTI

**Örnek yazılar:**
- `500x300` / `2.400 m³/h`
- `Ø150`
- `M1 400x200 250 m³/h`
- `Wc Aspiratörü 160 m3/h-50 pa Ø150 mm`
- `TAZE HAVA GİRİŞİ: 65 000 m3/h`
- `TAVANDA YIRTIK 240*200`
- `ÇATI ÜST KOTUNUN 1 METRE ÜZERİNDEN JETCAP İLE ATIŞ`
- `PANJURDAKİ EFEKTİF HAVA HIZI 2,5 m/s`
- `KARE PETEK MENFEZLER SÖKÜLEBİLİR FİLTRELİ TİP OLACAKTIR`
- `FCU-5 750 m3/h`
- `VRF sistemi 3 borulu ve -15°C de çalışır olmalıdır`

---

## 11. Açık konular / doğrulanacaklar
1. BYKHY'nin otopark havalandırması, mutfak (Bölüm 4.4) ve havalandırma kanalı/yangın damperi maddelerinin resmî metni. mevzuat.gov.tr bu ortamdan açılamadı; ayna PDF yalnız Md. 1–40'ı içeriyor.
2. Sığınak Yönetmeliği 8/b-ç debi tablosu görsel olduğu için metinde yok. Bölüm 6.2'deki değerler TESKON ve kutmankaplan aktarımıdır.
3. CO dedektörü kapsama alanı ve montaj yüksekliği seçilen üreticinin kataloğundan alınmalıdır.
4. VRF boru boyu ve kot farkı limitleri seçilen markanın (Daikin, Mitsubishi, LG, Samsung …) kurulum kılavuzundan alınmalıdır.
