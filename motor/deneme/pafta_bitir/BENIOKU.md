# pafta_bitir — teslim öncesi pafta bitirme aracı (DENEME, 14.10.2026)

## Ne yapar
`pafta_bitir.bitir(giris.dxf, cikis.dxf, ekler=[...])`. Girdideki tasarıma (boru, sembol, adet, katman) dokunmaz. Yalnız pafta, tablo ve ek ekler.

1. **Pafta bulma**: Önce `PAFTA/CERCEVE/ANTET` katmanlı kapalı dikdörtgenler aranır. Bunlar yoksa büyük dikdörtgenler, onlar da yoksa çizim kümeleri kullanılır. İç içe dikdörtgenden iç çerçeve ofseti çıkarılır. Pafta başlığı, çerçeve içinde "ÖLÇEK" geçen en alttaki yazıdır. Pafta türü başlıktan bulunur: PLAN / SEMA / YERLESIM / DETAY / LEJANT / DIGER. Toplam sınır da çıkarılır.
   - Genişliği medyanın 4 katını aşan ve içeriği yarısını doldurmayan çerçeve **anormal** sayılır. Raporlanır ve sağ kenarı içerik + boşluk kadar içeri çekilir (`cerceve_duzelt=False` ile kapatılır).
2. **Lejant + adet**: `semboller` modülü kullanılır (`kullanim_say_grup`, `lejant_tablosu`). Sayım pafta türü başına (PLAN, SEMA, DIGER) yapılır. **Adet = türler arasındaki en büyük sayı**, çünkü aynı vana planda ve şemada iki kez gösterilir ve toplanmaz. Lejant, detay ve yerleşim paftaları sayılmaz. Kütüphanede karşılığı olmayan, etiket olmayan bloklar (PVC çatal, rögar, kombi vb.) ayrı bir "DİĞER BLOKLAR" adet tablosuna yazılır.
   **Boru metrajı** katman + çap bazında, metre cinsinden (`$INSUNITS` dikkate alınır) ve yalnız PLAN paftalarından hesaplanır.
   - Boru katmanı adında BORU/PVC/PEX geçer; CAP/YAZI/NO/ETIKET geçen katmanlar hariçtir.
   - Çap DN / Ø / inç etiketinden (TEXT, MTEXT, MTY öznitelikleri SOCP/SCCP/PSCP) gelir. Her etiket en yakın uyumlu boru parçasına bağlanır. Etiketsiz parçalar, aynı katmanda uç uca ya da T ile bağlı parçalardan çapı alır.
   - MTY temiz su etiketinde sıcak çap boşsa, sıcak su paralel soğuk su borusunun çapını alır ve "(s)" ile işaretlenir.
   - Bağlanamayan parça "BELİRSİZ" yazılır.
   - Dikey kolon boyları ve fire payı dahil değildir; bu, tablo notunda yazar.
   Tablolar en sağdaki paftanın sağına, referans pafta tarzında (çerçeve kalınlığı, iç ofset, sağ alt başlık) yeni bir **"LEJANT, MALZEME / ARMATÜR ADET TABLOSU VE BORU METRAJI"** paftasına konur. İçerik sığmazsa çerçeve yukarı uzar.
3. **Ekler (SOL ALT)**: Ekler verilen sırada soldan sağa dizilir. Alt kenarları paftaların alt kenarıyla hizalıdır, aralarında 100 birim boşluk vardır ve sonuncusu ilk paftadan 100 birim solda durur. Her ek kendi çerçevesinde ve başlığıyla yer alır. İçe alma `ezdxf.addons.Importer` ile yapılır:
   - Katman adları korunur. Hedefte aynı adlı katman varsa hedefteki tanım kalır ve bu raporlanır.
   - Aynı adlı blok içerikçe aynıysa paylaşılır. Farklıysa `<ad>-<etiket>` olarak yeniden adlandırılır.
   - Anonim bloklar yeni anonim blok olur.
4. **Kontroller** (rapor):
   - ROTAS- öneki: 0 ve Defpoints hariç tüm üst seviye katmanlar denetlenir. Yalnız blok içinde kullanılan katmanlar (MTY blok içi) ayrı listelenir ve hata sayılmaz.
   - Yazı-yazı çakışması (MİMARİ katmanları hariç): tüm çizimde ve yeni paftalarda ayrı ayrı sayılır.
   - Boş katmanlar silinir.
   - AUDIT girişte, çıkışta ve geri okumada çalışır.

`kapak.py`: `kutuphane/asansor/kapak_sablon.json` şablonundan basit kapak üretir. Yazılar metin eşleşmesiyle ya da `"x,y"` konum anahtarıyla değiştirilir. Katmanlar `ROTAS-KAPAK`, `ROTAS-KAPAK-YAZI`.

## Çalıştırma
```
python3 motor/deneme/pafta_bitir/calistir.py                 # deneme_param.json ile
python3 motor/deneme/pafta_bitir/calistir.py --png /tmp/pb    # + önizleme PNG (depo dışı)
```
Kod içinden:
```python
import pafta_bitir as PB
R = PB.bitir('giris.dxf', 'cikis.dxf', ekler=[dict(yol='kapak.dxf', baslik='PROJE KAPAĞI'), 'isi_kaybi.dxf'])
PB.rapor_yaz(R)
```

## Deneme çıktıları (`proje/denemeler/pafta_bitir/`)
- `NB_SIHHI_BITMIS_DENEME.dxf`: girdi `NB_SIHHI_DENEME.dxf`. Ekler: kapak, `ISITMA_HESAPLARI_TABLOLAR.dxf` (ısı kaybı yerine), `HESAPLAR_SIHHI.dxf`.
- `KAPAK_SIHHI_DENEME.dxf`: şablondan üretilen kapak. Değerler örnektir ("DENEME").

Sonuç:
- 9 pafta bulundu.
- SIHHİ DETAYLAR çerçevesi 518 095 birim genişti (uctan_uca hatası); 2 500 genişliğe çekildi.
- Sembol tablosunda 14 sembol tipi var; ayrıca 6 kütüphane dışı blok.
- Boru metrajı: pis su 119 m, tavandan pis su 52 m, soğuk 233 m, sıcak 168 m (Ø20 (s)), yağmur 3 m (BELİRSİZ).
- AUDIT 0/0. Yeni paftalarda yazı çakışması yok.

## Sınırlar / açık konular
- `HESAPLAR_SIHHI.dxf` `MTY-HESAP*` katmanlarıyla geliyor. Bu katmanlar ROTAS- kontrolünde raporlanıyor. İstenirse ek alınırken `MTY-` → `ROTAS-` çevirisi eklenebilir; şu an "katman adlarını koru" kuralı geçerli.
- `ISITMA_HESAPLARI_TABLOLAR.dxf` içindeki tablolar kaynakta dağınık. Ek kendi iç düzeniyle alındığı için çerçevesi büyük ve 4 550 birim yüksek. Ekin iç düzeni değiştirilmez.
- Girdideki 6 yazı çakışması uctan_uca çıktısından geliyor: kat planlarında "0.5 YB / Ø20" ile "Ø100 / n SB" üst üste. Bunlar düzeltilmez, raporlanır.
- Metraja yalnız kat planları girer. Yağmur inişleri şemada olduğu için planda kısa kalır. Kolon boyları için şemadan dikey uzunluk eklenmesi açık iş olarak duruyor.
- Çap eşlemesi en yakın etiket ve bağlantı yayılımı ile yapılan bir yaklaşımdır. Teslimden önce gözle kontrol edilmeli.
- Lejant tabloları bölünmez. Çok uzun bir lejant paftayı yukarı uzatır.
