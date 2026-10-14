# -*- coding: utf-8 -*-
"""ROTAŞ deneme modülü: havalandırma kanal güzergâhı + boyutlandırma + çift çizgi plan çizimi.

Birimler: çizim cm (1/50 plan), kanal/menfez ölçüleri mm, debi m³/h, basınç Pa.
Akış: menfez noktaları + debiler + fan/cihaz ağzı -> tarak tipi ortogonal ağaç (aday gövde hatları denenir,
çakışmasız ve en az sac alanlı olan seçilir) -> eşit sürtünme / hız yöntemiyle 50 mm adımlı dikdörtgen kanal ->
çift çizgi (redüksiyon, yuvarlatılmış dirsek, T ayrım), akış okları, etiketler (maskeli), menfez/flex/VD/FD sembolleri,
basınç kaybı tablosu ve sac metrajı.
Mevcut motor modüllerine bağımlılığı yoktur (yalnız ezdxf + shapely).
"""
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import Polygon, LineString, Point, box, MultiLineString, GeometryCollection
from shapely.ops import unary_union
from shapely import affinity

RHO, NU, EPS = 1.2, 1.5e-5, 0.00015          # hava yoğunluğu, kinematik viskozite, galvaniz pürüzlülük (m)

# ------------------------------------------------------------------ katmanlar (ROTAS- önekli)
LAY = {
    "ROTAS-MIMARI-DUVAR": 8, "ROTAS-MIMARI-KOLON": 8, "ROTAS-MIMARI-YAZI": 8,
    "ROTAS-UFLEME-KANALI": 20, "ROTAS-EMIS-KANALI": 4, "ROTAS-TAZE-HAVA-KANALI": 3, "ROTAS-ATIK-HAVA-KANALI": 6,
    "ROTAS-EGZOZ-KANALI": 4, "ROTAS-DUMAN-EGZOZ": 1, "ROTAS-KANAL-CAP": 21, "ROTAS-KANAL-OK": 7,
    "ROTAS-FLEX": 8, "ROTAS-MENFEZ": 7, "ROTAS-MENFEZ-YAZI": 7, "ROTAS-DAMPER": 7,
    "ROTAS-HAVALANDIRMA-CIHAZ": 135, "ROTAS-JETFAN": 135, "ROTAS-TES-NOT": 7, "ROTAS-HESAP": 1,
    "ROTAS-TABLO": 7, "ROTAS-PAFTA": 7, "ROTAS-MASKE": 7, "ROTAS-SAFT": 8,
}
TUR_LAY = {"ufleme": "ROTAS-UFLEME-KANALI", "emis": "ROTAS-EMIS-KANALI", "taze": "ROTAS-TAZE-HAVA-KANALI",
           "atik": "ROTAS-ATIK-HAVA-KANALI", "egzoz": "ROTAS-EGZOZ-KANALI", "duman": "ROTAS-DUMAN-EGZOZ"}
# akış kaynağı: üfleme/atık/taze ağaçları kökten uca akar; emiş/egzoz/duman uçtan köke
TERS = {"emis", "egzoz", "duman"}


def tr(x, nd=0):
    """Türkçe sayı: binlik nokta, ondalık virgül"""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


# ------------------------------------------------------------------ hesap
def surtunme(q, w, h):
    """q m³/h, w,h mm -> (v m/s, R Pa/m) Darcy + Swamee-Jain, hidrolik çap"""
    a, b = w / 1000.0, h / 1000.0
    v = q / 3600.0 / (a * b)
    dh = 2 * a * b / (a + b)
    re = max(v * dh / NU, 2300.0)
    lam = 0.25 / (math.log10(EPS / (3.7 * dh) + 5.74 / re ** 0.9)) ** 2
    return v, lam / dh * RHO * v * v / 2


def kanal_sec(q, vmax, rmax=None, hmax=600, hmin=150, wmax=2500, oran=4.0):
    """50 mm adımlı dikdörtgen kanal: v<=vmax (ve R<=rmax: eşit sürtünme), w>=h, w/h<=oran, en az sac çevresi"""
    for orn in (oran, 6.0, 10.0):
        best = None
        for h in range(hmin, hmax + 1, 50):
            for w in range(h, wmax + 1, 50):
                if w / h > orn:
                    break
                v, r = surtunme(q, w, h)
                if v <= vmax and (rmax is None or r <= rmax):
                    c = (2 * (w + h), -h, w, h, v, r)
                    if best is None or c < best:
                        best = c
                    break
        if best:
            return dict(w=best[2], h=best[3], v=best[4], R=best[5])
    raise ValueError(f"kanal seçilemedi q={q}")


def menfez_sec(q, v_yuz=2.0, serbest=0.7, hler=(100, 150, 200, 250, 300, 400), wmax=1200):
    """menfez ölçüsü (mm): serbest kesitte hız <= v_yuz, en küçük alan"""
    best = None
    for h in hler:
        for w in range(max(200, h), wmax + 1, 50):
            if w / h > 4:
                break
            a = w * h / 1e6
            if a * serbest * v_yuz * 3600 >= q:
                c = (a * (1.0 if 1.5 <= w / h <= 3.0 else 1.25), -h, w, h)
                if best is None or c < best:
                    best = c
                break
    if not best:
        raise ValueError(f"menfez seçilemedi q={q}")
    w, h = best[2], best[3]
    return w, h, q / 3600 / (w * h / 1e6 * serbest)


FLEX_CAP = (100, 125, 150, 160, 200, 250, 315)


def flex_sec(q, vmax=3.5):
    for d in FLEX_CAP:
        if q / 3600 / (math.pi * (d / 1000) ** 2 / 4) <= vmax:
            return d
    return FLEX_CAP[-1]


def sac_kalinligi(uzun_kenar_mm, duman=False):
    """galvaniz sac kalınlığı (DIN 24190 / TS EN 1505 pratiği); duman kanalında en az 1,0 mm"""
    t = 0.5 if uzun_kenar_mm <= 300 else 0.6 if uzun_kenar_mm <= 750 else 0.8 if uzun_kenar_mm <= 1200 else 1.0 if uzun_kenar_mm <= 2000 else 1.2
    return max(t, 1.0) if duman else t


# ------------------------------------------------------------------ ağaç
class Dugum:
    __slots__ = ("id", "p", "ebeveyn", "cocuk", "uc", "q", "e")

    def __init__(self, i, p):
        self.id, self.p, self.ebeveyn, self.cocuk, self.uc, self.q, self.e = i, (float(p[0]), float(p[1])), None, [], None, 0.0, None


class Kenar:
    """ebeveyn -> çocuk kanal parçası (eksene paralel)"""
    __slots__ = ("a", "b", "q", "w", "h", "v", "R", "sinif", "grup", "zeta", "vd", "fd", "poly")

    def __init__(self, a, b, sinif):
        self.a, self.b, self.sinif = a, b, sinif
        self.q = 0.0; self.zeta = 0.0; self.vd = None; self.fd = []; self.grup = None; self.poly = None

    @property
    def L(self):
        return math.dist(self.a.p, self.b.p)

    @property
    def d(self):
        (x1, y1), (x2, y2) = self.a.p, self.b.p
        L = math.hypot(x2 - x1, y2 - y1) or 1.0
        return ((x2 - x1) / L, (y2 - y1) / L)

    @property
    def wc(self):          # genişlik cm (planda görünen)
        return self.w / 10.0


