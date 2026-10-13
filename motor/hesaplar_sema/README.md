# Şemadan sıhhi hesaplar (kullanıcının HESAPLAR şablonu)

Girdi: kullanıcının açılımlı kolon şeması (DWG → dwg2dxf) + HESAPLAR.dwg (OLE Excel şablonları).
Çalıştırma: `python hesap.py` (Excel) → LibreOffice ile yeniden hesap (`soffice --convert-to xlsx`) → `python dxf_tab.py` (DXF tablolar, MTY-HESAP).

Yöntem (kullanıcı şablonu ile birebir):
1. **Temiz su kritik devre (YB yöntemi):** Etkin basınç = Hidrofor/ŞŞB − (statik kot + akma + sayaç). Özgül kayıp Çizelge 3 plastik boru, YB'ye göre enterpolasyon; DN = şemadaki inç çapı (1/2"=15 … 3"=80). Debi = 0,25√YB.
2. **Blok armatür YB tablosu:** lavabo 0,75 / eviye 1 / rezervuar 0,5 / duş 2,5 / çamaşır 1,5 / şofben 1 (şemadaki MTY değerleri).
3. **Pis su kolon yükleri:** kolon başına adet × SB (klozet 10, duş 7, eviye 4, lavabo 2, süzgeç 2, çamaşır 4, **ızgara 8 SB (Ø100)**). SZ sütunu: bodrumdan pis su çukuruna giden süzgeç/ızgara.
4. **Pis su pompası (her çukur ayrı):** Qww = 0,5√ΣSB; Hm = Hgeo + Hazen-Williams (C=140, DN50) + Σζ·v²/2g, ×1,10; çukur aktif hacmi ≥ Qp/(4·Z), Z=15; motor P = ρgQH/η (η=0,40).
5. **Depo / hidrofor:** günlük ihtiyaç = daire × 4 kişi × 100 l; hidrofor Hm = bina yüksekliği + kritik devre kaybı + akma + sayaç + 2 mSS.

Proje verileri (B1-B2-B3 blok şeması, 2026-10-13): bina yüksekliği 21 m, su deposu 16 m³, 38 bağımsız birim (şofben sayısı), 3 pis su çukuru (her blokta 1), B1'de 1 adet ızgara (8 SB).
Not: şemadaki MTY dinamik blokları DXF'te '*U' adıyla gelir; `voyap/tes/ulabel.py` ile ham DXF'ten okunur.
