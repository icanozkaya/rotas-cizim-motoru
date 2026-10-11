"""Cafer Göktaş - örnek 'yerden ısıtma' çalışma kitabından ısı kaybı + yerden ısıtma hesabı (formül yapısı korunur)."""
import copy, math, pickle, datetime, sys
sys.path.insert(0, '/home/claude/nb')
import openpyxl
from openpyxl.utils import get_column_letter as CL
from shapely.geometry import LineString, box
import cg2_heat as H
import cg2_geo as G

SRC = '/tmp/claude-0/xl/ornek_yi.xlsx'
OUT = '/tmp/claude-0/xl/CAFER_GOKTAS_ISI_KAYBI_YERDEN_ISITMA.xlsx'
R_, HEAT = pickle.load(open('/tmp/claude-0/cg2_recs.pkl', 'rb'))
FLOOR_DX = [0.0, 1250.0, 2500.0]
HDY = -1900.0
KAT = ['Z', '1', '2']
SHEET = {'Z': 'ZEMİN', '1': '1 NK', '2': '2 NK'}
ZCODE = lambda k, n: ('Z%02d' % n) if k == 'Z' else int('%s%02d' % (k, n))
ANTRE = box(-5079, -22706, -4966, -22313)
MARK_XL = {'İDA': 'İDMK'}


def copy_style(src, dst):
    if src.has_style:
        dst.font = copy.copy(src.font); dst.border = copy.copy(src.border); dst.fill = copy.copy(src.fill)
        dst.number_format = src.number_format; dst.alignment = copy.copy(src.alignment)
        dst.protection = copy.copy(src.protection)


def clear_rows(ws, r0, r1, c1=17):
    for rng in list(ws.merged_cells.ranges):
        if rng.min_row >= r0 and rng.max_row <= r1:
            ws.unmerge_cells(str(rng))
    for r in range(r0, r1 + 1):
        for c in range(1, c1 + 1):
            ws.cell(r, c).value = None


