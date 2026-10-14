> **ONAYLI (14.10.2026 16:39):** Kullanıcı `plan_kesit.py` çıktısını (plan + kesit A-A + kısmi görünüş B) DOĞRU kazan
> dairesi olarak onayladı: "her yerde bunu kullanacaksın". Aşağıdaki eski "teslimde kullanılmaz / arşiv" ifadeleri İPTALDİR.

# KAZAN DAİRESİ GEREKEN HER PROJEDE `onayli_kazan_dairesi()` KULLANILIR

```python
sys.path.insert(0, 'motor/deneme/kazan_dairesi')
import plan_kesit as PK
k = PK.onayli_kazan_dairesi(doc_veya_msp, girdi, x0, y0)   # girdi: dict | JSON yolu | JSON metni
# k = (x0, y0, x1, y1) hedef koordinatında kapsam; k.satir (cihaz listesi), k.harita (rol→numara), k.uyarilar,
# k.yeniden_ad {'katman','blok','stil'}, k.girdi (plan dahil kullanılan JSON), k.numara
```
- Plan 1/50 + KESİT A-A + KISMİ GÖRÜNÜŞ B + lejant + kontrol kutusu (menfez/kapı/bakım) + cihaz listesi + notlar tek
  paftada, sol alt köşe (x0, y0). **Görünüş / tarz değiştirilmez**: semboller (MTY blokları dahil), köprülü atlatmalar,
  renkler onaylı çizimdeki gibidir; MTY / atlatma kuralları ve `kontrol.py` etiket kuralı bu paftaya uygulanmaz.
- Görünüşün tabanı `kazan_dairesi_r1.py`dir (onay anındaki şema modülü, git dc2bb3e, DONDURULMUŞ — değiştirmeyin).
  `kazan_dairesi.py` R2'ye geçince `plan_kesit.py` kırılmıştı (Sema API değişti); R1 taban ile onaylı çıktılar birebir
  yeniden üretilir (`GUNGOREN_/KUCUK_2x110_KAZAN_DAIRESI_PLAN_KESIT.dxf`: 943/804 nesne, tüm öznitelikler aynı).
- `numara='R2'` (API varsayılanı): K-, P-, V- ... numaraları teslimdeki R2 prensip şemasından (`kazan_dairesi.py`,
  radyatör kolon şemasına gömülen dahil) rol eşlemesiyle alınır → şema ile senkron. `numara='R1'`: onay anındaki numaralar
  (CLI varsayılanı; mevcut PLAN_KESIT dosyaları bununla aynı kalır).
- JSON'da `plan` yoksa `varsayilan_plan()` temsili oda kurar (genişlik kazan adedine göre, sekonder kollektör sığmazsa
  bir kez genişletilir; kapı / alt menfez yazıları binmesin diye 200 cm aralık; ΣQ > 350 kW ise 2. kapı).
- Çakışma yönetimi: hedefte aynı adlı katman farklı renk/çizgi tipindeyse `<ad>-KD`; aynı adlı blok farklı içerikteyse
  `<ad>-KD` (içerik aynıysa hedefteki kullanılır; iç içe başvurular da izlenir); ROTAS yazı stili fontu farklıysa
  `ROTAS-KD`. Kaynak `$LTSCALE` (8) hedefinkine nesne bazında taşınır. Çerçeveye XDATA `ROTAS: ONAYLI_KAZAN_DAIRESI`
  yazılır (denetimler bu bölgeyi tanır). `cerceve=False` dış çerçeveyi aktarmaz.
- Kullanan modüller: `radyator` (merkezi sistem, `radyator_merkezi_R4.dxf`). Yeni modüller de bunu çağırır; başka kazan
  dairesi plan / kesit / görünüşü çizilmez.

```
python3 plan_kesit.py ornekler/gungoren.json ../../../proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_PLAN_KESIT.dxf [png] [--numara R1|R2]
```

