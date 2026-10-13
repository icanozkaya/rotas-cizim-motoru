# -*- coding: utf-8 -*-
"""Tesisat çizim yardımcıları (VOYAP lib.doc üzerine): MTY katmanları, MTY blokları (öznitelikli), kendi semboller,
yazı yerleşimi (çakışmasız), boru + çap yazısı."""
import sys, math
sys.path.insert(0, '/home/claude/voyap')
from lib import *
from ezdxf.addons import Importer
from shapely.geometry import box as sbox, LineString, Point
from shapely.strtree import STRtree

TLAY = {
    "MTY-SOGUKSU-BORU": 5, "MTY-SICAKSU-BORU": 1, "MTY-SIRKULASYON-BORU": 31, "MTY-TEMIZSU-CAP": 101,
    "MTY-TEMIZSU-KOLON": 5, "MTY-PISSU-BORU": 6, "MTY-PISSU-KOLON": 211, "MTY-PISSU-CAP": 211, "MTY-PISSU-KOLONNO": 211,
    "MTY-ROGAR": 5, "MTY-CİHAZ": 135, "MTY-SAYAC": 3, "MTY-ISITMA-GIDIS-BORU": 10, "MTY-ISITMA-DONUS-BORU": 30,
    "MTY-ISITMA-CAP": 41, "MTY-PEX-BORU": 1, "MTY-KOLLETÖR": 7, "MTY-RADYATÖR": 2, "MTY-KALORIMETRE": 6,
    "MTY-UFLEME-KANALI": 20, "MTY-EGZOZ-KANALI": 4, "MTY-KANAL-CAP": 21, "MTY-DUMAN-EGZOZ": 1, "MTY-MENFEZ": 7,
    "MTY-HAVALANDIRMA-CIHAZ": 135, "MTY-TES-YAZI": 7, "MTY-TES-SAFT": 8, "MTY-TES-NOT": 1, "MTY-HESAP": 1,
    "MTY-TES-SEMA": 7, "MTY-TES-TABLO": 7, "MTY-BACA": 8, "MTY-DOGALGAZ": 2, "MIM-GUNCEL-BODRUM": 8,
    "MTY-TES-ISKELET": 9, "MTY-YAGMUR-BORUSU": 3, "MTY-PVC": 43, "MTY-ISIKAYBIMAHAL": 2, "MTY-KAT-ADI": 1, "MTY-SEMA": 8,
}
SS, SIS, SIRK, TCAP, TKOL = "MTY-SOGUKSU-BORU", "MTY-SICAKSU-BORU", "MTY-SIRKULASYON-BORU", "MTY-TEMIZSU-CAP", "MTY-TEMIZSU-KOLON"
PS, PSK, PSC, PSN, ROG = "MTY-PISSU-BORU", "MTY-PISSU-KOLON", "MTY-PISSU-CAP", "MTY-PISSU-KOLONNO", "MTY-ROGAR"
CHZ, SAY, IG, ID, ICAP = "MTY-CİHAZ", "MTY-SAYAC", "MTY-ISITMA-GIDIS-BORU", "MTY-ISITMA-DONUS-BORU", "MTY-ISITMA-CAP"
PEX, KLT, RAD, KAL = "MTY-PEX-BORU", "MTY-KOLLETÖR", "MTY-RADYATÖR", "MTY-KALORIMETRE"
UFL, EGZ, KCAP, DUM, MEN, HCH = "MTY-UFLEME-KANALI", "MTY-EGZOZ-KANALI", "MTY-KANAL-CAP", "MTY-DUMAN-EGZOZ", "MTY-MENFEZ", "MTY-HAVALANDIRMA-CIHAZ"
TY, SFT, TNOT, HES, TSEMA, TTAB, BACA = "MTY-TES-YAZI", "MTY-TES-SAFT", "MTY-TES-NOT", "MTY-HESAP", "MTY-TES-SEMA", "MTY-TES-TABLO", "MTY-BACA"
LT = {SS: None, SIS: 'BASMA HATTI', SIRK: 'SIRKULASYON HATTI', ID: 'ISITMA DONUS HATTI', PS: 'PIS'}

