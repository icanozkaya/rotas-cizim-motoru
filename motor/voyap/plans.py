# -*- coding: utf-8 -*-
"""Kat planları: sprinkler boruları + çaplar, kolonlar, kat kontrol istasyonu, yangın dolapları, pompa dairesi + depo (bodrum)."""
import math, pickle, sys
import numpy as np
from shapely.geometry import LineString, Point, box as sbox
from lib import *
sys.path.insert(0, '/home/claude/nb/p2')
from route import make_grid, K1L, K2L, SRC0, cap
from geo import OFF, KATAD, PAN, Y0, Y1
VY = '/tmp/claude-0/vy/'
GM = pickle.load(open(VY + 'geo.pkl', 'rb'))
HS = pickle.load(open(VY + 'heads.pkl', 'rb'))
RT = pickle.load(open(VY + 'routes.pkl', 'rb'))

YK1L = (K1L[0], K1L[1] - 25.0)           # dolap + itfaiye kolonu (3"), SP-1 yanında köşede
DEPO = (248235.0, -451720.0, 248640.0, -450860.0)
PLACED = []                              # yazı kutuları (çakışma önleme)
ALL_LINES = {i: [] for i in range(4)}    # kolon kontrolü için tüm borular


def W(i, p):
    return (p[0] + OFF[i][0], p[1] + OFF[i][1])


def free(bx):
    g = sbox(*bx)
    return not any(g.intersects(q) for q in PLACED)


def label_run(pts, txt, h=9.0, lay=CAPL, ust=None):
    """borunun en uzun parçasına, boruya paralel ve 7 cm yanına; çakışmada kaydır"""
    segs = sorted(zip(pts[:-1], pts[1:]), key=lambda s: -math.dist(*s))
    for a, b in segs[:3]:
        Ls = math.dist(a, b)
        if Ls < len(txt) * h * 0.55 + 20: continue
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if ang > 90.01 or ang <= -90: ang += 180; a, b = b, a
        ang = (ang + 180) % 360 - 180
        ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        nx_, ny_ = -uy, ux
        tw = len(txt) * h * 0.5
        for f in (0.5, 0.3, 0.7, 0.15, 0.85):
            for side in (1, -1):
                cx = a[0] + (b[0] - a[0]) * f + nx_ * (7 + h * 0.5) * side
                cy = a[1] + (b[1] - a[1]) * f + ny_ * (7 + h * 0.5) * side
                hk = h * (1.9 if ust else 1.0)
                hw = abs(ux) * tw / 2 + abs(nx_) * hk / 2 + 2
                hh = abs(uy) * tw / 2 + abs(ny_) * hk / 2 + 2
                bx = (cx - hw, cy - hh, cx + hw, cy + hh)
                if free(bx):
                    PLACED.append(sbox(*bx))
                    T(cx, cy, txt, h, lay, TA.MIDDLE_CENTER, ang, mask=True)
                    if ust:
                        T(cx + nx_ * h * 0.95 * side, cy + ny_ * h * 0.95 * side, ust, h * 0.6, lay, TA.MIDDLE_CENTER, ang, mask=True)
                    return True
    return False


def runs_of(ts):
    """ağacı aynı çaplı zincirlere ayır"""
    Tr = ts['T']; E = {(e['a'], e['b']): e for e in ts['edges']}
    hn = set(ts['hn'])
    out = []
    starts = [(ts['root'], c) for c in Tr.successors(ts['root'])]
    seen = set()
    while starts:
        a, b = starts.pop()
        if (a, b) in seen: continue
        e = E[(a, b)]; pts = [a, b]; seen.add((a, b))
        cur = b
        while True:
            ch = list(Tr.successors(cur))
            if len(ch) == 1 and E[(cur, ch[0])]['cap'] == e['cap']:
                seen.add((cur, ch[0])); pts.append(ch[0]); cur = ch[0]
            else:
                for c in ch: starts.append((cur, c))
                break
        out.append(dict(pts=pts, cap=e['cap'], dn=e['dn'], n=e['n']))
    return out


