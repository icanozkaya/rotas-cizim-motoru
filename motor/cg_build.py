"""Cafer Göktaş konut - sıhhi tesisat + kombili yerden ısıtma (ROTAŞ / MTY blokları)."""
import math, pickle, sys, re
sys.path.insert(0, '/home/claude/nb')
import numpy as np
import cv2
import cad
from cad import *
import mtyblk
from clean import clean
from design import LAYERS, LTYPES, lab_on
import rooms as RM
import cg_rooms
import spiral2 as S2

fl = pickle.load(open('/tmp/claude-0/cg_flat.pkl', 'rb'))
PROJE = "CAFER GÖKTAŞ'A AİT KONUT PROJESİ"
YER = 'SAKARYA / ADAPAZARI - PAPUÇÇULAR MAH. - PAFTA: G24-b-23-c-2-b  ADA: 405  PARSEL: 381'
CS, CH, PS = 'MTY-SOGUKSU-BORU', 'MTY-SICAKSU-BORU', 'MTY-PIS-SU-BORUSU'
TF, VN, CD, YZ = 'MTY-TEFRIS', 'MTY-VANA', 'MTY-CIHAZ', 'MTY-YAZI'
TH = 9.0
FLOORS = [('Z', 'ZEMİN KAT', 0.0, 1), ('1', '1. KAT', 1250.0, 2), ('2', '2. KAT', 2500.0, 3)]
CATI_DX = 3750.0
HDY = -1900.0                    # ısıtma paftaları ötelemesi
PLAN_CX = -5070.0
SHEET_Y = (-23500.0, -21800.0)

# ------------------------------------------------------------------ tasarım verisi (zemin kat koordinatı)
PK = (-4786.0, -22430.0)
MK = (-4944.0, -22655.0)
RISERS = [(-5104.0, -22625.0), (-5114.0, -22625.0), (-5124.0, -22625.0)]
KOMBI_O = (-5345.0, -22962.0)            # KOMBI1 bloğu (180° dönük, baca batıya)
KOMBI_SO = (-5363.0, -22962.0)
KOMBI_SC = (-5373.0, -22962.0)
YS_P = (-4860.0, -22530.0)

FIX = [  # (blok, nokta, dönüş, açıklama, YB, SB, pis çap)
    ('KLOZET1', (-4819.0, -22440.0), 0, 'WC', 0.5, 2.0, 100),
    ('LAVABO1', (-4896.0, -22622.0), 0, 'LV', 0.5, 0.5, 50),
    ('DUS TEKNESI1', (-4908.0, -22440.0), 0, 'DUŞ', 1.0, 0.7, 50),
    ('CAMASIR MAKINASI1', (-4807.0, -22631.0), 0, 'ÇM', 1.0, 0.8, 50),
    ('EVIYE1', (-4896.0, -22668.0), 0, 'EVİYE', 0.5, 0.8, 50),
    ('YER SUZGECI DN501', YS_P, 0, 'YS', 0.0, 0.8, 50),
]
YB_D = sum(f[4] for f in FIX)
SB_BANYO = sum(f[5] for f in FIX if f[3] != 'EVİYE')
SB_MUT = 0.8

COLD = [
    ([(-5060.0, -22625.0), (-5060.0, -22641.0), (-4807.0, -22641.0), (-4807.0, -22633.0)], 'DN25'),
    ([(-4890.0, -22641.0), (-4890.0, -22628.0)], ''),
    ([(-4884.0, -22641.0), (-4884.0, -22656.0)], ''),
    ([(-4945.0, -22641.0), (-4945.0, -22420.0), (-4819.0, -22420.0)], 'DN20'),
    ([(-4914.0, -22420.0), (-4914.0, -22428.0)], ''),
    ([(-5060.0, -22641.0), (-5060.0, -22935.0), (-5363.0, -22935.0), (-5363.0, -22960.0)], 'DN20'),
]
HOT = [
    ([(-5373.0, -22960.0), (-5373.0, -22927.0), (-5052.0, -22927.0), (-5052.0, -22649.0), (-4902.0, -22649.0)], 'DN20'),
    ([(-4902.0, -22649.0), (-4902.0, -22628.0)], ''),
    ([(-4902.0, -22649.0), (-4902.0, -22656.0)], ''),
    ([(-4937.0, -22649.0), (-4937.0, -22428.0), (-4902.0, -22428.0)], 'DN20'),
]
PIS = [
    ([(-4819.0, -22451.0), (-4795.0, -22440.0), (-4789.0, -22432.0)], 'Ø100'),
    ([(-4908.0, -22434.0), (-4880.0, -22470.0), (-4795.0, -22470.0)], 'Ø50'),
    ([(-4896.0, -22611.0), (-4865.0, -22590.0), (-4795.0, -22590.0)], 'Ø50'),
    ([(-4807.0, -22600.0), (-4795.0, -22590.0)], ''),
    ([YS_P, (-4795.0, -22530.0)], 'Ø50'),
    ([(-4795.0, -22600.0), (-4795.0, -22445.0), (-4789.0, -22436.0)], 'Ø70'),
    ([(-4913.0, -22683.0), (-4935.0, -22665.0), (-4941.0, -22659.0)], 'Ø50'),
]
# temel altı / altyapı (zemin)
ALT = [(-4786.0, -22430.0), (-4815.0, -22470.0), (-4815.0, -23120.0)]
ALT2 = [(-4944.0, -22655.0), (-4944.0, -22720.0), (-4815.0, -22790.0)]
R1 = (-4815.0, -23150.0)
PB = (-4815.0, -23300.0)


