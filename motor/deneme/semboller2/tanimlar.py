# -*- coding: utf-8 -*-
"""ROTAS- sembol tanımları (saf geometri). Birim cm. Hat üstü semboller: boru yerel +X yönünde akar, orijin boru ekseninde.
Vana boyu L = 20 cm (1/50'de 4 mm), plan armatür / süzgeç / rögar gerçek ölçüde, kolon şeması şablonları
MTY KOLON bloklarına yakın boyda (orijin = döşeme çizgisi üzerinde armatür ekseni)."""
import math
from cekirdek import sembol

L = 20.0
H = 12.0


# ============================================================================= ortak parçalar
def _kuresel(c, x=0.0, y=0.0, l=L, dikey=False):
    """küresel vana: papyon + ortada boş daire + yana kol"""
    h = 0.6 * l
    c.papyon((x, y), l, h, dikey=dikey)
    c.ci((x, y), 0.15 * l)
    if dikey:
        c.ln((x + 0.15 * l, y), (x + 0.42 * l, y))
        c.ln((x + 0.42 * l, y), (x + 0.42 * l, y + 0.3 * l))
    else:
        c.ln((x, y + 0.15 * l), (x, y + 0.42 * l))
        c.ln((x, y + 0.42 * l), (x + 0.3 * l, y + 0.42 * l))


def _cekvalf(c, x=0.0, y=0.0, l=L):
    a = 0.3 * l
    h = 0.3 * l
    c.ln((x - a, y - h), (x - a, y + h))
    c.ln((x - a, y - h), (x + a, y + h))
    c.ln((x + a, y - h), (x + a, y + h))
    c.okcizgi((x - 0.25 * l, y - 0.48 * l), (x + 0.25 * l, y - 0.48 * l), 0.12 * l)


def _pislik(c, x=0.0, y=0.0, l=L):
    a = 0.3 * l
    c.ln((x - a, y - a), (x - a, y + a))
    c.ln((x + a, y - a), (x + a, y + a))
    c.ln((x - a, y), (x + a, y))
    k = 0.35 * l / math.sqrt(2)
    p = (x - 0.12 * l + k, y - k)
    c.ln((x - 0.12 * l, y), p)
    d = 0.09 * l / math.sqrt(2)
    c.ln((p[0] - d, p[1] - d), (p[0] + d, p[1] + d))


def _sayac(c, x=0.0, y=0.0, l=L):
    r = 0.3 * l
    c.ci((x, y), r)
    c.okcizgi((x - 0.18 * l, y), (x + 0.2 * l, y), 0.12 * l)
    c.ln((x - 0.12 * l, y + r), (x - 0.12 * l, y + r + 0.1 * l))
    c.ln((x + 0.12 * l, y + r), (x + 0.12 * l, y + r + 0.1 * l))
    c.ln((x - 0.12 * l, y + r + 0.1 * l), (x + 0.12 * l, y + r + 0.1 * l))


def _pompa(c, x=0.0, y=0.0, r=10.0, aci=0.0):
    c.ci((x, y), r)
    a = math.radians(aci)
    pts = []
    for d in (0, 120, 240):
        t = a + math.radians(d)
        pts.append((x + r * math.cos(t), y + r * math.sin(t)))
    c.dolu(pts)
    c.pl(pts, True)


def _manometre(c, x=0.0, y=0.0):
    c.ln((x, y), (x, y + 6))
    c.ci((x, y + 10.5), 4.5)
    a = math.radians(50)
    c.ln((x, y + 10.5), (x + 3.4 * math.cos(a), y + 10.5 + 3.4 * math.sin(a)))
    for d in (150, 120, 90, 60, 30):
        t = math.radians(d)
        c.ln((x + 3.6 * math.cos(t), y + 10.5 + 3.6 * math.sin(t)), (x + 4.5 * math.cos(t), y + 10.5 + 4.5 * math.sin(t)))


def _purjor(c, x=0.0, y=0.0):
    c.ln((x, y), (x, y + 5))
    c.kapsul(x, y + 5, 5, 9)
    c.ln((x, y + 14), (x, y + 17))
    c.ln((x - 1.5, y + 17), (x + 1.5, y + 17))


def _kelebek(c, x=0.0, y=0.0):
    c.ln((x - 5, y - 8), (x - 5, y + 8))
    c.ln((x + 5, y - 8), (x + 5, y + 8))
    c.ln((x - 3.5, y - 6), (x + 3.5, y + 6))
    c.dolu_daire((x, y), 1.1)


def _ara_musluk(c, x, y, l=6.0):
    """kolon şemasında dikey küçük küresel ara musluk: üst ucu (x, y)"""
    c.papyon((x, y - l / 2), l, 0.6 * l, dikey=True)
    c.ci((x, y - l / 2), 0.15 * l)


# ============================================================================= SIHHİ (plan + hat üstü)
@sembol('ROTAS-SB-KURESEL-VANA', 'KÜRESEL VANA (ARA MUSLUK)', kesme=(-10, 10), tur='ikisi',
        celiski='Küresel = papyon + boş daire + kol; ventil (glob) için dolu nokta kullanılır.')
def s_kuresel(c):
    _kuresel(c)


@sembol('ROTAS-SB-SURGULU-VANA', 'SÜRGÜLÜ VANA', kesme=(-10, 10), tur='ikisi')
def s_surgulu(c):
    c.papyon((0, 0), L)
    c.ln((0, 0), (0, 10))
    c.ln((-5, 10), (5, 10))


@sembol('ROTAS-SB-VENTIL', 'VENTİL (GLOB VANA)', kesme=(-10, 10), tur='ikisi')
def s_ventil(c):
    c.papyon((0, 0), L)
    c.dolu_daire((0, 0), 2.0)
    c.ln((0, 2), (0, 9))
    c.ln((-4, 9), (4, 9))


@sembol('ROTAS-SB-CEKVALF', 'ÇEK VALF (OK AKIŞ YÖNÜ)', kesme=(-6, 6), tur='ikisi',
        celiski='TR lejant biçimi "|/|" + akış oku (ISO dolu üçgen biçimi değil).')
