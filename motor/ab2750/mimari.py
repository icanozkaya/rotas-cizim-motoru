# -*- coding: utf-8 -*-
"""2750 ada 7 parsel (Adapazarı Karapınar) A-B blok — mimari tanıma.
Girdi: mimari DWG -> dwg2dxf -> dxfparse düz liste (cp1254).  Çıktı: kat bazında mahal poligonları, daireler, armatürler,
kapı / pencere, betonarme (kolon/perde) poligonları, dış duvar segmentleri.  Birim cm, mimari koordinatı.
"""
import math, pickle, re, sys, os, json
import numpy as np
import cv2
from scipy import ndimage as ndi
from skimage.segmentation import watershed
from shapely.geometry import Polygon, Point, LineString, box, MultiPolygon
from shapely.ops import unary_union

FL_PKL = '/tmp/claude-0/ab/mim_fl.pkl'
RES = 2.0
# katlar: (blok, kat, x0, x1, y0, y1, kot(m), sıra)
KATLAR = [
    ('B', 'Z', 25300, 30210, -27560, -26000, 0.75),
    ('B', '1', 31300, 36210, -27560, -26000, 3.75),
    ('B', '2', 37300, 42210, -27560, -26000, 6.75),
    ('A', 'B', 16930, 24760, -35300, -32250, -2.20),
    ('A', 'Z', 25590, 33410, -35300, -32250, 0.80),
    ('A', '1', 34245, 42065, -35300, -32250, 3.80),
    ('A', '2', 42900, 50720, -35300, -32250, 6.80),
]
DUVAR_KATMAN = {'rtm-duv tugla', 'rtm-tas_betonarme', 'rtm-sıva', 'rtm-pen-ahsap', 'rtm-cam', 'rtm-kapı-ahsap',
                'rtm-door-sac', 'rtm-door-accesorry', 'rtm-beton', 'rtm-ylt-sürme', 'sbl-merdiven'}
ISLAK = ('BANYO', 'WC', 'DUŞ', 'MUTFAK', 'LAVABO')


def temiz(s):
    s = re.sub(r'\\[A-Za-z][^;]*;', '', s)
    s = s.replace('{', '').replace('}', '').replace('\\P', ' ')
    return s.strip()


_FL = None
def fl():
    global _FL
    if _FL is None:
        _FL = pickle.load(open(FL_PKL, 'rb'))
    return _FL


def kat_kayit(blok, kat):
    for k in KATLAR:
        if k[0] == blok and k[1] == kat:
            return k
    raise KeyError((blok, kat))


def icinde(p, k, pad=0):
    return k[2] - pad <= p[0] <= k[3] + pad and k[4] - pad <= p[1] <= k[5] + pad


def kayitlar(k):
    out = []
    for r in fl():
        if r[0] == 'T':
            if icinde(r[2][0], k):
                out.append(r)
        elif r[0] == 'C':
            if icinde(r[2][:2], k):
                out.append(r)
        elif r[0] in 'LP':
            pts = r[2]
            if any(icinde(p, k) for p in pts):
                out.append(r)
    return out


