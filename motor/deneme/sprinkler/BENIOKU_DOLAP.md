# Deneme: yangın dolabı otomatik yerleşimi ve kontrolü (sprinkler modülü eki, 14.10.2026)

Kat planından (mahal dikdörtgenleri, kapılar, merdivenler, çıkışlar, betonarme kolonlar) yangın dolaplarını otomatik yerleştirir. Erişimi yürüme yolu ile ölçer, YG kolonlarını ve besleme hattını çizer, yangın kolon şemasını üretir ve dolap debisini pompaya ekler. Sprinkler planı (`ag.py`, `hidrolik.py`, `cizim.py`) olduğu gibi kullanılır; bu dosyalara dokunulmadı.

## Çalıştırma
```
python3 motor/deneme/sprinkler/dolap_calistir.py motor/deneme/sprinkler/ornek_girdi/kat_ofis_dolap.json [--png /scratch/x]
python3 motor/deneme/sprinkler/dolap_calistir.py motor/deneme/sprinkler/ornek_girdi/otopark_dolap.json
```
Çıktılar `proje/denemeler/sprinkler/<ad>_plan.dxf` (sprinkler + dolap planı, kapsama haritası, tablolar) ve `<ad>_kolon_semasi.dxf`. Program sonunda üç kontrol raporu yazdırır: sprinkler `HATA`, `DOLAP_HATA` ve şema `HATA`. Üçünün de 0 olması gerekir.

## Kurallar (`dolap_kurallar.py`, kaynak `06_YANGIN.md` §5, §10)
| Değer | Varsayılan | Kaynak |
|---|---|---|
| Hortum + lüle menzili (yürüme yolu) | 30 m + 5 m (kontrol: 3 m ile ayrıca) | §5.2 ✅, §5.3 ⚠ |
| Dolaplar arası en fazla mesafe | 30 m; sprinklerli binada 45 m | §5.2 ✅ |
| Debi / basınç | 100 l/dk, 4 bar, 9 bar üstünde basınç düşürücü | §5.2 ✅ |
| Eşzamanlı çalışan dolap | 2 (Ek-8/C ile teyit) | §5.3 ⚠, §10.3 |
| Kolon / bağlantı çapı | DN50 / DN32 | §5.2 ⚠ |

Girdi JSON'undaki `dolap{}` sözlüğü bu değerleri ezer.

## Yöntem
1. **Izgara (`dolap.Plan`)**: 20 cm hücre. Mahal içi ve kapı açıklıkları serbesttir; duvar, betonarme kolon ve merdiven kapalıdır. Dijkstra 16 komşulu çalışır (at hamlesi dahil, köşe kesmez). Böylece mesafe öklid değil, **duvar ve kapı etrafından yürüme yoludur**.
2. **Adaylar**: Dağıtım mahallinin (koridor veya otopark) duvarları boyunca 25 cm adımla aday konur. Otoparkta serbest duran kolon yüzleri de adaydır. Diğer mahallerin duvarları yedek adaydır (2. öncelik). Dolap gövdesi (72×20) kapı açıklığına (±20 cm), betonarme kolona, sprinkler borusuna, başlığa, vanaya, kolona veya kolon balonuna binmez.
3. **Seçim**: Her merdiven (kat girişi) kapısına 6 m yürüme mesafesi içinde bir dolap konur (tohum). Kapsaması en iyinin %3'ü içinde kalan adaylardan kapıya en yakını seçilir. Ardından açgözlü küme kapsama çalışır: merdiven ve çıkış yakını %10 önceliklidir. Sonra fazlalık budanır. En son dolaplar arası en fazla mesafe kontrol edilir; aşılırsa ara dolap eklenir.
4. **Besleme**: Merdiven dolabının yanına, köşe tarafına YG kolonu konur. Diğer dolaplar en yakın kolona 10 cm ızgarada dik açılı en ucuz yolla bağlanır (`dolap.Rota`). Boru duvar ve kolon yüzünden ≥ 10 cm uzakta, duvar dibinde gider; sprinkler borusu üzerinden geçmesi cezalıdır. Ağ büyüdükçe yeni hat mevcut hatta T ile bağlanır. Sprinkler borusunu kestiği yerde boru tek parça kalır ve köprü yapar (bulge yarım daire). Her zincirde DN etiketi ve beslediği dolap sayısı (`1 YD`) yazılır.
5. **Kapsama haritası**:
   - `ROTAS-YANGIN-DOLAP-KAPSAMA`: kapsanan alan taraması
   - `ROTAS-YANGIN-DOLAP-KAPSANMAYAN`: kapsanmayan alan taraması ve kalın sınır (varsa)
   - `ROTAS-YANGIN-DOLAP-ERISIM`: her dolabın erişim sınırı (kesikli)

   Taramalar çizim sırasında en alttadır. Kapsama raporu tablosu her mahal için alan / kapsanan / kapsanmayan m² değerlerini verir.
