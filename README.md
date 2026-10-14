# ROTAŞ Çizim Motoru

ROTAŞ Mühendislik — MTY CAD standardında sıhhi tesisat, yerden ısıtma, klima ve yağmur projesi üreten Python çizim motoru.

## İçerik
| Klasör | Ne var |
|---|---|
| `motor/` | Çekirdek: `cad.py` (kayıt), `emit.py` (DXF + DWG metni), `mtyblk.py` (MTY blokları), `spiral3.py` (yerden ısıtma salyangozu), `dxfparse.py`, Cafer Göktaş (`cg2_*`), ekipman kütüphanesi (`ekipman.py`) |
| `motor/p2/` | Genel proje motoru: `gp.py`, `gsheet.py` (kolon/yağmur şeması, antet), `gheat.py` (ısı kaybı), `gheatsheet.py`, `gklima.py`, `gufh.py` (devre ayağı optimizasyonu), `gexcel.py`, `xcheck.py` (kesişme/köprü/çakışma temizliği), `ghidrolik.py` (kombi pompası, genleşme tankı, PEX kangal), `psychrolib.py` (MIT, psikrometri), `tcheck.py` (yazı çakışması), `emitp.py`, `pdfp.py` + projeler `tb.py`, `st.py`, `tb_excel.py`, `st_excel.py`; `router.py` (A* boru güzergâhı: duvar dibi, kapı/oda/kolon kaçınma) |
| `motor/p3/` | Emine Tunce (2 dükkân + 8 ofis, SASKİ altyapılı): `et.py`, `et_excel.py`, `rooms.py` (mahal poligonu çıkarma) |
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
- GENEL (13.10.2026, kullanıcı: "bir daha söyletme"): Her iş en son onaylanan sürümün üzerinden ve aynı tarzda yapılır (sıhhi = önceki onaylı sıhhi projeler / MTY bloklu kolon şeması; asansör = Korucuk onaylı seti; yangın = VOYAP yangın; ısıtma/yerden ısıtma = Emine Tunçel `p3/et.py` salyangoz + kapıdan geçen ayaklar). Kafaya göre yeni tarz, ayrı şema vb. yapılmaz.
- Tüm dosyalarda katman (kalem) adları `SCOTT-` ile başlar (teslimde 0 ve Defpoints dışındaki bütün katmanlar SCOTT- önekli).
- Plan ve akış/kolon şemalarındaki bütün vana ve cihazlar gerçek gösterimleriyle (MTY blokları / gerçek sembol; kutu, daire vb. temsili şekil yok) çizilir ve numaralandırılır (V-01, P-01 ... + ekipman listesi).
- Sıhhi kolon şeması tek şemadır: temiz su + sıcak su + pis su aynı şemada, kullanıcının MTY şemasındaki gibi vitrifiye "KOLON" blokları, PVC çatal, T.K., rögar blokları ile. Temiz/pis ayrı şema YAPILMAZ.
- Merkezi sıcak suya geçilen projede termosifon yazısı, termosifon sembolü ve termosifona giden sıcak/soğuk hat parçaları planda ve şemada tamamen kaldırılır; merkezi sıcak su ofisin sıcak su ağına bağlanır.
- Su deposu gereksiz yere ikiye bölünmez (tek depo).
- Dükkân peteği: dükkân başına 4 adet, duvar köşelerine dükkâna oranla, ~100x60 (gerekirse büyütülür).
- Yerden ısıtmada hiçbir çizgi üst üste binmez (serpantin, ayak, kollektör bağlantıları).
- Yangın pompa grubu şemada kesit (görünüş) olarak çizilir.
- Pis su kolon (iniş) noktası: kullanıcının MTY 'tavandan' pis su ağının çıkış ucu (en büyük Ø/SB etiketinin parçasından akış yönündeki uç), armatür ucu değil; betonarme kolona düşerse ağ boyunca ≥15 cm geri çekilir (`motor/voyap/tes/piscol2.py`).
- MRL asansör: makine yan perdeye ankrajlı duvar konsolunda (çapraz askılı, alttan sehpalı), makine askı kancası yok, kuyu aydınlatması her katta, regülatör ana ray yanında (kabin arkasında değil), halat 7xØ6,5, kesitlerde son kat döşemesi (+16,00 gibi) işlenir, döşeme kalınlıkları mimarideki gibi (öneri/kot yazısı yok), katmanlar SCOTT-, kapak sol alt köşede notlar üstünde, paftalar boşluksuz sıkıştırılır ve çizgiler üst üste binmez (`ornekler/asansor/ASANSOR_STANDARDI.md` §11).
- Yangın (13.10.2026): lift (araç asansörü) ara seviyelerine sprinkler konmaz; kolon (riser) hatları mahal ortasından değil duvar köşesinden çıkar; mahal sprinkler beslemeleri mümkün olduğunca mahal kapısından girer; çapı yazılmamış boru kalmaz (her boru parçasında DN + başlık sayısı).
- Merkezi sistemli ofis/dükkân binası (VOYAP 13.10.2026): her bağımsız bölüm girişinde sayaç dolabı (soğuk su + sıcak su sayacı + kalorimetre); 3 borulu sıcak su (soğuk / sıcak / sirkülasyon, sirkülasyon sayaç öncesinde biter); ofis yerden ısıtma 45/35, dükkân panel radyatör 70/50; kazan dairesi kullanıcı isterse sığınak içinde EI120 bölmeyle; otopark havalandırması 4 hava değişimi + duman tahliyesi 10 hava değişimi, egzoz çıkışı sığınağın karşı cephesinden, betonarmede boşluk notu; sığınak alanı ölçülür, alana göre taze hava/egzoz, 100 m² üstünde duman egzozu.
- Sprinkler boru çapı (Aselsan 02-Yangın pratiği): DN25 ≤2, DN32 3, DN40 ≤5, DN50 ≤10, DN65 ≤20, DN80 ≤40, DN100 ≤100, DN150 >100 başlık; ana kolon ve kat besleme buna göre; çap etiketi "DN.." ve üstünde başlık sayısı. Lejant/semboller `kutuphane/ornek_mekanik/aselsan_teknopark/`.
- Her çizim teslim öncesi kolon kontrolünden geçer: boru (yağmur dahil) ve sembol hiçbir betonarme kolon/perde poligonunu kesmez (`motor/gungoren/kolon_kontrol.py`); iniş kolona denk gelirse üst kat tavanında kolon yüzüne ötelenir ve (*) ile işaretlenir.
- ROTAŞ / MTY CAD standardı; her şey Türkçe; DWG ile birlikte DXF teslim.
- Kolondan boru geçmez; mutfak ve WC giderleri birleştirilmez; her ıslak hacim en yakın kendi kolonuna, kolon dibinden rögara.
- Hiçbir çizgi üst üste binmez: kesişmede köprü (boru tek parça polyline kalır); yazı altında boru KESİLMEZ, yazının altına maske (WIPEOUT) konur (`xcheck.py`).
- MTY blokları HİÇBİR ZAMAN patlatılmaz: kullanıcının kütüphanesindeki tanımla gerçek blok + öznitelik (kullanıcı MTY programında çapları vb. güncelleyebilmeli). Vana, çek valf, pislik tutucu, sayaç da MTY bloklarıdır.
- Yerden ısıtma devreleri patlatılmaz/kesilmez (her devre tek polyline). Etiketler kullanıcının `MTY-ETIKET` (devre) ve `MTY-RADYATOR MAHAL` (mahal) blokları ile, çerçeve içinde ve altı maskeli.
- "Düşüş" / bodrum tavanı toplama kurgusu YAPILMAZ: bodrum ıslak hacimleri üst katlardaki gibi döşemeden kendi kolonlarına bağlanır; bodrum kolonları pis su çukuruna.
- Bodrum varsa üst kat kolonları zemin katta biter, temele inmez; kolon diplerinden zemin kotundan ayrı ayrı doğrudan BİNA DIŞINDAKİ rögara.
- Zemin kat kolon hatları pompa basma hattına bağlanmaz: pompa basma ayrı rögara (R2), oradan ayrı hatla parsel bacasına.
- Pis su çukuru / pompasına havalık gösterilmez (plan ve şema).
- Yağmur suyu altyapısı yapılmaz (kanal, sızdırma bacası yok); yağmur iniş kolonları zemin katta biter, temele/bodruma inmez. İnişler kat planlarında cepheye / balkon köşesine yaslı (havada durmaz).
- Sayaç grubunda kollektör - vana - sayaç - çek valf hattı kesintisizdir; sayaç çıkış hatları birbirini kesmez.
- Bodrumda ıslak hacim veya depo varsa hidrofor ve pis su çukuru + dalgıç pompa işlenir; kot farklarına göre altyapı çizilir.
- Altyapı planı (zemin kotu) sıhhi paftaların en solunda; mimariden yalnız kolonlar + bina dış hattı; rögarlar bina dışında.
- Kalem kalınlıkları polyline sabit genişliği ile verilir (1/50'de 1 cm = 0,2 mm).
- Konut yerden ısıtma (devre ≤ 80 m), dükkan 1-2 adet duvar tipi split klima (hesabı rapora eklenir).
- Yerden ısıtma paftalarında tefriş ve mahal yazıları SİLİNMEZ; mutfak dolapları (tefriş) altına serpantin girmez; asansör, merdiven ve ortak alanlar ısıtılmaz.
- Projede klima varsa klimalar ŞEMAYA da eklenir (iç/dış ünite, bakır boru, drenaj; kat bantlarında) - mevcut iki projeye uygulanmayacak, sonraki dosyalardan itibaren.
- Depo: ≤10 BB 3 m³, her ek BB +0,5 m³; çatıdaysa hidrofor gerekmez; taşma/boşaltma açık uç bırakılmaz.
- Su sayaçları bina girişinde tek yerde; yağmur inişleri hesaplı, plan ve şemada.
- Temiz su kolonları her katta AYNI HİZADA; tamamı ortak alanda (merdiven holü / merdiven köşesi) kolon kutusu içinde. Başka bağımsız bölümün (dükkân, ofis) içinden üst katlara taşınmaz; sayaçtan kolonlara hatlar ortak alan asma tavanından.
- Şebeke / temiz su hatları kapı önlerinden ve kapı kanadından geçmez; ofis/daireye kapı dışındaki duvardan girilir.
- Temiz ve sıcak su hatları odalardan geçmez: hol ve ıslak hacim duvarlarından gider (A* güzergâhta odalar kapalı - `p2/router.py`).
- Zemin katta (veya alt katta) dükkân / koridor ortasına düşen pis su kolonu asma tavanda en yakın duvara kaydırılır, oradan zemin kotuna iner.
- Kombiler dış cepheye bitişik mahalde; baca doğrudan dış atmosfere (iç mahalde kalan kombi ofis içinde dış cepheye alınır).
- Yerden ısıtma bağlantı ayakları yalnız kendi bağımsız bölümünün holünden ve odanın kapısından geçer (duvar içinden, ortak alandan, başka odadan geçmez).
- Excel: örnek yerden ısıtma şablonu formüller bozulmadan, yazdırma alanları ayarlı, mahal m² mimariyle aynı. Şablondaki yabancı logo (dcm makina) hiçbir dosyada kullanılmaz (gexcel.logo_temizle).

## Asansör avan projesi (12.10.2026)
- Standart, pafta dizilimi, şablon hataları, kontrol listesi: `ornekler/asansor/ASANSOR_STANDARDI.md`
- Hesap motoru: `motor/asansor/asansor_hesap.py`. MMO avan trafik yöntemi (H ve S formülle hesaplanır, tablolarla doğrulandı), eski TS çapraz kontrolü, kuvvetler, halat, motor gücü, EN 81-20 alan ve imar kontrolleri: `python3 motor/asansor/asansor_hesap.py`
- Şablon DWG'ler: `ornekler/asansor/sablon/`. Makine daireli, makine dairesiz, kapak antet, eski TS trafik hesabı, MMO avan tabloları ve EN81-20 uygulama hesabı (xz). Örneklerin metin dökümleri `metin/`, önizlemeler `onizleme/` klasöründe.
- Asansör tipini (makine daireli / dairesiz) kullanıcı söyler. Şablondaki hesap sayıları kopyadır; her projede yeniden hesaplanır.
- Tesisat: asansör kuyusu ve makine dairesinden boru geçmez. Kuyu dibine pis su bağlantısı yapılmaz. Altyapı hatları ve rögarlar kuyu dibi altından ve kapı önünden geçmez. Asansör ısıtılmaz.

## AutoCAD içi araçlar
`araclar/autocad_lisp/BENIOKU.md`: `BPDF` (tüm paftaları `ROTAS_PAFTA` bloğuyla toplu PDF), `TOTLEN`, `TAGDEVICES`, `SPRINKLERLAYOUT`. Motor DWG'lerinde MTY blokları gerçek blok + öznitelik olarak gelir.

## Deneme modülleri (14.10.2026, `motor/deneme/`)
Araştırma raporları `kutuphane/arastirma/01-09`, ortak kurallar `DENEME_KURALLARI.md`. Her modülde `BENIOKU.md` var; çıktılar `proje/denemeler/`.
| Modül | Ne üretir |
|---|---|
| `semboller` | 134 sembollük birleşik kütüphane (62 MTY bloğu) + `otomatik_lejant(doc)` (kullanılan semboller + adet tablosu) |
| `kazan_dairesi` | JSON → kaskad kazan dairesi prensip şeması + cihaz listesi |
| `pompa_grubu` | Yangın pompa grubu, hidrofor, pis su çukuru kesitleri (JSON) |
| `sprinkler` | Mahal → TS EN 12845 başlık yerleşimi, ortogonal boru ağacı, DN etiketleri, Hazen-Williams hidrolik |
| `kanal` | Menfez/debi → kanal güzergâhı, boyutlandırma, çift çizgi plan, basınç kaybı ve sac metrajı; otopark jet fan |
| `dogalgaz` | İzometrik kolon şeması + çap/basınç kaybı hesabı (Excel formüllü); AKSAGAZ ile teyit bekliyor |
| `radyator` | Radyatör planı, kalorifer kolon şeması, kritik devre çap tablosu |
| `uctan_uca` | new_block.dxf mimarisinden sıhhi deneme + kullanıcı çizimiyle karşılaştırma (`KARSILASTIRMA.md`) |
