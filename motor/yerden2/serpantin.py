"""yerden2 — meander (gidiş-dönüş paralel) serpantin geometrisi.

Kullanıcının çizimi (YERDEN_ISITMA_ALTIN_REFERANS.md §3, §7 PEX-1..PEX-8):
  * parmaklar plan X eksenine paralel, boru aralığı 15, U dönüşü r7 yay + 1 cm düz + r7 yay (bulge ±0,4142)
  * besleme (gidiş) hattı dikey, ilk dönüş tepesinin 15 cm dışında; iki uç aynı köşede 15 cm aralıkla
  * iki/üç devreli mahalde devreler parmaklara paralel bantlara bölünür; uzak devrenin besleme + dönüş ayağı köşeye
    kadar iner, yakın devrenin besleme hattı 30 cm içeride (uçlar aynı köşede)

Hesap "kanonik" çerçevede yapılır: uç köşesi = sol-alt (besleme solda, uçlar altta). Diğer köşeler x/y aynalanarak
bu çerçeveye getirilir; çıktıda geri aynalanır (bulge işareti sx·sy ile çarpılır).
"""
import math

from shapely.affinity import scale as _scale
from shapely.geometry import LineString, Polygon, box, MultiPolygon
from shapely.ops import unary_union

ADIM = 15.0          # boru aralığı (pitch)
R_DON = 7.0          # dönüş yayı yarıçapı
KENAR = 7.5          # duvar iç yüzü -> boru ekseni
BULGE = math.tan(math.radians(22.5))   # 90° yay
AYAK_ARA = 30.0      # devreler arası besleme hattı kaydırması
ETIKET_W, ETIKET_H = 150.0, 80.0
CEP_PAY = 7.5        # cep (etiket boşluğu) - boru ekseni
MIN_SATIR = 24.0     # bir parmağın en kısa düz boyu (dönüşler dahil > 2·r)

KOSELER = ('SW', 'SE', 'NW', 'NE')


# ---------------------------------------------------------------- dönüşüm
class Cerceve:
    """dünya <-> kanonik (uç köşesi sol-alt) dönüşümü"""

    def __init__(self, kose, merkez):
        self.kose = kose
        self.sx = 1.0 if kose[1] == 'W' else -1.0
        self.sy = 1.0 if kose[0] == 'S' else -1.0
        self.ox, self.oy = merkez

    def ic(self, g):          # dünya -> kanonik (shapely)
        from shapely.affinity import affine_transform
        return affine_transform(g, [self.sx, 0, 0, self.sy, -self.sx * self.ox, -self.sy * self.oy])

    def dis(self, g):         # kanonik -> dünya
        from shapely.affinity import affine_transform
        return affine_transform(g, [self.sx, 0, 0, self.sy, self.ox, self.oy])

    def nokta_dis(self, x, y):
        return (self.sx * x + self.ox, self.sy * y + self.oy)

    def bulge_dis(self, b):
        return b * self.sx * self.sy


# ---------------------------------------------------------------- yardımcı
def araliklar(R, y):
    """R ∩ yatay doğru (y) -> [(x0, x1)] sıralı"""
    if R.is_empty:
        return []
    x0, _, x1, _ = R.bounds
    g = R.intersection(LineString([(x0 - 5, y), (x1 + 5, y)]))
    out = []
    for q in getattr(g, 'geoms', [g]):
        if q.is_empty:
            continue
        if q.geom_type == 'LineString':
            xs = [c[0] for c in q.coords]
            out.append((min(xs), max(xs)))
    out.sort()
    # birbirine değen parçaları birleştir
    bir = []
    for a in out:
        if bir and a[0] - bir[-1][1] < 0.05:
            bir[-1] = (bir[-1][0], max(bir[-1][1], a[1]))
        else:
            bir.append(a)
    return bir


def yay_uzunlugu(p, q, b):
    c = math.hypot(q[0] - p[0], q[1] - p[1])
    if abs(b) < 1e-9:
        return c
    th = 4 * math.atan(abs(b))
    r = c / (2 * math.sin(th / 2))
    return r * th


