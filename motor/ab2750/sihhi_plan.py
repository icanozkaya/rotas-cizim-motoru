# -*- coding: utf-8 -*-
"""2750/7 SIHHİ — kat planları (mimari koordinatında): pis su, temiz su (soğuk/sıcak), koridor asma tavan dağıtımı
(soğuk/sıcak/sirkülasyon), sayaç dolapları, temiz su kolon kutusu, kolon no balonları, ek armatürler, yer süzgeci,
balkon süzgeci -> yağmur inişi, aspiratör; etiketler çakışmasız yerleşir (Engel)."""
import math
import os
import sys

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import sihhi_cizim as C          # noqa: E402
import sihhi_tasarim as T        # noqa: E402

H_ET = 10.0          # etiket yazı yüksekliği (kullanıcı)


def sirk_cap(n_daire):
    return 'Ø20' if n_daire <= 4 else 'Ø25' if n_daire <= 12 else 'Ø32' if n_daire <= 30 else 'Ø40'


def _ac(p, q):
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))


def _okunur(a):
    a = (a + 360) % 360
    if 90 < a <= 270:
        a -= 180
    return a


class Plan:
    def __init__(self, msp, F, M, kat):
        self.m = msp
        self.F = F
        self.M = M
        self.kat = kat
        self.E = C.Engel()
        self.hatlar = []             # (LineString, sistem)
        self.say = dict(etiket_pis=0, etiketsiz_pis=0, etiket_temiz=0, etiketsiz_temiz=0)
        self.uyari = []

    # ------------------------------------------------------------------ çizgi
    def pl(self, pts, kat, sistem=None, engel=True):
        pts = [(float(x), float(y)) for x, y in pts]
        if len(pts) < 2:
            return None
        e = self.m.add_lwpolyline(pts, dxfattribs={'layer': kat})
        g = LineString(pts)
        if engel:
            self.E.ekle(g.buffer(1.5), 'hat')
        if sistem:
            self.hatlar.append((g, sistem))
        return e

    # ------------------------------------------------------------------ etiket yerleştirme
    def _dene(self, aday_kutular, haric=()):
        for k in aday_kutular:
            if self.E.carpar(k[0], haric) is None:
                return k
        return None

    def etiket_pis(self, yol, sb, cap, min_boy=22):
        """hat parçasının üstünde: kanca (dik 12 + paralel 8), üstte 'Ø50', altta '2 SB', hat doğrultusunda"""
        L = LineString(yol)
        if L.length < min_boy:
            return False
        s1, s2 = 'Ø%d' % cap, '%g SB' % sb
        adaylar = []
        for t in (0.5, 0.35, 0.65, 0.2, 0.8, 0.1, 0.9):
            P = L.interpolate(t, normalized=True)
            # parça doğrultusu
            d = 0.0
            seg = None
            acc = 0.0
            for a, b in zip(yol[:-1], yol[1:]):
                l = math.dist(a, b)
                if acc + l >= L.length * t - 1e-6:
                    seg = (a, b)
                    break
                acc += l
            if seg is None:
                seg = (yol[-2], yol[-1])
            ang = _okunur(_ac(*seg))
            r = math.radians(ang)
            u = (math.cos(r), math.sin(r))
            n = (-u[1], u[0])
            for sg in (1, -1):
                Q = (P.x + n[0] * sg * 17, P.y + n[1] * sg * 17)
                Q2 = (Q[0] + u[0] * 8, Q[1] + u[1] * 8)
                w = max(C.yazi_gen(s1, H_ET), C.yazi_gen(s2, H_ET)) + 2
                # yazılar Q2'den başlar; s1 kancanın üstünde, s2 altında (hat doğrultusunda)
                p1 = (Q2[0] + n[0] * 2.5, Q2[1] + n[1] * 2.5)
                p2 = (Q2[0] - n[0] * (H_ET + 2.5), Q2[1] - n[1] * (H_ET + 2.5))
                k1 = C.yazi_kutusu(s1, p1, H_ET, 'BL', ang, pay=1.0)
                k2 = C.yazi_kutusu(s2, p2, H_ET, 'BL', ang, pay=1.0)
                kk = unary_union([k1, k2])
                kanca = LineString([(P.x, P.y), Q, Q2])
                adaylar.append((kk, (P, Q, Q2, p1, p2, ang, kanca)))
        for kk, v in adaylar:
            P, Q, Q2, p1, p2, ang, kanca = v
            if self.E.carpar(kk) is not None:
                continue
            # kanca başka hattı kesmesin
            if self.E.carpar(LineString([Q, Q2]).buffer(0.5), haric=()) is not None:
                continue
            self.m.add_lwpolyline([(P.x, P.y), Q, Q2], dxfattribs={'layer': 'ROTAS-PISSU-CAP'})
            C.yazi(self.m, s1, p1, H_ET, 'ROTAS-PISSU-CAP', 'BL', ang)
            C.yazi(self.m, s2, p2, H_ET, 'ROTAS-PISSU-CAP', 'BL', ang)
            self.E.ekle(kk, 'yazi')
            self.say['etiket_pis'] += 1
            return True
        # kılavuzlu (yatay yazı, ≤ 110 cm)
        P = L.interpolate(0.5, normalized=True)
        w = max(C.yazi_gen(s1, H_ET), C.yazi_gen(s2, H_ET)) + 2
        for r in range(30, 115, 12):
            for a in range(0, 360, 30):
                c = (P.x + r * math.cos(math.radians(a)), P.y + r * math.sin(math.radians(a)))
                x0 = c[0] if math.cos(math.radians(a)) >= -0.1 else c[0] - w
                kk = box(x0 - 1, c[1] - 13, x0 + w + 1, c[1] + 13)
                kil = LineString([(P.x, P.y), c])
                if self.E.carpar(kk) is not None:
                    continue
                if self.E.carpar(kil.buffer(0.3), haric=('hat', 'mimyazi', 'armatur')) is not None:
                    continue
                if sum(1 for g, t in self.hatlar if t == 'pis' and g.crosses(kil)) > 0:
                    continue
                self.m.add_line((P.x, P.y), c, dxfattribs={'layer': 'ROTAS-PISSU-CAP'})
                self.m.add_line((x0, c[1]), (x0 + w, c[1]), dxfattribs={'layer': 'ROTAS-PISSU-CAP'})
                C.yazi(self.m, s1, (x0 + 1, c[1] + 2.5), H_ET, 'ROTAS-PISSU-CAP', 'BL')
                C.yazi(self.m, s2, (x0 + 1, c[1] - 2.5 - H_ET), H_ET, 'ROTAS-PISSU-CAP', 'BL')
                self.E.ekle(kk, 'yazi')
                self.E.ekle(kil.buffer(0.5), 'kanca')
                self.say['etiket_pis'] += 1
                self.say['kilavuzlu_pis'] = self.say.get('kilavuzlu_pis', 0) + 1
                return True
        self.say['etiketsiz_pis'] += 1
        return False

    def etiket_temiz(self, yol, satirlar, renk_kat='ROTAS-TEMIZSU-CAP', min_boy=40, kanca=24):
        """yatay yazılı etiket (1-3 satır), hattın üstündeki noktadan dik kanca ile"""
        L = LineString(yol)
        if L.length < min_boy:
            return False
        w = max(C.yazi_gen(s, H_ET) for s in satirlar) + 2
        hgt = len(satirlar) * 14
        for t in (0.5, 0.3, 0.7, 0.15, 0.85):
            P = L.interpolate(t, normalized=True)
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                for kb in (kanca, kanca + 18, kanca + 40):
                    Q = (P.x + dx * kb, P.y + dy * kb)
                    if dy == 1:
                        x0, y0 = Q[0] + 2, Q[1]
                    elif dy == -1:
                        x0, y0 = Q[0] + 2, Q[1] - hgt
                    elif dx == 1:
                        x0, y0 = Q[0] + 2, Q[1] - hgt / 2
                    else:
                        x0, y0 = Q[0] - w - 2, Q[1] - hgt / 2
                    kk = box(x0 - 1, y0 - 1, x0 + w + 1, y0 + hgt + 1)
                    ln = LineString([(P.x, P.y), Q])
                    if self.E.carpar(kk) is not None:
                        continue
                    if self.E.carpar(ln.parallel_offset(0.1) if False else LineString([Q, (P.x + dx * 4, P.y + dy * 4)]).buffer(0.4)) is not None:
                        continue
                    self.m.add_lwpolyline([(P.x, P.y), Q, (Q[0] + (8 if dx >= 0 else -8), Q[1])] if dy else [(P.x, P.y), Q],
                                          dxfattribs={'layer': renk_kat})
                    for i, s in enumerate(satirlar):
                        C.yazi(self.m, s, (x0, y0 + hgt - 14 * (i + 1) + 3), H_ET, renk_kat, 'BL')
                    self.E.ekle(kk, 'yazi')
                    self.E.ekle(ln.buffer(0.6), 'kanca')
                    self.say['etiket_temiz'] += 1
                    return True
        self.say['etiketsiz_temiz'] += 1
        return False

    def balon(self, p, ad, blok='ROTAS-PL-BALON', renk_yazi=6, kat='ROTAS-PISSU-KOLONNO', yasak=None, r_min=45, r_max=230):
        """kolon/iniş numara balonu: çevrede boş yer + kılavuz"""
        for r in range(r_min, r_max + 1, 15):
            for a in range(0, 360, 20):
                c = (p[0] + r * math.cos(math.radians(a)), p[1] + r * math.sin(math.radians(a)))
                g = Point(c).buffer(29)
                if self.E.carpar(g) is not None:
                    continue
                if yasak is not None and yasak.intersects(g):
                    continue
                ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                kil = LineString([(p[0] + 12 * ca, p[1] + 12 * sa), (c[0] - 27.5 * ca, c[1] - 27.5 * sa)])
                if self.E.carpar(kil.buffer(0.3), haric=('hat', 'mimyazi', 'armatur', 'beton', 'kanca')) is not None:
                    continue
                C.blok(self.m, blok, c, kat)
                C.yazi(self.m, ad, c, 20 if len(ad) <= 3 else 16, kat, 'MC', renk=renk_yazi)
                self.m.add_line(kil.coords[0], kil.coords[-1], dxfattribs={'layer': 'ROTAS-SEMBOL-KILAVUZ'})
                self.E.ekle(g, 'balon')
                self.E.ekle(kil.buffer(0.5), 'kanca')
                return c
        self.uyari.append('balon yeri yok ' + ad)
        return None

    def not_yaz(self, satirlar, p, h=12, kat='ROTAS-HAVALANDIRMA-YAZI', yakin=None, r_max=160, yasak=None):
        w = max(C.yazi_gen(s, h) for s in satirlar) + 2
        hgt = len(satirlar) * (h + 4)
        for r in range(0, r_max + 1, 12):
            for a in range(0, 360, 30):
                c = (p[0] + r * math.cos(math.radians(a)), p[1] + r * math.sin(math.radians(a)))
                kk = box(c[0] - w / 2, c[1] - hgt / 2, c[0] + w / 2, c[1] + hgt / 2)
                if self.E.carpar(kk) is not None or (yasak is not None and not yasak.contains(kk)):
                    continue
                for i, s in enumerate(satirlar):
                    C.yazi(self.m, s, (c[0] - w / 2 + 1, c[1] + hgt / 2 - (h + 4) * (i + 1) + 3), h, kat, 'BL')
                self.E.ekle(kk, 'yazi')
                return c
                if r == 0:
                    break
        return None


