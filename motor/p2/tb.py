"""TUNCAY BULUT - 3 katlı iş yeri + mesken (zemin: 2 iş yeri, 1-2. kat: 2'şer daire). Sıhhi tesisat planları.
Koordinatlar: 'bina çerçevesi' = mimari zemin kat planı kaynak koordinatı (cm). 1. kat kaynağı +3295, 2. kat +6590, çatı +9885.
"""
import math, pickle, sys
from shapely.geometry import LineString
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import cad
from cad import L, PL, C, T, RECT, ARC, ARROW, SOL, push, pop, MOVE, VANA, CEKVALF, SAYAC, PISLIK_TUTUCU, TEMIZLEME_KAPAGI, HEXTAG
import mtyblk
import gp
from gp import CS, CH, PS, PST, TSC, PSC, YBL, VN, CD, YZ, YL, YC, pipe, node, Fix, cap_temiz, cap_pis, fmt, dn_temiz, dn_sb

FLAT = pickle.load(open('/tmp/claude-0/p2/tb.dxf.flat.pkl', 'rb'))
SRC = {'Z': 0.0, '1': 3295.0, '2': 6590.0, 'C': 9885.0}
WIN = (5380.0, 15560.0, 8020.0, 16360.0)          # bina çerçevesi (zemin)
WIN_C = (5240.0, 15500.0, 8170.0, 16420.0)
BX0 = 5418.0
SLOT = 3400.0
# pafta: altyapı (temel) planı solda, sonra zemin, 1. kat, 2. kat, çatı
SLOTS = {'T': 0, 'Z': 1, '1': 2, '2': 3, 'C': 4}
SY = {'S': 0.0, 'H': -1500.0}                  # sıhhi sıra / ısıtma sırası (y kaydırma)
NAMES = {'T': 'ALTYAPI (TEMEL) PLANI', 'Z': 'ZEMİN KAT SIHHİ TESİSAT PLANI', '1': '1. KAT SIHHİ TESİSAT PLANI',
         '2': '2. KAT SIHHİ TESİSAT PLANI', 'C': 'ÇATI PLANI (SU DEPOSU / HAVALIKLAR / YAĞMUR)'}
KOT = {'T': '-1,70 TEMEL ALT', 'Z': '±0,00 [33,30]  İŞ YERİ SBS +0,20', '1': '+4,00 (SBS +3,50)', '2': '+7,00 (SBS +6,50)', 'C': '+10,00 ÇATI'}


def dx(slot):
    return SLOTS[slot] * SLOT - BX0 + 400.0


def COLS():
    return gp.columns(FLAT, (5400, 15580, 8000, 16340))


# ================================================================== armatürler (bina çerçevesi)
F_Z = {
    'WC2': Fix('WC', (6225.0, 15607.0), 0, name='WC2'), 'LV2': Fix('LV', (6300.0, 15712.0), 90, name='LV2'),
    'WC1': Fix('WC', (6870.0, 15607.0), 0, name='WC1'), 'LV1': Fix('LV', (6796.0, 15712.0), -90, name='LV1'),
    'YS2': Fix('YS', (6262.0, 15660.0), 0, name='YS2'), 'YS1': Fix('YS', (6905.0, 15668.0), 0, name='YS1'),
}
F_K = {   # 1. ve 2. kat aynı
    # D-1 / D-3 (batı)
    'WCa': Fix('WC', (6033.0, 15607.0), 0, name='WCa'), 'DUSa': Fix('DUS', (6170.0, 15645.0), 90, name='DUSa'),
    'LVa': Fix('LV', (6170.0, 15804.0), 90, name='LVa'), 'CMa': Fix('CM', (6170.0, 15719.0), 90, name='CMa'),
    'YSa': Fix('YS', (6090.0, 15682.0), 0, name='YSa'),
    'EVa': Fix('EV', (6415.0, 15987.0), 0, name='EVa'), 'BMa': Fix('BM', (6352.0, 15987.0), 0, name='BMa'),
    'KMa': Fix('KOMBI', (6158.0, 16205.0), 90, name='KMa'),
    # D-2 / D-4 (doğu)
    'WCb': Fix('WC', (6938.0, 15607.0), 0, name='WCb'), 'LVb': Fix('LV', (7050.0, 15607.0), 0, name='LVb'),
    'DUSb': Fix('DUS', (6950.0, 15745.0), 180, name='DUSb'), 'CMb': Fix('CM', (7160.0, 15607.0), 0, name='CMb'),
    'YSb': Fix('YS', (7000.0, 15690.0), 0, name='YSb'),
    'EVb': Fix('EV', (7346.0, 15924.0), -90, name='EVb'), 'BMb': Fix('BM', (7346.0, 15868.0), -90, name='BMb'),
    'KMb': Fix('KOMBI', (7343.0, 16168.0), -90, name='KMb'),
}
PK1 = (6062.0, 15626.0)     # D-1/D-3 banyo kolonu (zeminde iş yeri-2 WC hacmine iner)
PK2 = (6970.0, 15624.0)     # D-2/D-4 banyo kolonu (zeminde iş yeri-1 WC hacmine iner)
MK1 = (6480.0, 16010.0)     # D-1/D-3 mutfak kolonu (betonarme kolon yanında, kutu içinde)
MK2 = (7358.0, 16046.0)     # D-2/D-4 mutfak kolonu (betonarme kolon yanında, kutu içinde)
# temiz su kolonları (kat holü KB köşesi, asansör duvarı önü) - zemin sayaç grubundan
RZ = {'ADK': (6338.0, 15758.0), 'D1': (6350.0, 15758.0), 'D2': (6362.0, 15758.0), 'D3': (6374.0, 15758.0),
      'D4': (6386.0, 15758.0), 'DBK': (6398.0, 15758.0)}
SAYAC_X = 6338.0
SAY_Y = {'İ2': 15640.0, 'İ1': 15652.0, 'D4': 15664.0, 'D3': 15676.0, 'D2': 15688.0, 'D1': 15700.0}
ANA_NIS = (6560.0, 15560.0)    # bina girişi ana sayaç nişi (ön cephe)
DEPO = (6398.0, 15849.0, 6538.0, 15999.0)   # mimari çatı planındaki 3 m³ depo (bina çerçevesi)

YB_D = 4.5     # daire: WC .5 + LV .5 + DUŞ 1 + ÇM 1 + EV .5 + BM 1
YB_DS = 2.0    # sıcak: LV .5 + DUŞ 1 + EV .5
YB_I = 1.0     # iş yeri: WC .5 + LV .5
SB_BANYO = gp.SB['WC'] + gp.SB['DUS'] + gp.SB['LV'] + gp.SB['CM'] + gp.SB['YS']    # 25
SB_MUTFAK = gp.SB['EV'] + gp.SB['BM']                                              # 8
SB_DAIRE = SB_BANYO + SB_MUTFAK                                                   # 33
SB_IS = gp.SB['WC'] + gp.SB['LV'] + gp.SB['YS']                                    # 14

KOMBI_SPEC = ['DUVAR TİPİ HERMETİK YOĞUŞMALI KOMBİ (HER DAİREYE 1 ADET) 24 kW',
              'SICAK SU: 11,5 l/dk (ΔT=30 K) - BACA Ø60/100 DIŞ CEPHEYE',
              'YERDEN ISITMA: GİDİŞ/DÖNÜŞ 45/35 °C (KOMBİ DÜŞÜK SICAKLIK AYARLI)']


# ================================================================== çizim yardımcıları
def floor_arch(k, sy=0.0, furn=True):
    push(MOVE(dx(k) - SRC[k], sy))
    w = WIN_C if k == 'C' else WIN
    gp.copy_arch(FLAT, (w[0] + SRC[k], w[1], w[2] + SRC[k], w[3]), furn=furn, room_labels=(sy == 0.0))
    pop()
    push(MOVE(dx(k), sy))
    gp.hatch_cols([c for c in gp.columns(FLAT, (5400 + SRC[k], 15580, 8000 + SRC[k], 16340))]) if False else None
    pop()


def frame_title(k, sy, sub=None):
    gp.title((dx(k) + 6700.0, 15190.0 + sy), NAMES[k] if sy == 0 else sub, 'ÖLÇEK : 1/50   KOT: ' + KOT[k])


