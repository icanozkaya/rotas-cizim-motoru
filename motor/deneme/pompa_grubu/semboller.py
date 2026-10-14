# -*- coding: utf-8 -*-
"""Görünüş/kesit ekipman çizimleri (gerçek ölçü oranlı, cm). MTY kütüphanesinde karşılığı olmayan parçalar.
Pompa modülleri motor/ekipman.py (EN 733 uç emişli + elektrik motoru / dizel modül, DAB verisi) kayıtlarından aktarılır."""
import math
import cad, ekipman
from ortak import EQ, GZ, KD, TR, BT, SV, YB, SB, PB, YK, EG, DR, EL, DN_OD

_LMAP = {ekipman.EQ: EQ, ekipman.GZ: GZ, ekipman.KD: KD, ekipman.TR: TR, ekipman.OL: EQ, ekipman.YZ: EQ}


def ekipman_aktar(c, fn, *a, z=1, **kw):
    """motor/ekipman.py fonksiyonunu çalıştırıp cad.R kayıtlarını Cizim'e aktar (yazılar hariç)"""
    cad.R.clear()
    fn(*a, **kw)
    for r in cad.R:
        t = r[0]; ly = _LMAP.get(r[1], EQ)
        if t == 'L':
            c.L(r[2], r[3], ly, z)
        elif t == 'P':
            c.PL(r[2], ly, z, r[3])
        elif t == 'C':
            c.C(r[2], r[3], ly, z)
        elif t == 'S':
            c.SOLIDFILL([r[2], r[3], r[4]], ly, z)
    cad.R.clear()


# ------------------------------------------------------------------ pompa modülleri
def uc_emisli_pompa(c, xp, y0, A, B, H, dizel, dn_e, dn_b, kaide=15, z=1):
    """EN 733 uç emişli pompa yan görünüşü. Dönüş: emiş flanşı (xp-5, ax), basma flanşı üstü (xp+25, ax+45), ax=y0+kaide+47"""
    ekipman_aktar(c, ekipman._pompa_modul, 'Y', xp, y0, A, B, H, dizel, dn_e, dn_b, kaide, z=z)
    # titreşim takozları (kaide ile şasi arası)
    for xx in (xp + 8, xp + A - 12):
        c.RECT(xx, y0 + kaide - 0.01, xx + 6, y0 + kaide + 2.5, EQ, z)
    ax = y0 + kaide + 47
    if dizel:      # dizel: akü + marş motoru + yağ karteri
        c.RECT(xp + 70, y0 + kaide + 12, xp + 98, y0 + kaide + 26, EQ, z)
    return (xp - 5, ax), (xp + 25, ax + 45)


