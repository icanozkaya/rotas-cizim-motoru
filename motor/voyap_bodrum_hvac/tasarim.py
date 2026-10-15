# -*- coding: utf-8 -*-
"""VOYAP ASEM - Bodrum kat: sığınak havalandırması + otopark taze hava / duman tahliye kanal tasarımı.
Tüm kanallar otopark girişi (güney, araç asansörü) tarafındaki iki şafttan dışarı çıkar.
Birim: cm (mimari ile aynı koordinat). Çıktı: DXF R2018."""
import math, pickle, sys
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

PKL, OUT = sys.argv[1], sys.argv[2]
F = pickle.load(open(PKL, 'rb'))
fmt = lambda v, n=0: f'{v:,.{n}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

# ---------------------------------------------------------------- HESAPLAR
SIG_A = 109.44; SIG_H = 3.00            # net alan (polygon ölçümü), net yükseklik
OTO_A = 769.71; OTO_H = 3.00            # otopark net alanı (kolon, merdiven, asansör, tesisat alanı hariç)
up = lambda q, s: int(math.ceil(q / s) * s)
OLCU = [(30, 20), (40, 20), (40, 25), (40, 30), (50, 30), (50, 40), (60, 40), (60, 50), (80, 50), (100, 50)]
def gecis(q, v=2.5):
    a = q / 3600 / v * 1e4
    return next(f'{b}x{h} cm' for b, h in OLCU if b * h >= a)
S = dict(V=SIG_A * SIG_H)
S['qth'] = S['V'] * 4; S['qsec'] = up(S['qth'], 100); S['qeg'] = round(S['qsec'] * 0.9)
S['qdt'] = S['V'] * 10; S['qdts'] = up(S['qdt'], 500)
S['g_th'], S['g_eg'], S['g_dt'] = gecis(S['qsec']), gecis(S['qeg']), gecis(S['qdts'])
O = dict(V=OTO_A * OTO_H)
O['qdt'] = O['V'] * 10; O['qdts'] = up(O['qdt'], 500); O['qth'] = round(O['qdts'] * 0.9)
O['qn'] = O['V'] * 6
NG = 10                                   # otopark menfez adedi (her hat)
qE1, qT1 = O['qdts'] / NG, O['qth'] / NG

# ---------------------------------------------------------------- KANAL BOYUT
def boyut(q, vmax, wmax, hs=(200, 250, 300, 350, 400, 450, 500, 600, 700, 750)):
    """dikdörtgen kanal (mm): plan genişliği wmax (cm) sınırı, v<=vmax, en küçük çevre"""
    best = None
    for h in hs:
        for w in range(200, int(wmax * 10) + 1, 50):
            if w < h: continue
            v = q / 3600 / (w / 1000 * h / 1000)
            if v > vmax: continue
            c = w + h
            if best is None or c < best[0] or (c == best[0] and w < best[1]): best = (c, w, h, v)
    assert best, (q, vmax, wmax)
    return best[1], best[2], best[3]
def R_pam(q, w, h):                       # Darcy + Swamee-Jain, galvaniz e=0,15 mm
    A = w / 1000 * h / 1000; v = q / 3600 / A; Dh = 2 * A / ((w + h) / 1000)
    Re = v * Dh / 1.5e-5; f = 0.25 / math.log10(0.00015 / (3.7 * Dh) + 5.74 / Re ** 0.9) ** 2
    return f / Dh * 1.2 * v * v / 2, v

# ---------------------------------------------------------------- DXF
doc = ezdxf.new('R2018', setup=True); doc.header['$INSUNITS'] = 5
msp = doc.modelspace()
doc.styles.add('ROTAS', font='arial.ttf')
LAY = {'ROTAS-HVAC-OTP-EGZOZ': 1, 'ROTAS-HVAC-OTP-TAZE': 5, 'ROTAS-HVAC-SIG-TAZE': 4, 'ROTAS-HVAC-SIG-EGZOZ': 6,
       'ROTAS-HVAC-SIG-DUMAN': 30, 'ROTAS-HVAC-MENFEZ': 3, 'ROTAS-HVAC-CIHAZ': 2, 'ROTAS-HVAC-SAFT': 7,
       'ROTAS-HVAC-YAZI': 7, 'ROTAS-HVAC-OK': 1, 'ROTAS-HESAP-CIZGI': 8, 'ROTAS-HESAP-YAZI': 7, 'ROTAS-HESAP-CERCEVE': 1}
for n, c in LAY.items(): doc.layers.add(n, color=c)
# mimari altlık (kullanıcının çiziminden; kolonlar dahil, aynı koordinat)
arch_layers = {}
for L, a, b in F['segs']:
    if a[0] > 568700 or b[0] > 568700 or a[1] > 4523700: continue
    if L not in arch_layers:
        arch_layers[L] = 1
        if L not in doc.layers: doc.layers.add(L, color=8 if L != 'ARC_Duvar' else 7)
    msp.add_line(a, b, dxfattribs={'layer': L})
for L, x, y, s, h in F['texts']:
    if x > 568700 or y > 4523700: continue
    if L not in doc.layers: doc.layers.add(L, color=8)
    t = msp.add_mtext(s, dxfattribs={'layer': L, 'char_height': h, 'style': 'ROTAS'}); t.set_location((x, y))

def T(x, y, s, h, lay='ROTAS-HVAC-YAZI', al=TA.MIDDLE_CENTER, rot=0.0, wf=0.85):
    t = msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': wf}); t.set_placement((x, y), align=al); return t
def PL(pts, lay, close=False, w=0.0):
    return msp.add_lwpolyline(pts, close=close, dxfattribs={'layer': lay, 'const_width': w})
def draw_poly(g, lay):
    gs = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    for p in gs:
        PL(list(p.exterior.coords)[:-1], lay, True)
        for r in p.interiors: PL(list(r.coords)[:-1], lay, True)

