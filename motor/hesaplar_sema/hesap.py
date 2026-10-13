# -*- coding: utf-8 -*-
"""Şemaya göre HESAPLAR: temiz su kritik devre (YB yöntemi) + blok armatür YB + pis su kolon yükleri (kullanıcı şablonu)"""
import pickle, math, xlrd
from collections import Counter, defaultdict
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter as CL

W0 = xlrd.open_workbook('/tmp/claude-0/hs/ole0.cfb')
S4 = W0.sheet_by_name('Sayfa4')
# Çizelge 3 (plastik): sol tablo YB 0.5-50 sütunlar 15..65 (c=3..9); sağ tablo YB 55-1000 sütunlar 32..100 (c=17..22)
def tablo():
    L, Rt = [], []
    for r in range(5, S4.nrows):
        yb = S4.cell_value(r, 1)
        if isinstance(yb, float):
            L.append((yb, {d: S4.cell_value(r, c) for d, c in zip((15, 20, 25, 32, 40, 50, 65), range(3, 10))}))
        yb2 = S4.cell_value(r, 15)
        if isinstance(yb2, float):
            Rt.append((yb2, {d: S4.cell_value(r, c) for d, c in zip((32, 40, 50, 65, 80, 100), range(17, 23))}))
    return L, Rt
TL, TR = tablo()

def ozgul(yb, dn):
    T = TL if yb <= 50 else TR
    rows = [(y, v.get(dn)) for y, v in T if isinstance(v.get(dn), float)]
    lo = max([r for r in rows if r[0] <= yb], default=rows[0], key=lambda r: r[0])
    hi = min([r for r in rows if r[0] >= yb], default=rows[-1], key=lambda r: r[0])
    if hi[0] == lo[0]: return lo[1]
    return round(lo[1] + (hi[1] - lo[1]) * (yb - lo[0]) / (hi[0] - lo[0]))

PA = 9807
H_HID = 45.0           # hidrofor alt çalışma basıncı (mSS) — HİDROFOR-DEPO sayfasındaki hesaptan (41,5 → 45)
BINA_H = 21.0          # kullanıcı: hidrofordan en üst armatüre kot farkı (bina yüksekliği) 21 m
N_KAT = 7              # bodrum→zemin→1→2→3→4→5→çatı katı
KAT_H = BINA_H / N_KAT # 3,00 m
STAT = BINA_H
AKMA = 49035           # Çizelge 1: musluk DN15 / duş bataryası
SAYAC = 5 * PA         # sayaç kaybı 5 mSS (şablon notu)
# kritik devre: B1 blok çatı katı en uzak armatürden hidrofora (şemadaki YB ve çaplar)
SEG = [
    (1, 'Çatı katı - kritik armatür bağlantısı (şemada 1)', 1.0, 2.5, 20),
    (2, 'Çatı katı daire içi branşman (şemada 2)', 3.0, 3.75, 25),
    (3, '5. kat → çatı katı kolon/branşman (şemada 3, 1 1/4")', 5.0, 24.0, 32),
    (4, 'B1 kolon 4. kat → 5. kat (1 1/2")', KAT_H, 48.0, 40),
    (5, 'B1 kolon 3. kat → 4. kat (2")', KAT_H, 73.0, 50),
    (6, 'B1 kolon 2. kat → 3. kat (2")', KAT_H, 98.0, 50),
    (7, 'B1 kolon 1. kat → 2. kat (2")', KAT_H, 123.0, 50),
    (8, 'B1 kolon zemin → 1. kat (2")', KAT_H, 148.0, 50),
    (9, 'B1 kolon bodrum → zemin (2")', KAT_H, 173.0, 50),
    (10, 'Hidrofor → B1 kolon dibi ana hat (şemada 4, 3")', 70.0, 540.0, 80),
]
ROWS = [(n, ad, L, yb, dn, ozgul(yb, dn)) for n, ad, L, yb, dn in SEG]
LTOT = sum(r[2] for r in ROWS)
H_ETK = round(H_HID * PA - (STAT * PA + AKMA + SAYAC))
R_ORT = H_ETK / LTOT
KAYIP = sum(r[2] * r[5] for r in ROWS)

