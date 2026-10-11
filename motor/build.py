"""SA PROFİ konut projesi - ROTAŞ sıhhi tesisat + yerden ısıtma. Tüm çizimi kayıt olarak üretir."""
import math, pickle, sys
import cad
from cad import *
from design import *
from arch import FURN

arch = pickle.load(open('/tmp/claude-0/arch_clean.pkl', 'rb'))
PROJE = "SA PROFİ İNŞAAT YAPI MALZEMELERİ TİC. LTD. ŞTİ.'NE AİT KONUT PROJESİ"
YER = 'SAKARYA / ADAPAZARI - ALANDÜZÜ MAH. - PAFTA: G24B16B4B  ADA: 3661  PARSEL: 7'
HEAT = {}   # (blok, kat, daire) -> (res, tot)


def put_arch(sheet, dx=0, dy=0, furn=True, only=None):
    for k, d, l in arch[sheet]:
        if not furn and l in FURN:
            continue
        if only and l not in only:
            continue
        if k == 'L':
            R.append(('L', 'MIMARI', (d[0][0] + dx, d[0][1] + dy), (d[1][0] + dx, d[1][1] + dy)))
        elif k == 'P':
            R.append(('P', 'MIMARI', [(x + dx, y + dy) for x, y in d], False, 0))
        elif k == 'C':
            R.append(('C', 'MIMARI', (d[0] + dx, d[1] + dy), d[2]))
        elif k == 'T':
            R.append(('T', 'MIMARI', (d[0][0] + dx, d[0][1] + dy), d[1], d[2], 0, 'L'))


def qww(sb):
    return 0.5 * math.sqrt(sb)


def dia_col(sb):
    q = qww(sb)
    return 100 if q <= 2.9 else 125 if q <= 5.2 else 150 if q <= 8.4 else 200


def dn_ts(yb):
    for lim, dn in ((2.25, 20), (7.84, 25), (19.36, 32), (46.24, 40), (108.4, 50), (256, 63), (784, 75)):
        if yb <= lim:
            return dn
    return 90


def kolon_pts():
    """zemin koordinatında (no, PK, MK)"""
    out = []
    for no in range(1, 8):
        tip, ops, mi = DAIRES[no]
        cad.push(MOVE(0, 0))
        for op in ops:
            cad.push(op)
        out.append((no, cad.P(TYPES[tip]['PK']), cad.P(TYPES[tip]['MK'])))
        for _ in range(len(ops) + 1):
            cad.pop()
    return out


KOL = kolon_pts()
YIB = [(79241, -8806), (81574, -8806), (82529, -8806), (80609, -9181),
       (79241, -10321), (80196, -10321), (81574, -10321), (82529, -10321)]
SB_PK = 3 * (SB['WC'] + SB['LV'] + SB['DUS'] + SB['CM'] + SB['YS'])
SB_MK = 3 * (SB['EV'] + SB['BM'])
YB_D = sum(YB.values())
YB_BOD = 2 * (YB['WC'] + YB['LV']) + YB['EV']
SB_BOD = 2 * (SB['WC'] + SB['LV']) + SB['EV']


# ================================================================== çerçeve
def frame(x0, y0, x1, y1, title, sub='', olc='1/50'):
    RECT(x0, y0, x1, y1, 'MTY-PAFTA')
    RECT(x0 + 40, y0 + 40, x1 - 40, y1 - 40, 'MTY-PAFTA')
    T((x0 + 150, y0 + 110), title, 40, YZ, 'L')
    if sub:
        T((x0 + 150, y0 + 70), sub, 18, YZ, 'L')
    bx0, by0, bx1, by1 = x1 - 1450, y0 + 40, x1 - 40, y0 + 330
    RECT(bx0, by0, bx1, by1, 'MTY-PAFTA')
    L((bx0, by0 + 210), (bx1, by0 + 210), 'MTY-PAFTA')
    L((bx0, by0 + 120), (bx1, by0 + 120), 'MTY-PAFTA')
    T((bx0 + 20, by0 + 240), 'ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK.', 26, YZ, 'L')
    T((bx0 + 20, by0 + 150), PROJE[:70], 15, YZ, 'L')
    T((bx0 + 20, by0 + 80), 'MEKANİK TESİSAT PROJESİ', 18, YZ, 'L')
    T((bx0 + 20, by0 + 25), 'PROJE SORUMLUSU : Mak. Müh. Bayram GENÇ', 15, YZ, 'L')
    T((bx1 - 20, by0 + 25), 'ÖLÇEK : ' + olc, 15, YZ, 'R')


# ================================================================== kat planları
def sihhi_kat(block_off, fl):
    key, name, fdx, ffac, kat = fl
    base = {'Z': 0, '1': 7, '2': 14}[key]
    for no in range(1, 8):
        tip, n = daire_tf(no, fdx, block_off)
        sihhi_daire(no, tip, base + no)
        pop_n(n)
        corridor(no, base + no, fdx, block_off)
    sayac_grubu(fdx, block_off, 'SAYAÇ KOLL. DN40 / %.2f YB' % (7 * YB_D))
    # kolon çıkışı ve yağmur inişleri
    cad.push(MOVE(fdx + block_off[0], block_off[1]))
    for p in YIB:
        YB_PLAN(p, 7)
        T((p[0], p[1] + 14), 'Y.İ.B. Ø100', 8, 'MTY-YAGMUR-BORUSU-CAP', 'C')
    cad.pop()


def isitma_kat(bk, block_off, fl):
    key, name, fdx, ffac, kat = fl
    base = {'Z': 0, '1': 7, '2': 14}[key]
    z = 0
    for no in range(1, 8):
        tip, n = daire_tf(no, fdx, (block_off[0], block_off[1] + HEAT_DY))
        res, tot, z = isitma_daire(no, tip, ffac, z, kat)
        pop_n(n)
        HEAT[(bk, key, base + no)] = (tip, res, tot)


