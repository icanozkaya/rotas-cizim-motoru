"""R2 (14.10.2026 kuralları) yardımcıları: kolon yeri puanlama (köşe + şaft/ortak duvar), eksik çamaşır/bulaşık makinesi,
balkon süzgeci, sıcak suyu soğuğa paralel öteleme, yasak bölge (betonarme / asansör / enerji odası) kontrolü,
çakışmasız kolon etiketi, armatür/malzeme metrajı."""
import math
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

SBW = dict(WC=10.0, DUS=7.0, LV=2.0, CM=4.0, YS=2.0, EV=4.0, BM=4.0)
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ------------------------------------------------------------------ özel mahaller (yasak bölgeler) ve metinler
def texts(R, key):
    return [(a[1][-1], a[2][0]) for a in R if a[0] == 'T' and key in a[2][0]]


def ortho_walls(W):
    """yalnız eksene paralel duvar çizgileri (asansör boşluğu çaprazları ışını kesmesin)"""
    from shapely import STRtree
    ls = [l for l in W.ls if abs(l.coords[0][0] - l.coords[-1][0]) < 0.6 or abs(l.coords[0][1] - l.coords[-1][1]) < 0.6]
    return ls, STRtree(ls)


def ray_o(OW, s, d, L=700.0):
    ls, tree = OW
    seg = LineString([s, (s[0] + d[0] * L, s[1] + d[1] * L)])
    best = L
    for i in tree.query(seg):
        it = ls[i].intersection(seg)
        if it.is_empty:
            continue
        for g in (it.geoms if hasattr(it, 'geoms') else [it]):
            for q in (g.coords if g.geom_type != 'Point' else [g.coords[0]]):
                dd = _d(q, s)
                if 0.5 < dd < best:
                    best = dd
    return best


def rect_o(OW, s):
    e, w = ray_o(OW, s, (1, 0)), ray_o(OW, s, (-1, 0))
    n, so = ray_o(OW, s, (0, 1)), ray_o(OW, s, (0, -1))
    return (s[0] - w, s[1] - so, s[0] + e, s[1] + n)


def yasak_bolgeler(R, W, cols):
    """kat yasak bölgeleri: betonarme kolon/perde (tüm hatlar), asansör boşluğu (tüm hatlar), enerji odası (ıslak hat)"""
    OW = ortho_walls(W)
    out = [dict(tip='BETONARME', g=c) for c in cols]
    for p, t in texts(R, 'asansör'):
        r = rect_o(OW, p)
        if (r[2] - r[0]) * (r[3] - r[1]) < 12e4:
            out.append(dict(tip='ASANSÖR BOŞLUĞU', g=box(*r)))
    for p, t in texts(R, 'en. odas'):
        r = rect_o(OW, p)
        if (r[2] - r[0]) * (r[3] - r[1]) < 4e4:
            out.append(dict(tip='ENERJİ ODASI', g=box(*r)))
    return out


# ------------------------------------------------------------------ kolon yeri: köşe adayları + puan
class GercekDuvar:
    """yalnız gerçek duvar çizgileri: eksene paralel çizgiler aynı doğru üzerinde birleştirilir (kapı/pencere kesintisi
    ile bölünmüş duvar yüzü tek parça olur); birleşik boyu >= 100 cm olanlar duvardır. Tezgâh / eviye / tekne çizgileri
    (kısa, kapalı küçük şekiller) ışını kesmez."""
    def __init__(self, W, Lmin=100.0):
        from shapely import STRtree
        segs = {}
        for l in W.ls:
            cs = list(l.coords)
            for (x0, y0), (x1, y1) in zip(cs[:-1], cs[1:]):
                if abs(y0 - y1) < 0.6:
                    segs.setdefault(('h', round((y0 + y1) / 2)), []).append(sorted((x0, x1)))
                elif abs(x0 - x1) < 0.6:
                    segs.setdefault(('v', round((x0 + x1) / 2)), []).append(sorted((y0, y1)))
        keep = []
        for (o, c), iv in segs.items():
            iv.sort()
            cur = list(iv[0])
            for a_, b_ in iv[1:] + [[1e18, 1e18]]:
                if a_ <= cur[1] + 1.0:
                    cur[1] = max(cur[1], b_)
                else:
                    if cur[1] - cur[0] >= Lmin:
                        keep.append(LineString([(cur[0], c), (cur[1], c)] if o == 'h' else [(c, cur[0]), (c, cur[1])]))
                    cur = [a_, b_]
        self.ls = keep
        self.tree = STRtree(keep)

    def ray(self, s, d, L=700.0):
        return ray_o((self.ls, self.tree), s, d, L)


