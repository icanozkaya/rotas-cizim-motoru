# -*- coding: utf-8 -*-
"""OBA yangın / duman tahliye çizimleri için ortak DXF yardımcıları (ROTAS- katmanları, saf geometri)."""
import math, os, sys, pickle, json
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(KOK, 'motor', 'deneme', 'sprinkler'))
import rotas_sembol as RS  # noqa

GEO = '/tmp/claude-0/oba/geo.pkl'
TXT = '/tmp/claude-0/oba/tx.json'
PLAN_PENCERE = (183500, 7500, 200500, 15800)

AL = {'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER, 'BR': TA.BOTTOM_RIGHT, 'ML': TA.MIDDLE_LEFT,
      'MC': TA.MIDDLE_CENTER, 'MR': TA.MIDDLE_RIGHT, 'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT}


def yeni_doc(katmanlar):
    doc = ezdxf.new('R2018', setup=True)
    doc.units = 5
    doc.header['$MEASUREMENT'] = 1
    doc.header['$INSUNITS'] = 5
    doc.header['$LTSCALE'] = 20
    if 'ROTAS' not in doc.styles:
        doc.styles.new('ROTAS', dxfattribs={'font': 'arial.ttf'})
    for ad, (renk, lt) in katmanlar.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk, linetype=lt)
    return doc


class C:
    def __init__(self, doc):
        self.doc = doc
        self.m = doc.modelspace()

    def T(self, x, y, s, h, al='BL', lay='ROTAS-YAZI', rot=0.0, w=0.85):
        t = self.m.add_text(s, height=h, dxfattribs={'layer': lay, 'style': 'ROTAS', 'rotation': rot, 'width': w})
        t.set_placement((x, y), align=AL[al])
        return t

    def L(self, p, q, lay, w=0.0):
        if w:
            return self.m.add_lwpolyline([p, q], dxfattribs={'layer': lay, 'const_width': w})
        return self.m.add_line(p, q, dxfattribs={'layer': lay})

    def PL(self, pts, lay, kapali=False, w=0.0):
        return self.m.add_lwpolyline(pts, close=kapali, dxfattribs={'layer': lay, 'const_width': w})

    def R(self, x0, y0, x1, y1, lay, w=0.0):
        return self.PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, True, w)

    def CI(self, c, r, lay):
        return self.m.add_circle(c, r, dxfattribs={'layer': lay})

    def HATCH(self, pts, lay, desen='ANSI31', olcek=10.0, renk=None):
        h = self.m.add_hatch(color=renk if renk is not None else 256, dxfattribs={'layer': lay})
        if desen == 'SOLID':
            h.set_solid_fill(color=renk if renk is not None else 256)
        else:
            h.set_pattern_fill(desen, scale=olcek)
        h.paths.add_polyline_path(pts, is_closed=True)
        return h

    def SMB(self, ad, x, y, aci=0.0, olcek=1.0, lay='ROTAS-YANGIN-SEMBOL'):
        return RS.ciz(self.m, ad, x, y, aci=aci, olcek=olcek, katman=lay)

    def tablo(self, x, y, basliklar, gen, satirlar, h=12.0, rh=None, lay='ROTAS-HESAP', baslik=None, hb=None):
        """sol üst (x,y). Dönüş alt y"""
        rh = rh or h * 2.2
        X = [x]
        for g in gen:
            X.append(X[-1] + g)
        yy = y
        if baslik:
            self.T(x, yy + h * 0.8, baslik, hb or h * 1.5, 'BL', lay + '-BASLIK')
        self.L((x, yy), (X[-1], yy), lay + '-CIZGI')
        for i, s in enumerate(basliklar):
            self.T((X[i] + X[i + 1]) / 2, yy - rh / 2, s, h * 0.9, 'MC', lay + '-BASLIK')
        yy -= rh
        self.L((x, yy), (X[-1], yy), lay + '-CIZGI')
        for r in satirlar:
            for i, s in enumerate(r):
                s = '' if s is None else str(s)
                if i == 0 or (len(s) > 12 and not s.replace(',', '').replace('.', '').replace('-', '').isdigit()):
                    self.T(X[i] + h * 0.4, yy - rh / 2, s, h, 'ML', lay + '-YAZI')
                else:
                    self.T((X[i] + X[i + 1]) / 2, yy - rh / 2, s, h, 'MC', lay + '-YAZI')
            yy -= rh
            self.L((x, yy), (X[-1], yy), lay + '-CIZGI')
        for xx in X:
            self.L((xx, y), (xx, yy), lay + '-CIZGI')
        return yy

    def notlar(self, x, y, baslik, satirlar, h=14.0, gen=2600, lay='ROTAS-NOT'):
        self.T(x, y, baslik, h * 1.5, 'BL', lay)
        yy = y - h * 2.2
        maxc = int(gen / (h * 0.72))
        for s in satirlar:
            parca, cur = [], ''
            for k in s.split(' '):
                if len(cur) + len(k) + 1 > maxc and cur:
                    parca.append(cur)
                    cur = '   ' + k
                else:
                    cur = (cur + ' ' + k) if cur else k
            parca.append(cur)
            for p in parca:
                self.T(x, yy, p, h, 'BL', lay)
                yy -= h * 1.7
        return yy


