"""Genel paftalar: sıhhi kolon şeması (çok gruplu, bodrum/hidrofor/terfi destekli), yağmur şeması+hesabı, lejant, notlar, antet."""
import math, sys
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import cad
from cad import L, PL, C, T, RECT, RRECT, ARC, ARROW, SOL, VANA, CEKVALF, PISLIK_TUTUCU, SAMANDIRALI_VANA, KOLON, \
    ROGAR_PLAN, HAVALIK_SAPKA, HEXTAG, POMPA, MEMBRANLI_TANK, DALGIC_POMPA
import mtyblk
import gp
from gp import CS, CH, PS, YZ, CD, VN, TSC, PSC, YBL, YL, YC, fmt, dn_temiz, dn_sb, cap_temiz, cap_pis

PVC = 'MTY-PVC'
RED = 'MTY-KAT-ADI'
W = gp.WIDTH


def dl45(a, b, r=5.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy)
    nx, ny = -dy / l * r, dx / l * r
    L((a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), PVC); L((a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny), PVC)
    PL([a, b], PS, w=W[PS])


def dline(a, b, r=5.0):
    if abs(a[1] - b[1]) < 1e-6:
        L((a[0], a[1] + r), (b[0], b[1] + r), PVC); L((a[0], a[1] - r), (b[0], b[1] - r), PVC)
    else:
        L((a[0] + r, a[1]), (b[0] + r, b[1]), PVC); L((a[0] - r, a[1]), (b[0] - r, b[1]), PVC)
    PL([a, b], PS, w=W[PS])


def wl(pts, lay):
    PL(pts, lay, w=W.get(lay, 0))


FIXBLK = {'LV': 'LAVABO1 KOLON', 'DUS': 'DUS TEKNESI1 KOLON', 'WC': 'KLOZET1 KOLON', 'CM': 'CAMASIR MAKINASI1 KOLON',
          'YS': 'YER SUZGECI DN501 KOLON', 'EV': 'EVIYE1 KOLON', 'BM': 'BULASIK MAKINASI1 KOLON'}
YBC = dict(LV=(0.5, 0.5), DUS=(1.0, 1.0), WC=(0.5, None), CM=(1.0, None), YS=(None, None), EV=(0.5, 0.5), BM=(1.0, None))
DNP = dict(LV=50, DUS=50, WC=100, CM=50, YS=50, EV=50, BM=50)


def fixture_row(x0, y, keys, kol_x, step=140, tk=True):
    """y: kat döşemesi; keys: armatürler (soldan sağa, kolondan uzaklaşan); kol_x: kolon ekseni (solda).
    pis yatay hat y-50, 45° çatal ile kolona; dönüş: temiz su bağlantı x listesi"""
    xs = []
    for i, k in enumerate(keys):
        x = x0 + i * step
        so, sc = YBC[k]
        at = {}
        if so:
            at.update(SO=fmt(so), SOCP='Ø20')
        if sc:
            at.update(SC=fmt(sc), SCCP='Ø20')
        at.update(PS='%d' % gp.SB[k], PSCP='Ø%d' % DNP[k])
        mtyblk.insert(FIXBLK[k], (x, y), 0, 1.0, attrs=at)
        mtyblk.insert('PVC CATAL SAG', (x, y), 0, 1.0)
        xs.append(x)
    yp = y - 50
    xr = xs[-1] + 3
    if tk:
        dline((xr, yp), (xr + 30, yp), 5)
        L((xr + 30, yp - 7), (xr + 30, yp + 7), PVC); L((xr + 33, yp - 7), (xr + 33, yp + 7), PVC)
        T((xr + 38, yp - 3), 'T.K.', 7, PSC, 'L')
    prev = kol_x + 28
    cum = sum(gp.SB[k] for k in keys)
    dl45((kol_x + 28, yp), (kol_x + 4, yp - 24), 5.0)
    for idx, k in enumerate(keys):
        xa, xb = prev, xs[idx] - 27
        dline((xa, yp), (xb, yp), 5)
        wc = any(DNP[q] >= 100 for q in keys[idx:])
        cap_pis(((xa + xb) / 2, yp + 6), 0, '%d SB' % cum, 'Ø%d' % dn_sb(cum, wc), 6.5)
        cum -= gp.SB[k]
        prev = xs[idx] + 3
    return xs


