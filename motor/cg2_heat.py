"""Cafer Göktaş - ısı kaybı verisi (örnek 'yerden ısıtma' şablonu yöntemi; TS 825:2024 uyumlu U değerleri).

Yöntem (şablonla aynı):
  Q = A.U.ΔT ; Z = 1+(ZD+ZW+ZH)/100 ; Qs = a.L.R.H.ΔT.Ze (a=2, R=0.9, H=0.67)
"""
import math

T_DIS = -6.0          # Sakarya - kullanıcının Sakarya ısı kaybı şablonundaki değer (rüzgarlı)
T_TOPRAK = 6.0
T_CATI = 0.0          # çatı arası (örnek şablon teknik raporu)
T_HOL = 10.0          # ısıtılmayan merdiven holü
T_ASANSOR = 5.0       # asansör kuyusu (ısıtılmayan)
T_KOMSU = 5.0         # bitişik komşu bina (ısıtılmıyor kabulü - emniyetli taraf)
KAT_H = 3.00          # kat yüksekliği (+1.00 / +4.00 / +7.00)
KIRIS_H = 0.50        # kiriş bandı yüksekliği (kabul)
DUVAR_H = KAT_H - KIRIS_H

# ------------------------------------------------------------------ yapı bileşenleri (TS 825:2024, 2./3. bölge sınırları:
# duvar 0.40, tavan/çatı 0.30, döşeme 0.35, pencere 1.8 W/m²K)
def _u(layers, rsi, rse):
    return 1.0 / (rsi + sum(d / l for d, l in layers) + rse)

ASSY = {
    'DD':   ('Dış duvar: 2 cm iç sıva + 19 cm yatay delikli tuğla + 8 cm EPS (λ=0,035) + 0,8 cm dış sıva',
             [(0.02, 1.0), (0.19, 0.45), (0.08, 0.035), (0.008, 0.7)], 0.13, 0.04, 0.40),
    'DD25': ('Kiriş (dış): 2 cm sıva + 25 cm betonarme + 8 cm EPS + dış sıva',
             [(0.02, 1.0), (0.25, 2.5), (0.08, 0.035), (0.008, 0.7)], 0.13, 0.04, 0.40),
    'DD30': ('Kolon (dış): 2 cm sıva + 30 cm betonarme + 8 cm EPS + dış sıva',
             [(0.02, 1.0), (0.30, 2.5), (0.08, 0.035), (0.008, 0.7)], 0.13, 0.04, 0.40),
    'İDM':  ('Merdiven holü / komşu bina duvarı: sıva + 19 cm tuğla + 8 cm EPS + sıva',
             [(0.02, 1.0), (0.19, 0.45), (0.08, 0.035), (0.02, 1.0)], 0.13, 0.13, 0.40),
    'İDA':  ('Asansör kuyusu perdesi: sıva + 20 cm betonarme + 8 cm EPS + sıva',
             [(0.02, 1.0), (0.20, 2.5), (0.08, 0.035), (0.02, 1.0)], 0.13, 0.13, 0.40),
    'Ta':   ('Tavan (çatı arası altı): sıva + 15 cm betonarme + 14 cm taşyünü (λ=0,040)',
             [(0.02, 1.0), (0.15, 2.5), (0.14, 0.040)], 0.10, 0.08, 0.30),
    'Dö':   ('Toprağa oturan döşeme: seramik + 6,5 cm şap + 10 cm XPS (λ=0,035) + 15 cm betonarme + 10 cm grobeton',
             [(0.01, 1.3), (0.065, 1.4), (0.10, 0.035), (0.15, 2.5), (0.10, 1.65)], 0.17, 0.0, 0.35),
    'İD':   ('İç duvar (ısıtılan hacimler arası): sıva + 10 cm tuğla + sıva',
             [(0.02, 1.0), (0.10, 0.45), (0.02, 1.0)], 0.13, 0.13, None),
}
U = {k: round(_u(v[1], v[2], v[3]), 3) for k, v in ASSY.items()}
U['ÇP'] = 1.8      # PVC doğrama + Low-E ısıcam, Uw ≤ 1,8 (g ≤ 0,45)
U['DK'] = 2.0      # daire giriş kapısı (yalıtımlı çelik kapı, Ud ≤ 2,0) - ısıtılmayan hole açılır
U['İK'] = 2.0      # iç kapı
U_LIM = {'DD': 0.40, 'DD25': 0.40, 'DD30': 0.40, 'İDM': 0.40, 'İDA': 0.40, 'Ta': 0.30, 'Dö': 0.35, 'ÇP': 1.8}

