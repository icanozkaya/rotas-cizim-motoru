# 02 — İnternette Yayınlanmış Türk Mekanik Tesisat Proje Örnekleri

Araştırma tarihi: 14.10.2026. Yöntem: WebSearch/WebFetch (shell'den internet yok).
Amaç: Çizim motorunun (ROTAŞ / MTY CAD standardı) etiket, kolon şeması, tablo, lejant ve antet kararlarını yayınlanmış Türk örnekleriyle karşılaştırmak.

> **Önemli sınırlama:** Gerçek proje paftalarının çoğu DWG (arge7.com, tesisat.org Google Drive) ya da JS ile korunan Scribd/SlideShare sayfalarında. WebFetch bunları metin olarak okuyamadı. Bu yüzden somut etiket alıntıları ağırlıklı olarak MEB/MEGEP modüllerinden, üniversite ders notlarından ve idare şartnamelerinden geliyor. **DWG örnekleri listelendi ama içerikleri doğrulanmadı.** Kullanıcı bu DWG'leri indirip depoya koyarsa `ezdxf`/LibreDWG ile katman, blok ve etiket analizi yapılabilir.
>
> **Kaynakların durumu:** Okunan kaynakların hiçbiri ROTAŞ'ın kalıcı kurallarıyla (README "Kalıcı kurallar") çelişki doğurmuyor. Kullanıcının MTY şablonu her zaman önce gelir. Buradaki bilgiler yalnızca kıyas ve eksik tamamlama içindir.

---

## A. En değerli 10 kaynak (öncelik sırasıyla)

| # | Kaynak | Tür | Neden değerli |
|---|---|---|---|
| 1 | [MEB İEGM — Eğitim Yapılarında Mekanik Proje Hazırlanması Genel İlkeleri (2025)](https://iegm.meb.gov.tr/meb_iys_dosyalar/2025_08/04151916_egitimyapilarindamekanikprojehazirlanmasigenelilkeleri.pdf) | İdare çizim şartnamesi (tüm disiplinler) | Radyatör etiket kuralı, ısıtma gidiş/dönüş rengi, yangın kolonu adı (YG1), lejant notları, ölçekler, .xlsx teslim; en somut güncel kural seti |
| 2 | [MEB mevzuat 2304 — İnşaat ve Emlak GM proje esasları](https://mevzuat.meb.gov.tr/dosyalar/2304.pdf) | İdare yönergesi | 1 numaralı kaynağın madde numaralı (1.2.x) eski/resmî metni |
| 3 | [MEGEP — Sıhhi Tesisat Projesi modülü](https://megep.meb.gov.tr/mte_program_modul/moduller_pdf/S%C4%B1hhi%20Tesisat%20Projesi.pdf) | Ders modülü (sıhhi proje) | Kolon şeması çizim adımları, TS1/P1 kolon adları, kalem kalınlıkları, 60 mm kat aralığı, YB/YD etiketleri, hesap çizelgesi sütunları |
| 4 | [MEGEP — Bilgisayarda Doğal Gaz Tesisat Projesi](https://megep.meb.gov.tr/mte_program_modul/moduller_pdf/Bilgisayarda%20Do%C4%9Fal%20Gaz%20Tesisat%20Projesi.pdf) | Ders modülü (doğalgaz) | Üç satırlı boru etiketi (m³/h – m – DN), cihaz etiketi (Q kcal/h), 30° izometri, kat adı ve ölçek sağ altta |
| 5 | [KTÜ (E. Baydar) — Sıhhi Tesisat Ders Notu 4 (pis su)](https://ebaydar.ktu.edu.tr/files/sihhi_4.pdf) | Üniversite ders notu | Pis su boru planında çap ve SB'nin birlikte yazıldığı gerçek etiket örnekleri ("100", "12 SB", "111 SB", "P 1") |
| 6 | [arge7.com — Autocad Mekanik Tesisat Örnek Projeler (100 DWG)](https://www.arge7.com/altkategoridosyalar.php?kat=38) | İndirilebilir DWG arşivi | Sıhhi, kalorifer (kaskad, kolektörlü, kalorimetreli), döşemeden ısıtma, sprinkler, doğalgaz, VRF, havuz örnekleri ve **mekanik çizgi grubu lejantı** |
| 7 | [Pdfcoffee — Yangın Söndürme Tesisatı ve Duman Tahliye Projesi (MMO denetim esasları)](https://pdfcoffee.com/yangn-sndrme-tesisat-ve-duman-tahliye-projesi-pdf-free.html) | Oda proje esasları | Yangın paftalarında zorunlu bilgi bloğu, "HİDROLİK HESAPLAR BİLGİ TABLOSU", kolon adları ve kotlu izometri |
| 8 | [İlbank — Katı Atık Tesisleri Mekanik Tesisat Proje Teknik Şartnamesi 2022](https://www.ilbank.gov.tr/storage/uploads/files/kati_atik_tesisleri_mekanik_tesisat_proje_sartnamesi_1660053353.pdf) | İdare şartnamesi | Pafta numaralama (MEK-01…), antet içeriği, boru cins+çap+kot yazımı, "plan + kolon şeması her bina için" kuralı |
| 9 | [ÇŞB — Mimarlık ve Mühendislik Projelerinin Dijital Olarak Hazırlanması taslağı (2025)](https://webdosya.csb.gov.tr/db/meslekihizmetler/icerikler/cal-stay-taslak-dokumanlar--20251107085546-20251110130354.pdf) | Bakanlık dijital proje standardı taslağı | Mekanik alt disiplin kodları (SHTT, ISTT, YNGT, DGTT…), katman adı şablonu, dosya adlandırma |
| 10 | [tesisat.org — Doğalgaz Tesisat Resimleri](https://www.tesisat.org/dogalgaz-tesisat-resimleri.html) + [Isı İstasyonu Hesabı ve Mekanik Proje Adımları](https://www.tesisat.org/isi-istasyonu-hesabi-ve-mekanik-proje-adimlari.html) | Blog + DWG | Doğalgaz DWG (semboller, standart tablo, proje düzeltme tablosu); ısı istasyonu/kat istasyonu DWG ve örnek şema |

---

## B. Kaynak bazında ayrıntılar

### 1. MEB İEGM — Eğitim Yapılarında Mekanik Proje Hazırlanması Genel İlkeleri
- **URL:** https://iegm.meb.gov.tr/meb_iys_dosyalar/2025_08/04151916_egitimyapilarindamekanikprojehazirlanmasigenelilkeleri.pdf
- **Tür:** Tüm mekanik disiplinler (sıhhi, ısıtma, yangın, havalandırma, doğalgaz, VRF, yağmur suyu).
- **Pafta listesi:** Sabit bir liste yok. Sığmayan çizimler "ilgili paftaların bir kenarında veya ilgili pafta belirtilerek ayrı bir pafta olarak" verilir.
- **Ölçek:** Kat planları "1/50 ölçekli mekanik uygulama projeleri", detaylar "1/20, 1/10, 1/5, 1/1".
- **Katman ve renk:**
  - "Çizimde katmanlar (temiz su, pis su, ısıtma, soğutma, havalandırma, yangın, vb.) ayrı ayrı tanımlanmalıdır."
  - "Isıtma gidiş hatları kırmızı, dönüş hatları mavi renkli çizim ile gösterilebilir."
  - "Yağmurlama (sprink) sistemine ait hatlar (zonlar) farklı katmanda (layerde) ve farklı renkte çizilmelidir."
- **Kat planında gösterim:**
  - Sıhhi: "kolonlara ait numaralandırma yapılmalı ve boru çapları yazılmalıdır"; "Pis su hatlarının eğimleri belirtilmelidir"; akış yönleri gösterilir.
  - Isıtma: "Sıcak su borusu gidiş ve dönüş hatlarının yanına sıcaklıkları, ısı yükleri ve boru çapları yazılmalıdır."
  - **Radyatör etiketi:** "Radyatörün içine mahal numarası ve mahal sıcaklığı" yazılır; "radyatörün üstüne ise radyatör tipi, ısı yükü ve ebatı yazılmalıdır." Radyatör "yerden yaklaşık 10 cm" yükseklikte gösterilebilir.
- **Kolon şeması:** "Cihaz kapasiteleri, boru çapları" gösterilir; "her kat için kot ve kat adedi (zemin kat, 1. kat vb.)" yazılır; kotlar "Su basmandan itibaren … mimari projeden" alınır. Yangın için: "Yangın hatlarına ait kolonlar numaralandırılmalı, her kattaki boru çapları, spring sayıları ve yükleri yazılmalıdır (YG1, YG2, vb.)".
- **Lejant notları (aynen yazılması istenenler):**
  - "Yangın sistemlerine ait tüm tesisatlarda geçici kabul öncesi ön yıkama (flushing) yapılacaktır"
  - "Havalandırma kanallarının imalatları tamamlandıkça zonlar halinde sızdırmazlık ve duman testi yapılmalıdır"
- **Teslim:** Hesap ve metraj dosyaları ".xlsx" olarak; 1 onaylı çıktı + 2 harici bellek kopyası.
- **ROTAŞ'a etkisi:** Radyatör içi/üstü etiket düzeni, `MTY-RADYATOR MAHAL` bloğunun içeriğiyle karşılaştırılmalı. Yangın kolonlarında "YG" öneki ve kat başına "DN + başlık sayısı" yazımı, mevcut kalıcı kuralla (DN + başlık sayısı) uyumlu.

### 2. MEB mevzuat 2304 (İnşaat ve Emlak GM)
- **URL:** https://mevzuat.meb.gov.tr/dosyalar/2304.pdf
- 1 numaralı kaynağın madde numaralı hâli: 1.2.1 (katman, lejant, sembol listesi), 1.2.4 (kolon şemasında kot ve kat adedi), 1.2.8 (sprinkler zon katmanı), 1.2.10 (radyatör ve gidiş/dönüş etiketleri), 1.2.19–20 (.xlsx mahal listesi ve keşif).
- Kontrol listesi hazırlarken madde numaraları referans olarak kullanılabilir.

### 3. MEGEP — Sıhhi Tesisat Projesi modülü
- **URL:** https://megep.meb.gov.tr/mte_program_modul/moduller_pdf/S%C4%B1hhi%20Tesisat%20Projesi.pdf
- **Tür:** Sıhhi (temiz, sıcak, pis, yağmur).
- **Paftalar:** Bodrum kat, zemin kat, normal kat planları (aynı katlar bir kez çizilir) ve kolon şeması.
- **Kat planı hazırlığı:** Mimari kopyalanır ve "iç sıva ve dış sıva çizgileri plandan çıkarılır".
- **Kalem kalınlıkları:** "Mimari planlar 0.2 rapido kalemle çizilir." "Uç malzemeleri 0.5 kalemle çizilir." "Sıcak su boruları 0.3 kalemle ve kesik noktalı çizgi ile çizilir." Kontrol listesinde "Temiz su 0.3, pis su 0.5" geçiyor (modül kendi içinde tutarsız).
- **Kolon şeması kuralları:**
  - Şema, planın ön görünüşüdür. Sağdaki uç malzemesi sağa, soldaki sola yatırılır.
  - "Kat yüksekliği 3 metre olduğu için 1/50 ölçekli şema görünüşünde iki kat aralığı 60 mm olarak gösterilir."
  - Önce pis su ve temiz su kolonları çizilir. "Pis su kolonu çizildikten sonra en üst noktasına kolon numarası yazılır."
  - Soğuk su şeması bodrumdan başlar: şebeke girişi, ana sayaç, kollektör.
  - Havalandırma: "Kolonlar havalandırma boruları vasıtasıyla çatı katına kadar çap değiştirmeden çıkartılır."
  - "Yağış suyu doğrudan pissu tesisatına bağlanmaz."
- **Kolon adları:** Temiz su **TS1, TS2, TS3**; pis su **P1, P2, P3**.
- **Etiket ve yük birimleri:** Temiz suda YB (1 YB = 0,25 l/s), MB (15 mm musluk). Pis suda her uç malzemenin YD değeri üzerine yazılır, boru bölümlerine toplam YD yazılır.
- **Bağlantı çapları:** "Klozet ve hela taşları ø 100'lük PVC boru ile", "Küvetler ve lavabolar ø 50'lik PVC boru ile". Klozet olan kolon, hesap ø70 çıksa da ø100 olur.
- **Boru çapı hesap çizelgesi sütunları:** YB | gerçek boru boyu (m) | boru çapı (mm ve inch) | basınç kaybı (mSS/m) | toplam basınç kaybı. Kontrol satırı: "Emre Hazır Basınç > Toplam Basınç Kaybı".
- **Yağmur borusu kesit tablosu:** Ø50 19,55 cm², Ø70 38,36 cm², Ø100 78,31 cm², Ø125 122,34 cm², Ø150 175,75 cm².

### 4. MEGEP — Bilgisayarda Doğal Gaz Tesisat Projesi
- **URL:** https://megep.meb.gov.tr/mte_program_modul/moduller_pdf/Bilgisayarda%20Do%C4%9Fal%20Gaz%20Tesisat%20Projesi.pdf
- **Tür:** Doğalgaz iç tesisat (AutoCAD ile).
- **Kat planı:** 1/50. "Çizimlerimizin alt sağ kısmında hangi kata ait olduğu ve ölçeği yazmalıdır."
- **İzometri:** "30o açı ile" çizilir; "İzometrik planda ölçek önemli değildir."; "İzometrik plan başlangıcı doğalgaz saati olmalıdır."; "İzometrik planda yazılar birbirleriyle kesişmemelidir."
- **Boru etiketi (her bölüm için üç değer):** şablon "....... m³/h", "....... m", "DN ........."; örnek **"2 m³/h" / "3,2 m" / "DN20"**.
- **Cihaz etiketi:** "Q = ............ kcal/h" (örnek "16335 kcal/h") ve "................. Marka"; havalandırma menfezi "150 cm²"; servis kutusu "S200", "21 mbar", "Yandan Çıkış"; not "KOLON HAVALANDIRMASI MEVCUTTUR".
- **Notlar:** "Ana kesme vanasına koruyucu kabin yerleştirmeyi unutmayınız.", "Her sayaçtan önce bir kapama vanası bulunmalıdır."
- **Malzeme tablosu sütunları:** Seri No | Malzemenin Cinsi | Miktar | Birim | Birim Fiyat | Tutar; altta "İşçilik" ve "Genel Toplam".

### 5. MEGEP / tesisat.org — Doğal Gaz İç Tesisat Resim 1–2 (PDF)
- **URL:** https://www.tesisat.org/dogalgaz-tesisat-resimleri.html (PDF'ler Dropbox'ta, sayfadan bağlantılı)
- Resim-1: TSE tabanlı semboller (boru iniş/çıkış, çap değişimi, T temizleme, akış yönü, vana, regülatör, sayaç, cihaz, baca, fan). Etiket örnekleri: "Açıkta döşenen gaz borusu ve anma çapı", "Örtülü olarak döşenen gaz borusu ve anma çapı", "Tek manşon bağlantılı sayaç(DN 25)".
- Resim-2: Başlık "İZOMETRİK KOLON ŞEMASI". "Maksimum debinin veya tesisata ait parçaların sembollerinin değiştiği yerde ilgili tesisat bölümü biter." Hat tablosu: hat no | DN | L (m) | Q (m³/h) | v (m/s) | R (mbar/m) | R·L | ΣZ | yükseklik kaybı | toplam. Örnek satır: "1 Nulu hat — DN 50, L = 18,8 m, Q = 17,8 m³/h". Cihaz: "Qısıtma=120.000kcal/h", "Qbina=Qkazan+Qmutfak=16,2+1,6→17,8m³/h". Tablo 3.8 "Doğal gaz projesi anteti" (alanları metinde çıkmadı).
- Sayfadaki DWG: semboller, bağlantı/sayaç detayları, "standart tablosu" ve "proje düzeltme tablosu" içeriyor (Google Drive bağlantısı, okunmadı).

### 6. KTÜ (E. Baydar) — Sıhhi Tesisat ders notları
- **Pis su:** https://ebaydar.ktu.edu.tr/files/sihhi_4.pdf
  - Örnek boru planı etiketleri (PDF metninden, sıralı): `100`, `12 SB`, `70`, `4 SB`, `8 SB`, `24 SB`, `36 SB`, `21 SB`, `42 SB`, `63 SB`, `48 SB`, `100 111 SB`, `125`, `P 1`, `P 2`, `P 3`. Yani **çap (mm, Ø işaretsiz) + toplam yük "nn SB"** her boru parçasına birlikte yazılıyor. Bu, ROTAŞ'ın "Ø100 / 25 SB" formatının akademik karşılığı.
  - Plan notu: "Tesisatın yatay ve düşey boruları için belirlenen çap değerleri boru planı üzerinde gösterilmiştir."; "eğim 1/50".
  - Tablo 4.2 (SB ve bağlantı çapı): Lavabo 2 SB / 50; Yer süzgeci 2 / 70; Bide-pisuvar 1 / 70; Eviye 4 / 70; Küvet-duş 7 / 70; Çamaşır mak. 7 / 70; Bulaşık mak. 8 / 70; Klozet 10 / 100 (PDF metinden eşleştirildi, kesin değerler için orijinal tabloya bakılmalı).
  - Tablo 4.3 sütunları: "YATAY BORU [SB]" | "DÜŞEY BORU [SB]" | "BORU ÇAPI [mm]".
- **Temiz su:** https://ebaydar.ktu.edu.tr/files/sihhi_2.pdf — Galvaniz boru kritik hat örneği; bölüm adları **TB1…TB9**, hat adları Hat I/II/III, örnek çaplar TB1 65 mm (6 m), TB5 50 mm, TB7 32 mm; kontrol "1,914 mSS < 2 mSS".
- **Sıcak su:** https://ebaydar.ktu.edu.tr/files/sihhi_3.pdf — Boylerli tesisat çap tablosu (gidiş, boyler soğuk su, dolaşım doğal/pompalı).

### 7. Karabük/Çankırı Karatekin Ü. — Sıhhi tesisat ders notu
- **URL:** https://websitem.karatekin.edu.tr/user_files/hdag/files/20241022_c6eb214b44dd4131b70a353d95795e0a.pdf
- **Komple proje içeriği:** hesap raporu; kat planları; kolon şeması; gerekirse izometrik boru akış şemaları; özel boru diyagramları (mutfak, laboratuvar); rögar ve cihaz bağlantı detayları.
- **Çizgi:** "soğuk su boruları mavi kesikli çizgi", "Sıcak su boruları … noktalı kesik çizgi", "(Sıcak su kırmızı, soğuk su mavi.)"
- **Kolon şeması:** Kolonlar soldan sağa sıralanır, kolon numarası en üste yazılıp **daire içine alınır**, havalık kolon çapında çatıya çıkar.
- **Çap tablosu (inç):** Musluk birimine göre "8–20 Dahil 1 inç", "20–35 Dahil 1 ¼ inç"; daire sayısına göre "3–6 Daireye kadar 1 inç", "7–13 Daireye kadar 1 ¼ inç".
- **Montaj yükseklikleri:** lavabo bataryası 1,05 m, evye 1,15 m, duş 1,10 m, banyo 0,75 m.

### 8. arge7.com — Autocad Mekanik Tesisat Örnek Projeler (DWG arşivi)
- **URL:** https://www.arge7.com/altkategoridosyalar.php?kat=38 (2. sayfası da var)
- **İçerik (100 dosya, seçme):**
  - Sıhhi: KONUT-SIHHİ TESİSAT (`/panel/galeri/04.01.2024--1764508.dwg`), SIHHİ TESİSAT-ÖRNEK PROJE ANA ŞABLON (`…--5187996.dwg`), OKUL-PİS SU (`…--4934240.dwg`), ÇİFT DAİRE-SIĞINAK-KONUT (`…--8212025.dwg`), SIHHİ GEREÇ MONTAJ YÜKSEKLİKLERİ (`…--9848699.dwg`)
  - Isıtma: KALORİFER ANA ŞABLON (`…--4315008.dwg`), KASKAD SİSTEM 1–3, KOLLEKTÖRLÜ (`…--7667586.dwg`), KALORİMETRELİ (`23.03.2024--689288.dwg`), OKUL MERKEZİ KAZAN (`…--4446984.dwg`), KALORİFER TİP DETAYLARI (`…--5366102.dwg`)
  - Döşemeden ısıtma: 3 örnek (`04.01.2024--6252955.dwg`, `23.03.2024--800488.dwg`, `23.03.2024--3233262.dwg`)
  - Yangın: YANGIN TESİSATI-SPRİNK PROJESİ (`…--3988543.dwg`), HASTANE YANGIN, OTOPARK YANGIN, YANGIN TES TİP BLOKLARI (`…--4056779.dwg`), TİP DETAYLAR (`…--6012025.dwg`)
  - Doğalgaz: ANA ŞABLON (`23.03.2024--5709916.dwg`), KONUT (`04.01.2024--2615832.dwg`)
  - **Lejant:** GENEL MEKANİK TESİSAT ÇİZGİ GRUBU LEJANTI (`04.01.2024-7149-8256770.dwg`), MEKANİK TESİSAT ÇİZGİ GRUBU LEJANTI (`…--7814517.dwg`), VRF ELEMAN LEJANTI-2 (`…--895808.dwg`)
  - Havalandırma: otopark, sığınak+otopark, jet fan, spor salonu
  - Tam URL'ler `https://www.arge7.com/panel/galeri/<dosya>` biçiminde.
- **Not:** İçerik okunamadı. Çizgi tipleri, katman adları ve etiket blokları için **en yüksek potansiyelli kaynak** bu. İndirilip `ezdxf` ile katman ve blok envanteri çıkarılması önerilir.
- Aynı sitede [Kalorifer Tesisatı Uygulama Kuralları](https://www.arge7.com/detay.php?id=4087): "Kalorifer Boruları Kolon şemasında her kolonun Bodrum Kata inişinde 45 derece kırmak suretiyle" (kırımın üstüne boşaltma vanası); "Toplam daire içi Radyatör boyu 6m den küçük ise tüm kalorifer gidiş-dönüş boruları 3/4” çekilir". [Proje Hesapları-Pratik](https://arge7.com/detay.php?id=1677): Q (kcal/h) – d (inç) – d (mm) emniyetli çap tablosu.

### 9. Yangın Söndürme Tesisatı ve Duman Tahliye Projesi (MMO esasları, pdfcoffee)
- **URL:** https://pdfcoffee.com/yangn-sndrme-tesisat-ve-duman-tahliye-projesi-pdf-free.html
- **Tür:** Yangın (dolap, hidrant, sprinkler, pompa dairesi, duman tahliye).
- **Kolon adları:** "YG1, YG2,..."; izometride kotlar "0.00 kotu", "4.20 kotu", "8.40 kotu", "16.20 kotu".
- **Etiketler:** "O110 itfaiye bağlantı rakoru" ("Yerden 130 cm"), "KÜRESEL VANA"; boru lejantında "Basınç Rahatlatma Borusu", "Basınç Hissetme Hattı".
- **Pompa dairesi etiketleri:** "Otomatik hava atıcı", "Basınç emniyet vanası (gerekirse)", "İzleme anahtarlı kelebek vana", "Ayrılabilir gövdeli yangın pompası".
- **Tablo:** "HİDROLİK HESAPLAR BİLGİ TABLOSU" — Yapı Tehlike Sınıfı, Hesaplanan Sprinkler Alanı, Hortum Debisi, Toplam Debi (Yangın dolabı dahil), Tasdik Makamı.
- **Her paftada zorunlu bilgi:** tasarım standardı, bina tehlike sınıfı, sistem türü, sistem su talebi (debi, basınç), sprinkler özellikleri, koruma alanı, su uygulama süresi, olası yangın sınıfı.
- **Notlar:** "Test ve drenaj vanası en yakın pis su hattına akış gözlenebilir şekilde bağlanacaktır."; geçişlerde "yangın sızdırmazlığı sağlanmalıdır". Ölçek: pompa dairesi 1/20, kat planı 1/50.

### 10. İlbank — Mekanik Tesisat Proje Teknik Şartnamesi 2022
- **URL:** https://www.ilbank.gov.tr/storage/uploads/files/kati_atik_tesisleri_mekanik_tesisat_proje_sartnamesi_1660053353.pdf
- **Pafta numarası:** "MEK-01"den başlar. Hesap raporu numarasızdır ve önce gelir. İçindekiler klasör kapağına konur.
- **Antet:** "Proje antedinde projeyi yapan mühendis(ler)in adı-soyadı, ünvanı, diploma ve Oda sicil no."
- **Boru yazımı:** "boru cins, çap ve taban kotları verilecektir"; "Tüm boru hatlarının üzerine malzeme ve çap bilgileri yazılacaktır." Ø65 ve altı tek çizgi olabilir.
- **Paftalar:** Isıtma/havalandırma: "bu paftada kat planları ve kolon şeması bulunacaktır". Sıhhi: "ayrı ayrı sıhhi tesisat plan ve kolon şeması"; pis su "bina çıkışındaki ilk rögara kadar" gösterilir. Akış şemasında "notasyon anteti (lejant)".

### 11. ÇŞB — Dijital Proje Hazırlama taslağı (2025)
- **URL:** https://webdosya.csb.gov.tr/db/meslekihizmetler/icerikler/cal-stay-taslak-dokumanlar--20251107085546-20251110130354.pdf
- **Mekanik alt disiplin kodları:** SHTT Sıhhi, ISTT Isıtma, HVLT Havalandırma, SGTT Soğutma, DGTT Doğalgaz, YNGT Yangın, HVZT Havuz, MDGZ Medikal gaz, BSTT Bahçe sulama, OTMT Otomatik kontrol, DSDK Klima vb. Disiplin kodu **MK**.
- **Katman adı şablonu:** "M K - X X X - KELİME" (taslakta "MM-XXXX-KELİME" ile tutarsız). "İsimlendirmede büyük harf kullanılır ve “Ç, Ğ, İ, Ö, Ş, Ü” harfleri kullanılmaz." Renk katmana bağlı (ByLayer).
- **Dosya adı:** Proje kodu – Bina – Disiplin – Alt disiplin – Dosya türü – Dosya tipi (MKP: Mekanik Pafta, ITH: Isıtma Hesap Raporu …) – Kat – No – Revizyon.
- **Pafta:** "A4 sayfa boyutu ve katları kullanılır."
- **ROTAŞ'a etkisi:** Kullanıcı kuralı `SCOTT-` önekidir ve önceliklidir. Ancak ileride e-imar/dijital onay zorunlu olursa `SCOTT-` katmanlarından `MK-SHTT-…` adlarına bir eşleme tablosu hazır tutulabilir. Türkçe karakter yasağına da dikkat edilmeli.

### 12. tesisat.org
- **Isı İstasyonu Hesabı ve Mekanik Proje Adımları:** https://www.tesisat.org/isi-istasyonu-hesabi-ve-mekanik-proje-adimlari.html — 10 adımlık proje akışı; "Boruların metredeki basınç kaybı 2 mbarı ve akışkan hızı 0,5 m/s yi geçmemelidir."; DWG: Isı İstasyonu.dwg, Kat İstasyonu.dwg (Google Drive); şema görseli `…/2016/02/isi-istasyonu-ornek-tesisat-semasi.jpg`.
- **Örnek Yangın Sprinkler Hesabı:** https://www.tesisat.org/ornek-yangin-sprink-hesabi.html — Otel, OH; 72 m² tasarım alanı, 5 lt/dk·m², 12 m²/sprinkler, K80, C=120, 6 açık sprinkler; düğüm numaralı hidrolik tablo; sonuç ≈458 l/dk @ 4,14 bar; dolap+hidrant ile ≈58 m³/h pompa.
- **Mobil Kollektör ve Gidiş Dönüş Kollektörü:** https://www.tesisat.org/mobil-kollektor-ve-gidis-donus-kollektoru.html — "Kırmızı renk volanlı … kolektör gidiş", mavi dönüş; kollektör hızı 0,1–0,2 m/s (ısıtma).
- **Sıhhi Tesisat Projelendirme Esasları:** https://www.tesisat.org/sihhi-tesisat-projelendirme-esaslari.html — MEGEP modülüne yönlendiren giriş yazısı.

### 13. mtycad.com (eğitim videoları)
- Kat planı + kolon şeması tek tuş: https://www.mtycad.com/2023/10/mtycad-sihhi-tesisat-kat-plani-kolon.html (video `youtube.com/embed/eUdOFFkfYTI`)
- Sıhhi tesisat özellikleri: https://www.mtycad.com/2022/01/shhi-tesisat-temiz-su-tesisat-ve-pis-su.html — vitrifiye (tefriş) yerleştirme, otomatik çaplandırma, vana ekleme, "güncellenebilir çap tablosu", **lejant, vitrifiye adet tablosu, kolon şeması, bina şeması**, makine dairesi, metraj. Kullanıcının MTY bloklarıyla birebir aynı ürün ailesi.
- Yerden ısıtma çizim/metraj: https://www.mtycad.com/2023/09/blog-post_4.html (video `youtu.be/rkT0otQuRS0`); havalandırma: https://www.mtycad.com/2023/10/mtycad-havalandirma-tesisati-tek-tus.html; yangın: https://www.mtycad.com/2022/01/yangn-tesisat.html
- Sayfalarda etiket formatı metin olarak yok, bilgi videolarda. YouTube oynatma listesi: `PLtTce--4iM8VKD-YzgnbdSkpyVz8SfmUg`.

### 14. kutmankaplan.net
- Pis su kat planı ve kolon tesisatı (80 dk video): https://www.kutmankaplan.net/2019/04/autocad-programnda-pis-su-kat-plan-ve.html (video `youtube.com/embed/nwJp841iEKk`). Metindeki kurallar: kolon çapı konutta d = 6 × daire sayısı + 100 mm (10 daire → 160, 150'ye yuvarlanır); yatay %2 eğim; armatür bağlantıları 45°; her kolon dibine temizleme; rögar 60×60; bina içi hat 10 m'yi aşarsa rögar; yüksek binada 70 mm paralel havalık, her 3 katta bir bağlantı.
- Etiket sayfaları (Sıhhi 42, Isıtma 68, Yangın 39, Dinamik Blok 9 yazı) robots nedeniyle okunamadı.

### 15. Diğer yararlı kaynaklar
- **MEGEP Atık Su Tesisatı:** https://megep.meb.gov.tr/mte_program_modul/moduller_pdf/At%C4%B1k%20Su%20Tesisat%C4%B1.pdf — "Ø50, Ø70 ve Ø100 mm"; "Yatay atık su borularının eğimi % 2’dir."; "her kolonun altına temizleme parçası"; rögar "en az 50 x 50 cm", düz hatta "30 m’de bir rögar".
- **Normteknik — Sprinkler Borulama Esasları (Bölüm 7):** https://www.normteknik.com.tr/application/files/5316/6817/3300/2952017135636.Dosya.pdf — tablo yöntemi; LH: DN25 2, DN65 30, DN80 60, DN100 100; OH: DN65 20, DN80 40, DN125 160, DN150 275 sprinkler. Yalnız K80 ve ≤465 m² yeni yapı için geçerli.
- **KIRGAZ İç Tesisat Teknik Şartname Zeyilnamesi:** https://www.kirgaz.com.tr/assets/dosyalar/sertifika/kirgazteknik%20sartname%20zeyilnamesi.pdf — geçişler "kat planı ve izometride belirtilecek ayrıca proje ile ilgili notlar kısmına yazılacaktır"; dilatasyon geçişinde flexible eleman; TS 7363.
- **SALT Araştırma arşivi (tarihî Türk tesisat projeleri):** Kocaeli Anıtpark Sıhhi Tesisat Tatbikat Projesi, 1973, Mak-Tes: https://archives.saltresearch.org/handle/123456789/191231 — plan ve "kolon şeması" 1/50, sulama 1/200; taranmış JPEG paftalar. Muvaffak Güzel Evi Uygulama Projesi: https://archives.saltresearch.org/handle/123456789/87113. Kolon şeması geleneğinin görsel referansı olarak yararlı.
- **Academia — Isıtma Tesisatı Projesi (Trakya Ü., 2020):** https://www.academia.edu/42278987/Is%C4%B1tma_Tesisat%C4%B1_Projesi — 6 katlı 14 daire, Excel + AutoCAD, 75/65 °C, Edirne −9 °C (tam metin indirme gerektiriyor).
- **Okunamayanlar (JS veya robots engeli):** Scribd "Sıhhi Tesisat Projesi" (501821778, 67488174), Scribd "Kolon Şeması ve Boru Çapı Hesabı" (376308649), SlideShare "mmo yangın tesisatı", dogalgazprojesi.com "Kalorifer Tesisatı ve Kolon Şeması" / "Doğalgaz Projesi Kolon Şeması", MEGEP "Sıhhi Tesisat Meslek Resim-2", mtod "Kat Kaloriferi Tesisatı-1".

---

## C. Sentez — Türk proje pratiğinde ortak çizim tarzı

### C.1 Pafta düzeni (tipik konut/ticari mekanik set)
1. Kapak / içindekiler (İlbank: hesap raporu önce ve numarasız, paftalar MEK-01…)
2. Vaziyet planı / altyapı (rögar, şebeke girişi, 1/200 veya 1/500)
3. Bodrum, zemin, normal kat, çatı planları, her biri 1/50 (aynı katlar tek çizilir, plan adı ve ölçek sağ altta)
4. Kolon şemaları: sıhhi (temiz + sıcak + pis), ısıtma, yangın (YG), doğalgaz izometri (30°), yağmur
5. Kazan dairesi / pompa dairesi / su deposu planı ve kesiti (1/20–1/50)
6. Tip detaylar (1/20…1/1), lejant / sembol listesi, notlar
7. Ayrı hesap raporu (yangın raporu diğerlerinden ayrı), mahal listesi ve keşif .xlsx

### C.2 Etiket formatları (kaynaklardan derlenen)
| Disiplin | Kaynaktaki biçim | Kaynak |
|---|---|---|
| Pis su boru | `100` + `24 SB` (çap mm + toplam SB, aynı parçada) | KTÜ sihhi_4 |
| Pis su kolon adı | `P 1`, `P1`; kolon numarası en üstte, daire içinde | KTÜ, MEGEP, Karatekin |
| Temiz su kolon | `TS1, TS2…`; boru bölümü `TB1…`; çap mm + inç | MEGEP, KTÜ sihhi_2 |
| Temiz su yük | YB (1 YB = 0,25 l/s) veya MB; çap inç (`1"`, `1 1/4"`) | MEGEP, Karatekin |
| Isıtma boru | gidiş/dönüş yanında **sıcaklık + ısı yükü + çap** | MEB İEGM 1.2.10 |
| Radyatör | **içine** mahal no + mahal sıcaklığı; **üstüne** tip + ısı yükü + ebat | MEB İEGM 1.2.10 |
| Doğalgaz boru | üç satır: `2 m³/h` / `3,2 m` / `DN20` | MEGEP DG projesi |
| Doğalgaz cihaz | `Q = 16335 kcal/h` + marka; `150 cm²` menfez | MEGEP DG projesi |
| Yangın kolon | `YG1, YG2…`; her katta boru çapı + sprinkler sayısı + yük | MEB İEGM, MMO |
| Sprinkler boru | `DN..` ve sprinkler (başlık) sayısı (tablo yöntemi DN↔adet) | Normteknik, ROTAŞ kuralı |
| Proses/altyapı boru | malzeme + çap + taban kotu | İlbank |

ROTAŞ'ın mevcut formatları (`Ø100 / 25 SB`, `1" / 5.25 YB`) bu pratikle tam uyumlu. Akademik örnekler Ø işaretini çoğu zaman atlıyor, MTY ise Ø kullanıyor. **MTY biçimi korunmalı.**

### C.3 Çizgi, renk ve katman
- Soğuk su mavi kesikli, sıcak su kırmızı ve noktalı kesik (Karatekin, MEGEP). Isıtma gidiş kırmızı, dönüş mavi (MEB). Sprinkler zonları ayrı katman ve renkte (MEB).
- Kalemler: mimari 0,2; uç malzeme 0,5; temiz su 0,3; pis su 0,5 (MEGEP). Mimari altlıkta sıva çizgileri silinir.
- Sistemler ayrı katmanlarda tanımlanır. Renk ByLayer verilir (ÇŞB taslağı). ROTAŞ'ta katmanlar `SCOTT-` önekli kalır.

### C.4 Kolon şeması kuralları (ortak payda)
- Planın ön görünüşüdür: sağdaki armatür sağa, soldaki sola açılır. Kolonlar soldan sağa numara sırasıyla dizilir.
- Kat aralığı ölçekli (3 m kat, 1/50 → 60 mm). Her kat için kot ve kat adı yazılır (su basmanı referanslı, mimariden).
- Pis su kolonu havalıkla çatıya çap değiştirmeden çıkar. Kolon dibinde temizleme (T.K.) bulunur, oradan rögara gider.
- Temiz su şeması bodrumdan başlar: şebeke → ana sayaç → kollektör → kolonlar. Sıcak su boyler/şofben çıkışından alınır.
- Kat planları ile kolon şeması birebir uyumlu olmalıdır (MEB). Bu, motor için otomatik çapraz kontrol maddesi olarak kullanılabilir.
- Isıtmada kolonlar bodrum inişinde 45° kırılır ve kırım üstüne boşaltma vanası konur (arge7 uygulama kuralları).

### C.5 Lejant, not ve tablo blokları
- Lejant zorunlu. Semboller proje içinde tek tip olur. Çizimle anlatılamayan kapasite/cins bilgisi lejantta liste halinde verilir.
- Standart notlar: yangında flushing notu; havalandırmada zon zon sızdırmazlık ve duman testi; doğalgazda geçiş ve dilatasyon notları; pis suda eğim notu (%2 veya 1/50).
- Tablolar: sıhhi boru çapı/basınç kaybı çizelgesi (YB | L | Ø mm/inç | R | ΣR, Emre Hazır Basınç kontrolü); yangın "HİDROLİK HESAPLAR BİLGİ TABLOSU"; doğalgaz hat tablosu (DN | L | Q | v | R); malzeme listesi (Seri No | Cinsi | Miktar | Birim | Birim Fiyat | Tutar).

### C.6 Antet
- Proje müellifi adı-soyadı, unvanı, diploma no, Oda sicil no (İlbank). Pafta adı, ölçek ve kat adı plan altında sağda (MEGEP DG). Pafta A4 ve katları (ÇŞB).

---

## D. Motor için öneriler (kullanıcı onayı olmadan uygulanmaz)
1. **arge7 DWG'leri** (özellikle "MEKANİK TESİSAT ÇİZGİ GRUBU LEJANTI", "SIHHİ TESİSAT ANA ŞABLON", "KALORİFER ANA ŞABLON", "YANGIN TES TİP BLOKLARI") kullanıcı tarafından indirilip depoya konursa katman, çizgi tipi ve etiket envanteri çıkarılabilir. Bunlar yalnızca kıyas içindir, ROTAŞ/MTY şablonunun yerine geçmez.
2. **Plan ↔ kolon şeması tutarlılık kontrolü:** Kolon adları (P, TS, YG), çaplar ve kat kotları iki çizimde de aynı olmalı. `xcheck.py`'ye eklenebilir.
3. **Radyatör etiket kontrolü:** İçinde mahal no ve sıcaklık, üstünde tip, ısı yükü ve ebat var mı? `MTY-RADYATOR MAHAL` bloğuyla karşılaştırılmalı.
4. **Yangın paftası bilgi bloğu:** tehlike sınıfı, tasarım alanı, yoğunluk, K faktörü, debi/basınç, süre (MMO esasları). VOYAP yangın tarzına uygunluğu kullanıcıya sorulmalı.
5. **Standart lejant notları** kütüphanesi: flushing, kanal sızdırmazlık testi, eğim, test/drenaj vanası notu.
6. ÇŞB dijital standardı yürürlüğe girerse `SCOTT-` ↔ `MK-SHTT/ISTT/YNGT…` katman eşleme tablosu hazırlanmalı (Türkçe karakter yasağına dikkat).
