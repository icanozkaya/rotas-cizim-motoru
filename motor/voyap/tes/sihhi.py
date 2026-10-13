# -*- coding: utf-8 -*-
"""Sıhhi tesisat planları (S sırası): koridor ana hatları (soğuk / sıcak / sirkülasyon), ofis girişinde sayaç dolabı,
merkezi sıcak su bağlantısı (termosifon iptal), pis su kolonları, zemin dükkân bağlantıları, bodrum."""
import math, pickle
from shapely.geometry import Polygon, Point, LineString, box
from veri import *
from tlib import *
import termo, izgara, ag, yerlesim
from piscol2 import pis_kolonlar

INCH = [(1.0, '1/2"'), (2.25, '3/4"'), (7.84, '1"'), (19.36, '1 1/4"'), (46.24, '1 1/2"'), (108.4, '2"'), (256, '2 1/2"'),
        (784, '3"'), (1444, '3 1/2"'), (4096, '4"')]
YB_S, YB_H = 4.5, 4.0           # ofis soğuk / sıcak YB (kullanıcının MTY değerleri)


def inch(yb):
    for m, s in INCH:
        if yb <= m + 1e-9: return s
    return '5"'


def sirk_cap(n):
    return '1/2"' if n <= 2 else ('3/4"' if n <= 8 else '1"')


SYS = {'SS': (SS, lambda y, n: inch(y)), 'SIS': (SIS, lambda y, n: inch(y)), 'SIRK': (SIRK, lambda y, n: sirk_cap(n))}
PIS_KOL = pis_kolonlar()                     # 1. kat S koordinatı
OUT = {}                                     # şema için veriler


def dolaplar(kat):
    D = {}
    for k, d in OFIS_S1.items():
        poly = ofis_poly(k, kat, 'S')
        D[k] = yerlesim.dolap(poly, ofis_pt(k, 'dolap_pt' if 'dolap_pt' in d else 'besleme', kat), ofis_pt(k, 'kapi', kat))
    return D


