# -*- coding: utf-8 -*-
"""DXF yardımcıları: ROTAS- katmanları, maskeli yazı, köprülü boru, çakışmasız etiket yeri."""
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import LineString, Point, box as sbox, Polygon
import geo

KAT = {  # ad: (renk, çizgi tipi)
    'ROTAS-ISITMA-GIDIS': (10, 'Continuous'), 'ROTAS-ISITMA-DONUS': (30, 'DASHED'), 'ROTAS-ISITMA-CAP': (41, 'Continuous'),
    'ROTAS-RADYATOR': (2, 'Continuous'), 'ROTAS-MAHAL': (2, 'Continuous'), 'ROTAS-MIMARI-TEMSILI': (8, 'Continuous'),
    'ROTAS-MIMARI-PENCERE': (4, 'Continuous'), 'ROTAS-YAZI': (7, 'Continuous'), 'ROTAS-BASLIK': (7, 'Continuous'),
    'ROTAS-SEMA': (8, 'Continuous'), 'ROTAS-KAT-BANDI': (8, 'Continuous'), 'ROTAS-TABLO': (7, 'Continuous'),
    'ROTAS-VANA': (1, 'Continuous'), 'ROTAS-CIHAZ': (135, 'Continuous'), 'ROTAS-KRITIK': (1, 'Continuous'),
    'ROTAS-MASKE': (7, 'Continuous'), 'ROTAS-DENEME': (1, 'Continuous'), 'ROTAS-PAFTA': (7, 'Continuous'),
    'ROTAS-ISITMA-KOLEKTOR': (6, 'Continuous'), 'ROTAS-ISITMA-SEMBOL': (1, 'Continuous'),
    'ROTAS-MIMARI-TEFRIS': (9, 'Continuous'), 'ROTAS-DETAY': (7, 'Continuous'),
}
GID, DON, CAPK = 'ROTAS-ISITMA-GIDIS', 'ROTAS-ISITMA-DONUS', 'ROTAS-ISITMA-CAP'
YAZI, MSK = 'ROTAS-YAZI', 'ROTAS-MASKE'