def uzunluk(pts):
    """pts: [(x, y, bulge)] -> yaylar dahil gerçek uzunluk (cm)"""
    return sum(yay_uzunlugu(pts[i][:2], pts[i + 1][:2], pts[i][2]) for i in range(len(pts) - 1))


def yay_nokta(p, q, b, n=6):
    """bulge yayını n parçaya böl (kontrol için)"""
    if abs(b) < 1e-9:
        return [p, q]
    th = 4 * math.atan(b)
    cx_, cy_ = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    dx, dy = q[0] - p[0], q[1] - p[1]
    c = math.hypot(dx, dy)
    s = c / 2 / math.tan(th / 2)          # merkez ofseti (işaretli)
    mx, my = cx_ - dy / c * s, cy_ + dx / c * s
    a0 = math.atan2(p[1] - my, p[0] - mx)
    r = math.hypot(p[0] - mx, p[1] - my)
    return [(mx + r * math.cos(a0 + th * k / n), my + r * math.sin(a0 + th * k / n)) for k in range(n + 1)]


def cizgi(pts, n=6):
    """[(x, y, bulge)] -> yaylar açılmış LineString"""
    out = [pts[0][:2]]
    for i in range(len(pts) - 1):
        seg = yay_nokta(pts[i][:2], pts[i + 1][:2], pts[i][2], n)
        out += seg[1:]
    return LineString(out)


# ---------------------------------------------------------------- satır / devre kurma (kanonik)
def _satir_secimi(R_satir, y, sol_min):
    """y satırında kullanılacak aralık -> (L, r, l) | None. Önce sol_min'i (dönüş ayağı x'i) içeren aralık;
    yoksa (etiket cebi satırı) sol_min'in sağındaki en uzun aralık."""
    ar = araliklar(R_satir, y)
    for l, r in ar:
        if l - 0.5 <= sol_min <= r and r - sol_min >= MIN_SATIR:
            return (max(l, sol_min), r, l)
    best = None
    for l, r in ar:
        if l < sol_min or r - l < MIN_SATIR:
            continue
        if best is None or (r - l) > (best[1] - best[0]):
            best = (l, r, l)
    return best


def devre_noktalari(R, R_satir, ys, fx, alt_mi, y_u):
    """Tek devre (kanonik). ys: bu devrenin satırları YUKARIDAN aşağı (çift sayıda). fx: besleme x.
    alt_mi: en yakın devre (son satır y_u). Dönüş: [(x, y, bulge)] veya None."""
    if len(ys) < 2 or len(ys) % 2:
        return None
    ret = fx + ADIM
    sat = []
    for k, y in enumerate(ys):
        s = _satir_secimi(R_satir, y, ret)
        if s is None:
            return None
        sat.append(s)
    # ilk satır beslemeye bağlanır: aralık fx'i kapsamalı
    if sat[0][2] > fx + 0.5:
        return None
    T = BULGE
    pts = [(fx, y_u, 0.0), (fx, ys[0] - R_DON, -T), (fx + R_DON, ys[0], 0.0)]
    sag = True
    for k in range(len(ys)):
        y = ys[k]
        if k == len(ys) - 1:
            # son satır sola gider
            if alt_mi:
                pts.append((ret, y, 0.0))
            else:
                if ret + R_DON > pts[-1][0] - 0.5:
                    return None
                pts += [(ret + R_DON, y, T), (ret, y - R_DON, 0.0), (ret, y_u, 0.0)]
            break
        y2 = ys[k + 1]
        if sag:
            xr = min(sat[k][1], sat[k + 1][1])
            if xr - R_DON < pts[-1][0] + 0.5:
                return None
            pts += [(xr - R_DON, y, -T), (xr, y - R_DON, 0.0), (xr, y2 + R_DON, -T), (xr - R_DON, y2, 0.0)]
        else:
            xl = max(sat[k][0], sat[k + 1][0])
            if xl + R_DON > pts[-1][0] - 0.5:
                return None
            pts += [(xl + R_DON, y, T), (xl, y - R_DON, 0.0), (xl, y2 + R_DON, T), (xl + R_DON, y2, 0.0)]
        sag = not sag
    # sıfır boylu düz parçaları at (aynı nokta)
    temiz = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - temiz[-1][0], p[1] - temiz[-1][1]) < 1e-6:
            temiz[-1] = (temiz[-1][0], temiz[-1][1], p[2])
            continue
        temiz.append(p)
    return temiz