# ================================================================== temel / bodrum
def temel(dx, dy, bodrum):
    """dx,dy: zemin koordinatından bu plana öteleme."""
    cad.push(MOVE(dx, dy))
    lay = PT if bodrum else PS
    xs = []
    for no, pk, mk in KOL:
        for c, nm, sb in ((pk, 'PK-%d' % no, SB_PK), (mk, 'MK-%d' % no, SB_MK)):
            KOLON(c, 6.5, 'MTY-PISSU-KOLON')
            T((c[0] + 12, c[1] + 10), nm, TH, 'MTY-PISSU-KOLONNO', 'L')
            PL([c, (c[0], YM)], lay)
            lab_on([c, (c[0], YM)], 'Ø100', 'MTY-PISSU-CAP', off=10, minlen=80)
            TEMIZLEME_KAPAGI((c[0], c[1] + (-14 if c[1] > YM else 14)), 0.8, lay)
            xs.append((c[0], sb))
    if bodrum:
        xs.append((75060 + 4450, SB_BOD))
    xs.sort()
    XR = 82780.0
    pts = [x for x, _ in xs] + [XR]
    acc = 0
    for i, (x, sb) in enumerate(xs):
        acc += sb
        a, b = x, pts[i + 1]
        PL([(a, YM), (b, YM)], lay)
        if b - a > 150:
            T(((a + b) / 2, YM + 8), 'Ø%d / %.1f SB' % (dia_col(acc), acc), 8, 'MTY-PISSU-CAP', 'C')
            T(((a + b) / 2, YM - 16), '%%2', 8, 'MTY-PISSU-CAP', 'C')
    ARROW((XR - 30, YM), 0, lay, 12)
    # rögarlar
    R1 = (XR + 40, YM); R2 = (XR + 40, -10560.0)
    ROGAR_PLAN(R1, 35); ROGAR_PLAN(R2, 35)
    PL([(XR, YM), (R1[0] - 35, YM)], PS)
    PL([(R1[0], R1[1] - 35), (R2[0], R2[1] + 35)], PS)
    T((R1[0] + 50, R1[1] + 20), 'R1  60x60', 12, 'MTY-ROGAR', 'L')
    T((R1[0] + 50, R1[1] + 2), 'h: -110 cm', 10, 'MTY-ROGAR', 'L')
    T((R2[0] + 50, R2[1] + 20), 'R2  60x60', 12, 'MTY-ROGAR', 'L')
    T((R2[0] + 50, R2[1] + 2), 'h: -140 cm', 10, 'MTY-ROGAR', 'L')
    T((R1[0] + 10, (R1[1] + R2[1]) / 2), 'L=%d / Q=150' % (R1[1] - R2[1] - 70), 10, 'MTY-PISSU-CAP', 'L', 90)
    PL([(R2[0], R2[1] - 35), (R2[0], R2[1] - 160)], PS)
    ARROW((R2[0], R2[1] - 165), -90, PS, 15)
    T((R2[0] + 20, R2[1] - 150), 'PARSEL BACASINA (PB) - VAZİYET PLANINA BAKINIZ', 10, 'MTY-ROGAR', 'L')
    T((79400, YM + 20), ('BODRUM TAVANINDAN ASILI PİS SU TOPLAMA HATTI (PVC) %2 EĞİMLİ' if bodrum else
                         'TEMEL ALTINDAN PİS SU TOPLAMA HATTI (PVC) %2 EĞİMLİ'), 10, 'MTY-PISSU-CAP', 'L')
    # yağmur hattı (bina çevresi)
    YN, YS_, XE = -8730.0, -10420.0, 82650.0
    for p in YIB:
        YB_PLAN(p, 7)
        if p[1] > -9600:
            PL([p, (p[0], YN)], 'MTY-YAGMUR-BORUSU')
        else:
            PL([p, (p[0], YS_)], 'MTY-YAGMUR-BORUSU')
    PL([(79241, YN), (XE, YN), (XE, YS_), (79241, YS_)], 'MTY-YAGMUR-BORUSU')
    for p in ((XE, YN), (XE, YS_)):
        ROGAR_PLAN(p, 30, 'MTY-YAGMUR-BORUSU')
    T((XE + 45, YN + 5), 'YR1 50x50', 11, 'MTY-YAGMUR-BORUSU-CAP', 'L')
    T((XE + 45, YS_ + 5), 'YR2 50x50', 11, 'MTY-YAGMUR-BORUSU-CAP', 'L')
    T((80400, YN + 10), 'Ø150 PVC YAĞMUR SUYU TOPLAMA HATTI', 10, 'MTY-YAGMUR-BORUSU-CAP', 'C')
    T((80400, YS_ - 22), 'Ø150 PVC YAĞMUR SUYU TOPLAMA HATTI', 10, 'MTY-YAGMUR-BORUSU-CAP', 'C')
    PL([(XE, YS_ - 30), (XE, YS_ - 260)], 'MTY-YAGMUR-BORUSU')
    ARROW((XE, YS_ - 265), -90, 'MTY-YAGMUR-BORUSU', 15)
    T((XE - 15, YS_ - 200), 'Ø200 YAĞMUR SUYU KANALINA GİDER', 10, 'MTY-YAGMUR-BORUSU-CAP', 'R')
    # şebeke girişi + ana sayaç + depo besleme kolonu
    xs_ = DBK[0]
    PL([(xs_, -10650), (xs_, DBK[1])], CS)
    ARROW((xs_, -10450), 90, CS, 12)
    T((xs_ - 15, -10620), 'ŞEBEKEDEN Ø32', 10, 'MTY-TEMIZSU-CAP', 'R')
    y = -10380
    for f, s in ((VANA, 'KÜRESEL VANA'), (PISLIK_TUTUCU, 'PİSLİK TUTUCU'), (SAYAC, 'ANA SU SAYACI'),
                 (CEKVALF, 'ÇEK VALF'), (VANA, 'KÜRESEL VANA')):
        f((xs_, y), 1.0, 90)
        T((xs_ + 15, y - 4), s, 8, VN, 'L')
        y += 45
    KOLON(DBK, 6, CS, 'temiz'); KOLON(ADK, 6, CS, 'temiz')
    T((DBK[0] - 12, DBK[1] + 14), 'DBK DN40 (ÇATI DEPOLARINA)', 9, 'MTY-TEMIZSU-CAP', 'R')
    T((ADK[0] + 12, ADK[1] + 14), 'ADK DN50 (DEPODAN İNİŞ)', 9, 'MTY-TEMIZSU-CAP', 'L')
    cad.pop()


def bodrum_tesisat(dx):
    """A blok bodrum ortak ıslak hacimleri + pis su terfi (bodrum koordinatı)."""
    WC((74833, -10085), 'E', TF); LAVABO((74833, -10025), 'E', TF)
    WC((74833, -10175), 'E', TF); LAVABO((74925, -10255), 'N', TF)
    EVIYE((74814, -9900), 'E', TF)
    pc = (75060, -10070)
    RECT(pc[0] - 30, pc[1] - 30, pc[0] + 30, pc[1] + 30, 'MTY-CIHAZ')
    RECT(pc[0] - 24, pc[1] - 24, pc[0] + 24, pc[1] + 24, 'MTY-CIHAZ')
    POMPA(pc, 9, 90)
    T((pc[0] + 40, pc[1] + 10), 'PİS SU TERFİ ÇUKURU 60x60x100', 9, CD, 'L')
    T((pc[0] + 40, pc[1] - 4), 'DALGIÇ POMPA Q=2 l/s H=6 mSS', 9, CD, 'L')
    for pl in ([(74870, -10085), (74990, -10085), (75030, -10070)], [(74855, -10025), (74990, -10050), (75030, -10060)],
               [(74870, -10175), (74990, -10175), (75040, -10100)], [(74925, -10220), (74990, -10200), (75045, -10100)],
               [(74840, -9900), (75000, -9900), (75050, -10040)]):
        PL(pl, PS)
    lab_on([(74840, -9900), (75000, -9900)], 'Ø50', 'MTY-PISSU-CAP', off=6)
    lab_on([(74870, -10085), (74990, -10085)], 'Ø100', 'MTY-PISSU-CAP', off=6)
    PL([(pc[0], pc[1] + 30), (pc[0], YM)], PT)
    CEKVALF((pc[0], pc[1] + 60), 1, 90); VANA((pc[0], pc[1] + 85), 1, 90)
    T((pc[0] + 12, -9800), 'Ø50 PE BASMA HATTI (TAVANA)', 9, 'MTY-PISSU-CAP', 'L', 90)
    # temiz su: ADK alt ucu -> ortak alan sayacı -> ıslak hacimler
    ax, ay = ADK[0] + dx, ADK[1]
    PL([(ax, ay), (ax, -9600), (75010, -9600), (75010, -10190)], CS)
    SAYAC((75400, -9600), 1, 0); VANA((75440, -9600), 1, 0)
    T((75400, -9580), 'ORTAK ALAN SAYACI', 9, VN, 'C')
    for y, x in ((-9900, 74870), (-10040, 74870), (-10175, 74870)):
        PL([(75010, y), (x, y)], CS)
    PL([(75010, -10220), (74925, -10220)], CS)
    T((75600, -9590), 'DN20 / %.2f YB' % YB_BOD, 9, 'MTY-YUK-BIRIMI', 'L')


# ================================================================== çatı
DEPOTS = [(94760, -9456, 94970, -9352), (95125, -9456, 95330, -9352),
          (94760, -9770, 94970, -9665), (95125, -9770, 95330, -9665)]


