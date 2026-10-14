# -*- coding: utf-8 -*-
"""(2) HİDROFOR GRUBU KESİTİ (görünüş) — parametrik.
Solda GRP panel su deposu (kesit), önünden geçen emiş kollektörü, dikey çok kademeli pompalar (yan yana),
her pompada emişte küresel vana + esnek bağlantı, basmada esnek bağlantı + çek valf + küresel vana,
üstte basma kollektörü, membranlı tank, basınç şalteri, manometre, kumanda panosu."""
from ortak import *
import semboller as S


def _s(dn):
    return 0.8 if dn <= 32 else 1.0 if dn <= 65 else 1.1


def ciz(g, yol):
    c = Cizim(g.get('olcek', 25))
    th = c.th
    P, DP = g['pompa'], g['depo']
    n = int(P.get('adet', 2))
    Q = P['Q']                                   # set toplam debisi (m³/h)
    q1 = Q / max(1, n - P.get('yedek', 1))       # bir pompanın debisi
    dn_s = dn_sec(Q, 1.0)                        # emiş kollektörü ≤1,0 m/s
    dn_p = P.get('dn_agiz', 40)
    dn_b = dn_sec(Q, 1.5)                        # basma kollektörü ≤1,5 m/s
    # ---------------------------------------------------------------- depo (GRP panel, kesit)
    nx, nz = DP.get('panel_x', 4), DP.get('panel_z', 2)
    W, Hd = nx * 100, nz * 100
    ny = DP['V_m3'] / (W / 100 * Hd / 100)
    x1 = -40; x0 = x1 - W; yk = DP.get('kaide_cm', 20)
    XL = x0 - 80; XR = g.get('oda_sag_cm', 520); YT = g.get('oda_yukseklik_cm', 300); ts = 25
    S.kirisli_doseme(c, XL - 25, XR + 25, -ts, 0)
    S.kirisli_doseme(c, XL - 25, XR + 25, YT, YT + ts)
    S.kirisli_doseme(c, XL - 25, XL, 0, YT)
    S.kirisli_doseme(c, XR, XR + 25, 0, YT)
    c.RECT(x0 - 8, 0, x1 + 8, yk, KD, 1)
    c.HATCH([(x0 - 8, 0), (x1 + 8, 0), (x1 + 8, yk), (x0 - 8, yk)], TR, 1)
    yb = yk
    c.RECT(x0 - 2, yb, x1 + 2, yb + Hd + 4, EQ, 4)                 # GRP dış
    c.RECT(x0, yb + 2, x1, yb + Hd + 2, EQ, 4)                     # GRP iç
    for i in range(1, nx):                                          # panel birleşim flanşları
        xx = x0 + 100 * i
        c.L((xx, yb + Hd + 4), (xx, yb + Hd + 9), EQ, 4)
    for j in range(1, nz):
        yy = yb + 2 + 100 * j
        c.L((x0 - 2, yy), (x0 - 7, yy), EQ, 4); c.L((x1 + 2, yy), (x1 + 7, yy), EQ, 4)
    h_max = yb + 2 + Hd - 15
    h_min = yb + 2 + DP.get('min_su_cm', 30)
    c.L((x0 + 3, h_max), (x1 - 3, h_max), SV, 1)
    for k in range(4):
        c.L((x0 + 60 + 70 * k, h_max - 5), (x0 + 90 + 70 * k, h_max - 5), SV, 1)
    c.T(x0 + 150, yb + 120, 'KULLANMA SUYU DEPOSU (GRP)', th * 1.2, 'MC', lay=BS)
    c.T(x0 + 150, yb + 103, f'V = {tr(DP["V_m3"], 0)} m³', th, 'MC')
    c.T(x0 + 150, yb + 90, f'{nx} x {tr(ny, 1)} x {nz} m panel', th * 0.85, 'MC')
    # dolum (şamandıralı), taşma, boşaltma, menhol, havalık, kuru çalışma flatörü
    xf = x0 + 330
    c.boru([(xf, YT + ts + 25), (xf, yb + Hd + 4)], SB, 32)
    c.OCCLUDE(sbox(xf - 4, YT, xf + 4, YT + ts), 5, 'boru_haric')
    c.OCCLUDE(sbox(xf - 2, yb + Hd + 1, xf + 2, yb + Hd + 5), 5, 'boru_haric')
    c.boru([(xf, yb + Hd + 4), (xf, h_max + 12)], SB, 32, z=5)
    S.samandira_vana(c, (xf, h_max + 8), kol=28)
    c.OCCLUDE(Point(xf - 36, h_max + 8 - 9.8 - 2).buffer(10), 2)
    c.vana('kuresel', (xf, YT - 30), 90, 0.8, 'DN32')
    c.T(xf + 6, YT + ts + 18, 'ŞEBEKEDEN DOLUM', th * 0.85, 'BL', lay=SB)
    yt = yb + Hd - 5
    c.boru([(x0 + 15, yt), (x0 - 50, yt), (x0 - 50, 22)], DR, 65, kalin=0.8)
    c.OCCLUDE(sbox(x0 - 3, yt - 4, x0 + 1, yt + 4), 5, 'boru_haric')
    S.huni(c, (x0 - 50, 8)); S.yer_suzgeci(c, x0 - 50, 0)
    c.boru([(x0 + 10, yb + 10), (x0 - 25, yb + 10), (x0 - 25, 2)], DR, 40, kalin=0.6)
    c.OCCLUDE(sbox(x0 - 3, yb + 6, x0 + 1, yb + 14), 5, 'boru_haric')
    c.vana('kuresel', (x0 - 25, yb - 6), 90, 0.8, 'DN40')
    S.yer_suzgeci(c, x0 - 25, 0)
    S.menhol(c, x0 + 40, yb + Hd + 4, 60)
    xh = x0 + 180
    c.boru([(xh, yb + Hd + 4), (xh, yb + Hd + 30)], SB, 50, kalin=0.4)
    c.ARC((xh + 6, yb + Hd + 30), 6, 0, 180, EQ, 3)
    c.L((xh + 12, yb + Hd + 30), (xh + 12, yb + Hd + 26), EQ, 3)
    xfl = x1 - 60
    c.L((xfl, yb + Hd + 2), (xfl, h_min + 12), EQ, 3)          # flatör askı halatı (R2: kablo çizilmez)
    S.flator(c, (xfl, h_min + 12))
    # ---------------------------------------------------------------- emiş: depo çıkışı -> vana -> pislik tutucu -> kollektör (önde)
    y_s = yb + 20
    xs_son = 120 + 130 * (n - 1) - 75
    c.boru([(x1 - 25, y_s), (xs_son + 1, y_s)], SB, dn_s, z=3)
    c.boru_occ([(x1 + 2, y_s), (xs_son, y_s)], dn_s, 3)
    c.OCCLUDE(sbox(x1 - 1, y_s - 5, x1 + 3, y_s + 5), 5, 'boru_haric')
    c.RECT(xs_son + 1, y_s - DN_OD[dn_s] / 2 * 1.4, xs_son + 3, y_s + DN_OD[dn_s] / 2 * 1.4, EQ, 4)
    c.vana('kuresel', (x1 + 22, y_s), 0, _s(dn_s), f'DN{dn_s}', z=6)
    c.vana('pislik_tutucu', (x1 + 50, y_s), 0, _s(dn_s), f'DN{dn_s}', z=6)
    # ---------------------------------------------------------------- pompalar
    kj = P.get('kaide_cm', 40)
    Hm, Dm, Bp = P.get('Hm', 85), P.get('Dm', 22), P.get('Bp', 25)
    y_kb = g.get('basma_kollektor_cm', 200)
    pomp = []
    for i in range(n):
        xc = 120 + 130 * i
        sI, bI = S.dikey_pompa(c, xc, 0, Hm, Dm, Bp, 14, dn_p, kaide=kj, kaide_gen=Bp + 30)
        xv = xc - 75; xr = xc + 30
        c.boru([(xv, y_s), (xv, sI[1]), sI], SB, dn_p)
        c.vana('kuresel', (xc - 60, sI[1]), 0, _s(dn_p), f'DN{dn_p}')
        c.vana('esnek', (xc - 36, sI[1]), 0, _s(dn_p), f'DN{dn_p}')
        c.boru([bI, (xr, bI[1]), (xr, y_kb)], SB, dn_p)
        c.vana('esnek', (xr, 80), 90, _s(dn_p), f'DN{dn_p}')
        c.vana('cekvalf', (xr, 115), 90, _s(dn_p), f'DN{dn_p}')
        c.vana('kuresel', (xr, 150), 90, _s(dn_p), f'DN{dn_p}')
        pomp.append((xc, xv, xr, sI))
    # ---------------------------------------------------------------- basma kollektörü, çıkış, membranlı tank, şalter, manometre
    xk0 = pomp[0][2] - 25
    x_cik = pomp[-1][2] + 45
    xm = x_cik + 50
    c.boru([(xk0, y_kb), (xm, y_kb)], SB, dn_b)
    c.RECT(xk0 - 3, y_kb - DN_OD[dn_b] / 2 * 1.4, xk0 - 1, y_kb + DN_OD[dn_b] / 2 * 1.4, EQ, 4)
    c.boru([(x_cik, y_kb), (x_cik, YT + ts + 30)], SB, dn_b)
    c.OCCLUDE(sbox(x_cik - 5, YT, x_cik + 5, YT + ts), 5, 'boru_haric')
    c.vana('kuresel', (x_cik, y_kb + 45), 90, _s(dn_b), f'DN{dn_b}')
    c.T(x_cik + 8, YT + ts + 22, 'BİNA KULLANMA SUYU ŞEBEKESİNE', th * 0.85, 'ML', lay=SB)
    mt = S.membranli_tank(c, xm, 0, P.get('mtank_D', 45), P.get('mtank_H', 75))
    c.boru([(xm, y_kb), mt], SB, 25)
    c.vana('kuresel', (xm, 120), 90, 0.8, 'DN25')
    xps = xk0 + 45
    c.boru([(xps, y_kb), (xps, y_kb + 22)], SB, 15, kalin=0)
    c.vana('kuresel', (xps, y_kb + 14), 90, 0.5, 'DN15')
    S.basinc_salteri(c, (xps, y_kb + 22))
    xmn = xk0 + 85
    c.vana('manometre', (xmn, y_kb), 0, 1.0, kes=False)
    # pano
    xp0 = xm + 45
    S.pano(c, xp0, 0, 60, 110, 'H', kaide=40)
    # ---------------------------------------------------------------- etiketler, kot, ölçü
    def cap(x, y, s, rot=0, lay=CP):
        c.T(x, y, s, th * 0.85, 'BC', rot, lay=lay)
    cap((xk0 + xps) / 2 + 5, y_kb + 10, f'DN{dn_b}')
    cap(x1 + 68, y_s + 9, f'DN{dn_s}')
    cap(pomp[0][2] - 7, 180, f'DN{dn_p}', 90)
    cap(x_cik - 7, 270, f'DN{dn_b}', 90)
    c.KOT((XR - 40, 0), 0)
    c.KOT((x0 + 260, yb + 2), yb, sag=True)
    c.KOT((x0 + 200, h_max), h_max, sag=True, yazi='MAKS. SU')
    c.KOT((x0 + 200, h_min), h_min, sag=True, yazi='KURU ÇALIŞMA KESME')
    c.KOT((xm + 30, y_kb + DN_OD[dn_b] / 2), y_kb, sag=True)
    c.KOT((XR - 60, YT), YT, yazi='TAVAN ALTI')
    c.OLCU((x0, -ts), (x1, -ts), -30, 'h')
    c.OLCU((XL - 25, 0), (XL - 25, YT), -30, 'v')
    for i in range(n - 1):
        c.OLCU((pomp[i][0], -ts), (pomp[i + 1][0], -ts), -30, 'h')
    # ---------------------------------------------------------------- numaralar
    N, liste = {}, []
    PB_ = P['H'] / 10.2
    ADET = dict(kur=1 + 2 * n + 3, esnek=2 * n, cek=n, pompa=n, ys=2, kaide=n)

    def no(k, ad, oz):
        if k not in N:
            N[k] = f'{len(N) + 1:02d}'
            liste.append([N[k], ad, ADET.get(k, 1), oz])
        return N[k]
    B = c.BALON
    B(no('depo', 'KULLANMA SUYU DEPOSU (GRP PANEL)', [f'V={tr(DP["V_m3"], 0)} m³', f'{nx}x{tr(ny, 1)}x{nz} m', 'gıdaya uygun', 'çelik/beton kaide üzerinde']), (x0 + 30, yb + 60), (x0 + 30, yb + 80))
    B(no('sam', 'ŞAMANDIRALI DOLUM VANASI', ['DN32', 'şebeke beslemeli', 'önünde küresel vana']), (xf - 5, h_max + 8), (xf - 30, 150))
    B(no('tas', 'TAŞMA BORUSU (AÇIK UÇLU, SİNEK TELLİ)', ['DN65', 'yer süzgecine görünür akıtma']), (x0 - 50, 150), (x0 - 70, 165))
    B(no('bos', 'DİP BOŞALTMA HATTI', ['DN40', 'küresel vanalı']), (x0 - 25, 60), (x0 + 15, 75))
    B(no('men', 'MENHOL (KİLİTLİ KAPAK)', ['60x60 cm']), (x0 + 70, yb + Hd + 11), (x0 + 70, yb + Hd + 30))
    B(no('hav', 'HAVALIK (SİNEK TELLİ, KAZ BOYNU)', ['DN50']), (xh + 6, yb + Hd + 36), (xh + 30, yb + Hd + 45))
    B(no('flt', 'KURU ÇALIŞMA KORUMA FLATÖRÜ', ['seviye düşünce pompaları durdurur', 'panoya bağlı']), (xfl, h_min + 5), (xfl - 30, h_min + 25))
    B(no('emk', 'EMİŞ KOLLEKTÖRÜ', [f'DN{dn_s}', f'v={tr(hiz(Q, dn_s))} m/s', 'kör flanşlı uç']), (x1 + 85, y_s - 4), (x1 + 85, y_s - 30))
    B(no('kur', 'KÜRESEL VANA', ['DN15 - DN65', 'PN16']), (x1 + 22, y_s + 5), (x1 + 22, y_s + 28))
    B(no('pt', 'PİSLİK TUTUCU (Y TİPİ)', [f'DN{dn_s}']), (x1 + 50, y_s + 6), (x1 + 50, y_s + 28))
    B(no('pompa', 'HİDROFOR POMPASI (DİKEY ÇOK KADEMELİ)', [f'Q={tr(q1, 2)} m³/h', f'H={tr(P["H"], 0)} mSS', f'P={tr(P["P"], 1)} kW', '400V 50Hz',
                                                           f'{n - P.get("yedek", 1)} asıl + {P.get("yedek", 1)} yedek', 'frekans konvertörlü']), (pomp[0][0], 100), (pomp[0][0] - 40, 120))
    for xc, xv, xr, sI in pomp[1:]:
        B(N['pompa'], (xc, 100), (xc - 40, 120))
    B(no('esnek', 'ESNEK BAĞLANTI (KAUÇUK KÖRÜKLÜ)', [f'DN{dn_p}', 'PN16']), (pomp[0][0] - 36, pomp[0][3][1] + 6), (pomp[0][0] - 36, 85))
    B(no('cek', 'ÇEK VALF', [f'DN{dn_p}', 'PN16']), (pomp[0][2] + 7, 115), (pomp[0][2] + 22, 125))
    for xc, xv, xr, sI in pomp[1:]:
        B(N['cek'], (xr + 7, 115), (xr + 22, 125))
    B(no('bk', 'BASMA KOLLEKTÖRÜ', [f'DN{dn_b}', f'v={tr(hiz(Q, dn_b))} m/s']), (pomp[-1][2] + 20, y_kb + 3), (pomp[-1][2] + 20, y_kb + 25))
    B(no('mt', 'MEMBRANLI BASINÇ TANKI', [f'{P.get("mtank_L", 100)} L', '10 bar', 'gıdaya uygun membran']), (xm + 10, 50), (xm + 10, 98))
    B(no('ps', 'BASINÇ ŞALTERİ / TRANSMİTTER', [f'devreye {tr(PB_ - 0.5, 1)} bar / durur {tr(PB_, 1)} bar', 'küresel vanalı']), (xps + 5, y_kb + 34), (xps + 25, y_kb + 46))
    B(no('mano', 'MANOMETRE (MUSLUKLU)', ['Ø100', '0-10 bar']), (xmn + 5, y_kb + 22), (xmn + 25, y_kb + 34))
    B(no('pano', 'HİDROFOR KUMANDA PANOSU', ['frekans konvertörlü', 'kuru çalışma koruması', 'sıralı/yedekli çalışma', 'IP54']), (xp0 + 30, 120), (xp0 + 30, 175))
    B(no('ys', 'YER SÜZGECİ (SİFONLU)', ['DN100']), (x0 - 50, -3), (x0 - 75, -12))
    B(N['ys'], (x0 - 25, -3), (x0 - 2, -12))
    B(no('kaide', 'POMPA KAİDESİ (BETON) + TİTREŞİM TAKOZU', [f'h={kj} cm']), (pomp[0][0] + 18, 10), (pomp[0][0] + 18, -12))
    # ---------------------------------------------------------------- başlık, tablo, not
    ty = YT + ts + 70
    c.T(XL - 25, ty + th * 2.4, 'HİDROFOR GRUBU KESİTİ (GÖRÜNÜŞ) ......... ÖLÇEK : 1/%d' % c.olcek, th * 2, 'BL', lay=BS, mask=False)
    if g.get('deneme', True):
        c.T(XL - 25, ty, 'DENEME — değerler örnek/test girdisidir: ' + g.get('kaynak', ''), th * 1.1, 'BL', lay=NT, mask=False)
    yb2 = -ts - 100
    yend = c.tablo(XL - 25, yb2, 'HİDROFOR GRUBU CİHAZ LİSTESİ', liste)
    notlar = [
        f'1. Hidrofor seti {n} pompalı ({n - P.get("yedek", 1)} asıl + {P.get("yedek", 1)} yedek) olup set debisi Q={tr(Q, 2)} m³/h, basma yüksekliği H={tr(P["H"], 0)} mSS seçilmiştir.',
        f'2. Emiş kollektörü DN{dn_s} (v={tr(hiz(Q, dn_s))} m/s), basma kollektörü DN{dn_b} (v={tr(hiz(Q, dn_b))} m/s) yapılacaktır.',
        '3. Depo çıkışında küresel vana ve pislik tutucu, her pompa emiş ve basmasında esnek bağlantı ile kesme vanası, basmada çek valf bulunacaktır.',
        '4. Depoda kuru çalışma koruma flatörü bulunacak, su seviyesi düştüğünde pompalar pano üzerinden durdurulacaktır.',
        '5. Taşma ve boşaltma hatları açık uç bırakılmayacak, görünür akıtma ile yer süzgecine bağlanacaktır.',
        '6. Basınç şalteri ayar değerleri öneridir; en elverişsiz musluk basıncına göre devreye almada kesinleştirilecektir.',
        '7. Vana ve armatür sembolleri saf geometri ROTAS-SMB bloklarıdır; çaplar boru üzerindeki DN etiketlerindedir. Elektrik bağlantıları gösterilmez.',
    ]
    ynot = c.notlar(XL - 25 + th * 101 + th * 6, yb2, 'NOTLAR', notlar, th * 70)
    c.lejant(XL - 25, min(yend, ynot) - th * 8)      # R2b: kullanılan sembollerin lejantı + adet
    nuy = c.kaydet(yol)
    return c, nuy, dict(dn_s=dn_s, dn_p=dn_p, dn_b=dn_b, ny=ny, q1=q1)
