"""Cafer Göktaş konut - REVİZYON 2: sıhhi tesisat + kombili yerden ısıtma (ROTAŞ / MTY blokları)."""
import math, sys
sys.path.insert(0, '/home/claude/nb')
from shapely.geometry import LineString, Point, Polygon, box
import cad
from cad import *
import mtyblk
import cg_build as OLD            # mimari temizleme / çerçeve yardımcıları
import cg2_geo as G
import cg2_heat as H
import spiral3

CS, CH, PS = 'MTY-SOGUKSU-BORU', 'MTY-SICAKSU-BORU', 'MTY-PIS-SU-BORUSU'
TF, VN, CD, YZ = 'MTY-TEFRIS', 'MTY-VANA', 'MTY-CIHAZ', 'MTY-YAZI'
TSC, PSC, YB = 'MTY-TEMIZSU-CAP', 'MTY-PISSU-CAP', 'MTY-YUK-BIRIMI'
PEX, HGL, HDL, HCAP = 'MTY-PEX-BORU', 'MTY-ISITMA-GIDIS-BORU', 'MTY-ISITMA-DONUS-BORU', 'STM-ISITMA-CAP'
FLOORS = OLD.FLOORS            # ('Z','ZEMİN KAT',0,1) ...
HDY = OLD.HDY
CATI_DX = OLD.CATI_DX

KOMBI_SPEC = ['DUVAR TİPİ HERMETİK YOĞUŞMALI KOMBİ (HER DAİREYE 1 ADET)',
              'ISITMA KAPASİTESİ : 24 kW  -  SICAK SU : 11,5 l/dk (ΔT=30 K)',
              'YAKIT : DOĞALGAZ  -  BACA : Ø60/100 KOAKSİYEL, DIŞ CEPHEYE',
              'ISITMA SUYU : 50/40 °C (YERDEN ISITMA, KOMBİ MAKS. 50 °C AYARLI)']

# ------------------------------------------------------------------ çap seçimi
def dn_temiz(yb):
    """TS 1258 (ROTAŞ PPRC tablosu)"""
    for lim, d in ((2.25, 20), (7.84, 25), (19.36, 32), (46.24, 40), (108.4, 50)):
        if yb <= lim + 1e-9:
            return d
    return 63


def dn_pis(sb, min_d=50):
    for lim, d in ((0.8, 50), (5.0, 70), (14.0, 100), (17.0, 125), (60.0, 150), (200.0, 200)):
        if sb <= lim + 1e-9:
            return max(d, min_d)
    return 250