# ------------------------------------------------------------------ mimari temizlik
KEEP_GEOM = {'DUVAR', 'Kolon', 'kapı', 'tefriş', 'sıva', 'SIVA', 'Standart'}
FURN_L = {'tefriş'}


def arch_items(k_dx, furn=True):
    """zemin+k_dx paftasındaki temizlenmiş mimari öğeler (kaynak koordinatı)"""
    x0, x1 = PLAN_CX + k_dx - 625, PLAN_CX + k_dx + 625
    out = []
    for k, l, d, p in fl:
        q = (d[0], d[1]) if k == 'C' else d[0]
        if not (x0 < q[0] < x1 and -23250 < q[1] < -22080):
            continue
        if k == 'T':
            if l != 'tefriş':
                continue
            t = clean(d[1])
            if d[2] >= 14 or ('m²' in t and len(t) < 12) or t.startswith('DAİRE') or t == 'KOMBİ':
                out.append(('T', (d[0], t, d[2])))
            continue
        if l not in KEEP_GEOM:
            continue
        if not furn and l in FURN_L:
            continue
        out.append((k, d))
    return out


def put_arch(items, dx, dy):
    for k, d in items:
        if k == 'L':
            R.append(('L', 'MIMARI', (d[0][0] + dx, d[0][1] + dy), (d[1][0] + dx, d[1][1] + dy)))
        elif k == 'P':
            R.append(('P', 'MIMARI', [(x + dx, y + dy) for x, y in d], False, 0))
        elif k == 'C':
            R.append(('C', 'MIMARI', (d[0] + dx, d[1] + dy), d[2]))
        elif k == 'T':
            R.append(('T', 'MIMARI', (d[0][0] + dx, d[0][1] + dy), d[1], d[2], 0, 'L'))


# ------------------------------------------------------------------ çerçeve
def frame(x0, y0, x1, y1, title, olc='1/50'):
    RECT(x0, y0, x1, y1, 'MTY-PAFTA')
    RECT(x0 + 25, y0 + 25, x1 - 25, y1 - 25, 'MTY-PAFTA')
    T((x0 + 70, y0 + 230), title, 26, YZ, 'L')
    T((x0 + 70, y0 + 195), 'ÖLÇEK : ' + olc, 16, YZ, 'L')
    bx0, by0, bx1, by1 = x0 + 25, y0 + 25, x1 - 25, y0 + 170
    L((bx0, by1), (bx1, by1), 'MTY-PAFTA')
    L((bx0, by0 + 95), (bx1, by0 + 95), 'MTY-PAFTA')
    T((bx0 + 20, by0 + 115), 'ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK.', 17, YZ, 'L')
    T((bx0 + 20, by0 + 60), PROJE, 11, YZ, 'L')
    T((bx0 + 20, by0 + 40), 'MEKANİK TESİSAT PROJESİ', 11, YZ, 'L')
    T((bx0 + 20, by0 + 15), 'PROJE SORUMLUSU : Mak. Müh. Bayram GENÇ', 10, YZ, 'L')


def sheet_x(k):
    c = PLAN_CX + k * 1250
    return c - 625, c + 625


# ------------------------------------------------------------------ sıhhi kat planı
def kolon_tag(c, txt, side):
    tp = (c[0] + side[0], c[1] + side[1])
    L(c, (tp[0] - (27.5 if side[0] > 0 else -27.5), tp[1]), 'MTY-PISSU-KOLONNO')
    mtyblk.insert('MTY-KOLON NO PIS SU', tp, attrs={'K': txt})


def sihhi_kat(fi):
    key, name, fdx, dno = FLOORS[fi]
    cad.push(MOVE(fdx, 0))
    # armatür bağlantı blokları
    for blk, p, rot, nm, yb, sb, dn in FIX:
        mtyblk.insert(blk, p, rot)
    YER_SUZGECI(YS_P, TF, 15)
    mtyblk.insert('KOMBI1', KOMBI_O, 180)
    T((-5340.0, -22900.0), 'KOMBİ 24 kW', TH, CD, 'L')
    for pl, lb in COLD:
        PL(pl, CS)
        if lb:
            lab_on(pl, lb, 'MTY-TEMIZSU-CAP', h=8, off=6, minlen=60)
    for pl, lb in HOT:
        PL(pl, CH)
        if lb:
            lab_on(pl, lb, 'MTY-TEMIZSU-CAP', h=8, off=-12, minlen=60)
    for pl, lb in PIS:
        PL(pl, PS)
        if lb:
            lab_on(pl, lb, 'MTY-PISSU-CAP', h=8, off=-10, minlen=40)
    # yük birimi etiketleri
    T((-4930.0, -22395.0), 'DUŞ 1.0 YB / 0.7 SB', 7, 'MTY-YUK-BIRIMI', 'L')
    T((-4855.0, -22395.0), 'WC 0.5 YB / 2.0 SB', 7, 'MTY-YUK-BIRIMI', 'L')
    T((-4945.0, -22603.0), 'LV 0.5 YB', 7, 'MTY-YUK-BIRIMI', 'L')
    T((-4835.0, -22560.0), 'ÇM 1.0 YB / 0.8 SB', 7, 'MTY-YUK-BIRIMI', 'L')
    T((-4945.0, -22722.0), 'EVİYE 0.5 YB / 0.8 SB', 7, 'MTY-YUK-BIRIMI', 'L')
    # kolonlar
    mtyblk.insert('MTY-PIS SU KOLON', PK, 0, 0.6)
    mtyblk.insert('MTY-PIS SU KOLON', MK, 0, 0.6)
    kolon_tag(PK, 'PK1', (95, 35))
    kolon_tag(MK, 'MK1', (-40, -95))
    # temiz su kolonları (merdiven holü tesisat boşluğu)
    for i, r in enumerate(RISERS):
        if i + 1 >= dno:
            KOLON(r, 4.5, CS, 'temiz')
    T((-5185.0, -22605.0), 'TS%d..TS3 (DN25)' % dno, 7, 'MTY-TEMIZSU-CAP', 'L')
    rx, ry = RISERS[dno - 1]
    PL([(rx, ry), (-5060.0, ry)], CS)
    VANA((-5082.0, ry), 0.8, 0, VN)
    T((-5075.0, -22605.0), 'D%d: DN25 / %.1f YB' % (dno, YB_D), 7, 'MTY-YUK-BIRIMI', 'L')
    cad.pop()


