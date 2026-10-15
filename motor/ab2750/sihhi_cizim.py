# -*- coding: utf-8 -*-
"""2750/7 SIHHİ — çizim altyapısı: belge, katmanlar, çizgi tipleri, saf geometri semboller (MTY YOK), yazı yardımcıları,
çakışma kaydı (yazı/sembol/hat), mimari altlık kopyası (döndürmeli yazılar)."""
import math
import os
import pickle
import re
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import LineString, Point, Polygon, box
from shapely.affinity import rotate as s_rotate
from shapely.ops import unary_union

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
sys.path.insert(0, os.path.join(BURASI, '..', 'sihhi2'))
sys.path.insert(0, os.path.join(BURASI, '..'))

STIL = 'ROTAS'
KAT = {
    'ROTAS-MIMARI': (8, 'Continuous', 13), 'ROTAS-MIMARI-KOLON': (8, 'Continuous', 18),
    'ROTAS-MIMARI-YAZI': (8, 'Continuous', 9),
    'ROTAS-PISSU': (6, 'Continuous', 30), 'ROTAS-PISSU-CAP': (211, 'Continuous', 13),
    'ROTAS-PISSU-KOLON': (211, 'Continuous', 30), 'ROTAS-PISSU-KOLONNO': (6, 'Continuous', 13),
    'ROTAS-SOGUKSU': (5, 'Continuous', 30), 'ROTAS-SICAKSU': (1, 'ROTAS-SICAK', 30),
    'ROTAS-SIRKULASYON': (31, 'ROTAS-SIRK', 30), 'ROTAS-TEMIZSU-CAP': (101, 'Continuous', 13),
    'ROTAS-TEMIZSU-KOLON': (5, 'Continuous', 25), 'ROTAS-SEBEKE': (5, 'DASHED', 35),
    'ROTAS-SAYAC-DOLABI': (1, 'Continuous', 25), 'ROTAS-VANA': (1, 'Continuous', 18),
    'ROTAS-ARMATUR-EK': (4, 'Continuous', 18), 'ROTAS-YER-SUZGECI': (6, 'Continuous', 18),
    'ROTAS-YAGMUR': (3, 'ROTAS-YAGMURH', 30), 'ROTAS-YAGMUR-NO': (3, 'Continuous', 13),
    'ROTAS-HAVALANDIRMA': (4, 'Continuous', 25), 'ROTAS-HAVALANDIRMA-YAZI': (41, 'Continuous', 9),
    'ROTAS-ROGAR': (5, 'Continuous', 25), 'ROTAS-ALTYAPI-PIS': (6, 'Continuous', 35), 'ROTAS-ALTYAPI-YAZI': (2, 'Continuous', 13),
    'ROTAS-POMPA': (1, 'Continuous', 25), 'ROTAS-KAZAN': (1, 'Continuous', 25),
    'ROTAS-SEMBOL-KILAVUZ': (9, 'Continuous', 9), 'ROTAS-PAFTA': (144, 'Continuous', 50),
    'ROTAS-PAFTA-YAZI': (7, 'Continuous', 35), 'ROTAS-NOT': (7, 'Continuous', 13),
    'ROTAS-HESAP-CERCEVE': (1, 'Continuous', 25), 'ROTAS-HESAP-YAZI': (7, 'Continuous', 13),
    'ROTAS-HESAP-TABLO': (7, 'Continuous', 13), 'ROTAS-LEJANT': (7, 'Continuous', 13),
    'ROTAS-DEPO': (11, 'Continuous', 30), 'ROTAS-YERLESIM-EK': (6, 'Continuous', 35),
}


def belge():
    doc = ezdxf.new('R2010', setup=True)
    doc.header['$INSUNITS'] = 5
    doc.header['$MEASUREMENT'] = 1
    doc.header['$LTSCALE'] = 1.0
    if STIL not in doc.styles:
        doc.styles.add(STIL, font='arial.ttf')
    lt = doc.linetypes
    if 'ROTAS-SICAK' not in lt:
        lt.add('ROTAS-SICAK', pattern=[18.75, 12.5, -6.25], description='SICAK SU __ __ __')
        lt.add('ROTAS-SIRK', pattern=[30.0, 15.0, -5.0, 3.0, -5.0, 3.0, -4.0], description='SIRKULASYON __ . . __')
        lt.add('ROTAS-YAGMURH', pattern=[40.0, 30.0, -4.0, 2.0, -4.0], description='YAGMUR ___ . ___')
    for ad, (renk, tip, lw) in KAT.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk, linetype=tip if tip in doc.linetypes else 'Continuous', lineweight=lw)
    semboller(doc)
    return doc


