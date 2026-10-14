# -*- coding: utf-8 -*-
"""pompa_grubu ortak çizim çekirdeği (ezdxf, R2018, birim cm).

- Katmanlar ROTAS- önekli. R2 (14.10.2026 B): MTY BLOĞU YOK — vana/armatür sembolleri saf geometri ROTAS-SMB- bloklarıdır
  (motor/deneme/sprinkler/rotas_sembol.py, LINE/CIRCLE/ARC/LWPOLYLINE/HATCH). Elektrik kalemi (kablo/sinyal) çizilmez.
- Görünüşte önde kalan nesne (ör. önden geçen emiş kollektörü) arkadakini örter: arkadaki çizgiler kırpılır
  (z sırası), böylece çizgiler üst üste binmez. Vana/blok konan borular blok boyunca kesilir.
- Yazıların altına ROTAS-MASKE katmanında WIPEOUT konur; yazı/yazı ve yazı/blok çakışması denetlenir.
"""
import math, os, glob, sys
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import LineString, Polygon, box as sbox, Point
from shapely.ops import unary_union

MOTOR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if MOTOR not in sys.path:
    sys.path.insert(0, MOTOR)
_SPR = os.path.join(MOTOR, 'deneme', 'sprinkler')
if _SPR not in sys.path:
    sys.path.append(_SPR)                 # yalnız rotas_sembol için (sona eklenir: semboller.py ad çakışması olmasın)
import rotas_sembol as RS                 # noqa: E402

LAYERS = {
    'ROTAS-POMPA-EKIPMAN': (4, 'Continuous'), 'ROTAS-POMPA-GIZLI': (4, 'DASHED'), 'ROTAS-POMPA-KAIDE': (8, 'Continuous'),
    'ROTAS-TARAMA': (8, 'Continuous'), 'ROTAS-BETON': (7, 'Continuous'), 'ROTAS-SU-SEVIYE': (5, 'DASHED'),
    'ROTAS-YANGIN-BORU': (1, 'Continuous'), 'ROTAS-SOGUKSU-BORU': (5, 'Continuous'), 'ROTAS-PISSU-BORU': (6, 'Continuous'),
    'ROTAS-YAKIT-BORU': (30, 'Continuous'), 'ROTAS-EGZOZ': (8, 'Continuous'), 'ROTAS-DRENAJ-BORU': (140, 'DASHED'),
    'ROTAS-YANGIN-ITFAIYE': (1, 'Continuous'), 'ROTAS-YANGIN-ITFAIYE-SEMBOL': (1, 'Continuous'), 'ROTAS-VANA': (1, 'Continuous'), 'ROTAS-OLCU': (2, 'Continuous'),
    'ROTAS-KOT': (2, 'Continuous'), 'ROTAS-YAZI': (7, 'Continuous'), 'ROTAS-CAP': (3, 'Continuous'),
    'ROTAS-NUMARA': (1, 'Continuous'), 'ROTAS-TABLO': (7, 'Continuous'), 'ROTAS-BASLIK': (2, 'Continuous'),
    'ROTAS-CERCEVE': (4, 'Continuous'), 'ROTAS-MASKE': (7, 'Continuous'), 'ROTAS-NOT': (1, 'Continuous'),
}
EQ, GZ, KD, TR, BT, SV = 'ROTAS-POMPA-EKIPMAN', 'ROTAS-POMPA-GIZLI', 'ROTAS-POMPA-KAIDE', 'ROTAS-TARAMA', 'ROTAS-BETON', 'ROTAS-SU-SEVIYE'
YB, SB, PB, YK, EG, DR, EL = ('ROTAS-YANGIN-BORU', 'ROTAS-SOGUKSU-BORU', 'ROTAS-PISSU-BORU', 'ROTAS-YAKIT-BORU',
                              'ROTAS-EGZOZ', 'ROTAS-DRENAJ-BORU', None)      # EL: elektrik kalemi YOK (R2)
