# Deneme modülü: radyator (radyatörlü ısıtma) — R4 (merkezi) / R3 (kombi)

## R4 (14.10.2026, kullanıcı onayı: kazan dairesi "her yerde bunu kullanacaksın")
- Merkezi sistem çıktısı `proje/denemeler/radyator/radyator_merkezi_R4.dxf`: R3'ün tamamı + tüm çizimin sağında
  **ONAYLI KAZAN DAİRESİ paftası** (plan 1/50 + kesit A-A + kısmi görünüş B + lejant + kontroller + cihaz listesi)
  `kazan_dairesi/plan_kesit.onayli_kazan_dairesi()` ile (`sema.kazan_dairesi_paftasi`). Kolon şemasının bodrumundaki
  prensip bağlantısı (R2 şema, gömülü) kalır.
- Kazan adedi / kapasitesi ve pompa debi / basma radyatör hesabından gelen AYNI JSON ile verilir (bu veride 2 × 85 kW,
  zon pompası P-01 asıl+yedek 6,6 m³/h – 1,7 mSS); kullanılan JSON `radyator_merkezi_R4_kazan_dairesi.json` olarak
  yazılır (mimari yok → `plan` temsili oda 8,00 × 6,00 m). Numaralar `numara='R2'` ile gömülü şemayla aynı; çalıştırmada
  cihaz listesi satır satır karşılaştırılır ("numara senkron: True").
- `kontrol.py` onaylı paftayı (çerçeve XDATA `ONAYLI_KAZAN_DAIRESI`) ana denetimden ayırır (MTY/atlatma kuralı ona
  uygulanmaz) — ana denetim R3 ile aynı: MTY 0, köprü 0, kesişme 0, etiket 68/68, elektrik 0.
- Kombi sistem değişmedi (`radyator_kombi_R3.dxf`).

# R3 (14.10.2026 (B) talimatı)

## R3 değişiklikleri (R2'nin üzerine)
- **MTY bloğu yok:** radyatör (plan + şema), termostatik vana, dönüş rakoru, havlupan, kolektör dolabı, kalorimetre,
  küresel vana, pislik tutucu, boşaltma vanası, O.H.A.C, kolon (plan), kombi, mahal etiketi saf geometri `ROTAS-` blokları
  (`geo.py`). `ciz.Cizim.blok` yalnız `geo.py` anahtarlarını kabul eder; `mtylib.py` artık bu modülce kullanılmaz
  (wc_havalandirma modülü kullandığı için dosya silinmedi).
- **Atlatma / köprü yok (kesişme 0):** kolon şeması merdiven düzenine çevrildi — her dairenin gidiş kolonu bir yanda,
  dönüş kolonu öbür yanda, kat bağlantıları ikisinin arasında. Kolektör dolabında gidiş kolektörü üstte (ağızlar yukarı),
  dönüş kolektörü altta (ağızlar aşağı); en uzak radyatör en dış döngü → devreler iç içe, kesişmesiz. KS dönüşü kolona
  yakın noktadan aşağı inip radyatörlerin altından dönüş kolonuna gider. A dairesi aynalı: gidiş kolonları (K1, K2) ortada,
  dönüş kolonları dışta. Bodrumda gidiş dağıtımı üstte, dönüş toplama altta, **kazan dairesi prensip şeması ikisinin
  arasında** (`kazan_dairesi.ciz(gomulu=True)`). 1/10 kolektör/kalorimetre detayında gidiş-dönüş güzergâhı da kesişmesiz
  kuruldu (köprü kodu çağrılmaz). Plan PEX devreleri R2'de de kesişmesizdi (ag.py denetimi), korunuyor.
- **Elektrik kalemi yok:** kalorimetre sinyal (M-Bus) hattı planda, şemada ve detayda kaldırıldı (`ROTAS-ISITMA-SINYAL`
  katmanı yok); not: "okuma bağlantısı elektrik projesindedir".
- (R4'te değişti: plan/kesit/görünüş paftası eklendi) bodrumda prensip bağlantısı (kazan dairesi prensip şeması R2 +
  cihaz listesi). Kazan dairesi cihaz numaraları XDATA ile aktarılır, etiket–sembol eşleşmesi %100.
