# 09 — ROTAŞ çizim motoru denetimi (14.10.2026)

Kapsam: README.md, CLAUDE.md, `ornekler/ORNEK_DUZEN.md`, `ornekler/asansor/ASANSOR_STANDARDI.md`, `kutuphane/ornek_mekanik/BENIOKU.md`, `ARASTIRMA_GITHUB_AUTOCAD.md`, `motor/` altındaki tüm modüller (~150 .py), `araclar/`, `proje/`, git geçmişi (55 commit) ve `rotas-mekanik-proje-standardi`, `tesisat-hesap-kutuphanesi`, `rotas-asansor-avan-projesi` becerileri.
Bu denetimde hiçbir kod veya proje dosyası değiştirilmedi. Yalnızca `asansor_hesap.py` örnek hesabı geçici klasörde çalıştırıldı (smoke test, çıktısı sorunsuz).

---

## 0. Kısa sonuç

- Motor, **tek bir genel program değil.** Her proje için ayrı yazılmış betiklerden oluşuyor (`tb.py`, `st.py`, `et.py`, `voyap/*`, `p4/kd.py`, `gungoren/ys_ciz2.py`). Bu betikler ortak çekirdeği (`cad`, `emit`, `mtyblk`, `p2/gp`, `gsheet`, `router`, `xcheck`) kullanıyor. Kat kaydırmaları, pencere koordinatları, kolon yerleri ve ekipman seçimleri betiklerin içinde sabit değer olarak yazılı.
- Gerçek anlamda **veriyle çalışan (JSON girdili) tek hat asansör hattı:** `asansor_cizim.py proje.json çıkış/`.
- Yaklaşık **90 Python dosyasında `/tmp/claude-0/...` ve `/home/claude/nb` yolları sabit yazılmış.** VOYAP, Cafer Göktaş, SA PROFİ, şema HESAPLAR, ısıtma HESAPLAR ve İZODER işlerinin girdi dosyaları depoda yok. Bu yüzden bu işler bugün yeniden üretilemiyor; yalnız çıktıları arşivde duruyor.
- En büyük kural çelişkileri iki tane:
  - **Katman öneki:** SCOTT- / ROTAS- / MTY- arasında karar verilmemiş.
  - **Teslim biçimi:** CLAUDE.md DWG+DXF+PDF+Excel diyor, kullanıcının son tercihi ise yalnız DXF.

---

## 1. Yetenek haritası

Olgunluk ölçeği:
- **G (genel):** parametreyle başka projede kullanılabilir.
- **Ö (projeye özel):** betik o projenin koordinatlarına bağlı; yeni projede kopyalanıp elle uyarlanır.
- **A (arşiv):** girdisi depoda yok, yeniden çalıştırılamaz.