# ================================================================== ısı kaybı sayfası
def write_heat_sheet(ws, tpl, kat, sheet_no):
    """tpl: şablon sayfası (ZEMİN) - satır stilleri buradan"""
    st = {k: [tpl.cell(r, c) for c in range(1, 18)] for k, r in
          (('hdr', 8), ('el', 9), ('sum', 29), ('qsl', 30), ('qs', 31), ('top', 32))}
    clear_rows(ws, 8, max(ws.max_row, 140))
    ws['O1'] = {'Z': 'ZEMİN ', '1': '1. NORMAL', '2': '2. NORMAL'}[kat]
    ws['O2'] = sheet_no
    ws['Q1'] = '=kapak!G41'
    r = 8
    totals = {}
    for no, nm, ti, A, rows, qs, ze in H.rooms_for(kat):
        def put(rr, kind, vals):
            for c in range(1, 18):
                copy_style(st[kind][c - 1], ws.cell(rr, c))
            for col, v in vals.items():
                ws[col + str(rr)] = v
            ws.row_dimensions[rr].height = 10.35 if kind == 'hdr' else 9.95
        put(r, 'hdr', {'F': kat if kat == 'Z' else kat, 'G': '0', 'H': no, 'I': nm, 'K': '%dºC' % ti})
        ws.merge_cells('I%d:J%d' % (r, r))
        r += 1
        first = r
        rowof = {}
        for mark, yon, l, h, n, tk, sub in rows:
            rowof[mark] = r
            r += 1
        r = first
        dd_row = None
        for mark, yon, l, h, n, tk, sub in rows:
            uk = H.ukey(mark)
            label = MARK_XL.get(mark, mark.rstrip('0123456789') if uk not in ('DD25', 'DD30') else uk)
            dT = ti - (H.T_DIS if tk is None else tk)
            zh = H.ZH.get(yon, 0) if tk is None else 0
            vals = {'A': label, 'B': (yon or ''), 'D': l, 'E': h, 'F': '=IF(D%d=0," ",D%d*E%d)' % (r, r, r), 'G': n,
                    'I': '=IF(F%d=" "," ",F%d*G%d-H%d)' % (r, r, r, r), 'J': H.U[uk], 'K': dT,
                    'L': '=IF(I%d=" "," ",I%d*J%d*K%d)' % (r, r, r, r), 'M': H.ZD, 'N': H.ZW, 'O': zh,
                    'P': '=IF(M%d=" "," ",(1+(M%d+N%d+O%d)/100))' % (r, r, r, r), 'Q': '=IF(L%d=" "," ",L%d*P%d)' % (r, r, r)}
            if uk == 'DD':
                dd_row = r
            if uk == 'DD25' and dd_row is not None and abs(l - rows[[x[0] for x in rows].index(mark) - 1][2]) < 1e-9:
                vals['D'] = '=D%d' % dd_row
            if sub:
                vals['H'] = '=' + '+'.join('F%d*G%d' % (rowof[s], rowof[s]) for s in sub)
            put(r, 'el', vals)
            r += 1
        last = r - 1
        put(r, 'sum', {'F': '=IF(D%d=0," ",D%d*E%d)' % (r, r, r), 'I': '=IF(F%d=" "," ",F%d*G%d-H%d)' % (r, r, r, r),
                       'Q': '=SUM(Q%d:Q%d)' % (first, last)})
        rs = r
        r += 1
        put(r, 'qsl', {'J': 'Qs=', 'K': 'S a', 'L': 'L', 'M': 'R', 'N': 'H', 'O': 'D  T', 'P': 'Ze'})
        r += 1
        if qs:
            lf = '=' + '+'.join('(D%d+E%d)*2*G%d' % (rowof[m], rowof[m], rowof[m]) for m, a, b, nn in qs)
            dto = ti - (H.T_HOL if qs[0][0] == 'DK1' else H.T_DIS)
        else:
            lf, dto = 0, ti - H.T_DIS
        put(r, 'qs', {'A': ' ', 'J': 'Qs  =', 'K': 2, 'L': lf, 'M': 0.9, 'N': 0.67, 'O': dto, 'P': ze,
                      'Q': '=K%d*L%d*M%d*N%d*O%d*P%d' % (r, r, r, r, r, r)})
        rq = r
        r += 1
        put(r, 'top', {'M': '   TOPLAM ISI KAYBI =', 'Q': '=Q%d+Q%d' % (rs, rq)})
        ws.merge_cells('E%d:F%d' % (r, r))
        totals[nm] = r
        r += 1
    return totals


# ================================================================== devre verileri
def circuits():
    out = {}
    for k, (res, tot, calc) in enumerate(HEAT):
        lst = []
        antre_L = 0.0
        for d in res:
            pts = d['path']
            ls = LineString(pts)
            antre_L += ls.intersection(ANTRE).length / 100.0
            m = d['W'] / (1.163 * 10.0)                        # kg/h (50/40)
            q = m / 3600.0 / 990.0
            v = q / (math.pi * 0.006 ** 2)
            Re = v * 0.012 / 0.6e-6
            lam = 0.316 / Re ** 0.25 if Re > 2300 else 64.0 / Re
            Rpm = lam / 0.012 * 990 * v * v / 2
            lst.append(dict(d, m=m, v=v, R=Rpm, dP=Rpm * d['L'], ti=calc[d['room']]['ti']))
        out[KAT[k]] = dict(res=lst, antre_L=antre_L, calc=calc, tot=tot)
    return out