class Ag:
    """bir kanal şebekesi (ağaç)"""

    def __init__(self, ad, tur, kok, prm):
        self.ad, self.tur, self.prm = ad, tur, prm
        self.dugum = []
        self.kok = self.yeni(kok)
        self.kenar = []

    def yeni(self, p):
        n = Dugum(len(self.dugum), p); self.dugum.append(n); return n

    def bagla(self, a, b, sinif):
        if math.dist(a.p, b.p) < 0.5:          # sıfır boy: düğümleri birleştir
            return a
        b.ebeveyn = a; a.cocuk.append(b)
        e = Kenar(a, b, sinif); b.e = e; self.kenar.append(e)
        return b

    @property
    def lay(self):
        return TUR_LAY[self.tur]

    def uclar(self):
        return [n for n in self.dugum if n.uc is not None]


def _loc(eksen):
    """yerel (u: gövde boyunca, s: gövdeye dik) <-> global"""
    if eksen == "x":
        return (lambda x, y: (x, y)), (lambda u, s: (u, s))
    return (lambda x, y: (y, x)), (lambda u, s: (s, u))


def tarak(ad, tur, prm, port, yon, uclar, eksen, govde_c, yan, lead, yan_ozel=None):
    """tarak (balık kılçığı) ağaç: kaynak ağzı -> (öncü) -> gövde (eksen boyunca) -> her menfez sütununa branşman.
    uclar: [{p:(x,y), q, tip:'tavan'|'yan', ...}]; 'tavan' menfez branşmanın yanında, flex ile bağlanır (ofset prm['menfez_ofset']);
    'yan' menfez doğrudan kanal yanağında (nokta kanal ekseninde)."""
    g2l, l2g = _loc(eksen)
    ag = Ag(ad, tur, port, prm)
    pu, ps = g2l(*port); du, ds = g2l(*yon)
    off = prm.get("menfez_ofset", 70.0)
    # sütunlar
    cols = []
    for t in uclar:
        tu, ts = g2l(*t["p"])
        sy = (yan_ozel or {}).get(round(tu), yan)
        ub = tu if t["tip"] == "yan" else tu - sy * off
        for c in cols:
            if abs(c["u"] - ub) < (1.0 if t["tip"] == "yan" else 30.0):
                c["t"].append((ts, tu, t)); break
        else:
            cols.append(dict(u=ub, t=[(ts, tu, t)]))
    for c in cols:
        sy = (yan_ozel or {}).get(round(c["t"][0][1]), yan)
        c["u"] = round(sum(x[1] for x in c["t"]) / len(c["t"]) - (0 if c["t"][0][2]["tip"] == "yan" else sy * off), 1)
    # öncü
    cur = ag.kok
    if abs(ds) > 0.5:                       # ağız gövdeye dik bakıyor
        if (govde_c - ps) * ds <= 0:
            return None
        J = ag.bagla(cur, ag.yeni(l2g(pu, govde_c)), "ana")
    else:
        L1 = ag.bagla(cur, ag.yeni(l2g(pu + du * lead, ps)), "ana")
        J = ag.bagla(L1, ag.yeni(l2g(pu + du * lead, govde_c)), "ana")
        ju = pu + du * lead
        if abs(ps - govde_c) < 1 and any((c["u"] - ju) * du < -1 for c in cols):
            return None
    ju = g2l(*J.p)[0]
    # gövde zincirleri
    sag = sorted([c for c in cols if c["u"] > ju + 1], key=lambda c: c["u"])
    sol = sorted([c for c in cols if c["u"] < ju - 1], key=lambda c: -c["u"])
    orta = [c for c in cols if abs(c["u"] - ju) <= 1]
    colnode = []
    for c in orta:
        colnode.append((J, c))
    for zincir in (sag, sol):
        prev = J
        for c in zincir:
            n = ag.bagla(prev, ag.yeni(l2g(c["u"], govde_c)), "ana")
            colnode.append((n, c)); prev = n
    # branşmanlar
    for C, c in colnode:
        ust = sorted([x for x in c["t"] if x[0] > govde_c + 1], key=lambda x: x[0])
        alt = sorted([x for x in c["t"] if x[0] < govde_c - 1], key=lambda x: -x[0])
        ayni = [x for x in c["t"] if abs(x[0] - govde_c) <= 1]
        for x in ayni:
            if x[2]["tip"] != "yan" or C.uc is not None:
                return None
            C.uc = x[2]
        for kol in (ust, alt):
            prev = C
            for ts, tu, t in kol:
                n = ag.bagla(prev, ag.yeni(l2g(c["u"], ts)), "brans")
                if n.uc is not None:
                    return None
                n.uc = t; prev = n
    _akis(ag)
    return ag


def zincir(ad, tur, prm, noktalar, q, son=None):
    """verilen kırık çizgi boyunca tek debili hat (ör. taze hava/atık hava ağzı -> panjur)"""
    ag = Ag(ad, tur, noktalar[0], prm)
    cur = ag.kok
    for p in noktalar[1:]:
        cur = ag.bagla(cur, ag.yeni(p), "ana")
    cur.uc = dict(tip="son", q=q, p=noktalar[-1], **(son or {}))
    _akis(ag)
    return ag


def _akis(ag):
    def f(n):
        q = (n.uc or {}).get("q", 0.0) + sum(f(c) for c in n.cocuk)
        n.q = q
        if n.e:
            n.e.q = q
        return q
    f(ag.kok)


def boyutlandir(ag):
    p = ag.prm
    for e in ag.kenar:
        vmax = p["v_ana"] if e.sinif == "ana" else p["v_brans"]
        rmax = p.get("R") if p.get("yontem", "esit_surtunme") == "esit_surtunme" else None
        k = kanal_sec(e.q, vmax, rmax, hmax=p.get("hmax", 600), hmin=p.get("hmin", 150))
        e.w, e.h, e.v, e.R = k["w"], k["h"], k["v"], k["R"]
    # aynı debili ardışık parçalar tek grup (tek etiket, tek tablo satırı)
    gid = 0
    for e in _sirali(ag):
        pe = e.a.e
        if pe is not None and len(e.a.cocuk) == 1 and abs(pe.q - e.q) < 1e-6 and (pe.w, pe.h) == (e.w, e.h) and e.a.uc is None:
            e.grup = pe.grup
        else:
            gid += 1; e.grup = gid
    # menfez/flex ölçüleri
    for n in ag.uclar():
        t = n.uc
        if t["tip"] in ("tavan", "yan"):
            mw, mh, mv = menfez_sec(t["q"], p.get("menfez_v", 2.0), p.get("menfez_serbest", 0.7), p.get("menfez_hler", (100, 150, 200, 250, 300, 400)))
            t["mw"], t["mh"], t["mv"] = mw, mh, mv
            if t["tip"] == "tavan":
                t["flex"] = flex_sec(t["q"])


def _sirali(ag):
    out = []

    def f(n):
        for c in n.cocuk:
            out.append(c.e); f(c)
    f(ag.kok)
    return out


# ------------------------------------------------------------------ geometri
def _rect(a, b, w, ea=0.0, eb=0.0):
    (x1, y1), (x2, y2) = a, b
    L = math.hypot(x2 - x1, y2 - y1)
    if L < 1e-6:
        return Polygon()
    dx, dy = (x2 - x1) / L, (y2 - y1) / L
    nx, ny = -dy * w / 2, dx * w / 2
    p1 = (x1 - dx * ea, y1 - dy * ea); p2 = (x2 + dx * eb, y2 + dy * eb)
    return Polygon([(p1[0] + nx, p1[1] + ny), (p2[0] + nx, p2[1] + ny), (p2[0] - nx, p2[1] - ny), (p1[0] - nx, p1[1] - ny)])


