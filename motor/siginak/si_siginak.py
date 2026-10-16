# -*- coding: utf-8 -*-
"""SI_INAK.dwg (market zemin kat) — SIĞINAK A-Z-16 HAVALANDIRMA projesi (duman tahliyeli) — plan 1/50 + şema + kesit + detay + hesap.

Kullanıcı isteği (16.10.2026): "TAZE HAVA KİŞİ BAŞI, EGZOZ %10 ALTINA, DUMAN TAHLİYE 10 HAVA DEĞİŞİMLİ, YÜKSEKLİK 6 m".
  kişi = brüt alan / 1 m²; taze = kişi × kademeli kişi başı debi (motor/siginak/debi.py), 100'e yukarı; egzoz = taze × 0,90;
  duman = brüt × 6,00 × 10 /h, 500'e yukarı. Çıkışlar kullanıcının MTY-BORU dikdörtgeni hizasında batı duvarından
  YAN YANA yatay duvar geçişi ("duvardan atış"); kuranglez yok. Cihazlar tavana asılı. Sığınak içinde WC yok.
Girdi : proje/si_inak_siginak/si_mimari.dxf (SI_INAK.dwg -> dwg2dxf), si_mimari.json (si_mimari.py)
Çıktı : proje/si_inak_siginak/SI_INAK_SIGINAK_HAVALANDIRMA.dxf (R2010, cm, yalnız DXF, mimari + kolonlar içinde)
"""
import json, math, os, pickle, sys
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import Polygon, LineString, Point, box, MultiLineString, GeometryCollection
from shapely.ops import unary_union
from shapely.strtree import STRtree

BURA = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.abspath(os.path.join(BURA, '..', '..'))
sys.path.insert(0, os.path.join(KOK, 'motor', 'deneme', 'kanal'))
sys.path.insert(0, BURA)
import kanal as K                                    # kanal_sec, menfez_sec, surtunme (deneme/kanal modülü)
from debi import siginak_debileri, kisi_basi

PRJ = os.path.join(KOK, 'proje', 'si_inak_siginak')
MIM_DXF = os.path.join(PRJ, 'si_mimari.dxf')
MIM_JSON = os.path.join(PRJ, 'si_mimari.json')       # motor/siginak/si_mimari.py çıktısı
CIKTI = os.path.join(PRJ, 'SI_INAK_SIGINAK_HAVALANDIRMA.dxf')
ALTLIK_KUTU = (259850, -698300, 261850, -694400)    # sığınak plan bölgesi (kontrol / engel bölgesi)
MJ = json.load(open(MIM_JSON))

# ============================================================== HESAP (kullanıcı kuralı 16.10.2026: kişi başı)
HN = 6.00; N_DT = 10; V_GEC = 8.0; ESIK = 100.0     # h = 6,00 m (kullanıcı)
KISI_M2 = 1.0
A_BRUT = 618.2                                      # mimari mahal kutusu: SIĞINAK A-Z-16 618,2 m² (brüt)
X_IC = 260022.0                                     # batı duvarı iç yüzü (duvar 259947..260022)
X_DIS = 259947.0


def yukari(q, adim):
    return int(math.ceil(q / adim - 1e-9) * adim)


def gecis(q):
    """duvar geçişi: v ≤ V_GEC (8 m/s) sınırına en yakın, 10 cm adımlı en küçük kesit; yükseklik ≤ 70"""
    a = q / 3600 / V_GEC * 1e4
    aday = [(b, h) for b in range(30, 210, 10) for h in range(20, 80, 10) if b >= h and b * h >= a]
    b, h = min(aday, key=lambda t: (t[0] * t[1], t[0] - t[1]))
    return b, h, a


def tr(v, n=2):
    return f'{v:,.{n}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def hesap():
    A = A_BRUT
    d = siginak_debileri(A, HN)
    V = A * HN
    return dict(ad='SIĞINAK', A=A, V=V, kisi=d['kisi'], kb=d['kisi_basi'], qth=d['taze_hesap'], qsec=d['taze'], qeg=d['egzoz'],
                qdt=V * N_DT, qdts=d['duman'], dt=A > ESIK,
                gth=gecis(d['taze']), geg=gecis(d['egzoz']), gdt=gecis(d['duman']),
                na=dict(brut=A_BRUT, poligon=Polygon(MJ['sig']).intersection(box(X_IC, -699000, 262000, -694000))))


R = hesap()

# ============================================================== DXF altyapı
doc = ezdxf.new('R2010', setup=True)
doc.header['$INSUNITS'] = 5
doc.header['$LUNITS'] = 2
doc.header['$MEASUREMENT'] = 1
msp = doc.modelspace()
doc.styles.add('ROTAS', font='arial.ttf')
KATMAN = {
    'ROTAS-MIMARI': 8, 'ROTAS-MIMARI-KOLON': 8,
    'ROTAS-HAV-TAZE-HAVA': 3, 'ROTAS-HAV-TAZE-HAVA-GIZLI': 3, 'ROTAS-HAV-EGZOZ': 4, 'ROTAS-HAV-EGZOZ-GIZLI': 4, 'ROTAS-HAV-DUMAN': 1, 'ROTAS-HAV-DUMAN-GIZLI': 1, 'ROTAS-HAV-CIHAZ': 6,
    'ROTAS-HAV-MENFEZ': 7, 'ROTAS-HAV-GECIS': 2, 'ROTAS-HAV-BACA': 8, 'ROTAS-HAV-OK': 7, 'ROTAS-HAV-YAZI': 7,
    'ROTAS-HAV-SEMA': 7, 'ROTAS-HAV-KOT': 7, 'ROTAS-HAV-LEJANT': 7, 'ROTAS-HAV-NOT': 7, 'ROTAS-HAV-BASLIK': 7,
    'ROTAS-HAV-CERCEVE': 7, 'ROTAS-HESAP-CIZGI': 1, 'ROTAS-HESAP-YAZI': 7, 'ROTAS-HESAP-CERCEVE': 1,
}
for n, c in KATMAN.items():
    doc.layers.add(n, color=c, linetype='DASHED' if n.endswith('GIZLI') else 'Continuous')
TAZE, EGZ, DUM, CHZ, MEN, GEC, BACA, OK, YAZI = ('ROTAS-HAV-TAZE-HAVA', 'ROTAS-HAV-EGZOZ', 'ROTAS-HAV-DUMAN',
                                               'ROTAS-HAV-CIHAZ', 'ROTAS-HAV-MENFEZ', 'ROTAS-HAV-GECIS',
                                               'ROTAS-HAV-BACA', 'ROTAS-HAV-OK', 'ROTAS-HAV-YAZI')

CIZ = []          # (LineString, katman)  — kontrol için tüm bizim çizgilerimiz (plan bölgesi)
YAZ = []          # (kutu poligonu, metin) — bizim yazılarımız (plan bölgesi)
ADET = {}


def adet(k, n=1):
    ADET[k] = ADET.get(k, 0) + n


def L(a, b, lay):
    msp.add_line(a, b, dxfattribs={'layer': lay})
    CIZ.append((LineString([a, b]), lay))


def PL(pts, lay, kapali=False, gen=0.0):
    e = msp.add_lwpolyline(pts, close=kapali, dxfattribs={'layer': lay})
    if gen:
        e.dxf.const_width = gen
    p = list(pts) + ([pts[0]] if kapali else [])
    CIZ.append((LineString(p), lay))
    return e


def CIR(c, r, lay):
    msp.add_circle(c, r, dxfattribs={'layer': lay})
    CIZ.append((Point(c).buffer(r, 32).exterior, lay))


def ARC(c, r, a0, a1, lay):
    msp.add_arc(c, r, a0, a1, dxfattribs={'layer': lay})
    n = 16
    pts = [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    CIZ.append((LineString(pts), lay))


def SOLID(pts, lay):
    msp.add_solid(pts if len(pts) == 4 else [pts[0], pts[1], pts[2], pts[2]], dxfattribs={'layer': lay})


def geom(g, lay):
    if g.is_empty:
        return
    if g.geom_type in ('MultiLineString', 'GeometryCollection', 'MultiPolygon'):
        for x in g.geoms:
            geom(x, lay)
    elif g.geom_type == 'LineString':
        PL(list(g.coords), lay)
    elif g.geom_type == 'LinearRing':
        PL(list(g.coords)[:-1], lay, True)
    elif g.geom_type == 'Polygon':
        geom(g.exterior, lay)
        for r in g.interiors:
            geom(r, lay)


def yazi_gen(s, h):
    return len(s) * h * 0.62


def TXT(p, s, h, lay=YAZI, al=TA.MIDDLE_LEFT, rot=0.0, kayit=True):
    t = msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS'})
    t.set_placement(p, align=al)
    if kayit:
        w = yazi_gen(s, h)
        x, y = p
        if al in (TA.MIDDLE_LEFT, TA.LEFT, TA.BOTTOM_LEFT, TA.TOP_LEFT):
            x0 = x
        elif al in (TA.MIDDLE_CENTER, TA.CENTER, TA.BOTTOM_CENTER, TA.TOP_CENTER):
            x0 = x - w / 2
        else:
            x0 = x - w
        if al in (TA.MIDDLE_LEFT, TA.MIDDLE_CENTER, TA.MIDDLE_RIGHT):
            y0 = y - h * 0.5
        elif al in (TA.TOP_LEFT, TA.TOP_CENTER, TA.TOP_RIGHT):
            y0 = y - h
        else:
            y0 = y - h * 0.25
        b = box(x0, y0, x0 + w, y0 + h * 1.1)
        if rot:
            from shapely import affinity
            b = affinity.rotate(b, rot, origin=p)
        YAZ.append((b, s))


def add(p, d, s):
    return (p[0] + d[0] * s, p[1] + d[1] * s)


def birim(a, b):
    L_ = math.dist(a, b)
    return ((b[0] - a[0]) / L_, (b[1] - a[1]) / L_)


def dik(d):
    return (-d[1], d[0])


def rect(a, b, w, ea=0.0, eb=0.0):
    d = birim(a, b); n = dik(d)
    a2 = add(a, d, -ea); b2 = add(b, d, eb)
    return Polygon([add(a2, n, w / 2), add(b2, n, w / 2), add(b2, n, -w / 2), add(a2, n, -w / 2)])


def trap(a, wa, b, wb):
    d = birim(a, b); n = dik(d)
    return Polygon([add(a, n, wa / 2), add(b, n, wb / 2), add(b, n, -wb / 2), add(a, n, -wa / 2)])


# ============================================================== MİMARİ ALTLIK
# Kullanıcının çizimi kaydederken olduğu gibi (kolonlar dahil) aktarılır (mimari_birlestir); burada yalnız sığınak bölgesindeki
# çizgi/yazılar engel ve kontrol için okunur (bloklar patlatılarak: kapı, mahal kutusu, eviye...).
MIM_CIZ = []      # LineString
MIM_YAZI = []     # kutu
KOLON_POLY = [Polygon(p).buffer(0) for p in MJ['betonarme']] + [Polygon(p).buffer(0) for p in MJ['duvar']]
KOLON_U = unary_union(KOLON_POLY).buffer(2.0)
KUTU_G = box(*ALTLIK_KUTU)


def kutuda(p):
    return ALTLIK_KUTU[0] - 300 <= p[0] <= ALTLIK_KUTU[2] + 300 and ALTLIK_KUTU[1] - 300 <= p[1] <= ALTLIK_KUTU[3] + 300


def K_temiz(s):
    import re
    s = re.sub(r'\\[A-Za-z][^;]*;', '', s)
    return s.replace('{', '').replace('}', '').replace('\\P', ' ').replace('%%U', '').strip()


def _gez(es):
    for e in es:
        if e.dxftype() in ('INSERT', 'MULTILEADER', 'DIMENSION'):
            try:
                if e.dxftype() == 'INSERT':
                    for a_ in e.attribs:
                        yield a_
                yield from _gez(e.virtual_entities())
            except Exception:
                pass
        else:
            yield e


def mimari():
    md = ezdxf.readfile(MIM_DXF)
    for e in _gez(md.modelspace()):
        if e.dxf.get('layer') == 'MTY-BORU':          # kullanıcının çıkış hizası işareti (çizime alınmaz)
            continue
        t = e.dxftype()
        try:
            if t == 'LINE':
                a_, b_ = (e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1])
                if math.dist(a_, b_) > 0.01 and (kutuda(a_) or kutuda(b_)):
                    MIM_CIZ.append(LineString([a_, b_]))
            elif t in ('LWPOLYLINE', 'POLYLINE'):
                pts = [(q[0], q[1]) for q in e.get_points()] if t == 'LWPOLYLINE' else [(v.dxf.location[0], v.dxf.location[1]) for v in e.vertices]
                cl = e.closed if t == 'LWPOLYLINE' else e.is_closed
                if len(pts) > 1 and any(kutuda(q) for q in pts):
                    MIM_CIZ.append(LineString(pts + ([pts[0]] if cl else [])))
            elif t in ('ARC', 'CIRCLE'):
                c = (e.dxf.center[0], e.dxf.center[1]); r = e.dxf.radius
                if not kutuda(c):
                    continue
                a0, a1 = (0, 360) if t == 'CIRCLE' else (e.dxf.start_angle, e.dxf.end_angle)
                if a1 < a0: a1 += 360
                MIM_CIZ.append(LineString([(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / 12)),
                                            c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / 12))) for i in range(13)]))
            elif t in ('TEXT', 'ATTRIB', 'MTEXT'):
                x, y = e.dxf.insert[0], e.dxf.insert[1]
                if not kutuda((x, y)):
                    continue
                h = e.dxf.char_height if t == 'MTEXT' else e.dxf.height
                s_ = K_temiz(e.plain_text() if t == 'MTEXT' else e.dxf.text)
                if not s_:
                    continue
                if t == 'MTEXT':
                    w = len(s_) * h * 0.62; ap = e.dxf.get('attachment_point', 1)
                    col, row = (ap - 1) % 3, (ap - 1) // 3
                    x0 = x - w * col / 2; y1 = y + h * 1.2 * row / 2
                    bx = box(x0, y1 - h * 1.2, x0 + w, y1)
                else:
                    if e.dxf.get('halign', 0) or e.dxf.get('valign', 0):
                        x, y = e.dxf.align_point[0], e.dxf.align_point[1]
                        w = len(s_) * h * 0.62 * e.dxf.get('width', 1.0)
                        hl = e.dxf.get('halign', 0)
                        x0 = x - (w / 2 if hl in (1, 4) else w if hl == 2 else 0)
                        bx = box(x0, y - h * 0.8, x0 + w, y + h * 1.05)
                    else:
                        w = len(s_) * h * 0.62 * e.dxf.get('width', 1.0)
                        bx = box(x, y - h * 0.25, x + w, y + h * 1.05)
                    rot = e.dxf.get('rotation', 0.0)
                    if rot:
                        from shapely import affinity
                        bx = affinity.rotate(bx, rot, origin=(x, y))
                MIM_YAZI.append(bx)
        except Exception:
            continue


mimari()
ENGEL_MIM = MIM_CIZ + [g.exterior for g in KOLON_POLY]

# ============================================================== KANAL AĞLARI
# ağ tanımı: kök noktası, kenar listesi (ebeveyn->çocuk), menfezler (düğüm, taraf, debi)
CFG = {
    'taze': dict(lay=TAZE, vmax=8.0, hmax=400, onek='TM', ters=False, mv=2.0),
    'egzoz': dict(lay=EGZ, vmax=8.0, hmax=400, onek='EM', ters=True, mv=2.0),
    'duman': dict(lay=DUM, vmax=8.0, hmax=1000, onek='DM', ters=True, mv=3.0),
}


