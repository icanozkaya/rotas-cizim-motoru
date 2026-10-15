# KONTROL — SIHHİ, TUR 6 — 15.10.2026

- **Dosya:** `proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf` (commit aa2c28f, 14:33).
- **Bağımsızlık:** Üreticinin kodu ve notları okunmadı. Ölçüm DXF varlıkları üzerinden yapıldı. Gözle kontrol yan yana kırpımlarla yapıldı: solda kontrol edilen çizim, sağda kullanıcının `new_block.dxf` çizimi, iki tarafta pencere aynı.
- **Kat ötelemeleri:** 1. kat +2034, 2. kat +4082.
- **Ölçüm raporu:** `kontrol_png/sihhi_tur6/kontrolor_olcum_raporu.md`. Kırpımlar: `kontrol_png/sihhi_tur6/`.
- **Kullanıcının son şikâyeti (15.10, 13:07):** "pis su giderleri kolon içine girmiş hep, mutfakta gene süzgeç var onu kaldır, daire beslemeleri ve sayaç yerlerini de işle". Görüntü: `RED_sihhi_pissu_kolon_icine_giriyor.png`.

## KARAR: **RED** (3 madde)

Ne düzeldi:
- Mutfak süzgeci kaldırıldı.
- Sayaç grubu ve daire beslemeleri planda işlendi.
- Hiçbir pis su hattı kolon sembolünün içinde bitmiyor.

Ne kaldı:
- Beş kolonda iki hat aynı doğru üzerinde, kolon sembolünün iki yanında duruyor. Ekranda tek bir hat sembolün altından geçiyormuş gibi görünüyor. Altı kolonda da hat kolonun yanından geçip geri dönerek sembole bağlanıyor. Kullanıcının şikâyet ettiği görüntü böylece tekrar ediyor.
- 1. ve 2. kattaki üst dairenin besleme hattı kapı açıklığından giriyor ve kapı kanadı çizgisini kesiyor.

---

## 1. Pis su — kolon sembolü (şikâyetin ilk maddesi)

### Ölçüm
Planda 27 kolon var. Her hat ucunun kolon merkezine uzaklığı ölçüldü.

- Kolon sembolünün dış çemberi r = 10 cm, dolu iç diski r = 7 cm.
- 41 hat ucunun hepsi 9,8–10,2 cm'de bitiyor. Çemberin içine giren hat **yok** (tur 5'teki görüntü artık yok).

### Betonarme ve şaft
- Hiçbir kolon betonarme (ANSI35 taraması) içinde değil. P7, S05 kolon yüzüne 8 cm uzakta.
- P2, P3, P5, P6 ve P8 kolonları mimaride "mek. havl." yazılı şaft bölmesinde. Bu bölmede havalandırma kanalının (daire) ayrı bir alt bölmesi var. Kolon bu alt bölmenin yanında, **kullanıcının kendi çizimindeki yerinde**.
- Bunu engel saymadım. Kural metni ("mekanik havalandırma şaftı içinde olmaz") ile kullanıcının çizimi burada çelişiyor. Kullanıcıya sorulmalı (aşağıda, soru 1).

### R1 — engel. Hat kolonun "altından geçiyor" ve geri dönüşlü kanca var

**(a) Aynı doğru üzerinde iki hat.** Lavabo hattı ile klozet/süzgeç hattı kolonun iki yanında aynı doğru üzerinde bitiyor. Sembolün alt kirişi boyunca hat kesiliyor ama ekranda tek bir hat diskin altından geçiyormuş gibi okunuyor. Kullanıcının şikâyet ettiği görünüm budur.

| Kat | Kolon | Konum | Hattın kolon merkezinden kayması |
|---|---|---|---|
| Zemin | P5 | (253378, −442737) | 8,1 cm aşağıda |
| 1. kat | P5 | (255412, −442737) | 8,1 cm aşağıda |
| 2. kat | P5 | (257460, −442737) | 8,1 cm aşağıda |
| Zemin | P2 | (253751, −442737) | 5,4 cm aşağıda |
| 2. kat | P2 | (257833, −442737) | 5,4 cm aşağıda |

Kanıt: `ZOOM_Z_P2.png`, `ZOOM_Z_P5.png`, `KOL_Z_P5_253377.png`, `KOL_K2_P5_257459.png`.

**(b) Geri dönüşlü kanca.** Hat kolonun yanından geçiyor, sonra 95°'den fazla keskin bir dönüşle geri gelip sembol kenarına bağlanıyor. Bu, akış yönünün tersine bir bağlantı. Kural C "kolona 45° ile bağlanır" der.

- P5: zemin, 1. kat, 2. kat. Ø100 klozet hattı sağdan gelip yukarı kıvrılıyor ve geri dönüyor.
- P2: 2. kat. Kolonun solundan dolaşıyor.
- P3: 1. ve 2. kat. Sağ üstten gelen diyagonal kolonun solundan geçiyor ve sağa geri dönüyor.

