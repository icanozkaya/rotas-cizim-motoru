# -*- coding: utf-8 -*-
"""YANGIN KOLON ŞEMASI (açılımlı, düşey): gerçek kotlu kat bantları, sprinkler kolonu (SP-1) ve her katta zon vana
grubu (izlenebilir kelebek V-.., akış anahtarı FS-.., test-drenaj TD-.. -> drenaj kolonu), yangın dolabı kolonları
(YG1..) ve her katta dolap bağlantıları (YD-..), kolon tepelerinde otomatik purjör, pompa dairesinde yangın pompa
grubu + basma kollektörü + ıslak alarm vana istasyonu + itfaiye bağlantı ağzı + depo. Pompa grubu numaraları
motor/deneme/pompa_grubu YANGIN_POMPA_GRUBU_KESITI cihaz listesi ile aynıdır (dolap_pompa_no.py ile okunur).
Semboller birleşik sembol kütüphanesinden (motor/deneme/semboller/sembol.py), lejant + adet tablosu otomatik."""
import math
import os
import sys
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'semboller'))
import sembol as SB                    # noqa: E402

WF = 0.8
LAY = {
    'ROTAS-YANGIN-SEMA-KAT': 8, 'ROTAS-YANGIN-SEMA-KOT': 7, 'ROTAS-YANGIN-SPR-BORU': 140, 'ROTAS-YANGIN-DOLAP-BORU': 1,
    'ROTAS-YANGIN-ANA-BORU': 1, 'ROTAS-YANGIN-DRENAJ': 8, 'ROTAS-YANGIN-SEMA-CAP': 3, 'ROTAS-YANGIN-SEMA-YAZI': 7,
    'ROTAS-YANGIN-SEMA-NO': 1, 'ROTAS-YANGIN-SEMA-BALON': 6, 'ROTAS-YANGIN-MASKE': 7, 'ROTAS-YANGIN-BASLIK': 7,
    'ROTAS-YANGIN-NOT': 1, 'ROTAS-YANGIN-TABLO': 7, 'ROTAS-YANGIN-DEPO': 5,
}
SEMBOL_LAY = 'ROTAS-YANGIN-SEMBOL'
ISIM = {'depo': 'DEPOSU', 'emk': 'EMİŞ KOLLEKTÖRÜ', 'pe': 'ELEKTRİKLİ YANGIN POMPASI', 'pd': 'DİZEL YANGIN POMPASI',
        'pj': 'JOKEY POMPA', 'bk': 'BASMA KOLLEKTÖRÜ', 'cek': 'ÇEK VALF', 'ikv': 'İZLENEBİLİR KELEBEK', 'ys': 'YER SÜZGECİ'}


def fmt(v, n=2):
    return f'{v:.{n}f}'.replace('.', ',')


def tw(s, h):
    return len(s) * h * 0.62 * WF + h * 0.4


def th(h):
    return h * 1.35


