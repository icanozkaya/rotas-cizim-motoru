# -*- coding: utf-8 -*-
"""Hesap tablolarını AutoCAD'e yapıştırılabilir DXF tablo olarak çizer (MTY-HESAP katmanı, cm)."""
import ezdxf, openpyxl
from ezdxf.enums import TextEntityAlignment as TA
wb = openpyxl.load_workbook('/tmp/claude-0/hs/out/rc/HESAPLAR_SIHHI.xlsx', data_only=True)
doc = ezdxf.new('R2018', setup=True); doc.header['$INSUNITS'] = 5
msp = doc.modelspace()
doc.layers.add('MTY-HESAP', color=1); doc.layers.add('MTY-HESAP-YAZI', color=7)
if 'ROTAS' not in doc.styles: doc.styles.add('ROTAS', font='arial.ttf')
X0, Y0 = 302254.0, -486523.0          # HESAPLAR çizimindeki ilk hesap çerçevesinin sol üst köşesi
H = 6.0; RH = 14.0

def fmt(v):
    if isinstance(v, float):
        s = f'{v:.3f}'.rstrip('0').rstrip('.')
        return s.replace('.', ',')
    return '' if v is None else str(v)

def T(x, y, s, h=H, al=TA.MIDDLE_LEFT, lay='MTY-HESAP-YAZI'):
    t = msp.add_text(s, height=h, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.85}); t.set_placement((x, y), align=al)

def table(x, y, ws, r0, r1, cols, widths, head_rows=1, title=None):
    if title:
        T(x, y + 10, title, 8.0); 
    yy = y
    for r in range(r0, r1 + 1):
        vals = [ws.cell(r, c).value for c in cols]
        if all(v is None for v in vals): continue
        xx = x
        for c, w, v in zip(cols, widths, vals):
            msp.add_lwpolyline([(xx, yy), (xx + w, yy), (xx + w, yy - RH), (xx, yy - RH)], close=True, dxfattribs={'layer': 'MTY-HESAP'})
            s = fmt(v)
            if s:
                hh = H if len(s) * H * 0.5 < w - 2 else max(3.0, (w - 3) / (len(s) * 0.5))
                left = isinstance(v, str) and w > 60
                T(xx + (2 if left else w / 2), yy - RH / 2, s, hh, TA.MIDDLE_LEFT if left else TA.MIDDLE_CENTER)
            xx += w
        yy -= RH
    return yy

def lines(x, y, ws, rows, h=H):
    for r in rows:
        v = ws.cell(r, 1).value
        if v: T(x, y, str(v), h); y -= h * 1.8
    return y

# 1) temiz su kritik devre
ws = wb['TEMİZ SU KRİTİK DEVRE']
y = Y0
T(X0, y, ws['A1'].value, 9.0); y -= 18
y = lines(X0, y, ws, range(2, 9))
y -= 6
y = table(X0, y, ws, 10, 21, range(1, 9), [36, 190, 40, 28, 36, 80, 80, 36])
y -= 8
y = lines(X0, y, ws, range(23, 31))
# 2) bloklar
y -= 30
for B in ('B1', 'B2', 'B3'):
    ws = wb[f'{B} BLOK']
    T(X0, y, ws['B1'].value, 9.0); y -= 20
    ya = table(X0, y, ws, 3, 10, range(2, 8), [110, 36, 30, 34, 44, 70])
    table(X0 + 360, y, ws, 3, 9, range(8, 10), [60, 40])
    T(X0, ya - 8, f"{ws['B11'].value} {fmt(ws['F11'].value)} l/s", H); y = ya - 30
    ncol = 2 + ws.max_column
    last = max(c for c in range(4, ws.max_column + 1) if ws.cell(15, c).value is not None)
    T(X0, y, ws['B14'].value, 7.0); y -= 12
    y = table(X0, y, ws, 15, 23, range(2, last + 1), [110, 40] + [36] * (last - 3)) - 14
    r2 = [r for r in range(24, 40) if ws.cell(r, 2).value and 'YÜKLERİ' in str(ws.cell(r, 2).value)][0]
    T(X0, y, ws.cell(r2, 2).value, 7.0); y -= 12
    y = table(X0, y, ws, r2 + 1, r2 + 11, range(2, last + 1), [110, 40] + [36] * (last - 3)) - 40
doc.saveas('/tmp/claude-0/hs/out/HESAPLAR_SIHHI.dxf')
print('ok', y)