def cati(dx, dy):
    """dx,dy: zemin -> çatı planı ötelemesi (çatı = zemin + 13350 + blok)"""
    cad.push(MOVE(dx, dy))
    for p in YIB:
        YB_PLAN(p, 8)
        T((p[0], p[1] + (18 if p[1] > YM else -30)), 'YAĞMUR İNİŞİ Ø100', 10, 'MTY-YAGMUR-BORUSU-CAP', 'C')
    T((80875, -8700), 'YAĞMUR OLUĞU (YARIM DAİRE KESİTLİ, %0.5 EĞİMLİ)', 12, 'MTY-YAGMUR-BORUSU-CAP', 'C')
    T((80875, -10450), 'YAĞMUR OLUĞU (YARIM DAİRE KESİTLİ, %0.5 EĞİMLİ)', 12, 'MTY-YAGMUR-BORUSU-CAP', 'C')
    for no, pk, mk in KOL:
        for c in (pk, mk):
            C(c, 7, PS); C(c, 11, PS)
            T((c[0], c[1] - 24), 'HAVALIK Ø100', 8, 'MTY-PISSU-CAP', 'C')
    cad.pop()
    # depolar (çatı koordinatı) + hidrofor
    cad.push(MOVE(dx - 13350 + 13350 - 13350 + 13350 - 13350, dy))   # = dx - 13350
    cad.pop()
    cad.push(MOVE(dx - 13350, dy))
    for d in DEPOTS:
        RECT(d[0] + 6, d[1] + 6, d[2] - 6, d[3] - 6, 'RAST-TEM-SU DEPOSU')
    yc = -9560.0
    hx = 95045.0
    for d in DEPOTS:
        cx = (d[0] + d[2]) / 2
        y = d[1] if d[1] > -9600 else d[3]
        PL([(cx, y), (cx, yc)], CS)
        VANA((cx, (y + yc) / 2), 0.9, 90)
    PL([(94865, yc), (95228, yc)], CS)
    # hidrofor
    POMPA((hx - 20, yc - 40), 10, -90); POMPA((hx + 20, yc - 40), 10, -90)
    PL([(hx - 20, yc), (hx - 20, yc - 30)], CS); PL([(hx + 20, yc), (hx + 20, yc - 30)], CS)
    PL([(hx - 20, yc - 50), (hx - 20, yc - 70), (hx + 20, yc - 70), (hx + 20, yc - 50)], CS)
    MEMBRANLI_TANK((hx + 55, yc - 80), 26, 50)
    KONT = (hx - 70, yc - 60)
    RECT(KONT[0] - 15, KONT[1] - 12, KONT[0] + 15, KONT[1] + 12, CD)
    T((hx, yc - 115), 'PAKET HİDROFOR', 10, CD, 'C')
    T((hx, yc - 129), 'Q=9 m³/h  H=30 mSS  (1 ASİL + 1 YEDEK)', 8, CD, 'C')
    a = ADK; b = DBK
    PL([(hx, yc - 70), (hx, yc - 150), (a[0] + 13350, yc - 150), (a[0] + 13350, a[1])], CS)
    KOLON((a[0] + 13350, a[1]), 6, CS, 'temiz')
    T((a[0] + 13350 + 12, a[1] - 20), 'ADK DN50 (KATLARA İNİŞ)', 9, 'MTY-TEMIZSU-CAP', 'L')
    KOLON((b[0] + 13350, b[1]), 6, CS, 'temiz')
    PL([(b[0] + 13350, b[1]), (b[0] + 13350, -9300), (95380, -9300), (95380, -9820), (94865, -9820)], CS)
    for d in DEPOTS:
        cx = (d[0] + d[2]) / 2
        if d[1] > -9600:
            PL([(cx, -9300), (cx, d[3] - 6)], CS); SAMANDIRALI_VANA((cx, d[3] - 20), 0.8)
        else:
            PL([(cx, -9820), (cx, d[1] + 6)], CS); SAMANDIRALI_VANA((cx, d[1] + 20), 0.8)
    T((b[0] + 13350 - 12, -9320), 'DBK DN40 DEPO BESLEME', 9, 'MTY-TEMIZSU-CAP', 'R')
    T((95045, -9250), 'KULLANMA SUYU DEPOLARI 4 x 2.00 m³ = 8.00 m³ (PE, KAPAKLI, HAVALIKLI)', 12, 'RAST-TEM-SU DEPOSU', 'C')
    T((95045, -9870), 'DEPO TAŞMA VE BOŞALTMALARI EN YAKIN YAĞMUR İNİŞİNE BAĞLANACAKTIR', 9, 'RAST-TEM-SU DEPOSU', 'C')
    cad.pop()


# ================================================================== vaziyet (1 birim = 4 cm)
def vaziyet():
    s = 'MTY-ROGAR'
    pb = (73300, -10175)
    nets = [[(73394, -9800), (73440, -9800), (73440, -10100), (pb[0] + 10, pb[1] + 10)],
            [(72215, -9830), (72215, -10140), (pb[0] - 10, -10140), (pb[0] - 10, pb[1] + 10)]]
    for i, n in enumerate(nets):
        PL(n, PS)
        for j, p in enumerate(n[1:-1]):
            ROGAR_PLAN(p, 9)
            T((p[0] + 14, p[1] + 6), 'R%d' % (j + 1 + 2 * i), 8, s, 'L')
    ROGAR_PLAN(pb, 12)
    T((pb[0] + 16, pb[1] - 4), 'PB (PARSEL BACASI) 100x100', 8, s, 'L')
    PL([(pb[0], pb[1] - 12), (pb[0], -10290)], PS)
    ARROW((pb[0], -10295), -90, PS, 8)
    T((pb[0] + 6, -10280), 'Ø200 BELEDİYE ATIKSU KANALINA', 7, s, 'L')
    yn = [[(73420, -9560), (73490, -9560), (73490, -10230), (73420, -10230)],
          [(72180, -9830), (72140, -9830), (72140, -10230), (73420, -10230)]]
    for n in yn:
        PL(n, 'MTY-YAGMUR-BORUSU')
    ROGAR_PLAN((73420, -10230), 8, 'MTY-YAGMUR-BORUSU')
    PL([(73420, -10238), (73420, -10300)], 'MTY-YAGMUR-BORUSU')
    ARROW((73420, -10305), -90, 'MTY-YAGMUR-BORUSU', 8)
    T((73428, -10318), 'YAĞMUR SUYU KANALINA GİDER', 7, 'MTY-YAGMUR-BORUSU-CAP', 'L')
    T((71250, -10560), 'NOT: PİS SU VE YAĞMUR SUYU HATLARI AYRI AYRI BELEDİYE KANALLARINA BAĞLANACAKTIR.', 14, YZ, 'L')