# ====================================================================== kat planı
def kat_plani(msp, M, kat, cati=False):
    blok = M['blok']
    if kat == 'B':
        F = M['bodrum']['F']
    else:
        F = M['Fs'][kat]
    P = Plan(msp, F, M, kat)
    w = (F.x0, F.x1, F.y0, F.y1)
    C.mimari_altlik(msp, w, engel=P.E)
    # betonarme taraması (ayrı katman: kullanıcı hizalama için)
    for g in getattr(F.beton, 'geoms', [F.beton]):
        if g.area < 200:
            continue
        h = msp.add_hatch(color=8, dxfattribs={'layer': 'ROTAS-MIMARI-KOLON'})
        h.set_pattern_fill('ANSI31', scale=3.0)
        h.paths.add_polyline_path(list(g.exterior.coords), is_closed=True)
        P.E.ekle(g, 'beton')
    # mimari armatür kutuları engel (etiket armatür üstüne binmez)
    for a in F.K.armatur:
        P.E.ekle(a['kutu'], 'armatur')
    if kat == 'B':
        _bodrum(P, M)
    else:
        _daireler(P, M)
        _koridor(P, M)
        _yagmur(P, M)
        _gecis_kolonlari(P, M)
        if kat == 'Z':
            _sebeke(P, M)
        _etiketler(P, M)
    return P


