# 10 — Yerden Isıtma Borulama Sistemleri ve Çizim Pratiği (Araştırma Notu)

Tarih: 2026-10-14 · Hazırlayan: Claude (ROTAŞ çizim motoru araştırması)

> **Güven etiketi:** Her maddenin sonunda kaynak numarası `[Kn]` var (liste §9). **[DOĞRULANMADI]** etiketli maddeler
> açık kaynakta birebir bulunamayan, sektör pratiği / mühendislik çıkarımı olan maddelerdir; motor varsayılan olarak
> kullanabilir, projeye yazmadan önce Can Bey'le teyit edilmelidir.
>
> **Öncelik sırası:** Kullanıcının kendi örnekleri (`ornekler/new_block.dxf`, `ornekler/ORNEK_DUZEN.md`,
> `motor/p3/et.py` Emine Tunçel salyangozu, `sablon/ornek_yi.xlsx`) ve README "Kalıcı kurallar" [K0]
> > TS EN 1264 / üretici teknik dokümanı (Uponor TR) > bu not. Bu not `07_ISITMA_DOGALGAZ.md §4` ve
> `05_ALGORITMALAR.md §3`'ü **tamamlar**, onları değiştirmez.

---

## 0. Kısa özet — motor için kurallar

| Konu | Kural (kısa) | Kaynak |
|---|---|---|
| Boru | PEX 16×2,0 (d_i = 12 mm); ROTAŞ varsayılanı | K0 |
| Aralık | Oda 15 cm (varsayılan); banyo / q > 75 W/m² → 10 cm; düşük yük (≤ 40 W/m²) 20–30 cm | K0, K1, K2 |
| Serpantin tipi | Referans proje **meander** (gidiş-dönüş paralel U); `et.py` **bifilar salyangoz**. Banyo/hol/dar mahal → meander; salon/yatak odası → salyangoz (veya kullanıcının seçtiği tarz) | K0, K4, K6, K13 |
| Giriş noktası | Gidiş (sıcak) borusu önce dış duvar / pencere önünden geçer | K6, K13, K16 |
| Kenar şeridi | Duvardan 10 cm (motor); üretici: ≥ 15 cm (REHAU); kenar yalıtım bandı çevrede | K0, K6 |
| Kenar bölgesi (EN 1264) | Genişlik ≤ 1 m, yüzey ≤ 35 °C, aralık 10 cm (Danfoss 12 cm) | K4, K5 |
| Devre uzunluğu | **ROTAŞ ≤ 80 m** (ayaklar dahil); üretici 16×2: 100 m pratik, 110 m maks. (Danfoss) / 150 m & 250 mbar (Uponor) | K0, K5, K1, K12 |
| Devre dengesi | Aynı kollektördeki devreler birbirine ±%10 (REHAU) / "10–15 m" (kb.pl) yakın uzunlukta | K6, K12 |
| Mahal bölme | L_tah = A/s + 2·L_ayak > L_max ise n = ceil(L_tah/L_max) eşit alanlı parça; her parçanın girişi kapıya bakan kenarda | K0, K12 |
| Kollektör | Pirinç 1", 2–12 ağız, ağız aralığı 50 mm, debimetre 1–5 l/dk; ısıtılan hacim **içinde**, mahallerin **ortasında** (hol/antre duvarı, dolap içi), kombiye yakınlık ikinci öncelik; dış duvar/kazan yanı değil | K6, K7, K10, K19, 07-K11 |
| Ayaklar (bağlantı hatları) | Yalnız kendi bağımsız bölümünün holünden ve odanın **kapısından** geçer; duvar içinden, ortak alandan, başka odadan geçmez | K0 |
| Ayak demeti | Koridorda paralel şerit, hat aralığı 5 cm (min. 2×D + şap ≈ 4 cm) [DOĞRULANMADI]; hiçbir hat üst üste binmez; ≥ 5 devrede demet aşırı ısıtır → gidiş ayakları koruma borusunda | K0, K9 |
| Bağlantı sırası | Ağız sırası = odaların koridor boyunca kapı sırası; demet içinde **en yakın oda en dış (kapı tarafı) şeritte**, en uzak oda en iç şeritte; kollektörde merdiven (kademeli stub) çıkış | K0 (et.py), [DOĞRULANMADI] |
| Rejim | ROTAŞ 45/35 °C (ofis/konut yerden); şablon 50/40; ΔT = 10 K; EN 1264 hesabı σ = 5 K | K0, K5 |
| Kombi–kollektör | Kombi gidiş ≤ 55 °C ise karışım grubu gerekmez (kombi kendi pompasıyla); radyatör + yerden karma veya kazan > 55 °C → termostatik karışım vanalı pompa grubu | K4, K14 |
| Kombi–kollektör çapı | Yük/ΔT 10 K → ≤ 6,5 kW DN15, ≤ 12 kW DN20, ≤ 19 kW DN25 (v ≤ 0,8 m/s); ROTAŞ etiketi `8548.8W-DN20` | K0, 07-K5 |
| Devre debisi | ṁ = 0,86·Q/ΔT [l/h]; 1745 W, ΔT 10 K → 150 l/h = 2,5 l/dk | K5, K10 |
| Basınç kaybı | 16×2: 2 l/dk ≈ 1,3 mbar/m; 2,5 l/dk ≈ 2,0; 3 l/dk ≈ 2,7; 4 l/dk ≈ 4,5 mbar/m (Blasius, 40 °C); devre ≤ 250 mbar | K1, K5, hesap |
| Yüzey sıcaklığı | θF = θi + (q/8,92)^(1/1,1); yaşam 29 °C, banyo 33 °C, kenar 35 °C | K0 (şablon), K5 |
| Bükülme yarıçapı | 16 mm: destekli 5×D = 80 mm, serbest 8×D = 128 mm → meander yarım daire s/2 ≥ 80 mm ⇒ s = 15 cm OK, s = 10 cm'de omega/keskin köşe | K1, K3 |
| Çizim | Her devre **tek LWPOLYLINE**, kesişmez, üst üste binmez; etiket MTY-ETIKET (devre) + MTY-RADYATOR MAHAL (mahal); tefriş/mahal yazıları silinmez; mutfak dolabı altına boru girmez; asansör/merdiven/ortak alan ısıtılmaz | K0 |

---

## 1. Serpantin tipleri ve boru aralığı

### 1.1 Tipler