def kolon_adaylari(d, w, fx):
    """ıslak hacimdeki her armatürden en yakın duvara, oradan duvar boyunca iki yöne köşeye kadar (<= 260 cm) aday"""
    W = d.setdefault('GW', None) or GercekDuvar(d['W'])
    d['GW'] = W
    out = []
    for f in fx:
        p = f['c']
        for dn in DIRS:
            dist = W.ray(p, dn)
            if dist > 120:
                continue
            q = (p[0] + dn[0] * (dist - 10.0), p[1] + dn[1] * (dist - 10.0))
            out.append(dict(p=q, corner=False, f=f))
            for a in ((-dn[1], dn[0]), (dn[1], -dn[0])):
                da = W.ray(q, a)
                if da <= 260:
                    out.append(dict(p=(q[0] + a[0] * (da - 10.0), q[1] + a[1] * (da - 10.0)), corner=True, f=f))
    return out


def kolon_puan(c, fx, mek, cols, yasak, wet_others):
    p = c['p']
    # SB ağırlıklı ortalama uzaklık (boru boyu)
    ws = sum(SBW.get(f['kind'], 1.0) for f in fx) or 1.0
    s = sum(SBW.get(f['kind'], 1.0) * _d(p, f['c']) for f in fx) / ws
    if c['corner']:
        s -= 40.0
    if mek and min(_d(p, m) for m in mek) < 70:
        s -= 110.0                                   # havalandırma şaftı / tesisat şaftı yanı
    if wet_others and min(_d(p, q) for q in wet_others) < 90:
        s -= 35.0                                    # ortak ıslak duvar (komşu ıslak hacmin armatürü yakında)
    if any(z['g'].buffer(7).contains(Point(p)) for z in yasak):
        s += 1e4
    return s


def kolon_yeri2(d, w, mek, yasak):
    fx = [f for f in d['F'] if f['room'] is w and f['kind'] in SBW]
    if not fx:
        return None
    oth = [f['c'] for f in d['F'] if f['room'] is not None and f['room'] is not w and f['room']['name'] != 'mutfak'
           and f['kind'] in SBW]
    cands = kolon_adaylari(d, w, fx)
    if any(c['corner'] for c in cands):
        cands = [c for c in cands if c['corner']]          # kural: kolon mahal köşesinden
    if w['name'] == 'mutfak':
        fx = [f for f in fx if f['kind'] == 'EV'] or fx     # mutfakta eviyeye en yakın köşe
    best = None
    for c in cands:
        sc = kolon_puan(c, fx, mek, d['cols'], yasak, oth if w['name'] != 'mutfak' else [])
        if best is None or sc < best[0]:
            best = (sc, c)
    q = best[1]['p']
    # yasak bölgeye düşerse duvar boyunca >= 15 cm dışarı ötele
    W = d['W']
    if any(z['g'].buffer(15).contains(Point(q)) for z in yasak):
        for s in range(2, 200, 2):
            ok = None
            for v in DIRS:
                q2 = (q[0] + v[0] * s, q[1] + v[1] * s)
                if W.cross(q, q2) == 0 and not any(z['g'].buffer(15).contains(Point(q2)) for z in yasak):
                    ok = q2
                    break
            if ok:
                q = ok
                break
    return q


