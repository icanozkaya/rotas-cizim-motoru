"""Kazan dairesi + su deposu / hidrofor dairesi: PLAN (1/50) ve ŞEMA (ölçeksiz) - kullanıcının EKİPMAN LİSTESİ'ne göre.
6 x 115 kW duvar tipi yoğuşmalı kaskad kazan (70/50 °C) -> kombi kollektörü -> hava ayırıcı -> sekonder pompalar ->
700 kW plakalı eşanjör -> 7 x 1000 L emaye akümülasyon (kullanım sıcak suyu) tankı; tortu ayırıcı dönüşte.
Soğuk su: 30 ton betonarme depo -> hidrofor 29 m³/h 74 mSS (+100 L) -> yumuşatma -> aktif karbon -> soğuk su kollektörü.
"""
import math, pickle, sys
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import cad
from cad import L, PL, C, T, RECT, RRECT, ARC, ARROW, push, pop, MOVE, VANA, CEKVALF, PISLIK_TUTUCU, POMPA, MEMBRANLI_TANK, \
    SAMANDIRALI_VANA
import mtyblk
import gp
from gp import CS, CH, HGL, HDL, YZ, CD, VN, pipe, node
import gsheet as GS

SIR = 'MTY-SIRKULASYON-BORU'
BACA = 'MTY-BACA'
GAZ = 'MTY-DOGALGAZ'
DRN = 'MTY-PISSU-BORU-TAVANDAN'
NO = 'MTY-EKIPMAN-NO'
gp.EXTRA_LAYERS.update({SIR: (31, 'DASHED'), BACA: (8, 'CONTINUOUS'), GAZ: (2, 'DASHDOT'), NO: (1, 'CONTINUOUS'),
                        'MTY-ISITMA-GIDIS-BORU': (10, 'CONTINUOUS'), 'MTY-ISITMA-DONUS-BORU': (30, 'ISITMA DONUS HATTI')})
gp.WIDTH.update({SIR: 2.0, BACA: 1.5})

EKIPMAN = [
    (1, 'SU DEPOSU', 1, 'BETONARME 30 TON'),
    (2, 'HİDROFOR', 1, '29,00 m³/h, 74 mSS, FREKANS KONTROLLÜ, Elk. Gücü: 0,4 kW'),
    (3, 'GENLEŞME T.', 1, '100 LT. (HİDROFOR)'),
    (4, 'SOĞUK SU KOLLEKTÖRÜ', 1, 'GALVANİZ 3"'),
    (5, 'SU YUMUŞATMA CİHAZI', 1, 'GALVANİZ 3"'),
    (6, 'AKTİF KARBON FİLTRE', 1, 'GALVANİZ 3"'),
    (7, 'RE SİRKÜLASYON POMPASI', 2, '9,0 m³/h, 3,0 mSS, FREKANS KONTROLLÜ, Elk. Gücü: 0,3 kW'),
    (8, 'AKÜMÜLASYON TANKI', 7, '1000 LT. EMAYE KAPLAMALI'),
    (9, 'SEKONDER SİRKÜLASYON POMPASI', 2, '30,0 m³/h, 2,0 mSS, FREKANS KONTROLLÜ, Elk. Gücü: 0,3 kW'),
    (10, 'DÖNÜŞ KOLLEKTÖRÜ', 1, 'GALVANİZ 3"'),
    (11, 'TORTU AYIRICI', 1, '50 LT.'),
    (12, 'PLAKALI EŞANJÖR', 1, '700 kW'),
    (13, 'HAVA AYIRICI', 1, '80 LT.'),
    (14, 'DUVAR TİPİ KOMBİ', 6, '95.000 kcal/h (115 kW) GAZ YAKITLI DUVAR TİPİ YOĞUŞMALI KASKAD KAZAN 70/50 °C'),
    (15, 'GENLEŞME TANKI', 1, '200 LT. (KAZAN / PRİMER DEVRE)'),
    (16, 'GENLEŞME TANKI', 1, '50 LT. (KULLANIM SICAK SUYU)'),
    (17, 'KOMBİ KOLLEKTÖRÜ', 2, 'SİYAH BORU 3" (GİDİŞ + DÖNÜŞ)'),
]


def NOB(p, n, r=11.0):
    """ekipman numarası balonu (listeyle aynı no)"""
    C(p, r, NO); T(p, str(n), r * 1.05, NO, 'MC')


# ------------------------------------------------------------------ semboller (şema)
def TANK_DIK(cx, y0, w, h, lay=CD):
    """dik silindirik tank (akümülasyon / filtre / ayırıcı)"""
    r = w / 2
    PL([(cx - r, y0 + r * 0.5), (cx - r, y0 + h - r * 0.5)], lay)
    PL([(cx + r, y0 + r * 0.5), (cx + r, y0 + h - r * 0.5)], lay)
    ARC((cx, y0 + h - r * 0.5), r, 0, 180, lay)
    ARC((cx, y0 + r * 0.5), r, 180, 360, lay)


