# KONTROL — SIHHİ TAM ŞERİT, TUR 5 — 15.10.2026

- **Dosya:** `proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf` (commit 12f5d8b, 11:50).
- **Bağımsızlık:** Üreticinin kodu ve notları okunmadı. Ölçüm DXF varlıkları üzerinden yapıldı, gözle kontrol yan yana kırpımlarla.
- **Araç:** `motor/kontrolor/kontrolor.py --mimari ornekler/new_block.dxf.xz`. Ölçüm raporu: `kontrol_png/sihhi_tur5/kontrolor_olcum_raporu.md`.
- **Kırpımlar:** `kontrol_png/sihhi_tur5/`. Solda kontrol edilen çizim, sağda kullanıcının çizimi (`/tmp/claude-0/uu/new_block.dxf`); iki tarafta pencere aynı. Kat ötelemeleri: 1. kat +2034, 2. kat +4082.

## KARAR: **ONAY**

Tur 4'ten kalan iki engel (E1, E2) kapandı. Tur 4'te geçen testlerin hepsi hâlâ geçiyor. T07 bulguları 110'dan 63'e, T03 bulguları 6'dan 5'e indi. Genel görünümde kullanıcının dört RED görüntüsündeki hatalardan hiçbiri yok.

---

## 1. E1 — 1. kat D6 wc-duş: **KAPANDI**

Teknenin iç çerçevesi (mimari): x 255742…255807, y −442423…−442344.

| Öğe | Konum | Durum |
|---|---|---|
| Yer süzgeci `ROTAS-S2-YER-SUZGECI` | (255834, −442390) | **Tekne dışında**: sağ kenara 27 cm, tekne ile klozet arasında. Kullanıcının çiziminde `SUZGEC1` (255830, −442404) noktasında; konum aynı. |
| Aspiratör sembolü | (255829, −442337) | **Tekne dışında**: tekne ile lavabo arasında. |
| Tekne gideri | (255752, −442413) → (255747, −442424) | Teknenin kendi gideri. Kenara iniyor. |
| Pis su omurgası | y −442424, x 255742 → 255825 | Teknenin alt kenarından (−442423) 1 cm dışarıda, duvar dibinde. Kullanıcıda bu hat y −442425'te; konum aynı. |
| Klozet ve lavabo pis su bağlantısı | x 255845 | Tekne dışında. |

**Tekne içinden başka armatürün pis su yolu geçmiyor.** T03'te tur 4'te çıkan wc-duş bulgusu (255776, −442394) artık yok.

**Bilgi notu (engel değil):** Klozet ve lavaboya giden temiz su hatları tekneyi yatay kesiyor:
- Soğuk su y −442390, sıcak su y −442385.
- Bu hatlar teknenin alt kenarından yaklaşık 33–38 cm içeride, yani teknenin ortasında.
- Soğuk su hattı süzgeç sembolünün tam üstünden geçiyor.

Kullanıcı da temiz suyu tekne üzerinden geçiriyor (y −442357/−442362), ama üst duvara 13–18 cm mesafede. Bu yüzden hata sayılmadı. İstenirse hat üst duvar dibine alınabilir. Böylece süzgeç sembolünün üstü de açılır.

Kanıt:
- `Y_K1_D6_wcdus.png` (yakın plan)
- `Y_K1_D6_banyo_wcdus.png` (tur 4 penceresi)

## 2. E2 — wc-lvb klozet `Ø100 10 SB`: **KAPANDI**

| Kat | Etiket | Konum |
|---|---|---|
| Zemin D1 | `Ø100 10 SB` (TS-CAP2) | (253740, −442782); P2 → klozet düşeyinin hemen yanında, kılavuzlu. Lavabo için `Ø50 2 SB` de var. |
| 2. kat (aynı konum) | `Ø100 10 SB` (PS-CAP-U) | (257827, −442787); klozet hattının üstünde. Lavabo ve süzgeç için `Ø50 2 SB` ×2 var. |
| 1. kat (aynı konum) | — | Bu kattaki mahal **yüklük**; ıslak hacim yok. Kullanıcıda da yüklük. Etiket gerekmiyor. |
| Zemin D2 (ayna daire, kontrol için) | `Ø100 10 SB` + `Ø50 4 SB` | Etiketler duruyor. |

