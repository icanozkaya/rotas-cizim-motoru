# 05 — Mimari DXF'ten otomatik mekanik tesisat çizimi: algoritma araştırması

Tarih: 2026-10-14 · Kapsam: mimari kat planı DXF → mahal/duvar/kapı modeli → boru güzergâhı, yerden ısıtma serpantini,
sprinkler yerleşimi, etiketleme, kolon şeması/P&ID. Her başlıkta: önerilen yöntem (adım adım sözde kod), kütüphane, kaynak.

Ortam notu: depoda kurulu sürümler **shapely 2.2.0, ezdxf 1.4.4, networkx 3.6.1**, Graphviz `dot` ikili dosyası var
(`/usr/bin/dot`); `rtree` ve `pygraphviz` yok (shapely 2'nin `STRtree`'si rtree yerine yeter; Graphviz'e `subprocess` ile
`dot -Tjson` çağrısı yapılabilir).

Motorda zaten olanlarla bağlantı:
- `motor/rooms.py` → rasterden mahal tespiti + kapı yayından kapı kapatma (`door_closures`). Aşağıdaki §1 vektörel yol buna
  alternatif/doğrulayıcıdır.
- `motor/router.py` → ızgara A* (duvar bandı tercihi, dönüş cezası, başka sistemi kesme cezası). §2 bunun genişletmesidir.
- `motor/spiral3.py` → dik açılı poligonda bifilar (salyangoz) serpantin. §3 genel poligon ve devre bölme ekler.

---

## 1. DXF kat planından duvar, kapı, pencere ve mahal çıkarma

### 1.1 Önerilen yöntem (vektör tabanlı, CAD dosyası için)
Görüntü tabanlı derin öğrenme (CubiCasa5K, Raster-to-Vector) PDF/JPG plan için gereklidir; elimizde **DXF** olduğundan
öncelik geometrik/kural tabanlı çözümdür. Derin öğrenme yalnızca katmanları bozuk/“0” katmanlı dosyalarda yedek.

**Adım A — Ön işleme**
```
doc = ezdxf.readfile(f)
msp = doc.modelspace()
# 1) Blokları patlat (ezdxf: insert.virtual_entities()), INSERT adını+konumunu ayrıca sakla (kapı/pencere için)
# 2) Birim: $INSUNITS -> cm'ye çevir
# 3) Katman sınıflandırma: ad sözlüğü (DUVAR, WALL, A-WALL, BETON, KOLON, KAPI, DOOR, PENCERE, WINDOW, MAHAL, TEXT...)
#    + katman bilinmiyorsa istatistik: paralel çift çizgi oranı yüksek katman = duvar
# 4) Eğrileri parçala: ARC/CIRCLE/SPLINE -> ezdxf.path.make_path(e).flattening(dist=1.0)
# 5) Yakalama (snap): uç noktaları 0.5–1 cm toleransla birleştir (shapely.set_precision(geom, 0.5))
```

**Adım B — Duvar çiftleri ve orta çizgi**
```
segs = duvar katmanındaki tüm doğru parçaları
idx = STRtree(segs)
for s in segs:
    for t in idx.query(s.buffer(Tmax)):          # Tmax = 60 cm (en kalın duvar)
        if paralel(s,t, aci_tol=1°) and 5 <= mesafe(s,t) <= Tmax and izdusum_ortusmesi(s,t) > 0.5*min(len):
            duvar_parcasi.append( (orta_cizgi(s,t), kalinlik=mesafe(s,t)) )
# Alternatif (eğik/karmaşık duvarlar): duvar bandı poligonu = polygonize(duvar çizgileri)
#   -> medial axis: shapely.voronoi_polygons ile poligon kenarını sık örnekleyip iç Voronoi kenarlarını al
#   -> veya pygeoops.centerline / centerline paketi; kısa dalları (< kalınlık) buda
duvar_grafi = networkx: düğüm = orta çizgi uçları (snap), kenar = duvar parçası (kalınlık özniteliği)
```
Orta çizgi, §2 güzergâhında “duvar dibi” referansı ve §4'te duvar mesafesi için kullanılır.

**Adım C — Kapı ve pencere tespiti**
```
# 1) Blok adı: INSERT.dxf.name regex (KAPI|DOOR|D\d+|PENCERE|WIN|PNC) -> doğrudan
# 2) Blok adı anlamsızsa geometri imzası:
#    kapı  = yay (ARC) 80°-100°, yarıçap 55-125 cm + yay merkezinden çıkan yarıçap boyunda bir doğru (kanat)
#            menteşe = yay merkezi, açıklık genişliği = yarıçap, açılma yönü = yay orta noktası tarafı
#    pencere = duvar bandı içinde, duvara paralel 2-4 ince çizgi (cam), duvar kalınlığı boyunca uç kapakları
# 3) Açıklığı duvara bağla: duvar orta çizgisinde menteşe izdüşümü; [t0,t1] aralığı "açıklık" olarak işaretlenir
# 4) Mahal kapatma: her kapı açıklığına duvar yüzeyleri arasında 2 "sanal kapatma çizgisi" ekle
#    (motor/rooms.py::door_closures mantığının vektör sürümü)
```

