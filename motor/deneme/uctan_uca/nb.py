"""UÇTAN UCA SIHHİ TESİSAT DENEMESİ — new_block.dxf (Metra, Z+2, 9 daire).

Akış: yalın mimari (MKDU0) -> mahal / ıslak hacim / armatür / betonarme kolon tanıma (mimari.py)
      -> pis su kolonu yerleşimi + kat içi pis su (armatürden kolona doğrudan, eğik) + temiz/sıcak su (A* router)
      -> temel planı (kolon dipleri + rögarlar) -> açılımlı kolon şeması (p2/gsheet) + rögar şeması + yağmur şeması
      -> DXF (p2 emit, sonra ROTAS- katman öneki, AC1032).
Mevcut p2 dosyaları DEĞİŞTİRİLMEZ, yalnız import edilir.  Çalıştır:  python3 nb.py [params.json]
"""
import json, math, os, pickle, runpy, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = '/home/claude/rotas-cizim-motoru'
sys.path.insert(0, HERE)
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import importlib.util
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
import mimari as M
import cad
from cad import L, PL, C, T, RECT, ARROW, push, pop, MOVE, VANA, CEKVALF, PISLIK_TUTUCU, TEMIZLEME_KAPAGI
import mtyblk
import gp
from gp import CS, CH, PS, PST, TSC, PSC, YL, YC, VN, CD, YZ, cap_temiz, cap_pis, fmt, dn_temiz, dn_sb
import gsheet as GS
from gsheet import wl, dline

_spec = importlib.util.spec_from_file_location('router_p2', REPO + '/motor/p2/router.py')
RT = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(RT)

# ------------------------------------------------------------------ parametreler (tasarım kararları; JSON ile değiştirilebilir)
PRM = dict(
    rogar_cephe='D',            # rögarlar binanın doğu cephesinde (1033. Sokak / asfalt yol tarafı - yerleşim planı)
    depo='cati', depo_V=3.0,    # 9 BB <= 10 -> 3 m³, çatı deposu (hidrofor gerekmez)
    kombi_kw=24,
    cikti=REPO + '/proje/denemeler/uctan_uca/NB_SIHHI_DENEME.dxf',
)
if len(sys.argv) > 1 and sys.argv[1].endswith('.json'):
    PRM.update(json.load(open(sys.argv[1])))

FL = M.FLOORS
FNAME = {'Z': 'ZEMİN KAT', '1': '1. KAT', '2': '2. KAT'}
KOT = {'Z': '±0,00', '1': '+3,00', '2': '+6,00'}
SLOT, FH = 2500.0, 2800.0
SLOTS = {'ANTET': 0, 'YER': 1, 'T': 2, 'Z': 3, '1': 4, '2': 5}
SX0 = 6 * SLOT + 100.0          # şema başlangıcı
SB = dict(gp.SB)
YB = dict(gp.YB)
YBS = dict(gp.YBS)
WET_TYPE = {'banyo': 'BANYO', 'wc+banyo': 'BANYO', 'wc-lvb.': 'WC', 'duş': 'DUŞ', 'mutfak': 'MUTFAK'}


def sx(k):
    """kaynak -> pafta dönüşümü (kat k penceresi kendi slotuna)"""
    o = 0.0 if k == 'T' else M.OFF[k]
    return MOVE(SLOTS[k] * SLOT + 245.0 - (M.WIN_Z[0] + o), 300.0 - M.WIN_Z[1])


# ================================================================== 1. MİMARİ + TANIMA
A = M.extract()
Z_LABS = None
DATA = {}


def floor_data(k):
    global Z_LABS
    R = M.recs_in(A, M.win(k))
    labs = M.labels(R, k)
    if k == 'Z':
        Z_LABS = labs
    else:                                       # zeminde olup bu katta eksik mahal etiketi -> kaydırarak ekle
        for x, y, t in Z_LABS:
            q = (x + M.OFF[k], y)
            other = any(a[0] == 'T' and a[2][0].strip() in M.ROOM_WORDS + ('yüklük',) and a[2][0].strip() != t and
                        math.hypot(a[1][-1][0] - q[0], a[1][-1][1] - q[1]) < 90 for a in R)
            if not other and not any(t2 == t and math.hypot(x2 - q[0], y2 - q[1]) < 60 for x2, y2, t2 in labs):
                labs.append((q[0], q[1], t))
    wet, W = M.wet_rooms(R, labs)
    F = M.fixtures(R, wet, W)
    cols = M.columns(R)
    digits = [(a[1][-1], int(a[2][0].strip())) for a in R if a[0] == 'T' and a[2][0].strip().isdigit()
              and a[2][1] >= 20 and len(a[2][0].strip()) == 1]
    yb = [a[1][0] for a in R if a[0] == 'T' and 'yağmur' in a[2][0]]
    return dict(R=R, labs=labs, wet=wet, W=W, F=F, cols=cols, digits=digits, yb=yb)


