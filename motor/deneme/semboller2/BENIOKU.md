# semboller2 — ROTAS sembol kütüphanesi v2 (MTY'siz, saf geometri) — DENEME 14.10.2026

14.10.2026 (B) talimatına göre: **MTY bloğu kullanılmaz.** Bu modüldeki 75 blok yalnız LINE / CIRCLE / ARC / LWPOLYLINE /
HATCH(solid) ile çizilir. Blok içinde TEXT/MTEXT/INSERT yoktur. Sembol içi harfler (kalorimetre "Q", izlenebilir
kelebek "S") çizgi harf olarak çizilir. ATTDEF yalnız `NO` ve `CAP`. Görünüş vanası, gizli alt blok, dinamik blok yoktur.
Blok içi bütün geometri **katman 0, renk/çizgi tipi/kalınlık BYLAYER**. INSERT hangi `ROTAS-` katmanına konursa onun rengini alır.

## Dosyalar
| Dosya | Ne yapar |
|---|---|
| `cekirdek.py` | `Ciz` (blok içine dönüşümlü çizim: öteleme/döndürme/ayna, kapsam takibi, ok, papyon, kapsül, kesikli, zigzag, vektör harf), `sembol()` kayıt dekoratörü, `GRUP` |
| `tanimlar.py` | 75 sembolün geometrisi (aşağıdaki liste) |
| `sembol2.py` | API: `ekle`, `koy`, `hat`, `baglanti`, `Engel`, `etiket_yer`, `etiketle`, `kullanim_say`, `otomatik_lejant`, `lejant_tablosu` |
| `olustur.py` | Lejant paftalı kütüphane DXF'i ve deneme DXF'i üretir |

## Çalıştırma
```
python3 motor/deneme/semboller2/olustur.py              # DXF'ler
python3 motor/deneme/semboller2/olustur.py --png /tmp/x # + kontrol PNG'leri (depo dışı)
```
Çıktılar (AC1032, birim cm):
- `proje/denemeler/semboller2/SEMBOL_KUTUPHANESI_V2.dxf`: 7 pafta, soldan sağa SIHHİ, DEPO-HİDROFOR, ISITMA, YANGIN, HAVALANDIRMA,
  KOLON ŞEMASI ŞABLONLARI, ETİKET DENEMESİ. Grup paftalarının sütunları: NO | BLOK ADI | 1/50 GERÇEK BOY (örnek boru + numara,
  `etiket_yer` ile) | BÜYÜTÜLMÜŞ | AÇIKLAMA. Her paftanın sonunda o grubun boru katmanı çizgileri vardır.
- `proje/denemeler/semboller2/OTOMATIK_LEJANT_DENEME_V2.dxf`: iki kazanlı örnek hat (DENEME). Numaralar `etiketle()` ile
  yerleştirildi (kazan dairesi geri bildirimindeki V-21/V-10, TM-01/M-01 karışıklığının çözümü). Sağda `otomatik_lejant()` var.

## Boyutlar (1/50)
- Hat üstü vana L = 20 cm (kağıtta 4 mm), H = 12 cm. Çek valf, pislik tutucu ve sayaç 12 cm. Pompa Ø20.
- Numara yazısı 10 cm (2 mm), çap yazısı 8 cm. `koy(..., yh=)` ile değişir.
- Plan sembolleri gerçek ölçüdedir: yer süzgeci 15×15, rögar 70×70 iç (duvar 10), yangın dolabı 70×25, menfez 30×30,
  şaft 40×40, radyatör 100 cm (X ölçeği = boy/100).
- Kolon şeması şablonları MTY KOLON bloklarına yakın boydadır. Örneğin lavabo tezgahı 85 cm'de, klozet rezervuarı 72-98 cm,
  hela rezervuarı 170-192 cm, kombi 140-215 cm, çamaşır ve bulaşık makinesi 60×85.