MTY_BLK = ["MTY-SU SAYACI", "MTY-KURESEL VANA", "MTY-CEKVALF VANA", "MTY-PISLIK TUTUCU", "MTY-KOLON NO PIS SU",
           "MTY-TEMIZLEME KAPAGI KOLON", "PVC ROGAR", "MTY-TEMIZ SU CAP MB", "MTY-PIS SU CAP SB",
           "EVIYE1 KOLON", "KLOZET1 KOLON", "LAVABO1 KOLON", "DUS TEKNESI1 KOLON", "SUZGEC1 KOLON", "PVC CATAL SAG", "PVC DIRSEK",
           "MTY-ETIKET", "MTY-RADYATOR MAHAL", "MTY-RADYATOR KOLLEKTÖR KOLON", "MTY-RADYATOR CAP"]


def setup(sdoc):
    """kullanıcının katman/çizgi tiplerini ve MTY bloklarını al, eksik katmanları aç"""
    im = Importer(sdoc, doc)
    try:
        im.import_tables(('linetypes',))
    except Exception as e:
        print('linetype import', e)
    im.import_blocks([b for b in MTY_BLK if b in sdoc.blocks])
    im.finalize()
    for n, c in TLAY.items():
        if n in sdoc.layers and n not in doc.layers:
            L0 = sdoc.layers.get(n)
            lt = L0.dxf.get('linetype', 'Continuous')
            doc.layers.add(n, color=L0.dxf.get('color', c), linetype=lt if lt in doc.linetypes else 'Continuous')
        elif n not in doc.layers:
            doc.layers.add(n, color=c)
    for n, lt in LT.items():
        if lt and lt in doc.linetypes:
            doc.layers.get(n).dxf.linetype = lt
    _blocks()


# ------------------------------------------------------------------ çakışmasız yazı
PLACED_T = []
OBST = []          # boru çizgileri (yazının altına girmesin)


def reset_place():
    PLACED_T.clear(); OBST.clear()


def _free(bx, pipes=True):
    g = sbox(*bx)
    if any(g.intersects(q) for q in PLACED_T): return False
    if pipes and any(g.intersects(q) for q in OBST): return False
    return True


def reserve(bx):
    PLACED_T.append(sbox(*bx))


def TX(p, s, h=8.0, lay=TY, al=TA.MIDDLE_CENTER, rot=0.0, mask=True):
    return T(p[0], p[1], s, h, lay, al, rot, mask=mask)


def place_text(p, lines, h=7.0, lay=TY, rmax=80, leader=True, pipes=True, prefer=None):
    """p etrafında boş yer bul; satırlar ortalı; gerekirse kılavuz çizgi"""
    tw = max(len(s) for s in lines) * h * 0.56 + 3
    th = len(lines) * h * 1.45
    dirs = prefer or [(1, 1), (1, -1), (-1, 1), (-1, -1), (0, 1), (0, -1), (1, 0), (-1, 0)]
    for r in (10, 18, 28, 40, 55, 75, 100, 130)[: max(1, sum(1 for x in (10, 18, 28, 40, 55, 75, 100, 130) if x <= rmax))]:
        for dx, dy in dirs:
            cx = p[0] + dx * (r + tw / 2 if dx else 0); cy = p[1] + dy * (r + th / 2 if dy else 0)
            bx = (cx - tw / 2, cy - th / 2, cx + tw / 2, cy + th / 2)
            if _free(bx, pipes):
                reserve(bx)
                for k, s in enumerate(lines):
                    T(cx, cy + th / 2 - h * 1.45 * (k + 0.5), s, h, lay, TA.MIDDLE_CENTER, 0, mask=True)
                if leader and r > 18:
                    ex = min(max(p[0], bx[0]), bx[2]); ey = min(max(p[1], bx[1]), bx[3])
                    L(p, (ex, ey), lay)
                return (cx, cy)
    cx, cy = p[0] + 15, p[1] + 15
    for k, s in enumerate(lines):
        T(cx, cy - h * 1.45 * k, s, h * 0.8, lay, TA.BOTTOM_LEFT, 0, mask=True)
    return (cx, cy)