for k in FL:
    DATA[k] = floor_data(k)

# ------------------------------------------------------------------ daireler: ıslak hacim -> en yakın mutfak (görünürlük) -> daire no
def assign_daire(d):
    mut = [w for w in d['wet'] if w['name'] == 'mutfak']
    for m in mut:
        m['daire'] = min(d['digits'], key=lambda q: math.hypot(q[0][0] - m['xy'][0], q[0][1] - m['xy'][1]))[1]
        m['entry'] = min(d['digits'], key=lambda q: math.hypot(q[0][0] - m['xy'][0], q[0][1] - m['xy'][1]))[0]
    for w in d['wet']:
        if w['name'] != 'mutfak':
            m = min(mut, key=lambda m_: math.hypot(m_['xy'][0] - w['xy'][0], m_['xy'][1] - w['xy'][1]))
            w['daire'], w['entry'] = m['daire'], m['entry']
    for f in d['F']:
        if f['kind'] == 'KOMBI':        # kombi -> en yakın eviyenin dairesi (balkondaki kombiler mutfak etiketine uzak)
            ev = [e for e in d['F'] if e['kind'] == 'EV']
            e = min(ev, key=lambda e_: math.hypot(e_['c'][0] - f['c'][0], e_['c'][1] - f['c'][1]))
            f['daire'] = e['room']['daire']
        elif f['room']:
            f['daire'] = f['room']['daire']


for k in FL:
    assign_daire(DATA[k])


# ------------------------------------------------------------------ pis su kolonu yeri (ıslak hacim köşesi, zemin katta bulunur; üst katlar aynı hizada)
def near_wall(W, p, dirs=((1, 0), (-1, 0), (0, 1), (0, -1))):
    best = min(((W.ray(p, d), d) for d in dirs), key=lambda t: t[0])
    return best


def kolon_yeri(d, w):
    W = d['W']
    fx = [f for f in d['F'] if f['room'] is w]
    anchor = None
    for kind in ('WC', 'EV', 'DUS', 'LV'):
        c = [f for f in fx if f['kind'] == kind]
        if c:
            anchor = c[0]
            break
    if not anchor:
        return None
    p = anchor['c']
    dirs = ((1, 0), (-1, 0)) if anchor.get('axis') == 'x' else ((0, 1), (0, -1)) if anchor.get('axis') == 'y' else \
        ((1, 0), (-1, 0), (0, 1), (0, -1))
    dist, dn = near_wall(W, p, dirs)
    q = (p[0] + dn[0] * (dist - 10.0), p[1] + dn[1] * (dist - 10.0))       # duvar yüzünden 10 cm
    # duvar boyunca en yakın köşeye (<= 110 cm) git
    along = [(-dn[1], dn[0]), (dn[1], -dn[0])]
    cands = sorted(((W.ray(q, a), a) for a in along), key=lambda t: t[0])
    da, a = cands[0]
    if da <= 110:
        q = (q[0] + a[0] * (da - 10.0), q[1] + a[1] * (da - 10.0))
    elif anchor['kind'] == 'EV':
        q = (q[0] + a[0] * 25.0, q[1] + a[1] * 25.0)
    # betonarme kolon/perde içine düşerse duvar boyunca kolon dışına ötele (>= 15 cm)
    for c in d['cols']:
        if c.buffer(6).contains(Point(q)):
            for s in range(5, 200, 5):
                for sg in (-1, 1):
                    q2 = (q[0] + a[0] * s * sg, q[1] + a[1] * s * sg)
                    if not any(cc.buffer(15).contains(Point(q2)) for cc in d['cols']):
                        q = q2
                        break
                else:
                    continue
                break
    return q