def ESANJOR(x0, y0, w, h, lay=CD):
    RECT(x0, y0, x0 + w, y0 + h, lay)
    RECT(x0 + 6, y0 + 6, x0 + w - 6, y0 + h - 6, lay)
    n = 9
    for i in range(1, n):
        x = x0 + 6 + i * (w - 12) / n
        L((x, y0 + 10), (x, y0 + h - 10), lay)
    L((x0 + 8, y0 + 8), (x0 + w - 8, y0 + h - 8), lay)


def KAZAN_SEMA(x0, y0, w, h, i):
    RRECT(x0, y0, x0 + w, y0 + h, 6, CD)
    RECT(x0 + 12, y0 + h - 45, x0 + w - 12, y0 + h - 22, CD)
    C((x0 + 25, y0 + 25), 6, CD); RECT(x0 + 38, y0 + 20, x0 + 58, y0 + 30, CD)
    T((x0 + w / 2, y0 + h - 34), 'K-%d' % i, 9, CD, 'MC')
    T((x0 + w / 2, y0 + 60), '115 kW', 8, CD, 'MC')
    T((x0 + w / 2, y0 + 47), '70/50 °C', 7, CD, 'MC')


def HAVA_AYIRICI(cx, cy, lay=CD):
    TANK_DIK(cx, cy - 40, 34, 85, lay)
    L((cx, cy + 45), (cx, cy + 58), lay); RECT(cx - 6, cy + 58, cx + 6, cy + 68, lay)
    T((cx + 10, cy + 63), 'OTOMATİK PURJÖR', 5.5, lay, 'L')


def TORTU_AYIRICI(cx, cy, lay=CD):
    TANK_DIK(cx, cy - 55, 34, 85, lay)
    L((cx, cy - 55), (cx, cy - 72), lay)
    mtyblk.insert('MTY-BOSALTMA VANA', (cx, cy - 72), 0, 1.0)
    T((cx + 10, cy - 80), 'BLÖF', 5.5, lay, 'L')


def POMPA_HAT(xa, xb, y, lay, ang):
    """xa -> xb boyunca: vana - pompa - çek valf - vana (pompa yönü ang)"""
    d = 1 if xb > xa else -1
    pipe([(xa, y), (xb, y)], lay, 'P%d' % int(y))
    VANA((xa + d * 18, y), 0.8, 0)
    POMPA((xa + d * 55, y), 12, ang)
    CEKVALF((xa + d * 90, y), 0.8, 0 if d > 0 else 180)
    VANA((xb - d * 18, y), 0.8, 0)


