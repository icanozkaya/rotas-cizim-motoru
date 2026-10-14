# -*- coding: utf-8 -*-
"""Kat planı: sprinkler planı (cizim.Cizim) + yangın dolabı yerleşimi, YG kolonları, dolap besleme hattı (köprülü),
çap etiketleri, kapsama haritası (ayrı katmanlar), dolap tabloları, lejant ve notlar. Birim cm, 1/50, DXF R2018."""
import math
import os
import sys
import numpy as np
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import LineString, box as sbox

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'semboller'))
import sembol as SB                                     # noqa: E402  birleşik sembol kütüphanesi (yangın dolabı)
from cizim import Cizim, WD, tw, th, seg_kutu, fmt      # noqa: E402
from dolap import (Plan, adaylar, yerlestir, besleme_agi, hucre_poligon, kapi_yani)   # noqa: E402
from dolap_kurallar import KAYNAK                      # noqa: E402

LAY_D = {
    'ROTAS-YANGIN-DOLAP': 1, 'ROTAS-YANGIN-DOLAP-BORU': 1, 'ROTAS-YANGIN-DOLAP-CAP': 1, 'ROTAS-YANGIN-DOLAP-KOLON': 6,
    'ROTAS-YANGIN-DOLAP-YAZI': 1, 'ROTAS-YANGIN-DOLAP-KAPSAMA': 3, 'ROTAS-YANGIN-DOLAP-KAPSANMAYAN': 1,
    'ROTAS-YANGIN-DOLAP-ERISIM': 3, 'ROTAS-MIMARI-MERDIVEN': 8, 'ROTAS-YANGIN-DOLAP-TABLO': 7,
}
DOLAP_BLOK = 'yangin_dolabi_plan'
KOPRU_R = 8.0


