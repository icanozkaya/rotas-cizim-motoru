"""Duvar tipi split klima: ısı kazancı (CLTD/SHGF basit yöntem, TS 2164 / ASHRAE esaslı) + ısıtma kontrolü,
cihaz seçimi ve plan sembolleri (iç ünite, dış ünite, bakır boru, drenaj)."""
import math, sys
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import cad
from cad import L, PL, C, T, RECT, ARC
import gp

# Sakarya (Adapazarı) yaz tasarım şartları
T_YAZ_DIS, T_YAZ_YAS, T_YAZ_IC, RH_IC = 34.0, 24.0, 26.0, 50
import psychrolib as _ps                 # MIT, github.com/psychrometrics/psychrolib (ASHRAE Fundamentals denklemleri)
_ps.SetUnitSystem(_ps.SI)
P_ATM = _ps.GetStandardAtmPressure(31.0)            # Adapazarı rakım ≈ 31 m
W_DIS = _ps.GetHumRatioFromTWetBulb(T_YAZ_DIS, T_YAZ_YAS, P_ATM)   # kg/kg
W_IC = _ps.GetHumRatioFromRelHum(T_YAZ_IC, RH_IC / 100.0, P_ATM)
CLTD = {'G': 10.0, 'D': 13.0, 'B': 15.0, 'K': 6.0, 'GD': 11.0, 'GB': 13.0, 'KD': 9.0, 'KB': 10.0}   # orta renk duvar
SHG = {'G': 150.0, 'D': 420.0, 'B': 450.0, 'K': 75.0, 'GD': 300.0, 'GB': 330.0, 'KD': 250.0, 'KB': 260.0}  # W/m² maks. güneş
SC_CAM = 0.55                          # Low-E ısıcam gölgeleme katsayısı
CLF_CAM = 0.80                         # soğutma yük faktörü (camdan)
U_DUVAR, U_CAM = 0.40, 1.80
KISI_M2 = 8.0                          # dükkan: 8 m² / kişi
Q_KISI_D, Q_KISI_G = 75.0, 55.0        # W/kişi duyulur / gizli (hafif iş, ayakta)
AYD_W, CIH_W = 12.0, 8.0               # W/m² aydınlatma, cihaz
TAZE_LS = 8.0                          # l/s.kişi taze hava
EMNIYET = 1.10
SPLIT = [(9000, 2.64), (12000, 3.52), (18000, 5.28), (24000, 7.03)]   # BTU/h, kW


def kazanc(S):
    """S: dict(name, A, ext=[(yön, uzunluk, [(w,h,n,tip)])], H) -> satırlar ve toplam"""
    H = S.get('H', 2.50)
    rows = []
    for yon, l, wins in S['ext']:
        Ac = sum(w * h * n for w, h, n, _ in wins)
        Ad = l * H - Ac
        rows.append(('Duvar iletim', yon, Ad, U_DUVAR, CLTD[yon], Ad * U_DUVAR * CLTD[yon]))
        if Ac > 0:
            rows.append(('Cam iletim', yon, Ac, U_CAM, T_YAZ_DIS - T_YAZ_IC, Ac * U_CAM * (T_YAZ_DIS - T_YAZ_IC)))
            rows.append(('Cam güneş', yon, Ac, SC_CAM * CLF_CAM, SHG[yon], Ac * SHG[yon] * SC_CAM * CLF_CAM))
    n = max(1, math.ceil(S['A'] / KISI_M2))
    rows.append(('İnsan duyulur', '', n, 1, Q_KISI_D, n * Q_KISI_D))
    rows.append(('Aydınlatma', '', S['A'], 1, AYD_W, S['A'] * AYD_W))
    rows.append(('Cihaz / ekipman', '', S['A'], 1, CIH_W, S['A'] * CIH_W))
    V = n * TAZE_LS / 1000.0
    rows.append(('Taze hava duyulur', '', V, 1.2 * 1006, T_YAZ_DIS - T_YAZ_IC, V * 1.2 * 1006 * (T_YAZ_DIS - T_YAZ_IC)))
    Qd = sum(r[5] for r in rows)
    gl = [('İnsan gizli', '', n, 1, Q_KISI_G, n * Q_KISI_G),
          ('Taze hava gizli', '', V, 1.2 * 2501e3, W_DIS - W_IC, V * 1.2 * 2501e3 * (W_DIS - W_IC))]
    Qg = sum(r[5] for r in gl)
    Q = (Qd + Qg) * EMNIYET
    return dict(name=S['name'], A=S['A'], n=n, rows=rows, gl=gl, Qd=Qd, Qg=Qg, Q=Q, SHR=Qd / (Qd + Qg))


