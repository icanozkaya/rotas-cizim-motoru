# KONTROL — SIHHİ KOLON ŞEMASI + PAFTA ŞERİDİ, TUR 1 (15.10.2026)

Kontrolör: bağımsız ajan (üretenin kodu `motor/sihhi2/*.py` OKUNMADI; yalnız çıktı DXF'ler incelendi).
İncelenen: `proje/denemeler/sihhi2/NB_SIHHI_SEMA.dxf`, `NB_SIHHI_TEMEL.dxf`, `NB_SIHHI_PAFTA_DENEME.dxf` (commit 7d8d896).
Referans: kullanıcının `ornekler/new_block.dxf` çizimi, AYNI model koordinatlarında kırpıldı (birim cm).
Kurallar: README (C) KOLON ŞEMASI, (B), `KOLON_SEMASI_TARZI.md` §1–3 + 14 RED maddesi, `SIHHI_ALTIN_REFERANS.md` §1, §5–8,
`RED_sihhi_kolon_semasi_sayac_kapida_yanlis_tarz.png`, `ornekler/ORNEK_DUZEN.md`.
Kanıt PNG'leri (üst: kontrol edilen, alt: referans, aynı ölçek): `kutuphane/arastirma/kontrol_png/sihhi_sema_tur1/`.

## KARAR: **RED**

Kullanıcının asıl şikâyeti ("su saatleri aşağıda kalacak, kapı önlerine almışsın") GİDERİLMİŞ: sayaç grubu zemin bandının solunda,
şebeke girişinde, 5+4 = 9 sıra; kat bantlarında ve daire girişlerinde sayaç yok (02 PNG, T08 PASS). Depo sol üstte, kolon etiketleri
üstte, D blokları yan yana, T.K. kolon üzerinde, rögar şeması altta başlıksız, yağmur şeması sağda. D3 bloğu (05 PNG) referansa çok
yakın. Antet (21) ve yerleşim (25) referansla birebir.
Ancak şema ve şerit, kullanıcının çiziminden TASARIM ve DÜZEN olarak ayrılıyor (fazladan kolon/rögar, pafta boyu, çatı paftası yok,
armatür sırası, görünmeyen yazılar, kural metni sızıntısı). Aşağıdaki maddeler düzeltilmeden ONAY verilmez.

## Araç sonuçları
| Araç | Dosya | Sonuç |
|---|---|---|
| `kontrolor.py --mimari ornekler/new_block.dxf.xz` | NB_SIHHI_SEMA.dxf | T07 ✓ (0), T08 ✓, T11 ✓; T09 ✗ 20 (plan testi, şemada anlamsız — dikkate alınmadı). Rapor: `kontrol_png/sihhi_sema_tur1/K_NB_SIHHI_SEMA.md` |
| aynı | NB_SIHHI_PAFTA_DENEME.dxf | **T04 ✗ 1**: daire 6 (1. kat, wc-duş) sıcak su hattının 217 cm'si daire dışında @ (255756, −442384). Diğer testler ✓. Rapor: `K_NB_SIHHI_PAFTA_DENEME.md` |
| `motor/deneme/denetim/denetle.py` | SEMA, TEMEL | ✓ (MTY 0, önek 0, köprü 0, kesişme 0, yazı çakışması 0); bilgi: pis/temiz kesişme 56 (SEMA) |

Ölçülen sayılar (DXF'ten): şema paftası 260714…270531 = **9817 cm** (ref 7418); bant 260820…269845 = **9025 cm** (ref 6629);
kolon 11 (P1…P11; ref 9); rögar R1…R5 + PB (ref R1…R4 + PB); T.K./R 11 adet; kombi 9; sayaç 9.

## DÜZELTME LİSTESİ (önem sırasıyla)

1. **[Şema + temel + rögar] Fazladan kolon/rögar — kullanıcının tasarımı değiştirilmiş.** P10, P11 ve R5 kullanıcının çiziminde yok.
   P10/P11 yalnız 1. kat D6'ya hizmet ediyor; zemin (D1) ve 2. kat (D9) bantlarında daire bloğunun içinden HİÇBİR bağlantı almadan
   geçiyor, yine de zeminde T.K. + R çiziliyor (11_1kat_D6_blok, 01_sema_genel). Kullanıcının 1. kat D6'sında iki banyo grubu tek
   toplayıcıyla mevcut kolona bağlanır. Rögar dağılımı da farklı (bizde R3←P3,P6,P10,P11; R4←P2,P5; R5←P1,P4 —
   kullanıcıda R1←P7,P9; R2←P8; R3←P2,P3,P5,P6; R4←P1,P4) (08_rogar_semasi). Temel planında kolon yerleri kullanıcının
   temelindeki P konumlarıyla örtüşmüyor (P1 bina ortasında, P4 sol altta, P9 sol ortada; kullanıcıda P1/P4 alt mutfak arası,
   P2/P3/P5/P6 merdiven yanı ıslak hacimler) (22_temel). **Düzeltme:** 9 kolon, kullanıcının kolon yerleri ve numaraları; R1–R4 + PB,
   yukarıdaki dağılım. Kolon eklemek/kaldırmak tasarım değişikliğidir, kullanıcıya sorulmadan yapılmaz.

2. **[Şerit] Pafta boyu ve sırası ORNEK_DUZEN ile aynı değil.** Kolon şeması paftası 9817 cm (ref 7418), bant 9025 cm (ref 6629);
   bu yüzden detay paftası 268132 yerine 270531'de başlıyor ve şerit 2400 cm uzuyor (20_tum_serit). Fazla genişlik madde 1'deki
   kolonlar ve D1/D6/D9 bloğunun ~3600 cm'ye şişmesinden geliyor. **Düzeltme:** madde 1 düzelince blok genişlikleri ref'teki gibi
   (D1 ≈ 2140, D2 ≈ 1600, D3 ≈ 1800, aralık ≈ 140); şema paftası 7418, detay paftası 268132…270197.

3. **[Şerit — çatı paftası 258656…260714] ÇATI PLANI YOK.** Yerine "SIHHİ TESİSAT KAT PLANLARI — LEJANT" sayfası konmuş; "ÇATI
   PLANI..........ÖLÇEK: 1 / 50" başlığı yok (23_cati). Bu lejantta "PİS SU KOLON NUMARASI 0", "YAĞMUR İNİŞİ NUMARASI 0",
   "DAİRE TEMİZ SU GİRİŞİ 0" gibi yanlış adetler ve eski/iç notlar var ("Temiz su: daire girişi merdiven holünde kapı yanında",
   "(EK) işaretli armatür ... kural gereği eklenmiştir"). **Düzeltme:** kullanıcının çatı planı mimarisi + P1…P9 havalık uçları + YB1…YB9
   başlangıçları + "Çatı Tipi Fan / Ø150 mm" şaft konumlarında (ALTIN_REFERANS §7); lejant detay paftasındaki SIHHİ DETAYLAR içinde kalır.

4. **[Şema — daire blokları] Armatür sırası kullanıcınınkinden farklı** (12_banyo_armatur_yakin, 13_mutfak_kombi, 05_daire_D3).
   Kullanıcı (kolondan dışa): banyo **lavabo – klozet – süzgeç – duş – ÇM**; wc **lavabo – klozet**; mutfak **BM – eviye – kombi**.
   Bizde: D1 banyo lavabo – ÇM – klozet – duş – süzgeç; D3 orta grup klozet – lavabo – ÇM – duş; wc klozet – lavabo; mutfak eviye – BM – kombi.
   **Düzeltme:** ALTIN_REFERANS §5.2 sırası, aralık 130.

5. **[Şema — duş sembolü] Çizgi hatta biniyor.** El duşu askı/hortum çizgisi +130 dağıtım hattını (soğuk + sıcak) kesip MB etiketi
   bölgesine kadar yukarı çıkıyor (D3 P9 grubu, D1 banyo; 05 ve 12 PNG). Kullanıcıda duvar bataryası + hortum hattın ALTINDA kalır.
   **Düzeltme:** duş sembolünün tamamı +130 hattının altında, bataryası branşman ucunda.

6. **[Şema — lejant + yağmur hesap kutusu; temel lejantı] Yazılar ACI 250.** 18 lejant yazısı ve 8 hesap satırı renk 250 (koyu gri):
   AutoCAD siyah ekranda görünmez, kutu boş görünür (09_yagmur_semasi, 14_yagmur_hesap_kutusu, 10_lejant_baslik). Kullanıcının
   "YAĞMUR SUYU BORU ÇAPI HESABI" kutusu okunur renkte, h 10. **Düzeltme:** renk 7/bylayer (ya da kullanıcının hesap renkleri).

7. **[Şema + izometri + planlar] Kural/iç metin sızıntısı ve referansta olmayan blok.** Kolon şeması paftasında kullanıcıda olmayan
   bir LEJANT bloğu var ve içinde kural cümleleri: "Sayaçlar yalnız zemin bandında, şebeke girişinde toplu; kat bantlarında ve daire
   girişlerinde su sayacı çizilmez", "SICAK SU HATTI (kombiden, soğuğa 5 cm paralel)", "SU SAYACI (yalnız zemin, şebeke girişinde)".
   İzometri başlığında "(new_block.dxf, Z+2, 9 daire)" dosya adı, lejantında "(otomatik)"; planlarda "B.M. (EK)", "Ç.M. (EK)".
   **Düzeltme:** bu metinler kaldırılır; şema paftasındaki lejant kaldırılır (kullanıcının şemasında lejant/başlık yok; lejant detay paftasında).

8. **[Şema — yağmur bölmesi] Kat bant çizgileri yağmur şemasına devam etmiyor.** Bizde bant çizgileri sağ kat sütununda (269895) bitiyor,
   YB hatları boş zeminde; kullanıcıda kat çizgileri 571 cm'lik yağmur bölmesi boyunca sürer, Ø70 kat işaretleri bu çizgilere göre
   döşeme +170'te (09_yagmur_semasi). **Düzeltme:** bant çizgileri yağmur bölmesinin sağ ucuna kadar.

9. **[Detay paftası — WC havalandırma izometrisi] Şaft düzeni kullanıcınınkinden farklı.** Bizde 4 şaft (Ş1 D3-5-8, Ş2 D5,
   Ş3 D2-4-7, Ş4 D1-6-9) ve D5 iki şaftta; kullanıcıda 2 şaft: D3-5-8 "MEKANİK HAVALANDIRMA 240 m³/h", D1-2-4-6-7-9 "480 m³/h",
   kat başına "Wc Aspiratörü 80 m3/h-50 pa Ø150 mm" (24_detay). **Düzeltme:** kullanıcının iki şaftlı izometrisi.

10. **[Temel planı] Etiket boyu ve lejant.** "Ø125 / %1 EĞİM", "Ø150" h 12 (kullanıcıda h 20, *U67 biçimi, hattın 29–34 cm yanında);
    köşelerde 5 cm 45° pah yok; altta yazısı görünmeyen (ACI 250) lejant parçası (22_temel). **Düzeltme:** ALTIN_REFERANS §6.

### Ek (küçük ama ONAY için gerekli) maddeler
11. **[Şebeke/depo]** Akış okları yok (kullanıcıda şebeke girişinde → ve iki dikmede ↑ / ↓) (02, 03 PNG). Depo taşma borusu depoya
    flanşsız, depo içine uzanan çizgiyle giriyor; boşaltma depo tabanından değil taşma borusunun dibinden; flatör yok (kullanıcıda
    şamandıra + flanşlı giriş/çıkış) (03_depo).
12. **[Semboller]** T.K., küresel vana, çek valf, sayaç dolguları ACI 250: siyah ekranda içi boş görünür; kullanıcıda dolu (02, 07 PNG).
    D balonu tek daire (kullanıcıda dış mor + iç daire çift) (13 PNG). Kolon çizgisi havalık şapkasına ulaşmıyor, kolon–şapka–balon
    arası kopuk (06_kolon_ust_etiketler).
13. **[Pis su detay]** PVC toplayıcılarda muf halkaları/ek parçaları yok, armatür iniş etiketi (`Ø50 / 2 SB`) hat etiketiyle aynı boyda;
    kullanıcıda iniş etiketi h 15 ve inişin sağında, muflu PVC görünümü (12, 07 PNG).
14. **[Plan, PAFTA_DENEME] T04 ✗**: 1. kat daire 6 wc-duş sıcak su hattının 217 cm'si daire dışında @ (255756, −442384) —
    README (C) "SICAK SU daire İÇİNDEN".
15. **[Şema başlığı]** "SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI..........ÖLÇEK: YOK" kullanıcının şema paftasında yok (bilgi; kullanıcıya sorulabilir).

## Doğru bulunanlar (değiştirilmeyecek)
- Sayaç grubu: zemin bandı solu, şebeke girişi (küresel – pislik tutucu – çek valf – küresel – çek valf), 5 + 4 sıra, 20 aralık,
  sıra içi küresel – pislik tutucu – sayaç – çek valf – küresel; kat bantlarında sayaç yok (RED görüntüsü hatası yok).
- Depo yeri/boyu/yazıları, kat etiketi sütunları (h 25, 90°, kırmızı), bant yüksekliği 400, D balonu yeri, kombi yazısı,
  temiz su +250/+130, sıcak su kombiden 5 cm paralel, MB/SB etiket biçimi, T.K. kolon üzerinde band +24, dirsek + ok + "R".
- Rögar şeması biçimi (kutu, kesit kutusu, "70x70 / h:-70cm", "%1 EĞİM / Ø150", balonlar), yağmur YB1…YB9 60 aralık + "YAĞMUR
  SUYU KANALINA GİDER" kutusu.
- Antet (ROTAŞ, SIHHİ TESİSAT PROJESİ, arsa/yapı tabloları) ve yerleşim planı (vaziyet, kesitler, bilgi kutusu) referansla aynı.

## PNG dizini (`kontrol_png/sihhi_sema_tur1/`)
| PNG | Bölge |
|---|---|
| 01_sema_genel | şema paftası tamamı (aynı koordinat penceresi; bizim pafta 2400 cm daha geniş) |
| 02_sebeke_sayac_grubu | şebeke girişi + sayaç grubu |
| 03_depo | kullanım su deposu |
| 04_daire_D1_zemin, 13_mutfak_kombi_D1_yakin | D1 zemin bloğu / mutfak + kombi |
| 05_daire_D3_zemin | D3 zemin bloğu |
| 06_kolon_ust_etiketler | kolon üstü, havalık, balonlar |
| 07_kolon_dibi_TK_R | kolon dibi T.K. + dirsek + R |
| 08_rogar_semasi | rögar şeması |
| 09_yagmur_semasi, 14_yagmur_hesap_kutusu | yağmur şeması + hesap kutusu |
| 10_lejant_baslik | şema paftası sol alt (bizde lejant + başlık, ref'te boş) |
| 11_1kat_D6_blok | 1. kat D6 (P10/P11) |
| 12_banyo_armatur_yakin | banyo armatür grubu yakın |
| 20_tum_serit | PAFTA_DENEME tüm şerit ↔ new_block şerit |
| 21_antet, 22_temel, 23_cati, 24_detay, 25_yerlesim, 26_zemin_plan | şerit paftaları |
| K_NB_SIHHI_SEMA.md, K_NB_SIHHI_PAFTA_DENEME.md | kontrolor.py raporları |

Not: kırpımlar ezdxf drawing addon, beyaz zemin (renk 7 → siyah). 10 ve 14 numaralı kırpımlar ACI 250 yazıları görünür olsun diye
renkler değiştirilmeden çizildi.
