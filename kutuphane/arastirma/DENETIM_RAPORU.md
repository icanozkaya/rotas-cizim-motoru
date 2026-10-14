# Deneme çıktıları denetim raporu

Üretildi: 14.10.2026 17:58 — `python3 motor/deneme/denetim/denetle.py `

Kurallar: README en üst blok (14.10.2026 B): MTY bloğu/kalıntısı yok, katmanlar `ROTAS-`, boru atlatma (köprü) yok, elektrik kalemi yok, lejant zorunlu, "yetersiz" yazılmaz. Onaylı kazan dairesi için MTY istisnası **yok**; onaylı çizimdeki köprü/kesişmeler yalnız bilgi olarak verilir.

**Sütunlar:** MTY = MTY kalıntısı toplamı (blok adı + blok içi katman + katman + çizgi tipi + yazı stili + blok ekleme + yazı); Önek = 0/Defpoints dışında ROTAS- olmayan katman; Köprü = boru katmanında atlatma yayı; Kesişme = köprüsüz boru-boru kesişmesi (pis su-temiz su hariç); Yazı = yazı-yazı çakışan çift; Pis/temiz (bilgi) = farklı düzlemdeki pis su-temiz su üst üste geçişi; Elek = elektrik/kablo/sinyal katmanındaki nesne + KABLO yazısı; Audit = ezdxf audit hatası; Yetersiz = "yetersiz/uygun değil" yazısı.

## En yeni revizyonlar (26 dosya: 23 ✓, 3 ✗)

| Dosya | Rev | Sonuç | MTY | Önek | Lejant | Köprü | Kesişme | Yazı | Elek | Audit | Yetersiz | Pis/temiz (bilgi) | Onaylı (bilgi) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proje/denemeler/dogalgaz/test_z4_10daire_izometrik_kolon_semasi_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/kanal/ofis_kanal_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/kanal/otopark_jetfan_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_PLAN_KESIT_R2.dxf | R2 | ✗ | 0 | 0 | ✓ | 0 | 0 | 1 | 0 | 0 | 0 |  | dosya: köprü 34, kesişme 0 |
| proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_SEMA_R3.dxf | R3 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/kazan_dairesi/KUCUK_2x110_KAZAN_DAIRESI_PLAN_KESIT_R2.dxf | R2 | ✗ | 0 | 0 | ✓ | 0 | 0 | 1 | 0 | 0 | 0 |  | dosya: köprü 10, kesişme 0 |
| proje/denemeler/kazan_dairesi/KUCUK_2x110_KAZAN_DAIRESI_SEMA_R3.dxf | R3 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/pafta_bitir/KAPAK_SIHHI_DENEME.dxf | R1 | ✓ | 0 | 0 | - (kapak) | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/pafta_bitir/NB_SIHHI_BITMIS_DENEME_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 | 80 |  |
| proje/denemeler/pompa_grubu/HIDROFOR_GRUBU_KESITI_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/pompa_grubu/PIS_SU_POMPA_CUKURU_KESITI_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/pompa_grubu/YANGIN_POMPA_GRUBU_KESITI_OFIS_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/pompa_grubu/YANGIN_POMPA_GRUBU_KESITI_OTOPARK_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/radyator/radyator_kombi_R3.dxf | R3 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/radyator/radyator_merkezi_R4.dxf | R4 | ✗ | 0 | 0 | ✓ | 0 | 0 | 1 | 0 | 0 | 0 |  | bölge x1: köprü 10, kesişme 0 |
| proje/denemeler/semboller2/OTOMATIK_LEJANT_DENEME_V2.dxf | R1 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/semboller2/SEMBOL_KUTUPHANESI_V2.dxf | R1 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/sprinkler/kat_ofis_dolap_kolon_semasi_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/sprinkler/kat_ofis_dolap_plan_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/sprinkler/kat_ofis_oh1_sprinkler_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/sprinkler/otopark_dolap_kolon_semasi_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/sprinkler/otopark_dolap_plan_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/sprinkler/otopark_oh2_sprinkler_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R4.dxf | R4 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 | 80 |  |
| proje/denemeler/wc_havalandirma/NB_WC_HAVALANDIRMA_DENEME_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |
| proje/denemeler/wc_havalandirma/ORNEK_Z2_9DAIRE_WC_HAVALANDIRMA_R2.dxf | R2 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |  |

