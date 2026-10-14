# Deneme modülü: radyator (radyatörlü ısıtma) — R2 KOLEKTÖRLÜ (14.10.2026)

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
