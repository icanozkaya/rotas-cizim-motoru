# -*- coding: utf-8 -*-
"""OBA Makarnacılık 900 ada 84 parsel depolama binası — yangın tesisatı yerleşimi ve hesapları.

Birim cm (çizim), m (hesap). Mimari plan koordinatları (OBA__84_PARSEL_15_09_2026__MİMARİ.dwg zemin kat planı).
Kullanıcı seçimleri: HHS (depolama yüksek tehlike), paletli blok istif (ST1) ≤ 4 m, K160 dik başlık,
bina dışı toprak altı depo + pompa dairesi, duman tahliye 2 seçenek.
"""
import math
from hhs_hidrolik import Ag, hiz, dp_m, IC

# ------------------------------------------------------------------ mimari (aks) — İLK İŞ: kolon hatları
AX = [185409 + 600 * i for i in range(25)]                    # 1..25
AY = {'A': 8256, 'B': 10656, 'C': 13056, 'D': 15456}
X0, X1, Y0, Y1 = AX[0], AX[-1], AY['A'], AY['D']
CEP = 30                                                        # cephe kaplaması aks dışı (yaklaşık)
IC_KOLON = [(AX[i], AY[r]) for i in range(2, 23, 2) for r in 'BC']   # iç kolonlar (tek akslar 3..23)
TEKNIK = (AX[22], AY['A'], AX[24], 11867)                       # teknik depo bölümü (aks 23-25)
MAHYA_Y = (Y0 + Y1) / 2
KOT_SACAK, EGIM = 12.23, 0.07


def z_cati(y):
    """başlık / branşman kotu (m): çatı altı - 0,30 (çatı %7, saçak +12,23 → mahya +14,75)"""
    return KOT_SACAK - 0.30 + EGIM * min(y - Y0, Y1 - y) / 100.0


# ------------------------------------------------------------------ tasarım kriterleri (TS EN 12845 HHS)
TASARIM = dict(
    sinif='HHS — Yüksek Tehlike Depolama (TS EN 12845 Çizelge 4, ST1 serbest/blok istif)',
    istif='Paletli blok istif (ST1), istif yüksekliği ≤ 4,0 m, ürün kategorisi II (ambalajlı gıda/makarna)',
    yogunluk=10.0,          # mm/dk (Kat. II ST1 4,1 m: 7,5 mm/dk → güvenli tarafta 10,0 mm/dk alındı)
    alan=260.0,             # m² işletme alanı (ıslak sistem)
    sure=90,                # dk
    K=160, Pmin=0.5,        # bar (HH en az 0,5 bar)
    A_bas=9.0, S_max=3.7,   # m² / m
    sicaklik='68 °C (yangın sınıfı ısıl ampul)',
    ilave_dolap=200.0,      # l/dk (2 dolap x 100 l/dk eşzamanlı)
    ilave_hidrant=1900.0,   # l/dk (BYKHY Md.95: hidrant ≥ 1900 l/dk, çıkışta 7 bar)
)

# ------------------------------------------------------------------ sprinkler yerleşimi
BR_X = [AX[i] + d for i in range(24) for d in (150, 450)]      # 48 branşman (çerçeve aksları arası 2 hat)
BAS_Y = [Y0 + 150 + 300 * k for k in range(24)]                 # 24 başlık / hat
Y_AB = AY['B'] + 80                                             # B ana dağıtım (kolon yüzü yanında)
Y_AC = AY['C'] + 80                                             # C ana dağıtım
X_F = {1: AX[12] - 100, 2: AX[12] + 100}                        # zon besleme hatları (aks 13 yanında)
ZON_BR = {1: [x for x in BR_X if x < AX[12]], 2: [x for x in BR_X if x > AX[12]]}


def bolge(ad):
    """B ana dağıtımı mahyanın A tarafını, C ana dağıtımı D tarafını besler"""
    return [y for y in BAS_Y if (y < MAHYA_Y) == (ad == 'B')]


def dn_br(n):
    return 32 if n <= 1 else 40 if n == 2 else 50 if n <= 4 else 65


# ------------------------------------------------------------------ dış yerleşim (pompa dairesi, depo, hidrant)
POMPA = (AX[12] - 900, Y1 + 1500, AX[12] + 500, Y1 + 2500)      # pompa dairesi iç ölçü 14,0 x 10,0 m (toprak altı)
DUV = 40
HID_Y_UST, HID_Y_ALT = Y1 + 800, Y0 - 800                        # hidrant halkası (cepheden ~7,7 m)
HID_X_SOL, HID_X_SAG = X0 - 800, X1 + 800
HIDRANTLAR = ([(AX[i], HID_Y_UST) for i in (1, 8, 16, 23)] + [(AX[i], HID_Y_ALT) for i in (1, 8, 16, 23)] +
              [(HID_X_SOL, y) for y in (9856, 13856)] + [(HID_X_SAG, y) for y in (9856, 13856)])