DZ = DATA['Z']
KOLS = []          # dict(name, p (zemin kaynak koord), type, daire_col (zemin daire no))
for w in DZ['wet']:
    q = kolon_yeri(DZ, w)
    if q:
        KOLS.append(dict(p=q, wet=w.get('name'), d0=w['daire'], typ=WET_TYPE[w['name']]))
KOLS.sort(key=lambda c: (c['d0'], {'BANYO': 0, 'DUŞ': 1, 'WC': 2, 'MUTFAK': 3}[c['typ']]))
for i, c in enumerate(KOLS):
    c['name'] = 'P%d' % (i + 1)


def kolon_of(k, w):
    """kat k'deki ıslak hacmin kolonu (zemin kolonlarından en yakın, aynı tip)"""
    q = (w['xy'][0] - M.OFF[k], w['xy'][1])
    cs = [c for c in KOLS if c['typ'] == WET_TYPE[w['name']]]
    return min(cs, key=lambda c: math.hypot(c['p'][0] - q[0], c['p'][1] - q[1]))


# ================================================================== 2. KAT PLANLARI
def copy_arch(k, recs, furn=True):
    for a in recs:
        if a[0] == 'L':
            L(a[1][0], a[1][1], gp.ARC_L)
        elif a[0] in 'PA':
            PL(a[1], gp.ARC_L)
        elif a[0] == 'C':
            C(a[1][0], a[2], gp.ARC_L)
        elif a[0] == 'H':
            PL(a[1], gp.ARC_K)
        elif a[0] == 'T':
            t = a[2][0].replace('\n', ' ').strip()
            if t:
                T(a[1][1] if len(a[1]) > 1 else a[1][0], t, a[2][1], gp.ARC_T, 'MC', a[2][2] or 0)


def pis_ag(k, d, w, kp):
    """ıslak hacim pis su ağı: kolondan başlayarak en yakın armatür ağaca (en yakın boru noktasına) bağlanır -
    armatürden kolona doğrudan, eğik hatlar (kullanıcının tarzı). Dönüş: toplam SB"""
    fx = [f for f in d['F'] if f['room'] is w and f['kind'] in SB]
    if not fx:
        return 0, False
    nodes = [kp]
    edges = []               # (a_idx, b_idx) b akış yönünde (kolona yakın)
    up = {}
    rem = list(fx)
    fidx = {}
    while rem:
        best = None
        for f in rem:
            P_ = Point(f['c'])
            cand = [(math.hypot(f['c'][0] - kp[0], f['c'][1] - kp[1]), None, kp)]
            for ei, (a, b) in enumerate(edges):
                ls = LineString([nodes[a], nodes[b]])
                q = ls.interpolate(ls.project(P_))
                cand.append((q.distance(P_) * 1.0, ei, (q.x, q.y)))
            dd, ei, q = min(cand, key=lambda t: t[0])
            if best is None or dd < best[0]:
                best = (dd, f, ei, q)
        dd, f, ei, q = best
        rem.remove(f)
        nodes.append(f['c']); fi = len(nodes) - 1; fidx[fi] = f
        if ei is None:
            edges.append((fi, 0))
        else:
            a, b = edges[ei]
            if math.hypot(q[0] - nodes[b][0], q[1] - nodes[b][1]) < 2:
                edges.append((fi, b))
            elif math.hypot(q[0] - nodes[a][0], q[1] - nodes[a][1]) < 2:
                edges.append((fi, a))
            else:
                nodes.append(q); qi = len(nodes) - 1
                edges[ei] = (a, qi); edges.append((qi, b)); edges.append((fi, qi))
    # yukarı akış toplamları
    def upstream(n):
        s, wc = 0.0, False
        if n in fidx:
            s += SB[fidx[n]['kind']]; wc = wc or fidx[n]['kind'] == 'WC'
        for a, b in edges:
            if b == n:
                s2, w2 = upstream(a)
                s += s2; wc = wc or w2
        return s, wc
    tot, twc = upstream(0)
    for a, b in edges:
        pa, pb = nodes[a], nodes[b]
        pipe = [pa, pb]
        if any(LineString(pipe).intersects(c.buffer(2)) for c in d['cols']):      # betonarmeyi kesiyorsa dik kırık
            for cand in ([pa, (pa[0], pb[1]), pb], [pa, (pb[0], pa[1]), pb]):
                if not any(LineString(cand).intersects(c.buffer(2)) for c in d['cols']):
                    pipe = cand
                    break
        gp.pipe(pipe, PST, 'P')
        gp.node(pa, 'PS'); gp.node(pb, 'PS')
        s, wc = upstream(a)
        pa, pb = max(zip(pipe[:-1], pipe[1:]), key=lambda q: math.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]))
        ln = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
        if ln >= 18:
            ang = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
            if ang > 90: ang -= 180
            if ang < -90: ang += 180
            m = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            cap_pis(m, ang, '%d SB' % s, 'Ø%d' % dn_sb(s, wc), 4.0)
    return tot, twc