def snap_dolap(i, want, maxd=90):
    """istenen noktaya en yakın duvar parçasına dolap (arka yüz duvarda, ön yüz isteğe bakar)"""
    G = GM[i]; p = Point(W(i, want))
    best = None
    for a, b in G['walls']:
        if math.dist(a, b) < 90: continue
        s = LineString([a, b]); d = s.distance(p)
        if d < maxd and (best is None or d < best[0]): best = (d, a, b, s)
    assert best, ('dolap duvarı yok', i, want)
    d, a, b, s = best
    q = s.interpolate(s.project(p))
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    nx_, ny_ = -uy, ux
    if (p.x - q.x) * nx_ + (p.y - q.y) * ny_ < 0: ang += 180; nx_, ny_ = -nx_, -ny_
    return (q.x, q.y), ang, (q.x + nx_ * 12.5, q.y + ny_ * 12.5)


def _hits_pipe(i, bx, own=None):
    g = sbox(*bx)
    for q in ALL_LINES[i]:
        if q is own: continue
        if LineString(q).intersects(g): return True
    return False


def label_short(i, pts, txt, h=6.5, lay=CAPL, ust=None):
    """kısa boru: yazı borunun yanına (boruya değmeden), gerekirse kısa kılavuz çizgisiyle"""
    L_ = [math.dist(a, b) for a, b in zip(pts[:-1], pts[1:])]
    k = max(range(len(L_)), key=lambda j: L_[j])
    a, b = pts[k], pts[k + 1]
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    horiz = abs(b[1] - a[1]) < abs(b[0] - a[0])
    tw = len(txt) * h * 0.55 + 2; hk = h * (2.0 if ust else 1.1)
    for r in (9, 14, 20, 28, 38, 50):
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            cx, cy = m[0] + dx * (r + tw / 2 if dx else 0), m[1] + dy * (r + hk / 2 if dy else 0)
            bx = (cx - tw / 2, cy - hk / 2, cx + tw / 2, cy + hk / 2)
            if free(bx) and not _hits_pipe(i, bx):
                PLACED.append(sbox(*bx))
                T(cx, cy - (h * 0.45 if ust else 0), txt, h, lay, TA.MIDDLE_CENTER, 0, mask=True)
                if ust:
                    T(cx, cy + h * 0.6, ust, h * 0.6, lay, TA.MIDDLE_CENTER, 0, mask=True)
                if r > 14:   # kılavuz
                    ex = min(max(m[0], bx[0]), bx[2]); ey = min(max(m[1], bx[1]), bx[3])
                    L(m, (ex, ey), lay)
                return True
    T(m[0] + 6, m[1] + 6, txt, h * 0.8, lay, TA.BOTTOM_LEFT, 0, mask=True)
    return False


def draw_tree(i):
    ts = RT[i]['ts']
    R_ = runs_of(ts)
    for r in R_:
        PL(r['pts'], BORU, WD[r['cap']])
        ALL_LINES[i].append(r['pts'])
    # her boruda çap: önce büyük çaplar (uzun parçalara), sonra kalan tüm kısa parçalar
    R_.sort(key=lambda r: -r['dn'])
    for r in R_:
        h = 9.0 if r['dn'] >= 40 else 7.0
        if not label_run(r['pts'], r['cap'], h=h, ust=str(r['n'])):
            label_short(i, r['pts'], r['cap'], h=6.5, ust=str(r['n']))


def heads(i):
    for k, h in enumerate(HS[i]):
        PLACED.append(sbox(h['p'][0] - 10, h['p'][1] - 10, h['p'][0] + 10, h['p'][1] + 10))
        HEAD(h['p'], h['t'])


