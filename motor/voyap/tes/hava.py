# -*- coding: utf-8 -*-
"""Havalandırma sırası (V = Y - 10322): bodrum otopark egzoz + taze hava (4 hava değişimi; duman tahliyesi 10 hava
değişimi), sığınak havalandırması (alan ölçülerek, koruma havası + normal havalandırma + 100 m² üstü duman egzozu),
kazan dairesi menfezleri; zemin kat şaft çıkışları."""
import math, pickle
from shapely.geometry import Polygon, Point, LineString, box
from veri import *
from tlib import *
import ag
from hesap import kanal
from isitma import R

VY = '/tmp/claude-0/vy/'
OUTH = {}


def V(p, i=0):
    return W(p, i, 'V')


def duct(pts, wcm, lay, label=None, q=None, h=8.0):
    """dikdörtgen kanal: eksen çoklu çizgisi -> iki kenar + uçlar kapalı"""
    P = [V(p) for p in pts]
    a = ag.offset(P, wcm / 2); b = ag.offset(P, -wcm / 2)
    PL(a, lay); PL(b, lay)
    PL([a[0], b[0]], lay); PL([a[-1], b[-1]], lay)
    OBST.append(LineString(P).buffer(wcm / 2))
    if label:
        pipe_label(P, label, h, KCAP, ust=q)
    return P


def menfez(p, lay=MEN, rot=0.0, s=1.0):
    INS("T-MENFEZ", V(p), rot, s, lay=lay)


def bodrum_mim():
    M = pickle.load(open(VY + 'mimT.pkl', 'rb'))
    dx, dy = ROW['V']
    for r in M:
        if r[0] == 'L':
            a, b = r[2][0], r[2][1]
            if 247900 < a[0] < 250300: L((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy), "MIM-GUNCEL-BODRUM")
        elif r[0] == 'P':
            q = r[2]
            if 247900 < q[0][0] < 250300: PL([(p[0] + dx, p[1] + dy) for p in q], "MIM-GUNCEL-BODRUM")
        elif r[0] == 'C':
            c = r[2]
            if 247900 < c[0] < 250300: C((c[0] + dx, c[1] + dy), c[2], "MIM-GUNCEL-BODRUM")


def zemin_mim():
    S = pickle.load(open(VY + 'sih.pkl', 'rb'))
    dx = -ROW['S'][0] + ROW['V'][0]; dy = -ROW['S'][1] + ROW['V'][1]
    for r in S:
        if r[1] != 'MKDU0': continue
        if r[0] == 'L':
            a, b = r[2][0], r[2][1]
            if 252331 < a[0] < 254422 and -447800 < a[1] < -440300: L((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy), "MIM-GUNCEL-BODRUM")
        elif r[0] == 'P':
            q = r[2]
            if 252331 < q[0][0] < 254422 and -447800 < q[0][1] < -440300: PL([(p[0] + dx, p[1] + dy) for p in q], "MIM-GUNCEL-BODRUM")
        elif r[0] == 'T':
            (x, y), s, hh = r[2][0][:2], r[2][1], r[2][2]
            if 252331 < x < 254422 and -447800 < y < -440300 and 'PLANI' not in s:
                T(x + dx, y + dy, s.replace('\\U+0130', 'İ'), min(hh, 30), "MIM-GUNCEL-BODRUM")


