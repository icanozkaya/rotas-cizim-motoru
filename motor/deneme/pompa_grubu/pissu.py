# -*- coding: utf-8 -*-
"""(3) PİS SU DALGIÇ POMPA ÇUKURU KESİTİ — parametrik.
Betonarme çukur (iç ölçü a x b x h), sızdırmaz kapak, giriş borusu, dalgıç pompa, flatörler (durdurma / çalıştırma / alarm),
basma hattı (çukurdan yukarı, çek valf + vana erişilebilir yükseklikte, zemin kotu üzerinden ayrı rögara).
README kuralı: pis su çukuru/pompasına havalık gösterilmez; pompa basma hattı ayrı rögara (R2)."""
import math
from ortak import *
import semboller as S


def ciz(g, yol):
    c = Cizim(g.get('olcek', 20))
    th = c.th
    P, K = g['pompa'], g['cukur']
    a, b, h = K['a_cm'], K.get('b_cm', K['a_cm']), K['h_cm']
    tw, tb = K.get('duvar_cm', 20), K.get('taban_cm', 20)
    ts = K.get('doseme_cm', 30)
    z0 = g.get('doseme_kot_m', 0.0) * 100        # bodrum döşeme kotu (cm)
    n = int(P.get('adet', 1))
    Q, H = P['Q'], P['H']
    dn = P.get('dn_basma', 50)
    y_in = -K.get('giris_derinlik_cm', 35)      # giriş borusu alt kotu (döşemeye göre)
    # seviye kotları
    y_stop = -h + P.get('durma_yuk_cm', 22)
    y_start = y_in - 15
    y_alarm = y_in - 7
    V_fayda = a * b * (y_start - y_stop) / 1e6
    Z = P.get('maks_kalkis_saat', 10)
    V_gerek = Q / (4 * Z)
    dh_gerek = V_gerek / (a * b / 1e4) * 100
    h_gerek = (-y_alarm) + 8 + dh_gerek + P.get('durma_yuk_cm', 22)
    # ---------------------------------------------------------------- betonarme
    XL, XR = -tw - 190, a + tw + 110
    S.kirisli_doseme(c, XL, -tw, -ts, 0)
    S.kirisli_doseme(c, a + tw, XR, -ts, 0)
    S.kirisli_doseme(c, -tw, 0, -h - tb, 0)
    S.kirisli_doseme(c, a, a + tw, -h - tb, 0)
    S.kirisli_doseme(c, 0, a, -h - tb, -h)
    for x in (XL, XR):
        c.KIRIK((x, -ts - 8), (x, 8))
    # sızdırmaz kapak (köşebent çerçeve + kapak)
    c.PL([(-6, 0), (-6, -4), (-1, -4)], EQ, 5)
    c.PL([(a + 6, 0), (a + 6, -4), (a + 1, -4)], EQ, 5)
    c.RECT(-5, 0, a + 5, 2, EQ, 5)
    c.RECT(a / 2 - 8, 2, a / 2 + 8, 3.5, EQ, 5)
    # giriş borusu
    rP = DN_OD[100] / 2
    c.boru([(XL + 30, y_in + rP + 5), (-tw - 2, y_in + rP), (2, y_in + rP)], PB, 100, z=3)
    S.duvar_gecis(c, -tw, 0, y_in + rP, 100)
    c.T(XL + 32, y_in - 6, 'BODRUM PİS SU HATTI Ø100 (%2 EĞİM)', th * 0.85, 'TL', lay=PB)
    c.T(XL + 32, y_in - 6 - th * 1.6, f'çukura giriş alt kotu {kot_s(z0 + y_in)}', th * 0.85, 'TL', lay=PB)
    # ---------------------------------------------------------------- pompa(lar)
    D, Hp = P.get('D', 22), P.get('Hp', 48)
    xs = [a / 2 + 6] if n == 1 else [a * 0.3 + 4, a * 0.7 - 6]
    risers = []
    for i, xp in enumerate(xs):
        fl, kulp, kab = S.dalgic_pompa(c, xp, -h, D, Hp, dn)
        xr = fl[0] + 8
        risers.append((xp, fl, xr, kab))
    # flatörler (sol duvar, kapak altından kablo)
    xfs = [8, 16, 24]
    for xf, yy in zip(xfs, (y_alarm, y_start, y_stop)):
        pass
        S.flator(c, (xf, yy + 7))
    # seviye çizgileri (sağ duvar iç yüzüne kısa)
    for yy in (y_alarm, y_start, y_stop):
        c.L((a - 5, yy), (a - 1, yy), SV, 2)
    # basma: pompa flanşı -> yukarı (kapaktan geçer) -> çek valf -> vana -> yatay -> R2
    y_top = g.get('basma_yatay_cm', 110)
    for xp, fl, xr, kab in risers:
        c.boru([fl, (xr, fl[1]), (xr, y_top), (XR + 30, y_top)], PB, dn)
        c.OCCLUDE(sbox(xr - 4, -1, xr + 4, 4), 6, 'boru_haric')
        c.mty('MTY-CEKVALF VANA', (xr, 35), 90, 1.0, f'DN{dn}')
        c.mty('MTY-KURESEL VANA', (xr, 70), 90, 1.0, f'DN{dn}')
        c.L(kab, (kab[0], 4), EL, 3)
    c.T(XR + 32, y_top, 'ZEMİN KOTU ÜZERİNDEN AYRI RÖGARA (R2)', th * 0.85, 'ML', lay=PB)
    # pano
    xpn = -tw - 160
    S.kirisli_doseme(c, xpn - 15, xpn, 0, 190)
    S.pano(c, xpn, 70, 40, 60, 'P', kaide=0)
    c.L((xpn, 70), (xpn + 40, 70), EQ, 1)
    yk = 25
    c.PL([(risers[0][3][0], 4), (risers[0][3][0], yk), (xpn + 30, yk), (xpn + 30, 70)], EL, 3)
    for k, (xf, yy) in enumerate(zip(xfs, (y_alarm, y_start, y_stop))):
        c.PL([(xf, yy + 7), (xf, 9 + 4 * k), (xpn + 8 + 7 * k, 9 + 4 * k), (xpn + 8 + 7 * k, 70)], EL, 3)
    # ---------------------------------------------------------------- etiketler, kot, ölçü
    def kt(v):
        return z0 + v
    c.T(risers[0][2] - 6, 12, f'DN{dn}', th * 0.85, 'BL', 90, lay=CP)
    c.KOT((XR - 40, 0), kt(0), yazi='BODRUM DÖŞEMESİ')
    c.KOT((a + tw + 8, y_alarm), kt(y_alarm), sag=True, yazi='ALARM')
    c.KOT((a + tw + 50, y_start), kt(y_start), sag=True, yazi='ÇALIŞMA')
    c.KOT((a + tw + 8, y_stop), kt(y_stop), sag=True, yazi='DURMA')
    for yy in (y_alarm, y_start, y_stop):
        c.L((a + tw, yy), (a + tw + 8, yy), SV, 2)
    c.KOT((4, -h), kt(-h), sag=True)
    c.OLCU((0, -h - tb), (a, -h - tb), -25, 'h')
    c.OLCU((-tw, -h - tb), (0, -h - tb), -25, 'h')
    c.OLCU((a, -h - tb), (a + tw, -h - tb), -25, 'h')
    c.OLCU((a + tw, 0), (a + tw, -h), 115, 'v')
    c.OLCU((a + tw, -h), (a + tw, -h - tb), 115, 'v')
    # ---------------------------------------------------------------- numaralar
    N, liste = {}, []
    ADET = dict(pompa=n, cek=n, vana=n, flt=3)

    def no(k, ad, oz):
        if k not in N:
            N[k] = f'{len(N) + 1:02d}'
            liste.append([N[k], ad, ADET.get(k, 1), oz])
        return N[k]
    B = c.BALON
    xp, fl, xr, kab = risers[0]
    B(no('cukur', 'PİS SU ÇUKURU (BETONARME)', [f'iç {a:.0f}x{b:.0f}x{h:.0f} cm', 'su yalıtımlı', 'taban pompaya doğru eğimli']), (a - 10, -h + 6), (a + tw + 30, -h + 20))
    B(no('kapak', 'SIZDIRMAZ ÇUKUR KAPAĞI', [f'{a + 10:.0f}x{b + 10:.0f} cm', 'köşebent çerçeveli, contalı', 'kablo ve boru geçişli']), (a / 2 + 15, 2), (60, 42))
    B(no('pompa', 'DALGIÇ PİS SU POMPASI', [f'Q={tr(Q, 0)} m³/h', f'H={tr(H, 0)} mSS', f'P={tr(P["P"], 1)} kW', 'vortex çarklı', f'serbest geçiş ≥{P.get("serbest_gecis_mm", 50)} mm',
                                            f'{n} adet' + (' (asıl+yedek, sıralı)' if n > 1 else '')]), (xp + 6, -h + 40), (60, -22))
    B(no('cek', 'ÇEK VALF (BİLYELİ, PİS SU TİPİ)', [f'DN{dn}', 'PN10', 'MTY-CEKVALF VANA']), (xr + 7, 35), (xr + 28, 40))
    B(no('vana', 'KÜRESEL VANA (TAM GEÇİŞLİ)', [f'DN{dn}', 'PN16', 'MTY-KURESEL VANA']), (xr + 7, 70), (xr + 28, 75))
    B(no('basma', 'BASMA HATTI', [f'DN{dn} galvaniz/PE100', f'v={tr(hiz(Q, dn))} m/s', 'ayrı rögara (R2)']), (xr + 40, y_top + 2), (xr + 40, y_top + 22))
    B(no('flt', 'SEVİYE FLATÖRÜ', ['durdurma / çalıştırma / alarm', 'kablolu, armut tipi']), (xfs[1] + 4, y_start), (30, -18))
    B(no('giris', 'PİS SU GİRİŞ BORUSU', ['Ø100 PVC', 'bodrum ıslak hacimleri']), (-tw - 40, y_in + rP - 1), (-tw - 40, -60))
    B(no('pano', 'POMPA KUMANDA PANOSU', ['seviye kontrollü', 'yüksek seviye alarmı (sesli/ışıklı)', 'IP54', 'duvara monte']), (xpn + 20, 110), (xpn + 20, 150))
    # ---------------------------------------------------------------- başlık, tablo, notlar
    ty = 200
    c.T(XL, ty + th * 2.4, 'PİS SU DALGIÇ POMPA ÇUKURU KESİTİ ......... ÖLÇEK : 1/%d' % c.olcek, th * 2, 'BL', lay=BS, mask=False)
    if g.get('deneme', True):
        c.T(XL, ty, 'DENEME — değerler örnek/test girdisidir: ' + g.get('kaynak', ''), th * 1.1, 'BL', lay=NT, mask=False)
    yb2 = -h - tb - 90
    c.tablo(XL, yb2, 'PİS SU POMPA ÇUKURU CİHAZ LİSTESİ', liste)
    durum = 'SAĞLANIYOR' if V_fayda >= V_gerek else 'SAĞLANMIYOR'
    notlar = [
        f'1. Çukur iç ölçüsü {a:.0f}x{b:.0f}x{h:.0f} cm; çalışma-durma arası faydalı hacim {tr(V_fayda, 3)} m³.',
        f'2. Saatte en çok {Z} kalkış için gereken hacim V = Q/(4·Z) = {tr(Q, 0)}/(4·{Z}) = {tr(V_gerek, 3)} m³ → {durum}.'
        + ('' if V_fayda >= V_gerek else f' Çalışma-durma farkı ≥ {dh_gerek:.0f} cm için çukur derinliği ≈ {math.ceil(h_gerek / 10) * 10:.0f} cm olmalıdır (kullanıcı onayı).'),
        '3. Alarm seviyesi giriş borusu alt kotunun altında olacak, yüksek seviyede pano sesli/ışıklı alarm verecektir.',
        '4. Basma hattı zemin kotu üzerinden ayrı rögara (R2) bağlanacak, zemin kat kolon hatları basma hattına bağlanmayacaktır.',
        '5. Çek valf ve vana kapak üstünde erişilebilir yükseklikte yapılacaktır.',
        '6. Pis su çukuru ve pompası için havalık gösterilmemiştir (ROTAŞ kuralı).',
    ]
    c.notlar(XL + th * 101 + th * 6, yb2, 'NOTLAR', notlar, th * 62)
    nuy = c.kaydet(yol)
    return c, nuy, dict(V_fayda=round(V_fayda, 3), V_gerek=round(V_gerek, 3), h_gerek=round(h_gerek), durum=durum)


