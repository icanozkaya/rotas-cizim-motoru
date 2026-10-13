# -*- coding: utf-8 -*-
"""Kullanıcının MTY dinamik blok örnekleri (LibreDWG dxf çıktısında INSERT adı '*U' olarak kesilmiş; ezdxf bunları atıyor):
çap/MB etiketleri (MTY-TEMIZ SU CAP MB, MTY-PIS SU CAP SB), MTY tefrişleri (LAVABO1, EVIYE1, KLOZET1, DUS TEKNESI1, SUZGEC1),
rögar vb. Ham DXF'ten INSERT + ATTRIB okunur; öznitelik etiket kümesi ve konumları ile gerçek blok bulunup yeniden INSERT edilir,
eşleşmeyenlerde yalnızca ATTRIB metinleri TEXT olarak yazılır."""
import math, os, pickle
import ezdxf.math as em

_C = '/tmp/claude-0/vy/ulabels.pkl'


def oku(path='/tmp/claude-0/vy/sih.dxf'):
    if os.path.exists(_C) and os.path.getmtime(_C) > os.path.getmtime(path):
        return pickle.load(open(_C, 'rb'))
    raw = open(path, 'rb').read().split(b'\n')
    lines = []
    for b in raw:
        try: lines.append(b.decode('utf-8'))
        except UnicodeDecodeError: lines.append(b.decode('cp1254', errors='replace'))
    out = []; cur = None; att = None; mode = None; sec = None
    i, n = 0, len(lines)
    while i < n - 1:
        c = lines[i].strip(); v = lines[i + 1].strip()
        if c == '0':
            if v == 'SECTION': sec = lines[i + 3].strip()
            if sec == 'ENTITIES':
                if v == 'INSERT':
                    if cur: out.append(cur)
                    cur = dict(name=None, p=[0.0, 0.0], rot=0.0, sc=1.0, scy=None, lay='0', att=[]); att = None; mode = 'I'
                elif v == 'ATTRIB' and cur:
                    att = dict(tag='', txt='', p=[0.0, 0.0], p2=None, h=2.5, rot=0.0, lay='0', al=0, va=0, sty=None); cur['att'].append(att); mode = 'A'
                elif v == 'SEQEND':
                    if cur: out.append(cur)
                    cur = None; mode = None
                elif cur:
                    if mode == 'A': mode = None
                    else:
                        out.append(cur); cur = None; mode = None
        elif cur and mode in ('I', 'A'):
            t = att if mode == 'A' else cur
            if c == '2': t['name' if mode == 'I' else 'tag'] = v
            elif c == '1' and mode == 'A': t['txt'] = v
            elif c == '7' and mode == 'A': t['sty'] = v
            elif c == '8': t['lay'] = v
            elif c == '10': t['p'][0] = float(v)
            elif c == '20': t['p'][1] = float(v)
            elif c == '11' and mode == 'A': t['p2'] = [float(v), 0.0]
            elif c == '21' and mode == 'A' and t['p2'] is not None: t['p2'][1] = float(v)
            elif c == '40' and mode == 'A': t['h'] = float(v)
            elif c == '41' and mode == 'I': t['sc'] = float(v)
            elif c == '42' and mode == 'I': t['scy'] = float(v)
            elif c == '50': t['rot'] = float(v)
            elif c == '72' and mode == 'A': t['al'] = int(v)
            elif c == '74' and mode == 'A': t['va'] = int(v)
        i += 2
    if cur: out.append(cur)
    U = [o for o in out if o['name'] == '*U' and o['att']]
    pickle.dump(U, open(_C, 'wb'))
    return U


def _tx(u, p):
    a = math.radians(u['rot']); sx = u['sc']; sy = u['scy'] if u.get('scy') is not None else sx
    x, y = p[0] * sx, p[1] * sy
    return (u['p'][0] + x * math.cos(a) - y * math.sin(a), u['p'][1] + x * math.sin(a) + y * math.cos(a))