def dikey_pompa(c, x, y0, H, Dm, Bp, hp, dn, z=1, kaide=0, kaide_gen=None):
    """dikey çok kademeli in-line pompa (Grundfos CR tipi) ön görünüş; emiş solda, basma sağda, port ekseni y0+kaide+hp.
    H: kaide üstünden toplam yükseklik, Dm: motor çapı, Bp: taban genişliği. Dönüş: (emiş flanş ucu, basma flanş ucu)"""
    if kaide:
        kg = kaide_gen or Bp + 30
        c.RECT(x - kg / 2, y0, x + kg / 2, y0 + kaide, KD, z)
        c.HATCH([(x - kg / 2, y0), (x + kg / 2, y0), (x + kg / 2, y0 + kaide), (x - kg / 2, y0 + kaide)], TR, z)
    yb = y0 + kaide
    yp = yb + hp
    c.RECT(x - Bp / 2, yb, x + Bp / 2, yb + 3, EQ, z)                      # taban plakası
    c.PL([(x - Bp / 2 + 3, yb + 3), (x - Bp / 2 + 3, yp + 5), (x + Bp / 2 - 3, yp + 5), (x + Bp / 2 - 3, yb + 3)], EQ, z)  # pompa ayağı
    po = DN_OD.get(dn, 4) / 2
    fl = po * 1.9
    for s in (-1, 1):                                                         # emiş/basma ağızları + flanş
        x1 = x + s * (Bp / 2 - 3); x2 = x + s * (Bp / 2 + 4)
        c.L((x1, yp + po), (x2, yp + po), EQ, z); c.L((x1, yp - po), (x2, yp - po), EQ, z)
        c.RECT(min(x2, x2 + s * 1.6), yp - fl, max(x2, x2 + s * 1.6), yp + fl, EQ, z)
    hs = H * 0.48                                                             # kademe gövdesi
    c.RECT(x - Dm * 0.33, yp + 5, x + Dm * 0.33, yb + hs, EQ, z)
    for xx in (x - Dm * 0.45, x + Dm * 0.45):                                 # gergi cıvataları
        c.L((xx, yp + 5), (xx, yb + hs), EQ, z)
    c.RECT(x - Dm * 0.5, yb + hs, x + Dm * 0.5, yb + hs + 2.5, EQ, z)        # üst kafa
    c.PL([(x - Dm * 0.42, yb + hs + 2.5), (x - Dm * 0.3, yb + hs + H * 0.12), (x + Dm * 0.3, yb + hs + H * 0.12),
          (x + Dm * 0.42, yb + hs + 2.5)], EQ, z)                             # motor taşıyıcı (fener)
    ym = yb + hs + H * 0.12
    c.RECT(x - Dm / 2, ym, x + Dm / 2, yb + H - 6, EQ, z)                    # motor
    for i in range(1, 6):
        xx = x - Dm / 2 + Dm * i / 6
        c.L((xx, ym + 3), (xx, yb + H - 9), GZ, z)                            # soğutma kanatları
    c.RRECT(x - Dm / 2 + 1, yb + H - 6, x + Dm / 2 - 1, yb + H, 2, EQ, z)    # fan kapağı
    c.RECT(x + Dm / 2, ym + (yb + H - ym) * 0.45, x + Dm / 2 + Dm * 0.25, ym + (yb + H - ym) * 0.7, EQ, z)  # klemens kutusu
    return (x - Bp / 2 - 5.6, yp), (x + Bp / 2 + 5.6, yp)


def membranli_tank(c, x, y0, D, H, z=1, ust_baglanti=True):
    """dikey membranlı basınç tankı (ayaklı); bağlantı üstte (küçük) veya altta"""
    r = D / 2
    for xx in (x - r * 0.7, x + r * 0.7):
        c.L((xx - 1, y0), (xx - 1, y0 + 8), EQ, z); c.L((xx + 1, y0), (xx + 1, y0 + 8), EQ, z)
        c.L((xx - 2.5, y0), (xx + 2.5, y0), EQ, z)
    c.RRECT(x - r, y0 + 6, x + r, y0 + 6 + H, r * 0.45, EQ, z)
    c.ARC((x, y0 + 6 + H * 0.62), r * 0.92, 200, 340, GZ, z)                 # membran
    if ust_baglanti:
        c.RECT(x - 2, y0 + 6 + H, x + 2, y0 + 6 + H + 3, EQ, z)
        return (x, y0 + 9 + H)
    return (x, y0 + 6)


