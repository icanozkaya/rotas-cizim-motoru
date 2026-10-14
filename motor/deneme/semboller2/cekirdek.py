# -*- coding: utf-8 -*-
"""semboller2 çekirdeği: blok içi çizim yardımcıları (dönüşümlü), vektör harf, sembol kaydı.

Tüm blok içi geometri katman '0', renk/çizgi tipi/kalınlık BYLAYER olarak çizilir; böylece INSERT
hangi ROTAS- katmanına konursa onun rengini alır. Blok içinde TEXT/MTEXT YOKTUR: sembol içi harfler
(S, Q ...) çizgi (LWPOLYLINE) olarak çizilir. ATTDEF yalnız NO ve CAP.
"""
import math

BYL = {'layer': '0', 'color': 256, 'linetype': 'BYLAYER', 'lineweight': -1}

# ----------------------------------------------------------------------------- vektör harfler
# 4 x 6 ızgara, (0,0) sol alt. Her harf: çizgi (polyline) listesi.
_G = {
    'A': [[(0, 0), (2, 6), (4, 0)], [(0.7, 2), (3.3, 2)]],
    'B': [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(3, 3), (4, 2), (4, 1), (3, 0), (0, 0)]],
    'C': [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1)]],
    'D': [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    'E': [[(4, 6), (0, 6), (0, 0), (4, 0)], [(0, 3), (3, 3)]],
    'F': [[(4, 6), (0, 6), (0, 0)], [(0, 3), (3, 3)]],
    'G': [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (3, 0), (4, 1), (4, 3), (2.2, 3)]],
    'H': [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    'K': [[(0, 0), (0, 6)], [(4, 6), (0, 2.5)], [(1.3, 3.6), (4, 0)]],
    'L': [[(0, 6), (0, 0), (4, 0)]],
    'M': [[(0, 0), (0, 6), (2, 3), (4, 6), (4, 0)]],
    'N': [[(0, 0), (0, 6), (4, 0), (4, 6)]],
    'O': [[(1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0)]],
    'P': [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]],
    'Q': [[(1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0)], [(2.5, 1.5), (4.3, -0.5)]],
    'R': [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(2, 3), (4, 0)]],
    'S': [[(4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3), (3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)]],
    'T': [[(0, 6), (4, 6)], [(2, 6), (2, 0)]],
    'V': [[(0, 6), (2, 0), (4, 6)]],
    'W': [[(0, 6), (1, 0), (2, 4), (3, 0), (4, 6)]],
    'Y': [[(0, 6), (2, 3), (4, 6)], [(2, 3), (2, 0)]],
    'Z': [[(0, 6), (4, 6), (0, 0), (4, 0)]],
}


