# ROTAŞ asansör avan projesi standardı

Kaynak: Can Özkaya'nın 12.10.2026'da gönderdiği `asansör.zip` (38 DWG, 2 PDF, 1 DOCX, 1 XLSX).
Hesap motoru `motor/asansor/asansor_hesap.py` içinde. Asansör tipini (makine daireli / makine dairesiz)
**kullanıcı söyler**. Tip söylenmeden çizime başlanmaz.

## 1. Örnek setin içeriği
| Dosya (ornekler/asansor/sablon) | Ne |
|---|---|
| `MAKINE_DAIRELI_SABLON.dwg` | Makine daireli tam avan seti (Ufuk Semih Gürbak, 3 katlı iş yeri). |
| `MAKINE_DAIRESIZ_SABLON.dwg` | Makine dairesiz (MRL) tam avan seti (Akşit Mimarlık, B+Z+3, Hendek). |
| `MAKINE_DAIRESIZ_KAPI_KABIN_DETAYLI.dwg` | MRL seti. Ekinde kat kapıları, kabin, butonyer ve kapı kenarı tadilatı detayı (1/10) var. |
| `KAPAK_ANTET.dwg` | Yeni kapak/antet. İki müellif var (Elektrik M. + Makine M.), yapı denetim ve belediye onay kutuları da içinde. |
| `TRAFIK_HESABI_ESKI_TS.dwg` | Eski TS trafik yöntemi: TR, Sp, N, B2 < B3. |
| `AVAN_TABLOSU_MMO.docx` | MMO avan proje tabloları: b, hız, H, S, ta/tk, tg, kapasite, tp, %k, Izul. |
| `EN81-20_UYGULAMA_HESABI_KOCEL.dwg.xz` | EN 81-20/50 uygulama hesabı (firma seti): ray gerilmeleri, halat, tampon, T1/T2 tahrik, emniyet katsayısı, gerilim düşümü, aydınlatma, elektrik şemaları. |

Diğer örnekler (yalnız metin dökümü `metin/`): A/B Blok, A-B, Abdullah Birinci, Makine daireli 3/4,
Makine dairesiz 3/4/5, KONE E1/E2 otel yerleşim çizimleri (MonoSpace, üretici "FOR REFERENCE ONLY").
Ayrıca Aykut Saban mimarileri var (girdi dosyası).