def s_cekvalf(c):
    _cekvalf(c)


@sembol('ROTAS-SB-PISLIK-TUTUCU', 'PİSLİK TUTUCU (Y TİPİ)', kesme=(-6, 6), tur='ikisi')
def s_pislik(c):
    _pislik(c)


@sembol('ROTAS-SB-BASINC-DUSURUCU', 'BASINÇ DÜŞÜRÜCÜ VANA', kesme=(-10, 10), tur='ikisi')
def s_bdv(c):
    c.papyon((0, 0), L)
    c.ln((0, 0), (0, 6))
    c.arc((0, 6), 5, 0, 180)
    c.ln((-5, 6), (5, 6))
    c.kesikli((5, 8.5), (15, 8.5), 1.6, 1.0)
    c.kesikli((15, 8.5), (15, 0.5), 1.6, 1.0)


@sembol('ROTAS-SB-SU-SAYACI', 'SU SAYACI', kesme=(-6, 6), onek='S', tur='ikisi')
def s_sayac(c):
    _sayac(c)


@sembol('ROTAS-SB-YER-SUZGECI', 'YER SÜZGECİ (PLAN, 15x15)', onek='YS')
def s_yer_suzgeci(c):
    c.rect(-7.5, -7.5, 7.5, 7.5)
    r = 5.0
    c.ci((0, 0), r)
    for y in (-3.4, -1.7, 0, 1.7, 3.4):
        x = math.sqrt(r * r - y * y)
        c.ln((-x, y), (x, y))


@sembol('ROTAS-SB-BALKON-SUZGECI', 'BALKON SÜZGECİ (YAN ÇIKIŞLI, YAĞMUR HATTINA)', onek='BS')
def s_balkon_suzgeci(c):
    c.rect(-6, -6, 6, 6)
    c.rect(-4, -4, 4, 4)
    for t in (-2, 0, 2):
        c.ln((t, -4), (t, 4))
        c.ln((-4, t), (4, t))
    c.okcizgi((6, 0), (11, 0), 2.2)


@sembol('ROTAS-SB-TEMIZLEME-KAPAGI', 'TEMİZLEME KAPAĞI (T.K., PLAN)', onek='TK')
def s_tk(c):
    c.ci((0, 0), 5)
    c.ci((0, 0), 3)
    c.ln((-3, 0), (3, 0))
    c.ln((0, -3), (0, 3))
    c.dolu([(0, 0), (3, 0)] + [(3 * math.cos(math.radians(a)), 3 * math.sin(math.radians(a))) for a in range(10, 91, 10)])


@sembol('ROTAS-SB-HAVALIK', 'PİS SU HAVALIĞI (PLAN, ÇATI ÇIKIŞI)', onek='H')
def s_havalik(c):
    c.ci((0, 0), 6)
    c.ci((0, 0), 3)
    for a in (45, 135, 225, 315):
        t = math.radians(a)
        c.ln((6 * math.cos(t), 6 * math.sin(t)), (9 * math.cos(t), 9 * math.sin(t)))


@sembol('ROTAS-SB-KOLON-PIS', 'PİS SU KOLONU (İNİŞ) — PLAN', onek='P')
def s_kolon_pis(c):
    c.ci((0, 0), 5)
    c.dolu_daire((0, 0), 2.2)


@sembol('ROTAS-SB-KOLON-TEMIZ', 'TEMİZ SU KOLONU — PLAN', onek='TS')
def s_kolon_temiz(c):
    c.ci((0, 0), 4)
    c.dolu([(0, 0)] + [(4 * math.cos(math.radians(a)), 4 * math.sin(math.radians(a))) for a in range(90, 271, 15)])


@sembol('ROTAS-SB-KOLON-YAGMUR', 'YAĞMUR SUYU İNİŞİ — PLAN', onek='YB')
def s_kolon_yagmur(c):
    c.ci((0, 0), 5)
    c.ln((-3.5, -3.5), (3.5, 3.5))
    c.ln((-3.5, 3.5), (3.5, -3.5))


@sembol('ROTAS-SB-KOLON-NO', 'KOLON NUMARA BALONU (P1, YB1 ...)', onek='P', no_ic=True)
def s_kolon_no(c):
    c.ci((0, 0), 17)
    c.ci((0, 0), 15)


@sembol('ROTAS-SB-ROGAR', 'RÖGAR (MUAYENE BACASI) 70x70 — PLAN', onek='R', no_ic=True,
        baglanti={'giris': (-45, 0), 'cikis': (45, 0)})
def s_rogar(c):
    c.rect(-45, -45, 45, 45)
    c.rect(-35, -35, 35, 35)
    c.ci((0, 0), 30)


@sembol('ROTAS-SB-ARMATUR-SU', 'ARMATÜR TEMİZ SU BAĞLANTI NOKTASI (ARA MUSLUK + DUVAR ÇIKIŞI)', kesme=(-10, 0),
        onek='', uc=True, baglanti={'boru': (-10, 0), 'armatur': (5, 0)})
def s_armatur_su(c):
    # boru -X'ten gelir; küçük küresel vana + duvar çıkış rozeti
    c.papyon((-5, 0), 10)
    c.ci((-5, 0), 1.5)
    c.ln((-5, 1.5), (-5, 4.5))
    c.ln((0, 0), (3, 0))
    c.ln((3, -3), (3, 3))
    c.ln((5, -2), (5, 2))
    c.ln((3, -3), (5, -2))
    c.ln((3, 3), (5, 2))


@sembol('ROTAS-SB-ARMATUR-PIS', 'ARMATÜR PİS SU BAĞLANTI NOKTASI (GİDER AĞZI)', kesme=(-3, 3), onek='', uc=True,
        baglanti={'boru': (-3, 0)})
def s_armatur_pis(c):
    c.ci((0, 0), 3)
    c.dolu_daire((0, 0), 1.3)


# ============================================================================= DEPO / HİDROFOR
@sembol('ROTAS-DH-SAMANDIRALI-VANA', 'ŞAMANDIRALI VANA (DEPO GİRİŞİ)', kesme=(-10, 10), tur='sema')
def s_samandira(c):
    c.papyon((0, 0), L)
    c.ln((0, 0), (0, -8))
    c.ln((0, -8), (14, -18))
    c.ci((17.5, -20.5), 4)


