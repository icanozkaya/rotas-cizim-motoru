# KONTROL — SIHHİ TAM ŞERİT, TUR 3 (SON TUR) — 15.10.2026

- **Dosya:** `proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf` (commit 096ac7b, 06:11).
- **Bağımsızlık:** Kontrolör bağımsız çalıştı. Üretenin kodu ve "ne yapıldı" notları okunmadı. Yalnız DXF ölçüldü ve gözle incelendi.
- **Ölçütler:**
  - README (C), (B) ve 14.10 kuralları
  - `onay_protokolu.md`
  - `SIHHI_ALTIN_REFERANS.md`
  - 4 RED görüntüsü
  - kullanıcının kendi çizimi `/tmp/claude-0/uu/new_block.dxf`
- **Araç:** `motor/kontrolor/kontrolor.py --mimari ornekler/new_block.dxf.xz`. Ölçüm raporu: `kontrol_png/sihhi_tur3/kontrolor_olcum_raporu.md` (+ `olcum_png/`).
- **Yan yana PNG'ler:** `kontrol_png/sihhi_tur3/`. Tur 2'deki pencerelerle birebir aynı koordinatlarda kırpıldı. Solda kontrol edilen çizim, sağda kullanıcının new_block çizimi var.
- **Ek yakın kırpımlar** `B_*.png` adıyla. Bunların bir kısmı tek panel (yalnız kontrol edilen).

## KARAR: **RED**

Protokol gereği bu son turdu. **Dosya kullanıcıya GÖNDERİLMEZ.** Kalan eksikler aşağıda. Orkestratör kullanıcıya şunu yazmalı: "Kontrolör 3 turda onay vermedi …"

Tur 2 maddelerinin tamamı ya kapandı ya da büyük ölçüde iyileşti:
- 9 kolon, numaralar ve süreklilik doğru.
- ÇM ve BM yerinde.
- Sıcak su kombiden ve daire içinden geliyor.
- Köprü yok. Etiket etiket üstüne binmiyor.
- Şema, rögar, yağmur, çatı ve detay paftaları kullanıcıyla aynı düzende.
- Yeşil uzun kılavuzlar tamamen kalktı.

Ancak kat planlarında **dört engel** var. Bunlardan biri, Y2 düzeltilirken ortaya çıkan bir yan etki.

---

## 1. Tur 2 açık maddeleri (Y1–Y5)

| # | Madde | Durum | Kanıt |
|---|---|---|---|
| Y1 | 1. ve 2. kat D5/D8 wc-banyo lavabosunun pis su bağlantısı yok | **KAPANDI**. Lavabodan düşey branşman ana hatta bağlı (`Ø50 2 SB`). T02'de "LV bağlı değil" bulgusu kalmadı. | `K1_11`, `K2_11`, `B_K1_D5_wcbanyo_ust_tek.png` |
| Y2 | Uzun yeşil kılavuzlar, etiketlerin oda dışına taşınması | **KAPANDI**. Etiketler artık hattın üstünde, kancalı. D3 duş etiketi duşun içinde, balkonda değil. Yan etki için bkz. **R1**. | `Z_12`, `K1_12`, `K2_13` |
| Y3 | Aspiratör notları ıslak hacim dışında ya da hatla kesişiyor; debi tutarsız | **KISMEN**. Notların çoğu kendi ıslak hacmine alındı. Kalan sorunlar **R3**'te. | `Z_13`, `K2_11`, `B_Z_D3_aspirator_notu_koridorda.png` |
| Y4 | Temiz su giriş etiketi oda dışında | **KAPANDI**. Islak hacme giren çiftin etiketi girişte, hattın üstünde. Kanca biçimi kullanıcınınkiyle aynı. | `Z_31`, `K1_13`, `Z_16` |
| Y5 | Şemada ↑/↓ akış okları yok | **KAPANDI**. Şebeke girişinde → var. Depo doldurma düşeyinde ↑, dağıtım düşeyinde ↓ var. | `S_sebeke_sayac`, `S_depo` |

### Otomatik ölçüm (kontrolor.py), tur 2 ile karşılaştırma