# ---------------------------------------------------------------- YERLEŞİM
# alt bölge orta kolon aksı (betonarme kolon yüzleri, ölçülen): xw(y) batı yüzü, xe(y) doğu yüzü
xw = lambda y: 567237 + 0.02855 * (y - 4516900)
xe = lambda y: xw(y) + 82
Y_J0, Y_J1 = 4520550, 4520690           # alt (eğik aks) -> üst (iki kolon sırası) geçiş bandı
Y_TOP = 4522490                          # sığınak güney perdesi alt yüzü
GAP = 15
# kanal hatları: ad -> (katman, bileşenler)
NET = {}
LBL = []                                  # (x, y, rot, yazı, h)  kanal içi etiketler
MENF = []                                 # menfez: (tag, x, y, yön, uzunluk, ölçü, Q, katman)
def seg_poly(p, q, w1, w2=None):
    w2 = w1 if w2 is None else w2
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
    return Polygon([(p[0] + nx * w1 / 2, p[1] + ny * w1 / 2), (q[0] + nx * w2 / 2, q[1] + ny * w2 / 2),
                    (q[0] - nx * w2 / 2, q[1] - ny * w2 / 2), (p[0] - nx * w1 / 2, p[1] - ny * w1 / 2)])
def corner(p, w, h=None):
    h = w if h is None else h
    return box(p[0] - w / 2, p[1] - h / 2, p[0] + w / 2, p[1] + h / 2)

class Hat:
    def __init__(s, ad, lay, kisa): s.ad, s.lay, s.kisa, s.parts, s.tbl = ad, lay, kisa, [], []
    def add(s, g): s.parts.append(g)
    def run(s, pts, ws, lbl=None, red=True):
        """pts: köşe noktaları, ws: her parçanın genişliği (cm); aynı doğrultuda genişlik değişiminde 30 cm redüksiyon"""
        for i in range(1, len(pts) - 1):      # köşe birleşimi (gönye)
            p0, v, p1 = pts[i - 1], pts[i], pts[i + 1]
            d0 = math.hypot(v[0] - p0[0], v[1] - p0[1]); d1 = math.hypot(p1[0] - v[0], p1[1] - v[1])
            a0 = (v[0] - (v[0] - p0[0]) / d0 * 2, v[1] - (v[1] - p0[1]) / d0 * 2); a1 = (v[0] + (p1[0] - v[0]) / d1 * 2, v[1] + (p1[1] - v[1]) / d1 * 2)
            s.add(LineString([a0, v, a1]).buffer(min(ws[i - 1], ws[i]) / 2, cap_style=2, join_style=2, mitre_limit=3))
        for i in range(len(pts) - 1):
            p, q, w = pts[i], pts[i + 1], ws[i]
            if red and i > 0 and ws[i - 1] != w:
                dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy)
                m = (p[0] + dx / L * 30, p[1] + dy / L * 30)
                s.add(seg_poly(p, m, ws[i - 1], w)); s.add(seg_poly(m, q, w))
            else:
                s.add(seg_poly(p, q, w))
    def geom(s): return unary_union(s.parts).buffer(3, join_style=2).buffer(-3, join_style=2).simplify(0.5)

# ---- otopark egzoz (E) ve taze hava (B): menfez kotları (kuzeyden güneye)
YM = [4522330, 4521900, 4521350, 4520480, 4519985, 4519480, 4518960, 4518420, 4517880, 4517560]
# alt bölge hat eksenleri
def cx(lane, y):
    if y >= Y_J1: return UP[lane]
    return LO[lane](y)
# üst bölge (iki kolon sırası arası: batı kolon doğu yüzü 567192/tesisat perdesi 567174, doğu kolon batı yüzü 567611)
UP = {'B': 567255, 'A': 567310, 'D': 567435, 'S': 567510, 'E': 567582}
LO = {'A': lambda y: xw(y) - 20 - 20,
      'B': lambda y: xw(y) - 20 - 40 - GAP - 52.5,
      'D': lambda y: xe(y) + 15 + 20,
      'S': lambda y: xe(y) + 15 + 40 + GAP + 20,
      'E': lambda y: xe(y) + 15 + 40 + GAP + 40 + GAP + 45}
WMAX_UP = {'B': 50, 'E': 45}; WMAX_LO = {'B': 105, 'E': 90}

def lane_pts(lane, y_from, y_to):
    """kuzeyden güneye hat noktaları (geçiş bandında kısa eğik parça)"""
    pts = []
    for y in [y_from, Y_J1, Y_J0, y_to]:
        if y_to <= y <= y_from and (not pts or pts[-1][1] != y): pts.append((cx(lane, y if y != Y_J1 else Y_J1 + 0.01) if y != Y_J0 else LO[lane](y), y))
    return pts

# SE (egzoz) şaftı ve SW (taze hava) şaftı — otopark girişi (araç asansörü) tarafı
SAFT_E = (567322, 4516900, 567550, 4517045)
SAFT_T = (566620, 4517120, 566800, 4517280)

# ===== OTOPARK EGZOZ / DUMAN TAHLİYE (E)
E = Hat('OTOPARK EGZOZ / DUMAN TAHLİYE', 'ROTAS-HVAC-OTP-EGZOZ', 'E')
B = Hat('OTOPARK TAZE HAVA', 'ROTAS-HVAC-OTP-TAZE', 'T')
def ana_hat(H, lane, q1, vmax, y_end_s, tagp, menf_side):
    """menfezli ana hat: kuzey uçtan (ilk menfez) şafta kadar, her menfezden sonra büyür"""
    y0 = YM[0] + 60
    segs = []                                 # (y_kuzey, y_güney, Q)
    ys = [y0] + YM[1:] + [y_end_s]
    for k in range(len(YM)):
        segs.append((YM[k] if k else y0, YM[k + 1] if k + 1 < len(YM) else y_end_s, q1 * (k + 1)))
    out = []
    for (ya, yb, q) in segs:
        wmax = WMAX_UP[lane] if yb >= Y_J1 else WMAX_LO[lane]
        w, h, v = boyut(q, vmax, wmax)
        out.append((ya, yb, q, w, h, v))
    # çizim: parça parça (geçiş bandını keserek)
    cuts = sorted(set([o[0] for o in out] + [out[-1][1], Y_J1, Y_J0]), reverse=True)
    cuts = [c for c in cuts if out[-1][1] <= c <= out[0][0]]
    def wat(y):
        for ya, yb, q, w, h, v in out:
            if yb <= y <= ya: return w
        return out[-1][3]
    pos = lambda y: UP[lane] if y >= Y_J1 else LO[lane](y)
    pts = [(pos(c), c) for c in cuts]
    ws = [wat((cuts[i] + cuts[i + 1]) / 2) / 10 for i in range(len(cuts) - 1)]
    H.run(pts, ws)
    H.tbl = out
    # etiketler (kanal içinde, kanal doğrultusunda)
    for ya, yb, q, w, h, v in out:
        ym = (ya + yb) / 2 + (35 if ya - yb > 400 else 0)
        if ya - yb < 250: continue
        x = UP[lane] if ym >= Y_J1 else LO[lane](ym)
        LBL.append((x, ym, 90 + (math.degrees(math.atan(0.02855)) if ym < Y_J1 else 0), f'{w}x{h}  {fmt(q)} m³/h', 10))
    # menfezler
    for k, y in enumerate(YM):
        x = UP[lane] if y >= Y_J1 else LO[lane](y)
        w = wat(y - 1) / 10
        MENF.append((f'{tagp}{k + 1}', x + menf_side * w / 2, y, menf_side, H.lay))
    return out