def zemin_extra():
    """zemin: sayaç nişi + şebeke + pis su altyapı (SASKİ)"""
    # sayaç nişi (bina girişi dış duvarı)
    nx = -5450.0
    RECT(nx - 25, -22700.0, nx + 12, -22640.0, 'MTY-CIHAZ')
    for i, y in enumerate((-22652.0, -22670.0, -22688.0)):
        mtyblk.insert('MTY-SU SAYACI', (nx - 8, y), 0, 0.7)
        PL([(nx - 15, y), (nx - 15, -22700.0)], CS) if False else None
        rx, ry = RISERS[i]
        PL([(nx + 2, y), (rx + 0.0, y), (rx, ry)], CS)
    PL([(nx - 40, -23300.0), (nx - 40, -22652.0)], CS)
    for y in (-22652.0, -22670.0, -22688.0):
        L((nx - 40, y), (nx - 16, y), CS)
    mtyblk.insert('MTY-KURESEL VANA', (nx - 40, -22760.0), 90, 0.8)
    T((nx - 50, -22740.0), 'ANA VANA', 7, VN, 'R')
    T((nx - 50, -23280.0), 'ŞEBEKEDEN (SASKİ) DN32', 8, 'MTY-TEMIZSU-CAP', 'R', 90)
    T((nx - 30, -22625.0), 'SU SAYAÇ NİŞİ (3 ADET DAİRE SAYACI)', 7, VN, 'L')
    # pis su altyapı
    PL(ALT, PS); PL(ALT2, PS)
    lab_on(ALT, 'Ø125 PVC %2', 'MTY-PISSU-CAP', h=8, off=10, minlen=50)
    T((-4930.0, -22735.0), 'Ø100', 8, 'MTY-PISSU-CAP', 'L')
    T((-4775.0, -22850.0), 'TEMEL ALTI PİS SU HATTI', 8, 'MTY-PISSU-CAP', 'L', 90)
    mtyblk.insert('MTY-ROGAR KAT', (R1[0], R1[1] - 45), 0, 0.6, attrs={'R': 'R1'})
    mtyblk.insert('MTY-ROGAR KAT', (PB[0], PB[1] - 45), 0, 0.8, attrs={'R': 'PB'})
    PL([(R1[0], R1[1] - 27), (PB[0], PB[1] + 36)], PS)
    PL([(PB[0], PB[1] - 36), (PB[0], -23420.0)], PS)
    ARROW((PB[0], -23425.0), -90, PS, 14)
    T((R1[0] + 40, R1[1] + 8), 'R1  Ø80 BETON BİLEZİK', 9, 'MTY-ROGAR', 'L')
    T((R1[0] + 40, R1[1] - 6), 'K.K: 29.80  A.K: 29.00  h: 0.80 m', 8, 'MTY-ROGAR', 'L')
    T((PB[0] + 45, PB[1] + 8), 'PB  PARSEL BACASI Ø100', 9, 'MTY-ROGAR', 'L')
    T((PB[0] + 45, PB[1] - 6), 'K.K: 29.75  A.K: 28.85  h: 0.90 m', 8, 'MTY-ROGAR', 'L')
    T((R1[0] + 10, (R1[1] + PB[1]) / 2), 'L=1.0 m / Q=150 / %2', 8, 'MTY-PISSU-CAP', 'L')
    T((PB[0] + 10, -23400.0), 'Ø200 HDPE KORUGE - SASKİ ATIKSU HATTINA', 9, 'MTY-ROGAR', 'L')
    T((PB[0] + 10, -23414.0), '(BAĞLANTI KOTU VE YERİ SASKİ\'DEN ALINACAKTIR)', 7, 'MTY-ROGAR', 'L')


def cati_plan():
    cad.push(MOVE(CATI_DX, 0))
    for c, t in ((PK, 'PK1'), (MK, 'MK1')):
        C(c, 6, PS); C(c, 10, PS)
        T((c[0], c[1] - 22), 'HAVALIK Ø100 (%s)' % t, 8, 'MTY-PISSU-CAP', 'C')
    cad.pop()


# ------------------------------------------------------------------ yerden ısıtma
ROOMS = None


def detect_rooms():
    R0, g = cg_rooms.detect(0)
    out = {}
    for i, r in R0.items():
        nm = r['name']
        if nm.startswith(('ODA', 'BANYO', 'ANTRE', 'SALON')):
            out.setdefault(nm, []).append(r)
    return out, g


