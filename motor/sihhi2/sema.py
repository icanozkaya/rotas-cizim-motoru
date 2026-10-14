#!/usr/bin/env python3
"""sihhi2 — AÇILIMLI KOLON ŞEMASI + RÖGAR ŞEMASI + YAĞMUR ŞEMASI (+ TEMEL PLANI, sema_temel.py)

    python3 motor/sihhi2/sema.py [--model YOL] [--png] [--cikis KLASOR]

Girdi : proje/denemeler/sihhi2/sihhi_model.json (yoksa motor/sihhi2/ornek_model.json)
Çıktı : proje/denemeler/sihhi2/NB_SIHHI_SEMA.dxf, NB_SIHHI_TEMEL.dxf (AC1032, cm), sema_ozet.json

Tarz: kullanıcının new_block şeması (KOLON_SEMASI_TARZI.md §3 formülleri, SIHHI_ALTIN_REFERANS.md §5 ölçüleri):
bant 400, kat yazı sütunları 50, daire yığınları yan yana, armatür aralığı 130, kombi sağ uçta + D balonu,
kolon balonları üstte, T.K. + dirsek + R kolon dibinde, pis su çift çizgili PVC + 45° çatal, toplayıcı döşeme −50,
temiz su dikme / yatay 250 / dağıtım 130, sıcak 5 cm paralel (kombiden), SAYAÇ GRUBU zemin bandının solunda
(5+4 sıra: vana – pislik tutucu – sayaç – çek valf – vana), şebeke girişi, depo sol üstte; kat bandında SAYAÇ YOK;
rögar şeması altta (≈ −600), yağmur şeması sağda + "YAĞMUR SUYU KANALINA GİDER" + hesap kutusu. Ayrıntı: BENIOKU_SEMA.md
"""
import argparse
import json
import math
import os
import sys

import ezdxf
from shapely.geometry import LineString, box

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import sema_ortak as O  # noqa: E402
import sema_sembol as S  # noqa: E402

# ---------------------------------------------------------------- yerleşim sabitleri (new_block şema paftası)
X0, Y0, H = 260820.0, -443249.0, 400.0          # bant iç sol kenarı, zemin bant altı (döşeme), kat bandı
PX0, PY0, PY1 = 260714.0, -444050.0, -441150.0  # pafta
SEMA_PAFTA_MIN_X1 = 268132.0
A_ARM, A_ILK = 130.0, 154.0                      # armatür aralığı, kolon → ilk armatür
Y_UST_S, Y_UST_H, Y_ALT_S, Y_ALT_H = 250.0, 245.0, 130.0, 135.0
D_S, D_H = 24.0, 29.0                            # grup inişi: kolon + 24 (soğuk) / + 29 (sıcak)
Y_TOP = -50.0                                    # pis su toplayıcı
KOMBI_Y = 175.0

KATMAN = {  # ad: (renk, çizgi tipi, kalınlık)
    'ROTAS-SIHHI-SEMA-BANT': (7, 'Continuous', 25), 'ROTAS-SIHHI-SEMA-KAT-ADI': (1, 'Continuous', 25),
    'ROTAS-SIHHI-SOGUK-SU': (5, 'Continuous', 30), 'ROTAS-SIHHI-SICAK-SU': (1, 'ROTAS_BASMA', 30),
    'ROTAS-SIHHI-PIS-SU': (6, 'ROTAS_PISSU', 30), 'ROTAS-SIHHI-YAGMUR': (3, 'Continuous', 30),
    'ROTAS-SIHHI-SEBEKE': (5, 'Continuous', 35), 'ROTAS-SIHHI-PIS-SU-PVC-DETAY': (43, 'Continuous', 13),
    'ROTAS-SIHHI-PIS-SU-CAP': (211, 'Continuous', 18), 'ROTAS-SIHHI-TEMIZ-SU-CAP': (101, 'Continuous', 18),
    'ROTAS-SIHHI-YAGMUR-CAP': (3, 'Continuous', 18), 'ROTAS-SIHHI-KOLON-NO': (6, 'Continuous', 18),
    'ROTAS-SIHHI-YAGMUR-NO': (3, 'Continuous', 18), 'ROTAS-SIHHI-SEMBOL': (1, 'Continuous', 18),
    'ROTAS-SIHHI-SEMA-ARMATUR': (4, 'Continuous', 13), 'ROTAS-SIHHI-CIHAZ-YAZI': (1, 'Continuous', 13),
    'ROTAS-SIHHI-DEPO': (1, 'Continuous', 18), 'ROTAS-SIHHI-DEPO-YAZI': (3, 'Continuous', 13),
    'ROTAS-SIHHI-ROGAR': (5, 'Continuous', 25), 'ROTAS-SIHHI-ROGAR-YAZI': (9, 'Continuous', 9),
    'ROTAS-SIHHI-HESAP': (1, 'Continuous', 20), 'ROTAS-SEMBOL-KILAVUZ': (6, 'Continuous', 9),
    'ROTAS-PAFTA': (144, 'Continuous', 35), 'ROTAS-PAFTA-YAZI': (7, 'Continuous', 25),
    'ROTAS-LEJANT': (7, 'Continuous', 18), 'ROTAS-MIMARI': (8, 'Continuous', 13),
}
L_SOG, L_SIC, L_PIS, L_YAG, L_SEB = ('ROTAS-SIHHI-SOGUK-SU', 'ROTAS-SIHHI-SICAK-SU', 'ROTAS-SIHHI-PIS-SU',
                                     'ROTAS-SIHHI-YAGMUR', 'ROTAS-SIHHI-SEBEKE')
L_PVC, L_PCAP, L_TCAP = 'ROTAS-SIHHI-PIS-SU-PVC-DETAY', 'ROTAS-SIHHI-PIS-SU-CAP', 'ROTAS-SIHHI-TEMIZ-SU-CAP'
L_ARM, L_SEM, L_YAZ = 'ROTAS-SIHHI-SEMA-ARMATUR', 'ROTAS-SIHHI-SEMBOL', 'ROTAS-SIHHI-CIHAZ-YAZI'


