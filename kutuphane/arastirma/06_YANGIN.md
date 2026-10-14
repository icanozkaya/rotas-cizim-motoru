# 06 — Yangın Söndürme Tesisatı: Tasarım Kuralları ve Çizim Pratiği

Hazırlanma: 14.10.2026 · Kapsam: TS EN 12845, NFPA 13, TS EN 671, BYKHY (2007/12937, güncel değişikliklerle) ve Türk proje çizim pratiği.

> **Güven işaretleri:** ✅ kaynakta doğrulandı · ⚠️ hafızadan / ikincil kaynaktan, uygulamadan önce standart metninden kontrol edilmeli.
> TS EN 12845 ve NFPA 13 ücretli standartlardır; tam tablolar web'de açık değildir. Değerler sunum, ders notu ve çeviri metinlerinden derlenmiştir.
> **ROTAŞ kalıcı kuralları** (README) bu belgedeki genel pratiğin önündedir. Özet en sonda (§14).

---

## 1. Tehlike sınıfları ve tasarım kriterleri

### 1.1 TS EN 12845: yoğunluk, işletme alanı, süre

| Sınıf | Tasarım yoğunluğu (mm/dk = l/dk·m²) | İşletme alanı, ıslak / ön tepkili (m²) | İşletme alanı, kuru / alternatif (m²) | Süre (dk) | Durum |
|---|---|---|---|---|---|
| LH (Düşük) | 2,25 | 84 | İzin yok, OH1 olarak tasarlanır | 30 | ✅ |
| OH1 | 5,0 | 72 | 90 | 60 | ✅ |
| OH2 | 5,0 | 144 | 180 | 60 | ✅ |
| OH3 | 5,0 | 216 | 270 | 60 | ✅ |
| OH4 | 5,0 | 360 | İzin yok, HHP1 olarak tasarlanır | 60 | ✅ |
| HHP1 | 7,5 | 260 | 325 | 90 | ✅ |
| HHP2 | 10,0 | 260 | 325 | 90 | ✅ |
| HHP3 | 12,5 | 260 | 325 | 90 | ✅ |
| HHP4 | Baskın (deluge) sistem | – | – | 90 | ✅ |
| HHS (depolama) | Depolama yüksekliği, kategori (ST1–ST6) ve yönteme göre EN 12845 Tablo 4–6 | 260–300 | – | 90 | ⚠️ |

- **Süre:** LH 30 dk, OH 60 dk, HH 90 dk. BYKHY Md. 92/3 de aynı süreleri ister. ✅
- **K faktörü** (EN 12845 Tablo 37): LH K57; OH K80; HHP/HHS K80 veya K115. Tavan 10 m'nin üzerindeyse K80/115 kullanılır. ✅
- **En elverişsiz başlıkta en düşük basınç:** LH 0,70 bar; OH 0,35 bar; HHP/HHS 0,50 bar. ✅
- **En küçük boru çapı:** LH 20 mm; K ≤ 80 başlığı besleyen OH/HH boruları 20 mm; diğerleri 25 mm. ✅ HH branşmanlarında en az 25 mm. ✅
- **Başlık debisi:** Q = K·√P (Q l/dk, P bar). Örnek: K80 ve 0,56 bar → 60 l/dk. ✅

### 1.2 Tipik kullanım örnekleri (EN 12845 Ek A ve BYKHY Ek-1 mantığı) ⚠️

| Sınıf | Örnek mahaller |
|---|---|
| LH | Okul derslikleri, ofis (yangın yükü düşük, alan ≤ 126 m² bölmeli), hastane yatak katları |
| OH1 | Hastane, otel, kütüphane (raf hariç), ofis, restoran, konut tipi kullanımlar |
| OH2 | Kapalı otopark, laboratuvar, fırın ve pastane, çamaşırhane, mağaza |
| OH3 | AVM, depolu mağaza, matbaa, elektronik ve plastik imalat, sinema/tiyatro |
| OH4 | Sahne, film stüdyosu, kibrit/köpük/kauçuk imalatı, sergi salonları |
| HHP | Halı, köpük plastik, boya-vernik, alkollü ürün imalatı |
| HHS | Raflı veya yığın depolama (malzeme kategorisi ve yüksekliğe göre) |

> ROTAŞ notu: Deepo depo ve OBA Makarna çalışmalarında olduğu gibi depolama alanları HHS/OH-3 ayrımıyla ayrıca değerlendirilir.

### 1.3 NFPA 13: yoğunluk/alan (eğrinin alt noktası)

| Sınıf | Yoğunluk (gpm/ft²) → mm/dk | Alan (ft²) → m² | Hortum payı (gpm → l/dk) | Süre (dk) | Durum |
|---|---|---|---|---|---|
| LH | 0,10 → 4,1 | 1500 → 139 | 100 → 380 | 30 | ✅ |
| OH1 | 0,15 → 6,1 | 1500 → 139 | 250 → 950 | 60–90 | ✅ |
| OH2 | 0,20 → 8,1 | 1500 → 139 | 250 → 950 | 60–90 | ✅ |
| EH1 | 0,30 → 12,2 | 2500 → 232 | 500 → 1900 | 90–120 | ✅ |
| EH2 | 0,40 → 16,3 | 2500 → 232 | 500 → 1900 | 90–120 | ✅ |