# ================================================================== ZEMİN KAT
def zemin():
    push(MOVE(dx('Z'), 0.0))
    for f in F_Z.values():
        f.draw()
    # ---- pis su (döşeme altı, temel dolgusu içinde) -> kolon diplerine (temizleme kapaklı) -> temel altı
    w2, l2, y2 = F_Z['WC2'].cp('PS'), F_Z['LV2'].cp('PS'), F_Z['YS2'].cp('PS')
    pipe([w2, (PK1[0] + 20, w2[1]), PK1], PS, 'P')
    pipe([l2, (l2[0], 15675.0), y2], PS, 'P')
    pipe([y2, (y2[0], 15648.0), (PK1[0] + 22, 15648.0), PK1], PS, 'P')
    w1, l1, y1 = F_Z['WC1'].cp('PS'), F_Z['LV1'].cp('PS'), F_Z['YS1'].cp('PS')
    pipe([w1, (PK2[0] - 12, w1[1]), PK2], PS, 'P')
    pipe([l1, (l1[0], 15648.0), (PK2[0], 15648.0), PK2], PS, 'P')
    pipe([y1, (y1[0], 15660.0), (l1[0], 15660.0)], PS, 'P')
    cap_pis((6140.0, 15627.0), 0, '10 SB', 'Ø100'); cap_pis((6285.0, 15690.0), 90, '2 SB', 'Ø50')
    cap_pis((6845.0, 15627.0), 0, '10 SB', 'Ø100'); cap_pis((6860.0, 15660.0), 0, '2 SB', 'Ø50')
    for p, nm, sb in ((PK1, 'PK1', 2 * SB_DAIRE + SB_IS), (PK2, 'PK2', 2 * SB_DAIRE + SB_IS)):
        gp.kolon_pis(p, nm, (-60 if nm == 'PK1' else 60, -95))
        T((p[0] + (-58 if nm == 'PK1' else 62), p[1] - 112), 'Ø100 / %d SB' % sb, 7, PSC, 'L')
    T((6000.0, 15480.0), 'İŞ YERİ PİS SULARI DÖŞEME ALTINDAN PK1 / PK2 KOLON DİPLERİNE BAĞLANIR (TEMEL ALTI HATLAR ALTYAPI PLANINDA)', 7, PSC, 'L')
    # ---- temiz su: şebeke -> ana sayaç nişi -> DBK (çatı deposuna)
    nx, ny = ANA_NIS
    RECT(nx - 30, ny - 14, nx + 30, ny + 6, VN)
    T((nx, ny - 26), 'ANA SAYAÇ NİŞİ (SASKİ)', 7, VN, 'C')
    pipe([(nx - 45, 15380.0), (nx - 45, ny - 4), (nx - 20, ny - 4)], CS, 'S')
    VANA((nx - 45, 15420.0), 0.5, 90)
    PISLIK_TUTUCU((nx - 10, ny - 4), 0.45, 0); SAYAC((nx + 4, ny - 4), 0.6, 0); CEKVALF((nx + 18, ny - 4), 0.45, 0)
    pipe([(nx - 20, ny - 4), (nx + 26, ny - 4), (nx + 26, 15620.0), (6430.0, 15620.0), (6430.0, 15746.0),
          (RZ['DBK'][0], 15746.0), RZ['DBK']], CS, 'S')
    node((nx - 45, 15380.0), 'ŞEBEKE')
    T((nx - 52, 15390.0), 'ŞEBEKEDEN (SASKİ) Ø32', 7, TSC, 'R', 90)
    cap_temiz((6470.0, 15620.0), 0, so='DBK 15 YB', socp='Ø32')
    # ---- sayaç grubu (bina girişi - kat holü batı duvarı): ADK -> kollektör -> 6 sayaç
    RECT(SAYAC_X - 8, 15628.0, SAYAC_X + 28, 15712.0, VN)
    T((SAYAC_X + 34, 15705.0), 'SAYAÇ GRUBU (BİNA GİRİŞİ)', 7, VN, 'L')
    T((SAYAC_X + 34, 15694.0), '6 ADET SAYAÇ + KÜRESEL VANA + ÇEK VALF', 5.5, VN, 'L')
    pipe([RZ['ADK'], (SAYAC_X, SAY_Y['İ2'])], CS, 'S')
    for nm, yy in SAY_Y.items():
        mtyblk.insert('MTY-SU SAYACI', (SAYAC_X + 8, yy), 0, 0.28)
        T((SAYAC_X - 4, yy - 2), nm, 5, VN, 'R')
    # daire kolonlarına
    for i, d in enumerate(('D1', 'D2', 'D3', 'D4')):
        yy = SAY_Y[d]
        pipe([(SAYAC_X, yy), (RZ[d][0], yy), RZ[d]], CS, 'S')
    # iş yerleri
    l2so, w2so = F_Z['LV2'].cp('SO'), F_Z['WC2'].cp('SO')
    pipe([(SAYAC_X, SAY_Y['İ2']), (l2so[0], SAY_Y['İ2']), l2so], CS, 'S')
    pipe([(l2so[0], SAY_Y['İ2']), (l2so[0], 15602.0), (w2so[0], 15602.0), w2so], CS, 'S')
    l1so, w1so = F_Z['LV1'].cp('SO'), F_Z['WC1'].cp('SO')
    pipe([(SAYAC_X, SAY_Y['İ1']), (SAYAC_X + 14, SAY_Y['İ1']), (SAYAC_X + 14, 15626.0), (6700.0, 15626.0),
          (6700.0, l1so[1]), l1so], CS, 'S')
    pipe([(6700.0, 15626.0), (6802.0, 15626.0), (6802.0, 15602.0), (w1so[0], 15602.0), w1so], CS, 'S')
    cap_temiz((6250.0, 15712.0), 0, so='İ2 %s YB' % fmt(YB_I), socp='Ø20')
    cap_temiz((6620.0, 15620.0), 0, so='İ1 %s YB' % fmt(YB_I), socp='Ø20')
    for nm, p in RZ.items():
        gp.kolon_temiz(p)
        node(p, nm)
    T((6338.0, 15800.0), 'TEMİZ SU KOLONLARI: DBK Ø32 / ADK Ø32 / D1-D4 Ø25 (KOLON KUTUSU İÇİNDE)', 5.5, TSC, 'L')
    T((5450.0, 15520.0), 'İŞ YERİ LAVABOLARINA TEZGAH ALTI 10 L ELEKTRİKLİ SU ISITICI KONACAKTIR.', 6, CD, 'L')
    pop()