def _daireler(P, M):
    F, m = P.F, P.m
    for no, D in F.daire.items():
        for W in D['islak']:
            # ek armatürler
            for a in W['armatur']:
                if not a.get('ek'):
                    continue
                if a['tip'] in ('CM', 'BM'):
                    m.add_lwpolyline(list(a['kutu'].exterior.coords), dxfattribs={'layer': 'ROTAS-ARMATUR-EK'})
                    k = a['kutu'].buffer(-8)
                    m.add_circle(a['p'], 18, dxfattribs={'layer': 'ROTAS-ARMATUR-EK'})
                    C.yazi(m, "Ç'M'" if a['tip'] == 'CM' else "B'M'", (a['p'][0], a['p'][1]), 9, 'ROTAS-ARMATUR-EK', 'MC')
                    P.E.ekle(a['kutu'], 'armatur')
                elif a['tip'] == 'YS':
                    C.blok(m, 'ROTAS-PL-YER-SUZGECI', a['p'], 'ROTAS-YER-SUZGECI')
                    P.E.ekle(Point(a['p']).buffer(9), 'sembol')
            # pis su
            if W.get('kolon'):
                for h in W.get('pis', []):
                    P.pl(h['yol'], 'ROTAS-PISSU', 'pis')
                C.blok(m, 'ROTAS-PL-PIS-KOLON', W['kolon'], 'ROTAS-PISSU-KOLON')
                P.E.ekle(Point(W['kolon']).buffer(11), 'sembol')
            # havalandırma (aspiratör)
            hv = W.get('hav')
            if hv and W['tip'] == 'banyo':
                _aspirator(P, W)
        # temiz su
        t = D.get('temiz', {})
        for h in t.get('soguk', []):
            P.pl(h['yol'], 'ROTAS-SOGUKSU', 'soguk')
        for h in t.get('sicak', []):
            P.pl(h['yol'], 'ROTAS-SICAKSU', 'sicak')
        # sayaç dolabı
        d = F.dol.get(no)
        if d:
            m.add_lwpolyline(list(d['kutu'].exterior.coords), dxfattribs={'layer': 'ROTAS-SAYAC-DOLABI'})
            v, n = d['v'], d['n']
            for s in (-14, 14):
                c = (d['c'][0] + v[0] * s, d['c'][1] + v[1] * s)
                C.blok(m, 'ROTAS-PL-SAYAC', c, 'ROTAS-SAYAC-DOLABI', rot=math.degrees(math.atan2(v[1], v[0])), olcek=0.75)
            P.E.ekle(d['kutu'], 'sembol')