class DolapCizim(Cizim):
    def __init__(self, P, D):
        super().__init__(P)
        self.D = D
        for n, c in LAY_D.items():
            if n not in self.doc.layers:
                self.doc.layers.add(n, color=c)
        self.doc.layers.get('ROTAS-YANGIN-DOLAP-ERISIM').dxf.linetype = 'DASHED'
        self.cap_lay = 'ROTAS-YANGIN-SPR-CAP'
        self.dolap_borular = []          # (zid, pts, dn) kontrol için
        self.dolap_Z = []

    # sprinkler etiket fonksiyonlarını dolap katmanına yönlendir
    def L(self, a, b, lay):
        if lay == 'ROTAS-YANGIN-SPR-CAP':
            lay = self.cap_lay
        return super().L(a, b, lay)

    def _etiket_yaz(self, k, p1, p2, rot, s1, s2, h1, h2):
        self.yazi(p1[0], p1[1], s1, h1, self.cap_lay, rot, engel=False)
        self.yazi(p2[0], p2[1], s2, h2, self.cap_lay, rot, engel=False)
        self.E.ekle(k, 'yazi')

    # ---------------------------------------------------------------- mimari (merdiven + çıkış dahil)
    def mimari_tam(self):
        P, D = self.P, self.D
        kapilar = []     # (p, w, rect(kanat tarafı), kanat)
        for m in P['mahaller']:
            if m.get('kapi'):
                kapilar.append((m['kapi']['p'], m['kapi'].get('w', 90.0), m['rect'], True))
        for s in D.get('merdivenler', []):
            kapilar.append((s['kapi']['p'], s['kapi'].get('w', 100.0), s['rect'], True))
        for e in D.get('cikislar', []):
            kapilar.append((e['p'], e.get('w', 100.0), e.get('rect') or P['dis_hat'], e.get('kanat', False)))
        rects = [m['rect'] for m in P['mahaller']] + [s['rect'] for s in D.get('merdivenler', [])]
        dis = P['dis_hat']
        kenarlar = []
        for r in rects + [dis]:
            x0, y0, x1, y1 = r
            kenarlar += [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1))]
        # merdiven / rampa dış duvarı (bina dış hattının dışında kalan kısım)
        disbox = sbox(*dis)
        for r in [s['rect'] for s in D.get('merdivenler', [])]:
            o = (r[0] - 25, r[1] - 25, r[2] + 25, r[3] + 25)
            for a, b in (((o[0], o[1]), (o[2], o[1])), ((o[2], o[1]), (o[2], o[3])), ((o[0], o[3]), (o[2], o[3])),
                         ((o[0], o[1]), (o[0], o[3]))):
                g = LineString([a, b]).difference(disbox)
                for q in getattr(g, 'geoms', [g]):
                    if q.length > 0.5:
                        cs = list(q.coords)
                        kenarlar.append((cs[0], cs[-1]))
        for e in D.get('cikislar', []):
            if e.get('rect'):
                x0, y0, x1, y1 = e['rect']
                for a, b in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x1, y0), (x1, y1))):
                    kenarlar.append((a, b))
        kenarlar = _birlestir(kenarlar)
        for a, b in kenarlar:
            yatay = abs(a[1] - b[1]) < 0.1
            parcalar = [(a, b) if (a[0] <= b[0] and a[1] <= b[1]) else (b, a)]
            for p, w, r, kanat in kapilar:
                if yatay and abs(p[1] - a[1]) <= 20 and min(a[0], b[0]) < p[0] < max(a[0], b[0]):
                    yeni = []
                    for c, d in parcalar:
                        if c[0] < p[0] < d[0]:
                            yeni += [(c, (p[0] - w / 2, c[1])), ((p[0] + w / 2, c[1]), d)]
                        else:
                            yeni.append((c, d))
                    parcalar = yeni
                if (not yatay) and abs(p[0] - a[0]) <= 20 and min(a[1], b[1]) < p[1] < max(a[1], b[1]):
                    yeni = []
                    for c, d in parcalar:
                        if c[1] < p[1] < d[1]:
                            yeni += [(c, (c[0], p[1] - w / 2)), ((c[0], p[1] + w / 2), d)]
                        else:
                            yeni.append((c, d))
                    parcalar = yeni
            for c, d in parcalar:
                if math.dist(c, d) > 0.5 and (d[0] - c[0]) > -0.1 and (d[1] - c[1]) > -0.1:
                    super().L(c, d, 'ROTAS-MIMARI-DUVAR')
                    self.E.ekle(seg_kutu(c, d, 1.0), 'duvar')
        for p, w, r, kanat in kapilar:
            yan = kapi_yani(p, r)
            x0, y0, x1, y1 = r
            yuz = {'alt': y0, 'ust': y1, 'sol': x0, 'sag': x1}[yan]
            ic = {'alt': 1, 'ust': -1, 'sol': 1, 'sag': -1}[yan]
            karsi = yuz - ic * 2 * abs(yuz - (p[1] if yan in ('alt', 'ust') else p[0]))
            if yan in ('alt', 'ust'):
                for u in (p[0] - w / 2, p[0] + w / 2):
                    super().L((u, yuz), (u, karsi), 'ROTAS-MIMARI-KAPI')
                if kanat:
                    mn = (p[0] - w / 2, yuz)
                    super().L(mn, (mn[0], yuz + ic * w), 'ROTAS-MIMARI-KAPI')
                    a0, a1 = (0, 90) if ic > 0 else (270, 360)
                    self.msp.add_arc(mn, w, a0, a1, dxfattribs={'layer': 'ROTAS-MIMARI-KAPI'})
            else:
                for v in (p[1] - w / 2, p[1] + w / 2):
                    super().L((yuz, v), (karsi, v), 'ROTAS-MIMARI-KAPI')
                if kanat:
                    mn = (yuz, p[1] - w / 2)
                    super().L(mn, (yuz + ic * w, mn[1]), 'ROTAS-MIMARI-KAPI')
                    a0, a1 = (0, 90) if ic > 0 else (90, 180)
                    self.msp.add_arc(mn, w, a0, a1, dxfattribs={'layer': 'ROTAS-MIMARI-KAPI'})
        for k in P.get('kolonlar', []):
            pts = [(k[0], k[1]), (k[2], k[1]), (k[2], k[3]), (k[0], k[3])]
            self.PL(pts, 'ROTAS-MIMARI-KOLON', closed=True)
            h = self.msp.add_hatch(dxfattribs={'layer': 'ROTAS-MIMARI-KOLON-TARAMA'})
            h.set_pattern_fill('ANSI31', scale=1.0)
            h.paths.add_polyline_path(pts, is_closed=True)
            self.E.ekle(tuple(k), 'kolon')
        # merdiven basamakları (iki kol + sahanlık), kapıdan uzak tarafta
        for s in D.get('merdivenler', []):
            x0, y0, x1, y1 = s['rect']
            yan = kapi_yani(s['kapi']['p'], s['rect'])
            lay = 'ROTAS-MIMARI-MERDIVEN'
            sah = 120.0
            if yan in ('sol', 'sag'):
                xa, xb = (x0 + sah, x1 - 25) if yan == 'sol' else (x0 + 25, x1 - sah)
                ym = (y0 + y1) / 2
                self.PL([(xa, ym), (xb, ym)], lay)
                x = xa
                while x <= xb + 0.1:
                    self.PL([(x, y0), (x, ym - 5)], lay)
                    self.PL([(x, ym + 5), (x, y1)], lay)
                    x += 28.0
                self.PL([(xa, ym - 5), (xb, ym - 5), (xb, ym + 5), (xa, ym + 5)], lay, closed=True)
                self.E.ekle((xa, y0, xb, y1), 'merdiven')
            else:
                ya, yb = (y0 + sah, y1 - 25) if yan == 'alt' else (y0 + 25, y1 - sah)
                xm = (x0 + x1) / 2
                y = ya
                while y <= yb + 0.1:
                    self.PL([(x0, y), (xm - 5, y)], lay)
                    self.PL([(xm + 5, y), (x1, y)], lay)
                    y += 28.0
                self.PL([(xm - 5, ya), (xm + 5, ya), (xm + 5, yb), (xm - 5, yb)], lay, closed=True)
                self.E.ekle((x0, ya, x1, yb), 'merdiven')
        for e in D.get('cikislar', []):
            if e.get('rect'):
                x0, y0, x1, y1 = e['rect']
                y = y0 + 40
                while y < y1 - 20:
                    self.PL([(x0 + 20, y), (x1 - 20, y)], 'ROTAS-MIMARI-MERDIVEN', lt='DASHED', lts=2.0)
                    y += 120
                self.E.ekle(tuple(e['rect']), 'rampa')

    # ---------------------------------------------------------------- engeller (sprinkler)
    def sprinkler_engelleri(self, net, van):
        T = net['T']
        seg = [(a, b) for a, b in T.edges]
        kut = [(h[0] - 14, h[1] - 14, h[0] + 14, h[1] + 14) for h in net['heads']]
        R = net['root']
        kut.append((R[0] - 30, R[1] - 30, R[0] + 30, R[1] + 30))
        kut += [v['kutu'] for v in van]
        return seg, kut

    # ---------------------------------------------------------------- kapsama haritası
    def kapsama(self, pl, kap, covs, dolaplar):
        H = pl.hedef_dugum
        hand = []
        m = np.zeros(pl.n, bool)
        m[H[kap]] = True
        g = hucre_poligon(pl, m)
        if g is not None:
            hand += self._tara(g, 'ROTAS-YANGIN-DOLAP-KAPSAMA', 'ANSI37', 80.0)
        m2 = np.zeros(pl.n, bool)
        m2[H[~kap]] = True
        if m2.any():
            g2 = hucre_poligon(pl, m2)
            if g2 is not None:
                hand += self._tara(g2, 'ROTAS-YANGIN-DOLAP-KAPSANMAYAN', 'ANSI31', 8.0)
                for q in getattr(g2, 'geoms', [g2]):
                    self.PL(list(q.exterior.coords)[:-1], 'ROTAS-YANGIN-DOLAP-KAPSANMAYAN', w=2.0, closed=True)
        # her dolabın erişim sınırı (hortum + jet)
        for d, cv in zip(dolaplar, covs):
            mm = np.zeros(pl.n, bool)
            mm[H[cv]] = True
            gd = hucre_poligon(pl, mm)
            if gd is None:
                continue
            for q in getattr(gd, 'geoms', [gd]):
                self.PL(list(q.exterior.coords)[:-1], 'ROTAS-YANGIN-DOLAP-ERISIM', closed=True, lt='DASHED', lts=6.0)
        return hand

    def _tara(self, g, lay, desen, olcek):
        hs = []
        for q in getattr(g, 'geoms', [g]):
            h = self.msp.add_hatch(dxfattribs={'layer': lay})
            h.set_pattern_fill(desen, scale=olcek)
            h.paths.add_polyline_path(list(q.exterior.coords)[:-1], is_closed=True, flags=1)
            for r in q.interiors:
                h.paths.add_polyline_path(list(r.coords)[:-1], is_closed=True, flags=0)
            hs.append(h.dxf.handle)
        return hs

    # ---------------------------------------------------------------- dolap borusu (köprülü tek polyline)
    def koprulu(self, pts, spr):
        """pts dik açılı; sprinkler borusunu kestiği yerde yarım daire köprü (bulge) — boru tek parça kalır"""
        out = []
        for a, b in zip(pts[:-1], pts[1:]):
            L = math.dist(a, b)
            u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            ks = []
            for p, q in spr:
                x = _kesisim(a, b, p, q)
                if x is None:
                    continue
                t = math.dist(a, x)
                if KOPRU_R + 2 < t < L - KOPRU_R - 2:
                    ks.append(t)
            ks.sort()
            out.append((a[0], a[1], 0.0))
            son = -1e9
            for t in ks:
                if t - son < 2 * KOPRU_R + 2:
                    continue
                out.append((a[0] + u[0] * (t - KOPRU_R), a[1] + u[1] * (t - KOPRU_R), 1.0))
                out.append((a[0] + u[0] * (t + KOPRU_R), a[1] + u[1] * (t + KOPRU_R), 0.0))
                son = t
        out.append((pts[-1][0], pts[-1][1], 0.0))
        return out

    def dolap_borulari(self, kolonlar, T, dolaplar, net):
        spr = []
        for zid, pp, dn in self.borular:
            spr += list(zip(pp[:-1], pp[1:]))
        uclar = {n for n in T.nodes if 'dolap' in T.nodes[n]}
        Z = []
        for kc in kolonlar:
            if kc['p'] not in T:
                continue
            sub = T.subgraph({kc['p']} | __import__('networkx').descendants(T, kc['p'])).copy()
            for a, b in sub.edges:
                sub[a][b]['_z'] = None
            for z in self.zincirler(sub, kc['p'], uclar):
                z['id'] = f"D{len(Z)}"
                z['kolon'] = kc['ad']
                Z.append(z)
        for z in Z:
            v = self.koprulu(z['pts'], spr)
            e = self.msp.add_lwpolyline([(x, y, 0, 0, b) for x, y, b in v], format='xyseb',
                                        dxfattribs={'layer': 'ROTAS-YANGIN-DOLAP-BORU'})
            if WD.get(z['dn']):
                e.dxf.const_width = WD[z['dn']]
            self.dolap_borular.append((z['id'], z['pts'], z['dn']))
            for a, b in zip(z['pts'][:-1], z['pts'][1:]):
                self.E.ekle(seg_kutu(a, b, WD.get(z['dn'], 0) / 2 + 1.0), f"boru{z['id']}")
        self.dolap_Z = Z
        return Z

    # ---------------------------------------------------------------- dolap sembolleri ve kolonlar
    def dolaplar_ciz(self, dolaplar):
        for d in dolaplar:
            n = d['n']
            aci = math.degrees(math.atan2(n[1], n[0])) - 90.0
            ins_p = (d['w'][0] + n[0] * 32.8, d['w'][1] + n[1] * 32.8)
            SB.ciz(self.msp, DOLAP_BLOK, ins_p[0], ins_p[1], aci=aci, no=None, katman='ROTAS-YANGIN-DOLAP')
            d['ins'] = ins_p
            d['aci'] = aci
            # sembol kutusu (gövde + yükselen boru işareti)
            c_, s_ = math.cos(math.radians(aci)), math.sin(math.radians(aci))
            xs, ys = [], []
            for x, y in ((-36, -32.8), (36, -32.8), (36, 43.5), (-36, 43.5)):
                xs.append(ins_p[0] + x * c_ - y * s_)
                ys.append(ins_p[1] + x * s_ + y * c_)
            d['sem_kutu'] = (min(xs), min(ys), max(xs), max(ys))
            self.E.ekle(d['kutu'], 'dolap')
            # ok işareti kutusu (gövde dışı kısım), dar
            xs2, ys2 = [], []
            for x, y in ((-22, -12.8), (22, -12.8), (22, 43.5), (-22, 43.5)):
                xs2.append(ins_p[0] + x * c_ - y * s_)
                ys2.append(ins_p[1] + x * s_ + y * c_)
            self.E.ekle((min(xs2), min(ys2), max(xs2), max(ys2)), 'dolap')

    def kolon_ciz(self, R, ad, s1, s2, lay):
        """kolon sembolü + balon + DN etiketi (Cizim.kolon ile aynı yöntem)"""
        self.msp.add_blockref('ROTAS-SPR-KOLON', R, dxfattribs={'layer': lay})
        self.E.ekle((R[0] - 10, R[1] - 10, R[0] + 10, R[1] + 10), 'kolon_sembol')
        for r in (40, 50, 60, 75, 95, 120, 150, 190, 240):
            for ang in range(0, 360, 15):
                c = (R[0] + r * math.cos(math.radians(ang)), R[1] + r * math.sin(math.radians(ang)))
                kb = (c[0] - 15, c[1] - 15, c[0] + 15, c[1] + 15)
                w = max(tw(s1, 9), tw(s2, 7))
                sag = c[0] >= R[0]
                kx = c[0] + 17 if sag else c[0] - 17 - w
                ke = (kx, c[1] - 14, kx + w, c[1] + 14)
                if self.E.carpar(kb) or self.E.carpar(ke):
                    continue
                u = ((R[0] - c[0]) / r, (R[1] - c[1]) / r)
                a, b = (c[0] + u[0] * 14, c[1] + u[1] * 14), (R[0] - u[0] * 10, R[1] - u[1] * 10)
                if not self.serbest_cizgi(a, b):
                    continue
                self.msp.add_circle(c, 14, dxfattribs={'layer': lay})
                self.msp.add_circle(c, 12, dxfattribs={'layer': lay})
                super().L(a, b, lay)
                self.E.ekle(kb, 'kolon_balon')
                self.E.ekle(seg_kutu(a, b, 0.5), 'kilavuz')
                self.yazilar.append((c[0], c[1], ad, 6.5, lay, 0.0, (c[0] - 11, c[1] - 5, c[0] + 11, c[1] + 5)))
                self.yazi(kx + w / 2, c[1] - th(9) / 2 + 1, s1, 9, 'ROTAS-YANGIN-DOLAP-CAP')
                self.yazi(kx + w / 2, c[1] + th(7) / 2 + 1.5, s2, 7, 'ROTAS-YANGIN-DOLAP-CAP')
                return True
        self.etiketsiz.append(('kolon', ad))
        return False

    def dolap_etiketleri(self, dolaplar):
        for d in dolaplar:
            s = d['no']
            k = self.serbest_yazi(d['o'], s, 10.0, 'ROTAS-YANGIN-DOLAP-YAZI', rmax=160, kilavuz_ilk=-1, rmin=6)
            if k is None:
                self.etiketsiz.append(('dolap', s))

    def merdiven_yazilari(self):
        for s in self.D.get('merdivenler', []):
            x0, y0, x1, y1 = s['rect']
            # merdiven yazısı merdivenin dış tarafında (kapı ve basamaklar üstüne binmez)
            dis = self.P['dis_hat']
            yw = tw(s['ad'], 12.0) / 2 + 45
            if x1 <= dis[0] + 1:
                p = (x0 - yw, (y0 + y1) / 2)
            elif x0 >= dis[2] - 1:
                p = (x1 + yw, (y0 + y1) / 2)
            elif y0 >= dis[3] - 1:
                p = ((x0 + x1) / 2, y1 + 40)
            else:
                p = ((x0 + x1) / 2, y0 - 40)
            k = self.serbest_yazi(p, s['ad'], 12.0, 'ROTAS-MIMARI-MAHAL', rmax=400, kilavuz_ilk=-1)
            if k is None:
                self.etiketsiz.append(('merdiven', s['ad']))
        for e in self.D.get('cikislar', []):
            r = e.get('rect')
            c = ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2) if r else tuple(e['p'])
            k = self.serbest_yazi(c, e['ad'], 12.0, 'ROTAS-MIMARI-MAHAL', rmax=400, kilavuz_ilk=-1)
            if k is None:
                self.etiketsiz.append(('cikis', e['ad']))

    # ---------------------------------------------------------------- tablolar
    def dolap_ozet(self, x, y, k, hd, rap):
        top = self.D['katlar']
        rows = [
            ('Dolap tipi', f"{k['tip']} yarı sert hortum makaralı, Ø25 x {fmt(k['hortum_m'], 0)} m"),
            ('Erişim ölçütü (yürüme yolu)', f"hortum {fmt(k['hortum_m'], 0)} m + lüle {fmt(k['jet_m'], 0)} m = {fmt(rap['R_m'], 0)} m"),
            ('Dolaplar arası en fazla (sprinklerli)', f"{fmt(rap['aralik_max_m'], 0)} m  ({'UYGUN' if rap['aralik_ok'] else 'AŞILDI'})"),
            ('Kattaki dolap / bina toplamı', f"{len(self.dolaplar)} ad. / {hd['n_dolap_bina']} ad. ({hd['n_kat']} kat)"),
            ('Kapsanan alan / hedef alan', f"{fmt(rap['kapsanan_m2'], 1)} / {fmt(rap['hedef_m2'], 1)} m²  (%{fmt(100 * rap['oran'], 1)})"),
            ('Kapsanmayan alan', f"{fmt(rap['kapsanmayan_m2'], 1)} m²" + ('' if rap['kapsanmayan_m2'] > 0 else ' (YOK)')),
            ('Kontrol: lüle 3 m alınırsa kapsama', f"%{fmt(100 * rap['oran_jet3'], 1)}"),
            ('Dolap debisi x eşzamanlı dolap', f"{fmt(k['debi_lpm'], 0)} l/dk x {hd['ne']} = {fmt(hd['Qd'], 0)} l/dk"),
            ('En elverişsiz dolap', f"{hd['en']['no']} ({hd['en']['kolon']}, {hd['en']['kat']})"),
            ('Dolapta gerekli basınç', f"{fmt(k['basinc_bar'], 1)} bar"),
            (f"Ana hat kaybı (DN{hd['bdn']}, {fmt(hd['Lb'], 0)} m, Q={fmt(hd['Q'], 0)} l/dk)", f"{fmt(hd['en']['dp_ana'], 2)} bar"),
            (f"Dolap kolonu kaybı (DN{k['kolon_dn']}, {fmt(hd['en']['Lk'], 1)} m)", f"{fmt(hd['en']['dp_kol'], 2)} bar"),
            (f"Kat yatay hat + bağlantı (DN{k['besleme_dn']}/DN{k['baglanti_dn']}, {fmt(hd['en']['Lh'], 1)} m)",
             f"{fmt(hd['en']['dp_yat'] + hd['en']['dp_bag'], 2)} bar"),
            ('Statik yükseklik (pompa ekseni → dolap)', f"{fmt(hd['en']['stat'] * 10.2, 1)} m = {fmt(hd['en']['stat'], 2)} bar"),
            ('Dolap için pompa basıncı', f"{fmt(hd['P_dolap'], 2)} bar"),
            ('Sprinkler için pompa basıncı (Q toplam ile)', f"{fmt(hd['P_spr'], 2)} bar"),
            ('POMPA DEBİSİ (sprinkler + dolap)', f"{fmt(hd['Qs'], 0)} + {fmt(hd['Qd'], 0)} = {fmt(hd['Q'], 0)} l/dk = {fmt(hd['Q_m3h'], 1)} m³/h"),
            ('POMPA BASMA YÜKSEKLİĞİ', f"{fmt(hd['Pp'], 2)} bar = {fmt(hd['H'], 1)} mSS ({hd['yonetici']} belirleyici)"),
            (f"YANGIN SUYU DEPOSU ({hd['sure']} dk, sprinkler + dolap)", f"{fmt(hd['V'], 1)} m³"),
            ('En alt dolapta kapalı vana basıncı (1,15·H)', f"{fmt(hd['p_alt'], 2)} bar " +
             ('> 9 bar: BASINÇ DÜŞÜRÜCÜ' if hd['bdd'] else '≤ 9 bar (düşürücü gerekmez)')),
            ('Dolap kolonu hızı', f"{fmt(hd['v_kol'], 2)} m/s (DN{k['kolon_dn']}, {fmt(hd['Qd'], 0)} l/dk)"),
        ]
        return self.tablo(x, y, 'YANGIN DOLABI HESAP ÖZETİ (06_YANGIN §5, BYKHY Md. 92-94)',
                          [('KALEM', 560, 'L'), ('DEĞER', 600, 'L')], [list(r) for r in rows], h=10.0)

    def dolap_listesi(self, x, y, dolaplar, hd):
        rows = []
        sat = {s['no']: s for s in hd['satir']}
        for d in dolaplar:
            yer = 'kolon yüzü' if d['yer'] == 'kolon' else 'duvar'
            gir = d.get('giris', '-')
            rows.append([d['no'], d['mahal'], yer, gir, d['kolon'], f"{fmt(d['en_yakin_dolap_m'], 1)}" if len(dolaplar) > 1 else '-',
                         fmt(sat[d['no']]['Pp'], 2)])
        return self.tablo(x, y, 'YANGIN DOLABI LİSTESİ (HER KATTA AYNI)',
                          [('NO', 90, 'C'), ('MAHAL', 230, 'L'), ('YER', 110, 'C'), ('MERDİVEN', 190, 'L'),
                           ('KOLON', 80, 'C'), ('EN YAKIN DOLAP (m)', 200, 'C'), ('POMPA P (bar)', 150, 'C')], rows, h=10.0)

    def kapsama_tablo(self, x, y, rap):
        rows = []
        for ad, v in rap['mahal'].items():
            rows.append([ad, fmt(v['alan'], 1), fmt(v['alan'] - v['kapsanmayan'], 1), fmt(v['kapsanmayan'], 1),
                         'TAM' if v['kapsanmayan'] <= 0 else 'EKSİK'])
        rows.append(['TOPLAM', fmt(rap['hedef_m2'], 1), fmt(rap['kapsanan_m2'], 1), fmt(rap['kapsanmayan_m2'], 1),
                     'TAM' if rap['kapsanmayan_m2'] <= 0 else 'EKSİK'])
        return self.tablo(x, y, 'KAPSAMA RAPORU (YÜRÜME YOLU, ızgara 20 cm)',
                          [('MAHAL', 300, 'L'), ('ALAN m²', 140, 'C'), ('KAPSANAN m²', 160, 'C'), ('KAPSANMAYAN m²', 190, 'C'),
                           ('DURUM', 110, 'C')], rows, h=10.0)

    def dolap_lejant(self, x, y):
        lay = 'ROTAS-YANGIN-LEJANT'
        self.msp.add_text('LEJANT (YANGIN DOLABI)', height=14, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.8}) \
            .set_placement((x, y + 8), align=TA.BOTTOM_LEFT)
        i = 0

        def yc():
            return y - 45 - i * 70

        def yaz(s):
            self.msp.add_text(s, height=10, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.8}) \
                .set_placement((x + 150, yc()), align=TA.MIDDLE_LEFT)
        SB.ciz(self.msp, DOLAP_BLOK, x + 60, yc() + 5, katman='ROTAS-YANGIN-DOLAP')
        yaz('YANGIN DOLABI TS EN 671-1, Ø25 x 30 m (YD-..), gövde duvara')
        i += 1
        self.PL([(x + 10, yc()), (x + 110, yc())], 'ROTAS-YANGIN-DOLAP-BORU', w=2.0)
        yaz('DOLAP BESLEME HATTI (DN50) / BAĞLANTI (DN32), KÖPRÜLÜ GEÇİŞ')
        i += 1
        self.msp.add_blockref('ROTAS-SPR-KOLON', (x + 35, yc()), dxfattribs={'layer': 'ROTAS-YANGIN-DOLAP-KOLON'})
        self.msp.add_circle((x + 85, yc()), 14, dxfattribs={'layer': 'ROTAS-YANGIN-DOLAP-KOLON'})
        self.msp.add_circle((x + 85, yc()), 12, dxfattribs={'layer': 'ROTAS-YANGIN-DOLAP-KOLON'})
        self.msp.add_text('YG1', height=6.5, dxfattribs={'layer': 'ROTAS-YANGIN-DOLAP-KOLON', 'style': 'ROTAS', 'width': 0.8}) \
            .set_placement((x + 85, yc()), align=TA.MIDDLE_CENTER)
        super().L((x + 44, yc()), (x + 71, yc()), 'ROTAS-YANGIN-DOLAP-KOLON')
        yaz('YANGIN DOLABI KOLONU (YG..), ÜSTTE DN, ALTTA BESLENEN DOLAP')
        i += 1
        q = [(x + 15, yc() - 18), (x + 105, yc() - 18), (x + 105, yc() + 18), (x + 15, yc() + 18)]
        h = self.msp.add_hatch(dxfattribs={'layer': 'ROTAS-YANGIN-DOLAP-KAPSAMA'})
        h.set_pattern_fill('ANSI37', scale=4.0)
        h.paths.add_polyline_path(q, is_closed=True)
        yaz('KAPSANAN ALAN (dolaptan yürüme yolu ≤ hortum + lüle menzili)')
        i += 1
        h = self.msp.add_hatch(dxfattribs={'layer': 'ROTAS-YANGIN-DOLAP-KAPSANMAYAN'})
        h.set_pattern_fill('ANSI31', scale=3.0)
        q = [(x + 15, yc() - 18), (x + 105, yc() - 18), (x + 105, yc() + 18), (x + 15, yc() + 18)]
        h.paths.add_polyline_path(q, is_closed=True)
        self.PL(q, 'ROTAS-YANGIN-DOLAP-KAPSANMAYAN', w=2.0, closed=True)
        yaz('KAPSANMAYAN ALAN (varsa)')
        i += 1
        self.PL([(x + 10, yc()), (x + 110, yc())], 'ROTAS-YANGIN-DOLAP-ERISIM', lt='DASHED', lts=2.0)
        yaz('TEK DOLABIN ERİŞİM SINIRI (ayrı katman: ROTAS-YANGIN-DOLAP-ERISIM)')
        i += 1
        return yc() - 30

    def dolap_notlar(self, x, y, k, hd, rap, uyarilar):
        nt = [
            f"Yangın dolapları {k['tip']}, yarı sert hortumlu Ø25 mm x {fmt(k['hortum_m'], 0)} m, {fmt(k['debi_lpm'], 0)} l/dk, {fmt(k['basinc_bar'], 0)} bar olacaktır (BYKHY Md. 94).",
            f"Erişim, duvar ve kapı etrafından gerçek yürüme yolu ile ölçülmüştür: hortum {fmt(k['hortum_m'], 0)} m + lüle menzili {fmt(k['jet_m'], 0)} m; kapsama haritası ROTAS-YANGIN-DOLAP-KAPSAMA katmanındadır.",
            f"Dolaplar merdiven (kat girişi) yanında ve koridorda, kaçış genişliğini daraltmayacak şekilde sıva altı / yarı gömme monte edilecektir; vana ekseni +{fmt(k['montaj_m'], 2)} m.",
            f"Sprinklerli binada dolaplar arası en fazla {fmt(k['aralik_sprinkler_m'], 0)} m'dir; dolaplar ayrı YG kolonlarından (DN{k['kolon_dn']}) beslenir, dolap bağlantısı DN{k['baglanti_dn']}.",
            f"Pompa debisine eşzamanlı {hd['ne']} dolap ({fmt(hd['Qd'], 0)} l/dk) eklenmiştir; eşzamanlı dolap sayısı BYKHY Ek-8/C ile teyit edilecektir.",
            "Dolap besleme hattı sprinkler borusunu köprü ile geçer; borular betonarme kolon ve perdeyi kesmez.",
            "Lülede 9 bar'ı aşan katlarda dolap girişine basınç düşürücü konacaktır.",
            "Kat planı tip kattır; kolon şeması ve pompa bağlantısı ayrı paftadadır (*_dolap_kolon_semasi.dxf).",
        ]
        for u in uyarilar:
            nt.append('UYARI: ' + u)
        if self.P.get('deneme'):
            nt.append('DENEME: mimari yapaydır, değerler örnektir; bu çizim uygulamada kullanılmayacaktır.')
        lay = 'ROTAS-YANGIN-NOT'
        self.msp.add_text('NOTLAR :', height=14, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.8}) \
            .set_placement((x, y), align=TA.BOTTOM_LEFT)
        for i, s in enumerate(nt):
            self.msp.add_text(f'{i + 1}. {s}', height=10, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.8}) \
                .set_placement((x, y - 30 - i * 22), align=TA.BOTTOM_LEFT)
        y2 = y - 30 - len(nt) * 22 - 20
        self.msp.add_text('KAYNAK :', height=12, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.8}) \
            .set_placement((x, y2), align=TA.BOTTOM_LEFT)
        for i, s in enumerate(KAYNAK):
            self.msp.add_text(f'- {s}', height=9, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.8}) \
                .set_placement((x, y2 - 24 - i * 18), align=TA.BOTTOM_LEFT)
        return y2 - 24 - len(KAYNAK) * 18

    def baslik_dolap(self):
        P, D = self.P, self.D
        x0, y0, x1, y1 = P['dis_hat']
        y1 = max([y1] + [q['rect'][3] for q in D.get('merdivenler', []) + D.get('cikislar', []) if q.get('rect')]) + 60
        lay = 'ROTAS-YANGIN-BASLIK'
        t = f"{D.get('plan_adi', P.get('kat_adi', ''))} YANGIN TESİSATI PLANI (SPRİNKLER + YANGIN DOLABI).........ÖLÇEK: 1 / 50"
        self.msp.add_text(t, height=35, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.8}) \
            .set_placement(((x0 + x1) / 2, y0 - 110), align=TA.MIDDLE_CENTER)
        if P.get('deneme'):
            self.msp.add_text('DENEME', height=60, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.8}) \
                .set_placement((x0, y1 + 200), align=TA.BOTTOM_LEFT)
        self.msp.add_text(P.get('proje', ''), height=25, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.8}) \
            .set_placement((x0, y1 + 140), align=TA.BOTTOM_LEFT)


