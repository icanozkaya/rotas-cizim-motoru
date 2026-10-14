"""new_block.dxf -> yalın mimari + mahal / ıslak hacim / armatür / betonarme kolon tanıma (05_ALGORITMALAR §1).

Kaynak: kullanıcının "istediğim düzen" örneği. Mimari tek katmanda (MKDU0, patlatılmış); MTY mekanik çizim ayrı
katmanlarda. Burada YALNIZ MKDU0 kullanılır (kullanıcının mekanik çizimi tanımaya girmez; o yalnız karşılaştırmada okunur).
"""
import math, os, pickle, re, lzma, shutil, subprocess, sys
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box, MultiPolygon
from shapely.ops import unary_union

REPO = '/home/claude/rotas-cizim-motoru'
WD = '/tmp/claude-0/uu'
SRC_XZ = REPO + '/ornekler/new_block.dxf.xz'
SRC = WD + '/new_block.dxf'
MIMARI = WD + '/new_block_mimari.dxf'
CACHE = WD + '/mk.pkl'

# Kat pencereleri (kaynak koordinatı, cm). Zemin pencere; diğer katlar kaydırma ile (oda etiketlerinden ölçüldü).
WIN_Z = (252600.0, -443700.0, 254410.0, -441460.0)
OFF = {'Z': 0.0, '1': 2034.0, '2': 4082.0}
FLOORS = ['Z', '1', '2']
WET = {'banyo': 'B', 'wc+banyo': 'B', 'wc-lvb.': 'W', 'duş': 'D', 'mutfak': 'M'}
ROOM_WORDS = ('salon', 'yatak od.', 'oda', 'mutfak', 'banyo', 'wc+banyo', 'wc-lvb.', 'duş', 'antre-kor.', 'merdiven',
              'yüklük', 'balkon', 'asansör \nboşluğu', 'en. odası.')


def ensure_src():
    os.makedirs(WD, exist_ok=True)
    if not os.path.exists(SRC):
        with lzma.open(SRC_XZ) as f, open(SRC, 'wb') as g:
            shutil.copyfileobj(f, g)


def extract():
    """MKDU0 kayıtları (L/P/A/C/T/H) + yalın mimari DXF (MTY-*, M-*, RAST-*, TEM.SU ve MTY blokları süzülmüş)."""
    if os.path.exists(CACHE) and os.path.exists(MIMARI):
        return pickle.load(open(CACHE, 'rb'))
    import ezdxf
    from ezdxf import path as ep
    ensure_src()
    doc = ezdxf.readfile(SRC)
    msp = doc.modelspace()
    A = []
    drop = []
    for e in msp:
        lay = e.dxf.layer
        if lay != 'MKDU0':
            if lay not in ('YAZI', 'ANTED'):
                drop.append(e)
            continue
        t = e.dxftype()
        try:
            if t == 'LINE':
                A.append(('L', [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]], None))
            elif t in ('LWPOLYLINE', 'ARC', 'POLYLINE', 'ELLIPSE', 'SPLINE'):
                pts = [(v.x, v.y) for v in ep.make_path(e).flattening(1.0)]
                if t == 'LWPOLYLINE' and e.closed and pts and pts[0] != pts[-1]:
                    pts.append(pts[0])
                A.append(('A' if t in ('ARC', 'ELLIPSE') else 'P', pts, None))
            elif t == 'CIRCLE':
                A.append(('C', [tuple(e.dxf.center)[:2]], e.dxf.radius))
            elif t == 'TEXT':
                p = e.dxf.align_point if (e.dxf.halign or e.dxf.valign) and e.dxf.hasattr('align_point') else e.dxf.insert
                w_ = len(e.dxf.text) * e.dxf.height * 0.55
                cx = p[0] + w_ / 2 * (1 - e.dxf.halign) if e.dxf.halign in (0, 1, 2) else p[0]
                A.append(('T', [tuple(e.dxf.insert)[:2], (cx, p[1])], (e.dxf.text, e.dxf.height, e.dxf.rotation)))
            elif t == 'MTEXT':
                txt = e.plain_text()
                h = e.dxf.char_height
                w_ = max(len(q) for q in txt.split('\n')) * h * 0.55 if txt else 0
                nl = txt.count('\n') + 1
                ap = e.dxf.get('attachment_point', 1)
                col, row = (ap - 1) % 3, (ap - 1) // 3
                ip = e.dxf.insert
                cx = ip[0] + w_ / 2 * (1 - col)
                cy = ip[1] - nl * h * 1.4 / 2 * (1 - row)
                A.append(('T', [tuple(ip)[:2], (cx, cy)], (txt, h, e.dxf.get('rotation', 0))))
            elif t == 'HATCH':
                for p in ep.from_hatch(e):
                    A.append(('H', [(v.x, v.y) for v in p.flattening(1.0)], e.dxf.pattern_name))
        except Exception:
            pass
    pickle.dump(A, open(CACHE, 'wb'))
    for e in drop:
        msp.delete_entity(e)
    doc.saveas(MIMARI)
    return A