def _aspirator(P, W):
    """penceresiz banyo: tavanda aspiratör, Ø150 kanal şafta"""
    F, m = P.F, P.m
    poly = W['poly']
    hv = W['hav']
    # sembol: şafta en yakın köşe bölgesinde, boş yer
    hedef = hv.get('duvar') or hv.get('saft') or poly.centroid.coords[0]
    best = None
    ic = poly.buffer(-20)
    if ic.is_empty:
        ic = poly.buffer(-12)
    bx = ic.bounds
    for x in np.arange(bx[0], bx[2] + 1, 6):
        for y in np.arange(bx[1], bx[3] + 1, 6):
            q = Point(x, y)
            if not ic.contains(q):
                continue
            g = q.buffer(17)
            if P.E.carpar(g) is not None:
                continue
            d = q.distance(Point(hedef))
            if best is None or d < best[0]:
                best = (d, (x, y))
    if best is None:
        P.uyari.append('aspiratör yeri yok')
        return
    c = best[1]
    C.blok(m, 'ROTAS-PL-ASPIRATOR', c, 'ROTAS-HAVALANDIRMA')
    P.E.ekle(Point(c).buffer(17), 'sembol')
    W['asp_xy'] = c
    if hv.get('tip') == 'saft' and hv.get('duvar'):
        ln = [c, hv['duvar']]
        e = m.add_lwpolyline(ln, dxfattribs={'layer': 'ROTAS-HAVALANDIRMA', 'linetype': 'DASHED'})
        e.dxf.ltscale = 0.4
    W['asp_not'] = P.not_yaz(['Wc Aspiratörü', '80 m3/h-50 pa', 'Ø150 mm' + ('  (%s)' % hv.get('no', '') if hv.get('no') else '')],
                             c, 12, 'ROTAS-HAVALANDIRMA-YAZI', yasak=poly.buffer(25), r_max=150)


