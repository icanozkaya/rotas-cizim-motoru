"""Çift asansör kuyusu bulucu: aynı y'de, araları 8-30 cm duvar olan iki yatay 180-260 cm çizgi
+ bunlara dik 170-230 cm düşey çizgiler (dikdörtgen kuyu)."""
import pickle, sys, collections
fl = pickle.load(open(sys.argv[1], 'rb'))
H = collections.defaultdict(list)
V = collections.defaultdict(list)
for r in fl:
    if r[0] == 'L': pts = list(r[2])
    elif r[0] == 'P': pts = r[2]
    else: continue
    for a, b in zip(pts, pts[1:]):
        if abs(a[1] - b[1]) < 0.3 and 150 < abs(a[0] - b[0]) < 280:
            H[round(a[1], 0)].append((min(a[0], b[0]), max(a[0], b[0]), r[1]))
        if abs(a[0] - b[0]) < 0.3 and 150 < abs(a[1] - b[1]) < 280:
            V[round(a[0], 0)].append((min(a[1], b[1]), max(a[1], b[1]), r[1]))
Vx = sorted(V)
import bisect
def vert_at(x, y0, y1):
    i = bisect.bisect_left(Vx, x - 1.5)
    while i < len(Vx) and Vx[i] <= x + 1.5:
        for s, e, l in V[Vx[i]]:
            if abs(s - y0) < 3 and abs(e - y1) < 3 or abs(s - y1) < 3 and abs(e - y0) < 3: return True
        i += 1
    return False
found = set()
for y, segs in H.items():
    segs = sorted(set((round(a, 1), round(b, 1)) for a, b, l in segs))
    for i, (a1, b1) in enumerate(segs):
        for a2, b2 in segs:
            if 6 <= a2 - b1 <= 30:
                # karşı kenarı bul
                for dy in range(170, 240):
                    for yy in (y + dy, y - dy):
                        if yy in H and any(abs(s - a1) < 2 and abs(e - b1) < 2 for s, e, _ in H[yy]) \
                                and any(abs(s - a2) < 2 and abs(e - b2) < 2 for s, e, _ in H[yy]):
                            y0, y1 = min(y, yy), max(y, yy)
                            if vert_at(a1, y0, y1) or vert_at(b2, y0, y1):
                                found.add((a1, b1, a2, b2, y0, y1))
# yatay dizilim yanında düşey dizilimli (kuyular üst üste) çiftleri de ara
for x, segs in V.items():
    segs = sorted(set((round(a, 1), round(b, 1)) for a, b, l in segs))
    for a1, b1 in segs:
        for a2, b2 in segs:
            if 6 <= a2 - b1 <= 30:
                for dx in range(170, 240):
                    for xx in (x + dx, x - dx):
                        if xx in V and any(abs(s - a1) < 2 and abs(e - b1) < 2 for s, e, _ in V[xx]) \
                                and any(abs(s - a2) < 2 and abs(e - b2) < 2 for s, e, _ in V[xx]):
                            found.add(('D', min(x, xx), max(x, xx), a1, b1, a2, b2))
for f in sorted(found, key=str):
    if f[0] == 'D':
        _, x0, x1, a1, b1, a2, b2 = f
        print(f'DUSEY  x {x0:.1f}-{x1:.1f} (gen {x1-x0:.1f})  kuyu1 y {a1}-{b1} ({b1-a1:.1f})  duvar {a2-b1:.1f}  kuyu2 y {a2}-{b2} ({b2-a2:.1f})')
    else:
        a1, b1, a2, b2, y0, y1 = f
        print(f'YATAY  y {y0:.1f}-{y1:.1f} (der {y1-y0:.1f})  kuyu1 x {a1}-{b1} ({b1-a1:.1f})  duvar {a2-b1:.1f}  kuyu2 x {a2}-{b2} ({b2-a2:.1f})')
