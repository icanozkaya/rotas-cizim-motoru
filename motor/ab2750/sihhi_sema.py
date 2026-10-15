# -*- coding: utf-8 -*-
"""2750/7 SIHHİ — AÇILIMLI KOLON ŞEMASI (merkezi sistem), rögar şeması, yağmur şeması (blok başına).

Kurgu (kullanıcı, merkezi sistem — README VOYAP kuralı): kat bantları; sol uçta teknik merkez (şebeke + ana sayaç ->
depo dolum kolonu -> çatıdaki depo -> soğuk dağıtım kolonu; A blok bodrumunda boylerler, sıcak + sirkülasyon kolonları;
B blok sıcak/sirkülasyon A blok kazan dairesinden); her kat bandında asma tavandan kat dağıtımı (S/H/R) -> her dairenin
SAYAÇ DOLABI (soğuk + sıcak su sayacı, sirkülasyon dolapta biter) -> daire içi soğuk/sıcak -> armatürler.
Pis su: ıslak hacim grubu -> kolon (P..) -> çatıda havalık, zeminde T.K. + rögar (R..). Semboller saf geometri
(motor/sihhi2/sema_sembol.py yan görünüş armatürleri). Birim cm."""
import math
import os
import sys

from shapely.geometry import LineString, Point, box

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
sys.path.insert(0, os.path.join(BURASI, '..', 'sihhi2'))
import sihhi_cizim as C        # noqa: E402
import sihhi_tasarim as T      # noqa: E402
import sema_sembol as SS       # noqa: E402

BANT = 400.0
ARA = 88.0                     # armatür aralığı
SIRA = {'banyo': ['LV', 'WC', 'YS', 'DUS', 'CM'], 'mutfak': ['BM', 'EV'], 'bodrum': ['LV', 'WC', 'ABD', 'EV']}
KATLAR = {'A': ['B', 'Z', '1', '2'], 'B': ['Z', '1', '2']}
KAT_YAZI = {'B': 'BODRUM KAT', 'Z': 'ZEMİN KAT', '1': '1. KAT', '2': '2. KAT'}
Y_TAVAN = (305.0, 312.0, 319.0)      # kat dağıtım: soğuk / sıcak / sirkülasyon
Y_DOLAP = 250.0
Y_S1, Y_S2 = 250.0, 130.0
Y_KOL = -50.0


def hazirla(doc):
    if 'ROTAS-YAZI' not in doc.styles:
        doc.styles.add('ROTAS-YAZI', font='arial.ttf')
    if 'ROTAS-SEMA-LAVABO' not in doc.blocks:
        SS.bloklar(doc)
    for ad, r in (('ROTAS-SEMA-BANT', 7), ('ROTAS-SEMA-KAT-YAZI', 1), ('ROTAS-SEMA-ARMATUR', 4), ('ROTAS-SEMA-YAZI', 7)):
        C.katman(doc, ad, r)


# ====================================================================== veri: daire yığınları
def yiginlar(M):
    Fs = M['Fs']
    st = []
    for k in ('Z', '1', '2'):
        F = Fs[k]
        for no, D in F.daire.items():
            d = F.dol.get(no)
            if d is None:
                continue
            p = (d['c'][0] - F.dx, d['c'][1])
            for s in st:
                if math.dist(s['p'], p) < 80:
                    s['kat'][k] = (no, D)
                    break
            else:
                st.append(dict(p=p, kat={k: (no, D)}))
    st.sort(key=lambda s: (round(s['p'][0] / 100), -s['p'][1]))
    for s in st:
        gr = {}
        for k, (no, D) in s['kat'].items():
            for W in D['islak']:
                kn = W.get('kolon_no')
                if not kn:
                    continue
                g = gr.setdefault(kn, dict(kolon=kn, tip=W['tip'], kat={}))
                tips = [a['tip'] for a in W['armatur']]
                g['kat'][k] = dict(tips=[t for t in SIRA[W['tip']] if t in tips] +
                                   [t for t in tips if t not in SIRA[W['tip']]], W=W)
        for g in gr.values():
            alls = []
            for v in g['kat'].values():
                for t in v['tips']:
                    if t not in alls:
                        alls.append(t)
            g['tips'] = [t for t in SIRA[g['tip']] if t in alls]
        s['gruplar'] = sorted(gr.values(), key=lambda g: (g['tip'] != 'banyo', g['kolon']))
    return st


