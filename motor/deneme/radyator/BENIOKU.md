# Deneme modülü: radyator (radyatörlü çift borulu ısıtma)

**Ne yapar:** Kullanıcının ısı kaybı (`ik.xls`) ve radyatör seçim (`rad.xlsx`) dosyalarını `motor/izoder_rapor/oku.py` ile okur;
temsili daire tipik planı üzerinde radyatörleri pencere altına yerleştirir, gidiş-dönüş çiftini duvar boyunca kapılardan geçirerek çizer,
parça parça kümülatif yük → boru çapı hesabı yapar, kritik devreyi ve pompayı bulur. Tek DXF (R2018) içinde:

1. Kat planları (ZEMİN, NORMAL 1-5 tipik, ÇATI) – 1/50, `MTY-RADYATOR Panel` / `MTY-RADYATOR Banyopan` (termostatik vana blok içinde),
   `MTY-RADYATOR MAHAL` mahal etiketi, `MTY-RADYATOR CAP` hat etiketi "11216W-DN20", merkezi sistemde `MTY-BORU KOLON` (K1/K2) +
   daire giriş `MTY-KURESEL VANA`; kombili sistemde `MTY-KOMBİ` (mutfak, dış cepheye bitişik, baca dışarı).
2. KALORİFER TESİSAT PROJESİ KOLON ŞEMASI – kat bantları (düşey 1/50), `MTY-RADYATOR KOLON` / `MTY-RADYATÖR BANYOPAN KOLON` blokları
   (mahal, no, sıcaklık, tip×boy / kapasite öznitelikli), gidiş sürekli / dönüş kesikli, kesişmelerde köprü, her parçada "Q W-DN",
   kritik devre numaraları (1…n). Merkezi: bodrumda kazan (`aKAZAN.`), termometre, manometre, emniyet ventili, vanalar, pislik tutucu,
   çek valf, sirkülasyon pompası (MTY'de temiz pompa bloğu yok → 03_SEMBOLLER geometrisi), genleşme tankı, kolon başlarında O.H.A.C.
3. Hesap paftası – radyatör seçim çizelgesi, kritik devre boru çapı tablosu (parça, Q, L, çap, w, R, R·L, Σζ, Z, kümülatif),
   Σζ dökümü, pompa (V = Q/20000 m³/h, H = (ΣRL+ΣZ)·1,1 + kazan dairesi payı), uyarılar.

**Çalıştırma**
```
python3 motor/deneme/radyator/calistir.py                 # parametre.json (sistem: merkezi)
python3 motor/deneme/radyator/calistir.py --sistem kombi
python3 motor/deneme/radyator/kontrol.py proje/denemeler/radyator/*.dxf   # üst üste binme / köprüsüz kesişme / katman denetimi
```
Çıktılar: `proje/denemeler/radyator/radyator_merkezi.dxf`, `radyator_kombi.dxf`. MTY blokları `/tmp/claude-0/blk` (MTY_BLKDIR) içinden
gerçek blok tanımı + öznitelik olarak alınır, patlatılmaz.

**Dosyalar:** `veri.py` (okuma/model), `ag.py` (temsili plan + boru yolu ağacı), `hidrolik.py` (Darcy-Weisbach/Colebrook, çap seçimi),
`hesap.py` (parça, yük, Σζ, kritik devre, pompa), `plan.py`, `sema.py`, `tablo.py` (çizim), `ciz.py` (ROTAS- katmanları, maske, köprü),
`mtylib.py` (MTY WBLOCK DXF → blok), `parametre.json` (tasarım parametreleri; radyatör seçimi DEĞİL, o kullanıcının Excel'inden gelir).

**Sınırlar**
- Mimari yok: mahaller dikdörtgen temsili yerleşim (A dairesi + merdiven holü + aynalı B dairesi); boru boyları ve kritik devre buna göre.
- Yük esası varsayılan `radyator` (seçilen radyatör kapasitesi); `isi_kaybi` seçilebilir. Radyatörler kayıpların 3,8–9,6 katı seçilmiş.
- Radyatör boyu MTY bloğunun x ölçeği ile verilir (blok 100 cm tanımlı). Banyopan bloğunda termostatik vana çizimi yok.
- Kazan dairesi hat boyları, kolon-kazan mesafesi parametredir (temsili). Kalorimetre/pay ölçer çizilmedi (MTY bloğu yok).
- Katman öneki deneme kuralı gereği `ROTAS-` (README kalıcı kuralı `SCOTT-` diyor – teslimde karar verilmeli).
