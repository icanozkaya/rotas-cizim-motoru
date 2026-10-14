# Doğalgaz iç tesisat modülü (DENEME, 14.10.2026)

Bu modül konut doğalgaz iç tesisatının hesabını yapar ve izometrik kolon şemasını çizer. Kaynak: `kutuphane/arastirma/07_ISITMA_DOGALGAZ.md` §6.

**AKSAGAZ (Sakarya) şartnamesi doğrulanamadı.** Sınır değerler ve eşzamanlılık bu yüzden "AKSAGAZ şartnamesiyle teyit edilecek" notuyla verilir. Bu not hem DXF'te hem Excel'de yer alır.

## Çalıştırma
```
python3 motor/deneme/dogalgaz/dogalgaz.py motor/deneme/dogalgaz/test_z4_10daire.json proje/denemeler/dogalgaz [--onizleme]
```
- Çıktı: `<ad>_izometrik_kolon_semasi_R2.dxf` (R2018/AC1032) ve `<ad>_hesap.xlsx` (formüllü).
- `--onizleme` verilirse PNG önizleme de üretilir. PNG `$ONIZLEME_DIR` klasörüne yazılır (varsayılan `/tmp`) ve depoya konmaz.
- Konsolda iki kontrolün sonucu yazar:
  - çap seçiminin sınırları sağlayıp sağlamadığı;
  - geometri kontrolü: boru-boru kesişmesi, sembolün başka boruyla çakışması, yazı-yazı çakışması.

## Dosyalar
- `hesap.py` — ağı ve hesabı kurar.
  - Ağ sırası: servis kutusu → bina bağlantı hattı → ana kesme vanası → sayaç kollektörü → sayaç bağlantıları → G4 sayaçlar → daire hatları → kombi ve ocak hatları.
  - Hesap: eşzamanlılık f(n), bağımsız bölüm başına en az 3,5 m³/h, cihaz debisi Q = kW·860/(Hu·η).
  - Sürtünme kaybı Renouard formülüyle hesaplanır: ΔP_R = 23200·d·L·Q^1,82·D^-4,82.
  - Ayrıca yerel kayıp ΔP_Z = 3,97e-3·Σξ·V² ve yükseklik etkisi ΔP_H = −0,049·h hesaplanır.
  - Hız kontrolü: ≤ 6 m/s.
  - Çap seçimi: önce hıza ve en küçük çapa göre yapılır. Sonra kritik devre sınırları sağlanana kadar, en çok kayıp veren parça büyütülür. Sınırlar:
    - servis kutusu → sayaç vanası ≤ 1,0 mbar
    - sayaç → cihaz ≤ 0,8 mbar
    - toplam (sayaç hariç) ≤ 1,8 mbar
  - Boru: TS EN 10255 orta seri çelik.
- `cizim.py` — 30° izometrik şemayı ve DXF'teki tabloları çizer.
  - Boru etiketi üç satırdır: `Q m³/h / L m / DN [hat no]`. Etiketler boş yere otomatik yerleşir ve altlarına WIPEOUT maskesi konur. Etiket uzağa düşerse boruya kılavuz çizgi çizilir.
  - Her cihazın yanında kW, m³/h ve cihaz numarası yazar.
  - Vanalar V-01…, sayaçlar S-xx, kombiler K-xx, ocaklar O-xx, regülatör R-01 olarak numaralanır ve ekipman listesine girer.
  - DXF'te ayrıca hesap tablosu, kritik devre kontrol tablosu, lejant ve "...yapılacaktır." biçiminde notlar bulunur.
- `semboller.py` — sembolleri hazırlar.
  - R2: MTY bloğu yok. Gaz vanası `ROTAS-DG-KURESEL-VANA` (papyon + küre + kol, CAP özniteliği görünmez), `ROTAS-DG-ESNEK`, `ROTAS-DG-KOMBI` (gövde + eş eksenli baca) saf geometridir.
  - Diğerleri `03_SEMBOLLER.md` §7 geometrisiyle çizilir:
    - `ROTAS-DG-SAYAC`: izometrik ön yüzlü G4 sayaç
    - `ROTAS-DG-REGULATOR`: içi dolu papyon, diyafram kubbesi ve kesikli algılama hattı
    - `ROTAS-DG-OCAK`: 4 gözlü ocak