def katman(doc, ad, renk=7, tip='Continuous', lw=13):
    if ad not in doc.layers:
        doc.layers.add(ad, color=renk, linetype=tip, lineweight=lw)


# ====================================================================== semboller (blok, saf geometri)
def _hatch(b, pts, renk):
    h = b.add_hatch(color=renk)
    h.paths.add_polyline_path(pts, is_closed=True)


def semboller(doc):
    B = doc.blocks
    if 'ROTAS-PL-PIS-KOLON' in B:
        return
    b = B.new('ROTAS-PL-PIS-KOLON')            # pis su kolonu (planda): Ø20 içi dolu
    b.add_circle((0, 0), 10, dxfattribs={'color': 211})
    h = b.add_hatch(color=211)
    h.paths.add_edge_path().add_arc((0, 0), 10, 0, 360)
    b = B.new('ROTAS-PL-PIS-KOLON-GECIS')       # bu kattan geçen kolon (ıslak hacmi yok)
    b.add_circle((0, 0), 10, dxfattribs={'color': 211})
    b.add_line((-7, -7), (7, 7), dxfattribs={'color': 211})
    b.add_line((-7, 7), (7, -7), dxfattribs={'color': 211})
    b = B.new('ROTAS-PL-BALON')                 # kolon no balonu r 27,5 / 24,5
    b.add_circle((0, 0), 27.5, dxfattribs={'color': 1})
    b.add_circle((0, 0), 24.5, dxfattribs={'color': 1})
    b = B.new('ROTAS-PL-BALON-YAGMUR')
    b.add_circle((0, 0), 27.5, dxfattribs={'color': 3})
    b.add_circle((0, 0), 24.5, dxfattribs={'color': 3})
    b = B.new('ROTAS-PL-YER-SUZGECI')           # yer süzgeci: Ø16 + ızgara
    b.add_circle((0, 0), 8, dxfattribs={'color': 6})
    b.add_lwpolyline([(-5.6, -5.6), (5.6, -5.6), (5.6, 5.6), (-5.6, 5.6)], close=True, dxfattribs={'color': 6})
    for t in (-2.8, 0, 2.8):
        b.add_line((t, -5.6), (t, 5.6), dxfattribs={'color': 6})
    b = B.new('ROTAS-PL-BALKON-SUZGECI')        # balkon süzgeci (yağmur)
    b.add_lwpolyline([(-7, -7), (7, -7), (7, 7), (-7, 7)], close=True, dxfattribs={'color': 3})
    for t in (-3.5, 0, 3.5):
        b.add_line((t, -7), (t, 7), dxfattribs={'color': 3})
    b = B.new('ROTAS-PL-YAGMUR-INIS')           # yağmur iniş borusu Ø100 (plan)
    b.add_circle((0, 0), 5.5, dxfattribs={'color': 3})
    b.add_circle((0, 0), 3.5, dxfattribs={'color': 3})
    b = B.new('ROTAS-PL-ASPIRATOR')             # WC aspiratörü (tavan, Ø150 çıkış)
    b.add_lwpolyline([(-15, -15), (15, -15), (15, 15), (-15, 15)], close=True, dxfattribs={'color': 4})
    b.add_circle((0, 0), 11, dxfattribs={'color': 4})
    for a in (0, 120, 240):
        r = math.radians(a)
        b.add_line((0, 0), (10 * math.cos(r), 10 * math.sin(r)), dxfattribs={'color': 4})
        b.add_arc((5 * math.cos(r + 0.6), 5 * math.sin(r + 0.6)), 5, a + 30, a + 150, dxfattribs={'color': 4})
    b = B.new('ROTAS-PL-SAYAC')                 # su sayacı (plan / şema): kare + çapraz ok
    b.add_lwpolyline([(-6, -6), (6, -6), (6, 6), (-6, 6)], close=True, dxfattribs={'color': 1})
    b.add_line((-6, -6), (6, 6), dxfattribs={'color': 1})
    _hatch(b, [(6, 6), (2, 5), (5, 2)], 1)
    b = B.new('ROTAS-PL-VANA')                  # küresel vana (papyon + kol), eksen x
    _hatch(b, [(-8, -4), (0, 0), (-8, 4)], 8)
    _hatch(b, [(8, -4), (0, 0), (8, 4)], 8)
    b.add_lwpolyline([(-8, -4), (8, 4), (8, -4), (-8, 4)], close=True, dxfattribs={'color': 1})
    b.add_lwpolyline([(0, 0), (0, 8), (5, 8)], dxfattribs={'color': 1})
    b = B.new('ROTAS-PL-CEKVALF')
    b.add_lwpolyline([(-8, -4), (8, 4), (8, -4), (-8, 4)], close=True, dxfattribs={'color': 1})
    _hatch(b, [(8, -4), (0, 0), (8, 4)], 8)
    b.add_line((-4, 7), (6, 7), dxfattribs={'color': 1})
    b.add_lwpolyline([(3, 9), (6, 7), (3, 5)], dxfattribs={'color': 1})
    b = B.new('ROTAS-PL-PISLIK-TUTUCU')
    b.add_lwpolyline([(-8, -4), (8, 4), (8, -4), (-8, 4)], close=True, dxfattribs={'color': 1})
    b.add_line((0, 0), (4, -8), dxfattribs={'color': 1})
    b.add_line((2, -9), (6, -7), dxfattribs={'color': 1})
    b = B.new('ROTAS-PL-ROGAR')                 # rögar 70x70 (iç 56x56) — merkez
    b.add_lwpolyline([(-35, -35), (35, -35), (35, 35), (-35, 35)], close=True, dxfattribs={'color': 5})
    b.add_lwpolyline([(-28, -28), (28, -28), (28, 28), (-28, 28)], close=True, dxfattribs={'color': 2})
    b = B.new('ROTAS-PL-PB')                    # parsel bacası 80x80
    b.add_lwpolyline([(-40, -40), (40, -40), (40, 40), (-40, 40)], close=True, dxfattribs={'color': 5})
    b.add_lwpolyline([(-33, -33), (33, -33), (33, 33), (-33, 33)], close=True, dxfattribs={'color': 2})
    b.add_line((-33, -33), (33, 33), dxfattribs={'color': 2})
    b.add_line((-33, 33), (33, -33), dxfattribs={'color': 2})
    b = B.new('ROTAS-PL-POMPA')                 # dalgıç pompa (daire + üçgen)
    b.add_circle((0, 0), 14, dxfattribs={'color': 1})
    b.add_lwpolyline([(-10, -10), (14, 0), (-10, 10)], close=True, dxfattribs={'color': 1})
    b = B.new('ROTAS-PL-HAVALIK')               # çatıda pis su havalığı
    b.add_circle((0, 0), 10, dxfattribs={'color': 6})
    b.add_circle((0, 0), 16, dxfattribs={'color': 6})
    b = B.new('ROTAS-PL-CATI-FAN')              # çatı tipi fan
    b.add_circle((0, 0), 30, dxfattribs={'color': 4})
    b.add_circle((0, 0), 22, dxfattribs={'color': 4})
    for a in range(0, 360, 60):
        r = math.radians(a)
        b.add_line((0, 0), (22 * math.cos(r), 22 * math.sin(r)), dxfattribs={'color': 4})
    b = B.new('ROTAS-PL-BOYLER')                # boyler (plan): Ø110 daire + serpantin
    b.add_circle((0, 0), 55, dxfattribs={'color': 1})
    b.add_circle((0, 0), 50, dxfattribs={'color': 1})
    b.add_lwpolyline([(-30, -10), (-20, 10), (-10, -10), (0, 10), (10, -10), (20, 10), (30, -10)], dxfattribs={'color': 1})