def kolon(i, p, lab, sub, up=True, down=False, bo=(-34.0, 2.0)):
    INS("Y-KOLON", p, lay=KOL, mask=10)
    bx = (p[0] + bo[0], p[1] + bo[1])                # Aselsan kolon numarası: çift daire içinde
    MASKC(bx, 15); C(bx, 14, KOL); C(bx, 12, KOL)
    T(bx[0], bx[1], lab, 6.5, KOL, TA.MIDDLE_CENTER)
    d = math.dist(bx, p); u = ((p[0] - bx[0]) / d, (p[1] - bx[1]) / d)
    L((bx[0] + u[0] * 14, bx[1] + u[1] * 14), (p[0] - u[0] * 9, p[1] - u[1] * 9), KOL)
    sx = bx[0] + (-16 if bo[0] < 0 else 16); sy = bx[1] - 16
    T(sx, sy, sub, 6, KOL, TA.TOP_RIGHT if bo[0] < 0 else TA.TOP_LEFT, mask=True)
    PLACED.append(sbox(min(bx[0], p[0]) - 60, min(bx[1], p[1]) - 25, max(bx[0], p[0]) + 60, max(bx[1], p[1]) + 18))


def dolap(i, want, yk, no):
    back, ang, front = snap_dolap(i, want)
    a = math.radians(ang)
    INS("ASL-YD-PLAN", (back[0] + math.cos(a + math.pi / 2) * 33, back[1] + math.sin(a + math.pi / 2) * 33), ang, 0.9, lay=DOL, mask=None)
    # bağlantı: kolondan dolap arka-orta noktasına (önce dik, sonra yatay)
    c = (back[0] + math.cos(a + math.pi / 2) * 6, back[1] + math.sin(a + math.pi / 2) * 6)
    if abs(math.cos(a)) > 0.7:     # dolap yatay duvarda
        pts = [yk, (c[0], yk[1]), c] if abs(yk[1] - c[1]) > 1 else [yk, c]
    else:
        pts = [yk, (yk[0], c[1]), c] if abs(yk[0] - c[0]) > 1 else [yk, c]
    PL(pts, DOLB, 2.0); ALL_LINES[i].append(pts)
    tx = front[0] + math.cos(a + math.pi / 2) * 30; ty = front[1] + math.sin(a + math.pi / 2) * 30
    tx = front[0] + math.cos(a + math.pi / 2) * 45; ty = front[1] + math.sin(a + math.pi / 2) * 45
    for dy in (0, 40, -40, 80, -80):
        bx = (tx - 45, ty + dy - 16, tx + 45, ty + dy + 18)
        if free(bx) and not any(LineString(q).intersects(sbox(*bx)) for q in ALL_LINES[i]):
            ty += dy; break
    PLACED.append(sbox(tx - 45, ty - 16, tx + 45, ty + 18))
    T(tx, ty + 4, f"YD-{no}", 10, DOL, TA.BOTTOM_CENTER, mask=True)
    T(tx, ty - 4, "TS EN 671-1 Ø25/30m", 6.5, DOL, TA.TOP_CENTER, mask=True)
    return pts


def kat_kontrol(i, src):
    """kat girişi: izlenebilir kelebek vana + akış anahtarı + test/drenaj (omurganın ilk parçası üzerinde)"""
    l0 = RT[i]['lines'][0]
    a, b = l0[0], l0[1]
    if math.dist(a, b) < 60: a, b = l0[1], l0[2]
    ux, uy = (b[0] - a[0]) / math.dist(a, b), (b[1] - a[1]) / math.dist(a, b)
    ang = math.degrees(math.atan2(uy, ux))
    p1 = (a[0] + ux * 22, a[1] + uy * 22); p2 = (a[0] + ux * 42, a[1] + uy * 42); p3 = (a[0] + ux * 58, a[1] + uy * 58)
    INS("Y-KELEBEK", p1, ang, 0.8, mask=8)
    INS("Y-AKIS", p2, ang, 0.9, mask=7)
    # test-drenaj kolu
    nx_, ny_ = -uy, ux
    nx_, ny_ = -nx_, -ny_            # test kolu koridor tarafına
    q = (p3[0] + nx_ * 22, p3[1] + ny_ * 22)
    PL([p3, q], BORU, 0)
    INS("Y-TEST", q, ang, 0.8)
    T(q[0] + nx_ * 14, q[1] + ny_ * 14, "TEST/DRENAJ DN32", 6, VAN, TA.MIDDLE_CENTER, ang, mask=True)
    PLACED.append(sbox(min(a[0], p3[0]) - 25, min(a[1], p3[1]) - 25, max(a[0], p3[0]) + 25, max(a[1], p3[1]) + 25))
    return p1


