# Deneme çıktıları denetim raporu

Üretildi: 15.10.2026 05:00 — `python3 motor/deneme/denetim/denetle.py proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf`

Kurallar: README en üst blok (14.10.2026 B): MTY bloğu/kalıntısı yok, katmanlar `ROTAS-`, boru atlatma (köprü) yok, elektrik kalemi yok, lejant zorunlu, "yetersiz" yazılmaz. Onaylı kazan dairesi için MTY istisnası **yok**; onaylı çizimdeki köprü/kesişmeler yalnız bilgi olarak verilir.

**Sütunlar:** MTY = MTY kalıntısı toplamı (blok adı + blok içi katman + katman + çizgi tipi + yazı stili + blok ekleme + yazı); Önek = 0/Defpoints dışında ROTAS- olmayan katman; Köprü = boru katmanında atlatma yayı; Kesişme = köprüsüz boru-boru kesişmesi (pis su-temiz su hariç); Yazı = yazı-yazı çakışan çift; Pis/temiz (bilgi) = farklı düzlemdeki pis su-temiz su üst üste geçişi; Elek = elektrik/kablo/sinyal katmanındaki nesne + KABLO yazısı; Audit = ezdxf audit hatası; Yetersiz = "yetersiz/uygun değil" yazısı.

## En yeni revizyonlar (1 dosya: 1 ✓, 0 ✗)

| Dosya | Rev | Sonuç | MTY | Önek | Lejant | Köprü | Kesişme | Yazı | Elek | Audit | Yetersiz | Pis/temiz (bilgi) | Onaylı (bilgi) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf | R1 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |

## Eski revizyonlar (bilgi; yerini daha yeni R almış)

_(yok)_

## Ayrıntı — en yeni revizyonlar

- **proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf**
  - mimari altlığın kendi yazı çakışması (bilgi, mimar çizimi değiştirilmez): 111


## Sınırlar

- Boru katmanı katman adından seçilir (BORU, KANAL, SICAK, SOGUK, PIS, YAGMUR, GIDIS/DONUS, YANGIN, DOGALGAZ, SIHHI...; CAP/YAZI/SEMBOL/CIHAZ/MIMARI vb. hariç). Kesişme yalnız model alanında, uç noktalardan 15 cm içerideki geçişler (T bağlantısı, kanal ağzına giren flex vb. sayılmaz).
- Köprü: boru katmanında ARC (≥150°, r≤40 cm) veya LWPOLYLINE kavis segmenti (|bulge|≥0,8, kiriş≤80 cm). Köprü noktasına 45 cm içindeki kesişmeler kesişme sütununda tekrar sayılmaz.
- Yazı kutuları ezdxf yazı tipi ölçüsüyle (ölçülemezse 0,8·h·karakter); kesişim > küçük kutunun %2'si çakışma. Aynı INSERT'in öznitelikleri ve mimari-mimari çiftleri sayılmaz (uctan_uca ykontrol4 ile ortak kural).
- Pis su ile temiz su farklı düzlemdedir: üst üste geçişleri kesişme sayılmaz, "Pis/temiz (bilgi)" sütununda verilir.
- Dosya adında KAPAK geçen pafta lejant kontrolünden muaftır. Varsayılan taramada `_arsiv` atlanır.
- Onaylı bölge: `*KAZAN_DAIRESI_PLAN_KESIT*` dosyaları tamamen; diğer dosyalarda XDATA `ROTAS: ONAYLI_KAZAN_DAIRESI` çerçevesinin içi.
