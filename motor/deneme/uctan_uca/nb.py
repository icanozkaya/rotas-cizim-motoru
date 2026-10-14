"""UÇTAN UCA SIHHİ TESİSAT DENEMESİ — new_block.dxf (Metra, Z+2, 9 daire).  R2: 14.10.2026 kullanıcı kuralları (r2.py).

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
import r2
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
    depo='otomatik', depo_V=3.0,    # otomatik: bodrumda depo yeri varsa hidrofor, yoksa çatı deposu (9 BB <= 10 -> 3 m³)
    kombi_kw=24,
    k_cap=8.0,                  # çap / yük etiketi ölçeği (kullanıcı çiziminde 10)
    sicak_oteleme=7.0,          # sıcak su hattının soğuğa paralel ötelemesi (cm)
    cikti=REPO + '/proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R2.dxf',
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
WET_TYPE = {'banyo': 'BANYO', 'wc+banyo': 'BANYO', 'wc-banyo': 'BANYO', 'wc-lvb.': 'WC', 'duş': 'DUŞ', 'wc-duş': 'DUŞ',
            'mutfak': 'MUTFAK'}
# üst katlarda farklı adlı ıslak hacimler (1. kat: wc-banyo, wc-duş) - kat planı farklılığı (14.10.2026 kuralı)
M.WET.update({'wc-banyo': 'B', 'wc-duş': 'D'})
M.ROOM_WORDS = tuple(M.ROOM_WORDS) + ('wc-banyo', 'wc-duş')


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
    return dict(R=R, labs=labs, wet=wet, W=W, F=F, cols=cols, digits=digits, yb=yb, k=k)


for k in FL:
    DATA[k] = floor_data(k)

# ------------------------------------------------------------------ daireler: ıslak hacim -> en yakın mutfak (görünürlük) -> daire no
def assign_daire(d):
    mut = [w for w in d['wet'] if w['name'] == 'mutfak']
    for m in mut:
        m['daire'] = min(d['digits'], key=lambda q: math.hypot(q[0][0] - m['xy'][0], q[0][1] - m['xy'][1]))[1]
        m['entry'] = min(d['digits'], key=lambda q: math.hypot(q[0][0] - m['xy'][0], q[0][1] - m['xy'][1]))[0]
    nm = [w for w in d['wet'] if w['name'] != 'mutfak']
    try:                             # kapılardan yürüme mesafesiyle (üst kattaki farklı ıslak hacimler için gerekli)
        gd = r2.geodezik_daire(d, M.win(d['k']), [w['xy'] for w in nm])
    except Exception as e:
        print('geodezik daire atanamadı:', e); gd = [None] * len(nm)
    for w, g_ in zip(nm, gd):
        m = min(mut, key=lambda m_: math.hypot(m_['xy'][0] - w['xy'][0], m_['xy'][1] - w['xy'][1]))
        if g_ is not None and g_ != m['daire'] and any(m2['daire'] == g_ for m2 in mut):
            print('ıslak hacim %s %s: en yakın mutfak D%d, kapı yolu D%d -> D%d' % (w['name'], [round(v) for v in w['xy']], m['daire'], g_, g_))
            m = [m2 for m2 in mut if m2['daire'] == g_][0]
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


# ------------------------------------------------------------------ R2: yasak bölgeler, eksik ÇM/BM, depo kararı
for k in FL:
    d = DATA[k]
    d['YASAK'] = r2.yasak_bolgeler(d['R'], d['W'], d['cols'])
    d['MEK'] = [p for p, t in r2.texts(d['R'], 'mek.')]
    d['EK'] = r2.ek_makineler(d)


def depo_karari():
    """kural: depo bodrumda ise hidrofor grubu; mimaride depo yeri yoksa çatıda depo varmış gibi kurgulanır"""
    if PRM['depo'] != 'otomatik':
        return PRM['depo'], 'parametre'
    tx = [a[2][0].lower() for a in A if a[0] == 'T']
    bodrum = any('bodrum' in t for t in tx)
    depo_yeri = any(('su depo' in t or t.strip() == 'depo') for t in tx)
    if bodrum and depo_yeri:
        return 'bodrum', 'mimaride bodrum katta depo yeri var -> depo + hidrofor grubu'
    return 'cati', 'mimaride bodrum / depo yeri yok (Z+2, temel) -> çatı deposu kurgusu, hidroforsuz'


DEPO, DEPO_NEDEN = depo_karari()

DZ = DATA['Z']
KOLS = []          # dict(name, p (zemin kaynak koord), type, daire_col (zemin daire no))
for w in DZ['wet']:
    q = r2.kolon_yeri2(DZ, w, DZ['MEK'], DZ['YASAK'])
    if q:
        KOLS.append(dict(p=q, wet=w.get('name'), d0=w['daire'], typ=WET_TYPE[w['name']]))
# kullanıcı numaralaması: daire daire mutfak -> wc -> banyo -> duş (P1..Pn)
KOLS.sort(key=lambda c: (c['d0'], {'MUTFAK': 0, 'WC': 1, 'BANYO': 2, 'DUŞ': 3}[c['typ']]))
for i, c in enumerate(KOLS):
    c['name'] = 'P%d' % (i + 1)


def kolon_of(k, w):
    """kat k'deki ıslak hacmin kolonu: zemin kolonlarından aynı tipte en yakın (<= 300 cm). Alt katta karşılığı olmayan
    ıslak hacim (ör. 1. katta zemindeki yüklüğün yerindeki wc-duş) için o katta yeni köşe kolonu açılır; kolon alt katlardan
    geçerek temele iner, üst katlardan çatıya çıkar (kat planı farklılığına uyarlama)."""
    if w.get('_kolon'):
        return w['_kolon']
    q = (w['xy'][0] - M.OFF[k], w['xy'][1])
    cs = [c for c in KOLS if c['typ'] == WET_TYPE[w['name']]]
    best = min(cs, key=lambda c: math.hypot(c['p'][0] - q[0], c['p'][1] - q[1])) if cs else None
    if best is None or math.hypot(best['p'][0] - q[0], best['p'][1] - q[1]) > 300:
        d = DATA[k]
        p = r2.kolon_yeri2(d, w, d['MEK'], d['YASAK'])
        if p is None:
            return best
        pz = (p[0] - M.OFF[k], p[1])
        # zemin ve diğer katlarda yasak bölgeye denk geliyorsa ötele
        best = dict(p=pz, wet=w['name'], d0=daire_pos(k, w['daire']) or w['daire'], typ=WET_TYPE[w['name']],
                    name='P%d' % (len(KOLS) + 1), kat_ozel=k)
        KOLS.append(best)
    w['_kolon'] = best
    return best


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
        YZG = [z['g'] for z in d['YASAK']]
        if any(LineString(pipe).intersects(c.buffer(2)) for c in YZG):      # yasak bölgeyi kesiyorsa dik kırık
            for cand in ([pa, (pa[0], pb[1]), pb], [pa, (pb[0], pa[1]), pb]):
                if not any(LineString(cand).intersects(c.buffer(2)) for c in YZG):
                    pipe = cand
                    break
        gp.pipe(pipe, PST, 'P')
        METRAJ_ADD('PİS SU (PVC) Ø%d' % dn_sb(upstream(a)[0], upstream(a)[1]), pipe)
        gp.node(pa, 'PS'); gp.node(pb, 'PS')
        s, wc = upstream(a)
        pa, pb = max(zip(pipe[:-1], pipe[1:]), key=lambda q: math.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]))
        ln = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
        if ln >= 18:
            ang = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
            if ang > 90: ang -= 180
            if ang < -90: ang += 180
            m = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            cap_pis(m, ang, '%d SB' % s, 'Ø%d' % dn_sb(s, wc), PRM['k_cap'])
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


# ------------------------------------------------------------------ metraj (boru boyu, cm -> m)
METRAJ = {}


def METRAJ_ADD(key, pts, extra_cm=0.0):
    ln = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])) + extra_cm
    METRAJ[key] = METRAJ.get(key, 0.0) + ln / 100.0


# ------------------------------------------------------------------ temiz su ana dağıtım: ortak alanda daire kapısı yanında kolonlar
RISERS = {}     # grup adı -> dict(p (zemin kaynak koord), digits=[zemin daire no], name)
DBK = None


def gw_cross(GW, a, b):
    seg = LineString([a, b])
    return sum(1 for i in GW.tree.query(seg) if GW.ls[i].intersects(seg))


def riser_gruplari():
    """daire giriş numaralarını (merdiven holü) 300 cm içinde kümele; her küme için holde en yakın gerçek duvar dibine
    bir ADK kolonu (çatı deposundan iner). Her katta kolon -> daire kapısı kısa yatay hat (ortak alanda)."""
    GW = DZ.get('GW') or r2.GercekDuvar(DZ['W']); DZ['GW'] = GW
    dg = sorted(DZ['digits'], key=lambda q: q[1])
    groups = []
    for p, n in dg:
        for g_ in groups:
            if any(math.hypot(p[0] - q[0], p[1] - q[1]) < 300 for q, _ in g_):
                g_.append((p, n)); break
        else:
            groups.append([(p, n)])
    out = {}
    for i, g_ in enumerate(sorted(groups, key=lambda g_: -len(g_))):
        m = (sum(p[0] for p, _ in g_) / len(g_), sum(p[1] for p, _ in g_) / len(g_))
        best = None
        for v in r2.DIRS:
            dd = GW.ray(m, v)
            if dd > 250:
                continue
            q = (m[0] + v[0] * (dd - 12.0), m[1] + v[1] * (dd - 12.0))
            cands = [(dd, q)]
            if len(g_) == 1:            # tek daire girişi: holün en yakın köşesi (yoksa numaranın arkasındaki duvar dibi)
                cands = [(dd + 400.0, q)]
                for a in ((-v[1], v[0]), (v[1], -v[0])):
                    da = GW.ray(q, a)
                    if da <= 250:
                        c = (q[0] + a[0] * (da - 12.0), q[1] + a[1] * (da - 12.0))
                        cands.append((dd + da, c))
            for sc, c in cands:
                bad = any(z['g'].buffer(10).contains(Point(c)) for z in DZ['YASAK']) or \
                    any(gw_cross(GW, p_, c) > 0 for p_, _ in g_)          # holden çıkmaz (duvar/kapı arkasına geçmez)
                if not bad and (best is None or sc < best[0]):
                    best = (sc, c, v)
        out['ADK-%d' % (i + 1)] = dict(p=best[1], dn=best[2], digits=[n for _, n in g_], name='ADK-%d' % (i + 1))
    return out


def daire_pos(k, dno):
    """kat k'deki daire no -> zemin konumundaki daire no (aynı giriş yeri)"""
    for p, n in DATA[k]['digits']:
        if n == dno:
            q = (p[0] - M.OFF[k], p[1])
            return min(DZ['digits'], key=lambda t: math.hypot(t[0][0] - q[0], t[0][1] - q[1]))[1]
    return None