def pano(c, x0, y0, W, H, tip='E', z=1, kaide=10):
    """pompa kumanda panosu ön görünüş (gerçek görünüş: kapı, gösterge, sinyal lambaları, butonlar, menteşe)"""
    c.RECT(x0, y0, x0 + W, y0 + kaide, KD, z)
    yb = y0 + kaide
    c.RECT(x0, yb, x0 + W, yb + H, EQ, z)
    c.RECT(x0 + 2, yb + 2, x0 + W - 2, yb + H - 2, EQ, z)                   # kapı
    for yy in (yb + H * 0.2, yb + H * 0.8):
        c.RECT(x0 + 0.5, yy - 3, x0 + 2, yy + 3, EQ, z)                      # menteşe
    c.RECT(x0 + W - 6, yb + H * 0.48, x0 + W - 4, yb + H * 0.58, EQ, z)     # kol
    c.RECT(x0 + W * 0.2, yb + H * 0.78, x0 + W * 0.8, yb + H * 0.9, EQ, z)  # ekran / ampermetre
    for i in range(4):
        c.C((x0 + W * (0.2 + 0.2 * i), yb + H * 0.7), min(W, H) * 0.025 + 0.8, EQ, z)   # sinyal lambaları
    c.C((x0 + W * 0.35, yb + H * 0.6), min(W, H) * 0.04, EQ, z)             # seçici şalter
    c.L((x0 + W * 0.35 - min(W, H) * 0.03, yb + H * 0.6), (x0 + W * 0.35 + min(W, H) * 0.03, yb + H * 0.6), EQ, z)
    c.C((x0 + W * 0.65, yb + H * 0.6), min(W, H) * 0.045, EQ, z)            # acil stop
    c.C((x0 + W * 0.65, yb + H * 0.6), min(W, H) * 0.025, EQ, z)
    for i in range(5):                                                       # havalandırma panjuru
        yy = yb + H * 0.08 + i * 2.5
        c.L((x0 + W * 0.3, yy), (x0 + W * 0.7, yy), EQ, z)
    return (x0 + W / 2, yb + H)


def yakit_tanki(c, x0, y0, W, Ht, ayak, z=1):
    """dizel yakıt tankı (ayaklı) + taşma tavası + seviye göstergesi + dolum kapağı + havalık"""
    c.RECT(x0 - 8, y0, x0 + W + 8, y0 + 12, EQ, z)                          # tava (drenaj havuzu)
    c.RECT(x0 - 6, y0 + 2, x0 + W + 6, y0 + 12, EQ, z)
    for xx in (x0 + 5, x0 + W - 9):
        c.RECT(xx, y0 + 2, xx + 4, y0 + ayak, EQ, z)                        # ayaklar
    c.L((x0 + 9, y0 + ayak * 0.4), (x0 + W - 9, y0 + ayak * 0.4), EQ, z)    # bağlantı lamas
    yb = y0 + ayak
    c.RRECT(x0, yb, x0 + W, yb + Ht, 3, EQ, z)
    c.RECT(x0 + W * 0.7, yb + Ht, x0 + W * 0.7 + 12, yb + Ht + 4, EQ, z)    # dolum kapağı
    c.L((x0 + W * 0.25, yb + Ht), (x0 + W * 0.25, yb + Ht + 25), YK, z)     # havalık
    c.ARC((x0 + W * 0.25 + 4, yb + Ht + 25), 4, 0, 180, YK, z)
    c.RECT(x0 + W - 4, yb + 5, x0 + W - 1, yb + Ht - 5, EQ, z)              # seviye göstergesi
    c.L((x0 + W - 2.5, yb + 8), (x0 + W - 2.5, yb + Ht * 0.6), GZ, z)
    return (x0, yb + 6), (x0, yb + 14)                                      # besleme, dönüş bağlantıları (sol yan)


def susturucu(c, x0, y, L, D, z=1):
    """yatay egzoz susturucusu (bombeli uçlu silindir) + askı"""
    r = D / 2
    c.PL([(x0 + r * 0.5, y - r), (x0 + L - r * 0.5, y - r)], EQ, z)
    c.PL([(x0 + r * 0.5, y + r), (x0 + L - r * 0.5, y + r)], EQ, z)
    c.ARC((x0 + r * 0.5, y), r, 90, 270, EQ, z)
    c.ARC((x0 + L - r * 0.5, y), r, -90, 90, EQ, z)
    for xx in (x0 + L * 0.25, x0 + L * 0.75):
        c.L((xx, y + r), (xx, y + r + 20), EQ, z)
        c.L((xx - 4, y + r + 20), (xx + 4, y + r + 20), EQ, z)


