"""Cafer Göktaş ısı kaybı (ROTAŞ şablon yöntemi: Q=A.U.ΔT, Z=1+Zd+Zw+Zh, Qs=Σ(a.l).R.H.Δt.Ze)."""
TDIS = -3.0
U = dict(CP=1.8, DD=0.493, DK=3.5, IK=2.0, ID=0.402, DO=0.231, TA=0.300)
H = 3.0
ZD, ZW, ZH = 7, 0, 5
ZF = 1 + (ZD + ZW + ZH) / 100.0

# mahal: (ad, ti, alan, [satırlar]) satır: (işaret, uzunluk, yükseklik, adet, ΔT türü, çıkarılan ref)
ROOMS = [
    ('SALON VE MUTFAK', 20, 15.63, [('ÇP', 1.40, 2.10, 2, 'out'), ('DD', 7.36, H, 1, 'out', 'ÇP'),
                                    ('İD', 4.20, H, 1, 15), ('İD', 1.10, H, 1, 10)]),
    ('ODA', 20, 9.67, [('ÇP', 1.40, 1.40, 1, 'out'), ('DD', 6.93, H, 1, 'out', 'ÇP'), ('İD', 3.30, H, 1, 10)]),
    ('ODA2', 20, 4.67, [('ÇP', 1.40, 1.40, 1, 'out'), ('DD', 2.13, H, 1, 'out', 'ÇP')]),
    ('BANYO + WC', 24, 4.20, [('İK', 0.90, 2.10, 1, 4), ('İD', 4.05, H, 1, 4, 'İK')]),
    ('ANTRE', 20, 4.62, [('DK', 1.00, 2.10, 1, 10), ('İD', 2.70, H, 1, 10, 'DK')]),
]
NAMES = {'ODA2': 'ODA', 'ODA': 'ODA'}
ZNO = {'ODA': 1, 'ODA2': 2, 'BANYO + WC': 3, 'SALON VE MUTFAK': 4, 'ANTRE': 5}
UK = {'ÇP': 'CP', 'DD': 'DD', 'DK': 'DK', 'İK': 'IK', 'İD': 'ID', 'DÖ': 'DO', 'TA': 'TA'}


def calc(key):
    """key: 'Z','1','2' -> {oda: dict(rows, Qt, Qz, Qs, Q)}"""
    out = {}
    for nm, ti, A, rows in ROOMS:
        dto = ti - TDIS
        lines = []
        cp_area = {}
        for r in rows:
            mark, l, h, n = r[0], r[1], r[2], r[3]
            dt = dto if r[4] == 'out' else r[4]
            gross = l * h
            minus = 0.0
            if len(r) > 5:
                ref = r[5]
                minus = sum(x['A'] for x in lines if x['mark'] == ref)
            Aeff = gross * n - minus
            lines.append(dict(mark=mark, l=l, h=h, F=gross, n=n, minus=minus, A=Aeff, U=U[UK[mark]], dt=dt,
                              Q=Aeff * U[UK[mark]] * dt, ref=r[5] if len(r) > 5 else None))
        if key == 'Z':
            dt = ti - 9
            lines.append(dict(mark='DÖ', l=None, h=None, F=A, n=1, minus=0, A=A, U=U['DO'], dt=dt, Q=A * U['DO'] * dt))
        if key == '2':
            dt = ti - 4
            lines.append(dict(mark='TA', l=None, h=None, F=A, n=1, minus=0, A=A, U=U['TA'], dt=dt, Q=A * U['TA'] * dt))
        Qt = sum(x['Q'] for x in lines)
        Qz = Qt * ZF
        lsum = sum(x['l'] + x['h'] * x['n'] for x in lines if x['mark'] == 'ÇP')
        Qs = lsum * 2 * 0.97 * dto * 0.9 * 1.0
        out[nm] = dict(rows=lines, Qt=Qt, Qz=Qz, lsum=lsum, Qs=Qs, Q=Qz + Qs, ti=ti, A=A, dto=dto)
    return out


if __name__ == '__main__':
    for k in 'Z12':
        c = calc(k)
        print(k, {n: round(v['Q'], 1) for n, v in c.items()}, round(sum(v['Q'] for v in c.values()), 1))
