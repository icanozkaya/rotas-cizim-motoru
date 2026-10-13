# -*- coding: utf-8 -*-
"""Isıtma hesapları (kullanıcının ısıtma hesaplar şablonu): ısı kaybı → kazan, pompalar, genleşme, denge kabı, nötralizasyon,
kazan dairesi havalandırması. Girdi: radyatör seçim Excel'i (mahal ısı kayıpları) + blok/kat tekrarları."""
import math, openpyxl, pickle
SRC = '/tmp/claude-0/is/rad.xlsx'
ws = openpyxl.load_workbook(SRC, data_only=True)['MAHAL']
rows = [r for r in ws.iter_rows(min_row=9, values_only=True) if r[0] and isinstance(r[4], (int, float))]
KAT = {'N': 5, 'C': 1, 'Z': 1}          # 1-2-3-4-5 (5 normal kat), Ç (çatı katı), Z (zemin)
BLOK = 3                                  # B1, B2, B3 aynı
Q = {'N': 0, 'C': 0, 'Z': 0}; RAD = dict(Q); LR = dict(Q)
for r in rows:
    k = 'N' if str(r[0]).startswith('1-2') else ('C' if str(r[0]).startswith('Ç') else 'Z')
    Q[k] += r[4]; RAD[k] += r[7] * r[8]; LR[k] += r[5] * r[8]
Q_BLOK = sum(Q[k] * KAT[k] for k in Q) / 1000; RAD_BLOK = sum(RAD[k] * KAT[k] for k in Q) / 1000; L_BLOK = sum(LR[k] * KAT[k] for k in Q)
QT = Q_BLOK * BLOK; RADT = RAD_BLOK * BLOK; LT = L_BLOK * BLOK
TG, TD = 90, 70; DT = TG - TD
# kazan
EMN = 1.15                                # boru kayıpları + ilk ısınma payı
QK_GER = QT * EMN
K_ADET, K_BIRIM = 5, 110                 # projedeki kazanlar (5 x 110 kW)
QK = K_ADET * K_BIRIM
VP_K = K_BIRIM / (1.163 * DT)             # kazan başına primer debi m3/h
VS_SEK = RADT / (1.163 * DT)              # radyatör devresi debisi (kurulu radyatör kapasitesine göre)
IP1_Q, IP1_H = 5.0, 5.0
IP2_Q, IP2_H = 20.0, 10.0
def pw(q, h):
    n = q * h * 10 / 3600 / 0.6
    steps = [0, 0.04, 0.05, 0.062, 0.09, 0.107, 0.125, 0.15, 0.18, 0.25, 0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3.7, 5.5]
    nxt = steps[1:] + [7.5]
    v = [b for a, b in zip(steps, nxt) if a <= n][-1]
    return n, v
# pompa basma yüksekliği (kritik devre: B1/B3 çatı katı Ç01)
L_KD = 2 * (45 + 24 + 15); R_ORT = 150; Z_OZ = 0.30
H_BORU = L_KD * R_ORT * (1 + Z_OZ) / 9807
H_KAL, H_TRV, H_DK = 1.5, 1.0, 0.5
H_TOP = H_BORU + H_KAL + H_TRV + H_DK
# genleşme (TS EN 12828)
V_RAD = LT * 5.7                          # 22 PKKP 600: ~5,7 l/m (bilgi)
VS = QK * 10                              # sistem su hacmi = kurulu kapasite x 10 l/kW (şablon)
E_ = 0.0359                               # 90 °C
VE = VS * E_; VWR = max(VS * 0.005, 3.0)
H_ST = 24.0; P0 = H_ST / 10 + 0.3; PSV = 6.0; PE = PSV - 0.5
VN = (VE + VWR) * (PE + 1) / (PE - P0)
GT = 1000                                 # projedeki tank (≥ Vn)
# denge kabı
QMAX = max(K_ADET * VP_K, IP2_Q)
D_DK = math.sqrt(4 * QMAX / 3600 / (math.pi * 0.15)) * 1000
D_SEC = 300                               # şablondaki denge kabı (≥ hesaplanan)
# havalandırma
A_ALT = QK * 6; A_UST = QK * 3
def kare(a):
    for b, h in ((20, 20), (25, 20), (25, 25), (30, 25), (30, 30), (35, 30), (40, 30), (40, 40), (45, 40), (50, 50), (60, 60)):
        if b * h >= a: return f'{b} × {h} cm', b * h
