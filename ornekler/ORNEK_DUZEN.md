# İSTENEN DÜZEN — örnek dosya `new_block.dxf` (11.10.2026)

Can Özkaya'nın "istediğim düzeni orada göreceksin" diyerek gönderdiği örnek set (Metra Mimarlık, Adapazarı Tekeler 4739/4, Z+2, 9 daire).
**Kullanıcı yeni dosya gönderdiğinde bu düzen esas alınır.** Dosya: `ornekler/new_block.dxf.xz` (`xz -d` ile aç), önizlemeler: `ornekler/new_block_onizleme/`.

## Pafta düzeni (model uzayında soldan sağa, iki sıra)
**1. sıra — SIHHİ TESİSAT PROJESİ**
1. ROTAŞ anteti (en solda, dikey tablo: proje müellifi / yapı denetim / onay / inceleyen-uygundur-onaylanır / ROTAŞ logo + iletişim / "SIHHİ TESİSAT PROJESİ" / arsanın ve yapının özellikleri).
2. YERLEŞİM PLANI ÖLÇEK 1/250: mimari vaziyet + kesit + proje bilgi kutusu (il, ilçe, pafta, ada, parsel, emsal; arsa alanı, yapı cinsi/sınıfı, kat adedi; yapı inşaat alanı hesabı).
3. TEMEL PLANI 1/50: bina dış hattı + kolonlar; kolon dipleri (P1..Pn etiketli), rögarlar bina dışında bir cephe boyunca R1..R4 (70x70 h:-70cm notu) + PB; rögar arası ve bağlantılarda Ø/SB/% etiketleri (MTY-PIS SU CAP SB bloğu).
4. Her kat planı AYRI pafta: "ZEMİN KAT PLANI.........ÖLÇEK: 1 / 50" (başlık plan altında, tek satır).
5. AÇILIMLI KOLON ŞEMASI (tek geniş pafta): kat bantları alçak ve sıkı; her daire bloğu yan yana, daire etiketi D1..D9 (mor daire), kombi bloğun sağında; kolon etiketleri en üstte (P1..Pn daire içinde); depo en üst-solda, temiz su ana hattı sol kenardan iner; şebeke + sayaç sırası zemin bandının solunda.
   Altında rögar şeması (R1-R2-R3-R4-PB yatay, her rögarın üstünde ona bağlanan kolon etiketleri).
   Sağda yağmur şeması (YB1..YBn yeşil dikey hatlar, üstte etiketler) + kırmızı çerçeveli "YAĞMUR SUYU BORU ÇAPI HESABI" kutusu + "YAĞMUR SUYU KANALINA GİDER".
6. Son pafta: WC havalandırma izometrisi (penceresiz WC'ler için "Wc Aspiratörü 80/160 m³/h - 50 Pa - Ø150 mm", çatı tipi fan 240/480 m³/h, mekanik havalandırma şaftı) + **SIHHİ DETAYLAR** bloğu (TS 1258 çap tablosu, SB tablosu, pis su çap tablosu, YB/debi tablosu, pis su ve temiz su lejantı, alaturka/alafranga hela, havalık, PVC geçme muflu montaj, döşeme-duvardan geçiş, yer süzgeci, eviye montaj detayları). Blok kütüphanede: `MTY-SIHHİ DETAYLAR`.

**2. sıra — ISITMA TESİSATI PROJESİ**: aynı antet ("ISITMA TESİSATI PROJESİ"), yerleşim planı, her kat yerden ısıtma planı ayrı pafta, yerden ısıtma kolon şeması.

## Kat planı çizim tarzı (sıhhi)
- Pis su: ince mor çizgi, armatürden kolona **doğrudan (eğik olabilir)**; kolon ıslak hacmin köşesinde; çap etiketi boru doğrultusunda döndürülmüş "Ø50 / 2 SB".
- Kolon etiketi P1..Pn: kırmızı çift daire içinde mor yazı, mahal dışında kolonun yanında.
- Temiz su: soğuk mavi ince, sıcak kırmızı kesikli, duvar boyunca paralel; etiket yeşil "1\" / 3.25 MB" (inç çap + yük birimi, kanca çizgili). Armatür bağlantılarında küresel vana sembolü.
- Çamaşır mak. "C'W'", bulaşık mak. "B'M'" etiketi; mutfakta kombi nişi "kombi".
- Penceresiz WC/banyo: "mek. havl." şaft + "Wc Aspiratörü 160 m3/h-50 pa Ø150 mm" turuncu yazı.
- Yağmur inişleri: cephe köşelerinde, yeşil YB etiketli çift daire.

## Yerden ısıtma tarzı
- Serpantin **meander (gidiş-dönüş paralel U)**, mahali tamamen kaplar; **hol/antre de ısıtılır** (15 °C), banyo 24 °C.
- Mahal etiketi: yuvarlatılmış kutu, cyan "20°C" / kırmızı "Z05" (MTY-RADYATOR MAHAL bloğu).
- Devre etiketi: sarı tablo (MTY-ETIKET) "Hat uzunluğu: 53.37 m / Modülasyon aralığı: 15.0 / Kcal/h: 1867.9 W / Isıtma devresi no: 4".
- Kombi mutfak nişinde, kollektör yakınında.
- Şema: kat bantlı, her daire: kombi (sarı) + kollektör + devreler yan yana panel sembolleriyle (MTY-RADYATOR KOLLEKTÖR KOLON), gidiş/dönüş hatları altta.
