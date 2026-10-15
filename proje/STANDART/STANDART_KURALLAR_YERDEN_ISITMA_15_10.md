# YERDEN ISITMA — kullanıcı kaydı 15.10.2026 22:38 (onaylı dosya + notlar)

Kullanıcı: "Bu yaptığımız dosya çok güzel, notlarım ile beraber kayıt altına alalım." Bu dosyada değişiklik YAPILMAZ;
aşağıdakiler SONRAKİ dosyalarda uygulanır.

## Onaylı referans
- `STANDART_YERDEN_ISITMA_KOLLEKTORLU_15_10.dxf` + `STANDART_ISI_KAYBI_YERDEN_HESAP_15_10.xlsx`
  (üretim: `YI_HOL_YOK=1 YI_ISI_KAYBI=1 motor/yerden2/yerden.py` + `kullanici_birlestir.py`, bkz. proje/yerden_isitma_15_10/BENIOKU.md).
- Petek (radyatör) ve yerden ısıtma çizim tarzı BU ŞEKİLDE TAMAM.
- Kollektör bağlantıları, holden geçen ayaklar, mahal numaraları (Z01.., 101.., 201..) bu dosyadaki gibi.
- Serpantin uçları kollektöre / kapıya uzak kalırsa bu dosyadaki gibi düzeltilir (kapıdan uca ayak şeridi, uçlar kapı
  köşesine) — kullanıcı: "mükemmel".
- Holde (antre-koridor) yerden ısıtma yapılmaz; ayaklar holden geçer.

## Hesap kuralları
- Yerden ısıtma boru verimi: boru metresi başına 35 kcal/h (devre ısıl gücü = 35 kcal/h × L; 100 m → 3500 kcal/h —
  kullanıcı 22:44 teyit etti, "350" yazım hatasıydı).
- 80 m'yi geçen devre 2'ye bölünür (gerekirse daha fazla).
- Isı kaybı hesabı ayrıca yapılır (kullanıcının ZEMİN/1 NK sayfa düzeni, kat yüksekliği projeden; verilmezse sorulur).
- Sakarya = 3. BÖLGE (kullanıcı). Teknik rapor / kapak / ısı kaybı sayfalarında bölge 3 yazılır.
- Proje bilgileri olan her yer (kapak, teknik rapor, antet: ada/parsel, yapı sahibi, kat adedi, alan, tarih...) gözden
  kaçırılmadan doldurulur.
- Hazırlayan: Can Özkaya "TEKNİK RESSAM" olarak yazılır (Makina Mühendisi DEĞİL; proje müellifi değil).

## Çizim kuralları
- Yazı fontları bozulmaz (kullanıcının blok/yazı stilleri birebir).
- Kombi duvar üstüne binmez; HER dairede kombi olur (bu dosyada bazı dairelerde kombi yok / duvar üstünde — düzeltilecek).
- Projeye kombi kesitleri (kombi bağlantı detayı/kesiti) eklenir.
- MERKEZİ SİSTEM denildiğinde: kombi yerine bina kazan dairesinden, daire girişinde kalorimetreli tasarım.

## Bu dosyada görülen hatalar (sonraki dosyada motor düzeltilecek)
1. Zemin/1. kat sol mutfak (ör. 101) serpantini bozuk — sağdaki mutfak (113) düzgün
   (görsel: kutuphane/arastirma/geri_bildirim/RED_yerden_sol_mutfak_serpantin_bozuk_15_10.png).
2. Bazı dairelerde kombi duvar üstüne binmiş, bazılarında kombi yok; 2. kat D7 kombi–kollektör hattı yok.
3. Teknik raporda "2. bölge" ve hazırlayan unvanı — 3. bölge / teknik ressam olacak.

## Kullanıcı kaydı 15.10.2026 22:44
- **TÜM DOSYALARDA İLK ÖNCELİK: MİMARİYİ OKUMAK VE KOLON HATLARINI BELLİ ETMEK** (pis su / temiz su / yağmur kolonları,
  ıslak hacimler, betonarme kolonlar, şaftlar). Sonra diğer okuma ve tasarım adımlarına geçilir.
- U değerleri İZODER sisteminden (TS 825:2024, izoder.org.tr/ts825/<il>.pdf) alınır ve AŞILMAZ. Sakarya 3. bölge:
  dış duvar 0,40 · tavan/çatı 0,30 · taban/döşeme 0,35 · pencere/kapı 1,8 W/m²K (g ≤ 0,45);
  yüksek camlı (düşey yüzeyin ≥ %60'ı cam) yapıda 0,30 / 0,23 / 0,26 / 1,6.
  Projenin İZODER hesabı gelirse oradaki değerler kullanılır, sınırı aşan değer sınıra indirilmez — yalıtım revizesi
  için kullanıcıya bildirilir. Kod: `motor/yerden2/isi_kaybi.py` (TS825_2024, BOLGE=3, u_sec()).
- 15.10 onaylı dosyada şablon U değerleri (duvar 0,479, pencere 2,40) kullanıldı — 3. bölge sınırlarının üstünde;
  o dosya kullanıcı isteğiyle değiştirilmedi, sonraki dosyalarda yukarıdaki değerler kullanılır.