## 2. Pafta dizilimi (şablondaki sıra, soldan sağa)
1. **Antet / kapak**: ROTAŞ başlığı, yapı sahibi, il, ilçe, mahalle, pafta, ada, parsel, YİBF, kat adedi ve durak sayısı yer alır. "Asansörün Özellikleri" tablosunda şu alanlar var: beyan yükü, beyan hızı, seyir mesafesi, kapı ölçüsü, kuyu ölçüsü, kabin ölçüsü, askı tipi ve ray kalınlıkları. Müellif kutuları, yapı denetim ve belediye inceleme kutuları da buradadır. Altta "--- BLOK / ÖLÇEK 1/50" ile "MAKİNE DAİRELİ (veya DAİRESİZ) ASANSÖR AVAN PROJESİ" yazar.
2. **Yerleşim (vaziyet) planı** 1/200 (1/100–1/150): parsel, bina, yol, kotlar, kuzey oku.
3. **Hesap sayfası 1**: 1. ASANSÖR AVAN PROJESİ → 1.1 TRAFİK HESABI → 1.1.1 seyir zamanı → 1.1.1.2 asansör sayısı → 1.1.1.3 bekleme zamanı.
4. **Hesap sayfası 2**: 1.2 KUVVET HESABI → 1.2.1 kuyu dibi kuvvetleri → 1.2.2 halat ağırlığı → 1.2.3 kuyu üstü betonu kuvvetleri → 1.2.4 motor gücü. Sonunda "… kişilik … m/s hızında … lık 1 adet insan asansörü tesis edilecektir. ASANSÖR 4 HALATLI OLACAKTIR."
5–6. **Tablolar**: Tablo-1 … Tablo-12. Sırasıyla insan sayısı, H, S, kabin hızları, kapı zamanları, tek kat geçme, kabin kapasitesi, tp, %k, Izul, verim ve motor gücü.
7. **Şekil 1: Kuyu tabanına gelen yükler** 1/20. Kuyu planında PK, P1, PK (üst sıra) ve PR, P2, PR (alt sıra) kuvvetleri N cinsinden yazılır.
8. **Kuyu yerleşim planı** 1/20 (karşı ağırlık arkada): kuyu iç ölçüleri, kabin, ray, kapı. Altında ölçü tablosu (Kapasite, Hız, kapı mm, A, KG, Y, X, EE, RKE, RD, RE, RHA) ve kısaltma açıklamaları yer alır.
9. **Kuyu üzerinde bırakılacak halat delikleri** 1/20: 200×200 halat delikleri, 150×150 regülatör delikleri, Ø kancası.
10. **Asansör kuyusu (ve makine dairesi) dikine kesiti – yandan görünüş** 1/50. Katlar (B. KAT, Z. KAT, 1. KAT …) kat yükseklikleriyle gösterilir. Ayrıca KUYU MESAFESİ, SEYİR MESAFESİ, kuyu dibi P1/P2 ve tampon kaideleri, "Asansör kuyusu duman tahliye" bacası ve kesit ok işaretleri (A–A) bu paftadadır.
11. **Aynı kesit – karşıdan görünüş** 1/50.
12. **Makine daireli için**: Makine dairesi planı 1/50 (1/100) ve şu notlar: "Makine dairesi ortam sıcaklığı +5 °C ile +40 °C arasında korunmalıdır." / "Montaj sırasında veya değiştirmek gerektiğinde ağır asansör parçalarını kaldırmak için makine dairesi tavanına bir veya birden fazla uygun şekilde yerleştirilmiş taşıyıcı kanca monte edilmelidir." Makine dairesine 500×500 kurtarma kapağı ve yayılı yük gösterilir.
    **Makine dairesiz için**: makine ve tahrik kuyu tepesindedir. Kat kapıları, kabin detayı, kabin butonyeri ve kapı kenarı tadilatı 1/10 detayları eklenir.
13. **Kuyu-kabin yerleşim detayı** 1/10 ve **kümbet betonu delik detayı** 1/10.

Katmanlar (şablon): `YAZI` (hesap metni), `YAZI1` (tablolar, başlıklar), `kaçış` (kesitteki ölçüler, KUYU/SEYİR MESAFESİ), `KABİN`, `KUTUPHANE`, `MIMARI`, `MİMARİKOLON`, `MKDU0` (yerleşim ve antet yazıları), `02` (antet tablo), `çizgi` (firma başlığı), `ölçü dış`, `TEM.SU`.
Yazı yükseklikleri: hesap 12, kat adı 16, pafta başlığı 18–29,5, antet 20–30.

## 3. Kullanıcının pratiğindeki tipik değerler
- Kabin **10 kişi / 800 kg**, kabin **1200 × 1500 mm** (1,80 m²), kapı **900 mm teleskopik tam otomatik**, kapı yüksekliği 2200.
- **2/1 askı**, 4 halat (ø10, 0,373 kg/m). Kabin rayı 89×62×9 (T89), karşı ağırlık rayı 50×50×5, kapakta "90×70" yazıyor. Motor 380 V asenkron (motor tablosunda verim 0,8 yazıyor). Hız 1,00 m/s.
- Kuyu iç ölçüleri:
  - Makine daireli: 2100×2100, 2050×2000, 2050×1850, 2300×1900.
  - Makine dairesiz: 2100×1900, 2150×1900, 2200×1900, 2370×1900, 2500×2000, 2500×2050.
  - Kuyu derinliği **1900 mm** en yaygın değer.
- Kuyu mesafesi − seyir ≈ 2,9–3,5 m. Kesitte kuyu dibi ≈ 1,4–1,6 m. Son durak–kuyu tavanı: makine daireli 3,5 m (+ makine dairesi), makine dairesiz ≈ 3,6–4,5 m.
- Makine dairesinde 60/30 kolon ve 30/260 perde gösterimi var. Makine dairesi kapısı 90/220.