class Sema:
    def __init__(self):
        d = ezdxf.new('R2018', setup=True)
        d.header['$INSUNITS'] = 5
        d.styles.add('ROTAS', font='arial.ttf')
        d.set_wipeout_variables(frame=0)
        for n, c in LAY.items():
            d.layers.add(n, color=c)
        d.layers.get('ROTAS-YANGIN-DRENAJ').dxf.linetype = 'DASHED'
        SB.hazirla(d)
        self.doc, self.msp = d, d.modelspace()
        self.yazilar = []          # kontrol: (kutu, metin)
        self.cizgiler = []         # kontrol: (a, b, katman)
        self.kutular = []          # sembol kutuları

    def PL(self, pts, lay, w=0.0):
        e = self.msp.add_lwpolyline(pts, dxfattribs={'layer': lay})
        if w:
            e.dxf.const_width = w
        for a, b in zip(pts[:-1], pts[1:]):
            self.cizgiler.append((a, b, lay))
        return e

    def T(self, x, y, s, h, lay='ROTAS-YANGIN-SEMA-YAZI', al='MC', rot=0.0, maske=True):
        w, t = tw(s, h), th(h)
        hz = {'L': 0.0, 'C': 0.5, 'R': 1.0}[al[1]]
        vz = {'B': 0.0, 'M': 0.5, 'T': 1.0}[al[0]]
        if abs(rot) < 1:
            cx, cy = x + (0.5 - hz) * w, y + (0.5 - vz) * t
            k = (cx - w / 2, cy - t / 2, cx + w / 2, cy + t / 2)
        else:
            cx, cy = x - (0.5 - vz) * t, y + (0.5 - hz) * w
            k = (cx - t / 2, cy - w / 2, cx + t / 2, cy + w / 2)
        if maske:
            self.msp.add_wipeout([(k[0], k[1]), (k[2], k[1]), (k[2], k[3]), (k[0], k[3])],
                                 dxfattribs={'layer': 'ROTAS-YANGIN-MASKE'})
        e = self.msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF})
        e.set_placement((cx, cy), align=TA.MIDDLE_CENTER)
        self.yazilar.append((k, s))
        return k

    def sembol(self, ad, x, y, aci=0.0, olcek=1.0, ozn=None):
        ins = SB.ciz(self.msp, ad, x, y, aci=aci, olcek=olcek, katman=SEMBOL_LAY, ozn=ozn)
        u = SB._bb(self.doc, ins.dxf.name)
        if u:
            c, s = math.cos(math.radians(aci)), math.sin(math.radians(aci))
            xs, ys = [], []
            for px, py in ((u[0], u[1]), (u[2], u[1]), (u[2], u[3]), (u[0], u[3])):
                xs.append(x + (px * c - py * s) * olcek)
                ys.append(y + (px * s + py * c) * olcek)
            self.kutular.append(((min(xs), min(ys), max(xs), max(ys)), ad))
        return ins

    def hat(self, p0, p1, sem, lay, w=0.0):
        """düz boru + üzerindeki semboller (boru sembol boyunca kesilir)"""
        SB.hat(self.msp, p0, p1, [(t, ad, None) for t, ad in sem], lay, sembol_katmani=SEMBOL_LAY, genislik=w)
        self.cizgiler.append((p0, p1, lay))
        L = math.dist(p0, p1)
        aci = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
        for t, ad in sem:
            bn = SB.blok_tanimla(self.doc, ad)
            u = SB._bb(self.doc, bn)
            x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
            if u:
                c, s = math.cos(math.radians(aci)), math.sin(math.radians(aci))
                xs, ys = [], []
                for px, py in ((u[0], u[1]), (u[2], u[1]), (u[2], u[3]), (u[0], u[3])):
                    for sg in (1, -1):          # simetrik semboller ters dönebilir: iki yön birlikte
                        xs.append(x + sg * (px * c - py * s))
                        ys.append(y + sg * (px * s + py * c))
                self.kutular.append(((min(xs), min(ys), max(xs), max(ys)), ad))

    def balon(self, p, no, uc, lay='ROTAS-YANGIN-SEMA-BALON', r=13.0):
        """pompa grubu cihaz numarası balonu + kılavuz (uc: işaret edilen nokta)"""
        self.msp.add_circle(p, r, dxfattribs={'layer': lay})
        d = math.dist(p, uc)
        if d > r + 1:
            a = (p[0] + (uc[0] - p[0]) * r / d, p[1] + (uc[1] - p[1]) * r / d)
            self.PL([a, uc], lay)
        e = self.msp.add_text(no, height=9, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF})
        e.set_placement(p, align=TA.MIDDLE_CENTER)
        self.yazilar.append(((p[0] - r, p[1] - r, p[0] + r, p[1] + r), no))

    def cap(self, a, b, s, yan=1, f=0.5, h=9.0, lay='ROTAS-YANGIN-SEMA-CAP'):
        """boru parçası üzerinde çap etiketi (boruya paralel, boru yanında)"""
        x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        if abs(a[1] - b[1]) < 0.01:
            return self.T(x, y + yan * (th(h) / 2 + 3), s, h, lay)
        return self.T(x - yan * (th(h) / 2 + 3), y, s, h, lay, rot=90.0)

    def tablo(self, x, y, baslik, kolonlar, satirlar, h=9.0):
        rh = h * 2.0
        lay = 'ROTAS-YANGIN-TABLO'
        W = sum(c[1] for c in kolonlar)
        self.msp.add_text(baslik, height=h * 1.4, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x, y + h * 0.8), align=TA.BOTTOM_LEFT)
        yy = y
        self.msp.add_lwpolyline([(x, y), (x + W, y)], dxfattribs={'layer': lay})
        for i, row in enumerate([[c[0] for c in kolonlar]] + satirlar):
            xx = x
            for (cb, cw, hz), v in zip(kolonlar, row):
                t = self.msp.add_text(str(v), height=h if i else h * 0.9, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF})
                if hz == 'L':
                    t.set_placement((xx + h * 0.5, yy - rh / 2), align=TA.MIDDLE_LEFT)
                else:
                    t.set_placement((xx + cw / 2, yy - rh / 2), align=TA.MIDDLE_CENTER)
                xx += cw
            yy -= rh
            e = self.msp.add_lwpolyline([(x, yy), (x + W, yy)], dxfattribs={'layer': lay})
            if i == 0:
                e.dxf.const_width = 1.0
        xx = x
        for c in kolonlar + [None]:
            self.msp.add_line((xx, y), (xx, yy), dxfattribs={'layer': lay})
            if c:
                xx += c[1]
        return yy