def esnek_egzoz(c, x, y0, y1, d, z=1):
    """dikey egzoz körüğü (paslanmaz esnek bağlantı)"""
    n = 6; h = (y1 - y0) / n
    for i in range(n):
        yy = y0 + i * h
        c.PL([(x - d / 2, yy), (x - d / 2 - 1.5, yy + h / 2), (x - d / 2, yy + h)], EQ, z)
        c.PL([(x + d / 2, yy), (x + d / 2 + 1.5, yy + h / 2), (x + d / 2, yy + h)], EQ, z)


def redüksiyon(c, p, dn1, dn2, ang=0, eksantrik=True, L=20, z=3):
    """dn1 -> dn2 (akış yönünde). eksantrik: üst yüzey düz (emişte hava cebi oluşmaz)"""
    r1, r2 = DN_OD[dn1] / 2, DN_OD[dn2] / 2
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)

    def P(u, v):
        return (p[0] + u * ca - v * sa, p[1] + u * sa + v * ca)
    if eksantrik:
        pts = [P(-L / 2, r1), P(L / 2, r1), P(L / 2, r1 - 2 * r2), P(-L / 2, -r1)]
    else:
        pts = [P(-L / 2, r1), P(L / 2, r2), P(L / 2, -r2), P(-L / 2, -r1)]
    c.PL(pts, EQ, z, True)
    for u, r in ((-L / 2, r1), (L / 2, r2)):
        c.PL([P(u - 0.8, -r * 1.35 + (0 if not eksantrik or u < 0 else r1 - r2)), P(u - 0.8, r * 1.35 + (0 if not eksantrik or u < 0 else r1 - r2)),
              P(u + 0.8, r * 1.35 + (0 if not eksantrik or u < 0 else r1 - r2)), P(u + 0.8, -r * 1.35 + (0 if not eksantrik or u < 0 else r1 - r2))], EQ, z, True)
    c.OCCLUDE([P(-L / 2 - 1, -r1 - 2), P(L / 2 + 1, -r1 - 2), P(L / 2 + 1, r1 + 2), P(-L / 2 - 1, r1 + 2)], 98, 'boru')


def debimetre(c, p, dn, z=3):
    """flanşlı debimetre (venturi gövde + ibreli gösterge) - yatay hat"""
    x, y = p
    r = DN_OD[dn] / 2
    L = 40
    for u in (-L / 2, L / 2 - 2):
        c.RECT(x + u, y - r * 1.4, x + u + 2, y + r * 1.4, EQ, z)
    c.PL([(x - L / 2 + 2, y + r), (x - 6, y + r * 0.6), (x + 6, y + r * 0.6), (x + L / 2 - 2, y + r)], EQ, z)
    c.PL([(x - L / 2 + 2, y - r), (x - 6, y - r * 0.6), (x + 6, y - r * 0.6), (x + L / 2 - 2, y - r)], EQ, z)
    c.L((x - 10, y + r * 0.8), (x - 10, y + r + 10), EQ, z); c.L((x + 2, y + r * 0.6), (x + 2, y + r + 10), EQ, z)
    c.L((x - 10, y + r + 10), (x + 2, y + r + 10), EQ, z)
    c.C((x - 4, y + r + 17), 6, EQ, z); c.L((x - 4, y + r + 17), (x - 0.5, y + r + 20.5), EQ, z)
    c.OCCLUDE([(x - L / 2 - 1, y - r - 3), (x + L / 2 + 1, y - r - 3), (x + L / 2 + 1, y + r + 3), (x - L / 2 - 1, y + r + 3)], 98, 'boru')
    return L