### 1.1 Çekirdek (her hattın altında)
| Modül | İş | Giriş → Çıkış | Olgunluk |
|---|---|---|---|
| `dxfparse.py` | Toleranslı DXF okuyucu, INSERT açma | DXF → `(blocks, ents)` flat.pkl (`ENC='cp1254'` sabit; utf-8 için kod değişikliği gerekir) | G |
| `arch.py`, `p2/gp.copy_arch`, `p3/et._clean` | Mimariyi temizleyip tek kalem MIMARI yapar | flat → kayıt | G/Ö |
| `rooms.py`, `p3/rooms.py`, `voyap/tes/mahal.py`, `odaplan.py` | Raster yöntemiyle mahal poligonu ve kapı bulma | duvar çizgileri → mahal + kapı | G (4 ayrı sürüm) |
| `router.py`, `p2/router.py`, `voyap/route.py`, `voyap/tes/ag.py` | A* boru güzergâhı (duvar dibi; kolon, kapı ve oda kaçınma), ağaç ve aşağı akış yükü | ızgara → polyline | G (aynı adla iki farklı sürüm var) |
| `cad.py` | Kayıt tabanlı çizim + gerçek semboller (WC, lavabo, duş, eviye, kombi, kollektör, vana, çek valf, pislik tutucu, sayaç, pompa, membranlı tank, dalgıç pompa, rögar, YB, havalık, TK, HEXTAG) | → `cad.R` kayıtları | G |
| `mtyblk.py`, `blklib.py` + `kutuphane/ROTAS_2_MTY_BLOKLARI_*.tar.xz` (~305 blok DXF, `/tmp/claude-0/blk`) | MTY bloklarını gerçek INSERT + öznitelik olarak yerleştirir | blok adı → INSERT | G |
| `voyap/tes/ulabel.py` | MTY dinamik blokları (`*U`) ham DXF'ten okuyup geri yazar | kullanıcı DXF → INSERT+ATTRIB | G |
| `emit.py`, `p2/emitp.py` | Kayıt → DXF (ezdxf) → DWG (ACadSharp AC1032; yedek mkdwg R2000) → geri okuma kontrolü; her paftaya `ROTAS_PAFTA` sınır bloğu | R.pkl → .dxf/.dwg | G |
| `p2/xcheck.py`, `p2/tcheck.py`, `cg2_check.py`, `gungoren/kolon_kontrol.py`, `voyap/kontrol.py`, `voyap/tes/kontrol_tes.py` | Kesişme + köprü, WIPEOUT maskesi, yazı çakışması, kolon/perde kesişimi, boşta uç | kayıt/DXF → rapor/düzeltme | G (6 ayrı kontrol, tek komut yok) |
| `prev.py`, `pdf*.py`, `p2/pdfp.py`, `voyap/pdf_tum.py` | matplotlib önizleme PDF | R.pkl/DXF → PDF | G |
| `araclar/rotasdwg` (C#, ACadSharp) | DXF → DWG AC1032; `PAFTA-SINIRI` katmanını çizilmez yapar; geri okuma sayımı | .dxf → .dwg | G |

### 1.2 Konut / ofis sıhhi + ısıtma (p2, p3)
| Pafta/hesap | Modül | Not |
|---|---|---|
| Kat planı sıhhi (temiz/sıcak/pis, kolon no, Ø/SB ve inç/YB etiketleri) | `p2/gp.py` (pipe, kolon_pis/temiz, balloon, cap_*) + proje betiği | Islak hacim, armatür ve kolon yerleri betikte elle |
| Temel/altyapı planı (kolon dipleri, rögar R1..Rn, PB, SASKİ) | `tb.temel`, `st.temel`, `et._alt_route` | Ö |
| Çatı planı, yağmur inişleri (cepheye yaslı) | `gp.yb_on_facade`, `*.cati`, `*.yagmur_kat` | Ö |
| Açılımlı **tek** sıhhi kolon şeması (bodrum/hidrofor/terfi destekli) | `p2/gsheet.sihhi_sema` | G (girdi sözlüğü ile) |
| Yağmur şeması + hesap kutusu | `gsheet.yagmur_sema/yagmur_hesap` | G |
| Lejant, notlar, antet, pafta çerçevesi | `gsheet.lejant/notlar/antet/frame` | Lejant **sabit liste**; çizimdeki bloklardan üretilmiyor |
| Yerden ısıtma: salyangoz serpantin, kesişmesiz bağlantı ayakları | `spiral3.bifilar`, `p2/gufh.py`, `p3/et.py` | G/Ö. Meander (ORNEK_DUZEN tarzı) yok |
| Yerden ısıtma kolon şeması, devre çizelgesi, U tablosu | `p2/gheatsheet.py` | G |
| Isı kaybı (TS 2164 şablon yöntemi) | `p2/gheat.py`, `cg2_heat.py` | Mahal verisi betikte |
| Kombi pompası, genleşme tankı, PEX kangal | `p2/ghidrolik.py` | G |
| Split klima ısı kazancı + seçim + plan sembolleri | `p2/gklima.py` (+ `psychrolib`) | G |
| Excel (örnek yerden ısıtma şablonu, formüller korunur; klima, yağmur, hidrofor, kombi sayfaları, logo temizliği) | `p2/gexcel.py`, `*_excel.py` | G |
| Projeler | `p2/tb.py` (Tuncay Bulut), `p2/st.py` (Sinem Turhan), `p3/et.py` (Emine Tunçel) | Mimari DWG + teslim depoda → **yeniden üretilebilir** |
| Eski projeler | `cg_*`, `cg2_*` (Cafer Göktaş), `build.py` + `design.py` + `types_def.py` (SA PROFİ) | A (mimari girdisi depoda yok) |

### 1.3 Ticari/merkezi sistem (VOYAP) — `motor/voyap`
| İş | Modül | Not |
|---|---|---|
| Sprinkler boru ağacı (A*, kolonlar yasak), çap = aşağı akış başlık sayısı (Aselsan tablosu), köprüler | `route.py`, `plans.py` | Başlıklar **kullanıcının MTY dosyasından** okunuyor; otomatik başlık yerleşimi yok |
| Hidrolik (TS EN 12845, HW C=120, en elverişsiz alan) | `hidro.py` | G'ye yakın |
| Yangın kolon şeması, lejant (Aselsan sembolleri `asel_sym.pkl`), ekipman listesi, notlar | `sema.py`, `leg_extract.py`, `lib.py` | Ö |
| Yangın dolabı, kat kontrol istasyonu, itfaiye bağlantısı, pompa dairesi + depo | `plans.py` | Ö |
| Sıhhi: koridor ana hatları, sayaç dolabı, 3 borulu sıcak su, termosifon iptali, pis su kolon noktası (`piscol2`) | `tes/sihhi.py`, `yerlesim.py`, `termo.py`, `piscol2.py` | Ö (kurallar genel) |
| Tek sıhhi şema (MTY bloklu) + numaralı ekipman listesi | `tes/sema_sihhi.py` | G'ye yakın |
| Ofis yerden ısıtma (salyangoz, ≤80 m, kapıdan ayak), dükkân radyatörü, kalorimetre, kazan dairesi | `tes/yi.py`, `isitma.py`, `alt.py` | Ö |
| Otopark egzoz/taze hava, sığınak, kazan dairesi menfezleri (basit kanal) | `tes/hava.py` | Ö |
| Mekanik hesaplar (ısı kaybı, kazan, boyler, pompa, genleşme, baca, temiz/pis su, hidrofor, depo, otopark, sığınak) + Excel | `tes/hesap.py`, `xl_tes.py`, `yi_excel.py`, `voyap/xl.py` | G'ye yakın (girdi `veri.py`'de) |
| Birleştirme + SCOTT- öneki | `main_tum.py` (`scott()`) | A (`/tmp/claude-0/vy/sih.dxf` depoda yok) |

