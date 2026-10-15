# VOYAP ASEM bodrum — sığınak havalandırma + otopark taze hava / duman tahliye (15.10.2026)
- Girdi: kullanıcının BODRUM GÜNCEL DWG'si → dwg2dxf (yamalı LibreDWG, /home/claude/libredwg) → `flat.py bodrum.dxf bodrum.pkl`
- Üretim: `python3 -I tasarim.py bodrum.pkl CIKTI.dxf` ; önizleme: `plot2.py CIKTI.dxf out.png x0 y0 x1 y1 genişlik`
- Kullanıcı kuralı: TÜM KANALLAR otopark girişi (güney, araç asansörü) tarafındaki şaftlardan çıkar; otopark h = 3,00 m.
- Hesap: sığınak net 109,44 m² ×3,00 ×4 → 1.400 / egzoz 1.260 / duman (>100 m²) 3.500 m³/h, perde geçişi v=2,5 m/s.
  Otopark net 769,71 m² ×3 ×10 → 23.500 m³/h duman/egzoz, taze hava %90 = 21.150 m³/h, 10'ar kanal yanağı menfezi.
- Hatlar: otopark taze (B) + sığınak taze (A) orta kolon aksının batısında → SW taze hava şaftı; sığınak duman (D), sığınak egzoz (S), otopark egzoz (E) doğusunda → SE egzoz şaftı (araç asansörü yanı).
- Kontrolör ajan: 1. tur RED (dilatasyon kolonu çakışması, etiketler), düzeltme sonrası ONAY.
- Teslim yalnız DXF (kullanıcı tercihi), mimari altlık + kolonlar aynı koordinatta.