def so_pt_safe(d, f, hot=False):
    return so_pt(d, f, hot)


def router_for(k, d, ortak=False):
    """ortak=True: yalnız ortak alan (tüm daire mahalleri kapalı) - ana dağıtım hatları için"""
    w = M.win(k)
    walls = [list(ls.coords) for ls in d['W'].ls]
    g = RT.Grid((w[0], w[1], w[2], w[3]), step=4.0, walls=walls, wall_band=16.0)
    for z in d['YASAK']:
        g.add_block(z['g'], pad=6.0)
    try:
        rms, _ = M.rooms_of(A, k)
        d['ROOMS'] = rms
        kapali = ('salon', 'yatak', 'oda', 'yüklük', 'asansör', 'en.') if not ortak else \
            ('salon', 'yatak', 'oda', 'yüklük', 'asansör', 'en.', 'antre-kor.', 'mutfak', 'banyo', 'wc+banyo', 'wc-lvb.', 'duş', 'balkon')
        for r in rms:
            if r['name'].split()[0] in kapali:
                pg = r['poly'].buffer(-6)
                for g1 in (pg.geoms if hasattr(pg, 'geoms') else [pg]):
                    if g1.area > 400:
                        g.add_block(g1, pad=0.0)
    except Exception as e:
        print('oda engeli eklenemedi:', e)
    return g


