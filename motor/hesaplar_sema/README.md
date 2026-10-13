# Şemadan sıhhi hesaplar (kullanıcının HESAPLAR şablonu)

Girdi: kullanıcının açılımlı kolon şeması (DWG → dwg2dxf) + HESAPLAR.dwg (OLE Excel şablonları).
Çalıştırma: `python hesap.py` (Excel) → LibreOffice ile yeniden hesap (`soffice --convert-to xlsx`) → `python dxf_tab.py` (DXF tablolar, MTY-HESAP).

Yöntem (kullanıcı şablonu ile birebir):
1. **Temiz su kritik devre (YB yöntemi):** Etkin basınç = Hidrofor/ŞŞB − (statik kot + akma + sayaç). Özgül kayıp Çizelge 3 plastik boru, YB'ye göre enterpolasyon; DN = şemadaki inç çapı (1/2"=15 … 3"=80). Debi = 0,25√YB.
2. **Blok armatür YB tablosu:** lavabo 0,75 / eviye 1 / rezervuar 0,5 / duş 2,5 / çamaşır 1,5 / şofben 1 (şemadaki MTY değerleri).
3. **Pis su kolon yükleri:** kolon başına adet × SB (klozet 10, duş 7, eviye 4, lavabo 2, süzgeç 2, çamaşır 4, **ızgara 8 SB (Ø100)**). SZ sütunu: bodrumdan pis su çukuruna giden süzgeç/ızgara.
4. **Pis su pompası (her çukur ayrı):** Qww = 0,5√ΣSB; Hm = Hgeo + Hazen-Williams (C=140, DN50) + Σζ·v²/2g, ×1,10; çukur aktif hacmi ≥ Qp/(4·Z), Z=15; motor P = ρgQH/η (η=0,40).
5. **Depo / hidrofor:** depo = 1 günlük ihtiyaç (kullanıcı verir, ör. 16 ton); hidrofor Q = günlük ihtiyaç × 0,60 (kullanma faktörü) → üst standart değer (9,75 m³/h); Hm = bina yüksekliği + kritik devre kaybı + akma + sayaç + 2 mSS → 5'e yuvarla (45 mSS); kritik devre etkin basıncı bu Hm ile kontrol edilir.
6. **Yağmur suyu (her blok):** S = P×0,75 (cm²), A = S/f, D = 1,13√A; D < 7 cm → Ø70, 7–10 cm → Ø100.
7. **DXF düzeni:** her hesap ayrı çerçeve (kare) içinde; yağmur suyu hesabına not yazılmaz.
8. **Teslim kuralı:** tablolarda "yetersiz" yazılmaz; doğru seçilen değerler (pompa Q/H, çukur ölçüsü, çap) yazılır ve kontrol satırı UYGUNDUR olur — kullanıcı bu değerleri projeye işler.

Proje verileri (B1-B2-B3 blok şeması, 2026-10-13): bina yüksekliği 21 m, su deposu 16 m³ (günlük 16 ton esas), her blok çatı alanı 237 m² ve 4 yağmur oluğu, 38 bağımsız birim (şofben sayısı), 3 pis su çukuru (her blokta 1), B1'de 1 adet ızgara (8 SB).
Not: şemadaki MTY dinamik blokları DXF'te '*U' adıyla gelir; `voyap/tes/ulabel.py` ile ham DXF'ten okunur.

## Hesap isterken kullanıcının vermesi gerekenler
1. Kolon şeması DWG (MTY etiketli) + HESAPLAR şablon DWG'si
2. Bina yüksekliği (hidrofor/depo kotundan en üst armatüre, m)
3. Günlük su ihtiyacı / depo hacmi (ton)
4. Mevcut hidrofor ve pis su pompası seçimleri (varsa) ve pis su çukuru adedi/ölçüsü
5. Her blok için çatı alanı (m²) ve yağmur oluğu (iniş) adedi
6. Özel armatürler (ızgara vb.) ve SB değerleri farklıysa bunlar

## Kullanım alanı
- İlk uygulama: İstanbul projesi (B1-B2-B3 blok). Yöntem genel olarak Sakarya projelerinde de kullanılır.
- Kullanıcı yalnız şema gönderebilir: daire sayısı, YB/SB, kolonlar, pompa/hidrofor/depo yazıları ve kat sayısı şemadan okunur.
  Şemada yoksa varsayılanlar: kat yüksekliği 3,00 m; depo = günlük ihtiyaç (daire × 4 kişi × 100 l);
  hidrofor yoksa etkin basınçta şebeke basıncı (ŞŞB) 40 mSS (şablon değeri); yağmur için çatı alanı/oluk adedi şemada/planda yoksa kullanıcıya sorulur.