def belge():
    doc = ezdxf.new('R2018', setup=False)
    doc.header['$INSUNITS'] = 5
    doc.header['$LTSCALE'] = 1.0
    doc.header['$MEASUREMENT'] = 1
    lts = doc.linetypes
    if 'Continuous' not in lts:
        lts.add('Continuous', pattern=[0.0], description='Solid')
    lts.add('ROTAS_PISSU', pattern=[45.0, 25.0, -6.0, 0.0, -6.0, 2.0, -6.0], description='PIS SU ---- . - ----')
    lts.add('ROTAS_BASMA', pattern=[18.75, 12.5, -6.25], description='SICAK SU - - - -')
    for ad, (renk, lt, lw) in KATMAN.items():
        doc.layers.add(ad, color=renk, linetype=lt, lineweight=lw)
    if S.YAZI_STIL not in doc.styles:
        doc.styles.add(S.YAZI_STIL, font='arial.ttf')
    S.bloklar(doc)
    return doc


class Ciz:
    def __init__(self, msp):
        self.msp = msp
        self.n = 0

    def hat(self, pts, katman, lt=None, renk=None):
        pts = [(float(x), float(y)) for x, y in pts]
        a = {'layer': katman}
        if lt:
            a['linetype'] = lt
        if renk is not None:
            a['color'] = renk
        self.n += 1
        if len(pts) == 2:
            return self.msp.add_line(pts[0], pts[1], dxfattribs=a)
        return self.msp.add_lwpolyline(pts, dxfattribs=a)

    def parcali(self, p0, p1, kirik, katman, **kw):
        """p0→p1 doğrusunu kırık noktalarında (iniş / branşman ağızları) ayrı boru parçalarına böl"""
        ex = abs(p1[0] - p0[0]) >= abs(p1[1] - p0[1])
        a, b = (p0[0], p1[0]) if ex else (p0[1], p1[1])
        lo, hi = min(a, b), max(a, b)
        ks = sorted({round(k, 3) for k in kirik if lo + 0.5 < k < hi - 0.5} | {lo, hi})
        for u, v in zip(ks[:-1], ks[1:]):
            if ex:
                self.hat([(u, p0[1]), (v, p0[1])], katman, **kw)
            else:
                self.hat([(p0[0], u), (p0[0], v)], katman, **kw)

    def yazi(self, s, p, h, katman, renk=None, rot=0.0, hiza=None):
        a = {'layer': katman, 'height': h, 'style': S.YAZI_STIL, 'rotation': rot, 'width': S.YAZI_EN}
        if renk is not None:
            a['color'] = renk
        t = self.msp.add_text(s, dxfattribs=a)
        if hiza:
            t.set_placement(p, align=hiza)
        else:
            t.dxf.insert = p
        return t

    def blok(self, ad, p, katman, attr=None, rot=0.0, olcek=1.0):
        return S.ekle(self.msp, ad, p, katman, rot=rot, attr=attr, olcek=olcek)

    def pvc(self, pts, w, halka=True, muf_son=True):
        """PVC görünümü (kullanıcının PVC BORU / ÇATAL blokları): eksenin iki yanında dış hat (kahverengi 43) +
        her parçanın başında MUF (boru dış hattından 2 cm geniş, 8 cm boy, iki uç halkası); uzun parçada uçta da muf"""
        ls = LineString(pts)
        for s in (1, -1):
            o = ls.offset_curve(s * w, join_style=2, mitre_limit=3.0)
            if o.is_empty:
                continue
            gs = getattr(o, 'geoms', [o])
            for g in gs:
                self.hat(list(g.coords), L_PVC)
        if not halka:
            return
        n = len(pts) - 1
        for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 24:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            nx, ny = -uy, ux
            uclar = [2.0]
            if L >= 60 and (muf_son or i < n - 1):
                uclar.append(L - 10.0)
            W = w + 2.0
            for t in uclar:
                p0 = (a[0] + ux * t, a[1] + uy * t)
                p1 = (a[0] + ux * (t + 8), a[1] + uy * (t + 8))
                kose = [(p0[0] + nx * W, p0[1] + ny * W), (p1[0] + nx * W, p1[1] + ny * W),
                        (p1[0] - nx * W, p1[1] - ny * W), (p0[0] - nx * W, p0[1] - ny * W)]
                self.hat(kose + [kose[0]], L_PVC)


# ====================================================================== YERLEŞİM
# kullanıcının new_block şemasındaki kolon x'leri ve daire dikmeleri (SIHHI_ALTIN_REFERANS §5.2); bant 260820…267449
REF_KOLON_X = {'P9': 261562.6, 'P8': 262184.6, 'P7': 262914.1, 'P6': 263522.2, 'P5': 264272.5, 'P4': 264659.0,
               'P3': 265253.6, 'P2': 266548.1, 'P1': 266934.6}
REF_DIKME = {'P9': 261524.9, 'P6': 263480.3, 'P3': 265211.6}     # yığının ilk kolonu → daire dikmesi x
REF_X1 = 267449.0
BOS_MIN = 50.0                                   # grup son armatürü → sonraki kolon en az


def _grup_uc(Y, p):
    nmax = max((len(g.tipler) for (k, q), g in Y.gruplar.items() if q == p), default=1)
    return A_ILK + A_ARM * (nmax - 1)


