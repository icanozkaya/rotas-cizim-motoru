# ab2750 — Adapazarı Karapınar 2750 ada 7 parsel, A-B blok (ENGİN KABA ve hiss.), mekanik proje

Kullanıcı talebi (15.10.2026 18:05): sıhhi (2 blok, parsel bacası en yakın yola), sığınak havalandırma (duman tahliyeli),
merkezi sistem (kazan dairesi + boyler A blok bodrumunda, B blok buradan beslenir), yerden ısıtma; ısı kaybı ve yerden
ısıtma hesapları ile teslim. Teslim: yalnız DXF (+ hesap Excel), kolonlar dosyada (hizalama).

## Mimari
- Kaynak: `proje/ab2750/A-B_BLOK_MIMARI_15.10.2026.dwg` (AC1018, cp1254). Hazırlık:
  `dwg2dxf -y -o /tmp/claude-0/ab/mim.dxf mim.dwg` → `python3 /tmp/claude-0/flat.py mim.dxf mim.pkl cp1254`
  (flat.py = dxfparse.read + flatten; düz liste `mim_fl.pkl`: ('L'|'P'|'C'|'T', katman, veri, blok_yolu)).
- `mimari.py`: kat pencereleri `KATLAR` (B blok Z/1/2 x +6000; A blok bodrum/Z/1/2 x +8655), mahal poligonları
  (raster + kapı yayı kapalı konum çizgisi + jeodezik ağırlıklı Voronoi, mimari m² ile), daire ataması ('DAİRE n'
  yazısından jeodezik), kapılar, betonarme. `python3 -c "import mimari; mimari.hepsi()"` → `kat_<blok>_<kat>.json`
  (kopyası `proje/ab2750/`).
- B blok 30 daire (Z 1-10, 1. kat 11-20, 2. kat 21-30), A blok 48 daire (Z 1-16, 1. kat 17-32, 2. kat 33-48).
  A blok bodrum: SIĞINAK 241 m², KAZAN DAİRESİ 21,1 m², jeneratör, mescitler, WC/abdesthane, mutfak nişi.
- Kotlar: B blok SBK +0,75, katlar +3,75 / +6,75; A blok +0,80 / +3,80 / +6,80; kat yüksekliği 3,00 m.
- Vaziyet: yollar batı 7 m, doğu 10 m, güney 12 m. Kuzey yönü planda yukarı kabul edildi (mimaride kuzey oku yok).

## Sığınak havalandırması (duman tahliyeli) — `siginak_hav.py` (15.10.2026)
`python3 motor/ab2750/siginak_hav.py` → `proje/ab2750/AB2750_SIGINAK_HAVALANDIRMA.dxf` (R2010/AC1024, cm, yalnız DXF; ~6 s).
Girdi `/tmp/claude-0/ab/mim_fl.pkl` (yukarıdaki hazırlık) + `kat_A_B.json`. Betik sonunda KONTROL satırları basar
(kolon/perde kesişimi, kazan dairesi/asansör, çizgi-çizgi ve yazı binmesi, boşta kanal ucu, ağlar arası kesişme, hesap tekrarı, audit).
- Net alan = SIĞINAK mahal poligonu 229,81 + mutfak nişi 1,31 + sığınak içi 4 WC hücresi 5,80 − 7 serbest kolon 1,88 = 235,04 m².
- Kullanıcı kuralı: taze 235,04×3×4 = 2.820 → 2.900 m³/h; egzoz 2.610; duman 10/h 7.051 → 7.500 m³/h;
  perde geçişleri (v=2,5 m/s) taze 70×50, egzoz 60×50, duman 120×80 cm (ölçü listesi 80×50'nin üstüne uzatıldı).
- Yerleşim (kanallar kesişmesin diye üç ayrı cephe): taze hava emişi KUZEY perde (kuzey kanat, SHC-1 cihazı) → L1 hattı y=-33110
  + doğu hattı x=24560; duman tahliye BATI perde (DTF-1 F400) ← L2 hattı y=-33330 + x=24230; egzoz DOĞU perde y=-34480 (EF-1) ←
  WC/mutfak nişi önü. Mimarın "MENFEZ"/"EGZOZ ÇIKIŞI" yazıları jeneratör odasına ait; sığınak için kullanılmadı.
- Kanal: kanal.py `kanal_sec` (taze/egzoz v≤4,5, h≤400; duman v≤5,0, h≤500), menfez `menfez_sec`; yan (kanal yanağı) menfez;
  semboller saf geometri (SHC, GSK, kovan, baca, aksiyel/kanal tipi fan); MTY bloğu yok.
- Hesap tablosu `proje/isitma_944_343/SIGINAK_HAVALANDIRMA_HESABI.dxf` biçiminde (+ kişi/koruma satırları), kanal/menfez/fan basınç
  çizelgeleri, prensip kesit şeması (3 panel), lejant ve notlar bodrum pafta penceresinin solunda.