def pompa_no(liste, anahtar):
    for r in liste:
        if ISIM[anahtar] in r[1]:
            return r[0]
    return '?'


def ciz(D, P, k, hes, net, sonuc, hd, liste, cikti, pompa_girdi=None):
    S = Sema()
    katlar = sorted(D['katlar'], key=lambda q: q['kot_m'])
    pk = D['pompa']
    yP = pk['kot_m'] * 100.0
    ayni = any(abs(q['kot_m'] - pk['kot_m']) < 0.01 for q in katlar)
    if ayni:                 # pompa dairesi kat ile aynı kotta: şemada ayrı bant (ölçeksiz) olarak altta gösterilir
        yP -= 400.0
    dolaplar = sonuc['dolaplar']
    kolonlar = sonuc['kolonlar']
    R = net['root']
    sp_dn = max(net['T'][R][c]['dn'] for c in net['T'].successors(R))
    sp_ad = hes['ad'][R]
    n_bas = len(net['heads'])
    bdn = hd['bdn']
    # ---------------------------------------------------------------- yatay yerleşim
    x_sp = 700.0
    x_dr = x_sp + 720.0
    xs_yg = []
    x = x_dr + 260.0
    for kc in kolonlar:
        xs_yg.append(x)
        x += 160.0 + len(kc['dolaplar']) * 280.0 + 120.0
    x_ib = x + 60.0
    x_son = x_ib + 220.0
    x_bas = -560.0
    # ---------------------------------------------------------------- kat bantları + kotlar
    tepe = katlar[-1]['kot_m'] * 100.0 + 350.0
    seviyeler = [(pk['ad'] + (' - aynı kot, şematik' if ayni else ''), pk['kot_m'], yP)] + \
        [(q['ad'], q['kot_m'], q['kot_m'] * 100.0) for q in katlar]
    for ad, kot, y in seviyeler:
        S.PL([(x_bas, y), (x_son, y)], 'ROTAS-YANGIN-SEMA-KAT', w=1.5)
        S.T(x_bas + 5, y + 18, ad, 13, 'ROTAS-YANGIN-SEMA-KOT', al='ML')
        s = '±0,00' if abs(kot) < 1e-6 else (f'+{fmt(kot)}' if kot > 0 else f'-{fmt(-kot)}')
        S.T(x_bas + 5, y - 16, s, 11, 'ROTAS-YANGIN-SEMA-KOT', al='ML')
    S.PL([(x_bas, tepe), (x_son, tepe)], 'ROTAS-YANGIN-SEMA-KAT')
    S.T(x_bas + 5, tepe + 16, 'ÇATI / SON KAT TAVANI', 11, 'ROTAS-YANGIN-SEMA-KOT', al='ML')
    ust_kat = katlar[-1]['kot_m'] * 100.0
    # ---------------------------------------------------------------- pompa dairesi
    y_kol = yP + 150.0                  # basma kollektörü
    x_pg = -60.0
    y_pg = yP + 70.0
    S.sembol('yangin_pompa_seti', x_pg, y_pg, olcek=1.4)
    pg_sag = x_pg + 57.6 * 1.4
    pg_sol = x_pg - 57.6 * 1.4
    # depo (gerçek nesne; dikdörtgen gövde + su seviyesi)
    dx0, dx1 = x_bas + 30, pg_sol - 90
    S.PL([(dx0, yP), (dx0, yP + 260), (dx1, yP + 260), (dx1, yP)], 'ROTAS-YANGIN-DEPO', w=2.0)
    S.PL([(dx0 + 10, yP + 225), (dx1 - 10, yP + 225)], 'ROTAS-YANGIN-DEPO')
    S.T((dx0 + dx1) / 2, yP + 175, 'YANGIN SUYU DEPOSU', 11, 'ROTAS-YANGIN-DEPO')
    S.T((dx0 + dx1) / 2, yP + 150, f"V = {fmt(hd['V'], 1)} m³ ({hd['sure']} dk)", 10, 'ROTAS-YANGIN-DEPO')
    # emiş
    y_em = y_pg - 15
    S.hat((dx1, y_em), (pg_sol, y_em), [(0.5, 'izlenebilir_kelebek')], 'ROTAS-YANGIN-ANA-BORU', w=3.0)
    # basma: pompa grubu -> kollektör
    S.PL([(pg_sag, y_pg + 20), (pg_sag + 40, y_pg + 20), (pg_sag + 40, y_kol)], 'ROTAS-YANGIN-ANA-BORU', w=4.0)
    x_k0 = pg_sag + 40
    # kollektör parçaları (tee noktaları): SP, YG.., İB
    tees = [x_sp] + xs_yg + [x_ib]
    pts = [x_k0] + tees
    for a, b in zip(pts[:-1], pts[1:]):
        S.PL([(a, y_kol), (b, y_kol)], 'ROTAS-YANGIN-ANA-BORU', w=4.0)
        S.cap((a, y_kol), (b, y_kol), f'DN{bdn}', yan=-1, f=0.5 if b - a > 300 else 0.45)
    N = {a: pompa_no(liste, a) for a in ISIM}
    S.balon((dx0 + 40, yP + 300), N['depo'], (dx0 + 40, yP + 260))
    S.balon(((dx1 + pg_sol) / 2 - 30, y_em - 45), N['emk'], ((dx1 + pg_sol) / 2 - 30, y_em))
    S.balon((x_pg - 50, yP - 40), N['pe'], (x_pg - 50, y_pg - 25))
    S.balon((x_pg + 5, yP - 40), N['pd'], (x_pg + 5, y_pg - 25))
    S.balon((x_pg + 60, yP - 40), N['pj'], (x_pg + 60, y_pg - 25))
    S.balon((x_k0 + 55, y_kol + 45), N['bk'], (x_k0 + 55, y_kol))
    S.T(x_pg, y_pg + 75, 'YANGIN POMPA GRUBU', 11)
    S.T(x_pg, y_pg + 58, f"Q={fmt(hd['Q_m3h'], 1)} m³/h  H={fmt(hd['H'], 1)} mSS", 10)
    # ---------------------------------------------------------------- sprinkler kolonu SP-1
    y_sp_top = ust_kat + 270.0 + 60.0
    y_av = yP + 255.0
    S.hat((x_sp, y_kol), (x_sp, yP + 340.0), [(0.55, 'islak_alarm')], 'ROTAS-YANGIN-SPR-BORU', w=4.0)
    S.T(x_sp + 40, y_kol + 0.55 * (190.0) - 2, 'AV-01', 10, 'ROTAS-YANGIN-SEMA-NO', al='ML')
    S.cap((x_sp, y_kol), (x_sp, y_kol + 60), f'DN{bdn}', yan=1, f=0.5)
    prev = yP + 340.0
    numara = dict(V=0, FS=0, TD=0)
    ekipman = [['AV-01', 'ISLAK ALARM VANA İSTASYONU (SP-1 dibi)', f'DN{bdn}', 1]]
    for q in katlar:
        yf = q['kot_m'] * 100.0
        yz = yf + 270.0
        S.PL([(x_sp, prev), (x_sp, yz)], 'ROTAS-YANGIN-SPR-BORU', w=4.0)
        S.cap((x_sp, prev), (x_sp, yz), f'DN{sp_dn}', yan=1, f=0.35 if prev < yf else 0.5)
        prev = yz
        # zon vana grubu
        numara['V'] += 1
        numara['FS'] += 1
        numara['TD'] += 1
        vno, fno, tno = f"V-{numara['V']:02d}", f"FS-{numara['FS']:02d}", f"TD-{numara['TD']:02d}"
        xa, xb = x_sp, x_sp + 470.0
        S.hat((xa, yz), (xb, yz), [(90.0 / 470, 'izlenebilir_kelebek'), (190.0 / 470, 'akis_anahtari')],
              'ROTAS-YANGIN-SPR-BORU', w=3.0)
        S.T(xa + 90, yz - 22, vno, 9, 'ROTAS-YANGIN-SEMA-NO')
        S.T(xa + 190, yz - 22, fno, 9, 'ROTAS-YANGIN-SEMA-NO')
        S.T(xa + 400, yz + 14, f'DN{sp_dn}', 9, 'ROTAS-YANGIN-SEMA-CAP')
        S.T(xb + 8, yz, f'KAT SPRİNKLER AĞI ({n_bas} BAŞLIK)', 9, al='ML')
        # okun ucu
        S.PL([(xb - 10, yz + 5), (xb, yz), (xb - 10, yz - 5)], 'ROTAS-YANGIN-SPR-BORU')
        # test-drenaj -> drenaj kolonu
        xt = xa + 270.0
        yt = yz - 70.0
        S.PL([(xt, yz), (xt, yt)], 'ROTAS-YANGIN-SPR-BORU')
        S.hat((xt, yt), (x_dr, yt), [(0.4, 'test_drenaj')], 'ROTAS-YANGIN-DRENAJ')
        S.T(xt + 0.4 * (x_dr - xt), yt - 26, tno, 9, 'ROTAS-YANGIN-SEMA-NO')
        S.T(xt + 0.78 * (x_dr - xt), yt + 12, 'DN32', 9, 'ROTAS-YANGIN-SEMA-CAP')
        S.T(xt - 18, (yz + yt) / 2, 'DN32', 9, 'ROTAS-YANGIN-SEMA-CAP', rot=90.0)
        ekipman += [[vno, f"İZLENEBİLİR KELEBEK VANA ({q['ad']} zon)", f'DN{sp_dn}', 1],
                    [fno, f"AKIŞ ANAHTARI ({q['ad']} zon)", f'DN{sp_dn}', 1],
                    [tno, f"TEST VE DRENAJ SETİ ({q['ad']})", 'DN32', 1]]
    S.PL([(x_sp, prev), (x_sp, y_sp_top)], 'ROTAS-YANGIN-SPR-BORU', w=4.0)
    S.sembol('purjor_sprinkler', x_sp, y_sp_top, olcek=2.0)
    S.T(x_sp + 30, y_sp_top + 12, 'O.H.P.', 9, al='ML')
    _kolon_no(S, x_sp, y_sp_top + 75, sp_ad)
    # drenaj kolonu
    y_dr_top = ust_kat + 200.0
    y_dr_alt = yP + 215.0
    S.PL([(x_dr, y_dr_top), (x_dr, y_dr_alt), (x_dr + 90, y_dr_alt)], 'ROTAS-YANGIN-DRENAJ', w=2.0)
    S.T(x_dr + 95, y_dr_alt, 'YER SÜZGECİNE', 9, al='ML')
    S.balon((x_dr + 60, y_dr_alt - 40), N['ys'], (x_dr + 90, y_dr_alt))
    S.T(x_dr - 16, (yP + 350 + katlar[0]['kot_m'] * 100.0) / 2 + 40, 'DN50', 9, 'ROTAS-YANGIN-SEMA-CAP', rot=90.0) \
        if len(katlar) > 1 or katlar[0]['kot_m'] > pk['kot_m'] else None
    _kolon_no(S, x_dr, y_dr_top + 45, 'DR')
    # ---------------------------------------------------------------- dolap kolonları YG
    ad2d = {d['no']: d for d in dolaplar}
    yd_say = 0
    for xg, kc in zip(xs_yg, kolonlar):
        y_v = yP + 255.0
        S.hat((xg, y_kol), (xg, yP + 340.0), [(0.55, 'izlenebilir_kelebek'), (0.25, 'cekvalf')], 'ROTAS-YANGIN-DOLAP-BORU', w=2.0)
        numara['V'] += 1
        vno = f"V-{numara['V']:02d}"
        S.T(xg + 22, y_kol + 0.55 * 190 + 18, vno, 9, 'ROTAS-YANGIN-SEMA-NO', al='ML')
        S.T(xg + 22, y_kol + 0.25 * 190 - 20, 'ÇV', 9, 'ROTAS-YANGIN-SEMA-NO', al='ML')
        ekipman += [[vno, f"İZLENEBİLİR KELEBEK VANA ({kc['ad']} dibi)", f"DN{k['kolon_dn']}", 1],
                    ['ÇV', f"ÇEK VALF ({kc['ad']} dibi)", f"DN{k['kolon_dn']}", 1]]
        prev = yP + 340.0
        y_top = ust_kat + 190.0 + 60.0
        for q in katlar:
            yf = q['kot_m'] * 100.0
            yl = yf + 190.0
            S.PL([(xg, prev), (xg, yl)], 'ROTAS-YANGIN-DOLAP-BORU', w=2.0)
            S.cap((xg, prev), (xg, yl), f"DN{k['kolon_dn']}", yan=1, f=0.3 if prev < yf else 0.45)
            prev = yl
            # kat yatay hattı ve dolaplar
            n = len(kc['dolaplar'])
            xd = [xg + 160.0 + j * 280.0 for j in range(n)]
            S.PL([(xg, yl), (xd[-1], yl)], 'ROTAS-YANGIN-DOLAP-BORU', w=2.0)
            for j in range(n):
                a = xg if j == 0 else xd[j - 1]
                S.cap((a, yl), (xd[j], yl), f"DN{k['besleme_dn'] if n > 1 or True else k['baglanti_dn']}", yan=1, f=0.5)
            for j, dno in enumerate(kc['dolaplar']):
                yc = yf + 120.0
                xcn = xd[j] - 32.0
                S.PL([(xd[j], yl), (xd[j], yc), (xcn, yc)], 'ROTAS-YANGIN-DOLAP-BORU')
                S.T(xd[j] + 14, (yl + yc) / 2, f"DN{k['baglanti_dn']}", 9, 'ROTAS-YANGIN-SEMA-CAP', rot=90.0)
                ins = (xcn - 26.5 * 1.5, yc - 21.6 * 1.5)
                S.sembol('yangin_dolabi_kolon', ins[0], ins[1], olcek=1.5)
                yd_say += 1
                lbl = f"{dno} ({q['ad']})" if len(katlar) > 1 else dno
                S.T(ins[0] - 8, yc + 52, lbl, 9, 'ROTAS-YANGIN-SEMA-NO')
        S.PL([(xg, prev), (xg, y_top)], 'ROTAS-YANGIN-DOLAP-BORU', w=2.0)
        S.sembol('purjor_sprinkler', xg, y_top, olcek=2.0)
        S.T(xg + 30, y_top + 12, 'O.H.P.', 9, al='ML')
        _kolon_no(S, xg, y_top + 75, kc['ad'])
    # ---------------------------------------------------------------- itfaiye bağlantı ağzı
    y_ib = yP + 260.0
    S.hat((x_ib, y_kol), (x_ib, y_ib), [(0.5, 'cekvalf')], 'ROTAS-YANGIN-ANA-BORU', w=3.0)
    S.sembol('itfaiye_agzi', x_ib, y_ib + 22, olcek=1.2)
    S.T(x_ib + 50, y_ib + 22, 'İTFAİYE BAĞLANTI AĞZI 2 x 2 1/2" (CEPHEDE)', 9, al='ML')
    S.T(x_ib - 16, (y_kol + y_ib) / 2 - 30, 'DN100', 9, 'ROTAS-YANGIN-SEMA-CAP', rot=90.0)
    S.T(x_ib + 22, y_kol + 0.5 * (y_ib - y_kol), 'ÇV', 9, 'ROTAS-YANGIN-SEMA-NO', al='ML')
    ekipman += [['ÇV', 'ÇEK VALF (itfaiye bağlantısı)', 'DN100', 1], ['İB', 'İTFAİYE BAĞLANTI AĞZI 2 x 2 1/2"', 'DN100', 1],
                ['YD', 'YANGIN DOLABI TS EN 671-1 (Ø25 x 30 m)', f"DN{k['baglanti_dn']}", yd_say],
                ['O.H.P.', 'OTOMATİK HAVA PURJÖRÜ (kolon tepesi)', 'DN25', 1 + len(kolonlar)]]
    # ---------------------------------------------------------------- başlık, tablolar, notlar
    yb = yP - 120
    S.msp.add_text('YANGIN TESİSATI KOLON ŞEMASI (SPRİNKLER + YANGIN DOLABI)..........ÖLÇEKSİZ', height=30,
                   dxfattribs={'layer': 'ROTAS-YANGIN-BASLIK', 'style': 'ROTAS', 'width': WF}) \
        .set_placement((x_bas, tepe + 150), align=TA.BOTTOM_LEFT)
    S.msp.add_text(P.get('proje', ''), height=20, dxfattribs={'layer': 'ROTAS-YANGIN-BASLIK', 'style': 'ROTAS', 'width': WF}) \
        .set_placement((x_bas, tepe + 110), align=TA.BOTTOM_LEFT)
    if P.get('deneme'):
        S.msp.add_text('DENEME', height=50, dxfattribs={'layer': 'ROTAS-YANGIN-BASLIK', 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x_bas, tepe + 200), align=TA.BOTTOM_LEFT)
    y1 = S.tablo(x_bas, yb, 'EKİPMAN LİSTESİ (KOLON ŞEMASI)', [('NO', 90, 'C'), ('TANIM', 520, 'L'), ('ÇAP', 90, 'C'),
                                                              ('ADET', 70, 'C')], ekipman)
    pg_rows = [[N[a], [r[1] for r in liste if r[0] == N[a]][0] if N[a] != '?' else '-'] for a in
               ('depo', 'emk', 'pe', 'pd', 'pj', 'bk', 'ys')]
    y2 = S.tablo(x_bas + 860, yb, 'POMPA GRUBU BAĞLANTISI (numaralar YANGIN_POMPA_GRUBU_KESITI cihaz listesi ile aynı)',
                 [('NO', 70, 'C'), ('CİHAZ', 520, 'L')], pg_rows)
    rows = [
        ['Sprinkler debisi (hidrolik, en üst kat)', f"{fmt(hd['Qs'], 0)} l/dk"],
        [f"Dolap debisi ({hd['ne']} x {fmt(k['debi_lpm'], 0)} l/dk)", f"{fmt(hd['Qd'], 0)} l/dk"],
        ['POMPA DEBİSİ', f"{fmt(hd['Q'], 0)} l/dk = {fmt(hd['Q_m3h'], 1)} m³/h"],
        ['Sprinkler / dolap için pompa basıncı', f"{fmt(hd['P_spr'], 2)} / {fmt(hd['P_dolap'], 2)} bar"],
        ['POMPA BASMA YÜKSEKLİĞİ', f"{fmt(hd['H'], 1)} mSS ({hd['yonetici']} belirleyici)"],
        ['DEPO HACMİ', f"{fmt(hd['V'], 1)} m³ ({hd['sure']} dk)"],
    ]
    if pompa_girdi:
        Qg, Hg = pompa_girdi['elektrikli']['Q'], pompa_girdi['elektrikli']['H']
        ok = Qg >= hd['Q_m3h'] - 1e-6 and Hg >= hd['H'] - 1e-6
        rows.append(['Pompa grubu girdisi (kesit) Q / H', f"{fmt(Qg, 0)} m³/h / {fmt(Hg, 0)} mSS -> {'YETERLİ' if ok else 'YETERSİZ'}"])
    y3 = S.tablo(x_bas + 860, y2 - 80, 'POMPA SEÇİMİ (SPRİNKLER + DOLAP)', [('KALEM', 380, 'L'), ('DEĞER', 380, 'L')], rows)
    notlar = [
        'Kolon şeması ölçeksizdir; kat kotları mimari kotlardır. Her katta sprinkler zon vana grubu (izlenebilir kelebek vana, akış anahtarı, test-drenaj) bulunur.',
        f"Yangın dolabı kolonları (YG..) DN{k['kolon_dn']}, dolap bağlantıları DN{k['baglanti_dn']}; kolon diplerinde izlenebilir kelebek vana ve çek valf, tepelerinde otomatik hava purjörü vardır.",
        'Test-drenaj hatları drenaj kolonu (DR) ile pompa dairesi yer süzgecine verilir.',
        'Daire içindeki numaralar pompa grubu kesiti (motor/deneme/pompa_grubu, YANGIN_POMPA_GRUBU_KESITI.dxf) cihaz listesi numaralarıdır.',
        'İtfaiye bağlantı ağzı pompa çıkışı çek valflerinden sonraki basma kollektörüne bağlanır.',
    ]
    if hd['bdd']:
        notlar.append(f"Alt katlarda dolap girişinde basınç {fmt(hd['p_alt'], 1)} bar > 9 bar: basınç düşürücü konacaktır.")
    if P.get('deneme'):
        notlar.append('DENEME: değerler örnektir, uygulamada kullanılmayacaktır.')
    S.msp.add_text('NOTLAR :', height=14, dxfattribs={'layer': 'ROTAS-YANGIN-NOT', 'style': 'ROTAS', 'width': WF}) \
        .set_placement((x_bas, y1 - 60), align=TA.BOTTOM_LEFT)
    for i, s in enumerate(notlar):
        S.msp.add_text(f'{i + 1}. {s}', height=10, dxfattribs={'layer': 'ROTAS-YANGIN-NOT', 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x_bas, y1 - 85 - i * 22), align=TA.BOTTOM_LEFT)
    # kullanılan sembollerin lejantı + adet tablosu (otomatik)
    sayim = SB.otomatik_lejant(S.doc, x=x_son + 150, y=tepe)
    S.doc.saveas(cikti)
    return S, sayim