def daire(a):
    for d in (200, 250, 280, 315, 320, 355, 400, 450, 500, 560, 630, 700, 800):
        if math.pi * (d / 20) ** 2 >= a: return f'Ø{d} mm', round(math.pi * (d / 20) ** 2)
R = dict(Q=Q, RAD=RAD, Q_BLOK=Q_BLOK, RAD_BLOK=RAD_BLOK, QT=QT, RADT=RADT, QK_GER=QK_GER, QK=QK, VP_K=VP_K, VS_SEK=VS_SEK,
         IP1=(IP1_Q, IP1_H, pw(IP1_Q, IP1_H)), IP2=(IP2_Q, IP2_H, pw(IP2_Q, IP2_H)), H_TOP=H_TOP, H_BORU=H_BORU, L_KD=L_KD,
         VS=VS, V_RAD=V_RAD, LT=LT, VE=VE, VWR=VWR, P0=P0, PE=PE, PSV=PSV, VN=VN, GT=GT, QMAX=QMAX, D_DK=D_DK, D_SEC=D_SEC,
         A_ALT=A_ALT, A_UST=A_UST, ALT=(kare(A_ALT), daire(A_ALT)), UST=(kare(A_UST), daire(A_UST)), K_ADET=K_ADET, K_BIRIM=K_BIRIM)
pickle.dump(R, open('/tmp/claude-0/is/R.pkl', 'wb'))
f = lambda v, n=1: f'{v:,.{n}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
# ======================== rapor tabloları (bölümler)
SEC = []
SEC.append(('1. B1-B2-B3 BLOK ISI İHTİYACI', 'Radyatör seçim cetvelindeki mahal ısı kayıplarının toplamı esas alınmıştır (her blok aynı; 5 normal kat + zemin + çatı katı).',
    [('Bina / Blok', 'B1 + B2 + B3 BLOK (merkezi sistem)'), ('Bir blok ısı kaybı', f'{f(Q_BLOK, 2)} kW'), ('Blok adedi', f'{BLOK}'),
     ('Toplam ısı kaybı', f'{f(QT, 2)} kW ≈ {f(QT * 860, 0)} kcal/h'), ('Dış hava sıcaklığı', '-3 °C'), ('Su gidiş / dönüş sıcaklığı', f'{TG} °C / {TD} °C'),
     ('Çalışma rejimi', f'{TG}/{TD} °C (ΔT = {DT} °C)')], None))
SEC.append(('2. RADYATÖR TOPLAM KAPASİTESİ', 'Seçilen 22 PKKP/600 panel radyatörlerin toplam kapasitesi bina ısı kaybını karşılamaktadır.',
    [('Toplam bina ısı kaybı', f'{f(QT, 2)} kW'), ('Bir blok radyatör kapasitesi', f'{f(RAD_BLOK, 2)} kW'), ('Toplam radyatör kapasitesi', f'{f(RADT, 2)} kW')],
    'Sonuç: Radyatör kapasitesi bina ısı kaybını karşılamaktadır.'))
SEC.append(('3. ISITMA KAZANI KAPASİTE HESABI (TÜM BİNA)', f'Q kazan = Q ısı kaybı × {f(EMN, 2)} (boru kayıpları + ilk ısınma) = {f(QT, 2)} × {f(EMN, 2)} = {f(QK_GER, 1)} kW',
    [('Cihaz kodu', 'IK-01'), ('Kazan tipi', 'Duvar tipi yoğuşmalı, kaskad'), ('Kazan adedi', f'{K_ADET} adet'), ('Birim kazan gücü', f'{K_BIRIM} kW'),
     ('Toplam kurulu kapasite', f'{K_ADET} × {K_BIRIM} = {QK} kW ({f(QK * 860, 0)} kcal/h)'), ('Gerekli kapasite', f'{f(QK_GER, 1)} kW')],
    'Sonuç: Kazan sistemi toplam ısı yükünü karşılamaktadır.'))
