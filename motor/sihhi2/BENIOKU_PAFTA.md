# sihhi2 — pafta birleştirme (antet.py, detay.py, pafta.py)

SIHHİ TESİSAT PROJESİ 1. sıra paftalarını `ornekler/ORNEK_DUZEN.md` sırasıyla **tek şeritte** (yükseklik 2900 cm) birleştirir.
Ölçüler kullanıcının `new_block.dxf` çiziminden (`kutuphane/arastirma/SIHHI_ALTIN_REFERANS.md` §1, §7). MTY bloğu yok, saf geometri.

| Sıra | Pafta | Genişlik (cm) | x (referans) | Kaynak |
|---|---|---|---|---|
| 1 | ROTAŞ anteti (958 × 1428, şeridin sol altında = kapak) | 1008 | 247352 | `antet.antet_ciz` |
| 2 | YERLEŞİM PLANI ÖLÇEK: 1 / 250 + bilgi kutuları + alan hesabı | 1682 | 248360 | `antet.yerlesim_ciz` |
| 3 | TEMEL PLANI.........ÖLÇEK: 1 / 50 | 2471 | 250042 | `NB_SIHHI_TEMEL.dxf` ya da yer tutucu |
| 4 | ZEMİN / 1. / 2. KAT PLANI.........ÖLÇEK: 1 / 50 (+ plan.py lejant/çatı paftası 2058) | 2065 / 2039 / 2039 | 252513… | `NB_SIHHI_KAT_PLANLARI.dxf` (plan.py) |
| 5 | AÇILIMLI KOLON ŞEMASI (+ rögar, yağmur şeması; başlık/lejant yok, kullanıcınınki gibi) | 7418 | 260714 | `NB_SIHHI_SEMA.dxf` (sema.py) ya da yer tutucu |
| 6 | WC havalandırma izometrisi (üst) + SIHHİ DETAYLAR 2000 × 1500 (alt) | 2065 | 268132 | `detay.detay_paftasi` |

Başlıklar h 40, pafta solu + 538, alt çerçeveden 39 yukarı. Girdi DXF'inde `ROTAS-PAFTA` katmanında 2900 yükseklikli
dikdörtgenler varsa pafta sınırı onlardır (içerik ölçeksiz taşınır); yoksa içerik referans genişlikli paftanın ortasına
konur ve başlık yoksa eklenir. Girdi yoksa kesikli kırmızı `ROTAS-YER-TUTUCU` çerçeve. Ortak `ROTAS-` blokları
yeniden adlandırılmadan paylaşılır.

## Çalıştırma
```bash
cd motor/sihhi2
python3 pafta.py                                              # varsayılan girdiler proje/denemeler/sihhi2/
python3 pafta.py --vaziyet /tmp/claude-0/uu/new_block.dxf     # yerleşim paftasına kullanıcının vaziyet+kesit çizimi (~25 s)
python3 pafta.py --plan P.dxf --sema S.dxf --temel T.dxf --wc girdi.json --cikti OUT.dxf
python3 ../deneme/denetim/denetle.py ../../proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf --rapor-yok --ayrinti
```
Python: `pafta.birlestir(plan_dxf, sema_dxf, temel_dxf, cikti, bilgi=None, vaziyet=None, wc_girdi=None)`;
`bilgi` = `antet.BILGI_VARSAYILAN` anahtarları (il, ada, parsel, yapı sahibi, alan hesabı …).

## Ayrıntılar
- **antet.py**: antet kutuları/çizgileri new_block ölçüleri; yazı genişliği arial ile ölçülür (`yazi_genislik`), nokta dizili
  bilgi satırları etikete binmez. Vaziyet altlığı: INSERT/DIMENSION patlatılır (yabancı/MTY blok kalmaz), tek katman
  `ROTAS-MIMARI-VAZIYET`, yazı stili `ROTAS`; tek satırlık MTEXT'in aşırı geniş sütunu kaldırılır.
  `vaziyet['orijin']` verilirse bölge "yerinde" (ölçeksiz) alınır; kullanıcının bilgi kutusu/başlık/kuzey oku `haric` ile atlanır
  (`pafta.NB_YERLESIM`).
- **detay.py**: 4 tablo (TS 1258 çap, TS EN 12056-2 SB, pis su çap, TS 1258 YB/debi), PİSSU / TEMİZ SU lejantı + **ADET**
  (`adet_say`: semboller2 `kullanim_say` + plan.py `ROTAS-S2-*` eşdeğerleri; kolon/YB numaraları farklı numara sayısıyla, lejant
  katmanları sayılmaz). Lejant hücresinde çizimde kullanılan blok (ör. `ROTAS-S2-YER-SUZGECI`) gösterilir. Montaj detayları
  saf geometri. WC izometrisi `motor/deneme/wc_havalandirma` (girdi yoksa `nb_algilanan.json` → `ornek_z2_9daire.json`).
  **Şaft birleştirme** (`detay.saft_birlestir`, `pafta.py --saft "D3,D5,D8;D1,D2,D4,D6,D7,D9"`, varsayılan
  `pafta.NB_SAFT_GRUPLARI`): kullanıcının iki şaftı — D3-5-8 240 m³/h, D1-2-4-6-7-9 480 m³/h; her daire o katta tek
  aspiratör (80 m³/h-50 pa Ø150 mm). İzometride iç lejant ve proje/dosya adı satırı yok.

## Deneme sonucu (15.10.2026)
`proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf`: 9 pafta, şerit 22845 × 2900; pafta x'leri referansla birebir.
denetle.py ✓ (MTY 0, önek 0, lejant ✓, yazı çakışması 0, audit 0). Temel ve şema girdileri henüz yok → yer tutucu.

## Açık
- DWG/PDF/Excel teslim adımı burada yok (birleşik DXF üretir). Kontrolör onayı olmadan kullanıcıya gönderilmez.
- 2. sıra (ISITMA TESİSATI PROJESİ) aynı API ile `bilgi={'proje_turu': 'ISITMA TESİSATI PROJESİ'}` kurulabilir; yapılmadı.
