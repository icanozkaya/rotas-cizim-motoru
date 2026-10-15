# ROTAŞ STANDART — Sıhhi tesisat + Yerden ısıtma (kullanıcı kaydı 15.10.2026 21:24)

Kullanıcı: "BU SIHHİ VE YERDEN ISITMAYI SİSTEME KAYIT ET, HER YERDE BUNLARI KULLANACAKSIN. GEREKİRSE BEN SANA ÜZERİNDE
DEĞİŞTİRME YETKİSİ VERİRİM. BAŞKA KONUŞMADA AÇSAM DA BU SİSTEMİ KULLANACAKSIN."

- Sıhhi tesisat: motor `motor/sihhi2/` (plan.py → sema.py → pafta.py), referans çıktı `STANDART_SIHHI_new_block.dxf`.
- Yerden ısıtma: motor `motor/yerden2/` (yerden.py; bloklar `kutuphane/yerden/ROTAS_YI_BLOKLAR.dxf`, kullanıcının
  bloklarından birebir), referans çıktı `STANDART_YERDEN_ISITMA_new_block.dxf` + `.xlsx` (planda kollektör + ayaklar).
- Bu motorların tarzı/kuralları kullanıcının yazılı yetkisi olmadan DEĞİŞTİRİLMEZ. Yeni proje = aynı motor, yeni mimari.
- Kurallar: README.md en üstteki kural blokları (D, C, B, 14.10). Teslim öncesi kontrolör onayı (`motor/kontrolor/`).
- Bilinen açık maddeler (kullanıcı yetkisiyle yapılacak): ILERLEME_NOTU.md.