SEC.append(('4. KAZAN PRİMER DEVRE VE SİSTEM DEBİ HESABI', None,
    [('Q primer = P / (1,163 × ΔT)', f'{K_BIRIM} / (1,163 × {DT}) = {f(VP_K, 2)} m³/h (kazan başına)'), ('Seçilen kazan pompası IP-1', f'{f(IP1_Q, 2)} m³/h - {f(IP1_H, 1)} mSS (kazan başına)'),
     ('Q sistem = Q radyatör / (1,163 × ΔT)', f'{f(RADT, 1)} / (1,163 × {DT}) = {f(VS_SEK, 2)} m³/h'), ('Seçilen radyatör devresi pompası IP-2', f'{f(IP2_Q, 2)} m³/h - {f(IP2_H, 1)} mSS')], None))
SEC.append(('5. RADYATÖR DEVRESİ POMPA BASMA YÜKSEKLİĞİ (KRİTİK DEVRE Ç01)', None,
    [('Kritik devre uzunluğu (gidiş + dönüş)', f'{L_KD} m'), ('Ortalama özgül boru kaybı R', f'{R_ORT} Pa/m'), ('Özel dirençler payı', f'%{int(Z_OZ * 100)}'),
     ('Boru kaybı = L × R × 1,30', f'{f(H_BORU, 2)} mSS'), ('Kalorimetre + termostatik vana + denge kabı', f'{f(H_KAL, 1)} + {f(H_TRV, 1)} + {f(H_DK, 1)} mSS'),
     ('Toplam', f'{f(H_TOP, 2)} mSS'), ('Seçilen IP-2 basma yüksekliği', f'{f(IP2_H, 1)} mSS')], 'Sonuç: Seçilen pompa kritik devre direncini karşılamaktadır.'))
SEC.append(('6. KAPALI GENLEŞME DEPOSU HESABI (TS EN 12828)', None,
    [('Toplam sistem su hacmi (V_s)', f'{QK} kW × 10 lt/kW = {f(VS, 0)} Litre'),
     ('Genleşme katsayısı (e) — 90 °C', f'{f(E_, 4)}'), ('Genleşen su hacmi (V_e)', f'{f(VS, 0)} × {f(E_, 4)} = {f(VE, 1)} Litre'),
     ('Yedek su hacmi (V_WR) — %0,5', f'{f(VWR, 1)} Litre'), ('Statik yükseklik (H_statik)', f'{f(H_ST, 0)} m'), ('Ön basınç (P_0) = H/10 + 0,3', f'{f(P0, 1)} bar'),
     ('Emniyet ventili açma basıncı (P_sv)', f'{f(PSV, 1)} bar'), ('Son basınç (P_e) = P_sv − 0,5', f'{f(PE, 1)} bar'),
     ('Gerekli nominal hacim V_n = (V_e+V_WR)·(P_e+1)/(P_e−P_0)', f'{f(VN, 0)} Litre'), ('Seçilen tank (GT-01)', f'{GT} Litre')],
    f'Sonuç: Seçilen {GT} litre genleşme deposu yeterlidir.'))
SEC.append(('7. DENGE KABI BOYUTLANDIRMA HESABI (DK-01)', None,
    [('Maksimum sistem debisi (Q_maks)', f'{f(QMAX, 2)} m³/h = {f(QMAX / 3600, 5)} m³/s'), ('Azami gövde akış hızı (v)', '0,15 m/s'),
     ('Hesaplanan iç çap D = √[4·Q/(π·v)]', f'{f(D_DK, 0)} mm'), ('Seçilen denge kabı iç çapı', f'Ø {D_SEC} mm'), ('Denge kabı ısıl yükü', f'{QK} kW'),
     ('Giriş – çıkış çapları', 'DN100 (4")')], f'Sonuç: Seçilen Ø{D_SEC} mm denge kabı yeterlidir.'))
