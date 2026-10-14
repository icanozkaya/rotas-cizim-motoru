# KONTROL — SIHHİ KAT PLANLARI, TUR 1

- Dosya: `proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf` (zemin, 1. kat, 2. kat). Üretim commit'i: 7d8d896.
- Kontrolör: bağımsız ajan. Üretenin kodunu okumadı, yalnız çıktıyı ölçtü ve gözle inceledi. Tarih: 15.10.2026.
- Ölçüt: README (C), (B) ve 14.10 kural blokları, `motor/kontrolor/onay_protokolu.md`, `SIHHI_ALTIN_REFERANS.md` §3–4 ve §10'daki 26 kural, kullanıcının reddettiği 4 RED görüntüsü, kullanıcının `new_block.dxf` çizimi.
- Kanıt: `kutuphane/arastirma/kontrol_png/sihhi_plan_tur1/`. Her PNG'de solda kontrol edilen çizim, sağda aynı pencerenin kullanıcı çizimi (new_block) var. Siyah zemin, ezdxf. Otomatik ölçüm raporu da aynı klasörde: `kontrolor_olcum_raporu.md`.

## KARAR: **RED**

Otomatik kontrolör (T01–T11) yalnız 1 FAIL verdi (T04, 1. kat D6). T07 "etiket çakışması 0" dedi. Ancak gözle yapılan inceleme ve yazı tipiyle ölçülen gerçek yazı kutuları bunu doğrulamıyor: etiketler hâlâ üst üste biniyor (2. kat mutfak). Ayrıca ölçümlerin hiç bakmadığı ağır hatalar var:
- Kolonlar katlar arasında düşey olarak sürekli değil.
- Çamaşır ve bulaşık makinesi mimaride gösterildikleri yerden taşınmış; makinenin yerine kolon ya da aspiratör konmuş.
- Aspiratör notları merdiven holünde ya da yatak odasında duruyor, bazı banyolarda hiç yok.
- Etiketler duvar taramasının, kapı yazısının ve armatürün üstüne konmuş.

Kullanıcı bu çizime bakınca RED görüntülerindeki "karmaşa" şikâyetini 1. kat D6 banyosunda (P10/P11) ve mutfaklarda yeniden görür.

Olumlu bulgular (ONAY yönünde): balkon süzgeçleri yalnız yağmur inişine, kısa yeşil hatla bağlı (T01; zemin balkon PNG'leri). Zemin ve 2. katta sıcak su kombiden başlıyor ve daire içinde kalıyor. Oda içinden çapraz uzun pis su hattı yok, pis su hatları duvar dibinden gidiyor (T03). Sıcak ve soğuk su 5 cm paralel. Köprü/atlatma yok. Islak hacim başına 1 süzgeç var.

## RED maddeleri (önem sırasıyla)

Koordinatlar zemin kat çerçevesindedir. 1. kat için x'e 2034, 2. kat için 4082 ekleyin. Bu ekleme yapılmış mutlak değerler parantez içinde verilmiştir.

1. **[1. kat, D6] Kolon sürekliliği bozuk, P2/P3 yok, P10/P11 yalnız bu katta var.**
   - Zemin ve 2. katta kolonlar P2 (253736, −442806) ve P3 (253748, −442404) konumunda. 1. katta bu iki kolon çizilmemiş. Onların yerine yalnız 1. katta bulunan P10 (255742, −442424) ve P11 (255772, −442448) konmuş.
   - Sonuç: 2. katın P2/P3 atığı 1. kattan nasıl geçiyor, belli değil. P10/P11'in zemin katta devamı, temelde rögar bağlantısı yok.
   - Kullanıcı çiziminde 1. katta da P2/P3 aynı yerde. wc-duş, P3'e bağlanıyor. Toplam 9 kolon var.
   - Düzeltme: her kolon üç katta aynı (x, y) noktasında olsun. 1. kat wc-duş ve banyo, mevcut P3'e (gerekirse P2'ye) bağlansın. Yeni kolon numarası açılmasın.
   - PNG: `K1_merdiven_yani_D6_P10_P11.png`, `K1_D6_giris_hol.png`, `T04_1_01.png`.
2. **[Bütün katlar, D3/D5/D8 wc+banyo] Çamaşır makinesi mimarideki yerinden taşınmış.**
   - Mimaride ÇM sol alttaki nişte, yaklaşık (253050, −442190). Oraya turuncu aspiratör sembolü (253058, −442208) konmuş.
   - ÇM, "Ç.M. (EK)" adıyla duş teknesinin üstüne (253156, −442166) taşınmış. Kırmızı kutu duş teknesine biniyor.
   - Bu B kuralına aykırı ("ÇM bağlantısı mimaride gösterildiği konumda") ve bellekteki "tasarım seçimini değiştirme" kuralına da aykırı.
   - Kullanıcı çiziminde ÇM nişte; pis su branşmanı 4 SB ile nişe gidiyor.
   - PNG: `Z_11_wcbanyo_D3_P8.png`, `K1_wcbanyo_D5_P8.png`, `K2_wcbanyo_D8_P8.png`.