**Adım D — Mahal poligonları (polygonize)**
```
lines = duvar yüz çizgileri + kolon kenarları + pencere/kapı kapatma çizgileri
noded = shapely.node(MultiLineString(lines))        # tüm kesişimlerde böl (polygonize için şart)
polys, dangles, cuts, invalid = shapely.polygonize_full(noded.geoms)
adaylar = [p for p in polys.geoms if 1.0 m² <= p.area <= 2000 m²]
# duvar bandı poligonlarını ele: ince-uzun (alan/çevre² küçük, maximum_inscribed_circle yarıçapı < Tmax/2)
mahaller = [p for p in adaylar if shapely.maximum_inscribed_circle(p).length > 30 cm]  # dönen doğru merkez->sınır = iç çember yarıçapı
# Dış kontur (bina dışı) = en büyük poligon ve hiçbir mahal adı içermez -> ele
# Boşluk kapatma: kapatılmamış açıklıklar için polygonize başarısızsa
#   uç noktası boşta (dangle) olan çizgiyi en yakın duvara <= 15 cm uzat (snap/extend), sonra tekrar
```

**Adım E — Mahal adı TEXT/MTEXT'in poligona atanması**
```
for t in TEXT/MTEXT (mahal katmanı veya tüm yazılar):
    p = insert noktası (MTEXT için hizalama dikkate alınarak metin kutusunun merkezi)
    aday = [m for m in STRtree(mahaller).query(Point(p), predicate="within")]
    if not aday: en yakın mahal ve mesafe < 50 cm ise ona
    m.etiketler.append(t)
# Bir mahalde birden fazla yazı: sınıflandır
#   ad (harf ağırlıklı: SALON, YATAK ODASI, WC, BANYO, MUTFAK)
#   alan ("12.45 m²" / "A=..." regex) -> doğrulama: |poligon alanı - yazı alanı| / yazı < %5 ise atama doğru
#   kod (Z-01 vb.), döşeme (seramik/parke) -> ısı kaybı ve yerden ısıtma döşeme direnci girdisi
# Hiç yazı yoksa: "MAHAL-n" ver, polylabel ile merkez yerleştir, kullanıcıya sor
```
Mahal adından tip sözlüğü (WC/BANYO → ıslak hacim → sıhhi tesisat, sprinkler OH vb.) motorun diğer adımlarını besler.

**Adım F — Doğrulama**
- Mahal alanları toplamı ≈ brüt alan − duvar alanı (± %3).
- Her mahal en az bir kapı açıklığına komşu olmalı (komşuluk grafi: mahal–kapı–mahal; networkx bağlı bileşen).
- Bu komşuluk grafi §2'de koridor/kapı geçişleri için kullanılır.

### 1.2 Kütüphaneler
- **ezdxf** (okuma, blok patlatma, `ezdxf.path` ile eğri düzleştirme, `bbox`): https://ezdxf.readthedocs.io/en/stable/
- **shapely 2** (`node`, `polygonize_full`, `STRtree`, `voronoi_polygons`, `maximum_inscribed_circle`, `set_precision`):
  https://shapely.readthedocs.io/en/stable/