def _trap(a, wa, b, wb):
    (x1, y1), (x2, y2) = a, b
    L = math.hypot(x2 - x1, y2 - y1)
    dx, dy = (x2 - x1) / L, (y2 - y1) / L
    n = (-dy, dx)
    return Polygon([(x1 + n[0] * wa / 2, y1 + n[1] * wa / 2), (x2 + n[0] * wb / 2, y2 + n[1] * wb / 2),
                    (x2 - n[0] * wb / 2, y2 - n[1] * wb / 2), (x1 - n[0] * wa / 2, y1 - n[1] * wa / 2)])


def _add(p, d, s):
    return (p[0] + d[0] * s, p[1] + d[1] * s)


def _perp(d1, d2):
    return abs(d1[0] * d2[0] + d1[1] * d2[1]) < 0.1


def ag_geometri(ag):
    """her kenar için poligon parçaları + redüksiyon ek yeri çizgileri; dönen: (birleşik poligon, ek çizgileri, kenar->poly)"""
    parcalar, ekler = [], []
    for e in ag.kenar:
        A, B = e.a, e.b
        d, w, L = e.d, e.wc, e.L
        pe = A.e
        start = A.p
        geo = []
        if pe is not None and not _perp(pe.d, d) and abs(pe.wc - w) > 0.1:
            # gövde devamında redüksiyon: branşman ağzından sonra
            s0 = max([c.e.wc / 2 + 5 for c in A.cocuk if c.e is not e and _perp(c.e.d, d)] + [0.0])
            if A.uc and A.uc.get("tip") == "yan":
                s0 = max(s0, A.uc["mw"] / 20 + 5)
            if A.uc and A.uc.get("tip") == "tavan":
                s0 = max(s0, A.uc["flex"] / 20 + 5)
            tl = 25.0
            if L < s0 + tl + 5:
                tl = max(10.0, L - s0 - 5)
                if L < s0 + tl + 2:
                    s0 = 0.0; tl = min(tl, L * 0.6)
            p0 = _add(start, d, s0); p1 = _add(start, d, s0 + tl)
            if s0 > 0:
                geo.append(_rect(start, p0, pe.wc))
            geo.append(_trap(p0, pe.wc, p1, w))
            n = (-d[1], d[0])
            ekler.append(LineString([_add(p0, n, pe.wc / 2), _add(p0, n, -pe.wc / 2)]))
            ekler.append(LineString([_add(p1, n, w / 2), _add(p1, n, -w / 2)]))
            start = p1
        # uç uzatma
        eb = 0.0
        coll = [c for c in B.cocuk if not _perp(c.e.d, d)]
        perp = [c for c in B.cocuk if _perp(c.e.d, d)]
        if not coll and perp:
            if len(perp) == 1 and abs(perp[0].e.wc - w) < 0.1 and B.uc is None:
                # yuvarlatılmış dirsek (dış yarıçap = kanal genişliği)
                d2 = perp[0].e.d
                Pi = _add(_add(B.p, d, -w / 2), d2, w / 2)
                q1 = _add(Pi, d, w); q2 = _add(q1, d2, -w); q3 = _add(Pi, d2, -w)
                quad = Polygon([Pi, q1, q2, q3])
                geo.append(Point(Pi).buffer(w, 48).intersection(quad))
            else:
                eb = max(c.e.wc for c in perp) / 2
        if not B.cocuk:
            if B.uc and B.uc.get("tip") == "tavan":
                eb = B.uc["flex"] / 20 + 5
            elif B.uc and B.uc.get("tip") == "yan":
                eb = B.uc["mw"] / 20 + 5
        if B.uc and B.uc.get("tip") == "yan" and B.cocuk:
            pass
        geo.append(_rect(start, B.p, w, 0.0, eb))
        e.poly = unary_union([g for g in geo if not g.is_empty])
        parcalar.append(e.poly)
    return unary_union(parcalar), ekler


def _ag_genislik(n):
    ws = [c.e.wc for c in n.cocuk] + ([n.e.wc] if n.e else [])
    return max(ws) if ws else 0.0


def uc_geometri(ag):
    """menfez + flex geometrileri (çizim ve çakışma için). Her uç için dict döner."""
    out = []
    for n in ag.uclar():
        t = n.uc
        if t["tip"] == "tavan":
            tx, ty = t["p"]; bx, by = n.p
            d = (1.0 if tx > bx else -1.0, 0.0) if abs(tx - bx) > abs(ty - by) else (0.0, 1.0 if ty > by else -1.0)
            wB = _ag_genislik(n)
            S = _add(n.p, d, wB / 2)
            E = _add(t["p"], d, -t["mh"] / 20)
            ml, mk = t["mw"] / 10, t["mh"] / 10        # uzun kenar branşmana paralel
            nrm = (-d[1], d[0])
            m = _rect(_add(t["p"], nrm, -ml / 2), _add(t["p"], nrm, ml / 2), mk)
            fx = _rect(S, E, t["flex"] / 10)
            out.append(dict(n=n, t=t, d=d, S=S, E=E, menfez=m, flex=fx, kutu=m.buffer(14, join_style=2).union(fx)))
        elif t["tip"] == "yan":
            e = n.e if n.e else n.cocuk[0].e
            d = e.d
            nrm = (-d[1], d[0])
            yan = t.get("yon", 1)
            nrm = (nrm[0] * yan, nrm[1] * yan)
            wB = _ag_genislik(n)
            ml = t["mw"] / 10
            c0 = _add(n.p, nrm, wB / 2)
            m = _rect(_add(c0, d, -ml / 2), _add(c0, d, ml / 2), 0.01)
            r = Polygon([_add(_add(c0, d, -ml / 2), nrm, 0), _add(_add(c0, d, ml / 2), nrm, 0),
                         _add(_add(c0, d, ml / 2), nrm, 10), _add(_add(c0, d, -ml / 2), nrm, 10)])
            out.append(dict(n=n, t=t, d=d, nrm=nrm, c0=c0, ml=ml, menfez=r, flex=None, kutu=r.buffer(18, join_style=2)))
    return out


# ------------------------------------------------------------------ çakışma
def ag_kontrol(ag, engeller, duvarlar, izinli, bosluk=10.0, detay=None):
    """0 = temiz; >0 çakışma sayısı. engeller: [Polygon], duvarlar: [(Polygon, kalınlık)], izinli: Polygon"""
    hata = 0
    E = ag.kenar
    adj = {}
    for e in E:
        adj.setdefault(e.a.id, []).append(e); adj.setdefault(e.b.id, []).append(e)
    for i, e1 in enumerate(E):
        for e2 in E[i + 1:]:
            if {e1.a.id, e1.b.id} & {e2.a.id, e2.b.id}:
                continue
            if e1.poly.intersection(e2.poly).area > 0.5:
                hata += 1
                if detay is not None: detay.append(("kenar-kenar", e1.a.p, e1.b.p, e2.a.p, e2.b.p))
    ug = uc_geometri(ag)
    for u in ug:
        for e in E:
            if e.b is u["n"] or e.a is u["n"]:
                continue
            if e.poly.intersection(u["kutu"]).area > 0.5:
                hata += 1
                if detay is not None: detay.append(("menfez-kenar", u["t"]["p"], e.a.p, e.b.p))
    for i, u1 in enumerate(ug):
        for u2 in ug[i + 1:]:
            if u1["kutu"].intersection(u2["kutu"]).area > 0.5:
                hata += 1
                if detay is not None: detay.append(("menfez-menfez", u1["t"]["p"], u2["t"]["p"]))
    tum = unary_union([e.poly for e in E] + [u["menfez"] for u in ug] + [u["flex"] for u in ug if u["flex"] is not None])
    for o in engeller:
        if tum.intersection(o.buffer(bosluk, join_style=2)).area > 0.5:
            hata += 1
            if detay is not None: detay.append(("engel", o.bounds))
    if izinli is not None and tum.difference(izinli).area > 1.0:
        hata += 1
        if detay is not None: detay.append(("izinli-disi", tum.difference(izinli).bounds))
    for wp, kal in duvarlar:
        for e in E:
            it = e.poly.intersection(wp)
            if it.area > 0.5:
                x0, y0, x1, y1 = it.bounds
                boy = (x1 - x0) if abs(e.d[0]) > 0.5 else (y1 - y0)
                if boy > kal + 1.0:
                    hata += 1
                    if detay is not None: detay.append(("duvar", e.a.p, e.b.p))
    return hata