def SEMA():
    # ======================= üst sıra: kazanlar + primer devre + eşanjör
    YG, YD = 960.0, 900.0                 # kazan gidiş / dönüş kollektörleri
    xk = [1500.0 + 260.0 * i for i in range(6)]
    for i, x in enumerate(xk):
        KAZAN_SEMA(x, 1150.0, 100.0, 140.0, i + 1)
        g, d = (x + 30.0, 1150.0), (x + 70.0, 1150.0)
        pipe([g, (g[0], YG)], HGL, 'K'); pipe([(d[0], YD), d], HDL, 'K')
        VANA((g[0], 1110.0), 0.8, 90); VANA((d[0], 1110.0), 0.8, 90); CEKVALF((d[0], 1070.0), 0.8, 90)
        mtyblk.insert('MTY-EMNİYET VENTİLİ', (g[0], 1130.0), 0, 0.8)
        mtyblk.insert('MTY-TERMOMETRE', (g[0], 1040.0), 90, 0.8)
        # gaz + yoğuşma
        pipe([(x + 50.0, 1150.0), (x + 50.0, 1105.0)], GAZ, 'G')
        mtyblk.insert('MTY-KURESEL VANA', (x + 50.0, 1125.0), 90, 0.5, lay_override=GAZ)
        pipe([(x + 92.0, 1150.0), (x + 92.0, 1112.0)], DRN, 'D')
        ARC((x + 92.0, 1104.0), 8, 180, 360, DRN)
        # baca
        pipe([(x + 50.0, 1290.0), (x + 50.0, 1360.0 + i * 3.0)], BACA, 'B')
        NOB((x + 118.0, 1275.0), 14)
    T((xk[0] - 10, 1095.0), 'DOĞALGAZ GİRİŞİ (GAZ PROJESİNE GÖRE)', 6, GAZ, 'R')
    T((xk[-1] + 110, 1100.0), 'YOĞUŞMA SUYU → NÖTRALİZASYON → PİS SU', 6, DRN, 'L')
    T((xk[0], 1305.0), '6 x 115 kW (95.000 kcal/h) GAZ YAKITLI DUVAR TİPİ YOĞUŞMALI KASKAD KAZAN - TOPLAM 690 kW', 9, CD, 'L')
    # baca kollektörü + baca
    pipe([(xk[0] + 50.0, 1360.0), (xk[-1] + 50.0, 1375.0), (3150.0, 1380.0), (3150.0, 1640.0)], BACA, 'B', w=4.0)
    PL([(3130.0, 1640.0), (3150.0, 1665.0), (3170.0, 1640.0)], BACA)
    T((3165.0, 1390.0), 'PASLANMAZ ÇELİK ÇİFT CİDARLI BACA (KOLLEKTÖR %2 EĞİMLİ)', 7, BACA, 'L', 90)
    # kombi kollektörleri
    pipe([(1440.0, YG), (3030.0, YG)], HGL, 'KG', w=3.0); pipe([(1440.0, YD), (3030.0, YD)], HDL, 'KD', w=3.0)
    for y in (YG, YD):
        L((3030.0, y - 8), (3030.0, y + 8), CD)
        mtyblk.insert('MTY-BOSALTMA VANA', (3015.0, y), 0, 1.0)
    T((3045.0, YG - 3), 'KOMBİ KOLLEKTÖRÜ - GİDİŞ  SİYAH BORU 3"', 7, HGL, 'L')
    T((3045.0, YD - 3), 'KOMBİ KOLLEKTÖRÜ - DÖNÜŞ  SİYAH BORU 3"', 7, HDL, 'L')
    NOB((3010.0, 990.0), 17)
    # hava ayırıcı (gidiş)
    pipe([(1440.0, YG), (1260.0, YG)], HGL, 'PG')
    HAVA_AYIRICI(1350.0, YG); NOB((1395.0, 1035.0), 13)
    T((1350.0, 880.0 + 150), '', 1, CD)
    # sekonder pompalar (paralel 1+1)
    POMPA_HAT(1260.0, 1060.0, YG, HGL, 180)
    pipe([(1260.0, YG), (1260.0, 1030.0)], HGL, 'PG'); pipe([(1060.0, 1030.0), (1060.0, YG)], HGL, 'PG')
    POMPA_HAT(1260.0, 1060.0, 1030.0, HGL, 180)
    NOB((1160.0, 1075.0), 9)
    T((1160.0, 1095.0), 'SEKONDER SİRK. POMPASI 2 x 30 m³/h - 2 mSS (1+1)', 6.5, CD, 'C')
    pipe([(1060.0, YG), (950.0, YG)], HGL, 'PG')
    mtyblk.insert('MTY-TERMOMETRE', (1010.0, YG), 0, 0.8); mtyblk.insert('MTY-MANOMETRE', (990.0, YG), 0, 0.8)
    # eşanjör
    ESANJOR(850.0, 820.0, 100.0, 180.0); NOB((900.0, 1025.0), 12)
    T((900.0, 805.0), 'PLAKALI EŞANJÖR 700 kW', 7.5, CD, 'C')
    T((900.0, 793.0), 'PRİMER 70/50 °C - SEKONDER 10/60 °C', 6, CD, 'C')
    # primer dönüş: eşanjör -> tortu ayırıcı -> genleşme / dolum -> kazan dönüş kollektörü
    pipe([(950.0, 850.0), (1440.0, 850.0), (1440.0, YD)], HDL, 'PD')
    mtyblk.insert('MTY-TERMOMETRE', (990.0, 850.0), 180, 0.8)
    TORTU_AYIRICI(1150.0, 850.0 + 55.0 - 55.0 + 55.0 - 55.0 + 0.0) if False else None
    TANK_DIK(1150.0, 795.0, 34.0, 85.0); L((1150.0, 795.0), (1150.0, 778.0), CD)
    mtyblk.insert('MTY-BOSALTMA VANA', (1150.0, 778.0), 0, 1.0)
    T((1172.0, 785.0), 'TORTU AYIRICI 50 L (BLÖF)', 6, CD, 'L'); NOB((1120.0, 900.0), 11)
    pipe([(1300.0, 850.0), (1300.0, 760.0)], HDL, 'GT')
    MEMBRANLI_TANK((1300.0, 715.0), 40.0, 90.0, CD); VANA((1300.0, 800.0), 0.8, 90)
    NOB((1340.0, 740.0), 15); T((1328.0, 700.0), 'KAPALI GENLEŞME 200 L', 6, CD, 'L')
    mtyblk.insert('MTY-EMNİYET VENTİLİ', (1230.0, 850.0), 0, 0.8)
    T((1230.0, 892.0), 'EMN. VENTİLİ 3 bar', 5.5, CD, 'C')
    # ======================= alt sıra: kullanım sıcak suyu (akümülasyon) + soğuk su
    YH, YC = 480.0, 180.0                  # tank sıcak / soğuk manifoldları
    xt = [150.0 + 110.0 * i for i in range(7)]
    for i, cx in enumerate(xt):
        TANK_DIK(cx, 230.0, 70.0, 200.0)
        T((cx, 330.0), 'AT-%d' % (i + 1), 7, CD, 'MC'); T((cx, 316.0), '1000 L', 6, CD, 'MC')
        pipe([(cx, 430.0), (cx, YH)], CH, 'T'); pipe([(cx, YC), (cx, 230.0)], CS, 'T')
        VANA((cx, 455.0), 0.7, 90); VANA((cx, 205.0), 0.7, 90)
    NOB((xt[-1] + 55.0, 400.0), 8)
    T((xt[0] - 40.0, 545.0), '7 x 1000 L EMAYE KAPLAMALI AKÜMÜLASYON (KULLANIM SICAK SUYU) TANKI - TOPLAM 7000 L', 8, CD, 'L')
    pipe([(100.0, YH), (xt[-1] + 50.0, YH)], CH, 'TH', w=3.0)
    pipe([(100.0, YC), (xt[-1] + 50.0, YC)], CS, 'TC', w=3.0)
    # eşanjör sekonder sıcak çıkış -> tank sıcak manifoldu (batı ucu)
    pipe([(850.0, YG), (820.0, YG), (820.0, 1060.0), (60.0, 1060.0), (60.0, YH), (100.0, YH)], CH, 'ES')
    mtyblk.insert('MTY-TERMOMETRE', (400.0, 1060.0), 0, 0.8)
    T((300.0, 1068.0), 'SEKONDER (KULLANIM SUYU) GİDİŞ 60 °C', 6.5, CH, 'L')
    # tank sıcak manifoldu doğu ucu -> bina sıcak su
    pipe([(xt[-1] + 50.0, YH), (xt[-1] + 50.0, 680.0)], CH, 'BS')
    ARROW((xt[-1] + 50.0, 690.0), 90, CH, 12)
    T((xt[-1] + 60.0, 640.0), 'BİNA SICAK KULLANMA SUYU', 7, CH, 'L')
    mtyblk.insert('MTY-TERMOMETRE', (xt[-1] + 50.0, 560.0), 90, 0.8)
    # tank soğuk manifoldu doğu ucu -> re-sirkülasyon (şarj) pompaları -> eşanjör sekonder giriş
    xe = xt[-1] + 50.0
    pipe([(xe, YC), (1000.0, YC), (1000.0, 790.0), (820.0, 790.0), (820.0, 850.0), (850.0, 850.0)], SIR, 'RS')
    pipe([(1000.0, 330.0), (1070.0, 330.0), (1070.0, 610.0), (1000.0, 610.0)], SIR, 'RS')
    for x in (1000.0, 1070.0):
        VANA((x, 360.0), 0.8, 90); POMPA((x, 450.0), 12, 90); CEKVALF((x, 520.0), 0.8, 90); VANA((x, 580.0), 0.8, 90)
    NOB((1110.0, 450.0), 7)
    T((1095.0, 470.0), 'RE SİRKÜLASYON POMPASI', 6.5, CD, 'L'); T((1095.0, 458.0), '2 x 9 m³/h - 3 mSS (1+1)', 6, CD, 'L')
    # dönüş kollektörü (bina sıcak su sirkülasyon dönüşleri) -> tank soğuk manifoldu
    RECT(300.0, 90.0, 700.0, 110.0, CD); NOB((720.0, 125.0), 10)
    T((300.0, 76.0), 'DÖNÜŞ KOLLEKTÖRÜ GALVANİZ 3" (BİNA SICAK SU SİRKÜLASYON DÖNÜŞLERİ)', 6.5, CD, 'L')
    for x in (360.0, 460.0, 560.0):
        pipe([(x, 20.0), (x, 90.0)], SIR, 'SD'); VANA((x, 50.0), 0.7, 90); CEKVALF((x, 30.0), 0.7, 90)
        ARROW((x, 10.0), 90, SIR, 9)
    pipe([(500.0, 110.0), (500.0, YC)], SIR, 'SD')
    # ======================= soğuk su: depo -> hidrofor -> yumuşatma -> aktif karbon -> soğuk su kollektörü
    RECT(2900.0, 100.0, 3300.0, 420.0, 'RAST-TEM-SU DEPOSU'); RECT(2915.0, 115.0, 3285.0, 405.0, 'RAST-TEM-SU DEPOSU')
    L((2915.0, 360.0), (3285.0, 360.0), 'RAST-TEM-SU DEPOSU')
    T((3100.0, 280.0), 'BETONARME SU DEPOSU', 9, YZ, 'C'); T((3100.0, 264.0), 'V = 30 ton', 8, YZ, 'C')
    NOB((3270.0, 440.0), 1)
    pipe([(3400.0, 470.0), (3200.0, 470.0), (3200.0, 405.0)], CS, 'SB')
    SAMANDIRALI_VANA((3200.0, 392.0), 0.9); VANA((3330.0, 470.0), 0.8, 0)
    T((3330.0, 482.0), 'ŞEBEKEDEN', 7, CS, 'C')
    pipe([(3285.0, 370.0), (3360.0, 370.0), (3360.0, 60.0)], CS, 'TS'); T((3368.0, 200.0), 'TAŞMA + BOŞALTMA → PİS SU (HAVA BOŞLUKLU)', 6, CS, 'L', 90)
    pipe([(2900.0, 140.0), (2840.0, 140.0)], CS, 'H')
    # hidrofor (frekans kontrollü, 1 set)
    RRECT(2560.0, 95.0, 2840.0, 255.0, 8, CD)
    T((2700.0, 268.0), 'HİDROFOR 29 m³/h - 74 mSS FREKANS KONTROLLÜ (0,4 kW)', 6.5, CD, 'C')
    NOB((2850.0, 270.0), 2)
    pipe([(2840.0, 140.0), (2600.0, 140.0)], CS, 'H'); pipe([(2820.0, 140.0), (2820.0, 200.0), (2620.0, 200.0), (2620.0, 140.0)], CS, 'H')
    for y in (140.0, 200.0):
        POMPA((2720.0, y), 12, 180); CEKVALF((2670.0, y), 0.7, 180); VANA((2790.0, y), 0.7, 0)
    pipe([(2560.0, 140.0), (2560.0, 300.0)], CS, 'H')
    MEMBRANLI_TANK((2560.0, 335.0), 30.0, 70.0, CD); NOB((2600.0, 345.0), 3); T((2578.0, 310.0), '100 L', 6, CD, 'L')
    mtyblk.insert('MTY-MANOMETRE', (2530.0, 140.0), 0, 0.8)
    pipe([(2600.0, 140.0), (2470.0, 140.0)], CS, 'H')
    # yumuşatma
    # su yumuşatma: 2 reçine kolonu (dubleks) + tuz tankı, by-pass vanalı
    pipe([(2470.0, 140.0), (2090.0, 140.0)], CS, 'H')
    for cx in (2330.0, 2230.0):
        TANK_DIK(cx, 160.0, 40.0, 120.0); L((cx, 140.0), (cx, 160.0), CD)
    RECT(2130.0, 160.0, 2180.0, 240.0, CD); T((2155.0, 200.0), 'TUZ', 6, CD, 'MC')
    L((2180.0, 220.0), (2210.0, 220.0), CD)
    pipe([(2440.0, 140.0), (2440.0, 100.0), (2120.0, 100.0), (2120.0, 140.0)], CS, 'H'); VANA((2280.0, 100.0), 0.7, 0)
    T((2280.0, 88.0), 'BY-PASS', 5.5, CS, 'C')
    NOB((2400.0, 300.0), 5); T((2280.0, 300.0), 'SU YUMUŞATMA CİHAZI 3" (DUBLEKS)', 7, CD, 'C')
    pipe([(2090.0, 140.0), (2000.0, 140.0)], CS, 'H')
    # aktif karbon filtre
    TANK_DIK(1960.0, 140.0, 50.0, 160.0); T((1960.0, 320.0), 'AKTİF KARBON FİLTRE 3"', 7, CD, 'C'); NOB((2000.0, 280.0), 6)
    pipe([(1935.0, 140.0), (1850.0, 140.0), (1850.0, 400.0), (1800.0, 400.0)], CS, 'H')
    # soğuk su kollektörü
    RECT(1480.0, 392.0, 1800.0, 408.0, CD); NOB((1820.0, 430.0), 4)
    T((1480.0, 375.0), 'SOĞUK SU KOLLEKTÖRÜ GALVANİZ 3"', 7, CD, 'L')
    # çıkışlar: kazan dolum / bina soğuk su / tank besleme
    pipe([(1550.0, 408.0), (1550.0, 700.0), (1420.0, 700.0), (1420.0, 850.0)], CS, 'DL')
    mtyblk.insert('MTY-OTOMATIK DOLUM VANASI', (1550.0, 600.0), 90, 1.0)
    T((1560.0, 600.0), 'OTOMATİK DOLUM + ÇEK VALF (KAZAN DEVRESİ)', 6, CS, 'L')
    CEKVALF((1550.0, 650.0), 0.8, 90)
    pipe([(1680.0, 408.0), (1680.0, 690.0)], CS, 'BSG'); ARROW((1680.0, 700.0), 90, CS, 12)
    T((1690.0, 680.0), 'BİNA SOĞUK SU', 7, CS, 'L'); VANA((1680.0, 470.0), 0.8, 90)
    pipe([(1480.0, 400.0), (1440.0, 400.0), (1440.0, 60.0), (700.0, 60.0), (700.0, 90.0)], CS, 'TB')
    VANA((1300.0, 60.0), 0.8, 0); CEKVALF((1250.0, 60.0), 0.8, 180)
    pipe([(900.0, 60.0), (900.0, 0.0)], CS, 'GT2'); MEMBRANLI_TANK((900.0, -40.0), 30.0, 70.0, CD)
    NOB((940.0, -30.0), 16); T((918.0, -60.0), 'GENLEŞME 50 L (SIHHİ)', 6, CD, 'L')
    T((1000.0, 68.0), 'AKÜMÜLASYON SOĞUK SU BESLEMESİ (YUMUŞATILMIŞ)', 6.5, CS, 'L')
    # başlık
    T((1700.0, 1720.0), 'KAZAN DAİRESİ ISITMA - KULLANIM SICAK SUYU - SOĞUK SU (HİDROFOR) ŞEMASI', 28, YZ, 'C')
    T((1700.0, 1690.0), 'ÖLÇEKSİZ - EKİPMAN NUMARALARI EKİPMAN LİSTESİ İLE AYNIDIR', 11, YZ, 'C')


