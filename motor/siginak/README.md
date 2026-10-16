# Sığınak havalandırma hesabı (kullanıcı kuralı)
- Alan: NET alan esas alınır (kullanıcı tercihi). Net yükseklik 3,00 m (şablon).
- **(16.10.2026 19:11 kullanıcı — GEÇERLİ KURAL) Taze hava KİŞİ SAYISINA göre:** kişi = brüt alan / 1 m²;
  kişi başı ≤50 kişi 1,8 · 51–150 kişi 3,0 · >150 kişi 4,5 m³/h·kişi; taze = kişi × kişi başı → 100'e yukarı.
  Egzoz ona orantılı: taze × 0,90. Hesap: `motor/siginak/debi.py` → `siginak_debileri(brut_alan, h)`.
  Bu kural bundan sonraki projelerde uygulanır; önceki teslimler (new_block, AB2750) değiştirilmedi.
- ~~Taze hava = net alan × yükseklik × 4 defa/saat~~ (eski kural, 16.10.2026 19:11 öncesi projeler).
- Egzoz = seçilen taze havanın %10 eksiği.
- Net alan > 100 m² ise duman tahliye (10 defa/saat, 500'e yuvarla) eklenir; değilse taze hava + egzoz yeterli.
- Perde geçiş (duvar açıklığı) ölçüsü: v = 2,5 m/s ile standart dikdörtgen (30×20 … 80×50).
- Çıktı: her sığınak ayrı çerçevede cihaz listesi + yönetmelik tablosu + genel havalandırma tablosu; katmanlar ROTAS-HESAP-*.
- Çizim standardı (15.10.2026): `motor/ab2750/siginak_hav.py` + `proje/STANDART/STANDART_SIGINAK_HAVALANDIRMA_ab2750.dxf` — tüm dış hava bağlantıları perdede yan yana geçiş (kuranglez mimaride yoksa çizilmez); WC'lere egzoz anemostadı; pantolonlarda ayırıcı bölme, dirseklerde yönlendirici kanat.
- (16.10.2026 kullanıcı) Kanal hız seçimi: çok düşük kalma, 8 m/s'yi geçme, 8 m/s'ye yakın tut (kanallar küçük kalsın) — motorlarda vmax = 8,0.
- (16.10.2026 kullanıcı) Çizilen tüm detaylar (şema, kesit, özel parça detayları, lejant, notlar, tablolar, plan) kare/çerçeve içine alınır.
- (16.10.2026 kullanıcı) "Brüt al" denirse projede yazan brüt alan (ör. 428,84 m²) doğrudan esas alınır; tablolarda net alan satırı gösterilmez.
- (16.10.2026 kullanıcı) Çıkış delikleri (perde/döşeme geçişleri) küçültülebildiği kadar küçük: v ≤ 8 m/s sınırına en yakın, 10 cm adımlı en küçük kesit (2,5 m/s kuralı kaldırıldı).
- (16.10.2026 kullanıcı) SHC, fanlar ve klapeler TAVANA ASILI tasarlanır, yere konmaz (şemada askılı gösterilir; SHC el kolu zincir/uzatma mili ile).