def so_pt(d, f, hot=False):
    """armatürün temiz su bağlantısı: armatürden en yakın duvara (dik) 8 cm kala; sıcak 10 cm yanda"""
    W = d['W']
    p = f['c']
    dirs = ((1, 0), (-1, 0)) if f.get('axis') == 'x' else ((0, 1), (0, -1)) if f.get('axis') == 'y' else \
        ((1, 0), (-1, 0), (0, 1), (0, -1))
    dist, dn = near_wall(W, p, dirs)
    dist = min(dist, 80.0)
    q = (p[0] + dn[0] * (dist - 8.0), p[1] + dn[1] * (dist - 8.0))
    if hot:
        q = (q[0] - dn[1] * 10.0, q[1] + dn[0] * 10.0)
    return q


BOX = None      # temiz su kolon kutusu (merdiven holü) - zemin kaynak koordinatı
SAYAC_TXT = []


def riser_box():
    """temiz su kolon kutusu: daire 1 ve 2 girişlerinin (merdiven holü) ortası, holün duvar dibinde"""
    dg = sorted(DZ['digits'], key=lambda q: q[1])
    e1, e2 = dg[0][0], dg[1][0]
    m = ((e1[0] + e2[0]) / 2, (e1[1] + e2[1]) / 2)
    dist, dn = near_wall(DZ['W'], m)
    return (m[0] + dn[0] * (dist - 12.0), m[1] + dn[1] * (dist - 12.0)), dn


def risers():
    (bx, by), dn = BOX
    out = {}
    along = (-dn[1], dn[0])
    for i in range(9):
        s = (i - 4) * 7.0
        out[i + 1] = (bx + along[0] * s, by + along[1] * s)
    return out


def router_for(k, d):
    w = M.win(k)
    walls = [list(ls.coords) for ls in d['W'].ls]
    g = RT.Grid((w[0], w[1], w[2], w[3]), step=4.0, walls=walls, wall_band=16.0)
    for c in d['cols']:
        g.add_block(c, pad=2.0)
    # odalar (salon / yatak odası / oda / yüklük / asansör) kapalı: temiz su hol ve ıslak hacim duvarlarından gider
    try:
        rms, _ = M.rooms_of(A, k)
        for r in rms:
            if r['name'].split()[0] in ('salon', 'yatak', 'oda', 'yüklük', 'asansör'):
                pg = r['poly'].buffer(-6)
                for g1 in (pg.geoms if hasattr(pg, 'geoms') else [pg]):
                    if g1.area > 1000:
                        g.add_block(g1, pad=0.0)
    except Exception as e:
        print('oda engeli eklenemedi:', e)
    return g


