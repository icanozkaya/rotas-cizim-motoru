# KONTROL — SIHHİ TAM ŞERİT, TUR 4 — 15.10.2026

- **Dosya:** `proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf` (commit 5b493e0, 09:14).
- **Bağımsızlık:** Üreticinin kodu ve "ne yapıldı" notları okunmadı. Dosya ölçüldü ve gözle incelendi.
- **Araç:** `motor/kontrolor/kontrolor.py --mimari ornekler/new_block.dxf.xz`. Ölçüm raporu: `kontrol_png/sihhi_tur4/kontrolor_olcum_raporu.md`.
- **Yan yana kırpımlar:** `kontrol_png/sihhi_tur4/`. Tur 3 pencereleri (`Z_/K1_/K2_1x, _31`) aynı koordinatlarda yeniden kırpıldı. Solda kontrol edilen çizim, sağda kullanıcının kendi çizimi (`/tmp/claude-0/uu/new_block.dxf`).
- **Ek kırpımlar:**
  - `P_*_genel`: kat planları tam görünüm, yan yana.
  - `P_serit_genel`: tüm şerit.
  - `S_genel`: şema, yan yana.
  - `Y_*`: yakın plan.

## KARAR: **RED (küçük, 2 madde)**

Tur 3'ün dört engelinin (R1–R4) üçü tamamen kapandı. R1 büyük ölçüde kapandı. Kullanıcının dört RED görüntüsündeki hataların hiçbiri yok. Yan yana konduğunda düzen ve tarz kullanıcınınkiyle aynı.

Buna rağmen onay verilmedi. Sebep, iki yerel hata:
- **E1:** 1. kat D6 wc-duşta yer süzgeci duş teknesinin içine çizilmiş. Bu doğrudan bir tesisat hatası. Kullanıcı tesisat mühendisi olduğu için ilk bakışta görür.
- **E2:** Merdivenin sağındaki wc-lvb'de (zemin D1, 2. kat D7) klozet bağlantısında hâlâ çap/yük etiketi yok. Bu tam olarak tur 3 R1'de örnek gösterilen yerdi. Aynı paftadaki ayna daire (D2/D5/D8) etiketli olduğu için fark göze batıyor.

İkisi de birkaç dakikalık düzeltme; tasarım kararı gerektirmiyor. Bu iki madde düzelince ONAY verilebilir. 5. turda yalnız bu iki nokta yeniden kontrol edilir.

---

## 1. Tur 3 maddeleri

| # | Madde | Durum | Kanıt |
|---|---|---|---|
| R1 | Etiketsiz pis su parçaları | **BÜYÜK ÖLÇÜDE KAPANDI; E2 açık.** Kullanıcının çizimiyle yan yana etiket yoğunluğu aynı düzeyde (Z_11, K1_11, Z_15, Y_K2_D9). Mutfak, wc+banyo, banyo ve duş parçaları etiketli. 1. kat D6'da kullanıcının kendi çiziminde neredeyse hiç etiket yok; bizde daha fazla var. | `Z_11`, `Z_13`, `Z_15`, `K1_11`, `Y_K1_D6_banyo_wcdus`, `Y_Z_D1_wclvb`, `Y_K2_D9_banyo` |
| R2 | D5/D8 girişi k.bac. şaftından | **KAPANDI.** Şaftta hat yok. Giriş merdiven holünden, daire kapısının yanından. | `Y_K1_D5_giris`, `K1_16`, `K2_16` |
| R3 | Aspiratör notları | **KAPANDI.** wc+banyo ve wc-duş notları 80 m3/h (h 15). Banyo notları 160 m3/h (h 12; kullanıcıda h 15, ama okunaklı ve tek tip). 1. kat D6 wc-duş notu var. T14 ✓, T15 ✓. Notlar ıslak hacmin bitişiğinde. Z D1/D2 notu artık kapı yazısına binmiyor. | `Z_13`, `Z_31`, `K1_13` |
| R4 | Z D2 bulaşık makinesinin pis suyu | **KAPANDI.** `Ø50 4 SB` ile bağlı. | `Z_14` |
| K1 | D3/D5/D8 duş P9 hattı | **KAPANDI.** Hat duvar dibinden gidiyor, süzgeç hattın dışında. | `Z_12`, `K1_12` |

### Otomatik ölçüm (tur 3 → tur 4)