- **pygeoops.centerline** (Voronoi tabanlı orta çizgi, dal budama): https://pygeoops.readthedocs.io/en/stable/api/pygeoops.centerline.html
- **centerline** (PyPI, Voronoi orta çizgi): https://pypi.org/project/centerline/0.6.4
- **networkx** (duvar grafi, mahal komşuluk grafi)
- CGAL Straight Skeleton (eğik duvarlarda en temiz orta çizgi; Python'da scikit-geometry üzerinden):
  https://doc.cgal.org/5.5.4/Straight_skeleton_2/modules.html

### 1.3 Makaleler / veri setleri (yedek: görüntü tabanlı)
- CubiCasa5K — 5000 plan, duvar/kapı/pencere/oda çok görevli model: https://arxiv.org/pdf/1904.01920 ,
  kod: https://github.com/cubicasa/cubicasa5k
- Raster-to-Vector (Liu ve ark., ICCV 2017) — köşe tespiti + tamsayı programlama ile vektörleştirme:
  https://openaccess.thecvf.com/content_ICCV_2017/papers/Liu_Raster-To-Vector_Revisiting_Floorplan_ICCV_2017_paper.pdf ,
  kod: https://awesome.ecosyste.ms/projects/github.com%2Fart-programmer%2FFloorplanTransformation
- Floor-SP — oda bazında en kısa yol ile poligon çıkarımı: https://arxiv.org/pdf/1908.06702
- FloorPlanCAD — **vektörel CAD** çizimlerde sembol (kapı, pencere, vitrifiye) tespiti veri seti (ICCV 2021):
  https://arxiv.org/pdf/2105.07147 — DXF'te blok adı anlamsız olduğunda sembol tanıma için en ilgili kaynak.
- CubiGraph5K (oda komşuluk grafi): https://github.com/luyueheng/CubiGraph5K

---

## 2. Boru/kanal güzergâhı (ortogonal routing)

### 2.1 Önerilen yöntem: iki katmanlı — kaba graf + ince ızgara A*
Tek ızgara A* (mevcut `router.py`) küçük katlarda yeterli; büyük katlarda ve çoklu hatta **(1) kaba topolojik yol
(mahal/kapı grafı veya ortogonal görünürlük grafı) → (2) koridor içinde ince ızgara A* → (3) paralel öteleme (nudging)**
daha hızlı ve daha düzenli sonuç verir.

**Adım A — Maliyet haritası (mevcut Grid'in genişletilmiş hali)**
```
maliyet(h) = 1
  + w_uzak * mesafe_duvar_yuzu(h)/band        # duvar dibini tercih (distance transform, scipy.ndimage)
  + INF  if h kolon/perde/şaft dışı yasak alan
  + w_islak * (h ıslak hacim dışında ve sistem=pis su)   # pis su ıslak hacim dışına çıkmasın
  + w_kapi  * (h kapı açılma yayı içinde)               # kapı önünden geçişi minimize et
  + w_kes   * (h başka sistem borusu üzerinde)          # kesişme -> köprü gerektirir
  + w_yakin * (h başka boruya < min_aralık)
```

**Adım B — Minimum bükülme A\* (durum = hücre + yön)**
Klasik A* bükülme saymaz; durum uzayına **geliş yönünü** ekle:
```
durum = (i, j, yon)  yon ∈ {D, B, K, G} (+ başlangıçta "yok")
g(durum') = g(durum) + adim*maliyet(hücre') + (yon' != yon ? C_bukulme : 0)
h(durum)  = manhattan(hücre, hedef) + (hedefle aynı eksende değilse C_bukulme)   # kabul edilebilir sezgisel
# Çoklu hedef (branşmanı mevcut ana hatta bağla): hedef = sistem ağacının tüm hücreleri,
#   h = mesafe dönüşümü haritasından (önceden hesaplanmış) okunur.
# C_bukulme ≈ 5–20 hücre: dirsek maliyeti; büyük değer = az dirsek, uzun yol.
```
Lexicographic seçenek: önce dirsek sayısı, sonra uzunluk minimize → maliyeti `(bükülme, uzunluk)` ikilisi yap.

**Adım C — Ortogonal görünürlük grafı (ızgara yerine, büyük alanlarda)**
```
# Wybrow-Marriott-Stuckey "orthogonal visibility graph":
for her engel kutusu köşesi ve port: yatay+dikey ışın gönder, ilk engelde dur
düğümler = ışın kesişimleri; kenarlar = ışın parçaları
A* (durum=düğüm+yön, bükülme cezalı) -> en az dirsekli ortogonal yol
# Sonra "nudging": aynı kanalı paylaşan yolları eşit aralıkla ayır, sıralamayı kesişim sayısını azaltacak şekilde seç
```
Bu yöntemin hazır uygulaması **libavoid** (Adaptagrams, C++; ELK'de “libavoid” algoritması olarak da var).

**Adım D — Çoklu hat (temiz/sıcak/sirkülasyon) paralel öteleme**
İki yaklaşım; birincisi tesisat projesinde daha okunur ve önerilir:
```
# Yaklaşım 1 (demet/omurga): tek "omurga" güzergâhı bul, sonra hatları sabit sırada ötele
omurga = route(kaynak, hedefler)                     # §2B
sira = ["SOGUK", "SICAK", "SIRK"]                    # duvardan uzaklaşan sıra sabit (standart)
for k, sistem in enumerate(sira):
    d = (k - (n-1)/2) * aralik                        # veya duvar tarafından: d = e0 + k*aralik
    hat[sistem] = shapely.offset_curve(omurga, d, join_style="mitre", mitre_limit=2)
# Dönüşlerde sıra korunur (mitre); branşman ayrılırken dış hat önce ayrılır (iç içe L dirsekler)
# Yaklaşım 2 (sıralı yönlendirme): hatları sırayla A* ile çiz; çizilen hattın hücreleri
#   +-aralık bandında bir sonraki hat için "çekici" (düşük maliyet) ama üstü "yasak" -> doğal paralellik
```

**Adım E — Kesişme köprüsü (atlama/kesik gösterimi)**
```
for her (a, b) farklı sistem hat çifti:
    for x in a.intersection(b) noktaları:
        alttaki = öncelik sırasına göre (ör. büyük çap/ana hat üstte kalır, branşman kırılır)
        # DXF gösterimi: alttaki çizgiyi x etrafında r=2*çizgi_aralık kadar böl (gap) veya yarım daire köprü
        alttaki = alttaki.difference(Point(x).buffer(r))           # kesik gösterim
        # yay köprü istenirse: ezdxf ARC merkez x, yarıçap r, başlangıç/bitiş açıları hat yönüne göre
```
Kesişme sayısını en aza indirmek için Adım A'da `w_kes` yüksek tutulur; kalanlar köprü ile çözülür.

**Adım F — Sonradan düzeltme**
- Eşdoğrusal noktaları birleştir (mevcut `_collinear`), kısa zikzakları (< 2 hücre) “kanca kaldırma” ile düzle.
- Dirsek noktalarında boru çapı/yarıçapı ile fittings bloğu (MTY dirsek) yerleştir.

### 2.2 Kütüphaneler
- numpy + scipy.ndimage (distance transform), heapq (A*), networkx (`astar_path`, graf), shapely `offset_curve`.
- **extremitypathfinder** (poligon ortamında görünürlük grafı + en kısa yol, Python):
  https://extremitypathfinder.readthedocs.io/ ; **pyvisgraph**: https://pypi.python.org/project/pyvisgraph/0.1/
  (bunlar ortogonal değildir — kaba yol için kullanılır, sonra ortogonalleştirilir).
- **libavoid** (ortogonal konnektör yönlendirme + nudging): https://www.adaptagrams.org/documentation/libavoid.html ;
  ELK içinden: https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-alg-libavoid.html

### 2.3 Kaynaklar
- Wybrow, Marriott, Stuckey — “Orthogonal Connector Routing” (ortogonal görünürlük grafı, bükülme+uzunluk, nudging):
  https://findanexpert.unimelb.edu.au/scholarlywork/863594-orthogonal-connector-routing ;
  “Orthogonal Hyperedge Routing” (bir kaynaktan çok hedefe ağaç — branşmanlı tesisat hattına doğrudan uyar):
  https://findanexpert.unimelb.edu.au/scholarlywork/345909-orthogonal-hyperedge-routing
- Ortogonal kenar yönlendirme (EditLens, libavoid tabanlı uygulama notları): https://arxiv.org/pdf/1612.05064
- MEP boru otomatik güzergâh sistemi (ISARC/IAARC): https://www.iaarc.org/./publications/fulltext/173_Development_of_Auto_Route_System_for_MEP_Mechanical__Electrical_and_Plumbing_Pipe_Design_in_Construction.pdf
- Engelsiz 3B optimal boru güzergâhı teknikleri: https://www.scitepress.org/Papers/2020/89233/89233.pdf
- Geliştirilmiş çoklu arama A* ile 3B boru güzergâhı: https://research.mpu.edu.mo/en/publications/improved-multi-search-strategy-a-algorithm-to-solve-three-dimensi/
- Mevcut motorda referans alınan fikir: red1oon/mep_engineering (A* + dik açıya çevirme) — `motor/router.py` başlığında.

---

## 3. Yerden ısıtma serpantini (salyangoz ve meander)

### 3.1 Önerilen yöntem
**Adım A — Isıtılacak bölge**
```
bolge = mahal.buffer(-kenar_mesafesi, join_style="mitre")      # duvardan 10–15 cm (kenar şeridi)
bolge = bolge.difference(unary_union([sabit_dolap, kuvet, dus_tekne, kolon]).buffer(5))
# MultiPolygon çıkarsa: parçalar ayrı alt-devre adayı
```

**Adım B — Devre sayısı ve mahal bölme (uzunluk sınırı)**
```
L_tahmini = A_bolge / s + 2 * besleme_mesafesi(kollektör -> mahal girişi)     # s: boru aralığı (m)
n = ceil(L_tahmini / L_max)            # L_max: 16 mm boru ~ 80–100 m; 20 mm ~ 120 m (üretici kataloğu esas)
if n > 1:
    # Bölme: dik açılı mahalde en uzun kenara dik "kesim çizgileri" ile eşit alanlı şeritler
    # (ikili arama ile kesim konumu: area(parça_k) = A/n ± %5)
    # Karmaşık poligonda: rektangüler ayrıştırma (motor/rooms.py::rects_in) sonra parçaları
    #   alan dengesine göre birleştirerek n gruba ayır (bitişiklik grafında açgözlü birleştirme)
    # Her parçanın giriş köşesi kollektöre bakan kenarda olmalı
# Kenar bölgesi (cam cephe önü) için sıklaştırılmış aralık: bolge_kenar = bolge ∩ cephe.buffer(1.0 m)
```

**Adım C1 — Salyangoz / karşı akış (bifilar, counterflow)** — eşit sıcaklık dağılımı, konut için önerilen
```
# Fikir: halkaları 2s aralıkla içe doğru üret (gidiş), aralarına s kaydırılmış halkalar (dönüş) yerleştir,
# merkezde "S" dönüşüyle gidiş -> dönüş bağlanır.
halkalar = []
d = 0
while True:
    r = bolge.buffer(-d, join_style="mitre")
    if r.is_empty or maximum_inscribed_circle(r) < s: break
    halkalar.append(r.exterior); d += s
# Halkalar dönüşümlü olarak gidiş (0,2,4..) ve dönüş (1,3,5..) setine ayrılır.
# Her halka giriş köşesinin yakınında kesilir ve bir sonraki aynı-setteki halkaya "çapraz atlama" ile bağlanır
#   -> tek sürekli spiral (Fermat spiral mantığı).
# Merkezde: en içteki gidiş ve dönüş halkası yarıçapı >= R_min (boru min. bükülme ~ 5*D) olan S/U ile birleştirilir.
# Kontrol: check_self(path, s) -> kendi kendini kesmeme ve min aralık (motor/spiral3.py)
```
Mevcut `spiral3.bifilar` dik açılı poligonlar için bunu yapıyor; genel poligonda `buffer(-d)` ile halka üretimi +
**Connected Fermat Spirals** (Zhao ve ark. 2016) bağlama yöntemi kullanılabilir. Parçalı (çok halkalı/delikli) bölgede:
her bileşen ayrı Fermat spirali → komşu spiraller kenardan birbirine bağlanır (makaledeki “spiral ağacı”).

**Adım C2 — Meander (yılan, serpantin)** — banyo, dar koridor, kenar bölgesi için basit
```
eksen = poligonun en uzun kenar yönü (minimum_rotated_rectangle ile)
bolge_r = rotate(bolge, -aci)                           # eksene hizala
y = ymin + s/2; yol = []; yon = +1
while y < ymax:
    kesit = bolge_r ∩ yatay_cizgi(y)                     # MultiLineString olabilir -> en uzun / sıralı parçalar
    yol += kesit uçları (yon'a göre) ; yon *= -1 ; y += s
# Dönüşler: yarım daire r = s/2 (R_min kontrolü; s/2 < R_min ise "omega" dönüş veya 2s'lik ilmek)
yol = rotate(yol, +aci)
# Kesitin bölündüğü (girinti) yerlerde poligonu dikdörtgenlere ayırıp her birinde meander, sonra sırala
```
Meander'da giriş tarafı daha sıcak olur → giriş, cephe/soğuk kenar tarafına konur.

**Adım D — Besleme hatları ve kollektör**
```
for devre in devreler:
    giris = devre yolunun giriş köşesi
    besleme = route(kollektör_portu, giris)   # §2 A*, sistem="YI", paralel gidiş-dönüş çifti (§2D offset)
    L_toplam = devre.length + 2*besleme.length
    assert L_toplam <= L_max   # aşarsa n+1 ile Adım B'ye dön
# Kapı eşiklerinden geçen besleme demetleri tek koridor şeridinde paralel (offset) gider
```

**Adım E — Çıktı**: Devre adı (D1…Dn), uzunluk, aralık, alan → hesap Excel'i ve DXF etiketleri (§5).

### 3.2 Kütüphaneler
- shapely `buffer(-d, join_style="mitre")`, `offset_curve`, `maximum_inscribed_circle`, `minimum_rotated_rectangle`,
  `affinity.rotate`; pyclipper (Clipper offset, alternatif ve hızlı); CGAL straight skeleton (dar köşelerde daha temiz offset).

### 3.3 Kaynaklar
- Zhao ve ark., “Connected Fermat Spirals for Layered Fabrication” (SIGGRAPH 2016) — poligonu tek sürekli, kendini kesmeyen
  spiral ile doldurma; karşı akış (bifilar) serpantine birebir uyar: https://www.cs.purdue.edu/homes/bbenes/papers/Zhao16ToG.pdf
- Sürekli dolum yolu (devamı): https://arxiv.org/pdf/2201.02374
- Bükülme yarıçapı ve giriş konumunun yerden ısıtmaya etkisi (tez): https://elibrary.tucl.edu.np/bitstream/123456789/20903/1/Ishwor%20Acharya%20Master%20Thesis%20Mechanical%20and%20aero%20mechanical%20systems%20design%20and%20eng%20oct2023.pdf
- Ticari örnek mantık (CYPE radyant döşeme devresi, ArchlineXP yerden ısıtma): https://info.cype.com/en/subject/cypehvac-radiant-floor-circuit/ ,
  https://help.archlinexp.com/hc/de/articles/21504621317905-Heating-system-underfloor
- Devre uzunluğu sınırları: https://digital.bnpmedia.com/article/Pushing+The+Circuit+Length+Envelope/3374473/585187/article.html ,
  https://mechanicalbusiness.com/?p=28110 (kesin değer üretici kataloğu + EN 1264 basınç kaybı hesabından alınmalı).

---

## 4. Sprinkler yerleşimi

### 4.1 Kural parametreleri (girdi tablosu; değerler TS EN 12845 / NFPA 13 ve proje tehlike sınıfından okunur)
`S_max` (iki sprinkler arası azami), `A_max` (sprinkler başına azami koruma alanı), `D_duvar_max` (duvara azami,
genelde S_max/2), `D_duvar_min` (duvara asgari, ör. NFPA'da 102 mm), `S_min` (sprinkler arası asgari, ör. 1,8 m),
engel kuralları (kiriş/kanal altı, “3 kat kuralı”). Değerleri koda gömme — `tesisat-hesap-kutuphanesi` kaynak tablosundan oku.

### 4.2 Önerilen yöntem: dikdörtgen/kaydırmalı ızgara + optimizasyon + engel düzeltme
**Adım A — Dikdörtgen mahal (en sık durum), kapalı form**
```
P = mahal.buffer(-0) ; eksen = minimum_rotated_rectangle yönü ; L, W = kenarlar
for S_L in aday adımlar:
    nL = ceil(L / S_L_max) ; S_L = L / nL                # eşit bölme: uçta S_L/2 duvar mesafesi
    nW = ceil(W / S_W_max) ; S_W = W / nW
    kontrol: S_L*S_W <= A_max, S_L,S_W <= S_max, S_L/2 <= D_duvar_max
    noktalar = {(L*(i+0.5)/nL, W*(j+0.5)/nW)}
# En az nL*nW veren, eşitlikte S_L≈S_W (kareye yakın) olanı seç
```

**Adım B — Genel (L/U şekilli, eğik) mahal**
```
1) Rektangüler ayrıştırma (motor/rooms.py::rects_in veya ızgara tabanlı maksimal dikdörtgen) -> her dikdörtgende Adım A
   ve ortak kenarlarda adımları hizala (aynı hat boyunca branşman borusu için)
2) Alternatif: sabit ızgara (S_L, S_W) için faz kaydırma (ox, oy) ∈ [0,S)² araması:
   for ox, oy in ince örnekleme:
       pts = ızgara ∩ P.buffer(-D_duvar_min)
       kapsama = union(kare_kapsama(p, S_L/2, S_W/2)) ⊇ P ?   # her nokta S_L×S_W dikdörtgen korur
       skor = len(pts) + λ * kapsanmayan_alan
   en iyi (ox, oy)
3) Kapsanmayan cepler: P.difference(kapsama) -> her cep için polylabel(cep) noktasına ek sprinkler,
   S_min ihlali varsa yakın noktayı ötele
```

**Adım C — Engel kaçınma ve yerel düzeltme**
```
yasak = union(kolon, kiriş_altı_engel.buffer(kural), aydınlatma, menfez).
for p in pts:
    if p in yasak: p = en yakın serbest nokta (yasak dışı, P içi), hareket <= S_max - S_kullanılan
# Lokal optimizasyon (gerekirse): amaç = sayı min, kısıt = kapsama + S_min + D_duvar
# Basit yöntem: ihlal varsa ilgili satır/sütunu bütün olarak kaydır (hizayı bozmadan)
# Daha güçlü: tamsayı programlama (aday noktalar ızgarası -> set cover), PuLP/OR-Tools CP-SAT
```

**Adım D — Boru ağı (ağaç)**
```
Sprinklerleri satırlara grupla -> her satır bir branşman (dikdörtgen ızgarada doğal)
Ana dağıtım hattı = satırlara dik, mahal ortasından veya koridordan (§2 A*)
Hidrolik hesap için ağaç: networkx DiGraph (kaynak -> ana hat -> branşman -> sprinkler)
```

### 4.3 Kaynaklar
- Aralık/duvar mesafesi kural özetleri: https://blog.qrfs.com/214-maximum-and-minimum-sprinkler-distance-rules-part-1-standard-spray-fire-sprinklers/ ,
  https://www.meyerfire.com/uploads/1/6/0/7/16072416/meyerfire_-_sprinkler_-_spacing__2022_.pdf ,
  “Small room rule” SSS: https://nfsa.org/?p=10092
- OH alanında pratik yerleşim yaklaşımı: https://meyerfire.com/daily/best-way-to-layout-sprinklers-in-oh-space
- Dağıtım sistemi tasarım/edit patenti (otomatik sprinkler + boru yerleşimi): https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5808905
- Set cover / tamsayı programlama araçları: OR-Tools CP-SAT (https://developers.google.com/optimization), PuLP.
- Not: Türkiye'de esas standart TS EN 12845 (ve Binaların Yangından Korunması Hakkında Yönetmelik); NFPA değerleri yalnız
  karşılaştırma için.

---

## 5. Etiket yerleştirme (map labeling) ve DXF yazı maskesi

### 5.1 Önerilen yöntem: aday konumlar + öncelikli açgözlü + (isteğe bağlı) benzetimli tavlama
**Adım A — Aday üretimi**
```
for her etiket e (boru çapı, sprinkler tipi, devre adı, mahal adı...):
    nokta etiket (sprinkler, vana): 8 aday konum (Imhof sırası: sağ-üst, sol-üst, sağ-alt, sol-alt, sağ, üst, sol, alt)
    çizgi etiket (boru): hat boyunca t = 0.25,0.5,0.75 ve her birinde üst/alt, yazı açısı = hat açısı
                         (okunabilirlik: açı ∈ (-90°, 90°], aksi halde +180°)
    alan etiket (mahal): polylabel (en uzak iç nokta) + 4 kaydırılmış aday
    leader'lı adaylar: ana konumlar doluysa, hedeften 1-3 birim uzaklıkta halka üzerinde 16 aday + leader çizgisi
    her aday: kutu = ezdxf.text yazı genişliği tahmini (karakter sayısı * yükseklik * genişlik_faktörü veya
              ezdxf.fonts ile ölçüm) + 0.5 mm kenar payı
    ceza(aday) = konum_tercihi + leader_uzunluğu*w + (çizgi üstüne binerse)*w_geo
```
**Adım B — Çakışma grafiği ve açgözlü yerleşim**
```
engeller = STRtree(tüm çizim geometrisi: duvar, boru, sembol)  # etiket bunlara binmesin (ceza)
yerleşik = STRtree dinamik (yeni etiket eklendikçe)
sırala etiketleri öncelikle (mahal adı > ana hat çapı > branşman çapı > sprinkler) ve
    aday sayısı az olanı önce (en kısıtlı önce)
for e in sırala:
    for a in sorted(e.adaylar, key=ceza):
        if not yerleşik.query(a.kutu, predicate="intersects") and geo_çakışma(a) küçük:
            yerleştir(a); break
    else: e -> "yerleşmedi" listesi (leader'lı adaylar ile tekrar, olmazsa ölçeği küçült/kısalt)
```
**Adım C — Benzetimli tavlama (SA) iyileştirmesi** (Christensen–Marks–Shieber)
```
durum = her etiketin seçili aday indeksi
enerji = Σ çakışma_sayısı*W + Σ ceza(aday)
T = T0
repeat:
    e = rastgele çakışan etiket ; a' = rastgele başka aday
    Δ = enerji(yeni) - enerji
    if Δ < 0 or rand() < exp(-Δ/T): kabul
    her N adımda T *= 0.9 ; dur: çakışma yok veya T < Tmin
```
**Adım D — DXF yazı maskesi**
```
# 1) MTEXT arka plan maskesi (en basit, AutoCAD uyumlu):
mt = msp.add_mtext(txt, dxfattribs={...}); mt.set_bg_color("canvas", scale=1.2)   # "canvas" = çizim arka plan rengi (maske); None maskeyi kaldırır
# 2) TEXT için: yazının kutusu kadar WIPEOUT, yazıdan ÖNCE ekle (çizim sırası) veya SORTENTSTABLE ile öne/arkaya:
wo = msp.add_wipeout(vertices=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
doc.set_wipeout_variables(frame=0)        # çerçeveyi gizle
# Not: Boru çizgisini fiziksel olarak kesmek (geometrik boşluk) en taşınabilir yoldur;
#      WIPEOUT bazı görüntüleyicilerde/çıktılarda (PDF dönüşümü) desteklenmeyebilir -> önizleme PDF'te kontrol et.
```
Leader için: ezdxf `add_leader` veya `add_multileader_mtext` (MLEADER) ya da basit LINE+ok bloğu (MTY standardına göre).

### 5.2 Kütüphaneler
- shapely STRtree, **polylabel** (shapely 2'de `shapely.ops.polylabel`), ezdxf `MText.set_bg_color`, `add_wipeout`,
  `add_multileader_mtext`; ezdxf `fonts`/`text2path` ile gerçek yazı genişliği.

### 5.3 Kaynaklar
- Christensen, Marks, Shieber — “An Empirical Study of Algorithms for Point-Feature Label Placement” (SA en iyi sonuç):
  https://dash.harvard.edu/bitstream/1/2032678/2/AnEmpiricalStudy.pdf , MERL raporu: https://www.merl.com/publications/docs/TR94-12.pdf
- MERL TR97-13 (etiket yerleştirme devamı): https://merl.com/publications/docs/TR97-13.pdf
- R `car::pointLabel` (SA/GA uygulaması, referans kod): https://rdrr.io/rforge/car/man/pointLabel.html
- polylabel (pole of inaccessibility): https://cdn.jsdelivr.net/npm/polylabel@2.1.0/README.md
- ezdxf WIPEOUT: https://ezdxf.readthedocs.io/en/stable/dxfentities/wipeout.html ; MTEXT arka plan: https://ezdxf.readthedocs.io/en/stable/dxfentities/mtext.html ,
  MTEXT öğretici: https://ezdxf.readthedocs.io/en/stable/tutorials/mtext.html

---

## 6. Açılımlı kolon şeması ve P&ID otomatik yerleşimi

### 6.1 Kolon şeması (dikey katman = kat): kural tabanlı ızgara yeterli
Kolon şemasında y ekseni zaten kat kotu ile sabit; serbest graf çizimi gerekmez:
```
y(kat) = kat_indeksi * kat_yüksekliği_ölçekli            # bodrum en altta
kolonlar = [K1..Kn] -> x sırası: plandaki x konumuna göre (soldan sağa) veya şaft sırası
x(Kk) = k * kolon_aralığı
# Her kolon: dikey çizgi y(min kat)..y(max kat); her katta daire bağlantı sembolü + branşman yatay kısa çizgi
# Çok hatlı kolon (soğuk/sıcak/sirk): §2D gibi sabit sırayla dikey paralel öteleme
# Yatay toplayıcılar (bodrum tavanı, çatı): kolon tabanlarını birleştiren yatay hat, kesişmesiz olması için
#   kolon sırası = toplayıcı üzerindeki bağlanma sırası (barycenter ile çapraz azaltma, aşağıdaki 6.2 Adım C)
# Etiketler (çap, debi): §5 açgözlü, aday = hat sağı/solu
```

### 6.2 P&ID / kazan dairesi / hidrofor şeması: Sugiyama (katmanlı) çizim
**Adım A — Graf**: düğüm = ekipman (kazan, pompa, boyler, kollektör, genleşme tankı, vana grubu); kenar = boru
(yön = akış). Düğüm boyutu = sembol bloğu kutusu, portlar = blok bağlantı noktaları (sol/sağ/üst/alt).

**Adım B — Sugiyama aşamaları**
```
1) Döngü kırma: dönüş hatları (geri dönüş) döngü yaratır -> geri kenarları ters çevir (DFS veya açgözlü Eades)
   Pratik: "gidiş" kenarları yön belirler, "dönüş" kenarları katmanlamada yok sayılır, sonra eklenir.
2) Katman atama: en uzun yol veya network simplex (dot'un yöntemi) -> soldan sağa akış (kaynak->tüketici)
3) Sahte düğüm: birden fazla katman atlayan kenarlara ara düğüm ekle
4) Çapraz azaltma: katman katman barycenter/median sezgiseli ile sıralama (yukarı-aşağı süpürme, 20-24 tur)
5) Koordinat atama: Brandes–Köpf (düz kenarlar, kompakt)
6) Kenar yönlendirme: ortogonal (ELK "ORTHOGONAL"; Graphviz splines=ortho) -> dirsekli boru gösterimi
```
**Adım C — Uygulama yolları**
```
# Yol 1: Graphviz dot (kurulu): DOT metni üret -> subprocess "dot -Tjson" -> düğüm konumları + kenar noktaları
#   graph [rankdir=LR, splines=ortho, nodesep=..., ranksep=...]; node [shape=box, width=, height=, fixedsize=true]
#   aynı katmana zorlama: {rank=same; Pompa1; Pompa2}
# Yol 2: ELK Layered (en iyi port desteği): elkjs (Node) ile JSON graf -> konumlar;
#   elk.direction=RIGHT, elk.edgeRouting=ORTHOGONAL, portConstraints=FIXED_SIDE (pompanın emiş/basma tarafı sabit)
# Yol 3: Saf Python: grandalf (Sugiyama) -> konumlar; kenarlar §2 ortogonal router ile
# Sonuç: konumları DXF koordinatına ölçekle, ekipmanları MTY bloklarıyla INSERT et, kenarları LWPOLYLINE çiz
```
Kazan dairesi/hidrofor gibi **tekrarlayan topolojiler** için şablon (önceden çizilmiş referans düzen) + parametrik
çoğaltma (n pompa yan yana), otomatik yerleşimden daha okunur sonuç verir; otomatik yerleşim yeni/standart dışı
şemalarda kullanılmalı.

### 6.3 Kütüphaneler ve kaynaklar
- ELK Layered genel bakış (aşamalar, ayarlar): https://eclipse.dev/elk/blog/posts/2025/25-08-21-layered.html
- “The Eclipse Layout Kernel” makalesi: https://arxiv.org/pdf/2311.00533 ; GD 2024 yazılım özeti:
  https://drops.dagstuhl.de/storage/00lipics/lipics-vol320-gd2024/LIPIcs.GD.2024.56/LIPIcs.GD.2024.56.pdf
- elkjs (npm): https://classic.yarnpkg.com/en/package/elkjs ; Go portu (d2lang): https://pkg.go.dev/github.com/d2lang/elk-go
- grandalf (Python Sugiyama): https://pypi.org/project/grandalf/0.7
- Graphviz `dot` (rankdir, splines=ortho): https://dyn.manpages.debian.org/jessie/graphviz/dot.1.en.html ,
  ortogonal kenar tartışması: https://forum.graphviz.org/t/graph-with-orthogonal-edges/2362
- ELK içinde libavoid (sabit konumlu şemada sadece kenar yönlendirme): https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-alg-libavoid.html

---

## 7. Uygulama sırası önerisi (motor için)
1. §1 vektörel mahal çıkarma → `rooms.py` raster sonucu ile karşılaştırıp alan farkı raporu (doğrulama).
2. §2B yön-durumlu A* (bükülme maliyeti) → `router.py`'ye `state=(i,j,yon)` eklemesi; §2D omurga+offset çoklu hat.
3. §3 genel poligon salyangozu (buffer halkaları + Fermat bağlantı) ve L_max ile otomatik devre bölme.
4. §5 açgözlü etiketleyici (STRtree) + MTEXT bg mask; SA sadece yoğun paftalarda.
5. §4 sprinkler ızgarası (dikdörtgen kapalı form + rektangüler ayrıştırma).
6. §6 P&ID için Graphviz `dot -Tjson` köprüsü (kurulu, ek bağımlılık yok).

Uyarı: Bu dosyadaki tüm kural sayıları (L_max, S_max, duvar mesafeleri) örnek/yer tutucudur; projede kullanıcının
seçimleri ve ilgili TS EN standardı esastır, tasarım seçimleri kullanıcıya sorulmadan değiştirilmez.