- En uç başlıkta en düşük basınç 7 psi (0,48 bar). ✅
- Hidrolik alanın şekli: dikdörtgen, uzun kenar ≥ 1,2·√A ve branşmanlara paralel. EN 12845'te de aynı kural uygulanır. ⚠️
- NFPA 13'te OH3/OH4 yoktur. EN'deki OH3/OH4, NFPA'da OH2 veya EH1 ile karşılanır.

---

## 2. Başlık yerleşimi: alan, aralık, duvar mesafesi

### 2.1 TS EN 12845 (standart sarkık/dik başlık)

| Sınıf | Başlık başına en fazla alan | En fazla aralık S×D, standart düzen | Şaşırtmalı düzen | Durum |
|---|---|---|---|---|
| LH | 21 m² | 4,6 m | 4,6 m | ✅ (BYKHY Md. 96/5: LH ve OH1'de standart başlık en çok 21 m²) |
| OH (1–4) | 12 m² | 4,0 m | 4,6 m (S), D daha kısa | ✅ / ⚠️ şaşırtmalı |
| HHP/HHS | 9 m² | 3,7 m | 3,7 m | ✅ |

| Kural | Değer | Durum |
|---|---|---|
| Başlıklar arası en az mesafe | 2,0 m (daha yakınsa ıslanmayı önleyen siper/levha gerekir) | ✅ |
| Duvara en fazla mesafe | Genel kural 2,0 m. Açık kirişli tavan, yanıcı dış duvar veya cam cephede 1,5 m. Pratikte aralığın yarısı (S/2) alınır. | ⚠️ |
| Duvara en az mesafe | EN 12845'te açık bir sınır yok; pratikte 0,10 m (NFPA 4 in = 102 mm) | ⚠️ |
| Deflektörün tavana mesafesi | Genelde 75–150 mm; yanmaz tavanda en fazla 0,30 m, yanıcı tavanda 0,45 m sınırına dikkat | ⚠️ |
| Asma tavan boşluğu | Boşluk > 0,8 m ve yanıcı yük varsa tavan arasına da başlık konur | ⚠️ |
| Engel kuralı | 0,8 m'den geniş kanal veya tava altına ek başlık konur | ⚠️ |

### 2.2 NFPA 13 (standart sprey başlık)

| Sınıf | En fazla alan | En fazla aralık |
|---|---|---|
| LH, düz ve engelsiz tavan | 225 ft² (20,9 m²) | 15 ft (4,6 m) |
| LH, yanmaz ve engelli | 168 ft² (15,6 m²) | 15 ft (4,6 m) |
| LH, yanıcı ve engelli | 130 ft² (12,1 m²) | 15 ft (4,6 m) |
| OH | 130 ft² (12,1 m²) | 15 ft (4,6 m) |
| EH, yoğunluk < 0,25 | 100 ft² (9,3 m²) | 12 ft (3,7 m) |
| EH, yoğunluk ≥ 0,25 | 90 ft² (8,4 m²) | 12 ft (3,7 m) |
| Yüksek istif depolama | 100 ft² (9,3 m²) | 12 ft (3,7 m) |

- Başlıklar arası en az 6 ft (1,8 m).
- Duvara en fazla S/2: LH ve OH için 7,5 ft (2,3 m), EH için 6 ft (1,8 m). Duvara en az 4 in (102 mm).
- LH'de 800 ft² (74 m²) ve daha küçük odada bir duvara 9 ft (2,7 m) mesafeye izin verilir. ✅

---

## 3. Boru çapı seçimi

### 3.1 TS EN 12845: önceden hesaplanmış (pre-calculated) tablolar

**LH** (Tablo 25–29): branşman 20 mm → 1 başlık, 25 mm → 3 başlık. Dağıtım borusu 25 mm ve üzeri. Tasarım noktası 3. veya 4. başlıktadır. Vana istasyonundan tasarım noktasına toplam kayıp en fazla ≈0,7–0,9 bar (Şekil 17). ⚠️

**OH: branşman (Tablo 30)**, bir branşmandaki en fazla başlık sayısı: ✅

| Branşmanın konumu / düzen | 25 mm | 32 mm | 40 mm | 50 mm |
|---|---|---|---|---|
| İki uçtan beslemeli düzende son 2 branşman | 1 | 2 | – | – |
| Üç uçtan beslemeli düzende son 3 branşman | 2 | 3 | – | – |
| Diğer tüm düzenlerde son branşman | 2 | 3 | 4 | 9 |
| Diğer tüm branşmanlar | 3 | 4 | 6 | 9 |

- Eğimi 6°'den fazla çatı altında boyuna giden branşmanda en fazla 6 başlık bulunur. ✅

**OH: dağıtım borusu (Tablo 31)**, tesisat uçlarında beslenen en fazla başlık sayısı:

| Çap | İki uçtan beslemeli düzen | Diğer düzenler | Durum |
|---|---|---|---|
| 25 mm | – | 3 | ✅ |
| 32 mm | 2 | 6 | ✅ |
| 40 mm | 4 | 9 | ⚠️ |
| 50 mm | 8 | 18 | ⚠️ |
| 65 mm | 16 | – | ✅ |

- Tasarım noktası 16'dan fazla başlıkta 17. başlıkta, iki uçtan beslemeli düzende 18'den fazla başlıkta 19. başlıktadır. ✅
- Tasarım noktasından vana istasyonuna kadar olan borular hesapla boyutlandırılır. 1000 l/dk'da (OH) toplam kayıp en fazla 0,5 bar olur. Fazla basınç varsa artırılabilir. Örnek: OH3 → 0,5 + 1,7·(1000/1350)² = 1,43 bar. ✅

**HHP/HHS (Tablo 32–35, K80)**: branşmanda en fazla 4 başlık; branşman 150 mm'den büyük dağıtım borusuna bağlanmaz. ✅ Branşman 25 mm → 3, 32 mm → 4; son branşmanda 40 mm → 4. Tasarım noktası 48'den fazla başlıkta 49. başlıktadır. ✅

**Birim kayıp** (C=120, mbar/m) ✅:

| Çap | 100 l/dk | 225 l/dk |
|---|---|---|
| 25 | 44 | 198 |
| 32 | 12 | 52 |
| 40 | 5,5 | 25 |
| 50 | 1,7 | 7,8 |
| 65 | 0,44 | 2,0 |

### 3.2 Önceden hesaplanmış OH için vana istasyonu basınç/debi gereksinimi (EN 12845 Tablo 6) ⚠️

| Sınıf | Debi 1 (l/dk) @ basınç | Debi 2 (l/dk) @ basınç |
|---|---|---|
| LH (ıslak) | 225 @ 2,2 bar (statik hariç; kontrol et) | – |
| OH1 ıslak | 375 @ 1,0 bar | 540 @ 0,7 bar |
| OH2 ıslak | 725 @ 1,4 bar | 1000 @ 1,2 bar |
| OH3 ıslak | 1100 @ 1,7 bar | 1350 @ 1,4 bar |
| OH4 ıslak | 1300 @ 2,0 bar | 2100 @ 1,5 bar |

Vana istasyonu ile en yüksek başlık arasındaki statik fark bu basınçlara eklenir. Örnek: OH3'te 1,4 + 1,2 = 2,6 bar. ✅

### 3.3 Hız ve basınç sınırları

| Kural | Değer | Durum |
|---|---|---|
| Vana ve akış anahtarında en yüksek hız | 6 m/s | ✅ |
| Diğer noktalarda en yüksek hız | 10 m/s | ✅ |
| Sistem basıncı | En fazla 12 bar | ✅ |
| Hazen-Williams C | Siyah çelik / galvaniz 120, plastik / bakır 150 | ✅ |
| Hazen-Williams formülü | p = 6,05·10⁵·Q^1,85 / (C^1,85·d^4,87) bar/m (Q l/dk, d mm) | ✅ |

### 3.4 NFPA 13 boru çizelgesi (pipe schedule, çelik) ⚠️

Yeni tesislerde yalnızca küçük sistemlerde (≤ 5000 ft²) veya genişlemelerde kullanılır.

| Çap | 1" | 1¼" | 1½" | 2" | 2½" | 3" | 3½" | 4" | 5" | 6" |
|---|---|---|---|---|---|---|---|---|---|---|
| LH, en fazla başlık | 2 | 3 | 5 | 10 | 30 | 60 | 100 | (alan sınırı) | | |
| OH, en fazla başlık | 2 | 3 | 5 | 10 | 20 | 40 | 65 | 100 | 160 | 275 |

### 3.5 ROTAŞ çizim pratiği (README kalıcı kuralı, Aselsan 02-Yangın) ✅

| DN | 25 | 32 | 40 | 50 | 65 | 80 | 100 | 150 |
|---|---|---|---|---|---|---|---|---|
| Başlık sayısı | ≤2 | 3 | ≤5 | ≤10 | ≤20 | ≤40 | ≤100 | >100 |

Bu tablo NFPA OH çizelgesiyle büyük ölçüde örtüşür. Çap etiketi "DN.." olarak yazılır, başlık sayısı etiketin üstüne konur. Çapı yazılmamış boru parçası bırakılmaz. **Kesin projede EN 12845 hidrolik hesabı ile doğrulanmalıdır.**

---

## 4. Alarm vana istasyonu ve zon kontrol vanası

### 4.1 Vana istasyonu başına en büyük alan

| Sınıf | Islak / ön tepkili | Açıklama | Durum |
|---|---|---|---|
| LH | 10.000 m² | | ✅ |
| OH (LH dahil) | 12.000 m² | NFPA kökenli 4831 m²/kat sınırı da anılır | ✅ / ⚠️ |
| HH (LH ve OH dahil) | 9.000 m² | NFPA kökenli 3716 m²/kat sınırı da anılır | ✅ / ⚠️ |
| Kuru sistem | Islağın yaklaşık yarısı; boşalma süresi ≤ 60 s | | ⚠️ |

### 4.2 Islak alarm vana istasyonu bileşenleri (şemada sırasıyla) ⚠️ (endüstri pratiği)

1. İzlenebilir ana kesme vanası (OS&Y sürgülü vana veya izleme anahtarlı kelebek vana)
2. Islak alarm vanası (çek klapeli) ve tutma kabı (retard chamber)
3. Su motorlu alarm gongu hattı (Ø20, filtre ve test vanası ile)
4. Alarm basınç anahtarı (yangın alarm paneline)
5. Biri vana altında, biri vana üstünde olmak üzere iki manometre
6. Ana drenaj vanası (DN50) ve test vanası
7. Vana istasyonu, etiketi ve kilitli "AÇIK" konum etiketi ile pompa dairesinde veya korunmuş mahalde yer alır

### 4.3 Zon (kat) kontrol vanası grubu: BYKHY Md. 96/7 ✅

> "Ana besleme birden fazla yangın zonuna hizmet ediyorsa her zon veya kolon hattına **akış anahtarı**, **test ve drenaj vanası** ve **izleme anahtarlı hat kesme vanası** konulur."

Akış yönünde sıralama:

1. İzleme anahtarlı kelebek vana
2. Akış anahtarı (paddle tipi)
3. Manometre
4. Test-drenaj vanası

Test-drenaj vanası, tek bir başlığın akışına eşdeğer orifise (K80) sahiptir ve gözetleme camı bulunur. Drenaj hattı kuru kolona veya gidere bağlanır. Basınç düşürücü kullanılıyorsa önüne ve arkasına birer manometre konur (Md. 96/10). ✅

---

## 5. Yangın dolapları (TS EN 671 ve BYKHY Md. 94)

### 5.1 Zorunluluk: Md. 94/b-1 ✅

- Yüksek binalar
- Toplam kapalı alanı 1000 m²'den büyük imalathane, atölye, depo, konaklama, sağlık, toplanma ve eğitim binaları
- Toplam alanı 600 m²'den büyük kapalı otoparklar
- Isıl kapasitesi 350 kW'tan büyük kazan daireleri

### 5.2 Tasarım değerleri

| Konu | TS EN 671-1 (yarı sert hortum makaralı) | TS EN 671-2 (yassı hortumlu) | Durum |
|---|---|---|---|
| Kullanıcı | Eğitimsiz kişi | Eğitimli yangın görevlisi | ✅ |
| Hortum | Ø25 mm, en fazla 30 m (TS EN 694) | DN ≤ 50 mm, en fazla 20 m | ✅ |
| Tasarım debisi | 100 l/dk | 400 l/dk | ✅ |
| Tasarım basıncı | 400 kPa (4 bar) | En az 400 kPa | ✅ |
| Basınç düşürücü | Lülede 900 kPa (9 bar) üstünde gerekir | Lülede 900 kPa üstünde gerekir | ✅ |
| Dolaplar arası mesafe | En fazla 30 m. Sprinkler ve katlarda itfaiye su alma ağzı varsa 45 m; bu durumda ıslak sprinkler branşmanından beslenebilir. | Aynı | ✅ |
| Besleme hattı | En az DN50 kolon; dolap bağlantısı DN25–DN32 | | ⚠️ |
| Montaj yüksekliği | Vana / makara ekseni zeminden ≈1,2–1,5 m | | ⚠️ |
| Bakım | TS EN 671-3, bina sahibi veya yöneticisi yaptırır | | ✅ |

### 5.3 Yerleşim kuralları (çizim pratiği) ⚠️

- **30 m kuralı:** Hortum uzunluğu 30 m'ye lüle menzili (≈3–5 m) eklenir. Mahal içindeki her nokta, dolaptan **duvar ve kapı etrafından gerçek yürüme yolu** üzerinden ölçüldüğünde hortum boyu içinde kalmalıdır. Pratikte planda dolap merkezli **R=30 m** daire veya yol çizgisi ile kontrol edilir.
- Dolaplar kaçış yolu üzerinde, merdiven ve yangın kapısı yakınında, kat girişlerinde, korunmuş holde konur. Kapı açılışını ve kaçış genişliğini engellememelidir.
- Her yangın kompartımanında ayrı değerlendirme yapılır. Yangın duvarı hortumla geçilmez.
- Sıva altı veya sıva üstü dolap; gövde ≈ 65×70×22 cm (makaralı); yangın tüpü dolap içinde veya yanında olabilir.
- Su ihtiyacı (Md. 92/6): yalnızca dolap varsa hacim = dolap debisi × aynı anda çalışan dolap × süre. Yüksek tehlike yoksa dolaplar kullanım suyuna bağlanabilir. ✅ Aynı anda çalışan dolap sayısı Ek-8/C'den alınır; pratikte LH/OH için 2 dolap. ⚠️

---

## 6. İtfaiye su alma ağzı ve itfaiye su verme bağlantısı

### 6.1 Su alma (kat) ağzı: Md. 94/a ✅

- Yüksek binalarda ve kat alanı 1000 m²'den büyük AVM, otopark vb. yerlerde ıslak veya kuru sabit boru (kolon) üzerinde, **korunmuş mahalde** (yangın merdiveni yuvası veya yangın güvenlik holü) bulunur.
- Bir boyutu 60 m'yi aşan katlarda dolap ve su alma ağzı yapılır. Herhangi bir noktadan ağza en fazla **60 m**.
- Storz tip DN50 veya DN65 rakor kullanılır. Sprinkler ve dolap kolonundan alınacaksa **ana kolondan doğrudan** bağlanır.

### 6.2 İtfaiye su verme bağlantısı (Siamese / "Y" bağlantı): Md. 97 ✅

| Kural | Değer |
|---|---|
| Ne zaman | Yüksek bina, oturma alanı > 1000 m² olan bina veya cephe genişliği > 75 m olan bina |
| Boru çapı | Sulu söndürme sistemine en az **DN100** |
| Rakor | **2 × 65 mm storz** + çek valf + otomatik boşaltma (çek valf ile ağız arasındaki boruda donma önlemi) |
| Araç mesafesi | İtfaiye aracının bağlantıya ulaşma mesafesi en fazla **18 m** |
| Bağlantı noktası | Pompa çıkışından sonra, çek valften sonraki ana kollektöre (sprinkler ve dolap ana besleme hattına) bağlanır |
| Cephe uygulaması ⚠️ | Zeminden ≈0,6–1,0 m yükseklikte, "İTFAİYE BAĞLANTISI – SPRİNKLER/DOLAP" etiketli, kolay görülen cephe nişinde |

---

## 7. Hidrant (Md. 95) ✅

| Kural | Değer |
|---|---|
| Tasarım debisi | En az 1900 l/dk (tehlikeye göre artar) |
| Çıkış basıncı | 700 kPa (7 bar) |
| Hidrantlar arası mesafe | Çok riskli 50 m · riskli 100 m · orta 125 m · az riskli 150 m |
| Binaya mesafe | Ortalama 5–15 m |
| Hat | Ring yoksa en az DN100, hidrolik hesap ile; uygun noktalarda hat kesme vanası; TS'ye uygun yer üstü hidrant |
| Zorunluluk | Ayrı planlanan yerleşimde taban alanları toplamı > 5000 m² olan binalar (ve ilgili kullanım maddeleri) |
| Yalnız hidrant varsa su | 1900 l/dk × 90 dk ≈ **171 m³** (Md. 92/7) |

---

## 8. Sprinkler zorunluluğu: BYKHY Md. 96/2 ✅

| Bent | Koşul |
|---|---|
| a | Yapı yüksekliği **> 30,50 m** olan konut dışı binalar |
| b | Yapı yüksekliği **> 51,50 m** olan konutlar |
| c | Toplam alanı **> 600 m²** olan kapalı otoparklar; asansörle **10'dan fazla** araç alınan otoparklar |
| ç | Oda > 100 veya yatak > 200 olan otel, yurt, pansiyon, misafirhane; yapı yüksekliği **> 21,50 m** olan tüm yataklı tesisler |
| d | Toplam alanı **> 2000 m²** olan katlı mağaza, AVM, ticaret ve eğlence yerleri |
| e | Toplam alanı **> 1000 m²** olan, kolay alevlenen veya parlayıcı madde üreten ya da depolayan yapılar |

Not: Eski sürümlerde ve bazı ikincil kaynaklarda otopark eşiği "20'den fazla araç / birden fazla bodrum" olarak geçer. **Güncel metin 600 m²**'dir; Resmî Gazete'den teyit edilmelidir. ⚠️

- Sprinkler konmayabilecek yerler (yangın yüküne göre): yanıcı malzeme bulunmayan ıslak hacimler, korunmuş merdiven yuvaları, asansör kuyuları, gazlı veya tozlu sistemle korunan mahaller. ✅
- Sprinkler konmayacak yerler: su ile genleşen madde siloları, fırın ve tuz banyosu çevresi, suyun tehlike yarattığı mahaller. ✅
- Deprem bölgesinde: dört yollu destek, ≥ DN65 borularda esnek bağlantı ve iki yollu sabitleme (Md. 96/6). ✅
- Tasarım TS EN 12845'e göre yapılır (Md. 96/5). Elemanlar TS EN 12259 uyumlu olmalıdır. ✅

---

## 9. Yangın pompa grubu

### 9.1 BYKHY Md. 93 ✅

| Kural | Değer |
|---|---|
| Kapalı vana (churn) basıncı | Anma basma yüksekliğinin en fazla %140'ı |
| %150 debideki basınç | Anma basıncının en az %65'i |
| Kullanım | Anma debisinin %130'una kadar |
| Yedek | Tek pompa varsa aynı kapasitede yedek. Çok pompada toplam kapasitenin en az %50'si yedek olur. |
| Enerji | Dizel yedek yoksa elektrik beslemesi güvenilir ve genel sistemden bağımsız olmalıdır |
| Armatür | Otomatik hava atma ve sirkülasyon rahatlama vanası; her pompaya ayrı kilitlenebilir pano (faz hatası, faz sırası, kumanda fazı ışıkları) ve ayrı basınç anahtarı |
| Pompa dairesi sıcaklığı | Elektrikli için > +4 °C, dizel için > +10 °C |

EN 12845 tarafında: pompa karakteristiği %140 debide anma basıncının en az %70'i olmalıdır (ROTAŞ hesap kütüphanesi). Projede iki koşulun daha sıkı olanı sağlanır. ⚠️

### 9.2 Pompa grubu bileşimi ve uygulama pratiği ⚠️

| Pompa | Görev | Tipik ayar (örnek, asıl pompa 8 bar) |
|---|---|---|
| Jokey | Kaçakları karşılar, basıncı tutar. Debisi ≈ 1 başlık veya asıl pompanın %1–5'i; basıncı asıl pompadan ≈ 0,5–1 bar yüksek. | Devreye girer 8,5 bar, durur 9,5 bar |
| Asıl elektrikli | %100 kapasite. Otomatik devreye girer, **elle durdurulur** (otomatik durmaz). | Devreye girer 8,0 bar |
| Dizel yedek | %100 kapasite. Elektrik kesintisinde veya asıl pompa arızasında devreye girer; yakıt tankı ≈ 8 saat (EN 12845: 3 saat + rezerv). | Devreye girer 7,5 bar |

- **Emiş:** Pozitif emiş tercih edilir (depo tabanı pompa ekseninden yüksek). Her pompanın emişi ayrıdır. Emişte eksantrik redüksiyon kullanılır (düz üst yüzey); emiş hızı ≤ 1,8 m/s; emişte vorteks önleyici bulunur. EN 12845 emiş tarafında pozitif emiş ister, aksi halde ayrı hazırlık (priming) tankı gerekir.
- **Basma:** Esnek bağlantı → çek valf → izlenebilir kesme vanası → kollektör.
- **Kollektör:** Manometre, basınç anahtarları ve **akış ölçerli test hattı** (depoya geri dönüş, %150 debi testi). Dizel pompa çıkışında emniyet vanası çek valften önce yer alır.
- Dizel egzozu dışarı atılır; yanma havası menfezi ve yakıt tankı drenaj havuzu (tava) bulunur.

---

## 10. Yangın suyu deposu hacmi

### 10.1 Yöntem: BYKHY Md. 92 ✅

**V = (Q_sprinkler + Q_dolap + Q_hidrant) × t**

- Q_sprinkler = yoğunluk × işletme alanı. Hidrolik hesapta gerçek debi alınır (en uzak alandaki toplam başlık debisi, dengesizlik dahil).
- t: LH 30 dk · OH 60 dk · HH 90 dk.
- Ön hesap için BYKHY Ek-8/A (bina yüksekliği ve tehlike sınıfına göre m³), Ek-8/B (sprinkler debisi) ve Ek-8/C (dolap debisi) tabloları kullanılır. **Hidrolik hesap varsa o değer esastır.**
- Yangın rezervi başka amaçla kullanılamaz. Ortak depoda kullanım suyu emişi yangın rezervi seviyesinin üstünden alınır (Md. 92/2).
- Doldurma süresi en fazla 36 saat (EN 12845; ROTAŞ hesap kütüphanesi). ⚠️

### 10.2 Ek su payı (ROTAŞ hesap kütüphanesindeki pratik değerler)

| Sınıf | Dolap + hidrant (l/dk) | Süre |
|---|---|---|
| LH | 100 + 400 | 30 dk |
| OH 1–2 | 100 + 400 | 60 dk |
| OH 3–4 | 100 + 1000 | 60 dk |
| HH | 200 + 1500 | 90 dk |

### 10.3 Örnekler

**Kapalı otopark, OH2** (✅ İtalyan ders notu örneği):
- Sprinkler: 5 mm/dk × 144 m² = 720 l/dk. 144/12 = 12 başlık, başlık başına 60 l/dk ve 0,56 bar.
- Kayıplarla düzeltilmiş toplam ≈ 800 l/dk.
- 800 × 60 = **48 m³** (yalnız sprinkler).
- Dolap eklenirse 2 × 100 l/dk × 60 dk = 12 m³ → **≈ 60 m³**.

**EN 12845 ön hesaplı depo tablosu (Tablo 9, ıslak)** ⚠️ değerleri doğrula:

| En yüksek başlığın yüksekliği | LH | OH1 | OH2 | OH3 | OH4 |
|---|---|---|---|---|---|
| ≤ 15 m | 9 m³ | 55 m³ | 105 m³ | 135 m³ | 160 m³ |
| 15–30 m | 10 m³ | 70 m³ | 125 m³ | 160 m³ | 185 m³ |
| 30–45 m | 11 m³ | 80 m³ | 140 m³ | 185 m³ | 200 m³ |

---

## 11. Hidrolik en uzak alan (en elverişsiz alan) işaretleme

- **Alanın seçimi:** Hidrolik olarak en uzak (en yüksek ve en uzak) noktada, işletme alanı kadar (ör. OH2 için 144 m²) **dikdörtgen** alınır. Uzun kenar branşmanlara paralel ve ≥ 1,2·√A olur (144 m² için ≥ 14,4 m). ⚠️
- **Planda gösterim:**
  - Kalın kesikli veya noktalı sınır çizgisi, çoğu zaman taralı (ANSI31 veya hafif dolgu) olarak çizilir.
  - Etiket örneği: "HİDROLİK EN UZAK ALAN – OH2 – 144 m² – 5 mm/dk – 12 ad. K80".
  - Alan içindeki başlıklar numaralanır (S1…S12). Düğüm noktaları (N1, N2…) hesap tablosuyla eşleşir.
- **Hesap tablosu** (Excel ve pafta): düğüm · başlık K · P (bar) · q (l/dk) · Q toplam · DN · L · eşdeğer L · birim kayıp · Δp · kot farkı.
- Vana istasyonunda ve pompa çıkışında gerekli P–Q değeri verilir. Pompa seçimi için hidrolik eğri ile pompa eğrisi karşılaştırılır.

---

## 12. Türk projelerinde çizim pratiği

### 12.1 Pafta düzeni (ROTAŞ / MTY ticari set, Teknopark örneği)

- Pafta kodu **03-MT-YT: Yangın**. Başlık: "YANGIN TESİSATI KAT PLANLARI VE KOLON ŞEMASI".
- Kat planları 1/100 ölçekte, bodrumdan çatıya kadar çizilir. Pafta lejant, "Notlar :" bölümü ve şemaları içerir.
- Sistem şemasında (09-MT-P&ID) yangın şeması ve pompa grubu yer alır.
- Depolar ayrı ayrı yazılır (ör. "YANGIN DEPOSU 165 m³").
- Hesap raporunda "Yangın: depo ve pompa basıncı" bölümü bulunur.
- ROTAŞ'ta yangın işleri **VOYAP yangın** onaylı setinin tarzında yapılır (README GENEL kuralı).

### 12.2 Kat planı

| Öğe | Pratik |
|---|---|
| Sprinkler sembolü | Dolu daire: sarkık (pendent). Daire + üst çizgi veya boş daire: dik (upright). Yarım daire veya ok: yan duvar (sidewall). Kuru sarkık için ayrı sembol (TS 2164 / MTY blokları). Tümü **gerçek blok** olarak çizilir; ROTAŞ kuralı gereği temsili kutu veya daire kullanılmaz. |
| Başlık yerleşimi | Mahal içinde grid düzeni: duvara S/2, başlıklar arası ≤ S. Kiriş ve kanal engellerine göre ek başlık konur. Asma tavan varsa armatür ve difüzörlerle koordine edilir. |
| Boru | Kırmızı katman (ör. `SCOTT-YANGIN-SPRINKLER`, `SCOTT-YANGIN-DOLAP`). Ana hat kalın, branşman ince çizilir. Kesişmelerde köprü; yazı altında wipeout. |
| Çap etiketi | Her boru parçasında **"DN32"** ve üstünde başlık sayısı (ör. "3"). Çapı yazılmamış boru kalmaz (README). |
| Kolon | Kolon kodu (YK-1, SK-1…) ile işaretlenir. Kolon **duvar köşesinden** çıkar, mahal ortasından çıkmaz. Mahal beslemesi mümkünse **kapıdan** girer. |
| Zon vanası | Her kat kolon çıkışında MTY blokuyla; V-xx numarası; akış anahtarı ve test-drenaj gösterilir. |
| Dolap | Dikdörtgen sembol + "YD" yazısı (TS EN 671-1). İsteğe bağlı R=30 m kontrol eğrisi ayrı katmanda tutulur ve teslimde dondurulur. |
| İtfaiye ağzı | Cephede "İB" sembolü (2×65 storz). Kat su alma ağzı merdiven yuvasında gösterilir. |
| Hidrant | Saha planında, bina dışında 5–15 m mesafede; hidrant sembolü + DN100 ring hattı. |
| Hidrolik alan | §11'deki gibi taralı ve etiketli. |
| Özel kurallar | Lift ara seviyelerine sprinkler konmaz. Borular ve semboller betonarme kolon veya perdeyi kesmez (`kolon_kontrol.py`). |

### 12.3 Yangın kolon şeması (açılımlı / izometrik)

- **Açılımlı (düşey) şema** yaygındır:
  - Kat çizgileri ve kotlar (±0,00, +3,20 …) yatay çizgilerle gösterilir.
  - Kolonlar düşey çizilir; her katta zon vanası grubu, dolap çıkışları ve itfaiye su alma ağzı yer alır.
  - Kolon tepesinde otomatik hava tahliyesi, kolon dibinde drenaj bulunur.
  - Kolon çapı her kat arası parçada yazılır.
- Şemanın altında pompa dairesi bağlantısı, alarm vana istasyonu, itfaiye su verme bağlantısı ve depo yer alır.
- Büyük projelerde izometrik kat dağıtımı ayrıca verilir (MTY "otomatik çap" modülü).

### 12.4 Pompa dairesi kesit ve görünüşü

- ROTAŞ kalıcı kuralı: **pompa grubu şemada kesit (görünüş) olarak çizilir.**
- İçerik:
  - Depo kesiti: max/min su seviyesi, emiş ağızları, taşma ve dip boşaltma, şamandıralı dolum, seviye göstergesi, menhol
  - Asıl, yedek ve jokey pompalar (kaide ve titreşim takozları ile)
  - Emiş hatları: eksantrik redüksiyon, kesme vanası, esnek bağlantı
  - Basma hattı: esnek bağlantı, çek valf, kesme vanası, kollektör
  - Kollektör: test hattı (debimetreli), basınç anahtarları, manometreler, emniyet vanası
  - Alarm vana istasyonu, itfaiye bağlantısı, dizel egzoz ve yakıt tankı
- Ekipmanlar numaralanır (P-01 … V-01 …) ve ekipman listesiyle eşleşir.

### 12.5 Lejant (tipik içerik)

Sprinkler (sarkık, dik, yan duvar), yangın dolabı, itfaiye su verme bağlantısı, kat su alma ağzı, hidrant, alarm vana istasyonu, zon vanası grubu, akış anahtarı, izlenebilir kelebek vana, sürgülü vana, çek valf, test-drenaj vanası, manometre, basınç düşürücü, otomatik hava atma, esnek bağlantı, pompa, yangın boruları (sprinkler, dolap, ana hat), kolon numarası, çap etiketi biçimi.

### 12.6 Standart notlar (örnek, "Notlar :" bölümü) ⚠️ Projeye göre uyarlanır

1. Yangın tesisatı BYKHY ve TS EN 12845 / TS EN 671 / TS EN 12259'a göre projelendirilmiştir. Tehlike sınıfı: OH… Tasarım yoğunluğu: … mm/dk. İşletme alanı: … m².
2. Borular TS EN 10255 orta seri siyah çelik (dişli ≤ DN50; kaynaklı veya yivli ≥ DN65); boyaları kırmızıdır (RAL 3000).
3. Sprinkler başlıkları K80, 68 °C (kırmızı ampul), standart tepkilidir. Mutfak ve kazan dairesinde 93 °C kullanılır.
4. Askılar EN 12845 / NFPA 13'e uygundur; deprem bölgesinde 4 yollu destek ve ≥ DN65'te esnek bağlantı vardır.
5. Tesisat 15 bar (veya çalışma basıncı + 3,5 bar) ile 2 saat hidrostatik teste tabi tutulur.
6. Her kat zon vanası grubu (izlenebilir vana + akış anahtarı + test-drenaj) yangın alarm paneline bağlanır.
7. Yangın dolapları TS EN 671-1, 25 mm × 30 m hortumludur. Lülede 9 bar üstünde basınç düşürücü kullanılır.
8. İtfaiye su verme bağlantısı 2×65 mm storz, DN100, çek valfli ve otomatik drenajlıdır.
9. Yangın deposu … m³ (… dk), pompa grubu: asıl elektrikli … m³/h @ … bar + dizel yedek + jokey.
10. Uygulama öncesi mimari, statik ve elektrik projeleriyle koordinasyon yapılır. Kot ve ölçüler yerinde kontrol edilir.

---

## 13. Kaynaklar

- TS EN 12845 tablolarının ders notu (İtalyan UNI EN 12845 sunumu; yoğunluk/alan, K, minimum basınç, OH2 örneği): https://nuoro.ordingegneri.it/wp-content/uploads/sites/45/2021/04/04-S6-Impianti%20estinzione%20INGCE-2017%20Parte%20II.pdf
- EN 12845 çevirisi (DSTU; boru tabloları 30–35, tasarım noktaları, birim kayıplar): https://dnaop.com/html/67337_3.html · https://dnaop.com/html/67337_2.html
- Yangın Sempozyumu 2019, "Sulu Sistem Yağmurlama Sistemlerinin Tasarımı ve Tesisi" (tehlike tablosu, alan/aralık, alarm vanası alanı, zon vanası, pompa): https://yanginsempozyumu.org/wp-content/uploads/2019/10/2019-007.pdf
- BYKHY 2015 tesisat maddeleri (Md. 92–97): https://www.tesisat.org/binalarin-yangindan-korunmasi-hakkinda-yonetmelik-2015.html
- Sprinkler ile korunacak mahaller: https://www.tesisat.org/sprinkler-sistemi-ile-korunacak-mahaller.html
- BYKHY resmî metin (doğrulama için; araç erişimi engelli): https://www.mevzuat.gov.tr/MevzuatMetin/21.5.200712937.pdf · https://www.resmigazete.gov.tr/eskiler/2007/12/20071219-2.htm
- BYKHY Md. 96 özet: https://aspek.com.tr/yangin-sondurme-sistemleri/sprinkler-nerelerde-zorunlu
- EMO yangın algılama sunumu (Md. 94, 95, 97 atıfları): https://www.emo.org.tr/ekler/08670e12c6e0fcf_ek.pdf
- NFPA 13 alan ve aralık özeti: https://open-exam-prep.com/study-guides/nicet-water-based/sprinkler-selection-spacing/protection-area-spacing-rules
- NFPA 13 yoğunluk/alan ve hortum payı: https://www.toolgrit.com/guides/sprinkler-hydraulic-explained
- MeyerFire sprinkler aralık özeti: https://www.meyerfire.com/uploads/1/6/0/7/16072416/meyerfire_-_sprinkler_-_spacing__2022_.pdf
- ROTAŞ iç kaynakları: README "Kalıcı kurallar" (yangın, pompa kesiti, Aselsan çap tablosu), `rotas-mekanik-proje-standardi` (03-MT-YT pafta düzeni), `tesisat-hesap-kutuphanesi` §8 (ek su, pompa, depo).

---

## 14. Hızlı kontrol listesi (çizim motoru için)

1. Tehlike sınıfı → yoğunluk, alan, süre ve başlık başına en fazla alan/aralık seçilir.
2. Başlıklar grid düzeninde yerleştirilir. Kontroller: duvar ≤ S/2 (en fazla 2,0 m), başlıklar arası ≥ 2 m, kolon/perde çakışması yok.
3. Boru ağı kurulur: kolon köşeden, besleme kapıdan. Her parçaya DN ve başlık sayısı (ROTAŞ tablosu) yazılır.
4. Her katta zon vanası grubu; uygun yerlerde dolap (≤ 30/45 m) ve su alma ağzı (≤ 60 m) konur.
5. Hidrolik en uzak alan işaretlenir. Hesap: P_uç ≥ 0,35 bar (OH), hız ≤ 6/10 m/s.
6. Depo hacmi V = ΣQ × t; pompa asıl + dizel + jokey; itfaiye bağlantısı 2×65 / DN100.
7. Kolon şeması (açılımlı), pompa dairesi **kesit**, lejant ve notlar hazırlanır. Katmanlar `SCOTT-` önekli olur. Teslim: DWG + DXF + PDF + Excel.