EXCL = {
    'SALON VE MUTFAK': [(-5400.0, -23020.0, -5320.0, -22920.0), (-5420.0, -22935.0, -5140.0, -22895.0),
                        (-5180.0, -22935.0, -5120.0, -22690.0), (-5100.0, -22770.0, -5020.0, -22690.0)],
    'BANYO + WC': [(-4955.0, -22500.0, -4860.0, -22405.0), (-4850.0, -22478.0, -4780.0, -22405.0),
                   (-4842.0, -22640.0, -4768.0, -22566.0)],
}


def room_parts(rm, name):
    """mahal maskesini dikdörtgenlere ayır (her dikdörtgen bir devre)"""
    from shapely.geometry import box as _box
    g = ROOMS[1]
    m = rm['mask'].astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 31))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    for x0, y0, x1, y1 in EXCL.get(name, []):
        c0, r0 = g.px((x0, y1)); c1, r1 = g.px((x1, y0))
        m[max(0, r0):r1, max(0, c0):c1] = 0
    rs = RM.rects_in(m > 0, g, inset=10.0, minw=45.0, cover=0.92, maxn=3)
    out = []
    for r in rs:
        if (r[2] - r[0]) * (r[3] - r[1]) < (0.5e4 if name.startswith('BANYO') else 0.9e4):
            continue
        pg = _box(*r)
        dist = abs(pg.centroid.x - KOLL[0]) / 100 + abs(pg.centroid.y - KOLL[1]) / 100
        ln = pg.area / 1e4 / 0.15 + 2 * dist
        out += S2.split_poly(pg, max(1, math.ceil(ln / 88.0)))
    return out


KOLL = (-5063.0, -22420.0)      # kollektör (antre batı duvarı, doğuya bakar)


def isitma_kat(fi, losses):
    key, name, fdx, dno = FLOORS[fi]
    global ROOMS
    if ROOMS is None:
        ROOMS = detect_rooms()
    rd, g = ROOMS
    devs = []
    order = ['ODA', 'ODA2', 'BANYO + WC', 'SALON VE MUTFAK']
    rooms = []
    odas = sorted(rd.get('ODA', []), key=lambda r: -r['area'])
    if odas:
        rooms.append(('ODA', odas[0]))
    if len(odas) > 1:
        rooms.append(('ODA2', odas[1]))
    for nm in ('BANYO + WC', 'SALON VE MUTFAK'):
        if nm in rd:
            rooms.append((nm, rd[nm][0]))
    for nm, rm in rooms:
        for pg in room_parts(rm, nm):
            devs.append((nm, pg))
    n = len(devs)
    cad.push(MOVE(fdx, HDY))
    # kollektör (dikey)
    w = 20 + 10 * n
    kx, ky = KOLL
    RECT(kx - 14, ky - w, kx, ky, 'MTY-KOLLETOR')
    L((kx - 10, ky - 4), (kx - 10, ky - w + 4), 'MTY-KOLLETOR')
    L((kx - 5, ky - 4), (kx - 5, ky - w + 4), 'MTY-KOLLETOR')
    T((kx - 20, ky - w / 2), 'KOLLEKTÖR (%d AĞIZ)' % n, 8, 'MTY-KOLLETOR', 'C', 90)
    # devreler: kuzeye gidenler üst ağızlar
    cy_ = lambda i: devs[i][1].centroid.y
    north = [i for i in range(n) if cy_(i) > ky - w / 2]
    south = [i for i in range(n) if i not in north]
    ordered = sorted(north, key=lambda i: -cy_(i)) + sorted(south, key=lambda i: -cy_(i))
    res = []
    lane_n = 0
    lane_s = 0
    for pi, i in enumerate(ordered):
        nm, pg = devs[i]
        rc = pg.bounds
        py = ky - 10 - pi * 10
        C((kx - 10, py), 1.8, 'MTY-KOLLETOR'); C((kx - 5, py - 4), 1.8, 'MTY-KOLLETOR')
        T((kx + 3, py + 2), 'P%d' % (pi + 1), 5, 'MTY-KOLLETOR', 'L')
        # giriş köşesi: kollektöre en yakın köşe
        from shapely.geometry import Point as _Pt
        from shapely.ops import nearest_points as _np
        x0_, y0_, x1_, y1_ = pg.bounds
        cands = [((x0_, y0_), (0, 0)), ((x1_, y0_), (1, 0)), ((x0_, y1_), (0, 1)), ((x1_, y1_), (1, 1))]
        cp_, cr_ = min(cands, key=lambda c: abs(c[0][0] - kx) + abs(c[0][1] - py))
        path = spiral(x0_ - 10, y0_ - 10, x1_ + 10, y1_ + 10, 15.0, cr_)
        if len(path) < 2:
            continue
        # merkez bağlantısını dik yap
        PL(path, 'MTY-PEX-BORU')
        st, en = path[0], path[-1]
        if i in north:
            lx = kx + 8 + lane_n * 10; lane_n += 1
        else:
            lx = kx + 8 + lane_s * 10; lane_s += 1
        g1 = [(kx, py), (lx, py), (lx, st[1]), st]
        g2 = [(kx, py - 4), (lx + 4, py - 4), (lx + 4, en[1]), en]
        # dönüş yatay ayağı gidişle çakışmasın
        if abs(st[1] - en[1]) < 3:
            g2[2] = (lx + 4, en[1] - 5); g2.insert(3, (en[0], en[1] - 5))
        PL(g1, 'MTY-PEX-BORU'); PL(g2, 'MTY-PEX-BORU')
        Lm = (plen(path) + plen(g1) + plen(g2)) / 100.0
        res.append(dict(port=pi + 1, room=nm, rect=rc, L=Lm, area=pg.area / 1e4, cen=(pg.centroid.x, pg.centroid.y)))
    # ısı kaybı dağıt + etiketler
    zlab = {'ODA': 1, 'ODA2': 2, 'BANYO + WC': 3, 'SALON VE MUTFAK': 4, 'ANTRE': 5}
    for nm in set(d['room'] for d in res):
        ds = [d for d in res if d['room'] == nm]
        tot_a = sum(d['area'] for d in ds)
        Wroom = losses[(key, nm)]
        for d in ds:
            d['W'] = Wroom * d['area'] / tot_a
        z = zlab[nm]
        zl = ('Z%02d' % z) if key == 'Z' else ('%s%02d' % (key, z))
        cx, cy = max(ds, key=lambda d: d['area'])['cen']
        HEXTAG((cx, cy + 22), 'MTY-ISIKAYBIMAHAL', zl, '24°C' if 'BANYO' in nm else '20°C', 10)
        T((cx, cy - 4), 'Kcal/h: %.0f' % (Wroom * 0.86), 8, 'MTY-ISIKAYBIMAHAL', 'C')
        for d in ds:
            d['zl'] = zl
    for d in res:
        cx, cy = d['cen']
        yo = -20 if d['area'] == max(x['area'] for x in res if x['room'] == d['room']) else 10
        T((cx, cy + yo), '%d / PEX BORU, 16 × 2.0 %.1fW' % (d['port'], d['W']), 6.5, 'MTY-ISIKAYBIMAHAL', 'C')
        T((cx, cy + yo - 10), '15.0 / %.2f m / %s' % (d['L'], d['zl']), 6.5, 'MTY-ISIKAYBIMAHAL', 'C')
    # antre: geçiş boruları ile
    tot = sum(d['W'] for d in res) + losses[(key, 'ANTRE')]
    zl = ('Z05' if key == 'Z' else '%s05' % key)
    HEXTAG((-5020.0, -22560.0), 'MTY-ISIKAYBIMAHAL', zl, '20°C', 10)
    T((-5020.0, -22585.0), 'Kcal/h: %.0f' % (losses[(key, 'ANTRE')] * 0.86), 7, 'MTY-ISIKAYBIMAHAL', 'C')
    T((-5020.0, -22597.0), '(DEVRE GEÇİŞLERİ İLE)', 6, 'MTY-ISIKAYBIMAHAL', 'C')
    # kombi -> kollektör
    gpath = [(-5368.0, -22925.0), (-5368.0, -22915.0), (-5160.0, -22915.0), (-5160.0, -22700.0),
             (-5072.0, -22700.0), (-5072.0, ky - w - 6), (kx - 10, ky - w - 6), (kx - 10, ky - w)]
    dpath = [(-5378.0, -22925.0), (-5378.0, -22907.0), (-5152.0, -22907.0), (-5152.0, -22708.0),
             (-5066.0, -22708.0), (-5066.0, ky - w - 12), (kx - 5, ky - w - 12), (kx - 5, ky - w)]
    PL(gpath, 'MTY-ISITMA-GIDIS-BORU'); PL(dpath, 'MTY-ISITMA-DONUS-BORU')
    T((-5270.0, -22900.0), '%.1fW-DN20' % tot, 8, 'STM-ISITMA-CAP', 'C')
    mtyblk.insert('KOMBI1', KOMBI_O, 180)
    T((-5340.0, -22885.0), 'DUVARA ASILABİLEN HERMETİK KOMBİ', 7, CD, 'L')
    T((-5340.0, -22875.0), 'KAPASİTE : 24 kw', 7, CD, 'L')
    cad.pop()
    return res, tot