class Ag:
    def __init__(self, tur, kok):
        self.tur = tur; self.c = CFG[tur]
        self.N = {'K': kok}; self.cocuk = {'K': []}; self.ebe = {}
        self.menfez = []          # (düğüm, taraf vektörü, q)

    def yol(self, ebe, *noktalar, ad=None):
        """ebe düğümünden geçen ortogonal yol; ara noktalar düğüm olur. döner: son düğüm adı"""
        cur = ebe
        for i, p in enumerate(noktalar):
            nm = f'{ad or "n"}{len(self.N)}'
            self.N[nm] = p; self.cocuk[nm] = []; self.cocuk[cur].append(nm); self.ebe[nm] = cur
            cur = nm
        return cur

    def bol(self, a, b, p):
        """a->b kenarını p noktasında böl, yeni düğüm adı"""
        nm = f'm{len(self.N)}'
        self.N[nm] = p
        self.cocuk[a].remove(b); self.cocuk[a].append(nm)
        self.cocuk[nm] = [b]; self.ebe[nm] = a; self.ebe[b] = nm
        return nm

    def menfez_ekle(self, p, taraf, q):
        # p'yi içeren kenarı bul
        for a, ch in list(self.cocuk.items()):
            for b in ch:
                A, B = self.N[a], self.N[b]
                if LineString([A, B]).distance(Point(p)) < 0.01:
                    if math.dist(p, A) < 0.01:
                        nm = a
                    elif math.dist(p, B) < 0.01:
                        nm = b
                    else:
                        nm = self.bol(a, b, p)
                    self.menfez.append((nm, taraf, q))
                    return nm
        raise ValueError(f'menfez noktası kanal üzerinde değil: {p}')

    def akis(self):
        self.Q = {}

        def f(n):
            q = sum(m[2] for m in self.menfez if m[0] == n) + sum(f(c) for c in self.cocuk[n])
            self.Q[n] = q
            return q
        f('K')
        self.olcu = {}
        for n in self.N:
            if n == 'K':
                continue
            q = self.Q[n] + sum(m[2] for m in self.menfez if m[0] == n) * 0  # kenar (ebe->n) debisi = alt ağaç
            self.olcu[n] = K.kanal_sec(self.Q[n], self.c['vmax'], hmax=self.c['hmax'], hmin=150)
        self.ml = {nm: K.menfez_sec(q, v_yuz=self.c['mv'])[0] / 10.0 for nm, t, q in self.menfez if t != 'A'}

    def w(self, n):
        return self.olcu[n]['w'] / 10.0

    # ------------------------------------------------------------ özel parçalar (dirsek / pantolon / T / redüksiyon)
    def _yon(self, a, b):
        return birim(self.N[a], self.N[b])

    def parca(self):
        """kanal gövdesi + iç çizgiler.
        dirsek  : R_iç = 0,5·w kavisli dirsek, w ≥ 25 cm'de yönlendirici kanat (bölme); yer yetmezse köşeli dirsek + kanat dizisi
        pantolon: gövde iki kola ayrılır, ayrım noktasında AYIRICI BÖLME levhası; kollar kavisli, iç bölmeli
        T dal   : yuvarlatılmış ağız (R = 0,5·w_dal) + ayar kanadı (splitter damper)
        redüksiyon: 20 cm konik geçiş. her parça ucunda flanş çizgisi.
        döner: (poligonlar, iç çizgiler, flanş çizgileri)"""
        P = []; IC = []; FL_ = []
        TR = 20.0
        te = {n: 0.0 for n in self.ebe}          # kenar (ebe->n) n ucundan kırpma (+ kısaltır, - uzatır)
        ts = {n: 0.0 for n in self.ebe}          # kenar (ebe->n) ebe ucundan kırpma
        red = {}                                 # n -> (ofs, w_önce) : kenar başında redüksiyon
        self.tip = {}

        def flans(p, d, w, ek=2.5):
            n_ = dik(d)
            FL_.append(LineString([add(p, n_, w / 2 + ek), add(p, n_, -w / 2 - ek)]))

        def arc_pts(C, r, v0, v1, k=14):
            out = []
            for i in range(k + 1):
                f = math.pi / 2 * i / k
                v = (v0[0] * math.cos(f) + v1[0] * math.sin(f), v0[1] * math.cos(f) + v1[1] * math.sin(f))
                out.append(add(C, v, r))
            return out

        def sektor(C, ri, ro, v0, v1):
            return Polygon(arc_pts(C, ro, v0, v1) + arc_pts(C, ri, v0, v1)[::-1])

        def ayni(d1, d2):
            return abs(d1[0] - d2[0]) < 1e-6 and abs(d1[1] - d2[1]) < 1e-6

        for n in self.N:
            ch = self.cocuk[n]
            if n == 'K' or n not in self.ebe:
                continue
            d = self._yon(self.ebe[n], n); W = self.w(n)
            duz = [c for c in ch if ayni(self._yon(n, c), d)]
            yan = [c for c in ch if c not in duz]
            if not ch:
                if n in self.ml:
                    te[n] = -(self.ml[n] / 2 + 5)
                self.tip[n] = 'uc'
                continue
            for c in duz:                                    # düz devam: dal varsa / menfez varsa redüksiyon sonra
                if abs(self.w(c) - W) > 0.01:
                    ofs = max([self.w(y) / 2 + 8 for y in yan] + [0.0])
                    if n in self.ml:
                        ofs = max(ofs, self.ml[n] / 2 + 5)
                    red[c] = (ofs, W)
            if len(yan) == 1 and not duz and abs(sum(x * y for x, y in zip(d, self._yon(n, yan[0])))) <= 0.05:   # ---- DİRSEK
                c = yan[0]; u = self._yon(n, c); we = W
                Lin = math.dist(self.N[self.ebe[n]], self.N[n]); Lout = math.dist(self.N[n], self.N[c])
                ri = 0.5 * we
                bos = min(Lin * (0.5 if self.ebe[n] != 'K' else 0.8), Lout * (0.5 if self.cocuk[c] else 0.8)) - we / 2
                ri = max(0.0, min(ri, bos))
                p = self.N[n]
                if ri >= 0.25 * we:
                    self.tip[n] = 'dirsek'
                    m = we / 2 + ri
                    C = add(add(p, d, -m), u, m)
                    P.append(sektor(C, ri, ri + we, (-u[0], -u[1]), d))
                    te[n] = m; ts[c] = m
                    if we >= 25:
                        nv = 2 if we >= 60 else 1
                        for k in range(1, nv + 1):
                            IC.append(LineString(arc_pts(C, ri + we * k / (nv + 1), (-u[0], -u[1]), d)))
                    flans(add(p, d, -m), d, we); flans(add(p, u, m), u, we)
                    if abs(self.w(c) - we) > 0.01:
                        red[c] = (m, we)
                else:                                        # köşeli dirsek + yönlendirici kanat dizisi
                    self.tip[n] = 'kose'
                    te[n] = -we / 2; ts[c] = -we / 2
                    ic_k = add(add(p, d, -we / 2), u, we / 2); dis_k = add(add(p, d, we / 2), u, -we / 2)
                    nv = max(2, int(we // 12))
                    r = we / (nv + 1) * 0.75
                    for k in range(1, nv + 1):
                        f = k / (nv + 1)
                        q = (ic_k[0] + (dis_k[0] - ic_k[0]) * f, ic_k[1] + (dis_k[1] - ic_k[1]) * f)
                        st = add(add(q, d, -r / 2), u, -r / 2)
                        C = add(st, u, r)
                        IC.append(LineString(arc_pts(C, r, (-u[0], -u[1]), d, 8)))
                    flans(add(p, d, -we / 2 - 2), d, we); flans(add(p, u, we / 2 + 2), u, we)
                    if abs(self.w(c) - we) > 0.01:
                        red[c] = (we / 2, we)
            elif len(yan) == 2 and not duz:                  # ---- PANTOLON (gövde debi oranında iki kola bölünür)
                self.tip[n] = 'pantolon'
                cL, cR = yan; u = self._yon(n, cL)
                qL, qR = self.Q[cL], self.Q[cR]
                aL = min(max(12.0, round(W * qL / (qL + qR))), W - 12.0); aR = W - aL
                p = self.N[n]
                riL, riR = 0.5 * aL, 0.5 * aR
                sCL = -riL - aL / 2; sCR = -riR - aR / 2
                tc = W / 2 - aL
                sm = min(sCL, sCR)
                CL = add(add(p, d, sCL), u, W / 2 + riL)
                CR = add(add(p, d, sCR), u, -(W / 2 + riR))
                mu = (-u[0], -u[1])
                P.append(sektor(CL, riL, riL + aL, mu, d))
                P.append(sektor(CR, riR, riR + aR, u, d))
                for (sC, t0, t1) in ((sCL, tc, W / 2), (sCR, -W / 2, tc)):
                    if sC - sm > 0.01:
                        a0 = add(add(p, d, sm), u, (t0 + t1) / 2); b0 = add(add(p, d, sC), u, (t0 + t1) / 2)
                        P.append(rect(a0, b0, t1 - t0))
                te[n] = -sm
                ts[cL] = W / 2 + riL; ts[cR] = W / 2 + riR
                if abs(self.w(cL) - aL) > 0.01:
                    red[cL] = (ts[cL], aL)
                if abs(self.w(cR) - aR) > 0.01:
                    red[cR] = (ts[cR], aR)
                # ayırıcı bölme levhası (gövde içine uzanır, ucunda ayar mafsalı) + kollarda yönlendirici kanat
                Lb = min(0.9 * W, math.dist(self.N[self.ebe[n]], p) + sm - 15)
                ust = sm - Lb
                IC.append(LineString([add(add(p, d, ust), u, tc), add(add(p, d, sm), u, tc)]))
                self.bolme = getattr(self, 'bolme', []) + [(add(add(p, d, ust + Lb * 0.4), u, tc), add(add(p, d, sm), u, tc))]
                for C, ri, ww, v0 in ((CL, riL, aL, mu), (CR, riR, aR, u)):
                    if ww >= 25:
                        IC.append(LineString(arc_pts(C, ri + ww / 2, v0, d)))
                flans(add(p, d, sm), d, W)
                flans(add(p, u, W / 2 + riL), u, aL); flans(add(p, u, -(W / 2 + riR)), (-u[0], -u[1]), aR)
            elif len(yan) == 1 and not duz and abs(sum(x * y for x, y in zip(d, self._yon(n, yan[0])))) > 0.05:   # ---- OFSET (45°)
                self.tip[n] = 'ofset'
                c = yan[0]; u = self._yon(n, c); p = self.N[n]
                from shapely.ops import unary_union as _uu
                P.append(_uu([rect(add(p, d, -2), p, W), rect(p, add(p, u, 2), self.w(c))]).convex_hull)
                flans(add(p, d, -W * 0.45), d, W); flans(add(p, u, W * 0.45), u, self.w(c))
            else:                                            # ---- T DAL (düz devam + yan dal)
                for c in yan:
                    self.tip[n] = 'T'
                    u = self._yon(n, c); wb = self.w(c); p = self.N[n]
                    ts[c] = W / 2
                    rf = min(0.5 * wb, 25.0)
                    # yuvarlatılmış ağız: kare - çeyrek daire (akış yukarısı tarafı)
                    k0 = add(add(p, d, -wb / 2), u, W / 2)
                    kare = Polygon([k0, add(k0, d, -rf), add(add(k0, d, -rf), u, rf), add(k0, u, rf)])
                    P.append(kare.difference(Point(add(add(k0, d, -rf), u, rf)).buffer(rf, 32)))
                    # ayar kanadı: dalın akış aşağısı köşesinde mafsal, gövdeye eğik uzanır
                    h0 = add(add(p, d, wb / 2), u, W / 2)
                    h1 = add(add(h0, d, -0.55 * wb), u, -min(0.45 * W, 0.5 * wb))
                    IC.append(LineString([h0, h1]))
                    flans(add(p, u, W / 2 + rf), u, wb)
        # kenar gövdeleri
        self.duz = {}
        for n, e in self.ebe.items():
            a, b = self.N[e], self.N[n]
            d = birim(a, b); w = self.w(n)
            a2 = add(a, d, ts[n]); b2 = add(b, d, -te[n])
            if n in red:
                ofs, w0 = red[n]
                s0 = max(ofs, ts[n])
                t0 = add(a, d, s0); t1 = add(a, d, s0 + TR)
                if s0 > ts[n] + 0.01:
                    P.append(rect(a2, t0, w0))
                P.append(trap(t0, w0, t1, w))
                flans(t1, d, w)
                a2 = t1
            if math.dist(a, b2) - math.dist(a, a2) < -0.5:
                print('UYARI parça sığmıyor', self.tur, e, n, round(math.dist(a, b), 1), round(ts[n], 1), round(te[n], 1))
            P.append(rect(a2, b2, w))
            self.duz[n] = (a2, b2)
        return P, IC, FL_

def menfez_yan(ag, nm, taraf, q, no):
    """kanal yanağı menfezi: kanal yanağına dayalı 3 kenar + kanatlar + hava yönü okları"""
    p = ag.N[nm]; e = ag.ebe[nm] if nm in ag.ebe else ag.cocuk[nm][0]
    a = ag.N[e]
    d = birim(a, p) if nm in ag.ebe else birim(p, ag.N[e])
    w = ag.w(nm) if nm in ag.ebe else ag.w(e)
    n = taraf
    mw, mh, mv = K.menfez_sec(q, v_yuz=ag.c['mv'])
    ml = mw / 10.0
    c0 = add(p, n, w / 2)
    A = add(c0, d, -ml / 2); B = add(c0, d, ml / 2)
    A2 = add(A, n, 10); B2 = add(B, n, 10)
    PL([A, A2, B2, B], MEN)
    k = 4.0
    while k < ml - 3:
        x = add(A, d, k)
        L(add(x, n, 1.5), add(add(x, n, 8.5), d, -3), MEN)
        k += 5.0
    for f_ in (0.3, 0.7):
        x = add(A, d, ml * f_)
        o1, o2 = add(x, n, 13), add(x, n, 27)
        if ag.c['ters']:
            ok_acik(o2, o1, MEN, 5)
        else:
            ok_acik(o1, o2, MEN, 5)
    adet(f'menfez_{ag.tur}')
    poly = Polygon([A, A2, B2, B]).union(LineString([add(A, n, 10), add(add(A, n, 30), d, ml)]).buffer(0.1).envelope)
    return dict(no=f"{ag.c['onek']}-{no}", q=q, mw=mw, mh=mh, v=mv, p=add(c0, n, 18), n=n, d=d, ml=ml, govde=poly)


def ok_acik(a, b, lay, bas=4.0):
    L(a, b, lay)
    d = birim(a, b); n = dik(d)
    k = add(b, d, -bas)
    L(b, add(k, n, bas * 0.45), lay); L(b, add(k, n, -bas * 0.45), lay)


def ok_dolu(p, d, Lk, lay=OK):
    n = dik(d)
    tip = add(p, d, Lk / 2); b = add(p, d, -Lk / 2)
    SOLID([tip, add(b, n, Lk * 0.3), add(b, n, -Lk * 0.3)], lay)


# ---------------------------------------------------------------- semboller (saf geometri)
def gsk(c, d, w, lay=CHZ):
    """gaz sızdırmaz klape: flanşlı gövde + eğik disk + mil + dış kol + topuz. d akış yönü, w kanal genişliği"""
    n = dik(d); Lg = 28.0
    W = w + 8
    a1 = add(add(c, d, -Lg / 2), n, W / 2); a2 = add(add(c, d, -Lg / 2), n, -W / 2)
    b1 = add(add(c, d, Lg / 2), n, W / 2); b2 = add(add(c, d, Lg / 2), n, -W / 2)
    body = Polygon([a1, b1, b2, a2])
    PL([a1, b1, b2, a2], lay, True)
    # flanş çizgileri
    for s in (-Lg / 2 + 4, Lg / 2 - 4):
        L(add(add(c, d, s), n, W / 2), add(add(c, d, s), n, -W / 2), lay)
    # disk (kapalı konumda eğik)
    L(add(add(c, d, -6), n, W / 2 - 5), add(add(c, d, 6), n, -W / 2 + 5), lay)
    CIR(c, 2.5, lay)
    # kol
    k1 = add(c, n, W / 2); k2 = add(add(c, n, W / 2 + 18), d, -10)
    L(k1, k2, lay); CIR(add(k2, birim(k1, k2), 3), 3, lay)
    adet('gsk')
    return body.union(Point(add(k2, birim(k1, k2), 3)).buffer(3.5)).union(LineString([k1, k2]).buffer(0.5))


def kovan(a_ic, d_dis, wb, lay=GEC):
    """perde/duvar geçişi çelik kovan: a_ic duvar iç yüzü üzerindeki eksen noktası, d_dis dışarı yön, wb plan genişliği.
    kovan iç ve dış yüzden 5 cm taşar; çift çizgi (kovan sacı) + ortada geçiş ölçüsü yok (etiket ayrı)."""
    n = dik(d_dis)
    return d_dis, n


def kovan_ciz(ic, dis, wb, lay=GEC):
    d = birim(ic, dis); n = dik(d)
    a = add(ic, d, -5); b = add(dis, d, 5)
    o = Polygon([add(a, n, wb / 2), add(b, n, wb / 2), add(b, n, -wb / 2), add(a, n, -wb / 2)])
    PL(list(o.exterior.coords)[:-1], lay, True)
    i1 = [add(add(a, d, 2), n, wb / 2 - 2), add(add(b, d, -2), n, wb / 2 - 2)]
    i2 = [add(add(a, d, 2), n, -wb / 2 + 2), add(add(b, d, -2), n, -wb / 2 + 2)]
    L(*i1, lay); L(*i2, lay)
    adet('kovan')
    return o


def baca_ciz(c, wx, wy, lay=BACA):
    """dış hava bacası (toprak içinde betonarme şaft): dikdörtgen + çapraz (şaft gösterimi)"""
    x0, y0, x1, y1 = c[0] - wx / 2, c[1] - wy / 2, c[0] + wx / 2, c[1] + wy / 2
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, True)
    PL([(x0 + 6, y0 + 6), (x1 - 6, y0 + 6), (x1 - 6, y1 - 6), (x0 + 6, y1 - 6)], lay, True)
    L((x0 + 6, y0 + 6), (x1 - 6, y1 - 6), lay); L((x0 + 6, y1 - 6), (x1 - 6, y0 + 6), lay)
    adet('baca')
    return box(x0, y0, x1, y1)


def fan_aksiyel(c, d, Rr, lay=CHZ):
    """aksiyel duman tahliye fanı: silindirik gövde (yan görünüş dikdörtgen) + motor + çark daire + papyon kanat"""
    n = dik(d)
    g = rect(add(c, d, -Rr * 1.2), add(c, d, Rr * 1.2), 2 * Rr + 8)
    geom(g, lay)
    # flanşlar
    for s in (-Rr * 1.2 + 5, Rr * 1.2 - 5):
        L(add(add(c, d, s), n, Rr + 4), add(add(c, d, s), n, -Rr - 4), lay)
    CIR(c, Rr * 0.8, lay)
    a1, a2 = add(c, n, Rr * 0.7), add(c, n, -Rr * 0.7)
    PL([c, add(a1, d, -Rr * 0.3), add(a1, d, Rr * 0.3)], lay, True)
    PL([c, add(a2, d, -Rr * 0.3), add(a2, d, Rr * 0.3)], lay, True)
    adet('fan_duman')
    return g


def fan_kanal(c, d, Lb, Wb, lay=CHZ):
    """kanal tipi (inline) radyal egzoz fanı: kutu gövde + salyangoz + çark + motor"""
    n = dik(d)
    g = rect(add(c, d, -Lb / 2), add(c, d, Lb / 2), Wb)
    geom(g, lay)
    r = min(Lb, Wb) * 0.30
    CIR(c, r, lay); CIR(c, r * 0.35, lay)
    # salyangoz (spiral)
    pts = []
    for i in range(0, 41):
        t = i / 40 * 2 * math.pi * 0.9
        rr = r * (1.15 + 0.25 * t / (2 * math.pi))
        pts.append(add(add(c, d, rr * math.cos(t)), n, rr * math.sin(t)))
    PL(pts, lay)
    for k in range(6):
        t = k * math.pi / 3
        p1 = add(add(c, d, r * 0.4 * math.cos(t)), n, r * 0.4 * math.sin(t))
        p2 = add(add(c, d, r * 0.9 * math.cos(t + 0.4)), n, r * 0.9 * math.sin(t + 0.4))
        L(p1, p2, lay)
    adet('fan_egzoz')
    return g


def shc(c, Wx, Wy, lay=CHZ):
    """sığınak havalandırma cihazı (koruma havalandırması): giriş + toz filtre + kum filtre (by-pass damperli) + radyal fan
    (el kolu + elektrik motoru). c merkez, plan x-genişliği Wx, y-derinliği Wy. Giriş üstte (kuzey), çıkış altta (güney)."""
    x0, y0, x1, y1 = c[0] - Wx / 2, c[1] - Wy / 2, c[0] + Wx / 2, c[1] + Wy / 2
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, True)
    # bölmeler: [toz filtre | kum filtre | fan]
    xa, xb = x0 + Wx * 0.28, x0 + Wx * 0.58
    L((xa, y0), (xa, y1), lay); L((xb, y0), (xb, y1), lay)
    # toz filtre: pileli zikzak
    pts = []
    k = 0
    yy = y1 - 6
    while yy > y0 + 6:
        pts.append((x0 + 8 if k % 2 == 0 else xa - 8, yy)); yy -= 6; k += 1
    PL(pts, lay)
    # kum filtre: kum yatağı noktaları (küçük daireler)
    for i in range(5):
        for j in range(4):
            CIR((xa + 7 + i * (xb - xa - 14) / 4, y0 + 9 + j * (Wy - 18) / 3), 1.2, lay)
    # by-pass damper (kum filtre bölmesi üstünde eğik kanat + pivot)
    # fan: daire + kanat
    fc = ((xb + x1) / 2 - 6, (y0 + y1) / 2)
    rr = min(x1 - xb, Wy) * 0.3
    CIR(fc, rr, lay); CIR(fc, rr * 0.3, lay)
    for k in range(6):
        t = k * math.pi / 3
        L((fc[0] + rr * 0.3 * math.cos(t), fc[1] + rr * 0.3 * math.sin(t)),
          (fc[0] + rr * 0.95 * math.cos(t + 0.5), fc[1] + rr * 0.95 * math.sin(t + 0.5)), lay)
    # el kolu (cihazın doğu yüzünde): mil + krank + topuz
    m0 = (x1, fc[1]); m1 = (x1 + 14, fc[1]); m2 = (x1 + 14, fc[1] + 16)
    PL([m0, m1, m2], lay); CIR((m2[0] + 3.5, m2[1]), 3.5, lay)
    # elektrik motoru (fan bölmesinde, kutu + M)
    mb = (x1 - 16, y0 + 4, x1 - 4, y0 + 18)
    PL([(mb[0], mb[1]), (mb[2], mb[1]), (mb[2], mb[3]), (mb[0], mb[3])], lay, True)
    TXT(((mb[0] + mb[2]) / 2, (mb[1] + mb[3]) / 2), 'M', 7, lay, TA.MIDDLE_CENTER, kayit=False)
    adet('shc')
    return box(x0, y0, x1 + 18, y1).union(Point((m2[0] + 3.5, m2[1])).buffer(4))


