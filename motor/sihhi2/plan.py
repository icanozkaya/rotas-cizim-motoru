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
D_DUVAR = 8.0          # pis su toplama hattı / kolon: duvar yüzünden (≤ 9)
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
    b.add_circle((0, 0), 10.0)
    h = b.add_hatch(color=256)
    h.paths.add_edge_path().add_arc((0, 0), 10.0, 0, 360)
    b.add_circle((0, 0), 13.0)
    for s in (-1, 1):
        b.add_line((s * 13, 0), (s * 18, 0))
        b.add_lwpolyline([(s * 18, -3), (s * 18, 3)])
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
    elif e.dxftype() == 'MTEXT':
        pg = D.yazi_kutusu(e)
        if pg is not None:
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
def halka(poly, d=D_DUVAR):
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


def pah_45(pts, h=8.0):
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        u1, u2 = birim(a, b), birim(b, c)
        if abs(u1[0] * u2[0] + u1[1] * u2[1]) < 0.05 and dist(a, b) > h and dist(b, c) > h:
            out += [(b[0] - u1[0] * h, b[1] - u1[1] * h), (b[0] + u2[0] * h, b[1] + u2[1] * h)]
        else:
            out.append(b)
    return temiz(out + [pts[-1]])


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
    """kolon seçimi + kollar + branşmanlar. kolon_onceki: alt kattaki kolon noktaları (bu katın koordinatında)"""
    poly = oda['poly']
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
        ang, cr = kose_aci(a, b, c)
        if cr >= 0 and 60 <= ang <= 120 and dist(a, b) > 15 and dist(b, c) > 15:      # sol dönüş (ccw) = dışbükey
            sb = ring.project(Point(b))
            for t in (0, 10, 20, 30, 40):
                for yon in (1, -1):
                    if t == 0 and yon < 0:
                        continue
                    if t > 0 and ((yon > 0 and t > dist(b, c) - 15) or (yon < 0 and t > dist(a, b) - 15)):
                        continue
                    s = (sb + yon * t) % L
                    adaylar.append((s, t))
    out = []
    for s, t in adaylar:
        p = tuple(ring.interpolate(s).coords[0])
        pt = Point(p)
        if any(c.distance(pt) < 12 for c in K.cols):
            continue
        if any(sf['poly'].buffer(6).contains(pt) for sf in K.saftlar):
            continue
        if K.kapi_u.distance(pt) < 35:
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
        if mx > 280:
            pu += 20 * (mx - 280)
        if any(sf['poly'].distance(pt) < 60 for sf in K.saftlar):
            pu -= 40
        if kolon_onceki and any(dist(p, q) < 20 for q in kolon_onceki):
            pu -= 400
        out.append((pu, s, p))
    if not out:
        return None
    out.sort()
    pu, s0, p0 = out[0]
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
        kollar[yon] = LineString(pah_45(pts))
    # branşmanlar
    br = []
    for yon, lst in yonler.items():
        kol = kollar.get(yon)
        for d, sf, f in lst:
            c = f['c']
            if kol is None:                          # armatür kolonun dibinde
                br.append(dict(f=f, pts=temiz([c, p0]), t=0.0, kol=None))
                continue
            t = kol.project(Point(c))
            F = tuple(kol.interpolate(t).coords[0])
            h = dist(c, F)
            if h < 6.0 or t < 6.0:
                pts = [c, F]
                tq = t
            else:
                nrm = birim(F, c)
                Pp = (F[0] + nrm[0] * 5.0, F[1] + nrm[1] * 5.0)
                tq = max(0.0, t - 5.0)
                Q = tuple(kol.interpolate(tq).coords[0])
                pts = [c, Pp, Q]
            br.append(dict(f=f, pts=temiz(pts), t=tq, kol=yon))
    return dict(kolon=p0, kollar=kollar, br=br, ring=ring, oda=oda, puan=pu)


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
