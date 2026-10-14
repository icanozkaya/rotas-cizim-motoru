# -*- coding: utf-8 -*-
"""DXF (R2018/AC1032, ezdxf) çizimi: mimari altlık + sprinkler planı + çap/başlık etiketleri + hidrolik en uzak alan
+ düğüm numaraları + hesap özeti + düğüm tablosu + ekipman listesi + lejant + notlar. Birim cm, plan 1/50.
Yazılar engel kutularıyla (boru, başlık, duvar, kolon, sembol, diğer yazı) çakışmadan yerleştirilir; her yazının
altına ROTAS-YANGIN-MASKE katmanında WIPEOUT konur."""
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import box as sbox
from shapely.ops import unary_union
import networkx as nx
from kurallar import SINIF
from semboller import tanimla, OLCU, KELEBEK

LAY = {
    'ROTAS-MIMARI-DUVAR': 8, 'ROTAS-MIMARI-KOLON': 8, 'ROTAS-MIMARI-KOLON-TARAMA': 9, 'ROTAS-MIMARI-KAPI': 8,
    'ROTAS-MIMARI-MAHAL': 7, 'ROTAS-YANGIN-SPRINKLER': 15, 'ROTAS-YANGIN-SPR-BORU': 140, 'ROTAS-YANGIN-SPR-CAP': 141,
    'ROTAS-YANGIN-KOLON': 6, 'ROTAS-YANGIN-VANA': 1, 'ROTAS-YANGIN-HIDROLIK-ALAN': 2, 'ROTAS-YANGIN-HIDROLIK-TARAMA': 8,
    'ROTAS-YANGIN-DUGUM': 3, 'ROTAS-YANGIN-TABLO': 7, 'ROTAS-YANGIN-YAZI': 7, 'ROTAS-YANGIN-MASKE': 7,
    'ROTAS-YANGIN-BASLIK': 7, 'ROTAS-YANGIN-LEJANT': 7, 'ROTAS-YANGIN-NOT': 1,
}
WD = {25: 0.0, 32: 0.0, 40: 1.5, 50: 2.0, 65: 2.5, 80: 3.0, 100: 4.0, 125: 4.5, 150: 5.0}   # VOYAP kalem genişlikleri
WF = 0.8              # yazı genişlik katsayısı


def fmt(v, n=2):
    return f'{v:.{n}f}'.replace('.', ',')


def tw(s, h):
    # R2b: genişlik denetim aracının tahminiyle (0,8·h·karakter·WF) aynı + pay -> tahmini kutular da çakışmaz
    return len(s) * h * 0.8 * WF + h * 0.4


def th(h):
    return h * 1.35


class Engel:
    """eksene paralel kutu engelleri için ızgara karması"""

    def __init__(self, hucre=100.0):
        self.c = hucre
        self.g = {}
        self.items = []

    def _hucreler(self, b):
        c = self.c
        for i in range(math.floor(b[0] / c), math.floor(b[2] / c) + 1):
            for j in range(math.floor(b[1] / c), math.floor(b[3] / c) + 1):
                yield (i, j)

    def ekle(self, b, tag):
        k = len(self.items)
        self.items.append((b, tag))
        for h in self._hucreler(b):
            self.g.setdefault(h, []).append(k)

    def carpar(self, b, haric=()):
        for h in self._hucreler(b):
            for k in self.g.get(h, ()):
                bb, tag = self.items[k]
                if tag in haric:
                    continue
                if b[0] < bb[2] and b[2] > bb[0] and b[1] < bb[3] and b[3] > bb[1]:
                    return tag
        return None


def seg_kutu(a, b, r):
    return (min(a[0], b[0]) - r, min(a[1], b[1]) - r, max(a[0], b[0]) + r, max(a[1], b[1]) + r)


