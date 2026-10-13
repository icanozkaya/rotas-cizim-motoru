"""EMİNE TUNÇEL - 2 dükkan (zemin) + 8 ofis (1. ve 2. kat, katta 4) - SASKİ altyapılı.
Isıtma: ofisler kombili yerden ısıtma, dükkanlar duvar tipi split klima (şemada da).
Çerçeve: 1. KAT PLANI kaynak koordinatı (cm). Kaynak kaydırmaları: zemin -3686, 2. kat +3682, çatı +7367.
Kot: ±0,00 = +27,55 (yol +27,35). Kat yüksekliği 3,50 (1. kat +4,70 / 2. kat +8,20 / çatı +11,70).
Ön cephe (yol) planın üstü (≈ kuzey), arka cephe altı; yan duvarlar bitişik nizam (yangın duvarı).
"""
import math, pickle, re, sys
from shapely.geometry import LineString, Polygon, box
from shapely import affinity
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2'); sys.path.insert(0, '/home/claude/nb/p3')
import cad
from cad import L, PL, C, T, RECT, RRECT, ARC, ARROW, SOL, push, pop, MOVE, VANA, CEKVALF, SAYAC, PISLIK_TUTUCU, TEMIZLEME_KAPAGI
import mtyblk
import gp
from gp import CS, CH, PS, PST, TSC, PSC, YBL, VN, CD, YZ, YL, YC, pipe, node, Fix, cap_temiz, cap_pis, fmt, dn_temiz, dn_sb

FLAT = pickle.load(open('/tmp/claude-0/p3/et.dxf.flat.pkl', 'rb'))
SRC = {'Z': -3686.0, '1': 0.0, '2': 3682.0, 'C': 7367.0}
WIN = (29280.0, -12420.0, 32470.0, -11330.0)        # bina + yakın çevre (çerçeve)
BX0 = 29280.0
SLOT = 3800.0
SLOTS = {'T': 0, 'Z': 1, '1': 2, '2': 3, 'C': 4}
FY0, FY1 = -12900.0, -10950.0                     # sıhhi pafta sırası
HDY = -2150.0                                     # ısıtma / klima sırası
NAMES = {'T': 'ALTYAPI PLANI (ZEMİN KOTU)', 'Z': 'ZEMİN KAT SIHHİ TESİSAT PLANI', '1': '1. KAT SIHHİ TESİSAT PLANI',
         '2': '2. KAT SIHHİ TESİSAT PLANI', 'C': 'ÇATI PLANI (SU DEPOSU / HAVALIKLAR / YAĞMUR)'}
KOT = {'T': '±0,00 = +27,55 (KOLON DİPLERİ)', 'Z': '±0,00 [+27,55]  SBS +0,20', '1': '+4,70', '2': '+8,20', 'C': '+11,70 ÇATI'}


def dx(k):
    return SLOTS[k] * SLOT - BX0 + 330.0


# ================================================================== mimari (bu mimarın katmanları)
WALL_L = {'rtm-duv tugla', 'rtm-tas_betonarme', 'rtm-sıva', 'rtm-kapı-ahsap', 'rtm-pen-ahsap', 'Kapi_Pencere', 'rtm-cam', 'SIVA',
          'rtm-merdiven', 'rtm-merdiven izdusum', 'rtm-plan katmanı-03', 'BALKON', 'rtm-izdusum-üst ince'}
COL_L = {'P-KOLON'}
FURN_L = {'rtm-tefris vitrifiye', '0', 'rtm-plan katmanı-04', 'KUTUPHANE'}
ROOF_L = WALL_L | {'0', 'rtm-plan katmanı-04', 'P-KİRİŞ'}


def _clean(s):
    return re.sub(r'\\[A-Za-z][^;]*;|\\[A-Za-z]|[{}]|\\P', ' ', s).strip()


def copy_arch(win, furn=True, vitrifiye=False, labels=True, roof=False):
    """mimariyi kaynak koordinatından (o anki dönüşümle) kopyala. furn: tezgah/dolap; vitrifiye: mimarın vitrifiyesi
    (sıhhi planda MTY blokları kullanıldığından çizilmez, ısıtma planında tefriş korunur). labels: mahal adı + m²."""
    x0, y0, x1, y1 = win
    ins = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    lays = (ROOF_L if roof else WALL_L)
    for r in FLAT:
        k, lay = r[0], r[1]
        if lay in COL_L:
            tl = gp.ARC_K
        elif lay in lays:
            tl = gp.ARC_L
        elif furn and lay in FURN_L and (vitrifiye or lay != 'rtm-tefris vitrifiye'):
            tl = gp.ARC_F
        else:
            tl = None
        if tl:
            if k == 'L' and ins(r[2][0]) and ins(r[2][1]):
                L(r[2][0], r[2][1], tl)
            elif k == 'P' and all(ins(p) for p in r[2]):
                PL(r[2], tl)
            elif k == 'C' and ins(r[2][:2]):
                C(r[2][:2], r[2][2], tl)
        if k == 'T' and labels and lay == 'rtm-mhl-yazı-malzeme' and ins(r[2][0]):
            s = _clean(r[2][1])
            if re.fullmatch(r'[0-9]+\.[0-9]+ m²', s) or (s.isupper() and len(s) <= 22 and not s.startswith(('DİLATASYON', 'BİTİŞİK',
                                                                                                             'YANGIN'))):
                T(r[2][0], s, 9 if 'm²' in s else 10, gp.ARC_T, 'L')


def COLS(src=0.0):
    out = []
    for r in FLAT:
        if r[1] == 'P-KOLON' and r[0] == 'P' and len(r[2]) >= 4:
            q = r[2]
            if all(WIN[0] + src - 10 <= p[0] <= WIN[2] + src + 10 and WIN[1] <= p[1] <= WIN[3] for p in q):
                pg = Polygon([(p[0] - src, p[1]) for p in q]).buffer(0)
                if pg.area > 200 and not any(pg.symmetric_difference(o).area < 1 for o in out):
                    out.append(pg)
    return out


def floor_arch(k, sy=0.0, heat=False):
    push(MOVE(dx(k) - SRC[k], sy))
    w = (WIN[0] + SRC[k], WIN[1], WIN[2] + SRC[k], WIN[3])
    copy_arch(w, furn=True, vitrifiye=heat, labels=True, roof=(k == 'C'))
    pop()


def frame_title(k, sy, sub=None):
    gp.title((dx(k) + 30875.0, -12560.0 + sy), NAMES[k] if sy == 0 else sub, 'ÖLÇEK : 1/50   KOT: ' + KOT[k])


# ================================================================== ofisler (çerçeve koordinatı; 2. kat aynı)
XM_R, XM_F = 30862.5, 30875.5        # arka / ön ofis çiftlerinin ayna ekseni


def mx(p, xm):
    return (2 * xm - p[0], p[1])


def mfix(f, xm, name):
    # kombi bloğu aynalanır (baca yine dış cepheye bakar); diğer armatürler döndürülür (sıcak/soğuk tarafı korunur)
    return Fix(f.kind, mx(f.o, xm), -f.rot, sx=-1.0 if f.kind == 'KOMBI' else 1.0, name=name)


# ---- armatürler (Fix: o = duvar yüzü, +y odaya)
F_O1 = {'WC': Fix('WC', (30315.0, -12286.0), 0), 'LV': Fix('LV', (30392.0, -12168.0), 90), 'YS': Fix('YS', (30332.0, -12190.0), 0),
        'EV': Fix('EV', (30262.0, -12152.0), 90), 'BM': Fix('BM', (30262.0, -12190.0), 90),
        'KM': Fix('KOMBI', (30103.0, -12205.0), -90)}   # mutfak batı duvarında, baca arka cepheye
F_O2 = {'WC': Fix('WC', (29770.0, -11805.0), -90), 'LV': Fix('LV', (29898.0, -11899.0), 0), 'YS': Fix('YS', (29878.0, -11812.0), 0),
        'EV': Fix('EV', (30746.0, -11903.0), 0), 'BM': Fix('BM', (30790.0, -11903.0), 0),
        'KM': Fix('KOMBI', (30860.0, -11530.0), 90)}    # ön odada (dış cepheye bitişik) doğu duvarında, baca doğrudan ön cepheden dışarı
F_O4 = {k: mfix(f, XM_R, k) for k, f in F_O1.items()}
F_O3 = {k: mfix(f, XM_F, k) for k, f in F_O2.items()}
# dükkan WC'leri (zemin) arka ofis WC'lerinin altında
F_D1 = {'WC': F_O1['WC'], 'LV': F_O1['LV'], 'YS': F_O1['YS']}
F_D2 = {'WC': F_O4['WC'], 'LV': F_O4['LV'], 'YS': F_O4['YS']}

# ---- pis su kolonları (ıslak hacmin köşesinde; zeminde biter, zemin kotundan bina önündeki rögara)
PK = {'PK1': (30388.0, -12280.0), 'PK2': (29824.0, -11884.0)}
MK = {'MK1': (30247.0, -12232.0), 'MK2': (30812.0, -11895.0)}
PK['PK4'] = mx(PK['PK1'], XM_R); PK['PK3'] = mx(PK['PK2'], XM_F)
MK['MK4'] = mx(MK['MK1'], XM_R); MK['MK3'] = mx(MK['MK2'], XM_F)
# zemin katta dükkân ortasına / koridor ortasına düşen kolonlar zemin tavanında (asma tavan) en yakın duvara kaydırılıp
# oradan zemin kotuna iner (ZK: zemin kat kolon yeri)
ZK = {'PK2': (29830.0, -12290.0), 'MK2': (30857.0, -11895.0), 'MK3': (30857.0, -11872.0)}
KOLON_OF = {'O1': ('PK1', 'MK1'), 'O2': ('PK2', 'MK2'), 'O3': ('PK3', 'MK3'), 'O4': ('PK4', 'MK4')}

# ---- temiz su kolonları (merdiven holü KB köşesi, kolon kutusu): sayaç grubundan katlara + depo kolonları
# temiz su kolonları - TAMAMI ORTAK ALANDA (merdiven holü), her katta aynı hizada, kapı önlerinden ve betonarme
# kolonlardan geçmez, başka bağımsız bölüm içinden üst katlara taşınmaz:
#  O1/O5 : merdiven holü KB köşesi (O1 kapısının üstü) - O1 holüne doğrudan girer
#  O2/O6, O3/O7, ADK, DBK : O2 giriş kapısının doğusunda, hol kuzey duvarı önünde
#  O4/O8 : merdiven KD köşesi (O3 kapısı ile O4 kapısı arasındaki cep) - O4 holüne kapının üstünden girer
#  zeminde sayaçtan bu kolonlara hatlar merdiven holü asma tavanından gider
RZ = {'O1': (30448.0, -11948.0), 'O5': (30460.0, -11937.0), 'O2': (30610.0, -11950.0), 'O6': (30622.0, -11950.0),
      'O3': (30646.0, -11950.0), 'O7': (30658.0, -11950.0), 'ADK': (30670.0, -11950.0), 'DBK': (30712.0, -11950.0),
      'O4': (31287.0, -11932.0), 'O8': (31287.0, -11944.0)}