@sembol('ROTAS-DH-MEMBRANLI-TANK', 'MEMBRANLI GENLEŞME / HİDROFOR TANKI', onek='MT', tur='sema',
        baglanti={'baglanti': (0, 0)})
def s_membranli(c):
    c.ln((0, 0), (0, 8))
    _kuresel(c, 0, 4, l=7, dikey=True)
    c.kapsul(0, 8, 24, 50)
    # membran: aşağı sarkan yay (kiriş = tank genişliği)
    r = (12 ** 2 + 4 ** 2) / (2 * 4)
    c.arc((0, 33 + r - 4), r, 270 - math.degrees(math.asin(12 / r)), 270 + math.degrees(math.asin(12 / r)))
    c.ln((-6, 8), (-6, 3))
    c.ln((6, 8), (6, 3))
    c.ln((-9, 3), (9, 3))


@sembol('ROTAS-DH-HIDROFOR', 'HİDROFOR GRUBU (2 POMPA, KOLLEKTÖRLER, MEMBRANLI TANK)', onek='HF', tur='sema',
        baglanti={'emis': (-70, 0), 'basma': (110, 80)})
def s_hidrofor(c):
    # emiş kollektörü
    c.ln((-70, 0), (50, 0))
    c.ln((50, -3), (50, 3))
    # basma kollektörü
    c.ln((-50, 80), (110, 80))
    c.ln((-50, 77), (-50, 83))
    for x in (-25, 25):
        c.ln((x, 0), (x, 12))
        _kuresel(c, x, 17, l=10, dikey=True)
        c.ln((x, 22), (x, 28))
        _pompa(c, x, 36, 8, aci=90)
        c.ln((x, 44), (x, 50))
        k = c.alt(x, 54, aci=90)
        _cekvalf(k, l=12)
        c.ln((x, 58), (x, 63))
        _kuresel(c, x, 68, l=10, dikey=True)
        c.ln((x, 73), (x, 80))
    # tank
    t = c.alt(80, 80, aci=180)
    t.ln((0, 0), (0, 8))
    t2 = c.alt(80, 80)
    t2.ln((0, 0), (0, -6))
    k = c.alt(80, 74, aci=180)
    _membran_kucuk(k)
    # manometre
    _manometre(c, -5, 80)
    # çerçeve (kesikli)
    for p, q in (((-60, -12), (100, -12)), ((100, -12), (100, 105)), ((100, 105), (-60, 105)), ((-60, 105), (-60, -12))):
        c.kesikli(p, q, 6, 2.5)


def _membran_kucuk(c):
    # baş aşağı çizildiğinde tank aşağı sarkar; yerel +Y = tanktan uzak
    c.kapsul(0, 0, 18, 34)
    r = (9 ** 2 + 3 ** 2) / 6.0
    c.arc((0, 17 + r - 3), r, 270 - math.degrees(math.asin(9 / r)), 270 + math.degrees(math.asin(9 / r)))


@sembol('ROTAS-DH-DALGIC-POMPA', 'DALGIÇ POMPA (PİS SU / DRENAJ ÇUKURU)', onek='DP', tur='ikisi',
        baglanti={'basma': (0, 40)})
def s_dalgic(c):
    c.rect(-8, 0, 8, 20)
    c.ln((-8, 4), (8, 4))
    c.ln((-6, 0), (-6, -3))
    c.ln((6, 0), (6, -3))
    c.ln((-8, -3), (8, -3))
    _pompa(c, 0, 12, 5, aci=90)
    c.ln((0, 20), (0, 25))
    k = c.alt(0, 29, aci=90)
    _cekvalf(k, l=12)
    c.ln((0, 33), (0, 40))


# ============================================================================= ISITMA
@sembol('ROTAS-IS-RADYATOR-PLAN', 'PANEL RADYATÖR — PLAN (100 cm; X ölçeği = boy/100)', onek='R',
        baglanti={'gidis': (0, 6), 'donus': (100, 6)})
def s_rad_plan(c):
    c.rect(0, 2, 100, 10)
    c.ln((0, 6), (100, 6))
    c.ln((50, 2), (50, 10))


@sembol('ROTAS-IS-RADYATOR-SEMA', 'PANEL RADYATÖR — ŞEMA', onek='R', tur='sema',
        baglanti={'gidis': (-60, 25), 'donus': (60, 5)})
def s_rad_sema(c):
    c.rect(-60, 0, 60, 30)
    for x in range(-50, 51, 10):
        c.ln((x, 3), (x, 27))


@sembol('ROTAS-IS-TERMOSTATIK-VANA', 'TERMOSTATİK RADYATÖR VANASI', kesme=(-6, 6), tur='ikisi')
def s_termostatik(c):
    c.papyon((0, 0), 12)
    c.ln((0, 0), (0, 5))
    c.rect(-3.5, 5, 3.5, 13)
    for y in (7.5, 10, 12.5):
        c.ln((-3.5, y - 1.2), (3.5, y - 1.2))


@sembol('ROTAS-IS-RAKORLU-DONUS', 'RAKORLU DÖNÜŞ (ARA) VANASI', kesme=(-5, 5), tur='ikisi')
def s_rakorlu(c):
    c.papyon((0, 0), 10, dolu=True)


@sembol('ROTAS-IS-KOLLEKTOR', 'KOLLEKTÖR (4 ÇIKIŞLI, PURJÖR + BOŞALTMA)', onek='KL', tur='ikisi',
        baglanti={'giris': (0, 0), 'c1': (12, 16), 'c2': (24, 16), 'c3': (36, 16), 'c4': (48, 16)})
