# -*- coding: utf-8 -*-
"""Hesap paftası: radyatör seçim çizelgesi, kritik devre boru çapı hesabı (TS 2164 / 07_ISITMA §3.3 düzeni), pompa."""
import ciz as C

TB = 'ROTAS-TABLO'


def _n(v, d=0):
    s = f'{v:,.{d}f}'
    return s.replace(',', '#').replace('.', ',').replace('#', '.')


def tablo(cz, x, y, baslik, sutunlar, satirlar, h=9.0, vurgu=None):
    """sutunlar: [(başlık, genişlik, hizalama)]; satırlar: liste; y üst kenar. Dönüş: alt kenar y"""
    rh = h * 2.0
    W = sum(w for _, w, _ in sutunlar)
    cz.yazi((x + W / 2, y + rh * 0.9), baslik, h * 1.5, 'ROTAS-BASLIK', maske=False, kaydet=False)
    satir = [[s for s, _, _ in sutunlar]] + satirlar
    y1 = y - rh * len(satir)
    cz.pl([(x, y), (x + W, y), (x + W, y1), (x, y1)], TB, w=1.0, kapali=True, engel=False)
    xx = x
    for _, w, _ in sutunlar[:-1]:
        xx += w
        cz.pl([(xx, y), (xx, y1)], TB, engel=False)
    for i in range(1, len(satir)):
        cz.pl([(x, y - rh * i), (x + W, y - rh * i)], TB, w=0.6 if i == 1 else 0.0, engel=False)
    for i, row in enumerate(satir):
        yc = y - rh * (i + 0.5)
        xx = x
        for j, (s, (_, w, al)) in enumerate(zip(row, sutunlar)):
            if i == 0:
                p, a = (xx + w / 2, yc), 'MC'
            elif al == 'R':
                p, a = (xx + w - h * 0.4, yc), 'MR'
            elif al == 'L':
                p, a = (xx + h * 0.4, yc), 'ML'
            else:
                p, a = (xx + w / 2, yc), 'MC'
            renk = 1 if (vurgu and i > 0 and vurgu(i - 1)) else None
            cz.yazi(p, str(s), h * (0.85 if i == 0 else 0.9), TB, al=a, maske=False, kaydet=False, renk=renk)
            xx += w
    return y1


