"""SİNEM TURHAN - 3 bağımsız bölümlü mesken (2. bodrum: müştemilat + depo/hidrofor, 1. bodrum D-1, zemin D-2, 1. kat D-3).
Koordinatlar: 'bina çerçevesi' = mimari 1. BODRUM kat planı kaynak koordinatı (cm).
Kaynak kaydırmaları: 2. bodrum -1680, zemin +1680, 1. kat +3360, çatı +5040.
Kot: 2.B -6,00 / 1.B -3,00 / Z ±0,00 [102,55] / 1.K +3,00 / çatı +6,00. Yol ve kanal güney (bina girişi) tarafında.
"""
import math, pickle, sys
from shapely.geometry import LineString
from shapely import affinity
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import cad
from cad import L, PL, C, T, RECT, ARC, ARROW, SOL, push, pop, MOVE, VANA, CEKVALF, SAYAC, PISLIK_TUTUCU, TEMIZLEME_KAPAGI, \
    HEXTAG, POMPA, MEMBRANLI_TANK, DALGIC_POMPA
import mtyblk
import gp
from gp import CS, CH, PS, PST, TSC, PSC, YBL, VN, CD, YZ, YL, YC, pipe, node, Fix, cap_temiz, cap_pis, fmt, dn_temiz, dn_sb
import gheat as GH

FLAT = pickle.load(open('/tmp/claude-0/p2/st.dxf.flat.pkl', 'rb'))
SRC = {'B2': -1680.0, 'B1': 0.0, 'Z': 1680.0, '1': 3360.0, 'C': 5040.0}
WIN = (12070.0, 9790.0, 13150.0, 11560.0)
WIN_C = (12040.0, 9700.0, 13200.0, 11600.0)
SLOT = 1500.0
SLOTS = {'T': 0, 'B2': 1, 'B1': 2, 'Z': 3, '1': 4, 'C': 5}
NAMES = {'T': 'ALTYAPI PLANI (ZEMİN KOTU)', 'B2': '2. BODRUM KAT SIHHİ TESİSAT PLANI', 'B1': '1. BODRUM KAT SIHHİ TESİSAT PLANI',
         'Z': 'ZEMİN KAT SIHHİ TESİSAT PLANI', '1': '1. KAT SIHHİ TESİSAT PLANI', 'C': 'ÇATI PLANI (HAVALIKLAR / YAĞMUR)'}
KOT = {'T': '±0,00 ZEMİN (KOLON DİPLERİ)', 'B2': '-6,00', 'B1': '-3,00', 'Z': '±0,00 [102,55]', '1': '+3,00', 'C': '+6,00 ÇATI'}
FY0, FY1 = 9100.0, 11750.0          # pafta y sınırları
HDY = -2750.0                        # ısıtma sırası


def dx(k):
    return SLOTS[k] * SLOT - 12080.0 + 200.0


def COLS():
    return gp.columns(FLAT, (12080, 9800, 13150, 11560))


# ================================================================== armatürler (1., zemin ve 1. kat aynı)
F_K = {
    # büyük banyo-WC (5,41 m²)
    'LV1': Fix('LV', (12845.0, 10114.0), 0, name='LV1'), 'CM1': Fix('CM', (12942.0, 10114.0), 0, name='CM1'),
    'WC1': Fix('WC', (13074.0, 10256.0), 90, name='WC1'), 'DUS1': Fix('DUS', (12960.0, 10293.0), 180, name='DUS1'),
    'YS1': Fix('YS', (12890.0, 10190.0), 0, name='YS1'),
    # küçük banyo-WC (2,89 m²)
    'LV2': Fix('LV', (12792.0, 10838.0), 180, name='LV2'), 'WC2': Fix('WC', (12872.0, 10838.0), 180, name='WC2'),
    'YS2': Fix('YS', (12925.0, 10770.0), 0, name='YS2'),
    # mutfak
    'EV': Fix('EV', (12974.0, 11056.0), 90, name='EV'), 'BM': Fix('BM', (12974.0, 10999.0), 90, name='BM'),
    'KM': Fix('KOMBI', (12977.0, 11268.0), 90, name='KM'),
}
PK1 = (13045.0, 10160.0)     # büyük banyo kolonu
PK2 = (12960.0, 10826.0)     # küçük banyo kolonu
MK1 = (12940.0, 10930.0)     # mutfak kolonu
PR = (13025.0, 10100.0)      # dalgıç pompa basma hattı (PÇ'den zemin kotuna çıkar, R2'ye)
BK = {'BPK1': PK1, 'BPK2': PK2, 'BMK1': MK1}   # 1. bodrum kolonları (üst katlardaki gibi; 2. bodrum döşeme altından PÇ'ye)
RZ = {'DBK': (12627.0, 9900.0), 'D1': (12627.0, 9912.0), 'D3': (12627.0, 9924.0), 'ADK': (12627.0, 9936.0)}
E_IN = (12700.0, 10110.0)    # daire girişi (hol)
PIT = (12945.0, 10115.0, 13045.0, 10215.0)     # pis su çukuru (2. bodrum, müştemilat)
DEPO = (12374.0, 10134.0, 12574.0, 10281.0)    # 3 m³ depo (mimari, 2. bodrum)
HIDRO = (12596.0, 10226.0, 12716.0, 10300.0)   # hidrofor grubu
YSD = (12300.0, 10295.0)    # depo odası yer süzgeci
R1 = (12955.0, 9655.0)     # zemin kolonları rögarı (bina dışı)
R2 = (13095.0, 9655.0)     # pompa basma rögarı (bina dışı)
PB = (12955.0, 9465.0)     # parsel bacası
YB_PTS = {'YB1': (12137.0, 11529.0), 'YB2': (12992.0, 11529.0), 'YB3': (13120.0, 9769.0), 'YB4': (12335.0, 9769.0)}
ROOF_A = 164.0

SB = gp.SB
SB_B1 = SB['WC'] + SB['DUS'] + SB['LV'] + SB['CM'] + SB['YS']      # 25
SB_B2 = SB['WC'] + SB['LV'] + SB['YS']                               # 14
SB_M = SB['EV'] + SB['BM']                                           # 8
SB_D = SB_B1 + SB_B2 + SB_M                                          # 47
YB_D = 5.5      # 2xWC .5 + 2xLV .5 + DUŞ 1 + ÇM 1 + EV .5 + BM 1
KOMBI_SPEC = ['DUVAR TİPİ HERMETİK YOĞUŞMALI KOMBİ (HER DAİREYE 1 ADET) 24 kW',
              'SICAK SU: 11,5 l/dk (ΔT=30 K) - BACA Ø60/100 DIŞ CEPHEYE (MİMARİ KOMBİ NİŞİ)',
              'YERDEN ISITMA: GİDİŞ/DÖNÜŞ 45/35 °C (KOMBİ DÜŞÜK SICAKLIK AYARLI)']
# pompa / hidrofor hesap özeti (Excel ile aynı)
Q_PIS = 0.5 * math.sqrt(SB_D + 2)               # l/s (K=0,5 konut)
H_PIS = (-0.60 - (-7.00)) + 2.5               # statik + kayıplar (m)
Q_HID = 0.25 * math.sqrt(3 * YB_D) * 3.6      # m³/h
H_HID = (3.00 + 2.20 - (-5.50)) + 15.0 + 4.0  # geodezik + en uç basınç + kayıp (mSS)
PUMP_TXT = ['PİS SU ÇUKURU 100x100x120 cm (BETONARME, İZOLELİ, SIZDIRMAZ KAPAKLI)',
            '2 ADET DALGIÇ PİS SU POMPASI (1 ASIL + 1 YEDEK, ŞAMANDIRALI, SEVİYE ALARMLI)',
            'Q = %.1f l/s (%.1f m³/h) - H = %.1f mSS - BASMA HATTI PE100 Ø63 (ÇEK VALF + VANA)' % (Q_PIS, Q_PIS * 3.6, H_PIS)]
HID_TXT = ['HİDROFOR: 2 POMPALI (1+1) FREKANS KONVERTÖRLÜ PAKET HİDROFOR',
           'Q = %.1f m³/h  -  H = %.0f mSS (%.1f bar)  -  MEMBRANLI TANK 200 lt' % (Q_HID, H_HID, H_HID / 10.0),
           'KURU ÇALIŞMA KORUMALI (DEPO SEVİYE ŞAMANDIRASI)']


# ================================================================== yardımcılar
def floor_arch(k, sy=0.0, furn=True):
    push(MOVE(dx(k) - SRC[k], sy))
    w = WIN_C if k == 'C' else WIN
    gp.copy_arch(FLAT, (w[0] + SRC[k], w[1], w[2] + SRC[k], w[3]), furn=furn, room_labels=(sy == 0.0))
    pop()


