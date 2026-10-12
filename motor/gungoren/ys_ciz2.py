"""318-319 Parsel Güngören A-B Blok - Yağmur suyu sarnıcı (bahçe sulama) ekleri, rev.2: taşma pompa çukuru yok,
depo taşması cazibeyle yağmur suyu kanalına (birim cm, dünya koordinatları)."""
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from ybpts import A2, B2

doc = ezdxf.new("R2018", setup=True)
doc.header["$INSUNITS"] = 5      # cm
doc.header["$LTSCALE"] = 1
msp = doc.modelspace()
doc.styles.add("ROTAS", font="arial.ttf")

LAY = {
    "MTY-YAGMUR-BORUSU": (4, "CONTINUOUS"),
    "MTY-YAGMUR-BORUSU-CAP": (4, "CONTINUOUS"),
    "YS-KULLANMA": (6, "CONTINUOUS"),
    "YS-TASMA": (94, "DASHED"),
    "YS-TAKVIYE": (3, "CONTINUOUS"),
    "YS-CIHAZ": (2, "CONTINUOUS"),
    "YS-VANA": (1, "CONTINUOUS"),
    "YS-ELEKTRIK": (30, "DASHDOT"),
    "YS-YAZI": (7, "CONTINUOUS"),
    "YS-TABLO": (7, "CONTINUOUS"),
}
for n, (c, lt) in LAY.items():
    doc.layers.add(n, color=c, linetype=lt)

CY, CU, CT, CK = "MTY-YAGMUR-BORUSU", "YS-KULLANMA", "YS-TASMA", "YS-TAKVIYE"
DEV, VAN, EL, TXT = "YS-CIHAZ", "YS-VANA", "YS-ELEKTRIK", "YS-YAZI"


# ------------------------------------------------------------------ temel
def T(x, y, s, h=12.5, lay=TXT, al=TA.BOTTOM_LEFT, rot=0):
    t = msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": lay, "style": "ROTAS", "width": 0.8})
    t.set_placement((x, y), align=al)
    return t


def PL(pts, lay, w=0, closed=False):
    p = msp.add_lwpolyline(pts, dxfattribs={"layer": lay}, close=closed)
    if w:
        p.dxf.const_width = w
    return p


def L(a, b, lay):
    return msp.add_line(a, b, dxfattribs={"layer": lay})


def C(c, r, lay):
    return msp.add_circle(c, r, dxfattribs={"layer": lay})