def ciz(cz, P, M, A, pomp, x0=0.0, y0=-9000.0):
    y = y0
    cz.yazi((x0 + 1400, y + 230), 'ISITMA TESİSATI HESAPLARI – RADYATÖR SEÇİMİ, BORU ÇAPI VE POMPA', 40, 'ROTAS-BASLIK', maske=False)
    cz.yazi((x0 + 1400, y + 175), f"DENEME – {P['proje']['ad']} ({P['proje']['ilce']} / {P['proje']['il']}), sistem: "
            f"{'MERKEZİ (kazan + 2 kolon)' if P['sistem'] == 'merkezi' else 'KOMBİLİ (daire başına hermetik kombi)'}, "
            f"rejim {M['tg']:.0f}/{M['td']:.0f} °C, dış sıcaklık {M['genel']['tdis']} °C", 16, 'ROTAS-DENEME', maske=False)
    # 1) radyatör seçimi
    sut = [('KAT', 120, 'L'), ('MAHAL NO', 95, 'C'), ('MAHAL', 90, 'L'), ('t_i (°C)', 60, 'C'), ('ISI KAYBI (W)', 95, 'R'),
           ('RADYATÖR', 120, 'L'), ('TİP', 80, 'L'), ('BOY (mm)', 70, 'C'), ('ADET', 50, 'C'), ('KAPASİTE (W/ad)', 110, 'R'),
           ('TOPLAM (W)', 90, 'R'), ('KAPASİTE / KAYIP', 110, 'R')]
    rows = []
    ad = {'Z': 'ZEMİN', '1-2-3-4-5': 'NORMAL (×5)', 'Ç': 'ÇATI'}
    sira = ['Z', '1-2-3-4-5', 'Ç']
    for g in sira:
        rr = sorted([r for (gg, n), r in M['rad'].items() if gg == g], key=lambda r: r['no'])
        for r in rr:
            top = r['ver'] * r['adet']
            rows.append([ad[g], f"{g} {r['no']}" if g != '1-2-3-4-5' else r['no'], r['ad'], f"{r['ti']:.0f}", _n(r['q']), r['model'], r['tip'],
                         f"{r['boy'] * 1000:.0f}", str(r['adet']), _n(r['ver']), _n(top), f"{top / r['q']:.1f}"])
    qk = sum(r['q'] * (5 if g == '1-2-3-4-5' else 1) for (g, n), r in M['rad'].items())
    qr = sum(r['ver'] * r['adet'] * (5 if g == '1-2-3-4-5' else 1) for (g, n), r in M['rad'].items())
    rows.append(['BİNA TOPLAMI', '', '', '', _n(qk), '', '', '', '', '', _n(qr), f'{qr / qk:.1f}'])
    yalt = tablo(cz, x0, y, 'RADYATÖR SEÇİM ÇİZELGESİ (kullanıcı seçimi – rad.xlsx, değiştirilmedi)', sut, rows, 9.0)

    # 2) kritik devre
    x2 = x0 + 1300
    sut2 = [('PARÇA', 55, 'C'), ('HAT', 330, 'L'), ('Q (W)', 75, 'R'), ('Q (kcal/h)', 80, 'R'), ('L (m)', 55, 'R'),
            ('ÇAP', 95, 'C'), ('w (m/s)', 60, 'R'), ('R (mmSS/m)', 75, 'R'), ('R·L (mmSS)', 80, 'R'), ('Σζ', 50, 'R'),
            ('Z (mmSS)', 70, 'R'), ('R·L+Z', 70, 'R'), ('KÜMÜLATİF', 80, 'R')]
    rows2 = []
    kum = 0.0
    for p in A.kritik:
        kum += p['RL'] + p['Z']
        hat = p['ad'] if p['tur'] not in ('daire', 'radyator') else f"{p['ad']} – {p['kat']} kat, daire {p['daire']}"
        rows2.append([str(p['kno']), hat[:58], _n(p['Q']), _n(p['Q'] * 0.859845), _n(p['L'], 2), f"{p['dn']} ({p['inc']})",
                      _n(p['w'], 2), _n(p['R'], 2), _n(p['RL'], 1), _n(p['sz'], 1), _n(p['Z'], 1), _n(p['RL'] + p['Z'], 1), _n(kum, 1)])
    rows2.append(['', 'KRİTİK DEVRE TOPLAMI ΣR·L + ΣZ', '', '', _n(sum(p['L'] for p in A.kritik), 2), '', '', '',
                  _n(sum(p['RL'] for p in A.kritik), 1), '', _n(sum(p['Z'] for p in A.kritik), 1), _n(A.kritik_top, 1), ''])
    y2 = tablo(cz, x2, y, 'KRİTİK DEVRE BORU ÇAPI HESABI (parça 1 = en uzak radyatör, numara kazana doğru artar)', sut2, rows2, 9.0)

    # 3) Σζ dökümü
    sut3 = [('PARÇA', 55, 'C'), ('ÖZEL DİRENÇLER (adet × ζ)', 1050, 'L'), ('Σζ', 70, 'R')]
    rows3 = []
    for p in A.kritik:
        det = ', '.join(f"{a} {n}×{z:g}" for a, n, z in p['zeta_tum'])
        rows3.append([str(p['kno']), det[:150], _n(p['sz'], 1)])
    y3 = tablo(cz, x2, y2 - 120, 'KRİTİK DEVRE ÖZEL DİRENÇ KATSAYILARI (Σζ)', sut3, rows3, 9.0)

    # 4) pompa / cihaz
    b = P['boru']
    sat = [['Toplam ısı yükü (Q)', f"{_n(pomp['Q_W'])} W = {_n(pomp['Q_kcal'])} kcal/h"],
           ['Rejim / ΔT', f"{M['tg']:.0f}/{M['td']:.0f} °C, ΔT = {M['dT']:.0f} K"],
           ['Pompa debisi V = Q(kcal/h) / (ΔT·1000)', f"{_n(pomp['Q_kcal'])} / {M['dT'] * 1000:.0f} = {_n(pomp['V'], 2)} m³/h"],
           ['Kritik devre kaybı ΣR·L + ΣZ', f"{_n(pomp['H_kritik_mmSS'], 0)} mmSS"]]
    if P['sistem'] == 'merkezi':
        mp = P['merkezi']
        sat += [['Pompa basma yüksekliği', f"{_n(pomp['H_kritik_mmSS'], 0)} × {1 + mp['emniyet_orani']:.2f} + {mp['kazan_dairesi_ek_kayip_mmSS']} (kazan dairesi) = "
                                            f"{_n(pomp['H_mmSS'], 0)} mmSS ≈ {_n(pomp['H_mSS'], 2)} mSS"],
                ['Seçilecek pompa (P-01)', f"V ≥ {_n(pomp['V'], 2)} m³/h, H ≥ {_n(pomp['H_mSS'], 1)} mSS, frekans konvertörlü ıslak rotorlu"],
                ['Kazan kapasitesi (öneri)', f"≥ {_n(pomp['Q_W'] / 1000 * 1.1, 0)} kW (radyatör toplamı + %10) – kullanıcı onayı gerekli"]]
    else:
        k = P['kombi']
        sat += [['Gerekli basma (daire kritik devresi +%10)', f"{_n(pomp['H_mmSS'], 0)} mmSS ≈ {_n(pomp['H_mSS'], 2)} mSS"],
                ['Kombi pompası (katalogdan teyit)', f"{k['pompa_basma_mSS']} mSS @ {k['pompa_debi_m3h']} m³/h (parametre) – katalog eğrisiyle kontrol edilmeli"]]
    sat += [['Boru çapı ölçütü', f"{b['seri']}; R ≤ {b['Rmax_mmSS_m']:g} mmSS/m, w ≤ {b['wmax_m_s']:g} m/s, en küçük {b['dn_min']}"],
            ['Hız/R formülü', 'Darcy-Weisbach + Colebrook (ε = 0,045 mm), su 80 °C; Z = Σζ·ρ·w²/2']]
    tablo(cz, x0, yalt - 120, 'POMPA VE CİHAZ SEÇİMİ', [('KALEM', 330, 'L'), ('DEĞER', 760, 'L')], sat, 9.0)
    yy = min(y3, yalt - 120 - 18 * (len(sat) + 1)) - 80
    oran = [r['ver'] * r['adet'] / r['q'] for r in M['rad'].values()]
    uy = ['UYARILAR / KULLANICIYA SORULACAKLAR:',
          f'1) Seçilen radyatör kapasiteleri mahal ısı kayıplarının {min(oran):.1f}–{max(oran):.1f} katıdır (ör. normal kat salon 497 W kayba 2×1454 W). Seçim değiştirilmedi; boru çapı '
          + ('radyatör kapasitesine' if P['yuk_esasi'] == 'radyator' else 'ısı kaybına') + ' göre yapıldı.',
          '2) rad.xlsx antre t_i = 15 °C, ik.xls antre = 18 °C (ısı kaybı 18 °C ile hesaplanmış). ik.xls çatı katı oda başlıkları "Ç 11/Ç 12" iki kez geçiyor (rad.xlsx: Ç 13/14).',
          '3) Mahal yerleşimi, boru güzergâhları ve uzunluklar TEMSİLÎDİR (mimari yok); gerçek planla boru boyları ve kritik devre değişir.']
    for i, s in enumerate(uy):
        cz.yazi((x0, yy - i * 22), s, 12, 'ROTAS-DENEME' if i == 0 else 'ROTAS-YAZI', al='BL', maske=False)
    cz.pl([(x0 - 60, yy - 120), (x2 + 1420, yy - 120), (x2 + 1420, y + 290), (x0 - 60, y + 290)], 'ROTAS-PAFTA', w=2.0, kapali=True, engel=False)
