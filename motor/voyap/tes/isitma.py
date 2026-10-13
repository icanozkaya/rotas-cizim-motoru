# -*- coding: utf-8 -*-
"""Isıtma planları (H sırası = S + 30343): ofis girişinde kalorimetre (sayaç dolabında), ofis içinde yerden ısıtma
kollektörü, kullanıcının MTY devrelerinden kollektöre bağlantı ayakları (kapılardan), koridor ana hatları (45/35 °C),
zemin dükkân radyatörleri (70/50 °C), bodrum kazan dairesi."""
import math, pickle
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from veri import *
from tlib import *
import izgara, ag, yerlesim, sihhi
from hesap import hesapla, dn_isitma

HX = ROW['H'][0] - ROW['S'][0]          # S -> H
R = hesapla()
S_ = pickle.load(open('/tmp/claude-0/vy/sih.pkl', 'rb'))
PEXP = [r for r in S_ if r[0] == 'P' and r[1] == 'MTY-PEX-BORU']
OUTI = {}


def h(p):
    return (p[0] + HX, p[1])


def hl(pts):
    return [h(p) for p in pts]


def cap_kw(kw, n, dT=10.0):
    return dn_isitma(kw, dT)[0]


def devreler(k, kat):
    poly = ofis_poly(k, kat, 'H').buffer(20)
    out = []
    for r in PEXP:
        a = r[2][0][:2]; b = r[2][-1][:2]
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if poly.contains(Point(m)): out.append((a, b))
    return out


def kollektor_yer(Dd, n):
    """kollektör (S çerçevesi): dolabın arkası, ofis içi; boy devre sayısına göre"""
    ux, uy = Dd['u']; nx_, ny_ = Dd['n']; w = Dd['wall']
    Wk = n * 12 + 16
    c = (w[0] - nx_ * 17 + ux * 10, w[1] - ny_ * 17 + uy * 10)
    ports = []
    for j in range(n):
        t = -Wk / 2 + 8 + 6 + j * 12
        ports.append((c[0] + ux * t - nx_ * 8, c[1] + uy * t - ny_ * 8))
    return dict(c=c, W=Wk, ports=ports, u=(ux, uy), n=(-nx_, -ny_), ang=Dd['ang'])


def draw_kollektor(K, nd):
    c = K['c']; ux, uy = K['u']; nx_, ny_ = K['n']; Wk = K['W']
    pts = [(c[0] + sx * ux * Wk / 2 + sy * nx_ * 7, c[1] + sx * uy * Wk / 2 + sy * ny_ * 7) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    MASK(pts)
    PL(pts, KLT, closed=True)
    PL([(c[0] - ux * (Wk / 2 - 3) + nx_ * 2.5, c[1] - uy * (Wk / 2 - 3) + ny_ * 2.5), (c[0] + ux * (Wk / 2 - 3) + nx_ * 2.5, c[1] + uy * (Wk / 2 - 3) + ny_ * 2.5)], IG)
    PL([(c[0] - ux * (Wk / 2 - 3) - nx_ * 2.5, c[1] - uy * (Wk / 2 - 3) - ny_ * 2.5), (c[0] + ux * (Wk / 2 - 3) - nx_ * 2.5, c[1] + uy * (Wk / 2 - 3) - ny_ * 2.5)], ID)
    reserve(Polygon(pts).buffer(3).bounds)


def bacaklar(kat, k, Dd, gi):
    """devre uçlarından kollektöre çift hat (S çerçevesinde hesap, H'ye çizilir)"""
    dv = devreler(k, kat)
    n = len(dv)
    K = kollektor_yer(Dd, max(n, 1))
    # devre uçları S çerçevesine
    ends = [((a[0] - HX, a[1]), (b[0] - HX, b[1])) for a, b in dv]
    mids = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in ends]
    # portlara açısal sırayla eşle (kesişmeyi azalt)
    c = K['c']
    ang = lambda p: math.atan2(p[1] - c[1], p[0] - c[0])
    ux, uy = K['u']
    order = sorted(range(n), key=lambda j: (mids[j][0] - c[0]) * ux + (mids[j][1] - c[1]) * uy)
    legs = []
    for kk, j in enumerate(sorted(order, key=lambda j: -math.dist(mids[j], c))):
        port = K['ports'][order.index(j)]
        pts = gi.route(mids[j], port, sysn=f'L{j}', turn=12.0, free_end=12.0, max_exp=1_500_000, wsys=None)
        if not pts:
            pts = [mids[j], port]
            print('   ayak yok', kat, k, j)
        gi.add_line(pts, f'L{j}')
        legs.append((j, pts))
    return K, ends, legs