def _ref_yerlesim(ys):
    """model kullanıcının kolonlarıyla (P1…P9, aynı yığın sırası) aynıysa kullanıcının x'leri. Bir grup kullanıcınınkinden
    uzunsa (ör. ek armatür) yalnız sağındaki kolonlar gerektiği kadar kayar; aksi hâlde None (formül yerleşimi)."""
    sira = [p for Y in ys for p in Y.kolonlar]
    if sira != sorted(REF_KOLON_X, key=REF_KOLON_X.get):
        return None
    if [Y.kolonlar[0] for Y in ys] != sorted(REF_DIKME, key=REF_DIKME.get):
        return None
    L = {'yigin': [], 'kolon_x': {}}
    kay = 0.0                                   # birikmiş sağa kayma
    for Y in ys:
        dik = REF_DIKME[Y.kolonlar[0]] + kay
        if L['yigin']:
            kay = max(kay, L['yigin'][-1]['son'] + 50.0 - REF_DIKME[Y.kolonlar[0]])
            dik = REF_DIKME[Y.kolonlar[0]] + kay
        d = {'Y': Y, 'dikme': dik}
        onceki = None
        for p in Y.kolonlar:
            x = REF_KOLON_X[p] + kay
            if onceki is not None:
                gerek = L['kolon_x'][onceki] + _grup_uc(Y, onceki) + BOS_MIN
                if gerek > x:
                    kay += gerek - x
                    x = gerek
            L['kolon_x'][p] = x
            onceki = p
        son = Y.kolonlar[-1]
        d['kombi'] = L['kolon_x'][son] + max(_grup_uc(Y, son) + A_ARM, 300.0)
        d['son'] = d['kombi'] + 75.0
        L['yigin'].append(d)
    L['x1'] = max(REF_X1 + kay, L['yigin'][-1]['son'] + 25.0)
    L['ref'] = True
    L['kayma'] = round(kay, 1)
    return L


def yerlesim(m, ys):
    """yığın ve kolon x'leri; dönüş dict. Kolonlar kullanıcının şemasındakilerle aynıysa onun x'leri (bant 6629)."""
    n_d = len(m['daireler'])
    nk = max(1, math.ceil(n_d / 5.0))
    R = _ref_yerlesim(ys)
    if R:
        R['nk'] = nk
        return R
    sayac_son = X0 + 173 + 161 * (nk - 1) + 148
    x = max(X0 + 705.0, sayac_son + 230.0)
    L = {'yigin': [], 'kolon_x': {}, 'nk': nk, 'ref': False}
    for Y in ys:
        d = {'Y': Y, 'dikme': x}
        kx = x + 38.0
        for i, p in enumerate(Y.kolonlar):
            L['kolon_x'][p] = kx
            ext = _grup_uc(Y, p)
            if i == len(Y.kolonlar) - 1:
                d['kombi'] = kx + max(ext + A_ARM, 300.0)
            else:
                kx = kx + ext + 175.0
        d['son'] = d['kombi'] + 75.0
        L['yigin'].append(d)
        x = d['son'] + 65.0
    L['x1'] = L['yigin'][-1]['son'] + 25.0 if L['yigin'] else X0 + 2000
    return L


# ====================================================================== ŞEMA ÇİZİMİ
def cerceve(C, m, L):
    n = O.kat_sayisi(m)
    x1 = L['x1']
    yt = Y0 + n * H
    # kat çizgileri yağmur şeması bölmesinin sağ ucuna kadar sürer (new_block: 267499…268070, 571 cm)
    nyb = len(m.get('yagmur', []))
    xr = max(x1 + 621.0, x1 + 86 + 60 * (nyb - 1) + 76) if nyb else x1 + 50
    L['x_bolme'] = xr
    for k in range(n + 1):
        C.hat([(X0 - 50, Y0 + k * H), (xr, Y0 + k * H)], 'ROTAS-SIHHI-SEMA-BANT')
    for x in sorted({X0 - 50, X0, x1, x1 + 50, xr}):
        C.hat([(x, Y0), (x, yt)], 'ROTAS-SIHHI-SEMA-BANT')
    adlar = m['proje'].get('kat_adlari') or ['ZEMİN KAT']
    for k in range(n):
        for xx in (X0 - 12.5, x1 + 37.5):
            C.yazi(adlar[k], (xx, Y0 + k * H + 52), 25.0, 'ROTAS-SIHHI-SEMA-KAT-ADI', renk=1, rot=90.0)
    return yt