# ================================================================== kolon şeması (sıhhi)
def sihhi_sema(ox, oy, bodrum, blok):
    W = 1000
    lv = {'B': oy + 450, 'Z': oy + 900, '1': oy + 1350, '2': oy + 1800, 'C': oy + 2250}
    names = [('B', 'BODRUM KAT'), ('Z', 'ZEMİN KAT'), ('1', '1. KAT'), ('2', '2. KAT'), ('C', 'ÇATI')]
    for k, nm in names:
        if k == 'B' and not bodrum:
            continue
        L((ox + 200, lv[k]), (ox + 7900, lv[k]), 'MTY-SEMA')
        T((ox + 220, lv[k] + 12), nm, 18, YZ, 'L')
    T((ox + 4000, oy + 2900), '%s BLOK SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI' % blok, 40, YZ, 'C')
    xa, xd = ox + 560, ox + 500
    # depolar + hidrofor
    ty = lv['C'] + 150
    for i in range(4):
        x0 = ox + 300 + i * 260
        RECT(x0, ty, x0 + 220, ty + 140, 'RAST-TEM-SU DEPOSU')
        T((x0 + 110, ty + 95), 'DEPO %d' % (i + 1), 12, 'RAST-TEM-SU DEPOSU', 'C')
        T((x0 + 110, ty + 75), 'V=2.00 m³', 10, 'RAST-TEM-SU DEPOSU', 'C')
        PL([(x0 + 110, ty), (x0 + 110, ty - 40)], CS)
        VANA((x0 + 110, ty - 20), 1, 90)
        PL([(x0 + 30, ty + 140), (x0 + 30, ty + 165)], CS); HAVALIK_SAPKA((x0 + 30, ty + 165), 0.8, CS)
        PL([(x0 + 200, ty + 120), (x0 + 240, ty + 120), (x0 + 240, ty - 60)], 'MTY-YAGMUR-BORUSU')
        SAMANDIRALI_VANA((x0 + 70, ty + 120), 1)
    T((ox + 1400, ty - 70), 'TAŞMA / BOŞALTMA YAĞMUR İNİŞİNE', 9, 'MTY-YAGMUR-BORUSU-CAP', 'L')
    PL([(ox + 410, ty - 40), (ox + 1190, ty - 40)], CS)
    hx, hy = ox + 1300, ty - 40
    PL([(ox + 1190, ty - 40), (hx - 30, hy)], CS)
    POMPA((hx, hy + 20), 12, 0); POMPA((hx, hy - 20), 12, 0)
    PL([(hx - 30, hy + 20), (hx - 30, hy - 20)], CS); PL([(hx + 30, hy + 20), (hx + 30, hy - 20)], CS)
    for yy in (hy + 20, hy - 20):
        L((hx - 30, yy), (hx - 12, yy), CS); L((hx + 12, yy), (hx + 30, yy), CS)
    MEMBRANLI_TANK((hx + 80, hy), 30, 60)
    L((hx + 30, hy), (hx + 65, hy), CS)
    MANOMETRE((hx + 45, hy), 1)
    T((hx, hy - 55), 'PAKET HİDROFOR Q=9 m³/h H=30 mSS', 10, CD, 'C')
    PL([(hx + 30, hy), (hx + 30, hy - 80), (xa, hy - 80), (xa, lv['B'] + 40 if bodrum else lv['Z'] + 60)], CS)
    # DBK
    PL([(xd, (lv['B'] if bodrum else lv['Z']) - 200), (xd, ty + 160), (ox + 1200, ty + 160)], CS)
    for i in range(4):
        x0 = ox + 300 + i * 260
        L((x0 + 70, ty + 160), (x0 + 70, ty + 125), CS)
    yb = (lv['B'] if bodrum else lv['Z']) - 180
    for j, (f, s) in enumerate(((VANA, 'KÜRESEL VANA'), (PISLIK_TUTUCU, 'PİSLİK TUTUCU'), (SAYAC, 'ANA SAYAÇ'),
                                (CEKVALF, 'ÇEK VALF'))):
        f((xd, yb + j * 30), 1, 90)
        T((xd - 14, yb + j * 30 - 3), s, 8, VN, 'R')
    ARROW((xd, yb - 15), 90, CS, 12)
    T((xd - 14, yb - 40), 'ŞEBEKEDEN Ø32', 10, 'MTY-TEMIZSU-CAP', 'R')
    T((xd - 10, lv['Z'] + 220), 'DBK DN40', 10, 'MTY-TEMIZSU-CAP', 'R', 90)
    # ADK segment etiketleri
    tot = 21 * YB_D + (YB_BOD if bodrum else 0)
    segs = [('2', 21 * YB_D), ('1', 14 * YB_D), ('Z', 7 * YB_D)]
    T((xa + 12, lv['C'] - 150), 'ADK DN%d / %.2f YB' % (dn_ts(tot), tot), 10, 'MTY-YUK-BIRIMI', 'L', 90)
    for k, v in segs[1:]:
        y = (lv[k] + lv[{'1': '2', 'Z': '1'}[k]]) / 2
        T((xa + 12, y - 150), 'DN%d / %.2f YB' % (dn_ts(v + (YB_BOD if bodrum else 0)), v + (YB_BOD if bodrum else 0)),
          10, 'MTY-YUK-BIRIMI', 'L', 90)
    # katlar
    for k, base in (('Z', 0), ('1', 7), ('2', 14)):
        yk = lv[k] + 40
        L((xa, yk), (ox + 600 + 7 * W - 300, yk), CS)
        for i in range(7):
            no = base + i + 1
            cx = ox + 600 + i * W
            dx_ = cx + 60
            SAYAC((dx_, yk + 25), 0.9, 90); VANA((dx_, yk + 55), 0.8, 90)
            PL([(dx_, yk), (dx_, yk + 90), (dx_ + 400, yk + 90)], CS)
            T((dx_ + 8, yk + 30), 'DN25 / %.2f YB' % YB_D, 8, 'MTY-YUK-BIRIMI', 'L')
            T((cx + 230, yk + 330), 'DAİRE %d' % no, 14, YZ, 'C')
            # armatürler (temiz)
            items = [('KOMBİ', 0.0), ('LV', YB['LV']), ('DUŞ', YB['DUS']), ('EVİYE', YB['EV']),
                     ('WC', YB['WC']), ('ÇM', YB['CM']), ('BM', YB['BM'])]
            hotx = []
            for j, (nm, yb_) in enumerate(items):
                fx = dx_ + 40 + j * 55
                L((fx, yk + 90), (fx, yk + 150), CS)
                if nm == 'KOMBİ':
                    RRECT(fx - 18, yk + 150, fx + 18, yk + 210, 3, CD)
                    C((fx, yk + 180), 7, CD)
                    T((fx, yk + 218), 'KOMBİ', 8, CD, 'C')
                    T((fx, yk + 230), '24kW', 7, CD, 'C')
                else:
                    MUSLUK = None
                    C((fx, yk + 156), 5, CS)
                    T((fx, yk + 170), nm, 7, TF, 'C', 90 if False else 0)
                    T((fx, yk + 70), '%.1f' % yb_, 7, 'MTY-YUK-BIRIMI', 'C')
                    if nm in ('LV', 'DUŞ', 'EVİYE'):
                        hotx.append(fx)
            if hotx:
                PL([(dx_ + 40 + 18, yk + 160), (hotx[-1] + 8, yk + 160)], CH)
                for fx in hotx:
                    L((fx + 8, yk + 160), (fx + 8, yk + 152), CH)
                    C((fx + 8, yk + 148), 4, CH)
        # pis su kolonları
    for i in range(7):
        cx = ox + 600 + i * W
        for kx, sbk, nmk, items in ((cx + 520, SB_PK, 'PK', [('WC', 100, SB['WC']), ('LV', 50, SB['LV']), ('DUŞ', 50, SB['DUS']),
                                                               ('ÇM', 50, SB['CM']), ('YS', 50, SB['YS'])]),
                                    (cx + 830, SB_MK, 'MK', [('EV', 50, SB['EV']), ('BM', 50, SB['BM'])])):
            ytop = lv['C'] + 90
            ybot = (lv['Z'] - 120) if True else 0
            PL([(kx, ybot), (kx, ytop)], PS)
            HAVALIK_SAPKA((kx, ytop), 1.2)
            TEMIZLEME_KAPAGI((kx, lv['Z'] - 60), 1)
            T((kx, ytop + 30), '%s-%d' % (nmk, i + 1), 12, 'MTY-PISSU-KOLONNO', 'C')
            per = sum(it[2] for it in items)
            for kk, f in (('2', 1), ('1', 2), ('Z', 3)):
                yb_ = lv[kk] + 25
                for j, (nm, d, sb) in enumerate(items):
                    fx = kx + 22 + j * 30
                    PL([(kx, yb_ - 10), (fx, yb_), (fx, yb_ + 25)], PS)
                    T((fx + 3, yb_ + 30), '%s Ø%d %.1fSB' % (nm, d, sb), 6.5, 'MTY-PISSU-CAP', 'L', 90)
                T((kx - 8, lv[kk] - 200), 'Ø100 / %.1f SB' % (per * f), 9, 'MTY-PISSU-CAP', 'L', 90)
    # toplama hattı
    yc = lv['Z'] - 120
    acc = SB_BOD if bodrum else 0
    PL([(ox + 600 + 520, yc), (ox + 7850, yc)], PT if bodrum else PS)
    for i in range(7):
        acc += SB_PK + SB_MK
        x = ox + 600 + i * W + 830
        x2 = ox + 600 + (i + 1) * W + 520 if i < 6 else ox + 7700
        T(((x + x2) / 2, yc + 8), 'Ø%d / %.1f SB' % (dia_col(acc), acc), 9, 'MTY-PISSU-CAP', 'C')
    ROGAR_PLAN((ox + 7850, yc - 40), 35)
    PL([(ox + 7850, yc), (ox + 7850, yc - 5)], PS)
    T((ox + 7850, yc - 95), 'R1 -> R2 -> PB', 12, 'MTY-ROGAR', 'C')
    if bodrum:
        T((ox + 1200, yc + 14), 'BODRUM TAVANINDAN ASKILI TOPLAMA HATTI', 10, 'MTY-PISSU-CAP', 'L')
        # bodrum ortak hacimler
        yk = lv['B'] + 40
        PL([(xa, lv['B'] + 40), (xa + 300, yk)], CS)
        SAYAC((xa + 120, yk), 0.9, 0); VANA((xa + 70, yk), 0.8, 0)
        for j, nm in enumerate(('WC', 'LV', 'WC', 'LV', 'EVİYE')):
            fx = xa + 160 + j * 30
            L((fx, yk), (fx, yk + 40), CS); C((fx, yk + 45), 4, CS)
            T((fx, yk + 55), nm, 7, TF, 'L', 90)
        T((xa + 160, yk - 18), 'ORTAK ALAN DN20 / %.2f YB' % YB_BOD, 9, 'MTY-YUK-BIRIMI', 'L')
        px = ox + 1000
        RECT(px - 40, lv['B'] - 120, px + 40, lv['B'] - 20, CD)
        DALGIC_POMPA((px, lv['B'] - 110), 1.2)
        PL([(px, lv['B'] - 74), (px, yc)], PT)
        CEKVALF((px, lv['B'] + 40), 1, 90); VANA((px, lv['B'] + 70), 1, 90)
        T((px + 50, lv['B'] - 80), 'PİS SU TERFİ ÇUKURU + DALGIÇ POMPA', 9, CD, 'L')
        T((px + 50, lv['B'] - 95), 'Ø50 BASMA HATTI (%.1f SB)' % SB_BOD, 9, CD, 'L')


