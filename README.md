# ROTAŞ Çizim Motoru

ROTAŞ Mühendislik — MTY CAD standardında sıhhi tesisat, yerden ısıtma, klima ve yağmur projesi üreten Python çizim motoru.

## İçerik
| Klasör | Ne var |
|---|---|
| `motor/` | Çekirdek: `cad.py` (kayıt), `emit.py` (DXF + DWG metni), `mtyblk.py` (MTY blokları), `spiral3.py` (yerden ısıtma salyangozu), `dxfparse.py`, Cafer Göktaş (`cg2_*`), ekipman kütüphanesi (`ekipman.py`) |
| `motor/p2/` | Genel proje motoru: `gp.py`, `gsheet.py` (kolon/yağmur şeması, antet), `gheat.py` (ısı kaybı), `gheatsheet.py`, `gklima.py`, `gufh.py` (devre ayağı optimizasyonu), `gexcel.py`, `xcheck.py` (kesişme/köprü/çakışma temizliği), `ghidrolik.py` (kombi pompası, genleşme tankı, PEX kangal), `psychrolib.py` (MIT, psikrometri), `tcheck.py` (yazı çakışması), `emitp.py`, `pdfp.py` + projeler `tb.py`, `st.py`, `tb_excel.py`, `st_excel.py` |
| `araclar/` | `dwgtools/mkdwg.c` (DWG yazıcı), yamalı LibreDWG (`libredwg_yamali.tar.xz`), önizleme yardımcıları |
| `kutuphane/` | MTY blok kütüphanesi (`/tmp/claude-0/blk` + `blklib.pkl`) |
| `sablon/` | Örnek yerden ısıtma Excel şablonu (`ornek_yi.xlsx`) |
| `proje/` | Tuncay Bulut ve Sinem Turhan: mimari DWG + teslim edilen DWG/Excel/PDF |

## Yeni oturumda kurulum
```bash
cd /home/claude/rotas-cizim-motoru
mkdir -p /home/claude/nb /tmp/claude-0/xl /tmp/claude-0/p2/out
cp -r motor/. /home/claude/nb/
tar -xJf kutuphane/ROTAS_2_MTY_BLOKLARI_2026-10-11.tar.xz -C /
tar -xJf araclar/libredwg_yamali.tar.xz -C /    # /usr/local/lib/libredwg*, /usr/local/bin/dwg2dxf
cp -r araclar/dwgtools /home/claude/ && cd /home/claude/dwgtools && gcc -O2 -o mkdwg mkdwg.c -I/usr/local/include -L/usr/local/lib -lredwg
cp sablon/ornek_yi.xlsx /tmp/claude-0/xl/
cp proje/tuncay_bulut/mimari.dwg /tmp/claude-0/p2/tb.dwg; cp proje/sinem_turhan/mimari.dwg /tmp/claude-0/p2/st.dwg
cp araclar/*.py /tmp/claude-0/p2/
# mimariyi DXF'e çevir ve düzleştir (tb: utf-8, st: cp1254)
LD_LIBRARY_PATH=/usr/local/lib dwg2dxf -y -o /tmp/claude-0/p2/tb.dxf /tmp/claude-0/p2/tb.dwg
LD_LIBRARY_PATH=/usr/local/lib dwg2dxf -y -o /tmp/claude-0/p2/st.dxf /tmp/claude-0/p2/st.dwg
# sonra dxfparse.py ile .flat.pkl üret (D.ENC ayarı)
pip install --break-system-packages ezdxf shapely openpyxl pillow
```

## Çalıştırma
```bash
cd /home/claude/nb/p2
python3 st.py && python3 st_excel.py
python3 emitp.py /tmp/claude-0/p2/st_R.pkl /tmp/claude-0/p2/out/SINEM_TURHAN_SIHHI_ISITMA   # DXF + DWG + geri okuma kontrolü
python3 pdfp.py  /tmp/claude-0/p2/st_R.pkl /tmp/claude-0/p2/out/SINEM_TURHAN_ONIZLEME.pdf
```

## Kalıcı kurallar (kullanıcı talimatları)
- ROTAŞ / MTY CAD standardı; her şey Türkçe; DWG ile birlikte DXF teslim.
- Kolondan boru geçmez; mutfak ve WC giderleri birleştirilmez; her ıslak hacim en yakın kendi kolonuna, kolon dibinden rögara.
- Hiçbir çizgi üst üste binmez: kesişmede köprü, yazı altında boru kesilir (`xcheck.py`).
- Bodrum tavanı pis su toplamaları ayrı paftada, farklı katman/çizgi tipi ile gösterilir.
- Bodrumda ıslak hacim veya depo varsa hidrofor ve pis su çukuru + dalgıç pompa işlenir; kot farklarına göre altyapı çizilir.
- Altyapı (temel) planı sıhhi paftaların en solunda; temel planında yalnız kolonlar.
- Kalem kalınlıkları polyline sabit genişliği ile verilir (1/50'de 1 cm = 0,2 mm).
- Konut yerden ısıtma (devre ≤ 80 m), dükkan 1-2 adet duvar tipi split klima (hesabı rapora eklenir).
- Depo: ≤10 BB 3 m³, her ek BB +0,5 m³; çatıdaysa hidrofor gerekmez; taşma/boşaltma açık uç bırakılmaz.
- Su sayaçları bina girişinde tek yerde; yağmur inişleri hesaplı, plan ve şemada.
- Excel: örnek yerden ısıtma şablonu formüller bozulmadan, yazdırma alanları ayarlı, mahal m² mimariyle aynı.

## AutoCAD içi araçlar
`araclar/autocad_lisp/BENIOKU.md`: `BPDF` (tüm paftaları `ROTAS_PAFTA` bloğuyla toplu PDF), `TOTLEN`, `TAGDEVICES`, `SPRINKLERLAYOUT`. Motor DWG'lerinde MTY blokları gerçek blok + öznitelik olarak gelir.
