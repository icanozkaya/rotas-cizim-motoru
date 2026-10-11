"""Revizyon kontrolleri: kolon/şaft çakışması, dikey geçiş-kiriş, boşta uç, aynı sistem kesişme, devre kesişmesi."""
import math
from shapely.geometry import LineString, Point, Polygon, MultiLineString
from shapely.ops import unary_union
import cg2_geo as G

FLOOR_DX = [0.0, 1250.0, 2500.0]


def _shift(g, dx, dy):
    from shapely import affinity
    return affinity.translate(g, dx, dy)


def run(NET, NODES, HDY):
    rep = []
    cols = G.col_polys()
    shafts = G.SHAFT_BOX
    # 1) kolon ve şaft çakışması (her kat, sıhhi ve ısıtma paftaları)
    for n in NET:
        ls = LineString(n['pts'])
        for dx in FLOOR_DX + [3750.0]:
            for dy in (0.0, HDY):
                for c in cols:
                    cc = _shift(c, dx, dy)
                    if ls.intersects(cc) and ls.intersection(cc).length > 0.05:
                        if n['sys'] == 'A' and dy == 0:
                            pass
                        rep.append(('KOLON ÇAKIŞMASI', n['sys'], n['lay'], [round(v) for v in cc.bounds]))
                for s in shafts:
                    ss = _shift(s, dx, dy)
                    if ls.intersects(ss) and ls.intersection(ss).length > 0.05:
                        rep.append(('ŞAFT ÇAKIŞMASI', n['sys'], n['lay'], [round(v) for v in ss.bounds]))
    # 2) boşta uç: her boru ucu ya bir düğüme ya da başka bir borunun üzerine oturmalı
    pts_nodes = [p for p, _ in NODES]
    by_sys = {}
    for n in NET:
        by_sys.setdefault(n['sys'], []).append(n)
    for n in NET:
        for end in (n['pts'][0], n['pts'][-1]):
            ok = any(math.hypot(end[0] - q[0], end[1] - q[1]) < 0.3 for q in pts_nodes)
            if not ok:
                for m in by_sys[n['sys']]:
                    if m is n:
                        continue
                    if LineString(m['pts']).distance(Point(end)) < 0.3:
                        ok = True
                        break
            if not ok:
                rep.append(('BOŞTA UÇ', n['sys'], n['lay'], (round(end[0], 1), round(end[1], 1))))
    # 3) yerden ısıtma devreleri birbirini kesmemeli / kendini kesmemeli
    H = [n for n in NET if n['sys'] in ('H', 'K')]
    for i, a in enumerate(H):
        la = LineString(a['pts'])
        if a['sys'] == 'H' and not la.is_simple:
            rep.append(('DEVRE KENDİNİ KESİYOR', a['lay'], (round(a['pts'][0][0]), round(a['pts'][0][1]))))
        for b in H[i + 1:]:
            lb = LineString(b['pts'])
            if la.distance(lb) < 2.0:
                inter = la.intersection(lb)
                # ortak kollektör ucu hariç
                rep.append(('ISITMA BORULARI YAKIN/KESİŞİYOR (<2 cm)', a['lay'], b['lay'],
                            str(inter)[:60] if not inter.is_empty else 'mesafe %.1f' % la.distance(lb)))
    # 4) aynı sistem boru kesişmesi (bağlantı olmayan)
    for sysn in ('S', 'P'):
        L_ = [n for n in NET if n['sys'] == sysn]
        for i, a in enumerate(L_):
            la = LineString(a['pts'])
            for b in L_[i + 1:]:
                lb = LineString(b['pts'])
                if a['lay'] != b['lay']:
                    x = la.intersection(lb)
                    if not x.is_empty:
                        rep.append(('SOĞUK-SICAK KESİŞME', a['lay'], b['lay'], str(x)[:70]))
    # 5) dikey geçişler kiriş bandında mı?
    for nm, p, r in (('PK', G.PK, 7), ('MK', G.MK, 5), ('DBK', G.DBK, 3), ('ADK', G.ADK, 3)):
        c = Point(p).buffer(r)
        for b in G.BEAMS:
            if c.intersects(b):
                rep.append(('KİRİŞ BANDINDA DİKEY GEÇİŞ', nm, [round(v) for v in b.bounds]))
        for cc in cols:
            if c.intersects(cc):
                rep.append(('KOLON İÇİNDE DİKEY GEÇİŞ', nm))
    return rep