## 4. Hesap yöntemi (motor/asansor/asansor_hesap.py)
**MMO avan yöntemi (şablondaki):**
- B = Σb + n·Σb (Σb < 200 → n = %30, Σb ≥ 200 → %25). b, Tablo-1'den: konutta ilk yatak odası 2, diğer odalar 1. Mutfak ve diğer bölümler sayılmaz.
- P = 0,8 × kabin kişi sayısı (%80 doluluk).
- H = N − Σ_{i=1}^{N−1}(i/N)^P, S = N·[1 − ((N−1)/N)^P]. N, ana durak üzerindeki kat sayısıdır; ana durak ve zemin altı katlar dahil edilmez. Formüller MMO tablolarıyla birebir doğrulandı.
- tv = h/V, ts = ta + tk + tg − tv, tp = 2,2 s (kapı < 1 m) veya 2,0 s.
- T = 2·H·tv + (S+1)·ts + 2·P·tp
- R = 5·60·P/T, L = B·k/R → n = ⌈L⌉
- Bekleme zamanı I = T/n ≤ Izul (konut standart 100 s, şartlı kabul 120 s taahhütname ile).

**Eski TS yöntemi (çapraz kontrol):**
- TR = [(2H/V) + (ta+tt)(Sp+1) + tp·P]/n
- N = 300/TR, B3 = N·P, B2 = B1·K → B2 < B3 olmalı. Motor, dwg örneğini birebir veriyor (TR = 51, N = 5,88, B3 = 58,8).

**Kuvvetler:**
- Kabin tamponu altı: P1 = 4·gn·(P+Q)
- Karşı ağırlık tamponu altı: 4·gn·(P+q·Q)
- Karşı ağırlık = P + q·Q (q = 0,5)
- Kuyu üstü: gn·(makine + sehpa + montör + P + Q + Gh + KA)
- Motor: N = S·V/(102·η) kW, S = P + Gh + Q − KA

## 5. Şablonda bulunan hatalar (yeni projede yapılmayacak)
- **Hesap sayfası her projede aynı kopyalanmış.** Şu değerler kat sayısı ve kuyu ölçüsü ne olursa olsun değişmiyor: B=52, H=4,5, S=3,1, T=101,3, R=11,8, L=0,33, I=101,3, P1=80026 N, P2=55940 N, PR=24763 N, karşı ağırlık 738 kg, motor 10,5 HP.
  - Örnek: 3 katlı binada (N=3) H en fazla 3 olabilir, şablonda 4,5 yazıyor.
  - T formülünde P=4 kullanılmış, R formülünde 10×0,8 = 8 kullanılmış.
  - Motor: şablonda "= 550 + 31 + 50 + 800 − 738 = 269" yazıyor, ama bu toplam 693'tür.
  - Karşı ağırlık 738 kg alınmış. Q = 800 kg ve q = 0,5 ile 550 + 400 = 950 kg olmalı.
  - Doğru değerlerle S ≈ 481 kg ve N = S·V/(102·η) ≈ 5,9 kW çıkar. Şablonda 10,5 HP yazıyor; bir projede 5,5 HP.
  - Kuyu üstü: 9,81×2689 = 26.379 N olmalı, şablonda 25.888 yazıyor.
  - **Her projede motor/asansor_hesap.py ile yeniden hesaplanacak.**
- Kesitteki kat ölçüleri ile "KUYU MESAFESİ" toplamı tutmuyor (ör. Makine dairesiz 5: 265+445+280+280 = 12,70 seyir doğru, ama kuyu mesafesi 15,50 < 12,70 + dip + üst). Kuyu mesafesi = kuyu dibi + seyir + kuyu üstü olarak hesaplanır.
- Yazım hataları: "MAKİNA DAİRESLİ", "Diresi", "OTAMATİK", "İŞ MERKEİ", "asansörlerş", "klavuz", "Kuyu Kuyu Üzerinde". "4.40 m²" kuyu alanı olup kabin alanı değildir (kabin 1,80 m²).
- Antet notundaki yönetmelik atfı (14.06.1999 23725 / 08.05.2000 24043 RG) eskidir. Güncel asansör mevzuatı yürürlükteki Resmî Gazete metninden kontrol edilecek.

