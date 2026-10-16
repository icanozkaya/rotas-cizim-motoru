# -*- coding: utf-8 -*-
"""2750 ada 7 parsel A blok BODRUM KAT SIĞINAK HAVALANDIRMA projesi (duman tahliyeli) — plan 1/50 + şema + hesap tabloları.

Kullanıcı kuralları (motor/siginak/README.md):
  taze hava = alan x h x 4 /h -> 100'e yukarı; egzoz = seçilen taze havanın %10 eksiği;
  alan > 100 m² -> duman tahliye 10 /h -> 500'e yukarı; perde geçişi v = 2,5 m/s ile standart dikdörtgen.
  BU PROJEDE alan = BRÜT 428,84 m² (kullanıcı 16.10.2026); h = 2,95 m.
Girdi : /tmp/claude-0/ab/mim_fl.pkl (dwg2dxf + dxfparse düz liste, cp1254), /tmp/claude-0/ab/kat_A_B.json (mahal poligonları)
Çıktı : proje/ab2750/AB2750_SIGINAK_HAVALANDIRMA.dxf  (R2010, cm, yalnız DXF)
Kontrol: python3 siginak_hav.py --kontrol  (kolon/perde kesişimi, çizgi binmesi, yazı binmesi, açık kanal ucu, hesap tekrarı)
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
import kanal as K                                    # kanal_sec, menfez_sec, surtunme (deneme/kanal modülü)

PRJ = os.path.join(KOK, 'proje', 'new_block_siginak')
MIM_DXF = os.path.join(PRJ, 'new_block_mimari.dxf')
MIM_JSON = os.path.join(PRJ, 'nb_mimari.json')       # motor/siginak/nb_mimari.py çıktısı
CIKTI = os.path.join(PRJ, 'NEW_BLOCK_SIGINAK_HAVALANDIRMA.dxf')
ALTLIK_KUTU = (357700, -615300, 359300, -609850)    # bodrum kat planı (tamamı)
MJ = json.load(open(MIM_JSON))

# ============================================================== HESAP (kullanıcı kuralı; bu projede BRÜT alan — kullanıcı isteği 16.10.2026)
HN = 2.95; N_TH = 4; N_DT = 10; V_GEC = 2.5; ESIK = 100.0          # h = 2,95 m (planda "SIĞINAK (h 295)")
OLCU = [(30, 20), (40, 20), (40, 25), (40, 30), (50, 30), (50, 40), (60, 40), (60, 50), (70, 50), (80, 50),
        (80, 60), (100, 60), (100, 70), (100, 80), (120, 80), (140, 80), (140, 100), (160, 100), (180, 100), (200, 100)]
KISI_M2 = 1.0           # kişi başına alan (kabul)
KORUMA = 4.5            # >150 kişi: 4,5 m³/h-kişi (yönetmelik tablosu)
A_BRUT = 428.84                                   # kullanıcı: hesaba esas BRÜT alan 428,84 m²


def yukari(q, adim):
    return int(math.ceil(q / adim - 1e-9) * adim)


def gecis(q):
    """döşeme geçişi (riser): kullanıcının gösterdiği hiza 70 cm derin -> kısa kenar ≤ 70, uzun kenar 10 cm adımlı"""
    a = q / 3600 / V_GEC * 1e4
    b, h = next(((b, h) for b, h in OLCU if b * h >= a and h <= 70), (int(math.ceil(a / 70 / 10) * 10), 70))
    return b, h, a


def tr(v, n=2):
    return f'{v:,.{n}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def hesap():
    A = A_BRUT                                       # BRÜT (kullanıcı)
    V = A * HN; qth = V * N_TH; qsec = yukari(qth, 100); qeg = int(round(qsec * 0.9))
    qdt = V * N_DT; qdts = yukari(qdt, 500)
    kisi = int(A // KISI_M2)
    return dict(ad='SIĞINAK', A=A, V=V, qth=qth, qsec=qsec, qeg=qeg, qdt=qdt, qdts=qdts, dt=A > ESIK,
                gth=gecis(qsec), geg=gecis(qeg), gdt=gecis(qdts), kisi=kisi, qkor=kisi * KORUMA,
                na=dict(brut=A_BRUT, poligon=Polygon(MJ['sig'])))


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


# ============================================================== MİMARİ ALTLIK (kullanıcı DXF'i, tek katman MKDU0; taramalı betonarme ayrı katmana)
MIM_CIZ = []      # LineString (kontrol / yazı yerleşimi engeli)
MIM_YAZI = []     # kutu
KOLON_POLY = [Polygon(p) for p in MJ['betonarme']]
KOLON_U = unary_union(KOLON_POLY).buffer(2.0)
KUTU_G = box(*ALTLIK_KUTU)


def kutuda(p):
    return ALTLIK_KUTU[0] <= p[0] <= ALTLIK_KUTU[2] and ALTLIK_KUTU[1] <= p[1] <= ALTLIK_KUTU[3]


def K_temiz(s):
    import re
    s = re.sub(r'\\[A-Za-z][^;]*;', '', s)
    return s.replace('{', '').replace('}', '').replace('\\P', ' ').replace('%%U', '').strip()


def mimari():
    md = ezdxf.readfile(MIM_DXF)
    for e in md.modelspace():
        t = e.dxftype()
        if e.dxf.layer == 'M_Yazı':          # kullanıcının çıkış hizası işareti (çizime alınmaz; riserler bu hizada)
            continue
        if t == 'LINE':
            a_, b_ = (e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1])
            if math.dist(a_, b_) < 0.01:
                continue
            g = LineString([a_, b_])
            lay = 'ROTAS-MIMARI-KOLON' if KOLON_U.contains(g) else 'ROTAS-MIMARI'
            msp.add_line(a_, b_, dxfattribs={'layer': lay}); MIM_CIZ.append(g)
        elif t == 'LWPOLYLINE':
            pts = [(q[0], q[1]) for q in e.get_points()]
            if len(pts) < 2:
                continue
            g = LineString(pts + ([pts[0]] if e.closed else []))
            lay = 'ROTAS-MIMARI-KOLON' if KOLON_U.contains(g) else 'ROTAS-MIMARI'
            msp.add_lwpolyline(pts, close=e.closed, dxfattribs={'layer': lay}); MIM_CIZ.append(g)
        elif t == 'ARC':
            c = (e.dxf.center[0], e.dxf.center[1]); r = e.dxf.radius; a0, a1 = e.dxf.start_angle, e.dxf.end_angle
            msp.add_arc(c, r, a0, a1, dxfattribs={'layer': 'ROTAS-MIMARI'})
            if a1 < a0: a1 += 360
            MIM_CIZ.append(LineString([(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / 12)),
                                        c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / 12))) for i in range(13)]))
        elif t == 'CIRCLE':
            c = (e.dxf.center[0], e.dxf.center[1])
            msp.add_circle(c, e.dxf.radius, dxfattribs={'layer': 'ROTAS-MIMARI'})
            MIM_CIZ.append(Point(c).buffer(e.dxf.radius, 16).exterior)
        elif t == 'TEXT':
            x, y = e.dxf.insert[0], e.dxf.insert[1]; h = e.dxf.height
            s_ = K_temiz(e.dxf.text)
            if not s_:
                continue
            rot = e.dxf.get('rotation', 0.0); wf = e.dxf.get('width', 1.0)
            ee = msp.add_text(s_, height=h, rotation=rot, dxfattribs={'layer': 'ROTAS-MIMARI', 'style': 'ROTAS', 'width': wf})
            ee.set_placement((x, y), align=TA.LEFT)
            bx = box(x, y - h * 0.25, x + len(s_) * h * 0.62 * wf, y + h * 1.05)
            if rot:
                from shapely import affinity
                bx = affinity.rotate(bx, rot, origin=(x, y))
            MIM_YAZI.append(bx)


mimari()
ENGEL_MIM = MIM_CIZ + [g.exterior for g in KOLON_POLY]

# ============================================================== KANAL AĞLARI
# ağ tanımı: kök noktası, kenar listesi (ebeveyn->çocuk), menfezler (düğüm, taraf, debi)
CFG = {
    'taze': dict(lay=TAZE, vmax=8.0, hmax=400, onek='TM', ters=False, mv=2.0),
    'egzoz': dict(lay=EGZ, vmax=8.0, hmax=400, onek='EM', ters=True, mv=2.0),
    'duman': dict(lay=DUM, vmax=8.0, hmax=500, onek='DM', ters=True, mv=3.0),
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
n_tm, n_em, n_dm = 17, 10, 13
S, N_, E, W_ = (0, -1), (0, 1), (1, 0), (-1, 0)
TAZE_Q = q_th / n_tm; DUM_Q = q_dt / n_dm

# ---- ÇIKIŞLAR: kullanıcının gösterdiği hiza (alt salon üst kenarı, y -613415..-613486): döşemeden düşey baca (riser),
#      "zemin kotuna çıkacak direkt". Fanlar sığınak içinde (kullanıcı: "fanlar içerde kalacak"), riser altındaki inişlerde.
#      Hiza batısı (x<358637) perde altı, doğusu şerite açık geçit -> kuzeye giden hatlar geçitten.
Y_RS = -613450
X_RD, X_RT, X_RE = 358510, 358810, 359100            # duman / taze / egzoz riserleri
Y_GSK = -613514; Y_K = -613528; Y_T = -613720       # klape ekseni / ağ kökü / ayrım
WC_Y0, WC_Y1 = -610155, -609961
WC_HUCRE = [(357832, 358017), (358042, 358177), (358202, 358337), (358362, 358497), (358522, 358657),
            (358682, 358817), (358842, 358977), (359002, 359187)]
WC_Q = 100.0
Y_AN = -610060
EGZ_Q = (q_eg - WC_Q * len(WC_HUCRE)) / n_em
Y_WCK = -610260

# ---- duman: riser -> GSK-2 -> DTF-1 -> T (-613720): doğu kolu -> geçit 358700 -> şerit -> üst salon y -610600 / düz: alt salon y -614000
du = Ag('duman', (X_RD, Y_K))
dT = du.yol('K', (X_RD, Y_T))
du.yol(dT, (X_RD, -614000), (357950, -614000))
du.yol(dT, (358700, Y_T), (358700, -613000), (358840, -612860), (358840, -611310), (358895, -611255), (358895, -610600), (358000, -610600))
for p, t in [((X_RD, -613870), E), ((358400, -614000), S), ((358250, -614000), N_), ((358100, -614000), S), ((357950, -614000), S),
             ((358840, -612100), W_), ((358840, -611700), W_), ((358840, -611400), W_),
             ((358800, -610600), S), ((358680, -610600), N_), ((358500, -610600), S), ((358260, -610600), N_), ((358000, -610600), S)]:
    du.menfez_ekle(p, t, DUM_Q)

# ---- taze: riser -> GSK-1 -> SHC-1 -> T (-613720): doğu kolu -> 358960 -> şerit -> üst salon y -610420 / düz: alt salon y -614500
ta = Ag('taze', (X_RT, Y_K))
tT = ta.yol('K', (X_RT, Y_T))
ta.yol(tT, (X_RT, -614500), (357950, -614500))
ta.yol(tT, (358935, Y_T), (358935, -611290), (358955, -611270), (358955, -610420), (358000, -610420))
for p, t in [((X_RT, -613950), E), ((X_RT, -614200), E), ((358620, -614500), N_), ((358400, -614500), N_), ((358180, -614500), N_), ((357950, -614500), S),
             ((358935, -613200), W_), ((358935, -612600), E), ((358935, -612150), E), ((358935, -611750), E), ((358935, -611400), E),
             ((358955, -611000), W_), ((358800, -610420), S), ((358650, -610420), N_), ((358450, -610420), S), ((358200, -610420), N_), ((358000, -610420), S)]:
    ta.menfez_ekle(p, t, TAZE_Q)

# ---- egzoz: riser -> GSK-3 -> EF-1 -> T (-613720): doğu kolu -> 359140 -> şerit -> 359005 -> WC önü kolu / düz: -613790 batı -> 358700 -> alt salon y -614400
eg = Ag('egzoz', (X_RE, Y_K))
eT = eg.yol('K', (X_RE, -613690))
eg.yol(eT, (X_RE, -613790), (358700, -613790), (358700, -614400), (357950, -614400))
en = eg.yol(eT, (359003, -613690), (359003, -612760), (359080, -612683), (359080, -611330), (359005, -611255), (359005, Y_WCK))
eg.yol(en, (357870, Y_WCK))
eg.yol(en, (359094, Y_WCK), (359094, Y_AN))
for p, t in [((358700, -614100), W_), ((358400, -614400), N_), ((357950, -614400), S),
             ((359003, -613100), E), ((359080, -612400), E), ((359080, -611600), E),
             ((359005, -610400), E), ((358830, Y_WCK), S), ((358350, Y_WCK), S), ((357870, Y_WCK), S)]:
    eg.menfez_ekle(p, t, EGZ_Q)
WC_X = [357960, 358080, 358300, 358400, 358620, 358720, 358935]


def wc_dal(ag, x_, y_kol, y_an):
    for a, ch in list(ag.cocuk.items()):
        for b in ch:
            A_, B_ = ag.N[a], ag.N[b]
            if abs(A_[1] - y_kol) < 0.01 and abs(B_[1] - y_kol) < 0.01 and min(A_[0], B_[0]) < x_ < max(A_[0], B_[0]):
                nm = ag.bol(a, b, (x_, y_kol))
                return ag.yol(nm, (x_, y_an))
    raise ValueError(x_)


for x_ in WC_X:
    wc_dal(eg, x_, Y_WCK, Y_AN)
for nm, pp in list(eg.N.items()):
    if abs(pp[1] - Y_AN) < 0.01 and not eg.cocuk[nm]:
        eg.menfez.append((nm, 'A', WC_Q))

for ag in (ta, du, eg):
    ag.akis()

# ---- bileşen gövdeleri
GOVDE = []
gth_b, gth_h, _ = R['gth']; gdt_b, gdt_h, _ = R['gdt']; geg_b, geg_h, _ = R['geg']


def riser_ciz(c, b, h, lay=GEC):
    """döşeme geçişli düşey baca (zemin kotuna): çelik kovan + yukarı çıkış çaprazı"""
    x0, y0, x1, y1 = c[0] - b / 2, c[1] - h / 2, c[0] + b / 2, c[1] + h / 2
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, True)
    PL([(x0 + 4, y0 + 4), (x1 - 4, y0 + 4), (x1 - 4, y1 - 4), (x0 + 4, y1 - 4)], lay, True)
    L((x0 + 4, y0 + 4), (x1 - 4, y1 - 4), lay); L((x0 + 4, y1 - 4), (x1 - 4, y0 + 4), lay)
    adet('kovan')
    return box(x0, y0, x1, y1)


k_th = riser_ciz((X_RT, Y_RS), gth_b, gth_h)
k_dt = riser_ciz((X_RD, Y_RS), gdt_b, gdt_h)
k_eg = riser_ciz((X_RE, Y_RS), geg_b, geg_h)
gsk_th = gsk((X_RT, Y_GSK), S, ta.w(ta.cocuk['K'][0]))
gsk_dt = gsk((X_RD, Y_GSK), N_, du.w(du.cocuk['K'][0]))
gsk_eg = gsk((X_RE, Y_GSK), N_, eg.w(eg.cocuk['K'][0]))
SHC_C = (X_RT, -613602); SHC_W = 130
shc_g = shc_yatay(SHC_C, 130, 100, S)
DF_C = (X_RD, -613602)
fan_dt = fan_aksiyel(DF_C, N_, 55)
EF_C = (X_RE, -613592)
fan_eg = fan_kanal(EF_C, N_, 110, 80)
GOVDE += [k_th, gsk_th, shc_g, k_dt, gsk_dt, fan_dt, k_eg, gsk_eg, fan_eg]
AN_R = 15.0
GOVDE += [Point(eg.N[nm]).buffer(AN_R, 32) for nm, t, q in eg.menfez if t == 'A']


def bag(x, b, h, ag):
    w0 = ag.w(ag.cocuk['K'][0])
    return [trap((x, Y_RS - h / 2 + 2), b - 4, (x, Y_GSK + 14), w0)]


bag_th = bag(X_RT, gth_b, gth_h, ta); bag_dt = bag(X_RD, gdt_b, gdt_h, du); bag_eg = bag(X_RE, geg_b, geg_h, eg)
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


def plan_icinde(g):
    return SIG_ALAN.buffer(-2).contains(g)


SIG_ALAN = unary_union([R['na']['poligon'], box(357832, -610170, 359187, WC_Y0 - 0.1)] + [box(x0, WC_Y0, x1, WC_Y1) for x0, x1 in WC_HUCRE])


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


for ag in (ta, du, eg):
    kanal_etiketleri(ag)

for ag, m in [x for x in MENFEZLER if x[1].get('an')]:
    etiket(add(m['p'], (1, 0), 10), [m['no']], 6.5, YAZI, oncelik=[add(m['p'], (0, 1), 12), add(m['p'], (1, 1), 18)],
           alan=SIG_ALAN.buffer(-1), haric=m['govde'], rmax=60)
_an = [m for _, m in MENFEZLER if m.get('an')]
if _an:
    etiket(add(_an[-1]['p'], (1, 0), 30), [f"EA-1 … EA-{len(_an)} WC EGZOZ ANEMOSTADI {_an[0]['mw']}",
                                         f"{len(_an)} x {tr(WC_Q, 0)} m³/h — dal kanalları 150x150"], 7.5, YAZI,
           oncelik=[(24300, -34720), (24300, -34740), (24300, -34640)], alan=SIG_ALAN.buffer(-1), rmax=400, leader=False)
for ag, m in [x for x in MENFEZLER if not x[1].get('an')]:
    satir = [f"{m['no']}  {m['mw']}x{m['mh']}", f"Q={tr(m['q'], 0)} m³/h"]
    onc = [add(m['p'], m['n'], 22), add(add(m['p'], m['n'], 22), m['d'], 30), add(add(m['p'], m['n'], 22), m['d'], -30)]
    etiket(m['p'], satir, 7.5, YAZI, oncelik=onc, alan=SIG_ALAN.buffer(-1), haric=m['govde'], rmax=400)

# cihaz / fan / geçiş etiketleri
CEVRE = box(357300, -615200, 359800, -609700)
etiket((SHC_C[0] - 50, SHC_C[1] + 30), ['SHC-1'], 9.0, CHZ, alan=SIG_ALAN.buffer(-1), haric=shc_g, rmax=250)
if etiket((DF_C[0] - 62, DF_C[1]), ['DTF-1 (F400)'], 9.0, CHZ, oncelik=[(358340, -613620), (358340, -613600)], alan=SIG_ALAN.buffer(-1), haric=fan_dt, rmax=300) is None:
    TXT((DF_C[0] - 54, DF_C[1] + 48), 'DTF-1', 6.0, CHZ, TA.MIDDLE_LEFT, kayit=False)   # cihaz gövdesi içinde künye
etiket((EF_C[0] + 40, EF_C[1]), ['EF-1'], 9.0, CHZ, alan=SIG_ALAN.buffer(-1), haric=fan_eg, rmax=250)
_cy = -614880
_CIH0 = len(msp)
for s_ in ['CİHAZLAR (sığınak içinde, çıkış hizasının altında):',
           f"SHC-1  SIĞINAK HAVALANDIRMA CİHAZI — el + motor tahrikli, toz (G4) + kum filtreli, by-pass damperli — NORMAL {tr(q_th, 0)} m³/h / KORUMA {tr(R['qkor'], 0)} m³/h",
           f"DTF-1  DUMAN TAHLİYE FANI (aksiyel, kanal tipi) — {tr(q_dt, 0)} m³/h — F400 (400 °C / 2 saat)",
           f"EF-1   KANAL TİPİ EGZOZ FANI — {tr(q_eg, 0)} m³/h",
           f"GSK-1/2/3  gaz sızdırmaz klape (el kumandalı), her döşeme geçişinin hemen altında",
           f"DÖŞEME GEÇİŞLERİ (çelik kovan, zemin kotuna düşey baca): TAZE {gth_b}x{gth_h} / DUMAN {gdt_b}x{gdt_h} / EGZOZ {geg_b}x{geg_h} cm — v = 2,5 m/s"]:
    TXT((357850, _cy), s_, 9.0 if _cy == -614880 else 8.0, CHZ, TA.MIDDLE_LEFT); _cy -= 18
_CIH1 = len(msp)
for c_, ad_, b_, h_, kod, gk in ((X_RE, 'EGZOZ', geg_b, geg_h, 'GSK-3', gsk_eg), (X_RT, 'TAZE HAVA', gth_b, gth_h, 'GSK-1', gsk_th),
                                (X_RD, 'DUMAN', gdt_b, gdt_h, 'GSK-2', gsk_dt)):
    etiket((c_, Y_RS + 8), [f"{ad_} ↑ {b_}x{h_}"], 7.0, GEC,
           alan=CEVRE, haric=box(c_ - b_ / 2, Y_RS - h_ / 2, c_ + b_ / 2, Y_RS + h_ / 2).union(gk), rmax=400)
# kesişme notları (alttan geçen kanal kesikli)
for ust, alt_, ad_u, ad_a, lay_ in ((U_ta, U_du, 'TAZE HAVA', 'DUMAN', DUM), (U_ta, U_eg, 'TAZE HAVA', 'EGZOZ', EGZ), (U_du, U_eg, 'DUMAN', 'EGZOZ', EGZ)):
    _kes = ust.intersection(alt_)
    for kk in (_kes.geoms if hasattr(_kes, 'geoms') else [_kes]):
        if kk.is_empty or kk.area < 1:
            continue
        cc = kk.centroid
        etiket((cc.x, cc.y), [f"{ad_a} {ad_u} ALTINDAN GEÇER"], 6.0, lay_,
               alan=SIG_ALAN.buffer(-1), haric=kk.buffer(2), rmax=400)
# pantolon bölme notları
for ag in (ta, du, eg):
    for (pa, pb) in getattr(ag, 'bolme', []):
        etiket(pa, ['PANTOLON — AYIRICI BÖLME LEVHASI'], 6.5, ag.c['lay'], alan=SIG_ALAN.buffer(-1), haric=ag.U, rmax=300)

# plan başlığı
msp.add_lwpolyline([(357700, -615060), (359300, -615060), (359300, -609850), (357700, -609850)], close=True, dxfattribs={'layer': 'ROTAS-HAV-CERCEVE', 'const_width': 1.5})
TXT((357850, -614800), 'BODRUM KAT SIĞINAK HAVALANDIRMA PLANI (DUMAN TAHLİYELİ)', 24, 'ROTAS-HAV-BASLIK', TA.MIDDLE_LEFT)
TXT((357850, -614840), f"ÖLÇEK 1/50 — SIĞINAK BRÜT ALANI {tr(R['A'])} m²  —  "
                       f"TAZE HAVA {tr(q_th, 0)} m³/h  /  EGZOZ {tr(q_eg, 0)} m³/h  /  DUMAN TAHLİYE {tr(q_dt, 0)} m³/h", 10, 'ROTAS-HAV-BASLIK', TA.MIDDLE_LEFT)

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
            ['4', 'GAZ SIZDIRMAZ KLAPE + ÇELİK KOVAN', f"{r['gth'][0]}x{r['gth'][1]} / {r['geg'][0]}x{r['geg'][1]} / {r['gdt'][0]}x{r['gdt'][1]} cm", '3', 'Döşeme geçişleri']]
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
    kv(f"{r['ad']} GENEL HAVALANDIRMA HESABI",
       [('Sığınak Brüt Alanı', f"{tr(r['A'])} m²"), ('Sığınak Yüksekliği', f"{tr(HN)} m"), ('Sığınak Hacmi', f"{tr(r['V'])} m³"),
        ('Hava Değişim Sayısı', f"{N_TH} defa/saat"), ('Taze Hava İçin Gerekli Hava', f"{tr(r['qth'])} m³/h"),
        ('Seçilen Taze Hava Debisi', f"{tr(r['qsec'], 0)} m³/h"), ('Egzoz Debisi (taze havadan %10 az)', f"{tr(r['qeg'], 0)} m³/h"),
        (f'Döşeme Geçişi - Taze Hava (v = {tr(V_GEC, 1)} m/s)', f"{r['gth'][0]} × {r['gth'][1]} cm"),
        (f'Döşeme Geçişi - Egzoz (v = {tr(V_GEC, 1)} m/s)', f"{r['geg'][0]} × {r['geg'][1]} cm"),
        (f'Sığınak Kişi Kapasitesi ({tr(KISI_M2, 0)} m² brüt alan / kişi)', f"{r['kisi']} kişi"),
        (f'Koruma Havalandırması ({tr(KORUMA, 1)} m³/h-kişi)', f"{tr(r['qkor'], 0)} m³/h")])
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
        (f'Döşeme Geçişi - Duman Tahliye (v = {tr(V_GEC, 1)} m/s)', f"{r['gdt'][0]} × {r['gdt'][1]} cm")])
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
    """3 panel: TAZE HAVA (koruma havalandırması) | EGZOZ | DUMAN TAHLİYE. y0 sığınak döşemesi (-2,20), 1 cm = 1 cm (ölçeksiz prensip)."""
    S_T((x0, y0 + 490), 'SIĞINAK HAVALANDIRMA ŞEMASI (PRENSİP KESİT — ÖLÇEKSİZ)', 20, 'ROTAS-HAV-BASLIK')
    Hk = 295; G = y0 + 220; ys = y0 + 150; kanal_y = y0 + 220
    PW = 1150
    # ---------------- panel 1: taze hava (dış duvar solda)
    xw = x0 + 330                     # perde dış yüzü
    S_T((xw + 250, y0 + 420), 'A) TAZE HAVA / KORUMA HAVALANDIRMASI', 13, 'ROTAS-HAV-BASLIK')
    s_duvar_kesit(xw, y0 - 30, y0 + Hk)
    xe = xw + 25 + PW
    S_L((xw + 25, y0), (xe, y0)); S_L((xw + 25, y0 - 30), (xe, y0 - 30))
    S_L((xw, y0 + Hk), (xe, y0 + Hk)); S_L((xw, y0 + Hk - 15), (xe, y0 + Hk - 15))
    hh = R['gth'][1]
    cx0 = xw + 130; cx1 = cx0 + 320; ch = 120
    xr0 = cx0 + 50
    S_box(xr0 - hh / 2 - 5, y0 + Hk - 20, xr0 + hh / 2 + 5, y0 + Hk + 5, GEC)              # döşemede çelik kovan
    S_PL([(xr0 - hh / 2, y0 + Hk + 5), (xr0 - hh / 2, y0 + Hk + 90)], BACA); S_PL([(xr0 + hh / 2, y0 + Hk + 5), (xr0 + hh / 2, y0 + Hk + 90)], BACA)
    S_T((xr0 + hh / 2 + 10, y0 + Hk + 70), 'DÜŞEY BACA — ZEMİN KOTUNA (dış ağız mimari projeye göre)', 8, BACA)
    s_ok((xr0, y0 + Hk + 55), (0, -1))
    kovA = box(xr0 - hh / 2 - 5, y0 + Hk - 20, xr0 + hh / 2 + 5, y0 + Hk + 5)
    gskA = box(xr0 - hh / 2 - 4, y0 + Hk - 60, xr0 + hh / 2 + 4, y0 + Hk - 32)
    S_box(*gskA.bounds, CHZ); S_L((xr0 - hh / 2 + 2, y0 + Hk - 52), (xr0 + hh / 2 - 2, y0 + Hk - 40), CHZ); S_C((xr0, y0 + Hk - 46), 2.5, CHZ)
    cih = box(cx0, y0, cx1, y0 + ch)
    s_kanal_yol([(xr0, y0 + Hk + 5), (xr0, y0 + ch)], R['gth'][0] * 0.6, TAZE, [kovA, gskA, cih])
    s_ok((xr0, y0 + ch + 30), (0, -1))
    # cihaz
    S_box(cx0, y0, cx1, y0 + ch, CHZ)
    S_L((cx0 + 100, y0), (cx0 + 100, y0 + ch), CHZ); S_L((cx0 + 200, y0), (cx0 + 200, y0 + ch), CHZ)
    pts = []; yy = y0 + ch - 10; k = 0
    while yy > y0 + 8:
        pts.append((cx0 + 15 if k % 2 == 0 else cx0 + 85, yy)); yy -= 10; k += 1
    S_PL(pts, CHZ)
    for i in range(6):
        for j in range(4):
            S_C((cx0 + 115 + i * 14, y0 + 18 + j * 25), 1.8, CHZ)
    S_L((cx0 + 105, y0 + ch - 8), (cx0 + 195, y0 + ch - 22), CHZ)          # by-pass damper kanadı
    fc = (cx0 + 255, y0 + 62); S_C(fc, 38, CHZ); S_C(fc, 11, CHZ)
    for k in range(8):
        t = k * math.pi / 4
        S_L((fc[0] + 11 * math.cos(t), fc[1] + 11 * math.sin(t)), (fc[0] + 36 * math.cos(t + 0.5), fc[1] + 36 * math.sin(t + 0.5)), CHZ)
    S_box(cx1 - 34, y0 + 6, cx1 - 6, y0 + 32, CHZ); S_T((cx1 - 20, y0 + 19), 'M', 10, CHZ, TA.MIDDLE_CENTER)
    S_PL([(cx1, y0 + 62), (cx1 + 25, y0 + 62), (cx1 + 25, y0 + 85)], CHZ); S_C((cx1 + 25, y0 + 91), 6, CHZ)
    S_T((cx1 + 38, y0 + 91), 'EL KOLU', 8, CHZ, TA.MIDDLE_LEFT)
    S_T((cx0 + 50, y0 - 48), 'TOZ FİLTRE (G4)', 8, CHZ, TA.MIDDLE_CENTER)
    S_T((cx0 + 150, y0 - 48), 'KUM FİLTRE', 8, CHZ, TA.MIDDLE_CENTER)
    S_T((cx0 + 150, y0 - 62), 'BY-PASS DAMPERLİ', 8, CHZ, TA.MIDDLE_CENTER)
    S_T((cx0 + 260, y0 - 48), 'FAN + MOTOR', 8, CHZ, TA.MIDDLE_CENTER)
    S_T((cx0 + 160, y0 - 90), f"SHC-1 SIĞINAK HAVALANDIRMA CİHAZI — NORMAL {tr(q_th, 0)} m³/h, KORUMA {tr(R['qkor'], 0)} m³/h, {BAS['taze']['sec']} Pa", 9, CHZ, TA.MIDDLE_CENTER)
    # çıkış -> tavana -> üfleme kanalı
    o0 = ta.olcu[ta.cocuk['K'][0]]
    wt = o0['h'] / 10
    xr = cx1 - 70
    s_kanal_yol([(xr, y0 + ch), (xr, kanal_y), (xe - 40, kanal_y)], wt, TAZE)
    s_ok((xr, y0 + ch + 35), (0, 1)); s_ok((xr + 300, kanal_y), (1, 0))
    for xm in (xr + 180, xr + 460, xr + 740):
        s_menfez_alt(xm, kanal_y - wt / 2, 30, False)
    S_T((xr + 120, kanal_y + wt / 2 + 18), f"TAZE HAVA KANALI {tr(q_th, 0)} m³/h — {o0['w']}x{o0['h']}", 9, TAZE)
    S_T((xr + 120, kanal_y - wt / 2 - 52), f"TAZE HAVA MENFEZLERİ ({n_tm} AD. x {tr(TAZE_Q, 0)} m³/h)", 9, MEN)
    S_T((xr0 - hh / 2 - 12, y0 + Hk - 30), f"DÖŞEME GEÇİŞİ {R['gth'][0]}x{R['gth'][1]} cm", 8, GEC, TA.MIDDLE_RIGHT)
    S_T((xr0 - hh / 2 - 12, y0 + Hk - 44), 'ÇELİK KOVAN + GSK-1', 8, GEC, TA.MIDDLE_RIGHT)
    S_T((xw - 60, y0 + 150), 'SIĞINAK ÇEVRE PERDESİ', 8, SL, TA.MIDDLE_RIGHT)
    kot(xe - 30, y0, '±0,00 SIĞINAK DÖŞEMESİ', False)
    kot(xe - 30, y0 + Hk, '+2,95 SIĞINAK TAVANI', False)
    kot(xr + 30, kanal_y - wt / 2 - 22, 'KANAL ALT +2,40', True)
    # ---------------- panel 2 ve 3: egzoz / duman (dış duvar sağda)
    for i, (baslik, lay, qq, kod, ww, gg, fan, ad) in enumerate([
            ('B) EGZOZ', EGZ, q_eg, 'GSK-3', eg.olcu[eg.cocuk['K'][0]], R['geg'], 'kanal', 'EGZOZ'),
            ('C) DUMAN TAHLİYE', DUM, q_dt, 'GSK-2', du.olcu[du.cocuk['K'][0]], R['gdt'], 'aksiyel', 'DUMAN')]):
        bx = xe + 120 + i * (PW + 330)
        wx = bx + PW                    # perde iç yüzü
        S_T((bx + 400, y0 + 420), baslik, 13, 'ROTAS-HAV-BASLIK')
        S_L((bx, y0), (wx, y0)); S_L((bx, y0 - 30), (wx, y0 - 30))
        S_L((bx, y0 + Hk), (wx + 25, y0 + Hk)); S_L((bx, y0 + Hk - 15), (wx + 25, y0 + Hk - 15))
        s_duvar_kesit(wx, y0 - 30, y0 + Hk)
        hk = ww['h'] / 10; gh = gg[1]
        x_fan = wx - 260
        if fan == 'kanal':
            fb = box(x_fan - 50, kanal_y - 40, x_fan + 50, kanal_y + 40)
            S_box(*fb.bounds, CHZ)
            S_C((x_fan, kanal_y), 24, CHZ); S_C((x_fan, kanal_y), 8, CHZ)
            fan_ad = f"EF-1 KANAL TİPİ EGZOZ FANI {tr(qq, 0)} m³/h {BAS['egzoz']['sec']} Pa"
        else:
            fb = box(x_fan - 55, kanal_y - 50, x_fan + 55, kanal_y + 50)
            S_box(*fb.bounds, CHZ)
            S_PL([(x_fan, kanal_y), (x_fan - 18, kanal_y + 38), (x_fan + 18, kanal_y + 38)], CHZ, True)
            S_PL([(x_fan, kanal_y), (x_fan - 18, kanal_y - 38), (x_fan + 18, kanal_y - 38)], CHZ, True)
            S_L((x_fan - 45, kanal_y - 50), (x_fan - 45, kanal_y + 50), CHZ); S_L((x_fan + 45, kanal_y - 50), (x_fan + 45, kanal_y + 50), CHZ)
            fan_ad = f"DTF-1 DUMAN TAHLİYE FANI {tr(qq, 0)} m³/h {BAS['duman']['sec']} Pa F400"
        xr = wx - 120
        kov = box(xr - gh / 2 - 5, y0 + Hk - 20, xr + gh / 2 + 5, y0 + Hk + 5)
        S_box(*kov.bounds, GEC)
        gk = box(xr - gh / 2 - 4, y0 + Hk - 60, xr + gh / 2 + 4, y0 + Hk - 32)
        S_box(*gk.bounds, CHZ); S_L((xr - gh / 2 + 2, y0 + Hk - 52), (xr + gh / 2 - 2, y0 + Hk - 40), CHZ); S_C((xr, y0 + Hk - 46), 2.5, CHZ)
        S_PL([(xr - gh / 2, y0 + Hk + 5), (xr - gh / 2, y0 + Hk + 90)], BACA); S_PL([(xr + gh / 2, y0 + Hk + 5), (xr + gh / 2, y0 + Hk + 90)], BACA)
        s_kanal_yol([(bx + 40, kanal_y), (x_fan, kanal_y)], hk, lay, [fb])
        s_kanal_yol([(x_fan, kanal_y), (xr, kanal_y), (xr, y0 + Hk + 5)], gh * 0.6, lay, [fb, gk, kov])
        for xm in (bx + 160, bx + 440, bx + 720):
            s_menfez_alt(xm, kanal_y - hk / 2, 45 if lay == EGZ else 70, True)
        s_ok((bx + 300, kanal_y), (1, 0)); s_ok((bx + 860, kanal_y), (1, 0)); s_ok((xr, y0 + Hk + 55), (0, 1))
        S_T((x_fan + 40, kanal_y - 92), fan_ad, 9, CHZ, TA.MIDDLE_RIGHT)
        S_T((bx + 140, kanal_y + hk / 2 + 18), f"{'EGZOZ' if lay == EGZ else 'DUMAN EGZOZ'} KANALI {tr(qq, 0)} m³/h — {ww['w']}x{ww['h']}", 9, lay)
        S_T((bx + 140, kanal_y - hk / 2 - 52), f"{ad} MENFEZLERİ ({n_em if lay == EGZ else n_dm} AD. x {tr(EGZ_Q if lay == EGZ else DUM_Q, 0)} m³/h)", 9, MEN)
        S_T((xr - gh / 2 - 12, y0 + Hk - 30), f"DÖŞEME GEÇİŞİ {gg[0]}x{gg[1]} cm", 8, GEC, TA.MIDDLE_RIGHT)
        S_T((xr - gh / 2 - 12, y0 + Hk - 44), f"ÇELİK KOVAN + {kod}", 8, GEC, TA.MIDDLE_RIGHT)
        S_T((xr + gh / 2 + 10, y0 + Hk + 70), 'DÜŞEY BACA — ZEMİN KOTUNA', 8, BACA, TA.MIDDLE_LEFT)
        kot(bx + 20, y0, '±0,00', True)
        kot(bx + 20, y0 + Hk, '+2,95', True)
    return wx + 330



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
         f"DÖŞEME GEÇİŞİ ÇELİK KOVAN + DÜŞEY BACA (zemin kotuna) — {ADET.get('kovan', 0)} AD."),
        (lambda yy: (S_C((x + 40, yy), 14, MEN), S_C((x + 40, yy), 9, MEN), S_C((x + 40, yy), 4, MEN)),
         f"WC EGZOZ ANEMOSTADI (EA) — {ADET.get('anemostad', 0)} AD."),
        (lambda yy: (S_L((x + 5, yy + 12), (x + 40, yy + 12), TAZE), S_L((x + 5, yy - 12), (x + 40, yy - 12), TAZE),
                     S_L((x + 40, yy), (x + 75, yy), TAZE), S_L((x + 22, yy + 12), (x + 22, yy - 12), TAZE)),
         'PANTOLON AYRIM — AYIRICI BÖLME LEVHALI'),
        (lambda yy: (msp.add_arc((x + 10, yy + 20), 20, 270, 360, dxfattribs={'layer': TAZE}), msp.add_arc((x + 10, yy + 20), 32, 270, 360, dxfattribs={'layer': TAZE}),
                     msp.add_arc((x + 10, yy + 20), 8, 270, 360, dxfattribs={'layer': TAZE})), 'KAVİSLİ DİRSEK — YÖNLENDİRİCİ KANATLI'),
        (lambda yy: (S_L((x + 10, yy), (x + 70, yy), 'ROTAS-HAV-DUMAN-GIZLI'), S_L((x + 10, yy + 8), (x + 70, yy + 8), 'ROTAS-HAV-DUMAN-GIZLI')),
         'ALTTAN GEÇEN KANAL (KESİKLİ)'),
        (lambda yy: s_ok((x + 40, yy), (1, 0), 14), 'HAVA AKIŞ YÖNÜ'),
    ]
    for f_, s in ogeler:
        f_(y)
        S_T((x + 100, y), s, 10, LY)
        y -= 42
    return y


NOTLAR = [
    "Sığınak havalandırması Sığınak Yönetmeliği'ne göre normal havalandırma (4 hava değişimi) ve koruma havalandırması (filtreli) olarak yapılacaktır.",
    "Sığınak havalandırma cihazı el + elektrik motoru tahrikli, toz (G4) ve kum filtreli, by-pass damperli olarak temin edilecektir.",
    "Tüm dış hava bağlantıları mimarın gösterdiği hizada YAN YANA döşeme geçişleri ile düşey bacalarla doğrudan zemin kotuna çıkarılır (çıkış kesiti detayı); dış ağız düzeni mimari projeye göredir.",
    "Döşeme geçişlerinde betonarme dökülmeden önce plandaki ölçülerde çelik kovan yerleştirilecek, kovanlar ankrajlı ve su/gaz sızdırmaz yapılacaktır.",
    "Her döşeme geçişinin hemen altına sığınak iç tarafında el kumandalı gaz sızdırmaz klape (GSK) takılacaktır; fanlar ve SHC sığınak içindedir.",
    "Hesaba esas alan sığınak BRÜT alanıdır: 428,84 m²; yükseklik 2,95 m (mimari).",
    "WC hücrelerinin her birine egzoz hattından Ø160 tavan anemostadı (100 m³/h) bağlanmıştır.",
    "Duman tahliye fanı EN 12101-3 F400 (400 °C / 2 saat) sınıfında olacak ve yangın algılama sistemi ile otomatik devreye girecektir.",
    "Duman egzoz kanalları en az 1,0 mm galvaniz sacdan, askıları yangına dayanıklı olarak yapılacaktır.",
    "Kanallar kiriş altından geçecek şekilde kanal alt kotu sığınak döşemesinden en az +2,00 m olacak biçimde asılacaktır.",
    "Kanallar betonarme kolon, kazan dairesi ve asansör kuyusu içinden geçirilmeyecek, yalnız planda ölçüsü yazılı döşeme geçişleri kullanılacaktır.",
    "Menfezler ayar damperli (OBD) olacak ve devreye almada plandaki debilere göre ayarlanacaktır.",
    "Fan ve cihaz elektrik beslemeleri jeneratör destekli olarak elektrik projesine göre yapılacaktır.",
    "Egzoz ve duman atış ağızları komşu pencere ve kapılardan en az 3,00 m uzakta, dış zeminden +2,50 m yükseklikte panjurlu olarak yapılacaktır.",
    "Dirsekler R iç = 0,5·W kavisli ve yönlendirici kanatlı; yer olmayan yerde köşeli dirsek kanat dizili; pantolon ayrımlarda AYIRICI BÖLME levhası, T dallarda ayar kanadı (özel parça detayları).",
    "Duman kanalı taze hava dağıtım kanalının altından geçer (planda kesikli); kesişme bölgesinde iki kanal arası en az 5 cm boşluk bırakılır.",
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
yb = hesap_blok(359950, -609950, R)
_i = cer_bas(); x_sema_son = sema(361000, -610600); cer_bit(_i)
_i = cer_bas(); y_lj = lejant(361100, -610900); cer_bit(_i)
_i = cer_bas(); y_nt = notlar(362700, -610900); cer_bit(_i)


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
    """çıkış hizası A-A kesiti (güneyden bakış): üç düşey baca yan yana, döşeme geçişi + GSK + fan, zemin kotuna. yatay = plan x"""
    xa_, xb_ = 358373, 359187
    X = lambda x: x0 + (x - xa_) * KD
    Y = lambda kot: yg + kot * KD                 # kot cm, sığınak döşemesi = 0
    S_T((x0, Y(470)), 'ÇIKIŞLAR A-A KESİTİ (DÖŞEME GEÇİŞLERİ / DÜŞEY BACALAR) — 1/20', 16, 'ROTAS-HAV-BASLIK')
    S_T((x0, Y(452)), 'mimarın gösterdiği hizadan üç düşey baca yan yana, doğrudan zemin kotuna; fanlar sığınak içinde', 9, SL)
    S_L((X(xa_) - 60, Y(0)), (X(xb_) + 60, Y(0)), SL)
    S_tarama(X(xa_) - 60, Y(295), X(xb_) + 60, Y(320), 14, 'ROTAS-HAV-SEMA')          # sığınak tavan döşemesi
    S_L((X(xa_) - 60, Y(420)), (X(xb_) + 60, Y(420)), SL)
    S_T((X(xb_) + 70, Y(420)), 'ZEMİN KOT (dış ağız mimari projeye göre)', 8, SL)
    for xc, (b_, h_), ad, kod, fan_ in ((X_RD, R['gdt'][:2], 'DUMAN', 'GSK-2', 'DTF-1'), (X_RT, R['gth'][:2], 'TAZE HAVA', 'GSK-1', 'SHC-1'),
                                        (X_RE, R['geg'][:2], 'EGZOZ', 'GSK-3', 'EF-1')):
        xa, xb = X(xc - b_ / 2), X(xc + b_ / 2)
        S_box(xa - 12, Y(290), xb + 12, Y(325), GEC)                                   # çelik kovan
        S_L((xa, Y(325)), (xa, Y(420)), BACA); S_L((xb, Y(325)), (xb, Y(420)), BACA)
        S_L((xa, Y(240)), (xa, Y(290)), SL); S_L((xb, Y(240)), (xb, Y(290)), SL)
        S_box(xa - 8, Y(215), xb + 8, Y(240), CHZ); S_L((xa, Y(218)), (xb, Y(237)), CHZ)        # GSK
        S_box(xa, Y(120), xb, Y(205), CHZ)
        S_T(((xa + xb) / 2, Y(162)), fan_, 9, CHZ, TA.MIDDLE_CENTER)
        s_ok(((xa + xb) / 2, Y(370)), (0, 1) if ad != 'TAZE HAVA' else (0, -1), 16, BACA)
        S_T(((xa + xb) / 2, Y(440)), f"{ad} {b_}x{h_}", 8, GEC, TA.MIDDLE_CENTER)
        S_T(((xa + xb) / 2, Y(100)), f"{kod}", 7.5, GEC, TA.MIDDLE_CENTER)
    kot(X(xb_) + 40, Y(0), '±0,00 SIĞINAK DÖŞEMESİ', True)
    kot(X(xb_) + 40, Y(295), '+2,95 SIĞINAK TAVANI', True)
    return X(xb_) + 200


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
    detay_parca(cx, cy, '5) OFSET (45°) — DUMAN ÇIKIŞI', k5, ['GSK-2 çıkışından fan hattına kaydırma; iki adet 45° kırım, flanşlı.'])
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


_i = cer_bas(); x_det = cikis_kesit(361150, -613300); cer_bit(_i)
detaylar(364100, -611950)


_i = cer_bas()
y_t = tablo(362700, y_nt - 90, 'MENFEZ ÇİZELGESİ', ['NO', 'MENFEZ', 'ÖLÇÜ (mm)', 'ADET', 'DEBİ (m³/h)', 'v (m/s)'],
            menfez_satirlari(), [150, 260, 110, 70, 120, 90])


def bas_satir(tur, ad, kod):
    b = BAS[tur]
    return [kod, ad, tr(b['L'], 1), tr(b['sur'], 0), tr(b['yer'], 0), tr(sum(b['sabit'].values()), 0), tr(b['top'], 0), str(b['sec'])]


cer_bit(_i)
_i = cer_bas()
y_t2 = tablo(362700, y_t - 90, 'FAN BASINÇ HESABI (kritik hat: Σ R·L + Σ ζ·ρv²/2 + menfez/klape/baca; seçim = 1,1 x toplam, 50 Pa yukarı)',
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
y_t3 = tablo(359950, yb - 60, 'KANAL ÇİZELGESİ (kanal hızı 8,0 m/s sınırına yakın seçildi, v ≤ 8,0 m/s)',
             ['AĞ', 'ÖLÇÜ (mm)', 'MAKS. DEBİ (m³/h)', 'v (m/s)', 'BOY (m)', 'SAC (mm)'], kanal_satirlari(), [120, 130, 180, 110, 110, 110])
cer_bit(_i)

# ============================================================== KAYDET
doc.saveas(CIKTI)
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
    c = dict(qth=math.ceil(V * 4 / 100 - 1e-9) * 100, qdt=math.ceil(V * 10 / 500 - 1e-9) * 500)
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
