# 04 — Mekanik tesisat çizim motoru için açık kaynak araçlar

Araştırma tarihi: 2026-10-14. "Son aktivite", klonlanan depolarda `git log -1` tarihidir; klonlanmayanlarda web kaynağından alınmıştır.
Klonlar: `/tmp/claude-0/oss/<repo>` (yalnız okundu, hiçbiri çalıştırılmadı). Bu klasör geçicidir; kalıcı değildir.

**Lisans işaretleri:** [AÇIK] MIT/BSD/Apache/CC0/PD (koda gömülebilir) · [ŞARTLI] LGPL/EPL/CC-BY (kütüphane olarak kullanılabilir, kaynak/atıf şartı var) · [GPL] GPL (koda kopyalama yok, yalnız fikir/algoritma referansı) · [KAPALI] açık kaynak değil.

---

## En işe yarar 8 öğe (öncelik sırasıyla)

| # | Öğe | Lisans | Son aktivite | Motora katkısı |
|---|-----|--------|--------------|----------------|
| 1 | [ezdxf](https://github.com/mozman/ezdxf) | [AÇIK] MIT | 2026-10-10 (yerelde 1.4.4 kurulu) | Motorun DXF çekirdeği zaten bu; `tablepainter`, `importer`, `dimlines`, blok/attrib örnekleri pafta tablolarını ve MTY blok aktarımını doğrudan hızlandırır. |
| 2 | [fluids (CalebBell)](https://github.com/CalebBell/fluids) | [AÇIK] MIT | 2026-09-14 | Darcy-Weisbach/Colebrook ve yüzlerce bağlantı parçası K değeri (dirsek, daralma, vana) ile ısıtma/sıhhi kritik devre basınç kaybı hesabını standart kaynağa bağlar. |
| 3 | [WNTR (USEPA)](https://github.com/USEPA/WNTR) | [AÇIK] Revised BSD | 2026-09-08 | EPANET tabanlı, Hazen-Williams destekli halkalı şebeke çözücüsü; sprinkler/hidrant ağının (looped) hidrolik dengelemesi için hazır motor, `fire_flow` örneği var. |
| 4 | [hvacpy](https://github.com/anirudhsankar/hvacpy) | [AÇIK] MIT | 2026-03-08 | Eşit sürtünme / hız azaltma / statik geri kazanım kanal boyutlandırma + dairesel→dikdörtgen eşdeğer; havalandırma, otopark ve sığınak kanal çaplarının otomatik seçimi. |
| 5 | [networkx](https://github.com/networkx/networkx) (Steiner ağacı) + [python-pathfinding](https://github.com/brean/python-pathfinding) | [AÇIK] BSD-3 / MIT | sürekli / 2026-06-20 | Mimari DXF'ten ızgara çıkarıp A* ile engelden kaçan ortogonal boru güzergâhı, Steiner ağacı ile kolon→cihaz dağıtım ağacı kurma. |
| 6 | [pandapipes](https://github.com/e2nIEE/pandapipes) | [AÇIK] BSD-3 | 2026-10-13 | Sıcaklıklı boru ağı (ısı tüketici, sirkülasyon pompası, eşanjör bileşenleri) ile merkezi ısıtma/kazan dairesi kollektör hidroliğini ağ olarak çözer. |
| 7 | [graphviz (Python)](https://github.com/xflr6/graphviz) + [elkjs](https://github.com/kieler/elkjs) | [AÇIK] MIT (sarmalayıcı) / [ŞARTLI] EPL-1.0 (graphviz ikili) / [ŞARTLI] EPL-2.0 (elkjs) | 2026-07-06 / 2026-10-06 | Kolon şeması, kazan dairesi prensip şeması ve P&ID benzeri şemaların otomatik katmanlı yerleşimi (ELK `layered` + ortogonal kenar); çıkan koordinatlar ezdxf ile MTY bloklarına basılır. |
| 8 | [CoolProp](https://github.com/CoolProp/CoolProp) | [AÇIK] MIT | 2026-10-13 | Su/glikol/hava/soğutucu akışkan özellikleri (yoğunluk, viskozite, cp) — ΔT'li pompa debisi, ısı pompası ve VRF hesaplarında tablo yerine kesin değer. |

Ek olarak not: **dodo (FreeCAD)** içindeki `tablez/*.csv` (DIN/SCH boru, dirsek, flanş PN16, redüksiyon, vana ölçüleri) — [ŞARTLI] LGPL-3; veri tablosu olarak başvuruya çok uygun, ama kopyalanırsa LGPL atfı gerekir.

---

## 1. DXF çekirdeği ve eklentiler

### ezdxf — https://github.com/mozman/ezdxf
- **Lisans:** MIT [AÇIK] · **Son aktivite:** 2026-10-10 · yerel sürüm: 1.4.4
- **Katkı:** Motorun temel DXF okuma/yazma katmanı; aşağıdaki eklenti ve örnekler doğrudan yeniden kullanılabilir.
- **İşe yarar dosyalar (klon):**
  - `src/ezdxf/addons/tablepainter.py` — DXF içinde çizgi+metin tablo üretimi (malzeme listesi, cihaz tablosu, hesap özet tabloları).
  - `src/ezdxf/addons/importer.py` — başka DXF'ten blok/katman/stil aktarımı (MTY blok kütüphanesini proje dosyasına çekmek).
  - `src/ezdxf/addons/dimlines.py` — basit ölçü çizgileri (örnekteki `dont_use_dimline_addons.py` uyarısına dikkat; asıl ölçü için `msp.add_linear_dim`).
  - `src/ezdxf/addons/drawing/` — DXF→PDF/PNG önizleme (matplotlib/PyMuPDF backend); önizleme PDF üretiminde kullanılabilir.
  - `src/ezdxf/addons/odafc.py` — ODA File Converter üzerinden DWG okuma/yazma (ODA kurulumu gerekir; ACadSharp yolumuza alternatif).
  - `src/ezdxf/addons/binpacking.py` — pafta içine detay/kesit yerleştirme için 2B kutu paketleme.
  - `src/ezdxf/addons/iterdxf.py` — büyük mimari DXF'leri belleğe almadan tarama (58 MB tipi dosyalar için).
  - `examples/blocks/block_references_with_attributes.py`, `auto_blockref.py`, `multi_insert.py` — attrib'li blok (vana, radyatör etiketi) basma.
  - `examples/viewports_in_paperspace.py`, `simple_page_setup.py`, `tiled_window_setup.py` — paperspace pafta + viewport kurulumu.
  - `examples/using_lineweight.py`, `using_true_color_and_transparency.py`, `user_data_stored_in_XDATA.py` — MTY katman stili ve elemana hesap verisi (DN, debi) gömme.
  - `examples/addons/table_painter_addon.py` — tablo eklentisinin kullanım örneği.

---

## 2. FreeCAD boru/MEP eklentileri

### Dodo (Flamingo'nun halefi) — https://github.com/oddtopus/dodo
- **Lisans:** LGPL-3.0 [ŞARTLI] · **Son aktivite:** 2024-05-25
- **Katkı:** Boru, dirsek, flanş, redüksiyon, vana ölçü tablolarını (DIN/EN/ASME) CSV olarak veriyor; boru hattı polyline'ından parça dizme mantığı referans alınabilir.
- **İşe yarar dosyalar:** `tablez/Pipe_SCH-STD.csv`, `tablez/Elbow_DIN_1626_90.csv`, `tablez/Flange_DIN-PN16.csv`, `tablez/Reduct_ENxxxxx.csv`, `tablez/Valve_*.csv`, `tablez/roughness.csv`; mantık: `pCmd.py` (boru hattını çizgiden oluşturma, dirsek yerleştirme), `pFeatures.py`, `CPipe.py`.

### Flamingo — https://github.com/oddtopus/flamingo
- **Lisans:** LGPL-3.0 [ŞARTLI] · **Son aktivite:** 2019-03-30 (terk edildi, Dodo'ya taşındı)
- **Katkı:** Tarihî referans; `pipeCmd.py` ve `examples/pipeline.FCStd` boru hattı mantığını gösterir. Yeni iş için Dodo tercih edilmeli.

### FreeCAD-library — https://github.com/FreeCAD/FreeCAD-library
- **Lisans:** parçalar CC-BY-3.0 [ŞARTLI] (atıf zorunlu), kod LGPL · **Son aktivite:** 2026-10-07
- **Katkı:** `HVAC/Ducts/*` (dairesel/dikdörtgen kanal ve bağlantılar), `HVAC/Pipes`, `Hydraulics/Pump` 3B parçaları; DXF sembolü yok denecek kadar az (12 DXF, hiçbiri MEP değil). 3B/IFC hedefi için kaynak, 2B pafta için değil.

### FreeCAD "MEP workbench"
- Bağımsız, bakımlı bir FreeCAD MEP/kanal workbench'i bulunamadı; OSArch forumunda konuşulan çalışmalar ya Dodo ya da Bonsai tarafına kaymış. Not edildi, öğe eklenmedi.

---

## 3. IFC / BIM MEP

### IfcOpenShell (ifcopenshell-python) — https://github.com/IfcOpenShell/IfcOpenShell
- **Lisans:** `ifcopenshell-python` LGPL-3.0 [ŞARTLI]; Bonsai (eski BlenderBIM) GPL-3.0 [GPL] · **Son aktivite:** 2026-10-13
- **Katkı:** Motorun çıktısını ileride IFC'ye (IfcPipeSegment, IfcDuctSegment, IfcDistributionSystem, port bağlantıları) aktarmak ve mimari IFC'den mahal/duvar okumak için tek ciddi açık kaynak.
- **İşe yarar dosyalar:**
  - `src/ifcopenshell-python/ifcopenshell/api/system/` — `add_system.py`, `assign_system.py`, `add_port.py`, `connect_port.py`, `assign_flow_control.py` (sistem şeması = port grafı).
  - `src/ifcopenshell-python/ifcopenshell/util/system.py` — bağlı elemanları port üzerinden dolaşma (kolon şemasını IFC grafından türetmek için).
  - `src/ifcopenshell-python/ifcopenshell/util/shape_builder.py` — profil/ekstrüzyon ile boru/kanal geometrisi.
  - `src/bonsai/bonsai/bim/module/model/mep.py` [GPL] — Bonsai'nin boru/kanal segment ve fitting üretim mantığı (yalnız okunup fikir alınmalı, kopyalanmamalı).

---

## 4. Hidrolik / termodinamik hesap

### fluids — https://github.com/CalebBell/fluids
- **Lisans:** MIT [AÇIK] · **Son aktivite:** 2026-09-14
- **Katkı:** Boru sürtünmesi ve yerel kayıp K değerleri için literatür kaynaklı, testli fonksiyonlar.
- **İşe yarar dosyalar:** `fluids/friction.py` (`friction_factor()` satır ~2096, `Colebrook()` ~345, malzeme pürüzlülükleri), `fluids/fittings.py` (`bend_rounded`, `contraction_sharp`, `diffuser_conical`, vana K'ları), `fluids/piping.py` (nominal boru çapları — ASME ağırlıklı), `fluids/pump.py` (motor gücü/verim), `fluids/safety_valve.py`.
- **Not:** Hazen-Williams fonksiyonu **yok**; sprinkler için WNTR veya kendi H-W fonksiyonumuz gerekir.

### ht — https://github.com/CalebBell/ht
- **Lisans:** MIT [AÇIK] · **Son aktivite:** 2025-12-07
- **Katkı:** Isı transferi (boru ısı kaybı, yalıtım, eşanjör) — sıcak su hattı/boyler ısı kaybı ve yalıtım kalınlığı kontrolü.

### CoolProp — https://github.com/CoolProp/CoolProp
- **Lisans:** MIT [AÇIK] · **Son aktivite:** 2026-10-13
- **Katkı:** Su, glikollü su (inkompresibl karışımlar), nemli hava (HAPropsSI) ve soğutucu akışkan özellikleri; pompa debisi (Q = P/(ρ·cp·ΔT)) ve psikrometrik hesaplarda.

### pandapipes — https://github.com/e2nIEE/pandapipes
- **Lisans:** BSD-3 [AÇIK] · **Son aktivite:** 2026-10-13
- **Katkı:** Isıl+hidrolik boru ağı çözücüsü; çok bloklu merkezi ısıtma/bölgesel ısıtma kollektör dengesi.
- **İşe yarar dosyalar:** `src/pandapipes/component_models/` (`heat_consumer_component.py`, `circulation_pump_pressure_component.py`, `heat_exchanger_component.py`, `pipe_component.py`, `valve_component.py`), `src/pandapipes/std_types/library/Pipe.csv`, `tutorials/` (Jupyter örnekleri).

### WNTR — https://github.com/USEPA/WNTR
- **Lisans:** Revised BSD [AÇIK] · **Son aktivite:** 2026-09-08
- **Katkı:** Hazen-Williams/Darcy-Weisbach seçimli şebeke çözücüsü; sprinkler/hidrant halkalı ağlarında Hardy-Cross yerine Newton çözücü. Ağ, motorun boru grafından `.inp` (EPANET) olarak üretilebilir.
- **İşe yarar dosyalar:** `wntr/sim/models/constraint.py` (`piecewise_hazen_williams_headloss_constraint`), `wntr/sim/hydraulics.py`, `wntr/epanet/util.py` (birim dönüşümleri), `examples/fire_flow.py` ve `examples/fire_flow_tutorial.ipynb` (yangın debisi senaryosu).

### EPANET — https://github.com/OpenWaterAnalytics/EPANET
- **Lisans:** MIT [AÇIK] (web kaynağı; klonlanmadı) · **Son aktivite:** aktif (OpenWaterAnalytics)
- **Katkı:** WNTR'nin altındaki C çözücü; `.inp` formatı motor çıktısı için ortak değişim formatı olabilir.

### SPRINKLE — https://sprinkle.sourceforge.net/
- **Lisans:** GPL [GPL] · **Son aktivite:** belirtilmemiş (eski, C + glib-1.2)
- **Katkı:** Hazen-Williams tabanlı NFPA 13/13R sprinkler hesap çözücüsü; yalnız algoritma referansı (`solver.c` notları). GitHub'da bakımlı, açık lisanslı Python sprinkler hesap deposu **bulunamadı** — en gerçekçi yol: kendi H-W + K-faktörü (Q = K√P) fonksiyonlarımız + ağ çözümü için WNTR.

### pipedream — https://github.com/mdbartos/pipedream
- **Lisans:** GPL-3.0 [GPL] · **Son aktivite:** 2024-05-30
- **Katkı:** Dinamik açık kanal/kanalizasyon hidroliği; yağmur suyu ve pis su ana hat davranışı için yalnız referans.

---

## 5. Kanal (duct) boyutlandırma

### hvacpy — https://github.com/anirudhsankar/hvacpy
- **Lisans:** MIT [AÇIK] · **Son aktivite:** 2026-03-08 (PyPI 0.4.1)
- **Katkı:** `DuctSizer(method="equal_friction" | "velocity_reduction" | "static_regain")`, standart çapa yuvarlama ve dikdörtgen eşdeğer.
- **İşe yarar dosyalar:** `hvacpy/equipment/_duct.py` (`_equal_friction_diameter`, `_static_regain_diameter`, `_rectangular_equivalent`, `_next_std_size_mm`), `tests/test_duct_sizing.py` (doğrulama değerleri).
- **Not:** Standart çap serisi ve hava yoğunluğu sabitleri TS/EN serimize göre kontrol edilmeli.

### hvac-pressure (hvac-fitting-loss) — https://github.com/JeremySimonneau/hvac-fitting-loss
- **Lisans:** MIT [AÇIK] · **Son aktivite:** 2026-03-25 (PyPI 0.1.3)
- **Katkı:** ASHRAE 2009 fitting kayıp katsayıları (dirsek, T, geçiş, damper) ile kanal hattı statik basınç raporu — fan basıncı seçimi.
- **İşe yarar dosyalar:** `hvac_pressure/data/ashrae_tables.py`, `hvac_pressure/interpolation.py`, `hvac_pressure/system.py`, `hvac_pressure/core.py`.

---

## 6. Boru güzergâhı (routing)

### networkx — https://github.com/networkx/networkx
- **Lisans:** BSD-3 [AÇIK] · **Son aktivite:** sürekli aktif (yerelde kurulu)
- **Katkı:** Izgara grafında `astar_path`, `approximation.steiner_tree` (kolon/şaft → tüm ıslak hacimler ağacı), `minimum_spanning_tree`; mimari DXF'ten üretilen engel ızgarası üzerinde çalışır.
- **Yerel yol:** `/usr/local/lib/python3.13/dist-packages/networkx/algorithms/approximation/steinertree.py`.

### python-pathfinding — https://github.com/brean/python-pathfinding
- **Lisans:** MIT [AÇIK] · **Son aktivite:** 2026-06-20
- **Katkı:** Izgara üzerinde A*, Dijkstra, bi-A*, IDA*; köşegen kapatılarak ortogonal güzergâh, dönüş cezası için özelleştirilebilir.
- **İşe yarar dosyalar:** `pathfinding/finder/a_star.py`, `pathfinding/finder/finder.py` (maliyet/heuristic kancası), `pathfinding/finder/msp.py` (çok noktalı en kısa yol).

### libavoid (Adaptagrams) — https://www.adaptagrams.org/documentation/libavoid.html
- **Lisans:** LGPL-2.1 [ŞARTLI] · **Son aktivite:** web kaynağı (ELK 2022'de entegre etti)
- **Katkı:** Engelden kaçan ortogonal bağlantı yönlendirme, minimum kıvrım + çakışan hatları ayırma (nudging); şema ve tek hat çizimlerinde paralel boruları düzgün aralıklamak için en iyi algoritma referansı (C++, Python bağlaması resmi değil).

### Akademik referanslar (kod yok)
- IAARC 2022 "Development of Auto Route System for MEP Pipe Design" — https://www.iaarc.org/./publications/fulltext/173_Development_of_Auto_Route_System_for_MEP_Mechanical__Electrical_and_Plumbing_Pipe_Design_in_Construction.pdf
- "Optimal Pipe Routing Techniques in an Obstacle-Free 3D Space" (SciTePress 2020) — https://scitepress.org/Documents/2020/89233/
- "Improved multi-search strategy A* for 3D pipe routing" — https://research.mpu.edu.mo/en/publications/improved-multi-search-strategy-a-algorithm-to-solve-three-dimensi/
- Bakımlı, açık lisanslı bir MEP boru güzergâh deposu bulunamadı; networkx + pathfinding ile kendi modülümüz önerilir.

---

## 7. Şema / P&ID otomatik yerleşim

### graphviz (Python sarmalayıcı) — https://github.com/xflr6/graphviz
- **Lisans:** sarmalayıcı MIT [AÇIK]; Graphviz ikilisi EPL-1.0 [ŞARTLI] · **Son aktivite:** 2026-07-06
- **Katkı:** `rankdir=TB`, `splines=ortho` ile kolon şeması/prensip şeması yerleşimi; `-Tjson` çıktısındaki düğüm koordinatları ezdxf'e aktarılır. Sistemde `dot` ikilisi gerekir.

### elkjs — https://github.com/kieler/elkjs
- **Lisans:** EPL-2.0 [ŞARTLI] · **Son aktivite:** 2026-10-06
- **Katkı:** ELK `layered` algoritması — port kısıtlı (pompa giriş/çıkış yönü sabit) ve ortogonal kenarlı yerleşim; P&ID'e Graphviz'den daha uygun. Node.js alt süreci olarak JSON giriş/çıkışla çağrılır.

### pandid — https://github.com/Alpha9463/pandid
- **Lisans:** [KAPALI] PolyForm (depoda "Strict", PyPI'de "Small Business" + semboller Apache-2.0) — OSI onaylı değil · **Son aktivite:** 2026-10-03
- **Katkı:** Topolojiden koordinatsız P&ID: kısıt çözümlü ekipman yerleşimi + ortogonal A* hat çizimi. Kod alınmamalı; yalnız yaklaşım referansı ("akış omurgası", `pin()`/`via()` geçersiz kılma).

---

## 8. DXF sembol / blok kütüphaneleri

| Kaynak | Lisans | Format | Not |
|---|---|---|---|
| [draftsperson.net EN ISO 10628 P&ID](https://blocks.draftsperson.net/download/en-iso-10628-pid-symbol-library/) | [AÇIK] "kişisel ve ticari kullanım serbest, atıf gerekmez" (CC0 değil, site lisansı) | DWG (150 sembol, 11 kategori) | Pompa/vana/eşanjör sembolleri; ACadSharp/LibreDWG ile DXF'e çevrilip MTY katmanına uyarlanabilir. |
| [draftsperson.net Piping & Plumbing Symbols](https://blocks.draftsperson.net/download/piping-and-plumbing-symbols-list/) | [AÇIK] aynı site lisansı (sayfada doğrulanmalı) | DWG | Sıhhi tesisat sembolleri. |
| [FreeCAD-library](https://github.com/FreeCAD/FreeCAD-library) | [ŞARTLI] CC-BY-3.0 | FCStd/STEP (MEP DXF yok) | 3B kanal/boru parçaları. |
| Wikimedia Commons ISO 10628-2 SVG'leri (ör. [piston pompa](https://de.wikipedia.org/wiki/Datei:Pump,_reciprocating_piston_type_(ISO_10628-2).svg)) | dosya bazında kontrol edilmeli | SVG | SVG→DXF dönüşümüyle sembol çizimi için referans. |
| [designscad.com HVAC Symbols](https://designscad.com/downloads/hvac-symbols-and-equipment/) | [BELİRSİZ] lisans belirsiz | DWG | Kullanmadan önce şartlar okunmalı. |
| [PIDcircuitTikZ](https://github.com/umit-iace/PIDcircuitTikZ) / CTAN chempid | LaTeX (LPPL tipik) | TikZ | Sembol geometrisi referansı; doğrudan DXF değil. |

**Sonuç:** CC0/MIT lisanslı, MEP odaklı hazır DXF blok kütüphanesi bulunamadı. Mevcut `ROTAS_2_MTY_BLOKLARI` seti ana kaynak kalmalı; eksik P&ID sembolleri draftsperson ISO 10628 setinden dönüştürülebilir.

---

## Önerilen entegrasyon sırası
1. `fluids` + kendi Hazen-Williams fonksiyonu → kritik devre / sprinkler hesap modülü (Excel çıktısı mevcut şablona).
2. `hvacpy` mantığı (MIT, kopyalanabilir) → sığınak/otopark/genel havalandırma kanal çapı seçimi; `hvac-pressure` → fan statik basıncı.
3. `networkx` Steiner + `pathfinding` A* → mimari DXF ızgarasında yatay dağıtım güzergâhı önerisi (kullanıcı onayıyla, tasarım seçimlerine dokunmadan).
4. ELK/Graphviz → kolon şeması ve kazan dairesi prensip şeması yerleşimi; ezdxf + MTY blokları ile basım.
5. WNTR → halkalı yangın/hidrant ağı doğrulaması.
6. İleride: ifcopenshell-python ile IFC dışa aktarma.
