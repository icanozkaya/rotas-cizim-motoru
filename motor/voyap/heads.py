"""Başlık listeleri: kullanıcının MTY başlıkları + 1. kat (2. kattan kopya) + bodrum lift ara seviye başlıkları."""
import pickle
from shapely.geometry import Point
VY = '/tmp/claude-0/vy/'
from geo import OFF
U = pickle.load(open(VY + 'heads_user.pkl', 'rb'))
M = pickle.load(open(VY + 'mimT.pkl', 'rb'))
B = pickle.load(open(VY + 'liftbox.pkl', 'rb'))
def typ(n): return 'P' if 'PENDANT' in n else 'U'
H = {0: [], 1: [], 2: [], 3: []}
for i in (0, 1, 3):
    for x, y, n in U[i]:
        H[i].append(dict(p=(x, y), t=typ(n), yeni=False))
dx = OFF[2][0] - OFF[3][0]; dy = OFF[2][1] - OFF[3][1]
for x, y, n in U[3]:
    H[2].append(dict(p=(x + dx, y + dy), t=typ(n), yeni=True))
lifts = [r for r in M if r[0] == 'T' and 'lift' in r[2][1]]
nl = 0
for b in B:
    if any(b.buffer(60).contains(Point(r[2][0])) for r in lifts) and b.area < 13e4:
        c = b.centroid
        nl += 1      # lift ara seviyesine sprinkler KONMAZ (kullanıcı talimatı 13.10)
DEPO = (248235.0, -451720.0, 248640.0, -450860.0)   # 80 m³ yangın suyu deposu (tesisat alanı kuzeyi)
n0 = len(H[0])
H[0] = [h for h in H[0] if not (DEPO[0] < h['p'][0] < DEPO[2] and DEPO[1] < h['p'][1] < DEPO[3])]
print('depo içinden çıkarılan başlık', n0 - len(H[0]))
for i in H: print(i, len(H[i]), sum(h['yeni'] for h in H[i]))
pickle.dump(H, open(VY + 'heads.pkl', 'wb'))
