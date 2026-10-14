# Islak hacim içi boru güzergâhı — uygulanabilir algoritma (sıhhi, `motor/sihhi2/` için)

Tarih: 14.10.2026. Dayanak: README "Kalıcı kurallar (C) 14.10 SIHHİ RED", "(B) revizyon talimatı", "14.10 standart talimatı";
RED görüntüleri `kutuphane/arastirma/geri_bildirim/RED_sihhi_*.png`; eski kod `motor/p2/router.py`, `motor/deneme/uctan_uca/{r2,r3,nb,nb3,nb4,mimari,etiket4}.py`;
araştırma `05_ALGORITMALAR.md` §2.

> **REFERANSLA DOĞRULANACAK.** Tek referans kullanıcının kendi çizimi `ornekler/new_block.dxf`. Altın referans (kolon yeri, hat ofsetleri,
> etiket biçimi, hol hattının konumu, pis su branşman tarzı) başka bir ajan tarafından ölçülerek çıkarılıyor. Bu belgedeki bütün sayısal
> parametreler (§0 tablosu) ve `MOD_*` seçimleri o ölçümle güncellenecek; aşağıda "(ref?)" ile işaretli yerler ölçülmeden karara bağlanmaz.
> Önizlemelerden (`ornekler/new_block_onizleme/z_wet1.jpg`, `z_mutfak.jpg`) şimdiden görülen farklar:
> 1. Referansta pis su branşmanları armatürden kolona **doğrudan, eğik** ince çizgi (kolondan yıldız); (C) kuralı "duvar dibi + 45°" diyor → §2.9 iki mod.
> 2. Referansta antre-koridor temiz su çifti **duvar boyu**; (B) kuralı "koridor ortasından" diyor → §3.2 `MOD_HOL`.
> 3. Referans etiketleri yeşil `1" / 3.25 MB` (inç + MB, kanca çizgili); README 14.10 standart "YB/SB yöntemi MTY ile aynı" → etiket metni referanstan alınacak.

---

## 0. Parametreler (hepsi cm; referansla kalibre edilecek)

| Ad | Değer | Anlam |
|---|---|---|
| `D_DUVAR` | 12 (10–15) | Pis su toplama hattının duvar iç yüzünden ofseti |
| `D_KOLON` | 12 | Kolon merkezinin köşedeki iki duvardan ofseti (= `D_DUVAR`, hat kolona düz girer) |
| `H_45` | 2·`D_DUVAR` | 90° köşede 45°'lik pah boyu (iki 45° dirsek) |
| `L_BR_MAX` | WC 250, diğer 350 | Armatür çıkışı → kolon boru boyu üst sınırı (TEST T1) |
| `L_BALKON_MAX` | 300 | Balkon süzgeci → yağmur inişi hat boyu üst sınırı |
| `O_SICAK` | 8 (7–10) | Sıcak hattın soğuk hatta paralel ofseti |
| `D_TEMIZ_DUVAR` | 10 | Islak hacimde duvar boyu temiz su omurgasının duvardan ofseti (soğuk hat) |
| `TAP` | 8 | Armatür temiz su bağlantı noktasının duvardan uzaklığı |
| `MOD_PIS` | `duvar_dibi` / `yildiz` | §2.9 — (C) kuralı `duvar_dibi`; referans `yildiz` görünüyor (ref?) |
| `MOD_HOL` | `orta` / `duvar` | §3.2 — (B) kuralı `orta`; referans `duvar` görünüyor (ref?) |
| `MOD_ISLAK_TEMIZ` | `duvar` / `orta` | §3.3 — `duvar` her zaman kesişmesiz; `orta` yalnız tek taraflı armatür dizisinde |
| `ETIKET_H` | 10 (kullanıcı "çap 10") | Etiket yazı yüksekliği ölçeği |
| `ACI_KUMESI` | {0, 45, 90, 135} ±1° | Pis su parça doğrultuları (TEST T2) |

Veri modeli (shapely):
```python
IslakHacim = dict(ad, poly: Polygon (duvar iç yüzü), daire: int, kapi: [(p0, p1, duvar_idx)],
                  duvar: [dict(seg: LineString, n_ic: (nx, ny), tip: 'dis'|'ic'|'ortak_islak'|'saft'|'betonarme')],
                  komsu_islak: [IslakHacim])          # ortak duvarı olan ıslak hacimler
Armatur    = dict(kind: 'WC'|'LV'|'DUS'|'KUVET'|'EV'|'CM'|'BM'|'YS'|'ALA', c: merkez, bb: box, duvar_idx: int,
                  cikis: (x, y),          # pis su çıkış noktası (§2.2)
                  tap: (x, y),            # temiz su bağlantı noktası (duvardan TAP)
                  sb: float, yb_s: float, yb_h: float)   # yük birimleri, yb_h > 0 → sıcak su alır
Daire      = dict(no, poly: Polygon, giris: (x, y), giris_duvar: LineString, hol: Polygon, kombi: (x, y)|None,
                  islak: [IslakHacim], balkon: [Polygon], yb_inis: [(x, y)])
```
Armatür→mahal ataması **yalnız** `poly.contains(Point(f.c))` ile (duvar geçişine tolerans yok; bkz. §1.2).

---

## 1. RED görüntülerindeki hataların kök nedenleri (kod düzeyinde)