def ag_maliyet(ag):
    return sum(e.L * 2 * (e.w + e.h) / 1000 for e in ag.kenar) + 30 * len(ag.kenar)


def oto_ag(ad, tur, prm, port, yon, uclar, engeller, duvarlar, izinli, log=None, k=1):
    """aday gövde eksen/konum/yan/öncü kombinasyonlarını dener; çakışmasız en ucuz ağacı döner"""
    best = None
    liste = []
    for eksen in ("x", "y"):
        g2l, _ = _loc(eksen)
        ss = sorted(set(round(g2l(*t["p"])[1], 0) for t in uclar))
        sat = []
        for s in ss:
            if not sat or s - sat[-1] > 20:
                sat.append(s)
        aday = set()
        if all(t["tip"] == "yan" for t in uclar):
            aday |= set(sat)
        for a, b in zip(sat, sat[1:]):
            aday.add((a + b) / 2)
        for c in prm.get("govde_bosluk", (100, 150, 200, 250, 300, 350)):
            aday.add(sat[0] - c); aday.add(sat[-1] + c)
        for gc in sorted(aday):
            for yan in (1, -1):
                g2l_, _ = _loc(eksen)
                dik = abs(g2l_(*yon)[1]) > 0.5
                for lead in (prm.get("oncu", (60, 120, 200, 300))[:1] if dik else prm.get("oncu", (60, 120, 200, 300))):
                    try:
                        ag = tarak(ad, tur, prm, port, yon, uclar, eksen, gc, yan, lead)
                    except ValueError:
                        ag = None
                    if ag is None:
                        continue
                    boyutlandir(ag)
                    ag_geometri(ag)
                    h = ag_kontrol(ag, engeller, duvarlar, izinli)
                    if h and all(t["tip"] == "tavan" for t in uclar):
                        # onarım: sütun sütun branşman tarafını çevir (açgözlü)
                        oz = {}
                        for tu_ in sorted(set(round(g2l(*t["p"])[0]) for t in uclar)):
                            dene = dict(oz); dene[tu_] = -yan
                            a2 = tarak(ad, tur, prm, port, yon, uclar, eksen, gc, yan, lead, dene)
                            if a2 is None:
                                continue
                            boyutlandir(a2); ag_geometri(a2)
                            h2 = ag_kontrol(a2, engeller, duvarlar, izinli)
                            if h2 < h:
                                ag, h, oz = a2, h2, dene
                            if h == 0:
                                break
                    c = ag_maliyet(ag) + h * 1e6
                    if log is not None:
                        log.append((ad, eksen, gc, yan, lead, h, round(c, 1)))
                    liste.append((c, h, ag, (eksen, gc, yan, lead)))
                    if best is None or c < best[0]:
                        best = (c, h, ag, (eksen, gc, yan, lead))
    if best is None:
        raise RuntimeError(f"{ad}: güzergâh bulunamadı")
    if k > 1:
        liste.sort(key=lambda x: x[0])
        for c, h, a, sc in liste:
            a.secim = sc; a.maliyet = c
        out, imza = [], set()
        for c, h, a, sc in liste:
            sg = (sc[0], sc[1])          # çeşitlilik: her gövde ekseni/konumu için en iyi aday
            if sg in imza:
                continue
            imza.add(sg); out.append((a, h))
            if len(out) >= k:
                break
        return out
    ag = best[2]
    ag.secim = best[3]; ag.maliyet = best[0]
    if best[1]:
        dt = []
        ag_kontrol(ag, engeller, duvarlar, izinli, detay=dt)
        ag.cakisma = dt
        print(ad, "SEÇİLEN", best[3], "ÇAKIŞMA:", dt)
    return ag, best[1]


# ------------------------------------------------------------------ basınç kaybı
ZETA = dict(brans=1.0, duz_gecis=0.3, dirsek=0.3, vd=0.2, fd=0.2, giris=0.5)


def basinc(ag):
    """kenar başına ζ toplamı ve kayıp; uçlara kritik yol. dönen: grup tablosu + yol listesi"""
    for e in ag.kenar:
        z = 0.0
        A = e.a
        pe = A.e
        if pe is None:
            z += ZETA["giris"]
        elif _perp(pe.d, e.d):
            z += ZETA["brans"] if len(A.cocuk) > 1 or A.uc else ZETA["dirsek"]
        elif len(A.cocuk) > 1 or A.uc:
            z += ZETA["duz_gecis"]
        if e.vd:
            z += ZETA["vd"]
        z += ZETA["fd"] * len(e.fd)
        e.zeta = z
    gr = {}
    for e in _sirali(ag):
        g = gr.setdefault(e.grup, dict(no=e.grup, q=e.q, w=e.w, h=e.h, v=e.v, R=e.R, L=0.0, z=0.0, kenar=[]))
        g["L"] += e.L / 100; g["z"] += e.zeta; g["kenar"].append(e)
    for g in gr.values():
        g["RL"] = g["R"] * g["L"]; g["Z"] = g["z"] * RHO * g["v"] ** 2 / 2; g["dp"] = g["RL"] + g["Z"]
    p = ag.prm
    yollar = []
    for n in ag.uclar():
        dp, k = 0.0, n
        while k.e is not None:
            e = k.e
            dp += e.R * e.L / 100 + e.zeta * RHO * e.v ** 2 / 2
            k = e.a
        uc_dp = p.get("menfez_dp", 25.0) if n.uc["tip"] in ("tavan", "yan") else n.uc.get("dp", 0.0)
        flx = p.get("flex_dp", 5.0) if n.uc["tip"] == "tavan" else 0.0
        yollar.append(dict(n=n, kanal=dp, uc=uc_dp, flex=flx, top=dp + uc_dp + flx))
    yollar.sort(key=lambda y: -y["top"])
    return [gr[k] for k in sorted(gr)], yollar