| Test | Tur 2 | Tur 3 | Yorum |
|---|---|---|---|
| T01 | ✗ 6 | ✗ 6 | Araç sınırı, tur 2'deki gibi. Süzgeç → YB arasında 31 cm yeşil hat var; pis suyla ortak düğüm yok. Görsel sinyal (balkona taşan etiket ve kılavuz) bu turda kalktı. |
| T02 | ✗ 18 | ✗ 16 | LV bulguları kapandı. Kalanlar uzunluk ve mahal dışından dolaşma bulguları; kullanıcının çizimi aynı ölçümde 59 bulgu veriyor (D6 wc-duş → banyo → P3 yolu kullanıcıda da aynı). **İstisna** olarak Z D2 mutfaktaki "BM bağlı değil" BİLGİ bulgusu gerçek, bkz. **R4**. |
| T03 | ✗ 4 | ✗ 6 | Islak hacmin ortasından geçen omurgalar 103–143 cm. Kullanıcının omurgası da ıslak hacmi çaprazlıyor (21 BİLGİ). Engel sayılmadı, bkz. **K2**. |
| T07 | ✗ 66 | ✗ 88 | Çoğu MTEXT kutusu ve P balonu ↔ merdiven basamak numarası kaynaklı (bilinen sınır). Gözle doğrulananlar **R3**'te. |
| T10 | ✗ 16 | ✗ 16 | Kolonlar kullanıcının koordinatlarında; araç sınırı. |
| T11 | ✗ 1 | ✗ 1 | T07 ile aynı kaynak. |
| T04, T05, T08, T09, T12–T17 | ✓ | ✓ | — |
| Kılavuz (elle ölçüldü) | 8 adet > 1 m, ACI 3 yeşil | **0 adet > 60 cm** (en uzunu 59 cm), ACI 9 gri | Y2 kapandı |

---

## 2. KALAN MADDELER (RED gerekçesi)

### R1 — Kat başına 22–28 pis su parçası etiketsiz; kullanıcının çiziminde her parça etiketli. **ENGEL**

**Ölçüm:** Pis su parçaları (≥ 20 cm) için, 30 cm içinde bir `n SB` etiketi olup olmadığı sayıldı.