### 1.1 `RED_sihhi_wcbanyo_capraz_pissu_etiket_ust_uste.png` — oda içinden çapraz pis su, temiz su dolaşımı, etiket yığını
| Belirti | Kök neden (dosya:fonksiyon) |
|---|---|
| Lavabodan kolona odanın ortasından 45° uzun çapraz hat | `r3.balik_sirti`: omurga = `oktilineer(far, kp)` → en uzak armatürün **merkezinden** kolona *tek diyagonal + tek dik* parça. Duvara yapışma terimi yok; `maliyet()` (nb3 `pis_ag3`) yalnız duvar kesme (15), yasak (1000), şaft (300) sayar; oda içi serbest alan maliyeti 0 → en kısa yol odanın ortasından geçer. |
| Branşmanlar da çapraz | `balik_sirti` branşman = `[P, Q]`, Q omurgada `s = t + h` (45° izdüşüm) → her branşman armatür merkezinden omurgaya 45° uçar; omurga ortadaysa branşman da ortadan. Omurgaya değmeyen aday için `oktilineer(P, kp)` ile **doğrudan kolona** ikinci çapraz. |
| Bağlantı noktası yanlış | `f['c']` = armatür **merkezi** (mimari.py `fixtures`), gider/sifon çıkışı değil → hat armatürün ortasından başlar, armatür gövdesini keser. |
| Kolon odanın "yanlış" köşesinde, hatlar odayı boydan boya geçer | `r2.kolon_yeri2`: aday = her armatürden en yakın gerçek duvar + duvar boyunca ≤260 cm köşe; puan SB ağırlıklı **kuş uçuşu** mesafe (`_d`) − köşe 40 − şaft 110 − komşu ıslak 35. Boru boyu duvar dibi yürüyüşüyle değil kuş uçuşuyla ölçülünce odanın karşı köşesi de "yakın" çıkar; şaft bonusu (110) kolonu armatürlerden uzağa çeker. |
| Soğuk/sıcak çift ıslak hacmin içini dolaşıyor, pis suyu kesiyor | `r3.Alan.__init__`: `base = 1 + 2.2·exp(−dist/18)` → **duvardan uzak hücre ucuz** (koridor ortası tercihi ıslak hacme de uygulanmış). `nb3.sicak_yol`: sıcak su **tek hat**, armatürleri `sira()` en-yakın-komşu sırasıyla **dolaşır**; soğuk `r3.otele(cen, ±ara/2)` ile bu dolaşımın her yerine paralel → 2 m² odada çift hat ilmek yapar. R4 `AlanR4` pis su bandı cezası (30) yalnız üst üste binmeyi azaltır, dolaşımı değiştirmez. |
| Etiketler üst üste, mahal adının ve boruların üstünde | `nb3.pis_ag3`: omurga her branşman noktasında bölünür (`s_list`) ve **her parçaya + her branşmana** `_etiket_pis` → 5 armatürlü odada 9–10 etiket; `nb._etiketler`: soğuk ağacın **her kenarına** `_cap_on` (sıcak varsa 4 satır). Yerleştirmede çakışma kontrolü yok (`cap_pis`/`cap_temiz` doğrudan ekler). `etiket4.py` sonradan taşır ama (a) yalnız kendi boru ekseni boyunca ya da boruya dik 12–60 cm, (b) engel listesinde **boru çizgileri yok** (yazı + sembol) → etiket boruya biner, (c) mahal dışına çıkma yok. |

### 1.2 `RED_sihhi_balkon_suzgeci_banyo_kolonuna_bagli.png` — balkon süzgeci banyo kolonuna (P9) bağlı
- `mimari.fixtures` → `room_at(p)`: bir noktayı ıslak hacme atarken `W.cross(p, r.xy) <= 2` kabul eder (**2 duvar geçişine kadar**) ve dikdörtgen dışı olmak yalnız sıralama cezası (`0 if inr else 1`). Balkondaki 60/60 ızgara (yağmur inişi yanı) "duş" etiketine 380 cm içinde ve 1–2 duvar ötede → `kind='YS', room=duş` olarak kaydedildi.
- `nb3.suzgec_duzenle`: "ıslak hacim başına tam 1 süzgeç" → duşun gerçek süzgeci yerine kolona en yakın olan (balkondaki!) tutuldu, diğeri silindi.
- `r2.balkon_suzgecleri` doğru süzgeci (yeşil hat, yağmur inişine) **ayrıca** üretir; sonuçta balkonda biri yağmura, biri P9'a giden iki süzgeç.
- Düzeltme: mahal ataması yalnız poligon içi (§0); balkon poligonundaki ızgara = balkon süzgeci, ıslak hacim listesine giremez (§2.8).

### 1.3 `RED_sihhi_sicak_su_daire_disindan.png` — sıcak su merdiven holünden
- `nb3.daire_temiz`: `mask = (AL.lab == dno) | disk(ent, 90) | …`; `AL.lab` daire etiketi **kapılardan geodezik yayılım** (`MCP_Geometric`) → merdiven holü de en yakın daireye etiketlenir (daire kapısı açık).
- `r3.Alan.grid(mask_ok, yumusak=6.0)`: maske dışı hücre **yasak değil, +6 pahalı** ("sızıntılı etiket"). Duvar delme cezası hücre başına 20 (`dist < 3`) → daire içinde bir duvar geçmek (≈ 3 hücre × 20 = 60) merdiven holünden 10 hücre dolaşmaktan (60) pahalı → A* sıcak hattı kapıdan çıkarıp ortak alandan götürür.
- `nb3.sicak_yol`: sıcak tek hat sırayla armatür dolaşır (wc-duş → banyo); iki ıslak hacim arasında daire içi yol pahalıysa dışarıdan dolaşır; soğuk da ona paralel ötelenir (`otele`) → ana hatla birlikte 4 hat merdivende.
- Düzeltme: §3.1 sıcak ağ **daire poligonu dışında hiçbir hücreye giremez** (yasak, ceza değil); sıcak ağ = soğuk ağacın alt ağacı (§3.4), dolaşım yok. TEST T5.

### 1.4 `RED_sihhi_kolon_semasi_sayac_kapida_yanlis_tarz.png` — şema (kapsam dışı, kayıt için)
- `sema4.sihhi_sema4`: her katta ADK inişi + "Dn SAYAÇ (KAPIDA)" kat bandında; `nb3.temiz_kat3` planda sayacı daire kapısına koyar (`MTY-SU SAYACI`, `ent − 14·u`). Kullanıcı şeması: sayaç grubu **zemin bandında solda**; kolon etiketleri en üstte; armatür sembolleri kullanıcının KOLON blok görünümünde. Armatür sembolleri `semboller2` (kullanıcının blokları değil). → Şema `new_block` şemasından birebir; bu belge kapsamı dışında (README (C) KOLON ŞEMASI).

---

## 2. Pis su: armatür → duvar dibi toplama hattı → kolon

### 2.1 Genel kurgu
```
kolon (ıslak hacim köşesi, D_KOLON×D_KOLON içeride)
  ├── KOL_A: köşeden duvar A boyunca (duvardan D_DUVAR) en uzak armatüre kadar   ─┐ "toplama hattı" (iki kol en fazla)
  └── KOL_B: köşeden duvar B boyunca … ; köşe dönüşleri 45° pahlı                ─┘
        her armatür: çıkış noktası → kola kısa (≤ 40 cm) branşman, kola 45° akış yönünde giriş (dallı = her armatürün kendi T'si)
        süzgeç: kola en yakın serbest nokta, ≤ 60 cm branşman
```
Hat ıslak hacim **poligonunun içinde**, duvar dibinde (`poly.buffer(-D_DUVAR, join_style='mitre')` halkası üzerinde). Oda ortasından geçen parça **yoktur**.