### 1.4 Ekipman, kazan dairesi, yağmur suyu
| İş | Modül | Not |
|---|---|---|
| 1/50 ekipman kütüphanesi: plan/ön/yan görünüş. Kombi, duvar ve yer kazanı, boyler, genleşme, denge kabı, inline pompa, kollektör, eşanjör, yerden ısıtma kollektörü, pompa modülü, vana/flanş/çek valf/eksantrik redüksiyon | `ekipman.py`, `ekip_sheets.py` | G |
| Kazan dairesi + depo/hidrofor PLAN ve ŞEMA | `p4/kd.py`, `p4/xl.py` | Ö: 6×115 kW, 700 kW eşanjör, 7×1000 L **sabit**; çıktı `proje/kazan_dairesi_tipik` |
| Yangın pompa grubu cihaz listesi tablosu | `yangin_pompa/cihaz_listesi.py` | Ö (değerler kodda) |
| Yağmur suyu sarnıcı ekleri (vortex filtre, dalgıç pompa, hidrofor…) | `gungoren/ys_ciz2.py`, `xl.py` | Ö; sembolleri `cad.py`'dekilerin ayrı kopyası |

### 1.5 Hesap modülleri (çizimsiz veya tablo DXF)
| Modül | Giriş | Çıkış | Olgunluk |
|---|---|---|---|
| `hesaplar_sema/hesap.py` + `dxf_tab.py` | Kolon şeması DXF + HESAPLAR.dwg OLE Excel (`/tmp/claude-0/hs/*`) | HESAPLAR_SIHHI.xlsx + DXF tablo (MTY-HESAP) | A (girdi yok) |
| `isitma_hesap/isitma_hesap.py`, `hesap_dxf.py`, `isitma_dxf.py`, `oleext.py` | Radyatör seçim xlsx, hesaplar DWG | ISITMA_HESAPLARI xlsx/dxf, tablo DXF (ROTAS-HESAP-*) | A |
| `izoder_rapor/rapor.py ISI_KAYBI.xls RADYATOR.xlsx cikti.pdf [blok]` | İki Excel | İZODER düzeninde PDF | **G (CLI'li)** |
| `siginak/siginak.py` | Alanlar kodda | Sığınak havalandırma DXF (ROTAS-HESAP-*) | Ö |
| `asansor/asansor_hesap.py` | `Asansor(...)` parametreleri | MMO trafik, eski TS, kuvvet, halat, motor, EN 81-20/imar kontrol metni | **G** |

### 1.6 Asansör avan seti (en olgun hat)
`asansor_cizim.py <proje.json> <çıkış>` → R12 DXF (`dxfyaz.py`, bağımlılıksız) + ozalit PDF + hesap txt. Ardından `r12_to_dwg.py` → AC1032. MRL ve makine daireli, kapak şablonu, elektrik detayları, yerleştirme/sıkıştırma (`yerlestir`) içerir. Ölçü araçları: `araclar/asn_kuyu_bul.py`, `asn_olc.py`, `asn_olcu_oku.py`, `asn_kesit_olc.py`, `asn_sablon_cikar.py`. Örnek girdiler: `proje/korucuk_asansor/korucuk_[A-D].json`, `guven.json`, `tunce.json`.

### 1.7 AutoCAD içi araçlar ve referanslar
- LISP: `BPDF` (ROTAS_PAFTA ile toplu PDF), `TOTLEN`, `TAGDEVICES`, `SPRINKLERLAYOUT` (`araclar/autocad_lisp`).
- Referans setler: `kutuphane/ornek_mekanik` (Aselsan Akyurt OPAK 8 DWG, Ada Hayat 11 DWG; lejant/şema/önizleme/CSV), `ornekler/new_block.dxf.xz` (istenen düzen), `ornekler/asansor/sablon`.

---

## 2. Kurallar arası çelişkiler ve bayat kısımlar

### 2.1 Çelişkiler (karar verilmesi gerekenler)
| # | Konu | Kaynak A | Kaynak B | Öneri |
|---|---|---|---|---|
| 1 | **Katman öneki** | README "Tüm dosyalarda katman adları `SCOTT-`" (13.10); ASANSOR §11 "SCOTT- (eski ASN-)"; `voyap/main_tum.scott()` | En son işler `ROTAS-` kullanıyor: commit 7c33358 "ROTAS- katmanları" (14.10), isitma_hesap README "kullanıcı kalem adlarının ROTAS- ile başlamasını istiyor", `siginak.py`, `cihaz_listesi.py` (`ROTAS-HESAP-*`), `emit.py` (`ROTAS-PAFTA-SINIRI`). Ayrıca `hesaplar_sema/dxf_tab.py` → `MTY-HESAP`; beceri → MTY-/MEP-; p2/p3 hatları (emitp) hiç önek uygulamıyor | Kullanıcıya tek soru: önek **ROTAS-** mi? MTY- katmanları da öneklenecek mi? Karar tek bir `katman_profili` modülüne yazılsın, README ve ASANSOR §11 güncellensin. |
| 1b | Önek ile MTY uyumu | README: "MTY blokları patlatılmaz… kullanıcı MTY programında çapları güncelleyebilmeli" | `scott()` tüm `MTY-*` katmanlarını `SCOTT-MTY-*` yapıyor | MTY CAD katman adına bakıyorsa düzenleme özelliği bozulabilir (**doğrulanmadı**). Kullanıcının MTY'sinde öneklenmiş bir dosyayla denenmeli. |
| 2 | **Teslim biçimi** | CLAUDE.md md.5: DWG (ACadSharp) + DXF + önizleme PDF + Excel; README: "DWG ile birlikte DXF"; beceri §9/§11: DWG+DXF+PDF+XLS | Kullanıcı tercihi (son): mekanik çizim teslimlerinde **yalnız DXF**, DWG ve önizleme PDF yok; ASANSOR §12: "yalnız DXF" | CLAUDE.md md.5 ve README "DWG ile birlikte DXF" maddesi "yalnız DXF (+ hesap Excel)" olarak güncellensin. DWG üretimi isteğe bağlı bayrak olsun. |
| 3 | DWG yazma yolu | Beceri §9: kendi `dwg_add_*` R2000 yazıcısı, DXF AC1024 | CLAUDE.md: ACadSharp AC1032. ASANSOR §8: "DWG yazıcı kurulamadı" (bayat); §11: `r12_to_dwg.py` | Beceri §9 ve ASANSOR §8 güncellensin. |
| 4 | **Yerden ısıtma tarzı** | README GENEL: Emine Tunçel `p3/et.py` salyangoz + kapıdan geçen ayaklar | ORNEK_DUZEN: **meander** (gidiş-dönüş U), hol/antre 15 °C ısıtılır; ARASTIRMA "meander eklenecek". Ayrıca Emine Tunce'nin 13.10 yeniden üretimi kullanıcı isteğiyle geri alındı (59f561c) → "onaylı" sürüm 720903a mı? | Kullanıcıya sorulsun: konutta salyangoz mu meander mı? "Ortak alanlar ısıtılmaz" kuralı ile "daire içi hol ısıtılır" ayrımı açık yazılsın. |
| 5 | Su deposu hacmi | README + beceri: ≤10 BB 3 m³, her ek BB +0,5 m³ | `hesaplar_sema` README: depo = günlük ihtiyaç (daire × 4 kişi × 100 l); B1-B2-B3'te 16 m³ | Konut kuralı ile hesap yöntemi için bir öncelik maddesi yazılsın (örn. "kullanıcı ton verdiyse o, yoksa BB kuralı"). |
| 6 | YB değerleri | Beceri TS 1258 Ç.15: lavabo 0,5, ÇM/BM 1, termosifon 2,5; hesap kütüphanesi "ROTAŞ şemasında duş/ÇM/BM 1,0" | `hesaplar_sema` şablonu: lavabo 0,75, eviye 1, rezervuar 0,5, duş 2,5, çamaşır 1,5, şofben 1 | Tek YB tablosu (`kutuphane/tablolar/yb_sb.json`) ve hangi işte hangisi geçerli olduğu yazılsın. |
| 7 | Otopark havalandırması | README (VOYAP): 4 hava değişimi + duman tahliyesi 10 hava değişimi | Hesap kütüphanesi: en büyüğü (6 hava değişimi / CO / duman 10, **2000 m² üstünde**) | README kuralı kullanıcınındır. Kütüphaneye "ROTAŞ: 4 / 10" notu eklensin. |
| 8 | Sığınak | `siginak/README`: net alan × 3,00 × 4/h, egzoz %10 eksik, >100 m² duman | Hesap kütüphanesi: TS 3419 kişi başı koruma havası 1,8/3/4,5 m³/h | Kullanıcı yöntemi öncelikli; kütüphaneye çapraz başvuru notu. |
| 9 | Yağmur suyu temel planında | README: altyapı yok, inişler zemin katta biter | Beceri §10: temel planında yağmur inişleri + "YAĞMUR SUYU KANALINA GİDER" okları; ORNEK_DUZEN: yağmur şeması + "KANALINA GİDER" | "Ok/not var, hat/kanal yok" diye tek cümleyle netleştirilsin. |
| 10 | Antet onay notu | Beceri §1: 14.06.1999 RG 23725 / 08.05.2000 RG 24043 notu standart | ASANSOR §5: bu atıf eskidir | Mekanik antetler için de güncel atıf kullanıcıya sorulsun. |
| 11 | Asansör halatı | `asansor_hesap.py` varsayılanı 4 × Ø10 (çıktı: "4 HALATLI"); ASANSOR §3 "4 halat" | §11 MRL kuralı: 7 × Ø6,5 | MRL varsayılanı koda alınsın; makine daireli için kural yazılsın. |
| 12 | Sıhhi şema | README: temiz + sıcak + pis tek şema | `voyap/tes/sema_tes.py` içinde ayrı `sihhi_sema` + `pis_sema` fonksiyonları hâlâ duruyor (`sema_sihhi.py` onların yerini aldı) | Eski fonksiyonlar kaldırılsın veya "kullanılmaz" diye işaretlensin. |
| 13 | Temiz su renkleri | Beceri §3: temiz su yeşil/kırmızı | ORNEK_DUZEN: soğuk mavi, sıcak kırmızı kesikli, etiket yeşil | ORNEK_DUZEN geçerli; beceri düzeltilsin. |
| 14 | Hesap tablosu biçimi | isitma README: beyaz yazı + kırmızı çerçeve | `siginak.py` çerçeve rengi 1, `cihaz_listesi.py` çerçeve rengi 4 + ayrı BASLIK katmanı; `dxf_tab.py` MTY-HESAP | Tek `hesap_tablo.py` yardımcısında birleştirilsin. |
| 15 | Referans set adı | Beceri: "Aselsan Teknopark İstanbul 13 paftalık" | Kütüphane: "ASELSAN Akyurt-1 OPAK, 8 DWG" (Ankara) | İki ayrı set olabilir. Beceri metni kütüphaneyle eşlensin. |

### 2.2 Bayat / eksik belge ve kod
- **README içerik tablosu eski:** yalnız çekirdek, p2, p3 anlatılıyor. `voyap/`, `p4/`, `asansor/`, `hesaplar_sema/`, `isitma_hesap/`, `izoder_rapor/`, `siginak/`, `yangin_pompa/`, `gungoren/`, `ekipman.py` yok. "proje/" satırında yalnız Tuncay Bulut ve Sinem Turhan yazıyor (bugün 13 klasör var). "Kütüphane: /tmp/claude-0/blk" geçici bir yol.
- **Kurulum:**
  - `kurulum.sh` `set -e` ile `tar -C /` çalıştırıyor. CLAUDE.md md.7'deki `/home/claude/libredwg` yedeği betikte yok, yani tar başarısız olursa betik durur. (Şu an `/usr/local/bin/dwg2dxf` kurulu.)
  - Betik, README'deki mimari `dwg2dxf` dönüşümünü ve `flat.pkl` üretimini yapmıyor.
  - `dxfparse.py` CLI'sinde kodlama seçeneği yok (`ENC` sabit cp1254). Tuncay Bulut için utf-8 gerekiyor.
- **Sabit yollar:** ~90 dosyada `/tmp/claude-0/...` ve `/home/claude/nb` sabit. Ara dosyalar (`*_R.pkl`, `*_calc.pkl`, `yi_cache.pkl`, `et_heat_cache.pkl`) depoda tutulmuyor.
- **Arşivde kalan işler (A):** VOYAP (`sih.dxf`, `heads.pkl`, `mimT.pkl`…), Cafer Göktaş, SA PROFİ, şema HESAPLAR (`ole0.cfb`, `inis.pkl`, `fix.pkl`), ısıtma HESAPLAR (`rad.xlsx`), İZODER girdi XLS'leri. Girdi dosyaları `proje/<iş>/girdi/` altına konmadıkça bu işler yeniden üretilemez.
- **Ölü / yinelenen kod:**
  - `motor/router.py` ve `p2/router.py` aynı adlı, farklı içerikli iki dosya.
  - `voyap/tes/rooms.py` ile `odaplan.py` birebir aynı.
  - `pdf.py`, `cg_pdf.py`, `cg2_pdf.py` üç kopya.
  - `cg_*` modüllerinin yerini `cg2_*` aldı.
  - `test1-5.py`, `test_yi.py`, `rp.py`, `rp2.py`, `rn.py`, `t1.py`, `t_rooms.py`, `fitvaz.py`, `grid.py`, `rcg.py` tek seferlik yardımcılar.
  - `gungoren/ys_ciz2.py` kendi VANA/POMPA/MANOMETRE kopyalarını içeriyor.
- `asansor_cizim.py` başlık açıklaması "makine dairesiz (MRL) çift asansör" diyor; kod artık makine daireli ve tek asansörü de çiziyor.
- Emine Tunce geri almasında `araclar/scott_katman.py` ve `ust_uste_kontrol.py` de silindi. Genel bir "üst üste binme" kontrol komutu kalmadı (yalnız `xcheck`/`tcheck`).
- `__pycache__` dosyaları depoda (5 dosya), `.gitignore` yok.
- Otomatik test/regresyon yok. Teslim kontrolleri altı ayrı betiğe dağılmış durumda.
- `ARASTIRMA_GITHUB_AUTOCAD.md` "Sıradaki geliştirmeler" listesindeki 2. madde (ORNEK_DUZEN düzeni) ve 3. madde (meander) hâlâ açık; durumları işaretlenmemiş.

---

## 3. Eksik yetenekler (öncelik sırasıyla)

**Öncelik 1 — her işte zaman kazandıracaklar**
1. **Genel proje girdisi + tek komut hattı.** Asansördeki JSON modeli sıhhi/ısıtma için de kurulmalı: `proje.json` (katlar, kaynak kaydırmaları, kotlar, BB listesi, ısıtma tipi, teslim profili) → `rotas yap proje.json`. Bugün her yeni proje için 800–1200 satırlık bir betik elle yazılıyor.
2. **Mimari tanıma.** Kat planlarını model uzayında otomatik bulma (başlık yazısı + çerçeve), betonarme kolon/perde katmanı eşleme, ıslak hacim ve tefriş tanıma (WC, lavabo, duş, eviye blokları), kapı yönü. Mahal bulma kodu var ama dört kopya halinde; tek modülde birleşmeli.
3. **Teslim profili + birleşik kontrol.** Tek modülde toplanmalı:
   - katman öneki
   - DXF-only / DWG bayrağı
   - MTY bloklarının patlatılmadığı kontrolü
   - kolon kontrolü, kesişme/köprü, yazı çakışması, boşta uç, çapsız boru
   - tek bir `teslim_kontrol.py` raporu
4. **Otomatik lejant + adet/metraj.** Lejant çizimde kullanılan bloklardan üretilmeli (bugün sabit liste). Vitrifiye/ekipman adet tablosu ve çap bazında boru metrajı Excel'e yazılmalı (TOTLEN'in motor içi karşılığı).