## 6. Kontrol listesi (her asansör projesinde)
- **İmar** (Planlı Alanlar İmar Yönetmeliği md. 34, resmi metinden teyit edilecek):
  - 3 katlı binada asansör yeri bırakılır, 4 ve daha fazla katlı binada asansör yapılır. İskân edilen bodrum kat sayılır.
  - Tek asansörde kabin dar kenarı ≥ 1,20 m, alanı ≥ 1,80 m², kapı net geçişi ≥ 0,90 m.
  - Sahanlık: sürgülü kapıda ≥ 1,20 m, dışa açılanda ≥ 1,50 m.
  - Kuyu dibi ≥ 1,40 m.
  - Ek asansör şartlarına bakılacak: umumi binalarda kat alanı > 800 m² ve 3 kattan fazla; yüksek binalar.
- **EN 81-20 Tablo 6**: kabin faydalı alanı ≤ beyan yüküne göre en büyük alan. 800 kg için 2,00 m², 1200×1500 = 1,80 m² uygun.
- **EN 81-20 kuyu dibi ve kuyu üstü sığınma boşlukları** firma uygulama projesinde kontrol edilir. KONE örneğinde sığınma hacimleri 1000×700×500 ve 700×500×1000, kuyu dibi boşluğu ≥ 500 mm.
- Kuyu dibi merdiveni, kuyu aydınlatması (kabin tavanı ve kuyu dibinin 1 m üstünde ≥ 50 lüks), makine dairesi aydınlatması (≥ 200 lüks). Makine dairesine normal kat merdiveniyle ulaşılır.
- **Tesisat koordinasyonu** (12.10.2026 talimatı):
  - Asansör kuyusundan ve makine dairesinden asansöre ait olmayan boru veya hat geçmez.
  - Kuyu dibine pis su süzgeci ya da bağlantısı konmaz.
  - Rögar ve altyapı hatları kuyu dibi (pit) altından geçmez, kuyu çevresinden dolaştırılır, kot kontrolü yapılır.
  - Rögar asansör kapı önüne konmaz.
  - Asansör alanı ısıtılmaz.

## 7. Akış
1. Kullanıcıdan şunlar alınır: asansör tipi, mimari DWG, kat sayısı ve kat yükseklikleri, bağımsız bölüm/oda listesi, kuyu ölçüsü (mimariden).
2. `Asansor(...)` girdileri doldurulur → `rapor()` → hesap sayfası metni çıkar.
3. Kontroller UYGUN değilse kullanıcıya bildirilir: hız, kapasite veya asansör sayısı artırılır.
4. Paftalar şablon DWG düzeniyle çizilir: kapak → yerleşim → hesap → tablolar → kuyu planları → kesitler → makine dairesi veya detaylar.
5. Teslim: DWG + DXF + PDF önizleme. Her şey Türkçe.

## 8. Çizim motoru (12.10.2026, ilk uygulama: Korucuk A-B-C-D)
- `motor/asansor/asansor_cizim.py proje.json çıkış/` -> DXF (R12, ANSI_1254, bağımlılıksız `dxfyaz.py`) + PDF önizleme + hesap metni.
- Proje girdisi örneği: `proje/korucuk_asansor/korucuk_A.json` (kuyular [kaba genişlik, kiriş altı net], derinlik, durak kotları, son döşeme alt kotu, kuyu dibi, mimari konum penceresi).
- **Kullanıcı talimatı: motorun asıldığı son döşeme (kuyu tavanı) ve kuyu iç ölçüleri her projede tek tek kontrol edilir.** Kontrol: her katta kaba/sıvalı/kiriş altı net ölçü; asansör kesitinde kuyu dibi döşemesi, son döşeme alt kotu ve kalınlığı, son durak -> üst boşluk.
- Yardımcı ölçüm: `araclar/asn_kuyu_bul.py` (çift kuyu bulucu), `araclar/asn_olc.py` (noktadan duvara ışın: kaba/sıva/kiriş mesafeleri).
- DWG: bu oturumda DWG yazıcı (ACadSharp/ezdxf) kurulamadı; DXF teslim edildi, AutoCAD'de SAVEAS ile DWG yapılır.
- **Ozalit düzeni (kullanıcı talimatı 12.10.2026):** A4 gibi ayrı sayfa verilmez. Tüm paftalar 594 mm yükseklikte tek şeritte yan yana çizilir. Şerit 1/50; 1/20 ve 1/10 paftalar büyütülür. Sol kenarda 20 mm cilt payı ve A4 katlama işaretleri bulunur. Kapak ROTAŞ antet şablonu düzenindedir. PDF tek sayfa, gerçek kağıt boyunda (594 mm x şerit boyu), siyah-beyaz ve kalem kalınlıklıdır; renk -> mm tablosu kapakta.