# ================================================================== PLAN (1/50, cm)
def PLAN(ox, oy):
    push(MOVE(ox, oy))
    A = 'MIMARI'
    # kazan dairesi iç: 0..1100 x 0..700 ; depo/hidrofor dairesi: 1125..1625
    for (x0, y0, x1, y1) in ((0, 0, 1100, 700), (1125, 0, 1625, 700)):
        RECT(x0, y0, x1, y1, A)
    RECT(-25, -25, 1650, 725, A)
    L((1100, 0), (1100, 700), A); L((1125, 0), (1125, 700), A)
    # kapılar (dışa açılır, yangına dayanıklı)
    for (x0, x1) in ((900, 1000), (1450, 1540)):
        L((x0, 0), (x0, -25), A); L((x1, 0), (x1, -25), A)
        ARC((x0, -25), x1 - x0, 270, 360, A)
        L((x0, -25), (x0, -25 - (x1 - x0)), A)
    T((950.0, -140.0), 'ÇELİK KAPI 100/210 (DIŞA AÇILIR, T30)', 8, A, 'C')
    # ara duvar geçişi kapısı yok; boru geçişi kılıflı
    T((550.0, 360.0), 'KAZAN DAİRESİ', 22, 'MTY-KAT-ADI', 'C'); T((550.0, 335.0), '11,00 x 7,00 m = 77,00 m²', 10, YZ, 'C')
    T((1375.0, 690.0 - 260), 'SU DEPOSU + HİDROFOR DAİRESİ', 11, 'MTY-KAT-ADI', 'C')
    # havalandırma menfezleri (TS 12514: alt 6 cm²/kW, üst 3 cm²/kW, 690 kW)
    RECT(780, 700, 850, 725, 'MTY-CIHAZ'); T((760, 850), 'ALT HAVALANDIRMA 70x60 (≥4140 cm²) - DÖŞEMEDEN 30 cm', 7, YZ, 'L')
    RECT(980, 700, 1030, 725, 'MTY-CIHAZ'); T((1005, 790), 'ÜST HAVALANDIRMA 50x45 (≥2070 cm²) - TAVANDAN 20 cm', 7, YZ, 'C')
    # kazanlar (duvar tipi, kuzey duvarı) 6 x 60x50
    xs = [80.0 + 95.0 * i for i in range(6)]
    for i, x in enumerate(xs):
        RECT(x, 640, x + 60, 700, CD); L((x, 640), (x + 60, 700), CD); L((x, 700), (x + 60, 640), CD)
        T((x + 30, 625), 'K-%d' % (i + 1), 7, CD, 'C')
        pipe([(x + 18, 640), (x + 18, 590)], HGL, 'PK'); pipe([(x + 42, 640), (x + 42, 560)], HDL, 'PK')
    NOB((xs[-1] + 85, 670), 14)
    T((80, 760), '6 x 115 kW DUVAR TİPİ YOĞUŞMALI KASKAD KAZAN (h=1,60 m askı rafında)', 8, CD, 'L')
    # baca kollektörü (tavan) + baca (KD köşe, dış cephe)
    pipe([(xs[0] + 30, 690), (xs[-1] + 30, 690), (700, 690), (700, 760), (700, 860)], BACA, 'B', w=3.0)
    C((700, 860), 22, BACA); C((700, 860), 16, BACA)
    T((672, 860), 'BACA Ø300 PASLANMAZ ÇELİK ÇİFT CİDARLI', 7, BACA, 'R')
    # kombi kollektörleri
    pipe([(60, 590), (760, 590)], HGL, 'KG', w=3.0); pipe([(60, 560), (760, 560)], HDL, 'KD', w=3.0)
    NOB((40, 575), 17)
    # hava ayırıcı + sekonder pompalar + eşanjör + tortu ayırıcı + genleşmeler
    C((800, 590), 20, CD); NOB((800, 630), 13)
    pipe([(760, 590), (780, 590)], HGL, 'KG'); pipe([(820, 590), (860, 590)], HGL, 'KG')
    for y in (610.0, 560.0):
        POMPA((880, y), 15, 0)
    pipe([(860, 590), (860, 610), (865, 610)], HGL, 'KG'); pipe([(895, 610), (930, 610), (930, 590)], HGL, 'KG')
    NOB((880, 645), 9)
    RECT(950, 520, 1010, 640, CD); L((950, 520), (1010, 640), CD); NOB((980, 660), 12)
    T((980, 505), 'EŞANJÖR', 6, CD, 'C')
    pipe([(930, 590), (950, 590)], HGL, 'KG')
    pipe([(950, 540), (800, 540), (800, 560), (760, 560)], HDL, 'KD')
    C((840, 515), 18, CD); NOB((840, 480), 11)
    C((1050, 440), 30, CD); T((1050, 440), '200L', 6, CD, 'MC'); NOB((1050, 485), 15)
    C((1060, 360), 20, CD); T((1060, 360), '50L', 6, CD, 'MC'); NOB((1060, 395), 16)
    pipe([(1010, 540), (1050, 540), (1050, 470)], HDL, 'GT')
    # akümülasyon tankları (güney duvarı önü, Ø90)
    xt = [70.0 + 108.0 * i for i in range(7)]
    for i, cx in enumerate(xt):
        C((cx, 85), 45, CD); C((cx, 85), 40, CD); T((cx, 85), 'AT-%d' % (i + 1), 7, CD, 'MC')
    NOB((xt[-1] + 60, 160), 8)
    T((430, 150), '7 x 1000 L EMAYE AKÜMÜLASYON TANKI (Ø90)', 8, CD, 'C')
    pipe([(25, 150), (xt[-1] + 30, 150)], CH, 'TH'); pipe([(25, 190), (xt[-1] + 30, 190)], SIR, 'TC')
    for cx in xt:
        pipe([(cx, 130), (cx, 150)], CH, 'T')
    # re-sirkülasyon pompaları + dönüş kollektörü
    for x in (900.0, 960.0):
        POMPA((x, 250), 14, 90)
    NOB((1000, 280), 7)
    pipe([(xt[-1] + 30, 190), (900, 190), (900, 236)], SIR, 'RS'); pipe([(900, 264), (900, 400), (930, 400), (930, 520), (950, 520)], SIR, 'RS')
    RECT(20, 240, 40, 460, CD); NOB((70, 470), 10); T((50, 350), 'DÖNÜŞ KOL.', 6, CD, 'L', 90)
    pipe([(30, 240), (30, 190), (40, 190)], SIR, 'DK')
    # soğuk su kollektörü (batı duvarı)
    RECT(20, 480, 40, 540, CD); NOB((70, 520), 4)
    # elektrik / otomasyon panosu
    RECT(1040, 20, 1095, 45, 'MTY-ELEKTRIK'); T((1067, 55), 'ELK. + KASKAD KONTROL PANOSU', 6, 'MTY-ELEKTRIK', 'C')
    # yer süzgeci + gaz alarm
    C((600, 260), 10, 'MTY-PIS-SU-BORUSU'); T((615, 255), 'YER SÜZGECİ Ø100', 6, 'MTY-PISSU-CAP', 'L')
    T((1090, 690), 'GAZ ALARM + SELENOİD VANA', 6, GAZ, 'R')
    # ----- depo / hidrofor dairesi
    RECT(1150, 380, 1600, 680, 'RAST-TEM-SU DEPOSU'); RECT(1170, 400, 1580, 660, 'RAST-TEM-SU DEPOSU')
    T((1375, 545), 'BETONARME SU DEPOSU 30 TON', 9, YZ, 'C'); T((1375, 528), 'iç 4,10 x 2,60 x h 3,00 m', 7, YZ, 'C')
    RECT(1330, 640, 1390, 660, 'RAST-TEM-SU DEPOSU'); T((1360, 625), 'MENHOL 60x60', 6, YZ, 'C')
    NOB((1590, 700), 1)
    RRECT(1160, 120, 1330, 220, 6, CD)
    for x in (1200.0, 1250.0, 1300.0):
        C((x, 170), 16, CD)
    T((1245, 105), 'HİDROFOR 29 m³/h 74 mSS', 6.5, CD, 'C'); NOB((1245, 245), 2)
    C((1375, 170), 22, CD); T((1375, 170), '100L', 5.5, CD, 'MC'); NOB((1375, 205), 3)
    for x in (1440.0, 1490.0):
        C((x, 170), 18, CD)
    C((1550, 170), 25, CD); T((1490, 125), 'YUMUŞATMA (2 kolon + tuz)', 6, CD, 'C'); NOB((1490, 210), 5)
    C((1560, 290), 22, CD); T((1560, 325), 'AKTİF KARBON', 6, CD, 'C'); NOB((1600, 300), 6)
    pipe([(1245, 380), (1245, 220)], CS, 'H'); pipe([(1330, 170), (1353, 170)], CS, 'H'); pipe([(1397, 170), (1422, 170)], CS, 'H')
    pipe([(1508, 170), (1525, 170)], CS, 'H'); pipe([(1560, 195), (1560, 268)], CS, 'H')
    pipe([(1538, 290), (1112, 290), (1112, 510), (40, 510)], CS, 'H')
    T((1135, 300), 'YUMUŞATILMIŞ SU → SOĞUK SU KOLLEKTÖRÜ (TAVANDAN, DUVAR GEÇİŞİ KILIFLI)', 6, CS, 'L')
    pipe([(1600, 600), (1680, 600)], CS, 'SB'); T((1690, 600), 'ŞEBEKEDEN (ŞAMANDIRALI VANA)', 7, CS, 'L')
    T((1375, 360), 'TAŞMA/BOŞALTMA → PİS SU (HAVA BOŞLUKLU)', 6, CS, 'C')
    # başlık
    T((800.0, -230.0), 'KAZAN DAİRESİ VE SU DEPOSU / HİDROFOR DAİRESİ PLANI', 28, 'MTY-KAT-ADI', 'C')
    T((800.0, -262.0), 'ÖLÇEK : 1/50 - TİPİK YERLEŞİM (MİMARİ PROJEYE GÖRE YERİNDE UYARLANACAKTIR)', 11, 'MTY-KAT-ADI', 'C')
    pop()