ZD, ZW = 7, 0
ZH = {'K': 5, 'G': -5, 'D': 0, 'B': 0, None: 0}

# ------------------------------------------------------------------ mahaller
# satır: (işaret, yön, uzunluk, yükseklik, adet, karşı sıcaklık | None(=dış), [çıkarılacak satır işaretleri], açıklama)
# karşı sıcaklık None -> dış hava
def rooms_for(kat):
    """kat: 'Z', '1', '2' -> [(no, ad, ti, alan, satırlar, qs_satırları, Ze)]"""
    H, KH = DUVAR_H, KIRIS_H
    R = []
    # 1) SALON + MUTFAK (22 °C)
    rows = [
        ('DD', 'G', 5.40, H, 1, None, ['ÇP1']),
        ('DD25', 'G', 5.40, KH, 1, None, []),
        ('ÇP1', 'G', 1.40, 2.10, 2, None, []),
        ('DD30', 'G', 0.93, KAT_H, 1, None, []),
        ('DD', 'B', 0.65, H, 1, None, []),
        ('DD25', 'B', 0.65, KH, 1, None, []),
        ('DD30', 'B', 0.60, KAT_H, 1, None, []),
        ('İDM', 'D', 3.00, KAT_H, 1, T_KOMSU, []),        # bitişik komşu bina duvarı
        ('İDA', None, 4.28, KAT_H, 1, T_ASANSOR, []),    # asansör kuyusu perdesi
        ('İDM', None, 0.54, KAT_H, 1, T_HOL, []),         # merdiven holü duvarı
        ('İDA', None, 0.50, KAT_H, 1, T_HOL, []),         # hol tarafı kolon (50/30)
    ]
    R.append(('SALON + MUTFAK', 22, 15.63, rows, [('ÇP1', 1.40, 2.10, 2)], 1.2))
    # 2) ODA (20 °C) - kuzey/batı köşe
    rows = [
        ('DD', 'K', 3.95, H, 1, None, ['ÇP1']),
        ('DD25', 'K', 3.95, KH, 1, None, []),
        ('ÇP1', 'K', 1.40, 1.40, 1, None, []),
        ('DD30', 'K', 0.60, KAT_H, 1, None, []),
        ('DD', 'B', 1.85, H, 1, None, []),
        ('DD25', 'B', 1.85, KH, 1, None, []),
        ('DD30', 'B', 0.80, KAT_H, 1, None, []),
        ('İDM', None, 2.68, KAT_H, 1, T_HOL, []),
        ('İDA', None, 0.50, KAT_H, 1, T_HOL, []),
    ]
    R.append(('ODA', 20, 9.67, rows, [('ÇP1', 1.40, 1.40, 1)], 1.2))
    # 3) ODA (küçük, 20 °C) - kuzey/doğu (komşu) köşe
    rows = [
        ('DD', 'K', 1.60, H, 1, None, ['ÇP1']),
        ('DD25', 'K', 1.60, KH, 1, None, []),
        ('ÇP1', 'K', 1.40, 1.40, 1, None, []),
        ('DD30', 'K', 0.45, KAT_H, 1, None, []),
        ('İDM', 'D', 2.00, KAT_H, 1, T_KOMSU, []),
    ]
    R.append(('ODA 2', 20, 4.67, rows, [('ÇP1', 1.40, 1.40, 1)], 1.2))
    # 4) BANYO + WC (26 °C, penceresiz)
    rows = [
        ('İDM', 'D', 1.73, KAT_H, 1, T_KOMSU, []),
        ('İDA', 'D', 0.52, KAT_H, 1, T_KOMSU, []),
        ('İD', None, 1.85, KAT_H, 1, 20, []),            # oda 2 tarafı
        ('İD', None, 2.25, KAT_H, 1, 18, ['İK1']),       # antre tarafı
        ('İK1', None, 0.80, 2.10, 1, 18, []),
        ('İD', None, 1.85, KAT_H, 1, 22, []),            # mutfak tarafı
    ]
    R.append(('BANYO + WC', 26, 4.20, rows, [], 1.0))
    # 5) ANTRE (18 °C) - kollektör bağlantı boruları ile ısınır
    rows = [
        ('İDM', None, 1.35, KAT_H, 1, T_HOL, ['DK1']),
        ('DK1', None, 1.00, 2.10, 1, T_HOL, []),
    ]
    R.append(('ANTRE', 18, 4.62, rows, [('DK1', 1.00, 2.10, 1)], 1.0))
    out = []
    for i, (nm, ti, A, rows, qs, ze) in enumerate(R):
        rows = list(rows)
        if kat == 'Z':
            rows.append(('Dö', None, A, 1.0, 1, T_TOPRAK, []))
        if kat == '2':
            rows.append(('Ta', None, A, 1.0, 1, T_CATI, []))
        out.append((i + 1, nm, ti, A, rows, qs, ze))
    return out


