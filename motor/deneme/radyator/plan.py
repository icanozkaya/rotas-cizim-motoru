# -*- coding: utf-8 -*-
"""Radyatör tesisatı kat planı (R2, kolektörlü): temsili mimari (pencere/balkon kapısı, kapı kanadı, tefriş),
kolektör dolabı, her radyatöre ayrı PEX gidiş-dönüş çifti (duvar boyu, kapıdan), MTY radyatör blokları,
merkezi sistemde hol duvarında KALORİMETRE SETİ (küresel vana + pislik tutucu + kalorimetre + balans vanası + küresel vana),
kombili sistemde mutfak dış duvarında kombi. Etiketler boş yere yerleşir (yazı altına maske)."""
import math
from shapely.geometry import LineString, Point, Polygon, box as sbox
from shapely.ops import unary_union, substring
import ag
from ag import GEN, DER, YA0, YA1, CEK, HP, HF
import ciz as C
import semb

DIS = 25.0
MIM, PEN, TEF = 'ROTAS-MIMARI-TEMSILI', 'ROTAS-MIMARI-PENCERE', 'ROTAS-MIMARI-TEFRIS'
KOLK, SEM, SIN = 'ROTAS-ISITMA-KOLEKTOR', 'ROTAS-ISITMA-SEMBOL', 'ROTAS-ISITMA-SINYAL'
SET_ELEMAN = [  # (gidiş sembolü, dönüş sembolü, numara) – kolondan daireye sırayla
    ('kuresel_vana', 'kuresel_vana', '1'),
    ('pislik_tutucu', None, '2'),
    ('kalorimetre_sensor', 'kalorimetre_km', '3'),
    (None, 'balans_vanasi', '4'),
    ('kuresel_vana', 'kuresel_vana', '5'),
]


def _okunur(th):
    th = (th + 180) % 360 - 180
    if th > 90.01 or th <= -90:
        th += 180
    return (th + 180) % 360 - 180


