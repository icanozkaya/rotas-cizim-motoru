# Deneme çıktıları denetim raporu

Üretildi: 14.10.2026 17:01 — `python3 motor/deneme/denetim/denetle.py `

Kurallar: README en üst blok (14.10.2026 B): MTY bloğu/kalıntısı yok, katmanlar `ROTAS-`, boru atlatma (köprü) yok, elektrik kalemi yok, lejant zorunlu, "yetersiz" yazılmaz. Onaylı kazan dairesi için MTY istisnası **yok**; onaylı çizimdeki köprü/kesişmeler yalnız bilgi olarak verilir.

**Sütunlar:** MTY = MTY kalıntısı toplamı (blok adı + blok içi katman + katman + çizgi tipi + yazı stili + blok ekleme + yazı); Önek = 0/Defpoints dışında ROTAS- olmayan katman; Köprü = boru katmanında atlatma yayı; Kesişme = köprüsüz boru-boru kesişmesi; Yazı = yazı-yazı çakışan çift; Elek = elektrik/kablo/sinyal katmanındaki nesne + KABLO yazısı; Audit = ezdxf audit hatası; Yetersiz = "yetersiz/uygun değil" yazısı.

## En yeni revizyonlar (28 dosya: 3 ✓, 25 ✗)

| Dosya | Rev | Sonuç | MTY | Önek | Lejant | Köprü | Kesişme | Yazı | Elek | Audit | Yetersiz | Onaylı (bilgi) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proje/denemeler/dogalgaz/test_z4_10daire_izometrik_kolon_semasi_R2.dxf | R2 (en yeni) | ✗ | 0 | 0 | ✓ | 0 | 0 | 1 | 0 | 0 | 0 |  |
| proje/denemeler/kanal/ofis_kanal.dxf | R1 | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/kanal/otopark_jetfan.dxf | R1 | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_PLAN_KESIT.dxf | R1 | ✗ | 601 | 4 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 | dosya: köprü 34, kesişme 0 |
| proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_SEMA_R2.dxf | R2 (en yeni) | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/kazan_dairesi/KUCUK_2x110_KAZAN_DAIRESI_PLAN_KESIT.dxf | R1 | ✗ | 575 | 4 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 | dosya: köprü 10, kesişme 0 |
| proje/denemeler/kazan_dairesi/KUCUK_2x110_KAZAN_DAIRESI_SEMA_R2.dxf | R2 (en yeni) | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/pafta_bitir/KAPAK_SIHHI_DENEME.dxf | R1 | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/pafta_bitir/NB_SIHHI_BITMIS_DENEME.dxf | R1 | ✗ | 6104 | 37 | ✓ | 0 | 99 | 93 | 0 | 0 | 1 |  |
| proje/denemeler/pompa_grubu/HIDROFOR_GRUBU_KESITI_R2.dxf | R2 (en yeni) | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/pompa_grubu/PIS_SU_POMPA_CUKURU_KESITI_R2.dxf | R2 (en yeni) | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/pompa_grubu/YANGIN_POMPA_GRUBU_KESITI_OFIS_R2.dxf | R2 | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 1 | 0 | 0 |  |
| proje/denemeler/pompa_grubu/YANGIN_POMPA_GRUBU_KESITI_OTOPARK_R2.dxf | R2 | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 1 | 0 | 0 |  |
| proje/denemeler/radyator/radyator_kombi_R3.dxf | R3 (en yeni) | ✗ | 0 | 0 | ✓ | 0 | 0 | 2 | 0 | 0 | 0 |  |
| proje/denemeler/radyator/radyator_merkezi_R4.dxf | R4 (en yeni) | ✗ | 304 | 3 | ✓ | 0 | 0 | 2 | 1 | 0 | 0 | bölge x1: köprü 10, kesişme 0 |
| proje/denemeler/semboller/OTOMATIK_LEJANT_DENEME.dxf | R1 | ✗ | 559 | 3 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/semboller/SEMBOL_KUTUPHANESI.dxf | R1 | ✗ | 6185 | 64 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/semboller2/OTOMATIK_LEJANT_DENEME_V2.dxf | R1 | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/semboller2/SEMBOL_KUTUPHANESI_V2.dxf | R1 | ✗ | 6 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/kat_ofis_dolap_kolon_semasi_R2.dxf | R2 (en yeni) | ✗ | 0 | 0 | ✗ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/kat_ofis_dolap_plan_R2.dxf | R2 (en yeni) | ✗ | 0 | 0 | ✓ | 0 | 0 | 5 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/kat_ofis_oh1_sprinkler_R2.dxf | R2 (en yeni) | ✗ | 0 | 0 | ✓ | 0 | 0 | 5 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/otopark_dolap_kolon_semasi_R2.dxf | R2 (en yeni) | ✗ | 0 | 0 | ✗ | 0 | 0 | 3 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/otopark_dolap_plan_R2.dxf | R2 (en yeni) | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/otopark_oh2_sprinkler_R2.dxf | R2 (en yeni) | ✓ | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R3.dxf | R3 (en yeni) | ✗ | 0 | 6 | ✓ | 0 | 170 | 276 | 0 | 0 | 0 |  |
| proje/denemeler/wc_havalandirma/NB_WC_HAVALANDIRMA_DENEME.dxf | R1 | ✗ | 3 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/wc_havalandirma/ORNEK_Z2_9DAIRE_WC_HAVALANDIRMA.dxf | R1 | ✗ | 3 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |

## Eski revizyonlar (bilgi; yerini daha yeni R almış)

| Dosya | Rev | Sonuç | MTY | Önek | Lejant | Köprü | Kesişme | Yazı | Elek | Audit | Yetersiz | Onaylı (bilgi) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proje/denemeler/dogalgaz/test_z4_10daire_izometrik_kolon_semasi.dxf | R1 eski | ✗ | 132 | 2 | ✓ | 0 | 0 | 1 | 0 | 0 | 0 |  |
| proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_SEMA.dxf | R1 eski | ✗ | 566 | 2 | ✗ | 12 | 0 | 0 | 1 | 0 | 0 |  |
| proje/denemeler/kazan_dairesi/KUCUK_2x110_KAZAN_DAIRESI_SEMA.dxf | R1 eski | ✗ | 551 | 2 | ✗ | 3 | 0 | 0 | 1 | 0 | 0 |  |
| proje/denemeler/pompa_grubu/HIDROFOR_GRUBU_KESITI.dxf | R1 eski | ✗ | 125 | 1 | ✗ | 0 | 0 | 0 | 1 | 0 | 0 |  |
| proje/denemeler/pompa_grubu/PIS_SU_POMPA_CUKURU_KESITI.dxf | R1 eski | ✗ | 18 | 1 | ✗ | 0 | 0 | 0 | 7 | 0 | 0 |  |
| proje/denemeler/pompa_grubu/YANGIN_POMPA_GRUBU_KESITI.dxf | R1 eski | ✗ | 276 | 1 | ✗ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/radyator/radyator_kombi.dxf | R1 eski | ✗ | 984 | 8 | ✗ | 136 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/radyator/radyator_kombi_R2.dxf | R2 eski | ✗ | 914 | 6 | ✓ | 1 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/radyator/radyator_merkezi.dxf | R1 eski | ✗ | 1480 | 10 | ✗ | 152 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/radyator/radyator_merkezi_R2.dxf | R2 eski | ✗ | 1567 | 10 | ✓ | 20 | 0 | 0 | 22 | 0 | 0 |  |
| proje/denemeler/radyator/radyator_merkezi_R3.dxf | R3 eski | ✗ | 0 | 0 | ✓ | 0 | 0 | 2 | 1 | 0 | 0 |  |
| proje/denemeler/sprinkler/kat_ofis_dolap_kolon_semasi.dxf | R1 eski | ✗ | 73 | 2 | ✓ | 0 | 0 | 0 | 0 | 0 | 1 |  |
| proje/denemeler/sprinkler/kat_ofis_dolap_plan.dxf | R1 eski | ✗ | 44 | 1 | ✓ | 0 | 0 | 5 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/kat_ofis_oh1_sprinkler.dxf | R1 eski | ✗ | 44 | 1 | ✓ | 0 | 0 | 5 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/otopark_dolap_kolon_semasi.dxf | R1 eski | ✗ | 66 | 2 | ✓ | 0 | 0 | 2 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/otopark_dolap_plan.dxf | R1 eski | ✗ | 44 | 1 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/sprinkler/otopark_oh2_sprinkler.dxf | R1 eski | ✗ | 44 | 1 | ✓ | 0 | 0 | 0 | 0 | 0 | 0 |  |
| proje/denemeler/uctan_uca/NB_SIHHI_DENEME.dxf | R1 eski | ✗ | 6106 | 57 | ✓ | 0 | 99 | 89 | 0 | 0 | 0 |  |
| proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R2.dxf | R2 eski | ✗ | 6211 | 57 | ✓ | 0 | 137 | 116 | 0 | 0 | 0 |  |

