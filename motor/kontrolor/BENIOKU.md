# kontrolor — KONTROLÖR (onay) sistemi

```
python3 motor/kontrolor/kontrolor.py <dxf> --mimari ornekler/new_block.dxf.xz --rapor <rapor.md> [--png-ust 12] [--png-yok]
        [--pencere '{"Z":[x0,y0,x1,y1],...}'] [--katman AD,AD] [--referans-yok] [--referans-kaydet]
```
Çıktı: `<rapor>.md` (SONUÇ: ONAY / RED + düzeltme listesi, özet tablo, ayrıntı, eşikler) + `<rapor>_png/`
(her FAIL için `Tnn_kat_nn.png`: kontrol edilen | referans new_block yan yana, bulgu sarı halka; `GENEL_KAT_*.png`,
`GENEL_SEMA.png`). R4 örneği: `kutuphane/arastirma/KONTROLOR_R4_RAPORU.md`. Protokol: `onay_protokolu.md`.
Süre: R4 (3 kat + şema) ~15 s ölçüm, PNG'lerle ~80 s.

## Dosyalar
| Dosya | Ne yapar |
|---|---|
| `kontrolor.py` | CLI, kat eşleme, test çalıştırma, PNG, rapor |
| `mimari_bilgi.py` | mimari tanıma: `uctan_uca/mimari.py` (mahal poligonu `rooms.detect`, ıslak hacim, armatür imzaları, betonarme) + daire grupları (daire no yazıları tohum, duvar rasterinde yürüme mesafesi `MCP_Geometric`, ulaşılamayan mahal komşuluktan), ortak alan, koridor, balkon, mimarın yağmur inişi (eş merkezli çift daire) |
| `cizim.py` | kontrol edilen DXF: çerçeveler, kat paftaları (başlık "ZEMİN KAT ... PLANI"), şema paftası ("KOLON ŞEMASI"), katman sınıfları (`denetle.boru_katmani` üstüne pis/sıcak/soğuk/yağmur), semboller (SUZGEC, PIS-SU-KOLON, KOLON-NO, SAYAC, yağmur daireleri), etiketler (çap blok öznitelikleri + etiket katmanı yazıları), mimari yazılar; **kat eşleme**: kaynak kat penceresi yazıları ↔ pafta yazıları metin eşitliğiyle öteleme kipi (R4: 77-78 eşleşme) |
| `testler.py` | T01–T11 (aşağıda) ve eşikler (üst blok) |
| `kirp.py` | ezdxf drawing + matplotlib ile pencere kırpımı (siyah zemin), PIL yan yana |
| `referans_new_block.json` | aynı testlerin kullanıcının kendi `new_block.dxf` çiziminde verdiği sayılar (raporda "Referans" sütunu); `--referans-kaydet` ile yenilenir |