# ------------------------------------------------------------------ kolon şeması (sıhhi)
def sihhi_sema(ox, oy):
    """ox,oy: pafta sol alt. Katlar: zemin, 1, 2 (300 cm)"""
    base = oy + 420
    FH = 330
    lv = {0: base, 1: base + FH, 2: base + 2 * FH, 3: base + 3 * FH}
    names = ['ZEMİN KAT (+1.00)', '1. KAT (+4.00)', '2. KAT (+7.00)', 'ÇATI']
    for k in range(4):
        L((ox + 60, lv[k]), (ox + 1940, lv[k]), 'MTY-SEMA')
        L((ox + 60, lv[k] - 25), (ox + 1940, lv[k] - 25), 'MTY-SEMA')
        T((ox + 70, lv[k] + 8), names[k], 13, YZ, 'L')
    T((ox + 1000, oy + 1640), 'SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI', 26, YZ, 'C')
    xs = {'SAYAC': ox + 420, 'KOMBI': ox + 560, 'LV': ox + 720, 'DUS': ox + 870, 'WC': ox + 1020, 'CM': ox + 1170,
          'PK': ox + 1300, 'EV': ox + 1480, 'MK': ox + 1620}
    for k in range(3):
        y = lv[k]
        # bloklar
        mtyblk.insert('KOMBI1 KOLON', (xs['KOMBI'], y), 0, 1, attrs={'SO': '', 'SC': ''})
        mtyblk.insert('LAVABO1 KOLON', (xs['LV'], y), 0, 1, attrs={'SO': '0.5', 'SOCP': 'Ø20', 'SC': '0.5', 'SCCP': 'Ø20', 'PS': '0.5', 'PSCP': 'Ø50'})
        mtyblk.insert('DUS TEKNESI1 KOLON', (xs['DUS'], y), 0, 1, attrs={'SO': '1.0', 'SOCP': 'Ø20', 'SC': '1.0', 'SCCP': 'Ø20', 'PS': '0.7', 'PSCP': 'Ø50'})
        mtyblk.insert('KLOZET1 KOLON', (xs['WC'], y), 0, 1, attrs={'SO': '0.5', 'SOCP': 'Ø20', 'PS': '2.0', 'PSCP': 'Ø100'})
        mtyblk.insert('CAMASIR MAKINASI1 KOLON', (xs['CM'], y), 0, 1, attrs={'SO': '1.0', 'SOCP': 'Ø20', 'PS': '0.8', 'PSCP': 'Ø50'})
        mtyblk.insert('EVIYE1 KOLON', (xs['EV'], y), 0, 1, attrs={'SO': '0.5', 'SOCP': 'Ø20', 'SC': '0.5', 'SCCP': 'Ø20', 'PS': '0.8', 'PSCP': 'Ø50'})
        mtyblk.insert('YER SUZGECI DN501 KOLON', (xs['CM'] + 70, y), 0, 1, attrs={'PS': '0.8', 'PSCP': 'Ø50'})
        # soğuk / sıcak dağıtım hatları
        L((xs['SAYAC'], y + 130), (xs['EV'], y + 130), CS)
        L((xs['KOMBI'] - 15, y + 135), (xs['EV'] - 15, y + 135), CH)
        T((xs['KOMBI'] + 30, y + 141), 'DN20 SICAK SU', 7, 'MTY-TEMIZSU-CAP', 'L')
        T((xs['SAYAC'] + 20, y + 118), 'DN25 / %.1f YB' % YB_D, 7, 'MTY-YUK-BIRIMI', 'L')
        T((xs['KOMBI'] - 40, y + 285), 'DAİRE %d' % (k + 1), 14, YZ, 'L')
        # pis yatay hatlar (döşeme içi)
        L((xs['LV'], y), (xs['PK'], y - 12), PS)
        L((xs['EV'], y), (xs['MK'], y - 12), PS)
        T((xs['DUS'] + 20, y - 22), 'Ø70 / %.1f SB  %%2' % (SB_BANYO - 2.0), 7, 'MTY-PISSU-CAP', 'L')
        T((xs['EV'] + 20, y - 22), 'Ø50 / 0.8 SB', 7, 'MTY-PISSU-CAP', 'L')
    # sayaçlar + yükselen hatlar (zeminde)
    for i in range(3):
        sx = ox + 200 + i * 60
        mtyblk.insert('SU SAYAC1 KOLON', (sx, lv[0] - 40), 0, 0.7, attrs={'SO': 'S%d' % (i + 1), 'SOCP': ''})
        top = lv[i] + 130
        PL([(sx, lv[0] - 40 + 0.7 * 130), (sx, top), (xs['SAYAC'], top)], CS)
        T((sx - 6, lv[0] + 200), 'TS%d DN25' % (i + 1), 7, 'MTY-TEMIZSU-CAP', 'L', 90)
    PL([(ox + 120, lv[0] - 60), (ox + 200 + 2 * 60 + 20, lv[0] - 60)], CS)
    for i in range(3):
        sx = ox + 200 + i * 60 - 0.7 * 30
        L((sx, lv[0] - 60), (sx, lv[0] - 40 + 0.7 * 130), CS)
    mtyblk.insert('MTY-KURESEL VANA', (ox + 150, lv[0] - 60), 0, 0.8)
    T((ox + 90, lv[0] - 85), 'ŞEBEKEDEN (SASKİ) DN32', 8, 'MTY-TEMIZSU-CAP', 'L')
    T((ox + 190, lv[0] - 105), 'SU SAYAÇ NİŞİ (ZEMİN, BİNA GİRİŞİ)', 7, VN, 'L')
    # pis su kolonları
    for nm, x, sb in (('PK1', xs['PK'], SB_BANYO), ('MK1', xs['MK'], SB_MUT)):
        top = lv[3] + 80
        bot = lv[0] - 140
        L((x, bot), (x, top), PS)
        mtyblk.insert('MTY-KOLON HAVALIK SAPKASI', (x, top), 0, 1.5)
        mtyblk.insert('MTY-TEMIZLEME KAPAGI KOLON', (x, lv[0] - 60), 0, 1)
        mtyblk.insert('MTY-PIS SU KOLON NO', (x, top + 70), 0, 0.8, attrs={'K': nm})
        for k in range(3):
            T((x + 8, lv[k] + 60), 'Ø100 / %.1f SB' % (sb * (3 - k)), 7, 'MTY-PISSU-CAP', 'L', 90)
    L((xs['PK'], lv[0] - 140), (xs['MK'] + 60, lv[0] - 140), PS)
    T((xs['PK'] + 60, lv[0] - 133), 'Ø125 / %.1f SB  TEMEL ALTI %%2' % (3 * (SB_BANYO + SB_MUT)), 8, 'MTY-PISSU-CAP', 'L')
    mtyblk.insert('MTY-KOLON ROGAR', (xs['MK'] + 60, lv[0] - 140), 0, 1, attrs={'R': 'R1'})
    T((xs['MK'] + 150, lv[0] - 150), '-> PB -> SASKİ', 9, 'MTY-ROGAR', 'L')