def _koridor(P, M):
    F, m = P.F, P.m
    kr = getattr(F, 'koridor', None)
    if not kr:
        return
    for h in kr['hatlar']:
        P.pl(h['yol'], 'ROTAS-SOGUKSU', 'kor_soguk')
        P.pl([(x + 5, y + 5) for x, y in h['yol']], 'ROTAS-SICAKSU', 'kor_sicak')
        P.pl([(x + 10, y + 10) for x, y in h['yol']], 'ROTAS-SIRKULASYON', 'kor_sirk')
    # temiz su kolon kutusu (riser): 4 boru (dolum, soğuk, sıcak, sirkülasyon)
    rp = kr['riser']
    kb = box(rp[0] - 32, rp[1] - 14, rp[0] + 32, rp[1] + 14)
    m.add_lwpolyline(list(kb.exterior.coords), dxfattribs={'layer': 'ROTAS-TEMIZSU-KOLON'})
    for i, (lay, ad) in enumerate((('ROTAS-SEBEKE', 'DD'), ('ROTAS-SOGUKSU', 'S'), ('ROTAS-SICAKSU', 'H'),
                                   ('ROTAS-SIRKULASYON', 'R'))):
        c = (rp[0] - 22 + 14.5 * i, rp[1])
        m.add_circle(c, 5, dxfattribs={'layer': lay})
    P.E.ekle(kb, 'sembol')
    P.riser_kutu = kb


def _yagmur(P, M):
    F, m = P.F, P.m
    for y in getattr(F, 'yagmur', []):
        C.blok(m, 'ROTAS-PL-BALKON-SUZGECI', y['suzgec'], 'ROTAS-YAGMUR')
        C.blok(m, 'ROTAS-PL-YAGMUR-INIS', y['inis'], 'ROTAS-YAGMUR')
        yol = list(y.get('yol') or [y['suzgec'], y['inis']])
        # süzgeç ve iniş sembolünün içine girmez
        L = LineString(yol)
        L2 = L.difference(Point(y['suzgec']).buffer(7)).difference(Point(y['inis']).buffer(5.5))
        for q in getattr(L2, 'geoms', [L2]):
            if q.length > 0.5:
                P.pl(list(q.coords), 'ROTAS-YAGMUR', 'yagmur')
        P.E.ekle(Point(y['suzgec']).buffer(8), 'sembol')
        P.E.ekle(Point(y['inis']).buffer(6), 'sembol')


def _gecis_kolonlari(P, M):
    """bu katta ıslak hacmi olmayan ama üst kattan inen kolonlar (A blok zemin: giriş holü / yatak odası köşesi)"""
    F = P.F
    sira = ['Z', '1', '2']
    for k in M['kolonlar']:
        katlar = k['katlar']
        if P.kat in katlar:
            continue
        ust = [q for q in katlar if sira.index(q) > sira.index(P.kat)] if P.kat in sira else []
        if not ust:
            continue
        p = (k['p'][0] + F.dx, k['p'][1])
        C.blok(P.m, 'ROTAS-PL-PIS-KOLON-GECIS', p, 'ROTAS-PISSU-KOLON')
        P.E.ekle(Point(p).buffer(11), 'sembol')
        k.setdefault('gecis', {})[P.kat] = p