3. **[Bütün katlar, D3/D5/D8 mutfak] P7 kolonu bulaşık makinesinin yerine konmuş, BM odanın ortasına taşınmış.**
   - Mimaride BM tezgâh altında, yaklaşık (253660, −441860). P7 kolonu (253682, −441826) tam bu noktada.
   - "B.M. (EK)" (253668, −441635 / 2. kat −441726) mutfağın ortasında, tezgâhın önünde, boşlukta duruyor.
   - Kullanıcı çiziminde P7 tezgâh köşesinde, sağ duvarda (253765, −441812). BM mimarideki yerinde.
   - PNG: `Z_16_giris_hol_D3.png`, `K2_D8_mutfak_P7_etiket_ust_uste.png`.
4. **[2. kat D8 mutfak (257797, −441708); 1. ve 2. kat D6/D9 banyo (255894, −442484 / 257942, −442444)] Etiket üstüne etiket biniyor. Bu, RED görüntüsünün aynısı.**
   - Mutfakta "Ø50 6 SB" ve "Ø50 4 SB" iç içe geçmiş, ikisi de eviye sembolünün üstünde. "0.5 MB" ile "Ø50" birbirine değiyor. "Ø50 4 SB" yazısı B.M. kutusunun içinde. B.M. kutusu P7 balonuna değiyor.
   - Banyoda "Ø100 12 SB" ile "Ø50 7 SB" birbirine biniyor; "7 SB" duvar çift çizgisinin üstünde.
   - T07 bu çakışmaları yakalamadı. Yazı tipiyle ölçülen gerçek yazı kutularında çakışma var.
   - Kullanıcı çiziminde mutfakta tek parça için tek etiket var ve etiket armatürün üstünde değil.
   - PNG: `K2_D8_mutfak_P7_etiket_ust_uste.png`, `K1_D6_banyo_etiket_ust_uste.png`.
5. **[Bütün katlar] Etiketler duvar taramasının, kapı ve pencere yazısının ve armatürlerin üstüne konmuş.**
   - Zemin D1/D2 banyolarında "Ø50 2 SB" ve "Ø100 10/12 SB" merdiven duvarı taramasının ve P04/P05 duvar çizgilerinin üstünde (`Z_13`, `Z_15`).
   - D3 duşta "Ø50 7 SB / Ø70 9 SB / Ø50 2 SB" pencere duvarına ve "60/60" ölçüsüne sıkışmış (`Z_12`, `Z_D3_sol_hol_dus_yolu`).
   - D3 holünde "1" 5.25 MB / 1" 3.25 MB" etiketi K3 "80/220" kapı yazısına biniyor (zemin yaklaşık 253175, −442090; `Z_D3_sol_hol_dus_yolu.png`).
   - wc+banyo'da "Ø100 14 SB / Ø100 10 SB" asansör boşluğunun içine taşmış (`Z_11`).
   - Zemin mutfaklarında iki eviye üstünde 5 etiket var (`Z_mutfak_P4_P1_etiket.png`).
   - wc-lvb'de temiz su etiketi "1" 6.5 MB / 1" 4 MB" alt duvarın üstünde (`Z_15`).
   - Kural: etiket mimari yazıya ve hatta binmez; dar ıslak hacimde etiket mahal dışına KILAVUZLA ve boş yere alınır.
6. **[Zemin ve 2. kat, merdiven holü (253623, −442428); 1. kat D6 yatak odası (256082, −442566)] Aspiratör notları yanlış yerde.**
   - "Wc Aspiratörü 160 m³/h" notu merdiven holünde, basamakların yanında, yani daire dışında duruyor.
   - 1. katta not yatak odasında. Aspiratör sembolünden gelen yaklaşık 2,5 m'lik kılavuz çizgisi banyoyu çaprazlamasına kesiyor ve duvarı aşıyor. Bu, kullanıcının şikâyet ettiği "oda içinden çapraz uzun çizgi" görüntüsünü veriyor.
   - Kullanıcı çiziminde not banyonun içinde, boş alanda (§7).
   - PNG: `Z_merdiven_aspirator_notu.png`, `K1_D6_giris_hol.png`, `Z_13`.
7. **[Bütün katlar, D2/D4/D7 banyo + wc-lvb (P5/P6)] Penceresiz banyoda mekanik havalandırma yok.**
   - Her katta yalnız 2 aspiratör var. Kullanıcı çiziminde her katta 3 not var (D3, D2 ve D1 banyoları).
   - Bu B kuralına aykırı: "WC/banyo mekanik havalandırma kat planlarında da gösterilir".
   - PNG: `Z_15_banyo_wclvb_D2_P5_P6.png`.