def pipe_label(pts, txt, h=7.0, lay=TY, ust=None, minlen=None):
    """borunun en uzun parçasına paralel yazı (borunun 6 cm yanında); yer yoksa yakına kılavuzla"""
    segs = sorted(zip(pts[:-1], pts[1:]), key=lambda s: -math.dist(*s))
    tw = len(txt) * h * 0.56 + 2
    for a, b in segs[:4]:
        Ls = math.dist(a, b)
        if Ls < tw + 12: continue
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if ang > 90.01 or ang <= -90: ang += 180; a, b = b, a
        ang = (ang + 180) % 360 - 180
        ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        nx_, ny_ = -uy, ux
        for f in (0.5, 0.3, 0.7, 0.18, 0.82):
            for side in (1, -1):
                hk = h * (2.0 if ust else 1.1)
                off = 5 + hk / 2
                cx = a[0] + (b[0] - a[0]) * f + nx_ * off * side
                cy = a[1] + (b[1] - a[1]) * f + ny_ * off * side
                hw = abs(ux) * tw / 2 + abs(nx_) * hk / 2 + 1
                hh = abs(uy) * tw / 2 + abs(ny_) * hk / 2 + 1
                bx = (cx - hw, cy - hh, cx + hw, cy + hh)
                if _free(bx):
                    reserve(bx)
                    if ust:
                        c1 = (cx + nx_ * h * 0.55, cy + ny_ * h * 0.55); c2 = (cx - nx_ * h * 0.55, cy - ny_ * h * 0.55)
                        top, bot = (c1, c2)
                        T(top[0], top[1], txt, h, lay, TA.MIDDLE_CENTER, ang, mask=True)
                        T(bot[0], bot[1], ust, h * 0.85, lay, TA.MIDDLE_CENTER, ang, mask=True)
                    else:
                        T(cx, cy, txt, h, lay, TA.MIDDLE_CENTER, ang, mask=True)
                    return True
    m = max(segs, key=lambda s: math.dist(*s))
    mp = ((m[0][0] + m[1][0]) / 2, (m[0][1] + m[1][1]) / 2)
    place_text(mp, [txt] + ([ust] if ust else []), h=h * 0.9, lay=lay, rmax=75)
    return False


def PIPE(pts, lay, w=0.0):
    e = PL(pts, lay, w)
    OBST.append(LineString(pts) if len(pts) > 1 else Point(pts[0]))
    return e


# ------------------------------------------------------------------ MTY blok (öznitelikli)
def MTYB(name, p, rot=0.0, s=1.0, lay="MTY-VANA", attrs=None, mask=None):
    if mask: MASKC(p, mask)
    ins = msp.add_blockref(name, (p[0], p[1]), dxfattribs={"layer": lay, "rotation": rot, "xscale": s, "yscale": s})
    if attrs and name in doc.blocks:
        for ad in doc.blocks.get(name).query('ATTDEF'):
            tg = ad.dxf.tag
            if tg in attrs:
                at = ins.add_attrib(tg, str(attrs[tg]), (p[0], p[1]))
                at.dxf.height = ad.dxf.height * s
                at.dxf.layer = lay
                try:
                    import ezdxf.math as em
                    m = ins.matrix44()
                    at.dxf.insert = m.transform(ad.dxf.insert)
                    at.dxf.rotation = rot + ad.dxf.get('rotation', 0)
                except Exception:
                    pass
                at.dxf.owner = ins.dxf.handle
                if ad.dxf.get('style'): at.dxf.style = ad.dxf.style if ad.dxf.style in doc.styles else 'ROTAS'
    return ins


NUM = {}


def numara(p, rot, pre, s=0.6, h=4.0):
    """vana/cihaz numarası (gerçek gösterimli sembolün yanında): V-01, CV-01, PT-01, SY-01 ..."""
    NUM[pre] = NUM.get(pre, 0) + 1
    t = f"{pre}-{NUM[pre]:02d}"
    a = math.radians(rot + (90 if NUM[pre] % 2 else -90)); d = 9.0 * s / 0.6 + h * 0.6     # komşu semboller: numara sırayla iki yana
    q = (p[0] + math.cos(a) * d, p[1] + math.sin(a) * d)
    T(q[0], q[1], t, h, "MTY-VANA", TA.MIDDLE_CENTER, rot if -90 < (rot % 360) < 90 or (rot % 360) > 270 else rot - 180, mask=True)
    return t