## Prensip şeması R2 ↔ onaylı plan_kesit numara eşleşmesi (14.10.2026 denetimi)
Rol bazında (kazan, pompa, gidiş/dönüş vanası, zon vanası, gaz vanası ...) iki numaralandırma karşılaştırıldı:
cihaz adı/özelliği tutarsızlığı **0**; K-, P-, DK-, HA-, TA-, GT-, KL-, B-, BY-, NU-, EV-, M-, TM-, HP-, GF-, GR-, SV-,
GA- numaraları **aynı**. **V- numaraları FARKLI** (Güngören 40 rol, Küçük 2×110 35 rol): R2'de gaz hatları ayrı bölgeye
alındığı için gaz cihaz vanaları / esnek bağlantılar V- sırasının sonuna geçti (R1: V-21.. gaz, R2: V-21.. kelebek
vanalar; ör. Güngören V_PG1 V-31 → V-21, gaz cihaz vanası V-21 → V-39). Ayrıca SV-01 / GA-01 özellik metni R2'de
elektrik kalemi olmadan yazılır. Sonuç: depodaki `*_PLAN_KESIT.dxf` (R1 numara) ile `*_SEMA_R2.dxf` V- numaraları
uyuşmaz; şemayla birlikte teslimde `--numara R2` / API varsayılanı kullanılmalı (dosyalar kullanıcı sorulmadan
yeniden yazılmadı).

## R2 kuralları (kazan_dairesi.py)
- **MTY bloğu yok.** Tüm semboller saf geometri `ROTAS-` blokları: `bloklar_r2.py` (küresel / kelebek vana, çek valf,
  pislik tutucu, otomatik dolum, kilitli vana, esnek bağlantı, emniyet ventili, manometre, termometre, O.H.A.C, denge kabı,
  hava ayırıcı, tortu ayırıcı, genleşme tankı, baca şapkası, kollektör) + `bloklar.kendi_bloklar` (kazan, pompa, selenoid,
  regülatör, gaz alarm, boyler, nötralizasyon, ok). `motor/deneme/semboller2/` bu tarihte depoya işlenmemiş (yarım)
  olduğundan kullanılmadı; hazır olunca `bloklar_r2.TANIM` onunla değiştirilebilir.
- **Boru atlatma / köprü yok.** Ana hidrolik şemada yalnız iki toplayıcı vardır: kazan gidişleri üstte, dönüşleri altta.
  Kaskadda kaçınılmaz görünen kesişmeler (baca, doğalgaz, yoğuşma) **ayrı bölgede** çizilir: kazanın altında GAZ ve
  YOĞ., üstünde BACA bağlantı uçları (oklu kısa hat) bulunur; hatların kendisi alttaki **DOĞALGAZ BAĞLANTI ŞEMASI**
  (giriş → ana vana → selenoid → filtre → [regülatör] → manometre → kollektör vanası → kazan başına vana + esnek bağlantı,
  "K-01 KAZANINA"), **YOĞUŞMA DRENAJ ŞEMASI** (K-01..K-n → [nötralizasyon] → pis su) ve **BACA BAĞLANTI ŞEMASI**
  (K-01..K-n → baca kollektörü → baca + şapka) bölgelerindedir. `Sema.kesisim_denetle()` her çalışmada boru-boru iç
  kesişmesini sayar (0 olmalı).
- **Numara–sembol eşleşmesi:** her numara bir kez yazılır ve kendi sembolünün sınır kutusuna en çok 18 cm uzakta, başka
  hiçbir sembol kendi sembolünden 4 cm daha yakın olmayacak yere konur (bulunamazsa 28 cm / 2,5 cm). Numara DXF'te
  sembol INSERT'ine XDATA olarak (`ROTAS`, `NO=V-01`) yazılır; `kontrol.py` bağımsız olarak "etiketin en yakın sembolü
  kendi sembolü mü" testini yapar.