def otopark():
    o = R['otopark']
    # ---- egzoz: doğu ve batı kollar, güneyde toplayıcı, fan dairesi, ön cephe egzoz bacası
    Qd, Qn = o['Qd'], o['Qn']
    wA, hA, vA = kanal(Qd / 2, 9.0)
    wM, hM, vM = kanal(Qd, 9.0)
    dogu = [(249700.0, -452250.0), (249700.0, -456850.0)]
    bati = [(248850.0, -452450.0), (248850.0, -456850.0)]
    topl = [(248850.0, -456850.0), (249700.0, -456850.0)]
    duct(dogu, wA, EGZ, f"EGZOZ {wA}x{hA}", f"{Qd / 2:.0f} m³/h (yangın) / {Qn / 2:.0f} (normal)")
    duct(bati, wA, EGZ, f"EGZOZ {wA}x{hA}", f"{Qd / 2:.0f} m³/h (yangın) / {Qn / 2:.0f} (normal)")
    duct(topl, wM, EGZ, f"EGZOZ TOPLAYICI {wM}x{hM}", f"{Qd:.0f} m³/h")
    # menfezler her kolda ~5 m arayla
    nm = 0
    for x0, y0, y1 in ((249700.0, -452350.0, -456700.0), (248850.0, -452550.0, -456700.0)):
        y = y0
        while y > y1:
            menfez((x0 + wA / 2 + 22, y), rot=90); menfez((x0 - wA / 2 - 22, y), rot=90)
            nm += 2; y -= 500.0
    qm = Qd / nm
    place_text(V((249700.0 + wA / 2 + 22, -452350.0)), [f"{nm} AD. EGZOZ MENFEZİ 600x300", f"her biri {qm:.0f} m³/h (yangın)", "TAVAN SEVİYESİ, ≤5 m ARA"], 6.5, MEN, rmax=120)
    # fanlar (2 adet çift hızlı, F300 2 saat)
    fan_y = -456850.0
    for k, x in enumerate((249150.0, 249400.0)):
        INS("T-FAN", V((x, fan_y - 95)), 0, 1.0, lay=HCH)
        PL([V((x, fan_y - wM / 2)), V((x, fan_y - 65))], EGZ)
        T(*V((x, fan_y - 140)), f"EF-{k + 1}", 8, HCH, TA.TOP_CENTER)
    fq = Qd / 2
    place_text(V((249275.0, fan_y - 160)), [f"EF-1/EF-2 EGZOZ (DUMAN TAHLİYE) FANI", f"Q={fq:.0f}/{Qn / 2:.0f} m³/h ÇİFT HIZLI", "F300 (300 °C 2 saat) EN 12101-3", "H=450 Pa"], 6.0, HCH, rmax=120)
    cik = [(249150.0, fan_y - 125), (249150.0, -457250.0), (249100.0, -457300.0), (249100.0, -457420.0)]
    duct([(249150.0, fan_y - 125), (249150.0, -457330.0)], wM, EGZ)
    # ön cephe dışında egzoz bacası
    bx = (248990.0, -457560.0, 249230.0, -457360.0)
    pp = [V((bx[0], bx[1])), V((bx[2], bx[1])), V((bx[2], bx[3])), V((bx[0], bx[3]))]
    PL(pp, SFT, closed=True); L(pp[0], pp[2], SFT); L(pp[1], pp[3], SFT)
    place_text(V(((bx[0] + bx[2]) / 2, bx[1])), ["OTOPARK EGZOZ BACASI (ÖN CEPHE DIŞI)", f"{wM}x{hM} kanal; çıkış +3,00 m panjurlu",
                                                  "ÖN CEPHE PERDESİNDE BETONARMEDE", f"{wM + 10}x{hM + 10} cm BOŞLUK BIRAKILACAKTIR"], 6.5, TNOT, rmax=140,
               prefer=[(0, -1), (1, -1), (-1, -1)])
    # ---- taze hava: ön cephe (sol) emiş -> batı-orta kanal -> kuzey yarıda üfleme
    Qt, Qtd = o['Qt'], o['Qtd']
    wT, hT, vT = kanal(Qtd, 9.0)
    tz = [(248560.0, -457050.0), (248560.0, -456700.0), (249250.0, -456700.0), (249250.0, -452350.0)]
    duct(tz[1:], wT, UFL, f"TAZE HAVA {wT}x{hT}", f"{Qtd:.0f} m³/h (yangın) / {Qt:.0f} (normal)")
    for k, y in enumerate((-452450.0, -452950.0, -453450.0, -453950.0, -454450.0, -454950.0)):
        menfez((249250.0 + wT / 2 + 22, y), lay=MEN, rot=90); menfez((249250.0 - wT / 2 - 22, y), lay=MEN, rot=90)
    place_text(V((249250.0 - wT / 2 - 22, -452450.0)), ["12 AD. TAZE HAVA MENFEZİ 600x300", f"her biri {Qtd / 12:.0f} m³/h", "KUZEY YARIDA (egzoz güneyde)"], 6.5, MEN, rmax=120)
    for k, x in enumerate((248560.0,)):
        INS("T-FAN", V((x, -456880.0)), 0, 1.0, lay=HCH)
        T(*V((x + 40, -456880.0)), "SF-1/SF-2", 8, HCH, TA.MIDDLE_LEFT)
    place_text(V((248560.0, -456880.0)), ["SF-1/SF-2 TAZE HAVA FANI (2 AD.)", f"Q={Qtd / 2:.0f}/{Qt / 2:.0f} m³/h ÇİFT HIZLI", "H=350 Pa"], 6.0, HCH, rmax=120,
               prefer=[(1, 1), (1, 0), (1, -1)])
    duct([(248560.0, -456700.0), (248560.0, -457100.0)], wT, UFL)
    bx = (248420.0, -457330.0, 248640.0, -457150.0)
    pp = [V((bx[0], bx[1])), V((bx[2], bx[1])), V((bx[2], bx[3])), V((bx[0], bx[3]))]
    PL(pp, SFT, closed=True); L(pp[0], pp[2], SFT); L(pp[1], pp[3], SFT)
    place_text(V(((bx[0] + bx[2]) / 2, bx[1])), ["OTOPARK TAZE HAVA BACASI (ÖN CEPHE DIŞI)", "emiş +2,00 m ızgaralı, egzozdan ≥5 m",
                                                  f"BETONARMEDE {wT + 10}x{hT + 10} cm BOŞLUK BIRAKILACAKTIR"], 6.5, TNOT, rmax=140,
               prefer=[(0, -1), (-1, -1), (1, -1)])
    # CO dedektörleri
    for p in ((248700.0, -453000.0), (249500.0, -453000.0), (248700.0, -455500.0), (249500.0, -455500.0)):
        C(V(p), 10, HCH); T(*V(p), "CO", 6, HCH, TA.MIDDLE_CENTER)
    place_text(V((249500.0, -455500.0)), ["CO DEDEKTÖRÜ (4 AD.)", "50 ppm düşük hız / 100 ppm yüksek hız"], 6.0, HCH, rmax=80)
    OUTH['otopark'] = dict(wA=wA, hA=hA, wM=wM, hM=hM, wT=wT, hT=hT, nm=nm)