| Tip | Tanım | Isı dağılımı | Nerede |
|---|---|---|---|
| **Meander (tek serpantin, "yılan", linear)** | Boru odanın bir ucundan diğerine s aralığında gidip gelir; giriş ve çıkış aynı kenarda | Giriş tarafı sıcak, çıkış tarafı soğuk (gradyan) | Banyo, WC, antre/hol, koridor, mutfak, dar/uzun mahaller, pencere önü; referans new_block tarzı tüm mahaller | K0, K4, K8, K13 |
| **Çift meander (double meander)** | Gidiş 2s aralığında gider, dönüş aradaki boşluktan döner | Salyangoza yakın eşitlik; döşemesi zahmetli | Kuru/ahşap sistemde salyangoz yapılamıyorsa; Multipipe "mümkünse kaçının" | K8, K16 |
| **Salyangoz (bifilar, counterflow spiral, "snail")** | Gidiş dıştan içe 2s aralığında sarılır, merkezde S ile döner, dönüş gidişin arasından dışa çıkar | Gidiş–dönüş yan yana → en eşit yüzey sıcaklığı (1–2 K fark), daha düşük gidiş sıcaklığı (ısı pompası) | Salon, yatak odası, büyük/kare mahaller; şaplı sistemde tercih; `et.py` bu tipi kullanır | K0, K4, K6, K8, K13 |
| **Kombine** | Kenarda meander + ortada salyangoz | Pencere önü daha sıcak | Büyük cam cepheli salonlar (REHAU "most effective") | K6 |