oE = ana_hat(E, 'E', qE1, 10.0, SAFT_E[3], 'E', +1)
oB = ana_hat(B, 'B', qT1, 8.0, 4517417, 'T', -1)
# B güney ucu: batıya dönüp SW şaftına iner (dış hat; A içte kalır)
wB = oB[-1][3] / 10
pB = (LO['B'](4517417), 4517417)
B.add(corner(pB, wB, wB))
B.run([pB, (566688, 4517417), (566688, SAFT_T[3])], [wB, wB], red=False)
B.add(corner((566688, 4517417), wB, wB))
E_end = (LO['E'](SAFT_E[3]), SAFT_E[3])

# ===== SIĞINAK HATLARI (A taze, D duman, S egzoz) — güneyde şaftlara, kuzeyde sığınak perdesinden içeri
SQ = {'A': S['qsec'], 'D': S['qdts'], 'S': S['qeg']}
SW_ = {'A': (400, 200), 'D': (400, 300), 'S': (400, 200)}
A = Hat('SIĞINAK TAZE HAVA', 'ROTAS-HVAC-SIG-TAZE', 'SA'); D = Hat('SIĞINAK DUMAN TAHLİYE', 'ROTAS-HVAC-SIG-DUMAN', 'SD')
Sx = Hat('SIĞINAK EGZOZ', 'ROTAS-HVAC-SIG-EGZOZ', 'SE')
def sig_dis(H, lane, y_s):
    w = SW_[lane][0] / 10
    pts = [(UP[lane], Y_TOP + 40), (UP[lane], Y_J1), (LO[lane](Y_J0), Y_J0), (LO[lane](y_s), y_s)]
    H.run(pts, [w] * 3, red=False)
    for y in range(int(Y_J1) + 300, int(Y_TOP) - 600, 900):
        LBL.append((UP[lane], y + 300, 90, f'{SW_[lane][0]}x{SW_[lane][1]}  {fmt(SQ[lane])} m³/h', 8.5))
    for y in [4520250, 4519100, 4517950]:
        LBL.append((LO[lane](y), y, 90 + math.degrees(math.atan(0.02855)), f'{SW_[lane][0]}x{SW_[lane][1]}  {fmt(SQ[lane])} m³/h', 8.5))
sig_dis(D, 'D', SAFT_E[3]); sig_dis(Sx, 'S', SAFT_E[3])
sig_dis(A, 'A', 4517330)
pA = (LO['A'](4517330), 4517330)
A.add(corner(pA, 40, 40)); A.run([pA, (566765, 4517330), (566765, SAFT_T[3])], [40, 40], red=False)
A.add(corner((566765, 4517330), 40, 40))

# --- sığınak içi dağıtım (iç ölçü x 566781-568120, y 4522530-4523357)
YI_A, XA_W, YI_AN = 4522610, 566880, 4523230
A.run([(UP['A'], Y_TOP + 40), (UP['A'], YI_A), (XA_W, YI_A), (XA_W, YI_AN), (568040, YI_AN)], [40, 40, 40, 40], red=False)
for p in [(UP['A'], YI_A), (XA_W, YI_A), (XA_W, YI_AN)]: A.add(corner(p, 40))
YI_D = 4522780
D.run([(UP['D'], Y_TOP + 40), (UP['D'], YI_D)], [40], red=False); D.run([(567020, YI_D), (568040, YI_D)], [40], red=False)
D.add(corner((UP['D'], YI_D), 40))
YI_S = 4522650
Sx.run([(UP['S'], Y_TOP + 40), (UP['S'], YI_S), (568040, YI_S)], [40, 40], red=False); Sx.add(corner((UP['S'], YI_S), 40))
SMENF = [('SA1', 567200, YI_AN, -1, A.lay, 'y'), ('SA2', 567450, YI_AN, -1, A.lay, 'y'), ('SA3', 567780, YI_AN, -1, A.lay, 'y'),
         ('SA4', 568000, YI_AN, -1, A.lay, 'y'),
         ('SD1', 567110, YI_D, -1, D.lay, 'y'), ('SD2', 567280, YI_D, -1, D.lay, 'y'), ('SD3', 567880, YI_D, -1, D.lay, 'y'),
         ('SD4', 568010, YI_D, -1, D.lay, 'y'),
         ('SE1', 567760, YI_S, -1, Sx.lay, 'y'), ('SE2', 567900, YI_S, -1, Sx.lay, 'y'), ('SE3', 568030, YI_S, -1, Sx.lay, 'y')]

santral = (566930, 4522570, 567070, 4522650)
FANS = [('E', 4517330, 110), ('B', 4517720, 120)]
# ---------------------------------------------------------------- ÇİZİM: kanallar
NETS = [E, B, A, D, Sx]
G = {}
for H in NETS:
    g = H.geom()
    if H.kisa == 'E': g = g.difference(box(LO['E'](4517330) - oE[-1][3] / 20 - 3, 4517330 - 55, LO['E'](4517330) + oE[-1][3] / 20 + 3, 4517330 + 55))
    if H.kisa == 'T': g = g.difference(box(LO['B'](4517720) - oB[-1][3] / 20 - 3, 4517720 - 60, LO['B'](4517720) + oB[-1][3] / 20 + 3, 4517720 + 60))
    G[H.kisa] = g; draw_poly(g, H.lay)