**Öncelik 2 — iş yelpazesini genişletecekler**

5. **Sprinkler otomatik yerleşim.** Tehlike sınıfına göre (hafif 21 m²/4,6 m, orta 12 m²/4,0 m) başlık ızgarası, duvara ≥0,5 m, kiriş/kolon kaçınma. Ardından mevcut `route.py` + `hidro.py` hattına bağlanmalı. Bugün başlıklar kullanıcının dosyasından okunuyor.
6. **Parametrik kazan dairesi / ısı merkezi şeması.** `p4/kd.py` + `ekipman.py` üzerine JSON girdili üretici kurulmalı: kazan adedi ve gücü, kaskad, denge kabı/eşanjör, boyler/akümülasyon, pompalar, genleşme; plan + şema + ekipman listesi. Bugün değerler sabit (6×115 kW).
7. **Havalandırma kanal çizimi.** Çift çizgili kanal, debi → ebat (hız veya basınç sınırı), dirsek/redüksiyon/pantolon, damper, menfez, flex; otopark jet fan yerleşimi; kanal metrajı. Bugün `hava.py` içinde yalnız basit `duct` var.
8. **Genel sembol kütüphanesi.** Şu kaynaklar tek katalogda birleşmeli: `cad.py` sembolleri, `ekipman.py`, MTY tar (~305 blok), `asel_sym.pkl` (yangın), `kutuphane/asansor/semboller.json`, `ys_ciz2` kopyaları. Hepsi tek ad sözlüğü + önizleme paftası ile sunulmalı; TS 2164 sembolleri eklenmeli.
9. **Radyatörlü ısıtma planı + kolon şeması (genel).** Bugün yalnız hesap (`isitma_hesap`, `izoder_rapor`) ve VOYAP dükkân radyatörü var. Radyatör yerleşimi (pencere altı), kolon şeması "xxxW-DN15" etiketleri ve kritik devre eksik.