# ================================================================== yerden ısıtma kolon şeması
def isitma_sema(ox, oy, blok):
    T((ox + 4000, oy + 2900), '%s BLOK YERDEN ISITMA KOLON ŞEMASI' % blok, 40, YZ, 'C')
    rows = {'Z': oy + 420, '1': oy + 1230, '2': oy + 2040}
    for k, nm in (('Z', 'ZEMİN KAT'), ('1', '1. KAT'), ('2', '2. KAT')):
        y = rows[k]
        L((ox + 200, y), (ox + 7900, y), 'MTY-SEMA')
        T((ox + 220, y + 12), nm, 18, YZ, 'L')
        base = {'Z': 0, '1': 7, '2': 14}[k]
        for i in range(7):
            no = base + i + 1
            tip, res, tot = HEAT[(blok, k, no)]
            cx = ox + 500 + i * 1050
            ky = y + 120
            RRECT(cx, ky, cx + 70, ky + 110, 4, CD)
            C((cx + 35, ky + 70), 14, CD)
            T((cx + 35, ky - 18), 'H. KOMBİ 24KW', 10, CD, 'C')
            T((cx + 35, ky + 150), 'DAİRE %d' % no, 14, YZ, 'C')
            n = len(res)
            kx0, kx1 = cx + 170, cx + 170 + n * 100
            L((kx0, ky + 60), (kx1, ky + 60), 'MTY-ISITMA-GIDIS-BORU')
            L((kx0, ky + 30), (kx1, ky + 30), 'MTY-ISITMA-DONUS-BORU')
            RECT(kx0 - 10, ky + 20, kx1 + 10, ky + 70, 'MTY-KOLLETOR')
            PL([(cx + 70, ky + 80), (kx0 - 10, ky + 80), (kx0 - 10, ky + 60)], 'MTY-ISITMA-GIDIS-BORU')
            PL([(cx + 70, ky + 20), (kx0 - 20, ky + 20), (kx0 - 20, ky + 30), (kx0 - 10, ky + 30)], 'MTY-ISITMA-DONUS-BORU')
            T((cx + 110, ky + 88), '%.1fW-DN20' % tot, 9, 'STM-ISITMA-CAP', 'L')
            VANA((cx + 100, ky + 80), 0.8); VANA((cx + 100, ky + 20), 0.8)
            for j, d in enumerate(res):
                px = kx0 + 50 + j * 100
                L((px - 6, ky + 60), (px - 6, ky + 420), 'MTY-PEX-BORU')
                L((px + 6, ky + 30), (px + 6, ky + 420), 'MTY-PEX-BORU')
                L((px - 6, ky + 420), (px + 6, ky + 420), 'MTY-PEX-BORU')
                C((px - 6, ky + 60), 3, 'MTY-KOLLETOR'); C((px + 6, ky + 30), 3, 'MTY-KOLLETOR')
                T((px, ky + 5), 'P%d' % (j + 1), 9, 'MTY-KOLLETOR', 'C')
                lines = ['ISIKAYBI %d' % d['no'], '%.1fW' % d['W'], '%.2f m' % d['L'], d['zl'],
                         '24°C' if 'BANYO' in d['room'] else '20°C', 'PEX BORU 16x2.0']
                for m, s in enumerate(lines):
                    T((px - 12 - 0 * m, ky + 430 + m * 0), '', 1, YZ)
                T((px - 14, ky + 100), '  /  '.join(lines[:4]), 8, 'MTY-ISIKAYBIMAHAL', 'L', 90)
                T((px + 22, ky + 100), '%s  /  %s  /  %.1fW-DN15' % (lines[4], lines[5], d['W']), 8, 'STM-ISITMA-CAP', 'L', 90)


# ================================================================== tablolar / lejant / notlar
def table(x, y, cols, rows, title, h=11):
    """cols: [(başlık, genişlik)], rows: [[...]] ; (x,y): sol üst"""
    rh = h * 2.2
    W = sum(c[1] for c in cols)
    T((x + W / 2, y + 12), title, h * 1.4, 'MTY-HESAP', 'C')
    allr = [[c[0] for c in cols]] + rows
    for i, r in enumerate(allr):
        yy = y - i * rh
        L((x, yy), (x + W, yy), 'MTY-HESAP')
        cx = x
        for j, (c, w) in enumerate(cols):
            T((cx + 8, yy - rh * 0.68), str(r[j]), h * (0.9 if i == 0 else 0.85), 'MTY-HESAP', 'L')
            cx += w
    yb = y - len(allr) * rh
    L((x, yb), (x + W, yb), 'MTY-HESAP')
    cx = x
    for c, w in cols + [('', 0)]:
        L((cx, y), (cx, yb), 'MTY-HESAP')
        cx += w
    return yb