def _birlestir(kenarlar):
    """aynı doğru üzerindeki üst üste / bitişik duvar çizgilerini tek parçaya indirir (çizgi üst üste binmez)"""
    yat, dik = {}, {}
    for a, b in kenarlar:
        if abs(a[1] - b[1]) < 0.1:
            yat.setdefault(round(a[1], 2), []).append(sorted((a[0], b[0])))
        elif abs(a[0] - b[0]) < 0.1:
            dik.setdefault(round(a[0], 2), []).append(sorted((a[1], b[1])))
    out = []
    for grup, yatay in ((yat, True), (dik, False)):
        for c, ar in grup.items():
            ar.sort()
            m = [list(ar[0])]
            for u, v in ar[1:]:
                if u <= m[-1][1] + 0.05:
                    m[-1][1] = max(m[-1][1], v)
                else:
                    m.append([u, v])
            for u, v in m:
                out.append(((u, c), (v, c)) if yatay else ((c, u), (c, v)))
    return out


def _kesisim(a, b, p, q):
    """iki eksene paralel parçanın iç kesişimi (dik ise)"""
    ah = abs(a[1] - b[1]) < 0.01
    ph = abs(p[1] - q[1]) < 0.01
    if ah == ph:
        return None
    if ah:
        x, y = p[0], a[1]
        if min(a[0], b[0]) < x < max(a[0], b[0]) and min(p[1], q[1]) < y < max(p[1], q[1]):
            return (x, y)
    else:
        x, y = a[0], p[1]
        if min(p[0], q[0]) < x < max(p[0], q[0]) and min(a[1], b[1]) < y < max(a[1], b[1]):
            return (x, y)
    return None