# kanal içi etiketler
from shapely.strtree import STRtree
from shapely import affinity
ARCH = [LineString([a, b]) for L, a, b in F['segs'] if a[0] < 568700 and a != b]
ATREE = STRtree(ARCH)
def serbest(x, y, r, s, h):
    L = len(s) * h * 0.55; g = affinity.rotate(box(x - L / 2, y - h / 2 - 2, x + L / 2, y + h / 2 + 2), r, origin=(x, y))
    return len(ATREE.query(g, predicate='intersects')) == 0
for x, y, r, s, h in LBL:
    if any(abs(y - fy) < fl / 2 + len(s) * h * 0.4 and abs(x - (LO[ln](fy))) < 80 for ln, fy, fl in FANS): continue
    ok_ = None
    for d in [0, 40, -40, 80, -80, 120, -120, 160, -160, 200, -200, 250, -250, 300, -300]:
        yy = y + d; xx = (UP[next(k for k in UP if abs(UP[k] - x) < 1)] if yy >= Y_J1 else x + 0.02855 * d) if any(abs(UP[k] - x) < 1 for k in UP) else x + 0.02855 * d
        if serbest(xx, yy, r, s, h): ok_ = (xx, yy); break
    if ok_: T(ok_[0], ok_[1], s, h, rot=r)
    else: T(x, y, s, h, rot=r)

# menfez sembolü (kanal yanağı): kanal kenarına bitişik dikdörtgen + çapraz
MTAB = []
def menfez(tag, x, y, side, lay, L, D=10, yon='x', q=0, olc=''):
    if yon == 'x':        # dikey kanal, yanağa yatay çıkıntı
        x0, x1 = (x, x + side * D); y0, y1 = y - L / 2, y + L / 2
        x0, x1 = min(x0, x1), max(x0, x1)
        tx, ty, rot = x + side * (D + 9), y, 90
    else:                 # yatay kanal, yanağa düşey çıkıntı
        y0, y1 = (y, y + side * D); x0, x1 = x - L / 2, x + L / 2
        y0, y1 = min(y0, y1), max(y0, y1)
        tx, ty, rot = x, y + side * (D + 9), 0
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'ROTAS-HVAC-MENFEZ', True)
    msp.add_line((x0, y0), (x1, y1), dxfattribs={'layer': 'ROTAS-HVAC-MENFEZ'})
    msp.add_line((x0, y1), (x1, y0), dxfattribs={'layer': 'ROTAS-HVAC-MENFEZ'})
    T(tx, ty, tag, 11, 'ROTAS-HVAC-YAZI', rot=rot)
q_g = lambda q, vf: next(f'{a}x{b}' for a, b in [(300, 150), (300, 200), (400, 200), (400, 250), (500, 250), (600, 300), (800, 300), (1000, 300)] if a * b / 1e6 * 0.7 * vf * 3600 >= q)
gE, gT = q_g(qE1, 4.0), q_g(qT1, 4.0)
for tag, x, y, side, lay in MENF:
    olc = gE if tag[0] == 'E' else gT
    menfez(tag, x, y, side, lay, int(olc.split('x')[0]) / 10, q=0, olc=olc)
gSA, gSD, gSE = q_g(S['qsec'] / 4, 2.5), q_g(S['qdts'] / 4, 3.0), q_g(S['qeg'] / 3, 2.5)
for tag, x, y, side, lay, yon in SMENF:
    olc = {'SA': gSA, 'SD': gSD, 'SE': gSE}[tag[:2]]
    wd = SW_[{'SA': 'A', 'SD': 'D', 'SE': 'S'}[tag[:2]]][0] / 10
    menfez(tag, x, y + side * wd / 2, side, lay, int(olc.split('x')[0]) / 10, yon='y')

# ---------------------------------------------------------------- şaftlar
def saft(bx, ad, alt):
    x0, y0, x1, y1 = bx
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'ROTAS-HVAC-SAFT', True)
    PL([(x0 + 10, y0 + 10), (x1 - 10, y0 + 10), (x1 - 10, y1 - 10), (x0 + 10, y1 - 10)], 'ROTAS-HVAC-SAFT', True)
    msp.add_hatch(color=8, dxfattribs={'layer': 'ROTAS-HVAC-SAFT'}).paths.add_polyline_path(
        [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True, flags=1)
    h = msp.query('HATCH').last
    h.paths.add_polyline_path([(x0 + 10, y0 + 10), (x1 - 10, y0 + 10), (x1 - 10, y1 - 10), (x0 + 10, y1 - 10)], is_closed=True, flags=16)
    h.set_pattern_fill('ANSI31', scale=6.0)
def riser(cx_, cy_, w, d, lay):
    PL([(cx_ - w / 2, cy_ - d / 2), (cx_ + w / 2, cy_ - d / 2), (cx_ + w / 2, cy_ + d / 2), (cx_ - w / 2, cy_ + d / 2)], lay, True)
    msp.add_line((cx_ - w / 2, cy_ - d / 2), (cx_ + w / 2, cy_ + d / 2), dxfattribs={'layer': lay})
    msp.add_line((cx_ - w / 2, cy_ + d / 2), (cx_ + w / 2, cy_ - d / 2), dxfattribs={'layer': lay})
saft(SAFT_E, 'EGZOZ ŞAFTI', '')
saft(SAFT_T, 'TAZE HAVA ŞAFTI', '')
wE, hE = oE[-1][3] / 10, oE[-1][4] / 10
riser(E_end[0], 4516985, wE, hE, E.lay)
riser(LO['D'](SAFT_E[3]), 4516990, 40, 30, D.lay); riser(LO['S'](SAFT_E[3]), 4516995, 40, 20, Sx.lay)
riser(566688, 4517210, wB, oB[-1][4] / 10, B.lay); riser(566765, 4517240, 40, 20, A.lay)
# kanalları şaft iç yüzüne kadar uzat (şaft duvarından geçiş)
for H, x, w in [(E, E_end[0], wE), (D, LO['D'](SAFT_E[3]), 40), (Sx, LO['S'](SAFT_E[3]), 40)]:
    draw_poly(box(x - w / 2, SAFT_E[3] - 10, x + w / 2, SAFT_E[3]), H.lay)
for H, x, w in [(B, 566688, wB), (A, 566765, 40)]:
    draw_poly(box(x - w / 2, SAFT_T[3] - 10, x + w / 2, SAFT_T[3]), H.lay)

# ---------------------------------------------------------------- cihazlar (kanal içi fan / santral sembolleri)
def fan(x, y, w, L, tag, rot=90, lay='ROTAS-HVAC-CIHAZ'):
    """kanal üstünde fan: dikdörtgen gövde + daire + kanat; rot=90 dikey kanal"""
    if rot == 90: x0, y0, x1, y1 = x - w / 2 - 3, y - L / 2, x + w / 2 + 3, y + L / 2
    else: x0, y0, x1, y1 = x - L / 2, y - w / 2 - 3, x + L / 2, y + w / 2 + 3
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, True)
    r = min(x1 - x0, y1 - y0) / 2 - 4
    msp.add_circle((x, y), r, dxfattribs={'layer': lay})
    for a in (0, 120, 240):
        a1 = math.radians(a + 90 if rot == 90 else a)
        msp.add_line((x, y), (x + r * 0.9 * math.cos(a1), y + r * 0.9 * math.sin(a1)), dxfattribs={'layer': lay})
    return (x0, y0, x1, y1)