def draw_ofis_isitma(kat):
    D = sihhi.dolaplar(kat)
    reset_place()
    # ana hatlar: ortak alan ızgarası (S'de hesap)
    g = izgara.grid_ortak(kat, 5.0, extra_block=[sihhi.dolap_rect(d) for d in D.values()])
    res = {}
    for sh in ('S1', 'S2'):
        offs = [k for k in OFIS_S1 if SAFT_OF[k] == sh]
        for key in ('IG', 'ID'):
            src = W(SAFT[sh]['boru'][key], kat, 'S')
            tg = [(yerlesim.dolap_port(D[k], key), R['ofis'][(kat, k)]['Q'] / 1000.0, k) for k in offs]
            lines, fail = ag.route_tree(g, src, tg, key + sh, turn=40.0)
            if fail: print('  ısıtma bağlanamayan', kat, key, sh, [f[2] for f in fail])
            res[(sh, key)] = dict(lines=lines, runs=ag.runs(src, lines, tg, lambda y, n: cap_kw(y, n)), src=src)
    # şaftlar
    for sh, S0 in SAFT.items():
        x0, y0, x1, y1 = S0['kutu']
        a = h(W((x0, y0), kat, 'S')); b = h(W((x1, y1), kat, 'S'))
        PL([a, (b[0], a[1]), b, (a[0], b[1])], SFT, closed=True)
        for key in ('IG', 'ID'):
            INS("T-KOLON-T", h(W(S0['boru'][key], kat, 'S')), 0, 1.0, lay=IG if key == 'IG' else ID)
        place_text(h(W(S0['boru']['IG'], kat, 'S')), [f"Ş{sh[1]} ISITMA KOLONU", "45/35 °C G/D"], 6.5, SFT, rmax=90,
                   prefer=[(1, 1), (1, -1), (1, 0)])
    for (sh, key), r in res.items():
        for rn in r['runs']:
            PIPE(hl(rn['pts']), IG if key == 'IG' else ID)
    for (sh, key), r in res.items():
        if key != 'IG': continue
        for rn in r['runs']:
            pipe_label(hl(rn['pts']), rn['cap'], 8.0, ICAP, ust=f"{rn['yuk'] * 1000:.0f} W")
    OUTI[('ana', kat)] = res
    # ofisler
    for k, Dd in D.items():
        sihhi.draw_dolap(dict(Dd, c=h(Dd['c']), wall=h(Dd['wall'])))
        c = h(Dd['c']); ux, uy = Dd['u']; nx_, ny_ = Dd['n']
        INS("T-KALORIMETRE", (c[0] + ux * 22, c[1] + uy * 22), Dd['ang'], 0.9, lay=KAL)
        poly = ofis_poly(k, kat, 'S')
        gi = izgara.grid_ofis(kat, poly, 5.0, far_pen=0.5, soft=250.0)
        # kollektör alanı bloke olmasın: portlar uçta serbest
        K, ends, legs = bacaklar(kat, k, Dd, gi)
        Kh = dict(K, c=h(K['c']))
        draw_kollektor(Kh, len(ends))
        # dolap -> kollektör (duvardan geçiş)
        for key, lay, dd in (('IG', IG, 15), ('ID', ID, 30)):
            p0 = (c[0] + ux * dd - nx_ * 9, c[1] + uy * dd - ny_ * 9)
            kc = Kh['c']
            p1 = (kc[0] + ux * (Kh['W'] / 2 - 4) * (1 if dd > 20 else 0.7), kc[1] + uy * (Kh['W'] / 2 - 4) * (1 if dd > 20 else 0.7))
            PIPE([p0, (p0[0] - nx_ * 0, p0[1]), p1] if False else [p0, p1], lay)
        q = R['ofis'][(kat, k)]
        place_text(Kh['c'], [f"KOLLEKTÖR {len(ends)} AĞIZLI", f"Q={q['Q']} W  1\""], 5.5, KLT, rmax=70)
        place_text(c, [f"SD-{kat - 1}{k}", "KALORİMETRE"], 6.0, KAL, rmax=50)
        # bacaklar: çift hat (gidiş / dönüş) ±3 cm
        for (j, pts), in [((j, pts),) for j, pts in legs]:
            a, b = ends[j]
            hp = hl(pts)
            if len(hp) < 2: continue
            try:
                g1 = ag.offset(hp, 3.0); g2 = ag.offset(hp, -3.0)
            except Exception:
                g1 = g2 = hp
            ha, hb = h(a), h(b)
            # devre uçlarını en yakın paralel hatta bağla
            if math.dist(ha, g1[0]) + math.dist(hb, g2[0]) <= math.dist(ha, g2[0]) + math.dist(hb, g1[0]):
                PL([ha] + g1, PEX); PL([hb] + g2, PEX)
            else:
                PL([ha] + g2, PEX); PL([hb] + g1, PEX)
        OUTI[('ofis', kat, k)] = dict(n=len(ends), K=Kh, legs=legs)
    return D, res