- **Elektrik kalemi yok:** gaz alarmı – selenoid sinyal hattı çizilmez (cihazlar kalır, notta "elektrik projesinde").
- Gömülü kullanım: `ciz(P, cikti, gomulu=True)` başlık / liste / notları çizmez, zon gidişini şemanın üstüne, zon dönüşünü
  altına uzatır (`S.baglanti`), cihaz listesi `S.satir`, notlar `S.notlar` (radyatör kolon şeması bunu kullanır).

## Çalıştırma
```
python3 kazan_dairesi.py ornekler/gungoren.json ../../../proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_SEMA_R2.dxf
python3 kontrol.py <cikti.dxf>   # ÖZET: MTY 0, köprü 0, kesişme 0, etiket %100, elektrik 0 + çakışma dökümü
python3 onizleme.py <cikti.dxf> <png> [x0,y0,x1,y1 dpi genişlik]   # yalnız kontrol için, depoya konmaz
```
Son çıktılar: `GUNGOREN_KAZAN_DAIRESI_SEMA_R2.dxf` (5×110 kW, etiket 102/102), `KUCUK_2x110_KAZAN_DAIRESI_SEMA_R2.dxf`
(2×110 kW + boyler + nötralizasyon, etiket 84/84); ikisinde de MTY 0, köprü 0, kesişme 0, çakışma yok.

JSON alanları (bkz. `ornekler/`): proje, deneme, rejim{gidis,donus}, kazan{adet,kapasite_kw,tip,pompa{ad,debi,basma}},
denge_kabi{cap}, genlesme{hacim_l,on_basinc,maks_bar}, emniyet{ventil_bar,ventil_cap},
zonlar[{ad,aciklama,debi,basma,yedek,adet}], boyler{hacim_l,tip,cap,ev_bar,sarj_pompa{debi,basma}}|null,
sirkulasyon{debi,basma,cap}|null, notralizasyon bool, baca{cap,tip},
dogalgaz{vana,filtre,selenoid,alarm,regulator{giris,cikis}|null, kazan_cap,kollektor_cap,giris_cap}, doldurma, notlar[].
(`plan` bloğu plan_kesit.py içindir; şema onu kullanmaz.)