YB_HOT = YBS


def _cap_on(seg, so, socp, sc=None, sccp=None):
    """çap / yük etiketi tam boru ekseninde (ekleme noktası borunun üstünde, boru doğrultusunda)"""
    (ax, ay), (bx, by) = seg
    ang = math.degrees(math.atan2(by - ay, bx - ax))
    if ang > 90.1: ang -= 180
    if ang < -89.9: ang += 180
    m = ((ax + bx) / 2, (ay + by) / 2)
    cap_temiz(m, ang, so=so, socp=socp, sc=sc, sccp=sccp, k=PRM['k_cap'])


def temiz_kat(k, d):
    """ADK kolonu (ortak alan) -> sayaç + vana -> daire kapısı; daire içi soğuk ağaç (A*), sıcak = kombiden sıcak
    armatürlere soğuk ağacı boyunca paralel öteleme (yan yana)."""
    o = M.OFF[k]
    gd = router_for(k, d)
    go = router_for(k, d, ortak=True)
    res = {}
    for dno in sorted(set(f.get('daire') for f in d['F'] if f.get('daire'))):
        fx = [f for f in d['F'] if f.get('daire') == dno and f['kind'] in YB and YB[f['kind']] > 0]
        km = [f for f in d['F'] if f['kind'] == 'KOMBI' and f.get('daire') == dno]
        ent = [w['entry'] for w in d['wet'] if w['daire'] == dno][0]
        dz = daire_pos(k, dno)
        rk = [r for r in RISERS.values() if dz in r['digits']][0]
        r0 = (rk['p'][0] + o, rk['p'][1])
        # ---- ana hat: ADK -> daire kapısı (yalnız ortak alan)
        p0 = go.route(r0, ent, sysn='A%d' % dno)
        if not p0:
            p0 = RT.ortho([r0, (r0[0], ent[1]), ent])
        gp.pipe(p0, CS, 'S'); go.add_line(p0, 'A%d' % dno); gp.node(p0[0], 'KOLON'); gp.node(p0[-1], 'GİRİŞ')
        ANA_HAT.append((k, [cad.P(q) for q in p0]))
        METRAJ_ADD('TEMİZ SU ANA HAT (PPRC) Ø25', p0)
        seg = max(zip(p0[:-1], p0[1:]), key=lambda s_: math.hypot(s_[1][0] - s_[0][0], s_[1][1] - s_[0][1]))
        vx = (seg[1][0] - seg[0][0], seg[1][1] - seg[0][1]); ln = math.hypot(*vx) or 1.0
        ux = (vx[0] / ln, vx[1] / ln)
        ang = math.degrees(math.atan2(ux[1], ux[0]))
        sp = (ent[0] - ux[0] * 12, ent[1] - ux[1] * 12) if math.hypot(p0[-1][0] - p0[-2][0], p0[-1][1] - p0[-2][1]) > 30 else ent
        mtyblk.insert('MTY-SU SAYACI', sp, 0, 0.45)
        VANA(ent, 0.45, ang)
        # ---- daire içi soğuk ağaç
        sysn = 'S%d' % dno
        gd.add_line([ent, (ent[0] + 0.1, ent[1])], sysn)
        paths = []
        targets = [(f, so_pt(d, f)) for f in fx] + [(kf, (kf['c'][0], kf['c'][1])) for kf in km]
        targets.sort(key=lambda t: math.hypot(t[1][0] - ent[0], t[1][1] - ent[1]))
        nok, nfail = 0, 0
        fnode = []
        for f, q in targets:
            pth = gd.route(q, None, sysn=sysn, to_tree=True)
            if not pth:
                nfail += 1
                continue
            paths.append(pth); gd.add_line(pth, sysn); nok += 1
            fnode.append((f, q))
            if f['kind'] != 'KOMBI':
                mtyblk.insert('MTY-KURESEL VANA', q, 0, 0.25)
        # ---- ağaç grafı, yükler
        import networkx as nx
        G = r2.agac_graf(paths + [[ent, ent]] if False else paths)
        if not G.nodes:
            continue
        root = r2.en_yakin_dugum(G, ent)
        hot_f = [(f, q) for f, q in fnode if f['kind'] in YBS]
        ybs_tot = sum(YBS[f['kind']] for f, _ in hot_f)
        cold_load, hot_load = {}, {}
        for f, q in fnode:
            n = r2.en_yakin_dugum(G, q)
            try:
                pth = nx.shortest_path(G, root, n, weight='w')
            except Exception:
                continue
            ld = ybs_tot if f['kind'] == 'KOMBI' else YB[f['kind']]
            for a_, b_ in zip(pth[:-1], pth[1:]):
                e = tuple(sorted((a_, b_))); cold_load[e] = cold_load.get(e, 0.0) + ld
        hot_paths = []
        if km and hot_f:
            kn = r2.en_yakin_dugum(G, km[0]['c'])
            for f, q in hot_f:
                n = r2.en_yakin_dugum(G, q)
                try:
                    pth = nx.shortest_path(G, kn, n, weight='w')
                except Exception:
                    continue
                for a_, b_ in zip(pth[:-1], pth[1:]):
                    e = tuple(sorted((a_, b_))); hot_load[e] = hot_load.get(e, 0.0) + YBS[f['kind']]
            hot_paths = r2.sicak_yollar(G, km[0]['c'], [q for _, q in hot_f])
        # ---- çizim: soğuk zincirler + etiketler; sıcak paralel
        from shapely.ops import linemerge
        chains = linemerge([LineString(e) for e in cold_load]) if cold_load else None
        chains = [list(g_.coords) for g_ in (chains.geoms if hasattr(chains, 'geoms') else [chains])] if chains else []
        for ch in chains:
            gp.pipe(ch, CS, 'S')
            METRAJ_ADD('TEMİZ SU SOĞUK (PPRC)', ch)
        for pth in paths:
            gp.node(pth[0], 'ARM')
        if hot_paths:
            v, hps = r2.otele_sec(hot_paths, d['W'], d['YASAK'], PRM['sicak_oteleme'])
            for hp in hps:
                gp.pipe(hp, CH, 'S')
                METRAJ_ADD('TEMİZ SU SICAK (PPRC, izoleli)', hp)
            for hp in hps:
                gp.node(hp[0], 'ARM'); gp.node(hp[-1], 'ARM')
        # etiket: zincirleri dallanma düğümlerinde böl, her parçanın en uzun düz kısmına bir etiket
        deg = {n: G.degree(n) for n in G.nodes}
        segs_done = []
        for ch in chains:
            parts, cur = [], [ch[0]]
            for q in ch[1:]:
                cur.append(q)
                if deg.get((round(q[0], 3), round(q[1], 3)), 2) != 2:
                    parts.append(cur); cur = [q]
            if len(cur) > 1:
                parts.append(cur)
            for pt in parts:
                sg = max(zip(pt[:-1], pt[1:]), key=lambda s_: math.hypot(s_[1][0] - s_[0][0], s_[1][1] - s_[0][1]))
                if math.hypot(sg[1][0] - sg[0][0], sg[1][1] - sg[0][1]) < 45:
                    continue
                e = tuple(sorted(((round(sg[0][0], 3), round(sg[0][1], 3)), (round(sg[1][0], 3), round(sg[1][1], 3)))))
                # segment kenarı graf kenarlarının birleşimi olabilir: ilk alt kenarı bul
                cl = next((v_ for e_, v_ in cold_load.items() if LineString(e_).within(LineString(sg).buffer(0.05))), None)
                hl = next((v_ for e_, v_ in hot_load.items() if LineString(e_).within(LineString(sg).buffer(0.05))), None)
                if cl is None:
                    continue
                if hl:
                    _cap_on(sg, '%s YB' % fmt(cl), 'Ø%d' % dn_temiz(cl), '%s YB' % fmt(hl), 'Ø%d' % dn_temiz(hl))
                else:
                    _cap_on(sg, '%s YB' % fmt(cl), 'Ø%d' % dn_temiz(cl))
        ybt = sum(YB[f['kind']] for f in fx)
        sg = max(zip(p0[:-1], p0[1:]), key=lambda s_: math.hypot(s_[1][0] - s_[0][0], s_[1][1] - s_[0][1]))
        _cap_on(sg, 'D%d %s YB' % (dno, fmt(ybt)), 'Ø%d' % dn_temiz(ybt))
        if km:
            kc = km[0]['c']
            T((kc[0] + 8, kc[1] - 14), 'KOMBİ %d kW' % PRM['kombi_kw'], 6, CD, 'L')
        res[dno] = dict(yb=ybt, ok=nok, fail=nfail, hot=len(hot_f), sicak_paralel=bool(hot_paths))
    return res