- Radyatör bilgisi (tip/boy/kapasite, mahal/no/sıcaklık, (kritik no) devre / yük / çap) şema radyatör gövdesinin içinde.

**Çalıştırma**
```
python3 motor/deneme/radyator/calistir.py                 # merkezi → proje/denemeler/radyator/radyator_merkezi_R3.dxf
python3 motor/deneme/radyator/calistir.py --sistem kombi  # kombi   → radyator_kombi_R3.dxf
python3 motor/deneme/radyator/kontrol.py proje/denemeler/radyator/*_R3.dxf   # MTY 0, köprü 0, kesişme 0, etiket %100
```
Son denetim: merkezi ve kombi R3 — MTY 0, köprü 0, boru-boru kesişmesi 0, elektrik 0, kazan dairesi etiketi 68/68.
"Diğer çakışma (bilgi)" satırındaki boru-sembol sayıları hat üstü sembollerin (maskeli vana/kalorimetre) ve dolap /
detay çerçevelerinin boruyla temasıdır; kesişme değildir.

**Sorulacaklar (R3):** A dairesinin aynalı çizilmesi (gidiş kolonları ortada) ve dönüşün radyatörlerin altından dönüş
kolonuna gitmesi kesişmesizlik için seçildi — kullanıcının kolon şeması tarzına uygunluğu onaylatılmalı.

---

# (R2 açıklaması — tarihçe)

**Ne yapar:** Kullanıcının ısı kaybı (`ik.xls`) ve radyatör seçim (`rad.xlsx`) dosyalarını `motor/izoder_rapor/oku.py` ile okur
(radyatör seçimi DEĞİŞTİRİLMEZ). Temsili daire tipik planında (mimari yok) KOLEKTÖRLÜ dağıtım çizer ve hesaplar. Tek DXF (R2018):

1. **Kat planları** (Z, NORMAL 1-5 tipik, Ç – 1/50)
   - Temsili mimari: pencere / balkon kapısı (`parametre.json → mimari.pencere`), kapı kanadı, temsili tefriş (ince çizgi).
   - **Radyatör yerleşimi:** önce pencere altı, cam ölçüsüne göre (radyatör boyu ≤ pencere genişliği − 10 cm, ortalanmış);
     pencere yoksa / sığmıyorsa / dolu ise pencereye (antrede kolektöre) **en yakın boş duvar** — kapı + kapı açılım alanı,
     tefriş, balkon kapısı, kolektör dolabı, köşe payı (50 cm) ve diğer radyatörler dışında. Seçim gerekçesi devre
     çizelgesinde ("YERLEŞİM" sütunu).
   - **Kolektör dolabı (KD)** antre duvarında, daire girişine yakın; ağız sayısı = radyatör sayısı (blok `ROTAS-KOLEKTOR-DOLABI-n`).
   - **Her radyatöre ayrı PE-Xc/Al/PE-X gidiş-dönüş hattı** (eksen ±3 cm paralel): antrede şeritler, odaya kapıdan girip
     duvar boyu; ilk biten devre duvara en yakın izde → devreler birbirini ve besleme hattını KESMEZ (kesişirse plan kurulmaz,
     hata verir). Radyatör bağlantısı: gidiş termostatik vana ucunda, dönüş rakor ucunda (MTY Panel / Banyopan blokları).
   - Merkezi: kolon hol köşesinde (`MTY-BORU KOLON`), hol duvarında sıva altı kalorimetre dolabında **KS – KALORİMETRE SETİ**
     (1 küresel vana, 2 pislik tutucu, 3 kalorimetre: debi ölçer + dönüş sensörü dönüşte, gidiş sensörü gidişte, sinyal
     kesikli, 4 balans vanası, 5 küresel vana) → daire kapısından KD'ye. Kombi: mutfak dış duvarında `MTY-KOMBİ`, baca dışarı → KD.
   - Etiketler: radyatör tipi/kapasite + mahal no + devre no; devre "D3 1662W-Ø16x2"; besleme "11216W-Ø32x3"; mahal bloğu;
     hepsi boş yere yerleşir (yazı altında maske).