def VANA(p, rot=0.0, cap='DN25', s=0.6, no=True):
    e = MTYB("MTY-KURESEL VANA", p, rot, s, "MTY-VANA", {'CAP': cap}, mask=7 * s / 0.6)
    if no: numara(p, rot, 'V', s)
    return e


def CEKV(p, rot=0.0, cap='DN25', s=0.6, no=True):
    e = MTYB("MTY-CEKVALF VANA", p, rot, s, "MTY-VANA", {'CAP': cap}, mask=7 * s / 0.6)
    if no: numara(p, rot, 'CV', s)
    return e


def PISLIK(p, rot=0.0, cap='DN25', s=0.6, no=True):
    e = MTYB("MTY-PISLIK TUTUCU", p, rot, s, "MTY-VANA", {'CAP': cap}, mask=7 * s / 0.6)
    if no: numara(p, rot, 'PT', s)
    return e


def UCYOL(p, rot=0.0, s=1.0, lay="MTY-VANA", no=True):
    """3 yollu vana (gerçek gösterim): papyon + 3. ağız üçgeni + motor"""
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
    R_ = lambda x, y: (p[0] + (x * ca - y * sa) * s, p[1] + (x * sa + y * ca) * s)
    MASKC(p, 9 * s)
    PL([R_(-8, -5), R_(8, 5), R_(8, -5), R_(-8, 5)], lay, closed=True)
    PL([R_(0, 0), R_(-5, -9), R_(5, -9)], lay, closed=True)
    PL([R_(0, 0), R_(0, 7)], lay); PL([R_(-4, 7), R_(4, 7), R_(4, 13), R_(-4, 13)], lay, closed=True)
    T(*R_(0, 10), "M", 3.5 * s, lay, TA.MIDDLE_CENTER)
    if no: numara(p, rot, '3YV', s * 0.6 / 0.6 * 1.2)


def SAYAC(p, rot=0.0, cap='DN20', s=0.7, no=True):
    e = MTYB("MTY-SU SAYACI", p, rot, s, SAY, {'CAP': cap}, mask=7)
    if no: numara(p, rot, 'SY', s)
    return e


# ------------------------------------------------------------------ kendi bloklarım
def _b(name):
    if name in doc.blocks: return None
    return doc.blocks.new(name)


