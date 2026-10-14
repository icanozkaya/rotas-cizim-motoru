# semboller — birleşik mekanik tesisat sembol kütüphanesi (DENEME, 14.10.2026)

## Ne yapar
- `sembol.py`: sıhhi, ısıtma, yangın, havalandırma ve doğalgaz için 134 sembolü (BLOCK) tanımlar ve çizer.
  - **MTY bloğu varsa o kullanılır.** Kaynaklar: `/tmp/claude-0/blk/*.dxf` (yoksa `kutuphane/ROTAS_2_MTY_BLOKLARI_*.tar.xz` açılır) ve VOYAP dosyasındaki MTY sprinkler blokları. Bloklar patlatılmaz, iç katmanları korunur. Dinamik bloktan kalan tanımsız `*U`/`*X` alt-INSERT'ler yalnız kaynak kopyada atlanır.
  - Yangın: Aselsan 02 lejantından çıkarılmış semboller (`motor/voyap/asel_sym.pkl`, salt okunur; VOYAP'ta kullanılan biçim).
  - Diğerleri: `kutuphane/arastirma/03_SEMBOLLER.md` geometrisi (L = 20 cm vana, B = 50 cm cihaz, havalandırma gerçek ölçü). Kutu veya daire ile temsili sembol yoktur.
- `ciz(hedef, ad, x, y, aci=0, olcek=1, no='V-01', katman=None, ozn={'CAP': 'DN25'})`: blok tanımlı değilse tanımlar, INSERT eder ve numarayı `NO` özniteliği olarak yazar. Numara her zaman düz okunur ve sembolün üstünde durur.
- `blok_tanimla(doc, ad)` / `tumunu_tanimla(doc)`: yalnız BLOCK tanımı üretir.
- `hat(hedef, p0, p1, [(t, ad, no), ...], katman)`: düz boru çizer. Boru sembol boyunca kesilir; pislik tutucu ve kalorimetrede gövde borudur, boru kesilmez. Simetrik semboller ters dönmez; yönlü olanlar (çekvalf, pompa ...) boru yönünü korur.
- `otomatik_lejant(doc)`: modelspace'teki INSERT'leri sayar. Kütüphane dışı grup bloklarının içi özyinelemeli taranır. Tesisat grubu, INSERT'in katmanından bulunur. Yalnız kullanılan sembollerin lejantını ve ADET tablosunu çizimin sağına çizer. VOYAP'taki eski blok adları (`ASL-*`, `Y-*`) da tanınır; lejantta çizimde kullanılan blok gösterilir.
- `kullanim_say(doc)` / `kullanim_say_grup(doc)`: yalnız sayım yapar.

## Çalıştırma
```
python3 motor/deneme/semboller/olustur.py            # DXF'leri üretir
python3 motor/deneme/semboller/olustur.py --png /tmp/x   # + kontrol PNG'leri (depo dışı)
```
Çıktılar (AC1032):
- `proje/denemeler/semboller/SEMBOL_KUTUPHANESI.dxf`: 183 blok tanımı ve 5 lejant paftası. Tablo sütunları SEMBOL | AÇIKLAMA | KAYNAK; her paftada ilgili boru çizgileri de vardır.
- `proje/denemeler/semboller/OTOMATIK_LEJANT_DENEME.dxf`: örnek şema (DENEME, adetler `deneme_param.json`) ve otomatik lejant ile adet tabloları.

Katmanlar: `ROTAS-<GRUP>-SEMBOL`, `ROTAS-<GRUP>-<BORU>`, `ROTAS-LEJANT-*`. MTY blok içleri kendi katmanlarında kalır.

## Sınırlar / açık konular
- 03 §8 çelişkili semboller önerilen biçimle çizildi ve lejantta (*) ile işaretlendi: küresel/ventil, sprinkler dik/sarkık, çekvalf, doğalgaz vanası.
- README "Kalıcı kurallar" katman öneki `SCOTT-`, DENEME_KURALLARI ise `ROTAS-` diyor. Deneme kuralına uyuldu (`ROTAS-`).
- Aynı adlı MTY blokları (ör. `MTY-KURESEL VANA` sıhhi ve radyatör sürümü) bir DXF'te tek tanım olabilir. Sıhhi VANALAR sürümü önceliklidir. Kosva için radyatör kolon şeması sürümü alındı (sıhhi sürüm yalnız bir daire).
- Sprinkler MTY blokları VOYAP dosyasından (`/tmp/claude-0/vy/sih.dxf`) okunur. Dosya yoksa bu iki sembol atlanır ve uyarı yazılır. Lejantta koruma dairesi (`*ALAN*` katmanı) gösterilmez (`ROTAS-LJ-` kopyası). Çizimdeki blok aynen kalır.
- Yazı maskesi (WIPEOUT): lejant yazıları hücre içindedir ve altlarında çizgi yoktur. Deneme şemasında etiketler boru dışına konduğu için maske gerekmedi (VOYAP notu: kullanıcı görünmeyen wipeout istemiyor).
- MTY armatür "KAT PLANI" blokları (LAVABO1 vb.) yalnız bağlantı noktasıdır. Lejantta onların yerine KOLON şeması ve `std_*_plan` blokları kullanıldı.
