# -*- coding: utf-8 -*-
"""Sprinkler boru ağı (ortogonal ağaç) — README yangın kuralları:
- kolon (riser) dağıtım mahallinin (koridor / tek hacim) DUVAR KÖŞESİNDEN çıkar, mahal ortasından çıkmaz;
- koridor ana hattı koridor ekseninde; koridor başlıkları doğrudan ana hat üzerinde;
- her mahal beslemesi KAPIDAN girer: ana hattan kapı açıklığı içinden dik iner, duvar ile ilk branşman arasında
  duvara paralel gider, mahal dağıtım borusuna (branşmanlara dik) bağlanır; branşmanlar kapı duvarına paraleldir;
- boru çapı README ROTAŞ/Aselsan tablosu ile aşağı akış başlık sayısından (kurallar.dn_sec).
Bütün güzergâhlar betonarme kolonlara (KOLON_BORU_PAY) karşı kontrol edilir; çakışmada başka aday denenir.
"""
import math
import networkx as nx
from kurallar import dn_sec, SINIF
from yerlesim import yerlesim, uv, xy, rect_uv

KOLON_BORU_PAY = 10.0     # boru ekseni kolon yüzünden en az (cm)
KOSE_ICERI = 15.0         # kolon (riser) ekseni duvar yüzlerinden (cm)
TAP_BASLIK = 40.0         # ana hattan sapma noktası koridor başlığından en az (cm)
TAP_TAP = 30.0
E_ADAY = [50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 120.0]   # besleme bacağının duvardan uzaklığı (cm)


def _seg_kolon(a, b, kolonlar, pad=KOLON_BORU_PAY):
    """ortogonal parça kolon dikdörtgenine (pad ile) değiyor mu"""
    x0, x1 = sorted((a[0], b[0]))
    y0, y1 = sorted((a[1], b[1]))
    for k in kolonlar:
        if x0 < k[2] + pad and x1 > k[0] - pad and y0 < k[3] + pad and y1 > k[1] - pad:
            return True
    return False


def _yol_kolon(pts, kolonlar):
    return any(_seg_kolon(a, b, kolonlar) for a, b in zip(pts[:-1], pts[1:]))


def _sadele(pts):
    out = []
    for p in pts:
        p = (round(p[0], 1), round(p[1], 1))
        if out and math.dist(out[-1], p) < 0.5:
            continue
        out.append(p)
    i = 1
    while i < len(out) - 1:      # doğrusal ara noktaları at
        a, b, c = out[i - 1], out[i], out[i + 1]
        if (abs(a[0] - b[0]) < 0.1 and abs(b[0] - c[0]) < 0.1) or (abs(a[1] - b[1]) < 0.1 and abs(b[1] - c[1]) < 0.1):
            out.pop(i)
        else:
            i += 1
    return out


def kapi_eksen(m):
    """kapı hangi duvarda: yatay duvarda -> branşman ekseni 'x', düşey duvarda -> 'y'"""
    x0, y0, x1, y1 = m['rect']
    px, py = m['kapi']['p']
    d = {'alt': abs(py - y0), 'ust': abs(py - y1), 'sol': abs(px - x0), 'sag': abs(px - x1)}
    yan = min(d, key=d.get)
    return ('x' if yan in ('alt', 'ust') else 'y'), yan


def mahal_besleme(m, yer, giris_uv, v_duvar, s, bas_xy, kolonlar):
    """Kapı (veya kolon) girişinden mahal dağıtım borusuna besleme + branşman hatları. Dönüş: [(rol, pts_xy)]"""
    ax = yer['axis']
    rows = sorted(yer['rows'], key=lambda v: s * (v - v_duvar))
    cols = sorted(yer['cols'])
    nu = len(cols)
    d1 = s * (rows[0] - v_duvar)
    eler = [e for e in E_ADAY if e <= d1 - 40.0] or [d1 / 2.0]
    if nu >= 2:
        uc = [((cols[i] + cols[i + 1]) / 2.0, max(i + 1, nu - i - 1)) for i in range(nu - 1)]
        uc.sort(key=lambda t: (t[1], abs(t[0] - giris_uv[0])))
        uc = [t[0] for t in uc]
    else:
        uc = sorted([cols[0] + 60.0, cols[0] - 60.0], key=lambda u: abs(u - giris_uv[0]))
    for u_c in uc:
        for e in eler:
            v_e = v_duvar + s * e
            yol_uv = [(giris_uv[0], v_e), (u_c, v_e), (u_c, rows[-1])]
            pts = _sadele([bas_xy] + [xy(ax, u, v) for u, v in yol_uv])
            if _yol_kolon(pts, kolonlar):
                continue
            hat = [('besleme', pts)]
            ok = True
            for v in rows:
                ua, ub = min(cols[0], u_c), max(cols[-1], u_c)
                r = [xy(ax, ua, v), xy(ax, ub, v)]
                if _yol_kolon(r, kolonlar):
                    ok = False
                    break
                hat.append(('brans', r))
            if ok:
                return hat
    raise ValueError(f"{m['ad']}: besleme güzergâhı kolonlardan kaçamadı")


