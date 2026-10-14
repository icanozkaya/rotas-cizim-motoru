"""sihhi2 — TEMEL PLANI (altyapı): bina dış hattı + betonarme kolonlar + pis su kolon dipleri → bina dışındaki rögarlar.

Kullanıcı çizimi (SIHHI_ALTIN_REFERANS.md §6, referans/sihhi/10_temel_plan_genel.png):
- rögarlar DOĞU cephesinde bina dışına 110 cm (rögar ekseni), kuzeyden güneye R1, R2, ...; PB son rögarın 506 doğusunda;
- rögarlar arası Ø150 %1 (düşey hat, etiket 34 sağda, 90° döndürülmüş); kolon → rögar Ø125 %1 yatay hat, iki kolon
  aynı hatta toplanabilir; L köşelerde 5 cm 45° pah; etiket "%1 EĞİM / Ø125" hattın üstünde + akış oku;
- "70x70 / h:-70cm" (h 9,6) rögarın sağ üstünde; kolon dipleri P balonlu; başlık "TEMEL PLANI..........ÖLÇEK: 1 / 50".
Rögar ataması (model `rogarlar` boşsa): kolonlar kuzey-güney (y) sırasında 1B kümelenir (DP: sapma toplamı + rögar
cezası, küme yayılımı ≤ 520); her kümenin yatay hattı betonarme kolon/perdeye değmeyen en yakın y'ye kaydırılır.
"""
import math
import os
import pickle
import sys

import ezdxf
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import sema_ortak as O  # noqa: E402
import sema_sembol as S  # noqa: E402

TPX0, TPX1 = 250042.0, 252513.0
PY0, PY1 = -444050.0, -441150.0
CEPHE_ARA = 110.0
PB_ARA = 506.0
ONBELLEK = '/tmp/claude-0/s2/temel_mimari_v3.pkl'


def mimari_zemin():
    """bina dış hattı (Polygon) + betonarme kolon/perde poligonları (zemin, kaynak koordinat)"""
    if os.path.exists(ONBELLEK):
        with open(ONBELLEK, 'rb') as f:
            return pickle.load(f)
    import mimari2 as M2
    A = M2.kayitlar()
    K = M2.Kat(A, 'Z')
    # bina dış hattı: balkon hariç mahaller (duvar ortasına kadar şişirilmiş) → dış duvar yüzüne 12 cm, köşeler dik
    duvar = K.S.intersection(K.bina.buffer(40, join_style=2))
    u = unary_union([duvar, K.bina]).buffer(8, join_style=2).buffer(-8, join_style=2)
    gs = list(getattr(u, 'geoms', [u]))
    g = max(gs, key=lambda q: q.area)
    bina = Polygon(g.exterior).simplify(3.0)
    cols = [c for c in K.cols if c.area > 300]
    out = {'bina': bina, 'cols': cols}
    os.makedirs(os.path.dirname(ONBELLEK), exist_ok=True)
    with open(ONBELLEK, 'wb') as f:
        pickle.dump(out, f)
    return out