def router_line(i, a, b, sysn='YD'):
    g = make_grid(GM[i])
    for l in ALL_LINES[i]: g.add_line(l, 'S')
    pts = g.route(a, b, sysn=sysn, turn=60.0, max_exp=3_000_000, wsys={'S': 1.0})
    assert pts, ('dolap hattı', i, a, b)
    return pts


# ================================================================== KATLAR
def floor(i):
    heads(i)
    draw_tree(i)
    k1 = W(i, K1L); yk1 = W(i, YK1L); yk2 = W(i, K2L)
    # kolonlar
    if i == 0:
        kolon(i, k1, "SP-1", 'DN150 yukarı (Z-1-2)', bo=(75.0, -38.0))
    else:
        kolon(i, k1, "SP-1", 'DN150' + (' yukarı' if i < 3 else ''), bo=(75.0, -38.0))
    kolon(i, yk1, "Y-1", 'DN80' + (' yukarı' if i < 3 else ''), bo=(75.0, -55.0))
    kolon(i, yk2, "Y-2", 'DN65' + (' yukarı' if i < 3 else ''), bo=(34.0, 30.0))
    # dolaplar
    if i == 0:
        d1 = dolap(i, (248470.0, -452200.0), yk1, "B1")
        d2 = dolap(i, (248420.0, -456125.0), yk2, "B2")
    elif i == 1:
        d1 = dolap(i, (248215.0, -452250.0), yk1, "Z1")
        d2 = dolap(i, (248665.0, -456300.0), yk2, "Z2")
    else:
        kk = {2: '1', 3: '2'}[i]
        d1 = dolap(i, (248380.0, -452060.0), yk1, kk + "1")
        d2 = dolap(i, (248610.0, -456300.0), yk2, kk + "2")
    for d in (d1, d2):
        label_run(d, 'DN50', 8, DOL)
    if i > 0:
        kat_kontrol(i, RT[i]['src'])
        T(k1[0] + 120, k1[1] - 50, "KAT KONTROL İST.", 7, VAN, TA.BOTTOM_LEFT, mask=True)
    if i == 1:
        itfaiye(i, yk1)
    if i == 0:
        pompa_dairesi()


def itfaiye(i, yk1):
    """zemin: itfaiye bağlantısı sol cephe (merdiven hizası) -> YK1"""
    p = W(i, (248150.0, -452250.0))
    INS("Y-ITFAIYE", p, 0, 1.2, lay=ITF)
    pts = [(p[0] + 17, p[1]), (yk1[0], p[1]), (yk1[0], yk1[1] + 9)]
    PL(pts, ITF, 3.0); ALL_LINES[i].append(pts)
    CEK((p[0] + 60, p[1]), 0, 1.0, mask=8)
    T(p[0] - 30, p[1] + 26, "İTFAİYE BAĞLANTISI", 9, ITF, TA.BOTTOM_LEFT, mask=True)
    T(p[0] - 30, p[1] + 14, "2x2 1/2\" STORZ + ÇEK VALF, h=+0,80", 6.5, ITF, TA.BOTTOM_LEFT, mask=True)
    label_run(pts, 'DN80', 8, ITF)


