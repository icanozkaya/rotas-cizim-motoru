#!/usr/bin/env python3
"""sihhi2 — SIHHİ KAT PLANLARI (zemin, 1, 2) — new_block mimarisinden, SIFIRDAN.

    python3 motor/sihhi2/plan.py [--png]

Çıktı: proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf (AC1032, cm; kat paftaları yan yana, mimari ROTAS-MIMARI*)
       proje/denemeler/sihhi2/sihhi_model.json (MODEL.md)

Tarz: kullanıcının kendi çizimi (kutuphane/arastirma/SIHHI_ALTIN_REFERANS.md) + README (C)/(B) kuralları.
Ayrıntı ve kararlar: BENIOKU.md.
"""
import json
import math
import os
import sys
import time
import heapq
from collections import defaultdict

import numpy as np
import cv2
from scipy import ndimage as ndi
import ezdxf
from ezdxf.addons import Importer
from shapely import STRtree
from shapely.geometry import LineString, Point, Polygon, box, MultiLineString
from shapely.ops import unary_union, substring, nearest_points

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import mimari2 as M2  # noqa: E402
KOK = M2.KOK
sys.path.insert(0, KOK + '/motor/deneme/denetim')
import denetle as D  # noqa: E402

CIKIS = KOK + '/proje/denemeler/sihhi2'
CIKIS_DXF = CIKIS + '/NB_SIHHI_KAT_PLANLARI.dxf'
CIKIS_JSON = CIKIS + '/sihhi_model.json'
MIMARI_DXF = '/tmp/claude-0/uu/new_block_mimari.dxf'
TMP = '/tmp/claude-0/s2'

KATLAR = ['Z', '1', '2']
KAT_ADI = {'Z': 'ZEMİN KAT', '1': '1. KAT', '2': '2. KAT'}
PAFTA = {'Z': (252513.0, 254578.0), '1': (254578.0, 256617.0), '2': (256617.0, 258656.0)}
LEJANT_PAFTA = (258656.0, 260714.0)
PY0, PY1 = -444050.0, -441150.0

# ---- kullanıcı çizimi değerleri (SIHHI_ALTIN_REFERANS.md, MODEL.md)
SB = {'LV': 2, 'WC': 10, 'DUS': 7, 'EV': 4, 'CM': 4, 'BM': 4, 'YS': 2}
MB_S = {'LV': 0.75, 'WC': 0.5, 'DUS': 2.5, 'EV': 1.0, 'CM': 1.5, 'BM': 1.5, 'KOMBI': 0.5}   # soğuk
MB_H = {'LV': 0.75, 'DUS': 2.5, 'EV': 1.0}                                              # sıcak (kombiden)
D_DUVAR = 4.0          # pis su toplama hattı / kolon: duvar yüzünden (≤ 9; kullanıcı 1–8)
O_SICAK = 5.0          # sıcak–soğuk paralel aralık
ETIKET_H = 10.0

KATMAN = {  # ad: (renk, çizgi tipi, kalınlık)
    'ROTAS-MIMARI': (8, 'Continuous', 13), 'ROTAS-MIMARI-YAZI': (8, 'Continuous', 13),
    'ROTAS-SIHHI-PIS-SU': (6, 'ROTAS_PISSU', 30), 'ROTAS-SIHHI-SOGUK-SU': (5, 'Continuous', 30),
    'ROTAS-SIHHI-SICAK-SU': (1, 'ROTAS_BASMA', 30), 'ROTAS-SIHHI-YAGMUR': (3, 'ROTAS_YAGMUR', 30),
    'ROTAS-SIHHI-PIS-SU-CAP': (211, 'Continuous', 18), 'ROTAS-SIHHI-TEMIZ-SU-CAP': (101, 'Continuous', 18),
    'ROTAS-SIHHI-KOLON-NO': (1, 'Continuous', 18), 'ROTAS-SIHHI-YAGMUR-NO': (3, 'Continuous', 18),
    'ROTAS-SIHHI-SEMBOL': (1, 'Continuous', 18), 'ROTAS-SIHHI-CIHAZ-YAZI': (1, 'Continuous', 13),
    'ROTAS-SIHHI-HAVALANDIRMA-YAZI': (30, 'Continuous', 9), 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL': (30, 'Continuous', 13),
    'ROTAS-SEMBOL-KILAVUZ': (8, 'Continuous', 9), 'ROTAS-PAFTA': (144, 'Continuous', 35),
    'ROTAS-PAFTA-YAZI': (8, 'Continuous', 25), 'ROTAS-LEJANT': (7, 'Continuous', 18),
}
L_PIS, L_SOG, L_SIC, L_YAG = 'ROTAS-SIHHI-PIS-SU', 'ROTAS-SIHHI-SOGUK-SU', 'ROTAS-SIHHI-SICAK-SU', 'ROTAS-SIHHI-YAGMUR'
L_PCAP, L_TCAP = 'ROTAS-SIHHI-PIS-SU-CAP', 'ROTAS-SIHHI-TEMIZ-SU-CAP'
L_KIL = 'ROTAS-SEMBOL-KILAVUZ'