| Kat | Bizim parça sayısı | Bizde etiketsiz | Kullanıcının parça sayısı | Kullanıcıda etiketsiz |
|---|---|---|---|---|
| Zemin | 46 | **22** (12'si ≥ 50 cm) | 36 | 2 |
| 1. kat | 50 | **28** (13'ü ≥ 50 cm) | 38 | 2 |
| 2. kat | 45 | **25** (16'sı ≥ 50 cm) | 36 | 2 |

- ALTIN §3.2: "her parça (omurga parçası ve branşman) etiketli". Zeminde 33 etiketin 33'ü bu kurala uyuyor.
- Tur 2'de etiket sayısı daha fazlaydı. Örneğin D3 mutfakta `Ø70 10 SB` vardı (`sihhi_tur2/K1_16`). Bu turda etiketler kılavuzsuz yerleştirilirken sığmayanlar **silinmiş**.

**Göze çarpan yerler:**
- **wc-lvb (D1/D2/D4/D5/D7/D8):** P2/P5'ten klozete ve lavaboya giden üç parçanın hiçbirinde etiket yok. Klozet bağlantısının **Ø100** olduğu planda hiçbir yerde yazmıyor. Kullanıcıda `Ø100 10 SB` ×2 ve `Ø50 2 SB` var. → `B_Z_D1_wclvb_pissu_etiketsiz.png`, `Z_13`, `Z_15`
- **1. kat D5 wc-banyo:** Duş branşmanı P8'e ayrı hatla ve etiketsiz gidiyor. Ayrıca ana hattaki `Ø100 18 SB`, duşun 7 SB'sini içermiyor. P8'e giren toplam yük planda hiçbir yerde okunmuyor. → `B_K1_D5_wcbanyo_dus_bransmani_etiketsiz.png`
- **D3/D5/D8 duş (P9):** P9'dan lavaboya giden 11 SB'lik ana parça etiketsiz. Yalnız branşmanlarda (`7 SB`, `2 SB`) etiket var. → `Z_12`, `K1_12`

**Kullanıcı bunu görür mü?** **Evet.** Yan yana konduğunda bu, ilk göze çarpan fark. Kullanıcının ıslak hacimleri etiketlerle dolu, bizimkiler yarı boş. Klozet hattında çap yazmaması tesisatçı açısından eksik bilgi demek; kullanıcı bunu "çaplar nerede" diye sorar. Etiketin olmaması da kullanıcının istediği "temiz görünüm" sayılmaz, çünkü kendi çiziminde bütün parçalar etiketli.

**Düzeltme (üretici):**
- Her parçaya, kullanıcının bloğu ölçüsünde (kanca 11,7 + 8,3; h 10) hattın üstüne etiket konmalı.
- Sığmayan kısa uç branşmanlarda (< 25 cm) kullanıcının yaptığı gibi kanca ters yöne çevrilebilir ya da etiket parçanın uzantısına kaydırılabilir.
- Hiçbir parça etiketsiz bırakılmamalı.
- ÇM/BM uçlarındaki 2–5 cm'lik parçalar hariç tutulabilir; kullanıcıda da 2 parça etiketsiz.

**Kullanıcıya sorulmalı mı?** Hayır, referans net.

### R2 — 1. ve 2. kat D5/D8 daire giriş ana hattı (soğuk, 1 1/4") `k.bac.` şaftının içinden ve duvardan geçiyor. **ENGEL** (tur 2'de de vardı, kaçırılmış)

**Durum:**
- Merdiven holündeki düşey (≈ 255491, −442095 ve +2048) yatay olarak k.bac.'ın (0,39 m², zeminde "en. odası" olan şaft) içine giriyor.
- Hat şaftın içinden yukarı çıkıyor, k.bac. ile antre arasındaki duvarı delerek antre-kor.'a ulaşıyor (x ≈ 255485).
- Zemin katta aynı yerde hat yok; Z D3 girişi kapıdan.

**Kullanıcıda:** Düşey "5" no'lu daire kapısının (K1 100/220) yanında; hat kapıdan antreye giriyor, `1 1/4" 11.5 MB`.

**İhlal edilen kurallar:**
- 14.10 standart talimatı: "Kolon, asansör boşluğu ve **şaftından hiçbir hat geçmez; enerji odası/şaftından ıslak hat geçmez**."
- "Ana hatlar koridor/ortak alandan dairelere girer."

**Kanıt:** `B_K1_D5_giris_kbac_icinden.png`, `B_K2_D8_giris_kbac_icinden.png`, `B_K1_D5_giris_genel.png`, `K1_16`, `K2_16`. Tur 2'de aynı durum `sihhi_tur2/K1_16`'da görülüyor.

**Düzeltme (üretici):** Düşey ve giriş kullanıcının yerine (kapı yanı, merdiven holü) alınmalı; hat kapıdan girmeli.

**Kullanıcıya sorulmalı mı?** Hayır.

### R3 — Aspiratör notları: debi, yazı boyu, yer. **ENGEL** (Y3'ün kalanı)

**a) Debi yanlış. Tur 2 kontrolör raporunun hatası; düzeltme.**
- Tur 2 raporu "kullanıcının planında hepsi 160 m3/h" diyordu. Bu YANLIŞ.
- Kullanıcının planında (`new_block.dxf`, M-ANNO-TEXT h 15):
  - **wc-banyo D3/D5/D8 → "80 m3/h-50 pa"** (252923 / 254957 / 257005, −442206)
  - **1. kat D6 wc-duş → "80 m3/h-50 pa"** (255762, −442208)
  - **banyolar D1/D2/D4/D6/D7/D9 → "160 m3/h-50 pa"**
- Üretici tur 2 raporuna uyup bütün notları 160 yapmış. Sonuç: D3/D5/D8 wc-banyo planda 160 yazıyor, ama izometride D3-5-8 şaftı 240 m³/h = 3 × 80. Çizim kendi içinde çelişiyor.
- **Düzeltme (üretici):** wc-banyo ve wc-duş notları 80 m3/h olmalı; banyolar 160 kalmalı.

**b) Yazı boyu küçük ve notlar arasında tutarsız.**
- Bizde h **8** (6 not), **10** (Z D1/D2) ve **12** (1. kat D6 banyo) var. Kullanıcıda bütün notlar tek tip h **15**.
- h 8, 1/50 çıktıda 1,6 mm eder. Ekranda ve büyük ölçekte okunuyor, ama çap etiketlerinden (h 10) küçük kalıyor. Kullanıcının notunun yarısı boyunda.
- Yan yana konduğunda (`Z_13`, `Z_31`, `K1_15`) bizim not ıslak hacmin köşesinde küçük bir yazı gibi duruyor; kullanıcınınki odanın en belirgin yazısı.
- Okunaklı mı? **Sınırda.** Teknik resimde alt sınır sayılan 1,8–2,5 mm'nin altında.
- **Düzeltme (üretici):** Bütün notlar tek tip, en az h 10, tercihen h 15 olmalı. Sığmayan yerde kullanıcının yaptığı gibi not ıslak hacmin hemen dışına (bitişik oda, ≤ 60 cm) alınabilir; ama hat ve kapı yazısı üzerine binmemeli.

**c) Yer.**
- **Z D3 wc+banyo:** Not antre-kor.'da. Kılavuzu soğuk/sıcak düşey çiftini kesiyor. Yazı, sıcak su yatayına 2–3 cm mesafede. → `B_Z_D3_aspirator_notu_koridorda.png`, `Z_16`
- **Z D1 banyo:** "160 m3/h-50 pa" satırı K3 kapı yazısına ve kapı yayına değiyor (T07 @ 253860, −442675). → `Z_13`, `Z_31`
- **1. kat D5 wc-banyo:** Not duş teknesinin içinde ve teknenin çapraz çizgisi yazının üstünden geçiyor. → `K1_11`, `B_K1_D5_wcbanyo_dus_bransmani_etiketsiz.png`