def _sebeke(P, M):
    """zemin: şebeke girişi + ana sayaç (bina girişi) -> depo dolum kolonu; B blok: A blok kazan dairesinden sıcak/sirk."""
    F, m = P.F, P.m
    kr = getattr(F, 'koridor', None)
    if not kr:
        return
    rp = kr['riser']
    blok = M['blok']
    # bina girişi yönü: riserden en yakın dış cephe (ayak izi dışına) — dik hat
    fp = M['altyapi']['ayak_izi']
    x0, y0, x1, y1 = fp.bounds
    if blok == 'B':
        dis = (rp[0] - 22, y0 - 120)            # güney (giriş kapısı tarafı)
    else:
        dis = (rp[0] - 22, y0 - 120)
    yol = [(rp[0] - 22, rp[1] - 5), (rp[0] - 22, dis[1])]
    e = m.add_lwpolyline(yol, dxfattribs={'layer': 'ROTAS-SEBEKE'})
    P.E.ekle(LineString(yol).buffer(2), 'hat')
    # ana sayaç grubu: girişten 120 cm içeride (vana-pislik tutucu-sayaç-çek valf-vana)
    x = rp[0] - 22
    yb = y0 + 80
    for i, ad in enumerate(('ROTAS-PL-VANA', 'ROTAS-PL-PISLIK-TUTUCU', 'ROTAS-PL-SAYAC', 'ROTAS-PL-CEKVALF', 'ROTAS-PL-VANA')):
        c = (x, yb + 22 * i)
        if F.beton.distance(Point(c)) < 10:
            continue
        C.blok(m, ad, c, 'ROTAS-VANA', rot=90)
        P.E.ekle(Point(c).buffer(10), 'sembol')
    P.not_yaz(['ŞEBEKEDEN (SASKİ) DN50', 'ANA SU SAYACI GRUBU', '(BİNA GİRİŞİ, DEPO DOLUM)'], (x + 90, yb + 40), 10,
              'ROTAS-TEMIZSU-CAP', r_max=220)
    P.sebeke_yol = yol


# ====================================================================== bodrum (A blok)
def _bodrum(P, M):
    m = P.m
    B = M['bodrum']
    F = B['F']
    for a in B['armatur']:
        P.E.ekle(a['kutu'], 'armatur')
    for h in B['pis']:
        P.pl(h['yol'], 'ROTAS-PISSU', 'pis')
    for h in B['soguk']:
        P.pl(h['yol'], 'ROTAS-SOGUKSU', 'soguk')
    for h in B['sicak']:
        P.pl(h['yol'], 'ROTAS-SICAKSU', 'sicak')
    # pis su çukuru + 2 dalgıç pompa
    c = B['cukur']
    k = box(c[0] - 50, c[1] - 50, c[0] + 50, c[1] + 50)
    m.add_lwpolyline(list(k.exterior.coords), dxfattribs={'layer': 'ROTAS-POMPA'})
    m.add_lwpolyline(list(k.buffer(-10, join_style=2).exterior.coords), dxfattribs={'layer': 'ROTAS-POMPA'})
    for dx in (-22, 22):
        C.blok(m, 'ROTAS-PL-POMPA', (c[0] + dx, c[1]), 'ROTAS-POMPA', olcek=0.8)
    P.E.ekle(k.buffer(2), 'sembol')
    # basma hattı: çukurdan tavana -> doğu cephesi -> RP rögarı (temel planında)
    P.not_yaz(['PİS SU ÇUKURU 100x100 h:120', '2 AD. DALGIÇ POMPA (1 ASIL + 1 YEDEK)',
               'BASMA HATTI Ø63 TAVANDAN RP RÖGARINA'], (c[0], c[1] + 110), 10, 'ROTAS-NOT', r_max=250)
    # temiz su: ortak alan sayacı (riser dibi)
    rp = B['riser']
    kb = box(rp[0] - 32, rp[1] - 14, rp[0] + 32, rp[1] + 14)
    m.add_lwpolyline(list(kb.exterior.coords), dxfattribs={'layer': 'ROTAS-TEMIZSU-KOLON'})
    P.E.ekle(kb, 'sembol')
    for i, lay in enumerate(('ROTAS-SEBEKE', 'ROTAS-SOGUKSU', 'ROTAS-SICAKSU', 'ROTAS-SIRKULASYON')):
        m.add_circle((rp[0] - 22 + 14.5 * i, rp[1]), 5, dxfattribs={'layer': lay})
    _kazan_dairesi(P, M)
    _etiket_bodrum(P, M)