## API
```python
import sys; sys.path.insert(0, 'motor/deneme/semboller2')
import sembol2 as S
S.ekle(doc)                                          # tüm ROTAS- blokları + katmanlar
ins = S.koy(msp, 'SB-KURESEL-VANA', x, y, aci=0, olcek=1, no='V-01', cap='Ø20',
            katman='ROTAS-SIHHI-SOGUK-SU', ayna=False, yh=10)
S.hat(msp, (x0, y0), (x1, y1), [(0.3, 'SB-KURESEL-VANA', 'V-01', 'DN25'), (0.6, 'SB-CEKVALF', 'V-02')],
      katman='ROTAS-ISITMA-GIDIS', sembol_katman='ROTAS-ISITMA-SEMBOL')   # boru sembolde kesilir
S.baglanti(ins)            # {'soguk': (x, y), 'sicak': ..., 'pis': ...}  dünya koordinatı
eng = S.Engel(msp)         # STRtree: çizgi, yay, daire, yazı, öznitelik, INSERT kapsamları
S.etiket_yer(ins, eng, 'NO')   # tek etiket
S.etiketle(msp, eng)           # bütün ROTAS- INSERT'lerin NO/CAP'i; dönüş: yerleştirilemeyenler
S.otomatik_lejant(doc)         # yalnız kullanılan semboller, grup grup + ADET; dönüş {blok: adet}
```
- Ad kısaltılabilir: `'ROTAS-SB-CEKVALF'`, `'SB-CEKVALF'` veya `'CEKVALF'`.
- Yön kuralı: hat üstü semboller yerel +X'te akar (çek valf oku, pompa üçgeni ucu). `hat()` açıyı p0→p1 yönünden alır.
  Uç sembollerinde (`uc=True`: armatür bağlantı noktaları) boru sembolde biter.
- `koy()` öznitelikleri her zaman ekler, değer boşsa boş bırakır; böylece CAD'de sonradan düzenlenebilir. Öznitelik
  döndürülmez, her zaman düz okunur. `no_ic` sembollerde (rögar, kolon balonu) numara sembolün ortasındadır.
- `etiket_yer`: aday konumlar sembol kapsamının 8 yönündedir. Hat üstü sembollerde önce boruya dik yön denenir (yatay hatta
  üst/alt, dikey hatta sağ/sol). Aday kutu, sembolün kendisi dışında hiçbir çizgi, yazı veya bloğa değmemelidir. İlk halkada
  yer yoksa 3 halka daha uzaklaşılır ve `ROTAS-SEMBOL-KILAVUZ` katmanına kılavuz çizgisi konur. Konan etiket engellere eklenir.
- `otomatik_lejant`: sembol grubu INSERT'in katmanından bulunur. Örneğin ısıtma hattındaki küresel vana ısıtma lejantına girer.
  Kullanıcı grup bloklarının içi taranır. `ROTAS-LEJANT*` katmanı sayılmaz. Çizimde kullanılan boru katmanları da lejantta
  çizgi örneği olarak gösterilir.

## Katmanlar
Sembol: `ROTAS-SIHHI-SEMBOL`, `ROTAS-SIHHI-DEPO-HIDROFOR`, `ROTAS-ISITMA-SEMBOL`, `ROTAS-YANGIN-SEMBOL`,
`ROTAS-HAVALANDIRMA-SEMBOL`, `ROTAS-SIHHI-ARMATUR` (kolon şeması armatürleri). Etiket: `ROTAS-SEMBOL-NO`, `ROTAS-SEMBOL-CAP`,
`ROTAS-SEMBOL-KILAVUZ`. Boru: v1 ile aynı adlar (`ROTAS-SIHHI-SOGUK-SU`, `ROTAS-SIHHI-SICAK-SU` DASHED, `ROTAS-SIHHI-PIS-SU`,
`ROTAS-ISITMA-GIDIS`, `ROTAS-ISITMA-DONUS` ...). Lejant: `ROTAS-LEJANT-*`.

## Kontroller (olustur.py sonrası yapıldı)
- ezdxf audit: 0 hata. Blok içinde katman 0 dışında veya BYLAYER olmayan varlık yok. Blok içinde TEXT/MTEXT/INSERT yok,
  `NO`/`CAP` dışında ATTDEF yok. MTY adlı blok yok.