def tr(v, n=2):
    s = f'{v:,.{n}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def mimari_altlik(c, pencere=PLAN_PENCERE, haric=('Part', 'PartMark', 'TEC', 'SPRINKLER - TEXT')):
    """mimari zemin kat planını ROTAS-MIMARI katmanlarına (gri) kopyala; kolonlar ayrı katmanda kalır"""
    x0, y0, x1, y1 = pencere
    G = pickle.load(open(GEO, 'rb'))
    n = 0
    for it in G:
        lay = it[0]
        if lay in haric:
            continue
        p = it[2]
        if not all(x0 <= q[0] <= x1 and y0 <= q[1] <= y1 for q in p):
            continue
        hl = 'ROTAS-MIMARI-KOLON' if lay == 'KOLON' else 'ROTAS-MIMARI-AKS' if lay in ('S-GRID', 'AKS', 'AKSNO') else 'ROTAS-MIMARI'
        if it[1] == 'L':
            c.m.add_lwpolyline(p, dxfattribs={'layer': hl})
            n += 1
        elif it[1] == 'C':
            c.m.add_circle(p[0], it[3], dxfattribs={'layer': hl})
            n += 1
    for t in json.load(open(TXT)):
        if t[0] in haric:
            continue
        if x0 <= t[2] <= x1 and y0 <= t[3] <= y1:
            s = t[1].strip()
            if not s or '{' in s:
                continue
            lay = 'ROTAS-MIMARI-AKS' if t[0] == 'S-GRID' else 'ROTAS-MIMARI-YAZI'
            c.m.add_text(s, height=t[4], dxfattribs={'layer': lay, 'style': 'ROTAS', 'insert': (t[2], t[3])})
            n += 1
    return n


def import_dxf(c, yol, dx, dy):
    """başka DXF'in model alanını (bloklarıyla) taşıyarak ekle"""
    from ezdxf import xref
    kaynak = ezdxf.readfile(yol)
    once = {e.dxf.handle for e in c.m}
    xref.load_modelspace(kaynak, c.doc)
    for e in c.m:
        if e.dxf.handle not in once:
            try:
                e.translate(dx, dy, 0)
            except Exception:
                pass


def pafta_cerceve(c, x0, y0, x1, y1, baslik, olcek, lay='ROTAS-PAFTA', h=45):
    c.R(x0, y0, x1, y1, lay, 4)
    c.T(x0 + 40, y1 - 40, baslik, h, 'TL', lay)
    c.T(x0 + 40, y1 - 40 - h * 1.6, olcek, h * 0.7, 'TL', lay)