def shc_yatay(c, Lb, Wb, d, lay=CHZ):
    """sığınak havalandırma cihazı, akış d yönünde (giriş arkada): [toz filtre | kum filtre (by-pass) | fan + motor] + el kolu"""
    n = dik(d)
    G = lambda s_, t_: add(add(c, d, s_), n, t_)
    PL([G(-Lb / 2, -Wb / 2), G(Lb / 2, -Wb / 2), G(Lb / 2, Wb / 2), G(-Lb / 2, Wb / 2)], lay, True)
    sa, sb = -Lb / 2 + Lb * 0.28, -Lb / 2 + Lb * 0.58
    L(G(sa, -Wb / 2), G(sa, Wb / 2), lay); L(G(sb, -Wb / 2), G(sb, Wb / 2), lay)
    pts = []; t_ = -Wb / 2 + 6; k = 0
    while t_ < Wb / 2 - 6:
        pts.append(G(-Lb / 2 + 8 if k % 2 == 0 else sa - 8, t_)); t_ += 7; k += 1
    PL(pts, lay)
    for i in range(5):
        for j in range(4):
            CIR(G(sa + 7 + i * (sb - sa - 14) / 4, -Wb / 2 + 10 + j * (Wb - 20) / 3), 1.4, lay)
    fc = G((sb + Lb / 2) / 2 - 4, 0); rr = min(Lb / 2 - sb, Wb) * 0.32
    CIR(fc, rr, lay); CIR(fc, rr * 0.3, lay)
    for k in range(6):
        a_ = k * math.pi / 3
        L(add(fc, (math.cos(a_), math.sin(a_)), rr * 0.3), add(fc, (math.cos(a_ + 0.5), math.sin(a_ + 0.5)), rr * 0.95), lay)
    m0 = G(Lb / 2 - 30, Wb / 2); m1 = G(Lb / 2 - 30, Wb / 2 + 14); m2 = G(Lb / 2 - 14, Wb / 2 + 14)
    PL([m0, m1, m2], lay); CIR(add(m2, d, 3.5), 3.5, lay)
    mb = [G(Lb / 2 - 18, -Wb / 2 + 4), G(Lb / 2 - 4, -Wb / 2 + 4), G(Lb / 2 - 4, -Wb / 2 + 18), G(Lb / 2 - 18, -Wb / 2 + 18)]
    PL(mb, lay, True)
    TXT(G(Lb / 2 - 11, -Wb / 2 + 11), 'M', 7, lay, TA.MIDDLE_CENTER, kayit=False)
    adet('shc')
    return Polygon([G(-Lb / 2, -Wb / 2), G(Lb / 2, -Wb / 2), G(Lb / 2, Wb / 2 + 18), G(-Lb / 2, Wb / 2 + 18)])


# ============================================================== PLAN YERLEŞİMİ
q_th, q_eg, q_dt = R['qsec'], R['qeg'], R['qdts']
n_tm, n_em, n_dm = 14, 12, 12
S, N_, E, W_ = (0, -1), (0, 1), (1, 0), (-1, 0)
TAZE_Q = q_th / n_tm; EGZ_Q = q_eg / n_em; DUM_Q = q_dt / n_dm
WC_Q = 0.0                                           # sığınak içinde WC yok

# ---- ÇIKIŞLAR: kullanıcının gösterdiği hiza = batı duvarı (259947..260022), kolonlar arası y -694815..-695230.
#      "Duvardan atış": üç yatay duvar geçişi YAN YANA (kuzeyden güneye DUMAN / TAZE / EGZOZ), dışta panjurlu ağız.
Y_D, Y_T, Y_E = -694925, -695080, -695170
X_GSK, X_K = 260060, 260074
X_E, X_T, X_D1, X_T1, X_D2, X_T2, X_E2 = 260225, 260300, 260590, 260720, 261120, 261450, 261560
Y_TF, Y_EF, Y_DEND = -697720, -697790, -697450    # taze / egzoz güney toplayıcıları (giriş holü ve orta aks kolonu arasından)


def dal(ag, p, *noktalar):
    """p noktasını içeren kenarı böl, oradan yeni yol"""
    for a_, ch in list(ag.cocuk.items()):
        for b_ in ch:
            A_, B_ = ag.N[a_], ag.N[b_]
            if LineString([A_, B_]).distance(Point(p)) < 0.01 and math.dist(A_, p) > 0.01 and math.dist(B_, p) > 0.01:
                nm = ag.bol(a_, b_, p)
                return ag.yol(nm, *noktalar)
    raise ValueError(p)


# ---- duman: duvar -> GSK-2 -> DTF-1 -> T (X_D1): batı bölme gövdesi D1 / doğu: orta aks kolonları arasından D2
du = Ag('duman', (X_K, Y_D))
dT = du.yol('K', (X_D1, Y_D))
du.yol(dT, (X_D1, Y_DEND))
du.yol(dT, (X_D2, Y_D), (X_D2, Y_DEND))
for x_ in (X_D1, X_D2):
    for y_, t_ in zip((-695350, -695800, -696250, -696700, -697150, -697450), (E, W_, E, W_, E, W_)):
        du.menfez_ekle((x_, y_), t_, DUM_Q)

# ---- taze: duvar -> GSK-1 -> SHC-1 (düşey kol üzerinde) -> güney toplayıcı -> T1 (batı bölme) / T2 (doğu bölme)
ta = Ag('taze', (X_K, Y_T))
t1 = ta.yol('K', (X_T, Y_T))
tf = ta.yol(t1, (X_T, Y_TF))
ta.yol(tf, (X_T2, Y_TF), (X_T2, -694900))
dal(ta, (X_T1, Y_TF), (X_T1, -695500))
for p, t in [((X_T, -696000), E), ((X_T, -696700), E), ((X_T, -697400), E),
             ((X_T1, -695500), E), ((X_T1, -696100), W_), ((X_T1, -696700), E), ((X_T1, -697300), W_),
             ((X_T2, -694900), W_), ((X_T2, -695400), W_), ((X_T2, -695900), W_), ((X_T2, -696400), W_), ((X_T2, -696900), W_), ((X_T2, -697400), W_),
             ((261000, Y_TF), N_)]:
    ta.menfez_ekle(p, t, TAZE_Q)

# ---- egzoz: duvar -> GSK-3 -> EF-1 (düşey kol üzerinde) <- batı kolu <- güney toplayıcı <- doğu kolu E2
eg = Ag('egzoz', (X_K, Y_E))
e1 = eg.yol('K', (X_E, Y_E))
ef = eg.yol(e1, (X_E, Y_EF))
eg.yol(ef, (X_E2, Y_EF), (X_E2, -694850))
for p, t in [((X_E, -695700), W_), ((X_E, -696100), W_), ((X_E, -696900), W_), ((X_E, -697400), W_),
             ((260500, Y_EF), S), ((261300, Y_EF), S),
             ((X_E2, -694850), W_), ((X_E2, -695350), W_), ((X_E2, -695850), W_), ((X_E2, -696350), W_), ((X_E2, -696850), W_), ((X_E2, -697350), W_)]:
    eg.menfez_ekle(p, t, EGZ_Q)

for ag in (ta, du, eg):
    ag.akis()

# ---- bileşen gövdeleri
GOVDE = []
gth_b, gth_h, _ = R['gth']; gdt_b, gdt_h, _ = R['gdt']; geg_b, geg_h, _ = R['geg']


