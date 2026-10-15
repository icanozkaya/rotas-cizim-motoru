"""yerden2 — PLANDA KOLLEKTÖR, KOMBİ VE DEVRE AYAKLARI (kullanıcı 15.10 (D): "kollektör bağlantıları yok").

Her daire için (10_YERDEN_ISITMA_BORULAMA §3, §4.2, §7.5; 05_ALGORITMALAR §3):
  1. Kollektör dolabı daire holünün (antre-kor.) duvarında, servis verdiği mahallerin ortasına en yakın yerde
     (kapı önü değil, ortak alan / dış duvar / balkon duvarı değil). Ağızlar 5 cm aralıklı (gidiş-dönüş çifti yan yana).
  2. Kombi yeri sıhhi plandaki kombi (proje/denemeler/sihhi2/sihhi_model.json daireler[].kombi) ile aynı nokta.
     Kombi–kollektör gidiş/dönüş hattı ızgara A* ile (mutfak tezgâhı / duvar dibi tercihli); geçtiği mahalin
     serpantini bu hattın dışında yeniden kurulur.
  3. Her devrenin gidiş ve dönüş ayağı: kollektör ağzı -> hol -> mahalin hol kapısı -> serpantin ucu. 5 cm ızgarada
     dik açılı A*; çizilen her ayak sonrakiler için engel (kesişme ve üst üste binme imkânsız, komşu ayak 5 cm).
     Ayaklar yalnız hol + kendi mahalinin kapısı + kendi mahali içinden geçer (merdiven, başka daire, ıslak olmayan
     başka mahal yok). Mahal içinde kapıdan uca yol yoksa kapıdan uca bir şerit (ayak koridoru) ayrılır ve mahalin
     serpantini bu şeridin dışında, uçlar kapı tarafında olacak şekilde yeniden kurulur.
  4. Hol serpantini ayaklardan sonra, ayak demetinin dışında kalan hol alanında (kollektöre bitişik parça) kurulur.
  5. Devre boyu = ayaklar + serpantin; > 80 m ise mahal bir devre fazla bölünerek daire yeniden çözülür.
"""
import heapq
import json
import math
import os

import numpy as np
import shapely
from shapely.geometry import Point, LineString, Polygon, box, MultiLineString
from shapely.ops import unary_union

import mimari_yi as MY
import serpantin as S
import tasarim as T

RES = 5.0            # ızgara (ayak aralığı)
DUVAR = 4.0          # ayak ekseni -> duvar yüzü en az
SERP_ARA = 7.6       # ayak ekseni -> serpantin ekseni en az (parmaklar arasına (7,5) giremez)
DONUS = 3.0          # dönüş cezası (adım) — müzakere
DONUS_TEMIZ = 10.0   # temizleme turunda dönüş cezası (düz, az kırılan demet)
UCUZ_DEMET = 1.0     # müzakerede başka çiftin yanı (kapalı)
YEDEK = 2            # kollektörün iki yanında yedek ağız çifti (yeniden kurulumda devre sayısı artarsa)
YASLA_KAZANC = 0.45  # duvar takibinde yaslanan adımın indirimi
HOL_PAY = 10.0       # hol serpantini ile ayak demeti arası ek pay (hol devresinin ayağına yer)
YANAS = 0.8          # duvara / başka ayağa yanaşık adım maliyeti (demet)
KOL_DERIN = 10.0     # kollektör dolabı derinliği (planda duvar önünde)
KOL_PAY = 10.0       # dolap ucu -> ilk ağız
STUB = 2             # ağızdan dik çıkış (düğüm) — başka ayak bu bölgeye giremez
MAX_L = 8000.0
DEBUG = False
SIHHI_MODEL = MY.KOK + '/proje/denemeler/sihhi2/sihhi_model.json'

L_KOL = 'ROTAS-ISITMA-KOLLEKTOR'
L_CIHAZ = 'ROTAS-ISITMA-CIHAZ'
L_G = 'ROTAS-ISITMA-GIDIS-BORU'
L_D = 'ROTAS-ISITMA-DONUS-BORU'
L_CAP = 'ROTAS-ISITMA-CAP'

DIRS = ((1, 0), (0, 1), (-1, 0), (0, -1))


def log(*a):
    print('[ayak]', *a, flush=True)


# ====================================================================== ızgara
class Izgara:
    def __init__(self, bbox, ox, oy):
        x0, y0, x1, y1 = bbox
        i0 = math.floor((x0 - ox) / RES)
        j0 = math.floor((y0 - oy) / RES)
        i1 = math.ceil((x1 - ox) / RES)
        j1 = math.ceil((y1 - oy) / RES)
        self.ox = ox + i0 * RES
        self.oy = oy + j0 * RES
        self.nx = i1 - i0 + 1
        self.ny = j1 - j0 + 1
        xs = self.ox + np.arange(self.nx) * RES
        ys = self.oy + np.arange(self.ny) * RES
        self.X, self.Y = np.meshgrid(xs, ys, indexing='ij')
        self.P = shapely.points(self.X, self.Y)

    def ij(self, x, y):
        return int(round((x - self.ox) / RES)), int(round((y - self.oy) / RES))

    def xy(self, i, j):
        return self.ox + i * RES, self.oy + j * RES

    def maske(self, g):
        if g is None or g.is_empty:
            return np.zeros((self.nx, self.ny), bool)
        shapely.prepare(g)
        return shapely.contains_xy(g, self.X, self.Y)

    def yakin(self, g, d):
        if g is None or g.is_empty:
            return np.zeros((self.nx, self.ny), bool)
        shapely.prepare(g)
        return shapely.dwithin(g, self.P, d)


def astar(G, serbest, baslar, hedefler, ucuz=None):
    """serbest: bool (nx, ny); baslar/hedefler: [(i, j)] -> düğüm listesi (bas..hedef) | None.
    Dik açılı; dönüş cezası; duvara/ayağa yanaşık adım ucuz (demet). ucuz: bool dizi, o düğümlerde adım 0,7."""
    nx, ny = G.nx, G.ny
    hs = set(hedefler)
    if not hs or not baslar:
        return None
    gi = [h[0] for h in hs]
    gj = [h[1] for h in hs]
    gx0, gx1, gy0, gy1 = min(gi), max(gi), min(gj), max(gj)
    fr = serbest

    def H(i, j):
        return YANAS * 0.85 * (max(gx0 - i, 0, i - gx1) + max(gy0 - j, 0, j - gy1))

    best = {}
    pq = []
    for (i, j) in baslar:
        if 0 <= i < nx and 0 <= j < ny:
            heapq.heappush(pq, (H(i, j), 0.0, i, j, -1, None))
    geldi = {}
    while pq:
        f, g, i, j, d, onc = heapq.heappop(pq)
        key = (i, j, d)
        if key in geldi:
            continue
        geldi[key] = onc
        if (i, j) in hs:
            yol = [(i, j)]
            k = onc
            while k is not None:
                yol.append((k[0], k[1]))
                k = geldi[k]
            return yol[::-1]
        for nd, (di, dj) in enumerate(DIRS):
            if d >= 0 and nd == (d + 2) % 4:
                continue
            a, b = i + di, j + dj
            if not (0 <= a < nx and 0 <= b < ny) or not fr[a, b]:
                continue
            # yanaşık: dik komşulardan biri dolu
            pi, pj = DIRS[(nd + 1) % 4]
            yan = False
            for s in (1, -1):
                u, v = a + s * pi, b + s * pj
                if not (0 <= u < nx and 0 <= v < ny) or not fr[u, v]:
                    yan = True
                    break
            c = YANAS if yan else 1.0
            if ucuz is not None and ucuz[a, b]:
                c = min(c, 0.7)
            if d >= 0 and nd != d:
                c += DONUS
            ng = g + c
            k2 = (a, b, nd)
            if best.get(k2, 1e18) <= ng:
                continue
            best[k2] = ng
            heapq.heappush(pq, (ng + H(a, b), ng, a, b, nd, key))
    return None


def astar_cift(G, fr, baslar, hedef_ok, yan, ucuz=None, ceza=None, kutu=None, bas_b=None, ucuz_d=0.7, donus=None,
               yasla=None):
    donus = DONUS if donus is None else donus
    """ÇİFT (gidiş+dönüş) yönlendirme: A hattı düğümlerde, B hattı A'nın 'yan' tarafında 1 düğüm (5 cm) ötede, paralel.
    yan=+1 sol, -1 sağ (hareket yönüne göre). fr: serbest dizi. baslar: A'nın başlangıç düğümleri.
    hedef_ok(i, j, d) -> A bu düğüme d yönüyle geldiğinde hedef mi. -> [(i, j)] A düğümleri | None.
    Koşullar: A ve B düğümleri serbest; dönüşte B'nin köşe düğümü serbest. Çift tek birim: aralarına kimse giremez."""
    nx, ny = G.nx, G.ny

    def Lv(d):
        di, dj = DIRS[d]
        return (-dj * yan, di * yan)

    def ok(i, j):
        return 0 <= i < nx and 0 <= j < ny and fr[i, j]

    if kutu is not None:
        gx0, gx1, gy0, gy1 = kutu

        def Hh(i, j):
            return 0.7 * (max(gx0 - i, 0, i - gx1) + max(gy0 - j, 0, j - gy1))
    else:
        def Hh(i, j):
            return 0.0
    pq = []
    best = {}
    for (i, j) in baslar:
        if not ok(i, j):
            continue
        for d in range(4):
            li, lj = Lv(d)
            if ok(i + li, j + lj) and (bas_b is None or (i + li, j + lj) in bas_b):
                heapq.heappush(pq, (Hh(i, j), 0.0, i, j, d, None))
    geldi = {}
    while pq:
        f, g, i, j, d, onc = heapq.heappop(pq)
        key = (i, j, d)
        if key in geldi:
            continue
        geldi[key] = onc
        if onc is not None and hedef_ok(i, j, d):
            yol = [(i, j)]
            k = onc
            while k is not None:
                yol.append((k[0], k[1]))
                k = geldi[k]
            yol = yol[::-1]
            return yol, d
        for nd in range(4):
            if nd == (d + 2) % 4:
                continue
            di, dj = DIRS[nd]
            a, b = i + di, j + dj
            if not ok(a, b):
                continue
            li, lj = Lv(nd)
            if not ok(a + li, b + lj):
                continue
            c = 1.0
            if nd != d:
                l0 = Lv(d)
                ci, cj = i + l0[0] + li, j + l0[1] + lj
                if not ok(ci, cj) or not ok(i + l0[0], j + l0[1]) or not ok(i + li, j + lj):
                    continue
                c += donus
            # demet: çiftin dış tarafı (A'nın karşı yanı ya da B'nin ötesi) dolu ise ucuz
            if yasla is None:
                if not ok(a - li, b - lj) or not ok(a + 2 * li, b + 2 * lj):
                    c -= (1.0 - YANAS)
            else:
                # yalnız belirtilen taraf (hareket yönüne göre sol=+1 / sağ=-1): duvar takibi
                ldi, ldj = -dj, di                        # sol birim
                ofs = (max(0, yan) + 1) if yasla > 0 else (min(0, yan) - 1)
                if not ok(a + ldi * ofs, b + ldj * ofs):
                    c -= YASLA_KAZANC
            if ucuz is not None and ucuz[a, b]:
                c = min(c, ucuz_d + (donus if nd != d else 0.0))
            if ceza is not None:
                c += ceza[a, b] + ceza[a + li, b + lj]
            ng = g + c
            k2 = (a, b, nd)
            if best.get(k2, 1e18) <= ng:
                continue
            best[k2] = ng
            heapq.heappush(pq, (ng + Hh(a, b), ng, a, b, nd, key))
    return None