- `excel.py` — Excel dosyasını yazar. Sayfalar: PARAMETRE (adlandırılmış hücreler), BORU, ESZAMANLILIK, CIHAZLAR, CAP_HESABI, KONTROL, HAVALANDIRMA.
  - Debi, hız, kayıplar, kümülatif değerler ve kontroller formüldür; koşullu biçim uygulanır.
  - DN değerini değiştirmek yeterlidir; gerisi yeniden hesaplanır.
  - LibreOffice ile yeniden hesaplandığında sonuçlar Python sonuçlarıyla aynı çıkıyor (fark < 1e-13).
- `test_z4_10daire.json` — DENEME girdisi: Z+4 kat, katta 2 daire, her dairede 24 kW kombi ve 1,6 m³/h ocak, sayaçlar zemin girişte toplu.

## JSON parametreleri
- `gaz`, `sinirlar`, `eszamanlilik`: eşzamanlılık katsayıları `tablo` alanına `{"n": f}` biçiminde girilir. Tablo boşken f = 1,0 alınır.
- `daire_tipi.cihazlar`: kW veya katalog debisi.
- `daireler`: no, kat, taraf (sol/sag).
- `geometri`:
  - `L_*` ve `h_*`: gerçek uzunluk ve kot farkı (m). Hesapta ve etikette bu değerler kullanılır.
  - `xi_*`: Σξ.
  - `sema_*`: ölçeksiz şema koordinatı (cm).
  - Şemada sol daire kolonları kata göre artan, sağ daire kolonları azalan sırada dizilir; böylece dallar kesişmez.

## Sınırlar / yapılmayanlar
- Yalnız konut tipi akış desteklenir: toplu sayaç ve her daireye ayrı hat. Kat sayaçlı ortak kolon ve merkezi kazan dairesi yoktur.
- Kat planı (mimari üzerinde hat) çizilmez; yalnız izometrik kolon şeması, tablolar ve Excel üretilir.
- Eşzamanlılık tablosu, gaz vanası sembolü ve cihaz debileri AKSAGAZ ile teyit edilmelidir.
  - Gaz vanası açık papyon + küre ile çizildi; bazı şartnamelerde gaz vanası içi dolu papyonla gösterilir (regülatör içi dolu papyondur).
- Sayaçta oluşan basınç kaybı hesaba katılmaz (şartname "sayaç hariç" der). Test nipeli ve kolon havalandırması çizilmez.
- Eşzamanlılık f = 1,0 alındığı için ana hat debisi 43,8 m³/h çıkar ve DN50–DN65 seçilir. AKSAGAZ tablosu girildiğinde çaplar küçülür.

## R2 revizyonu (14.10.2026 (B) talimatı)
- MTY bloğu / katmanı / yazı stili (`MTY-VANA`, `MTY-TEFRIS`, `MTYCAPLT`) tamamen kaldırıldı; `/tmp/claude-0/blk` gerekmez.
- Lejant otomatik: `Cizim.lejant()` modeldeki INSERT'leri sayar (lejant katmanı `ROTAS-DOGALGAZ-LEJANT` hariç), yalnız kullanılan
  ROTAS-DG-* sembollerini ADET sütunuyla, boruyu toplam metreyle yazar; tanımsız blok varsa hata verir.
- `dogalgaz.py` kaydettikten sonra `mty_kontrol()` çalıştırır (blok/katman/stil/yazı/öznitelik); sonuç konsolda.
- Test çıktısı: boru kesişmesi 0, yazı çakışması 0, bütün boru etiketleri yerleşti, MTY 0. Excel değişmedi.
