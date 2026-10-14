# -*- coding: utf-8 -*-
"""Çift borulu sıcak su ısıtma: boru çapı (Darcy-Weisbach + Colebrook), yerel kayıp, kritik devre, pompa.
Birimler: Q [W], L [m], R [mmSS/m], R·L ve Z [mmSS] (TS 2164 / tesisat.org çizelge düzeni)."""
import math

G = 9.80665
# Siyah çelik boru TS EN 10255 orta seri: DN -> (inç, iç çap mm)
BORU = [('DN15', '1/2"', 16.1), ('DN20', '3/4"', 21.7), ('DN25', '1"', 27.3), ('DN32', '1 1/4"', 36.0),
        ('DN40', '1 1/2"', 41.9), ('DN50', '2"', 53.1), ('DN65', '2 1/2"', 68.9), ('DN80', '3"', 80.9),
        ('DN100', '4"', 105.3)]


def su(tort):
    """ortalama sıcaklıkta su: yoğunluk kg/m3, cp kJ/kgK, kinematik viskozite m2/s (80 °C civarı doğrusal yaklaşım)"""
    rho = 1000.0 - 0.0035 * (tort - 4) ** 2 if tort < 30 else 971.8 + (80 - tort) * 0.62
    nu = 0.365e-6 * (1 + (80 - tort) * 0.022)
    return rho, 4.197, nu


def debi(Q, dT, tort):
    rho, cp, nu = su(tort)
    m = Q / 1000.0 / (cp * dT)            # kg/s
    return m, m / rho                     # kg/s, m3/s


def R_hesap(Vs, di_mm, tort, eps_mm=0.045):
    """birim sürtünme kaybı (mmSS/m) ve hız (m/s)"""
    rho, cp, nu = su(tort)
    d = di_mm / 1000.0
    A = math.pi * d * d / 4
    w = Vs / A
    if w <= 0:
        return 0.0, 0.0
    Re = w * d / nu
    if Re < 2300:
        lam = 64.0 / Re
    else:
        lam = 0.02
        for _ in range(30):
            lam = (-2.0 * math.log10(eps_mm / 1000.0 / d / 3.71 + 2.51 / (Re * math.sqrt(lam)))) ** -2
    R_pa = lam / d * rho * w * w / 2
    return R_pa / G, w


def cap_sec(Q, dT, tort, Rmax, wmax, dnmin='DN15'):
    """R ≤ Rmax (mmSS/m) ve w ≤ wmax koşulunu sağlayan en küçük çap"""
    m, Vs = debi(Q, dT, tort)
    basla = [b[0] for b in BORU].index(dnmin)
    for dn, inc, di in BORU[basla:]:
        R, w = R_hesap(Vs, di, tort)
        if R <= Rmax and w <= wmax:
            return dict(dn=dn, inc=inc, di=di, R=R, w=w, m=m, V=Vs * 3600)
    dn, inc, di = BORU[-1]
    R, w = R_hesap(Vs, di, tort)
    return dict(dn=dn, inc=inc, di=di, R=R, w=w, m=m, V=Vs * 3600)


def Z_hesap(zeta, w, tort):
    rho, _, _ = su(tort)
    return zeta * rho * w * w / 2 / G      # mmSS


# PE-Xc/Al/PE-X çok katmanlı boru: ad -> iç çap mm (daire içi devreler ve kolektör besleme hattı)
PEX = [('Ø16x2', '16x2', 12.0), ('Ø20x2', '20x2', 16.0), ('Ø26x3', '26x3', 20.0), ('Ø32x3', '32x3', 26.0),
       ('Ø40x3,5', '40x3,5', 33.0), ('Ø50x4', '50x4', 42.0)]


def cap_sec_pex(Q, dT, tort, Rmax, wmax, minimum='Ø16x2'):
    m, Vs = debi(Q, dT, tort)
    basla = [b[0] for b in PEX].index(minimum)
    for dn, inc, di in PEX[basla:]:
        R, w = R_hesap(Vs, di, tort, eps_mm=0.007)
        if R <= Rmax and w <= wmax:
            return dict(dn=dn, inc=inc, di=di, R=R, w=w, m=m, V=Vs * 3600)
    dn, inc, di = PEX[-1]
    R, w = R_hesap(Vs, di, tort, eps_mm=0.007)
    return dict(dn=dn, inc=inc, di=di, R=R, w=w, m=m, V=Vs * 3600)
