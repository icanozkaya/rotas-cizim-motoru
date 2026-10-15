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
from shapely.affinity import translate as shapely_translate

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import mimari2 as M2  # noqa: E402
KOK = M2.KOK
sys.path.insert(0, KOK + '/motor/deneme/denetim')
import denetle as D  # noqa: E402
import etiket_kontrol as EK  # noqa: E402
import besleme as BES  # noqa: E402
sys.path.insert(0, KOK + '/motor/kontrolor')
import kutu as KUTU  # noqa: E402

CIKIS = KOK + '/proje/denemeler/sihhi2'
CIKIS_DXF = CIKIS + '/NB_SIHHI_KAT_PLANLARI.dxf'
CIKIS_JSON = CIKIS + '/sihhi_model.json'
MIMARI_DXF = '/tmp/claude-0/uu/new_block_mimari.dxf'
TMP = '/tmp/claude-0/s2'

KATLAR = ['Z', '1', '2']
KAT_ADI = {'Z': 'ZEMİN KAT', '1': '1. KAT', '2': '2. KAT'}
PAFTA = {'Z': (252513.0, 254578.0), '1': (254578.0, 256617.0), '2': (256617.0, 258656.0)}
CATI_PAFTA = (258656.0, 260714.0)
PY0, PY1 = -444050.0, -441150.0
CATI_OFF = 6143.0            # çatı paftası mimari ötelemesi (zemin çerçevesine göre)

# ---- kullanıcının tasarım seçimleri (new_block MTY çizimi): kolon yeri/numarası, rögar ataması, ÇM/BM yeri.
# Kural (kullanıcı): bunlar kafaya göre değiştirilmez. Üretim: tasarim_cikar.py
with open(BURASI + '/tasarim_new_block.json', encoding='utf-8') as _f:
    TASARIM = json.load(_f)
KOLON_SABIT = {k: tuple(v) for k, v in TASARIM['kolonlar'].items()}
# kullanıcının kolon bloğu: ekleme noktası (KOLON_SABIT) = borunun BAĞLANDIĞI nokta; sembolün (STM-PISSU-KOLON r 10)
# MERKEZİ ondan 15,9 cm içeride (15.10 (D): hat kolon sembolünün İÇİNE girmez, çevresinde biter; eskiden sembol bağlantı
# noktasına konuyordu -> P2/P5 'mek. havl.' şaftına, P3/P6 betonarmeye biniyordu)
KOLON_MERKEZ = {k: tuple(TASARIM.get('kolon_merkez', {}).get(k, v)) for k, v in KOLON_SABIT.items()}
KOLON_R = 10.0               # kolon sembolü dış çemberi (kullanıcının STM-PISSU-KOLON r 10)
MARJ = 1.5                   # etiket yazı kutusu çevresi boşluk (cm)

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
    'ROTAS-SEMBOL-KILAVUZ': (9, 'Continuous', 9), 'ROTAS-PAFTA': (144, 'Continuous', 35),
    'ROTAS-PAFTA-YAZI': (7, 'Continuous', 25), 'ROTAS-SIHHI-CATI': (3, 'Continuous', 18),
    'ROTAS-SIHHI-CATI-YAZI': (7, 'Continuous', 13),
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


def sbf(f):
    """armatür SB yükü (bağlantı sözde-armatürü: komşu ıslak hacmin toplamı)"""
    return f.get('sb', SB.get(f['kind'], 0))


def wcf(f):
    return f['kind'] == 'WC' or bool(f.get('wc'))


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


def kolon_merkezi(no, off):
    q = KOLON_MERKEZ[no]
    return (q[0] + off, q[1])


def kolon_cember_noktasi(no, off):
    """bağlantı noktası -> merkez doğrultusunda dış çember (r 10) üstündeki nokta: hat burada biter"""
    c = kolon_merkezi(no, off)
    b = (KOLON_SABIT[no][0] + off, KOLON_SABIT[no][1])
    if dist(b, c) < 0.5:
        return b
    u = birim(c, b)
    return (c[0] + u[0] * KOLON_R, c[1] + u[1] * KOLON_R)


def kolon_aci(no):
    """kelepçe kolu bağlantı noktasına bakar (derece)"""
    c, b = KOLON_MERKEZ[no], KOLON_SABIT[no]
    return math.degrees(math.atan2(b[1] - c[1], b[0] - c[0])) if dist(b, c) > 0.5 else 0.0


def kolon_baglantisi(ps, off):
    """15.10 (D): pis su hattı kolon sembolünün İÇİNE girmez. Kolondan (bağlantı noktası C) başlayan omurga /
    branşman, C'den sembolün dış çemberine (r 10) kelepçe doğrultusunda kısa uzatılır ve orada biter; t'ler kayar."""
    no = ps.get('no')
    if ps.get('misafir') or no not in KOLON_MERKEZ:
        return
    C = (KOLON_SABIT[no][0] + off, KOLON_SABIT[no][1])
    E = kolon_cember_noktasi(no, off)
    ek = dist(C, E)
    ps['merkez'] = kolon_merkezi(no, off)
    ps['cember'] = E
    if ek < 0.5:
        return
    for yon, kol in list(ps['kollar'].items()):
        cs = list(kol.coords)
        if dist(cs[0], C) <= 1.0:
            ps['kollar'][yon] = LineString(temiz([E] + cs))
            for b in ps['br']:
                if b['kol'] == yon:
                    b['t'] += ek
    for b in ps['br']:
        if b['pts'] and dist(b['pts'][-1], C) <= 1.0 and (b['kol'] is None or b['kol'] not in ps['kollar']
                                                         or b.get('t', 1.0) <= 0.01):
            b['pts'] = temiz(list(b['pts']) + [E])


def kolon_ici_kirp(g, merkezler, r=KOLON_R):
    """hat geometrisi (LineString) kolon çemberlerinin içinden geçmez: iç kısım kırpılır -> [LineString]"""
    out = [g]
    for c in merkezler:
        cc = Point(c).buffer(r - 0.05, resolution=32)
        yeni = []
        for h in out:
            if not h.intersects(cc):
                yeni.append(h)
                continue
            d = h.difference(cc)
            yeni += [q for q in getattr(d, 'geoms', [d]) if q.geom_type == 'LineString' and q.length > 0.3]
        out = yeni
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

    # etiket / balon için ek yasak alanlar (duvar katısı, mimari tarama, armatür kutusu, asansör, merdiven)
    def yasak_ekle(self, g, tur):
        if g is None or g.is_empty:
            return
        d = self.__dict__.setdefault('_yasak', {})
        d.setdefault(tur, []).append(g)
        self.__dict__.setdefault('_yasak_t', {})[tur] = None

    def yasakta(self, pg, tur, tol=0.5):
        d = self.__dict__.get('_yasak', {})
        L = d.get(tur)
        if not L:
            return False
        tt = self.__dict__.setdefault('_yasak_t', {})
        if tt.get(tur) is None:
            tt[tur] = STRtree(L)
        for i in tt[tur].query(pg):
            g = L[i]
            if g.intersects(pg) and g.intersection(pg).area > tol:
                return True
        return False

    def duvar_orani(self, pg):
        d = self.__dict__.get('_yasak', {}).get('duvar')
        if not d:
            return 0.0
        tt = self.__dict__.setdefault('_yasak_t', {})
        if tt.get('duvar') is None:
            tt['duvar'] = STRtree(d)
        a = sum(d[i].intersection(pg).area for i in tt['duvar'].query(pg))
        return a / max(pg.area, 1e-6)

    def pis_yasak(self, pg, diger=None):
        """pis su etiketi yasağı (kontrolör tur 3 R1, kullanıcı çizimi): yazı beton taraması / asansör / armatür / ortak
        alan / başka daire üstüne binmez; duvar çizgileri üstüne en çok yarısı kadar binebilir (kullanıcı wc-lvb.
        etiketini duvar üstüne koyuyor)"""
        if self.yasakta(pg, 'tarama') or self.yasakta(pg, 'asansor') or self.yasakta(pg, 'armatur') or \
                self.yasakta(pg, 'ortak'):
            return True
        if diger is not None and not diger.is_empty and pg.intersection(diger).area > 0.5:
            return True
        return self.duvar_orani(pg) > 0.5

    def etiket_carpar(self, pg, tur='etiket'):
        """etiket yazı kutusu: marjlı kutu engellere + yasak alanlara"""
        return self.carpar(pg.buffer(MARJ, join_style=2)) or self.yasakta(pg, tur) or self.yasakta(pg, 'armatur') \
            or self.yasakta(pg, 'ortak')

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
    b.add_attdef('NO', (0, 0), dxfattribs={'height': 5.0, 'style': 'ROTAS-YAZI', 'flags': 1})   # görünmez kolon no
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
    for ad, s, yon in (('ROTAS-S2-PS-CAP-U', 1, 1), ('ROTAS-S2-PS-CAP-A', -1, 1),
                       ('ROTAS-S2-PS-CAP-UL', 1, -1), ('ROTAS-S2-PS-CAP-AL', -1, -1)):
        b = B.new(ad)
        b.add_line((0, 0), (0, 16 * s))
        b.add_line((0, 16 * s), (34 * yon, 16 * s))
        ycap = 18.0 if s > 0 else -14.0
        ysb = 4.0 if s > 0 else -28.0
        x0 = 2.0 if yon > 0 else -32.0          # L: kanca sola, yazı kancanın üstünde sola doğru (okuma yönü aynı)
        b.add_attdef('CAP', (x0, ycap), dxfattribs={'height': ETIKET_H, 'style': 'ROTAS-YAZI', 'width': 0.8})
        b.add_attdef('SB', (x0, ysb), dxfattribs={'height': ETIKET_H, 'style': 'ROTAS-YAZI', 'width': 0.8})
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
            if a.is_invisible:
                continue
            pg = EK.glif_kutusu(a) or D.yazi_poligonu(a)
            if pg is not None and pg.is_valid:
                out.append(pg)
            try:
                pk = KUTU.yazi_kutusu(a)
                if pk is not None and pk.is_valid and pk.area > 0:
                    out.append(pk)
            except Exception:
                pass
    else:                                   # gerçek glif kutusu (yazı tipi ölçüsü, döndürme dahil)
        pg = EK.glif_kutusu(e) or D.yazi_poligonu(e)
        if pg is not None and pg.is_valid:
            out.append(pg)
        if e.dxftype() == 'MTEXT' and pg is not None and not e.dxf.get('rotation', 0) and \
                pg.bounds[2] - pg.bounds[0] > pg.bounds[3] - pg.bounds[1]:
            # sütun genişliğiyle KAYAN satırlar ('148m² / Döş. / Seramik'): glif kutusu tek satır sayar; yükseklik
            # kontrolör kutusundan (kaydırma dahil), genişlik glif kutusundan
            try:
                pk = KUTU.yazi_kutusu(e)
                if pk is not None and pk.is_valid and pk.bounds[1] < pg.bounds[1] - 1:
                    out.append(box(pg.bounds[0], pk.bounds[1], pg.bounds[2], pg.bounds[3]))
            except Exception:
                pass
        if e.dxftype() != 'MTEXT':          # kontrolör kutusu da (TEXT alt uzantı); MTEXT'te sütun genişliği değil glif
            try:
                pk = KUTU.yazi_kutusu(e)
                if pk is not None and pk.is_valid and pk.area > 0:
                    out.append(pk)
            except Exception:
                pass
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
        for k, (x0, x1) in list(PAFTA.items()) + [('C', CATI_PAFTA)]:
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
            if e.dxftype() == 'HATCH':          # duvar / kolon taraması: etiket ve balon konmaz
                for pth in e.paths:
                    try:
                        vs = [(v[0], v[1]) for v in pth.vertices] if hasattr(pth, 'vertices') else \
                             [(ed.start[0], ed.start[1]) for ed in pth.edges if hasattr(ed, 'start')]
                        if len(vs) >= 3:
                            pg = Polygon(vs).buffer(0)
                            if pg.area > 50:
                                eng.yasak_ekle(pg, 'etiket')
                                eng.yasak_ekle(pg, 'balon')
                                eng.yasak_ekle(pg, 'tarama')
                    except Exception:
                        pass
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


def pis_su_oda(K, oda, fx, kolon_onceki, yasak, sabit=None):
    """iki halka denenir: (1) eski mahal poligonu (mutfakta tezgâh altı +22), (2) armatür çentikleri kapatılmış poligon
    (mutfakta tezgâh dahil, duvar dibine kadar). Doğrulanan en iyi puanlı sonuç.
    sabit: kullanıcının kolon ekseni (tasarım) — kolon buraya oturur, kollar halkadan kısa ayakla bağlanır."""
    sonuclar = []
    for p_ in _pis_poligonlar(K, oda):
        r_ = _pis_su_halka(K, oda, fx, kolon_onceki, yasak, p_, sabit=sabit)
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


def _pis_su_halka(K, oda, fx, kolon_onceki, yasak, poly, sabit=None):
    """kolon seçimi + kollar + branşmanlar (verilen mahal poligonunun halkasında)"""
    hg = halka(poly)
    ring = hg.exterior
    if not ring.is_ccw:
        ring = LineString(list(ring.coords)[::-1])
    L = ring.length
    if sabit is not None:
        a_ = _pis_omurga(K, oda, fx, sabit)
        b_ = _pis_sabit(K, oda, fx, ring, sabit)
        ad = [q for q in (a_, b_) if q is not None]
        if not ad:
            return None
        ok = [q for q in ad if not q.get('dogrulanmadi')]
        # omurga (kullanıcı tarzı) tercih: halka çözümü ancak belirgin kısaysa
        if a_ is not None and not a_.get('dogrulanmadi'):
            return a_
        return min(ok or ad, key=lambda q: q['puan'])
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
            w = 2.0 if wcf(f) else 1.0
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


def kol_bol(kol, noktalar, tol=1.0):
    """kol polyline'ına, üzerindeki noktaları köşe olarak ekle"""
    cs = list(kol.coords)
    ek = []
    for q in noktalar:
        if kol.distance(Point(q)) <= tol and min(dist(q, c) for c in cs) > 0.05:
            ek.append((kol.project(Point(q)), tuple(q)))
    if not ek:
        return cs
    acc = [0.0]
    for a, b in zip(cs[:-1], cs[1:]):
        acc.append(acc[-1] + dist(a, b))
    hep = sorted([(t, c) for t, c in zip(acc, cs)] + ek, key=lambda q: q[0])
    return [c for _, c in hep]


def _omurga_adaylari(C, T):
    """C (kolon) -> T (en uzak armatür) arası 0/45/90 açılı 1–2 parçalı omurga adayları"""
    dx, dy = T[0] - C[0], T[1] - C[1]
    sx, sy = math.copysign(1, dx), math.copysign(1, dy)
    m = min(abs(dx), abs(dy))
    out = []
    if abs(dx) < 2 or abs(dy) < 2:
        out.append([C, T])
        return out
    out.append([C, (T[0], C[1]), T])
    out.append([C, (C[0], T[1]), T])
    D1 = (C[0] + sx * m, C[1] + sy * m)
    out.append([C, D1, T])
    D2 = (T[0] - sx * m, T[1] - sy * m)
    out.append([C, D2, T])
    return [temiz(q) for q in out]


def _brans_omurga(sp, c, akis_kolona=True):
    """armatür c'den omurgaya: dik + son 5x5 cm 45° (akış kolona doğru). Dönüş (pts, t) ya da None"""
    cs = list(sp.coords)
    best = None
    acc = 0.0
    for a, b in zip(cs[:-1], cs[1:]):
        L = dist(a, b)
        u = birim(a, b)
        tt = (c[0] - a[0]) * u[0] + (c[1] - a[1]) * u[1]
        if -1.0 <= tt <= L + 1.0:
            tt = min(max(tt, 0.0), L)
            F = (a[0] + u[0] * tt, a[1] + u[1] * tt)
            h = dist(c, F)
            if best is None or h < best[2]:
                best = (acc + tt, F, h, u)
        acc += L
    if best is None:
        return None
    t, F, h, u = best
    if h < 6.0:
        return [c, F], t
    if t < 7.0:                       # kolon dibinde: dik ayak doğrudan kolon noktasına
        return [c, F, cs[0]] if dist(F, cs[0]) > 0.5 else [c, cs[0]], 0.0
    n = birim(F, c)
    tj = max(t - 5.0, 0.0)
    J = tuple(sp.interpolate(tj).coords[0])                 # omurga ÜZERİNDE kolona doğru 5 cm
    if dist(J, F) < 4.0 or abs(dist(J, F) - 5.0) > 0.5:     # köşe dönüşü: 45° yerine doğrudan dik ayak
        return [c, F], t
    P = (F[0] + n[0] * 5.0, F[1] + n[1] * 5.0)
    return [c, P, J], tj