| Test | Tur 3 | Tur 4 | Yorum |
|---|---|---|---|
| T01 | 6 | 4 | Araç sınırı. Balkon süzgecinden yağmur inişine giden yeşil hat var. P9'a bağlantı yok (Z_12'de gözle doğrulandı). "Balkon içinden pis su" bulgusu duş poligonunun balkon sanılmasından geliyor. |
| T02 | 16 | 18 | Uzunluk ve "mahal dışından dolaşma" bulguları. Kullanıcıda bu tür 59 bulgu var. Z D2 BM "mahal dışı" bulgusunun sebebi: P1 ve P4 ortak duvarda. Kullanıcıda da aynı durum var. |
| T03 | 6 | 6 | Kullanıcı da omurgayı ıslak hacmin ortasından geçiriyor (21 BİLGİ). |
| T07 | 88 | 110 | Etiket–etiket örtüşmesi **0**. Kalanlar etiket–mimari yazı (57) ve etiket–hat (53). Kullanıcıda bu tür 208 bulgu var. Gözle bakıldığında yazı üstüne binen etiket görülmedi. |
| T10 | 16 | 16 | Kolonlar kullanıcının koordinatlarında. Araç sınırı. |
| T11 | 1 | 1 | Aynı kaynak. |
| T04, T05, T08, T09, T12–T17 | ✓ | ✓ | — |

### Etiketsiz parça sayımı (bağımsız sayım)

Yöntem: ≥ 20 cm'lik parçalar arasında, 30 cm içinde `n SB` yazısı olmayanlar sayıldı.

| Kat | Üretici | Kullanıcı |
|---|---|---|
| Zemin | 9 | 6 |
| 1. kat | 9 | 16 |
| 2. kat | 5 | 6 |

Bu yöntemde üretici kullanıcıdan farklı değil. Kılavuzla etiketlenen parçalar (D6 banyo klozet/süzgeç/duş) da gözle kontrol edildi; etiketleri var.

Gerçekten etiketsiz kalan, göze çarpan yerler:
- E2: aşağıda.
- Mutfak süzgecinden eviyenin altından omurgaya giden ≤ 70 cm'lik parça (Z/1/2 D1 mutfak; `Y_Z_mutfak_eviye_D1D2`). Kullanıcının mutfağında süzgeç yok, dolayısıyla bu parça da yok. Küçük bir madde; engel değil.

## 2. KALAN MADDELER (RED gerekçesi)

### E1 — 1. kat D6 wc-duş: yer süzgeci duş teknesinin içinde, pis su omurgası teknenin içinden geçiyor. **ENGEL**

- **Ölçüm:**
  - Tekne (mimari, iç çizgi): x 255742…255807, y −442423…−442344.
  - `ROTAS-S2-YER-SUZGECI` @ (255781, −442413): **teknenin içinde**, alt kenara 10 cm.
  - Aspiratör sembolü @ (255761, −442353) de tekne çerçevesinin içinde.
  - Omurga, tekne giderinden çıkıp teknenin içinden y −442394'te ~36 cm gidiyor, sonra klozete ulaşıyor.
  - Tüm şeritte süzgecin tekne içinde olduğu tek yer burası. Otomatik tarama 14 tekneyi kontrol etti.
- **Kullanıcıda:** `SUZGEC1` (255830, −442404) teknenin **dışında**, tekne ile klozet arasında. Tekne giderinden çıkan hat hemen teknenin alt kenarına iniyor, duvar dibinden devam ediyor.
- **Neden hata:** Tekne altında kalan yer süzgeci su toplayamaz. Ayrıca tekne sifonunun bulunduğu bölgeden boru geçirilmiş olur. Kullanıcı bunu görür ve hata sayar.
- **Kanıt:** `Y_K1_D6_banyo_wcdus.png`, sol panel, üst oda.
- **Düzeltme (üretici):**
  - Süzgeç kullanıcının yerine alınmalı: tekne dışında, tekne ile klozet arası, duvar dibi.
  - Tekne giderinden çıkan hat teknenin kenarına (alt kenar ya da duvar dibi) inmeli, oradan omurgaya bağlanmalı.
  - Aspiratör sembolü tekne çerçevesinin dışına alınmalı (kullanıcının notu odanın üstünde).

### E2 — wc-lvb (merdivenin sağı; zemin D1 ve 2. katta aynı konumdaki daire): klozet bağlantısında `Ø100 10 SB` yok. **ENGEL (küçük)**

- **Zemin D1 hatları:**
  - P2 (253735, −442737) → düşey → klozet (253744, −442808). Bu hatta etiket yok.
  - Planda yalnız lavabo kılavuzunda `Ø50 2 SB` var (253784, −442783).
- **2. kat (aynı konum):** Aynı durum. Yalnız `Ø50 2 SB` var (257865, −442724).
- **Aynı paftadaki ayna daire:** D2 wc-lvb'de `Ø100 10 SB` var (253386, −442788). 1. ve 2. kattaki aynalarında da var.
- **Kullanıcıda:** Bu odada `Ø100 10 SB` ×2 ve `Ø50 2 SB` var.
- **Kanıt:** `Y_Z_D1_wclvb.png`, `Z_13` alt, `Y_K2_D9_banyo` alt (wc-lvb).
- **Düzeltme (üretici):** D2'deki etiket bu odaya da konmalı: P2 düşeyi ve klozet bağlantısı, hattın üstüne `Ø100 / 10 SB`. Gerekirse süzgeç parçasına `Ø50 2 SB`.

