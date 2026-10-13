# -*- coding: utf-8 -*-
"""SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI (temiz + sıcak + sirkülasyon + pis su TEK şemada) — onaylı MTY bloklu şema tarzı
(gsheet.sihhi_sema): armatürler MTY '... KOLON' blokları (SO/SC/PS öznitelikli), PVC çatal, 45° kolon bağlantısı, MTY çap
blokları (MB/SB), temizleme kapağı, PVC dirsek, kolon no bloğu; vanalar/cihazlar gerçek gösterim + numara."""
import math
from shapely.geometry import Polygon, Point
from veri import *
from tlib import *
from isitma import R
from sihhi import PIS_KOL, inch
from hesap import YB_OFIS, YB_SICAK

PVC = "MTY-PVC"
KAT = "MTY-KAT-ADI"
SEMA = "MTY-SEMA"
SB = dict(WC=10.0, DUS=7.0, LV=2.0, YS=2.0, EV=4.0)
YB = dict(WC=YB_OFIS['klozet'], LV=YB_OFIS['lavabo'], DUS=YB_OFIS['dus'], EV=YB_OFIS['eviye'], YS=0.0)
YBH = dict(LV=YB_SICAK['lavabo'], DUS=YB_SICAK['dus'], EV=YB_SICAK['eviye'])
BLK = dict(WC='KLOZET1 KOLON', LV='LAVABO1 KOLON', DUS='DUS TEKNESI1 KOLON', EV='EVIYE1 KOLON', YS='SUZGEC1 KOLON')
DNP = dict(WC=100, LV=50, DUS=50, EV=50, YS=50)
VN = [0]          # vana numarası sayacı