# ================================================================== ana
def build():
    wb = openpyxl.load_workbook(SRC)
    CIR = circuits()
    # ---------------- kapak
    ws = wb['kapak']
    ws['A2'] = ('ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK.\nMak. Müh. Bayram GENÇ\n'
                'Semerciler Mah. Sait Faik Sk. No:22/C Z01 Adapazarı/Sakarya\n'
                'TEL: 0264 272 00 49   rotasmuhendislik@gmail.com\n')
    ws['B10'] = 'BAYRAM GENÇ'; ws['D10'] = None; ws['F10'] = None
    ws['A11'] = 'YERDEN ISITMA (KOMBİLİ) TESİSATI PROJE RAPORU'
    ws['C31'] = 'CAFER GÖKTAŞ - KONUT (ZEMİN + 2 KAT, 3 DAİRE)'
    ws['A36'] = 'SAKARYA'; ws['B36'] = 'ADAPAZARI'; ws['D36'] = 'PAPUÇÇULAR'
    ws['G36'] = 'G24-b-23-c-2-b'; ws['H36'] = 405; ws['I36'] = 381
    ws['A41'] = 'BETONARME'; ws['B41'] = '3A'; ws['C41'] = 3; ws['D41'] = 'ZEMİN + 2'
    ws['G41'] = datetime.datetime(2026, 10, 11); ws['H41'] = 'KONUT'
    # ---------------- teknik rapor
    ws = wb['TEKNİK RAPOR']
    ws['F8'] = '   / SAKARYA'
    ws['E9'] = ': TS 825:2024'; ws['F9'] = ' -6 °C Rüzgarlı (Sakarya)'
    ws['E11'] = ': Duvar tipi hermetik yoğuşmalı kombi (her dairede 1 adet, 24 kW)'
    ws['E13'] = ': Zeminden ısıtma borusu PEX 16x2,0 / 50-40 °C çalışma sıcaklığında 17,5 W/m (şablon değeri)'
    ws['E14'] = ': Bitişik nizam'
    ws['E16'] = ': Zemin + 2 normal kat (her katta 1 daire)'
    ws['E17'] = ': Zeminden ısıtma borusu PEX 16x2,0 (oksijen bariyerli)'
    ws['F21'] = ': 22°C'; ws['F22'] = ': 20°C'; ws['F23'] = ': 20°C'; ws['F24'] = ': 26°C'
    ws['F25'] = ': 18°C (kollektör bağlantı boruları ile ısıtılır)'
    ws['F26'] = None; ws['F27'] = None; ws['F28'] = None
    ws['F29'] = ':   0°C'; ws['F30'] = ':   6°C'; ws['F31'] = ': 22°C (salon ile birleşik)'
    ws['B37'] = 'Kolon (dış) 30 cm'
    ws['F35'] = H.U['DD']; ws['F36'] = H.U['DD25']; ws['F37'] = H.U['DD30']; ws['F38'] = H.U['DK']
    ws['F39'] = H.U['ÇP']; ws['F40'] = 0; ws['F41'] = H.U['İDM']; ws['F42'] = H.U['İDA']; ws['F43'] = H.U['Dö']
    ws['F44'] = H.U['Ta']; ws['F45'] = 0; ws['F46'] = 0; ws['F47'] = 0; ws['F48'] = H.U['İD']
    ws['H35'] = 'TS 825:2024 sınır 0,40 - 19 cm tuğla + 8 cm EPS'
    ws['H36'] = 'sınır 0,40 - betonarme + 8 cm EPS'
    ws['H37'] = 'sınır 0,40 - betonarme + 8 cm EPS'
    ws['H38'] = 'yalıtımlı çelik daire kapısı (hole açılır)'
    ws['H39'] = 'sınır 1,8 - PVC + Low-E ısıcam, g ≤ 0,45'
    ws['H40'] = 'ısıtılan kat üstü - hesaba girmez'
    ws['H41'] = 'merdiven holü / komşu bina duvarı - 19 cm tuğla + 8 cm EPS (sınır 0,40)'
    ws['H42'] = 'asansör / hol betonarme - 20 cm + 8 cm EPS (sınır 0,40)'
    ws['H43'] = 'sınır 0,35 - 10 cm XPS (toprağa oturan)'
    ws['H44'] = 'sınır 0,30 - 14 cm taşyünü (çatı arası altı)'
    ws['H48'] = 'ısıtılan hacimler arası - sınır yok'
    # ---------------- ısı kaybı sayfaları
    tpl = wb['ZEMİN']
    tot_rows = {}
    tot_rows['Z'] = write_heat_sheet(wb['ZEMİN'], tpl, 'Z', 3)
    ws1 = wb['1 NK']
    tot_rows['1'] = write_heat_sheet(ws1, tpl, '1', 4)
    ws2 = wb.copy_worksheet(ws1)
    ws2.title = '2 NK'
    wb.move_sheet('2 NK', offset=-(len(wb.sheetnames) - 1 - wb.sheetnames.index('1 NK') - 1))
    tot_rows['2'] = write_heat_sheet(ws2, tpl, '2', 5)
    # ---------------- petek list (mahal / boru boyu özeti)
    ws = wb['PETEK LİST']
    clear_rows(ws, 10, 40, 16)
    tplr = [ws.cell(10, c) for c in range(1, 17)]
    tpls = [ws.cell(15, c) for c in range(1, 17)]
    r = 10
    PROW = {}
    order = ['SALON + MUTFAK', 'ODA', 'ODA 2', 'BANYO + WC', 'ANTRE']
    for k in KAT:
        c = CIR[k]
        r0 = r
        for i, nm in enumerate(order):
            n = G.ZONE_NO[nm]
            if nm == 'ANTRE':
                L = c['antre_L']
            else:
                L = sum(d['L'] for d in c['res'] if d['room'] == nm)
            vals = {'A': ZCODE(k, n), 'B': nm, 'C': str(c['calc'][nm]['ti']),
                    'D': "=%s!Q%d" % ("'%s'" % SHEET[k] if k != 'Z' else 'ZEMİN', tot_rows[k][nm]),
                    'E': 17.5, 'F': "='YERDEN ISITMA'!N%d" % r, 'G': round(L, 2), 'H': 1,
                    'I': 'ZEMİNDEN ISITMA' + (' (BAĞLANTI BORULARI)' if nm == 'ANTRE' else '')}
            for cc in range(1, 17):
                copy_style(tplr[cc - 1], ws.cell(r, cc))
            for col, v in vals.items():
                ws[col + str(r)] = v
            ws.merge_cells('I%d:P%d' % (r, r))
            PROW[(k, nm)] = r
            r += 1
        for cc in range(1, 17):
            copy_style(tpls[cc - 1], ws.cell(r, cc))
        ws['E%d' % r] = 'TOPLAM ='; ws['F%d' % r] = '=SUM(F%d:F%d)' % (r0, r - 1); ws['G%d' % r] = 'watt'
        r += 1
    ws['C1'] = 'MAHAL VE YERDEN ISITMA BORU BOYU ÇİZELGESİ'
    ws['A1'] = 'ROTAŞ'
    ws['N3'] = datetime.datetime(2026, 10, 11)
    # ---------------- yerden ısıtma (modülasyon)
    ws = wb['YERDEN ISITMA']
    clear_rows(ws, 10, 40, 14)
    tplr = [ws.cell(10, c) for c in range(1, 15)]
    ws['A1'] = 'ROTAŞ'
    ws['H6'] = 'BAYRAM GENÇ'
    for (k, nm), rr in PROW.items():
        c = CIR[k]
        ds = [d for d in c['res'] if d['room'] == nm]
        A = sum(d['A'] for d in ds) if ds else 4.62
        s = ds[0]['s'] if ds else 15
        vals = {'A': "='PETEK LİST'!A%d" % rr, 'B': "='PETEK LİST'!B%d" % rr, 'C': "='PETEK LİST'!C%d" % rr,
                'D': "='PETEK LİST'!D%d" % rr, 'E': round(A, 2), 'F': '=D%d/E%d' % (rr, rr), 'G': '=76.263-0.539*F%d' % rr,
                'H': '=D%d/G%d' % (rr, rr), 'I': s, 'J': "='PETEK LİST'!G%d" % rr, 'K': '=J%d/80' % rr,
                'L': max(1, len(ds)), 'M': 17.5, 'N': '=J%d*M%d' % (rr, rr)}
        for cc in range(1, 15):
            copy_style(tplr[cc - 1], ws.cell(rr, cc))
        for col, v in vals.items():
            ws[col + str(rr)] = v
    # ---------------- MMO yerden ısıtma (devre bazında)
    def mmo(ws, kats, title):
        clear_rows(ws, 7, 35, 50)
        tpl_col = [ws.cell(rr, 6) for rr in range(1, 48)]
        ws['A2'] = title
        n = sum(len(CIR[k]['res']) for k in kats)
        ws['D3'] = 'Isıtma Çevrim Sayısı : %d' % n
        ws['D5'] = 'Mak. Müh. Bayram GENÇ'
        labels = {7: ('ISITMA ÇEVRİM SIRASI',), }
        # A-E sütunları (satır başlıkları) şablondan korunur; yalnız devre sütunları yazılır
        col = 6
        cols = []
        for k in kats:
            for d in CIR[k]['res']:
                C = CL(col)
                below = 6 if k == 'Z' else d['ti']
                v = {7: 'P%d' % d['port'], 8: str(d['zl']), 9: d['room'], 10: d['ti'], 11: below, 12: round(d['A'], 2),
                     13: round(d['W'], 1), 14: '=%s13/%s12' % (C, C), 15: 0.012, 16: 1, 17: '=%s12' % C,
                     18: '=%s13/%s17' % (C, C), 19: '=%s10+(%s14/8.92)^0.91' % (C, C), 20: 50, 21: '=%s20-%s10' % (C, C),
                     22: d['s'], 23: 45, 24: '=%s23-%s10' % (C, C), 25: '=2*(%s21-%s24)' % (C, C),
                     26: '=0.2*%s14' % C, 27: '=%s17*(%s14+%s26)' % (C, C, C), 28: '=%s27/(1.163*%s25)' % (C, C),
                     29: '=%s17/(%s22*0.01)' % (C, C), 30: round(d['L'] - d['A'] / (d['s'] / 100.0), 2),
                     31: '=%s29+%s30' % (C, C), 32: round(d['dP']), 33: '=%s32*0.05' % C, 34: '=%s32+%s33' % (C, C)}
                for rr, val in v.items():
                    copy_style(tpl_col[rr - 1], ws.cell(rr, col))
                    ws.cell(rr, col).value = val
                cols.append(C)
                col += 1
        for C in cols:
            copy_style(tpl_col[34], ws[C + '35'])
            ws[C + '35'] = '=MAX(%s34:%s34)-%s34' % (cols[0], cols[-1], C)
        ws['D36'] = 'Δpmax = en uzun devrenin basınç kaybı (Pa)'
        ws['E2'] = 'TOPLAM ISI KAYBI = %.0f W' % sum(CIR[k]['tot'] for k in kats)
        ws['E3'] = 'MAX. BASINÇ KAYBI = %.0f Pa' % max(d['dP'] * 1.05 for k in kats for d in CIR[k]['res'])
        ws['C30'] = 'BAĞLANTI BORULARI'; ws['D30'] = 'Kat Planından (çizimden ölçülen)'
        ws['C31'] = 'TOPLAM BORU UZUNLUĞU'; ws['D31'] = 'Lç + Lb (çizimden ölçülen toplam)'
        ws['C28'] = 'SICAK SU DEBİSİ'; ws['D28'] = 'q/(1,163.ΔTs)'
        ws['C32'] = 'DÜZ BORU BASINÇ KAYBI (5)'; ws['D32'] = 'R.L (PEX 16x2,0, Blasius)'
        for rr in range(36, 47):
            for cc in range(8, 30):
                ws.cell(rr, cc).value = None
        ws['B41'] = 'Sıcak su girişi (kombi gidiş suyu sıcaklığı) 50 °C, dönüş 40 °C (ortalama 45 °C) seçilmiştir.'
        ws['B42'] = 'Ortalama su sıcaklığı 50/40 °C rejimine göre 45 °C alınmıştır.'
        ws['B44'] = 'R (Pa/m): PEX 16x2,0 (iç çap 12 mm), 45 °C su, Blasius bağıntısı ile hesaplanmıştır.'
        ws['B46'] = 'Isıtma devrelerinin basıncı kollektördeki debimetreli reglaj vanası ile ayarlanmalıdır.'
        ws['B43'] = 'Alta geçen ısı 0,2 q" olarak alınmıştır (ara katlarda alt daire ısıtılmaktadır).'
    mmo(wb['MMO YERDEN ISITMA'], ['Z', '1'], 'ZEMİN ve 1.KAT')
    mmo(wb['YERDEN ISITMA- DEVAMI'], ['2'], '2. KAT')
    wb['YERDEN ISITMA- DEVAMI']['M5'] = None
    wb.save(OUT)
    return CIR


if __name__ == '__main__':
    CIR = build()
    print('kaydedildi', OUT)
    for k, c in CIR.items():
        print(k, round(c['antre_L'], 2), [(d['port'], round(d['m'], 1), round(d['v'], 3), round(d['R']), round(d['dP'])) for d in c['res']])