def supply_labels(xstart, xend, y, xs, keys, hot_keys=(), hot_from=None):
    """temiz su hattı üzerinde her parçaya çap/YB etiketi (y: hat kotu)"""
    pts = [xstart] + [x for x, k in zip(xs, keys) if YBC[k][0]] + ([xend] if xend else [])
    names = [k for k in keys if YBC[k][0]]
    pos = [x for x, k in zip(xs, keys) if YBC[k][0]]
    for a, b in zip(pts[:-1], pts[1:]):
        mid = (a + b) / 2
        down = [n for n, p in zip(names, pos) if p > a + 1]
        yb = sum(YBC[n][0] for n in down) if down else 0
        if yb <= 0:
            continue
        cap_temiz((mid, y), 0, so='%s YB' % fmt(yb), socp='Ø%d' % dn_temiz(yb), k=6.5)


# ================================================================== SIHHİ KOLON ŞEMASI
def sihhi_sema(ox, oy, P):
    fl = P['floors']                    # [(anahtar, ad), ...] alttan üste (çatı hariç)
    nf = len(fl)
    FH = 330.0
    yf = [oy + 520 + i * FH for i in range(nf + 1)]       # son eleman: çatı/çatı arası döşemesi
    width = P['sema_w']
    T((ox + width / 2, yf[-1] + 330), 'SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI', 28, YZ, 'C')
    T((ox + width / 2, yf[-1] + 300), '(TEMİZ SU: TS 1258 YÜK BİRİMİ (YB), PPRC PN20 - PİS SU: SU BİRİMİ (SB), PVC - ÖLÇEKSİZ)', 10, YZ, 'C')
    for i in range(nf + 1):
        wl([(ox + 40, yf[i]), (ox + width - 60, yf[i])], 'MTY-SEMA')
        nm = fl[i][1] if i < nf else P['roof_name']
        T((ox + width - 30, yf[i] + 20), nm, 15, RED, 'L', 90)
    xs = lambda dx: ox + dx
    sup = P['supply']
    # -------- şebeke + ana sayaç (zemin bandı altı)
    iz = [k for k, _ in fl].index('Z')
    ysb = yf[iz] - 120
    xd = xs(110)
    wl([(xs(30), ysb), (xd, ysb)], CS)
    VANA((xs(40), ysb), 0.7); PISLIK_TUTUCU((xs(55), ysb), 0.7); mtyblk.insert('MTY-SU SAYACI', (xs(72), ysb), 0, 0.8)
    CEKVALF((xs(90), ysb), 0.6)
    T((xs(30), ysb - 22), 'ŞEBEKEDEN (SASKİ) Ø32 - ANA SAYAÇ (BİNA GİRİŞİ NİŞİ)', 8, TSC, 'L')
    # -------- depo
    DW, DH = 200, 120
    if sup['depo'] == 'cati':
        dx0, dy0 = xs(170), yf[-1] + 40
    else:
        ib = 0
        dx0, dy0 = xs(170), yf[ib] + 40
    RECT(dx0, dy0, dx0 + DW, dy0 + DH, 'RAST-TEM-SU DEPOSU')
    T((dx0 + 100, dy0 + 82), 'KULLANMA SUYU DEPOSU', 9, YZ, 'C')
    T((dx0 + 100, dy0 + 66), 'V = %.2f m³ (ŞAMANDIRALI)' % sup['V'], 8, YZ, 'C')
    T((dx0 + 100, dy0 + 52), sup['vnote'], 7, YZ, 'C')
    L((dx0 + 60, dy0 + DH), (dx0 + 60, dy0 + DH + 22), CS); HAVALIK_SAPKA((dx0 + 60, dy0 + DH + 22), 0.8, CS)
    T((dx0 + 72, dy0 + DH + 24), 'HAVALIK (SİNEKLİKLİ)', 6.5, YZ, 'L')
    L((dx0 + 185, dy0 + 10), (dx0 + 185, dy0 + 100), YZ); T((dx0 + 180, dy0 + 20), 'SEVİYE GÖST.', 6, YZ, 'L', 90)
    wl([(xd, ysb), (xd, dy0 + 100), (dx0 + 30, dy0 + 100)], CS); SAMANDIRALI_VANA((dx0 + 36, dy0 + 100), 0.9)
    cap_temiz((xd, (ysb + dy0) / 2 + 40), 90, so='DBK %s YB' % fmt(sup['ybt']), socp='Ø32', k=7)
    # taşma + boşaltma
    xt = dx0 + DW + 12
    wl([(dx0 + DW, dy0 + 6), (xt, dy0 + 6), (xt, dy0 + 105), (dx0 + DW, dy0 + 105)], CS)
    VANA((xt, dy0 + 30), 0.7, 90)
    if sup['depo'] == 'cati':
        yt = dy0 + DH + 18
        wl([(xt, dy0 + 105), (xt, yt), (dx0 + 150, yt)], CS)
        wl([(dx0 + 150, yt + 30), (dx0 + 150, dy0 + DH + 4)], YL)
        T((dx0 + 155, yt + 20), sup['tasma'], 6.5, YC, 'L')
        T((dx0 + 154, yt - 9), 'TAŞMA Ø40/BOŞ.Ø32', 6, TSC, 'L')
    else:
        wl([(xt, dy0 + 6), (xt, dy0 - 25)], CS)
        mtyblk.insert('YER SUZGECI DN501 KOLON', (xt, dy0 - 40), 0, 1.0)
        T((xt + 12, dy0 - 32), sup['tasma'], 6.5, TSC, 'L')
    # depo çıkışı -> (hidrofor) -> ADK -> sayaç grubu (zemin)
    xa = xs(140)
    yk = yf[iz] + 45
    if sup.get('hidrofor'):
        hx, hy = dx0 + DW + 60, dy0 + 10
        wl([(dx0 + DW, dy0 + 15), (hx, dy0 + 15)], CS)
        RECT(hx, dy0 - 10, hx + 120, dy0 + 70, gp.HID)
        for j in range(2):
            POMPA((hx + 35 + j * 50, dy0 + 15), 12, 0, gp.HID)
        MEMBRANLI_TANK((hx + 150, dy0 + 40), 34, 80, gp.HID)
        wl([(hx + 120, dy0 + 30), (hx + 133, dy0 + 30)], CS)
        T((hx + 60, dy0 + 82), 'HİDROFOR', 10, gp.HID, 'C')
        for j, s in enumerate(sup['hidrofor']):
            T((hx - 10, dy0 - 52 - j * 10), s, 6.5, gp.HID, 'L')
        wl([(hx + 120, dy0 + 55), (hx + 175, dy0 + 55), (hx + 175, yk - 10 if yk > dy0 + 55 else yk + 10), (xa + 70, yk - 10 if yk > dy0 + 55 else yk + 10)], CS)
        xa_line = None
    else:
        wl([(dx0, dy0 + 10), (xa, dy0 + 10), (xa, yk)], CS)
        VANA((xa, dy0 - 15), 0.8, 90)
        cap_temiz((xa, (yk + dy0) / 2), 90, so='ADK %s YB' % fmt(sup['ybt']), socp='Ø32', k=7)
    # sayaç grubu
    units = sup['units']               # [(ad, kat anahtarı, grup no, yb)]
    # sayaç sırası: bodrum (sola çıkar) - üst katlar yukarıdan aşağı (yukarı çıkar) - zemin (sağa çıkar) => hatlar kesişmez
    fkeys = [k for k, _ in fl]
    units = sorted(units, key=lambda u: (0, 0) if u[1].startswith('B') else ((2, 0) if u[1] == 'Z' else (1, -fkeys.index(u[1]))))
    xr0 = xs(220)
    RECT(xr0 - 30, yk - 22, xr0 + 40 * len(units) + 10, yk + 110, VN)
    T((xr0 - 30, yk - 34), 'SAYAÇ GRUBU - BİNA GİRİŞİ (%d ADET)' % len(units), 7.5, VN, 'L')
    wl([(xa + (70 if sup.get('hidrofor') else 0), yk), (xr0 + 40 * (len(units) - 1), yk)], CS)
    if sup.get('hidrofor'):
        wl([(xa + 70, yk - 10), (xa + 70, yk)], CS)
    ux = {}
    for j, (nm, fk, g, yb) in enumerate(units):
        x = xr0 + 40 * j
        ux[nm] = x
        wl([(x, yk), (x, yk + 60)], CS)          # kollektör -> vana -> sayaç -> çek valf: kesintisiz hat
        VANA((x, yk + 14), 0.55, 90); mtyblk.insert('MTY-SU SAYACI', (x, yk + 34), 90, 0.6); CEKVALF((x, yk + 54), 0.5, 90)
        T((x + 6, yk + 66), nm, 6.5, VN, 'L', 90)
    # -------- gruplar (her biri kolon takımı)
    ytk = yf[0] - 150.5          # temel altı / kolon dipleri
    unames = [q[0] for q in units]
    for gi, G in enumerate(P['groups']):
        gx = xs(G['x'])
        for i, (fk, fname) in enumerate(fl):
            y = yf[i]
            u = G['units'].get(fk)
            if not u:
                continue
            nm, kind = u
            j = unames.index(nm)
            x_s = ux[nm]
            ylev = y + 130
            ycor = y + 285 + 7 * j if fk != 'Z' or True else ylev
            if y + 130 > yk + 60 and fk != 'Z':
                wl([(x_s, yk + 60), (x_s, ycor), (gx + 40 + 6 * j, ycor), (gx + 40 + 6 * j, ylev), (gx + 120, ylev)], CS)
            elif fk == 'Z':
                wl([(x_s, yk + 60), (x_s, yk + 72 + 6 * j), (gx + 40 + 6 * j, yk + 72 + 6 * j), (gx + 40 + 6 * j, ylev), (gx + 120, ylev)], CS)
            else:     # bodrum: sayaç çıkışından kutunun sol dışına, sonra aşağı in (diğer hatları kesmez)
                xb = xr0 - 40 - 6 * j
                wl([(x_s, yk + 60), (x_s, yk + 66 + 4 * j), (xb, yk + 66 + 4 * j), (xb, yk - 40 - 6 * j),
                    (gx + 40 + 6 * j, yk - 40 - 6 * j), (gx + 40 + 6 * j, ylev), (gx + 120, ylev)], CS)
            VANA((gx + 100, ylev), 0.6)
            T((gx + 60, ylev + 14), '%s GİRİŞ VANASI' % nm, 6.5, VN, 'L')
            if kind == 'daire':
                rows = [(G['pkx'], G['bkeys'])] + [(e['kx'], e['keys']) for e in G.get('extra', [])] + [(G['mkx'], G['mkeys'])]
                allx, allk = [], []
                for kx_, keys in rows:
                    xr = fixture_row(xs(kx_) + 120, y, keys, xs(kx_))
                    allx += xr; allk += keys
                kx = xs(G['kombi'])
                wl([(gx + 120, ylev), (kx, ylev)], CS)
                mtyblk.insert('KOMBI1 KOLON', (kx, y), 0, 1.0, attrs={'SO': fmt(2.0), 'SOCP': 'Ø20', 'SC': fmt(2.0), 'SCCP': 'Ø20'})
                T((kx + 25, y + 215), 'H. KOMBİ 24 kW', 8, CD, 'L')
                hx = [x for x, k in zip(allx, allk) if YBC[k][1]]
                wl([(kx - 15, y + 135), (min(hx) - 15, y + 135)], CH)
                pts = sorted(zip(allx, allk))
                supply_labels(gx + 120, kx, ylev, [p[0] for p in pts], [p[1] for p in pts])
                C((kx + 110, y + 175), 34, 'MTY-PISSU-KOLONNO')
                T((kx + 110, y + 175), nm, 18, 'MTY-PISSU-KOLONNO', 'MC')
            else:   # iş yeri
                ik = G['ikeys']
                xsi = fixture_row(xs(G['pkx']) + 120, y, ik, xs(G['pkx']))
                wl([(gx + 120, ylev), (max(xsi) + 5, ylev)], CS)
                supply_labels(gx + 120, None, ylev, xsi, ik)
                C((xs(G['mkx']) + 200, y + 240), 40, 'MTY-PISSU-KOLONNO')
                T((xs(G['mkx']) + 200, y + 240), nm, 13, 'MTY-PISSU-KOLONNO', 'MC')
                T((xs(G['mkx']) + 110, y + 175), 'LAVABO ALTI 10 L ELEKTRİKLİ SU ISITICI', 7, CD, 'L')
        # kolonlar
        for nm, xk, dk, sbf in G['kolons']:
            x = xs(xk)
            top = yf[-1] + 110
            ybot = ytk + 20 if not G.get('bottom', {}).get(nm) else G['bottom'][nm](yf)
            dline((x, ybot), (x, top), 5)
            mtyblk.insert('MTY-KOLON HAVALIK SAPKASI', (x, top), 0, 1.6)
            T((x + 12, yf[-1] + 60), 'HAVALIK Ø%d (ÇATIDAN 50 cm YUKARI)' % dk, 6.5, PSC, 'L', 90)
            mtyblk.insert('MTY-PIS SU KOLON NO', (x, top + 70), 0, 1.0, attrs={'K': nm})
            for i in range(nf):
                s = sbf(i)
                if s:
                    T((x - 12, yf[i] + 40), 'Ø%d / %d SB' % (dk, s), 8, PSC, 'L', 90)
            mtyblk.insert('MTY-TEMIZLEME KAPAGI KOLON', (x, ybot + 55), 0, 0.8, attrs={'TK': 'T.K.'})
            mtyblk.insert('PVC DIRSEK', (x, ybot), 0, 1.0)
    return yf, ytk