def ciz_dolapli(P, D, k, net, hes, cikti):
    """sprinkler + dolap kat planı; dönüş: (cizim, sonuç sözlüğü)"""
    c = DolapCizim(P, D)
    hes['r']['root'] = net['root']
    c.hidrolik_alan(net, hes)
    c.mimari_tam()
    c.Z = c.zincirler(net['T'], net['root'], net['heads'])
    van = c.vana_yeri(net)
    c.borular_ciz(net, van)
    c.vanalar_ciz(van)
    c.kolon(net, hes['ad'][net['root']])          # sprinkler kolon balonu önce: dolaplar ona binmesin
    eng = c.sprinkler_engelleri(net, van)
    eng = (eng[0], eng[1] + [b for b, t in c.E.items if t in ('kolon_balon', 'yazi', 'kilavuz')])
    pl = Plan(P, D, k)
    A = adaylar(pl, eng)
    dolaplar, kap, covs, rap = yerlestir(pl, A)
    c.dolaplar = dolaplar
    kolonlar, T, uy = besleme_agi(pl, dolaplar, eng)
    hand = c.kapsama(pl, kap, covs, dolaplar)
    c.dolaplar_ciz(dolaplar)
    Zd = c.dolap_borulari(kolonlar, T, dolaplar, net)
    for kc in kolonlar:
        c.kolon_ciz(kc['p'], kc['ad'], f"DN{k['kolon_dn']}", f"{len(kc['dolaplar'])} YD", 'ROTAS-YANGIN-DOLAP-KOLON')
    c.cap_etiketleri()
    c.cap_lay = 'ROTAS-YANGIN-DOLAP-CAP'
    for z in sorted(Zd, key=lambda z: sum(math.dist(a, b) for a, b in zip(z['pts'][:-1], z['pts'][1:]))):
        z2 = dict(z)
        z2['n'] = f"{z['n']} YD"
        if not c.etiket_zincir(z2):
            # kısa bağlantı parçası: kılavuzlu tek satır "DN32"
            a_, b_ = max(zip(z['pts'][:-1], z['pts'][1:]), key=lambda q: math.dist(*q))
            m_ = ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2)
            if c.serbest_yazi(m_, f"DN{z['dn']}", 10.0, 'ROTAS-YANGIN-DOLAP-CAP', rmax=220, kilavuz_ilk=0, rmin=12) is None:
                c.etiketsiz.append(('dolap_boru', z['id'], z['dn']))
    c.cap_lay = 'ROTAS-YANGIN-SPR-CAP'
    c.dolap_etiketleri(dolaplar)
    c.vana_etiket(van)
    c.dugumler(hes)
    c.mahal_adlari()
    c.merdiven_yazilari()
    c.alan_yazi(hes)
    c.yazilari_bas()
    # kapsama taramaları en altta görünsün
    if hand:
        sira = [(h, f'{i + 1:X}') for i, h in enumerate(hand)]
        diger = [(e.dxf.handle, e.dxf.handle) for e in c.msp if e.dxf.handle not in hand]
        c.msp.set_redraw_order(sira + diger)
    return c, dict(pl=pl, dolaplar=dolaplar, kap=kap, rap=rap, kolonlar=kolonlar, T=T, uyari=uy, van=van, Zd=Zd,
                   aday=len(A))