def s_kollektor(c):
    c.rect(0, -2.5, 60, 2.5)
    c.ln((61, -3.5), (61, 3.5))
    for x in (12, 24, 36, 48):
        c.ln((x, 2.5), (x, 6))
        c.papyon((x, 8.5), 5, 3.5, dikey=True)
        c.ln((x, 11), (x, 16))
    # purjör
    c.ln((56, 2.5), (56, 4))
    c.kapsul(56, 4, 3, 5)
    # boşaltma
    c.ln((4, -2.5), (4, -6))
    c.papyon((4, -8.5), 5, 3.5, dikey=True)
    c.ln((4, -11), (4, -13))


@sembol('ROTAS-IS-KALORIMETRE', 'KALORİMETRE (ISI PAY ÖLÇER)', kesme=(-7, 7), onek='KM', tur='ikisi')
def s_kalorimetre(c):
    c.rect(-7, -5, 7, 5)
    c.harf('Q', (0, 0), 5.5)
    c.dolu_daire((0, -8), 1.3)
    c.ln((0, -5), (0, -6.7))


@sembol('ROTAS-IS-BALANS-VANASI', 'BALANS (DENGELEME) VANASI', kesme=(-10, 10), tur='ikisi')
def s_balans(c):
    c.papyon((0, 0), L)
    c.ln((0, 0), (0, 9))
    c.ln((-4, 9), (4, 9))
    c.okcizgi((-8, -7), (8, 7), 3.0)


@sembol('ROTAS-IS-POMPA', 'SİRKÜLASYON POMPASI (ÜÇGEN UCU = AKIŞ YÖNÜ)', kesme=(-10, 10), onek='P', tur='ikisi')
def s_pompa(c):
    _pompa(c, 0, 0, 10, 0)


@sembol('ROTAS-IS-KAZAN', 'KAZAN (DUVAR / YER TİPİ)', onek='K', tur='ikisi',
        baglanti={'gidis': (-15, 0), 'donus': (15, 0), 'gaz': (0, 0), 'baca': (0, 100)})
def s_kazan(c):
    c.rect(-30, 0, 30, 90)
    c.rect(-22, 8, 22, 20)
    for x in (-15, -9, -3):
        c.ci((x, 14), 2)
    c.rect(5, 11, 17, 17)
    c.pl([(-6, 45), (6, 45), (0, 65)], True)
    c.rect(-7.5, 90, 7.5, 100)


@sembol('ROTAS-IS-KOMBI', 'KOMBİ — PLAN (YOĞUŞMALI, BACA DIŞ CEPHEYE)', onek='K',
        baglanti={'arka': (0, 0)})
def s_kombi_plan(c):
    c.rect(-22, 0, 22, 32)
    c.pl([(-6, 10), (6, 10), (0, 24)], True)
    c.ci((0, -6), 5)
    c.ln((0, -1), (0, 0))


@sembol('ROTAS-IS-GENLESME-TANKI', 'KAPALI GENLEŞME TANKI (MEMBRANLI)', onek='GT', tur='ikisi',
        baglanti={'baglanti': (0, 0)})
def s_genlesme(c):
    c.ln((0, 0), (0, 10))
    _kuresel(c, 0, 5, l=8, dikey=True)
    r = 12.0
    cy = 22.0
    c.ci((0, cy), r)
    c.ln((-r, cy), (r, cy))
    for y in (cy + 3, cy + 6, cy + 9):
        x = math.sqrt(r * r - (y - cy) ** 2)
        c.ln((-x, y), (x, y))


@sembol('ROTAS-IS-DENGE-KABI', 'DENGE KABI (HİDROLİK AYIRICI)', onek='DK', tur='sema',
        baglanti={'p_gidis': (-18, 62), 'p_donus': (-18, 18), 's_gidis': (18, 62), 's_donus': (18, 18)})
def s_denge(c):
    c.kapsul(0, 0, 20, 80)
    for y in (62, 18):
        c.ln((-10, y), (-18, y))
        c.ln((10, y), (18, y))
    _purjor(c, 0, 80)
    c.ln((0, 0), (0, -4))
    c.papyon((0, -7), 6, 4, dikey=True)
    c.ln((0, -10), (0, -13))


@sembol('ROTAS-IS-EMNIYET-VENTILI', 'EMNİYET VENTİLİ (YAYLI)', onek='EV', tur='ikisi',
        baglanti={'giris': (0, 0), 'cikis': (16, 0)})
def s_emniyet(c):
    c.ln((0, 0), (0, 3))
    c.pl([(-4, 3), (4, 3), (0, 10)], True)
    c.pl([(7, 6), (7, 14), (0, 10)], True)
    c.zigzag((0, 10), (0, 23), 3, 2.5)
    c.ln((7, 10), (16, 10))
    c.okcizgi((16, 10), (16, 1), 2.4)


@sembol('ROTAS-IS-MANOMETRE', 'MANOMETRE', onek='M', tur='ikisi', baglanti={'boru': (0, 0)})
def s_manometre(c):
    _manometre(c)


@sembol('ROTAS-IS-TERMOMETRE', 'TERMOMETRE', onek='T', tur='ikisi', baglanti={'boru': (0, 0)})
def s_termometre(c):
    c.ln((0, 0), (0, 2.5))
    c.dolu_daire((0, 4.5), 2.0)
    c.ci((0, 4.5), 2.0)
    c.ln((-1.1, 6.2), (-1.1, 16))
    c.ln((1.1, 6.2), (1.1, 16))
    c.arc((0, 16), 1.1, 0, 180)
    for y in (9, 11.5, 14):
        c.ln((1.1, y), (3, y))


@sembol('ROTAS-IS-PURJOR', 'OTOMATİK PURJÖR (HAVA ATICI)', onek='HP', tur='ikisi', baglanti={'boru': (0, 0)})
def s_purjor(c):
    _purjor(c)


# ============================================================================= YANGIN
@sembol('ROTAS-YG-SPRINKLER-DIK', 'SPRİNKLER — DİK (UPRIGHT)', onek='SP',
        celiski='Örnek lejantlar çelişiyor: dik = daire + artı (deflektör), sarkık = çift daire.')
def s_spr_dik(c):
    c.ci((0, 0), 8)
    c.ln((-5, 0), (5, 0))
    c.ln((0, -5), (0, 5))