# ================================================================== YAĞMUR ŞEMASI + HESAP
def yagmur_hesap(Pm2, f):
    S = Pm2 * 0.75
    A = S / f
    D = 1.13 * math.sqrt(A)
    return dict(P=Pm2, S=S, f=f, A=A, D=D)


def yagmur_sema(ox, oy, P):
    fl = P['floors']
    nf = len(fl)
    FH = 330.0
    yf = [oy + 520 + i * FH for i in range(nf + 1)]
    Y = P['yagmur']
    names = Y['names']
    w = 260 + 170 * len(names) + 560
    T((ox + w / 2, yf[-1] + 330), 'YAĞMUR SUYU KOLON ŞEMASI VE HESABI', 26, YZ, 'C')
    for i in range(nf + 1):
        wl([(ox + 40, yf[i]), (ox + w - 40, yf[i])], 'MTY-SEMA')
        T((ox + 50, yf[i] + 8), fl[i][1] if i < nf else P['roof_name'], 11, YZ, 'L')
    ytop = yf[-1] + 120
    x1 = ox + 220 + (len(names) - 1) * 170
    wl([(ox + 150, ytop), (x1 + 60, ytop)], YL)
    T((ox + 150, ytop + 12), 'YAĞMUR OLUĞU (SAÇAK BOYUNCA, İNİŞE DOĞRU %0,5 EĞİMLİ)', 8, YC, 'L')
    iz = [k for k, _ in fl].index('Z') if 'Z' in [k for k, _ in fl] else 0
    for j, nm in enumerate(names):
        x = ox + 220 + j * 170
        foot = iz                                   # inişler zemin katta biter (bodrum/temele inmez, altyapı yok)
        ybot = yf[foot] + 25
        wl([(x, ytop), (x, ybot), (x + 30, ybot)], YL)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (x, ytop + 55), 0, 0.9, attrs={'K': nm})
        for i in range(foot, nf):
            T((x - 10, yf[i] + 60), '%s - Ø%d PVC' % (nm, Y['dn']), 8, YC, 'L', 90)
        T((x + 36, ybot - 3), 'ZEMİN KOTUNDA', 6.5, YC, 'L'); T((x + 36, ybot - 13), 'BIRAKILIR', 6.5, YC, 'L')
        if nm == Y.get('tasma_to'):
            yd = yf[-1] + 60
            L((x - 110, yd), (x, yd), CS); RECT(x - 140, yd - 15, x - 110, yd + 15, 'RAST-TEM-SU DEPOSU')
            T((x - 105, yd + 5), 'DEPO TAŞMA Ø40 + BOŞALTMA Ø32', 6, TSC, 'L')
    h = yagmur_hesap(Y['P'], len(names))
    x, y = ox + 260 + 170 * len(names), yf[-1] + 40
    T((x, y), 'YAĞMUR İNİŞ BORUSU ÇAP HESABI', 12, 'MTY-HESAP', 'L')
    rows = [('P', 'Çatı alanı (yatay izdüşüm)', '%.2f m²' % h['P']), ('S', 'P x 0,75 / 1', '%.2f cm²' % h['S']),
            ('f', 'İniş borusu adedi', '%d' % h['f']), ('A', 'S / f', '%.2f cm²' % h['A']), ('D', '1,13 x √A', '%.2f cm' % h['D'])]
    for i, (a, b_, c) in enumerate(rows):
        T((x, y - 24 - i * 17), '%s = %s' % (a, b_), 9, 'MTY-HESAP', 'L')
        T((x + 250, y - 24 - i * 17), '= %s' % c, 9, 'MTY-HESAP', 'L')
    ok = h['D'] < 7.0
    T((x, y - 24 - 5 * 17 - 6), ('D = %.2f cm < 7 cm → Ø70\'lik boru UYGUNDUR.' if ok else 'D = %.2f cm ≥ 7 cm → Ø100 kullanılmalıdır.') % h['D'], 9, 'MTY-HESAP', 'L')
    T((x, y - 24 - 6 * 17 - 6), 'Uygulamada %d x Ø%d PVC iniş borusu seçilmiştir.' % (h['f'], Y['dn']), 9, 'MTY-HESAP', 'L')
    nts = ['Yağmur suları pis su tesisatına bağlanmayacaktır.', 'İniş boruları cepheye kelepçe ile tespit edilecektir.',
           'Yağmur suyu altyapısı bu proje kapsamında değildir; iniş boruları zemin kotunda bırakılacaktır.', 'Oluklar iniş yönüne %0,5 eğimle yapılacaktır.'] + Y.get('notes', [])
    for i, n in enumerate(nts):
        T((x, y - 170 - i * 15), '%d. %s' % (i + 1, n), 8, YZ, 'L')
    return h, w


