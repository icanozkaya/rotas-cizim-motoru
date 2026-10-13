# -*- coding: utf-8 -*-
"""Zemin kat (dükkânlar) ve bodrum (kazan dairesi, hidrofor, depo, ana dağıtım, pis su toplama) - S ve H sıraları."""
import math, pickle
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import nearest_points
from veri import *
from tlib import *
import izgara, ag, yerlesim, sihhi
from sihhi import inch, PIS_KOL
from isitma import R, h, hl, cap_kw
from hesap import dn_isitma

OUTA = {}
SPLIT_SAFT = {'İŞYERİ 1': 'S1', 'İŞYERİ 2': 'S1', 'İŞYERİ 3': 'S1', 'İŞYERİ 4': 'S2', 'İŞYERİ 5': 'S2'}


def P0(p, row='S'):
    """yerel (Y) -> bodrum dünya"""
    return W(p, 0, row)


def mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


# =================================================================== ZEMİN
def dukkan_dolaplari():
    D = {}
    for nm, d in DUKKAN_S.items():
        a, b = d['arka']
        D[nm] = yerlesim.dolap(Polygon(d['poly']), mid(a, b))
    return D


def kolon_kaydir():
    """1-2. kat pis su kolonları zeminde: dükkân ortasına düşenler asma tavanda en yakın duvara kaydırılır"""
    out = []
    for j, pk in enumerate(PIS_KOL):
        p = (pk['kol'][0] - 2101.0, pk['kol'][1])
        q = p; yol = None
        for nm, d in DUKKAN_S.items():
            poly = Polygon(d['poly'])
            if not poly.contains(Point(p)): continue
            if poly.exterior.distance(Point(p)) < 45: break
            # cephe kenarları hariç en yakın kenar
            c = list(poly.exterior.coords); best = None
            cep = [tuple(map(tuple, e)) for e in d['cephe']]
            for a, b in zip(c[:-1], c[1:]):
                if any(math.dist(a, e[0]) < 5 and math.dist(b, e[1]) < 5 or math.dist(a, e[1]) < 5 and math.dist(b, e[0]) < 5 for e in cep):
                    continue
                s = LineString([a, b]); dd = s.distance(Point(p))
                if best is None or dd < best[0]: best = (dd, s, a, b)
            dd, s, a, b = best
            m = s.interpolate(s.project(Point(p)))
            L = s.length; ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            nx_, ny_ = -uy, ux
            if not poly.contains(Point(m.x + nx_ * 5, m.y + ny_ * 5)): nx_, ny_ = -nx_, -ny_
            q = (m.x + nx_ * 12, m.y + ny_ * 12)
            yol = [p, (q[0], p[1]), q] if abs(ny_) > 0.7 else [p, (p[0], q[1]), q]
            break
        # bodrumda sığınak / depo / kazan dairesi / lobi bandına düşüyorsa asma tavanda güneye uzat
        yb_ = q[1] - ROW['S'][1] - OFF[1][1]
        if yb_ > -452200.0:
            yz = -452230.0 + ROW['S'][1] + OFF[1][1]
            q2 = (q[0], yz)
            yol = (yol or [p, q])[:-1] + [q, q2] if q != p else [p, q2]
            q = q2
        # kolon (betonarme) kaçınma: düşüş noktası ve tavan ötelemesi kolonu kesmez
        CZ = izgara.cols_S(1).buffer(12); CB = izgara.cols_S(0).buffer(12)
        def ok(qq, yy):
            bq = Point(qq[0] - 2161.0, qq[1] + 10.0)
            if CZ.contains(Point(qq)) or CB.contains(bq): return False
            return not (yy and LineString(yy).intersects(izgara.cols_S(1).buffer(3)))
        if not ok(q, yol):
            found = False
            for dd in (30, -30, 60, -60, 90, -90, 130, -130, 180, -180):
                for ax in ((1, 0), (0, 1)):
                    q2 = (q[0] + ax[0] * dd, q[1] + ax[1] * dd)
                    for y2 in ([p, (q2[0], p[1]), q2], [p, (p[0], q2[1]), q2]):
                        if ok(q2, y2):
                            q, yol, found = q2, y2, True; break
                    if found: break
                if found: break
            if not found: print('   kolon kaçınma bulunamadı', j + 1)
        out.append(dict(no=f"P{j + 1}", cap=pk['cap'], p=p, q=q, yol=yol, sb=pk['sb'] or ('21 SB' if pk['cap'] == 'Ø100' else '4 SB')))
    return out


