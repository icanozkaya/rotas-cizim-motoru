"""Daire bazında yerden ısıtma hidroliği: kombi pompası kontrolü, kapalı genleşme tankı, PEX kangal metrajı.

Kaynaklar (GitHub araştırması 11.10.2026, ikisi de MIT lisanslı; kod birebir alınmadı, yöntem uyarlandı):
- TomLXXVI/python-hvac  hvac/hydronics/expansion_tank.py  (membranlı genleşme tankı: Vmin = (P2+Patm)/(P2-P1) x (Vdolum + ΔVgenleşme))
- TomLXXVI/python-hvac  hvac/fluid_flow/conduit/conduit.py (Churchill sürtünme katsayısı)
- egmalt/house-planner   src/networks/heating/calc.ts      (yerel kayıp çarpanı 1,3; kollektör+vana 5 kPa; 200/500 m kangal paketleme)
"""
import math

RHO, NU = 992.0, 0.66e-6          # su, 40 °C
D_I = 0.012                        # PEX 16x2,0 iç çap (m)
LOKAL = 1.3                        # dirsek, kollektör bağlantısı vb. yerel kayıplar çarpanı
DP_KOLL = 5.0                      # kPa: kollektör + debimetre + vana
KOMBI_POMPA_KPA = 25.0             # 24 kW kombi pompası, ~1000 l/h'de kullanılabilir basma (katalogdan teyit edilir)
KOMBI_TANK_L = 8.0                 # kombi içi genleşme tankı
PATM = 1.013


def churchill(Re, e_rel=0.007e-3 / D_I):
    if Re <= 0:
        return 0.0
    d = (7.0 / Re) ** 0.9 + 0.27 * e_rel
    A = (2.457 * math.log(1.0 / d)) ** 16
    B = (37530.0 / Re) ** 16
    return 8.0 * ((8.0 / Re) ** 12 + 1.0 / (A + B) ** 1.5) ** (1.0 / 12.0)


def devre(W, L, dT=10.0):
    """W: devre yükü (W), L: devre boyu (m) -> debi l/h, hız m/s, basınç kaybı kPa"""
    q_lh = W / (1.163 * dT)
    v = q_lh / 3.6e6 / (math.pi * D_I ** 2 / 4)
    Re = v * D_I / NU
    lam = churchill(Re)
    dp = lam * L / D_I * RHO * v * v / 2.0 * LOKAL / 1000.0
    return dict(q=q_lh, v=v, Re=Re, dp=dp)


def rho(T):
    """suyun yoğunluğu kg/m³ (0-100 °C, Kell bağıntısı)"""
    return (999.83952 + 16.945176 * T - 7.9870401e-3 * T ** 2 - 46.170461e-6 * T ** 3 + 105.56302e-9 * T ** 4
            - 280.54253e-12 * T ** 5) / (1 + 16.879850e-3 * T)


def genlesme(V_l, T_soguk=10.0, T_sicak=50.0, h_m=1.5, P_emn=3.0):
    """V_l: sistem su hacmi (l). Membranlı tank minimum hacmi ve dolum basıncı (bar)."""
    dV = (rho(T_soguk) / rho(T_sicak) - 1.0) * V_l
    Vd = 0.01 * V_l                                    # dolum sırasında alınan %1
    P1 = max(0.5, RHO * 9.81 * h_m / 1e5 + 0.3)        # ön basınç
    P2 = P_emn - 0.5                                   # emniyet ventili - 0,5 bar
    Vmin = (P2 + PATM) / (P2 - P1) * (Vd + dV)
    return dict(V=V_l, dV=dV, P1=P1, P2=P2, Vmin=Vmin, ok=Vmin <= KOMBI_TANK_L)


def _ffd(ls, cap):
    bins = []
    for l in sorted(ls, reverse=True):
        for b in bins:
            if sum(b) + l <= cap:
                b.append(l)
                break
        else:
            bins.append([l])
    return bins


def kangal(ls):
    """devre boyları (m) -> 200 m ve 500 m kangal adedi (devre ortasında ek yapılmaz)"""
    c500 = c200 = 0
    for b in _ffd(ls, 500.0):
        small = len(_ffd(b, 200.0)) if all(l <= 200 for l in b) else 99
        if small * 200 < 500:
            c200 += small
        else:
            c500 += 1
    return c200, c500


def daire(circ, ek_boru_m=6.0):
    """circ: [{'W','L',...}] -> daire özeti"""
    rs = [dict(d, **devre(d['W'], d['L'])) for d in circ]
    dpmax = max(r['dp'] for r in rs)
    Q = sum(r['q'] for r in rs)
    H = dpmax + DP_KOLL
    L = sum(d['L'] for d in circ)
    V = L * math.pi * D_I ** 2 / 4 * 1000 + 2.0 + 1.0 + ek_boru_m * 0.33   # PEX + kombi eşanjör + kollektör + DN20 bağlantı
    g = genlesme(V)
    c200, c500 = kangal([d['L'] for d in circ])
    return dict(devreler=rs, Q=Q, dpmax=dpmax, H=H, H_m=H / 9.81, pompa_ok=H <= KOMBI_POMPA_KPA, L=L, gen=g,
                kangal200=c200, kangal500=c500, W=sum(d['W'] for d in circ))