# yangın dolapları: iç kolonlara (B ve C sırası, aks 3-7-11-15-19-23)
DOLAP_AKS = [2, 6, 10, 14, 18, 22]
DOLAPLAR = [(AX[i], AY[r], r) for r in 'BC' for i in DOLAP_AKS]      # dolap kolonun +x yüzünde (kaide 100x100)
Y_DOLAP = {'B': AY['B'] - 80, 'C': AY['C'] - 80}                   # dolap hattı (+4,50), kolon yüzünden 30 cm


# ------------------------------------------------------------------ sprinkler hidroliği
def ag_kur(zon=1, cap_ana=None):
    """zon ağını kur. Kök: pompa çıkışı (POMPA). Dönüş Ag ve başlık konumları"""
    cap_ana = cap_ana or {}
    g = Ag()
    zp = -3.60                                     # pompa ekseni (pompa dairesi taban -4,00)
    xf = X_F[zon]
    g.dugum('POMPA', zp)
    g.dugum('KOLL', zp + 0.9); g.kenar('POMPA', 'KOLL', 2.0, 250, 1, 1)
    g.dugum('AV', zp + 1.2); g.kenar('KOLL', 'AV', 3.0, 200, 1, 1, ek_bar=0.40)   # alarm vana seti + 2 kelebek
    g.dugum('CIK', -1.20); g.kenar('AV', 'CIK', 6.0, 200, 2, 0)
    g.dugum('BINA', -1.20); g.kenar('CIK', 'BINA', (POMPA[1] - Y1 - CEP) / 100, 200, 0, 0)
    zr = z_cati(Y1 - 60)
    g.dugum('KT', zr); g.kenar('BINA', 'KT', 1.0 + zr + 1.2, 200, 2, 0)      # kolon (riser) üstü
    yol = {}
    onceki, yon = 'KT', Y1 - 60
    for ad, ya in (('C', Y_AC), ('B', Y_AB)):
        n = 'F' + ad
        g.dugum(n, z_cati(ya)); g.kenar(onceki, n, (yon - ya) / 100, 200, 0, 0)
        onceki, yon = n, ya
        # ana dağıtım: besleme hattından uzağa
        xs = sorted(ZON_BR[zon], key=lambda x: abs(x - xf))
        u, xu = n, xf
        for j, xb in enumerate(xs):
            m = f'M{ad}{j}'
            g.dugum(m, z_cati(ya))
            dn = cap_ana.get(j, 150)
            g.kenar(u, m, abs(xb - xu) / 100, dn, 0, 1 if j == 0 else 0)
            u, xu = m, xb
            # branşman iki yöne
            ust = [y for y in bolge(ad) if y > ya]
            alt = [y for y in bolge(ad) if y < ya]
            for kol, ys in (('u', sorted(ust)), ('a', sorted(alt, reverse=True))):
                if not ys:
                    continue
                p, yp = m, ya
                n_t = len(ys)
                for k, yh in enumerate(ys):
                    h = f'H{ad}{j}{kol}{k}'
                    g.dugum(h, z_cati(yh))
                    g.kenar(p, h, abs(yh - yp) / 100, dn_br(n_t - k), 0, 1 if k == 0 else 0)
                    g.bas(h, TASARIM['K'])
                    yol[h] = (xb, yh)
                    p, yp = h, yh
    return g, yol


def alan_sec(yol, x_uzak, y_uzak, n=29, uzun=7):
    """dikdörtgen işletme alanı: uzun kenar branşmana paralel (uzun x başlık), uç köşeden başlayarak"""
    xs = sorted({p[0] for p in yol.values()}, key=lambda x: abs(x - x_uzak))
    ys = sorted({p[1] for p in yol.values()}, key=lambda y: abs(y - y_uzak))
    sec = []
    for xb in xs:
        for yh in ys[:uzun]:
            if len(sec) < n:
                sec.append((xb, yh))
    ters = {v: k for k, v in yol.items()}
    return [ters[p] for p in sec if p in ters]


def sprinkler_hesap(cap_ana=None):
    g, yol = ag_kur(1, cap_ana)
    T = TASARIM
    nA = math.ceil(T['alan'] / T['A_bas'])
    # en uzak: zon-1, aks 1 ucu, A cephesi (B ana dağıtımın 8 başlıklı tarafı)
    uzak = alan_sec({k: v for k, v in yol.items() if k.startswith('HB') and 'a' in k}, BR_X[0], BAS_Y[0], nA)
    P0, P, Qk, Qb = g.kaynak_bul(uzak, T['Pmin'])
    Qs = sum(Qb.values())
    # en yakın (en elverişli) alan: C ana dağıtım, besleme hattına en yakın branşmanlar, D tarafı
    yakin = alan_sec({k: v for k, v in yol.items() if k.startswith('HC') and 'u' in k}, X_F[1] - 50, Y_AC, nA)
    Pf, Qkf, Qbf = g.coz(yakin, P0)
    # yoğunluk kontrolü
    q_min = min(Qb.values())
    yog = q_min / T['A_bas']
    # kenar tablosu (uzak alan yolu)
    tablo = []
    for i, (u, a, L, dn, nd, nt, ek) in enumerate(g.k):
        if Qk[i] > 0.01:
            tablo.append(dict(u=u, a=a, L=L, dn=dn, nd=nd, nt=nt, Q=Qk[i], v=hiz(Qk[i], dn),
                              j=dp_m(Qk[i], dn), dP=P[u] - P[a], Pu=P[u], Pa=P[a], z=g.z[a] - g.z[u], ek=ek))
    return dict(g=g, yol=yol, uzak=uzak, yakin=yakin, P0=P0, P=P, Qk=Qk, Qb=Qb, Qs=Qs, Qf=sum(Qbf.values()),
                Pf=Pf, q_min=q_min, yog=yog, nA=nA, tablo=tablo, alan=nA * T['A_bas'])


