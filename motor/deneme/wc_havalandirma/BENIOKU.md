# wc_havalandirma — penceresiz ıslak hacim mekanik havalandırması (deneme, 14.10.2026)

## Ne yapar
Girdi JSON (katlar, şaftlar, penceresiz WC/banyo listesi) → hesap → tek pafta DXF:
1. **Debi** (`hesap.py`)
   - DIN 18017-3 asgari değerleri tabloda karşılaştırma için gösterilir: banyo 40/60, WC 20/30 m³/h (sürekli/kesikli).
   - Tasarımda kullanıcının örnek kabulü esas alınır: hacim başına **80 m³/h**, iki kademeli **80/160 m³/h - 50 Pa - Ø150** aspiratör.
   - Aynı daire, aynı şaft ve aynı kattaki hacimler tek aspiratöre bağlanır (new_block örneği: banyo + wc-lvb. → 160).
   - `oda_basina_aspirator: true` verilirse her hacme ayrı aspiratör konur.
2. **Şaft kesiti:** galvaniz dikdörtgen kanal, 50 mm adımlı, sabit kesit. Kesit en büyük debiye göre seçilir (v ≤ 6 m/s, en az 150x150). Huebscher eşdeğer çapı ve mimari şaft iç ölçüsü (kanal + 10 cm) da yazılır.
3. **Basınç kaybı** (Darcy + Swamee-Jain, ρ = 1,2)
   - Branş: Ø150 spiro + 0,5 m flex (×1,5). ζ: dirsek 0,3 + geri akış klapesi 1,0 + T-branş 1,0. Toplam ≤ aspiratör basıncı (50 Pa) kontrol edilir.
   - Şaft: her bölümde R·L + T düz geçiş ζ 0,3. Üst bölümde çatı geçişi ζ 0,5 + çatı başlığı ζ 1,0 eklenir.
   - Kritik hat = branş + şaft.
4. **Çatı tipi fan:** Q = Σ aspiratör (örnekteki 240 / 480 m³/h ile birebir çıkar). P = şaft kaybı × 1,10. Sınıf (ÇF-200…500) tipik eğriden seçilir: P = Pmax·(1-(Q/Qmax)²), Q ≤ 0,85·Qmax. Marka/model katalogdan teyit edilmelidir.
5. **Çizim** (`ciz.py`), kullanıcının new_block son paftasındaki izometri tarzında:
   - Kat bantları ve kotlar.
   - Her şaft için düşey kanal (3 kenar çizgisi + alt kapak + üst yüz) ve çatı döşemesi geçişi.
   - Her katta Ø150 branş, geri akış klapesi, akordeon flex ve küp aspiratör. Aspiratör yazısı: "Wc Aspiratörü / 80 m3/h-50 pa / Ø150 mm / D3 · wc+banyo".
   - Şaft bölüm etiketi döndürülmüş "150x150 / 240 m³/h" biçimindedir.
   - Şaft başında izometrik çatı tipi fan, üstünde "Ş1 / D3-5-8 / Çatı Tipi Fan ÇF-1 / MEKANİK HAVALANDIRMA / 240 m³/h - 13 Pa".
   - Hesap tabloları: debi (DIN ve kabul, hava değişimi), şaft basınç kaybı, branş kontrolü ve fan seçimi, ayrıca havalandırmaya alınmayan hacimler.
   - Lejant (R2): otomatik; yalnız izometride çizilen öğeler + çizim sırasında sayılan ADET. Notlar.
   - Yazı bir çizgiye değerse altına WIPEOUT konur. Yazı-yazı çakışması sayılır (iki çıktıda da 0).
6. **Mimariden algılama** (`algila.py`, new_block.dxf):
   - `uctan_uca/mimari.py` ile MKDU0 okunur, `rooms.detect` ile mahal poligonları çıkarılır.
   - Islak hacim pencereli sayılır: dış bölge veya balkonla ≥ 40 cm ortak duvarı olmalı VE 90 cm içinde pencere ölçü yazısı (60/60, 160/230) bulunmalı. Kapı (K1..K3) ve kolon (S../P..) yanındaki ölçü yazıları sayılmaz.
   - Şaft: mimarın "mek. havl." yazısı (≤ 3 m). Katlar arası aynı düşeyde toplanır → Ş1..Şn.
   - Daire no: en yakın mutfak → kapıdaki daire numarası.