def frame_title(k, sy, sub=None):
    gp.title((dx(k) + 12600.0, 9230.0 + sy), NAMES[k] if sy == 0 else sub, 'ÖLÇEK : 1/50   KOT: ' + KOT[k])


def clamp(v, a, b):
    return max(a, min(b, v))


# ================================================================== pis su (kat içi) - her mahal kendi kolonuna
def pis_kat(t1, t2, t3):
    F = F_K
    wc, lv, cm, ds, ys = (F[n].cp('PS') for n in ('WC1', 'LV1', 'CM1', 'DUS1', 'YS1'))
    yc = 10150.0
    pipe([wc, (wc[0], t1[1] + 14.0), t1], PS, 'P')
    pipe([lv, (lv[0], yc), (t1[0] - 14.0, yc), t1], PS, 'P')
    pipe([cm, (cm[0], yc)], PS, 'P')
    pipe([ys, (ys[0], yc)], PS, 'P')
    pipe([ds, (ds[0], yc)], PS, 'P')
    wc, lv, ys = (F[n].cp('PS') for n in ('WC2', 'LV2', 'YS2'))
    pipe([wc, (t2[0] - 14.0, wc[1]), t2], PS, 'P')
    pipe([lv, (lv[0], 10798.0), (t2[0] - 16.0, 10798.0), t2], PS, 'P')
    pipe([ys, (ys[0], 10798.0)], PS, 'P')
    ev, bm = F['EV'].cp('PS'), F['BM'].cp('PS')
    pipe([bm, (t3[0] + 5.0, bm[1]), (t3[0] + 5.0, t3[1] + 12.0), t3], PS, 'P')
    pipe([ev, (t3[0] + 5.0, ev[1]), (t3[0] + 5.0, bm[1])], PS, 'P')
    k = 5.0
    cap_pis((12870.0, yc), 0, '%d SB' % (SB['LV'] + SB['YS'] + SB['CM']), 'Ø70', k)
    cap_pis((12985.0, yc), 0, '%d SB' % (SB['LV'] + SB['YS'] + SB['CM'] + SB['DUS']), 'Ø70', k)
    cap_pis((wc[0] + 20, wc[1]), 0, '10 SB', 'Ø100', k)
    cap_pis((F['WC1'].cp('PS')[0], 10215.0), 90, '10 SB', 'Ø100', k)
    cap_pis((12905.0, 10798.0), 0, '4 SB', 'Ø50', k)
    cap_pis((t3[0] + 5.0, 10975.0), 90, '8 SB', 'Ø50', k)


def temiz_kat(entry_from):
    """daire içi temiz su (soğuk/sıcak). entry_from: kolondan daire girişine gelen hat noktaları"""
    F = F_K
    ex, ey = E_IN
    pipe(entry_from + [E_IN], CS, 'S')
    VANA((ex, ey - 8.0), 0.4, 90)
    xl, xh = 12725.0, 12731.0
    pipe([E_IN, (xl, ey), (xl, 10846.0), (12970.0, 10846.0), (12970.0, F['KM'].cp('SO')[1]), F['KM'].cp('SO')], CS, 'S')
    pipe([(12970.0, F['BM'].cp('SO')[1]), F['BM'].cp('SO')], CS, 'S')
    pipe([(12970.0, F['EV'].cp('SO')[1]), F['EV'].cp('SO')], CS, 'S')
    for n in ('LV2', 'WC2'):
        so = F[n].cp('SO')
        pipe([(so[0], 10846.0), so], CS, 'S')
    # büyük banyo: güney duvarı (lavabo, çamaşır) + kuzey duvarı (duş, wc)
    pipe([(xl, ey), (xl, 10106.0), (F['CM1'].cp('SO')[0], 10106.0), F['CM1'].cp('SO')], CS, 'S')
    pipe([(F['LV1'].cp('SO')[0], 10106.0), F['LV1'].cp('SO')], CS, 'S')
    so_d, so_w = F['DUS1'].cp('SO'), F['WC1'].cp('SO')
    pipe([(xl, 10302.0), (so_w[0], 10302.0), so_w], CS, 'S')
    pipe([(so_d[0], 10302.0), so_d], CS, 'S')
    # sıcak: kombi -> eviye -> küçük banyo lavabo -> büyük banyo (duş, lavabo)
    sc = F['KM'].cp('SC')
    pipe([sc, (12964.0, sc[1]), (12964.0, F['EV'].cp('SC')[1]), F['EV'].cp('SC')], CH, 'S')
    pipe([(12964.0, F['EV'].cp('SC')[1]), (12964.0, 10852.0), (xh, 10852.0), (xh, 10296.0), (F['DUS1'].cp('SC')[0], 10296.0),
          F['DUS1'].cp('SC')], CH, 'S')
    s2 = F['LV2'].cp('SC')
    pipe([(s2[0], 10852.0), s2], CH, 'S')
    pipe([(xh, 10296.0), (xh, 10116.0), (F['LV1'].cp('SC')[0], 10116.0), F['LV1'].cp('SC')], CH, 'S')
    k = 5.0
    cap_temiz((12760.0, 10846.0), 0, so='3.5 YB', socp='Ø25', k=k)
    cap_temiz((12880.0, 10852.0), 0, sc='1.5 YB', sccp='Ø20', k=k)
    cap_temiz((12725.0, 10500.0), 90, so='%s YB' % fmt(YB_D), socp='Ø%d' % dn_temiz(YB_D), k=k)
    cap_temiz((12731.0, 10600.0), 90, sc='2.5 YB', sccp='Ø25', k=k)
    cap_temiz((12800.0, 10106.0), 0, so='1.5 YB', socp='Ø20', k=k)
    cap_temiz((12800.0, 10302.0), 0, so='1.5 YB', socp='Ø20', k=k)
    for i, s in enumerate(KOMBI_SPEC):
        T((12640.0, 11180.0 - i * 10.0), s, 5.5, CD, 'L')
    T((12640.0, 11192.0), 'KOMBİ (MİMARİ KOMBİ NİŞİNDE)', 7, CD, 'L')


def kolon_etiket(fk):
    up = {'B1': 1, 'Z': 2, '1': 1}[fk]
    nms = ('BPK1', 'BPK2', 'BMK1') if fk == 'B1' else ('PK1', 'PK2', 'MK1')
    for p, nm, sb, off, d in ((PK1, nms[0], up * SB_B1, (60, 60), 100), (PK2, nms[1], up * SB_B2, (70, -60), 100),
                              (MK1, nms[2], up * SB_M, (-90, 50), 70)):
        gp.kolon_pis(p, nm, off, k=0.6 if d == 100 else 0.5)
        T((p[0] + off[0] + 2, p[1] + off[1] - 17), 'Ø%d / %d SB' % (d, sb), 7, PSC, 'L')


def gecen_kolonlar(fk):
    for nm, p in RZ.items():
        if nm in ('DBK', 'ADK') or (nm == 'D1' and fk in ('B1', 'Z', 'B2')) or (nm == 'D3' and fk in ('Z', '1', 'B2', 'B1')):
            gp.kolon_temiz(p)
            node(p, nm)
    T((12600.0, 9870.0), 'TS KOLONLARI', 5.5, TSC, 'R')
    T((12600.0, 9860.0), 'DBK Ø32 / ADK Ø32 / D1-D3 Ø25', 5.0, TSC, 'R')


# ================================================================== 1. BODRUM (D-1)
def bodrum1():
    push(MOVE(dx('B1'), 0.0))
    for f in F_K.values():
        f.draw()
    pis_kat(PK1, PK2, MK1)
    kolon_etiket('B1')
    cad.KOLON(PR, 4, 'MTY-PIS SU-BASMA'); node(PR, 'PR')
    T((PR[0] + 8, PR[1] - 14), 'POMPA BASMA Ø63 ↑ (R2)', 5.5, PSC, 'L')
    # temiz su: D1 kolonu (zeminden iner) -> daire girişi
    gecen_kolonlar('B1')
    temiz_kat([RZ['D1'], (12700.0, RZ['D1'][1]), (12700.0, 10090.0)])
    cap_temiz((12660.0, RZ['D1'][1]), 0, so='D1 %s YB' % fmt(YB_D), socp='Ø%d' % dn_temiz(YB_D), k=5.0)
    pop()


