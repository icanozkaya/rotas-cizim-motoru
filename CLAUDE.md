# ROTAŞ çizim motoru — oturum başı talimatı

Bu depo Can Özkaya'nın (ROTAŞ Mühendislik) mekanik proje çizim motorudur. Yeni oturumda:
1. `bash kurulum.sh` çalıştır (motor, MTY blokları, yamalı LibreDWG, ACadSharp DWG yazıcı, Excel şablonu, örnek dosya).
2. **Kullanıcı yeni bir proje dosyası gönderdiğinde, işe başlamadan önce `ornekler/ORNEK_DUZEN.md`'yi oku ve ona hatırlat: istenen pafta düzeni ve çizim tarzı `new_block.dxf` örneğindeki gibidir.** Önizlemeler `ornekler/new_block_onizleme/` içinde.
3. README.md'deki "Kalıcı kurallar" listesine her çizimde uy; ROTAŞ/MTY standardı becerisi de geçerlidir.
4. Yaptığın her kod ve proje değişikliğini bu depoya commit + push et (kullanıcı çalışmanın kaybolmasını istemiyor).
5. Teslim: DWG (ACadSharp, AC1032) + DXF + önizleme PDF + hesap Excel; her şey Türkçe.
6. Asansör projesi gelirse önce `ornekler/asansor/ASANSOR_STANDARDI.md` oku. Asansör tipini kullanıcıya sor (makine daireli / dairesiz). Hesabı `motor/asansor/asansor_hesap.py` ile yeniden yap.
7. Kurulumda kök dizine tar açılamazsa LibreDWG `araclar/libredwg_yamali.tar.xz` dosyası `/home/claude/libredwg` içine açılır. `libredwg.so.0` sembolik bağı oluşturulur ve `LD_LIBRARY_PATH=/home/claude/libredwg/usr/local/lib` ile çalıştırılır.
8. Asansör setlerinde: düzen ozalit şeridi (594 mm, A4/A3 hücreler, örnek proje sırası); kapak kullanıcının kapak şablonundan; **elektrik detaylarının tamamı her asansör setinin sonuna eklenir** (`kutuphane/asansor/elektrik_detay.json`).
