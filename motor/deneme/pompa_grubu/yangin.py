# -*- coding: utf-8 -*-
"""(1) YANGIN POMPA GRUBU KESİTİ (görünüş) — parametrik.
Görünüş: pompa dairesi boyuna kesiti; pompalar yan görünüşte (mil çizim düzleminde), emiş kollektörü pompaların
önünden döşemeye yakın geçer (arkasında kalan kaide/şasi çizgileri kırpılır), basma kollektörü üstte.
Depo solda (kesit, kısaltılmış), sağda dizel yakıt tankı ve pompa panoları."""
import math
from ortak import *
import semboller as S

EN12845_BATMA = {65: 25, 80: 31, 100: 37, 125: 44, 150: 50, 200: 62, 250: 75}   # emiş ağzı üstü min. su (cm) - teyit


def _s(dn):
    return 0.8 if dn <= 32 else 1.0 if dn <= 65 else 1.1 if dn <= 100 else 1.25


def ciz(g, yol):
    c = Cizim(g.get('olcek', 25))
    th = c.th
    E, D, J, DP = g['elektrikli'], g['dizel'], g['jokey'], g['depo']
    Q = E['Q']
    # ---------------------------------------------------------------- çaplar (hız sınırları)
    dn_se = dn_sec(1.4 * Q, 1.8)            # emiş: %140 debide ≤1,8 m/s (EN 12845)
    dn_be = dn_sec(Q, 3.0)                  # basma branşmanı ≤3 m/s
    dn_kb = max(dn_se, dn_sec(1.4 * Q, 2.5))  # basma kollektörü
    dn_t = dn_sec(1.5 * Q, 3.5)             # test hattı %150 debi
    dn_js, dn_jb = dn_sec(J['Q'], 1.0), dn_sec(J['Q'], 2.0)
    dn_ee, dn_eb = E.get('dn_emis_agzi', 100), E.get('dn_basma_agzi', 80)
    # ---------------------------------------------------------------- depo
    W_ic, H_ic, h_max = DP.get('ic_genislik_cm', 600), DP.get('ic_yukseklik_cm', 300), DP.get('maks_su_cm', 270)
    tw, ts = DP.get('duvar_cm', 30), DP.get('doseme_cm', 25)
    y_s = 35                                # emiş kollektörü ekseni
    y_agiz = 10                             # çan ağzı (girdap önleyici plaka üstü)
    h_min = y_agiz + EN12845_BATMA.get(dn_se, 50)
    h_ef = h_max - h_min
    derinlik = DP['V_m3'] / (W_ic / 100 * h_ef / 100)
    WS = 230                                # kesitte gösterilen depo genişliği (kırık çizgiyle kısaltılmış)
    XR = g.get('oda_genislik_cm', 1400)     # sağ duvar iç yüzü
    YT = g.get('oda_yukseklik_cm', 450)
    # betonarme: döşeme, depo duvarı, depo tavanı, pompa dairesi tavanı, sağ duvar
    S.kirisli_doseme(c, -WS, XR + 25, -ts, 0)
    S.kirisli_doseme(c, 0, tw, 0, H_ic)
    S.kirisli_doseme(c, -WS, tw, H_ic, H_ic + ts)
    S.kirisli_doseme(c, -WS, XR + 25, YT, YT + ts)
    S.kirisli_doseme(c, XR, XR + 25, 0, YT)
    for y0, y1 in ((-ts, 0), (H_ic, H_ic + ts), (YT, YT + ts)):
        c.KIRIK((-WS, y0 - 8), (-WS, y1 + 8))
    c.KIRIK((-WS, 8), (-WS, H_ic - 8))
    # su seviyeleri
    c.L((-WS + 15, h_max), (-3, h_max), SV, 1)
    c.L((-WS + 15, h_min), (-3, h_min), SV, 1)
    for k in range(4):
        xx = -WS + 40 + k * 45
        c.L((xx, h_max - 5), (xx + 22, h_max - 5), SV, 1)
    c.T(-122, h_max + 3, 'MAKS. SU SEVİYESİ', th * 0.85, 'BL', lay=SV)
    yakin = abs(h_min - y_s) < 25                # min. su kotu emiş ekseni kotuna yakın: yazılar ayrılır
    c.T(-WS + 20, h_min - 4 if yakin else h_min + 3, 'MİN. SU SEVİYESİ (EN 12845 batma)', th * 0.85, 'TL' if yakin else 'BL', lay=SV)
    c.T(-WS / 2 - 10, 205, 'YANGIN SUYU DEPOSU', th * 1.3, 'MC', lay=BS)
    c.T(-WS / 2 - 10, 185, f'V = {tr(DP["V_m3"], 0)} m³ (efektif)', th, 'MC')
    c.T(-WS / 2 - 10, 170, f'iç ölçü {W_ic:.0f} x {derinlik * 100:.0f} x {H_ic:.0f} cm', th * 0.85, 'MC')
    c.T(-WS / 2 - 10, 156, f'h ef = {tr(h_ef / 100)} m (kesit kısaltılmıştır)', th * 0.85, 'MC')
    # emiş ağzı + girdap önleyici + duvar geçişi
    xin = -70
    c.boru([(tw, y_s), (xin, y_s), (xin, y_agiz + 12)], YB, dn_se, z=3)
    S.girdap_onleyici(c, xin, y_agiz, dn_se)
    S.duvar_gecis(c, 0, tw, y_s, dn_se)
    # dolum (şamandıralı), taşma, dip boşaltma, menhol, seviye göstergesi
    xf = -180
    c.boru([(xf, YT + ts + 25), (xf, 287)], SB, 32, z=2)
    c.OCCLUDE(sbox(xf - 4, YT, xf + 4, YT + ts), 5, 'boru_haric')
    c.OCCLUDE(sbox(xf - 4, H_ic, xf + 4, H_ic + ts), 5, 'boru_haric')
    S.samandira_vana(c, (xf, 283), kol=25)
    c.OCCLUDE(Point(xf - 33, 283 - 8.75 - 2).buffer(10), 2)
    c.T(xf + 5, YT + ts + 18, 'ŞEBEKEDEN DOLUM', th * 0.85, 'BL', lay=SB)
    c.boru([(-30, 280), (160, 280), (160, 22)], DR, 80, z=2, kalin=1.0)
    S.duvar_gecis(c, 0, tw, 280, 80)
    S.huni(c, (160, 8))
    S.yer_suzgeci(c, 160, 0)
    c.boru([(-10, 12), (95, 12), (95, 2)], DR, 50, z=2, kalin=0.8)
    S.duvar_gecis(c, 0, tw, 12, 50)
    c.vana('kuresel', (62, 12), 0, 1.0, 'DN50')
    S.yer_suzgeci(c, 108, 0)
    S.menhol(c, -110, H_ic + ts, 65)
    S.seviye_gostergesi(c, 42, 52, 262)
    for yy in (58, 256):
        c.OCCLUDE(sbox(0, yy - 1.5, tw, yy + 1.5), 5, 'boru_haric')
        c.L((tw, yy), (0, yy), EQ, 6)
    # ---------------------------------------------------------------- pompalar
    pompalar = {}
    # elektrikli asıl pompa
    xvE, xpE = 200, 330
    sE, bE = S.uc_emisli_pompa(c, xpE, 0, E.get('A', 125), E.get('B', 54), E.get('Hm', 168.2), False, dn_ee, dn_eb)
    # dizel yedek pompa
    xvD, xpD = 670, 800
    sD, bD = S.uc_emisli_pompa(c, xpD, 0, D.get('A', 157.6), D.get('B', 97.8), D.get('Hm', 179.5), True, dn_ee, dn_eb)
    y_ax = sE[1]
    y_kb = g.get('basma_kollektor_cm', 370)
    for ad, xv, sf, bf in (('E', xvE, sE, bE), ('D', xvD, sD, bD)):
        # emiş branşmanı: kollektörden yukarı, yatay pompaya
        xr = sf[0] - 12
        c.boru([(xv, y_s), (xv, y_ax), (xr - 10, y_ax)], YB, dn_se)
        c.boru([(xr + 10, y_ax), sf], YB, dn_ee)
        S.redüksiyon(c, (xr, y_ax), dn_se, dn_ee, 0, True)
        c.vana('izlenebilir_kelebek', (xv + 30, y_ax), 0, _s(dn_se), f'DN{dn_se}')
        c.vana('manometre', (xv + 55, y_ax), 0, 1.0, kes=False)
        c.vana('kompansator', (xv + 80, y_ax), 0, _s(dn_se) * 0.45, f'DN{dn_se}')
        # basma: konsantrik red., kompansatör, manometre, (emniyet), çek valf, izlenebilir kelebek, kollektör
        xb = bf[0]
        c.boru([bf, (xb, bf[1] + 10)], YB, dn_eb)
        S.redüksiyon(c, (xb, bf[1] + 20), dn_eb, dn_be, 90, False)
        c.boru([(xb, bf[1] + 30), (xb, y_kb)], YB, dn_be)
        c.vana('kompansator', (xb, 160), 90, _s(dn_be) * 0.45, f'DN{dn_be}')
        c.vana('manometre', (xb, 195), -90, 1.0, kes=False)
        c.vana('cekvalf', (xb, 250), 90, _s(dn_be), f'DN{dn_be}')
        c.vana('izlenebilir_kelebek', (xb, 300), 90, _s(dn_be), f'DN{dn_be}')
        pompalar[ad] = (xv, sf, bf)
    # dizel emniyet (tahliye) vanası: çek valften önce, sola; tahliye huni -> yer süzgeci
    xbD = bD[0]
    xrv = xbD - 30
    c.boru([(xbD, 215), (xrv, 215)], YB, 32)
    c.vana('emniyet', (xrv, 215), 0, 1.0, 'DN32', kes=False, sx=-1.0)
    c.boru([(xrv - 17, 205), (xrv - 17, 120), (xvD - 7, 120), (xvD - 7, 2)], DR, 32, z=2, kalin=0.6)
    S.yer_suzgeci(c, xvD - 7, 0)
    # jokey pompa (dikey çok kademeli, beton kaide üzerinde)
    xj = 560; kj = 40
    sJ, bJ = S.dikey_pompa(c, xj, 0, J.get('Hm', 91.3), J.get('Dm', 20), J.get('Bp', 25), 14, dn_js, kaide=kj, kaide_gen=55)
    xvJ, xrJ = 490, 595
    c.boru([(xvJ, y_s), (xvJ, sJ[1]), sJ], YB, dn_js)
    c.vana('kuresel', (xvJ + 16, sJ[1]), 0, _s(dn_js), f'DN{dn_js}')
    c.vana('pislik_tutucu', (xvJ + 36, sJ[1]), 0, _s(dn_js), f'DN{dn_js}')
    c.boru([bJ, (xrJ, bJ[1]), (xrJ, y_kb)], YB, dn_jb)
    c.vana('cekvalf', (xrJ, 125), 90, _s(dn_jb), f'DN{dn_jb}')
    c.vana('kuresel', (xrJ, 165), 90, _s(dn_jb), f'DN{dn_jb}')
    c.vana('manometre', (xrJ, 200), -90, 1.0, kes=False)
    # membranlı tank (jokey hattına, çek valf sonrası)
    xm = 632
    mt = S.membranli_tank(c, xm, 0, J.get('mtank_D', 36), J.get('mtank_H', 50))
    c.boru([(xrJ, 235), (xm, 235), mt], YB, 25)
    c.vana('kuresel', (xm, 150), 90, 0.8, 'DN25')
    # emiş kollektörü (önde)
    c.boru([(tw, y_s), (xvD + 1, y_s)], YB, dn_se, z=3)
    c.boru_occ([(tw, y_s), (xvD, y_s)], dn_se, 3)
    c.RECT(xvD + 1, y_s - DN_OD[dn_se] / 2 * 1.4, xvD + 3, y_s + DN_OD[dn_se] / 2 * 1.4, EQ, 4)   # kör flanş
    # ---------------------------------------------------------------- basma kollektörü + çıkış + test hattı
    x_cik = 1000
    xk0 = 100
    c.boru([(xk0, y_kb), (x_cik, y_kb), (x_cik, YT + ts + 30)], YB, dn_kb)
    c.OCCLUDE(sbox(x_cik - 6, YT, x_cik + 6, YT + ts), 5, 'boru_haric')
    c.RECT(xk0 - 3, y_kb - DN_OD[dn_kb] / 2 * 1.4, xk0 - 1, y_kb + DN_OD[dn_kb] / 2 * 1.4, EQ, 4)
    c.vana('izlenebilir_kelebek', (x_cik, 410), 90, _s(dn_kb), f'DN{dn_kb}')
    c.T(x_cik + 14, YT + ts + 22, 'YANGIN TESİSATINA (SPRİNKLER + DOLAP ANA HATTI)', th * 0.85, 'ML', lay=YB)
    # test hattı: kollektör sol ucu -> yukarı -> depo üstünden depoya
    xt_in = -135
    y_t = 420
    c.boru([(xk0 + 25, y_kb), (xk0 + 25, y_t), (xt_in, y_t), (xt_in, H_ic - 12)], YB, dn_t)
    c.OCCLUDE(sbox(xt_in - 8, H_ic, xt_in + 8, H_ic + ts), 5, 'boru_haric')
    c.vana('kelebek', (95, y_t), 0, _s(dn_t), f'DN{dn_t}')
    S.debimetre(c, (30, y_t), dn_t)
    c.vana('kelebek', (-25, y_t), 0, _s(dn_t), f'DN{dn_t}')
    # basınç şalterleri + kollektör manometresi + hava purjörü
    ps_x = (420, 470, 520)
    for x in ps_x:
        c.boru([(x, y_kb), (x, y_kb + 22)], YB, 15, kalin=0)
        c.vana('kuresel', (x, y_kb + 14), 90, 0.5, 'DN15')
        S.basinc_salteri(c, (x, y_kb + 22))
    c.vana('manometre', (720, y_kb), 0, 1.0, kes=False)
    # ---------------------------------------------------------------- dizel: egzoz, yakıt tankı
    A_D = D.get('A', 157.6)
    xe = xpD + A_D * 0.55 + 6
    ye0 = D.get('Hm', 179.5) + 15 - 5
    S.esnek_egzoz(c, xe, ye0, ye0 + 30, 10)
    c.boru([(xe, ye0 + 30), (xe, 300), (920, 300)], EG, 100, z=2)
    S.susturucu(c, 920, 300, 140, 32)
    c.boru([(1060, 300), (XR + 25 + 40, 300)], EG, 100, z=2)
    c.OCCLUDE(sbox(XR - 1, 290, XR + 26, 310), 5, 'boru_haric')
    c.T(XR + 25 + 5, 312, 'DIŞ ATMOSFERE', th * 0.85, 'BL', lay=EG)
    xy0 = 1000
    fb, fr = S.yakit_tanki(c, xy0, 0, 80, 40, 80)
    xrad = xpD + A_D - 5
    c.boru([fb, (xrad, fb[1])], YK, 15, kalin=0.4)
    c.boru([fr, (xrad, fr[1])], YK, 15, kalin=0.4)
    c.vana('kuresel', ((xrad + xy0) / 2, fb[1]), 0, 0.45, 'DN15')
    # ---------------------------------------------------------------- itfaiye bağlantısı (KOLLEKTÖRLÜ) — R2
    # akış: cephedeki 2 x DN65 storz -> itfaiye kollektörü (düşey, DN100) -> çek valf -> vana -> tesisat çıkış hattı
    y_it = 432.0
    x_ik = XR - 15
    y_in = (355.0, 400.0)
    itf_hedef = (x_cik, y_it)
    if g.get('itfaiye', False):
        c.boru([(x_ik, y_in[0] - 10), (x_ik, y_it), (x_cik, y_it)], IT, 100)
        for yy in y_in:
            c.boru([(x_ik, yy), (XR + 25 + 25, yy)], IT, 65)
            c.OCCLUDE(sbox(XR - 1, yy - 7, XR + 26, yy + 7), 5, 'boru_haric')
            c.vana('storz', (XR + 25 + 25, yy), 0, 1.0, kes=False, lay=ITS)
            c.vana('akis_oku', (XR + 25 + 12, yy), 180, 0.9, kes=False, lay=ITS)
        c.vana('cekvalf', (1250, y_it), 180, 1.0, 'DN100', lay=ITS)
        c.vana('izlenebilir_kelebek', (1130, y_it), 180, 1.0, 'DN100', lay=ITS)
        c.vana('akis_oku', (1320, y_it), 180, 0.9, kes=False, lay=ITS)
        c.vana('akis_oku', (1060, y_it), 180, 0.9, kes=False, lay=ITS)
        # otomatik boşaltma (donma önlemi): kollektör dibinden
        c.boru([(x_ik, y_in[0] - 10), (x_ik, 330), (1310, 330)], DR, 25, z=2, kalin=0.5)
        c.vana('kuresel', (1345, 330), 0, 0.6, 'DN25')
        c.T(1305, 330, 'OTOMATİK BOŞALTMA DN25 → DRENAJ', th * 0.8, 'MR', lay=DR)
        c.T(1190, y_it + 7, 'İTFAİYE HATTI DN100', th * 0.8, 'BC', lay=CP)
        c.T(XR + 25 + 40, y_in[1] + 26, '2 x DN65 STORZ (CEPHEDE)', th * 0.8, 'BC', lay=IT)
    # ---------------------------------------------------------------- panolar
    px = [(1110, 80, 190, 'E'), (1205, 80, 190, 'D'), (1300, 60, 120, 'J')]
    for x0, Wp, Hp, t in px:
        S.pano(c, x0, 0, Wp, Hp, t)
    # ---------------------------------------------------------------- çap etiketleri
    def cap(x, y, s, rot=0, lay=CP):
        c.T(x, y, s, th * 0.85, 'BC', rot, lay=lay)
    cap(250, y_s + 11, f'DN{dn_se}')
    cap(bE[0] - 9, 275, f'DN{dn_be}', 90)
    cap(bD[0] - 9, 275, f'DN{dn_be}', 90)
    cap(xrJ - 6, 290, f'DN{dn_jb}', 90)
    cap(620, y_kb + 11, f'BASMA KOLLEKTÖRÜ DN{dn_kb}', lay=YB)
    cap(-120, y_t + 9, f'TEST HATTI DN{dn_t}', lay=YB)
    cap(x_cik - 9, 440, f'DN{dn_kb}', 90)
    cap(1150, 304, 'EGZOZ Ø100', lay=EG)
    cap(80, 285, 'TAŞMA DN80', lay=DR)
    # ---------------------------------------------------------------- kotlar
    c.KOT((1368, 0), 0)
    c.KOT((-180, 0), 0)
    c.KOT((-65, h_max), h_max, sag=True)
    c.KOT((-WS + 18 if yakin else -100, h_min), h_min, sag=True)
    c.KOT((-WS + 90, H_ic + ts), H_ic + ts, sag=True)
    c.KOT((-25, y_s + DN_OD[dn_se] / 2), y_s, sag=False, yazi='EMİŞ EKSENİ')
    c.KOT((1300, YT), YT, yazi='TAVAN ALTI')
    c.KOT((785, y_kb + DN_OD[dn_kb] / 2), y_kb, yazi='KOLLEKTÖR EKSENİ')
    # ---------------------------------------------------------------- ölçüler
    c.OLCU((-WS, 0), (-WS, H_ic), -40, 'v')
    c.OLCU((-WS, H_ic), (-WS, H_ic + ts), -40, 'v')
    c.OLCU((XR + 25, 0), (XR + 25, YT), 120 if g.get('itfaiye') else 45, 'v')
    c.OLCU((tw, -ts), (bE[0], -ts), -35, 'h')
    c.OLCU((bE[0], -ts), (bD[0], -ts), -35, 'h')
    c.OLCU((bD[0], -ts), (x_cik, -ts), -35, 'h')
    c.OLCU((x_cik, -ts), (XR, -ts), -35, 'h')
    # ---------------------------------------------------------------- numaralar (cihaz listesi ile eşleşir)
    N = {}
    liste = []

    def no(anahtar, ad, oz):
        if anahtar not in N:
            N[anahtar] = f'{len(N) + 1:02d}'
            liste.append([N[anahtar], ad, ADET.get(anahtar, 1), oz])
        return N[anahtar]

    itf = g.get('itfaiye', False)
    ADET = dict(ikv=5 + itf, komp=4, ered=2, kred=2, mano=6, cek=3 + itf, kur=8 + itf, kv=2, ps=3, ys=3, kaide=3, itf=2)

    Pn = E['H'] / 10.2
    PJ = J['H'] / 10.2
    B = c.BALON
    B(no('depo', 'YANGIN SUYU DEPOSU (BETONARME)', [f'V={tr(DP["V_m3"], 0)} m³ efektif', f'{g.get("calisma_suresi_dk", 60)} dk',
                                                   f'iç {W_ic:.0f}x{derinlik * 100:.0f}x{H_ic:.0f} cm', 'iç yüzey su yalıtımlı']), (-WS + 30, 120), (-WS + 30, 140))
    B(no('vorteks', 'EMİŞ AĞZI + GİRDAP ÖNLEYİCİ PLAKA', [f'DN{dn_se} çan ağızlı', 'plaka 2D x 2D', 'EN 12845']), (xin - 30, y_agiz), (-150, 16 if yakin else 30))
    B(no('gecis', 'SU TUTUCU FLANŞLI DUVAR GEÇİŞ PARÇASI', [f'DN{dn_se}', 'beton dökümünden önce yerleştirilir']), (tw / 2, y_s + 20), (tw / 2, 100))
    B(no('emk', 'EMİŞ KOLLEKTÖRÜ', [f'DN{dn_se} çelik boru', f'v={tr(hiz(1.4 * Q, dn_se))} m/s (%140 debi)', 'kör flanşlı uç']), (430, y_s - 7), (430, -12))
    B(no('pe', 'ELEKTRİKLİ YANGIN POMPASI (ASIL)', [f'Q={tr(Q, 0)} m³/h', f'H={tr(E["H"], 0)} mSS', f'P={tr(E["P"], 0)} kW', '400V 50Hz',
                                                   f'{E.get("rpm", 2900)} rpm', 'EN 733 uç emişli', '%140 Q da ≥%70 H']), (xpE + 90, 80), (xpE + 90, 140))
    B(no('pd', 'DİZEL YANGIN POMPASI (YEDEK)', [f'Q={tr(D["Q"], 0)} m³/h', f'H={tr(D["H"], 0)} mSS', f'P={tr(D["P"], 0)} kW',
                                               f'{D.get("rpm", 2900)} rpm', 'akülü marş (2 set akü)', 'radyatör soğutmalı']), (xpD + 110, 120), (xpD + 128, 238))
    B(no('pj', 'JOKEY POMPA (DİKEY ÇOK KADEMELİ)', [f'Q={tr(J["Q"], 0)} m³/h', f'H={tr(J["H"], 0)} mSS', f'P={tr(J["P"], 1)} kW', '400V 50Hz']), (xj, 110), (xj - 32, 150))
    B(no('ikv', 'İZLENEBİLİR KELEBEK VANA (SİNYAL ANAHTARLI)', [f'emiş DN{dn_se}', f'basma DN{dn_be}', f'çıkış DN{dn_kb}', 'PN16']), (xvE + 30, y_ax + 12), (xvE + 30, 100))
    B(N['ikv'], (xvD + 30, y_ax + 12), (xvD + 30, 100))
    B(N['ikv'], (bE[0] - 12, 300), (bE[0] - 32, 300))
    B(N['ikv'], (bD[0] - 12, 300), (bD[0] - 32, 300))
    B(N['ikv'], (x_cik + 8, 405), (x_cik + 30, 395))
    B(no('komp', 'KOMPANSATÖR (KAUÇUK KÖRÜKLÜ, FLANŞLI)', [f'DN{dn_se} / DN{dn_be}', 'PN16']), (xvE + 80, y_ax + 6), (xvE + 80, 100))
    B(N['komp'], (bE[0] + 6, 160), (bE[0] + 30, 160))
    B(N['komp'], (bD[0] + 6, 160), (bD[0] + 30, 160))
    B(N['komp'], (xvD + 80, y_ax + 6), (xvD + 80, 100))
    B(no('ered', 'EKSANTRİK REDÜKSİYON (ÜST DÜZ)', [f'DN{dn_se}/DN{dn_ee}', 'emişte hava cebi oluşmaz']), (sE[0] - 12, y_ax + 4), (sE[0] - 12, 128))
    B(N['ered'], (sD[0] - 12, y_ax + 4), (sD[0] - 5, 100))
    B(no('kred', 'KONSANTRİK REDÜKSİYON', [f'DN{dn_eb}/DN{dn_be}']), (bE[0] + 5, bE[1] + 20), (bE[0] + 30, 125))
    B(N['kred'], (bD[0] + 5, bD[1] + 20), (bD[0] + 30, 125))
    B(no('mano', 'MANOMETRE / VAKUM-MANOMETRE (MUSLUKLU)', ['Ø100 gliserinli', '0-16 bar (basma)', '-1/+5 bar (emiş)']), (xvE + 55, y_ax + 25), (xvE + 55, 128))
    B(N['mano'], (xvD + 55, y_ax + 25), (xvD + 55, 128))
    B(N['mano'], (bE[0] + 25, 195), (bE[0] + 45, 210))
    B(N['mano'], (bD[0] + 25, 195), (bD[0] + 45, 210))
    B(N['mano'], (xrJ + 25, 200), (xrJ + 45, 215))
    B(N['mano'], (720, y_kb + 25), (745, y_kb + 30))
    B(no('cek', 'ÇEK VALF (YAYLI, FLANŞLI)', [f'DN{dn_be} / DN{dn_jb}', 'PN16']), (bE[0] + 8, 250), (bE[0] + 30, 250))
    B(N['cek'], (bD[0] + 8, 250), (bD[0] + 30, 250))
    B(N['cek'], (xrJ + 7, 125), (xrJ + 14, 105))
    B(no('emn', 'EMNİYET (BASINÇ TAHLİYE) VANASI', ['DN32', 'dizel pompa çıkışı', 'çek valf öncesi', f'ayar {tr(Pn * 1.15, 1)} bar']), (xrv - 4, 235), (xrv - 30, 255))
    B(no('bk', 'BASMA KOLLEKTÖRÜ', [f'DN{dn_kb} çelik boru', 'kör flanşlı uç']), (300, y_kb + 8), (300, y_kb + 30))
    B(no('ps', 'BASINÇ ŞALTERİ (PRESOSTAT)', [f'PS-J: devreye {tr(PJ - 0.5, 1)} / durur {tr(PJ, 1)} bar', f'PS-E: devreye {tr(Pn, 1)} bar (elle durdurulur)',
                                            f'PS-D: devreye {tr(Pn - 0.5, 1)} bar', 'her biri küresel vanalı']), (ps_x[0] - 5, y_kb + 34), (ps_x[0] - 25, y_kb + 46))
    B(N['ps'], (ps_x[1] - 5, y_kb + 34), (ps_x[1] - 25, y_kb + 46))
    B(N['ps'], (ps_x[2] - 5, y_kb + 34), (ps_x[2] - 25, y_kb + 46))
    B(no('debi', 'TEST HATTI DEBİMETRESİ', [f'DN{dn_t}', f'ölçme aralığı 0-{tr(1.6 * Q, 0)} m³/h', 'önünde ≥10D, arkasında ≥5D düz boru']), (30, y_t + 20), (30, y_t + 40))
    B(no('kv', 'KELEBEK VANA (TEST HATTI)', [f'DN{dn_t}', 'PN16']), (95, y_t + 7), (110, y_t + 30))
    B(N['kv'], (-25, y_t + 7), (-40, y_t + 30))
    if itf:
        B(no('itf', 'İTFAİYE BAĞLANTI AĞZI (STORZ)', ['2 x DN65 storz', 'kör kapaklı, zincirli', 'cephede, araç ≤ 18 m', 'BYKHY Md. 97']), (XR + 25 + 32, y_in[0] - 7), (XR + 25 + 60, y_in[0] - 30))
        B(no('itk', 'İTFAİYE BAĞLANTI KOLLEKTÖRÜ', ['DN100, 2 girişli', 'altında otomatik boşaltma', 'akış tesisata doğru']), (x_ik - 6, 378), (x_ik - 40, 378))
        B(N['cek'], (1250, y_it - 7), (1250, y_it - 30))
        B(N['ikv'], (1130, y_it - 8), (1130, y_it - 30))
    B(no('kur', 'KÜRESEL VANA', ['DN15 - DN50', 'PN16']), (xvJ + 16, sJ[1] + 4), (xvJ + 16, 92))
    B(N['kur'], (xrJ + 6, 165), (xrJ + 14, 182))
    B(N['kur'], (xm + 6, 150), (xm + 30, 150))
    B(N['kur'], (62, 16), (80, 75))
    if itf:
        B(N['kur'], (1345, 335), (1350, 352))
    B(no('pt', 'PİSLİK TUTUCU (Y TİPİ)', [f'DN{dn_js}', 'jokey emişi']), (xvJ + 36, sJ[1] + 6), (xvJ + 46, 92))
    B(no('mt', 'MEMBRANLI BASINÇ TANKI', [f'{J.get("mtank_L", 24)} L', '16 bar', 'jokey kısa çalışmayı önler']), (xm - 10, 50), (xm - 22, 82))
    B(no('pnE', 'ELEKTRİKLİ POMPA KONTROL PANOSU', ['IP54', 'otomatik/manuel', 'yıldız-üçgen yol verme', 'faz koruma', 'arıza alarmı']), (1150, 120), (1150, 230))
    B(no('pnD', 'DİZEL POMPA KONTROL PANOSU', ['IP54', 'otomatik start', '2 set akü şarj ünitesi', '6 deneme startı', 'arıza alarmı']), (1245, 120), (1245, 230))
    B(no('pnJ', 'JOKEY POMPA PANOSU', ['basınç kontrollü otomatik', 'IP54', '400V']), (1330, 90), (1330, 160))
    B(no('yt', 'DİZEL YAKIT TANKI', [f'{D.get("yakit_L", 100)} L', 'seviye göstergeli, havalıklı', 'taşma tavalı (drenaj havuzu)', 'motor besleme seviyesinin üstünde']), (1040, 112), (1040, 160))
    B(no('egz', 'EGZOZ SUSTURUCU + ESNEK BAĞLANTI', ['Ø100', 'yalıtımlı', 'dış atmosfere']), (990, 316), (990, 345))
    B(no('sam', 'ŞAMANDIRALI DOLUM VANASI', ['DN32', 'şebeke beslemeli']), (xf, 287), (xf + 30, 240))
    B(no('tas', 'TAŞMA BORUSU (AÇIK UÇLU)', ['DN80', 'görünür akıtma, yer süzgecine']), (160, 200), (180, 220))
    B(no('ys', 'YER SÜZGECİ (SİFONLU)', ['DN100', 'pompa dairesi drenajı']), (160, -3), (185, -12))
    B(N['ys'], (108, -3), (135, -12))
    B(N['ys'], (xvD - 7, -3), (xvD + 18, -12))
    B(no('men', 'MENHOL (KİLİTLİ KAPAK)', ['65x65 cm', 'depo üst döşemesi']), (-78, H_ic + ts + 9), (-78, H_ic + ts + 32))
    B(no('svg', 'SEVİYE GÖSTERGESİ (MANYETİK)', ['depo yüksekliği boyunca', 'alt/üst bağlantı vanalı']), (42, 150), (65, 165))
    B(no('kaide', 'BETON KAİDE + TİTREŞİM TAKOZU', ['pompa başına', 'h=15 cm (jokey h=40 cm)']), (xpE + 20, 7), (xpE + 20, -12))
    # ---------------------------------------------------------------- başlık, tablo, notlar
    ty = YT + ts + 70
    c.T(-WS, ty + th * 2.4, 'YANGIN POMPA GRUBU KESİTİ (GÖRÜNÜŞ) ......... ÖLÇEK : 1/%d' % c.olcek, th * 2, 'BL', lay=BS, mask=False)
    if g.get('deneme', True):
        c.T(-WS, ty, 'DENEME — değerler örnek/test girdisidir: ' + g.get('kaynak', ''), th * 1.1, 'BL', lay=NT, mask=False)
    yb = -ts - 110
    yend = c.tablo(-WS, yb, 'YANGIN POMPA GRUBU CİHAZ LİSTESİ', liste)
    notlar = [
        f'1. Asıl elektrikli ve dizel yedek pompaların her biri %100 kapasitede (Q={tr(Q, 0)} m³/h, H={tr(E["H"], 0)} mSS) olacak, pompa karakteristiği %140 debide anma basıncının en az %70\'ini sağlayacaktır.',
        f'2. Emiş kollektörü ve branşmanları DN{dn_se} seçilmiştir; %140 debide hız {tr(hiz(1.4 * Q, dn_se))} m/s ≤ 1,8 m/s (EN 12845) olacaktır.',
        f'3. Basma branşmanları DN{dn_be} (v={tr(hiz(Q, dn_be))} m/s), basma kollektörü DN{dn_kb}, test hattı DN{dn_t} (%150 debide v={tr(hiz(1.5 * Q, dn_t))} m/s) yapılacaktır.',
        f'4. Pozitif emiş: depo efektif hacminin tamamı pompa ekseninin (+{tr(y_ax / 100)}) üstündedir (EN 12845: ≥ 2/3).',
        f'5. Depo iç ölçüsü {W_ic:.0f} x {derinlik * 100:.0f} cm, maks. su +{tr(h_max / 100)}, min. su +{tr(h_min / 100)} (emiş ağzı + {EN12845_BATMA.get(dn_se, 50)} cm batma, EN 12845 tablosundan teyit edilecektir).',
        '6. Emişte eksantrik redüksiyon düz yüzü üstte olacak şekilde takılacak, emiş hattında hava cebi oluşturacak yükselme yapılmayacaktır.',
        '7. Dizel pompa emniyet vanası çek valften önce bağlanacak, tahliyesi görünür huni ile yer süzgecine verilecektir.',
        '8. Basınç şalteri ayar değerleri öneridir; devreye alma sırasında sistem eğrisine göre kesinleştirilecektir.',
        '9a. İtfaiye bağlantısı: 2 x DN65 storz (cephe, kör kapaklı) -> DN100 itfaiye kollektörü -> çek valf -> izlenebilir kelebek vana -> pompa çek valflerinden sonraki tesisat ana hattı; akış dışarıdan tesisata doğrudur, kollektör altında otomatik boşaltma vardır (BYKHY Md. 97).' if itf else '',
        '9. Dizel egzozu yalıtımlı ve susturuculu olarak dış atmosfere verilecek, pompa dairesi en az +10 °C\'de tutulacak, yanma havası menfezi yapılacaktır.',
        '10. Vana ve armatür sembolleri saf geometri ROTAS-SMB bloklarıdır; çaplar boru üzerindeki DN etiketlerindedir. Elektrik kablo/sinyal hatları bu kesitte gösterilmez (elektrik projesi).',
    ]
    notlar = [n_ for n_ in notlar if n_]
    c.notlar(-WS + sum([th * 4, th * 30, th * 5, th * 62]) + th * 6, yb, 'NOTLAR', notlar, th * 75)
    n = c.kaydet(yol)
    return c, n, dict(itf_hedef=itf_hedef if g.get('itfaiye') else None, dn_se=dn_se, dn_be=dn_be, dn_kb=dn_kb, dn_t=dn_t, dn_js=dn_js, dn_jb=dn_jb, derinlik=derinlik, h_min=h_min)