## Ayrıntı — en yeni revizyonlar

- **proje/denemeler/dogalgaz/test_z4_10daire_izometrik_kolon_semasi_R2.dxf**
  - yazı çakışması: (2050, 2277)

- **proje/denemeler/kanal/ofis_kanal.dxf**
  - LEJANT yazısı yok

- **proje/denemeler/kanal/otopark_jetfan.dxf**
  - LEJANT yazısı yok

- **proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_PLAN_KESIT.dxf**
  - MTY blok adı 18, blok içi katman 493, katman 3, yazı stili 1, blok ekleme 86 — örn. blok adı: MTY-CEKVALF VANA, MTY-DENGE KABI PLAN, MTY-DENGE KABI ŞEMADA; blok içi katman: MTY-CIHAZ, MTY-TEFRIS, MTY-VANA; katman: MTY-CIHAZ, MTY-TEFRIS, MTY-VANA; yazı stili: MTYCAPLT
  - ROTAS- olmayan katman: MD-YUK-BIRIMI, MTY-CIHAZ, MTY-TEFRIS, MTY-VANA
  - ONAYLI kazan dairesi (dosya): köprü 34, kesişme 0 — bilgi, hata sayılmadı

- **proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_SEMA_R2.dxf**
  - LEJANT yazısı yok

- **proje/denemeler/kazan_dairesi/KUCUK_2x110_KAZAN_DAIRESI_PLAN_KESIT.dxf**
  - MTY blok adı 18, blok içi katman 493, katman 3, yazı stili 1, blok ekleme 60 — örn. blok adı: MTY-CEKVALF VANA, MTY-DENGE KABI PLAN, MTY-DENGE KABI ŞEMADA; blok içi katman: MTY-CIHAZ, MTY-TEFRIS, MTY-VANA; katman: MTY-CIHAZ, MTY-TEFRIS, MTY-VANA; yazı stili: MTYCAPLT
  - ROTAS- olmayan katman: MD-YUK-BIRIMI, MTY-CIHAZ, MTY-TEFRIS, MTY-VANA
  - ONAYLI kazan dairesi (dosya): köprü 10, kesişme 0 — bilgi, hata sayılmadı

- **proje/denemeler/kazan_dairesi/KUCUK_2x110_KAZAN_DAIRESI_SEMA_R2.dxf**
  - LEJANT yazısı yok

- **proje/denemeler/pafta_bitir/KAPAK_SIHHI_DENEME.dxf**
  - LEJANT yazısı yok