def pompa_dairesi():
    """bodrum tesisat alanı: 80 m³ depo (kuzey) + pompa grubu + kollektör + AV1/AV2 + dolap çıkışı"""
    x0, y0, x1, y1 = DEPO
    # depo güney perdesi (yeni, 25 cm betonarme)
    HATCH_RECT(x0, y0 - 25, x1, y0, DEP)
    PL([(x0 + 5, y0 + 5), (x1 - 5, y0 + 5), (x1 - 5, y1 - 5), (x0 + 5, y1 - 5)], DEP, 0, closed=True)
    cx = (x0 + x1) / 2
    T(cx, -451250, "YANGIN SUYU DEPOSU", 14, DEP, TA.MIDDLE_CENTER, 90)
    T(cx + 26, -451250, "V = 80 m³ NET (4,00 x 8,50 x 2,35 m)", 9, DEP, TA.MIDDLE_CENTER, 90)
    T(cx + 44, -451250, "BETONARME, İÇİ EPOKSİ KAPLI", 7, DEP, TA.MIDDLE_CENTER, 90)
    T(cx - 26, -451250, "BU ALANDAKİ 3 ADET MEVCUT SPRİNKLER SİLİNECEKTİR", 7, "MTY-YANGIN-NOT", TA.MIDDLE_CENTER, 90)
    # menhol, havalık, taşma, dolum, seviye
    PL([(x0 + 30, -450930), (x0 + 90, -450930), (x0 + 90, -450990), (x0 + 30, -450990)], DEP, 0, True)
    T(x0 + 60, -450925, "MENHOL 60x60", 6, DEP, TA.BOTTOM_CENTER)
    INS("Y-SAMANDIRA", (x1 - 60, -450950), 180, 1.0, lay=DEP)
    T(x1 - 60, -450925, "ŞEBEKE DOLUM 1\" (şamandıralı)", 6, DEP, TA.BOTTOM_CENTER)
    T(x1 - 80, -451000, "TAŞMA DN80 + HAVALIK DN50", 6, DEP, TA.BOTTOM_CENTER)
    T(x0 + 60, -451010, "SEVİYE GÖSTERGESİ", 6, DEP, TA.BOTTOM_CENTER)
    T(x0 + 60, -451630, "BOŞALTMA 2\" (pompa çukuruna)", 6, DEP, TA.BOTTOM_CENTER)
    # ---- pompalar (emiş depodan güneye, basma kollektöre)
    YC = -452050.0
    pumps = [(248300.0, "E", "ELK. ANA POMPA", "Q=70 m³/h H=60 mSS 22 kW", 'DN150', 'DN100'),
             (248420.0, "D", "DİZEL YEDEK POMPA", "Q=70 m³/h H=60 mSS 30 kW", 'DN150', 'DN100'),
             (248545.0, "J", "JOKEY POMPA", "Q=3 m³/h H=70 mSS 1,5 kW", 'DN40', 'DN25')]
    for x, tag, ad, ozl, de, db in pumps:
        big = tag != "J"; s = 1.0 if big else 0.6
        ys = y0 - 25                          # depo perdesi alt yüzü
        PL([(x, ys + 25 - 20), (x, -451860 + (18 if big else 11))], POM, 3.0 if big else 1.5)
        INS("Y-VORTEX", (x, ys + 25 - 20), 0, s, lay=POM)
        INS("Y-OSY", (x, -451760), 90, s * 0.9, mask=9)
        INS("Y-RED", (x, -451820), -90, s, mask=8)
        INS("Y-POMPA", (x, -451860), -90, s, lay=POM, mask=None)
        INS("Y-MOTOR", (x + (34 if big else 22), -451860), 0, s * (1 if big else 0.6), lay=POM)
        T(x, -451860, tag, 9 if big else 6, POM, TA.MIDDLE_CENTER)
        PL([(x, -451860 - (18 if big else 11)), (x, YC)], POM, 3.0 if big else 1.5)
        CEK((x, -451940), -90, s, mask=8)
        INS("Y-OSY", (x, -451985), 90, s * 0.9, mask=9)
        INS("Y-MANO", (x, -451905), 0, 0.8)
        T(x - 24, -451760, f"emiş {de}", 6, POM, TA.MIDDLE_CENTER, 90)
        T(x - 24, -451985, f"basma {db}", 6, POM, TA.MIDDLE_CENTER, 90)
    # pompa etiketleri (pompa sırasının güneyinde, kollektör altında)
    yy = -452095
    for x, tag, ad, ozl, de, db in pumps:
        pass
    # emniyet vanası (dizel) + sirkülasyon
    L((248420, -451915), (248400, -451915), POM); INS("Y-EMNIYET", (248400, -451915), 90, 0.8)
    # kollektör
    PL([(K1L[0], YC), (248880, YC)], POM, 5.0)
    T(248650, YC + 8, 'KOLLEKTÖR DN150', 7, POM, TA.BOTTOM_CENTER, mask=True)
    # jokey membranlı tank + basınç anahtarları
    INS("Y-MTANK", (248620, -451960), 0, 0.9, lay=POM)
    PL([(248620, -451978), (248620, YC)], POM, 1.0)
    for k, x in enumerate((248700, 248740, 248780)):
        INS("Y-PS", (x, YC), 0, 0.8)
    T(248740, YC + 22, "PS-E / PS-D / PS-J", 6, POM, TA.BOTTOM_CENTER)
    # test hattı + debimetre -> depoya dönüş
    tl = [(248820, YC), (248820, -451760), (248600, -451760), (248600, y0 - 25)]
    PL(tl, POM, 2.5)
    INS("Y-DEBI", (248820, -451900), 0, 1.0, lay=POM, mask=9)
    INS("Y-OSY", (248820, -451960), 90, 0.8, mask=8)
    T(248836, -451900, "TEST HATTI DN80 + DEBİMETRE (depoya dönüş)", 6, POM, TA.MIDDLE_LEFT, 90)
    # AV1: bodrum sprinkler
    PL([(248880, YC), (248880, SRC0[1]), SRC0], BORU, 5.0)
    INS("Y-ALARM", (248880, -452005), 90, 0.9, mask=12)
    T(248895, -452030, "AV1 DN150 - BODRUM", 7, VAN, TA.BOTTOM_LEFT, 90, mask=True)
    # AV2: üst katlar -> SK
    k1 = K1L
    PL([(k1[0], YC), (k1[0], k1[1] + 9)], BORU, 5.0)
    INS("Y-ALARM", (k1[0] + 27, YC), 180, 0.7, mask=10)
    T(k1[0] - 6, YC + 30, "AV2 DN150 - Z/1/2 KAT (SP-1)", 6, VAN, TA.BOTTOM_LEFT, 0, mask=True)
    # dolap çıkışı -> YK1 ve YK2
    xd = 248520.0
    yk1 = YK1L
    dl = [(xd, YC), (xd, yk1[1]), (yk1[0] + 9, yk1[1])]
    PL(dl, DOLB, 3.0); ALL_LINES[0].append(dl)
    INS("Y-OSY", (xd, -452100), 90, 0.8, mask=8)
    T(xd + 12, -452100, "DOLAP HATTI DN80", 7, DOL, TA.MIDDLE_LEFT, 0, mask=True)
    # YK2 besleme (bodrum tavanından, A*)
    r = router_line(0, (xd, yk1[1]), K2L)
    PL(r, DOLB, 2.5); ALL_LINES[0].append(r)
    label_run(r, 'DN65', 8, DOL)
    # panolar (doğu duvarı) + yakıt tankı + egzoz
    for k, (yy, t) in enumerate(((-451790, "ELK. POMPA PANOSU"), (-451850, "DİZEL POMPA PANOSU"), (-451910, "JOKEY PANOSU"))):
        INS("Y-PANO", (248915, yy), 90, 0.9, lay=POM)
        T(248898, yy, t, 5, POM, TA.MIDDLE_RIGHT)
    INS("Y-YAKIT", (248484, -451905), 90, 0.7, lay=POM)
    T(248484, -451935, "YAKIT 100 L", 5, POM, TA.TOP_CENTER)
    eg = [(248420 + 34, -451845), (248420 + 34, -451830)]
    T(248250, -452140, "DİZEL EGZOZU: yalıtımlı, susturuculu, dış atmosfere", 6, POM, TA.BOTTOM_LEFT)
    T(248250, -452155, "POMPA DAİRESİ min. +10°C, yer süzgeci, menfez", 6, POM, TA.BOTTOM_LEFT)
    # pompa adları (kollektör altında)
    for x, tag, ad, ozl, de, db in pumps:
        T(x, -452070, ad, 5.5, POM, TA.TOP_CENTER)
        T(x, -452080, ozl, 4.5, POM, TA.TOP_CENTER)
    PLACED.append(sbox(248230, -452175, 248950, -451700))