**Öncelik 3 — yeni disiplinler**

10. **Doğalgaz iç tesisat projesi:** kolon/izometri, basınç kaybı (21 mbar, ≤1,8 mbar), baca. MTY'de de bu modül yok; ticari fırsat olabilir. Gaz dağıtım şirketi şartnameleri ayrıca incelenmeli.
11. **VRF/VRV ve fancoil:** beceri §6'da tarif var, motorda yok.
12. **Yangın dolabı/hidrant genelleştirmesi** (VOYAP'ta projeye özel) ve **yangın algılama** (zon/sonlandırıcı).
13. **Mimariden otomatik ısı kaybı:** U·A·ΔT doğrudan mahal tanımadan hesaplanmalı; TS 825 / BEP raporu bağlantısı kurulmalı.
14. Fosseptik, havuz ve sığınak **çizimleri:** hesapları var, çizimleri kısmi.
15. **Regresyon testleri:** örnek projeler için katman/blok/varlık sayımı karşılaştırması.

---

## 4. Deneme projesi önerisi

Aşağıdaki sıra önerilir: önce ortamı ve regresyonu doğrula, sonra yeni projede uçtan uca dene.

### Adım 1 — Sinem Turhan regresyonu (ortamın ve p2 hattının doğrulanması, ~30 dk)
Neden: mimari DWG ve onaylı teslim (DXF/DWG/PDF/Excel) depoda var, README komutları bu proje için yazılmış.
```bash
cd /home/claude/rotas-cizim-motoru && bash kurulum.sh        # tar -C / hata verirse CLAUDE.md md.7
mkdir -p /tmp/claude-0/p2/out
cp proje/sinem_turhan/mimari.dwg /tmp/claude-0/p2/st.dwg
LD_LIBRARY_PATH=/usr/local/lib dwg2dxf -y -o /tmp/claude-0/p2/st.dxf /tmp/claude-0/p2/st.dwg
cd /home/claude/nb && python3 dxfparse.py /tmp/claude-0/p2/st.dxf /tmp/claude-0/p2/st.dxf.flat.pkl   # ENC=cp1254 (st için doğru)
cd /home/claude/nb/p2 && python3 st.py && python3 st_excel.py
python3 emitp.py /tmp/claude-0/p2/st_R.pkl /tmp/claude-0/p2/out/SINEM_TURHAN_SIHHI_ISITMA
python3 pdfp.py  /tmp/claude-0/p2/st_R.pkl /tmp/claude-0/p2/out/SINEM_TURHAN_ONIZLEME.pdf
```
Karşılaştırma ölçütü: `proje/sinem_turhan/SINEM_TURHAN_SIHHI_ISITMA.dxf` ile yeni DXF arasında katman bazında varlık sayısı, INSERT/öznitelik sayısı (rotasdwg çıktısı) ve `xcheck`/`kolon_kontrol` sonuçları (`python3 /home/claude/nb/gungoren/kolon_kontrol.py <dxf>`).

### Adım 2 — Korucuk asansör regresyonu (tek komutluk hat)
```bash
cd /home/claude/rotas-cizim-motoru     # json içindeki flat yolu depo köküne göre
python3 motor/asansor/asansor_cizim.py proje/korucuk_asansor/korucuk_A.json /tmp/claude-0/deneme/korucuk_A/
```
Çıktı `proje/korucuk_asansor/teslim/KORUCUK_A_BLOK_ASANSOR_AVAN.dxf` ve `_HESAP.txt` ile karşılaştırılır. Kullanıcı tercihi gereği DWG adımı (`r12_to_dwg.py`) atlanabilir.

### Adım 3 — Uçtan uca deneme: `ornekler/new_block.dxf.xz` (önerilen asıl deneme)
Neden:
- Kullanıcının "istediğim düzen" dediği set.
- Mimari ile tam MTY mekanik çizimi aynı dosyada (AC1027, 35 479 varlık). Bu sayede motorun çıktısı kullanıcının kendi çizimiyle karşılaştırılabilir; elimizde "altın referans" olur.
- Katman dağılımı:
  - Mimari tek katmanda: `MKDU0` (30 588 varlık).
  - Mekanik: `MTY-VANA` 659, `MTY-SOGUKSU-BORU` 279, `MTY-PISSU-BORU-TAVANDAN` 188, `MTY-SICAKSU-BORU` 154, `MTY-PEX-BORU` 81, `MTY-ROGAR` 63, `MTY-YAGMUR-BORUSU` 30 ve `M-HVAC-*`, `M-EQPT`.

Akış:
1. `xz -dc ornekler/new_block.dxf.xz > /tmp/claude-0/ornek/new_block.dxf` (kurulum.sh bunu zaten yapıyor).
2. **Yalın mimari çıkar:** `MTY-*`, `M-*`, `RAST-*`, `TEM.SU` katmanları süzülüp `new_block_mimari.dxf` elde edilir (ezdxf ile 10 satırlık betik). Ardından `dxfparse.py` ile flat.pkl üretilir.
3. **Yeni proje betiği:** `motor/p5/nb.py` dosyası `p2/st.py` şablonundan kopyalanır. Z+2, 9 daire; kat kaydırmaları ve pencereler `araclar/dxf_pencere.py` / `grid.py` ile okunur. Pafta sırası ORNEK_DUZEN'deki gibi olur: antet → yerleşim 1/250 → temel → her kat ayrı → tek açılımlı şema + rögar şeması + yağmur şeması → WC havalandırma + SIHHİ DETAYLAR; 2. sırada ısıtma.
4. `emitp.py` → DXF (teslim profili: yalnız DXF, ROTAS-/SCOTT- kararına göre önek).
5. **Ölçüm:** üretilen ile orijinal arasında rögar sayısı, kolon sayısı ve yerleri, Ø/SB ve inç/YB etiket değerleri, depo hacmi, yerden ısıtma devre sayısı ve uzunlukları (orijinaldeki MTY-ETIKET öznitelikleri `ulabel.py` ile okunur). Fark tablosu kullanıcıya gösterilir.

Risk ve not: mimari tek katmanda (`MKDU0`) olduğu için duvar, kolon ve tefriş ayrımı geometriden yapılmalı. Mahal tanıma modülleri (`rooms.py`) burada gerçekten sınanmış olur; bu da 3. bölümdeki 1. ve 2. maddelerin (genel girdi + mimari tanıma) ilk uygulaması olur.

Alternatif: Emine Tunce (`proje/emine_tunce/mimari.dwg`, `p3/et.py`) teknik olarak hazır. Ancak kullanıcı 13.10'daki mekanik denemeyi geri aldırdığı için kullanıcı istemedikçe önerilmez.

---

## 5. Kullanıcıya sorulacaklar (karar listesi)
1. Katman öneki **ROTAS-** mi, **SCOTT-** mi? `MTY-*` katmanları da öneklenecek mi (MTY CAD uyumu)?
2. Teslim bütün mekanik işlerde **yalnız DXF + hesap Excel** mi? (CLAUDE.md güncellenecek.)
3. Konut yerden ısıtması **salyangoz** (Emine Tunçel) mu, **meander** (new_block) mu? Daire içi hol ısıtılacak mı?
4. Depo hacmi kuralı: BB kuralı mı, günlük ihtiyaç mı (hangi durumda hangisi)?
5. Antetteki 1999/2000 RG onay notu güncellenecek mi?
6. Arşiv işlerinin girdi dosyaları (VOYAP, HESAPLAR, İZODER) yeniden üretilebilirlik için depoya konsun mu?