# ------------------------------------------------------------------ DXF çizim
class Cizim:
    def __init__(self):
        self.doc = ezdxf.new("R2018", setup=True)
        self.doc.header["$INSUNITS"] = 5            # cm
        self.doc.header["$LUNITS"] = 2
        for n, c in LAY.items():
            self.doc.layers.add(n, color=c)
        if "ROTAS" not in self.doc.styles:
            self.doc.styles.add("ROTAS", font="arial.ttf")
        self.doc.set_wipeout_variables(frame=0)
        self.msp = self.doc.modelspace()
        self.engel = []          # yazı yerleşiminde kaçınılacak geometriler
        self.yazi = []           # yerleşmiş yazı kutuları
        self.maske = []          # (köşeler, katman) – en son eklenir
        self.metin = []          # bekleyen yazılar (maskenin üstünde kalsın diye en son)

    # temel
    def L(self, a, b, lay):
        self.msp.add_line(a, b, dxfattribs=dict(layer=lay))

    def PL(self, pts, lay, kapali=False, gen=0.0):
        e = self.msp.add_lwpolyline(pts, close=kapali, dxfattribs=dict(layer=lay))
        if gen:
            e.dxf.const_width = gen
        return e

    def geom(self, g, lay, gen=0.0):
        """shapely çizgi/poligon geometrisini çiz"""
        if g.is_empty:
            return
        if isinstance(g, (MultiLineString, GeometryCollection)) or g.geom_type.startswith("Multi"):
            for x in g.geoms:
                self.geom(x, lay, gen)
        elif g.geom_type == "LineString":
            self.PL(list(g.coords), lay, gen=gen)
        elif g.geom_type == "LinearRing":
            self.PL(list(g.coords)[:-1], lay, True, gen)
        elif g.geom_type == "Polygon":
            self.geom(g.exterior, lay, gen)
            for r in g.interiors:
                self.geom(r, lay, gen)

    def C(self, c, r, lay):
        self.msp.add_circle(c, r, dxfattribs=dict(layer=lay))

    def solid(self, pts, lay):
        self.msp.add_solid(pts if len(pts) == 4 else [pts[0], pts[1], pts[2], pts[2]], dxfattribs=dict(layer=lay))

    def T(self, p, s, h, lay, al=TA.MIDDLE_CENTER, rot=0.0):
        self.metin.append((p, s, h, lay, al, rot))

    # çakışmasız yazı bloğu
    @staticmethod
    def _gen(s, h):
        return max(1, len(s)) * h * 0.68

    def blok_kutu(self, c, satir, h, rot):
        W = max(self._gen(s, h) for s in satir) + h * 0.6
        H = len(satir) * h * 1.45 + h * 0.3
        b = box(c[0] - W / 2, c[1] - H / 2, c[0] + W / 2, c[1] + H / 2)
        return affinity.rotate(b, rot, origin=c), W, H

    def serbest(self, g):
        return not any(g.intersects(o) for o in self.engel) and not any(g.intersects(o) for o in self.yazi)

    def blok(self, c, satir, h, lay, rot=0.0, kayit=True):
        g, W, H = self.blok_kutu(c, satir, h, rot)
        self.maske.append((list(g.exterior.coords)[:-1], "ROTAS-MASKE"))
        if kayit:
            self.yazi.append(g)
        n = len(satir)
        a = math.radians(rot)
        ux, uy = -math.sin(a), math.cos(a)       # yazı "yukarı" yönü
        for i, s in enumerate(satir):
            off = ((n - 1) / 2 - i) * h * 1.45
            self.T((c[0] + ux * off, c[1] + uy * off), s, h, lay, TA.MIDDLE_CENTER, rot)
        return g

    def yerlestir(self, adaylar, satir, h, lay, rot=0.0, cizgi_ucu=None, zorla=True):
        """adaylar: [(merkez, rot)] sırayla dener; serbest bulursa koyar. cizgi_ucu verilirse uzak konumda kılavuz çizgisi çizer"""
        for c, r in adaylar:
            g, _, _ = self.blok_kutu(c, satir, h, r)
            if self.serbest(g):
                self.blok(c, satir, h, lay, r)
                if cizgi_ucu and g.distance(Point(cizgi_ucu)) > 80:
                    q = g.exterior.interpolate(g.exterior.project(Point(cizgi_ucu)))
                    self.L(cizgi_ucu, (q.x, q.y), lay)
                return g, c
        if not zorla:
            return None, None
        # spiral arama
        c0, r0 = adaylar[0]
        for rr in range(30, 900, 15):
            for k in range(16):
                a = 2 * math.pi * k / 16
                c = (c0[0] + rr * math.cos(a), c0[1] + rr * math.sin(a))
                g, _, _ = self.blok_kutu(c, satir, h, 0.0)
                if self.serbest(g):
                    self.blok(c, satir, h, lay, 0.0)
                    if cizgi_ucu:
                        q = g.exterior.interpolate(g.exterior.project(Point(cizgi_ucu)))
                        ln = LineString([cizgi_ucu, (q.x, q.y)])
                        self.L(cizgi_ucu, (q.x, q.y), lay)
                        self.engel.append(ln.buffer(1))
                    return g, c
        self.blok(c0, satir, h, lay, r0)
        print("UYARI: yazı yeri bulunamadı:", satir)
        return None, c0

    def bitir(self, yol):
        for pts, lay in self.maske:
            w = self.msp.add_wipeout(pts)
            w.dxf.layer = lay
        for p, s, h, lay, al, rot in self.metin:
            t = self.msp.add_text(s, height=h, rotation=rot, dxfattribs=dict(layer=lay, style="ROTAS"))
            t.set_placement(p, align=al)
        self.doc.saveas(yol)


# ------------------------------------------------------------------ sembol çizimleri
def ok_dolu(cz, p, d, L, lay):
    """akış oku: içi dolu üçgen, ucu d yönünde"""
    n = (-d[1], d[0])
    tip = _add(p, d, L / 2); b = _add(p, d, -L / 2)
    cz.solid([tip, _add(b, n, L * 0.3), _add(b, n, -L * 0.3)], lay)


def ok_acik(cz, a, b, lay, bas=4.0):
    cz.L(a, b, lay)
    d = (b[0] - a[0], b[1] - a[1]); L = math.hypot(*d) or 1
    d = (d[0] / L, d[1] / L); n = (-d[1], d[0])
    k = _add(b, d, -bas)
    cz.L(b, _add(k, n, bas * 0.45), lay); cz.L(b, _add(k, n, -bas * 0.45), lay)


def menfez_tavan(cz, u, tur):
    """çift sıra kanatlı tavan menfezi: çerçeve + iç çerçeve + orta çizgi + kanatlar + hava yönü okları"""
    t = u["t"]; P = t["p"]; d = u["d"]; nrm = (-d[1], d[0])
    ml, mk = t["mw"] / 10, t["mh"] / 10
    cz.geom(u["menfez"], "ROTAS-MENFEZ")
    ic = _rect(_add(P, nrm, -ml / 2 + 1.5), _add(P, nrm, ml / 2 - 1.5), mk - 3)
    cz.geom(ic, "ROTAS-MENFEZ")
    cz.L(_add(P, nrm, -ml / 2 + 1.5), _add(P, nrm, ml / 2 - 1.5), "ROTAS-MENFEZ")
    k = -ml / 2 + 5.0
    while k < ml / 2 - 4.0:
        a = _add(P, nrm, k)
        cz.L(_add(a, d, -mk / 2 + 1.5), _add(a, d, -1.0), "ROTAS-MENFEZ")
        cz.L(_add(a, d, 1.0), _add(a, d, mk / 2 - 1.5), "ROTAS-MENFEZ")
        k += 5.0
    ters = tur in TERS
    for yon, uz in ((d, mk / 2), (nrm, ml / 2), ((-nrm[0], -nrm[1]), ml / 2)):
        a = _add(P, yon, uz + 2); b = _add(P, yon, uz + 12)
        if ters:
            ok_acik(cz, b, a, "ROTAS-MENFEZ")
        else:
            ok_acik(cz, a, b, "ROTAS-MENFEZ")