## Çalıştırma
```bash
cd /home/claude/rotas-cizim-motoru/motor/deneme/wc_havalandirma
python3 calistir.py ornek_z2_9daire.json ../../../proje/denemeler/wc_havalandirma/ORNEK_Z2_9DAIRE_WC_HAVALANDIRMA.dxf
cd /tmp/claude-0/uu && python3 /home/claude/rotas-cizim-motoru/motor/deneme/wc_havalandirma/calistir.py --nb \
    /home/claude/rotas-cizim-motoru/proje/denemeler/wc_havalandirma/NB_WC_HAVALANDIRMA_DENEME.dxf   # algıla + hesap + çiz (~10 s)
python3 hesap.py <girdi.json>        # yalnız hesap dökümü
```
Gerekenler:
- ezdxf, shapely, opencv, scipy
- `--nb` için `uctan_uca` önbelleği (`/tmp/claude-0/uu`, yoksa `mimari.py` new_block.dxf.xz'yi açar)

## Girdi JSON
`katlar[{kod, ad, kot(m), h(m)}]`, `cati_kot`, `cati_ustu` (fan kaidesi, m),
`kabul{q_oda, kademeler, asp_basinc, baglanti_cap, oda_basina_aspirator}`, `saftlar[{ad, baglanti_yuk(m), kesit?[w,h]}]`,
`mahaller[{kat, daire, ad, tip: BANYO|WC, saft, brans_m, alan_m2}]` (yalnız penceresizler), `pencereli[...]` (bilgi).
`deneme: true` → pafta üstünde kırmızı DENEME başlığı.

## Dosyalar
- `hesap.py`: debi, kesit, basınç kaybı, fan seçimi
- `ciz.py`: izometri, tablolar, lejant, notlar, maske
- `algila.py`: new_block.dxf'ten penceresiz hacim ve şaft bulma
- `calistir.py`: komut satırı
- `ornek_z2_9daire.json`: elle hazırlanmış örnek, kullanıcının izometrisindeki kurgu (D3-5-8 240 m³/h; D2-4-7 ve D1-6-9 480 m³/h)
- `nb_algilanan.json`: algılama çıktısı (yeniden üretilir)

## new_block sonucu (algılanan)
| Şaft | Daireler | Debi | Kanal | Çatı fanı |
|---|---|---|---|---|
| Ş1 | D3-5-8 (wc+banyo / wc-banyo) | 240 m³/h | 150x150 | ÇF-200, 13 Pa |
| Ş2 | 1. kat wc-duş (yalnız 1. kat) | 80 m³/h | 150x150 | ÇF-200, 2 Pa |
| Ş3 | D2-4-7 (banyo + wc-lvb.) | 480 m³/h | 150x150 (5,9 m/s) | ÇF-200, 50 Pa |
| Ş4 | D1-6-9 | 400 m³/h | 150x150 | ÇF-200, 35 Pa |

- Algılanan sonuç kullanıcının çizimindeki aspiratör yerleriyle örtüşüyor: katta 3 aspiratör, 1. katta ek wc-duş.
- Ş4'te 1. kat 80 m³/h çıktı, çünkü mimar D6'daki wc-lvb. hacmini "yüklük" yazmış.
- Pencereli sayılanlar: zemin ve 2. kat sol duş, 1. kat wc-duş (60/60 pencereli).

## Sınırlar
- Pencere tespiti mimarın ölçü yazısına dayanır; yazısız pencere bulunmaz. Dışa bakan ama penceresiz duvar doğru biçimde penceresiz sayılır.
- 1. kat wc-duş "D5" etiketlendi; büyük olasılıkla D6'ya aittir (mutfak yakınlığı kuralının zayıflığı). Daire etiketi elle kontrol edilmeli.
- İzometri şematiktir: branş boyu ve flex sabit uzunlukta çizilir (gerçek boy tabloda), branş kat yüksekliği - 60 cm'de gösterilir.
- Aynı şaft ve katta ikiden fazla aspiratör olursa üçüncüsü 70 cm aşağıya kaydırılır. Bu durum denenmedi.
- ζ değerleri, flex boyu ve fan eğrileri varsayımdır; yangın damperi yalnız notta yer alır, çizilmez.
- Kat planlarına "mek. havl." yazısı ve aspiratör etiketi eklenmez. Yalnız izometri paftası üretilir (DWG, PDF ve Excel yok; deneme kuralı).

## R2 revizyonu (14.10.2026 (B) talimatı)
- `mtylib` / `radyator` importu ve `MTY-ÇATI TİPİ FAN` bloğu kaldırıldı; pafta tamamen saf geometri.
- Lejant otomatik: `Cizim.adet()` izometri çizilirken şaft, Ø150 branş, geri akış klapesi, flex, aspiratör ve çatı fanını sayar;
  lejant yalnız sayılan öğeleri ADET sütunuyla gösterir (planda kullanılmayan plan-fan sembolü artık lejantta yok).
- `calistir.py` sonunda `mty_kontrol()`; çıktılar `*_R2.dxf` (ORNEK_Z2_9DAIRE ve NB). Yazı çakışması 0, MTY 0. Elektrik kalemi çizilmez.
