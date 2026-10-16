**16.10.2026: Bu betiklerin çıktısı (SASKİ'yi temel paftalarına bölmek) KULLANICI TARAFINDAN REDDEDİLDİ.** Doğru mantık: `proje/STANDART/STANDART_KURALLAR_ALTYAPI_SARNIC.md` son bölüm. Hizalama kısmı (giriş yazısı + korelasyon) yeniden kullanılabilir — ama yön tersine: temel → SASKİ.

# SASKİ onay dosyasını kullanıcının temel planına işleme (16.10.2026)

1. `hiza_korelasyon.py SASKI.dxf TEMEL.dxf` → kayd.json: blok başına öteleme ince ayarı. Ölçek 4 (SASKİ birimi → cm;
   rögar arası 185,4 birim = 6,82 m boru + 0,60 m rögar). Başlangıç: iki dosyadaki "X BLOK GİRİŞ" yazıları
   (kullanıcı hiza için ekliyor). İnce ayar: temel çizgileri ile ölçeklenmiş SASKİ çizgilerinin raster çapraz korelasyonu.
   Kontrol: SASKİ B blok dış hattı temel B dış hattına 2,6 / 1,2 cm farkla oturdu.
2. `saski_temel_isle.py SASKI.dxf TEMEL.dxf kayd.json CIKIS.dxf` → blok başına SASKİ altyapısı (SIVA hat/rögar,
   MAHALYAZI R no / 60x60 / Ø150 L, ubg_kot kot blokları) ROTAS-SASKI-* katmanlarında; solda SASKİ vaziyet altyapı planı,
   sağda kanal durum belgesi + bağlantı/sayaç detayları; üstte notlar. Dinamik blok uzantı sözlükleri atılır (audit 0).
Bölge kutuları (BOL) projeye özeldir (Korucuk 3346/13 A-B-C-D blok); yeni projede yeniden belirlenir.
