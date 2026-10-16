# new_block sığınak havalandırma (duman tahliyeli, BRÜT alan) — ilerleme notu (16.10.2026)
İstek: "BRÜT M2 HESABINA GÖRE SIĞINAK HAVALANDIRMA YAPSANA DUMAN TAHLİYELİ OLACAK WC'LERİ UNUTMA" (new_block.dxf bodrum).
Kabuller: brüt = 402,10 net + 4,26 mutfak nişi + 22,48 WC = 428,84 m²; h = 2,95 (planda "h 295").
Sığınak = üst salon + doğu şerit + alt salon (U biçimli, tek bölge). Çıkışlar doğu perdesinde (üst salon GD köşesi) yan yana.
Plan: motor/siginak/nb_mimari.py (mimari tanıma) -> motor/siginak/nb_siginak.py (siginak_hav.py tabanlı çizim).
## Yapılanlar
- [x] mimari tanıma (sığınak poligonu, WC hücreleri, betonarme)
- [x] ağ yerleşimi + çizim (v8: riserler duman 358510 / taze 358810 / egzoz 359100; şerit hatları duman 358840, taze 358935, egzoz 359080; tek kesişme egzoz×taze)
- [x] tablolar/şema/çıkış kesiti/özel parça detayları/kontrol (kesişme 0 hariç bilinçli 1)
- [x] teslim: proje/new_block_siginak/NEW_BLOCK_SIGINAK_HAVALANDIRMA.dxf
- 10:48 kullanıcı çıkış yerini gösterdi: alt salon üst kenarı x 358373..359159, y -613415..-613486 ("çıkışlar bu hizadan olacak zemin kotuna çıkacak direkt") -> döşemeden düşey baca (riser) yan yana.
- Kullanıcı: "fanlar içerde kalacak şekilde yap" -> SHC/EF/DTF sığınak içinde, risere bağlı düşey (planda güneye) inişlerde; kesişmeler farklı kotta (alttaki kesikli) kabul.
- Yerleşim v7: riser egzoz 358423 / taze 358530 / duman 358745; şerit hatları taze 358890, egzoz 358975, duman 359075; üst salon kolları taze -610670, duman -610600, egzoz WC kolu -610260.