class Ciz:
    """Blok içine dönüşümlü çizim. Alt çizer (alt()) üst dönüşümü devralır; kapsam (bbox) ortaktır."""

    def __init__(self, blk, dx=0.0, dy=0.0, aci=0.0, s=1.0, ayna=False, ust=None):
        self.b = blk
        self.dx, self.dy, self.aci, self.s, self.ayna = dx, dy, aci, s, ayna
        self.ust = ust
        self.kap = ust.kap if ust else [1e18, 1e18, -1e18, -1e18]

    # --- dönüşüm
    def T(self, p):
        x, y = p
        if self.ayna:
            x = -x
        x *= self.s
        y *= self.s
        c, sn = math.cos(math.radians(self.aci)), math.sin(math.radians(self.aci))
        x, y = x * c - y * sn + self.dx, x * sn + y * c + self.dy
        if self.ust:
            return self.ust.T((x, y))
        k = self.kap
        k[0], k[1], k[2], k[3] = min(k[0], x), min(k[1], y), max(k[2], x), max(k[3], y)
        return (x, y)

    def _aci_t(self, a):
        if self.ayna:
            a = 180.0 - a
        a += self.aci
        return self.ust._aci_t(a) if self.ust else a

    def _olcek(self):
        return self.s * (self.ust._olcek() if self.ust else 1.0)

    def _ayna_t(self):
        return self.ayna ^ (self.ust._ayna_t() if self.ust else False)

    def alt(self, dx=0.0, dy=0.0, aci=0.0, s=1.0, ayna=False):
        return Ciz(self.b, dx, dy, aci, s, ayna, ust=self)

    # --- ilkel çizimler
    def ln(self, p, q):
        self.b.add_line(self.T(p), self.T(q), dxfattribs=dict(BYL))

    def pl(self, pts, kapali=False):
        self.b.add_lwpolyline([self.T(p) for p in pts], close=kapali, dxfattribs=dict(BYL))

    def ci(self, c, r):
        cc = self.T(c)
        rr = r * self._olcek()
        self.b.add_circle(cc, rr, dxfattribs=dict(BYL))
        self._kapsam_daire(cc, rr)

    def _kapsam_daire(self, cc, rr):
        # yalnız en üst düzeyde kapsamı güncelle
        u = self
        while u.ust:
            u = u.ust
        k = u.kap
        k[0], k[1], k[2], k[3] = min(k[0], cc[0] - rr), min(k[1], cc[1] - rr), max(k[2], cc[0] + rr), max(k[3], cc[1] + rr)

    def arc(self, c, r, a0, a1):
        """a0 -> a1 saat tersi (derece)"""
        cc = self.T(c)
        rr = r * self._olcek()
        b0, b1 = self._aci_t(a0), self._aci_t(a1)
        if self._ayna_t():
            b0, b1 = b1, b0
        self.b.add_arc(cc, rr, b0, b1, dxfattribs=dict(BYL))
        # kapsam: yay üzerindeki noktalar
        n = 12
        sp = (a1 - a0) % 360 or 360
        for i in range(n + 1):
            a = math.radians(a0 + sp * i / n)
            self.T((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))

    def dolu(self, pts):
        h = self.b.add_hatch(color=256, dxfattribs={'layer': '0'})
        h.paths.add_polyline_path([self.T(p) for p in pts], is_closed=True)
        h.set_solid_fill(color=256)

    def dolu_daire(self, c, r, n=24):
        self.dolu([(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)])

    def rect(self, x0, y0, x1, y1):
        self.pl([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True)

    def kapsul(self, cx, y0, w, h):
        """dikey kapsül: alt uç y0, genişlik w, toplam yükseklik h (uçlar yarım daire)"""
        r = w / 2.0
        self.ln((cx - r, y0 + r), (cx - r, y0 + h - r))
        self.ln((cx + r, y0 + r), (cx + r, y0 + h - r))
        self.arc((cx, y0 + h - r), r, 0, 180)
        self.arc((cx, y0 + r), r, 180, 360)

    def kesikli(self, p, q, d=2.0, b=1.2):
        """kesikli çizgi (blokta çizgi tipi BYLAYER kalsın diye parça parça)"""
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L <= 0:
            return
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        t = 0.0
        while t < L:
            t1 = min(L, t + d)
            self.ln((p[0] + ux * t, p[1] + uy * t), (p[0] + ux * t1, p[1] + uy * t1))
            t = t1 + b

    def ok(self, p, aci, boy, dolu=True, gen=0.5):
        """ok başı: ucu p, yönü aci (derece), boy"""
        a = math.radians(aci)
        bx, by = p[0] - boy * math.cos(a), p[1] - boy * math.sin(a)
        nx, ny = -math.sin(a) * boy * gen / 2, math.cos(a) * boy * gen / 2
        pts = [p, (bx + nx, by + ny), (bx - nx, by - ny)]
        if dolu:
            self.dolu(pts)
            self.pl(pts, True)
        else:
            self.pl([pts[1], p, pts[2]])

    def okcizgi(self, p, q, boy, dolu=True):
        self.ln(p, q)
        self.ok(q, math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])), boy, dolu)

    def harf(self, s, c, h):
        """vektör harf dizisi, c = orta-orta"""
        k = h / 6.0
        w = len(s) * 4 * k + (len(s) - 1) * 1.6 * k
        x0 = c[0] - w / 2
        y0 = c[1] - h / 2
        for i, ch in enumerate(s):
            for st in _G[ch]:
                self.pl([(x0 + (i * 5.6 + px) * k, y0 + py * k) for px, py in st])

    def papyon(self, c=(0, 0), l=20.0, h=None, dolu=False, dikey=False):
        h = 0.6 * l if h is None else h
        x, y = c
        if dikey:
            a = [(x - h / 2, y - l / 2), (x + h / 2, y - l / 2), (x, y)]
            b = [(x - h / 2, y + l / 2), (x + h / 2, y + l / 2), (x, y)]
        else:
            a = [(x - l / 2, y + h / 2), (x - l / 2, y - h / 2), (x, y)]
            b = [(x + l / 2, y + h / 2), (x + l / 2, y - h / 2), (x, y)]
        for t in (a, b):
            if dolu:
                self.dolu(t)
            self.pl(t, True)

    def zigzag(self, p, q, n, gen):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        nx, ny = -uy, ux
        pts = [p]
        for i in range(n * 2):
            t = (i + 0.5) / (n * 2) * L
            sg = gen if i % 2 == 0 else -gen
            pts.append((p[0] + ux * t + nx * sg, p[1] + uy * t + ny * sg))
        pts.append(q)
        self.pl(pts)


