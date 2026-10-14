# Uçtan uca sıhhi tesisat denemesi — karşılaştırma (new_block.dxf)

Tarih: 14.10.2026. Motor çıktısı: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME.dxf` (`motor/deneme/uctan_uca/nb.py`).
Referans: kullanıcının aynı dosyadaki MTY çizimi (MTY-* katmanları). Kullanıcı çizimi tanımaya **girmedi**; yalnız burada okundu.
Koordinatlar zemin kat mimari kaynak koordinatıdır (cm). Kullanıcının kolon konumu = "MTY-KOLON NO" dinamik bloğunun yerleştirme noktası (yaklaşık).

## 1. Pis su kolonları (zemin kat)

Kolon sayısı: kullanıcı **9** (zemin 9 / 1. kat 9 / 2. kat 9 / temel 9 etiket), motor **9** (her katta aynı hizada).

| Kullanıcı | Islak hacim | Kullanıcı konum | Motor | Motor tip | Motor konum | Fark (cm) |
|---|---|---|---|---|---|---|
| P1 | mutfak | 253578, -443414 | P3 | MUTFAK | 253617, -443305 | 116 |
| P2 | wc-lvb. | 253735, -442737 | P2 | WC | 253742, -442795 | 59 |
| P3 | banyo | 253716, -442662 | P1 | BANYO | 253862, -442622 | 151 |
| P4 | mutfak | 253553, -443414 | P6 | MUTFAK | 253513, -443305 | 116 |
| P5 | wc-lvb. | 253394, -442737 | P5 | WC | 253388, -442795 | 58 |
| P6 | banyo | 253414, -442662 | P4 | BANYO | 253268, -442622 | 152 |
| P7 | mutfak | 253765, -441812 | P9 | MUTFAK | 253723, -441692 | 128 |
| P8 | wc+banyo | 253066, -442255 | P7 | BANYO | 253202, -442168 | 161 |
| P9 | duş | 252778, -441881 | P8 | DUŞ | 252783, -441978 | 97 |


Not: kolon adları farklı sıralanıyor (kullanıcı: P1/P4 mutfaklar, P2/P5 wc-lvb, P3/P6 banyo, P7 3. daire mutfak, P8 wc+banyo, P9 duş; motor: daire daire banyo → wc → mutfak). Eşleme ıslak hacme göre yapıldı.

## 2. Islak hacim armatürleri ve yükler (zemin kat)

| Mahal | Etiket konumu | Kullanıcı armatürleri | Motorun tanıdığı | SB kull. | SB motor | MB kull. (SO+SC) | YB motor (SO+SC) |
|---|---|---|---|---|---|---|---|
| banyo | 253356,-442520 | LV/YS(2 SB, 1.5 MB), WC(10 SB, 0.5 MB), LV/YS(2 SB, 0 MB), DUŞ(7 SB, 5 MB), ÇM/EV/BM(4 SB, 1.5 MB) | WC, LV, DUS, YS, CM | 25 | 25 | 8.5 | 4.5 |
| banyo | 253802,-442561 | LV/YS(2 SB, 1.5 MB), WC(10 SB, 0.5 MB), LV/YS(2 SB, 0 MB), DUŞ(7 SB, 5 MB), ÇM/EV/BM(4 SB, 1.5 MB) | WC, LV, DUS, YS, CM | 25 | 25 | 8.5 | 4.5 |
| duş | 252827,-441927 | LV/YS(2 SB, 0 MB), LV/YS(2 SB, 1.5 MB), DUŞ(7 SB, 5 MB), LV/YS(2 SB, 0 MB) | LV, DUS, YS | 13 | 11 | 6.5 | 3 |
| mutfak | 253412,-443179 | ÇM/EV/BM(4 SB, 1.5 MB), ÇM/EV/BM(4 SB, 2 MB) | BM, EV | 8 | 8 | 3.5 | 2 |
| mutfak | 253600,-441690 | ÇM/EV/BM(4 SB, 2 MB), ÇM/EV/BM(4 SB, 1.5 MB) | EV | 8 | 4 | 3.5 | 1 |
| mutfak | 253748,-443179 | ÇM/EV/BM(4 SB, 1.5 MB), ÇM/EV/BM(4 SB, 2 MB) | BM, EV | 8 | 8 | 3.5 | 2 |
| wc+banyo | 253134,-442100 | ÇM/EV/BM(4 SB, 1.5 MB), DUŞ(7 SB, 5 MB), WC(10 SB, 0.5 MB), LV/YS(2 SB, 0 MB), LV/YS(2 SB, 1.5 MB) | WC, LV, DUS, YS | 25 | 21 | 8.5 | 3.5 |
| wc-lvb. | 253323,-442780 | WC(10 SB, 0.5 MB), LV/YS(2 SB, 1.5 MB) | LV, WC(alaturka) | 12 | 12 | 2 | 1.5 |
| wc-lvb. | 253847,-442783 | WC(10 SB, 0.5 MB), LV/YS(2 SB, 1.5 MB) | LV, WC(alaturka) | 12 | 12 | 2 | 1.5 |


Kullanıcı ayrıca balkon / ıslak hacim dışı **5 adet yer süzgeci** (SUZGEC1, 2 SB) çizmiş; motor balkon süzgeci koymuyor.

## 3. Rögarlar (temel planı)

|  | Kullanıcı | Motor |
|---|---|---|
| Rögar sayısı | 4 + PB | 4 + PB |
| Cephe | doğu (x≈254520) | doğu (x≈254518) |
| R1 konumu / kolonlar | 254520, -441848 / P7, P9 | 254518, -441692 / P9 |
| R2 konumu / kolonlar | 254520, -442335 / P8 | 254518, -442073 / P8, P7 |
| R3 konumu / kolonlar | 254520, -442841 / P2, P3, P5, P6 | 254518, -442708 / P1, P4, P2, P5 |
| R4 konumu / kolonlar | 254520, -443366 / P1, P4 | 254518, -443305 / P3, P6 |
| PB konumu / kolonlar | 255026, -443366 /  | 254738, -443305 /  |
| Kolon→rögar boru çapı | Ø150 x8, Ø125 x8 | Ø100 (kolon çapı, en az Ø100); rögarlar arası Ø150 %1 |
| Şemadaki rögar blokları | 5 (MTY-ROGAR KAT) | rögar şeması: R1..R4 + PB (PVC ROGAR bloğu) |


Kullanıcı rögar kolon gruplaması kolonların y konumuna göre çıkarıldı (en yakın rögar).

## 4. Çap etiketleri (zemin kat planı)

### Pis su (Ø / SB)

| Etiket | Kullanıcı adet | Motor adet |
|---|---|---|
| Ø100 / 10 SB | 7 | 0 |
| Ø100 / 14 SB | 0 | 1 |
| Ø100 / 23 SB | 2 | 1 |
| Ø100 / 25 SB | 3 | 2 |
| Ø50 / 2 SB | 6 | 7 |
| Ø50 / 4 SB | 8 | 5 |
| Ø50 / 7 SB | 3 | 1 |
| Ø50 / 8 SB | 2 | 0 |
| Ø70 / 11 SB | 0 | 2 |
| Ø70 / 13 SB | 2 | 2 |


### Temiz su (çap / yük)

| Hat | Çap | Yük | Kullanıcı adet | Motor adet |
|---|---|---|---|---|
| sıcak | 1" | 3.25 MB | 4 | 0 |
| sıcak | 1" | 4 MB | 4 | 0 |
| sıcak | 1" | 6.5 MB | 1 | 0 |
| sıcak | 1/2" | 0.5 MB | 3 | 0 |
| sıcak | 1/2" | 0.75 MB | 2 | 0 |
| sıcak | 3/4" | 1.5 MB | 3 | 0 |
| soğuk | 1 1/4" | 11.5 MB | 1 | 0 |
| soğuk | 1 1/4" | 9.5 MB | 2 | 0 |
| soğuk | 1" | 3 MB | 3 | 0 |
| soğuk | 1" | 3.25 MB | 1 | 0 |
| soğuk | 1" | 5.25 MB | 3 | 0 |
| soğuk | 1" | 6.5 MB | 4 | 0 |
| soğuk | 1" | 8.5 MB | 1 | 0 |
| soğuk | 1/2" | 0.5 MB | 3 | 0 |
| soğuk | 3/4" | 1.25 MB | 2 | 0 |
| soğuk | Ø20 | 0.5 YB | 0 | 13 |
| soğuk | Ø20 | 1.0 YB | 0 | 7 |
| soğuk | Ø20 | 2.0 YB | 0 | 3 |
| soğuk | Ø25 | D1 5.5 YB | 0 | 1 |
| soğuk | Ø25 | D2 5.5 YB | 0 | 1 |
| soğuk | Ø25 | D3 4.0 YB | 0 | 1 |


Kullanıcı temiz su çapını **inç** ("1\"", "3/4\"", "1 1/4\"") ve yükü **MB** ile yazıyor; motor (p2 gp.dn_temiz) **Ø mm** ve **YB** yazıyor. Kullanıcının armatür yük birimleri: lavabo 0,75, duş 2,5, klozet 0,5, çamaşır 1,5, eviye 1, bulaşık 1,5, kombi 0,5 MB; motorun (gp.YB) değerleri: lavabo 0,5, duş 1, klozet 0,5, çamaşır 1, eviye 0,5, bulaşık 1. Daire ana hattı: kullanıcı 9,5 / 9,5 / 11,5 MB (1 1/4"), motor D1 5.5 / D2 5.5 / D3 4 YB.

## 5. YB / SB toplamları

|  | Kullanıcı | Motor |
|---|---|---|
| Zemin kat toplam SB (ıslak hacimler) | 136 | 126 |
| Bina toplam temiz su yükü | - | 44 YB (soğuk, 9 daire) |
| Yağmur inişi | 9 (YB1..YB9) | 9 (mimari "yağmur inişi" notlarından; ort. konum farkı 39 cm) |
| Yağmur hesabı | - | P=404.5 m², f=9, D=6.56 cm → Ø100 |


## 6. Pafta düzeni

| # | Kullanıcı (soldan sağa, sıhhi sıra) | Motor |
|---|---|---|
| 1 | YERLEŞİM  PLANI   ÖLÇEK: 1 / 250 | ANTET, NOTLAR VE LEJANT |
| 2 | TEMEL PLANI..........ÖLÇEK: 1 / 50 | YERLEŞİM PLANI |
| 3 | ZEMİN KAT PLANI..........ÖLÇEK: 1 / 50 | TEMEL PLANI |
| 4 | 1. KAT PLANI..........ÖLÇEK: 1 / 50 | ZEMİN KAT SIHHİ TESİSAT PLANI |
| 5 | 2. KAT PLANI..........ÖLÇEK: 1 / 50 | 1. KAT SIHHİ TESİSAT PLANI |
| 6 | ÇATI PLANI..........ÖLÇEK: 1 / 50 | 2. KAT SIHHİ TESİSAT PLANI |
| 7 |  | SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI + RÖGAR ŞEMASI |
| 8 |  | YAĞMUR SUYU ŞEMASI VE HESABI |
| 9 |  | SIHHİ DETAYLAR |


## 7. Kontroller (motor)

| Kontrol | Sonuç |
|---|---|
| kolon_cakisma | 0 |
| bosta_uc | 0 |
| kopru | 14 |
| cakisik | 13 |
| yazi_maskesi | 120 |
| dedupe | 20 |


## 8. Yorum: önemli farklar ve nedenleri

| Konu | Kullanıcı (MTY) | Motor | Değerlendirme |
|---|---|---|---|
| Kolon sayısı / ıslak hacim eşlemesi | 9 kolon: her ıslak hacim kendi kolonu | 9 kolon, aynı ıslak hacimler | UYUMLU |
| Banyo kolon yeri | banyo ile wc-lvb arasındaki duvarda, "mek. havl." şaftına yakın | klozetin arka duvarında en yakın köşe | FARKLI (~150 cm). Kural: şaft / ortak duvar tercih edilmeli |
| Mutfak kolon yeri | tezgâh ucunda balkon duvarı dibi | eviye arkasında duvar dibi | FARKLI (~120 cm) |
| Islak hacim SB | banyo 25, wc-lvb 12, mutfak 8, wc+banyo 25, duş 13 | banyo 25, wc-lvb 12, mutfak 8 (3. daire 4), wc+banyo 21, duş 11 | 3. daire mutfağında bulaşık mak. ve wc+banyoda çamaşır mak. mimaride işaretli değil (motor bulamadı); kullanıcı ekledi |
| Klozet tipi (wc-lvb) | klozet bloğu (10 SB) | mimarideki alaturka hela çizimi -> WC (alaturka) 10 SB | SB aynı |
| 1. kat sağ wc-lvb | kolon etiketi her katta (P2) | mimaride 1. katta bu mahal "yüklük" -> armatür yok, kolon geçer | KULLANICIYA SORULMALI |
| Temiz su yük birimi | MB, armatür başına lavabo 0,75 / duş 2,5 / çamaşır 1,5 / bulaşık 1,5 / eviye 1 / kombi 0,5 | gp.YB: lavabo 0,5 / duş 1 / çamaşır 1 / bulaşık 1 / eviye 0,5 | FARKLI: daire ana hattı kullanıcı 9,5-11,5 MB 1 1/4", motor 4-5,5 YB Ø25. Motor tablosu kullanıcınınkine çekilmeli |
| Temiz su çap yazımı | inç (1/2", 3/4", 1", 1 1/4") | Ø mm (Ø20, Ø25) | FARKLI - kullanıcı tarzı inç |
| Kolon -> rögar çapı | Ø125 (kolon bağlantıları), Ø150 %1 (rögarlar arası) | Ø100 kolon bağlantısı, Ø150 %1 rögarlar arası | FARKLI: kullanıcı Ø125 kullanıyor |
| Rögar dizilimi | doğu cephesi, R1..R4 + PB (PB R4 hizasında, ~500 cm doğuda) | doğu cephesi, R1..R4 + PB (R4 hizasında, 220 cm doğuda) | BÜYÜK ÖLÇÜDE UYUMLU; kolon gruplaması kısmen farklı (P7/P9) |
| Balkon yer süzgeçleri | var (5 adet, zemin) | yok | EKSİK |
| Çatı planı | var (sıhhi sırasında) | yok | EKSİK |
| WC havalandırma izometrisi | var (detay paftasında) | yok (yalnız MTY-SIHHİ DETAYLAR bloğu) | EKSİK |
| Temiz su güzergâhı | kolon kutusundan daireye, antre duvarları boyunca kısa | A* router: merdiven holünden uzun dikey hatlar (3. daireye holün içinden) | İYİLEŞTİRİLMELİ |
| Kolon şeması | tek şema, D1..D9 bloklar yan yana | p2 gsheet ile tek şema (3 grup x 3 kat), D1..D9 | BENZER; 1. kattaki yüklük farkı şemada gösterilmiyor |