def bodrum_mimari():
    """güncel bodrum mimarisi (kullanıcının yangın paftasındaki eski bodrumun yerine) ayrı katmanda"""
    M = pickle.load(open(VY + 'mimT.pkl', 'rb'))
    for r in M:
        if r[0] == 'L':
            a, b = r[2][0], r[2][1]
            if 247900 < a[0] < 250300: L(a, b, "MIM-BODRUM-GUNCEL")
        elif r[0] == 'P':
            q = r[2]
            if 247900 < q[0][0] < 250300: PL(q, "MIM-BODRUM-GUNCEL")
        elif r[0] == 'C':
            c = r[2]
            if 247900 < c[0] < 250300: C((c[0], c[1]), c[2], "MIM-BODRUM-GUNCEL")
        elif r[0] == 'T':
            (x, y), s, h = r[2][0], r[2][1], r[2][2]
            if 247900 < x < 250300 and 'lift' not in s and 'BODRUM' not in s and 'KOLON' not in s:
                s2 = s.split(';')[-1].strip('}') if ';' in s else s
                T(x, y, s2, min(h, 30), "MIM-BODRUM-GUNCEL")
            elif 247900 < x < 250300 and 'lift' in s:
                T(x, y, "LİFT", 12, "MIM-BODRUM-GUNCEL")