def dolap_rect(Dd, pad=0.0):
    c = Dd['c']; ux, uy = Dd['u']; nx_, ny_ = Dd['n']
    return Polygon([(c[0] + sx * ux * (45 + pad) + sy * nx_ * (9 + pad), c[1] + sx * uy * (45 + pad) + sy * ny_ * (9 + pad))
                    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


def draw_dolap(Dd):
    c = Dd['c']
    MASK(list(dolap_rect(Dd).exterior.coords)[:-1])
    INS("T-DOLAP", c, Dd['ang'], 1.0, lay=SAY, mask=None)
    reserve(dolap_rect(Dd, 3).bounds)


def kat_ofis_sihhi(kat):
    reset_place()
    D = dolaplar(kat)
    g = izgara.grid_ortak(kat, 5.0, extra_block=[dolap_rect(d) for d in D.values()])
    res = {}
    for sh in ('S1', 'S2'):
        offs = [k for k in OFIS_S1 if SAFT_OF[k] == sh]
        for key in ('SS', 'SIS', 'SIRK'):
            lay, capf = SYS[key]
            src = W(SAFT[sh]['boru'][key], kat, 'S')
            yb = {'SS': YB_S, 'SIS': YB_H, 'SIRK': 1.0}[key]
            tg = [(yerlesim.dolap_port(D[k], key), yb, k) for k in offs]
            lines, fail = ag.route_tree(g, src, tg, key + sh, turn=40.0)
            if fail: print('  bağlanamayan', kat, key, sh, [f[2] for f in fail])
            res[(sh, key)] = dict(lines=lines, runs=ag.runs(src, lines, tg, capf), src=src)
    OUT[('ofis', kat)] = dict(D=D, res=res)
    return D, res


_UH = None


def _kullanici_hatlari(area):
    global _UH
    if _UH is None:
        S_ = pickle.load(open('/tmp/claude-0/vy/sih.pkl', 'rb'))
        _UH = []
        for r in S_:
            if r[1] in ('MTY-SICAKSU-BORU', 'MTY-SOGUKSU-BORU') and r[0] in 'LP':
                q = [p[:2] for p in (r[2] if r[0] == 'P' else r[2][:2])]
                if len(q) > 1: _UH.append(q)
    T_ = termo.tara()
    out = []
    for q in _UH:
        if LineString(q).intersects(area): out.append(q)
    return out


def draw_ofis_sihhi(kat):
    D, res = kat_ofis_sihhi(kat)
    # şaftlar
    for sh, S_ in SAFT.items():
        x0, y0, x1, y1 = S_['kutu']
        a = W((x0, y0), kat, 'S'); b = W((x1, y1), kat, 'S')
        PL([a, (b[0], a[1]), b, (a[0], b[1])], SFT, closed=True)
        for key in ('SS', 'SIS', 'SIRK'):
            p = W(S_['boru'][key], kat, 'S')
            INS("T-KOLON-T", p, 0, 1.0, lay=SYS[key][0])
    # ana hatlar
    for (sh, key), r in res.items():
        lay = SYS[key][0]
        for rn in r['runs']:
            PIPE(rn['pts'], lay)
    for (sh, key), r in res.items():
        for rn in r['runs']:
            ust = (f"{rn['yuk']:.2f} MB".replace('.00', '') if key != 'SIRK' else None)
            pipe_label(rn["pts"], rn["cap"], 8.0, TCAP, ust=ust)
    # dolaplar + sayaçlar + ofis bağlantısı
    for k, Dd in D.items():
        draw_dolap(Dd)
        ux, uy = Dd['u']; nx_, ny_ = Dd['n']; c = Dd['c']
        # dolap içi: ana hat girişi -> vana -> sayaç -> ofis tarafı (kesintisiz)
        ic = {}
        for key, off, lay in (('SS', -33, SS), ('SIS', -18, SIS)):
            pp = yerlesim.dolap_port(Dd, key)
            ic[key] = (c[0] + ux * off - nx_ * 9, c[1] + uy * off - ny_ * 9)
            if not any(LineString([pp, ic[key]]).buffer(1.5).intersection(LineString(q_)).length > 2
                       for q_ in _kullanici_hatlari(LineString([pp, ic[key]]).buffer(3))):      # kullanıcı hattı zaten geçiyorsa tekrar çizme
                PIPE([pp, ic[key]], lay)
            SAYAC((c[0] + ux * off, c[1] + uy * off), Dd['ang'] + 90, 'DN20', 0.55)
        pr = yerlesim.dolap_port(Dd, 'SIRK')
        PIPE([pr, (c[0] - ux * 3, c[1] - uy * 3), (c[0] - ux * 18, c[1] - uy * 18)], SIRK)
        # soğuk: dolaptan kullanıcının besleme ucuna
        bp = ofis_pt(k, 'besleme', kat)
        sp = (c[0] - ux * 42 - nx_ * 9, c[1] - uy * 42 - ny_ * 9)          # ana hat girişinden 9 cm yanda (üst üste binmesin)
        cands = [[sp, (sp[0], bp[1]), bp], [sp, (bp[0], sp[1]), bp]]
        for f_ in (0.3, 0.5, 0.7):                                                               # Z biçimli seçenekler
            ym_ = sp[1] + (bp[1] - sp[1]) * f_; xm_ = sp[0] + (bp[0] - sp[0]) * f_
            cands += [[sp, (sp[0], ym_), (bp[0], ym_), bp], [sp, (xm_, sp[1]), (xm_, bp[1]), bp]]
        mains = [LineString(rn['pts']) for (sh_, key_), r_ in res.items() if key_ == 'SS' for rn in r_['runs']]
        mains += [LineString(q_) for q_ in _kullanici_hatlari(Point(bp).buffer(150))]          # kullanıcının soğuk/sıcak hatları
        q = min(cands, key=lambda qq: sum(LineString(qq).buffer(1.5).intersection(m).length for m in mains))
        # kullanıcının soğuk hattı dolaptan geçiyorsa: o hatta dik T bağlantı (hat üzerinde yürümeden)
        for ul in [LineString(q_) for q_ in _kullanici_hatlari(Point(bp).buffer(3))]:
            if ul.distance(Point(bp)) > 2: continue
            for a_, b_ in zip(list(ul.coords)[:-1], list(ul.coords)[1:]):
                sg = LineString([a_, b_])
                if sg.distance(Point(bp)) > 2: continue
                t_ = sg.interpolate(sg.project(Point(ic['SS'])))
                if 0.5 < t_.distance(Point(ic['SS'])) < 150 and (abs(t_.x - ic['SS'][0]) < 0.5 or abs(t_.y - ic['SS'][1]) < 0.5):
                    q = [(t_.x, t_.y)]
                    break
        PIPE([ic['SS']] + q if len(q) > 1 else [ic['SS'], q[0]], SS)
        # sıcak: dolaptan ofis içindeki sıcak su ağının başına (merkezi sıcak su)
        poly = ofis_poly(k, kat, 'S')
        gi = izgara.grid_ofis(kat, poly, 5.0, soft=250.0)
        # kullanıcının mevcut soğuk/sıcak hatları: yeni sıcak hat bunların üstünden/yanından yürümesin
        for q_ in _kullanici_hatlari(poly.buffer(80)):
            gi.add_line(q_, 'U')
        hp = (c[0] - ux * 18 - nx_ * (9 + 26), c[1] - uy * 18 - ny_ * (9 + 26))
        tp = termo.tara()['head'][(kat, k)]          # termosifon iptal: kullanıcının sıcak su ağının başı
        pts = gi.route((c[0] - ux * 18 - nx_ * 9, c[1] - uy * 18 - ny_ * 9), tp, sysn='H', turn=20.0, free_end=30.0, max_exp=2_000_000)
        if not pts:
            print('  sıcak su ofis hattı yok', kat, k); pts = [hp, tp]
        PIPE(pts, SIS)
        pipe_label(pts, '3/4"', 6.0, TCAP, ust=f"{YB_H:.0f} MB")
        place_text(c, [f"SD-{kat - 1}{k}"], 8.0, SAY, rmax=40)
        OUT.setdefault(('hat_ic', kat), {})[k] = pts
    # pis su kolonları (kullanıcının MTY ağ uçları)
    dx = D12[0] if kat == 3 else 0.0
    for j, pk in enumerate(PIS_KOL):
        p = (pk['kol'][0] + dx, pk['kol'][1])
        INS("T-KOLON-P", p, 0, 1.0, lay=PSK)
        nm = f"P{j + 1}"
        # onaylı plan düzeni: kolon balonu (daire içinde kolon no) + 'Ø100 PVC' çap yazısı
        bp_ = place_text(p, [nm], 9.0, PSN, rmax=60, prefer=[(-1, 1), (-1, 0), (-1, -1), (1, 1)])
        C((bp_[0], bp_[1]), 14, PSN)
        place_text(p, [f"{pk['cap']} PVC"], 6.0, PSC, rmax=60, prefer=[(1, 0), (1, 1), (1, -1)])
    for sh in ('S1', 'S2'):
        p = W(SAFT[sh]['boru']['SS'], kat, 'S')
        place_text(p, [f"Ş{sh[1]} TESİSAT ŞAFTI", "SS / SıS / SİRK"], 6.0, SFT, rmax=90, prefer=[(1, 1), (1, -1), (1, 0)])
    return D, res
