# KONTROL — YERDEN ISITMA, TUR 4 (bağımsız kontrolör)

- İncelenen dosyalar: `proje/denemeler/yerden2/NB_YERDEN_ISITMA.dxf` ve `NB_YERDEN_ISITMA.xlsx` (15.10.2026 09:41 sürümü).
- Referans: kullanıcının `new_block.dxf` çizimindeki ısıtma seti (dx = +22 761,9 cm). Her kat referansın aynı katıyla karşılaştırıldı (kat kayması +2 034 / +4 082 cm).
- Ayrıca kullanılanlar: README kalıcı kuralları, `YERDEN_ISITMA_ALTIN_REFERANS.md` (§3.4 ve PEX-10'un güncel hali: klozet önü borulu; lavabo, duş teknesi ve Ç.M. altı boş), `onay_protokolu.md`, tur 3 raporu.
- Yöntem:
  - Üreticinin kodu okunmadı.
  - `kontrolor.py --tur yerden --excel` çalıştırıldı. Araç raporu: `kontrol_png/yerden_tur4_kontrol/kontrolor_arac_raporu.md`.
  - Tur 3 pencereleri, her katın genel görünümü ve kolon şeması kırpıldı, kullanıcının çizimiyle yan yana kondu ve görüntü olarak incelendi.
  - Vitrifiye altındaki boru, maskelerin altında kalan mimari çizgi ve etiket ölçekleri DXF'ten ölçüldü (shapely).
  - Excel LibreOffice ile yeniden hesaplatıldı ve hata taraması yapıldı.

## KARAR: **ONAY**. Dosya kullanıcıya gönderilebilir.

- Araç sonucu: ONAY. T11, T16, T17 ve Y01–Y06 testlerinin hepsi geçti, FAIL 0.
  - Y01'de 54 BİLGİ var. Bunlar 5,3–6,0 m/m² aralığındaki mahaller ve mutfaklar. Kullanıcının kendi çiziminde de 24 mahal bu aralıkta.
- Görsel karşılaştırmada engelleyici bir tarz farkı yok.

---

## Tur 3 maddeleri: KAPANDI / AÇIK

| Madde | Durum | Kanıt (ölçüm) | PNG |
|---|---|---|---|
| **Y-2'** wc+banyoda serpantin, klozet önü kullanıcının çizimindeki gibi (Z21, 114, 214) | **KAPANDI** | Y02 FAIL 0. Ölçümler aşağıdaki tabloda. | `01b_*`, `02b_*`, `03b_*_etiketsiz_boru.png`, `01–03_*_tam_yan_yana.png` |
| **E-1** wc+banyo devre etiketleri ×0,7 | **KAPANDI** | Devre etiketi ölçekleri: 76 adet ×1,0, 6 adet ×0,85 (hol etiketleri, tur 3'te engelleyici sayılmamıştı). ×0,7 etiket kalmadı. 156 WIPEOUT'un hiçbirinin altında `ROTAS-MIMARI` çizgisi yok (ölçülen 0 cm). | `12_wcbanyo_devre_etiketi_x1_Z21_114_214.png` |
| **K-1** 35 W/m × L esası | **KULLANICI SORUSU** (RED gerekçesi değil, değişmedi) | Excel'deki değerler: Z21 13,29 m → 465,1 W; 214 13,15 m → 460,2 W. Plan = şema = Excel (Y06: 81/81 devre, 63 zon). | — |

### Y-2' ölçümleri

Borunun her armatürün dış çizgisinin içinde kalan boyu, metre:

| Mahal | Mahal içi devre | Klozet (elips) | Rezervuar arka şeridi | Lavabo | Duş teknesi | Ç.M. |
|---|---|---|---|---|---|---|
| Z21 | 13,27 | 1,25 | 0 | 0 | 0 | 0,61 |
| 114 | 13,28 | 1,26 | 0 | 0 | 0 | 0,61 |
| 214 | 13,14 | 1,27 | 0 | 0 | 0 | 0,59 |
| **Kullanıcının çizimi** (aynı üç konum) | 13,79 | 1,25–1,27 | 0 | 0 | 0 | 0,55–0,56 |

- Üç mahalde de devre ≥ 13,1 m, eşik sağlanıyor.
- Ç.M. satırındaki değer, Ç.M. kapak bandındaki (üst kenarın 1,1 cm altı) besleme parçasıdır. Kullanıcının çiziminde de aynı parça var (0,56 m), bu yüzden kabul edildi. Ç.M. gövdesinin içine boru girmiyor.
- İlmek düzeni kullanıcınınkiyle aynı tarzda:
  - 5 sıra U dönüş var. Dönüşler klozet çanağının içinde.
  - Lavabo, duş teknesi, Ç.M. ve mek. havl. altı boş.
  - Devre uçları mahal içinde bitiyor. Kullanıcının çiziminde de öyle (PEX-12: planda ayak çizilmez).

## Kalan maddeler

Engelleyici madde yok. Aşağıdakiler bilgi notudur.

1. **Bilinen küçük not.** Z21 ve 114'te mahal etiketi (24 °C / no) kapı kanadı çizgisinin üstünde duruyor. Maske kesik olduğu için kanat çizgisi görünüyor. 214'te etiket kapıdan uzakta. Kullanıcının çiziminde etiket kanadın altında. Bu bir tarz farkı, okunurluğu bozmuyor. → `13_wcbanyo_mahal_etiketi_kapi_kanadi.png`
2. **wc+banyo devre etiketi klozetin üstünde.** Etiket klozet elipsinin sol yarısının üstünde duruyor. Maske elipsin çevresinden kesildiği için elips görünüyor, ama "13.29 m" değerinin üst kısmı elips çizgisine değiyor. Okunuyor. Kullanıcının etiketi de Ç.M., duş teknesi ve "mek. havl." çizgilerinin üstünde, maskesiz. Engelleyici değil. → `12_*.png`, `01_*_tam_yan_yana.png`
3. **Etiketin gizli ALAN özniteliği mimari m² ile aynı değil.** Mahal etiketi bloğundaki görünmez ALAN özniteliği mimari m²'den farklı: Z21 için 3,47 (mimari 4,37), Z07 için 4,85 (mimari 5,36). Muhtemelen net alan. Paftada görünmüyor; Excel ve hesap mimari m²'yi kullanıyor (4,37). Bilgi notu.
4. **K-1** kullanıcıya sorulacak (aşağıdaki metinde).
5. Tur 3'teki gözlem değişmedi: iki devreli mahallerde iki etiket aynı x hizasında alt alta durmuyor (ET-3). Tarz farkı, engelleyici değil. → `07_1kat_102_yukluk_iki_devre.png`

## Gerileme kontrolü (tur 3'te geçen konular)

- Yüklük, balkon, wc-lvb, wc-duş, asansör ve merdivende boru yok (Y01). → `07`, `08`, `GENEL_KAT_*`
- 81 devrenin her biri tek polyline, kesişme yok (T11).
- Plan W = şema W = Excel W (Y06).
- Kolon şeması kullanıcının düzeniyle aynı: 3 kat bandı × 3 daire, kombi + kollektör solda, devre kutuları sağa doğru dizili. → `14_sema_D3_yan_yana.png` (referans `ornekler/new_block_onizleme/c_h3.jpg`), `kontrolor_arac_raporu_png/GENEL_SEMA.png`
- Excel yeniden hesaplatıldı. 7 sayfanın hiçbirinde hücre hatası yok ve hepsinde yazdırma alanı var.
  - Z21, 114 ve 214 satırları planla aynı: 13,29 / 13,29 / 13,15 m ve 465,1 / 465,1 / 460,2 W.

## Kanıtlar

Hepsi `kutuphane/arastirma/kontrol_png/yerden_tur4_kontrol/` klasöründe. Sol taraf kontrol edilen dosya, sağ taraf kullanıcının çizimi.

- `01_Z_wcbanyo_Z21_yan_yana.png`, `01_Z_wcbanyo_tam_yan_yana.png`, `01b_Z_wcbanyo_etiketsiz_boru.png`
- `02_1kat_wcbanyo_114_yan_yana.png`, `02_1kat_wcbanyo_tam_yan_yana.png`, `02b_1_wcbanyo_etiketsiz_boru.png`
- `03_2kat_wcbanyo_214_yan_yana.png`, `03_2kat_wcbanyo_tam_yan_yana.png`, `03b_2_wcbanyo_etiketsiz_boru.png`
- `04_Z_wcbanyo_Z21_etiketler_yakin.png`
- `05_Z_banyo_Z07_Z14_yan_yana.png`
- `06_1kat_banyo_121_yan_yana.png`
- `07_1kat_102_yukluk_iki_devre.png`
- `08_2kat_202_yukluk_iki_devre.png`
- `09_1kat_111_salon_iki_devre.png`
- `10_Z_hol_Z13_Z20.png`
- `12_wcbanyo_devre_etiketi_x1_Z21_114_214.png`
- `13_wcbanyo_mahal_etiketi_kapi_kanadi.png`
- `14_sema_D3_yan_yana.png`
- `GENEL_KAT_Z_yan_yana.png`, `GENEL_KAT_1_yan_yana.png`, `GENEL_KAT_2_yan_yana.png`
- `kontrolor_arac_raporu.md` ve `kontrolor_arac_raporu_png/` (GENEL_KAT_*, GENEL_SEMA)

## Kullanıcıya gidecek kısa metin

> Yerden ısıtma projesi (3 kat, 81 devre) bağımsız kontrolden geçti.
>
> wc+banyolarda serpantin sizin çiziminizdeki gibi klozet önünün altından geçiyor. Lavabo, duş teknesi ve çamaşır makinesi altı boş. Bu mahallerin devre etiketleri artık tam boyda.
>
> Plan, kolon şeması ve Excel'deki devre güçleri birbiriyle aynı.
>
> Tek sorumuz var: Devre gücü sizin çiziminizdeki gibi 35 W/m × hat uzunluğu olarak mı kalsın, yoksa ısı kaybı esasına mı geçelim? 35 W/m ile yüzey sıcaklığı yaklaşık 38 °C çıkıyor (sınır 29 °C) ve devre basınç kayıpları yüksek. Bunlar Excel'deki notlarda açıklandı.