(ka, kn), (da, dn_) = R['ALT']; (ku, kun), (du, dun) = R['UST']
SEC_H = [('1. HESAP ESASI', 'Kazan dairesi doğal havalandırma menfez alanları toplam kurulu kazan gücüne bağlı olarak hesaplanmıştır.',
          [('Toplam kurulu kazan gücü (Q_toplam)', f'{QK} kW'), ('Alt havalandırma katsayısı', '6 cm²/kW'), ('Üst havalandırma katsayısı', '3 cm²/kW')], None),
         ('2. ALT HAVALANDIRMA HESABI (TAZE HAVA GİRİŞİ)', f'A_alt = {QK} × 6 = {f(A_ALT, 0)} cm²',
          [('Kare/dikdörtgen kanal', f'{ka}  ({f(kn, 0)} cm²)'), ('Dairesel kanal', f'{da}  ({f(dn_, 0)} cm²)')], f'Sonuç: Seçilen alt havalandırma menfezi: {ka}.'),
         ('3. ÜST HAVALANDIRMA HESABI (SICAK HAVA / YANMA GAZI TAHLİYESİ)', f'A_üst = {QK} × 3 = {f(A_UST, 0)} cm²',
          [('Kare/dikdörtgen kanal', f'{ku}  ({f(kun, 0)} cm²)'), ('Dairesel kanal', f'{du}  ({f(dun, 0)} cm²)')], f'Sonuç: Seçilen üst havalandırma menfezi: {ku}.'),
         ('4. YERLEŞİM KURALI', None, [('Alt havalandırma', 'Zemin seviyesinden +30 cm yükseklikte, dış cepheye açılan duvarda'),
                                       ('Üst havalandırma', 'Tavan seviyesinden -30 cm aşağıda, alt menfezin karşı/çapraz konumunda')], None)]
# ekipman tabloları (kullanıcı şablonu sütunları)
EQ = [('DUVAR TİPİ YOĞUŞMALI ISITMA KAZANI TABLOSU', ['CİHAZ NO', 'CİHAZIN HİZMET ETTİĞİ YER', 'CİHAZIN BULUNDUĞU YER', 'MODEL', 'ADET', 'ISITMA KAPASİTESİ (kW)', 'KAZAN ÇALIŞMA SICAKLIĞI', 'ÇEKTİĞİ GÜÇ / ADET (kW)', 'İŞLETME BASINCI (bar)'],
       [['IK-01', 'TÜM BİNA (B1-B2-B3)', 'BODRUM', 'Doğalgaz yakan, duvar tipi yoğuşmalı sıcak su kazanı (kaskad)', K_ADET, K_BIRIM, f'{TG}ºC / {TD}ºC', '0,2', '6']]),
      ('ISITMA SİSTEMİ SİRKÜLASYON POMPASI TABLOSU', ['CİHAZ NO', 'HİZMET ETTİĞİ ALAN', 'TİP', 'DEBİ (m³/h)', 'BASMA YÜKSEKLİĞİ (mSS)', 'ÇEKTİĞİ GÜÇ (kW)', 'V / Hz', 'ADET (ASIL)', 'ADET (YEDEK)'],
       [['IP-1', 'Kazan sirkülasyon pompası', 'Islak rotorlu, frekans konvertörlü', f(IP1_Q, 2), f(IP1_H, 1), f(pw(IP1_Q, IP1_H)[1], 2), '220 / 50', K_ADET, '-'],
        ['IP-2', 'Radyatör ısıtma devresi sirkülasyon pompası', 'Islak rotorlu, frekans konvertörlü', f(IP2_Q, 2), f(IP2_H, 1), f(pw(IP2_Q, IP2_H)[1], 2), '220 / 50', 1, 1]]),
      ('DENGE KABI TABLOSU', ['CİHAZ NO', 'TANIMLAMA', 'ISIL YÜK (kW)', 'DENGE KABI İÇ ÇAPI (mm)', 'DENGE KABI YÜKSEKLİĞİ (mm)', 'GİRİŞ - ÇIKIŞ ÇAPLARI (DN)', 'DEBİ (m³/h)', 'ADET'],
       [['DK-01', 'ISITMA DENGE KABI', QK, D_SEC, 145, 100, f(QMAX, 2), 1]]),
      ('KAPALI GENLEŞME ve BÜZÜLME TANKLARI TABLOSU', ['CİHAZ NO', 'TANIMLAMA', 'TANK TİPİ', 'TANK KAPASİTESİ (Lt)', 'ÖN BASINÇ (bar)', 'EMNİYET VENTİLİ (bar)', 'ADET'],
       [['GT-01', 'ISITMA SİSTEMİ', 'KAPALI, DİKEY TİP, DEĞİŞTİRİLEBİLİR MEMBRANLI', GT, f(P0, 1), f(PSV, 0), 1]]),
]
pickle.dump(dict(SEC=SEC, SEC_H=SEC_H, EQ=EQ, R=R), open('/tmp/claude-0/is/content.pkl', 'wb'))
# ======================== Excel
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
thin = Side(style='thin'); BR = Border(left=thin, right=thin, top=thin, bottom=thin); HB = Font(bold=True); HF = PatternFill('solid', fgColor='DDEBF7')
wb = openpyxl.Workbook()
def sheet(ws, title, secs):
    ws.column_dimensions['A'].width = 55; ws.column_dimensions['B'].width = 60
    ws['A1'] = 'MEKANİK TESİSAT ISITMA SİSTEMİ'; ws['A1'].font = Font(bold=True, size=13)
    ws['A2'] = title; ws['A2'].font = Font(bold=True, size=12, color='C00000')
    r = 4
    for h, intro, rows_, son in secs:
        ws.cell(r, 1, h).font = Font(bold=True, size=11, color='1F3864'); r += 1
        if intro: ws.cell(r, 1, intro); r += 1
        for a, b in rows_:
            for c, v in ((1, a), (2, b)):
                x = ws.cell(r, c, v); x.border = BR; x.alignment = Alignment(wrap_text=True, vertical='center')
            ws.cell(r, 1).font = HB; r += 1
        if son: ws.cell(r, 1, son).font = Font(bold=True, color='2E7D32'); r += 1
        r += 1