SAY_X = {'DK1': 30436.0, 'O1': 30448.0, 'O5': 30460.0, 'O2': 30610.0, 'O6': 30622.0, 'O3': 30646.0, 'O7': 30658.0,
         'O4': 30724.0, 'O8': 30736.0, 'DK2': 30748.0}
KOLL_Y = -12060.0                 # sayaç kollektörü kotu (plan y) - asansör perdesi önü
ANA_NIS = (30830.0, -11408.0)     # bina ön girişi (merdiven koridoru) ana sayaç nişi - kapının doğusunda
DEPO = (29817.0, -11968.0, 30367.0, -11758.0)   # mimari çatı planındaki 15 m³ depo (çerçeve)
DEPO_V = 15.0

# ---- yağmur inişleri: mimarın Y.İ.B noktaları (zemin kaynak + 3686) -> 4 köşe
YB_PTS = {'YB1': (29359.0, -11410.0), 'YB2': (32398.0, -11410.0), 'YB3': (32375.0, -12317.0), 'YB4': (29342.0, -12317.0)}
ROOF_A = round((32402 - 29325) / 100.0 * (12320 - 11430) / 100.0 + 2 * 0.45 * 30.8, 2)   # çatı + saçak izdüşümü

# ---- yük / su birimleri
SB = gp.SB
SB_WC = SB['WC'] + SB['LV'] + SB['YS']           # 14
SB_MT = SB['EV'] + SB['BM']                      # 8
YB_OF = 0.5 + 0.5 + 0.5 + 1.0                    # WC + LV + EV + BM (soğuk) = 2.5 ; sıcak LV+EV
YB_DK = 1.0                                      # dükkan WC + LV
KOMBI_SPEC = ['DUVAR TİPİ HERMETİK YOĞUŞMALI KOMBİ (HER OFİSE 1 ADET) 24 kW',
              'SICAK SU: 11,5 l/dk (ΔT=30 K) - BACA Ø60/100 DIŞ CEPHEYE',
              'YERDEN ISITMA: GİDİŞ/DÖNÜŞ 45/35 °C (KOMBİ DÜŞÜK SICAKLIK AYARLI)']


# ================================================================== yardımcılar: mimari duvar çizgileri / kolonlar (çerçeve koordinatı)
import router as RT

WALL_ROUTE_L = {'rtm-duv tugla', 'rtm-tas_betonarme', 'rtm-sıva', 'SIVA', 'Kapi_Pencere', 'rtm-pen-ahsap', 'rtm-cam'}


def wall_lines(k, win, lays=WALL_ROUTE_L):
    s = SRC[k]
    x0, y0, x1, y1 = win
    out = []
    for r in FLAT:
        if r[1] not in lays or r[0] not in ('L', 'P'):
            continue
        q = [(p[0] - s, p[1]) for p in (r[2] if r[0] == 'P' else (r[2][0], r[2][1]))]
        if all(x0 - 5 <= p[0] <= x1 + 5 and y0 - 5 <= p[1] <= y1 + 5 for p in q):
            out.append(q)
    return out


_COLS = {}


def cols(k):
    if k not in _COLS:
        _COLS[k] = COLS(SRC[k])
    return _COLS[k]


_DOORS = {}


def doors(k):
    """kapı kanadı + açılım bölgeleri (mimari kapı katmanından kümelenmiş)"""
    if k not in _DOORS:
        from shapely.ops import unary_union
        s = SRC[k]
        segs = []
        for r in FLAT:
            if r[1] == 'rtm-kapı-ahsap' and r[0] in 'LP':
                q = r[2] if r[0] == 'P' else [r[2][0], r[2][1]]
                if len(q) > 1 and all(WIN[0] + s <= p[0] <= WIN[2] + s and WIN[1] <= p[1] <= WIN[3] for p in q):
                    segs.append(LineString([(p[0] - s, p[1]) for p in q]).buffer(4))
        u = unary_union(segs)
        _DOORS[k] = [box(*g.bounds) for g in (u.geoms if hasattr(u, 'geoms') else [u])]
    return _DOORS[k]


def grid_for(k, win, extra_block=(), step=2.0):
    from shapely.geometry import Point as _P
    g = RT.Grid(win, step, walls=wall_lines(k, win), obstacles=[c for c in cols(k) if c.intersects(box(*win))])
    for d in doors(k):                       # kapı önü / kanadı: boru buradan geçmesin (yüksek maliyet)
        if d.intersects(box(*win)):
            g.add_cost(d.buffer(6, join_style=2), 4.0)
    for p in extra_block:
        g.add_block(_P(p).buffer(5.0), pad=0.0)
    return g


def P2(p, xm):          # ayna (None: aynen)
    return p if xm is None else mx(p, xm)


# ================================================================== ofis sıhhi tesisatı (1. ve 2. kat aynı)
# pis su: elle (kısa, kolona doğrudan) - O1 / O2 tanımı, O4 / O3 aynası
PIS_O1 = [[('WC', 'PS'), (30388.0, -12266.0), 'PK1'], [('LV', 'PS'), (30377.0, -12266.0)], [('YS', 'PS'), (30377.0, -12190.0)],
          [('EV', 'PS'), 'MK1']]
PIS_O2 = [[('WC', 'PS'), (29824.0, -11805.0), 'PK2'], [('YS', 'PS'), (29878.0, -11830.0), (29824.0, -11830.0)],
          [('LV', 'PS'), 'PK2'], [('EV', 'PS'), (30746.0, -11880.0), (30812.0, -11880.0), 'MK2'],
          [('BM', 'PS'), (30790.0, -11880.0)]]
OFIS = {   # ad: (armatürler, pis tanımı, ayna ekseni, kolon adları (tanımdaki -> gerçek), giriş noktası, ofis penceresi)
    'O1': (F_O1, PIS_O1, None, {'PK1': 'PK1', 'MK1': 'MK1'}, (30395.0, -11948.0), (29330.0, -12320.0, 30410.0, -11900.0)),
    'O2': (F_O2, PIS_O2, None, {'PK2': 'PK2', 'MK2': 'MK2'}, (30610.0, -11898.0), (29750.0, -11920.0, 30880.0, -11430.0)),
    'O3': (F_O3, PIS_O2, XM_F, {'PK2': 'PK3', 'MK2': 'MK3'}, (31120.0, -11898.0), (30870.0, -11920.0, 32000.0, -11430.0)),
    'O4': (F_O4, PIS_O1, XM_R, {'PK1': 'PK4', 'MK1': 'MK4'}, (31420.0, -11938.0), (31315.0, -12320.0, 32395.0, -11900.0)),
}
ALLK = dict(PK, **MK)
# ofis odaları: temiz / sıcak su hatları ODADAN GEÇMEZ - holden ve ıslak hacim duvarlarından gider
ODALAR = {
    'O1': [(29352, -11891, 29741, -11451), (29346, -12281, 29598, -11928), (29631, -12281, 30073, -12058)],
    'O2': [(29778, -11739, 30096, -11451), (30115, -11739, 30428, -11451), (30460, -11739, 30843, -11451)],   # doğu duvarı dibi: kombi hattı (duvar içi)
    'O3': [(30911, -11739, 31280, -11451), (31310, -11739, 31636, -11451), (31655, -11739, 31975, -11451)],
    'O4': [(32010, -11891, 32391, -11451), (32131, -12281, 32383, -11928), (31655, -12281, 32100, -12058)],
}
# odalar (ofis/çalışma odası): temiz su / sıcak su hatları ODADAN GEÇMEZ, holden ve ıslak hacim duvarlarından gider
ODALAR = {
    'O1': [(29352, -11891, 29741, -11451), (29346, -12281, 29598, -11928), (29631, -12281, 30073, -12058)],
    'O2': [(29778, -11739, 30096, -11451), (30115, -11739, 30428, -11451), (30460, -11739, 30843, -11451)],   # doğu duvarı dibi: kombi hattı (duvar içi)
    'O3': [(30911, -11739, 31280, -11451), (31310, -11739, 31636, -11451), (31655, -11739, 31975, -11451)],
    'O4': [(32010, -11891, 32391, -11451), (32131, -12281, 32383, -11928), (31655, -12281, 32100, -12058)],
}
ZK['PK3'] = (2 * XM_F - ZK['PK2'][0], ZK['PK2'][1])
ZKOL = {nm: ZK.get(nm, p) for nm, p in ALLK.items()}       # zemin kotundaki kolon dipleri


def pis_paths(of):
    F, defs, xm, km, E, win = OFIS[of]
    out = []
    for d in defs:
        pts = []
        for q in d:
            if isinstance(q, tuple) and isinstance(q[0], str):
                pts.append(F[q[0]].cp(q[1]))
            elif isinstance(q, str):
                pts.append(ALLK[km[q]])
            else:
                pts.append(P2(q, xm))
        out.append(pts)
    return out


_SUP_CACHE = {}


def supply_paths(of, k='1'):
    """soğuk + sıcak su: giriş noktasından armatürlere A* güzergâh (duvar dibi, kesişme cezalı)"""
    if of in _SUP_CACHE:
        return _SUP_CACHE[of]
    F, defs, xm, km, E, win = OFIS[of]
    kol = [ALLK[v] for v in km.values()]
    g = grid_for(k, win, extra_block=kol)
    for r in ODALAR[of]:
        g.add_block(box(r[0] + 3, r[1] + 3, r[2] - 3, r[3] - 3), pad=0.0)
    pis = pis_paths(of)
    for p in pis:
        g.add_line(p, 'P')
    cold, hot = [], []
    p = g.route(E, F['KM'].cp('SO'), 'S'); cold.append(p); g.add_line(p, 'S')
    for f in ('EV', 'BM', 'LV', 'WC'):
        p = g.route(F[f].cp('SO'), None, 'S', to_tree=True, wsys={'P': 0.35}, free_end=4.0)
        cold.append(list(reversed(p))); g.add_line(p, 'S')
    p = g.route(F['KM'].cp('SC'), F['EV'].cp('SC'), 'H', free_end=4.0); hot.append(p); g.add_line(p, 'H')
    p = g.route(F['LV'].cp('SC'), None, 'H', to_tree=True, free_end=4.0); hot.append(list(reversed(p))); g.add_line(p, 'H')
    _SUP_CACHE[of] = (cold, hot)
    return cold, hot