# ================================================================== EKİPMAN LİSTESİ + HESAP ÖZETİ + NOTLAR
HESAP = [
    ('Toplam kazan kapasitesi', '6 x 115 kW', '690 kW ≈ 700 kW eşanjör ✓'),
    ('Primer (kazan) debisi  Q = P / (1,163 · ΔT), 70/50 °C', '700 / (1,163 x 20)', '30,1 m³/h → sekonder pompa 30 m³/h ✓'),
    ('Kollektör hızı (3" iç Ø80,8 mm)', 'v = Q / A', '30 m³/h → 1,63 m/s (≤ 2 m/s) ✓'),
    ('Alt havalandırma (TS 12514: 6 cm²/kW)', '690 x 6', '4140 cm² → 70 x 60 cm'),
    ('Üst havalandırma (TS 12514: 3 cm²/kW)', '690 x 3', '2070 cm² → 50 x 45 cm'),
    ('Akümülasyon kapasitesi', '7 x 1000 L', '7000 L (60 °C)'),
    ('Kullanım suyu ısıtma süresi (10→60 °C, 700 kW)', '7000 x 1,163 x 50 / 700.000 h', '0,58 h ≈ 35 dk'),
    ('Su deposu', '30 ton betonarme', 'hidrofor debisinin ≈ 1 saatlik karşılığı'),
]
NOTLAR = [
    'Kazan dairesi yerleşimi tipik olup mimari projedeki kazan dairesi ölçülerine göre yerinde uyarlanacaktır.',
    'Kazanlar kaskad kontrol panosu ile sırayla devreye alınacak, dış hava kompanzasyonlu çalıştırılacaktır.',
    'Kazan dairesi kapısı dışa açılır, T30 yangın dayanımlı çelik kapı olacaktır.',
    'Alt ve üst havalandırma menfezleri TS 12514 değerlerine göre doğrudan dış havaya açılacaktır.',
    'Baca paslanmaz çelik çift cidarlı olacak, kaskad baca kollektörü %2 eğimle kazanlara doğru yoğuşma drenajlı yapılacaktır.',
    'Yoğuşma suları nötralizasyon cihazından geçirilerek pis su tesisatına verilecektir.',
    'Kazan ve primer devre kapalı genleşme tankı (200 L) ve 3 bar emniyet ventili ile korunacaktır.',
    'Kullanım sıcak suyu devresinde 50 L sıhhi tip genleşme tankı ve 6 bar emniyet ventili bulunacaktır.',
    'Akümülasyon tankları haftada bir 70 °C lejyoner şoklaması yapılacak şekilde kontrol edilecektir.',
    'Kazan dairesinde gaz alarm cihazı ve gaz girişinde selenoid vana bulunacak; doğalgaz tesisatı ayrı projeye göre yapılacaktır.',
    'Tüm vanalar küresel / kelebek tip, pompalar frekans kontrollü olacak; pompa giriş-çıkışlarına titreşim alıcı konulacaktır.',
    'Kazan dairesinde yer süzgeci ve aydınlatma etanj tip olacaktır.',
]