# ------------------------------------------------------------------ yerden ısıtma kolon şeması
def isitma_sema(ox, oy, H):
    T((ox + 1000, oy + 1640), 'YERDEN ISITMA KOLON ŞEMASI', 26, YZ, 'C')
    for k in range(3):
        y = oy + 330 + k * 420
        L((ox + 60, y), (ox + 1940, y), 'MTY-SEMA')
        T((ox + 70, y + 8), FLOORS[k][1], 13, YZ, 'L')
        res, tot = H[k]
        kx = ox + 200
        RRECT(kx, y + 60, kx + 60, y + 160, 4, CD); C((kx + 30, y + 120), 12, CD)
        T((kx + 30, y + 40), 'H. KOMBİ 24KW', 8, CD, 'C')
        T((kx + 30, y + 175), 'DAİRE %d' % (k + 1), 12, YZ, 'C')
        n = len(res)
        c0, c1 = kx + 160, kx + 160 + n * 140
        RECT(c0 - 10, y + 70, c1 + 10, y + 110, 'MTY-KOLLETOR')
        L((c0, y + 100), (c1, y + 100), 'MTY-ISITMA-GIDIS-BORU')
        L((c0, y + 80), (c1, y + 80), 'MTY-ISITMA-DONUS-BORU')
        PL([(kx + 60, y + 130), (c0 - 10, y + 130), (c0 - 10, y + 100)], 'MTY-ISITMA-GIDIS-BORU')
        PL([(kx + 60, y + 70), (c0 - 20, y + 70), (c0 - 20, y + 80), (c0 - 10, y + 80)], 'MTY-ISITMA-DONUS-BORU')
        T((kx + 70, y + 136), '%.1fW-DN20' % tot, 7, 'STM-ISITMA-CAP', 'L')
        for j, d in enumerate(res):
            px = c0 + 70 + j * 140
            L((px - 5, y + 100), (px - 5, y + 330), 'MTY-PEX-BORU')
            L((px + 5, y + 80), (px + 5, y + 330), 'MTY-PEX-BORU')
            L((px - 5, y + 330), (px + 5, y + 330), 'MTY-PEX-BORU')
            T((px, y + 58), 'P%d' % d['port'], 8, 'MTY-KOLLETOR', 'C')
            T((px - 12, y + 125), 'ISIKAYBI %d / %.1fW / %.2f m / %s' % (d['port'], d['W'], d['L'], d['zl']), 7, 'MTY-ISIKAYBIMAHAL', 'L', 90)
            T((px + 18, y + 125), '%s / PEX BORU 16x2.0 / %.1fW-DN15' % ('24°C' if 'BANYO' in d['room'] else '20°C', d['W']), 7, 'STM-ISITMA-CAP', 'L', 90)


