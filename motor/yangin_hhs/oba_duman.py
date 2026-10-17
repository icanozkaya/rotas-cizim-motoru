# -*- coding: utf-8 -*-
"""OBA 84 parsel depolama binası — DUMAN TAHLİYE (2 seçenek).

  CATI : doğal duman tahliyesi — çatıda duman ve ısı tahliye kapakları (DTK, TS EN 12101-2)
  DUVAR: mekanik duman tahliyesi — dış duvarda duman egzoz fanları (F400/120, TS EN 12101-3)
Ortak: 8 duman bölgesi (36 x 36 m ≤ 1600 m², boy ≤ 60 m), duman perdeleri (TS EN 12101-1), alt seviyede taze hava girişleri.
Hesap: aks-simetrik duman tüyü (plume) M = 0,188·P·Y^1,5 (TS EN 12101-5 / DIN 18232-2 yaklaşımı).

Çalıştırma: python3 motor/yangin_hhs/oba_duman.py
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ciz_ortak import yeni_doc, C, tr, mimari_altlik, pafta_cerceve, KOK
from oba_veri import AX, AY, X0, X1, Y0, Y1, MAHYA_Y, z_cati, KOT_SACAK, EGIM
import oba_yangin as OY

CIKTI = os.path.join(KOK, 'proje', 'oba_84_parsel_yangin')
KAT = {k: v for k, v in OY.KAT.items() if k.startswith(('ROTAS-MIMARI', 'ROTAS-HESAP', 'ROTAS-NOT', 'ROTAS-PAFTA', 'ROTAS-DETAY', 'ROTAS-LEJANT'))}
KAT.update({'ROTAS-DUMAN-PERDE': (1, 'CONTINUOUS'), 'ROTAS-DUMAN-BOLGE': (6, 'DASHDOT'), 'ROTAS-DUMAN-DTK': (3, 'CONTINUOUS'),
            'ROTAS-DUMAN-FAN': (3, 'CONTINUOUS'), 'ROTAS-DUMAN-TAZE': (5, 'CONTINUOUS'), 'ROTAS-DUMAN-YAZI': (7, 'CONTINUOUS'),
            'ROTAS-DUMAN-OK': (3, 'CONTINUOUS')})
PR, BO, DT, FN, TZ, YZ = ('ROTAS-DUMAN-PERDE', 'ROTAS-DUMAN-BOLGE', 'ROTAS-DUMAN-DTK', 'ROTAS-DUMAN-FAN', 'ROTAS-DUMAN-TAZE',
                          'ROTAS-DUMAN-YAZI')

# ------------------------------------------------------------------ duman bölgeleri
XB = [AX[0], AX[6], AX[12], AX[18], AX[24]]          # perdeler aks 7, 13, 19 (+ mahya)
YB = [Y0, MAHYA_Y, Y1]
BOLGELER = []
for j in range(2):
    for i in range(4):
        BOLGELER.append(dict(no=len(BOLGELER) + 1, x0=XB[i], x1=XB[i + 1], y0=YB[j], y1=YB[j + 1], cephe='A' if j == 0 else 'D'))

# ------------------------------------------------------------------ hesap
H = dict(Y=7.0, P=18.0, Qf=10000.0, kc=0.80, T0=293.0, rho0=1.20, cp=1.01, Cv=0.60, v_taze=5.0,
         dtk=(2.00, 1.50), n_dtk=6, fan_Q=70000, n_fan=4, fan_cap=1250)


def hesap():
    h = dict(H)
    A_b = (XB[1] - XB[0]) * (YB[1] - YB[0]) / 1e4
    z_ort = (KOT_SACAK + z_cati(MAHYA_Y) + 0.30) / 2
    M = 0.188 * h['P'] * h['Y'] ** 1.5
    Qc = h['Qf'] * h['kc']
    dT = Qc / (M * h['cp'])
    Tl = h['T0'] + dT
    rho = 353.0 / Tl
    Vs = M / rho
    dl = z_ort - h['Y']                      # duman tabakası kalınlığı (ortalama)
    AvCv = M * Tl / (h['rho0'] * math.sqrt(2 * 9.81 * dl * dT * h['T0']))
    Aa_dtk = h['dtk'][0] * h['dtk'][1] * h['Cv']
    n_gerek = math.ceil(AvCv / Aa_dtk)
    Mmax_dtk = 2.05 * h['rho0'] * dl ** 2.5 * math.sqrt(h['T0'] * dT) / Tl
    Vmax_fan = 4.16 * 0.5 * dl ** 2.5 * math.sqrt(dT / h['T0'])          # duvar tipi (γ=0,5), m³/s
    Vfan = h['fan_Q'] / 3600
    n_fan_gerek = math.ceil(Vs * 3600 / h['fan_Q'])
    v_fan = Vfan / (math.pi / 4 * (h['fan_cap'] / 1000) ** 2)
    A_taze_dog = 1.5 * AvCv                                                 # aerodinamik (doğal)
    A_taze_mek = Vs / h['v_taze']                                           # serbest kesit (mekanik, ≤ 5 m/s)
    h.update(A_b=A_b, z_ort=z_ort, M=M, Qc=Qc, dT=dT, Tl=Tl, Ts=Tl - 273, rho=rho, Vs=Vs, Vs_h=Vs * 3600, dl=dl, AvCv=AvCv,
             Aa_dtk=Aa_dtk, n_gerek=n_gerek, Aa_top=h['n_dtk'] * Aa_dtk, Mmax_dtk=Mmax_dtk, Vmax_fan=Vmax_fan, Vfan=Vfan,
             n_fan_gerek=n_fan_gerek, Q_fan_top=h['n_fan'] * h['fan_Q'], v_fan=v_fan, A_taze_dog=A_taze_dog, A_taze_mek=A_taze_mek)
    return h


# taze hava giriş panjurları: uzun cephelerde (A, D) 4'er, kısa cephelerde 2'şer — alt seviye (+0,50 .. +3,00)
PANJUR = ([(AX[i] + 300, Y0, 'A') for i in (1, 7, 13, 19)] + [(AX[i] + 300, Y1, 'D') for i in (1, 7, 13, 19)] +
          [(X0, y, '1') for y in (AY['B'] - 300, AY['C'] + 300)] + [(X1, y, '25') for y in (AY['B'] - 300, AY['C'] + 300)])
PANJUR_OLCU = (3.00, 2.50, 0.65)        # g x y (m), Cv / serbest oran


def plan_ortak(c, h, baslik):
    mimari_altlik(c)
    for b in BOLGELER:
        c.R(b['x0'] + 40, b['y0'] + 40, b['x1'] - 40, b['y1'] - 40, BO, 0)
        cx, cy = (b['x0'] + b['x1']) / 2, (b['y0'] + b['y1']) / 2
        c.T(cx, cy + 120, f'DUMAN BÖLGESİ DB-{b["no"]}', 40, 'MC', YZ)
        c.T(cx, cy + 60, f'{tr(h["A_b"], 0)} m²  (36,00 x 36,00 m)', 22, 'MC', YZ)
        c.T(cx, cy + 20, f'duman tabakası alt sınırı +{tr(h["Y"], 2)}', 18, 'MC', YZ)
    # perdeler
    for x in XB[1:-1]:
        c.L((x + 70, Y0), (x + 70, Y1), PR, 12)
        c.T(x + 100, Y0 + 900, 'DUMAN PERDESİ (TS EN 12101-1 D60) - ALT KOTU +7,00', 16, 'ML', PR, rot=90)
    c.L((X0, MAHYA_Y + 60), (X1, MAHYA_Y + 60), PR, 12)
    for xm in (AX[3], AX[9], AX[15], AX[21]):
        c.T(xm, MAHYA_Y + 90, 'DUMAN PERDESİ (MAHYA) - ALT KOTU +7,00', 16, 'BC', PR)
    # taze hava panjurları
    g, yy, cv = PANJUR_OLCU
    for i, (x, y, k) in enumerate(PANJUR):
        if k in 'AD':
            d = -1 if k == 'A' else 1
            c.R(x - g * 50, y + d * 10, x + g * 50, y + d * 60, TZ, 3)
            for t in range(1, 6):
                c.L((x - g * 50 + t * g * 100 / 6, y + d * 10), (x - g * 50 + t * g * 100 / 6, y + d * 60), TZ)
            c.T(x, y + d * 90, f'TH-{i + 1}', 20, 'BC' if d > 0 else 'TC', TZ)
            c.T(x, y + d * 125, f'TAZE HAVA PANJURU {tr(g)} x {tr(yy)} m (+0,50/+3,00, motorlu)', 12, 'BC' if d > 0 else 'TC', TZ)
            # ok (içeri)
            c.PL([(x - 25, y + d * 200), (x, y + d * 150), (x + 25, y + d * 200)], TZ, False, 3)
        else:
            d = -1 if k == '1' else 1
            c.R(x + d * 10, y - g * 50, x + d * 60, y + g * 50, TZ, 3)
            c.T(x + d * 90, y, f'TH-{i + 1}', 20, 'ML' if d > 0 else 'MR', TZ)
            c.T(x + d * 90, y - 35, f'TAZE HAVA PANJURU {tr(g)} x {tr(yy)} m', 12, 'TL' if d > 0 else 'TR', TZ)
    c.T(X0 - 900, Y1 + 1300, baslik, 60, 'BL', 'ROTAS-PAFTA')
    c.T(X0 - 900, Y1 + 1210, 'ÖLÇEK : 1/100', 40, 'BL', 'ROTAS-PAFTA')
    c.T(X0 - 900, Y1 + 1150, 'OBA MAKARNACILIK SAN. ve TİC. A.Ş. - HENDEK ÇAĞLAYAN MAH. 900 ADA 84 PARSEL - DEPOLAMA BİNASI (9.991 m²)', 26, 'BL', 'ROTAS-PAFTA')
    pafta_cerceve(c, X0 - 1100, Y0 - 1000, X1 + 1100, Y1 + 1500, '', '')


def dtk_konum(b):
    """6 kapak: her 6 m'lik çerçeve açıklığının ortasında, şaşırtmalı iki sıra (bölge derinliğinin 1/3 ve 2/3'ü)"""
    out = []
    for k in range(6):
        x = b['x0'] + 300 + k * 600
        y = b['y0'] + (b['y1'] - b['y0']) * (1 / 4 if k % 2 == 0 else 3 / 4)
        out.append((x, y))
    return out


def fan_konum(b):
    y = Y0 if b['cephe'] == 'A' else Y1
    return [(b['x0'] + d, y) for d in (450, 1350, 2250, 3150)]


def plan_cati(c, h):
    w, l = h['dtk']
    n = 0
    for b in BOLGELER:
        for (x, y) in dtk_konum(b):
            n += 1
            c.R(x - w * 50, y - l * 50, x + w * 50, y + l * 50, DT, 4)
            c.L((x - w * 50, y - l * 50), (x + w * 50, y + l * 50), DT)
            c.L((x - w * 50, y + l * 50), (x + w * 50, y - l * 50), DT)
            c.T(x, y + l * 50 + 20, f'DTK-{n}', 16, 'BC', DT)
        cx = (b['x0'] + b['x1']) / 2
        c.T(cx, b['y0'] + (b['y1'] - b['y0']) / 2 - 40, f'6 x DTK {tr(w)} x {tr(l)} m  Aa = {tr(h["Aa_top"], 2)} m² ≥ {tr(h["AvCv"], 2)} m²', 18, 'MC', DT)
    return n


def plan_duvar(c, h):
    n = 0
    D = h['fan_cap'] / 10          # mm → cm
    for b in BOLGELER:
        for (x, y) in fan_konum(b):
            n += 1
            d = -1 if b['cephe'] == 'A' else 1
            c.R(x - D / 2 - 15, y - 25, x + D / 2 + 15, y + 25, FN, 4)
            c.m.add_circle((x, y), D * 0.15, dxfattribs={'layer': FN})
            c.L((x - D / 2, y), (x + D / 2, y), FN)
            c.PL([(x - 40, y + d * 80), (x, y + d * 160), (x + 40, y + d * 80)], FN, False, 4)
            c.T(x, y + d * 200, f'DEF-{n}', 18, 'BC' if d > 0 else 'TC', FN)
            c.T(x, y + d * 235, f'{h["fan_Q"]:,} m³/h - Ø{h["fan_cap"]} - F400/120 - eksen +10,00'.replace(',', '.'), 12, 'BC' if d > 0 else 'TC', FN)
        cx = (b['x0'] + b['x1']) / 2
        c.T(cx, (b['y0'] + b['y1']) / 2 - 40, f'4 x {h["fan_Q"]:,} = {h["Q_fan_top"]:,} m³/h ≥ {tr(h["Vs_h"], 0)} m³/h'.replace(',', '.'),
            18, 'MC', FN)
    return n


def kesit(c, h, tip, ox, oy):
    """şematik enine kesit (A-D), 1/200 görünüm (ölçeksiz sunum)"""
    c.T(ox, oy, f'ŞEMATİK ENİNE KESİT ({"DOĞAL - ÇATI KAPAKLI" if tip == "cati" else "MEKANİK - DUVAR FANLI"})', 40, 'BL', 'ROTAS-PAFTA')
    c.T(ox, oy - 55, 'ÖLÇEKSİZ (1/200 oranlı)', 26, 'BL', 'ROTAS-PAFTA')
    s = 0.5                                           # 1 m = 50 birim
    x0, y0 = ox + 200, oy - 1100
    W = 72 * 50
    def P(y_m, z_m):
        return (x0 + y_m * 50, y0 + z_m * 50)
    c.L(P(-3, 0), P(75, 0), 'ROTAS-DETAY', 4)
    c.PL([P(0, 0), P(0, KOT_SACAK), P(36, KOT_SACAK + 36 * EGIM), P(72, KOT_SACAK), P(72, 0)], 'ROTAS-DETAY', False, 5)
    for ym in (24, 48):
        c.L(P(ym, 0), P(ym, KOT_SACAK + min(ym, 72 - ym) * EGIM), 'ROTAS-DETAY', 3)
    # istif
    for k in range(9):
        a = 2 + k * 7.6
        c.R(*P(a, 0.15), *P(a + 5.5, 4.0), 'ROTAS-DETAY')
    c.T(*P(5, 4.3), 'PALETLİ İSTİF ≤ 4,00 m', 18, 'BL', 'ROTAS-DETAY-YAZI')
    # duman tabakası
    pts = [P(0, h['Y']), P(72, h['Y']), P(72, KOT_SACAK), P(36, KOT_SACAK + 36 * EGIM), P(0, KOT_SACAK)]
    c.HATCH(pts, BO, 'ANSI37', 60)
    c.L(P(-3, h['Y']), P(75, h['Y']), BO, 3)
    c.T(*P(73, h['Y'] + 0.2), f'DUMAN TABAKASI ALT SINIRI +{tr(h["Y"], 2)}', 18, 'BL', BO)
    c.L(P(36, h['Y']), P(36, KOT_SACAK + 36 * EGIM), PR, 10)
    c.T(*P(36.5, h['Y'] + 0.4), 'DUMAN PERDESİ (mahya)', 16, 'BL', PR)
    # kotlar
    for z, s_ in ((0.0, '±0,00 (84,00)'), (KOT_SACAK, '+12,23 SAÇAK'), (KOT_SACAK + 36 * EGIM, '+14,75 MAHYA')):
        c.T(*P(-3.5, z), s_, 16, 'MR', 'ROTAS-DETAY-YAZI')
    # yangın + tüy
    c.PL([P(14, 0), P(14 - 0.4 * h['Y'] / 2, h['Y']), P(14 + 0.4 * h['Y'] / 2 + 4.5, h['Y']), P(18.5, 0)], 'ROTAS-DUMAN-OK', False, 2)
    c.T(*P(16, 0.5), f'TASARIM YANGINI 4,5x4,5 m - {tr(h["Qf"] / 1000, 0)} MW', 14, 'BC', 'ROTAS-DUMAN-OK')
    if tip == 'cati':
        for ym in (12, 60):
            z = KOT_SACAK + min(ym, 72 - ym) * EGIM
            c.R(*P(ym - 1.0, z), *P(ym + 1.0, z + 0.6), DT, 3)
            c.PL([P(ym - 0.4, z + 1.2), P(ym, z + 2.2), P(ym + 0.4, z + 1.2)], DT, False, 4)
            c.T(*P(ym + 1.3, z + 0.4), 'DTK (TS EN 12101-2)', 16, 'BL', DT)
    else:
        for ym, d in ((0, -1), (72, 1)):
            c.R(*P(ym - 0.3, 9.4), *P(ym + 0.3, 10.6), FN, 4)
            c.PL([P(ym + d * 0.8, 10.4), P(ym + d * 2.0, 10.0), P(ym + d * 0.8, 9.6)], FN, False, 4)
            c.T(*P(ym + d * 2.3, 10.0), 'DUMAN EGZOZ FANI +10,00', 16, 'ML' if d > 0 else 'MR', FN)
    for ym, d in ((0, 1), (72, -1)):
        c.R(*P(ym - 0.25, 0.5), *P(ym + 0.25, 3.0), TZ, 3)
        c.PL([P(ym + d * 0.6, 1.4), P(ym + d * 2.0, 1.75), P(ym + d * 0.6, 2.1)], TZ, False, 4)
    c.T(*P(2.5, 2.6), 'TAZE HAVA (alt seviye)', 16, 'BL', TZ)
    return x0 + W + 1500, y0 - 300


def tablo(c, h, tip, x, y):
    ort = [
        ['Bina / kullanım', 'Depolama, 144 x 72 m = 10.368 m² brüt, sprinklerli (HHS)'],
        ['Duman bölgesi', f'8 adet 36 x 36 m = {tr(h["A_b"], 0)} m² (≤ 1600 m², boy ≤ 60 m)'],
        ['Ortalama tavan yüksekliği', f'{tr(h["z_ort"], 2)} m (saçak +12,23 / mahya +14,75)'],
        ['Dumansız yükseklik Y', f'{tr(h["Y"], 2)} m (istif 4,0 m + 3,0 m)'],
        ['Tasarım yangını', f'4,5 x 4,5 m, P = {tr(h["P"], 1)} m, Q = {tr(h["Qf"] / 1000, 1)} MW, Qc = {tr(h["Qc"] / 1000, 1)} MW (sprinklerli)'],
        ['Duman kütle debisi M = 0,188·P·Y^1,5', f'{tr(h["M"], 2)} kg/s'],
        ['Duman sıcaklık artışı ΔT = Qc/(M·cp)', f'{tr(h["dT"], 1)} K → duman {tr(h["Ts"], 0)} °C, ρ = {tr(h["rho"], 3)} kg/m³'],
        ['Hacimsel debi V = M/ρ', f'{tr(h["Vs"], 2)} m³/s = {tr(h["Vs_h"], 0)} m³/h (bölge başına)'],
        ['Duman tabakası kalınlığı d', f'{tr(h["dl"], 2)} m'],
    ]
    if tip == 'cati':
        ek = [
            ['Gerekli aerodinamik alan AvCv', f'{tr(h["AvCv"], 2)} m² (bölge başına)'],
            ['Seçilen DTK', f'{tr(h["dtk"][0])} x {tr(h["dtk"][1])} m, Cv = {tr(h["Cv"])} → Aa = {tr(h["Aa_dtk"], 2)} m²/adet'],
            ['Bölge başına DTK', f'gerekli {h["n_gerek"]} → seçilen {h["n_dtk"]} adet, Aa = {tr(h["Aa_top"], 2)} m²'],
            ['Toplam DTK', f'{8 * h["n_dtk"]} adet (8 bölge)'],
            ['Delinme (plugholing) kontrolü', f'Mmax = {tr(h["Mmax_dtk"], 1)} kg/s/kapak ≥ {tr(h["M"] / h["n_dtk"], 1)} kg/s'],
            ['Taze hava girişi (alt seviye)', f'Aa ≥ 1,5·AvCv = {tr(h["A_taze_dog"], 1)} m²; {len(PANJUR)} panjur x {tr(PANJUR_OLCU[0] * PANJUR_OLCU[1] * PANJUR_OLCU[2], 2)} m² = {tr(len(PANJUR) * PANJUR_OLCU[0] * PANJUR_OLCU[1] * PANJUR_OLCU[2], 1)} m²'],
        ]
    else:
        ek = [
            ['Bölge egzoz debisi', f'≥ {tr(h["Vs_h"], 0)} m³/h'],
            ['Seçilen fan', f'{h["n_fan"]} x {h["fan_Q"]:,} = {h["Q_fan_top"]:,} m³/h, Ø{h["fan_cap"]}, F400/120, v = {tr(h["v_fan"], 1)} m/s'.replace(',', '.')],
            ['Toplam fan', f'{8 * h["n_fan"]} adet (yalnız yangın bölgesinin fanları çalışır)'],
            ['Delinme kontrolü (duvar, γ=0,5)', f'Vmax = {tr(h["Vmax_fan"], 1)} m³/s/fan ≥ {tr(h["Vfan"], 1)} m³/s'],
            ['Taze hava girişi (v ≤ 5 m/s)', f'serbest kesit ≥ {tr(h["A_taze_mek"], 1)} m²; {len(PANJUR)} panjur → {tr(len(PANJUR) * PANJUR_OLCU[0] * PANJUR_OLCU[1] * PANJUR_OLCU[2], 1)} m²'],
            ['Fan besleme', 'yangına dayanıklı kablo (elektrik projesinde), jeneratör/2. besleme'],
        ]
    return c.tablo(x, y, ['BÜYÜKLÜK', 'DEĞER'], [1250, 1900], ort + ek, h=18, baslik='DUMAN TAHLİYE HESABI', hb=30)


def notlar(tip):
    n = [
        '1. Depolama alanı duman perdeleri ile 8 duman bölgesine ayrılmış olup her bölge 1296 m² ve en büyük boyu 36 m\'dir.',
        '2. Duman perdeleri TS EN 12101-1 D60 sınıfı olacak, alt kotu +7,00 olacak ve kolon/çatı birleşimleri duman sızdırmaz yapılacaktır.',
        '3. Taze hava girişleri duman tabakası altında (+0,50 / +3,00) yapılacak, yangın alarmı ile otomatik açılacaktır.',
        '4. Sistem yangın algılama sistemine bağlanacak, yalnız yangın algılanan bölgenin tahliye elemanları devreye girecektir.',
        '5. İtfaiye için ana girişte manuel kumanda paneli (OSP/ITF) bulunacaktır.',
    ]
    if tip == 'cati':
        n += ['6. Duman ve ısı tahliye kapakları TS EN 12101-2 belgeli, rüzgar yükü ve kar yükü sınıfına uygun, termik + pnömatik/elektrik açmalı olacaktır.',
              '7. Kapaklar 6 m\'lik çerçeve açıklıklarının ortasına, aşıkların arasına yerleştirilecek, statik projede kasa açıklıkları gösterilecektir.',
              '8. Kapakların açılma süresi 60 saniyeyi geçmeyecek, kapak üstünde rüzgar engeli bulunmayacaktır.']
    else:
        n += ['6. Duman egzoz fanları TS EN 12101-3 F400/120 sınıfı duvar tipi aksiyal olacak, dış tarafta yağmur panjuru ve kuş teli, iç tarafta geri dönüşsüz klape olacaktır.',
              '7. Fanlar dış duvarda +10,00 eksen kotunda, kolonlar arasındaki açıklıklara konacak; statik projede duvar boşlukları gösterilecektir.',
              '8. Fan kabloları yangına dayanıklı olacak, fanlar ikinci bir enerji kaynağından (jeneratör) beslenecektir.']
    return n


def ciz(tip):
    h = hesap()
    doc = yeni_doc(KAT)
    c = C(doc)
    plan_ortak(c, h, 'DUMAN TAHLİYE PLANI - ' + ('SEÇENEK 1: DOĞAL (ÇATI KAPAKLI)' if tip == 'cati' else 'SEÇENEK 2: MEKANİK (DUVAR FANLI)'))
    n = plan_cati(c, h) if tip == 'cati' else plan_duvar(c, h)
    ox, oy = X0 - 900, Y0 - 1300
    kx, ky = kesit(c, h, tip, ox, oy)
    yt = tablo(c, h, tip, kx, oy)
    cihaz = ([['01', 'DUMAN VE ISI TAHLİYE KAPAĞI (DTK)', str(n), f'{tr(h["dtk"][0])} x {tr(h["dtk"][1])} m, Cv ≥ 0,60, TS EN 12101-2'],
              ['02', 'DTK KUMANDA PANELİ + CO2/ELEKTRİK AÇMA', '8', 'bölge başına'] ] if tip == 'cati' else
             [['01', 'DUVAR TİPİ DUMAN EGZOZ FANI', str(n), f'{h["fan_Q"]:,} m³/h, Ø{h["fan_cap"]}, F400/120'.replace(',', '.')],
              ['02', 'FAN KUMANDA PANOSU', '8', 'bölge başına, yangın algılamaya bağlı']])
    cihaz += [['03', 'DUMAN PERDESİ (TS EN 12101-1 D60)', f'{tr(3 * 72 + 144, 0)} m', 'alt kotu +7,00 (sabit veya inen tip)'],
              ['04', 'TAZE HAVA PANJURU (MOTORLU)', str(len(PANJUR)), f'{tr(PANJUR_OLCU[0])} x {tr(PANJUR_OLCU[1])} m, alt seviye'],
              ['05', 'İTFAİYE KUMANDA PANELİ', '1', 'ana girişte']]
    yc = c.tablo(kx, yt - 200, ['NO', 'CİHAZ', 'ADET', 'ÖZELLİK'], [100, 1000, 300, 1750], cihaz, h=18, baslik='CİHAZ LİSTESİ', hb=30)
    yn = c.notlar(ox, ky - 200, 'NOTLAR', notlar(tip), h=20, gen=5000)
    alt = min(yn, yc) - 300
    OY.antet(c, X1 + 1000 - 1800, alt - 750)
    # antet proje adı
    for e in c.m.query('TEXT'):
        if e.dxf.text.startswith('PROJE: YANGIN'):
            e.dxf.text = 'PROJE: DUMAN TAHLİYE - ' + ('DOĞAL (ÇATI)' if tip == 'cati' else 'MEKANİK (DUVAR)')
    pafta_cerceve(c, X0 - 1100, alt - 850, X1 + 1100, oy + 300, '', '')
    yol = os.path.join(CIKTI, f'OBA_84_DUMAN_TAHLIYE_{"CATI_DOGAL" if tip == "cati" else "DUVAR_MEKANIK"}.dxf')
    doc.saveas(yol)
    print(yol, n, {k: round(v, 2) for k, v in h.items() if isinstance(v, float)})
    return yol, h


if __name__ == '__main__':
    ciz('cati')
    ciz('duvar')
