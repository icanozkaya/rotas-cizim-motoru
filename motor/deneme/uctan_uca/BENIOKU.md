# uctan_uca — new_block.dxf üzerinde uçtan uca sıhhi tesisat denemesi (14.10.2026)

## Ne yapar
1. `mimari.py`: `ornekler/new_block.dxf.xz` -> `/tmp/claude-0/uu/new_block.dxf`; yalnız **MKDU0** (mimari) okunur,
   `MTY-*`, `M-*`, `RAST-*`, `TEM.SU` süzülerek `/tmp/claude-0/uu/new_block_mimari.dxf` yazılır.
   Tanıma (05_ALGORITMALAR §1, kural tabanlı):
   - kat pencereleri: zemin penceresi + kat kaydırmaları (oda etiketlerinden ölçüldü: 1. kat +2034, 2. kat +4082; temel -2629),
   - mahal etiketleri (MTEXT hizası dikkate alınarak merkez), ıslak hacim dikdörtgeni = etiketten 4 yöne ışın (duvar çizgileri),
   - armatürler geometri imzasıyla: klozet (birbirine değen yaylardan elips), lavabo (3 küçük daire: 2 batarya + gider),
     duş (gider + kare tekne / köşegen), eviye (mutfakta r≤3,5 gider), alaturka (r≈5 gider), yer süzgeci (kısa yatay+dikey çizgi
     ızgarası), çamaşır mak. (banyoda 50-72 cm boş kare), bulaşık mak. / kombi (mimari yazılarından),
   - betonarme kolon/perde: ANSI35 taramalı poligonlar, daire no: 1-9 rakam yazıları (giriş kapısı yanı).
2. `nb.py`: pis su kolonu = çapa armatürün (klozet / eviye / duş) en yakın duvarı boyunca köşe, betonarme dışına ötelenir;
   zeminde bulunur, üst katlarda aynı hizada. Kat içi pis su: kolondan başlayan en yakın-ağaç (eğik, armatürden kolona doğrudan,
   kullanıcı tarzı) + her parçada `MTY-PIS SU CAP SB` (Ø/SB, akış yukarısı toplamı). Temiz/sıcak su: merdiven holünde
   9 kolonlu kolon kutusu -> daire girişi -> armatürler (p2 `router.py` A*, odalar kapalı, betonarme yasak), kombiden sıcak su.
   Temel planı: bina dış hattı (duvarlardan morfolojik kapama) + kolonlar + kolon dipleri -> doğu cephesindeki rögarlar
   (kolon y kümelerine göre R1..Rn, A* ile kolon kesmeden) -> PB.
3. `sema.py`: p2 `gsheet.sihhi_sema` ile tek açılımlı kolon şeması (3 daire konumu x 3 kat, D1..D9), rögar şeması,
   `gsheet.yagmur_sema` (9 iniş), antet / notlar / lejant, `MTY-SIHHİ DETAYLAR` bloğu, pafta çerçeveleri.
4. `cikti.py`: kolon çakışma / boşta uç kontrolü (`gp.check`), köprü / yazı maskesi / tekrar temizliği (`xcheck`), p2 `emit.py`
   ile DXF, sonra model uzayı katmanlarına `ROTAS-` öneki (MTY blok tanımlarının iç katmanları korunur), sürüm AC1032.
5. `karsilastir.py`: kullanıcının aynı dosyadaki MTY çizimi ile karşılaştırma -> `KARSILASTIRMA.md`.

## Çalıştırma
```bash
cd /tmp/claude-0/uu   # çalışma klasörü (önbellek: mk.pkl, nb_ozet.json)
python3 /home/claude/rotas-cizim-motoru/motor/deneme/uctan_uca/nb.py [params.json]   # ~2 dk
python3 /home/claude/rotas-cizim-motoru/motor/deneme/uctan_uca/karsilastir.py
```
Gereken: `/home/claude/nb` (motor kopyası, kurulum.sh), `/tmp/claude-0/blk` MTY blokları, ezdxf / shapely / cv2 / scipy / skimage.
Parametreler (`params.json`): `rogar_cephe`, `depo`, `depo_V`, `kombi_kw`, `cikti`.
Çıktı: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME.dxf` (antette "DENEME" yazar).

## Sınırlar
- Armatür imzaları bu mimarın çizim tarzına göre ayarlı; başka dosyada eşikler gözden geçirilmeli. Mimaride işaretli olmayan
  cihaz (3. daire bulaşık mak., wc+banyo çamaşır mak.) bulunamaz.
- Yük birimi / çap tablosu p2 `gp` değerleri (YB, Ø mm); kullanıcının MB / inç tablosu değil.
- Kolon yeri kuralı (klozet duvarı köşesi) kullanıcının şaft / ortak duvar tercihinden ~1-1,5 m farklı.
- Çatı planı, balkon yer süzgeçleri, WC havalandırma izometrisi ve ısıtma sırası yapılmadı. DWG / Excel üretilmedi (deneme kuralı: yalnız DXF).
- Kolon şeması tüm katlarda zemin kat armatür dizisini kullanır (1. kattaki yüklük farkı şemada görünmez).