def b_yolu(G, yol, yan, d_son):
    """A düğümlerinden B hattının köşe noktaları (mitre ofset)"""
    def Lv(d):
        di, dj = DIRS[d]
        return (-dj * yan, di * yan)

    def yon(p, q):
        return DIRS.index((q[0] - p[0], q[1] - p[1]))
    if len(yol) < 2:
        return None
    ds = [yon(yol[k], yol[k + 1]) for k in range(len(yol) - 1)]
    out = []
    l0 = Lv(ds[0])
    out.append((yol[0][0] + l0[0], yol[0][1] + l0[1]))
    for k in range(1, len(yol) - 1):
        if ds[k] != ds[k - 1]:
            a, b = Lv(ds[k - 1]), Lv(ds[k])
            out.append((yol[k][0] + a[0] + b[0], yol[k][1] + a[1] + b[1]))
    l1 = Lv(ds[-1])
    out.append((yol[-1][0] + l1[0], yol[-1][1] + l1[1]))
    return out


def dugumler(kose):
    """köşe düğümlerinden tüm ara düğümler"""
    out = [kose[0]]
    for a, b in zip(kose[:-1], kose[1:]):
        di = (b[0] > a[0]) - (b[0] < a[0])
        dj = (b[1] > a[1]) - (b[1] < a[1])
        x, y = a
        while (x, y) != tuple(b):
            x += di
            y += dj
            out.append((x, y))
    return out


def sade(pts):
    """ardışık doğrusal noktaları at"""
    out = []
    for p in pts:
        if out and abs(out[-1][0] - p[0]) < 1e-6 and abs(out[-1][1] - p[1]) < 1e-6:
            continue
        out.append(p)
    i = 1
    while i < len(out) - 1:
        a, b, c = out[i - 1], out[i], out[i + 1]
        if (abs(a[0] - b[0]) < 1e-6 and abs(b[0] - c[0]) < 1e-6) or (abs(a[1] - b[1]) < 1e-6 and abs(b[1] - c[1]) < 1e-6):
            out.pop(i)
        else:
            i += 1
    return out


def _parca(g):
    if g.is_empty:
        return []
    return list(g.geoms) if hasattr(g, 'geoms') else [g]


# ====================================================================== kombi (sıhhi modelden)
def kombi_yerleri(kat_off):
    """{daire_no(int): (x, y)} — sıhhi model koordinatı + kat ofseti (sıhhi model x - K.off yazar)"""
    try:
        m = json.load(open(SIHHI_MODEL))
    except Exception as ex:
        log('UYARI: sıhhi model okunamadı: %s' % ex)
        return {}
    out = {}
    for d in m.get('daireler', []):
        k = d.get('kombi')
        if not k:
            continue
        out[int(d['no'][1:])] = (k['x'] + kat_off.get(d['kat'], 0.0), k['y'], k.get('mahal', ''))
    return out