def LISTE(ox, oy):
    T((ox, oy), 'EKİPMAN LİSTESİ', 22, YZ, 'L')
    cw = [60, 420, 90, 900]
    xs = [ox]
    for w in cw:
        xs.append(xs[-1] + w)
    rh = 34
    y = oy - 30
    hdr = ['NO', 'ADI', 'ADEDİ', 'ÖZELLİĞİ']
    rows = [hdr] + [[str(a), b, str(c), d] for a, b, c, d in EKIPMAN]
    for i, r in enumerate(rows):
        yy = y - i * rh
        L((xs[0], yy), (xs[-1], yy), 'MTY-PAFTA')
        for j, s in enumerate(r):
            T((xs[j] + 8, yy - rh / 2), s, 10 if i else 11, YZ, 'ML' if True else 'L')
    yb = y - len(rows) * rh
    L((xs[0], yb), (xs[-1], yb), 'MTY-PAFTA')
    for x in xs:
        L((x, y), (x, yb), 'MTY-PAFTA')
    # hesap
    hy = yb - 70
    T((ox, hy), 'HESAP ÖZETİ / KONTROLLER', 18, YZ, 'L')
    for i, (a, b, c) in enumerate(HESAP):
        T((ox, hy - 34 - i * 22), a, 10, 'MTY-HESAP', 'L')
        T((ox + 640, hy - 34 - i * 22), b, 10, 'MTY-HESAP', 'L')
        T((ox + 1000, hy - 34 - i * 22), c, 10, 'MTY-HESAP', 'L')
    ny = hy - 34 - len(HESAP) * 22 - 50
    T((ox, ny), 'NOTLAR', 18, YZ, 'L')
    for i, n in enumerate(NOTLAR):
        T((ox, ny - 32 - i * 20), '%d. %s' % (i + 1, n), 10, YZ, 'L')
    return ny - 32 - len(NOTLAR) * 20