def ofis(of, k):
    F, defs, xm, km, E, win = OFIS[of]
    for nm, f in F.items():
        f.name = '%s.%s' % (of, nm)
        f.draw()
    for p in pis_paths(of):
        pipe(p, PS, 'P')
    cold, hot = supply_paths(of)
    for p in cold:
        pipe(p, CS, 'S')
    for p in hot:
        pipe(p, CH, 'S')
    VANA(E, 0.4, 0)
    # çap / yük etiketleri
    no = int(of[1]) + (4 if k == '2' else 0)
    c0 = cold[0]
    mid = max(zip(c0[:-1], c0[1:]), key=lambda s: math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]))
    ang = 0 if abs(mid[0][1] - mid[1][1]) < 0.1 else 90
    cap_temiz(((mid[0][0] + mid[1][0]) / 2, (mid[0][1] + mid[1][1]) / 2), ang, so='O%d %s YB' % (no, fmt(YB_OF)),
              socp='Ø%d' % dn_temiz(YB_OF), k=5.0)
    h0 = hot[0]
    mid = max(zip(h0[:-1], h0[1:]), key=lambda s: math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]))
    ang = 0 if abs(mid[0][1] - mid[1][1]) < 0.1 else 90
    cap_temiz(((mid[0][0] + mid[1][0]) / 2, (mid[0][1] + mid[1][1]) / 2), ang, sc='1.0 YB', sccp='Ø20', k=5.0)
    wc = pis_paths(of)[0]
    cap_pis(((wc[0][0] + wc[1][0]) / 2, (wc[0][1] + wc[1][1]) / 2), 0 if abs(wc[0][1] - wc[1][1]) < 0.1 else 90,
            '%d SB' % SB['WC'], 'Ø100', 4.5)


# kolon başına taşınan SB (1. ve 2. kat ofisleri + zemin dükkân WC'leri PK1 / PK4'e)
def kolon_sb(nm, k):
    n = {'Z': 2, '1': 2, '2': 1}[k]
    if nm.startswith('PK'):
        return n * SB_WC + (SB_WC if (k == 'Z' and nm in ('PK1', 'PK4')) else 0)
    return n * SB_MT


def kolonlar(k, labels=True):
    if k == 'Z':           # zeminde orta alana düşen kolonlar: tavanda en yakın duvara kaydır, oradan zemin kotuna
        for nm, q in ZK.items():
            p = ALLK[nm]
            C(p, 5.0, PST); L((p[0] - 4, p[1] - 4), (p[0] + 4, p[1] + 4), PST)
            pts = [p, (p[0], q[1]), q] if abs(q[0] - p[0]) > 1 and abs(q[1] - p[1]) > 1 else [p, q]
            pipe(pts, PST, 'PT')
            node(p, nm + '-ÜST'); node(q, nm)
            m = ((pts[-2][0] + pts[-1][0]) / 2, (pts[-2][1] + pts[-1][1]) / 2)
            vert = abs(pts[-2][0] - pts[-1][0]) < 1
            T((m[0] + (8 if vert else 0), m[1] + (0 if vert else 6)), '%s ASMA TAVANDA DUVARA KAYDIRILIR Ø%d %%2' % (nm, 100 if nm[0] == 'P' else 70),
              5.5, PSC, 'C' if not vert else 'L', 0 if not vert else 90)
    offs = {'PK1': (40, 45), 'MK1': (-45, 50), 'PK2': (45, -40), 'MK2': (-40, 45), 'PK3': (-45, -40), 'MK3': (40, 45),
            'PK4': (-40, 45), 'MK4': (45, 50)}
    for nm, p in sorted((ZKOL if k == 'Z' else ALLK).items()):
        gp.kolon_pis(p, nm, offs[nm], k=0.6 if nm[0] == 'P' else 0.5)
        if labels:
            T((p[0] + offs[nm][0] + (2 if offs[nm][0] > 0 else -2), p[1] + offs[nm][1] - 16),
              'Ø%d / %d SB' % (100 if nm[0] == 'P' else 70, kolon_sb(nm, k)), 6.5, PSC, 'L' if offs[nm][0] > 0 else 'R')


def gecen_kolonlar(k):
    """temiz su kolonları (merdiven holü): bu kattan geçen / biten"""
    for nm, p in RZ.items():
        if nm in ('ADK', 'DBK') or (k == '1') or nm in ('O5', 'O6', 'O7', 'O8'):
            gp.kolon_temiz(p)
            node(p, nm)
            T((p[0] + (-3 if nm in ('O1', 'O5') else 3), p[1] - 5), nm, 3.5, TSC, 'R' if nm in ('O1', 'O5') else 'L', -90 if nm not in ('O1', 'O5', 'O4', 'O8', 'DBK') else 0)
    T((30600.0, -11978.0), 'TEMİZ SU KOLONLARI (KOLON KUTUSU İÇİNDE) O1-O8 Ø25 / ADK Ø40', 5.0, TSC, 'L')


# kat holü temiz su hatları: kolon -> ofis girişi (çerçeve koordinatı)
def hol_hatlari(k):
    """kat holü temiz su hatları: kolon -> ofis girişi (kapı önünden geçmez)"""
    names = {'O1': 'O1', 'O2': 'O2', 'O3': 'O3', 'O4': 'O4'} if k == '1' else {'O1': 'O5', 'O2': 'O6', 'O3': 'O7', 'O4': 'O8'}
    out = {}
    for of, rn in names.items():
        r = RZ[rn]
        E = OFIS[of][4]
        if of == 'O1':
            out[of] = [r, E] if abs(r[1] - E[1]) < 0.1 else [r, (E[0], r[1]), E]
        elif of == 'O2':
            out[of] = [r, E] if abs(r[0] - E[0]) < 0.1 else [r, (r[0], -11910.0), (E[0], -11910.0), E]
        elif of == 'O3':
            out[of] = [r, (r[0], -11932.0), (E[0], -11932.0), E]
        else:
            out[of] = [r, (E[0], r[1]), E]
    return out, names


def normal_kat(k):
    push(MOVE(dx(k), 0.0))
    for of in OFIS:
        ofis(of, k)
    hh, names = hol_hatlari(k)
    for of, pts in hh.items():
        pipe(pts, CS, 'S')
    kolonlar(k)
    gecen_kolonlar(k)
    T((29360.0, -12370.0), 'OFİS KOMBİLERİ: ' + KOMBI_SPEC[0], 6.5, CD, 'L')
    T((29360.0, -12382.0), KOMBI_SPEC[1] + ' (TÜM KOMBİLER DIŞ CEPHEYE BİTİŞİK MAHALDE, BACA DOĞRUDAN DIŞ ATMOSFERE)', 6.5, CD, 'L')
    pop()


# ================================================================== ZEMİN KAT
F_D = {'DK1': (F_D1, None, 'PK1'), 'DK2': (F_D2, XM_R, 'PK4')}
DK_E = {'DK1': (30400.0, -11990.0), 'DK2': (31330.0, -11955.0)}
_DK_CACHE = {}


def dukkan_wc(nm):
    F, xm, pk = F_D[nm]
    if nm not in _DK_CACHE:
        win = (30200.0, -12320.0, 30440.0, -11960.0) if nm == 'DK1' else (31300.0, -12320.0, 31480.0, -11900.0)
        g = grid_for('Z', win, extra_block=[PK[pk]])
        defs = [d for d in PIS_O1 if d[0][0] in ('WC', 'LV', 'YS')]
        pis = []
        for d in defs:
            pts = [F[q[0]].cp(q[1]) if isinstance(q, tuple) and isinstance(q[0], str) else (PK[pk] if isinstance(q, str) else P2(q, xm))
                   for q in d]
            pis.append(pts); g.add_line(pts, 'P')
        E = DK_E[nm]
        c = [g.route(E, F['WC'].cp('SO'), 'S')]
        g.add_line(c[0], 'S')
        p = g.route(F['LV'].cp('SO'), None, 'S', to_tree=True); c.append(list(reversed(p)))
        _DK_CACHE[nm] = (pis, c)
    return _DK_CACHE[nm]


def zemin():
    push(MOVE(dx('Z'), 0.0))
    for nm in ('DK1', 'DK2'):
        F = F_D[nm][0]
        for fn, f in F.items():
            f.name = '%s.%s' % (nm, fn)
            f.draw()
        pis, cold = dukkan_wc(nm)
        for p in pis:
            pipe(p, PS, 'P')
        for p in cold:
            pipe(p, CS, 'S')
        E = DK_E[nm]
        VANA(E, 0.4, 0)
        cap_temiz((E[0] + (-40 if nm == 'DK1' else 40), E[1] - 8), 0, so='%s %s YB' % (nm, fmt(YB_DK)), socp='Ø20', k=5.0)
    # ---- şebeke -> ana sayaç nişi (ön cephe, giriş kapısının doğusu) -> DBK (O2/O3 ara duvarı içinde çatı deposuna)
    nx, ny = ANA_NIS
    RECT(nx - 30, ny - 12, nx + 30, ny + 8, VN)
    T((nx + 36, ny + 14), 'ANA SAYAÇ NİŞİ (SASKİ)', 7, VN, 'L')
    xw = nx - 22.0
    pipe([(xw, -11260.0), (xw, ny - 2), (nx + 30, ny - 2)], CS, 'S')
    node((xw, -11260.0), 'ŞEBEKE')
    VANA((xw, -11300.0), 0.5, 90)
    PISLIK_TUTUCU((nx - 10, ny - 2), 0.45, 0); SAYAC((nx + 4, ny - 2), 0.6, 0); CEKVALF((nx + 18, ny - 2), 0.45, 0)
    T((xw - 7, -11270.0), 'ŞEBEKEDEN (SASKİ) Ø40', 7, TSC, 'R', 90)
    db = RZ['DBK']
    pipe([(nx + 30, ny - 2), (30862.0, ny - 2), (30862.0, -11860.0), (db[0], -11860.0), db], CS, 'S')
    cap_temiz((30862.0, -11650.0), 90, so='DBK %s YB' % fmt(YB_TOP), socp='Ø%d' % dn_temiz(YB_TOP), k=5.0)
    # ---- sayaç grubu: ADK -> kollektör -> sayaçlar -> kolonlar / dükkânlar (hatlar kesişmez, kapı önünden geçmez)
    ad = RZ['ADK']
    xl, xr = SAY_X['DK1'], SAY_X['DK2']
    RECT(xl - 8, KOLL_Y - 10, xr + 8, KOLL_Y + 68, VN)
    T((xl - 8, KOLL_Y - 22), 'SAYAÇ GRUBU (BİNA GİRİŞİ - MERDİVEN HOLÜ) 10 ADET SAYAÇ + KÜRESEL VANA + ÇEK VALF', 6.0, VN, 'L')
    pipe([ad, (ad[0], KOLL_Y)], CS, 'S')
    pipe([(xl, KOLL_Y), (xr, KOLL_Y)], CS, 'S')
    for nm, x in SAY_X.items():
        if nm == 'DK1':
            pts = [(x, KOLL_Y), (x, DK_E['DK1'][1]), DK_E['DK1']]
        elif nm in ('O4', 'O8'):    # merdiven holü asma tavanından merdiven KD köşesindeki kolona
            pts = [(x, KOLL_Y), (x, RZ[nm][1]), RZ[nm]]
        elif nm == 'DK2':           # merdiven holü asma tavanından dükkân-2'ye (WC duvarından)
            pts = [(x, KOLL_Y), (x, DK_E['DK2'][1]), DK_E['DK2']]
        else:
            pts = [(x, KOLL_Y), RZ[nm]]
        pipe(pts, CS, 'S')
        VANA((x, KOLL_Y + 12), 0.35, 90); SAYAC((x, KOLL_Y + 32), 0.45, 90); CEKVALF((x, KOLL_Y + 52), 0.35, 90)
        T((x + 3.5, KOLL_Y + 62), nm, 4.5, VN, 'L', 90)
    T((30930.0, -11985.0), 'O4 / O8 / DK2 BESLEMELERİ MERDİVEN HOLÜ (ORTAK ALAN) ASMA TAVANI İÇİNDEN', 5.5, TSC, 'L')
    cap_temiz((ad[0] + 14, -12000.0), 90, so='ADK %s YB' % fmt(YB_TOP), socp='Ø%d' % dn_temiz(YB_TOP), k=4.5)
    for nm, p in RZ.items():
        gp.kolon_temiz(p)
        node(p, nm)
    kolonlar('Z')
    T((29380.0, -12370.0), 'DÜKKÂN WC LAVABOLARINA TEZGAH ALTI 10 L ELEKTRİKLİ SU ISITICI KONACAKTIR. ZEMİNDEN GEÇEN PK / MK KOLONLARI '
      'KOLON KUTUSU İÇİNE ALINACAKTIR.', 6.5, CD, 'L')
    pop()