yF = 4517330
fan(LO['E'](yF), yF, wE, 110, 'DTF-1')
yT = 4517720
fan(LO['B'](yT), yT, wB, 120, 'TF-1')
# sığınak cihazları
x0, y0, x1, y1 = santral
PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'ROTAS-HVAC-CIHAZ', True)
for k in range(1, 4): msp.add_line((x0 + k * 35, y0), (x0 + k * 35, y1), dxfattribs={'layer': 'ROTAS-HVAC-CIHAZ'})
fan(UP['D'], 4522690, 40, 70, 'SDF-1'); T(UP['D'] + 30, 4522690, 'SDF-1', 11, al=TA.MIDDLE_LEFT)
fan(567640, YI_S, 40, 70, 'SEF-1', rot=0); T(567700, YI_S + 35, 'SEF-1', 11, al=TA.MIDDLE_LEFT)
T((santral[0] + santral[2]) / 2, santral[3] + 14, 'SHC-1', 11)
# gaz geçirmez kapama vanaları (perde geçişlerinde, iki yüzde)
for lane in ('A', 'D', 'S'):
    for yy in (Y_TOP - 12, Y_TOP + 52):
        msp.add_line((UP[lane] - 25, yy), (UP[lane] + 25, yy), dxfattribs={'layer': 'ROTAS-HVAC-CIHAZ'})
        msp.add_circle((UP[lane], yy), 6, dxfattribs={'layer': 'ROTAS-HVAC-CIHAZ'})

# ---------------------------------------------------------------- etiket balonları (kılavuzlu, mimariden uzak)
def balon(px, py, tx, ty, lines, h=11):
    msp.add_line((px, py), (tx, ty), dxfattribs={'layer': 'ROTAS-HVAC-YAZI'})
    msp.add_circle((px, py), 2, dxfattribs={'layer': 'ROTAS-HVAC-YAZI'})
    wmax = max(len(s) for s in lines) * h * 0.62 + 16; hh = len(lines) * h * 1.6 + 8
    al_left = tx >= px
    bx0 = tx if al_left else tx - wmax
    PL([(bx0, ty - hh / 2), (bx0 + wmax, ty - hh / 2), (bx0 + wmax, ty + hh / 2), (bx0, ty + hh / 2)], 'ROTAS-HVAC-YAZI', True)
    for i, s in enumerate(lines):
        T(bx0 + 8, ty + hh / 2 - 4 - h * 0.8 - i * h * 1.6, s, h, al=TA.MIDDLE_LEFT)
    return (bx0, ty - hh / 2, bx0 + wmax, ty + hh / 2)
BAL = []
BAL.append(balon(LO['E'](yF) + wE / 2 + 3, yF, 567900, 4517520, ['DTF-1 OTOPARK DUMAN TAHLİYE / EGZOZ FANI', f'{fmt(O["qdts"])} m³/h - 400 °C / 2 saat - çift devirli']))
BAL.append(balon(LO['B'](yT) - wB / 2 - 3, yT, 566380, 4517900, ['TF-1 OTOPARK TAZE HAVA FANI', f'{fmt(O["qth"])} m³/h - çift devirli']))
BAL.append(balon(SAFT_E[2], (SAFT_E[1] + SAFT_E[3]) / 2, 567900, 4516950,
                 ['EGZOZ / DUMAN TAHLİYE ŞAFTI (2 saat yangın dayanımlı)', 'otopark egzoz + sığınak egzoz + sığınak duman', 'ayrı kanallarla zemin kotu üzerine çıkar, panjurla atılır']))
BAL.append(balon(SAFT_T[0], (SAFT_T[1] + SAFT_T[3]) / 2, 566380, 4517100,
                 ['TAZE HAVA ŞAFTI', 'otopark taze hava + sığınak taze hava', 'ayrı kanallarla zemin kotu üzerinden', 'kuş teli + yağmur panjurlu emiş']))
BAL.append(balon(UP['A'], Y_TOP + 20, 566290, 4522250, ['PERDE GEÇİŞLERİ (gaz geçirmez kapama vanalı)', f'TAZE HAVA {S["g_th"]}', f'DUMAN {S["g_dt"]}  -  EGZOZ {S["g_eg"]}']))

# akış okları (dolu üçgen) — her hatta birkaç adet, kanal içinde
def ok(x, y, ang, lay, s=14):
    a = math.radians(ang)
    p1 = (x + s * math.cos(a), y + s * math.sin(a)); p2 = (x + s * 0.5 * math.cos(a + 2.5), y + s * 0.5 * math.sin(a + 2.5))
    p3 = (x + s * 0.5 * math.cos(a - 2.5), y + s * 0.5 * math.sin(a - 2.5))
    h = msp.add_hatch(color=256, dxfattribs={'layer': lay}); h.paths.add_polyline_path([p1, p2, p3], is_closed=True)
    PL([p1, p2, p3], lay, True)