# ====================================================================== kollektör yeri
def _kenarlar(P):
    ext = list(P.simplify(1.0).exterior.coords)
    for a, b in zip(ext[:-1], ext[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1:
            continue
        if abs(a[0] - b[0]) > 0.5 and abs(a[1] - b[1]) > 0.5:
            continue
        yield a, b, L


def kollektor_yeri(K, hol, odalar, kapi_polys, n_agiz, kombi, yedek=0, sira=0):
    """-> dict(kutu, yuz (2 nokta), ic (birim normal), slotlar [(x, y)], merkez) | None"""
    P = hol['poly']
    gen = 2 * KOL_PAY + RES * (2 * n_agiz - 1)
    kapilar = unary_union(kapi_polys) if kapi_polys else Polygon()
    hedef = []
    for o in odalar:
        if o is hol:
            continue
        for c in o['tasarim']['devreler']:
            hedef.append(c['pts'][0][:2])
    best = None
    adaylar = []
    for a, b, L in _kenarlar(P):
        if L < gen + 10:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        for nxv, nyv in ((-uy, ux), (uy, -ux)):
            m = (a[0] + b[0]) / 2 + nxv * 6, (a[1] + b[1]) / 2 + nyv * 6
            if P.contains(Point(m)):
                break
        # dış taraf: aynı daire mahali (ortak alan, balkon, dış değil)
        t = gen / 2 + 5
        while t <= L - gen / 2 - 5 + 1e-6:
            cx, cy = a[0] + ux * t, a[1] + uy * t
            dis = Point(cx - nxv * 25, cy - nyv * 25)
            arka = next((r for r in K.rooms if r['poly'].buffer(3).contains(dis)), None)
            if arka is None or arka['tip'] in ('ortak', 'balkon') or arka.get('daire') != hol['daire']:
                t += 10
                continue
            k0 = (cx - ux * gen / 2, cy - uy * gen / 2)
            k1 = (cx + ux * gen / 2, cy + uy * gen / 2)
            kutu = Polygon([k0, k1, (k1[0] + nxv * KOL_DERIN, k1[1] + nyv * KOL_DERIN),
                            (k0[0] + nxv * KOL_DERIN, k0[1] + nyv * KOL_DERIN)])
            on = kutu.buffer(12, join_style=2).intersection(P)
            if on.intersects(kapilar) or not P.buffer(1).contains(kutu):
                t += 10
                continue
            # hol bu noktada en az 70 cm derin olmalı
            derin = LineString([(cx + nxv * 1, cy + nyv * 1), (cx + nxv * 300, cy + nyv * 300)]).intersection(P)
            dl = derin.geoms[0].length if hasattr(derin, 'geoms') else derin.length
            if dl < 70:
                t += 10
                continue
            puan = sum(abs(h[0] - cx) + abs(h[1] - cy) for h in hedef)
            if kombi:
                puan += 0.5 * (abs(kombi[0] - cx) + abs(kombi[1] - cy))
            adaylar.append((puan, kutu, (k0, k1), (nxv, nyv), (cx, cy), (ux, uy)))
            t += 10
    # birbirinden ≥ 120 cm uzak adaylar, puan sırasıyla; sira'ıncısı
    adaylar.sort(key=lambda q: q[0])
    secili = []
    for q in adaylar:
        if all(math.hypot(q[4][0] - r[4][0], q[4][1] - r[4][1]) >= 120 for r in secili):
            secili.append(q)
    if sira >= len(secili):
        return None
    best = secili[sira]
    _, kutu, yuz, ic, mer, u = best
    d0 = KOL_DERIN + RES          # ağız düğümü duvardan 15
    slotlar = []
    for s in range(2 * n_agiz + 4 * yedek):
        t = KOL_PAY + RES * (s - 2 * yedek)
        slotlar.append((yuz[0][0] + u[0] * t + ic[0] * d0, yuz[0][1] + u[1] * t + ic[1] * d0))
    return dict(kutu=kutu, yuz=yuz, ic=ic, u=u, merkez=mer, slotlar=slotlar, gen=gen)


# ====================================================================== mahal yeniden kurulumu
def yeniden_kur(o, ek, kapi, yasak, kapi_zorla=True, hedef_L=None, n_min=None):
    """mahal serpantinini ek engelin (ayak şeridi / kombi hattı / ayak demeti) dışında yeniden kurar.
    Islak hacimde duvar payı 7,5 / 6 / 5 / 4 / 3 / 2,5 denenir (yerden.islak_doldur ile aynı), en çok mahal içi boru."""
    r = o['r']
    eng = o['eng'] if ek is None or ek.is_empty else unary_union([o['eng'], ek])
    islak = o['tur'] == 'banyo'
    eski = (T.KAPI_ORAN, T.HEDEF_L, T.MAX_L)
    en = None
    try:
        if hedef_L is not None:
            T.HEDEF_L = min(T.HEDEF_L, hedef_L)
            T.MAX_L = min(T.MAX_L, hedef_L + 1000)
        for kn in ((7.5, 6.0, 5.0, 4.0, 3.0, 2.5) if islak else (None,)):
            H, R = MY.bolge(r, eng, kenar=kn)
            if R.is_empty or R.area < 900:
                continue
            d = T.oda_tasarla(r, H, R, kapi, yasak, False, islak=islak, kapi_zorla=kapi_zorla, n_min=n_min)
            if d is None:
                continue
            Lic = sum(S.cizgi(c['pts']).intersection(r['poly'].buffer(5)).length for c in d['devreler'])
            if en is None or Lic > en[0] + 5:
                en = (Lic, H, d)
            if islak and o.get('esik') and Lic >= o['esik']:
                break
    finally:
        T.KAPI_ORAN, T.HEDEF_L, T.MAX_L = eski
    if en is None:
        return None
    return dict(H=en[1], tasarim=en[2])


# ====================================================================== daire çözümü
class Daire:
    def __init__(self, K, dno, odalar, hol, kombi, diger_serp, yasak, kol_sira=0, sahte_hol=True):
        self.kol_sira = kol_sira
        self.sahte_hol_izin = sahte_hol
        self.K = K
        self.dno = dno
        self.odalar = odalar            # bu dairenin ısıtılan mahalleri (o dict'leri; o['r'], o['eng'] var)
        self.hol = hol
        self.kombi = kombi
        self.diger = diger_serp         # başka dairelerin serpantinleri (MultiLineString)
        self.yasak = yasak
        self.uyari = []

    # ---------------------------------------------------------------- kapılar
    def kapi_poly(self, o):
        """mahal o ile hol arasındaki kapı poligonu (ana kapıya en yakın)"""
        P, Hh = o['poly'], self.hol['poly']
        ad = []
        for q in list(self.K.kapilar) + list(getattr(self.K, 'acikliklar', [])):
            if P.distance(q) < 20 and Hh.distance(q) < 35:
                ad.append(q)
        if not ad:
            return self.aciklik(o)
        # duvar boşluğunu köprüleyen kapı (iki mahale de değen) önce; eşitlikte ana kapıya yakın olan
        ka = o.get('kapi')
        return min(ad, key=lambda q: (round(P.distance(q) + Hh.distance(q), 0),
                                      q.centroid.distance(Point(ka)) if ka else 0.0))

    def aciklik(self, o):
        """kapısız geçiş (duvar boşluğu): iki mahal arasındaki şeridin mimari çizgi kesmeyen parçası"""
        if not hasattr(self, '_acik'):
            self._acik = {}
        if id(o) in self._acik:
            return self._acik[id(o)]
        if not hasattr(self, '_mim'):
            gs = []
            for a in self.K.R:
                g = MY._geom(a)
                if g is not None and not g.is_empty:
                    gs.append(g)
            self._mim = unary_union(gs)
        P, Hh = o['poly'], self.hol['poly']
        # duvarsız ortak kenar (iki poligon ≤ 3 cm): açık geçiş
        ortak = P.buffer(3, join_style=2).intersection(Hh.buffer(3, join_style=2))
        if not ortak.is_empty:
            q = ortak.envelope
            x0, y0, x1, y1 = q.bounds
            if max(x1 - x0, y1 - y0) >= 60:
                self._acik[id(o)] = q
                log('D%d %s: duvarsız geçiş %s' % (self.dno, o.get('zon', o['ad']), [round(v) for v in q.bounds]))
                return q
        serit = P.buffer(30, join_style=2).intersection(Hh.buffer(30, join_style=2)).difference(
            unary_union([P, Hh]).buffer(-1))
        en = None
        if not serit.is_empty:
            bos = serit.difference(self._mim.intersection(serit.buffer(5)).buffer(2.0))
            for q in _parca(bos.buffer(0)):
                x0, y0, x1, y1 = q.bounds
                if min(x1 - x0, y1 - y0) < 8 or max(x1 - x0, y1 - y0) < 60:
                    continue
                if q.distance(P) > 3 or q.distance(Hh) > 3:
                    continue
                if en is None or q.area > en.area:
                    en = q
        self._acik[id(o)] = en
        if en is not None:
            log('D%d %s: kapısız geçiş %s' % (self.dno, o.get('zon', o['ad']), [round(v) for v in en.bounds]))
        return en

    def esik(self, kp, o):
        """kapı poligonu (kanat süpürme alanı) + duvar boşluğu (eşik): kapının dik kutusu hol tarafına uzatılır"""
        if kp is None:
            return None
        x0, y0, x1, y1 = kp.bounds
        Hh = self.hol['poly']
        en = None
        for ex in ((x0, y0 - 45, x1, y0), (x0, y1, x1, y1 + 45), (x0 - 45, y0, x0, y1), (x1, y0, x1 + 45, y1)):
            b = box(*ex)
            a = b.intersection(Hh).area
            if en is None or a > en[0]:
                en = (a, ex)
        ex = en[1]
        if ex[1] == y0 - 45 or ex[3] == y1 + 45:
            bx = box(x0 + 3, min(ex[1], y0), x1 - 3, max(ex[3], y1))
        else:
            bx = box(min(ex[0], x0), y0 + 3, max(ex[2], x1), y1 - 3)
        return unary_union([kp.buffer(1), bx.buffer(DUVAR + 1, join_style=2)])

    def hol_kapilari(self):
        out = []
        for q in list(self.K.kapilar) + list(getattr(self.K, 'acikliklar', [])):
            if self.hol['poly'].distance(q) < 20:
                out.append(q)
        return out

    # ---------------------------------------------------------------- serpantin engeli
    def serp_geo(self, haric=()):
        ls = []
        for o in self.odalar:
            if (o is self.hol and not getattr(self, 'hol_hazir', False)) or id(o) in haric:
                continue
            for c in o['tasarim']['devreler']:
                ls.append(S.cizgi(c['pts'], 4))
        return unary_union(ls + ([self.diger] if self.diger is not None and not self.diger.is_empty else []))

    def kirp_uc(self, c):
        """serpantinin iki ucundan 9 cm kırpılmış hali (uç düğümleri serbest kalsın)"""
        g = S.cizgi(c['pts'], 4)
        return g.difference(unary_union([Point(c['pts'][0][:2]).buffer(9), Point(c['pts'][-1][:2]).buffer(9)]))

    def coz(self):
        """-> dict(kollektor, kombi_hat, ayaklar) ; mahallerin tasarımlarını yerinde günceller"""
        n = sum(len(o['tasarim']['devreler']) for o in self.odalar)
        hk = self.hol_kapilari()
        kol = kollektor_yeri(self.K, self.hol, self.odalar, hk, n + 2, self.kombi, YEDEK, self.kol_sira)    # +kombi +hol; iki yanda yedek
        if kol is None:
            self.uyari.append('D%d: kollektör yeri bulunamadı' % self.dno)
            return None
        self.kol = kol
        # ızgara: ilk ağız düğümüne hizalı
        U = unary_union([o['poly'] for o in self.odalar])
        bb = U.buffer(80).bounds
        if self.kombi:
            bb = (min(bb[0], self.kombi[0] - 80), min(bb[1], self.kombi[1] - 80),
                  max(bb[2], self.kombi[0] + 80), max(bb[3], self.kombi[1] + 80))
        G = self.G = Izgara(bb, kol['slotlar'][0][0], kol['slotlar'][0][1])
        # kollektör dolabı ve ağız çıkış bölgesi engeli
        self.kol_engel = G.yakin(kol['kutu'], DUVAR)
        self.slot_ij = [G.ij(*p) for p in kol['slotlar']]
        ic = kol['ic']
        di, dj = int(round(ic[0])), int(round(ic[1]))
        self.slot_on = [(i + di * STUB, j + dj * STUB) for i, j in self.slot_ij]
        self.stub_dugum = set()
        for (i, j) in self.slot_ij:
            for s in range(STUB):
                self.stub_dugum.add((i + di * s, j + dj * s))
        self.dolu = np.zeros((G.nx, G.ny), bool)
        self.slot_sahip = {}
        # düzlemsel ağız ataması (kesişmesiz kirişler): hol kapıları hol sınırı boyunca kollektörün bir ucundan
        # öbürüne sıralanır, ağızlar aynı sırayla ters yönde verilir; hol devresine boş kalan uç
        self.planar_atama()
        for s_ in self.hol_uclar[0]:
            self.slot_sahip[s_] = 'hol'
        sonuc = dict(kollektor=kol, ayaklar=[], kombi_hat=None)
        # ---- 1) kombi hattı
        if self.kombi:
            kh = self.kombi_bagla()
            sonuc['kombi_hat'] = kh
        # ---- 2) mahaller: kapıdan uca erişim (gerekirse ayak şeridi + yeniden kurulum)
        for o in self.odalar:
            if o is self.hol:
                continue
            self.erisim_sagla(o)
        # ---- 3) ayaklar (hol hariç); yeniden kurulan mahallerin devreleri için atama tazelenir (kapı sırası aynı)
        ks = getattr(self, 'kombi_slot', None)
        self.planar_atama()
        if ks is not None and ks != self.kombi_slot:
            log('UYARI: D%d kombi ağzı değişti' % self.dno)
        for s_ in [k for k, v in self.slot_sahip.items() if v == 'hol']:
            del self.slot_sahip[s_]
        devs = [(o, c) for o in self.odalar if o is not self.hol for c in o['tasarim']['devreler']]
        if getattr(self, 'hol_sahte', None):
            devs.append((self.hol, self.hol_sahte))
            for s_ in self.hol_uclar[0]:
                self.slot_sahip.pop(s_, None)
        if getattr(self, 'kombi_hat', None):
            for q in self.kombi_dugum:
                self.dolu[q] = False
            for s_ in self.kombi_slot:
                self.slot_sahip.pop(s_, None)
            for s_ in self.kombi_hat['slot']:
                self.slot_sahip.pop(s_, None)
            devs.append((self.kombi_o, self.kombi_c))
        dolu_pre, sahip_pre = self.dolu.copy(), dict(self.slot_sahip)
        if not self._yerlestir_ayir(devs):
            return None
        # ---- 4) hol serpantini (demetin dışında kalan, ayrılmış kollektör ucuna bitişik parçada) + ayakları
        if not self.hol_kur() and getattr(self, '_hol_aday', None) and self._hol_erisilir(self._hol_aday):
            # hol devresi demetin içinde kaldı: en büyük boş parçadaki hol serpantini sabit engel olarak,
            # tüm çiftler hol devresiyle birlikte yeniden yönlendirilir
            y, ek = self._hol_aday
            o = self.hol
            o['H'], o['tasarim'], o['ek_eng'] = y['H'], y['tasarim'], ek
            self.hol_hazir = True
            self.uyari = [u for u in self.uyari if 'hol serpantini' not in u]
            log('D%d: hol devresi demetle kapalı -> hepsi hol serpantiniyle birlikte yeniden' % self.dno)
            import copy
            yedek = (list(self.ayaklar), self.dolu.copy(), dict(self.slot_sahip), copy.copy(self.kombi_hat),
                     list(self.uyari))
            self.dolu, self.slot_sahip = dolu_pre.copy(), dict(sahip_pre)
            devs2 = devs + [(o, c) for c in o['tasarim']['devreler']]
            n_uy = len(self.uyari)
            ok2 = self._yerlestir_ayir(devs2)
            tam = ok2 and len(self.ayaklar) == len(devs2) - (1 if getattr(self, 'kombi_c', None) and
                                                               any(c is self.kombi_c for _, c in devs2) else 0) \
                and len(self.uyari) == n_uy
            if not tam:
                # kısmi kalırsa ilk (hol devresiz, tam) çözüme dön
                self.ayaklar, self.dolu, self.slot_sahip, self.kombi_hat, self.uyari = yedek
                self.hol_hazir = False
                o['tasarim'] = dict(o['tasarim'], devreler=[])
        bagli = {id(a['c']) for a in self.ayaklar}
        for o in self.odalar:
            if o['tasarim']['devreler'] and all(id(c) in bagli for c in o['tasarim']['devreler']):
                ad = o.get('zon', o['ad'])
                self.uyari = [u for u in self.uyari if not (('%s:' % ad) in u and 'erişim yok' in u)]
        if not self.hol['tasarim']['devreler'] or not any(a['o'] is self.hol for a in self.ayaklar):
            if not any('hol' in u for u in self.uyari):
                self.uyari.append('D%d %s: hol devresi kurulamadı (hol ayak demetiyle ısınır)' % (self.dno, self.hol.get('zon', self.hol['ad'])))
            self.hol['tasarim'] = dict(self.hol['tasarim'], devreler=[])
        for s_ in [k for k, v in self.slot_sahip.items() if v == 'hol']:
            del self.slot_sahip[s_]
        sonuc['ayaklar'] = self.ayaklar
        return sonuc

    def _hol_erisilir(self, aday):
        """hol serpantini (aday) uçları, yalnız duvar + serpantinler engelken ağızlarla aynı bölgede mi"""
        from scipy import ndimage
        y, ek = aday
        o = self.hol
        eski = (o['H'], o['tasarim'])
        o['H'], o['tasarim'] = y['H'], y['tasarim']
        self.hol_hazir = True
        try:
            for c in o['tasarim']['devreler']:
                m = self.serbest(o) & ~self.kol_engel & ~self.engel(o, c)
                for q in self.slot_on:
                    m[q] = True
                lab, _ = ndimage.label(m)
                ls = {lab[q] for q in self.slot_on if lab[q]}
                lu = {lab[u] for u in self.uc_dugumleri(c['pts'][0][:2], m)} & {lab[u] for u in self.uc_dugumleri(c['pts'][-1][:2], m)}
                if not (ls & lu):
                    return False
            return True
        finally:
            o['H'], o['tasarim'] = eski
            self.hol_hazir = False

    def _yerlestir_ayir(self, devs):
        if not self.ayaklari_yerlestir(devs):
            return False
        hs = getattr(self, 'hol_sahte', None)
        if hs is not None:
            sa = next((a for a in self.ayaklar if a['c'] is hs), None)
            self.ayaklar = [a for a in self.ayaklar if a['c'] is not hs]
            if sa is not None:
                for q in sa.get('dugum', []):
                    self.dolu[q] = False
                self.hol_uclar = [(sa['g'][1], sa['d'][1])]
            self.uyari = [u for u in self.uyari if not (self.hol.get('zon', self.hol['ad']) + ':' in u and 'bağlanamadı' in u)]
            for s_ in self.hol_uclar[0]:
                self.slot_sahip[s_] = 'hol'
        if getattr(self, 'kombi_hat', None):
            ka = next((a for a in self.ayaklar if a['c'] is self.kombi_c), None)
            if ka is None:
                # son çare: öbürleri sabitken kombi çifti herhangi bir boş ağız çiftine
                c = self.kombi_c
                bos = [s_ for s_ in range(len(self.slot_ij)) if s_ not in self.slot_sahip]
                r = self.cift(c['pts'][0][:2], c['pts'][-1][:2], self.kombi_taban() & ~self.dolu, bos, None, 'y', 'y')
                if r is not None:
                    ka = dict(o=self.kombi_o, c=c, g=(r['g'], r['slot'][0]), d=(r['d'], r['slot'][1]), dugum=r['dugum'])
                    self.uyari = [u for u in self.uyari if 'KOMBİ' not in u]
            if ka is None:
                self.uyari.append('D%d: kombi hattı kollektöre bağlanamadı' % self.dno)
                self.kombi_hat = None
                return True
            self.ayaklar = [a for a in self.ayaklar if a['c'] is not self.kombi_c]
            kx, ky = self.kombi[0], self.kombi[1]
            self.kombi_hat = dict(gidis=[(kx, ky)] + ka['g'][0], donus=[(kx, ky)] + ka['d'][0],
                                  slot=(ka['g'][1], ka['d'][1]))
            for s_ in self.kombi_hat['slot']:
                self.slot_sahip[s_] = 'kombi'
        for s_ in self.hol_uclar[0]:
            if s_ not in self.slot_sahip:
                self.slot_sahip[s_] = 'hol'
        return True

    # ---------------------------------------------------------------- düzlemsel atama
    def planar_atama(self, ters=False):
        Hb = self.hol['poly'].exterior
        P = Hb.length
        k0, k1 = self.kol['yuz']
        p0, p1 = Hb.project(Point(k0)), Hb.project(Point(k1))
        yon = 1 if ((p0 - p1) % P) > P / 2 else -1

        def ileri(pt):
            return ((Hb.project(Point(pt)) - p1) * yon) % P
        N = len(self.slot_ij)
        term = []
        for o in self.odalar:
            if o is self.hol:
                continue
            kp = self.kapi_poly(o)
            if kp is None:
                continue
            es = self.esik(kp, o).centroid
            t = ileri((es.x, es.y))
            sira_o = o.get('ayak_sira') or []
            for c in o['tasarim']['devreler']:
                m = ((c['pts'][0][0] + c['pts'][-1][0]) / 2, (c['pts'][0][1] + c['pts'][-1][1]) / 2)
                ix = sira_o.index(id(c)) if id(c) in sira_o else None
                term.append((t, ileri(m), 'dev', o, c, ix))
        if self.kombi:
            mut = [o for o in self.odalar if o['tur'] == 'mutfak' and self.kapi_poly(o) is not None]
            if mut:
                kp = self.kapi_poly(mut[0])
                es = self.esik(kp, mut[0]).centroid
                es_p = self.esik(kp, mut[0])
                t2 = ileri(self.kombi[:2])
                if getattr(self, 'kombi_hat', None):
                    # kombi hattının kapı eşiğini geçtiği nokta (mutfak devresiyle sırası buna göre)
                    kes = LineString(self.kombi_hat['gidis']).intersection(es_p)
                    if not kes.is_empty:
                        t2 = ileri((kes.centroid.x, kes.centroid.y))
                term.append((ileri((es.x, es.y)), t2, 'kombi', getattr(self, 'kombi_o', None),
                             getattr(self, 'kombi_c', None), None))
        gen = self.kol['gen']
        tmin = min((q[0] for q in term), default=P)
        tmax = max((q[0] for q in term), default=0.0)
        on_yon = ((P - gen - tmax) >= tmin) != ters
        # aynı kapıdaki devreler: mahal içinde önce girilmesi gereken (erişim sırası) yönlendirme sırasında önce
        kombi_t = {round(q[0], 1) for q in term if q[2] == 'kombi'}

        def anahtar(q):
            if q[5] is not None and round(q[0], 1) not in kombi_t:
                return (q[0], q[5] if on_yon else -q[5])
            return (q[0], q[1])
        term.sort(key=anahtar)
        term = [q[:5] for q in term]
        # yönlendirme yönü: kirişler bir uçtan başlayarak duvara / bir önceki kirişe yaslanır (duvar takibi);
        # boş hol alanı son kirişin öbür yanında, kollektörün öbür ucunda kalır -> hol devresi oraya.
        A1 = term[0][0] if term else P
        A0 = (P - gen - term[-1][0]) if term else P
        ileri_yon = (A0 >= A1) != ters          # True: k1 ucundan başla, hol k0 ucunda
        # hol devresi: kapısız en uzun sınır yayına; uzak uçtaki yay değilse o yaya sahte uç (20 cm içeri) konur ve
        # sahte çift de demetle birlikte yönlendirilir (hol alanına koridor kalır)
        ts = [q[0] for q in term]
        sinir = [0.0] + ts + [P - gen]
        yaylar = [(sinir[k + 1] - sinir[k], k) for k in range(len(sinir) - 1)]
        L_, kmax = max(yaylar)
        uzak_uc = (len(sinir) - 2) if ileri_yon else 0
        self.hol_sahte = None
        if kmax == uzak_uc or not term or not getattr(self, 'sahte_hol_izin', True):
            hol_kayit = (0.0, 0.0, 'hol', self.hol, None)
            if ileri_yon:
                term.append(hol_kayit)
            else:
                term.insert(0, hol_kayit)
        else:
            hol_t = (sinir[kmax] + sinir[kmax + 1]) / 2
            pt = Hb.interpolate((p1 + yon * hol_t) % P)
            q1 = Hb.interpolate((p1 + yon * hol_t + 1.0) % P)
            tx, ty = q1.x - pt.x, q1.y - pt.y
            tl = math.hypot(tx, ty) or 1.0
            nx_, ny_ = -ty / tl, tx / tl
            if not self.hol['poly'].contains(Point(pt.x + nx_ * 10, pt.y + ny_ * 10)):
                nx_, ny_ = -nx_, -ny_
            if abs(nx_) >= abs(ny_):
                nx_, ny_ = (1.0 if nx_ > 0 else -1.0), 0.0
            else:
                nx_, ny_ = 0.0, (1.0 if ny_ > 0 else -1.0)
            E0 = self.G.xy(*self.G.ij(pt.x + nx_ * 25, pt.y + ny_ * 25))
            tx_, ty_ = -ny_, nx_
            E1 = (E0[0] + tx_ * 10, E0[1] + ty_ * 10)
            self.hol_sahte = dict(pts=[(E0[0], E0[1], 0.0), (E0[0] + nx_ * 5, E0[1] + ny_ * 5, 0.0),
                                       (E1[0] + nx_ * 5, E1[1] + ny_ * 5, 0.0), (E1[0], E1[1], 0.0)],
                                  sahte=True, L=0.0)
            term.insert(kmax, (hol_t, 0.0, 'hol', self.hol, self.hol_sahte))
        # yaslanma tarafı: kapıdan ağıza yürürken başlangıç ucu (k1 ya da k0) tarafındaki duvarlar
        ccw = Hb.is_ccw
        sol = ((yon == 1) == ccw)
        self.yasla = (1 if sol else -1) if ileri_yon else (-1 if sol else 1)
        self.ileri_yon = ileri_yon
        self.atama = {}
        self.sira = []
        self.hol_uclar = []
        sabit = getattr(self, 'kombi_slot', None) if getattr(self, 'kombi_hat', None) else None
        ik = next((k for k, q in enumerate(term) if q[2] == 'kombi'), None)
        # geçerli ağız çiftleri (ağız ve ön düğümü holde, duvar içinde değil)
        if not hasattr(self, '_gecerli'):
            Am = self.G.maske(self.hol['poly'].buffer(-DUVAR, join_style=2))
            self._gecerli = [Am[self.slot_ij[s_]] and Am[self.slot_on[s_]] for s_ in range(N)]
        gc = self._gecerli
        ust = [(a, a - 1) for a in range(N - 1, 0, -2)]          # yukarıdan aşağı çiftler
        if sabit is not None and ik is not None:
            hi, lo = max(sabit), min(sabit)
            yukari = [(a, a - 1) for a in range(hi + 2, N, 2) if a < N and gc[a] and gc[a - 1]]
            asagi = [(a, a - 1) for a in range(lo - 1, 0, -2) if gc[a] and gc[a - 1]]
            bas = yukari[:ik][::-1]
            if len(bas) < ik:
                bas = [(hi + 2 * (ik - k), hi + 2 * (ik - k) - 1) for k in range(ik)]
            son = asagi[:len(term) - ik - 1]
            ciftler = bas + [tuple(sabit)] + son
        else:
            gecerli = [pr for pr in ust if gc[pr[0]] and gc[pr[1]]]
            # kullanılacak çiftler: geçerlilerin ortası (yedekler iki uçta kalır)
            fazla = max(0, len(gecerli) - len(term))
            ciftler = gecerli[fazla // 2: fazla // 2 + len(term)]
        if len(ciftler) < len(term):
            log('UYARI: D%d geçerli ağız sayısı yetmedi' % self.dno)
            ciftler = list(ciftler) + [(0, 1)] * (len(term) - len(ciftler))
        if DEBUG:
            log('atama', [(round(t), round(t2), tur, o.get('zon', o['ad']) if o else '-', pr) for (t, t2, tur, o, c), pr in zip(term, ciftler)], 'P', round(P), 'yon', yon)
        for (t, t2, tur, o, c), pair in zip(term, ciftler):
            if tur == 'kombi':
                self.kombi_slot = pair
                if c is not None:
                    self.atama[id(c)] = pair
                    self.sira.append((o, c))
            elif tur == 'hol':
                self.hol_uclar = [pair]
                if c is not None:
                    self.atama[id(c)] = pair
                    self.sira.append((o, c))
            else:
                self.atama[id(c)] = pair
                self.sira.append((o, c))
        if not ileri_yon:
            self.sira = self.sira[::-1]

    # ---------------------------------------------------------------- serbest maske
    def serbest(self, o, ek_haric=()):
        """devrenin mahali o için serbest düğümler (hol + kapı + mahal; serpantinler, dolu ayaklar engel)"""
        G = self.G
        key = id(o)
        if not hasattr(self, '_alan'):
            self._alan = {}
        if key not in self._alan:
            kp = self.kapi_poly(o)
            parcalar = [self.hol['poly']] + ([self.esik(kp, o)] if kp is not None else []) + [o['poly']]
            A = unary_union(parcalar).buffer(-DUVAR, join_style=2)
            self._alan[key] = (G.maske(A), kp)
        m, kp = self._alan[key]
        return m

    def engel(self, o, c):
        """serpantin engelleri: diğer tüm serpantinler + bu devrenin uçları kırpılmış hali"""
        G = self.G
        ls = []
        for o2 in self.odalar:
            if o2 is self.hol and not getattr(self, 'hol_hazir', False):
                continue
            for c2 in o2['tasarim']['devreler']:
                ls.append(self.kirp_uc(c2) if c2 is c else S.cizgi(c2['pts'], 4))
        if self.diger is not None and not self.diger.is_empty:
            ls.append(self.diger)
        return G.yakin(unary_union(ls), SERP_ARA)

    def uc_dugumleri(self, E, serb, r=7.6):
        G = self.G
        i0, j0 = G.ij(E[0], E[1])
        k = int(math.ceil(r / RES))
        out = []
        for i in range(i0 - k, i0 + k + 1):
            for j in range(j0 - k, j0 + k + 1):
                if 0 <= i < G.nx and 0 <= j < G.ny and serb[i, j]:
                    x, y = G.xy(i, j)
                    if abs(x - E[0]) <= r and abs(y - E[1]) <= r:
                        out.append((i, j))
        return out

    # ---------------------------------------------------------------- ortak: çift yerleştirme
    def cift_yol(self, E0, E1, ser, hedef, dgel=None, ucuz=None, yon0=None, yon1=None, son_ek=None, ceza=None, donus=None,
                 yasla=None):
        """uçlardan hedef düğüm kümesine çift yol (A uç E0'dan, B A'nın yanında). -> (L, ga, gb, yolA, kB) | None
        hedef: düğüm kümesi; A ve B'nin ikisi de kümede bitmeli (dgel verilirse varış yönü o)."""
        G = self.G
        en = None
        for yan in (1, -1):
            bas = self.uc_dugumleri(E0, ser)
            if not bas:
                continue

            def hedef_ok(i, j, d, yan=yan):
                if (dgel is not None and d != dgel) or (i, j) not in hedef:
                    return False
                di, dj = DIRS[d]
                return (i - dj * yan, j + di * yan) in hedef
            hi = [h[0] for h in hedef]
            hj = [h[1] for h in hedef]
            dE = math.hypot(E0[0] - E1[0], E0[1] - E1[1])
            uzak = dE > 20.0                      # basamaklı beslemede uçlar ayrık (ör. 41 cm)
            bas_b = set(self.uc_dugumleri(E1, ser, dE + 2.6 if uzak else 7.6))
            r = astar_cift(G, ser, bas, hedef_ok, yan, ucuz, ceza, (min(hi), max(hi), min(hj), max(hj)) if hedef else None,
                           bas_b, 0.7 if ceza is None else UCUZ_DEMET, donus, yasla)
            if r is None:
                continue
            yol, dson = r
            bk = b_yolu(G, yol, yan, dson)
            pa = [G.xy(*q) for q in sade(yol)]
            pb = [G.xy(*q) for q in sade(bk)]
            ga = sade(self._uc_bag(E0, pa[0], yon0) + pa[1:] + (son_ek(yol[-1]) if son_ek else []))
            gb = sade(self._uc_bag(E1, pb[0], yon1) + pb[1:] + (son_ek(bk[-1]) if son_ek else []))
            LA, LB = LineString(ga), LineString(gb)
            if uzak:
                # uzun uç bağlantısı serpantinlere değmesin (uç noktası hariç)
                jog = LineString(gb[:3]).difference(Point(E1).buffer(3.5))
                if jog.distance(self.serp_geo()) < 3.0:
                    continue
            if LA.distance(LB) < 3.0 or not LA.is_simple or not LB.is_simple:
                if DEBUG:
                    log('cift red', yan, round(LA.distance(LB), 2), LA.is_simple, LB.is_simple, ga[:4], gb[:4])
                continue
            L = LA.length + LB.length
            if ceza is not None:
                L += RES * sum(ceza[q] for q in dugumler(sade(yol)) + dugumler(sade(bk))
                               if 0 <= q[0] < G.nx and 0 <= q[1] < G.ny)
            if en is None or L < en[0]:
                en = (L, ga, gb, yol, bk)
        return en

    def cift(self, E0, E1, ser_taban, slot_izin, ucuz=None, yon0=None, yon1=None, ceza=None, isaretle=True, donus=None,
             yasla=None):
        """E0 (gidiş ucu) ve E1 (dönüş ucu) -> komşu iki serbest ağız. -> dict(g=pts, d=pts, slot=(sg, sd)) | None
        yon0/yon1: uçtaki serpantin doğrultusu ('x' | 'y') — uç bağlantısının köşesi bu doğrultuda."""
        G = self.G
        ic = self.kol['ic']
        dgel = DIRS.index((-int(round(ic[0])), -int(round(ic[1]))))       # ağza varış yönü (duvara doğru)
        sahipsiz = set(s for s in slot_izin if s not in self.slot_sahip)
        on_idx = {self.slot_on[s]: s for s in sahipsiz}
        ser = ser_taban & ~self.dolu
        for (i, j) in self.stub_dugum:
            ser[i, j] = False
        for q in on_idx:
            ser[q] = True
        en = self.cift_yol(E0, E1, ser, set(on_idx), dgel, ucuz, yon0, yon1,
                           son_ek=lambda q: self._stub_pts(on_idx[q]), ceza=ceza, donus=donus, yasla=yasla)
        if en is None:
            return None
        L, ga, gb, yol, bk = en
        sa, sb = on_idx[yol[-1]], on_idx[bk[-1]]
        nod = [q for q in dugumler(sade(yol)) + dugumler(sade(bk)) if 0 <= q[0] < G.nx and 0 <= q[1] < G.ny]
        if isaretle:
            for q in nod:
                self.dolu[q] = True
        return dict(g=ga, d=gb, slot=(sa, sb), dugum=nod)

    def cift_c(self, c, ser_taban, slot_izin, ucuz=None, **kw):
        """devre için çift yönlendirme; mahal içi kısmı (kapı eşiğine kadar) erişim denetiminde sabitlenmişse
        hol kısmı eşikten başlar, sonra birleştirilir"""
        oa = c.get('oda_ayak')
        if not oa:
            return self.cift(c['pts'][0][:2], c['pts'][-1][:2], ser_taban, slot_izin, ucuz,
                             self.uc_yonu(c, True), self.uc_yonu(c, False), **kw)
        G = self.G
        ser = ser_taban.copy()
        for q in oa['dugum']:
            if 0 <= q[0] < G.nx and 0 <= q[1] < G.ny:
                ser[q] = False
        a0, b0 = oa['ga'][-1], oa['gb'][-1]
        for q in (G.ij(*a0), G.ij(*b0)):
            ser[q] = True
        r = self.cift(a0, b0, ser, slot_izin, ucuz, oa['yon_a'], oa['yon_b'], **kw)
        if r is None:
            return None
        r = dict(r)
        r['g'] = sade(oa['ga'][:-1] + r['g'])
        r['d'] = sade(oa['gb'][:-1] + r['d'])
        r['dugum'] = list(r['dugum']) + [q for q in oa['dugum'] if 0 <= q[0] < G.nx and 0 <= q[1] < G.ny]
        if kw.get('isaretle', True):
            for q in oa['dugum']:
                if 0 <= q[0] < G.nx and 0 <= q[1] < G.ny:
                    self.dolu[q] = True
        return r

    def _uc_bag(self, E, p, yon):
        """uç E -> ızgara noktası p: dik köşe (uç doğrultusunda önce)"""
        if abs(p[0] - E[0]) < 0.3 or abs(p[1] - E[1]) < 0.3:
            return [(E[0], E[1]), p]
        kose = (p[0], E[1]) if yon == 'x' else (E[0], p[1])
        return [(E[0], E[1]), kose, p]

    @staticmethod
    def uc_yonu(c, ilk):
        p = c['pts']
        a, b = (p[0], p[1]) if ilk else (p[-1], p[-2])
        return 'x' if abs(b[0] - a[0]) >= abs(b[1] - a[1]) else 'y'

    # ---------------------------------------------------------------- 1) kombi
    def kombi_bagla(self):
        G = self.G
        kx, ky = self.kombi[0], self.kombi[1]
        mut = [o for o in self.odalar if o['tur'] == 'mutfak']
        parcalar = [self.hol['poly']]
        transit = []
        for o in mut:
            kp = self.kapi_poly(o)
            if kp is not None:
                parcalar += [o['poly'], self.esik(kp, o)]
                transit.append(o)
        kombi_oda = next((r for r in self.K.rooms if r['poly'].buffer(2).contains(Point(kx, ky))), None)
        if kombi_oda is not None:
            parcalar.append(kombi_oda['poly'])
        A = unary_union(parcalar)
        Pk = Point(kx, ky)
        hedef_alan = unary_union([o['poly'] for o in transit] + [self.hol['poly']])
        if not hedef_alan.buffer(2).contains(Pk):
            from shapely.ops import nearest_points
            q = nearest_points(hedef_alan.buffer(-20, join_style=2), Pk)[0]
            gecis = LineString([(kx, ky), (q.x, ky), (q.x, q.y)]) if abs(q.x - kx) > abs(q.y - ky) else \
                LineString([(kx, ky), (kx, q.y), (q.x, q.y)])
            A = unary_union([A, gecis.buffer(14, cap_style=2)])
        A = A.buffer(-DUVAR, join_style=2).union(Pk.buffer(16))
        serb = G.maske(A) & ~self.engel_transit(transit) & ~self.kol_engel
        if getattr(self, 'kombi_slot', None) is None:
            # mutfak hole kapısız: kombi çifti kollektörün kombiye yakın ucuna
            N = len(self.slot_ij)
            d0 = Point(self.kol['slotlar'][2 * YEDEK]).distance(Pk)
            d1 = Point(self.kol['slotlar'][N - 1 - 2 * YEDEK]).distance(Pk)
            self.kombi_slot = (2 * YEDEK + 1, 2 * YEDEK) if d0 <= d1 else (N - 2 * YEDEK - 1, N - 2 * YEDEK - 2)
        sl = list(self.kombi_slot)
        ucuz = np.zeros_like(serb)
        for o in transit:
            # tezgâh / dolap altı (ısıtılmayan tefriş) ucuz: kombi hattı mutfağı tezgâh boyunca geçer
            if o.get('eng') is not None and not o['eng'].is_empty:
                ucuz |= G.maske(o['eng'].buffer(12).intersection(o['poly']))
        i0, j0 = G.ij(kx, ky)
        E0, E1 = G.xy(i0 + 1, j0), G.xy(i0 - 1, j0)
        for e in (E0, E1):
            serb[G.ij(*e)] = True
        # kapı / geçiş eşiğinin mutfak devresi uçlarına yakın yarısı kombi hattına kapalı (mutfak devresi
        # kapıdan o yarıdan çıkar; kombi öbür yarıdan geçer)
        ceza = None
        serb_tum = serb.copy()
        for o in transit:
            kp = self.kapi_poly(o)
            uc = [c['pts'][k][:2] for c in o['tasarim']['devreler'] for k in (0, -1)]
            if kp is None or not uc:
                continue
            es = self.esik(kp, o)
            x0, y0, x1, y1 = es.bounds
            mx = sum(u[0] for u in uc) / len(uc)
            my = sum(u[1] for u in uc) / len(uc)
            kx0, ky0, kx1, ky1 = kp.bounds
            dikey_uzanti = (y1 - y0) > (ky1 - ky0) + 10       # eşik hol tarafına dikey uzanıyorsa duvar yatay
            if dikey_uzanti or ((x1 - x0) >= (y1 - y0) and not (x1 - x0) > (kx1 - kx0) + 10):
                # kombi uçların geniş kalan tarafından geçer (uçlardan 12 cm öte); öbür taraf kapalı
                if kx < mx:                                   # kombi solda: sol taraftan geçer
                    yarim = box(mx - 12, y0 - 60, x1 + 30, y1 + 60)
                else:
                    yarim = box(x0 - 30, y0 - 60, mx + 12, y1 + 60)
            else:
                if ky < my:
                    yarim = box(x0 - 60, my - 12, x1 + 60, y1 + 30)
                else:
                    yarim = box(x0 - 60, y0 - 30, x1 + 60, my + 12)
            serb &= ~G.maske(yarim.intersection(es.buffer(6, join_style=2)))
        r = None
        for sb in (serb, serb_tum):
            r = self.cift(E0, E1, sb, sl, ucuz, 'y', 'y', ceza=ceza)
            if r is None:
                r = self.cift(E1, E0, sb, sl, ucuz, 'y', 'y', ceza=ceza)
                if r is not None:
                    r = dict(g=r['d'], d=r['g'], slot=r['slot'][::-1], dugum=r['dugum'])
            if r is not None:
                break
        if r is None:
            self.uyari.append('D%d: kombi hattı kurulamadı' % self.dno)
            return None
        for s in r['slot']:
            self.slot_sahip[s] = 'kombi'
        hatlar = [[(kx, ky)] + r['g'], [(kx, ky)] + r['d']]
        hg = unary_union([LineString(h) for h in hatlar])
        for o in transit:
            if not hg.intersects(o['poly']):
                continue
            ek = hg.buffer(4, cap_style=2).intersection(o['poly'])
            # mutfak devresinin uçları kapının kombi hattından uzak ucunda (kombi kapının öbür yanından geçer)
            kapi_m = o['kapi']
            kp = self.kapi_poly(o)
            if kp is not None:
                es = self.esik(kp, o)
                kes = hg.intersection(es)
                if not kes.is_empty:
                    kc = kes.centroid
                    ex0, ey0, ex1, ey1 = es.bounds
                    adaylar = [(ex0 + 15, (ey0 + ey1) / 2), (ex1 - 15, (ey0 + ey1) / 2),
                               ((ex0 + ex1) / 2, ey0 + 15), ((ex0 + ex1) / 2, ey1 - 15)]
                    kapi_m = max(adaylar, key=lambda q: math.hypot(q[0] - kc.x, q[1] - kc.y))
                    kapi_m = (Point(kapi_m).buffer(1).centroid.x, Point(kapi_m).buffer(1).centroid.y)
            y = yeniden_kur(o, ek, kapi_m, self.yasak, kapi_zorla=True)
            if y is None:
                self.uyari.append('D%d: %s kombi hattı dışında kurulamadı' % (self.dno, o.get('zon', o['ad'])))
                continue
            o['H'], o['tasarim'] = y['H'], y['tasarim']
            o['ek_eng'] = ek
        self.kombi_hat = dict(gidis=hatlar[0], donus=hatlar[1], slot=r['slot'])
        # müzakerede kombi çifti de yeniden yönlendirilir (mutfak şeridi içinde kalır)
        self.kombi_o = dict(ad='kombi', zon='KOMBİ', transit=transit)
        self.kombi_c = dict(pts=[(E0[0], E0[1], 0.0), (E0[0], E0[1] + 5, 0.0), (E1[0], E1[1] + 5, 0.0),
                                 (E1[0], E1[1], 0.0)], kombi=True, L=0.0)
        self.kombi_taban0 = G.maske(A) & ~self.kol_engel
        for e in (E0, E1):
            self.kombi_taban0[G.ij(*e)] = True
        self.kombi_ucuz = ucuz
        self.kombi_dugum = r['dugum']
        return self.kombi_hat

    def kombi_taban(self):
        """kombi çiftinin serbest alanı: yeniden kurulmuş mutfak dahil tüm serpantinler engel"""
        return self.kombi_taban0 & ~self.G.yakin(self.serp_geo(), SERP_ARA)

    def engel_transit(self, transit):
        haric = {id(o) for o in transit}
        return self.G.yakin(self.serp_geo(haric), SERP_ARA)

    def _stub_pts(self, s):
        """ağız ön düğümünden ağıza ve dolap yüzüne"""
        G = self.G
        i, j = self.slot_ij[s]
        ic = self.kol['ic']
        x, y = G.xy(i, j)
        return [(x, y), (x - ic[0] * RES, y - ic[1] * RES)]

    # ---------------------------------------------------------------- 2) mahal içi erişim
    def _oda_ici_serbest(self, o, c=None):
        G = self.G
        kp = self.kapi_poly(o)
        A = unary_union([o['poly']] + ([self.esik(kp, o)] if kp is not None else [])).buffer(-DUVAR, join_style=2)
        m = G.maske(A)
        ls = []
        for c2 in o['tasarim']['devreler']:
            ls.append(self.kirp_uc(c2))
        m &= ~G.yakin(unary_union(ls), SERP_ARA)
        m &= ~self.dolu                       # kombi hattı (sabit)
        return m, kp

    def _erisim_var(self, o):
        """mahalin TÜM devrelerinin uç çiftleri birlikte (birbirini kesmeden) kapı eşiğine ulaşabiliyor mu.
        Her devre için yalnız kendi uçları açık; öbür devrelerin serpantini (uçları dahil) engel."""
        G = self.G
        kp = self.kapi_poly(o)
        if kp is None:
            return False
        es = self.esik(kp, o)
        A = unary_union([o['poly'], es]).buffer(-DUVAR, join_style=2)
        taban = G.maske(A) & ~self.dolu
        devs = o['tasarim']['devreler']
        ser_c = {}
        for c in devs:
            ls = [self.kirp_uc(c2) if c2 is c else S.cizgi(c2['pts'], 4) for c2 in devs]
            ser_c[id(c)] = taban & ~G.yakin(unary_union(ls), SERP_ARA)
        Hm = G.maske(self.hol['poly'].buffer(-DUVAR, join_style=2))
        kap = set(tuple(p) for p in np.argwhere(G.maske(es) & taban & Hm))
        if not kap:
            kap = set(tuple(p) for p in np.argwhere(G.maske(es) & taban & ~G.maske(o['poly'].buffer(-2))))
        if not kap:
            return False
        denemeler = [(sira, ys) for sira in (devs, devs[::-1]) for ys in ((None, 1, -1) if len(devs) > 1 else (None,))]
        for sira, ys in denemeler:
            kul = np.zeros_like(taban)
            tamam = True
            for c in sira:
                mm = ser_c[id(c)] & ~kul
                r = self.cift_yol(c['pts'][0][:2], c['pts'][-1][:2], mm, kap, None, None,
                                  self.uc_yonu(c, True), self.uc_yonu(c, False), yasla=ys)
                if r is None:
                    tamam = False
                    break
                for q in dugumler(sade(r[3])) + dugumler(sade(r[4])):
                    if 0 <= q[0] < G.nx and 0 <= q[1] < G.ny:
                        kul[q] = True
            if tamam:
                o['ayak_sira'] = [id(c) for c in sira]       # kapıdan ilk girilmesi gereken devre önce
                return True
        return False

    def besleme_kirp(self, o, t=15.0):
        """besleme ucunu (parmaklara dik ilk segment) yol boyunca t cm kısalt (basamaklı beslemede köşeden dönerek):
        köşedeki öbür uca (parmak ucu) kapı tarafından yol açılır. Uygulanamazsa False."""
        yeni = []
        for c in o['tasarim']['devreler']:
            p = [list(q) for q in c['pts']]
            tamam = False
            for ilk in (True, False):
                q = p if ilk else p[::-1]
                a, b = q[0], q[1]
                if abs(b[0] - a[0]) >= abs(b[1] - a[1]):
                    continue                                  # yatay uç = parmak, kırpılmaz
                kalan = t
                k = 0
                while k < len(q) - 1:
                    bulge = q[k][2] if ilk else q[k + 1][2]
                    if abs(bulge) > 1e-9:
                        break
                    L = math.hypot(q[k + 1][0] - q[k][0], q[k + 1][1] - q[k][1])
                    if L > kalan + 8.0:
                        f = kalan / L
                        nx_ = q[k][0] + (q[k + 1][0] - q[k][0]) * f
                        ny_ = q[k][1] + (q[k + 1][1] - q[k][1]) * f
                        q = [[nx_, ny_, 0.0]] + q[k + 1:]
                        tamam = True
                        break
                    kalan -= L
                    k += 1
                if tamam:
                    p = q if ilk else q[::-1]
                    break
            if not tamam:
                return False
            yeni.append([tuple(v) for v in p])
        for c, p in zip(o['tasarim']['devreler'], yeni):
            c['pts'] = p
            c['L'] = S.uzunluk(p)
        return True

    def _dene_kirp(self, o):
        if self._erisim_var(o):
            return True
        import copy
        yedek = copy.deepcopy(o['tasarim']['devreler'])
        for t in (15.0, 30.0):
            if self.besleme_kirp(o, t) and self._erisim_var(o):
                log('D%d %s: besleme ucu %.0f cm kısaltıldı (köşedeki uca kapıdan yol)' % (self.dno, o.get('zon', o['ad']), t))
                return True
            o['tasarim']['devreler'] = copy.deepcopy(yedek)
        return False

    def erisim_sagla(self, o):
        if self._dene_kirp(o):
            return True
        kp = self.kapi_poly(o)
        if kp is None:
            self.uyari.append('D%d %s: hol kapısı yok' % (self.dno, o.get('zon', o['ad'])))
            return False
        G = self.G
        nd = len(o['tasarim']['devreler'])
        genis = RES * (2 * nd - 1) / 2.0 + S.KENAR + 1.0
        kc = kp.centroid
        # kapı ile mahal arasındaki eşik orta noktası
        for deneme in range(3):
            # yalnız duvarlara göre, kapıdan mevcut uçlara duvar dibi şerit
            A = unary_union([o['poly'], self.esik(kp, o)]).buffer(-DUVAR, join_style=2)
            m = G.maske(A)
            kap = [tuple(p) for p in np.argwhere(G.maske(self.esik(kp, o)) & m & ~G.maske(o['poly'].buffer(-2)))]
            c0 = o['tasarim']['devreler'][0]
            hedef = self.uc_dugumleri(c0['pts'][0], m) + self.uc_dugumleri(c0['pts'][-1], m)
            if not kap or not hedef:
                break
            yol = astar(G, m, kap, hedef)
            if yol is None:
                break
            serit = LineString([G.xy(*p) for p in yol] + [c0['pts'][0][:2]]) if len(yol) > 1 else Point(G.xy(*yol[0]))
            ek = serit.buffer(genis, cap_style=2, join_style=2).intersection(o['poly'])
            onceki = o.get('ek_eng')
            ek_t = ek if onceki is None else unary_union([onceki, ek])
            y = yeniden_kur(o, ek_t, (kc.x, kc.y), self.yasak, kapi_zorla=True)
            if y is None:
                break
            o['H'], o['tasarim'] = y['H'], y['tasarim']
            o['ek_eng'] = ek_t
            if self._dene_kirp(o):
                log('D%d %s: kapıdan uca ayak şeridi açıldı (deneme %d)' % (self.dno, o.get('zon', o['ad']), deneme + 1))
                return True
        # son çare: uçlar kapıya en yakın köşede (şeritsiz)
        y = yeniden_kur(o, o.get('ek_eng'), (kc.x, kc.y), self.yasak, kapi_zorla=True)
        if y is not None:
            o['H'], o['tasarim'] = y['H'], y['tasarim']
            if self._dene_kirp(o):
                return True
        self.uyari.append('D%d %s: kapıdan serpantin ucuna erişim yok' % (self.dno, o.get('zon', o['ad'])))
        return False

    # ---------------------------------------------------------------- 3) ayaklar
    def ayaklari_yerlestir(self, devs):
        """Müzakereli yönlendirme (PathFinder): her devre çifti tek birim; başka çiftin düğümü önce yasak değil
        cezalı; çakışan düğümlerin tarihsel cezası artırılarak her turda yeniden yönlendirilir. Çakışma kalmayınca
        biter. Böylece sıralamaya bağlı tıkanma (bir demetin ağızları kapatması) çözülür."""
        G = self.G
        dolu0 = self.dolu.copy()
        sahip0 = dict(self.slot_sahip)
        taban = {}
        for o, c in devs:
            if c.get('kombi'):
                taban[id(c)] = self.kombi_taban() & ~dolu0
            else:
                taban[id(c)] = self.serbest(o) & ~self.kol_engel & ~self.engel(o, c) & ~dolu0
        izin = lambda c: list(self.atama[id(c)]) if id(c) in self.atama else list(range(len(self.slot_ij)))  # noqa
        # 1) düzlemsel sırayla tek tek (sabit engel): önce tercih edilen yön, olmazsa ters yön
        for ters in (False, True):
            if ters:
                sahip_h = {k: v for k, v in sahip0.items() if v != 'hol'}
                self.planar_atama(ters=True)
                for s_ in self.hol_uclar[0]:
                    sahip_h[s_] = 'hol'
                sahip0 = sahip_h
            sira0 = [oc for oc in self.sira if any(oc[1] is c for _, c in devs)]
            sira0 += [oc for oc in devs if not any(oc[1] is c for _, c in sira0)]
            self.dolu, self.slot_sahip = dolu0.copy(), dict(sahip0)
            rota = {}
            i = 0
            takas = set()
            while i < len(sira0):
                o, c = sira0[i]
                r = self.cift_c(c, taban[id(c)], izin(c), None,
                              yasla=self.yasla)
                if r is None:
                    # aynı mahalin bir önceki devresiyle sıra (ve ağız çifti) takası
                    if i > 0 and sira0[i - 1][0] is o and (id(c), i) not in takas:
                        takas.add((id(c), i))
                        o2, c2 = sira0[i - 1]
                        r2 = rota.pop(id(c2))
                        for q in r2['dugum']:
                            self.dolu[q] = False
                        for s_ in r2['slot']:
                            self.slot_sahip.pop(s_, None)
                        self.atama[id(c)], self.atama[id(c2)] = self.atama[id(c2)], self.atama[id(c)]
                        sira0[i - 1], sira0[i] = sira0[i], sira0[i - 1]
                        i -= 1
                        continue
                    break
                r['o'], r['c'] = o, c
                rota[id(c)] = r
                for s_ in r['slot']:
                    self.slot_sahip[s_] = (o.get('zon', o['ad']), c)
                i += 1
            if len(rota) == len(devs):
                log('D%d: ayaklar düzlemsel sırayla (duvar takibi%s) yerleşti' % (self.dno, ', ters yön' if ters else ''))
                self.ayaklar = [dict(o=r['o'], c=r['c'], g=(r['g'], r['slot'][0]), d=(r['d'], r['slot'][1]),
                                     dugum=r['dugum']) for r in (rota[id(c)] for o, c in devs)]
                return True
            log('D%d: düzlemsel sıra (%s) tıkandı: %s' % (self.dno, 'ters' if ters else 'ileri', o.get('zon', o['ad'])))
            if DEBUG == 'sira' or (DEBUG == 'sira1' and not ters) or (DEBUG == 'sira2' and ters):
                self.ayaklar = [dict(o=r['o'], c=r['c'], g=(r['g'], 0), d=(r['d'], 0)) for r in rota.values()]
                return False
        sira = sira0
        self.dolu, self.slot_sahip = dolu0.copy(), dict(sahip0)
        occ = np.zeros((G.nx, G.ny), np.int32)
        tarih = np.zeros((G.nx, G.ny), float)
        rota = {}
        pf = 0.6
        mer = self.kol['merkez']
        sira = sorted(devs, key=lambda oc: -(abs(oc[1]['pts'][0][0] - mer[0]) + abs(oc[1]['pts'][0][1] - mer[1])))
        for tur in range(40):
            for o, c in sira:
                k = id(c)
                if k in rota:
                    if tur > 0 and not any(occ[q] > 1 for q in rota[k]['dugum']):
                        continue
                    for q in rota[k]['dugum']:
                        occ[q] -= 1
                    del rota[k]
                ceza = tarih + pf * occ
                # demet: başka çiftin hemen yanındaki (5 cm) düğümler ucuz -> sıkı, paralel demet
                dol = occ > 0
                yan = np.zeros_like(dol)
                yan[1:, :] |= dol[:-1, :]
                yan[:-1, :] |= dol[1:, :]
                yan[:, 1:] |= dol[:, :-1]
                yan[:, :-1] |= dol[:, 1:]
                yan &= ~dol
                self.slot_sahip = dict(sahip0)
                r = self.cift_c(c, taban[k], izin(c), None,
                              ceza=ceza, isaretle=False)
                if r is None:
                    if DEBUG and o is self.hol:
                        m_ = taban[k]
                        log('hol çift yok: uç düğüm', len(self.uc_dugumleri(c['pts'][0][:2], m_)), len(self.uc_dugumleri(c['pts'][-1][:2], m_)),
                            'izin', izin(c)[:6], 'sahip', {k_: v for k_, v in self.slot_sahip.items() if isinstance(v, str)})
                    if DEBUG:
                        r0 = self.cift_c(c, taban[k], range(len(self.slot_ij)), None,
                                       isaretle=False)
                        log('yol yok', o.get('zon', o['ad']), tur, 'cezasız:', r0 is not None)
                    continue
                r['o'], r['c'] = o, c
                rota[k] = r
                for q in r['dugum']:
                    occ[q] += 1
            asiri = occ > 1
            eksik = [oc for oc in devs if id(oc[1]) not in rota]
            if not asiri.any() and not eksik:
                break
            tarih[asiri] += 1.0
            pf *= 1.5
            if eksik:
                # yer bulamayan devre önce
                sira = eksik + [oc for oc in sira if oc not in eksik]
        self.slot_sahip = dict(sahip0)
        self.dolu = dolu0
        if (occ > 1).any() or len(rota) < len(devs):
            log('D%d: müzakere %d turda çözülemedi (çakışan düğüm %d, eksik %s)' % (
                self.dno, tur + 1, int((occ > 1).sum()), [o.get('zon', o['ad']) for o, c in devs if id(c) not in rota]))
            if DEBUG:
                for q in np.argwhere(occ > 1):
                    log('çakışma', G.xy(*q), [r['o'].get('zon', r['o']['ad']) for r in rota.values() if tuple(q) in r['dugum']])
            if DEBUG == 'mz':
                self.ayaklar = [dict(o=r['o'], c=r['c'], g=(r['g'], 0), d=(r['d'], 0)) for r in rota.values()]
                return False
            # kısmi çözüm: çakışan çiftler çıkarılır, sonra sabit engelle tek tek yeniden denenir
            while (occ > 1).any():
                say_ = {k: sum(1 for q in r['dugum'] if occ[q] > 1) for k, r in rota.items()}
                k = max(say_, key=say_.get)
                for q in rota[k]['dugum']:
                    occ[q] -= 1
                del rota[k]
            self.dolu = dolu0.copy()
            self.slot_sahip = dict(sahip0)
            for r in rota.values():
                for q in r['dugum']:
                    self.dolu[q] = True
                for s_ in r['slot']:
                    self.slot_sahip[s_] = (r['o'].get('zon', r['o']['ad']), r['c'])
            for o, c in devs:
                if id(c) in rota:
                    continue
                r = self.cift_c(c, taban[id(c)], list(range(len(self.slot_ij))), None)
                if r is None:
                    self.uyari.append('D%d %s: devre ayağı kollektöre bağlanamadı' % (self.dno, o.get('zon', o['ad'])))
                    continue
                r['o'], r['c'] = o, c
                rota[id(c)] = r
                for s_ in r['slot']:
                    self.slot_sahip[s_] = (o.get('zon', o['ad']), c)
            self.ayaklar = [dict(o=r['o'], c=r['c'], g=(r['g'], r['slot'][0]), d=(r['d'], r['slot'][1]),
                                 dugum=r['dugum']) for r in (rota[id(c)] for o, c in devs if id(c) in rota)]
            log('D%d: kısmi çözüm %d/%d' % (self.dno, len(rota), len(devs)))
            return True
        log('D%d: ayaklar %d turda yerleşti (müzakere)' % (self.dno, tur + 1))
        self.dolu = dolu0.copy()
        for o, c in devs:
            r = rota[id(c)]
            for s_ in r['slot']:
                self.slot_sahip[s_] = (o.get('zon', o['ad']), c)
            for q in r['dugum']:
                self.dolu[q] = True
        return self._temizle_bitir(devs, rota, taban, izin, sira)

    def _temizle_bitir(self, devs, rota, taban, izin, sira):
        # temizleme: her çift, ötekiler sabit engelken yüksek dönüş cezasıyla yeniden yönlendirilir (duvara / komşu
        # çifte yaslanan düz demet). Yeni yol bulunamazsa eskisi kalır; geçerlilik korunur.
        for gecis in range(3):
            degisen = 0
            for o, c in sira:
                k = id(c)
                r = rota[k]
                for q in r['dugum']:
                    self.dolu[q] = False
                for s_ in r['slot']:
                    self.slot_sahip.pop(s_, None)
                r2 = self.cift_c(c, taban[k], izin(c), None,
                               isaretle=False, donus=DONUS_TEMIZ)
                if r2 is not None and r2['dugum'] != r['dugum']:
                    r2['o'], r2['c'] = o, c
                    rota[k] = r = r2
                    degisen += 1
                for q in r['dugum']:
                    self.dolu[q] = True
                for s_ in r['slot']:
                    self.slot_sahip[s_] = (o.get('zon', o['ad']), c)
            if not degisen:
                break
        self.ayaklar = []
        for o, c in devs:
            r = rota[id(c)]
            self.ayaklar.append(dict(o=o, c=c, g=(r['g'], r['slot'][0]), d=(r['d'], r['slot'][1]), dugum=r['dugum']))
        return True

    def _devre_ayak(self, o, c, ser_ek=None, slot_izin=None):
        ser_t = self.serbest(o) & ~self.kol_engel & ~self.engel(o, c)
        if ser_ek is not None:
            ser_t &= ser_ek
        izin = list(range(len(self.slot_ij))) if slot_izin is None else slot_izin
        r = self.cift_c(c, ser_t, izin, None)
        if r is None:
            return None
        for s in r['slot']:
            self.slot_sahip[s] = (o.get('zon', o['ad']), c)
        return dict(o=o, c=c, g=(r['g'], r['slot'][0]), d=(r['d'], r['slot'][1]))

    # ---------------------------------------------------------------- 4) hol
    def _devre_ayak_hepsi(self, o):
        eklenen = []
        for c in o['tasarim']['devreler']:
            r = self._devre_ayak(o, c)
            if r is None:
                return False
            eklenen.append(r)
        self.ayaklar = self.ayaklar + eklenen
        return True

    def hol_kur(self):
        """hol serpantini: ayak demeti + kombi hattı + kollektör dışında kalan alanın, hol için ayrılmış uç ağız
        çiftine bitişik parçasında; uçlar o ağızlara yakın köşede. İki uç denenir, borusu uzun olan alınır."""
        o = self.hol
        G = self.G
        hat = [LineString(a['g'][0]) for a in self.ayaklar] + [LineString(a['d'][0]) for a in self.ayaklar]
        if getattr(self, 'kombi_hat', None):
            hat += [LineString(self.kombi_hat['gidis']), LineString(self.kombi_hat['donus'])]
        demet = unary_union(hat).buffer(RES / 2 + 1.0, cap_style=2, join_style=2) if hat else Polygon()
        # kollektör önü (ağız çıkışları, 30 cm) serpantine kapalı: hol devresinin ayağı ağzına buradan girer
        ic = self.kol['ic']
        k0, k1 = self.kol['yuz']
        on = Polygon([k0, k1, (k1[0] + ic[0] * 40, k1[1] + ic[1] * 40), (k0[0] + ic[0] * 40, k0[1] + ic[1] * 40)])
        bos = o['poly'].difference(unary_union([demet, self.kol['kutu'].buffer(4, join_style=2),
                                                on.buffer(2 * RES * YEDEK + 10, join_style=2).intersection(on.buffer(200).envelope)
                                                if False else on]))
        eski = (o['H'], o['tasarim'], o.get('ek_eng'))
        en = None
        uc = self.hol_uclar[0]
        ps = [G.xy(*self.slot_on[s_]) for s_ in uc]
        Pu = Point((ps[0][0] + ps[1][0]) / 2, (ps[0][1] + ps[1][1]) / 2)
        if getattr(self, 'hol_sahte', None):
            Pu = Point(self.hol_sahte['pts'][0][:2])
        parcalar = sorted([q for q in _parca(bos.buffer(0)) if q.area > 900], key=lambda g: -g.area)
        # önce ayrılmış ağızlara bitişik parça; sonra büyükten küçüğe diğer parçalar (boş herhangi bir ağız)
        aday = [q for q in parcalar if q.distance(Pu) < 30] + [q for q in parcalar if q.distance(Pu) >= 30]
        bos_slot = [s_ for s_ in range(len(self.slot_ij)) if s_ not in self.slot_sahip or self.slot_sahip[s_] == 'hol']
        for q in aday[:5]:
            Mk = Point(self.kol['merkez'])
            from shapely.ops import nearest_points
            Ps = nearest_points(q, Pu if q.distance(Pu) < 30 else Mk)[0]
            ek = o['poly'].difference(q).buffer(0)
            y = yeniden_kur(o, ek, (Ps.x, Ps.y), self.yasak, kapi_zorla=5.0)
            if DEBUG:
                log('hol tasarım', y is not None, round(q.area), round(q.distance(Pu)))
            if y is None:
                continue
            if getattr(self, '_hol_aday', None) is None or \
                    sum(c['L'] for c in y['tasarim']['devreler']) > sum(c['L'] for c in self._hol_aday[0]['tasarim']['devreler']):
                self._hol_aday = (y, ek)
            o['H'], o['tasarim'], o['ek_eng'] = y['H'], y['tasarim'], ek
            dolu0, sahip0 = self.dolu.copy(), dict(self.slot_sahip)
            for s_ in uc:
                self.slot_sahip.pop(s_, None)
            eklenen = []
            ok = True
            for c in o['tasarim']['devreler']:
                r = self._devre_ayak(o, c, slot_izin=list(uc))
                if r is None:
                    r = self._devre_ayak(o, c, slot_izin=bos_slot)
                if r is None:
                    ok = False
                    break
                eklenen.append(r)
            L = sum(c['L'] for c in o['tasarim']['devreler'])
            if ok and (en is None or L > en[0]):
                en = (L, y, ek, eklenen, self.dolu.copy(), dict(self.slot_sahip))
            self.dolu, self.slot_sahip = dolu0, sahip0
            o['H'], o['tasarim'], o['ek_eng'] = eski
            if en is not None and en[0] > 2500:
                break
        if en is None:
            self.uyari.append('D%d %s: hol serpantini ayak demeti dışında kurulamadı / bağlanamadı' % (
                self.dno, o.get('zon', o['ad'])))
            o['tasarim'] = dict(o['tasarim'], devreler=[])
            return False
        L, y, ek, eklenen, dolu, sahip = en
        o['H'], o['tasarim'], o['ek_eng'] = y['H'], y['tasarim'], ek
        self.dolu, self.slot_sahip = dolu, sahip
        self.ayaklar = self.ayaklar + eklenen
        return True

    def _erisim_hol(self, o):
        return True
