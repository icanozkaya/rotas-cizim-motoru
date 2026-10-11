"""Genel proje motoru (ROTAŞ / MTY standardı): mimari kopyalama, armatür, boru ağı, etiket, kalem kalınlıkları."""
import math, pickle, re, sys
sys.path.insert(0, '/home/claude/nb')
from shapely.geometry import Polygon, LineString, Point, box
import cad
from cad import L, PL, C, T, RECT, ARC, ARROW, SOL, push, pop, MOVE
import mtyblk

# ------------------------------------------------------------------ katmanlar
CS, CH, PS, PST = 'MTY-SOGUKSU-BORU', 'MTY-SICAKSU-BORU', 'MTY-PIS-SU-BORUSU', 'MTY-PISSU-BORU-TAVANDAN'
TF, VN, CD, YZ = 'MTY-TEFRIS', 'MTY-VANA', 'MTY-CIHAZ', 'MTY-YAZI'
TSC, PSC, YBL = 'MTY-TEMIZSU-CAP', 'MTY-PISSU-CAP', 'MTY-YUK-BIRIMI'
PEX, HGL, HDL, HCAP = 'MTY-PEX-BORU', 'MTY-ISITMA-GIDIS-BORU', 'MTY-ISITMA-DONUS-BORU', 'STM-ISITMA-CAP'
YL, YC = 'MTY-YAGMUR-BORUSU', 'MTY-YAGMUR-BORUSU-CAP'
ARC_L, ARC_K, ARC_T, ARC_F = 'MIMARI', 'MIMARI-KOLON', 'MIMARI-YAZI', 'MIMARI-TEFRIS'
HID = 'MTY-HIDROFOR'
EXTRA_LAYERS = {ARC_K: (8, 'CONTINUOUS'), ARC_T: (8, 'CONTINUOUS'), ARC_F: (9, 'CONTINUOUS'), HID: (4, 'CONTINUOUS'),
                'MTY-KAT-ADI': (1, 'CONTINUOUS'), 'MTY-SEMA': (8, 'CONTINUOUS'), 'MTY-PAFTA': (7, 'CONTINUOUS'),
                'MTY-KLIMA': (4, 'CONTINUOUS'), PST: (6, 'PISSU HATTI')}

# kalem kalınlıkları (polyline sabit genişliği, cm; 1/50 baskıda 1 cm = 0,2 mm)
WIDTH = {PS: 3.0, PST: 2.5, CS: 2.0, CH: 2.0, YL: 3.0, HGL: 2.0, HDL: 2.0, PEX: 1.2, HID: 2.0}

NET, NODES = [], []


def pipe(pts, lay, sysn, w=None):
    PL(pts, lay, w=WIDTH.get(lay, 0) if w is None else w)
    NET.append(dict(sys=sysn, lay=lay, pts=[cad.P(p) for p in pts], ri=len(cad.R) - 1))


def node(p, name):
    NODES.append((cad.P(p), name))