def panjur(y, b, disari, lay=GEC):
    """dış ağız: duvar dış yüzünde panjur kanatları + hava yönü oku (dışarıda)"""
    for k in range(int(b // 10)):
        yy = y - b / 2 + 5 + k * 10
        L((X_DIS + 3, yy - 3), (X_DIS + 11, yy + 3), lay)
    if disari:
        ok_acik((X_DIS - 12, y), (X_DIS - 62, y), OK, 8)
    else:
        ok_acik((X_DIS - 62, y), (X_DIS - 12, y), OK, 8)


k_dt = kovan_ciz((X_IC, Y_D), (X_DIS, Y_D), gdt_b); panjur(Y_D, gdt_b, True)
k_th = kovan_ciz((X_IC, Y_T), (X_DIS, Y_T), gth_b); panjur(Y_T, gth_b, False)
k_eg = kovan_ciz((X_IC, Y_E), (X_DIS, Y_E), geg_b); panjur(Y_E, geg_b, True)
gsk_th = gsk((X_GSK, Y_T), E, ta.w(ta.cocuk['K'][0]))
gsk_dt = gsk((X_GSK, Y_D), W_, du.w(du.cocuk['K'][0]))
gsk_eg = gsk((X_GSK, Y_E), W_, eg.w(eg.cocuk['K'][0]))
SHC_C = (X_T, -695450)
shc_g = shc_yatay(SHC_C, 130, 100, S)
DF_C = (260230, Y_D)
fan_dt = fan_aksiyel(DF_C, W_, du.w(du.cocuk['K'][0]) / 2 + 4)
EF_C = (X_E, -695290)
fan_eg = fan_kanal(EF_C, N_, 90, 60)
GOVDE += [k_th, gsk_th, shc_g, k_dt, gsk_dt, fan_dt, k_eg, gsk_eg, fan_eg]
AN_R = 15.0


def bag(y, b, ag):
    w0 = ag.w(ag.cocuk['K'][0])
    return [trap((X_IC + 2, y), b - 4, (X_GSK + 14, y), w0)]


bag_th = bag(Y_T, gth_b, ta); bag_dt = bag(Y_D, gdt_b, du); bag_eg = bag(Y_E, geg_b, eg)
GOVDE_U = unary_union(GOVDE)

def ag_ciz(ag, ekler=(), alt=None):
    """kanalı çiz; alt verilirse o gövdeler (üstten geçen kanallar) içindeki çizgiler GİZLİ (kesikli) katmana"""
    P, IC, FLN = ag.parca()
    P = P + list(ekler)
    k = ag.N['K']; c0 = ag.cocuk['K'][0]
    d = birim(k, ag.N[c0])
    P.append(rect(add(k, d, -8), k, ag.w(c0)))
    U = unary_union(P).buffer(0)
    cizgi = U.boundary.difference(GOVDE_U.buffer(0.01))
    ic = unary_union(IC + FLN).difference(GOVDE_U.buffer(0.01)) if IC or FLN else GeometryCollection()
    if alt is not None:
        gz = cizgi.intersection(alt.buffer(-0.01)); cizgi = cizgi.difference(alt.buffer(-0.01))
        gz2 = ic.intersection(alt.buffer(-0.01)); ic = ic.difference(alt.buffer(-0.01))
        for g_ in (gz, gz2):
            for x in (g_.geoms if hasattr(g_, 'geoms') else [g_]):
                if x.geom_type == 'LineString' and x.length > 0.3:
                    e = msp.add_lwpolyline(list(x.coords), dxfattribs={'layer': ag.c['lay'] + '-GIZLI', 'ltscale': 15.0})
                    CIZ.append((x, ag.c['lay'] + '-GIZLI'))
    geom(cizgi, ag.c['lay'])
    geom(ic, ag.c['lay'])
    ag.U = U
    # akış okları: düz kısım ortasında
    for n, (a, b) in ag.duz.items():
        Lk = math.dist(a, b)
        if Lk < 60:
            continue
        dd = birim(a, b)
        if ag.c['ters']:
            dd = (-dd[0], -dd[1])
        m = add(a, birim(a, b), Lk * 0.5)
        if ag.menfez and any(math.dist(m, ag.N[mm[0]]) < ag.ml.get(mm[0], 2 * AN_R) / 2 + 12 for mm in ag.menfez):
            m = add(a, birim(a, b), Lk * 0.25)
        ok_dolu(m, dd, min(14, ag.w(n) * 0.6))
    return U


U_ta = ag_ciz(ta, bag_th)
U_du = ag_ciz(du, bag_dt, alt=U_ta)
U_eg = ag_ciz(eg, bag_eg, alt=unary_union([U_ta, U_du]))

def anemostad(ag, nm, q, no):
    """WC egzoz anemostadı (tavan, dairesel Ø160 boyun / Ø300 panel): 3 halka + emiş okları"""
    c = ag.N[nm]
    for r in (AN_R, AN_R * 0.66, AN_R * 0.33):
        CIR(c, r, MEN)
    for v in ((1, 1), (-1, -1)):
        u_ = (v[0] / math.sqrt(2), v[1] / math.sqrt(2))
        ok_acik(add(c, u_, AN_R + 12), add(c, u_, AN_R + 2), MEN, 4)
    adet('anemostad')
    v = q / 3600 / (math.pi * 0.08 ** 2)
    return dict(no=f"EA-{no}", q=q, mw='Ø160', mh='', v=v, p=add(c, (0, 1), AN_R), n=(0, 1), d=(1, 0), ml=2 * AN_R,
                govde=Point(c).buffer(AN_R + 13), an=True)


MENFEZLER = []
for ag in (ta, du, eg):
    i = 0; j = 0
    for nm, t, q in ag.menfez:
        if t == 'A':
            j += 1; MENFEZLER.append((ag, anemostad(ag, nm, q, j)))
        else:
            i += 1; MENFEZLER.append((ag, menfez_yan(ag, nm, t, q, i)))

# ============================================================== ETİKET YERLEŞİMİ
ENGEL = []


def engel_guncelle():
    global AGAC, ENGEL_G
    ENGEL_G = [g for g in ENGEL_MIM] + [g for g, _ in CIZ] + [b for b in MIM_YAZI] + [b for b, _ in YAZ] + \
              [ag.U for ag in (ta, du, eg)] + list(GOVDE) + [m['govde'] for _, m in MENFEZLER]
    AGAC = STRtree(ENGEL_G)
    global AGAC_B, ENGEL_B
    ENGEL_B = [g for g, _ in CIZ] + [b for b, _ in YAZ] + [b for b in MIM_YAZI] + [ag.U for ag in (ta, du, eg)] + list(GOVDE) + \
              [m['govde'] for _, m in MENFEZLER] + [g.exterior for g in KOLON_POLY]
    AGAC_B = STRtree(ENGEL_B)


def serbest(g):
    for i in AGAC.query(g):
        if ENGEL_G[i].intersects(g):
            return False
    return True


def serbest_b(g):
    for i in AGAC_B.query(g):
        if ENGEL_B[i].intersects(g):
            return False
    return True


SIG_ALAN = R['na']['poligon']


def plan_icinde(g):
    return SIG_ALAN.buffer(-2).contains(g)


def etiket(anchor, satirlar, h, lay=YAZI, oncelik=(), rmax=260, leader=True, alan=None, haric=None):
    """satırlar bloğunu anchor yakınında serbest yere koy (yatay); uzak kalırsa kılavuz çizgisi"""
    W = max(yazi_gen(s, h) for s in satirlar) + 4
    H = len(satirlar) * h * 1.5
    adaylar = list(oncelik)
    for r in range(12, rmax, 8):
        for k in range(24):
            a = 2 * math.pi * k / 24
            adaylar.append((anchor[0] + r * math.cos(a), anchor[1] + r * math.sin(a)))
    for c in adaylar:
        b = box(c[0] - W / 2, c[1] - H / 2, c[0] + W / 2, c[1] + H / 2)
        if alan is not None and not alan.contains(b):
            continue
        if not serbest(b.buffer(2)):
            continue
        ln = None
        if leader and b.distance(Point(anchor)) > 6:
            q = b.exterior.interpolate(b.exterior.project(Point(anchor)))
            ln = LineString([anchor, (q.x, q.y)])
            # kılavuz başka çizgiyi/yazıyı kesmesin
            kisa = LineString([ln.interpolate(3), ln.interpolate(ln.length - 1)]) if ln.length > 5 else None
            if kisa is not None and haric is not None:
                kisa = kisa.difference(haric.buffer(1.5))
            if kisa is not None and not kisa.is_empty and not serbest_b(kisa):
                continue
        for i, s in enumerate(satirlar):
            yy = c[1] + H / 2 - h * 1.5 * (i + 0.5)
            TXT((c[0], yy), s, h, lay, TA.MIDDLE_CENTER, kayit=False)
        YAZ.append((b, ' / '.join(satirlar)))
        if ln is not None:
            if haric is not None:
                lk = ln.difference(haric)
                lk = max(lk.geoms, key=lambda g: g.length) if hasattr(lk, 'geoms') else lk
                if lk.length > 1:
                    L(lk.coords[0], lk.coords[-1], lay)
                    if Point(lk.coords[0]).distance(Point(anchor)) < 0.5:
                        CIR(anchor, 1.2, lay)
            else:
                L(ln.coords[0], ln.coords[-1], lay)
                CIR(anchor, 1.2, lay)
        engel_guncelle()
        return b
    print('UYARI: etiket yeri yok', satirlar)
    return None


engel_guncelle()

# kanal etiketleri: aynı ölçülü ardışık kenarlar tek etiket
KANAL_ETIKET = []


def dik_etiket(ag, n, s1, h=8.0):
    """yer bulunamazsa: kanala paralel (döndürülmüş) yazı, kanalın hemen yanında"""
    a, b = ag.duz.get(n, (ag.N[ag.ebe[n]], ag.N[n]))
    d = birim(a, b); nn = dik(d); w = ag.w(n)
    Lw = yazi_gen(s1, h)
    if math.dist(a, b) < Lw + 20:
        return None
    rot = math.degrees(math.atan2(d[1], d[0]))
    if rot > 90 or rot <= -90:
        rot += 180
    for f in (0.5, 0.3, 0.7, 0.2, 0.8):
        for sgn in (1, -1):
            c = add(add(a, d, math.dist(a, b) * f), nn, sgn * (w / 2 + h * 0.9))
            from shapely import affinity
            bx = affinity.rotate(box(c[0] - Lw / 2, c[1] - h * 0.55, c[0] + Lw / 2, c[1] + h * 0.55), rot, origin=c)
            if SIG_ALAN.buffer(-1).contains(bx) and serbest(bx.buffer(1.5)):
                TXT(c, s1, h, ag.c['lay'], TA.MIDDLE_CENTER, rot=rot, kayit=False)
                YAZ.append((bx, s1)); engel_guncelle()
                return bx
    print('UYARI: dik etiket de yok', s1)
    return None


def kanal_etiketleri(ag):
    for n, e in ag.ebe.items():
        a, b = ag.N[e], ag.N[n]
        if math.dist(a, b) < 40:
            continue
        o = ag.olcu[n]
        if ag.tur == 'egzoz' and ag.Q[n] <= WC_Q + 0.1:
            continue
        # ebeveyn aynı ölçülü ve aynı doğrultudaysa atla (yalnız ilk parçaya)
        if e in ag.ebe:
            pa = ag.N[ag.ebe[e]]
            if ag.olcu[e]['w'] == o['w'] and ag.olcu[e]['h'] == o['h']:
                continue
        m = add(a, birim(a, b), math.dist(a, b) * 0.62)
        s1 = f"{tr(ag.Q[n], 0)} m³/h / {o['w']}x{o['h']}"
        KANAL_ETIKET.append((ag, n, m, s1))
        w = ag.w(n)
        d = birim(a, b); nn = dik(d)
        onc = [add(m, nn, w / 2 + 12), add(m, nn, -w / 2 - 12)]
        if etiket(m, [s1], 9.0, ag.c['lay'], oncelik=onc, alan=SIG_ALAN.buffer(-1), haric=ag.U, rmax=300) is None:
            dik_etiket(ag, n, s1)


CEVRE = box(259300, -695600, 260100, -694500)
for y_, ad_, b_, h_ in ((Y_D, 'DUMAN ATIŞ', gdt_b, gdt_h), (Y_T, 'TAZE HAVA EMİŞ', gth_b, gth_h), (Y_E, 'EGZOZ ATIŞ', geg_b, geg_h)):
    TXT((X_DIS - 70, y_), f"{ad_} {b_}x{h_}", 9.0, GEC, TA.MIDDLE_RIGHT)
TXT((X_DIS - 20, -695330), 'DUVAR GEÇİŞLERİ (kullanıcı hizası) — dış ağızlar panjurlu', 7.0, GEC, TA.MIDDLE_RIGHT)
for ag in (ta, du, eg):
    kanal_etiketleri(ag)

for ag, m in MENFEZLER:
    satir = [f"{m['no']}  {m['mw']}x{m['mh']}", f"Q={tr(m['q'], 0)} m³/h"]
    onc = [add(m['p'], m['n'], 22), add(add(m['p'], m['n'], 22), m['d'], 30), add(add(m['p'], m['n'], 22), m['d'], -30)]
    etiket(m['p'], satir, 7.5, YAZI, oncelik=onc, alan=SIG_ALAN.buffer(-1), haric=m['govde'], rmax=400)

# cihaz / fan / klape etiketleri
etiket((SHC_C[0] + 60, SHC_C[1]), ['SHC-1 (TAVANA ASILI)'], 9.0, CHZ, alan=SIG_ALAN.buffer(-1), haric=shc_g, rmax=300)
etiket((DF_C[0], DF_C[1] - 70), ['DTF-1 (F400, TAVANA ASILI)'], 9.0, CHZ, alan=SIG_ALAN.buffer(-1), haric=fan_dt, rmax=300)
etiket((EF_C[0] - 30, EF_C[1]), ['EF-1 (TAVANA ASILI)'], 9.0, CHZ, alan=SIG_ALAN.buffer(-1), haric=fan_eg, rmax=300)
for gk_, kod in ((gsk_dt, 'GSK-2'), (gsk_th, 'GSK-1'), (gsk_eg, 'GSK-3')):
    c_ = gk_.centroid
    etiket((c_.x, c_.y), [kod], 7.0, CHZ, alan=SIG_ALAN.buffer(-1), haric=gk_, rmax=300)
# kesişme notları (alttan geçen kanal kesikli)
for ust, alt_, ad_u, ad_a, lay_ in ((U_ta, U_du, 'TAZE HAVA', 'DUMAN', DUM), (U_ta, U_eg, 'TAZE HAVA', 'EGZOZ', EGZ), (U_du, U_eg, 'DUMAN', 'EGZOZ', EGZ)):
    _kes = ust.intersection(alt_)
    for kk in (_kes.geoms if hasattr(_kes, 'geoms') else [_kes]):
        if kk.is_empty or kk.area < 1:
            continue
        cc = kk.centroid
        etiket((cc.x, cc.y), [f"{ad_a} {ad_u} ALTINDAN GEÇER"], 6.0, lay_, alan=SIG_ALAN.buffer(-1), haric=kk.buffer(2), rmax=400)
for ag in (ta, du, eg):
    for (pa, pb) in getattr(ag, 'bolme', []):
        etiket(pa, ['PANTOLON — AYIRICI BÖLME LEVHASI'], 6.5, ag.c['lay'], alan=SIG_ALAN.buffer(-1), haric=ag.U, rmax=300)

# plan başlığı + cihaz listesi (planın batısındaki boş alanda)
PLAN_CER = (258000, -701350, 283550, -693450)
msp.add_lwpolyline([(PLAN_CER[0], PLAN_CER[1]), (PLAN_CER[2], PLAN_CER[1]), (PLAN_CER[2], PLAN_CER[3]), (PLAN_CER[0], PLAN_CER[3])],
                   close=True, dxfattribs={'layer': 'ROTAS-HAV-CERCEVE', 'const_width': 1.5})
_cy = -694300
TXT((258250, _cy), 'ZEMİN KAT SIĞINAK (A-Z-16)', 24, 'ROTAS-HAV-BASLIK', TA.MIDDLE_LEFT); _cy -= 40
TXT((258250, _cy), 'HAVALANDIRMA PLANI (DUMAN TAHLİYELİ)', 24, 'ROTAS-HAV-BASLIK', TA.MIDDLE_LEFT); _cy -= 34
TXT((258250, _cy), 'ÖLÇEK 1/50', 14, 'ROTAS-HAV-BASLIK', TA.MIDDLE_LEFT); _cy -= 40
for s_ in [f"BRÜT ALAN {tr(R['A'])} m²  —  YÜKSEKLİK {tr(HN)} m  —  {R['kisi']} KİŞİ",
           f"TAZE HAVA {R['kisi']} x {tr(R['kb'], 1)} = {tr(R['qth'], 1)} → {tr(q_th, 0)} m³/h",
           f"EGZOZ (taze x 0,90) {tr(q_eg, 0)} m³/h",
           f"DUMAN TAHLİYE {tr(R['V'], 1)} m³ x {N_DT} = {tr(R['qdt'], 0)} → {tr(q_dt, 0)} m³/h"]:
    TXT((258250, _cy), s_, 11, 'ROTAS-HAV-BASLIK', TA.MIDDLE_LEFT); _cy -= 26
_cy -= 20
for s_ in ['CİHAZLAR — HEPSİ TAVANA ASILI (yere konmaz):',
           f"SHC-1  SIĞINAK HAVALANDIRMA CİHAZI {tr(q_th, 0)} m³/h",
           '        el + motor tahrikli, toz (G4) + kum filtreli, by-pass damperli',
           f"EF-1   KANAL TİPİ EGZOZ FANI {tr(q_eg, 0)} m³/h",
           f"DTF-1  DUMAN TAHLİYE FANI (aksiyel) {tr(q_dt, 0)} m³/h — F400",
           'GSK-1/2/3  gaz sızdırmaz klape (el kumandalı), duvar geçişi iç yüzünde',
           'DUVAR GEÇİŞLERİ (çelik kovan, yan yana, dışta panjurlu ağız):',
           f"        DUMAN {gdt_b}x{gdt_h} / TAZE {gth_b}x{gth_h} / EGZOZ {geg_b}x{geg_h} cm — v ≤ {tr(V_GEC, 1)} m/s"]:
    TXT((258250, _cy), s_, 9.0, CHZ, TA.MIDDLE_LEFT); _cy -= 20

# ============================================================== BASINÇ KAYBI / FAN SEÇİMİ
RHO = 1.2


def kritik(ag, sabit):
    """kök -> en uzak menfez yolu: Σ R·L + Σ ζ·ρv²/2 + sabit kayıplar (Pa)"""
    best = None
    for nm, t, q in ag.menfez:
        yol = []
        n = nm
        while n in ag.ebe:
            yol.append(n); n = ag.ebe[n]
        Lt = sum(math.dist(ag.N[x], ag.N[ag.ebe[x]]) for x in yol) / 100
        if best is None or Lt > best[0]:
            best = (Lt, yol)
    Lt, yol = best
    sur = 0.0; yer = 0.0
    for x in yol:
        o = ag.olcu[x]
        v, Rm = K.surtunme(ag.Q[x], o['w'], o['h'])
        sur += Rm * math.dist(ag.N[x], ag.N[ag.ebe[x]]) / 100
        e = ag.ebe[x]
        if e in ag.ebe:
            d0 = birim(ag.N[ag.ebe[e]], ag.N[e]); d1_ = birim(ag.N[e], ag.N[x])
            ZT = {'dirsek': 0.20, 'kose': 0.25, 'ofset': 0.15, 'pantolon': 0.35, 'T': 0.40}
            z = ZT.get(ag.tip.get(e), 0.10) if abs(d0[0] * d1_[0] + d0[1] * d1_[1]) < 0.99 else (0.10 if len(ag.cocuk[e]) == 1 else 0.15)
            yer += z * RHO * v * v / 2
    v0 = K.surtunme(ag.Q[ag.cocuk['K'][0]], ag.olcu[ag.cocuk['K'][0]]['w'], ag.olcu[ag.cocuk['K'][0]]['h'])[0]
    yer += 0.5 * RHO * v0 * v0 / 2
    top = sur + yer + sum(sabit.values())
    return dict(L=Lt, sur=sur, yer=yer, sabit=sabit, top=top, sec=yukari(top * 1.1, 50))


BAS = {
    'taze': kritik(ta, {'dış hava ağzı + ızgara': 25, 'çelik kovan + GSK-1': 30, 'menfez': 25}),
    'egzoz': kritik(eg, {'menfez': 25, 'çelik kovan + GSK-3': 30, 'dış atış ağzı + panjur': 25}),
    'duman': kritik(du, {'menfez': 30, 'çelik kovan + GSK-2': 30, 'dış atış ağzı + panjur': 30}),
}

# ============================================================== HESAP TABLOSU (onaylı biçim: proje/isitma_944_343/SIGINAK_HAVALANDIRMA_HESABI.dxf)
H = 12.0; RH = 26.0


def HT(x, y, s, h, al=TA.MIDDLE_LEFT):
    t = msp.add_text(s, height=h, dxfattribs={'layer': 'ROTAS-HESAP-YAZI', 'style': 'ROTAS', 'width': 0.85})
    t.set_placement((x, y), align=al)


def hbox(x0, y0, x1, y1, lay='ROTAS-HESAP-CIZGI', w=0.0):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': lay, 'const_width': w})


def hesap_blok(x, y, r):
    W = 900; y0 = y
    HT(x + W / 2, y - 16, f"{r['ad']} - CİHAZ LİSTESİ", H * 1.1, TA.MIDDLE_CENTER); y -= 32
    cols = [60, 330, 250, 90, 170]; hdr = ['SIRA NO', 'CİHAZ ADI', 'KAPASİTE VE EBATLAR', 'MİKTAR', 'AÇIKLAMA']
    rows = [['1', 'SIĞINAK HAVALANDIRMA CİHAZI', f"{tr(r['qsec'], 0)} m³/h {BAS['taze']['sec']} Pa", '1', 'El+motor, kum filtreli'],
            ['2', 'KANAL TİPİ EGZOZ FANI', f"{tr(r['qeg'], 0)} m³/h {BAS['egzoz']['sec']} Pa", '1', ''],
            ['3', 'DUMAN TAHLİYE FANI', f"{tr(r['qdts'], 0)} m³/h {BAS['duman']['sec']} Pa", '1', 'F400 (400°C / 2 saat)'],
            ['4', 'GAZ SIZDIRMAZ KLAPE + ÇELİK KOVAN', f"{r['gth'][0]}x{r['gth'][1]} / {r['geg'][0]}x{r['geg'][1]} / {r['gdt'][0]}x{r['gdt'][1]} cm", '3', 'Duvar geçişleri']]
    for rw in [hdr] + rows:
        xx = x
        for w, v in zip(cols, rw):
            hbox(xx, y, xx + w, y - RH); HT(xx + w / 2, y - RH / 2, v, H * (0.85 if rw is hdr else 0.95), TA.MIDDLE_CENTER); xx += w
        y -= RH
    y -= 30
    HT(x + 20, y - 14, f"{r['ad']} HAVALANDIRMA HESABI", H * 1.6); y -= 40
    for s in ['SIĞINAK YÖNETMELİĞİ (Resmi Gazete Tarihi: 25.08.1988 Resmi Gazete Sayısı: 19910)',
              'Madde 8 – (Başlığı ile birlikte değişik: RG-29/9/2010-27714)']:
        HT(x + 20, y - 8, s, H); y -= 22
    y -= 6
    tc = [200, 170, 260, 230]
    th = [['Sığınak Kapasitesi', 'Koruma Havalandırması', 'Yüksek Yangın Tehlikesi', 'Düşük ve Orta Yangın Tehlikesi'],
          ['0-50 kişiye kadar', '1,8 m³/h-kişi', 'Kum filtre,', 'G4 toz filtre'],
          ['51-150 kişiye kadar', '3,0 m³/h-kişi', 'G4 toz filtre ve', 'Radyoaktif filtre ve'],
          ['150 kişiden fazla', '4,5 m³/h-kişi', 'Aktif karbon filtre', 'Aktif karbon filtre']]
    for rw in th:
        xx = x + 20
        for w, v in zip(tc, rw):
            hbox(xx, y, xx + w, y - RH); HT(xx + w / 2, y - RH / 2, v, H * 0.85, TA.MIDDLE_CENTER); xx += w
        y -= RH
    y -= 24

    def kv(baslik, items):
        nonlocal y
        HT(x + 20, y - 12, baslik, H * 1.3); y -= 32
        c1 = 520
        for a, b in items:
            hbox(x + 20, y, x + 20 + c1, y - RH); hbox(x + 20 + c1, y, x + W - 20, y - RH)
            HT(x + 30, y - RH / 2, a, H); HT(x + 20 + c1 + (W - 40 - c1) / 2, y - RH / 2, b, H, TA.MIDDLE_CENTER); y -= RH
        y -= 22
    kv(f"{r['ad']} GENEL HAVALANDIRMA HESABI (KİŞİ BAŞI)",
       [('Sığınak Brüt Alanı', f"{tr(r['A'])} m²"), ('Sığınak Yüksekliği (kullanıcı)', f"{tr(HN)} m"),
        (f'Sığınak Kişi Kapasitesi ({tr(KISI_M2, 0)} m² brüt alan / kişi)', f"{r['kisi']} kişi"),
        ('Kişi Başı Taze Hava (150 kişiden fazla)', f"{tr(r['kb'], 1)} m³/h-kişi"),
        ('Taze Hava İçin Gerekli Hava (kişi x kişi başı)', f"{tr(r['qth'])} m³/h"),
        ('Seçilen Taze Hava Debisi (100\'e yukarı)', f"{tr(r['qsec'], 0)} m³/h"), ('Egzoz Debisi (taze havadan %10 az)', f"{tr(r['qeg'], 0)} m³/h"),
        (f'Duvar Geçişi - Taze Hava (v ≤ {tr(V_GEC, 1)} m/s)', f"{r['gth'][0]} × {r['gth'][1]} cm"),
        (f'Duvar Geçişi - Egzoz (v ≤ {tr(V_GEC, 1)} m/s)', f"{r['geg'][0]} × {r['geg'][1]} cm")])
    for s in ['Sığınak havalandırma fanının enerji ihtiyacı fan elektrik motoruna uygun kapasitede bir jeneratör ile karşılanmalı,',
              'jeneratör için sığınak alanı dışında bir alan makine dairesi olarak tasarlanmalıdır. Jeneratör egzozu doğrudan dışarıya',
              'verilmelidir. Jeneratörün devre dışı kaldığı durumlarda ise, enerji ihtiyacı fana bağlı insan gücü ile çalışan çevirmeli',
              'kol yardımı ile karşılanmalıdır.']:
        HT(x + 20, y - 8, s, H * 0.9); y -= 20
    y -= 16
    kv(f"{r['ad']} DUMAN TAHLİYE HAVALANDIRMASI HESABI",
       [('Sığınak Brüt Alanı', f"{tr(r['A'])} m²"), ('Sığınak Yüksekliği', f"{tr(HN)} m"), ('Sığınak Hacmi', f"{tr(r['V'])} m³"),
        ('Çevrim Oranı', f"{N_DT} defa/saat"), ('Duman Tahliye İçin Gerekli Hava', f"{tr(r['qdt'])} m³/h"),
        ('Seçilen Duman Tahliye Debisi', f"{tr(r['qdts'], 0)} m³/h"),
        (f'Duvar Geçişi - Duman Tahliye (v ≤ {tr(V_GEC, 1)} m/s)', f"{r['gdt'][0]} × {r['gdt'][1]} cm")])
    HT(x + 20, y - 8, f"Sığınak brüt alanı {tr(r['A'])} m² > 100 m² olduğundan duman tahliye fanı eklenmiştir.", H); y -= 30
    hbox(x, y0 + 6, x + W, y, 'ROTAS-HESAP-CERCEVE', 1.0)
    return y


def tablo(x, y, baslik, kolon, satirlar, gen, h=10.0):
    HT(x, y - 12, baslik, h * 1.3); y -= 30
    rh = h * 2.2
    for i, rw in enumerate([kolon] + satirlar):
        xx = x
        for w, v in zip(gen, rw):
            hbox(xx, y, xx + w, y - rh)
            HT(xx + w / 2, y - rh / 2, str(v), h * (0.85 if i == 0 else 0.9), TA.MIDDLE_CENTER); xx += w
        y -= rh
    return y


# ============================================================== ŞEMA (prensip kesit)
SL = 'ROTAS-HAV-SEMA'


def S_L(a, b, lay=SL):
    msp.add_line(a, b, dxfattribs={'layer': lay})


def S_PL(pts, lay=SL, kapali=False, gen=0.0):
    e = msp.add_lwpolyline(pts, close=kapali, dxfattribs={'layer': lay})
    if gen:
        e.dxf.const_width = gen


def S_T(p, s, h, lay=SL, al=TA.MIDDLE_LEFT, rot=0.0):
    t = msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS'})
    t.set_placement(p, align=al)


def S_box(x0, y0, x1, y1, lay=SL):
    S_PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, True)


def S_C(c, r, lay=SL):
    msp.add_circle(c, r, dxfattribs={'layer': lay})


def kot(x, y, s, sag=True, lay='ROTAS-HAV-KOT'):
    """kot işareti: üçgen + yatay çizgi + yazı"""
    S_PL([(x, y), (x - 6, y + 10), (x + 6, y + 10)], lay, True)
    x1 = x + (70 if sag else -70)
    S_L((x - 10 if sag else x + 10, y + 10), (x1, y + 10), lay)
    S_T(((x + 12) if sag else (x - 12), y + 18), s, 9, lay, TA.MIDDLE_LEFT if sag else TA.MIDDLE_RIGHT)


def s_kanal(a, b, w, lay):
    d = birim(a, b); n = dik(d)
    S_L(add(a, n, w / 2), add(b, n, w / 2), lay); S_L(add(a, n, -w / 2), add(b, n, -w / 2), lay)


def s_ok(p, d, Lk=14, lay=OK):
    n = dik(d); tip = add(p, d, Lk / 2); b = add(p, d, -Lk / 2)
    msp.add_solid([tip, add(b, n, Lk * 0.3), add(b, n, -Lk * 0.3), add(b, n, -Lk * 0.3)], dxfattribs={'layer': lay})


def s_menfez_alt(x, y, w, ters, lay=MEN):
    """kesitte kanal altı menfez: kanal alt çizgisine bitişik kanatlı çerçeve + hava yönü oku"""
    S_box(x - w / 2, y - 8, x + w / 2, y, lay)
    k = x - w / 2 + 4
    while k < x + w / 2 - 2:
        S_L((k, y - 7), (k + 3, y - 1), lay); k += 5
    if ters:
        S_L((x, y - 34), (x, y - 12), lay); S_L((x, y - 12), (x - 3, y - 17), lay); S_L((x, y - 12), (x + 3, y - 17), lay)
    else:
        S_L((x, y - 12), (x, y - 34), lay); S_L((x, y - 34), (x - 3, y - 29), lay); S_L((x, y - 34), (x + 3, y - 29), lay)


def s_gsk(c, w, yatay=True, lay=CHZ):
    if yatay:
        S_box(c[0] - 12, c[1] - w / 2 - 4, c[0] + 12, c[1] + w / 2 + 4, lay)
        S_L((c[0] - 6, c[1] + w / 2 - 2), (c[0] + 6, c[1] - w / 2 + 2), lay)
        S_C(c, 2.5, lay)
        S_L((c[0], c[1] + w / 2 + 4), (c[0] - 8, c[1] + w / 2 + 20), lay); S_C((c[0] - 9.5, c[1] + w / 2 + 23), 3, lay)
    else:
        S_box(c[0] - w / 2 - 4, c[1] - 12, c[0] + w / 2 + 4, c[1] + 12, lay)
        S_L((c[0] - w / 2 + 2, c[1] - 6), (c[0] + w / 2 - 2, c[1] + 6), lay)
        S_C(c, 2.5, lay)


def s_duvar_kesit(x, y0, y1, t=25):
    """betonarme perde kesiti: iki çizgi + çapraz tarama"""
    S_box(x, y0, x + t, y1, 'ROTAS-HAV-SEMA')
    yy = y0
    while yy < y1 - 8:
        S_L((x, yy), (x + t, min(yy + t, y1)), 'ROTAS-HAV-SEMA'); yy += 20


def s_toprak(x0, x1, y):
    S_L((x0, y), (x1, y))
    k = x0 + 4
    while k < x1 - 6:
        S_L((k, y), (k + 8, y + 8)); k += 16


def s_kovan(xw, yc, t, hh, lay=GEC):
    S_box(xw - 5, yc - hh / 2, xw + t + 5, yc + hh / 2, lay)


def s_baca(xa, xb, y0, y1, ust_kapak=True, lay=BACA):
    S_box(xa, y0, xb, y1, lay)
    if ust_kapak:   # şapka (yağmur başlığı) + panjur
        S_PL([(xa - 10, y1 + 25), (xb + 10, y1 + 25), (xb + 10, y1 + 18), (xa - 10, y1 + 18)], lay, True)
        for k in range(3):
            S_L((xa, y1 + 2 + k * 5), (xb, y1 + 6 + k * 5), lay)
        S_L((xa, y1), (xa, y1 + 18), lay); S_L((xb, y1), (xb, y1 + 18), lay)


def s_kanal_yol(yol, w, lay, govdeler=()):
    """kesitte kanal: eksen yolu -> düz uçlu, köşeli dirsekli çift çizgi; bileşen gövdeleri içinde çizgi silinir"""
    g = LineString(yol).buffer(w / 2, cap_style=2, join_style=2)
    c = g.boundary
    if govdeler:
        c = c.difference(unary_union(list(govdeler)).buffer(0.01))
    for p in (c.geoms if hasattr(c, 'geoms') else [c]):
        if p.length > 0.01:
            S_PL(list(p.coords), lay)


def s_gsk_g(c, w, d='y', lay=CHZ):
    """kesitte gaz sızdırmaz klape; d='y' yatay kanal üzerinde. döner gövde poligonu"""
    if d == 'y':
        b = box(c[0] - 14, c[1] - w / 2 - 4, c[0] + 14, c[1] + w / 2 + 4)
        S_box(*b.bounds, lay)
        S_L((c[0] - 6, c[1] + w / 2 - 2), (c[0] + 6, c[1] - w / 2 + 2), lay)
        S_C(c, 2.5, lay)
        S_L((c[0], c[1] + w / 2 + 4), (c[0] - 8, c[1] + w / 2 + 18), lay); S_C((c[0] - 9.5, c[1] + w / 2 + 21), 3, lay)
    return b


def sema(x0, y0):
    """3 panel: TAZE HAVA | EGZOZ | DUMAN TAHLİYE — batı duvarından yatay çıkış (duvardan atış), h = 6,00 m, ölçeksiz prensip."""
    Hk = HN * 100
    S_T((x0, y0 + Hk + 190), f'SIĞINAK HAVALANDIRMA ŞEMASI (PRENSİP KESİT — ÖLÇEKSİZ) — SIĞINAK YÜKSEKLİĞİ {tr(HN)} m', 20, 'ROTAS-HAV-BASLIK')
    PW = 1300; t = 75
    panel = [('A) TAZE HAVA / KORUMA HAVALANDIRMASI', TAZE, q_th, 'GSK-1', ta.olcu[ta.cocuk['K'][0]], R['gth'], 'shc', n_tm, TAZE_Q, False, 'TAZE HAVA'),
             ('B) EGZOZ', EGZ, q_eg, 'GSK-3', eg.olcu[eg.cocuk['K'][0]], R['geg'], 'kanal', n_em, EGZ_Q, True, 'EGZOZ'),
             ('C) DUMAN TAHLİYE', DUM, q_dt, 'GSK-2', du.olcu[du.cocuk['K'][0]], R['gdt'], 'aksiyel', n_dm, DUM_Q, True, 'DUMAN')]
    for i, (baslik, lay, qq, kod, ww, gg, cihaz, nm_, qm_, ters, ad) in enumerate(panel):
        bx = x0 + i * (PW + 420)
        xw = bx + 230; xi = xw + t; xe = xi + PW
        S_T((xw, y0 + Hk + 120), baslik, 13, 'ROTAS-HAV-BASLIK')
        s_duvar_kesit(xw, y0 - 30, y0 + Hk + 30, t)
        S_L((xi, y0), (xe, y0)); S_L((xi, y0 - 30), (xe, y0 - 30))
        S_L((xi, y0 + Hk), (xe, y0 + Hk)); S_L((xw, y0 + Hk + 30), (xe, y0 + Hk + 30))
        s_toprak(bx, xw, y0 - 10)
        S_T((bx + 10, y0 + 12), 'DIŞ ZEMİN', 8, SL)
        hk = ww['h'] / 10; gb, gh = gg[0], gg[1]
        ky = y0 + Hk - 25 - max(hk, gh) / 2                      # kanal ekseni (tavandan 25 cm askı payı)
        kov = box(xw - 5, ky - gh / 2 - 5, xi + 5, ky + gh / 2 + 5)
        S_box(*kov.bounds, GEC)
        for k in range(max(2, int(gh // 10))):                    # dış ağız panjuru
            yy = ky - gh / 2 + 4 + k * (gh - 8) / max(1, int(gh // 10) - 1)
            S_L((xw - 22, yy - 4), (xw - 8, yy + 4), GEC)
        S_box(xw - 25, ky - gh / 2 - 5, xw - 5, ky + gh / 2 + 5, GEC)
        s_ok((xw - 70, ky), (-1, 0) if ters else (1, 0), 16, OK)
        gk = box(xi + 30, ky - gh / 2 - 4, xi + 58, ky + gh / 2 + 4)
        S_box(*gk.bounds, CHZ); S_L((xi + 38, ky + gh / 2 - 2), (xi + 50, ky - gh / 2 + 2), CHZ); S_C(((xi + 44), ky), 2.5, CHZ)
        S_L((xi + 44, ky + gh / 2 + 4), (xi + 44, y0 + Hk), CHZ)                       # klape askısı
        # cihaz
        cx0 = xi + 180
        if cihaz == 'shc':
            cw, ch = 320, 100
        elif cihaz == 'kanal':
            cw, ch = 110, max(hk, gh) + 20
        else:
            cw, ch = 130, max(hk, gh) + 24
        cih = box(cx0, ky - ch / 2, cx0 + cw, ky + ch / 2)
        for xa in (cx0 + 15, cx0 + cw - 15):
            S_L((xa, ky + ch / 2), (xa, y0 + Hk), CHZ)                                # tavan askı çubukları
        S_box(*cih.bounds, CHZ)
        if cihaz == 'shc':
            cy0 = ky - ch / 2
            S_L((cx0 + 100, cy0), (cx0 + 100, cy0 + ch), CHZ); S_L((cx0 + 200, cy0), (cx0 + 200, cy0 + ch), CHZ)
            pts = []; yy = cy0 + ch - 10; k = 0
            while yy > cy0 + 8:
                pts.append((cx0 + 15 if k % 2 == 0 else cx0 + 85, yy)); yy -= 10; k += 1
            S_PL(pts, CHZ)
            for ii in range(6):
                for jj in range(3):
                    S_C((cx0 + 115 + ii * 14, cy0 + 20 + jj * 28), 1.8, CHZ)
            S_L((cx0 + 105, cy0 + ch - 8), (cx0 + 195, cy0 + ch - 22), CHZ)
            fc = (cx0 + 255, ky); S_C(fc, 34, CHZ); S_C(fc, 10, CHZ)
            for k in range(8):
                a_ = k * math.pi / 4
                S_L((fc[0] + 10 * math.cos(a_), fc[1] + 10 * math.sin(a_)), (fc[0] + 32 * math.cos(a_ + 0.5), fc[1] + 32 * math.sin(a_ + 0.5)), CHZ)
            S_box(cx0 + cw - 34, cy0 + 6, cx0 + cw - 6, cy0 + 32, CHZ); S_T((cx0 + cw - 20, cy0 + 19), 'M', 10, CHZ, TA.MIDDLE_CENTER)
            S_PL([(cx0 + 150, cy0), (cx0 + 150, y0 + 150)], CHZ); S_C((cx0 + 150, y0 + 144), 6, CHZ)
            S_T((cx0 + 162, y0 + 144), 'EL KOLU — zincir / uzatma mili ile yerden çevrilir', 8, CHZ, TA.MIDDLE_LEFT)
            S_T((cx0 + 50, cy0 - 14), 'TOZ FİLTRE (G4)', 8, CHZ, TA.MIDDLE_CENTER)
            S_T((cx0 + 150, cy0 - 28), 'KUM FİLTRE (BY-PASS DAMPERLİ)', 8, CHZ, TA.MIDDLE_CENTER)
            S_T((cx0 + 255, cy0 - 14), 'FAN + MOTOR', 8, CHZ, TA.MIDDLE_CENTER)
            fan_ad = f"SHC-1 SIĞINAK HAVALANDIRMA CİHAZI (TAVANA ASILI) {tr(qq, 0)} m³/h {BAS['taze']['sec']} Pa"
        elif cihaz == 'kanal':
            S_C((cx0 + cw / 2, ky), min(cw, ch) * 0.3, CHZ); S_C((cx0 + cw / 2, ky), 8, CHZ)
            fan_ad = f"EF-1 KANAL TİPİ EGZOZ FANI (TAVANA ASILI) {tr(qq, 0)} m³/h {BAS['egzoz']['sec']} Pa"
        else:
            xf = cx0 + cw / 2
            S_PL([(xf, ky), (xf - 18, ky + ch * 0.38), (xf + 18, ky + ch * 0.38)], CHZ, True)
            S_PL([(xf, ky), (xf - 18, ky - ch * 0.38), (xf + 18, ky - ch * 0.38)], CHZ, True)
            S_L((cx0 + 10, ky - ch / 2), (cx0 + 10, ky + ch / 2), CHZ); S_L((cx0 + cw - 10, ky - ch / 2), (cx0 + cw - 10, ky + ch / 2), CHZ)
            fan_ad = f"DTF-1 DUMAN TAHLİYE FANI (TAVANA ASILI) {tr(qq, 0)} m³/h {BAS['duman']['sec']} Pa F400"
        # kanal: duvar -> klape -> cihaz (geçiş ölçüsü), cihaz -> dağıtım (ana kanal ölçüsü)
        s_kanal_yol([(xi + 5, ky), (cx0, ky)], gh, lay, [gk, kov])
        s_kanal_yol([(cx0 + cw, ky), (xe - 40, ky)], hk, lay)
        S_L((xe - 40, ky - hk / 2), (xe - 40, ky + hk / 2), lay)
        for xa in (cx0 + cw + 150, cx0 + cw + 450, cx0 + cw + 750):
            S_L((xa, ky + hk / 2), (xa, y0 + Hk), lay)                                # kanal askıları
        for xm in (cx0 + cw + 300, cx0 + cw + 600, cx0 + cw + 900):
            s_menfez_alt(xm, ky - hk / 2, 40 if lay != DUM else 90, ters)
        s_ok((cx0 + cw + 220, ky), (-1, 0) if ters else (1, 0)); s_ok((xi + 120, ky), (-1, 0) if ters else (1, 0))
        S_T((cx0 + cw / 2, ky - max(ch, hk) / 2 - 70), fan_ad, 9, CHZ, TA.MIDDLE_CENTER)
        S_T((cx0 + cw + 60, ky - hk / 2 - 100), f"{ad} KANALI {tr(qq, 0)} m³/h — {ww['w']}x{ww['h']} (h ≤ 8 m/s)", 9, lay)
        S_T((cx0 + cw + 60, ky - hk / 2 - 120), f"{ad} MENFEZLERİ ({nm_} AD. x {tr(qm_, 0)} m³/h)", 9, MEN)
        S_T((xw - 30, ky - gh / 2 - 30), f"DUVAR GEÇİŞİ {gb}x{gh} cm", 8, GEC, TA.MIDDLE_RIGHT)
        S_T((xw - 30, ky - gh / 2 - 44), f"ÇELİK KOVAN + PANJUR / {kod} içte", 8, GEC, TA.MIDDLE_RIGHT)
        S_T((xw - 30, y0 + 250), 'SIĞINAK DIŞ DUVARI', 8, SL, TA.MIDDLE_RIGHT)
        kot(xe - 30, y0, '±0,00 SIĞINAK DÖŞEMESİ', False)
        kot(xe - 30, y0 + Hk, f'+{tr(HN)} SIĞINAK TAVANI', False)
        kot(xe - 120, ky - max(hk, gh) / 2 - 30, f"KANAL ALT +{tr((ky - max(hk, gh) / 2 - y0) / 100)}", False)
    return xe + 100


# ============================================================== LEJANT + NOTLAR
def lejant(x, y):
    LY = 'ROTAS-HAV-LEJANT'
    S_T((x, y), 'LEJANT', 16, 'ROTAS-HAV-BASLIK'); y -= 40
    satir = []

    def kanal_ornek(yy, lay):
        S_L((x, yy + 8), (x + 80, yy + 8), lay); S_L((x, yy - 8), (x + 80, yy - 8), lay)
        s_ok((x + 40, yy), (1, 0), 10)

    ogeler = [
        (lambda yy: kanal_ornek(yy, TAZE), 'TAZE HAVA (ÜFLEME) KANALI — debi m³/h / genişlik x yükseklik (mm)'),
        (lambda yy: kanal_ornek(yy, EGZ), 'EGZOZ KANALI'),
        (lambda yy: kanal_ornek(yy, DUM), 'DUMAN EGZOZ KANALI (min. 1,0 mm galvaniz sac)'),
        (lambda yy: (S_PL([(x + 25, yy + 6), (x + 25, yy - 4), (x + 55, yy - 4), (x + 55, yy + 6)], MEN),
                     S_L((x + 10, yy + 6), (x + 70, yy + 6), TAZE)), f"KANAL YANAĞI MENFEZİ (TM taze, EM egzoz, DM duman) — {ADET.get('menfez_taze', 0)}+{ADET.get('menfez_egzoz', 0)}+{ADET.get('menfez_duman', 0)} AD."),
        (lambda yy: (S_box(x + 10, yy - 14, x + 70, yy + 14, CHZ), S_L((x + 27, yy - 14), (x + 27, yy + 14), CHZ), S_L((x + 44, yy - 14), (x + 44, yy + 14), CHZ), S_C((x + 57, yy), 8, CHZ)),
         'SHC SIĞINAK HAVALANDIRMA CİHAZI (toz filtre + kum filtre + fan, el kolu + motor) — 1 AD.'),
        (lambda yy: (S_box(x + 15, yy - 14, x + 65, yy + 14, CHZ), S_C((x + 40, yy), 9, CHZ)), 'EF KANAL TİPİ EGZOZ FANI — 1 AD.'),
        (lambda yy: (S_box(x + 15, yy - 16, x + 65, yy + 16, CHZ), S_PL([(x + 40, yy), (x + 33, yy + 12), (x + 47, yy + 12)], CHZ, True), S_PL([(x + 40, yy), (x + 33, yy - 12), (x + 47, yy - 12)], CHZ, True)),
         'DTF DUMAN TAHLİYE FANI (aksiyel, F400) — 1 AD.'),
        (lambda yy: (S_box(x + 28, yy - 16, x + 52, yy + 16, CHZ), S_L((x + 34, yy + 12), (x + 46, yy - 12), CHZ), S_C((x + 40, yy), 2.5, CHZ)),
         f"GSK GAZ SIZDIRMAZ KLAPE (el kumandalı) — {ADET.get('gsk', 0)} AD."),
        (lambda yy: (S_box(x + 20, yy - 12, x + 60, yy + 12, GEC), S_L((x + 22, yy + 9), (x + 58, yy + 9), GEC), S_L((x + 22, yy - 9), (x + 58, yy - 9), GEC)),
         f"DUVAR GEÇİŞİ ÇELİK KOVAN + PANJURLU DIŞ AĞIZ (duvardan atış) — {ADET.get('kovan', 0)} AD."),
        (lambda yy: (S_L((x + 10, yy + 12), (x + 70, yy + 12), TAZE), S_L((x + 10, yy - 12), (x + 70, yy - 12), TAZE),
                     S_L((x + 40, yy + 12), (x + 40, yy + 40), TAZE), S_L((x + 55, yy + 12), (x + 55, yy + 40), TAZE),
                     S_L((x + 55, yy + 12), (x + 47, yy + 4), TAZE)), 'T DAL — YUVARLATILMIŞ AĞIZ + AYAR KANADI'),
        (lambda yy: (msp.add_arc((x + 10, yy + 20), 20, 270, 360, dxfattribs={'layer': TAZE}), msp.add_arc((x + 10, yy + 20), 32, 270, 360, dxfattribs={'layer': TAZE}),
                     msp.add_arc((x + 10, yy + 20), 8, 270, 360, dxfattribs={'layer': TAZE})), 'KAVİSLİ DİRSEK — YÖNLENDİRİCİ KANATLI'),
        (lambda yy: s_ok((x + 40, yy), (1, 0), 14), 'HAVA AKIŞ YÖNÜ'),
    ]
    for f_, s in ogeler:
        f_(y)
        S_T((x + 100, y), s, 10, LY)
        y -= 42
    return y


NOTLAR = [
    "Sığınak havalandırması Sığınak Yönetmeliği'ne göre kişi başı taze hava (normal) ve filtreli koruma havalandırması olarak yapılacaktır.",
    f"Hesaba esas alan sığınak BRÜT alanıdır: {tr(A_BRUT)} m²; kişi sayısı brüt alan / 1 m² = {R['kisi']} kişi; yükseklik {tr(HN)} m alınmıştır.",
    f"Taze hava {R['kisi']} kişi x {tr(R['kb'], 1)} m³/h-kişi = {tr(q_th, 0)} m³/h, egzoz taze havanın %10 altında {tr(q_eg, 0)} m³/h olarak tasarlanmıştır.",
    f"Duman tahliye sığınak hacminin 10 katı ({tr(q_dt, 0)} m³/h) olarak tasarlanmış olup fan yangın algılama sistemi ile otomatik devreye girecektir.",
    "Sığınak havalandırma cihazı el + elektrik motoru tahrikli, toz (G4) ve kum filtreli, by-pass damperli olarak temin edilecektir.",
    "Tüm dış hava bağlantıları kullanıcının gösterdiği hizada batı duvarından YAN YANA yatay duvar geçişleri ile yapılacak, dış ağızlar panjurlu olacaktır.",
    "Duvar geçişlerinde duvar örülmeden / beton dökülmeden önce plandaki ölçülerde çelik kovan yerleştirilecek, kovanlar ankrajlı ve su/gaz sızdırmaz yapılacaktır.",
    "Her duvar geçişinin iç yüzüne el kumandalı gaz sızdırmaz klape (GSK) takılacaktır; fanlar ve SHC sığınak içindedir.",
    "SHC-1, DTF-1, EF-1 ve GSK'lar tavana askı çubukları ve titreşim izolatörleri ile asılacak, SHC el kolu zincir/uzatma mili ile yerden çevrilecektir.",
    "Duman tahliye fanı EN 12101-3 F400 (400 °C / 2 saat) sınıfında olacaktır.",
    "Duman egzoz kanalları en az 1,0 mm galvaniz sacdan, askıları yangına dayanıklı olarak yapılacaktır.",
    "Kanallar tavana yakın asılacak, kanal üstü ile tavan arasında en az 25 cm askı payı bırakılacaktır.",
    "Kanallar betonarme kolon ve giriş holü duvarları içinden geçirilmeyecek, yalnız planda ölçüsü yazılı duvar geçişleri kullanılacaktır.",
    "Menfezler ayar damperli (OBD) olacak ve devreye almada plandaki debilere göre ayarlanacaktır.",
    "Fan ve cihaz elektrik beslemeleri jeneratör destekli olarak elektrik projesine göre yapılacaktır.",
    "Egzoz ve duman atış ağızları komşu pencere ve kapılardan en az 3,00 m uzakta, taze hava emiş ağzından ayrık olarak panjurlu yapılacaktır.",
    "Dirsekler R iç = 0,5·W kavisli ve yönlendirici kanatlı, T dallar yuvarlatılmış ağızlı ve ayar kanatlı yapılacaktır (özel parça detayları).",
]


def notlar(x, y):
    S_T((x, y), 'PROJE NOTLARI', 16, 'ROTAS-HAV-BASLIK'); y -= 36
    for i, s in enumerate(NOTLAR, 1):
        S_T((x, y), f"{i}. {s}", 10, 'ROTAS-HAV-NOT'); y -= 24
    return y


# ============================================================== DETAY ÇERÇEVELERİ (kullanıcı: tüm detaylar kare içinde)


def cer_bas():
    return len(msp)


def cer_bit(i0, pay=30.0, baslik=None, i1=None):
    from ezdxf import bbox as _bb
    ents = list(msp)[i0:i1]
    if not ents:
        return
    ex = _bb.extents(ents, fast=True)
    x0, y0, x1, y1 = ex.extmin[0] - pay, ex.extmin[1] - pay, ex.extmax[0] + pay, ex.extmax[1] + pay
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': 'ROTAS-HAV-CERCEVE', 'const_width': 1.5})
    return (x0, y0, x1, y1)


# ============================================================== YERLEŞİM (bodrum pafta penceresinin boş sol kısmı)
yb = hesap_blok(259800, -701600, R)
_i = cer_bas(); x_sema_son = sema(260900, -702450); cer_bit(_i)
_i = cer_bas(); y_lj = lejant(260950, -702750); cer_bit(_i)
_i = cer_bas(); y_nt = notlar(262400, -702750); cer_bit(_i)


def menfez_satirlari():
    rows = []
    for tur, ad in (('taze', 'TAZE HAVA MENFEZİ'), ('egzoz', 'EGZOZ MENFEZİ'), ('duman', 'DUMAN EGZOZ MENFEZİ')):
        ms = [m for a, m in MENFEZLER if a.tur == tur and not m.get('an')]
        m = ms[0]
        rows.append([f"{m['no'][:2]}-1 … {m['no'][:2]}-{len(ms)}", ad, f"{m['mw']}x{m['mh']}", str(len(ms)), tr(m['q'], 0), tr(m['v'], 2)])
    an = [m for a, m in MENFEZLER if m.get('an')]
    if an:
        rows.append([f"EA-1 … EA-{len(an)}", 'WC EGZOZ ANEMOSTADI', an[0]['mw'], str(len(an)), tr(an[0]['q'], 0), tr(an[0]['v'], 2)])
    return rows



# ============================================================== DETAYLAR: KURANGLEZ GÖRÜNÜŞ / KESİT + KANAL ÖZEL PARÇALARI (1/20)
KD = 2.5                     # plan 1/50 -> detay 1/20


def S_tarama(x0, y0, x1, y1, ad=12, lay=BACA):
    """betonarme kesit: kutu + eğik tarama (kutu içine kırpılır)"""
    S_box(x0, y0, x1, y1, lay)
    b = box(x0, y0, x1, y1)
    k = -(y1 - y0)
    while k < (x1 - x0):
        ln = LineString([(x0 + k, y0), (x0 + k + (y1 - y0), y1)]).intersection(b)
        if ln.geom_type == 'LineString' and ln.length > 1:
            S_L(ln.coords[0], ln.coords[-1], lay)
        k += ad


def S_klavuz(a, b, s, h=8.0, lay='ROTAS-HAV-SEMA', sag=True):
    S_L(a, b, lay); S_C(a, 1.6, lay)
    S_T((b[0] + (4 if sag else -4), b[1]), s, h, lay, TA.MIDDLE_LEFT if sag else TA.MIDDLE_RIGHT)


def cikis_kesit(x0, yg):
    """çıkış duvarı A-A görünüşü (içeriden batıya bakış): üç duvar geçişi yan yana. yatay = plan y (kuzey sağda), düşey = kot"""
    ya_, yb_ = -695330, -694720
    X = lambda y: x0 + (y - ya_) * KD
    Y = lambda kot_: yg + kot_ * KD
    Hk = HN * 100
    S_T((x0, Y(Hk + 120)), 'ÇIKIŞ DUVARI A-A GÖRÜNÜŞÜ (DUVAR GEÇİŞLERİ — DUVARDAN ATIŞ) — 1/20', 16, 'ROTAS-HAV-BASLIK')
    S_T((x0, Y(Hk + 100)), 'kullanıcının gösterdiği hizada batı duvarından üç yatay geçiş yan yana; dış ağızlar panjurlu, GSK iç yüzde', 9, SL)
    S_L((X(ya_), Y(0)), (X(yb_), Y(0)), SL)
    s_toprak(X(ya_), X(yb_), Y(0))
    S_tarama(X(ya_), Y(Hk), X(yb_), Y(Hk + 30), 14, 'ROTAS-HAV-SEMA')                 # tavan döşemesi
    for c0, c1 in ((-695290, -695230), (-694815, -694755)):                                # kolonlar
        S_tarama(X(max(c0, ya_)), Y(0), X(min(c1, yb_)), Y(Hk), 20, 'ROTAS-HAV-SEMA')
    S_box(X(-695230), Y(0), X(-694815), Y(Hk), SL)
    S_T((X(-695022), Y(30)), 'DUVAR (kolonlar arası 4,15 m)', 8, SL, TA.MIDDLE_CENTER)
    for yc, (b_, h_), ad, kod, ww in ((Y_D, R['gdt'][:2], 'DUMAN ATIŞ', 'GSK-2', du.olcu[du.cocuk['K'][0]]),
                                      (Y_T, R['gth'][:2], 'TAZE HAVA EMİŞ', 'GSK-1', ta.olcu[ta.cocuk['K'][0]]),
                                      (Y_E, R['geg'][:2], 'EGZOZ ATIŞ', 'GSK-3', eg.olcu[eg.cocuk['K'][0]])):
        zc = Hk - 25 - max(ww['h'] / 10, h_) / 2
        x_a, x_b = X(yc - b_ / 2), X(yc + b_ / 2)
        S_box(x_a - 12, Y(zc - h_ / 2 - 5), x_b + 12, Y(zc + h_ / 2 + 5), GEC)            # çelik kovan
        S_box(x_a, Y(zc - h_ / 2), x_b, Y(zc + h_ / 2), GEC)
        for k in range(1, int(h_ // 10)):
            S_L((x_a + 3, Y(zc - h_ / 2 + k * 10)), (x_b - 3, Y(zc - h_ / 2 + k * 10)), GEC)   # panjur kanatları
        S_T(((x_a + x_b) / 2, Y(zc + h_ / 2 + 40)), f"{ad}", 8, GEC, TA.MIDDLE_CENTER)
        S_T(((x_a + x_b) / 2, Y(zc + h_ / 2 + 24)), f"{b_}x{h_} cm", 8, GEC, TA.MIDDLE_CENTER)
        S_T(((x_a + x_b) / 2, Y(zc - h_ / 2 - 24)), f"{kod}", 7.5, GEC, TA.MIDDLE_CENTER)
        S_T(((x_a + x_b) / 2, Y(zc - h_ / 2 - 40)), f"alt +{tr((zc - h_ / 2) / 100)}", 7.5, GEC, TA.MIDDLE_CENTER)
    kot(X(yb_) + 40, Y(0), '±0,00 SIĞINAK DÖŞEMESİ', True)
    kot(X(yb_) + 40, Y(Hk), f'+{tr(HN)} SIĞINAK TAVANI', True)
    S_T((X(ya_), Y(-40)), 'GÜNEY', 9, SL); S_T((X(yb_), Y(-40)), 'KUZEY', 9, SL, TA.MIDDLE_RIGHT)
    return X(yb_) + 300


def detay_parca(cx, cy, baslik, kur, notlar_):
    """kanal özel parça detayı (1/20). kur(ag) ağacı kurar; ağ ölçüleri elle verilir"""
    _i0 = cer_bas()
    _detay_parca(cx, cy, baslik, kur, notlar_)
    S_box(cx - 350, cy - 300, cx + 400, cy + 330, 'ROTAS-HAV-CERCEVE')


def _detay_parca(cx, cy, baslik, kur, notlar_):
    S_T((cx - 330, cy + 300), baslik, 12, 'ROTAS-HAV-BASLIK')
    ag, ekle = kur()
    P, IC, FLN = ag.parca()
    U = unary_union(P).buffer(0)
    for g_ in [U.boundary] + IC + FLN:
        for x in (g_.geoms if hasattr(g_, 'geoms') else [g_]):
            if x.geom_type == 'LineString':
                S_PL(list(x.coords), ag.c['lay'])
            elif x.geom_type == 'LinearRing':
                S_PL(list(x.coords), ag.c['lay'])
    for f_ in ekle:
        f_(ag)
    yy = cy - 250
    for s_ in notlar_:
        S_T((cx - 330, yy), s_, 7.5, SL); yy -= 13


def mini(tur, kok, kenar, gen):
    """kenar: [(ebe, ad, nokta)], gen: {ad: genişlik cm (detay ölçeğinde gerçek x KD)}"""
    ag = Ag(tur, kok)
    for e_, nm, p_ in kenar:
        ag.N[nm] = p_; ag.cocuk[nm] = []; ag.cocuk[e_].append(nm); ag.ebe[nm] = e_
    ag.olcu = {n: {'w': int(gen[n] * 10), 'h': 0} for n in ag.ebe}
    ag.ml = {}
    Q = {}

    def f(n):
        Q[n] = gen.get(n, 1) ** 2 if not ag.cocuk[n] else sum(f(c) for c in ag.cocuk[n])
        return Q[n]
    f('K'); ag.Q = Q
    return ag


def detaylar(x0, y0):
    S_T((x0, y0 + 60), 'KANAL ÖZEL PARÇA DETAYLARI — 1/20 (ölçüler mm, plan ölçüleri ile uygulanır)', 16, 'ROTAS-HAV-BASLIK')
    C = [(x0 + 380, y0 - 340), (x0 + 1180, y0 - 340), (x0 + 1980, y0 - 340),
         (x0 + 380, y0 - 1000), (x0 + 1180, y0 - 1000), (x0 + 1980, y0 - 1000)]
    w = lambda mm: mm / 10 * KD
    # 1) pantolon (duman L2): 850 gövde -> 400 / 600 kollar
    cx, cy = C[0]

    def k1():
        ag = mini('duman', (cx, cy + 260), [('K', 'a', (cx, cy)), ('a', 'b', (cx - 300, cy)), ('a', 'c', (cx + 300, cy))],
                  {'a': w(850), 'b': w(400), 'c': w(600)})
        ag.Q = {'K': 3, 'a': 3, 'b': 1, 'c': 2}

        def e(ag_):
            (pa, pb) = ag_.bolme[-1]
            S_klavuz(pb, (cx + 150, cy + 215), 'AYIRICI BÖLME LEVHASI (1,0 mm galv., gövdeye 0,9·W uzanır)', 7.5)
            S_klavuz((pa[0], (pa[1] + pb[1]) / 2 + 20), (cx - 330, cy + 250), 'ayar mafsalı', 7.5, sag=True)
            S_C((pa[0], (pa[1] + pb[1]) / 2 + 20), 3, SL)
            S_klavuz((cx - 120, cy - 30), (cx - 300, cy - 120), 'YÖNLENDİRİCİ KANAT (kol ≥ 250 mm)', 7.5)
            S_klavuz((cx + 240, cy + 60), (cx + 120, cy + 140), 'FLANŞLI BAĞLANTI', 7.5)
            S_T((cx, cy + 280), '850x500', 8, DUM, TA.MIDDLE_CENTER)
            S_T((cx - 300, cy - 50), '400x500', 8, DUM, TA.MIDDLE_CENTER); S_T((cx + 300, cy - 50), '600x500', 8, DUM, TA.MIDDLE_CENTER)
        return ag, [e]
    detay_parca(cx, cy, '1) PANTOLON — AYIRICI BÖLMELİ Y AYRIM', k1,
                ['Gövde, kol debileri oranında iki kanala bölünür (bölme levhası ayrım noktasından gövdeye uzanır).',
                 'Kollar R iç = 0,5·W kavisli; kol genişliği ≥ 250 mm ise kanal ortasında yönlendirici kanat.',
                 'Kol ölçüsüne geçiş, dirsek çıkışında 200 mm konik redüksiyonla yapılır.'])
    # 2) kavisli dirsek
    cx, cy = C[1]

    def k2():
        ag = mini('egzoz', (cx - 200, cy + 230), [('K', 'a', (cx - 200, cy - 60)), ('a', 'b', (cx + 300, cy - 60))], {'a': w(600), 'b': w(600)})

        def e(ag_):
            S_klavuz((cx - 170, cy - 20), (cx - 40, cy + 120), 'YÖNLENDİRİCİ KANATLAR (2 ad., W ≥ 600 mm)', 7.5)
            S_klavuz((cx - 275, cy - 60), (cx - 340, cy - 170), 'R iç = 0,5·W', 7.5, sag=True)
            S_T((cx - 200, cy + 250), '600x400', 8, EGZ, TA.MIDDLE_CENTER)
        return ag, [e]
    detay_parca(cx, cy, '2) KAVİSLİ DİRSEK — KANATLI', k2,
                ['Dirsek iç yarıçapı 0,5·W, dış yarıçapı 1,5·W; kanatlar eş aralıklı ve dirsekle eş merkezli.',
                 'Kanatlar 1,0 mm galvaniz sac, iki uçtan perçinli.'])
    # 3) köşeli dirsek + kanat dizisi
    cx, cy = C[2]

    def k3():
        ag = mini('duman', (cx - 150, cy + 230), [('K', 'a', (cx - 150, cy - 60)), ('a', 'b', (cx + 40, cy - 60)), ('b', 'c', (cx + 250, cy - 60))],
                  {'a': w(850), 'b': w(850), 'c': w(850)})

        def e(ag_):
            S_klavuz((cx - 150, cy - 60), (cx + 30, cy + 150), 'KANAT DİZİSİ (turning vane, köşegen boyunca)', 7.5)
            S_T((cx - 150, cy + 250), '850x500', 8, DUM, TA.MIDDLE_CENTER)
        return ag, [e]
    detay_parca(cx, cy, '3) KÖŞELİ DİRSEK — KANAT DİZİLİ', k3,
                ['Kavisli dirsek için yer yetmeyen büyük kesitlerde kullanılır;', 'kanatlar köşegen üzerinde 12 cm aralıkla dizilir.'])
    # 4) T dal: yuvarlatılmış ağız + ayar kanadı + redüksiyon
    cx, cy = C[3]

    def k4():
        ag = mini('taze', (cx - 330, cy), [('K', 'a', (cx - 30, cy)), ('a', 'b', (cx + 300, cy)), ('a', 'c', (cx - 30, cy + 230))],
                  {'a': w(400), 'b': w(300), 'c': w(250)})

        def e(ag_):
            S_klavuz((cx + 20, cy + 15), (cx + 120, cy + 150), 'AYAR KANADI (splitter damper, mafsallı)', 7.5)
            S_klavuz((cx - 65, cy + 60), (cx - 330, cy + 150), 'YUVARLATILMIŞ AĞIZ R = 0,5·w dal', 7.5)
            S_klavuz((cx + 120, cy + 30), (cx + 160, cy - 110), 'KONİK REDÜKSİYON 200 mm', 7.5)
            S_T((cx - 250, cy - 50), '400x400', 8, TAZE, TA.MIDDLE_CENTER); S_T((cx + 250, cy - 50), '300x300', 8, TAZE, TA.MIDDLE_CENTER)
        return ag, [e]
    detay_parca(cx, cy, '4) T DAL — YUVARLATILMIŞ AĞIZ + AYAR KANADI', k4,
                ['Dal ağzı akış yukarısı tarafında yuvarlatılır; ayar kanadı dalın akış aşağısı köşesine mafsallanır.',
                 'Gövde redüksiyonu dal ağzından sonra yapılır.'])
    # 5) ofset
    cx, cy = C[4]

    def k5():
        ag = mini('duman', (cx - 120, cy + 230), [('K', 'a', (cx - 120, cy + 90)), ('a', 'b', (cx + 90, cy - 120)), ('b', 'c', (cx + 90, cy - 260))],
                  {'a': w(850), 'b': w(850), 'c': w(850)})

        def e(ag_):
            S_klavuz((cx - 20, cy - 15), (cx + 160, cy + 120), '45° OFSET PARÇASI', 7.5)
        return ag, [e]
    detay_parca(cx, cy, '5) OFSET (45°)', k5, ['Kanal hattında kaydırma gereken yerde iki adet 45° kırım, flanşlı.'])
    # 6) menfez bağlantısı (kanal yanağı)
    cx, cy = C[5]
    S_T((cx - 330, cy + 300), '6) KANAL YANAĞI MENFEZİ', 12, 'ROTAS-HAV-BASLIK')
    S_box(cx - 350, cy - 300, cx + 400, cy + 330, 'ROTAS-HAV-CERCEVE')
    W6 = w(300)
    S_L((cx - 300, cy + W6 / 2), (cx + 300, cy + W6 / 2), TAZE); S_L((cx - 300, cy - W6 / 2), (cx + 300, cy - W6 / 2), TAZE)
    ml = w(300); mh = 30
    S_PL([(cx - ml / 2, cy - W6 / 2), (cx - ml / 2, cy - W6 / 2 - mh), (cx + ml / 2, cy - W6 / 2 - mh), (cx + ml / 2, cy - W6 / 2)], MEN)
    k = cx - ml / 2 + 8
    while k < cx + ml / 2 - 6:
        S_L((k, cy - W6 / 2 - 4), (k + 8, cy - W6 / 2 - mh + 4), MEN); k += 12
    for f_ in (-0.25, 0.25):
        s_ok((cx + ml * f_, cy - W6 / 2 - mh - 30), (0, -1), 14, MEN)
    S_klavuz((cx + ml / 2, cy - W6 / 2 - 15), (cx + 140, cy - 150), 'ÇİFT SIRA AYARLI MENFEZ + OBD DAMPER', 7.5)
    S_klavuz((cx - 200, cy + W6 / 2), (cx - 250, cy + 150), 'kanal yanağına flanşlı montaj', 7.5)
    yy = cy - 250
    for s_ in ['Menfez ölçüsü planda yazılıdır (ör. 300x200); yüz hızı taze/egzoz 2,0 m/s, duman 3,0 m/s.',
               'Duman menfezleri çelik, sabit kanatlı (F400 hatta uygun) yapılır.']:
        S_T((cx - 330, yy), s_, 7.5, SL); yy -= 13


_i = cer_bas(); x_det = cikis_kesit(264200, -705150); cer_bit(_i)
detaylar(266400, -701700)


_i = cer_bas()
y_t = tablo(262400, y_nt - 90, 'MENFEZ ÇİZELGESİ', ['NO', 'MENFEZ', 'ÖLÇÜ (mm)', 'ADET', 'DEBİ (m³/h)', 'v (m/s)'],
            menfez_satirlari(), [150, 260, 110, 70, 120, 90])


def bas_satir(tur, ad, kod):
    b = BAS[tur]
    return [kod, ad, tr(b['L'], 1), tr(b['sur'], 0), tr(b['yer'], 0), tr(sum(b['sabit'].values()), 0), tr(b['top'], 0), str(b['sec'])]


cer_bit(_i)
_i = cer_bas()
y_t2 = tablo(262400, y_t - 90, 'FAN BASINÇ HESABI (kritik hat: Σ R·L + Σ ζ·ρv²/2 + menfez/klape/baca; seçim = 1,1 x toplam, 50 Pa yukarı)',
             ['KOD', 'AĞ', 'L (m)', 'SÜRT. (Pa)', 'YEREL (Pa)', 'SABİT (Pa)', 'TOPLAM (Pa)', 'SEÇİLEN (Pa)'],
             [bas_satir('taze', 'TAZE HAVA (SHC-1)', 'SHC-1'), bas_satir('egzoz', 'EGZOZ (EF-1)', 'EF-1'), bas_satir('duman', 'DUMAN TAHLİYE (DTF-1)', 'DTF-1')],
             [70, 220, 80, 100, 100, 100, 110, 120])
cer_bit(_i)


def kanal_satirlari():
    rows = []
    for ag, ad in ((ta, 'TAZE'), (eg, 'EGZOZ'), (du, 'DUMAN')):
        gor = {}
        for n in ag.ebe:
            o = ag.olcu[n]
            k = (o['w'], o['h'])
            Lk = math.dist(ag.N[n], ag.N[ag.ebe[n]]) / 100
            v = K.surtunme(ag.Q[n], o['w'], o['h'])[0]
            g = gor.setdefault(k, [0, 0, 0])
            g[0] += Lk; g[1] = max(g[1], ag.Q[n]); g[2] = max(g[2], v)
        for (w, h), (Lk, q, v) in sorted(gor.items(), key=lambda t: -t[1][1]):
            t_ = K.sac_kalinligi(w, ad == 'DUMAN')
            rows.append([ad, f"{w}x{h}", tr(q, 0), tr(v, 2), tr(Lk, 1), tr(t_, 1)])
    return rows


_i = cer_bas()
y_t3 = tablo(259800, yb - 60, 'KANAL ÇİZELGESİ (kanal hızı 8,0 m/s sınırına yakın seçildi, v ≤ 8,0 m/s)',
             ['AĞ', 'ÖLÇÜ (mm)', 'MAKS. DEBİ (m³/h)', 'v (m/s)', 'BOY (m)', 'SAC (mm)'], kanal_satirlari(), [120, 130, 180, 110, 110, 110])
cer_bit(_i)

# ============================================================== KAYDET
def mimari_birlestir(bizim, yol):
    """kullanıcının mimarisi (kolonlar dahil, MTY-BORU işaretleri hariç) + bizim çizim -> temiz R2010 (AutoCAD güvenli)"""
    from ezdxf.addons import Importer
    src = ezdxf.readfile(MIM_DXF)
    hedef = ezdxf.new('R2010', setup=True)
    hedef.header['$INSUNITS'] = 5; hedef.header['$MEASUREMENT'] = 1; hedef.header['$LUNITS'] = 2
    tm = hedef.modelspace()
    imp = Importer(src, hedef); imp.import_tables('*')
    normal, patlat = [], []
    for e in src.modelspace():
        if e.dxf.layer == 'MTY-BORU':
            continue
        if e.dxftype() == 'INSERT' and e.dxf.name not in src.blocks:
            continue
        (patlat if e.dxftype() in ('MULTILEADER', 'DIMENSION', 'ACAD_PROXY_ENTITY') else normal).append(e)
    imp.import_entities(normal, tm); imp.finalize()
    for e in patlat:
        try:
            for v in e.virtual_entities():
                if v.dxftype() in ('MTEXT', 'TEXT') and v.dxf.get('style') not in hedef.styles:
                    v.dxf.style = 'Standard'
                v.dxf.layer = e.dxf.layer
                tm.add_entity(v)
        except Exception as ex:
            print('  patlatılamadı', e.dxftype(), ex)
    for L_ in hedef.layers:
        if L_.dxf.name == 'MKDU0':
            L_.color = 8
    imp2 = Importer(bizim, hedef); imp2.import_tables('*')
    imp2.import_entities(list(bizim.modelspace()), tm); imp2.finalize()
    gecersiz = {st.dxf.name for st in hedef.styles if not st.dxf.name.strip() or st.dxf.name.lower().endswith('.shx')}
    yerler = [tm] + [b for b in hedef.blocks]
    for yer in yerler:
        for e in yer:
            for x in [e] + (list(e.attribs) if e.dxftype() == 'INSERT' else []):
                if x.dxf.hasattr('style') and (x.dxf.style in gecersiz or x.dxf.style not in hedef.styles):
                    x.dxf.style = 'Standard'
                if x.dxf.hasattr('linetype') and x.dxf.linetype not in hedef.linetypes:
                    x.dxf.linetype = 'BYLAYER'
    kul = {e.dxf.linetype for yer in yerler for e in yer if e.dxf.hasattr('linetype')} | {L_.dxf.linetype for L_ in hedef.layers}
    for lt in list(hedef.linetypes):
        if lt.pattern_tags.is_complex_type() and lt.dxf.name not in kul:
            hedef.linetypes.remove(lt.dxf.name)
    for ad in gecersiz:
        try:
            hedef.styles.remove(ad)
        except Exception:
            pass
    try:
        hedef.layers.remove('MTY-BORU')          # kullanıcının işaret katmanı (boş kaldı)
    except Exception:
        pass
    hedef.audit()
    if os.path.exists(yol):
        os.remove(yol)
    hedef.saveas(yol)


mimari_birlestir(doc, CIKTI)
print('yazıldı:', CIKTI)
print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in R.items() if k not in ('na',)})
print('brüt alan:', R['A'])
for t_, b in BAS.items():
    print(t_, {k: (round(v, 1) if isinstance(v, float) else v) for k, v in b.items()})
print('adet:', ADET)
print('tablo alt y:', yb, y_t3, 'şema sağ x:', x_sema_son, 'lejant/not:', y_lj, y_nt, y_t, y_t2)


# ============================================================== KONTROL
def kontrol():
    rap = []
    PLAN = box(*ALTLIK_KUTU)
    biz = [(g, l) for g, l in CIZ if g.intersects(PLAN)]
    kanal_g = [ag.U for ag in (ta, du, eg)]
    kovanlar = unary_union([k_th, k_dt, k_eg]).buffer(0.5)
    govdeler = kanal_g + [shc_g, gsk_th, gsk_dt, gsk_eg, fan_dt, fan_eg] + [m['govde'] for _, m in MENFEZLER]
    kes = []
    for k in KOLON_POLY:
        for g in govdeler:
            a_ = g.difference(kovanlar).intersection(k).area
            if a_ > 0.5:
                kes.append(([round(c) for c in k.bounds], round(a_, 1)))
    rap.append(f'betonarme (kolon/perde) kesişimi (kovan hariç): {len(kes)} {kes[:6]}')
    gec = [[round(c) for c in k.bounds] for kv in (k_th, k_dt, k_eg) for k in KOLON_POLY if kv.intersects(k)]
    rap.append(f'bilinçli perde geçişleri (kovan ∩ betonarme): {gec}')
    disari = [ag.tur for ag in (ta, du, eg) if ag.U.difference(SIG_ALAN.buffer(3)).difference(kovanlar.buffer(30)).area > 5]
    rap.append(f'sığınak dışına taşan kanal (riser hariç): {disari} '
               + str({ag.tur: round(ag.U.difference(SIG_ALAN.buffer(3)).difference(kovanlar.buffer(30)).area) for ag in (ta, du, eg)}))
    mt = STRtree(MIM_CIZ)
    bin_m = 0; ornek = []
    for g, l in biz:
        for i in mt.query(g):
            x = g.intersection(MIM_CIZ[i])
            if not x.is_empty and x.length > 0.5:
                bin_m += 1; ornek.append((l, [round(c) for c in x.bounds]))
    rap.append(f'bizim çizgi ∩ mimari çizgi (üst üste, >0,5 cm): {bin_m} {ornek[:6]}')
    bt = STRtree([g for g, _ in biz])
    bin_b = 0; ob = []
    for i, (g, l) in enumerate(biz):
        for j in bt.query(g):
            if j <= i:
                continue
            x = g.intersection(biz[j][0])
            if not x.is_empty and x.length > 0.5:
                bin_b += 1; ob.append((l, biz[j][1], [round(c) for c in x.bounds]))
    rap.append(f'bizim çizgi ∩ bizim çizgi (üst üste): {bin_b} {ob[:6]}')
    yz = [(b, s) for b, s in YAZ if b.intersects(PLAN)]
    yy = [(yz[i][1], yz[j][1]) for i in range(len(yz)) for j in range(i + 1, len(yz)) if yz[i][0].intersects(yz[j][0])]
    ym = [(s) for b, s in yz for m in MIM_YAZI if b.intersects(m)]
    tl = [g for g, _ in biz] + MIM_CIZ + [ag.U for ag in (ta, du, eg)]
    tum = STRtree(tl)
    yc = []
    for b, s in yz:
        for i in tum.query(b):
            if tl[i].intersects(b.buffer(-0.5)):
                yc.append(s); break
    mys = [g for g, _ in biz] + [ag.U for ag in (ta, du, eg)]
    ymc = [[round(c) for c in m.bounds] for m in MIM_YAZI for g in mys if g.intersects(m)]
    rap.append(f'bizim çizgi ∩ mimari yazı: {len(ymc)} {ymc[:6]}')
    rap.append(f'yazı ∩ yazı: {len(yy)} {yy[:3]}; yazı ∩ mimari yazı: {len(ym)} {ym[:4]}; yazı ∩ çizgi: {len(yc)} {yc[:6]}')
    acik = [(ag.tur, ag.N[n]) for ag in (ta, du, eg) for n, ch in ag.cocuk.items() if not ch and not any(m[0] == n for m in ag.menfez)]
    rap.append(f'boşta kanal ucu: {len(acik)} {acik}')
    rap.append('ağlar arası kanal kesişmesi (bilinçli, alttaki kesikli): ' + str([(x, y) for x, y, a, b in (('taze', 'duman', U_ta, U_du), ('taze', 'egzoz', U_ta, U_eg), ('duman', 'egzoz', U_du, U_eg))
                                                     if a.intersection(b).area > 1]))
    A = R['A']; V = A * HN
    kisi_ = math.ceil(A - 1e-9); c = dict(qth=math.ceil(kisi_ * kisi_basi(kisi_) / 100 - 1e-9) * 100, qdt=math.ceil(V * 10 / 500 - 1e-9) * 500)
    rap.append(f"hesap tekrarı: A={A} V={V:.2f} taze {c['qth']} (tablo {R['qsec']}), egzoz {c['qth'] * 0.9:.0f} (tablo {R['qeg']}), duman {c['qdt']} (tablo {R['qdts']}); "
               f"menfez toplamları taze {sum(m[2] for m in ta.menfez):.0f} egzoz {sum(m[2] for m in eg.menfez):.0f} duman {sum(m[2] for m in du.menfez):.0f}")
    hiz = []
    for ag in (ta, du, eg):
        for n in ag.ebe:
            o = ag.olcu[n]; v = ag.Q[n] / 3600 / (o['w'] * o['h'] / 1e6)
            hiz.append((ag.tur, round(v, 2)))
    rap.append('maks kanal hızı: ' + str({t: max(v for tt, v in hiz if tt == t) for t in ('taze', 'egzoz', 'duman')}))
    return rap


for s in kontrol():
    print('KONTROL', s)
dd = ezdxf.readfile(CIKTI)
au = dd.audit()
print('KONTROL audit hata:', len(au.errors), 'düzeltme:', len(au.fixes), 'sürüm:', dd.dxfversion,
      'katmanlar:', sorted(l.dxf.name for l in dd.layers if l.dxf.name not in ('0', 'Defpoints')))