def _kazan_dairesi(P, M):
    """kazan dairesi (bodrum): 2 boyler + riser bağlantıları (soğuk besleme, sıcak çıkış, sirkülasyon dönüş) + B blok hattı"""
    m = P.m
    F = M['bodrum']['F']
    kd = None
    for x, y, s, h, L in F.K.yazilar:
        if s.upper().startswith('KAZAN DA'):
            kd = (x, y)
    if kd is None:
        return
    # kazan dairesi hücresi (raster bileşeni)
    import sihhi_tasarim as T
    from scipy import ndimage as ndi
    r = int((F.y1 - kd[1]) / 2)
    c = int((kd[0] - F.x0) / 2)
    lab, n = ndi.label(F.img == 0)
    i = lab[r, c]
    gs = T.maske_poligon(lab == i, F.x0, F.y1)
    if not gs:
        return
    oda = max(gs, key=lambda q: q.area)
    P.kazan_oda = oda
    bx = oda.bounds
    # boylerler odanın kuzey-doğu bölümünde, duvardan 25 cm
    b1 = (bx[2] - 90, bx[3] - 90)
    b2 = (bx[2] - 230, bx[3] - 90)
    for b in (b1, b2):
        C.blok(m, 'ROTAS-PL-BOYLER', b, 'ROTAS-KAZAN')
        P.E.ekle(Point(b).buffer(58), 'sembol')
    C.yazi(m, 'BOYLER-1', (b1[0], b1[1] - 70), 10, 'ROTAS-KAZAN', 'TC')
    C.yazi(m, 'BOYLER-2', (b2[0], b2[1] - 70), 10, 'ROTAS-KAZAN', 'TC')
    P.boylerler = (b1, b2)
    # riser dibi -> boyler bağlantıları (kazan dairesi kapısından değil, duvar geçişiyle; tavan altı)
    rp = M['bodrum']['riser']
    G = F.G
    cost = np.where(F.duvar4, 60.0, 1.0 + 6.0 * np.exp(-F.dduvar / 20.0))
    cost[F.beton4 | F.yasak4 | F.saft4] = np.inf
    for p in getattr(P, '_kazan_yasak', []):
        pass
    yol = G.yol([G.hucre((rp[0] - 7.5, rp[1] - 20))], [G.hucre((b2[0] - 70, b2[1]))], donus=60.0, maliyet=cost)
    if yol:
        pts = [(float(x), float(y)) for x, y in G.koseler(yol)]
        P.pl(pts, 'ROTAS-SOGUKSU', 'kazan')
        P.pl([(x + 5, y + 5) for x, y in pts], 'ROTAS-SICAKSU', 'kazan')
        P.pl([(x + 10, y + 10) for x, y in pts], 'ROTAS-SIRKULASYON', 'kazan')
        P.kazan_hat = pts
        P.pl([(b2[0] - 70, b2[1]), (b2[0] - 56, b2[1])], 'ROTAS-SOGUKSU', 'kazan')
        P.pl([(b1[0] - 70 + 5, b1[1] + 5), (b2[0] + 56, b1[1] + 5)] if False else [(b2[0] - 65, b2[1] + 5), (b2[0] - 65, b2[1] + 60), (b1[0], b1[1] + 60), (b1[0], b1[1] + 55)], 'ROTAS-SICAKSU', 'kazan')
    # B bloğa giden sıcak su + sirkülasyon hattı: kazan dairesinin batı duvarından dışarı (toprak altı)
    yB = bx[1] + 60
    pts = [(bx[0] + 20, yB), (bx[0] - 150, yB)]
    P.pl(pts, 'ROTAS-SICAKSU', 'bblok')
    P.pl([(x, y + 12) for x, y in pts], 'ROTAS-SIRKULASYON', 'bblok')
    P.not_yaz(['B BLOĞA: SICAK SU Ø50 + SİRKÜLASYON Ø32', '(İZOLELİ, TOPRAK ALTI KORUGE KILIF İÇİNDE)'],
              (bx[0] - 150, yB + 60), 10, 'ROTAS-NOT', r_max=200)
    P.not_yaz(['KAZAN DAİRESİ: 2 AD. 1500 lt ÇİFT SERPANTİNLİ BOYLER', 'SOĞUK SU BESLEMESİ A BLOK DEPO DAĞITIM KOLONUNDAN'],
              ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2), 10, 'ROTAS-NOT', yasak=oda, r_max=200)