def fmt(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return s if '.' in s else s + '.0'


# ------------------------------------------------------------------ boru ağı kaydı (bağlantı kontrolü için)
NET = []          # dict(sys, pts, floor)
NODES = []        # (x, y, ad) geçerli uç noktaları (armatür, kolon, kollektör, cihaz)


def pipe(pts, lay, sysn, fi=None):
    PL(pts, lay)
    NET.append(dict(sys=sysn, lay=lay, pts=[cad.P(p) for p in pts], fi=fi))


def node(p, name):
    NODES.append((cad.P(p), name))


# ------------------------------------------------------------------ MTY çap etiketi blokları
def cap_temiz(p, rot, so=None, socp=None, sc=None, sccp=None, k=6.0):
    a = {}
    if so is not None:
        a.update(SO=so, SOCP=socp)
    if sc is not None:
        a.update(SC=sc, SCCP=sccp)
    mtyblk.insert('MTY-TEMIZ SU CAP MB', p, rot, k, attrs=a)


def cap_pis(p, rot, ps, pscp, k=6.0):
    mtyblk.insert('MTY-PIS SU CAP SB', p, rot, k, attrs={'PS': ps, 'PSCP': pscp})


def seg_mid(a, b, f=0.5):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def seg_rot(a, b):
    """etiket bloğu dönüşü: yatay -> 0, dikey -> 90 (okunur)"""
    return 0 if abs(b[0] - a[0]) >= abs(b[1] - a[1]) else 90


# ------------------------------------------------------------------ mimari
def put_floor_arch(k, dy=0.0, furn=True, texts=True):
    it = OLD.arch_items(k * 1250, furn=furn)
    if not texts:
        it = [x for x in it if x[0] != 'T']
    OLD.put_arch(it, 0, dy)


# ================================================================== SIHHİ TESİSAT KAT PLANI
FIXDATA = {  # pis/temiz çap etiketleri armatür başına
    'DUS': dict(so=1.0, sc=1.0, sb=0.7), 'WC': dict(so=0.5, sb=2.0), 'LV': dict(so=0.5, sc=0.5, sb=0.5),
    'CM': dict(so=1.0, sb=0.8), 'EV': dict(so=0.5, sc=0.5, sb=0.8), 'BM': dict(so=1.0, sb=0.8), 'YS': dict(sb=0.8)}
YB_DAIRE = 4.5      # WC .5 + LV .5 + DUŞ 1 + ÇM 1 + EV .5 + BM 1 (her armatür bir kez)
YB_SICAK = 2.0      # LV + DUŞ + EV
SB = dict(WC=10.0, DUS=7.0, LV=2.0, CM=4.0, YS=2.0, EV=4.0, BM=4.0)   # örnek şema (ROTAŞ) pis su birimleri
SB_BANYO = SB['DUS'] + SB['WC'] + SB['LV'] + SB['CM'] + SB['YS']        # 25 SB
SB_MUTFAK = SB['EV'] + SB['BM']                                         # 8 SB


def dn_sb(sb, wc=False):
    """ROTAŞ örnek şeması: WC'li hat en az Ø100; Ø50 ≤10 SB, Ø70 ≤30 SB, Ø100 ≤160 SB"""
    for lim, d in ((10, 50), (30, 70), (160, 100), (300, 125), (600, 150)):
        if sb <= lim + 1e-9:
            return max(d, 100 if wc else 50)
    return 200


def fixtures_plan():
    for key, (blk, o, rot, sx, yb, sb, dn, nm) in G.FIX.items():
        mtyblk.insert(blk, o, rot, 1.0, sx=None if sx == 1 else sx)
        for w in G.BLK_PTS[blk]:
            node(G.cp(key, w), key + '.' + w)
    b, o, r, sx = G.KOMBI
    mtyblk.insert(b, o, r, 1.0, sx=sx)
    for w in ('SO', 'SC', 'HG', 'HD'):
        node(G.kombi_cp(w), 'KOMBI.' + w)
    # ısıtma bağlantı uçları (kombi alt yüzü)
    for w in ('HG', 'HD'):
        C(G.kombi_cp(w), 1.2, CD)


def fixture_labels():
    """armatür bağlantı etiketleri: armatür yanında numara balonu + bina doğusunda açıklama listesi"""
    items = [
        ('1', (-4938.0, -22428.0), 'DUŞ : SO/SC Ø20 - 1.0 YB / PİS Ø50 - 7 SB'),
        ('2', (-4852.0, -22428.0), 'WC (HELA) : SO Ø20 - 0.5 YB / PİS Ø100 - 10 SB'),
        ('3', (-4855.0, -22497.0), 'YER SÜZGECİ : PİS Ø50 - 2 SB'),
        ('4', (-4826.0, -22582.0), 'ÇAMAŞIR MAK. : SO Ø20 - 1.0 YB / PİS Ø50 - 4 SB'),
        ('5', (-4932.0, -22618.0), 'LAVABO : SO/SC Ø20 - 0.5 YB / PİS Ø50 - 2 SB'),
        ('6', (-4935.0, -22688.0), 'EVİYE : SO/SC Ø20 - 0.5 YB / PİS Ø50 - 4 SB'),
        ('7', (-4870.0, -22700.0), 'BULAŞIK MAK. (TEZGAH ALTI) : SO Ø20 - 1.0 YB / PİS Ø50 - 4 SB'),
    ]
    tx, ty = -4712.0, -22440.0
    T((tx, ty + 14.0), 'ARMATÜR BAĞLANTILARI', 7.0, YB, 'L')
    for i, (n, p, s) in enumerate(items):
        C(p, 4.5, YB); T(p, n, 5.0, YB, 'MC')
        q = (tx + 4.0, ty - i * 13.0)
        C(q, 4.5, YB); T(q, n, 5.0, YB, 'MC')
        T((q[0] + 7.0, q[1] - 2.2), s, 4.8, YB, 'L')


def kombi_text(dno, y0=-23060.0):
    T((-5330.0, y0), 'KOMBİ (DAİRE %d) - HERMETİK BACA DIŞ CEPHEYE' % dno, 8.0, CD, 'L')
    for i, s in enumerate(KOMBI_SPEC):
        T((-5330.0, y0 - 12.0 - i * 9.0), s, 6.0, CD, 'L')


def water_entry(fi):
    """zemin: sayaç grubu (ADK -> kollektör -> 3 daire sayacı); katlar: daire kolonundan antreye"""
    key, name, fdx, dno = FLOORS[fi]
    x0, y0, x1, y1 = G.SAYAC_BOX
    yb_ = -22660.0
    sx0 = -5140.0
    ent = [(sx0, yb_), (sx0, G.COLD_Y), (-4966.0, G.COLD_Y)]
    if fi == 0:
        RECT(x0, y0, x1, y1, VN)
        T((x0 - 4.0, y0 - 8.0), 'SAYAÇ GRUBU (BİNA GİRİŞİ - ZEMİN)', 6.5, VN, 'R')
        T((x0 - 4.0, y0 - 16.0), '3 ADET DAİRE SAYACI + KÜRESEL VANA + ÇEK VALF', 5.0, VN, 'R')
        ky = G.KOLL_Y
        pipe([G.ADK, (G.ADK[0], ky), (G.METER[3], ky)], CS, 'S', fi)
        for d in (1, 2, 3):
            mx = G.METER[d]
            if d == 1:
                pipe([(mx, ky), (mx, yb_)] + ent, CS, 'S', fi)
            else:
                pipe([(mx, ky), (G.D2R if d == 2 else G.D3R)], CS, 'S', fi)
            mtyblk.insert('MTY-SU SAYACI', (mx, ky + 5.5), 90, 0.32)
        node(G.ADK, 'ADK')
        cap_temiz((-5112.0, G.COLD_Y), 0, so='D1 %s YB' % fmt(YB_DAIRE), socp='Ø%d' % dn_temiz(YB_DAIRE), k=5.5)
    else:
        rz = G.D2R if fi == 1 else G.D3R
        pipe([rz, (rz[0], yb_)] + ent, CS, 'S', fi)
        node(rz, 'D%dR' % dno)
        mtyblk.insert('MTY-KURESEL VANA', (rz[0] + 14.0, yb_), 0, 0.35)
        cap_temiz((-5112.0, G.COLD_Y), 0, so='D%d %s YB' % (dno, fmt(YB_DAIRE)), socp='Ø%d' % dn_temiz(YB_DAIRE), k=5.5)
    CEKVALF((sx0, -22650.0), 0.45, 90)
    # geçen kolonlar
    rs = [(G.DBK, 'DBK'), (G.ADK, 'ADK')] + ([(G.D2R, 'D2')] if fi < 1 else []) + ([(G.D3R, 'D3')] if fi < 2 else [])
    for p, nm in rs:
        KOLON(p, 2.6, CS, 'temiz')
        node(p, nm)
    T((x0 - 4.0, y0 + 40.0), 'TEMİZ SU KOLONLARI: DBK Ø32 (ŞEBEKE→DEPO), ADK Ø32 (DEPO→SAYAÇ GRUBU)', 5.0, TSC, 'R')
    lab = 'D2 Ø25 (1. KAT), D3 Ø25 (2. KAT)' if fi == 0 else ('D2 KOLONU BU KATTA BİTER, D3 Ø25 (2. KAT)' if fi == 1 else 'D3 KOLONU BU KATTA BİTER')
    T((x0 - 4.0, y0 + 33.0), lab, 5.0, TSC, 'R')


def sihhi_kat(fi):
    key, name, fdx, dno = FLOORS[fi]
    cad.push(MOVE(fdx, 0))
    fixtures_plan()
    # ---------------- temiz su: soğuk
    water_entry(fi)
    # duvar içi soğuk hat (antre duvarı -> çamaşır mak.)
    pipe([(-4966.0, G.COLD_Y), (-4807.0, G.COLD_Y), G.cp('CM', 'SO')], CS, 'S', fi)
    pipe([(-4901.0, G.COLD_Y), G.cp('LV', 'SO')], CS, 'S', fi)
    pipe([(-4894.0, G.COLD_Y), (-4894.0, G.cp('EV', 'SO')[1]), G.cp('EV', 'SO')], CS, 'S', fi)
    pipe([(-4855.0, G.COLD_Y), G.cp('BM', 'SO')], CS, 'S', fi)
    # banyo soğuk kolonu (antre-banyo duvarı) -> duş, wc
    cy = -22409.0
    pipe([(-4956.0, G.COLD_Y), (-4956.0, cy), (-4820.0, cy), G.cp('WC', 'SO')], CS, 'S', fi)
    pipe([(-4898.0, cy), G.cp('DUS', 'SO')], CS, 'S', fi)
    # kombi soğuk besleme
    KC = [(G.KC_X, G.COLD_Y), (G.KC_X, -22750.0), (-5168.0, -22750.0), (-5168.0, -22934.0), (-5320.0, -22934.0),
          (-5320.0, G.kombi_cp('SO')[1]), G.kombi_cp('SO')]
    pipe(KC, CS, 'S', fi)
    VANA((G.KC_X, -22690.0), 0.5, 90)
    # ---------------- temiz su: sıcak (kombi -> çevre duvarları -> mutfak/banyo)
    hy = G.HOT_Y
    sc = G.kombi_cp('SC')
    KH = [sc, (-5312.0, sc[1]), (-5312.0, -23000.0), (-4826.0, -23000.0), (-4812.0, -22851.0), (-4812.0, hy),
          (-4962.0, hy), (-4962.0, -22404.0), (-4918.0, -22404.0), G.cp('DUS', 'SC')]
    pipe(KH, CH, 'S', fi)
    pipe([(-4901.0, hy), G.cp('EV', 'SC')], CH, 'S', fi)
    pipe([(-4886.0, hy), (-4886.0, G.cp('LV', 'SC')[1]), G.cp('LV', 'SC')], CH, 'S', fi)
    # ---------------- çap etiketleri (temiz)
    k = 5.5
    cap_temiz((-5112.0, G.COLD_Y), 0, so='%s YB' % fmt(YB_DAIRE), socp='Ø%d' % dn_temiz(YB_DAIRE), k=k)
    cap_temiz((-5010.0, G.COLD_Y), 0, so='%s YB' % fmt(YB_DAIRE - YB_SICAK + 1.0), socp='Ø25', k=k) if False else None
    cap_temiz((G.KC_X, -22672.0), 90, so='%s YB' % fmt(YB_SICAK), socp='Ø%d' % dn_temiz(YB_SICAK), k=k)
    cap_temiz((-5250.0, -22934.0), 0, so='%s YB' % fmt(YB_SICAK), socp='Ø20', k=k)
    cap_temiz((-5000.0, -23000.0), 0, sc='%s YB' % fmt(YB_SICAK), sccp='Ø%d' % dn_temiz(YB_SICAK), k=k)
    cap_temiz((-4812.0, -22780.0), 90, sc='%s YB' % fmt(YB_SICAK), sccp='Ø20', k=k)
    cap_temiz((-4956.0, -22460.0), 90, so='1.5 YB', socp='Ø20', k=k)
    cap_temiz((-4962.0, -22560.0), 90, sc='1.0 YB', sccp='Ø20', k=k)
    cap_temiz((-4840.0, cy), 0, so='0.5 YB', socp='Ø20', k=k)
    # ---------------- pis su (döşeme)
    pk, mk = G.PK, G.MK
    j1 = (-4802.0, -22606.0)
    pipe([G.cp('LV', 'PS'), (-4881.0, -22606.0), j1], PS, 'P', fi)
    pipe([G.cp('CM', 'PS'), j1], PS, 'P', fi)
    pipe([j1, (-4791.0, -22606.0), (-4791.0, -22480.0)], PS, 'P', fi)
    pipe([G.cp('DUS', 'PS'), (-4908.0, -22465.0), (-4893.0, -22480.0), G.cp('YS', 'PS')], PS, 'P', fi)
    pipe([G.cp('YS', 'PS'), (-4791.0, -22480.0), (-4786.0, -22470.0), pk], PS, 'P', fi)
    pipe([G.cp('WC', 'PS'), (-4789.0, -22462.0), pk], PS, 'P', fi)
    j2 = (-4921.0, -22661.0)
    pipe([G.cp('EV', 'PS'), j2], PS, 'P', fi)
    pipe([G.cp('BM', 'PS'), (-4861.0, -22672.0), (-4910.0, -22672.0), j2], PS, 'P', fi)
    pipe([j2, (-4938.0, -22661.0), mk], PS, 'P', fi)
    kp = 5.0
    cap_pis((-4858.0, -22606.0), 0, '2 SB', 'Ø50', kp)
    cap_pis((-4791.0, -22560.0), 90, '6 SB', 'Ø50', kp)
    cap_pis((-4880.0, -22480.0), 0, '7 SB', 'Ø50', kp)
    cap_pis((-4830.0, -22480.0), 0, '9 SB', 'Ø50', kp)
    cap_pis((-4787.0, -22492.0), 90, '15 SB', 'Ø70', kp)
    cap_pis((-4805.0, -22446.0), 0, '10 SB', 'Ø100', kp)
    cap_pis((-4885.0, -22672.0), 0, '4 SB', 'Ø50', kp)
    cap_pis((-4932.0, -22661.0), 0, '8 SB', 'Ø50', kp)
    # kolonlar
    mtyblk.insert('MTY-PIS SU KOLON', pk, 0, 0.6)
    mtyblk.insert('MTY-PIS SU KOLON', mk, 0, 0.5)
    node(pk, 'PK'); node(mk, 'MK')
    _kolon_tag(pk, 'PK1', (60.0, 50.0))
    _kolon_tag(mk, 'MK1', (-15.0, -150.0))
    T((pk[0] + 35.0, pk[1] + 80.0), 'Ø100 / %d SB' % (SB_BANYO * (3 - fi)), 6.5, PSC, 'L')
    T((mk[0] + 27.0, mk[1] - 150.0), 'Ø70 / %d SB' % (SB_MUTFAK * (3 - fi)), 6.5, PSC, 'L')
    # kombi bilgisi
    kombi_text(dno)
    fixture_labels()
    cad.pop()


def _kolon_tag(c, txt, off):
    tp = (c[0] + off[0], c[1] + off[1])
    L(c, (tp[0] - (27.5 if off[0] > 0 else -27.5) * (1 if abs(off[0]) > 30 else 0), tp[1] + (0 if abs(off[0]) > 30 else 27.5)), 'MTY-PISSU-KOLONNO')
    mtyblk.insert('MTY-KOLON NO PIS SU', tp, 0, 0.7, attrs={'K': txt})


# ------------------------------------------------------------------ zemin: şebeke, ana sayaç, pis su altyapısı (SASKİ)
R1 = (-4873.0, -23085.0)
PB = (-4873.0, -23165.0)
NIS = (-5445.0, -22490.0)       # ana sayaç nişi (bina girişi kuzeyi, batı cephe)


def zemin_extra():
    # şebeke -> ana sayaç -> DBK
    nx, ny = NIS
    RECT(nx - 14, ny - 30, nx + 6, ny + 30, VN)
    T((nx - 18, ny + 36), 'ANA SAYAÇ NİŞİ (SASKİ)', 7, VN, 'R')
    pipe([(nx - 40, -23180.0), (nx - 40, ny - 18), (nx - 6, ny - 18)], CS, 'S', 0)
    mtyblk.insert('MTY-KURESEL VANA', (nx - 40, ny - 50), 90, 0.5)
    mtyblk.insert('MTY-SU SAYACI', (nx - 4, ny), 90, 0.6)
    pipe([(nx - 6, ny - 18), (nx - 4, ny - 18), (nx - 4, ny + 18), (-5395.0, ny + 18), (-5395.0, -22660.0),
          (G.DBK[0], -22660.0), G.DBK], CS, 'S', 0)
    T((-5390.0, -22655.0), 'ŞEBEKE → DBK', 5.0, TSC, 'L')
    PISLIK_TUTUCU((nx - 4, ny - 9), 0.45, 90)
    CEKVALF((nx - 4, ny + 10), 0.45, 90)
    T((nx - 48, -23170.0), 'ŞEBEKEDEN (SASKİ) Ø32', 7, TSC, 'R', 90)
    cap_temiz((-5395.0, -22580.0), 90, so='13.5 YB', socp='Ø32', k=5.5)
    node((nx - 40, -23180.0), 'SEBEKE')
    T((-4870.0, -23070.0), 'PİS SU ALTYAPISI (TEMEL ALTI HATLAR, R1, PB) TEMEL PLANINDA GÖSTERİLMİŞTİR.', 6.5, PSC, 'L')


# ------------------------------------------------------------------ çatı planı: depo, kolon çıkışları, havalıklar
def cati_plan():
    cad.push(MOVE(CATI_DX, 0))
    x0, y0, x1, y1 = G.DEPO
    RECT(x0, y0, x1, y1, 'RAST-TEM-SU DEPOSU')
    RECT(x0 + 6, y0 + 6, x1 - 6, y1 - 6, 'RAST-TEM-SU DEPOSU')
    C(((x0 + x1) / 2, (y0 + y1) / 2), 22, 'RAST-TEM-SU DEPOSU')
    T(((x0 + x1) / 2, (y0 + y1) / 2 + 2), 'V = 3,00 m³', 9, 'RAST-TEM-SU DEPOSU', 'MC')
    T(((x0 + x1) / 2, (y0 + y1) / 2 - 12), 'MENHOL', 6, 'RAST-TEM-SU DEPOSU', 'MC')
    T((x0 + 20, y0 - 45), 'KULLANMA SUYU DEPOSU 3,00 m³ (PE, ŞAMANDIRALI)', 8, YZ, 'L')
    # DBK / ADK çatı arasında depoya
    pipe([G.DBK, (-5215.0, G.DBK[1]), (-5215.0, -22560.0), (x0, -22560.0)], CS, 'S', 3)
    pipe([G.ADK, (-5110.0, G.ADK[1]), (-5110.0, -22640.0), (x0, -22640.0)], CS, 'S', 3)
    node((x0, -22560.0), 'DEPO.IN'); node((x0, -22640.0), 'DEPO.OUT')
    SAMANDIRALI_VANA((x0 + 4, -22560.0), 0.6)
    mtyblk.insert('MTY-KURESEL VANA', (x0 - 25, -22560.0), 0, 0.45)
    mtyblk.insert('MTY-KURESEL VANA', (x0 - 25, -22640.0), 0, 0.45)
    KOLON(G.DBK, 3.5, CS, 'temiz'); KOLON(G.ADK, 3.5, CS, 'temiz')
    node(G.DBK, 'DBK'); node(G.ADK, 'ADK')
    for q in ((x1, -22560.0), (x1, -22655.0)):
        node(q, 'DEPO')
    cap_temiz((-5090.0, -22560.0), 0, so='DBK', socp='Ø32', k=5.5)
    cap_temiz((-5080.0, -22640.0), 0, so='ADK 13.5 YB', socp='Ø32', k=5.5)
    # taşma + boşaltma -> YB2 yağmur inişine (birleşik hat, boşta uç yok)
    yb2 = YB_PTS['YB2']
    yj = -22175.0
    pipe([(x1, -22560.0), (x1 + 25, -22560.0), (x1 + 25, yj), (yb2[0], yj), (yb2[0], yb2[1] - 5.0)], CS, 'X', 3)
    pipe([(x1, -22655.0), (x1 + 35, -22655.0), (x1 + 35, yj)], CS, 'X', 3)
    node((yb2[0], yb2[1] - 5.0), 'YB2-TASMA'); node((x1 + 35, yj), 'TASMA-BIRLESIM')
    C((x1 + 35, yj), 1.5, CS)
    mtyblk.insert('MTY-KURESEL VANA', (x1 + 35, -22620.0), 90, 0.45)
    T((x1 + 45, -22420.0), 'TAŞMA Ø40 + BOŞALTMA Ø32 (VANALI)', 6, TSC, 'L', 90)
    T((x1 + 45, yj + 5), 'Ø40 → YB2 YAĞMUR İNİŞİNE', 6, TSC, 'L')
    # depo havalığı
    C((x0 + 20, y1 - 20), 3, 'RAST-TEM-SU DEPOSU'); T((x0 + 26, y1 - 23), 'HAVALIK (SİNEKLİKLİ)', 5, YZ, 'L')
    T((x0 + 6, y0 + 10), 'SEVİYE GÖSTERGESİ', 5, YZ, 'L')
    # çatı kapağı (mimari)
    T((G.CATI_KAPAK[0], G.CATI_KAPAK[1] - 10), 'ÇATI KAPAĞI 80x80 (DEPO BAKIM ERİŞİMİ)', 6, YZ, 'L')
    # pis su havalıkları
    pk = G.PK
    KOLON(pk, 6, PS); C(pk, 10, PS)
    T((pk[0] - 10, pk[1] - 25), 'PK1 HAVALIK Ø100 (ÇATIDAN 50 cm YUKARI)', 6.5, PSC, 'R')
    mk = G.MK
    mk2 = (-5030.0, -22680.0)
    pipe([mk, (mk[0], -22680.0), mk2], PS, 'H', 3)
    KOLON(mk2, 5, PS); C(mk2, 9, PS)
    node(mk, 'MK'); node(mk2, 'MK-HAV')
    T((mk2[0] - 12, mk2[1] - 12), 'MK1 HAVALIK Ø70 (ÇATI ARASINDA 2x45° İLE DEPODAN SAPTIRILIR)', 6, PSC, 'R')
    cad.pop()


# ================================================================== YERDEN ISITMA
def heat_floor(fi):
    """kat yerden ısıtma planı. Dönüş: devre listesi"""
    key, name, fdx, dno = FLOORS[fi]
    cad.push(MOVE(fdx, HDY))
    calc = {r['name']: r for r in H.calc(key)}
    res = []
    # --- spiraller
    spir = {}
    for zk, (poly, e, f, s, room, zn) in G.ZONES.items():
        if zk == 'ODA':
            W = [(-5391.0, -22419.0), (-5142.0, -22419.0), (-5142.0, -22202.0), (-5391.0, -22202.0)]
            full, info = spiral3.bifilar(W, 2, 'a', s)
        else:
            full, info = spiral3.bifilar(poly, e, f, s)
        spir[zk] = (full, s)
    # --- bağlantı (ayak) yolları
    KX = G.KX
    legs = {}
    # ODA: W spirali + E bölümünde menderes çift + antre
    cl = [(-5142.0, -22209.5), (-5002.5, -22209.5), (-5002.5, -22239.5), (-5117.5, -22239.5), (-5117.5, -22269.5),
          (-5002.5, -22269.5), (-5002.5, -22477.5), (KX, -22477.5)]
    legs['ODA'] = _pair(cl, 7.5)
    # ODA 2
    cl = [(-4939.0, -22384.0), (-4977.0, -22384.0), (-4977.0, -22495.0), (KX, -22495.0)]
    legs['ODA 2'] = _pair(cl, 5.0)
    # BANYO
    cl = [(-4939.0, -22511.0), (KX, -22511.0)]
    legs['BANYO'] = _pair(cl, 5.0)
    # SALON-1
    cl = [(-5003.0, -22725.0), (-5003.0, -22528.0), (KX, -22528.0)]
    legs['SALON-1'] = _pair(cl, 5.0)
    # SALON-2
    cl = [(-5028.0, -22770.0), (-5028.0, -22543.0), (KX, -22543.0)]
    legs['SALON-2'] = _pair(cl, 5.0)
    port_no = {'ODA': 1, 'ODA 2': 2, 'BANYO': 3, 'SALON-1': 4, 'SALON-2': 5}
    # --- çiz
    for zk in ('ODA', 'ODA 2', 'BANYO', 'SALON-1', 'SALON-2'):
        full, s = spir[zk]
        la, lb = legs[zk]
        # spiral uçlarını ayaklara bağla: ayak uçları spiral başı/sonu ile çakışmalı
        sa, sb = full[0], full[-1]
        if _d(la[0], sa) > 0.5 and _d(la[0], sb) < 0.5:
            la, lb = lb, la
        path = list(reversed(la)) + full[1:-1] + lb      # kollektör -> gidiş -> spiral -> dönüş -> kollektör
        PL(path, PEX)
        NET.append(dict(sys='H', lay=PEX, pts=[cad.P(p) for p in path], fi=fi))
        node(path[0], 'KOLL'); node(path[-1], 'KOLL')
        Lm = LineString(path).length / 100.0
        res.append(dict(port=port_no[zk], zone=zk, room=G.ZONES[zk][4], s=s, L=Lm, A=Polygon(G.ZONES[zk][0]).area / 1e4,
                        poly=G.ZONES[zk][0], path=path, sup=path[0], ret=path[-1]))
    # oda bazında ısı yükü dağıtımı (alan oranı)
    for d in res:
        same = [x for x in res if x['room'] == d['room']]
        tot = sum(x['A'] for x in same)
        d['W'] = calc[d['room']]['Q'] * d['A'] / tot
    res.sort(key=lambda d: d['port'])
    # --- kollektör
    x0, y0, x1, y1 = G.KOLL_BOX
    RECT(x0, y1, x1, y0, 'MTY-KOLLETOR')
    L((x0 + 4, y0 - 4), (x0 + 4, y1 + 4), 'MTY-KOLLETOR'); L((x0 + 8, y0 - 4), (x0 + 8, y1 + 4), 'MTY-KOLLETOR')
    for d in res:
        for p, lab in ((d['sup'], 'G'), (d['ret'], 'D')):
            C(p, 1.6, 'MTY-KOLLETOR')
    for d in res:
        T((x1 + 2, (d['sup'][1] + d['ret'][1]) / 2 + 2.5), 'P%d' % d['port'], 4.5, 'MTY-KOLLETOR', 'L') if False else None
    T((x0 - 6, (y0 + y1) / 2), 'KOLLEKTÖR DOLABI - 5 AĞIZLI (DEBİMETRELİ)', 6.5, 'MTY-KOLLETOR', 'C', 90)
    # --- kombi -> kollektör (gidiş/dönüş)
    hg = [(KX, G.INLET['HG'][0]), (G.INLET['HG'][1], G.INLET['HG'][0]), (-5060.0, -22738.0), (-5180.0, -22738.0),
          (-5180.0, -22922.0), (-5332.0, -22922.0), (-5332.0, G.kombi_cp('HG')[1]), G.kombi_cp('HG')]
    hd = [(KX, G.INLET['HD'][0]), (G.INLET['HD'][1], G.INLET['HD'][0]), (-5054.0, -22744.0), (-5174.0, -22744.0),
          (-5174.0, -22928.0), (-5326.0, -22928.0), (-5326.0, G.kombi_cp('HD')[1]), G.kombi_cp('HD')]
    pipe(hg, HGL, 'K', fi); pipe(hd, HDL, 'K', fi)
    b, o, r, sx = G.KOMBI
    mtyblk.insert(b, o, r, 1.0, sx=sx)
    node(G.kombi_cp('HG'), 'KOMBI.HG'); node(G.kombi_cp('HD'), 'KOMBI.HD')
    node((KX, G.INLET['HG'][0]), 'KOLL'); node((KX, G.INLET['HD'][0]), 'KOLL')
    tot = sum(d['W'] for d in res) + calc['ANTRE']['Q']
    T((-5305.0, -22958.0), '%.1fW-DN20 (GİDİŞ/DÖNÜŞ)' % tot, 6.0, HCAP, 'L')
    kombi_text(dno)
    # --- mahal etiketleri + devre etiketleri
    zprefix = 'Z' if key == 'Z' else key
    ztag = lambda n: ('Z%02d' % n) if key == 'Z' else ('%s%02d' % (key, n))
    lab_pos = {'SALON + MUTFAK': (-4924.0, -22800.0), 'ODA': (-5265.0, -22300.0), 'ODA 2': (-4855.0, -22285.0),
               'BANYO + WC': (-4890.0, -22545.0), 'ANTRE': (-5025.0, -22410.0)}
    for rm in calc.values():
        zn = G.ZONE_NO[rm['name']]
        p = lab_pos[rm['name']]
        HEXTAG(p, 'MTY-ISIKAYBIMAHAL', ztag(zn), '%d°C' % rm['ti'], 9)
        T((p[0], p[1] - 30), 'Kcal/h: %.0f' % (rm['Q'] * 0.86), 7, 'MTY-ISIKAYBIMAHAL', 'C')
        T((p[0], p[1] + 26), rm['name'], 9, YZ, 'C')
    T((-5025.0, -22462.0), '(KOLLEKTÖR BAĞLANTI', 5.5, 'MTY-ISIKAYBIMAHAL', 'C')
    T((-5025.0, -22469.0), 'BORULARI İLE ISINIR)', 5.5, 'MTY-ISIKAYBIMAHAL', 'C')
    dev_pos = {'ODA': (-5265.0, -22355.0), 'ODA 2': (-4855.0, -22345.0), 'BANYO': (-4880.0, -22584.0),
               'SALON-1': (-4925.0, -22950.0), 'SALON-2': (-5090.0, -22955.0)}
    for d in res:
        d['zl'] = ztag(G.ZONE_NO[d['room']])
        p = dev_pos[d['zone']]
        T(p, 'P%d / PEX BORU, 16 × 2.0 %.1fW' % (d['port'], d['W']), 6.0, 'MTY-ISIKAYBIMAHAL', 'C')
        T((p[0], p[1] - 8.5), '%.1f / %.2f m / %s' % (d['s'], d['L'], d['zl']), 6.0, 'MTY-ISIKAYBIMAHAL', 'C')
    cad.pop()
    return res, tot, calc


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _pair(cl, h):
    """merkez çizgisinden ± h paralel iki boru (sol, sağ); dik köşeler"""
    ls = LineString(cl)
    a = ls.parallel_offset(h, 'left', join_style=2, mitre_limit=5)
    b = ls.parallel_offset(h, 'right', join_style=2, mitre_limit=5)
    pa = [(round(x, 2), round(y, 2)) for x, y in a.coords]
    pb = [(round(x, 2), round(y, 2)) for x, y in b.coords]
    # shapely 'right' sonucu ters yönde olabilir -> merkez çizgisi yönüne getir
    if _d(pa[0], cl[0]) > _d(pa[-1], cl[0]):
        pa = pa[::-1]
    if _d(pb[0], cl[0]) > _d(pb[-1], cl[0]):
        pb = pb[::-1]
    return pa, pb


# ================================================================== YAĞMUR SUYU
YL, YC = 'MTY-YAGMUR-BORUSU', 'MTY-YAGMUR-BORUSU-CAP'
YB_PTS = {'YB1': (-5448.0, -22200.0), 'YB2': (-4790.0, -22148.0), 'YB3': (-5448.0, -23000.0), 'YB4': (-4815.0, -23052.0)}
YB_TAG = {'YB1': (0.0, 40.0), 'YB2': (45.0, 0.0), 'YB3': (0.0, -40.0), 'YB4': (45.0, 0.0)}
ROOF = [(-4712.0, -22115.0), (-5483.0, -22111.0), (-5476.0, -23086.0), (-4797.0, -23086.0)]


def yagmur_hesap():
    from shapely.geometry import Polygon as _P
    P = _P(ROOF).area / 1e4
    S = P * 0.75 / 1.0
    f = len(YB_PTS)
    A = S / f
    D = 1.13 * math.sqrt(A)
    return dict(P=P, S=S, f=f, A=A, D=D)


def yagmur_inis(tag_side=True, label=True):
    for nm, p in YB_PTS.items():
        C(p, 5.0, YL); C(p, 2.0, YL)
        node(p, nm)
        if label:
            off = YB_TAG[nm]
            tp = (p[0] + off[0], p[1] + off[1])
            L(p, tp, YL)
            mtyblk.insert('MTY-KOLON NO YAGMUR', tp, 0, 0.55, attrs={'K': nm})
            T((tp[0] + 18.0, tp[1] - 4.0), 'Ø100 PVC', 6.0, YC, 'L')


def yagmur_kat(fi):
    key, name, fdx, dno = FLOORS[fi]
    cad.push(MOVE(fdx, 0))
    yagmur_inis()
    cad.pop()


def yagmur_cati():
    cad.push(MOVE(CATI_DX, 0))
    a, b, c, d = ROOF                 # NE, NW, SW, SE
    o = 8.0
    oluk = [(a[0], a[1] - o), (b[0] + o, b[1] - o), (c[0] + o, c[1] + o), (d[0], d[1] + o)]
    PL(oluk, YL)
    for nm, p in YB_PTS.items():
        q = min(oluk, key=lambda z: math.hypot(z[0] - p[0], z[1] - p[1]))
        # oluktan inişe dik bağlantı
        if nm in ('YB1', 'YB3'):
            con = [(oluk[1][0], p[1]), p]
        else:
            con = [(p[0], oluk[0][1] if nm == 'YB2' else oluk[3][1]), p]
        PL(con, YL)
    yagmur_inis()
    T((b[0] + 30.0, b[1] - 25.0), 'YAĞMUR OLUĞU (KUZEY / BATI / GÜNEY SAÇAK)', 7.0, YC, 'L')
    T((c[0] + 30.0, c[1] + 18.0), 'YAĞMUR OLUĞU', 7.0, YC, 'L')
    h = yagmur_hesap()
    T((a[0] + 40.0, -22300.0), 'YAĞMUR İNİŞLERİ: YB1-YB4  4 x Ø100 PVC', 7.0, YC, 'L')
    T((a[0] + 40.0, -22312.0), 'ÇATI ALANI P = %.2f m²  (HESAP: YAĞMUR SUYU ŞEMASI PAFTASI)' % h['P'], 6.0, YC, 'L')
    cad.pop()


# ================================================================== TEMEL PLANI (sadece kolonlar + pis su altyapısı)
TDY = -3800.0
R1 = (-4873.0, -23085.0)
PB = (-4873.0, -23165.0)


def put_columns(dy):
    for k_, l_, d_, p_ in G.FL:
        if l_ != 'Kolon':
            continue
        pts = d_ if k_ == 'P' else ([d_[0], d_[1]] if k_ == 'L' else None)
        if not pts or not all(-5695 < q[0] < -4445 and -23250 < q[1] < -22080 for q in pts):
            continue
        if k_ == 'P':
            R.append(('P', 'MIMARI', [(x, y + dy) for x, y in pts], True, 0))
            if len(pts) >= 4:
                xs_ = [q[0] for q in pts]; ys_ = [q[1] for q in pts]
                R.append(('L', 'MIMARI', (min(xs_), min(ys_) + dy), (max(xs_), max(ys_) + dy)))
                R.append(('L', 'MIMARI', (min(xs_), max(ys_) + dy), (max(xs_), min(ys_) + dy)))
        else:
            R.append(('L', 'MIMARI', (pts[0][0], pts[0][1] + dy), (pts[1][0], pts[1][1] + dy)))
    for k_, l_, d_, p_ in G.FL:     # kolon tarama yerine çapraz
        pass


def temel_plan():
    put_columns(TDY)
    cad.push(MOVE(0.0, TDY))
    sbp = SB_BANYO * 3          # 75
    sbm = SB_MUTFAK * 3         # 24
    main = [G.PK, (-4835.0, -22511.0), (-4835.0, -22920.0), (-4873.0, -22958.0)]
    branch = [G.MK, (-4944.0, -22887.0), (-4873.0, -22958.0)]
    col = [(-4873.0, -22958.0), (-4873.0, R1[1] + 25.0)]
    pipe(main, PS, 'T', 9); pipe(branch, PS, 'T', 9); pipe(col, PS, 'T', 9)
    for p, nm, dk, sb in ((G.PK, 'PK1', 100, sbp), (G.MK, 'MK1', 70, sbm)):
        mtyblk.insert('MTY-PIS SU KOLON', p, 0, 0.6)
        node(p, nm)
        TEMIZLEME_KAPAGI((p[0], p[1] - 14.0), 0.8)
    _kolon_tag(G.PK, 'PK1', (60.0, 50.0))
    _kolon_tag(G.MK, 'MK1', (-80.0, 30.0))
    T((G.PK[0] + 35.0, G.PK[1] + 80.0), 'KOLON DİBİ T.K. - Ø100 / %d SB' % sbp, 6.5, PSC, 'L')
    T((G.MK[0] - 160.0, G.MK[1] + 60.0), 'KOLON DİBİ T.K. - Ø70 / %d SB' % sbm, 6.5, PSC, 'L')
    Lm = LineString(main).length / 100.0
    Lb = LineString(branch).length / 100.0
    Lc = LineString(col).length / 100.0
    cap_pis((-4835.0, -22760.0), 90, '%d SB' % sbp, 'Ø%d' % dn_sb(sbp, True), 6.0)
    T((-4825.0, -22640.0), 'L=%.1f m / Q=%d / %%1' % (Lm, dn_sb(sbp, True)), 6.5, PSC, 'L', 90)
    cap_pis((-4944.0, -22800.0), 90, '%d SB' % sbm, 'Ø100', 6.0)
    T((-4934.0, -22700.0), 'L=%.1f m / Q=100 / %%1 (TEMEL ALTI EN AZ Ø100)' % Lb, 6.5, PSC, 'L', 90)
    cap_pis((-4873.0, -23000.0), 90, '%d SB' % (sbp + sbm), 'Ø%d' % dn_sb(sbp + sbm, True), 6.0)
    T((-4863.0, -22985.0), 'L=%.1f m / Q=%d / %%1' % (Lc, dn_sb(sbp + sbm, True)), 6.5, PSC, 'L')
    ROGAR_PLAN(R1, 25, 'MTY-ROGAR'); ROGAR_PLAN(PB, 30, 'MTY-ROGAR')
    T(R1, 'R1', 12, 'MTY-ROGAR', 'MC'); T(PB, 'PB', 13, 'MTY-ROGAR', 'MC')
    node((R1[0], R1[1] + 25.0), 'R1'); node((R1[0], R1[1] - 25.0), 'R1')
    node((PB[0], PB[1] + 30.0), 'PB'); node((PB[0], PB[1] - 30.0), 'PB'); node((PB[0], -23230.0), 'SASKI')
    pipe([(R1[0], R1[1] - 25.0), (PB[0], PB[1] + 30.0)], PS, 'T', 9)
    pipe([(PB[0], PB[1] - 30.0), (PB[0], -23230.0)], PS, 'T', 9)
    ARROW((PB[0], -23235.0), -90, PS, 12)
    T((R1[0] - 40, R1[1] + 8), 'R1  50x50 MUAYENE BACASI  h: 0.80 m', 8, 'MTY-ROGAR', 'R')
    T((R1[0] - 40, R1[1] - 4), 'K.K: 29.85  A.K: 29.05 (YAKLAŞIK, SAHADA TEYİT)', 6.5, 'MTY-ROGAR', 'R')
    T((R1[0] + 10, (R1[1] + PB[1]) / 2 - 3), 'L=0.2 m / Q=150 / %1', 6.5, PSC, 'L')
    T((PB[0] - 45, PB[1] + 8), 'PB  60x60 PARSEL BACASI  h: 0.85 m', 8, 'MTY-ROGAR', 'R')
    T((PB[0] - 45, PB[1] - 4), 'K.K: 29.80  A.K: 28.95 (YAKLAŞIK, SAHADA TEYİT)', 6.5, 'MTY-ROGAR', 'R')
    T((PB[0] + 15, -23215.0), 'SASKİ ATIKSU HATTINA (BAĞLANTI KOTU VE YERİ SASKİ\'DEN ALINACAKTIR)', 6.5, 'MTY-ROGAR', 'L')
    # yağmur iniş dipleri
    yagmur_inis()
    for nm, p in YB_PTS.items():
        q = (p[0] - 45.0, p[1]) if p[0] < -5400 else (p[0], p[1] + (40.0 if p[1] > -22500 else -45.0))
        PL([p, q], YL)
        ARROW(q, 180 if p[0] < -5400 else (90 if p[1] > -22500 else -90), YL, 8)
        T((q[0] - (4 if p[0] < -5400 else -4), q[1] + (8 if p[1] > -22500 else -12)), 'YAĞMUR SUYU KANALINA GİDER', 5.5, YC,
          'R' if p[0] < -5400 else 'L')
    T((-5420.0, -23210.0), 'NOT: TEMEL PLANINDA YALNIZCA TAŞIYICI KOLONLAR GÖSTERİLMİŞTİR. BORULAR KOLON VE PERDELERDEN GEÇİRİLMEMİŞ,', 6.5, YZ, 'L')
    T((-5420.0, -23221.0), 'TEMEL KİRİŞİ / RADYE GEÇİŞLERİ STATİK PROJE MÜELLİFİ ONAYI İLE KILIFLI YAPILACAKTIR. YAĞMUR SULARI PİS SU HATTINA BAĞLANMAYACAKTIR.', 6.5, YZ, 'L')
    cad.pop()
    return dict(Lm=Lm, Lb=Lb, Lc=Lc)
