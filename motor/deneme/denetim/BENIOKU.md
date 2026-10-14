# denetim — deneme çıktılarını tek komutla denetleme

```
python3 motor/deneme/denetim/denetle.py [dosya_veya_klasor ...]     # varsayılan: proje/denemeler/
    --ayrinti        konsola dosya bazında ayrıntı da yaz
    --rapor YOL      rapor yolu (varsayılan kutuphane/arastirma/DENETIM_RAPORU.md)
    --rapor-yok      rapor yazma
```
Çıktı: konsol tablosu + `kutuphane/arastirma/DENETIM_RAPORU.md` (dosya bazında ✓/✗, sayılar, ayrıntı örnek koordinatları).
29 + 18 dosya ~16 s.

## Kontroller (her DXF)
| Sütun | Ne sayılır |
|---|---|
| MTY | MTY kalıntısı: adında MTY geçen blok tanımı, blok içi MTY katmanlı nesne, katman tablosu, çizgi tipi, yazı stili, MTY blok eklemesi, içinde "MTY" geçen yazı (TEXT/MTEXT/ATTRIB/ATTDEF) |
| Önek | `0` ve `Defpoints` dışında `ROTAS-` ile başlamayan katman |
| Lejant | herhangi bir yazıda "LEJANT" var mı |
| Köprü | boru katmanında atlatma yayı: ARC (≥150°, r≤40 cm) veya LWPOLYLINE kavis segmenti (\|bulge\|≥0,8, kiriş≤80 cm) |
| Kesişme | köprüsüz boru-boru kesişmesi (shapely; uçtan 15 cm içindeki geçişler bağlantı sayılır; köprüye 45 cm yakın olanlar Köprü'de) |
| Yazı | yazı-yazı çakışması (tahmini yazı kutusu 0,8·h·karakter; küçük kutunun ≥%15 örtüşmesi) |
| Elek | ELEKTRIK/KABLO/SINYAL katmanındaki nesne + "KABLO" geçen yazı |
| Audit | `doc.audit()` hata sayısı |
| Yetersiz | "yetersiz" / "uygun değil" geçen yazı |

Boru katmanı adından seçilir (BORU, KANAL, SICAK, SOGUK, PIS, YAGMUR, GIDIS/DONUS, PEX, FLEX, YANGIN, DOGALGAZ, SIHHI ...;
CAP, YAZI, SEMBOL, CIHAZ, MIMARI, VANA, SPRINKLER (başlık) vb. hariç; ad BORU içeriyorsa geri alınır) — `boru_katmani()`.

## Revizyonlar
`AD_R<n>.dxf` → taban `AD`, revizyon n (soneksiz = R1). Her tabanın en büyük R'si "en yeni" bölümünde, diğerleri "eski".
Soneksiz R1 dosyasının adıyla başlayan bir R2+ türevi aynı klasörde varsa (ör. `YANGIN_POMPA_GRUBU_KESITI.dxf` →
`..._OFIS_R2.dxf`) R1 eski sayılır.

## Onaylı kazan dairesi
İstisna YOK: MTY / önek / yazı vb. onaylı paftada da hata sayılır. Yalnız köprü ve boru kesişmesi onaylı bölgede
"Onaylı (bilgi)" sütununa yazılır, ✗ yapmaz. Onaylı bölge: `*KAZAN_DAIRESI_PLAN_KESIT*` dosyaları tamamen, diğer
dosyalarda XDATA `ROTAS: ONAYLI_KAZAN_DAIRESI` olan çerçeve (`plan_kesit.onayli_kazan_dairesi`) içi.

## Sınırlar
- Yazı kutuları font ölçülmeden tahmin edilir; dar/geniş fontlarda az/çok sayabilir.
- "KABLO" ve "uygun değil" metin eşleşmesidir: "elektrik projesindedir" notu veya şartname cümlesi de sayılır (ayrıntıda
  bağlamıyla gösterilir, karar kullanıcıda).
- "MTY" yazı kontrolü açıklama notlarını da yakalar (ör. "MTY bloğu yok").
- Yalnız model alanı geometrisi (kesişme/köprü/yazı); kâğıt alanı denetlenmez.