def _hat_y(K, xr, engel, diger):
    """kümenin ortak yatay hattı için y: betonarme kolon/perdeye ve başka kümelerin kolonlarına değmeyen,
    medyana en yakın y. Dönüş (y, iniş toplamı) veya None."""
    ys = sorted(k['y'] for k in K)
    med = ys[len(ys) // 2]
    xw = min(k['x'] for k in K)
    for d in sorted(set([0] + [s * t for t in range(5, 305, 5) for s in (1, -1)]), key=abs):
        y = med + d
        if y > max(ys) + 120 or y < min(ys) - 120:
            continue
        gs = [LineString([(xw, y), (xr - 45, y)])] + [LineString([(k['x'], k['y']), (k['x'], y)]) for k in K
                                                       if abs(k['y'] - y) > 1]
        if engel is not None and any(g.intersects(engel) for g in gs):
            continue
        if any(gs[0].distance(Point(q['x'], q['y'])) < 25 for q in diger):
            continue
        return y, sum(abs(k['y'] - y) for k in K)
    return None


def kumele(ks, xr, engel, ceza=350.0, yayilim=520.0):
    """kolonları kuzeyden güneye 1B kümeler (DP): maliyet = iniş boyları + rögar başına ceza; hattı betonarme
    kolon/perdeye değen küme olanaksız. Dönüş: [(kolonlar, hat_y), ...]"""
    ks = sorted(ks, key=lambda k: -k['y'])
    n = len(ks)
    if n == 0:
        return []
    INF = 1e18
    best, prev, ysec = [INF] * (n + 1), [0] * (n + 1), {}
    best[0] = 0.0
    for j in range(1, n + 1):
        for i in range(j):
            grp = ks[i:j]
            if max(k['y'] for k in grp) - min(k['y'] for k in grp) > yayilim or best[i] >= INF:
                continue
            r = _hat_y(grp, xr, engel, ks[:i] + ks[j:])
            if r is None:
                if j - i > 1:
                    continue
                r = (grp[0]['y'], 0.0)       # tek kolon: kendi y'sinde (kaçamıyorsa olduğu gibi)
            c = best[i] + r[1] + ceza
            if c < best[j]:
                best[j], prev[j], ysec[j] = c, i, r[0]
    out = []
    j = n
    while j > 0:
        i = prev[j]
        out.append((ks[i:j], ysec[j]))
        j = i
    return out[::-1]


def rogar_plani(m, mim):
    bina, cols = mim['bina'], mim['cols']
    xe = bina.bounds[2]
    xr = xe + CEPHE_ARA
    kol = [dict(no=k['no'], x=k['x'], y=k['y'], sb=k.get('sb_toplam', 0)) for k in m.get('kolonlar', [])]
    engel = unary_union([c.buffer(4) for c in cols]) if cols else None
    kumeler = kumele(kol, xr, engel)
    rog = []
    for i, (K, secim) in enumerate(kumeler):
        rog.append(dict(no='R%d' % (i + 1), x=xr, y=secim, kolonlar=[k['no'] for k in sorted(K, key=lambda q: O.kno(q['no']))],
                        _K=K, cap_giris='Ø125', cap_cikis='Ø150', egim='%1', olcu_1='70x70', olcu_2='h:-70cm',
                        sb=sum(k['sb'] for k in K)))
    # rögarlar arası en az 160 cm
    for a, b in zip(rog[:-1], rog[1:]):
        if a['y'] - b['y'] < 160:
            b['y'] = a['y'] - 160
    kum = 0
    for r in rog:
        kum += r['sb']
        r['sb_kumulatif'] = kum
    if rog:
        s = rog[-1]
        rog.append(dict(no='PB', x=s['x'] + PB_ARA, y=s['y'], kolonlar=[], _K=[], cap_giris='Ø150', cap_cikis='Ø150',
                        egim='%1', olcu_1='80x80', olcu_2='h:-80cm', sb=0, sb_kumulatif=kum))
    return rog


def _yazi(msp, s, p, h, katman, renk=None, rot=0.0, hiza=None):
    a = {'layer': katman, 'height': h, 'style': S.YAZI_STIL, 'rotation': rot, 'width': S.YAZI_EN}
    if renk is not None:
        a['color'] = renk
    t = msp.add_text(s, dxfattribs=a)
    if hiza:
        t.set_placement(p, align=hiza)
    else:
        t.dxf.insert = p
    return t


def temel_uret(m, cikis):
    import sema as SM
    mim = mimari_zemin()
    rog = rogar_plani(m, mim)
    dx = float(m['proje'].get('temel_ofset', -2629))
    T = lambda p: (p[0] + dx, p[1])  # noqa: E731
    doc = SM.belge()
    msp = doc.modelspace()
    MC = ezdxf.enums.TextEntityAlignment
    L_PIS, L_CAP = 'ROTAS-SIHHI-PIS-SU', 'ROTAS-SIHHI-PIS-SU-CAP'
    # pafta + başlık
    msp.add_lwpolyline([(TPX0, PY0), (TPX1, PY0), (TPX1, PY1), (TPX0, PY1)], close=True, dxfattribs={'layer': 'ROTAS-PAFTA'})
    _yazi(msp, 'TEMEL PLANI..........ÖLÇEK: 1 / 50', (TPX0 + 538, PY0 + 39), 40.0, 'ROTAS-PAFTA-YAZI')
    # mimari: bina dış hattı + betonarme
    msp.add_lwpolyline([T(p) for p in mim['bina'].exterior.coords], close=True, dxfattribs={'layer': 'ROTAS-MIMARI'})
    for c in mim['cols']:
        msp.add_lwpolyline([T(p) for p in c.exterior.coords], close=True, dxfattribs={'layer': 'ROTAS-MIMARI'})
    cizgiler, alanlar = [], [c.buffer(2) for c in mim['cols']]
    kol = {k['no']: k for k in m.get('kolonlar', [])}

    def hat(pts):
        pts = [T(p) for p in pts]
        msp.add_lwpolyline(pts, dxfattribs={'layer': L_PIS})
        cizgiler.append(LineString(pts))

    def egim_et(p, q, cap, dikey=False):
        mx, my = (p[0] + q[0]) / 2 + dx, (p[1] + q[1]) / 2
        if dikey:
            e1 = _yazi(msp, cap, (mx + 18, my), 12.0, L_CAP, renk=2, rot=90.0, hiza=MC.BOTTOM_CENTER)
            e2 = _yazi(msp, '%1 EĞİM', (mx + 40, my), 12.0, L_CAP, renk=2, rot=90.0, hiza=MC.BOTTOM_CENTER)
            yon = -1 if q[1] < p[1] else 1
            S.ekle(msp, 'ROTAS-SEMA-EGIM-OKU', (mx + 52, my - 60 * yon), 'ROTAS-SIHHI-SEMBOL', rot=90 * (1 if yon > 0 else -1))
        else:
            e1 = _yazi(msp, '%1 EĞİM', (mx, my + 28), 12.0, L_CAP, renk=2, hiza=MC.BOTTOM_CENTER)
            e2 = _yazi(msp, cap, (mx, my + 7), 12.0, L_CAP, renk=2, hiza=MC.BOTTOM_CENTER)
            yon = 1 if q[0] > p[0] else -1
            S.ekle(msp, 'ROTAS-SEMA-EGIM-OKU', (mx + 52 * yon, my + 20), 'ROTAS-SIHHI-SEMBOL', rot=0 if yon > 0 else 180)
        return e1, e2

    for r in rog:
        if r['no'] == 'PB':
            continue
        K = r['_K']
        y = r['y']
        xw = min(k['x'] for k in K)
        bag = []
        for k in sorted(K, key=lambda q: q['x']):
            if abs(k['y'] - y) <= 1:
                bag.append(k['x'])
                continue
            s = 1 if k['y'] > y else -1
            if k['x'] == xw:   # L köşe, 5 cm 45° pah
                hat([(k['x'], k['y']), (k['x'], y + 5 * s), (k['x'] + 5, y)])
                bag.append(k['x'] + 5)
            else:
                hat([(k['x'], k['y']), (k['x'], y)])
                bag.append(k['x'])
        xs = sorted(set(bag)) + [r['x'] - 45]
        for a, b in zip(xs[:-1], xs[1:]):
            hat([(a, y), (b, y)])
            if b - a >= 150:
                for e in egim_et((a, y), (b, y), 'Ø125'):
                    alanlar.append(_kutu(e))
    # rögarlar ve aralarındaki Ø150
    for i, r in enumerate(rog):
        p = T((r['x'], r['y']))
        S.ekle(msp, 'ROTAS-TEMEL-ROGAR', p, 'ROTAS-SIHHI-ROGAR', attr={'NO': r['no']})
        alanlar.append(box(p[0] - 45, p[1] - 45, p[0] + 45, p[1] + 45))
        if r['no'] == 'PB':
            tp = (p[0] - 45, p[1] - 62)
            e1 = _yazi(msp, r['olcu_1'], tp, 9.6, 'ROTAS-SIHHI-ROGAR-YAZI', renk=8)
            e2 = _yazi(msp, r['olcu_2'], (tp[0], tp[1] - 14), 9.6, 'ROTAS-SIHHI-ROGAR-YAZI', renk=8)
        else:
            e1 = _yazi(msp, r['olcu_1'], (p[0] + 55, p[1] + 30), 9.6, 'ROTAS-SIHHI-ROGAR-YAZI', renk=8)
            e2 = _yazi(msp, r['olcu_2'], (p[0] + 55, p[1] + 16), 9.6, 'ROTAS-SIHHI-ROGAR-YAZI', renk=8)
        alanlar += [_kutu(e1), _kutu(e2)]
        if i + 1 < len(rog):
            q = rog[i + 1]
            if q['no'] == 'PB':
                a, b = (r['x'] + 45, r['y']), (q['x'] - 45, q['y'])
                hat([a, b])
                for e in egim_et(a, b, 'Ø150'):
                    alanlar.append(_kutu(e))
            else:
                a, b = (r['x'], r['y'] - 45), (q['x'], q['y'] + 45)
                hat([a, b])
                for e in egim_et(a, b, 'Ø150', dikey=True):
                    alanlar.append(_kutu(e))
    # kolon dipleri + P balonları
    for k in m.get('kolonlar', []):
        p = T((k['x'], k['y']))
        S.ekle(msp, 'ROTAS-TEMEL-PIS-KOLON', p, 'ROTAS-SIHHI-SEMBOL')
        alanlar.append(Point(p).buffer(10))
    for k in m.get('kolonlar', []):
        p = T((k['x'], k['y']))
        b = _balon_yeri(p, cizgiler, alanlar)
        if math.hypot(b[0] - p[0], b[1] - p[1]) > 40:
            u = ((b[0] - p[0]), (b[1] - p[1]))
            L = math.hypot(*u)
            a = (p[0] + u[0] / L * 11, p[1] + u[1] / L * 11)
            c = (b[0] - u[0] / L * 28, b[1] - u[1] / L * 28)
            msp.add_line(a, c, dxfattribs={'layer': 'ROTAS-SEMBOL-KILAVUZ'})
        S.ekle(msp, 'ROTAS-SEMA-KOLON-NO', b, 'ROTAS-SIHHI-KOLON-NO', attr={'NO': k['no']})
        alanlar.append(Point(b).buffer(29))
    # lejant (pafta sağ altı)
    lx, ly = TPX1 - 980, PY0 + 330
    _yazi(msp, 'LEJANT', (lx, ly), 18.0, 'ROTAS-LEJANT', renk=250)
    sat = [('hat', 'PİS SU HATTI (kolon dibi → rögar Ø125 %1, rögarlar arası Ø150 %1)'),
           ('ROTAS-TEMEL-PIS-KOLON', 'PİS SU KOLON DİBİ (zemin döşemesi altı)'),
           ('ROTAS-TEMEL-ROGAR', 'RÖGAR (MUAYENE BACASI) 70x70, PB: PARSEL BACASI')]
    for i, (ad, ack) in enumerate(sat):
        yy = ly - 50 - 70 * i
        if ad == 'hat':
            msp.add_lwpolyline([(lx, yy), (lx + 120, yy)], dxfattribs={'layer': L_PIS})
        else:
            S.ekle(msp, ad, (lx + 60, yy), 'ROTAS-LEJANT', attr={'NO': 'R'} if 'ROGAR' in ad else None,
                   olcek=0.5 if 'ROGAR' in ad else 1.0)
        _yazi(msp, ack, (lx + 150, yy - 5), 11.0, 'ROTAS-LEJANT', renk=250)
    os.makedirs(os.path.dirname(cikis), exist_ok=True)
    doc.saveas(cikis)
    ek = {'cati_alani_m2': round(mim['bina'].area / 1e4, 1), 'cephe_x': round(mim['bina'].bounds[2], 1),
          'rogar_x': round(mim['bina'].bounds[2] + CEPHE_ARA, 1), 'dxf': cikis}
    rog_out = [{k: v for k, v in r.items() if not k.startswith('_')} for r in rog]
    return rog_out, ek


def _kutu(e):
    import denetle as D
    pg = D.yazi_poligonu(e)
    return pg if pg is not None else Point(0, 0).buffer(0.1)


def _balon_yeri(p, cizgiler, alanlar):
    for r in (55, 70, 85, 100, 120):
        for a in (90, 45, 135, 0, 180, 270, 315, 225):
            c = (p[0] + r * math.cos(math.radians(a)), p[1] + r * math.sin(math.radians(a)))
            d = Point(c).buffer(30)
            if any(d.intersects(g) for g in cizgiler) or any(d.intersects(g) for g in alanlar):
                continue
            return c
    return (p[0], p[1] + 60)


sys.path.insert(0, O.KOK + '/motor/deneme/denetim')