ANA_HAT = []          # (kat, dünya koordinatlı nokta listesi) - ortak alan kontrolü için
LABEL_ENGEL = []


def ek_cihaz_ciz(d):
    """mimaride olmayan, kural gereği eklenen çamaşır / bulaşık makinesi"""
    for f in d['EK']:
        cad.MAKINE(f['c'], 'MTY-TEFRIS', 'CM' if f['kind'] == 'CM' else 'BM', 56)
        T((f['c'][0], f['c'][1] - 2), "C'W'" if f['kind'] == 'CM' else "B'M'", 7, CD, 'MC')
        T((f['c'][0], f['c'][1] - 12), '(EK)', 5, CD, 'MC')


def balkon_ciz(k, d, o):
    """balkon süzgeçleri: pis su hattına bağlanmaz; en yakın yağmur inişine ayrı yağmur/süzgeç hattıyla"""
    ybp = [(p[0] + o, p[1]) for p in YBP]
    bs = r2.balkon_suzgecleri(d, d['R'], ybp)
    n = 0
    for b in bs:
        p, yb = b['p'], b['yb']
        cands = [[p, (yb[0], p[1]), yb], [p, (p[0], yb[1]), yb]]
        def cost(c):
            ls = LineString(c)
            return sum(1000 for z in d['YASAK'] if ls.intersects(z['g'].buffer(2))) + \
                sum(1 for i in d['W'].tree.query(ls) if d['W'].ls[i].intersects(ls))
        pth = RT._collinear(min(cands, key=cost))
        mtyblk.insert('SUZGEC1', p, 0, 1.6)
        gp.pipe(pth, YL, 'B%d' % n); gp.node(pth[0], 'SÜZGEÇ'); gp.node(pth[-1], 'YB')
        METRAJ_ADD('BALKON SÜZGEÇ HATTI (PVC) Ø50', pth)
        seg = max(zip(pth[:-1], pth[1:]), key=lambda s_: math.hypot(s_[1][0] - s_[0][0], s_[1][1] - s_[0][1]))
        if math.hypot(seg[1][0] - seg[0][0], seg[1][1] - seg[0][1]) > 170:
            ang = 0 if abs(seg[1][1] - seg[0][1]) < 0.5 else 90
            m = ((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2)
            T((m[0], m[1] + 3) if ang == 0 else (m[0] - 3, m[1]), 'BALKON SÜZGECİ Ø50 → YAĞMUR', 5, YC, 'BC', ang)
        n += 1
        BALKON.append(dict(k=k, p=p, yb=yb))
    return n


BALKON = []


def kolon_etiketleri(k, i0, kps):
    """P1.. balonları kolon sembolünün hemen yanında, çizgi / bloklara binmeden (16 yön x 5 uzaklık arama)"""
    from shapely import STRtree
    import tcheck
    geoms = []
    for r in cad.R[i0:]:
        try:
            if r[0] == 'L':
                geoms.append(LineString([r[2], r[3]]))
            elif r[0] == 'P' and len(r[2]) >= 2:
                geoms.append(LineString(r[2]))
            elif r[0] == 'C':
                geoms.append(Point(r[2]).buffer(r[3]).exterior)
            elif r[0] == 'T' and r[3].strip():
                geoms.append(tcheck.tbox(r).exterior)
        except Exception:
            pass
    tree = STRtree(geoms)

    class E:
        @staticmethod
        def query_geoms(g):
            return [geoms[i] for i in tree.query(g)]
    taken = []
    rep = []
    ks = 0.55
    rr = 27.5 * ks
    for name, kp, txt in kps:
        w = cad.P(kp)
        q, hit = r2.serbest_yer(w, rr, E, yasak_kutu=taken)
        taken.append(Point(q).buffer(rr + 3))
        # dünya -> yerel (push edilmiş MOVE) : yalnız öteleme
        loc = (kp[0] + q[0] - w[0], kp[1] + q[1] - w[1])
        mtyblk.insert('MTY-KOLON NO PIS SU', loc, 0, ks, attrs={'K': name})
        dd = math.hypot(loc[0] - kp[0], loc[1] - kp[1])
        if dd > rr + 8:
            ux = ((loc[0] - kp[0]) / dd, (loc[1] - kp[1]) / dd)
            L((kp[0] + ux[0] * 4, kp[1] + ux[1] * 4), (loc[0] - ux[0] * rr, loc[1] - ux[1] * rr), 'MTY-PISSU-KOLONNO')
        rep.append((name, round(hit, 1), round(dd)))
    return rep


def kat_plani(k):
    d = DATA[k]
    push(sx(k))
    i0 = len(cad.R)
    copy_arch(k, d['R'])
    o = M.OFF[k]
    stats = dict(kolon={}, temiz=None)
    ek_cihaz_ciz(d)
    for w in d['wet']:
        kc = kolon_of(k, w)
        kp = (kc['p'][0] + o, kc['p'][1])
        sb, wc = pis_ag(k, d, w, kp)
        stats['kolon'].setdefault(kc['name'], 0)
        stats['kolon'][kc['name']] += sb
    kps = []
    for kc in KOLS:
        kp = (kc['p'][0] + o, kc['p'][1])
        mtyblk.insert('MTY-PIS SU KOLON', kp, 0, 0.5)
        gp.node(kp, kc['name'])
        sb_here = sum(STATS_SB[kc['name']].get(f, 0) for f in FL[FL.index(k):])
        kps.append((kc['name'], kp, 'Ø%d / %d SB' % (kc['dn'], sb_here)))
    # ADK kolonları (ortak alan) + DBK
    for r in RISERS.values():
        p = (r['p'][0] + o, r['p'][1])
        gp.kolon_temiz(p, r=3.0); T((p[0] + 6, p[1] + 6), r['name'], 6, TSC, 'L')
    if DBK:
        p = (DBK[0] + o, DBK[1])
        gp.kolon_temiz(p, r=3.0); T((p[0] + 6, p[1] - 12), 'DBK', 6, TSC, 'L')
    stats['temiz'] = temiz_kat(k, d)
    stats['balkon_suzgec'] = balkon_ciz(k, d, o)
    for i, p in enumerate(YBP):
        q = (p[0] + o, p[1])
        cad.YB_PLAN(q, 6.0, YL)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (q[0] + 26, q[1] + 26), 0, 0.5, attrs={'K': 'YB%d' % (i + 1)})
    if k == 'Z':
        zemin_sebeke()
    stats['kolon_etiket'] = kolon_etiketleri(k, i0, kps)
    # kolon Ø / SB yazısı balonun altında değil: kolon şeması ve temel planında; planda armatür hatlarında
    pop()
    T((SLOTS[k] * SLOT + SLOT / 2, 120.0), '%s SIHHİ TESİSAT PLANI..........ÖLÇEK: 1 / 50' % FNAME[k], 40, 'MTY-KAT-ADI', 'C')
    return stats