**d) 1. kat D6 wc-duş notsuz.**
- Aspiratör sembolü var, not yok.
- Kullanıcıda "Wc Aspiratörü / 80 m3/h-50 pa / Ø150 mm" var; ıslak hacmin üstünde, h 15. → `B_K1_D6_wcdus_aspirator_notu_yok.png`
- T15 bu durumu yakalamıyor, çünkü sembol olduğu için test geçiyor.

**Kullanıcıya sorulmalı mı?** Hayır, debiler kullanıcının kendi planında yazılı.

### R4 — Zemin kat D2 mutfakta bulaşık makinesinin pis su bağlantısı yok. **ENGEL** (küçük; tur 2'de BİLGİ olarak vardı, kaçırılmış)

- **Durum:** B.M. sembolüne (≈ 253533…253561, −443150) yalnız soğuk su geliyor; pis su hattı yok. Aynı mutfak 1. ve 2. katta (D4, D7) ve yan daire D1'de bağlı.
- **Kullanıcıda:** `Ø50 4 SB` var.
- **İhlal edilen kural:** "her dairede bulaşık makinesi hattı" (14.10 standart talimatı).
- **Kanıt:** `B_Z_D2_BM_pissu_yok.png` (karşılaştırma için bağlı olan `B_K1_D4_BM_bagli_karsilastirma.png`), ölçüm raporu T02 BİLGİ @ (253502, −443181).
- **Düzeltme (üretici):** Zemin katta da 1. ve 2. kattaki gibi bağlantı yapılmalı. Yük toplamı güncellenmeli.
- **Kullanıcıya sorulmalı mı?** Hayır.

---

## 3. Küçük / bilgi maddeleri (tek başına RED sebebi değil)

- **K1 — D3/D5/D8 duş, P9 → lavabo ana hattı:**
  - Bizde: 1,48 m²'lik duşu ~130 cm çapraz kesiyor ve süzgeç sembolünün üstünden geçiyor.
  - Kullanıcıda: Hat P9'dan duvar dibinden aşağı iniyor, sonra alt duvar boyunca lavaboya gidiyor (ALTIN §3.2 "D3 duş 90°+0°, duvar dibi").
  - RED-4 görüntüsü (kalın çapraz hat + etiket yığını) kadar kötü değil: hat ince, etiket yok. Ama kullanıcının bu odadaki güzergâhı farklı.
  - Kanıt: `Z_12`, `K1_12`.
  - Kim düzeltmeli: Üretici, R1 ile birlikte; kullanıcının duvar dibi güzergâhına alınmalı.