## Testler
| Test | Ölçüm | FAIL eşiği |
|---|---|---|
| T01 | balkon süzgeci (balkon poligonunda SUZGEC sembolü) → bağlı ağ: pis su katmanı/kolonu var mı; yağmur inişine (yağmur dairesi / YB balonu / mimarın çift dairesi) yol boyu | pis suya bağlı; inişe ulaşmıyor; yol > 300 cm; balkon içinden pis su hattı |
| T02 | pis su ağı (graf): her parça açısı; her armatür (mimari imza) → en yakın kolon yolu | açı {0,45,90} ± 4° dışı (≥ 25 cm parça); yol > 300 cm; yol armatür+kolon mahalleri (+30 cm) dışında > 40 cm; WC/LV/DUŞ/EVİYE 50 cm içinde hat yok |
| T03 | pis su hattının mahal iç bölgesinde (poligon −30 cm) kalan boyu; 0/90 dışı tek parça boyu | iç bölge ≥ 100 cm (30–100 BİLGİ; referansta en çok 97); eğik parça ≥ 150 cm |
| T04 | sıcak su bağlı ağı: en çok örtüştüğü daire; ortak alan (−10) ∪ başka daire (balkonsuz, −45) ∪ bina dışı (+100) içindeki boyu; kombiye yakınlık | > 15 cm; kombiye 80 cm içinde başlamıyor |
| T05 | sıcak ↔ soğuk kesişme; sıcak parçası (≥ 60) boyunca soğuğa mesafe | kesişme (uçtan 15 cm / armatüre 60 cm / köşe yan değiştirme hariç → köşe BİLGİ); eşlenen (3–30 cm) oran < %80; ofset std > 6 |
| T06 | koridor (antre-kor./merdiven/hol) içindeki temiz su parçasının duvara oranı | **yalnız BİLGİ**: kullanıcının kendi çiziminde antre hatları duvar dibinde, B kuralı "koridor ortası" — karar kullanıcıda |
| T07 | etiket (çap blok öznitelikleri, CIHAZ/KOLONNO/HAVALANDIRMA-YAZI/YAZI katmanı) kutuları (ezdxf yazı ölçüsü) | etiket–etiket örtüşme > 0,2 cm² (aynı bloğun kendi öznitelikleri hariç); etiket–mimari yazı örtüşme; hat yazı kutusundan ≥ 8 cm geçiyor; çap etiketi yüksekliği ortanca 8–12 dışı |
| T08 | şema paftası: ZEMİN KAT / n. KAT yazılarından bantlar; SAYAC sembolleri; D1.. daire etiketleri | sayaç y ≥ 1. kat çizgisi; sayaç x daire bloklarının solunda değil; "SAYAÇ ... KAPI" yazısı; zemin solunda sayaç yok |
| T09 | ıslak mahal poligonunda süzgeç sembolü (çizim SUZGEC blokları + mimari ızgara, 15 cm kümeli) | ≠ 1; süzgeç kuru mahalde |
| T10 | PIS-SU-KOLON sembolü: ıslak mahal (+40 cm) içinde mi, betonarme içinde mi, en yakın köşe | dışında / betonarme / köşe > 45 cm |
| T11 | `denetle.denetle()` | MTY, önek, köprü, kesişme, elektrik, yazı (%2), lejant, audit, "yetersiz" |

## Doğrulama (14.10.2026)
- **R4** (`proje/denemeler/_arsiv/uctan_uca/NB_SIHHI_DENEME_R4.dxf`): RED 237 madde. Kullanıcının 4 RED görüntüsündeki
  hata türlerinin tamamı yakalandı: balkon süzgeci → P9 (T01 ×3 kat), sayaç kat bandında/daire bloğunda (T08 ×17),
  sıcak su merdiven holünden (T04 daire 6: 716 cm, ortak alanda 384 cm; daire 9), wc-banyo çapraz uzun pis su (T03),
  etiket hat üstüne (T07 ×180). Rapor: `kutuphane/arastirma/KONTROLOR_R4_RAPORU.md`.
- **R3** (RED görüntülerinin 4.'sü R3'ten): etiket–etiket 91, etiket–mimari yazı 59, etiket–hat 131 (1. kat) → yakalanıyor.
- **new_block (referans, kullanıcının çizimi)**: T01/T03/T05/T06/T08/T10 geçer; T02 59 (serbest açılı branşman — kural C
  45° ister), T04 1 (daire ataması sınırı), T07 175 (kullanıcının etiketleri de başka hatların üstünden geçiyor),
  T09 16 (mutfak/wc-lvb.'de süzgeç yok — B kuralı ister), T11 34 (MTY, beklenen). Bu sayılar raporda "Referans" sütunu.

## Sınırlar
- Mahal tanıma kural tabanlı (`mimari.py`): etiketleri ROOM_WORDS + burada eklenen adlar; başka mimaride ad listesi
  (`mimari_bilgi._etiketler`) genişletilmeli. Daire grupları daire numarası yazısı (h ≥ 15, 1–40) ister; yoksa T04 yalnız
  ortak alan/bina dışı ölçer.
- Kat eşleme yazı eşitliğiyle (en az 6 eşleşme); mimari yazıları değiştirilmiş çıktıda `oteleme_bul_cizgi` (duvar çizgisi
  histogramı) yedeği denenir.
- Armatür bağlantı noktası mimari imzadan (klozet elipsi merkezi, lavabo gideri ...) alınır; motor hattı armatürün 50 cm
  dışından başlıyorsa "bağlı değil" sayılır.
- Şema tarzı (new_block şemasına benzerlik) ölçülmez; kontrolör GENEL_SEMA.png'yi `ornekler/new_block_onizleme/` ile
  göz ile karşılaştırır (protokol §2-3).
- T07 yazı kutuları yazı tipine bağlıdır (ezdxf ölçüsü); MTEXT mimari yazılarda karakter tahmini.