# ------------------------------------------------------------------ lejant / notlar / antet
NOTES = [
    'Temiz su tesisatı PPRC PN20 borularla yapılacak, duvar içi borular izolasyonlu olarak döşenecektir.',
    'Daire su sayaçları zemin kat bina girişindeki su sayaç nişine SASKİ şartlarına uygun olarak monte edilecektir.',
    'Sayaçlardan önce DN x 10, sonra DN x 5 uzunluğunda düz boru bırakılacaktır.',
    'Her daire girişinde küresel vana konulacaktır.',
    'Sıcak kullanma suyu her dairede duvar tipi hermetik kombiden sağlanacaktır.',
    'Pis su tesisatı TS EN 1451 çok katmanlı PVC borularla, yatay hatlarda en az %2 eğimle yapılacaktır.',
    'Pis su kolonları çatıdan Ø100 havalık olarak çıkarılacak ve ucuna havalık şapkası takılacaktır.',
    'Her kolon dibinde temizleme kapağı bırakılacaktır.',
    'Bina pis suları R1 rögarı ve parsel bacası üzerinden SASKİ atıksu hattına bağlanacaktır.',
    'Parsel bacası bağlantı kotu ve yeri SASKİ\'den alınacak, bağlantı SASKİ denetiminde yapılacaktır.',
    'Yağmur suları pis su hattına bağlanmayacaktır.',
    'Yerden ısıtma devreleri PEX 16x2.0 borularla 15 cm aralıkla salyangoz düzende döşenecektir.',
    'Bir devre boyu 100 m yi geçmeyecek, devreler kollektörde debi ayarlı vanalarla dengelenecektir.',
    'Döşemede ısı yalıtımı, kenar bandı, folyo ve 5 cm şap uygulaması yapılacaktır.',
    'Kombi bacaları hermetik koaksiyel baca olarak dış cepheye çıkarılacaktır.',
    'Tesisat tamamlandıktan sonra temiz su hatlarına 10 bar, ısıtma devrelerine 6 bar basınç testi yapılacaktır.',
    'Tüm imalat TS 1258, TS EN 12056 ve TS EN 1264 standartlarına uygun olarak yapılacaktır.',
]


