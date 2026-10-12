# Örnek mekanik proje kütüphanesi

Kullanıcının referans olarak gönderdiği iki ticari mekanik proje setinin arşivi. Buradaki dosyalar **çizim yapmak için değil**, lejant, şema, pafta düzeni, boru çapı yazım biçimi ve hesap değerlerine başvurmak için tutuluyor. Orijinal DWG'ler değiştirilmeden saklanır. Önizlemeler ve metin dökümleri bu DWG'lerden otomatik olarak üretildi (LibreDWG → DXF → düzleştirme → matplotlib).

| Set | İçerik | Ayrıntı |
|---|---|---|
| `aselsan_teknopark/` | ASELSAN Akyurt-1 OPAK Binası (Ana Bina) uygulama projesi. 8 DWG: 01 ısıtma-soğutma, 02 yangın, 03 azot ve basınçlı hava, 04 pis su ve yağmur suyu, 05 temiz su, 06 havalandırma, 07 vinç, 08 XREF mimari altlık. Bunlara ek olarak opak cihaz listesi (25 sayfalık XLS). | [KATALOG.md](aselsan_teknopark/KATALOG.md) |
| `ada_hayat/` | Ada Hayat AVM ve Belediye binası (Adapazarı, GÖK-AY Proje). 11 DWG: ısıtma-soğutma planları, havalandırma planları, 8 kolon şeması ve 1 akım şeması. Bunlara ek olarak 7 metraj ve icmal XLS'i, mekanik pafta listesi, teknik şartname (DOC) ve CTB dosyaları. | [KATALOG.md](ada_hayat/KATALOG.md) |

## Klasör yapısı (her iki sette aynı)

```
<set>/
  KATALOG.md       dosya listesi, pafta başlıkları, katman/blok listeleri, lejant satırları,
                   şema özetleri, önemli hesap değerleri, boru çapı yazım biçimi
  dwg/             orijinal DWG'ler (okunur Türkçe adla; hepsi 95 MB altında, sıkıştırma yok)
  belge/           orijinal XLS/DOC/CTB (+ DOC'lardan çıkarılmış *_metin.txt)
  onizleme/        <dosya>_<n>.png: her pafta ya da çerçeve dışı içerik grubu (≤3000 px)
  lejant/          <dosya>_lejant_<n>.png + .txt: sembol tabloları ve satır adları
  sema/            <dosya>_sema_<n>.png: kolon/akım şeması, izometri içeren paftalar (≤4000 px)
  hesap/           XLS sayfalarının CSV dökümü (UTF-8 BOM) + <dosya>_notlar.txt (DWG içi not/hesap metinleri)
```

## Öne çıkan bilgiler

- **Sprinkler boru çapı ile beslenen başlık sayısı** (Aselsan 02, `-M-YNGN-BORUYUK`):

  | Boru | Başlık sayısı |
  |---|---|
  | DN25 | 1–2 |
  | DN32 | 3 |
  | DN40 | 4–5 |
  | DN50 | 6–10 |
  | DN65 | 11–20 |
  | DN80 | 21–40 |
  | DN100 | 41–100 |
  | DN150 | 100 üstü |

  Ada Hayat'ta kat zonu besleme çapları: DN80 en çok 58 sprinkler, DN100 41–98, DN125 114, DN150 180–275, DN200 279 ve üstü. Ayrıntılar iki KATALOG.md dosyasında da var.
- **Pafta düzeni farkı:**
  - Aselsan'da paftalar yatay bir ozalit şeridi halinde dizilmiş. Şerit yüksekliği 9000, antet sağ uçta dikey bir sütun.
  - Ada Hayat'ta paftalar ayrı ayrı 25000×20000 çerçeve içinde (`UP_ANTET_01`). Sağda 2500 genişliğinde antet sütunu var. Numaralar disipline göre seri halinde: 100 temiz su, 200 pis su, 300 ısıtma-soğutma, 400 havalandırma, 500 yangın.
- **Ada Hayat plan DWG'leri:** Bütün disiplinlerin katmanları aynı dosyada duruyor; ilgisiz olanlar dondurulmuş. Temiz su, pis su ve yangın kat planlarının DWG'si sette yok.

## Bilinen sınırlamalar

- Önizlemelerde tarama (hatch), çizgi tipi ve yazı hizalaması yok. Yazılar sola hizalı basitleştirilmiş biçimde gösteriliyor. Kapalı ya da dondurulmuş katmanlar gizlendi. Mimari oda adı gibi çok büyük yazılar (pafta medyanının 3 katından büyük olanlar) önizlemede gösterilmedi.
- Paftalar otomatik ayrıldı: önce antet/başlık katmanındaki dikdörtgen çerçeveler bulundu, çerçeve dışında kalan içerik ise boşluk kümelemesiyle "serbest grup" olarak ayrıldı. Bu yüzden bazı küçük serbest gruplar yalnızca birkaç sembolden oluşuyor (ör. Aselsan 07 Vinç'teki "BEKET 105" grupları).
- Lejant bölgeleri de otomatik bulundu: başlığın altındaki metin satırları izlendi ya da başlığı çevreleyen çerçeve kullanıldı. Bu yüzden bazı lejant .txt dosyalarına komşu detay metinleri de karışmış olabilir.
