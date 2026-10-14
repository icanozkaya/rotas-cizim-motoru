# -*- coding: utf-8 -*-
"""Yangın dolabı otomatik yerleşimi ve erişim kontrolü (06_YANGIN.md §5).

Akış:
 1) Izgara: mahal poligonları (dikdörtgen, duvar iç yüzleri) + kapı açıklıkları serbest, duvar / betonarme kolon / merdiven
    kapalı. Hücre 20 cm. 16 komşulu (at hamlesi dahil) Dijkstra -> duvar ve kapı etrafından GERÇEK YÜRÜME YOLU
    (öklid değil). Köşe kesme yok: çapraz ve at hamlelerinde ara hücreler de serbest olmalı.
 2) Aday dolap yerleri: dağıtım mahalli (koridor / otopark) duvarları boyunca 25 cm adımla, serbest duran kolon
    yüzleri; yedek olarak diğer mahallerin duvarları (2. öncelik). Kapı açıklığı, betonarme kolon, sprinkler borusu /
    başlığı / kolonu üstüne dolap konmaz.
 3) Erişim: dolap önündeki noktadan yürüme yolu ≤ hortum (30 m) + lüle menzili (5 m).
 4) Seçim: her merdiven / kat girişinin yanına bir dolap (zorunlu tohum), sonra açgözlü küme kapsama (her adımda en çok
    yeni alanı kapsayan aday; merdiven/çıkış yakınındakiler %10 öncelikli), sonra fazlalık budama, sonra dolaplar arası
    en fazla mesafe (sprinklerli 45 m) kontrolü ve gerekirse ara dolap.
 5) Dolap kolonları YG1..: merdiven yanındaki dolapların bitişiğinde (duvar köşesi tarafı); diğer dolaplar en yakın
    kolondan koridor duvarı boyunca (A*, dik açılı, kolon / duvar / sprinkler borusu kaçınmalı) DN50 yatay hatla,
    dolap bağlantısı DN32.
 6) Hidrolik: en elverişsiz (en üst kat, en uzak) dolapta 4 bar, eşzamanlı dolap debisi pompa debisine eklenir.
"""
import math
import heapq
import numpy as np
import networkx as nx
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy import ndimage
from dolap_kurallar import ayarlar
from kurallar import IC_CAP, hw_birim, hiz

HAMLE = [(1, 0), (0, 1), (1, 1), (1, -1), (2, 1), (1, 2), (2, -1), (1, -2)]
ARA = {(1, 1): [(1, 0), (0, 1)], (1, -1): [(1, 0), (0, -1)], (2, 1): [(1, 0), (1, 1)], (1, 2): [(0, 1), (1, 1)],
       (2, -1): [(1, 0), (1, -1)], (1, -2): [(0, -1), (1, -1)]}


def kapi_yani(p, rect):
    x0, y0, x1, y1 = rect
    d = {'alt': abs(p[1] - y0), 'ust': abs(p[1] - y1), 'sol': abs(p[0] - x0), 'sag': abs(p[0] - x1)}
    return min(d, key=d.get)


def _kaydir(F, dx, dy):
    """G[i, j] = F[i+dx, j+dy] (dışarısı False)"""
    G = np.zeros_like(F)
    nx_, ny_ = F.shape
    xs = slice(max(0, -dx), min(nx_, nx_ - dx))
    xd = slice(max(0, dx), min(nx_, nx_ + dx))
    ys = slice(max(0, -dy), min(ny_, ny_ - dy))
    yd = slice(max(0, dy), min(ny_, ny_ + dy))
    G[xs, ys] = F[xd, yd]
    return G


def kutu_kesisir(a, b, pay=0.0):
    return a[0] < b[2] + pay and a[2] > b[0] - pay and a[1] < b[3] + pay and a[3] > b[1] - pay


def seg_kutu_kesisir(p, q, b, pay=0.0):
    k = (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))
    return kutu_kesisir(k, b, pay)