def _n(t):
    return t.replace('_001', '').upper()


def eslestir(sdoc):
    """öznitelik etiket kümesi (normalize: _001 soneki atılır) -> aday bloklar (isimli; *U hariç)"""
    cand = {}
    for b in sdoc.blocks:
        if b.name.startswith('*'): continue
        tags = tuple(sorted(_n(e.dxf.tag) for e in b if e.dxftype() == 'ATTDEF'))
        if tags: cand.setdefault(tags, []).append(b.name)
    return cand


def yaz(sdoc, doc, msp, U, kabul, tol=150.0, onek=''):
    """kabul(u) -> True ise yazılır. Dönüş: (blok olarak, metin olarak) adetleri"""
    from ezdxf.addons import Importer
    cand = eslestir(sdoc)
    need = set()
    plan = []
    for u in U:
        if not kabul(u): continue
        tags = tuple(sorted(_n(a['tag']) for a in u['att']))
        best = None
        for nm in cand.get(tags, []):
            b = sdoc.blocks.get(nm)
            pos = {_n(e.dxf.tag): (e.dxf.insert.x, e.dxf.insert.y) for e in b if e.dxftype() == 'ATTDEF'}
            d = max(min(math.dist(_tx(u, pos[_n(a['tag'])]), tuple(a['p'])), math.dist(_tx(u, pos[_n(a['tag'])]), tuple(a['p2'] or a['p']))) for a in u['att'])
            ps = next((a['txt'].strip() for a in u['att'] if a['tag'] == 'PS'), '')
            if nm.startswith('EVIYE') and not ps.startswith('4'): d += 1000           # lavabo / eviye aynı etiket kümesi: SB değeri ayırır
            if nm.startswith('LAVABO') and ps.startswith('4'): d += 1000
            if nm.startswith('DUS') and not ps.startswith('7'): d += 1000
            if best is None or d < best[0]: best = (d, nm)
        if best and best[0] <= tol:
            plan.append((u, best[1])); need.add(best[1])
        else:
            plan.append((u, None))
    need = [n for n in need if n not in doc.blocks]
    if need:
        im = Importer(sdoc, doc); im.import_blocks(need); im.finalize()
    nb = nt = 0
    for u, nm in plan:
        if nm:
            ins = msp.add_blockref(nm, (u['p'][0], u['p'][1]), dxfattribs={'layer': onek + u['lay'], 'rotation': u['rot'], 'xscale': u['sc'], 'yscale': (u['scy'] if u.get('scy') is not None else u['sc'])})
            tmap = {_n(e.dxf.tag): e.dxf.tag for e in doc.blocks.get(nm) if e.dxftype() == 'ATTDEF'}
            for a in u['att']:
                at = ins.add_attrib(tmap.get(_n(a['tag']), a['tag']), a['txt'], (a['p'][0], a['p'][1]))
                at.dxf.height = a['h']; at.dxf.rotation = a['rot']; at.dxf.layer = onek + a['lay']
                at.dxf.halign = a['al']; at.dxf.valign = a['va']
                if a['p2'] is not None: at.dxf.align_point = (a['p2'][0], a['p2'][1])
                if a['sty'] and a['sty'] in doc.styles: at.dxf.style = a['sty']
                at.dxf.owner = ins.dxf.handle
            nb += 1
        else:
            for a in u['att']:
                if not a['txt'].strip(): continue
                t = msp.add_text(a['txt'], dxfattribs={'layer': onek + a['lay'], 'height': a['h'], 'rotation': a['rot']})
                if a['p2'] is not None and (a['al'] or a['va']):
                    t.dxf.halign = a['al']; t.dxf.valign = a['va']; t.dxf.insert = (a['p'][0], a['p'][1]); t.dxf.align_point = (a['p2'][0], a['p2'][1])
                else:
                    t.dxf.insert = (a['p'][0], a['p'][1])
                nt += 1
    return nb, nt