# ================================================================== ZEMİN (D-2) + sayaçlar
def zemin():
    push(MOVE(dx('Z'), 0.0))
    for f in F_K.values():
        f.draw()
    pis_kat(PK1, PK2, MK1)
    kolon_etiket('Z')
    gecen_kolonlar('Z')
    # şebeke -> ana sayaç nişi (ön cephe, bina girişi yanı) -> DBK (2. bodrum deposuna iner)
    nx, ny = 12680.0, 9800.0
    RECT(nx - 30, ny - 14, nx + 30, ny + 6, VN)
    T((nx, ny - 26), 'ANA SAYAÇ NİŞİ (SASKİ)', 7, VN, 'C')
    pipe([(nx - 45, 9560.0), (nx - 45, ny - 4), (nx - 20, ny - 4)], CS, 'S')
    VANA((nx - 45, 9600.0), 0.5, 90)
    PISLIK_TUTUCU((nx - 10, ny - 4), 0.45, 0); SAYAC((nx + 4, ny - 4), 0.6, 0); CEKVALF((nx + 18, ny - 4), 0.45, 0)
    pipe([(nx - 20, ny - 4), (nx + 26, ny - 4), (nx + 26, 9870.0), (12645.0, 9870.0), (12645.0, RZ['DBK'][1]), RZ['DBK']], CS, 'S')
    node((nx - 45, 9560.0), 'ŞEBEKE')
    T((nx - 52, 9570.0), 'ŞEBEKEDEN (SASKİ) Ø32', 7, TSC, 'R', 90)
    T((12800.0, 9870.0), 'DBK Ø32 → 2. BODRUM DEPOSU', 6, TSC, 'L')
    # sayaç grubu (bina girişi - kat holü batı duvarı): ADK (hidrofordan) -> 3 sayaç
    RECT(12627.0, 9950.0, 12680.0, 10025.0, VN)
    T((12690.0, 10030.0), 'SAYAÇ GRUBU (BİNA GİRİŞİ)', 6.5, VN, 'L')
    T((12690.0, 10020.0), '3 SAYAÇ + VANA + ÇEK VALF', 5.5, VN, 'L')
    pipe([RZ['ADK'], (12627.0, 9955.0), (12634.0, 9955.0), (12634.0, 10010.0)], CS, 'S')
    SY = {'D3': 9970.0, 'D1': 9990.0, 'D2': 10010.0}
    for nm, yy in SY.items():
        pipe([(12634.0, yy), (12672.0, yy)], CS, 'S')
        mtyblk.insert('MTY-SU SAYACI', (12652.0, yy), 0, 0.28)
        T((12674.0, yy + 2), nm, 5, VN, 'L')
    pipe([(12672.0, SY['D3']), (12684.0, SY['D3']), (12684.0, RZ['D3'][1]), RZ['D3']], CS, 'S')
    pipe([(12672.0, SY['D1']), (12690.0, SY['D1']), (12690.0, RZ['D1'][1]), RZ['D1']], CS, 'S')
    temiz_kat([(12672.0, SY['D2']), (12700.0, SY['D2']), (12700.0, 10090.0)])
    cap_temiz((12560.0, 9955.0), 0, so='ADK %s YB' % fmt(3 * YB_D), socp='Ø%d' % dn_temiz(3 * YB_D), k=5.0)
    pop()


# ================================================================== 1. KAT (D-3)
def kat1():
    push(MOVE(dx('1'), 0.0))
    for f in F_K.values():
        f.draw()
    pis_kat(PK1, PK2, MK1)
    kolon_etiket('1')
    gecen_kolonlar('1')
    temiz_kat([RZ['D3'], (12700.0, RZ['D3'][1]), (12700.0, 10090.0)])
    cap_temiz((12660.0, RZ['D3'][1]), 0, so='D3 %s YB' % fmt(YB_D), socp='Ø%d' % dn_temiz(YB_D), k=5.0)
    pop()


# ================================================================== 2. BODRUM: depo + hidrofor + pis su çukuru
def bodrum2():
    push(MOVE(dx('B2'), 0.0))
    x0, y0, x1, y1 = DEPO
    T(((x0 + x1) / 2, (y0 + y1) / 2 + 8), 'KULLANMA SUYU DEPOSU', 7, YZ, 'C')
    T(((x0 + x1) / 2, (y0 + y1) / 2 - 6), 'V = 3,00 m³', 9, 'RAST-TEM-SU DEPOSU', 'C')
    # DBK (zeminden iner) -> şamandıralı giriş
    pipe([RZ['DBK'], (12627.0, 10265.0), (x1, 10265.0)], CS, 'S')
    cad.SAMANDIRALI_VANA((x1 - 6, 10265.0), 0.6)
    node((x1, 10265.0), 'DEPO')
    # depo çıkışı -> hidrofor emiş
    hx0, hy0, hx1, hy1 = HIDRO
    pipe([(x1, 10150.0), (12588.0, 10150.0), (12588.0, 10245.0), (hx0, 10245.0)], CS, 'S')
    node((x1, 10150.0), 'DEPO'); node((hx0, 10245.0), 'HİD')
    mtyblk.insert('MTY-KURESEL VANA', (12588.0, 10190.0), 90, 0.4)
    RECT(hx0, hy0, hx1, hy1, gp.HID)
    for j in range(2):
        POMPA((hx0 + 30 + j * 40, hy0 + 20), 10, 0, gp.HID)
    MEMBRANLI_TANK((hx1 - 14, hy0 + 40), 20, 50, gp.HID)
    T((hx0, hy1 + 8), 'HİDROFOR', 8, gp.HID, 'L')
    for i, s in enumerate(HID_TXT):
        T((hx0 - 300, 10420.0 - i * 10.0), s, 6.0, gp.HID, 'L')
    # hidrofor basma -> ADK (zemin sayaç grubuna çıkar)
    pipe([(hx1, 10240.0), (12726.0, 10240.0), (12726.0, 10120.0), (12640.0, 10120.0), (12640.0, RZ['ADK'][1]), RZ['ADK']], CS, 'S')
    node((hx1, 10240.0), 'HİD')
    CEKVALF((12726.0, 10200.0), 0.45, 90)
    cap_temiz((12726.0, 10170.0), 90, so='ADK %s YB' % fmt(3 * YB_D), socp='Ø32', k=5.0)
    cap_temiz((12627.0, 10200.0), 90, so='DBK', socp='Ø32', k=5.0)
    gecen_kolonlar('B2')
    # taşma + boşaltma -> yer süzgeci -> pis su çukuru (döşeme altı)
    ysp = YSD
    mtyblk.insert('YER SUZGECI DN501', ysp, 0, 1.0); node(ysp, 'YS-D')
    pipe([(x0, 10270.0), (ysp[0] + 8, 10270.0), (ysp[0] + 8, ysp[1] - 6)], CS, 'X')       # taşma (üst)
    node((x0, 10270.0), 'DEPO'); node((ysp[0] + 8, ysp[1] - 6), 'YS-D')
    pipe([(x0, 10150.0), (ysp[0], 10150.0), (ysp[0], ysp[1] - 10)], CS, 'X')               # boşaltma (alt)
    node((x0, 10150.0), 'DEPO'); node((ysp[0], ysp[1] - 10), 'YS-D')
    mtyblk.insert('MTY-KURESEL VANA', (12340.0, 10150.0), 0, 0.35)
    T((12262.0, 10125.0), 'TAŞMA Ø40 / BOŞALTMA Ø32', 5.5, TSC, 'L')
    T((12262.0, 10115.0), '→ YER SÜZGECİ (HAVA BOŞLUKLU)', 5.5, TSC, 'L')
    DR = [ysp, (ysp[0], 10307.0), (12900.0, 10307.0), (12900.0, 10135.0), (PIT[0], 10135.0)]
    pipe(DR, PS, 'P')
    node(DR[-1], 'PÇ')
    cap_pis((12780.0, 10307.0), 0, '2 SB', 'Ø70', 5.0)
    T((12460.0, 10318.0), 'DÖŞEME ALTI Ø70 %2 → PÇ', 5.5, PSC, 'L')
    # pis su çukuru + dalgıç pompalar
    px0, py0, px1, py1 = PIT
    PL([(px0, py0), (px1, py0), (px1, py1), (px0, py1)], PS, True, 2.0)
    PL([(px0 + 6, py0 + 6), (px1 - 6, py0 + 6), (px1 - 6, py1 - 6), (px0 + 6, py1 - 6)], PS, True, 0.0)
    DALGIC_POMPA((px0 + 30, py0 + 30), 0.9, 'MTY-CIHAZ'); DALGIC_POMPA((px0 + 62, py0 + 30), 0.9, 'MTY-CIHAZ')
    T((px0 - 5, py1 + 12), 'PİS SU ÇUKURU (PÇ)', 8, PSC, 'R')
    T((12520.0, 9772.0), 'PİS SU ÇUKURU (PÇ) VE POMPALAR:', 6.5, PSC, 'L')
    for i, s in enumerate(PUMP_TXT):
        T((12520.0, 9760.0 - i * 9), s, 5.5, PSC, 'L')
    # 1. bodrum kolonları (BPK1 / BPK2 / BMK1): 2. bodrum döşeme altından ayrı ayrı PÇ'ye
    BL = {'BPK1': None,
          'BPK2': [PK2, (12940.0, PK2[1]), (12940.0, py1 + 20), (12965.0, py1 + 20), (12965.0, py1)],
          'BMK1': [MK1, (12925.0, MK1[1]), (12925.0, py1 + 14), (12950.0, py1 + 14), (12950.0, py1)]}
    for nm, p in BK.items():
        cad.KOLON(p, 4, PS); node(p, nm)
        if BL[nm]:
            pipe(BL[nm], PS, 'P'); node(BL[nm][-1], 'PÇ')
    T((PK1[0] + 8, PK1[1] + 10), 'BPK1 Ø100 → PÇ (DOĞRUDAN)', 5.5, PSC, 'L')
    T((12948.0, 10450.0), 'BPK2 Ø100 DÖŞEME ALTI %2 → PÇ', 5.5, PSC, 'L', 90)
    T((12917.0, 10600.0), 'BMK1 Ø70 DÖŞEME ALTI %2 → PÇ', 5.5, PSC, 'R', 90)
    # pompa basma hattı (PÇ -> zemin kotu -> R2)
    pipe([(px1 - 25, py0 + 30), (px1 - 25, PR[1]), PR], 'MTY-PIS SU-BASMA', 'T', w=1.8)
    node((px1 - 25, py0 + 30), 'PÇ'); node(PR, 'PR')
    cad.KOLON(PR, 4, 'MTY-PIS SU-BASMA')
    T((PR[0] + 8, PR[1] - 14), 'BASMA Ø63 ↑ (R2)', 5.5, PSC, 'L')
    pop()


