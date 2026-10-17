# Adapeker mimari uygulama projesi — ilerleme notu (başlangıç 17.10.2026 23:42)
İstek: sıhhi + yerden ısıtma çizimi, SASKİ altyapı, ısı kaybı + yerden ısıtma hesabı (U değerleri İZODER, Sakarya 3. bölge). Kullanıcı uyuyor; otomatik devam.
Girdi: /tmp/claude-0/ad/ad.dwg → ad.dxf (yükleme: /root/.claude/uploads/.../77ea8943-Adapeker_Mimari_Uygulama_Projesi.dwg)
Zamanlanmış kontroller (trig_): 017kX9aCvxCEkChQEGwr99eo, 01ST73bkywjs1muoE5PZQJhq, 0153Ruo1pvH7wVxB82427pQ3, 01K4jJBT1K9BMvwLBK7ebTbq, 01SbLcTfgv5Wt56ZzJCFu8wK, 012LR3Lh22DQ4Gg668NmFt5p
## Yapılanlar
- DWG→DXF
## Kalanlar
1. mimariyi oku: katlar, daireler, ıslak hacimler, kolon hatları
2. sıhhi plan + şema  3. yerden ısıtma plan + şema  4. ısı kaybı + YI Excel  5. SASKİ altyapı/vaziyet  6. kontrol, commit, teslim
- (00:30) mimari okundu: 3 kat (Z +0,50 / 1 +3,50 / 2 +6,50; h=3,00), kat başı 2 daire, aks 5'e göre simetrik, katlar x+2350/+4700.
  motor/adapeker/mimari_ad.py: tip daire (D1 zemin) mahalleri, armatürler, kolonlar P1 (banyo 4,33) P2 (banyo 2,60+ÇM) P3 (mutfak), kombi balkonda (mimari), M.H. şaftı.
  sihhi2/yerden2 motorları new_block'a sabit (pencere, tasarım json) → bu proje için motor/adapeker/ (yerden2 serpantin/tasarım, YI blokları, isi_kaybi, excel_yi, yi_sema yeniden kullanılır).
- (01:15) YERDEN ISITMA tamam (taslak): motor/adapeker/yerden_ad.py → proje/adapeker/ADAPEKER_YERDEN_ISITMA.dxf (54 devre, ayaklar kesişme araması; salon/ODA 1'er iç kesişme kalabilir), şema (yi_sema), kombi kesiti, ısı kaybı karşılaştırma tablosu.
  excel_ad.py → ADAPEKER_ISI_KAYBI_YERDEN_ISITMA_HESABI.xlsx (LibreOffice hesap hatasız; U: DD 0,40 Ta 0,30 Dö 0,35 ÇP 1,8).
- SIRADA: sihhi_ad.py (plan + kolon şeması), saski_ad.py (altyapı/vaziyet), kontrol + teslim.
- (02:00) SIHHİ: sihhi_ad.py → ADAPEKER_SIHHI_TESISAT.dxf (3 kat, 6 kolon P1-P6, sayaç grubu girişte, kolon kutuları, kolon şeması, lejant/notlar).
  SASKİ: saski_ad.py → ADAPEKER_SASKI_ALTYAPI_VAZIYET.dxf (altyapı zemin koordinatında + vaziyet mimari yerleşim koordinatında; R1-R2-R3 → PB → 10 m yol Ø200).
- SIRADA: bağımsız kontrol (render + kurallar), küçük düzeltmeler, teslim mesajı, kalan zamanlanmış kontrolleri iptal.