def _kolon_no(S, x, y, ad):
    """kolon numarası: MTY-KOLON NO bloğu (K özniteliği), kolon ekseninde"""
    S.PL([(x, y - 75 + 10), (x, y - 28)], 'ROTAS-YANGIN-SEMA-BALON')
    ins = S.sembol('kolon_no_yangin', x, y, olcek=1.0, ozn={'K': ad})
    S.yazilar.append(((x - 27, y - 27, x + 27, y + 27), ad))
    return ins


def kontrol(S, dosya):
    """şema: yazı-yazı ve yazı-boru çakışması, katman adları"""
    d = ezdxf.readfile(dosya)
    msp = d.modelspace()
    kul = {e.dxf.layer for e in msp} | {e.dxf.layer for b in d.blocks for e in b}
    yanlis = sorted(l for l in kul if l not in ('0', 'Defpoints') and not l.startswith('ROTAS-') and not l.startswith('MTY-'))
    yy = S.yazilar
    yc = []
    for i in range(len(yy)):
        for j in range(i + 1, len(yy)):
            a, b = yy[i][0], yy[j][0]
            if a[0] < b[2] - 0.5 and a[2] > b[0] + 0.5 and a[1] < b[3] - 0.5 and a[3] > b[1] + 0.5:
                yc.append((yy[i][1], yy[j][1]))
    boru = [c for c in S.cizgiler if c[2] in ('ROTAS-YANGIN-SPR-BORU', 'ROTAS-YANGIN-DOLAP-BORU', 'ROTAS-YANGIN-ANA-BORU',
                                              'ROTAS-YANGIN-DRENAJ')]
    yb = []
    for k, s in yy:
        for a, b, lay in boru:
            if min(a[0], b[0]) < k[2] and max(a[0], b[0]) > k[0] and min(a[1], b[1]) < k[3] and max(a[1], b[1]) > k[1]:
                if s in ('O.H.P.',):
                    continue
                yb.append((s, lay))
                break
    ys = []
    for k, s in yy:
        for kb, ad in S.kutular:
            if ad == 'kolon_no_yangin':
                continue
            if k[0] < kb[2] - 1 and k[2] > kb[0] + 1 and k[1] < kb[3] - 1 and k[3] > kb[1] + 1:
                ys.append((s, ad))
                break
    rap = dict(yanlis_katman=yanlis, yazi_yazi=yc, yazi_boru=yb, yazi_sembol=ys, dxf_surum=d.dxfversion)
    rap['HATA'] = len(yanlis) + len(yc) + len(yb) + len(ys)
    return rap