## Sınırlar / sorulacaklar
- Baca, gaz ve yoğuşma ayrı bölgede (kazan numarasıyla eşlenmiş) gösterildi; kullanıcı bunları ana şemada görmek isterse
  kesişmesiz çizim mümkün değildir (kaskadda her kazanın 5 bağlantısı vardır, yalnız 2'si toplayıcıyla kesişmesiz kalır).
- Gaz alarm cihazı (dedektör) çizildi, kablosu çizilmedi — tamamen kaldırılması istenirse `dogalgaz.alarm=false`.
- Yerden ısıtma karışım (3 yollu) vanalı zon, eşanjör, akümülasyon tankı, yumuşatma yok; kazan bloğu duvar tipi.
- Hesap (genleşme hacmi, denge kabı çapı, baca) yapılmaz; değerler JSON'dan gelir.
- Teslimde prensip şeması R2 + ONAYLI plan/kesit/kısmi görünüş paftası (`onayli_kazan_dairesi`, numara R2).

---

# ONAYLI PLAN + KESİT A-A + GÖRÜNÜŞ B (`plan_kesit.py`, 14.10.2026)

Kural: "tüm projelerde gerekli kesit ve görünüşler". Aynı JSON'a `plan` bloğu eklenir; tek DXF'te:
1. **KAZAN DAİRESİ PLANI 1/50** — EI 120 taramalı duvarlar (oda poligonu + `duvar` kalınlığı), duvar tipi kaskad
   kazanlar kazan duvarında (üst kenar), gaz / yoğuşma / dönüş / gidiş başlıkları (kazan önünden 12 / 24 / 40 / 100 cm),
   kazan bağlantıları köprülü, kazan pompası + vanası, hava ayırıcı, tortu ayırıcı, denge kabı, genleşme tankı
   (kilitlenebilir vana), sekonder gidiş/dönüş kollektörü, zon pompaları (asıl + yedek), boyler, nötralizasyon,
   yer süzgeci, baca + tavandaki baca kollektörü, gaz girişi (ana vana + selenoid DIŞARIDA, filtre/regülatör/manometre/
   kollektör vanası içeride), gaz alarm, alt/üst menfez (açıklık + ızgara + ölçü/kot etiketi), kapılar (dışa açılır,
   EI2 90-C; ΣQ > 350 kW veya A > 100 m² ise 2. kapı yoksa otomatik eklenir + uyarı), bakım alanı (≥1,00 m), ölçü
   zincirleri, A-A kesit ve B görünüş işaretleri, ±0,00 kotu.
2. **KESİT A-A** (1. kazan ekseninden): döşeme/tavan/duvar kesiti, kazan yan görünüşü, başlık kesitleri (daire) ve
   kotları, baca kollektörü kesiti, menfez açıklıkları (kesite izdüşürülmüş) ve kotları, düşey ölçüler, kazan önü serbest
   mesafe kontrolü.
3. **GÖRÜNÜŞ B (kazan duvarı)**: kazan ön görünüşleri, her kazanın gidişinde EV, HP, TM, M, pompa, çek valf, vana;
   dönüş vanası, gaz vanası + esnek bağlantı, yoğuşma; başlıklar köprülü; baca kollektörü (çift çizgi) + baca (tavandan
   çatıya), gaz alarm (tavanda, üst menfezden yüksek), kot kolonu.
4. **Lejant + kontrol kutusu** (menfez hesabı §5.4, kapı sayısı, bakım mesafesi, EI 120) + **cihaz listesi** + notlar.

**Numara senkronu:** `numara_haritasi()` prensip şemasını (`kazan_dairesi.ciz`) bellekte üretip numaraları rollerine
göre alır; cihaz listesi şemanınkiyle birebir aynıdır (K-, P-, V-, DK-, HA-, TA-, GT-, KL-, GF-, GR-, SV-, GA-, B-, BY-,
NU-, EV-, M-, TM-, HP-). Şema çıktısı bu çalışmayla değişmedi.

Menfez: ΣQ < 1000 kW `S_A = F·a·2,25·(ΣQ+70)` cm², ≥ 1000 kW `ΣQ/3600` m²; üst `S_Ü = max(180 cm²; oran·S_A)`
(`ust_menfez_orani`, varsayılan 0,6 — İGDAŞ >1000 kW oranı; <1000 kW için yerel dağıtım şirketiyle TEYİT). Ölçü 5 cm
modüllü, kenar oranı ≤ 1,5 (F = 1).

```
python3 plan_kesit.py ornekler/gungoren.json proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_PLAN_KESIT.dxf
python3 kontrol.py proje/denemeler/kazan_dairesi/GUNGOREN_KAZAN_DAIRESI_PLAN_KESIT.dxf
```
`plan` alanları: `temsili` (true → "DENEME – temsili oda"), `oda` [[x,y]...] (cm, dik açılı), `duvar`, `doseme`,
`ic_yukseklik`, `kazan_olcu`{g,d,h,ara,alt_kot,baca_cap}, `baca` [x,y] (y kazan baca eksenine çekilir),
`kapilar` [{duvar: alt|ust|sol|sag, konum, genislik}], `menfez`{alt{duvar,konum,alt_kot}, ust{duvar,konum,tavandan}},
`menfez_F`, `menfez_a`, `ust_menfez_orani`, `kazan_baslangic` (ops.).

Sınırlar: kazan duvarı odanın üst (max y) kenarı olmalı (oda poligonu buna göre döndürülerek verilir); görünüş kısmi
(denge kabı / genleşme tankı planda); sistem doldurma ve kullanım suyu bağlantıları yalnız şemada; görünüşte kazan
araları 40 cm iken etiketler sık; ölçüler kendi bloklarıyla (AutoCAD DIMENSION değil).