class Cizim:
    def __init__(self):
        self.doc = ezdxf.new('R2018', setup=True)
        self.doc.header['$INSUNITS'] = 5          # cm
        self.doc.header['$LTSCALE'] = 1.0
        self.doc.header['$PSLTSCALE'] = 0
        self.doc.header['$CELTSCALE'] = 1.0
        if 'ROTAS' not in self.doc.styles:
            self.doc.styles.add('ROTAS', font='arial.ttf')
        self.doc.set_wipeout_variables(frame=0)
        for n, (c, lt) in KAT.items():
            self.doc.layers.add(n, color=c, linetype=lt)
        self.msp = self.doc.modelspace()
        self.engel = []          # yazıların kaçınacağı geometri (boru çizgileri, semboller)
        self.yazilar = []        # yerleştirilmiş yazı kutuları

    # ------------------------------------------------------------ temel
    def pl(self, pts, kat, w=0.0, kapali=False, ltscale=None, engel=True):
        e = self.msp.add_lwpolyline([tuple(p[:2]) if len(p) < 5 else p for p in pts], close=kapali, dxfattribs={'layer': kat},
                                    format='xyseb' if pts and len(pts[0]) == 5 else 'xy')
        if w:
            e.dxf.const_width = w
        if ltscale:
            e.dxf.ltscale = ltscale
        if engel and len(pts) > 1:
            self.engel.append(LineString([tuple(p[:2]) for p in pts]))
        return e

    def cizgi(self, a, b, kat):
        return self.msp.add_line(a, b, dxfattribs={'layer': kat})

    def maske(self, pts):
        w = self.msp.add_wipeout([tuple(p) for p in pts], dxfattribs={'layer': MSK})
        w.dxf.layer = MSK              # 0 katmanında görünmez nesne bırakılmaz

    def kutu_yazi(self, p, s, h, al='MC', rot=0.0, w=0.85):
        tw = len(s) * h * 0.60 * w + h * 0.5
        th = h * 1.5
        ax = {'L': 0, 'C': 0.5, 'R': 1}[al[1]]
        ay = {'B': 0, 'M': 0.5, 'T': 1}[al[0]]
        x0 = -ax * tw - h * 0.25; y0 = -ay * h - h * 0.25
        a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
        q = [(x0, y0), (x0 + tw, y0), (x0 + tw, y0 + th), (x0, y0 + th)]
        return [(p[0] + x * ca - y * sa, p[1] + x * sa + y * ca) for x, y in q]

    def yazi(self, p, s, h=10.0, kat=YAZI, al='MC', rot=0.0, maske=True, w=0.85, renk=None, kaydet=True):
        k = self.kutu_yazi(p, s, h, al, rot, w)
        if maske:
            self.maske(k)
        if kaydet:
            self.yazilar.append(Polygon(k))
        A = {'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER, 'BR': TA.BOTTOM_RIGHT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER,
             'MR': TA.MIDDLE_RIGHT, 'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT}[al]
        t = self.msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': kat, 'style': 'ROTAS', 'width': w})
        if renk is not None:
            t.dxf.color = renk
        t.set_placement((p[0], p[1]), align=A)
        return t

    def once_ciz(self, ents):
        """bu nesneleri çizim sırasında en alta al (sembol/maske boruların üstünde kalsın)"""
        ro = dict(self.msp.get_redraw_order())
        for i, e in enumerate(ents):
            ro[e.dxf.handle] = format(0x10 + i, 'X')
        self.msp.set_redraw_order(ro)

    def bos_mu(self, poly, borular=True):
        if any(poly.intersects(q) for q in self.yazilar):
            return False
        if borular and any(poly.intersects(q) for q in self.engel):
            return False
        return True

    # ------------------------------------------------------------ blok
    def blok(self, anahtar, p, rot=0.0, sx=1.0, sy=1.0, kat='ROTAS-RADYATOR', ozn=None, ozn_h=None, ic=None, ozn_rot=None, ozn_konum=None, maske=False):
        if maske and ozn and ozn_konum:
            for t, q in ozn_konum.items():
                hh = (ozn_h or {}).get(t, 8.0)
                k = self.kutu_yazi(q, str(ozn.get(t, '')), hh, 'MC', 0.0, 1.0)
                self.maske(k); self.yazilar.append(Polygon(k))
        ad = geo.tanimla(self.doc, anahtar)          # R3: yalnız saf geometri ROTAS- blokları (MTY yok)
        return ekle(self.msp, ad, p, rot, sx, sy, kat, ozn, ozn_h, ozn_rot, ozn_konum)


def ekle(msp, ad, p, rot=0.0, sx=1.0, sy=1.0, katman='0', ozn=None, ozn_h=None, ozn_rot=None, ozn_konum=None):
    """INSERT + öznitelikler (ATTDEF konumundan; ozn_konum verilirse orta-orta hizalı elle konum)"""
    doc = msp.doc
    ins = msp.add_blockref(ad, (p[0], p[1]), dxfattribs={'layer': katman, 'rotation': rot, 'xscale': sx, 'yscale': sy})
    if ozn:
        m = ins.matrix44()
        for a in doc.blocks.get(ad).query('ATTDEF'):
            t = a.dxf.tag
            if t not in ozn:
                continue
            at = ins.add_attrib(t, str(ozn[t]), (0, 0))
            at.dxf.height = (ozn_h or {}).get(t, a.dxf.height * abs(sy))
            at.dxf.layer = katman
            if ozn_konum and t in ozn_konum:
                q = ozn_konum[t]
                at.dxf.insert = (q[0], q[1]); at.dxf.align_point = (q[0], q[1])
                at.dxf.halign = 1; at.dxf.valign = 2
            else:
                at.dxf.insert = m.transform(a.dxf.insert)
                if a.dxf.hasattr('align_point'):
                    at.dxf.align_point = m.transform(a.dxf.align_point)
                at.dxf.halign = a.dxf.get('halign', 0); at.dxf.valign = a.dxf.get('valign', 0)
            at.dxf.rotation = (ozn_rot if ozn_rot is not None else rot + a.dxf.get('rotation', 0))
            if 'ROTAS' in doc.styles:
                at.dxf.style = 'ROTAS'
    return ins


# ------------------------------------------------------------------ köprü (R3: kullanılmaz; yalnız eski uyum için)
def kopru_ekle(pts, kesenler, r=4.0, haric=()):
    """pts: polyline noktaları; kesenler: LineString listesi. Kesişme noktalarında yarım daire (bulge) köprü.
    Dönüş: [(x, y, 0, 0, bulge)] (LWPOLYLINE xyseb)"""
    out = []
    n = len(pts)
    for i in range(n - 1):
        a, b = pts[i], pts[i + 1]
        seg = LineString([a, b])
        L = seg.length
        out.append([a[0], a[1], 0, 0, 0.0])
        if L < 1e-9:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        ts = []
        for k in kesenler:
            if not seg.intersects(k):
                continue
            g = seg.intersection(k)
            for q in (getattr(g, 'geoms', None) or [g]):
                if q.geom_type != 'Point':
                    continue
                t = seg.project(q)
                if t < r + 0.5 or t > L - r - 0.5:
                    continue
                if any(Point(q.x, q.y).distance(Point(h)) < 0.5 for h in haric):
                    continue
                ts.append(t)
        ts = sorted(set(round(t, 3) for t in ts))
        birlesik = []
        for t in ts:
            if birlesik and t - birlesik[-1][1] < 2 * r + 1:
                birlesik[-1][1] = t
            else:
                birlesik.append([t, t])
        for t0, t1 in birlesik:
            s0 = t0 - r; s1 = t1 + r
            p0 = (a[0] + ux * s0, a[1] + uy * s0); p1 = (a[0] + ux * s1, a[1] + uy * s1)
            out.append([p0[0], p0[1], 0, 0, -1.0])     # yay (sağa/sola seçim çağıranda)
            out.append([p1[0], p1[1], 0, 0, 0.0])
    out.append([pts[-1][0], pts[-1][1], 0, 0, 0.0])
    return out


def yay_noktalari(p0, p1, bulge, n=8):
    """bulge yayının ara noktaları (çakışma denetimi için)"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    c = math.hypot(dx, dy)
    if c < 1e-9:
        return [p0, p1]
    th = 4 * math.atan(bulge)
    R = c / (2 * math.sin(th / 2))
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    nx, ny = -dy / c, dx / c
    d = R * math.cos(th / 2)
    cx, cy = mx + nx * d, my + ny * d
    a0 = math.atan2(p0[1] - cy, p0[0] - cx)
    return [(cx + abs(R) * math.cos(a0 + th * i / n), cy + abs(R) * math.sin(a0 + th * i / n)) for i in range(n + 1)]


def kopru_yon(xyseb, digerleri):
    """her köprü yayı için, diğer borulara en uzak tarafı seç (bulge işareti)"""
    for i in range(len(xyseb) - 1):
        if xyseb[i][4] == 0:
            continue
        best = None
        kiris = LineString([xyseb[i][:2], xyseb[i + 1][:2]])
        uzak = [o for o in digerleri if not o.intersects(kiris)]
        for bg in (1.0, -1.0):
            pts = yay_noktalari(xyseb[i][:2], xyseb[i + 1][:2], bg)
            tepe = Point(pts[len(pts) // 2])
            d = min((tepe.distance(o) for o in uzak), default=99)
            if best is None or d > best[0]:
                best = (d, bg)
        xyseb[i][4] = best[1]
    return xyseb