def zemin_sihhi():
    reset_place()
    kat = 1
    D = dukkan_dolaplari()
    res = {}
    for sh, S0 in SAFT.items():
        x0, y0, x1, y1 = S0['kutu']
        a = W((x0, y0), kat, 'S'); b = W((x1, y1), kat, 'S')
        PL([a, (b[0], a[1]), b, (a[0], b[1])], SFT, closed=True)
        for key in ('SS', 'SIS', 'SIRK'):
            INS("T-KOLON-T", W(S0['boru'][key], kat, 'S'), 0, 1.0, lay=sihhi.SYS[key][0])
        place_text(W(S0['boru']['SS'], kat, 'S'), [f"Ş{sh[1]} TESİSAT ŞAFTI", "SS / SıS / SİRK 1-2. KATA"], 6.5, SFT, rmax=90,
                   prefer=[(1, 1), (1, -1), (1, 0)])
    for nm, Dd in D.items():
        sihhi.draw_dolap(Dd)
        c = Dd['c']; ux, uy = Dd['u']; nx_, ny_ = Dd['n']
        SAYAC((c[0] - ux * 33, c[1] - uy * 33), Dd['ang'], 'DN20', 0.55)
        INS("T-KOLON-T", yerlesim.dolap_port(Dd, 'SS'), 0, 1.0, lay=SS)
        place_text(yerlesim.dolap_port(Dd, 'SS'), ["SS 3/4\" BODRUM TAVANINDAN"], 5.5, TCAP, rmax=60)
        p0 = (c[0] - ux * 33 - nx_ * 9, c[1] - uy * 33 - ny_ * 9)
        p1 = (p0[0] - nx_ * 60, p0[1] - ny_ * 60)
        PIPE([p0, p1], SS)
        VANA(p1, Dd['ang'] + 90, 'DN20', 0.5)
        place_text(p1, ["Ø25 (3/4\") BEKLEME UCU", "VANALI - KÖR TAPALI"], 5.5, TNOT, rmax=60)
        place_text(c, [f"SD-Z{nm[-1]}"], 8.0, SAY, rmax=40)
    # pis su kolonları
    K = kolon_kaydir()
    for k in K:
        INS("T-KOLON-P", k['q'], 0, 1.0, lay=PSK)
        if k['yol']:
            INS("T-KOLON-P", k['p'], 0, 0.8, lay=PSK)
            PIPE(k['yol'], PS)
            place_text(k['p'], ["TAVANDA"], 5.0, PSC, rmax=30)
        place_text(k['q'], [f"{k['no']} {k['cap']}"], 7.0, PSN, rmax=50)
    OUTA['zemin'] = dict(D=D, res=res, K=K)
    return D, K


def radyatorler(nm, n, boy):
    """vitrin cephesi boyunca eşit aralıklı paneller (S, cephe kenarının 15 cm içi)"""
    d = DUKKAN_S[nm]; poly = Polygon(d['poly'])
    a, b = d['cephe'][0]
    L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx_, ny_ = -uy, ux
    if not poly.contains(Point(mid(a, b)[0] + nx_ * 10, mid(a, b)[1] + ny_ * 10)): nx_, ny_ = -nx_, -ny_
    out = []
    for i in range(n):
        t = min(max(L * (i + 0.5) / n, boy * 50 + 25), L - boy * 50 - 25)
        c = (a[0] + ux * t + nx_ * 16, a[1] + uy * t + ny_ * 16)
        out.append(dict(c=c, u=(ux, uy), n=(nx_, ny_), boy=boy, port=(c[0] + nx_ * 14 - ux * boy * 35, c[1] + ny_ * 14 - uy * boy * 35)))
    return out