# ================================================================== LEJANT / NOTLAR / ANTET
def lejant(x, y, extra=()):
    T((x, y), 'LEJANT', 20, YZ, 'L')
    items = [
        (lambda p: wl([(p[0] - 30, p[1]), (p[0] + 30, p[1])], CS), 'SOĞUK SU BORUSU (PPRC PN20)'),
        (lambda p: wl([(p[0] - 30, p[1]), (p[0] + 30, p[1])], CH), 'SICAK SU BORUSU (PPRC PN20, İZOLELİ)'),
        (lambda p: wl([(p[0] - 30, p[1]), (p[0] + 30, p[1])], PS), 'PİS SU BORUSU (PVC)'),
        (lambda p: wl([(p[0] - 30, p[1]), (p[0] + 30, p[1])], gp.PST), 'PİS SU BORUSU (TAVANDAN / ASMA TAVAN)'),
        (lambda p: wl([(p[0] - 30, p[1]), (p[0] + 30, p[1])], YL), 'YAĞMUR SUYU BORUSU (PVC)'),
        (lambda p: wl([(p[0] - 30, p[1]), (p[0] + 30, p[1])], gp.PEX), 'YERDEN ISITMA PEX 16x2,0'),
        (lambda p: wl([(p[0] - 30, p[1]), (p[0] + 30, p[1])], gp.HGL), 'ISITMA GİDİŞ (KOMBİ→KOLLEKTÖR)'),
        (lambda p: wl([(p[0] - 30, p[1]), (p[0] + 30, p[1])], gp.HDL), 'ISITMA DÖNÜŞ (KOLLEKTÖR→KOMBİ)'),
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
        (lambda p: KOLON(p, 5, CS, 'temiz'), 'TEMİZ SU KOLONU'),
        (lambda p: ROGAR_PLAN(p, 18, 'MTY-ROGAR'), 'MUAYENE / PARSEL BACASI'),
        (lambda p: RECT(p[0] - 25, p[1] - 12, p[0] + 25, p[1] + 12, 'RAST-TEM-SU DEPOSU'), 'KULLANMA SUYU DEPOSU'),
        (lambda p: (RECT(p[0] - 6, p[1] - 22, p[0] + 6, p[1] + 22, 'MTY-KOLLETOR')), 'YERDEN ISITMA KOLLEKTÖRÜ'),
        (lambda p: HEXTAG(p, 'MTY-ISIKAYBIMAHAL', 'Z01'), 'ISI KAYBI MAHAL ETİKETİ'),
        (lambda p: cap_temiz((p[0] - 20, p[1] - 15), 0, so='4.5 YB', socp='Ø25', k=6.5), 'TEMİZ SU ÇAP / YÜK BİRİMİ'),
        (lambda p: cap_pis((p[0] - 20, p[1] - 10), 0, '8 SB', 'Ø70', 6.5), 'PİS SU ÇAP / SU BİRİMİ'),
    ] + list(extra)
    for i, (f, s) in enumerate(items):
        col, row = divmod(i, 16)
        p = (x + 60 + col * 600, y - 70 - row * 62)
        f(p)
        T((p[0] + 70, p[1] - 4), s, 11, YZ, 'L')


