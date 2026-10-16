# Market havalandırma — temiz mimariye oturtma + paftalama (16.10.2026)
İstek: "temiz mimari ve havalandırma gönderdim, bunu temiz mimariye göre ayarla, paftalandır, havalandırma detaylarını ekle".
Girdi: havalanıdırma.dxf (eski mimari + kanallar, A-ANNO-TEXT katmanında + 4 blok), temiz_mimari.dxf.
- Öteleme bulundu: temiz = hav + (47244, 54361) (S-CONC kolonları 82/88 birebir).
- Kanal ayıklama: motor/market_hav/ayikla.py → girdi/hav_kanal.dxf (üfleme/dönüş/cihaz/yazı sınıflı).
- Pafta: motor/market_hav/hav_pafta.py → MARKET_HAVALANDIRMA_PROJESI.dxf.
- 16.10.2026 17:50 — teslim: MARKET_HAVALANDIRMA_PROJESI.dxf (5 pafta). Kontroller 0. 3. sistem +190 x, 4. sistem −20 y
  (temiz mimaride kolon aksı değişmiş). 2. sistemdeki kopya çizgiler ve 4. sistemdeki taşan uçlar temizlendi.
  1. kat planı mimari olarak paftada (kullanıcı çiziminde 1. katta havalandırma yok).
