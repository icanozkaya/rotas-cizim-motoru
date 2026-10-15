# ROTAŞ STANDART — Sıhhi tesisat + Yerden ısıtma (kullanıcı kaydı 15.10.2026 21:24)

Kullanıcı: "BU SIHHİ VE YERDEN ISITMAYI SİSTEME KAYIT ET, HER YERDE BUNLARI KULLANACAKSIN. GEREKİRSE BEN SANA ÜZERİNDE
DEĞİŞTİRME YETKİSİ VERİRİM. BAŞKA KONUŞMADA AÇSAM DA BU SİSTEMİ KULLANACAKSIN."

- Sıhhi tesisat: motor `motor/sihhi2/` (plan.py → sema.py → pafta.py), referans çıktı `STANDART_SIHHI_new_block.dxf`.
- Yerden ısıtma: motor `motor/yerden2/` (yerden.py; bloklar `kutuphane/yerden/ROTAS_YI_BLOKLAR.dxf`, kullanıcının
  bloklarından birebir), referans çıktı `STANDART_YERDEN_ISITMA_new_block.dxf` + `.xlsx` (planda kollektör + ayaklar).
- Bu motorların tarzı/kuralları kullanıcının yazılı yetkisi olmadan DEĞİŞTİRİLMEZ. Yeni proje = aynı motor, yeni mimari.
- Kurallar: README.md en üstteki kural blokları (D, C, B, 14.10). Teslim öncesi kontrolör onayı (`motor/kontrolor/`).
- Bilinen açık maddeler (kullanıcı yetkisiyle yapılacak): ILERLEME_NOTU.md.

- EK KURALLAR (altyapı/rögar, vaziyet, yağmur sarnıcı, merkezi sistem, havalandırma): `STANDART_KURALLAR_ALTYAPI_SARNIC.md` — kullanıcı kaydı 15.10.2026 21:27, sihhi2/yerden2 ile BİRLİKTE uygulanır.
# ROTAŞ STANDART — Sığınak havalandırma (duman tahliyeli) (kullanıcı kaydı 15.10.2026)
Kullanıcı: "HAVALANDIRMA SİSTEMİ İÇİN KAYIT ET BU ÇİZDİĞİN DOSYAYI ... PANTOLON VESAİRE YAPARKEN BÖLMELERİNİ GÖSTER
VE KANALLARIN HEPSİNİ BİR YERDEN YAN YANA ÇIKART, KURANGLEZ OLACAKMIŞ GİBİ TASARLA".
- Motor `motor/ab2750/siginak_hav.py` (hesap kuralları `motor/siginak/README.md`), referans çıktı `STANDART_SIGINAK_HAVALANDIRMA_ab2750.dxf`.
- Tarz: taze emiş + duman atış + egzoz atış perde geçişleri tek perdede YAN YANA, ortak bölmeli KURANGLEZ (emiş +0,50 ızgara,
  atışlar +2,50 panjur, hücreler betonarme bölmeli); B-B görünüş + A-A kesit detayı paftada.
- Kanal özel parçaları: kavisli dirsek R iç 0,5·W + yönlendirici kanat; yer yoksa köşeli dirsek kanat dizili; pantolon ayrımda
  AYIRICI BÖLME levhası + kol kanatları; T dalda yuvarlatılmış ağız + ayar kanadı; 45° ofset; 20 cm konik redüksiyon; flanş çizgileri.
  Kaçınılmaz kanal kesişmesinde alttaki kanal kesikli (…-GIZLI katmanı). 1/20 özel parça detay paftası eklenir.
- Kolonlar teslim dosyasında ROTAS-MIMARI-KOLON katmanında bırakılır. Teslim yalnız DXF.