def basinc_salteri(c, p, ang=90, z=3):
    """basınç şalteri (presostat): bağlantı somunu + körüklü gövde + ayar kapağı + kablo rakoru; p = bağlantı noktası"""
    a = math.radians(ang - 90); ca, sa = math.cos(a), math.sin(a)

    def P(u, v):
        return (p[0] + u * ca - v * sa, p[1] + u * sa + v * ca)
    c.PL([P(-2, 0), P(2, 0), P(2, 3), P(-2, 3)], EQ, z, True)                     # altıgen somun
    c.PL([P(-1.2, 3), P(-1.2, 5), P(1.2, 5), P(1.2, 5)], EQ, z)
    c.PL([P(-5, 5), P(5, 5), P(5, 15), P(-5, 15)], EQ, z, True)                   # gövde
    for v in (7, 9, 11, 13):
        c.L(P(-5, v), P(5, v), GZ, z)
    c.PL([P(-4, 15), P(-3, 18), P(3, 18), P(4, 15)], EQ, z)                       # kapak
    c.PL([P(5, 9), P(8, 9), P(8, 12), P(5, 12)], EQ, z)                          # kablo rakoru
    return P(0, 18)


def huni(c, p, z=3, lay=EQ):
    """açık drenaj hunisi (görünür akıtma) / yer süzgecine boşaltma"""
    x, y = p
    c.PL([(x - 5, y + 6), (x - 1.5, y), (x + 1.5, y), (x + 5, y + 6)], lay, z)


def yer_suzgeci(c, x, y0, z=3):
    """döşemede yer süzgeci (kesit): ızgara + gövde + sifon"""
    c.L((x - 8, y0), (x + 8, y0), EQ, z)
    c.PL([(x - 7, y0), (x - 7, y0 - 10), (x + 7, y0 - 10), (x + 7, y0)], EQ, z)
    c.PL([(x - 3, y0 - 10), (x - 3, y0 - 18), (x + 3, y0 - 18), (x + 3, y0 - 10)], EQ, z)
    for k in (-4, 0, 4):
        c.L((x + k, y0 - 1), (x + k, y0 - 3), EQ, z)


def samandira_vana(c, p, kol=45, z=3):
    """şamandıralı dolum vanası: p = vana gövdesi (boru ucu). Kol sola/aşağı, top şamandıra"""
    x, y = p
    c.PL([(x - 5, y - 4), (x + 5, y - 4), (x + 5, y + 4), (x - 5, y + 4)], EQ, z, True)
    c.L((x - 5, y), (x - kol, y - kol * 0.35), EQ, z)
    c.C((x - kol - 8, y - kol * 0.35 - 2), 9, EQ, z)


def girdap_onleyici(c, x, y, dn, z=3):
    """aşağı bakan çan ağızlı emiş + girdap önleyici plaka (EN 12845)"""
    r = DN_OD[dn] / 2
    c.PL([(x - r, y + 12), (x - r * 1.5, y)], EQ, z); c.PL([(x + r, y + 12), (x + r * 1.5, y)], EQ, z)
    c.RECT(x - 2 * DN_OD[dn], y - 1.5, x + 2 * DN_OD[dn], y, EQ, z)          # plaka (2D x 2D)
    for xx in (x - 1.6 * DN_OD[dn], x + 1.6 * DN_OD[dn]):
        c.L((xx, y), (xx, y - 8), EQ, z)                                   # plaka ayakları
        c.L((xx - 3, y - 8), (xx + 3, y - 8), EQ, z)


def duvar_gecis(c, x0, x1, y, dn, z=4):
    """su tutucu (puddle) flanşlı duvar geçiş parçası: duvar ortasında flanş"""
    xm = (x0 + x1) / 2; r = DN_OD[dn] / 2
    c.RECT(xm - 1, y - r * 2.2, xm + 1, y + r * 2.2, EQ, z)
    c.OCCLUDE([(x0, y - r - 1), (x1, y - r - 1), (x1, y + r + 1), (x0, y + r + 1)], z + 1, 'boru_haric')


def menhol(c, x0, y_ust, W=70, z=4):
    """depo üst döşemesinde menhol (çerçeve + kilitli kapak) kesit"""
    c.RECT(x0 - 4, y_ust, x0 + W + 4, y_ust + 4, EQ, z)
    c.RECT(x0, y_ust + 4, x0 + W, y_ust + 7, EQ, z)
    c.RECT(x0 + W * 0.45, y_ust + 7, x0 + W * 0.55, y_ust + 10, EQ, z)


