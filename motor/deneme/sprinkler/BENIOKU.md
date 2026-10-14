# Deneme modülü: sprinkler (14.10.2026)

Mahal poligonu ve tehlike sınıfından sprinkler başlıklarını otomatik yerleştirir. Ardından ortogonal boru ağacını kurar, çapları ROTAŞ/Aselsan tablosuyla seçer ve TS EN 12845 hidrolik hesabını yapar. Sonuç tek bir DXF dosyasıdır (R2018/AC1032). Dosyada plan, etiketler, hidrolik en uzak alan, hesap özeti, düğüm tablosu, ekipman listesi, lejant ve notlar bulunur.

## Çalıştırma
```
python3 motor/deneme/sprinkler/ornek_uret.py                       # deneme girdilerini yazar
python3 motor/deneme/sprinkler/calistir.py motor/deneme/sprinkler/ornek_girdi/kat_ofis_oh1.json \
        proje/denemeler/sprinkler/kat_ofis_oh1_sprinkler.dxf [--png /scratch/onizleme.png]
```
Program sonuçların özetini ve kontrol raporunu yazdırır. Raporda `HATA: 0` görünmelidir.

## Dosyalar
| Dosya | Görev |
|---|---|
| `kurallar.py` | Tehlike sınıfı tablosu (yoğunluk, alan, süre, başlık başına alan, S, K, Pmin), ROTAŞ DN tablosu, EN 10255 iç çapları, eşdeğer boylar, Hazen-Williams. Kaynak: `06_YANGIN.md` |
| `yerlesim.py` | Dikdörtgen mahalde eşit bölmeli ızgara kurar (05 §4 Adım A). Değerler: S ≤ Smax, duvara ≤ S/2 ve ≤ 2 m, başlıklar arası ≥ 2 m, başlık başına alan ≤ Amax. Betonarme kolona çarpan satır veya sütun hizası bozulmadan kaydırılır (Adım C). |
| `ag.py` | Kolon (riser) dağıtım mahallinin duvar köşesine konur; köşede betonarme kolon varsa duvar boyunca kaydırılır. Koridor ana hattı eksende gider, koridor başlıkları doğrudan ana hat üzerindedir. Her mahal kapıdan beslenir: ana hattan kapı açıklığı içinden iner, duvar ile ilk branşman arasında duvara paralel bir bacak yapar ve mahal dağıtım borusuna bağlanır. Branşmanlar kapı duvarına paraleldir ve ortadan beslenir. Çap, aşağı akıştaki başlık sayısından README tablosuyla seçilir. |
| `hidrolik.py` | Q = K·√P, HW C=120, dirsek/te eşdeğer boyu. Ağaç üzerinde kesin çözüm yapılır (sabit nokta yinelemesi). İşletme alanı dikdörtgen pencerelerden seçilir: uzun kenar branşmana paralel ve ≥ 1,2·√A. Bütün aday pencereler hesaplanır ve kolonda en yüksek basıncı isteyen pencere "hidrolik en uzak alan" olur. Pompa basıncı = kolon basıncı + besleme kaybı + vana kaybı + statik yük. Depo hacmi = Q·t. |
| `semboller.py` | İzlenebilir kelebek vana: MTY bloğu (`/tmp/claude-0/blk`; yoksa tar'dan çıkarılır), patlatılmaz, CAP özniteliği vardır. Sprinkler (sarkık/dik), akış anahtarı: Aselsan 02-Yangın lejantı (`motor/voyap/asel_sym.pkl`, yalnız okunur). Kolon sembolü VOYAP'taki gibidir. |
| `cizim.py` | DXF çizimini yapar. Katmanlar `ROTAS-` önekli, birim cm, ölçek 1/50, yazılar Türkçe. Etiketler engel kutularıyla çakışmadan yerleştirilir; olmazsa kılavuz çizgisi kullanılır. Her yazının altında WIPEOUT vardır (`ROTAS-YANGIN-MASKE`). Vana olan yerde boru kesilir. |
| `kontrol.py` | DXF dosyası yeniden okunarak denetlenir: katman adları, boru-boru çakışma ve kesişme, boru veya başlığın betonarme kolonu kesmesi, yazı ile yazı/boru/başlık/duvar çakışması, DN etiket sayısının boru zinciri sayısına eşitliği, başlık aralığının ≥ 2 m olması. |
| `calistir.py` | Komut satırı ve önizleme. PNG yalnız kontrol içindir, depoya konmaz. |

## Girdi (JSON, cm)
`mahaller[]`: `ad`, `sinif` (LH/OH1..4/HHP1..3), `rect` [x0,y0,x1,y1] (duvar iç yüzleri), `kapi` {p:[x,y] duvar ekseninde, w}. Bir mahal `dagitim: true` olur (koridor veya tek hacim).
`kolonlar[]`: betonarme kolon dikdörtgenleri. `dis_hat`: bina dış hattı. `tavan`: `asma` → sarkık başlık, `yok` → dik başlık.
`kolon_hatti` {ad, kose: sol-alt|sol-ust|sag-alt|sag-ust}.
`hidrolik` {C, K?, statik_m, besleme_L_m, besleme_dn, vana_kaybi_bar, ek_debi_lpm}.
`deneme: true` verilirse çizimde "DENEME" başlığı ve notu yazılır.

## Deneme sonuçları (yapay mimari, örnek değerler)
| Deneme | Başlık | En uzak alan | Q | P kolon | Pompa | Depo |
|---|---|---|---|---|---|---|
| Ofis katı 30×20 m, OH1 | 56 | ODA-4 (7 başlık) | 463 l/dk | 1,15 bar | 27,8 m³/h @ 23,1 mSS | 27,8 m³ |
| Otopark 40×25 m, OH2 | 84 | uzak köşe (13 başlık) | 894 l/dk | 1,46 bar | 53,6 m³/h @ 22,1 mSS | 53,6 m³ |

İki çıktıda da kontrol `HATA: 0` verdi. Her boru zincirinde DN etiketi ve başlık sayısı vardır (ofis 74/74, otopark 92/92).

## Sınırlar
- Yalnız eksene paralel dikdörtgen mahaller desteklenir. L/U biçimli veya eğik mahallerde dikdörtgenlere ayırma (05 §4 Adım B) yapılmadı.
- Bütün mahaller dağıtım mahalline (koridora) açılan bir kapıdan beslenmelidir. Oda içinden odaya besleme ve çok sıralı dağıtım mahalline ek mahal bağlanması desteklenmez.
- Koridor tek sıra başlık alır (genişlik ≤ 2·Dmax). Kiriş, kanal ve aydınlatma engelleri yoktur; yalnız betonarme kolonlardan kaçınılır.
- Ağaç (tree) sistemdir; ring/grid hidrolik çözümü yoktur. Kot farkı yok sayılır (düz tavan). Başlık bağlantı nipeli/düşüşü hesaba katılmaz.
- Eşdeğer boy tablosu ⚠ (EN 12845 Tablo 38 değerleri doğrulanmalı). Vana kayıpları (0,35 bar) kabuldür.
- İşletme alanı başlık sayısı N'ye göre kırpılınca alan tam dikdörtgen olmayabilir (L biçimi). Küçük mahalde eksik başlıklar en yakın komşu mahallerden tamamlanır.
- Kapı kanadı yayını mahal besleme borusu planda keser (tavan seviyesinde normaldir). Kontrol yalnız boru, yazı ve kolon çakışmalarına bakar.
- Pompa ve depo tek kat içindir; dolap/hidrant payı `ek_debi_lpm` ile verilir. Kat zon vana grubunda izlenebilir kelebek vana ve akış anahtarı plandadır; test-drenaj yalnız not olarak yazılır.
- Önizlemede ezdxf/matplotlib sabit genişlikli polyline'ları kaybedebiliyor. Önizleme bu yüzden genişliği çizgi kalınlığına çevirir; DXF dosyası değişmez.