# ================================================================== ALTYAPI (TEMEL) PLANI
R_KOT = {'R1': (-0.30, -1.00), 'R2': (-0.30, -0.90), 'PB': (-0.25, -1.30)}


def bina_hatti():
    xs_, ys_ = [], []
    for pg in COLS():
        x0, y0, x1, y1 = pg.bounds
        xs_ += [x0, x1]; ys_ += [y0, y1]
    return min(xs_) - 10, min(ys_) - 10, max(xs_) + 10, max(ys_) + 10


def temel():
    """ALTYAPI PLANI (zemin kotu): kolon dipleri zeminde biter, zemin kotundan ayrı ayrı bina dışındaki R1'e (cazibe);
    pompa basma hattı ayrı R2'ye; R1 ve R2 ayrı hatlarla parsel bacasına. Yağmur suyu altyapısı yoktur."""
    push(MOVE(dx('T'), 0.0))
    for pg in COLS():
        x0, y0, x1, y1 = pg.bounds
        PL(list(pg.exterior.coords), gp.ARC_K, True, 1.5)
        L((x0, y0), (x1, y1), gp.ARC_K); L((x0, y1), (x1, y0), gp.ARC_K)
    bx0, by0, bx1, by1 = bina_hatti()
    PL([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], 'MTY-BINA-HATTI', True)
    T((bx0 + 10, by1 + 12), 'BİNA DIŞ HATTI', 7, gp.ARC_K, 'L')
    T((12090.0, 11640.0), 'ALTYAPI PLANI: MİMARİ PROJEDEN YALNIZCA BETONARME KOLONLAR ALINMIŞTIR. KOLON DİPLERİ ZEMİN KOTUNDADIR.', 7, YZ, 'L')
    # rögarlar (bina dışı)
    for nm, p, lbl, side in (('R1', R1, 'R1 60x60 (ZEMİN KOLONLARI)', 'R'), ('R2', R2, 'R2 60x60 (POMPA BASMA)', 'L'),
                             ('PB', PB, 'PB 60x60 (PARSEL BACASI)', 'B')):
        cad.ROGAR_PLAN(p, 30, 'MTY-ROGAR')
        if side == 'B':
            tx, ty, al = p[0], p[1] - 44, 'C'
        else:
            tx, ty, al = (p[0] - 40 if side == 'R' else p[0] + 40), p[1] + 5, side
        T((tx, ty), lbl, 8, 'MTY-ROGAR', al)
        T((tx, ty - 13), 'K.Ü. %+.2f / A.K. %+.2f' % R_KOT[nm], 7, 'MTY-ROGAR', al)
    # kolon dipleri (zemin kotu) -> R1 : her kolon ayrı, cazibe
    inl = {'MK1': 12935.0, 'PK2': 12950.0, 'PK1': 12970.0}
    for nm, p, x, d in (('MK1', MK1, 12918.0, 70), ('PK2', PK2, 12934.0, 100), ('PK1', PK1, 13005.0, 100)):
        pts = [p, (x, p[1]), (x, 9790.0), (inl[nm], R1[1] + 30)]
        pipe(pts, PS, 'T'); node(pts[-1], 'R1')
        gp.kolon_pis(p, nm, (-70 if nm != 'PK1' else 50, 40), k=0.6 if d == 100 else 0.5)
        TEMIZLEME_KAPAGI((p[0], p[1] - 14), 0.8)
        lx = {'MK1': 12912.0, 'PK2': 12928.0, 'PK1': 12999.0}[nm]
        ly = {'MK1': 10380.0, 'PK2': 10380.0, 'PK1': 9840.0}[nm]
        T((lx, ly), '%s Ø%d %%2 (%d SB) → R1' % (nm, d, 2 * {'PK1': SB_B1, 'PK2': SB_B2, 'MK1': SB_M}[nm]), 6.0, PSC, 'L', 90)
    # pompa basma hattı -> R2 (zemin hatlarına bağlanmaz)
    pts = [PR, (PR[0], 9790.0), (R2[0] - 10, R2[1] + 30)]
    pipe(pts, 'MTY-PIS SU-BASMA', 'T', w=1.8); node(PR, 'PR'); node(pts[-1], 'R2')
    cad.KOLON(PR, 5, 'MTY-PIS SU-BASMA')
    T((PR[0] + 8, 9840.0), 'POMPA BASMA Ø63 PE100 → R2', 6.0, PSC, 'L', 90)
    # R1 -> PB, R2 -> PB (ayrı hatlar), PB -> SASKİ
    pipe([(R1[0], R1[1] - 30), (PB[0], PB[1] + 30)], PS, 'T'); node((R1[0], R1[1] - 30), 'R1'); node((PB[0], PB[1] + 30), 'PB')
    T((R1[0] + 8, (R1[1] + PB[1]) / 2), 'L=%d / Ø150 / %%1' % (R1[1] - PB[1] - 60), 7, PSC, 'L', 90)
    pts = [(R2[0], R2[1] - 30), (R2[0], PB[1]), (PB[0] + 30, PB[1])]
    pipe(pts, PS, 'T'); node(pts[0], 'R2'); node(pts[-1], 'PB')
    T((R2[0] + 8, PB[1] + 40), 'Ø100 / %1', 7, PSC, 'L', 90)
    pipe([(PB[0] - 30, PB[1]), (PB[0] - 260, PB[1])], PS, 'T')
    node((PB[0] - 30, PB[1]), 'PB'); node((PB[0] - 260, PB[1]), 'SASKİ')
    ARROW((PB[0] - 275, PB[1]), 180, PS, 14)
    T((PB[0] - 260, PB[1] + 12), 'SASKİ ATIKSU HATTINA (KANAL KOTU SASKİ\'DEN ALINACAK)', 7, PSC, 'L')
    # temiz su: şebeke
    pipe([(12635.0, 9400.0), (12635.0, 9560.0)], CS, 'S'); node((12635.0, 9400.0), 'ŞEBEKE'); node((12635.0, 9560.0), 'NİŞ')
    T((12627.0, 9405.0), 'ŞEBEKE Ø32 → NİŞ', 6.5, TSC, 'L', 90)
    T((12090.0, 11690.0), 'ZEMİN VE 1. KAT KOLONLARI ZEMİN KOTUNDAN AYRI AYRI BİNA DIŞINDAKİ R1\'E, BODRUM GİDERLERİ PİS SU ÇUKURUNDAN '
      'POMPA İLE AYRI HATLA R2\'YE VERİLİR.', 6.5, PSC, 'L')
    pop()


# ================================================================== ÇATI
def cati():
    push(MOVE(dx('C'), 0.0))
    for nm, p, d in (('PK1', PK1, 100), ('PK2', PK2, 100), ('MK1', MK1, 70)):
        cad.KOLON(p, 6, PS); C(p, 10, PS)
        T((p[0] - 14, p[1] + 8), '%s HAVALIK Ø%d (ÇATIDAN 50 cm YUKARI)' % (nm, d), 6.5, PSC, 'R')
    for nm, p in YB_PTS.items():
        C(p, 6, YL); C(p, 3, YL)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (p[0] + 30, p[1] + (-40 if p[1] < 10000 else 40)), 0, 0.55, attrs={'K': nm})
    PL([(12087.0, 9776.0), (13142.0, 9776.0), (13142.0, 11521.0), (12087.0, 11521.0)], YL, True, 1.5)
    T((12090.0, 9745.0), 'YAĞMUR OLUĞU (SAÇAK BOYUNCA) - 4 ADET Ø100 PVC YAĞMUR İNİŞİ', 8, YC, 'L')
    T((12090.0, 11660.0), 'KULLANMA SUYU DEPOSU 2. BODRUM KATTADIR (HİDROFORLU) - ÇATIDA DEPO YOKTUR.', 7, YZ, 'L')
    pop()


