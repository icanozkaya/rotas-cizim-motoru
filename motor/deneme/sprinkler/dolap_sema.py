# -*- coding: utf-8 -*-
"""YANGIN KOLON ŞEMASI (açılımlı, düşey) — R2 (14.10.2026 B talimatı).
Gerçek kotlu kat bantları, sprinkler kolonu (SP-1) ve her katta zon vana grubu (izlenebilir kelebek V-.., akış anahtarı
FS-.., test-drenaj TD-.. -> drenaj kolonu), yangın dolabı kolonları (YG1..) ve her katta dolap bağlantıları (YD-..),
pompa dairesinde yangın pompa grubu + basma kollektörü + ıslak alarm vana istasyonu + depo, itfaiye bağlantısı
KOLLEKTÖRLÜ (2 x DN65 storz -> kollektör -> çek valf -> vana -> ana hat; akış tesisata doğru).
R2: kolon tepelerinde PURJÖR YOK (kör tapa); MTY bloğu yok (rotas_sembol.py saf geometri); çaplar kademeli (kademe.py);
pompa tablosunda hesaplanan ve seçilen debi / basma (çalışma basıncı 9-10 bar).
Pompa grubu numaraları motor/deneme/pompa_grubu YANGIN_POMPA_GRUBU_KESITI cihaz listesi ile aynıdır (dolap_pompa_no.py)."""
import math
import os
import sys
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rotas_sembol as SB              # noqa: E402  saf geometri (MTY yok)
import kademe                          # noqa: E402

WF = 0.8
LAY = {
    'ROTAS-YANGIN-SEMA-KAT': 8, 'ROTAS-YANGIN-SEMA-KOT': 7, 'ROTAS-YANGIN-SPR-BORU': 140, 'ROTAS-YANGIN-DOLAP-BORU': 1,
    'ROTAS-YANGIN-ANA-BORU': 1, 'ROTAS-YANGIN-DRENAJ': 8, 'ROTAS-YANGIN-SEMA-CAP': 3, 'ROTAS-YANGIN-SEMA-YAZI': 7,
    'ROTAS-YANGIN-SEMA-NO': 1, 'ROTAS-YANGIN-SEMA-BALON': 6, 'ROTAS-YANGIN-MASKE': 7, 'ROTAS-YANGIN-BASLIK': 7,
    'ROTAS-YANGIN-NOT': 1, 'ROTAS-YANGIN-TABLO': 7, 'ROTAS-YANGIN-DEPO': 5,
    'ROTAS-YANGIN-ITFAIYE': 1, 'ROTAS-YANGIN-ITFAIYE-SEMBOL': 1, 'ROTAS-LEJANT': 7,
}
SEMBOL_LAY = 'ROTAS-YANGIN-SEMBOL'
ISIM = {'depo': 'DEPOSU', 'emk': 'EMİŞ KOLLEKTÖRÜ', 'pe': 'ELEKTRİKLİ YANGIN POMPASI', 'pd': 'DİZEL YANGIN POMPASI',
        'pj': 'JOKEY POMPA', 'bk': 'BASMA KOLLEKTÖRÜ', 'cek': 'ÇEK VALF', 'ikv': 'İZLENEBİLİR KELEBEK', 'ys': 'YER SÜZGECİ'}


def fmt(v, n=2):
    return f'{v:.{n}f}'.replace('.', ',')