class Cizim:
    def __init__(self, P):
        self.P = P
        d = ezdxf.new('R2018', setup=True)
        d.header['$INSUNITS'] = 5
        d.header['$LTSCALE'] = 1
        d.styles.add('ROTAS', font='arial.ttf')
        d.set_wipeout_variables(frame=0)
        for n, c in LAY.items():
            d.layers.add(n, color=c)
        self.doc = d
        self.msp = d.modelspace()
        self.sem = tanimla(d)
        self.E = Engel()
        self.yazilar = []           # (x, y, s, h, lay, rot, kutu) -> sonda maske + yazı
        self.borular = []           # kontrol: (zincir_id, pts, dn)
        self.etiketsiz = []

    # ---------------------------------------------------------------- temel
    def PL(self, pts, lay, w=0.0, closed=False, lt=None, lts=None):
        e = self.msp.add_lwpolyline([(p[0], p[1]) for p in pts], close=closed, dxfattribs={'layer': lay})
        if w:
            e.dxf.const_width = w
        if lt:
            e.dxf.linetype = lt
        if lts:
            e.dxf.ltscale = lts
        return e

    def L(self, a, b, lay):
        return self.msp.add_line((a[0], a[1]), (b[0], b[1]), dxfattribs={'layer': lay})

    def yazi(self, x, y, s, h, lay, rot=0.0, engel=True):
        w, t = tw(s, h), th(h)
        if abs(rot) < 1:
            k = (x - w / 2, y - t / 2, x + w / 2, y + t / 2)
        else:
            k = (x - t / 2, y - w / 2, x + t / 2, y + w / 2)
        self.yazilar.append((x, y, s, h, lay, rot, k))
        if engel:
            self.E.ekle(k, 'yazi')
        return k

    def yazilari_bas(self):
        for x, y, s, h, lay, rot, k in self.yazilar:
            self.msp.add_wipeout([(k[0], k[1]), (k[2], k[1]), (k[2], k[3]), (k[0], k[3])],
                                 dxfattribs={'layer': 'ROTAS-YANGIN-MASKE'})
            t = self.msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF})
            t.set_placement((x, y), align=TA.MIDDLE_CENTER)

    def serbest_cizgi(self, a, b, haric=()):
        n = max(2, int(math.dist(a, b) / 4))
        for i in range(1, n):
            p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            if self.E.carpar((p[0] - 0.8, p[1] - 0.8, p[0] + 0.8, p[1] + 0.8), haric):
                return False
        return True

    # ---------------------------------------------------------------- mimari
    def mimari(self):
        P = self.P
        kapilar = [(m['kapi']['p'], m['kapi'].get('w', 90.0), m) for m in P['mahaller'] if m.get('kapi')]
        rects = [m['rect'] for m in P['mahaller']]
        dis = P.get('dis_hat')
        kenarlar = []
        for r in rects + ([dis] if dis else []):
            x0, y0, x1, y1 = r
            kenarlar += [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1))]
        for a, b in kenarlar:
            yatay = abs(a[1] - b[1]) < 0.1
            parcalar = [(a, b)]
            for p, w, m in kapilar:
                if yatay and abs(p[1] - a[1]) <= 20 and min(a[0], b[0]) < p[0] < max(a[0], b[0]):
                    yeni = []
                    for c, d in parcalar:
                        if c[0] < p[0] < d[0]:
                            yeni += [(c, (p[0] - w / 2, c[1])), ((p[0] + w / 2, c[1]), d)]
                        else:
                            yeni.append((c, d))
                    parcalar = yeni
                if (not yatay) and abs(p[0] - a[0]) <= 20 and min(a[1], b[1]) < p[1] < max(a[1], b[1]):
                    yeni = []
                    for c, d in parcalar:
                        if c[1] < p[1] < d[1]:
                            yeni += [(c, (c[0], p[1] - w / 2)), ((c[0], p[1] + w / 2), d)]
                        else:
                            yeni.append((c, d))
                    parcalar = yeni
            for c, d in parcalar:
                if math.dist(c, d) > 0.5:
                    self.L(c, d, 'ROTAS-MIMARI-DUVAR')
                    self.E.ekle(seg_kutu(c, d, 1.0), 'duvar')
        # kapı: söve çizgileri + kanat + açılım yayı (kanat mahal içine açılır)
        for p, w, m in kapilar:
            x0, y0, x1, y1 = m['rect']
            d = {'alt': abs(p[1] - y0), 'ust': abs(p[1] - y1), 'sol': abs(p[0] - x0), 'sag': abs(p[0] - x1)}
            yan = min(d, key=d.get)
            yuz = {'alt': y0, 'ust': y1, 'sol': x0, 'sag': x1}[yan]
            ic = {'alt': 1, 'ust': -1, 'sol': 1, 'sag': -1}[yan]
            karsi = yuz - ic * 2 * abs(yuz - (p[1] if yan in ('alt', 'ust') else p[0]))
            if yan in ('alt', 'ust'):
                for u in (p[0] - w / 2, p[0] + w / 2):
                    self.L((u, yuz), (u, karsi), 'ROTAS-MIMARI-KAPI')
                mn = (p[0] - w / 2, yuz)
                self.L(mn, (mn[0], yuz + ic * w), 'ROTAS-MIMARI-KAPI')
                a0, a1 = (0, 90) if ic > 0 else (270, 360)
                self.msp.add_arc(mn, w, a0, a1, dxfattribs={'layer': 'ROTAS-MIMARI-KAPI'})
            else:
                for v in (p[1] - w / 2, p[1] + w / 2):
                    self.L((yuz, v), (karsi, v), 'ROTAS-MIMARI-KAPI')
                mn = (yuz, p[1] - w / 2)
                self.L(mn, (yuz + ic * w, mn[1]), 'ROTAS-MIMARI-KAPI')
                a0, a1 = (0, 90) if ic > 0 else (90, 180)
                self.msp.add_arc(mn, w, a0, a1, dxfattribs={'layer': 'ROTAS-MIMARI-KAPI'})
        for k in P.get('kolonlar', []):
            pts = [(k[0], k[1]), (k[2], k[1]), (k[2], k[3]), (k[0], k[3])]
            self.PL(pts, 'ROTAS-MIMARI-KOLON', closed=True)
            h = self.msp.add_hatch(dxfattribs={'layer': 'ROTAS-MIMARI-KOLON-TARAMA'})
            h.set_pattern_fill('ANSI31', scale=1.0)
            h.paths.add_polyline_path(pts, is_closed=True)
            self.E.ekle(tuple(k), 'kolon')

    # ---------------------------------------------------------------- hidrolik alan (tarama önce çizilir)
    def hidrolik_alan(self, net, hes):
        r = hes['r']
        parcalar = []
        for h in r['aktif']:
            m = net['heads'][h]['mahal']
            y = net['yer'][m]
            mr = [mm for mm in self.P['mahaller'] if mm['ad'] == m][0]['rect']
            hu, hv = (y['Su'] / 2, y['Sv'] / 2) if y['axis'] == 'x' else (y['Sv'] / 2, y['Su'] / 2)
            b = sbox(max(h[0] - hu, mr[0]), max(h[1] - hv, mr[1]), min(h[0] + hu, mr[2]), min(h[1] + hv, mr[3]))
            parcalar.append(b)
        U = unary_union(parcalar).buffer(1.0, join_style='mitre').buffer(-1.0, join_style='mitre').simplify(0.5)
        self.alan = U
        for g in getattr(U, 'geoms', [U]):
            pts = list(g.exterior.coords)
            h = self.msp.add_hatch(dxfattribs={'layer': 'ROTAS-YANGIN-HIDROLIK-TARAMA'})
            h.set_pattern_fill('ANSI31', scale=12.0)
            h.paths.add_polyline_path(pts[:-1], is_closed=True)
            self.PL(pts[:-1], 'ROTAS-YANGIN-HIDROLIK-ALAN', w=1.5, closed=True, lt='DASHED', lts=8.0)

    # ---------------------------------------------------------------- boru zincirleri
    def zincirler(self, T, root, heads):
        out = []
        for a, b in T.edges:
            T[a][b]['_z'] = None
        cid = 0
        for a, b in nx.bfs_edges(T, root):
            if T[a][b]['_z'] is not None:
                continue
            pts = [a, b]
            e0 = T[a][b]
            e0['_z'] = cid
            cur = b
            while True:
                ch = list(T.successors(cur))
                if len(ch) != 1 or cur in heads:
                    break
                e = T[cur][ch[0]]
                if e['dn'] != e0['dn'] or e['n'] != e0['n']:
                    break
                e['_z'] = cid
                pts.append(ch[0])
                cur = ch[0]
            out.append(dict(id=cid, pts=pts, dn=e0['dn'], n=e0['n']))
            cid += 1
        return out

    def borular_ciz(self, net, vanalar):
        T, root, heads = net['T'], net['root'], net['heads']
        Z = self.zincirler(T, root, heads)
        self.Z = Z
        for z in Z:
            pts = z['pts']
            # vana bulunan parçada boru sembol boyunca kesilir
            parcalar = [list(pts)]
            for v in vanalar:
                if v['zid'] != z['id']:
                    continue
                yeni = []
                for pp in parcalar:
                    bol = None
                    for i, (a, b) in enumerate(zip(pp[:-1], pp[1:])):
                        if _uzerinde(v['p'], a, b):
                            bol = i
                            break
                    if bol is None:
                        yeni.append(pp)
                        continue
                    a, b = pp[bol], pp[bol + 1]
                    L = math.dist(a, b)
                    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
                    y = OLCU[v['blok']]['yari']
                    q1 = (v['p'][0] - ux * y, v['p'][1] - uy * y)
                    q2 = (v['p'][0] + ux * y, v['p'][1] + uy * y)
                    yeni.append(pp[:bol + 1] + [q1])
                    yeni.append([q2] + pp[bol + 1:])
                parcalar = yeni
            for pp in parcalar:
                self.PL(pp, 'ROTAS-YANGIN-SPR-BORU', w=WD[z['dn']])
                self.borular.append((z['id'], pp, z['dn']))
            for a, b in zip(pts[:-1], pts[1:]):
                self.E.ekle(seg_kutu(a, b, WD[z['dn']] / 2 + 1.0), f"boru{z['id']}")
        tip = 'ROTAS-SPR-SARKIK' if self.P.get('tavan', 'asma') == 'asma' else 'ROTAS-SPR-DIK'
        self.bas_tip = tip
        for h in heads:
            self.msp.add_blockref(tip, h, dxfattribs={'layer': 'ROTAS-YANGIN-SPRINKLER'})
            self.E.ekle((h[0] - 13, h[1] - 13, h[0] + 13, h[1] + 13), 'bas')

    # ---------------------------------------------------------------- vanalar (kat zon grubu)
    def vana_yeri(self, net):
        T, root = net['T'], net['root']
        z0 = None
        # kolondan çıkan ilk zincir(ler) üzerinde en uzun parça
        for a, b in nx.bfs_edges(T, root):
            z0 = T[a][b]['_z']
            break
        z = [q for q in self.Z if q['id'] == z0][0]
        segs = sorted(zip(z['pts'][:-1], z['pts'][1:]), key=lambda s: -math.dist(*s))
        a, b = segs[0]
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        if L >= 260:
            t1, t2 = 50.0, 105.0
        else:
            t1, t2 = L * 0.28, L * 0.62
        ang = math.degrees(math.atan2(uy, ux))
        return [dict(blok=KELEBEK, p=(a[0] + ux * t1, a[1] + uy * t1), rot=ang, zid=z0,
                     no='V-01', ad='İZLENEBİLİR KELEBEK VANA', dn=z['dn']),
                dict(blok='ROTAS-AKIS-ANAHTARI', p=(a[0] + ux * t2, a[1] + uy * t2), rot=ang, zid=z0, no='FS-01',
                     ad='AKIŞ ANAHTARI', dn=z['dn'])]

    def vanalar_ciz(self, vanalar):
        for v in vanalar:
            ins = self.msp.add_blockref(v['blok'], v['p'], dxfattribs={'layer': 'ROTAS-YANGIN-VANA', 'rotation': v['rot']})
            k = OLCU[v['blok']]['kutu']
            c = math.cos(math.radians(v['rot']))
            s = math.sin(math.radians(v['rot']))
            xs, ys = [], []
            for x, y in ((k[0], k[1]), (k[2], k[1]), (k[2], k[3]), (k[0], k[3])):
                xs.append(v['p'][0] + x * c - y * s)
                ys.append(v['p'][1] + x * s + y * c)
            v['kutu'] = (min(xs), min(ys), max(xs), max(ys))
            self.E.ekle(v['kutu'], 'sembol')

    def vana_etiket(self, vanalar):
        for v in vanalar:
            kx = v['kutu']
            cx = (kx[0] + kx[2]) / 2
            cy = (kx[1] + kx[3]) / 2
            s = v['no']
            h = 7.0
            ok = False
            for r in (4, 10, 18, 28, 40, 55):
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                    w, t = tw(s, h), th(h)
                    x = cx + dx * ((kx[2] - kx[0]) / 2 + r + w / 2)
                    y = cy + dy * ((kx[3] - kx[1]) / 2 + r + t / 2)
                    k = (x - w / 2, y - t / 2, x + w / 2, y + t / 2)
                    if not self.E.carpar(k):
                        self.yazi(x, y, s, h, 'ROTAS-YANGIN-VANA')
                        ok = True
                        break
                if ok:
                    break
            if not ok:
                self.etiketsiz.append(('vana', s))

    # ---------------------------------------------------------------- çap etiketleri
    def cap_etiketleri(self):
        for z in sorted(self.Z, key=lambda z: sum(math.dist(a, b) for a, b in zip(z['pts'][:-1], z['pts'][1:]))):
            if not self.etiket_zincir(z):
                self.etiketsiz.append(('boru', z['id'], z['dn'], z['n'], z['pts'][0]))

    def _etiket_kur(self, a, b, f, side, off, s1, s2, h1, h2):
        """borunun yanında, boruya paralel iki satır: DN (boruya yakın taraf) ve üstünde başlık sayısı"""
        w = max(tw(s1, h1), tw(s2, h2))
        t1, t2, g = th(h1), th(h2), 1.0
        dep = t1 + g + t2
        yatay = abs(a[1] - b[1]) < 0.1
        if yatay:
            c = a[0] + (b[0] - a[0]) * f
            y = a[1]
            if side > 0:
                k = (c - w / 2, y + off, c + w / 2, y + off + dep)
                p1, p2 = (c, y + off + t1 / 2), (c, y + off + t1 + g + t2 / 2)
            else:
                k = (c - w / 2, y - off - dep, c + w / 2, y - off)
                p2, p1 = (c, y - off - t2 / 2), (c, y - off - t2 - g - t1 / 2)
            rot = 0.0
        else:
            c = a[1] + (b[1] - a[1]) * f
            x = a[0]
            if side > 0:          # sol taraf (yazının üstü -x)
                k = (x - off - dep, c - w / 2, x - off, c + w / 2)
                p1, p2 = (x - off - t1 / 2, c), (x - off - t1 - g - t2 / 2, c)
            else:
                k = (x + off, c - w / 2, x + off + dep, c + w / 2)
                p2, p1 = (x + off + t2 / 2, c), (x + off + t2 + g + t1 / 2, c)
            rot = 90.0
        return k, p1, p2, rot

    def etiket_zincir(self, z):
        s1, s2 = f"DN{z['dn']}", str(z['n'])
        h1, h2 = 10.0, 7.0
        w = max(tw(s1, h1), tw(s2, h2))
        pw = WD[z['dn']] / 2
        segs = sorted(zip(z['pts'][:-1], z['pts'][1:]), key=lambda s: -math.dist(*s))
        for a, b in segs:
            if math.dist(a, b) < w + 16:
                continue
            for f in (0.5, 0.35, 0.65, 0.22, 0.78, 0.42, 0.58, 0.15, 0.85):
                if not (w / 2 + 6 <= f * math.dist(a, b) <= math.dist(a, b) - w / 2 - 6):
                    continue
                for side in (1, -1):
                    k, p1, p2, rot = self._etiket_kur(a, b, f, side, pw + 3.0, s1, s2, h1, h2)
                    if not self.E.carpar(k):
                        self._etiket_yaz(k, p1, p2, rot, s1, s2, h1, h2)
                        return True
        # kılavuzlu: borunun ortasından dik çizgi + yatay yazı
        for a, b in segs:
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            yatay = abs(a[1] - b[1]) < 0.1
            for r in (22, 32, 45, 60, 80, 105, 135):
                for side in (1, -1):
                    if yatay:
                        uc = (m[0], m[1] + side * r)
                        k, p1, p2, rot = self._etiket_kur((uc[0] - 100, uc[1]), (uc[0] + 100, uc[1]), 0.5, side, 0.0,
                                                           s1, s2, h1, h2)
                    else:
                        uc = (m[0] - side * r, m[1])
                        w2 = max(tw(s1, h1), tw(s2, h2))
                        dep = th(h1) + 1.0 + th(h2)
                        cx = uc[0] - side * w2 / 2
                        k = (cx - w2 / 2, m[1] - dep / 2, cx + w2 / 2, m[1] + dep / 2)
                        p1 = (cx, m[1] - dep / 2 + th(h1) / 2)
                        p2 = (cx, m[1] + dep / 2 - th(h2) / 2)
                        rot = 0.0
                    if self.E.carpar(k):
                        continue
                    bas = (m[0], m[1] + side * (pw + 1)) if yatay else (m[0] - side * (pw + 1), m[1])
                    if not self.serbest_cizgi(bas, uc, haric=(f"boru{z['id']}",)):
                        continue
                    self.L(bas, uc, 'ROTAS-YANGIN-SPR-CAP')
                    self.E.ekle(seg_kutu(bas, uc, 0.5), 'kilavuz')
                    self._etiket_yaz(k, p1, p2, rot, s1, s2, h1, h2)
                    return True
        return False

    def _etiket_yaz(self, k, p1, p2, rot, s1, s2, h1, h2):
        self.yazi(p1[0], p1[1], s1, h1, 'ROTAS-YANGIN-SPR-CAP', rot, engel=False)
        self.yazi(p2[0], p2[1], s2, h2, 'ROTAS-YANGIN-SPR-CAP', rot, engel=False)
        self.E.ekle(k, 'yazi')

    # ---------------------------------------------------------------- kolon (riser)
    def kolon(self, net, ad):
        R = net['root']
        T = net['T']
        dn = max(T[R][c]['dn'] for c in T.successors(R))
        n = net['cnt'][R]
        self.msp.add_blockref('ROTAS-SPR-KOLON', R, dxfattribs={'layer': 'ROTAS-YANGIN-KOLON'})
        self.E.ekle((R[0] - 10, R[1] - 10, R[0] + 10, R[1] + 10), 'kolon_sembol')
        s1, s2 = f'DN{dn}', str(n)
        for r in (40, 50, 60, 75, 95, 120, 150, 190, 240):
            for ang in range(0, 360, 15):
                c = (R[0] + r * math.cos(math.radians(ang)), R[1] + r * math.sin(math.radians(ang)))
                kb = (c[0] - 15, c[1] - 15, c[0] + 15, c[1] + 15)
                w = max(tw(s1, 9), tw(s2, 7))
                sag = c[0] >= R[0]
                kx = c[0] + 17 if sag else c[0] - 17 - w
                ke = (kx, c[1] - 14, kx + w, c[1] + 14)
                if self.E.carpar(kb) or self.E.carpar(ke):
                    continue
                u = ((R[0] - c[0]) / r, (R[1] - c[1]) / r)
                a, b = (c[0] + u[0] * 14, c[1] + u[1] * 14), (R[0] - u[0] * 10, R[1] - u[1] * 10)
                if not self.serbest_cizgi(a, b):
                    continue
                self.msp.add_circle(c, 14, dxfattribs={'layer': 'ROTAS-YANGIN-KOLON'})
                self.msp.add_circle(c, 12, dxfattribs={'layer': 'ROTAS-YANGIN-KOLON'})
                self.L(a, b, 'ROTAS-YANGIN-KOLON')
                self.E.ekle(kb, 'kolon_balon')
                self.E.ekle(seg_kutu(a, b, 0.5), 'kilavuz')
                self.yazilar.append((c[0], c[1], ad, 6.5, 'ROTAS-YANGIN-KOLON', 0.0,
                                     (c[0] - 11, c[1] - 5, c[0] + 11, c[1] + 5)))
                self.yazi(kx + w / 2, c[1] - th(9) / 2 + 1, s1, 9, 'ROTAS-YANGIN-SPR-CAP')
                self.yazi(kx + w / 2, c[1] + th(7) / 2 + 1.5, s2, 7, 'ROTAS-YANGIN-SPR-CAP')
                return True
        self.etiketsiz.append(('kolon', ad))
        return False

    # ---------------------------------------------------------------- düğüm / mahal / alan yazıları
    def serbest_yazi(self, p, s, h, lay, rmax=200, kilavuz_ilk=0, rmin=0):
        w, t = tw(s, h), th(h)
        r = rmin
        while r <= rmax:
            for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                x = p[0] + dx * (r + (w / 2 if dx else 0))
                y = p[1] + dy * (r + (t / 2 if dy else 0))
                k = (x - w / 2, y - t / 2, x + w / 2, y + t / 2)
                if self.E.carpar(k):
                    continue
                if r > kilavuz_ilk and kilavuz_ilk >= 0 and r > 0:
                    ex = min(max(p[0], k[0]), k[2])
                    ey = min(max(p[1], k[1]), k[3])
                    if math.dist(p, (ex, ey)) > 16:
                        q0 = (p[0] + (ex - p[0]) * 14 / math.dist(p, (ex, ey)), p[1] + (ey - p[1]) * 14 / math.dist(p, (ex, ey)))
                        if not self.serbest_cizgi(q0, (ex, ey), haric=('bas',)):
                            continue
                        self.L(q0, (ex, ey), lay)
                        self.E.ekle(seg_kutu(q0, (ex, ey), 0.5), 'kilavuz')
                self.yazi(x, y, s, h, lay)
                return k
            r += 4 if r < 40 else 10
        return None

    def dugumler(self, hes):
        for n, ad in hes['ad'].items():
            if n == hes['r'].get('root'):
                continue
            if ad.startswith('SP'):
                continue
            k = self.serbest_yazi(n, ad, 7.0, 'ROTAS-YANGIN-DUGUM', rmax=120, kilavuz_ilk=22, rmin=14)
            if k is None:
                self.etiketsiz.append(('dugum', ad))

    def mahal_adlari(self):
        for m in self.P['mahaller']:
            x0, y0, x1, y1 = m['rect']
            c = ((x0 + x1) / 2, (y0 + y1) / 2)
            a = (x1 - x0) * (y1 - y0) / 1e4
            s = f"{m['ad']}  ({m['sinif']}, {fmt(a, 1)} m²)"
            k = self.serbest_yazi(c, s, 14.0, 'ROTAS-MIMARI-MAHAL', rmax=min(x1 - x0, y1 - y0) / 2, kilavuz_ilk=-1)
            if k is None:
                self.etiketsiz.append(('mahal', m['ad']))

    def alan_yazi(self, hes):
        o = hes['ozet']
        s = f"HİDROLİK EN UZAK ALAN - {o['sinif']} - {fmt(o['A'], 0)} m² - {fmt(o['yog'], 1)} mm/dk - {o['N']} ad. K{int(o['K'])}"
        c = self.alan.centroid
        k = self.serbest_yazi((c.x, c.y), s, 10.0, 'ROTAS-YANGIN-HIDROLIK-ALAN', rmax=900, kilavuz_ilk=-1)
        if k is None:
            self.etiketsiz.append(('alan', s))

    # ---------------------------------------------------------------- tablolar
    def tablo(self, x, y, baslik, kolonlar, satirlar, h=9.0, rh=None):
        """kolonlar: [(başlık, genişlik, hiza)], y: üst kenar. Dönüş: alt kenar y"""
        rh = rh or h * 2.0
        W = sum(c[1] for c in kolonlar)
        lay = 'ROTAS-YANGIN-TABLO'
        self.msp.add_text(baslik, height=h * 1.4, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x, y + h * 0.8), align=TA.BOTTOM_LEFT)
        tum = [[c[0] for c in kolonlar]] + satirlar
        yy = y
        self.PL([(x, y), (x + W, y)], lay)
        for i, row in enumerate(tum):
            xx = x
            for (cb, cw, hz), v in zip(kolonlar, row):
                hh = h if i else h * 0.9
                if hz == 'L':
                    self.msp.add_text(str(v), height=hh, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
                        .set_placement((xx + h * 0.5, yy - rh / 2), align=TA.MIDDLE_LEFT)
                else:
                    self.msp.add_text(str(v), height=hh, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
                        .set_placement((xx + cw / 2, yy - rh / 2), align=TA.MIDDLE_CENTER)
                xx += cw
            yy -= rh
            self.PL([(x, yy), (x + W, yy)], lay, w=(1.0 if i == 0 else 0.0))
        xx = x
        for c in kolonlar + [None]:
            self.L((xx, y), (xx, yy), lay)
            if c:
                xx += c[1]
        return yy

    def ozet_tablo(self, x, y, hes, net):
        o = hes['ozet']
        rows = [
            ('Tehlike sınıfı (TS EN 12845)', o['sinif']),
            ('Tasarım yoğunluğu', f"{fmt(o['yog'], 1)} mm/dk"),
            ('İşletme alanı (ıslak sistem)', f"{fmt(o['A'], 0)} m²"),
            ('Başlık tipi', f"K{int(o['K'])}, {'sarkık' if self.bas_tip.endswith('SARKIK') else 'dik'}, 68 °C"),
            ('En elverişsiz başlıkta en düşük basınç', f"{fmt(o['pmin'], 2)} bar"),
            ('Kattaki toplam başlık', f"{o['toplam_bas']} ad."),
            ('Hidrolik en uzak alan', f"{o['mahal']} ({o['N']} başlık; {o['aday']} aday alan hesaplandı)"),
            ('En elverişsiz başlık debisi q', f"{fmt(o['qmin'], 1)} l/dk"),
            ('Alan toplam debisi Q (dengeli)', f"{fmt(o['Qs'], 0)} l/dk"),
            ('Kolon (SP-1) çıkışında gerekli basınç', f"{fmt(o['P_kolon'], 2)} bar"),
            (f"Besleme hattı kaybı (DN{o['besleme_dn']}, {fmt(o['besleme_L'], 0)} m)", f"{fmt(o['dp_bes'], 2)} bar"),
            ('Alarm + zon vana kayıpları (kabul)', f"{fmt(o['dp_van'], 2)} bar"),
            ('Statik yükseklik (pompa ekseni → başlık)', f"{fmt(o['statik_m'], 1)} m = {fmt(o['stat'], 2)} bar"),
            ('Ek debi (dolap / hortum payı)', f"{fmt(o['ek'], 0)} l/dk"),
            ('Sprinkler debisi - hesaplanan', f"{fmt(o['Qp_m3h'], 1)} m³/h ({fmt(o['Qp'], 0)} l/dk)"),
            ('Sprinkler için pompa basıncı - hesaplanan', f"{fmt(o['Hp'], 1)} mSS = {fmt(o['Pp'], 2)} bar"),
            (f"Yangın suyu deposu ({o['sure']} dk, yalnız sprinkler)", f"{fmt(o['V'], 1)} m³"),
            ('En yüksek boru hızı', f"{fmt(o['vmax'], 2)} m/s {'≤' if o['v_ok'] else '>'} 10 m/s"),
            ('Hazen-Williams C / formül', '120 / p = 6,05·10⁵·Q^1,85 / (C^1,85·d^4,87)'),
        ]
        return self.tablo(x, y, 'SPRİNKLER HİDROLİK HESAP ÖZETİ', [('KALEM', 520, 'L'), ('DEĞER', 560, 'L')],
                          [list(r) for r in rows], h=10.0)

    def dugum_tablo(self, x, y, hes):
        cols = [('Düğüm', 70, 'C'), ('→', 70, 'C'), ('Başlık', 60, 'C'), ('P (bar)', 75, 'C'), ('q (l/dk)', 75, 'C'),
                ('Q (l/dk)', 80, 'C'), ('DN', 55, 'C'), ('İç Ø (mm)', 75, 'C'), ('L (m)', 65, 'C'), ('Parça', 65, 'C'),
                ('Le (m)', 65, 'C'), ('Lt (m)', 65, 'C'), ('J (bar/m)', 85, 'C'), ('Δp (bar)', 75, 'C'),
                ('P→ (bar)', 80, 'C'), ('v (m/s)', 70, 'C')]
        rows = []
        for s in hes['satir']:
            rows.append([s['den'], s['ye'], s['bas'], fmt(s['P'], 3), fmt(s['q'], 1) if s['q'] else '-', fmt(s['Q'], 1),
                         str(s['dn']), fmt(s['d'], 1), fmt(s['L'], 2), s['fit'] or '-', fmt(s['Le'], 2), fmt(s['Lt'], 2),
                         fmt(s['J'], 4), fmt(s['dp'], 3), fmt(s['Pye'], 3), fmt(s['v'], 2)])
        return self.tablo(x, y, 'HİDROLİK HESAP TABLOSU (DÜĞÜM - DÜĞÜM, HAZEN-WILLIAMS C=120, Q = K·√P)', cols, rows,
                          h=8.0)

    def ekipman_tablo(self, x, y, vanalar, net, hes):
        n = len(net['heads'])
        R = net['root']
        dn = max(net['T'][R][c]['dn'] for c in net['T'].successors(R))
        rows = [[hes['ad'][R], 'SPRİNKLER KOLONU (RISER)', f'DN{dn}', '1']]
        for v in vanalar:
            rows.append([v['no'], v['ad'], f"DN{v['dn']}", '1'])
        rows.append(['-', f"SPRİNKLER BAŞLIĞI {'SARKIK' if self.bas_tip.endswith('SARKIK') else 'DİK'} K{int(hes['ozet']['K'])} 68 °C",
                     '1/2"', str(n)])
        return self.tablo(x, y, 'EKİPMAN LİSTESİ', [('NO', 90, 'C'), ('TANIM', 520, 'L'), ('ÇAP', 110, 'C'),
                                                     ('ADET', 90, 'C')], rows, h=10.0)

    def lejant(self, x, y):
        lay = 'ROTAS-YANGIN-LEJANT'
        self.msp.add_text('LEJANT', height=14, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x, y + 8), align=TA.BOTTOM_LEFT)
        satir = 0

        def yaz(s):
            self.msp.add_text(s, height=10, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
                .set_placement((x + 150, y - 30 - satir * 50), align=TA.MIDDLE_LEFT)

        def yc():
            return y - 30 - satir * 50
        bt = 'SARKIK (PENDENT) SPRİNKLER K80 68 °C' if self.bas_tip.endswith('SARKIK') else 'DİK (UPRIGHT) SPRİNKLER K80 68 °C'
        self.msp.add_blockref(self.bas_tip, (x + 60, yc()), dxfattribs={'layer': 'ROTAS-YANGIN-SPRINKLER'})
        yaz(bt); satir += 1
        self.PL([(x + 10, yc()), (x + 110, yc())], 'ROTAS-YANGIN-SPR-BORU', w=2.0)
        yaz('SPRİNKLER BORUSU (TS EN 10255 ORTA SERİ, KIRMIZI)'); satir += 1
        self.msp.add_blockref(KELEBEK, (x + 60, yc()), dxfattribs={'layer': 'ROTAS-YANGIN-VANA'})
        self.PL([(x + 10, yc()), (x + 50, yc())], 'ROTAS-YANGIN-SPR-BORU')
        self.PL([(x + 70, yc()), (x + 110, yc())], 'ROTAS-YANGIN-SPR-BORU')
        yaz('İZLENEBİLİR KELEBEK VANA (V-..)'); satir += 1
        self.msp.add_blockref('ROTAS-AKIS-ANAHTARI', (x + 60, yc()), dxfattribs={'layer': 'ROTAS-YANGIN-VANA'})
        self.PL([(x + 10, yc()), (x + 43.7, yc())], 'ROTAS-YANGIN-SPR-BORU')
        self.PL([(x + 76.3, yc()), (x + 110, yc())], 'ROTAS-YANGIN-SPR-BORU')
        yaz('AKIŞ ANAHTARI (FS-..)'); satir += 1
        self.msp.add_blockref('ROTAS-SPR-KOLON', (x + 35, yc()), dxfattribs={'layer': 'ROTAS-YANGIN-KOLON'})
        self.msp.add_circle((x + 85, yc()), 14, dxfattribs={'layer': 'ROTAS-YANGIN-KOLON'})
        self.msp.add_circle((x + 85, yc()), 12, dxfattribs={'layer': 'ROTAS-YANGIN-KOLON'})
        self.msp.add_text('SP-1', height=6.5, dxfattribs={'layer': 'ROTAS-YANGIN-KOLON', 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x + 85, yc()), align=TA.MIDDLE_CENTER)
        self.L((x + 44, yc()), (x + 71, yc()), 'ROTAS-YANGIN-KOLON')
        yaz('SPRİNKLER KOLONU VE KOLON NUMARASI'); satir += 1
        self.PL([(x + 10, yc() - 14), (x + 110, yc() - 14)], 'ROTAS-YANGIN-SPR-BORU')
        for s, hh, dy in (('DN32', 10, -4), ('3', 7, 7)):
            self.msp.add_text(s, height=hh, dxfattribs={'layer': 'ROTAS-YANGIN-SPR-CAP', 'style': 'ROTAS', 'width': WF}) \
                .set_placement((x + 60, yc() + dy), align=TA.MIDDLE_CENTER)
        yaz('ÇAP ETİKETİ: ALTTA DN, ÜSTTE BESLENEN BAŞLIK SAYISI'); satir += 1
        q = [(x + 15, yc() - 15), (x + 105, yc() - 15), (x + 105, yc() + 15), (x + 15, yc() + 15)]
        h = self.msp.add_hatch(dxfattribs={'layer': 'ROTAS-YANGIN-HIDROLIK-TARAMA'})
        h.set_pattern_fill('ANSI31', scale=3.0)
        h.paths.add_polyline_path(q, is_closed=True)
        self.PL(q, 'ROTAS-YANGIN-HIDROLIK-ALAN', w=1.5, closed=True, lt='DASHED', lts=2.0)
        yaz('HİDROLİK EN UZAK ALAN (İŞLETME ALANI)'); satir += 1
        self.msp.add_text('S1 / N1', height=7, dxfattribs={'layer': 'ROTAS-YANGIN-DUGUM', 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x + 60, yc()), align=TA.MIDDLE_CENTER)
        yaz('HESAP DÜĞÜMÜ: S = ÇALIŞAN BAŞLIK, N = BORU DÜĞÜMÜ'); satir += 1
        q = [(x + 40, yc() - 20), (x + 80, yc() - 20), (x + 80, yc() + 20), (x + 40, yc() + 20)]
        self.PL(q, 'ROTAS-MIMARI-KOLON', closed=True)
        h = self.msp.add_hatch(dxfattribs={'layer': 'ROTAS-MIMARI-KOLON-TARAMA'})
        h.set_pattern_fill('ANSI31', scale=1.0)
        h.paths.add_polyline_path(q, is_closed=True)
        yaz('BETONARME KOLON'); satir += 1
        return y - 30 - satir * 50

    def notlar(self, x, y, hes):
        o = hes['ozet']
        nt = [
            f"Sprinkler tesisatı BYKHY ve TS EN 12845'e göre {o['sinif']} tehlike sınıfı, {fmt(o['yog'], 1)} mm/dk yoğunluk ve {fmt(o['A'], 0)} m² işletme alanı ile yapılacaktır.",
            "Borular TS EN 10255 orta seri siyah çelik olacak, DN50 ve altı dişli, DN65 ve üstü kaynaklı veya yivli bağlantı ile yapılacaktır.",
            "Sprinkler başlıkları K80, 68 °C, standart tepkili olarak monte edilecektir.",
            "Boru çapları ROTAŞ başlık sayısı tablosuna göre seçilmiş olup hidrolik hesap tablosu ile doğrulanacaktır; ana hat her ayrımda en fazla bir standart kademe düşer (DN150-125-100-80-65...).",
            "Kolon çıkışında izlenebilir kelebek vana, akış anahtarı ve DN32 test-drenaj vanası (kolon şemasında) yapılacaktır.",
            "Tesisat 15 bar basınçla 2 saat hidrostatik teste tabi tutulacaktır.",
            "Askı ve deprem destekleri TS EN 12845 ve NFPA 13'e uygun olarak yapılacaktır.",
            "Pompa ve depo değerleri tek kat hesabıdır; pompa seçimi (sistem çalışma basıncı 9-10 bar) kolon şemasındaki pompa tablosundadır.",
        ]
        if self.P.get('deneme'):
            nt.append("DENEME: mimari yapaydır, hidrolik giriş değerleri örnektir; bu çizim uygulamada kullanılmayacaktır.")
        lay = 'ROTAS-YANGIN-NOT'
        self.msp.add_text('NOTLAR :', height=14, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x, y), align=TA.BOTTOM_LEFT)
        for i, s in enumerate(nt):
            self.msp.add_text(f'{i + 1}. {s}', height=10, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
                .set_placement((x, y - 30 - i * 22), align=TA.BOTTOM_LEFT)
        return y - 30 - len(nt) * 22

    def basliklar(self):
        P = self.P
        x0, y0, x1, y1 = P['dis_hat']
        lay = 'ROTAS-YANGIN-BASLIK'
        t = f"{P.get('kat_adi', '')} SPRİNKLER TESİSATI PLANI.........ÖLÇEK: 1 / 50"
        self.msp.add_text(t, height=35, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
            .set_placement(((x0 + x1) / 2, y0 - 90), align=TA.MIDDLE_CENTER)
        if P.get('deneme'):
            self.msp.add_text('DENEME', height=60, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
                .set_placement((x0, y1 + 150), align=TA.BOTTOM_LEFT)
        self.msp.add_text(P.get('proje', ''), height=25, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x0, y1 + 90), align=TA.BOTTOM_LEFT)


def _uzerinde(n, a, b):
    if abs(a[0] - b[0]) < 0.1:
        return abs(n[0] - a[0]) < 0.2 and min(a[1], b[1]) - 0.2 <= n[1] <= max(a[1], b[1]) + 0.2
    return abs(n[1] - a[1]) < 0.2 and min(a[0], b[0]) - 0.2 <= n[0] <= max(a[0], b[0]) + 0.2


def ciz(P, net, hes, cikti):
    c = Cizim(P)
    hes['r']['root'] = net['root']
    c.hidrolik_alan(net, hes)
    c.mimari()
    # önce zincirler (vana yeri için), sonra boru + vana
    c.Z = c.zincirler(net['T'], net['root'], net['heads'])
    van = c.vana_yeri(net)
    c.borular_ciz(net, van)
    c.vanalar_ciz(van)
    c.kolon(net, hes['ad'][net['root']])
    c.cap_etiketleri()
    c.vana_etiket(van)
    c.dugumler(hes)
    c.mahal_adlari()
    c.alan_yazi(hes)
    c.yazilari_bas()
    x0, y0, x1, y1 = P['dis_hat']
    X = x1 + 300
    yb = c.ozet_tablo(X, y1, hes, net)
    yb = c.ekipman_tablo(X, yb - 120, van, net, hes)
    yb = c.lejant(X, yb - 110)
    c.notlar(x0, y0 - 220, hes)
    c.dugum_tablo(X + 1250, y1, hes)
    c.basliklar()
    c.doc.saveas(cikti)
    return c, van