## 9. Pafta düzeni ve elektrik detayları (kullanıcı talimatı 12.10.2026, ikinci örnek)
- Örnek proje: `sablon/ORNEK_MRL_ELEKTRIKLI_2026-10-12.dxf.xz`. Kapak: `sablon/KAPAK_ANTET_2026-10-12.dwg`.
- **Düzen (örnekteki gibi):** 594 mm ozalit şeridi, A4/A3 hücreler iki sıra halinde. Sıra şöyledir:
  1. Kapak (kullanıcının kapak şablonu, alanlar doldurulur; altında kontrol notları ve kalem tablosu)
  2. Konum/yerleşim planı (tam yükseklik)
  3. Hesap-1 / Hesap-2
  4. Tablolar / kuyu yerleşim planı 1/20
  5. Detaylar 1/20 / kuyu dibi yükleri ve son döşeme 1/20
  6. Kesit yandan 1/50 (tam yükseklik)
  7. Kesit karşıdan 1/50 (tam yükseklik)
  8. **Elektrik detayları**
- **ELEKTRİK DETAYLARININ TAMAMI her asansör setinin sonuna eklenir (bu proje ve bundan sonraki tüm dosyalar).** Kaynak: `kutuphane/asansor/elektrik_detay.json`. İçerik: kumanda pano ve kuyu dibi güvenlik devresi bağlantıları (KBK 10-11, EN81-20), kuyu ve kabin beslemesi, kat kapıları tam otomatik / kapı kilit kontakları, kuyu dibi kutusu / revizyon el terminali, güvenlik devresi, şebeke beslemesi / dağıtım panosu.
- Kapak şablonu: `kutuphane/asansor/kapak_sablon.json`. Çıkarma aracı: `araclar/asn_sablon_cikar.py` (yeni örnek gelirse yeniden çıkarılır). Kapakta müellifler: Elektrik M. Hasan Daldal, Makine M. Bayram Genç (şablondaki gibi).
- Kapaktaki sorumluluk paragrafının sonu ("... yapı müteahhidine ve şantiye şefine aittir.") DWG dönüşümünde kesik geldiği için tamamlandı; kullanıcı teyit edecek.