def yb_plan(k='1', off=8.0):
    """yağmur inişinin kat planındaki yeri: mimari çatı planındaki iniş noktasına en yakın cephe / balkon / kolon yüzü,
    boru yüzeye bitişik (off cm dışarıda). Böylece iniş havada durmaz, binaya yaslanır."""
    from shapely.geometry import LineString as _LS, Point as _Pt
    from shapely.ops import nearest_points
    src = SRC[k]
    W = (WIN[0] + src - 20, 9700.0, WIN[2] + src + 20, 11600.0)
    gs = []
    for r in FLAT:
        if r[1] not in ('YLZ-DUVAR', 'YLZ-KORKULUK', 'YLZ-PENCERE', 'YLZ-KOLON', 'YLZ-BETON-KESİT', 'A-YALITIM PERDE'):
            continue
        if r[0] not in ('P', 'L'):
            continue
        pts = list(r[2])
        if len(pts) < 2 or not all(W[0] <= x <= W[2] and W[1] <= y <= W[3] for x, y in pts):
            continue
        gs.append(_LS([(x - src, y) for x, y in pts]))
    out = {}
    for nm, p in YB_PTS.items():
        P_ = _Pt(p)
        g = min(gs, key=lambda q: q.distance(P_))
        q = nearest_points(g, P_)[0]
        d = max(1e-6, q.distance(P_))
        out[nm] = (q.x + (p[0] - q.x) / d * off, q.y + (p[1] - q.y) / d * off)
    return out


def yagmur_kat(k):
    push(MOVE(dx(k), 0.0))
    for nm, p in yb_plan().items():
        C(p, 6, YL); C(p, 3, YL)
        node(p, nm)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (p[0] + 30, p[1] + (-40 if p[1] < 10000 else 40)), 0, 0.55, attrs={'K': nm})
        T((p[0] + 48, p[1] + (-44 if p[1] < 10000 else 36)), 'Ø100', 6.5, YC, 'L')
    pop()


def build_sihhi():
    for k in ('B2', 'B1', 'Z', '1', 'C'):
        floor_arch(k)
        frame_title(k, 0.0)
    frame_title('T', 0.0)
    bodrum2(); bodrum1(); zemin(); kat1()
    temel(); cati()
    for k in ('Z', '1'):          # yağmur inişleri zemin katta biter (bodrumlara ve temele inmez)
        yagmur_kat(k)


# ================================================================== YERDEN ISITMA (3 daire)
T_HOL = GH.T_HOL
ROOMS = [
    dict(name='SALON', ti=22, A=28.29, rects=[(12160, 10737, 12571, 11337)],
         ext=[('K', 4.11, [(2.5, 2.5, 1, 'BK')]), ('B', 6.00, [(2.0, 2.2, 1, 'ÇP')])], int=[]),
    dict(name='MUTFAK', ti=20, A=13.87, rects=[(12615, 10854, 12974, 11228)],
         ext=[('K', 3.59, [(1.5, 2.5, 1, 'BK')]), ('D', 3.74, [])], int=[]),
    dict(name='ODA', ti=20, A=10.44, rects=[(12255, 10402, 12571, 10701)],
         ext=[('B', 3.00, [(1.5, 1.6, 1, 'ÇP')])], int=[]),
    dict(name='YATAK ODASI 1', ti=20, A=10.22, rects=[(12255, 10099, 12599, 10393)],
         ext=[('B', 2.94, [(1.5, 1.6, 1, 'ÇP')])], int=[('İDA', 3.44, GH.T_ASANSOR, None)]),
    dict(name='YATAK ODASI 2', ti=20, A=13.34, rects=[(12745, 10309, 13074, 10703)],
         ext=[('D', 3.94, [(1.5, 1.6, 1, 'ÇP')])], int=[]),
    dict(name='BANYO', ti=26, A=5.41, rects=[(12785, 10114, 13074, 10293)],
         ext=[('D', 1.79, [(0.5, 0.75, 1, 'ÇP')])], int=[('İDM', 2.89, T_HOL, None)]),
    dict(name='BANYO-WC', ti=26, A=2.89, rects=[(12745, 10719, 12974, 10838)],
         ext=[('D', 1.19, [(0.5, 0.75, 1, 'ÇP')])], int=[]),
    dict(name='HOL', ti=18, A=9.46, rects=[(12615, 10114, 12735, 10838)],
         ext=[], int=[('İDM', 1.70, T_HOL, (1.0, 2.2))]),
]
DOORS = {'SALON': (12590, 10780, 'E'), 'MUTFAK': (12660, 10854, 'S'), 'ODA': (12590, 10470, 'E'),
         'YATAK ODASI 1': (12599, 10350, 'E'), 'YATAK ODASI 2': (12745, 10650, 'W'), 'BANYO': (12785, 10245, 'W'),
         'BANYO-WC': (12745, 10770, 'W')}
KOLL = (12615.0, 10548.0)
HKIND = {'B1': 'zemin', 'Z': 'ara', '1': 'ust'}
HDN = {'B1': 'DAİRE 1', 'Z': 'DAİRE 2', '1': 'DAİRE 3'}


def heat_calc(k):
    return [GH.calc_room(R, HKIND[k]) for R in ROOMS]


def _circuits(calc):
    circ = []
    for R in ROOMS:
        if R['name'] == 'HOL':
            continue
        res = [c for c in calc if c['name'] == R['name']][0]
        q = res['Q'] / R['A']
        sp = 10.0 if q > 75 or R['ti'] >= 24 else 15.0
        dxd, dyd, wall = DOORS[R['name']]
        parts = []
        for rc in R['rects']:
            x0, y0, x1, y1 = rc
            est = (x1 - x0 - 20) * (y1 - y0 - 20) / sp / 100.0
            m = max(1, math.ceil(est / 60.0))
            for j in range(m):
                if wall in 'NS':
                    parts.append((x0 + (x1 - x0) * j / m, y0, x0 + (x1 - x0) * (j + 1) / m, y1))
                else:
                    parts.append((x0, y0 + (y1 - y0) * j / m, x1, y0 + (y1 - y0) * (j + 1) / m))
        parts.sort(key=lambda r: math.hypot((r[0] + r[2]) / 2 - dxd, (r[1] + r[3]) / 2 - dyd))
        for j, p_ in enumerate(parts):
            Ar = (p_[2] - p_[0]) * (p_[3] - p_[1]) / 1e4
            circ.append(dict(room=R['name'], rect=p_, Ar=Ar, ti=R['ti'], Qroom=res['Q'], Aroom=R['A'], s=sp,
                             door=(dxd, dyd, wall), npart=len(parts), ipart=j))
    for c in circ:
        same = [x for x in circ if x['room'] == c['room']]
        c['W'] = c['Qroom'] * c['Ar'] / sum(x['Ar'] for x in same)
    return circ


def _poly_and_corner(c):
    x0, y0, x1, y1 = c['rect']
    band = 12.0 * (c['npart'] - 1) if c['npart'] > 1 else 0.0
    dxd, dyd, wall = c['door']
    r = [x0 + 10, y0 + 10, x1 - 10, y1 - 10]
    if wall == 'S': r[1] += band
    if wall == 'N': r[3] -= band
    if wall == 'W': r[0] += band
    if wall == 'E': r[2] -= band
    cs = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
    cand = {'S': (0, 1), 'N': (3, 2), 'W': (0, 3), 'E': (1, 2)}[wall]
    ci = min(cand, key=lambda j: math.hypot(cs[j][0] - dxd, cs[j][1] - dyd))
    return tuple(r), ci, cs[ci]


def _order(circ):
    ky = KOLL[1] + 60
    north = [c for c in circ if c['door'][1] > ky]
    south = [c for c in circ if c['door'][1] <= ky]
    rk = {'E': 0, 'S': 1, 'N': 1, 'W': 2}
    north.sort(key=lambda c: (rk[c['door'][2]], -c['door'][1] if c['door'][2] == 'W' else 0, c['ipart']))
    sw = sorted([c for c in south if c['door'][2] == 'E'], key=lambda c: (-c['door'][1], c['ipart']))
    se = sorted([c for c in south if c['door'][2] != 'E'], key=lambda c: (c['door'][1], c['ipart']))
    lanes = north + sw + se
    n = len(lanes)
    # port: güney grubu alttan yukarı, kuzey grubu üstten aşağı
    ns = len(sw + se)
    for i, c in enumerate(sw + se):
        c['pidx'] = i
    for i, c in enumerate(north):
        c['pidx'] = n - 1 - i
    for i, c in enumerate(lanes):
        c['lane'] = i
    return lanes