8. **[Bütün katlar] Kolonlar ıslak hacim köşesinde değil, kolon balonları ıslak hacmin içinde.**
   - P9 (252834, −441985) duşun alt duvarının ortasında, süzgeçle lavabo arasında. Kullanıcı çiziminde sol üst köşede, S03'ün yanında (252778, −441881).
   - P8 (253209, −442176) wc+banyo sağ duvarının ortasında, duşun yanında. Kullanıcı çiziminde sol alt köşede, mek. havl. nişinin yanında.
   - P3 (253748, −442404) ÇM nişinin içinde, makinenin arkasında.
   - P6 (253352, −442404) üst duvarın ortasında. Bu yüzden klozetin atığı duvar boyunca yaklaşık 2,6 m dolaşıyor (Ø100, 10 SB). Kullanıcı çiziminde klozet kolona kısa bir hatla bağlı.
   - 1. katta P11 balonu banyonun içinde, duş ile ÇM nişinin üstünde. P10 balonu merdiven duvarının üstünde.
   - PNG: `Z_12`, `Z_11`, `Z_13`, `Z_15`, `K1_merdiven_yani_D6_P10_P11.png`.
9. **[Zemin D3, 1. kat D5, 2. kat D8] Duşun temiz suyu iki yatak odasından geçiyor.**
   - Sıcak-soğuk çifti holden yukarı çıkıyor. Ardından 15,44 m²'lik yatak odasının duvar dibinden, K2 kapısının açılma alanının içinden 2,6 m yatay gidiyor.
   - Sonra 7,75 m²'lik "oda"nın içinden duvara 36 cm mesafeden 1,25 m düşey iniyor. Duşa alttan, odanın duvar dibinden giriyor.
   - Kullanıcı çiziminde çift holden tek yatay hatla gelip yalnız "oda"nın üst kısmından geçerek duşa üstten giriyor (yaklaşık 3,5 m, tek oda).
   - Düzeltme: kullanıcının güzergâhı kullanılsın; kapı açılma alanı ve ikinci yatak odası kullanılmasın.
   - PNG: `Z_D3_sol_hol_dus_yolu.png`.
10. **[1. kat D6, T04] Sıcak su 217 cm daire dışında (255756, −442384).**
    - Otomatik ölçüm FAIL verdi. Kullanıcı çizimi de aynı ölçümde 1 FAIL veriyor; mahal/daire eşlemesinden kaynaklanan bir yanılgı olabilir.
    - Ancak bu bölge zaten madde 1 nedeniyle baştan çizilecek. Yeniden çizildikten sonra T04 = 0 olmalı.
    - Ayrıca mimarideki "C.M." yazısı (D1 ve D2 banyo nişleri, wc+banyo) kontrol edilen çizimde görünmüyor. Mimari eksiksiz kopyalanmalı; ÇM/BM yerleri mimariden okunmalı ve korunmalı.
    - PNG: `T04_1_01.png`, `Z_merdiven_aspirator_notu.png`.

## Daire kontrol listesi (özet)

| Daire | Balkon süzgeci → YB, kısa | Pis su kısa/düzenli, çapraz yok | Kolon köşede | Sıcak su daire içinden, kombiden | Temiz su oda/kapı önü | Etiket okunaklı, binme yok | Karmaşa |
|---|---|---|---|---|---|---|---|
| D1 (Z) | ✓ | ✓ (duvar dibi) | ✗ P3 ÇM nişinde | ✓ | ✓ | ✗ duvar taraması, merdivende aspiratör notu | orta |
| D2 (Z) | ✓ | △ klozet 2,6 m dolaşıyor | ✗ P6 duvar ortasında | ✓ | ✓ | ✗ duvar üstünde etiket | orta; aspiratör yok |
| D3 (Z) | ✓ YB8 | ✓ | ✗ P8, P9 duvar ortasında | ✓ | ✗ duşa 2 yatak odasından | ✗ K3 yazısına biniyor, asansöre taşıyor | yüksek; ÇM/BM taşınmış |
| D4 (1) | ✓ | △ | ✗ | ✓ | ✓ | ✗ | orta; aspiratör yok |
| D5 (1) | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | yüksek; ÇM/BM taşınmış |
| D6 (1) | ✓ | ✗ P10/P11 yeni kolon | ✗ balon banyo içinde | ✗ T04 | ✓ | ✗ etiket üst üste | **çok yüksek (RED görüntüsüne benziyor)** |
| D7 (2) | ✓ | △ | ✗ | ✓ | ✓ | ✗ | orta; aspiratör yok |
| D8 (2) | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ mutfakta etiket üst üste | yüksek |
| D9 (2) | ✓ | ✓ | ✗ P3 ÇM nişinde | ✓ | ✓ | ✗ "12 SB" ile "7 SB" binişiyor | orta |

## Kontrolör aracı için not

T07, döndürülmüş etiketleri ve gerçek yazı tipi genişliğini hesaba katmıyor. Bu yüzden 2. kat D8 mutfakta açıkça görülen etiket üst üste binmesini 0 saydı. Ayrıca şu durumları ölçen bir test yok:
- kolonun katlar arasında düşey sürekliliği,
- ÇM/BM'nin mimarideki konumda kalması,
- aspiratör notunun ait olduğu mahalde durması.

Bu testler `motor/kontrolor/testler.py`'ye eklenmeli. Bu turdaki karar gözle yapılan incelemeye dayanıyor.