def _kose_noktasi(D, kose, kolonlar, ax):
    x0, y0, x1, y1 = D['rect']
    k = KOSE_ICERI
    px = x0 + k if 'sol' in kose else x1 - k
    py = y0 + k if 'alt' in kose else y1 - k
    # köşede betonarme kolon varsa duvar boyunca (uzun eksen) kolondan çıkana kadar kaydır
    u, v = uv(ax, px, py)
    u0, v0, u1, v1 = rect_uv(ax, D['rect'])
    yon = 1.0 if abs(u - u0) < abs(u - u1) else -1.0
    for _ in range(400):
        p = xy(ax, u, v)
        if not _seg_kolon(p, p, kolonlar, pad=12.0):
            return p
        u += yon * 5.0
    raise ValueError('kolon (riser) için köşede yer bulunamadı')


def tasarla(P):
    kolonlar = [tuple(k) for k in P.get('kolonlar', [])]
    mahaller = P['mahaller']
    D = [m for m in mahaller if m.get('dagitim')]
    assert len(D) == 1, 'tam bir dağıtım mahalli (dagitim: true) olmalı'
    D = D[0]
    x0, y0, x1, y1 = D['rect']
    axD = 'x' if (x1 - x0) >= (y1 - y0) else 'y'
    axD = D.get('brans_ekseni', axD)
    yer = {}
    # dağıtım mahalli: önce tek sıra (koridor), olmazsa ızgara
    try:
        yer[D['ad']] = yerlesim(D, axD, kolonlar, tek_satir=True)
        tek = True
    except ValueError:
        yer[D['ad']] = yerlesim(D, axD, kolonlar)
        tek = False
    for m in mahaller:
        if m is D:
            continue
        ax, yan = kapi_eksen(m)
        m['_yan'] = yan
        yer[m['ad']] = yerlesim(m, m.get('brans_ekseni', ax), kolonlar)
    kh = P.get('kolon_hatti', {})
    R = _kose_noktasi(D, kh.get('kose', 'sol-alt'), kolonlar, axD)
    hatlar = []
    Ru, Rv = uv(axD, *R)
    u0, v0, u1, v1 = rect_uv(axD, D['rect'])
    yon = 1.0 if abs(Ru - u0) < abs(Ru - u1) else -1.0
    if tek:
        yD = yer[D['ad']]
        v_c = yD['rows'][0]
        heads_u = sorted(yD['cols'])
        taps = []
        diger = []
        for m in mahaller:
            if m is D:
                continue
            kp = m['kapi']['p']
            ku, kv = uv(axD, *kp)
            if not (u0 - 1 < ku < u1 + 1 and v0 - 40 < kv < v1 + 40):
                raise ValueError(f"{m['ad']}: kapı dağıtım mahalline açılmıyor (desteklenmiyor)")
            w = m['kapi'].get('w', 90.0)
            cand = sorted([ku + d for d in [i * 5.0 for i in range(-int((w / 2 - 15) / 5), int((w / 2 - 15) / 5) + 1)]],
                          key=lambda u: abs(u - ku))
            ut = None
            for u in cand:
                if any(abs(u - h) < TAP_BASLIK for h in heads_u) or any(abs(u - t) < TAP_TAP for t in taps) \
                        or abs(u - Ru) < TAP_BASLIK:
                    continue
                ut = u
                break
            if ut is None:
                raise ValueError(f"{m['ad']}: kapıda sapma noktası bulunamadı")
            taps.append(ut)
            diger.append((m, ut, kv))
        ucs = heads_u + taps
        u_end = max(ucs) if yon > 0 else min(ucs)
        ana = _sadele([R, xy(axD, Ru, v_c), xy(axD, u_end, v_c)])
        if _yol_kolon(ana, kolonlar):
            raise ValueError('ana hat kolona çarpıyor')
        hatlar.append(('ana', ana))
        for m, ut, kv in diger:
            ym = yer[m['ad']]
            axm = ym['axis']
            assert axm == axD, f"{m['ad']}: branşman ekseni koridora paralel olmalı"
            mu0, mv0, mu1, mv1 = ym['uv_rect']
            # oda duvar yüzü: kapının bulunduğu kenar
            if abs(kv - mv0) < abs(kv - mv1):
                v_duvar, s = mv0, 1.0
            else:
                v_duvar, s = mv1, -1.0
            hatlar += mahal_besleme(m, ym, (ut, kv), v_duvar, s, xy(axD, ut, v_c), kolonlar)
    else:
        yD = yer[D['ad']]
        if abs(Rv - v0) < abs(Rv - v1):
            v_duvar, s = v0, 1.0
        else:
            v_duvar, s = v1, -1.0
        hatlar += mahal_besleme(D, yD, (Ru, Rv), v_duvar, s, R, kolonlar)
        for m in mahaller:
            if m is not D:
                raise ValueError('çok sıralı dağıtım mahallinde ek mahal beslemesi henüz desteklenmiyor')
    net = ag_kur(P, yer, hatlar, R, mahaller)
    # R2: kademeli çap (kollektör -> kolon -> zon -> kat ağı ana hattı her ayrımda en fazla bir kademe)
    import kademe
    T_, R_ = net['T'], net['root']
    kok_dn = max(T_[R_][c]['dn'] for c in T_.successors(R_))
    z = kademe.sema_zinciri(P.get('hidrolik', {}).get('besleme_dn', 100), kok_dn)
    net['kademe_degisen'] = kademe.uygula(net, z['zon'])
    net['sema_dn'] = z
    return net