def build_plans():
    for i in range(4):
        floor(i)
    return ALL_LINES


def kopruler():
    """dolap/itfaiye hattı sprinkler borusunu kestiği yerde köprü (pompa dairesinde kotlar farklı: köprü yok)"""
    import ezdxf
    n = 0
    S = []
    for i in range(4):
        sp = [LineString(l) for l in ALL_LINES[i]]
    E = list(msp.query('LWPOLYLINE'))
    spr = [e for e in E if e.dxf.layer == BORU]
    dol = [e for e in E if e.dxf.layer in (DOLB, ITF)]
    for d in dol:
        dp = [q[:2] for q in d.get_points()]
        for a, b in zip(dp[:-1], dp[1:]):
            sd = LineString([a, b])
            for e in spr:
                ep = [q[:2] for q in e.get_points()]
                for c, f in zip(ep[:-1], ep[1:]):
                    se = LineString([c, f])
                    if sd.crosses(se):
                        x = sd.intersection(se)
                        if x.geom_type != 'Point': continue
                        if 248230 < x.x < 248950 and -452180 < x.y < -451700: continue
                        p = (x.x, x.y)
                        u = ((b[0]-a[0])/sd.length, (b[1]-a[1])/sd.length); v = ((f[0]-c[0])/se.length, (f[1]-c[1])/se.length)
                        MASKC(p, 8)
                        PL([(p[0]-10*v[0], p[1]-10*v[1]), (p[0]+10*v[0], p[1]+10*v[1])], BORU, e.dxf.const_width)
                        nx_, ny_ = -u[1], u[0]
                        arc = [(p[0] + 8*math.cos(t)*u[0] + 8*math.sin(t)*nx_, p[1] + 8*math.cos(t)*u[1] + 8*math.sin(t)*ny_) for t in [math.pi*k/12 for k in range(12, -1, -1)]]
                        PL(arc, d.dxf.layer, d.dxf.const_width)
                        n += 1
    print('köprü', n)