def blok(msp, ad, p, kat, rot=0.0, olcek=1.0):
    return msp.add_blockref(ad, p, dxfattribs={'layer': kat, 'rotation': rot, 'xscale': olcek, 'yscale': olcek})


# ====================================================================== yazı ölçüsü
_FONT = {}


def yazi_gen(s, h, w=0.85):
    try:
        from ezdxf.fonts import fonts
        k = (round(h, 2), round(w, 2))
        if k not in _FONT:
            _FONT[k] = fonts.make_font('arial.ttf', h, w)
        return _FONT[k].text_width(str(s))
    except Exception:
        return len(str(s)) * h * 0.6 * w


def yazi(msp, s, p, h, kat, al='BL', rot=0.0, w=0.85, renk=None):
    e = msp.add_text(str(s), height=h, rotation=rot, dxfattribs={'layer': kat, 'style': STIL, 'width': w})
    if renk is not None:
        e.dxf.color = renk
    e.set_placement(p, align={'BL': TA.LEFT, 'BC': TA.CENTER, 'BR': TA.RIGHT, 'ML': TA.MIDDLE_LEFT,
                              'MC': TA.MIDDLE_CENTER, 'MR': TA.MIDDLE_RIGHT, 'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER,
                              'TR': TA.TOP_RIGHT}[al])
    return e