# ================================================================== NORMAL KAT (1. ve 2. kat)
def normal_kat(k):
    fi = 1 if k == '1' else 2
    da, db = (1, 2) if fi == 1 else (3, 4)
    push(MOVE(dx(k), 0.0))
    F = F_K
    for f in F.values():
        f.draw()
    # ---------------- pis su: D-a (batı) -> PK1
    wc, ds, lv, cm, ys = (F[n].cp('PS') for n in ('WCa', 'DUSa', 'LVa', 'CMa', 'YSa'))
    pipe([wc, (PK1[0] - 12, wc[1]), PK1], PS, 'P')
    pipe([lv, (6150.0, lv[1]), (6150.0, cm[1]), cm], PS, 'P')
    pipe([cm, (6150.0, cm[1]), (6150.0, 15700.0), (PK1[0] + 12, 15700.0), (PK1[0], 15688.0), PK1], PS, 'P')
    pipe([ys, (PK1[0] + 14, ys[1]), (PK1[0], 15668.0)], PS, 'P')
    pipe([ds, (PK1[0] + 22, ds[1]), (PK1[0], 15630.0)], PS, 'P')
    ev, bm = F['EVa'].cp('PS'), F['BMa'].cp('PS')
    pipe([bm, (bm[0], 16014.0), (MK1[0] - 12, 16014.0), MK1], PS, 'P')
    pipe([ev, (ev[0], 16014.0)], PS, 'P')
    # ---------------- pis su: D-b (doğu) -> PK2 (banyo içinde, WC ile lavabo arası)
    wc, ds, lv, cm, ys = (F[n].cp('PS') for n in ('WCb', 'DUSb', 'LVb', 'CMb', 'YSb'))
    pipe([wc, (PK2[0] - 14, wc[1]), PK2], PS, 'P')
    pipe([cm, (cm[0], 15648.0), (lv[0], 15648.0)], PS, 'P')
    pipe([lv, (lv[0], 15648.0), (PK2[0] + 14, 15648.0), PK2], PS, 'P')
    pipe([ds, (ds[0], 15690.0), ys], PS, 'P')
    pipe([ys, (ys[0], 15660.0), (PK2[0] + 6, 15660.0), PK2], PS, 'P')
    ev, bm = F['EVb'].cp('PS'), F['BMb'].cp('PS')
    pipe([bm, (7372.0, bm[1]), (7372.0, MK2[1] - 12), MK2], PS, 'P')
    pipe([ev, (7372.0, ev[1])], PS, 'P')
    kp = 5.0
    cap_pis((6045.0, 15640.0), 0, '10 SB', 'Ø100', kp); cap_pis((6115.0, 15645.0), 0, '7 SB', 'Ø50', kp)
    cap_pis((6100.0, 15700.0), 0, '6 SB', 'Ø50', kp); cap_pis((6150.0, 15770.0), 90, '2 SB', 'Ø50', kp)
    cap_pis((6075.0, 15682.0), 0, '2 SB', 'Ø50', kp)
    cap_pis((6385.0, 16014.0), 0, '4 SB', 'Ø50', kp); cap_pis((6450.0, 16014.0), 0, '8 SB', 'Ø50', kp)
    cap_pis((6945.0, 15640.0), 0, '10 SB', 'Ø100', kp); cap_pis((7110.0, 15648.0), 0, '4 SB', 'Ø50', kp)
    cap_pis((7020.0, 15648.0), 0, '6 SB', 'Ø50', kp); cap_pis((6950.0, 15668.0), 90, '7 SB', 'Ø50', kp)
    cap_pis((6985.0, 15660.0), 0, '9 SB', 'Ø50', kp); cap_pis((7372.0, 15990.0), 90, '8 SB', 'Ø50', kp)
    for p, nm, sb, off in ((PK1, 'PK1', (3 - fi) * SB_BANYO, (-55, -90)), (PK2, 'PK2', (3 - fi) * SB_BANYO, (55, -90)),
                           (MK1, 'MK1', (3 - fi) * SB_MUTFAK, (40, 70)), (MK2, 'MK2', (3 - fi) * SB_MUTFAK, (70, 60))):
        gp.kolon_pis(p, nm, off, k=0.6 if nm[0] == 'P' else 0.5)
        T((p[0] + off[0] + 2, p[1] + off[1] - 17), 'Ø%d / %d SB' % (100 if nm[0] == 'P' else 70, sb), 7, PSC, 'L')
    # ---------------- temiz su: D-a
    ra, rb = RZ['D%d' % da], RZ['D%d' % db]
    # kolon (D1/D2 1. katta, D3/D4 2. katta biter) -> daire giriş vanası
    lva, cma, dsa, wca, eva, bma, kma = (F[n] for n in ('LVa', 'CMa', 'DUSa', 'WCa', 'EVa', 'BMa', 'KMa'))
    yA = 15765.0
    pipe([ra, (ra[0], yA), (6300.0, yA), (6176.0, yA)], CS, 'S')
    VANA((6315.0, yA), 0.4, 0)
    pipe([(6176.0, yA), (6176.0, cma.cp('SO')[1]), cma.cp('SO')], CS, 'S')
    pipe([(6176.0, yA), (6176.0, lva.cp('SO')[1]), lva.cp('SO')], CS, 'S')
    pipe([(6176.0, cma.cp('SO')[1]), (6176.0, dsa.cp('SO')[1]), dsa.cp('SO')], CS, 'S')
    pipe([(6176.0, lva.cp('SO')[1]), (6176.0, 15856.0), (5996.0, 15856.0), (5996.0, 15602.0), (wca.cp('SO')[0], 15602.0), wca.cp('SO')], CS, 'S')
    pipe([(6295.0, yA), (6295.0, 15980.0), (eva.cp('SO')[0], 15980.0), eva.cp('SO')], CS, 'S')
    pipe([(bma.cp('SO')[0], 15980.0), bma.cp('SO')], CS, 'S')
    ksa = kma.cp('SO')
    pipe([(6295.0, 15980.0), (6196.0, 15980.0), (6196.0, ksa[1]), ksa], CS, 'S')
    # sıcak (kombi -> mutfak -> banyo)
    sca = kma.cp('SC')
    pipe([sca, (6202.0, sca[1]), (6202.0, 15992.0), (eva.cp('SC')[0], 15992.0), eva.cp('SC')], CH, 'S')
    pipe([(6202.0, 15992.0), (6186.0, 15992.0), (6186.0, lva.cp('SC')[1]), lva.cp('SC')], CH, 'S')
    pipe([(6186.0, lva.cp('SC')[1]), (6186.0, dsa.cp('SC')[1]), dsa.cp('SC')], CH, 'S')
    # ---------------- temiz su: D-b
    lvb, cmb, dsb, wcb, evb, bmb, kmb = (F[n] for n in ('LVb', 'CMb', 'DUSb', 'WCb', 'EVb', 'BMb', 'KMb'))
    yB = 15770.0 + 4.0
    pipe([rb, (rb[0], yB), (6800.0, yB)], CS, 'S')
    VANA((6760.0, yB), 0.4, 0)
    pipe([(6800.0, yB), (6800.0, 15602.0), (wcb.cp('SO')[0], 15602.0), wcb.cp('SO')], CS, 'S')
    pipe([(wcb.cp('SO')[0], 15602.0), (lvb.cp('SO')[0], 15602.0), lvb.cp('SO')], CS, 'S')
    pipe([(lvb.cp('SO')[0], 15602.0), (cmb.cp('SO')[0], 15602.0), cmb.cp('SO')], CS, 'S')
    pipe([(6800.0, 15756.0), (dsb.cp('SO')[0], 15756.0), dsb.cp('SO')], CS, 'S')
    pipe([(6800.0, yB), (6800.0, 15890.0), (7341.0, 15890.0)], CS, 'S')
    pipe([(7341.0, 15890.0), (7341.0, bmb.cp('SO')[1]), bmb.cp('SO')], CS, 'S')
    pipe([(7341.0, 15890.0), (7341.0, evb.cp('SO')[1]), evb.cp('SO')], CS, 'S')
    ksb = kmb.cp('SO')
    pipe([(7341.0, evb.cp('SO')[1]), (7341.0, 15990.0), (7384.0, 15990.0), (7384.0, ksb[1]), ksb], CS, 'S')
    scb = kmb.cp('SC')
    pipe([scb, (7390.0, scb[1]), (7390.0, 15984.0), (7336.0, 15984.0), (7336.0, evb.cp('SC')[1]), evb.cp('SC')], CH, 'S')
    pipe([(7336.0, evb.cp('SC')[1]), (7336.0, 15896.0), (6806.0, 15896.0), (6806.0, 15762.0),
          (dsb.cp('SC')[0], 15762.0), dsb.cp('SC')], CH, 'S')
    pipe([(6806.0, 15762.0), (6806.0, 15608.0), (lvb.cp('SC')[0], 15608.0), lvb.cp('SC')], CH, 'S')
    # ---------------- çap etiketleri
    k5 = 5.0
    cap_temiz((6240.0, yA), 0, so='D%d %s YB' % (da, fmt(YB_D)), socp='Ø%d' % dn_temiz(YB_D), k=k5)
    cap_temiz((6600.0, yB), 0, so='D%d %s YB' % (db, fmt(YB_D)), socp='Ø%d' % dn_temiz(YB_D), k=k5)
    cap_temiz((6176.0, 15815.0), 90, so='1.5 YB', socp='Ø20', k=k5)
    cap_temiz((6186.0, 15930.0), 90, sc='1.5 YB', sccp='Ø20', k=k5)
    cap_temiz((6250.0, 15980.0), 0, so='3.0 YB', socp='Ø25', k=k5)
    cap_temiz((7000.0, 15890.0), 0, so='1.5 YB', socp='Ø20', k=k5)
    cap_temiz((7120.0, 15896.0), 0, sc='1.5 YB', sccp='Ø20', k=k5)
    cap_temiz((6880.0, 15602.0), 0, so='2.5 YB', socp='Ø25', k=k5)
    # geçen kolonlar
    for nm, p in RZ.items():
        if nm in ('DBK', 'ADK') or (fi == 1) or nm in ('D3', 'D4'):
            gp.kolon_temiz(p)
            node(p, nm)
    # kombi bilgileri
    for i, s in enumerate(KOMBI_SPEC):
        T((5460.0, 16300.0 - i * 10.0), s, 6, CD, 'L')
    T((5460.0, 16312.0), 'KOMBİ (D-%d / D-%d)' % (da, db), 8, CD, 'L')
    pop()


def build_sihhi():
    for k, sub in (('Z', 'ZEMİN KAT İŞ YERLERİ KLİMA PLANI'), ('1', '1. KAT YERDEN ISITMA PLANI'), ('2', '2. KAT YERDEN ISITMA PLANI')):
        floor_arch(k, HDY, furn=False)
        frame_title(k, HDY, sub)
    for k in ('Z', '1', '2', 'C'):
        floor_arch(k)
        frame_title(k, 0.0)
    frame_title('T', 0.0)
    zemin()
    normal_kat('1')
    normal_kat('2')