def _pis_omurga(K, oda, fx, C):
    """kullanıcı topolojisi: kolondan en uzak armatüre TEK düz omurga (0/45/90; L ya da 45°+düz), diğer armatürler
    omurgaya dik kısa branşman + 45° bağlantı. Birden çok aday omurga denenir; en kısa/temiz olanı."""
    ic = unary_union([q.buffer(3, join_style=2) for q in _pis_poligonlar(K, oda)])
    cs_ = [f for f in fx]
    if not cs_:
        return None
    iyi = None
    # küçük duş / wc-duş (D3/D5/D8, P9): kullanıcı hattı kolondan duvar dibinden iner, alt duvar boyunca lavaboya gider
    # (kontrolör tur 3 K1: çapraz hat süzgecin üstünden geçiyordu)
    kucuk_dus = 'duş' in oda['name'] and oda['poly'].area < 2.0e4
    hedefler = sorted(cs_, key=lambda f: -dist(C, f['c']))[:3]
    for T in hedefler:
        for pts in _omurga_adaylari(C, T['c']):
            eksenli = all(abs(a[0] - b[0]) < 0.5 or abs(a[1] - b[1]) < 0.5 for a, b in zip(pts[:-1], pts[1:]))
            if len(pts) > 2 and eksenli:
                pts = pah_45(pts)
            sp = LineString(pts)
            if sp.length < 1:
                continue
            ceza = 0.0
            ic30 = oda['poly'].buffer(-30, join_style=2)
            if not ic30.is_empty:                  # oda ortasından uzun çapraz hat yok (kontrolör T03: > 100 cm)
                Lic = sp.intersection(ic30).length
                if Lic > 85:
                    ceza += 8.0 * (Lic - 85)
            c_ic = ceza
            muaf = min(Point(C).distance(oda['poly']) + 6.0, sp.length * 0.5)
            ic_kisim = substring(sp, muaf, sp.length)
            dis_kisim = ic_kisim.difference(ic)
            if kucuk_dus:          # lavabo tezgâhı mahalden kesik: armatüre son yaklaşım (≤ 40 cm) cezasız
                dis_kisim = dis_kisim.difference(Point(T['c']).buffer(40).intersection(oda['poly'].envelope))
            ceza += 40.0 * dis_kisim.length
            c_dis = ceza - c_ic
            br = []
            for f in cs_:
                if f is T:
                    br.append(dict(f=f, pts=[f['c']], t=sp.length, kol=1))
                    continue
                r_ = _brans_omurga(sp, f['c'])
                if r_ is None:                     # armatür omurgaya bağlanamıyor: aday geçersiz (armatür düşmesin)
                    ceza += 100000
                    continue
                bp, t = r_
                bp = temiz(bp)
                L = LineString(bp).length if len(bp) > 1 else 0.0
                if L > 110:
                    ceza += 6 * (L - 110)
                if len(bp) > 1:
                    ceza += 20.0 * LineString(bp).difference(ic).length
                br.append(dict(f=f, pts=bp, t=max(0.0, t), kol=1))
            hat = [sp] + [LineString(b['pts']) for b in br if len(b['pts']) > 1]
            for i in range(len(hat)):
                for j in range(i + 1, len(hat)):
                    if hat[i].crosses(hat[j]):
                        ceza += 500
            c_tk = _tekne_cezasi(K, oda, sp, br, T)
            ceza += c_tk
            boy = sp.length + sum(LineString(b['pts']).length for b in br if len(b['pts']) > 1)
            puan = boy + ceza
            if os.environ.get('S2_DEBUG_OMURGA'):
                log('   OM', T['kind'], [tuple(round(v) for v in c) for c in pts], round(boy), round(ceza), 'ic', round(c_ic),
                    'dis', round(c_dis), 'tekne', round(c_tk), [(b['f']['kind'], [tuple(round(v) for v in c) for c in b['pts']]) for b in br])
            if iyi is None or puan < iyi['puan']:
                iyi = dict(kolon=C, kollar={1: sp}, br=br, ring=None, oda=oda, puan=puan, dogrulanmadi=ceza >= 500)
    return iyi


def _tekne_cezasi(K, oda, sp, br, T):
    """tekne içinden yalnız teknenin KENDİ gider branşmanı geçer (kontrolör tur 4 E1): omurganın / başka armatür
    branşmanının tekne içindeki boyu 40/cm cezalı. Omurga teknenin kendi giderinde bitiyorsa giderden tekne kenarına
    kadarki kısım (≤ kısa kenarın yarısı + 5) serbest. Tekne kasası 6 cm içeriden ölçülür (duvar dibi hattı tekne kenarından
    geçebilir, kullanıcı gibi); başka armatürün birleşimi tekne içinde olamaz."""
    ceza = 0.0
    for f_, pg in getattr(K, 'tekneler', []):
        if not pg.intersects(oda['poly'].buffer(10)):
            continue
        ti = pg.buffer(-6, join_style=2)          # dış kasa çizgisi duvara dayalı: duvar dibi hattı (≤ 5 cm) serbest
        if ti.is_empty:
            continue
        L = sp.intersection(ti).length
        if T is f_:
            x0, y0, x1, y1 = pg.bounds
            L = max(0.0, L - (max(ti.exterior.distance(Point(f_['c'])), 0.5 * min(x1 - x0, y1 - y0)) + 5.0))
        ceza += 40.0 * L
        for b in br:
            if b['f'] is f_ or len(b['pts']) < 2:
                continue
            ceza += 40.0 * LineString(b['pts']).intersection(ti).length
            if ti.contains(Point(b['pts'][-1])):
                ceza += 200.0
    return ceza


def _pis_sabit(K, oda, fx, ring, C):
    """kolon kullanıcının ekseninde (C): halkada C'nin izdüşümü ve ±10/20 cm komşuları denenir; halka noktasından
    C'ye kısa dik ayak. Doğrulanan, en kısa toplam boylu sonuç."""
    s_c = ring.project(Point(C))
    L = ring.length
    iyi = None
    for ds in (0, 10, -10, 20, -20, 35, -35):
        s0 = (s_c + ds) % L
        p0 = tuple(ring.interpolate(s0).coords[0])
        r_ = _pis_kur(ring, fx, s0, p0)
        if r_ is None:
            continue
        kollar, br = r_
        if dist(p0, C) > 1.0:
            kollar, br, p1 = _ayak_ekle(oda, kollar, br, p0, C)
        else:
            p1 = C
        boy = sum(k.length for k in kollar.values()) + sum(LineString(b['pts']).length for b in br if len(b['pts']) > 1)
        ok = pis_dogrula(K, oda, kollar, br, p1, kose_kontrol=False)
        puan = boy + (0 if ok else 10000) + 2 * abs(ds)
        if iyi is None or puan < iyi['puan']:
            iyi = dict(kolon=C, kollar=kollar, br=br, ring=ring, oda=oda, puan=puan, dogrulanmadi=not ok)
    return iyi


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