- Yerleştirme sonrası 126 etiketin hiçbiri bir çizgi, yazı veya bloğa binmiyor (Engel ile yeniden sınandı).
- Bütün paftalar PNG önizlemeyle tek tek kontrol edildi.

## Sınırlar / açık konular
- (*) işaretli semboller örnek lejantlar arasında çelişkilidir ve kullanıcı teyidi bekler: küresel/ventil ayrımı, TR tipi
  çek valf, sprinkler dik (daire + artı) / sarkık (çift daire).
- Kolon şeması şablonları borunun kendisini çizmez. Ara musluk ve sifon dahildir, bağlantı noktası `baglanti()` ile alınır.
  Boruyu şemayı çizen modül, kendi katmanında çizer. Kombi ve termosifon bağlantıları alttan, diğer armatürlerinki üstten
  (temiz su) ve alttan (pis su) yapılır.
- Damper ve yangın damperi 30 cm kanal içindir. Başka kanal genişliğinde Y ölçeği G/30 verilir: `olcek=(1, G/30)`.
- `etiket_yer` yazı genişliğini 0,72·h·karakter olarak tahmin eder (Arial). Çok uzun metinlerde kutu biraz büyük çıkabilir.
- Doğalgaz sembolleri bu sürümde yoktur (v1'de vardı). İstenirse aynı yöntemle eklenir.
- v1 (`motor/deneme/semboller`) MTY bloklarına bağlıdır, 14.10 (B) ile geçersizdir. Yeni işlerde v2 kullanılmalıdır.

## Sembol listesi (75)

### SIHHİ TESİSAT SEMBOLLERİ — varsayılan katman `ROTAS-SIHHI-SEMBOL`
| Blok | Açıklama | Kapsam (cm) | Kesme | Bağlantı | Önek |
|---|---|---|---|---|---|
| `ROTAS-SB-KURESEL-VANA` | KÜRESEL VANA (ARA MUSLUK) (*) | 20×14 | (-10, 10) | - | V |
| `ROTAS-SB-SURGULU-VANA` | SÜRGÜLÜ VANA | 20×16 | (-10, 10) | - | V |
| `ROTAS-SB-VENTIL` | VENTİL (GLOB VANA) | 20×15 | (-10, 10) | - | V |
| `ROTAS-SB-CEKVALF` | ÇEK VALF (OK AKIŞ YÖNÜ) (*) | 12×16 | (-6, 6) | - | V |
| `ROTAS-SB-PISLIK-TUTUCU` | PİSLİK TUTUCU (Y TİPİ) | 12×12 | (-6, 6) | - | V |
| `ROTAS-SB-BASINC-DUSURUCU` | BASINÇ DÜŞÜRÜCÜ VANA | 25×17 | (-10, 10) | - | V |
| `ROTAS-SB-SU-SAYACI` | SU SAYACI | 12×14 | (-6, 6) | - | S |
| `ROTAS-SB-YER-SUZGECI` | YER SÜZGECİ (PLAN, 15x15) | 15×15 | - | - | YS |
| `ROTAS-SB-BALKON-SUZGECI` | BALKON SÜZGECİ (YAN ÇIKIŞLI, YAĞMUR HATTINA) | 17×12 | - | - | BS |
| `ROTAS-SB-TEMIZLEME-KAPAGI` | TEMİZLEME KAPAĞI (T.K., PLAN) | 10×10 | - | - | TK |
| `ROTAS-SB-HAVALIK` | PİS SU HAVALIĞI (PLAN, ÇATI ÇIKIŞI) | 13×13 | - | - | H |
| `ROTAS-SB-KOLON-PIS` | PİS SU KOLONU (İNİŞ) — PLAN | 10×10 | - | - | P |
| `ROTAS-SB-KOLON-TEMIZ` | TEMİZ SU KOLONU — PLAN | 8×8 | - | - | TS |
| `ROTAS-SB-KOLON-YAGMUR` | YAĞMUR SUYU İNİŞİ — PLAN | 10×10 | - | - | YB |
| `ROTAS-SB-KOLON-NO` | KOLON NUMARA BALONU (P1, YB1 ...) | 34×34 | - | - | P |
| `ROTAS-SB-ROGAR` | RÖGAR (MUAYENE BACASI) 70x70 — PLAN | 90×90 | - | giris, cikis | R |
| `ROTAS-SB-ARMATUR-SU` | ARMATÜR TEMİZ SU BAĞLANTI NOKTASI (ARA MUSLUK + DUVAR ÇIKIŞI) | 15×8 | (-10, 0) uç | boru, armatur | - |
| `ROTAS-SB-ARMATUR-PIS` | ARMATÜR PİS SU BAĞLANTI NOKTASI (GİDER AĞZI) | 6×6 | (-3, 3) uç | boru | - |

### SU DEPOSU / HİDROFOR SEMBOLLERİ — varsayılan katman `ROTAS-SIHHI-DEPO-HIDROFOR`
| Blok | Açıklama | Kapsam (cm) | Kesme | Bağlantı | Önek |
|---|---|---|---|---|---|
| `ROTAS-DH-SAMANDIRALI-VANA` | ŞAMANDIRALI VANA (DEPO GİRİŞİ) | 32×30 | (-10, 10) | - | V |
| `ROTAS-DH-MEMBRANLI-TANK` | MEMBRANLI GENLEŞME / HİDROFOR TANKI | 24×58 | - | baglanti | MT |
| `ROTAS-DH-HIDROFOR` | HİDROFOR GRUBU (2 POMPA, KOLLEKTÖRLER, MEMBRANLI TANK) | 180×117 | - | emis, basma | HF |
| `ROTAS-DH-DALGIC-POMPA` | DALGIÇ POMPA (PİS SU / DRENAJ ÇUKURU) | 16×43 | - | basma | DP |

### ISITMA TESİSATI SEMBOLLERİ — varsayılan katman `ROTAS-ISITMA-SEMBOL`
| Blok | Açıklama | Kapsam (cm) | Kesme | Bağlantı | Önek |
|---|---|---|---|---|---|
| `ROTAS-IS-RADYATOR-PLAN` | PANEL RADYATÖR — PLAN (100 cm; X ölçeği = boy/100) | 100×8 | - | gidis, donus | R |
| `ROTAS-IS-RADYATOR-SEMA` | PANEL RADYATÖR — ŞEMA | 120×30 | - | gidis, donus | R |
| `ROTAS-IS-TERMOSTATIK-VANA` | TERMOSTATİK RADYATÖR VANASI | 12×17 | (-6, 6) | - | V |
| `ROTAS-IS-RAKORLU-DONUS` | RAKORLU DÖNÜŞ (ARA) VANASI | 10×6 | (-5, 5) | - | V |
| `ROTAS-IS-KOLLEKTOR` | KOLLEKTÖR (4 ÇIKIŞLI, PURJÖR + BOŞALTMA) | 61×29 | - | giris, c1, c2, c3, c4 | KL |
| `ROTAS-IS-KALORIMETRE` | KALORİMETRE (ISI PAY ÖLÇER) | 14×14 | (-7, 7) | - | KM |
| `ROTAS-IS-BALANS-VANASI` | BALANS (DENGELEME) VANASI | 20×16 | (-10, 10) | - | V |
| `ROTAS-IS-POMPA` | SİRKÜLASYON POMPASI (ÜÇGEN UCU = AKIŞ YÖNÜ) | 20×20 | (-10, 10) | - | P |
| `ROTAS-IS-KAZAN` | KAZAN (DUVAR / YER TİPİ) | 60×100 | - | gidis, donus, gaz, baca | K |
| `ROTAS-IS-KOMBI` | KOMBİ — PLAN (YOĞUŞMALI, BACA DIŞ CEPHEYE) | 44×43 | - | arka | K |
| `ROTAS-IS-GENLESME-TANKI` | KAPALI GENLEŞME TANKI (MEMBRANLI) | 24×34 | - | baglanti | GT |
| `ROTAS-IS-DENGE-KABI` | DENGE KABI (HİDROLİK AYIRICI) | 36×110 | - | p_gidis, p_donus, s_gidis, s_donus | DK |
| `ROTAS-IS-EMNIYET-VENTILI` | EMNİYET VENTİLİ (YAYLI) | 21×23 | - | giris, cikis | EV |
| `ROTAS-IS-MANOMETRE` | MANOMETRE | 9×15 | - | boru | M |
| `ROTAS-IS-TERMOMETRE` | TERMOMETRE | 5×17 | - | boru | T |
| `ROTAS-IS-PURJOR` | OTOMATİK PURJÖR (HAVA ATICI) | 5×17 | - | boru | HP |

### YANGIN TESİSATI SEMBOLLERİ — varsayılan katman `ROTAS-YANGIN-SEMBOL`
| Blok | Açıklama | Kapsam (cm) | Kesme | Bağlantı | Önek |
|---|---|---|---|---|---|
| `ROTAS-YG-SPRINKLER-DIK` | SPRİNKLER — DİK (UPRIGHT) (*) | 16×16 | - | - | SP |
| `ROTAS-YG-SPRINKLER-SARKIK` | SPRİNKLER — SARKIK (PENDENT) (*) | 16×16 | - | - | SP |
| `ROTAS-YG-SPRINKLER-YAN` | SPRİNKLER — YAN DUVAR (SIDEWALL) | 16×8 | - | - | SP |
| `ROTAS-YG-YANGIN-DOLABI` | YANGIN DOLABI (HORTUM Ø1" 30 m) — PLAN | 70×25 | - | boru | YD |
| `ROTAS-YG-ITFAIYE-AGZI` | İTFAİYE BAĞLANTI AĞZI (İKİZ, STORZ) | 16×27 | - | boru | İB |
| `ROTAS-YG-ITFAIYE-KOLLEKTOR` | İTFAİYE BAĞLANTI KOLLEKTÖRÜ (2 AĞIZ, ÇEK VALF TESİSATA DOĞRU) | 74×46 | - | cikis | İB |
| `ROTAS-YG-ALARM-VANASI` | ISLAK ALARM VANASI (KAT/ZON) | 28×19 | (-10, 18) | - | AV |
| `ROTAS-YG-AKIS-ANAHTARI` | AKIŞ ANAHTARI (FLOW SWITCH) | 10×16 | (-5, 5) | - | AA |
| `ROTAS-YG-IZLENEBILIR-KELEBEK` | İZLENEBİLİR KELEBEK VANA (S = KONUM ANAHTARI) | 10×26 | (-5, 5) | - | V |
| `ROTAS-YG-KELEBEK-VANA` | KELEBEK VANA | 11×19 | (-5, 5) | - | V |
| `ROTAS-YG-TEST-DRENAJ` | TEST VE DRENAJ VANASI (GÖZETLEME CAMLI) | 31×14 | - | boru, drenaj | TD |

### HAVALANDIRMA TESİSATI SEMBOLLERİ — varsayılan katman `ROTAS-HAVALANDIRMA-SEMBOL`
| Blok | Açıklama | Kapsam (cm) | Kesme | Bağlantı | Önek |
|---|---|---|---|---|---|
| `ROTAS-HV-ASPIRATOR` | WC ASPİRATÖRÜ (TAVAN / KANAL TİPİ) — PLAN | 24×24 | - | - | A |
| `ROTAS-HV-MENFEZ-UFLEME` | ÜFLEME MENFEZİ / DİFÜZÖR (4 YÖNLÜ, 30x30) — PLAN | 48×48 | - | - | M |
| `ROTAS-HV-MENFEZ-EMIS` | EMİŞ / EGZOZ MENFEZİ (30x30) — PLAN | 48×48 | - | - | M |
| `ROTAS-HV-PANJUR` | PANJUR (TAZE HAVA / EGZOZ, DUVARDA) — PLAN | 40×8 | - | - | PJ |
| `ROTAS-HV-DAMPER` | AYAR DAMPERİ (KANAL GENİŞLİĞİ 30; Y ÖLÇEĞİ = G/30) | 14×43 | - | - | D |
| `ROTAS-HV-YANGIN-DAMPERI` | YANGIN DAMPERİ (KANAL GENİŞLİĞİ 30) | 8×36 | - | - | FD |
| `ROTAS-HV-CATI-FANI` | ÇATI TİPİ FAN — PLAN | 40×40 | - | - | F |
| `ROTAS-HV-CATI-FANI-KESIT` | ÇATI TİPİ FAN — KESİT / ŞEMA SONU (MANTAR) | 36×32 | - | kanal | F |
| `ROTAS-HV-SAFT` | MEKANİK HAVALANDIRMA ŞAFTI 40x40 — PLAN | 40×40 | - | - | ŞF |

### KOLON ŞEMASI ŞABLONLARI (YAN GÖRÜNÜŞ) — varsayılan katman `ROTAS-SIHHI-ARMATUR`
| Blok | Açıklama | Kapsam (cm) | Kesme | Bağlantı | Önek |
|---|---|---|---|---|---|
| `ROTAS-KS-LAVABO` | LAVABO | 60×58 | - | soguk, sicak, pis | - |
| `ROTAS-KS-KLOZET` | KLOZET (ALAFRANGA, ASMA REZERVUAR) | 45×100 | - | soguk, pis | - |
| `ROTAS-KS-HELA` | HELA TAŞI (ALATURKA, YÜKSEK REZERVUAR) | 60×230 | - | soguk, pis | - |
| `ROTAS-KS-DUS` | DUŞ TEKNESİ + DUŞ BATARYASI | 80×190 | - | soguk, sicak, pis | - |
| `ROTAS-KS-KUVET` | KÜVET + BATARYA | 110×78 | - | soguk, sicak, pis | - |
| `ROTAS-KS-EVIYE` | EVİYE (TEZGAH ALTI DOLAPLI) | 110×104 | - | soguk, sicak, pis | - |
| `ROTAS-KS-CAMASIR-MAKINESI` | ÇAMAŞIR MAKİNESİ | 60×102 | - | soguk, pis | - |
| `ROTAS-KS-BULASIK-MAKINESI` | BULAŞIK MAKİNESİ | 60×102 | - | soguk, pis | - |
| `ROTAS-KS-YER-SUZGECI` | YER SÜZGECİ (SİFONLU) | 20×18 | - | pis | - |
| `ROTAS-KS-KOMBI` | KOMBİ (DUVAR TİPİ, YOĞUŞMALI) | 40×98 | - | gidis, sicak, gaz, soguk, donus | K |
| `ROTAS-KS-TERMOSIFON` | TERMOSİFON (ELEKTRİKLİ, EMNİYET VENTİLLİ) | 42×99 | - | soguk, sicak | TS |
| `ROTAS-KS-SAYAC-GRUBU` | SAYAÇ GRUBU (VANA - SAYAÇ - ÇEK VALF - VANA, KESİNTİSİZ) | 92×19 | (0, 92) | giris, cikis | S |
| `ROTAS-KS-PVC-CATAL` | PVC ÇATAL (45°, SAĞ; SOL İÇİN ayna=True) | 21×31 | - | ust, alt, dal | - |
| `ROTAS-KS-TEMIZLEME-KAPAGI` | TEMİZLEME KAPAĞI (T.K., KOLON) | 14×24 | - | ust, alt | TK |
| `ROTAS-KS-ROGAR` | RÖGAR (ŞEMA) | 50×45 | - | giris, cikis | R |
| `ROTAS-KS-HAVALIK` | PİS SU HAVALIK ŞAPKASI (KOLON SONU) | 18×15 | - | kolon | - |
| `ROTAS-KS-SU-DEPOSU` | SU DEPOSU (ŞAMANDIRA, HAVALIK, TAŞMA, BOŞALTMA, SEVİYE) | 258×192 | - | giris, cikis, huni | D |
