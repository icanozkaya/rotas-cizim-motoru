# Sığınak havalandırma hesabı (kullanıcı kuralı)
- Alan: NET alan esas alınır (kullanıcı tercihi). Net yükseklik 3,00 m (şablon).
- Taze hava = net alan × yükseklik × 4 defa/saat → 100'e yukarı yuvarlanır (seçilen).
- Egzoz = seçilen taze havanın %10 eksiği.
- Net alan > 100 m² ise duman tahliye (10 defa/saat, 500'e yuvarla) eklenir; değilse taze hava + egzoz yeterli.
- Perde geçiş (duvar açıklığı) ölçüsü: v = 2,5 m/s ile standart dikdörtgen (30×20 … 80×50).
- Çıktı: her sığınak ayrı çerçevede cihaz listesi + yönetmelik tablosu + genel havalandırma tablosu; katmanlar ROTAS-HESAP-*.
- Çizim standardı (15.10.2026): `motor/ab2750/siginak_hav.py` + `proje/STANDART/STANDART_SIGINAK_HAVALANDIRMA_ab2750.dxf` — tüm dış hava bağlantıları yan yana ortak bölmeli kuranglezden; pantolonlarda ayırıcı bölme, dirseklerde yönlendirici kanat.
