"""Kuyu iç ölçüsü ölçer: olc.py flat.pkl x y [x y ...]
Noktadan sol/sağ/yukarı/aşağı ışın atar; ilk 3 duvar çizgisini (katman ile) listeler."""
import pickle, sys
fl = pickle.load(open(sys.argv[1], 'rb'))
pts = list(map(float, sys.argv[2:]))
SKIP = {'TEFRIS-Yaşar', 'KUTUPHANE', 'YAZI', 'ÖLÇÜ', 'ÖLÇÜ DIŞ', 'OLÇÜ', 'OLCU', 'Aks', 'kesit çizgisi', 'MEKAN YAZILARI', 'M_Yazı', 'TEXT', 'T', 'YZ30', 'KOT', 'NKOT', 'iç alan', 'ARABA', 'PV PANEL'}
V, H = [], []
for r in fl:
    if r[0] not in 'LP' or r[1] in SKIP: continue
    p = list(r[2])
    for a, b in zip(p, p[1:]):
        if abs(a[0] - b[0]) < 0.2 and abs(a[1] - b[1]) > 5: V.append((a[0], min(a[1], b[1]), max(a[1], b[1]), r[1]))
        if abs(a[1] - b[1]) < 0.2 and abs(a[0] - b[0]) > 5: H.append((a[1], min(a[0], b[0]), max(a[0], b[0]), r[1]))
for i in range(0, len(pts), 2):
    x, y = pts[i], pts[i + 1]
    L = sorted({(round(x - v[0], 1), v[3]) for v in V if v[1] <= y <= v[2] and v[0] < x})[:3]
    R = sorted({(round(v[0] - x, 1), v[3]) for v in V if v[1] <= y <= v[2] and v[0] > x})[:3]
    D = sorted({(round(y - h[0], 1), h[3]) for h in H if h[1] <= x <= h[2] and h[0] < y})[:3]
    U = sorted({(round(h[0] - y, 1), h[3]) for h in H if h[1] <= x <= h[2] and h[0] > y})[:3]
    gen = [round(L[k][0] + R[k][0], 1) for k in range(min(len(L), len(R), 2))]
    der = [round(D[k][0] + U[k][0], 1) for k in range(min(len(D), len(U), 2))]
    print(f'({x:.0f},{y:.0f}) GEN(x) {gen}  DER(y) {der}   sol {L[:2]} sag {R[:2]} alt {D[:2]} ust {U[:2]}')