def siginak():
    s = R['siginak']
    x0, y0, x1, y1 = SIGINAK
    kx = KAZAN_D[2]
    # alan ölçüsü
    pp = [V((kx, y0)), V((x1, y0)), V((x1, y1)), V((kx, y1))]
    a = V((x0 + 30, y0 + 30))
    T(*V((kx + 40, y1 - 40)), "SIĞINAK", 18, TNOT, TA.TOP_LEFT)
    T(*V((kx + 40, y1 - 66)), f"MİMARİ SIĞINAK ALANI (ÖLÇÜLEN): {(x1 - x0) / 100:.2f} x {(y1 - y0) / 100:.2f} = {s['A']} m²", 7, TNOT, TA.TOP_LEFT)
    T(*V((kx + 40, y1 - 80)), f"KİŞİ: {s['kisi']} (1 m²/kişi)  h={s['h']} m  V={s['V']} m³", 7, TNOT, TA.TOP_LEFT)
    # taze hava: arka cephe hava bacası -> basınç kapağı -> kum filtresi -> vantilatör -> sığınak
    q1 = s['Q_normal']; wq, hq, _ = kanal(q1, 5.0)
    tb = (249480.0, -450800.0, 249620.0, -450700.0)
    eb = (249840.0, -450800.0, 249980.0, -450700.0)
    for bx, t in ((tb, "SIĞINAK TAZE HAVA BACASI"), (eb, "SIĞINAK EGZOZ / DUMAN BACASI")):
        pp = [V((bx[0], bx[1])), V((bx[2], bx[1])), V((bx[2], bx[3])), V((bx[0], bx[3]))]
        PL(pp, SFT, closed=True); L(pp[0], pp[2], SFT); L(pp[1], pp[3], SFT)
        place_text(V(((bx[0] + bx[2]) / 2, bx[3])), [t, "(arka cephe dışı, ızgaralı +0,50)"], 6.0, TNOT, rmax=90, prefer=[(0, 1), (1, 1), (-1, 1)])
    INS("T-GAZKAPAK", V((249550.0, -450900.0)), 0, 1.0, lay=HCH)
    INS("T-GAZKAPAK", V((249910.0, -450900.0)), 0, 1.0, lay=HCH)
    PL([V((249550.0, -450800.0)), V((249550.0, -450888.0))], UFL, 3.0)
    PL([V((249910.0, -450800.0)), V((249910.0, -450888.0))], EGZ, 3.0)
    place_text(V((249550.0, -450900.0)), ["GAZ SIZDIRMAZ BASINÇ KAPAĞI", "(perdede, betonarmede Ø300 boşluk)"], 5.5, HCH, rmax=60, prefer=[(-1, -1), (-1, 0)])
    # kum filtresi + vantilatör
    kf = (249480.0, -451000.0, 249640.0, -450940.0)
    pp = [V((kf[0], kf[1])), V((kf[2], kf[1])), V((kf[2], kf[3])), V((kf[0], kf[3]))]
    PL(pp, HCH, closed=True); T(*V(((kf[0] + kf[2]) / 2, (kf[1] + kf[3]) / 2)), "KUM FİLTRESİ", 5.5, HCH, TA.MIDDLE_CENTER)
    PL([V((249550.0, -450912.0)), V((249550.0, -450940.0))], UFL, 3.0)
    INS("T-FAN", V((249550.0, -451060.0)), 0, 0.7, lay=HCH)
    place_text(V((249550.0, -451060.0)), ["SV-1 SIĞINAK VANTİLATÖRÜ (EL+ELEKTRİK)", f"normal {q1} m³/h / koruma {s['Q_koruma']} m³/h"], 6.0, HCH, rmax=90, prefer=[(-1, -1), (-1, 0), (1, -1)])
    duct([(249550.0, -451081.0), (249550.0, -451150.0), (249300.0, -451150.0)], wq, UFL, None)
    duct([(249550.0, -451150.0), (249950.0, -451150.0)], wq, UFL, f"TAZE HAVA {wq}x{hq}", f"{q1} m³/h")
    for x in (249300.0, 249500.0, 249700.0, 249900.0):
        menfez((x, -451150.0 - wq / 2 - 18), lay=MEN)
    # egzoz + duman egzozu (çift hızlı, F400)
    qe = s['Q_egzoz']; qd = s['Q_duman']; we, he, _ = kanal(max(qe, qd), 6.0)
    duct([(249300.0, -451600.0), (249910.0, -451600.0), (249910.0, -451050.0)], we, EGZ, f"EGZOZ/DUMAN {we}x{he}", f"{qe}/{qd} m³/h")
    for x in (249350.0, 249550.0, 249750.0):
        menfez((x, -451600.0 + we / 2 + 18), lay=MEN)
    INS("T-FAN", V((249910.0, -451000.0)), 0, 0.7, lay=HCH)
    place_text(V((249910.0, -451000.0)), ["EF-S SIĞINAK EGZOZ / DUMAN FANI", f"{qe}/{qd} m³/h ÇİFT HIZLI, F400 (400 °C 2 s)",
                                           f"sığınak {s['A']} m² > 100 m² → DUMAN EGZOZU"], 6.0, HCH, rmax=110, prefer=[(-1, -1), (-1, 0)])
    INS("T-DAMPER", V((249910.0, -450960.0)), 0, 1.0, lay=HCH)
    PL([V((249910.0, -450912.0)), V((249910.0, -450975.0))], EGZ, 3.0)
    place_text(V((249700.0, -451450.0)), ["AŞIRI BASINÇ VALFİ (+50 Pa)", "WC/lobi üzerinden egzoz"], 5.5, HCH, rmax=60)
    # kazan dairesi menfez kanalları (arka cephe hava bacasına)
    for k, (x, t) in enumerate(((248760.0, f"KAZAN D. ALT MENFEZ {R['kd_hava']['alt']} cm² → +0,30"), (249150.0, f"KAZAN D. ÜST MENFEZ {R['kd_hava']['ust']} cm² (tavan)"))):
        bx = (x - 50, -450800.0, x + 50, -450720.0)
        pp = [V((bx[0], bx[1])), V((bx[2], bx[1])), V((bx[2], bx[3])), V((bx[0], bx[3]))]
        PL(pp, SFT, closed=True); L(pp[0], pp[2], SFT); L(pp[1], pp[3], SFT)
        menfez((x, -450900.0)); PL([V((x, -450800.0)), V((x, -450890.0))], UFL if k == 0 else EGZ, 3.0)
        place_text(V((x, -450900.0)), [t, "betonarmede boşluk bırakılacaktır"], 5.5, MEN, rmax=80, prefer=[(1, -1), (-1, -1)])
    OUTH['siginak'] = dict(wq=wq, hq=hq, we=we, he=he)