def build_rest():
    temel()
    cati()
    for k in ('Z', '1', '2'):
        yagmur_kat(k)


# ================================================================== ALTYAPI (TEMEL) PLANI - solda
R_ = {'R1': (6062.0, 15420.0), 'R2': (6560.0, 15420.0), 'R3': (6812.0, 15420.0), 'R4': (7358.0, 15420.0), 'PB': (7700.0, 15330.0)}
R_KOT = {'R1': (-0.80, -1.30), 'R2': (-0.85, -1.35), 'R3': (-0.88, -1.38), 'R4': (-0.93, -1.44), 'PB': (-1.00, -1.50)}   # (kapak altı kot, akış kotu)
YB_PTS = {'YB1': (5398.0, 15572.0), 'YB2': (7280.0, 15572.0), 'YB3': (8008.0, 15572.0),
          'YB4': (5430.0, 16348.0), 'YB5': (6700.0, 16348.0), 'YB6': (7975.0, 16348.0)}
ROOF_A = 28.10 * 8.60


def temel():
    push(MOVE(dx('T'), 0.0))
    for pg in COLS():
        x0, y0, x1, y1 = pg.bounds
        PL(list(pg.exterior.coords), gp.ARC_K, True, 1.5)
        L((x0, y0), (x1, y1), gp.ARC_K); L((x0, y1), (x1, y0), gp.ARC_K)
    T((5420.0, 16420.0), 'TEMEL PLANI: MİMARİ PROJEDEN YALNIZCA BETONARME KOLONLAR ALINMIŞTIR (TEMEL ÜST KOTU -1,70 ALTI YAPI DIŞI).', 8, YZ, 'L')
    for nm, p in R_.items():
        cad.ROGAR_PLAN(p, 25 if nm != 'PB' else 30, 'MTY-ROGAR')
        T((p[0] - 30, p[1] - 45), '%s  50x50' % nm if nm != 'PB' else 'PB (PARSEL BACASI) 60x60', 8, 'MTY-ROGAR', 'L')
        T((p[0] - 30, p[1] - 57), 'K.Ü. %+.2f / A.K. %+.2f' % R_KOT[nm], 7, 'MTY-ROGAR', 'L')
    segs = [('PK1', [PK1, (PK1[0], R_['R1'][1] + 25)], 2 * SB_BANYO + SB_IS, 100),
            ('MK1', [MK1, (MK1[0], 16060.0), (6560.0, 16060.0), (6560.0, R_['R2'][1] + 25)], 2 * SB_MUTFAK, 70),
            ('PK2', [PK2, (PK2[0], R_['R3'][1] + 25)], 2 * SB_BANYO + SB_IS, 100),
            ('MK2', [MK2, (MK2[0], R_['R4'][1] + 25)], 2 * SB_MUTFAK, 70)]
    for nm, pts, sb, d in segs:
        pipe(pts, PS, 'T'); node(pts[-1], 'R')
        TEMIZLEME_KAPAGI((pts[0][0], pts[0][1] - 15), 0.9)
        gp.kolon_pis(pts[0], nm, (45, 30), k=0.6 if d == 100 else 0.5)
        mid = ((pts[-2][0] + pts[-1][0]) / 2, (pts[-2][1] + pts[-1][1]) / 2) if len(pts) > 2 else (pts[0][0], (pts[0][1] + pts[1][1]) / 2)
        T((pts[0][0] + 14, (pts[0][1] + pts[1][1]) / 2), 'L=%d / Q=%d / %%2' % (abs(pts[0][1] - pts[1][1]), max(d, 100)), 7, PSC, 'L', 90)
    chain = [('R1', 'R2', 2 * SB_BANYO + SB_IS), ('R2', 'R3', 2 * SB_DAIRE + SB_IS), ('R3', 'R4', 2 * SB_DAIRE + 2 * SB_BANYO + 2 * SB_IS),
             ('R4', 'PB', 4 * SB_DAIRE + 2 * SB_IS)]
    for a, b, sb in chain:
        pa, pb_ = R_[a], R_[b]
        pts = [(pa[0] + 25, pa[1]), (pb_[0] - 30, pa[1])] if b != 'PB' else [(pa[0] + 25, pa[1]), (pb_[0], pa[1]), (pb_[0], pb_[1] + 30)]
        pipe(pts, PS, 'T'); node(pts[0], 'R'); node(pts[-1], 'R')
        ln = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts[:-1], pts[1:]))
        T(((pa[0] + pb_[0]) / 2 - 40, pa[1] + 8), 'L=%d / Q=150 / %%1 (%d SB)' % (ln, sb), 7.5, PSC, 'L')
    pipe([(R_['PB'][0] + 30, R_['PB'][1]), (R_['PB'][0] + 160, R_['PB'][1])], PS, 'T')
    node((R_['PB'][0] + 30, R_['PB'][1]), 'PB'); node((R_['PB'][0] + 160, R_['PB'][1]), 'SASKİ')
    ARROW((R_['PB'][0] + 175, R_['PB'][1]), 0, PS, 14)
    T((R_['PB'][0] + 40, R_['PB'][1] + 12), 'SASKİ ATIKSU HATTINA (KANAL KOTU SASKİ\'DEN ALINACAK)', 7.5, PSC, 'L')
    for nm, p in YB_PTS.items():
        C(p, 6, YL); C(p, 3, YL)
        d = -1 if p[1] < 16000 else 1
        pipe([p, (p[0], p[1] + d * 60)], YL, 'Y')
        node(p, nm); node((p[0], p[1] + d * 60), nm + '-KANAL')
        ARROW((p[0], p[1] + d * 72), 90 * d, YL, 12)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (p[0] + 30, p[1] + d * 40), 0, 0.55, attrs={'K': nm})
        T((p[0] + 8, p[1] + d * 95), 'YAĞMUR SUYU KANALINA GİDER', 6.5, YC, 'L')
    T((5420.0, 15240.0), 'BİNA PİS SULARI KOLON DİPLERİNDEN (TEMİZLEME KAPAKLI) EN YAKIN MUAYENE BACASINA, BACALAR ARASI %1 EĞİMLE PARSEL BACASINA BAĞLANIR.', 8, PSC, 'L')
    pop()


# ================================================================== ÇATI PLANI
def cati():
    push(MOVE(dx('C'), 0.0))
    x0, y0, x1, y1 = DEPO
    T(((x0 + x1) / 2, y1 + 40), 'KULLANMA SUYU DEPOSU 3,00 m³ (MİMARİ ÇATI PLANINDAKİ YERİNDE)', 8, YZ, 'C')
    T(((x0 + x1) / 2, (y0 + y1) / 2), 'V=3,00 m³', 10, 'RAST-TEM-SU DEPOSU', 'MC')
    db, ad = RZ['DBK'], RZ['ADK']
    pipe([db, (db[0], 15975.0), (x0, 15975.0)], CS, 'S')
    pipe([ad, (ad[0], 15870.0), (x0, 15870.0)], CS, 'S')
    node((x0, 15975.0), 'DEPO'); node((x0, 15870.0), 'DEPO')
    cad.SAMANDIRALI_VANA((x0 + 4, 15975.0), 0.6)
    mtyblk.insert('MTY-KURESEL VANA', (x0 - 20, 15870.0), 0, 0.4)
    gp.kolon_temiz(db); gp.kolon_temiz(ad); node(db, 'DBK'); node(ad, 'ADK')
    cap_temiz((6360.0, 15975.0), 0, so='DBK', socp='Ø32'); cap_temiz((6370.0, 15870.0), 0, so='ADK 15 YB', socp='Ø32')
    # taşma + boşaltma -> YB5
    yb = YB_PTS['YB5']
    pipe([(x1, 15990.0), (yb[0], 15990.0), (yb[0], yb[1] - 6)], CS, 'X')
    pipe([(x1, 15860.0), (x1 + 15, 15860.0), (x1 + 15, 15990.0)], CS, 'X')
    node((x1, 15990.0), 'DEPO'); node((x1, 15860.0), 'DEPO'); node((yb[0], yb[1] - 6), 'YB5')
    mtyblk.insert('MTY-KURESEL VANA', (x1 + 15, 15920.0), 90, 0.4)
    T((yb[0] - 8, 16200.0), 'TAŞMA Ø40 + BOŞALTMA Ø32 → YB5 YAĞMUR İNİŞİNE', 6.5, TSC, 'L', 90)
    for nm, p in (('PK1', PK1), ('PK2', PK2), ('MK1', MK1), ('MK2', MK2)):
        cad.KOLON(p, 6, PS); C(p, 10, PS)
        T((p[0] + 12, p[1] + 8), '%s HAVALIK Ø%d (ÇATIDAN 50 cm YUKARI)' % (nm, 100 if nm[0] == 'P' else 70), 6.5, PSC, 'L')
    for nm, p in YB_PTS.items():
        C(p, 6, YL); C(p, 3, YL)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (p[0] + 30, p[1] + (-40 if p[1] < 16000 else 40)), 0, 0.55, attrs={'K': nm})
    # oluk (saçak boyunca)
    ox0, oy0, ox1, oy1 = 5370.0, 15540.0, 8155.0, 16378.0
    PL([(ox0, oy0), (ox1, oy0), (ox1, oy1), (ox0, oy1)], YL, True, 1.5)
    T((ox0 + 300, oy0 - 18), 'YAĞMUR OLUĞU (SAÇAK BOYUNCA) - 6 ADET Ø100 PVC YAĞMUR İNİŞİ', 8, YC, 'L')
    pop()