def yazi_kutusu(s, p, h, al='BL', rot=0.0, w=0.85, pay=1.5):
    """yazının (dönmüş) kutusu: shapely Polygon"""
    W = yazi_gen(s, h, w)
    dx = {'L': 0, 'C': -W / 2, 'R': -W}[al[1]]
    dy = {'B': -0.22 * h, 'M': -0.5 * h, 'T': -h}[al[0]]
    g = box(dx - pay, dy - pay, dx + W + pay, dy + h * 1.22 + pay)
    if rot:
        g = s_rotate(g, rot, origin=(0, 0))
    from shapely.affinity import translate
    return translate(g, p[0], p[1])


# ====================================================================== çakışma kaydı
class Engel:
    """ızgara kovası (60 cm) ile hızlı kesişim sorgusu"""

    def __init__(self, hucre=60.0):
        self.h = hucre
        self.kova = {}
        self.say = 0

    def _anahtar(self, g):
        x0, y0, x1, y1 = g.bounds
        h = self.h
        for i in range(int(math.floor(x0 / h)), int(math.floor(x1 / h)) + 1):
            for j in range(int(math.floor(y0 / h)), int(math.floor(y1 / h)) + 1):
                yield (i, j)

    def ekle(self, g, tur='x'):
        if g is None or g.is_empty:
            return
        for k in self._anahtar(g):
            self.kova.setdefault(k, []).append((g, tur))
        self.say += 1

    def carpar(self, g, haric=()):
        gor = set()
        for k in self._anahtar(g):
            for q, t in self.kova.get(k, ()):
                if id(q) in gor or t in haric:
                    continue
                gor.add(id(q))
                if q.intersects(g):
                    return (q, t)
        return None


# ====================================================================== mimari altlık (döndürmeli yazılar)
FL_PKL = '/tmp/claude-0/ab/mim.pkl'
_MIM = None


def _temiz(s):
    s = re.sub(r'\\[A-Za-z][^;]*;', '', s)
    s = s.replace('{', '').replace('}', '').replace('\\P', ' ').replace('%%c', 'Ø').replace('%%C', 'Ø')
    s = s.replace('%%d', '°').replace('%%p', '±')
    return s.strip()