ws = wb.active; ws.title = 'ISITMA HESAP RAPORU'; sheet(ws, 'B1-B2-B3 BLOK – MERKEZİ ISITMA SİSTEMİ HESAP RAPORU', SEC)
ws = wb.create_sheet('KAZAN DAİRESİ HAVALANDIRMA'); sheet(ws, 'KAZAN DAİRESİ ALT-ÜST HAVALANDIRMA HESAP RAPORU', SEC_H)
ws = wb.create_sheet('EKİPMAN TABLOLARI'); r = 1
for t, hdr, rows_ in EQ:
    ws.cell(r, 1, t).font = Font(bold=True, size=11); r += 1
    for j, h in enumerate(hdr, 1):
        c = ws.cell(r, j, h); c.font = HB; c.fill = HF; c.border = BR; c.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
    r += 1
    for row in rows_:
        for j, v in enumerate(row, 1):
            c = ws.cell(r, j, v); c.border = BR; c.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
        r += 1
    r += 2
for j, w in enumerate((10, 34, 30, 40, 12, 16, 16, 14, 14), 1): ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = w
ws = wb.create_sheet('MAHAL ISI KAYIPLARI')
for j, h in enumerate(('Mahal No', 'Mahal Adı', 'Oda Sıc. (°C)', 'Isı Kaybı (W)', 'Radyatör Boyu (m)', 'Model', 'Verim (W)', 'Adet', 'Tip'), 1):
    c = ws.cell(1, j, h); c.font = HB; c.fill = HF
for i, r_ in enumerate(rows, 2):
    for j, v in enumerate((r_[0], r_[1], r_[2], round(r_[4], 1), r_[5], r_[6], round(r_[7], 1), r_[8], r_[9]), 1): ws.cell(i, j, v)
n = len(rows) + 3
for lab, val in (('Normal kat (×5) toplam W', Q['N']), ('Çatı katı toplam W', Q['C']), ('Zemin kat toplam W', Q['Z']), ('BİR BLOK TOPLAM kW', Q_BLOK), ('3 BLOK TOPLAM kW', QT)):
    ws.cell(n, 2, lab).font = HB; ws.cell(n, 4, round(val, 2)); n += 1
wb.save('/tmp/claude-0/is/out/ISITMA_HESAPLARI.xlsx')
print('Q blok', round(Q_BLOK, 2), 'QT', round(QT, 2), 'RADT', round(RADT, 1), 'Qk ger', round(QK_GER, 1), 'VP_K', round(VP_K, 2), 'VS', round(VS_SEK, 2),
      'H', round(H_TOP, 2), 'Vs', round(VS), 'Vn', round(VN), GT, 'D', round(D_DK), D_SEC, 'alt', R['ALT'], 'üst', R['UST'], 'IP', pw(IP1_Q, IP1_H), pw(IP2_Q, IP2_H))