def tw(s, h):
    # R2b: denetim aracının yazı kutusu tahmini (0,8·h·karakter·WF) + pay
    return len(s) * h * 0.8 * WF + h * 0.4


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

    def hat(self, p0, p1, sem, lay, w=0.0, skat=SEMBOL_LAY):
        """düz boru + üzerindeki semboller (boru sembol boyunca kesilir); p0 -> p1 akış yönü"""
        SB.hat(self.msp, p0, p1, [(t, ad, None) for t, ad in sem], lay, sembol_katmani=skat, genislik=w)
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
                    xs.append(x + (px * c - py * s))       # rotas_sembol: yön sabit (ters dönmez)
                    ys.append(y + (px * s + py * c))
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
    zdn = net['sema_dn']                          # kademeli çap zinciri (kademe.py)
    kok_dn = max(net['T'][R][c]['dn'] for c in net['T'].successors(R))
    sp_ad = hes['ad'][R]
    n_bas = len(net['heads'])
    bdn = hd['bdn']
    sec = hd['sec']
    # ---------------------------------------------------------------- yatay yerleşim
    x_sp = 700.0
    x_dr = x_sp + 720.0
    xs_yg = []
    x = x_dr + 260.0
    for kc in kolonlar:
        xs_yg.append(x)
        x += 160.0 + len(kc['dolaplar']) * 280.0 + 120.0
    x_ib = x + 60.0
    x_son = x_ib + 330.0
    x_bas = -560.0
    # ---------------------------------------------------------------- kat bantları + kotlar
    tepe = katlar[-1]['kot_m'] * 100.0 + 350.0
    # R2b: aynı kotta şematik pompa dairesi bandının adı çizginin ALTINA, kot yazısının yanına (depo çizgisine binmez)
    seviyeler = [(pk['ad'][:-1] + ', aynı kot)' if ayni and pk['ad'].endswith(')') else
                  pk['ad'] + (' - aynı kot' if ayni else ''), pk['kot_m'], yP, ayni)] + \
        [(q['ad'], q['kot_m'], q['kot_m'] * 100.0, False) for q in katlar]
    for ad, kot, y, alta in seviyeler:
        S.PL([(x_bas, y), (x_son, y)], 'ROTAS-YANGIN-SEMA-KAT', w=1.5)
        if alta:
            S.T(x_bas + 70, y - 16, ad, 13, 'ROTAS-YANGIN-SEMA-KOT', al='ML')
        else:
            S.T(x_bas + 5, y + 18, ad, 13, 'ROTAS-YANGIN-SEMA-KOT', al='ML')
        s_ = '±0,00' if abs(kot) < 1e-6 else (f'+{fmt(kot)}' if kot > 0 else f'-{fmt(-kot)}')
        S.T(x_bas + 5, y - 16, s_, 11, 'ROTAS-YANGIN-SEMA-KOT', al='ML')
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
    dx0, dx1 = x_bas + 30, pg_sol - 90
    S.PL([(dx0, yP), (dx0, yP + 260), (dx1, yP + 260), (dx1, yP)], 'ROTAS-YANGIN-DEPO', w=2.0)
    S.PL([(dx0 + 10, yP + 225), (dx1 - 10, yP + 225)], 'ROTAS-YANGIN-DEPO')
    S.T((dx0 + dx1) / 2, yP + 175, 'YANGIN SUYU DEPOSU', 11, 'ROTAS-YANGIN-DEPO')
    S.T((dx0 + dx1) / 2, yP + 150, f"V = {fmt(hd['V'], 1)} m³ ({hd['sure']} dk)", 10, 'ROTAS-YANGIN-DEPO')
    y_em = y_pg - 15
    S.hat((dx1, y_em), (pg_sol, y_em), [(0.5, 'izlenebilir_kelebek')], 'ROTAS-YANGIN-ANA-BORU', w=3.0)
    S.PL([(pg_sag, y_pg + 20), (pg_sag + 40, y_pg + 20), (pg_sag + 40, y_kol)], 'ROTAS-YANGIN-ANA-BORU', w=4.0)
    x_k0 = pg_sag + 40
    tees = [x_sp] + xs_yg + [x_ib]
    pts = [x_k0] + tees
    for a, b in zip(pts[:-1], pts[1:]):
        S.PL([(a, y_kol), (b, y_kol)], 'ROTAS-YANGIN-ANA-BORU', w=4.0)
        S.cap((a, y_kol), (b, y_kol), f'DN{bdn}', yan=-1, f=0.5 if b - a > 300 else 0.45)
    N = {a: pompa_no(liste, a) for a in ISIM}
    S.balon((dx0 + 40, yP + 300), N['depo'], (dx0 + 40, yP + 260))
    S.balon(((dx1 + pg_sol) / 2 - 30, y_em + 45), N['emk'], ((dx1 + pg_sol) / 2 - 30, y_em))   # R2b: kat yazısından uzak, boru üstünde
    S.balon((x_pg - 42, yP - 40), N['pe'], (x_pg - 42, y_pg - 13))
    S.balon((x_pg + 5, yP - 40), N['pd'], (x_pg, y_pg - 13))
    S.balon((x_pg + 52, yP - 40), N['pj'], (x_pg + 42, y_pg - 9))
    S.balon((x_k0 + 55, y_kol + 45), N['bk'], (x_k0 + 55, y_kol))
    S.T(x_pg, y_pg + 75, 'YANGIN POMPA GRUBU', 11)
    S.T(x_pg, y_pg + 58, f"Q={fmt(sec['Q_sec'], 0)} m³/h  H={fmt(sec['H_sec'], 0)} mSS ({fmt(sec['P_sec'], 1)} bar)", 10)
    # ---------------------------------------------------------------- sprinkler kolonu SP-1 (kademeli çap)
    y_sp_top = ust_kat + 270.0 + 60.0
    S.hat((x_sp, y_kol), (x_sp, yP + 340.0), [(0.55, 'islak_alarm')], 'ROTAS-YANGIN-SPR-BORU', w=4.0)
    S.T(x_sp + 44, y_kol + 0.55 * 190.0 - 6, 'AV-01', 10, 'ROTAS-YANGIN-SEMA-NO', al='ML')
    S.cap((x_sp, y_kol), (x_sp, y_kol + 60), f"DN{zdn['kolon']}", yan=1, f=0.5)
    prev = yP + 340.0
    numara = dict(V=0, FS=0, TD=0, CV=0)
    ekipman = [['AV-01', 'ISLAK ALARM VANA İSTASYONU (SP-1 dibi)', f"DN{zdn['kolon']}", 1]]
    for q in katlar:
        yf = q['kot_m'] * 100.0
        yz = yf + 270.0
        S.PL([(x_sp, prev), (x_sp, yz)], 'ROTAS-YANGIN-SPR-BORU', w=4.0)
        S.cap((x_sp, prev), (x_sp, yz), f"DN{zdn['kolon']}", yan=1, f=0.35 if prev < yf else 0.5)
        prev = yz
        numara['V'] += 1
        numara['FS'] += 1
        numara['TD'] += 1
        vno, fno, tno = f"V-{numara['V']:02d}", f"FS-{numara['FS']:02d}", f"TD-{numara['TD']:02d}"
        xa, xb = x_sp, x_sp + 470.0
        S.hat((xa, yz), (xb, yz), [(90.0 / 470, 'izlenebilir_kelebek'), (190.0 / 470, 'akis_anahtari')],
              'ROTAS-YANGIN-SPR-BORU', w=3.0)
        S.T(xa + 90, yz - 19, vno, 9, 'ROTAS-YANGIN-SEMA-NO')
        S.T(xa + 190, yz - 22, fno, 9, 'ROTAS-YANGIN-SEMA-NO')
        S.T(xa + 400, yz + 14, f"DN{zdn['zon']}", 9, 'ROTAS-YANGIN-SEMA-CAP')
        S.T(xb + 8, yz + 8, f'KAT SPRİNKLER AĞI ({n_bas} BAŞLIK)', 9, al='ML')
        S.T(xb + 8, yz - 8, f"ana hat DN{zdn['kok']} ile başlar", 8, al='ML')
        S.sembol('akis_oku', xb - 6, yz, olcek=1.0)
        xt = xa + 270.0
        yt = yz - 70.0
        S.PL([(xt, yz), (xt, yt)], 'ROTAS-YANGIN-SPR-BORU')
        S.hat((xt, yt), (x_dr, yt), [(0.4, 'test_drenaj')], 'ROTAS-YANGIN-DRENAJ')
        S.T(xt + 0.4 * (x_dr - xt), yt - 16, tno, 9, 'ROTAS-YANGIN-SEMA-NO')
        S.T(xt + 0.78 * (x_dr - xt), yt + 12, 'DN32', 9, 'ROTAS-YANGIN-SEMA-CAP')
        S.T(xt - 18, (yz + yt) / 2, 'DN32', 9, 'ROTAS-YANGIN-SEMA-CAP', rot=90.0)
        ekipman += [[vno, f"İZLENEBİLİR KELEBEK VANA ({q['ad']} zon)", f"DN{zdn['zon']}", 1],
                    [fno, f"AKIŞ ANAHTARI ({q['ad']} zon)", f"DN{zdn['zon']}", 1],
                    [tno, f"TEST VE DRENAJ SETİ ({q['ad']})", 'DN32', 1]]
    S.PL([(x_sp, prev), (x_sp, y_sp_top)], 'ROTAS-YANGIN-SPR-BORU', w=4.0)
    S.sembol('kor_tapa', x_sp, y_sp_top, aci=90.0, olcek=1.5)          # R2: kolon tepesinde purjör YOK
    _kolon_no(S, x_sp, y_sp_top + 75, sp_ad)
    # drenaj kolonu
    y_dr_top = ust_kat + 200.0
    y_dr_alt = yP + 215.0
    S.PL([(x_dr, y_dr_top), (x_dr, y_dr_alt), (x_dr + 90, y_dr_alt)], 'ROTAS-YANGIN-DRENAJ', w=2.0)
    S.T(x_dr + 95, y_dr_alt, 'YER SÜZGECİNE', 9, al='ML')
    S.balon((x_dr + 60, y_dr_alt - 40), N['ys'], (x_dr + 90, y_dr_alt))
    if len(katlar) > 1 or katlar[0]['kot_m'] > pk['kot_m']:
        S.T(x_dr - 16, (yP + 350 + katlar[0]['kot_m'] * 100.0) / 2 + 40, 'DN50', 9, 'ROTAS-YANGIN-SEMA-CAP', rot=90.0)
    _kolon_no(S, x_dr, y_dr_top + 45, 'DR')
    # ---------------------------------------------------------------- dolap kolonları YG
    yd_say = 0
    for xg, kc in zip(xs_yg, kolonlar):
        S.hat((xg, y_kol), (xg, yP + 340.0), [(0.55, 'izlenebilir_kelebek'), (0.25, 'cekvalf')], 'ROTAS-YANGIN-DOLAP-BORU', w=2.0)
        numara['V'] += 1
        numara['CV'] += 1
        vno, cno = f"V-{numara['V']:02d}", f"ÇV-{numara['CV']:02d}"
        S.T(xg + 24, y_kol + 0.55 * 190 + 4, vno, 9, 'ROTAS-YANGIN-SEMA-NO', al='ML')
        S.T(xg + 18, y_kol + 0.25 * 190 - 4, cno, 9, 'ROTAS-YANGIN-SEMA-NO', al='ML')
        ekipman += [[vno, f"İZLENEBİLİR KELEBEK VANA ({kc['ad']} dibi)", f"DN{k['kolon_dn']}", 1],
                    [cno, f"ÇEK VALF ({kc['ad']} dibi)", f"DN{k['kolon_dn']}", 1]]
        prev = yP + 340.0
        y_top = ust_kat + 190.0 + 60.0
        for q in katlar:
            yf = q['kot_m'] * 100.0
            yl = yf + 190.0
            S.PL([(xg, prev), (xg, yl)], 'ROTAS-YANGIN-DOLAP-BORU', w=2.0)
            S.cap((xg, prev), (xg, yl), f"DN{k['kolon_dn']}", yan=1, f=0.3 if prev < yf else 0.45)
            prev = yl
            n = len(kc['dolaplar'])
            xd = [xg + 160.0 + j * 280.0 for j in range(n)]
            S.PL([(xg, yl), (xd[-1], yl)], 'ROTAS-YANGIN-DOLAP-BORU', w=2.0)
            for j in range(n):
                a = xg if j == 0 else xd[j - 1]
                S.cap((a, yl), (xd[j], yl), f"DN{k['besleme_dn']}", yan=1, f=0.5)
            for j, dno in enumerate(kc['dolaplar']):
                yc = yf + 120.0
                xcn = xd[j] - 32.0
                S.PL([(xd[j], yl), (xd[j], yc), (xcn, yc)], 'ROTAS-YANGIN-DOLAP-BORU')
                S.T(xd[j] + 14, (yl + yc) / 2, f"DN{k['baglanti_dn']}", 9, 'ROTAS-YANGIN-SEMA-CAP', rot=90.0)
                S.sembol('yangin_dolabi_kolon', xcn, yc, olcek=1.2)
                yd_say += 1
                lbl = f"{dno} ({q['ad']})" if len(katlar) > 1 else dno
                S.T(xcn - 24, yc + 25 * 1.2 + 10, lbl, 9, 'ROTAS-YANGIN-SEMA-NO')
        S.PL([(xg, prev), (xg, y_top)], 'ROTAS-YANGIN-DOLAP-BORU', w=2.0)
        S.sembol('kor_tapa', xg, y_top, aci=90.0, olcek=1.5)            # R2: purjör YOK
        _kolon_no(S, xg, y_top + 75, kc['ad'])
    # ---------------------------------------------------------------- itfaiye bağlantısı (KOLLEKTÖRLÜ)
    # akış: 2 x DN65 storz (cephe) -> itfaiye kollektörü DN100 -> çek valf -> vana -> basma kollektörü (tesisat ana hattı)
    y_h = yP + 300.0
    IL, IS = 'ROTAS-YANGIN-ITFAIYE', 'ROTAS-YANGIN-ITFAIYE-SEMBOL'
    numara['V'] += 1
    numara['CV'] += 1
    vno_i, cno_i = f"V-{numara['V']:02d}", f"ÇV-{numara['CV']:02d}"
    S.hat((x_ib, y_h), (x_ib, y_kol), [(0.40, 'cekvalf'), (0.72, 'izlenebilir_kelebek')], IL, w=3.0, skat=IS)
    for (xa_, xb_) in ((x_ib - 60, x_ib), (x_ib + 60, x_ib)):
        S.PL([(xa_, y_h + 32), (xa_, y_h), (xb_, y_h)], IL, w=3.0)
    for xs_ in (x_ib - 60, x_ib + 60):
        S.msp.add_blockref(SB.blok_tanimla(S.doc, 'storz'), (xs_, y_h + 32), dxfattribs={'layer': IS, 'rotation': 90.0})
        S.kutular.append(((xs_ - 9, y_h + 32, xs_ + 9, y_h + 46), 'storz'))
        ok_ = S.msp.add_blockref(SB.blok_tanimla(S.doc, 'akis_oku'), (xs_, y_h + 18), dxfattribs={'layer': IS, 'rotation': -90.0})
        S.kutular.append(((xs_ - 5, y_h + 12, xs_ + 5, y_h + 24), 'akis_oku'))
    S.msp.add_blockref(SB.blok_tanimla(S.doc, 'akis_oku'), (x_ib, y_kol + 0.12 * (y_h - y_kol)),
                       dxfattribs={'layer': IS, 'rotation': -90.0})
    # otomatik boşaltma (donma önlemi): kollektör ile çek valf arasında
    y_ob = y_h - 18.0
    S.hat((x_ib, y_ob), (x_ib + 90, y_ob), [(0.45, 'kuresel')], 'ROTAS-YANGIN-DRENAJ', w=0.0)
    S.T(x_ib + 96, y_ob, 'OTOMATİK BOŞALTMA DN25 → DRENAJ', 8, al='ML')
    S.T(x_ib + 84, y_h + 40, '2 x DN65 STORZ (CEPHEDE)', 9, al='ML')
    S.T(x_ib - 74, y_h + 12, 'İTFAİYE KOLLEKTÖRÜ DN100', 8, al='MR')
    S.T(x_ib + 22, y_kol + 0.60 * (y_h - y_kol), cno_i, 9, 'ROTAS-YANGIN-SEMA-NO', al='ML')
    S.T(x_ib + 26, y_kol + 0.28 * (y_h - y_kol), vno_i, 9, 'ROTAS-YANGIN-SEMA-NO', al='ML')
    S.T(x_ib - 16, y_kol + 0.12 * (y_h - y_kol) + 14, 'DN100', 9, 'ROTAS-YANGIN-SEMA-CAP', rot=90.0)
    S.T(x_ib - 80, y_h - 50, 'İTFAİYE BAĞLANTISI', 9, al='MR')
    S.T(x_ib - 80, y_h - 64, '(akış tesisata doğru)', 8, al='MR')
    ekipman += [['İB', 'İTFAİYE BAĞLANTI AĞZI 2 x DN65 STORZ (kör kapaklı, cephede)', 'DN65', 2],
                ['İK', 'İTFAİYE BAĞLANTI KOLLEKTÖRÜ (2 giriş)', 'DN100', 1],
                [cno_i, 'ÇEK VALF (itfaiye bağlantısı; akış tesisata doğru)', 'DN100', 1],
                [vno_i, 'İZLENEBİLİR KELEBEK VANA (itfaiye bağlantısı)', 'DN100', 1],
                ['OB', 'OTOMATİK BOŞALTMA VANASI (donma önlemi)', 'DN25', 1],
                ['YD', 'YANGIN DOLABI TS EN 671-1 (Ø25 x 30 m)', f"DN{k['baglanti_dn']}", yd_say]]
    if hd['bdd'] or sec['bdv_sprinkler']:
        ekipman.append(['BDV', 'BASINÇ DÜŞÜRÜCÜ VANA (alt katlar, önünde/arkasında manometre)', 'proje', '-'])
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
    y1 = S.tablo(x_bas, yb, 'EKİPMAN LİSTESİ (KOLON ŞEMASI)', [('NO', 90, 'C'), ('TANIM', 560, 'L'), ('ÇAP', 90, 'C'),
                                                              ('ADET', 70, 'C')], ekipman)
    pg_rows = [[N[a], [r[1] for r in liste if r[0] == N[a]][0] if N[a] != '?' else '-'] for a in
               ('depo', 'emk', 'pe', 'pd', 'pj', 'bk', 'ys')]
    y2 = S.tablo(x_bas + 900, yb, 'POMPA GRUBU BAĞLANTISI (numaralar YANGIN_POMPA_GRUBU_KESITI cihaz listesi ile aynı)',
                 [('NO', 70, 'C'), ('CİHAZ', 520, 'L')], pg_rows)
    rows = [
        ['Sprinkler debisi (hidrolik, en üst kat)', f"{fmt(hd['Qs'], 0)} l/dk", '-'],
        [f"Dolap debisi ({hd['ne']} x {fmt(k['debi_lpm'], 0)} l/dk)", f"{fmt(hd['Qd'], 0)} l/dk", '-'],
        ['POMPA DEBİSİ (m³/h)', f"{fmt(sec['Q_hes'], 1)} m³/h", f"{fmt(sec['Q_sec'], 0)} m³/h"],
        ['POMPA BASMA (mSS)', f"{fmt(sec['H_hes'], 1)} mSS", f"{fmt(sec['H_sec'], 0)} mSS"],
        ['POMPA BASMA (bar)', f"{fmt(sec['P_hes'], 2)} bar", f"{fmt(sec['P_sec'], 2)} bar"],
        ['Belirleyici / çalışma basıncı hedefi', f"{hd['yonetici']}",
         f"{fmt(sec['aralik'][0], 0)}-{fmt(sec['aralik'][1], 0)} bar"],
        ['Elektrikli / dizel motor gücü (η=0,65, +%10)', f"{fmt(sec['kw_hesap'], 1)} kW", f"{fmt(sec['motor_kW'], 1)} / {fmt(sec['dizel_kW'], 1)} kW"],
        ['Jokey pompa basma', '-', f"{fmt(sec['H_jokey'], 0)} mSS ({fmt(sec['P_jokey'], 1)} bar)"],
        [f"En alt kat ({sec['alt_kat']}) çalışma / kapalı vana", f"{fmt(sec['p_alt_cal'], 2)} / {fmt(sec['p_alt_kap'], 2)} bar",
         f"sınır {fmt(sec['p_max'], 0)} bar"],
        ['DEPO HACMİ', f"{fmt(hd['V'], 1)} m³ ({hd['sure']} dk)", '-'],
    ]
    y3 = S.tablo(x_bas + 900, y2 - 80, 'POMPA SEÇİMİ (SPRİNKLER + DOLAP) - HESAPLANAN / SEÇİLEN',
                 [('KALEM', 380, 'L'), ('HESAPLANAN', 260, 'L'), ('SEÇİLEN', 260, 'L')], rows)
    notlar = [
        'Kolon şeması ölçeksizdir; kat kotları mimari kotlardır. Her katta sprinkler zon vana grubu (izlenebilir kelebek vana, akış anahtarı, test-drenaj) bulunur.',
        f"Yangın dolabı kolonları (YG..) DN{k['kolon_dn']}, dolap bağlantıları DN{k['baglanti_dn']}; kolon diplerinde izlenebilir kelebek vana ve çek valf vardır. Kolon tepeleri kör tapa ile biter (purjör konmaz).",
        f"Ana hat çapları kademelidir: kollektör DN{zdn['kollektor']} - SP-1 kolonu DN{zdn['kolon']} - kat zon hattı DN{zdn['zon']} - kat ağı DN{max(kok_dn, zdn['kok'])}; her ayrımda en fazla bir standart kademe düşülür.",
        'Test-drenaj hatları drenaj kolonu (DR) ile pompa dairesi yer süzgecine verilir.',
        'Daire içindeki numaralar pompa grubu kesiti (YANGIN_POMPA_GRUBU_KESITI) cihaz listesi numaralarıdır.',
        'İtfaiye bağlantısı: 2 x DN65 storz (cephede, kör kapaklı) - DN100 itfaiye kollektörü - çek valf - izlenebilir kelebek vana - pompa çek valflerinden sonraki basma kollektörü; akış dışarıdan tesisata doğrudur. Storz ile çek valf arasında otomatik boşaltma vardır.',
        f"Pompa seçimi: {sec['durum']}; seçilen {fmt(sec['Q_sec'], 0)} m³/h - {fmt(sec['H_sec'], 0)} mSS ({fmt(sec['P_sec'], 2)} bar).",
    ]
    if sec['bdv_sprinkler']:
        notlar.append(f"En alt katta kapalı vana basıncı {fmt(sec['p_alt_kap'], 1)} bar > {fmt(sec['p_max'], 0)} bar: alt kat zon hatlarına basınç düşürücü konacaktır.")
    if hd['bdd']:
        notlar.append(f"Alt katlarda dolap girişinde basınç {fmt(hd['p_alt'], 1)} bar > 9 bar: dolap girişlerine basınç düşürücü konacaktır.")
    if P.get('deneme'):
        notlar.append('DENEME: değerler örnektir, uygulamada kullanılmayacaktır.')
    y_not = min(y1, y3)          # R2b: notlar her iki tablo sütununun altından başlar (POMPA SEÇİMİ tablosuna binmez)
    S.msp.add_text('NOTLAR :', height=14, dxfattribs={'layer': 'ROTAS-YANGIN-NOT', 'style': 'ROTAS', 'width': WF}) \
        .set_placement((x_bas, y_not - 60), align=TA.BOTTOM_LEFT)
    for i, s_ in enumerate(notlar):
        S.msp.add_text(f'{i + 1}. {s_}', height=10, dxfattribs={'layer': 'ROTAS-YANGIN-NOT', 'style': 'ROTAS', 'width': WF}) \
            .set_placement((x_bas, y_not - 85 - i * 22), align=TA.BOTTOM_LEFT)
    # R2b: pafta sonu LEJANT + ADET tablosu (yalnız çizimde kullanılan ROTAS-SMB sembolleri, INSERT sayımından)
    _, sayim = SB.lejant(S.doc, x_son + 150, tepe, baslik='LEJANT VE ADET TABLOSU - YANGIN TESİSATI SEMBOLLERİ')
    S.kademe = dict(zincir=[('kollektör', zdn['kollektor']), ('SP-1 kolonu', zdn['kolon']), ('zon hattı', zdn['zon']),
                            ('kat ağı kökü', max(kok_dn, zdn['kok']))],
                    ag=kademe.kontrol_ag(net, zdn['zon']))
    S.itfaiye_hedef = (x_ib, y_kol)
    S.doc.saveas(cikti)
    return S, sayim