def flex_ciz(cz, u):
    """flex bağlantı: çift çizgi + akordeon çizgileri (5 cm aralık)"""
    S, E, D = u["S"], u["E"], u["t"]["flex"] / 10
    d = u["d"]; n = (-d[1], d[0])
    L = math.dist(S, E)
    cz.L(_add(S, n, D / 2), _add(E, n, D / 2), "ROTAS-FLEX")
    cz.L(_add(S, n, -D / 2), _add(E, n, -D / 2), "ROTAS-FLEX")
    k = 5.0
    while k < L - 2:
        a = _add(S, d, k)
        cz.L(_add(a, n, D / 2), _add(a, n, -D / 2), "ROTAS-FLEX")
        k += 5.0


def menfez_yan(cz, u, tur):
    """kanal yanağı menfezi: 3 kenar (4. kenar kanal yanağı) + eğik kanatlar + oklar"""
    c0, d, nrm, ml = u["c0"], u["d"], u["nrm"], u["ml"]
    a = _add(c0, d, -ml / 2); b = _add(c0, d, ml / 2)
    a2 = _add(a, nrm, 10); b2 = _add(b, nrm, 10)
    cz.PL([a, a2, b2, b], "ROTAS-MENFEZ")
    k = 4.0
    while k < ml - 2:
        p = _add(a, d, k)
        cz.L(_add(p, nrm, 1.5), _add(_add(p, nrm, 8.5), d, -3), "ROTAS-MENFEZ")
        k += 5.0
    ters = tur in TERS
    for f in (0.25, 0.75):
        p = _add(a, d, ml * f)
        o1, o2 = _add(p, nrm, 12), _add(p, nrm, 26)
        if ters:
            ok_acik(cz, o2, o1, "ROTAS-MENFEZ", 5)
        else:
            ok_acik(cz, o1, o2, "ROTAS-MENFEZ", 5)


def vd_ciz(cz, p, d, w):
    """ayar (volüm) damperi: eğik kanat + pivot + dışarı kol + VD"""
    n = (-d[1], d[0])
    t = math.tan(math.radians(30))
    a = _add(_add(p, n, w / 2 - 0.5), d, (w / 2) * t * 0.5)
    b = _add(_add(p, n, -w / 2 + 0.5), d, -(w / 2) * t * 0.5)
    cz.L(a, b, "ROTAS-DAMPER")
    cz.C(p, max(1.2, w * 0.05), "ROTAS-DAMPER")
    k1 = _add(p, n, w / 2); k2 = _add(p, n, w / 2 + max(8, 0.2 * w))
    cz.L(k1, k2, "ROTAS-DAMPER")
    g = LineString([k1, k2]).buffer(2)
    cz.engel.append(g)
    return k2


def fd_ciz(cz, p, d, w):
    """yangın damperi: kanala dik dar dikdörtgen (yan kenarları kanal yanağı) + X"""
    n = (-d[1], d[0])
    t = max(8.0, 0.1 * w)
    a1, a2 = _add(_add(p, d, -t / 2), n, w / 2), _add(_add(p, d, -t / 2), n, -w / 2)
    b1, b2 = _add(_add(p, d, t / 2), n, w / 2), _add(_add(p, d, t / 2), n, -w / 2)
    cz.L(a1, a2, "ROTAS-DAMPER"); cz.L(b1, b2, "ROTAS-DAMPER")
    cz.L(a1, b2, "ROTAS-DAMPER"); cz.L(a2, b1, "ROTAS-DAMPER")


def bdd_ciz(cz, p, d, w):
    """geri basınç (geri akış) damperi: kanal içinde 3 paralel eğik kanat"""
    n = (-d[1], d[0])
    for k in (-w / 3, 0, w / 3):
        c = _add(p, n, k)
        cz.L(_add(_add(c, n, w / 8), d, -w / 10), _add(_add(c, n, -w / 8), d, w / 10), "ROTAS-DAMPER")