## 10. Kalıcı kurallar (2026-10-12 kullanıcı talimatı)
- **Kabin standardı: en az 800 kg / 10 kişi**, kabin 1200x1500 — tüm projelerde (aksi söylenmedikçe).
- **Kat kapıları her zaman 90/210** (teleskopik otomatik). Mimar farklı yazdıysa (örn. 100/220) dikkate alınmaz, 90/210 çizilir ve notta "düzeltildi" yazılır.
- Durak kotları mimari asansör kesitinden okunur (`araclar/asn_kesit_olc.py flat.pkl cx cy`); zemin dükkân ±0,00 ise ve asansör girişi +1,00'de ise ilk durak +1,00'dir.
- **MRL (makine dairesiz):** makine dişlisiz PM, Ø240 kasnak, 2/1 askı, kuyu tepesinde kabin ve K.A. ray başlarına oturan 2xUPN kaide (parametrik `MRL` sözlüğü). Örnekteki kaideli makine sembolleri MRL'de KULLANILMAZ.
- **Makine daireli:** `tip: makine_daireli`, `aski: 1`; makine dairesinde örnek sembolleri (`semboller.json`: makine_yan karşıdan, makine_on yandan) kaide + tahrik + saptırma kasnağı; regülatör, kumanda panosu, ana şalter, askı kancası, halat delikleri makine dairesinde. JSON `makine_dairesi` (doseme_ust, tavan_alt, cati_ust, ic_gen, ic_der, sahanlik) ve `makine_dairesi_notlari`, `kesit_notlari` alanları.
- Kesitlerde "MOTOR" kutusu yazılmaz: iç sistem komple çizilir (raylar+konsollar, kabin çerçevesi, paraşüt, kasnaklar, halat güzergâhı, K.A., regülatör + gergi, tamponlar, aydınlatma, kuyu dibi stop/merdiven, kumanda panosu) ve etiketlenir.
- **Ölçüler kotlardan HESAPLANMAZ, mimarın ölçü yazılarından OKUNUR.** `araclar/asn_olcu_oku.py mimari.dxf x.dims.pkl` DIMENSION varlıklarını açar; kesit zinciri (kuyu dibi 140, 300'ler, son döşemeye 160, döşeme 10) buradan alınır. Kot yazısı çizginin ~15-20 cm üstündedir; ±0 kot yazısından türetilirse kayar (Korucuk'ta 15 cm kaydı: kuyu dibi 1,55 sanıldı, gerçek 1,40).
- Korucuk doğru değerleri: ilk durak +1,00 (D: -3,15), kuyu dibi -0,40 (D: -4,55) = 1,40 m, son döşeme altı +17,60, üst boşluk 4,60, +16,00 çatı döşemesi (durak değil). Dış duvar A/C/D 15, B 20; ara duvar 10.
- Kontrol listesi (her projede): durak sayısı = kat planı sayısı; kuyu dibi ölçüsü; son durak -> kuyu tavanı; döşeme kalınlığı; kuyu en/boy + kiriş; duvar kalınlıkları; kapı 90/210; 800 kg/10 kişi; daire sayısı.

## 11. Makine dairesiz (MRL) kalıcı kuralları (kullanıcı talimatı 13.10.2026, Korucuk revizyonu) — bundan sonraki TÜM MRL setlerinde
- **Makine montajı:** MRL makinesi kuyu tepesinde **yan perdeye ankrajlı duvar konsolu (2xUPN)** üzerinde, konsol altında **çapraz askılı sehpa** ile taşınır; raylara oturan kaide çizilmez. Karşıdan kesitte konsol + duvar ankraj plakası + çapraz askı (2 profil), yandan kesitte konsol altında X çapraz askı gösterilir.
- **Makine askı kancası yoktur** (kesitlerde, son döşeme planında, notlarda). Kabin ekseninde yalnız montaj kancası kalır.
- **Kuyu aydınlatması her katta** (her durak +1,50) + kuyu dibi + kuyu tepesi, min 50 lüks; kesitlerde her katta armatür sembolü.
- **Hız regülatörü ana (kabin) rayının yanında**, ray ile yan duvar arasında; kabin arkasında (arka duvarda) kalmaz. Planda ve kesitlerde bu konumda.
- **Halat: 7 x Ø6,5 mm** (gh = 0,152 kg/m), 2/1 askı. Hesapta "Halat: 7 x Ø6,5 mm", "ASANSÖR 7 x Ø6,5 mm (7 HALATLI)"; 1.2.3 başlığı "Makine Konsolu Üzerinden Kuyu Perdesine Etki Eden Kuvvetler".
- **Kesitlerde son döşeme üst kotu** (ör. +16,00 / +17,80) kot sembolüyle işlenir (MRL: kuyu tavanı döşemesi üstü; makine daireli: çatı döşemesi üstü).
- **Kapak düzeni:** kapak (antet) şeridin sol alt köşesine sıfırlanır, "KONTROL VE NOTLAR" paftası kapağın üstündedir (aynı sütun).
- **Paftalar sıkıştırılır:** her pafta içeriğine göre daraltılır, paftalar arasında boşluk kalmaz; ayırıcı ve çerçeve çizgileri tek çizgi, üst üste binmez (`asansor_cizim.py` → `yerlestir()`).
- DWG: asansör çizici R12 DXF yazar; DWG için `motor/asansor/r12_to_dwg.py` (R2018'e yükseltip ACadSharp AC1032).