def temiz_kat(k, d):
    """daire içi temiz (soğuk) + sıcak su: kolon kutusu -> daire girişi -> armatürler (A*, ağaca bağlanarak)"""
    g = router_for(k, d)
    o = M.OFF[k]
    RS = {n: (p[0] + o, p[1]) for n, p in risers().items()}
    res = {}
    for dno in sorted(set(f.get('daire') for f in d['F'] if f.get('daire'))):
        fx = [f for f in d['F'] if f.get('daire') == dno and f['kind'] in YB and YB[f['kind']] > 0]
        km = [f for f in d['F'] if f['kind'] == 'KOMBI' and f.get('daire') == dno]
        ent = [w['entry'] for w in d['wet'] if w['daire'] == dno][0]
        r0 = RS[dno]
        # kolon -> daire girişi (ortak alan asma tavanı)
        p0 = g.route(r0, ent, sysn='S%d' % dno)
        if p0:
            gp.pipe(p0, CS, 'S'); g.add_line(p0, 'S%d' % dno); gp.node(p0[0], 'KOLON'); gp.node(p0[-1], 'GİRİŞ')
        VANA(ent, 0.45, 0)
        ybt = sum(YB[f['kind']] for f in fx) + (0.0 if not km else 0.0)
        cap_temiz(((r0[0] + ent[0]) / 2, (r0[1] + ent[1]) / 2 + 6), 0, so='D%d %s YB' % (dno, fmt(ybt)), socp='Ø%d' % dn_temiz(ybt), k=4.5)
        # soğuk: girişten en yakından başlayarak
        targets = [(f, so_pt(d, f)) for f in fx] + [(kf, (kf['c'][0], kf['c'][1])) for kf in km]
        targets.sort(key=lambda t: math.hypot(t[1][0] - ent[0], t[1][1] - ent[1]))
        sysn = 'S%d' % dno
        g.add_line([ent, (ent[0] + 0.1, ent[1])], sysn)
        nok, nfail = 0, 0
        for f, q in targets:
            pth = g.route(q, None, sysn=sysn, to_tree=True)
            if not pth:
                nfail += 1
                continue
            gp.pipe(pth, CS, 'S'); g.add_line(pth, sysn); gp.node(pth[0], 'ARM'); nok += 1
            mtyblk.insert('MTY-KURESEL VANA', q, 0, 0.25)
            ybf = YB.get(f['kind'], 2.0)
            seg = max(zip(pth[:-1], pth[1:]), key=lambda s: math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]))
            if math.hypot(seg[1][0] - seg[0][0], seg[1][1] - seg[0][1]) > 30:
                rot = 90 if abs(seg[1][0] - seg[0][0]) < 0.5 else 0
                cap_temiz(((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2), rot, so='%s YB' % fmt(ybf),
                          socp='Ø%d' % dn_temiz(ybf), k=4.0)
        # sıcak: kombiden sıcak armatürlere
        hn = 0
        if km:
            kc = km[0]['c']
            hs = 'H%d' % dno
            g.add_line([kc, (kc[0] + 0.1, kc[1])], hs)
            hot = [(f, so_pt(d, f, hot=True)) for f in fx if f['kind'] in YBS]
            hot.sort(key=lambda t: math.hypot(t[1][0] - kc[0], t[1][1] - kc[1]))
            for f, q in hot:
                pth = g.route(q, None, sysn=hs, to_tree=True)
                if not pth:
                    continue
                gp.pipe(pth, CH, 'S'); g.add_line(pth, hs); gp.node(pth[0], 'ARM'); hn += 1
            T((kc[0] + 8, kc[1] - 14), 'KOMBİ %d kW' % PRM['kombi_kw'], 6, CD, 'L')
        res[dno] = dict(yb=ybt, ok=nok, fail=nfail, hot=hn)
    return res


def kat_plani(k):
    d = DATA[k]
    push(sx(k))
    copy_arch(k, d['R'])
    stats = dict(kolon={}, temiz=None)
    for w in d['wet']:
        kc = kolon_of(k, w)
        kp = (kc['p'][0] + M.OFF[k], kc['p'][1])
        sb, wc = pis_ag(k, d, w, kp)
        stats['kolon'].setdefault(kc['name'], 0)
        stats['kolon'][kc['name']] += sb
    for kc in KOLS:
        kp = (kc['p'][0] + M.OFF[k], kc['p'][1])
        cx = sum(c['p'][0] for c in KOLS) / len(KOLS)
        off = (45 if kc['p'][0] > cx else -45, 40)
        gp.kolon_pis(kp, kc['name'], off, k=0.5)
        nup = len(FL) - FL.index(k)
        sb_here = sum(STATS_SB[kc['name']].get(f, 0) for f in FL[FL.index(k):])
        T((kp[0] + off[0] + (4 if off[0] > 0 else -4), kp[1] + off[1] - 16), 'Ø%d / %d SB' % (kc['dn'], sb_here), 5.5, PSC,
          'L' if off[0] > 0 else 'R')
    # temiz su kolon kutusu
    rs = risers()
    o = M.OFF[k]
    for n, p in rs.items():
        gp.kolon_temiz((p[0] + o, p[1]), r=2.4)
    (bx, by), dn = BOX
    xs_ = [p[0] + o for p in rs.values()]; ys_ = [p[1] for p in rs.values()]
    RECT(min(xs_) - 8, min(ys_) - 8, max(xs_) + 8, max(ys_) + 8, VN)
    T((max(xs_) + 12, max(ys_) + 6), 'TEMİZ SU KOLON KUTUSU (D1-D9)', 6, TSC, 'L')
    stats['temiz'] = temiz_kat(k, d)
    # yağmur inişleri (mimari "yağmur inişi" notları) - cepheye yaslı
    if k == 'Z':
        pass
    for i, p in enumerate(YBP):
        q = (p[0] + o, p[1])
        cad.YB_PLAN(q, 6.0, YL)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (q[0] + 26, q[1] + 26), 0, 0.5, attrs={'K': 'YB%d' % (i + 1)})
    if k == 'Z':
        zemin_sebeke()
    pop()
    w = M.win(k)
    T((SLOTS[k] * SLOT + SLOT / 2, 120.0), '%s SIHHİ TESİSAT PLANI..........ÖLÇEK: 1 / 50' % FNAME[k], 40, 'MTY-KAT-ADI', 'C')
    return stats