def lejant(x, y):
    T((x, y + 20), 'LEJANT', 24, YZ, 'L')
    items = [
        (lambda p: L((p[0] - 40, p[1]), (p[0] + 40, p[1]), CS), 'SOĞUK SU BORUSU (PPRC PN20)'),
        (lambda p: L((p[0] - 40, p[1]), (p[0] + 40, p[1]), CH), 'SICAK KULLANMA SUYU BORUSU (PPRC PN20)'),
        (lambda p: L((p[0] - 40, p[1]), (p[0] + 40, p[1]), PS), 'PİS SU BORUSU (PVC, ÇOK KATMANLI)'),
        (lambda p: L((p[0] - 40, p[1]), (p[0] + 40, p[1]), PT), 'TAVANDAN ASKILI PİS SU BORUSU'),
        (lambda p: L((p[0] - 40, p[1]), (p[0] + 40, p[1]), 'MTY-YAGMUR-BORUSU'), 'YAĞMUR SUYU BORUSU (PVC)'),
        (lambda p: KOLON(p, 7, 'MTY-PISSU-KOLON'), 'PİS SU KOLONU (PK BANYO / MK MUTFAK)'),
        (lambda p: KOLON(p, 7, CS, 'temiz'), 'TEMİZ SU KOLONU (ADK / DBK)'),
        (lambda p: YB_PLAN(p, 8), 'YAĞMUR İNİŞ BORUSU'),
        (lambda p: VANA(p, 1.4), 'KÜRESEL VANA'),
        (lambda p: CEKVALF(p, 1.4), 'ÇEK VALF'),
        (lambda p: PISLIK_TUTUCU(p, 1.4), 'PİSLİK TUTUCU'),
        (lambda p: SAYAC(p, 1.4), 'SU SAYACI'),
        (lambda p: SAMANDIRALI_VANA((p[0], p[1] + 10), 1.0), 'ŞAMANDIRALI VANA'),
        (lambda p: POMPA(p, 12), 'POMPA'),
        (lambda p: MEMBRANLI_TANK(p, 18, 34), 'MEMBRANLI GENLEŞME TANKI'),
        (lambda p: ROGAR_PLAN(p, 18), 'RÖGAR / PARSEL BACASI'),
        (lambda p: TEMIZLEME_KAPAGI(p, 1.6), 'TEMİZLEME KAPAĞI'),
        (lambda p: HAVALIK_SAPKA((p[0], p[1] - 8), 1.4), 'HAVALIK ŞAPKASI'),
        (lambda p: WC((p[0], p[1] - 30), 'N', TF), 'ALAFRANGA KLOZET (GÖMME REZERVUAR)'),
        (lambda p: LAVABO((p[0], p[1] - 22), 'N', TF), 'LAVABO'),
        (lambda p: DUS(p[0] - 30, p[1] - 30, p[0] + 30, p[1] + 30, TF), 'DUŞ TEKNESİ'),
        (lambda p: EVIYE((p[0], p[1] - 25), 'N', TF, 70, 45), 'EVİYE'),
        (lambda p: MAKINE(p, TF, 'CM', 50), 'ÇAMAŞIR MAKİNESİ'),
        (lambda p: MAKINE(p, TF, 'BM', 50), 'BULAŞIK MAKİNESİ'),
        (lambda p: YER_SUZGECI(p, TF, 22), 'YER SÜZGECİ (Ø50)'),
        (lambda p: KOMBI_PLAN((p[0], p[1] - 16), 'N', CD), 'DUVARA ASILABİLEN HERMETİK KOMBİ 24 kW'),
        (lambda p: KOLLEKTOR_PLAN((p[0], p[1] - 7), 'N', 4, 'MTY-KOLLETOR'), 'YERDEN ISITMA KOLLEKTÖRÜ (P1..Pn)'),
        (lambda p: PL([(p[0] - 40, p[1] - 8), (p[0] + 40, p[1] - 8), (p[0] + 40, p[1] + 8), (p[0] - 40, p[1] + 8)], 'MTY-PEX-BORU'), 'PEX BORU 16x2.0 (15 cm ARALIKLI)'),
        (lambda p: L((p[0] - 40, p[1]), (p[0] + 40, p[1]), 'MTY-ISITMA-GIDIS-BORU'), 'ISITMA GİDİŞ BORUSU'),
        (lambda p: L((p[0] - 40, p[1]), (p[0] + 40, p[1]), 'MTY-ISITMA-DONUS-BORU'), 'ISITMA DÖNÜŞ BORUSU'),
        (lambda p: HEXTAG(p, 'MTY-ISIKAYBIMAHAL', 'Z01'), 'ISI KAYBI MAHAL ETİKETİ (SICAKLIK / ZON)'),
    ]
    for i, (f, s) in enumerate(items):
        col, row = divmod(i, 8)
        p = (x + 70 + col * 900, y - 60 - row * 85)
        f(p)
        T((p[0] + 90, p[1] - 5), s, 12, YZ, 'L')


NOTES = [
    'Temiz su tesisatı PPRC PN20 borularla yapılacak, duvar içi borular izolasyonlu olarak döşenecektir.',
    'Her daire girişinde küresel vana, enerji odasında daire su sayaçları sayaç kollektörü üzerine monte edilecektir.',
    'Sayaçlardan önce DN x 10, sonra DN x 5 uzunluğunda düz boru bırakılacaktır.',
    'Kullanma suyu çatıdaki 4 x 2.00 m³ depolardan paket hidrofor ile katlara dağıtılacaktır.',
    'Depolar gıdaya uygun PE malzemeden kapaklı, havalıklı ve taşma/boşaltma bağlantılı olarak yapılacaktır.',
    'Pis su tesisatı TS EN 1451 çok katmanlı PVC borularla, yatay hatlarda en az %2 eğimle yapılacaktır.',
    'Pis su kolonları çatıdan Ø100 havalık olarak çıkarılacak ve ucuna havalık şapkası takılacaktır.',
    'Her kolon dibinde temizleme kapağı bırakılacak, kolonlar döşeme geçişlerinde kovan içine alınacaktır.',
    'Bodrum ıslak hacimlerinin atık suları terfi çukuru ve dalgıç pompa ile toplama hattına basılacaktır.',
    'Yağmur suyu hatları pis su hatlarına bağlanmayacak, ayrı olarak yağmur suyu kanalına verilecektir.',
    'Yerden ısıtma devreleri PEX 16x2.0 borularla 15 cm aralıkla ve salyangoz (karşı akışlı) düzende döşenecektir.',
    'Bir devre boyu 100 m yi geçmeyecek, devreler kollektörde debi ayarlı vanalarla dengelenecektir.',
    'Döşemede ısı yalıtımı (EPS en az 3 cm), kenar bandı, folyo ve 5 cm şap uygulaması yapılacaktır.',
    'Kombiler yoğuşmalı tip seçilirse yoğuşma suyu en yakın pis su hattına sifonlu olarak bağlanacaktır.',
    'Kombi bacaları hermetik koaksiyel baca olarak dış cepheye çıkarılacaktır.',
    'Isı kaybı değerleri ön boyutlandırma içindir, TS 825 / TS 2164 ısı kaybı hesabı ile kesinleştirilecektir.',
    'Tesisat tamamlandıktan sonra temiz su hatlarına 10 bar, ısıtma devrelerine 6 bar basınç testi yapılacaktır.',
    'Tüm imalat TS 1258, TS EN 12056 ve TS EN 1264 standartlarına uygun olarak yapılacaktır.',
]


def notlar(x, y):
    T((x, y + 20), 'PROJE NOTLARI', 24, YZ, 'L')
    for i, n in enumerate(NOTES):
        T((x, y - 40 - i * 32), '%d. %s' % (i + 1, n), 13, YZ, 'L')
    y2 = y - 40 - len(NOTES) * 32 - 40
    for s in ('DİKKAT: MİMARİ PROJENİN ONAY AŞAMASINDA YAPILACAK DEĞİŞİKLİKTEN FEN İŞLERİ MD. BİLGİLENDİRİLMESİ',
              'BU PROJE MÜELLİFİN İZNİ OLMADAN YAYINLANAMAZ-ÇOĞALTILAMAZ-KULLANILAMAZ-DEĞİŞTİRİLEMEZ.'):
        T((x, y2), s, 13, YZ, 'L'); y2 -= 32


