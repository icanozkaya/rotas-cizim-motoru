# YERDEN_ISITMA.dwg tamamlama (kullanıcı 15.10.2026 21:45)

İstek: kollektörleri bağla, holde yerden ısıtma yok, şema çıkar, ısı kaybı + yerden ısıtma hesabı, mahaller numaralı, kat yüksekliği 3 m.
Mimari = new_block (Metra 4739/4) yerden ısıtma paftası, x ofseti +22 761,88 cm (motor çıktısı kullanıcı koordinatına taşındı).

Üretim:
```
YI_HOL_YOK=1 YI_ISI_KAYBI=1 YI_CIKIS=<dizin> python3 motor/yerden2/yerden.py
python3 motor/yerden2/kullanici_birlestir.py KULLANICI.dxf <dizin>/NB_YERDEN_ISITMA.dxf CIKIS.dxf
```
- `YI_HOL_YOK`: hol serpantini yok, ayaklar holden geçer, hol ısıtılmayan listesinde.
- `YI_ISI_KAYBI`: `isi_kaybi.py` (kullanıcının ZEMİN/1 NK ısı kaybı sayfası düzeni); devre W = mahal Q × L/ΣL.
- Kullanıcının bağlantısız serpantinleri (MTY-PEX-BORU) motorun kollektöre bağlı devreleriyle değiştirildi.
Kabuller: dış hava −3 °C, U: DD 0,479 / ÇP 2,40 / döşeme 0,269 / çatı arası tavanı 0,30 / iç duvar 0,814; pencere ölçüleri mimari yazılardan (160/230); kuzey plan üstü.
Açık: 2. kat D7 kombi–kollektör hattı çizilemedi (kombi yeri işaretli) — standart motorun bilinen açık maddesi.
