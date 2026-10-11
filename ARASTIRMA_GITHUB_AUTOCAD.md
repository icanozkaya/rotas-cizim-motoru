# GitHub'da AutoCAD / DWG araştırması ve motora katkısı (11.10.2026)

| Kaynak | Ne işe yarar | Durum |
|---|---|---|
| [DomCR/ACadSharp](https://github.com/DomCR/ACadSharp) (MIT, C#) | DWG/DXF okuma-yazma; DWG yazma AC1014–AC1032 (R2018 dahil), katman, blok, yazı stili | **Motora eklendi**: `araclar/rotasdwg` ile DXF → AutoCAD 2018 DWG. Türkçe yazılar, kalem genişlikleri ve katmanlar korunuyor; LibreDWG ile çapraz okunarak doğrulandı (20 748 / 20 748 varlık). Eski mkdwg (R2000) yedek olarak kaldı. |
| [ezdxf](https://github.com/mozman/ezdxf) (Python) | DXF okuma/yazma, blok içe aktarma (importer), çizim/PDF önizleme | Zaten çekirdekte. Örnek dosyadaki 78 MTY bloğu `importer` ile kütüphaneye çekildi (`ORNEK__*.dxf`). |
| LibreDWG (GNU) | DWG → DXF okuma | Yamalı derleme kullanılıyor (R2004 LZ77, tutamaç, ANSI_1254 yamaları). |
| [mazerab/design.automation-dwgquery-arxapp](https://github.com/mazerab/design.automation-dwgquery-arxapp), [gileCAD/AutoCAD-Csharp-Project-Template](https://github.com/gileCAD/AutoCAD-Csharp-Project-Template), [luanshixia/AutoCADCodePack](https://github.com/luanshixia/AutoCADCodePack) | AutoCAD .NET eklenti şablonları ve örnekleri | İleride: AutoCAD içinde çalışan ROTAŞ eklentisi (CadGPT hedefi) için başlangıç şablonu. |
| [pyautocad](https://pyautocad.readthedocs.io/) / pyacadcom | Windows'ta açık AutoCAD'i Python'dan COM ile yönetme | Kullanıcının kendi bilgisayarında AutoCAD'e doğrudan çizim için seçenek (bulutta çalışmaz). |
| [Lee Mac programları](https://lee-mac.com/programs.html) | Olgun AutoLISP araçları (blok/öznitelik, yazı, katman) | Kullanıcının AutoCAD'inde yardımcı LISP'ler için referans. |
| [marcin-filipiak/cpp_SpiralFloorHeating](https://github.com/marcin-filipiak/cpp_SpiralFloorHeating) | Yerden ısıtma salyangoz yerleşimi | Kendi `spiral3.py` + `gufh.py` (kesişmesiz bağlantı optimizasyonu) daha gelişmiş; örnek dosyadaki meander düzeni eklenecek. |

## 2. tur tarama (11.10.2026 akşam) — GitHub konu sayfaları: autocad, autolisp, dxf, mep, hvac, plumbing

GitHub arama servisi bu ortamda kapalı olduğu için konu sayfaları yıldıza göre tarandı; 12 depo klonlanıp kodları ve lisansları incelendi.

| Kaynak | Lisans | Ne alındı / ne öğrenildi |
|---|---|---|
| [psychrometrics/psychrolib](https://github.com/psychrometrics/psychrolib) | MIT | **Motora eklendi** (`motor/p2/psychrolib.py`). Klima ısı kazancında dış/iç nem oranları artık ASHRAE denklemleriyle hesaplanıyor (Adapazarı 34/24 °C → 0,01472 kg/kg; 26 °C %50 → 0,01054 kg/kg). |
| [TomLXXVI/python-hvac](https://github.com/TomLXXVI/python-hvac) | MIT | Yöntem uyarlandı (`motor/p2/ghidrolik.py`): membranlı genleşme tankı boyutlandırma, Churchill sürtünme katsayısı. Hardy-Cross ağ çözümü, pompa eğrisi, EN 12831 tarzı ısı kaybı modülleri ileride büyük kazan dairesi/kolon şebekesi hesapları için referans. |
| [egmalt/house-planner](https://github.com/egmalt/house-planner) | MIT | Yöntem uyarlandı: yerel kayıp çarpanı 1,3, kollektör+vana 5 kPa, 200/500 m kangal paketleme. Serpantin üretimi (`spiralRings`, `snakeLines`, clipper ofset) meander yerden ısıtma çizimi için referans. |
| [beastt1992/autocad-batch-plot](https://github.com/beastt1992/autocad-batch-plot) | MIT | **Depoya eklendi** (`araclar/autocad_lisp/batch-plot`). Motor DWG'lerine her pafta için çizilmeyen `ROTAS_PAFTA` bloğu konuldu → AutoCAD'de `BPDF` ile tüm paftalar tek tıkla PDF. |
| [hassin070/MEP-AUTOCAD-Scripts](https://github.com/hassin070/MEP-AUTOCAD-Scripts) | Apache-2.0 | **Depoya eklendi**: `TOTLEN` (boru metrajı), `TAGDEVICES` (cihaz numaralama), `SPRINKLERLAYOUT`. |
| [chuongmep/OpenMEP](https://github.com/chuongmep/OpenMEP) | MIT | Dynamo/Revit ağırlıklı; AutoCAD tarafı COM ile okuma. pyautocad yolu aynı işi görüyor, alınmadı. |
| [red1oon/mep_engineering](https://github.com/red1oon/mep_engineering) | GPL-3.0 | Kod alınmadı (kopyalayıcı lisans). Fikir: örneklenmiş noktalar üzerinde A* + dik açıya çevirme ile otomatik boru güzergâhı — ileride kat planında otomatik tesisat güzergâhı için. |
| DerekEubanks Revit pis su / yağmur çap eklentileri | MIT | Yalnız tablo yapısı incelendi; IPC (ABD) değerleri TS EN 12056 ile uyuşmuyor ve hatalı, alınmadı. |
| marcin-filipiak/cpp_SpiralFloorHeating | GPL-3.0 | Alınmadı; kendi `spiral3`/`gufh` modülümüz daha kapsamlı. |
| altsun/My-Lisps, Mr-Saxobeat/turn-or-break-line | lisanssız | Alınmadı (izin yok); fikir listesi olarak kullanıldı (boru kesme/köprü zaten motorda `xcheck.hops`). |

### Bu turda motora giren geliştirmeler
1. **Gerçek blok (INSERT + öznitelik):** `mtyblk.insert` her bloğu kayıtlarıyla işaretliyor; çakışma temizliğinden sonra kayıtları aynen duran bloklar DWG/DXF'e gerçek blok olarak yazılıyor (Sinem Turhan 218, Tuncay Bulut 265 blok; geometri eski çizimle birebir aynı, öznitelikler DWG'de korunuyor). Temizlikte çizgisi kesilen bloklar görünüm bozulmasın diye patlatılmış kalıyor.
2. **Yerden ısıtma daire hidroliği** (`ghidrolik.py`): kombi pompası basma kontrolü, kapalı genleşme tankı (kombi içi 8 l yeterli mi), PEX kangal metrajı; paftadaki ısıtma çizelgesine ve Excel'e yeni `KOMBİ-POMPA-GENLEŞME` sayfası olarak eklendi.
3. **Psikrometri** ile klima gizli ısı hesabı.
4. **BPDF uyumlu pafta sınırları** (`ROTAS_PAFTA`).
5. Hata düzeltmesi: "BANYO-WC" mahalleri döşeme sıcaklığı kontrolünde banyo sınırı (33 °C) ile değerlendiriliyor.

## Sıradaki geliştirmeler
1. ~~Gerçek blok yazma~~ (yapıldı). Kalan: temizlikte kesilen blokların (PVC çatal, şema armatürleri) da blok kalması için kesmeyi blok yerine boruda yapmak.
2. Örnek düzen (`ornekler/ORNEK_DUZEN.md`): her kat ayrı pafta, sıkı açılımlı şema, rögar şeması, yağmur şeması + hesap kutusu, SIHHİ DETAYLAR paftası, WC aspiratör izometrisi.
3. Yerden ısıtmada meander (gidiş-dönüş) serpantin + hol ısıtma + MTY-ETIKET devre tablosu.
