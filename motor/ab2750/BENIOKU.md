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
