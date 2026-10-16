# market_hav — kullanıcının havalandırma çizimini temiz mimariye oturtma + paftalama + detaylar (16.10.2026)

Kullanıcı isteği: "temiz mimari ve havalandırma gönderdim, bunu temiz mimariye göre ayarla, paftalandır, havalandırma detaylarını ekle".
Kanal tasarımı (güzergâh, ölçü, debi, santral) **kullanıcınındır, değiştirilmez**; yalnız yeni mimariye uydurulur.

## Akış
1. `ayikla.py HAV.dxf TEMIZ.dxf girdi/hav_kanal.dxf` — eski mimarili havalandırma DXF'inden kanalları ayıklar.
   - Öteleme S-CONC kolon eşleşmesinden bulunur (bu projede temiz = hav + (47244, 54361), 82/88 kolon birebir).
   - Kanallar A-ANNO-TEXT katmanında + 4 blokta (tazehava/dönüşhava/manavüfleme/manavemiş; adlar NFD Türkçe → `unicodedata.normalize`).
   - Sınıflama: blok adı → üfleme/dönüş; gevşek çizilmiş 1.–2. sistem 3. sistem bloğuyla bbox eşleşmesi; kalanı geometri komşuluğu.
   - 2. sistemde 30 cm kaydırılmış kopya çizgi (`ikiz_duzelt`).
2. `hav_pafta.py` — temiz mimari üstüne yerleştirir, kontrol eder, paftalar:
   - Katmanlar: MTY-UFLEME-KANALI 20 / MTY-UFLEME-CAP 21, MTY-DONUS-KANALI 4 / MTY-DONUS-CAP 110, MTY-CIHAZ 135, kesişmede alttaki branşman `…-GIZLI` (DASHED).
   - Mimari katmanlar gri (8); kolon katmanları (S-CONC/S-HTCH/S-STEL) olduğu gibi kalır.
   - Yeni kolon aksına çarpan sistem bütün olarak en küçük ötelemeyle kaydırılır (3. sistem +190 x, 4. sistem −20 y).
   - Kontroller (hepsi 0): kanal–kolon, yazı–yazı/kanal/kolon/duvar/mimari etiket, boşta kanca ucu, aynı sistem kesişmesi, pafta dışı varlık.
   - Paftalar (1/100 şerit, y −600…9300): ANTET ×2 | VAZİYET 1/200 | ZEMİN KAT HAVALANDIRMA PLANI 1/100 (+ lejant, cihaz listesi,
     kanal hız kontrol tablosu) | 1. KAT PLANI 1/100 | HAVALANDIRMA TESİSATI DETAYLARI (10 detay + notlar, hepsi çerçeveli).
3. `detaylar.py` — kanal askı, flanş, kenet/pim, duvar geçişi, döşeme/çatı geçişi, menfez montajı, hacim ayar damperi,
   dış hava panjuru, santral esnek bağlantı, sac kalınlık tablosu (TS EN 1505/1507). Saf geometri, başka projelerde de kullanılır.

Denetim: `python3 motor/deneme/denetim/denetle.py proje/market_havalandirma/MARKET_HAVALANDIRMA_PROJESI.dxf --rapor-yok --ayrinti`
(kesişme 0, yazı 0, audit 0; MTY/önek uyarıları havalandırma MTY katmanları ve kullanıcının mimari katmanları — beklenen).