def _legs(c, port, corner, off):
    dxd, dyd, wall = c['door']
    xl = 12634.0 + 7.0 * c['lane'] + off
    ys, xs_ = c.get('yslot', c['ipart']), c.get('xslot', c['ipart'])
    yd = (dyd + 5.0 + 6.0 * ys + off) if wall == 'S' else (dyd - 6.0 * (c['npart'] - 1) / 2.0 + 6.0 * ys + off)
    pts = [port, (xl, port[1]), (xl, yd)]
    if wall in 'EW':
        xin = dxd + (1 if wall == 'W' else -1) * (5.0 + 6.0 * xs_ + (off if wall == 'W' else -off) + 2.5)
        pts.append((xin, yd))
    last = pts[-1]
    if abs(last[0] - corner[0]) > 0.1 and abs(last[1] - corner[1]) > 0.1:
        pts.append((corner[0], last[1]) if wall in 'NS' else (last[0], corner[1]))
    pts.append(corner)
    return pts


_PLAN_CACHE = {}


def _count_x(paths):
    gs = [LineString(p) for p in paths]
    n = 0
    for i in range(len(gs)):
        for j in range(i + 1, len(gs)):
            if gs[i].distance(gs[j]) > 0.4:
                continue
            it = gs[i].buffer(0.3).intersection(gs[j])
            if it.is_empty:
                continue
            parts = list(it.geoms) if hasattr(it, 'geoms') else [it]
            n += sum(10 if p.length > 2 else 1 for p in parts)
    return n


def _optimize(circ, ports, spir):
    """oda bazında şerit / kapı ofseti / duvar bandı sıralarını kesişme sayısı en az olacak şekilde seç"""
    import itertools

    def build():
        out = []
        for c in circ:
            full = spir[id(c)]
            pa, pb = ports[c['pidx']]
            la = _legs(c, pa, full[0], -2.5); lb = _legs(c, pb, full[-1], 2.5)
            out.append(la[:-1] + full + list(reversed(lb))[1:])
        return out
    for c in circ:
        c['yslot'] = c['ipart']; c['xslot'] = c['ipart']
    best = _count_x(build())
    rooms = []
    for c in circ:
        if c['npart'] > 1 and c['room'] not in rooms:
            rooms.append(c['room'])
    for _ in range(2):
        for rm in rooms:
            cs = [c for c in circ if c['room'] == rm]
            lanes0 = [(c['lane'], c['pidx']) for c in cs]
            cur = ([c['lane'] for c in cs], [c['pidx'] for c in cs], [c['yslot'] for c in cs], [c['xslot'] for c in cs])
            for lp in itertools.permutations(range(len(cs))):
                for yp in itertools.permutations(range(len(cs))):
                    for xp in itertools.permutations(range(len(cs))):
                        for c, li, yi, xi in zip(cs, lp, yp, xp):
                            c['lane'], c['pidx'] = lanes0[li]
                            c['yslot'], c['xslot'] = yi, xi
                        v = _count_x(build())
                        if v < best:
                            best = v
                            cur = ([c['lane'] for c in cs], [c['pidx'] for c in cs], [c['yslot'] for c in cs], [c['xslot'] for c in cs])
            for c, a, b, y_, x_ in zip(cs, *cur):
                c['lane'], c['pidx'], c['yslot'], c['xslot'] = a, b, y_, x_
    return best


def heat_floor(k):
    calc = heat_calc(k)
    push(MOVE(dx(k), HDY))
    circ = _order(_circuits(calc))
    n = len(circ)
    kx, ky = KOLL
    RECT(kx, ky, kx + 10, ky + 12 + n * 10, 'MTY-KOLLETOR')
    ports = [((kx + 10, ky + 8 + i * 10), (kx + 10, ky + 12 + i * 10)) for i in range(n)]
    for a_, b_ in ports:
        C(a_, 1.2, 'MTY-KOLLETOR'); C(b_, 1.2, 'MTY-KOLLETOR')
    T((kx - 4, ky + 20), 'KOLLEKTÖR DOLABI %d AĞIZLI' % n, 6.5, 'MTY-KOLLETOR', 'R', 90) if False else \
        T((kx - 6, ky - 4), 'KOLLEKTÖR DOLABI %d AĞIZLI' % n, 6.5, 'MTY-KOLLETOR', 'R')
    spir = {}
    for c in circ:
        r, ci, corner = _poly_and_corner(c)
        poly = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
        spir[id(c)] = GH.spiral3.bifilar(poly, ci, 'a', c['s'])[0]
    key = tuple((c['room'], c['ipart']) for c in circ)
    if key in _PLAN_CACHE:
        for c, v in zip(circ, _PLAN_CACHE[key][0]):
            c['lane'], c['pidx'], c['yslot'], c['xslot'] = v
    else:
        nx_ = _optimize(circ, ports, spir)
        _PLAN_CACHE[key] = ([(c['lane'], c['pidx'], c['yslot'], c['xslot']) for c in circ], nx_)
        print('ısıtma kesişme (en az):', nx_)
    for c in circ:
        full = spir[id(c)]
        pa, pb = ports[c['pidx']]
        la = _legs(c, pa, full[0], -2.5)
        lb = _legs(c, pb, full[-1], 2.5)
        path = la[:-1] + full + list(reversed(lb))[1:]
        pipe(path, gp.PEX, 'H')
        node(path[0], 'KOLL'); node(path[-1], 'KOLL')
        c['L'] = LineString(path).length / 100.0
        c['port'] = c['pidx'] + 1
        c['path'] = path
    zb = {'B1': 'B', 'Z': 'Z', '1': '1'}[k]
    for c in circ:
        c['zone'] = '%s%02d' % (zb, [R['name'] for R in ROOMS].index(c['room']) + 1)
    # etiketler: kullanıcının MTY-RADYATOR MAHAL ve MTY-ETIKET blokları (çerçeveli, altındaki borular maskeli - boru kesilmez)
    from shapely.geometry import box as _bx
    w0, w1 = cad.P((kx - 40, ky - 20)), cad.P((kx + 30, ky + 22 + n * 10))
    taken = [_bx(w0[0], w0[1], w1[0], w1[1])]
    hol = [x for x in calc if x['name'] == 'HOL'][0]
    for R in ROOMS:
        rc = R['rects'][0]
        cs_ = [c for c in circ if c['room'] == R['name']]
        if R['name'] == 'HOL':
            gp.mahal_etiket('HOL', '%s%02d' % (zb, 8), R['ti'], hol['Q'], R['A'], rc, taken, extra='(BAĞL. BORULARI)',
                            prefer=((rc[0] + rc[2]) / 2, rc[3] - 120))
        elif cs_:
            gp.mahal_etiket(R['name'], cs_[0]['zone'], R['ti'], cs_[0]['Qroom'], R['A'], rc, taken, prefer=(rc[0] + 40, rc[3] - 40))
    for c in circ:
        gp.devre_etiket(c, c['rect'], taken, k=5.0 if (c['rect'][3] - c['rect'][1]) < 160 or (c['rect'][2] - c['rect'][0]) < 160 else 6.0)
    # kombi -> kollektör (gidiş/dönüş): kombi nişi -> mutfak kuzey duvarı -> hol batı duvarı
    km = F_K['KM']
    hg0, hd0 = km.cp('HG'), km.cp('HD')
    top = ky + 12 + n * 10
    hg = [hg0, (12950.0, hg0[1]), (12950.0, 11236.0), (12623.0, 11236.0), (12623.0, top)]
    hd = [hd0, (12946.0, hd0[1]), (12946.0, 11240.0), (12619.0, 11240.0), (12619.0, top)]
    mtyblk.insert('KOMBI1', km.o, km.rot, 1.0)
    pipe(hg, gp.HGL, 'HG'); pipe(hd, gp.HDL, 'HD')
    for p_ in (hg[0], hg[-1], hd[0], hd[-1]):
        node(p_, 'KOMBI-KOLL')
    Qd = sum(c['W'] for c in circ) + hol['Q']
    T((12780.0, 11140.0), '%d W - DN20 PEX (KOMBİ - KOLLEKTÖR G/D)' % round(Qd), 6.5, gp.HCAP, 'L')
    pop()
    return {'a': (circ, calc)}