# ====================================================================== çizim
class Sema:
    def __init__(self, msp, M, x0, y0):
        self.m, self.M, self.x0, self.y0 = msp, M, x0, y0
        self.blok = M['blok']
        self.katlar = KATLAR[self.blok]
        self.yb = {k: y0 + i * BANT for i, k in enumerate(self.katlar)}
        self.ytop = y0 + len(self.katlar) * BANT
        self.E = C.Engel()

    def L(self, pts, kat, engel=True):
        e = self.m.add_lwpolyline([(float(x), float(y)) for x, y in pts], dxfattribs={'layer': kat})
        if engel:
            self.E.ekle(LineString(pts).buffer(1.0), 'hat')
        return e

    def T(self, s, p, h=10, kat='ROTAS-SEMA-YAZI', al='BL', rot=0.0, renk=None, engel=True):
        C.yazi(self.m, s, p, h, kat, al, rot, renk=renk)
        if engel:
            self.E.ekle(C.yazi_kutusu(s, p, h, al, rot), 'yazi')

    def B(self, ad, p, kat='ROTAS-SEMA-ARMATUR', rot=0.0, olcek=1.0):
        return C.blok(self.m, ad, p, kat, rot, olcek)

    # ------------------------------------------------------------------
    def ciz(self):
        st = yiginlar(self.M)
        self.st = st
        x = self.x0 + 700          # teknik merkez genişliği
        yer = []
        for s in st:
            s['x'] = x
            gx = x + 110
            for g in s['gruplar']:
                g['x'] = gx                          # kolon ekseni
                g['w'] = 70 + len(g['tips']) * ARA
                gx += g['w'] + 40
            s['w'] = gx - x
            x = gx + 60
        self.x1 = x + 40
        self._bantlar()
        self._teknik()
        for s in st:
            self._yigin(s)
        self._kolonlar()
        self._rogar_semasi()
        self._yagmur_semasi()
        return dict(x1=self.xy1, y_alt=self.y_alt, y_ust=self.ytop + 450)

    def _bantlar(self):
        x0, x1 = self.x0 + 50, self.x1
        for k, yb in self.yb.items():
            self.m.add_line((x0 - 50, yb), (x1 + 50, yb), dxfattribs={'layer': 'ROTAS-SEMA-BANT'})
            for xx in (x0 - 25, x1 + 25):
                self.T(KAT_YAZI[k].replace(' KAT', '. KAT') if k == 'Z' else KAT_YAZI[k], (xx, yb + 52), 25,
                       'ROTAS-SEMA-KAT-YAZI', 'ML', 90)
        self.m.add_line((x0 - 50, self.ytop), (x1 + 50, self.ytop), dxfattribs={'layer': 'ROTAS-SEMA-BANT'})
        for xx in (x0 - 50, x0, x1, x1 + 50):
            self.m.add_line((xx, self.y0), (xx, self.ytop), dxfattribs={'layer': 'ROTAS-SEMA-BANT'})
        self.T('ÇATI DÖŞEMESİ', (x0 + 10, self.ytop + 6), 12)

    # ------------------------------------------------------------------ teknik merkez
    def _teknik(self):
        M, m = self.M, self.m
        X = self.x0 + 140
        xs = {'DD': X, 'S': X + 60, 'H': X + 90, 'R': X + 120}
        self.xs = xs
        yZ = self.yb['Z']
        alt = self.yb[self.katlar[0]]
        # şebeke + ana sayaç (zemin bandı, +15)
        ys = yZ + 40
        self.T('ŞEBEKEDEN (SASKİ)', (self.x0 + 60, ys - 25), 12)
        self.L([(self.x0 + 60, ys), (xs['DD'], ys)], 'ROTAS-SEBEKE')
        for i, ad in enumerate(('ROTAS-SEMA-KURESEL-VANA', 'ROTAS-SEMA-PISLIK-TUTUCU', 'ROTAS-SEMA-SU-SAYACI',
                                'ROTAS-SEMA-CEKVALF', 'ROTAS-SEMA-KURESEL-VANA')):
            self.B(ad, (self.x0 + 75 + 13 * i * 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 12 * 0 + 0 + i * 12 * 0 + i * 12, ys), 'ROTAS-VANA', olcek=0.5)
        self.T('ANA SAYAÇ DN50', (self.x0 + 62, ys + 10), 9)
        # depo (çatı)
        n = self.M['daire_sayisi']
        V = 3.0 + 0.5 * max(0, n - 10)
        dx0, dy0 = self.x0 + 80, self.ytop + 150
        dw, dh = 260.0, 170.0
        self.L([(dx0, dy0), (dx0 + dw, dy0), (dx0 + dw, dy0 + dh), (dx0, dy0 + dh), (dx0, dy0)], 'ROTAS-DEPO')
        h = m.add_hatch(color=8, dxfattribs={'layer': 'ROTAS-DEPO'})
        h.set_pattern_fill('ANSI31', scale=2.0)
        h.paths.add_polyline_path([(dx0 - 10, dy0 - 25), (dx0 + dw + 10, dy0 - 25), (dx0 + dw + 10, dy0), (dx0 - 10, dy0)], is_closed=True)
        self.T('KULLANIM SU DEPOSU', (dx0 + dw / 2, dy0 + dh / 2 + 12), 13, 'ROTAS-DEPO', 'MC', renk=3)
        self.T('V=%g m³ (ÇATI)' % V, (dx0 + dw / 2, dy0 + dh / 2 - 12), 13, 'ROTAS-DEPO', 'MC', renk=3)
        self.depo = (dx0, dy0, dw, dh, V)
        # dolum: şebekeden depoya (depo üstünden şamandıralı)
        self.L([(xs['DD'], ys), (xs['DD'], dy0 + dh + 30), (dx0 + 40, dy0 + dh + 30), (dx0 + 40, dy0 + dh)], 'ROTAS-SEBEKE')
        self.B('ROTAS-SEMA-KURESEL-VANA', (dx0 + 40, dy0 + dh + 12), 'ROTAS-VANA', 90, 0.6)
        self.T('ŞAMANDIRALI DOLUM', (dx0 + 48, dy0 + dh + 36), 9)
        # dağıtım: depodan aşağı soğuk kolonu
        yalt_S = alt + 25 if self.blok == 'A' else yZ + 60
        self.L([(dx0 + dw - 40, dy0), (dx0 + dw - 40, dy0 - 45), (xs['S'], dy0 - 45), (xs['S'], yalt_S)], 'ROTAS-SOGUKSU')
        self.B('ROTAS-SEMA-KURESEL-VANA', (dx0 + dw - 40, dy0 - 20), 'ROTAS-VANA', 90, 0.6)
        # taşma + boşaltma -> yağmur inişi (açık uç yok)
        yb1 = self.M['yagmur'][0]['no'] if self.M['yagmur'] else 'YB'
        self.L([(dx0 + dw, dy0 + dh - 20), (dx0 + dw + 60, dy0 + dh - 20), (dx0 + dw + 60, dy0 + 10)], 'ROTAS-YAGMUR')
        self.L([(dx0 + dw - 10, dy0), (dx0 + dw - 10, dy0 - 12), (dx0 + dw + 60, dy0 - 12), (dx0 + dw + 60, dy0 + 10)], 'ROTAS-YAGMUR')
        self.B('ROTAS-SEMA-KURESEL-VANA', (dx0 + dw + 25, dy0 - 12), 'ROTAS-VANA', 0, 0.5)
        self.T('TAŞMA Ø50 + BOŞALTMA Ø40 -> %s İNİŞİNE' % yb1, (dx0 + dw + 70, dy0), 9, renk=3)
        # sıcak / sirkülasyon
        if self.blok == 'A':
            yB = self.yb['B']
            bx = self.x0 + 300
            for i in range(2):
                cx = bx + i * 110
                self.L([(cx - 35, yB + 40), (cx + 35, yB + 40), (cx + 35, yB + 230), (cx - 35, yB + 230), (cx - 35, yB + 40)], 'ROTAS-KAZAN')
                self.T('BOYLER-%d' % (i + 1), (cx, yB + 135), 10, 'ROTAS-KAZAN', 'MC', 90)
            self.T('KAZAN DAİRESİ: 2x1500 lt ÇİFT SERPANTİNLİ BOYLER', (bx - 40, yB + 20), 10, 'ROTAS-KAZAN')
            # soğuk besleme -> boyler alt
            self.L([(xs['S'], yalt_S), (xs['S'], yB + 60), (bx - 35, yB + 60)], 'ROTAS-SOGUKSU')
            # sıcak: boyler üstünden yukarı
            self.L([(bx + 145, yB + 210), (bx + 165, yB + 210), (bx + 165, yB + 260), (xs['H'], yB + 260), (xs['H'], self.ytop - 60)], 'ROTAS-SICAKSU')
            self.L([(xs['R'], self.ytop - 60), (xs['R'], yB + 280), (bx + 185, yB + 280), (bx + 185, yB + 100), (bx + 145, yB + 100)], 'ROTAS-SIRKULASYON')
            self.T('SİRK. POMPASI', (bx + 190, yB + 180), 9, rot=90)
            # B bloğa
            self.L([(bx + 165, yB + 260), (bx + 220, yB + 260), (bx + 220, yB + 330)], 'ROTAS-SICAKSU')
            self.L([(bx + 185, yB + 280), (bx + 240, yB + 280), (bx + 240, yB + 330)], 'ROTAS-SIRKULASYON')
            self.T('B BLOĞA (TOPRAK ALTI): H Ø50 + R Ø32', (bx + 250, yB + 335), 9)
        else:
            yb = self.yb['Z']
            self.L([(self.x0 + 60, yb + 100), (xs['H'], yb + 100), (xs['H'], self.ytop - 60)], 'ROTAS-SICAKSU')
            self.L([(xs['R'], self.ytop - 60), (xs['R'], yb + 85), (self.x0 + 60, yb + 85)], 'ROTAS-SIRKULASYON')
            self.T('A BLOK KAZAN DAİRESİNDEN', (self.x0 + 60, yb + 125), 9)
            self.T('H Ø50 + R Ø32 (TOPRAK ALTI)', (self.x0 + 60, yb + 112), 9)
        # kolon etiketleri (teknik)
        kr = self.M['Fs']['Z'].koridor
        ys_ = sum(F.koridor['yb_s'] for F in self.M['Fs'].values())
        yh_ = sum(F.koridor['yb_h'] for F in self.M['Fs'].values())
        yt = self.yb[self.katlar[-1]]
        self.T('S: %s / %g YB' % (T.temiz_cap(ys_), ys_), (xs['S'] - 6, yt + 120), 10, rot=90, al='BL')
        self.T('H: %s / %g YB' % (T.temiz_cap(yh_), yh_), (xs['H'] - 6, yt + 120), 10, rot=90, al='BL')
        self.T('DEPO DOLUM DN50', (xs['DD'] - 6, yt + 120), 10, rot=90, al='BL')
        self.T('R: Ø40', (xs['R'] - 6, yt + 120), 10, rot=90, al='BL')
        # kat dağıtım (asma tavan): riserden her dolaba
        xmax = max(s_['x'] + 30 + 7 * 2 - 7 for s_ in self.st) if self.st else X + 200
        for k in ('Z', '1', '2'):
            yb = self.yb[k]
            for i, (lay, key) in enumerate((('ROTAS-SOGUKSU', 'S'), ('ROTAS-SICAKSU', 'H'), ('ROTAS-SIRKULASYON', 'R'))):
                xe = max(s_['x'] + 30 + 7 * i - 7 for s_ in self.st if k in s_['kat'])
                self.L([(xs[key], yb + Y_TAVAN[i]), (xe, yb + Y_TAVAN[i])], lay)
            F = self.M['Fs'][k]
            kr = F.koridor
            self.T('KAT DAĞITIMI (ASMA TAVAN) S: %s / %g YB  H: %s / %g YB  R: Ø32' % (
                T.temiz_cap(kr['yb_s']), kr['yb_s'], T.temiz_cap(kr['yb_h']), kr['yb_h']), (xs['R'] + 20, yb + 326), 10)
        if self.blok == 'A':
            self._bodrum_grup()
        # akış okları
        for k in self.katlar:
            yb = self.yb[k]
            self.B('ROTAS-SEMA-AKIS-OKU', (xs['DD'] - 12, yb + 200), 'ROTAS-SEBEKE')
            self.B('ROTAS-SEMA-AKIS-OKU', (xs['S'] - 12, yb + 200), 'ROTAS-SOGUKSU', 180)

    def _bodrum_grup(self):
        B = self.M['bodrum']
        yb = self.yb['B']
        xs = self.xs
        x0 = self.x0 + 760
        from collections import Counter
        c = Counter(a['tip'] for a in B['armatur'])
        tips = []
        for t in ('LV', 'WC', 'ABD', 'EV'):
            tips += [t] * c.get(t, 0)
        pos = [x0 + 90 + i * ARA for i in range(len(tips))]
        # ortak alan sayacı
        self.L([(xs['S'], yb + 25), (x0 - 20, yb + 25), (x0 - 20, yb + Y_S2), (pos[-1] + 5, yb + Y_S2)], 'ROTAS-SOGUKSU')
        self.B('ROTAS-SEMA-SU-SAYACI', (x0 - 60, yb + 25), 'ROTAS-SAYAC-DOLABI', olcek=0.8)
        self.T('ORTAK ALAN SAYACI', (x0 - 110, yb + 8), 9)
        sic = [p for p, t in zip(pos, tips) if t in ('LV', 'EV', 'ABD')]
        bx = self.x0 + 300
        self.L([(bx + 220, yb + 260), (x0 - 15, yb + 260), (x0 - 15, yb + Y_S2 + 5), (max(sic) - 5, yb + Y_S2 + 5)], 'ROTAS-SICAKSU')
        for x, t in zip(pos, tips):
            ad = SS.ARM_BLOK.get(t if t != 'ABD' else 'LV')
            self.B(ad, (x, yb))
            hs, cs = SS.BAG.get(t if t != 'ABD' else 'LV')
            if cs is not None:
                self.L([(x + cs[0], yb + Y_S2), (x + cs[0], yb + cs[1])], 'ROTAS-SOGUKSU', engel=False)
            if hs is not None and t in ('LV', 'EV', 'ABD'):
                self.L([(x + hs[0], yb + Y_S2 + 5), (x + hs[0], yb + hs[1])], 'ROTAS-SICAKSU', engel=False)
            self.L([(x, yb), (x, yb - 38), (x - 12, yb - 50)], 'ROTAS-PISSU', engel=False)
        if 'ABD' in tips:
            self.T('ABDEST MUSLUKLARI', (pos[tips.index('ABD')] - 30, yb + 150), 9)
        # pis su çukuru + pompalar (bant tabanının altında değil: bodrum döşemesi altında)
        xc = pos[-1] + 140
        self.L([(x0 + 60, yb - 50), (xc - 50, yb - 50)], 'ROTAS-PISSU')
        self.L([(xc - 50, yb - 10), (xc + 50, yb - 10), (xc + 50, yb - 140), (xc - 50, yb - 140), (xc - 50, yb - 10)], 'ROTAS-POMPA')
        self.T('PİS SU ÇUKURU 100x100x120', (xc + 60, yb - 130), 9)
        self.T('Ø%d / %g SB' % (T.pis_cap(B['sb'], True), B['sb']), (x0 + 70, yb - 66), 9, 'ROTAS-PISSU-CAP')
        for dx in (-22, 22):
            self.B('ROTAS-PL-POMPA', (xc + dx, yb - 115), 'ROTAS-POMPA', 90, 0.7)
        self.L([(xc + 22, yb - 100), (xc + 22, yb + 290), (xc + 90, yb + 290)], 'ROTAS-PISSU')
        self.B('ROTAS-SEMA-CEKVALF', (xc + 22, yb + 40), 'ROTAS-VANA', 90, 0.6)
        self.B('ROTAS-SEMA-KURESEL-VANA', (xc + 22, yb + 80), 'ROTAS-VANA', 90, 0.6)
        self.T('BASMA HATTI Ø63 -> RP (AYRI RÖGAR)', (xc + 95, yb + 285), 9)
        self.T('2 AD. DALGIÇ POMPA (1 ASIL + 1 YEDEK)', (xc + 60, yb - 110), 9)

    # ------------------------------------------------------------------ daire yığını
    def _yigin(self, s):
        xs = self.xs
        for k in ('Z', '1', '2'):
            if k not in s['kat']:
                continue
            no, D = s['kat'][k]
            yb = self.yb[k]
            xd = s['x'] + 30
            t = D.get('temiz', {})
            # kat dağıtımından dolaba
            for i, (lay, key) in enumerate((('ROTAS-SOGUKSU', 'S'), ('ROTAS-SICAKSU', 'H'), ('ROTAS-SIRKULASYON', 'R'))):
                self.L([(xd + 7 * i - 7, yb + Y_TAVAN[i]), (xd + 7 * i - 7, yb + Y_DOLAP + 14)], lay)
            # dolap
            self.L([(xd - 30, yb + Y_DOLAP - 14), (xd + 30, yb + Y_DOLAP - 14), (xd + 30, yb + Y_DOLAP + 14),
                    (xd - 30, yb + Y_DOLAP + 14), (xd - 30, yb + Y_DOLAP - 14)], 'ROTAS-SAYAC-DOLABI')
            self.B('ROTAS-SEMA-SU-SAYACI', (xd - 14, yb + Y_DOLAP), 'ROTAS-SAYAC-DOLABI', olcek=0.7)
            self.B('ROTAS-SEMA-SU-SAYACI', (xd + 14, yb + Y_DOLAP), 'ROTAS-SAYAC-DOLABI', olcek=0.7)
            self.T('SD-%d' % no, (xd, yb + Y_DOLAP - 30), 10, 'ROTAS-SAYAC-DOLABI', 'MC')
            # daire balonu
            self.B('ROTAS-SEMA-DAIRE-NO', (xd + 10, yb + 345 - 55 + 0), 'ROTAS-PISSU-KOLONNO', olcek=0.55)
            self.T('D%d' % no, (xd + 10, yb + 290), 20, 'ROTAS-PISSU-KOLONNO', 'MC', renk=6)
            # daire içi soğuk / sıcak
            gs = [g for g in s['gruplar'] if k in g['kat']]
            if not gs:
                continue
            xe = max(g['x'] + 70 + (len(g['tips']) - 1) * ARA for g in gs)
            self.L([(xd + 30, yb + Y_S1), (xe + 5, yb + Y_S1)], 'ROTAS-SOGUKSU')
            self.L([(xd + 30, yb + Y_S1 - 5), (xe, yb + Y_S1 - 5)], 'ROTAS-SICAKSU')
            self.T('S: %s / %g YB' % (T.temiz_cap(t.get('yb_s', 0)), t.get('yb_s', 0)), (xd + 34, yb + Y_S1 + 4), 10)
            self.T('H: %s / %g YB' % (T.temiz_cap(t.get('yb_h', 0)), t.get('yb_h', 0)), (xd + 34, yb + Y_S1 + 17), 10)
            for g in gs:
                self._grup(g, k, yb)

    def _grup(self, g, k, yb):
        tips = g['kat'][k]['tips']
        xg = g['x']
        xa0 = xg + 70
        xs = [xa0 + i * ARA for i, t in enumerate(g['tips'])]
        pos = {t: xs[i] for i, t in enumerate(g['tips'])}
        sic = [t for t in tips if t in T.SICAK]
        su = [t for t in tips if t in T.YB]
        # soğuk iniş: grup sol ucundan (kolon + 30)
        xdr = xg + 30
        if su:
            xe = max(pos[t] for t in su)
            self.L([(xdr, yb + Y_S1), (xdr, yb + Y_S2), (xe + 5, yb + Y_S2)], 'ROTAS-SOGUKSU')
        if sic:
            xe2 = max(pos[t] for t in sic)
            self.L([(xdr + 5, yb + Y_S1 - 5), (xdr + 5, yb + Y_S2 + 5), (xe2 - 5, yb + Y_S2 + 5)], 'ROTAS-SICAKSU')
        ys_ = sum(T.YB[t][0] for t in su)
        yh_ = sum(T.YB[t][1] for t in sic)
        self.T('%s / %g YB' % (T.temiz_cap(ys_), ys_), (xdr + 8, yb + Y_S2 + 26), 9)
        if sic:
            self.T('%s / %g YB' % (T.temiz_cap(yh_), yh_), (xdr + 8, yb + Y_S2 + 38), 9)
        # armatürler
        for t in tips:
            x = pos[t]
            ad = SS.ARM_BLOK.get(t if t != 'ABD' else 'LV')
            self.B(ad, (x, yb))
            bag = SS.BAG.get(t if t != 'ABD' else 'LV', (None, (0, 100)))
            hs, cs = bag
            if cs is not None:
                self.L([(x + cs[0], yb + Y_S2), (x + cs[0], yb + cs[1])], 'ROTAS-SOGUKSU', engel=False)
            if hs is not None and t in T.SICAK:
                self.L([(x + hs[0], yb + Y_S2 + 5), (x + hs[0], yb + hs[1])], 'ROTAS-SICAKSU', engel=False)
            # pis su inişi
            self.L([(x, yb), (x, yb + Y_KOL + 12), (x - 12, yb + Y_KOL)], 'ROTAS-PISSU', engel=False)
            sb = T.SB[t]
            self.T('Ø%d' % T.pis_cap(sb, t == 'WC'), (x + 4, yb - 22), 8, 'ROTAS-PISSU-CAP')
            self.T('%g SB' % sb, (x + 4, yb - 32), 8, 'ROTAS-PISSU-CAP')
        # toplayıcı
        if tips:
            xe = max(pos[t] for t in tips)
            self.L([(xg + 6, yb + Y_KOL), (xe - 12, yb + Y_KOL)], 'ROTAS-PISSU')
            sb_t = sum(T.SB[t] for t in tips)
            self.T('Ø%d / %g SB' % (T.pis_cap(sb_t, 'WC' in tips), sb_t), (xg + 12, yb + Y_KOL - 14), 9, 'ROTAS-PISSU-CAP')

    # ------------------------------------------------------------------ kolonlar (havalık, T.K., rögar)
    def _kolonlar(self):
        M = self.M
        ks = {k['no']: k for k in M['kolonlar']}
        rog = {}
        for r in M['altyapi']['rogarlar']:
            for kn in r['kolonlar']:
                rog[kn] = r['no']
        for b in M['altyapi']['baglar']:
            if b.get('kolona'):
                rog[b['kolon']] = rog.get(b['kolona'], '?')
        yZ = self.yb['Z']
        self.kolon_x = {}
        for s in self.st:
            for g in s['gruplar']:
                kn = g['kolon']
                if kn in self.kolon_x:
                    continue
                x = g['x']
                self.kolon_x[kn] = x
                ust = max(self.katlar.index(q) for q in ks[kn]['katlar'])
                ytop = self.ytop + 50
                ybot = yZ - 75
                for dx in (-5, 5):
                    self.m.add_line((x + dx, ybot), (x + dx, ytop), dxfattribs={'layer': 'ROTAS-PISSU-KOLON'})
                self.m.add_line((x, ybot), (x, ytop), dxfattribs={'layer': 'ROTAS-PISSU'})
                self.E.ekle(box(x - 6, ybot, x + 6, ytop), 'hat')
                self.B('ROTAS-SEMA-HAVALIK', (x, ytop), 'ROTAS-PISSU-KOLON')
                self.B('ROTAS-SEMA-KOLON-NO', (x, ytop + 55), 'ROTAS-PISSU-KOLONNO')
                self.T(kn, (x, ytop + 55), 18 if len(kn) <= 3 else 15, 'ROTAS-PISSU-KOLONNO', 'MC', renk=6, engel=False)
                # T.K. + dirsek + rögar
                self.B('ROTAS-SEMA-TEMIZLEME-KAPAGI', (x - 20, yZ + 24), 'ROTAS-PISSU-KOLON', olcek=0.8)
                self.T('T.K.', (x - 34, yZ + 20), 9, 'ROTAS-PISSU-CAP', 'BR', renk=1)
                self.L([(x, ybot), (x + 12, ybot - 12), (x + 30, ybot - 12)], 'ROTAS-PISSU')
                self.B('ROTAS-SEMA-ROGAR-OK', (x + 30, ybot - 12), 'ROTAS-ROGAR', olcek=0.6)
                self.T(rog.get(kn, 'R'), (x + 54, ybot - 18), 14, 'ROTAS-ROGAR', 'BL', renk=5)
                # kat etiketleri (o kattan aşağı toplam)
                k = ks[kn]
                acc = 0
                for q in reversed(self.katlar):
                    if q in k['katlar']:
                        acc += k['katlar'][q]['sb']
                    if q == 'B' or acc == 0:
                        continue
                    yb = self.yb[q]
                    self.T('Ø%d / %g SB' % (T.pis_cap(acc, k['tip'] == 'banyo'), acc), (x - 9, yb + 120), 9,
                           'ROTAS-PISSU-CAP', 'BL', 90)

    # ------------------------------------------------------------------ rögar şeması
    def _rogar_semasi(self):
        AY = self.M['altyapi']
        y = self.y0 - 520
        if self.blok == 'A':
            y = self.yb['B'] - 420
        R = {r['no']: r for r in AY['rogarlar']}
        kol_rog = {}
        for r in AY['rogarlar']:
            for kn in r['kolonlar']:
                kol_rog.setdefault(r['no'], []).append(kn)
        for b in AY['baglar']:
            if b.get('kolona'):
                for rn, ks in kol_rog.items():
                    if b['kolona'] in ks:
                        ks.append(b['kolon'])
        x = self.x0 + 300
        pos = {}
        for d in AY['diziler']:
            for rn in d:
                if rn in pos:
                    continue
                pos[rn] = x
                x += 250
        pos['PB'] = x + 60
        for rn, xx in pos.items():
            if rn == 'PB':
                self.B('ROTAS-PL-PB', (xx, y), 'ROTAS-ROGAR')
                self.T('PB', (xx, y), 22, 'ROTAS-ROGAR', 'MC', renk=5)
                self.T('80x80 / h:-%d cm' % AY['pb']['h'], (xx, y - 55), 9, 'ROTAS-ROGAR', 'TC')
                self.T('SASKİ ATIKSU KANALINA', (xx + 60, y), 12, 'ROTAS-ROGAR', 'ML')
                continue
            r = R[rn]
            self.B('ROTAS-PL-ROGAR', (xx, y), 'ROTAS-ROGAR')
            self.T(rn, (xx, y), 20, 'ROTAS-ROGAR', 'MC', renk=5)
            self.T('%s / h:-%d cm' % (r['olcu'], r['h']), (xx, y - 48), 9, 'ROTAS-ROGAR', 'TC')
            ks = kol_rog.get(rn, [])
            for i, kn in enumerate(ks):
                cx = xx - 30 + 60 * (i % 2)
                cy = y + 110 + 62 * (i // 2)
                self.B('ROTAS-SEMA-KOLON-NO', (cx, cy), 'ROTAS-PISSU-KOLONNO')
                self.T(kn, (cx, cy), 15, 'ROTAS-PISSU-KOLONNO', 'MC', renk=6)
            if ks:
                self.L([(xx, y + 35), (xx, y + 80)], 'ROTAS-PISSU')
        for h in AY['zincir']:
            xa, xb = pos[h['a']], pos[h['b']]
            if xa > xb:
                xa, xb = xb, xa
                # akış ters yön (doğu dizisi): hat yine iki rögar arasında; ok yönü
            ya = y
            self.L([(xa + (41 if pos.get('PB') == xa else 36), ya), (xb - (41 if pos.get('PB') == xb else 36), ya)], 'ROTAS-ALTYAPI-PIS')
            xm = (xa + xb) / 2
            self.T('L=%.2f m / Q=Ø%d / %%1' % (h['L'] / 100, h['cap']), (xm, ya + 8), 9, 'ROTAS-ALTYAPI-YAZI', 'BC')
        self.xy1 = max(self.x1 + 700, pos['PB'] + 400)
        self.y_alt = y - 120
        self.rogar_pos = pos

    # ------------------------------------------------------------------ yağmur şeması
    def _yagmur_semasi(self):
        M = self.M
        yb = M['yagmur']
        x = self.x1 + 120
        yZ = self.yb['Z']
        for i, q in enumerate(yb):
            xx = x + 60 * i
            self.L([(xx, yZ - 20), (xx, self.ytop + 10)], 'ROTAS-YAGMUR')
            self.B('ROTAS-SEMA-KOLON-NO-YAGMUR', (xx, self.ytop + 40), 'ROTAS-YAGMUR-NO')
            self.T(q['no'], (xx, self.ytop + 40), 13, 'ROTAS-YAGMUR-NO', 'MC', renk=3, engel=False)
            for k in ('Z', '1', '2'):
                self.T(self.M['yagmur_cap'], (xx - 4, self.yb[k] + 170), 9, 'ROTAS-YAGMUR-NO', 'BL', 90, renk=3)
            self.B('ROTAS-SEMA-DESARJ-OK', (xx, yZ - 20), 'ROTAS-YAGMUR')
        w = 60 * max(len(yb) - 1, 0) + 80
        self.T('YAĞMUR İNİŞLERİ ZEMİN KOTUNDA SONLANIR', (x - 40, yZ - 70), 12, 'ROTAS-YAGMUR-NO', renk=3)
        # hesap kutusu
        H = M['yagmur_hesap']
        kx, ky = x - 40, yZ - 100
        sat = ['YAĞMUR SUYU BORU ÇAPI HESABI',
               'P = Çatı + balkon alanı = %.1f m²' % H['P'],
               'S = P x 0,75 / 1 = %.1f cm²' % H['S'],
               'f = İniş adedi = %d' % H['f'],
               'A = S / f = %.2f cm²' % H['A'],
               'D = 1,13 x √A = %.2f cm' % H['D'],
               H['sonuc']]
        wk = max(C.yazi_gen(s_, 10) for s_ in sat) + 30
        hk = 18 * len(sat) + 20
        self.L([(kx, ky), (kx + wk, ky), (kx + wk, ky - hk), (kx, ky - hk), (kx, ky)], 'ROTAS-HESAP-CERCEVE')
        for i, s_ in enumerate(sat):
            self.T(s_, (kx + 15, ky - 25 - 18 * i), 10, 'ROTAS-HESAP-YAZI')
        self.xy1 = max(self.xy1, x + w + 400, kx + wk + 100)