Bilgi:
- 2. katta `Ø100 10 SB` dikey yazı "wc-lvb." mahal adının kenarına biniyor. Kullanıcının kendi çiziminde de aynı odada `Ø100 10 SB` mahal adının üstünde. Okunaklı; engel değil.
- Süzgecin yeri katlar arasında farklı: zeminde sol duvar dibinde, 2. katta oda ortasına yakın. Tek tip olması daha iyi olur; engel değil.

Kanıt:
- `Y_Z_D1_wclvb.png`
- `Y_K2_D7_wclvb.png`
- `Y_K1_ayni_konum_yukluk.png`
- `Y_Z_D2_wclvb_ayna.png`

## 3. Gerileme kontrolü

### Otomatik ölçüm (tur 4 → tur 5)

| Test | Tur 4 | Tur 5 | Yorum |
|---|---|---|---|
| T04, T05, T08, T09, T12, T13, T14, T15, T16, T17 | ✓ | ✓ | **Gerileme yok.** |
| T06 | bilgi (0 FAIL) | bilgi (0 FAIL) | Değişmedi. |
| T01 | 4 | 4 | Araç sınırı; tur 4'teki açıklama geçerli. Genel görünümde balkon süzgeçleri yağmur inişine (YB8/YB9) bağlı. |
| T02 | 18 | 18 | Değişmedi. Kullanıcıda bu tür 59 bulgu var. |
| T03 | 6 | 5 | 1. kat wc-duş bulgusu düştü (E1). |
| T07 | 110 | 63 | Etiket–etiket **0** (Z/1/2). Etiket–tarama, etiket–armatür ve etiket–asansör bulgusu da 0. Kalanlar: 17 etiket–mimari yazı, 52 etiket–hat. Kullanıcıda bu tür 208 bulgu var. |
| T10 | 16 | 16 | Araç sınırı. Kolonlar kullanıcının koordinatlarında. |
| T11 | 1 | 1 | Aynı kaynak. |

### Gözle kontrol

**D3/D5/D8 wc+banyo:** `Z_11_wcbanyo_D3`, `K1_11_wcbanyo`, `K2_11_wcbanyo`.
- Pis su hatları etiketli.
- Etiketler üst üste binmiyor.
- Süzgeç tekne dışında, tekne üst kenarına 9–11 cm.
- Bilgi: 1. ve 2. katta aspiratör sembolünün merkezi tekne dışında, ama sembol kenarı tekne köşesine yaklaşık 7 cm biniyor. Tur 4'te sembol teknenin içine daha fazla giriyordu. Engel değil.

**Genel görünüm, 3 kat:** `P_zemin_genel`, `P_1kat_genel`, `P_2kat_genel`.
- Balkon süzgeçleri yağmur inişine bağlı.
- Sıcak su daire içinde, kombiden başlıyor (T04 ✓).
- Kat planlarında sayaç yok (T08 ✓).
- Etiket yığını yok.
- Kolon, YB ve giriş yerleri kullanıcının yerinde.

**RED görüntüleri tekrar ediyor mu?** Hayır. Dört görüntünün hiçbiri tekrar etmiyor:
- balkon süzgecinin kolona bağlanması,
- sayacın kapıda olması,
- sıcak suyun daire dışından gelmesi,
- çapraz pis su ve etiket yığını.

## 4. Kullanıcıya iletilecek kısa metin

> Sıhhi tesisat tam şeridi kontrolden geçti. Kolon şeması, kat planları, temel, çatı ve detay paftaları sizin new_block düzeninizde. Önceki RED'lerinizdeki hataların hiçbiri yok (balkon süzgeci, sayaç yeri, daire dışından sıcak su, çapraz hat/etiket yığını). Son turda iki şey düzeltildi:
> - 1. kat wc-duşta süzgeç ve aspiratör duş teknesinin dışına, sizin çizdiğiniz yere alındı.
> - Zemin ve 2. kattaki wc-lvb'de klozet çapı (Ø100 10 SB) yazıldı.
>
> Bilginize üç soru:
> 1. wc-lvb ve mutfağa yer süzgeci konuldu. Sizin çiziminizde yok, ama talimatınız her ıslak hacimde süzgeç istiyor. Kalsın mı?
> 2. Koridorda temiz su hattı duvar dibinden mi, ortadan mı gitsin?
> 3. 1. kat wc-duşta klozet/lavabo temiz su hattı duş teknesinin üstünden geçiyor (siz de öyle çizmişsiniz, ama duvara daha yakın). Duvar dibine alalım mı?