def log(*a):
    print(*a, flush=True)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def birim(a, b):
    L = dist(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 1e-9 else (1.0, 0.0)


def fmt_mb(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return s + ' MB'


def inc(mb):
    if mb <= 1.0:
        return '1/2"'
    if mb <= 2.5:
        return '3/4"'
    if mb <= 8.5:
        return '1"'
    if mb <= 12.0:
        return '1 1/4"'
    return '1 1/2"'


def pis_cap(sb, wc):
    if wc:
        return 'Ø100'
    if sb <= 8:
        return 'Ø50'
    if sb <= 16:
        return 'Ø70'
    return 'Ø100'


def temiz(pts):
    """ardışık eş / doğrusal noktaları at"""
    out = []
    for p in pts:
        p = (float(p[0]), float(p[1]))
        if out and dist(out[-1], p) < 0.5:
            continue
        out.append(p)
    i = 1
    while i < len(out) - 1:
        a, b, c = out[i - 1], out[i], out[i + 1]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) < 1e-6 * max(1.0, dist(a, b) * dist(b, c)):
            out.pop(i)
        else:
            i += 1
    return out


# ====================================================================== ÇAKIŞMA MOTORU
class Engel:
    """etiket yerleştirme engelleri: alan (yazı / sembol kutusu) + çizgi (boru, kılavuz)"""

    def __init__(self):
        self.alan, self.cizgi = [], []
        self._ta = self._tc = None
        self._na = self._nc = 0

    def ekle_alan(self, g):
        if g is not None and not g.is_empty:
            self.alan.append(g)

    def ekle_cizgi(self, g):
        if g is not None and not g.is_empty:
            self.cizgi.append(g)

    def _agac(self):
        if self._ta is None or len(self.alan) - self._na > 40:
            self._ta, self._na = STRtree(self.alan) if self.alan else None, len(self.alan)
        if self._tc is None or len(self.cizgi) - self._nc > 40:
            self._tc, self._nc = STRtree(self.cizgi) if self.cizgi else None, len(self.cizgi)

    def carpar(self, pg, alan_tol=0.05, cizgi_tol=0.3, haric=()):
        self._agac()
        ad = [self.alan[i] for i in (self._ta.query(pg) if self._ta is not None else [])] + self.alan[self._na:]
        for g in ad:
            if any(g is h for h in haric):
                continue
            if g.intersects(pg) and g.intersection(pg).area > alan_tol:
                return True
        cd = [self.cizgi[i] for i in (self._tc.query(pg) if self._tc is not None else [])] + self.cizgi[self._nc:]
        for g in cd:
            if any(g is h for h in haric):
                continue
            if g.intersects(pg):
                x = g.intersection(pg)
                if x.length > cizgi_tol or (x.length == 0 and not x.is_empty and pg.buffer(-0.3).intersects(g)):
                    return True
        return False


# ====================================================================== DXF HAZIRLIK
def belge():
    doc = ezdxf.new('R2018', setup=False)
    doc.header['$INSUNITS'] = 5          # cm
    doc.header['$LTSCALE'] = 1.0
    doc.header['$MEASUREMENT'] = 1
    lts = doc.linetypes
    if 'Continuous' not in lts:
        lts.add('Continuous', pattern=[0.0], description='Solid')
    lts.add('ROTAS_PISSU', pattern=[45.0, 25.0, -6.0, 0.0, -6.0, 2.0, -6.0], description='PIS SU ---- . - ----')
    lts.add('ROTAS_BASMA', pattern=[18.75, 12.5, -6.25], description='SICAK SU - - - -')
    lts.add('ROTAS_YAGMUR', pattern=[45.0, 30.0, -6.0, 0.0, -9.0], description='YAGMUR ---- . ----')
    for ad, (renk, lt, lw) in KATMAN.items():
        doc.layers.add(ad, color=renk, linetype=lt, lineweight=lw)
    if 'ROTAS-YAZI' not in doc.styles:
        doc.styles.add('ROTAS-YAZI', font='arial.ttf')
    bloklar(doc)
    return doc


def bloklar(doc):
    B = doc.blocks
    # pis su kolonu (içi dolu daire Ø20 + kelepçe) — referans: STM-PISSU-KOLON r 10
    b = B.new('ROTAS-S2-PIS-KOLON')
    b.add_circle((0, 0), 7.0, dxfattribs={'color': 6})
    h = b.add_hatch(color=6)
    h.paths.add_edge_path().add_arc((0, 0), 7.0, 0, 360)
    b.add_circle((0, 0), 10.0, dxfattribs={'color': 30})
    for s in (-1, 1):
        b.add_line((s * 10, 0), (s * 14, 0), dxfattribs={'color': 30})
        b.add_lwpolyline([(s * 14, -3), (s * 14, 3)], dxfattribs={'color': 1})
    # kolon numara balonu (r 27,5 / 24,5, yazı h 20)
    for ad, renk_yazi in (('ROTAS-S2-KOLON-NO', 6), ('ROTAS-S2-KOLON-NO-YAGMUR', 3)):
        b = B.new(ad)
        b.add_circle((0, 0), 27.5, dxfattribs={'color': 1})
        b.add_circle((0, 0), 24.5, dxfattribs={'color': 1})
        b.add_attdef('NO', (0, 0), dxfattribs={'height': 20.0, 'color': renk_yazi, 'style': 'ROTAS-YAZI',
                                                'halign': 1, 'valign': 2, 'width': 0.8}).set_placement(
            (0, 0), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    # yağmur inişi (plan): çift daire
    b = B.new('ROTAS-S2-KOLON-YAGMUR')
    b.add_circle((0, 0), 5.0, dxfattribs={'color': 3})
    b.add_circle((0, 0), 8.0, dxfattribs={'color': 3})
    # yer süzgeci 15x15 (ızgara)
    b = B.new('ROTAS-S2-YER-SUZGECI')
    b.add_lwpolyline([(-7.5, -7.5), (7.5, -7.5), (7.5, 7.5), (-7.5, 7.5)], close=True)
    b.add_lwpolyline([(-5.5, -5.5), (5.5, -5.5), (5.5, 5.5), (-5.5, 5.5)], close=True)
    for t in (-3, 0, 3):
        b.add_line((t, -5.5), (t, 5.5))
        b.add_line((-5.5, t), (5.5, t))
    b.add_circle((0, 0), 2.0)
    # balkon süzgeci (yağmur hattına)
    b = B.new('ROTAS-S2-BALKON-SUZGECI')
    b.add_lwpolyline([(-7.5, -7.5), (7.5, -7.5), (7.5, 7.5), (-7.5, 7.5)], close=True)
    for t in (-4.5, -1.5, 1.5, 4.5):
        b.add_line((t, -6), (t, 6))
    b.add_circle((0, 0), 2.0)
    # küresel vana (armatür ucu, ara musluk)
    b = B.new('ROTAS-S2-KURESEL-VANA')
    b.add_lwpolyline([(-4, -2.5), (4, 2.5), (4, -2.5), (-4, 2.5)], close=True)
    b.add_circle((0, 0), 1.2)
    # temiz su daire girişi işareti (r 2 + ok)
    b = B.new('ROTAS-S2-TEMIZ-GIRIS')
    b.add_circle((0, 0), 2.0)
    b.add_circle((0, 0), 4.0)
    # WC aspiratörü (plan)
    b = B.new('ROTAS-S2-ASPIRATOR')
    b.add_lwpolyline([(-12, -12), (12, -12), (12, 12), (-12, 12)], close=True)
    b.add_circle((0, 0), 9.0)
    for a in (0, 90, 180, 270):
        r = math.radians(a)
        b.add_line((0, 0), (8 * math.cos(r), 8 * math.sin(r)))
        b.add_arc((4 * math.cos(r + 0.6), 4 * math.sin(r + 0.6)), 4.0, a + 20, a + 120)
    # EK armatür (mimaride olmayan ÇM / BM): 60x60
    b = B.new('ROTAS-S2-MAKINE-EK')
    b.add_lwpolyline([(-27, -27), (27, -27), (27, 27), (-27, 27)], close=True)
    b.add_circle((0, 0), 17.0)
    # pis su çap etiketi (kanca + "Ø50" / "2 SB"); U: yazı hattın üstünde, A: altında
    for ad, s in (('ROTAS-S2-PS-CAP-U', 1), ('ROTAS-S2-PS-CAP-A', -1)):
        b = B.new(ad)
        b.add_line((0, 0), (0, 16 * s))
        b.add_line((0, 16 * s), (34, 16 * s))
        ycap = 18.0 if s > 0 else -14.0
        ysb = 4.0 if s > 0 else -28.0
        b.add_attdef('CAP', (2, ycap), dxfattribs={'height': ETIKET_H, 'style': 'ROTAS-YAZI', 'width': 0.8})
        b.add_attdef('SB', (2, ysb), dxfattribs={'height': ETIKET_H, 'style': 'ROTAS-YAZI', 'width': 0.8})
    # temiz su etiketi (4 / 2 satır, yatay, satır aralığı 15)
    b = B.new('ROTAS-S2-TS-CAP4')
    for i, t in enumerate(('C1', 'M1', 'C2', 'M2')):
        b.add_attdef(t, (0, 45 - 15 * i), dxfattribs={'height': ETIKET_H, 'style': 'ROTAS-YAZI', 'width': 0.8})
    b = B.new('ROTAS-S2-TS-CAP2')
    for i, t in enumerate(('C1', 'M1')):
        b.add_attdef(t, (0, 15 - 15 * i), dxfattribs={'height': ETIKET_H, 'style': 'ROTAS-YAZI', 'width': 0.8})


def ekle_insert(msp, ad, p, katman, rot=0.0, olcek=1.0, attr=None):
    e = msp.add_blockref(ad, p, dxfattribs={'layer': katman, 'rotation': rot, 'xscale': olcek, 'yscale': olcek})
    if attr:
        e.add_auto_attribs(attr)
    return e


def yazi_kutulari(e):
    """INSERT'in görünür öznitelikleri + TEXT/MTEXT kutuları (kontrolörle aynı ölçü: denetle.yazi_poligonu)"""
    out = []
    if e.dxftype() == 'INSERT':
        for a in e.attribs:
            pg = D.yazi_poligonu(a)
            if pg is not None and pg.is_valid:
                out.append(pg)
    elif e.dxftype() == 'MTEXT':          # kontrolör: mimari MTEXT -> yazi_kutusu, diğer -> yazi_poligonu; ikisi de
        for pg in (D.yazi_kutusu(e), D.yazi_poligonu(e)):
            if pg is not None and pg.is_valid:
                out.append(pg)
    else:
        pg = D.yazi_poligonu(e)
        if pg is not None:
            out.append(pg)
    return out


# ====================================================================== MİMARİ ALTLIK
def mimari_kopyala(doc, eng):
    t0 = time.time()
    if not os.path.exists(MIMARI_DXF):
        M2.kayitlar()
    src = ezdxf.readfile(MIMARI_DXF)
    smsp = src.modelspace()
    msp = doc.modelspace()
    sec = []
    for e in smsp:
        if e.dxf.layer != 'MKDU0' or e.dxftype() == 'INSERT':
            continue
        try:
            if e.dxftype() in ('TEXT', 'MTEXT'):
                p = e.dxf.insert
                xs, ys = [p[0]], [p[1]]
            elif e.dxftype() == 'LINE':
                xs, ys = [e.dxf.start[0], e.dxf.end[0]], [e.dxf.start[1], e.dxf.end[1]]
            elif e.dxftype() in ('CIRCLE', 'ARC'):
                c = e.dxf.center
                xs, ys = [c[0]], [c[1]]
            elif e.dxftype() == 'LWPOLYLINE':
                ps = list(e.get_points('xy'))
                xs, ys = [q[0] for q in ps], [q[1] for q in ps]
            elif e.dxftype() == 'HATCH':
                xs, ys = [], []
                for pth in e.paths:
                    for v in getattr(pth, 'vertices', []):
                        xs.append(v[0]); ys.append(v[1])
                    for ed in getattr(pth, 'edges', []):
                        if hasattr(ed, 'start'):
                            xs.append(ed.start[0]); ys.append(ed.start[1])
                if not xs:
                    continue
            else:
                continue
        except Exception:
            continue
        if not (PY0 < min(ys) and max(ys) < PY1):
            continue
        if e.dxftype() in ('TEXT', 'MTEXT'):
            tx = (e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()).upper()
            if 'PLANI' in tx and 'ÖLÇEK' in tx:          # kullanıcının pafta başlığı: bizim başlığımız yazılır
                continue
        for k, (x0, x1) in PAFTA.items():
            if x0 < min(xs) and max(xs) < x1:
                sec.append(e)
                break
    n0 = len(msp)
    imp = Importer(src, doc)
    imp.import_entities(sec, target_layout=msp)
    imp.finalize()
    yeni = list(msp)[n0:]
    for e in yeni:
        if e.dxftype() in ('TEXT', 'MTEXT'):
            e.dxf.layer = 'ROTAS-MIMARI-YAZI'
            for pg in yazi_kutulari(e):
                eng.ekle_alan(pg)
        else:
            e.dxf.layer = 'ROTAS-MIMARI'
        e.dxf.color = 256
    # içe aktarılan katman MKDU0 ve MTY adlı stilleri temizle
    for ad in ('MKDU0',):
        if ad in doc.layers:
            try:
                doc.layers.remove(ad)
            except Exception:
                pass
    log('mimari altlık: %d varlık (%.1f s)' % (len(yeni), time.time() - t0))
    return yeni


# ====================================================================== PİS SU
def duzgun(poly):
    """armatür çıkıntıları / nişler (< 36 cm) temizlenmiş, dik açılı mahal poligonu"""
    g = poly.buffer(18, join_style=2, mitre_limit=3.0).buffer(-18, join_style=2, mitre_limit=3.0)
    g = g.buffer(-10, join_style=2, mitre_limit=3.0).buffer(10, join_style=2, mitre_limit=3.0)
    if g.is_empty:
        return poly
    if g.geom_type == 'MultiPolygon':
        g = max(g.geoms, key=lambda q: q.area)
    return orto(Polygon(g.exterior).simplify(2.0))


def orto(pg, tol=7.0):
    """eksene ±tol° yakın kenarları tam yatay/düşey yapar (raster kontur eğikliği)"""
    cs = [list(c) for c in pg.exterior.coords][:-1]
    n = len(cs)
    if n < 4:
        return pg
    for _ in range(2):
        for i in range(n):
            a, b = cs[i], cs[(i + 1) % n]
            dx, dy = b[0] - a[0], b[1] - a[1]
            if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                continue
            ang = abs(math.degrees(math.atan2(dy, dx))) % 180
            if min(ang, 180 - ang) <= tol:
                m = (a[1] + b[1]) / 2
                a[1] = b[1] = m
            elif abs(ang - 90) <= tol:
                m = (a[0] + b[0]) / 2
                a[0] = b[0] = m
    q = Polygon(cs).buffer(0)
    if q.is_empty or q.geom_type != 'Polygon' or abs(q.area - pg.area) > 0.05 * pg.area:
        return pg
    return q


def halka(poly, d=D_DUVAR):
    poly = duzgun(poly)
    g = poly.buffer(-d, join_style=2, mitre_limit=3.0)
    if g.is_empty:
        g = poly.buffer(-d / 2, join_style=2, mitre_limit=3.0)
    if g.geom_type == 'MultiPolygon':
        g = max(g.geoms, key=lambda q: q.area)
    g = g.simplify(1.5)
    return g


def kose_aci(a, b, c):
    """b köşesinde iç açı (derece) — saat yönü tersine halka için dışbükey < 180"""
    u, v = birim(b, a), birim(b, c)
    cr = u[0] * v[1] - u[1] * v[0]
    ang = math.degrees(math.atan2(abs(cr), u[0] * v[0] + u[1] * v[1]))
    return ang, cr


def yay_mesafesi(ring, s0, s1):
    L = ring.length
    d = (s1 - s0) % L
    return d, L - d


def pah_45(pts, h=None):
    """köşelerde 45° pah; h verilmezse parça boyuna göre 8–20 cm (uzun kolda yol kısalır)"""
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        u1, u2 = birim(a, b), birim(b, c)
        if h is None:
            h_ = max(8.0, min(20.0, dist(a, b) / 3.0, dist(b, c) / 3.0))
        else:
            h_ = h
        if abs(u1[0] * u2[0] + u1[1] * u2[1]) < 0.05 and dist(a, b) > h_ and dist(b, c) > h_:
            out += [(b[0] - u1[0] * h_, b[1] - u1[1] * h_), (b[0] + u2[0] * h_, b[1] + u2[1] * h_)]
        else:
            out.append(b)
    return temiz(out + [pts[-1]])


def oktal(pts, tol=3.0):
    """0/45/90 dışındaki parçaları 45° + eksen parçasına böler (kontrolör T02: açı {0,45,90})"""
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        ang = math.degrees(math.atan2(abs(dy), abs(dx)))
        if L < 4.0 or min(abs(ang - 0), abs(ang - 45), abs(ang - 90)) <= tol:
            out.append(b)
            continue
        m = min(abs(dx), abs(dy))
        sx, sy = math.copysign(1, dx), math.copysign(1, dy)
        out.append((a[0] + sx * m, a[1] + sy * m))
        out.append(b)
    return temiz(out)


def yay_parca(ring, s0, s1, yon):
    """halka üzerinde s0'dan s1'e (yon +1 / -1) nokta listesi"""
    L = ring.length
    cs = list(ring.coords)[:-1]
    ss = [ring.project(Point(c)) for c in cs]
    pts = [tuple(ring.interpolate(s0).coords[0])]
    if yon > 0:
        d = (s1 - s0) % L
        ara = sorted(((s - s0) % L, c) for s, c in zip(ss, cs) if 1e-6 < (s - s0) % L < d - 1e-6)
    else:
        d = (s0 - s1) % L
        ara = sorted(((s0 - s) % L, c) for s, c in zip(ss, cs) if 1e-6 < (s0 - s) % L < d - 1e-6)
    pts += [c for _, c in ara]
    pts.append(tuple(ring.interpolate(s1).coords[0]))
    return temiz(pts)


class PisOda:
    """bir ıslak hacmin pis su ağı: kolon, kollar (duvar dibi), branşmanlar"""

    def __init__(self, oda, armaturler):
        self.oda = oda
        self.fx = armaturler
        self.kolon = None


def pis_su_oda(K, oda, fx, kolon_onceki, yasak):
    """iki halka denenir: (1) eski mahal poligonu (mutfakta tezgâh altı +22), (2) armatür çentikleri kapatılmış poligon
    (mutfakta tezgâh dahil, duvar dibine kadar). Doğrulanan en iyi puanlı sonuç."""
    sonuclar = []
    for p_ in _pis_poligonlar(K, oda):
        r_ = _pis_su_halka(K, oda, fx, kolon_onceki, yasak, p_)
        if r_ is not None:
            sonuclar.append(r_)
    if not sonuclar:
        return None
    iyi = [r_ for r_ in sonuclar if not r_.get('dogrulanmadi')]
    return min(iyi or sonuclar, key=lambda r_: r_['puan'])


def _pis_poligonlar(K, oda):
    poly = oda['poly']
    kb = getattr(K, 'kb', None)
    if kb is not None and oda['tip'] == 'mutfak':
        # tezgâh altı: kontrolörün mutfak serbest alanı 22 cm büyütülür (pis su tezgâh dolabı içinden), duvarlarla kırpılır
        ser = [r['poly'] for r in kb['rooms'] if r['islak'] and r['poly'].intersects(poly)
               and r['poly'].intersection(poly).area > 0.3 * r['poly'].area]
        if ser:
            yeni = unary_union([q.buffer(22, join_style=2) for q in ser]).intersection(poly)
            if yeni.geom_type == 'MultiPolygon':
                yeni = max(yeni.geoms, key=lambda q: q.area)
            if not yeni.is_empty and yeni.area > 0.5 * poly.area:
                poly = yeni
    out = [poly]
    # armatür kutusu çentiklerini kapat (oda poligonu armatür çizgilerinden kesiliyor): mitre kapanış
    p0_ = oda['poly']
    kap = p0_.buffer(55, join_style=2, mitre_limit=3.0).buffer(-55, join_style=2, mitre_limit=3.0)
    diger = unary_union([r['poly'].buffer(-1) for r in K.rooms if r is not oda and r['poly'].area > 1.5e4]
                        + [c.buffer(1) for c in K.cols])
    kap = kap.difference(diger).intersection(p0_.buffer(70, join_style=2))
    if kap.geom_type == 'MultiPolygon':
        kap = max(kap.geoms, key=lambda q: q.area)
    if not kap.is_empty:
        kap = orto(Polygon(kap.exterior).simplify(3.0), tol=20.0)
        if kap.area < 1.35 * p0_.area and kap.contains(p0_.representative_point()):
            out.append(kap)
    return out


def _pis_su_halka(K, oda, fx, kolon_onceki, yasak, poly):
    """kolon seçimi + kollar + branşmanlar (verilen mahal poligonunun halkasında)"""
    hg = halka(poly)
    ring = hg.exterior
    if not ring.is_ccw:
        ring = LineString(list(ring.coords)[::-1])
    L = ring.length
    cs = list(ring.coords)[:-1]
    n = len(cs)
    # aday kolon noktaları: dışbükey köşeler + köşeden 40 cm'e kadar kenar boyunca
    adaylar = []
    for i in range(n):
        a, b, c = cs[i - 1], cs[i], cs[(i + 1) % n]
        ang, _ = kose_aci(a, b, c)
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if cr > 0 and 60 <= ang <= 120 and dist(a, b) > 15 and dist(b, c) > 15:      # sol dönüş (ccw) = dışbükey
            sb = ring.project(Point(b))
            for t in (0, 10, 20, 30, 40):
                for yon in (1, -1):
                    if t == 0 and yon < 0:
                        continue
                    if t > 0 and ((yon > 0 and t > dist(b, c) - 15) or (yon < 0 and t > dist(a, b) - 15)):
                        continue
                    s = (sb + yon * t) % L
                    adaylar.append((s, t))
    # diğer katlardaki kolon noktaları (düşey süreklilik): halkaya izdüşümü ≤ 25 cm ise aday
    for q in (kolon_onceki or []):
        if poly.buffer(30).contains(Point(q)) and ring.distance(Point(q)) <= 25:
            adaylar.append((ring.project(Point(q)), 0))
    kb = getattr(K, 'kb', None)
    if kb is not None:              # kontrolörün tanıdığı ıslak hacim köşelerine en yakın halka noktaları
        for r in kb['rooms']:
            if not r['islak'] or not r['poly'].intersects(poly):
                continue
            sp = r['poly'].simplify(6)
            for pg in (sp.geoms if hasattr(sp, 'geoms') else [sp]):
                for q in pg.exterior.coords:
                    if ring.distance(Point(q)) < 32:
                        adaylar.append((ring.project(Point(q)), 5))
    out = []
    for s, t in adaylar:
        p = tuple(ring.interpolate(s).coords[0])
        pt = Point(p)
        if any(c.distance(pt) < 3 for c in K.cols):
            continue
        if any(sf['poly'].buffer(6).contains(pt) for sf in K.saftlar):
            continue
        if K.kapi_u.distance(pt) < 15:
            continue
        if yasak is not None and yasak.contains(pt):
            continue
        # puan
        top, mx = 0.0, 0.0
        for f in fx:
            sf = ring.project(Point(f['c']))
            d1, d2 = yay_mesafesi(ring, s, sf)
            y = min(d1, d2) + ring.distance(Point(f['c']))
            w = 2.0 if f['kind'] == 'WC' else 1.0
            top += w * y
            mx = max(mx, y)
        pu = top + 0.7 * mx + 1.5 * t
        if mx > 250:
            pu += 20 * (mx - 250)
        if any(sf['poly'].distance(pt) < 60 for sf in K.saftlar):
            pu -= 40
        if K.kapi_u.distance(pt) < 35:
            pu += 60
        if kolon_onceki and any(dist(p, q) < 25 for q in kolon_onceki):
            pu -= 400 + 4 * (25 - min(dist(p, q) for q in kolon_onceki))
        out.append((pu, s, p))
    if not out:
        return None
    out.sort()
    for pu, s0, p0 in out[:80]:
        sonuc = _pis_kur(ring, fx, s0, p0)
        if sonuc is None:
            continue
        kollar, br = sonuc
        q = min(kolon_onceki, key=lambda q: dist(p0, q)) if kolon_onceki else None
        if q is not None and 1.0 < dist(p0, q) < 25:
            kollar, br, p0 = _ayak_ekle(oda, kollar, br, p0, q)
        if pis_dogrula(K, oda, kollar, br, p0):
            return dict(kolon=p0, kollar=kollar, br=br, ring=ring, oda=oda, puan=pu)
    pu, s0, p0 = out[0]
    kollar, br = _pis_kur(ring, fx, s0, p0)
    return dict(kolon=p0, kollar=kollar, br=br, ring=ring, oda=oda, puan=pu, dogrulanmadi=True)


def _ayak_ekle(oda, kollar, br, p0, q):
    """alt/üst kattaki kolon ekseni q: kol başına kısa dik (gerekirse L) ayak; kolon q'ya taşınır"""
    u = birim(q, p0)
    if abs(u[0]) < 0.02 or abs(u[1]) < 0.02:
        ayak = [q]
    else:
        k1, k2 = (q[0], p0[1]), (p0[0], q[1])
        kk = k1 if oda['poly'].buffer(6).contains(Point(k1)) else k2
        ayak = [q, kk]
    ek_boy = LineString(ayak + [p0]).length
    kollar = {yon: LineString(temiz(ayak + list(kol.coords))) for yon, kol in kollar.items()}
    br2 = []
    for b in br:
        b = dict(b)
        if b['kol'] is None:
            b['pts'] = temiz(b['pts'][:-1] + [p0] + ayak[::-1]) if b['pts'] else [q]
        else:
            b['t'] += ek_boy
        br2.append(b)
    return kollar, br2, q


def pis_dogrula(K, oda, kollar, br, p0):
    """kontrolör ölçüleriyle aynı mimari tanıma (MB) üzerinden: kolon ıslak hacim köşesinde, balkona taşmıyor,
    branşman yolu ≤ 260, pis–pis kesişme yok"""
    kb = getattr(K, 'kb', None)
    pt = Point(p0)
    if kb is not None:
        aday = [r for r in kb['rooms'] if r['islak'] and r['poly'].buffer(35).contains(pt)]
        if not aday:
            return False
        r = min(aday, key=lambda q: q['poly'].area)
        sp = r['poly'].simplify(6)
        kose = []
        for pg in (sp.geoms if hasattr(sp, 'geoms') else [sp]):
            kose += list(pg.exterior.coords)
        if not kose or min(dist(p0, k) for k in kose) > 43:
            return False
        hatlar = list(kollar.values()) + [LineString(b['pts']) for b in br if len(b['pts']) > 1]
        for r2 in kb['rooms']:
            if r2['balkon']:
                ic = r2['poly'].buffer(-5)
                if any(h.intersection(ic).length > 18 for h in hatlar):
                    return False
    # yol boyu
    for b in br:
        L = LineString(b['pts']).length if len(b['pts']) > 1 else 0
        kol = kollar.get(b['kol'])
        L += b['t'] if kol is not None else 0
        if L > 282:
            return False
    # pis–pis kesişme
    hat = [LineString(b['pts']) for b in br if len(b['pts']) > 1] + list(kollar.values())
    for i in range(len(hat)):
        for j in range(i + 1, len(hat)):
            if hat[i].crosses(hat[j]):
                return False
    return True


def dik_ayak(kol, c):
    """c'den kolun düz bir parçasına dik ayak (pah parçaları hariç); yoksa en yakın nokta. Dönüş (t, F, h)"""
    cs = list(kol.coords)
    best = None
    acc = 0.0
    for a, b in zip(cs[:-1], cs[1:]):
        L = dist(a, b)
        if L > 12:
            u = birim(a, b)
            tt = (c[0] - a[0]) * u[0] + (c[1] - a[1]) * u[1]
            if 2.0 <= tt <= L - 2.0:
                F = (a[0] + u[0] * tt, a[1] + u[1] * tt)
                h = dist(c, F)
                if best is None or h < best[2]:
                    best = (acc + tt, F, h, True)
        acc += L
    if best is not None and best[2] <= kol.distance(Point(c)) + 25:
        return best
    t = kol.project(Point(c))
    F = tuple(kol.interpolate(t).coords[0])
    return t, F, dist(c, F), dist(c, F) < 6.0


def izgara_noktasi(kol, t):
    """kol üzerinde t'deki nokta; köşeye < 3 cm ise köşe, eksen paralel parçada 2 cm ızgaraya oturtulmuş
    (kontrolörün 2 cm düğüm yuvarlamasında birleşimin kopmaması için)"""
    cs = list(kol.coords)
    acc = 0.0
    for a, b in zip(cs[:-1], cs[1:]):
        L = dist(a, b)
        if acc - 1e-6 <= t <= acc + L + 1e-6:
            tt = t - acc
            if tt < 3.0:
                return a
            if L - tt < 3.0:
                return b
            u = birim(a, b)
            p = (a[0] + u[0] * tt, a[1] + u[1] * tt)
            if abs(u[1]) < 1e-6:
                x = round(p[0] / 2.0) * 2.0
                x = min(max(x, min(a[0], b[0]) + 1), max(a[0], b[0]) - 1)
                return (x, a[1])
            if abs(u[0]) < 1e-6:
                y = round(p[1] / 2.0) * 2.0
                y = min(max(y, min(a[1], b[1]) + 1), max(a[1], b[1]) - 1)
                return (a[0], y)
            return p
        acc += L
    return cs[-1]


def _pis_kur(ring, fx, s0, p0):
    oda_poly_ic = lambda q: Polygon(ring.coords).buffer(6).contains(Point(q))
    # kollar
    yonler = {1: [], -1: []}
    for f in fx:
        sf = ring.project(Point(f['c']))
        d1, d2 = yay_mesafesi(ring, s0, sf)
        if d1 <= d2:
            yonler[1].append((d1, sf, f))
        else:
            yonler[-1].append((d2, sf, f))
    kollar = {}
    for yon, lst in yonler.items():
        if not lst:
            continue
        dmax, smax, _ = max(lst, key=lambda q: q[0])
        if dmax < 1.0:
            continue
        pts = yay_parca(ring, s0, smax, yon)
        kollar[yon] = LineString(oktal(pah_45(pts)))
    # branşmanlar
    br = []
    for yon, lst in yonler.items():
        kol = kollar.get(yon)
        for d, sf, f in lst:
            c = f['c']
            if kol is None:                          # armatür kolonun dibinde
                br.append(dict(f=f, pts=temiz([c, p0]), t=0.0, kol=None))
                continue
            t, F, h, dik = dik_ayak(kol, c)
            if not dik:                                   # dik ayak yok: dik açılı L ile kol noktasına
                Fq = izgara_noktasi(kol, t)
                tq = kol.project(Point(Fq))
                k1, k2 = (c[0], Fq[1]), (Fq[0], c[1])
                kk = k1 if oda_poly_ic(k1) else k2
                pts = [c, kk, Fq]
            elif h < 6.0 or t < 6.0:
                V = min(kol.coords, key=lambda v: dist(v, c))       # hat üstündeki armatür: köşe düğümüne bağla
                Fq = tuple(V) if dist(V, c) < 15 else izgara_noktasi(kol, t)
                tq = kol.project(Point(Fq))
                pts = [c, Fq]
            else:
                nrm = birim(F, c)
                tq = max(0.0, t - 5.0)
                Q = izgara_noktasi(kol, tq)
                tq = kol.project(Point(Q))
                u = birim(Q, F) if dist(Q, F) > 0.5 else (0.0, 0.0)
                F2 = (Q[0] + u[0] * 5.0, Q[1] + u[1] * 5.0)
                Pp = (F2[0] + nrm[0] * 5.0, F2[1] + nrm[1] * 5.0)
                pts = [c, Pp, Q]
            br.append(dict(f=f, pts=temiz(pts), t=tq, kol=yon))
    # kol, en uzak birleşim noktasında biter
    for yon in list(kollar):
        ts_ = [b['t'] for b in br if b['kol'] == yon]
        if not ts_:
            del kollar[yon]
            continue
        tm = max(ts_)
        if tm < kollar[yon].length - 0.5:
            kollar[yon] = substring(kollar[yon], 0, tm) if tm > 0.5 else None
            if kollar[yon] is None:
                del kollar[yon]
    return kollar, br



def pis_parcalar(ps):
    """kol parçaları (birleşim noktalarında bölünmüş) + branşmanlar; her parçaya SB, Ø"""
    parcalar = []
    for yon, kol in ps['kollar'].items():
        brs = [b for b in ps['br'] if b['kol'] == yon]
        ts = sorted(set([0.0] + [round(b['t'], 2) for b in brs] + [kol.length]))
        ts = [t for t in ts if 0 <= t <= kol.length + 1e-6]
        for t0, t1 in zip(ts[:-1], ts[1:]):
            if t1 - t0 < 0.5:
                continue
            ust = [b for b in brs if b['t'] >= t1 - 0.01]
            sb = sum(SB[b['f']['kind']] for b in ust)
            wc = any(b['f']['kind'] == 'WC' for b in ust)
            g = substring(kol, t0, t1)
            parcalar.append(dict(g=g, sb=sb, cap=pis_cap(sb, wc), tur='kol'))
    for b in ps['br']:
        k = b['f']['kind']
        parcalar.append(dict(g=LineString(b['pts']) if len(b['pts']) > 1 else None, sb=SB[k], cap=pis_cap(SB[k], k == 'WC'),
                             tur='br', f=b['f']))
    return [p for p in parcalar if p['g'] is not None and p['g'].length > 0.5]


# ====================================================================== TEMİZ SU (ızgara Dijkstra, dönüş cezalı)
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]          # (dc, dr) : sağ, aşağı(r+), sol, yukarı


class Izgara5:
    def __init__(self, w, res=5.0):
        self.x0, self.y1, self.res = w[0], w[3], res
        self.W = int((w[2] - w[0]) / res) + 1
        self.H = int((w[3] - w[1]) / res) + 1

    def rc(self, p):
        return (int(round((self.y1 - p[1]) / self.res)), int(round((p[0] - self.x0) / self.res)))

    def xy(self, r, c):
        return (self.x0 + c * self.res, self.y1 - r * self.res)

    def doldur(self, g, deger=1):
        img = np.zeros((self.H, self.W), np.uint8)
        for q in (g.geoms if hasattr(g, 'geoms') else [g]):
            if q.is_empty or q.geom_type != 'Polygon':
                continue
            pts = np.array([[(x - self.x0) / self.res, (self.y1 - y) / self.res] for x, y in q.exterior.coords], np.int32)
            cv2.fillPoly(img, [pts], deger)
            for hh in q.interiors:
                pts = np.array([[(x - self.x0) / self.res, (self.y1 - y) / self.res] for x, y in hh.coords], np.int32)
                cv2.fillPoly(img, [pts], 0)
        return img


def dijkstra_agac(cost, agac, hedefler, donus=12.0):
    """agac: set((r,c)) kaynak; hedefler: dict((r,c) -> anahtar). En yakın hedefe dönüş cezalı en ucuz yol.
    Dönüş: (anahtar, [ (r,c) ... hedeften ağaca ]) ya da (None, None)"""
    H, W = cost.shape
    INF = float('inf')
    best = {}
    pq = []
    for (r, c) in agac:
        for d in range(4):
            best[(r, c, d)] = 0.0
            heapq.heappush(pq, (0.0, r, c, d))
    prev = {}
    while pq:
        g, r, c, d = heapq.heappop(pq)
        if g > best.get((r, c, d), INF):
            continue
        if (r, c) in hedefler and (r, c) not in agac:
            yol = [(r, c)]
            st = (r, c, d)
            while st in prev:
                st = prev[st]
                if (st[0], st[1]) != yol[-1]:
                    yol.append((st[0], st[1]))
            return hedefler[(r, c)], yol
        for nd, (dc, dr) in enumerate(DIRS):
            if (nd + 2) % 4 == d and (r, c) not in agac:
                continue
            nr, nc = r + dr, c + dc
            if not (0 <= nr < H and 0 <= nc < W):
                continue
            cc = cost[nr, nc]
            if cc == INF:
                continue
            ng = g + cc + (donus if (nd != d and (r, c) not in agac) else 0.0)
            if ng < best.get((nr, nc, nd), INF):
                best[(nr, nc, nd)] = ng
                prev[(nr, nc, nd)] = (r, c, d)
                heapq.heappush(pq, (ng, nr, nc, nd))
    return None, None


def _cizgi_hucreler(a, b):
    """eksen paralel iki hücre arası hücreler (a dahil, b dahil)"""
    (r0, c0), (r1, c1) = a, b
    if r0 == r1:
        st = 1 if c1 >= c0 else -1
        return [(r0, c) for c in range(c0, c1 + st, st)]
    st = 1 if r1 >= r0 else -1
    return [(r, c0) for r in range(r0, r1 + st, st)]


def merdiven_duzelt(yol, cost, agac, oran=1.6):
    """ızgara yolundaki basamak (iki ardışık dönüş) parçalarını tek dönüşlü L ile değiştir (maliyet ≤ oran × eski)"""
    def koseler(y):
        k = [0]
        for i in range(1, len(y) - 1):
            a, b, c = y[i - 1], y[i], y[i + 1]
            if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
                k.append(i)
        k.append(len(y) - 1)
        return k
    degisti = True
    tur = 0
    while degisti and tur < 50:
        degisti = False
        tur += 1
        k = koseler(yol)
        for j in range(len(k) - 3):
            ia, id_ = k[j], k[j + 3]
            A, D = yol[ia], yol[id_]
            eski = yol[ia:id_ + 1]
            m_eski = sum(cost[r, c] for r, c in eski[1:])
            for ara in ((A[0], D[1]), (D[0], A[1])):
                yeni = _cizgi_hucreler(A, ara) + _cizgi_hucreler(ara, D)[1:]
                if any(not np.isfinite(cost[r, c]) for r, c in yeni):
                    continue
                if any(h in agac for h in yeni[:-1]):
                    continue
                m_yeni = sum(cost[r, c] for r, c in yeni[1:])
                if m_yeni <= oran * m_eski:
                    yol = yol[:ia] + yeni + yol[id_ + 1:]
                    degisti = True
                    break
            if degisti:
                break
    return yol


def duvara_dayali_nokta(oda_poly, c, eksen=None, ic=10.0):
    """armatürün bağlandığı duvar noktası (oda içinde duvardan `ic` cm)"""
    ring = oda_poly.exterior
    if eksen is not None:
        best = None
        for s in (1, -1):
            d = (s, 0) if eksen == 'x' else (0, s)
            ray = LineString([c, (c[0] + d[0] * 400, c[1] + d[1] * 400)])
            x = ray.intersection(ring)
            pts = [x] if x.geom_type == 'Point' else [g for g in getattr(x, 'geoms', []) if g.geom_type == 'Point']
            for q in pts:
                dd = dist(c, (q.x, q.y))
                if best is None or dd < best[0]:
                    best = (dd, (q.x, q.y), d)
        if best is not None:
            q, d = best[1], best[2]
            return (q[0] - d[0] * ic, q[1] - d[1] * ic)
    q = nearest_points(ring, Point(c))[0]
    u = birim((q.x, q.y), c)
    return (q.x + u[0] * ic, q.y + u[1] * ic)


def temiz_su_daire(K, dno, fx, tohum):
    """daire temiz su ağacı. Dönüş: dict(soguk=[(p,q,mb)], sicak=[(p,q,mb)], giris=(G,H), musluk=[(p, kind)],
    zincir=[dict(pts, mb_s, mb_h, ...)], kombi=p)"""
    izin = [r for r in K.rooms if r['daire'] == dno and r['tip'] in ('hol', 'islak', 'mutfak')]
    kombiler = [f for f in fx if f['kind'] == 'KOMBI']
    for f in kombiler:
        if f['oda'] is not None and f['oda'] not in izin:
            izin.append(f['oda'])
    ids = {r['i'] for r in izin}
    yasak = [r for r in K.rooms if r['i'] not in ids]
    U = unary_union([r['poly'] for r in izin])
    w = U.buffer(80).bounds
    g = Izgara5(w)
    izin_m = g.doldur(unary_union([r['poly'].buffer(1) for r in izin])) > 0
    yasak_m = g.doldur(unary_union([r['poly'].buffer(-3) for r in yasak])) > 0 if yasak else np.zeros_like(izin_m)
    duvar_m = g.doldur(K.S) > 0
    kapi_m = g.doldur(K.kapi_u.buffer(6)) > 0 if not K.kapi_u.is_empty else np.zeros_like(izin_m)
    d = ndi.distance_transform_edt(izin_m) * g.res
    cost = np.full(izin_m.shape, np.inf)
    cost[izin_m] = 1.0 + 60.0 / (d[izin_m] + 3.0)
    blk = [r for r in izin if r['tip'] == 'balkon']
    if blk:            # kombi balkonda: hat balkonun ortasından değil, duvar dibinden kombiye (kullanıcı çizimi PNG 14)
        bm = (g.doldur(unary_union([r['poly'] for r in blk])) > 0) & izin_m
        cost[bm] = 1.0 + 0.3 * np.maximum(d[bm] - 10.0, 0.0)
    yakin = cv2.dilate(izin_m.astype(np.uint8), np.ones((17, 17), np.uint8)) > 0
    dm = duvar_m & yakin & ~izin_m
    cost[dm] = 25.0
    cost[yasak_m & ~izin_m] = np.inf
    # aynı dairenin kuru mahalleri (oda/salon): yalnız gerekirse, duvar dibinden (ör. odadan girilen duş)
    kuru = [r for r in yasak if r['daire'] == dno and r['tip'] not in ('ortak', 'balkon')]
    if kuru:
        km = (g.doldur(unary_union([r['poly'].buffer(-3) for r in kuru])) > 0) & ~izin_m
        dk = ndi.distance_transform_edt(km) * g.res
        cost[km] = 3.0 + 0.3 * np.maximum(dk[km] - 15.0, 0.0)
        yk = cv2.dilate(km.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0     # kuru mahal duvarı (ara duvar geçişi)
        dmk = duvar_m & yk & ~izin_m & ~np.isfinite(cost)
        cost[dmk] = 25.0
        cost[yasak_m & ~izin_m & ~km] = np.inf
    cost[kapi_m] = np.inf
    if not K.kapi_u.is_empty:      # kapı kanadı süpürme alanı: hat kapı önünden/kanadından geçmesin
        kk = (g.doldur(K.kapi_u.buffer(48)) > 0) & np.isfinite(cost)
        cost[kk] += 30.0
    # ---- giriş: hol mahallinin ortak alana bakan DOLU duvarında, daire no yazısına (kapı önü) en yakın nokta
    hol = [r for r in izin if r['tip'] == 'hol']
    ortak = unary_union([r['poly'] for r in K.rooms if r['tip'] == 'ortak'] or [Polygon()])
    G = H = None
    if hol and tohum is not None and not ortak.is_empty:
        h0 = min(hol, key=lambda r: r['poly'].distance(Point(tohum)))
        ring = h0['poly'].exterior
        aday, acik = [], []
        for i in range(int(ring.length / 4)):
            p = ring.interpolate(i * 4.0)
            q = nearest_points(ortak, p)[0]
            dd = p.distance(q)
            if not (6 <= dd <= 50):
                continue
            seg = LineString([p, q])
            kap = seg.intersection(K.S).length / max(seg.length, 1e-6)
            if kap < 0.6:
                acik.append((p.x, p.y))
            elif kap > 0.9:
                aday.append(((p.x, p.y), (q.x, q.y)))
        aday = [(p, q) for p, q in aday if not acik or min(dist(p, a) for a in acik) >= 30]
        aday = [(p, q) for p, q in aday if K.kapi_u.distance(Point(p)) >= 30]
        if aday:
            p, q = min(aday, key=lambda pq: dist(pq[1], tohum))
            u = birim(q, p)
            Hn = (p[0] + u[0] * 12, p[1] + u[1] * 12)
            r_, c_ = g.rc(Hn)
            H = g.xy(r_, c_)
            if abs(u[0]) > abs(u[1]):
                G = (q[0], H[1])
            else:
                G = (H[0], q[1])
    if H is None:
        h0 = hol[0] if hol else izin[0]
        p = h0['poly'].representative_point()
        r_, c_ = g.rc((p.x, p.y))
        H = g.xy(r_, c_)
        G = H
    # ---- hedefler (armatür bağlantı noktaları)
    hedef = {}
    musluk = []
    for f in fx:
        k = f['kind']
        if k not in MB_S or f['oda'] is None:
            continue
        tap = f['c'] if k == 'KOMBI' else duvara_dayali_nokta(f['oda']['poly'], f['c'], f.get('eksen'), ic=10.0)
        r_, c_ = g.rc(tap)
        # sonlu maliyetli en yakın hücre
        best = None
        for dr in range(-4, 5):
            for dc in range(-4, 5):
                rr, cc = r_ + dr, c_ + dc
                if 0 <= rr < g.H and 0 <= cc < g.W and cost[rr, cc] < np.inf:
                    dd = dr * dr + dc * dc
                    if best is None or dd < best[0]:
                        best = (dd, rr, cc)
        if best is None:
            log('  ! D%s %s bağlantı noktası ulaşılamaz' % (dno, k))
            continue
        hedef[(best[1], best[2])] = f
        musluk.append((g.xy(best[1], best[2]), f))
        f['tap'] = g.xy(best[1], best[2])
    kok = g.rc(H)
    agac = {kok}
    kenar = set()
    kalan = dict(hedef)
    hucre_f = {}
    while kalan:
        tm = np.zeros(cost.shape, np.uint8)
        for (r, c) in agac:
            tm[r, c] = 1
        yak = (cv2.dilate(tm, np.ones((7, 7), np.uint8)) > 0) & (tm == 0)
        ce = cost.copy()
        ce[yak] += 12.0
        anahtar, yol = dijkstra_agac(ce, agac, {k: v for k, v in kalan.items()}, donus=30.0)
        if anahtar is None:
            log('  ! D%s: %d hedefe yol bulunamadı: %s' % (dno, len(kalan), ', '.join(
                '%s/%s@%.0f,%.0f' % (f['kind'], f['oda']['name'], f['c'][0], f['c'][1]) for f in kalan.values())))
            break
        yol = merdiven_duzelt(yol, cost, agac)
        hc = yol[0]
        hucre_f[hc] = kalan.pop(hc)
        for a, b in zip(yol[:-1], yol[1:]):
            kenar.add((a, b) if a < b else (b, a))
        agac.update(yol)
        # aynı hücreye düşen başka hedef
        for k2 in list(kalan):
            if k2 in agac:
                hucre_f[k2] = kalan.pop(k2)
    import networkx as nx
    T = nx.Graph()
    T.add_node(kok)
    T.add_edges_from(kenar)
    # önemli düğümler: derece != 2, dönüş, hedef, kök
    def onemli(v):
        if v == kok or v in hucre_f or T.degree(v) != 2:
            return True
        a, b = list(T.neighbors(v))
        return not (a[0] == b[0] or a[1] == b[1])
    # kökten yönlendir
    ebeveyn = {kok: None}
    sira = list(nx.bfs_tree(T, kok))
    for v in sira:
        for u in T.neighbors(v):
            if u not in ebeveyn:
                ebeveyn[u] = v
    # aşağı akış yükleri
    alt_s, alt_h = defaultdict(float), defaultdict(float)
    kombi_h = None
    for hc, f in hucre_f.items():
        if f['kind'] == 'KOMBI':
            kombi_h = hc
    for v in reversed(sira):
        f = hucre_f.get(v)
        if f is not None:
            alt_s[v] += MB_S.get(f['kind'], 0.0)
        p = ebeveyn[v]
        if p is not None:
            alt_s[p] += alt_s[v]
    # sıcak alt ağaç: kombi -> sıcak armatürler
    sicak_k = set()
    sicak_mb = defaultdict(float)          # kenar -> sıcak yük (kombiden uzak taraftaki sıcak armatürler)
    if kombi_h is not None:
        for hc, f in hucre_f.items():
            if f['kind'] in MB_H:
                yol = nx.shortest_path(T, kombi_h, hc)
                for a, b in zip(yol[:-1], yol[1:]):
                    e = (a, b) if a < b else (b, a)
                    sicak_k.add(e)
                    sicak_mb[e] += MB_H[f['kind']]
    # düz parçalar (önemli düğümler arası) -> soğuk / sıcak segmentleri
    soguk, sicak = [], []
    gorulen = set()
    for v in T.nodes:
        if not onemli(v):
            continue
        for u in T.neighbors(v):
            e0 = (v, u) if v < u else (u, v)
            if e0 in gorulen:
                continue
            zin = [v, u]
            while not onemli(zin[-1]):
                a, b = list(T.neighbors(zin[-1]))
                nxt = a if a != zin[-2] else b
                zin.append(nxt)
            for a, b in zip(zin[:-1], zin[1:]):
                gorulen.add((a, b) if a < b else (b, a))
            # yük: zincirin aşağı ucu
            a0, b0 = zin[0], zin[-1]
            asagi = b0 if ebeveyn.get(b0) is not None and ebeveyn[b0] in zin else a0
            mb_s = alt_s[asagi]
            e1 = (zin[0], zin[1]) if zin[0] < zin[1] else (zin[1], zin[0])
            p, q = g.xy(*zin[0]), g.xy(*zin[-1])
            soguk.append(dict(p=p, q=q, mb=mb_s, hucre=(zin[0], zin[-1])))
            if e1 in sicak_k:
                sicak.append(dict(p=(p[0] + O_SICAK, p[1] + O_SICAK), q=(q[0] + O_SICAK, q[1] + O_SICAK),
                                  mb=sicak_mb[e1], hucre=(zin[0], zin[-1])))
    toplam = alt_s[kok]
    # etiket zincirleri: dallanma düğümleri arası (dönüşler dahil)
    def dal(v):
        return v == kok or v in hucre_f or T.degree(v) != 2
    zincirler = []
    gor2 = set()
    for v in T.nodes:
        if not dal(v):
            continue
        for u in T.neighbors(v):
            e0 = (v, u) if v < u else (u, v)
            if e0 in gor2:
                continue
            zin = [v, u]
            while not dal(zin[-1]):
                a, b = list(T.neighbors(zin[-1]))
                zin.append(a if a != zin[-2] else b)
            for a, b in zip(zin[:-1], zin[1:]):
                gor2.add((a, b) if a < b else (b, a))
            a0, b0 = zin[0], zin[-1]
            if ebeveyn.get(a0) == zin[1]:          # yönü kökten aşağı çevir
                zin = zin[::-1]
            e1 = (zin[0], zin[1]) if zin[0] < zin[1] else (zin[1], zin[0])
            pts = temiz([g.xy(*c) for c in zin])
            uc = hucre_f.get(zin[-1])
            zincirler.append(dict(pts=pts, mb_s=alt_s[zin[-1]], mb_h=sicak_mb[e1] if e1 in sicak_k else 0.0,
                                  sicak=e1 in sicak_k, kok=(zin[0] == kok), uc=uc,
                                  bas=g.xy(*zin[0]), son=g.xy(*zin[-1])))
    return dict(soguk=soguk, sicak=sicak, G=G, H=H, musluk=musluk, zincir=zincirler, toplam=toplam,
                kombi=kombiler[0]['c'] if kombiler else None, izin=U)


# ====================================================================== EK ARMATÜR (mimaride yoksa)
def ek_nokta(oda, fx_oda, K, ofset, uzak, tercih, makine=False):
    """oda halkası üzerinde (duvardan `ofset`), diğer armatürlere ≥ uzak, kapıya ≥ 50; `tercih` noktasına en yakın"""
    hg = halka(oda['poly'], ofset)
    if hg.is_empty:
        return None
    ring = hg.exterior
    best = None
    for i in range(int(ring.length / 5)):
        p = ring.interpolate(i * 5.0)
        pt = (p.x, p.y)
        if any(dist(pt, f['c']) < uzak for f in fx_oda):
            continue
        if K.kapi_u.distance(p) < 50 or any(s['poly'].distance(p) < 20 for s in K.saftlar):
            continue
        kb = getattr(K, 'kb', None)
        if kb is not None and not makine:
            ic = [r for r in kb['rooms'] if r['islak'] and r['poly'].buffer(-6).contains(p)]
            if not ic:
                continue
        if makine:
            kare = Point(pt).buffer(28, cap_style=3)
            if not oda['poly'].buffer(2).contains(kare):
                continue
        dd = dist(pt, tercih) if tercih else 0.0
        if best is None or dd < best[0]:
            best = (dd, pt)
    return best[1] if best else None


def ek_armaturler(K):
    """her ıslak hacimde 1 süzgeç; her dairede ÇM ve BM (mimaride yoksa EK)"""
    ekler = []
    daireler = sorted({r['daire'] for r in K.rooms if r['daire'] is not None})
    for r in K.rooms:
        if r['tip'] not in ('islak', 'mutfak'):
            continue
        fo = [f for f in K.fx if f['oda'] is r]
        if not any(f['kind'] == 'YS' for f in fo):
            ref = next((f['c'] for f in fo if f['kind'] == 'DUS'), None) or \
                  next((f['c'] for f in fo if f['kind'] in ('WC', 'EV', 'LV')), None)
            p = ek_nokta(r, [f for f in fo if f['kind'] != 'KOMBI'], K, 15.0, 28.0, ref)
            if p:
                f = dict(kind='YS', c=p, oda=r, ek=True)
                K.fx.append(f)
                ekler.append(f)
    for d in daireler:
        fo = [f for f in K.fx if f['oda'] is not None and f['oda']['daire'] == d]
        if not any(f['kind'] == 'CM' for f in fo):
            banyolar = sorted([r for r in K.rooms if r['daire'] == d and r['tip'] == 'islak'],
                              key=lambda r: -r['poly'].area)
            for r in banyolar:
                fr = [f for f in K.fx if f['oda'] is r]
                ref = next((f['c'] for f in fr if f['kind'] in ('DUS', 'WC')), None)
                p = ek_nokta(r, fr, K, 32.0, 48.0, ref, makine=True)
                if p:
                    f = dict(kind='CM', c=p, oda=r, ek=True)
                    K.fx.append(f)
                    ekler.append(f)
                    break
        if not any(f['kind'] == 'BM' for f in fo):
            mut = [r for r in K.rooms if r['daire'] == d and r['tip'] == 'mutfak']
            for r in mut:
                fr = [f for f in K.fx if f['oda'] is r]
                ev = next((f['c'] for f in fr if f['kind'] == 'EV'), None)
                p = ek_nokta(r, fr, K, 32.0, 48.0, ev, makine=True)
                if p:
                    f = dict(kind='BM', c=p, oda=r, ek=True)
                    K.fx.append(f)
                    ekler.append(f)
                    break
    return ekler


# ====================================================================== YERLEŞTİRME YARDIMCILARI
def daire_poly(c, r, n=24):
    return Point(c).buffer(r, resolution=max(4, n // 4))


def balon_yeri(c, eng, yasak, r=27.5, mesafeler=(55, 70, 85, 100, 115), disarida=None, kil_tol=0.5):
    for dd in mesafeler:
        for k in range(16):
            a = math.radians(22.5 * k + 11.25 * ((dd // 15) % 2))
            p = (c[0] + dd * math.cos(a), c[1] + dd * math.sin(a))
            pg = daire_poly(p, r + 1.0)
            if yasak is not None and pg.intersects(yasak):
                continue
            if disarida is not None and not disarida.contains(Point(p)):
                continue
            if eng.carpar(pg):
                continue
            kil = LineString([(c[0] + 16 * math.cos(a), c[1] + 16 * math.sin(a)),
                              (p[0] - r * math.cos(a), p[1] - r * math.sin(a))])
            if kil_tol is not None and eng.carpar(kil.buffer(0.5), cizgi_tol=kil_tol):
                continue
            return p, kil
    return None, None


def etiket_dene_pis(msp, eng, g, cap, sb, adaylar_t=(0.5, 0.38, 0.62, 0.26, 0.74, 0.15, 0.85)):
    """pis su etiketi: hattın ÜZERİNDE (kanca ucu hatta), parça ortasında, hat yönünde döndürülmüş."""
    L = g.length
    if L < 1:
        return None
    for t in adaylar_t:
        a = g.interpolate(t * L)
        # yerel yön
        t0, t1 = max(0, t * L - 1), min(L, t * L + 1)
        p0, p1 = g.interpolate(t0), g.interpolate(t1)
        ang = math.degrees(math.atan2(p1.y - p0.y, p1.x - p0.x))
        if ang > 90.0001:
            ang -= 180
        elif ang <= -90:
            ang += 180
        for ad in ('ROTAS-S2-PS-CAP-U', 'ROTAS-S2-PS-CAP-A'):
            e = ekle_insert(msp, ad, (a.x, a.y), L_PCAP, rot=ang, attr={'CAP': cap, 'SB': '%d SB' % sb})
            kut = yazi_kutulari(e)
            if kut and not any(eng.carpar(k) for k in kut):
                for k in kut:
                    eng.ekle_alan(k)
                return e
            msp.delete_entity(e)
    return None


def etiket_kilavuzlu(msp, eng, a, satirlar, blok, katman, yasak=None, hks=(14, 24, 34, 48, 64, 82, 104, 130),
                     yatay_hat=True):
    """yatay (dönmesiz) çok satırlı etiket: a (hat üstü nokta) -> kanca -> yazı bloğu. satirlar: attr sözlüğü"""
    n = len(satirlar)
    yuk = 15.0 * (n - 1) + ETIKET_H
    for hk in hks:
        for (sx, sy) in ((1, 1), (-1, 1), (1, -1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if yatay_hat and sx != 0 and sy == 0:
                continue
            if not yatay_hat and sy != 0 and sx == 0:
                continue
            # kanca ucu
            hx = a[0] + sx * (hk if not yatay_hat or sy == 0 else 0)
            hy = a[1] + sy * (hk if yatay_hat or sx == 0 else 0)
            if yatay_hat:          # yatay hat: kanca düşey, yazı kanca ucunun sağında/solunda
                hx, hy = a[0], a[1] + sy * hk
            else:                  # düşey hat: kanca yatay
                hx, hy = a[0] + sx * hk, a[1] + sy * (hk * 0.5 if sy else 0)
            e = ekle_insert(msp, blok, (0, 0), katman, attr=satirlar)
            kut = yazi_kutulari(e)
            if not kut:
                msp.delete_entity(e)
                return None
            bx0 = min(k.bounds[0] for k in kut)
            bx1 = max(k.bounds[2] for k in kut)
            by0 = min(k.bounds[1] for k in kut)
            by1 = max(k.bounds[3] for k in kut)
            gen = bx1 - bx0
            # yazı bloğunun konumu
            if yatay_hat:
                ix = hx + 2 if sx > 0 else hx - 2 - gen
                iy = hy + 2 - by0 if sy > 0 else hy - 2 - by1
            else:
                ix = hx + 2 - bx0 if sx > 0 else hx - 2 - bx1
                iy = hy - (by0 + by1) / 2.0
            msp.delete_entity(e)
            e = ekle_insert(msp, blok, (ix, iy), katman, attr=satirlar)
            kut = yazi_kutulari(e)
            kil = LineString([a, (hx, hy)])
            if any(eng.carpar(k) for k in kut) or (hk > 40 and eng.carpar(kil.buffer(0.4), cizgi_tol=1.0)):
                msp.delete_entity(e)
                continue
            if yasak is not None and any(k.intersects(yasak) for k in kut):
                msp.delete_entity(e)
                continue
            for k in kut:
                eng.ekle_alan(k)
            # kanca: hat noktasından kanca ucuna + yazı altı çizgi
            ux0 = min(k.bounds[0] for k in kut)
            ux1 = max(k.bounds[2] for k in kut)
            msp.add_lwpolyline([a, (hx, hy)], dxfattribs={'layer': katman})
            if yatay_hat:
                msp.add_line((hx, hy), (ux1 if sx > 0 else ux0, hy), dxfattribs={'layer': katman})
            eng.ekle_cizgi(kil)
            return e
    return None


def etiket_halka(msp, eng, m, satirlar, blok, katman, mesafeler=(35, 50, 70, 90, 115, 140, 170, 210, 250, 300)):
    """kalabalıkta etiket dışarı: m (parça ortası) çevresinde halka araması, kılavuz çizgili (yazı yatay)"""
    e = ekle_insert(msp, blok, (0, 0), katman, attr=satirlar)
    kut = yazi_kutulari(e)
    msp.delete_entity(e)
    if not kut:
        return None
    bx0 = min(k.bounds[0] for k in kut); bx1 = max(k.bounds[2] for k in kut)
    by0 = min(k.bounds[1] for k in kut); by1 = max(k.bounds[3] for k in kut)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    for dd in mesafeler:
        for k in range(24):
            a = math.radians(15.0 * k + 5)
            p = (m[0] + dd * math.cos(a), m[1] + dd * math.sin(a))
            ins = (p[0] - cx, p[1] - cy)
            kutu = box(bx0 + ins[0] - 1, by0 + ins[1] - 1, bx1 + ins[0] + 1, by1 + ins[1] + 1)
            if eng.carpar(kutu):
                continue
            q = nearest_points(kutu.exterior, Point(m))[0]
            kil = LineString([m, (q.x, q.y)])
            kil_k = substring(kil, min(20.0, kil.length * 0.4), kil.length) if kil.length > 1 else kil
            if eng.carpar(kil_k.buffer(0.3), cizgi_tol=99999):
                continue
            e = ekle_insert(msp, blok, ins, katman, attr=satirlar)
            kut2 = yazi_kutulari(e)
            if any(eng.carpar(k2) for k2 in kut2):
                msp.delete_entity(e)
                continue
            for k2 in kut2:
                eng.ekle_alan(k2)
            msp.add_line(m, (q.x, q.y), dxfattribs={'layer': L_KIL})
            eng.ekle_cizgi(kil)
            msp.add_circle(m, 1.5, dxfattribs={'layer': L_KIL})
            return e
    return None


def yazi_yerlestir(msp, eng, metin, h, katman, merkezler, renk=None, mtext=True, yasak=None):
    """serbest yazı (MTEXT): verilen aday merkezlerden ilk çakışmasızı"""
    for c in merkezler:
        e = msp.add_mtext(metin, dxfattribs={'layer': katman, 'char_height': h, 'style': 'ROTAS-YAZI',
                                             'attachment_point': 5, 'width': 0})
        e.dxf.insert = (c[0], c[1])
        if renk:
            e.dxf.color = renk
        kut = yazi_kutulari(e)
        if kut and not any(eng.carpar(k) for k in kut) and (yasak is None or not any(k.intersects(yasak) for k in kut)):
            for k in kut:
                eng.ekle_alan(k)
            return e
        msp.delete_entity(e)
    return None


# ====================================================================== KAT ÇİZİMİ
ISLAK_SIRA = {'mutfak': 0}


def kolon_sirasi(ps):
    oda = ps['oda']
    wc = any(b['f']['kind'] == 'WC' for b in ps['br'])
    return (oda['daire'] or 99, 0 if oda['tip'] == 'mutfak' else (1 if wc else 2), oda['poly'].area)


def yb_sirasi(inisler, merkez):
    """YB numarası: sol alttan başlayıp saat yönü tersine (kullanıcı çizimi YB1..YB9)"""
    cx, cy = merkez
    a0 = math.atan2(-1, -1)
    def aci(p):
        a = math.atan2(p[1] - cy, p[0] - cx)
        return (a - a0) % (2 * math.pi)
    return sorted(inisler, key=aci)


class Durum:
    def __init__(self):
        self.kolonlar = {}          # no -> dict(x0, y0 (zemin çerçevesi), katlar, sb_kat)
        self.n_kolon = 0
        self.yb = {}                # no -> (x0, y0)
        self.model_daire = []
        self.adet = defaultdict(int)
        self.uyari = []
        self.temiz_daire = {}


def kat_ciz(doc, eng, K, dur, onceki):
    msp = doc.modelspace()
    k = K.k
    off = K.off
    ek = ek_armaturler(K)
    log('kat %s: mahal %d, armatür %d (EK %d: %s)' % (k, len(K.rooms), len(K.fx), len(ek),
                                                     ', '.join('%s/%s' % (f['kind'], f['oda']['name']) for f in ek)))
    # ---------------- pis su
    pisler = []
    kol_onceki = [(x + off, y) for (x, y) in onceki] if onceki else []
    for r in K.rooms:
        if r['tip'] not in ('islak', 'mutfak') or r['daire'] is None:
            continue
        fo = [f for f in K.fx if f['oda'] is r and f['kind'] in SB]
        if not fo:
            continue
        ps = pis_su_oda(K, r, fo, kol_onceki, None)
        if ps is None:
            dur.uyari.append('kat %s %s: kolon yeri bulunamadı' % (k, r['name']))
            continue
        pisler.append(ps)
    pisler.sort(key=kolon_sirasi)
    # numara: alt kattaki aynı konumdaki kolonun numarası; yoksa yeni
    for ps in pisler:
        x0, y0 = ps['kolon'][0] - off, ps['kolon'][1]
        no = None
        for kn, kv in dur.kolonlar.items():
            if dist((x0, y0), (kv['x'], kv['y'])) < 3 and k not in kv['katlar']:
                no = kn
                break
        if no is None:
            dur.n_kolon += 1
            no = 'P%d' % dur.n_kolon
            dur.kolonlar[no] = dict(no=no, x=round(x0, 1), y=round(y0, 1), katlar=[], sb_kat={}, oda={})
        ps['no'] = no
        kv = dur.kolonlar[no]
        kv['katlar'].append(k)
        kv['oda'][k] = '%s D%s' % (ps['oda']['name'], ps['oda']['daire'])
        kv['sb_kat'][k] = sum(SB[b['f']['kind']] for b in ps['br'])
        kv.setdefault('armatur', {})[k] = [b['f']['kind'] for b in ps['br']]
    for ps in pisler:
        for kol in ps['kollar'].values():
            msp.add_lwpolyline(list(kol.coords), dxfattribs={'layer': L_PIS})
            eng.ekle_cizgi(kol)
        for b in ps['br']:
            if len(b['pts']) > 1:
                msp.add_lwpolyline(b['pts'], dxfattribs={'layer': L_PIS})
                eng.ekle_cizgi(LineString(b['pts']))
        ekle_insert(msp, 'ROTAS-S2-PIS-KOLON', ps['kolon'], 'ROTAS-SIHHI-SEMBOL')
        eng.ekle_alan(daire_poly(ps['kolon'], 15))
        dur.adet['ROTAS-S2-PIS-KOLON'] += 1
    # süzgeçler (ıslak hacim)
    for f in K.fx:
        if f['kind'] == 'YS' and f['oda'] is not None and f['oda']['tip'] in ('islak', 'mutfak'):
            ekle_insert(msp, 'ROTAS-S2-YER-SUZGECI', f['c'], 'ROTAS-SIHHI-SEMBOL')
            eng.ekle_alan(Point(f['c']).buffer(8, cap_style=3))
            dur.adet['ROTAS-S2-YER-SUZGECI'] += 1
        if f.get('ek') and f['kind'] in ('CM', 'BM'):
            ekle_insert(msp, 'ROTAS-S2-MAKINE-EK', f['c'], 'ROTAS-SIHHI-SEMBOL')
            dur.adet['ROTAS-S2-MAKINE-EK'] += 1
    # ---------------- temiz su
    temizler = {}
    for p, dno in K.tohum:
        fx = [f for f in K.fx if f['oda'] is not None and f['oda']['daire'] == dno and f['kind'] in MB_S]
        if not fx:
            continue
        t0 = time.time()
        ts = temiz_su_daire(K, dno, fx, p)
        temizler[dno] = ts
        log('  D%d temiz su: soğuk %d parça, sıcak %d parça, %.1f MB (%.1f s)' % (dno, len(ts['soguk']), len(ts['sicak']),
                                                                              ts['toplam'], time.time() - t0))
        for s in ts['soguk']:
            msp.add_lwpolyline([s['p'], s['q']], dxfattribs={'layer': L_SOG})
            eng.ekle_cizgi(LineString([s['p'], s['q']]))
        for s in ts['sicak']:
            msp.add_lwpolyline([s['p'], s['q']], dxfattribs={'layer': L_SIC})
            eng.ekle_cizgi(LineString([s['p'], s['q']]))
        if dist(ts['G'], ts['H']) > 1:
            msp.add_lwpolyline([ts['G'], ts['H']], dxfattribs={'layer': L_SOG})
            eng.ekle_cizgi(LineString([ts['G'], ts['H']]))
        ekle_insert(msp, 'ROTAS-S2-TEMIZ-GIRIS', ts['G'], 'ROTAS-SIHHI-SEMBOL')
        eng.ekle_alan(Point(ts['G']).buffer(5))
        for tap, f in ts['musluk']:
            if f['kind'] == 'KOMBI':
                continue
            ekle_insert(msp, 'ROTAS-S2-KURESEL-VANA', tap, 'ROTAS-SIHHI-SEMBOL')
            dur.adet['ROTAS-S2-KURESEL-VANA'] += 1
            if f['kind'] in MB_H:
                ekle_insert(msp, 'ROTAS-S2-KURESEL-VANA', (tap[0] + O_SICAK, tap[1] + O_SICAK), 'ROTAS-SIHHI-SEMBOL')
                dur.adet['ROTAS-S2-KURESEL-VANA'] += 1
    # ---------------- balkon süzgeci -> yağmur inişi
    balkon_s = []
    for r in K.rooms:
        if r['tip'] != 'balkon' or r['poly'].area < 1.5e4:
            continue
        yak = [p for p in K.inisler if r['poly'].distance(Point(p)) < 45]
        if not yak:
            continue
        c = r['poly'].centroid
        ini = min(yak, key=lambda p: r['poly'].distance(Point(p)))
        mim = [f for f in K.fx if f['kind'] == 'YS' and f['oda'] is r and dist(f['c'], ini) < 60]
        if mim:
            s = mim[0]['c']
        else:
            hg = halka(r['poly'], 12.0)
            ring = hg.exterior
            s, bd = None, None
            for i in range(int(ring.length / 2)):
                q = ring.interpolate(i * 2.0)
                dd = abs(dist((q.x, q.y), ini) - 30.0)
                if bd is None or dd < bd:
                    s, bd = (q.x, q.y), dd
        if s is None:
            continue
        msp.add_lwpolyline([s, ini], dxfattribs={'layer': L_YAG})
        eng.ekle_cizgi(LineString([s, ini]))
        ekle_insert(msp, 'ROTAS-S2-BALKON-SUZGECI', s, 'ROTAS-SIHHI-SEMBOL')
        eng.ekle_alan(Point(s).buffer(8, cap_style=3))
        dur.adet['ROTAS-S2-BALKON-SUZGECI'] += 1
        balkon_s.append(dict(r=r, s=s, ini=ini))
    # ---------------- yağmur inişleri
    merkez = K.bina.centroid
    for p in yb_sirasi(K.inisler, (merkez.x, merkez.y)):
        x0 = p[0] - off
        no = next((n for n, q in dur.yb.items() if dist(q, (x0, p[1])) < 15), None)
        if no is None:
            no = 'YB%d' % (len(dur.yb) + 1)
            dur.yb[no] = (round(x0, 1), round(p[1], 1))
        ekle_insert(msp, 'ROTAS-S2-KOLON-YAGMUR', p, 'ROTAS-SIHHI-SEMBOL')
        eng.ekle_alan(Point(p).buffer(9))
        dur.adet['ROTAS-S2-KOLON-YAGMUR'] += 1
    # ---------------- aspiratör (penceresiz ıslak hacim)
    asp = []
    for r in K.rooms:
        if r['tip'] != 'islak' or r['daire'] is None:
            continue
        dis = r['poly'].buffer(50).difference(K.bina).area
        if dis > 300:
            continue
        sf = min(K.saftlar, key=lambda s: s['poly'].distance(r['poly'])) if K.saftlar else None
        if sf is None or sf['poly'].distance(r['poly']) > 200:
            sf = None
        asp.append(dict(r=r, saft=sf))
    gruplar = defaultdict(list)
    for a in asp:
        gruplar[id(a['saft']) if a['saft'] else id(a)].append(a)
    aspirator = []
    for gl in gruplar.values():
        debi = 80 * len(gl)
        ana = max(gl, key=lambda a: a['r']['poly'].area)
        sf = ana['saft']
        if sf:
            q = nearest_points(ana['r']['poly'].buffer(-16), Point(sf['c']))[0]
            pa = (q.x, q.y)
        else:
            pa = tuple(ana['r']['poly'].representative_point().coords[0])
        ekle_insert(msp, 'ROTAS-S2-ASPIRATOR', pa, 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL')
        eng.ekle_alan(Point(pa).buffer(13, cap_style=3))
        dur.adet['ROTAS-S2-ASPIRATOR'] += 1
        aspirator.append(dict(r=ana['r'], p=pa, debi=debi, odalar=[a['r'] for a in gl], saft=sf))
    return dict(pisler=pisler, temiz=temizler, balkon=balkon_s, aspirator=aspirator, ek=ek)


def kat_etiketle(doc, eng, K, kat, dur):
    msp = doc.modelspace()
    islak_u = unary_union([r['poly'].buffer(-2) for r in K.rooms if r['tip'] in ('islak',)])
    n_ok = n_yok = 0
    # P balonları (ıslak hacim dışında, kılavuzlu)
    for ps in kat['pisler']:
        p, kil = balon_yeri(ps['kolon'], eng, islak_u)
        if p is None:
            p, kil = balon_yeri(ps['kolon'], eng, None, mesafeler=(55, 70, 85, 100, 120, 140))
        if p is None:
            p, kil = balon_yeri(ps['kolon'], eng, islak_u, mesafeler=(55, 70, 85, 100, 120, 140, 165, 190), kil_tol=1e9)
        if p is None:
            dur.uyari.append('kat %s %s balonu yerleşmedi' % (K.k, ps['no']))
            continue
        e = ekle_insert(msp, 'ROTAS-S2-KOLON-NO', p, 'ROTAS-SIHHI-KOLON-NO', attr={'NO': ps['no']})
        eng.ekle_alan(daire_poly(p, 28.5))
        msp.add_line(kil.coords[0], kil.coords[-1], dxfattribs={'layer': L_KIL})
        eng.ekle_cizgi(kil)
    # YB balonları (bina dışında)
    dis = box(*K.w).difference(K.bina.buffer(5))
    for no, q in dur.yb.items():
        p0 = (q[0] + K.off, q[1])
        if not any(dist(p0, i) < 3 for i in K.inisler):
            continue
        p, kil = balon_yeri(p0, eng, K.bina.buffer(5), mesafeler=(40, 52, 64, 76, 90, 110, 130))
        if p is None:
            p, kil = balon_yeri(p0, eng, islak_u, mesafeler=(40, 52, 64, 76, 90, 110, 130, 150))
        if p is None:      # kılavuz hat kesebilir (yazı/sembol kesmez)
            p, kil = balon_yeri(p0, eng, islak_u, mesafeler=(40, 52, 64, 76, 90, 110, 130, 150, 175, 200), kil_tol=1e9)
        if p is None:      # son çare: kılavuz denetimsiz (yalnız balon dairesi boş yerde)
            p, kil = balon_yeri(p0, eng, islak_u, mesafeler=(40, 52, 64, 76, 90, 110, 130), kil_tol=None)
        if p is None:
            if os.environ.get('S2_DEBUG'):
                from collections import Counter
                cn = Counter()
                for dd in (40, 64, 90, 130):
                    for kk in range(16):
                        a_ = math.radians(22.5 * kk)
                        pp = (p0[0] + dd * math.cos(a_), p0[1] + dd * math.sin(a_))
                        pg = daire_poly(pp, 28.5)
                        cn['islak' if pg.intersects(islak_u) else ('engel' if eng.carpar(pg) else 'serbest')] += 1
                log('  DEBUG %s %s %s' % (no, p0, dict(cn)))
            dur.uyari.append('kat %s %s balonu yerleşmedi' % (K.k, no))
            continue
        ekle_insert(msp, 'ROTAS-S2-KOLON-NO-YAGMUR', p, 'ROTAS-SIHHI-YAGMUR-NO', attr={'NO': no})
        eng.ekle_alan(daire_poly(p, 28.5))
        msp.add_line(kil.coords[0], kil.coords[-1], dxfattribs={'layer': L_KIL})
        eng.ekle_cizgi(kil)
    # aspiratör yazısı (turuncu, 3 satır h 15)
    for a in kat['aspirator']:
        r = a['r']
        metin = 'Wc Aspiratörü\\P%d m3/h-50 pa\\PØ150 mm' % a['debi']
        mer = []
        bnd = r['poly'].buffer(-30)
        if not bnd.is_empty:
            x0, y0, x1, y1 = bnd.bounds
            for yy in np.linspace(y0, y1, 9):
                for xx in np.linspace(x0, x1, 7):
                    if bnd.contains(Point(xx, yy)):
                        mer.append((xx, yy))
        c = r['poly'].centroid
        mer.sort(key=lambda q: dist(q, (c.x, c.y)))
        e = yazi_yerlestir(msp, eng, metin, 15.0, 'ROTAS-SIHHI-HAVALANDIRMA-YAZI', mer)
        if e is None:      # mahal dışı + kılavuz
            dis_m = []
            for dd in (110, 150, 190, 240, 290, 340, 400):
                for kk in range(16):
                    an = math.radians(22.5 * kk)
                    dis_m.append((a['p'][0] + dd * math.cos(an), a['p'][1] + dd * math.sin(an)))
            e = yazi_yerlestir(msp, eng, metin, 15.0, 'ROTAS-SIHHI-HAVALANDIRMA-YAZI', dis_m)
            if e is not None:
                kb = yazi_kutulari(e)[0]
                q = nearest_points(kb, Point(a['p']))[0]
                msp.add_line(a['p'], (q.x, q.y), dxfattribs={'layer': L_KIL})
                eng.ekle_cizgi(LineString([a['p'], (q.x, q.y)]))
        if e is None:
            dur.uyari.append('kat %s %s aspiratör yazısı yerleşmedi' % (K.k, r['name']))
    # pis su etiketleri: her parça bir etiket (uzun parçalar önce)
    parcalar = []
    for ps in kat['pisler']:
        parcalar += pis_parcalar(ps)
    parcalar = [p for p in parcalar if p['g'].length >= 10.0]      # < 10 cm parça (birleşim arası) etiketlenmez
    parcalar.sort(key=lambda p: -p['g'].length)
    for pc in parcalar:
        e = etiket_dene_pis(msp, eng, pc['g'], pc['cap'], pc['sb'])
        if e is None:
            # kalabalık: kılavuzla dışarı (parça ortasından)
            m = pc['g'].interpolate(0.5, normalized=True)
            e = etiket_halka(msp, eng, (m.x, m.y), {'C1': pc['cap'], 'M1': '%d SB' % pc['sb']}, 'ROTAS-S2-TS-CAP2', L_PCAP)
            for tt in (0.3, 0.7, 0.15, 0.85):
                if e is not None:
                    break
                m = pc['g'].interpolate(tt, normalized=True)
                e = etiket_halka(msp, eng, (m.x, m.y), {'C1': pc['cap'], 'M1': '%d SB' % pc['sb']}, 'ROTAS-S2-TS-CAP2',
                                 L_PCAP)
        if e is None:
            n_yok += 1
            dur.uyari.append('kat %s pis su etiketi yerleşmedi: %s %d SB @ (%.0f, %.0f)' % (
                K.k, pc['cap'], pc['sb'], pc['g'].centroid.x, pc['g'].centroid.y))
        else:
            n_ok += 1
    # temiz su etiketleri: daire girişi, ıslak hacim girişleri, hol ana hattı, kombi
    for dno, ts in kat['temiz'].items():
        islak_d = unary_union([r['poly'] for r in K.rooms if r['daire'] == dno and r['tip'] in ('islak', 'mutfak')]
                              or [Polygon()])
        sec = []
        for z in ts['zincir']:
            L = LineString(z['pts']).length if len(z['pts']) > 1 else 0
            if L < 12:
                continue
            bas_ic = islak_d.contains(Point(z['bas']))
            son_ic = islak_d.contains(Point(z['son']))
            uc = z['uc']
            if z['kok']:
                sec.append((0, z))
            elif uc is not None and uc['kind'] == 'KOMBI':
                sec.append((1, z))
            elif not bas_ic and son_ic:
                sec.append((2, z))
            elif not bas_ic and not son_ic and L >= 80 and uc is None:
                sec.append((3, z))
        for oncelik, z in sorted(sec, key=lambda q: q[0]):
            uc = z['uc']
            if uc is not None and uc['kind'] == 'KOMBI':
                sat = {'C1': '1/2"', 'M1': fmt_mb(MB_S['KOMBI']), 'C2': '1/2"', 'M2': fmt_mb(MB_S['KOMBI'])}
                blok = 'ROTAS-S2-TS-CAP4'
            elif z['sicak'] and z['mb_h'] > 0:
                sat = {'C1': inc(z['mb_s']), 'M1': fmt_mb(z['mb_s']), 'C2': inc(z['mb_h']), 'M2': fmt_mb(z['mb_h'])}
                blok = 'ROTAS-S2-TS-CAP4'
            else:
                sat = {'C1': inc(z['mb_s']), 'M1': fmt_mb(z['mb_s'])}
                blok = 'ROTAS-S2-TS-CAP2'
            # en uzun düz parça üzerinde
            pts = z['pts']
            segs = sorted(zip(pts[:-1], pts[1:]), key=lambda ab: -dist(*ab))
            konan = None
            for a, b in segs[:2]:
                yatay = abs(b[1] - a[1]) < abs(b[0] - a[0])
                for t in (0.5, 0.3, 0.7, 0.15, 0.85):
                    m = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                    konan = etiket_kilavuzlu(msp, eng, m, sat, blok, L_TCAP, hks=(14, 24, 34, 48), yatay_hat=yatay)
                    if konan is not None:
                        break
                if konan is not None:
                    break
            if konan is None:
                a, b = segs[0]
                yatay = abs(b[1] - a[1]) < abs(b[0] - a[0])
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                konan = etiket_halka(msp, eng, m, sat, blok, L_TCAP)
            if konan is None:
                n_yok += 1
                dur.uyari.append('kat %s D%s temiz su etiketi yerleşmedi (%s)' % (K.k, dno, sat.get('M1')))
            else:
                n_ok += 1
        # daire girişi etiketi (G-H parçası): 1 1/4" / n MB
    # EK makine yazıları
    for f in kat['ek']:
        if f['kind'] in ('CM', 'BM'):
            ad = 'Ç.M.' if f['kind'] == 'CM' else 'B.M.'
            mer = [(f['c'][0] + dx, f['c'][1] + dy) for dx, dy in ((0, 40), (0, -40), (55, 0), (-55, 0), (45, 45),
                                                                     (-45, 45), (45, -45), (-45, -45), (0, 70), (0, -70))]
            for dd in (35, 50, 65, 80, 100, 125, 150):
                for kk in range(24):
                    an = math.radians(15.0 * kk)
                    mer.append((f['c'][0] + dd * math.cos(an), f['c'][1] + dd * math.sin(an)))
            e = yazi_yerlestir(msp, eng, ad + ' (EK)', 10.0, 'ROTAS-SIHHI-CIHAZ-YAZI', mer)
            if e is None:
                dur.uyari.append('kat %s %s EK yazısı yerleşmedi' % (K.k, ad))
    log('  etiket: %d yerleşti, %d yerleşmedi' % (n_ok, n_yok))


# ====================================================================== PAFTA, LEJANT, MODEL
def paftalar(doc, eng):
    msp = doc.modelspace()
    for k, (x0, x1) in PAFTA.items():
        msp.add_lwpolyline([(x0, PY0), (x1, PY0), (x1, PY1), (x0, PY1)], close=True, dxfattribs={'layer': 'ROTAS-PAFTA'})
        e = msp.add_text('%s PLANI.........ÖLÇEK: 1 / 50' % KAT_ADI[k],
                         dxfattribs={'layer': 'ROTAS-PAFTA-YAZI', 'height': 40.0, 'style': 'ROTAS-YAZI'})
        e.dxf.insert = (x0 + 538.0, PY0 + 39.0)
        for pg in yazi_kutulari(e):
            eng.ekle_alan(pg)


def lejant(doc, dur):
    msp = doc.modelspace()
    x0, x1 = LEJANT_PAFTA
    msp.add_lwpolyline([(x0, PY0), (x1, PY0), (x1, PY1), (x0, PY1)], close=True, dxfattribs={'layer': 'ROTAS-PAFTA'})
    t = msp.add_text('SIHHİ TESİSAT KAT PLANLARI — LEJANT', dxfattribs={'layer': 'ROTAS-LEJANT', 'height': 30.0,
                                                                     'style': 'ROTAS-YAZI'})
    t.dxf.insert = (x0 + 120, PY1 - 200)
    y = PY1 - 300
    satir = [
        ('hat', L_PIS, 'PİS SU HATTI (PVC, döşemeden; Ø / SB etiketli)'),
        ('hat', L_SOG, 'SOĞUK SU HATTI (PPRC / PEX)'),
        ('hat', L_SIC, 'SICAK SU HATTI (kombiden, soğuğa 5 cm paralel)'),
        ('hat', L_YAG, 'BALKON SÜZGECİ – YAĞMUR İNİŞİ HATTI'),
        ('blok', 'ROTAS-S2-PIS-KOLON', 'PİS SU KOLONU (İNİŞ)'),
        ('blok', 'ROTAS-S2-KOLON-NO', 'PİS SU KOLON NUMARASI (P1 ...)'),
        ('blok', 'ROTAS-S2-KOLON-YAGMUR', 'YAĞMUR SUYU İNİŞİ'),
        ('blok', 'ROTAS-S2-KOLON-NO-YAGMUR', 'YAĞMUR İNİŞİ NUMARASI (YB1 ...)'),
        ('blok', 'ROTAS-S2-YER-SUZGECI', 'YER SÜZGECİ (ıslak hacim, pis su)'),
        ('blok', 'ROTAS-S2-BALKON-SUZGECI', 'BALKON SÜZGECİ (yağmur inişine)'),
        ('blok', 'ROTAS-S2-KURESEL-VANA', 'KÜRESEL VANA (ARA MUSLUK, armatür bağlantısı)'),
        ('blok', 'ROTAS-S2-TEMIZ-GIRIS', 'DAİRE TEMİZ SU GİRİŞİ (sayaçlar kolon şemasında, zemin)'),
        ('blok', 'ROTAS-S2-ASPIRATOR', 'WC ASPİRATÖRÜ (penceresiz ıslak hacim, şafta)'),
        ('blok', 'ROTAS-S2-MAKINE-EK', 'ÇAMAŞIR / BULAŞIK MAKİNESİ BAĞLANTISI (mimaride yoksa EK)'),
    ]
    h = msp.add_text('SEMBOL', dxfattribs={'layer': 'ROTAS-LEJANT', 'height': 15.0, 'style': 'ROTAS-YAZI'})
    h.dxf.insert = (x0 + 120, y + 40)
    h = msp.add_text('AÇIKLAMA', dxfattribs={'layer': 'ROTAS-LEJANT', 'height': 15.0, 'style': 'ROTAS-YAZI'})
    h.dxf.insert = (x0 + 330, y + 40)
    h = msp.add_text('ADET', dxfattribs={'layer': 'ROTAS-LEJANT', 'height': 15.0, 'style': 'ROTAS-YAZI'})
    h.dxf.insert = (x0 + 1500, y + 40)
    for tur, ad, ack in satir:
        if tur == 'hat':
            msp.add_lwpolyline([(x0 + 120, y), (x0 + 280, y)], dxfattribs={'layer': ad})
        else:
            attr = {'NO': 'P1'} if ad == 'ROTAS-S2-KOLON-NO' else ({'NO': 'YB1'} if ad == 'ROTAS-S2-KOLON-NO-YAGMUR' else None)
            ekle_insert(msp, ad, (x0 + 200, y), 'ROTAS-LEJANT', attr=attr)
            a = msp.add_text(str(dur.adet.get(ad, 0)), dxfattribs={'layer': 'ROTAS-LEJANT', 'height': 12.0,
                                                                  'style': 'ROTAS-YAZI'})
            a.dxf.insert = (x0 + 1500, y - 6)
        t = msp.add_text(ack, dxfattribs={'layer': 'ROTAS-LEJANT', 'height': 12.0, 'style': 'ROTAS-YAZI'})
        t.dxf.insert = (x0 + 330, y - 6)
        y -= 80
    y -= 40
    notlar = [
        'NOTLAR:',
        '1. Pis su: kolon ıslak hacim köşesinde duvar yüzünden 8 cm; toplama hattı duvar dibinden, armatürler 45° + dik',
        '   kısa branşmanla (dallı). Çap: ≤8 SB Ø50, 11-16 SB Ø70, klozet ve ≥21 SB Ø100 (SB: LV 2, WC 10, DUŞ 7, YS 2, ÇM/BM/EV 4).',
        '2. Temiz su: daire girişi merdiven holünde kapı yanında; hol/koridorda koridor ortasından, ıslak hacimde mahal',
        '   ortasından; sıcak su kombiden daire içinde, soğuğa 5 cm paralel. MB: LV 0,75/0,75 DUŞ 2,5/2,5 EV 1/1 WC 0,5',
        '   ÇM 1,5 BM 1,5 KOMBİ 0,5. Çap: ≤1 MB 1/2", ≤2,5 MB 3/4", ≤8,5 MB 1", ≤12 MB 1 1/4".',
        '3. Balkon süzgeçleri yalnız balkondaki yağmur inişine bağlanır (pis suya bağlanmaz).',
        '4. Su sayaçları kolon şemasında zemin bandında, şebeke girişindedir (kat planında sayaç yoktur).',
        '5. (EK) işaretli armatür / süzgeç mimaride yoktur, kural gereği eklenmiştir.',
    ]
    for n in notlar:
        t = msp.add_text(n, dxfattribs={'layer': 'ROTAS-LEJANT', 'height': 12.0, 'style': 'ROTAS-YAZI'})
        t.dxf.insert = (x0 + 120, y)
        y -= 26


def model_yaz(Ks, katlar, dur):
    daireler = []
    for K in Ks:
        kat = katlar[K.k]
        for p, dno in K.tohum:
            ts = kat['temiz'].get(dno)
            z = lambda q: [round(q[0] - K.off, 1), round(q[1], 1)]
            d = dict(no='D%d' % dno, kat=KATLAR.index(K.k))
            if ts:
                d['giris'] = dict(x=z(ts['G'])[0], y=z(ts['G'])[1], mahal='merdiven holü (kapı yanı)')
                if ts['kombi']:
                    ko = next((f for f in K.fx if f['kind'] == 'KOMBI' and f['c'] == ts['kombi']), None)
                    d['kombi'] = dict(x=z(ts['kombi'])[0], y=z(ts['kombi'])[1],
                                      mahal=ko['oda']['name'] if ko and ko['oda'] else '')
                d['temiz_su_mb'] = round(ts['toplam'], 2)
                d['temiz_su_cap'] = inc(ts['toplam'])
            ih = []
            for r in K.rooms:
                if r['daire'] != dno or r['tip'] not in ('islak', 'mutfak'):
                    continue
                ps = next((q for q in kat['pisler'] if q['oda'] is r), None)
                fo = [f for f in K.fx if f['oda'] is r and f['kind'] != 'KOMBI']
                ys = next((f for f in fo if f['kind'] == 'YS'), None)
                h = dict(ad=r['name'], poligon=[z(q) for q in r['poly'].exterior.coords],
                         armaturler=[dict(tip=f['kind'], x=z(f['c'])[0], y=z(f['c'])[1], ek=bool(f.get('ek')))
                                     for f in fo if f['kind'] != 'YS'],
                         suzgec=dict(x=z(ys['c'])[0], y=z(ys['c'])[1], ek=bool(ys.get('ek'))) if ys else None,
                         kolon=ps['no'] if ps else None)
                a = next((a for a in kat['aspirator'] if r in a['odalar']), None)
                if a:
                    h['aspirator'] = dict(x=z(a['p'])[0], y=z(a['p'])[1], debi=80,
                                          saft=('Ş@%.0f,%.0f' % tuple(z(a['saft']['c']))) if a['saft'] else None)
                ih.append(h)
            d['islak_hacimler'] = ih
            bl = []
            for b in kat['balkon']:
                if b['r']['daire'] == dno:
                    no = next((n for n, q in dur.yb.items() if dist(q, (b['ini'][0] - K.off, b['ini'][1])) < 15), None)
                    bl.append(dict(poligon=[z(q) for q in b['r']['poly'].exterior.coords], suzgec=dict(x=z(b['s'])[0], y=z(b['s'])[1]),
                                   yagmur_inisi=no))
            d['balkonlar'] = bl
            daireler.append(d)
    kolonlar = []
    for no, kv in sorted(dur.kolonlar.items(), key=lambda q: int(q[0][1:])):
        sbk = [kv['sb_kat'].get(k, 0) for k in KATLAR]
        top = sum(sbk)
        wc = any('WC' in v for v in kv.get('armatur', {}).values())
        kolonlar.append(dict(no=no, x=kv['x'], y=kv['y'], katlar=[KATLAR.index(k) for k in kv['katlar']], rogar=None,
                             sb_kat=sbk, sb_toplam=top, cap='Ø100' if (wc or top >= 21) else pis_cap(top, False),
                             mahal=kv['oda'], armatur_sirasi_sema=kv.get('armatur', {}).get(kv['katlar'][0], [])))
    m = dict(
        proje=dict(ad='METRA MİMARLIK 4739/4 (new_block)', kat_adlari=[KAT_ADI[k] for k in KATLAR],
                   kat_ofset=[M2.M.OFF[k] for k in KATLAR], temel_ofset=-2629, bina_yuksekligi_m=9.0,
                   depo=dict(yer='çatı', hacim_m3=3.0 + 0.5 * max(0, len(daireler) - 10)), hidrofor=False,
                   kaynak='motor/sihhi2/plan.py', tarih=time.strftime('%d.%m.%Y %H:%M')),
        yuk_tablosu=dict(MB_S), yuk_tablosu_sicak=dict(MB_H), sb_tablosu=dict(SB), daireler=daireler, kolonlar=kolonlar,
        rogarlar=[], yagmur=[dict(no=n, x=q[0], y=q[1], cap='Ø70') for n, q in sorted(dur.yb.items(), key=lambda q: int(q[0][2:]))],
        temiz_su=dict(sebeke=None, ana_sayac_cap=inc(sum(d.get('temiz_su_mb', 0) for d in daireler)),
                      daire_mb={d['no']: d.get('temiz_su_mb') for d in daireler},
                      daire_cap={d['no']: d.get('temiz_su_cap') for d in daireler}),
        hav_saftlari=[], uyarilar=dur.uyari)
    sa = {}
    for K in Ks:
        for a in katlar[K.k]['aspirator']:
            if not a['saft']:
                continue
            key = (round(a['saft']['c'][0] - K.off), round(a['saft']['c'][1]))
            s = sa.setdefault(key, dict(no='Ş%d' % (len(sa) + 1), x=key[0], y=key[1], daireler=[], debi=0, fan=None))
            s['daireler'] += sorted({'D%s' % r['daire'] for r in a['odalar']})
            s['debi'] += a['debi']
    for s in sa.values():
        s['fan'] = 'ÇATI TİPİ FAN %d m3/h' % s['debi']
    m['hav_saftlari'] = list(sa.values())
    with open(CIKIS_JSON, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    return m


def main(argv):
    t0 = time.time()
    os.makedirs(CIKIS, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    doc = belge()
    eng = Engel()
    mimari_kopyala(doc, eng)
    paftalar(doc, eng)
    A = M2.kayitlar()
    Ks, katlar = [], {}
    dur = Durum()
    onceki = None
    for k in ('Z', '2', '1'):          # 1. kat en son: alt ve üst katın kolon eksenlerine oturur
        t1 = time.time()
        K = M2.Kat(A, k)
        K.kb = M2.MB.kat_analiz(A, M2.pencere(k), k)
        log('kat %s mimari: %.1f s' % (k, time.time() - t1))
        katlar[k] = kat_ciz(doc, eng, K, dur, onceki)
        onceki = [(kv['x'], kv['y']) for kv in dur.kolonlar.values()]
        Ks.append(K)
    Ks.sort(key=lambda K: KATLAR.index(K.k))
    for K in Ks:
        kat_etiketle(doc, eng, K, katlar[K.k], dur)
    lejant(doc, dur)
    m = model_yaz(Ks, katlar, dur)
    aud = doc.audit()
    doc.saveas(CIKIS_DXF)
    log('DXF: %s (audit hata %d) — %d kolon, %d YB, %.0f s' % (CIKIS_DXF, len(aud.errors), len(dur.kolonlar), len(dur.yb),
                                                            time.time() - t0))
    for u in dur.uyari:
        log('  UYARI:', u)


if __name__ == '__main__':
    main(sys.argv[1:])