def zemin_sebeke():
    """şebeke -> bina girişi -> ana sayaç; ADK (çatı deposundan iner) -> sayaç grubu -> D1..D9 kolonları (kolon kutusu)"""
    (bx, by), dn = BOX
    rs = risers()
    xs_ = [p[0] for p in rs.values()]; ys_ = [p[1] for p in rs.values()]
    # DBK (şebekeden çatı deposuna) ve ADK (depodan sayaçlara) kolonları kutunun yanında
    dbk = (max(xs_) + 0.0, max(ys_) + 18.0) if abs(dn[1]) > 0.5 else (max(xs_) + 18.0, max(ys_))
    adk = (min(xs_) + 0.0, max(ys_) + 18.0) if abs(dn[1]) > 0.5 else (min(xs_) - 18.0, max(ys_))
    for p, nm in ((dbk, 'DBK'), (adk, 'ADK')):
        gp.kolon_temiz(p, r=3.0); T((p[0] + 5, p[1] + 5), nm, 6, TSC, 'L')
    # bina girişi (mimari "bina giriş" yazısı) - şebeke girişi ve ana sayaç
    bg = [a[1][0] for a in DZ['R'] if a[0] == 'T' and 'bina' in a[2][0] and 'giri' in a[2][0]]
    if bg:
        e = bg[0]
        g = router_for('Z', DZ)
        sebeke = (M.WIN_Z[2] - 5.0, e[1])
        pth = g.route(sebeke, dbk, sysn='SEB')
        if pth:
            gp.pipe(pth, CS, 'S'); gp.node(pth[0], 'ŞEBEKE'); gp.node(pth[-1], 'DBK')
            VANA((sebeke[0] - 15, sebeke[1]), 0.5, 0); PISLIK_TUTUCU((sebeke[0] - 30, sebeke[1]), 0.45, 0)
            mtyblk.insert('MTY-SU SAYACI', (sebeke[0] - 46, sebeke[1]), 0, 0.3); CEKVALF((sebeke[0] - 62, sebeke[1]), 0.45, 0)
            T((sebeke[0] - 70, sebeke[1] + 12), 'ŞEBEKE Ø32 - ANA SAYAÇ (BİNA GİRİŞİ)', 6, TSC, 'R')
        T((bx + 20, by - 40), 'SAYAÇ GRUBU (9 ADET) KOLON KUTUSU ALTINDA - ADK ÇATI DEPOSUNDAN İNER', 6, VN, 'L')


# ================================================================== 3. TEMEL PLANI (kolon dipleri + rögarlar, bina dışı)
def bina_hatti():
    """zemin kat duvarlarından dış kontur (morfolojik kapama + dış bölge doldurma)"""
    import numpy as np, cv2
    from scipy import ndimage as ndi
    w = M.win('Z')
    res = 4.0
    W_, H_ = int((w[2] - w[0]) / res) + 1, int((w[3] - w[1]) / res) + 1
    img = np.zeros((H_, W_), np.uint8)
    px = lambda p: (int((p[0] - w[0]) / res), int((w[3] - p[1]) / res))
    for ls in DZ['W'].ls:
        cs = list(ls.coords)
        for a, b in zip(cs[:-1], cs[1:]):
            cv2.line(img, px(a), px(b), 255, 1)
    r = 15
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    cl = cv2.dilate(img, k)
    lab, n = ndi.label(cl == 0)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    ext = np.isin(lab, list(border))
    bld = (~ext).astype(np.uint8)
    bld = cv2.erode(bld, k)
    cs, _ = cv2.findContours(bld, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cs, key=cv2.contourArea)
    pts = [(w[0] + p[0][0] * res, w[3] - p[0][1] * res) for p in c]
    return Polygon(pts).buffer(0).simplify(6.0)