def zemin_sebeke():
    """şebeke -> ana sayaç (bina girişi, dışarıda) -> DBK (çatı deposuna çıkar). Daireler çatı deposundan inen
    ADK kolonlarından beslenir (kat sahanlığında daire sayacı + küresel vana)."""
    bg = [a[1][0] for a in DZ['R'] if a[0] == 'T' and 'bina' in a[2][0] and 'giri' in a[2][0]]
    if not (bg and DBK):
        return
    e = bg[0]
    g = router_for('Z', DZ, ortak=True)
    sebeke = (M.WIN_Z[2] - 5.0, e[1])
    # şebeke: bina giriş holünden düz (ortak alan) DBK'ya; yasak bölge keserse A*
    pth = RT._collinear([sebeke, (DBK[0], sebeke[1]), DBK])
    if any(LineString(pth).intersects(z['g'].buffer(3)) for z in DZ['YASAK']):
        pth = g.route(sebeke, DBK, sysn='SEB')
    if pth:
        gp.pipe(pth, CS, 'S'); gp.node(pth[0], 'ŞEBEKE'); gp.node(pth[-1], 'DBK')
        ANA_HAT.append(('Z', [cad.P(q) for q in pth]))
        METRAJ_ADD('TEMİZ SU ŞEBEKE / DBK (PPRC) Ø32', pth)
        VANA((sebeke[0] - 15, sebeke[1]), 0.5, 0); PISLIK_TUTUCU((sebeke[0] - 30, sebeke[1]), 0.45, 0)
        mtyblk.insert('MTY-SU SAYACI', (sebeke[0] - 46, sebeke[1]), 0, 0.3); CEKVALF((sebeke[0] - 62, sebeke[1]), 0.45, 0)
        T((sebeke[0] - 70, sebeke[1] + 12), 'ŞEBEKE Ø32 - ANA SAYAÇ (BİNA GİRİŞİ) → DBK → ÇATI DEPOSU', 6, TSC, 'R')


