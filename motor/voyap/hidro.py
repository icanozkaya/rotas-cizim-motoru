"""Sprinkler hidrolik hesabı (TS EN 12845, Hazen-Williams C=120), en elverişsiz tasarım alanı, ağaç üzerinde dengeli çözüm."""
import pickle, math
import numpy as np
import networkx as nx
VY = '/tmp/claude-0/vy/'
from geo import KATAD
ID = {25: 27.3, 32: 36.0, 40: 41.9, 50: 53.1, 65: 68.9, 80: 80.9, 100: 105.3, 125: 130.0, 150: 155.4}
C = 120.0; KF = 80.0; PMIN = 0.35; FIT = 1.20          # fitting eşdeğer boy payı %20
SINIF = {0: ('OH2', 5.0, 144.0, 9.0), 1: ('OH2', 5.0, 144.0, 12.0), 2: ('OH1', 5.0, 72.0, 12.0), 3: ('OH1', 5.0, 72.0, 12.0)}
KOT = {0: 3.20, 1: 6.70, 2: 9.70, 3: 12.70}           # pompa ekseninden tavan borusu kotu (m) - kabul
def hw(q, dn, L):          # bar
    if q <= 0: return 0.0
    d = ID[dn]
    return 6.05e5 * q ** 1.85 / (C ** 1.85 * d ** 4.87) * L * FIT

def calc(i, R, H):
    ts = R[i]['ts']; T = ts['T']; root = ts['root']
    E = {(e['a'], e['b']): e for e in ts['edges']}
    hn = ts['hn']
    sinif, dens, area, cov = SINIF[i]
    # en uzak başlık (boru yolu)
    dist = nx.single_source_dijkstra_path_length(T.to_undirected(), root, weight=lambda a, b, d: E.get((a, b), E.get((b, a)))['L'])
    rem = max(set(hn), key=lambda n: dist[n])
    # tasarım alanı: en uzak başlığa en yakın N başlık (bodrumda ara seviye başlıklar da)
    pts = np.array(rem)
    hs = [(k, h) for k, h in enumerate(H[i])]
    N = math.ceil(area / cov)
    near = sorted([k for k, h in hs if H[i][k]['t'] != 'ARA'], key=lambda k: math.dist(H[i][k]['p'], rem))[:N]
    ara = []
    if i == 0:   # tasarım alanı içindeki lift platform altı başlıklar
        rr = max(math.dist(H[i][k]['p'], rem) for k in near)
        ara = [k for k, h in hs if h['t'] == 'ARA' and math.dist(h['p'], rem) <= rr]
    act = set(near) | set(ara)
    qmin = max(dens * cov, KF * math.sqrt(PMIN))
    pdes = (qmin / KF) ** 2
    nodeh = {}
    for k in act: nodeh.setdefault(hn[k], []).append(k)
    # alttan üste: her düğüm için (Q, p) — alt dalları dengele
    FLOW = {}
    def solve(n):
        subs = []
        for c in T.successors(n):
            e = E[(n, c)]
            r = solve(c)
            if r is None: continue
            Q, p = r
            FLOW[(n, c)] = Q
            subs.append((Q, p + hw(Q, e['dn'], e['L'] / 100.0)))
        if n in nodeh:
            for _ in nodeh[n]: subs.append((qmin, pdes))
        if not subs: return None
        P = max(p for Q, p in subs)
        Qt = sum(Q * math.sqrt(P / p) for Q, p in subs)
        return Qt, P
    Qs, Ps = solve(root)
    path = nx.shortest_path(T, root, rem)
    det = [(E[(a, b)]['cap'], E[(a, b)]['dn'], E[(a, b)]['L'] / 100.0, FLOW.get((a, b), 0.0)) for a, b in zip(path[:-1], path[1:])]
    # aynı çap ve debideki ardışık parçaları birleştir
    mg = []
    for c_, dn, L_, q in det:
        if mg and mg[-1][0] == c_ and abs(mg[-1][3] - q) < 0.5: mg[-1][2] += L_
        else: mg.append([c_, dn, L_, q])
    return dict(det=mg, kat=KATAD[i], sinif=sinif, yog=dens, alan=area, N=len(act), ara=len(ara), qmin=qmin, pdes=pdes, Q=Qs, P=Ps,
                rem=rem, act=sorted(act), Lrem=dist[rem] / 100.0)

def ozet():
    R = pickle.load(open(VY + 'routes.pkl', 'rb')); H = pickle.load(open(VY + 'heads.pkl', 'rb'))
    res = []
    for i in range(4):
        r = calc(i, R, H)
        # kat girişinden pompaya: bodrum -> pompa dairesi; üst katlar -> K1 kolonu + bodrum bağlantısı (DN100) + AV
        if i == 0:
            Lsup, dn = 8.0, 100
        else:
            Lsup, dn = 10.0 + KOT[i] - 3.2, 100
        dpsup = hw(r['Q'], dn, Lsup) + 0.25 + 0.10          # alarm vanası 0,25 bar + kat kontrol/kelebek 0,10 bar
        r['Pp'] = r['P'] + dpsup + KOT[i] / 10.2
        r['Lsup'] = Lsup
        res.append(r)
    # dolap: en uzak 2 dolap aynı anda 2x100 l/dk, nozulda 4 bar (2. kat) 
    qd = 200.0
    pd = 4.0 + hw(100.0, 50, 25.0) + hw(qd, 65, 30.0) + 0.3 + 11.3 / 10.2      # 2. kat dolap +11,30 m
    return res, dict(Q=qd, P=pd)

if __name__ == '__main__':
    res, d = ozet()
    for r in res:
        print(f"{r['kat']:10s} {r['sinif']} N={r['N']:2d} (ara {r['ara']}) q={r['qmin']:.1f} l/dk Qsp={r['Q']:.0f} l/dk  P_kat={r['P']:.2f} bar  P_pompa={r['Pp']:.2f} bar  Luzak={r['Lrem']:.0f} m")
    print('dolap', d)
    w = max(res, key=lambda r: r['Pp'])
    Qt = max(r['Q'] for r in res) + d['Q']
    print('pompa ihtiyacı Q=', round(Qt * 0.06, 1), 'm3/h  H=', round(max(w['Pp'], d['P']) * 10.2, 1), 'mSS')