class Plan:
    """yürüme ızgarası + kapılar + merdivenler"""

    def __init__(self, P, D, k):
        self.P, self.D, self.k = P, D, k
        c = self.c = k['hucre_cm']
        self.mahaller = P['mahaller']
        self.kolonlar = [tuple(q) for q in P.get('kolonlar', [])]
        self.merdivenler = D.get('merdivenler', [])
        self.cikislar = D.get('cikislar', [])
        dis = P['dis_hat']
        tum = [m['rect'] for m in self.mahaller] + [s['rect'] for s in self.merdivenler] + [dis] + \
              [e['rect'] for e in self.cikislar if e.get('rect')]
        X0 = min(r[0] for r in tum) - 2 * c
        Y0 = min(r[1] for r in tum) - 2 * c
        X1 = max(r[2] for r in tum) + 2 * c
        Y1 = max(r[3] for r in tum) + 2 * c
        self.X0, self.Y0 = X0, Y0
        nx_, ny_ = int(math.ceil((X1 - X0) / c)), int(math.ceil((Y1 - Y0) / c))
        xs = X0 + (np.arange(nx_) + 0.5) * c
        ys = Y0 + (np.arange(ny_) + 0.5) * c
        XX, YY = np.meshgrid(xs, ys, indexing='ij')
        self.XX, self.YY = XX, YY
        mid = np.full(XX.shape, -1, dtype=int)
        for i, m in enumerate(self.mahaller):
            x0, y0, x1, y1 = m['rect']
            mid[(XX >= x0) & (XX < x1) & (YY >= y0) & (YY < y1)] = i
        self.mid = mid
        kol = np.zeros(XX.shape, bool)
        for q in self.kolonlar:
            kol |= (XX >= q[0]) & (XX < q[2]) & (YY >= q[1]) & (YY < q[3])
        mer = np.zeros(XX.shape, bool)
        for s in self.merdivenler:
            x0, y0, x1, y1 = s['rect']
            mer |= (XX >= x0) & (XX < x1) & (YY >= y0) & (YY < y1)
        ic = (XX >= dis[0]) & (XX < dis[2]) & (YY >= dis[1]) & (YY < dis[3])
        free = mid >= 0
        self.kapilar = []          # (p, w, yan, rect, ad, tur)
        for m in self.mahaller:
            if m.get('kapi'):
                p = m['kapi']['p']
                self.kapilar.append((tuple(p), m['kapi'].get('w', 90.0), kapi_yani(p, m['rect']), m['rect'], m['ad'], 'mahal'))
        for s in self.merdivenler:
            p = s['kapi']['p']
            self.kapilar.append((tuple(p), s['kapi'].get('w', 100.0), kapi_yani(p, s['rect']), s['rect'], s['ad'], 'merdiven'))
        for e in self.cikislar:
            p = e['p']
            r = e.get('rect') or dis
            self.kapilar.append((tuple(p), e.get('w', 100.0), kapi_yani(p, r), r, e['ad'], 'cikis'))
        for p, w, yan, r, ad, tur in self.kapilar:
            if yan in ('alt', 'ust'):
                msk = (np.abs(XX - p[0]) < w / 2) & (np.abs(YY - p[1]) <= 40)
            else:
                msk = (np.abs(YY - p[1]) < w / 2) & (np.abs(XX - p[0]) <= 40)
            free |= msk & ~mer & ic
        free &= ~kol
        self.free = free
        self.hedef = (mid >= 0) & ~kol
        # graf
        idx = np.full(XX.shape, -1, dtype=int)
        n = int(free.sum())
        idx[free] = np.arange(n)
        self.idx, self.n = idx, n
        R, C, W = [], [], []
        for dx, dy in HAMLE:
            ok = free & _kaydir(free, dx, dy)
            for ax, ay in ARA.get((dx, dy), []):
                ok &= _kaydir(free, ax, ay)
            a = idx[ok]
            b = _kaydir(idx + 1, dx, dy)[ok] - 1
            R.append(a)
            C.append(b)
            W.append(np.full(a.shape, c * math.hypot(dx, dy)))
        R, C, W = np.concatenate(R), np.concatenate(C), np.concatenate(W)
        self.G = coo_matrix((W, (R, C)), shape=(n, n)).tocsr()
        hi = idx[self.hedef]
        self.hedef_dugum = hi[hi >= 0]
        self.hedef_mahal = self.mid[self.hedef][hi >= 0]

    def dugum(self, p, r=3):
        """noktanın hücresi; serbest değilse en yakın serbest hücre"""
        i = int((p[0] - self.X0) // self.c)
        j = int((p[1] - self.Y0) // self.c)
        best = None
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                a, b = i + di, j + dj
                if 0 <= a < self.idx.shape[0] and 0 <= b < self.idx.shape[1] and self.idx[a, b] >= 0:
                    d = math.hypot(self.XX[a, b] - p[0], self.YY[a, b] - p[1])
                    if best is None or d < best[0]:
                        best = (d, int(self.idx[a, b]))
        return None if best is None else best[1]

    def mesafe(self, dugumler, limit=np.inf):
        return dijkstra(self.G, directed=False, indices=dugumler, limit=limit)

    def hucre_alani_m2(self):
        return (self.c / 100.0) ** 2


# ======================================================================================  aday yerler
def _kenarlar(rect):
    """(ad, duvar başı, duvar sonu, iç normal)"""
    x0, y0, x1, y1 = rect
    return [('alt', (x0, y0), (x1, y0), (0, 1)), ('ust', (x0, y1), (x1, y1), (0, -1)),
            ('sol', (x0, y0), (x0, y1), (1, 0)), ('sag', (x1, y0), (x1, y1), (-1, 0))]


def govde_kutu(w, t, n, g, d):
    """duvar noktası w, duvar yönü t, iç normal n -> gövde kutusu"""
    pts = [(w[0] + t[0] * s + n[0] * u, w[1] + t[1] * s + n[1] * u) for s in (-g / 2, g / 2) for u in (0.0, d)]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def adaylar(pl, engeller):
    """engeller: sprinkler boru parçaları [(a,b)], başlık/kolon/vana kutuları [kutu]"""
    k = pl.k
    g, d = k['govde_g'], k['govde_d']
    seg, kutular = engeller
    out = []

    def uygun(kb, kenar_kapilari, s0, s1, s):
        for q in pl.kolonlar:
            if kutu_kesisir(kb, q, k['kolon_pay_cm']):
                return False
        for (a, b) in kenar_kapilari:
            if s + g / 2 + k['kapi_pay_cm'] > a and s - g / 2 - k['kapi_pay_cm'] < b:
                return False
        for a, b in seg:
            if seg_kutu_kesisir(a, b, kb, 4.0):
                return False
        for q in kutular:
            if kutu_kesisir(kb, q, 3.0):
                return False
        return True

    for mi, m in enumerate(pl.mahaller):
        tier = 1 if (m.get('dagitim') or m.get('dolap_yeri')) else 2
        for ad, a, b, nrm in _kenarlar(m['rect']):
            L = math.dist(a, b)
            t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            yatay = abs(t[1]) < 0.5
            kk = []
            for p, w, yan, r, kad, tur in pl.kapilar:
                if yatay and abs(p[1] - a[1]) <= 30 and min(a[0], b[0]) - w < p[0] < max(a[0], b[0]) + w:
                    kk.append((p[0] - a[0] - w / 2, p[0] - a[0] + w / 2))
                if (not yatay) and abs(p[0] - a[0]) <= 30 and min(a[1], b[1]) - w < p[1] < max(a[1], b[1]) + w:
                    kk.append((p[1] - a[1] - w / 2, p[1] - a[1] + w / 2))
            s = g / 2 + 5.0
            while s <= L - g / 2 - 5.0 + 1e-6:
                w_ = (a[0] + t[0] * s, a[1] + t[1] * s)
                kb = govde_kutu(w_, t, nrm, g, d)
                if uygun(kb, kk, 0, L, s):
                    o = (w_[0] + nrm[0] * (d + 10), w_[1] + nrm[1] * (d + 10))
                    out.append(dict(w=w_, t=t, n=nrm, kutu=kb, mahal=m['ad'], mi=mi, tier=tier, yer='duvar', o=o,
                                    duvar=(a, b), s=s, L=L, kapi_araliklari=kk))
                s += 25.0
    # serbest duran betonarme kolon yüzleri (otopark)
    for m in pl.mahaller:
        if not m.get('dagitim'):
            continue
        x0, y0, x1, y1 = m['rect']
        for q in pl.kolonlar:
            if not (q[0] > x0 + 30 and q[2] < x1 - 30 and q[1] > y0 + 30 and q[3] < y1 - 30):
                continue
            cx, cy = (q[0] + q[2]) / 2, (q[1] + q[3]) / 2
            for nrm, w_, t, L in (((0, -1), (cx, q[1]), (1, 0), q[2] - q[0]), ((0, 1), (cx, q[3]), (1, 0), q[2] - q[0]),
                                  ((-1, 0), (q[0], cy), (0, 1), q[3] - q[1]), ((1, 0), (q[2], cy), (0, 1), q[3] - q[1])):
                if L < 50:
                    continue
                kb = govde_kutu(w_, t, nrm, g, d)
                ok = all(not seg_kutu_kesisir(a, b, kb, 4.0) for a, b in seg) and \
                    all(not kutu_kesisir(kb, z, 3.0) for z in kutular) and \
                    all(not kutu_kesisir(kb, z, 1.0) for z in pl.kolonlar if z != q)
                if ok:
                    o = (w_[0] + nrm[0] * (d + 10), w_[1] + nrm[1] * (d + 10))
                    out.append(dict(w=w_, t=t, n=nrm, kutu=kb, mahal=m['ad'], mi=pl.mahaller.index(m), tier=1,
                                    yer='kolon', o=o, kolon=q, duvar=None, s=L / 2, L=L, kapi_araliklari=[]))
    for c in out:
        c['dug'] = pl.dugum(c['o'])
    return [c for c in out if c['dug'] is not None]


# ======================================================================================  seçim
def yerlestir(pl, A):
    k = pl.k
    R = (k['hortum_m'] + k['jet_m']) * 100.0
    dug = [c['dug'] for c in A]
    Dm = pl.mesafe(dug, limit=max(R, k['yakin_m'] * 100.0) + 1)
    H = pl.hedef_dugum
    cov = Dm[:, H] <= R                          # aday x hedef
    alan = pl.hucre_alani_m2()
    # merdiven / çıkış kapılarına yakınlık (kapının iç tarafındaki hücre)
    giris = []
    for p, w, yan, r, ad, tur in pl.kapilar:
        if tur == 'mahal':
            continue
        n_ = {'alt': (0, -1), 'ust': (0, 1), 'sol': (-1, 0), 'sag': (1, 0)}[yan]     # merdiven/çıkış dışına -> kat tarafına
        if tur == 'cikis' and r is pl.P['dis_hat']:
            n_ = (-n_[0], -n_[1])
        q = (p[0] + n_[0] * 45, p[1] + n_[1] * 45)
        dq = pl.dugum(q, r=4)
        if dq is not None:
            giris.append((ad, tur, dq, p))
    yakin = np.zeros((len(A), max(1, len(giris))), bool)
    gd = np.full((len(A), max(1, len(giris))), np.inf)
    if giris:
        Dg = pl.mesafe([g[2] for g in giris], limit=k['yakin_m'] * 100.0 + 1)
        for j in range(len(giris)):
            gd[:, j] = Dg[j, dug]
        yakin = gd <= k['yakin_m'] * 100.0
    secilen, tohum = [], []
    # 1) tohum: her merdivenin (kat girişinin) yanına bir dolap
    for j, (ad, tur, dq, p) in enumerate(giris):
        if tur != 'merdiven':
            continue
        ad_ = [i for i in range(len(A)) if yakin[i, j] and A[i]['tier'] == 1]
        if not ad_:
            continue
        cmax = max(cov[i].sum() for i in ad_)
        ad_ = [i for i in ad_ if cov[i].sum() >= 0.97 * cmax]        # kapsaması %3 içinde olanlardan kapıya en yakını
        i = min(ad_, key=lambda i: (gd[i, j], -cov[i].sum()))
        if i not in secilen:
            secilen.append(i)
            tohum.append(i)
            A[i]['giris'] = ad
    kap = np.zeros(len(H), bool)
    for i in secilen:
        kap |= cov[i]
    # 2) açgözlü küme kapsama
    agirlik = np.where(yakin.any(axis=1), 1.10, 1.0)
    tier = np.array([c['tier'] for c in A])
    while not kap.all():
        kaz = cov[:, ~kap].sum(axis=1) * alan
        sec = None
        for t in (1, 2):
            m = (tier == t) & (kaz >= k['min_kazanc_m2'])
            if m.any():
                skor = np.where(m, kaz * agirlik, -1.0)
                sec = int(np.argmax(skor))
                break
        if sec is None:
            break
        secilen.append(sec)
        kap |= cov[sec]
    # 3) budama (tohumlar korunur)
    for i in list(reversed(secilen)):
        if i in tohum:
            continue
        diger = [j for j in secilen if j != i]
        u = np.zeros(len(H), bool)
        for j in diger:
            u |= cov[j]
        if (u | ~kap).all():
            secilen.remove(i)
    # 4) dolaplar arası en fazla mesafe (yürüme yolu)
    amax = (k['aralik_sprinkler_m'] if pl.D.get('sprinkler', True) else k['aralik_m']) * 100.0
    Dfull = pl.mesafe(dug)
    ek = 0
    while len(secilen) > 1 and ek < 6:
        bozuk = None
        for i in secilen:
            nn = min(Dfull[i, A[j]['dug']] for j in secilen if j != i)
            if nn > amax:
                bozuk = i
                break
        if bozuk is None:
            break
        j = min((j for j in secilen if j != bozuk), key=lambda j: Dfull[bozuk, A[j]['dug']])
        aday = [c for c in range(len(A)) if c not in secilen and A[c]['tier'] == 1]
        if not aday:
            break
        c = min(aday, key=lambda c: max(Dfull[c, A[bozuk]['dug']], Dfull[c, A[j]['dug']]))
        secilen.append(c)
        ek += 1
    # numaralama: tohumlar önce (merdiven sırası), sonra soldan sağa / alttan üste
    diger = sorted([i for i in secilen if i not in tohum], key=lambda i: (round(A[i]['o'][0], -2), A[i]['o'][1]))
    sira = tohum + diger
    dolaplar = []
    for n, i in enumerate(sira):
        c = dict(A[i])
        c['no'] = f'YD-{n + 1:02d}'
        c['aday_i'] = i
        c['tohum'] = i in tohum
        c['yakin'] = bool(yakin[i].any()) if giris else False
        dolaplar.append(c)
    # kapsama
    kap = np.zeros(len(H), bool)
    for i in sira:
        kap |= cov[i]
    ara = []
    for a in range(len(sira)):
        nn = min((Dfull[sira[a], A[sira[b]]['dug']] for b in range(len(sira)) if b != a), default=0.0)
        ara.append(nn / 100.0)
        dolaplar[a]['en_yakin_dolap_m'] = nn / 100.0
    rapor = kapsama_raporu(pl, kap)
    rapor.update(R_m=R / 100.0, aralik_max_m=amax / 100.0, aralik_ok=all(x <= amax / 100.0 + 1e-6 for x in ara),
                 aday=len(A), tohum=len(tohum), giris=[g[0] for g in giris])
    # kontrol için 3 m daha kısa jet (en kötü lüle menzili 3 m) ile kapsama oranı
    R3 = (k['hortum_m'] + min(3.0, k['jet_m'])) * 100.0
    k3 = np.zeros(len(H), bool)
    for i in sira:
        k3 |= Dm[i, H] <= R3
    rapor['oran_jet3'] = float(k3.mean())
    return dolaplar, kap, cov[sira], rapor


def kapsama_raporu(pl, kap):
    alan = pl.hucre_alani_m2()
    H = pl.hedef_dugum
    mahal = {}
    for mi, m in enumerate(pl.mahaller):
        msk = pl.hedef_mahal == mi
        mahal[m['ad']] = dict(alan=float(msk.sum() * alan), kapsanmayan=float((msk & ~kap).sum() * alan))
    return dict(hedef_m2=float(len(H) * alan), kapsanan_m2=float(kap.sum() * alan),
                kapsanmayan_m2=float((~kap).sum() * alan), oran=float(kap.mean()), mahal=mahal)


# ======================================================================================  kapsama poligonları
def hucre_poligon(pl, maske_dugum):
    """düğüm maskesinden (serbest hücre sırası) birleşik shapely poligonu: satır şeritleri -> birleşim"""
    from shapely.geometry import box
    from shapely.ops import unary_union
    F = np.zeros(pl.free.shape, bool)
    F[pl.free] = maske_dugum
    c = pl.c
    serit = []
    for i in range(F.shape[0]):
        col = F[i]
        if not col.any():
            continue
        j = 0
        n = len(col)
        while j < n:
            if col[j]:
                j0 = j
                while j < n and col[j]:
                    j += 1
                serit.append(box(pl.X0 + i * c, pl.Y0 + j0 * c, pl.X0 + (i + 1) * c, pl.Y0 + j * c))
            else:
                j += 1
    if not serit:
        return None
    return unary_union(serit).simplify(0.1)


# ======================================================================================  besleme güzergâhı
class Rota:
    """10 cm ızgarada dik açılı en ucuz yol (Dijkstra, dönüş cezası). Boru ekseni duvar / kolon yüzünden ≥ 10 cm."""

    def __init__(self, pl, engel_seg, engel_kutu, dolap_kutulari, h=10.0):
        self.pl, self.h = pl, h
        P = pl.P
        tum = [m['rect'] for m in pl.mahaller]
        X0 = min(r[0] for r in tum) - 2 * h
        Y0 = min(r[1] for r in tum) - 2 * h
        X1 = max(r[2] for r in tum) + 2 * h
        Y1 = max(r[3] for r in tum) + 2 * h
        X0 = math.floor(X0 / h) * h
        Y0 = math.floor(Y0 / h) * h
        self.X0, self.Y0 = X0, Y0
        nx_, ny_ = int(math.ceil((X1 - X0) / h)), int(math.ceil((Y1 - Y0) / h))
        xs = X0 + (np.arange(nx_) + 0.5) * h
        ys = Y0 + (np.arange(ny_) + 0.5) * h
        XX, YY = np.meshgrid(xs, ys, indexing='ij')
        self.XX, self.YY = XX, YY
        free = np.zeros(XX.shape, bool)
        for r in tum:
            free |= (XX >= r[0]) & (XX < r[2]) & (YY >= r[1]) & (YY < r[3])
        for p, w, yan, r, ad, tur in pl.kapilar:
            if tur != 'mahal':
                continue
            if yan in ('alt', 'ust'):
                free |= (np.abs(XX - p[0]) < w / 2 - 15) & (np.abs(YY - p[1]) <= 40)
            else:
                free |= (np.abs(YY - p[1]) < w / 2 - 15) & (np.abs(XX - p[0]) <= 40)
        for q in pl.kolonlar:
            free &= ~((XX >= q[0]) & (XX < q[2]) & (YY >= q[1]) & (YY < q[3]))
        dist = ndimage.distance_transform_edt(free) * h - h / 2      # en yakın engel yüzüne yaklaşık mesafe (cm)
        ok = free & (dist >= 9.0)
        for kb in list(engel_kutu) + list(dolap_kutulari):
            ok &= ~((XX >= kb[0] - 6) & (XX <= kb[2] + 6) & (YY >= kb[1] - 6) & (YY <= kb[3] + 6))
        self.ok = ok
        cost = np.where((dist >= 9.0) & (dist <= 24.0), 1.0, 1.6)
        sp = np.zeros(XX.shape, bool)
        for a, b in engel_seg:
            sp |= (XX >= min(a[0], b[0]) - 8) & (XX <= max(a[0], b[0]) + 8) & (YY >= min(a[1], b[1]) - 8) & \
                (YY <= max(a[1], b[1]) + 8)
        # R2 (14.10.2026 B): BORU ATLATMA YOK — sprinkler borusunun 8 cm yakınından geçiş (kesişme) yasak
        self.ok &= ~sp
        self.cost = cost
        self.ag = np.zeros(XX.shape, bool)       # mevcut dolap besleme ağı (hedef)

    def hucre(self, p):
        return (int((p[0] - self.X0) // self.h), int((p[1] - self.Y0) // self.h))

    def merkez(self, ij):
        return (self.X0 + (ij[0] + 0.5) * self.h, self.Y0 + (ij[1] + 0.5) * self.h)

    def ag_ekle(self, pts):
        for a, b in zip(pts[:-1], pts[1:]):
            self.ag |= (self.XX >= min(a[0], b[0]) - 6) & (self.XX <= max(a[0], b[0]) + 6) & \
                (self.YY >= min(a[1], b[1]) - 6) & (self.YY <= max(a[1], b[1]) + 6)

    def yol(self, bas, ilk_yon=None, donus=25.0):
        """bas: başlangıç noktası (dolap bağlantı ucu); hedef: mevcut ağ hücreleri. Dönüş: hücre listesi"""
        s = self.hucre(bas)
        nx_, ny_ = self.ok.shape
        ok = self.ok.copy()
        ok[s] = True
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        best = {}
        pq = []
        for di, d in enumerate(dirs):
            if ilk_yon is not None and d != ilk_yon:
                continue
            best[(s, di)] = 0.0
            heapq.heappush(pq, (0.0, s, di, None))
        prev = {}
        hit = None
        while pq:
            g, u, di, pr = heapq.heappop(pq)
            if g > best.get((u, di), 1e18) + 1e-9:
                continue
            if (u, di) in prev:
                pass
            prev[(u, di)] = pr
            if self.ag[u] and u != s:
                hit = (u, di)
                break
            for dj, d in enumerate(dirs):
                if (dj ^ 1) == di and pr is not None:
                    continue
                v = (u[0] + d[0], u[1] + d[1])
                if not (0 <= v[0] < nx_ and 0 <= v[1] < ny_) or not (ok[v] or self.ag[v]):
                    continue
                c = self.cost[v] + (donus if (dj != di) else 0.0)
                if self.ag[v]:
                    c = 1.0 + (donus if dj != di else 0.0)
                ng = g + c
                if ng < best.get((v, dj), 1e18) - 1e-9:
                    best[(v, dj)] = ng
                    heapq.heappush(pq, (ng, v, dj, (u, di)))
        if hit is None:
            return None
        cells = []
        st = hit
        while st is not None:
            cells.append(st[0])
            st = prev.get(st)
        cells.reverse()
        return cells


def _sadele(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, out[-1]) < 0.01:
            continue
        if len(out) >= 2:
            a, b = out[-2], out[-1]
            if (abs(a[0] - b[0]) < 0.01 and abs(b[0] - p[0]) < 0.01) or (abs(a[1] - b[1]) < 0.01 and abs(b[1] - p[1]) < 0.01):
                out[-1] = p
                continue
        out.append(p)
    return out


def hucre_poligon_cizgi(rota, cells, bas, ag_segler, kok):
    """hücre yolu -> dik açılı polyline; ilk parça başlangıç noktasının ekseninde; son nokta mevcut ağ parçasına dik
    birleşim (T) ya da kolon noktası."""
    pts = _sadele([rota.merkez(c) for c in cells])
    seg = []
    for a, b in zip(pts[:-1], pts[1:]):
        seg.append(['h', a[1]] if abs(a[1] - b[1]) < 0.01 else ['v', a[0]])
    if not seg:
        return None
    seg[0][1] = bas[1] if seg[0][0] == 'h' else bas[0]
    son = pts[-1]
    hedef = None
    for a, b in ag_segler:
        if math.dist(a, b) < 1:
            continue
        if abs(a[1] - b[1]) < 0.01 and seg[-1][0] == 'v' and min(a[0], b[0]) + 1 <= seg[-1][1] <= max(a[0], b[0]) - 1 \
                and abs(son[1] - a[1]) <= 12:
            hedef = (seg[-1][1], a[1])
            break
        if abs(a[0] - b[0]) < 0.01 and seg[-1][0] == 'h' and min(a[1], b[1]) + 1 <= seg[-1][1] <= max(a[1], b[1]) - 1 \
                and abs(son[0] - a[0]) <= 12:
            hedef = (a[0], seg[-1][1])
            break
    if hedef is None:
        if math.dist(son, kok) > 25:
            return None
        if len(seg) == 1 and abs(seg[0][1] - (kok[1] if seg[0][0] == 'h' else kok[0])) > 0.01:
            # tek parça, eksen kayık: kolona dik küçük kırılma
            if seg[0][0] == 'h':
                xm = kok[0] - math.copysign(15.0, kok[0] - bas[0])
                return _sadele([tuple(bas), (xm, bas[1]), (xm, kok[1]), tuple(kok)])
            ym = kok[1] - math.copysign(15.0, kok[1] - bas[1])
            return _sadele([tuple(bas), (bas[0], ym), (kok[0], ym), tuple(kok)])
        seg[-1][1] = kok[1] if seg[-1][0] == 'h' else kok[0]
        hedef = tuple(kok)
    out = [tuple(bas)]
    for i in range(len(seg) - 1):
        s0, s1 = seg[i], seg[i + 1]
        out.append((s1[1], s0[1]) if s0[0] == 'h' else (s0[1], s1[1]))
    out.append(hedef)
    return _sadele(out)


def besleme_agi(pl, dolaplar, engeller):
    """YG kolonları ve dolap besleme hattı. Dönüş: kolonlar [dict], T (DiGraph, kök = kolon noktaları), uyarılar"""
    k = pl.k
    g = k['govde_g']
    seg, kutular = engeller
    uyari = []
    dk = [d['kutu'] for d in dolaplar]

    def nokta_uygun(p, pay=10.0):
        for q in pl.kolonlar:
            if q[0] - pay < p[0] < q[2] + pay and q[1] - pay < p[1] < q[3] + pay:
                return False
        for kb in dk + list(kutular):
            if kb[0] - 4 < p[0] < kb[2] + 4 and kb[1] - 4 < p[1] < kb[3] + 4:
                return False
        for a, b in seg:
            if seg_kutu_kesisir(a, b, (p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8)):
                return False
        if pl.dugum(p, r=0) is None and not any(m['rect'][0] < p[0] < m['rect'][2] and m['rect'][1] < p[1] < m['rect'][3]
                                                for m in pl.mahaller):
            return False
        return True

    def yan_nokta(d, yon, aci):
        """gövde ucundan 'aci' kadar ötede, duvardan 12 cm"""
        s = yon * (g / 2 + aci)
        return (d['w'][0] + d['t'][0] * s + d['n'][0] * 12.0, d['w'][1] + d['t'][1] * s + d['n'][1] * 12.0)

    def uc(d, yon):
        s = yon * (g / 2)
        return (d['w'][0] + d['t'][0] * s + d['n'][0] * 12.0, d['w'][1] + d['t'][1] * s + d['n'][1] * 12.0)

    def kapi_icinde(d, yon, aci):
        s = d['s'] + yon * (g / 2 + aci)
        if d['yer'] == 'duvar' and not (12.0 <= s <= d['L'] - 12.0):
            return True
        for a, b in d.get('kapi_araliklari', []):
            if a - 10 <= s <= b + 10:
                return True
        return False

    # kolonlar: merdiven tohumları; yoksa ilk dolap
    kok = [d for d in dolaplar if d['tohum']] or dolaplar[:1]
    kolonlar = []

    def kolon_kur(d, n):
        sec = None
        for yon in sorted((1, -1), key=lambda y: (d['L'] - d['s']) if y > 0 else d['s']):     # köşeye yakın taraf önce
            for aci in (45.0, 55.0, 35.0, 25.0, 18.0):
                p = yan_nokta(d, yon, aci)
                if nokta_uygun(p) and not kapi_icinde(d, yon, aci):
                    sec = (p, yon)
                    break
            if sec:
                break
        if sec is None:
            uyari.append(f"{d['no']}: kolon yeri bulunamadı, gövde önüne alındı")
            p = (d['o'][0], d['o'][1])
            sec = (p, 1)
        d['kolon'] = f'YG{n}'
        d['baglanti_uc'] = uc(d, sec[1])
        kc = dict(ad=f'YG{n}', p=sec[0], dolap=d['no'], dolaplar=[d['no']])
        kolonlar.append(kc)
        return kc
    for n, d in enumerate(kok):
        kolon_kur(d, n + 1)
    T = nx.DiGraph()
    for kc in kolonlar:
        d = [x for x in dolaplar if x['no'] == kc['dolap']][0]
        T.add_edge(kc['p'], d['baglanti_uc'], dn=k['baglanti_dn'], tur='baglanti')
        T.nodes[d['baglanti_uc']]['dolap'] = d['no']
        T.nodes[kc['p']]['kolon'] = kc['ad']
    # diğer dolaplar: en yakın kolona yürüme yolu ile, ağ büyüyerek
    diger = [d for d in dolaplar if 'kolon' not in d]
    if diger:
        Dk = pl.mesafe([pl.dugum(kc['p'], r=4) for kc in kolonlar])
        for d in diger:
            j = int(np.argmin([Dk[i, d['dug']] for i in range(len(kolonlar))]))
            d['kolon'] = kolonlar[j]['ad']
            d['_kd'] = Dk[j, d['dug']]
        rota = Rota(pl, seg, kutular, dk)
        for kc in kolonlar:
            grup = sorted([d for d in diger if d['kolon'] == kc['ad']], key=lambda d: d['_kd'])
            if not grup:
                continue
            # kolon ağının başlangıcı: kolon noktasından dolaba ters yönde değil, ilk dolaba doğru kısa bir çıkış
            ag_seg = []
            kok_ = kc['p']
            rota.ag[:] = False
            ii, jj = rota.hucre(kok_)
            rota.ag[max(0, ii - 1):ii + 2, max(0, jj - 1):jj + 2] = True
            for d in grup:
                yol = None
                for yon in sorted((1, -1), key=lambda y: math.dist(yan_nokta(d, y, 45.0), kok_)):
                    if kapi_icinde(d, yon, 45.0):
                        continue
                    on = yan_nokta(d, yon, 45.0)
                    if not nokta_uygun(on, pay=10.0):
                        continue
                    ilk = (int(round(d['t'][0] * yon)), int(round(d['t'][1] * yon)))
                    cells = rota.yol(on, ilk_yon=ilk)
                    if cells is None:
                        continue
                    pts = hucre_poligon_cizgi(rota, cells, on, ag_seg, kok_)
                    if pts is None:
                        continue
                    yol = (pts, on, yon)
                    break
                if yol is None:
                    # R2: sprinkler borusunu kesmeyen güzergâh yok -> dolabın yanına ayrı YG kolonu (atlatma yapılmaz)
                    kn = kolon_kur(d, len(kolonlar) + 1)
                    T.add_edge(kn['p'], d['baglanti_uc'], dn=k['baglanti_dn'], tur='baglanti')
                    T.nodes[d['baglanti_uc']]['dolap'] = d['no']
                    T.nodes[kn['p']]['kolon'] = kn['ad']
                    uyari.append(f"{d['no']}: sprinkler borusunu kesmeyen besleme güzergâhı yok, ayrı kolon {kn['ad']} verildi")
                    continue
                pts, on, yon = yol
                d['baglanti_uc'] = uc(d, yon)
                # ağa ekle: son nokta mevcut bir kenarın üstündeyse kenarı böl
                J = pts[-1]
                J = (round(J[0], 3), round(J[1], 3))
                pts[-1] = J
                if J not in T:
                    for a, b in list(T.edges):
                        if _uzerinde(J, a, b):
                            at = T[a][b]
                            T.remove_edge(a, b)
                            T.add_edge(a, J, **at)
                            T.add_edge(J, b, **at)
                            break
                    else:
                        if math.dist(J, kok_) < 1:
                            J = kok_
                            pts[-1] = kok_
                for a, b in zip(reversed(pts[1:]), reversed(pts[:-1])):
                    T.add_edge(a, b, dn=k['besleme_dn'], tur='besleme')
                T.add_edge(on, d['baglanti_uc'], dn=k['baglanti_dn'], tur='baglanti')
                T.nodes[d['baglanti_uc']]['dolap'] = d['no']
                kc['dolaplar'].append(d['no'])
                rota.ag_ekle(pts)
                ag_seg += list(zip(pts[:-1], pts[1:]))
    # yön: kolonlardan aşağı akış, sayaç = beslenen dolap sayısı
    U = T.to_undirected()
    D = nx.DiGraph()
    for kc in kolonlar:
        if kc['p'] not in U:
            continue
        for a, b in nx.bfs_edges(U, kc['p']):
            D.add_edge(a, b, **U[a][b])
    for n_ in D.nodes:
        D.nodes[n_].update(T.nodes[n_] if n_ in T.nodes else {})
    for a, b in D.edges:
        alt = nx.descendants(D, b) | {b}
        D[a][b]['n'] = sum(1 for x in alt if 'dolap' in D.nodes[x])
        D[a][b]['L'] = math.dist(a, b)
    return kolonlar, D, uyari


def pompa_sec(Q_m3h, P_hes, k, z_p, katlar):
    """R2 pompa seçimi (14.10.2026 B): sistem çalışma basıncı calisma_basinci_bar = [9, 10] aralığında.
    Hidrolik ihtiyaç alt sınırdan küçükse basma yüksekliği alt sınırla (9 bar) seçilir; aralıkta ise ihtiyaç (yukarı
    yuvarlanmış) alınır; üst sınırı aşarsa ihtiyaç alınır ve not düşülür. Seçilen debi hesaplanan debinin üstündeki
    debi adımıdır. En alt katta (çalışma ve kapalı vana) basıncı sistem_max_bar (12) ile karşılaştırılır."""
    from dolap_kurallar import MOTOR_KW
    p0, p1 = k['calisma_basinci_bar']
    H_hes = P_hes * 10.2
    if P_hes <= p0:
        H_sec = p0 * 10.2
        durum = f"hidrolik ihtiyaç {P_hes:.2f} bar < {p0:g} bar: çalışma basıncı {p0:g} bar seçildi"
    elif P_hes <= p1:
        H_sec = H_hes
        durum = f"hidrolik ihtiyaç {P_hes:.2f} bar, {p0:g}-{p1:g} bar aralığında"
    else:
        H_sec = H_hes
        durum = f"hidrolik ihtiyaç {P_hes:.2f} bar > {p1:g} bar: basma yüksekliği hidrolik ihtiyaca göre"
    ad = k['basma_adim_mss']
    H_sec = math.ceil(H_sec / ad - 1e-9) * ad
    qa = k['debi_adim_m3h']
    Q_sec = max(qa, math.ceil(Q_m3h / qa - 1e-9) * qa)
    P_sec = H_sec / 10.2
    kw = 1000 * 9.81 * (Q_sec / 3600) * H_sec / k['pompa_verim'] / 1000 * 1.10
    motor = next((m for m in MOTOR_KW if m >= kw), MOTOR_KW[-1])
    dizel = next((m for m in MOTOR_KW if m >= motor * 1.2), MOTOR_KW[-1])
    alt = min(katlar, key=lambda q: q['kot_m'])
    z_alt = alt['kot_m']                                     # en alt kat döşemesi (en düşük nokta, kabul)
    p_alt_cal = P_sec + (z_p - z_alt) / 10.2
    p_alt_kap = k['kapama_kat'] * P_sec + (z_p - z_alt) / 10.2
    bdv = p_alt_kap > k['sistem_max_bar'] + 1e-9
    PJ = P_sec + k['jokey_ek_bar']
    return dict(Q_hes=Q_m3h, Q_sec=Q_sec, H_hes=H_hes, P_hes=P_hes, H_sec=H_sec, P_sec=P_sec, durum=durum, motor_kW=motor,
                dizel_kW=dizel, kw_hesap=kw, alt_kat=alt['ad'], p_alt_cal=p_alt_cal, p_alt_kap=p_alt_kap,
                bdv_sprinkler=bdv, H_jokey=math.ceil(PJ * 10.2), P_jokey=PJ, aralik=(p0, p1), p_max=k['sistem_max_bar'])


def _uzerinde(n, a, b):
    if abs(a[0] - b[0]) < 0.1:
        return abs(n[0] - a[0]) < 0.5 and min(a[1], b[1]) + 0.5 < n[1] < max(a[1], b[1]) - 0.5
    if abs(a[1] - b[1]) < 0.1:
        return abs(n[1] - a[1]) < 0.5 and min(a[0], b[0]) + 0.5 < n[0] < max(a[0], b[0]) - 0.5
    return False


# ======================================================================================  hidrolik
def hidrolik(D, k, kolonlar, T, dolaplar, spr_ozet, P):
    """eşzamanlı dolap debisi + en elverişsiz dolapta gerekli pompa basıncı; sprinkler ile birleşik pompa seçimi"""
    hp = P.get('hidrolik', {})
    C = hp.get('C', 120.0)
    katlar = D['katlar']
    pk = D['pompa']
    z_p = pk['kot_m'] + pk.get('eksen_m', 0.5)
    n_kat = len(katlar)
    top = max(katlar, key=lambda q: q['kot_m'])
    alt = min(katlar, key=lambda q: q['kot_m'])
    n_top = len(dolaplar) * n_kat
    ne = min(k['eszamanli'], n_top)
    Qd = ne * k['debi_lpm']
    Qs = spr_ozet['Qs']
    Lb = hp.get('besleme_L_m', 25.0)       # pompa -> kolon dibi yatay ana hat (girdiden)
    bdn = hp.get('besleme_dn', 100)
    satir = []
    en = None
    for d in dolaplar:
        kc = [x for x in kolonlar if x['ad'] == d['kolon']][0]
        # kolondan dolaba yatay boru boyu
        yol = nx.shortest_path(T, kc['p'], d['baglanti_uc'])
        Lh = sum(math.dist(a, b) for a, b in zip(yol[:-1], yol[1:])) / 100.0
        L50 = sum(math.dist(a, b) for a, b in zip(yol[:-1], yol[1:]) if T[a][b]['dn'] == k['besleme_dn']) / 100.0
        L32 = Lh - L50
        z = top['kot_m'] + k['montaj_m']
        Lk = z - z_p + 1.0                    # kolon boyu (+ dip bağlantısı)
        ek = 1.2                              # bağlantı parçaları için +%20 eşdeğer boy (kabul)
        dp_ana = hw_birim(Qs + Qd, bdn, C) * Lb * ek
        dp_kol = hw_birim(Qd, k['kolon_dn'], C) * Lk * ek
        dp_yat = hw_birim(Qd if L50 > 0 else k['debi_lpm'], k['besleme_dn'], C) * L50 * ek
        dp_bag = hw_birim(k['debi_lpm'], k['baglanti_dn'], C) * max(L32, 0.3) * ek + 0.30   # + dolap vanası (kabul)
        stat = (z - z_p) / 10.2
        Pp = k['basinc_bar'] + dp_ana + dp_kol + dp_yat + dp_bag + stat
        r = dict(no=d['no'], kolon=d['kolon'], kat=top['ad'], Lh=Lh, Lk=Lk, dp_ana=dp_ana, dp_kol=dp_kol, dp_yat=dp_yat,
                 dp_bag=dp_bag, stat=stat, Pp=Pp)
        satir.append(r)
        if en is None or Pp > en['Pp']:
            en = r
    # sprinkler (en üst kat) pompa basıncı: sprinkler hesabından (statik / besleme girdisi en üst kata göre ayarlı)
    # sprinkler pompa basıncı: sprinkler hesabı (statik / besleme girdisi en üst kata göre ayarlı); ana hat kaybı
    # sprinkler + dolap toplam debisiyle yeniden
    P_spr = spr_ozet['Pp'] - spr_ozet['dp_bes'] + hw_birim(Qs + Qd, bdn, C) * Lb
    Pp = max(P_spr, en['Pp'])
    H = Pp * 10.2
    Q = Qs + Qd
    # en alt kattaki dolapta kapalı vana basıncı (pompa kapama basıncı ≈ 1,15·H kabul)
    z_alt = alt['kot_m'] + k['montaj_m']
    sec = pompa_sec(Q * 0.06, Pp, k, z_p, katlar)
    # R2: seçilen pompa basıncıyla (çalışma basıncı 9-10 bar) en alt dolapta kapalı vana basıncı
    p_alt = k['kapama_kat'] * sec['P_sec'] - (z_alt - z_p) / 10.2
    v_kol = hiz(Qd, k['kolon_dn'])
    V = Q * k['sure_dk'] / 1000.0
    return dict(sec=sec, ne=ne, Qd=Qd, Qs=Qs, Q=Q, Q_m3h=Q * 0.06, P_spr=P_spr, P_dolap=en['Pp'], Pp=Pp, H=H, en=en, satir=satir,
                p_alt=p_alt, bdd=p_alt > k['p_max_bar'], v_kol=v_kol, V=V, sure=k['sure_dk'], z_p=z_p, Lb=Lb, bdn=bdn,
                yonetici='dolap' if en['Pp'] >= P_spr else 'sprinkler', n_kat=n_kat, n_dolap_bina=n_top)