def _kolon_no(S, x, y, ad):
    """kolon numarası: daire (saf geometri) + ortada numara, kolon ekseninde"""
    S.PL([(x, y - 75 + 10), (x, y - 27)], 'ROTAS-YANGIN-SEMA-BALON')
    ins = S.sembol('kolon_no', x, y, olcek=1.0)
    e = S.msp.add_text(ad, height=12, dxfattribs={'layer': 'ROTAS-YANGIN-SEMA-NO', 'style': 'ROTAS', 'width': WF})
    e.set_placement((x, y), align=TA.MIDDLE_CENTER)
    S.yazilar.append(((x - 27, y - 27, x + 27, y + 27), ad))
    return ins


def kontrol(S, dosya):
    """şema: yazı-yazı / yazı-boru / yazı-sembol çakışması, katman adları, MTY yok, purjör yok, 'yetersiz' yok,
    itfaiye çek valf akış yönü, kademeli çap"""
    import itfaiye_test
    d = ezdxf.readfile(dosya)
    msp = d.modelspace()
    kul = {e.dxf.layer for e in msp} | {e.dxf.layer for b in d.blocks for e in b}
    yanlis = sorted(l for l in kul if l not in ('0', 'Defpoints') and not l.startswith('ROTAS-'))
    yy = S.yazilar
    yc = []
    for i in range(len(yy)):
        for j in range(i + 1, len(yy)):
            a, b = yy[i][0], yy[j][0]
            if a[0] < b[2] - 0.5 and a[2] > b[0] + 0.5 and a[1] < b[3] - 0.5 and a[3] > b[1] + 0.5:
                yc.append((yy[i][1], yy[j][1]))
    boru = [c for c in S.cizgiler if c[2] in ('ROTAS-YANGIN-SPR-BORU', 'ROTAS-YANGIN-DOLAP-BORU', 'ROTAS-YANGIN-ANA-BORU',
                                              'ROTAS-YANGIN-DRENAJ', 'ROTAS-YANGIN-ITFAIYE')]
    yb = []
    for k_, s in yy:
        for a, b, lay in boru:
            if min(a[0], b[0]) < k_[2] and max(a[0], b[0]) > k_[0] and min(a[1], b[1]) < k_[3] and max(a[1], b[1]) > k_[1]:
                yb.append((s, lay))
                break
    ys = []
    for k_, s in yy:
        for kb, ad in S.kutular:
            if ad == 'kolon_no':
                continue
            if k_[0] < kb[2] - 1 and k_[2] > kb[0] + 1 and k_[1] < kb[3] - 1 and k_[3] > kb[1] + 1:
                ys.append((s, ad))
                break
    yazilar = [e.dxf.text.upper() for e in msp.query('TEXT')]
    purjor = [t for t in yazilar if 'PURJ' in t.replace('Ö', 'O') and 'YOK' not in t and 'KONMAZ' not in t] + \
        [b.name for b in d.blocks if 'PURJ' in b.name.upper()]
    yetersiz = [t for t in yazilar if 'YETERS' in t or 'UYGUN DEĞİL' in t or 'YETERLİ' in t]
    mty = SB.mty_kontrol(dosya)
    itf = itfaiye_test.kontrol(dosya, S.itfaiye_hedef, katman_on='ROTAS-YANGIN-ITFAIYE')
    kz = kademe.kontrol_zincir(S.kademe['zincir'])
    rap = dict(yanlis_katman=yanlis, yazi_yazi=yc, yazi_boru=yb, yazi_sembol=ys, mty=mty, purjor=purjor, yetersiz_yazisi=yetersiz,
               itfaiye=itf, kademe_zincir=kz, kademe_ag=S.kademe['ag'], dxf_surum=d.dxfversion)
    rap['HATA'] = len(yanlis) + len(yc) + len(yb) + len(ys) + len(mty) + len(purjor) + len(yetersiz) + len(itf['hata']) + \
        len(kz) + len(S.kademe['ag'])
    return rap
