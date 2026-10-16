# SI_INAK.dwg — Sığınak havalandırma (16.10.2026)
İstek: "BURAYA SIĞINAK HAVALANDIRMA YAP TAZE HAVA KİŞİ BAŞI EGZOZ DA %10 ALTINA DUMAN TAHLİYE DE 10 HAVA DEĞİŞİMLİ ŞEKİLDE YÜKSEKLIK TE 6MT OLARAK YAP"
- Sığınak A-Z-16 brüt 618,2 m², h = 6,00 m (kullanıcı) → 619 kişi × 4,5 = 2.785,5 → taze 2.800; egzoz 2.520; duman 618,2×6×10 = 37.092 → 37.500 m³/h
- Çıkış: kullanıcının MTY-BORU dikdörtgeni (batı cephe duvarı, y −694792…−695291) — "duvardan atış", yatay perde/duvar geçişleri yan yana
- Sığınak içinde WC yok (WC'ler güney dışında) → anemostad yok
- Motor: motor/siginak/si_siginak.py (nb_siginak.py'den uyarlandı), mimari: si_mimari.py
## Durum
- [x] DWG → DXF, mahal/kolon tespiti
- [x] motor uyarlama (si_siginak.py), plan, şema (h 6,00), çıkış duvarı A-A görünüşü, özel parça detayları, tablolar
- [x] kontroller: kolon/duvar kesişimi 0, çizgi binmesi 0, yazı binmesi 0, boşta uç 0, ağlar arası kesişme 0, audit 0, maks hız 7,78/7,78/7,89 m/s
- Sonuç: taze 2.800 (14 menfez, SHC-1 350 Pa) / egzoz 2.520 (12 menfez, EF-1 400 Pa) / duman 37.500 (12 menfez, DTF-1 200 Pa, F400)
- Duvar geçişleri: DUMAN 190x70, TAZE 50x20, EGZOZ 30x30 cm (v ≤ 8 m/s)
