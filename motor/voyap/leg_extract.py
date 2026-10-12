"""Aselsan 02-Yangın 'YANGIN SÖNDÜRME TESİSATI SEMBOLLERİ' lejantından sembolleri blok geometrisi olarak çıkar."""
import pickle, re, math, sys
F = pickle.load(open('/tmp/claude-0/as/y02.pkl', 'rb'))
LX0, LX1, Y0, Y1 = 534600, 534975, 52150, 55400
labels = sorted([(r[2][0][1], str(r[2][1]).strip()) for r in F if r[0] == 'T' and 534960 < r[2][0][0] < 535100 and Y0 < r[2][0][1] < Y1], key=lambda t: -t[0])
# satır sınırları: lejant tablosunun yatay çizgileri
hl = sorted(set(round(min(r[2][0][1], r[2][1][1])) for r in F if r[0] == 'L' and abs(r[2][0][1] - r[2][1][1]) < 0.5
                and abs(r[2][0][0] - r[2][1][0]) > 1000 and 534500 < min(r[2][0][0], r[2][1][0]) < 534700 and Y0 - 200 < r[2][0][1] < Y1 + 100))
print('çizgiler', hl)
def bandof(y):
    lo = max([h for h in hl if h < y], default=None); hi = min([h for h in hl if h > y], default=None)
    return lo, hi
SYM = {}
for y, lab in labels:
    lo, hi = bandof(y)
    if lo is None or hi is None: continue
    recs = []
    for r in F:
        if r[0] in 'LP':
            pts = r[2] if r[0] == 'P' else r[2][:2]
            if all(LX0 < p[0] < LX1 and lo + 1 < p[1] < hi - 1 for p in pts): recs.append(r)
        elif r[0] == 'C':
            if LX0 < r[2][0] < LX1 and lo + 1 < r[2][1] < hi - 1: recs.append(r)
        elif r[0] == 'T':
            if LX0 < r[2][0][0] < LX1 and lo + 1 < r[2][0][1] < hi - 1: recs.append(r)
    if not recs: continue
    xs = []; ys = []
    for r in recs:
        if r[0] in 'LP':
            for p in (r[2] if r[0] == 'P' else r[2][:2]): xs.append(p[0]); ys.append(p[1])
        elif r[0] == 'C': xs += [r[2][0] - r[2][2], r[2][0] + r[2][2]]; ys += [r[2][1] - r[2][2], r[2][1] + r[2][2]]
        else: xs.append(r[2][0][0]); ys.append(r[2][0][1])
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    prim = []
    for r in recs:
        if r[0] == 'L': prim.append(('L', [(p[0] - cx, p[1] - cy) for p in r[2][:2]]))
        elif r[0] == 'P': prim.append(('P', [(p[0] - cx, p[1] - cy) for p in r[2]]))
        elif r[0] == 'C': prim.append(('C', (r[2][0] - cx, r[2][1] - cy, r[2][2])))
        else: prim.append(('T', (r[2][0][0] - cx, r[2][0][1] - cy), r[2][1], r[2][2]))
    key = lab
    if key in SYM: key += ' (2)'
    SYM[key] = dict(prim=prim, w=max(xs) - min(xs), h=max(ys) - min(ys))
    print(f'{lab[:45]:45s} {len(prim):4d} w={max(xs)-min(xs):.1f} h={max(ys)-min(ys):.1f}')
# yangın dolabı plan bloğu (SPRYD01) ve kolon şeması bloğu: ilk örnekten
def first_instance(name):
    g = []; started = False
    for r in F:
        if r[3].startswith('/' + name):
            g.append(r); started = True
        elif started: break
    return g
for name, key in (('SPRYD01', 'YANGIN DOLABI (KAT PLANI)'), ('0-MEK-YANGIN-YANGIN DOLABI-KOLON', 'YANGIN DOLABI (KOLON ŞEMASI)'), ('SPR-RISERNO', 'SPR KOLON NO')):
    g = first_instance(name)
    xs = []; ys = []
    for r in g:
        if r[0] in 'LP':
            for p in (r[2] if r[0] == 'P' else r[2][:2]): xs.append(p[0]); ys.append(p[1])
        elif r[0] == 'C': xs += [r[2][0]]; ys += [r[2][1]]
        elif r[0] == 'T': xs.append(r[2][0][0]); ys.append(r[2][0][1])
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    prim = []
    for r in g:
        if r[0] == 'L': prim.append(('L', [(p[0] - cx, p[1] - cy) for p in r[2][:2]]))
        elif r[0] == 'P': prim.append(('P', [(p[0] - cx, p[1] - cy) for p in r[2]]))
        elif r[0] == 'C': prim.append(('C', (r[2][0] - cx, r[2][1] - cy, r[2][2])))
        else: prim.append(('T', (r[2][0][0] - cx, r[2][0][1] - cy), r[2][1], r[2][2]))
    SYM[key] = dict(prim=prim, w=max(xs) - min(xs), h=max(ys) - min(ys))
    print(key, len(prim), round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1))
pickle.dump(SYM, open('asel_sym.pkl', 'wb'))
