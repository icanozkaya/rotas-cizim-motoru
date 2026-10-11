"""Kayıtları DXF (ezdxf) ve mkdwg giriş dosyasına yaz."""
import pickle, sys
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from design import LAYERS, LTYPES

out_dxf, out_txt = sys.argv[1], sys.argv[2]
_pk = pickle.load(open(sys.argv[3] if len(sys.argv) > 3 else '/tmp/claude-0/recs.pkl', 'rb'))
R, fr, H = _pk[:3]
BLKS = _pk[3] if len(_pk) > 3 and _pk[3] else []
# gerçek blok adayları: kayıtları kontrollerden sonra aynen duranlar INSERT olarak yazılır, gerisi patlatılmış kalır
import math as _m
_idx = {id(r): i for i, r in enumerate(R)}
SKIP, INS = set(), []
for b in BLKS:
    ids = [_idx.get(id(r)) for r in b['recs']]
    if not ids or None in ids or any(i in SKIP for i in ids):
        continue
    a, bb, c, d, e, f_ = b['m']
    sx, sy0 = _m.hypot(a, d), _m.hypot(bb, e)
    det = a * e - bb * d
    if sx < 1e-9 or abs(a * bb + d * e) > 1e-6 * sx * sy0:      # kayma varsa patlatılmış kalsın
        continue
    if det < 0 and any(r[0] == 'T' for r in b['recs']):           # aynalı + yazılı blok patlatılmış kalsın
        continue
    SKIP.update(ids)
    INS.append((b, sx, sy0 if det > 0 else -sy0, _m.degrees(_m.atan2(d, a)), (c, f_)))
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

import re as _re, mtyblk as _mb
def _bn(n):
    return _re.sub(r'[^A-Za-z0-9_\- ]', '_', SN(n))
def _lay(n):
    n = SN(n)
    if n != '0' and n not in doc.layers:
        doc.layers.add(n, color=LAYERS.get(n, (7,))[0] if n in LAYERS else 7)
    return n
_DEF = {}
def _blockdef(name):
    bn = _bn(name)
    if bn in _DEF:
        return bn
    blk = doc.blocks.new(bn)
    for p in _mb.load(name):
        k, lay = p[0], _lay(p[1])
        def ca(col):
            return {'layer': lay, **({'color': col} if col is not None else {})}
        if k == 'L':
            blk.add_line(p[2], p[3], dxfattribs=ca(p[4]))
        elif k == 'P':
            q = blk.add_lwpolyline(p[2], close=p[3], dxfattribs=ca(p[5]))
            if p[4]:
                q.dxf.const_width = p[4]
        elif k == 'C':
            blk.add_circle(p[2], p[3], dxfattribs=ca(p[4]))
        elif k == 'S':
            blk.add_solid([p[2], p[3], p[4]], dxfattribs=ca(p[5]))
        elif k == 'T':
            if not str(p[3]).strip():
                continue
            t = blk.add_text(str(p[3])[:240], height=p[4], rotation=p[5], dxfattribs={**ca(p[7]), 'style': 'ROTAS'})
            t.set_placement(p[2], align=TAE.get(p[6], TA.LEFT))
        elif k == 'A':
            t = blk.add_attdef(_bn(p[8]).replace(' ', '_'), p[2], text=str(p[3])[:240], height=p[4], rotation=p[5],
                               dxfattribs={**ca(p[7]), 'style': 'ROTAS'})
            t.set_placement(p[2], align=TAE.get(p[6], TA.LEFT))
    _DEF[bn] = blk
    return bn
# pafta sınırları: AutoCAD'de BPDF (toplu PDF) için çizilmeyen ROTAS_PAFTA blokları
NPAF = 0
if fr and isinstance(fr, list) and fr and isinstance(fr[0], tuple) and isinstance(fr[0][0], tuple):
    _pl = doc.layers.add('ROTAS-PAFTA-SINIRI', color=8)
    _pl.dxf.plot = 0
    _pb = doc.blocks.new('ROTAS_PAFTA')
    _pb.add_lwpolyline([(0, 0), (1, 0), (1, 1), (0, 1)], close=True, dxfattribs={'layer': '0'})
    for (x0, y0, x1, y1), *_ in fr:
        msp.add_blockref('ROTAS_PAFTA', (x0, y0), dxfattribs={'layer': 'ROTAS-PAFTA-SINIRI', 'xscale': x1 - x0,
                                                              'yscale': y1 - y0})
        NPAF += 1
NINS = 0
for b, sx, sy, rot, ins in INS:
    bn = _blockdef(b['name'])
    br = msp.add_blockref(bn, ins, dxfattribs={'layer': _lay(b['lay0']), 'xscale': sx, 'yscale': sy, 'rotation': rot})
    tags = {a.dxf.tag for a in _DEF[bn].attdefs()}
    if tags:
        vals = {t: '' for t in tags}
        for k_, v_ in b['attrs'].items():
            vals[_bn(k_).replace(' ', '_')] = v_[:240]
        br.add_auto_attribs(vals)
        for at in br.attribs:
            at.dxf.owner = br.dxf.handle          # ATTRIB sahibi INSERT olmalı (ACadSharp/AutoCAD bunu arar)
            if at.dxf.layer == '0':
                at.dxf.layer = br.dxf.layer
    NINS += 1


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
for ri, r in enumerate(R):
    k, lay = r[0], r[1]
    _ins = ri in SKIP
    col = r[NREC[k]] if len(r) > NREC[k] else None
    cs = ('\t%d' % col) if col is not None else ''
    ca = {'color': col} if col is not None else {}
    if k == 'L':
        a, b = r[2], r[3]
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1e-6:
            continue
        _ins or msp.add_line(a, b, dxfattribs={'layer': lay, **ca})
        f.write('L\t%s\t%.2f\t%.2f\t%.2f\t%.2f%s\n' % (lay, a[0], a[1], b[0], b[1], cs))
    elif k == 'P':
        pts, cl, w = r[2], r[3], r[4]
        p = None if _ins else msp.add_lwpolyline(pts, close=cl, dxfattribs={'layer': lay, **ca})
        if w and p is not None:
            p.dxf.const_width = w
        f.write('P\t%s\t%d\t%g\t%d\t' % (lay, 1 if cl else 0, w, len(pts)) + '\t'.join('%.2f\t%.2f' % q for q in pts) + cs + '\n')
    elif k == 'C':
        _ins or msp.add_circle(r[2], r[3], dxfattribs={'layer': lay, **ca})
        f.write('C\t%s\t%.2f\t%.2f\t%.3f%s\n' % (lay, r[2][0], r[2][1], r[3], cs))
    elif k == 'S':
        _ins or msp.add_solid([r[2], r[3], r[4]], dxfattribs={'layer': lay, **ca})
        f.write('S\t%s\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f%s\n' % (lay, r[2][0], r[2][1], r[3][0], r[3][1], r[4][0], r[4][1], cs))
    elif k == 'T':
        p, s, h, rot, al = r[2], r[3], r[4], r[5], r[6]
        s = s.strip()
        if not s or h <= 0:
            continue
        s = s[:240]
        if not _ins:
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
print('entities', n, 'blok INSERT', NINS, 'blok tanımı', len(_DEF), 'pafta sınırı', NPAF)