# ----------------------------------------------------------------------------- kayıt
GRUP = {
    # kod: (başlık, varsayılan katman, renk)
    'SB': ('SIHHİ TESİSAT SEMBOLLERİ', 'ROTAS-SIHHI-SEMBOL', 5),
    'DH': ('SU DEPOSU / HİDROFOR SEMBOLLERİ', 'ROTAS-SIHHI-DEPO-HIDROFOR', 150),
    'IS': ('ISITMA TESİSATI SEMBOLLERİ', 'ROTAS-ISITMA-SEMBOL', 1),
    'YG': ('YANGIN TESİSATI SEMBOLLERİ', 'ROTAS-YANGIN-SEMBOL', 10),
    'HV': ('HAVALANDIRMA TESİSATI SEMBOLLERİ', 'ROTAS-HAVALANDIRMA-SEMBOL', 30),
    'KS': ('KOLON ŞEMASI ŞABLONLARI (YAN GÖRÜNÜŞ)', 'ROTAS-SIHHI-ARMATUR', 2),
}

SEMBOL = {}   # blok adı -> kayıt


def sembol(ad, aciklama, kesme=None, baglanti=None, onek='V', no_ic=False, celiski=None, tur='plan', uc=False):
    """Sembol kaydı (dekoratör).
    ad: tam blok adı 'ROTAS-SB-...'
    kesme: (x0, x1) borunun sembolde kesildiği yerel X aralığı (boru yerel +X ekseninde). None = hat üstü değil.
    baglanti: {'ad': (x, y)} yerel bağlantı noktaları
    onek: önerilen numara öneki (V, P, M ...)
    no_ic: NO özniteliği sembolün içinde (rögar, kolon balonu) — etiket_yer taşımaz
    tur: 'plan' / 'sema' / 'ikisi' (lejant notu)
    uc: hat sonu sembolü (boru sembolde biter; hat() sembolden sonra boru çizmez)"""
    grup = ad.split('-')[1]
    assert grup in GRUP, ad

    def d(f):
        SEMBOL[ad] = dict(ad=ad, grup=grup, aciklama=aciklama, ciz=f, kesme=kesme, baglanti=baglanti or {},
                          onek=onek, no_ic=no_ic, celiski=celiski, tur=tur, uc=uc, kap=None)
        return f
    return d