# ------------------------------------------------------------------ eksik çamaşır / bulaşık makinesi
def ek_makineler(d):
    """her dairede ÇM (banyo / wc+banyo / duş) ve BM (mutfak) yoksa ekle (f['ek']=True)"""
    W = d['W']
    eklenen = []
    daireler = sorted({w['daire'] for w in d['wet'] if w.get('daire')})
    for dn in daireler:
        F = [f for f in d['F'] if f.get('daire') == dn]
        wets = [w for w in d['wet'] if w.get('daire') == dn]
        if not any(f['kind'] == 'CM' for f in F):
            for nm in ('banyo', 'wc+banyo', 'wc-banyo', 'wc-duş', 'duş', 'wc-lvb.', 'mutfak'):
                rs = [w for w in wets if w['name'] == nm]
                if rs:
                    p = _bos_kose(d, rs[0], 32.0)
                    if p:
                        f = dict(kind='CM', c=p, room=rs[0], daire=dn, ek=True)
                        d['F'].append(f); eklenen.append(f)
                        break
        if not any(f['kind'] == 'BM' for f in F):
            ms = [w for w in wets if w['name'] == 'mutfak']
            ev = [f for f in F if f['kind'] == 'EV']
            if ms and ev:
                e = ev[0]['c']
                dist, dnv = min(((W.ray(e, v), v) for v in DIRS), key=lambda t: t[0])
                base = (e[0] + dnv[0] * (dist - 30.0), e[1] + dnv[1] * (dist - 30.0))
                cand = []
                for sg in (1, -1):
                    for off in (60.0, 65.0, 120.0):
                        q = (base[0] - dnv[1] * off * sg, base[1] + dnv[0] * off * sg)
                        free = min([_d(q, f['c']) for f in d['F'] if f is not ev[0]] + [999])
                        room = min(W.ray(q, (-dnv[1] * sg, dnv[0] * sg)), 999)
                        if room >= 28 and free >= 45:
                            cand.append((off, -free, q))
                if cand:
                    q = min(cand)[2]
                    f = dict(kind='BM', c=q, room=ms[0], daire=dn, ek=True)
                    d['F'].append(f); eklenen.append(f)
    return eklenen


def _bos_kose(d, w, inset):
    """ıslak hacimde armatürden en uzak, duvarlara yaslı köşe (makine merkezi duvardan inset)"""
    W = d['W']
    fx = [f for f in d['F'] if f['room'] is w]
    seeds = [f['c'] for f in fx] + [w['xy']]
    best = None
    for s in seeds:
        for dn in DIRS:
            dist = W.ray(s, dn)
            if dist > 200:
                continue
            q = (s[0] + dn[0] * (dist - inset), s[1] + dn[1] * (dist - inset))
            for a in ((-dn[1], dn[0]), (dn[1], -dn[0])):
                da = W.ray(q, a)
                if da > 300:
                    continue
                c = (q[0] + a[0] * (da - inset), q[1] + a[1] * (da - inset))
                if W.cross(c, w['xy']) > 0:
                    continue
                fr = min([_d(c, f['c']) for f in fx] + [999])
                if fr < 50:
                    continue
                if best is None or fr > best[0]:
                    best = (min(fr, 120), c)
    return best[1] if best else None


# ------------------------------------------------------------------ balkon süzgeçleri
def balkon_suzgecleri(d, R, ybp):
    """balkon etiketinden ortogonal dikdörtgen; süzgeç en yakın yağmur inişine bakan köşede (duvardan 20 cm)"""
    OW = ortho_walls(d['W'])
    out = []
    for p, t in texts(R, 'balkon'):
        if t.strip() != 'balkon' or not ybp:
            continue
        r = rect_o(OW, p)
        yb = min(ybp, key=lambda q: _d(q, p))
        cs = [(r[0] + 20, r[1] + 20), (r[2] - 20, r[1] + 20), (r[0] + 20, r[3] - 20), (r[2] - 20, r[3] - 20)]
        c = min(cs, key=lambda q: _d(q, yb))
        out.append(dict(p=c, yb=yb, rect=r, lab=p))
    return out


# ------------------------------------------------------------------ sıcak su: soğuk ağaçta kombi -> sıcak armatür yolları, paralel öteleme
def agac_graf(paths):
    import networkx as nx
    lines = unary_union([LineString(p) for p in paths if len(p) >= 2])
    G = nx.Graph()
    for g in (lines.geoms if hasattr(lines, 'geoms') else [lines]):
        cs = [(round(x, 3), round(y, 3)) for x, y in g.coords]
        for a, b in zip(cs[:-1], cs[1:]):
            if a != b:
                G.add_edge(a, b, w=_d(a, b))
    return G


def en_yakin_dugum(G, p):
    return min(G.nodes, key=lambda n: _d(n, p))


