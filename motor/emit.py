"""Kayıtları DXF (ezdxf) ve mkdwg (yedek) giriş dosyasına yaz.

Çizim sırası (AutoCAD'de alttan üste): çizgiler/borular -> yazı/etiket maskeleri (WIPEOUT) + çerçeveler -> MTY blokları (INSERT) -> yazılar.
MTY blokları HİÇBİR ZAMAN patlatılmaz: tanım kullanıcının kütüphane dosyasından birebir aktarılır, öznitelikler (ATTRIB) değerleriyle yazılır.
Katman ve blok adları orijinal (Türkçe karakterli) haliyle korunur.
"""
import math, pickle, sys, re
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from ezdxf.addons import Importer
from design import LAYERS, LTYPES
import mtyblk

out_dxf, out_txt = sys.argv[1], sys.argv[2]
_pk = pickle.load(open(sys.argv[3] if len(sys.argv) > 3 else '/tmp/claude-0/recs.pkl', 'rb'))
R, fr, H = _pk[:3]
BLKS = _pk[3] if len(_pk) > 3 and _pk[3] else []

AL = {'L': (0, 0), 'C': (1, 0), 'R': (2, 0), 'ML': (0, 2), 'MC': (1, 2), 'MR': (2, 2), 'TL': (0, 3), 'TC': (1, 3), 'TR': (2, 3),
      'BL': (0, 1), 'BC': (1, 1), 'BR': (2, 1)}
TAE = {'L': TA.LEFT, 'C': TA.CENTER, 'R': TA.RIGHT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER, 'MR': TA.MIDDLE_RIGHT,
       'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT, 'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER,
       'BR': TA.BOTTOM_RIGHT}
NREC = {'L': 4, 'P': 5, 'C': 4, 'S': 5, 'T': 7, 'W': 99}

# ------------------------------------------------------------------ blok grupları
_idx = {id(r): i for i, r in enumerate(R)}
SKIP, INS, NMISS = set(), [], 0
for b in BLKS:
    ids = [_idx.get(id(r)) for r in b['recs']]
    if any(i is None for i in ids):
        NMISS += 1                      # kontrol aşamasında değişmiş kayıt: blok yine INSERT yazılır
    ids = [i for i in ids if i is not None and i not in SKIP]
    a, bb, c, d, e, f_ = b['m']
    sx, sy0 = math.hypot(a, d), math.hypot(bb, e)
    det = a * e - bb * d
    SKIP.update(ids)
    INS.append((b, sx, sy0 if det > 0 else -sy0, math.degrees(math.atan2(d, a)), (c, f_)))

# ------------------------------------------------------------------ katmanlar
used = sorted(set(r[1] for r in R))
LAYERS = dict(LAYERS)
for n in used:
    if n not in LAYERS:
        u = n.upper()
        c = 6 if 'PIS' in u else 5 if 'SOGUK' in u else 1 if 'SICAK' in u else 101 if 'TEMIZSU' in u else 15 if 'TEFRIS' in u \
            else 5 if 'ROGAR' in u else 1 if 'VANA' in u else 43 if 'PVC' in u else 7
        LAYERS[n] = (c, 'CONTINUOUS')

doc = ezdxf.new('R2010', setup=False)
doc.header['$INSUNITS'] = 5
doc.header['$LTSCALE'] = 1.0
doc.header['$DWGCODEPAGE'] = 'ANSI_1254'
doc.styles.add('ROTAS', font='arial.ttf')
for n, (dd, g) in LTYPES.items():
    doc.linetypes.add(n, pattern=[dd + g, dd, -g], description=n)
for n, (c, lt) in LAYERS.items():
    if n in doc.layers:
        continue
    doc.layers.add(n, color=c, linetype=lt if (lt in doc.linetypes or lt.upper() == 'CONTINUOUS') else 'CONTINUOUS')
msp = doc.modelspace()


def _lay(n):
    if n != '0' and n not in doc.layers:
        doc.layers.add(n, color=7)
    return n