for y in [4522100, 4520700, 4519230, 4517760]:
    ok(UP['E'] if y >= Y_J1 else LO['E'](y), y - 120, -90, 'ROTAS-HVAC-OK')
for y in [4522100, 4520700, 4519230]:
    ok(UP['B'] if y >= Y_J1 else LO['B'](y), y - 120, 90, 'ROTAS-HVAC-OK')
for lane, ang in (('A', 90), ('D', -90), ('S', -90)):
    for y in [4521550, 4519700, 4518300]:
        ok(UP[lane] if y >= Y_J1 else LO[lane](y), y + 40, ang, 'ROTAS-HVAC-OK', 10)

# başlık
T(567300, 4524000, 'BODRUM KAT - SIĞINAK HAVALANDIRMA VE OTOPARK TAZE HAVA / DUMAN TAHLİYE PLANI  Ö: 1/50', 40)
T(567300, 4523910, 'Tüm kanallar otopark girişi (araç asansörü) tarafındaki şaftlardan dışarı çıkar. Otopark net yüksekliği 3,00 m.', 18)

# ---------------------------------------------------------------- BASINÇ KAYBI
def hat_kaybi(out, L_ek, n_dirsek, ek_pa, q_son):
    R = 0; rows = []
    for ya, yb, q, w, h, v in out:
        r, vv = R_pam(q, w, h); L = (ya - yb) / 100; R += r * L; rows.append((w, h, q, vv, r, L))
    w, h = out[-1][3], out[-1][4]; r, v = R_pam(q_son, w, h); R += r * L_ek
    zeta = n_dirsek * 0.3 * 0.6 * v * v + 1.0 * 0.6 * v * v
    return R, zeta, ek_pa, R + zeta + ek_pa, rows
pE = hat_kaybi(oE, 6.0, 3, 30 + 60 + 25, O['qdts'])
pB = hat_kaybi(oB, 12.0, 4, 30 + 60 + 25, O['qth'])
def kucuk(q, w, h, L, nd, ek):
    r, v = R_pam(q, w, h); return r * L + nd * 0.3 * 0.6 * v * v + ek, r, v
Ld = (Y_TOP - SAFT_E[3]) / 100 + 12; La = (Y_TOP - 4517330) / 100 + 7 + 22
pSA = kucuk(S['qsec'], 400, 200, La + 10, 7, 30 + 60 + 25 + 40)
pSD = kucuk(S['qdts'], 400, 300, Ld + 10, 4, 30 + 60 + 25 + 40)
pSE = kucuk(S['qeg'], 400, 200, Ld + 6, 3, 30 + 60 + 25 + 40)
P = lambda p: up(p * 1.1, 50)
FAN = {'DTF-1': P(pE[3]), 'TF-1': P(pB[3]), 'SHC-1': P(pSA[0] + 150), 'SDF-1': P(pSD[0]), 'SEF-1': P(pSE[0])}

# ---------------------------------------------------------------- TABLOLAR (planın solunda)
def tbox(x0, y0, x1, y1, lay='ROTAS-HESAP-CIZGI', w=0.0):
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, True, w)
def tablo(x, y, cols, rows, h=11, rh=24, hdr=True):
    for i, rw in enumerate(rows):
        xx = x
        for w, v in zip(cols, rw):
            tbox(xx, y, xx + w, y - rh)
            T(xx + w / 2, y - rh / 2, str(v), h * (0.9 if (hdr and i == 0) else 1.0), 'ROTAS-HESAP-YAZI')
            xx += w
        y -= rh
    return y
def kv(x, y, W, baslik, items, h=11, rh=24, c1=480):
    T(x, y - 12, baslik, h * 1.3, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); y -= 32
    for a, b in items:
        tbox(x, y, x + c1, y - rh); tbox(x + c1, y, x + W, y - rh)
        T(x + 10, y - rh / 2, a, h, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); T(x + c1 + (W - c1) / 2, y - rh / 2, b, h, 'ROTAS-HESAP-YAZI'); y -= rh
    return y - 20
def notlar(x, y, lines, h=10.5):
    for s in lines: T(x, y - 8, s, h, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); y -= h * 1.8
    return y - 12

TX, TY = 563300, 4523700; W = 1000
# 1) SIĞINAK
yy = TY; y0 = yy
T(TX + W / 2, yy - 16, 'SIĞINAK - CİHAZ LİSTESİ', 13.5, 'ROTAS-HESAP-YAZI'); yy -= 34
yy = tablo(TX, yy, [70, 360, 300, 90, 180], [
    ['SIRA', 'CİHAZ ADI', 'KAPASİTE', 'MİKTAR', 'AÇIKLAMA'],
    ['1', 'SIĞINAK HAVALANDIRMA CİHAZI (SHC-1)', f"{fmt(S['qsec'])} m³/h  {FAN['SHC-1']} Pa", '1', 'El çevirmeli kollu'],
    ['2', 'KANAL TİPİ EGZOZ FANI (SEF-1)', f"{fmt(S['qeg'])} m³/h  {FAN['SEF-1']} Pa", '1', ''],
    ['3', 'DUMAN TAHLİYE FANI (SDF-1)', f"{fmt(S['qdts'])} m³/h  {FAN['SDF-1']} Pa", '1', '400 °C / 2 saat'],
    ['4', 'GAZ GEÇİRMEZ KAPAMA VANASI', 'perde geçiş ölçüsünde', '6', 'her geçişte iki yüz']])