def _etiket_bodrum(P, M):
    B = M['bodrum']
    for h in B['pis']:
        P.etiket_pis(h['yol'], h['sb'], h['cap'])
    for h in B['soguk']:
        P.etiket_temiz(h['yol'], ['%s / %g YB' % (T.temiz_cap(h['yb']), h['yb'])])


# ====================================================================== etiketler
def _etiketler(P, M):
    F = P.F
    # 1) kolon balonları (ıslak hacim dışında)
    for no, D in F.daire.items():
        for W in D['islak']:
            if W.get('kolon') and W.get('kolon_no'):
                P.balon(W['kolon'], W['kolon_no'], yasak=W['poly'].buffer(-5))
    for k in M['kolonlar']:
        p = k.get('gecis', {}).get(P.kat)
        if p:
            P.balon(p, k['no'])
    for y in getattr(F, 'yagmur', []):
        if y.get('no'):
            P.balon(y['inis'], y['no'], blok='ROTAS-PL-BALON-YAGMUR', renk_yazi=3, kat='ROTAS-YAGMUR-NO', r_min=40)
    # 2) pis su etiketleri (kısa parçalar önce)
    isler = []
    for no, D in F.daire.items():
        for W in D['islak']:
            for h in W.get('pis', []):
                isler.append(h)
    isler.sort(key=lambda h: LineString(h['yol']).length)
    for h in isler:
        P.etiket_pis(h['yol'], h['sb'], h['cap'])
    # 3) temiz su (daire içi): her zincir ≥ 40 cm — soğuk + (varsa) sıcak tek etiket
    for no, D in F.daire.items():
        t = D.get('temiz', {})
        sic = {tuple(map(tuple, h['hucreler'])): h for h in t.get('sicak', [])} if t else {}
        for h in sorted(t.get('soguk', []), key=lambda h: -LineString(h['yol']).length):
            s = ['%s / %g YB' % (T.temiz_cap(h['yb']), h['yb'])]
            hh = sic.get(tuple(map(tuple, h['hucreler'])))
            if hh:
                s.append('%s / %g YB' % (T.temiz_cap(hh['yb']), hh['yb']))
            P.etiket_temiz(h['yol'], s)
        # daire girişi (sayaç dolabı) etiketi
        d = F.dol.get(no)
        if d:
            P.not_yaz(['SAYAÇ DOLABI D%d' % no, 'S: %s / %g YB' % (T.temiz_cap(t.get('yb_s', 0)), t.get('yb_s', 0)),
                       'H: %s / %g YB' % (T.temiz_cap(t.get('yb_h', 0)), t.get('yb_h', 0))],
                      (d['c'][0] + d['n'][0] * 60, d['c'][1] + d['n'][1] * 60), 9, 'ROTAS-SAYAC-DOLABI', r_max=200,
                      yasak=F.ortak.buffer(10))
    # 4) koridor hatları
    kr = getattr(F, 'koridor', None)
    if kr:
        for h in sorted(kr['hatlar'], key=lambda h: -LineString(h['yol']).length):
            nd = h['daire']
            P.etiket_temiz(h['yol'], ['S: %s / %g YB' % (T.temiz_cap(h['yb_s']), h['yb_s']),
                                      'H: %s / %g YB' % (T.temiz_cap(h['yb_h']), h['yb_h']),
                                      'R: %s' % sirk_cap(nd)], min_boy=120, kanca=30)
        rp = kr['riser']
        P.not_yaz(['TEMİZ SU KOLON KUTUSU (TSK)', 'DD: DEPO DOLUM  S: SOĞUK (DEPODAN)', 'H: SICAK  R: SİRKÜLASYON',
                   '(ASMA TAVANDAN KAT DAĞITIMI)'], (rp[0], rp[1] - 90), 9, 'ROTAS-TEMIZSU-CAP', r_max=260)