@sembol('ROTAS-YG-SPRINKLER-SARKIK', 'SPRİNKLER — SARKIK (PENDENT)', onek='SP',
        celiski='Örnek lejantlar çelişiyor: dik = daire + artı (deflektör), sarkık = çift daire.')
def s_spr_sarkik(c):
    c.ci((0, 0), 8)
    c.ci((0, 0), 4)


@sembol('ROTAS-YG-SPRINKLER-YAN', 'SPRİNKLER — YAN DUVAR (SIDEWALL)', onek='SP')
def s_spr_yan(c):
    c.arc((0, 0), 8, 0, 180)
    c.ln((-8, 0), (8, 0))
    c.okcizgi((0, 0), (0, 6), 2.4)


@sembol('ROTAS-YG-YANGIN-DOLABI', 'YANGIN DOLABI (HORTUM Ø1" 30 m) — PLAN', onek='YD', no_ic=False,
        baglanti={'boru': (-35, 12.5)})
def s_dolap(c):
    c.rect(-35, 0, 35, 25)
    c.ln((-35, 0), (35, 25))
    c.ln((-35, 25), (35, 0))
    c.ci((0, 12.5), 5)
    c.dolu_daire((0, 12.5), 2)


@sembol('ROTAS-YG-ITFAIYE-AGZI', 'İTFAİYE BAĞLANTI AĞZI (İKİZ, STORZ)', onek='İB',
        baglanti={'boru': (0, 0)})
def s_itfaiye_agzi(c):
    c.ln((0, -5), (0, 5))
    for s in (1, -1):
        c.ln((0, 2.5 * s), (-10, 9 * s))
        c.ci((-12.5, 10.6 * s), 3)
        c.ln((-15.4, 9.8 * s - 0.4 * s), (-14.0, 13.2 * s))


@sembol('ROTAS-YG-ITFAIYE-KOLLEKTOR', 'İTFAİYE BAĞLANTI KOLLEKTÖRÜ (2 AĞIZ, ÇEK VALF TESİSATA DOĞRU)', onek='İB',
        tur='ikisi', baglanti={'cikis': (0, 0)})
def s_itfaiye_kol(c):
    # kollektör gövdesi
    c.rect(-24, -16, -18, 16)
    c.ln((-18, 0), (0, 0))
    _kuresel(c, -9, 0, l=10)
    for y in (10, -10):
        c.ln((-24, y), (-30, y))
        _cekvalf(c, -36, y, l=12)
        c.ln((-42, y), (-48, y))
        c.ln((-58, y), (-66, y))
        _kuresel(c, -53, y, l=10)
        c.ln((-66, y - 4), (-66, y + 4))
        c.ci((-70, y), 4)
    # boşaltma
    c.ln((-21, -16), (-21, -21))
    c.papyon((-21, -24), 6, 4, dikey=True)
    c.ln((-21, -27), (-21, -30))


@sembol('ROTAS-YG-ALARM-VANASI', 'ISLAK ALARM VANASI (KAT/ZON)', kesme=(-10, 18), onek='AV', tur='ikisi')
def s_alarm(c):
    c.papyon((0, 0), L)
    c.pl([(10, 0), (18, 6), (18, -6)], True)
    c.ln((0, 0), (0, 9))
    c.ci((0, 11), 2)


@sembol('ROTAS-YG-AKIS-ANAHTARI', 'AKIŞ ANAHTARI (FLOW SWITCH)', kesme=(-5, 5), onek='AA', tur='ikisi')
def s_akis(c):
    c.rect(-5, -5, 5, 5)
    c.pl([(-5, 5), (-5, -5), (0, 0)], True)
    c.pl([(5, 5), (5, -5), (0, 0)], True)
    c.ci((0, 0), 1.4)
    c.ln((0, 5), (0, 8))
    c.pl([(0, 8), (3, 9.5), (0, 11)])


@sembol('ROTAS-YG-IZLENEBILIR-KELEBEK', 'İZLENEBİLİR KELEBEK VANA (S = KONUM ANAHTARI)', kesme=(-5, 5), tur='ikisi')
def s_izl_kelebek(c):
    _kelebek(c)
    c.ln((0, 8), (0, 10))
    c.rect(-4, 10, 4, 18)
    c.harf('S', (0, 14), 5)


@sembol('ROTAS-YG-KELEBEK-VANA', 'KELEBEK VANA', kesme=(-5, 5), tur='ikisi')
def s_kelebek(c):
    _kelebek(c)
    c.ln((0, 8), (0, 11))
    c.ln((0, 11), (6, 11))


@sembol('ROTAS-YG-TEST-DRENAJ', 'TEST VE DRENAJ VANASI (GÖZETLEME CAMLI)', onek='TD', tur='ikisi',
        baglanti={'boru': (0, 0), 'drenaj': (30, -10)})
def s_test_drenaj(c):
    c.ln((0, 0), (5, 0))
    _kuresel(c, 10, 0, l=10)
    c.ln((15, 0), (19, 0))
    c.ci((22, 0), 3)
    c.ci((22, 0), 1.5)
    c.ln((25, 0), (30, 0))
    c.okcizgi((30, 0), (30, -10), 2.4)


# ============================================================================= HAVALANDIRMA
@sembol('ROTAS-HV-ASPIRATOR', 'WC ASPİRATÖRÜ (TAVAN / KANAL TİPİ) — PLAN', onek='A')
def s_aspirator(c):
    c.rect(-12, -12, 12, 12)
    c.ci((0, 0), 9)
    for a in (45, 135, 225, 315):
        t = math.radians(a)
        p = (8 * math.cos(t), 8 * math.sin(t))
        q1 = (5 * math.cos(t + 0.5), 5 * math.sin(t + 0.5))
        c.pl([(0, 0), q1, p, (0, 0)])


@sembol('ROTAS-HV-MENFEZ-UFLEME', 'ÜFLEME MENFEZİ / DİFÜZÖR (4 YÖNLÜ, 30x30) — PLAN', onek='M')
def s_menfez_ufleme(c):
    c.rect(-15, -15, 15, 15)
    c.ln((-15, -15), (15, 15))
    c.ln((-15, 15), (15, -15))
    for a in (0, 90, 180, 270):
        t = math.radians(a)
        c.okcizgi((16 * math.cos(t), 16 * math.sin(t)), (24 * math.cos(t), 24 * math.sin(t)), 3)