Kanıt: `ZOOM_K2_P2.png`, `ZOOM_K2_P5.png`, `KOL_K1_P3_255766.png`, `KOL_K2_P3_257814.png`.

**İstenen:** Her branşman kolona kendi geldiği taraftan, merkeze doğru (radyal) ya da 45° ile varmalı ve çember kenarında bitmeli. İki branşman aynı doğru üzerinde kolonun karşılıklı iki yanına gelmemeli. Birleşme kolonun önünde, tek bir dalla yapılmalı.

Bu kolonlarda sorun yok: P1, P4, P6, P7, P8, P9, zemin P3. Kanıt: `KOL_*` kırpımları.

**Bilgi (engel değil):** İki hat çembere teğete yakın varıyor (radyal yöne 31–59°):
- 1. ve 2. kat P8: yatay hat, merkezin 5 cm altından.
- 2. kat P1: düşey hat, çemberin sol üst kenarına.

Okunaklı, ama (a) düzeltilirken bunlar da radyale alınabilir.

## 2. Mutfak süzgeci (şikâyetin ikinci maddesi): **KAPANDI**

- **Planda:** 18 yer süzgeci var, katta 6. Hepsi banyo, wc-banyo, duş/wc-duş ve wc-lvb'de. Dokuz mutfağın hiçbirinde süzgeç yok. Kanıt: `MUTFAK_Z_1..3`, `MUTFAK_K1_1..3`, `MUTFAK_K2_1..3`.
- **Şemada:** 13 yer süzgeci var, hepsi duş, klozet ve lavabo grubunun yanında. Eviyenin yanında süzgeç yok.
- T09 (ıslak hacim başına bir süzgeç) ✓.

## 3. Sayaç yeri ve daire beslemeleri (şikâyetin üçüncü maddesi)

### Geçenler ✓

**Bina girişi ve şebeke** (`Z_sag_ust.png`):
- Şebeke bina girişinden (sağ cephe) giriyor ve giriş holünün üst duvarı boyunca (y −442078) ilerliyor.
- Hol ile merdiven holü arasındaki bölme duvarı kapı kasasının üstünden geçiyor.
- Düşey hatta ana vana, pislik tutucu ve çek valf var. Hat sayaç grubuna iniyor.

**Sayaç grubu** (`CEKIRDEK_Z.png`, `HOL_Z.png`, `SAYAC_Z_yakin.png`):
- Zemin katta, ortak alanda, merdiven kolu ile S10 arasındaki geçişte. 9 sayaç var.
- Her satırın sırası: vana → pislik tutucu → sayaç → çek valf → vana. Kollektör sağda, akış sağdan sola; sıra doğru.
- "SAYAÇ GRUBU 9 AD." listesi okunaklı. Çıkış hatları iç içe L biçiminde ve birbirini kesmiyor.

**Besleme kolonları:**
- Kolon kutusu S10'un yanında. Kolonlar üç katta da aynı eksende: zemin x 253672, 1. kat 255706 (= +2034), 2. kat 257754 (= +4082).
- Kolon sayısı zeminde 8 (6 üst daire + 2 depo), 1. katta 8, 2. katta 5, çatıda 2. Hepsi şemayla tutarlı.

**Kesişme:** Üç katın çekirdeğinde temiz su ve şebeke hatları arasında kesişme **0**.

**Şema ile plan tutarlı mı?** Evet (`SEMA_sayac.png`, `SEMA_sol.png`):
- Şemada şebeke depoya çıkıyor, depo dönüşü sayaç kollektörüne iniyor.
- Şemada 9 sayaç var (5+4), kullanıcının şemasıyla aynı düzende. Plandaki 9 sayaç ve 2 depo kolonu buna karşılık geliyor.

**Daire girişleri:**
- Zemin D1/D2 (`GIRIS_Z_alt_genis.png`): hol köşesinden, kapının üstündeki duvar parçasından giriyor. Kapı açıklığından geçmiyor.
- Zemin D3 (`GIRIS_Z_ust_genis.png`): 3 no'lu kapının solundaki duvardan giriyor.
- 1. kat D4/D6 ve 2. kat D7/D9: aynı düzen.

### R2 — engel. 1. kat D5 ve 2. kat D8 besleme hattı kapı açıklığından giriyor

Konumlar: 1. kat x 255634, 2. kat x 257684.
- Hat kapı eşiğini kapı açıklığının içinden kesiyor. Eşik çizgisi (255549…255649, −442056) 100 cm; hat sağ kasaya 15 cm.
- Sonra y −442024'te kapı kanadı çizgisini kesiyor (255633,−442003)–(255649,−442041). 2. katta da aynısı var.

Kural: "Şebeke / temiz su hatları kapı önlerinden ve kapı kanadından geçmez; daireye kapı dışındaki duvardan girilir."

Zemin D3'te bu doğru yapılmış (kapının solundaki duvardan). Üst katlarda da aynısı yapılmalı. Kolonlar zaten aynı eksende; yalnız daireye giriş noktası duvara alınmalı.

