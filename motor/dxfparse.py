"""Toleranslı DXF okuyucu: BLOCKS + ENTITIES, INSERT açma, tutamaçlardan bağımsız."""
import math, pickle, sys


ENC = 'cp1254'

def pairs(path):
    with open(path, encoding=ENC, errors='replace') as f:
        while True:
            c = f.readline()
            if not c:
                return
            cs = c.strip()
            if not cs.lstrip('-').isdigit():
                continue  # yeniden hizala (çok satırlı değer)
            v = f.readline()
            yield cs, v.rstrip('\r\n')


def read(path):
    blocks = {}
    ents = []
    sec = None
    cur = None          # current entity dict
    curblk = None       # name of block being read
    target = None
    expect_secname = False
    for c, v in pairs(path):
        if c == '0':
            # close current entity
            if cur is not None:
                target.append(cur)
                cur = None
            if v == 'SECTION':
                expect_secname = True
                continue
            if v == 'ENDSEC':
                sec = None
                continue
            if sec == 'BLOCKS':
                if v == 'BLOCK':
                    cur = {'_t': 'BLOCK'}
                    target = []
                    curblk = cur
                    continue
                if v == 'ENDBLK':
                    if curblk is not None:
                        blocks[curblk.get('name', '?')] = (curblk.get('base', (0, 0)), [e for e in target if e['_t'] != 'BLOCK'])
                    curblk = None
                    target = []
                    continue
                cur = {'_t': v}
                continue
            if sec == 'ENTITIES':
                target = ents
                cur = {'_t': v}
                continue
            continue
        if expect_secname and c == '2':
            sec = v
            expect_secname = False
            if sec == 'ENTITIES':
                target = ents
            continue
        if cur is None:
            continue
        t = cur['_t']
        if c == '8':
            cur['layer'] = v
        elif c == '62':
            try: cur['color'] = int(v)
            except ValueError: pass
        elif t == 'BLOCK':
            if c == '2': cur['name'] = v
            elif c == '10': cur['bx'] = float(v)
            elif c == '20': cur['base'] = (cur.get('bx', 0.0), float(v))
        elif t == 'LINE':
            if c in ('10', '20', '11', '21'): cur[c] = float(v)
        elif t in ('LWPOLYLINE',):
            if c == '10': cur.setdefault('pts', []).append([float(v), 0.0])
            elif c == '20': cur['pts'][-1][1] = float(v)
            elif c == '70': cur['flag'] = int(v)
            elif c == '43': cur['w'] = float(v)
        elif t == 'POLYLINE':
            if c == '70': cur['flag'] = int(v)
        elif t == 'VERTEX':
            if c in ('10', '20'): cur[c] = float(v)
        elif t in ('CIRCLE', 'ARC'):
            if c in ('10', '20', '40', '50', '51'): cur[c] = float(v)
        elif t in ('TEXT', 'ATTRIB', 'MTEXT', 'ATTDEF'):
            if c in ('10', '20', '11', '21', '40', '50'): cur[c] = float(v)
            elif c == '1': cur['text'] = v
            elif c == '3': cur['text'] = cur.get('text3', '') + v; cur['text3'] = cur['text']
            elif c == '72': cur['ha'] = int(v)
            elif c == '73' and t != 'MTEXT': cur['va'] = int(v)
            elif c == '71' and t == 'MTEXT': cur['att'] = int(v)
            elif c == '2' and t in ('ATTRIB', 'ATTDEF'): cur['tag'] = v
        elif t == 'INSERT':
            if c == '2': cur['name'] = v
            elif c in ('10', '20', '41', '42', '50'): cur[c] = float(v)
        elif t == 'HATCH':
            pass
    if cur is not None and target is not None:
        target.append(cur)
    # glue POLYLINE + VERTEX
    def glue(lst):
        out = []; poly = None
        for e in lst:
            if e['_t'] == 'POLYLINE':
                poly = e; e['pts'] = []; out.append(e)
            elif e['_t'] == 'VERTEX' and poly is not None:
                poly['pts'].append([e.get('10', 0), e.get('20', 0)])
            elif e['_t'] == 'SEQEND':
                poly = None
            else:
                out.append(e)
        return out
    ents = glue(ents)
    blocks = {k: (b, glue(v)) for k, (b, v) in blocks.items()}
    return blocks, ents


def xf(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + b * y + c, d * x + e * y + f)


def mul(m1, m2):
    a, b, c, d, e, f = m1
    A, B, C, D, E, F = m2
    return (a * A + b * D, a * B + b * E, a * C + b * F + c, d * A + e * D, d * B + e * E, d * C + e * F + f)


def flatten(blocks, ents, depth=0, m=(1, 0, 0, 0, 1, 0), out=None, layer_over=None, path=''):
    """yields (kind, layer, data, blockpath)"""
    if out is None: out = []
    for e in ents:
        t = e['_t']; lay = e.get('layer', '0')
        if lay == '0' and layer_over: lay = layer_over
        if t == 'LINE':
            out.append(('L', lay, (xf(m, e.get('10', 0), e.get('20', 0)), xf(m, e.get('11', 0), e.get('21', 0))), path))
        elif t in ('LWPOLYLINE', 'POLYLINE'):
            pts = [xf(m, *p) for p in e.get('pts', [])]
            if (e.get('flag', 0) & 1) and pts: pts = pts + [pts[0]]
            if len(pts) > 1: out.append(('P', lay, pts, path))
        elif t == 'CIRCLE':
            cx, cy = xf(m, e.get('10', 0), e.get('20', 0)); s = math.hypot(m[0], m[3])
            out.append(('C', lay, (cx, cy, e.get('40', 0) * s), path))
        elif t == 'ARC':
            r = e.get('40', 0); a0 = math.radians(e.get('50', 0)); a1 = math.radians(e.get('51', 0))
            if a1 < a0: a1 += 2 * math.pi
            n = max(4, int((a1 - a0) / 0.2))
            pts = [xf(m, e.get('10', 0) + r * math.cos(a0 + (a1 - a0) * i / n), e.get('20', 0) + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
            out.append(('P', lay, pts, path))
        elif t in ('TEXT', 'MTEXT', 'ATTRIB'):
            if t == 'TEXT' and (e.get('ha', 0) or e.get('va', 0)) and '11' in e:
                x, y = e['11'], e.get('21', 0)
            else:
                x, y = e.get('10', 0), e.get('20', 0)
            s = math.hypot(m[0], m[3])
            out.append(('T', lay, (xf(m, x, y), e.get('text', ''), e.get('40', 0) * s), path))
        elif t == 'INSERT' and depth < 6:
            nm = e.get('name')
            if nm not in blocks: continue
            base, sub = blocks[nm]
            sx, sy = e.get('41', 1.0), e.get('42', e.get('41', 1.0))
            r = math.radians(e.get('50', 0))
            cr, sr = math.cos(r), math.sin(r)
            local = (cr * sx, -sr * sy, e.get('10', 0), sr * sx, cr * sy, e.get('20', 0))
            local = mul(local, (1, 0, -base[0], 0, 1, -base[1]))
            flatten(blocks, sub, depth + 1, mul(m, local), out, lay, path + '/' + nm)
    return out


if __name__ == '__main__':
    blocks, ents = read(sys.argv[1])
    print('blocks', len(blocks), 'ents', len(ents))
    pickle.dump((blocks, ents), open(sys.argv[2], 'wb'), protocol=5)