def yasak_kontrol():
    """geometrik kontrol: hiçbir boru betonarme kolon/perde, asansör boşluğu ve enerji odası içinden geçmez;
    ana dağıtım hatları daire mahallerine girmez (yalnız kapıdaki son 40 cm serbest)."""
    from shapely import affinity
    rep = []
    for k in FL:
        m = sx(k)
        T_ = [m[0], m[1], m[3], m[4], m[2], m[5]]
        Z = [dict(tip=z['tip'], g=affinity.affine_transform(z['g'], T_)) for z in DATA[k]['YASAK']]
        w = M.win(k)
        (wx0, wy0), (wx1, wy1) = [(m[0] * p[0] + m[1] * p[1] + m[2], m[3] * p[0] + m[4] * p[1] + m[5]) for p in ((w[0], w[1]), (w[2], w[3]))]
        for n in gp.NET:
            pts = n['pts']
            if not (wx0 - 5 <= pts[0][0] <= wx1 + 5 and wy0 - 5 <= pts[0][1] <= wy1 + 5):
                continue
            ls = LineString(pts) if len(pts) > 1 else None
            if ls is None:
                continue
            for z in Z:
                it = ls.intersection(z['g'])
                if not it.is_empty and it.length > 0.5:
                    rep.append(dict(kat=k, tip=z['tip'], hat=n['lay'], uz=round(it.length, 1)))
        rms = DATA[k].get('ROOMS') or []
        # not: oda tespiti kapı boşluğundan taşıp ortak alanla birleşen (> 28 m²) poligonlar daire sınırı sayılmaz
        dpol = [affinity.affine_transform(r['poly'].buffer(-8), T_) for r in rms if r['area'] <= 28.0 and
                r['name'].split()[0] in ('salon', 'yatak', 'oda', 'yüklük', 'antre-kor.', 'mutfak', 'banyo', 'wc+banyo', 'wc-lvb.', 'duş')]
        for kk, pts in ANA_HAT:
            if kk != k or len(pts) < 2:
                continue
            ls = LineString(pts)
            core = ls.difference(Point(pts[-1]).buffer(40)).difference(Point(pts[0]).buffer(10))
            for pg in dpol:
                it = core.intersection(pg)
                if not it.is_empty and it.length > 1.0:
                    rep.append(dict(kat=k, tip='DAİRE İÇİ ANA HAT', hat='ana', uz=round(it.length, 1)))
    return rep



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
        if groups and groups[-1][0]['p'][1] - c['p'][1] <= 450:      # grup boyu en çok 4,5 m (kullanıcı: 4 rögar)
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
            cap_pis(((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2), ang, '%d SB' % sbk, 'Ø%d' % max(100, c['dn']), PRM['k_cap'])
            METRAJ_ADD('PİS SU ZEMİN ALTI (PVC) Ø%d' % max(100, c['dn']), pts)
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
        cap_pis(m, 90 if vert else 0, '%d SB' % acc, 'Ø%d' % max(150, dn_sb(acc, True)), PRM['k_cap'])
        METRAJ_ADD('PİS SU RÖGAR ARASI (PVC) Ø%d' % max(150, dn_sb(acc, True)), pts)
        T((m[0] + (22 if vert else 0), m[1] - (0 if vert else 14)), '%1', 6, PSC, 'L', 90 if vert else 0)
    T((x0, y0 - 60), 'TEMEL PLANI: MİMARİDEN YALNIZ BETONARME KOLON/PERDELER VE BİNA DIŞ HATTI. KOLON DİPLERİ ZEMİN KOTUNDAN AYRI AYRI BİNA DIŞINDAKİ RÖGARLARA.', 7, YZ, 'L')
    T((x0, y0 - 80), 'KOLON-RÖGAR BAĞLANTI ÇAPI HESABI: kolon toplam SB ≤ 160 → Ø100 (TS EN 12056-2 / DIN 1986 tablosu; zemin altı en az Ø100). Rögarlar arası Ø150 %1.', 7, YZ, 'L')
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
    global STATS_SB, YBP, RISERS, DBK
    for k in FL:                       # kat planı farklılığı: karşılıksız ıslak hacimlere yeni kolon (P10..)
        for w in DATA[k]['wet']:
            kolon_of(k, w)
    RISERS = riser_gruplari()
    # DBK: bina girişine en yakın ADK kolonunun 18 cm yanında (şebeke -> çatı deposu)
    bg = [a[1][0] for a in DZ['R'] if a[0] == 'T' and 'bina' in a[2][0] and 'giri' in a[2][0]]
    if bg:
        r = min(RISERS.values(), key=lambda r_: math.hypot(r_['p'][0] - bg[0][0], r_['p'][1] - bg[0][1]))
        dn = r['dn']
        DBK = (r['p'][0] - dn[1] * 18.0, r['p'][1] + dn[0] * 18.0)
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
    out['depo'] = dict(karar=DEPO, neden=DEPO_NEDEN)
    out['adk'] = {n: dict(p=[round(v) for v in r['p']], daire=r['digits']) for n, r in RISERS.items()}
    out['ek_makine'] = {k: [(f['kind'], f['daire']) for f in DATA[k]['EK']] for k in FL}
    # kolon -> rögar bağlantı çapı: hesap (dn_sb, zemin altı en az Ø100) / kullanıcı çizimi Ø125
    out['kolon_rogar'] = [(c['name'], sum(STATS_SB[c['name']].values()), max(100, dn_sb(sum(STATS_SB[c['name']].values()), WCK[c['name']])))
                          for c in KOLS]
    yerlesim()
    bh, rep = temel()
    out['temel_kolon_kesen'] = rep
    out['rogar'] = {k: dict(p=[round(v) for v in v_['p']], kols=v_['kols']) for k, v_ in ROG.items()}
    out['kat'] = {}
    for k in FL:
        out['kat'][k] = kat_plani(k)
    out['yasak'] = yasak_kontrol()
    out['bina_alani'] = bh.area / 1e4
    out['balkon'] = [(b['k'], [round(v) for v in b['p']]) for b in BALKON]
    global ROOF_A
    ROOF_A = round(bh.area / 1e4 * 1.10, 2)          # çatı izdüşümü ~ taban alanı + %10 saçak (DENEME varsayımı)
    import sema
    out['sema'] = sema.ciz(globals())
    # kolon (dikey) boyları: kat yüksekliği 3 m, + çatı üstü havalık 0,5 m
    for c in KOLS:
        n = len(STATS_SB[c['name']])
        METRAJ['PİS SU KOLONU (PVC) Ø%d' % c['dn']] = METRAJ.get('PİS SU KOLONU (PVC) Ø%d' % c['dn'], 0) + 3.0 * len(FL) + 0.5
    for r in RISERS.values():
        METRAJ['TEMİZ SU ADK KOLONU (PPRC) Ø32'] = METRAJ.get('TEMİZ SU ADK KOLONU (PPRC) Ø32', 0) + 3.0 * len(FL) + 1.0
    METRAJ['TEMİZ SU DBK KOLONU (PPRC) Ø32'] = 3.0 * len(FL) + 1.0
    out['metraj'] = {k: round(v, 1) for k, v in sorted(METRAJ.items())}
    adet = {}
    for k in FL:
        for f in DATA[k]['F']:
            if f.get('daire'):
                adet[f['kind']] = adet.get(f['kind'], 0) + 1
    adet['BALKON_SUZGEC'] = len(BALKON)
    out['adet'] = adet
    return out


STATS_SB, YBP, ROOF_A = {}, [], 0.0

if __name__ == '__main__':
    OUT = main()
    import cikti
    cikti.yaz(OUT, globals())