def notlar(x, y, notes):
    T((x, y), 'PROJE NOTLARI', 20, YZ, 'L')
    yy = y - 34
    for i, n in enumerate(notes):
        T((x, yy), '%d. %s' % (i + 1, n), 10, YZ, 'L')
        yy -= 20
    yy -= 10
    for s in ('DİKKAT: MİMARİ PROJENİN ONAY AŞAMASINDA YAPILACAK DEĞİŞİKLİKTEN FEN İŞLERİ MD. BİLGİLENDİRİLMESİ',
              'BU PROJE MÜELLİFİN İZNİ OLMADAN YAYINLANAMAZ-ÇOĞALTILAMAZ-KULLANILAMAZ-DEĞİŞTİRİLEMEZ.'):
        T((x, yy), s, 10, YZ, 'L'); yy -= 20
    return yy


def antet(x, y, A):
    w, h = 1700, 900
    PL([(x, y - h), (x + w, y - h), (x + w, y), (x, y)], 'MTY-PAFTA', True, 2.5)
    T((x + w / 2, y - 55), 'ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK.', 36, YZ, 'C')
    T((x + w / 2, y - 92), 'Semerciler Mah. Sait Faik Sk. No:22/C Z01 Adapazarı/Sakarya', 14, YZ, 'C')
    T((x + w / 2, y - 115), 'rotasmuhendislik@gmail.com   0264 272 00 49', 14, YZ, 'C')
    L((x, y - 132), (x + w, y - 132), 'MTY-PAFTA')
    T((x + w / 2, y - 175), A['proje'], 22, YZ, 'C')
    T((x + w / 2, y - 207), A['konu'], 18, YZ, 'C')
    L((x, y - 228), (x + w, y - 228), 'MTY-PAFTA')
    yy = y - 260
    for a, b in A['rows']:
        T((x + 30, yy), a, 13 if b else 15, YZ, 'L')
        if b:
            T((x + 500, yy), ': ' + b, 13, YZ, 'L')
        yy -= 29
    L((x, y - h + 150), (x + w, y - h + 150), 'MTY-PAFTA')
    L((x + w / 2, y - h), (x + w / 2, y - h + 150), 'MTY-PAFTA')
    T((x + 30, y - h + 115), 'PROJE SORUMLUSU', 13, YZ, 'L')
    T((x + 30, y - h + 75), 'Mak. Müh. Bayram GENÇ', 17, YZ, 'L')
    T((x + 30, y - h + 40), A.get('tarih', '11.10.2026'), 11, YZ, 'L')
    T((x + w / 2 + 30, y - h + 115), 'ONAY', 13, YZ, 'L')
    T((x + w / 2 + 30, y - h + 85), '14.06.1999 T. 23725 S. VE 08.05.2000 T. 24043 S. RESMİ', 9, YZ, 'L')
    T((x + w / 2 + 30, y - h + 70), 'GAZETE YÖNETMELİKLERİNE UYULMASI KAYDIYLA', 9, YZ, 'L')


def frame(x0, y0, x1, y1, title, olcek):
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'MTY-PAFTA', True, 4.0)
    PL([(x0 + 25, y0 + 25), (x1 - 25, y0 + 25), (x1 - 25, y1 - 25), (x0 + 25, y1 - 25)], 'MTY-PAFTA', True, 1.0)
    T((x1 - 40, y0 + 45), '%s   ÖLÇEK : %s' % (title, olcek), 14, 'MTY-PAFTA', 'R')