IT, ITS = 'ROTAS-YANGIN-ITFAIYE', 'ROTAS-YANGIN-ITFAIYE-SEMBOL'
VN, OL, KT, YZ, CP, NU, TB, BS, CR, MS, NT = ('ROTAS-VANA', 'ROTAS-OLCU', 'ROTAS-KOT', 'ROTAS-YAZI', 'ROTAS-CAP', 'ROTAS-NUMARA',
                                              'ROTAS-TABLO', 'ROTAS-BASLIK', 'ROTAS-CERCEVE', 'ROTAS-MASKE', 'ROTAS-NOT')
BORU_LAY = {YB, SB, PB, YK, EG, DR, IT}

# R2: vana sembolleri rotas_sembol (saf geometri). Yarı boy (boru ekseni boyunca, ölçek 1) RS.TANIM'dan.
VANA = {ad: RS.TANIM[ad][2] for ad in RS.TANIM}

DN_OD = {15: 2.13, 20: 2.69, 25: 3.37, 32: 4.24, 40: 4.83, 50: 6.03, 65: 7.61, 80: 8.89, 100: 11.43, 125: 13.97,
         150: 16.83, 200: 21.91, 250: 27.3}
DN_IC = {15: 1.6, 20: 2.16, 25: 2.79, 32: 3.6, 40: 4.19, 50: 5.3, 65: 6.89, 80: 8.08, 100: 10.5, 125: 12.9,
         150: 15.9, 200: 20.7, 250: 26.0}
DN_LIST = [25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250]


def dn_sec(q_m3h, vmax):
    """hız sınırına göre en küçük DN (iç çap DN_IC)"""
    for dn in DN_LIST:
        a = math.pi * (DN_IC[dn] / 100) ** 2 / 4
        if q_m3h / 3600 / a <= vmax:
            return dn
    return DN_LIST[-1]


def hiz(q_m3h, dn):
    return q_m3h / 3600 / (math.pi * (DN_IC[dn] / 100) ** 2 / 4)


def tr(x, d=2):
    """Türkçe ondalık"""
    s = f'{x:.{d}f}'
    return s.replace('.', ',')


def kot_s(cm):
    m = cm / 100
    if abs(m) < 0.005:
        return '±0,00'
    return ('+' if m > 0 else '-') + tr(abs(m), 2)