@sembol('ROTAS-HV-MENFEZ-EMIS', 'EMİŞ / EGZOZ MENFEZİ (30x30) — PLAN', onek='M')
def s_menfez_emis(c):
    c.rect(-15, -15, 15, 15)
    c.ln((-15, -15), (15, 15))
    for a in (0, 90, 180, 270):
        t = math.radians(a)
        c.okcizgi((24 * math.cos(t), 24 * math.sin(t)), (16 * math.cos(t), 16 * math.sin(t)), 3)


@sembol('ROTAS-HV-PANJUR', 'PANJUR (TAZE HAVA / EGZOZ, DUVARDA) — PLAN', onek='PJ')
def s_panjur(c):
    c.rect(-20, -4, 20, 4)
    for x in range(-16, 17, 8):
        c.ln((x - 3, -4), (x + 3, 4))


@sembol('ROTAS-HV-DAMPER', 'AYAR DAMPERİ (KANAL GENİŞLİĞİ 30; Y ÖLÇEĞİ = G/30)', onek='D', tur='ikisi')
def s_damper(c):
    for s in (1, -1):
        c.ln((-3, 15 * s), (-3, 18 * s))
        c.ln((3, 15 * s), (3, 18 * s))
    c.ln((-6, -12), (6, 12))
    c.ci((0, 0), 1.5)
    c.ln((6, 12), (6, 22))
    c.ci((6, 23.5), 1.5)


@sembol('ROTAS-HV-YANGIN-DAMPERI', 'YANGIN DAMPERİ (KANAL GENİŞLİĞİ 30)', onek='FD', tur='ikisi')
def s_ydamper(c):
    c.rect(-4, -15, 4, 15)
    c.ln((-4, -15), (4, 15))
    c.ln((-4, 15), (4, -15))
    for s in (1, -1):
        c.ln((-4, 15 * s), (-4, 18 * s))
        c.ln((4, 15 * s), (4, 18 * s))


@sembol('ROTAS-HV-CATI-FANI', 'ÇATI TİPİ FAN — PLAN', onek='F')
def s_cati_fani(c):
    c.ci((0, 0), 20)
    c.ci((0, 0), 6)
    for a in (0, 90, 180, 270):
        t = math.radians(a)
        c.arc((13 * math.cos(t + 0.6), 13 * math.sin(t + 0.6)), 9, math.degrees(t) + 120, math.degrees(t) + 215)


@sembol('ROTAS-HV-CATI-FANI-KESIT', 'ÇATI TİPİ FAN — KESİT / ŞEMA SONU (MANTAR)', onek='F', tur='sema',
        baglanti={'kanal': (0, 0)})
def s_cati_fani_kesit(c):
    c.rect(-9, 0, 9, 8)
    c.rect(-14, 8, 14, 14)
    c.arc((0, 14), 18, 0, 180)
    c.ln((-18, 14), (-14, 14))
    c.ln((14, 14), (18, 14))
    _pompa_fan(c, 0, 22)


def _pompa_fan(c, x, y):
    c.ci((x, y), 5)
    c.ln((x - 4, y - 2), (x + 4, y + 2))
    c.ln((x - 4, y + 2), (x + 4, y - 2))


@sembol('ROTAS-HV-SAFT', 'MEKANİK HAVALANDIRMA ŞAFTI 40x40 — PLAN', onek='ŞF')
def s_saft(c):
    c.rect(-20, -20, 20, 20)
    c.ln((-20, -20), (20, 20))
    c.ln((-20, 20), (20, -20))
    c.ci((0, 0), 7.5)


# ============================================================================= KOLON ŞEMASI ŞABLONLARI
# Orijin: armatür ekseni, döşeme (kat bandı alt çizgisi) üzerinde. Temiz su bağlantısı üstten iner
# (ara musluk üst ucu = bağlantı noktası), pis su bağlantı noktası 'pis'.

@sembol('ROTAS-KS-LAVABO', 'LAVABO', onek='', tur='sema',
        baglanti={'soguk': (8, 62), 'sicak': (-8, 62), 'pis': (0, 40)})
def k_lavabo(c):
    c.rect(-30, 80, 30, 85)
    c.pl([(-27, 80), (-20, 68), (20, 68), (27, 80)])
    c.ln((0, 68), (0, 54))
    c.rect(-3, 40, 3, 54)
    # batarya
    c.rect(-3, 85, 3, 92)
    c.pl([(0, 92), (0, 96), (8, 95), (8, 93)])
    c.ln((-3, 94), (-7, 98))
    for s in (1, -1):
        _ara_musluk(c, 8 * s, 62)
        c.ln((8 * s, 56), (2.5 * s, 85))


@sembol('ROTAS-KS-KLOZET', 'KLOZET (ALAFRANGA, ASMA REZERVUAR)', onek='', tur='sema',
        baglanti={'soguk': (24, 100), 'pis': (0, 0)})
def k_klozet(c):
    c.rect(-19, 40, 19, 43)
    c.pl([(-18, 40), (-16, 24), (-10, 10), (10, 10), (16, 24), (18, 40)])
    c.pl([(-10, 10), (-12, 0), (12, 0), (10, 10)])
    c.rect(-18, 72, 18, 98)
    c.ci((0, 90), 2.5)
    c.ln((0, 72), (0, 43))
    _ara_musluk(c, 24, 100)
    c.pl([(24, 94), (24, 85), (18, 85)])


@sembol('ROTAS-KS-HELA', 'HELA TAŞI (ALATURKA, YÜKSEK REZERVUAR)', onek='', tur='sema',
        baglanti={'soguk': (22, 200), 'pis': (12, -20)})