def antet(x, y):
    """büyük ROTAŞ anteti (sol üst köşe x,y)"""
    w, h = 2400, 1300
    RECT(x, y - h, x + w, y, 'MTY-PAFTA')
    T((x + w / 2, y - 80), 'ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK.', 48, YZ, 'C')
    T((x + w / 2, y - 130), 'Semerciler Mah. Sait Faik Sk. No:22/C Z01 Adapazarı/Sakarya', 18, YZ, 'C')
    T((x + w / 2, y - 160), 'rotasmuhendislik@gmail.com   0264 272 00 49', 18, YZ, 'C')
    L((x, y - 190), (x + w, y - 190), 'MTY-PAFTA')
    T((x + w / 2, y - 250), PROJE, 22, YZ, 'C')
    T((x + w / 2, y - 290), 'SIHHİ TESİSAT VE YERDEN ISITMA (KOMBİLİ) PROJESİ', 30, YZ, 'C')
    T((x + w / 2, y - 330), YER, 16, YZ, 'C')
    L((x, y - 360), (x + w, y - 360), 'MTY-PAFTA')
    rows = [('YAPININ ÖZELLİKLERİ', ''), ('YAPI CİNSİ', 'KONUT (A ve B BLOK)'), ('YAPI SINIFI', '3A'),
            ('KAT ADEDİ', 'A BLOK: BODRUM + ZEMİN + 2 KAT  /  B BLOK: ZEMİN + 2 KAT'),
            ('BAĞIMSIZ BÖLÜM SAYISI', '42 DAİRE (2 x 21)'), ('TOPLAM İNŞAAT ALANI', '2728.48 m²'),
            ('ISITMA SİSTEMİ', 'DAİRE TİPİ YOĞUŞMALI / HERMETİK KOMBİ 24 kW + YERDEN ISITMA'),
            ('BİNA MALİYETİ', '..............................'),
            ('ARSANIN ÖZELLİKLERİ', ''), ('İLİ / İLÇESİ', 'SAKARYA / ADAPAZARI'), ('MAHALLESİ', 'ALANDÜZÜ'),
            ('PAFTA / ADA / PARSEL', 'G24B16B4B / 3661 / 7'), ('ARSA ALANI', '2798.45 m²')]
    yy = y - 400
    for a, b in rows:
        T((x + 40, yy), a, 18 if b else 22, YZ, 'L')
        if b:
            T((x + 700, yy), ': ' + b, 18, YZ, 'L')
        yy -= 40
    L((x, y - h + 260), (x + w, y - h + 260), 'MTY-PAFTA')
    L((x + w / 2, y - h), (x + w / 2, y - h + 260), 'MTY-PAFTA')
    T((x + 40, y - h + 220), 'PROJE SORUMLUSU', 18, YZ, 'L')
    T((x + 40, y - h + 160), 'Mak. Müh. Bayram GENÇ', 22, YZ, 'L')
    T((x + w / 2 + 40, y - h + 220), 'ONAY', 18, YZ, 'L')
    T((x + w / 2 + 40, y - h + 180), '14.06.1999 T. 23725 S. VE 08.05.2000 T. 24043 S. RESMİ GAZETE', 12, YZ, 'L')
    T((x + w / 2 + 40, y - h + 160), 'YÖNETMELİKLERİNE UYULMASI KAYDIYLA', 12, YZ, 'L')


def hesaplar(x, y):
    yb = table(x, y, [('ARMATÜR', 330), ('YB', 90), ('DEBİ l/s', 120)],
               [['Lavabo', '0.5', '0.175'], ['Duş bataryası', '1.0', '0.20'], ['Hela rezervuarı', '0.5', '0.125'],
                ['Eviye (1 gözlü)', '0.5', '0.175'], ['Çamaşır makinesi', '1.0', '0.40'], ['Bulaşık makinesi', '1.0', '0.40'],
                ['Pisuvar', '0.25', '0.125'], ['Şofben 16 l/dk', '1.0', '0.25'], ['Termosifon', '2.5', '0.40']],
               'TS 1258 ÇİZELGE 15 - YÜK BİRİMLERİ')
    yb2 = table(x, yb - 90, [('YB ARALIĞI', 200), ('MAKS. DEBİ l/s', 170), ('ÇAP', 120)],
                [['0 - 2.25', '0.38', 'DN20'], ['2.25 - 7.84', '0.70', 'DN25'], ['7.84 - 19.36', '1.01', 'DN32'],
                 ['19.36 - 46.24', '1.70', 'DN40'], ['46.24 - 108.4', '2.60', 'DN50'], ['108.4 - 256', '4.00', 'DN63'],
                 ['256 - 784', '7.00', 'DN75']], 'TS 1258 - PPRC TEMİZ SU ÇAP TABLOSU')
    x2 = x + 650
    yb3 = table(x2, y, [('ARMATÜR', 330), ('SB (DU)', 110)],
                [['Lavabo', '0.5'], ['Duş', '0.7'], ['WC (9 lt rezervuar)', '2.0'], ['Eviye', '0.8'],
                 ['Çamaşır makinesi', '0.8'], ['Bulaşık makinesi', '0.8'], ['Yer süzgeci Ø50', '0.8'],
                 ['Yer süzgeci Ø100', '2.0'], ['Pisuvar', '0.8']], 'TS EN 12056-2 TABLO 2 - SB DEĞERLERİ')
    yb4 = table(x2, yb3 - 90, [('SB ARALIĞI', 200), ('ÇAP', 120), ('KULLANIM', 220)],
                [['0 - 0.8', 'Ø50', 'branşman'], ['0.81 - 5', 'Ø70', 'branşman'], ['5.1 - 14', 'Ø100', 'branşman/kolon'],
                 ['14.1 - 17', 'Ø125', 'toplama'], ['17.1 - 60', 'Ø150', 'toplama'], ['61 - 200', 'Ø200', 'toplama'],
                 ['201 - 720', 'Ø250', 'toplama']], 'TS EN 12056-2 - PİS SU ÇAP TABLOSU')
    T((x2, yb4 - 40), 'Kolon ve toplama hatları Qww = K x √ΣSB (K=0.5) debisine göre kontrol edilmiştir:', 11, 'MTY-HESAP', 'L')
    T((x2, yb4 - 62), 'Daire banyo kolonu (3 kat): ΣSB=%.1f  Qww=%.2f l/s  -> Ø100 havalandırmalı kolon (4.0 l/s) UYGUNDUR.' % (SB_PK, qww(SB_PK)), 11, 'MTY-HESAP', 'L')
    tot = 21 * (SB_PK + SB_MK) + SB_BOD
    T((x2, yb4 - 84), 'Blok toplama hattı: ΣSB=%.1f  Qww=%.2f l/s  -> Ø%d, %%2 eğim.' % (tot, qww(tot), dia_col(tot)), 11, 'MTY-HESAP', 'L')
    # yağmur
    x3 = x2 + 650
    P_ = 597.0; S_ = P_ * 0.75; f = 8; A_ = S_ / f; D_ = 1.13 * math.sqrt(A_)
    yb5 = table(x3, y, [('YAĞMUR İNİŞ BORUSU HESABI (HER BLOK)', 520), ('DEĞER', 200)],
                [['P = çatı alanı (m²)', '%.1f' % P_], ['S = P x 0.75 / 1 (cm²)', '%.1f' % S_], ['f = iniş borusu adedi', '%d' % f],
                 ['A = S / f (cm²)', '%.2f' % A_], ['D = 1.13 x √A (cm)', '%.2f' % D_],
                 ['SONUÇ', 'D > 7 cm -> Ø100 UYGUNDUR' if D_ > 7 else 'Ø70 UYGUNDUR']], 'YAĞMUR SUYU HESABI')
    # depo/hidrofor
    nd = 21
    Qd = nd * 3 * 150 / 1000.0
    q = 0.25 * math.sqrt(21 * YB_D)
    yb6 = table(x3, yb5 - 90, [('KULLANMA SUYU DEPO / HİDROFOR (HER BLOK)', 520), ('DEĞER', 200)],
                [['Daire sayısı / kişi', '21 / 63 kişi'], ['Günlük ihtiyaç (150 l/kişi.gün)', '%.2f m³' % Qd],
                 ['Mevcut depo (mimari proje)', '4 x 2.00 = 8.00 m³'],
                 ['Toplam yük birimi ΣYB', '%.1f YB' % (21 * YB_D)],
                 ['Debi Q = 0.25 x √ΣYB', '%.2f l/s = %.1f m³/h' % (q, q * 3.6)],
                 ['Seçilen hidrofor debisi', '9 m³/h (2 pompa)'],
                 ['Basma yük. (Hmin 10 + kayıp 8 + hat 12)', '30 mSS'],
                 ['Membranlı tank', '100 lt / 10 bar']], 'HİDROFOR VE DEPO HESABI')
    return min(yb2, yb6)