def _cember(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-6:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy, math.hypot(ax - ux, ay - uy)


class Kat:
    def __init__(self, blok, kat):
        self.k = kat_kayit(blok, kat)
        self.blok, self.kat = blok, kat
        self.kot = self.k[6]
        self.R = kayitlar(self.k)
        self._yazilar()
        self._betonarme()
        self._mahaller()
        self._daireler()
        self._armaturler()
        self._acikliklar()

    # ---------------------------------------------------------------- yazılar
    def _yazilar(self):
        self.adlar, self.m2, self.daire_yazi = [], [], []
        for r in self.R:
            if r[0] != 'T':
                continue
            (x, y), s, h = r[2]
            s = temiz(s)
            if r[1] == 'rtm-mhl-yazı-adı':
                m = re.match(r'DA[İI]RE\s*(\d+)', s)
                if m:
                    self.daire_yazi.append((x, y, int(m.group(1))))
                elif s and not s.startswith('%') and s != 'EĞİM':
                    self.adlar.append((x, y, s, h))
            elif r[1] == 'rtm-mhl-yazı-m2':
                m = re.search(r'(\d+[.,]\d+)\s*m', s)
                if m:
                    self.m2.append((x, y, float(m.group(1).replace(',', '.'))))

    def _betonarme(self):
        polys = []
        for r in self.R:
            if r[1] == 'rtm-tas_betonarme' and r[0] == 'P':
                p = r[2]
                if len(p) >= 4 and math.dist(p[0], p[-1]) < 1:
                    g = Polygon(p)
                    if g.is_valid and g.area > 100:
                        polys.append(g)
        self.betonarme = polys

    # ---------------------------------------------------------------- mahaller (raster + watershed)
    def _mahaller(self):
        k = self.k
        x0, x1, y0, y1 = k[2], k[3], k[4], k[5]
        W, H = int((x1 - x0) / RES) + 2, int((y1 - y0) / RES) + 2
        img = np.zeros((H, W), np.uint8)
        self.kapilar = []
        px = lambda p: (int(round((p[0] - x0) / RES)), int(round((y1 - p[1]) / RES)))
        for r in self.R:
            if r[1] not in DUVAR_KATMAN:
                continue
            if r[1] in ('rtm-kapı-ahsap', 'rtm-door-sac', 'rtm-door-accesorry'):
                # kapı kanadı / açılım yayı mahal bölmez: yalnız kısa kasa parçaları
                pts = r[2] if r[0] == 'P' else (list(r[2]) if r[0] == 'L' else None)
                if pts is None:
                    continue
                Ls = sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:]))
                if r[0] == 'P' and len(pts) >= 5 and 40 < Ls < 260:
                    cc = _cember(pts[0], pts[len(pts) // 2], pts[-1])
                    if cc and 40 <= cc[2] <= 130:
                        c = (cc[0], cc[1])
                        self.kapilar.append(dict(mentese=c, uc1=tuple(pts[0]), uc2=tuple(pts[-1]), r=cc[2], katman=r[1]))
                        cv2.line(img, px(c), px(pts[0]), 255, 2)
                        cv2.line(img, px(c), px(pts[-1]), 255, 2)
                    continue
                if Ls > 16 or len(pts) > 5:
                    continue
            if r[0] == 'L':
                cv2.line(img, px(r[2][0]), px(r[2][1]), 255, 2)
            elif r[0] == 'P':
                pts = np.array([px(p) for p in r[2]], np.int32)
                cv2.polylines(img, [pts], False, 255, 2)
            elif r[0] == 'C':
                cx, cy, rr = r[2]
                cv2.circle(img, px((cx, cy)), max(1, int(rr / RES)), 255, 1)
        for g in self.betonarme:
            pts = np.array([px(p) for p in g.exterior.coords], np.int32)
            cv2.fillPoly(img, [pts], 255)
        self.img_duvar = img
        # kapılar açık (kanat/yay ve kapalı-konum çizgisi yok) raster: daire ataması için
        acik = np.zeros_like(img)
        for r in self.R:
            if r[1] not in DUVAR_KATMAN or r[1] in ('rtm-kapı-ahsap', 'rtm-door-sac', 'rtm-door-accesorry'):
                continue
            if r[0] == 'L':
                cv2.line(acik, px(r[2][0]), px(r[2][1]), 255, 2)
            elif r[0] == 'P':
                cv2.polylines(acik, [np.array([px(p) for p in r[2]], np.int32)], False, 255, 2)
        for g in self.betonarme:
            cv2.fillPoly(acik, [np.array([px(p) for p in g.exterior.coords], np.int32)], 255)
        self.img_acik = acik
        self.px = px
        free = img == 0
        lab, n = ndi.label(free)
        # dış (kenara değen) bölgeler
        kenar = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
        tohum = np.zeros_like(lab, np.int32)
        seeds = []
        for i, (x, y, s, h) in enumerate(self.adlar):
            c, rr = px((x, y))
            if 0 <= rr < H and 0 <= c < W:
                L = lab[rr, c]
                if L == 0:   # yazı duvar çizgisine denk: yakın serbest pikseli ara
                    for d in range(1, 12):
                        win = lab[max(0, rr - d):rr + d + 1, max(0, c - d):c + d + 1]
                        nz = win[win > 0]
                        if nz.size:
                            L = np.bincount(nz).argmax(); break
                if L and L not in kenar:
                    seeds.append((i, L, rr, c))
                    cv2.circle(tohum, (c, rr), 3, i + 1, -1)
        tohum[~free] = 0
        # her bileşende tohumlar: tek tohum -> bileşenin tamamı; çok tohum -> jeodezik ağırlıklı Voronoi
        # (ağırlıklar mimari m² oranını tutturacak şekilde ayarlanır)
        from skimage.graph import MCP_Geometric
        regs = np.zeros_like(lab, np.int32)
        bylab = {}
        for sd in seeds:
            bylab.setdefault(sd[1], []).append(sd)
        def hedef_m2(i):
            x, y, s, h = self.adlar[i]
            a = min(self.m2, key=lambda t: (t[0] - x) ** 2 + (t[1] - y) ** 2) if self.m2 else None
            return a[2] if a and math.hypot(a[0] - x, a[1] - y) < 80 else None
        for L, ss in bylab.items():
            comp = lab == L
            if len(ss) == 1:
                regs[comp] = ss[0][0] + 1
                continue
            ys, xs = np.where(comp)
            r0, r1, c0, c1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            sub = comp[r0:r1, c0:c1]
            cost = np.where(sub, 1.0, np.inf)
            D = []
            for i, L2, rr, cc in ss:
                m = MCP_Geometric(cost)
                d, _ = m.find_costs([(rr - r0, cc - c0)])
                D.append(d)
            D = np.array(D)
            w = np.zeros(len(ss))
            hed = [hedef_m2(i) for i, *_ in ss]
            for it in range(60):
                asg = np.argmin(D - w[:, None, None], axis=0)
                if None in hed:
                    break
                cur = np.array([((asg == j) & sub).sum() * RES * RES / 1e4 for j in range(len(ss))])
                tot_h = sum(hed); tot_c = cur.sum()
                tgt = np.array(hed) / tot_h * tot_c
                err = tgt - cur
                if np.abs(err).max() < 0.15:
                    break
                w += 0.6 * err / np.maximum(cur, 0.5) * 60
            for j, (i, *_ ) in enumerate(ss):
                regs[r0:r1, c0:c1][(asg == j) & sub] = i + 1
        self.mahal = []
        for i, L, rr, c in seeds:
            m = (regs == i + 1).astype(np.uint8)
            cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not cs:
                continue
            cmax = max(cs, key=cv2.contourArea)
            cmax = cv2.approxPolyDP(cmax, 1.5, True)
            pts = [(x0 + q[0][0] * RES, y1 - q[0][1] * RES) for q in cmax]
            if len(pts) < 3:
                continue
            g = Polygon(pts).buffer(0)
            if g.geom_type != 'Polygon':
                g = max(g.geoms, key=lambda q: q.area)
            x, y, s, h = self.adlar[i]
            a = min(self.m2, key=lambda t: (t[0] - x) ** 2 + (t[1] - y) ** 2) if self.m2 else None
            am2 = a[2] if a and math.hypot(a[0] - x, a[1] - y) < 80 else None
            self.mahal.append(dict(ad=s, xy=(x, y), poly=g, alan_cizim=g.area / 1e4, alan_mimari=am2, bilesen=int(L)))

    def _daireler(self):
        """kapı grafiği: her kapının iki yanındaki mahaller bağlıdır; ortak alan (merdiven/asansör/koridor/adsız) dışı
        bileşenler = daire. Daire no: giriş kapısına (ortak alana açılan) en yakın 'DAİRE n' yazısı."""
        OR = ('MERDİVEN', 'ASANSÖR', 'KORİDOR', 'ENERJİ', 'SIĞINAK', 'KAZAN', 'JENERATÖR', 'güvenlik', 'MESC', 'MUTFAK NİŞİ')
        polys = [m['poly'] for m in self.mahal]
        def bul(p):
            pt = Point(p)
            best, bd = None, 1e9
            for i, g in enumerate(polys):
                d = g.distance(pt)
                if d < bd:
                    best, bd = i, d
            return best if bd < 20 else None
        for m in self.mahal:
            m['ortak'] = any(m['ad'].upper().startswith(o.upper()) for o in OR) or m['alan_cizim'] > 45
        for d in self.kapilar:
            c, u1, u2 = d['mentese'], d['uc1'], d['uc2']
            # kapalı konum: menteşeden duvar doğrultusundaki uç; iki uçtan hangisi kapalıysa onun orta noktası
            yan = []
            for u in (u1, u2):
                mx, my = (c[0] + u[0]) / 2, (c[1] + u[1]) / 2
                vx, vy = u[0] - c[0], u[1] - c[1]
                L = math.hypot(vx, vy) or 1
                nx, ny = -vy / L, vx / L
                a1 = bul((mx + nx * 35, my + ny * 35)); a2 = bul((mx - nx * 35, my - ny * 35))
                if a1 is not None and a2 is not None and a1 != a2:
                    yan.append((a1, a2, (mx, my), (u[0] - c[0], u[1] - c[1])))
            d['mahaller'] = yan[0][:2] if yan else None
            if yan:
                d['orta'] = yan[0][2]; d['dogrultu'] = yan[0][3]
        # daire ataması: her 'DAİRE n' yazısından kapılar açık serbest alanda jeodezik mesafe; mahal en yakın yazıya
        from skimage.graph import MCP_Geometric
        free = self.img_acik == 0
        cost = np.where(free, 1.0, np.inf)
        H, W = free.shape
        D = []
        for (x, y, no) in self.daire_yazi:
            c, r = self.px((x, y))
            if not (0 <= r < H and 0 <= c < W) or not free[r, c]:
                ys, xs = np.where(free[max(0, r - 15):r + 16, max(0, c - 15):c + 16])
                if len(ys) == 0:
                    D.append(None); continue
                r, c = max(0, r - 15) + ys[0], max(0, c - 15) + xs[0]
            m = MCP_Geometric(cost)
            d, _ = m.find_costs([(r, c)])
            D.append(d)
        self.daireler = {}
        for i, m in enumerate(self.mahal):
            m['daire'] = None
            if m['ortak'] or not self.daire_yazi:
                continue
            c, r = self.px(m['poly'].representative_point().coords[0])
            best, bd = None, np.inf
            for j, d in enumerate(D):
                if d is None:
                    continue
                v = d[r, c]
                if v < bd:
                    best, bd = j, v
            if best is not None and bd < 1500 / RES:
                m['daire'] = self.daire_yazi[best][2]
                self.daireler.setdefault(m['daire'], []).append(i)
        # giriş kapısı: daire mahallerinden birine ve ortak/adsız alana açılan kapı
        self.daire_giris = {}
        for no, idx in self.daireler.items():
            t = [t for t in self.daire_yazi if t[2] == no][0]
            best, bd = None, 1e9
            for d in self.kapilar:
                if not d.get('mahaller'):
                    # bir yanı mahal değil (koridor) olabilir
                    pass
                mx, my = d['mentese']
                dd = math.hypot(mx - t[0], my - t[1])
                if dd < bd:
                    best, bd = d, dd
            self.daire_giris[no] = best

    def _armaturler(self):
        self.armatur = []
        for r in self.R:
            if r[1] in ('rtm-tefris vitrifiye', 'sbl-tefris vitrifiye') and r[0] in 'PLC':
                self.armatur.append(r)

    def _acikliklar(self):
        self.pencere_yazi = []
        for r in self.R:
            if r[0] == 'T':
                s = temiz(r[2][1])
                m = re.match(r'^(P|K|PK|KP)\.?\s*(\d+)\s*/\s*(\d+)', s)
                if m:
                    self.pencere_yazi.append((r[2][0][0], r[2][0][1], m.group(1), int(m.group(2)), int(m.group(3))))


if __name__ == '__main__':
    import time
    for b, k, *_ in KATLAR:
        t = time.time()
        K = Kat(b, k)
        bad = [(m['ad'], round(m['alan_cizim'], 2), m['alan_mimari']) for m in K.mahal
               if m['alan_mimari'] and abs(m['alan_cizim'] - m['alan_mimari']) > 0.15 * m['alan_mimari'] + 0.3]
        print('   daireler', sorted((k, len(v)) for k, v in K.daireler.items()))
        print(b, k, 'mahal', len(K.mahal), 'ad', len(K.adlar), 'daire', len(K.daire_yazi), 'beton', len(K.betonarme),
              'pencere', len(K.pencere_yazi), 'uyumsuz', len(bad), round(time.time() - t, 1))
        print('   ', bad[:8])


def disa_aktar(K, yol):
    """kat JSON'u: diğer modüller (sıhhi, ısıtma, havalandırma) bunu okur."""
    out = dict(blok=K.blok, kat=K.kat, kot=K.kot, pencere_kutusu=K.k[2:6],
               mahaller=[dict(no=i, ad=m['ad'], xy=m['xy'], alan_mimari=m['alan_mimari'], alan_cizim=round(m['alan_cizim'], 2),
                              daire=m.get('daire'), ortak=m.get('ortak'),
                              poligon=[(round(x, 1), round(y, 1)) for x, y in m['poly'].exterior.coords])
                         for i, m in enumerate(K.mahal)],
               daireler={str(k): v for k, v in K.daireler.items()},
               daire_yazi=K.daire_yazi,
               kapilar=[dict(mentese=d['mentese'], uc1=d['uc1'], uc2=d['uc2'], r=d['r'], mahaller=d.get('mahaller'),
                             orta=d.get('orta')) for d in K.kapilar],
               daire_giris={str(k): (dict(mentese=v['mentese'], uc1=v['uc1'], uc2=v['uc2']) if v else None)
                            for k, v in K.daire_giris.items()},
               betonarme=[[(round(x, 1), round(y, 1)) for x, y in g.exterior.coords] for g in K.betonarme],
               pencere_yazi=K.pencere_yazi)
    json.dump(out, open(yol, 'w'), ensure_ascii=False, indent=0, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))


def hepsi(klasor='/tmp/claude-0/ab'):
    for b, k, *_ in KATLAR:
        K = Kat(b, k)
        disa_aktar(K, f'{klasor}/kat_{b}_{k}.json')
        print('yazıldı', b, k)
