# ONAY PROTOKOLÜ — üreten ajan ↔ kontrolör ajan döngüsü (14.10.2026 C: "TESLİM ONAYI")

README kuralı: *hiçbir sıhhi/ısıtma dosyası kullanıcıya KONTROLÖR AJAN onayı olmadan gönderilmez. Kontrolör, üreten
ajandan bağımsızdır; dosyayı kırpılmış PNG'lerle inceler, kural bloğu + RED görüntüleri + new_block referansıyla
karşılaştırır, geçmezse üreten ajana geri gönderir.*

## Roller
- **Üreten ajan**: çizimi yapan oturum/alt ajan. Kendi kontrolünü yapar (`denetle.py`, kendi özetleri) ama ONAY VEREMEZ.
- **Kontrolör ajan**: ayrı bir alt ajan (`Agent` ile, üretenin kodunu ve konuşmasını GÖRMEDEN başlatılır). Yalnız şunları alır:
  1. kontrol edilecek DXF yolu,
  2. mimari kaynak (`ornekler/new_block.dxf.xz` veya projenin mimari DXF'i),
  3. kural metni: `README.md` "Kalıcı kurallar — 14.10.2026 (C)" + (B) + standart talimatı,
  4. RED görüntüleri `kutuphane/arastirma/geri_bildirim/RED_*.png` ve onaylı örnekler `ONAYLI_*.png`,
  5. referans önizlemeler `ornekler/new_block_onizleme/`.
  Üretenin "şunu şöyle yaptım" açıklaması kontrolöre verilmez; kontrolör dosyayı bir insan gibi *görerek* ve *ölçerek* yargılar.

## Kontrolörün yaptığı iş (her tur)
1. `python3 motor/kontrolor/kontrolor.py <dxf> --mimari <mimari> --rapor <klasör>/KONTROLOR_<ad>_R<n>.md`
   → ölçümler (T01–T17; yerden ısıtmada `--tur yerden`: Y01–Y06 + T11/T16/T17), her FAIL için koordinat + kırpılmış PNG (kontrol edilen | referans new_block yan yana),
   kat ve şema genel görünümleri.
2. PNG'leri **okur** (görüntü olarak açar): her RED görüntüsündeki hata türü (balkon süzgeci → pis su kolonu; sayaç
   kapıda/kat bandında; sıcak su merdiven holünden; oda içi çapraz pis su + etiket yığını) çizimde var mı diye bakar;
   referans kırpımıyla tarzı karşılaştırır (etiket biçimi/boyu, hat güzergâhı, kolon yeri, şema düzeni).
3. Ölçümün yakalayamadığı tarz farkı görürse (ör. şema düzeni new_block'a benzemiyor, armatür sembolleri farklı) bunu da
   madde olarak yazar — "göze çarpan" her şey yazılır, ölçülemeyen şeyler için PNG referansı verilir.
4. Karar yazar — tek biçim:
   - `ONAY` — hiç FAIL yok (T06 ve INFO'lar engel değildir) ve görsel karşılaştırmada tarz farkı yok.
   - `RED + madde listesi` — her madde: `[Tnn kat] ne yanlış @ (x, y) — PNG adı — hangi kural`.
   Raporun başındaki "Düzeltme listesi" bu listedir; kontrolör görsel maddelerini ekler.

## Döngü
```
tur 1: üreten çizer  →  kontrolör RED/ONAY
tur 2: üreten yalnız RED maddelerini düzeltir (tasarım seçimleri değişmez)  →  kontrolör yeniden (yeni dosya, yeni rapor)
tur 3: aynı
```
- Her turda üreten, bir önceki raporun madde numaralarına karşılık "ne yapıldı" yazar; kontrolör bunu okumaz, dosyayı
  yeniden ölçer (bağımsızlık).
- Kontrolör aynı eşiklerle çalışır; eşik gevşetme yalnız kullanıcı kararıyla (`testler.py` üst bloğu, BENIOKU'da gerekçe).
- **3 turda ONAY yoksa**: dosya kullanıcıya GÖNDERİLMEZ. Kullanıcıya açıkça şu yazılır: "Kontrolör 3 turda onay vermedi.
  Kalan eksikler: (madde listesi, PNG kanıtlarıyla). Şu kurallar motorla çözülemedi: ... Nasıl ilerleyelim?"
  Gizli teslim ("şu kadarı tamam, gerisini sonra") yapılmaz.

## Kontrolörün bakacağı RED türleri (kullanıcı görüntüleri ↔ test)
| RED görüntüsü | Ne gösteriyor | Ölçen test |
|---|---|---|
| `RED_sihhi_balkon_suzgeci_banyo_kolonuna_bagli.png` | balkon süzgeci yağmur inişi yerine P9 pis su kolonuna | T01 (+T02 mahal dışı) |
| `RED_sihhi_kolon_semasi_sayac_kapida_yanlis_tarz.png` | her katta "Dn SAYAÇ (KAPIDA)"; sayaç grubu zemin bandında/şebeke girişinde değil; şema tarzı new_block değil | T08 + görsel karşılaştırma (GENEL_SEMA.png ↔ `ornekler/new_block_onizleme/c_s*.jpg`) |
| `RED_sihhi_sicak_su_daire_disindan.png` | sıcak su hattı merdiven holünden (daire dışı), banyoda çapraz pis su | T04, T03, T10 |
| `RED_sihhi_wcbanyo_capraz_pissu_etiket_ust_uste.png` | wc-banyo içinden çapraz uzun pis su; etiketler üst üste, mimari yazı ve hat üstünde | T03, T07 |

## Çıktı yerleri
- Rapor + PNG klasörü: teslim klasörünün yanına (`proje/.../KONTROLOR_<ad>_R<n>.md`, `_png/`); kalıcı örnek
  `kutuphane/arastirma/KONTROLOR_R4_RAPORU.md`.
- Onaylanan dosya için rapor teslimle birlikte depoya girer (kanıt). RED raporları da silinmez (geçmiş).