# ================================================================== YAĞMUR İNİŞLERİ (kat planları)
def yagmur_kat(k):
    push(MOVE(dx(k), 0.0))
    for nm, p in YB_PTS.items():
        C(p, 6, YL); C(p, 3, YL)
        node(p, nm)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (p[0] + 30, p[1] + (-40 if p[1] < 16000 else 40)), 0, 0.55, attrs={'K': nm})
        T((p[0] + 48, p[1] + (-44 if p[1] < 16000 else 36)), 'Ø100', 6.5, YC, 'L')
    pop()



# ================================================================== ISITMA (yerden ısıtma - daireler)
import gheat as GH
HDY = -1700.0          # ısıtma paftaları (sıhhi sıranın altında)
T_HOL = GH.T_HOL
ROOMS = {   # ad: (ti, A mimari, boru bölgesi(ler) [duvar iç yüzü], dış duvarlar, iç (ısıtılmayan) sınırlar)
    'a': [
        dict(name='SALON', ti=22, A=19.38, rects=[(5448, 15995, 5918, 16295), (5918, 15995, 6147, 16150)],
             ext=[('K', 4.70, [(1.5, 1.6, 1, 'ÇP')]), ('K', 2.29, [(1.5, 2.5, 1, 'BK')]), ('B', 3.00, [])], int=[]),
        dict(name='MUTFAK', ti=20, A=9.48, rects=[(6181, 16000, 6511, 16265)],
             ext=[('K', 3.30, [(1.5, 1.6, 1, 'ÇP')])], int=[('İDM', 2.66, T_HOL, None)]),
        dict(name='YATAK ODASI', ti=20, A=10.84, rects=[(5448, 15617, 5705, 15965)],
             ext=[('G', 2.57, [(1.5, 1.6, 1, 'ÇP')]), ('B', 3.48, [])], int=[]),
        dict(name='ODA', ti=20, A=7.00, rects=[(5707, 15617, 5987, 15850)],
             ext=[('G', 2.80, [(1.5, 1.6, 1, 'ÇP')])], int=[]),
        dict(name='BANYO', ti=26, A=4.29, rects=[(6005, 15617, 6178, 15850)],
             ext=[('G', 1.73, [(0.5, 0.65, 1, 'ÇP')])], int=[]),
        dict(name='HOL', ti=18, A=9.17, rects=[(5796, 15860, 6185, 15975)],
             ext=[('G', 1.17, [])], int=[('İDM', 2.38, T_HOL, (1.0, 2.2)), ('İDA', 1.20, GH.T_ASANSOR, None)]),
    ],
    'b': [
        dict(name='SALON', ti=22, A=22.18, rects=[(7611, 15617, 7963, 15885), (7611, 15885, 7860, 16070)],
             ext=[('D', 2.68, [(1.5, 2.2, 1, 'ÇP')]), ('G', 4.89, [(1.5, 1.6, 1, 'ÇP')]), ('K', 3.77, []), ('D', 2.15, [])], int=[]),
        dict(name='MUTFAK', ti=20, A=8.93, rects=[(7350, 15725, 7595, 16085)],
             ext=[('K', 2.45, [(1.5, 2.5, 1, 'BK')])], int=[]),
        dict(name='YATAK ODASI', ti=20, A=9.76, rects=[(6793, 15900, 7075, 16225)],
             ext=[('K', 2.82, [(1.5, 1.6, 1, 'ÇP')])], int=[('İDM', 3.35, T_HOL, None)]),
        dict(name='ODA', ti=20, A=8.10, rects=[(7087, 15900, 7303, 16225)],
             ext=[('K', 2.16, [(1.5, 1.6, 1, 'ÇP')])], int=[]),
        dict(name='BANYO', ti=26, A=4.29, rects=[(6905, 15612, 7105, 15740)],
             ext=[('G', 2.00, [(0.5, 0.65, 1, 'ÇP')])], int=[]),
        dict(name='HOL', ti=18, A=11.86, rects=[(6800, 15760, 7180, 15875)],
             ext=[('G', 2.50, [])], int=[('İDM', 1.30, T_HOL, (1.0, 2.2))]),
    ]}


def heat_calc(fi):
    kind = 'ara' if fi == 1 else 'ust'
    return {side: [GH.calc_room(R, kind) for R in ROOMS[side]] for side in ('a', 'b')}


DOORS = {   # oda kapısı: (x, y, odanın hangi duvarı)
    'a': {'SALON': (5851, 15990, 'S'), 'MUTFAK': (6240, 15990, 'S'), 'YATAK ODASI': (5705, 15925, 'E'),
          'ODA': (5934, 15852, 'N'), 'BANYO': (6050, 15852, 'N')},
    'b': {'SALON': (7606, 15660, 'W'), 'MUTFAK': (7541, 15722, 'S'), 'YATAK ODASI': (7022, 15897, 'S'),
          'ODA': (7142, 15897, 'S'), 'BANYO': (7052, 15742, 'N')}}
KOLL = {'a': (6045.0, 15965.0, 'S'), 'b': (7195.0, 15862.0, 'S')}