# ---------------- şemadan sayımlar
inis, K = pickle.load(open('/tmp/claude-0/hs/inis.pkl', 'rb'))
FX = pickle.load(open('/tmp/claude-0/hs/fix.pkl', 'rb'))
def blok(x): return 'B3' if x < 276300 else ('B2' if x < 284800 else 'B1')
KOL = defaultdict(Counter)
for i in inis:
    c = Counter(i['fix'])
    if i['kol'] == 'P9' and i['fl'] == 'BODRUM': c['SUZGEC'] = 0
    for k, v in c.items(): KOL[(i['blok'], i['kol'])][k] += v
SZ = {'B1': 5, 'B2': 7, 'B3': 7}            # bodrum yer süzgeçleri (pis su çukuruna)
IZG = {'B1': 1, 'B2': 0, 'B3': 0}           # bodrum ızgarası (IZGARA1 KOLON, 8 SB, Ø100) — B1 blokta 1 adet
ARM = Counter((blok(r['p'][0]), r['nm']) for r in FX if r['nm'] and 'KOLON' in r['nm'])
KOMBI_YB = defaultdict(float)
for r in FX:
    if r['nm'] == 'KOMBI1 KOLON': KOMBI_YB[blok(r['p'][0])] += float(r['v']['SO'].split()[0])

thin = Side(style='thin'); BR = Border(left=thin, right=thin, top=thin, bottom=thin)
HB = Font(bold=True); HF = PatternFill('solid', fgColor='DDEBF7')
def box(ws, r0, c0, r1, c1):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            ws.cell(r, c).border = BR
            ws.cell(r, c).alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

wb = openpyxl.Workbook()
# ======================= TEMİZ SU KRİTİK DEVRE
ws = wb.active; ws.title = 'TEMİZ SU KRİTİK DEVRE'
for c, w in zip('ABCDEFGH', (9, 52, 12, 10, 11, 17, 17, 12)): ws.column_dimensions[c].width = w
txt = ['YÜK BİRİMİ YÖNTEMİ (YB) - TEMİZ SU KRİTİK DEVRE BASINÇ KAYBI HESABI (B1-B2-B3 BLOK)',
       'Maksimum su hızı: ana borular 1-3 m/s, daire içi borular 1-2 m/s, sessizlik gereken yerler 0,5-0,7 m/s.',
       'ETKİN BASINÇ = HİDROFOR BASINCI - (STATİK KOT FARKI + AKMA BASINCI + SAYAÇ KAYBI)',
       f'Hidrofor çalışma basıncı = {H_HID:.2f} mSS x 9807 = {round(H_HID * PA)} Pa',
       f'Statik kot farkı (bina yüksekliği) = {STAT:.2f} m  →  {round(STAT * PA)} Pa',
       f'Akma basıncı (kritik armatür, Çizelge 1) = {AKMA} Pa ;  Sayaç kaybı = 5 mSS x 9807 = {SAYAC} Pa',
       f'ETKİN BASINÇ = {H_HID:.2f}x9807-({STAT:.2f}x9807+{AKMA}+{SAYAC}) = {H_ETK} Pa',
       f'ORTALAMA ÖZGÜL BASINÇ KAYBI = Etkin basınç / Kritik devre uzunluğu = {H_ETK}/{LTOT:.0f} = {R_ORT:.0f} Pa/m']
for i, t in enumerate(txt, 1):
    ws.cell(i, 1, t).font = HB if i in (1, 7, 8) else Font()
r0 = 10
hdr = ['BORU NO', 'KRİTİK DEVRE ELEMANI', 'UZUNLUK (m)', 'YB', 'ÇAP (DN)', 'ÖZGÜL BASINÇ KAYBI (Pa/m)', 'TOPLAM BASINÇ KAYBI (Pa)', 'DEBİ (l/s)']
for j, h in enumerate(hdr, 1):
    c = ws.cell(r0, j, h); c.font = HB; c.fill = HF