def satirlar(R, y_u_ofset=None):
    """R alt sınırından ADIM aralıklı satır y'leri (yukarı doğru), çift sayıda; boşluk iki kenara paylaştırılır."""
    _, y0, _, y1 = R.bounds
    H = y1 - y0
    if H < ADIM:
        return []
    N = int(math.floor(H / ADIM + 1e-6)) + 1
    if N % 2:
        N -= 1
    if N < 2:
        return []
    bos = H - ADIM * (N - 1)
    off = bos / 2.0 if y_u_ofset is None else y_u_ofset
    return [y0 + off + ADIM * j for j in range(N)]


def _satirlar_faz(R, faz):
    """R alt sınırından faz (+ k·ADIM) satırları; faz None -> eski davranış (çift sayı, boşluk iki kenara)"""
    if faz is None:
        return satirlar(R)
    _, y0, _, y1 = R.bounds
    out = []
    y = y0 + faz
    while y <= y1 + 1e-6:
        out.append(y)
        y += ADIM
    return out


FAZ_ADIM = 2.5      # satır fazı tarama adımı (cm); ıslak hacimde 0,5 (tur 4 Y-2': 1 cm'lik pencereler)


def fazlar_listesi():
    k = int(round(ADIM / FAZ_ADIM))
    return [None] + [FAZ_ADIM * i for i in range(k)]


def kur(R, n, R_satir=None, bolme=None, cepler=None, y_u_ofset=None, atla=0):
    """Kanonik çerçevede n devreli meander. bolme: devre başına satır sayıları (aşağıdan yukarı: yakın..uzak) | None.
    Dönüş: dict(devreler=[pts...] (0 = en yakın/alt), ys, x_f, bolme) | None"""
    if R.is_empty:
        return None
    # atla=None: satır fazı (0..12,5 cm) ve uç tarafında atlanan satır sayısı (0..6) taranır, en çok boru boyu
    # veren (faz, atla, besleme x) seçilir. Kapı önündeki dar çıkıntı/girinti yüzünden besleme hattının odanın
    # ortasına kayması ve satır kaybı önlenir (R1 yoğunluk, R10 Z19).
    if atla is None:
        fazlar = fazlar_listesi()
        atlar = range(0, 7)
    else:
        fazlar = [y_u_ofset]
        atlar = [atla]
    best = None
    for faz in fazlar:
        ys_all = _satirlar_faz(R, faz)
        if not ys_all:
            continue
        ok_all = []
        for y in ys_all:
            a = araliklar(R, y)
            if not ok_all and (not a or max(r - l for l, r in a) < 4 * ADIM):
                continue
            if not a:
                break
            ok_all.append((y, a))
        for at in atlar:
            ok = ok_all[at:]
            if len(ok) < 2:
                break
            # besleme x'i adayları: satırların sol uçları; her aday için alttan kesintisiz kapsanan satırlar
            # (çift sayıya kırpılmış) ve kabaca kaplanan boy (sum r - x_f) -> en iyisi
            adaylar = sorted({round(l, 2) for y, a in ok for l, r in a if r - l > 3 * ADIM})
            for xf in adaylar:
                kul_, boy = [], []
                for y, a in ok:
                    hit = [(l, r) for l, r in a if l - 0.5 <= xf <= r + 0.5]
                    if not hit:
                        break
                    kul_.append(y)
                    boy.append(hit[0][1] - xf)
                Nc = len(kul_) - len(kul_) % 2
                if Nc < 2:
                    continue
                top = sum(boy[:Nc]) + 2 * ADIM * Nc
                kul_ = kul_[:Nc]
                if best is None or top > best[0] + (1e-6 if (at, faz) == (best[3], best[4]) else 20.0):
                    best = (top, xf, kul_, at, faz)
    if best is None:
        return None
    _, x_f, kul, atla, faz = best
    N = len(kul) - (len(kul) % 2)
    ys = kul[:N]
    if N < 2:
        return None
    y_u = ys[0]
    if R_satir is None:
        R_satir = R
    if bolme is None:
        bolme = esit_bol(N, n)
    if bolme is None or sum(bolme) != N:
        return None
    devreler = []
    i0 = 0
    for d, m in enumerate(bolme):          # d=0 en yakın (alt)
        sat = ys[i0:i0 + m][::-1]          # yukarıdan aşağı
        i0 += m
        fx = x_f + AYAK_ARA * (n - 1 - d)  # en yakın devre en içte
        Rs = R_satir
        pts = devre_noktalari(R, Rs, sat, fx, d == 0, y_u)
        if pts is None:
            return None
        devreler.append(pts)
    return dict(devreler=devreler, ys=ys, x_f=x_f, bolme=list(bolme), y_u=y_u, atla=atla, faz=faz)