ROG = {}


def temel():
    push(sx('T'))
    bh = bina_hatti()
    PL(list(bh.exterior.coords), 'MTY-BINA-HATTI', True, 1.5)
    for c in DZ['cols']:
        PL(list(c.exterior.coords), gp.ARC_K, True, 1.0)
    gp.hatch_cols(DZ['cols'])
    x0, y0, x1, y1 = bh.bounds
    xr = x1 + 110.0
    # kolon diplerini y'ye göre kümele -> her küme bir rögar
    ks = sorted(KOLS, key=lambda c: -c['p'][1])
    groups = []
    for c in ks:
        if groups and groups[-1][-1]['p'][1] - c['p'][1] < 260:
            groups[-1].append(c)
        else:
            groups.append([c])
    rp = []
    for gi, gr in enumerate(groups):
        ry = sum(c['p'][1] for c in gr) / len(gr)
        rp.append((xr, ry))
    # rögarlar arası en az 150 cm
    for i in range(1, len(rp)):
        if rp[i - 1][1] - rp[i][1] < 150:
            rp[i] = (xr, rp[i - 1][1] - 150)
    cols_g = DZ['cols']
    rep = []
    TG = RT.Grid((x0 - 100, y0 - 100, xr + 100, y1 + 100), step=4.0)
    for cg in cols_g:
        TG.add_block(cg, pad=4.0)
    for gi, (gr, r) in enumerate(zip(groups, rp)):
        nm = 'R%d' % (gi + 1)
        ROG[nm] = dict(p=r, kols=[c['name'] for c in gr])
        cad.ROGAR_PLAN(r, 35, 'MTY-ROGAR')
        T((r[0] + 45, r[1] + 12), nm, 14, 'MTY-ROGAR', 'L')
        T((r[0] + 45, r[1] - 6), '70x70 h:-70cm', 6, 'MTY-ROGAR', 'L')
        for j, c in enumerate(sorted(gr, key=lambda c: c['p'][0])):
            kp = c['p']
            inlet = (r[0] - 35, r[1] - 12 + 6 * j)
            pth = TG.route(kp, inlet, sysn='T' + c['name'], cross=200.0)
            if pth is None:
                pth = [kp, (inlet[0] - 20, kp[1]), (inlet[0] - 20, inlet[1]), inlet]
            TG.add_line(pth, 'T' + c['name'])
            hit = sum(1 for cg in cols_g if LineString(pth).intersects(cg.buffer(1)))
            best = (hit, pth)
            pts = RT._collinear(best[1])
            gp.pipe(pts, PS, 'T'); gp.node(pts[0], c['name']); gp.node(pts[-1], nm)
            if best[0]:
                rep.append(c['name'])
            gp.kolon_pis(kp, c['name'], (-40, 35), k=0.5)
            TEMIZLEME_KAPAGI((kp[0], kp[1] - 12), 0.8)
            sbk = sum(STATS_SB[c['name']].values())
            seg = max(zip(pts[:-1], pts[1:]), key=lambda s: math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]))
            ang = 0 if abs(seg[1][1] - seg[0][1]) < 0.5 else 90
            cap_pis(((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2), ang, '%d SB' % sbk, 'Ø%d' % max(100, c['dn']), 5.0)
    # rögar -> rögar -> parsel bacası (güneye, sonra doğuya)
    acc = 0
    names = list(ROG)
    for i, nm in enumerate(names):
        acc += sum(sum(STATS_SB[k_].values()) for k_ in ROG[nm]['kols'])
        a = ROG[nm]['p']
        if i + 1 < len(names):
            b = ROG[names[i + 1]]['p']
            pts = [(a[0], a[1] - 35), (b[0], b[1] + 35)]
        else:
            pb = (a[0] + 220, a[1])
            ROG['PB'] = dict(p=pb, kols=[])
            pts = [(a[0] + 35, a[1]), (pb[0] - 35, pb[1])]
            cad.ROGAR_PLAN(pb, 35, 'MTY-ROGAR')
            T((pb[0] - 18, pb[1] + 45), 'PB', 16, 'MTY-ROGAR', 'L')
            T((pb[0] - 30, pb[1] - 52), 'PARSEL BACASI → SASKİ', 6, 'MTY-ROGAR', 'L')
        gp.pipe(pts, PS, 'T'); gp.node(pts[0], nm); gp.node(pts[1], 'R')
        m = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
        vert = abs(pts[0][0] - pts[1][0]) < 0.5
        cap_pis((m[0] + (8 if vert else 0), m[1] + (0 if vert else 6)), 90 if vert else 0, '%d SB' % acc, 'Ø%d' % max(150, dn_sb(acc, True)), 5.5)
        T((m[0] + (22 if vert else 0), m[1] - (0 if vert else 14)), '%1', 6, PSC, 'L', 90 if vert else 0)
    T((x0, y0 - 60), 'TEMEL PLANI: MİMARİDEN YALNIZ BETONARME KOLON/PERDELER VE BİNA DIŞ HATTI. KOLON DİPLERİ ZEMİN KOTUNDAN AYRI AYRI BİNA DIŞINDAKİ RÖGARLARA.', 7, YZ, 'L')
    pop()
    T((SLOTS['T'] * SLOT + SLOT / 2, 120.0), 'TEMEL PLANI..........ÖLÇEK: 1 / 50', 40, 'MTY-KAT-ADI', 'C')
    return bh, rep


# ================================================================== 4. YERLEŞİM (mimari vaziyetten kopya)
def yerlesim():
    w = (248150.0, -444080.0, 250300.0, -441350.0)
    R = M.recs_in(A, w)
    push(MOVE(SLOTS['YER'] * SLOT + 120.0 - w[0], 300.0 - w[1] - 150))
    copy_arch('Y', R)
    pop()
    T((SLOTS['YER'] * SLOT + SLOT / 2, 120.0), 'YERLEŞİM PLANI   ÖLÇEK: 1 / 250', 40, 'MTY-KAT-ADI', 'C')


# ================================================================== çalıştır
def main():
    global BOX, STATS_SB, YBP
    BOX = riser_box()
    YBP = [p for p in DZ['yb']]
    # her kolonun kat bazında SB yükü ve çapı (önce hesap, sonra çizim)
    STATS_SB = {c['name']: {} for c in KOLS}
    WCK = {c['name']: False for c in KOLS}
    for k in FL:
        d = DATA[k]
        for w in d['wet']:
            kc = kolon_of(k, w)
            fx = [f for f in d['F'] if f['room'] is w and f['kind'] in SB]
            STATS_SB[kc['name']][k] = STATS_SB[kc['name']].get(k, 0) + sum(SB[f['kind']] for f in fx)
            WCK[kc['name']] |= any(f['kind'] == 'WC' for f in fx)
    for c in KOLS:
        c['dn'] = dn_sb(sum(STATS_SB[c['name']].values()), WCK[c['name']])
    out = dict(kolon=[(c['name'], c['typ'], c['d0'], [round(v) for v in c['p']], c['dn'], STATS_SB[c['name']]) for c in KOLS])
    yerlesim()
    bh, rep = temel()
    out['temel_kolon_kesen'] = rep
    out['rogar'] = {k: dict(p=[round(v) for v in v_['p']], kols=v_['kols']) for k, v_ in ROG.items()}
    out['kat'] = {}
    for k in FL:
        out['kat'][k] = kat_plani(k)
    out['bina_alani'] = bh.area / 1e4
    global ROOF_A
    ROOF_A = round(bh.area / 1e4 * 1.10, 2)          # çatı izdüşümü ~ taban alanı + %10 saçak (DENEME varsayımı)
    import sema
    out['sema'] = sema.ciz(globals())
    return out


STATS_SB, YBP, ROOF_A = {}, [], 0.0

if __name__ == '__main__':
    OUT = main()
    import cikti
    cikti.yaz(OUT, globals())