## Eski revizyonlar (bilgi; yerini daha yeni R almış)

_(yok)_

## Ayrıntı — en yeni revizyonlar

- **proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_PLAN_KESIT_R2.dxf**
  - yazı çakışması: ROTAS-ISITMA-ETIKET "V-10" / ROTAS-ISITMA-ETIKET "V-21" (180, -611)
  - ONAYLI kazan dairesi (dosya): köprü 34, kesişme 0 — bilgi, hata sayılmadı

- **proje/denemeler/kazan_dairesi/KUCUK_2x110_KAZAN_DAIRESI_PLAN_KESIT_R2.dxf**
  - yazı çakışması: ROTAS-ISITMA-ETIKET "V-10" / ROTAS-ISITMA-ETIKET "V-21" (180, -611)
  - ONAYLI kazan dairesi (dosya): köprü 10, kesişme 0 — bilgi, hata sayılmadı

- **proje/denemeler/pafta_bitir/NB_SIHHI_BITMIS_DENEME_R2.dxf**
  - pis su / temiz su farklı düzlem üst üste geçiş (bilgi, hata değil): 80 — örn. (8476, 1366), (8486, 1356), (8322, 1906)
  - mimari altlığın kendi yazı çakışması (bilgi, mimar çizimi değiştirilmez): 144

- **proje/denemeler/radyator/radyator_merkezi_R4.dxf**
  - yazı çakışması: ROTAS-ISITMA-ETIKET "V-19" / ROTAS-ISITMA-ETIKET "V-24" (11186, -2311)
  - ONAYLI kazan dairesi (bölge x1): köprü 10, kesişme 0 — bilgi, hata sayılmadı

- **proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R4.dxf**
  - pis su / temiz su farklı düzlem üst üste geçiş (bilgi, hata değil): 80 — örn. (8476, 1366), (8486, 1356), (8322, 1906)
  - mimari altlığın kendi yazı çakışması (bilgi, mimar çizimi değiştirilmez): 144


## Sınırlar

- Boru katmanı katman adından seçilir (BORU, KANAL, SICAK, SOGUK, PIS, YAGMUR, GIDIS/DONUS, YANGIN, DOGALGAZ, SIHHI...; CAP/YAZI/SEMBOL/CIHAZ/MIMARI vb. hariç). Kesişme yalnız model alanında, uç noktalardan 15 cm içerideki geçişler (T bağlantısı, kanal ağzına giren flex vb. sayılmaz).
- Köprü: boru katmanında ARC (≥150°, r≤40 cm) veya LWPOLYLINE kavis segmenti (|bulge|≥0,8, kiriş≤80 cm). Köprü noktasına 45 cm içindeki kesişmeler kesişme sütununda tekrar sayılmaz.
- Yazı kutuları ezdxf yazı tipi ölçüsüyle (ölçülemezse 0,8·h·karakter); kesişim > küçük kutunun %2'si çakışma. Aynı INSERT'in öznitelikleri ve mimari-mimari çiftleri sayılmaz (uctan_uca ykontrol4 ile ortak kural).
- Pis su ile temiz su farklı düzlemdedir: üst üste geçişleri kesişme sayılmaz, "Pis/temiz (bilgi)" sütununda verilir.
- Dosya adında KAPAK geçen pafta lejant kontrolünden muaftır. Varsayılan taramada `_arsiv` atlanır.
- Onaylı bölge: `*KAZAN_DAIRESI_PLAN_KESIT*` dosyaları tamamen; diğer dosyalarda XDATA `ROTAS: ONAYLI_KAZAN_DAIRESI` çerçevesinin içi.
