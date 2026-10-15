"""yerden2 — mimari okuma: mahal poligonları (sihhi2.mimari2.Kat), ısıtılan mahaller, kapılar, tefriş/vitrifiye
engelleri ve ısıtma bölgesi.

Mahal tanıma yalnız `motor/sihhi2/mimari2.py` (o da kontrolörün `mimari_bilgi.py`'si) ile yapılır; burada
yerden ısıtmaya özgü kararlar var:
  * ısıtılan / ısıtılmayan mahal ve sıcaklık (oda/salon/mutfak 20, hol 15, banyo 24)
  * başka mahal etiketini içine alan poligonun bölünmesi (ör. yatak odasından kapıyla açılan yüklük)
  * tefriş engelleri: mahal içindeki MKDU0 çizgilerinin (kapı kanadı/yayı hariç) kapattığı bölgeler
    (mutfak tezgâhı + buzdolabı, klozet, lavabo, duş teknesi, çamaşır makinesi, şaft) — serpantin girmez
"""
import math
import os
import pickle
import sys

import cv2
import numpy as np
from scipy import ndimage as ndi
from shapely.geometry import LineString, Point, Polygon, box, MultiPolygon
from shapely.ops import unary_union

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
sys.path.insert(0, KOK + '/motor/sihhi2')
import mimari2 as M2  # noqa: E402

ONBELLEK = '/tmp/claude-0/y2/onbellek'
KENAR = 7.5


def kat_oku(k, yenile=False):
    os.makedirs(ONBELLEK, exist_ok=True)
    yol = '%s/kat_%s.pkl' % (ONBELLEK, k)
    if os.path.exists(yol) and not yenile:
        try:
            return pickle.load(open(yol, 'rb'))
        except Exception:
            pass
    A = M2.kayitlar()
    K = M2.Kat(A, k)
    pickle.dump(K, open(yol, 'wb'))
    return K