def ukey(mark):
    m = mark.rstrip('0123456789') if mark not in ('DD25', 'DD30') else mark
    return m


def calc(kat):
    res = []
    for no, nm, ti, A, rows, qs, ze in rooms_for(kat):
        lines = []
        for mark, yon, l, h, n, tk, sub in rows:
            uk = ukey(mark)
            dT = ti - (T_DIS if tk is None else tk)
            F = l * h
            minus = 0.0
            for s in sub:
                for x in lines:
                    if x['mark'] == s:
                        minus += x['F'] * x['n']
            # çıkarılacak satır sonra gelirse ileri bak
            for s in sub:
                for mk2, yon2, l2, h2, n2, tk2, sub2 in rows:
                    if mk2 == s and not any(x['mark'] == s for x in lines):
                        minus += l2 * h2 * n2
            Aeff = F * n - minus
            zh = ZH.get(yon, 0) if tk is None else 0
            z = 1 + (ZD + ZW + zh) / 100.0
            Q0 = Aeff * U[uk] * dT
            lines.append(dict(mark=mark, uk=uk, yon=yon if tk is None or (yon == 'D') else '', l=l, h=h, F=F, n=n,
                              minus=minus, A=Aeff, U=U[uk], dT=dT, Q0=Q0, ZH=zh, Z=z, Q=Q0 * z, sub=sub))
        Qt = sum(x['Q'] for x in lines)
        L = sum((a + b) * 2 * n for _, a, b, n in qs)
        dTo = ti - T_DIS
        Qs = 2 * L * 0.9 * 0.67 * dTo * ze if qs else 0.0
        if qs and qs[0][0] == 'DK1':
            Qs = 2 * L * 0.9 * 0.67 * (ti - T_HOL) * ze
        res.append(dict(no=no, name=nm, ti=ti, A=A, rows=lines, Qt=Qt, L=L, Qs=Qs, Ze=ze, Q=Qt + Qs))
    return res


if __name__ == '__main__':
    for k, v in ASSY.items():
        print('%-5s U=%.3f  sınır=%s  %s' % (k, U[k], v[4], v[0]))
    tot = 0
    for kat in 'Z12':
        r = calc(kat)
        s = sum(x['Q'] for x in r)
        tot += s
        print(kat, ' '.join('%s=%.0f' % (x['name'], x['Q']) for x in r), ' TOPLAM=%.0f W' % s)
    print('BİNA', round(tot))
