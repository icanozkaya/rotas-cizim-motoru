# denetim — deneme çıktılarını tek komutla denetleme

```
python3 motor/deneme/denetim/denetle.py [dosya_veya_klasor ...]     # varsayılan: proje/denemeler/ (_arsiv hariç)
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
| Lejant | herhangi bir yazıda "LEJANT" var mı. **Kapak istisnası:** dosya adında KAPAK geçen paftada lejant aranmaz (sütunda `- (kapak)`), diğer kontroller geçerli |
| Köprü | boru katmanında atlatma yayı: ARC (≥150°, r≤40 cm) veya LWPOLYLINE kavis segmenti (\|bulge\|≥0,8, kiriş≤80 cm) |
| Kesişme | köprüsüz boru-boru kesişmesi (shapely; uçtan 15 cm içindeki geçişler bağlantı sayılır; köprüye 45 cm yakın olanlar Köprü'de). **Pis su – temiz su** (PIS katmanı ile SOGUK/SICAK/SIRKULASYON/TEMIZ/SEBEKE katmanı) farklı düzlemdedir: kesişme sayılmaz, `Pis/temiz (bilgi)` sütununa yazılır (✗ yapmaz). Yağmur hattı bu istisnada değildir |
| Yazı | yazı-yazı çakışması: TEXT / MTEXT / görünür ATTRIB, kutu **ezdxf yazı tipi ölçüsüyle** (`disassemble.make_primitive`; ölçülemezse 0,8·h·karakter tahmini), kesişim > küçük kutunun %2'si. Sayılmaz: aynı INSERT'in kendi öznitelikleri; iki yazı da MİMARİ katmanında (mimar altlığı — ayrıntıda bilgi olarak) |
| Pis/temiz (bilgi) | pis su – temiz su üst üste geçiş sayısı (bilgi) |
| Elek | ELEKTRIK/KABLO/SINYAL katmanındaki nesne + "KABLO" geçen yazı |
| Audit | `doc.audit()` hata sayısı |
| Yetersiz | "yetersiz" / "uygun değil" geçen yazı |

Boru katmanı adından seçilir (BORU, KANAL, SICAK, SOGUK, PIS, YAGMUR, GIDIS/DONUS, PEX, FLEX, YANGIN, DOGALGAZ, SIHHI ...;
CAP, YAZI, SEMBOL, CIHAZ, MIMARI, VANA, SPRINKLER (başlık) vb. hariç; ad BORU içeriyorsa geri alınır) — `boru_katmani()`.

## Ortak kural (uctan_uca ile aynı sayı)
`yazi_cakismalari(msp)` ve `boru_kesismeleri(doc)` fonksiyonları ortaktır: `motor/deneme/uctan_uca/ykontrol4.py` yazı
kontrolünü doğrudan `denetle.yazi_cakismalari` ile yapar, `cikti4.son_islem` özetine (`ozet_r4.json` → `kontrol.boru_kesisme`)
`denetle.boru_kesismeleri` sonucunu yazar. Böylece iki araç aynı sayıyı verir. (14.10.2026 öncesi fark: denetim 0,8·h·karakter
tahmini kutu + %15 eşikle mimari-mimari ve tahmin taşması dahil 60 yazı, pis su-temiz su geçişleriyle 80 kesişme sayıyordu;
ykontrol4 ölçülü kutu + mimari hariç 0 diyordu. 20 "yazı" çakışmasının hiçbiri ölçülü kutuda örtüşmüyordu, 40'ı mimar
altlığının kendi yazılarıydı; 80 kesişmenin tamamı pis su / tavandan pis su ile temiz su arasındaydı.)

## Revizyonlar
`AD_R<n>.dxf` → taban `AD`, revizyon n (soneksiz = R1). Her tabanın en büyük R'si "en yeni" bölümünde, diğerleri "eski".
Soneksiz R1 dosyasının adıyla başlayan bir R2+ türevi aynı klasörde varsa (ör. `YANGIN_POMPA_GRUBU_KESITI.dxf` →
`..._OFIS_R2.dxf`) R1 eski sayılır.

## Onaylı kazan dairesi
İstisna YOK: MTY / önek / yazı vb. onaylı paftada da hata sayılır. Yalnız köprü ve boru kesişmesi onaylı bölgede
"Onaylı (bilgi)" sütununa yazılır, ✗ yapmaz. Onaylı bölge: `*KAZAN_DAIRESI_PLAN_KESIT*` dosyaları tamamen, diğer
dosyalarda XDATA `ROTAS: ONAYLI_KAZAN_DAIRESI` olan çerçeve (`plan_kesit.onayli_kazan_dairesi`) içi.

## Sınırlar
- Yazı kutuları ezdxf'in yazı tipi ölçüsüyle; yazı tipi bulunamazsa ezdxf'in yedek fontu / tahmin kullanılır.
- %2 eşik sıkıdır: maskeleri birbirine değen numaralar da sayılır (ör. onaylı kazan dairesi `V-10` / `V-21`, radyatör merkezi `V-19` / `V-24`).
- "KABLO" ve "uygun değil" metin eşleşmesidir: "elektrik projesindedir" notu veya şartname cümlesi de sayılır (ayrıntıda
  bağlamıyla gösterilir, karar kullanıcıda).
- "MTY" yazı kontrolü açıklama notlarını da yakalar (ör. "MTY bloğu yok").
- Yalnız model alanı geometrisi (kesişme/köprü/yazı); kâğıt alanı denetlenmez.
