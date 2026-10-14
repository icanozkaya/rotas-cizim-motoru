# pompa_grubu (deneme modülü, 14.10.2026)

Parametrik **pompa grubu kesitleri** (görünüş) üretir. Çıktı yalnız DXF (R2018 / AC1032), `proje/denemeler/pompa_grubu/`.

| Girdi (`tip`) | Çıktı | Ölçek |
|---|---|---|
| `yangin` | `YANGIN_POMPA_GRUBU_KESITI.dxf` | 1/25 |
| `hidrofor` | `HIDROFOR_GRUBU_KESITI.dxf` | 1/25 |
| `pissu` | `PIS_SU_POMPA_CUKURU_KESITI.dxf` | 1/20 |

## Çalıştırma
```
cd motor/deneme/pompa_grubu
python3 calistir.py girdi/yangin_test.json
python3 calistir.py girdi/hidrofor_test.json
python3 calistir.py girdi/pissu_test.json
python3 onizle.py <dxf> <png> [dpi] [x0 y0 x1 y1]   # yalnız kontrol amaçlı PNG (depoya konmaz)
```
Ön koşul: MTY blok kütüphanesi `/tmp/claude-0/blk/*.dxf` açılmış olmalı (`bash kurulum.sh`).

## Ne çizer
- **Yangın**: betonarme depo kesiti (kısaltılmış; maks./min. su, girdap önleyicili çan ağızlı emiş, su tutucu flanşlı duvar geçişi,
  şamandıralı dolum, taşma, dip boşaltma, menhol, manyetik seviye göstergesi), önden geçen emiş kollektörü, elektrikli + dizel pompa
  (EN 733 yan görünüş, `motor/ekipman.py` gerçek ölçüleri), dikey çok kademeli jokey pompa, emişte izlenebilir kelebek + vakum manometresi +
  kompansatör + eksantrik redüksiyon, basmada konsantrik redüksiyon + kompansatör + manometre + çek valf + izlenebilir kelebek, dizelde emniyet
  vanası (huni → yer süzgeci), basma kollektörü, basınç şalterleri (PS-J/E/D), test hattı + debimetre (depoya dönüş), hava purjörü, membranlı tank,
  3 kumanda panosu, yakıt tankı (tavalı), egzoz esnek bağlantısı + susturucu (dış atmosfere), kot ve ölçüler.
- **Hidrofor**: GRP panel depo kesiti (dolum, taşma, boşaltma, menhol, havalık, kuru çalışma flatörü), depo çıkışında küresel vana + pislik
  tutucu, önden geçen emiş kollektörü, N adet dikey pompa (her birinde küresel vana + esnek bağlantı / esnek bağlantı + çek valf + küresel vana),
  basma kollektörü, membranlı tank, basınç şalteri, manometre, frekans konvertörlü pano.
- **Pis su çukuru**: betonarme çukur, sızdırmaz kapak, giriş borusu, dalgıç pompa(lar), 3 flatör (durdurma/çalıştırma/alarm), basma hattı
  (çek valf + vana kapak üstünde, zemin kotu üzerinden ayrı rögara R2), duvara monte pano ve kablolar. Havalık **gösterilmez** (README).
  Faydalı hacim kontrolü: V = Q/(4·Z); yetersizse notta gerekli derinlik yazılır.
- Her parça numaralı balonla işaretlenir; numaralar **cihaz listesi** tablosuyla eşleşir (NO / CİHAZ / ADET / TEKNİK ÖZELLİKLER,
  `motor/yangin_pompa/cihaz_listesi.py` tarzı). Altında hidrolik özet notları (DN seçimi, hızlar, ayar değerleri) yer alır.

## Nasıl çalışır
- `ortak.py`: Cizim çekirdeği. Katmanlar `ROTAS-` önekli. MTY vana blokları kullanıcı kütüphanesinden **gerçek blok (INSERT)** olarak alınır,
  patlatılmaz; `CAP` özniteliği DN ile doldurulur (görünmez; görünür çap etiketi boru üzerinde). Görünüşte önde kalan nesne arkadakini örter
  (z sırası + şapely kırpma): emiş kollektörü pompa kaidesinin önünden geçer, arkadaki çizgiler kesilir; vana/redüksiyon konan boru blok boyunca
  kesilir; duvar/döşeme geçişlerinde tarama boru bandında açılır. Yazı altına `ROTAS-MASKE` katmanında WIPEOUT konur.
  `denetle()` yazı/yazı, yazı/blok, balon/çizgi, kılavuz kesişmesi çakışmalarını raporlar (test girdilerinde 0).
- `semboller.py`: MTY'de karşılığı olmayan görünüşler (dikey pompa, membranlı tank, pano, yakıt tankı, susturucu, debimetre, presostat,
  redüksiyonlar, girdap önleyici, şamandıra, flatör, dalgıç pompa, yer süzgeci, menhol, seviye göstergesi). EN 733 pompa modülleri
  `motor/ekipman.py` kayıtlarından aktarılır (mevcut koda dokunulmaz).
- Çap seçimi: yangın emişi %140 debide ≤1,8 m/s, basma ≤3 m/s, test hattı %150 debide ≤3,5 m/s; hidrofor emiş ≤1,0, basma ≤1,5 m/s.

## Sınırlar / açık konular
- Yangın kesiti tek görünüştür (pompalar yan görünüşte, sıralı); gerçek pompa dairesi planı ve alarm vana istasyonu / itfaiye bağlantısı bu
  kesitte yok. Depo genişliği kırık çizgiyle kısaltılmıştır.
- Pompa/tank/pano ölçüleri tipik (DAB/Grundfos/Zilmet verisi); proje ürünüyle teyit edilmelidir. Pompa yerleşim x koordinatları sabit
  (test değerleri için), çok farklı ölçülerde `girdi` dosyasıyla birlikte koddaki konumlar gözden geçirilmelidir.
- EN 12845 emiş ağzı batma tablosu (`EN12845_BATMA`) teyit edilmelidir.
- README katman öneki `SCOTT-`, deneme kuralları `ROTAS-` diyor; bu modül deneme kuralına uyar.