if __name__ == '__main__':
    SEMA()
    PLAN(4300.0, 300.0)
    yl = LISTE(6400.0, 1650.0)
    FR = [((-150.0, -200.0, 3700.0, 1800.0), 'KAZAN DAİRESİ ŞEMASI', 'ÖLÇEKSİZ'),
          ((3900.0, -100.0, 6250.0, 1350.0), 'KAZAN DAİRESİ VE SU DEPOSU PLANI', '1/50'),
          ((6300.0, yl - 120.0, 8000.0, 1800.0), 'EKİPMAN LİSTESİ, HESAP ÖZETİ VE NOTLAR', 'ÖLÇEKSİZ')]
    for (a, b, c, d), t, o in FR:
        GS.frame(a, b, c, d, t, o)
        T((a + 40, d - 50), 'ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK.  -  Mak. Müh. Bayram GENÇ', 10, 'MTY-PAFTA', 'L')
    import xcheck
    xr = xcheck.crossings()
    print('köprü', xcheck.hops(xr), 'çakışık', [r for r in xcheck.summary(xr) if r[0] == 'ÇAKIŞIK'][:10])
    print('maske', xcheck.wipe_texts())
    pickle.dump((cad.R, FR, cad.BLK), open('/tmp/claude-0/kd/kd_R.pkl', 'wb'))
    print('ok', len(cad.R))