def fmt(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return s if '.' in s else s + '.0'


def dn_temiz(yb):
    for lim, d in ((2.25, 20), (7.84, 25), (19.36, 32), (46.24, 40), (108.4, 50), (256, 63)):
        if yb <= lim + 1e-9: return d
    return 75


def dn_sb(sb, wc=False):
    for lim, d in ((10, 50), (30, 70), (160, 100), (300, 125), (600, 150)):
        if sb <= lim + 1e-9: return max(d, 100 if wc else 50)
    return 200


def no(p, pre='V', h=5.0, d=(0, 9)):
    NUM[pre] = NUM.get(pre, 0) + 1
    t = f"{pre}-{NUM[pre]:02d}"
    T(p[0] + d[0], p[1] + d[1], t, h, "MTY-VANA", TA.BOTTOM_CENTER, mask=True)
    return t


def V(p, rot=0, cap='DN20', s=0.55, numara=True):
    VANA(p, rot, cap, s, no=numara)


def dline(a, b, r=5.0):
    if abs(a[1] - b[1]) < 1e-6:
        L((a[0], a[1] + r), (b[0], b[1] + r), PVC); L((a[0], a[1] - r), (b[0], b[1] - r), PVC)
    else:
        L((a[0] + r, a[1]), (b[0] + r, b[1]), PVC); L((a[0] - r, a[1]), (b[0] - r, b[1]), PVC)
    PL([a, b], PS, 1.2)


def dl45(a, b, r=5.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy); nx, ny = -dy / l * r, dx / l * r
    L((a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), PVC); L((a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny), PVC)
    PL([a, b], PS, 1.2)


def cap_temiz(p, so=None, socp=None, sc=None, sccp=None, k=6.5, rot=0):
    a = {}
    if so is not None: a.update(SO=so, SOCP=socp)
    if sc is not None: a.update(SC=sc, SCCP=sccp)
    MTYB('MTY-TEMIZ SU CAP MB', p, rot, k, TCAP, a)


def cap_pis(p, ps, pscp, k=6.5, rot=0):
    MTYB('MTY-PIS SU CAP SB', p, rot, k, PSC, {'PS': ps, 'PSCP': pscp})


def havalik(x, y, k=1.4):
    """havalık şapkası (gerçek gösterim): boru ucu + şapka"""
    L((x - 5, y), (x - 5, y + 14 * k), PVC); L((x + 5, y), (x + 5, y + 14 * k), PVC)
    PL([(x - 14 * k, y + 14 * k), (x + 14 * k, y + 14 * k), (x + 9 * k, y + 22 * k), (x - 9 * k, y + 22 * k)], PVC, closed=True)


def fixture_row(x0, y, keys, kol_x, step=120):
    """armatür sırası (kolondan uzaklaşan), pis yatay y-50, 45° çatal ile kolona"""
    xs = []
    for i, k in enumerate(keys):
        x = x0 + i * step
        at = {}
        if YB[k]: at.update(SO=fmt(YB[k]), SOCP='Ø20')
        if k in YBH: at.update(SC=fmt(YBH[k]), SCCP='Ø20')
        at.update(PS='%d' % SB[k], PSCP='Ø%d' % DNP[k])
        MTYB(BLK[k], (x, y), 0, 1.0, CHZ, at)
        MTYB('PVC CATAL SAG', (x, y), 0, 1.0, PVC)
        xs.append(x)
    yp = y - 50
    xr = xs[-1] + 3
    dline((xr, yp), (xr + 30, yp), 5)
    L((xr + 30, yp - 7), (xr + 30, yp + 7), PVC); L((xr + 33, yp - 7), (xr + 33, yp + 7), PVC)
    T(xr + 38, yp - 3, 'T.K.', 6, PSC, TA.BOTTOM_LEFT)
    prev = kol_x + 28
    cum = sum(SB[k] for k in keys)
    dl45((kol_x + 28, yp), (kol_x + 4, yp - 24), 5.0)
    for idx, k in enumerate(keys):
        xa, xb = prev, xs[idx] - 27
        if xb > xa + 1:
            dline((xa, yp), (xb, yp), 5)
            wc = any(DNP[q] >= 100 for q in keys[idx:])
            cap_pis(((xa + xb) / 2, yp + 6), '%d SB' % cum, 'Ø%d' % dn_sb(cum, wc))
        cum -= SB[k]
        prev = xs[idx] + 3
    return xs


def ofis_kolonlari():
    """her pis su kolonu en yakın ofise; ofis -> [(no, kolon dict)]"""
    out = {k: [] for k in OFIS_S1}
    for j, pk in enumerate(PIS_KOL):
        p = Point(pk['kol'])
        k = min(OFIS_S1, key=lambda n: Polygon(OFIS_S1[n]['poly']).distance(p) - (1e-3 if Polygon(OFIS_S1[n]['poly']).contains(p) else 0))
        out[k].append((f"P{j + 1}", pk))
    return out


def sema(X0=258900.0, YT=-440600.0):
    VN[0] = 0
    FH = 1250.0
    yb = YT - 6400.0
    yf = [yb, yb + 1150, yb + 1150 + FH, yb + 1150 + 2 * FH, yb + 1150 + 3 * FH]     # B, Z, 1, 2, ÇATI
    names = ["BODRUM KAT -3,50", "ZEMİN KAT ±0,00", "1. KAT +3,50", "2. KAT +6,50", "ÇATI +9,50"]
    XE = 276550.0
    T((X0 + XE) / 2, yf[-1] + 520, "SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI", 40, TSEMA, TA.BOTTOM_CENTER)
    T((X0 + XE) / 2, yf[-1] + 470, "(TEMİZ SU / SICAK SU / SİRKÜLASYON: TS 1258 YÜK BİRİMİ (MB), PPRC PN20 - PİS SU: SU BİRİMİ (SB), PVC - ÖLÇEKSİZ)",
      13, TSEMA, TA.BOTTOM_CENTER)
    for y, n in zip(yf, names):
        PL([(X0, y), (XE, y)], SEMA)
        T(XE + 30, y + 20, n, 18, KAT, TA.BOTTOM_LEFT, 90)
    # ---------------------------------------------------------- bodrum: kazan dairesi (sığınak içi) ekipmanı
    y0 = yb
    T(X0 + 30, y0 + 1060, "KAZAN DAİRESİ / SU DEPOSU - HİDROFOR (SIĞINAK İÇİ)", 14, CHZ, TA.BOTTOM_LEFT)
    ys = y0 + 160
    PL([(X0 + 20, ys), (X0 + 420, ys)], SS)
    T(X0 + 20, ys + 10, "ŞEBEKEDEN Ø50", 10, TCAP, TA.BOTTOM_LEFT)
    V((X0 + 90, ys), 0, 'DN40', 0.9); PISLIK((X0 + 140, ys), 0, 'DN40', 0.9)
    SAYAC((X0 + 200, ys), 0, 'DN40', 1.0); CEKV((X0 + 260, ys), 0, 'DN40', 0.9)
    T(X0 + 200, ys - 22, "ANA SAYAÇ DN40", 8, SAY, TA.TOP_CENTER)
    # depo D-01
    dx0, dx1, dy0, dy1 = X0 + 460, X0 + 860, y0 + 60, y0 + 420
    PL([(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)], "MTY-CİHAZ", 1.5, True)
    L((dx0 + 8, dy1 - 60), (dx1 - 8, dy1 - 60), CHZ)
    for k in range(4): L((dx0 + 50 + k * 80, dy1 - 70), (dx0 + 80 + k * 80, dy1 - 70), CHZ)
    T((dx0 + dx1) / 2, (dy0 + dy1) / 2 + 20, "D-01 KULLANIM SUYU DEPOSU", 11, CHZ, TA.MIDDLE_CENTER)
    T((dx0 + dx1) / 2, (dy0 + dy1) / 2 - 2, f"V = {R['depo']['Vsec']} m³ (paslanmaz, 2 bölmeli)", 9, CHZ, TA.MIDDLE_CENTER)
    PL([(X0 + 420, ys), (X0 + 420, dy1 - 40), (dx0 + 30, dy1 - 40)], SS)
    INS("Y-SAMANDIRA", (dx0 + 30, dy1 - 40), 0, 0.8, lay=SS); no((dx0 + 30, dy1 - 40), 'ŞV', 4.5, (0, 10))
    PL([(dx0 + 120, dy1), (dx0 + 120, dy1 + 40)], SS); havalik(dx0 + 120, dy1 + 40, 0.9)
    T(dx0 + 135, dy1 + 30, "HAVALIK (SİNEKLİKLİ)", 6, TY, TA.BOTTOM_LEFT)
    PL([(dx1, dy1 - 20), (dx1 + 30, dy1 - 20), (dx1 + 30, dy0 - 40)], SS)
    T(dx1 + 36, dy1 - 20, "TAŞMA Ø50 → POMPA ÇUKURU", 6, TY, TA.MIDDLE_LEFT)
    PL([(dx0 + 40, dy0), (dx0 + 40, dy0 - 40)], SS); V((dx0 + 40, dy0 - 22), 90, 'DN32', 0.7)
    T(dx0 + 50, dy0 - 44, "BOŞALTMA", 6, TY, TA.TOP_LEFT)
    L((dx1 - 20, dy0 + 20), (dx1 - 20, dy1 - 80), CHZ); T(dx1 - 26, dy0 + 30, "SEVİYE GÖST.", 6, CHZ, TA.BOTTOM_LEFT, 90)
    # hidrofor H-01 (2 pompa + membranlı tank MT-01)
    hx0 = X0 + 960
    ye = dy0 + 40
    PL([(dx1, ye), (hx0 + 40, ye)], SS); V((dx1 + 60, ye), 0, 'DN50', 0.8)
    PL([(hx0, y0 + 40), (hx0 + 300, y0 + 40), (hx0 + 300, y0 + 330), (hx0, y0 + 330)], CHZ, closed=True)
    T(hx0 + 150, y0 + 340, f"H-01 HİDROFOR (2 POMPALI, FREKANS KONV.) Q={R['hidrofor'].get('Q', '')} m³/h H={R['hidrofor'].get('Hust', '')} mSS", 7, CHZ, TA.BOTTOM_CENTER)
    PL([(hx0 + 40, ye), (hx0 + 40, ye + 130)], SS); PL([(hx0 + 230, ye), (hx0 + 230, ye + 200)], SS)
    for j, yy in enumerate((ye, ye + 130)):
        PL([(hx0 + 40, yy), (hx0 + 230, yy)], SS)
        V((hx0 + 70, yy), 0, 'DN40', 0.6)
        C((hx0 + 130, yy), 18, CHZ); PL([(hx0 + 130 - 9, yy - 12), (hx0 + 130 - 9, yy + 12), (hx0 + 130 + 15, yy)], CHZ, closed=True)
        T(hx0 + 130, yy - 22, f"HP-0{j + 1}", 6, CHZ, TA.TOP_CENTER)
        CEKV((hx0 + 180, yy), 0, 'DN40', 0.6)
        V((hx0 + 210, yy), 0, 'DN40', 0.6)
    # membranlı tank
    mx = hx0 + 270
    PL([(hx0 + 230, ye + 200), (mx, ye + 200), (mx, ye + 160)], SS)
    PL([(mx - 22, ye + 160), (mx + 22, ye + 160), (mx + 22, ye + 60), (mx - 22, ye + 60)], CHZ, closed=True)
    L((mx - 22, ye + 110), (mx + 22, ye + 110), CHZ)
    T(mx, ye + 52, f"MT-01 {R['hidrofor']['Vn']} L", 6, CHZ, TA.TOP_CENTER)
    C((hx0 + 250, ye + 215), 6, CHZ); L((hx0 + 250, ye + 200), (hx0 + 250, ye + 209), CHZ); no((hx0 + 250, ye + 215), 'M', 4.5, (0, 8))
    # yumuşatma YC-01 -> SS ana + boyler soğuk besleme
    yx = hx0 + 400
    PL([(hx0 + 230, ye + 200), (hx0 + 230, ye + 260), (yx - 20, ye + 260)], SS)
    PL([(yx - 20, ye + 220), (yx + 20, ye + 220), (yx + 20, ye + 320), (yx - 20, ye + 320)], CHZ, closed=True)
    C((yx, ye + 290), 12, CHZ); T(yx, ye + 330, "YC-01 YUMUŞATMA", 6, CHZ, TA.BOTTOM_CENTER)
    yss = y0 + 860; yhs = y0 + 890; ysr = y0 + 920       # bodrum tavanı ana dağıtım kotları (şema)
    PL([(yx + 20, ye + 260), (yx + 80, ye + 260), (yx + 80, yss), (276300, yss)], SS)
    V((yx + 80, ye + 300), 90, 'DN50', 0.8)
    # boyler B-01
    bx = X0 + 1900
    PL([(yx + 80, ye + 260), (bx - 140, ye + 260), (bx - 140, y0 + 120), (bx - 60, y0 + 120)], SS)
    V((bx - 140, ye + 200), 90, 'DN32', 0.6); CEKV((bx - 100, y0 + 120), 0, 'DN32', 0.6)
    PL([(bx - 60, y0 + 60), (bx + 60, y0 + 60), (bx + 60, y0 + 560), (bx - 60, y0 + 560)], CHZ, closed=True)
    for k in range(5):
        a = y0 + 150 + k * 30
        PL([(bx - 45, a), (bx + 45, a + 15)], "MTY-ISITMA-GIDIS-BORU")
    T(bx, y0 + 470, "B-01", 10, CHZ, TA.MIDDLE_CENTER); T(bx, y0 + 450, f"BOYLER {R['boyler']['Vsec']} L", 8, CHZ, TA.MIDDLE_CENTER)
    T(bx, y0 + 432, "ÇİFT SERPANTİNLİ", 6, CHZ, TA.MIDDLE_CENTER)
    PL([(bx + 60, y0 + 160), (bx + 140, y0 + 160)], IG); PL([(bx + 60, y0 + 140), (bx + 140, y0 + 140)], ID)
    T(bx + 145, y0 + 150, "KAZANDAN 75/55 °C (ISITMA ŞEMASI)", 6, TY, TA.MIDDLE_LEFT)
    # emniyet + termometre
    PL([(bx + 60, y0 + 520), (bx + 100, y0 + 520), (bx + 100, y0 + 545)], SIS); INS("Y-EMNIYET", (bx + 100, y0 + 545), 0, 0.8, lay=SIS)
    no((bx + 100, y0 + 545), 'EV', 4.5, (14, 0)); C((bx - 75, y0 + 400), 7, CHZ); no((bx - 75, y0 + 400), 'TM', 4.5, (0, 10))
    # sıcak çıkış (karışım vanası) + sirkülasyon dönüşü (pompa SP-01)
    PL([(bx, y0 + 560), (bx, yhs), (276300, yhs)], SIS)
    C((bx, y0 + 640), 12, CHZ); T(bx + 16, y0 + 640, "TKV-01 TERMOSTATİK KARIŞIM VANASI 60 °C", 6, CHZ, TA.MIDDLE_LEFT)
    PL([(276300, ysr), (bx + 40, ysr), (bx + 40, y0 + 480), (bx + 60, y0 + 480)], SIRK)
    C((bx + 40, y0 + 720), 12, CHZ); PL([(bx + 40 - 8, y0 + 712), (bx + 40 + 8, y0 + 712), (bx + 40, y0 + 730)], CHZ, closed=True)
    T(bx + 56, y0 + 720, f"SP-01 SİRKÜLASYON POMPASI", 6, CHZ, TA.MIDDLE_LEFT)
    CEKV((bx + 40, y0 + 680), 90, 'DN25', 0.6); V((bx + 40, y0 + 770), 90, 'DN25', 0.6)
    T(X0 + 2300, yss + 8, "SOĞUK SU ANA HAT (BODRUM TAVANI)", 7, TCAP, TA.BOTTOM_LEFT)
    T(X0 + 2300, yhs + 8, "SICAK SU ANA HAT", 7, TCAP, TA.BOTTOM_LEFT)
    T(X0 + 2300, ysr + 8, "SİRKÜLASYON ANA HAT", 7, TCAP, TA.BOTTOM_LEFT)
    # ---------------------------------------------------------- gruplar (ofisler) ve şaftlar
    order = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'D3', 'E1', 'E2']
    GX0 = X0 + 3000
    GW = 960.0
    gx = {k: GX0 + 300 + i * GW + (240 if i >= 6 else 0) for i, k in enumerate(order)}
    sx = {'S1': GX0 + 60, 'S2': GX0 + 300 + 6 * GW + 60}
    KO = ofis_kolonlari()
    nS = {sh: sum(1 for k in OFIS_S1 if SAFT_OF[k] == sh) for sh in sx}
    from sihhi import YB_S, YB_H
    for sh, x in sx.items():
        n2 = nS[sh] * 2
        for lay, dx, yy, yb_, lbl in ((SS, 0, yss, YB_S, 'SS'), (SIS, 16, yhs, YB_H, 'SıS'), (SIRK, 32, ysr, 0, 'SİRK')):
            top = yf[3] + 300 + dx * 0.6
            PL([(x + dx, yy), (x + dx, top)], lay)
            V((x + dx, yy + 60), 90, 'DN40', 0.6, numara=(dx == 0))
            if yb_:
                tot = n2 * yb_
                cap_temiz((x + dx - 8, yf[1] + 500), so=f"{fmt(tot)} MB", socp=f"Ø{dn_temiz(tot)}", k=6.5, rot=90)
        T(x - 20, yf[1] + 250, f"Ş{sh[1]} TESİSAT ŞAFTI (SS / SıS / SİRK)", 9, SFT, TA.BOTTOM_LEFT, 90)
        L((x + 32, yf[3] + 320), (x + 32, yf[3] + 340), SIRK)
        T(x + 40, yf[3] + 330, "OTOMATİK PÜRJÖR", 6, TY, TA.MIDDLE_LEFT)
    # kat dağıtımı (ofis dolaplarına) — her kat bandında şaft -> dolaplar
    for fi in (2, 3):
        y = yf[fi]
        kat = fi
        for sh, x in sx.items():
            offs = [k for k in order if SAFT_OF[k] == sh]
            xe = gx[offs[-1]] + 40
            for lay, dx, yy in ((SS, 0, y + 330), (SIS, 16, y + 350), (SIRK, 32, y + 370)):
                PL([(x + dx, yy), (xe + (60 if lay == SIRK else 0), yy)], lay)
            # sirk: son dolaptan sonra sıcak ile birleşir (termostatik sirkülasyon vanası)
            PL([(xe, y + 350), (xe + 60, y + 350), (xe + 60, y + 370)], SIS)
            C((xe + 60, y + 360), 5, CHZ); no((xe + 60, y + 360), 'TSV', 4.5, (14, 0))
        for k in order:
            x = gx[k]
            # dolap SD (sayaçlar) — soğuk + sıcak
            PL([(x - 10, y + 175), (x + 90, y + 175), (x + 90, y + 395), (x - 10, y + 395)], SAY, closed=True)
            T(x + 40, y + 400, f"SD-{kat - 1}{k}", 8, SAY, TA.BOTTOM_CENTER)
            for lay, xx, yy in ((SS, x + 20, y + 330), (SIS, x + 60, y + 350)):
                PL([(xx, yy), (xx, y + 140 if lay == SS else y + 155)], lay)
                V((xx, yy - 25), 90, 'DN20', 0.5)
                SAYAC((xx, yy - 60), 90, 'DN20', 0.55)
                CEKV((xx, yy - 95), 90, 'DN20', 0.5)
            # armatür sıraları ve pis su kolonları
            ks = KO[k]
            k100 = [q for q in ks if q[1]['cap'] == 'Ø100'] or ks
            k50 = [q for q in ks if q[1]['cap'] == 'Ø50']
            rows = []
            if k50:
                rows.append((x + 160, ['WC', 'LV', 'DUS', 'YS'], k100[0] if k100 else k50[0]))
                rows.append((x + 700, ['EV'], k50[0]))
            else:
                rows.append((x + 160, ['WC', 'LV', 'DUS', 'YS', 'EV'], k100[0] if k100 else None))
            allx, allk = [], []
            for kx, keys, kol in rows:
                xs_ = fixture_row(kx + 120, y, keys, kx)
                allx += xs_; allk += keys
            # soğuk / sıcak dağıtım + çap etiketleri
            xmax = max(allx) + 5
            PL([(x + 20, y + 140), (xmax, y + 140)], SS)
            hx = [q for q, kk in zip(allx, allk) if kk in YBH]
            PL([(x + 60, y + 155), (max(hx) + 15, y + 155)], SIS)
            pts = sorted(zip(allx, allk))
            for a, b in zip([x + 20] + [p[0] for p in pts], [p[0] for p in pts]):
                dn = [kk for q, kk in pts if q >= b - 1]
                yb_ = sum(YB[kk] for kk in dn); ybh = sum(YBH.get(kk, 0) for kk in dn)
                if b - a > 60 and yb_ > 0:
                    cap_temiz(((a + b) / 2, y + 162), so=f"{fmt(yb_)} MB", socp=f"Ø{dn_temiz(yb_)}",
                              sc=(f"{fmt(ybh)} MB" if ybh else None), sccp=(f"Ø{dn_temiz(ybh)}" if ybh else None))
    # pis su kolonları (1. ve 2. kat aynı aks; bodrum tavanından bina dışı rögara)
    for k in order:
        x = gx[k]
        ks = KO[k]
        k100 = [q for q in ks if q[1]['cap'] == 'Ø100'] or ks
        k50 = [q for q in ks if q[1]['cap'] == 'Ø50']
        rows = [(x + 160, ['WC', 'LV', 'DUS', 'YS'], k100[0] if k100 else None), (x + 700, ['EV'], k50[0])] if k50 else \
               [(x + 160, ['WC', 'LV', 'DUS', 'YS', 'EV'], k100[0] if k100 else None)]
        for kx, keys, kol in rows:
            if kol is None: continue
            nm = kol[0]
            sbk = sum(SB[q] for q in keys)
            dk = dn_sb(2 * sbk, 'WC' in keys)
            top = yf[4] + 110
            ybot = yf[1] - 60
            dline((kx, ybot), (kx, top), 5)
            havalik(kx, top, 1.4)
            T(kx + 12, yf[4] + 40, f"HAVALIK Ø{dk} (ÇATIDAN 50 cm YUKARI)", 6, PSC, TA.BOTTOM_LEFT, 90)
            MTYB('MTY-KOLON NO PIS SU', (kx, top + 75), 0, 1.0, PSN, {'K': nm})
            for fi, mult in ((2, 2), (3, 1)):                   # kat bandı içinde kolon yanında kümülatif SB (onaylı şema düzeni)
                T(kx - 12, yf[fi] + 40, f"Ø{dk} / {fmt(sbk * mult)} SB", 8, PSC, TA.BOTTOM_LEFT, 90, mask=True)
            T(kx - 12, yf[1] + 300, f"Ø{dk} / {fmt(sbk * 2)} SB (ZEMİN ASMA TAVANI)", 8, PSC, TA.BOTTOM_LEFT, 90, mask=True)
            MTYB('MTY-TEMIZLEME KAPAGI KOLON', (kx, ybot + 55), 0, 0.8, PSC, {'TK': 'T.K.'})
            MTYB('PVC DIRSEK', (kx, ybot), 0, 1.0, PVC)
            dline((kx + 20, ybot - 26), (kx + 120, ybot - 26), 5)
            T(kx + 125, ybot - 26, "→ BİNA DIŞI RÖGAR", 6, ROG, TA.MIDDLE_LEFT)
    # zemin: dükkân bekleme uçları (bodrum tavanından)
    xs_d = [GX0 + 300 + i * 1500 for i in range(5)]
    for i, (nm, x) in enumerate(zip(DUKKAN_S, xs_d)):
        x = x + 400
        y = yf[1]
        PL([(x, yss), (x, y + 140), (x + 140, y + 140)], SS)
        V((x, y - 60), 90, 'DN20', 0.5)
        SAYAC((x, y + 60), 90, 'DN20', 0.55)
        PL([(x - 20, y + 20), (x + 20, y + 20), (x + 20, y + 110), (x - 20, y + 110)], SAY, closed=True)
        V((x + 140, y + 140), 0, 'DN20', 0.5)
        L((x + 150, y + 132), (x + 150, y + 148), SS)
        T(x + 160, y + 140, f"{nm} - SD-Z{nm[-1]} - BEKLEME UCU 3/4\" (VANALI, KÖR TAPALI)", 7, TY, TA.MIDDLE_LEFT)
        cap_temiz((x - 10, y - 200), so="1.0 MB", socp="Ø20", rot=90)
    return yf


