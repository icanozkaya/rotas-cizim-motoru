"""Revizyon 2 - kolon şemaları, lejant, notlar, antet, tablolar, paftalar."""
import math
import cad
from cad import *
import mtyblk
import cg2_build as B
import cg2_heat as H
import cg2_geo as G

CS, CH, PS, YZ, CD, VN = B.CS, B.CH, B.PS, B.YZ, B.CD, B.VN
TSC, PSC, YBL = B.TSC, B.PSC, B.YB
PVC = 'MTY-PVC'
RED = 'MTY-KAT-ADI'


def dl45(a, b, r=5.0):
    """eğik çift çizgili boru"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy)
    nx, ny = -dy / l * r, dx / l * r
    L((a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), PVC); L((a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny), PVC)
    L(a, b, PS)


def dline(a, b, r=5.0):
    """çift çizgili PVC boru (yatay/dikey) + eksen"""
    if abs(a[1] - b[1]) < 1e-6:
        L((a[0], a[1] + r), (b[0], b[1] + r), PVC); L((a[0], a[1] - r), (b[0], b[1] - r), PVC)
    else:
        L((a[0] + r, a[1]), (b[0] + r, b[1]), PVC); L((a[0] - r, a[1]), (b[0] - r, b[1]), PVC)
    L(a, b, PS)


# ================================================================== SIHHİ KOLON ŞEMASI (MTY görünüş blokları)
FIXS = [  # (anahtar, blok, x ofset, so, sc, sb, pis çap, grup)
    ('LV', 'LAVABO1 KOLON', 560, 0.5, 0.5, 2, 50, 'B'),
    ('DUS', 'DUS TEKNESI1 KOLON', 720, 1.0, 1.0, 7, 50, 'B'),
    ('WC', 'KLOZET1 KOLON', 880, 0.5, None, 10, 100, 'B'),
    ('CM', 'CAMASIR MAKINASI1 KOLON', 1020, 1.0, None, 4, 50, 'B'),
    ('YS', 'YER SUZGECI DN501 KOLON', 1130, None, None, 2, 50, 'B'),
    ('EV', 'EVIYE1 KOLON', 1380, 0.5, 0.5, 4, 50, 'M'),
    ('BM', 'BULASIK MAKINASI1 KOLON', 1530, 1.0, None, 4, 50, 'M'),
]
X_PK, X_MK, X_KOMBI = 440, 1270, 1700


def sihhi_sema(ox, oy):
    T((ox + 1000, oy + 1655), 'SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI', 26, YZ, 'C')
    T((ox + 1000, oy + 1630), '(TEMİZ SU: TS 1258 YÜK BİRİMİ (YB), PPRC PN20 - PİS SU: SU BİRİMİ (SB) ROTAŞ ÖRNEK ŞEMA DEĞERLERİ, PVC)', 9, YZ, 'C')
    FH = 320.0
    yf = [oy + 470 + i * FH for i in range(4)]       # zemin, 1, 2, çatı döşemesi
    names = ['ZEMİN KAT (+1.00)', '1. KAT (+4.00)', '2. KAT (+7.00)', 'ÇATI ARASI (+10.00)']
    for i in range(4):
        L((ox + 60, yf[i]), (ox + 1940, yf[i]), 'MTY-SEMA')
        T((ox + 1965, yf[i] + 20), names[i], 15, RED, 'L', 90)
    xs = lambda dx: ox + dx
    # ---- depo (çatı arası)
    dx0, dy0 = xs(200), yf[3] + 30
    DW, DH = 200, 120
    RECT(dx0, dy0, dx0 + DW, dy0 + DH, 'RAST-TEM-SU DEPOSU')
    T((dx0 + 100, dy0 + 80), 'KULLANMA SUYU DEPOSU', 9, YZ, 'C')
    T((dx0 + 100, dy0 + 64), 'V = 3,00 m³ (PE, ŞAMANDIRALI)', 8, YZ, 'C')
    T((dx0 + 100, dy0 + 50), '3 DAİRE ≤ 10 → 3 m³', 7, YZ, 'C')
    L((dx0 + 60, dy0 + DH), (dx0 + 60, dy0 + DH + 22), CS); HAVALIK_SAPKA((dx0 + 60, dy0 + DH + 22), 0.8, CS)
    T((dx0 + 72, dy0 + DH + 24), 'HAVALIK', 6, YZ, 'L')
    L((dx0 + 185, dy0 + 10), (dx0 + 185, dy0 + 100), YZ); T((dx0 + 180, dy0 + 20), 'SEVİYE GÖST.', 5.5, YZ, 'L', 90)
    # DBK giriş (üstten, şamandıralı), ADK çıkış (alttan)
    xd, xa = xs(90), xs(115)
    L((xd, dy0 + 100), (dx0 + 30, dy0 + 100), CS); SAMANDIRALI_VANA((dx0 + 36, dy0 + 100), 0.9)
    # taşma / boşaltma -> birleşik Ø40 -> YB2 yağmur inişi (depo üstünden, PK1 kolonuna değmeden)
    xt = dx0 + DW + 10
    yt = dy0 + DH + 18
    xyb = dx0 + 150
    L((dx0 + DW, dy0 + 6), (xt, dy0 + 6), CS); L((xt, dy0 + 6), (xt, yt), CS)
    VANA((xt, dy0 + 30), 0.7, 90)
    L((dx0 + DW, dy0 + 105), (xt, dy0 + 105), CS); C((xt, dy0 + 105), 1.5, CS)
    L((xt, yt), (xyb, yt), CS); C((xyb, yt), 1.5, CS)
    L((xyb, yt + 30), (xyb, dy0 + DH + 4), B.YL)
    T((xyb + 5, yt + 20), 'YB2 YAĞMUR İNİŞİ Ø100', 6, B.YC, 'L')
    T((xyb + 4, yt - 9), 'TAŞMA Ø40/BOŞ.Ø32', 5, TSC, 'L')
    # ---- DBK (şebeke -> depo) / ADK (depo -> zemin sayaç grubu)
    ysb = oy + 330
    yk = yf[0] + 40                       # sayaç kollektörü (zemin, bina girişi)
    L((xd, ysb), (xd, dy0 + 100), CS)
    L((xa, dy0 + 10), (xa, yk), CS)
    L((xa, dy0 + 10), (dx0, dy0 + 10), CS)
    VANA((xa, dy0 - 15), 0.8, 90)
    B.cap_temiz((xd, yf[2] + 200), 90, so='DBK', socp='Ø32', k=7)
    B.cap_temiz((xa, yf[2] + 60), 90, so='ADK 13.5 YB', socp='Ø32', k=7)
    # şebeke + ana sayaç
    L((xs(40), ysb), (xd, ysb), CS)
    VANA((xs(50), ysb), 0.7); PISLIK_TUTUCU((xs(62), ysb), 0.7); mtyblk.insert('MTY-SU SAYACI', (xs(75), ysb), 0, 0.8)
    CEKVALF((xs(84), ysb), 0.6)
    T((xs(40), ysb - 25), 'ŞEBEKEDEN (SASKİ) Ø32 - ANA SAYAÇ (BİNA GİRİŞİ NİŞİ)', 7.5, TSC, 'L')
    T((xs(40), ysb - 37), 'KÜRESEL VANA + PİSLİK TUTUCU + SAYAÇ + ÇEK VALF', 6.5, VN, 'L')
    # sayaç kollektörü + 3 daire sayacı (zemin - bina girişi)
    XR = {3: xs(170), 2: xs(210), 1: xs(250)}
    L((xa, yk), (XR[1], yk), CS)
    RECT(xs(140), yk - 22, xs(275), yk + 80, VN)
    T((xs(140), yk - 32), 'SAYAÇ GRUBU - BİNA GİRİŞİ (ZEMİN MERDİVEN HOLÜ)', 6.5, VN, 'L')
    T((xs(140), yk - 41), 'SAYAÇ KOLLEKTÖRÜ Ø32 / 13.5 YB', 6, TSC, 'L')
    for d in (1, 2, 3):
        x = XR[d]
        L((x, yk), (x, yf[d - 1] + 130), CS)
        VANA((x, yk + 14), 0.6, 90); mtyblk.insert('MTY-SU SAYACI', (x, yk + 34), 90, 0.7); CEKVALF((x, yk + 54), 0.55, 90)
        T((x + 9, yk + 66), 'D%d' % d, 6.5, VN, 'L')
        if d > 1:
            B.cap_temiz((x, yf[d - 2] + 230 if d == 2 else yf[1] + 200), 90, so='D%d 4.5 YB' % d, socp='Ø25', k=6.5)
    # ---- her kat
    for i in range(3):
        y = yf[i]
        dno = i + 1
        yc = y + 130
        L((XR[dno], yc), (xs(X_KOMBI), yc), CS)
        VANA((xs(300), yc), 0.7)
        T((xs(290), yc - 22), 'DAİRE %d GİRİŞ VANASI' % dno, 6, VN, 'L')
        # sıcak hat: kombi -> lavabo
        L((xs(X_KOMBI) - 15, y + 135), (xs(560) - 15, y + 135), CH)
        # armatür blokları
        for key, blk, dx, so, sc, sb, dn, gr in FIXS:
            at = {}
            if so:
                at.update(SO='%s' % B.fmt(so), SOCP='Ø20')
            if sc:
                at.update(SC='%s' % B.fmt(sc), SCCP='Ø20')
            at.update(PS='%d' % sb, PSCP='Ø%d' % dn)
            mtyblk.insert(blk, (xs(dx), y), 0, 1.0, attrs=at)
            # pis çatal
            mtyblk.insert('PVC CATAL SAG', (xs(dx), y), 0, 1.0)
        mtyblk.insert('KOMBI1 KOLON', (xs(X_KOMBI), y), 0, 1.0, attrs={'SO': B.fmt(B.YB_SICAK), 'SOCP': 'Ø20', 'SC': B.fmt(B.YB_SICAK), 'SCCP': 'Ø20'})
        for j, s in enumerate(B.KOMBI_SPEC):
            T((xs(X_KOMBI) - 300, y + 252 - j * 9), s, 6, CD, 'L')
        T((xs(X_KOMBI) + 25, y + 215), 'H. KOMBİ 24 kW', 8, CD, 'L')
        C((xs(1865), y + 230), 40, 'MTY-PISSU-KOLONNO'); C((xs(1865), y + 230), 36, 'MTY-PISSU-KOLONNO')
        T((xs(1865), y + 230), 'D%d' % dno, 30, 'MTY-PISSU-KOLONNO', 'MC')
        # temiz su çap etiketleri (her parça)
        pos = [xs(dx) for k_, blk, dx, so, sc, sb, dn, gr in FIXS if so]
        names = [k_ for k_, blk, dx, so, sc, sb, dn, gr in FIXS if so]
        yb_of = {k_: so for k_, blk, dx, so, sc, sb, dn, gr in FIXS if so}
        hot_set = {'LV', 'DUS', 'EV'}
        pts = [xs(310)] + pos + [xs(X_KOMBI)]
        for a, b in zip(pts[:-1], pts[1:]):
            mid = (a + b) / 2
            down = [n for n, p in zip(names, pos) if p > a + 1]
            served = set(down) | hot_set
            yb = sum(yb_of[n] for n in served)
            hot_served = [n for n, p in zip(names, pos) if p - 15 < mid and n in hot_set]
            ybh = sum(yb_of[n] for n in hot_served)
            kw = dict(so='%s YB' % B.fmt(yb), socp='Ø%d' % B.dn_temiz(yb))
            if ybh > 0 and mid > xs(560) - 15:
                kw.update(sc='%s YB' % B.fmt(ybh), sccp='Ø%d' % B.dn_temiz(ybh))
            B.cap_temiz((mid, y + 135), 0, k=6.5, **kw)
        # pis yatay hatlar (döşeme altı, y-50) - banyo -> PK ; mutfak -> MK
        for grp, xk in (('B', X_PK), ('M', X_MK)):
            fx = [(dx, sb, dn) for k_, blk, dx, so, sc, sb, dn, gr in FIXS if gr == grp]
            yp = y - 50
            # sağ uç temizleme kapağı
            xr = xs(fx[-1][0]) + 3
            dline((xr, yp), (xr + 30, yp), 5)
            L((xr + 30, yp - 7), (xr + 30, yp + 7), PVC); L((xr + 33, yp - 7), (xr + 33, yp + 7), PVC)
            T((xr + 38, yp - 3), 'TEMİZLEME KAPAĞI', 5.5, PSC, 'L')
            # parçalar
            prev = xs(xk) + 28
            cum = sum(f[1] for f in fx)
            # kolona 45° çatal (dirsek) ile bağlantı
            r_ = 5.0
            dl45((xs(xk) + 28, yp), (xs(xk) + 4, yp - 24), r_)
            for idx, (dx, sb, dn) in enumerate(fx):
                xa_ = prev
                xb_ = xs(dx) - 27
                dline((xa_, yp), (xb_, yp), 5)
                dmin = max(f[2] for f in fx[idx:])
                d = B.dn_sb(cum, dmin >= 100)
                B.cap_pis(((xa_ + xb_) / 2, yp + 6), 0, '%d SB' % cum, 'Ø%d' % d, 6.5)
                cum -= sb
                prev = xs(dx) + 3
    # ---- pis su kolonları
    for nm, xk, sbf, dk in (('PK1', X_PK, B.SB_BANYO, 100), ('MK1', X_MK, B.SB_MUTFAK, 70)):
        x = xs(xk)
        ybot = yf[0] - 130
        top = yf[3] + 110
        dline((x, ybot), (x, top), 5)
        mtyblk.insert('MTY-KOLON HAVALIK SAPKASI', (x, top), 0, 1.6)
        T((x + 12, yf[3] + 60), 'HAVALIK Ø%d (ÇATIDAN 50 cm YUKARI)' % dk, 6, PSC, 'L', 90)
        mtyblk.insert('MTY-PIS SU KOLON NO', (x, top + 70), 0, 1.0, attrs={'K': nm})
        for i in range(3):
            T((x - 12, yf[i] + 40), 'Ø%d / %d SB' % (dk, sbf * (3 - i)), 8, PSC, 'L', 90)
        mtyblk.insert('MTY-TEMIZLEME KAPAGI KOLON', (x, yf[0] - 95), 0, 0.8, attrs={'TK': 'T.K.'})
        # kolon dibi dirsek -> temel altı
        mtyblk.insert('PVC DIRSEK', (x, ybot), 0, 1.0)
    # temel altı toplayıcı -> R1 -> PB
    yb_ = yf[0] - 150.5
    dline((xs(X_PK) + 20, yb_), (xs(X_MK) - 5, yb_), 6)
    B.cap_pis(((xs(X_PK) + xs(X_MK)) / 2, yb_ + 7), 0, '%d SB' % (3 * B.SB_BANYO), 'Ø100', 7)
    dline((xs(X_MK) + 20, yb_), (xs(1640), yb_), 7.5)
    B.cap_pis((xs(1450), yb_ + 9), 0, '%d SB' % (3 * (B.SB_BANYO + B.SB_MUTFAK)), 'Ø100', 7)
    T((xs(X_MK) - 60, yb_ - 25), 'MK1 TEMEL ALTI: Ø100 / %d SB' % (3 * B.SB_MUTFAK), 6.5, PSC, 'L')
    mtyblk.insert('PVC ROGAR', (xs(1640), yb_), 0, 1.0)
    T((xs(1700), yb_ - 4), 'R1 → PB → SASKİ ATIKSU HATTI  (TEMEL ALTI %1)', 8, 'MTY-ROGAR', 'L')


# ================================================================== YAĞMUR SUYU ŞEMASI + HESAP
def yagmur_sema(ox, oy):
    YL, YC = B.YL, B.YC
    T((ox + 625, oy + 1655), 'YAĞMUR SUYU KOLON ŞEMASI VE HESABI', 24, YZ, 'C')
    FH = 320.0
    yf = [oy + 470 + i * FH for i in range(4)]
    names = ['ZEMİN KAT (+1.00)', '1. KAT (+4.00)', '2. KAT (+7.00)', 'ÇATI (+10.00)']
    for i in range(4):
        L((ox + 60, yf[i]), (ox + 1190, yf[i]), 'MTY-SEMA')
        T((ox + 70, yf[i] + 8), names[i], 11, YZ, 'L')
    ytop = yf[3] + 120
    L((ox + 150, ytop), (ox + 820, ytop), YL)
    T((ox + 150, ytop + 10), 'YAĞMUR OLUĞU (KUZEY / BATI / GÜNEY SAÇAKLARI)', 8, YC, 'L')
    for j, nm in enumerate(B.YB_PTS):
        x = ox + 220 + j * 180
        L((x, ytop), (x, yf[0] - 80), YL)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (x, ytop + 55), 0, 0.9, attrs={'K': nm})
        for i in range(3):
            T((x - 10, yf[i] + 60), '%s - Ø100 PVC' % nm, 8, YC, 'L', 90)
        L((x, yf[0] - 80), (x + 40, yf[0] - 80), YL); ARROW((x + 46, yf[0] - 80), 0, YL, 10)
        if nm == 'YB2':
            yd = yf[3] + 60
            L((x - 110, yd), (x, yd), CS); RECT(x - 140, yd - 15, x - 110, yd + 15, 'RAST-TEM-SU DEPOSU')
            T((x - 105, yd + 5), 'DEPO TAŞMA Ø40 + BOŞALTMA Ø32', 5.5, TSC, 'L')
        T((x - 10, yf[0] - 110), 'YAĞMUR SUYU', 6.5, YC, 'L')
        T((x - 10, yf[0] - 120), 'KANALINA GİDER', 6.5, YC, 'L')
    h = B.yagmur_hesap()
    x, y = ox + 860, yf[2] + 200
    T((x, y), 'YAĞMUR İNİŞ BORUSU ÇAP HESABI', 11, 'MTY-HESAP', 'L')
    rows = [('P', 'Çatı alanı (yatay izdüşüm)', '%.2f m²' % h['P']),
            ('S', 'P x 0,75 / 1', '%.2f cm²' % h['S']),
            ('f', 'İniş borusu adedi', '%d' % h['f']),
            ('A', 'S / f', '%.2f cm²' % h['A']),
            ('D', '1,13 x √A', '%.2f cm' % h['D'])]
    for i, (a, b_, c) in enumerate(rows):
        T((x, y - 22 - i * 16), '%s = %s' % (a, b_), 8, 'MTY-HESAP', 'L')
        T((x + 230, y - 22 - i * 16), '= %s' % c, 8, 'MTY-HESAP', 'L')
    T((x, y - 22 - 5 * 16 - 6), 'D = %.2f cm < 7 cm → Ø70\'lik boru UYGUNDUR.' % h['D'], 8, 'MTY-HESAP', 'L')
    T((x, y - 22 - 6 * 16 - 6), 'Uygulamada 4 x Ø100 PVC iniş borusu seçilmiştir.', 8, 'MTY-HESAP', 'L')
    nts = ['Yağmur suları pis su tesisatına bağlanmayacaktır.',
           'İniş boruları cepheye kelepçe ile tespit edilecektir.',
           'İniş dipleri parsel yağmur suyu kanalına verilecektir.',
           'Oluklar iniş yönüne %0,5 eğimle yapılacaktır.']
    for i, n in enumerate(nts):
        T((x, y - 160 - i * 14), '%d. %s' % (i + 1, n), 7, YZ, 'L')
    return h


# ================================================================== YERDEN ISITMA KOLON ŞEMASI
def isitma_sema(ox, oy, HEAT):
    T((ox + 1000, oy + 1645), 'YERDEN ISITMA KOLON ŞEMASI', 26, YZ, 'C')
    T((ox + 1000, oy + 1615), '(HER DAİREDE 1 ADET 24 kW HERMETİK YOĞUŞMALI KOMBİ - KOLLEKTÖR - PEX 16x2,0 DEVRELER, 50/40 °C)', 9, YZ, 'C')
    for k in range(3):
        y = oy + 280 + k * 470
        L((ox + 60, y), (ox + 1940, y), 'MTY-SEMA')
        T((ox + 1965, y + 20), B.FLOORS[k][1], 15, RED, 'L', 90)
        res, tot, calc = HEAT[k]
        kx = ox + 150
        RRECT(kx, y + 150, kx + 70, y + 270, 5, CD); C((kx + 35, y + 215), 14, CD)
        T((kx + 35, y + 285), 'H. KOMBİ 24 kW', 9, CD, 'C')
        for j, s in enumerate(B.KOMBI_SPEC):
            T((kx - 80, y + 380 - j * 10), s, 6.5, CD, 'L')
        T((kx + 35, y + 130), 'DAİRE %d' % (k + 1), 12, YZ, 'C')
        n = len(res)
        c0 = kx + 220
        c1 = c0 + n * 220
        RECT(c0 - 15, y + 160, c1 + 15, y + 210, 'MTY-KOLLETOR')
        L((c0 - 10, y + 198), (c1 + 10, y + 198), B.HGL)
        L((c0 - 10, y + 172), (c1 + 10, y + 172), B.HDL)
        T(((c0 + c1) / 2, y + 140), 'KOLLEKTÖR %d AĞIZLI (DEBİMETRELİ, GİDİŞ/DÖNÜŞ VANALI, OTOMATİK PURJÖRLÜ)' % n, 7, 'MTY-KOLLETOR', 'C')
        PL([(kx + 70, y + 240), (c0 - 30, y + 240), (c0 - 30, y + 198), (c0 - 10, y + 198)], B.HGL)
        PL([(kx + 70, y + 180), (c0 - 40, y + 180), (c0 - 40, y + 172), (c0 - 10, y + 172)], B.HDL)
        T((kx + 80, y + 246), '%.1fW-DN20' % tot, 7, B.HCAP, 'L')
        T((kx + 80, y + 165), 'DÖNÜŞ DN20', 6, B.HCAP, 'L')
        for j, d in enumerate(res):
            px = c0 + 110 + j * 220
            L((px - 6, y + 198), (px - 6, y + 400), B.PEX)
            L((px + 6, y + 172), (px + 6, y + 400), B.PEX)
            ARC((px, y + 400), 6, 0, 180, B.PEX)
            C((px - 6, y + 198), 2, 'MTY-KOLLETOR'); C((px + 6, y + 172), 2, 'MTY-KOLLETOR')
            T((px, y + 150), 'P%d' % d['port'], 9, 'MTY-KOLLETOR', 'C')
            ti = calc[d['room']]['ti']
            T((px - 14, y + 215), 'ISIKAYBI %d / %.1fW / %.2f m / %s' % (d['port'], d['W'], d['L'], d['zl']), 6.5,
              'MTY-ISIKAYBIMAHAL', 'L', 90)
            T((px + 22, y + 215), '%d°C / PEX BORU 16x2.0 / %.0f cm / %s' % (ti, d['s'], d['room']), 6.5, B.HCAP, 'L', 90)
            T((px + 36, y + 215), '%.1fW-DN15 (DÖNÜŞ)' % d['W'], 6.5, B.HCAP, 'L', 90)


# ================================================================== LEJANT / NOTLAR / ANTET / TABLOLAR
NOTES = [
    'Temiz su tesisatı PPRC PN20 borularla yapılacak, sıcak su boruları izolasyonlu olarak döşenecektir.',
    'Bina ana sayacı bina girişindeki nişe, daire sayaçları merdiven holündeki sayaç dolabına SASKİ şartlarına uygun monte edilecektir.',
    'Sayaçlardan önce DN x 10, sonra DN x 5 uzunluğunda düz boru bırakılacak; her daire girişinde küresel vana ve çek valf konulacaktır.',
    'Kullanma suyu mimari çatı planındaki 3,00 m³ depodan sağlanacak; depo şamandıralı vana, havalık, taşma, boşaltma ve seviye göstergeli olacaktır.',
    'Depo taşma ve boşaltma boruları hava boşluklu olarak saçak oluğuna verilecek, pis su tesisatına doğrudan bağlanmayacaktır.',
    'Sıcak kullanma suyu her dairede duvar tipi hermetik yoğuşmalı kombiden sağlanacaktır.',
    'Pis su tesisatı TS EN 1451 PVC borularla yapılacak; bina içi yatay hatlar en az %2, temel altı ve bacalar arası (R1-PB) hatlar %1 eğimle döşenecektir.',
    'Pis su kolonları Ø100 (banyo) ve Ø70 (mutfak) olarak çatıdan en az 50 cm yukarı çıkarılacak, uçlarına havalık şapkası takılacaktır.',
    'MK1 havalığı çatı arasında 2x45° dirsekle depo altından saptırılarak çatıdan çıkarılacaktır.',
    'Her kolon dibinde temizleme kapağı bırakılacak, kolonlar temel altında R1 muayene bacasına bağlanacaktır.',
    'Bina pis suları R1 ve parsel bacası (PB) üzerinden SASKİ atıksu hattına, SASKİ denetiminde bağlanacaktır.',
    'Parsel bacası kotu ve bağlantı yeri SASKİ\'den alınacak; plandaki kotlar yaklaşık olup sahada teyit edilecektir.',
    'Hiçbir boru kolon içinden geçirilmeyecek; döşeme geçişleri kiriş bantları dışında kılıflı olarak yapılacaktır.',
    'Yağmur suları pis su hattına bağlanmayacaktır.',
    'Temiz su boruları döşemede ısı yalıtımı altından, yerden ısıtma boruları yalıtım üstünden geçirilecektir.',
    'Yerden ısıtma devreleri PEX 16x2,0 oksijen bariyerli borularla karşı akışlı salyangoz düzende döşenecektir.',
    'Boru aralıkları planda belirtildiği gibidir (oda 15 cm, salon/oda 2/banyo 10 cm); duvardan ilk boru mesafesi 10 cm olacaktır.',
    'Yerden ısıtma devre boyları (bağlantı boruları dahil) 80 m\'yi geçmeyecek; devreler kollektördeki debimetreli vanalarla dengelenecektir.',
    'Döşemede 10 cm XPS (zemin kat) / 3 cm EPS (ara kat) yalıtım, kenar bandı, PE folyo ve 6,5 cm şap uygulanacaktır.',
    'Kombi ısıtma gidiş suyu sıcaklığı yerden ısıtma için en fazla 50 °C\'ye ayarlanacaktır.',
    'Kombi bacaları hermetik koaksiyel baca olarak dış cepheye çıkarılacak; AKSA Doğalgaz iç tesisat şartnamesine uyulacaktır.',
    'Temiz su hatlarına 10 bar, yerden ısıtma devrelerine şap öncesi 6 bar basınç testi yapılacaktır.',
    'Tüm imalat TS 1258, TS EN 806, TS EN 12056, TS EN 1264 ve TS 825 standartlarına uygun olarak yapılacaktır.',
]


def lejant(x, y):
    T((x, y), 'LEJANT', 18, YZ, 'L')
    items = [
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), CS), 'SOĞUK SU BORUSU (PPRC PN20)'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), CH), 'SICAK SU BORUSU (PPRC PN20, İZOLELİ)'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), PS), 'PİS SU BORUSU (PVC)'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), B.YL), 'YAĞMUR SUYU BORUSU (PVC Ø100)'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), B.PEX), 'YERDEN ISITMA PEX 16x2,0'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), B.HGL), 'ISITMA GİDİŞ (KOMBİ→KOLLEKTÖR)'),
        (lambda p: L((p[0] - 30, p[1]), (p[0] + 30, p[1]), B.HDL), 'ISITMA DÖNÜŞ (KOLLEKTÖR→KOMBİ)'),
        (lambda p: mtyblk.insert('KLOZET1', (p[0], p[1] - 10), 0, 1.4), 'KLOZET BAĞLANTISI'),
        (lambda p: mtyblk.insert('LAVABO1', (p[0], p[1] - 8), 0, 1.4), 'LAVABO BAĞLANTISI'),
        (lambda p: mtyblk.insert('DUS TEKNESI1', (p[0], p[1] - 12), 0, 1.2), 'DUŞ BAĞLANTISI'),
        (lambda p: mtyblk.insert('EVIYE1', (p[0], p[1] - 8), 0, 1.4), 'EVİYE BAĞLANTISI'),
        (lambda p: mtyblk.insert('CAMASIR MAKINASI1', (p[0], p[1] - 22), 0, 0.6), 'ÇAMAŞIR MAKİNESİ'),
        (lambda p: mtyblk.insert('BULASIK MAKINASI1', (p[0], p[1] - 22), 0, 0.6), 'BULAŞIK MAKİNESİ'),
        (lambda p: mtyblk.insert('YER SUZGECI DN501', p, 0, 2), 'YER SÜZGECİ Ø50'),
        (lambda p: mtyblk.insert('KOMBI1', (p[0] - 30, p[1] - 10), 0, 0.6), 'HERMETİK YOĞUŞMALI KOMBİ 24 kW'),
        (lambda p: mtyblk.insert('MTY-SU SAYACI', p), 'SU SAYACI'),
        (lambda p: mtyblk.insert('MTY-KURESEL VANA', p), 'KÜRESEL VANA'),
        (lambda p: CEKVALF(p, 1.2), 'ÇEK VALF'),
        (lambda p: PISLIK_TUTUCU(p, 1.2), 'PİSLİK TUTUCU'),
        (lambda p: SAMANDIRALI_VANA(p, 1.2), 'ŞAMANDIRALI VANA'),
        (lambda p: mtyblk.insert('MTY-PIS SU KOLON', p, 0, 0.6), 'PİS SU KOLONU'),
        (lambda p: KOLON(p, 5, CS, 'temiz'), 'TEMİZ SU KOLONU (DBK / ADK)'),
        (lambda p: ROGAR_PLAN(p, 18, 'MTY-ROGAR'), 'MUAYENE / PARSEL BACASI'),
        (lambda p: RECT(p[0] - 25, p[1] - 12, p[0] + 25, p[1] + 12, 'RAST-TEM-SU DEPOSU'), 'SU DEPOSU 3,00 m³'),
        (lambda p: (RECT(p[0] - 6, p[1] - 22, p[0] + 6, p[1] + 22, 'MTY-KOLLETOR')), 'YERDEN ISITMA KOLLEKTÖRÜ'),
        (lambda p: HEXTAG(p, 'MTY-ISIKAYBIMAHAL', 'Z01'), 'ISI KAYBI MAHAL ETİKETİ'),
        (lambda p: B.cap_temiz((p[0] - 20, p[1] - 15), 0, so='4.5 YB', socp='Ø25', k=6), 'TEMİZ SU ÇAP / YÜK BİRİMİ'),
        (lambda p: B.cap_pis((p[0] - 20, p[1] - 10), 0, '2.8 SB', 'Ø70', 6), 'PİS SU ÇAP / SU BİRİMİ'),
    ]
    for i, (f, s) in enumerate(items):
        col, row = divmod(i, 14)
        p = (x + 60 + col * 560, y - 70 - row * 62)
        f(p)
        T((p[0] + 70, p[1] - 4), s, 10, YZ, 'L')


def notlar(x, y):
    T((x, y), 'PROJE NOTLARI', 18, YZ, 'L')
    for i, n in enumerate(NOTES):
        T((x, y - 30 - i * 18), '%d. %s' % (i + 1, n), 8.5, YZ, 'L')
    yy = y - 30 - len(NOTES) * 18 - 14
    for s in ('DİKKAT: MİMARİ PROJENİN ONAY AŞAMASINDA YAPILACAK DEĞİŞİKLİKTEN FEN İŞLERİ MD. BİLGİLENDİRİLMESİ',
              'BU PROJE MÜELLİFİN İZNİ OLMADAN YAYINLANAMAZ-ÇOĞALTILAMAZ-KULLANILAMAZ-DEĞİŞTİRİLEMEZ.'):
        T((x, yy), s, 8.5, YZ, 'L'); yy -= 18


def antet(x, y):
    w, h = 1650, 820
    RECT(x, y - h, x + w, y, 'MTY-PAFTA')
    T((x + w / 2, y - 55), 'ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK.', 34, YZ, 'C')
    T((x + w / 2, y - 90), 'Semerciler Mah. Sait Faik Sk. No:22/C Z01 Adapazarı/Sakarya', 13, YZ, 'C')
    T((x + w / 2, y - 112), 'rotasmuhendislik@gmail.com   0264 272 00 49', 13, YZ, 'C')
    L((x, y - 130), (x + w, y - 130), 'MTY-PAFTA')
    T((x + w / 2, y - 170), OLDPROJE, 20, YZ, 'C')
    T((x + w / 2, y - 200), 'SIHHİ TESİSAT VE YERDEN ISITMA (KOMBİLİ) PROJESİ - REVİZYON 2', 18, YZ, 'C')
    T((x + w / 2, y - 225), B.OLD.YER, 11, YZ, 'C')
    L((x, y - 245), (x + w, y - 245), 'MTY-PAFTA')
    rows = [('YAPININ ÖZELLİKLERİ', ''), ('YAPI SAHİBİ', 'CAFER GÖKTAŞ'), ('YAPI CİNSİ / SINIFI', 'KONUT / BETONARME - 3A'),
            ('KAT ADEDİ', 'ZEMİN + 2 KAT (+ÇATI ARASI)'), ('BAĞIMSIZ BÖLÜM', '3 DAİRE (HER KATTA 1)'),
            ('ISITMA', '3 x 24 kW HERMETİK YOĞUŞMALI KOMBİ + YERDEN ISITMA'),
            ('SU TEMİNİ', 'ŞEBEKE (SASKİ) + 3,00 m³ ÇATI DEPOSU (HİDROFOR YOK)'),
            ('ARSANIN ÖZELLİKLERİ', ''), ('İLİ / İLÇESİ', 'SAKARYA / ADAPAZARI'), ('MAHALLESİ', 'PAPUÇÇULAR'),
            ('PAFTA / ADA / PARSEL', 'G24-b-23-c-2-b / 405 / 381'), ('ARSA ALANI', '103.84 m²')]
    yy = y - 275
    for a, b in rows:
        T((x + 30, yy), a, 12 if b else 14, YZ, 'L')
        if b:
            T((x + 480, yy), ': ' + b, 12, YZ, 'L')
        yy -= 27
    L((x, y - h + 150), (x + w, y - h + 150), 'MTY-PAFTA')
    L((x + w / 2, y - h), (x + w / 2, y - h + 150), 'MTY-PAFTA')
    T((x + 30, y - h + 115), 'PROJE SORUMLUSU', 12, YZ, 'L')
    T((x + 30, y - h + 75), 'Mak. Müh. Bayram GENÇ', 16, YZ, 'L')
    T((x + 30, y - h + 40), 'REVİZYON 2 - 11.10.2026', 10, YZ, 'L')
    T((x + w / 2 + 30, y - h + 115), 'ONAY', 12, YZ, 'L')
    T((x + w / 2 + 30, y - h + 85), '14.06.1999 T. 23725 S. VE 08.05.2000 T. 24043 S. RESMİ', 8, YZ, 'L')
    T((x + w / 2 + 30, y - h + 72), 'GAZETE YÖNETMELİKLERİNE UYULMASI KAYDIYLA', 8, YZ, 'L')


OLDPROJE = "CAFER GÖKTAŞ'A AİT KONUT PROJESİ"


def isitma_tablo(x, y, HEAT):
    T((x, y), 'YERDEN ISITMA DEVRE ÇİZELGESİ VE KONTROLLER', 16, YZ, 'L')
    T((x, y - 20), 'Yöntem: devre ısı yükü = mahal ısı kaybı x (devre alanı / mahal devre alanı). Kontroller: '
      '(1) 35 kcal/h·m kuralı, (2) örnek şablon 17,5 W/m, (3) EN 1264 θF = θi + (q/8,92)^0,91, q = yük / mahal net alanı (mimari m²)', 7, YZ, 'L')
    T((x, y - 31), 'EN 1264 sınırları: oturma alanı θF ≤ 29 °C, banyo θF ≤ 33 °C (θi+9). EK ISITMA: döşemenin sınır sıcaklıkta '
      'veremediği ısı - havlupan / panel radyatör ile karşılanması önerilir (yapı sahibi / mimar onayı ile).', 7, YZ, 'L')
    hdr = ['KAT', 'P', 'MAHAL', 'ZON', 'θi', 'A MAHAL (m²)', 'ARALIK', 'L (m)', 'YÜK (W)', 'q (W/m²)', 'θF (°C)',
           '17,5 W/m', '35 kcal/h·m', 'EN1264 MAKS.', 'EK ISITMA']
    cx = [0, 60, 90, 250, 300, 340, 400, 460, 520, 590, 660, 730, 810, 900, 990]
    yy = y - 45
    for c, s in zip(cx, hdr):
        T((x + c, yy), s, 7.5, YZ, 'L')
    L((x, yy - 5), (x + 1150, yy - 5), YZ)
    yy -= 18
    for k, (res, tot, calc) in enumerate(HEAT):
        for d in res:
            ti = calc[d['room']]['ti']
            same = [x for x in res if x['room'] == d['room']]
            Am = calc[d['room']]['A'] * d['A'] / sum(x['A'] for x in same)
            q = d['W'] / Am
            tf = ti + (q / 8.92) ** 0.91
            lim = 33.0 if 'BANYO' in d['room'] else 29.0
            c1 = d['L'] * 17.5
            c2 = d['L'] * 35 / 0.86
            cap = Am * 8.92 * (lim - ti) ** 1.1
            ek = d['W'] - cap
            st = 'GEREKMEZ' if ek <= 0 else '%.0f W' % ek
            vals = [B.FLOORS[k][1].replace(' KAT', ''), 'P%d' % d['port'], d['room'], d['zl'], '%d' % ti, '%.2f' % Am,
                    '%.0f cm' % d['s'], '%.2f' % d['L'], '%.1f' % d['W'], '%.0f' % q, '%.1f' % tf, '%.0f W' % c1,
                    '%.0f W' % c2, '%.0f W (θF=%d)' % (cap, lim), st]
            for c, s in zip(cx, vals):
                T((x + c, yy), s, 7, YZ, 'L')
            yy -= 14
        a = calc['ANTRE']
        T((x + 90, yy), 'ANTRE %d°C - %.1f W : kollektör bağlantı boruları ile ısıtılır' % (a['ti'], a['Q']), 7, YZ, 'L')
        yy -= 14
        T((x + 90, yy), 'DAİRE TOPLAMI : %.1f W (%.0f kcal/h) - KOMBİ 24 kW YETERLİ' % (tot, tot * 0.86), 7.5, YZ, 'L')
        yy -= 20
    return yy


def u_tablo(x, y):
    T((x, y), 'TS 825:2024 (2./3. BÖLGE) U DEĞERİ KONTROLÜ - ÖNERİLEN YAPI ELEMANLARI', 14, YZ, 'L')
    yy = y - 24
    for k, v in H.ASSY.items():
        lim = v[4]
        st = ('≤ %.2f UYGUN' % lim) if lim else '(ısıtılan hacimler arası, sınır yok)'
        T((x, yy), '%-5s U = %.3f W/m²K  %s  -  %s' % (k, H.U[k], st, v[0]), 7, YZ, 'L')
        yy -= 13
    T((x, yy), 'ÇP    U = 1.80 W/m²K  ≤ 1.80 UYGUN  -  PVC doğrama + Low-E ısıcam (g ≤ 0,45)', 7, YZ, 'L'); yy -= 13
    T((x, yy), 'DK/İK U = 2.00 W/m²K  -  yalıtımlı çelik daire kapısı / iç kapı (TS 825:2024 tablosunda kapı sınırı yok)', 7, YZ, 'L')
    return yy - 13


def build(HEAT, Y0, Y1, HY0, HY1, TEMEL=None):
    sihhi_sema(-695, Y0)
    isitma_sema(-1945, HY0, HEAT)
    antet(-7900, Y1 - 50)
    notlar(-7900, Y1 - 885)
    lejant(-7900, HY1 - 80)
    yy = isitma_tablo(-7900, HY1 - 1000, HEAT)
    u_tablo(-6650, HY1 - 160)
    TY0, TY1 = Y0 + B.TDY, Y1 + B.TDY
    yagmur_sema(-4445, TY0)
    fr = []
    names = ['ZEMİN KAT SIHHİ TESİSAT PLANI', '1. KAT SIHHİ TESİSAT PLANI', '2. KAT SIHHİ TESİSAT PLANI',
             'ÇATI PLANI (SU DEPOSU, KOLON ÇIKIŞLARI)']
    for k in range(4):
        a, b = B.OLD.sheet_x(k)
        fr.append(((a, Y0, b, Y1), names[k], '1/50'))
    fr.append(((-695, Y0, 1305, Y1), 'SIHHİ TESİSAT KOLON ŞEMASI', 'ÖLÇEKSİZ'))
    for k in range(3):
        a, b = B.OLD.sheet_x(k)
        fr.append(((a, HY0, b, HY1), ['ZEMİN', '1.', '2.'][k] + ' KAT YERDEN ISITMA PLANI', '1/50'))
    fr.append(((-1945, HY0, 55, HY1), 'YERDEN ISITMA KOLON ŞEMASI', 'ÖLÇEKSİZ'))
    fr.append(((-7950, Y0, -5695, Y1), 'ANTET VE PROJE NOTLARI', 'ÖLÇEKSİZ'))
    fr.append(((-7950, HY0, -5695, HY1), 'LEJANT VE HESAP ÖZETLERİ', 'ÖLÇEKSİZ'))
    fr.append(((-5695, TY0, -4445, TY1), 'TEMEL PLANI (PİS SU ALTYAPISI / YAĞMUR İNİŞLERİ)', '1/50'))
    fr.append(((-4445, TY0, -3195, TY1), 'YAĞMUR SUYU KOLON ŞEMASI VE HESABI', 'ÖLÇEKSİZ'))
    for (a, b, c, d), t, o in fr:
        B.OLD.frame(a, b, c, d, t, o)
    return fr