def tablolar_ve_kaydet(c, P, D, k, hes, net, sonuc, hd, cikti):
    x0, y0, x1, y1 = P['dis_hat']
    xm = max([x1] + [q['rect'][2] for q in D.get('merdivenler', []) + D.get('cikislar', []) if q.get('rect')])
    ym = min([y0] + [q['rect'][1] for q in D.get('merdivenler', []) + D.get('cikislar', []) if q.get('rect')])
    X = xm + 450
    yb = c.ozet_tablo(X, y1, hes, net)
    yb = c.ekipman_tablo(X, yb - 120, sonuc['van'], net, hes)
    yb = c.lejant(X, yb - 110)
    yb = c.dolap_lejant(X, yb - 60)
    X2 = X + 1300
    yb2 = c.dolap_ozet(X2, y1, k, hd, sonuc['rap'])
    yb2 = c.dolap_listesi(X2, yb2 - 120, sonuc['dolaplar'], hd)
    yb2 = c.kapsama_tablo(X2, yb2 - 120, sonuc['rap'])
    c.dolap_notlar(x0, ym - 260, k, hd, sonuc['rap'], sonuc['uyari'])
    c.dugum_tablo(X2 + 1350, y1, hes)
    c.baslik_dolap()
    c.doc.saveas(cikti)