# ------------------------------------------------------------------ yardımcı
def win(k, pad=0.0):
    o = OFF[k]
    return (WIN_Z[0] + o - pad, WIN_Z[1] - pad, WIN_Z[2] + o + pad, WIN_Z[3] + pad)


def inside(p, w):
    return w[0] <= p[0] <= w[2] and w[1] <= p[1] <= w[3]


def recs_in(A, w, kinds='LPACTH'):
    out = []
    for a in A:
        if a[0] not in kinds:
            continue
        if a[0] in 'LPAH':
            if all(inside(p, w) for p in a[1]):
                out.append(a)
        elif inside(a[1][0], w):
            out.append(a)
    return out


def columns(R):
    """betonarme kolon/perde: ANSI35 taramalı poligonlar (yazı adası olan küçük iç poligonlar atılır)"""
    ps = [Polygon(a[1]).buffer(0) for a in R if a[0] == 'H' and len(a[1]) >= 4]
    ps = [p for p in ps if p.area > 300]
    out = []
    for p in sorted(ps, key=lambda q: -q.area):
        if any(q.buffer(1.0).contains(p) for q in out):
            continue
        out.append(p)
    return out


def labels(R, k):
    """mahal adları; üst katlarda eksik etiket zeminden kaydırılarak tamamlanır"""
    out = []
    for a in R:
        if a[0] == 'T' and a[2][1] >= 19.0:
            t = a[2][0].strip()
            if t in ROOM_WORDS or t.split()[0] in ('salon', 'mutfak', 'banyo'):
                c = a[1][1] if len(a[1]) > 1 else a[1][0]          # yazı merkezi (MTEXT hizalaması dikkate alınır)
                out.append((c[0], c[1], t))
    return out


def walls_ents(R):
    ents = []
    """yalnız duvar benzeri çizgiler: armatür/tefriş (küçük kapalı şekil, yay, daire, kısa çizgi) mahal tespitine girmez"""
    for a in R:
        if a[0] == 'L':
            if math.hypot(a[1][1][0] - a[1][0][0], a[1][1][1] - a[1][0][1]) >= 30:
                ents.append(('L', a[1]))
        elif a[0] == 'P':
            b = _bbox(a[1])
            if max(b[2] - b[0], b[3] - b[1]) >= 130:
                ents.append(('P', a[1]))
    return ents


def rooms_of(A, k, lab_z=None):
    sys.path.insert(0, REPO + '/motor')
    import rooms as RM
    w = win(k)
    R = recs_in(A, w)
    labs = labels(R, k)
    if lab_z is not None:            # zemin etiketlerinden eksikleri tamamla
        have = [(x, y, t) for x, y, t in labs]
        for x, y, t in lab_z:
            q = (x + OFF[k], y)
            if not any(t2 == t and math.hypot(x2 - q[0], y2 - q[1]) < 60 for x2, y2, t2 in have):
                have.append((q[0], q[1], t))
        labs = have
    # mahal tespiti: yalnız uzun çizgiler + kapı / pencere (tefriş hariç değil; armatürler oda içinde ada olur, fill_holes)
    ents = walls_ents(R)
    out, g = RM.detect(ents, labs, w, res=2.0, door=100.0, disc=40.0)
    rms = []
    for i, d in out.items():
        rms.append(dict(name=d['name'], poly=d['poly'], area=d['area'], xy=d['xy']))
    return rms, R