def k_hela(c):
    c.ln((-30, 0), (30, 0))
    c.pl([(-30, 0), (-24, -12), (24, -12), (30, 0)])
    c.rect(-22, 0, -10, 1.8)
    c.rect(10, 0, 22, 1.8)
    # sifon (U)
    c.ln((0, -12), (0, -24))
    c.arc((6, -24), 6, 180, 360)
    c.ln((12, -24), (12, -20))
    # rezervuar + iniş borusu
    c.rect(-16, 170, 16, 192)
    c.ln((-12, 170), (-12, 0))
    c.pl([(16, 188), (20, 186)])
    _ara_musluk(c, 22, 200)
    c.pl([(22, 194), (22, 188), (16, 188)])


@sembol('ROTAS-KS-DUS', 'DUŞ TEKNESİ + DUŞ BATARYASI', onek='', tur='sema',
        baglanti={'soguk': (8, 128), 'sicak': (-8, 128), 'pis': (0, 0)})
def k_dus(c):
    c.rect(-40, 0, 40, 8)
    c.ln((-37, 5), (37, 5))
    c.rect(-8, 108, 8, 114)
    c.ln((0, 108), (0, 104))
    c.ln((12, 111), (16, 111))
    c.ln((16, 100), (16, 190))
    c.pl([(16, 190), (26, 190), (30, 186), (22, 182), (26, 190)])
    for s in (1, -1):
        _ara_musluk(c, 8 * s, 128)
        c.ln((8 * s, 122), (8 * s, 114))


@sembol('ROTAS-KS-KUVET', 'KÜVET + BATARYA', onek='', tur='sema',
        baglanti={'soguk': (8, 78), 'sicak': (-8, 78), 'pis': (-40, 0)})
def k_kuvet(c):
    c.pl([(-55, 45), (55, 45), (52, 6), (47, 0), (-47, 0), (-52, 6)], True)
    c.ln((-55, 41), (55, 41))
    c.rect(-8, 58, 8, 64)
    c.pl([(0, 58), (0, 51), (5, 51)])
    c.pl([(-40, 6), (-40, 0)])
    for s in (1, -1):
        _ara_musluk(c, 8 * s, 78)
        c.ln((8 * s, 72), (8 * s, 64))


@sembol('ROTAS-KS-EVIYE', 'EVİYE (TEZGAH ALTI DOLAPLI)', onek='', tur='sema',
        baglanti={'soguk': (8, 62), 'sicak': (-8, 62), 'pis': (0, 45)})
def k_eviye(c):
    c.rect(-40, 85, 70, 90)
    c.pl([(-18, 85), (-15, 70), (15, 70), (18, 85)])
    c.ln((-40, 0), (-40, 85))
    c.ln((70, 0), (70, 85))
    c.ln((-40, 8), (70, 8))
    c.ln((28, 8), (28, 85))
    c.ci((24, 46), 1.2)
    c.ci((32, 46), 1.2)
    c.ln((0, 70), (0, 58))
    c.rect(-3, 45, 3, 58)
    c.rect(-2.5, 90, 2.5, 96)
    c.pl([(0, 96), (0, 104), (10, 102), (10, 99)])
    for s in (1, -1):
        _ara_musluk(c, 8 * s, 62)
        c.ln((8 * s, 56), (2 * s, 90))


@sembol('ROTAS-KS-CAMASIR-MAKINESI', 'ÇAMAŞIR MAKİNESİ', onek='', tur='sema',
        baglanti={'soguk': (20, 102), 'pis': (0, 0)})
def k_camasir(c):
    c.rect(-30, 0, 30, 85)
    c.ln((-30, 70), (30, 70))
    c.rect(-26, 74, -10, 81)
    c.ci((18, 77.5), 3)
    c.ci((0, 36), 19)
    c.ci((0, 36), 14)
    c.rect(-30, 0, 30, 4)
    _ara_musluk(c, 20, 102)
    c.ln((20, 96), (20, 85))


@sembol('ROTAS-KS-BULASIK-MAKINESI', 'BULAŞIK MAKİNESİ', onek='', tur='sema',
        baglanti={'soguk': (20, 102), 'pis': (0, 0)})
def k_bulasik(c):
    c.rect(-30, 0, 30, 85)
    c.ln((-30, 75), (30, 75))
    c.ln((-15, 70), (15, 70))
    for y in (24, 48):
        c.kesikli((-26, y), (26, y), 3, 2)
        for x in range(-22, 23, 8):
            c.ln((x, y), (x, y + 6))
    c.rect(-30, 0, 30, 4)
    c.rect(-24, 78, -8, 82)
    _ara_musluk(c, 20, 102)
    c.ln((20, 96), (20, 85))


@sembol('ROTAS-KS-YER-SUZGECI', 'YER SÜZGECİ (SİFONLU)', onek='', tur='sema',
        baglanti={'pis': (0, -18)})
def k_yer_suzgeci(c):
    c.pl([(-10, 0), (10, 0), (6, -8), (-6, -8)], True)
    for x in (-5, 0, 5):
        c.ln((x, 0), (x * 0.7, -2.5))
    c.rect(-5, -8, 5, -14)
    c.ln((-2.5, -14), (-2.5, -10))
    c.ln((0, -14), (0, -18))


@sembol('ROTAS-KS-KOMBI', 'KOMBİ (DUVAR TİPİ, YOĞUŞMALI)', onek='K', tur='sema',
        baglanti={'gidis': (-14, 126), 'sicak': (-7, 126), 'gaz': (0, 126), 'soguk': (7, 126), 'donus': (14, 126)})
def k_kombi(c):
    c.rect(-20, 140, 20, 215)
    c.rect(-14, 146, 14, 156)
    for x in (-9, -3, 3):
        c.ci((x, 151), 2)
    c.rect(6, 148.5, 12, 153.5)
    c.pl([(-6, 172), (6, 172), (0, 192)], True)
    c.rect(-5, 215, 5, 224)
    for x in (-14, -7, 0, 7, 14):
        c.ln((x, 140), (x, 138))
        c.papyon((x, 135), 6, 4, dikey=True)
        c.ln((x, 132), (x, 126))


@sembol('ROTAS-KS-TERMOSIFON', 'TERMOSİFON (ELEKTRİKLİ, EMNİYET VENTİLLİ)', onek='TS', tur='sema',
        baglanti={'soguk': (8, 126), 'sicak': (-8, 126)})