def notlar_hava(x, y):
    o = R['otopark']; s = R['siginak']
    N = [
        "OTOPARK HAVALANDIRMASI SAATTE 4 HAVA DEĞİŞİMİ (NORMAL), DUMAN TAHLİYESİ SAATTE 10 HAVA DEĞİŞİMİ ESAS ALINARAK YAPILACAKTIR.",
        "EGZOZ ÇIKIŞI SIĞINAĞIN BULUNDUĞU ARKA CEPHENİN TERSİ OLAN ÖN CEPHEDEN VERİLECEKTİR (BİNA BİTİŞİK NİZAM, YAN CEPHELERDEN ÇIKIŞ YOKTUR).",
        "EGZOZ VE TAZE HAVA KANALLARI İÇİN ÖN CEPHE BETONARME PERDESİNDE KANAL ÖLÇÜSÜNDEN 10 CM BÜYÜK BOŞLUK BIRAKILACAKTIR.",
        "SIĞINAK HAVALANDIRMA VE EGZOZ GEÇİŞLERİ İÇİN SIĞINAK BETONARMESİNDE Ø300 BOŞLUK BIRAKILACAK, GAZ SIZDIRMAZ BASINÇ KAPAĞI TAKILACAKTIR.",
        "EGZOZ FANLARI EN 12101-3 F300 (OTOPARK) / F400 (SIĞINAK) SINIFINDA, ÇİFT HIZLI VE YANGIN ALGILAMA SİSTEMİNE BAĞLI OLACAKTIR.",
        "NORMAL İŞLETMEDE FANLAR CO DEDEKTÖRLERİ İLE DÜŞÜK / YÜKSEK HIZDA, YANGIN ANINDA YÜKSEK HIZDA ÇALIŞACAKTIR.",
        "DUMAN TAHLİYE KANALLARI EN AZ 1,2 MM GALVANİZ SAÇ, ASKILARI YANGINA DAYANIKLI OLACAKTIR.",
        "SIĞINAK TAZE HAVA HATTINDA KUM FİLTRESİ VE EL + ELEKTRİK TAHRİKLİ SIĞINAK VANTİLATÖRÜ KULLANILACAKTIR.",
        "KAZAN DAİRESİ ALT VE ÜST MENFEZ KESİTLERİ GAZ DAĞITIM ŞİRKETİ TEKNİK ŞARTNAMESİNE GÖRE KESİNLEŞTİRİLECEKTİR.",
    ]
    T(x, y, "HAVALANDIRMA NOTLARI", 14, TNOT, TA.TOP_LEFT)
    for k, n in enumerate(N):
        T(x, y - 30 - k * 18, f"{k + 1}. {n}", 8, TNOT, TA.TOP_LEFT)
    return y - 30 - len(N) * 18


