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
    # ofisler: yerden ısıtma (yi motoru — mahal başına karşı akışlı salyangoz, ayaklar kapıdan, çakışma yok)
    import yi
    for k, Dd in D.items():
        sihhi.draw_dolap(dict(Dd, c=h(Dd['c']), wall=h(Dd['wall'])))
        c = h(Dd['c']); ux, uy = Dd['u']; nx_, ny_ = Dd['n']
        INS("T-KALORIMETRE", (c[0] + ux * 22, c[1] + uy * 22), Dd['ang'], 0.9, lay=KAL)
        Y = yi.ofis_k(kat, k, Dd)
        dk = D12[0] if kat == 3 else 0.0
        sh_ = lambda p_: (p_[0] + dk + HX, p_[1])
        shl = lambda q_: [sh_(p_) for p_ in q_]
        kc = sh_(Y['kc']); Wk = Y['Wk']; ku, kv = Y['u']; kn, km = Y['n']
        nd = len(Y['circ'])
        # kollektör (gerçek gösterim): gidiş / dönüş kollektör gövdesi, ağız uçları, giriş vanaları
        box_ = [(kc[0] + sx * ku * Wk / 2 + sy * kn * 9, kc[1] + sx * kv * Wk / 2 + sy * km * 9) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        MASK(box_); PL(box_, KLT, closed=True)
        gb = lambda t, o: (kc[0] + ku * t + kn * o, kc[1] + kv * t + km * o)
        PL([gb(-Wk / 2 + 3, -2), gb(Wk / 2 - 3, -2)], IG, 1.6)
        PL([gb(-Wk / 2 + 3, 4), gb(Wk / 2 - 3, 4)], ID, 1.6)
        for c_ in Y['circ']:
            pa, pb = Y['ports'][c_['pidx']]
            pa, pb = sh_(pa), sh_(pb)
            PL([pa, (pa[0] + kn * 4, pa[1] + km * 4)], IG)
            PL([pb, (pb[0] + kn * 10, pb[1] + km * 10)], ID)
        reserve(Polygon(box_).buffer(3).bounds)
        # dolap -> kollektör besleme (kalorimetre sonrası)
        for key, lay, dd, oo in (('IG', IG, 15, -2), ('ID', ID, 30, 4)):
            p0 = (c[0] + ux * dd - nx_ * 9, c[1] + uy * dd - ny_ * 9)
            p1 = gb(-Wk / 2 + 3, oo) if math.dist(gb(-Wk / 2 + 3, oo), p0) < math.dist(gb(Wk / 2 - 3, oo), p0) else gb(Wk / 2 - 3, oo)
            PIPE([p0, p1], lay)
        q = R['ofis'][(kat, k)]
        place_text(kc, [f"KL-{kat - 1}{k} KOLLEKTÖR", f"{nd} AĞIZLI  Q={q['Q']} W  DN25"], 5.5, KLT, rmax=80)
        place_text(c, [f"KM-{kat - 1}{k}", "KALORİMETRE"], 6.0, KAL, rmax=50)
        # devreler
        for i_, c_ in enumerate(sorted(Y['circ'], key=lambda z: z['pidx'])):
            PL(shl(c_['path']), PEX)
            no = f"{kat - 1}{k}.{c_['pidx'] + 1}"
            rp = c_['rpoly']; x0, y0, x1, y1 = rp.bounds
            cen = sh_(((x0 + x1) / 2, (y0 + y1) / 2))
            W_ = c_.get('W', 0.0)
            if min(x1 - x0, y1 - y0) >= 95:
                s_ = 4.2
                bx = [(cen[0] - 7.5 * s_, cen[1] - 9 * s_), (cen[0] + 9 * s_, cen[1] - 9 * s_), (cen[0] + 9 * s_, cen[1] + 8.5 * s_), (cen[0] - 7.5 * s_, cen[1] + 8.5 * s_)]
                MASK(bx)
                MTYB("MTY-ETIKET", cen, 0, s_, PEX, {'UZ_001': f"{c_['L']:.1f} m", 'AR_001': f"{c_['s']:.1f}", 'NO1_001': no,
                                                     'BORU_001': 'PEX BORU, 16 x 2.0', 'MAHAL_001': c_['room']['name'][:12],
                                                     'NO_001': no, 'DERECE_001': f"{c_.get('ti', 20)}°C",
                                                     'KCAL/H:_001': f"{W_:.1f}W", 'ALAN_001': f"{c_['Ar']:.2f} m²",
                                                     'MALZEMECINSI_001': 'Seramik', 'YER_001': ''})
                reserve((bx[0][0], bx[0][1], bx[2][0], bx[2][1]))
            else:
                place_text(cen, [f"D{no}", f"{c_['L']:.1f} m  {W_:.0f} W"], 5.0, PEX, rmax=70)
        # mahal etiketleri (ısı kaybı)
        for r in Y['rooms']:
            cc = yi.oda_calc(Y, r)[0]
            rp = r['poly'].representative_point()
            pp = sh_((rp.x, rp.y)); sc = 0.45
            MASK([(pp[0] - 37 * sc, pp[1] - 62 * sc), (pp[0] + 37 * sc, pp[1] - 62 * sc), (pp[0] + 37 * sc, pp[1] + 44 * sc), (pp[0] - 37 * sc, pp[1] + 44 * sc)])
            MTYB("MTY-RADYATOR MAHAL", sh_((rp.x, rp.y + 0)), 0, 0.45, "MTY-ISIKAYBIMAHAL",
                 {'DERECE_001': f"{cc['ti']}%%DC", 'MAHAL_001': r['name'][:14], 'ISIKAYBI_001': f"{cc['Q']:.0f} W",
                  'NO_001': f"{kat - 1}{k}", 'ALAN': f"{r['A']:.2f} m²"}, mask=None)
        OUTI[('ofis', kat, k)] = dict(n=nd, K=dict(c=kc, W=Wk), Y=Y)
    return D, res