def sec(Qsog, Qisi):
    """1 veya 2 adet eşit duvar tipi split; kapasite hem soğutma hem ısıtma (ısıtma ≈ 1,1 x soğutma) karşılanır"""
    need = max(Qsog, Qisi / 1.1) / 1000.0
    for adet in ((1,) if need <= 5.28 else (2,)):
        for btu, kw in SPLIT:
            if kw * adet >= need:
                return adet, btu, kw
    return 2, 24000, 7.03


# ------------------------------------------------------------------ semboller
LIC, LDIS, LBAK, LDRN = 'MTY-KLIMA-IC UNITE', 'MTY-KLIMA-DIS UNITE', 'MTY-KLIMA-BAKIR BORU', 'MTY-KLIMA-DRENAJ'
LAYERS = {LIC: (4, 'CONTINUOUS'), LDIS: (4, 'CONTINUOUS'), LBAK: (30, 'CONTINUOUS'), LDRN: (8, 'DASHED')}
gp.EXTRA_LAYERS.update(LAYERS)
gp.WIDTH.update({LBAK: 1.5, LDRN: 1.2})


def _xf(o, rot):
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    return lambda x, y: (o[0] + x * ca - y * sa, o[1] + x * sa + y * ca)


def ic_unite(o, rot, btu, w=90.0):
    """duvar tipi iç ünite planı: o = duvar yüzü orta noktası, rot 0 -> güney duvarında kuzeye üfler"""
    f = _xf(o, rot)
    d = 22.0 if btu <= 12000 else 25.0
    PL([f(-w / 2, 0), f(w / 2, 0), f(w / 2, d - 4), f(w / 2 - 4, d), f(-w / 2 + 4, d), f(-w / 2, d - 4)], LIC, closed=True, w=1.2)
    L(f(-w / 2 + 6, d - 7), f(w / 2 - 6, d - 7), LIC)        # üfleme kanadı
    for i in range(5):
        x = -w / 2 + 12 + i * (w - 24) / 4.0
        L(f(x, d - 7), f(x + 3, d - 2), LIC)
    for s in (-1, 1):                                    # üfleme okları
        L(f(s * 20, d + 4), f(s * 24, d + 34), LIC)
        cad.ARROW(f(s * 24, d + 34), rot + 90 + s * -7.6, LIC, 7)
    return f(-w / 2 + 8, 2), f(-w / 2 + 14, 2)        # bakır ve drenaj çıkışı


def dis_unite(o, rot, w=80.0, d=30.0):
    """dış ünite (konsol üzerinde): o = dış duvar yüzü orta noktası, rot 0 -> cephe güneyde, ünite +y"""
    f = _xf(o, rot)
    PL([f(-w / 2, 4), f(w / 2, 4), f(w / 2, 4 + d), f(-w / 2, 4 + d)], LDIS, closed=True, w=1.5)
    cx, cy = f(-w / 2 + d / 2 + 6, 4 + d / 2)
    C((cx, cy), d / 2 - 3, LDIS); C((cx, cy), 3, LDIS)
    for a in (0, 120, 240):
        r = math.radians(a + rot)
        L((cx, cy), (cx + (d / 2 - 5) * math.cos(r), cy + (d / 2 - 5) * math.sin(r)), LDIS)
    for i in range(4):
        L(f(w / 2 - 22 + i * 5, 8), f(w / 2 - 22 + i * 5, d), LDIS)
    for s in (-1, 1):                                    # konsol
        L(f(s * (w / 2 - 6), 0), f(s * (w / 2 - 6), 4), LDIS)
    return f(w / 2 - 8, 4)