## 3. Sorulan özel noktalar

**"Hat duş teknesinin içinden geçiyorsa bu kendi başına hata mı?"**

**Hayır**, eğer hat o teknenin kendi giderine gidiyorsa. Kullanıcı da Z/1/2 D3 wc+banyo'da `7 SB` duş branşmanını teknenin içinden çapraz olarak gidere götürüyor (`Z_11` sağ panel). 1. kat D4 banyosunda da hattı teknenin kenarı boyunca çiziyor. Bizim 1. kat D6 **banyo** (4,37 m²) çizimimizde de durum bu:
- Duş branşmanı teknenin üst kenarının ~14 cm içinden kendi giderine gidiyor.
- Etiketli: `Ø50 7 SB`, kılavuzlu.
- Kabul edilebilir.
- İstenirse kenara daha yakın (≤ 5 cm) çizilebilir; bu bilgi notudur.

**Hata olan durum:** Tekne başka bir armatürün yolu olarak kullanılıyorsa ya da teknenin içine süzgeç konmuşsa. 1. kat D6 **wc-duş** bu durumda (E1).

**"Etiketsiz parçalar kat başına 8/8/5; kullanıcı şikâyet eder mi?"**
- Genel olarak **hayır**. Bağımsız sayımda kullanıcının kendi çiziminde de 6/16/6 parça etiketsiz. 1. kat D6'da kullanıcı neredeyse hiç etiket kullanmamış.
- Mutfak eviye branşmanları: eviye kolu kullanıcıda da etiketsiz. Bizde fark yalnız mutfak süzgeci parçası. Bu da B kuralının istediği süzgeçten geliyor.
- **İstisna E2:** İki ayna daireden birinde klozet çapının yazıp diğerinde yazmaması yan yana göze batıyor. Tur 3'te de adıyla bildirilmişti.

## 4. Küçük / bilgi maddeleri (engel değil)

- **B1:** Banyo aspiratör notları h 12 (kullanıcıda h 15). wc notları h 15. Okunaklı.
- **B2:** 2. kat D9 banyoda `Ø50 7 SB` etiketi banyonun üst duvarının dışında, bitişik odada, kılavuzlu. Kural "dar ıslak hacimde mahal dışına kılavuz" buna izin veriyor.
- **B3:** D3/D6/D8 mutfakta P7 çevresinde eviye, BM ve süzgeç kolları sıkışık ama okunaklı (`K2_16`). Kullanıcınınki daha sade.
- **B4:** Tur 3'teki K3 (kolon sembolü iri), K4 (wc-lvb süzgeci) ve K5 (koridor ortası) değişmedi. Kullanıcı kararı.

## 5. Genel görünüm

- **Şerit** (`P_serit_genel`): antet, yerleşim, temel, Z, 1, 2, çatı, şema ve detay sırası tam. T17 ✓.
- **Şema** (`S_genel`): kullanıcının şemasıyla aynı düzende:
  - depo sol üstte,
  - sayaç grubu zemin bandının solunda,
  - P balonları en üstte,
  - D1..D9 blokları,
  - rögar altta,
  - yağmur sağda.
- **Kat planları** (`P_zemin/1kat/2kat_genel`):
  - kolon ve YB yerleri, giriş hatları, kombiler, balkon süzgeçleri kullanıcınınkiyle aynı yerde;
  - karışıklık, etiket yığını ya da daire dışından sıcak su yok.

**RED görüntüleri tekrar ediyor mu?** Hayır. Dördü de (balkon süzgeci → kolon, sayaç kapıda, sıcak su daire dışından, çapraz pis su + etiket yığını) yok.

## 6. Kullanıcıya iletilecek kısa metin

Teslimden önce E1 ve E2 düzeltilip 5. tur hızlı kontrolle onaylanırsa kullanıcıya şu yazılır:

> Sıhhi tesisat tam şeridi kontrolörden geçti. Kolon şeması, kat planları, temel, çatı ve detay paftaları sizin new_block düzeninizde. Önceki RED'lerinizdeki hataların hiçbiri yok (balkon süzgeci, sayaç yeri, daire dışı sıcak su, çapraz hat/etiket yığını). Bilginize iki soru:
> 1. wc-lvb ve mutfakta yer süzgeci konuldu. Sizin çiziminizde yok, ama talimatınız her ıslak hacimde süzgeç istiyor. Kalsın mı?
> 2. Koridorda temiz su hattı duvar dibinden mi, ortadan mı gitsin?

Orkestratör düzeltmeyi yaptırmadan göndermek isterse bu iki maddenin de açıkça söylenmesi gerekir:

> 1. kat D6 wc-duşta süzgeç duş teknesinin içine düşmüş. Zemin D1 ve 2. kattaki aynı konumdaki wc-lvb'de klozet çapı (Ø100 10 SB) yazmıyor.
