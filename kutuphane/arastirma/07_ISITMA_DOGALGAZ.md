# 07 — Isıtma ve Doğalgaz Proje Çizim Pratiği (Araştırma Notu)

Tarih: 2026-10-14 · Hazırlayan: Claude (ROTAŞ çizim motoru araştırması)

> **Güven etiketi:** Her maddenin sonunda kaynak numarası `[Kn]` var. **[DOĞRULANMADI]** etiketli maddeler,
> araştırma sırasında açık bir kaynakta bulunamayan genel mühendislik pratiğidir. Motor bunları varsayılan
> olarak kullanabilir, ama projeye yazmadan önce ilgili şartnameyle (AKSAGAZ/İGDAŞ) veya Can Bey'le
> teyit edilmelidir.
>
> **Öncelik sırası:** Kullanıcının kendi örnek projesi (`ornekler/new_block.dxf`) ve ROTAŞ/MTY standardı becerisi
> > yerel gaz dağıtım şirketi şartnamesi (Sakarya: **AKSA Sakarya Doğal Gaz**) > bu not.

---

## 0. Kısa özet — motor için kurallar

| Konu | Kural (kısa) | Kaynak |
|---|---|---|
| Isıtma kolon şeması | Düşey ölçekli, yataylar ölçeksiz; gidiş **sürekli**, dönüş **kesikli** çizgi; radyatörler gerçek kotunda | K5 |
| Isıtma hat etiketi (ROTAŞ) | Kümülatif yük + çap: `2070W-DN15`, `12020W-DN25` | K0 |
| Kritik devre numarası | En uzak/en üst radyatörden kazana doğru artan numara (1, 2, 3…) | K5 |
| Boru çapı tablosu (ısıtma) | Hat no · Q · L · Ø · w · R · R×L · Σζ · Z | K5 |
| Su hızı | Branşman 0,2–0,3 m/s; ≤2" ≈1 m/s; büyük çap ≤1,5 m/s (konforda ≤0,8 m/s önerisi) | K5, K12 |
| Yerden ısıtma | PEX 16×2,0, aralık 15 cm (ROTAŞ); devre ≤80 m (ROTAŞ notu); üretici limiti 150 m / 250 mbar | K0, K10 |
| Döşeme yüzey sıcaklığı | Yaşam 29 °C, banyo 33 °C, kenar bölge 35 °C | K10 |
| Gaz basınç kaybı (21 mbar) | Kritik devre ≤1,8 mbar; servis kutusu→sayaç vanası ≤1,0; sayaç→cihaz ≤0,8 | K6, K8 |
| Gaz hızı | 21 mbar: ≤6 m/s; 300 mbar: ≤15 m/s (endüstri ≤25) | K6, K8 |
| Kolon debisi | Bağımsız birim başına ≥3,5 m³/h; >100 birimde f=0,397 | K6, K8 |
| B tipi cihaz hacmi | ≥1 m³/kW; mahal net hacmi ≥8 m³; yatak odası/banyo/WC yasak | K3, K7 |
| Komşu hacim menfezi | 2 × 150 cm², aynı duvar; üst ≥1,80 m, alt ≤0,45 m | K3, K7 |
| Kazan dairesi alt menfez (<1000 kW) | SA = F·a·2,25·(ΣQ+70) cm² | K4, K9 |
| Kazan dairesi (>1000 kW) | SA = ΣQ/3600 m²; SÜ = 0,6·SA | K4, K9 |
| Gaz sayacı | Kazan dairesi **dışında**; G4–G25 körüklü, G40+ rotary/türbin | K2, K4 |
| Kazan dairesi güvenlik | Solenoid vana + ex-proof gaz alarm + CO alarm + siren; acil stop dışarıda | K4, K8 |
| Baca hesabı | Tek cihaz TS EN 13384-1, çoklu cihaz TS EN 13384-2; duman kanalı ≥3° eğim | K1 |

---

## 1. Isıtma projesi — mevzuat ve standart çerçevesi

- **TS 2164** — Kalorifer tesisatı proje hazırlama kuralları (ısı kaybı, boru çapı, kazan/pompa/genleşme seçimi). Türk mühendislik pratiğinde hesap TS 2164 tablolarıyla yürür; ısı kaybı U değerleri **TS 825** sınırlarına uyar (ROTAŞ kuralı: U aşılırsa U küçültülmez, yalıtım revize edilir) [K0].
- **TS EN 12831-1** — Avrupa ısı yükü yöntemi (iletim + havalandırma + yeniden ısıtma). TS 2164'ün artırım katsayılı yöntemi yerine kullanılabilir. Bakanlık BEP-TR ve yeni uygulama kılavuzu taslakları EN 12831'e yönelir [K1].
- **TS EN 1264-1…5** — Yerden ısıtma (ısı akısı, yüzey sıcaklığı sınırı, devre tasarımı) [K10].
- **TS EN 13384-1/-2** — Baca ısıl ve akışkanlar dinamiği hesabı: tek cihaz için -1, birden çok cihaz için -2 [K1].
- **Çevre ve Şehircilik Bakanlığı ısıtma tesisatı uygulama esasları taslağı (2018/2019)**: ısı merkezi yerleşimi, gazlı ısı merkezi, baca ve emniyet kuralları [K1].