YB_TOP = 2 * YB_DK + 8 * YB_OF                 # toplam yük birimi (DBK / ADK)


# ================================================================== ALTYAPI PLANI (zemin kotu) - SASKİ onaylı atıksu projesine göre
# kolon dipleri (temizleme kapaklı) zemin döşemesi altından düz olarak bina önündeki muayene bacalarına iner;
# bacalar ön bahçede %1 eğimle doğuya, R9'dan parsel bacasına (PB) ve mevcut kanalizasyon şebekesine (SASKİ, Ø150 SN8 koruge).
R_Y = -11335.0
_GR = []                                       # birbirine çok yakın kolon dipleri aynı bacaya (MK2 + MK3)
for nm, p in sorted(ZKOL.items(), key=lambda kv: kv[1][0]):
    if _GR and p[0] - _GR[-1][1] < 80.0:
        _GR[-1][0].append(nm); _GR[-1][1] = (_GR[-1][1] + p[0]) / 2.0
    else:
        _GR.append([[nm], p[0]])
R_ = {'R%d' % (i + 1): (x, R_Y) for i, (n_, x) in enumerate(_GR)}
R_KOL = {'R%d' % (i + 1): n_ for i, (n_, x) in enumerate(_GR)}
R_['R%d' % (len(_GR) + 1)] = (32470.0, R_Y)
R_LAST = 'R%d' % (len(_GR) + 1)
R_['PB'] = (32470.0, R_Y + 478.0)
R_AK0 = -0.80                                  # R1 akış kotu (±0,00 = +27,55)


def _rogar_kot():
    names = ['R%d' % i for i in range(1, len(_GR) + 2)] + ['PB']
    ak = {names[0]: R_AK0}
    for a, b in zip(names[:-1], names[1:]):
        L_ = math.hypot(R_[b][0] - R_[a][0], R_[b][1] - R_[a][1]) / 100.0
        ak[b] = ak[a] - 0.01 * L_ - 0.02          # %1 eğim + baca içi 2 cm düşü
    return ak


_ALT = {}


def _alt_route(kn):
    """kolon dibinden bacaya döşeme altı güzergâh: betonarme kolonlardan ve diğer hatlardan kaçar (A*)"""
    if not _ALT:
        g = RT.Grid((29300.0, -12340.0, 32500.0, -11300.0), 4.0, obstacles=cols('Z'))
        for rn, kl in R_KOL.items():
            for k_ in kl:
                p = ZKOL[k_]
                q = (R_[rn][0] + (0 if len(kl) == 1 else (p[0] - R_[rn][0])), R_Y - 25.0)
                pts = g.route(p, q, 'T' + k_, turn=20.0)
                g.add_line(pts, 'T' + k_)
                _ALT[k_] = pts
    return _ALT[kn]


def temel():
    push(MOVE(dx('T'), 0.0))
    cs_ = cols('1')
    for pg in cols('Z'):
        x0, y0, x1, y1 = pg.bounds
        PL(list(pg.exterior.coords), gp.ARC_K, True, 1.5)
        L((x0, y0), (x1, y1), gp.ARC_K); L((x0, y1), (x1, y0), gp.ARC_K)
    bx0, by0, bx1, by1 = 29330.0, -12318.0, 32402.0, -11400.0
    PL([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], 'MTY-BINA-HATTI', True)
    T((bx0 + 10, by0 - 22), 'BİNA DIŞ HATTI (RADYE TEMEL ÜSTÜ ±0,00)', 8, gp.ARC_K, 'L')
    T((bx0 + 10, by1 + 140), 'YOL (ÖN CEPHE) +27,35  ↑', 12, YZ, 'L')
    T((29340.0, -12400.0), 'ALTYAPI PLANI: MİMARİ PROJEDEN YALNIZCA BETONARME KOLONLAR VE BİNA DIŞ HATTI ALINMIŞTIR. KOLON DİPLERİ ZEMİN KOTUNDADIR.',
      8, YZ, 'L')
    ak = _rogar_kot()
    for nm, p in R_.items():
        s = 25 if nm != 'PB' else 30
        cad.ROGAR_PLAN(p, s, 'MTY-ROGAR')
        lab = '%s  50x50' % nm if nm != 'PB' else 'PB (MEVCUT PARSEL BACASI) 60x60'
        yo = 40 if nm not in ('PB',) else 0
        xo = -30 if nm != 'PB' else 40
        T((p[0] + xo, p[1] + yo + 12), lab, 7.5, 'MTY-ROGAR', 'L')
        T((p[0] + xo, p[1] + yo), 'K.Ü. -0,20 / A.K. %+.2f' % ak[nm], 6.5, 'MTY-ROGAR', 'L')
    # kolon dipleri -> bacalar
    for rn, kl in R_KOL.items():
      for kn in kl:
        p = ZKOL[kn]
        d = 100 if kn[0] == 'P' else 70
        pts = _alt_route(kn)
        pipe(pts, PS, 'T'); node(pts[-1], 'R')
        TEMIZLEME_KAPAGI((p[0], p[1] + 12), 0.9)
        gp.kolon_pis(p, kn, (45, -35), k=0.6 if d == 100 else 0.5)
        sb = kolon_sb(kn, 'Z')
        Ln = sum(math.hypot(b_[0] - a_[0], b_[1] - a_[1]) for a_, b_ in zip(pts[:-1], pts[1:]))
        seg = max(zip(pts[:-1], pts[1:]), key=lambda s_: abs(s_[1][1] - s_[0][1]))
        T((seg[0][0] - 8, (seg[0][1] + seg[1][1]) / 2), '%s: L=%d / Ø%d / %%2 (%d SB)' % (kn, Ln, max(d, 100), sb), 7, PSC, 'C', 90)
    names = ['R%d' % i for i in range(1, len(_GR) + 2)] + ['PB']
    cum = 0
    for a, b in zip(names[:-1], names[1:]):
        if a in R_KOL:
            cum += sum(kolon_sb(kn, 'Z') for kn in R_KOL[a])
        pa, pb_ = R_[a], R_[b]
        if b == 'PB':
            pts = [(pa[0], pa[1] + 25), (pb_[0], pb_[1] - 30)]
        else:
            pts = [(pa[0] + 25, pa[1]), (pb_[0] - 25, pb_[1])]
        pipe(pts, PS, 'T'); node(pts[0], 'R'); node(pts[-1], 'R')
        ln = math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) + 50
        if b == 'PB':
            T((pa[0] + 12, (pa[1] + pb_[1]) / 2), 'L=%d / Q=150 / %%1 (%d SB)' % (ln, cum), 7, PSC, 'C', 90)
        else:
            T(((pa[0] + pb_[0]) / 2, pa[1] - 14), 'L=%d / Q=150' % ln, 6, PSC, 'C')
            T(((pa[0] + pb_[0]) / 2, pa[1] - 23), '%%1 (%d SB)' % cum, 6, PSC, 'C')
    pb = R_['PB']
    pipe([(pb[0], pb[1] + 30), (pb[0], pb[1] + 130)], PS, 'T')
    node((pb[0], pb[1] + 30), 'PB'); node((pb[0], pb[1] + 130), 'SASKİ')
    ARROW((pb[0], pb[1] + 145), 90, PS, 14)
    T((pb[0] - 12, pb[1] + 60), 'MEVCUT KANALİZASYON ŞEBEKESİNE DEŞARJ (SASKİ)', 7.5, PSC, 'R')
    T((29340.0, -10980.0), 'BİNA PİS SULARI KOLON DİPLERİNDEN (TEMİZLEME KAPAKLI) ZEMİN DÖŞEMESİ ALTINDAN BİNA ÖNÜNDEKİ MUAYENE BACALARINA, '
      'BACALAR ARASI Ø150 SN8 KORUGE BORU İLE %1 EĞİMLE MEVCUT PARSEL BACASINA (PB) BAĞLANIR. (SASKİ ATIKSU PROJESİ: TOPLAM L=35,21 m)',
      8, PSC, 'L')
    pop()


# ================================================================== ÇATI PLANI
def cati():
    push(MOVE(dx('C'), 0.0))
    x0, y0, x1, y1 = DEPO
    T(((x0 + x1) / 2, y1 + 30), 'KULLANMA SUYU DEPOSU 15,00 m³ (MİMARİ ÇATI PLANINDAKİ YERİNDE - UMUMİ BİNA)', 8, YZ, 'C')
    T(((x0 + x1) / 2, (y0 + y1) / 2), 'V=15,00 m³', 12, 'RAST-TEM-SU DEPOSU', 'MC')
    db, ad = RZ['DBK'], RZ['ADK']
    pipe([db, (db[0], y1 - 30), (x1, y1 - 30)], CS, 'S')
    pipe([ad, (ad[0], y0 + 30), (x1, y0 + 30)], CS, 'S')
    node((x1, y1 - 30), 'DEPO'); node((x1, y0 + 30), 'DEPO')
    cad.SAMANDIRALI_VANA((x1 - 4, y1 - 30), 0.6)
    mtyblk.insert('MTY-KURESEL VANA', (x1 + 40, y0 + 30), 0, 0.4)
    gp.kolon_temiz(db); gp.kolon_temiz(ad); node(db, 'DBK'); node(ad, 'ADK')
    cap_temiz(((x1 + db[0]) / 2, y1 - 30), 0, so='DBK', socp='Ø%d' % dn_temiz(YB_TOP), k=5.0)
    cap_temiz(((x1 + ad[0]) / 2 + 30, y0 + 30), 0, so='ADK %s YB' % fmt(YB_TOP), socp='Ø%d' % dn_temiz(YB_TOP), k=5.0)
    # taşma + boşaltma -> YB1 (ön sol köşe iniş)
    yb = gp.yb_on_facade(FLAT, YB_PTS, SRC['2'], WIN)['YB1'] if False else YB_PTS['YB1']
    pipe([(x0, y1 - 10), (x0 - 20, y1 - 10), (x0 - 20, yb[1] - 30), (yb[0] + 8, yb[1] - 30), (yb[0] + 8, yb[1])], CS, 'X')
    pipe([(x0, y0 + 10), (x0 - 20, y0 + 10), (x0 - 20, y1 - 10)], CS, 'X')
    node((x0, y1 - 10), 'DEPO'); node((x0, y0 + 10), 'DEPO'); node((yb[0] + 8, yb[1]), 'YB1')
    mtyblk.insert('MTY-KURESEL VANA', (x0 - 20, y0 + 60), 90, 0.4)
    T((x0 - 28, y0 + 20), 'TAŞMA Ø50 + BOŞALTMA Ø40 → YB1 YAĞMUR SÜZGECİNE', 6.5, TSC, 'L', 90)
    for nm, p in sorted(ALLK.items()):
        cad.KOLON(p, 6, PS); C(p, 10, PS)
        T((p[0] + 12, p[1] + 8), '%s HAVALIK Ø%d (ÇATIDAN 50 cm YUKARI)' % (nm, 100 if nm[0] == 'P' else 70), 6, PSC, 'L')
    for nm, p in YB_PTS.items():
        C(p, 8, YL); C(p, 4, YL)
        up = p[1] > -11800
        mtyblk.insert('MTY-KOLON NO YAGMUR', (p[0] + (40 if p[0] < 30800 else -40), p[1] + (-45 if up else 45)), 0, 0.55, attrs={'K': nm})
        T((p[0] + (14 if p[0] < 30800 else -14), p[1] + (-14 if up else 10)), 'YAĞMUR SÜZGECİ + Ø100 İNİŞ', 6, YC,
          'L' if p[0] < 30800 else 'R')
    T((29400.0, -12390.0), 'TERAS ÇATI YAĞMUR SULARI KÖŞELERDEKİ 4 ADET YAĞMUR SÜZGECİNDEN Ø100 PVC İNİŞLERLE ZEMİN KOTUNA İNDİRİLİR '
      '(YAĞMUR SUYU ALTYAPISI BU PROJE KAPSAMINDA DEĞİLDİR).', 7.5, YC, 'L')
    pop()