def pis_dogrula(K, oda, kollar, br, p0, kose_kontrol=True):
    """kontrolör ölçüleriyle aynı mimari tanıma (MB) üzerinden: kolon ıslak hacim köşesinde, balkona taşmıyor,
    branşman yolu ≤ 260, pis–pis kesişme yok"""
    kb = getattr(K, 'kb', None)
    pt = Point(p0)
    if kb is not None and not kose_kontrol:
        hatlar = list(kollar.values()) + [LineString(b['pts']) for b in br if len(b['pts']) > 1]
        for r2 in kb['rooms']:
            if r2['balkon'] and any(h.intersection(r2['poly'].buffer(-5)).length > 18 for h in hatlar):
                return False
    elif kb is not None:
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
            sb = sum(sbf(b['f']) for b in ust)
            wc = any(wcf(b['f']) for b in ust)
            g = substring(kol, t0, t1)
            parcalar.append(dict(g=g, sb=sb, cap=pis_cap(sb, wc), tur='kol'))
    for b in ps['br']:
        k = b['f']['kind']
        parcalar.append(dict(g=LineString(b['pts']) if len(b['pts']) > 1 else None, sb=sbf(b['f']),
                             cap=pis_cap(sbf(b['f']), wcf(b['f'])),
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


def kapi_girisi(K, hol, ortak, tohum, saft):
    """daire kapısından giriş (kullanıcı çizimi 1./2. kat D5/D8): düşey merdiven holünde kapı kasasının yanında
    (şaftın UZAK tarafındaki kasa, kasadan 8 cm içeride), hat kapı açıklığından antreye girer.
    Dönüş (p: antre tarafı kapı yüzü, q: ortak alanda 15 cm dışarıda, u: q->p birim) ya da None."""
    adaylar = []
    for kq in list(getattr(K, 'kapilar', [])) + list(getattr(K, 'acikliklar', [])):
        if kq.distance(hol['poly']) > 20 or kq.distance(ortak) > 20:
            continue
        adaylar.append(kq)
    if not adaylar:
        return None
    kq = min(adaylar, key=lambda q: q.distance(Point(tohum)))
    rr = kq.minimum_rotated_rectangle
    cs = list(rr.exterior.coords)[:4]
    e1 = (cs[1][0] - cs[0][0], cs[1][1] - cs[0][1])
    e2 = (cs[2][0] - cs[1][0], cs[2][1] - cs[1][1])
    L1, L2 = math.hypot(*e1), math.hypot(*e2)
    (ea, La), (en, Ln) = ((e1, L1), (e2, L2)) if L1 >= L2 else ((e2, L2), (e1, L1))
    a = (ea[0] / La, ea[1] / La)
    n = (en[0] / Ln, en[1] / Ln)
    # eksene oturt (kapılar eksenel)
    if abs(a[0]) > abs(a[1]):
        a, n = (1.0 if a[0] > 0 else -1.0, 0.0), (0.0, 1.0)
    else:
        a, n = (0.0, 1.0 if a[1] > 0 else -1.0), (1.0, 0.0)
    c = (rr.centroid.x, rr.centroid.y)
    if not hol['poly'].buffer(3).contains(Point(c[0] + n[0] * (Ln / 2 + 6), c[1] + n[1] * (Ln / 2 + 6))):
        n = (-n[0], -n[1])
    # gerçek açıklık: duvar ekseni boyunca merkezden iki yana ilk duvar katısına kadar (kapı tanıması kaymış olabilir)
    uclar = []
    for s in (1, -1):
        d_ = 0.0
        while d_ < 130:
            q_ = Point(c[0] + a[0] * s * (d_ + 1), c[1] + a[1] * s * (d_ + 1))
            if K.S.contains(q_):
                break
            d_ += 1.0
        d_ = max(d_ - 10.0, 0.0) if d_ < 130 else La / 2 - 8
        uclar.append((c[0] + a[0] * s * d_, c[1] + a[1] * s * d_))
    m = max(uclar, key=lambda q: Point(q).distance(saft) if saft is not None and not saft.is_empty else 0)
    p = (m[0] + n[0] * Ln / 2, m[1] + n[1] * Ln / 2)
    q = (m[0] - n[0] * (Ln / 2 + 15), m[1] - n[1] * (Ln / 2 + 15))
    if not ortak.buffer(3).contains(Point(q)):
        return None
    return p, q, n


def temiz_su_daire(K, dno, fx, tohum):
    """kuru mahaller (oda/salon/yatak odası) önce KAPALI; ulaşılamayan armatür varsa yalnız o ıslak hacme bitişik EN KÜÇÜK
    kuru mahal açılır (ör. D3 duşu: 7,75 m² 'oda', yatak odası değil) — kullanıcı güzergâhı."""
    izin = set()
    for _ in range(4):
        ts = _temiz_su_daire(K, dno, fx, tohum, izin)
        if not ts.get('eksik'):
            return ts
        ek = None
        for f in ts['eksik']:
            ad = [r for r in K.rooms if r['daire'] == dno and r['tip'] == 'kuru' and r['i'] not in izin
                  and r['poly'].distance(f['oda']['poly']) < 30]
            if ad:
                q = min(ad, key=lambda r: r['poly'].area)
                if ek is None or q['poly'].area < ek['poly'].area:
                    ek = q
        if ek is None:
            return ts
        izin.add(ek['i'])
    return ts


def _temiz_su_daire(K, dno, fx, tohum, kuru_izin):
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
    kuru = [r for r in yasak if r['daire'] == dno and r['tip'] not in ('ortak', 'balkon') and r['i'] in kuru_izin]
    if kuru:
        km = (g.doldur(unary_union([r['poly'].buffer(-3) for r in kuru])) > 0) & ~izin_m
        dk = ndi.distance_transform_edt(km) * g.res
        cost[km] = 3.0 + 0.3 * np.maximum(dk[km] - 15.0, 0.0)
        yk = cv2.dilate(km.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0     # kuru mahal duvarı (ara duvar geçişi)
        dmk = duvar_m & yk & ~izin_m & ~np.isfinite(cost)
        cost[dmk] = 25.0
        cost[yasak_m & ~izin_m & ~km] = np.inf
    else:
        km = np.zeros_like(izin_m)
    ph = getattr(K, 'pis_hat', None)
    if ph is not None and not ph.is_empty:      # pis su hattına paralel/üst üste gitmesin (etiket yeri kalsın)
        pm = (g.doldur(ph.buffer(14)) > 0) & np.isfinite(cost)
        cost[pm] += 6.0
    cost[kapi_m] = np.inf
    if not K.kapi_u.is_empty:      # kapı kanadı süpürme alanı: hat kapı önünden/kanadından geçmesin
        kk = (g.doldur(K.kapi_u.buffer(48)) > 0) & np.isfinite(cost)
        cost[kk] += 30.0
        cost[kk & km] += 150.0     # kuru mahalde kapı açılım alanı: kesinlikle kaçın
    saft = getattr(K, 'saft_u', None)
    if saft is not None and not saft.is_empty:          # şaft / k.bac. / enerji odası: yasak bölge
        cost[g.doldur(saft.buffer(2)) > 0] = np.inf
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
        kapidan = None
        if aday and saft is not None and not saft.is_empty:
            en_iyi = min(aday, key=lambda pq: dist(pq[1], tohum))
            aday = [(p, q) for p, q in aday if LineString([p, q]).distance(saft) >= 25]
            if not aday or min(aday, key=lambda pq: dist(pq[1], tohum)) != en_iyi:
                # daire kapısının yanındaki duvar şafta (k.bac.) bitişik: kullanıcı gibi KAPIDAN girilir
                kapidan = kapi_girisi(K, h0, ortak, tohum, saft)
        if kapidan is not None:
            p, q, u = kapidan
            Hn = (p[0] + u[0] * 30, p[1] + u[1] * 30)          # kapı kanadı bölgesinden düz çıkar (kullanıcı gibi)
            r_, c_ = g.rc(Hn)
            H = g.xy(r_, c_)
            G = (q[0], H[1]) if abs(u[0]) > abs(u[1]) else (H[0], q[1])
        elif aday:
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
    eksik = []
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
            eksik = list(kalan.values())
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
    if eksik:
        log('  D%s: %d hedefe yol yok (kuru izin %s): %s' % (dno, len(eksik), sorted(kuru_izin), ', '.join(
            '%s/%s' % (f['kind'], f['oda']['name']) for f in eksik)))
    return dict(soguk=soguk, sicak=sicak, G=G, H=H, musluk=musluk, zincir=zincirler, toplam=toplam,
                kombi=kombiler[0]['c'] if kombiler else None, izin=U, eksik=eksik)


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


def makine_ciz(msp, eng, f):
    """ÇM / BM bağlantı yeri: kullanıcının blok kutusu ölçüsünde dikdörtgen + 'Ç.M.' / 'B.M.' yazısı (mimari yerinde)"""
    kutu = f['kutu']
    x0, y0, x1, y1 = kutu.bounds
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                       dxfattribs={'layer': 'ROTAS-SIHHI-SEMBOL'})
    dik = (y1 - y0) > (x1 - x0)
    eng.ekle_alan(kutu)
    c = kutu.centroid
    if f.get('mimari_yazi') or not f.get('ek'):   # mimari makineyi çiziyor/yazıyor: yalnız bağlantı kutusu
        return
    t = msp.add_text('Ç.M.' if f['kind'] == 'CM' else 'B.M.',
                     dxfattribs={'layer': 'ROTAS-SIHHI-CIHAZ-YAZI', 'height': 7.0, 'style': 'ROTAS-YAZI', 'width': 0.8,
                                 'rotation': 90.0 if dik else 0.0})
    t.set_placement(((x0 + x1) / 2, (y0 + y1) / 2), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    for pg in yazi_kutulari(t):
        eng.ekle_alan(pg)


def kucuk_dus_suzgeci(K, r, fo):
    """küçük duş / wc-duş (P9): pis su hattı kolondan duvar dibinden iner, lavabo hizasında alt duvar boyunca gider
    (`_pis_omurga`, kucuk_dus). EK süzgeç bu hattın ÜSTÜNE düşmesin (kontrolör tur 3 K1 'süzgeç üstünden aşmadan'):
    duş ile lavabo arasında, hatta ≥ 14 cm, duşa/lavaboya ≥ 25 cm, duvardan ≥ 10 cm; kısa dik branşmanla bağlanır."""
    if 'duş' not in r['name'] or r['poly'].area >= 2.0e4:
        return None
    dus = next((f for f in fo if f['kind'] == 'DUS'), None)
    lv = next((f for f in fo if f['kind'] == 'LV'), None)
    if dus is None or lv is None:
        return None
    C = min(((q[0] + K.off, q[1]) for q in KOLON_SABIT.values()), key=lambda c: r['poly'].distance(Point(c)))
    if r['poly'].distance(Point(C)) > 45:
        return None
    hat = LineString([C, (C[0], lv['c'][1]), lv['c']])
    ic = r['poly'].buffer(-10, join_style=2)
    kb = getattr(K, 'kb', None)
    if kb is not None:          # kontrolörün ıslak hacim poligonunda kalsın (1. kat wc-duş: yalnız lavabo tarafı)
        kbi = unary_union([q['poly'].buffer(-4) for q in kb['rooms'] if q.get('islak') and q['poly'].intersects(r['poly'])]
                          or [Polygon()])
        if not kbi.is_empty and not ic.intersection(kbi).is_empty:
            ic = ic.intersection(kbi)
    if ic.is_empty:
        return None
    hedef = ((dus['c'][0] + lv['c'][0]) / 2, (dus['c'][1] + lv['c'][1]) / 2)
    x0, y0, x1, y1 = ic.bounds
    best = None
    for yy in np.arange(y0, y1 + 0.1, 2.0):
        for xx in np.arange(x0, x1 + 0.1, 2.0):
            q = Point(xx, yy)
            if not ic.contains(q) or hat.distance(q) < 14 or q.distance(Point(dus['c'])) < 25 or \
                    q.distance(Point(lv['c'])) < 25:
                continue
            d = dist((xx, yy), hedef) + 0.5 * hat.distance(q)
            if best is None or d < best[0]:
                best = (d, (float(xx), float(yy)))
    return best[1] if best else None


def tekne_ici(K, p, pay=0.0):
    """p (nokta ya da geometri) bir duş teknesi / küvet poligonunun (pay kadar büyütülmüş) içinde mi"""
    g = Point(p) if isinstance(p, tuple) else p
    return any(pg.buffer(pay, join_style=2).intersects(g) if pay else pg.intersects(g)
               for _, pg in getattr(K, 'tekneler', []))


def tekne_disi_suzgec(K, r, fo):
    """yer süzgeci tekne içine düşerse (1. kat D6 wc-duş): kullanıcı gibi teknenin DIŞINDA, tekne ile klozet arasında,
    duvar dibine ~20 cm; tekneye ≥ 12 cm, armatürlere ≥ 25 cm, duvardan ≥ 12 cm (kontrolör tur 4 E1)."""
    tk = [pg for f_, pg in getattr(K, 'tekneler', []) if f_ in fo or r['poly'].intersects(pg)]
    if not tk:
        return None
    tu = unary_union(tk)
    hedefler = [f for f in fo if f['kind'] == 'WC'] or [f for f in fo if f['kind'] in ('LV', 'EV')]
    if not hedefler:
        return None
    w = min(hedefler, key=lambda f: tu.distance(Point(f['c'])))
    a_ = nearest_points(tu, Point(w['c']))[0]
    hedef = ((a_.x + w['c'][0]) / 2, (a_.y + w['c'][1]) / 2)
    ic = r['poly'].buffer(-12, join_style=2)
    kb = getattr(K, 'kb', None)
    if kb is not None:
        kbi = unary_union([q['poly'].buffer(-4) for q in kb['rooms'] if q.get('islak') and q['poly'].intersects(r['poly'])]
                          or [Polygon()])
        if not kbi.is_empty and not ic.intersection(kbi).is_empty:
            ic = ic.intersection(kbi)
    if ic.is_empty:
        return None
    yasak = tu.buffer(12, join_style=2)
    x0, y0, x1, y1 = ic.bounds
    best = None
    for yy in np.arange(y0, y1 + 0.1, 2.0):
        for xx in np.arange(x0, x1 + 0.1, 2.0):
            q = Point(xx, yy)
            if not ic.contains(q) or yasak.contains(q) or any(q.distance(Point(f['c'])) < 25 for f in fo):
                continue
            if K.kapi_u.distance(q) < 40:
                continue
            duvar = r['poly'].exterior.distance(q)
            d = dist((xx, yy), hedef) + 0.6 * abs(duvar - 20.0)
            if best is None or d < best[0]:
                best = (d, (float(xx), float(yy)))
    return best[1] if best else None


def klozet_hatti(K, r, fo):
    """kolon (kullanıcı ekseni) -> klozet: (C, W) ya da None (klozet yok / kolon komşu mahalde)"""
    w = next((f for f in fo if f['kind'] == 'WC'), None)
    if w is None:
        return None
    C = min(((q[0] + K.off, q[1]) for q in KOLON_SABIT.values()), key=lambda c: r['poly'].distance(Point(c)))
    if r['poly'].distance(Point(C)) > 45:
        return None
    return C, w['c']


def klozet_yani_suzgec(K, r, fo, p, CW):
    """wc-lvb: EK süzgeç kolon -> klozet düşey hattının (C.x..W.x bandı) üstüne / dibine düşerse hattın DAR tarafına
    (duvarla hat arasına) alınır; geniş taraf klozet 'Ø100 10 SB' etiketine kalır (kontrolör tur 4 E2). Topoloji aynı
    kalır (omurga kolondan klozete, süzgeç kısa yatay branşman)."""
    C, W = CW
    if abs(W[1] - C[1]) < 2 * abs(W[0] - C[0]) or abs(W[1] - C[1]) < 40:      # yalnız düşey ağırlıklı hat
        return None
    bx0, bx1 = min(C[0], W[0]), max(C[0], W[0])
    y_lo, y_hi = min(C[1], W[1]), max(C[1], W[1])
    if not (y_lo <= p[1] <= y_hi) or not (bx0 - 25 <= p[0] <= bx1 + 25):
        return None
    ray_y = p[1]
    poly = r['poly']
    sol = LineString([(bx0, ray_y), (bx0 - 200, ray_y)]).intersection(poly.exterior)
    sag = LineString([(bx1, ray_y), (bx1 + 200, ray_y)]).intersection(poly.exterior)
    xs_sol = [q.x for q in getattr(sol, 'geoms', [sol]) if not q.is_empty and q.geom_type == 'Point']
    xs_sag = [q.x for q in getattr(sag, 'geoms', [sag]) if not q.is_empty and q.geom_type == 'Point']
    if not xs_sol or not xs_sag:
        return None
    g_sol, g_sag = bx0 - max(xs_sol), min(xs_sag) - bx1
    if min(g_sol, g_sag) >= 30:
        return None
    if min(g_sol, g_sag) >= 17:          # dar taraf süzgece yeter: duvar ile hat arası (Z D1)
        x = (bx0 + max(xs_sol)) / 2 if g_sol < g_sag else (bx1 + min(xs_sag)) / 2
    elif max(g_sol, g_sag) >= 32:        # dar taraf süzgece de yetmez: geniş tarafta hattan 22 cm (2. kat wc-lvb)
        x = bx0 - 22 if g_sol > g_sag else bx1 + 22
    else:
        return None
    for dy in (0, -4, 4, -8, 8, -12, 12, -16, 16):
        q = (x, p[1] + dy)
        Q = Point(q)
        kare = Q.buffer(7.5, cap_style=3)
        if not poly.buffer(1).contains(kare) or K.kapi_u.distance(Q) < 40 or tekne_ici(K, kare, 2.0):
            continue
        if any(pg.intersects(kare) for pg in getattr(K, 'armatur_kutulari', [])):
            continue
        if any(Q.distance(Point(f['c'])) < 20 for f in fo if f['kind'] != 'YS'):
            continue
        return q
    return None


def mutfak_mi(r):
    return r is not None and (r.get('tip') == 'mutfak' or 'mutfak' in M2.MB.norm(r.get('name') or ''))


def ek_armaturler(K):
    """her ıslak hacimde (MUTFAK HARİÇ, 15.10 (D)) 1 süzgeç; her dairede ÇM ve BM (mimaride yoksa EK)"""
    ekler = []
    # 15.10 (D): mutfakta yer süzgeci YOK — mimari tanımanın bulduğu mutfak süzgeci de atılır
    K.fx[:] = [f for f in K.fx if not (f['kind'] == 'YS' and mutfak_mi(f.get('oda')))]
    daireler = sorted({r['daire'] for r in K.rooms if r['daire'] is not None})
    # ÇM / BM: kullanıcının çiziminde (mimari niş / tezgâh altı) gösterildiği yer — tasarim_new_block.json
    for m in TASARIM['makineler'].get(K.k, []):
        c = (m['x'] + K.off, m['y'])
        kutu = box(m['kutu'][0] + K.off, m['kutu'][1], m['kutu'][2] + K.off, m['kutu'][3])
        aday = [r for r in K.rooms if r['tip'] in ('islak', 'mutfak') and r['poly'].distance(Point(c)) < 45]
        if not aday:
            continue
        r = min(aday, key=lambda q: q['poly'].distance(kutu))
        var = [f for f in K.fx if f['kind'] == m['tip'] and f['oda'] is r]
        mim_yazi = any(dist(p_, c) < 60 and (M2.MB.norm(t_).startswith('bul') or M2.MB.norm(t_).startswith('cam')
                                             or M2.MB.norm(t_).startswith('çam'))
                       for p_, t_, h_, rot_, c_ in K.yazilar)
        if var:                                   # mimari tanıma buldu: bağlantı noktası kullanıcınınki
            f = min(var, key=lambda q: dist(q['c'], c))
            f['c'] = c
            f['kutu'] = kutu
            f['mimari_yazi'] = mim_yazi
        else:
            f = dict(kind=m['tip'], c=c, oda=r, ek=True, kutu=kutu, mimari_yazi=mim_yazi)
            K.fx.append(f)
            ekler.append(f)
    # tasarımda olmayan, mimari tanımanın bulduğu fazladan ÇM/BM (aynı dairede ikinci) atılır
    for d in daireler:
        for tip in ('CM', 'BM'):
            fs = [f for f in K.fx if f['kind'] == tip and f['oda'] is not None and f['oda']['daire'] == d]
            if len(fs) > 1 and any(f.get('kutu') is not None for f in fs):
                for f in fs:
                    if f.get('kutu') is None:
                        K.fx.remove(f)
    for r in K.rooms:
        if r['tip'] not in ('islak', 'mutfak') or mutfak_mi(r):
            continue
        fo = [f for f in K.fx if f['oda'] is r]
        if not any(f['kind'] == 'YS' for f in fo):
            ref = next((f['c'] for f in fo if f['kind'] == 'DUS'), None) or \
                  next((f['c'] for f in fo if f['kind'] in ('WC', 'EV', 'LV')), None)
            p = kucuk_dus_suzgeci(K, r, fo)
            if p is None:
                p = ek_nokta(r, [f for f in fo if f['kind'] != 'KOMBI'], K, 15.0, 28.0, ref)
            if p and tekne_ici(K, p, 10.0):           # süzgeç tekne içine konmaz (kontrolör tur 4 E1)
                p = tekne_disi_suzgec(K, r, fo) or p
            kh = klozet_hatti(K, r, fo) if not any(f['kind'] == 'DUS' for f in fo) else None   # wc-lvb
            if p and kh is not None:
                p2 = klozet_yani_suzgec(K, r, fo, p, kh)
                if p2 is not None:
                    log('  süzgeç klozet hattının dar tarafına: %s D%s (%.0f, %.0f) -> (%.0f, %.0f)' % (
                        r['name'], r['daire'], p[0], p[1], p2[0], p2[1]))
                    p = p2
            if p:
                f = dict(kind='YS', c=p, oda=r, ek=True)
                K.fx.append(f)
                ekler.append(f)
    return ekler


# ====================================================================== YERLEŞTİRME YARDIMCILARI
def daire_poly(c, r, n=24):
    return Point(c).buffer(r, resolution=max(4, n // 4))


def balon_yeri(c, eng, yasak, r=27.5, mesafeler=(55, 70, 85, 100, 115), disarida=None, kil_tol=0.5, tercih=None,
               duvar_tol=0.5, islak=None, islak_max=30.0, haric=()):
    def adaylar():
        if tercih is not None:
            dd = math.hypot(*tercih)
            a0 = math.atan2(tercih[1], tercih[0])
            for da in (0, 12, -12, 24, -24):
                for ek in (0, 10, 20):
                    yield dd + ek, a0 + math.radians(da)
        for dd in mesafeler:
            for k in range(24):
                yield dd, math.radians(15.0 * k + 7.5 * ((dd // 15) % 2))
    for dd, a in adaylar():
            p = (c[0] + dd * math.cos(a), c[1] + dd * math.sin(a))
            pg = daire_poly(p, r + 1.0)
            if yasak is not None and pg.intersects(yasak):
                if os.environ.get('S2_DEBUG_BALON') and tercih is not None and dd <= math.hypot(*tercih) + 1:
                    log('   BAL yasak', round(p[0]), round(p[1]))
                continue
            if disarida is not None and not disarida.contains(Point(p)):
                continue
            if eng.carpar(pg.buffer(MARJ), haric=haric) or eng.yasakta(pg, 'balon', tol=duvar_tol) or \
                    eng.yasakta(pg, 'asansor'):
                if os.environ.get('S2_DEBUG_BALON') and tercih is not None and dd <= math.hypot(*tercih) + 1:
                    hit_ = [[round(v) for v in g_.bounds] for g_ in eng.alan if g_.intersects(pg.buffer(MARJ))
                            and g_.intersection(pg.buffer(MARJ)).area > 0.05 and not any(g_ is h for h in haric)][:2]
                    log('   BAL', round(p[0]), round(p[1]), eng.carpar(pg.buffer(MARJ), cizgi_tol=1e9, haric=haric),
                        eng.carpar(pg.buffer(MARJ), haric=haric), eng.yasakta(pg, 'balon', tol=duvar_tol),
                        eng.yasakta(pg, 'asansor'), hit_)
                continue
            kil = LineString([(c[0] + 16 * math.cos(a), c[1] + 16 * math.sin(a)),
                              (p[0] - r * math.cos(a), p[1] - r * math.sin(a))])
            if islak is not None and kil.intersection(islak).length > islak_max:
                if os.environ.get('S2_DEBUG_BALON') and tercih is not None and dd <= math.hypot(*tercih) + 1:
                    log('   BAL islak', round(p[0]), round(p[1]), round(kil.intersection(islak).length))
                continue            # kılavuz ıslak hacmi (duş vb.) boydan boya kesmez (Y2a, P9)
            tol = 1e9 if (tercih is not None and dd <= math.hypot(*tercih) + 20) else kil_tol
            if tol is not None and eng.carpar(kil.buffer(0.5), cizgi_tol=tol, haric=haric):
                if os.environ.get('S2_DEBUG_BALON') and tercih is not None and dd <= math.hypot(*tercih) + 1:
                    log('   BAL kil', round(p[0]), round(p[1]))
                continue
            return p, kil
    return None, None


def carp_haric(eng, k, g, gevsek=False, diger=None, mimari_serbest=False):
    """etiket yazı kutusu çakışması; etiketin KENDİ hattı (g) ile kesişim sayılmaz.
    gevsek: başka boru hatlarının yazının altından geçmesine izin (kullanıcı çiziminde de var); yazı/sembol yasak,
    duvar çizgisi üstüne kısmen binebilir (Engel.pis_yasak).
    mimari_serbest: mimari yazı (mahal adı / alan / kapı yazısı) üstüne binebilir — yalnız klozet bağlantısı son çare
    (kullanıcı wc-lvb. klozet 'Ø100 10 SB' etiketini mahal yazısının üstüne koyuyor; kontrolör tur 4 E2)"""
    kb = k.buffer(MARJ, join_style=2)
    haric = ()
    if mimari_serbest:
        eng._agac()
        haric = tuple(eng.alan[i] for i in (eng._ta.query(kb) if eng._ta is not None else []) if i < eng.n_mimari)
    if eng.carpar(kb, cizgi_tol=1e9, haric=haric) or eng.pis_yasak(k, diger):
        return True
    if gevsek:
        return False
    eng._agac()
    gb = g.buffer(1.0)
    cd = [eng.cizgi[i] for i in (eng._tc.query(kb) if eng._tc is not None else [])] + eng.cizgi[eng._nc:]
    for c in cd:
        if not c.intersects(kb):
            continue
        x = c.intersection(kb)
        if x.is_empty or (x.length <= 0.3 and x.geom_type != 'Point'):
            continue
        if gb.contains(x):
            continue
        return True
    return False


PIS_SEG = {'segs': [], 'agac': None}
T_GEVSEK = (0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74, 0.18, 0.82, 0.1, 0.9, 0.03, 0.97, 0.0, 1.0)


def sb_kutusu(e):
    """etiketin 'n SB' satırının kutusu (kontrolör ölçüsü: 30 cm içindeki 'n SB' yazısı en yakın parçaya sayılır)"""
    for a in e.attribs:
        if (a.dxf.text or '').strip().upper().endswith('SB'):
            try:
                pk = KUTU.yazi_kutusu(a)
                if pk is not None and pk.is_valid and pk.area > 0:
                    return pk
            except Exception:
                pass
            pg = EK.glif_kutusu(a) or D.yazi_poligonu(a)
            if pg is not None:
                return pg
    return None


def sahiplik_ok(U, g):
    """etiket yazısı KENDİ parçasına en yakın pis su parçası olmalı (okuyan hangi hatta ait olduğunu bilsin;
    kontrolör ölçüsü: 30 cm içindeki etiket en yakın parçaya sayılır). Eşitlik serbest."""
    segs, agac = PIS_SEG['segs'], PIS_SEG['agac']
    if agac is None:
        return True
    d0 = U.distance(g)
    if d0 > 30:
        return False
    gb = g.buffer(0.5)
    for i in agac.query(U.buffer(d0 + 0.5)):
        s_ = segs[i]
        if gb.contains(s_):
            continue
        if s_.distance(U) < d0 - 0.5:
            return False
    return True


def etiket_dene_pis(msp, eng, g, cap, sb, adaylar_t=(0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74, 0.18, 0.82, 0.1, 0.9),
                    gevsek=False, disari=None, mimari_serbest=False):
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
        for ad in ('ROTAS-S2-PS-CAP-U', 'ROTAS-S2-PS-CAP-A', 'ROTAS-S2-PS-CAP-UL', 'ROTAS-S2-PS-CAP-AL'):
            e = ekle_insert(msp, ad, (a.x, a.y), L_PCAP, rot=ang, attr={'CAP': cap, 'SB': '%d SB' % sb})
            kut = yazi_kutulari(e)
            sg = 1 if ad.rstrip('L').endswith('U') else -1
            yx = -1 if ad.endswith('L') else 1
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            T = lambda x, y: (a.x + x * ca - y * sa, a.y + x * sa + y * ca)  # noqa: E731
            kanca = LineString([T(0, 0), T(0, 16 * sg), T(34 * yx, 16 * sg)])
            kanca_u = LineString([T(0, 16 * sg), T(34 * yx, 16 * sg)])
            dn = os.environ.get('S2_DEBUG_NOKTA')
            if dn and kut and g.centroid.distance(Point(*map(float, dn.split(',')))) < 8:
                kb_ = unary_union(kut).buffer(MARJ, join_style=2)
                hit = [('alan', [round(v) for v in q.bounds]) for q in eng.alan if q.intersects(kb_)
                       and q.intersection(kb_).area > 0.05][:2]
                hit += [('cizgi', [round(v) for v in q.bounds]) for q in eng.cizgi if q.intersects(kb_)][:3]
                log('   DN', ad, round(t, 2), hit, eng.yasakta(unary_union(kut), 'etiket'),
                    eng.carpar(kanca_u.buffer(0.4), cizgi_tol=1.0), 'ch', [carp_haric(eng, k, g, gevsek, diger=PIS_SEG.get('diger')) for k in kut],
                    'py', [eng.pis_yasak(k, PIS_SEG.get('diger')) for k in kut], 'sah', sahiplik_ok(sb_kutusu(e) or unary_union(kut), g),
                    'dis', disari is not None and any(k.intersection(disari).area > 0.5 for k in kut))
            if os.environ.get('S2_DEBUG') and kut:
                R = etiket_dene_pis.red
                kb_ = unary_union(kut)
                if eng.carpar(kb_.buffer(MARJ, join_style=2), cizgi_tol=1e9):
                    R['alan'] += 1
                    kk_ = kb_.buffer(MARJ, join_style=2)
                    for g_ in eng.alan:
                        if g_.intersects(kk_) and g_.intersection(kk_).area > 0.05:
                            b_ = g_.bounds
                            R['A%dx%d' % (round((b_[2] - b_[0]) / 10) * 10, round((b_[3] - b_[1]) / 10) * 10)] += 1
                            break
                elif eng.carpar(kb_.buffer(MARJ, join_style=2)):
                    R['cizgi'] += 1
                elif eng.yasakta(kb_, 'etiket'):
                    R['duvar/ortak'] += 1
                elif eng.yasakta(kb_, 'armatur'):
                    R['armatur'] += 1
                elif eng.carpar(kanca_u.buffer(0.4), cizgi_tol=1.0):
                    R['kanca'] += 1
            if mimari_serbest and os.environ.get('S2_DEBUG') and kut:
                kb_ = unary_union(kut).buffer(MARJ, join_style=2)
                eng._agac()
                hit = [(i < eng.n_mimari, [round(v) for v in eng.alan[i].bounds]) for i in eng._ta.query(kb_)
                       if eng.alan[i].intersects(kb_) and eng.alan[i].intersection(kb_).area > 0.05]
                ky = unary_union(kut)
                log('   MS', ad, round(t, 2), hit, 'tarama', eng.yasakta(ky, 'tarama'), 'arm', eng.yasakta(ky, 'armatur'),
                    'ortak', eng.yasakta(ky, 'ortak'), 'duvar', round(eng.duvar_orani(ky), 2),
                    'sah', sahiplik_ok(sb_kutusu(e) or ky, g))
            if disari is not None and kut and any(k.intersection(disari).area > 0.5 for k in kut):
                msp.delete_entity(e)
                continue
            if kut and not any(carp_haric(eng, k, g, gevsek, diger=PIS_SEG.get('diger'), mimari_serbest=mimari_serbest)
                               for k in kut) and \
                    (gevsek or not eng.carpar(kanca_u.buffer(0.4), cizgi_tol=1.0)) and sahiplik_ok(sb_kutusu(e) or unary_union(kut), g):
                for k in kut:
                    eng.ekle_alan(k)
                eng.ekle_cizgi(kanca)
                return e
            msp.delete_entity(e)
    return None


etiket_dene_pis.red = defaultdict(int)


def etiket_kilavuzlu(msp, eng, a, satirlar, blok, katman, yasak=None, hks=(14, 24, 34, 48, 64, 82, 104, 130),
                     yatay_hat=True, K=None, seg=None):
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
            if yatay_hat:          # yatay hat: kanca düşey (hatta dik), yazı kanca ucunun sağında/solunda
                hx, hy = a[0], a[1] + sy * hk
            else:                  # düşey hat: kullanıcı bloğu döndürülmez -> kanca hat boyunca, 8 cm yatay çentik
                if sx == 0 or sy == 0:
                    continue
                hx, hy = a[0], a[1] + sy * hk
                if seg is not None and not (min(seg[0][1], seg[1][1]) - 1 <= hy <= max(seg[0][1], seg[1][1]) + 1):
                    continue           # kanca hat parçasının dışına taşmaz
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
                ix = hx + 10 - bx0 if sx > 0 else hx - 10 - bx1
                iy = hy - (by0 + by1) / 2.0
            msp.delete_entity(e)
            e = ekle_insert(msp, blok, (ix, iy), katman, attr=satirlar)
            kut = yazi_kutulari(e)
            kil = LineString([a, (hx, hy)])
            if K is not None and (K.kapi_u.intersects(kil) or K.S.intersection(kil).length > 0.5):
                msp.delete_entity(e)       # kanca duvar/kapı kesmez (kontrolör tur 2, Y2/Y4)
                continue
            if yatay_hat:
                kk_ = substring(kil, min(8.0, kil.length * 0.5), kil.length) if kil.length > 1 else kil   # çiftin eşi hariç
            else:          # kanca kendi hattının üstünde; yalnız çentik denetlenir (çiftin eşi 5 cm'de, çentik 8)
                kk_ = LineString([(hx + sx * 6.0, hy), (hx + sx * 8.0, hy)])
            if any(eng.etiket_carpar(k) for k in kut) or eng.carpar(kk_.buffer(0.4), cizgi_tol=1.0):
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
            else:
                msp.add_line((hx, hy), (hx + sx * 8.0, hy), dxfattribs={'layer': katman})
            eng.ekle_cizgi(kil)
            return e
    return None


def etiket_halka(msp, eng, m, satirlar, blok, katman, mesafeler=(25, 32, 40, 50, 62, 75, 90, 105, 120, 140, 160),
                 duvar=None, izin=None, ortak_izin=False):
    """kalabalıkta etiket dışarı: m (parça ortası) çevresinde halka araması, kılavuz çizgili (yazı yatay)"""
    red = defaultdict(int)
    olc = {}
    for rot in (0.0, 90.0):
        e = ekle_insert(msp, blok, (0, 0), katman, rot=rot, attr=satirlar)
        kut = yazi_kutulari(e)
        msp.delete_entity(e)
        if not kut:
            return None
        olc[rot] = (min(k.bounds[0] for k in kut), min(k.bounds[1] for k in kut),
                    max(k.bounds[2] for k in kut), max(k.bounds[3] for k in kut))
    for dd, rot, k in [(dd, rot, k) for dd in mesafeler for rot in (0.0, 90.0) for k in range(24)]:
            bx0, by0, bx1, by1 = olc[rot]
            cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
            a = math.radians(15.0 * k + 5)
            p = (m[0] + dd * math.cos(a), m[1] + dd * math.sin(a))
            ins = (p[0] - cx, p[1] - cy)
            kutu = box(bx0 + ins[0] - 1, by0 + ins[1] - 1, bx1 + ins[0] + 1, by1 + ins[1] + 1)
            if izin is not None and kutu.intersects(izin):
                red['izin'] += 1
                continue
            if eng.carpar(kutu.buffer(MARJ, join_style=2)):
                red['engel'] += 1
                if os.environ.get('S2_DEBUG') and dd >= 90 and red['engel'] % 25 == 1:
                    kb_ = kutu.buffer(MARJ, join_style=2)
                    for g_ in eng.alan:
                        if g_.intersects(kb_) and g_.intersection(kb_).area > 0.05:
                            log('      alan', [round(v) for v in g_.bounds], round(g_.area)); break
                    for g_ in eng.cizgi:
                        if g_.intersects(kb_):
                            log('      cizgi', [round(v) for v in g_.bounds], g_.geom_type); break
                continue
            ortakta = eng.yasakta(kutu, 'ortak')
            if eng.yasakta(kutu, 'etiket') or eng.yasakta(kutu, 'armatur') or (ortakta and not ortak_izin):
                red['yasak'] += 1
                continue
            q = nearest_points(kutu.exterior, Point(m))[0]
            kil = LineString([m, (q.x, q.y)])
            if ortakta and kil.length > 80:
                red['ortak'] += 1
                continue
            if duvar is not None and kil.intersection(duvar).length > 28:
                red['duvar'] += 1
                continue
            kil_k = substring(kil, min(20.0, kil.length * 0.4), kil.length) if kil.length > 1 else kil
            if eng.carpar(kil_k.buffer(0.3), cizgi_tol=99999):
                red['kil'] += 1
                continue
            e = ekle_insert(msp, blok, ins, katman, rot=rot, attr=satirlar)
            kut2 = yazi_kutulari(e)
            if any(eng.etiket_carpar(k2) for k2 in kut2):
                msp.delete_entity(e)
                continue
            for k2 in kut2:
                eng.ekle_alan(k2)
            msp.add_line(m, (q.x, q.y), dxfattribs={'layer': L_KIL})
            eng.ekle_cizgi(kil)
            msp.add_circle(m, 1.5, dxfattribs={'layer': L_KIL})
            return e
    if os.environ.get('S2_DEBUG'):
        log('    halka red @%.0f,%.0f %s' % (m[0], m[1], dict(red)))
    return None


KIL_MAX = 60.0          # kılavuz üst sınırı (kontrolör tur 2, Y2): yalnız dar hacimde, ≤ 60 cm


def etiket_kisa(msp, eng, K, g, satirlar, blok, katman, oda_poly, mesafeler=(18, 24, 30, 37, 45, 53, 62, 72, 82),
                rotlar=(0.0, 90.0), disari=None):
    """kalabalık parçada son çare: KISA kılavuzlu etiket (≤ KIL_MAX). Yazı kutusu hattın kendi mahallinde (oda_poly),
    kılavuz duvar/kapı/başka hat/sembol kesmez, mahal dışına çıkmaz. Kılavuz gri (ROTAS-SEMBOL-KILAVUZ).
    disari verilirse (pis su, R1): oda_poly yerine — yazı kutusu disari'ya (başka daire / ortak / balkon) girmez,
    parçaya ≤ 30 cm, kılavuz ≤ 45 cm ve en çok bir ara duvar (≤ 25 cm) keser; kılavuz başka hattı kesebilir."""
    if disari is not None:
        e = _etiket_kisa_daire(msp, eng, K, g, satirlar, blok, katman, disari, rotlar)
        if e is None:          # sığmayan: kılavuz ≤ 60 cm (yazı parçadan uzakta; kılavuz parçaya iner)
            e = _etiket_kisa_daire(msp, eng, K, g, satirlar, blok, katman, disari, rotlar, uzak=55.0, kil_max=KIL_MAX)
        return e
    if oda_poly is None or oda_poly.is_empty:
        return None
    ic = oda_poly.buffer(-2, join_style=2)
    if ic.is_empty:
        return None
    olc = {}
    for rot in rotlar:
        e = ekle_insert(msp, blok, (0, 0), katman, rot=rot, attr=satirlar)
        kut = yazi_kutulari(e)
        msp.delete_entity(e)
        if not kut:
            return None
        olc[rot] = (min(k.bounds[0] for k in kut), min(k.bounds[1] for k in kut),
                    max(k.bounds[2] for k in kut), max(k.bounds[3] for k in kut))
    gb = g.buffer(1.0)
    L = g.length
    adaylar = []
    for tt in (0.5, 0.35, 0.65, 0.2, 0.8):
        m = g.interpolate(tt * L)
        for dd in mesafeler:
            for rot in rotlar:
                for k in range(24):
                    adaylar.append((dd, abs(tt - 0.5), rot, k, (m.x, m.y)))
    adaylar.sort(key=lambda q: (q[0], q[1]))
    red = defaultdict(int)
    for dd, _, rot, k, m in adaylar:
        bx0, by0, bx1, by1 = olc[rot]
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        a = math.radians(15.0 * k + 5)
        p = (m[0] + dd * math.cos(a), m[1] + dd * math.sin(a))
        ins = (p[0] - cx, p[1] - cy)
        kutu = box(bx0 + ins[0] - 1, by0 + ins[1] - 1, bx1 + ins[0] + 1, by1 + ins[1] + 1)
        if not ic.contains(kutu):
            red['oda'] += 1
            continue
        q = nearest_points(kutu.exterior, Point(m))[0]
        kil = LineString([m, (q.x, q.y)])
        if kil.length > KIL_MAX or kil.length < 3:
            red['boy'] += 1
            continue
        if kil.difference(oda_poly.buffer(1)).length > 25:     # tezgâh/duvar dibindeki hattan çıkış payı
            red['kil_oda'] += 1
            continue
        kil_d = substring(kil, min(8.0, kil.length * 0.4), kil.length)     # hat duvar yüzündeyse ilk 8 cm muaf
        if K.kapi_u.intersects(kil_d) or K.S.intersection(kil_d).length > 0.5:
            red['kapi_duvar'] += 1
            continue
        if eng.carpar(kutu.buffer(MARJ, join_style=2), cizgi_tol=1e9):
            red['alan'] += 1
            continue
        if eng.carpar(kutu.buffer(MARJ, join_style=2)):
            red['cizgi'] += 1
            continue
        if eng.yasakta(kutu, 'etiket') or eng.yasakta(kutu, 'armatur'):
            red['yasak'] += 1
            continue
        # kılavuz: kendi hattından ayrıldıktan sonra hiçbir hat/sembol/yazı kesmez
        kil_k = substring(kil, min(3.0, kil.length * 0.3), kil.length)
        if eng.carpar(kil_k.buffer(0.3), cizgi_tol=0.05) or eng.yasakta(kil_k.buffer(0.3), 'armatur', tol=0.05):
            red['kil_kes'] += 1
            continue
        if kutu.intersects(gb):
            continue
        e = ekle_insert(msp, blok, ins, katman, rot=rot, attr=satirlar)
        kut2 = yazi_kutulari(e)
        if any(eng.etiket_carpar(k2) for k2 in kut2):
            msp.delete_entity(e)
            continue
        for k2 in kut2:
            eng.ekle_alan(k2)
        msp.add_line(m, (q.x, q.y), dxfattribs={'layer': L_KIL})
        eng.ekle_cizgi(kil)
        msp.add_circle(m, 1.5, dxfattribs={'layer': L_KIL})
        etiket_kisa.boylar.append(kil.length)
        return e
    if os.environ.get('S2_DEBUG'):
        log('    kisa red @%.0f,%.0f %s' % (g.centroid.x, g.centroid.y, dict(red)))
    return None


etiket_kisa.boylar = []


def _etiket_kisa_daire(msp, eng, K, g, satirlar, blok, katman, disari, rotlar, uzak=30.0, kil_max=45.0):
    olc = {}
    for rot in rotlar:
        e = ekle_insert(msp, blok, (0, 0), katman, rot=rot, attr=satirlar)
        kut = yazi_kutulari(e)
        msp.delete_entity(e)
        if not kut:
            return None
        olc[rot] = (min(k.bounds[0] for k in kut), min(k.bounds[1] for k in kut),
                    max(k.bounds[2] for k in kut), max(k.bounds[3] for k in kut))
    gb = g.buffer(1.0)
    L = g.length
    adaylar = []
    for tt in (0.5, 0.3, 0.7, 0.15, 0.85, 0.04, 0.96):
        m = g.interpolate(tt * L)
        for dd in (16, 20, 25, 30, 36, 42, 50) + ((58, 66, 75) if uzak > 30 else ()):
            for rot in rotlar:
                for k in range(24):
                    adaylar.append((dd, abs(tt - 0.5), rot, k, (m.x, m.y)))
    adaylar.sort(key=lambda q: (q[0], q[1]))
    red = defaultdict(int)
    bina = K.bina
    for dd, _, rot, k, m in adaylar:
        bx0, by0, bx1, by1 = olc[rot]
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        a = math.radians(15.0 * k + 5)
        p = (m[0] + dd * math.cos(a), m[1] + dd * math.sin(a))
        ins = (p[0] - cx, p[1] - cy)
        kutu = box(bx0 + ins[0] - 1, by0 + ins[1] - 1, bx1 + ins[0] + 1, by1 + ins[1] + 1)
        if kutu.intersects(gb) or kutu.distance(g) > uzak or not (sahiplik_ok(kutu, g) if uzak <= 30 else True):
            red['uzak'] += 1
            continue
        if kutu.intersects(disari) or not bina.buffer(-2).contains(kutu):
            red['disari'] += 1
            continue
        q = nearest_points(kutu.exterior, Point(m))[0]
        kil = LineString([m, (q.x, q.y)])
        if kil.length > kil_max or kil.length < 3:
            red['boy'] += 1
            continue
        if K.kapi_u.intersects(kil) or K.S.intersection(kil).length > 25:
            red['kapi_duvar'] += 1
            continue
        kb = kutu.buffer(MARJ, join_style=2)
        if eng.carpar(kb, cizgi_tol=1e9) or eng.pis_yasak(kutu, PIS_SEG.get('diger')):
            red['alan'] += 1
            dn = os.environ.get('S2_DEBUG_NOKTA')
            if dn and g.centroid.distance(Point(*map(float, dn.split(',')))) < 8 and dd <= 30 and red['alan'] < 40:
                hit = [[round(v) for v in q.bounds] for q in eng.alan if q.intersects(kb) and q.intersection(kb).area > 0.05][:2]
                log('    DNK', dd, rot, k, [round(v) for v in kutu.bounds], hit, eng.pis_yasak(kutu, PIS_SEG.get('diger')))
            continue
        # kılavuz: yazı / sembol kesmez (boru hattının ve armatür çizgisinin üstünden geçebilir — eviye / lavabo
        # içindeki parçayı gösterir)
        kil_k = substring(kil, min(3.0, kil.length * 0.3), kil.length)
        if eng.carpar(kil_k.buffer(0.3), cizgi_tol=1e9):
            red['kil_kes'] += 1
            continue
        e = ekle_insert(msp, blok, ins, katman, rot=rot, attr=satirlar)
        kut2 = yazi_kutulari(e)
        if any(eng.carpar(k2.buffer(MARJ, join_style=2), cizgi_tol=1e9) for k2 in kut2) or \
                (uzak <= 30 and not sahiplik_ok(sb_kutusu(e) or kutu, g)):
            msp.delete_entity(e)
            continue
        for k2 in kut2:
            eng.ekle_alan(k2)
        msp.add_line(m, (q.x, q.y), dxfattribs={'layer': L_KIL})
        eng.ekle_cizgi(kil)
        msp.add_circle(m, 1.5, dxfattribs={'layer': L_KIL})
        etiket_kisa.boylar.append(kil.length)
        return e
    if os.environ.get('S2_DEBUG'):
        log('    kisa2 red @%.0f,%.0f %s' % (g.centroid.x, g.centroid.y, dict(red)))
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
        self.kolonlar = {no: dict(no=no, x=q[0], y=q[1], katlar=[], sb_kat={}, oda={})   # kullanıcının P1..P9
                         for no, q in KOLON_SABIT.items()}
        self.n_kolon = len(self.kolonlar)
        self.yb = {}                # no -> (x0, y0)
        self.model_daire = []
        self.adet = defaultdict(int)
        self.uyari = []
        self.temiz_daire = {}


def kat_yasaklari(eng, K):
    """etiket / balon konmayacak alanlar: duvar katısı, asansör boşluğu, (etiket için) merdiven ve armatür kutuları"""
    # merdiven basamakları (28 cm aralıklı paralel çizgi) duvar sanılır: merdiven içi duvar yasağından çıkarılır
    merd = unary_union([r['poly'].buffer(-6) for r in K.rooms if r['tip'] == 'ortak'
                        and 'asans' not in M2.MB.norm(r['name'])] or [Polygon()])
    S_ = K.S.difference(merd) if not merd.is_empty else K.S
    # mutfak tezgâhı (yoğun mimari çizgi) duvar katısı sanılıyor: kalın (≥ 40 cm) katı parçalar mutfak yanında
    # etiket yasağından çıkar — kullanıcı mutfak hattının etiketini tezgâh üstüne koyuyor (R1)
    mutfak = unary_union([r['poly'] for r in K.rooms if r['tip'] == 'mutfak'] or [Polygon()])
    if not mutfak.is_empty:
        S8 = K.S.buffer(8, join_style=2).buffer(-8, join_style=2)          # tezgâhtaki eviye/ocak boşlukları kapanır
        kalin = S8.buffer(-20, join_style=2).buffer(20, join_style=2)
        tezgah = kalin.intersection(mutfak.buffer(80, join_style=2))
        if not tezgah.is_empty:
            S_ = S_.difference(tezgah.buffer(-1))
            K.tezgah = tezgah
    for g in (S_.geoms if hasattr(S_, 'geoms') else [S_]):
        g = g.buffer(-1.0)
        if not g.is_empty:
            eng.yasak_ekle(g, 'etiket')
            eng.yasak_ekle(g, 'balon')
            eng.yasak_ekle(g, 'duvar')
    for r in K.rooms:
        a = M2.MB.norm(r['name'])
        if 'asans' in a:
            eng.yasak_ekle(r['poly'].buffer(8), 'etiket')
            eng.yasak_ekle(r['poly'].buffer(8), 'balon')
            eng.yasak_ekle(r['poly'].buffer(8), 'asansor')
        elif r['tip'] == 'ortak':
            eng.yasak_ekle(r['poly'], 'ortak')
    for f in K.fx:
        bb = f.get('bb')
        if bb and f['kind'] != 'KOMBI':
            try:
                eng.yasak_ekle(box(bb[0], bb[1], bb[2], bb[3]).buffer(-2), 'armatur')
            except Exception:
                pass



def makine_bransmani(ps):
    """BM/ÇM omurganın UCUNDA ise (branşman yok, omurga makine kutusunun kenarından geçiyor) görünür bağlantı:
    kutunun içinde, omurgadan uzak yarıda bağlantı noktası + 45° kısa branşman; omurga o düğümde biter
    (kontrolör tur 3 R4: Z D2 bulaşık makinesi pis su hattı görünmüyordu — hat tezgâh arası duvar boşluğunda)."""
    for b in ps['br']:
        f = b['f']
        if f['kind'] not in ('BM', 'CM') or f.get('kutu') is None:
            continue
        if len(b['pts']) > 1 and LineString(b['pts']).length >= 5.0:
            continue
        kol = ps['kollar'].get(b['kol'])
        if kol is None or kol.length < 40:
            continue
        cs = list(kol.coords)
        # son anlamlı (≥ 15 cm) omurga parçası
        acc = [0.0]
        for a_, b_ in zip(cs[:-1], cs[1:]):
            acc.append(acc[-1] + dist(a_, b_))
        i = len(cs) - 2
        while i > 0 and dist(cs[i], cs[i + 1]) < 15:
            i -= 1
        A, B = cs[i], cs[i + 1]
        u = birim(A, B)
        kx0, ky0, kx1, ky1 = f['kutu'].bounds
        kc = ((kx0 + kx1) / 2, (ky0 + ky1) / 2)
        if abs(u[1]) > abs(u[0]):           # düşey omurga: bağlantı noktası kutunun omurgadan uzak yanında
            ex = kx0 + 8 if A[0] >= kc[0] else kx1 - 8
            e = (ex, kc[1])
        else:
            ey = ky0 + 8 if A[1] >= kc[1] else ky1 - 8
            e = (kc[0], ey)
        h = abs((e[0] - A[0]) * u[1] - (e[1] - A[1]) * u[0])
        s_e = (e[0] - A[0]) * u[0] + (e[1] - A[1]) * u[1]
        s_n = acc[i] + s_e - h
        if h < 6 or s_n < acc[i] + 5 or s_n > kol.length:
            continue
        diger = [q['t'] for q in ps['br'] if q is not b and q['kol'] == b['kol']]
        if diger and s_n <= max(diger) + 5:
            continue
        N = tuple(kol.interpolate(s_n).coords[0])
        ps['kollar'][b['kol']] = substring(kol, 0, s_n)
        b['pts'] = [e, N]
        b['t'] = s_n
        b['makine_ucu'] = True


SAFT_ADLARI = ('k.bac', 'kbac', 'en. oda', 'en.oda', 'enerji oda', 'şaft', 'saft', 'tes. bac', 'tesisat bac')


def saft_poligonlari(K):
    """şaft / k.bac. / enerji odası: temiz su (ve hiçbir hat) buradan geçmez (14.10 talimatı; kontrolör tur 3 R2).
    Havalandırma şaftları (K.saftlar) + mimari yazısı şaft adı olan, duvarla çevrili küçük (< 1 m²) hücre.
    (1./2. kat k.bac. mahal tanımada antre-kor. poligonuna karışıyor.)"""
    gs = [s['poly'] for s in K.saftlar]
    for p, t, h, rot, c in K.yazilar:
        n = M2.MB.norm(t)
        if not any(a in n for a in SAFT_ADLARI):
            continue
        bx = box(p[0] - 120, p[1] - 120, p[0] + 120, p[1] + 120).difference(K.S.buffer(0.5)).difference(K.kapi_u.buffer(0.5))
        hs = [g for g in getattr(bx, 'geoms', [bx]) if g.distance(Point(p)) < 3]
        hs = [g for g in hs if g.area < 1.0e4]
        gs += hs
    return unary_union(gs) if gs else Polygon()


def kat_ciz(doc, eng, K, dur, onceki):
    msp = doc.modelspace()
    k = K.k
    off = K.off
    K.saft_u = saft_poligonlari(K)
    # tekne kuralları (süzgeç / aspiratör / omurga, kontrolör tur 4 E1): küçük duş (P9, < 2 m², teknesiz duş alanı;
    # tur 4 K1 onaylı düzen) hariç
    K.tekneler = [(f, pg) for f, pg in tekne_poligonlari(doc, K)
                  if not (f.get('oda') is not None and 'duş' in f['oda']['name'] and f['oda']['poly'].area < 2.0e4)]
    K.armatur_kutulari = [pg for _, pg in armatur_poligonlari(doc, K)]
    ek = ek_armaturler(K)
    for f in K.fx:                     # makine kutusu (bb yok): etiket üstüne binmez (kontrolör T07 armatür)
        if not f.get('bb') and f.get('kutu') is not None and f['kind'] in ('BM', 'CM'):
            eng.yasak_ekle(f['kutu'].buffer(-2), 'armatur')
    for f in (getattr(K, 'kb', None) or {}).get('fx', []):      # kontrolörün tanıdığı eviye/BM/ÇM yeri (aynı ölçü)
        if f['kind'] in ('EV', 'BM', 'CM'):
            g_ = box(*f['bb']) if f.get('bb') else Point(f['c']).buffer(18 if f['kind'] == 'EV' else 12)
            eng.yasak_ekle(g_, 'armatur')
    log('kat %s: mahal %d, armatür %d (EK %d: %s)' % (k, len(K.rooms), len(K.fx), len(ek),
                                                     ', '.join('%s/%s' % (f['kind'], f['oda']['name']) for f in ek)))
    # ---------------- pis su (kolonlar: kullanıcının P1..P9 eksenleri, her katta aynı nokta)
    pisler = []
    odalar = []
    for r in K.rooms:
        if r['tip'] not in ('islak', 'mutfak') or r['daire'] is None:
            continue
        fo = [f for f in K.fx if f['oda'] is r and f['kind'] in SB]
        if not fo:
            continue
        no, C = min(((n, (q[0] + off, q[1])) for n, q in KOLON_SABIT.items()),
                    key=lambda nc: (r['poly'].distance(Point(nc[1])), dist(nc[1], tuple(r['poly'].centroid.coords[0]))))
        odalar.append(dict(r=r, fo=fo, no=no, C=C, misafir=r['poly'].distance(Point(C)) > 45))
    # misafir ıslak hacim (kolonu komşu ıslak hacimde, ör. 1. kat D6 wc-duş -> P3): kendi halkasından komşunun halkasına
    # duvar içinden kısa bağlantı; komşu (ev sahibi) ağına 'BAG' sözde-armatürü olarak katılır
    for o in odalar:
        if not o['misafir']:
            continue
        ev = [q for q in odalar if q['no'] == o['no'] and not q['misafir']]
        if not ev:
            o['misafir'] = False
            continue
        ev = min(ev, key=lambda q: q['r']['poly'].distance(o['r']['poly']))
        hr = halka(ev['r']['poly']).exterior
        E = tuple(nearest_points(hr, o['r']['poly'])[0].coords[0])
        gr = halka(o['r']['poly']).exterior
        G = tuple(nearest_points(gr, Point(E))[0].coords[0])
        if abs(G[0] - E[0]) < 3:
            G = (E[0], G[1])
        elif abs(G[1] - E[1]) < 3:
            G = (G[0], E[1])
        ps = pis_su_oda(K, o['r'], o['fo'], [], None, sabit=G)
        if ps is None:
            dur.uyari.append('kat %s %s: bağlantı kurulamadı' % (k, o['r']['name']))
            continue
        bag = temiz([G, E]) if (abs(G[0] - E[0]) < 0.5 or abs(G[1] - E[1]) < 0.5) else oktal([G, (G[0], E[1]), E])
        sb = sum(sbf(f) for f in o['fo'])
        ps.update(no=o['no'], misafir=True, baglanti=bag, bag_sb=sb, bag_wc=any(wcf(f) for f in o['fo']))
        ev['fo'] = ev['fo'] + [dict(kind='BAG', c=E, oda=ev['r'], sb=sb, wc=ps['bag_wc'], ek=False)]
        pisler.append(ps)
    for o in odalar:
        if o['misafir']:
            continue
        ps = pis_su_oda(K, o['r'], o['fo'], [], None, sabit=o['C'])
        if ps is None:
            dur.uyari.append('kat %s %s: pis su ağı kurulamadı' % (k, o['r']['name']))
            continue
        ps['no'] = o['no']
        pisler.append(ps)
    pisler.sort(key=kolon_sirasi)
    for ps in pisler:
        makine_bransmani(ps)
    for ps in pisler:
        kolon_baglantisi(ps, off)
    for ps in pisler:
        no = ps['no']
        kv = dur.kolonlar[no]
        if k not in kv['katlar']:
            kv['katlar'].append(k)
        kv['oda'][k] = ((kv['oda'][k] + ' + ') if k in kv['oda'] else '') + '%s D%s' % (ps['oda']['name'], ps['oda']['daire'])
        kv['sb_kat'][k] = kv['sb_kat'].get(k, 0) + sum(sbf(b['f']) for b in ps['br'] if b['f']['kind'] != 'BAG')
        kv.setdefault('armatur', {}).setdefault(k, [])
        kv['armatur'][k] += [b['f']['kind'] for b in ps['br'] if b['f']['kind'] != 'BAG']
        if ps.get('dogrulanmadi'):
            dur.uyari.append('kat %s %s %s: pis su doğrulaması (yol boyu/kesişme) geçmedi' % (k, ps['oda']['name'], no))
    # 15.10 (D): hiçbir pis su hattı (bu kattaki) kolon sembolü çemberinin içine girmez — çizimde kırpılır, sayılır
    merkezler = [kolon_merkezi(no, off) for no in KOLON_MERKEZ]
    K.kolon_merkezleri = merkezler
    K.kolon_ici_kirpilan = 0

    def _pis_ciz(pts):
        g = LineString(pts)
        parca = kolon_ici_kirp(g, merkezler)
        if len(parca) != 1 or abs(parca[0].length - g.length) > 0.05:
            K.kolon_ici_kirpilan += 1
        for h in parca:
            msp.add_lwpolyline(list(h.coords), dxfattribs={'layer': L_PIS})
            eng.ekle_cizgi(h)

    for ps in pisler:
        for yon, kol in ps['kollar'].items():
            # branşman birleşim noktaları omurgaya köşe olarak eklenir (T-bağlantı ağ düğümü olsun)
            js = [b['pts'][-1] for b in ps['br'] if b['kol'] == yon and len(b['pts']) > 1]
            kc = kol_bol(kol, js)
            _pis_ciz(kc)
        for b in ps['br']:
            if len(b['pts']) > 1:
                _pis_ciz(b['pts'])
        if ps.get('misafir'):
            _pis_ciz(ps['baglanti'])
            continue
        ekle_insert(msp, 'ROTAS-S2-PIS-KOLON', ps['merkez'], 'ROTAS-SIHHI-SEMBOL', rot=kolon_aci(ps['no']),
                    attr={'NO': ps['no']})
        eng.ekle_alan(daire_poly(ps['merkez'], 15))
        dur.adet['ROTAS-S2-PIS-KOLON'] += 1
    # bağlantısız geçen kolon (o katta ıslak hacmi yok, ör. 1. kat P2): kolon sembolü yine çizilir (düşey süreklilik)
    kullanilan = {ps['no'] for ps in pisler}
    K.gecis_kolonlari = []
    for no, q in KOLON_SABIT.items():
        if no not in kullanilan:
            C = kolon_merkezi(no, off)
            ekle_insert(msp, 'ROTAS-S2-PIS-KOLON', C, 'ROTAS-SIHHI-SEMBOL', rot=kolon_aci(no), attr={'NO': no})
            eng.ekle_alan(daire_poly(C, 15))
            K.gecis_kolonlari.append((no, C))
    # süzgeçler (ıslak hacim)
    for f in K.fx:
        if f['kind'] == 'YS' and f['oda'] is not None and f['oda']['tip'] in ('islak', 'mutfak'):
            ekle_insert(msp, 'ROTAS-S2-YER-SUZGECI', f['c'], 'ROTAS-SIHHI-SEMBOL')
            eng.ekle_alan(Point(f['c']).buffer(8, cap_style=3))
            dur.adet['ROTAS-S2-YER-SUZGECI'] += 1
        if f['kind'] in ('CM', 'BM') and f.get('kutu'):
            makine_ciz(msp, eng, f)
            dur.adet['ROTAS-S2-MAKINE'] += 1
    # ---------------- temiz su
    temizler = {}
    pis_hat_u = unary_union([k_ for ps in pisler for k_ in ps['kollar'].values()] +
                            [LineString(b['pts']) for ps in pisler for b in ps['br'] if len(b['pts']) > 1] +
                            [LineString(ps['baglanti']) for ps in pisler if ps.get('misafir') and len(ps['baglanti']) > 1])
    for p, dno in K.tohum:
        fx = [f for f in K.fx if f['oda'] is not None and f['oda']['daire'] == dno and f['kind'] in MB_S]
        if not fx:
            continue
        t0 = time.time()
        K.pis_hat = pis_hat_u
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
            eng.ekle_alan(Point(tap).buffer(6, cap_style=3))          # vana sembolü: etiket üstüne binmez
            dur.adet['ROTAS-S2-KURESEL-VANA'] += 1
            if f['kind'] in MB_H:
                ekle_insert(msp, 'ROTAS-S2-KURESEL-VANA', (tap[0] + O_SICAK, tap[1] + O_SICAK), 'ROTAS-SIHHI-SEMBOL')
                eng.ekle_alan(Point(tap[0] + O_SICAK, tap[1] + O_SICAK).buffer(6, cap_style=3))
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
    # ---------------- aspiratör: penceresiz HER ıslak hacimde sembol (şafta yakın, ÇM nişi / armatür / kolon dışı);
    # yazı şaft grubu başına 1 (kullanıcı: 80 m3/h × bağlı ıslak hacim)
    asp = []
    bina_dolu = unary_union([Polygon(g.exterior) for g in (K.bina.geoms if hasattr(K.bina, 'geoms') else [K.bina])])
    for r in K.rooms:
        if r['tip'] != 'islak' or r['daire'] is None:
            continue
        dis = r['poly'].buffer(50).difference(bina_dolu).area
        saft_bitisik = any(s_['poly'].distance(r['poly']) <= 10 for s_ in K.saftlar)
        if dis > 300 and not saft_bitisik:          # cepheye bakan (pencereli) ve şaftsız ıslak hacim
            continue
        sf = min(K.saftlar, key=lambda s: s['poly'].distance(r['poly'])) if K.saftlar else None
        if sf is None or sf['poly'].distance(r['poly']) > 200:
            sf = None
        asp.append(dict(r=r, saft=sf))
    engel_p = [f['kutu'].buffer(22) for f in K.fx if f.get('kutu') is not None] + \
              [Point(f['c']).buffer(24) for f in K.fx if f['oda'] is not None and f['kind'] != 'KOMBI'] + \
              [daire_poly(ps['merkez'], 24) for ps in pisler if not ps.get('misafir')]
    engel_u = unary_union(engel_p) if engel_p else Polygon()
    for a_ in asp:
        r = a_['r']
        fo_ = [f for f in K.fx if f['oda'] is r]
        kh_ = klozet_hatti(K, r, fo_) if not any(f['kind'] == 'DUS' for f in fo_) else None
        # wc-lvb: klozet bağlantı hattının yanı 'Ø100 10 SB' etiketine kalır (kontrolör tur 4 E2)
        kh_ = LineString([kh_[0], (kh_[0][0], kh_[1][1]), kh_[1]]) if kh_ is not None else None
        ic = r['poly'].buffer(-15, join_style=2)
        if ic.is_empty:
            ic = r['poly'].buffer(-8, join_style=2)
        hedef = a_['saft']['c'] if a_['saft'] else tuple(r['poly'].centroid.coords[0])
        x0, y0, x1, y1 = ic.bounds
        aday = []
        for yy in np.arange(y0, y1 + 0.1, 4.0):
            for xx in np.arange(x0, x1 + 0.1, 4.0):
                q = Point(xx, yy)
                kare = q.buffer(13, cap_style=3)
                if not ic.contains(q) or not r['poly'].contains(kare):
                    continue
                if kare.intersects(engel_u) or eng.carpar(kare):
                    continue
                if any(kare.intersection(pg.buffer(-4, join_style=2)).area > 1.0 for _, pg in K.tekneler):
                    continue                         # aspiratör sembolü tekne içine konmaz (kontrolör tur 4 E1)
                if kh_ is not None and kh_.distance(kare) < 30:
                    continue
                aday.append((dist((xx, yy), hedef), (xx, yy)))
        if not aday:
            q = nearest_points(ic, Point(hedef))[0]
            aday = [(0, (q.x, q.y))]
        aday.sort()
        a_['aday'] = [q for _, q in aday]
        a_['p'] = a_['aday'][0]
    gruplar = defaultdict(list)
    for a_ in asp:
        gruplar[id(a_['saft']) if a_['saft'] else id(a_)].append(a_)
    aspirator = []
    for gl in gruplar.values():
        ana = max(gl, key=lambda q: q['r']['poly'].area)
        for q in gl:                       # yazısız ıslak hacimlerin sembolü şimdi; ana mahalinki yazıyla birlikte
            if q is ana:
                continue
            ekle_insert(msp, 'ROTAS-S2-ASPIRATOR', q['p'], 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL')
            eng.ekle_alan(Point(q['p']).buffer(13, cap_style=3))
            dur.adet['ROTAS-S2-ASPIRATOR'] += 1
        # kullanıcının planı: banyo 160 m3/h (banyo + wc-lvb. ya da tek banyo), wc-banyo / wc+banyo / wc-duş 80 m3/h
        banyo_var = any(M2.MB.norm(q['r']['name']).startswith('banyo') for q in gl)
        debi = max(160, 80 * len(gl)) if banyo_var else 80 * len(gl)
        aspirator.append(dict(r=ana['r'], p=ana['p'], debi=debi, odalar=[q['r'] for q in gl], saft=ana['saft'],
                              semboller=[(q['r'], q['p']) for q in gl], ana=ana, grup=gl))
    return dict(pisler=pisler, temiz=temizler, balkon=balkon_s, aspirator=aspirator, ek=ek)


ASP_METIN = ('Wc Aspiratörü', '%d m3/h-50 pa', 'Ø150 mm')     # kullanıcının planı: banyo 160, wc-banyo/wc-duş 80
ASP_BICIM = ((15.0, 25.0, 3), (12.0, 20.0, 3))          # tek tip h 15 (sığmazsa en az h 12; kontrolör tur 3 R3)


def aspirator_notu(msp, eng, K, a, dur):
    """'Wc Aspiratörü / 160|80 m3/h-50 pa / Ø150 mm' (TEXT, genişlik 0,8; kullanıcı biçimi; banyo 160, wc-banyo /
    wc-duş 80): YALNIZ kendi ıslak hacminin İÇİNDE, hiçbir hat/yazı/sembol/duş teknesini kesmeden; aspiratör sembolü
    notun ≤ 35 cm yanında. Tek tip h 15, sığmazsa h 12 (kontrolör tur 3 R3)."""
    sec = None
    for ana in [a['ana']] + [q for q in a.get('grup', []) if q is not a['ana']]:
        r = ana['r']
        sec, ts, h, ara, ns = _asp_yer(msp, eng, ana, a, sabit=ana is not a['ana'])
        if sec is not None:
            break
    if sec is None:
        # oda tamamen dolu (mahal adı + hatlar): kullanıcı gibi aynı dairenin bitişik HOL/ANTRE'sinde, ıslak hacim
        # duvarının dibinde; sembolden kısa kılavuz ≤ 60 cm (kapı, başka ıslak hacim, hat kesmez). Yatak odası yok.
        ana = a['ana']
        r = ana['r']
        # kullanıcı çizimi (1. kat D5 wc-banyo -> 'oda', D6 wc-duş -> üstteki oda): not ıslak hacmin duvarına bitişik
        # kuru mahalde, kılavuzsuz; hat / kapı / kapı yazısı / mimari yazı üstüne binmez
        komsular = [q for q in K.rooms if q is not r and q['daire'] == r['daire'] and q['tip'] in ('hol', 'kuru')
                    and q['poly'].distance(r['poly']) <= 30]
        komsular.sort(key=lambda q: (q['tip'] != 'hol', q['poly'].area))
        for q in komsular:
            sec, ts, h, ara, ns = _asp_yer(msp, eng, ana, a, komsu=q['poly'].buffer(-3, join_style=2), K=K)
            if sec is not None:
                break
    if sec is None:
        r, ana = a['r'], a['ana']
        sp = ana['aday'][0]
        ekle_insert(msp, 'ROTAS-S2-ASPIRATOR', sp, 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL')
        eng.ekle_alan(Point(sp).buffer(13, cap_style=3))
        dur.uyari.append('kat %s %s aspiratör yazısı yerleşmedi' % (K.k, r['name']))
        return None
    xx, yy, kb, sp, cx0, cy0, kil = sec
    if kil is not None:
        msp.add_line(kil.coords[0], kil.coords[-1], dxfattribs={'layer': L_KIL})
        eng.ekle_cizgi(kil)
    if not r['poly'].buffer(2).contains(kb):
        dur.uyari.append('kat %s %s aspiratör yazısı bitişik mahalde (kullanıcı gibi, ıslak hacim duvarına bitişik)' % (
            K.k, r['name']))
    for i, e in enumerate(ts):
        e.dxf.insert = (xx - cx0, yy - cy0 - ara * i)
        for g in yazi_kutulari(e):
            eng.ekle_alan(g)
    if ana is a['ana']:
        a['p'] = sp
    ana['p'] = sp
    a['semboller'] = [(q_r, (sp if q_r is r else q_p)) for q_r, q_p in a['semboller']]
    if ana is a['ana']:
        ekle_insert(msp, 'ROTAS-S2-ASPIRATOR', sp, 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL')
        eng.ekle_alan(Point(sp).buffer(13, cap_style=3))
    else:                            # yazı gruptaki diğer ıslak hacimde (sembolü zaten çizili); ana mahal sembolü yazısız
        sp0 = a['ana']['aday'][0]
        ekle_insert(msp, 'ROTAS-S2-ASPIRATOR', sp0, 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL')
        eng.ekle_alan(Point(sp0).buffer(13, cap_style=3))
    if h < 15:
        dur.uyari.append('kat %s %s aspiratör yazısı küçük (h %.0f, %d satır)' % (K.k, r['name'], h, ns))
    return ts


def _asp_yer(msp, eng, ana, a, sabit=False, komsu=None, K=None):
    """bir ıslak hacimde aspiratör notu yeri: (sec, ts, h, ara, ns); sec None ise yazı yok.
    sabit: sembol zaten çizili (ana['p']); yalnız onun yanına"""
    r = ana['r']
    adaylar_s = [ana['p']] if sabit else ana['aday']
    semb = [Point(q).buffer(13, cap_style=3) for q in adaylar_s]
    alan = r['poly'].buffer(-3, join_style=2) if komsu is None else komsu
    hedef = a['saft']['c'] if a['saft'] else tuple(r['poly'].centroid.coords[0])
    if komsu is not None:
        hedef = tuple(ana['p'])
        diger_islak = unary_union([q['poly'].buffer(-2) for q in K.rooms if q is not r and q['tip'] in ('islak', 'mutfak')]
                                  or [Polygon()])
        kapi_b = K.kapi_u.buffer(8)
    sec = None
    for h, ara, ns in ASP_BICIM:
        satirlar = [ASP_METIN[0], ASP_METIN[1] % a['debi'], ASP_METIN[2]]
        ts = []
        for i, t_ in enumerate(satirlar):
            e = msp.add_text(t_, dxfattribs={'layer': 'ROTAS-SIHHI-HAVALANDIRMA-YAZI', 'height': h, 'style': 'ROTAS-YAZI',
                                             'width': 0.8})
            e.dxf.insert = (0.0, -ara * i)
            ts.append(e)
        k0 = unary_union([g for e in ts for g in yazi_kutulari(e)]).envelope
        cx0, cy0 = k0.centroid.x, k0.centroid.y
        k0 = shapely_translate(k0, -cx0, -cy0)
        if alan.is_empty:
            break
        x0, y0, x1, y1 = alan.bounds
        ad = []
        for yy in np.arange(y0, y1 + 0.1, 3.0):
            for xx in np.arange(x0, x1 + 0.1, 3.0):
                kb = shapely_translate(k0, xx, yy)
                if alan.contains(kb):
                    ad.append((dist((xx, yy), hedef), xx, yy, kb))
        ad.sort(key=lambda q: q[0])
        red = defaultdict(int)
        red['aday'] = len(ad)
        for _, xx, yy, kb in ad:
            if eng.etiket_carpar(kb) or eng.yasakta(kb, 'tekne', tol=0.5):     # duş teknesi üstüne binmez (R3)
                if os.environ.get('S2_DEBUG_ASP'):
                    kk = kb.buffer(MARJ, join_style=2)
                    if eng.carpar(kk, cizgi_tol=1e9):
                        red['alan'] += 1
                    elif eng.carpar(kk):
                        red['cizgi'] += 1
                    else:
                        red['yasak'] += 1
                continue
            red['bos'] += 1
            if komsu is not None:
                if kb.intersects(kapi_b) or kb.distance(r["poly"]) > 30:
                    continue
                sec = (xx, yy, kb, adaylar_s[0], cx0, cy0, None)
                break
            for sp, sg in zip(adaylar_s, semb):
                d = sg.distance(kb)
                if d < MARJ or d > (35 if komsu is None else KIL_MAX) or (not sabit and eng.carpar(sg)):
                    red['sembol'] += 1
                    continue
                kil = None
                if komsu is not None and d > 6:
                    q1, q2 = nearest_points(sg, kb)
                    kil = LineString([q1, q2])
                    if kil.intersects(diger_islak) or kil.intersects(K.kapi_u) or \
                            eng.carpar(kil.buffer(0.3), cizgi_tol=1e9):      # yazı/sembol kesmez (boru altından geçebilir)
                        red['kil'] += 1
                        continue
                sec = (xx, yy, kb, sp, cx0, cy0, kil)
                break
            if sec:
                break
        if sec:
            return sec, ts, h, ara, ns
        if os.environ.get('S2_DEBUG_ASP'):
            log('   ASP %s h%.0f/%d komsu=%s %s' % (r['name'], h, ns, komsu is not None, dict(red)))
        for e in ts:
            msp.delete_entity(e)
    return None, [], 0, 0, 0


def daire_alani(K, p):
    """p noktasının dairesinin mahalleri (etiket daire dışına çıkmaz); ortak alanda ise None"""
    r = K.oda(p)
    if r is None or r['daire'] is None:
        rs = [q for q in K.rooms if q['daire'] is not None and q['poly'].distance(Point(p)) < 20]
        if not rs:
            return None
        r = min(rs, key=lambda q: q['poly'].distance(Point(p)))
    # dönüş: etiketin GİREMEYECEĞİ alan = başka dairelerin mahalleri
    return unary_union([q['poly'].buffer(-6) for q in K.rooms if q['daire'] is not None and q['daire'] != r['daire']]
                       or [Polygon()])


_MIM_CIZGI = {}


def _mim_cizgiler(doc):
    """ROTAS-MIMARI çizgileri (parça listesi + STRtree), belge başına önbellek"""
    if id(doc) not in _MIM_CIZGI:
        from ezdxf import path as ezpath
        ls = []
        for e in doc.modelspace().query('LINE LWPOLYLINE ARC'):
            if e.dxf.layer != 'ROTAS-MIMARI':
                continue
            if e.dxftype() == 'LINE':
                a_, b_ = e.dxf.start, e.dxf.end
                if abs(a_.x - b_.x) + abs(a_.y - b_.y) >= 1:
                    ls.append(LineString([(a_.x, a_.y), (b_.x, b_.y)]))
                continue
            try:
                vs = [(v.x, v.y) for v in ezpath.make_path(e).flattening(1.0)]
            except Exception:
                continue
            for a_, b_ in zip(vs[:-1], vs[1:]):
                if abs(a_[0] - b_[0]) + abs(a_[1] - b_[1]) >= 0.5:
                    ls.append(LineString([a_, b_]))
        _MIM_CIZGI.clear()
        _MIM_CIZGI[id(doc)] = (ls, STRtree(ls) if ls else None)
    return _MIM_CIZGI[id(doc)]


def tekne_poligonlari(doc, K):
    """duş teknesi / küvet poligonları: [(DUS armatürü, poligon)] — armatür kutusu (bb) ya da mimari çizgilerin
    poligonlaştırılması (0,3–1,6 m², köşegenli). K'de önbellek. Kural (kontrolör tur 4 E1): yer süzgeci ve aspiratör
    sembolü tekne içine konmaz; tekne içinden yalnız teknenin kendi gider branşmanı geçer."""
    if getattr(K, '_tekneler', None) is not None and K._tekneler[0] == id(doc):
        return K._tekneler[1]
    from shapely.ops import polygonize
    ls, tr = _mim_cizgiler(doc)
    out = []
    for f in K.fx:
        if f['kind'] != 'DUS':
            continue
        if f.get('bb'):
            out.append((f, box(*f['bb'])))
            continue
        if tr is None:
            continue
        c = f['c']
        B = box(c[0] - 150, c[1] - 150, c[0] + 150, c[1] + 150)
        loc = [ls[i] for i in tr.query(B)]
        try:
            polys = list(polygonize(unary_union(loc)))
        except Exception:
            continue
        aday = []
        for pg in polys:
            if not (0.3e4 < pg.area < 1.6e4) or pg.distance(Point(c)) > 20:
                continue
            x0, y0, x1, y1 = pg.bounds
            kosegen = math.hypot(x1 - x0, y1 - y0)
            if any(pg.buffer(3).contains(l_) and l_.length > 0.5 * kosegen and
                   abs(l_.coords[0][0] - l_.coords[1][0]) > 5 and abs(l_.coords[0][1] - l_.coords[1][1]) > 5 for l_ in loc):
                aday.append(pg)
        if aday:
            out.append((f, unary_union(aday).envelope))
    K._tekneler = (id(doc), out)
    return out


def armatur_poligonlari(doc, K):
    """klozet / lavabo kutuları: armatür kutusu (bb) ya da mimari çizgilerin poligonları (c'ye ≤ 5 cm, ≤ 0,5 m², her
    yönde ≤ 90 cm, zarf). K'de önbellek."""
    if getattr(K, '_armkutu', None) is not None and K._armkutu[0] == id(doc):
        return K._armkutu[1]
    from shapely.ops import polygonize
    ls, tr = _mim_cizgiler(doc)
    out = []
    for f in K.fx:
        if f['kind'] not in ('WC', 'LV'):
            continue
        if f.get('bb'):
            out.append((f, box(*f['bb'])))
            continue
        if tr is None:
            continue
        c = f['c']
        B = box(c[0] - 120, c[1] - 120, c[0] + 120, c[1] + 120)
        loc = [ls[i] for i in tr.query(B)]
        try:
            polys = list(polygonize(unary_union(loc)))
        except Exception:
            continue
        sec = []
        for pg in polys:
            x0, y0, x1, y1 = pg.bounds
            if 0.01e4 < pg.area < 0.5e4 and x1 - x0 <= 90 and y1 - y0 <= 90 and pg.distance(Point(c)) <= 5:
                sec.append(pg)
        if sec:
            out.append((f, unary_union(sec).envelope))
    K._armkutu = (id(doc), out)
    return out


def dus_tekneleri(doc, eng, K):
    """duş teknesi poligonları -> eng yasak 'tekne' (aspiratör notu üstüne binmez); klozet/lavabo kutusu -> 'armatur'"""
    n = 0
    # klozet / lavabo kutusu (armatür kutusu tanınmamışsa) -> 'armatur' yasağı (pis su etiketi klozet/lavabo üstüne
    # binmez; R1)
    for f, pg in armatur_poligonlari(doc, K):
        if not f.get('bb'):
            eng.yasak_ekle(pg.buffer(-1), 'armatur')
            n += 1
    for f, pg in tekne_poligonlari(doc, K):
        eng.yasak_ekle(pg if f.get('bb') else pg.buffer(4, join_style=2), 'tekne')
        n += 1
    return n


def kat_etiketle(doc, eng, K, kat, dur):
    msp = doc.modelspace()
    dus_tekneleri(doc, eng, K)
    islak_u = unary_union([r['poly'].buffer(-2) for r in K.rooms if r['tip'] in ('islak',)])
    n_ok = n_yok = 0
    # P balonları (ıslak hacim dışında, kılavuzlu)
    kolon_bal = [(ps['no'], ps['merkez']) for ps in kat['pisler'] if not ps.get('misafir')]
    kolon_bal += list(getattr(K, 'gecis_kolonlari', []))
    merd_ = unary_union([r['poly'].buffer(5) for r in K.rooms if r['tip'] == 'ortak'
                         and 'asans' not in M2.MB.norm(r['name'])] or [Polygon()])
    # merdivendeki mimari yazılar (basamak no, "merdiven" adı): kullanıcı balonu bunların üstüne koyuyor (P3/P5/P6)
    merd_yazi = [g for g in eng.alan[:getattr(eng, 'n_mimari', 0)] if merd_.intersects(g)]
    gor = set()
    for no, kc in kolon_bal:
        if no in gor:
            continue
        gor.add(no)
        ps = dict(no=no, kolon=kc)
        # kullanıcının balonu, kolon SEMBOL MERKEZİNE göre (tasarim_cikar: balon_ofset_merkez)
        to_ = TASARIM.get('balon_ofset_merkez', {}).get(no) or TASARIM['balon_ofset'].get(no)
        # kullanıcı ofseti 49–101 cm: balon ıslak hacim dışında, kılavuz ıslak hacimde ≤ 30 cm (duşu/odayı kesmez)
        MB_ = (55, 65, 75, 85, 95, 105, 115)
        p, kil = balon_yeri(ps['kolon'], eng, islak_u, tercih=to_, islak=islak_u)
        if p is None:          # kullanıcının ofseti: kılavuz/balon mimari yazının (kolon adı, mahal adı) üstünden geçebilir
            yakin_ = Point(kc).buffer(160)
            mim_ = [g for g in eng.alan[:getattr(eng, 'n_mimari', 0)] if g.intersects(yakin_)]
            p, kil = balon_yeri(ps['kolon'], eng, islak_u, tercih=to_, islak=islak_u,
                                haric=mim_)
        if p is None:          # merdiven basamakları duvar katısı sanılabiliyor: kullanıcı ofsetinde duvar toleranslı
            p, kil = balon_yeri(ps['kolon'], eng, islak_u, tercih=to_, islak=islak_u,
                                duvar_tol=1e9, mesafeler=())        # önce yazıya binmeyen varyant
        if p is None:
            p, kil = balon_yeri(ps['kolon'], eng, islak_u, tercih=to_, islak=islak_u,
                                haric=mim_, duvar_tol=1e9)
        if p is None:
            p, kil = balon_yeri(ps['kolon'], eng, islak_u, mesafeler=MB_, islak=islak_u)
        if p is None:          # kullanıcı gibi merdivende: basamak numarasının üstüne binebilir
            p, kil = balon_yeri(ps['kolon'], eng, islak_u, tercih=to_, islak=islak_u,
                                haric=merd_yazi)
        if p is None:
            p, kil = balon_yeri(ps['kolon'], eng, islak_u, mesafeler=MB_, kil_tol=1e9, islak=islak_u, haric=merd_yazi)
        if p is None:          # balon duvar çizgisine kısmen değebilir (yazı/hat/asansöre değmez)
            p, kil = balon_yeri(ps['kolon'], eng, islak_u, mesafeler=MB_, kil_tol=1e9, duvar_tol=500.0, islak=islak_u,
                                haric=merd_yazi)
        if p is None:
            p, kil = balon_yeri(ps['kolon'], eng, None, mesafeler=MB_ + (130,), kil_tol=1e9, duvar_tol=500.0,
                                islak=islak_u, islak_max=45.0, haric=merd_yazi)
        if p is None and os.environ.get('S2_DEBUG'):
            from collections import Counter
            cn = Counter()
            for dd in (55, 85, 120, 165):
                for kk in range(16):
                    a_ = math.radians(22.5 * kk)
                    pp = (kc[0] + dd * math.cos(a_), kc[1] + dd * math.sin(a_))
                    pg = daire_poly(pp, 28.5)
                    cn['carp' if eng.carpar(pg.buffer(MARJ)) else ('duvar' if eng.yasakta(pg, 'balon', tol=500)
                       else ('asansor' if eng.yasakta(pg, 'asansor') else 'serbest'))] += 1
            log('  DEBUG balon %s %s' % (ps['no'], dict(cn)))
        if p is None:
            dur.uyari.append('kat %s %s balonu yerleşmedi' % (K.k, ps['no']))
            continue
        e = ekle_insert(msp, 'ROTAS-S2-KOLON-NO', p, 'ROTAS-SIHHI-KOLON-NO', attr={'NO': ps['no']})
        eng.ekle_alan(daire_poly(p, 28.5))
        msp.add_line(kil.coords[0], kil.coords[-1], dxfattribs={'layer': L_KIL})
        eng.ekle_cizgi(kil)
    for a in kat['aspirator']:          # büyük yazılar (P balonlarından sonra, hat etiketlerinden önce)
        aspirator_notu(msp, eng, K, a, dur)
        dur.adet['ROTAS-S2-ASPIRATOR'] += 1
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
    # pis su etiketleri: her parça bir etiket (uzun parçalar önce)
    parcalar = []
    for ps in kat['pisler']:
        parcalar += pis_parcalar(ps)
        if ps.get('misafir') and len(ps['baglanti']) > 1:
            parcalar.append(dict(g=LineString(ps['baglanti']), sb=ps['bag_sb'], cap=pis_cap(ps['bag_sb'], ps['bag_wc']),
                                 tur='bag'))
    # HER pis su parçası etiketli (kontrolör tur 3 R1; kullanıcı katta yalnız 2 parçayı etiketsiz bırakıyor):
    # parça = çizgi segmenti (köşelerde bölünür); ≥ 20 cm her segment kendi etiketini alır, 45° pah / kısa uç
    # (< 20 cm) segmentler parçanın tamamı ≥ 12 cm ise bir kez denenir (zorunlu değil)
    segler = []
    for p in parcalar:
        cs = list(p['g'].coords)
        uzun = [(a, b) for a, b in zip(cs[:-1], cs[1:]) if dist(a, b) >= 20.0]
        if uzun:
            for a, b in uzun:
                segler.append(dict(p, g=LineString([a, b]), zorunlu=True))
        elif p['g'].length >= 12.0:
            a, b = max(zip(cs[:-1], cs[1:]), key=lambda ab: dist(*ab))
            segler.append(dict(p, g=LineString([a, b]), zorunlu=False))
    # zor yerler önce: kısa ve kalabalık parçalar uzun parçalardan önce yer seçer (uzun parçada çok aday konum var)
    segler.sort(key=lambda p: (not p['zorunlu'], p['g'].length))
    tum = []            # çizimdeki gibi (omurga birleşim noktalarında bölünmüş) segmentler
    for p in parcalar:
        cs = list(p['g'].coords)
        tum += [LineString([a, b]) for a, b in zip(cs[:-1], cs[1:]) if dist(a, b) >= 20.0]
    PIS_SEG['segs'] = tum
    PIS_SEG['agac'] = STRtree(tum) if tum else None
    balkon_u = unary_union([r['poly'].buffer(-3) for r in K.rooms if r['tip'] == 'balkon'] or [Polygon()])
    ortak_u = unary_union([r['poly'].buffer(-3) for r in K.rooms if r['tip'] == 'ortak'] or [Polygon()])
    def _yerlestir(pc):
        mm_ = pc['g'].interpolate(0.5, normalized=True)
        PIS_SEG['diger'] = daire_alani(K, (mm_.x, mm_.y))               # yazı başka dairenin mahaline girmez
        dis_ = None if balkon_u.intersects(pc['g']) else balkon_u      # duş etiketi balkona çıkmaz (Y2a)
        e = etiket_dene_pis(msp, eng, pc['g'], pc['cap'], pc['sb'], disari=dis_)
        if e is None:       # hattın üstünde; başka boru yazının altından geçebilir (kullanıcı çizimi); kısa parçada
            # etiket parçanın ucuna / uzantısına kayabilir (kontrolör tur 3 önerisi)
            e = etiket_dene_pis(msp, eng, pc['g'], pc['cap'], pc['sb'], gevsek=True, disari=dis_,
                                adaylar_t=T_GEVSEK)
        if e is None and pc['zorunlu']:
            # dar hacim: kısa kılavuz (≤ 45 cm), yazı parçaya ≤ 30 cm; aynı dairenin mahallerinde (bitişik mahal
            # dahil, kılavuz en çok bir ara duvar keser); başka daire / ortak alan / balkon / duvar / yazı / armatür yok
            mm = pc['g'].interpolate(0.5, normalized=True)
            dis2 = daire_alani(K, (mm.x, mm.y))
            if dis2 is not None:
                dis2 = unary_union([dis2, ortak_u, balkon_u])
                e = etiket_kisa(msp, eng, K, pc['g'], {'C1': pc['cap'], 'M1': '%d SB' % pc['sb']},
                                'ROTAS-S2-TS-CAP2', L_PCAP, None, disari=dis2)
        return e

    def _iz_yerlestir(pc):
        """yerleştir + geri alınabilir iz (msp varlıkları, engel alan/çizgi indisleri)"""
        n0, a0, c0 = len(msp), len(eng.alan), len(eng.cizgi)
        e = _yerlestir(pc)
        if e is None:
            return None
        return dict(pc=pc, e=e, ent=[msp[i] for i in range(n0, len(msp))], alan=(a0, len(eng.alan)),
                    cizgi=(c0, len(eng.cizgi)), kutu=unary_union(yazi_kutulari(e)))

    BOS = Point(-1e9, -1e9).buffer(0.01)

    def _geri_al(iz):
        for x in iz['ent']:
            if x.is_alive:
                msp.delete_entity(x)
        for i in range(*iz['alan']):
            eng.alan[i] = BOS
        for i in range(*iz['cizgi']):
            eng.cizgi[i] = LineString([(-1e9, -1e9), (-1e9 + 0.01, -1e9)])
        eng._ta = eng._tc = None

    konan, eksik = [], []
    for pc in segler:
        iz = _iz_yerlestir(pc)
        if iz is None:
            if pc['zorunlu']:
                eksik.append(pc)
        else:
            konan.append(iz)
    # klozet bağlantısı (Ø100) etiketsiz kaldıysa (kontrolör tur 4 E2, Z D1 / 2. kat wc-lvb): yakındaki Ø50 etiketi
    # geçici kaldırılır, önce klozet etiketi konur, sonra kaldırılan etiket yeniden yerleştirilir; ikisi birden
    # konamazsa eski hâl geri gelir (başka etiket kaybolmaz)
    for pc in list(eksik):
        if not pc['cap'].startswith('Ø100'):
            continue
        r_ = K.oda((pc['g'].centroid.x, pc['g'].centroid.y))
        yakin = [iz for iz in konan if iz['pc']['cap'] == 'Ø50' and iz['kutu'].distance(pc['g']) < 45
                 and (r_ is None or r_['poly'].buffer(30).intersects(iz['pc']['g']))]
        yakin.sort(key=lambda iz: iz['kutu'].distance(pc['g']))
        if os.environ.get('S2_DEBUG'):
            log('   onarım yakın etiketler', r_ and r_['name'], [(iz['pc']['cap'], iz['pc']['sb'], round(iz['kutu'].distance(pc['g'])))
                                         for iz in konan if iz['kutu'].distance(pc['g']) < 60])
            log('   onarım aday %s %d SB @%.0f,%.0f: %s' % (pc['cap'], pc['sb'], pc['g'].centroid.x, pc['g'].centroid.y,
                [(iz['pc']['cap'], iz['pc']['sb'], round(iz['kutu'].distance(pc['g']))) for iz in yakin]))
        for iz in yakin[:3]:
            _geri_al(iz)
            yeni = _iz_yerlestir(pc)
            if yeni is not None:
                tekrar = _iz_yerlestir(iz['pc'])
                if tekrar is not None:
                    konan.remove(iz)
                    konan += [yeni, tekrar]
                    eksik.remove(pc)
                    log('  etiket onarım: %s %d SB yerleşti, %s %d SB yeniden konuldu' % (
                        pc['cap'], pc['sb'], iz['pc']['cap'], iz['pc']['sb']))
                    break
                _geri_al(yeni)
            eski = _iz_yerlestir(iz['pc'])         # eski etiketi geri koy (aynı aday sırası: aynı yer)
            if eski is not None:
                konan[konan.index(iz)] = eski
            else:
                konan.remove(iz)
                if iz['pc']['zorunlu']:
                    eksik.append(iz['pc'])
    # son çare (yalnız klozet bağlantısı Ø100, klozete ≤ 15 cm): hattın üstünde, mimari yazının üstüne binebilir
    wc_c = [Point(f['c']) for f in K.fx if f['kind'] == 'WC']
    for pc in list(eksik):
        if not pc['cap'].startswith('Ø100') or not any(pc['g'].distance(q) <= 15 for q in wc_c):
            continue
        mm_ = pc['g'].interpolate(0.5, normalized=True)
        PIS_SEG['diger'] = daire_alani(K, (mm_.x, mm_.y))
        n0, a0, c0 = len(msp), len(eng.alan), len(eng.cizgi)
        e = etiket_dene_pis(msp, eng, pc['g'], pc['cap'], pc['sb'], gevsek=True, disari=balkon_u, adaylar_t=T_GEVSEK,
                            mimari_serbest=True)
        if e is not None:
            eksik.remove(pc)
            konan.append(dict(pc=pc, e=e, ent=[msp[i] for i in range(n0, len(msp))], alan=(a0, len(eng.alan)),
                              cizgi=(c0, len(eng.cizgi)), kutu=unary_union(yazi_kutulari(e))))
            log('  etiket son çare (mimari yazı üstünde): %s %d SB @ (%.0f, %.0f)' % (
                pc['cap'], pc['sb'], pc['g'].centroid.x, pc['g'].centroid.y))
    for pc in eksik:
        n_yok += 1
        dur.uyari.append('kat %s pis su etiketi yerleşmedi: %s %d SB @ (%.0f, %.0f) %.0f cm' % (
            K.k, pc['cap'], pc['sb'], pc['g'].centroid.x, pc['g'].centroid.y, pc['g'].length))
    n_ok += len(konan)
    # temiz su etiketleri: daire girişi, ıslak hacim girişleri, hol ana hattı, kombi
    for dno, ts in kat['temiz'].items():
        disari_u = unary_union([r['poly'].buffer(-3) for r in K.rooms if r['tip'] in ('balkon', 'ortak')
                                or (r['daire'] is not None and r['daire'] != dno)] or [Polygon()])
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
            pts = z['pts']
            Lz = LineString(pts)
            ankrajlar = []          # (nokta, yatay mı, parça)
            if oncelik == 2:
                # ıslak hacim girişi: etiket GİRİŞTE, hattın üstünde (kullanıcı: kanca 31 + 8,3)
                r_son = K.oda(z['son'], tipler=('islak', 'mutfak'))
                s_g = None
                if r_son is not None:
                    x_ = Lz.intersection(r_son['poly'].exterior)
                    xs_ = [g_ for g_ in getattr(x_, 'geoms', [x_]) if not g_.is_empty]
                    if xs_:
                        s_g = min(Lz.project(g_.centroid) for g_ in xs_)
                if s_g is not None:
                    for d_ in (25, 40, -25, -40, 55, -55, 15, -15, 70):
                        s_ = s_g + d_
                        if not (3 <= s_ <= Lz.length - 3):
                            continue
                        acc_ = 0.0
                        for a, b in zip(pts[:-1], pts[1:]):
                            L_ = dist(a, b)
                            if acc_ + 4 <= s_ <= acc_ + L_ - 4:
                                q_ = Lz.interpolate(s_)
                                ankrajlar.append(((q_.x, q_.y), abs(b[1] - a[1]) < abs(b[0] - a[0]), (a, b)))
                                break
                            acc_ += L_
            segs = sorted(zip(pts[:-1], pts[1:]), key=lambda ab: -dist(*ab))
            for a, b in segs[:3]:
                for t in (0.5, 0.3, 0.7, 0.15, 0.85):
                    ankrajlar.append(((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t),
                                      abs(b[1] - a[1]) < abs(b[0] - a[0]), (a, b)))
            konan = None
            for m, yatay, sg_ in ankrajlar:
                konan = etiket_kilavuzlu(msp, eng, m, sat, blok, L_TCAP, hks=(31, 22, 14, 40), yatay_hat=yatay, K=K,
                                         yasak=disari_u, seg=sg_)
                if konan is not None:
                    break
            if konan is None:       # dar hacim: kendi mahallinde ≤ 60 cm kısa kılavuz
                for m, yatay, (a, b) in ankrajlar[:6]:
                    r_ = K.oda(m)
                    if r_ is None or r_['tip'] == 'balkon':
                        continue
                    konan = etiket_kisa(msp, eng, K, LineString([a, b]), sat, blok, L_TCAP, r_['poly'], rotlar=(0.0,))
                    if konan is not None:
                        break
            if konan is None:
                n_yok += 1
                dur.uyari.append('kat %s D%s temiz su etiketi yerleşmedi (%s)' % (K.k, dno, sat.get('M1')))
            else:
                n_ok += 1
        # daire girişi etiketi (G-H parçası): 1 1/4" / n MB
    if os.environ.get('S2_DEBUG'):
        log('  pis etiket red', dict(etiket_dene_pis.red))
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


def cati_plani(doc, eng, dur, Kz, depo_m3):
    """ÇATI PLANI paftası (258656…260714): mimari çatı altlığı (kullanıcının çatı planı) + pis su kolonu havalık uçları
    P1…P9, yağmur inişleri YB1…YB9 (kullanıcının çatı konumları), çatı tipi fanlar (havalandırma şaftları), eğim okları,
    kullanım su deposu. Başlık 'ÇATI PLANI.........ÖLÇEK: 1 / 50'."""
    msp = doc.modelspace()
    x0, x1 = CATI_PAFTA
    msp.add_lwpolyline([(x0, PY0), (x1, PY0), (x1, PY1), (x0, PY1)], close=True, dxfattribs={'layer': 'ROTAS-PAFTA'})
    e = msp.add_text('ÇATI PLANI.........ÖLÇEK: 1 / 50',
                     dxfattribs={'layer': 'ROTAS-PAFTA-YAZI', 'height': 40.0, 'style': 'ROTAS-YAZI'})
    e.dxf.insert = (x0 + 538.0, PY0 + 39.0)
    cati = {k: (v[0], v[1]) for k, v in TASARIM['cati'].items()}
    # çatı çerçevesinin zemine göre ötelemesi (kullanıcının P konumlarından)
    dxs = [cati[k][0] - KOLON_SABIT[k][0] for k in KOLON_SABIT if k in cati]
    dys = [cati[k][1] - KOLON_SABIT[k][1] for k in KOLON_SABIT if k in cati]
    ox, oy = (sum(dxs) / len(dxs), sum(dys) / len(dys)) if dxs else (CATI_OFF, 0.0)
    ybs = [v for k, v in cati.items() if k.startswith('YB')]
    bx0, by0 = min(p[0] for p in ybs), min(p[1] for p in ybs)
    bx1, by1 = max(p[0] for p in ybs), max(p[1] for p in ybs)
    ic = box(bx0, by0, bx1, by1)
    for no in sorted(cati, key=lambda k: (k[0] == 'Y', int(''.join(c for c in k if c.isdigit())))):
        p = cati[no]
        if no.startswith('P'):
            p = tuple(TASARIM.get('cati_merkez', {}).get(no, p))     # sembol merkezi (bağlantı noktası değil)
            ekle_insert(msp, 'ROTAS-S2-PIS-KOLON', p, 'ROTAS-SIHHI-SEMBOL', attr={'NO': no},
                        rot=kolon_aci(no) if no in KOLON_MERKEZ else 0.0)
            msp.add_circle(p, 13.0, dxfattribs={'layer': 'ROTAS-SIHHI-SEMBOL'})        # havalık şapkası
            eng.ekle_alan(daire_poly(p, 15))
            q, kil = balon_yeri(p, eng, None, mesafeler=(45, 55, 70, 85))
            if q is not None:
                ekle_insert(msp, 'ROTAS-S2-KOLON-NO', q, 'ROTAS-SIHHI-KOLON-NO', attr={'NO': no})
                eng.ekle_alan(daire_poly(q, 28.5))
                msp.add_line(kil.coords[0], kil.coords[-1], dxfattribs={'layer': L_KIL})
        else:
            ekle_insert(msp, 'ROTAS-S2-KOLON-YAGMUR', p, 'ROTAS-SIHHI-SEMBOL')
            eng.ekle_alan(daire_poly(p, 9))
            q, kil = balon_yeri(p, eng, ic.buffer(-20), mesafeler=(40, 50, 60, 75))
            if q is None:
                q, kil = balon_yeri(p, eng, None, mesafeler=(40, 50, 60, 75))
            if q is not None:
                ekle_insert(msp, 'ROTAS-S2-KOLON-NO-YAGMUR', q, 'ROTAS-SIHHI-YAGMUR-NO', attr={'NO': no})
                eng.ekle_alan(daire_poly(q, 28.5))
                msp.add_line(kil.coords[0], kil.coords[-1], dxfattribs={'layer': L_KIL})
    # çatı tipi fanlar: havalandırma şaftları (zemin katta tanınan şaftlar, çatı çerçevesine ötelenmiş)
    pler = [v for k, v in cati.items() if k.startswith('P')]
    for sf in Kz.saftlar:
        c = (sf['c'][0] + ox, sf['c'][1] + oy)
        q = min(pler, key=lambda v: dist(v, c)) if pler else None
        if q is not None and dist(q, c) < 32:           # fan, havalık ucuna binmesin (şaft içinde, kolondan uzağa)
            u = birim(q, c) if dist(q, c) > 0.5 else (1.0, 0.0)
            c = (q[0] + u[0] * 32, q[1] + u[1] * 32)
        msp.add_circle(c, 14.0, dxfattribs={'layer': 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL'})
        msp.add_circle(c, 9.0, dxfattribs={'layer': 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL'})
        for aci in (45, 135):
            r_ = math.radians(aci)
            msp.add_line((c[0] - 14 * math.cos(r_), c[1] - 14 * math.sin(r_)),
                         (c[0] + 14 * math.cos(r_), c[1] + 14 * math.sin(r_)),
                         dxfattribs={'layer': 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL'})
        eng.ekle_alan(daire_poly(c, 15))
        mer = [(c[0] + dx, c[1] + dy) for dx, dy in ((70, -10), (70, -40), (-70, -10), (70, 20), (-70, -40), (0, -55),
                                                     (0, 45), (95, -10), (-95, -10))]
        t = yazi_yerlestir(msp, eng, 'Çatı Tipi Fan\\PØ150 mm', 15.0, 'ROTAS-SIHHI-HAVALANDIRMA-YAZI', mer)
        if t is not None:
            q = nearest_points(unary_union(yazi_kutulari(t)), Point(c))[0]
            if dist((q.x, q.y), c) > 16:
                msp.add_line(c, (q.x, q.y), dxfattribs={'layer': L_KIL})
    # eğim okları: her çatı yüzeyinde saçağa (yağmur oluğuna) doğru
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    for (px, py), (ux, uy) in (((cx, by0 + 230), (0, -1)), ((cx, by1 - 230), (0, 1)), ((bx0 + 230, cy - 250), (-1, 0)),
                               ((bx1 - 230, cy + 250), (1, 0)), ((cx - 400, by0 + 230), (0, -1)),
                               ((cx + 400, by1 - 230), (0, 1))):
        a_ = (px - ux * 60, py - uy * 60)
        b_ = (px + ux * 60, py + uy * 60)
        if eng.carpar(LineString([a_, b_]).buffer(12)):
            continue
        msp.add_line(a_, b_, dxfattribs={'layer': 'ROTAS-SIHHI-CATI'})
        nx_, ny_ = -uy, ux
        msp.add_solid([b_, (b_[0] - ux * 20 + nx_ * 7, b_[1] - uy * 20 + ny_ * 7),
                       (b_[0] - ux * 20 - nx_ * 7, b_[1] - uy * 20 - ny_ * 7)], dxfattribs={'layer': 'ROTAS-SIHHI-CATI'})
        rot = 90.0 if ux == 0 else 0.0
        t = msp.add_text('EĞİM', dxfattribs={'layer': 'ROTAS-SIHHI-CATI-YAZI', 'height': 12.0, 'style': 'ROTAS-YAZI',
                                            'rotation': rot, 'width': 0.8})
        t.set_placement((px + nx_ * 14, py + ny_ * 14), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        eng.ekle_alan(LineString([a_, b_]).buffer(14))
    # kullanım su deposu (mimaride "SU DEPOSU" yazılı yer)
    dep = None
    for e in msp.query('TEXT MTEXT'):
        if e.dxf.layer != 'ROTAS-MIMARI-YAZI':
            continue
        tx = e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()
        if 'DEPO' in tx.upper() and x0 < e.dxf.insert[0] < x1:
            dep = (e.dxf.insert[0], e.dxf.insert[1])
            break
    if dep is not None:
        mer = [(dep[0] + dx, dep[1] + dy) for dx, dy in ((40, -70), (40, -95), (40, 60), (190, -10), (-150, -10))]
        yazi_yerlestir(msp, eng, 'KULLANIM SU DEPOSU\\PV=%g m³' % depo_m3, 15.0, 'ROTAS-SIHHI-CIHAZ-YAZI', mer)
    # depo dolum / dönüş kolonları (kat planlarındaki temiz su kolon kutusu, P kolonlarıyla aynı öteleme)
    cb = None
    if getattr(dur, 'besleme', None):
        oxm = [TASARIM['cati_merkez'][k][0] - KOLON_MERKEZ[k][0] for k in KOLON_MERKEZ if k in TASARIM.get('cati_merkez', {})]
        oym = [TASARIM['cati_merkez'][k][1] - KOLON_MERKEZ[k][1] for k in KOLON_MERKEZ if k in TASARIM.get('cati_merkez', {})]
        of_ = (sum(oxm) / len(oxm), sum(oym) / len(oym)) if oxm else (ox, oy)
        cb = BES.cati_ciz(doc, eng, dur.besleme, of_, dep, sys.modules[__name__])
        if cb is None:
            dur.uyari.append('çatı: su deposu kutusu bulunamadı, depo kolon hatları çizilmedi')
        dur.besleme['cati'] = cb
    return dict(ofset=(ox, oy))


def rogarlar_model(kolonlar):
    """kullanıcının rögar ataması (R1<-P7,P9; R2<-P8; R3<-P2,P3,P5,P6; R4<-P1,P4) + PB; SB kümülatif"""
    sb = {k['no']: k['sb_toplam'] for k in kolonlar}
    adlar = sorted(TASARIM['rogar_atama'], key=lambda r: int(r[1:]))
    out, kum = [], 0
    for i, r in enumerate(adlar):
        ks = TASARIM['rogar_atama'][r]
        top = sum(sb.get(k, 0) for k in ks)
        kum += top
        xy = TASARIM['rogar_konum'][r]
        out.append(dict(no=r, x=xy[0], y=xy[1], olcu='70x70 h:-70cm', kolonlar=ks,
                        sonraki=adlar[i + 1] if i + 1 < len(adlar) else 'PB', cap='Ø150', egim='%1', sb=top,
                        sb_kumulatif=kum))
    xy = TASARIM['rogar_konum']['PB']
    out.append(dict(no='PB', x=xy[0], y=xy[1], olcu='80x80 h:-80cm', kolonlar=[], sonraki=None, cap='Ø150', egim='%1',
                    sb=0, sb_kumulatif=kum))
    return out


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
                    sp = next((pp for rr, pp in a.get('semboller', []) if rr is r), a['p'])
                    h['aspirator'] = dict(x=z(sp)[0], y=z(sp)[1], debi=80,
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
        ki = sorted(KATLAR.index(k) for k in kv['katlar'])
        gecis = [i for i in range(len(KATLAR)) if i not in ki and ki and ki[0] < i < ki[-1]]   # bağlantısız geçtiği ara kat
        rg = next((r for r, ks in TASARIM['rogar_atama'].items() if no in ks), None)
        gecis = [i for i in range(len(KATLAR)) if i not in ki and ki and i < ki[-1]]
        kolonlar.append(dict(no=no, x=kv['x'], y=kv['y'], katlar=ki, gecis_katlari=gecis, rogar=rg,
                             sb_kat=sbk, sb_toplam=top, cap='Ø100' if (wc or top >= 21) else pis_cap(top, False),
                             mahal=kv['oda'], armatur_sirasi_sema=kv.get('armatur', {}).get(kv['katlar'][0], [])))
    m = dict(
        proje=dict(ad='METRA MİMARLIK 4739/4 (new_block)', kat_adlari=[KAT_ADI[k] for k in KATLAR],
                   kat_ofset=[M2.M.OFF[k] for k in KATLAR], temel_ofset=-2629, bina_yuksekligi_m=9.0,
                   depo=dict(yer='çatı', hacim_m3=3.0 + 0.5 * max(0, len(daireler) - 10)), hidrofor=False,
                   kaynak='motor/sihhi2/plan.py', tarih=time.strftime('%d.%m.%Y %H:%M')),
        yuk_tablosu=dict(MB_S), yuk_tablosu_sicak=dict(MB_H), sb_tablosu=dict(SB), daireler=daireler, kolonlar=kolonlar,
        rogarlar=rogarlar_model(kolonlar), yagmur=[dict(no=n, x=q[0], y=q[1], cap='Ø70') for n, q in sorted(dur.yb.items(), key=lambda q: int(q[0][2:]))],
        temiz_su=dict(sebeke=None, ana_sayac_cap=inc(sum(d.get('temiz_su_mb', 0) for d in daireler)),
                      daire_mb={d['no']: d.get('temiz_su_mb') for d in daireler},
                      daire_cap={d['no']: d.get('temiz_su_cap') for d in daireler}),
        hav_saftlari=[], uyarilar=dur.uyari)
    bes = getattr(dur, 'besleme', None)
    if bes:                     # 15.10 (D): plandaki besleme kurgusu (şema ile aynı: şebeke -> depo -> sayaç -> daire)
        Z = bes['plan'].get('Z', {})
        cfg = bes['cfg']
        m['temiz_su'].update(
            sebeke=dict(x=cfg['sebeke'][0][0], y=cfg['sebeke'][0][1], yer='bina girişi (döşeme altından)'),
            sayac_grubu=dict(kat=0, yer='zemin kat merdiven holü, bina girişi kapısı yanı (ortak alan)',
                             adet=Z.get('sayac', {}).get('adet'), sira=[BES.dad(q) for q in Z.get('sayac', {}).get('satirlar', [])],
                             dizilim='vana – pislik tutucu – sayaç – çek valf – vana'),
            kolon_kutusu=dict(x=cfg['kolon_x'], kolonlar={BES.dad(ad): round(y, 1) for ad, y in bes['kol_y'].items()},
                              yer='merdiven holü doğu duvarı (her katta aynı nokta)'),
            depo_kolonlari=dict(dolum='şebeke -> çatı deposu', donus='çatı deposu -> sayaç kollektörü',
                                by_pass='çek valf (şebeke -> kollektör)'),
            daire_besleme={BES.dad(dn): dict(kat=d['kat'], kolon=(BES.dad(dn) if d['kat'] > 0 else None), cap=inc(d['mb']),
                                    mb=round(d['mb'], 2)) for dn, d in bes['daireler'].items()})
    sa = {}
    for K in Ks:
        for a in katlar[K.k]['aspirator']:
            if not a['saft']:
                continue
            key = (round(a['saft']['c'][0] - K.off), round(a['saft']['c'][1]))
            key = next((k_ for k_ in sa if abs(k_[0] - key[0]) <= 5 and abs(k_[1] - key[1]) <= 5), key)
            s = sa.setdefault(key, dict(no='Ş%d' % (len(sa) + 1), x=key[0], y=key[1], daireler=[], debi=0, fan=None))
            s['daireler'] = sorted(set(s['daireler']) | {'D%s' % r['daire'] for r in a['odalar']},
                                   key=lambda d_: int(d_[1:]))
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
    eng.n_mimari = len(eng.alan)          # ilk n alan = mimari yazılar
    paftalar(doc, eng)
    onb = os.environ.get('S2_ONBELLEK')          # geliştirme: mimari tanıma önbelleği (pickle, {kat: Kat})
    onb_K = None
    if onb and os.path.exists(onb):
        import pickle
        with open(onb, 'rb') as f_:
            onb_K = pickle.load(f_)
    A = M2.kayitlar() if onb_K is None else None
    Ks, katlar = [], {}
    dur = Durum()
    onceki = None
    adim = os.environ.get('S2_ADIM')          # geliştirme: 'kaydet' / 'yukle' — kat çizimi sonrası durum (etiket denemesi)
    if adim == 'yukle':
        import pickle
        with open(TMP + '/adim.pkl', 'rb') as f_:
            eng, katlar, dur, Ks = pickle.load(f_)
        doc = ezdxf.readfile(TMP + '/adim.dxf')
        for K in Ks:
            kat_etiketle(doc, eng, K, katlar[K.k], dur)
        if getattr(dur, 'besleme', None):
            dur.uyari += BES.etiketle(doc, eng, Ks, dur.besleme, sys.modules[__name__])
        cati_plani(doc, eng, dur, Ks[0], 3.0)
        model_yaz(Ks, katlar, dur)
        doc.saveas(CIKIS_DXF)
        log('DXF (adım yükle): %s %.0f s' % (CIKIS_DXF, time.time() - t0))
        for u in dur.uyari:
            log('  UYARI:', u)
        return
    for k in ('Z', '2', '1'):          # 1. kat en son: alt ve üst katın kolon eksenlerine oturur
        t1 = time.time()
        if onb_K is not None:
            K = onb_K[k]
        else:
            K = M2.Kat(A, k)
            K.kb = M2.MB.kat_analiz(A, M2.pencere(k), k)
        kat_yasaklari(eng, K)
        log('kat %s mimari: %.1f s' % (k, time.time() - t1))
        katlar[k] = kat_ciz(doc, eng, K, dur, onceki)
        onceki = [(kv['x'], kv['y']) for kv in dur.kolonlar.values()]
        Ks.append(K)
    Ks.sort(key=lambda K: KATLAR.index(K.k))
    # 15.10 (D): daire beslemeleri + sayaç grubu + temiz su kolon kutusu planlarda (şema ile aynı kurgu)
    dur.besleme = BES.ciz(doc, eng, Ks, katlar, KATLAR, TASARIM, sys.modules[__name__])
    if adim == 'kaydet':
        import pickle
        eng._ta = eng._tc = None
        eng.__dict__.pop('_yasak_t', None)
        with open(TMP + '/adim.pkl', 'wb') as f_:
            pickle.dump((eng, katlar, dur, Ks), f_)
        doc.saveas(TMP + '/adim.dxf')
    for K in Ks:
        kat_etiketle(doc, eng, K, katlar[K.k], dur)
    dur.uyari += BES.etiketle(doc, eng, Ks, dur.besleme, sys.modules[__name__])
    cati_plani(doc, eng, dur, Ks[0], 3.0)
    m = model_yaz(Ks, katlar, dur)
    aud = doc.audit()
    doc.saveas(CIKIS_DXF)
    log('DXF: %s (audit hata %d) — %d kolon, %d YB, %.0f s' % (CIKIS_DXF, len(aud.errors), len(dur.kolonlar), len(dur.yb),
                                                            time.time() - t0))
    for u in dur.uyari:
        log('  UYARI:', u)


if __name__ == '__main__':
    main(sys.argv[1:])