def seviye_gostergesi(c, x, y0, y1, z=3):
    """manyetik seviye göstergesi (depo dış yüzünde, üst/alt bağlantılı)"""
    c.RECT(x - 2.5, y0, x + 2.5, y1, EQ, z)
    c.L((x, y0 + 5), (x, y1 - 5), GZ, z)
    for yy in (y0 + 6, y1 - 6):
        c.L((x - 2.5, yy), (x - 12, yy), EQ, z)
    for k in range(int((y1 - y0) / 25)):
        c.L((x + 2.5, y0 + 10 + 25 * k), (x + 5, y0 + 10 + 25 * k), EQ, z)


def dalgic_pompa(c, x, y0, D, H, dn, z=1):
    """dalgıç pis su pompası görünüşü: taban ayağı, salyangoz, motor gövdesi, kaldırma kulpu; basma ağzı sağ yanda"""
    c.RECT(x - D * 0.55, y0, x + D * 0.55, y0 + 3, EQ, z)                    # taban halkası (ayak)
    for s in (-1, 1):
        c.L((x + s * D * 0.45, y0 + 3), (x + s * D * 0.42, y0 + 6), EQ, z)
    ys = y0 + 6
    c.PL([(x - D * 0.42, ys), (x - D * 0.55, ys + H * 0.12), (x - D * 0.55, ys + H * 0.25), (x + D * 0.55, ys + H * 0.25),
          (x + D * 0.55, ys + H * 0.12), (x + D * 0.42, ys)], EQ, z, True)    # salyangoz
    for k in (-0.3, 0, 0.3):
        c.L((x + D * k, ys), (x + D * k, ys - 3), EQ, z)                      # emiş ızgarası
    yp = ys + H * 0.16
    po = DN_OD[dn] / 2
    c.L((x + D * 0.55, yp + po), (x + D * 0.55 + 6, yp + po), EQ, z)
    c.L((x + D * 0.55, yp - po), (x + D * 0.55 + 6, yp - po), EQ, z)
    c.RECT(x + D * 0.55 + 6, yp - po * 1.6, x + D * 0.55 + 7.5, yp + po * 1.6, EQ, z)  # basma flanşı
    c.RECT(x - D * 0.4, ys + H * 0.25, x + D * 0.4, ys + H * 0.82, EQ, z)    # motor
    for i in range(1, 5):
        c.L((x - D * 0.4 + D * 0.8 * i / 5, ys + H * 0.3), (x - D * 0.4 + D * 0.8 * i / 5, ys + H * 0.78), GZ, z)
    c.PL([(x - D * 0.4, ys + H * 0.82), (x - D * 0.3, ys + H * 0.9), (x + D * 0.3, ys + H * 0.9), (x + D * 0.4, ys + H * 0.82)], EQ, z)
    c.ARC((x, ys + H * 0.9), D * 0.22, 0, 180, EQ, z)                         # kulp
    c.RECT(x - 2, ys + H * 0.9, x + 2, ys + H * 0.94, EQ, z)                  # kablo girişi
    return (x + D * 0.55 + 7.5, yp), (x, ys + H * 0.9 + D * 0.22), (x - 1, ys + H * 0.94)


def flator(c, p, z=3):
    """armut tipi seviye flatörü (kabloya asılı)"""
    x, y = p
    c.PL([(x, y), (x - 3.5, y - 4), (x - 4.5, y - 10), (x - 3, y - 15), (x + 3, y - 15), (x + 4.5, y - 10), (x + 3.5, y - 4)], EQ, z, True)


def kirisli_doseme(c, x0, x1, y0, y1, z=4):
    """betonarme kesit (dolgu tarama)"""
    c.RECT(x0, y0, x1, y1, 'ROTAS-BETON', z)
    c.HATCH([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'ROTAS-TARAMA', z, 'AR-CONC', c.olcek * 0.012)