def panjur_ciz(cz, a, b, ic_yon, dis_kal, tur):
    """duvar boşluğunda panjur: a-b duvar iç yüzü üzerinde, ic_yon binaya doğru; dis_kal duvar kalınlığı.
    çerçeve + 45° kanatlar + hava yönü oku"""
    d = (b[0] - a[0], b[1] - a[1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    o = (-ic_yon[0], -ic_yon[1])
    a2, b2 = _add(a, o, dis_kal), _add(b, o, dis_kal)
    cz.PL([a, b, b2, a2], "ROTAS-MENFEZ", kapali=True)
    k = 5.0
    while k < L - 2:
        p = _add(a, d, k)
        cz.L(_add(p, o, 2), _add(_add(p, o, dis_kal - 2), d, -min(dis_kal - 4, 6)), "ROTAS-MENFEZ")
        k += 6.0
    m = _add(_add(a, d, L / 2), o, dis_kal + 6)
    m2 = _add(m, o, 30)
    if tur == "taze":
        ok_acik(cz, m2, m, "ROTAS-MENFEZ", 8)
    else:
        ok_acik(cz, m, m2, "ROTAS-MENFEZ", 8)
    cz.engel.append(LineString([m, m2]).buffer(6))


def fan_aksiyel(cz, p, d, R, lay="ROTAS-HAVALANDIRMA-CIHAZ"):
    """aksiyel fan: kısa kanal gövdesi + daire + papyon kanat (ISO 14617-9)"""
    n = (-d[1], d[0])
    g = _rect(_add(p, d, -R * 1.2), _add(p, d, R * 1.2), 2 * R + 6)
    cz.geom(g, lay)
    cz.C(p, R, lay)
    a1, a2 = _add(p, n, R * 0.85), _add(p, n, -R * 0.85)
    cz.PL([p, _add(a1, d, -R * 0.35), _add(a1, d, R * 0.35)], lay, kapali=True)
    cz.PL([p, _add(a2, d, -R * 0.35), _add(a2, d, R * 0.35)], lay, kapali=True)
    return g


def jetfan_ciz(cz, p, d, L, D, lay="ROTAS-JETFAN"):
    """jet fan: gövde (susturucu-fan-susturucu bölmeli) + fan dairesi + atış yönü oku"""
    n = (-d[1], d[0])
    g = _rect(_add(p, d, -L / 2), _add(p, d, L / 2), D)
    cz.geom(g, lay)
    for f in (-L / 2 + L * 0.3, L / 2 - L * 0.3):
        q = _add(p, d, f)
        cz.L(_add(q, n, D / 2), _add(q, n, -D / 2), lay)
    cz.C(p, D * 0.38, lay)
    a1, a2 = _add(p, n, D * 0.33), _add(p, n, -D * 0.33)
    cz.PL([p, _add(a1, d, -D * 0.12), _add(a1, d, D * 0.12)], lay, kapali=True)
    cz.PL([p, _add(a2, d, -D * 0.12), _add(a2, d, D * 0.12)], lay, kapali=True)
    t0 = _add(p, d, L / 2 + 8); t1 = _add(p, d, L / 2 + 70)
    cz.L(t0, t1, lay)
    k = _add(t1, d, -18)
    cz.solid([t1, _add(k, n, 8), _add(k, n, -8)], lay)
    return g.union(LineString([t0, t1]).buffer(9))


def igk_ciz(cz, c, Wx, Wy, rot_d):
    """tavan tipi ısı geri kazanım cihazı (plakalı): gövde, çapraz plaka eşanjör, 2 fan, 2 filtre.
    rot_d: (dx,dy) oda tarafı yönü (ÜF/EM ağızları bu yüzde). dönen: gövde poligonu + ağız noktaları"""
    d = rot_d; n = (-d[1], d[0])
    lay = "ROTAS-HAVALANDIRMA-CIHAZ"
    hx, hy = Wx / 2, Wy / 2
    P = lambda a, b: (c[0] + d[0] * a + n[0] * b, c[1] + d[1] * a + n[1] * b)
    body = Polygon([P(-hx, -hy), P(hx, -hy), P(hx, hy), P(-hx, hy)])
    cz.geom(body, lay)
    r = min(hx, hy) * 0.55
    cz.PL([P(-r, 0), P(0, r), P(r, 0), P(0, -r)], lay, kapali=True)          # plaka eşanjör
    cz.L(P(-r, 0), P(r, 0), lay); cz.L(P(0, -r), P(0, r), lay)
    for a, b in ((hx * 0.72, hy * 0.5), (-hx * 0.72, -hy * 0.5)):             # fanlar (ÜF ve AT tarafı)
        cz.C(P(a, b), hy * 0.28, lay)
        cz.C(P(a, b), hy * 0.08, lay)
    for a in (-hx * 0.72, hx * 0.72):                                          # filtreler (TH ve EM girişinde)
        b0 = hy * 0.5 if a < 0 else -hy * 0.5
        for k in range(5):
            y0 = b0 - hy * 0.4 + k * hy * 0.2
            cz.L(P(a - 3, y0), P(a + 3, y0 + hy * 0.15), lay)
        cz.geom(Polygon([P(a - 4, b0 - hy * 0.42), P(a + 4, b0 - hy * 0.42), P(a + 4, b0 + hy * 0.42), P(a - 4, b0 + hy * 0.42)]), lay)
    agiz = dict(UF=P(hx, hy * 0.5), EM=P(hx, -hy * 0.5), TH=P(-hx, hy * 0.5), AT=P(-hx, -hy * 0.5))
    return body, agiz


# ------------------------------------------------------------------ şebeke çizimi
def ag_ciz(cz, ag, kes, etiket_h=10.0, menfez_h=8.0, fd_hatlari=(), vd=True, etiket_on="", okla=True):
    """kanal ağını çiz. kes: çizilmeyecek (üst üste binecek) çizgilerin geometrisi listesi"""
    lay = ag.lay
    union, ekler = ag_geometri(ag)
    ug = uc_geometri(ag)
    # kenar çizgileri: başka çizgilerle çakışan kısımlar (cihaz yüzü, panjur, duvar boşluğu, yan menfez) çıkarılır
    kesg = unary_union([k.buffer(0.3) for k in kes] + [u["menfez"].exterior.buffer(0.3) for u in ug if u["t"]["tip"] == "yan"])
    sinir = union.boundary.difference(kesg) if not kesg.is_empty else union.boundary
    cz.geom(sinir, lay)
    for ln in ekler:
        cz.geom(ln, lay)
    cz.engel.append(union)
    # yangın damperleri (yangın duvarı kesişimi)
    for e in ag.kenar:
        ax = LineString([e.a.p, e.b.p])
        for fl in fd_hatlari:
            it = ax.intersection(fl)
            if not it.is_empty and it.geom_type == "Point":
                e.fd.append((it.x, it.y))
    # ayar damperleri: her branşman başında
    if vd:
        for e in ag.kenar:
            pe = e.a.e
            if pe is not None and _perp(pe.d, e.d) and (len(e.a.cocuk) > 1 or e.a.uc) and e.sinif == "brans":
                s = pe.wc / 2 + 15
                if e.L > s + 10:
                    e.vd = _add(e.a.p, e.d, s)
    for e in ag.kenar:
        if e.vd:
            k2 = vd_ciz(cz, e.vd, e.d, e.wc)
            n = (-e.d[1], e.d[0])
            cz.yerlestir([(_add(k2, n, 7), 0.0), (_add(_add(k2, n, 3), e.d, 12), 0.0), (_add(_add(k2, n, 3), e.d, -12), 0.0)],
                         ["VD"], 7, "ROTAS-DAMPER")
        for p in e.fd:
            fd_ciz(cz, p, e.d, e.wc)
            n = (-e.d[1], e.d[0])
            ad = [(_add(p, n, s * (e.wc / 2 + 12)), 0.0) for s in (1, -1)]
            ad += [(_add(_add(p, n, s * (e.wc / 2 + 12)), e.d, k), 0.0) for s in (1, -1) for k in (25, -25, 50, -50)]
            cz.yerlestir(ad, ["FD", "YANGIN DAMPERİ"], 7, "ROTAS-DAMPER")
    # menfezler + flex
    for u in ug:
        if u["t"]["tip"] == "tavan":
            flex_ciz(cz, u); menfez_tavan(cz, u, ag.tur)
        else:
            menfez_yan(cz, u, ag.tur)
        cz.engel.append(u["kutu"])
    # akış okları
    if okla:
        for e in ag.kenar:
            if e.L < 60:
                continue
            ters = ag.tur in TERS
            for f in (0.5, 0.35, 0.65, 0.25, 0.75):
                p = _add(e.a.p, e.d, e.L * f)
                if e.vd and math.dist(p, e.vd) < e.wc + 10:
                    continue
                if any(math.dist(p, q) < e.wc + 15 for q in e.fd):
                    continue
                if e.b.uc and e.b.uc.get("tip") == "yan" and math.dist(p, e.b.p) < e.b.uc["mw"] / 20 + 15:
                    continue
                if e.a.uc and e.a.uc.get("tip") == "yan" and math.dist(p, e.a.p) < e.a.uc["mw"] / 20 + 15:
                    continue
                d = (-e.d[0], -e.d[1]) if ters else e.d
                ok_dolu(cz, p, d, min(max(e.wc * 0.45, 8), 30), "ROTAS-KANAL-OK")
                break
    return union, ug


def ag_etiket(cz, ag, ug, etiket_h=10.0, menfez_h=8.0, onek=""):
    """kanal etiketleri (ölçü + debi [grup no]) ve menfez etiketleri (Q / ölçü). Ağlar çizildikten sonra çağrılır"""
    grup = {}
    for e in ag.kenar:
        grup.setdefault(e.grup, []).append(e)
    for g, es in sorted(grup.items()):
        e0 = max(es, key=lambda e: e.L)
        satir = [f"{e0.w}x{e0.h}", f"{tr(e0.q)} m³/h  [{onek}{g}]"]
        rot = 0.0 if abs(e0.d[0]) > 0.5 else 90.0
        n = (-e0.d[1], e0.d[0])
        _, W, H = cz.blok_kutu((0, 0), satir, etiket_h, 0)
        ad = []
        for gap in (4, 12, 25):
            for f in (0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8):
                for es2 in es if len(es) > 1 else [e0]:
                    p = _add(es2.a.p, es2.d, es2.L * f)
                    for s in (1, -1):
                        ad.append((_add(p, n, s * (es2.wc / 2 + gap + H / 2)), rot))
        cz.yerlestir(ad, satir, etiket_h, "ROTAS-KANAL-CAP", cizgi_ucu=_add(e0.a.p, e0.d, e0.L / 2))
    for u in ug:
        t = u["t"]
        satir = [f"Q={tr(t['q'])} m³/h", f"{t['mw']}x{t['mh']}"]
        _, W, H = cz.blok_kutu((0, 0), satir, menfez_h, 0)
        P = t["p"] if t["tip"] == "tavan" else _add(u["c0"], u["nrm"], 5)
        ad = []
        for r in (W / 2 + 16, W / 2 + 30):
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                rr = r if dx else H / 2 + 16 + (r - W / 2 - 16)
                ad.append(((P[0] + dx * (W / 2 + 16 + (r - W / 2 - 16)), P[1] + dy * rr), 0.0))
        cz.yerlestir(ad, satir, menfez_h, "ROTAS-MENFEZ-YAZI", cizgi_ucu=P)


# ------------------------------------------------------------------ tablolar
def tablo(cz, x, y, baslik, kolon, satirlar, gen, h=9.0, lay="ROTAS-TABLO"):
    """sol üst köşe (x,y); kolon başlıkları; gen = kolon genişlikleri (cm). Dönen: alt kenar y"""
    rh = h * 2.0
    W = sum(gen)
    cz.T((x + W / 2, y + h * 1.2), baslik, h * 1.3, lay, TA.BOTTOM_CENTER)
    rows = [kolon] + satirlar
    yy = y
    cz.L((x, yy), (x + W, yy), lay)
    for i, r in enumerate(rows):
        xx = x
        for j, (c, g) in enumerate(zip(r, gen)):
            cz.T((xx + g / 2, yy - rh / 2), str(c), h, lay, TA.MIDDLE_CENTER)
            xx += g
        yy -= rh
        cz.L((x, yy), (x + W, yy), lay)
    xx = x
    for g in [0] + list(gen):
        xx += g
        cz.L((xx, y), (xx, yy), lay)
    cz.engel.append(box(x, yy, x + W, y + h * 3))
    return yy


def basinc_tablosu(cz, x, y, ag, gruplar, yollar, onek):
    kol = ["Kanal", "Debi m³/h", "Ölçü mm", "v m/s", "L m", "R Pa/m", "R·L Pa", "Σζ", "Z Pa", "ΔP Pa"]
    sat = []
    for g in gruplar:
        sat.append([f"{onek}{g['no']}", tr(g["q"]), f"{g['w']}x{g['h']}", tr(g["v"], 2), tr(g["L"], 2), tr(g["R"], 2),
                    tr(g["RL"], 1), tr(g["z"], 2), tr(g["Z"], 1), tr(g["dp"], 1)])
    y2 = tablo(cz, x, y, f"{ag.ad} KANAL BASINÇ KAYBI TABLOSU", kol, sat, [70, 85, 85, 60, 60, 65, 65, 55, 60, 65])
    k = yollar[0]
    yol = []
    n = k["n"]
    while n.e is not None:
        if not yol or yol[-1] != n.e.grup:
            yol.append(n.e.grup)
        n = n.e.a
    yol = "-".join(f"{onek}{g}" for g in reversed(yol))
    uc = "menfez" if k["n"].uc["tip"] in ("tavan", "yan") else k["n"].uc.get("ad", "uç")
    s = [f"KRİTİK HAT: {yol}  ->  kanal {tr(k['kanal'], 1)} Pa + {uc} {tr(k['uc'], 0)} Pa" +
         (f" + flex {tr(k['flex'], 0)} Pa" if k["flex"] else "") + f" = {tr(k['top'], 1)} Pa"]
    for i, t in enumerate(s):
        cz.T((x, y2 - 16 - i * 14), t, 9, "ROTAS-HESAP", TA.MIDDLE_LEFT)
    cz.engel.append(box(x, y2 - 30, x + 700, y2))
    return y2 - 30, k["top"]


def metraj(aglar, duman_aglari=()):
    """ölçü bazında sac metrajı: uzunluk (eksen), çevre, alan m², sac kalınlığı, kg"""
    m = {}
    for ag in aglar:
        for e in ag.kenar:
            dum = ag.tur == "duman" or ag.ad in duman_aglari
            k = (e.w, e.h, sac_kalinligi(max(e.w, e.h), dum))
            m[k] = m.get(k, 0.0) + e.L / 100
    rows = []
    for (w, h, t), L in sorted(m.items(), key=lambda x: (-x[0][0] * x[0][1])):
        c = 2 * (w + h) / 1000
        A = c * L
        rows.append(dict(w=w, h=h, t=t, L=L, cevre=c, A=A, kg=A * t * 7.85))
    return rows


def metraj_tablosu(cz, x, y, rows, ekler=()):
    kol = ["Kanal mm", "Uzunluk m", "Çevre m", "Alan m²", "Sac mm", "Ağırlık kg"]
    sat = [[f"{r['w']}x{r['h']}", tr(r["L"], 2), tr(r["cevre"], 2), tr(r["A"], 2), tr(r["t"], 1), tr(r["kg"], 1)] for r in rows]
    tA = sum(r["A"] for r in rows); tk = sum(r["kg"] for r in rows)
    sat.append(["TOPLAM", "", "", tr(tA, 2), "", tr(tk, 1)])
    for t in sorted(set(r["t"] for r in rows)):
        sat.append([f"{tr(t, 1)} mm sac", "", "", tr(sum(r["A"] for r in rows if r["t"] == t), 2), "", tr(sum(r["kg"] for r in rows if r["t"] == t), 1)])
    y2 = tablo(cz, x, y, "KANAL METRAJI (GALVANİZ SAC)", kol, sat, [95, 80, 70, 80, 65, 85])
    notlar = ["Uzunluklar kanal ekseninden ölçülmüştür; ek yeri, flanş ve fire payı (≈%15) dahil değildir.",
              "Sac kalınlığı: uzun kenar ≤300: 0,5 / ≤750: 0,6 / ≤1200: 0,8 / ≤2000: 1,0 mm (duman kanalında en az 1,0 mm)."] + list(ekler)
    for i, t in enumerate(notlar):
        cz.T((x, y2 - 16 - i * 14), t, 8.5, "ROTAS-HESAP", TA.MIDDLE_LEFT)
    return y2 - 20 - len(notlar) * 14


def lejant(cz, x, y, ogeler):
    """ogeler: [(ad, cizici(cz, p))] satır satır. Sembolün aynısı çizilir"""
    cz.T((x, y + 14), "HAVALANDIRMA TESİSATI SEMBOLLERİ", 13, "ROTAS-TABLO", TA.BOTTOM_LEFT)
    cz.L((x, y + 8), (x + 520, y + 8), "ROTAS-TABLO")
    yy = y - 30
    for ad, f in ogeler:
        f(cz, (x + 70, yy))
        cz.T((x + 170, yy), ad, 9, "ROTAS-TABLO", TA.MIDDLE_LEFT)
        yy -= 55
    cz.engel.append(box(x, yy, x + 520, y + 30))
    return yy


# ------------------------------------------------------------------ teslim öncesi kontrol
def kontrol_raporu(cz, aglar, kolonlar=(), bosluk=5.0):
    """kanallar üst üste binmez, kolonu kesmez, yazılar birbirine binmez. dönen: (hata listesi)"""
    hata = []
    polys = []
    for ag in aglar:
        un = unary_union([e.poly for e in ag.kenar] + [u["kutu"] for u in uc_geometri(ag)])
        polys.append((ag.ad, un))
    for i, (a1, p1) in enumerate(polys):
        for a2, p2 in polys[i + 1:]:
            it = p1.intersection(p2.buffer(bosluk))
            if it.area > 0.5:
                hata.append(f"{a1} / {a2} kanal çakışması {it.bounds}")
        for k in kolonlar:
            if p1.intersection(k).area > 0.1:
                hata.append(f"{a1} kolonu kesiyor {k.bounds}")
    Y = cz.yazi
    for i, g1 in enumerate(Y):
        for g2 in Y[i + 1:]:
            if g1.intersection(g2).area > 0.1:
                hata.append(f"yazı çakışması {g1.bounds}")
        for a, p in polys:
            if g1.intersection(p).area > 0.1:
                hata.append(f"yazı {a} kanalına biniyor {g1.bounds}")
    return hata