def sebeke_sayac_depo(C, m, L, yt):
    """zemin bandı solu: şebeke girişi, 5+4 sayaç grubu, çatıda depo ve iki dikme (new_block 5.3–5.4)"""
    n_d = len(m['daireler'])
    ys = Y0 + 15.0
    C.yazi('Şebekeden', (X0 + 12, Y0 - 38), 16.6, L_YAZ, renk=15)
    C.hat([(X0 + 18, Y0 - 12), (X0 + 18, ys), (X0 + 125, ys)], L_SEB)
    for dx, ad in ((36, 'KURESEL-VANA'), (62, 'PISLIK-TUTUCU'), (87, 'CEKVALF'), (112, 'KURESEL-VANA')):
        C.blok('ROTAS-SEMA-' + ad, (X0 + dx, ys), L_SEM)
    # depo dolum dikmesi (şebeke → depo), depo dönüş dikmesi (depo → sayaç grubu), arada by-pass çek valf
    xk1 = X0 + 173.0
    kol_x = [X0 + 173.0 + 161.0 * j for j in range(L['nk'])]
    C.parcali((X0 + 125, ys), (kol_x[-1], ys), [X0 + 158] + kol_x, L_SEB)
    C.blok('ROTAS-SEMA-CEKVALF', (X0 + 141, ys), L_SEM)
    # depo (çatı, üst bant üstünde, sol)
    dx0, dx1, dy0 = X0 + 285.0, X0 + 485.0, yt + 30.0
    dy1 = dy0 + 200.0
    C.hat([(X0 + 125, ys), (X0 + 125, dy1 + 62), (X0 + 437, dy1 + 62), (X0 + 437, dy1)], L_SEB)
    C.blok('ROTAS-SEMA-KURESEL-VANA', (X0 + 437, dy1 + 32), L_SEM, rot=90)
    # depo çıkışı: alt sağ flanştan kaide içinden aşağı, sağa (vana + pislik tutucu), dağıtım dikmesine
    C.hat([(dx1 - 45, dy0 + 22), (dx1 - 45, yt + 13), (X0 + 585, yt + 13), (X0 + 585, yt - 33), (X0 + 158, yt - 33),
           (X0 + 158, ys)], L_SEB)
    C.msp.add_circle((dx1 - 45, dy0 + 30), 8.0, dxfattribs={'layer': 'ROTAS-SIHHI-DEPO'})
    C.msp.add_circle((dx1 - 45, dy0 + 30), 4.0, dxfattribs={'layer': 'ROTAS-SIHHI-DEPO'})
    C.blok('ROTAS-SEMA-KURESEL-VANA', (X0 + 526, yt + 13), L_SEM)
    C.blok('ROTAS-SEMA-PISLIK-TUTUCU', (X0 + 551, yt + 13), L_SEM)
    depo = 'ROTAS-SIHHI-DEPO'
    C.hat([(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1), (dx0, dy0)], depo)
    C.hat([(dx0 - 8, yt), (dx1 + 7, yt), (dx1 + 7, yt + 30), (dx0 - 8, yt + 30), (dx0 - 8, yt)], depo, renk=5)
    kb = box(dx0 - 8, yt, dx1 + 7, yt + 30)      # betonarme kaide taraması (45°, 10 cm)
    for c in range(int(dx0 - 8 - 30), int(dx1 + 7), 10):
        g = LineString([(c, yt), (c + 40, yt + 40)]).intersection(kb)
        if g.length > 1:
            C.hat(list(g.coords), depo, renk=5)
    C.hat([(dx0 + 60, dy1), (dx0 + 60, dy1 + 6), (dx0 + 160, dy1 + 6), (dx0 + 160, dy1)], depo)     # menhol
    # dolum girişi: üstte flanş + şamandıralı (flatörlü) vana
    xd = X0 + 437
    C.hat([(xd - 7, dy1 + 2), (xd + 7, dy1 + 2), (xd + 7, dy1 + 6), (xd - 7, dy1 + 6), (xd - 7, dy1 + 2)], depo)
    C.hat([(xd, dy1), (xd, dy1 - 18)], depo)
    C.hat([(xd - 5, dy1 - 18), (xd + 5, dy1 - 18), (xd + 5, dy1 - 26), (xd - 5, dy1 - 26), (xd - 5, dy1 - 18)], depo)
    C.hat([(xd, dy1 - 22), (xd - 30, dy1 - 34)], depo)                       # şamandıra kolu
    C.msp.add_circle((xd - 37, dy1 - 37), 7.0, dxfattribs={'layer': depo})  # şamandıra topu
    C.hat([(xd - 60, dy1 - 40), (xd + 20, dy1 - 40)], depo, lt='ROTAS_BASMA', renk=4)   # su seviyesi
    # havalık + taşma (2"): kaz boynu havalık, taşma depo yan duvarına FLANŞLA girer (içeri uzanmaz)
    xh = dx0 - 70
    yta = dy1 - 45
    C.hat([(dx0, yta), (xh, yta)], depo)
    for fx in (dx0 - 3, dx0 - 8):                                            # flanş çifti
        C.hat([(fx, yta - 7), (fx, yta + 7)], depo)
    C.hat([(xh, dy0 - 15), (xh, dy1 + 25)], depo)
    C.msp.add_arc((xh - 7, dy1 + 25), 7.0, 0, 180, dxfattribs={'layer': depo})
    C.hat([(xh - 14, dy1 + 25), (xh - 14, dy1 + 18)], depo)
    C.yazi('2"', (xh - 6, dy0 + 90), 11.0, 'ROTAS-SIHHI-DEPO-YAZI', hiza=ezdxf.enums.TextEntityAlignment.BOTTOM_RIGHT)
    # boşaltma: DEPO TABANINDAN (flanşlı), kaide içinden sola, vana, taşma birleşimi, huni
    xb = dx0 + 25
    C.hat([(xb - 7, dy0 - 2), (xb + 7, dy0 - 2)], depo)
    C.hat([(xb, dy0), (xb, dy0 - 15), (dx0 - 115, dy0 - 15), (dx0 - 115, dy0 - 32)], depo)
    C.hat([(dx0 - 121, dy0 - 32), (dx0 - 115, dy0 - 40), (dx0 - 109, dy0 - 32)], depo)       # huni
    C.blok('ROTAS-SEMA-KURESEL-VANA', (dx0 - 35, dy0 - 15), depo)
    # seviye göstergesi (flanşlı, iki ağız)
    C.hat([(dx1 + 14, dy0 + 20), (dx1 + 14, dy1 - 20)], depo, lt='ROTAS_BASMA', renk=4)
    for yy_ in (dy0 + 20, dy1 - 20):
        C.hat([(dx1, yy_), (dx1 + 14, yy_)], depo)
        C.hat([(dx1 + 3, yy_ - 5), (dx1 + 3, yy_ + 5)], depo)
    v = m['proje'].get('depo', {}).get('hacim_m3', 3.0)
    C.yazi('KULLANIM SU DEPOSU', ((dx0 + dx1) / 2, dy0 + 112), 15.0, 'ROTAS-SIHHI-DEPO-YAZI',
           hiza=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    C.yazi('V=%sm3' % O.fmt(v), ((dx0 + dx1) / 2, dy0 + 90), 15.0, 'ROTAS-SIHHI-DEPO-YAZI',
           hiza=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    R = ezdxf.enums.TextEntityAlignment.BOTTOM_RIGHT
    C.yazi('Havalık', (xh - 22, dy1 - 10), 13.0, 'ROTAS-SIHHI-DEPO-YAZI', hiza=R)
    C.yazi('Taşma', (xh - 22, yta + 4), 13.0, 'ROTAS-SIHHI-DEPO-YAZI', hiza=R)
    C.yazi('Boşaltma', (X0 + 132, dy0 + 6), 13.0, 'ROTAS-SIHHI-DEPO-YAZI')
    C.yazi('Su Seviye', (dx1 + 22, dy0 + 120), 13.0, 'ROTAS-SIHHI-DEPO-YAZI')
    C.yazi('Göstergesi', (dx1 + 22, dy0 + 103), 13.0, 'ROTAS-SIHHI-DEPO-YAZI')
    # akış okları: şebeke girişinde →, her katta dolum ↑, dağıtım ↓
    C.blok('ROTAS-SEMA-AKIS-OKU', (X0 + 30, Y0 - 12), L_SEM, rot=-90)
    for k in range(O.kat_sayisi(m)):
        yy = Y0 + k * H + (200 if k else 260)
        C.blok('ROTAS-SEMA-AKIS-OKU', (X0 + 112, yy), L_SEM)
        C.blok('ROTAS-SEMA-AKIS-OKU', (X0 + 171, yy), L_SEM, rot=180)
    # SAYAÇ GRUBU: kollektör j, sıra i; sıra: vana(27) pislik(52) sayaç(74) çek valf(96) vana(121), uç 148
    kalan = n_d
    for j, xc in enumerate(kol_x):
        n_s = min(5, kalan)
        kalan -= n_s
        if n_s <= 0:
            break
        yy = [Y0 + 32 + 20 * i for i in range(n_s)]
        if j == 0 and L['nk'] > 1:
            yy = [Y0 + 32 + 20 * i for i in range(n_s)]
        C.parcali((xc, ys), (xc, max(yy)), yy, L_SEB)
        for y in yy:
            C.hat([(xc, y), (xc + 148, y)], L_SEB)
            C.hat([(xc + 148, y - 5), (xc + 148, y + 5)], L_SEB)
            for dx, ad in ((27, 'KURESEL-VANA'), (52, 'PISLIK-TUTUCU'), (74, 'SU-SAYACI'), (96, 'CEKVALF'),
                           (121, 'KURESEL-VANA')):
                C.blok('ROTAS-SEMA-' + ad, (xc + dx, y), L_SEM)


def grup_ciz(C, g, xk, y0, kombi_x=None, sicak_disari=0.0, sicak_yukari=False):
    """bir ıslak hacim grubu: armatürler, branşmanlar, 130 / 135 dağıtım, pis su toplayıcı + etiketler.
    kombi_x: bu grup kombi grubuysa kombi ekseni (soğuk kombiye uzar, sıcak kombiden başlar).
    sicak_disari: kombi grubunda +135 hattından gruba dışarıdan giden (diğer grupların) sıcak yük."""
    T = g.tipler
    xa = [xk + A_ILK + A_ARM * i for i in range(len(T))]
    ts, th = [], []          # soğuk / sıcak ağız x'leri
    for t, x in zip(T, xa):
        C.blok(S.ARM_BLOK[t], (x, y0), L_ARM)
        b = S.BAG.get(t, (None, None))
        if b[0]:
            C.hat([(x + b[0][0], y0 + Y_ALT_H), (x + b[0][0], y0 + b[0][1])], L_SIC)
            th.append(x + b[0][0])
        if b[1]:
            C.hat([(x + b[1][0], y0 + Y_ALT_S), (x + b[1][0], y0 + b[1][1])], L_SOG)
            ts.append(x + b[1][0])
        # armatür bağlantı etiketi (Ø / MB)
        ms, mh = O.MB_S.get(t, 0), O.MB_H.get(t, 0)
        cap = O.BAG_CAP.get(t, 'Ø20')
        if t == 'YS':
            continue
        yl = {'LV': 28, 'DUS': 40, 'EV': 96, 'WC': 46, 'CM': 40, 'BM': 40}[t]
        if b[0]:      # iki hatlı: sıcak solda, soğuk sağda
            C.blok('ROTAS-SEMA-ET2-SOL', (x - 14, y0 + yl), L_TCAP, attr={'CAP': cap, 'DEGER': O.fmt(mh) + ' MB'})
            C.blok('ROTAS-SEMA-ET2-SAG', (x + (22 if t == 'EV' else 14), y0 + yl), L_TCAP,
                   attr={'CAP': cap, 'DEGER': O.fmt(ms) + ' MB'})
        else:         # tek hatlı (klozet, ÇM, BM): kullanıcıda etiket armatürün SOLUNDA
            xl = x - (14 if t == 'WC' else S.YARI[t] + 4)
            C.blok('ROTAS-SEMA-ET2-SOL', (xl, y0 + yl), L_TCAP, attr={'CAP': cap, 'DEGER': O.fmt(ms) + ' MB'})
    xs0, xh0 = xk + D_S, xk + D_H
    # soğuk 130 hattı
    son_s = (kombi_x + 5) if kombi_x else (max(ts) if ts else None)
    if son_s:
        C.parcali((xs0, y0 + Y_ALT_S), (son_s, y0 + Y_ALT_S), ts, L_SOG)
    if kombi_x:
        C.hat([(kombi_x + 5, y0 + Y_ALT_S), (kombi_x + 5, y0 + KOMBI_Y - 4)], L_SOG)
    # sıcak 135 hattı
    if kombi_x:
        C.hat([(kombi_x - 5, y0 + KOMBI_Y - 4), (kombi_x - 5, y0 + Y_ALT_H)], L_SIC)
        x_sol = xh0 if sicak_yukari else (min(th) if th else kombi_x - 5)
        if x_sol < kombi_x - 5.5:
            C.parcali((x_sol, y0 + Y_ALT_H), (kombi_x - 5, y0 + Y_ALT_H), th, L_SIC)
        if sicak_yukari:
            C.hat([(xh0, y0 + Y_ALT_H), (xh0, y0 + Y_UST_H)], L_SIC)
    elif th:
        C.parcali((xh0, y0 + Y_ALT_H), (max(th), y0 + Y_ALT_H), th, L_SIC)
    # temiz su hat etiketleri (her parça bir etiket, armatürün 80 solunda, kanca yukarı)
    for i, (t, x) in enumerate(zip(T, xa)):
        if t == 'YS':
            continue
        s_ = sum(O.MB_S.get(u, 0) for u in T[i:]) + (O.MB_S['KOMBI'] if kombi_x else 0)
        if kombi_x:   # sıcak kombiden sola akar: bu parçadan soldaki armatürler + diğer gruplar
            h_ = sum(O.MB_H.get(u, 0) for u in T[:i]) + sicak_disari
        else:
            h_ = sum(O.MB_H.get(u, 0) for u in T[i:])
        mb_et(C, (x - 80, y0 + Y_ALT_S), s_, h_)
    # pis su: inişler + toplayıcı + PVC + etiketler
    yt = y0 + Y_TOP
    kir = []
    for i, (t, x) in enumerate(zip(T, xa)):
        sb = O.SB.get(t, 0)
        wc = t == 'WC'
        w = 4.0 if wc else 3.0
        p = [(x, y0), (x, y0 - 35), (x - 15, yt)]
        C.hat(p, L_PIS, lt='Continuous')
        C.pvc(p, w)
        kir.append(x - 15)
        C.blok('ROTAS-SEMA-ET2-SAG', (x + 9, y0 - 40), L_PCAP, olcek=1.5,
               attr={'CAP': O.pis_cap(sb, wc), 'DEGER': '%d SB' % sb})
        top = sum(O.SB.get(u, 0) for u in T[i:])
        C.blok('ROTAS-SEMA-ET-SB', (x - 80, yt), L_PCAP,
               attr={'CAP': O.pis_cap(top, 'WC' in T[i:]), 'SB': '%d SB' % top})
    if kir:
        C.hat([(xk, yt - 20), (xk + 20, yt)], L_PIS, lt='Continuous')
        C.parcali((xk + 20, yt), (max(kir), yt), kir, L_PIS, lt='Continuous')
        C.pvc([(xk, yt - 20), (xk + 20, yt), (max(kir), yt)], 4.0)
    return xa


def mb_et(C, p, s_, h_):
    if s_ > 0 and h_ > 0:
        C.blok('ROTAS-SEMA-ET-MB4', p, L_TCAP, attr={'C1': O.inc(s_), 'M1': O.fmt(s_) + ' MB',
                                                     'C2': O.inc(h_), 'M2': O.fmt(h_) + ' MB'})
    elif s_ > 0 or h_ > 0:
        v = s_ if s_ > 0 else h_
        C.blok('ROTAS-SEMA-ET-MB2', p, L_TCAP, attr={'C1': O.inc(v), 'M1': O.fmt(v) + ' MB'})


def yigin_kat_ciz(C, m, L, d, k, ozet):
    Y = d['Y']
    dno = Y.daire.get(k)
    if not dno:
        return
    y0 = Y0 + k * H
    KX = L['kolon_x']
    gs = [Y.gruplar[(k, p)] for p in Y.kolonlar if (k, p) in Y.gruplar]
    if not gs:
        return
    kombi = d['kombi']
    kg = [g for g in gs if g.mutfak]
    kg = kg[-1] if kg else gs[-1]
    sicakli = [g for g in gs if g.mb_h() > 0 or g is kg]
    # kombi
    C.blok('ROTAS-SEMA-KOMBI', (kombi, y0 + KOMBI_Y), L_ARM)
    for i, s in enumerate(('DUVARA ASILABİLEN', 'HERMETİK KOMBİ', 'KAPASİTE: 24 kW')):
        C.yazi(s, (kombi, y0 + KOMBI_Y + 86 - 8 * i), 5.5, L_YAZ, renk=1,
               hiza=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    C.blok('ROTAS-SEMA-ET2-SAG', (kombi + 25, y0 + KOMBI_Y + 6), L_TCAP, attr={'CAP': 'Ø20', 'DEGER': '0.5 MB'})
    C.blok('ROTAS-SEMA-DAIRE-NO', (kombi - 197, y0 + 268), 'ROTAS-SIHHI-KOLON-NO', attr={'NO': dno})
    # daire besleme dikmesi + 250 / 245 hatları
    toplam_s = sum(g.mb_s() for g in gs) + O.MB_S['KOMBI']
    toplam_h = sum(g.mb_h() for g in gs)
    xr = d['dikme']
    C.hat([(xr, y0), (xr, y0 + Y_UST_S)], L_SOG)
    C.blok('ROTAS-SEMA-ET-DIKME', (xr, y0 + 125), L_TCAP, attr={'CAP': O.inc(toplam_s), 'MB': O.fmt(toplam_s) + ' MB'})
    inis_s = [KX[g.kolon] + D_S for g in gs]
    C.parcali((xr, y0 + Y_UST_S), (KX[kg.kolon] + D_S, y0 + Y_UST_S), inis_s, L_SOG)
    inis_h = sorted(KX[g.kolon] + D_H for g in sicakli)
    if len(inis_h) > 1:
        C.parcali((inis_h[0], y0 + Y_UST_H), (inis_h[-1], y0 + Y_UST_H), inis_h, L_SIC)
    # üst hat etiketleri: iki iniş arası parça başına
    for j, g in enumerate(gs[:-1]):
        sag = gs[j + 1:]
        s_ = sum(q.mb_s() for q in sag) + O.MB_S['KOMBI']
        h_ = sum(q.mb_h() for q in gs[:j + 1]) if inis_h and inis_h[0] <= KX[g.kolon] + D_H else 0.0
        mb_et(C, (KX[g.kolon] + D_S + 60, y0 + Y_UST_S), s_, h_)
    # gruplar
    for g in gs:
        xk = KX[g.kolon]
        C.hat([(xk + D_S, y0 + Y_UST_S), (xk + D_S, y0 + Y_ALT_S)], L_SOG)
        if g is kg:
            disari = sum(q.mb_h() for q in gs if q is not kg)
            grup_ciz(C, g, xk, y0, kombi_x=kombi, sicak_disari=disari, sicak_yukari=len(inis_h) > 1)
        else:
            if g in sicakli:
                C.hat([(xk + D_H, y0 + Y_UST_H), (xk + D_H, y0 + Y_ALT_H)], L_SIC)
            grup_ciz(C, g, xk, y0)
    ozet['daireler'][dno] = {'kat': k, 'soguk_mb': round(toplam_s, 2), 'sicak_mb': round(toplam_h, 2),
                             'cap': O.inc(toplam_s), 'gruplar': {g.kolon: g.tipler for g in gs}}


def kolonlar_ciz(C, m, L, ys, yt, ozet):
    n = O.kat_sayisi(m)
    KX = L['kolon_x']
    for Y in ys:
        for p in Y.kolonlar:
            xk = KX[p]
            sbk = [Y.gruplar[(k, p)].sb() if (k, p) in Y.gruplar else 0 for k in range(n)]
            wck = [Y.gruplar[(k, p)].wc() if (k, p) in Y.gruplar else False for k in range(n)]
            # dip: dirsek + R
            dip = [(xk + 30, Y0 - 98), (xk + 10, Y0 - 98), (xk, Y0 - 88), (xk, Y0 - 70)]
            C.hat(dip, L_PIS, lt='Continuous')
            C.pvc(dip, 5.0)
            C.blok('ROTAS-SEMA-ROGAR-OK', (xk + 32, Y0 - 98), 'ROTAS-SIHHI-ROGAR')
            C.yazi('R', (xk + 72, Y0 - 110), 25.0, 'ROTAS-SIHHI-ROGAR-YAZI', renk=5)
            for k in range(n):
                ya = Y0 + k * H - 70
                yb = (Y0 + (k + 1) * H - 70) if k < n - 1 else yt + 45.5   # kolon balonun altına değer
                C.hat([(xk, ya), (xk, yb)], L_PIS, lt='Continuous')
                C.pvc([(xk, ya), (xk, yb)], 5.0, muf_son=k < n - 1)
                kum = sum(sbk[k:])
                if sbk[k] > 0 or k == 0:
                    C.blok('ROTAS-SEMA-ET2-SOL', (xk - 14, Y0 + k * H - 112), L_PCAP, olcek=1.5,
                           attr={'CAP': O.pis_cap(kum, any(wck[k:])), 'DEGER': '%d SB' % kum})
            C.blok('ROTAS-SEMA-TEMIZLEME-KAPAGI', (xk, Y0 + 24), L_SEM)
            C.yazi('T.K.', (xk - 13, Y0 + 19), 10.0, L_YAZ, renk=1, hiza=ezdxf.enums.TextEntityAlignment.BOTTOM_RIGHT)
            C.blok('ROTAS-SEMA-HAVALIK', (xk, yt + 28), 'ROTAS-SIHHI-PIS-SU-PVC-DETAY')
            C.blok('ROTAS-SEMA-KOLON-NO', (xk, yt + 73), 'ROTAS-SIHHI-KOLON-NO', attr={'NO': p})
            ozet['kolonlar'][p] = {'x_sema': round(xk, 1), 'sb_kat': sbk, 'sb_toplam': sum(sbk),
                                   'cap': O.pis_cap(sum(sbk), any(wck))}


def yagmur_ciz(C, m, L, yt):
    x1 = L['x1']
    yb = sorted(m.get('yagmur', []), key=lambda r: O.kno(r['no']))
    n = O.kat_sayisi(m)
    xs = []
    for i, r in enumerate(yb):
        x = x1 + 86 + 60 * i
        xs.append(x)
        C.hat([(x, Y0 - 20), (x, yt + 10)], L_YAG)
        C.blok('ROTAS-SEMA-KOLON-NO-YAGMUR', (x, yt + 37.5), 'ROTAS-SIHHI-YAGMUR-NO', attr={'NO': r['no']})
        C.blok('ROTAS-SEMA-DESARJ-OK', (x, Y0 - 20), 'ROTAS-SIHHI-ROGAR')
        for k in range(n):
            yy = Y0 + k * H + 170
            C.hat([(x, yy), (x + 8, yy)], 'ROTAS-SIHHI-YAGMUR-CAP')
            C.yazi(r.get('cap', 'Ø70'), (x + 10, yy - 4), 9.0, 'ROTAS-SIHHI-YAGMUR-CAP')
    if not xs:
        return
    gx1 = max(x1 + 585, xs[-1] + 40)
    C.hat([(x1 + 36, Y0 - 58), (gx1, Y0 - 58), (gx1, Y0 - 124), (x1 + 36, Y0 - 124), (x1 + 36, Y0 - 58)],
          'ROTAS-SIHHI-HESAP')
    C.yazi('YAĞMUR SUYU KANALINA GİDER', ((x1 + 36 + gx1) / 2, Y0 - 91), 20.0, L_YAZ, renk=3,
           hiza=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    return gx1


def yagmur_hesap(C, m, L, ek):
    """kırmızı çerçeveli hesap kutusu 500x280 (new_block 5.6); alan temel planındaki bina dış hattından"""
    x1 = L['x1']
    bx0, by1 = x1 + 68, Y0 - 161
    bx1, by0 = bx0 + 500, by1 - 280
    C.hat([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)], 'ROTAS-SIHHI-HESAP')
    n = max(1, len(m.get('yagmur', [])))
    A = ek.get('cati_alani_m2') or 0.0
    a1 = A / n
    r = 0.03            # l/s·m² (300 l/s·ha)
    Q = a1 * r * 1.0
    d = 66.0            # Ø70 PVC iç çapı, mm
    qmax = 2.5e-4 * (0.25 ** (-1 / 6.0)) * (0.33 ** (5 / 3.0)) * d ** (8 / 3.0)
    satir = ['YAĞMUR SUYU BORU ÇAPI HESABI',
             'Çatı alanı (yatay izdüşüm)  A = %.0f m²' % A,
             'İniş sayısı  n = %d  ->  iniş başına  A1 = %.1f m²' % (n, a1),
             'Yağış şiddeti  r = 0,03 l/s.m² (300 l/s.ha),  C = 1,0',
             'Debi  Q = A1 x r x C = %.2f l/s' % Q,
             'Ø70 iniş kapasitesi (TS EN 12056-3, Wyly-Eaton,',
             '  doluluk f = 0,33, k = 0,25 mm, di = 66 mm)  Qmax = %.2f l/s' % qmax,
             'Q = %.2f l/s  <  Qmax = %.2f l/s' % (Q, qmax),
             'Ø70 lik Boru %s.' % ('UYGUNDUR' if Q < qmax else 'YETMEZ, Ø100 SEÇİLİR')]
    for i, s in enumerate(satir):
        C.yazi(s, (bx0 + 18, by1 - 34 - 27 * i), 12.0 if i == 0 else 10.5, 'ROTAS-SIHHI-HESAP', renk=1 if i == 0 else 7)


def rogar_semasi(C, m, L, rogarlar):
    """altta R1 → R2 → ... → PB; üstlerinde bağlanan kolon balonları (2'li sıra), aralık 239"""
    if not rogarlar:
        return
    A = 239.0
    nR = len(rogarlar)
    xm = (X0 + L['x1']) / 2
    xr0 = xm - A * (nR - 1) / 2
    yr = Y0 - 600.0
    C_ = ezdxf.enums.TextEntityAlignment
    for i, r in enumerate(rogarlar):
        x = xr0 + A * i
        C.blok('ROTAS-SEMA-ROGAR', (x, yr), 'ROTAS-SIHHI-ROGAR', attr={'NO': r['no']})
        C.yazi(r.get('olcu_1', '70x70'), (x + 175, yr - 44), 9.6, 'ROTAS-SIHHI-ROGAR-YAZI', renk=9, hiza=C_.BOTTOM_RIGHT)
        C.yazi(r.get('olcu_2', 'h:-70cm'), (x + 175, yr - 58), 9.6, 'ROTAS-SIHHI-ROGAR-YAZI', renk=9, hiza=C_.BOTTOM_RIGHT)
        if i < nR - 1:
            C.hat([(x + 44.5, yr), (x + A - 44.5, yr)], L_PIS, lt='Continuous')
            xm_ = x + A / 2
            C.yazi('%1 EĞİM', (xm_ - 6, yr + 34), 18.0, L_PCAP, renk=2, hiza=C_.BOTTOM_CENTER)
            C.yazi(r.get('cap_cikis', 'Ø150'), (xm_ - 6, yr + 6), 18.0, L_PCAP, renk=2, hiza=C_.BOTTOM_CENTER)
            C.blok('ROTAS-SEMA-EGIM-OKU', (xm_ + 64, yr + 43), L_SEM)
        ks = r.get('kolonlar', [])
        if ks:
            C.hat([(x, yr + 32), (x, yr + 82)], 'ROTAS-SEMBOL-KILAVUZ')
            for j, p in enumerate(ks):
                C.blok('ROTAS-SEMA-KOLON-NO', (x + 55 * (j % 2), yr + 109.5 + 55 * (j // 2)), 'ROTAS-SIHHI-KOLON-NO',
                       attr={'NO': p})


def pafta(C, x_son):
    px1 = max(SEMA_PAFTA_MIN_X1, x_son + 80)
    C.hat([(PX0, PY0), (px1, PY0), (px1, PY1), (PX0, PY1), (PX0, PY0)], 'ROTAS-PAFTA')
    return px1     # kullanıcının şema paftasında başlık ve lejant yok (lejant detay paftasında)


def sema_uret(m, rogarlar, ek, cikis):
    ys = O.yiginlar(m)
    L = yerlesim(m, ys)
    doc = belge()
    msp = doc.modelspace()
    C = Ciz(msp)
    yt = cerceve(C, m, L)
    ozet = {'model': m['_yol'], 'daireler': {}, 'kolonlar': {}, 'yiginlar': [], 'rogarlar': rogarlar}
    sebeke_sayac_depo(C, m, L, yt)
    for d in L['yigin']:
        ozet['yiginlar'].append({'daireler': d['Y'].daire, 'kolonlar': d['Y'].kolonlar, 'dikme_x': d['dikme'],
                                 'kombi_x': d['kombi']})
        for k in range(O.kat_sayisi(m)):
            yigin_kat_ciz(C, m, L, d, k, ozet)
    kolonlar_ciz(C, m, L, ys, yt, ozet)
    gx1 = yagmur_ciz(C, m, L, yt) or L['x1']
    yagmur_hesap(C, m, L, ek)
    rogar_semasi(C, m, L, rogarlar)
    px1 = pafta(C, max(gx1, L.get('x_bolme', gx1) - 20))
    ozet['pafta'] = [PX0, PY0, px1, PY1]
    ozet['sema_genislik'] = round(L['x1'] - X0, 1)
    os.makedirs(os.path.dirname(cikis), exist_ok=True)
    doc.saveas(cikis)
    return doc, ozet, L


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default=None)
    ap.add_argument('--cikis', default=O.CIKIS)
    ap.add_argument('--ad', default='NB_SIHHI')
    ap.add_argument('--png', action='store_true')
    ap.add_argument('--kolon-birlestir', action='store_true',
                    help='planda aynı düşeyde (≤30 cm), katları ayrık kolonları tek kolon say (plan numaralandırma hatası)')
    a = ap.parse_args(argv)
    m = O.model_oku(a.model)
    if a.kolon_birlestir:
        m, es = O.kolon_birlestir(m)
        print('birleşen kolonlar:', es)
    import sema_temel as T
    rog, ek = T.temel_uret(m, os.path.join(a.cikis, a.ad + '_TEMEL.dxf'))
    doc, ozet, L = sema_uret(m, rog, ek, os.path.join(a.cikis, a.ad + '_SEMA.dxf'))
    ozet['temel'] = ek
    with open(os.path.join(a.cikis, a.ad + '_sema_ozet.json'), 'w', encoding='utf-8') as f:
        json.dump(ozet, f, ensure_ascii=False, indent=1, default=str)
    print('şema:', os.path.join(a.cikis, a.ad + '_SEMA.dxf'), 'genişlik %.0f' % ozet['sema_genislik'])
    if a.png:
        import sema_kontrol as K
        K.pngler(a.cikis, a.ad)


if __name__ == '__main__':
    main()
