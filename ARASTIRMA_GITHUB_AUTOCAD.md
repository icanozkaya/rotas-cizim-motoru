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

## Sıradaki geliştirmeler
1. ACadSharp ile **gerçek blok (INSERT + öznitelik)** yazma: MTY blokları AutoCAD'de patlatılmış değil düzenlenebilir blok olarak gelsin.
2. Örnek düzen (`ornekler/ORNEK_DUZEN.md`): her kat ayrı pafta, sıkı açılımlı şema, rögar şeması, yağmur şeması + hesap kutusu, SIHHİ DETAYLAR paftası, WC aspiratör izometrisi.
3. Yerden ısıtmada meander (gidiş-dönüş) serpantin + hol ısıtma + MTY-ETIKET devre tablosu.
