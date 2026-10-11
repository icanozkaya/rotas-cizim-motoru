"""Kayıtları DXF (ezdxf) ve mkdwg giriş dosyasına yaz."""
import pickle, sys
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from design import LAYERS, LTYPES

out_dxf, out_txt = sys.argv[1], sys.argv[2]
R, fr, H = pickle.load(open(sys.argv[3] if len(sys.argv) > 3 else '/tmp/claude-0/recs.pkl', 'rb'))
TRM = str.maketrans('ÇĞİÖŞÜçğıöşü', 'CGIOSUcgiosu')
def SN(n):
    return n.translate(TRM)
# blok katman renkleri
import glob as _g
BLAY = {}
for f in _g.glob('/tmp/claude-0/blk/SIHHI*.dxf'):
    try:
        with open(f, 'rb') as fh:
            pass
    except Exception:
        pass
used = sorted(set(r[1] for r in R))
LAYERS = dict(LAYERS)
for n in used:
    if n not in LAYERS:
        c = 7
        u = n.upper()
        if 'PIS' in u: c = 6
        elif 'SOGUK' in u: c = 5
        elif 'SICAK' in u: c = 1
        elif 'TEMIZSU' in u: c = 101
        elif 'YUK' in u: c = 7
        elif 'TEFRIS' in u: c = 15
        elif 'ROGAR' in u: c = 5
        elif 'VANA' in u: c = 1
        elif 'PVC' in u: c = 43
        LAYERS[n] = (c, 'CONTINUOUS')
R = [(r[0], SN(r[1])) + tuple(r[2:]) for r in R]
LAYERS = {SN(k): v for k, v in LAYERS.items()}

AL = {'L': (0, 0), 'C': (1, 0), 'R': (2, 0), 'ML': (0, 2), 'MC': (1, 2), 'MR': (2, 2), 'TL': (0, 3), 'TC': (1, 3), 'TR': (2, 3), 'BL': (0, 1), 'BC': (1, 1), 'BR': (2, 1)}
TAE = {'L': TA.LEFT, 'C': TA.CENTER, 'R': TA.RIGHT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER,
       'MR': TA.MIDDLE_RIGHT, 'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT,
       'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER, 'BR': TA.BOTTOM_RIGHT}

doc = ezdxf.new('R2010', setup=False)
doc.header['$INSUNITS'] = 5
doc.header['$LTSCALE'] = 1.0
doc.header['$DWGCODEPAGE'] = 'ANSI_1254'
doc.styles.add('ROTAS', font='arial.ttf')
for n, (d, g) in LTYPES.items():
    doc.linetypes.add(n, pattern=[d + g, d, -g], description=n)
for n, (c, lt) in LAYERS.items():
    if n in doc.layers:
        continue
    doc.layers.add(n, color=c, linetype=lt)
msp = doc.modelspace()


def esc(s):
    return ''.join(c if ord(c) < 128 else '\\U+%04X' % ord(c) for c in s).replace('\t', ' ')


f = open(out_txt, 'w', encoding='ascii')
f.write('H\t5\t1.0\n')
for n, (d, g) in LTYPES.items():
    f.write('K\t%s\t%g\t%g\n' % (n, d, g))
for n, (c, lt) in LAYERS.items():
    if n == '0':
        continue
    f.write('Y\t%s\t%d\t%s\n' % (n, c, lt))
n = 0
NREC = {'L': 4, 'P': 5, 'C': 4, 'S': 5, 'T': 7}
for r in R:
    k, lay = r[0], r[1]
    col = r[NREC[k]] if len(r) > NREC[k] else None
    cs = ('\t%d' % col) if col is not None else ''
    ca = {'color': col} if col is not None else {}
    if k == 'L':
        a, b = r[2], r[3]
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1e-6:
            continue
        msp.add_line(a, b, dxfattribs={'layer': lay, **ca})
        f.write('L\t%s\t%.2f\t%.2f\t%.2f\t%.2f%s\n' % (lay, a[0], a[1], b[0], b[1], cs))
    elif k == 'P':
        pts, cl, w = r[2], r[3], r[4]
        p = msp.add_lwpolyline(pts, close=cl, dxfattribs={'layer': lay, **ca})
        if w:
            p.dxf.const_width = w
        f.write('P\t%s\t%d\t%g\t%d\t' % (lay, 1 if cl else 0, w, len(pts)) + '\t'.join('%.2f\t%.2f' % q for q in pts) + cs + '\n')
    elif k == 'C':
        msp.add_circle(r[2], r[3], dxfattribs={'layer': lay, **ca})
        f.write('C\t%s\t%.2f\t%.2f\t%.3f%s\n' % (lay, r[2][0], r[2][1], r[3], cs))
    elif k == 'S':
        msp.add_solid([r[2], r[3], r[4]], dxfattribs={'layer': lay, **ca})
        f.write('S\t%s\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f%s\n' % (lay, r[2][0], r[2][1], r[3][0], r[3][1], r[4][0], r[4][1], cs))
    elif k == 'T':
        p, s, h, rot, al = r[2], r[3], r[4], r[5], r[6]
        s = s.strip()
        if not s or h <= 0:
            continue
        s = s[:240]
        t = msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS', **ca})
        t.set_placement(p, align=TAE[al])
        ha, va = AL[al]
        parts = [s]
        while any(len(esc(q)) > 245 for q in parts):
            q = parts.pop()
            i = q.rfind(' ', 0, len(q) // 2 + 10)
            i = i if i > 0 else len(q) // 2
            parts += [q[:i], q[i:].strip()]
        for j, q in enumerate(parts):
            y = p[1] - j * h * 1.6
            f.write('T\t%s\t%.3f\t%.3f\t%d\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%s\t1.0%s\n' % (lay, h, rot, ha, va, p[0], y, p[0], y, esc(q), cs))
    n += 1
f.close()
doc.saveas(out_dxf)
print('entities', n)
