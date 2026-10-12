"""Sinem Turhan - ısı kaybı / yerden ısıtma / hidrofor-pompa / yağmur hesap kitabı"""
import datetime, pickle, sys
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import openpyxl
from openpyxl.utils import get_column_letter as CL
import gheat as H
import gexcel as X

OUT = '/tmp/claude-0/p2/out/SINEM_TURHAN_ISI_KAYBI_YERDEN_ISITMA_HIDROFOR.xlsx'
D = pickle.load(open('/tmp/claude-0/p2/st_calc.pkl', 'rb'))
HEAT, ROOMS = D['HEAT'], {'a': D['ROOMS']}
P = dict(proje="SİNEM TURHAN'A AİT 3 BAĞIMSIZ BÖLÜMLÜ MESKEN (SERDİVAN 13748 PARSEL)")
FL = [('B1', 'BODRUM', 'zemin', ('DAİRE 1',)), ('Z', 'ZEMİN', 'ara', ('DAİRE 2',)), ('1', '1 NK', 'ust', ('DAİRE 3',))]


def zone_of(k, side, nm):
    circ = HEAT[k][side][0]
    for c in circ:
        if c['room'] == nm:
            return c['zone']
    return '%s08' % {'B1': 'B', 'Z': 'Z', '1': '1'}[k]     # HOL