def _blocks():
    a0 = {"layer": "0"}
    b = _b("T-KALORIMETRE")              # kalorimetre: daire + "Q" + akış ok
    if b is not None:
        b.add_circle((0, 0), 6, dxfattribs=a0)
        b.add_line((-10, 0), (-6, 0), dxfattribs=a0); b.add_line((6, 0), (10, 0), dxfattribs=a0)
        b.add_text("Q", height=6, dxfattribs={"layer": "0", "style": "ROTAS"}).set_placement((0, 0), align=TA.MIDDLE_CENTER)
        b.add_lwpolyline([(-4, 8), (4, 8), (2, 10), (4, 8), (2, 6)], dxfattribs=a0)
    b = _b("T-DOLAP")                    # sayaç dolabı 90x18 (merkez)
    if b is not None:
        b.add_lwpolyline([(-45, -9), (45, -9), (45, 9), (-45, 9)], close=True, dxfattribs=a0)
        b.add_line((-45, -9), (45, 9), dxfattribs=a0)
    b = _b("T-KOLLEKTOR")                # ofis yerden ısıtma kollektörü (gidiş/dönüş volan) 70x14
    if b is not None:
        b.add_lwpolyline([(-35, -7), (35, -7), (35, 7), (-35, 7)], close=True, dxfattribs=a0)
        b.add_line((-32, 2.5), (32, 2.5), dxfattribs=a0); b.add_line((-32, -2.5), (32, -2.5), dxfattribs=a0)
    b = _b("T-KOLON-T")                   # temiz su kolonu (plan): dolu küçük daire
    if b is not None:
        b.add_circle((0, 0), 3.0, dxfattribs=a0)
        h = b.add_hatch(dxfattribs=a0); h.paths.add_polyline_path([(3 * math.cos(t * math.pi / 8), 3 * math.sin(t * math.pi / 8)) for t in range(16)], is_closed=True)
    b = _b("T-KOLON-P")                   # pis su kolonu (plan): Ø iç içe daire
    if b is not None:
        b.add_circle((0, 0), 5.5, dxfattribs=a0); b.add_circle((0, 0), 3.5, dxfattribs=a0)
    b = _b("T-POMPA")                     # sirkülatör: daire + üçgen
    if b is not None:
        b.add_circle((0, 0), 8, dxfattribs=a0)
        b.add_lwpolyline([(-5, -6), (7, 0), (-5, 6)], close=True, dxfattribs=a0)
    b = _b("T-YER-SUZGECI")
    if b is not None:
        b.add_lwpolyline([(-8, -8), (8, -8), (8, 8), (-8, 8)], close=True, dxfattribs=a0)
        for k in (-4, 0, 4): b.add_line((-6, k), (6, k), dxfattribs=a0)
    b = _b("T-MENFEZ")                    # kanal menfezi (planda) 40x20 kutu + çapraz
    if b is not None:
        b.add_lwpolyline([(-20, -10), (20, -10), (20, 10), (-20, 10)], close=True, dxfattribs=a0)
        b.add_line((-20, -10), (20, 10), dxfattribs=a0); b.add_line((-20, 10), (20, -10), dxfattribs=a0)
    b = _b("T-FAN")                       # kanal tipi fan: daire + kanatlar
    if b is not None:
        b.add_circle((0, 0), 30, dxfattribs=a0)
        for k in range(4):
            t = k * math.pi / 2
            b.add_lwpolyline([(0, 0), (22 * math.cos(t + 0.35), 22 * math.sin(t + 0.35)), (22 * math.cos(t - 0.15), 22 * math.sin(t - 0.15))], close=True, dxfattribs=a0)
    b = _b("T-DAMPER")                    # yangın damperi (kanalda)
    if b is not None:
        b.add_lwpolyline([(-6, -15), (6, -15), (6, 15), (-6, 15)], close=True, dxfattribs=a0)
        b.add_line((-6, -15), (6, 15), dxfattribs=a0)
    b = _b("T-GAZKAPAK")                  # sığınak gaz sızdırmaz basınç kapağı
    if b is not None:
        b.add_circle((0, 0), 12, dxfattribs=a0); b.add_line((-12, 0), (12, 0), dxfattribs=a0)
        b.add_line((0, -12), (0, 12), dxfattribs=a0)
    b = _b("T-KAZAN")                     # duvar tipi yoğuşmalı kazan (plan) 60x45
    if b is not None:
        b.add_lwpolyline([(-30, 0), (30, 0), (30, 45), (-30, 45)], close=True, dxfattribs=a0)
        b.add_circle((0, 22), 9, dxfattribs=a0)
        b.add_text("K", height=8, dxfattribs={"layer": "0", "style": "ROTAS"}).set_placement((0, 22), align=TA.MIDDLE_CENTER)
    b = _b("T-RAD-SEMA")                  # şemada radyatör
    if b is not None:
        b.add_lwpolyline([(-20, 0), (20, 0), (20, 25), (-20, 25)], close=True, dxfattribs=a0)
        for k in range(-16, 20, 6): b.add_line((k, 2), (k, 23), dxfattribs=a0)
    b = _b("T-GENLESME")
    if b is not None:
        b.add_lwpolyline([(-15, 10), (15, 10)], dxfattribs=a0)
        b.add_arc((0, 10), 15, 0, 180, dxfattribs=a0)
        b.add_lwpolyline([(-15, 10), (-15, -20), (15, -20), (15, 10)], dxfattribs=a0)
        b.add_arc((0, -20), 15, 180, 360, dxfattribs=a0)
        b.add_line((-15, -5), (15, -5), dxfattribs=a0)