def zemin_isitma():
    reset_place()
    kat = 1
    D = dukkan_dolaplari()
    for sh, S0 in SAFT.items():
        x0, y0, x1, y1 = S0['kutu']
        a = h(W((x0, y0), kat, 'S')); b = h(W((x1, y1), kat, 'S'))
        PL([a, (b[0], a[1]), b, (a[0], b[1])], SFT, closed=True)
        for key in ('IG', 'ID'):
            INS("T-KOLON-T", h(W(S0['boru'][key], kat, 'S')), 0, 1.0, lay=IG if key == 'IG' else ID)
        place_text(h(W(S0['boru']['IG'], kat, 'S')), [f"Ş{sh[1]} ISITMA KOLONU", "45/35 °C 1-2. KAT OFİSLERE"], 6.5, SFT, rmax=90,
                   prefer=[(1, 1), (1, -1), (1, 0)])
    out = {}
    for nm, Dd in D.items():
        q = R['dukkan'][nm]; rd = q['rad']
        Dh = dict(Dd, c=h(Dd['c']), wall=h(Dd['wall']))
        sihhi.draw_dolap(Dh)
        c = Dh['c']; ux, uy = Dd['u']; nx_, ny_ = Dd['n']
        INS("T-KALORIMETRE", (c[0] + ux * 22, c[1] + uy * 22), Dd['ang'], 0.9, lay=KAL)
        place_text(c, [f"SD-Z{nm[-1]} KALORİMETRE", "70/50 °C BODRUM TAVANINDAN"], 6.0, KAL, rmax=60)
        rads = radyatorler(nm, rd['adet'], rd['boy'])
        poly = Polygon(DUKKAN_S[nm]['poly'])
        gi = izgara.grid_ofis(1, poly, 5.0, far_pen=1.0, soft=250.0)
        # dolaptan dükkân içine
        s0 = (Dd['c'][0] - nx_ * 35, Dd['c'][1] - ny_ * 35)
        tg = [(r['port'], q['Q'] / len(rads) / 1000.0, i) for i, r in enumerate(rads)]
        lines, fail = ag.route_tree(gi, s0, tg, 'R', turn=30.0)
        rr = ag.runs(s0, lines, tg, lambda y, n: dn_isitma(y, 20.0)[0])
        for rn in rr:
            hp = hl(rn['pts'])
            try:
                g1 = ag.offset(hp, 4.0); g2 = ag.offset(hp, -4.0)
            except Exception:
                g1 = g2 = hp
            PIPE(g1, IG); PIPE(g2, ID)
        for rn in rr:
            pipe_label(hl(rn['pts']), rn['cap'], 7.0, ICAP, ust=f"{rn['yuk'] * 1000:.0f} W")
        PIPE([h((Dd['c'][0] - nx_ * 9, Dd['c'][1] - ny_ * 9)), h(s0)], IG)
        for i, r in enumerate(rads):
            cc = h(r['c']); ux2, uy2 = r['u']; nx2, ny2 = r['n']; Lr = r['boy'] * 100
            pts = [(cc[0] + sx * ux2 * Lr / 2 + sy * nx2 * 5, cc[1] + sx * uy2 * Lr / 2 + sy * ny2 * 5) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            MASK(pts); PL(pts, RAD, closed=True)
            PL([(cc[0] - ux2 * Lr / 2, cc[1] - uy2 * Lr / 2), (cc[0] + ux2 * Lr / 2, cc[1] + uy2 * Lr / 2)], RAD)
            reserve(Polygon(pts).buffer(4).bounds)
            if i == 0:
                place_text(cc, [f"{rd['adet']} AD. {rd['tip']}/{int(Lr)}", f"her biri {q['Q'] / rd['adet']:.0f} W"], 6.0, RAD, rmax=80)
        out[nm] = dict(rads=rads, runs=rr)
    OUTA['zemin_isi'] = dict(D=D, out=out)
    return D


# =================================================================== BODRUM
KD = dict(
    kazan=[(248655.0, -451650.0), (248655.0, -451565.0), (248655.0, -451480.0)],
    denge=(248800.0, -451560.0), kol_y=(-451360.0, -451395.0), kol_x=(248760.0, 249160.0),
    pompa={'OFIS': 248840.0, 'DUKKAN': 248900.0, 'BOYLER': 249070.0},
    genlesme=(248705.0, -451300.0), boyler=(249150.0, -451590.0), depo=[(248750.0, -450880.0, 248900.0, -451030.0), (248920.0, -450880.0, 249070.0, -451030.0)],
    hidrofor=(248745.0, -451060.0, 248870.0, -451150.0), mtank=(248900.0, -451105.0), yumusatma=(249120.0, -451100.0),
    sirk=(249160.0, -451440.0), baca_cikis=(248700.0, -451719.0),
    menfez_alt=(248760.0, -450867.0), menfez_ust=(249150.0, -450867.0),
)


def kd_cizim(row):
    """kazan dairesi ekipmanı (Y koordinatından row sırasına)"""
    X = lambda p: P0(p, row)
    x0, y0, x1, y1 = KAZAN_D
    # EI120 bölme duvarı (sığınak içinde yeni)
    HATCH_RECT(*X((x1 - 7, y0)), *X((x1 + 7, y1)), CHZ)
    a = X((x0 + 20, y1 - 25))
    T(a[0], a[1], "KAZAN DAİRESİ", 16, CHZ, TA.TOP_LEFT)
    T(a[0], a[1] - 22, f"(sığınak içinde, EI120 bölme) {((x1 - x0) * (y1 - y0) / 1e4):.1f} m²", 7, CHZ, TA.TOP_LEFT)
    for i, k in enumerate(KD['kazan']):
        INS("T-KAZAN", X(k), -90, 1.0, lay=CHZ)
        p = X((k[0] + 50, k[1]))
        T(p[0], p[1], f"K{i + 1}", 7, CHZ, TA.MIDDLE_LEFT)
    p = X((KD['kazan'][0][0] + 75, KD['kazan'][0][1] - 50))
    T(p[0], p[1], f"{R['kazan']['adet']} x {R['kazan']['birim']} kW YOĞUŞMALI KASKAD KAZAN", 6.5, CHZ, TA.TOP_LEFT)
    C(X(KD['denge']), 12, CHZ); T(*X((KD['denge'][0] + 16, KD['denge'][1])), "DENGE KABI", 5.5, CHZ, TA.MIDDLE_LEFT)
    C(X(KD['genlesme']), 25, CHZ); T(*X((KD['genlesme'][0] + 30, KD['genlesme'][1])), f"GENLEŞME {R['genlesme']['Vsec']} L", 5.5, CHZ, TA.MIDDLE_LEFT)
    C(X(KD['boyler']), 45, CHZ); C(X(KD['boyler']), 40, CHZ)
    T(*X(KD['boyler']), "BOYLER", 7, CHZ, TA.MIDDLE_CENTER)
    T(*X((KD['boyler'][0], KD['boyler'][1] - 12)), f"{R['boyler']['Vsec']} L", 6, CHZ, TA.MIDDLE_CENTER)
    for i, (a0, b0, a1, b1) in enumerate(KD['depo']):
        p = [X((a0, b0)), X((a1, b0)), X((a1, b1)), X((a0, b1))]
        PL(p, CHZ, closed=True)
        T(*mid(p[0], p[2]), f"DEPO-{i + 1}", 7, CHZ, TA.MIDDLE_CENTER)
        T(mid(p[0], p[2])[0], mid(p[0], p[2])[1] - 12, f"{R['depo']['Vsec'] // 2} m³", 6, CHZ, TA.MIDDLE_CENTER)
    a0, b0, a1, b1 = KD['hidrofor']
    p = [X((a0, b0)), X((a1, b0)), X((a1, b1)), X((a0, b1))]
    PL(p, CHZ, closed=True); T(*mid(p[0], p[2]), "HİDROFOR", 6, CHZ, TA.MIDDLE_CENTER)
    C(X(KD['mtank']), 20, CHZ); T(*X((KD['mtank'][0], KD['mtank'][1] - 26)), f"{R['hidrofor']['Vn']} L", 5, CHZ, TA.TOP_CENTER)
    PL([X((KD['yumusatma'][0] - 15, KD['yumusatma'][1] - 25)), X((KD['yumusatma'][0] + 15, KD['yumusatma'][1] - 25)),
        X((KD['yumusatma'][0] + 15, KD['yumusatma'][1] + 25)), X((KD['yumusatma'][0] - 15, KD['yumusatma'][1] + 25))], CHZ, closed=True)
    T(*X((KD['yumusatma'][0], KD['yumusatma'][1] + 30)), "YUMUŞATMA", 5, CHZ, TA.BOTTOM_CENTER)
    INS("T-YER-SUZGECI", X((248950.0, -451650.0)), 0, 1.0, lay=PS)
    T(*X((248965.0, -451650.0)), "YER SÜZGECİ → POMPA ÇUKURU", 5, PSC, TA.MIDDLE_LEFT)
    for k, t in (('menfez_alt', f"ALT MENFEZ {R['kd_hava']['alt']} cm² (+0,30)"), ('menfez_ust', f"ÜST MENFEZ {R['kd_hava']['ust']} cm² (tavan)")):
        p = X(KD[k]); INS("T-MENFEZ", (p[0], p[1] - 12), 0, 1.0, lay=MEN)
        T(p[0], p[1] - 28, t, 5, MEN, TA.TOP_CENTER)


def bodrum_grid(row='S'):
    kat = 0
    x0, x1 = izgara.PANS[0]
    from router import Grid
    g = Grid((x0, izgara.YR[0], x1, izgara.YR[1]), step=5.0)
    fp = izgara.foot_S(0)
    g.block |= ~izgara.poly_mask(g, fp.buffer(-8))
    g.base[izgara.raster_walls(g, izgara.walls_S(0), 1)] += 150.0
    for c in getattr(izgara.cols_S(0), 'geoms', [izgara.cols_S(0)]):
        g.add_block(c, pad=3.0)
    # yangın deposu, kazan dairesi ekipmanları
    dx, dy = ROW['S']
    g.add_block(box(248235 + dx, -451720 + dy, 248640 + dx, -450860 + dy), pad=0)
    return g


def bodrum_sihhi():
    reset_place()
    kd_cizim('S')
    g = bodrum_grid()
    X = lambda p: P0(p, 'S')
    # kazan dairesi çıkışları: SS (hidrofor), SIS (boyler), SIRK (boyler)
    cik = {'SS': X((248808.0, -451150.0)), 'SIS': X((249120.0, -451515.0)), 'SIRK': X((249160.0, -451440.0))}
    res = {}
    for key in ('SS', 'SIS', 'SIRK'):
        lay = sihhi.SYS[key][0]
        tg = []
        for sh in ('S1', 'S2'):
            n = sum(1 for k in OFIS_S1 if SAFT_OF[k] == sh) * 2
            yb = n * (sihhi.YB_S if key == 'SS' else sihhi.YB_H)
            tg.append((X(SAFT[sh]['boru'][key]), yb if key != 'SIRK' else n, sh))
        if key == 'SS':
            for nm, Dd in OUTA['zemin']['D'].items():
                p = yerlesim.dolap_port(Dd, 'SS')
                tg.append(((p[0] - 2161.0, p[1] + 10.0), 1.0, nm))
        lines, fail = ag.route_tree(g, cik[key], tg, key + 'B', turn=60.0)
        if fail: print('  bodrum', key, 'bağlanamayan', fail)
        res[key] = ag.runs(cik[key], lines, tg, sihhi.SYS[key][1])
        for rn in res[key]: PIPE(rn['pts'], lay)
    for key, rr in res.items():
        for rn in rr:
            pipe_label(rn['pts'], rn['cap'], 8.0, TCAP, ust=(f"{rn['yuk']:.1f} MB" if key != 'SIRK' else None))
    for sh, S0 in SAFT.items():
        for key in ('SS', 'SIS', 'SIRK'):
            INS("T-KOLON-T", X(S0['boru'][key]), 0, 1.0, lay=sihhi.SYS[key][0])
        place_text(X(S0['boru']['SS']), [f"Ş{sh[1]} SS / SıS / SİRK", "YUKARI (Z-1-2)"], 6.5, SFT, rmax=90)
    for nm, Dd in OUTA['zemin']['D'].items():
        p = yerlesim.dolap_port(Dd, 'SS'); p = (p[0] - 2161.0, p[1] + 10.0)
        INS("T-KOLON-T", p, 0, 1.0, lay=SS)
        place_text(p, [f"{nm} SS YUKARI"], 6.0, TCAP, rmax=60)
    # şebeke girişi: ön cephe (alt çekirdek yanı) -> ana sayaç -> depolar
    gir = X((248640.0, -457180.0)); say = X((248640.0, -457090.0))
    dep = X((248825.0, -451030.0))
    pts = g.route(say, dep, sysn='SB', turn=60.0, max_exp=3_000_000)
    PIPE([gir, say], SS)
    if pts: PIPE(pts, SS); pipe_label(pts, '1 1/2"', 8.0, TCAP, ust='ŞEBEKE HATTI (bodrum tavanından)')
    SAYAC(mid(gir, say), 90, 'DN40', 1.0)
    VANA((say[0], say[1] - 8), 90, 'DN40', 0.8); CEKV((say[0], say[1] + 10), 90, 'DN40', 0.8)
    place_text(gir, ["ŞEBEKEDEN Ø50", "ANA SU SAYACI DN40 (BİNA GİRİŞİ)", "VANA + PİSLİK TUTUCU + ÇEK VALF"], 7.0, SAY, rmax=120)
    # pis su toplama: zemin kolon dipleri -> bodrum tavanı -> ön cephe rögarları
    K = OUTA['zemin']['K']
    rog = {'R1': X((248560.0, -457330.0)), 'R2': X((248930.0, -457450.0)), 'R3': X((249230.0, -457545.0))}
    for nm, p in rog.items():
        PL([(p[0] - 25, p[1] - 25), (p[0] + 25, p[1] - 25), (p[0] + 25, p[1] + 25), (p[0] - 25, p[1] + 25)], ROG, closed=True)
        C(p, 18, ROG)
        T(p[0], p[1] - 34, nm, 9, ROG, TA.TOP_CENTER)
        T(p[0], p[1] - 46, "50x50 h:-60", 6, ROG, TA.TOP_CENTER)
    cikis = {'R1': X((248560.0, -457135.0)), 'R2': X((248930.0, -457250.0)), 'R3': X((249230.0, -457345.0))}
    pb = X((248930.0, -457700.0))
    PL([(pb[0] - 30, pb[1] - 30), (pb[0] + 30, pb[1] - 30), (pb[0] + 30, pb[1] + 30), (pb[0] - 30, pb[1] + 30)], ROG, closed=True)
    T(pb[0] + 38, pb[1], "PB (PARSEL BACASI) → ŞEHİR KANALI", 8, ROG, TA.MIDDLE_LEFT)
    for a, b in (('R1', 'R2'), ('R3', 'R2')):
        PIPE([rog[a], rog[b]], PS)
    PIPE([rog['R2'], pb], PS)
    # kolon dipleri (bodrum çerçevesi)
    drops = [(dict(k, b=(k['q'][0] - 2161.0, k['q'][1] + 10.0))) for k in K]
    def lane(x):
        lx = x - ROW['S'][0]
        return 'R1' if lx < 248700 else ('R2' if lx < 249250 else 'R3')
    gp = bodrum_grid()
    pres = {}
    for rn in ('R1', 'R2', 'R3'):
        ds = [d for d in drops if lane(d['b'][0]) == rn]
        if not ds: continue
        tg = [(d['b'], float(d['sb'].split()[0]) * 2, d['no']) for d in ds]
        ex = cikis[rn]
        PIPE([ex, rog[rn]], PS)
        lines, fail = ag.route_tree(gp, ex, tg, 'P' + rn, turn=80.0)
        if fail: print('  pis bağlanamayan', rn, [f[2] for f in fail])
        rr = ag.runs(ex, lines, tg, lambda y, n: 'Ø100' if y <= 160 else ('Ø125' if y <= 300 else 'Ø150'))
        for r in rr: PIPE(r['pts'], PS)
        for r in rr: pipe_label(r['pts'], r['cap'], 8.0, PSC, ust=f"{r['yuk']:.0f} SB %1")
        pres[rn] = rr
    for d in drops:
        INS("T-KOLON-P", d['b'], 0, 1.0, lay=PSK)
        place_text(d['b'], [d['no']], 6.5, PSN, rmax=40)
    # otopark süzgeçleri + pis su çukuru + dalgıç pompa (alt sağ)
    cuk = X((249330.0, -456700.0))
    PL([(cuk[0] - 50, cuk[1] - 50), (cuk[0] + 50, cuk[1] - 50), (cuk[0] + 50, cuk[1] + 50), (cuk[0] - 50, cuk[1] + 50)], PS, closed=True)
    INS("T-POMPA", (cuk[0] - 18, cuk[1]), 90, 1.0, lay=CHZ); INS("T-POMPA", (cuk[0] + 18, cuk[1]), 90, 1.0, lay=CHZ)
    place_text(cuk, ["PİS SU ÇUKURU 100x100 h:150", "2 AD. DALGIÇ POMPA (1 ASİL+1 YEDEK)", "Q=10 m³/h H=8 mSS, ŞAMANDIRALI"], 6.5, PSC, rmax=110)
    r4 = X((249330.0, -457620.0))
    PL([(r4[0] - 25, r4[1] - 25), (r4[0] + 25, r4[1] - 25), (r4[0] + 25, r4[1] + 25), (r4[0] - 25, r4[1] + 25)], ROG, closed=True)
    T(r4[0] + 30, r4[1], "R4 (BASMA HATTI RÖGARI)", 7, ROG, TA.MIDDLE_LEFT)
    e4 = X((249330.0, -457360.0))
    bas = gp.route((cuk[0], cuk[1] + 50), e4, sysn='BAS', turn=60.0, max_exp=2_000_000) or [(cuk[0], cuk[1] + 50), e4]
    bas = bas + [r4]
    PIPE(bas, PS); pipe_label(bas, 'Ø63 PE BASMA', 7.0, PSC)
    CEKV((bas[0][0], bas[0][1] + 20), 90, 'DN50', 0.7); PIPE([r4, pb], PS)
    suz = [X(p) for p in ((248800.0, -453800.0), (249600.0, -453800.0), (248750.0, -455200.0), (249600.0, -455200.0),
                          (248900.0, -456600.0), (249500.0, -456600.0))]
    for s in suz: INS("T-YER-SUZGECI", s, 0, 1.2, lay=PS)
    tgs = [(s, 2.0, i) for i, s in enumerate(suz)]
    lines, fail = ag.route_tree(gp, (cuk[0], cuk[1] - 50), tgs, 'OTS', turn=80.0)
    for l in lines: PIPE(l, PS)
    place_text(suz[0], ["OTOPARK YER SÜZGECİ Ø100", "döşeme altından pompa çukuruna"], 6.0, PSC, rmax=80)
    OUTA['bodrum'] = dict(res=res, drops=drops, pres=pres)


def bodrum_isitma():
    reset_place()
    kd_cizim('H')
    X = lambda p: P0(p, 'H')
    XS = lambda p: P0(p, 'S')
    g = bodrum_grid()
    # kollektör + pompalar (kazan dairesi içinde, H)
    (yg, yd), (xa, xb) = KD['kol_y'], KD['kol_x']
    PL([X((xa, yg)), X((xb, yg))], IG, 3.0); PL([X((xa, yd)), X((xb, yd))], ID, 3.0)
    T(*X((xa, yg + 8)), "GİDİŞ KOLLEKTÖRÜ DN80", 6, ICAP, TA.BOTTOM_LEFT)
    T(*X((xa, yd - 8)), "DÖNÜŞ KOLLEKTÖRÜ DN80", 6, ICAP, TA.TOP_LEFT)
    # kazanlar -> denge kabı -> kollektör
    for k in KD['kazan']:
        PL([X((k[0] + 45, k[1] + 12)), X((KD['denge'][0] - 12, k[1] + 12))], IG)
        PL([X((k[0] + 45, k[1] - 12)), X((KD['denge'][0] - 12, k[1] - 12))], ID)
    PL([X((KD['denge'][0], KD['denge'][1] + 12)), X((KD['denge'][0], yg)), X((xa, yg))], IG, 2.0)
    PL([X((KD['denge'][0] + 8, KD['denge'][1] + 10)), X((KD['denge'][0] + 8, yd)), X((xa, yd))], ID, 2.0)
    PL([X((KD['genlesme'][0], KD['genlesme'][1] + 25)), X((KD['genlesme'][0], yd)), X((xa, yd))], ID)
    for ad, x in KD['pompa'].items():
        INS("T-POMPA", X((x, yg - 70)), -90, 1.0, lay=CHZ)
        PL([X((x, yg)), X((x, -451700.0))], IG, 1.5)
        PL([X((x + 25, yd)), X((x + 25, -451700.0))], ID, 1.5)
        VANA(X((x, yg - 30)), 90, 'DN40', 0.6); CEKV(X((x, yg - 100)), -90, 'DN40', 0.6)
        T(*X((x - 6, yg - 140)), {'OFIS': 'P1 OFİS Y.I. 45/35', 'DUKKAN': 'P2 DÜKKÂN 70/50', 'BOYLER': 'P3 BOYLER'}[ad], 5, CHZ, TA.MIDDLE_RIGHT, 90)
    INS("T-POMPA", X((KD['pompa']['OFIS'] - 0, yg - 180)), 0, 0.7, lay=CHZ)
    T(*X((KD['pompa']['OFIS'] + 12, yg - 180)), "3 YOLLU KARIŞIM VANASI", 4.5, CHZ, TA.MIDDLE_LEFT)
    # boyler serpantini
    bx = KD['pompa']['BOYLER']
    PL([X((bx, -451700.0)), X((bx, -451690.0)), X((KD['boyler'][0] - 40, -451690.0))], IG)
    # devre çıkışları (kazan dairesi güney duvarı)
    out_of = {'OFIS': (X((KD['pompa']['OFIS'], -451700.0)), X((KD['pompa']['OFIS'] + 25, -451700.0))),
              'DUKKAN': (X((KD['pompa']['DUKKAN'], -451700.0)), X((KD['pompa']['DUKKAN'] + 25, -451700.0)))}
    res = {}
    # ofis devresi -> Ş1, Ş2
    for key, lay, j in (('IG', IG, 0), ('ID', ID, 1)):
        tg = []
        for sh in ('S1', 'S2'):
            kw = sum(R['ofis'][(kat, k)]['Q'] for kat in (2, 3) for k in OFIS_S1 if SAFT_OF[k] == sh) / 1000.0
            tg.append((XS(SAFT[sh]['boru'][key]), kw, sh))
        src = (out_of['OFIS'][j][0] - ROW['H'][0] + ROW['S'][0], out_of['OFIS'][j][1])
        lines, fail = ag.route_tree(g, src, tg, 'O' + key, turn=60.0)
        rr = ag.runs(src, lines, tg, lambda y, n: dn_isitma(y, 10.0)[0])
        for rn in rr: PIPE(hl(rn['pts']), lay)
        res[('OFIS', key)] = rr
    # dükkân devresi -> dükkân dolapları (zemin dolap noktası bodrum tavanında)
    D = OUTA['zemin_isi']['D']
    for key, lay, j in (('IG', IG, 0), ('ID', ID, 1)):
        tg = []
        for nm, Dd in D.items():
            p = yerlesim.dolap_port(Dd, key)
            tg.append(((p[0] - 2161.0, p[1] + 10.0), R['dukkan'][nm]['Q'] / 1000.0, nm))
        src = (out_of['DUKKAN'][j][0] - ROW['H'][0] + ROW['S'][0], out_of['DUKKAN'][j][1])
        lines, fail = ag.route_tree(g, src, tg, 'D' + key, turn=60.0)
        if fail: print('  dükkan ısıtma bağlanamayan', fail)
        rr = ag.runs(src, lines, tg, lambda y, n: dn_isitma(y, 20.0)[0])
        for rn in rr: PIPE(hl(rn['pts']), lay)
        res[('DUKKAN', key)] = rr
        for t in tg:
            if key == 'IG':
                INS("T-KOLON-T", h(t[0]), 0, 1.0, lay=IG)
                place_text(h(t[0]), [f"{t[2]} G/D YUKARI", f"{t[1] * 1000:.0f} W"], 6.0, ICAP, rmax=60)
    for (dv, key), rr in res.items():
        if key != 'IG': continue
        for rn in rr:
            pipe_label(hl(rn['pts']), rn['cap'], 8.0, ICAP, ust=f"{rn['yuk']:.1f} kW " + ('45/35' if dv == 'OFIS' else '70/50'))
    for sh, S0 in SAFT.items():
        for key in ('IG', 'ID'):
            INS("T-KOLON-T", X(S0['boru'][key]), 0, 1.0, lay=IG if key == 'IG' else ID)
        place_text(X(S0['boru']['IG']), [f"Ş{sh[1]} ISITMA G/D", "YUKARI (1-2. KAT)"], 6.5, SFT, rmax=90)
    # baca: kazan dairesi -> Ş1 baca şaftı
    bc = g.route(XS(KD['baca_cikis']), XS(SAFT['S1']['baca']), sysn='BC', turn=80.0, max_exp=3_000_000) or [XS(KD['baca_cikis']), XS(SAFT['S1']['baca'])]
    PIPE(hl(bc), BACA, 2.0)
    pipe_label(hl(bc), f"BACA Ø{R['baca']['Dsec']} PP (yoğuşmalı, fanlı)", 7.0, BACA)
    place_text(X(SAFT['S1']['baca']), [f"BACA ŞAFTI Ø{R['baca']['Dsec']}", "ÇATI +1,00 m ÜZERİNE"], 6.5, BACA, rmax=80)
    OUTA['bodrum_isi'] = res