2. **Kolon şeması** (kat bantlı): her daire kolon T → KS seti (sembollerle, 1-5 numaralı) → `ROTAS-KOLEKTOR-SEMA-n` dolap
   görünüşü → her radyatöre iç içe (kesişmesiz) ayrı gidiş-dönüş; kolon diplerinde küresel vana + boşaltma, başlarda O.H.A.C,
   kritik devre (n) numaraları. Merkezi sistemde bodrum bandının solunda **KAZAN DAİRESİ PRENSİP ŞEMASI**
   (`motor/deneme/kazan_dairesi/kazan_dairesi.py` import edilir; kazan adedi/kapasite, zon pompası debi/basma bu modülün
   hesabından), zon pompası gidiş çıkışı ve dönüş girişi kolon diplerine bağlanır.
   **KESİT/GÖRÜNÜŞ detayı (1/10):** kalorimetre (sayaç) dolabı görünüşü, kolektör dolabı görünüşü, A-A kesiti, açıklama listesi.
3. **Hesap paftası:** radyatör seçim çizelgesi, kritik devre boru çapı tablosu + Σζ dökümü, pompa, KOLEKTÖR DEVRE ÇİZELGESİ
   (tipik daire), MALZEME LİSTESİ (radyatör, vana takımı, kolektör (ağız sayısına göre), KS seti, dolaplar, boru metrajı).
4. **Pafta sonu:** `motor/deneme/semboller/sembol.py → otomatik_lejant` ile kullanılan sembollerin lejantı + ADET tablosu
   (MTY'de olmayan balans vanası, kalorimetre, sensör, kolektör dolabı `semb.py`'de 03_SEMBOLLER geometrisiyle tanımlanır ve
   lejant kaydına çalışma anında eklenir; semboller modülünün dosyasına dokunulmaz).

**Hidrolik:** çelik (kolon, kazan dairesi) TS EN 10255; daire içi PE-Xc/Al/PE-X (ε = 0,007 mm), Darcy-Weisbach + Colebrook,
R ≤ 10 mmSS/m, w ≤ 0,6 m/s (PEX). ζ: kalorimetre 8, balans vanası 5, kolektör 1,5 (giriş/çıkış) – `parametre.json` (katalogla teyit).

**Çalıştırma**
```
python3 motor/deneme/radyator/calistir.py                 # merkezi  → proje/denemeler/radyator/radyator_merkezi_R2.dxf
python3 motor/deneme/radyator/calistir.py --sistem kombi  # kombi    → radyator_kombi_R2.dxf
python3 motor/deneme/radyator/kontrol.py proje/denemeler/radyator/*_R2.dxf
```

**Dosyalar:** `veri.py` (okuma), `ag.py` (temsili mimari, pencere/tefriş, radyatör yerleşimi, kolektör, devre güzergâhları,
B dairesi aynası), `hidrolik.py` (çelik + PEX çap seçimi), `hesap.py` (ağaç, kritik devre, pompa, malzeme), `plan.py`,
`sema.py` (kolon şeması + kazan dairesi bağlantısı + detay), `tablo.py`, `semb.py` (sembol köprüsü), `ciz.py`, `mtylib.py`.

**Sınırlar / sorulacaklar**
- Mimari yok: pencere genişlikleri, balkon kapısı, tefriş TEMSİLÎ (parametre). Gerçek projede cam ölçüleri mimariden okunmalı.
- Salonda 2. radyatör (pencere tek, balkon kapısının altına konmaz) en yakın boş duvara gitti — kullanıcı onayı.
- Kalorimetre seti hol duvarındaki sayaç dolabında varsayıldı (okuma ortak alandan). Daire içinde istenirse yer değişir.
- Plan sembol adedi lejantta plan + şema + detay INSERT'lerinin toplamıdır (malzeme adedi için MALZEME LİSTESİ esas).
- R1 çıktıları (`radyator_merkezi.dxf`, `radyator_kombi.dxf`) depoda duruyor; R2 bunların yerine geçer.