class Cizim:
    def __init__(self, olcek=25):
        self.olcek = olcek
        self.th = 0.25 * olcek          # 2,5 mm yazı (cm)
        self.doc = ezdxf.new('R2018', setup=True)
        self.doc.header['$INSUNITS'] = 5
        self.doc.header['$LTSCALE'] = olcek * 0.4
        self.doc.header['$MEASUREMENT'] = 1
        self.doc.styles.add('ROTAS', font='arial.ttf')
        self.doc.set_wipeout_variables(frame=0)
        for n, (c, lt) in LAYERS.items():
            self.doc.layers.add(n, color=c, linetype=lt if lt in self.doc.linetypes or lt == 'Continuous' else 'Continuous')
        self.doc.layers.get(MS).dxf.plot = 1
        self.msp = self.doc.modelspace()
        self.G = []          # geometri: dict(t, pts, lay, z, closed, w)
        self.OCC = []        # örtücüler: (Polygon, z)
        self.HAT = []        # taramalar: (poly pts, lay, z, pattern, scale)
        self.INS = []        # bloklar
        self.TXT = []        # yazılar
        self.LEAD = []       # balon kılavuz çizgileri
        self.BAL = []        # balonlar
        self.DIMS = []
        self._blk = {}
        self.uyari = []
        st = self.doc.dimstyles.new('ROTAS-OLCU')
        th = self.th * 0.9
        st.dxf.dimtxt = th; st.dxf.dimasz = th * 0.8; st.dxf.dimtsz = th * 0.5; st.dxf.dimexe = th * 0.6
        st.dxf.dimexo = th * 0.5; st.dxf.dimgap = th * 0.3; st.dxf.dimdec = 0; st.dxf.dimtad = 1; st.dxf.dimtih = 0
        st.dxf.dimtoh = 0; st.dxf.dimclrd = 2; st.dxf.dimclre = 2; st.dxf.dimclrt = 2; st.dxf.dimtxsty = 'ROTAS'
        st.dxf.dimzin = 8; st.dxf.dimdsep = ord(',')

    # ------------------------------------------------------------------ ilkel
    def L(self, a, b, lay=EQ, z=1, w=0.0):
        assert lay is not None, 'elektrik kalemi (kablo/sinyal) çizilmez (R2)'
        self.G.append(dict(t='P', pts=[tuple(a), tuple(b)], lay=lay, z=z, closed=False, w=w))

    def PL(self, pts, lay=EQ, z=1, closed=False, w=0.0):
        assert lay is not None, 'elektrik kalemi (kablo/sinyal) çizilmez (R2)'
        if len(pts) > 1:
            self.G.append(dict(t='P', pts=[tuple(p) for p in pts], lay=lay, z=z, closed=closed, w=w))

    def RECT(self, x0, y0, x1, y1, lay=EQ, z=1, w=0.0):
        self.PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, z, True, w)

    def C(self, c, r, lay=EQ, z=1):
        self.G.append(dict(t='C', c=tuple(c), r=r, lay=lay, z=z))

    def ARC(self, c, r, a0, a1, lay=EQ, z=1, n=None):
        n = n or max(8, int(abs(a1 - a0) / 8))
        self.PL([(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
                 for i in range(n + 1)], lay, z)

    def RRECT(self, x0, y0, x1, y1, r, lay=EQ, z=1):
        pts = []
        for cx, cy, a in ((x1 - r, y0 + r, 270), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for i in range(5):
                t = math.radians(a + 90 * i / 4)
                pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        self.PL(pts, lay, z, True)

    def OCCLUDE(self, poly, z, mod='hepsi'):
        """z'den küçük z'li çizgileri bu çokgen içinde gizle (önde kalan nesne).
        mod: 'hepsi' | 'boru' (yalnız boruları keser: vana boşluğu) | 'boru_haric' (duvar geçişi: boru görünür kalır)"""
        self.OCC.append((poly if isinstance(poly, Polygon) else Polygon(poly), z, mod))

    def SOLID_OCC(self, x0, y0, x1, y1, z):
        self.OCCLUDE(sbox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), z)

    def HATCH(self, pts, lay=TR, z=1, pat='ANSI31', sc=None):
        self.HAT.append((pts, lay, z, pat, sc or self.olcek * 0.06))

    def SOLIDFILL(self, pts, lay=EQ, z=1):
        self.HAT.append((pts, lay, z, 'SOLID', 1))

    # ------------------------------------------------------------------ boru
    def boru(self, pts, lay, dn, z=2, kalin=None):
        """tek çizgi boru; kalem kalınlığı DN'e göre (1/25'te 1 cm = 0,4 mm)"""
        w = kalin if kalin is not None else (0.0 if dn <= 32 else min(2.0, 0.5 + dn / 150))
        w = w * self.olcek / 25
        self.PL(pts, lay, z, False, w)
        return pts

    def boru_occ(self, pts, dn, z):
        """önde kalan borunun arkasını örtmesi için gerçek dış çap bandı"""
        ls = LineString(pts)
        self.OCCLUDE(ls.buffer(DN_OD[dn] / 2 + 1.5, cap_style=2), z)

    # ------------------------------------------------------------------ vana / armatür (saf geometri blok)
    def vana(self, ad, p, rot=0.0, s=1.0, cap='', kes=True, z=5, sx=None, lay=VN):
        """ROTAS-SMB saf geometri sembolü (+X = boru/akış yönü). kes=True ise üzerindeki boru sembol boyunca kesilir."""
        name = RS.blok_tanimla(self.doc, ad)
        self.INS.append(dict(name=name, ad=ad, p=tuple(p), rot=rot, s=s, sx=sx if sx is not None else s, cap=cap, lay=lay))
        hl = VANA[ad] * abs(s)
        if kes and hl > 0:
            a = math.radians(rot)
            d = (math.cos(a) * hl, math.sin(a) * hl)
            self.OCCLUDE(LineString([(p[0] - d[0], p[1] - d[1]), (p[0] + d[0], p[1] + d[1])]).buffer(2.2, cap_style=2), 99, 'boru')

    # ------------------------------------------------------------------ yazı
    def T(self, x, y, s, h=None, al='BL', rot=0.0, lay=YZ, mask=True, w=0.85):
        h = h or self.th
        self.TXT.append(dict(x=x, y=y, s=s, h=h, al=al, rot=rot, lay=lay, mask=mask, w=w))

    def _tbox(self, t):
        tw = len(t['s']) * t['h'] * 0.62 * t['w'] + t['h'] * 0.3
        th = t['h'] * 1.45
        ax = {'L': 0, 'C': 0.5, 'R': 1}[t['al'][1]] if len(t['al']) == 2 else 0
        ay = {'B': 0, 'M': 0.5, 'T': 1}[t['al'][0]]
        x0, y0 = -ax * tw - t['h'] * 0.15, -ay * t['h'] - t['h'] * 0.25
        a = math.radians(t['rot']); ca, sa = math.cos(a), math.sin(a)
        pts = [(x0, y0), (x0 + tw, y0), (x0 + tw, y0 + th), (x0, y0 + th)]
        return [(t['x'] + px * ca - py * sa, t['y'] + px * sa + py * ca) for px, py in pts]

    def BALON(self, no, hedef, konum, r=None):
        """numara balonu + kılavuz çizgisi (hedefte nokta)"""
        r = r or self.th * 1.15
        self.BAL.append(dict(no=str(no), c=tuple(konum), r=r))
        dx, dy = hedef[0] - konum[0], hedef[1] - konum[1]
        d = math.hypot(dx, dy)
        if d > r + 0.5:
            a = (konum[0] + dx / d * r, konum[1] + dy / d * r)
            self.LEAD.append((a, tuple(hedef)))

    # ------------------------------------------------------------------ kot / ölçü
    def KOT(self, p, deger_cm, sag=True, yazi=None, lay=KT):
        """kot sembolü: ucu seviye çizgisine değen üçgen (yarısı dolu) + kot yazısı"""
        s = self.th * 0.9
        x, y = p
        self.G.append(dict(t='P', pts=[(x, y), (x - s * 0.6, y + s), (x + s * 0.6, y + s)], lay=lay, z=6, closed=True, w=0))
        self.HAT.append(([(x, y), (x, y + s), (x + s * 0.6, y + s)], lay, 6, 'SOLID', 1))
        L = s * 5.5 + len(yazi or '') * self.th * 0.5
        x1 = x + (L if sag else -L)
        self.G.append(dict(t='P', pts=[(x - s * 0.8 if sag else x + s * 0.8, y + s), (x1, y + s)], lay=lay, z=6, closed=False, w=0))
        txt = kot_s(deger_cm) + ((' ' + yazi) if yazi else '')
        self.T(x + s * 0.9 if sag else x - s * 0.9, y + s * 1.25, txt, self.th * 0.9, 'BL' if sag else 'BR', lay=lay)

    def OLCU(self, p1, p2, off, yon='h', txt=None):
        self.DIMS.append((p1, p2, off, yon, txt))

    def KIRIK(self, a, b, lay=BT, z=4):
        """kırık (kesme) çizgisi a->b"""
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy); ux, uy = dx / d, dy / d; nx, ny = -uy, ux
        m = (a[0] + dx / 2, a[1] + dy / 2); k = self.th * 0.8
        pts = [a, (m[0] - ux * k, m[1] - uy * k), (m[0] - ux * k * 0.4 + nx * k * 1.2, m[1] - uy * k * 0.4 + ny * k * 1.2),
               (m[0] + ux * k * 0.4 - nx * k * 1.2, m[1] + uy * k * 0.4 - ny * k * 1.2), (m[0] + ux * k, m[1] + uy * k), b]
        self.PL(pts, lay, z)

    # ------------------------------------------------------------------ tablo
    def tablo(self, x, y, baslik, satirlar, W=None):
        """cihaz listesi: NO | CİHAZ | ADET | TEKNİK ÖZELLİKLER (motor/yangin_pompa/cihaz_listesi.py tarzı)"""
        H, HB, HT = self.th, self.th * 1.15, self.th * 1.6
        W = W or [self.th * 4, self.th * 30, self.th * 5, self.th * 62]
        X = [x]
        for w in W:
            X.append(X[-1] + w)
        RH = H * 2.6; TH = HT * 2.2

        def sar(parcalar, gen):
            sat, cur = [], ''
            for p in parcalar:
                s = (cur + '  •  ' + p) if cur else p
                if len(s) * H * 0.62 * 0.85 > gen - H * 2 and cur:
                    sat.append(cur); cur = p
                else:
                    cur = s
            sat.append(cur)
            return sat
        rows = []
        for no, ad, adet, oz in satirlar:
            a_s = sar(ad.split(' | '), W[1]) if ' | ' in ad else [ad]
            rows.append((no, a_s, adet, sar(oz, W[3])))
        hts = [max(RH, H * 1.8 + max(len(t), len(a)) * H * 1.7) for _, a, _, t in rows]

        def box(x1, y1, x2, y2):
            self.G.append(dict(t='P', pts=[(x1, y1), (x2, y1), (x2, y2), (x1, y2)], lay=TB, z=6, closed=True, w=0))
        yy = y
        box(X[0], yy - TH, X[-1], yy)
        self.T((X[0] + X[-1]) / 2, yy - TH / 2, baslik, HT, 'MC', lay=BS, mask=False)
        yy -= TH
        for i, b in enumerate(['NO', 'CİHAZ', 'ADET', 'TEKNİK ÖZELLİKLER']):
            box(X[i], yy - RH, X[i + 1], yy)
            self.T((X[i] + X[i + 1]) / 2, yy - RH / 2, b, HB, 'MC', lay=BS, mask=False)
        yy -= RH
        for (no, ad, adet, t), h in zip(rows, hts):
            for i in range(4):
                box(X[i], yy - h, X[i + 1], yy)
            self.T((X[0] + X[1]) / 2, yy - h / 2, no, H, 'MC', lay=TB, mask=False)
            sp = H * 1.7
            for k, s in enumerate(ad):
                self.T(X[1] + H, yy - h / 2 + (len(ad) - 1) * sp / 2 - k * sp, s, H, 'ML', lay=TB, mask=False)
            self.T((X[2] + X[3]) / 2, yy - h / 2, str(adet), H, 'MC', lay=TB, mask=False)
            for k, s in enumerate(t):
                self.T(X[3] + H, yy - h / 2 + (len(t) - 1) * sp / 2 - k * sp, s, H, 'ML', lay=TB, mask=False)
            yy -= h
        self.G.append(dict(t='P', pts=[(X[0] - H, yy - H), (X[-1] + H, yy - H), (X[-1] + H, y + H), (X[0] - H, y + H)],
                           lay=CR, z=6, closed=True, w=0.6 * self.olcek / 25))
        return yy

    def notlar(self, x, y, baslik, satirlar, gen):
        H = self.th
        self.T(x, y, baslik, H * 1.3, 'TL', lay=BS, mask=False)
        yy = y - H * 2.6
        for s in satirlar:
            # sar
            kel, cur, out = s.split(' '), '', []
            for k in kel:
                t = (cur + ' ' + k) if cur else k
                if len(t) * H * 0.62 * 0.85 > gen and cur:
                    out.append(cur); cur = '   ' + k
                else:
                    cur = t
            out.append(cur)
            for o in out:
                self.T(x, yy, o, H, 'TL', lay=NT, mask=False)
                yy -= H * 1.7
            yy -= H * 0.4
        return yy

    # ------------------------------------------------------------------ çıktı
    def _write_geom(self):
        cache = {}

        def occ_for(z, lay=None):
            b = lay in BORU_LAY
            k = (z, b)
            if k not in cache:
                ps = [p for p, oz, m in self.OCC if oz > z and (m == 'hepsi' or (m == 'boru' and b) or (m == 'boru_haric' and not b))]
                cache[k] = unary_union(ps) if ps else None
            return cache[k]

        def add_ls(coords, lay, w):
            if len(coords) < 2:
                return
            e = self.msp.add_lwpolyline(coords, dxfattribs={'layer': lay})
            if w:
                e.dxf.const_width = w

        for g in self.G:
            U = occ_for(g['z'], g['lay'])
            if g['t'] == 'C':
                c, r = g['c'], g['r']
                circ = Point(c).buffer(r, 64).exterior
                if U is None or not circ.intersects(U):
                    self.msp.add_circle(c, r, dxfattribs={'layer': g['lay']})
                    continue
                geom = LineString(circ.coords).difference(U)
                w = 0
            else:
                pts = list(g['pts'])
                if g['closed']:
                    pts = pts + [pts[0]]
                ls = LineString(pts)
                if U is None or not ls.intersects(U):
                    e = self.msp.add_lwpolyline(g['pts'], close=g['closed'], dxfattribs={'layer': g['lay']})
                    if g['w']:
                        e.dxf.const_width = g['w']
                    continue
                geom = ls.difference(U)
                w = g['w']
            if geom.is_empty:
                continue
            parts = [geom] if geom.geom_type == 'LineString' else list(getattr(geom, 'geoms', []))
            for p in parts:
                if p.geom_type == 'LineString' and p.length > 0.05:
                    add_ls(list(p.coords), g['lay'], w)
        for pts, lay, z, pat, sc in self.HAT:
            U = occ_for(z, lay)
            poly = Polygon(pts)
            if U is not None and poly.intersects(U):
                poly = poly.difference(U)
            polys = [poly] if poly.geom_type == 'Polygon' else list(getattr(poly, 'geoms', []))
            for pg in polys:
                if pg.is_empty or pg.geom_type != 'Polygon' or pg.area < 0.5:
                    continue
                h = self.msp.add_hatch(color=256, dxfattribs={'layer': lay})
                if pat == 'SOLID':
                    h.set_solid_fill(color=256)
                else:
                    h.set_pattern_fill(pat, scale=sc)
                h.paths.add_polyline_path(list(pg.exterior.coords)[:-1], is_closed=True, flags=1)
                for hole in pg.interiors:
                    h.paths.add_polyline_path(list(hole.coords)[:-1], is_closed=True, flags=0)

    def _write_ins(self):
        for b in self.INS:
            r = self.msp.add_blockref(b['name'], b['p'], dxfattribs={'layer': b.get('lay', VN), 'rotation': b['rot'],
                                                                      'xscale': b['sx'], 'yscale': b['s']})
            b['ref'] = r

    def _write_text(self):
        for t in self.TXT:
            if t['mask']:
                self.msp.add_wipeout(self._tbox(t)).dxf.layer = MS
        for a, b in self.LEAD:
            self.msp.add_line(a, b, dxfattribs={'layer': NU})
            self.msp.add_circle(b, self.th * 0.15, dxfattribs={'layer': NU})
            h = self.msp.add_hatch(dxfattribs={'layer': NU}); h.set_solid_fill(color=256)
            h.paths.add_polyline_path([(b[0] + self.th * 0.15 * math.cos(i * math.pi / 6), b[1] + self.th * 0.15 * math.sin(i * math.pi / 6)) for i in range(12)], is_closed=True)
        for bl in self.BAL:
            pts = [(bl['c'][0] + bl['r'] * math.cos(i * math.pi / 12), bl['c'][1] + bl['r'] * math.sin(i * math.pi / 12)) for i in range(24)]
            self.msp.add_wipeout(pts).dxf.layer = MS
            self.msp.add_circle(bl['c'], bl['r'], dxfattribs={'layer': NU})
            t = self.msp.add_text(bl['no'], height=self.th * 0.95, dxfattribs={'layer': NU, 'style': 'ROTAS', 'width': 0.8})
            t.set_placement(bl['c'], align=TA.MIDDLE_CENTER)
        AL = {'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER, 'BR': TA.BOTTOM_RIGHT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER,
              'MR': TA.MIDDLE_RIGHT, 'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT}
        for t in self.TXT:
            e = self.msp.add_text(t['s'], height=t['h'], rotation=t['rot'], dxfattribs={'layer': t['lay'], 'style': 'ROTAS', 'width': t['w']})
            e.set_placement((t['x'], t['y']), align=AL[t['al']])
        for p1, p2, off, yon, txt in self.DIMS:
            if yon == 'h':
                base = (p1[0], max(p1[1], p2[1]) + off) if off > 0 else (p1[0], min(p1[1], p2[1]) + off)
                d = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=0, dimstyle='ROTAS-OLCU', text=txt or '<>',
                                            dxfattribs={'layer': OL})
            else:
                base = (max(p1[0], p2[0]) + off, p1[1]) if off > 0 else (min(p1[0], p2[0]) + off, p1[1])
                d = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=90, dimstyle='ROTAS-OLCU', text=txt or '<>',
                                            dxfattribs={'layer': OL})
            d.render()

    # ------------------------------------------------------------------ denetim
    def denetle(self):
        """yazı-yazı, yazı-balon, yazı-blok, balon-balon, kılavuz-kılavuz çakışmaları"""
        items = []
        for t in self.TXT:
            items.append(('Y:' + t['s'][:30], Polygon(self._tbox(t))))
        for b in self.BAL:
            items.append(('B:' + b['no'], Point(b['c']).buffer(b['r'] + 0.5)))
        from ezdxf import bbox as zb
        for b in self.INS:
            ext = zb.extents([b['ref']], fast=True)
            if ext.has_data:
                items.append(('K:' + b['name'], sbox(ext.extmin.x + 1, ext.extmin.y + 1, ext.extmax.x - 1, ext.extmax.y - 1)))
        n = 0
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                if a[0][0] == 'K' and b[0][0] == 'K':
                    continue
                if a[1].intersects(b[1]) and a[1].intersection(b[1]).area > 0.5:
                    self.uyari.append(f'çakışma: {a[0]} <-> {b[0]}'); n += 1
        # kılavuzlar birbirini ve balonları kesmesin
        ls = [LineString(l) for l in self.LEAD]
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                if ls[i].crosses(ls[j]):
                    self.uyari.append(f'kılavuz kesişmesi: {self.LEAD[i]} x {self.LEAD[j]}'); n += 1
            for t in self.TXT:
                if ls[i].intersects(Polygon(self._tbox(t))):
                    self.uyari.append(f'kılavuz yazıdan geçiyor: {t["s"][:25]}'); n += 1
            for b in self.BAL:
                if ls[i].distance(Point(b['c'])) < b['r'] - 0.5:
                    self.uyari.append(f'kılavuz balondan geçiyor: {b["no"]}'); n += 1
        # balon / yazı - çizim çizgileri (borular dahil; beton tarama ve tablo hariç)
        geo = []
        for g in self.G:
            if g['lay'] in (TB, CR, KT, BT, TR):
                continue
            if g['t'] == 'C':
                geo.append((g['lay'], Point(g['c']).buffer(g['r']).exterior))
            else:
                pts = list(g['pts']) + ([g['pts'][0]] if g['closed'] else [])
                geo.append((g['lay'], LineString(pts)))
        from shapely.strtree import STRtree
        tree = STRtree([q for _, q in geo])
        for b in self.BAL:
            P_ = Point(b['c']).buffer(b['r'])
            for i in tree.query(P_):
                if geo[i][1].intersects(P_):
                    self.uyari.append(f'balon {b["no"]} @({b["c"][0]:.0f},{b["c"][1]:.0f}) çizgi üstünde ({geo[i][0]})'); n += 1
                    break
        for t in self.TXT:
            if not t['mask'] or t['lay'] in (TB, BS, NT):
                continue
            P_ = Polygon(self._tbox(t)).buffer(-0.5)
            for i in tree.query(P_):
                if geo[i][0] not in BORU_LAY and geo[i][0] != SV and geo[i][1].intersects(P_):
                    self.uyari.append(f'yazı "{t["s"][:25]}" @({t["x"]:.0f},{t["y"]:.0f}) ekipman çizgisi üstünde ({geo[i][0]})'); n += 1
                    break
        return n

    def kaydet(self, yol):
        self._write_geom()
        self._write_ins()
        self._write_text()
        n = self.denetle()
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        self.doc.saveas(yol)
        return n