### 1.1 TS 2164 ısı kaybı tablosu (artırım katsayıları)

**Birleştirilmiş artırım Z_D (%)** — D = Q₀ / (A_top · (t_i − t_d)) [K12]

| İşletme \ D | 0,10–0,29 | 0,30–0,69 | 0,70–1,49 | ≥1,50 |
|---|---|---|---|---|
| I (sürekli) | 7 | 7 | 7 | 7 |
| II (gece azaltmalı) | 20 | 15 | 15 | 15 |
| III (kesintili) | 30 | 25 | 25 | 15 |

**Yön artırımı Z_H (%)** [K12]

| G | GB | B | KB | K | KD | D | GD |
|---|---|---|---|---|---|---|---|
| −5 | −5 | 0 | +5 | +5 | +5 | 0 | −5 |

- Oda durum katsayısı R: normal pencere/kapılı odada 0,9; tek iç kapılı odada 0,7 [K12].
- Kat artırımı Z_W tablosu kaynak çıkarımında bozuk geldi — motorun kendi tablosundan alınmalı [K12].

**Mahal ısı kaybı tablosu sütunları (TS 2164 Excel düzeni)** — [DOĞRULANMADI, yaygın pratik; ROTAŞ Excel şablonu esastır]

`Mahal No | Mahal Adı | t_i (°C) | Yapı elemanı (DD/DP/K/T/D) | Yön | En (m) | Boy/Yük. (m) | Adet | Alan (m²) | Çıkarılan alan (m²) | Net alan (m²) | U (W/m²K) | Δt (K) | Q₀ (W) | Z_H (%) | Z_D (%) | Z_W (%) | Q_iletim (W) | Q_sızıntı (W) | Q_toplam (W)`

ROTAŞ mahal etiketi: altıgen/yuvarlatılmış çerçevede `20°C` + zon kodu `Z01`, yanında `Kcal/h:` ve ısı kaybı değeri [K0].

---

## 2. Radyatör seçimi ve yerleşimi

### 2.1 Yerleşim
- Radyatör tercihen **pencere altına**, pencere genişliğini mümkün olduğunca kaplayacak şekilde konur (soğuk hava düşüşünü kesmek için). İyi yalıtımlı binada zorunlu değildir [K13].
- Döşemeden **en az 10–15 cm** yükseklik; duvardan **3–5 cm** açıklık [K13].
- Pencere denizliği ile radyatör üstü arasında en az ~10 cm boşluk bırakılır (konveksiyon için) [DOĞRULANMADI].
- Kat planında her radyatörün **tipi ve boyu/dilim sayısı** yazılır. Kolon şemasında radyatörü çevreleyen dikdörtgenin içine **mahal no + mahal sıcaklığı**, üstüne **dilim sayısı/tip** yazılır [K5].

### 2.2 Vana gösterimi
- Gidiş bağlantısında **radyatör vanası** (termostatik veya köşe tip), dönüş bağlantısında **dönüş rakoru / ayar vanası (kilitli)** gösterilir. Termostatik vana kafası sembolü (vana gövdesi + daire/T başlık) kullanılır [DOĞRULANMADI — sembol MTY bloğundan alınmalı].
- Termostatik vana sensörü perde/radyatör örtüsü arkasında kalırsa uzak sensör kullanılır [DOĞRULANMADI].
- Kombi + radyatörlü dairede en az bir oda (referans oda/salon) termostatik vanasız bırakılır veya oda termostatı oraya konur [DOĞRULANMADI, üretici pratiği].