def zemin_saft():
    """zemin planında şaft / baca çıkışları (V sırası zemin paftası)"""
    for bx, t in (((248990.0, -457560.0, 249230.0, -457360.0), "OTOPARK EGZOZ BACASI çıkış +3,00"),
                  ((248420.0, -457330.0, 248640.0, -457150.0), "OTOPARK TAZE HAVA BACASI emiş +2,00"),
                  ((249480.0, -450800.0, 249620.0, -450700.0), "SIĞINAK TAZE HAVA BACASI"),
                  ((249840.0, -450800.0, 249980.0, -450700.0), "SIĞINAK EGZOZ/DUMAN BACASI"),
                  ((248710.0, -450800.0, 248810.0, -450720.0), "KAZAN D. ALT MENFEZ"),
                  ((249100.0, -450800.0, 249200.0, -450720.0), "KAZAN D. ÜST MENFEZ")):
        pp = [W((bx[0], bx[1]), 0, 'V'), W((bx[2], bx[1]), 0, 'V'), W((bx[2], bx[3]), 0, 'V'), W((bx[0], bx[3]), 0, 'V')]
        dx, dy = OFF[1]
        pp = [(p[0] + dx, p[1] + dy) for p in pp]
        PL(pp, SFT, closed=True); L(pp[0], pp[2], SFT); L(pp[1], pp[3], SFT)
        place_text(((pp[0][0] + pp[2][0]) / 2, (pp[0][1] + pp[2][1]) / 2), [t], 7.0, TNOT, rmax=90)
    # kazan bacası (Ş1)
    p = W(SAFT['S1']['baca'], 1, 'V')
    C(p, 13, BACA); place_text(p, [f"KAZAN BACASI Ø{R['baca']['Dsec']} (Ş1) ÇATIYA"], 7.0, BACA, rmax=90)
