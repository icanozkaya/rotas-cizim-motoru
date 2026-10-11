"""Sıhhi tesisat + yerden ısıtma plan çizimi (MTY katmanları)."""
import math
import cad
from cad import *
from types_def import *

LAYERS = {
    'MIMARI': (8, 'CONTINUOUS'),
    'MTY-SOGUKSU-BORU': (5, 'CONTINUOUS'), 'MTY-SICAKSU-BORU': (1, 'BASMA HATTI'),
    'MTY-PIS-SU-BORUSU': (6, 'PIS'), 'MTY-PISSU-BORU-TAVANDAN': (6, 'PISSU HATTI'),
    'MTY-PISSU-CAP': (211, 'CONTINUOUS'), 'MTY-PISSU-KOLON': (211, 'DASHED'),
    'MTY-PISSU-KOLONNO': (211, 'CONTINUOUS'),
    'MTY-TEMIZSU-CAP': (101, 'CONTINUOUS'), 'MTY-YUK-BIRIMI': (7, 'CONTINUOUS'),
    'MTY-YAGMUR-BORUSU': (3, 'YAGMUR HATTI'), 'MTY-YAGMUR-BORUSU-CAP': (3, 'CONTINUOUS'),
    'MTY-ROGAR': (5, 'CONTINUOUS'), 'MTY-VANA': (1, 'CONTINUOUS'), 'MTY-TEFRIS': (15, 'CONTINUOUS'),
    'MTY-CIHAZ': (135, 'CONTINUOUS'), 'RAST-TEM-SU DEPOSU': (11, 'CONTINUOUS'),
    'MTY-ISITMA-GIDIS-BORU': (10, 'CONTINUOUS'), 'MTY-ISITMA-DONUS-BORU': (30, 'ISITMA DONUS HATTI'),
    'STM-ISITMA-CAP': (41, 'CONTINUOUS'), 'MTY-PEX-BORU': (1, 'CONTINUOUS'),
    'MTY-ISIKAYBIMAHAL': (2, 'CONTINUOUS'), 'MTY-KOLLETOR': (7, 'CONTINUOUS'),
    'MTY-HESAP': (1, 'CONTINUOUS'), 'MTY-YAZI': (7, 'CONTINUOUS'), 'MTY-PAFTA': (7, 'CONTINUOUS'),
    'MTY-SEMA': (7, 'CONTINUOUS'), 'MTY-ELEKTRIK': (30, 'DASHDOT'),
    'MTY-PVC': (43, 'CONTINUOUS'), 'MTY-KAT-ADI': (1, 'CONTINUOUS'),
}
LTYPES = {'DASHED': (12, 6), 'DASHDOT': (14, 6), 'BASMA HATTI': (25, 6), 'PIS': (30, 8), 'PISSU HATTI': (20, 6),
          'YAGMUR HATTI': (30, 6), 'ISITMA DONUS HATTI': (20, 6)}

CS, CH, PS, PT = 'MTY-SOGUKSU-BORU', 'MTY-SICAKSU-BORU', 'MTY-PIS-SU-BORUSU', 'MTY-PISSU-BORU-TAVANDAN'
TF, VN, CD, YZ = 'MTY-TEFRIS', 'MTY-VANA', 'MTY-CIHAZ', 'MTY-YAZI'
TH = 10.0   # plan etiket yüksekliği