- **proje/denemeler/pafta_bitir/NB_SIHHI_BITMIS_DENEME.dxf**
  - MTY blok adı 21, blok içi katman 5466, katman 21, yazı stili 2, blok ekleme 590, yazı 4 — örn. blok adı: MTY-CEKVALF VANA, MTY-CEKVALF VANA0, MTY-GERI AKIS ONLEYICI; blok içi katman: MTY-CIHAZ, MTY-CİHAZ, MTY-CİHAZ2; katman: MTY-CIHAZ, MTY-CİHAZ, MTY-CİHAZ2; yazı stili: MTYCAPLT, MTY_CAP; yazı: *Boru YB ve çap değerleri şemadaki MTY ç, 1) Küresel vana / ventil: küresel = MTY-, 3) Çekvalf: TR lejant biçimi (MTY-CEKVAL
  - ROTAS- olmayan katman: ANTED, DETAY, IFF-VANA, MD-YUK-BIRIMI, MEP-DETAYLAR, MEP-M-TEFRİŞ, MEP-MAHAL, MEP-T-CİHAZ
  - kesişme noktaları: (6383, 1280), (8305, 1934), (7918, 2048), (8805, 1024), (8829, 1044)
  - yazı çakışması: (8516, 1232), (8513, 1228), (8340, 1912), (8942, 1415), (8944, 1411)
  - yetersiz/uygun değil: yanıcı membranların kullanımı uygun değildir. 12. Çatı Kapla

- **proje/denemeler/pompa_grubu/HIDROFOR_GRUBU_KESITI_R2.dxf**
  - LEJANT yazısı yok

- **proje/denemeler/pompa_grubu/PIS_SU_POMPA_CUKURU_KESITI_R2.dxf**
  - LEJANT yazısı yok

- **proje/denemeler/pompa_grubu/YANGIN_POMPA_GRUBU_KESITI_OFIS_R2.dxf**
  - LEJANT yazısı yok
  - elektrik: katman - (0 nesne); KABLO yazısı 1 — örn. "iketlerindedir. Elektrik kablo/sinyal hatları"

- **proje/denemeler/pompa_grubu/YANGIN_POMPA_GRUBU_KESITI_OTOPARK_R2.dxf**
  - LEJANT yazısı yok
  - elektrik: katman - (0 nesne); KABLO yazısı 1 — örn. "iketlerindedir. Elektrik kablo/sinyal hatları"

- **proje/denemeler/radyator/radyator_kombi_R3.dxf**
  - yazı çakışması: (3314, -8865), (3314, -9229)

- **proje/denemeler/radyator/radyator_merkezi_R4.dxf**
  - MTY blok adı 11, blok içi katman 235, katman 2, yazı stili 1, blok ekleme 55 — örn. blok adı: MTY-CEKVALF VANA, MTY-DENGE KABI PLAN, MTY-EMNİYET VENTİLİ; blok içi katman: MTY-TEFRIS, MTY-VANA; katman: MTY-TEFRIS, MTY-VANA; yazı stili: MTYCAPLT
  - ROTAS- olmayan katman: MD-YUK-BIRIMI, MTY-TEFRIS, MTY-VANA
  - yazı çakışması: (3314, -11133), (3314, -11391)
  - elektrik: katman - (0 nesne); KABLO yazısı 1 — örn. "sıcaklık sensörü (okuma kablosu elektrik projesin"
  - ONAYLI kazan dairesi (bölge x1): köprü 10, kesişme 0 — bilgi, hata sayılmadı

- **proje/denemeler/semboller/OTOMATIK_LEJANT_DENEME.dxf**
  - MTY blok adı 12, blok içi katman 509, katman 3, yazı stili 1, blok ekleme 28, yazı 6 — örn. blok adı: MTY-CEKVALF VANA, MTY-EMNİYET VENTİLİ, MTY-IZLENEBILIR KELEBEK VANA; blok içi katman: MTY-RADYATÖR, MTY-TEFRIS-CIKTI, MTY-VANA; katman: MTY-RADYATÖR, MTY-TEFRIS-CIKTI, MTY-VANA; yazı stili: MTYCAPLT; yazı: 1) Küresel vana / ventil: küresel = MTY-, 2) Sprinkler: dik = tek daire Ø25, sarkı, 3) Çekvalf: TR lejant biçimi (MTY-CEKVAL
  - ROTAS- olmayan katman: MTY-RADYATÖR, MTY-TEFRIS-CIKTI, MTY-VANA

- **proje/denemeler/semboller/SEMBOL_KUTUPHANESI.dxf**
  - MTY blok adı 75, blok içi katman 5928, katman 31, yazı stili 1, blok ekleme 62, yazı 88 — örn. blok adı: MTY- KATI YAKITLI KAZAN, MTY-BOSALTMA VANA, MTY-BOYLER KAT- KOLON; blok içi katman: MTY-CIHAZ, MTY-CIHAZ-NO, MTY-ISITMA-CAP; katman: MTY-CIHAZ, MTY-CIHAZ-NO, MTY-ISITMA-CAP; yazı stili: MTYCAPLT; yazı: 1) Küresel vana / ventil: küresel = MTY-, 2) Sprinkler: dik = tek daire Ø25, sarkı, 3) Çekvalf: TR lejant biçimi (MTY-CEKVAL
  - ROTAS- olmayan katman: ++MC CIHAZ LİSTE, +M+CIHAZ, +MC YAZI-1, -İG  GIDIS BORUSU, -İG GIDIS BORUSU, AÇIK GENLEŞME DEPOSU, BASLIK, CHZ

- **proje/denemeler/semboller2/SEMBOL_KUTUPHANESI_V2.dxf**
  - MTY yazı 6 — örn. yazı: ROTAŞ SEMBOL KÜTÜPHANESİ v2 — KOLON ŞEMA, Saf geometri (MTY bloğu yok). Blok içi k

- **proje/denemeler/sprinkler/kat_ofis_dolap_kolon_semasi_R2.dxf**
  - LEJANT yazısı yok

- **proje/denemeler/sprinkler/kat_ofis_dolap_plan_R2.dxf**
  - yazı çakışması: (1489, 575), (376, 1670), (1119, 1670), (1861, 1670), (2604, 1670)

- **proje/denemeler/sprinkler/kat_ofis_oh1_sprinkler_R2.dxf**
  - yazı çakışması: (1489, 575), (376, 1670), (1119, 1670), (1861, 1670), (2604, 1670)

- **proje/denemeler/sprinkler/otopark_dolap_kolon_semasi_R2.dxf**
  - LEJANT yazısı yok
  - yazı çakışması: (-404, -732), (471, -1229), (393, -1247)

- **proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R3.dxf**
  - ROTAS- olmayan katman: MIMARI, MIMARI-KOLON, MIMARI-TEFRIS, MIMARI-YAZI, RAST-TEM-SU DEPOSU, STM-ISITMA-CAP
  - kesişme noktaları: (8476, 1366), (8486, 1356), (8444, 1482), (8454, 1492), (8437, 1475)
  - yazı çakışması: (6764, 1286), (6768, 1277), (8424, 1517), (8424, 1517), (8424, 1517)

- **proje/denemeler/wc_havalandirma/NB_WC_HAVALANDIRMA_DENEME.dxf**
  - MTY blok adı 1, blok ekleme 1, yazı 1 — örn. blok adı: MTY-ÇATI TİPİ FAN; yazı: Çatı tipi fan (plan — MTY-ÇATI TİPİ FAN)

- **proje/denemeler/wc_havalandirma/ORNEK_Z2_9DAIRE_WC_HAVALANDIRMA.dxf**
  - MTY blok adı 1, blok ekleme 1, yazı 1 — örn. blok adı: MTY-ÇATI TİPİ FAN; yazı: Çatı tipi fan (plan — MTY-ÇATI TİPİ FAN)


## Sınırlar

- Boru katmanı katman adından seçilir (BORU, KANAL, SICAK, SOGUK, PIS, YAGMUR, GIDIS/DONUS, YANGIN, DOGALGAZ, SIHHI...; CAP/YAZI/SEMBOL/CIHAZ/MIMARI vb. hariç). Kesişme yalnız model alanında, uç noktalardan 15 cm içerideki geçişler (T bağlantısı, kanal ağzına giren flex vb. sayılmaz).
- Köprü: boru katmanında ARC (≥150°, r≤40 cm) veya LWPOLYLINE kavis segmenti (|bulge|≥0,8, kiriş≤80 cm). Köprü noktasına 45 cm içindeki kesişmeler kesişme sütununda tekrar sayılmaz.
- Yazı kutuları yazı tipi ölçülmeden tahmin edilir (karakter genişliği 0,8·h); küçük kutunun ≥%15 örtüşmesi çakışma sayılır. Yalnız model alanı yazıları (blok öznitelikleri dahil).
- Onaylı bölge: `*KAZAN_DAIRESI_PLAN_KESIT*` dosyaları tamamen; diğer dosyalarda XDATA `ROTAS: ONAYLI_KAZAN_DAIRESI` çerçevesinin içi.