def ag_kur(P, yer, hatlar, R, mahaller):
    heads = {}
    for m in mahaller:
        y = yer[m['ad']]
        for p in y['heads']:
            heads[(round(p[0], 1), round(p[1], 1))] = dict(mahal=m['ad'], sinif=m['sinif'], cov=y['cov'][p])
    segs = []
    R1 = lambda p: (round(p[0], 1), round(p[1], 1))
    hatlar = [(rol, [R1(p) for p in pts]) for rol, pts in hatlar]
    for rol, pts in hatlar:
        for a, b in zip(pts[:-1], pts[1:]):
            segs.append((a, b, rol))
    nodes = set(heads) | {a for a, b, r in segs} | {b for a, b, r in segs}
    # ortogonal kesişimler (dağıtım borusu x branşman)
    for i, (a, b, _) in enumerate(segs):
        for c, d, _ in segs[i + 1:]:
            h1 = abs(a[1] - b[1]) < 0.1
            h2 = abs(c[1] - d[1]) < 0.1
            if h1 == h2:
                continue
            H, V = ((a, b), (c, d)) if h1 else ((c, d), (a, b))
            x, y = V[0][0], H[0][1]
            if min(H[0][0], H[1][0]) - 0.1 <= x <= max(H[0][0], H[1][0]) + 0.1 and \
                    min(V[0][1], V[1][1]) - 0.1 <= y <= max(V[0][1], V[1][1]) + 0.1:
                nodes.add((round(x, 1), round(y, 1)))
    G = nx.Graph()
    for a, b, rol in segs:
        on = [n for n in nodes if _uzerinde(n, a, b)]
        on.sort(key=lambda n: math.dist(a, n))
        for p, q in zip(on[:-1], on[1:]):
            if math.dist(p, q) < 0.5:
                continue
            if G.has_edge(p, q):
                raise ValueError(f'üst üste binen boru: {p}-{q}')
            G.add_edge(p, q, L=math.dist(p, q), rol=rol)
    root = (round(R[0], 1), round(R[1], 1))
    for h in heads:
        if h not in G:
            raise ValueError(f'bağlanmamış başlık {h}')
    if not nx.is_tree(G):
        raise ValueError('boru ağı ağaç değil (döngü / kopukluk)')
    T = nx.bfs_tree(G, root)
    cnt = {n: (1 if n in heads else 0) for n in T.nodes}
    for n in reversed(list(nx.topological_sort(T))):
        for c in T.successors(n):
            cnt[n] += cnt[c]
    for a, b in T.edges:
        T[a][b].update(G[a][b])
        T[a][b]['n'] = cnt[b]
        T[a][b]['dn'] = dn_sec(cnt[b])
    return dict(T=T, root=root, heads=heads, hatlar=hatlar, yer=yer, cnt=cnt, G=G)


def _uzerinde(n, a, b):
    if abs(a[0] - b[0]) < 0.1:       # düşey
        return abs(n[0] - a[0]) < 0.2 and min(a[1], b[1]) - 0.2 <= n[1] <= max(a[1], b[1]) + 0.2
    return abs(n[1] - a[1]) < 0.2 and min(a[0], b[0]) - 0.2 <= n[0] <= max(a[0], b[0]) + 0.2