- Meander'da **gidiş borusu önce en yüksek ısı kaybı olan kenardan** (dış duvar, pencere, balkon kapısı) geçer; iki devreye bölünen odada her iki devre de dış duvara doğru akar [K6, K13, K16].
- Salyangoz "yarım dönüşlerle" döşendiği için 10 cm gibi sık aralıkta meander'dan daha kolay döşenir (tam U dönüşü yok) [K8].
- Tek meander ile büyük oda ısıtılırsa giriş sıcak / cam önü soğuk kalır (kb.pl'deki 55 m², 160 m tek devre örneği) [K12].

### 1.2 Boru aralığı seçimi (s = 10 / 15 / 20 / 25 / 30 cm)

Isı akısı q = Q_mahal / A_döşeme [W/m²] ve döşeme kaplaması direnci R_λ,B'ye göre:

**Uponor Tacker, 16×2 PEX, şap üstü 45 mm, R_λ,B = 0,10 m²K/W, sınır eğrisi (θi 20 °C, θF,max 29 °C)** — kolonlar `q_H,max [W/m²] / Δθ_H [K]` (Δθ_H: ortalama su–oda sıcaklık farkı) [K2 s.17]:

| Aralık | 16×2, şap 35 mm | şap 45 mm | şap 65 mm | şap 75 mm |
|---|---|---|---|---|
| 10 cm | 92,2 / 13,5 | 97,7 / 15,2 | 100 / 17,6 | 100 / 18,7 |
| 15 cm | 86,2 / 14,7 | 94,7 / 17,1 | 98,0 / 19,8 | 98,8 / 21,1 |
| 20 cm | 80,3 / 15,9 | 90,6 / 18,9 | 96,4 / 22,2 | 97,3 / 23,6 |
| 25 cm | 72,5 / 16,7 | 84,4 / 20,3 | 94,3 / 24,8 | 95,9 / 26,3 |
| 30 cm | 64,9 / 17,3 | 77,0 / 21,3 | 90,3 / 27,0 | 93,8 / 29,1 |

Okunuşu: sık aralık aynı yüzey sıcaklığında (29 °C) daha düşük su sıcaklığıyla aynı gücü verir. Yani 15 cm'de 45/35 rejimi (ort. 40 °C, Δθ_H ≈ 20 K @ 20 °C oda) ile ~90 W/m²'ye kadar çıkılabilir; 30 cm'de aynı rejim ~75 W/m² verir.

**Uponor Klett (14/16 mm), gidiş 45 °C, R_λ,B = 0,15 (parke), θi = 20 °C — tasarım q'ya göre önerilen aralık ve tek devrede kaplanabilecek maks. alan (150 m / 250 mbar sınırı)** [K1 §2.2–2.3]:

| q_des [W/m²] | 16 mm, 45 °C: aralık / A_F,max | 16 mm, 50 °C | 16 mm, 55 °C |
|---|---|---|---|
| 55 | 20 cm / 22 m² | 25 cm / 35 m² | 30 cm / 42 m² |
| 50 | 20 cm / 28 m² | 30 cm / 39,5 m² | 30 cm / 42 m² |
| 45 | 25 cm / 35 m² | 30 cm / 42 m² | 30 cm / 42 m² |
| ≤ 40 | 30 cm / 40,5 m² | 30 cm / 42 m² | 30 cm / 42 m² |
| Banyo (θi 24, R 0,02) | 10 cm / 14 m² | 10 cm / 14 m² | 10 cm / 14 m² |

**Motor için seçim tablosu** (ROTAŞ 45/35, PEX 16×2; şap ≈ 45 mm, kaplama seramik 0,02 / parke 0,10–0,15) — K1, K2 tablolarından ve `et.py` kuralından (q > 75 veya θi ≥ 24 → 10 cm) türetilmiştir [DOĞRULANMADI — sayılar üreticiden, eşikler motor kuralı]:

| q = Q/A [W/m²] | Seramik / mermer | Parke 8–16 mm, laminat | Halı (R ≥ 0,15) | Not |
|---|---|---|---|---|
| ≤ 40 | 30 (20) | 20 | 15 | Çok iyi yalıtılmış, ara kat |
| 40–60 | 20 | 15 | 15 | Tipik konut odası |
| 60–75 | 15 | 15 | 10 | ROTAŞ varsayılanı 15 |
| 75–100 | 10 | 10 | 10 + kenar bölgesi | Zemin kat, cam cephe |
| > 100 | 10 + **EK ISITMA** | 10 + EK ISITMA | EK ISITMA | Yerden ısıtma yetmez → panel radyatör / havlupan (Excel "EK ISITMA" sütunu) [K0] |
| Banyo / duş (24 °C) | 10 | – | – | Yüzey 33 °C'ye izin; havlupan eklenebilir |
| Hol / antre (15–18 °C) | 15–20 | 15–20 | – | Referans projede hol ısıtılır [K0]; ayak demeti geçiyorsa ayrı devre açılmayabilir ("HOL (BAĞL. BORULARI)") |

Pratik boru metrajı: L ≈ A/s → 10 cm: 10 m/m², 15 cm: 6,7 m/m², 20 cm: 5 m/m², 30 cm: 3,3 m/m² (+ ayaklar) [07-K10].
Şablon `ornek_yi.xlsx` → "YERDEN ISITMA" sayfası: `MODÜL = 76,263 − 0,539·(Q/A)` W/m², `BORU BOYU` kat planından, `KOLLEKTÖR ADETİ = L/80` (CEILING), birim verim 17,5 W/m @ 50/40 [K0].

### 1.3 Kenar bölgesi (çevre bölgesi, EN 1264)

- Tanım: dış duvar / büyük cam önünde **en fazla 1 m genişliğinde**, yüzey sıcaklığı **35 °C**'ye kadar izinli şerit [K5 s.3,5].
- Aralık: 10 cm (kb.pl), 12 cm (Danfoss pencere önü örneği, 92 W/m²), 15–20 cm (REHAU konut çevre) [K4 s.21, K6 s.30, K13].
- Kenar bölgesi **ayrı devre** olabilir (büyük salon) ya da aynı devrenin ilk sıraları sıklaştırılır (meander'da ilk 3–5 hat s/2 aralıkla) [K6, K15 "peripheral area"].
- ROTAŞ pratiği: kenar bölgesi ayrı gösterilmez; yük yüksekse mahalin tamamı 10 cm; yetmezse EK ISITMA [K0]. Motor seçeneği: `kenar_bolge=True` ise `bolge ∩ cephe.buffer(1.0 m)` içinde s/2 (05 §3.1 Adım B).
- Boru duvardan: motor 10 cm [K0]; REHAU ≥ 15 cm (6") [K6 s.34]; kenar yalıtım bandı (8–10 mm köpük) tüm çevrede ve kolon diplerinde — metraja girer.
- Boru girmeyen alanlar: sabit mutfak dolabı/ada, küvet, duş teknesi, klozet, dolap, betonarme kolon; şömine/soba yakını [K0, K4 s.22, K13, K19]. Ağır mobilya altı (kb.pl) ROTAŞ'ta **tefrişe göre boşaltılmaz** (sadece sabit tesisat/dolap) [K0].

---

## 2. Devre uzunluğu, mahal bölme, devre sayısı

### 2.1 Sınırlar

| Kaynak | 16×2 PEX devre sınırı | Basınç kaybı |
|---|---|---|
| ROTAŞ (proje notu) | **≤ 80 m** (ayaklar dahil); `et.py`: serpantin ≤ 72 m hedef + ~20 m ayak payı → bölme | — [K0] |
| Danfoss | ≤ 100 m, maks. 110 m | ≤ 250 mbar [K5 s.7] |
| Uponor | 150 m (2×5 m bağlantı dahil) | ≤ 250 mbar [K1] |
| REHAU | 1/2" (≈16 mm): 101 m; 5/8": 122 m | su sıcaklık düşümü ≤ 11 K [K6 s.30] |
| h2x, Multipipe | ~100 m; ayak (tek yön) < 20 m | — [K7, K10] |
| kb.pl (uygulama) | 80–100 m güvenli; 120–130 m soğukta/ısı pompasında sorun | — [K12] |

Uzun devrenin sakıncaları: yüksek Δp → pompa yetmez; aynı kollektördeki kısa devre suyu çeker, uzun devre az debi alır; sonunda yüzey soğuk kalır [K12].

### 2.2 Mahal bölme kuralı

```
L_tah = A_bolge / s + 2 · L_ayak            # L_ayak: kollektör → mahal girişi tek yön (kapıdan)
n     = ceil(L_tah / L_max)                 # L_max = 80 m (ROTAŞ)
```
- n > 1 ise mahal **eşit alanlı** n parçaya bölünür; kesim çizgisi kapı duvarına **dik** (ayaklar kapıdan girip her parçaya ulaşabilsin); `et.py`: kapı K/G duvarındaysa x ortasından, D/B'deyse y ortasından ikiye böler, en büyük parça 72 m'yi aşana kadar tekrarlar [K0].
- Bölme yönü alternatifi: zonlara göre (cam önü devresi / oturma alanı / dolaşım) [K12].
- Aynı kollektördeki devreler **±%10** (REHAU) veya en fazla "10–15 m" (kb.pl) fark; 40 m ile 120 m aynı kollektörde dengelenemez [K6 s.34, K12].
- Parça sınırında serpantin bölgesi 3–4 cm daha içeri çekilir (iki parçanın hatları arasına ayak sığsın) [K0 et.py `_spiral`].
- Her parçanın girişi kapıya en yakın köşe; parçalar kapıya uzaklığa göre sıralanıp numaralanır (ipart) [K0].
- Devre adı: mahal kodu + sıra (Z03, 101…; aynı mahalde iki devre aynı zon numarası, ayrı devre no) [K0 Excel: ISITMA ÇEVRİMİ SAYISI sütunu].

### 2.3 Devre sayısı ve kollektör ağzı

- n_devre(daire) = Σ n_i (mahaller) ; hol ayrı devre (referans) veya "bağl. boruları" ile ısınan hol (et.py) [K0].
- Kollektör ağız sayısı = n_devre (yedek ağız bırakılmaz; ROTAŞ "KOLLEKTÖR n AĞIZLI") [K0]. Üretici 2–12 ağız; REHAU "6 devreye kadar küçük kollektörler büyük merkezî kollektöre tercih edilir" [K6 s.32].
- > 10–12 devre → ikinci kollektör (kat/daire bazında) [K6 Tablo 4.3, K14: pompa grubu ≤ 10 devre / 15 kW].

---

## 3. Kollektör

### 3.1 Ağız ve ölçüler
- Pirinç kollektör 1" (≤ 12 devre, ~20 GPM ≈ 4,5 m³/h) veya 1¼"; ağız aralığı **50 mm**; gidiş kollektöründe debimetre (1–5 l/dk), dönüşte termostatik vana / aktüatör; uçlarda hava purjörü + doldurma-boşaltma; girişte küresel vana çifti ve termometre [07-K11, K6 s.15].
- Dolap genişliği ≈ 50 cm + 5 cm × n_ağız (pratik) [DOĞRULANMADI]. Planda ROTAŞ dikdörtgen `MTY-KOLLETOR`, ağızlar 10 cm aralıklı daire çiftleri, yazı "KOLLEKTÖR n AĞIZLI" [K0 et.py].
- Yükseklik: kollektör alt kenarı döşemeden ≥ 25 cm (Ambiente), çalışma yüksekliği 1–1,5 m (h2x); gidiş üstte, dönüş altta [K10, K19].

### 3.2 Yerleşim
- **Isıtılan hacmin içinde** (REHAU "must always be installed within the heated space"); ayak uzunluklarını kısaltacak şekilde servis verdiği mahallerin **ortasında** [K6 s.32, K7, K19].
- Tercih sırası: daire holü/antre duvarı (dolap içi) > koridor nişi > mutfak kombi nişi yanı. Kombiye yakınlık **ikinci** öncelik; "kombinin yanı = dış duvardaki çamaşır odası" tipik hata: ayaklar uzar, 18 m² oda 90 m yerine 150 m boru ister [K7].
- Yatak odası içine konmaz (debimetre/aktüatör sesi) [K10]. Dış duvara, ısıtılmayan hacme (merdiven holü, sığınak) konmaz [K6, K7].
- Kat başına ayrı kollektör; dubleks/çok katlı dairede her kat kendi kollektörü [K10].
- Referans projede kombi mutfak nişinde, kollektör yakınında [K0 ORNEK_DUZEN]. VOYAP ofislerinde kollektör hol duvarında, kapı önünde değil [K0 et.py KOLL].

### 3.3 Ayakların (gidiş-dönüş) kollektöre toplanması
1. **Güzergâh:** her devrenin gidiş-dönüş çifti kollektörden çıkar, holde/koridorda demet halinde ilerler, **odanın kapısından** girip serpantinin giriş köşesine bağlanır. Duvar içinden, başka bağımsız bölümden, ortak alandan, başka odadan geçmez [K0 README].
2. **Demet aralığı:** koridor şeridinde hatlar paralel, aralık 5 cm (`et.py`: ızgara 2 cm, `near_r` 4 cm, dönüş 6 cm); min. fiziksel aralık ≈ 2×D (3–4 cm) [DOĞRULANMADI]. Demetin kapladığı genişlik = (2n − 1)·5 cm; 6 devrede ≈ 55 cm → dar holde (< 1,2 m) iki sıra ayak [DOĞRULANMADI].
3. **Üst üste binme yasağı:** hiçbir hat başka bir hattın üzerinden geçmez (plan tek düzlem, şap içinde boru çaprazlanamaz; kesişme = kot değişimi = şap kalınlığı sorunu) [K0]. `et.py` 4 sıralama dener, en az kesişme puanlısını seçer; hedef 0.
4. **Sıralama kuralı (kesişmesiz demet):** koridor boyunca odalar sırayla ayrılıyorsa, ilk ayrılan (kollektöre en yakın) odanın çifti demetin **o odanın tarafındaki en dış şeridinde**, en uzak oda **en iç şeritte** olur; koridorun iki yanında oda varsa demet iki alt demete bölünür (kuzey tarafı / güney tarafı), her biri kendi tarafına uzaklık sırasıyla dizilir. Soru "en uzak devre dışta mı?" → **hayır**, en uzak devre demetin ortasında/iç tarafında kalır; dışta kalan, ilk ayrılan devredir [DOĞRULANMADI — kesişimsizlik koşulundan türetildi; et.py kapı x sırasıyla aynı sonucu verir].
5. **Kollektörde ağız sırası:** ağızlar koridor yönünde sıralı (en yakın oda kollektörün demete en yakın ucundan değil, **demetin şerit sırasına göre**); her ağızdan 10–12 cm dik "stub" çıkıp sonra demete katılır; stub'lar kademeli (merdiven) uzatılırsa ağız sırası ile şerit sırası kesişmeden eşlenir [K0 et.py `stub`].
6. **Isı birikmesi:** ≥ 5–6 devrede kollektör önündeki demet holü aşırı ısıtır; gidiş ayakları koruma borusu (spiral kılıf) ile yalıtılır, dönüşler yalıtılmaz; alternatif: kollektörü merkeze alıp ayakları kısaltmak [K7, K9]. Kapı eşiği geçişinde kılıf ±38 cm (REHAU: derz geçişinde koruma ≥ 15") [K6 s.22].
7. Ayaklar devre uzunluğuna **dahil** edilir; L_devre = L_serpantin + L_gidiş_ayak + L_dönüş_ayak [K5, K6].

---

## 4. Kombi / ısı kaynağı bağlantısı

### 4.1 Rejim ve karışım
- ROTAŞ: yerden ısıtma **45/35 °C** (ofis/konut), dükkân radyatör 70/50 [K0 README]; şablon 50/40 [K0 Excel]; EN 1264: θ_V,des = Δθ_H + θ_i + 2,5 K, tipik 45–55 °C; şap için ≤ 55 °C, alçı şap ≤ 50 °C [K2, K5 s.7].
- **Yalnız yerden ısıtmalı daire, yoğuşmalı kombi:** kombi gidiş sıcaklığı 45 °C'ye ayarlanır, karışım grubu **gerekmez**; kombi pompası kollektörü besler (Danfoss "low supply temperature applications — mixing shunt not needed") [K4 s.5]. Kombi kapasitesi: pompa artık basıncı Σ(ayak + kollektör + en kötü devre Δp) ≥ 250–300 mbar olmalı [DOĞRULANMADI].
- **Radyatör + yerden karma** veya **kazan ≥ 55 °C** (merkezi sistem, kalorimetreli daire girişi): termostatik **3 yollu karışım vanalı pompa grubu** (yerden ısıtma istasyonu): karışım vanası (35–60 °C ayar), sirkülasyon pompası, emniyet termostatı (55 °C'de pompayı durdurur), gidiş/dönüş termometre, by-pass (tüm devreler kapanınca pompa koruması), kollektör gidiş-dönüş kesme vanaları [K4 s.6–8, K14]. Kapasite: ≤ 10–12 devre / 15 kW (Kv 2,5), ≤ 6 devre / 7,5 kW (Kv 1,6) [K14].
- Merkezi sistemde daire girişi: kalorimetre seti (sayaç dolabı) → yerden ısıtma istasyonu → kollektör; kat bandında "H. KOMBİ 24KW" yerine "KALORİMETRE + Y.I. İSTASYONU" [K0 README (merkezi), DOĞRULANMADI etiket].

### 4.2 Kombi–kollektör hattı
- Debi: ṁ = 0,86·ΣQ/ΔT [l/h]; ΔT = 10 K. Çap seçimi (çelik/PPR, v ≤ 0,8 m/s, R ≤ 150 Pa/m) [07-K5, K10]:

| ΣQ (ΔT 10 K) | Debi | Çap |
|---|---|---|
| ≤ 6,5 kW | ≤ 560 l/h | DN15 (1/2") |
| 6,5–12 kW | 560–1050 l/h | DN20 (3/4") |
| 12–19 kW | 1050–1650 l/h | DN25 (1") |
| 19–30 kW | 1650–2600 l/h | DN32 |

- ROTAŞ planda: kombi HG/HD çıkışından kollektör uçlarına iki hat (gidiş sürekli, dönüş kesikli), ortasına etiket `8548.8W-DN20` (ΣW − çap) [K0 07 §4.3]. Kombi ile kollektör arası hat kollektör ağızlarıyla **kesişmez**; `et.py` önce HG/HD'yi çizer, ayaklar ona paralel gider [K0].
- Kollektör gidiş girişi kollektörün bir ucu, dönüş çıkışı diğer uç (aynı taraftan ters bağlama — Tichelmann gerekmez, debimetreyle dengelenir) [DOĞRULANMADI].

---

## 5. Hidrolik

### 5.1 Devre debisi
```
ṁ_devre [kg/h] = Q_devre [W] · 3600 / (4186 · ΔT)  =  0,86 · Q / ΔT        (ΔT = 10 K → 0,086 · Q)
ṁ [l/dk] = ṁ [l/h] / 60
```
EN 1264 tam hesabı (tesisat.org TS EN 1264-2/3 modülü, beceri §3): ṁ = A_F·[q·(1 + R_o/R_u) + (θi − θu)/R_u] / (c_W·σ), σ = 5 K [K5 s.6, K17].
Örnekler (ΔT 10 K): 1000 W → 1,4 l/dk; 1745 W → 2,5 l/dk; 2500 W → 3,6 l/dk; 3500 W → 5 l/dk (debimetre üst sınırı; devreyi böl) [K5, 07-K11].
ΔT'yi 5 K'ya indirmek debiyi 2 katına, Δp'yi ~3,5 katına çıkarır [K5 s.7].

### 5.2 Basınç kaybı
```
Δp = λ · (L/d_i) · ρ·v²/2 + Σζ·ρ·v²/2 ;  λ = 0,3164 / Re^0,25 (Blasius, pürüzsüz PEX, 2300 < Re < 1e5)
v = ṁ / (ρ · π d_i²/4) ;  Re = v·d_i/ν ;  ν(40 °C) ≈ 0,66e-6 m²/s ; d_i = 12 mm (16×2)
```
Hesaplanmış tablo (16×2 PEX, 40 °C) — üretici diyagramıyla aynı mertebede (Uponor Tecto s.11: 0,1–0,6 m/s) [K3, hesap]:

| Debi | v [m/s] | Re | R [mbar/m] | 80 m devre + %10 dirsek/ayak | Sonuç |
|---|---|---|---|---|---|
| 1,5 l/dk | 0,22 | 4 000 | 0,8 | 70 mbar | OK |
| 2,0 l/dk | 0,29 | 5 400 | 1,3 | 117 mbar | OK |
| 2,5 l/dk | 0,37 | 6 700 | 2,0 | 172 mbar | OK |
| 3,0 l/dk | 0,44 | 8 100 | 2,7 | 238 mbar | sınırda (≤ 250) |
| 4,0 l/dk | 0,59 | 10 800 | 4,5 | 394 mbar | **aşıyor** → devreyi böl / s'yi aç |

Kural: 16×2 ve 80 m'de devre yükü ≤ ~2,0 kW (ΔT 10 K) tutulur; üstü ikiye bölünür [DOĞRULANMADI — tablodan]. Sistem Δp = en kötü devre + ayak + kollektör (~50 mbar debimetre/vana) + kombi-kollektör hattı; kombi pompası eğrisiyle karşılaştırılır.

### 5.3 Kollektör dengeleme
- Tüm devreler aynı Δp görür (paralel); en uzun/en yüklü devre debimetresi tam açık, diğerleri hesaplanan l/dk değerine kısılır; Danfoss/REHAU: devre uzunlukları ±%10 içindeyse ön ayar yeterli [K6 s.34, K12].
- Proje tablosu sütunları: Devre no · Mahal · Q [W] · A [m²] · s [cm] · L_serpantin · L_ayak · L_toplam [m] · ṁ [l/h, l/dk] · R·L + Z [mbar] · debimetre ayarı [l/dk] [DOĞRULANMADI — öneri; şablon "MMO YERDEN ISITMA" sayfası satır 1–16'ya ṁ ve Δp satırı eklenebilir].
- Isı pompası / düşük sıcaklıkta kollektöre by-pass fark basınç vanası 25 kPa [07-K11].

---

## 6. Çizim pratiği (ROTAŞ / MTY / tesisat.org)

### 6.1 Plan gösterimi
- Katman/renk: serpantin `MTY-YERDEN` benzeri ısıtma katmanı, gidiş kırmızı sürekli, dönüş mavi/kesikli (kolon şemasında); planda devre tek renk, tek **LWPOLYLINE**, patlatılmaz [K0 README, 07].
- Serpantin köşeleri planda **keskin 90°** çizilir (referans new_block), yuvarlatma isteğe bağlı (gerçek döşemede r ≥ 5×D) [K0].
- Serpantin mahal dışına taşmaz; duvardan 10 cm; sabit dolap/küvet altına girmez; tefriş ve mahal yazıları silinmez (serpantin altına girer, yazı maskesi ile) [K0].
- Ayaklar kapıdan geçer; koridorda paralel şerit; kollektöre merdiven bağlantı [K0].
- Kollektör: dikdörtgen + ağız daireleri + "KOLLEKTÖR 6 AĞIZLI"; kombi: kullanıcı bloğu (sarı), HG/HD çıkış noktaları [K0 et.py].
- Mahal etiketi `MTY-RADYATOR MAHAL`: yuvarlatılmış kutu, cyan "20°C" / kırmızı "Z05", mahal adı; altında Q [W] ve A [m²] [K0 ORNEK_DUZEN].
- Devre etiketi `MTY-ETIKET` (sarı tablo, çerçeveli, altı maskeli):
  ```
  Hat uzunluğu: 53.37 m
  Modülasyon aralığı: 15.0
  Kcal/h: 1867.9 W
  Isıtma devresi no: 4
  ```
  Kısa biçim (07 §4.3): `3  PEX BORU, 16 × 2.0  1745.0W  49.86 m  Z03` + aralık `15.0` [K0].
- Etiket mahal içinde serpantin üstüne, tefrişle çakışmayan yere (05 §5 açgözlü yerleştirme); küçük mahalde (< 1,6 m kenar) yazı yüksekliği 4, diğerlerinde 5 [K0 et.py].
- tesisat.org online aracı sütunları: hat no · oda no · oda adı · oda sıcaklığı (15/18/20/22/24) · kaplama (mermer/seramik/parke 8/parke 16/halı) · ısı kaybı W · oda alanı · modülasyon alanı · M5…M30 aralık · boru boyu · devre sayısı (L / sabit devre boyu, yukarı yuvarlanır) · karşılama oranı · yüzey sıcaklığı kontrolü (29 °C; 24 °C mahallerde daha yüksek) [K17].
- MTY CAD: "Yerden ısıtma çizimi hesabı ve metrajı" (video; salyangoz/meander/U, kollektör ekleme, metraj Excel'e aktarma) — yazılı kural yok [K18].

### 6.2 Kolon şeması (kat bantlı)
- Her kat bir yatay bant; bant içinde daire başına: **kombi** (sarı blok, "H. KOMBİ 24KW") → gidiş/dönüş hattı (`8548.8W-DN20`) → **kollektör** (`MTY-RADYATOR KOLLEKTÖR KOLON` bloğu) → devreler yan yana panel sembolleriyle, gidiş/dönüş hatları altta [K0 ORNEK_DUZEN].
- Devre üstü etiket: `ISIKAYBI 3 / 1745 W / 49.86 m / Z03 / 20°C / PEX BORU 16×2.0`; devre dönüş hattı `453.5W-DN15` [K0 07 §4.3].
- Merkezi sistemde: kazan dairesi → kolon → kat bandında kalorimetre + Y.I. istasyonu (karışım vanası, pompa) → kollektör [K0 README merkezi kural].
- Isıtma kolon şeması genel kuralları (düşey ölçekli, gidiş sürekli / dönüş kesikli) 07 §3.1'de [07-K5].

### 6.3 Metraj (yerden ısıtma)
| Kalem | Birim | Hesap |
|---|---|---|
| PEX 16×2,0 boru | m | Σ(L_serpantin + 2·L_ayak) + %3–5 fire (h2x %5–10) [K10] |
| Kollektör n ağız (debimetreli) + dolap | ad | daire/kat başına |
| Kollektör küresel vana, termometre, purjör, doldurma seti | tk | kollektör başına |
| Karışım vanalı pompa grubu (gerekiyorsa) | ad | §4.1 |
| Yalıtım plakası (EPS/tırnaklı) + folyo | m² | Σ A_ısıtılan |
| Kenar yalıtım bandı | m | Σ mahal çevresi + kolon çevreleri |
| Boru klipsi / ray | ad | ≈ 2–3 ad/m boru [DOĞRULANMADI] |
| Koruma (spiral) borusu | m | kapı eşiği geçişleri 2×0,5 m + kollektör önü gidiş ayakları [K6, K9] |
| Genleşme derzi profili | m | 40 m² / 8 m kenar üstü alanlar, kapı eşikleri [K6 s.21–22] |
| Şap (yerden ısıtma katkılı) | m² | Σ A, kalınlık boru üstü ≥ 45 mm [beceri §3] |
| Oda termostatı + aktüatör | ad | devre/mahal başına (isteğe bağlı) |

Excel: `ornek_yi.xlsx` "YERDEN ISITMA" + "MMO YERDEN ISITMA" sayfaları formülleri bozulmadan doldurulur; mahal m² mimariyle aynı; dcm logosu temizlenir [K0 README].

---

## 7. Algoritma — shapely ile mahal poligonundan serpantin üretimi (sözde kod)

`05_ALGORITMALAR.md §3`'ün uygulanabilir ayrıntısı. Birim cm; D = 1,6 (boru dış çapı), s = aralık (10/15/20), R_min = 5·D = 8 cm.
Mevcut kod: `motor/spiral3.bifilar(poly_pts, entry_corner, first, s)` (dik açılı poligon), `motor/p3/et.py::_circuits/_spiral/_heat_routes` (bölme + A* ayaklar).

### 7.1 Isıtılacak bölge
```python
def bolge_hazirla(mahal: Polygon, engeller: list[Polygon], kenar=10.0, kenar_bolge_cephe: LineString|None=None):
    b = mahal.buffer(-kenar, join_style="mitre")                      # duvardan 10 cm
    b = b.difference(unary_union([e.buffer(5, join_style="mitre") for e in engeller]))  # dolap, küvet, kolon +5 cm
    parcalar = [p for p in getattr(b, "geoms", [b]) if p.area > (2*s)**2]   # çok küçük artıklar atılır
    # kenar bölgesi (isteğe bağlı): cephe önü 100 cm şerit → s/2 ile ayrı doldurulur
    kb = b.intersection(kenar_bolge_cephe.buffer(100)) if kenar_bolge_cephe else None
    return parcalar, kb
```

### 7.2 Serpantin tipi ve giriş köşesi seçimi
```python
def tip_sec(mahal_adi, poly, q, ti, kullanici_tarzi="meander"):
    if kullanici_tarzi: return kullanici_tarzi            # ROTAŞ: referans projenin tarzı (meander) ya da et.py salyangoz
    mrr = poly.minimum_rotated_rectangle; a, b = kenarlar(mrr)
    if mahal_adi in BANYO_WC_HOL or min(a,b) < 4*s or max(a,b)/min(a,b) > 2.5: return "meander"
    return "salyangoz"

def giris_kosesi(poly, kapi_pt, dis_duvar: LineString|None):
    # 1) kapıya en yakın köşe (ayak kısa); 2) eşitlikte dış duvara bitişik köşe (gidiş önce soğuk kenardan)
    koseler = list(poly.exterior.coords)[:-1]
    return min(koseler, key=lambda c: (round(dist(c, kapi_pt)/50), -(dis_duvar.distance(Point(c)) < 1) if dis_duvar else 0))
```

### 7.3 Meander (scanline)
```python
def meander(poly, s, giris, dis_duvar=None, r_kose=None):
    # eksen: dış duvara PARALEL hatlar (ilk hat cam önünde en sıcak) — yoksa en uzun kenar yönü
    aci = acisi(dis_duvar) if dis_duvar else uzun_kenar_acisi(poly.minimum_rotated_rectangle)
    P = rotate(poly, -aci, origin=giris); g = rotate(Point(giris), -aci, origin=giris)
    x0,y0,x1,y1 = P.bounds
    yon = +1 if g.y < (y0+y1)/2 else -1          # giriş alt kenardaysa yukarı doğru tara
    y = (y0 if yon>0 else y1) + yon*s/2 ; yol = []; sol_sag = +1 if g.x < (x0+x1)/2 else -1
    while y0 <= y <= y1:
        kesit = P.intersection(LineString([(x0-1,y),(x1+1,y)]))        # LineString | MultiLineString
        parca = en_uzun(kesit)                                           # girintili mahalde: §7.6 dikdörtgen ayrıştırma
        a, b = parca.coords[0], parca.coords[-1]
        yol += [a, b] if sol_sag > 0 else [b, a]
        sol_sag *= -1 ; y += yon*s
    # dönüşler: keskin köşe (plan) — r_kose verilirse yarım daire r=s/2 (s/2 >= R_min değilse omega: 2s genişlik)
    # gidiş ve dönüş = aynı polyline (U'nun iki bacağı): giriş yol[0], çıkış yol[-1]; her ikisi giriş kenarında olsun diye
    # hat sayısı TEK ise son hattı s/2 kısaltıp "çift meander" bacağıyla kapat ya da hat sayısını çift yap (y aralığını ayarla)
    return rotate(LineString(yol), aci, origin=giris)
```
Kurallar: hat sayısı çift → giriş ve çıkış aynı (kapı) kenarında; tek kalırsa son hat yarım bırakılıp ters yönde dönülür. Yol uzunluğu `LineString.length/100` m.

### 7.4 Salyangoz (bifilar, offset halkalar)
```python
def salyangoz(poly, s, giris):
    halkalar = []; d = s/2
    while True:
        r = poly.buffer(-d, join_style="mitre")
        if r.is_empty or r.area < (s)**2 : break
        r = en_buyuk(r)                                   # MultiPolygon: diğer parçalar ayrı alt-devre (nadiren)
        halkalar.append(r.exterior); d += s                # halka aralığı s → gidiş halkaları 0,2,4.. ; dönüş 1,3,5..
    # kesme noktası: giriş köşesine en yakın nokta; her halka orada açılır
    gidis = [kes(h, giris) for h in halkalar[0::2]]        # dıştan içe
    donus = [kes(h, giris) for h in halkalar[1::2]]
    # bağla: gidiş_k sonu → gidiş_{k+1} başı (çapraz atlama, uzunluk s, kesme noktasının hemen yanında)
    # merkezde: en içteki gidiş sonu → en içteki dönüş başı (U, r = s/2 ≥ R_min → s ≥ 16 cm; s=10/15 için keskin S kabul)
    # dönüş: içten dışa, aynı kesme noktasından, gidişin aralarından çıkar
    yol = zincir(gidis) + merkez_U + zincir(reversed(donus))
    assert check_self(yol, s)                              # motor/spiral3.check_self: kendini kesmez, min aralık s-ε
    return LineString(yol)
```
Dik açılı poligonda `spiral3.bifilar` aynı işi köşe-yürüyüşüyle yapar; genel poligonda buffer yöntemi + Fermat spirali bağlama [K20]. `buffer(-d)` dar boğazlarda halkayı koparırsa (MultiPolygon) → §7.6'ya göre önce dikdörtgenlere ayır.

### 7.5 Ayak demeti (kollektör → giriş) ve kesişme garantisi
```python
def ayaklar(kollektor, devreler, hol_poly, kapilar, s_ayak=5.0):
    # 1) izinli alan: yalnız bu bağımsız bölümün holü + hedef odanın kapı boşluğu + hedef oda (kendi serpantini hariç)
    # 2) sıralama: devreleri kollektörden kapıya "koridor eksenindeki ayrılma noktası"na göre sırala (yakından uzağa)
    #    her taraf (koridorun sol/sağ tarafı) ayrı alt-demet
    # 3) şerit atama: taraf T'de k. ayrılan devre → T tarafından k. şerit çifti (gidiş iç, dönüş dış veya tersi — sabit)
    #    ofset = kenar + s_ayak*(2k-1), s_ayak*(2k)   (ortogonal "nudging", 05 §2 Yaklaşım 1)
    # 4) ağız eşleme: ağız sırası = şerit sırası; ağızdan dik stub L_stub = 10 + 2*k cm (merdiven) → kesişmesiz fan
    # 5) güzergâh: omurga = hol ekseni (medial axis / kapı-kollektör A*), her çift omurgaya ofset ile paralel;
    #    kapıdan dik girip serpantin giriş köşesine (yol[0]) ve çıkışına (yol[-1]) bağlan
    # 6) kesişme kontrolü: tüm hatların unary_union'ı; her çift (i,j) için  Li.intersects(Lj) ⇒ HATA → sıralamayı değiştir
    #    aralık kontrolü: Li.buffer(s_ayak/2 - 0.5).intersects(Lj) ⇒ HATA (üst üste / çok yakın)
    # 7) devre uzunluğu: L = serp + gidiş_ayak + dönüş_ayak ≤ 80 m değilse §2.2 ile böl, tekrar
```
Kesişme garantisi: (a) aynı koridorda çiftler sabit şerit sırasını korur (düz gidişte, dönüşlerde "mitre" ile sıra korunur); (b) ayrılan çift her zaman kendi tarafının en dış şeridinde olduğundan dışarı dönerken kimseyi kesmez; (c) kollektörde kademeli stub + monoton ağız sırası; (d) odaya giren çift serpantinin giriş köşesine geldiği için serpantini kesmez (serpantin bölgesi köşeye kadar boş bırakılır: `_spiral` parça sınırında 3–4 cm pay). Bu dört koşul sağlanınca kontrol (6) her zaman geçer; geçmezse `et.py` gibi 4 sıralama denenip en az kesişen seçilir ve uyarı verilir.

### 7.6 Girintili / L mahaller
```
dikdortgenler = rects_in(poly)                 # motor/rooms.py; en büyük dikdörtgen + kalanlar
ana = en büyük; her ek parça için: s*2'den dar ise atla; değilse ana ile aynı devrede "uzatma" (meander'ın ek şeridi)
ya da alan payı büyükse ayrı devre (§2.2)
```
### 7.7 Çıktı
Her devre: `dict(devre_no, mahal, zon, s, yol: LineString (tek polyline), L_serp, L_ayak, L, W, ṁ, Δp, agiz)` → DXF (LWPOLYLINE + MTY-ETIKET + MAHAL), kolon şeması bandı, Excel satırı (§6.3), metraj.

---

## 8. Açık kalanlar
- Kullanıcıdan teyit: varsayılan serpantin tarzı (referans meander mi, Emine Tunçel salyangoz mu — README 13.10: "ısıtma/yerden ısıtma = Emine Tunçel et.py salyangoz + kapıdan geçen ayaklar").
- Ayak demeti aralığı (5 cm) ve koruma borusu gösterimi (planda çizilsin mi).
- Kollektör dolabı plan ölçüsü ve kalorimetreli merkezi sistemde istasyon etiketi.
- TS EN 1264-2 tam tablolar (K_H, Δθ_H) — tesisat.org modülü kopyalanamaz; üretici (Uponor TR) tabloları yukarıda.

---

## 9. Kaynaklar
- **K0** Kullanıcı referansları: `ornekler/new_block.dxf`, `ornekler/ORNEK_DUZEN.md` ("Yerden ısıtma tarzı"), `motor/p3/et.py` (`_circuits`, `_spiral`, `_heat_routes`), `motor/spiral3.py`, `sablon/ornek_yi.xlsx` ("YERDEN ISITMA", "MMO YERDEN ISITMA"), README "Kalıcı kurallar"; `07_ISITMA_DOGALGAZ.md §4` (07-K5, 07-K10, 07-K11 oradaki numaralar).
- **K1** Uponor Klett Twinboard — Teknik Bilgi (TR): boru aralığı / q_des / A_F,max tabloları 14 ve 16 mm, 150 m, 250 mbar, 5×D / 8×D bükülme — https://brandportal.uponor.com/asset/ea461bf7-25bb-45b3-930f-1441e7e37091/TI-Klett-Twinboard-TR-1188089-v1.pdf
- **K2** Uponor Tacker — Teknik Bilgi (TR): 16/17/20×2 boru, 10–30 cm aralık, şap kalınlığına göre q_H ve Δθ_H tabloları (s.16–27) — https://brandportal.uponor.com/asset/d6094bbc-9867-40e5-a680-a98b3996e01e/TI-Tacker-UFH-C-TR-1188086-v2.pdf
- **K3** Uponor Tecto — Teknik Bilgi (TR): basınç kaybı diyagramı 16×2 (0,1–0,6 m/s), bükülme 80/128 mm — https://brandportal.uponor.com/asset/c45f68d6-7490-43c4-a3e6-f9410c66f357/TI-Tecto-TN-TL-TR-1240154-v1.pdf
- **K4** Danfoss Floor Heating Application Guide (meander/snail karşılaştırması s.20, pencere önü 120 mm s.21, banyo salyangoz s.22, büyük oda 3 devre s.23, mutfak dolabı altı yasak, karışım şant ne zaman) — https://assets.danfoss.com/documents/latest/186594/AB179586476913en-020402.pdf
- **K5** Danfoss Floor Heating Design Guide (EN 1264 yüzey 29/33/35 °C, kenar bölgesi ≤ 1 m, devre ≤ 100 m / 110 m maks, 250 mbar, σ = 5 K, ṁ = V_H/n, ayak = 2 × mesafe) — https://assets.danfoss.com/documents/100650/AG000086464394en-010201.pdf
- **K6** REHAU Radiant Heating Systems Design Guide (counterflow spiral / serpentine / kombine s.34; çevre aralığı 6–8" s.30; duvardan ≥ 6"; Tablo 6.1 devre uzunlukları; kollektör ısıtılan hacim içinde s.32; devreler ±%10 s.34; derz geçişi 15") — https://www.rehau.com/downloads/497804/radiantheatingsystemsdesignguide-855601-rehau.pdf
- **K7** Multipipe — Manifold location (merkezî yerleşim, kazan yanı/dış duvar hatası, ayak < 20 m, ≥ 6 devrede ısı birikmesi) — https://www.multipipe.co.uk/knowledge-base/manifold-location-important/
- **K8** Multipipe — UFH patterns (bifilar / meander / double meander) — https://multipipe.co.uk/ufh-patterns
- **K9** Multipipe — Controlling the feeds (≥ 5 devrede koruma borusu, yalnız gidiş yalıtılır, duvardan geçiş) — https://multipipe.co.uk/controlling-the-feeds-in-an-ufh-system
- **K10** h2x — Underfloor heating design guide (kollektör 1–1,5 m yükseklik, merkezî, yatak odasından uzak, kat başına; 16 mm ≤ 100 m; debi formülü; v ≤ 1 m/s; L = (A/s + ayak)·1,1) — https://www.h2xengineering.com/blogs/underfloor-heating-design-guide-radiant/
- **K11** h2x — UFH settings (loop shape serpentine/spiral, min bend radius, transit spacing, perimeter offset parametreleri) — https://help.h2xengineering.com/settings/systems/underfloor-heating
- **K12** kb.pl — Maksymalna długość pętli (16×2: 80–100 m, uzun devre sorunları, 40 m² → 3×85–90 m, kollektörde benzer uzunluk) — https://kb.pl/aktualnosci/ogrzewanie/maksymalna-dlugosc-petli-ogrzewania-podlogowego/
- **K13** kb.pl — Błąd przy układaniu podłogówki (meander küçük/koridor/pencere, salyangoz salon; giriş dış duvardan; kenar 10 cm; sabit mobilya altı yok) — https://kb.pl/aktualnosci/ogrzewanie/blad-przy-samodzielnym-ukladaniu-podlogowki/
- **K14** KAN-therm — Underfloor heating pump group (karışım grubu bileşenleri, ≤ 10 devre / 15 kW, Kv 1,6 → 6 devre) — https://ae.kan-therm.com/a/an-underfloor-heating-pump-group-basic-info
- **K15** CYPE — CYPEHVAC Radiant floor circuit (otomatik serpentine/spiral/coil, occupied/peripheral/service alan aralıkları, split circuit, edge clearance) — https://info.cype.com/en/subject/cypehvac-radiant-floor-circuit/
- **K16** BuildHub — Two circuit room layout (iki devrede her ikisi dış duvara akar; NHBC "serpentine" = 2s gidiş, aradan dönüş) — https://forum.buildhub.org.uk/topic/22388-two-circuit-room-layout/
- **K17** tesisat.org — Yerden ısıtma online hesap (girdi/çıktı sütunları, 29 °C kontrolü, TS EN 1264-2:2021) — https://www.tesisat.org/online/yerdenisitma.html ; https://www.tesisat.org/yerden-isitma-hesabi.html
- **K18** MTY CAD — Yerden ısıtma çizimi hesabı ve metrajı (video) — https://www.mtycad.com/2023/09/blog-post_4.html ; https://www.mtycad.com/2021/07/yerden-istma-cizimi.html
- **K19** Ambiente UFH — Design guide (200 mm tipik, kollektör ≥ 250 mm, merkezî; klozet/mutfak dolabı/duş teknesi altı yok) — https://ambienteufh.co.uk/ufh-design/
- **K20** Zhao ve ark., Connected Fermat Spirals (SIGGRAPH 2016) — https://www.cs.purdue.edu/homes/bbenes/papers/Zhao16ToG.pdf