def ARC(c, r, a0, a1, lay, n=16):
    pts = [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    return PL(pts, lay)


def SOL(p1, p2, p3, lay):
    return msp.add_solid([p1, p2, p3], dxfattribs={"layer": lay})


def rot(p, c, a):
    a = math.radians(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def ARROW(p, ang, lay, s=18):
    a = math.radians(ang)
    b1 = (p[0] - s * math.cos(a) + 0.35 * s * math.sin(a), p[1] - s * math.sin(a) - 0.35 * s * math.cos(a))
    b2 = (p[0] - s * math.cos(a) - 0.35 * s * math.sin(a), p[1] - s * math.sin(a) + 0.35 * s * math.cos(a))
    SOL(p, b1, b2, lay)


# ------------------------------------------------------------------ semboller
def VANA(c, k=1.0, ang=0, lay=VAN):
    """Küresel vana: papyon + mil + kelebek kol."""
    w, h = 10 * k, 6 * k
    pts = [(-w, h), (w, -h), (w, h), (-w, -h)]
    PL([rot((c[0] + x, c[1] + y), c, ang) for x, y in pts], lay, closed=True)
    L(rot(c, c, ang), rot((c[0], c[1] + 9 * k), c, ang), lay)
    L(rot((c[0] - 5 * k, c[1] + 9 * k), c, ang), rot((c[0] + 5 * k, c[1] + 9 * k), c, ang), lay)


def CEKVALF(c, k=1.0, ang=0, lay=VAN):
    """Çek valf: papyon, akış yönündeki üçgen dolu + yön oku."""
    w, h = 10 * k, 6 * k
    PL([rot((c[0] + x, c[1] + y), c, ang) for x, y in [(-w, h), (w, -h), (w, h), (-w, -h)]], lay, closed=True)
    SOL(rot((c[0] + w, c[1] + h), c, ang), rot((c[0] + w, c[1] - h), c, ang), rot(c, c, ang), lay)
    L(rot((c[0] - 6 * k, c[1] + 11 * k), c, ang), rot((c[0] + 6 * k, c[1] + 11 * k), c, ang), lay)
    SOL(rot((c[0] + 9 * k, c[1] + 11 * k), c, ang), rot((c[0] + 4 * k, c[1] + 13 * k), c, ang),
        rot((c[0] + 4 * k, c[1] + 9 * k), c, ang), lay)


def SELENOID(c, k=1.0, ang=0, lay=VAN):
    """Selenoid vana: papyon + mil + bobin (zikzaklı gövde)."""
    w, h = 10 * k, 6 * k
    PL([rot((c[0] + x, c[1] + y), c, ang) for x, y in [(-w, h), (w, -h), (w, h), (-w, -h)]], lay, closed=True)
    L(rot(c, c, ang), rot((c[0], c[1] + 8 * k), c, ang), lay)
    box = [(-6 * k, 8 * k), (6 * k, 8 * k), (6 * k, 18 * k), (-6 * k, 18 * k)]
    PL([rot((c[0] + x, c[1] + y), c, ang) for x, y in box], lay, closed=True)
    zz = [(-6 * k, 10 * k), (6 * k, 12 * k), (-6 * k, 14 * k), (6 * k, 16 * k)]
    PL([rot((c[0] + x, c[1] + y), c, ang) for x, y in zz], lay)


def POMPA(c, r=12.0, ang=0, lay=DEV):
    """Santrifüj pompa: daire + basma yönünde üçgen."""
    C(c, r, lay)
    pts = [(r * 0.75, 0), (-r * 0.45, r * 0.55), (-r * 0.45, -r * 0.55)]
    PL([rot((c[0] + x, c[1] + y), c, ang) for x, y in pts], lay, closed=True)


def MANOMETRE(c, k=1.0, lay=DEV):
    L((c[0], c[1]), (c[0], c[1] + 8 * k), lay)
    C((c[0], c[1] + 14 * k), 6 * k, lay)
    L((c[0], c[1] + 14 * k), (c[0] + 4 * k, c[1] + 18 * k), lay)


def MEMBRANLI_TANK(c, w, h, lay=DEV):
    """Dik membranlı genleşme tankı: kapsül gövde + membran eğrisi + ayaklar."""
    x, y = c
    r = w / 2
    pts = [(x - r, y - h / 2 + r), (x - r, y + h / 2 - r)]
    PL(pts, lay)
    PL([(x + r, y - h / 2 + r), (x + r, y + h / 2 - r)], lay)
    ARC((x, y + h / 2 - r), r, 0, 180, lay)
    ARC((x, y - h / 2 + r), r, 180, 360, lay)
    ARC((x, y + h * 0.05), r * 0.95, 200, 340, lay, 10)          # membran
    L((x - r * 0.7, y - h / 2 + r * 0.3), (x - r * 0.9, y - h / 2 - r * 0.25), lay)
    L((x + r * 0.7, y - h / 2 + r * 0.3), (x + r * 0.9, y - h / 2 - r * 0.25), lay)


def MEMBRANLI_TANK_PLAN(c, r, lay=DEV):
    C(c, r, lay); C(c, r * 0.8, lay)
    L((c[0] - r * 0.8, c[1]), (c[0] + r * 0.8, c[1]), lay)


def KARTUS_FILTRE(c, k=1.0, lay=DEV):
    """Kartuş filtre: kafa + şeffaf hazne + kartuş (kesik)."""
    x, y = c
    PL([(x - 9 * k, y + 4 * k), (x + 9 * k, y + 4 * k), (x + 9 * k, y - 2 * k), (x - 9 * k, y - 2 * k)], lay, closed=True)
    PL([(x - 7 * k, y - 2 * k), (x - 7 * k, y - 26 * k)], lay)
    PL([(x + 7 * k, y - 2 * k), (x + 7 * k, y - 26 * k)], lay)
    ARC((x, y - 26 * k), 7 * k, 180, 360, lay, 8)
    for i in range(5):
        L((x - 3 * k, y - 6 * k - i * 4 * k), (x + 3 * k, y - 6 * k - i * 4 * k), lay)


def VORTEX_FILTRE_PLAN(c, r, lay=DEV):
    """Girdap filtre (plan): baca + gövde + süzgeç (spiral) + kapak."""
    C(c, r, lay); C(c, r * 0.72, lay)
    for a0 in (0, 120, 240):
        pts = []
        for i in range(13):
            t = i / 12
            ang = math.radians(a0 + 200 * t)
            rr = r * 0.65 * (1 - 0.75 * t)
            pts.append((c[0] + rr * math.cos(ang), c[1] + rr * math.sin(ang)))
        PL(pts, lay)
    C(c, r * 0.12, lay)


def VORTEX_FILTRE_KESIT(x, ytop, w, h, lay=DEV):
    """Girdap filtre (şema): üst gövde + konik alt + elek (kesik)."""
    yb = ytop - h
    PL([(x - w / 2, ytop), (x + w / 2, ytop), (x + w / 2, ytop - h * 0.6), (x, yb), (x - w / 2, ytop - h * 0.6)], lay, closed=True)
    for i in range(4):
        yy = ytop - h * 0.12 - i * h * 0.12
        L((x - w * 0.32, yy), (x + w * 0.32, yy), lay)
    ARC((x, ytop - h * 0.3), w * 0.18, 30, 330, lay, 10)


def DALGIC_POMPA(c, k=1.0, lay=DEV):
    """Dalgıç pompa: motor gövdesi (kanatçıklı) + hidrolik kısım + ayak."""
    x, y = c
    PL([(x - 8 * k, y), (x + 8 * k, y), (x + 8 * k, y + 22 * k), (x - 8 * k, y + 22 * k)], lay, closed=True)
    for i in range(4):
        L((x - 8 * k, y + 5 * k + i * 4.5 * k), (x - 11 * k, y + 5 * k + i * 4.5 * k), lay)
        L((x + 8 * k, y + 5 * k + i * 4.5 * k), (x + 11 * k, y + 5 * k + i * 4.5 * k), lay)
    PL([(x - 10 * k, y), (x + 10 * k, y), (x + 7 * k, y - 7 * k), (x - 7 * k, y - 7 * k)], lay, closed=True)
    L((x, y + 22 * k), (x, y + 30 * k), lay)


def SAMANDIRA(c, k=1.0, lay=EL):
    """Şamandıralı seviye şalteri: kablo + kol + top."""
    x, y = c
    L((x, y), (x + 10 * k, y - 8 * k), lay)
    C((x + 14 * k, y - 11 * k), 4.5 * k, lay)


def SEVIYE_SENSOR(x, ytop, ybot, k=1.0, lay=EL):
    """Hidrostatik seviye sensörü: kablo + prob."""
    L((x, ytop), (x, ybot + 8 * k), lay)
    PL([(x - 3 * k, ybot + 8 * k), (x + 3 * k, ybot + 8 * k), (x + 3 * k, ybot), (x - 3 * k, ybot)], lay, closed=True)
    L((x - 3 * k, ybot + 3 * k), (x + 3 * k, ybot + 3 * k), lay)


def YUZER_EMIS(c, k=1.0, lay=CU):
    """Yüzer emiş: top şamandıra + süzgeç kafesi."""
    x, y = c
    C((x, y + 9 * k), 7 * k, lay)
    L((x, y + 2 * k), (x, y - 2 * k), lay)
    PL([(x - 8 * k, y - 2 * k), (x + 8 * k, y - 2 * k), (x + 8 * k, y - 10 * k), (x - 8 * k, y - 10 * k)], lay, closed=True)
    for i in range(3):
        L((x - 8 * k + (i + 1) * 4 * k, y - 2 * k), (x - 8 * k + (i + 1) * 4 * k, y - 10 * k), lay)


def SAKINLESTIRICI(x, ytop, ybot, k=1.0, lay=CY):
    """Sakinleştirici giriş: dibe inen boru + yukarı dönük dirsek."""
    PL([(x, ytop), (x, ybot + 6 * k)], lay, 1.2 * k)
    ARC((x + 6 * k, ybot + 6 * k), 6 * k, 180, 270, lay, 6)
    PL([(x + 6 * k, ybot), (x + 12 * k, ybot)], lay)
    ARC((x + 12 * k, ybot + 6 * k), 6 * k, 270, 360, lay, 6)
    PL([(x + 18 * k, ybot + 6 * k), (x + 18 * k, ybot + 12 * k)], lay)


def TASMA_SIFONU(x, y, k=1.0, lay=CT):
    """Taşma sifonu (U) + kemirgen kapanı (klape)."""
    PL([(x, y), (x, y - 12 * k)], lay)
    ARC((x + 6 * k, y - 12 * k), 6 * k, 180, 360, lay, 8)
    PL([(x + 12 * k, y - 12 * k), (x + 12 * k, y - 2 * k)], lay)
    L((x + 12 * k, y - 2 * k), (x + 20 * k, y - 2 * k), lay)
    L((x + 20 * k, y + 4 * k), (x + 24 * k, y - 6 * k), lay)          # klape


def HAVA_BOSLUGU(x, yout, ytop_tank, k=1.0, lay=CK):
    """AB hava boşluğu: serbest çıkış + boşluk işareti."""
    L((x - 5 * k, yout), (x + 5 * k, yout), lay)
    for yy in (yout - 3 * k, ytop_tank + 3 * k):
        L((x - 9 * k, yy), (x - 4 * k, yy), TXT)
    L((x - 6.5 * k, yout - 3 * k), (x - 6.5 * k, ytop_tank + 3 * k), TXT)


def MUSLUK(c, k=1.0, lay=CU):
    """Kilitli bahçe/yıkama musluğu: vana gövdesi + ağız + kilit."""
    x, y = c
    C((x, y), 6 * k, lay)
    PL([(x + 6 * k, y), (x + 14 * k, y), (x + 14 * k, y - 7 * k)], lay)
    L((x, y + 6 * k), (x, y + 11 * k), lay)
    PL([(x - 3 * k, y + 11 * k), (x + 3 * k, y + 11 * k), (x + 3 * k, y + 16 * k), (x - 3 * k, y + 16 * k)], lay, closed=True)


def YB_PLAN(c, r=9.0, lay=CY):
    """Tavandan inen yağmur iniş borusu: çift daire + iniş oku."""
    C(c, r, lay); C(c, r * 0.45, lay)
    L((c[0] - r * 0.7, c[1] - r * 0.7), (c[0] + r * 0.7, c[1] + r * 0.7), lay)


def KOLON_CIKIS(c, r=9.0, lay=CU):
    """Yukarı çıkan kolon: daire + nokta + yukarı ok."""
    C(c, r, lay)
    SOL((c[0] - 2.5, c[1] - 2.5), (c[0] + 2.5, c[1] - 2.5), (c[0], c[1] + 2.5), lay)
    L((c[0], c[1] + r), (c[0], c[1] + r + 16), lay)
    ARROW((c[0], c[1] + r + 22), 90, lay, 10)


def KONTROL_PANOSU(c, w, h, lay=DEV):
    x, y = c
    PL([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], lay, closed=True)
    for i in range(3):
        C((x - w * 0.3 + i * w * 0.3, y + h * 0.18), h * 0.12, lay)
    L((x - w * 0.35, y - h * 0.22), (x + w * 0.35, y - h * 0.22), lay)


def ROGAR_PLAN(c, s, lay=CT):
    x, y = c
    PL([(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)], lay, closed=True)
    C(c, s * 0.7, lay)
    L((x - s * 0.5, y), (x + s * 0.5, y), lay)


def HOP(x, y, r, lay):
    """Boru köprüsü (kesişim atlama)."""
    ARC((x, y), r, 0, 180, lay, 8)


def HAT(xa, xb, y, items, lay, w=0):
    """xa -> xb yatay hat; items: [(x_merkez, yarı_genişlik)] sembol uçları arasında boşluk kalmadan çizgi"""
    d = 1 if xb > xa else -1
    cur = xa
    for xc, hw in sorted(items, key=lambda t: d * t[0]):
        a = xc - d * hw
        if d * (a - cur) > 0.01:
            PL([(cur, y), (a, y)], lay, w)
        cur = xc + d * hw
    if d * (xb - cur) > 0.01:
        PL([(cur, y), (xb, y)], lay, w)


NOLAY = "YS-EKIPMAN-NO"
doc.layers.add(NOLAY, color=1)


def NOB(p, n, r=9.0):
    """ekipman numarası balonu (ekipman listesiyle aynı)"""
    C(p, r, NOLAY)
    T(p[0], p[1], str(n), r * 1.1, NOLAY, TA.MIDDLE_CENTER)


# ================================================================== 1) 2. BODRUM PLANI
XC = 247420.0          # ana düşey kolektör
YT = -488005.0         # kuzey tavan hattı (kolonların güneyinden)
YSH = -489990.0        # güney tavan hattı
F1 = (247290.0, -489720.0)
NODE = (XC, F1[1])
TANK = (246801.0, -490108.0, 247175.0, -489603.0)    # iç ölçü
YSR = (247285.0, -490330.0)


def pipe(pts, lay, w=2.0):
    return PL(pts, lay, w)

# --- YB iniş noktaları kolon yüzüne ötelenir (boru ve sembol kolon içinden geçmez)
A2 = list(A2); B2 = list(B2)
OTELE = {}
def _ot(lst, i, p, lab):
    lst[i] = p; OTELE[lab] = p
_ot(A2, 2, (248500.0, A2[2][1]), "A-YB3")
_ot(A2, 3, (A2[3][0] - 2.0, -489622.0), "A-YB4")
_ot(A2, 4, (248392.0, A2[4][1]), "A-YB5")
_ot(A2, 6, (247255.0, A2[6][1]), "A-YB7")
_ot(B2, 2, (250396.0, B2[2][1]), "B-YB3")
_ot(B2, 3, (250396.0, B2[3][1]), "B-YB4")
_ot(B2, 4, (B2[4][0], -490325.0), "B-YB5")
_ot(B2, 5, (249163.0, B2[5][1]), "B-YB6")
for i, p in enumerate(A2, 1):
    YB_PLAN(p)
    T(p[0] + 12, p[1] + 10, f"A-YB{i} %%C70" + (" *" if f"A-YB{i}" in OTELE else ""), 10, CY)
for i, p in enumerate(B2, 1):
    YB_PLAN(p)
    T(p[0] + 12, p[1] + 10, f"B-YB{i} %%C70" + (" *" if f"B-YB{i}" in OTELE else ""), 10, CY)

# --- A blok bağlantıları
a1, a2, a3, a4, a5, a6, a7, a8 = A2
pipe([a1, (247255.0, a1[1]), (247255.0, YT), (XC, YT)], CY)
pipe([a2, (248395.0, a2[1]), (248395.0, YT)], CY)
pipe([a3, (a3[0], YT)], CY)
pipe([a8, (a8[0], -488650.0), (XC, -488650.0)], CY)
pipe([a7, (XC, a7[1])], CY)
pipe([a6, (a6[0], -490180.0), (247260.0, -490180.0), (247260.0, YSH), (XC, YSH)], CY)
T(247170, a6[1] - 22, "A-YB6 duvar dışından, duvar geçişi ile", 8, CY)
pipe([a5, (a5[0], YSH)], CY)
pipe([a4, (a4[0], YSH), (XC, YSH)], CY)
# --- B blok bağlantıları
b1, b2, b3, b4, b5, b6, b7, b8 = B2
XBE, XBW = 250440.0, 249090.0
pipe([b1, (b1[0], YT)], CY)
pipe([b2, (b2[0], YT)], CY)
pipe([b3, (XBE, b3[1])], CY)
pipe([b4, (XBE, b4[1])], CY)
pipe([b5, (250398.0, b5[1]), (250398.0, -490200.0), (XBE, -490200.0), (XBE, YT)], CY)
pipe([b6, (b6[0], -490200.0), (XBW, -490200.0), (XBW, YT)], CY)
pipe([b7, (XBW, b7[1])], CY)
pipe([b8, (XBW, b8[1])], CY)
# --- ana hatlar
pipe([(XBE, YT), (a3[0], YT)], CY, 3.0)            # Ø160
pipe([(a3[0], YT), (XC, YT), (XC, NODE[1])], CY, 4.0)  # Ø200
pipe([(XC, YSH), (XC, NODE[1])], CY, 2.5)          # Ø110 güney
pipe([NODE, (F1[0] + 42, F1[1])], CY, 4.0)
# akış okları
for p, a in [((249900, YT), 180), ((248000, YT), 180), ((XC, -488300), 270), ((XC, -489300), 270),
             ((XC, -489900), 90), ((247900, YSH), 180), ((XBE, -489000), 90), ((XBW, -489000), 90),
             ((247350, NODE[1]), 180)]:
    ARROW(p, a, CY, 16)
# çap etiketleri
T(249700, YT + 8, "%%C160 PVC  %0,5  TAVANDAN", 12.5, "MTY-YAGMUR-BORUSU-CAP")
T(247650, YT + 8, "%%C200 PVC  %0,5  TAVANDAN", 12.5, "MTY-YAGMUR-BORUSU-CAP")
T(XC + 8, -488950, "%%C200 PVC  %0,5  TAVANDAN", 12.5, "MTY-YAGMUR-BORUSU-CAP", TA.BOTTOM_LEFT, 90)
T(247800, YSH + 8, "%%C110 PVC  %1  TAVANDAN", 12.5, "MTY-YAGMUR-BORUSU-CAP")
T(XBE + 8, -489400, "%%C110 PVC  %1  TAVANDAN", 12.5, "MTY-YAGMUR-BORUSU-CAP", TA.BOTTOM_LEFT, 90)
T(XBW - 8, -489400, "%%C110 PVC  %1  TAVANDAN", 12.5, "MTY-YAGMUR-BORUSU-CAP", TA.BOTTOM_RIGHT, 90)
T(247830, -488640, "YB BRANŞMANLARI %%C110 PVC %1", 10, "MTY-YAGMUR-BORUSU-CAP")

# --- F1 vortex filtre
VORTEX_FILTRE_PLAN(F1, 42)
T(F1[0] - 60, F1[1] + 55, "F1 GİRDAP FİLTRE DN200", 10, DEV)
T(F1[0] - 60, F1[1] + 44, "0,35 mm, çatı ≥ 750 m²", 9, DEV)
# temiz çıkış -> depo, sakinleştirici
pipe([(F1[0] - 42, F1[1]), (TANK[2] - 60, F1[1])], CY, 4.0)
L((TANK[2] - 60, F1[1]), (TANK[2] - 60, F1[1] - 120), CY)
ARC((TANK[2] - 75, F1[1] - 120), 15, 180, 360, CY, 8)
T(TANK[2] - 250, F1[1] - 105, "Sakinleştirici giriş (dipte)", 9, CY)
# --- taşma (depo içinde taşma sifonu) + F1 kirli su: cazibeyle tek hat, duvar geçişi ile YSR rögarı -> yağmur suyu kanalı
XT = 247290.0
pipe([(TANK[2] - 25, -489935.0), (XT, -489935.0), (XT, YSR[1] + 20)], CT, 3.0)
TASMA_SIFONU(TANK[2] - 40, -489935.0, 1.0)
pipe([(F1[0], F1[1] - 42), (F1[0], -489935.0)], CT, 2.0)
HOP(F1[0], -489840.0, 8, CT)
ROGAR_PLAN((XT, YSR[1]), 20, CT)
ARROW((XT, -490050.0), 270, CT, 16)
T(XT + 14, -490010.0, "DEPO TAŞMASI + F1 KİRLİ SU %%C200 PVC %1 (CAZİBE)", 10, CT)
T(XT + 14, -490024.0, "Taşma depo içindeki taşma sifonundan; ayrıca pompa yoktur.", 9, CT)
T(YSR[0] + 28, YSR[1] - 5, "YSR: YAĞMUR SUYU BAĞLANTI RÖGARI (BİNA DIŞI)", 10, CT)
T(YSR[0] + 28, YSR[1] - 18, "YAĞMUR SUYU KANALINA GİDER (pis su kanalına bağlanmaz)", 10, CT)

# --- seviye sensörü + şamandıralar
C((247120, -489980), 6, EL)
T(247030, -490000, "LT", 9, EL)
PL([(247120, -489974), (247120, -489960), (247445, -489960), (247445, -489900)], EL)  # seviye -> kontrol panosu

# --- hidrofor (tank dışında, sığınak yanı - zemin)
HX, HY = 247510.0, -489800.0
pipe([(247060.0, -489840.0), (247440.0, -489840.0)], CU, 2.0)       # emiş
HOP(XC, -489840.0, 8, CU)
YUZER_EMIS((247060.0, -489840.0), 1.0)
T(246900, -489870, "Yüzer emiş", 9, CU)
for py in (-489770.0, -489830.0):
    VANA((247455.0, py), 0.8, 0, VAN)
    POMPA((247490.0, py), 14, 0)
    CEKVALF((247525.0, py), 0.8, 0, VAN)
    HAT(247440.0, 247560.0, py, [(247455.0, 8.0), (247490.0, 14.0), (247525.0, 8.0)], CU)
L((247440.0, -489770.0), (247440.0, -489840.0), CU)
L((247560.0, -489770.0), (247560.0, -489830.0), CU)
MEMBRANLI_TANK_PLAN((247600.0, -489860.0), 22)
L((247560.0, -489830.0), (247578.0, -489852.0), CU)
MANOMETRE((247560.0, -489770.0), 0.8)
KONTROL_PANOSU((247470.0, -489900.0), 50, 24)
T(247440, -489935, "H-YS SULAMA HİDROFORU 1,5 m³/h - 36 mSS - 0,55 kW", 9, DEV)
T(247440, -489947, "(1 asıl+1 yedek), MT 100 L, KP kontrol panosu", 9, DEV)
# kartuş filtre + YSK çıkışı
KARTUS_FILTRE((247560.0, -489700.0), 0.8)
pipe([(247560.0, -489770.0), (247560.0, -489700.0), (247580.0, -489700.0), (247580.0, -488600.0)], CU, 2.0)
pipe([(247580.0, -488600.0), (246780.0, -488600.0)], CU, 2.0)          # bahçe hattı
HOP(XC, -488600.0, 8, CU)
VANA((246830.0, -488600.0), 1.0, 0, VAN)
PL([(246740.0, -488620.0), (246780.0, -488620.0), (246780.0, -488580.0), (246740.0, -488580.0)], CU, 0, True)
L((246740.0, -488620.0), (246780.0, -488580.0), CU)
T(246740, -488640, "BAHÇE SULAMA VANA KUTUSU (KİLİTLİ)", 8, CU)
T(246790, -488585, "YSK %%C32 PE100 → BİNA DIŞI BAHÇE SULAMA VANA KUTUSUNA", 10, CU)
T(246790, -488625, "(duvar geçişi, toprak altı -0,80)", 9, CU)
T(247590, -489300, "YSK %%C32 PE100 - YAĞMUR SUYU İÇİLEMEZ - YALNIZ BAHÇE SULAMA", 10, CU, TA.BOTTOM_LEFT, 90)
ARROW((247000, -488600), 180, CU, 14)

# --- şebeke takviyesi (mevcut hidrofor basma hattından)
TK = 247540.0
pipe([(TK, -488828.0), (TK, -489625.0), (TANK[2] - 30, -489625.0), (TANK[2] - 30, -489650.0)], CK, 1.5)
C((TK, -488828.0), 4, CK)
T(TK - 8, -488818.0, 'MEVCUT HİDROFOR BASMA HATTINDAN', 8, CK, TA.BOTTOM_RIGHT)
VANA((TK, -488900.0), 0.9, 90, VAN)
SELENOID((TK, -489100.0), 0.9, 90, VAN)
CEKVALF((TK, -489200.0), 0.9, 270, VAN)
T(TK + 12, -489000, "Şebeke takviyesi %%C25", 10, CK, TA.BOTTOM_LEFT, 90)
HOP(XC, -489625.0, 8, CK)
T(TANK[2] - 230, -489665, "AB hava boşluğu ≥ 2xDN", 9, CK)
PL([(TK, -489100.0), (247625.0, -489100.0), (247625.0, -489900.0), (247495.0, -489900.0)], EL)

# --- depo etiketi
T(246830, -489700, "YAĞMUR SUYU SARNICI (MİMARİ: YAĞMUR HASADI DEPOSU)", 12.5, CY)
T(246830, -489718, "İç 3,74 x 5,05 m - faydalı h ≥ 1,10 m", 10, CY)
T(246830, -489733, "V ≥ 20,0 m³ (h=1,50 m ile ≈ 28 m³)", 10, CY)

# genel not (plan)
T(248600, -489200, "YAĞMUR SUYU SARNICI - A+B BLOK 16 ADET YB - BAHÇE SULAMA", 14, CY)
T(248600, -489218, "Tüm toplama hatları 2. bodrum tavanından askı ile, otopark net yüksekliği ≥ 2,20 m korunacaktır.", 10, CY)


# ================================================================== 2) A BLOK KOLON ŞEMASI (2. bodrum bandı)
SY = -489815.0
k = 0.8
YBX_A = [277153.9 + 60 * i for i in range(8)]
for x in YBX_A:
    L((x, -489783.9), (x, SY), CY)
PL([(277095.0, SY), (277780.0, SY)], CY, 2.0)
ARROW((277120.0, SY), 0, CY, 10)
ARROW((277765.0, SY), 0, CY, 10)
T(277095, SY - 52, "← B BLOK YB1-YB8 (B şeması)", 8, CY)
# F1
VORTEX_FILTRE_KESIT(277800.0, -489800.0, 40, 55)
T(277825, -489800, "F1", 10, DEV)
# depo
TX0, TY0, TX1, TY1 = 277760.0, -490150.0, 277915.0, -489900.0
PL([(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], CY, 2.0, True)
wl = TY0 + 160
l = L((TX0, wl), (TX1, wl), CY); l.dxf.linetype = "DASHED"
T(TX0 + 8, TY1 - 18, "YAĞMUR SUYU SARNICI", 10, CY)
T(TX0 + 8, TY1 - 31, "V ≥ 20 m³", 9, CY)
SAKINLESTIRICI(277800.0, -489855.0, TY0 + 6, 0.8)
# kirli su + taşma -> cazibe ile yağmur suyu kanalına (pompa yok)
PL([(277820.0, -489833.0), (277945.0, -489833.0), (277945.0, -490205.0), (277099.0, -490205.0)], CT, 1.2)
HOP(277945.0, -489875.0, 5, CK)
PL([(TX1, wl + 10), (277945.0, wl + 10)], CT, 1.2)
TASMA_SIFONU(TX1 - 14, wl + 10, 0.6)
ROGAR_PLAN((277085.0, -490205.0), 14, CT)
T(277110, -490228, "TAŞMA + F1 KİRLİ SU %%C200 → YSR → YAĞMUR SUYU KANALINA GİDER (pis suya bağlanmaz)", 8, CT)
# hidrofor (2 pompa paralel)
SEV_Y = -490120.0
PL([(TX0, SEV_Y), (277575.0, SEV_Y)], CU, 1.2)
YUZER_EMIS((277785.0, SEV_Y + 10), 0.6)
PL([(277575.0, -490145.0), (277575.0, -490095.0)], CU, 1.2)
PL([(277445.0, -490145.0), (277445.0, -490095.0)], CU, 1.2)
for ry in (-490095.0, -490145.0):
    VANA((277555.0, ry), 0.6, 0, VAN)
    POMPA((277530.0, ry), 10, 180)
    CEKVALF((277490.0, ry), 0.6, 180, VAN)
    VANA((277465.0, ry), 0.6, 0, VAN)
    HAT(277575.0, 277445.0, ry, [(277555.0, 6.0), (277530.0, 10.0), (277490.0, 6.0), (277465.0, 6.0)], CU, 1.2)
PL([(277445.0, -490120.0), (277430.0, -490120.0), (277430.0, -490040.0), (277250.0, -490040.0), (277250.0, -489950.0)], CU, 1.2)
MEMBRANLI_TANK((277390.0, -490090.0), 26, 60)
L((277390.0, -490060.0), (277390.0, -490040.0), CU)
MANOMETRE((277350.0, -490040.0), 0.7)
KARTUS_FILTRE((277310.0, -490040.0), 0.6)
VANA((277275.0, -490040.0), 0.7, 0, VAN)
PL([(277235.0, -489950.0), (277265.0, -489950.0), (277265.0, -489925.0), (277235.0, -489925.0)], CU, 0, True)
T(277272, -489940, "YSK %%C32 PE100 → BAHÇE SULAMA VANA KUTUSU (İÇİLEMEZ)", 8, CU)
T(277600, -490070, "H-YS 1,5 m³/h-36 mSS (1+1)", 7, DEV)
# takviye
PL([(278060.0, -489875.0), (277860.0, -489875.0), (277860.0, -489888.0)], CK, 1.0)
C((278060.0, -489875.0), 3, CK)
T(278066, -489890, "ŞEBEKEDEN (MEVCUT HİDROFOR BASMA HATTI)", 7, CK)
SELENOID((277990.0, -489875.0), 0.7, 0, VAN)
VANA((278020.0, -489875.0), 0.7, 0, VAN)
HAVA_BOSLUGU(277860.0, -489888.0, TY1, 0.8)
T(277870, -489868, "Şebeke takviye %%C25", 7, CK)
# seviye
SEVIYE_SENSOR(277880.0, TY1, TY0 + 8, 0.7)

# ================================================================== 3) B BLOK KOLON ŞEMASI
YBX_B = [306811.7 + 60 * i for i in range(8)]
for x in YBX_B:
    L((x, -489783.9), (x, SY), CY)
PL([(307231.7, SY), (306775.0, SY), (306775.0, -489880.0)], CY, 2.0)
ARROW((306790.0, SY), 180, CY, 10)
ARROW((306775.0, -489875.0), 270, CY, 10)
for i, s in enumerate(["B BLOK YB1-YB8 (8 x %%C70)",
                       "2. bodrum tavanından %%C160 PVC %0,5 toplama hattı ile",
                       "A BLOK şemasındaki F1 GİRDAP FİLTRE ve",
                       "YAĞMUR SUYU SARNICINA bağlanır (2. bodrum planına bkz.)"]):
    T(306800, -489905 - i * 15, s, 9 if i else 10, CY)


# ================================================================== 4) LEJANT / HESAP / NOTLAR
PX, PY = 246100.0, -491000.0
T(PX, PY + 40, "YAĞMUR SUYU SARNICI (BAHÇE SULAMA) - LEJANT, HESAP ÖZETİ VE PROJE NOTLARI", 30, TXT)
L((PX, PY + 30), (PX + 5800, PY + 30), TXT)
# --- LEJANT
T(PX, PY - 30, "LEJANT", 20, TXT)
items = [
 ("yb", "Yağmur iniş borusu (YB), tavandan inen %%C70"),
 ("ln", CY, 2.0, "Yağmur suyu toplama hattı (PVC, tavandan, eğimli)"),
 ("ln", CU, 2.0, "Yağmur suyu kullanma hattı YSK (PE100, İÇİLEMEZ)"),
 ("ln", CT, 2.0, "Taşma / filtre kirli su hattı (cazibe, yağmur suyu kanalına)"),
 ("ln", CK, 1.5, "Şebeke takviye hattı"),
 ("ln", EL, 0, "Seviye / kumanda kablosu"),
 ("vana", "Küresel vana"),
 ("cek", "Çek valf"),
 ("sel", "Selenoid vana (NC, 24 V)"),
 ("pompa", "Santrifüj pompa (hidrofor)"),
 ("mt", "Membranlı genleşme tankı"),
 ("vf", "F1 girdap (vortex) filtre"),
 ("kf", "Kartuş filtre 100 µm"),
 ("man", "Manometre"),
 ("ye", "Yüzer emiş (şamandıralı, süzgeçli)"),
 ("lt", "Hidrostatik seviye sensörü"),
 ("sak", "Sakinleştirici giriş"),
 ("sif", "Taşma sifonu + kemirgen kapanı"),
 ("ab", "AB hava boşluğu (TS EN 1717)"),
 ("kp", "Kontrol panosu"),
 ("rog", "YSR yağmur suyu bağlantı rögarı"),
 ("hop", "Boru köprüsü (kesişim)"),
 ("ok", "Akış yönü"),
]
y = PY - 80
for it in items:
    cx, cy = PX + 60, y
    t = it[0]
    if t == "yb": YB_PLAN((cx, cy))
    elif t == "ln":
        pl = PL([(cx - 45, cy), (cx + 45, cy)], it[1], it[2])
    elif t == "vana": L((cx - 40, cy), (cx - 12, cy), VAN); L((cx + 12, cy), (cx + 40, cy), VAN); VANA((cx, cy))
    elif t == "cek": L((cx - 40, cy), (cx - 12, cy), VAN); L((cx + 12, cy), (cx + 40, cy), VAN); CEKVALF((cx, cy))
    elif t == "sel": L((cx - 40, cy), (cx - 12, cy), VAN); L((cx + 12, cy), (cx + 40, cy), VAN); SELENOID((cx, cy - 4))
    elif t == "pompa": L((cx - 40, cy), (cx - 14, cy), DEV); L((cx + 14, cy), (cx + 40, cy), DEV); POMPA((cx, cy), 14)
    elif t == "mt": MEMBRANLI_TANK((cx, cy + 4), 22, 44)
    elif t == "vf": VORTEX_FILTRE_PLAN((cx, cy), 20)
    elif t == "kf": KARTUS_FILTRE((cx, cy + 14), 0.9)
    elif t == "man": L((cx - 30, cy - 8), (cx + 30, cy - 8), DEV); MANOMETRE((cx, cy - 8))
    elif t == "ye": YUZER_EMIS((cx, cy), 1.0)
    elif t == "dp": DALGIC_POMPA((cx, cy - 12), 0.9)
    elif t == "sam": L((cx - 10, cy + 10), (cx - 10, cy), EL); SAMANDIRA((cx - 10, cy), 1.0)
    elif t == "lt": SEVIYE_SENSOR(cx, cy + 15, cy - 15, 1.0)
    elif t == "sak": SAKINLESTIRICI(cx - 10, cy + 18, cy - 15, 1.0)
    elif t == "sif": TASMA_SIFONU(cx - 10, cy + 8, 1.0)
    elif t == "ab": L((cx - 20, cy - 14), (cx + 25, cy - 14), CY); L((cx, cy + 20), (cx, cy + 2), CK); HAVA_BOSLUGU(cx, cy + 2, cy - 14, 1.0)
    elif t == "mus": L((cx - 35, cy), (cx - 6, cy), CU); MUSLUK((cx, cy))
    elif t == "kp": KONTROL_PANOSU((cx, cy), 46, 24)
    elif t == "rog": ROGAR_PLAN((cx, cy), 16)
    elif t == "hop": L((cx - 40, cy), (cx - 8, cy), CU); L((cx + 8, cy), (cx + 40, cy), CU); HOP(cx, cy, 8, CU); L((cx, cy - 20), (cx, cy + 20), CY)
    elif t == "ok": L((cx - 40, cy), (cx + 10, cy), CY); ARROW((cx + 25, cy), 0, CY, 18)
    T(PX + 130, y - 5, it[-1], 12.5, TXT)
    y -= 48

# --- HESAP ÖZETİ
HX0 = PX + 1600
T(HX0, PY - 30, "HESAP ÖZETİ (PAİY m.57/7-a, TS EN 16941-1, TS EN 12056-3)", 20, TXT)
rows = [
 ("1", "Yıllık yağış - İstanbul, MGM 1950-2025 aylık ortalamaları toplamı", "h = 659,4 mm"),
 ("2", "A Blok çatı iz düşümü (çatı planından, saçak dahil)", "365,0 m²  (çatı arası 346,75)"),
 ("3", "B Blok çatı iz düşümü (çatı planından, saçak dahil)", "337,7 m²  (çatı arası 322,38)"),
 ("4", "Toplam toplama alanı A", "702,6 m²"),
 ("5", "Verim katsayıları: kiremit kırma çatı e / filtre η", "0,80 / 0,90"),
 ("6", "Yıllık toplanabilir su  E = A·h·e·η", "333,6 m³/yıl"),
 ("7", "Asgari depo hacmi  Vmin = %6 · E", "20,0 m³"),
 ("8", "Mevcut hasat deposu iç 3,74 x 5,05 = 18,9 m² → faydalı h ≥ 1,06 m", "h=1,50 m → 28,3 m³ ≥ 20,0 ✓"),
 ("9", "Tasarım yağış debisi  Qr = A·r·C  (r = 0,030 l/s·m², C = 1,0)", "21,1 l/s (A 10,95 / B 10,13)"),
 ("10", "YB başına debi / mevcut %%C70 kapasitesi (f = 0,33)", "1,37 l/s ≤ ≈3,5 l/s ✓"),
 ("11", "%%C110 PVC %1 kapasite (Manning n = 0,010) / en yüklü branşman", "7,4 ≥ 4,1 l/s ✓"),
 ("12", "%%C160 PVC %0,5 kapasite / B blok + A2-A3 yükü", "14,2 ≥ 12,9 l/s ✓"),
 ("13", "%%C200 PVC %0,5 kapasite / F1 girişi toplam", "25,6 ≥ 21,1 l/s ✓"),
 ("14", "Kullanım: YALNIZ BAHÇE SULAMA - bahçe 181,6 m² x 60 l/m²·yıl", "10,9 m³/yıl ≤ 333,6 ✓"),
 ("15", "Sulama günlük ihtiyacı (yaz, 5 l/m²·gün) / depo karşılama süresi", "0,91 m³/gün → ≈ 31 gün"),
 ("16", "Hidrofor debisi: 1 sulama zonu (6 rotor x 0,25 m³/h) eş zamanlı", "Q = 1,5 m³/h"),
 ("17", "Basma yüksekliği: Hgeo 5,3 + kayıp (boru+filtre+vana) 5,7 + çıkış 25", "H = 36 mSS"),
 ("18", "Pompa gücü  P = ρ·g·Q·H / η  (η = 0,40)", "0,37 → 0,55 kW (1 asıl + 1 yedek)"),
 ("19", "Membranlı tank V = 1000·Q/(4Z)·(Pk+1)/(Pk−Pd), Z=20, Pd/Pk=3,6/5,0", "80 → 100 L, ön basınç 3,4 bar"),
 ("20", "Filtreler: F1 girdap DN200 (0,35 mm, ≥ 750 m² çatı) + kartuş 100 µm", "Q filtre ≥ 21,1 l/s ✓"),
 ("21", "Taşma: depo içi taşma sifonu, %%C200 PVC %1 cazibe hattı (Q = Qr)", "37,2 ≥ 21,1 l/s ✓ → kanala"),
]
cw = [70, 1120, 560]
xs = [HX0]
for w in cw: xs.append(xs[-1] + w)
rh = 34
ytop = PY - 55
PL([(xs[0], ytop), (xs[-1], ytop), (xs[-1], ytop - rh * len(rows)), (xs[0], ytop - rh * len(rows))], "YS-TABLO", 0, True)
for x in xs[1:-1]: L((x, ytop), (x, ytop - rh * len(rows)), "YS-TABLO")
for i, r in enumerate(rows):
    yy = ytop - rh * i
    if i: L((xs[0], yy), (xs[-1], yy), "YS-TABLO")
    for j, sv in enumerate(r):
        T(xs[j] + 10, yy - rh / 2, sv, 12.5, "YS-TABLO", TA.MIDDLE_LEFT)

# --- PROJE NOTLARI
NX0 = HX0
NY0 = ytop - rh * len(rows) - 60
T(NX0, NY0, "PROJE NOTLARI", 20, TXT)
notes = [
 "1. Yağmur suyu yalnızca A ve B blok çatılarından toplanacak, YALNIZCA bahçe sulamasında kullanılacaktır.",
 "2. Toplanan yağmur suyu içme, yemek, kişisel temizlik ve araç / zemin yıkama amacıyla kullanılmayacaktır.",
 "3. 16 adet YB, 2. bodrum tavanından askılı PVC hatlarla F1 girdap filtreye, oradan sakinleştirici girişle yağmur suyu sarnıcına bağlanacaktır.",
 "4. Tavan hatları gösterilen çap ve eğimlerde döşenecek, otopark net yüksekliği 2,20 m'den az bırakılmayacaktır.",
 "5. Sarnıç taşması depo içindeki taşma sifonundan, F1 kirli suyu ile birlikte cazibeyle YSR rögarı üzerinden yağmur suyu kanalına gidecektir; ayrıca taşma pompası yoktur.",
 "6. Yağmur suyu hatları hiçbir şekilde pis su şebekesine, PB1 ve PB2 pompa çukurlarına bağlanmayacaktır.",
 "7. Şebeke takviyesi yalnızca TS EN 1717 AB hava boşluğu üzerinden yapılacak, selenoid vana seviye sensörüyle alt seviyede açılacaktır.",
 "8. 'YAĞMURLAMA SUYU DEPOSU' yağmur suyu sistemine bağlanmayacaktır.",
 "9. YSK boruları mor renkli veya 'YAĞMUR SUYU - İÇİLEMEZ' etiketli olacak, bahçe sulama vana kutusu kilitli ve levhalı olacaktır.",
 "10. Sulama hidroforunda kuru çalışma koruması (seviye sensörü) ve kontrol panosunda yüksek / düşük seviye alarmı olacaktır.",
 "11. YB konumları 1. bodrum kat planından aktarılmış olup (*) işaretli inişler 1. bodrum tavanında kolon yüzüne ötelenecek, hiçbir boru betonarme kolon ve perde içinden geçirilmeyecektir.",
 "12. Sarnıç çıkış kotu, bağlantı rögarı ve yağmur suyu kanal kotu belediyeden (İSKİ) alınarak sahada teyit edilecektir.",
]
yy = NY0 - 40
for n in notes:
    T(NX0, yy, n, 12.5, TXT)
    yy -= 28

# ================================================================== EKİPMAN NUMARALARI (plan + şema) ve LİSTE
for n, p in [(1, (247355.0, -489665.0)), (2, (247140.0, -489820.0)), (3, (246815.0, -489645.0)), (4, (247165.0, -489965.0)),
             (5, (247060.0, -489800.0)), (6, (247095.0, -490005.0)), (7, (247490.0, -489740.0)), (8, (247578.0, -489905.0)),
             (9, (247600.0, -489690.0)), (10, (247535.0, -489745.0)), (11, (247515.0, -489885.0)), (12, (247570.0, -489100.0)),
             (13, (247250.0, -490330.0)), (14, (246725.0, -488570.0))]:
    NOB(p, n)
for n, p in [(1, (277850.0, -489815.0)), (2, (277830.0, -490030.0)), (3, (277900.0, -490135.0)), (4, (277885.0, -490005.0)),
             (5, (277805.0, -490090.0)), (6, (277870.0, -490060.0)), (7, (277530.0, -490170.0)), (8, (277420.0, -490110.0)),
             (9, (277310.0, -490090.0)), (10, (277365.0, -490012.0)), (12, (277990.0, -489850.0)), (13, (277085.0, -490180.0)),
             (14, (277215.0, -489935.0))]:
    NOB(p, n, 7.0)
EK = [
 (1, "F1 GİRDAP (VORTEX) FİLTRE", 1, "DN200, elek 0,35 mm, çatı ≥ 750 m², kirli su taşma hattına"),
 (2, "SAKİNLEŞTİRİCİ GİRİŞ", 1, "DN200, depo dibinde yukarı dönük"),
 (3, "YAĞMUR SUYU SARNICI", 1, "Betonarme, iç 3,74 x 5,05 m, h=1,50 m, V ≈ 28 m³"),
 (4, "TAŞMA SİFONU + KEMİRGEN KAPANI", 1, "DN200, cazibe ile YSR rögarına"),
 (5, "YÜZER EMİŞ", 1, "Şamandıralı, süzgeçli, DN40"),
 (6, "HİDROSTATİK SEVİYE SENSÖRÜ (LT)", 1, "4-20 mA, kuru çalışma + takviye kumandası"),
 (7, "SULAMA HİDROFORU (H-YS)", 1, "1 asıl + 1 yedek, 1,5 m³/h, 36 mSS, 0,55 kW"),
 (8, "MEMBRANLI GENLEŞME TANKI", 1, "100 L, PN10, ön basınç 3,4 bar"),
 (9, "KARTUŞ FİLTRE", 1, "100 µm, yıkanabilir"),
 (10, "MANOMETRE", 1, "0-10 bar, gliserinli"),
 (11, "KONTROL PANOSU (KP)", 1, "Hidrofor + seviye + takviye kumandası, alarm"),
 (12, "ŞEBEKE TAKVİYE SELENOİD VANA + AB HAVA BOŞLUĞU", 1, "Ø25, NC, 24 V, TS EN 1717"),
 (13, "YSR YAĞMUR SUYU BAĞLANTI RÖGARI", 1, "Bina dışı, yağmur suyu kanalına gider"),
 (14, "BAHÇE SULAMA VANA KUTUSU", 1, "Ø32 PE100, kilitli, 'YAĞMUR SUYU - İÇİLEMEZ'"),
]
EX0, EY0 = HX0 + 1900.0, PY - 30.0
T(EX0, EY0, "EKİPMAN LİSTESİ (YAĞMUR SUYU SARNICI)", 20, TXT)
ecw = [70, 820, 110, 1050]
exs = [EX0]
for w in ecw: exs.append(exs[-1] + w)
ey = EY0 - 25
rows_e = [("NO", "ADI", "ADEDİ", "ÖZELLİĞİ")] + [(str(a), b, str(c), d) for a, b, c, d in EK]
for i, r in enumerate(rows_e):
    yy = ey - i * 34
    L((exs[0], yy), (exs[-1], yy), "YS-TABLO")
    for j, sv in enumerate(r):
        T(exs[j] + 10, yy - 17, sv, 12.5, "YS-TABLO", TA.MIDDLE_LEFT)
eyb = ey - len(rows_e) * 34
L((exs[0], eyb), (exs[-1], eyb), "YS-TABLO")
for x in exs:
    L((x, ey), (x, eyb), "YS-TABLO")

doc.saveas("/tmp/claude-0/gg/YS_EK2.dxf")
print("ok")