# ================================================================== YAĞMUR İNİŞLERİ (kat planları)
def yagmur_kat(k):
    push(MOVE(dx(k), 0.0))
    for nm, p in gp_yb_facade(k).items():
        C(p, 6, YL); C(p, 3, YL)
        node(p, nm)
        up = p[1] > -11800
        mtyblk.insert('MTY-KOLON NO YAGMUR', (p[0] + (35 if p[0] < 30800 else -35), p[1] + (40 if up else -40)), 0, 0.55, attrs={'K': nm})
        T((p[0] + (55 if p[0] < 30800 else -55), p[1] + (36 if up else -44)), 'Ø100', 6.5, YC, 'L' if p[0] < 30800 else 'R')
    pop()


def gp_yb_facade(k):
    """iniş boruları cepheye yaslı: köşe noktasından dış cepheye 8 cm (havada değil)"""
    out = {}
    for nm, p in YB_PTS.items():
        fx = 29330.0 if p[0] < 30800 else 32402.0
        fy = -11400.0 if p[1] > -11800 else -12318.0
        out[nm] = (fx + (14 if p[0] < 30800 else -14), fy + (8 if p[1] > -11800 else -8))
    return out


# ================================================================== ISITMA: ofislerde kombili yerden ısıtma
import gheat as GH
import spiral3
GH.KAT_H = 3.50
GH.T_CATI = -6.0                 # teras çatı: tavan dış havaya
T_KOMSU = 15.0                   # bitişik nizam komşu bina (yangın duvarı)
T_HOL = GH.T_HOL
_W = lambda w, h=2.7: [(w, h, 1, 'ÇP')]
HROOMS = {
    'O1': [dict(name='ODA', ti=20, A=19.54, rect=(29352, -11891, 29741, -11451), door=(29685, -11891, 'S'),
                ext=[('K', 3.90, _W(3.50))], int=[('İDM', 4.40, T_KOMSU, None)]),
           dict(name='ODA ', ti=20, A=10.10, rect=(29346, -12281, 29598, -11928), door=(29600, -11979, 'E'),
                ext=[('G', 2.50, _W(2.20))], int=[('İDM', 3.50, T_KOMSU, None)]),
           dict(name='ODA  ', ti=20, A=10.96, rect=(29631, -12281, 30073, -12058), door=(30003, -12055, 'N'),
                ext=[('G', 4.40, _W(4.15))], int=[]),
           dict(name='MUTFAK', ti=20, A=3.83, rect=(30103, -12281, 30196, -12059), door=(30150, -12057, 'N'),
                ext=[('G', 0.90, _W(0.80, 1.40))], int=[]),
           dict(name='LVB.WC', ti=24, A=2.73, rect=(30276, -12282, 30395, -12090), door=(30324, -12087, 'N'),
                ext=[('G', 1.20, _W(0.50, 0.50))], int=[('İDA', 1.90, GH.T_ASANSOR, None)]),
           dict(name='HOL', ti=18, A=9.87, rect=(29600, -12052, 30400, -11926), door=None, ext=[],
                int=[('İDM', 1.30, T_HOL, (1.0, 2.2))])],
    'O2': [dict(name='ODA', ti=20, A=10.76, rect=(29778, -11739, 30096, -11451), door=(30045, -11741, 'S'),
                ext=[('K', 3.20, _W(2.80))], int=[]),
           dict(name='ODA ', ti=20, A=10.68, rect=(30115, -11739, 30428, -11451), door=(30390, -11741, 'S'),
                ext=[('K', 3.10, _W(2.70))], int=[]),
           dict(name='ODA  ', ti=20, A=13.32, rect=(30460, -11739, 30861, -11451), door=(30510, -11741, 'S'),
                ext=[('K', 4.00, _W(3.60))], int=[]),
           dict(name='MUTFAK', ti=20, A=3.65, rect=(30605, -11840, 30800, -11762), door=(30602, -11808, 'W'),
                ext=[], int=[('İDM', 2.60, T_HOL, None)]),
           dict(name='LVB.WC', ti=24, A=2.90, rect=(29772, -11880, 29958, -11762), door=(29964, -11809, 'E'),
                ext=[], int=[('İD', 6.60, 20.0, None)]),
           dict(name='HOL', ti=18, A=9.00, rect=(29969, -11889, 30600, -11748), door=None, ext=[],
                int=[('İDM', 1.30, T_HOL, (1.0, 2.2))])],
    'O3': [dict(name='ODA', ti=20, A=13.10, rect=(30893, -11739, 31280, -11451), door=(31240, -11741, 'S'),
                ext=[('K', 3.90, _W(3.50))], int=[]),
           dict(name='ODA ', ti=20, A=10.75, rect=(31310, -11739, 31636, -11451), door=(31362, -11741, 'S'),
                ext=[('K', 3.30, _W(2.90))], int=[]),
           dict(name='ODA  ', ti=20, A=10.77, rect=(31655, -11739, 31975, -11451), door=(31707, -11741, 'S'),
                ext=[('K', 3.20, _W(2.80))], int=[]),
           dict(name='MUTFAK', ti=20, A=3.97, rect=(30958, -11840, 31145, -11762), door=(31149, -11808, 'E'),
                ext=[], int=[('İDM', 2.60, T_HOL, None)]),
           dict(name='LVB.WC', ti=24, A=2.90, rect=(31793, -11880, 31979, -11762), door=(31788, -11809, 'W'),
                ext=[], int=[('İD', 6.60, 20.0, None)]),
           dict(name='HOL', ti=18, A=9.00, rect=(31150, -11889, 31783, -11748), door=None, ext=[],
                int=[('İDM', 1.30, T_HOL, (1.0, 2.2))])],
    'O4': [dict(name='ODA', ti=20, A=19.19, rect=(32010, -11891, 32391, -11451), door=(32065, -11891, 'S'),
                ext=[('K', 3.80, _W(3.40))], int=[('İDM', 4.40, T_KOMSU, None)]),
           dict(name='ODA ', ti=20, A=9.62, rect=(32131, -12281, 32383, -11928), door=(32131, -11979, 'W'),
                ext=[('G', 2.50, _W(2.45))], int=[('İDM', 3.50, T_KOMSU, None)]),
           dict(name='ODA  ', ti=20, A=11.24, rect=(31655, -12281, 32100, -12058), door=(31723, -12055, 'N'),
                ext=[('G', 4.45, _W(3.80))], int=[]),
           dict(name='MUTFAK', ti=20, A=3.83, rect=(31529, -12281, 31622, -12059), door=(31578, -12057, 'N'),
                ext=[('G', 0.90, _W(0.80, 1.40))], int=[]),
           dict(name='LVB.WC', ti=24, A=2.83, rect=(31330, -12282, 31453, -12090), door=(31390, -12087, 'N'),
                ext=[('G', 1.20, _W(0.50, 0.50))], int=[('İD', 4.00, 20.0, None)]),
           dict(name='HOL', ti=18, A=10.07, rect=(31310, -12052, 32100, -11926), door=None, ext=[],
                int=[('İDM', 1.30, T_HOL, (1.0, 2.2))])],
}
KOLL = {'O1': (30230.0, -11938.0, 'S'), 'O2': (30230.0, -11889.0, 'N'), 'O3': (31480.0, -11889.0, 'N'), 'O4': (31480.0, -11938.0, 'S')}
OF_ADI = {('1', 'O1'): 'OFİS 1', ('1', 'O2'): 'OFİS 2', ('1', 'O3'): 'OFİS 3', ('1', 'O4'): 'OFİS 4',
          ('2', 'O1'): 'OFİS 5', ('2', 'O2'): 'OFİS 6', ('2', 'O3'): 'OFİS 7', ('2', 'O4'): 'OFİS 8'}


def heat_calc(k):
    kind = 'ara' if k == '1' else 'ust'
    return {of: [GH.calc_room(R, kind) for R in rs] for of, rs in HROOMS.items()}