def sicak_yollar(G, kombi, hedefler):
    import networkx as nx
    k = en_yakin_dugum(G, kombi)
    E = set()
    for h in hedefler:
        t = en_yakin_dugum(G, h)
        try:
            pth = nx.shortest_path(G, k, t, weight='w')
        except Exception:
            continue
        for a, b in zip(pth[:-1], pth[1:]):
            E.add(tuple(sorted((a, b))))
    from shapely.ops import linemerge
    if not E:
        return []
    m = linemerge([LineString(e) for e in E])
    return [list(g.coords) for g in (m.geoms if hasattr(m, 'geoms') else [m])]


def otele(paths, v):
    return [[(x + v[0], y + v[1]) for x, y in p] for p in paths]


def otele_sec(paths, W, yasak, d=7.0):
    """4 ötelemeden (±d, ±d) duvar / yasak bölge kesişimi en az olanı"""
    best = None
    for v in ((d, d), (-d, d), (d, -d), (-d, -d)):
        ps = otele(paths, v)
        sc = 0.0
        for p in ps:
            ls = LineString(p)
            sc += sum(1 for i in W.tree.query(ls) if W.ls[i].intersects(ls))
            sc += sum(100 for z in yasak if ls.intersects(z['g']))
        if best is None or sc < best[0]:
            best = (sc, v, ps)
    return best[1], best[2]


# ------------------------------------------------------------------ çakışmasız etiket (kolon no balonu)
def serbest_yer(center, r, engel, r0=None, yasak_kutu=()):
    """center çevresinde r yarıçaplı balon için engel çizgilerine en az değen konum"""
    best = None
    for dist in ([r0] if r0 else []) + [r + 6, r + 14, r + 26, r + 40, r + 60]:
        for k in range(16):
            a = math.radians(22.5 * k + 45)
            q = (center[0] + math.cos(a) * dist, center[1] + math.sin(a) * dist)
            disk = Point(q).buffer(r + 2)
            hit = sum(g.intersection(disk).length if g.geom_type != 'Polygon' else g.intersection(disk).area * 0.2
                      for g in engel.query_geoms(disk))
            hit += sum(1000 for b in yasak_kutu if b.intersects(disk))
            sc = hit * 10 + dist
            if best is None or sc < best[0]:
                best = (sc, q, hit)
        if best and best[2] < 0.5:
            break
    return best[1], best[2]


# ------------------------------------------------------------------ ıslak hacim -> daire: kapılardan geçen yürüme mesafesi
def geodezik_daire(d, win, noktalar, res=5.0):
    """gerçek duvarlar (birleşik >= 100 cm eksen çizgileri; kapı boşlukları açık) engel; her daire giriş numarasından
    (merdiven holü) yürüme mesafesi. Dönüş: [en yakın daire no] (noktalar sırasıyla)"""
    import numpy as np
    from skimage.graph import MCP_Geometric
    from skimage.draw import line as skl
    from scipy import ndimage
    GW = d.get('GW') or GercekDuvar(d['W']); d['GW'] = GW
    x0, y0, x1, y1 = win
    nx, ny = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
    img = np.zeros((nx, ny), bool)
    ij = lambda p: (min(nx - 1, max(0, int(round((p[0] - x0) / res)))), min(ny - 1, max(0, int(round((p[1] - y0) / res)))))
    for l in GW.ls:
        a, b = ij(l.coords[0]), ij(l.coords[-1])
        rr, cc = skl(a[0], a[1], b[0], b[1]); img[rr, cc] = True
    from skimage.draw import polygon as skp
    for c in d['cols']:                       # betonarme kolon / perde (duvar çizgisi olarak gelmez) de engel
        xs, ys = c.exterior.coords.xy
        rr, cc = skp([(x - x0) / res for x in xs], [(y - y0) / res for y in ys], (nx, ny)); img[rr, cc] = True
    img = ndimage.binary_dilation(img, iterations=1)
    cost = np.where(img, 1e6, 1.0)
    out = []
    dist = {}
    for p, n in d['digits']:
        m = MCP_Geometric(cost)
        cum, _ = m.find_costs([ij(p)])
        dist[n] = cum
    for q in noktalar:
        c = ij(q)
        out.append(min(dist, key=lambda n: dist[n][c]))
    return out