def build():
    wb = openpyxl.load_workbook(X.SRC)
    ws = wb['kapak']
    ws['A2'] = ('ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK.\nMak. Müh. Bayram GENÇ\n'
                'Semerciler Mah. Sait Faik Sk. No:22/C Z01 Adapazarı/Sakarya\nTEL: 0264 272 00 49   rotasmuhendislik@gmail.com\n')
    ws['B10'] = 'BAYRAM GENÇ'; ws['D10'] = None; ws['F10'] = None
    ws['A11'] = 'YERDEN ISITMA (KOMBİLİ) TESİSATI PROJE RAPORU'
    ws['C31'] = 'SİNEM TURHAN - MESKEN (2 BODRUM + ZEMİN + 1 KAT, 3 DAİRE)'
    ws['A36'] = 'SAKARYA'; ws['B36'] = 'SERDİVAN'; ws['D36'] = 'SERDİVAN'
    ws['G36'] = '28J1'; ws['H36'] = '-'; ws['I36'] = 13748
    ws['A41'] = 'BETONARME'; ws['B41'] = '3B'; ws['C41'] = 4; ws['D41'] = '2B + Z + 1'
    ws['G41'] = datetime.datetime(2026, 10, 11); ws['H41'] = 'KONUT'
    ws = wb['TEKNİK RAPOR']
    ws['F8'] = '   / SAKARYA'
    ws['E9'] = ': TS 825'; ws['F9'] = ' -6 °C (Sakarya)'
    ws['E10'] = ': Konut (3 daire)'
    ws['E11'] = ': Duvar tipi hermetik yoğuşmalı kombi (her dairede 1 adet, 24 kW)'
    ws['E12'] = ': Doğalgaz'
    ws['E13'] = ': Zeminden ısıtma borusu PEX 16x2,0 / 45-35 °C'
    ws['E14'] = ': Ayrık nizam'
    ws['E16'] = ': 2. bodrum (müştemilat) + 1. bodrum + zemin + 1. kat (her katta 1 daire)'
    ws['E17'] = ': Zeminden ısıtma borusu PEX 16x2,0 (oksijen bariyerli)'
    ws['E18'] = ': 45 - 35 °C'
    ws['F21'] = ': 22°C'; ws['F22'] = ': 20°C'; ws['F23'] = ': 20°C'; ws['F24'] = ': 26°C'
    ws['B25'] = 'Hol'; ws['F25'] = ': 18°C (kollektör bağlantı boruları ile ısıtılır)'
    ws['F26'] = None; ws['F27'] = None; ws['F28'] = None
    ws['F29'] = ':   0°C'; ws['F30'] = ':   6°C'; ws['F31'] = ': 20°C'; ws['B30'] = 'Döşeme altı (2. bodrum müştemilat)'
    ws['F35'] = H.U['DD']; ws['F36'] = H.U['DD25']; ws['F37'] = H.U['DD30']; ws['F38'] = H.U['DK']
    ws['F39'] = H.U['ÇP']; ws['F40'] = 0; ws['F41'] = H.U['İDM']; ws['F42'] = H.U['İDA']; ws['F43'] = H.U['Dö']
    ws['F44'] = H.U['Ta']; ws['F45'] = 0; ws['F46'] = 0; ws['F47'] = 0; ws['F48'] = H.U['İD']
    ws.print_area = 'A1:N65'
    # ---------------- ısı kaybı sayfaları (ZEMİN şablonu = 1. bodrum, 1 NK = zemin, kopya = 1. kat)
    tpl_wb = openpyxl.load_workbook(X.SRC)
    tpl = tpl_wb['ZEMİN']
    wsB = wb['ZEMİN']; wsB.title = 'BODRUM'
    wsZ = wb['1 NK']; wsZ.title = 'ZEMİN'
    ws1 = wb.copy_worksheet(wsZ); ws1.title = '1 NK'
    wb.move_sheet('1 NK', offset=-(len(wb.sheetnames) - 1 - wb.sheetnames.index('ZEMİN') - 1))
    tot = {}
    for (k, sh, kind, dn), wsx, no in zip(FL, (wsB, wsZ, ws1), (3, 4, 5)):
        rooms = []
        for R in ROOMS['a']:
            z = zone_of(k, 'a', R['name'])
            e, c = X.room_entries(R, kind, z)
            e = (e[0], '%s %s' % (dn[0], R['name']), *e[2:])
            rooms.append(e)
        tot[k] = X.write_heat_sheet(wsx, tpl, {'B1': '1. BODRUM', 'Z': 'ZEMİN', '1': '1. NORMAL'}[k], no, rooms, k)
    # ---------------- PETEK LİST (mahal / boru)
    ws = wb['PETEK LİST']
    X.clear_rows(ws, 10, 60, 16)
    tplr = [tpl_wb['PETEK LİST'].cell(10, c) for c in range(1, 17)]
    tpls = [tpl_wb['PETEK LİST'].cell(15, c) for c in range(1, 17)]
    r = 10
    PROW = {}
    for k, sh, kind, dn in FL:
        r0 = r
        for side in ('a',):
            circ, calc = HEAT[k][side]
            for R in ROOMS[side]:
                nm = R['name']
                z = zone_of(k, side, nm)
                cs = [c for c in circ if c['room'] == nm]
                if nm == 'HOL':
                    L_ = 0.0
                    for c in circ:
                        L_ += max(0.0, c['L'] - c['Ar'] / (c['s'] / 100.0)) * 0.5
                else:
                    L_ = sum(c['L'] for c in cs)
                vals = {'A': z, 'B': '%s %s' % (dn[0], nm), 'C': str(R['ti']),
                        'D': "='%s'!Q%d" % (sh, tot[k][z]), 'E': 17.5, 'F': "='YERDEN ISITMA'!N%d" % r, 'G': round(L_, 2),
                        'H': max(1, len(cs)), 'I': 'ZEMİNDEN ISITMA' + (' (BAĞLANTI BORULARI)' if nm == 'HOL' else '')}
                for cc in range(1, 17):
                    X.copy_style(tplr[cc - 1], ws.cell(r, cc))
                for col, v in vals.items():
                    ws[col + str(r)] = v
                ws.merge_cells('I%d:P%d' % (r, r))
                PROW[(k, side, nm)] = r
                r += 1
        for cc in range(1, 17):
            X.copy_style(tpls[cc - 1], ws.cell(r, cc))
        ws['E%d' % r] = 'TOPLAM ='; ws['F%d' % r] = '=SUM(F%d:F%d)' % (r0, r - 1); ws['G%d' % r] = 'watt'
        r += 1
    ws['C1'] = 'MAHAL VE YERDEN ISITMA BORU BOYU ÇİZELGESİ'; ws['A1'] = 'ROTAŞ'
    ws['N3'] = datetime.datetime(2026, 10, 11)
    ws.print_area = 'A1:P%d' % r
    # ---------------- YERDEN ISITMA
    ws = wb['YERDEN ISITMA']
    X.clear_rows(ws, 10, 60, 14)
    tplr = [tpl_wb['YERDEN ISITMA'].cell(10, c) for c in range(1, 15)]
    ws['A1'] = 'ROTAŞ'; ws['H6'] = 'BAYRAM GENÇ'
    for (k, side, nm), rr in PROW.items():
        circ = HEAT[k][side][0]
        ds = [d for d in circ if d['room'] == nm]
        R = [x for x in ROOMS[side] if x['name'] == nm][0]
        A = R['A']
        s = ds[0]['s'] if ds else 15
        vals = {'A': "='PETEK LİST'!A%d" % rr, 'B': "='PETEK LİST'!B%d" % rr, 'C': "='PETEK LİST'!C%d" % rr,
                'D': "='PETEK LİST'!D%d" % rr, 'E': A, 'F': '=D%d/E%d' % (rr, rr), 'G': '=76.263-0.539*F%d' % rr,
                'H': '=D%d/G%d' % (rr, rr), 'I': s, 'J': "='PETEK LİST'!G%d" % rr, 'K': '=J%d/80' % rr,
                'L': max(1, len(ds)), 'M': 17.5, 'N': '=J%d*M%d' % (rr, rr)}
        for cc in range(1, 15):
            X.copy_style(tplr[cc - 1], ws.cell(rr, cc))
        for col, v in vals.items():
            ws[col + str(rr)] = v
    ws.print_area = 'A1:N%d' % (max(PROW.values()) + 2)

    # ---------------- MMO (devre bazında)
    def mmo(ws, kats, title):
        X.clear_rows(ws, 7, 35, 60)
        tpl_col = [ws.cell(rr, 6) for rr in range(1, 48)]
        ws['A2'] = title
        allc = []
        for k in kats:
            for side in ('a',):
                allc += [(k, side, d) for d in X.hydraulics(HEAT[k][side][0])]
        ws['D3'] = 'Isıtma Çevrim Sayısı : %d' % len(allc)
        ws['D5'] = 'Mak. Müh. Bayram GENÇ'
        col = 6
        cols = []
        for k, side, d in allc:
            C = CL(col)
            v = {7: 'P%d' % d['port'], 8: 'Z' + d['zone'], 9: d['room'], 10: d['ti'], 11: 10 if k == 'B1' else 20,
                 12: round(d['Ar'], 2), 13: round(d['W'], 1), 14: '=%s13/%s12' % (C, C), 15: 0.012, 16: 1, 17: '=%s12' % C,
                 18: '=%s13/%s17' % (C, C), 19: '=%s10+(%s14/8.92)^0.91' % (C, C), 20: 45, 21: '=%s20-%s10' % (C, C),
                 22: d['s'], 23: 40, 24: '=%s23-%s10' % (C, C), 25: '=2*(%s21-%s24)' % (C, C),
                 26: '=0.2*%s14' % C, 27: '=%s17*(%s14+%s26)' % (C, C, C), 28: '=%s27/(1.163*%s25)' % (C, C),
                 29: '=%s17/(%s22*0.01)' % (C, C), 30: round(max(0.0, d['L'] - d['Ar'] / (d['s'] / 100.0)), 2),
                 31: '=%s29+%s30' % (C, C), 32: round(d['dP']), 33: '=%s32*0.05' % C, 34: '=%s32+%s33' % (C, C)}
            for rr, val in v.items():
                X.copy_style(tpl_col[rr - 1], ws.cell(rr, col))
                ws.cell(rr, col).value = val
            cols.append(C)
            col += 1
        for C in cols:
            X.copy_style(tpl_col[34], ws[C + '35'])
            ws[C + '35'] = '=MAX(%s34:%s34)-%s34' % (cols[0], cols[-1], C)
        ws['E2'] = 'TOPLAM ISI KAYBI = %.0f W' % sum(d['W'] for _, _, d in allc)
        ws['E3'] = 'MAX. BASINÇ KAYBI = %.0f Pa' % max(d['dP'] * 1.05 for _, _, d in allc)
        ws['C30'] = 'BAĞLANTI BORULARI'; ws['D30'] = 'Kat Planından (çizimden ölçülen)'
        ws['C31'] = 'TOPLAM BORU UZUNLUĞU'; ws['D31'] = 'Lç + Lb (çizimden ölçülen toplam)'
        ws['C28'] = 'SICAK SU DEBİSİ'; ws['D28'] = 'q/(1,163.ΔTs)'
        ws['C32'] = 'DÜZ BORU BASINÇ KAYBI (5)'; ws['D32'] = 'R.L (PEX 16x2,0, Blasius)'
        for rr in range(36, 47):
            for cc in range(8, 50):
                ws.cell(rr, cc).value = None
        ws['B41'] = 'Kombi gidiş suyu sıcaklığı 45 °C, dönüş 35 °C (ortalama 40 °C) seçilmiştir.'
        ws['B42'] = 'Ortalama su sıcaklığı 45/35 °C rejimine göre 40 °C alınmıştır.'
        ws['B43'] = 'Alta geçen ısı 0,2 q" olarak alınmıştır (1. bodrumun altı ısıtılmayan müştemilat 10 °C).'
        ws['B44'] = 'R (Pa/m): PEX 16x2,0 (iç çap 12 mm), Blasius bağıntısı ile hesaplanmıştır.'
        ws['B46'] = 'Isıtma devrelerinin basıncı kollektördeki debimetreli reglaj vanası ile ayarlanmalıdır.'
        ws.print_area = 'A1:%s47' % cols[-1]
        ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True
    mmo(wb['MMO YERDEN ISITMA'], ['B1'], '1. BODRUM (DAİRE 1)')
    mmo(wb['YERDEN ISITMA- DEVAMI'], ['Z', '1'], 'ZEMİN (DAİRE 2) + 1. KAT (DAİRE 3)')
    wb['YERDEN ISITMA- DEVAMI']['M5'] = None
    # ---------------- ek sayfalar
    X.hidrofor_sheet(wb, P, 3, D['YB_D'], -5.50, 5.20, D['SB_D'] + 2, -7.00, -0.60)
    X.yagmur_sheet(wb, P, round(D['ROOF_A'], 2), D['NYB'])
    X.kombi_sheet(wb, P, [('%s %s' % (fl[1], nm), HEAT[fl[0]][side][0]) for fl in FL for side, nm in zip(('a', 'b'), fl[3])])
    for nm in ('kapak', 'TEKNİK RAPOR (2)'):
        pass
    if 'TEKNİK RAPOR (2)' in wb.sheetnames:
        del wb['TEKNİK RAPOR (2)']
    print('kaldırılan logo/resim', X.logo_temizle(wb))
    wb.save(OUT)


if __name__ == '__main__':
    import os
    os.makedirs('/tmp/claude-0/p2/out', exist_ok=True)
    build()
    print('ok', OUT)