### 2.3 Radyatör kapasitesi
- Seçim: Q_rad ≥ Q_mahal (gerekirse %10–15 emniyet). Kapasite katalogdan **EN 442 ΔT=50 K** değeriyle verilir; 90/70/20 rejiminde ΔT_log ≈ 60 K olduğundan farklı rejim için düzeltme: `Q = Q_50 · (ΔT/50)^n`, n ≈ 1,3 [DOĞRULANMADI — katalog değeri esastır].
- Panel radyatör etiketi önerisi (plan): `PKKP 600×1200 / 2105 W` (tip, yükseklik×boy, kapasite) [DOĞRULANMADI; ROTAŞ'ta ölçü "radyatör katmanı"nda yazılır K0].

---

## 3. Çift borulu radyatör sistemi — kolon şeması formatı

### 3.1 Çizim kuralları
- Kolon şeması kazanı, kollektörleri, boruları, vanaları, ısıtıcıları, genleşme tankını ve armatürleri gösteren **iki boyutlu düşey görünüştür** [K5].
- **Düşey ölçekli**, kaydırılmış yatay hatlar **ölçeksiz** çizilir; radyatörler **gerçek kotlarında** gösterilir [K5].
- **Gidiş hattı sürekli, dönüş hattı kesikli** çizgi — hem kolon şemasında hem kat planlarında [K5].
- Her boru parçasının üzerine **ısı yükü ve uzunluk** yazılır [K5]; ROTAŞ'ta hat etiketi **kümülatif yük + çap**: `2070W-DN15`, `12020W-DN25` (katman STM-ISITMA-CAP) [K0].
- Kritik devrede parçalar **en uzak üst radyatörden kazana doğru** artan numaralarla numaralanır [K5].
- Kat bantları: her katın döşeme çizgisi yatay bant olarak çizilir, solda kat adı ve kotu (`ZEMİN KAT ±0.00`, `1. NORMAL KAT +3.00`) yazılır [K0 — yerden ısıtma şemasındaki kat bandı düzeni; DOĞRULANMADI radyatör için].
- Büyük binalarda pafta başlığı: **"KALORİFER TESİSAT PROJESİ KOLON ŞEMASI"** [K0].

### 3.2 Somut etiket örnekleri
```
Hat etiketi (ROTAŞ):     2070W-DN15          12020W-DN25
Hat no + uzunluk:        (3)  L=4.20 m
Radyatör kutusu:         [ 104 | 20°C ]   üstünde:  PKKP 600/1000  1755 W
Kolon numarası:          K1 / K2 (gidiş-dönüş çifti)
Kat bandı:               2. NORMAL KAT  +6.00
```

### 3.3 Boru çapı hesap tablosu (TS 2164 / Çizelge 3 düzeni) [K5]

| Sütun | İçerik | Birim |
|---|---|---|
| a | Hat (parça) no | — |
| b | Isı yükü Q | kcal/h (W'a çevrilebilir) |
| d | Uzunluk L | m |
| e | Boru çapı | inç / DN |
| f | Hız w | m/s |
| g | R (birim sürtünme kaybı) | mmSS/m (Pa/m) |
| h | R·L | mmSS |
| i | Σζ (Çizelge 4'ten: radyatör 3, T 1,5, dirsek …, radyatör vanası 10) | — |
| k | Z (yerel kayıp) | mmSS |

- Seçim için başlangıç R: küçük tesis **5–8 mmSS/m**, büyük tesis **8–15 mmSS/m** [K5].
- Örnek satır: Parça 1 — 2678 kcal/h, 8 m, ½", w=0,20 m/s, R=4,5 → R·L=36; Σζ=20,5 → Z=32,8 [K5].
- Pompa debisi (90/70, ΔT=20 K): **V = Q_K / 20 000 m³/h** (Q kcal/h) — W cinsinden V = Q / (1,163·ΔT·1000) [K5].
- Pompa basıncı: ΣRL + ΣZ + %10 veya +300…800 mmSS (kazan dairesi kayıpları dahil edilmemişse) [K5].
- Hız sınırı: konfor branşmanı 0,2–0,3 m/s; ≤2" ≈1 m/s; büyük çap ≤1,5 m/s [K5]; tezde üst sınır 0,8 m/s [K12].

---

## 4. Yerden ısıtma (TS EN 1264)

### 4.1 Tasarım değerleri
- Boru aralıkları: **10 / 15 / 20 / 25 / 30 cm** [K10]. Boru boyu ≈ 1/T m/m² (T=0,15 → ~6,7 m/m²) + kollektör bağlantı hatları.
- Maks. devre boyu: üretici sınırı **150 m**, devre başına Δp ≤ **250 mbar** (2×5 m bağlantı dahil) [K10]. **ROTAŞ kuralı: devre ≤ 80 m** ve bu genel not olarak yazılır [K0].
- Yüzey sıcaklığı sınırı: yaşam alanı **29 °C**, banyo **33 °C**, kenar bölge **35 °C** [K10].
- Tasarım gidiş sıcaklığı: θ_V,des = Δθ_H,g + θ_i + 2,5 K; tipik 45–55 °C; tablo baz koşulu θ_i=20 °C (banyo 24 °C), R_λ,B=0,15 m²K/W (banyo 0,02) [K10].
- Isı akısı örneği (14 mm, θ_V 50 °C): q=70 W/m² → T15, maks. alan 11,5 m²; q=50 W/m² → T30 [K10].
- ROTAŞ: PEX 16×2,0, aralık 15 cm; değerlendirme 35 kcal/h·m boru verimi veya ısı kaybı üzerinden; yetersiz mahal "EK ISITMA" sütununda raporlanır [K0].

### 4.2 Kollektör
- Pirinç kollektör: 1" / 1¼" ana bağlantı, ağız aralığı **50 mm**, **3–14 çıkış**, debimetre 1–5 l/dk, maks. 10 bar / 80 °C, baypas 25 kPa [K11].
- Kollektör dolabı kat planında gösterilir; ağızlar **P1…P8** olarak numaralanır [K0].

### 4.3 Plan ve kolon şeması etiketleri (ROTAŞ) [K0]
```
Plan devre etiketi:   3  PEX BORU, 16 × 2.0  1745.0W   49.86 m   Z03
Aralık:               15.0
Şema (devre üstü):    ISIKAYBI 3 / 1745 W / 49.86 m / Z03 / 20°C / PEX BORU 16×2.0
Dönüş hattı:          453.5W-DN15
Kollektör besleme:    8548.8W-DN20
Kat bandı içi:        H. KOMBİ 24KW
```
- Serpantin mahal dışına taşmaz, borular üst üste gelmez, devreler kesişmez [K0].

---

## 5. Kazan dairesi tasarımı ve şeması

### 5.1 Yerleşim (Bakanlık taslağı + MEB)
- Kazan önü ile ön duvar arasında **kazan boyu + 1,00 m** [K1].
- Gazlı ısı merkezi diğer bölümlerden **≥120 dk** yangın dayanımlı bölmelerle ayrılır; 50–350 kW **≥1 kapı**; alan >100 m² veya kapasite >350 kW ise **≥2 çıkış**; kapılar **≥90 dk** yangın dayanımlı, kendiliğinden kapanır, dışa açılır [K1, K4].
- Gaz sayacı ısı merkezi **dışında** [K1, K2, K4].
- Kazan kaidesi bitmiş döşemeden 10–15 cm; brülör alt noktası yerden ≥30 cm [K4].
- Isı merkezine işletme rejimi, min/maks basınç ve emniyet ventili açma basınçları büyük levhada asılır [K1].
- Kanalizasyon kotunun altındaysa pis su çukuru (≥1,0 m³) ve yedekli dalgıç pompa [K1].

### 5.2 Gaz hattı armatür sırası (kazan önü, kaynaktan cihaza) [K4]
`Ana kapama vanası → kompansatör → test nipeli → filtre (50 µm) → regülatör → manometre → min. gaz presostatı → servis solenoid vanası → hava basınç test nipeli → maks. yakma havası presostatı → emniyet solenoid vanası → brülör`
- Bina girişinde kazan dairesi **dışında** gaz kesme vanası + solenoid vana; **ex-proof gaz alarm** (üst menfezden daha yükseğe), **CO alarm**, siren; **acil stop** kazan dairesi dışında (alarm hariç tüm elektriği keser) [K4, K8].
- Esnek bağlantı: kısa, metal örgülü, çalışma basıncının 3 katına dayanıklı, girişinde küresel vana [K4].
- Regülatör maks. kapasitesinin ≤2/3'ünde çalışacak şekilde seçilir [K4].

### 5.3 Hidrolik şema elemanları (kaskad yoğuşmalı)
Şemada gösterilecek elemanlar [K0, K1, DOĞRULANMADI kısımlar işaretli]:
1. **Kaskad kazanlar** (örn. ROTAŞ projesi: 120 + 130 kW yoğuşmalı) [K0] — her kazan çıkışında kazan pompası + çek valf + izolasyon vanası.
2. **Denge kabı (hidrolik ayırıcı)** — örnek ürün: DN65 bağlantı, maks. 10 m³/h, ΔT=20 K'de 233 kW; çamur tahliyesi 2", sensör soketi ½" [K14]. Boyutlandırma pratiği: kap içi hız ≈ **0,1–0,2 m/s**, kap çapı ≈ **3 × bağlantı çapı** ("3D kuralı"), bağlantılar arası mesafe ≈ 3D [DOĞRULANMADI].
3. **Kapalı genleşme tankı** (örn. 300 / 750 l [K0]) — EN 12828 pratiği: `V_n = V_e · (p_e + 1) / (p_e − p_0)`; `p_0 = H_st/10 + 0,2 bar`; `p_e = p_sv − 0,5 bar`; V_e = V_sistem · n (90 °C'de n ≈ %3,55) [DOĞRULANMADI].
4. **Emniyet grubu** — her kazanda kapatılamaz emniyet ventili, manometre, termometre, otomatik hava purjörü; açık genleşme tankı kullanılırsa en yüksek noktada ve kazana en yakın yerde [K1].
5. **Boyler** (örn. 1000–2000 l çift serpantinli [K0]) + boyler şarj pompası + sirkülasyon (resirkülasyon) pompası.
6. **Sirkülasyon pompaları** — frekans konvertörlü ıslak rotorlu [K0]; her zon için ayrı (radyatör / yerden ısıtma karışım vanalı / boyler).
7. **Nötralizasyon ünitesi** — yoğuşma suyu pH ≈ **3,5**, nötralizasyon sonrası ≈ 7–8 [K15]. İsviçre uygulamasında **200 kW** üzeri yoğuşmalı kazanlarda deşarj izne tabidir ve gerekirse nötralizasyon zorunludur [K16]. Türkiye için açık bir kW eşiği bulunamadı → **≥200 kW'ta nötralizasyon ünitesi şemaya eklenmesi önerilir** [DOĞRULANMADI, TR'de belediye/İSU-SASKİ şartına bakılmalı].
8. Kazan dairesi pis su süzgeci, yumuşatma cihazı, doldurma grubu (çek valf + pislik tutucu) [DOĞRULANMADI, yaygın pratik].

### 5.4 Kazan dairesi havalandırması (İGDAŞ 7.4 / Başkentgaz 9.4 / MEB)

**Tabii havalandırma, ΣQ < 1000 kW** [K4, K9]
```
Alt menfez  S_A = F · a · 2,25 · (ΣQ_br + 70)   [cm²]
F: kare/dairesel ya da dikdörtgen (uzun ≤1,5×kısa) = 1 ; ≤5× = 1,1 ; ≤10× = 1,25
a: ızgarasız = 1 ; ızgaralı = 1,2
```
Örnek: ΣQ=250 kW, F=1, a=1,2 → S_A = 864 cm² (≈ 30×30 cm net) [K9].
Hazır değerler (F=1, a=1,2): 125 kW→527 · 150 kW→594 · 250 kW→864 · 375 kW→1201 cm² [K9].

**ΣQ > 1000 kW** [K4, K9]: `S_A = ΣQ / 3600 [m²]`, `S_Ü = 0,6 · S_A`.

**Üst (pis hava) menfezi**: MEB: kW başına 0,5 m³/h atık hava, kesit ≥ **180 cm²**, tavana yakın [K4]. İGDAŞ <1000 kW için ayrı formül vermez → yerel şirketle teyit [K9]. Başkentgaz: üst menfez tavandan ≤40 cm, alt menfez döşemeden ≤45 cm [K9].

**Cebri havalandırma** [K4, K9]

| Brülör | Taze hava (m³/h) | Egzoz (m³/h) | Kanal hızı |
|---|---|---|---|
| Üflemeli | Q·1,184·3,6 | Q·0,781·3,6 | 5–10 m/s |
| Atmosferik | Q·1,304·3,6 | Q·0,709·3,6 | 3–6 m/s |

- Eşdeğer kanal boyu: 90° dirsek 3 m, 45° dirsek 1,5 m, ızgara 0,5 m; **toplam ≥10 m ise cebri zorunlu** [K9].
- Yalnız üst cebri olamaz; fan arızasında brülörü durduran kilitleme; fan motoru ex-proof [K1, K9].
- Alt kanal brülör seviyesine indirilir; alt/üst menfezler kısa devre yapmayacak şekilde zıt/uzak konumlanır [K9].
- Tamamen hermetik (C tipi) cihazlı kazan dairesinde **150 cm²** menfez yeterli [K9].

### 5.5 Baca (TS EN 13384)
- Tek cihaz TS EN 13384-1, çoklu cihaz (kaskad ortak baca) TS EN 13384-2 [K1].
- Baca plakasında: performans sınıfı, cihaz kapasitesi, baca çapı, yükseklik, CE, yanıcıya min. mesafe, montaj tarihi, üretici [K1].
- Metal bacada izolasyon ≥5 cm, ≥80 kg/m³; duman kanalı bacaya **≥3°** yükselen eğim; kazan çıkışından 2D–3D mesafede **½" analiz manşonu** [K1].
- Baca bina mahyasını aşmalı [K1]. Bina içi basınç sınıfları: N1 40 Pa, P1 200 Pa, H1 5000 Pa [K1].
- Bireysel cihaz: müstakil bacaya bağlanır; **etkili baca yüksekliği ≥4 m**; bağlantıda 2–3° yükselen eğim; hızlandırma parçası **≥40 cm** düşey; bacalar düşey, bir kez ≤30° sapma; bağlantı borusu kapı/pencereden ≥40 cm [K7]. Konutta yatay açınım ≤2,5 m [K3]. Şönt baca ve adi baca doğalgazda kullanılmaz [K8].

**Baca hesap tablosu sütunları (TS EN 13384-1 çıktısı)** [DOĞRULANMADI — yazılım çıktısı düzeni]
`Cihaz | Q_N (kW) | Atık gaz debisi ṁ (g/s) | Atık gaz sıcaklığı t_W (°C) | CO₂ (%) | Gerekli itiş P_W (Pa) | Baca iç çapı D_h (mm) | Etkin yükseklik H (m) | Bağlantı boyu L (m) | Dış sıcaklık t_L (°C) | Basınç şartı P_Z ≥ P_W + P_FV + P_L ✔ | Sıcaklık şartı t_iob ≥ t_g ✔ (yoğuşmalıda kuru/ıslak işletme) | Hız w (m/s)`

---

## 6. Doğalgaz iç tesisat projesi (AKSAGAZ / İGDAŞ / GAZDAŞ)

> Sakarya'da dağıtım şirketi **AKSA Sakarya Doğal Gaz** (AKSA grubu). AKSA grubunun ortak dokümanı
> "AKSA Doğal Gaz — Binalar İçin Doğal Gaz Teknik Esasları" (Nisan 2015) PDF'i aranmış, ancak sunucu robots ile
> engellediği için içeriğe ulaşılamadı [K17]. Aşağıdaki kurallar EPDK İç Tesisat Yönetmeliği'ne dayanan
> şartnamelerin (Kargaz, Kırgaz, Palgaz, UDAŞ, İGDAŞ 2017, ESGAZ) ortak içeriğidir. **Proje onayı öncesi
> AKSAGAZ'ın güncel teknik esaslarıyla karşılaştırılmalıdır.** GAZDAŞ (Gaziantep) için ayrı açık şartname bulunamadı.

### 6.1 Proje içeriği ve çizim
- Ölçek: **1/50 veya 1/100**; mimari proje üzerine hatlar, cihazlar ve hesaplar işlenir [K8].
- Pafta seti (uygulama pratiği) [DOĞRULANMADI — sıralama]:
  1. Vaziyet planı (servis kutusu, bina bağlantı hattı, ana vana, gömülü hat) — bina bağlantı hattı projede gösterilmek zorunda [K2].
  2. Kat planları (sayaç yerleri, kolon hatları, daire içi hatlar, cihazlar, menfezler, bacalar).
  3. **İzometrik kolon şeması** (45° izometri; her parçaya çap + uzunluk; hat/nokta numaraları).
  4. Basınç kaybı / çap hesap tablosu.
  5. Kazan dairesi detayı (merkezi sistemde), lejant, notlar, antet + mühendis/firma kaşesi.
- Esnek bağlantı kullanılan projelerde bu durum projede belirtilir [K2].
- Proje 3 takım ozalit + dijital teslim (Kırgaz örneği) [K8].

### 6.2 İzometrik kolon şeması — etiket formatı [DOĞRULANMADI — sektör pratiği; İGDAŞ 2017 Şekil-2 "Tesisat Projelerinde Kullanılan Semboller" esas alınmalı K18]
- Hat noktaları (düğüm) sırayla numaralanır: servis kutusu **0** veya **A**, sonra 1-2-3…; ESGAZ şartnamesinde "18.2 Boru hattının numaralandırılması" ayrı madde [K19].
- Her boru parçasına: `DN25  L=6,40 m` (çelik) veya `Ø1"  6,40 m`; dikey hatlarda kot farkı `h=+3,00`.
- Sayaç: dikdörtgen + `G4` (daire), kazan dairesi için `G16/G25` vb.; sayaç vanası ve test nipeli gösterilir [K2].
- Cihaz: `KOMBİ 24 kW (2,5 m³/h)`, `OCAK 1,6 m³/h`; cihaz vanası.
- Ana vana, acil kesme vanası (bina girişine yatay mesafe ≥15 m ise ek vana) [K2]; kolon havalandırması 150 cm² veya gaz alarm [K7].

```
Örnek izometri etiketleri:
  [0]─DN32 L=4,20─[1]─DN32 L=3,00 h=+3,00─[2] ...
  [5]─▭ G4 ─DN25 L=1,20─[6]─DN20 L=2,80─ KOMBİ 24 kW
                          └─DN20 L=3,10─ OCAK (4 bekli) 1,6 m³/h
```

### 6.3 Basınç kaybı ve çap hesabı [K6, K8]
- **21 mbar servis kutusu çıkışı**: kritik devre toplamı (sayaç hariç) **≤1,8 mbar**; servis kutusu → daire/kazan dairesi sayaç vanası **≤1,0 mbar**; sayaç çıkışı → cihaz **≤0,8 mbar**; hız **≤6 m/s**.
- **300 mbar**: reglaj (21 mbar'a düşürme) → cihaz ≤1,8 mbar; merkezi sistemde evsel noktaya ≤0,7 mbar; servis kutusu → sayaç ≤21 mbar kayıp; hız ≤15 m/s (endüstri ≤25).
- Formüller: `ΔP_R = (ΔP/L)·L` · `ΔP_Z = 3,97·10⁻³·Σξ·V²` · `ΔP_H = 0,049·h` (yükselişte −, düşüşte +) · `ΔP_Σ = ΔP_R + ΔP_Z + ΔP_H`.
- Mutlak basınç: 21 mbar→1,021 bar; 50→1,05; 300→1,3. Yüksek basınç hızı: `V = 353,677·Q / (D²·P₂)` (D mm, Q m³/h).
- Debi: kolonda **bağımsız birim başına ≥3,5 m³/h**; daire toplamı 5 m³/h'i geçmiyorsa ek debi yok; ticari tesiste f=1; **>100 birim beslenen hatta f=0,397** [K8].
- Cihaz debileri: ocak/fırın 1,6 m³/h · kombi 20 000 kcal/h 2,5 · kombi 24 000 kcal/h 3,2 · şofben 2,2 · soba 0,7/1,2 · büyük cihaz: `Q = Kapasite / (8250 · 0,9)` [K6].
- G4 sonrası minimum çap (kaynaklı, 0,8 mbar şartıyla): ayrıma kadar DN25; kombi/soba/şofben DN20; ocak DN20 (dişlide DN15 kabul) [K6].

**Hesap tablosu sütunları** [DOĞRULANMADI — İGDAŞ/ESGAZ çizelge düzeni (ESGAZ 18.7, İGDAŞ Tablo 12–13) içeriği açık kaynakta okunamadı]

| Hat | Cihazlar | Q_top (m³/h) | f | Q_hesap (m³/h) | L (m) | L_eş (m) | DN | V (m/s) | ΔP/L (mbar/m) | ΔP_R | Σξ | ΔP_Z | h (m) | ΔP_H | ΔP_Σ (mbar) | Kümülatif ΔP |

### 6.4 Sayaç yeri [K2, K4]
- G4–G25 körüklü; **G40+** rotary/türbin + konik filtre (50 µm); türbin öncesi/sonrası 5D düz boru.
- Sayaç ortak alanda, bağımsız bölüm girişine yakın; daire içine konmaz; merkezi sistem sayacı kazan dairesine konmaz.
- Sayaç kutusu: her yandan ≥5 cm, duvardan ≥2 cm; elektrik ve sıcak su borusundan ≥15 cm; sayaç vanası merdiven boşluğunda 1,90–2,10 m.
- Ana kapama vanası 1,90–2,10 m, bina girişinde; DN50'ye kadar küresel (TS EN 331), üstü flanşlı (TS 9809).
- Boru mesafeleri: elektrik/telefon/sıcak boru ≥15 cm; pano, paratoner, >1000 V ≥30 cm; havai YG hattı ≥10 m. Kelepçe aralığı ½" 2,0/2,5 m … 2" 3,0/3,5 m (yatay/düşey).

### 6.5 Cihaz yerleştirme ve havalandırma [K3, K7]
- **A tipi (bacasız, ocak)**: mahal ≥12 m³, ≥1 m³/kW; sürekli açık ≥150 cm² menfez; yatak odası/banyo/WC/merdiven yasak; 1+0 konutta kurulamaz.
- **B tipi (bacalı)**: mahal net hacmi **≥8 m³**, **≥1 m³/kW**; yetmezse komşu mahalle **2 × 150 cm²** menfez, **aynı duvarda**, üst ≥1,80 m, alt ≤0,45 m; komşu mahal yatak odası/banyo/WC/ortak alan olamaz; cihaz mahallinde ≥150 cm² sürekli açık menfez; CO dedektörü cihazdan 1,5–3 m içinde. Dolaylı havalandırmada komşu mahalin penceresine ≥150 cm² üst menfez.
- A+B karma, toplam <35 kW → 150 cm² yeterli; ≥35 kW → hesapla.
- **C tipi (hermetik)**: yanma havası/atık gaz ortamdan bağımsız; mahalde dış atmosfere açılan **150 cm²** havalandırma; zemin altı kanal kesiti ≤14 kW 0,5 m², >14 kW 0,75 m² (kısa kenar ≥50 cm); üstü açık avluya atış için avlu ≥200 m².
- Yoğuşmalı cihazda dış havaya açılan menfez gerekiyorsa ≥150 cm².
- Esnek hortum: mutfak cihazı ≤150 cm, kombi/şofben/soba ≤60 cm; her cihaz girişinde kesme vanası.
- Hermetik baca çıkış mesafeleri (pencere, balkon, zemin, köşe): ESGAZ Çizelge-5 "Baca Çıkışlarının Konumu İçin Tavsiye Edilen Boyutlar" — değerler açık metinde okunamadı [K19]; üretici kılavuzu + AKSAGAZ esasından alınmalı.

### 6.6 Doğalgaz kazan dairesi ek kuralları
- İGDAŞ kapsamında kombi/kat kaloriferi ≤70 kW; üzeri "merkezi sistem / kazan dairesi" [K18, K19].
- Kazan dairesi havalandırma formülleri §5.4; sayaç dışarıda; solenoid + gaz alarm + CO alarm + siren zorunlu [K8]; QB ≥1200 kW / <1200 kW için farklı gaz kontrol hattı şekilleri (Palgaz 9.3) [K20].
- Test: <300 mbar işletmede işletme basıncı +50 mbar, 5 dk dengeleme + 5 dk U-manometre, düşüş yok; 300 mbar'da 1,5× dayanım 15 dk + ≥71 mbar sızdırmazlık [K2].

---

## 7. Motor için uygulanabilir şablonlar

### 7.1 Isıtma hesap Excel sayfaları
1. `ISI_KAYBI` — §1.1 sütunları (ROTAŞ Excel şablonu öncelikli).
2. `RADYATOR` — Mahal | Q (W) | Tip | H×L | Q_katalog (ΔT50) | Düzeltilmiş Q | Fazlalık %.
3. `BORU_CAPI` — §3.3 sütunları, kritik devre işaretli.
4. `YERDEN_ISITMA` — Devre | Mahal | Alan | Aralık | Boru boyu | q (W/m²) | Q | Debi (l/h) | Δp | Ek ısıtma.
5. `KAZAN_DAIRESI` — kazan, pompa, genleşme, denge kabı, menfez (§5.4), baca özeti.

### 7.2 Doğalgaz hesap Excel sayfaları
1. `CIHAZLAR` — bağımsız bölüm, cihaz, kW, m³/h.
2. `CAP_HESABI` — §6.3 sütunları, 0,8 / 1,0 / 1,8 mbar kontrolleri koşullu biçimle.
3. `HAVALANDIRMA` — mahal hacmi ≥ 1 m³/kW kontrolü, menfez kararı; kazan dairesi S_A/S_Ü.

### 7.3 Lejant (öneri sembol listesi) [DOĞRULANMADI — MTY blokları esas]
Isıtma: gidiş (sürekli), dönüş (kesikli), radyatör, termostatik vana, dönüş rakoru, küresel vana, çek valf, pislik tutucu, pompa, otomatik purjör, emniyet ventili, manometre, termometre, genleşme tankı, denge kabı, kollektör, 3 yollu vana, boyler.
Doğalgaz: servis kutusu, ana vana, acil kesme vanası, sayaç (G4…), test nipeli, küresel vana, regülatör, filtre, solenoid vana, gaz alarm, CO alarm, kombi (C), ocak (A), şofben (B), menfez (alt/üst), baca, kılıf borusu, izolasyon flanşı.

---

## 8. Kaynaklar

- **K0** — ROTAŞ/MTY proje standardı becerisi (`rotas-mekanik-proje-standardi/SKILL.md`, §4 Isıtma, §10 Yerden ısıtma) — kullanıcının kendi örnek projelerinden çıkarılmış kurallar (yerel).
- **K1** — Çevre ve Şehircilik Bakanlığı, Isıtma Tesisatı Uygulama Esasları Taslağı (31.12.2018): https://webdosya.csb.gov.tr/db/yfk/icerikler/taslak-uk-isitma-tes-sati-31.12.12018-20190610153814.pdf
- **K2** — KARGAZ Doğal Gaz İç Tesisat Teknik Şartnamesi: https://www.kargaz.com.tr/DogalGazPiyasa/Kargaz_ic_tesisat_sartname_web.pdf
- **K3** — Demirkıran Mühendislik, "Cihazların Bağlantıları ve Yerleştirme Kuralları" (İGDAŞ esaslı): https://igdasproje.blogspot.com/2017/10/cihazlarn-baglantlar-ve-yerlestirme.html
- **K4** — MEB MEGEP, "Kazan Dairesi Doğal Gaz Tesisatı" modülü: https://megep.meb.gov.tr/mte_program_modul/moduller_pdf/Kazan%20Dairesi%20Do%C4%9Fal%20Gaz%20Tesisat%C4%B1.pdf
- **K5** — tesisat.org, "Kolon Şeması ve Boru Çapı Hesabı": https://www.tesisat.org/kolon-semasi-ve-boru-capi-hesabi.html
- **K6** — tesisat.org, "Doğalgaz Tesisatı Boru Çapı Hesabı": https://www.tesisat.org/dogalgaz-tesisati-boru-capi-hesabi.html
- **K7** — UDAŞ Doğal Gaz İç Tesisat Şartnamesi: https://udas.com.tr/wp-content/uploads/2020/11/Dogal-gaz-ic-tesisat-sartnamesi.pdf
- **K8** — KIRGAZ Doğal Gaz İç Tesisat Yönetmeliği ve Teknik Şartnamesi: https://www.kirgaz.com.tr/assets/dosyalar/sertifika/kirgazteknik%20sartnamesi.pdf
- **K9** — Projenik, Kazan Dairesi Havalandırma Menfezi Hesabı (İGDAŞ 7.4 / Başkentgaz 9.4): https://projenik.com/hesap/m/kazan-dairesi-havalandirma-menfezi.html
- **K10** — Uponor Klett Twinboard Teknik Bilgi (TR): https://brandportal.uponor.com/asset/ea461bf7-25bb-45b3-930f-1441e7e37091/TI-Klett-Twinboard-TR-1188089-v1.pdf
- **K11** — Caleffi 668 serisi yerden ısıtma kollektörü (TR): https://www.caleffi.com/sites/default/files/media/external-file/01144_TR.pdf
- **K12** — Salim Yusuf, "Isıtma tesisatlarının bilgisayar destekli hesap ve çizim programının geliştirilmesi", Balıkesir Ün. tezi: https://acikerisim.balikesir.edu.tr/bitstreams/c0a6f3f0-9124-40cf-bfb1-94610f53a5f7/download
- **K13** — Vasco, radyatör yerleşimi: https://vasco.eu/en/blog/what-is-the-best-place-for-your-radiators
- **K14** — Reflex hidrolik ayırıcı 160/80 ürün sayfası (TR): https://xom-web.reflex.de/xom-rest/assets/84af47ad-a6cb-43eb-a8c1-078866ee776c/content?locale=tr
- **K15** — Baymak nötralizasyon kabı (Turkchem, sponsorlu içerik): https://turkchem.net/en/advertorial/baymaktan-notralizasyon-kabi-cozumu
- **K16** — Kanton Schwyz, "Abwasser aus Kondensationsheizkesseln": https://www.sz.ch/public/upload/assets/69121/Abwasser_aus_Kondensationsheizkesseln.pdf?fp=1
- **K17** — AKSA Doğal Gaz, Binalar İçin Doğal Gaz Teknik Esasları (Nisan 2015) — erişilemedi (robots engeli): http://www.bandirmagaz.com.tr/utility/Binalar-Icin-Dogalgaz-Teknik-Esaslari-Nisan-2015.pdf
- **K18** — İGDAŞ Doğal Gaz İç Tesisat Teknik Esasları 2017 (yalnız içindekiler/tanımlar okunabildi): https://globalmuhendislik.com.tr/igdas_ictesisat_sartname_2017.pdf
- **K19** — ESGAZ İç Tesisat Teknik Esasları ST.12.02 Rev.1 (yalnız ilk bölümler okunabildi): https://www.esgaz.com.tr/assets/media/pdf/ST.12.02-Ic_Tesisat_Teknik_Esaslari_Rev_1.pdf
- **K20** — PALGAZ İç Tesisat Teknik Şartnamesi PALGAZ-Ş-ITY-01.3 (yalnız ilk bölümler okunabildi): https://online.palgaz.com.tr/uploads/main/190621130721_palgaz.pdf

### Açık kalanlar (sonraki oturumda)
1. AKSAGAZ (Sakarya) güncel teknik esasları — kullanıcıdan PDF istenmeli ya da tarayıcıyla indirilmeli (sunucu robots engelli, proxy bazı .com.tr alanlarını 403 ile reddediyor).
2. Eşzamanlılık katsayısı tablosu (daire sayısı × cihaz kombinasyonu) — İGDAŞ Tablo 13 / ESGAZ Çizelge-10 değerleri açık metinde okunamadı.
3. Hermetik kombi baca çıkış mesafeleri (ESGAZ Çizelge-5).
4. TS 2164 kat artırımı Z_W tablosu ve iç sıcaklık tablosu.
5. Genleşme tankı / denge kabı formülleri için EN 12828 veya üretici (Reflex/Pneumatex) TR kılavuzuyla doğrulama.