def mid(pts):
    """en uzun parçanın ortası ve açısı"""
    best = (0, pts[0], 0)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        if l > best[0]:
            best = (l, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
    return best


def lab_on(pts, s, lay, h=TH * 0.8, off=6, minlen=40):
    l, m, ang = mid(pts)
    if l < minlen:
        return
    # dünya açısı (ayna sonrası)
    a = P(pts[0]); b = P(pts[-1])
    p0 = P(m)
    # metni parçaya paralel, okunur yönde yaz
    wa, wb = None, None
    for i in range(len(pts) - 1):
        q0, q1 = pts[i], pts[i + 1]
        if abs(math.hypot(q1[0] - q0[0], q1[1] - q0[1]) - l) < 1e-6:
            wa, wb = P(q0), P(q1)
            break
    ang = math.degrees(math.atan2(wb[1] - wa[1], wb[0] - wa[0]))
    if ang > 90.01 or ang < -89.99:
        ang += 180
    ang = (ang + 180) % 360 - 180
    nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
    cad.R.append(('T', lay, (p0[0] + nx * off, p0[1] + ny * off), s, h, ang, 'C'))


# ------------------------------------------------------------------ sıhhi daire
def fixtures(t):
    for f in t['fix']:
        k = f[0]
        if k == 'WC':
            WC(f[1], f[2], TF)
        elif k == 'LV':
            LAVABO(f[1], f[2], TF)
        elif k == 'EV':
            EVIYE(f[1], f[2], TF)
        elif k == 'DUS':
            DUS(*f[1], TF)
        elif k == 'CM':
            MAKINE(f[1], TF, 'CM')
        elif k == 'BM':
            MAKINE(f[1], TF, 'BM')
        elif k == 'YS':
            YER_SUZGECI(f[1], TF)


def kombi(t, label=True, heat=False):
    o, d = t['kombi']
    KOMBI_PLAN(o, d, CD)
    if label:
        dx = {'E': (60, 0), 'W': (-75, 0)}[d]
        c = (o[0] + dx[0], o[1] + 22)
        T(c, 'KOMBİ', TH, CD, 'C')
        if heat:
            T((c[0], c[1] - 14), '24 kW', TH * 0.8, CD, 'C')


def sihhi_daire(no, tip, kat_no):
    t = TYPES[tip]
    fixtures(t)
    kombi(t)
    for pl in t['cold']:
        PL(pl, CS)
    for pl in t['hot']:
        PL(pl, CH)
    for pl, dn in t['pis']:
        PL(pl, PS)
    # çap etiketleri
    lab_on(t['cold'][0], 'DN25', 'MTY-TEMIZSU-CAP')
    lab_on(t['cold'][3] if tip == 'A' else t['cold'][3], 'DN25', 'MTY-TEMIZSU-CAP')
    lab_on(t['hot'][0], 'DN20', 'MTY-TEMIZSU-CAP', off=-12)
    for pl, dn in t['pis']:
        lab_on(pl, 'Ø%d' % dn, 'MTY-PISSU-CAP', off=-10, minlen=60)
    # vanalar: daire girişi + kombi soğuk girişi + banyo/mutfak ara vanaları
    e = t['E']; c0 = t['cold'][0]
    VANA(((e[0] + c0[1][0]) / 2, (e[1] + c0[1][1]) / 2), 1.0, 90, VN)
    kc = t['cold'][-1] if tip == 'A' else [c for c in t['cold'] if abs(c[-1][0] - t['kombi'][0][0]) < 40][0]
    VANA(((kc[-2][0] + kc[-1][0]) / 2, (kc[-2][1] + kc[-1][1]) / 2), 0.8,
         90 if abs(kc[-1][0] - kc[-2][0]) < 1 else 0, VN)
    # kolonlar
    KOLON(t['PK'], 6.5, 'MTY-PISSU-KOLON')
    KOLON(t['MK'], 6.5, 'MTY-PISSU-KOLON')
    pk, mk = t['PK'], t['MK']
    T((pk[0], pk[1] + 12), 'PK-%d' % no, TH, 'MTY-PISSU-KOLONNO', 'C')
    T((pk[0], pk[1] - 20), 'Ø100', TH * 0.8, 'MTY-PISSU-CAP', 'C')
    T((mk[0] - 2, mk[1] - 20), 'MK-%d' % no, TH, 'MTY-PISSU-KOLONNO', 'C')
    T((mk[0] - 2, mk[1] - 32), 'Ø100', TH * 0.8, 'MTY-PISSU-CAP', 'C')
    # daire girişi yük birimi
    tot = sum(YB[f[0]] for f in t['fix'] if f[0] in YB)
    T((e[0], e[1] + (40 if e[1] > YM else -40)), 'D%d: DN25 / %.2f YB' % (kat_no, tot), TH * 0.8, 'MTY-YUK-BIRIMI', 'C')


def daire_tf(no, floor_dx, extra=(0, 0)):
    tip, ops, mi = DAIRES[no]
    cad.push(MOVE(floor_dx + extra[0], extra[1]))
    for op in ops:
        cad.push(op)
    return tip, len(ops) + 1


def pop_n(n):
    for _ in range(n):
        cad.pop()


def corridor(no, kat_no, floor_dx, extra):
    """sayaçtan daire girişine koridor hattı (aynasız)."""
    tip, ops, mi = DAIRES[no]
    # daire girişi dünya (zemin) koordinatı
    cad.push(MOVE(0, 0))
    for op in ops:
        cad.push(op)
    e = cad.P(TYPES[tip]['E'])
    pop_n(len(ops) + 1)
    mx = METER_X[mi]
    yc = -9548.0 - 6 * mi
    cad.push(MOVE(floor_dx + extra[0], extra[1]))
    PL([(mx, METER_Y + 12), (mx, yc), (e[0], yc), e], CS)
    SAYAC((mx, METER_Y), 0.9, 90, VN)
    VANA((mx, METER_Y + 24), 0.8, 90, VN)
    T((mx + 4, METER_Y - 22), 'S%d' % kat_no, 7, VN, 'C')
    cad.pop()


def sayac_grubu(floor_dx, extra, label_yb):
    cad.push(MOVE(floor_dx + extra[0], extra[1]))
    x0 = ADK[0]
    PL([(x0, METER_Y), (METER_X[-1], METER_Y - 14), ][:1] + [(x0, METER_Y - 14), (METER_X[-1], METER_Y - 14)], CS)
    for mx in METER_X:
        L((mx, METER_Y - 14), (mx, METER_Y - 7), CS)
    KOLON(ADK, 6, CS, 'temiz')
    KOLON(DBK, 6, CS, 'temiz')
    T((ADK[0] - 10, METER_Y - 34), 'ADK DN50', 8, 'MTY-TEMIZSU-CAP', 'R')
    T((DBK[0] - 10, METER_Y - 22), 'DBK DN40', 8, 'MTY-TEMIZSU-CAP', 'R')
    T((80733, -9628), 'SAYAÇ GRUBU (ENERJİ ODASI)', 8, VN, 'C')
    T((80733, -9712), label_yb, 8, 'MTY-YUK-BIRIMI', 'C')
    cad.pop()


# ------------------------------------------------------------------ ısıtma
def loc2base(o, d, u, v):
    a = math.radians(DIRS[d])
    return (o[0] + u * math.cos(a) - v * math.sin(a), o[1] + u * math.sin(a) + v * math.cos(a))


def heat_rooms(tip, ffac):
    """oda listesi -> devreler [(oda, rect, W)]"""
    t = TYPES[tip]
    out = []
    for name, area, rects, q in t['rooms']:
        Q = area * q * ffac
        ra = [r for r in rects if (r[2] - r[0]) * (r[3] - r[1]) >= 1.0e4]
        tot = sum((r[2] - r[0]) * (r[3] - r[1]) for r in ra)
        devs = []
        for r in ra:
            # 100 m sınırı: tek devre ~ alan/0.15 + 2*bağlantı
            a = (r[2] - r[0]) * (r[3] - r[1]) / 1e4
            ko = t['koll'][0]
            dist = abs((r[0] + r[2]) / 2 - ko[0]) / 100 + abs((r[1] + r[3]) / 2 - ko[1]) / 100
            ln = a / 0.15 + 2 * dist
            parts = max(1, math.ceil(ln / 95.0))
            if parts == 1:
                devs.append(r)
            else:
                w, h = r[2] - r[0], r[3] - r[1]
                for i in range(parts):
                    if w >= h:
                        devs.append((r[0] + w * i / parts, r[1], r[0] + w * (i + 1) / parts, r[3]))
                    else:
                        devs.append((r[0], r[1] + h * i / parts, r[2], r[1] + h * (i + 1) / parts))
        for r in devs:
            out.append((name, area, r, Q * (r[2] - r[0]) * (r[3] - r[1]) / tot))
    return out


def isitma_daire(no, tip, ffac, zone0, kat):
    """döner: (devre listesi, toplam W)"""
    t = TYPES[tip]
    kombi(t, True, True)
    ko, kd = t['koll']
    devs = heat_rooms(tip, ffac)
    n = len(devs)
    KOLLEKTOR_PLAN(ko, kd, n, 'MTY-KOLLETOR')
    w = 20 + 9 * n
    res = []
    zone = zone0
    lastroom = None
    # oda etiketleri
    roomtags = {}
    for i, (name, area, r, W) in enumerate(devs):
        if name != lastroom:
            zone += 1
            lastroom = name
            roomtags[name] = (zone, r)
        z = roomtags[name][0]
        # giriş köşesi: kollektöre en yakın köşe
        cands = [((r[0], r[1]), (0, 0)), ((r[2], r[1]), (1, 0)), ((r[0], r[3]), (0, 1)), ((r[2], r[3]), (1, 1))]
        pg = loc2base(ko, kd, -w / 2 + 14 + i * 9 - 1.5, 14)
        pr = loc2base(ko, kd, -w / 2 + 14 + i * 9 + 1.5, 14)
        cp, cr = min(cands, key=lambda c: math.hypot(c[0][0] - pg[0], c[0][1] - pg[1]))
        path = spiral(r[0], r[1], r[2], r[3], 15.0, cr)
        PL(path, 'MTY-PEX-BORU')
        st, en = path[0], path[-1]
        # bağlantı: kollektör yüzünden dışarı e kadar, sonra L
        e = 10 + 5 * i
        og = loc2base(ko, kd, -w / 2 + 14 + i * 9 - 1.5, 14 + e)
        orr = loc2base(ko, kd, -w / 2 + 14 + i * 9 + 1.5, 14 + e + 3)
        vertical_face = kd in ('E', 'W')

        def route(a, o, b, sh):
            if vertical_face:     # önce x yönünde çık, sonra y, sonra x
                return [a, o, (o[0], b[1] + sh), (b[0], b[1] + sh), b] if False else [a, o, (o[0], b[1]), b]
            return [a, o, (b[0], o[1]), b]
        cg = route(pg, og, st, 0)
        crr = route(pr, orr, en, 0)
        PL(cg, 'MTY-PEX-BORU'); PL(crr, 'MTY-PEX-BORU')
        L_m = (plen(path) + plen(cg) + plen(crr)) / 100.0
        res.append(dict(no=i + 1, room=name, W=W, L=L_m, zone=z, rect=r))
        # devre etiketi
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        zl = ('Z%02d' % z) if kat == 'Z' else ('%s%02d' % (kat, z))
        res[-1]['zl'] = zl
        T((cx, cy - 22), '%d / PEX BORU, 16 × 2.0 %.1fW' % (i + 1, W), 7, 'MTY-ISIKAYBIMAHAL', 'C')
        T((cx, cy - 32), '15.0 / %.2f m / %s' % (L_m, zl), 7, 'MTY-ISIKAYBIMAHAL', 'C')
        # port numarası
        pn = loc2base(ko, kd, -w / 2 + 14 + i * 9, -8)
        T(pn, 'P%d' % (i + 1), 5, 'MTY-KOLLETOR', 'MC')
    for name, (z, r) in roomtags.items():
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        zl = ('Z%02d' % z) if kat == 'Z' else ('%s%02d' % (kat, z))
        tot = sum(d['W'] for d in res if d['room'] == name)
        HEXTAG((cx, cy + 20), 'MTY-ISIKAYBIMAHAL', zl, '24°C' if 'BANYO' in name else '20°C', 10)
        T((cx, cy - 6), 'Kcal/h: %.0f' % (tot * 0.86), 8, 'MTY-ISIKAYBIMAHAL', 'C')
    # kombi -> kollektör
    tot = sum(d['W'] for d in res)
    kb, kbd = t['kombi']
    k1 = loc2base(kb, kbd, -8, 34); k2 = loc2base(kb, kbd, 8, 34)
    c1 = loc2base(ko, kd, -w / 2 - 6, 5); c2 = loc2base(ko, kd, -w / 2 - 6, 10)
    if tip == 'A':
        g = [k1, (k1[0] + 0, k1[1]), (k1[0] + 12, k1[1]), (k1[0] + 12, c1[1] + 0), c1]
        g = [loc2base(kb, kbd, -8, 32), (kb[0] + 50, kb[1] + 8), (kb[0] + 50, c1[1] + 14), (c1[0] + 5, c1[1] + 14), (c1[0] + 5, c1[1] + 6)]
        dn = [loc2base(kb, kbd, 8, 32), (kb[0] + 42, kb[1] - 8), (kb[0] + 42, c2[1] + 22), (c2[0] + 10, c2[1] + 22), (c2[0] + 10, c2[1] + 6)]
    else:
        sgn = 1 if kb[1] < ko[1] else -1
        g = [loc2base(kb, kbd, -8, 32), (kb[0] - 45, kb[1] - 8 * sgn), (kb[0] - 45, ko[1] - 30 * sgn), (c1[0] - 6, ko[1] - 30 * sgn), (c1[0] - 6, c1[1])]
        dn = [loc2base(kb, kbd, 8, 32), (kb[0] - 53, kb[1] + 8 * sgn), (kb[0] - 53, ko[1] - 22 * sgn), (c2[0] - 14, ko[1] - 22 * sgn), (c2[0] - 14, c2[1])]
    PL(g, 'MTY-ISITMA-GIDIS-BORU'); PL(dn, 'MTY-ISITMA-DONUS-BORU')
    lab_on(g, '%.1fW-DN20' % tot, 'STM-ISITMA-CAP', minlen=30)
    T((kb[0] + (80 if kbd == 'E' else -95), kb[1] - 30), 'DUVARA ASILABİLEN HERMETİK KOMBİ', 7, CD, 'C')
    T((kb[0] + (80 if kbd == 'E' else -95), kb[1] - 40), 'KAPASİTE : 24 kw', 7, CD, 'C')
    return res, tot, zone