# ---------------------------------------------------------------------- mimari (temsili)
def mimari(cz, pl_list, dx, dy, sistem):
    T = lambda p: (p[0] + dx, p[1] + dy)
    dis = unary_union([sbox(0, 0, GEN, DER), sbox(GEN, YA0, ag.GENIS_TOP - GEN, DER), sbox(ag.GENIS_TOP - GEN, 0, ag.GENIS_TOP, DER)])
    hatlar = [LineString(list(dis.exterior.coords))]
    for pl in pl_list:
        for o in pl['odalar']:
            x0, y0, x1, y1 = o['r']
            hatlar.append(LineString([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]))
    hatlar.append(LineString([(GEN, YA0), (ag.GENIS_TOP - GEN, YA0)]))
    birlesik = unary_union(hatlar)
    bosluk = []
    for pl in pl_list:
        for a, b, yy in pl['kapilar']:
            bosluk.append(sbox(a, yy - 1, b, yy + 1))
        for o in pl['odalar']:
            for p in o.get('pencere', []):
                bosluk.append(sbox(p['a'], p['y'] - DIS - 2, p['b'], p['y'] + DIS + 2))
    bosluk.append(sbox(1340.0, YA0 - 1, 1460.0, YA0 + 1))
    for x in (GEN, ag.GENIS_TOP - GEN):
        bosluk.append(sbox(x - 1, 480, x + 1, 570))
    ic = birlesik.difference(unary_union(bosluk))
    dd = LineString(dis.buffer(DIS, join_style='mitre').exterior.coords).difference(unary_union(bosluk))
    for g in [ic, dd]:
        for ls in getattr(g, 'geoms', [g]):
            if ls.length > 0.5:
                cz.pl([T(p) for p in ls.coords], MIM, engel=False)
    for pl in pl_list:
        for o in pl['odalar']:
            for p in o.get('pencere', []):
                a, b, yy = p['a'], p['b'], p['y']
                s = 1 if yy >= DER - 1 else -1
                for x in (a, b):
                    cz.pl([T((x, yy)), T((x, yy + s * DIS))], PEN, engel=False)
                if p['tip'] == 'P':
                    for f in (0.35, 0.65):
                        cz.pl([T((a, yy + s * DIS * f)), T((b, yy + s * DIS * f))], PEN, engel=False)
                else:                                   # balkon kapısı: eşik + kanat
                    cz.pl([T((a, yy + s * DIS * 0.5)), T((b, yy + s * DIS * 0.5))], PEN, engel=False)
                    w = b - a
                    arc = [T((a + w * math.sin(math.radians(90 * i / 12)), yy - s * w * math.cos(math.radians(90 * i / 12))))
                           for i in range(13)]
                    cz.pl([T((a, yy)), T((a, yy - s * w))] , MIM, engel=False)
                    cz.pl(arc, MIM, engel=False)
    for pl in pl_list:
        for o in pl['odalar']:
            if not o.get('kapi'):
                continue
            a, b, yy = o['kapi']
            ic_yon = 1 if o['sira'] == 'N' else -1
            w = b - a
            mente = o['mente']
            karsi = b if abs(mente - a) < 1e-6 else a
            cz.pl([T((mente, yy)), T((mente, yy + ic_yon * w))], MIM, engel=False)
            arc = []
            for i in range(13):
                t = math.radians(90 * i / 12)
                arc.append(T((mente + (karsi - mente) * math.sin(t), yy + ic_yon * w * math.cos(t))))
            cz.pl(arc, MIM, engel=False)
            for x0, y0, x1, y1, ad in o.get('tefris', []):
                if ad == 'KOMBİ':
                    continue
                cz.pl([T((x0, y0)), T((x1, y0)), T((x1, y1)), T((x0, y1))], TEF, kapali=True, engel=False)
        oa = [o for o in pl['odalar'] if o['sira'] == 'A'][0]
        for x0, y0, x1, y1, ad in oa.get('tefris', []):
            cz.pl([T((x0, y0)), T((x1, y0)), T((x1, y1)), T((x0, y1))], TEF, kapali=True, engel=False)
    for x in (GEN, ag.GENIS_TOP - GEN):
        s = 1 if x == GEN else -1
        cz.pl([T((x, 570)), T((x + s * 90, 570))], MIM, engel=False)
    mx0, mx1, my0, my1 = 1330.0, 1470.0, 640.0, 960.0
    cz.pl([T((mx0, my0)), T((mx1, my0)), T((mx1, my1)), T((mx0, my1))], MIM, kapali=True, engel=False)
    cz.pl([T((1400, my0)), T((1400, my1))], MIM, engel=False)
    for k in range(1, 11):
        yy = my0 + (my1 - my0) * k / 11
        cz.pl([T((mx0, yy)), T((1395, yy))], MIM, engel=False)
        cz.pl([T((1405, yy)), T((mx1, yy))], MIM, engel=False)
    cz.yazi(T((1400, 610)), 'MERDİVEN HOLÜ', 9, MIM)


