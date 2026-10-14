# -*- coding: utf-8 -*-
"""Sprinkler tasarım kuralları — kaynak: kutuphane/arastirma/06_YANGIN.md (TS EN 12845) + README kalıcı kuralları.
Değerler koda dağıtılmaz; diğer modüller buradan okur. Uzunluk birimi: cm (plan), hesap m / bar / l/dk."""

# §1.1 + §2.1 : yoğunluk (mm/dk), işletme alanı ıslak (m²), süre (dk), başlık başına en fazla alan (m²),
#               en fazla aralık S (cm), K, en uç başlıkta en düşük basınç (bar)
SINIF = {
    'LH':  dict(yog=2.25, alan=84.0,  sure=30, amax=21.0, smax=460.0, K=57.0, pmin=0.70),
    'OH1': dict(yog=5.0,  alan=72.0,  sure=60, amax=12.0, smax=400.0, K=80.0, pmin=0.35),
    'OH2': dict(yog=5.0,  alan=144.0, sure=60, amax=12.0, smax=400.0, K=80.0, pmin=0.35),
    'OH3': dict(yog=5.0,  alan=216.0, sure=60, amax=12.0, smax=400.0, K=80.0, pmin=0.35),
    'OH4': dict(yog=5.0,  alan=360.0, sure=60, amax=12.0, smax=400.0, K=80.0, pmin=0.35),
    'HHP1': dict(yog=7.5, alan=260.0, sure=90, amax=9.0,  smax=370.0, K=80.0, pmin=0.50),
    'HHP2': dict(yog=10.0, alan=260.0, sure=90, amax=9.0, smax=370.0, K=80.0, pmin=0.50),
    'HHP3': dict(yog=12.5, alan=260.0, sure=90, amax=9.0, smax=370.0, K=115.0, pmin=0.50),
}
SMIN = 200.0          # başlıklar arası en az (cm) — EN 12845
DUVAR_MAX = 200.0     # duvara en fazla (cm) — genel kural 2,0 m (S/2 ile birlikte kontrol)
DUVAR_MIN = 10.0      # duvara en az (cm) — pratik (⚠)
KOLON_PAY = 30.0      # başlık / branşman betonarme kolon yüzünden en az (cm) — kabul

# README kalıcı kuralı (Aselsan 02-Yangın): başlık sayısı -> çap
DN_TABLO = [(2, 25), (3, 32), (5, 40), (10, 50), (20, 65), (40, 80), (100, 100), (160, 125)]
# R2 (14.10.2026 B): DN125 kademesi eklendi (NFPA OH çizelgesi 5" = 160 başlık); > 160 başlık DN150.
# Standart kademe dizisi: şemada her ayrımda ana hat en fazla BİR kademe düşer (kademe.py).
DN_SERI = [25, 32, 40, 50, 65, 80, 100, 125, 150, 200]


def dn_sec(n):
    for m, dn in DN_TABLO:
        if n <= m:
            return dn
    return 150


# TS EN 10255 orta seri iç çaplar (mm) — motor/voyap/hidro.py ile aynı
IC_CAP = {25: 27.3, 32: 36.0, 40: 41.9, 50: 53.1, 65: 68.9, 80: 80.9, 100: 105.3, 125: 130.0, 150: 155.4}   # 125: EN 10255 139,7x4,85 ⚠

# Eşdeğer boy (m), C=120 — EN 12845 Tablo 38 (⚠ değerler standart metninden doğrulanmalı)
ES_DIRSEK = {25: 0.76, 32: 1.0, 40: 1.2, 50: 1.5, 65: 1.9, 80: 2.4, 100: 3.0, 125: 3.7, 150: 4.3}   # 125 ara değer ⚠
ES_TE = {25: 1.5, 32: 2.1, 40: 2.4, 50: 3.0, 65: 3.9, 80: 4.8, 100: 6.1, 125: 7.4, 150: 8.6}

HW_C = 120.0
V_MAX = 10.0          # m/s, boru (vana ve akış anahtarında 6 m/s)
V_MAX_VANA = 6.0


def hw_birim(q_lpm, dn, C=HW_C):
    """Hazen-Williams birim kayıp (bar/m): p = 6,05e5 · Q^1,85 / (C^1,85 · d^4,87); Q l/dk, d mm (06 §3.3)"""
    if q_lpm <= 0:
        return 0.0
    d = IC_CAP[dn]
    return 6.05e5 * q_lpm ** 1.85 / (C ** 1.85 * d ** 4.87)


def hiz(q_lpm, dn):
    d = IC_CAP[dn] / 1000.0
    return (q_lpm / 60000.0) / (3.14159265 * d * d / 4.0)