Kanıt: `GIRIS_K1_ust.png`, `GIRIS_K1_ust_genis.png`, `GIRIS_K2_ust.png`.

### R3 — engel (küçük). Şebeke hattı 3 no'lu kapı numarası balonunun içinden geçiyor

- Konum: zemin (253580…253620, −442078).
- Yatay şebeke hattı ve düşey inişi "3" balonunu kesiyor. Hat mimari sembolün üstüne biniyor.
- Hat birkaç cm kaydırılırsa (inişi balonun solundan) çözülür.

Kanıt: `GIRIS_Z_ust_genis.png`, `GIRIS_Z.png`.

### Üreticinin sorusu: Şebekenin 3 no'lu kapının ~20 cm önünden geçmesi ve 43 cm duvar geçişi kabul edilebilir mi?

**Kabul edilebilir, ama kullanıcıya bildirilmeli.** Gerekçe:
- 3 no'lu kapı daire içine açılıyor; hol tarafında kanat yok.
- Giriş holünden merdiven holüne geçmenin iki yolu var: bölme duvarındaki K1 kapısının kanat süpürme alanı ya da 3 no'lu kapının önü. İkisinin arasında boş bant yok (K1 kanadı 100 cm, 3 no'lu kapıya kadar uzanıyor).
- Hat, kapı açıklığını kesmiyor; duvara paralel, asma tavanda gidiyor.
- 43 cm duvar geçişi, giriş holü ile merdiven holü arasındaki bölme duvarı. Kapı kasasının üstünde, kapı açıklığının dışında. Kabul.

R3 düzeltilirken iniş, balonun solundan ve kapı açıklığının dışından kalmalı.

**Bilgi:**
- Plandaki sayaç listesinin sırası (D9, D6, D7, D4, D8, D5, D3, D2, D1, DEPO) şemadaki sırayla aynı değil. Hatlar kesişmesin diye böyle dizilmiş, okunaklı. İstenirse şemanın sırasına uyulabilir.
- Sayaç grubu 1,2 m'lik geçişte yaklaşık 0,9 × 1,6 m'lik bir sembol olarak çizilmiş. Okunaklı. Dolap/niş notu eklenebilir.

## 4. Gerileme (tur 5'te kapanan maddeler)

| Madde | Durum | Kanıt |
|---|---|---|
| Balkon süzgeci | ✓ Yağmur inişine kısa hatla bağlı. T01'deki 3 bulgu araç sınırı: P9 komşuluğu, tur 4–5'le aynı. | `KOL_K2_P9_256860.png` |
| Sıcak su daire içinde, kombiden başlıyor | ✓ T04 0 | — |
| Etiket yığını | ✓ T07'de etiket–etiket 0. Toplam 64 (tur 5: 63). Fark: etiket–mimari yazıda "P5"/"14" ile "P6"/"13" yer değiştirdi. | — |
| 1. kat D6 wc-duş | ✓ Süzgeç (255834, −442390) tekne dışında, tur 5 ile aynı. | — |
| wc-lvb klozet Ø100 10 SB | ✓ Zemin ve 2. katta var. | `KOL_Z_P2_253751.png`, `KOL_K2_P2_257833.png` |
| T02, T03, T10, T11 | Tur 5 ile aynı sayı, yalnız uzunluklarda birkaç cm fark. Yeni test türü bulgusu yok. | — |
| T04, T05, T08, T09, T12–T17 | ✓ | — |

**Gerileme yok.**

## 5. Üreticiye düzeltme listesi

1. **R1:** P5 (zemin, 1. kat, 2. kat), P2 (zemin, 2. kat) ve P3 (1. kat, 2. kat) kolon bağlantıları yeniden çizilmeli:
   - Branşmanlar kolona kendi tarafından, radyal ya da 45° ile varmalı.
   - Aynı doğru üzerinde karşılıklı iki uç olmamalı.
   - Geri dönüşlü kanca olmamalı.
   - Çember kenarında bitme kuralı korunmalı.
2. **R2:** 1. kat D5 ve 2. kat D8 beslemesi kapı açıklığından değil, kapının yanındaki duvardan girmeli. Zemin D3 gibi yapılmalı. Kapı kanadı çizgisi kesilmemeli.
3. **R3:** Zeminde şebeke hattı ve inişi "3" kapı numarası balonundan çekilmeli.

## 6. Kullanıcıya sorulacak

1. Pis su kolonları P2, P3, P5, P6 ve P8, mimaride "mek. havl." yazılı şaft bölmesinde. Sizin çiziminizdeki yerde, havalandırma kanalının yanındalar. Kural metni "kolon havalandırma şaftında olmaz" diyor. Bu yer kalsın mı?
2. Şebeke, giriş holünden merdiven holüne geçerken 3 no'lu daire kapısının yaklaşık 20 cm önünden, asma tavanda geçiyor. Başka geçiş yolu yok. Uygun mu?