6. **Hidrolik (`dolap.hidrolik`)**: En elverişsiz dolap en üst kattaki en uzak dolaptır. Gerekli basınç şöyle hesaplanır: 4 bar + ana hat kaybı (Qs+Qd) + YG kolonu (Qd) + yatay hat + bağlantı (+%20 parça, +0,3 bar dolap vanası) + statik yük. Sprinkler hesabı en üst kata göre yapılır: statik yük ve kolon boyu otomatik eklenir, ana hat kaybı toplam debiyle yeniden hesaplanır. **Pompa Q = Qsprinkler + eşzamanlı dolap × 100 l/dk**, H = max(sprinkler, dolap). Depo hacmi V = Q·t olarak bulunur. En alt dolapta 1,15·H kapama basıncı kontrol edilir; 9 bar aşılırsa basınç düşürücü uyarısı verilir.
7. **Kolon şeması (`dolap_sema.py`)**:
   - Gerçek kotlu kat bantları
   - SP-1 kolonu ve her katta zon grubu: V-.. izlenebilir kelebek, FS-.. akış anahtarı, TD-.. test-drenaj → DR drenaj kolonu → yer süzgeci
   - YG kolonları: dipte izlenebilir kelebek + çek valf, her katta dolap bağlantısı (YD-.., DN32), tepede O.H.P.
   - Pompa dairesi: pompa grubu, basma kollektörü, AV-01 ıslak alarm vanası, itfaiye bağlantı ağzı, depo
   - Pompa grubu numaraları `motor/deneme/pompa_grubu` kesitinin cihaz listesinden okunur (`dolap_pompa_no.py`, ayrı süreçte; pompa_grubu koduna dokunulmaz). Örnek: 01 depo, 04 emiş kollektörü, 05/06/07 pompalar, 15 basma kollektörü, 30 yer süzgeci.
   - Kullanılan sembollerin lejantı ve adet tablosu `semboller.otomatik_lejant` ile otomatik çizilir.

   Pompa grubu girdisindeki Q/H, hesaplanan değerle karşılaştırılır (YETERLİ/YETERSİZ).
8. **Kontrol (`dolap_kontrol.py`, DXF yeniden okunur)**: Dolap borusu kolon veya duvar kesmez, üst üste binmez; köprü dışında kesişme olmaz. Gövde kolona veya kapıya binmez. Dolap yazıları diğer yazı, boru, başlık, duvar veya sembolle çakışmaz. Her zincirde DN etiketi vardır. **Kapsama yeniden hesaplanır**: dolap konumları DXF'teki INSERT'lerden okunur. Dolaplar arası en fazla mesafe kontrol edilir. Şema için de yazı çakışması ve katman kontrolü yapılır.

## Girdi (`ornek_girdi/*_dolap.json`)
| Alan | Açıklama |
|---|---|
| `sprinkler_girdi` | Sprinkler modülü girdisi (göreli yol) |
| `merdivenler[]` | `{ad, rect, kapi{p,w}}`. Merdiven yürüme ızgarasına kapalıdır (ayrı kompartıman). |
| `cikislar[]` | `{ad, p, w, rect?, kanat?}`, ör. araç rampası |
| `katlar[]` | `{ad, kot_m}` (tip kat planı her katta aynı) |
| `tavan_m` | Tavan yüksekliği |
| `pompa` | `{ad, kot_m, eksen_m}` |
| `pompa_grubu_girdi` | Pompa grubu girdisi (numara senkronu için) |
| `dolap{}` | Kural değerlerini ezer |

## Deneme sonuçları (yapay mimari, DENEME)
| Deneme | Dolap/kat | Kapsama | Pompa | Depo | Kontroller |
|---|---|---|---|---|---|
| Ofis 30×20 m, 5 kat (Z+4), 2 merdiven | 2 (iki merdiven yanında, koridor), YG1/YG2 | %100 (557,6 m²), en büyük ara mesafe 27,3 m | 463+200 = 663 l/dk (39,8 m³/h), 64,9 mSS (dolap belirleyici) | 39,8 m³ | 0 / 0 / 0 |
| Otopark 40×25 m, köşede merdiven + rampa | 2 (merdiven yanı + doğu duvarı, DN50 duvar dibi hat), YG1 | %100 (956 m²), en büyük ara mesafe 37,9 m | 894+200 = 1094 l/dk (65,6 m³/h), 49,0 mSS | 65,6 m³ | 0 / 0 / 0 |

Pompa grubu test girdisi (81 m³/h, 60 mSS) iki deneme için de YETERLİ çıkar. Stres testinde hortum 12 m alındı (depoya konmadı). Bu testte 6 dolap çıktı; 2'si açık ofis içinde (yedek aday), besleme kapıdan girdi ve kontroller 0 verdi.

## Sınırlar
- Mahaller eksene paralel dikdörtgendir (sprinkler modülüyle aynı sınır). Tek kat tek yangın kompartımanı kabul edilir.
- Lüle menzili yürüme mesafesine eklenir. Bu, düz görüş yerine yürüme yolunun kullanıldığı ihtiyatlı bir kabuldür. Izgara 20 cm, 16 komşulu; mesafe hatası ≤ ~%3.
- Yedek aday (oda içi dolap) kullanılırsa besleme hattı o mahalin kapısından girer. README kuralına göre ana hatlar ortak alandan gitmelidir; bu durum kullanıcıya sorulmalıdır.
- Eşzamanlı dolap sayısı (2), dolap girişinde 4 bar, +%20 parça payı ve 1,15·H kapama basıncı kabul değerleridir (⚠).
- Kat su alma ağzı (yüksek bina, > 60 m kat boyutu) ve hidrant hesaba katılmadı. Hidrant payı depo hacminde yoktur.
- Kolon şeması ölçeksizdir. Pompa dairesi kat ile aynı kottaysa şemada ayrı bant olarak altta gösterilir.
- Dolap plan sembolü Aselsan lejantındaki bloktur. Gövdenin arka yüzü duvara oturur; üstteki yükselen boru işareti blokla birlikte gelir.