yy -= 26
T(TX, yy - 14, 'SIĞINAK HAVALANDIRMA HESABI', 18, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 40
yy = notlar(TX, yy, ['SIĞINAK YÖNETMELİĞİ (Resmi Gazete Tarihi: 25.08.1988 Resmi Gazete Sayısı: 19910)',
                     'Madde 8 – (Başlığı ile birlikte değişik: RG-29/9/2010-27714)'], 11)
yy = tablo(TX + 20, yy, [220, 190, 270, 270], [
    ['Sığınak Kapasitesi', 'Koruma Havalandırması', 'Yüksek Yangın Tehlikesi', 'Düşük ve Orta Yangın Tehlikesi'],
    ['0-50 kişiye kadar', '1,8 m³/h-kişi', 'Kum filtre,', 'G4 toz filtre'],
    ['51-150 kişiye kadar', '3,0 m³/h-kişi', 'G4 toz filtre ve', 'Radyoaktif filtre ve'],
    ['150 kişiden fazla', '4,5 m³/h-kişi', 'Aktif karbon filtre', 'Aktif karbon filtre']], h=10.5)
yy -= 24
yy = kv(TX, yy, W, 'SIĞINAK GENEL HAVALANDIRMA HESABI', [
    ('Sığınak Net Alanı', f"{fmt(SIG_A, 2)} m²"), ('Sığınak Net Yüksekliği', f"{fmt(SIG_H, 2)} m"), ('Sığınak Hacmi', f"{fmt(S['V'], 2)} m³"),
    ('Hava Değişim Sayısı', '4 defa/saat'), ('Taze Hava İçin Gerekli Hava', f"{fmt(S['qth'], 2)} m³/h"),
    ('Seçilen Taze Hava Debisi', f"{fmt(S['qsec'])} m³/h"), ('Egzoz Debisi (taze havadan %10 az)', f"{fmt(S['qeg'])} m³/h"),
    ('Perde Geçişi - Taze Hava (v = 2,5 m/s)', S['g_th']), ('Perde Geçişi - Egzoz (v = 2,5 m/s)', S['g_eg'])])
yy = kv(TX, yy, W, 'SIĞINAK DUMAN TAHLİYE HAVALANDIRMASI HESABI (net alan > 100 m²)', [
    ('Sığınak Net Alanı', f"{fmt(SIG_A, 2)} m²"), ('Sığınak Net Yüksekliği', f"{fmt(SIG_H, 2)} m"), ('Sığınak Hacmi', f"{fmt(S['V'], 2)} m³"),
    ('Çevrim Oranı', '10 defa/saat'), ('Duman Tahliye İçin Gerekli Hava', f"{fmt(S['qdt'], 2)} m³/h"),
    ('Seçilen Duman Tahliye Debisi', f"{fmt(S['qdts'])} m³/h"), ('Perde Geçişi - Duman Tahliye (v = 2,5 m/s)', S['g_dt'])])
yy = notlar(TX, yy, ['Sığınak havalandırma fanının enerji ihtiyacı fan elektrik motoruna uygun kapasitede bir jeneratör ile karşılanmalı,',
                     'jeneratör için sığınak alanı dışında bir alan makine dairesi olarak tasarlanmalıdır. Jeneratör egzozu doğrudan dışarıya',
                     'verilmelidir. Jeneratörün devre dışı kaldığı durumlarda ise, enerji ihtiyacı fana bağlı insan gücü ile çalışan çevirmeli',
                     'kol yardımı ile karşılanmalıdır.'])
tbox(TX - 20, y0 + 10, TX + W + 20, yy, 'ROTAS-HESAP-CERCEVE', 1.0)
# 2) OTOPARK
yy -= 60; y0 = yy
T(TX, yy - 14, 'OTOPARK TAZE HAVA VE DUMAN TAHLİYE HESABI', 18, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 44
yy = kv(TX, yy, W, 'OTOPARK HAVALANDIRMA HESABI', [
    ('Otopark Net Alanı (kolon, merdiven, asansör, tesisat alanı hariç)', f"{fmt(OTO_A, 2)} m²"), ('Otopark Net Yüksekliği', f"{fmt(OTO_H, 2)} m"),
    ('Otopark Hacmi', f"{fmt(O['V'], 2)} m³"), ('Duman Tahliye Hava Değişimi', '10 defa/saat'),
    ('Duman Tahliye İçin Gerekli Hava', f"{fmt(O['qdt'], 2)} m³/h"), ('Seçilen Duman Tahliye / Egzoz Debisi', f"{fmt(O['qdts'])} m³/h"),
    ('Taze Hava Debisi (egzozdan %10 az, otopark negatif basınçta)', f"{fmt(O['qth'])} m³/h"),
    ('Normal Havalandırma (6 defa/saat, fan düşük devir)', f"{fmt(O['qn'])} m³/h"),
    ('Egzoz Menfezi Adedi / Debisi', f"{NG} ad. x {fmt(qE1)} m³/h  ({gE})"), ('Taze Hava Menfezi Adedi / Debisi', f"{NG} ad. x {fmt(qT1)} m³/h  ({gT})")], c1=600)
T(TX, yy - 12, 'OTOPARK - CİHAZ LİSTESİ', 14.3, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 32
yy = tablo(TX, yy, [70, 360, 300, 90, 180], [
    ['SIRA', 'CİHAZ ADI', 'KAPASİTE', 'MİKTAR', 'AÇIKLAMA'],
    ['1', 'DUMAN TAHLİYE / EGZOZ FANI (DTF-1)', f"{fmt(O['qdts'])} m³/h  {FAN['DTF-1']} Pa", '1', '400 °C/2 saat, 2 devir'],
    ['2', 'TAZE HAVA FANI (TF-1)', f"{fmt(O['qth'])} m³/h  {FAN['TF-1']} Pa", '1', '2 devir'],
    ['3', 'EGZOZ MENFEZİ (E1-E10)', f"{gE}  {fmt(qE1)} m³/h", str(NG), 'kanal yanağı, ayarlı'],
    ['4', 'TAZE HAVA MENFEZİ (T1-T10)', f"{gT}  {fmt(qT1)} m³/h", str(NG), 'kanal yanağı, ayarlı'],
    ])
yy -= 30
T(TX, yy - 12, 'KANAL BOYUTLARI VE BASINÇ KAYBI', 14.3, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 32
rows = [['HAT', 'KANAL (mm)', 'DEBİ (m³/h)', 'HIZ (m/s)', 'R (Pa/m)', 'L (m)']]
for nm, o in (('EGZOZ', oE), ('TAZE HAVA', oB)):
    for ya, yb, q, w, h, v in o:
        r, _ = R_pam(q, w, h); rows.append([nm, f'{w}x{h}', fmt(q), fmt(v, 2), fmt(r, 2), fmt((ya - yb) / 100, 1)])
for nm, q, (w, h), L in (('SIĞ. TAZE', S['qsec'], SW_['A'], La + 10), ('SIĞ. DUMAN', S['qdts'], SW_['D'], Ld + 10), ('SIĞ. EGZOZ', S['qeg'], SW_['S'], Ld + 6)):
    r, v = R_pam(q, w, h); rows.append([nm, f'{w}x{h}', fmt(q), fmt(v, 2), fmt(r, 2), fmt(L, 1)])
yy = tablo(TX, yy, [170, 150, 160, 140, 140, 120], rows, h=10, rh=21)
yy -= 16
yy = tablo(TX, yy, [260, 170, 170, 170, 150], [
    ['FAN', 'Sürtünme (Pa)', 'Özel kayıp (Pa)', 'Menfez+şaft+panjur', 'Seçilen (Pa)'],
    ['DTF-1', fmt(pE[0]), fmt(pE[1]), fmt(pE[2]), str(FAN['DTF-1'])],
    ['TF-1', fmt(pB[0]), fmt(pB[1]), fmt(pB[2]), str(FAN['TF-1'])],
    ['SHC-1 (+150 Pa filtre)', fmt(pSA[1] * (La + 10)), fmt(pSA[0] - pSA[1] * (La + 10) - 155), '155', str(FAN['SHC-1'])],
    ['SDF-1', fmt(pSD[1] * (Ld + 10)), fmt(pSD[0] - pSD[1] * (Ld + 10) - 155), '155', str(FAN['SDF-1'])],
    ['SEF-1', fmt(pSE[1] * (Ld + 6)), fmt(pSE[0] - pSE[1] * (Ld + 6) - 155), '155', str(FAN['SEF-1'])]], h=10, rh=21)
yy -= 10
yy = notlar(TX, yy, [
    'NOTLAR:',
    '1- Otopark duman tahliyesi 10 hava değişimine göre (net alan x net yükseklik x 10) hesaplanmıştır; taze hava egzozdan %10 azdır.',
    '2- Fanlar çift devirlidir: normal işletmede CO dedektörleri ile düşük devir (6 defa/saat), yangın alarmında yüksek devir (10 defa/saat).',
    '3- DTF-1 ve egzoz kanalı 400 °C / 2 saat dayanımlıdır; egzoz kanalları 1,0 mm galvaniz, flanşlı, yangın dayanımlı askılıdır.',
    '4- Tüm kanallar otopark girişi (araç asansörü) tarafındaki şaftlardan çıkar; egzoz ve taze hava şaft ağızları zemin kotunda',
    '   birbirinden en az 5 m uzak ve egzoz ağzı taze hava ağzından yüksek olacaktır (şaft yerleri mimari ile koordine edilecektir).',
    '5- Sığınak taze hava, egzoz ve duman tahliye kanalları otopark kanallarından ayrı hattır; perde geçişlerinde iki yüzde gaz',
    '   geçirmez kapama vanası bulunur. Sığınak kanalları otopark içinde 2 saat yangın dayanımlı kaplanacaktır.',
    '6- Kanal alt kotu en az +2,25 m; kanallar araç yolu tavanında, betonarme kolonlardan bağımsız güzergâhta asılır.',
    '7- Kanal boyutları mm (en x yükseklik), menfez etiketleri E (egzoz), T (taze hava), SA/SE/SD (sığınak) kodludur.'])
tbox(TX - 20, y0 + 10, TX + W + 20, yy, 'ROTAS-HESAP-CERCEVE', 1.0)
# 3) LEJANT
yy -= 60; y0 = yy
T(TX, yy - 14, 'LEJANT', 18, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 50
for lay, ad in (('ROTAS-HVAC-OTP-EGZOZ', 'Otopark egzoz / duman tahliye kanalı'), ('ROTAS-HVAC-OTP-TAZE', 'Otopark taze hava kanalı'),
                ('ROTAS-HVAC-SIG-TAZE', 'Sığınak taze hava kanalı'), ('ROTAS-HVAC-SIG-EGZOZ', 'Sığınak egzoz kanalı'),
                ('ROTAS-HVAC-SIG-DUMAN', 'Sığınak duman tahliye kanalı')):
    PL([(TX, yy), (TX + 160, yy), (TX + 160, yy - 20), (TX, yy - 20)], lay, True)
    T(TX + 190, yy - 10, ad, 11, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 40
menfez('', TX + 80, yy - 10, +1, '', 60, yon='y'); T(TX + 190, yy - 5, 'Kanal yanağı menfezi (ayar damperli)', 11, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 45
fan(TX + 80, yy - 15, 30, 60, '', rot=0); T(TX + 190, yy - 15, 'Kanal içi fan', 11, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 55
riser(TX + 80, yy - 15, 40, 25, 'ROTAS-HVAC-SAFT'); T(TX + 190, yy - 15, 'Şaftta düşey kanal (yukarı)', 11, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 50
msp.add_line((TX + 66, yy - 15), (TX + 94, yy - 15), dxfattribs={'layer': 'ROTAS-HVAC-CIHAZ'}); msp.add_circle((TX + 80, yy - 15), 7, dxfattribs={'layer': 'ROTAS-HVAC-CIHAZ'})
T(TX + 190, yy - 15, 'Gaz geçirmez kapama vanası (sığınak perde geçişi)', 11, 'ROTAS-HESAP-YAZI', al=TA.MIDDLE_LEFT); yy -= 50
tbox(TX - 20, y0 + 10, TX + W + 20, yy, 'ROTAS-HESAP-CERCEVE', 1.0)

doc.saveas(OUT)
pickle.dump(dict(G={k: v for k, v in G.items()}, BAL=BAL, S=S, O=O, oE=oE, oB=oB, FAN=FAN, SAFT=(SAFT_E, SAFT_T), gE=gE, gT=gT,
                 gS=(gSA, gSD, gSE)), open(OUT + '.pkl', 'wb'))
print('S', {k: v for k, v in S.items()}); print('O', O); print('FAN', FAN, gE, gT, gSA, gSD, gSE)
for o in (oE, oB):
    for r in o: print([round(v, 2) if isinstance(v, float) else v for v in r])