def mimari_duz():
    """dxfparse blok/varlıklarından düz liste — yazı dönüşü ve hizası korunur.
    öğe: (tip, katman, veri) ; L ((x,y),(x,y)) ; P [pts] ; C (x,y,r) ; A (x,y,r,a0,a1) ; T (x, y, metin, h, rot, ha, va)"""
    global _MIM
    if _MIM is not None:
        return _MIM
    import dxfparse as DP
    blocks, ents = pickle.load(open(FL_PKL, 'rb'))[:2]
    out = []

    def xf(m, x, y):
        a, b, c, d, e, f = m
        return (a * x + b * y + c, d * x + e * y + f)

    def git(lst, m, derin, lay_over):
        for e in lst:
            t = e['_t']
            lay = e.get('layer', '0')
            if lay == '0' and lay_over:
                lay = lay_over
            if t == 'LINE':
                out.append(('L', lay, (xf(m, e.get('10', 0), e.get('20', 0)), xf(m, e.get('11', 0), e.get('21', 0)))))
            elif t in ('LWPOLYLINE', 'POLYLINE'):
                pts = [xf(m, *p) for p in e.get('pts', [])]
                if (e.get('flag', 0) & 1) and pts:
                    pts = pts + [pts[0]]
                if len(pts) > 1:
                    out.append(('P', lay, pts))
            elif t == 'CIRCLE':
                cx, cy = xf(m, e.get('10', 0), e.get('20', 0))
                s = math.hypot(m[0], m[3])
                out.append(('C', lay, (cx, cy, e.get('40', 0) * s)))
            elif t == 'ARC':
                r = e.get('40', 0)
                a0, a1 = math.radians(e.get('50', 0)), math.radians(e.get('51', 0))
                if a1 < a0:
                    a1 += 2 * math.pi
                n = max(4, int((a1 - a0) / 0.15))
                pts = [xf(m, e.get('10', 0) + r * math.cos(a0 + (a1 - a0) * i / n),
                          e.get('20', 0) + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
                out.append(('P', lay, pts))
            elif t in ('TEXT', 'MTEXT', 'ATTRIB'):
                ha, va = e.get('ha', 0), e.get('va', 0)
                if t == 'TEXT' and (ha or va) and '11' in e:
                    x, y = e['11'], e.get('21', 0)
                else:
                    x, y = e.get('10', 0), e.get('20', 0)
                    if t == 'MTEXT':
                        att = e.get('att', 1)
                        ha = (att - 1) % 3
                        va = 3 - (att - 1) // 3
                    else:
                        ha, va = 0, 0
                s = math.hypot(m[0], m[3])
                if t == 'MTEXT':
                    rot = math.degrees(e.get('50', 0)) + math.degrees(math.atan2(m[3], m[0]))
                else:
                    rot = e.get('50', 0) + math.degrees(math.atan2(m[3], m[0]))
                p = xf(m, x, y)
                out.append(('T', lay, (p[0], p[1], e.get('text', ''), e.get('40', 0) * s, rot, ha, va)))
            elif t == 'INSERT' and derin < 6:
                nm = e.get('name')
                if nm not in blocks:
                    continue
                base, sub = blocks[nm]
                sx, sy = e.get('41', 1.0), e.get('42', e.get('41', 1.0))
                r = math.radians(e.get('50', 0))
                cr, sr = math.cos(r), math.sin(r)
                local = (cr * sx, -sr * sy, e.get('10', 0), sr * sx, cr * sy, e.get('20', 0))
                local = DP.mul(local, (1, 0, -base[0], 0, 1, -base[1]))
                git(sub, DP.mul(m, local), derin + 1, lay)
    git(ents, (1, 0, 0, 0, 1, 0), 0, None)
    _MIM = out
    return out


HARIC_KATMAN = ('Araba', 'rtm-sembol balon', 'rtm-aks', 'DEFPOINTS', 'Defpoints')


def mimari_altlik(msp, pencere, dx=0.0, dy=0.0, engel=None, yazi_al=True, haric=HARIC_KATMAN, sadece=None):
    """pencere (x0, x1, y0, y1) içindeki mimari çizim -> ROTAS-MIMARI (betonarme ROTAS-MIMARI-KOLON); (dx, dy) öteleme.
    engel: Engel — mimari yazı kutuları eklenir. Dönüş: (çizgi sayısı, yazı sayısı)"""
    x0, x1, y0, y1 = pencere
    W = box(x0, y0, x1, y1)
    n = ny = 0

    def icinde(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    for t, lay, d in mimari_duz():
        if any(lay.startswith(h) for h in haric):
            continue
        if sadece and lay not in sadece:
            continue
        kat = 'ROTAS-MIMARI-KOLON' if lay == 'rtm-tas_betonarme' else 'ROTAS-MIMARI'
        if t == 'L':
            if icinde(d[0]) and icinde(d[1]):
                msp.add_line((d[0][0] + dx, d[0][1] + dy), (d[1][0] + dx, d[1][1] + dy), dxfattribs={'layer': kat})
                n += 1
        elif t == 'P':
            if all(icinde(p) for p in d):
                msp.add_lwpolyline([(p[0] + dx, p[1] + dy) for p in d], dxfattribs={'layer': kat})
                n += 1
            elif any(icinde(p) for p in d):
                g = LineString(d).intersection(W)
                for q in getattr(g, 'geoms', [g]):
                    if q.geom_type == 'LineString' and q.length > 0.5:
                        msp.add_lwpolyline([(p[0] + dx, p[1] + dy) for p in q.coords], dxfattribs={'layer': kat})
                        n += 1
        elif t == 'C':
            if icinde(d[:2]):
                msp.add_circle((d[0] + dx, d[1] + dy), d[2], dxfattribs={'layer': kat})
                n += 1
        elif t == 'T' and yazi_al:
            x, y, s, h, rot, ha, va = d
            if not icinde((x, y)) or h <= 0:
                continue
            s = _temiz(s)
            if not s:
                continue
            al = {0: 'B', 1: 'B', 2: 'M', 3: 'T'}[va] + {0: 'L', 1: 'C', 2: 'R'}.get(ha, 'L')
            if va == 0 and ha in (3, 4, 5):
                al = 'BL'
            e = yazi(msp, s, (x + dx, y + dy), h, 'ROTAS-MIMARI-YAZI', al, rot, w=1.0)
            ny += 1
            if engel is not None:
                engel.ekle(yazi_kutusu(s, (x + dx, y + dy), h, al, rot, 1.0, pay=1.0), 'mimyazi')
    return n, ny