def isi_ozet(x, y):
    rows = []
    for bk in ('A',):
        for k, nm in (('Z', 'ZEMİN'), ('1', '1. KAT'), ('2', '2. KAT')):
            base = {'Z': 0, '1': 7, '2': 14}[k]
            for i in range(7):
                tip, res, tot = HEAT[(bk, k, base + i + 1)]
                rows.append(['%d' % (base + i + 1), nm, 'TİP-%s' % tip, '%d' % len(res),
                             '%.0f' % sum(d['L'] for d in res), '%.1f' % tot, '%.0f' % (tot * 0.86), '24 kW'])
    yb = table(x, y, [('DAİRE', 100), ('KAT', 130), ('TİP', 110), ('DEVRE', 110), ('PEX (m)', 130), ('ISI KAYBI (W)', 190),
                      ('kcal/h', 130), ('KOMBİ', 110)], rows,
               'YERDEN ISITMA ÖZET TABLOSU (A ve B BLOK AYNIDIR)', 10)
    T((x, yb - 30), 'Tasarım: Adapazarı, dış -3°C, iç 20°C (banyo 24°C). Ön boyutlandırma W/m² x kat katsayısı (zemin 1.15, ara 1.00, son kat 1.25).', 10, 'MTY-HESAP', 'L')
    return yb


# ================================================================== çalıştır
def run():
    A0, B0 = (0.0, 0.0), B_OFF
    # ---------- mimari (tek kalem)
    put_arch('VAZ')
    for s in ('A-BOD', 'A-ZEM', 'A-K1', 'A-K2', 'A-CATI', 'B-ZEM', 'B-K1', 'B-K2', 'B-CATI'):
        put_arch(s)
    put_arch('B-ZEM', -4450, 0, only={'A-WALL', 'S-COLS', 'A-DOOR', 'Kapi_Pencere', 'S-STRS', 'A-GENM', 'A-AREA-IDEN'})
    for s in ('A-ZEM', 'A-K1', 'A-K2', 'B-ZEM', 'B-K1', 'B-K2'):
        put_arch(s, 0, HEAT_DY, furn=False)
    # ---------- sıhhi kat planları
    for off in (A0, B0):
        for fl in FLOORS:
            sihhi_kat(off, fl)
    # ---------- ısıtma
    for bk, off in (('A', A0), ('B', B0)):
        for fl in FLOORS:
            isitma_kat(bk, off, fl)
    # ---------- temel/bodrum
    temel(BOD_DX, 0, True)
    bodrum_tesisat(BOD_DX)
    temel(B_OFF[0] - 4450, B_OFF[1], False)
    # ---------- çatı
    cati(CATI_DX, 0)
    cati(CATI_DX + B_OFF[0], B_OFF[1])
    vaziyet()
    # ---------- şemalar
    sihhi_sema(96600, -11094, True, 'A')
    sihhi_sema(91200, -14594, False, 'B')
    isitma_sema(92100, -18094, 'A')
    isitma_sema(86700, -21594, 'B')
    # ---------- antet / lejant / tablolar / notlar
    antet(56600, -8200)
    cad.push(SCALE((59300, -8250), 2.0)); notlar(59300, -8250); cad.pop()
    cad.push(SCALE((56600, -9650), 1.35)); lejant(56600, -9650); cad.pop()
    cad.push(SCALE((64450, -8300), 2.0)); hesaplar(64450, -8300); cad.pop()
    cad.push(SCALE((68500, -8300), 1.5)); isi_ozet(68500, -8300); cad.pop()
    # ---------- paftalar
    fr = [((56467, -11094, 64322, -8094), 'PAFTA 01 - ANTET, LEJANT VE PROJE NOTLARI', ''),
          ((64322, -11094, 71102, -8094), 'PAFTA 02 - HESAP TABLOLARI', ''),
          ((71102, -11094, 74217, -8094), 'VAZİYET PLANI (SIHHİ TESİSAT) ÖLÇEK : 1/200', ''),
          ((74217, -11094, 78667, -8094), 'A BLOK BODRUM KAT VE TEMEL SIHHİ TESİSAT PLANI ÖLÇEK : 1/50', ''),
          ((78667, -11094, 83117, -8094), 'A BLOK ZEMİN KAT SIHHİ TESİSAT PLANI ÖLÇEK : 1/50', ''),
          ((83117, -11094, 87567, -8094), 'A BLOK 1. KAT SIHHİ TESİSAT PLANI ÖLÇEK : 1/50', ''),
          ((87567, -11094, 92017, -8094), 'A BLOK 2. KAT SIHHİ TESİSAT PLANI ÖLÇEK : 1/50', ''),
          ((92017, -11094, 96467, -8094), 'A BLOK ÇATI PLANI (YAĞMUR, HAVALIK, DEPO) ÖLÇEK : 1/50', ''),
          ((96467, -11094, 104667, -8094), 'A BLOK SIHHİ TESİSAT KOLON ŞEMASI', 'ÖLÇEKSİZ'),
          ((68817, -14594, 73267, -11594), 'B BLOK TEMEL SIHHİ TESİSAT PLANI ÖLÇEK : 1/50', ''),
          ((73267, -14594, 77717, -11594), 'B BLOK ZEMİN KAT SIHHİ TESİSAT PLANI ÖLÇEK : 1/50', ''),
          ((77717, -14594, 82167, -11594), 'B BLOK 1. KAT SIHHİ TESİSAT PLANI ÖLÇEK : 1/50', ''),
          ((82167, -14594, 86617, -11594), 'B BLOK 2. KAT SIHHİ TESİSAT PLANI ÖLÇEK : 1/50', ''),
          ((86617, -14594, 91067, -11594), 'B BLOK ÇATI PLANI (YAĞMUR, HAVALIK, DEPO) ÖLÇEK : 1/50', ''),
          ((91067, -14594, 99267, -11594), 'B BLOK SIHHİ TESİSAT KOLON ŞEMASI', 'ÖLÇEKSİZ'),
          ((78667, -18094, 83117, -15094), 'A BLOK ZEMİN KAT YERDEN ISITMA PLANI ÖLÇEK : 1/50', ''),
          ((83117, -18094, 87567, -15094), 'A BLOK 1. KAT YERDEN ISITMA PLANI ÖLÇEK : 1/50', ''),
          ((87567, -18094, 92017, -15094), 'A BLOK 2. KAT YERDEN ISITMA PLANI ÖLÇEK : 1/50', ''),
          ((92017, -18094, 100217, -15094), 'A BLOK YERDEN ISITMA KOLON ŞEMASI', 'ÖLÇEKSİZ'),
          ((73267, -21594, 77717, -18594), 'B BLOK ZEMİN KAT YERDEN ISITMA PLANI ÖLÇEK : 1/50', ''),
          ((77717, -21594, 82167, -18594), 'B BLOK 1. KAT YERDEN ISITMA PLANI ÖLÇEK : 1/50', ''),
          ((82167, -21594, 86617, -18594), 'B BLOK 2. KAT YERDEN ISITMA PLANI ÖLÇEK : 1/50', ''),
          ((86617, -21594, 94817, -18594), 'B BLOK YERDEN ISITMA KOLON ŞEMASI', 'ÖLÇEKSİZ')]
    for (a, b, c, d), t, s in fr:
        o = '1/200' if 'VAZİYET' in t else ('ÖLÇEKSİZ' if ('ŞEMA' in t or 'PAFTA' in t) else '1/50')
        frame(a, b, c, d, t, s, o)
    return fr


if __name__ == '__main__':
    fr = run()
    pickle.dump((cad.R, fr, HEAT), open('/tmp/claude-0/recs.pkl', 'wb'))
    print('records', len(cad.R))
