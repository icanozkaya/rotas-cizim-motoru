# Market havalandırma — temiz mimariye oturtma + paftalama (16.10.2026)
İstek: "temiz mimari ve havalandırma gönderdim, bunu temiz mimariye göre ayarla, paftalandır, havalandırma detaylarını ekle".
Girdi: havalanıdırma.dxf (eski mimari + kanallar, A-ANNO-TEXT katmanında + 4 blok), temiz_mimari.dxf.
- Öteleme bulundu: temiz = hav + (47244, 54361) (S-CONC kolonları 82/88 birebir).
- Kanal ayıklama: motor/market_hav/ayikla.py → girdi/hav_kanal.dxf (üfleme/dönüş/cihaz/yazı sınıflı).
- Pafta: motor/market_hav/hav_pafta.py → MARKET_HAVALANDIRMA_PROJESI.dxf.
- 16.10.2026 17:50 — teslim: MARKET_HAVALANDIRMA_PROJESI.dxf (5 pafta). Kontroller 0. 3. sistem +190 x, 4. sistem −20 y
  (temiz mimaride kolon aksı değişmiş). 2. sistemdeki kopya çizgiler ve 4. sistemdeki taşan uçlar temizlendi.
  1. kat planı mimari olarak paftada (kullanıcı çiziminde 1. katta havalandırma yok).

## 2. aşama (16.10.2026 18:05) — ısıtma-soğutma: ısı geri kazanımlı KS + DX bataryalar
İstek: "bu aslında ısıtma soğutma projesi; ısı geri kazanımlı klima santrali ısıtma ve soğutma bataryalarını (DX) hesapla;
kesitleri gönderdim; tüm cihazların kesitlerini ve yerleşimlerini gönder; m³ hesabına göre ısı kazancı çıkart".
Girdi: KES_TLER.dxf (AA, BB kesit + 4 cephe). Kotlar: ±0.00, tavan/makas altı +6.00, parapet +9.00, 1. kat/teras +4.50.
Plan: (1) Excel hesap  (2) KS kesit + yerleşim paftaları DXF  (3) kontrol + teslim.
- 16.10.2026 18:45 — 2. aşama teslim: MARKET_ISITMA_SOGUTMA_HAVALANDIRMA_PROJESI.dxf (7 pafta: + KLİMA SANTRALİ VE DIŞ ÜNİTE
  KESİTLERİ, KESİTLER — CİHAZ VE KANAL YERLEŞİMİ) ve ISI_KAZANCI_VE_KLIMA_SANTRALI_HESABI.xlsx.
  Akış: zonlar.py → hesap_excel.py → recalc.py → hav_pafta.py. Sonuç: oda ısı kazancı 673 kW (m³ yöntemi),
  DX soğutma 300/280/280/300 kW, DX ısıtma 135/135/135/140 kW; projedeki "Q=200 kW" soğutmaya yetmiyor (×1,4–1,5).
- 16.10.2026 19:20 — 3. aşama: fan hesabı (FAN HESABI sayfası: iç kayıplar + dış statik basınç, EC plug fan duvarı 4+4,
  üfleme 940 Pa / 4×5,5 kW, dönüş 620 Pa / 4×4,0 kW, SFP4/SFP3), elektrik yükü tablosu yalnız elektrik güçleri
  (ısıl kapasiteler çıkarıldı; ısıl değerler her yerde "kW ISIL"). Toplam kurulu elektrik 540,2 kW.