def ekipman_listesi(x, y):
    """numaralı ekipman listesi (sıhhi)"""
    rows = [("D-01", "KULLANIM SUYU DEPOSU", f"{R['depo']['Vsec']} m³, paslanmaz, 2 bölmeli"),
            ("H-01", "HİDROFOR (HP-01/02)", f"2 pompalı, frekans konvertörlü"),
            ("MT-01", "MEMBRANLI BASINÇ TANKI", f"{R['hidrofor']['Vn']} L, 10 bar"),
            ("YC-01", "SU YUMUŞATMA CİHAZI", "otomatik rejenerasyonlu"),
            ("B-01", "BOYLER", f"{R['boyler']['Vsec']} L çift serpantinli"),
            ("TKV-01", "TERMOSTATİK KARIŞIM VANASI", "60 °C, lejyonella şoku için by-pass"),
            ("SP-01", "SİRKÜLASYON POMPASI", "ıslak rotorlu, zaman saatli"),
            ("V-xx", "KÜRESEL VANA", "şemada numaralı"), ("CV-xx", "ÇEK VALF", "şemada numaralı"),
            ("SY-xx", "SU SAYACI", "ofis/dükkân dolaplarında (soğuk + sıcak)"), ("TSV-xx", "TERMOSTATİK SİRKÜLASYON VANASI", "kat hattı sonu"),
            ("PT/ŞV/EV/M/TM", "PİSLİK TUTUCU / ŞAMANDIRALI VANA / EMNİYET VENTİLİ / MANOMETRE / TERMOMETRE", "")]
    import sema_tes
    return sema_tes.tablo(x, y, "SIHHİ TESİSAT EKİPMAN LİSTESİ", ("NO", "EKİPMAN", "ÖZELLİK"), rows, [220, 900, 700])
