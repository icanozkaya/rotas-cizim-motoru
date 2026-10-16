# -*- coding: utf-8 -*-
"""siginak/debi.py — sığınak havalandırma debileri (kullanıcı kuralı, 16.10.2026 19:11).

Taze hava KİŞİ SAYISINA göre tasarlanır, egzoz ona orantılıdır:
    kişi sayısı  = brüt alan (m²) / 1 m² kişi⁻¹   (yukarı yuvarlanır)
    kişi başı    = ≤50 kişi 1,8 · 51–150 kişi 3,0 · >150 kişi 4,5 m³/h·kişi (kademe toplam kişi sayısına göre)
    taze hava    = kişi × kişi başı → 100'e yukarı yuvarlanır
    egzoz        = taze hava × 0,90 (taze havanın %10 aşağısı)
    duman tahliye = alan > 100 m² ise hacim × 10 /h → 500'e yukarı (değişmedi)
Eski kural (hacim × 4 /h) 16.10.2026'dan önceki projelerde kaldı; yeni projeler bu modülü kullanır.
"""
import math


# kanal / duvar-döşeme geçişi hız sınırları (m/s) — kullanıcı 16.10.2026: duman tahliye 11–12 m/s, taze/egzoz ≤ 8 m/s
HIZ = {'taze': 8.0, 'egzoz': 8.0, 'duman': 12.0}
HIZ_DUMAN_ALT = 11.0


def kisi_basi(kisi):
    return 1.8 if kisi <= 50 else 3.0 if kisi <= 150 else 4.5


def sigınak_debileri(brut_alan, yukseklik):
    kisi = math.ceil(brut_alan / 1.0 - 1e-9)
    q = kisi * kisi_basi(kisi)
    taze = int(math.ceil(q / 100.0) * 100)
    egzoz = int(round(taze * 0.90))
    duman = int(math.ceil(brut_alan * yukseklik * 10 / 500.0) * 500) if brut_alan > 100 else 0
    return dict(kisi=kisi, kisi_basi=kisi_basi(kisi), taze_hesap=q, taze=taze, egzoz=egzoz, duman=duman)


siginak_debileri = sigınak_debileri


if __name__ == '__main__':
    print(siginak_debileri(428.84, 2.95))