# ------------------------------------------------------------------ blok tanımları: kullanıcının kütüphane dosyasından birebir
_DEF = {}


def _safe(n):
    return re.sub(r'[<>/\\":;?*|=`]', '_', n)


def _blockdef(name):
    bn = _safe(name)
    if bn in _DEF:
        return bn
    src = ezdxf.readfile(mtyblk.find(name))
    ents = list(src.modelspace())
    imp = Importer(src, doc)
    one = ents[0] if len(ents) == 1 and ents[0].dxftype() == 'INSERT' else None
    if one is not None and one.dxf.name == name and one.dxf.insert.isclose((0, 0, 0), abs_tol=1e-6) \
            and abs(one.dxf.get('rotation', 0)) < 1e-9 and abs(one.dxf.get('xscale', 1) - 1) < 1e-9 \
            and abs(one.dxf.get('yscale', 1) - 1) < 1e-9 and name not in doc.blocks:
        imp.import_block(name)
        imp.finalize()
        _DEF[bn] = doc.blocks.get(name)
        return bn
    blk = doc.blocks.new(bn)
    imp.import_entities(ents, target_layout=blk)
    imp.finalize()
    _DEF[bn] = blk
    return bn


def _place(t, p, al):
    t.set_placement(p, align=TAE.get(al, TA.LEFT))


NINS = 0
NATR = 0


def write_inserts():
    global NINS, NATR
    for b, sx, sy, rot, ins in INS:
        bn = _blockdef(b['name'])
        br = msp.add_blockref(bn, ins, dxfattribs={'layer': _lay(b['lay0']), 'xscale': sx, 'yscale': sy, 'rotation': rot})
        defs = {a.dxf.tag: a for a in _DEF[bn].query('ATTDEF')}
        if defs:
            br.add_auto_attribs({t: '' for t in defs})
            byt = {a.dxf.tag: a for a in br.attribs}
            for tag, v in b['attrs'].items():
                val, off = v[0], v[1]
                at = byt.get(tag)
                if at is None:
                    continue
                at.dxf.text = val[:240]
                if len(v) > 2 and v[2]:
                    at.is_invisible = True
                rec = b['recs'][off] if off is not None and off < len(b['recs']) else None
                if rec is not None and rec[0] == 'T':           # konum, yükseklik, açı: çizimdeki yazı ile birebir
                    at.dxf.height = rec[4]
                    at.dxf.rotation = rec[5]
                    at.dxf.layer = _lay(rec[1])
                    if len(rec) > 7 and rec[7] is not None:
                        at.dxf.color = rec[7]
                    _place(at, rec[2], rec[6])
                NATR += 1
            for at in br.attribs:
                at.dxf.owner = br.dxf.handle          # ATTRIB sahibi INSERT (ACadSharp/AutoCAD bunu arar)
                if at.dxf.layer == '0':
                    at.dxf.layer = br.dxf.layer
        NINS += 1


# ------------------------------------------------------------------ pafta sınırları (AutoCAD BPDF toplu PDF için, çizilmez)
NPAF = 0
if fr and isinstance(fr, list) and isinstance(fr[0], tuple) and isinstance(fr[0][0], tuple):
    _pl = doc.layers.add('ROTAS-PAFTA-SINIRI', color=8)
    _pl.dxf.plot = 0
    _pb = doc.blocks.new('ROTAS_PAFTA')
    _pb.add_lwpolyline([(0, 0), (1, 0), (1, 1), (0, 1)], close=True, dxfattribs={'layer': '0'})
    for (x0, y0, x1, y1), *_ in fr:
        msp.add_blockref('ROTAS_PAFTA', (x0, y0), dxfattribs={'layer': 'ROTAS-PAFTA-SINIRI', 'xscale': x1 - x0,
                                                              'yscale': y1 - y0})
        NPAF += 1

# ------------------------------------------------------------------ mkdwg yedek dosyası (patlatılmış, ASCII)
TRM = str.maketrans('ÇĞİÖŞÜçğıöşü', 'CGIOSUcgiosu')