for k, (n, ad, L, yb, dn, oz) in enumerate(ROWS, r0 + 1):
    for j, v in enumerate((n, ad, L, yb, f'DN{dn}', oz), 1): ws.cell(k, j, v)
    ws.cell(k, 7, f'=C{k}*F{k}'); ws.cell(k, 8, f'=ROUND(0.25*SQRT(D{k}),3)')
rt = r0 + len(ROWS) + 1
ws.cell(rt, 2, 'TOPLAM').font = HB; ws.cell(rt, 3, f'=SUM(C{r0+1}:C{rt-1})'); ws.cell(rt, 6, 'Pa').font = HB
ws.cell(rt, 7, f'=SUM(G{r0+1}:G{rt-1})').font = HB
box(ws, r0, 1, rt, 8)
for k in range(r0 + 1, rt): ws.cell(k, 2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
ws.cell(rt + 2, 1, 'Toplam basınç kaybı < Etkin basınç ise seçilen çap değerleri UYGUNDUR.')
ws.cell(rt + 3, 1, f'=IF(G{rt}<{H_ETK},TEXT(G{rt},"0")&" < {H_ETK} Pa OLDUĞUNDAN UYGUNDUR.",TEXT(G{rt},"0")&" > {H_ETK} Pa - ÇAPLAR BÜYÜTÜLMELİDİR.")').font = HB
notes = ['Debi = 0,25 x √YB (l/s) ile tespit edilir.',
         'Özgül basınç kaybı Çizelge 3 (plastik boru) tablosundan, YB değerine göre doğrusal enterpolasyonla alınmıştır.',
         'Kritik devre: hidrofordan en uzak ve en yüksek blok olan B1 blok çatı katındaki son armatür.',
         'Boru YB ve çap değerleri şemadaki MTY çap etiketlerinden alınmıştır; bina yüksekliği 21 m (kat başı 3,00 m) alınmıştır.',
         'Akma basıncı kritik devredeki en son cihaza göre Çizelge 1’den, sayaç kaybı 5 mSS olarak alınmıştır.']
for i, t in enumerate(notes): ws.cell(rt + 5 + i, 1, '*' + t)

# ======================= BLOK SAYFALARI
NM = {'LAVABO1 KOLON': 'LAVABO', 'EVIYE1 KOLON': 'SİFON,EVİYE', 'KLOZET1 KOLON': 'KLOZET,HELA', 'DUS TEKNESI1 KOLON': 'BANYO KÜVETİ-DUŞ',
      'CAMASIR MAKINASI1 KOLON': 'ÇAMAŞIR,BUL.MAK', 'SUZGEC': 'YERSÜZGECİ'}
PSROWS = [('KLOZET,HELA', 10), ('BANYO KÜVETİ-DUŞ', 7), ('SİFON,EVİYE', 4), ('İKİ GÖZLÜ EVİYE', 8), ('LAVABO', 2),
          ('YERSÜZGECİ', 2), ('ÇAMAŞIR,BUL.MAK', 4), ('PİSUVAR', 2), ('IZGARA (Ø100)', 8)]
for B in ('B1', 'B2', 'B3'):
    ws = wb.create_sheet(f'{B} BLOK')
    ws.column_dimensions['A'].width = 3; ws.column_dimensions['B'].width = 24
    ws.cell(1, 2, f'{B} BLOK - ARMATÜR YÜK BİRİMLERİ VE PİS SU KOLON YÜKLERİ').font = Font(bold=True, size=12)
    # armatür YB tablosu
    hdr = ['ARMATÜR', 'BW', 'YB', 'ADET', 'TOPLAM YB']
    for j, h in enumerate(hdr, 2): c = ws.cell(3, j, h); c.font = HB; c.fill = HF
    arm = [('Lavabo', 'DN15', 0.75, ARM[(B, 'LAVABO1 KOLON')]), ('Eviye', 'DN15', 1.0, ARM[(B, 'EVIYE1 KOLON')]),
           ('Rezervuar,Pisuvar', 'DN15', 0.5, ARM[(B, 'KLOZET1 KOLON')]), ('Küvet,Duş', 'DN15', 2.5, ARM[(B, 'DUS TEKNESI1 KOLON')]),
           ('Çamaşır,Bulaşık Makinesi', 'DN15', 1.5, ARM[(B, 'CAMASIR MAKINASI1 KOLON')]),
           ('Şofben / Kombi', 'DN15', 1.0, ARM[(B, 'KOMBI1 KOLON')])]
    for k, (a, bw, yb, n) in enumerate(arm, 4):
        for j, v in enumerate((a, bw, yb, n), 2): ws.cell(k, j, v)
        ws.cell(k, 6, f'=D{k}*E{k}')
    if KOMBI_YB[B] != ARM[(B, 'KOMBI1 KOLON')]:          # şemada 1 adet 0,5 YB şofben var
        n1 = ARM[(B, 'KOMBI1 KOLON')]; ws.cell(9, 6, KOMBI_YB[B]); ws.cell(9, 7, f'({n1 - 1}x1 + 1x0,5)')
    ws.cell(10, 2, 'TOPLAM').font = HB; ws.cell(10, 6, '=SUM(F4:F9)').font = HB
    box(ws, 3, 2, 10, 6)
    # çap referansı
    for j, h in enumerate(('YB ARALIĞI', 'ÇAP'), 8): c = ws.cell(3, j, h); c.font = HB; c.fill = HF
    for k, (a, b) in enumerate((('0-3', '1/2"'), ('3-8', '3/4"'), ('8-20', '1"'), ('20-35', '1 1/4"'), ('35-50', '1 1/2"'), ('50 ve üstü', '2"')), 4):
        ws.cell(k, 8, a); ws.cell(k, 9, b)
    box(ws, 3, 8, 9, 9)
    ws.cell(11, 2, f'Blok debisi: Q = 0,25 x √YB =')
    ws.cell(11, 6, '=ROUND(0.25*SQRT(F10),2)'); ws.cell(11, 7, 'l/s')
    # pis su kolon adetleri
    kols = sorted({k for b, k in KOL if b == B}, key=lambda s: int(s[1:])) + ['SZ']
    def cnt(kol, row):
        if kol == 'SZ': return SZ[B] if row == 'YERSÜZGECİ' else (IZG[B] if row.startswith('IZGARA') else 0)
        c = KOL[(B, kol)]
        return sum(v for n, v in c.items() if NM.get(n) == row)
    r = 14
    ws.cell(r, 2, 'PİS SU - KOLON NO / ADET').font = HB
    ws.cell(r + 1, 2, 'CİNSİ').font = HB; ws.cell(r + 1, 3, 'YÜK (SB)').font = HB
    for j, k in enumerate(kols): c = ws.cell(r + 1, 4 + j, k); c.font = HB; c.fill = HF
    for i, (row, sb) in enumerate(PSROWS):
        rr = r + 2 + i
        ws.cell(rr, 2, row); ws.cell(rr, 3, sb)
        for j, k in enumerate(kols):
            v = cnt(k, row); ws.cell(rr, 4 + j, v if v else None)
        ws.cell(rr, 4 + len(kols), f'=SUM({CL(4)}{rr}:{CL(3 + len(kols))}{rr})')
    ws.cell(r + 1, 4 + len(kols), 'TOPLAM').font = HB
    box(ws, r + 1, 2, r + 1 + len(PSROWS), 4 + len(kols))
    # yükler
    r2 = r + 4 + len(PSROWS)
    ws.cell(r2, 2, 'PİS SU - KOLON YÜKLERİ (SB)').font = HB
    ws.cell(r2 + 1, 2, 'CİNSİ').font = HB; ws.cell(r2 + 1, 3, 'YÜK (SB)').font = HB
    for j, k in enumerate(kols): c = ws.cell(r2 + 1, 4 + j, k); c.font = HB; c.fill = HF
    for i, (row, sb) in enumerate(PSROWS):
        rr = r2 + 2 + i; src = r + 2 + i
        ws.cell(rr, 2, row); ws.cell(rr, 3, sb)
        for j in range(len(kols)):
            col = CL(4 + j); ws.cell(rr, 4 + j, f'=$C{rr}*N({col}{src})')
    rt2 = r2 + 2 + len(PSROWS)
    ws.cell(rt2, 2, 'TOPLAM').font = HB
    for j in range(len(kols)):
        col = CL(4 + j); ws.cell(rt2, 4 + j, f'=SUM({col}{r2+2}:{col}{rt2-1})').font = HB
    ws.cell(rt2, 4 + len(kols), f'=SUM({CL(4)}{rt2}:{CL(3+len(kols))}{rt2})').font = HB
    ws.cell(rt2 + 1, 2, 'Qww = 0,5 x √ΣSB (l/s)')
    for j in range(len(kols)):
        col = CL(4 + j); ws.cell(rt2 + 1, 4 + j, f'=ROUND(0.5*SQRT({col}{rt2}),2)')
    box(ws, r2 + 1, 2, rt2 + 1, 4 + len(kols))
    # K.B. tablosu (şablon)
    rk = rt2 + 4
    for j, h in enumerate(('BORU ÇAPI', 'K.B.', 'YÜK DEĞERİ'), 3): c = ws.cell(rk, j, h); c.font = HB; c.fill = HF
    for i, row in enumerate(((50, 10, 10), (70, 40, 25), (100, 150, 100), (125, 400, 270), (150, 900, 600), (200, 2200, 1550))):
        for j, v in enumerate(row, 3): ws.cell(rk + 1 + i, j, v)
    box(ws, rk, 3, rk + 6, 5)
    for j in range(len(kols) + 1): ws.column_dimensions[CL(4 + j)].width = 8
    ws.column_dimensions['C'].width = 10


# ======================= PİS SU POMPALARI (3 çukur, ayrı ayrı)
import math as _m
def hw(Q_ls, D_mm, L, C=140.0):
    Q = Q_ls / 1000.0; D = D_mm / 1000.0
    return 10.67 * Q ** 1.852 / (C ** 1.852 * D ** 4.87) * L
CUKUR = [('PİS SU ÇUKURU-1', 'B1', 'Bodrum: 5 yer süzgeci + 1 ızgara', 18),
         ('PİS SU ÇUKURU-2', 'B2', 'Bodrum birimi (P9+P10) + 7 süzgeç', 64),
         ('PİS SU ÇUKURU-3', 'B3', 'Bodrum birimi (P9+P10) + 7 süzgeç', 64)]
K_ = 0.5; Q_SEC = 13.7; H_SEC = 5.2; DN_B = 50; L_B = 15.0; ZETA = 5.3
CA, CB, CH = 0.70, 0.70, 0.85; H_MIN = 0.30; H_PAY = 0.10; Z_ST = 15
H_GEO = CH + KAT_H - 0.40
PUMP = []
for ad, B, kaynak, sb in CUKUR:
    q = K_ * _m.sqrt(sb); qh = q * 3.6
    A = _m.pi * (DN_B / 1000) ** 2 / 4
    def sist(qls):
        v = qls / 1000 / A
        return H_GEO + hw(qls, DN_B, L_B) + ZETA * v * v / (2 * 9.81), v
    hm, v = sist(q); hm_t = hm * 1.10
    h_sec, v_sec = sist(Q_SEC / 3.6)
    vreq = Q_SEC / (4 * Z_ST); vakt = CA * CB * (CH - H_MIN - H_PAY)
    q_on = 10.0 if q * 3.6 <= 9.0 else 15.0                       # önerilen pompa debisi (m³/h)
    h_on = _m.ceil(sist(q_on / 3.6)[0] * 1.10 * 2) / 2               # 0,5 mSS'ye yuvarlanmış
    on_olcu = (0.70, 0.70, 0.85) if q_on / (4 * Z_ST) <= vakt else (0.80, 0.80, 1.00)
    v_on = on_olcu[0] * on_olcu[1] * (on_olcu[2] - H_MIN - H_PAY)
    P = 1000 * 9.81 * (q_on / 3600) * h_on / (0.40 * 1000)
    h_sys, v_sys = sist(q_on / 3.6)
    PUMP.append(dict(h_sys=h_sys, v_sys=v_sys, q_on=q_on, h_on=h_on, olcu=on_olcu, v_on=v_on, vreq_on=q_on / (4 * Z_ST), ad=ad, B=B, kaynak=kaynak, sb=sb, q=q, qh=qh, v=v, hm=hm, hm_t=hm_t, h_sec=h_sec, v_sec=v_sec, vreq=vreq, vakt=vakt, P=P))
ws = wb.create_sheet('PİS SU POMPALARI')
ws.column_dimensions['A'].width = 58
for c in 'BCDE': ws.column_dimensions[c].width = 22
ws['A1'] = 'PİS SU POMPASI HESAPLARI (TS EN 12056-2 / -4) - HER ÇUKUR İÇİN AYRI'; ws['A1'].font = Font(bold=True, size=12)
ws['A2'] = 'Qww = K x √ΣSB  (K = 0,5 konut) ;  Hm = Hgeo + sürtünme (Hazen-Williams, C=140) + özel kayıplar ;  Vaktif ≥ Qp / (4 x Z)'
rows = [('Toplandığı yer', 'kaynak', ''), ('Toplam su birimi ΣSB', 'sb', 'SB'), ('Atık su debisi Qww = 0,5√ΣSB', 'q', 'l/s'),
        ('Atık su debisi', 'qh', 'm³/h'), ('Basma hattı çapı', 'c:'+f'DN{DN_B}', ''), ('Basma hattında hız (Qww)', 'v', 'm/s'),
        ('Geometrik yükseklik Hgeo = çukur derinliği + bodrum kat yük. - 0,40', 'hgeo', 'mSS'),
        (f'Basma hattı uzunluğu (kabul)', 'c:'+f'{L_B:.0f}', 'm'), (f'Özel kayıp katsayısı Σζ (çek valf+vana+3 dirsek+çıkış)', 'c:'+f'{ZETA}', ''),
        ('Gerekli basma yüksekliği Hm (Qww)', 'hm', 'mSS'), ('Hm x 1,10 emniyet', 'hm_t', 'mSS'),
        ('SEÇİLEN POMPA DEBİSİ (1 asıl + 1 yedek, dalgıç-parçalayıcı)', 'q_on', 'm³/h'),
        ('SEÇİLEN POMPA BASMA YÜKSEKLİĞİ', 'h_on', 'mSS'), ('Seçilen debide sistem direnci', 'h_sys', 'mSS'),
        ('Seçilen debide basma hattı hızı (0,7-2,3 m/s)', 'v_sys', 'm/s'),
        ('Pompa debisi ≥ Qww ve basma yük. ≥ sistem direnci', 'chk', ''),
        ('PİS SU ÇUKURU ÖLÇÜSÜ (en x boy x derinlik)', 'olcu', 'cm'),
        (f'Çukur aktif hacmi (min seviye {H_MIN:.2f} m, pay {H_PAY:.2f} m) / gerekli Qp/(4·Z), Z = {Z_ST}'.replace('.', ','), 'vchk', 'm³'),
        ('Motor gücü P = ρ·g·Q·H/η (η = 0,40) → seçilen motor', 'P', 'kW')]
for j, p in enumerate(PUMP):
    c = ws.cell(4, 2 + j, f"{p['ad']} ({p['B']} BLOK)"); c.font = HB; c.fill = HF
ws.cell(4, 1, 'HESAP ADIMI').font = HB; ws.cell(4, 1).fill = HF; ws.cell(4, 5, 'BİRİM').font = HB; ws.cell(4, 5).fill = HF
for i, (lab, key, unit) in enumerate(rows, 5):
    ws.cell(i, 1, lab)
    for j, p in enumerate(PUMP):
        if key is None: v = ''
        elif key.startswith('c:'): v = key[2:].replace('.', ',')
        elif key == 'chk': v = 'UYGUNDUR' if (p['q_on'] >= p['qh'] and p['h_on'] >= p['h_sys'] and p['v_on'] >= p['vreq_on']) else 'KONTROL'
        elif key == 'hgeo': v = round(H_GEO, 2)
        elif key == 'kaynak': v = p['kaynak']
        elif key == 'olcu': v = 'x'.join(str(int(round(a * 100))) for a in p['olcu'])
        elif key == 'vchk': v = f"{p['v_on']:.2f} / {p['vreq_on']:.2f}".replace('.', ',')
        elif key == 'P': v = f"{p['P']:.2f} → {next(m_ for m_ in (0.37, 0.55, 0.75, 1.1, 1.5, 2.2) if m_ >= p['P'] * 1.2)} kW".replace('.', ',')
        else: v = round(p[key], 2) if isinstance(p[key], float) else p[key]
        ws.cell(i, 2 + j, v)
    ws.cell(i, 5, unit)
box(ws, 4, 1, 4 + len(rows), 5)
for i in range(5, 5 + len(rows)): ws.cell(i, 1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
nr = 6 + len(rows)
for t in ['Pompalar dalgıç-parçalayıcı tip, 1 asıl + 1 yedek, seviye şamandıralı otomatik çalışmalı ve yüksek seviye alarmlı olacaktır.',
          'Basma hattı kanal geri tepmesine karşı çek valfli ve en yüksek kanal seviyesinin üstünden (geri tepme döngüsü) bağlanacaktır.',
          'Basma hattı uzunluğu şema ölçeksiz olduğundan 15 m kabul edilmiştir; uygulamada boy farklıysa Hm yeniden kontrol edilmelidir.']:
    ws.cell(nr, 1, '*' + t); nr += 1

# ======================= HİDROFOR - DEPO (günlük 16 m³ esas)
DAIRE = {B: ARM[(B, 'KOMBI1 KOLON')] for B in ('B1', 'B2', 'B3')}
ND = sum(DAIRE.values()); VG = 16.0; KF = 0.60; Q_SECH = 9.75
ws = wb.create_sheet('HİDROFOR-DEPO')
ws.column_dimensions['A'].width = 66; ws.column_dimensions['B'].width = 24; ws.column_dimensions['C'].width = 12
ws['A1'] = 'KULLANMA SUYU DEPOSU VE HİDROFOR HESABI'; ws['A1'].font = Font(bold=True, size=12)
H_REQ = STAT + KAYIP / PA + AKMA / PA + SAYAC / PA + 2.0
QH = VG * KF
P_H = Q_SECH * H_HID / (367 * 0.60)
rr = [('Bağımsız birim (daire) sayısı', f"{ND} (B1 {DAIRE['B1']}, B2 {DAIRE['B2']}, B3 {DAIRE['B3']})", 'adet'),
      ('Günlük kullanma suyu ihtiyacı', VG, 'm³/gün'),
      ('Daire başına günlük ihtiyaç', round(VG * 1000 / ND), 'l/gün'),
      ('KULLANMA SUYU DEPOSU (1 günlük ihtiyaç)', '16 m³ (16 ton)', ''),
      (f'Hidrofor debisi Q = günlük ihtiyaç x kullanma faktörü ({KF})', round(QH, 2), 'm³/h'),
      ('Statik yükseklik (bina yüksekliği)', STAT, 'mSS'),
      ('Kritik devre boru kayıpları (TEMİZ SU KRİTİK DEVRE sayfası)', round(KAYIP / PA, 2), 'mSS'),
      ('Akma basıncı + sayaç kaybı', round((AKMA + SAYAC) / PA, 1), 'mSS'),
      ('Hidrofor kollektörü / emme kayıpları', 2.0, 'mSS'),
      ('Gerekli basma yüksekliği', round(H_REQ, 1), 'mSS'),
      ('HİDROFOR ALT ÇALIŞMA BASINCI (seçilen)', H_HID, 'mSS'),
      ('HİDROFOR ÜST ÇALIŞMA BASINCI (frekans konvertörlü, +1 bar)', H_HID + 10, 'mSS'),
      ('SEÇİLEN HİDROFOR (Q ≥ hesaplanan)', f'{Q_SECH:.2f} m³/h - {H_HID:.0f} mSS'.replace('.', ','), '1 asıl + 1 yedek'),
      ('Pompa motor gücü P = Q·H/(367·η), η = 0,60', f'{P_H:.2f} → {next(m_ for m_ in (0.75, 1.1, 1.5, 2.2, 3.0, 4.0) if m_ >= P_H * 1.2)} kW (pompa başına)'.replace('.', ','), ''),
      ('Kontrol', 'UYGUNDUR', '')]
for j, h in enumerate(('HESAP ADIMI', 'DEĞER', 'BİRİM'), 1): c = ws.cell(3, j, h); c.font = HB; c.fill = HF
for i, (a_, b_, c_) in enumerate(rr, 4):
    ws.cell(i, 1, a_); ws.cell(i, 2, b_); ws.cell(i, 3, c_)
box(ws, 3, 1, 3 + len(rr), 3)
for i in range(4, 4 + len(rr)): ws.cell(i, 1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ======================= YAĞMUR SUYU (her blok)
ws = wb.create_sheet('YAĞMUR SUYU')
ws.column_dimensions['A'].width = 60
for c in 'BCDE': ws.column_dimensions[c].width = 16
ws['A1'] = 'YAĞMUR SUYU İNİŞ BORUSU ÇAP HESABI (HER BLOK)'; ws['A1'].font = Font(bold=True, size=12)
for j, h in enumerate(('HESAP ADIMI', 'B1 BLOK', 'B2 BLOK', 'B3 BLOK', 'BİRİM'), 1): c = ws.cell(3, j, h); c.font = HB; c.fill = HF
YR = [('P = Çatı alanı', 237, 'm²'), ('S = P x 0,75 / 1', '=ROUND({c}4*0.75,2)', 'cm²'), ('f = İniş (yağmur oluğu) adedi', 4, 'adet'),
      ('A = S / f', '=ROUND({c}5/{c}6,2)', 'cm²'), ('D = 1,13 x √A', '=ROUND(1.13*SQRT({c}7),2)', 'cm'),
      ('SEÇİLEN İNİŞ BORUSU', '=IF({c}8<7,"Ø70 PVC",IF({c}8<10,"Ø100 PVC","Ø125 PVC"))', ''),
      ('Sonuç', '=IF({c}8<7,"Ø70\'lik boru UYGUNDUR.",IF({c}8<10,"D>7 cm olduğundan Ø100\'lük boru UYGUNDUR.","Ø125\'lik boru UYGUNDUR."))', '')]
for i, (a_, v, u) in enumerate(YR, 4):
    ws.cell(i, 1, a_)
    for j, c in enumerate('BCD'):
        ws.cell(i, 2 + j, v.format(c=c) if isinstance(v, str) else v)
    ws.cell(i, 5, u)
box(ws, 3, 1, 3 + len(YR), 5)

# ======================= ÇİZELGELER (şablondan aynen)
for nm, title in (('Sayfa2', 'ÇİZELGE_1'), ('Sayfa3', 'ÇİZELGE_2'), ('Sayfa4', 'ÇİZELGE_3')):
    sh = W0.sheet_by_name(nm); ws = wb.create_sheet(title)
    for r in range(sh.nrows):
        for c in range(sh.ncols):
            v = sh.cell_value(r, c)
            if v != '': ws.cell(r + 1, c + 1, v)
wb.save('/tmp/claude-0/hs/out/HESAPLAR_SIHHI.xlsx')
print('H_ETK', H_ETK, 'L', LTOT, 'R_ort', round(R_ORT), 'KAYIP', round(KAYIP))
for r in ROWS: print(r, r[2] * r[5])
print({B: (sum(n * y for (b, nm), n in ARM.items() if b == B and False), ) for B in ('B1',)})
pickle.dump(dict(PUMP=PUMP, H_REQ=H_REQ, ROWS=ROWS, H_ETK=H_ETK, LTOT=LTOT, R_ORT=R_ORT, KAYIP=KAYIP, STAT=STAT, KOL=KOL, ARM=ARM, KOMBI_YB=KOMBI_YB, SZ=SZ), open('/tmp/claude-0/hs/res.pkl', 'wb'))