# ================================================================== PAFTALAR
import gsheet as GS
import gheatsheet as HS
from gsheet import dline, wl
SX0 = 6 * SLOT + 100.0
OY = 9150.0
SB_UP = lambda base: (lambda i: [0, 0, 2 * base, base][i])
P = dict(
    floors=[('B2', '2. BODRUM -6,00'), ('B1', '1. BODRUM -3,00'), ('Z', 'ZEMİN ±0,00'), ('1', '1. KAT +3,00')],
    roof_name='ÇATI +6,00', sema_w=3400.0,
    supply=dict(depo='bodrum', V=3.0, vnote='3 BAĞIMSIZ BÖLÜM ≤ 10 → 3 m³', ybt=3 * YB_D,
                tasma='TAŞMA/BOŞALTMA → YER SÜZGECİ → PÇ', hidrofor=HID_TXT,
                units=[('D1', 'B1', 1, YB_D), ('D2', 'Z', 1, YB_D), ('D3', '1', 1, YB_D)]),
    groups=[dict(x=520, pkx=680, mkx=2120, kombi=2620, bkeys=['LV', 'DUS', 'WC', 'CM', 'YS'], mkeys=['EV', 'BM'],
                 extra=[dict(kx=1500, keys=['LV', 'WC', 'YS'])], ikeys=[],
                 units={'B1': ('D1', 'daire'), 'Z': ('D2', 'daire'), '1': ('D3', 'daire')},
                 kolons=[('PK1', 680, 100, SB_UP(SB_B1)), ('PK2', 1500, 100, SB_UP(SB_B2)), ('MK1', 2120, 70, SB_UP(SB_M))],
                 bottom={'PK1': lambda yf: yf[2] - 91.0, 'PK2': lambda yf: yf[2] - 85.0, 'MK1': lambda yf: yf[2] - 79.0})],
    yagmur=dict(names=list(YB_PTS), P=ROOF_A, dn=100, foot={'YB1': 2, 'YB2': 2, 'YB3': 2, 'YB4': 2}, tasma_to=None, notes=[]),
)


def sema_ek(yf):
    """zemin ve 1. kat kolonları zemin kotundan ayrı ayrı bina dışındaki R1'e; 1. bodrum kolonları 2. bodrum döşeme altından PÇ'ye;
    pompa basma hattı ayrı R2'ye (zemin hatlarına bağlanmaz). PÇ'ye havalık yoktur. Hiçbir hat üst üste binmez."""
    xs = lambda d: SX0 + d
    r1 = (xs(2900), yf[2] - 60)
    cad.ROGAR_PLAN(r1, 24, 'MTY-ROGAR')
    T((r1[0] - 24, r1[1] + 30), 'R1 (BİNA DIŞI)', 9, 'MTY-ROGAR', 'L')
    T((r1[0] - 24, r1[1] - 36), 'A.K. -1,00', 7, 'MTY-ROGAR', 'L')
    # kolon dipleri (zemin döşemesi altı = zemin kotu) -> R1 : üstteki hat önce yukarı döner, hiçbir hat kesişmez
    for nm, xk, yb, xt, yu in (('MK1', 2120, -79.0, 2530, -54.0), ('PK2', 1500, -85.0, 2542, -60.0), ('PK1', 680, -91.0, 2554, -66.0)):
        wl([(xs(xk), yf[2] + yb), (xs(xt), yf[2] + yb), (xs(xt), yf[2] + yu), (r1[0] - 24, yf[2] + yu)], PS)
    T((xs(700), yf[2] - 104), 'PK1 / PK2 / MK1 → R1 : ZEMİN KOTUNDAN AYRI AYRI CAZİBE İLE (%2) - KOLONLAR BODRUMA İNMEZ', 6.5, PSC, 'L')
    # R1 -> PB -> SASKİ (sağa)
    pb = (xs(3100), r1[1])
    cad.ROGAR_PLAN(pb, 24, 'MTY-ROGAR')
    wl([(r1[0] + 24, r1[1]), (pb[0] - 24, pb[1])], PS)
    T((pb[0] - 24, pb[1] + 30), 'PB', 10, 'MTY-ROGAR', 'L')
    wl([(pb[0] + 24, pb[1]), (pb[0] + 70, pb[1])], PS)
    ARROW((pb[0] + 80, pb[1]), 0, PS, 10)
    T((pb[0] + 30, pb[1] - 36), 'SASKİ %1', 7, 'MTY-ROGAR', 'L')
    T((r1[0] + 30, r1[1] + 6), 'Ø150 %d SB' % (3 * SB_D + 2), 6, PSC, 'L')
    # pis su çukuru (havalık yok)
    px = xs(2880)
    py0 = yf[0] - 130
    RECT(px - 100, py0, px + 100, yf[0], PSC)
    T((px - 100, py0 - 14), 'PİS SU ÇUKURU (PÇ) - 2 x DALGIÇ POMPA', 7.5, PSC, 'L')
    for i, s_ in enumerate(PUMP_TXT):
        T((px - 100, py0 - 26 - i * 10), s_, 6, PSC, 'L')
    DALGIC_POMPA((px - 40, py0 + 10), 1.3, 'MTY-CIHAZ'); DALGIC_POMPA((px + 10, py0 + 10), 1.3, 'MTY-CIHAZ')
    # 1. bodrum kolonları (BPK1 / BPK2 / BMK1) -> 2. bodrum döşeme altından PÇ : sol kolon en alt hat ve ilk döner
    for i, (nm, xk) in enumerate((('BPK1', 680), ('BPK2', 1500), ('BMK1', 2120))):
        x = xs(xk)
        yl = yf[1] - 130 + 10 * i
        xt = px - 60 + 25 * i
        wl([(x + 4, yf[1] - 74), (x + 4, yl), (xt, yl), (xt, yf[0])], PS)
        T((x + 12, yf[1] - 120), nm, 7, PSC, 'L')
    T((xs(700), yf[1] - 150), '1. BODRUM KOLONLARI (BPK1 / BPK2 / BMK1) 2. BODRUM DÖŞEME ALTINDAN AYRI AYRI PİS SU ÇUKURUNA', 6.5, PSC, 'L')
    # depo odası yer süzgeci -> PÇ (döşeme altı)
    yd = yf[0] - 45
    wl([(xs(382), yd), (px - 100, yd)], PS)
    T((xs(400), yd - 12), 'DEPO ODASI YER SÜZGECİ → PÇ (DÖŞEME ALTI)', 6.5, PSC, 'L')
    # pompa basma hattı -> zemin kotu -> R2 (bina dışı) -> PB  (zemin kolon hatlarına bağlanmaz)
    xb = px + 90
    r2 = (xb, yf[2] - 150)
    wl([(xb, py0 + 30), (xb, r2[1] - 24)], 'MTY-PIS SU-BASMA')
    CEKVALF((xb, yf[0] + 40), 0.8, 90); VANA((xb, yf[0] + 70), 0.7, 90)
    T((xb + 8, yf[0] + 90), 'BASMA Ø63 PE100', 6.5, PSC, 'L', 90)
    cad.ROGAR_PLAN(r2, 24, 'MTY-ROGAR')
    T((r2[0] - 24, r2[1] - 36), 'R2 (POMPA BASMA, BİNA DIŞI)', 7, 'MTY-ROGAR', 'L')
    wl([(r2[0] + 24, r2[1]), (pb[0], r2[1]), (pb[0], pb[1] - 24)], PS)
    T((pb[0] + 6, r2[1] + 8), 'R2 → PB Ø100 %1', 6.5, PSC, 'L')