def _circuits(of, calc):
    circ = []
    for R, res in zip(HROOMS[of], calc):
        if R['door'] is None:
            continue
        q = res['Q'] / R['A']
        sp = 10.0 if q > 75 or R['ti'] >= 24 else 15.0
        dxd, dyd, wall = R['door']
        ps_ = [R['rect']]
        while True:
            big = max(ps_, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
            est = (big[2] - big[0] - 20) * (big[3] - big[1] - 20) / sp / 100.0 + 20.0
            if est <= 72.0:
                break
            ps_.remove(big)
            x0, y0, x1, y1 = big
            if wall in 'NS':
                xm = (x0 + x1) / 2; ps_ += [(x0, y0, xm, y1), (xm, y0, x1, y1)]
            else:
                ym = (y0 + y1) / 2; ps_ += [(x0, y0, x1, ym), (x0, ym, x1, y1)]
        ps_.sort(key=lambda r: math.hypot((r[0] + r[2]) / 2 - dxd, (r[1] + r[3]) / 2 - dyd))
        for j, p_ in enumerate(ps_):
            circ.append(dict(room=R['name'].strip(), rkey=R['name'], rect=p_, Ar=(p_[2] - p_[0]) * (p_[3] - p_[1]) / 1e4, ti=R['ti'],
                             Qroom=res['Q'], Aroom=R['A'], s=sp, door=R['door'], npart=len(ps_), ipart=j))
    for c in circ:
        same = [x for x in circ if x['rkey'] == c['rkey']]
        c['W'] = c['Qroom'] * c['Ar'] / sum(x['Ar'] for x in same)
    return circ


def _spiral(c):
    """boru bölgesi (duvardan 10 cm), giriş köşesi kapıya en yakın köşe; çok parçalı mahalde parçalar arası 6 cm"""
    x0, y0, x1, y1 = c['rect']
    r = [x0 + 10, y0 + 10, x1 - 10, y1 - 10]
    if c['npart'] > 1:      # parça sınırında 3 cm daha içeri (bağlantı ayakları için)
        R = [x for x in HROOMS_ALL[c['rkey']]['rect']]
        if abs(x0 - R[0]) > 1: r[0] += 4
        if abs(x1 - R[2]) > 1: r[2] -= 4
        if abs(y0 - R[1]) > 1: r[1] += 4
        if abs(y1 - R[3]) > 1: r[3] -= 4
    dxd, dyd, wall = c['door']
    cs = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
    ci = min(range(4), key=lambda j: math.hypot(cs[j][0] - dxd, cs[j][1] - dyd))
    full = spiral3.bifilar(cs, ci, 'a', c['s'])[0]
    return full


HROOMS_ALL = {}
_HCACHE = {}


_HPK = '/tmp/claude-0/p3/et_heat_cache.pkl'


def heat_routes(of):
    if of not in _HCACHE:
        try:
            _HCACHE.update(pickle.load(open(_HPK, 'rb')))
        except Exception:
            pass
    if of in _HCACHE:
        for R in HROOMS[of]:
            HROOMS_ALL[R['name']] = R
        return _HCACHE[of]
    r = _heat_routes(of)
    try:
        pickle.dump(_HCACHE, open(_HPK, 'wb'))
    except Exception:
        pass
    return r


def _heat_routes(of):
    """kollektör -> devre ayakları (A*, kapılardan geçer, odaları/diğer serpantinleri kesmez) + kombi -> kollektör"""
    if of in _HCACHE:
        return _HCACHE[of]
    for R in HROOMS[of]:
        HROOMS_ALL[R['name']] = R
    calc = heat_calc('1')[of]
    circ = _circuits(of, calc)
    kx, ky, kd = KOLL[of]
    n = len(circ)
    ports = [((kx + 8 + i * 10, ky + (0 if kd == 'S' else 10)), (kx + 12 + i * 10, ky + (0 if kd == 'S' else 10))) for i in range(n)]
    F, defs, xm, km, E, win = OFIS[of]
    xs = [r['rect'][0] for r in HROOMS[of]] + [r['rect'][2] for r in HROOMS[of]]
    ys = [r['rect'][1] for r in HROOMS[of]] + [r['rect'][3] for r in HROOMS[of]]
    hw = (min(xs) - 15, min(ys) - 15, max(xs) + 15, max(ys) + 15)
    g = RT.Grid(hw, 2.0, walls=wall_lines('1', hw, lays={'rtm-duv tugla', 'rtm-tas_betonarme', 'rtm-sıva', 'SIVA'}),
                obstacles=[c_ for c_ in cols('1') if c_.intersects(box(*hw))], far_pen=0.6)
    # ayaklar YALNIZ bu ofisin mahal alanlarında (hol + kendi odası) ve kapı boşluklarında gider:
    # duvar içinden, ortak alandan (merdiven holü) veya başka bağımsız bölümden geçmez
    allowed = None
    for R in HROOMS[of]:
        m_ = g.rect_mask((R['rect'][0] - 2, R['rect'][1] - 2, R['rect'][2] + 2, R['rect'][3] + 2))
        allowed = m_ if allowed is None else (allowed | m_)
    for d_ in doors('1'):
        if d_.intersects(box(*hw)):
            allowed |= g.rect_mask(d_.bounds)
    g.block |= ~allowed
    for c in circ:
        c['full'] = _spiral(c)
        g.add_line(c['full'], 'SP' + c['rkey'] + str(c['ipart']))
    # her devre ayağı yalnız kendi mahalline girer (başka odanın içinden geçmez, holden + kapıdan)
    # kollektör dolabı ve arkası (duvar) ayaklara kapalı
    kb = (kx - 6, ky - 20, kx + 18 + n * 10, ky + 8) if kd == 'N' else (kx - 6, ky + 2, kx + 18 + n * 10, ky + 30)
    g.add_block(box(*kb), pad=0.0)
    rmask = {R['name']: g.rect_mask((R['rect'][0] - 3, R['rect'][1] - 3, R['rect'][2] + 3, R['rect'][3] + 3))
             for R in HROOMS[of] if R['door'] is not None}
    # ağız ataması: kapı x sırasına göre (kesişme az)
    order = sorted(range(n), key=lambda i: (circ[i]['door'][0], circ[i]['ipart']))
    for p_i, ci in enumerate(order):
        circ[ci]['pidx'] = p_i
    # kombi -> kollektör gidiş / dönüş (önce: ayaklar bunlara paralel gider)
    km = F['KM']
    hg = g.route(km.cp('HG'), (kx + 2, ky + (0 if kd == 'S' else 10)), 'HG', turn=6.0, free_end=4.0)
    g.add_line(hg, 'HG')
    hd = g.route(km.cp('HD'), (kx + 10 + 10 * n, ky + (0 if kd == 'S' else 10)), 'HD', turn=6.0, free_end=4.0)
    g.add_line(hd, 'HD')
    # ağız ağzından 10 cm dik çıkış (düzenli kollektör bağlantısı), sonra A*; birkaç sıralama denenir, en az kesişen seçilir
    sgn = -1.0 if kd == 'S' else 1.0
    stub = lambda p: (p[0], p[1] + sgn * 12.0)
    import copy as _cp
    base_occ = {k_: v.copy() for k_, v in g.occ.items()}
    base_lines = {k_: list(v) for k_, v in g.lines.items()}
    dist = lambda c: math.hypot(c['full'][0][0] - kx, c['full'][0][1] - ky)
    orders = [sorted(circ, key=lambda c: -dist(c)), sorted(circ, key=dist),
              sorted(circ, key=lambda c: c['pidx']), sorted(circ, key=lambda c: -c['pidx'])]
    best = None
    for seq in orders:
        g.occ = {k_: v.copy() for k_, v in base_occ.items()}
        g.lines = {k_: list(v) for k_, v in base_lines.items()}
        res = {}
        for c in seq:
            sid = 'L' + c['rkey'] + str(c['ipart'])
            mk = None
            for nm_, m_ in rmask.items():
                if nm_ != c['rkey']:
                    mk = m_.copy() if mk is None else (mk | m_)
            pa, pb = ports[c['pidx']]
            a_ = g.route(stub(pa), c['full'][0], sid + 'a', turn=6.0, free_end=2.0, near_r=4.0, mask=mk)
            a_ = [pa] + a_ if abs(a_[0][0] - pa[0]) < 0.01 else [pa, (pa[0], a_[0][1])] + a_
            g.add_line(a_, sid + 'a')
            b_ = g.route(stub(pb), c['full'][-1], sid + 'b', turn=6.0, free_end=2.0, near_r=4.0, mask=mk)
            b_ = [pb] + b_
            g.add_line(b_, sid + 'b')
            res[id(c)] = (RT._collinear(a_), RT._collinear(b_))
        import gufh as _gu
        allp = [p_ for v in res.values() for p_ in v] + [hg, hd]
        nx_ = _gu.count_x(allp)
        if best is None or nx_ < best[0]:
            best = (nx_, res)
    print('ısıtma', of, 'kesişme puanı', best[0])
    for c in circ:
        a_, b_ = best[1][id(c)]
        c['legs'] = (a_, b_)
        c['path'] = a_[:-1] + c['full'] + list(reversed(b_))[1:]
        c['L'] = LineString(c['path']).length / 100.0
        c['port'] = c['pidx'] + 1
    _HCACHE[of] = (circ, ports, hg, hd)
    return _HCACHE[of]


def heat_floor(k):
    calc = heat_calc(k)
    push(MOVE(dx(k), HDY))
    out = {}
    for oi, of in enumerate(OFIS):
        circ0, ports, hg, hd = heat_routes(of)
        circ = []
        for c0, res in zip(circ0, [None] * len(circ0)):
            c = dict(c0)
            rr = [x for x in calc[of] if x['name'] == c['rkey']][0]
            same = [x for x in circ0 if x['rkey'] == c['rkey']]
            c['Qroom'] = rr['Q']
            c['W'] = rr['Q'] * c['Ar'] / sum(x['Ar'] for x in same)
            circ.append(c)
        kx, ky, kd = KOLL[of]
        n = len(circ)
        RECT(kx, ky, kx + 12 + n * 10, ky + 10, 'MTY-KOLLETOR')
        for a_, b_ in ports:
            C(a_, 1.2, 'MTY-KOLLETOR'); C(b_, 1.2, 'MTY-KOLLETOR')
        T((kx + 14 + n * 10, ky + 2), 'KOLLEKTÖR %d AĞIZLI' % n, 5.0, 'MTY-KOLLETOR', 'L')
        for c in circ:
            pipe(c['path'], gp.PEX, 'H')
            node(c['path'][0], 'KOLL'); node(c['path'][-1], 'KOLL')
        # zon numaraları
        zb = (100 if k == '1' else 200) + 10 * oi
        zones = {}
        for c in circ:
            if c['rkey'] not in zones:
                zones[c['rkey']] = zb + len(zones) + 1
            c['zone'] = '%03d' % zones[c['rkey']]
        taken = []
        for R in HROOMS[of]:
            cs_ = [c for c in circ if c['rkey'] == R['name']]
            rc = R['rect']
            rq = [x for x in calc[of] if x['name'] == R['name']][0]
            if cs_:
                gp.mahal_etiket(R['name'].strip(), cs_[0]['zone'], R['ti'], rq['Q'], R['A'], rc, taken, k=0.5,
                                prefer=(rc[0] + 40, rc[3] - 35))
            else:
                gp.mahal_etiket('HOL', '%03d' % (zb + 9), R['ti'], rq['Q'], R['A'], rc, taken, k=0.5, extra='(BAĞL. BORULARI)')
        for c in circ:
            r_ = c['rect']
            gp.devre_etiket(c, r_, taken, k=4.0 if min(r_[2] - r_[0], r_[3] - r_[1]) < 160 else 5.0)
        F = OFIS[of][0]
        F['KM'].draw()
        pipe(hg, gp.HGL, 'HG'); pipe(hd, gp.HDL, 'HD')
        for p_ in (hg[0], hg[-1], hd[0], hd[-1]):
            node(p_, 'KOMBI-KOLL')
        Qd = sum(c['W'] for c in circ)
        mid = hg[len(hg) // 2]
        T((mid[0] + 4, mid[1] + 4), '%d W - DN20' % round(Qd), 5.5, gp.HCAP, 'L')
        out[of] = (circ, calc[of])
    pop()
    return out


# ================================================================== ZEMİN KAT DÜKKÂN KLİMA (duvar tipi split, hesap raporlu)
import gklima as GK
YBF = gp_yb_facade('Z')
DUKKAN = [
    dict(name='DÜKKÂN-1', A=100.38, ti=20, H=4.50,
         ext=[('K', 12.90, [(12.00, 3.00, 1, 'ÇP')]), ('G', 13.40, [])],
         int=[('İDM', 9.00, T_KOMSU, None), ('İDM', 5.00, T_HOL, None)],
         # (iç ünite duvar yüzü, rot, dış ünite (arka cephe dış yüzü), drenaj hedefi = köşe yağmur inişi)
         units=[((29349.0, -11700.0), -90, (29520.0, -12322.0), YBF['YB4']),
                ((29341.0, -12150.0), -90, (29720.0, -12322.0), YBF['YB4'])],
         lab=(29600.0, -11800.0)),
    dict(name='DÜKKÂN-2', A=105.71, ti=20, H=4.50,
         ext=[('K', 15.00, [(14.00, 3.00, 1, 'ÇP')]), ('G', 10.50, [])],
         int=[('İDM', 9.00, T_KOMSU, None), ('İDM', 5.00, T_HOL, None)],
         units=[((32392.0, -11700.0), 90, (32220.0, -12322.0), YBF['YB3']),
                ((32385.0, -12150.0), 90, (32020.0, -12322.0), YBF['YB3'])],
         lab=(31560.0, -11800.0)),
]


def klima_calc():
    out = []
    kh = GH.KAT_H
    GH.KAT_H = 4.70
    for S in DUKKAN:
        k = GK.kazanc(S)
        h = GH.calc_room(S, 'zemin')
        adet, btu, kw = GK.sec(k['Q'], h['Q'])
        out.append(dict(S=S, kaz=k, kay=h, adet=adet, btu=btu, kw=kw))
    GH.KAT_H = kh
    return out


def klima_zemin():
    res = klima_calc()
    push(MOVE(dx('Z'), HDY))
    for r in res:
        S = r['S']
        uu = S['units'][:r['adet']]
        sg = 1 if uu[0][1] == -90 else -1                  # batı duvarı: oda +x yönünde
        cus = [GK.ic_unite(io, irot, r['btu']) for io, irot, oo, dtar in uu]
        W = min(u[0][0] for u in uu) if sg > 0 else max(u[0][0] for u in uu)   # duvar yüzü
        for i, (io, irot, oo, dtar) in enumerate(uu):
            cu, dr = cus[i]
            dc = GK.dis_unite(oo, 180)
            # hatlar DUVAR İÇİNDE (ünitelerin arkasında), her ünite ayrı şeritte; yatay seviyeler arka duvar içinde ayrı
            xd = W - sg * (3 + 12 * i); xb = xd - sg * 6
            yd_ = -12296.0 - 12 * i; yb_ = yd_ - 6
            path = [cu, (xb, cu[1]), (xb, yb_), (dc[0], yb_), dc]
            pipe(path, GK.LBAK, 'K'); node(path[0], 'KLIMA'); node(path[-1], 'KLIMA')
            if i == 0:
                dp = [dr, (xd, dr[1]), (xd, yd_), (dtar[0], yd_), dtar]
            else:                                         # sonraki ünite drenajı birinci drenajın yağmur inişine inen düşeyine bağlanır
                dp = [dr, (xd, dr[1]), (xd, yd_), (dtar[0], yd_)]
            pipe(dp, GK.LDRN, 'KD'); node(dp[0], 'KLIMA'); node(dp[-1], 'KLIMA')
            west = irot == -90
            tx, ty = io
            off = 60 if west else -60
            al = 'L' if west else 'R'
            nm = 'K%d%s' % (1 if S['name'].endswith('1') else 2, 'AB'[i])
            T((tx + off, ty + 30), nm, 9.0, GK.LIC, al)
            T((tx + off, ty + 18), 'DUVAR TİPİ SPLİT KLİMA %d BTU/h' % r['btu'], 7.0, GK.LIC, al)
            T((tx + off, ty + 8), 'Qs=%.2f kW  Qı=%.2f kW' % (r['kw'], r['kw'] * 1.1), 6.5, GK.LIC, al)
            T((tx + off, ty - 2), 'BAKIR 1/4"-1/2" İZOLELİ (DUVAR İÇİNDEN ARKA CEPHEYE)', 6.0, GK.LBAK, al)
            T((dc[0], oo[1] - 48), nm + ' DIŞ ÜNİTE (ARKA CEPHE KONSOLU)', 6.0, GK.LDIS, 'C')
        T((dtar[0] + (14 if dtar[0] < 30800 else -14), yb_ + 20), 'DRENAJ Ø20 PVC → YAĞMUR İNİŞİNE', 6.0, GK.LDRN,
          'L' if dtar[0] < 30800 else 'R')
        lx, ly = S['lab']
        T((lx, ly), '%s  -  ISI KAZANCI %.0f W / ISI KAYBI %.0f W' % (S['name'], r['kaz']['Q'], r['kay']['Q']), 9.0, GK.LIC, 'L')
        T((lx, ly - 14), '%d ADET DUVAR TİPİ İNVERTER SPLİT KLİMA (%d BTU/h) SEÇİLMİŞTİR' % (r['adet'], r['btu']), 7.5, GK.LIC, 'L')
    for nm, p in YBF.items():
        C(p, 6, YL); C(p, 3, YL)
    pop()
    return res


# ================================================================== PAFTALAR
import gsheet as GS
import gheatsheet as HS
SX0 = 5 * SLOT                 # şemalar (çatı paftasının sağı)
OY = FY0 + 20.0
YBS_ = {'O%d' % i: YB_OF for i in range(1, 9)}
P = dict(
    floors=[('Z', 'ZEMİN KAT ±0,00'), ('1', '1. KAT +4,70'), ('2', '2. KAT +8,20')], roof_name='TERAS ÇATI +11,70',
    sema_w=5650.0,
    supply=dict(depo='cati', V=DEPO_V, vnote='UMUMİ BİNA - MİMARİ PROJEDE 15 m³', ybt=YB_TOP, tasma='YB1 YAĞMUR SÜZGECİNE (TAŞMA Ø50)',
                units=[('DK1', 'Z', 1, YB_DK), ('DK2', 'Z', 4, YB_DK), ('O1', '1', 1, YB_OF), ('O2', '1', 2, YB_OF), ('O3', '1', 3, YB_OF),
                       ('O4', '1', 4, YB_OF), ('O5', '2', 1, YB_OF), ('O6', '2', 2, YB_OF), ('O7', '2', 3, YB_OF), ('O8', '2', 4, YB_OF)]),
    groups=[],
    yagmur=dict(names=list(YB_PTS), P=ROOF_A, dn=100, foot={k: 0 for k in YB_PTS}, tasma_to='YB1'),
)
_FI = {0: 'Z', 1: '1', 2: '2'}
for gi, (pkn, mkn, dk, o1, o2) in enumerate([('PK1', 'MK1', 'DK1', 'O1', 'O5'), ('PK2', 'MK2', None, 'O2', 'O6'),
                                              ('PK3', 'MK3', None, 'O3', 'O7'), ('PK4', 'MK4', 'DK2', 'O4', 'O8')]):
    x = 560 + gi * 1270
    units = {'1': (o1, 'daire'), '2': (o2, 'daire')}
    if dk:
        units['Z'] = (dk, 'isyeri')
    P['groups'].append(dict(x=x, pkx=x + 120, mkx=x + 720, kombi=x + 1080, bkeys=['LV', 'WC', 'YS'], mkeys=['EV', 'BM'],
                            ikeys=['LV', 'WC', 'YS'], units=units,
                            kolons=[(pkn, x + 120, 100, (lambda i, n=pkn: kolon_sb(n, _FI[i]))),
                                    (mkn, x + 720, 70, (lambda i, n=mkn: kolon_sb(n, _FI[i])))]))

NOTES = [
    'Temiz su tesisatı PPRC PN20 borularla yapılacak, sıcak su boruları izolasyonlu olarak döşenecektir.',
    'Şebeke suyu bina ön girişindeki ana sayaç nişinden DBK kolonu ile teras çatıdaki 15,00 m³ kullanma suyu deposuna verilecektir.',
    'Depodan inen ADK kolonu zemin kat merdiven holündeki sayaç grubuna bağlanacak; her bağımsız bölüm ayrı sayaçtan beslenecektir.',
    'Temiz su kolonları ve sayaçtan kolonlara giden hatlar yalnız ortak alanlarda (merdiven holü) kolon kutusu / asma tavan içinden geçirilecektir.',
    'Sayaçlardan önce DN x 10, sonra DN x 5 düz boru bırakılacak; her bağımsız bölüm girişinde küresel vana ve çek valf konulacaktır.',
    'Depo şamandıralı vana, sinekli havalık, taşma, boşaltma ve seviye göstergeli olacak; taşma ve boşaltma YB1 yağmur süzgecine bağlanacaktır.',
    'Sıcak kullanma suyu her ofiste duvar tipi hermetik yoğuşmalı kombiden, dükkânlarda lavabo altı elektrikli su ısıtıcıdan sağlanacaktır.',
    'Kombiler dış cepheye bitişik mahallere asılacak, bacaları doğrudan dış atmosfere verilecektir.',
    'Pis su tesisatı TS EN 1451 PVC borularla yapılacak; bina içi yatay hatlar en az %2, bacalar arası hatlar %1 eğimle döşenecektir.',
    'Mutfak ve WC giderleri birbirine bağlanmayacak; her mahal en yakın kendi kolonuna (PK WC, MK mutfak) bağlanacaktır.',
    'Zemin katta dükkân / koridor ortasına düşen kolonlar asma tavanda en yakın duvara kaydırılıp kolon kutusu içinde zemin kotuna indirilecektir.',
    'Pis su kolonları zemin kotunda temizleme kapağı üzerinden döşeme altından bina önündeki muayene bacalarına bağlanacaktır.',
    'Bacalar arası Ø150 SN8 koruge borular %1 eğimle SASKİ onaylı atıksu projesine göre mevcut parsel bacasına (PB) bağlanacaktır.',
    'Pis su kolonları çatıdan en az 50 cm yukarı çıkarılacak, uçlarına havalık şapkası takılacaktır.',
    'Parsel bacası kotu ve bağlantı yeri SASKİ\'den alınacak; plandaki kotlar yaklaşık olup sahada teyit edilecektir.',
    'Hiçbir boru betonarme kolon içinden geçirilmeyecek; döşeme geçişleri kiriş bantları dışında kılıflı yapılacaktır.',
    'Yağmur suları pis su hattına bağlanmayacak; 4 adet Ø100 PVC iniş borusu cepheye kelepçeyle tespit edilecek ve zemin kotunda bırakılacaktır (yağmur suyu altyapısı bu proje kapsamında değildir).',
    'Ofislerde yerden ısıtma devreleri PEX 16x2,0 oksijen bariyerli borularla karşı akışlı salyangoz düzende, devre boyunca eksiz döşenecektir.',
    'Yerden ısıtma devre boyları (bağlantı boruları dahil) 80 m\'yi geçmeyecek; mutfak dolapları altına ve ortak alanlara (merdiven holü, asansör) boru döşenmeyecektir.',
    'Dükkânlar duvar tipi inverter split klima ile ısıtılıp soğutulacak; dış üniteler arka cephe konsolu üzerine, drenajlar köşe yağmur inişlerine bağlanacaktır.',
    'Temiz su hatlarına 10 bar, yerden ısıtma devrelerine şap öncesi 6 bar basınç testi yapılacaktır.',
    'Tüm imalat TS 1258, TS EN 806, TS EN 12056, TS EN 1264 ve TS 825 standartlarına uygun olarak yapılacaktır.',
]
ANTET = dict(proje="EMİNE TUNCE'YE AİT İŞ YERİ PROJESİ", konu='SIHHİ TESİSAT, YERDEN ISITMA VE KLİMA PROJESİ',
             rows=[('YAPININ ÖZELLİKLERİ', ''), ('YAPI SAHİBİ', 'EMİNE TUNCE'), ('YAPI CİNSİ / SINIFI', 'BETONARME İŞ YERİ / 3A'),
                   ('KAT ADEDİ', 'ZEMİN + 2 KAT (+ TERAS ÇATI)'), ('BAĞIMSIZ BÖLÜM', '2 DÜKKÂN + 8 OFİS = 10'),
                   ('ISITMA', '8 x 24 kW YOĞUŞMALI KOMBİ + YERDEN ISITMA / DÜKKÂN SPLİT KLİMA'),
                   ('SU TEMİNİ', 'ŞEBEKE (SASKİ) + 15,00 m³ TERAS DEPOSU'), ('KOTLAR', '±0,00 = +27,55 (YOL +27,35)'),
                   ('ARSANIN ÖZELLİKLERİ', ''), ('İLİ / İLÇESİ', 'SAKARYA / SERDİVAN'), ('MAHALLE', 'YAZLIK'),
                   ('PAFTA / ADA / PARSEL', 'G24B23A3B / - / 5799'), ('TOPLAM İNŞAAT ALANI', '824,10 m²')],
             tarih='12.10.2026')


def temel_sema(ytk):
    xs = lambda d: SX0 + d
    names = list(R_)
    for j, nm in enumerate(names):
        x = 700 + j * 520
        if nm != 'PB':
            mtyblk.insert('PVC ROGAR', (xs(x), ytk), 0, 1.0)
            T((xs(x) - 20, ytk - 40), nm, 10, 'MTY-ROGAR', 'L')
        else:
            mtyblk.insert('PVC ROGAR', (xs(x), ytk), 0, 1.2)
            T((xs(x) + 40, ytk - 4), 'PB → MEVCUT KANALİZASYON (SASKİ) %1', 9, 'MTY-ROGAR', 'L')
        if j < len(names) - 1:
            GS.dline((xs(x + 40), ytk), (xs(x + 480), ytk), 6)
    cum = 0
    for j, nm in enumerate(names[:-1]):
        cum += sum(kolon_sb(kn, 'Z') for kn in R_KOL.get(nm, []))
        cap_pis((xs(700 + j * 520 + 260), ytk + 8), 0, '%d SB' % cum, 'Ø150', 7)


HFLOORS = [('1', '1. KAT', 'OFİS 1', 'OFİS 2', 'OFİS 3', 'OFİS 4'), ('2', '2. KAT', 'OFİS 5', 'OFİS 6', 'OFİS 7', 'OFİS 8')]


def klima_sema(ox, y, KL):
    """kolon şemasında zemin kat bandı: dükkân split klimaları (iç ünite - bakır - dış ünite, drenaj)"""
    L((ox + 60, y), (ox + 5400, y), 'MTY-SEMA')
    T((ox + 5420, y + 20), 'ZEMİN KAT', 15, 'MTY-KAT-ADI', 'L', 90)
    x = ox + 200
    for r in KL:
        S = r['S']
        T((x, y + 330), '%s - %d x %d BTU/h DUVAR TİPİ SPLİT KLİMA' % (S['name'], r['adet'], r['btu']), 10, GK.LIC, 'L')
        for i in range(r['adet']):
            ix = x + i * 600
            RRECT(ix, y + 220, ix + 180, y + 270, 6, GK.LIC)
            T((ix + 90, y + 245), 'K%d%s İÇ ÜNİTE' % (1 if S['name'].endswith('1') else 2, 'AB'[i]), 8, GK.LIC, 'MC')
            T((ix + 90, y + 282), '%d BTU/h - Qs %.2f kW / Qı %.2f kW' % (r['btu'], r['kw'], r['kw'] * 1.1), 6.5, GK.LIC, 'C')
            RECT(ix + 300, y + 60, ix + 470, y + 140, GK.LDIS)
            C((ix + 350, y + 100), 28, GK.LDIS); C((ix + 350, y + 100), 4, GK.LDIS)
            T((ix + 385, y + 150), 'DIŞ ÜNİTE (ARKA CEPHE)', 6.5, GK.LDIS, 'C')
            PL([(ix + 180, y + 255), (ix + 240, y + 255), (ix + 240, y + 120), (ix + 300, y + 120)], GK.LBAK, w=1.5)
            PL([(ix + 180, y + 235), (ix + 230, y + 235), (ix + 230, y + 110), (ix + 300, y + 110)], GK.LBAK, w=1.5)
            T((ix + 246, y + 190), 'BAKIR 1/4" SIVI', 6, GK.LBAK, 'L', 90); T((ix + 222, y + 190), 'BAKIR 1/2" GAZ', 6, GK.LBAK, 'R', 90)
            PL([(ix + 20, y + 220), (ix + 20, y + 30), (ix + 160, y + 30)], GK.LDRN, w=1.2)
            T((ix + 26, y + 40), 'DRENAJ Ø20 → YAĞMUR İNİŞİ', 6, GK.LDRN, 'L')
        x += 600 * r['adet'] + 300


def build_sheets(HEAT, KL):
    yf, ytk = GS.sihhi_sema(SX0, OY, P)
    temel_sema(ytk)
    h, yw = GS.yagmur_sema(SX0 + P['sema_w'] + 50, OY, P)
    ax = -3900.0
    GS.antet(ax, FY1 - 10, ANTET)
    GS.notlar(ax + 1800, FY1 - 10, NOTES)
    GS.lejant(ax, FY1 - 1010)
    FR = []
    for k in ('T', 'Z', '1', '2', 'C'):
        x0 = SLOTS[k] * SLOT
        FR.append(((x0, FY0, x0 + SLOT, FY1), NAMES[k], '1/50'))
    FR.append(((SX0, OY - 20, SX0 + P['sema_w'] + 30, FY1), 'SIHHİ TESİSAT KOLON ŞEMASI', 'ÖLÇEKSİZ'))
    FR.append(((SX0 + P['sema_w'] + 30, OY - 20, SX0 + P['sema_w'] + 80 + yw + 60, FY1), 'YAĞMUR SUYU ŞEMASI VE HESABI', 'ÖLÇEKSİZ'))
    FR.append(((ax - 50, FY0 - 250, -40.0, FY1 + 40), 'ANTET, NOTLAR VE LEJANT', 'ÖLÇEKSİZ'))
    HNAMES = {'Z': 'ZEMİN KAT DÜKKÂN KLİMA PLANI', '1': '1. KAT OFİSLER YERDEN ISITMA PLANI', '2': '2. KAT OFİSLER YERDEN ISITMA PLANI'}
    for k in ('Z', '1', '2'):
        x0 = SLOTS[k] * SLOT
        FR.append(((x0, FY0 + HDY, x0 + SLOT, FY1 + HDY), HNAMES[k], '1/50'))
    hy = FY0 + HDY + 20
    klima_sema(SX0, hy + 60, KL)
    HS.isitma_sema(SX0, hy + 540, HEAT, HFLOORS, W=5400.0, step=105)
    FR.append(((SX0, FY0 + HDY, SX0 + 5520, FY1 + HDY + 200), 'YERDEN ISITMA VE KLİMA KOLON ŞEMASI', 'ÖLÇEKSİZ'))
    tx = SX0 + 5570
    yy = HS.isitma_tablo(tx, FY1 + HDY + 160, HEAT, HFLOORS)
    tx2 = tx + 900
    yy2 = HS.klima_tablo(tx2, FY1 + HDY + 160, KL, 'ZEMİN KAT DÜKKÂNLAR - DUVAR TİPİ SPLİT KLİMA ISI KAZANCI VE SEÇİMİ')
    HS.u_tablo(tx2, yy2 - 10)
    FR.append(((tx - 30, min(yy, FY0 + HDY) - 40, tx2 + 640, FY1 + HDY + 200), 'ISITMA VE KLİMA HESAP ÇİZELGELERİ', 'ÖLÇEKSİZ'))
    for (a, b, c, d), t, o in FR:
        GS.frame(a, b, c, d, t, o)
    return FR, h


def build_all():
    for k, sub in (('Z', 'ZEMİN KAT DÜKKÂN KLİMA PLANI'), ('1', '1. KAT OFİSLER YERDEN ISITMA PLANI'),
                   ('2', '2. KAT OFİSLER YERDEN ISITMA PLANI')):
        floor_arch(k, HDY, heat=True)          # tefriş ve mahal yazıları korunur
        frame_title(k, HDY, sub)
    for k in ('Z', '1', '2', 'C'):
        floor_arch(k)
        frame_title(k, 0.0)
    frame_title('T', 0.0)
    zemin(); normal_kat('1'); normal_kat('2'); temel(); cati()
    for k in ('Z', '1', '2'):
        yagmur_kat(k)
    HEAT = {k: heat_floor(k) for k in ('1', '2')}
    KL = klima_zemin()
    FR, YH = build_sheets(HEAT, KL)
    return HEAT, KL, FR, YH


if __name__ == '__main__':
    HEAT, KL, FR, YH = build_all()
    for r in KL:
        print(r['S']['name'], round(r['kaz']['Q']), round(r['kay']['Q']), r['adet'], r['btu'])
    for k, v in HEAT.items():
        for of, (circ, calc) in v.items():
            print(k, of, [(c['room'], c['port'], round(c['W']), round(c['L'], 1), c['s']) for c in circ])
    print('yağmur', YH)
    from shapely import affinity
    cl = []
    for k in ('T', 'Z', '1', '2'):
        for c in cols('Z' if k == 'T' else k):
            cl.append(affinity.translate(c, dx(k), 0))
    rep = gp.check(cl)
    print('KONTROL', len(rep))
    for r in rep[:60]:
        print('  ', r)
    import xcheck
    xr = xcheck.crossings()
    print('köprü', xcheck.hops(xr), 'çakışık', [r for r in xcheck.summary(xr) if r[0] == 'ÇAKIŞIK'][:20])
    print('yazı maskesi', xcheck.wipe_texts())
    print('üst üste binen çizgi temizlendi', xcheck.dedupe())
    pickle.dump((cad.R, FR, cad.BLK), open('/tmp/claude-0/p3/et_R.pkl', 'wb'))
    pickle.dump(dict(HEAT=HEAT, KLIMA=KL, HROOMS=HROOMS, ROOF_A=ROOF_A, NYB=len(YB_PTS)), open('/tmp/claude-0/p3/et_calc.pkl', 'wb'))