# ------------------------------------------------------------------ armatür tanıma (geometri imzası)
def _bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


class Walls:
    """duvar çizgileri (STRtree) + ışın atma + görünürlük (kaç duvar çizgisi kesiliyor)"""
    def __init__(self, R):
        from shapely import STRtree
        self.ls = [LineString(d) for k, d in walls_ents(R) if len(d) >= 2]
        self.tree = STRtree(self.ls)

    def cross(self, a, b):
        seg = LineString([a, b])
        return sum(1 for i in self.tree.query(seg) if self.ls[i].intersects(seg))

    def ray(self, s, d, L=700.0):
        seg = LineString([s, (s[0] + d[0] * L, s[1] + d[1] * L)])
        best = L
        for i in self.tree.query(seg):
            it = self.ls[i].intersection(seg)
            if it.is_empty:
                continue
            for g in (it.geoms if hasattr(it, 'geoms') else [it]):
                for q in (g.coords if g.geom_type != 'Point' else [g.coords[0]]):
                    dd = math.hypot(q[0] - s[0], q[1] - s[1])
                    if 0.5 < dd < best:
                        best = dd
        return best

    def rect(self, s):
        e, w_ = self.ray(s, (1, 0)), self.ray(s, (-1, 0))
        n, so = self.ray(s, (0, 1)), self.ray(s, (0, -1))
        return (s[0] - w_, s[1] - so, s[0] + e, s[1] + n)


def wet_rooms(R, labs):
    """ıslak hacim: etiket noktası + ışın atma ile dikdörtgen yaklaşık sınır"""
    W = Walls(R)
    out = []
    for x, y, t in labs:
        if t in WET:
            out.append(dict(name=t, xy=(x, y), rect=W.rect((x, y))))
    return out, W