# ------------------------------------------------------------------ hidrant / dolap / depo / pompa
def halka_boy():
    return 2 * ((HID_X_SAG - HID_X_SOL) + (HID_Y_UST - HID_Y_ALT)) / 100


def hidrant_hesap():
    Q = TASARIM['ilave_hidrant']
    L_halka = halka_boy()
    # giriş: pompa dairesinden halka üst kenarına; en uzak hidrant karşı (alt) kenarda — debi iki koldan yarı yarıya
    L_yol = L_halka / 2 + (POMPA[1] - HID_Y_UST) / 100 + 4.0
    j = dp_m(Q / 2, 150)
    dP_halka = j * (L_yol + 6 * 8.6)
    dP_bag = dp_m(Q, 150) * 10 + dp_m(Q, 100) * (3 + 2 * 3.0) + 0.30     # pompa dairesi içi + hidrant kolu + vana
    z = 0.80 - (-3.60)
    P_pompa = 7.0 + dP_halka + dP_bag + 0.0981 * z
    return dict(Q=Q, L_halka=L_halka, L_yol=L_yol, dP_halka=dP_halka, dP_bag=dP_bag, z=z, P_pompa=P_pompa,
                v_halka=hiz(Q / 2, 150), n=len(HIDRANTLAR))


def dolap_hesap():
    q, n = 100.0, 2
    Q = q * n
    # halka (batı) → B sırası dolap hattı → en uzak iki dolap (aks 19 ve 23)
    L = (X0 - HID_X_SOL) / 100 + (AX[22] - X0) / 100 + 6.0
    dP = dp_m(Q, 80) * (L + 4 * 2.4) + dp_m(q, 50) * (4.0 + 2 * 1.5) + 0.20
    z = 1.50 - 0.0
    return dict(q=q, n=n, Q=Q, L=L, dP=dP, z=z, P_gerek=4.0 + dP + 0.0981 * z, dn_hat=80, dn_dolap=50,
                v=hiz(Q, 80))


def ozet():
    S = sprinkler_hesap()
    H = hidrant_hesap()
    D = dolap_hesap()
    T = TASARIM
    Q_top = S['Qs'] + T['ilave_dolap'] + T['ilave_hidrant']            # l/dk
    P_ihtiyac = max(S['P0'], H['P_pompa'])                             # bar (pompa çıkışı)
    Qm3 = Q_top * 60 / 1000
    Q_sec = math.ceil(Qm3 / 10) * 10
    H_sec = math.ceil(P_ihtiyac * 10.2 / 5) * 5 + 5
    eta = 0.74
    P_mil = 1000 * 9.81 * (Q_sec / 3600) * H_sec / eta / 1000
    motor = next(m for m in (75, 90, 110, 132, 160, 200, 250, 315) if m >= P_mil * 1.10)
    dizel = next(m for m in (90, 110, 132, 160, 200, 250, 315, 355) if m >= P_mil * 1.20)
    V = Q_top * T['sure'] / 1000                                       # m³
    V_sec = math.ceil(V / 10) * 10
    return dict(S=S, H=H, D=D, Q_top=Q_top, Qm3=Qm3, Q_sec=Q_sec, P_ihtiyac=P_ihtiyac, H_sec=H_sec,
                P_mil=P_mil, motor=motor, dizel=dizel, V=V, V_sec=V_sec, dolum=V_sec / 36.0,
                jokey=dict(Q=6, H=H_sec + 10, P=5.5))


if __name__ == '__main__':
    o = ozet()
    S = o['S']
    print('başlık/zon', sum(len(ZON_BR[1]) for _ in [0]) * 24, 'toplam', len(BR_X) * 24)
    print('uzak alan', S['nA'], 'başlık', round(S['alan']), 'm²  P0=%.2f bar  Qs=%.0f l/dk  qmin=%.1f yoğ=%.2f' %
          (S['P0'], S['Qs'], S['q_min'], S['yog']))
    print('elverişli alan Q=%.0f' % S['Qf'])
    print('hidrant', {k: round(v, 2) if isinstance(v, float) else v for k, v in o['H'].items()})
    print('dolap', {k: round(v, 2) if isinstance(v, float) else v for k, v in o['D'].items()})
    print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in o.items() if k not in 'SHD'})
    for t in S['tablo'][:14]:
        print(t['u'], t['a'], round(t['L'], 1), t['dn'], round(t['Q']), round(t['v'], 2), round(t['dP'], 3), round(t['Pa'], 2))