- **K2 — T03, ıslak hacmin ortasından geçen düz omurgalar (103–143 cm):**
  - Yerler: 1. ve 2. kat D5/D8 wc-banyo'daki yatay ana hat, 2. kat D9 banyodaki düşey hat.
  - Kullanıcı da omurgayı odanın ortasından çapraz geçiriyor. Tarz farkı yok, karmaşa da görülmedi.
  - Bilgi olarak not edildi.
- **K3 — Kolon sembolü:** Bizde içi dolu Ø ≈ 15 cm mor disk ve turuncu halka var; kullanıcıda r 10, yarım dolu, kırmızı flanşlı sembol. Tur 2'de kabul edildi. Yan yana konduğunda daha iri görünüyor, ama "karışıklık" yaratmıyor.
- **K4 — wc-lvb ıslak hacimlerinde süzgeç:** Bizde süzgeç var, kullanıcıda yok. B kuralı "her ıslak hacimde 1 süzgeç" diyor; bizimki kurala uygun. Kullanıcıya sorulabilir, ama engel değil.
- **K5 — T06, koridor hatları ortada mı:** BİLGİ. Kararı kullanıcı verir. Değişmedi.

## 4. Genel izlenim: kullanıcı yan yana koyunca ne der?

- **Şema, temel, çatı, detay paftaları:** "Bu benim düzenim" der. Değişiklik gerekmiyor.
- **Kat planları:** "Karışıklık" demez. Tur 2'deki yeşil kılavuz karmaşası tamamen gitti; etiket etiket üstüne binmiyor. Ama hemen şu iki şeyi söyler:
  1. "Çaplar eksik." wc-lvb'ler, P8 duş hattı ve P9 ana hattı etiketsiz (R1).
  2. "Aspiratör yazıları küçük, birinde debi yanlış, D6 wc-duşta yok" (R3).
- **R2 (şafttan geçen giriş)** kullanıcının açık kuralına aykırı. Kullanıcı görürse ciddi hata sayar.

**RED görüntülerinden biri tekrar ediyor mu?**
- RED-1 (balkon süzgeci → pis su kolonu): **Hayır.** Bağlantı yağmur inişine; balkona taşan etiket de kalktı.
- RED-2 (sayaç kapıda / yanlış şema tarzı): **Hayır.**
- RED-3 (sıcak su daire dışından): **Hayır.** T04 ✓. R2 bir soğuk su güzergâh hatası; sıcak su değil.
- RED-4 (wc-banyo'da çapraz pis su ve üst üste etiket): **Hayır.** Etiket–etiket örtüşmesi 0. K1'deki duş çaprazı yalnız uzaktan benzer, bilgi maddesi olarak yazıldı.

## 5. Değiştirilmeyecekler (doğru bulundu)

Tur 2 listesinin tamamı geçerli. Ek olarak:
- Y1 lavabo bağlantıları
- gri ve kısa kılavuzlar
- hattın üstündeki kancalı etiketler
- temiz su giriş etiketleri
- şemadaki ↑/↓ okları

## 6. Kullanıcıya iletilecek özet (protokol: 3 turda onay yok)

> Kontrolör 3 turda onay vermedi. Kalan eksikler:
> 1. Kat başına 22–28 pis su parçası çapsız/yüksüz (wc-lvb'lerde hiç etiket yok, klozet Ø100 yazmıyor).
> 2. 1. ve 2. kat D5/D8 daire giriş hattı k.bac. şaftının içinden geçiyor.
> 3. Aspiratör notları: wc-banyo ve wc-duş debisi sizin planınızdaki 80 m3/h yerine 160 yazılmış; yazılar h 8–12 (sizinki h 15); Z D3 notu koridorda; 1. kat D6 wc-duşta not yok.
> 4. Zemin kat D2 bulaşık makinesinin pis su bağlantısı yok.
>
> Şema, temel, çatı ve detay paftaları ile kolon yerleri, sıcak su, balkon süzgeci ve etiket çakışmaları tamam. Dört madde motorla düzeltilebilir; kullanıcı kararı gerektiren madde yok. Bilgi için iki soru:
> - wc-lvb'de yer süzgeci olsun mu? (Sizin çiziminizde yok, B kuralı istiyor.)
> - Koridorda hat duvar dibinden mi, ortadan mı geçsin?
>
> Nasıl ilerleyelim: bu 4 maddeyi düzeltip 4. tur kontrol mü yapalım?