def _parcalar(g):
    if g.is_empty:
        return []
    return [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon' and not q.is_empty]


def _yari_duzlem_parca(P, p, oda_xy, pen=260.0, adim=2.0, kesit_max=140.0):
    """Tur 3 Y-1: yatak odasından kapıyla açılan yüklük (kapı boşluğu duvarsız olduğundan iki mahal tek poligonda).
    Etiket noktası p'nin çevresinde x/y eksenine dik kesitler (yarı düzlem) taranır: kesit çizgisinin poligonla kesişimi
    ≤ 140 cm (80'lik kapı + kasa/duvar kalınlığı), kesilen parça p'yi içerir, oda etiketini içermez, tek parça ve
    0,6–3,5 m² -> en büyük parça (kesit kapı eşiğinde). Morfolojik açma (eski yöntem) katlar arasında kararsızdı
    (zemin katta bölüyor, 1. ve 2. katta bölmüyordu)."""
    x0, y0, x1, y1 = P.bounds
    best = None
    for eks in 'xy':
        for yon in (1, -1):
            c = (p.x if eks == 'x' else p.y) - pen
            son = (p.x if eks == 'x' else p.y) + pen
            while c <= son:
                if eks == 'x':
                    ln = LineString([(c, y0 - 5), (c, y1 + 5)])
                    yd = box(c, y0 - 5, x1 + 5, y1 + 5) if yon > 0 else box(x0 - 5, y0 - 5, c, y1 + 5)
                else:
                    ln = LineString([(x0 - 5, c), (x1 + 5, c)])
                    yd = box(x0 - 5, c, x1 + 5, y1 + 5) if yon > 0 else box(x0 - 5, y0 - 5, x1 + 5, c)
                c += adim
                if P.intersection(ln).length > kesit_max:
                    continue
                q = P.intersection(yd)
                ps = _parcalar(q)
                if len(ps) != 1:
                    continue
                q = ps[0]
                if not (6000 <= q.area <= 35000) or not q.buffer(15).contains(p) or q.buffer(5).contains(Point(oda_xy)):
                    continue
                if best is None or q.area > best.area:
                    best = q
    return best


def yabanci_etiket_bol(K):
    """Bir mahal poligonu başka bir mahalin etiket noktasını içeriyorsa (kapıyla bağlı yüklük vb.) o kısmı ayır:
    80 cm açma ile kopan bileşen, etiketin olduğu taraf -> o mahale verilir."""
    for r in K.rooms:
        for q in K.rooms:
            if q is r:
                continue
            p = Point(q['xy'])
            if not r['poly'].buffer(20).contains(p) or math.hypot(q['xy'][0] - r['xy'][0], q['xy'][1] - r['xy'][1]) < 80:
                continue
            parca = _yari_duzlem_parca(r['poly'], p, r['xy'])
            for rad in ((40, 50, 60) if parca is None else ()):
                ac = r['poly'].buffer(-rad, join_style=2).buffer(rad, join_style=2)
                for c in _parcalar(ac):
                    if c.buffer(30).contains(p) and not c.buffer(5).contains(Point(r['xy'])):
                        parca = c.buffer(rad * 0.0)
                if parca is None:
                    # etiket tarafı açmada yok oldu: kalan (poligon - açılmış) içinde etiketi taşıyan büyük parça
                    kal = r['poly'].difference(ac.buffer(1, join_style=2))
                    for c in _parcalar(kal):
                        if c.buffer(15).contains(p) and c.area > 8000:
                            parca = c
                if parca is not None:
                    break
            if parca is None:
                continue
            ek = r['poly'].intersection(parca.buffer(2, join_style=2))
            r['poly'] = max(_parcalar(r['poly'].difference(ek).buffer(0)), key=lambda g: g.area)
            r['area'] = r['poly'].area / 1e4
            yeni = unary_union([q['poly'], ek]).buffer(0)
            q['poly'] = max(_parcalar(yeni), key=lambda g: g.area)
            q['area'] = q['poly'].area / 1e4
            q['bolundu'] = True


def isitma_sinifi(r):
    """-> (ısıtılır mı, sıcaklık, tür)"""
    ad = M2.MB.norm(r['name'])
    tip = r['tip']
    A = r['area']
    if tip in ('balkon', 'ortak') or r.get('daire') is None:
        return False, None, tip
    if 'yüklük' in ad or 'kiler' in ad:
        return False, None, 'yukluk'
    if tip == 'hol':
        return True, 15, 'hol'
    if tip == 'mutfak':
        return True, 20, 'mutfak'
    if tip == 'islak':
        if 'banyo' in ad:
            return True, 24, 'banyo'
        # wc-lvb, duş, wc-duş: küçükse ısıtılmaz (duş kabini / dar WC). Kullanıcı 1. kat D6'da 2,65 m² wc-duşu
        # ayrı devre yapmamış, yalnız yanındaki banyoyu ısıtmış (R2): banyo adı taşımayan ıslak hacim ≤ 2,7 m² ısıtılmaz
        if A < 2.7:
            return False, None, 'wc'
        return True, 24, 'banyo'
    return True, 20, 'oda'


def kapilar(K, r):
    """mahalin kapıları (merkez noktası, karşı taraftaki mahal tipi)"""
    out = []
    for q in list(K.kapilar) + list(getattr(K, 'acikliklar', [])):
        if r['poly'].distance(q) > 20:
            continue
        c = q.centroid
        karsi = [o for o in K.rooms if o is not r and o['poly'].distance(q) < 20]
        out.append(dict(poly=q, c=(c.x, c.y), karsi=[o['tip'] for o in karsi]))
    return out


def ana_kapi(K, r, tur):
    ks = kapilar(K, r)
    if not ks:
        return None
    if tur == 'hol':
        tercih = [k for k in ks if 'ortak' in k['karsi']]
    else:
        tercih = [k for k in ks if 'hol' in k['karsi']]
    k = (tercih or [k for k in ks if 'balkon' not in k['karsi']] or ks)[0]
    return k['c']


def _geom(a):
    if a[0] == 'L':
        return LineString(a[1])
    if a[0] in 'PA':
        return LineString(a[1]) if len(a[1]) > 1 else None
    if a[0] == 'C':
        return Point(a[1][0]).buffer(a[2], 16).exterior
    return None


def _kapi_parcasi(a, ge, kapi_u):
    """kapı kanadı (ince uzun dikdörtgen / çizgi) veya kapı süpürme yayı (r 60-115)"""
    b = ge.bounds
    bw, bh = b[2] - b[0], b[3] - b[1]
    if a[0] == 'A':
        pts = a[1]
        if len(pts) >= 3:
            c = M2._c3(pts[0], pts[len(pts) // 2], pts[-1])
            if c:
                rr = math.hypot(pts[0][0] - c[0], pts[0][1] - c[1])
                if 55 <= rr <= 120:
                    return True
        return False
    if a[0] == 'P' and len(a[1]) >= 4:
        mrr = Polygon(a[1]).minimum_rotated_rectangle if len(a[1]) >= 3 else None
        if mrr is not None and not mrr.is_empty and mrr.geom_type == 'Polygon':
            cs = list(mrr.exterior.coords)
            d1 = math.hypot(cs[1][0] - cs[0][0], cs[1][1] - cs[0][1])
            d2 = math.hypot(cs[2][0] - cs[1][0], cs[2][1] - cs[1][1])
            if min(d1, d2) < 9 and 55 <= max(d1, d2) <= 125:
                return True
    if not kapi_u.is_empty and ge.intersects(kapi_u):
        kapali = a[0] in 'AC' or (a[0] == 'P' and len(a[1]) > 3 and
                                  math.hypot(a[1][0][0] - a[1][-1][0], a[1][0][1] - a[1][-1][1]) < 1)
        # kapıya değen küçük kapalı şekil (klozet elipsi, lavabo) engeldir; diğerleri kapı parçası
        return not (kapali and max(bw, bh) < 55)
    return False


def engeller(K, r, res=2.0, islak=False):
    """mahal içindeki tefriş/vitrifiye engelleri (MultiPolygon) — çizgilerin kapattığı, ana boşluğa açılmayan bölgeler.
    islak=True (banyo, wc-banyo): yalnız duş teknesi / küvet, klozet ve lavabo hariç tutulur (R2); çamaşır makinesi
    kutusu gibi diğer kapalı bölgelerin altı ısıtılır."""
    eng = _engeller(K, r, res)
    if not islak:
        return eng
    P = r['poly']
    vit = []           # vitrifiye: klozet, duş teknesi, lavabo (+ küvet)
    for f in getattr(K, 'fx', []):
        if f['kind'] not in ('WC', 'LV', 'DUS', 'KUVET') or not P.buffer(10).contains(Point(f['c'])):
            continue
        vit.append(box(*f['bb']).buffer(4, join_style=2) if f.get('bb') else Point(f['c']).buffer(12))
    lav = lavabolar(K, P)
    vit += lav
    vit_u = unary_union(vit) if vit else Polygon()
    tut = []
    for q in _parcalar(eng):
        if q.area < 3000 or (not vit_u.is_empty and q.intersection(vit_u).area > 50) or _cm_kutusu(q):
            tut.append(q)
    tut += [q.intersection(P) for q in lav]
    # Tur 3 Y-2: çamaşır makinesi kutusu (fx 'CM' ya da 40-80 cm kare kapalı kutu) altına boru girmez (referansta
    # Ç.M. altı boş; kontrolörün mahal poligonu da Ç.M. nişini dışarıda bırakıyor)
    for f in getattr(K, 'fx', []):
        if f['kind'] == 'CM' and f.get('bb') and P.buffer(10).contains(Point(f['c'])):
            tut.append(box(*f['bb']).buffer(4, join_style=2).intersection(P))
    if not tut:
        return Polygon()
    # vitrifiye payı: kutu + 4 cm yerine kutu + 1 cm (boru ekseni vitrifiyeden ≈ 7,5 cm, altı yine boş) -> ıslak hacimde
    # serbest zemin daha çok dolar (Y-2)
    return unary_union(tut).buffer(-ISLAK_PAY_AZALT, join_style=2).buffer(0)


ISLAK_PAY_AZALT = 3.0


def _cm_kutusu(q):
    """kapalı, kareye yakın 40-80 cm kutu (çamaşır makinesi / dolap)"""
    mrr = q.minimum_rotated_rectangle
    if mrr.is_empty or mrr.geom_type != 'Polygon':
        return False
    cs = list(mrr.exterior.coords)
    a = math.hypot(cs[1][0] - cs[0][0], cs[1][1] - cs[0][1])
    b = math.hypot(cs[2][0] - cs[1][0], cs[2][1] - cs[1][1])
    return 40 <= min(a, b) and max(a, b) <= 85 and q.area > 0.8 * mrr.area


def lavabolar(K, P):
    """lavabo: duvara yaslı küçük kutu (P, 4+ köşe, 25..75 cm) ve içinde batarya/süzgeç daireleri (r < 4)"""
    daire = [Point(a[1][0]) for a in K.R if a[0] == 'C' and a[2] < 4.0 and P.buffer(-2).contains(Point(a[1][0]))]
    out = []
    for a in K.R:
        if a[0] != 'P' or len(a[1]) < 4:
            continue
        g = LineString(a[1])
        x0, y0, x1, y1 = g.bounds
        if not (25 <= x1 - x0 <= 75 and 25 <= y1 - y0 <= 75):
            continue
        b = box(x0, y0, x1, y1)
        if not P.buffer(5).contains(b):
            continue
        if sum(1 for c in daire if b.contains(c)) >= 2:
            out.append(b.buffer(4, join_style=2))
    return out


def _engeller(K, r, res=2.0):
    P = r['poly']
    Pin = P.buffer(-3)
    if Pin.is_empty:
        return Polygon()
    kapi_u = unary_union([q.buffer(14) for q in list(K.kapilar) + list(getattr(K, 'acikliklar', []))
                          if q.distance(P) < 25] or [Polygon()])
    x0, y0, x1, y1 = P.bounds
    w = (x0 - 10, y0 - 10, x1 + 10, y1 + 10)
    g = M2.Izgara(w, res)
    oda = g.doldur(P.buffer(-1))
    bar = np.zeros_like(oda)
    say = 0
    ogeler = []
    for a in K.R:
        if a[0] not in 'LPAC':
            continue
        ge = _geom(a)
        if ge is None or ge.is_empty:
            continue
        b = ge.bounds
        if b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1:
            continue
        ic = ge.intersection(Pin)
        if ic.is_empty or ic.length < 8:
            continue
        ogeler.append([a, ge, ic, _kapi_parcasi(a, ge, kapi_u)])
    # kapı kanadının (açılı çizilmiş kapı) kapı parçasına değen kısa çizgileri ve kapı etiket dairesi (K2, r≈8)
    # da kapı parçasıdır: süpürme alanı engel değildir, altından boru geçer (R10 Z19)
    kapi_y = kapi_u.buffer(40) if not kapi_u.is_empty else kapi_u
    for _ in range(3):
        kp = [o[1] for o in ogeler if o[3]]
        if not kp:
            break
        degisti = False
        for o in ogeler:
            if o[3]:
                continue
            a, ge = o[0], o[1]
            if a[0] == 'C' and 6.0 <= a[2] <= 10.0 and not kapi_y.is_empty and kapi_y.contains(ge.centroid):
                o[3] = degisti = True
            elif a[0] == 'L' and ge.length < 130 and any(ge.distance(k) < 2.0 for k in kp):
                o[3] = degisti = True
        if not degisti:
            break
    for a, ge, ic, kapi_mi in ogeler:
        if kapi_mi:
            continue                     # kapı kanadı / kapı yayı: süpürme alanı hariç tutulmaz
        for s in getattr(ic, 'geoms', [ic]):
            if s.geom_type != 'LineString':
                continue
            pts = np.array([g.px(p) for p in s.coords], np.int32)
            cv2.polylines(bar, [pts], False, 255, 1)
            say += 1
    ek = []
    for f in getattr(K, 'fx', []):
        if f['kind'] not in ('WC', 'LV', 'DUS', 'CM') or not P.buffer(10).contains(Point(f['c'])):
            continue
        if f.get('bb'):
            ek.append(box(*f['bb']).buffer(4, join_style=2))
        elif f['kind'] == 'WC':
            ek.append(Point(f['c']).buffer(35))
        elif f['kind'] == 'LV':
            ek.append(Point(f['c']).buffer(28))
    ek = unary_union(ek).intersection(P) if ek else Polygon()
    if not say:
        return ek
    bar = cv2.dilate(bar, np.ones((3, 3), np.uint8), iterations=2)       # ~4-8 cm aralıkları kapat
    serbest = (oda > 0) & (bar == 0)
    lab, n = ndi.label(serbest)
    if n == 0:
        return Polygon()
    alan = ndi.sum(serbest, lab, range(1, n + 1))
    ana = int(np.argmax(alan)) + 1
    eng = (oda > 0) & (lab != ana)
    # yalnız çizgi (kapatmayan) pikselleri: açma ile at
    eng = cv2.morphologyEx(eng.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    pg = g.poligon(eng, min_alan=150)
    pg = pg.buffer(res, join_style=2) if not pg.is_empty else pg
    # çok küçük parçaları at (< 0,03 m²)
    pg = unary_union([q for q in _parcalar(pg) if q.area > 300]) if _parcalar(pg) else Polygon()
    return unary_union([pg, ek]) if not ek.is_empty else pg


def bolge(r, eng, kenar=None):
    """ısıtma bölgesi (boru ekseninin bulunabileceği alan): mahal - engel(+kenar) , duvardan KENAR içeride.
    Delik (duvara değmeyen engel) yatay doğrultuda en yakın kenara uzatılır: parmaklar tek aralıkta kalsın."""
    P = r['poly']
    H = P.buffer(-1.0, join_style=2)
    if not eng.is_empty:
        H = H.difference(eng)
    H = H.buffer(0)
    parca = max(_parcalar(H), key=lambda q: q.area) if _parcalar(H) else Polygon()
    if parca.is_empty:
        return Polygon(), Polygon()
    # delikler -> yatayda en yakın dış kenara uzat
    if parca.interiors:
        dis = Polygon(parca.exterior)
        ek = []
        bx0, _, bx1, _ = dis.bounds
        for ring in parca.interiors:
            h = Polygon(ring)
            hx0, hy0, hx1, hy1 = h.bounds
            sol = box(bx0 - 1, hy0, hx1, hy1).difference(dis)
            sag = box(hx0, hy0, bx1 + 1, hy1).difference(dis)
            dl, dr = hx0 - bx0, bx1 - hx1
            ek.append(box(bx0 - 1, hy0, hx1, hy1) if dl <= dr else box(hx0, hy0, bx1 + 1, hy1))
        parca = dis.difference(unary_union(ek)).buffer(0)
        parca = max(_parcalar(parca), key=lambda q: q.area) if _parcalar(parca) else Polygon()
    H = parca
    kenar = KENAR if kenar is None else kenar
    R = H.buffer(-(kenar - 1.0), join_style=2)
    R = R.buffer(-12, join_style=2).buffer(12, join_style=2)     # 24 cm'den dar dilleri at
    pr = _parcalar(R)
    if not pr:
        return H, Polygon()
    R = max(pr, key=lambda q: q.area)
    # duvar yüzündeki küçük girintileri (kolon/pencere sıvası, ≤ 10 cm) kapat; duvardan ≥ 4 cm kalsın
    R = R.buffer(5, join_style=2).buffer(-5, join_style=2).intersection(H.buffer(-4, join_style=2))
    pr = _parcalar(R.buffer(0))
    if not pr:
        return H, Polygon()
    R = max(pr, key=lambda q: q.area).simplify(0.5)
    return H, R