def esc(s):
    return ''.join(c if ord(c) < 128 else '\\U+%04X' % ord(c) for c in s).replace('\t', ' ')


f = open(out_txt, 'w', encoding='ascii')
f.write('H\t5\t1.0\n')
for n, (dd, g) in LTYPES.items():
    f.write('K\t%s\t%g\t%g\n' % (n, dd, g))
for n, (c, lt) in LAYERS.items():
    if n != '0':
        f.write('Y\t%s\t%d\t%s\n' % (n.translate(TRM), c, lt))


def ca_(r, k):
    col = r[NREC[k]] if len(r) > NREC[k] else None
    return col, ({'color': col} if col is not None else {})


n = 0
# 1) çizgiler / borular / semboller
for ri, r in enumerate(R):
    k, lay = r[0], r[1]
    if k in ('T', 'W'):
        continue
    col, ca = ca_(r, k)
    cs = ('\t%d' % col) if col is not None else ''
    sl = lay.translate(TRM)
    skip = ri in SKIP
    if k == 'L':
        a, b = r[2], r[3]
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1e-6:
            continue
        if not skip:
            msp.add_line(a, b, dxfattribs={'layer': lay, **ca})
        f.write('L\t%s\t%.2f\t%.2f\t%.2f\t%.2f%s\n' % (sl, a[0], a[1], b[0], b[1], cs))
    elif k == 'P':
        pts, cl, w = r[2], r[3], r[4]
        if not skip:
            p = msp.add_lwpolyline(pts, close=cl, dxfattribs={'layer': lay, **ca})
            if w:
                p.dxf.const_width = w
        f.write('P\t%s\t%d\t%g\t%d\t' % (sl, 1 if cl else 0, w, len(pts)) + '\t'.join('%.2f\t%.2f' % q for q in pts) + cs + '\n')
    elif k == 'C':
        if not skip:
            msp.add_circle(r[2], r[3], dxfattribs={'layer': lay, **ca})
        f.write('C\t%s\t%.2f\t%.2f\t%.3f%s\n' % (sl, r[2][0], r[2][1], r[3], cs))
    elif k == 'S':
        if not skip:
            msp.add_solid([r[2], r[3], r[4]], dxfattribs={'layer': lay, **ca})
        f.write('S\t%s\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f%s\n' % (sl, r[2][0], r[2][1], r[3][0], r[3][1], r[4][0], r[4][1], cs))
    n += 1
# 2) yazı / etiket maskeleri + çerçeveler (blokların ve yazıların altında, boruların üstünde)
NW = 0
doc.set_wipeout_variables(frame=0)
for r in R:
    if r[0] != 'W':
        continue
    pts = r[2]
    msp.add_wipeout(pts, dxfattribs={'layer': _lay(r[1])})
    if r[3]:
        msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': r[1]})
        f.write('P\t%s\t1\t0\t%d\t' % (r[1].translate(TRM), len(pts)) + '\t'.join('%.2f\t%.2f' % q for q in pts) + '\n')
    NW += 1
# 3) MTY blokları
write_inserts()
# 4) yazılar (en üstte)
for ri, r in enumerate(R):
    if r[0] != 'T':
        continue
    lay = r[1]
    col, ca = ca_(r, 'T')
    cs = ('\t%d' % col) if col is not None else ''
    p, s, h, rot, al = r[2], r[3], r[4], r[5], r[6]
    s = s.strip()
    if not s or h <= 0:
        continue
    s = s[:240]
    if ri not in SKIP:
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
        f.write('T\t%s\t%.3f\t%.3f\t%d\t%d\t%.2f\t%.2f\t%.2f\t%.2f\t%s\t1.0%s\n' % (lay.translate(TRM), h, rot, ha, va, p[0], y,
                                                                                   p[0], y, esc(q), cs))
    n += 1
f.close()
doc.saveas(out_dxf)
print('entities', n, 'blok INSERT', NINS, 'dolu öznitelik', NATR, 'blok tanımı', len(_DEF), 'değişmiş blok', NMISS,
      'maske', NW, 'pafta sınırı', NPAF)