def lejant(x, y):
    T((x, y), 'LEJANT', 18, YZ, 'L')
    items = [
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), CS), 'SOĞUK SU BORUSU (PPRC)'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), CH), 'SICAK SU BORUSU (PPRC)'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), PS), 'PİS SU BORUSU (PVC)'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), 'MTY-PEX-BORU'), 'PEX BORU 16x2.0'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), 'MTY-ISITMA-GIDIS-BORU'), 'ISITMA GİDİŞ'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), 'MTY-ISITMA-DONUS-BORU'), 'ISITMA DÖNÜŞ'),
        (lambda p: mtyblk.insert('KLOZET1', p), 'KLOZET BAĞLANTISI'),
        (lambda p: mtyblk.insert('LAVABO1', p), 'LAVABO BAĞLANTISI'),
        (lambda p: mtyblk.insert('DUS TEKNESI1', p), 'DUŞ BAĞLANTISI'),
        (lambda p: mtyblk.insert('EVIYE1', p), 'EVİYE BAĞLANTISI'),
        (lambda p: mtyblk.insert('CAMASIR MAKINASI1', (p[0], p[1] - 25), 0, 0.6), 'ÇAMAŞIR MAKİNESİ'),
        (lambda p: mtyblk.insert('YER SUZGECI DN501', p, 0, 2), 'YER SÜZGECİ Ø50'),
        (lambda p: mtyblk.insert('KOMBI1', (p[0] - 30, p[1] - 10), 0, 0.6), 'HERMETİK KOMBİ 24 kW'),
        (lambda p: mtyblk.insert('MTY-SU SAYACI', p), 'SU SAYACI'),
        (lambda p: mtyblk.insert('MTY-KURESEL VANA', p), 'KÜRESEL VANA'),
        (lambda p: mtyblk.insert('MTY-PIS SU KOLON', p, 0, 0.6), 'PİS SU KOLONU'),
        (lambda p: KOLON(p, 5, CS, 'temiz'), 'TEMİZ SU KOLONU'),
        (lambda p: mtyblk.insert('MTY-ROGAR KAT', (p[0], p[1] - 22), 0, 0.5, attrs={'R': 'R'}), 'RÖGAR / PARSEL BACASI'),
        (lambda p: HEXTAG(p, 'MTY-ISIKAYBIMAHAL', 'Z01'), 'ISI KAYBI MAHAL ETİKETİ'),
    ]
    for i, (f, s) in enumerate(items):
        col, row = divmod(i, 10)
        p = (x + 60 + col * 520, y - 60 - row * 62)
        f(p)
        T((p[0] + 70, p[1] - 4), s, 10, YZ, 'L')


def antet(x, y):
    w, h = 1650, 820
    RECT(x, y - h, x + w, y, 'MTY-PAFTA')
    T((x + w / 2, y - 55), 'ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK.', 34, YZ, 'C')
    T((x + w / 2, y - 90), 'Semerciler Mah. Sait Faik Sk. No:22/C Z01 Adapazarı/Sakarya', 13, YZ, 'C')
    T((x + w / 2, y - 112), 'rotasmuhendislik@gmail.com   0264 272 00 49', 13, YZ, 'C')
    L((x, y - 130), (x + w, y - 130), 'MTY-PAFTA')
    T((x + w / 2, y - 170), PROJE, 20, YZ, 'C')
    T((x + w / 2, y - 200), 'SIHHİ TESİSAT VE YERDEN ISITMA (KOMBİLİ) PROJESİ', 18, YZ, 'C')
    T((x + w / 2, y - 225), YER, 11, YZ, 'C')
    L((x, y - 245), (x + w, y - 245), 'MTY-PAFTA')
    rows = [('YAPININ ÖZELLİKLERİ', ''), ('YAPI SAHİBİ', 'CAFER GÖKTAŞ'), ('YAPI CİNSİ', 'KONUT / BETONARME'),
            ('YAPI SINIFI', '3A'), ('KAT ADEDİ', 'ZEMİN + 2 KAT'), ('BAĞIMSIZ BÖLÜM', '3 DAİRE'),
            ('ISITMA', '3 x 24 kW HERMETİK KOMBİ + YERDEN ISITMA'), ('SU TEMİNİ', 'ŞEBEKE (SASKİ), DEPO / HİDROFOR YOK'),
            ('ARSANIN ÖZELLİKLERİ', ''), ('İLİ / İLÇESİ', 'SAKARYA / ADAPAZARI'), ('MAHALLESİ', 'PAPUÇÇULAR'),
            ('PAFTA / ADA / PARSEL', 'G24-b-23-c-2-b / 405 / 381'), ('ARSA ALANI', '103.84 m²')]
    yy = y - 275
    for a, b in rows:
        T((x + 30, yy), a, 12 if b else 14, YZ, 'L')
        if b:
            T((x + 480, yy), ': ' + b, 12, YZ, 'L')
        yy -= 27
    L((x, y - h + 150), (x + w, y - h + 150), 'MTY-PAFTA')
    L((x + w / 2, y - h), (x + w / 2, y - h + 150), 'MTY-PAFTA')
    T((x + 30, y - h + 115), 'PROJE SORUMLUSU', 12, YZ, 'L')
    T((x + 30, y - h + 75), 'Mak. Müh. Bayram GENÇ', 16, YZ, 'L')
    T((x + w / 2 + 30, y - h + 115), 'ONAY', 12, YZ, 'L')
    T((x + w / 2 + 30, y - h + 85), '14.06.1999 T. 23725 S. VE 08.05.2000 T. 24043 S. RESMİ', 8, YZ, 'L')
    T((x + w / 2 + 30, y - h + 72), 'GAZETE YÖNETMELİKLERİNE UYULMASI KAYDIYLA', 8, YZ, 'L')


def notlar(x, y):
    T((x, y), 'PROJE NOTLARI', 18, YZ, 'L')
    for i, n in enumerate(NOTES):
        T((x, y - 35 - i * 22), '%d. %s' % (i + 1, n), 9.5, YZ, 'L')
    yy = y - 35 - len(NOTES) * 22 - 20
    for s in ('DİKKAT: MİMARİ PROJENİN ONAY AŞAMASINDA YAPILACAK DEĞİŞİKLİKTEN FEN İŞLERİ MD. BİLGİLENDİRİLMESİ',
              'BU PROJE MÜELLİFİN İZNİ OLMADAN YAYINLANAMAZ-ÇOĞALTILAMAZ-KULLANILAMAZ-DEĞİŞTİRİLEMEZ.'):
        T((x, yy), s, 9.5, YZ, 'L'); yy -= 22