NOTES = [
    'Temiz su tesisatı PPRC PN20 borularla yapılacak, sıcak su boruları izolasyonlu olarak döşenecektir.',
    'Şebeke suyu bina girişindeki ana sayaç nişinden DBK kolonu ile 2. bodrum kattaki 3,00 m³ kullanma suyu deposuna verilecektir.',
    'Depo 2. bodrumda olduğundan kullanma suyu 2 pompalı (1+1) frekans konvertörlü paket hidrofor ile basınçlandırılacaktır.',
    'Hidrofordan çıkan ADK kolonu bina girişindeki (zemin kat holü) sayaç grubuna bağlanacak; her daire ayrı sayaçtan beslenecektir.',
    'Sayaçlardan önce DN x 10, sonra DN x 5 düz boru bırakılacak; her daire girişinde küresel vana ve çek valf konulacaktır.',
    'Depo şamandıralı vana, sinekli havalık, taşma, boşaltma ve seviye göstergeli olacak; taşma ve boşaltma hava boşluklu olarak yer süzgecine verilecektir.',
    'Sıcak kullanma suyu her dairede mimari kombi nişindeki duvar tipi hermetik yoğuşmalı kombiden sağlanacaktır.',
    'Pis su tesisatı TS EN 1451 PVC borularla yapılacak; bina içi yatay hatlar en az %2, bacalar arası hatlar %1 eğimle döşenecektir.',
    'Mutfak ve banyo/WC giderleri birbirine bağlanmayacak; her mahal kendi kolonuna (PK1 büyük banyo, PK2 küçük banyo, MK1 mutfak) bağlanacaktır.',
    'Zemin ve 1. kat pis su kolonları zemin katta sonlanacak; kolon diplerinden zemin kotunda birleştirilmeden ayrı ayrı %2 eğimle bina dışındaki R1 muayene bacasına cazibe ile bağlanacaktır.',
    '1. bodrum ıslak hacimleri üst katlardaki gibi kendi kolonlarına (BPK1, BPK2, BMK1) bağlanacak; bu kolonlar 2. bodrum döşeme altından ayrı ayrı pis su çukuruna verilecektir.',
    'Pis su çukurundaki dalgıç pompanın basma hattı zemin kolon hatlarına bağlanmadan ayrı olarak R2 muayene bacasına, R2 de ayrı hatla parsel bacasına bağlanacaktır.',
    'Pis su çukuru sızdırmaz ve kapaklı olacak; pompalar şamandıralı otomatik çalışacak, seviye alarmı konulacaktır.',
    'Pompa basma hattına çek valf ve küresel vana konulacak, basma hattı R2\'ye üstten bağlanacaktır.',
    'Pis su kolonları çatıdan en az 50 cm yukarı çıkarılacak, uçlarına havalık şapkası takılacaktır.',
    'Parsel bacası ve SASKİ kanal kotu SASKİ\'den alınacak; plandaki kotlar yaklaşık olup sahada teyit edilecektir.',
    'Hiçbir boru betonarme kolon içinden geçirilmeyecek; döşeme ve perde geçişleri kılıflı yapılacaktır.',
    'Yağmur suları pis su hattına bağlanmayacak; yağmur iniş boruları cepheye kelepçeyle tespit edilecek ve zemin kotunda bırakılacaktır (yağmur suyu altyapısı bu proje kapsamında değildir).',
    'Yerden ısıtma devreleri PEX 16x2,0 oksijen bariyerli borularla karşı akışlı salyangoz düzende, devre boyunca eksiz döşenecektir.',
    'Yerden ısıtma devre boyları (bağlantı boruları dahil) 80 m\'yi geçmeyecek; devreler debimetreli kollektörde dengelenecektir.',
    'Temiz su hatlarına 10 bar, yerden ısıtma devrelerine şap öncesi 6 bar basınç testi yapılacaktır.',
    'Tüm imalat TS 1258, TS EN 806, TS EN 12056, TS EN 1264 ve TS 825 standartlarına uygun olarak yapılacaktır.',
]
ANTET = dict(proje="SİNEM TURHAN'A AİT 3 BAĞIMSIZ BÖLÜMLÜ MESKEN PROJESİ", konu='SIHHİ TESİSAT VE YERDEN ISITMA PROJESİ',
             rows=[('YAPININ ÖZELLİKLERİ', ''), ('YAPI SAHİBİ', 'SİNEM TURHAN'), ('YAPI CİNSİ', 'MESKEN / BETONARME (3B)'),
                   ('KAT ADEDİ', '2 BODRUM + ZEMİN + 1 KAT'), ('BAĞIMSIZ BÖLÜM', '3 DAİRE'),
                   ('ISITMA', '3 x 24 kW YOĞUŞMALI KOMBİ + YERDEN ISITMA'),
                   ('SU TEMİNİ', 'ŞEBEKE (SASKİ) + 3,00 m³ BODRUM DEPOSU + HİDROFOR'), ('KOTLAR', '±0,00 = +102,55'),
                   ('ARSANIN ÖZELLİKLERİ', ''), ('İLİ / İLÇESİ', 'SAKARYA / SERDİVAN'), ('MAHALLE', 'SERDİVAN'),
                   ('PAFTA / PARSEL', '28J1 / 13748'), ('TOPLAM İNŞAAT ALANI', '549,69 m²')])
HFLOORS = [('B1', '1. BODRUM', 'DAİRE 1'), ('Z', 'ZEMİN', 'DAİRE 2'), ('1', '1. KAT', 'DAİRE 3')]


def build_sheets(HEAT):
    yf, ytk = GS.sihhi_sema(SX0, OY, P)
    sema_ek(yf)
    h, yw = GS.yagmur_sema(SX0 + 3470, OY, P)
    ax = -3900.0
    GS.antet(ax, 11650.0, ANTET)
    GS.notlar(ax + 1800, 11650.0, NOTES)
    GS.lejant(ax, 10650.0, extra=[
        (lambda p: wl([(p[0] - 30, p[1]), (p[0] + 30, p[1])], 'MTY-PIS SU-BASMA'), 'PİS SU POMPA BASMA HATTI (PE100)'),
        (lambda p: DALGIC_POMPA((p[0], p[1] - 10), 0.8, 'MTY-CIHAZ'), 'DALGIÇ PİS SU POMPASI'),
        (lambda p: (RECT(p[0] - 25, p[1] - 12, p[0] + 25, p[1] + 12, gp.HID), POMPA((p[0] - 8, p[1]), 7, 0, gp.HID)), 'HİDROFOR')])
    FR = []
    for k in ('T', 'B2', 'B1', 'Z', '1', 'C'):
        x0 = SLOTS[k] * SLOT
        FR.append(((x0, FY0, x0 + SLOT, FY1), NAMES[k], '1/50'))
    FR.append(((SX0 - 50, OY - 20, SX0 + 3420, OY + 2580), 'SIHHİ TESİSAT KOLON ŞEMASI', 'ÖLÇEKSİZ'))
    FR.append(((SX0 + 3420, OY - 20, SX0 + 3470 + yw + 60, OY + 2580), 'YAĞMUR SUYU ŞEMASI VE HESABI', 'ÖLÇEKSİZ'))
    FR.append(((ax - 50, FY0, -40.0, FY1), 'ANTET, NOTLAR VE LEJANT', 'ÖLÇEKSİZ'))
    HN = {'B1': '1. BODRUM KAT YERDEN ISITMA PLANI', 'Z': 'ZEMİN KAT YERDEN ISITMA PLANI', '1': '1. KAT YERDEN ISITMA PLANI'}
    for k in ('B1', 'Z', '1'):
        x0 = SLOTS[k] * SLOT
        FR.append(((x0, FY0 + HDY, x0 + SLOT, FY1 + HDY), HN[k], '1/50'))
    hy = FY0 + HDY + 50
    HS.isitma_sema(SX0, hy, HEAT, HFLOORS)
    FR.append(((SX0 - 50, FY0 + HDY, SX0 + 3750, FY1 + HDY), 'YERDEN ISITMA KOLON ŞEMASI', 'ÖLÇEKSİZ'))
    tx = SX0 + 3800
    yy = HS.isitma_tablo(tx, FY1 + HDY - 80, HEAT, HFLOORS)
    HS.u_tablo(tx, yy - 20)
    FR.append(((tx - 30, FY0 + HDY, tx + 900, FY1 + HDY), 'ISITMA HESAP ÇİZELGELERİ', 'ÖLÇEKSİZ'))
    for (a, b, c, d), t, o in FR:
        GS.frame(a, b, c, d, t, o)
    return FR, h



gp.EXTRA_LAYERS['MTY-BINA-HATTI'] = (8, 'DASHED')


gp.EXTRA_LAYERS['MTY-PIS SU-BASMA'] = (6, 'BASMA HATTI')
gp.WIDTH['MTY-PIS SU-BASMA'] = 1.8


def run_check():
    cols = []
    base = COLS()
    for k in ('T', 'B2', 'B1', 'Z', '1'):
        for c in base:
            cols.append(affinity.translate(c, dx(k), 0))
    rep = gp.check(cols)
    print('KONTROL', len(rep))
    for r in rep[:60]:
        print('  ', r)
    return rep


if __name__ == '__main__':
    build_sihhi()
    for k, sub in (('B1', '1. BODRUM KAT YERDEN ISITMA PLANI'), ('Z', 'ZEMİN KAT YERDEN ISITMA PLANI'), ('1', '1. KAT YERDEN ISITMA PLANI')):
        floor_arch(k, HDY, furn=False)
        frame_title(k, HDY, sub)
    HEAT = {k: heat_floor(k) for k in ('B1', 'Z', '1')}
    for k, v in HEAT.items():
        circ, calc = v['a']
        print(k, round(sum(c['W'] for c in circ)), [(c['room'][:6], c['port'], round(c['W']), round(c['L'], 1), c['s']) for c in circ])
    FR, YH = build_sheets(HEAT)
    print('yağmur', YH)
    run_check()
    import xcheck
    rep = xcheck.crossings()
    print('köprü', xcheck.hops(rep), 'çakışık', [r for r in xcheck.summary(rep) if r[0] == 'ÇAKIŞIK'])
    print('yazı maskesi (boru kesilmez)', xcheck.wipe_texts())
    print('üst üste binen çizgi temizlendi', xcheck.dedupe())
    pickle.dump((cad.R, FR, cad.BLK), open('/tmp/claude-0/p2/st_R.pkl', 'wb'))
    pickle.dump(dict(HEAT=HEAT, ROOMS=ROOMS, ROOF_A=ROOF_A, NYB=len(YB_PTS), Q_PIS=Q_PIS, H_PIS=H_PIS, Q_HID=Q_HID, H_HID=H_HID,
                     SB_D=SB_D, YB_D=YB_D), open('/tmp/claude-0/p2/st_calc.pkl', 'wb'))