def fixtures(R, wet, W):
    """R: kat kayıtları; wet: ıslak hacimler. Dönüş: [dict(kind, c (bağlantı noktası), room)]"""
    circles = [(a[1][0], a[2]) for a in R if a[0] == 'C']
    arcs = [a[1] for a in R if a[0] == 'A']
    polys = [a[1] for a in R if a[0] == 'P']
    lines = [a[1] for a in R if a[0] == 'L']
    texts = [(a[1][0], a[2][0].strip()) for a in R if a[0] == 'T']
    found = []

    def room_at(p):
        best = None
        for r in wet:
            if math.hypot(r['xy'][0] - p[0], r['xy'][1] - p[1]) > 380:
                continue
            x0, y0, x1, y1 = r['rect']
            inr = x0 - 5 <= p[0] <= x1 + 5 and y0 - 5 <= p[1] <= y1 + 5
            key = (W.cross(p, r['xy']), 0 if inr else 1, math.hypot(r['xy'][0] - p[0], r['xy'][1] - p[1]))
            if best is None or key < best[0]:
                best = (key, r)
        return best[1] if best and best[0][0] <= 2 else None

    # 1) yay kümeleri (birbirine değen yaylar tek şekil): klozet elipsi / alaturka ayak izi / eviye teknesi
    cl = []
    for a in arcs:
        la = LineString(a) if len(a) > 1 else Point(a[0])
        hit = [g for g in cl if g['g'].distance(la) < 3.0]
        if hit:
            g0 = hit[0]
            g0['g'] = unary_union([g0['g'], la] + [h['g'] for h in hit[1:]])
            for h in hit[1:]:
                cl.remove(h)
        else:
            cl.append(dict(g=la))
    for g in cl:
        b = g['g'].bounds
        w_, h_ = b[2] - b[0], b[3] - b[1]
        lo, hi = min(w_, h_), max(w_, h_)
        c = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        r = room_at(c)
        if not r:
            continue
        if 45 <= hi <= 85 and 25 <= lo <= 50 and r['name'] != 'mutfak':
            found.append(dict(kind='WC', c=c, axis='x' if w_ > h_ else 'y', bb=b, room=r))
        elif 25 <= hi <= 60 and 25 <= lo <= 60 and r['name'] == 'mutfak':
            found.append(dict(kind='EV', c=c, bb=b, room=r))
        elif 12 <= hi <= 35 and 4 <= lo <= 16 and r['name'] != 'mutfak':      # alaturka ayak basma yeri
            found.append(dict(kind='ALA', c=c, bb=b, room=r))
    # alaturka: iki ayak izi + gider -> tek WC (alaturka)
    alas = [f for f in found if f['kind'] == 'ALA']
    found = [f for f in found if f['kind'] != 'ALA']
    while alas:
        a = alas.pop()
        mate = min(alas, key=lambda q: math.hypot(q['c'][0] - a['c'][0], q['c'][1] - a['c'][1]), default=None)
        if mate and math.hypot(mate['c'][0] - a['c'][0], mate['c'][1] - a['c'][1]) < 40:
            alas.remove(mate)
            c = ((a['c'][0] + mate['c'][0]) / 2, (a['c'][1] + mate['c'][1]) / 2)
        else:
            c = a['c']
        # gider deliği: en yakın daire (r 4-12)
        dr = min(circles, key=lambda q: math.hypot(q[0][0] - c[0], q[0][1] - c[1]))
        found.append(dict(kind='WC', alaturka=True, c=dr[0] if math.hypot(dr[0][0] - c[0], dr[0][1] - c[1]) < 50 else c,
                          room=a['room'], bb=a['bb']))
    # 2) lavabo: 3 küçük daire (2 batarya + gider) birbirine < 25 cm; duş: kare tekne içinde gider dairesi
    small = [(c, r) for c, r in circles if 1.0 <= r <= 4.5]
    taken = set()
    for i, (c, r) in enumerate(small):
        if i in taken:
            continue
        rr = room_at(c)
        if not rr:
            continue
        nb = [j for j, (c2, r2) in enumerate(small) if j != i and j not in taken and math.hypot(c2[0] - c[0], c2[1] - c[1]) < 26]
        if len(nb) >= 2 and rr['name'] != 'mutfak':
            grp = [i] + nb[:2]
            pts = [small[j][0] for j in grp]
            # gider: diğer ikisinin ortasına en uzak olan
            def aligned(j):           # diğer ikisi (batarya) aynı hizada ise j giderdir
                o = [small[q][0] for q in grp if q != j]
                return min(abs(o[0][0] - o[1][0]), abs(o[0][1] - o[1][1]))
            jd = min(grp, key=aligned)
            taken.update(grp)
            found.append(dict(kind='LV', c=small[jd][0], room=rr))
    for i, (c, r) in enumerate(small):
        if i in taken:
            continue
        rr = room_at(c)
        if not rr or rr['name'] == 'mutfak':
            continue
        # duş teknesi: gideri içeren 65-110 kare kapalı poligon
        for pl in polys:
            if len(pl) < 4:
                continue
            b = _bbox(pl)
            w_, h_ = b[2] - b[0], b[3] - b[1]
            if 60 <= w_ <= 120 and 60 <= h_ <= 120 and b[0] <= c[0] <= b[2] and b[1] <= c[1] <= b[3]:
                found.append(dict(kind='DUS', c=c, bb=b, room=rr))
                taken.add(i)
                break
        else:
            for l in lines:          # tekne çizgilerle çizilmişse: gidere uzanan köşegen (>=50 cm)
                ln = math.hypot(l[1][0] - l[0][0], l[1][1] - l[0][1])
                if ln >= 50 and abs(l[1][0] - l[0][0]) > 25 and abs(l[1][1] - l[0][1]) > 25 and \
                        min(math.hypot(q[0] - c[0], q[1] - c[1]) for q in l) < 12:
                    found.append(dict(kind='DUS', c=c, room=rr))
                    taken.add(i)
                    break
    # 3) mutfak: eviye gideri (yay kümesinden), bulaşık mak. ('bul. mak' yazısı), kombi ('kombi' yazısı)
    for p, t in texts:
        if t.startswith('bul'):
            r = room_at(p)
            if r:
                found.append(dict(kind='BM', c=p, room=r))
        if t == 'kombi':
            found.append(dict(kind='KOMBI', c=p, room=room_at(p)))
    # eviye: mutfakta küçük gider dairesi (r <= 3,5; ocak gözleri r ~10 hariç)
    found = [f for f in found if not (f['kind'] == 'EV' and 'bb' in f)]
    for c, r_ in circles:
        if 1.0 <= r_ <= 3.5:
            mk = [w_ for w_ in wet if w_['name'] == 'mutfak' and math.hypot(w_['xy'][0] - c[0], w_['xy'][1] - c[1]) < 260]
            r = min(mk, key=lambda w_: (W.cross(c, w_['xy']), math.hypot(w_['xy'][0] - c[0], w_['xy'][1] - c[1]))) if mk else None
            if r and r['name'] == 'mutfak' and not any(f['kind'] == 'EV' and f['room'] is r for f in found):
                found.append(dict(kind='EV', c=c, room=r))
    found = [f for f in found if not (f['kind'] == 'EV' and 'bb' in f)]
    # alaturka hela: gider dairesi r ~5 (ayak izleri yay+çizgi), klozet olmayan ıslak hacimde
    for c, r_ in circles:
        if 4.6 <= r_ <= 5.4:
            r = room_at(c)
            if r and r['name'] != 'mutfak' and not any(f['kind'] == 'WC' and f['room'] is r for f in found):
                found.append(dict(kind='WC', alaturka=True, c=c, room=r))
    # 4) yer süzgeci: kısa yatay+dikey çizgilerden ızgara (8-24 cm kare, >=3 yatay ve >=3 dikey)
    short = []
    for l in lines:
        dx_, dy_ = abs(l[1][0] - l[0][0]), abs(l[1][1] - l[0][1])
        if 6 <= max(dx_, dy_) <= 24 and min(dx_, dy_) < 0.5:
            short.append((LineString(l), 'h' if dx_ > dy_ else 'v'))
    grp = []
    for g, o in short:
        hit = [q for q in grp if q['g'].distance(g) < 0.6]
        if hit:
            q0 = hit[0]
            q0['g'] = unary_union([q0['g'], g] + [h['g'] for h in hit[1:]]); q0[o] += 1
            for h in hit[1:]:
                q0['h'] += h['h']; q0['v'] += h['v']; grp.remove(h)
        else:
            grp.append(dict(g=g, h=1 if o == 'h' else 0, v=1 if o == 'v' else 0))
    for q in grp:
        b = q['g'].bounds
        if q['h'] >= 3 and q['v'] >= 3 and 8 <= b[2] - b[0] <= 24 and 8 <= b[3] - b[1] <= 24:
            c = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
            r = room_at(c)
            if r and r['name'] != 'mutfak':
                found.append(dict(kind='YS', c=c, room=r))
    for pl in polys:
        if len(pl) < 5:
            continue
        b = _bbox(pl)
        w_, h_ = b[2] - b[0], b[3] - b[1]
        c = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        r = room_at(c)
        if not r or r['name'] not in ('banyo', 'wc+banyo'):
            continue
        if 50 <= w_ <= 72 and 50 <= h_ <= 72:
            inner = [f for f in found if b[0] <= f['c'][0] <= b[2] and b[1] <= f['c'][1] <= b[3]]
            if not inner and not any(f['kind'] == 'CM' and math.hypot(f['c'][0] - c[0], f['c'][1] - c[1]) < 30 for f in found):
                found.append(dict(kind='CM', c=c, bb=b, room=r))
    return found