### 2.2 Armatür çıkış noktası (`cikis`)
Armatür arkasındaki duvar `duvar_idx` (gövde kutusu `bb`'nin en yakın duvar kenarı; WC/LV/EV/ÇM için eksen duvara dik). `n` = o duvarın içe normali.
| kind | `cikis` |
|---|---|
| WC (alafranga) | duvar iç yüzü + 20·n, armatür ekseni üzerinde (sifon çıkışı) |
| ALA (alaturka) | gider dairesi merkezi |
| LV | duvar iç yüzü + 10·n, armatür ekseni (sifon) |
| DUŞ / KÜVET | tekne giderinin konumu (mimaride gider dairesi varsa o, yoksa teknenin **kola en yakın** köşesinden 15 cm içeri) |
| EV | tezgâh altı, duvar iç yüzü + 12·n, eviye ekseni |
| ÇM / BM | duvar iç yüzü + 10·n, makine ekseni |
| YS | süzgeç merkezi (§2.7) |

### 2.3 Kolon seçimi (ıslak hacim köşesi; şaft / ortak duvar öncelikli; toplam branşman boyu minimum)
```python
def kolon_adaylari(w):                         # w: IslakHacim
    ring = w.poly.buffer(-D_KOLON, join_style='mitre').exterior
    adaylar = []
    for i, (p_prev, p, p_next) in enumerate(kose_uclusu(ring)):
        if ic_aci(p_prev, p, p_next) > 180: continue            # yalnız dışbükey köşe (girinti köşesi kolon için uygun değil)
        a, b = duvar_bul(w, p_prev, p), duvar_bul(w, p, p_next)   # köşeyi oluşturan iki duvar
        if 'betonarme' in (a.tip, b.tip) or Point(p).buffer(15).intersects(YASAK): continue
        if kapi_araliginda(p, w.kapi, 40): continue              # kapı kanadı önü
        adaylar.append(dict(p=p, duvarlar=(a, b)))
    return adaylar

def kolon_puani(w, cand):
    # (1) toplam boru boyu — DUVAR DİBİ yürüyüşü (kuş uçuşu değil): halka üzerinde köşeden armatür izdüşümüne
    ring = w.poly.buffer(-D_DUVAR, join_style='mitre').exterior
    s0 = ring.project(Point(cand.p))
    L = 0.0
    for f in w.armaturler:
        sf = ring.project(Point(f.cikis))
        d_ring = min(abs(sf - s0), ring.length - abs(sf - s0))   # iki yönden kısası (kol seçimi)
        stub = ring.distance(Point(f.cikis))                     # çıkış → kol dik mesafe
        L += (sb_agirlik(f) * (d_ring + stub))                    # WC ağırlığı yüksek: klozet kolona yakın olsun
    # (2) bonuslar: tesisat şaftı / ortak ıslak duvar / komşu ıslak hacmin aynı köşesi (ortak kolon)
    bonus = 0
    if any(d.tip == 'saft' for d in cand.duvarlar): bonus += 150          # şaft (tesisat şaftı; mek. havl. şaftı DEĞİL)
    if any(d.tip == 'ortak_islak' for d in cand.duvarlar): bonus += 80    # komşu ıslak hacimle ortak duvar
    if ortak_kolon_mumkun(w, cand): bonus += 120                           # §2.6
    if any(d.tip == 'dis' and pencere_var(d) for d in cand.duvarlar): bonus -= 60   # cephe/pencere köşesi istenmez
    return L - bonus

kolon = min(kolon_adaylari(w), key=lambda c: kolon_puani(w, c))
```
Kısıt: WC için `d_ring + stub ≤ L_BR_MAX['WC']`; sağlanamıyorsa aday elenir. Mutfak kolonu ayrı (mutfak ve WC giderleri birleşmez — kalıcı kural). Kolon mek. havalandırma şaftının **içinde olamaz** (B); betonarme kolona ≥ 15 cm.

### 2.4 Toplama hattı (kollar) ve 45° pahlı köşe
```python
def toplama_kollari(w, kolon):
    ring = w.poly.buffer(-D_DUVAR, join_style='mitre').exterior       # kapalı halka, duvardan D_DUVAR
    s0 = ring.project(Point(kolon.p))
    yon = {+1: [], -1: []}                                              # halka üzerinde iki yön
    for f in w.armaturler:
        sf = ring.project(Point(f.cikis))
        d_plus  = (sf - s0) % ring.length
        d_minus = (s0 - sf) % ring.length
        f.kol, f.s = (+1, d_plus) if d_plus <= d_minus else (-1, d_minus)
        yon[f.kol].append(f)
    kollar = {}
    for k, fs in yon.items():
        if not fs: continue
        s_end = max(f.s for f in fs) + 5                                 # en uzak armatürün 5 cm ötesi (T.K. / kör tapa yok: hat orada biter)
        kol = substring_yon(ring, s0, s_end, k)                          # kolon → en uzak armatür (akış yönünün tersi)
        kollar[k] = pah_45(kol, H_45)                                    # her 90° köşede H_45 boyunda 45° pah
    return kollar

def pah_45(pts, h):
    """90° köşe → iki 45° dirsek: köşe noktası yerine köşeden h/2 geri ve h/2 ileri iki nokta"""
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        u1, u2 = birim(a, b), birim(b, c)
        if abs(u1[0]*u2[0] + u1[1]*u2[1]) < 0.01:                        # dik dönüş
            out += [(b[0]-u1[0]*h/2, b[1]-u1[1]*h/2), (b[0]+u2[0]*h/2, b[1]+u2[1]*h/2)]
        else:
            out.append(b)
    return out + [pts[-1]]
```
Kolon, halkanın köşesinde olduğu için kollar kolona **düz** girer (kol ekseni kolon merkezinden geçer). Kullanıcı kuralı "kolona 45° giriş" branşmanın kola/kolona 45°'lik Y ile bağlanmasıdır (§2.5). Kolonun köşeden kaydırılması gerekirse (betonarme), kol son parçası kolona 45° kırıkla bağlanır (`oktilineer(kol_ucu, kolon.p, 'diag')`).

### 2.5 Armatür branşmanı: kola 45° giriş, dallı topoloji
Her armatürün **kendi** branşmanı vardır (seri zincir yok). Kol üzerindeki yerel koordinat: `s` = kol boyunca parametre (kolona doğru azalır), `h` = kola dik uzaklık (oda içine pozitif).
```python
def bransman(f, kol):
    P  = f.cikis
    s_P = kol.project(Point(P)); h = kol.distance(Point(P))
    if h <= 3.0:                                   # çıkış zaten kol üzerinde (WC, LV, EV, ÇM): kolda düğüm, branşman yok
        return [kol.interpolate(s_P)]              # çizimde: kolda düğüm (T), SB burada eklenir
    # 45° akış yönünde giriş: birleşim noktası Q, s_Q = s_P − h (kolona doğru)
    Q = kol.interpolate(s_P - h) if s_P - h >= 0 else kol.interpolate(0)
    br = [P, Q]                                                   # tek 45° parça
    if h > 40 or gövde_keser(br, w.armaturler - {f}):             # uzun/komşu gövdeyi kesiyor: dik + 45° (son 8 cm 45°)
        br = [P, (P + n_kol * (h - 8)), Q]                        # P'den kola dik in, son 8 cm 45° ile Q'ya
    return br
```
**Kesişmezlik garantisi (branşmanlar arası).** Bütün branşmanlar yerel koordinatta aynı yönlü vektöre sahiptir: 45° parçaları `(−1, −1)/√2`, dik parçaları `(0, −1)`. Aynı yönlü (paralel) doğru parçaları ancak **eşdoğrusal** olduklarında kesişebilir; eşdoğrusal iki 45° parça = `s_P − h` değerleri eşit → ikisi aynı Q'ya iner; bu durumda uzaktaki armatürün branşmanı yakındakinin branşmanına T ile bağlanır (`agacta_kes`), kesişme değil birleşim. Dik parçalar farklı `s`'lerde paralel → kesişmez. Dik parça ile 45° parça: dik parça `s=s_P` doğrusu üzerinde, 45° parça `s ∈ [s_P' − h', s_P']`; kesişme için `s_P ∈ (s_P' − h', s_P')` ve dik parçanın yüksekliği `h_P > s_P' − s_P` gerekir → bu, P'nin gövdesinin P' branşmanının altında kalması demektir ve `gövde_keser` testinde yakalanır: o zaman P' de dik+45° yapılır (iki dik parça paralel; iki kısa 45° parça `h=8` ile `s` aralıkları ayrık). İspat tamamlanır.
**Kesişmezlik (branşman – kol).** Branşman kolun oda tarafında (`h>0`), kola yalnız Q'da değer. **Kol – kol:** iki kol aynı halkanın ayrık alt yayları (ortak noktaları yalnız kolon). **Kol – duvar:** halka poligonun içinde (`D_DUVAR < min_genişlik/2` şartıyla halka basit). Dolayısıyla pis su ağı düzlemsel ağaç → TEST T3 `pis–pis = 0`.

SB toplama ve çap: kol, düğümlerinde (Q'lar) bölünür; her parçanın SB'si = akış yukarısındaki armatürlerin toplamı; çap `dn_sb(SB, wc_var)` (mevcut tablo). Etiket §4.

### 2.6 İki ıslak hacim arası ortak duvar kolonu
`ortak_kolon_mumkun(w, cand)`: `cand.duvarlar` içinde `tip == 'ortak_islak'` olan duvar `d`, komşu `w2`'nin **aynı köşesine** (w2'nin halkasında `d`'ye bitişik köşe, kolondan ≤ 40 cm) denk geliyorsa ve `w2` mutfak değilse (mutfak+WC birleşmez) ve `SB(w)+SB(w2) ≤ kolon_kapasite(Ø100)`:
- Tek kolon duvarın içinde/köşesinde; `w`'nin kolları kendi halkasından, `w2`'nin kolları kendi halkasından gelir; `w2` kolu kolona ortak duvarı **tek noktada** (kolon merkezi hizası) dik geçerek girer (geçiş parçası ≤ duvar kalınlığı + 2·D).
- Her iki hacme de aynı `P-n` numarası; kolon etiketi mahal dışında kolonun yanında (README).
- İki hacim için puan: `kolon_puani(w) + kolon_puani(w2) − 120`. Ortak kolon aday puanı tekil adaylardan iyi değilse ayrı kolon.

### 2.7 Yer süzgeci konumu (her ıslak hacimde tam 1)
Mimaride süzgeç varsa **o konum** (poligon içi). Yoksa EK süzgeç:
```
aday = halkanın (D_DUVAR+25) içe ötelenmiş çizgisi üzerindeki noktalar, 10 cm adım
elenir: armatür gövdesi bb.buffer(20) içinde, kapı önü 60 cm, ÇM altı
puan = branşman boyu (bransman(f_ys) uzunluğu)  + 0.5·(duş teknesine uzaklık)   # duşa yakın tercih
seç = min puan;  branşman §2.5 (h ≤ 60)
```
Kullanıcı reddi: süzgeç başka mahalde (balkon) bulunup odaya "atanmaz" (§1.2).

### 2.8 Balkon süzgeci → yalnız yağmur inişine
```python
for balkon in daire.balkon:                                      # balkon poligonu (mimari 'balkon' etiketi + duvar ışınları)
    izgaralar = [g for g in izgara_sembolleri if balkon.contains(Point(g))]    # yoksa balkonun inişe en yakın köşesi, 20 cm içeride
    yb = [p for p in daire.yb_inis if balkon.buffer(60).contains(Point(p))]   # bu balkondaki / balkona bitişik iniş
    if not yb: yb = [yeni_yagmur_inisi(balkon)]                  # cephe köşesine yaslı yeni YB (kural: inişler balkon köşesinde)
    hedef = min(yb, key=dist)
    hat = L_yolu(suzgec, hedef, balkon)                          # balkon içinde 1 kırıklı ortogonal, duvar dibinden
    assert hat.length <= L_BALKON_MAX and balkon.buffer(5).contains(hat)
    # bu hat pis su ağına, ıslak hacim poligonlarına, pis su kolonlarına değmez (TEST T4)
```

### 2.9 `MOD_PIS = 'yildiz'` (referans tarzı, ref?)
Referans önizlemesinde (`z_wet1.jpg`) her armatürden kolona **doğrudan eğik** ince çizgi var (P8'de yıldız). Kesişmezlik garantisi: aynı uç noktayı (kolon) paylaşan doğru parçaları yalnız o uçta kesişir (eşdoğrusal değilse). Eşdoğrusal çakışma (iki armatür aynı doğrultuda) → yakındaki uzaktakinin hattına T ile bağlanır. Gövde kesme (bir çizgi başka armatür gövdesinden geçiyorsa) → o armatür için `duvar_dibi` branşmanı. Mod `yildiz` seçilirse §2.5 yerine bu; §2.3 kolon seçimi aynı (toplam `|cikis − kolon|`). T2 açı testi bu modda **uygulanmaz** (referans eğik). Altın referans ölçümü hangisini onaylarsa `MOD_PIS` o olur; (C) metni `duvar_dibi + 45°` diyor.

---

## 3. Temiz su (soğuk + sıcak çift)

### 3.1 Değişmezler
1. Soğuk ağ `T_c`: daire girişinden (kapı **yanı** duvar; kapı kanadı değil) köklenen, daire poligonu içinde düzlemsel ağaç.
2. Sıcak ağ `T_h`: kökü kombi; **`T_h ⊆ T_c` topolojik alt ağaç** — kombiden her sıcak armatüre giden yol soğuk ağacın yolu, `O_SICAK` sabit ofsetle paralel. Sıcak hattın bağımsız dolaşımı (R3 `sicak_yol`) yok.
3. Daire poligonu dışı sıcak için **yasak** (ceza değil): A* ızgarasında `block |= ~raster(daire.poly)`; soğuk için de yasak (ana hat ortak alandan kapı yanına kadar ayrı sistemdir).
4. Hiçbir sıcak–soğuk kesişmesi yok (§3.5 teoremi + TEST T3); köprü/atlatma çizilmez.

### 3.2 Daire girişi → hol → ıslak hacim
```python
giris = kapi_yani(daire.giris_duvar, daire.kapi, tarafı=ıslak hacimlere yakın taraf, 25 cm)   # kapı kasasından 25 cm, duvar içinden
hol_eksen = {'orta': medial_eksen(daire.hol), 'duvar': duvar_dibi_eksen(daire.hol, 10)}[MOD_HOL]
# medial_eksen: hol poligonu raster (2 cm) → distance_transform_edt → skeletonize → kısa dal budama (< 40 cm)
#               → ortogonal doğrultuya oturtma (parça yönleri 0/90; L kırıkları köşede) → LineString/MultiLineString
# duvar_dibi_eksen: hol.poly.buffer(-10).exterior'ün ıslak hacim kapılarının bulunduğu kenarları
omurga = agac_bagla(giris, hol_eksen)                          # giriş noktasından eksene dik kısa bağlantı
for w in daire.islak + ([mutfak] if mutfak else []):
    giris_w = islak_giris_noktasi(w, hol_eksen)                 # w'nin hol'e bakan duvarında, w içi omurganın başlangıcına en yakın,
                                                                # kapı aralığı dışında (kapı kanadı 40 cm), betonarme dışı
    omurga += dik_baglanti(hol_eksen, giris_w)                  # eksene dik tek parça (duvarı dik geçer)
```
Yatak odasından geçmesi zorunlu ebeveyn banyosu: oda içinde duvar dibi (`D_TEMIZ_DUVAR`), kapıdan girer (B kuralı).

### 3.3 Islak hacim içi omurga: `MOD_ISLAK_TEMIZ`
**`duvar` (varsayılan, her zaman kesişmesiz):** omurga = `w.poly.buffer(-D_TEMIZ_DUVAR).exterior` halkası üzerinde, `giris_w`'den başlayıp **sıcak+soğuk alan armatürlerin (LV, DUŞ, KÜVET, EV) `tap` noktalarından geçen** tek yol (halka yönü: iki yönden toplam boy kısa olan). Yol boyunca:
- sıcak+soğuk armatür: `tap` omurga üzerinde → plan görünüşünde branşman yok, iki hatta da armatür hizasında küresel vana sembolü (referans tarzı), bağlantı düşey (duvar içinde) — "geçiş musluğu".
- yalnız soğuk alan armatür (WC, ÇM, BM, rezervuar, ALA): omurgadan **oda tarafına** dik kısa branşman (`tap` duvardan `TAP` cm → branşman boyu ≈ `D_TEMIZ_DUVAR − TAP`, 2–10 cm; ÇM/BM makine ekseninde).
- yol, son sıcak armatürden sonra yalnız soğuk olarak devam eder (kalan soğuk armatürlere).

**`orta`:** omurga = odanın uzun ekseni (medial) üzerinde `giris_w` → sıcak+soğuk armatür `tap`larına L'lerle uğrayan yol; **yalnız** bütün soğuk-alan armatürler omurganın sıcak hattın olmadığı tarafındaysa geçerli (§3.5 koşulu); değilse otomatik `duvar`. (B) "ıslak hacim içinde borular mahal ortasından" bu modla; referans ölçümü karar verir (ref?).

### 3.4 Sıcak hat: kombiden başlangıç, soğuğa paralel alt ağaç
```python
T_c = soguk_agac(daire)                       # §3.2 + §3.3 (networkx Graph; kenar = ortogonal/45° LineString)
K   = en_yakin_dugum(T_c, kombi.cikis)        # kombi: soğuk ağacın YAPRAĞI (soğuk besleme kombiye gider)
hot_taps = [f.tap for f in armaturler if f.yb_h > 0]
E_h = ∪ kenarlar( shortest_path(T_c, K, t) for t in hot_taps )     # sıcak alt ağaç (r2.sicak_yollar fikri)
# taraf ataması (§3.5): her "paylaşılan maksimal yol" (E_h'nin düğüm derecesi 2 olan zinciri) için taraf s ∈ {+1, −1}
H = { yol: offset_curve(LineString(yol), s·O_SICAK, join_style='mitre', mitre_limit=2.0) for yol in zincirler(E_h) }
```
Kombi bağlantısı: kombi mutfakta dış cephede; `kombi.cikis` = kombi alt orta noktasından 10 cm aşağı (soğuk giriş + sıcak çıkış yan yana, `O_SICAK` aralıkla — kombinin altında iki hat başlar). Kombi varsa termosifon/sıcak sembolü yok (kalıcı kural).

### 3.5 Sıcak–soğuk kesişmezlik: taraf kuralı, "yakın hat önce ayrılır" ve ispat
Tanımlar: `T_c` düzlemsel ağaç. Paylaşılan yol `Π` = `T_c`'de sıcak hattın soğuğa paralel gittiği maksimal zincir; `Π` boyunca sıcak hattın tarafı `s` sabittir (taraf değişimi = kesişme). `Π` üzerindeki bir `v` düğümünde soğuk kolları: devam eden kollar (Π içinde) ve **ayrılan** kollar (yalnız soğuk, ya da sıcağın da döndüğü kol).

**Kural A (soğuk-alan branşmanı):** `Π` üzerindeki yalnız-soğuk branşman sıcağın **olmadığı** tarafa (`−s`) ayrılır.
**Kural B (sıcak dönüşü):** sıcak, `Π`'nin sonunda soğukla birlikte döner (L; ofset köşesi) ya da biter (düşey çıkış/vana). Soğuğun `Π` sonunda **düz devam eden** üçüncü kolu varsa, sıcağın döndüğü kol sıcağın tarafında (`+s`) olmalıdır.
**Kural C (sıralama — "armatür/dönüş tarafına yakın olan hat önce ayrılır"):** bir demette (`Π` üzerinde soğuk + aynı `+s` tarafında birden fazla sıcak hat, §3.6) `+s` tarafına ayrılacak hatlardan **`Π` boyunca en önce ayrılan en dışta** (`+s` tarafına en yakın), en son ayrılan soğuğa en yakın (iç) yürür: sıra `soğuk | h_en_son | … | h_en_önce`. Aynı kural bir çiftin L dönüşünde: dönüş `+s` tarafına ise sıcak (dönüşün **iç** tarafı, armatüre yakın) `O_SICAK` **önce** döner, soğuk köşede döner (mitre iç köşe); dönüş `−s` tarafına ise soğuk önce döner, sıcak `O_SICAK` ileride (dış köşe). İki hat **aynı kola** dönüyorsa iç içe L (C'nin özel hali).
Yerel koordinatla doğrulama: soğuk `y=0`, iç sıcak `y=o`, dış sıcak `y=2o`, `s=+y`. `x_1`'de `+y` yönüne ayrılan hat dış (`y=2o`) ise düşey parçası `x=x_1, y≥2o` → `y=o`'da düz devam eden iç hattı kesmez. İç hat `x_1`'de dönse düşey parçası `y=o..∞` dış hattın `y=2o` düz parçasını keser → yasak. Dolayısıyla "önce ayrılan = dışta".
**Kural D (yasak):** `Π`'nin **ortasındaki** bir düğümde hem soğuk hem sıcağın üçüncü kola ayrılması (çiftli T) yoktur (§1 kök neden: düzlemde çiftli T her zaman bir kesişme üretir — r3 başlığındaki gözlem doğru, çözümü (tek hat dolaşım) yanlıştı).

**Önerme.** A–D sağlanıyorsa `H ∩ T_c = ∅` ve `H` kendi kendini kesmez.
*İspat.* Kesişme adayı parça çiftleri üçe ayrılır. (i) Paralel çiftler: `Π` boyunca sıcak parça soğuk parçanın `s` tarafında tam `O_SICAK` (demette `k·O_SICAK`) uzaklıkta (ofset) → kesişmez; mitre köşede ofset eğrisi `k·O_SICAK < min(parça boyu)/2` ve dönüş açısı ≤ 90° iken basittir (mitre_limit 2 ile dış köşe sonlu). (ii) Soğuk-alan branşmanı: açık yarı düzlem `−s` içinde, `Π` parçasına yalnız ayağında değer; sıcak `+s` yarı düzlemindedir → ayrık (Kural A). (iii) Ayrılma/dönüş düğümü `v`: `v`'de `+s` tarafına ayrılan hat demetin en dışındaki hattır (C); düşey parçası `y ≥ (kendi ofseti)` bölgesinde kalır, bu bölgede daha içteki hatların düz parçası yok; soğuğun `v`'deki öteki kolları ya `Π` içinde (paralel durumu) ya `−s` tarafında (A) ya da ayrılan hattın gittiği kolun kendisidir (B, o kolda yine paralel/ofset) → kesişme yok. Ayrılan hat demetten çıkınca kalan hatlar `v`'den sonra bir kademe dışa kaydırılmaz (sıra korunur; boşluk kalır) — kaydırma gerekirse `v`'den sonra 45°/mitre ile ve yalnız `+s` yönünde, kalan hatların hepsi birlikte (paralel öteleme, kesişmesiz). Farklı taraflara dönecek hatlar farklı taraflarda yürür (§3.6 `s(h)` = h'nin dönüş tarafı); Kural D ile çiftli T yoktur. Böylece (i)–(iii) tüm çiftler ayrıktır: `H ∩ T_c = ∅`. `H` kendi kendini kesmez: her sıcak hat soğuk ağacın bir yolunun ofseti (basit) ve iki sıcak hat ya ayrık `Π`'lerde ya aynı demette sabit sıralıdır. ∎

**Uygulanabilirlik ve yedek:** bir `Π` üzerinde hem `+s` hem `−s` tarafına yalnız-soğuk branşman gerekiyorsa (A ihlali) → (1) `−s` tarafına düşenleri `Π` bittikten sonraki yalnız-soğuk kuyruktan besle (yol sırasını değiştir), (2) olmuyorsa branşmanı `Π`'nin ucundan (L sonrası) al, (3) olmuyorsa kombiden ikinci sıcak hat (§3.6). `MOD_ISLAK_TEMIZ='duvar'`da A her zaman sağlanır (bütün armatürler duvar tarafının karşısında, sıcak duvar tarafında `s = −n_ic`).

### 3.6 Kombiden birden fazla sıcak hat (gerektiğinde)
Sıcak armatürler holün iki yanındaysa (banyo solda, wc-lavabo sağda) tek sıcak hat için `T_h` holde dallanır → Kural D ihlali. Seçenekler, maliyete göre:
1. **Zincir:** iki ıslak hacim ortak duvarlıysa sıcak+soğuk çift birinci hacmin duvar boyu omurgasından ortak duvarı tek noktada geçip ikinciye devam eder (tek yol, dallanma yok).
2. **İki sıcak hat:** kombiden `h1`, `h2`; holde demet `h_sol | soğuk | h_sağ` (her sıcak hat **kendi dönüş tarafında**, Kural C). Üç boru holde; her birinin ofseti `±O_SICAK`. Soğuğun hol T'leri: sola ayrılan soğuk kolla birlikte `h_sol` döner (B), sağa ayrılanla `h_sağ`.
Maliyet = toplam sıcak boru boyu; eşitlikte 1.

### 3.7 Ana hat (ortak alan → daire girişi) ile kesişmezlik
Ana hat daire poligonuna kapı yanı duvardan tek noktada girer; daire içindeki `T_c` bu noktadan başlar → kesişme yok. Ana hat koridorda `MOD_HOL`'a göre ortadan; başka dairelerin ana hatları paralel demet (`O_SICAK` aralık, sıralama: kapısına önce varan hat **dışta** değil **kapı tarafında** → iç içe L, Kural C'nin aynısı).

---

## 4. Etiket yerleşimi
- **Birim:** her "parça" (ağacın iki düğüm arası kenarı) için **tek etiket**; soğuk+sıcak çiftinde **tek birleşik etiket** (iki satır: soğuk `Ø25 / 7.5 YB`, altında sıcak `Ø20 / 3.0 YB`; metin biçimi referanstan — ref?). Pis su: `Ø50 / 2 SB` tek satır, boru doğrultusunda döndürülmüş (okunur yön: açı (−90°, 90°]).
- **Kısa parça kuralı:** boyu `< 1.6·etiket_genişliği` parçalar etiketlenmez; değer bir sonraki parçanın etiketine taşınır (ağaçta aynı yük). Kol üzerindeki düğüm aralıkları çok kısaysa (WC–LV yan yana) iki parça tek etiket: "Ø100 / 12 SB".
- **Aday konumlar:** parça parametresi `t ∈ {0.5, 0.35, 0.65, 0.2, 0.8}` × taraf `{−n, +n}` (sıcak çiftte yalnız sıcağın olmadığı taraf) × dik uzaklık `{6, 12, 18}` cm. Etiket kutusu = döndürülmüş dikdörtgen (shapely `affinity.rotate(box(...), ang)`).
- **Engel kümesi** (STRtree): mimari yazılar (mahal adı, m², kapı/pencere ölçüleri, kolon adları), **tüm boru çizgileri** (buffer 1), semboller (vana, süzgeç, kolon, armatür gövdeleri), yerleşmiş etiketler, kılavuz çizgiler. İlk sıfır-temaslı aday seçilir.
- **Kalabalık (hiç aday sığmıyor, ya da mahal alanı < 3 m² ve etiket sayısı > 3):** etiket **mahal dışına**: mahal poligonunun dışında, parçanın doğrultusunda 16 yön × {40, 70, 100, 140} cm halka araması; ilk sıfır-temaslı konum; parça orta noktasından etikete **kılavuz** (katman `ROTAS-SEMBOL-KILAVUZ`, ince). Kılavuzlar birbirini ve etiketleri kesmez (kılavuz da engel kümesine eklenir).
- **Sıra:** önce pis su (uzun parçalar önce), sonra temiz çift, sonra serbest yazılar (aspiratör, kombi). Kolon balonu `P-n` mahal dışında, kolon sembolünün yanında (mevcut `kolon_etiketleri` araması, engel kümesi aynı).
- Yazı altına maske konmaz (boru etiketin altından geçmez — çakışma 0 hedefi); referans tarzında etiketler borunun **yanında**.

---

## 5. Otomatik testler (kontrolör; girdi DXF → ezdxf → shapely)
Okuma: `doc = ezdxf.readfile(dxf)`; katmanlar `ROTAS-PIS-SU*`, `ROTAS-TEMIZ-SU-SOGUK*`, `ROTAS-TEMIZ-SU-SICAK*`, `ROTAS-BALKON-SUZGEC*`, `ROTAS-*-CAP-*` (etiket), `ROTAS-MIMARI*` yazılar. LWPOLYLINE/LINE → `LineString`; TEXT/MTEXT → döndürülmüş kutu (`ezdxf.tools.text_size` / `tcheck` kutusu); INSERT → blok sınır kutusu.
Hazır yardımcılar: `r3.kesisimler(items)` (T birleşimi serbest, diğer temas kesişme), `denetim/denetle.boru_kesismeleri`, `denetle.yazi_cakismalari`.

| Test | Ölçüm | Geçme |
|---|---|---|
| T1 branşman boyu | Pis su grafı (networkx, kenar=parça): her armatür düğümünden kendi kolonuna yol boyu | WC ≤ 250, diğer ≤ 350; ıslak hacim başına ortalama ≤ 200 |
| T2 açı kümesi | Her pis su parçası `atan2 mod 180` | ∈ {0, 45, 90, 135} ± 1° (`MOD_PIS='yildiz'` ise test atlanır, bunun yerine: her parça kolonda biter veya başka parçaya T ile bağlanır) |
| T3 kesişme | `kesisimler` ile: pis–pis, soğuk–soğuk, soğuk–sıcak, sıcak–sıcak, balkon–pis, ana hat–daire içi | hepsi 0 (pis–temiz farklı düzlem: bilgi, sınır yok — referansta kesişiyor) |
| T3b köprü/atlatma | ARC/boşluk köprü sembolü sayısı | 0 |
| T4 balkon süzgeci | Balkon poligonu içindeki her süzgeç: hattının öbür ucu bir YB noktasına ≤ 5 cm; `hat.length ≤ 300`; `hat ∩ (pis su ağı ∪ ıslak hacim poligonları)` | ✓ / 0 |
| T4b süzgeç sayısı | Her ıslak hacim poligonunda YS sembolü | tam 1; balkon poligonundaki süzgeç hiçbir ıslak hacme sayılmaz |
| T5 sıcak su daire içinde | `daire.poly.buffer(duvar_kalınlığı/2 + 2).contains(unary_union(sıcak hatlar))` her daire | True; ayrıca sıcak ∩ ortak alan poligonu = ∅ |
| T5b sıcak kombiden | Sıcak ağın graf bileşeni sayısı = 1 ve kombi `cikis`'e ≤ 15 cm düğüm var; derece ≥ 3 düğüm yalnız kombide | ✓ |
| T6 ofset sabit | Her paylaşılan yolda sıcak hattın soğuğa uzaklığı (20 cm örnekleme) | `O_SICAK ± 1` |
| T7 kolon köşede | Kolon merkezinin en yakın iki **dik** duvara uzaklığı | ikisi de ≤ `D_KOLON + 5`; betonarme/asansör/mek. havl. şaftı ≥ 15; kapı önü dışında |
| T7b kolon ataması | Her ıslak hacmin pis su bileşeni tek kolona bağlı; mutfak ve WC/banyo aynı kolonda değil | ✓ |
| T8 duvar dibi | `MOD_PIS='duvar_dibi'`: kol parçalarının duvar iç yüzüne uzaklığı | `D_DUVAR ± 3` (pah parçaları hariç) |
| T9 hol hattı | `MOD_HOL='orta'`: ana/omurga hol parçalarının hol genişliğinin ortasına uzaklığı | ≤ %15·genişlik; `duvar`: ≤ 15 cm duvar |
| T10 kapı | Temiz su hatları kapı kanadı yayı ve eşik aralığı ile kesişmez (giriş kapı yanı duvardan) | 0 |
| T11 etiket çakışma | Etiket kutuları ↔ (etiket, mimari yazı, boru çizgisi, sembol) kesişimi (kendi kılavuzu hariç) | 0; kılavuz–kılavuz 0 |
| T11b etiket sayısı | Ağaç kenarı başına etiket | ≤ 1; çift hatta birleşik 1 |
| T12 yasak bölgeler | Tüm hatlar ∩ (betonarme kolon/perde, asansör, mek. havl. şaftı, enerji odası) | 0 (`motor/gungoren/kolon_kontrol.py` + `nb.yasak_kontrol`) |

Kontrolör raporu JSON: `{test: {deger, sinir, gecti, ornekler[(x,y)...]}}`; geçmeyen test → üreten ajana geri (README (C) TESLİM ONAYI).

---

## 6. Uygulama sözde kodu (modül iskeleti `motor/sihhi2/guzergah.py`)
```python
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import substring, unary_union, nearest_points
from shapely import STRtree, affinity
import networkx as nx, ezdxf

def pis_su_islak(w: IslakHacim, yasak, komsular) -> dict:
    kolon = kolon_sec(w, yasak, komsular)                   # §2.3 (+ §2.6 ortak)
    if MOD_PIS == 'duvar_dibi':
        kollar = toplama_kollari(w, kolon)                  # §2.4 (pah_45)
        brs = {f: bransman(f, kollar[f.kol]) for f in w.armaturler if f.kind != 'YS'}
        ys = suzgec_konumu(w, kollar, kolon)                # §2.7
        brs[ys] = bransman(ys, kollar[ys.kol])
        for f in brs: brs[f] = agacta_kes(brs[f], [LineString(b) for g, b in brs.items() if g is not f])   # eşdoğrusal → T
    else:                                                   # 'yildiz' §2.9
        brs = yildiz(w, kolon)
    agac = graf([*kollar.values(), *brs.values()])          # düğümler: Q'lar, kolon, çıkışlar
    sb = sb_topla(agac, kolon)                              # her kenar: akış yukarısı SB, Ø
    assert len(r3.kesisimler([(w.ad, 'PIS', LineString(p)) for p in agac.kenarlar])) == 0
    return dict(kolon=kolon, kenarlar=agac, sb=sb)

def temiz_su_daire(daire: Daire) -> dict:
    T = nx.Graph()
    giris = kapi_yani(daire)                                # §3.2
    eksen = hol_eksen(daire.hol, MOD_HOL)
    T.add_edges(dik_baglanti(giris, eksen)); T.add_edges(eksen)
    for w in daire.islak_ve_mutfak:
        g_w = islak_giris_noktasi(w, eksen); T.add_edges(dik_baglanti(eksen, g_w))
        T.add_edges(islak_omurga(w, g_w, MOD_ISLAK_TEMIZ)) # §3.3: sıcak+soğuk tap'ler omurga üzerinde, soğuk-alan dik stub
    if daire.kombi: T.add_edges(kombi_baglanti(daire.kombi, T))   # kombi = yaprak
    H = sicak_alt_agac(T, daire.kombi, hot_taps(daire))     # §3.4
    taraf = taraf_ata(T, H)                                 # §3.5 A–D; çözümsüz → §3.5 yedek 1-3 / §3.6
    sicak = [offset_curve(LineString(Pi), taraf[Pi] * O_SICAK, join_style='mitre', mitre_limit=2) for Pi in zincirler(H)]
    assert daire.poly.buffer(8).contains(unary_union(sicak))
    assert kesisme_sayisi(T, sicak) == 0
    return dict(soguk=T, sicak=sicak, yb=yb_topla(T, giris), yb_h=yb_topla(H, daire.kombi))

def etiketle(kenarlar, engeller: STRtree, mahal_poly) -> list:   # §4
    out = []
    for e in sorted(kenarlar, key=lambda e: -e.length):
        if e.length < 1.6 * etiket_gen(e.metin): devret(e); continue
        for t, taraf, dik in adaylar(e):
            kutu = etiket_kutusu(e, t, taraf, dik)
            if not engeller.query(kutu): out.append((e, kutu, None)); engeller.insert(kutu); break
        else:
            kutu, kilavuz = mahal_disi(e, mahal_poly, engeller)
            out.append((e, kutu, kilavuz)); engeller.insert(kutu); engeller.insert(kilavuz)
    return out

def dxf_yaz(doc, sonuc):
    msp = doc.modelspace()
    for pts, dn in sonuc.pis:  msp.add_lwpolyline(pts, dxfattribs=dict(layer='ROTAS-PIS-SU', const_width=0.2))
    for pts in sonuc.soguk:    msp.add_lwpolyline(pts, dxfattribs=dict(layer='ROTAS-TEMIZ-SU-SOGUK'))
    for pts in sonuc.sicak:    msp.add_lwpolyline(pts, dxfattribs=dict(layer='ROTAS-TEMIZ-SU-SICAK', linetype='DASHED'))
    for e, kutu, kil in sonuc.etiket:
        msp.add_text(e.metin, dxfattribs=dict(layer=e.katman, height=ETIKET_H, rotation=e.aci)).set_placement(kutu.merkez, align='MIDDLE_CENTER')
        if kil: msp.add_line(*kil, dxfattribs=dict(layer='ROTAS-SEMBOL-KILAVUZ'))
```
Sembol/blok: MTY blokları kullanılmaz (B); vana, süzgeç, kolon sembolleri saf geometri (`semboller2`), kullanıcının referans görünümüne göre (ref?).

---

## 7. Eski koddan alınabilecek / atılacak parçalar
| Parça | Karar |
|---|---|
| `r3.kesisimler`, `r3.collinear`, `r3.temizle`, `r3.agacta_kes` | **Al** (kontrolör + ağaç temizliği) |
| `r3.oktilineer`, `r3.balik_sirti` | **At** (oda ortası omurga; §2 ile değişir) |
| `r3.Alan` (orta tercihli maliyet), `r3.Alan.grid(yumusak)` | **At** (ıslak hacim/daire için yanlış model); hol ekseni için §3.2 medial eksen |
| `nb3.sicak_yol`, `nb3.sira`, `nb3.daire_temiz` | **At** (sıcak dolaşım, sızıntılı maske) |
| `r2.sicak_yollar` (soğuk ağaç yolları), `r2.otele_sec` | **Fikir al**: §3.4 alt ağaç + §3.5 taraf kuralı (4 yön deneme yerine kurallı taraf) |
| `r2.kolon_adaylari/kolon_puan` | **Değiştir**: aday = halka köşeleri, puan = duvar dibi yürüyüş boyu (§2.3) |
| `mimari.room_at` (≤2 duvar geçişi) | **Değiştir**: yalnız `poly.contains` |
| `nb3.suzgec_duzenle` | **Değiştir**: §2.7 (balkon süzgeci ıslak hacme sayılmaz) |
| `etiket4` | **Değiştir**: engel kümesine boru çizgileri + mahal dışı kılavuz (§4); etiket üretimi parça başına 1 |
| `p2/router.py` A* | Yalnız ortak alan ana hattı için (kapı/oda kaçınma); ıslak hacim ve daire içinde kullanılmaz |

Referans ajanının çıktısı geldiğinde güncellenecek: §0 tablosu, `MOD_*`, §4 etiket metni/biçimi, §2.9/§3.3 kararı.