def k_termosifon(c):
    c.kapsul(0, 140, 36, 85)
    c.zigzag((0, 150), (0, 175), 3, 6)
    c.rect(-6, 196, 6, 204)
    for x in (-8, 8):
        c.ln((x, 140 + 18 - math.sqrt(18 ** 2 - x ** 2)), (x, 138))
        c.papyon((x, 135), 6, 4, dikey=True)
        c.ln((x, 132), (x, 126))
    # emniyet ventili soğuk girişte
    c.ln((8, 130), (14, 130))
    c.pl([(14, 127), (14, 133), (18, 130)], True)
    c.zigzag((18, 130), (24, 130), 2, 1.5)


@sembol('ROTAS-KS-SAYAC-GRUBU', 'SAYAÇ GRUBU (VANA - SAYAÇ - ÇEK VALF - VANA, KESİNTİSİZ)', kesme=(0, 92), onek='S',
        tur='ikisi', baglanti={'giris': (0, 0), 'cikis': (92, 0)})
def k_sayac_grubu(c):
    c.ln((0, 0), (2, 0))
    _kuresel(c, 12, 0)
    c.ln((22, 0), (29, 0))
    _sayac(c, 35, 0)
    c.ln((41, 0), (52, 0))
    _cekvalf(c, 58, 0)
    c.ln((64, 0), (70, 0))
    _kuresel(c, 80, 0)
    c.ln((90, 0), (92, 0))


@sembol('ROTAS-KS-PVC-CATAL', 'PVC ÇATAL (45°, SAĞ; SOL İÇİN ayna=True)', onek='', tur='sema',
        baglanti={'ust': (0, 15), 'alt': (0, -15), 'dal': (13.4, 13.4)})
def k_catal(c):
    r = 3.0
    k = math.sqrt(0.5)
    ya, yu = r * (1 - 2 * k), r * (1 + 2 * k)     # dal duvarlarının ana boru sağ duvarını kestiği yerler
    c.ln((-r, -15), (-r, 15))
    c.ln((r, -15), (r, ya))
    c.ln((r, yu), (r, 15))
    c.ln((r, ya), (13.4 + r * k, 13.4 - r * k))
    c.ln((r, yu), (13.4 - r * k, 13.4 + r * k))
    for y in (-15, 15):
        c.ln((-r - 1.2, y), (r + 1.2, y))
    c.ln((13.4 + (r + 1.2) * k, 13.4 - (r + 1.2) * k), (13.4 - (r + 1.2) * k, 13.4 + (r + 1.2) * k))


@sembol('ROTAS-KS-TEMIZLEME-KAPAGI', 'TEMİZLEME KAPAĞI (T.K., KOLON)', onek='TK', tur='sema',
        baglanti={'ust': (0, 12), 'alt': (0, -12)})
def k_tk(c):
    r = 3.0
    c.ln((-r, -12), (-r, 12))
    c.ln((r, -12), (r, -r))
    c.ln((r, r), (r, 12))
    c.ln((r, -r), (9, -r))
    c.ln((r, r), (9, r))
    c.rect(9, -r - 1.5, 11.5, r + 1.5)
    c.ln((10.25, -2), (10.25, 2))


@sembol('ROTAS-KS-ROGAR', 'RÖGAR (ŞEMA)', onek='R', no_ic=True, tur='sema',
        baglanti={'giris': (-25, -25), 'cikis': (25, -30)})
def k_rogar(c):
    c.rect(-25, -40, 25, 0)
    c.rect(-21, -36, 21, -4)
    c.rect(-15, 0, 15, 5)


@sembol('ROTAS-KS-HAVALIK', 'PİS SU HAVALIK ŞAPKASI (KOLON SONU)', onek='', tur='sema',
        baglanti={'kolon': (0, 0)})
def k_havalik(c):
    c.ln((-2.5, 0), (-2.5, 6))
    c.ln((2.5, 0), (2.5, 6))
    c.arc((0, 6), 9, 0, 180)
    c.ln((-9, 6), (9, 6))


@sembol('ROTAS-KS-SU-DEPOSU', 'SU DEPOSU (ŞAMANDIRA, HAVALIK, TAŞMA, BOŞALTMA, SEVİYE)', onek='D', tur='sema',
        baglanti={'giris': (-20, 140), 'cikis': (40, -30), 'huni': (230, -45)})
def k_depo(c):
    c.rect(0, 0, 200, 120)
    # su seviyesi
    c.kesikli((5, 95), (195, 95), 8, 4)
    c.pl([(100, 95), (95, 103), (105, 103)], True)
    # giriş + şamandıralı vana
    c.pl([(-20, 140), (20, 140), (20, 120)])
    c.ln((20, 120), (20, 110))
    c.papyon((20, 104), 12, 7, dikey=True)
    c.ln((20, 98), (34, 88))
    c.ci((37.5, 85.5), 4)
    # havalık (ters J + tel)
    c.ln((100, 120), (100, 140))
    c.arc((107, 140), 7, 0, 180)
    c.ln((114, 140), (114, 132))
    c.ln((111, 132), (117, 132))
    # taşma
    c.pl([(200, 105), (230, 105), (230, -36)])
    # boşaltma
    c.ln((180, 0), (180, -8))
    c.papyon((180, -14), 12, 7, dikey=True)
    c.pl([(180, -20), (180, -30), (224, -30)])
    # huni (taşma + boşaltma açık uç bırakılmaz -> sifonlu huni)
    c.pl([(222, -36), (238, -36), (232, -45), (228, -45)], True)
    # çıkış
    c.ln((40, 0), (40, -12))
    _kuresel(c, 40, -19, l=12, dikey=True)
    c.ln((40, -25), (40, -30))
    # seviye göstergesi (cam boru)
    c.pl([(0, 12), (-12, 12)])
    c.pl([(0, 108), (-12, 108)])
    c.rect(-15, 18, -9, 102)
    c.ln((-12, 12), (-12, 18))
    c.ln((-12, 102), (-12, 108))
    c.dolu([(-15, 18), (-9, 18), (-9, 95), (-15, 95)])
