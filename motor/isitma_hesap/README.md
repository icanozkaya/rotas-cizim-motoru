# Isıtma hesapları (kullanıcının ısıtma hesaplar şablonu)

Girdi: ısıtma projesi DWG, ısıtma hesaplar DWG (rapor metinleri + OLE Excel/ resim tablolar), radyatör seçim Excel'i (mahal ısı kayıpları), ısı kaybı XLS.
Akış: `dwg2dxf` → hesaplar DXF'teki bozuk MTEXT satırları birleştirilir (hesap_fix) → `isitma_hesap.py` (hesap + Excel) → `hesap_dxf.py` (eski OLE'ler silinir, güncel rapor/ekipman tabloları çizilir, rapor metinleri düzeltilir) → `isitma_dxf.py` (kazan dairesi güncellenir, MTY *U blokları ulabel ile geri yazılır).

Yöntem:
- Toplam ısı kaybı = radyatör seçim cetvelindeki mahal kayıpları × kat tekrarı (1-2-3-4-5 → ×5, Ç, Z) × blok adedi.
- KAZAN VE EKİPMANLAR KULLANICININ PROJESİNDEKİ GİBİ KALIR (ör. 5 × 110 kW, 1000 lt, 60×60 / 45×40): hesap bu seçimlerin yeterliliğini gösterir; çizim ve rapor metinleri kendiliğinden değiştirilmez.
- Kontrol: Q × 1,15 ≤ kurulu kazan gücü.
- Debi: Q/(1,163·ΔT); IP-1 kazan başına, IP-2 radyatör devresi (×1,10). Basma: kritik devre L·R·1,30 + kalorimetre 1,5 + TRV 1,0 + denge kabı 0,5 mSS.
- Genleşme (TS EN 12828): Vs = radyatör boyu × 5,7 l/m × 1,30; e(90°C)=0,0359; P0 = H/10+0,3; Psv 6 bar; Vn=(Ve+VWR)(Pe+1)/(Pe−P0).
- Denge kabı D = √(4Q/(π·0,15)); kazan dairesi havalandırma alt 6 cm²/kW, üst 3 cm²/kW.
Proje: İstanbul Güngören, 69 pafta 944 ada 343 parsel, B1-B2-B3 blok (aynı proje sıhhi hesapları: motor/hesaplar_sema).