def _circuits(side, calc):
    rooms = [R for R in ROOMS[side] if R['name'] != 'HOL']
    circ = []
    for R in rooms:
        res = [c for c in calc if c['name'] == R['name']][0]
        q = res['Q'] / R['A']
        sp = 10.0 if q > 75 or R['ti'] >= 24 else 15.0
        dxd, dyd, wall = DOORS[side][R['name']]
        parts = []
        for rc in R['rects']:
            ps_ = [rc]
            while True:
                big = max(ps_, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
                est = (big[2] - big[0] - 20) * (big[3] - big[1] - 20) / sp / 100.0 + 14.0
                if est <= 72.0:
                    break
                ps_.remove(big)
                x0, y0, x1, y1 = big
                if wall in 'NS':      # kapı duvarına dik kes (her parça kapı duvarına değsin)
                    xm = (x0 + x1) / 2; ps_ += [(x0, y0, xm, y1), (xm, y0, x1, y1)]
                else:
                    ym = (y0 + y1) / 2; ps_ += [(x0, y0, x1, ym), (x0, ym, x1, y1)]
            parts += ps_
        # kapıya yakın parça önce
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
    """boru bölgesi (10 cm duvar payı + kapı duvarında bağlantı bandı) ve giriş köşesi"""
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
    first = 'a' if ci in ((0,) if wall == 'S' else ()) else 'a'
    return tuple(r), ci, cs[ci]


def _inroom(c, pts, corner, off):
    """kapı noktasından oda içi bağlantı bandı ile giriş köşesine"""
    dxd, dyd, wall = c['door']
    last = pts[-1]
    if wall in 'NS':
        sgn = 1 if wall == 'S' else -1          # S duvarı: oda yukarıda
        yin = dyd + sgn * (5.0 + 6.0 * c['yslot'] + sgn * off)
        pts += [(last[0], yin), (corner[0], yin)]
    else:
        sgn = 1 if wall == 'W' else -1          # W duvarı: oda doğuda
        xin = dxd + sgn * (5.0 + 6.0 * c['xslot'] + sgn * off)
        pts += [(xin, last[1]), (xin, corner[1])]
    pts.append(corner)
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > 0.05 or abs(p[1] - out[-1][1]) > 0.05:
            out.append(p)
    return out


def _legs(side, port, corner, c, off):
    dxd, dyd, wall = c['door']
    w = 6.0 * (c['npart'] - 1) / 2.0
    pts = [port]
    if side == 'a':
        # kollektör hol kuzey duvarında (ağızlar güneye) -> hol şeridi (y 15950 aşağı) -> kapı
        yl = 15952.0 - 7.0 * c['lane'] + off
        pts.append((port[0], yl))
        if wall in 'NS':
            pts.append((dxd - w + 6.0 * c['xslot'] + off, yl))
        else:
            pts.append((dxd, yl))
        return _inroom(c, pts, corner, off)
    # b: kollektör hol kuzey duvarı (ağızlar güneye) -> hol şeridi (y 15845 aşağı) -> kapı / doğu koridoru
    yl = 15846.0 - 7.0 * c['lane'] + off
    pts.append((port[0], yl))
    if c['room'] in ('SALON', 'MUTFAK'):
        xc = 7300.0 + 6.0 * c['hlane'] + off
        ys = 15705.0 - 6.0 * c['slane'] + off
        pts += [(xc, yl), (xc, ys)]
        if wall in 'NS':
            pts.append((dxd - w + 6.0 * c['xslot'] + off, ys))
        else:
            pts.append((dxd, ys))
        return _inroom(c, pts, corner, off)
    if wall in 'NS':
        pts.append((dxd - w + 6.0 * c['xslot'] + off, yl))
    else:
        pts.append((dxd, yl))
    return _inroom(c, pts, corner, off)


import gufh
_TB_CACHE = {}


def heat_floor(k):
    fi = 1 if k == '1' else 2
    calc = heat_calc(fi)
    push(MOVE(dx(k), HDY))
    out = {}
    for side in ('a', 'b'):
        circ = _circuits(side, calc[side])
        n = len(circ)
        kx, ky, kd = KOLL[side]
        if kd == 'E':
            RECT(kx, ky, kx + 10, ky + 12 + n * 10, 'MTY-KOLLETOR')
            ports = [((kx + 10, ky + 8 + i * 10), (kx + 10, ky + 12 + i * 10)) for i in range(n)]
        else:
            RECT(kx, ky, kx + 12 + n * 10, ky + 10, 'MTY-KOLLETOR')
            ports = [((kx + 8 + i * 10, ky), (kx + 12 + i * 10, ky)) for i in range(n)]
        for a_, b_ in ports:
            C(a_, 1.2, 'MTY-KOLLETOR'); C(b_, 1.2, 'MTY-KOLLETOR')
        T((kx - 4 if kd == 'E' else kx, ky - 8 if kd == 'E' else ky + 16), 'KOLLEKTÖR DOLABI %d AĞIZLI' % n, 6.5, 'MTY-KOLLETOR',
          'R' if kd == 'E' else 'L')
        spir = {}
        for i, c in enumerate(circ):
            r, ci, corner = _poly_and_corner(c)
            poly = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
            spir[id(c)] = GH.spiral3.bifilar(poly, ci, 'a', c['s'])[0]
            c['lane'] = c['hlane'] = c['slane'] = c['pidx'] = i
            c['yslot'] = c['xslot'] = c['ipart']

        def build():
            out = []
            for c in circ:
                full = spir[id(c)]
                la = _legs(side, ports[c['pidx']][0], full[0], c, -2.5)
                lb = _legs(side, ports[c['pidx']][1], full[-1], c, 2.5)
                out.append(la[:-1] + full + list(reversed(lb))[1:])
            return out
        key = (side, tuple((c['room'], c['ipart']) for c in circ))
        if key in _TB_CACHE:
            for c, v in zip(circ, _TB_CACHE[key]):
                c['lane'], c['hlane'], c['slane'], c['pidx'], c['yslot'], c['xslot'] = v
        else:
            nx_ = gufh.optimize(circ, build, keys=('lane', 'hlane', 'slane', 'pidx'), iters=10, restarts=25)
            _TB_CACHE[key] = [(c['lane'], c['hlane'], c['slane'], c['pidx'], c['yslot'], c['xslot']) for c in circ]
            print('ısıtma kesişme', side, nx_)
        paths = build()
        for i, c in enumerate(circ):
            path = paths[i]
            pipe(path, gp.PEX, 'H')
            node(path[0], 'KOLL'); node(path[-1], 'KOLL')
            c['L'] = LineString(path).length / 100.0
            c['port'] = c['pidx'] + 1
            c['path'] = path
        # etiketler
        zbase = (100 if k == '1' else 200) + (0 if side == 'a' else 10)
        zones = {}
        for i, c in enumerate(circ):
            if c['room'] not in zones:
                zones[c['room']] = zbase + len(zones) + 1
            c['zone'] = '%s%02d' % (k, zones[c['room']] % 100)
            x0, y0, x1, y1 = c['rect']
            cx, cy = (x0 + x1) / 2, ((y0 + y1) / 2 if (y1 - y0) > 220 or c['ipart'] > 0 else y0 + 0.33 * (y1 - y0))
            T((cx, cy + 9), 'P%d  PEX 16×2,0' % c['port'], 7.0, 'MTY-ISIKAYBIMAHAL', 'MC')
            T((cx, cy), '%d W  -  %.1f m' % (round(c['W']), c['L']), 7.0, 'MTY-ISIKAYBIMAHAL', 'MC')
            T((cx, cy - 9), 'ARALIK %d cm' % c['s'], 6.0, 'MTY-ISIKAYBIMAHAL', 'MC')
            if c['ipart'] == 0:
                hx, hy = x0 + 45, y1 - 35
                HEXTAG((hx, hy), 'MTY-ISIKAYBIMAHAL', 'Z' + c['zone'], '%d°C' % c['ti'], 10)
                T((hx + 40, hy + 4), c['room'], 8.0, 'MTY-ISIKAYBIMAHAL', 'L')
                T((hx + 40, hy - 8), 'ISI KAYBI : %d W' % round(c['Qroom']), 7.0, 'MTY-ISIKAYBIMAHAL', 'L')
                T((hx + 40, hy - 18), 'SERAMİK / LAMİNAT KAPLAMA' if c['room'] != 'BANYO' else 'SERAMİK FAYANS', 6.0,
                  'MTY-ISIKAYBIMAHAL', 'L')
        # kombi -> kollektör (gidiş / dönüş)
        Qd = sum(c['W'] for c in circ)
        if side == 'a':
            hg = [(6161.52, 16211.0), (6156, 16211), (6156, 15978), (6124, 15978), (6124, 15975)]
            hd = [(6161.52, 16217.0), (6152, 16217), (6152, 15982), (6114, 15982), (6114, 15975)]
            kp = (6158.0, 16205.0); lp = (6100, 15940)
        else:
            hg = [(7339.48, 16162.0), (7326, 16162), (7326, 15884), (7268, 15884), (7268, 15872)]
            hd = [(7339.48, 16156.0), (7331, 16156), (7331, 15879), (7273, 15879), (7273, 15872)]
            kp = (7343.0, 16168.0); lp = (7180, 15905)
        mtyblk.insert('KOMBI1', kp, 90 if side == 'a' else -90, 1.0)
        pipe(hg, gp.HGL, 'HG'); pipe(hd, gp.HDL, 'HD')
        for p_ in (hg[0], hg[-1], hd[0], hd[-1]):
            node(p_, 'KOMBI-KOLL')
        T(lp, '%d W - DN20 PEX' % round(Qd), 7.0, gp.HCAP, 'L')
        T((lp[0], lp[1] - 10), 'KOMBİ - KOLLEKTÖR G/D', 6.0, gp.HCAP, 'L')
        out[side] = (circ, calc[side])
    pop()
    return out


# ================================================================== PAFTALAR
import gsheet as GS
SX0 = 5 * SLOT          # şemalar
OY = 14650.0
P = dict(
    floors=[('Z', 'ZEMİN KAT ±0,00'), ('1', '1. KAT +4,00'), ('2', '2. KAT +7,00')], roof_name='ÇATI ARASI +10,00',
    sema_w=3650.0,
    supply=dict(depo='cati', V=3.0, vnote='6 BAĞIMSIZ BÖLÜM ≤ 10 → 3 m³', ybt=15.0, tasma='YB5 YAĞMUR İNİŞİNE (TAŞMA Ø40)',
                units=[('İ2', 'Z', 1, 1.0), ('İ1', 'Z', 2, 1.0), ('D1', '1', 1, 4.5), ('D2', '1', 2, 4.5),
                       ('D3', '2', 1, 4.5), ('D4', '2', 2, 4.5)]),
    groups=[
        dict(x=560, pkx=680, mkx=1460, kombi=1860, bkeys=['LV', 'DUS', 'WC', 'CM', 'YS'], mkeys=['EV', 'BM'], ikeys=['LV', 'WC', 'YS'],
             units={'Z': ('İ2', 'isyeri'), '1': ('D1', 'daire'), '2': ('D3', 'daire')},
             kolons=[('PK1', 680, 100, lambda i: [2 * SB_BANYO + SB_IS, 2 * SB_BANYO, SB_BANYO][i]),
                     ('MK1', 1460, 70, lambda i: [2 * SB_MUTFAK, 2 * SB_MUTFAK, SB_MUTFAK][i])]),
        dict(x=2070, pkx=2190, mkx=2970, kombi=3370, bkeys=['LV', 'DUS', 'WC', 'CM', 'YS'], mkeys=['EV', 'BM'], ikeys=['LV', 'WC', 'YS'],
             units={'Z': ('İ1', 'isyeri'), '1': ('D2', 'daire'), '2': ('D4', 'daire')},
             kolons=[('PK2', 2190, 100, lambda i: [2 * SB_BANYO + SB_IS, 2 * SB_BANYO, SB_BANYO][i]),
                     ('MK2', 2970, 70, lambda i: [2 * SB_MUTFAK, 2 * SB_MUTFAK, SB_MUTFAK][i])]),
    ],
    yagmur=dict(names=list(YB_PTS), P=ROOF_A, dn=100, foot={k: 0 for k in YB_PTS}, tasma_to='YB5'),
)

NOTES = [
    'Temiz su tesisatı PPRC PN20 borularla yapılacak, sıcak su boruları izolasyonlu olarak döşenecektir.',
    'Şebeke suyu bina girişindeki ana sayaç nişinden DBK kolonu ile çatıdaki 3,00 m³ kullanma suyu deposuna verilecektir.',
    'Depodan inen ADK kolonu bina girişindeki (zemin kat holü) sayaç grubuna bağlanacak; her bağımsız bölüm ayrı sayaçtan beslenecektir.',
    'Sayaçlardan önce DN x 10, sonra DN x 5 düz boru bırakılacak; her bağımsız bölüm girişinde küresel vana ve çek valf konulacaktır.',
    'Depo şamandıralı vana, sinekli havalık, taşma, boşaltma ve seviye göstergeli olacak; taşma ve boşaltma YB5 yağmur inişine bağlanacaktır.',
    'Sıcak kullanma suyu her dairede duvar tipi hermetik yoğuşmalı kombiden, iş yerlerinde lavabo altı elektrikli su ısıtıcıdan sağlanacaktır.',
    'Pis su tesisatı TS EN 1451 PVC borularla yapılacak; bina içi yatay hatlar en az %2, bacalar arası hatlar %1 eğimle döşenecektir.',
    'Mutfak ve banyo/WC giderleri birbirine bağlanmayacak; her mahal en yakın kendi kolonuna (PK banyo, MK mutfak) bağlanacaktır.',
    'Pis su kolonları kolon diplerinden temizleme kapağı üzerinden en yakın muayene bacasına (R1-R3) inecek, PB parsel bacası ile SASKİ hattına bağlanacaktır.',
    'Pis su kolonları çatıdan en az 50 cm yukarı çıkarılacak, uçlarına havalık şapkası takılacaktır.',
    'Kolonların geçtiği iş yeri ve hol köşelerinde kolon kutusu (alçıpan, ses yalıtımlı) yapılacaktır.',
    'Parsel bacası kotu ve bağlantı yeri SASKİ\'den alınacak; plandaki kotlar yaklaşık olup sahada teyit edilecektir.',
    'Hiçbir boru betonarme kolon içinden geçirilmeyecek; döşeme geçişleri kiriş bantları dışında kılıflı yapılacaktır.',
    'Yağmur suları pis su hattına bağlanmayacak; 6 adet Ø100 PVC iniş borusu ile yağmur suyu kanalına verilecektir.',
    'Yerden ısıtma devreleri PEX 16x2,0 oksijen bariyerli borularla karşı akışlı salyangoz düzende döşenecektir.',
    'Yerden ısıtma devre boyları (bağlantı boruları dahil) 80 m\'yi geçmeyecek; devreler debimetreli kollektörde dengelenecektir.',
    'İş yerleri duvar tipi split klima ile ısıtılıp soğutulacak; dış üniteler cephe konsolu üzerine, drenajlar en yakın gidere bağlanacaktır.',
    'Temiz su hatlarına 10 bar, yerden ısıtma devrelerine şap öncesi 6 bar basınç testi yapılacaktır.',
    'Tüm imalat TS 1258, TS EN 806, TS EN 12056, TS EN 1264 ve TS 825 standartlarına uygun olarak yapılacaktır.',
]
ANTET = dict(proje="TUNCAY BULUT'A AİT İŞ YERİ + MESKEN PROJESİ", konu='SIHHİ TESİSAT, YERDEN ISITMA VE KLİMA PROJESİ',
             rows=[('YAPININ ÖZELLİKLERİ', ''), ('YAPI SAHİBİ', 'TUNCAY BULUT'), ('YAPI CİNSİ', 'İŞ YERİ + MESKEN / BETONARME'),
                   ('KAT ADEDİ', 'ZEMİN + 2 KAT (+ ÇATI ARASI)'), ('BAĞIMSIZ BÖLÜM', '2 İŞ YERİ + 4 DAİRE = 6'),
                   ('ISITMA', '4 x 24 kW YOĞUŞMALI KOMBİ + YERDEN ISITMA / İŞ YERİ SPLİT KLİMA'),
                   ('SU TEMİNİ', 'ŞEBEKE (SASKİ) + 3,00 m³ ÇATI DEPOSU'), ('KOTLAR', '±0,00 = +33,30'),
                   ('ARSANIN ÖZELLİKLERİ', ''), ('İLİ / İLÇESİ', 'SAKARYA / SERDİVAN'), ('MAHALLE', 'SERDİVAN'), ('PAFTA / ADA / PARSEL', '27J2 / 422 / 1'), ('TOPLAM İNŞAAT ALANI', '492,86 m²')])


def temel_sema(ytk):
    xs = lambda d: SX0 + d
    for nm, x in (('R1', 760), ('R2', 1540), ('R3', 2270), ('R4', 3050)):
        mtyblk.insert('PVC ROGAR', (xs(x), ytk), 0, 1.0)
        T((xs(x) - 20, ytk - 40), nm, 10, 'MTY-ROGAR', 'L')
    for a_, b_ in ((700, 740), (780, 1520), (1480, 1520), (1560, 2250), (2210, 2250), (2290, 3030), (2990, 3030), (3070, 3480)):
        GS.dline((xs(a_), ytk), (xs(b_), ytk), 6)
    mtyblk.insert('PVC ROGAR', (xs(3500), ytk), 0, 1.2)
    T((xs(3540), ytk - 4), 'PB → SASKİ ATIKSU HATTI (%1)', 9, 'MTY-ROGAR', 'L')
    for x, sb in ((1150, 2 * SB_BANYO + SB_IS), (1900, 2 * SB_DAIRE + SB_IS), (2650, 2 * SB_DAIRE + 2 * SB_BANYO + 2 * SB_IS),
                  (3250, 4 * SB_DAIRE + 2 * SB_IS)):
        cap_pis((xs(x), ytk + 8), 0, '%d SB' % sb, 'Ø150', 7)


import gheatsheet as HS
HFLOORS = [('1', '1. KAT', 'DAİRE 1', 'DAİRE 2'), ('2', '2. KAT', 'DAİRE 3', 'DAİRE 4')]


def build_sheets(HEAT, KL):
    yf, ytk = GS.sihhi_sema(SX0, OY, P)
    temel_sema(ytk)
    h, yw = GS.yagmur_sema(SX0 + 3800, OY, P)
    ax = -3900.0
    GS.antet(ax, 16550.0, ANTET)
    GS.notlar(ax + 1800, 16550.0, NOTES)
    GS.lejant(ax, 15550.0)
    # pafta çerçeveleri
    FR = []
    for k in ('T', 'Z', '1', '2', 'C'):
        x0 = SLOTS[k] * SLOT
        FR.append(((x0, 15030.0, x0 + SLOT, 16560.0), NAMES[k], '1/50'))
    FR.append(((SX0, OY - 20, SX0 + 3750, OY + 2080), 'SIHHİ TESİSAT KOLON ŞEMASI', 'ÖLÇEKSİZ'))
    FR.append(((SX0 + 3750, OY - 20, SX0 + 3800 + yw + 60, OY + 2080), 'YAĞMUR SUYU ŞEMASI VE HESABI', 'ÖLÇEKSİZ'))
    FR.append(((ax - 50, 14400.0, -40.0, 16600.0), 'ANTET, NOTLAR VE LEJANT', 'ÖLÇEKSİZ'))
    # ısıtma / klima paftaları
    HNAMES = {'Z': 'ZEMİN KAT İŞ YERLERİ KLİMA PLANI', '1': '1. KAT YERDEN ISITMA PLANI', '2': '2. KAT YERDEN ISITMA PLANI'}
    for k in ('Z', '1', '2'):
        x0 = SLOTS[k] * SLOT
        FR.append(((x0, 15030.0 + HDY, x0 + SLOT, 16560.0 + HDY), HNAMES[k], '1/50'))
    HS.isitma_sema(SX0, 13330.0, HEAT, HFLOORS)
    FR.append(((SX0, 13300.0, SX0 + 3750, 14600.0), 'YERDEN ISITMA KOLON ŞEMASI', 'ÖLÇEKSİZ'))
    tx = SX0 + 3800
    yy = HS.isitma_tablo(tx, 14540.0, HEAT, HFLOORS)
    tx2 = tx + 900
    yy2 = HS.klima_tablo(tx2, 14540.0, KL)
    HS.u_tablo(tx2, yy2 - 10)
    FR.append(((tx - 30, 13300.0, tx2 + 620, 14600.0), 'ISITMA VE KLİMA HESAP ÇİZELGELERİ', 'ÖLÇEKSİZ'))
    for (a, b, c, d), t, o in FR:
        GS.frame(a, b, c, d, t, o)
    return FR, h



# ================================================================== ZEMİN KAT İŞ YERİ KLİMA
import gklima as GK
DUKKAN = [
    dict(name='İŞ YERİ-2', A=50.39, ti=20,
         ext=[('G', 7.10, [(6.0, 2.5, 1, 'ÇP')]), ('B', 6.70, [(1.0, 2.5, 2, 'ÇP')]),
              ('K', 7.10, [(4.3, 1.6, 1, 'ÇP'), (2.2, 2.5, 1, 'BK')])],
         int=[('İDM', 6.00, GH.T_HOL, None)],
         # (iç ünite duvar yüzü, rot, dış ünite dış yüz noktası, rot, drenaj hedefi, drenaj ara noktaları, bakır ara noktalar)
         units=[((5447.0, 15900.0), -90, (5407.0, 15900.0), 90, (5430.0, 16348.0), [(5395.0, None), (5395.0, 16348.0)]),
                ((6148.0, 15930.0), 90, (6035.0, 16212.0), 0, F_Z['YS2'].cp('PS'), [(6125.0, None), (6125.0, 15700.0), (6262.0, 15700.0)])],
         lab=(5560.0, 15760.0)),
    dict(name='İŞ YERİ-1', A=53.34, ti=20,
         ext=[('G', 10.0, [(7.0, 2.5, 1, 'ÇP')]), ('D', 6.30, []),
              ('K', 10.7, [(5.1, 1.6, 1, 'ÇP'), (3.0, 1.6, 1, 'ÇP'), (2.2, 2.5, 1, 'BK')])],
         int=[('İDM', 6.30, GH.T_HOL, None)],
         units=[((7955.0, 15850.0), 90, (7978.0, 15850.0), -90, (8008.0, 15572.0), [(7995.0, None), (7995.0, 15572.0)]),
                ((6792.0, 15950.0), -90, (6900.0, 16132.0), 0, F_Z['YS1'].cp('PS'), [(6815.0, None), (6815.0, 15700.0), (6905.0, 15700.0)])],
         lab=(7300.0, 15780.0)),
]


def klima_calc():
    out = []
    for S in DUKKAN:
        k = GK.kazanc(S)
        h = GH.calc_room(S, 'zemin')
        adet, btu, kw = GK.sec(k['Q'], h['Q'])
        out.append(dict(S=S, kaz=k, kay=h, adet=adet, btu=btu, kw=kw))
    return out


def klima_zemin():
    res = klima_calc()
    push(MOVE(dx('Z'), HDY))
    for r in res:
        S = r['S']
        for i, (io, irot, oo, orot, dtar, dvia) in enumerate(S['units']):
            cu, dr = GK.ic_unite(io, irot, r['btu'])
            dc = GK.dis_unite(oo, orot)
            # bakır boru (sıvı + gaz, izoleli) - asma tavan / duvar içinden dış üniteye
            path = [cu]
            if abs(cu[0] - dc[0]) > 0.5 and abs(cu[1] - dc[1]) > 0.5:
                path.append((cu[0], dc[1]) if irot in (90, -90) and orot == 0 else (dc[0], cu[1]) if orot in (90, -90) else (cu[0], dc[1]))
            path.append(dc)
            pipe(path, GK.LBAK, 'K'); node(path[0], 'KLIMA'); node(path[-1], 'KLIMA')
            # drenaj
            dp = [dr] + [(x if x is not None else dr[0], y if y is not None else dr[1]) for x, y in
                         [(v[0], v[1]) for v in dvia]] + [dtar]
            pipe(dp, GK.LDRN, 'KD'); node(dp[0], 'KLIMA'); node(dp[-1], 'KLIMA')
            T((dp[-2][0] + 6, (dp[-2][1] + dp[-3][1]) / 2 if len(dp) > 2 else dp[-2][1]),
              'DRENAJ Ø20 PVC (%s)' % ('YAĞMUR İNİŞİNE' if dtar[1] > 16300 or dtar[1] < 15580 else 'SİFONLU YER SÜZGECİNE'), 6.0, GK.LDRN, 'L', rot=90)
            tx, ty = io
            off = 60 if irot == -90 else -60
            T((tx + off, ty + 30), 'K%d%s' % (1 if S['name'].endswith('1') else 2, 'AB'[i]), 9.0, GK.LIC, 'L' if off > 0 else 'R')
            T((tx + off, ty + 18), 'DUVAR TİPİ SPLİT KLİMA %d BTU/h' % r['btu'], 7.0, GK.LIC, 'L' if off > 0 else 'R')
            T((tx + off, ty + 8), 'Qs=%.2f kW  Qı=%.2f kW' % (r['kw'], r['kw'] * 1.1), 6.5, GK.LIC, 'L' if off > 0 else 'R')
            T((tx + off, ty - 2), 'BAKIR 1/4"-1/2" İZOLELİ', 6.0, GK.LBAK, 'L' if off > 0 else 'R')
        lx, ly = S['lab']
        T((lx, ly), '%s  -  ISI KAZANCI %.0f W / ISI KAYBI %.0f W' % (S['name'], r['kaz']['Q'], r['kay']['Q']), 8.0, GK.LIC, 'L')
        T((lx, ly - 12), '%d ADET DUVAR TİPİ SPLİT KLİMA (%d BTU/h) SEÇİLMİŞTİR' % (r['adet'], r['btu']), 7.0, GK.LIC, 'L')
    pop()
    return res


if __name__ == '__main__':
    build_sihhi()
    build_rest()
    HEAT = {k: heat_floor(k) for k in ('1', '2')}
    KLIMA = klima_zemin()
    for r in KLIMA:
        print(r['S']['name'], round(r['kaz']['Q']), round(r['kay']['Q']), r['adet'], r['btu'])
    for k, v in HEAT.items():
        for side, (circ, calc) in v.items():
            print(k, side, [(c['room'], c['port'], round(c['W']), round(c['L'], 1), c['s']) for c in circ])
    FR, YH = build_sheets(HEAT, KLIMA)
    print('yağmur', YH)
    cols = []
    from shapely import affinity
    base = COLS()
    for k in ('T', 'Z', '1', '2'):
        for c in base:
            cols.append(affinity.translate(c, dx(k), 0))
    rep = gp.check(cols)
    print('KONTROL', len(rep))
    for r in rep[:60]:
        print('  ', r)
    import xcheck
    xr = xcheck.crossings()
    print('köprü', xcheck.hops(xr), 'çakışık', [r for r in xcheck.summary(xr) if r[0] == 'ÇAKIŞIK'])
    print('yazı altı kesilen boru', xcheck.mask_texts())
    print('üst üste binen çizgi temizlendi', xcheck.dedupe())
    pickle.dump((cad.R, FR), open('/tmp/claude-0/p2/tb_R.pkl', 'wb'))
    pickle.dump(dict(HEAT=HEAT, KLIMA=KLIMA, ROOMS=ROOMS, ROOF_A=ROOF_A, NYB=len(YB_PTS)),
                open('/tmp/claude-0/p2/tb_calc.pkl', 'wb'))