def esit_bol(N, n):
    if N < 2 * n:
        return None
    base = (N // 2) // n
    rem = (N // 2) % n
    # uzak devrelerin ayakları uzun -> fazlalık yakın devrelere
    return [2 * (base + (1 if d < rem else 0)) for d in range(n)]


def bolmeler(N, n):
    """N satırın n devreye (her biri çift) tüm bölünmeleri (n<=3 için)"""
    out = []
    if n == 1:
        return [[N]] if N >= 2 else []
    for a in range(2, N - 2 * (n - 1) + 1, 2):
        for rest in bolmeler(N - a, n - 1):
            out.append([a] + rest)
    return out


# ---------------------------------------------------------------- basamaklı besleme (tek devre)
NEDEN = []


def _red(k):
    NEDEN.append(k)
    return None


def kur_merdiven(R, faz=None, ust_kirp=0, pay=0.0, alt=0):
    """Tek devre, besleme hattı BASAMAKLI: dikey besleme her satır grubunda o grubun sol sınırına yaslanır,
    gruplar arasında (sağdan bağlı satır çiftinin arasında, satırlardan 7,5 cm) yatay kısa bir basamakla kayar.
    Klozet/lavabo gibi duvara yaslı engellerin iki yanında ve L biçimli mahallerde besleme hattının mahalin
    ortasında kalıp bir şeridi boş bırakmasını önler (R2, R10). Kanonik çerçeve: uçlar sol-altta.
    Dönüş: kur() ile aynı biçim (devreler=[pts]) | None"""
    if R.is_empty:
        return _red(7)
    ys_all = _satirlar_faz(R, faz)
    rows = []
    for y in ys_all:
        a = [(l, r) for l, r in araliklar(R, y) if r - l >= 2 * ADIM]
        if not a:
            if rows:
                break
            continue
        rows.append((y, max(a, key=lambda t: t[1] - t[0])))
    rows = rows[alt:]
    if ust_kirp:
        rows = rows[:-ust_kirp]
    if len(rows) % 2:
        rows = rows[:-1]
    if len(rows) < 2:
        return _red(22)
    # kanonik: rows aşağıdan yukarı; devre yukarıdan aşağı gider
    top = rows[::-1]
    N = len(top)
    # gruplar: {0}, {1,2}, {3,4}, ..., {N-1}
    gruplar = [[0]] + [[k, k + 1] for k in range(1, N - 1, 2)] + [[N - 1]]
    F = []
    for g in gruplar:
        F.append(max(top[k][1][0] for k in g) + pay)
    # küçük basamakları (< 15 cm, sıva/kolon girintisi) yok et: komşu gruplar büyük olana eşitlenir
    degisti = True
    while degisti:
        degisti = False
        for i in range(len(F) - 1):
            if 0.05 < abs(F[i] - F[i + 1]) < ADIM:
                F[i] = F[i + 1] = max(F[i], F[i + 1])
                degisti = True
    # komşu satırlarla ardışık bağlantı: bir satırın aralığı bir sonrakinin F'sini kapsamıyorsa geçersiz
    gk = {}
    for gi, g in enumerate(gruplar):
        for k in g:
            gk[k] = gi
    ret = []
    for k in range(N):
        gi = gk[k]
        f = F[gi]
        # basamak komşusu satır: basamağın uç noktası + 15 cm sağında başlar
        if k % 2 == 0 and k + 1 < N and gk[k + 1] != gi:
            f = max(f, F[gk[k + 1]])
        if k % 2 == 1 and k - 1 >= 0 and gk[k - 1] != gi:
            f = max(f, F[gk[k - 1]])
        ret.append(f + ADIM)
    T = BULGE
    y_u = top[-1][0]
    # besleme: (F_son, y_u) -> yukarı, basamaklar, -> (F_0, y0 - R) -> satır 0
    pts = [(F[-1], y_u, 0.0)]
    for gi in range(len(gruplar) - 1, 0, -1):
        # grup gi'nin üstündeki basamak: grup gi'nin ilk satırı ile grup gi-1'in son satırı arasında
        k_alt = gruplar[gi][0]
        y_b = top[k_alt][0] + ADIM / 2.0
        if abs(F[gi] - F[gi - 1]) > 0.05:
            pts += [(F[gi], y_b, 0.0), (F[gi - 1], y_b, 0.0)]
    y0 = top[0][0]
    pts += [(F[0], y0 - R_DON, -T), (F[0] + R_DON, y0, 0.0)]
    sag = True
    for k in range(N):
        y = top[k][0]
        if k == N - 1:
            pts.append((ret[k], y, 0.0))
            break
        y2 = top[k + 1][0]
        if sag:
            xr = min(top[k][1][1], top[k + 1][1][1])
            if xr - R_DON < pts[-1][0] + 0.5:
                return _red(76)
            pts += [(xr - R_DON, y, -T), (xr, y - R_DON, 0.0), (xr, y2 + R_DON, -T), (xr - R_DON, y2, 0.0)]
        else:
            xl = max(ret[k], ret[k + 1])
            if xl + R_DON > pts[-1][0] - 0.5:
                return _red(81)
            pts += [(xl + R_DON, y, T), (xl, y - R_DON, 0.0), (xl, y2 + R_DON, T), (xl + R_DON, y2, 0.0)]
        sag = not sag
    # son satır sola, ret'e kadar gidiyor; ret son satırın aralığında olmalı
    if ret[-1] + 0.5 < top[-1][1][0] or ret[-1] > top[-1][1][1] - MIN_SATIR:
        return _red(86)
    # ilk satır: F_0 aralıkta
    for gi, g in enumerate(gruplar):
        for k in g:
            if F[gi] < top[k][1][0] - 0.5 or F[gi] > top[k][1][1] - MIN_SATIR:
                return _red(91)
    temiz = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - temiz[-1][0], p[1] - temiz[-1][1]) < 1e-6:
            temiz[-1] = (temiz[-1][0], temiz[-1][1], p[2])
            continue
        temiz.append(p)
    g = cizgi(temiz)
    if not g.is_simple or not R.buffer(0.6).covers(g):
        return _red(100)
    ys = [t[0] for t in rows]
    return dict(devreler=[temiz], ys=ys, x_f=F[-1], bolme=[N], y_u=y_u, atla=0, faz=faz, merdiven=True)


def en_iyi_merdiven(R):
    best = None
    for faz in fazlar_listesi():
        for alt in (0, 1, 2, 3):
            for uk in (0, 1, 2):
                for pay in (0.0, 2.5, 5.0):
                    r = kur_merdiven(R, faz, uk, pay, alt)
                    if r is not None:
                        break
                if r is None:
                    continue
                L = uzunluk(r['devreler'][0])
                if best is None or L > best[0]:
                    best = (L, r)
    return best[1] if best else None