def fmt(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return s if '.' in s else s + '.0'


# ------------------------------------------------------------------ çap seçimi
def dn_temiz(yb):
    for lim, d in ((2.25, 20), (7.84, 25), (19.36, 32), (46.24, 40), (108.4, 50), (256, 63)):
        if yb <= lim + 1e-9:
            return d
    return 75


def dn_sb(sb, wc=False):
    """ROTAŞ örnek şeması: WC'li hat en az Ø100; Ø50 ≤10 SB, Ø70 ≤30 SB, Ø100 ≤160 SB"""
    for lim, d in ((10, 50), (30, 70), (160, 100), (300, 125), (600, 150)):
        if sb <= lim + 1e-9:
            return max(d, 100 if wc else 50)
    return 200


SB = dict(WC=10.0, DUS=7.0, LV=2.0, CM=4.0, YS=2.0, EV=4.0, BM=4.0)
YB = dict(WC=0.5, DUS=1.0, LV=0.5, CM=1.0, EV=0.5, BM=1.0, YS=0.0)
YBS = dict(DUS=1.0, LV=0.5, EV=0.5)        # sıcak su YB


def cap_temiz(p, rot, so=None, socp=None, sc=None, sccp=None, k=5.5):
    a = {}
    if so is not None:
        a.update(SO=so, SOCP=socp)
    if sc is not None:
        a.update(SC=sc, SCCP=sccp)
    mtyblk.insert('MTY-TEMIZ SU CAP MB', p, rot, k, attrs=a)


def cap_pis(p, rot, ps, pscp, k=5.0):
    mtyblk.insert('MTY-PIS SU CAP SB', p, rot, k, attrs={'PS': ps, 'PSCP': pscp})


# ------------------------------------------------------------------ mimari
ARCH_LAYERS = {'YLZ-DUVAR', 'YLZ-KOLON', 'YLZ-KAPI', 'YLZ-PENCERE', 'YLZ-MERDİVEN', 'YLZ-KORKULUK', 'YLZ-ISLAK HACİMLER',
               'YLZ-PERDE', 'YLZ-VERANDA-BALKON', 'YLZ-BACA', 'YLZ-HAVALANDIRMA', 'YLZ-ÇIKMA İZDÜŞÜMÜ', 'YLZ-İSTİNAT',
               'A-YALITIM PERDE', 'YLZ-ÇATI', 'YLZ-SU DEPOSU'}
FURN_LAYERS = {'YLZ-TEFRİŞ'}


def clean_text(t):
    t = re.sub(r'\\U\+([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1), 16)), t)
    t = re.sub(r'\\[A-Za-z][^;\\]*;', '', t)
    t = t.replace('\\P', ' ').replace('{', '').replace('}', '').replace('%%c', 'Ø').replace('%%C', 'Ø')
    return re.sub(r'\s+', ' ', t).strip()


def copy_arch(flat, win, furn=True, room_labels=True, roof=False, extra_layers=()):
    """kaynak penceredeki mimariyi (kaynak koordinatında) kayda ekler; o anki dönüşüm (push) uygulanır"""
    x0, y0, x1, y1 = win
    ins = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    lays = set(ARCH_LAYERS) | set(extra_layers)
    for r in flat:
        k, lay = r[0], r[1]
        if lay in lays or (furn and lay in FURN_LAYERS):
            tl = ARC_F if lay in FURN_LAYERS else (ARC_K if lay == 'YLZ-KOLON' else ARC_L)
            if k == 'L' and ins(r[2][0]) and ins(r[2][1]):
                L(r[2][0], r[2][1], tl)
            elif k == 'P' and all(ins(p) for p in r[2]):
                PL(r[2], tl)
            elif k == 'C' and ins(r[2][:2]):
                C(r[2][:2], r[2][2], tl)
        if k == 'T' and room_labels and ins(r[2][0]) and lay in ('YLZ-YAZI', 'YLZ-TEFRİŞ'):
            t = clean_text(r[2][1])
            m = re.search(r'(.+?)\s*ALAN\s*:\s*([0-9]+,[0-9]+)\s*M²', t)
            if m:
                T((r[2][0][0], r[2][0][1] - 8), m.group(1).strip(), 10, ARC_T, 'L')
                T((r[2][0][0], r[2][0][1] - 21), 'A = %s m²' % m.group(2), 8, ARC_T, 'L')
            elif re.fullmatch(r'D-\d+', t) or t.startswith('İŞ YERİ') or t in ('BİNA GİRİŞİ',):
                T(r[2][0], t, 14, ARC_T, 'L')


def columns(flat, win, layer='YLZ-KOLON'):
    x0, y0, x1, y1 = win
    out = []
    for r in flat:
        if r[1] == layer and r[0] == 'P' and len(r[2]) >= 4 and all(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in r[2]):
            pg = Polygon(r[2]).buffer(0)
            if pg.area > 200 and not any(pg.symmetric_difference(q).area < 1 for q in out):
                out.append(pg)
    return out


def hatch_cols(cols):
    for pg in cols:
        x0, y0, x1, y1 = pg.bounds
        L((x0, y0), (x1, y1), ARC_K); L((x0, y1), (x1, y0), ARC_K)


# ------------------------------------------------------------------ armatürler (MTY blokları: y=0 duvar yüzü, +y odaya)
BLK = {'WC': 'KLOZET1', 'LV': 'LAVABO1', 'EV': 'EVIYE1', 'DUS': 'DUS TEKNESI1', 'CM': 'CAMASIR MAKINASI1',
       'BM': 'BULASIK MAKINASI1', 'KOMBI': 'KOMBI1', 'YS': 'YER SUZGECI DN501'}
BLK_PTS = {
    'KLOZET1': dict(SO=(0.0, -4.52), PS=(0.0, 20.0)),
    'LAVABO1': dict(SO=(-5.0, -3.52), SC=(5.0, -3.52), PS=(0.0, 15.0)),
    'EVIYE1': dict(SO=(-5.0, -3.52), SC=(5.0, -3.52), PS=(0.0, 15.0)),
    'DUS TEKNESI1': dict(SO=(-10.0, -4.52), SC=(10.0, -4.52), PS=(0.0, 25.0)),
    'CAMASIR MAKINASI1': dict(SO=(0.0, -4.52), PS=(0.0, 20.0)),
    'BULASIK MAKINASI1': dict(SO=(0.0, -4.52), PS=(0.0, 20.0)),
    'KOMBI1': dict(SO=(18.89, -3.52), SC=(28.89, -3.52), HG=(6.0, -3.52), HD=(12.0, -3.52)),
    'YER SUZGECI DN501': dict(PS=(0.0, 0.0)),
}


def bpt(o, rot, p, sx=1.0):
    x, y = p[0] * sx, p[1]
    a = math.radians(rot)
    return (round(o[0] + x * math.cos(a) - y * math.sin(a), 2), round(o[1] + x * math.sin(a) + y * math.cos(a), 2))


class Fix:
    def __init__(self, kind, o, rot, sx=1.0, name=None):
        self.kind, self.o, self.rot, self.sx = kind, o, rot, sx
        self.blk = BLK[kind]
        self.name = name or kind

    def cp(self, w):
        return bpt(self.o, self.rot, BLK_PTS[self.blk][w], self.sx)

    def draw(self):
        mtyblk.insert(self.blk, self.o, self.rot, 1.0, sx=None if self.sx == 1 else self.sx)
        for w in BLK_PTS[self.blk]:
            node(self.cp(w), self.name + '.' + w)


def orth(a, b, first='x'):
    """a'dan b'ye dik açılı yol"""
    return [a, (b[0], a[1]), b] if first == 'x' else [a, (a[0], b[1]), b]


# ------------------------------------------------------------------ kolon / etiket
def kolon_pis(c, nm, off=(40, 40), k=0.6):
    mtyblk.insert('MTY-PIS SU KOLON', c, 0, k)
    node(c, nm)
    tp = (c[0] + off[0], c[1] + off[1])
    L(c, tp, 'MTY-PISSU-KOLONNO')
    mtyblk.insert('MTY-KOLON NO PIS SU', tp, 0, 0.7, attrs={'K': nm})


def kolon_temiz(c, r=2.6, lay=CS):
    cad.KOLON(c, r, lay, 'temiz')


def balloon(p, n, lay=YBL, r=5.0):
    C(p, r, lay); T(p, str(n), 5.5, lay, 'MC')


def title(p, txt, sub=None, h=30):
    T(p, txt, h, 'MTY-KAT-ADI', 'C')
    L((p[0] - len(txt) * h * 0.33, p[1] - 6), (p[0] + len(txt) * h * 0.33, p[1] - 6), 'MTY-KAT-ADI')
    if sub:
        T((p[0], p[1] - 30), sub, 13, 'MTY-KAT-ADI', 'C')


# ------------------------------------------------------------------ kontrol
def check(cols_world, shafts=()):
    rep = []
    for n in NET:
        ls = LineString(n['pts'])
        for c in cols_world:
            if ls.intersects(c) and ls.intersection(c).length > 0.5:
                rep.append(('KOLON ÇAKIŞMASI', n['sys'], n['lay'], [round(v) for v in c.bounds]))
    pts_nodes = [p for p, _ in NODES]
    by = {}
    for n in NET:
        by.setdefault(n['sys'], []).append(n)
    for n in NET:
        for e in (n['pts'][0], n['pts'][-1]):
            ok = any(math.hypot(e[0] - q[0], e[1] - q[1]) < 0.6 for q in pts_nodes)
            if not ok:
                for m in by[n['sys']]:
                    if m is not n and LineString(m['pts']).distance(Point(e)) < 0.6:
                        ok = True
                        break
            if not ok:
                rep.append(('BOŞTA UÇ', n['sys'], n['lay'], (round(e[0], 1), round(e[1], 1))))
    return rep