def tefris_yazilari(cz, pl, dx, dy):
    for o in pl['odalar']:
        for x0, y0, x1, y1, ad in o.get('tefris', []):
            if ad == 'KOMBİ':
                continue
            c = ((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy)
            rot = 90.0 if (y1 - y0) > (x1 - x0) * 1.3 else 0.0
            k = Polygon(cz.kutu_yazi(c, ad, 6.0, 'MC', rot))
            if cz.bos_mu(k):
                cz.yazi(c, ad, 6.0, TEF, rot=rot, maske=False, renk=8)


# ---------------------------------------------------------------------- yardımcılar
def _ofs(pts, d):
    g = LineString(pts).offset_curve(d, join_style='mitre', mitre_limit=10)
    return [tuple(p) for p in g.coords]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _rad_uclari(r):
    """radyatörün bağlantı uçları: (vana_payı, rakor_payı, vana_b, rakor_b, banyopan_mi, ölçek)"""
    L = r['L']
    if r['tip'] == 'Banyopan':
        s = L / 32.0
        return 16.0 * s, 16.0 * s, CEK + 3.0 * s, CEK + 3.0 * s, True, s
    s = L / 100.0
    return 54.7 * s, 50.7 * s, CEK + 12.0, CEK + 7.3, False, s


def devre_cizgileri(dv):
    """devre ekseni → gidiş (sol ofset) / dönüş (sağ ofset) çizgileri, radyatör bağlantısı ve blok yerleşimi"""
    r = dv['rad']
    pts = dv['pts']
    g, d = _ofs(pts, HP), _ofs(pts, -HP)
    c, t, n = r['c'], r['t'], r['n']
    a = lambda p: _dot((p[0] - c[0], p[1] - c[1]), t)
    b = lambda p: _dot((p[0] - c[0], p[1] - c[1]), n)
    u = 1.0 if a(pts[-1]) - a(pts[-2]) > 0 else -1.0                # son parçanın duvar boyu yönü
    duvar_g = b(g[-1]) < b(d[-1])                                   # gidiş duvar tarafında mı
    pv, pr, bv, br, ban, s = _rad_uclari(r)
    vana_yakinda = duvar_g                                          # duvar tarafı = yakın uç
    a_v = -u * pv if vana_yakinda else u * pv
    a_r = u * pr if vana_yakinda else -u * pr
    P_ = lambda aa, bb: (c[0] + aa * t[0] + bb * n[0], c[1] + aa * t[1] + bb * n[1])

    def bagla(cs, aa, bb):
        bl = b(cs[-1])
        return cs[:-1] + [P_(aa, bl), P_(aa, bb)]
    g = bagla(g, a_v , bv)
    d = bagla(d, a_r, br)
    # blok: yerel y → n, yerel x → e = rot90cw(n)
    rot = math.degrees(math.atan2(n[1], n[0])) - 90.0
    e = (n[1], -n[0])
    yon_vr = 1.0 if a_r > a_v else -1.0                              # vanadan rakora t yönü
    sx_sign = 1.0 if yon_vr * _dot(t, e) > 0 else -1.0
    if ban:
        ins = P_(a_v + yon_vr * 4.0 * s, CEK)
        blok = dict(ad='MTY-RADYATOR Banyopan', p=ins, rot=rot, sx=sx_sign * s, sy=s)
    else:
        blok = dict(ad='MTY-RADYATOR Panel', p=P_(a_v, CEK), rot=rot, sx=sx_sign * s, sy=1.0)
    return g, d, blok


# ---------------------------------------------------------------------- boru + cihaz çizimi
def borular(cz, pl, dx, dy, bilgi):
    T = lambda p: (p[0] + dx, p[1] + dy)
    kayit = {}
    tum = []
    for dv in pl['devreler']:
        g, d, blok = devre_cizgileri(dv)
        kayit[dv['no']] = dict(g=g, d=d, blok=blok, dv=dv)
        tum += [g, d]
    # besleme (kolon/kombi → kolektör)
    bg, bd = _ofs(pl['besleme'], HF), _ofs(pl['besleme'], -HF)
    kayit['besleme'] = dict(g=bg, d=bd)
    for k, v in kayit.items():
        cz.pl([T(p) for p in v['g']], C.GID, w=1.2 if k != 'besleme' else 1.6)
        cz.pl([T(p) for p in v['d']], C.DON, w=1.2 if k != 'besleme' else 1.6, ltscale=0.4)
    # kolektör dolabı
    kk = pl['kolektor']
    W = kk['x1'] - kk['x0']
    ad = semb.kolektor_dolabi(cz.doc, W, kk['n'])
    cz.msp.add_blockref(ad, T((kk['x0'], kk['y0'])), dxfattribs={'layer': KOLK})
    cz.engel.append(sbox(*T((kk['x0'], kk['y0'])), *T((kk['x1'], kk['y1']))).exterior)
    # radyatörler
    for no, v in kayit.items():
        if no == 'besleme':
            continue
        r = v['dv']['rad']; b = v['blok']
        cz.blok(b['ad'], T(b['p']), b['rot'], b['sx'], b['sy'], 'ROTAS-RADYATOR')
        cz.engel.append(LineString([T(p) for p in (v['g'][-1], v['d'][-1])]))
    return kayit


def radyator_etiketleri(cz, pl, kayit, dx, dy, kat_on):
    """radyatör tipi/kapasite + mahal no + devre no: radyatörün oda tarafında boş yere (maske altı boru kesilmez)"""
    for no, v in kayit.items():
        if no == 'besleme':
            continue
        r = v['dv']['rad']
        m = r['m']
        t1 = (f"HAVLUPAN {r['boy'] * 1000:.0f} - {r['ver']:.0f} W" if r['tip'] == 'Banyopan'
              else f"{r['model']}x{r['boy'] * 1000:.0f} - {r['ver']:.0f} W")
        t2 = f"{kat_on}{m['no']}  D{no}"
        c, t, n = r['c'], r['t'], r['n']
        yer = None
        for bb in (40, 58, 76, 95, 115, 140):
            for aa in (0, -40, 40, -80, 80):
                p1 = (c[0] + aa * t[0] + bb * n[0] + dx, c[1] + aa * t[1] + bb * n[1] + dy)
                p2 = (p1[0], p1[1] - 11) if n[1] >= -0.5 else (p1[0], p1[1] + 11)
                k1 = Polygon(cz.kutu_yazi(p1, t1, 7.0)); k2 = Polygon(cz.kutu_yazi(p2, t2, 6.0))
                if cz.bos_mu(k1) and cz.bos_mu(k2):
                    yer = (p1, p2); break
            if yer:
                break
        if yer is None:
            p1 = (c[0] + 40 * n[0] + dx, c[1] + 40 * n[1] + dy); p2 = (p1[0], p1[1] - 11)
            yer = (p1, p2)
        cz.yazi(yer[0], t1, 7.0, 'ROTAS-RADYATOR')
        cz.yazi(yer[1], t2, 6.0, 'ROTAS-RADYATOR')


def devre_etiketleri(cz, pl, kayit, A_prc, dx, dy):
    """her devreye bir 'D3 1454W-Ø16x2' etiketi (MTY-RADYATOR CAP), oda içindeki en uzun boş parçada"""
    h = 7.0
    T = lambda p: (p[0] + dx, p[1] + dy)
    for no, v in kayit.items():
        if no == 'besleme':
            continue
        prc = [p for p in A_prc if p.get('devre') == no]
        if not prc:
            continue
        p = prc[0]
        _etiket(cz, v['dv']['pts'], f"D{no} {p['Q']:.0f}W-{p['dn']}", h, T, HP, ilk=2)
    pb = [p for p in A_prc if p['tur'] == 'giris']
    if pb:
        _etiket(cz, pl['besleme'], f"{pb[0]['Q']:.0f}W-{pb[0]['dn']}", 8.0, T, HF, ilk=0)


def _etiket(cz, pts, txt, h, T, yari, ilk=0):
    tw = len(txt) * h * 0.60 * 0.85 + 6
    segs = list(zip(pts[:-1], pts[1:]))[ilk:]
    segs = sorted(segs, key=lambda s: -math.dist(*s))
    for a, b in segs[:6]:
        Ls = math.dist(a, b)
        if Ls < tw + 12:
            continue
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        th = _okunur(ang)
        u = (math.cos(math.radians(th)), math.sin(math.radians(th)))
        nn = (-u[1], u[0])
        for f in (0.5, 0.3, 0.7, 0.15, 0.85):
            cc = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            for yon in (1, -1):
                o = (cc[0] + nn[0] * (yari + 2.0 + h * 0.75) * yon, cc[1] + nn[1] * (yari + 2.0 + h * 0.75) * yon)
                k = Polygon(cz.kutu_yazi(T(o), txt, h, 'MC', th))
                if not cz.bos_mu(k):
                    continue
                cz.yazi(T(o), txt, h, C.CAPK, rot=th)
                return True
    return False


def cihazlar(cz, pl, dx, dy, P, kat_on):
    T = lambda p: (p[0] + dx, p[1] + dy)
    if pl['sistem'] == 'merkezi':
        kx, ky = pl['kolon']
        bes = pl['besleme']
        bg, bd = _ofs(bes, HF), _ofs(bes, -HF)
        xg, xd = bg[0][0], bd[0][0]
        # kolon (gidiş + dönüş) – MTY-BORU KOLON
        cz.blok('MTY-BORU KOLON', T((kx, ky)), 0.0, 0.6, 0.6, 'ROTAS-CIHAZ',
                ozn={'K': 'K1' if not pl.get('ayna') else 'K2'}, ozn_h={'K': 12.0}, ozn_rot=0.0,
                ozn_konum={'K': T((kx + (-45 if not pl.get('ayna') else 45), ky + 5))}, maske=True)
        # kalorimetre dolabı (sıva altı, hol duvarı) + set
        y0, y1 = min(pl['set_y']) - 25, max(pl['set_y']) + 25
        x0, x1 = min(xg, xd) - 14, max(xg, xd) + 14
        cz.pl([T((x0, y0)), T((x1, y0)), T((x1, y1)), T((x0, y1))], 'ROTAS-CIHAZ', kapali=True, engel=False)
        for (sg, sd, no), yy in zip(SET_ELEMAN, pl['set_y']):
            for sm, xx in ((sg, xg), (sd, xd)):
                if not sm:
                    continue
                rot = -90.0
                cz.maske([T((xx - 7, yy - 8)), T((xx + 7, yy - 8)), T((xx + 7, yy + 8)), T((xx - 7, yy + 8))])
                e = semb.ciz(cz.msp, sm, T((xx, yy)), rot=rot, olcek=0.6, kat=SEM)
                cz.engel.append(sbox(*T((xx - 7, yy - 8)), *T((xx + 7, yy + 8))).exterior)
            if sg == 'kalorimetre_sensor':
                cz.pl([T((xg, yy)), T((xd, yy))], SIN, engel=False, ltscale=0.3)
        tx = x1 + 6 if not pl.get('ayna') else x0 - 6
        al = 'ML' if not pl.get('ayna') else 'MR'
        cz.yazi(T((tx, y1 - 6)), 'KS - KALORİMETRE SETİ', 7.0, 'ROTAS-CIHAZ', al=al)
        cz.yazi(T((tx, y1 - 17)), '(SAYAÇ DOLABI, SIVA ALTI)', 6.0, 'ROTAS-CIHAZ', al=al)
        for (sg, sd, no), yy in zip(SET_ELEMAN, pl['set_y']):
            ad = {'1': 'KÜRESEL VANA', '2': 'PİSLİK TUTUCU', '3': 'KALORİMETRE', '4': 'BALANS VANASI', '5': 'KÜRESEL VANA'}[no]
            cz.yazi(T((tx, yy)), f'{no}- {ad}', 5.5, 'ROTAS-CIHAZ', al=al)
    else:
        kb = pl['kombi']
        p = kb['p']
        if kb.get('ayna'):
            cz.blok('MTY-KOMBİ', T((p[0], p[1] + 30.0)), 180.0, 1.0, 1.0, 'ROTAS-CIHAZ')
            tx, al = p[0] - 52 + 48, 'ML'
        else:
            cz.blok('MTY-KOMBİ', T(p), 0.0, 1.0, 1.0, 'ROTAS-CIHAZ')
            tx, al = p[0] - 4, 'MR'
        cz.engel.append(sbox(*T((min(p[0], p[0] + 48) - (48 if kb.get('ayna') else 0), p[1])),
                             *T((max(p[0], p[0] + 48) - (48 if kb.get('ayna') else 0), p[1] + 30))).exterior)
        cz.yazi(T((tx, 28.0)), f"HERMETİK KOMBİ {P['kombi']['kapasite_kW']} kW", 7, 'ROTAS-CIHAZ', al=al)
    kk = pl['kolektor']
    cx = (kk['x0'] + kk['x1']) / 2
    cz.yazi(T((cx, kk['y0'] - 14)), f"KD - KOLEKTÖR DOLABI {kk['n']} AĞIZ", 6.5, KOLK)


def mahal_etiketleri(cz, pl, dx, dy, kat_on):
    for o in pl['odalar']:
        m = o['m']
        x0, y0, x1, y1 = o['r']
        s = 0.55 if o['sira'] == 'A' else 0.8
        w = 72 * s
        best = None
        cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
        for ddx in [0, -60, 60, -120, 120, -180, 180, -240, 240, -300, 300, -360, 360]:
            for ddy in [0, -40, 40, -80, 80, -120, 120]:
                cx, cy = cx0 + ddx, cy0 + ddy
                kb = sbox(cx - w / 2 + dx, cy - 59 * s + dy, cx + w / 2 + dx, cy + 42 * s + dy)
                if kb.bounds[0] < x0 + dx + 5 or kb.bounds[2] > x1 + dx - 5 or kb.bounds[1] < y0 + dy + 5 or kb.bounds[3] > y1 + dy - 5:
                    continue
                if cz.bos_mu(kb):
                    best = (cx, cy, kb); break
            if best:
                break
        if not best:
            cx, cy = cx0, cy0
            best = (cx, cy, sbox(cx - w / 2 + dx, cy - 59 * s + dy, cx + w / 2 + dx, cy + 42 * s + dy))
        cx, cy, kb = best
        cz.maske(list(kb.exterior.coords)[:4])
        cz.blok('MTY-RADYATOR MAHAL', (cx + dx, cy + dy), 0, s, s, 'ROTAS-MAHAL',
                ozn={'MAHAL_001': m['ad'], 'NO_001': f"{kat_on}{m['no']}", 'DERECE_001': f"{m['ti']:.0f}°C",
                     'ISIKAYBI_001': f"{m['q']:.0f} W", 'ALAN': ''})
        cz.yazilar.append(kb)
