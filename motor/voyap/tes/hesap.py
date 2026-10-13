# -*- coding: utf-8 -*-
"""VOYAP mekanik hesaplar: ısı kaybı (ofis + dükkân), kazan, boyler, pompa, genleşme, baca, temiz su / pis su,
hidrofor + depo, otopark havalandırma + duman tahliyesi, sığınak havalandırması.
Tüm sonuçlar R sözlüğünde; Excel ve paftalar buradan beslenir."""
import math, pickle
from shapely.geometry import Polygon, Point, LineString
from shapely.affinity import translate
from veri import *

VY = '/tmp/claude-0/vy/'
GEO = pickle.load(open(VY + 'geo.pkl', 'rb'))

# ------------------------------------------------------------------ iklim ve yapı kabulleri
TD = -3.0                       # dış tasarım sıcaklığı (TS 825 2. bölge / Sakarya-İstanbul)
TI = {'ofis': 20.0, 'dukkan': 20.0}
T_KOR = 10.0                    # ısıtılmayan ortak alan (koridor, merdiven holü)
T_OTO = 5.0                     # kapalı otopark
U = dict(duvar=0.50, pencere=1.70, cati=0.35, doseme_oto=0.50, ic_duvar=1.20, ic_tavan=1.10, vitrin=1.60)
PEN_ORAN = dict(cephe=0.35, isiklik=0.30, vitrin=0.70)
N_INF = dict(ofis=1.0, dukkan=1.5)
F_RH = 11.0                     # kesintili ısıtma yeniden ısıtma payı W/m² (EN 12831, 1 h)
ZD = 0.07                       # işletme zammı (kesintili ısıtma)
ZH = {'K': 0.05, 'G': -0.05, 'I': 0.0}

IS1 = Polygon([(255150, -442732), (256480, -442732), (256460, -443102), (255131, -443102)])
IS2 = Polygon([(255483, -445202), (256295, -445202), (256263, -445552), (255483, -445552)])


def _foot_S(i):
    return translate(GEO[i]['foot'], ROW['S'][0], ROW['S'][1])


def kenar_sinif(poly, foot, others, isiklik=(IS1, IS2), d=45.0):
    """her kenar: ('dis', yön) / ('isiklik',) / ('komsu',) / ('kor',) / ('ic',)"""
    out = []
    c = list(poly.exterior.coords)
    if poly.exterior.is_ccw is False:
        c = c[::-1]
    for a, b in zip(c[:-1], c[1:]):
        L = math.dist(a, b)
        if L < 20: continue
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx_, ny_ = uy, -ux                       # ccw çokgende dış normal
        q = Point(m[0] + nx_ * d, m[1] + ny_ * d)
        if any(g.contains(q) for g in isiklik):
            k = ('isiklik', 'K' if ny_ > 0 else 'G')
        elif not foot.contains(q):
            if abs(ny_) > 0.6:
                k = ('dis', 'K' if ny_ > 0 else 'G')
            else:
                k = ('komsu',)
        elif any(o.contains(q) for o in others):
            k = ('ic',)
        else:
            k = ('kor',)
        out.append((k, L / 100.0))
    return out


def ofis_isi(k, kat):
    poly = ofis_poly(k, kat, 'S')
    foot = _foot_S(kat)
    others = [ofis_poly(j, kat, 'S') for j in OFIS_S1 if j != k]
    A = poly.area / 1e4 * 0.92                      # net alan (duvar payı %8)
    h = KH[kat] - 0.20
    ti = TI['ofis']
    sat = []
    Q = 0.0
    for kk, L in kenar_sinif(poly, foot, others):
        if kk[0] in ('dis', 'isiklik'):
            oran = PEN_ORAN['cephe' if kk[0] == 'dis' else 'isiklik']
            Aw = L * h; Ap = Aw * oran; Ad = Aw - Ap
            dT = ti - TD
            z = 1 + ZD + ZH[kk[1]]
            q1 = U['duvar'] * Ad * dT * z; q2 = U['pencere'] * Ap * dT * z
            sat.append((f"Dış duvar ({'cephe' if kk[0] == 'dis' else 'ışıklık'} {kk[1]})", L, round(Ad, 2), U['duvar'], dT, round(q1)))
            sat.append((f"Pencere ({kk[1]})", L, round(Ap, 2), U['pencere'], dT, round(q2)))
            Q += q1 + q2
        elif kk[0] == 'kor':
            Aw = L * h; dT = ti - T_KOR
            q1 = U['ic_duvar'] * Aw * dT * (1 + ZD)
            sat.append(("İç duvar (ısıtılmayan koridor)", L, round(Aw, 2), U['ic_duvar'], dT, round(q1)))
            Q += q1
    if kat == 3:
        dT = ti - TD
        q1 = U['cati'] * A * dT * (1 + ZD)
        sat.append(("Çatı döşemesi", '', round(A, 2), U['cati'], dT, round(q1)))
        Q += q1
    V = A * h
    qs = 0.34 * N_INF['ofis'] * V * (ti - TD)
    sat.append((f"Havalandırma/sızıntı n={N_INF['ofis']}", '', round(V, 1), 0.34 * N_INF['ofis'], ti - TD, round(qs)))
    Q += qs
    qr = F_RH * A
    sat.append(("Yeniden ısıtma payı (kesintili, 11 W/m²)", '', round(A, 2), F_RH, '', round(qr)))
    Q += qr
    return dict(ad=f"{KATAD[kat]} OFİS {k}", kod=f"{kat - 1}{k}", A=round(A, 1), V=round(V, 1), Q=round(Q), satir=sat,
                wm2=round(Q / A, 1))


def dukkan_isi(nm):
    d = DUKKAN_S[nm]
    poly = Polygon(d['poly'])
    foot = _foot_S(1)
    others = [Polygon(DUKKAN_S[j]['poly']) for j in DUKKAN_S if j != nm]
    A = poly.area / 1e4 * 0.95
    h = KH[1] - 0.20
    ti = TI['dukkan']
    sat = []; Q = 0.0
    for kk, L in kenar_sinif(poly, foot, others, isiklik=()):
        if kk[0] == 'dis':
            Aw = L * h; Ap = Aw * PEN_ORAN['vitrin']; Ad = Aw - Ap
            dT = ti - TD; z = 1 + ZD + ZH[kk[1]]
            q1 = U['duvar'] * Ad * dT * z; q2 = U['vitrin'] * Ap * dT * z
            sat.append((f"Dış duvar (cephe {kk[1]})", L, round(Ad, 2), U['duvar'], dT, round(q1)))
            sat.append((f"Vitrin / kapı ({kk[1]})", L, round(Ap, 2), U['vitrin'], dT, round(q2)))
            Q += q1 + q2
        elif kk[0] == 'kor':
            Aw = L * h; dT = ti - T_KOR
            q1 = U['ic_duvar'] * Aw * dT * (1 + ZD)
            sat.append(("İç duvar (ısıtılmayan hol/geçit)", L, round(Aw, 2), U['ic_duvar'], dT, round(q1)))
            Q += q1
    # döşeme: otopark üstü
    dT = ti - T_OTO
    q1 = U['doseme_oto'] * A * dT * (1 + ZD)
    sat.append(("Döşeme (kapalı otopark üstü)", '', round(A, 2), U['doseme_oto'], dT, round(q1))); Q += q1
    # tavan: ışıklık altı kısımlar çatı
    up = poly.intersection(translate(IS1, -2101, 0)).area / 1e4 + poly.intersection(translate(IS2, -2101, 0)).area / 1e4
    if up > 0.5:
        q1 = U['cati'] * up * (ti - TD) * (1 + ZD)
        sat.append(("Tavan (ışıklık altı, çatı)", '', round(up, 2), U['cati'], ti - TD, round(q1))); Q += q1
    V = A * h
    qs = 0.34 * N_INF['dukkan'] * V * (ti - TD)
    sat.append((f"Havalandırma/sızıntı n={N_INF['dukkan']}", '', round(V, 1), 0.34 * N_INF['dukkan'], ti - TD, round(qs)))
    Q += qs
    qr = F_RH * A
    sat.append(("Yeniden ısıtma payı (kesintili, 11 W/m²)", '', round(A, 2), F_RH, '', round(qr)))
    Q += qr
    return dict(ad=f"ZEMİN KAT {nm}", kod=nm, A=round(A, 1), V=round(V, 1), Q=round(Q), satir=sat, wm2=round(Q / A, 1))


# ------------------------------------------------------------------ radyatör (PKKP 600, 70/50/20 → ΔT=40 K)
def pkkp_wm(tip='PKKP', h=600, dT=40.0):
    q50 = {('PKKP', 600): 1969.0, ('PKKP', 500): 1689.0, ('PKKP', 300): 1100.0}[(tip, h)]   # W/m, ΔT=50 K
    return q50 * (dT / 50.0) ** 1.30


def dukkan_radyator(Q, cephe_m):
    """kullanıcı talimatı: dükkân başına 4 panel, köşelere; 600 yükseklik, ≥100 cm (gerekirse büyütülür, 1,6 m üstü PKKKP)"""
    n = 4
    wm = pkkp_wm('PKKP', 600)
    L = math.ceil(Q / wm / n * 10) / 10
    tip = 'PKKP 600 (Tip 22)'
    if L > 1.6:
        wm = wm * 1.42                                   # Tip 33 / Tip 22 oranı (EN 442 katalog)
        L = math.ceil(Q / wm / n * 10) / 10; tip = 'PKKKP 600 (Tip 33)'
    return dict(adet=n, boy=round(max(1.0, L), 1), tip=tip, wm=round(wm))


# ------------------------------------------------------------------ yerden ısıtma ofis devresi (45/35)
def yi_kontrol(o):
    """ofis q (W/m²) kontrolü: seramik/laminat için 15 cm aralık, 45/35 °C → ~80 W/m² üst sınır"""
    return 'UYGUN' if o['wm2'] <= 85 else 'KONTROL'


# ------------------------------------------------------------------ BOYLER / sıcak su
CIHAZ_SS = [('Lavabo', 28, 8.0), ('Eviye (mutfak)', 28, 40.0), ('Duş', 28, 150.0)]     # adet, l/h (60 °C)


def boyler():
    top = sum(n * q for _, n, q in CIHAZ_SS)
    phi = 0.20                     # ofis kullanma (eşzamanlılık) katsayısı
    dep = 0.80                     # depolama katsayısı
    Qh = top * phi                 # l/h
    V = Qh * dep
    Vsec = 1000 if V <= 1000 else 1500
    P = Qh * (60 - 10) * 1.163 / 1000.0        # kW (ısıtma süresi 1 h)
    P_serp = P * 0.75              # depolama payı ile serpantin
    return dict(cihaz=CIHAZ_SS, toplam=top, phi=phi, Qh=round(Qh), dep=dep, V=round(V), Vsec=Vsec, P=round(P, 1),
                P_serp=round(P_serp, 1))


# ------------------------------------------------------------------ temiz su (TS 1258 / MTY YB)
YB_OFIS = dict(lavabo=0.5, klozet=0.5, dus=2.5, eviye=1.0)          # kullanıcının MTY değerleri (soğuk)
YB_SICAK = dict(lavabo=0.5, dus=2.5, eviye=1.0)


def yb_ofis():
    soguk = sum(YB_OFIS.values()); sicak = sum(YB_SICAK.values())
    return soguk, sicak


def dn_pprc(yb):
    T = [(2.25, 'Ø20', 20), (7.84, 'Ø25', 25), (19.36, 'Ø32', 32), (46.24, 'Ø40', 40), (108.4, 'Ø50', 50),
         (256, 'Ø63', 63), (784, 'Ø75', 75), (1444, 'Ø90', 90), (4096, 'Ø110', 110)]
    for m, s, d in T:
        if yb <= m: return s
    return 'Ø125'


def q_yb(yb):
    return 0.25 * math.sqrt(yb)        # l/s


def dn_sirk(n_ofis):
    return 'Ø20' if n_ofis <= 4 else ('Ø25' if n_ofis <= 14 else 'Ø32')


# ------------------------------------------------------------------ ısıtma borusu çapı (çelik / PPRC-AL)
def dn_isitma(kw, dT):
    """debi ve hız sınırına göre çelik boru"""
    q = kw / (4.18 * dT) * 3.6          # m³/h
    T = [(0.35, 'DN15', 15.8), (0.75, 'DN20', 21.6), (1.4, 'DN25', 27.2), (2.6, 'DN32', 35.9), (3.8, 'DN40', 41.8),
         (7.0, 'DN50', 53.0), (13.0, 'DN65', 68.8), (20.0, 'DN80', 80.8), (40.0, 'DN100', 105.3)]
    for m, s, d in T:
        if q <= m: return s, round(q, 2)
    return 'DN125', round(q, 2)


# ------------------------------------------------------------------ pis su (TS EN 12056-2, K=0,5 ofis)
def qww(sb, K=0.5):
    return K * math.sqrt(sb)


# ------------------------------------------------------------------ hidrofor + kullanım suyu deposu
def hidrofor(yb_top, h_bina=9.5, z_dep=-3.5):
    Q = q_yb(yb_top) * 3.6               # m³/h (eşzamanlı)
    Hgeo = h_bina - z_dep + 1.5          # depo tabanından en üst armatüre
    Hk = 0.03 * 80                        # yaklaşık sürtünme (80 m kritik hat)
    Halt = Hgeo + Hk + 15.0               # 1,5 bar akma
    Hust = Halt + 10.0                    # frekans konvertörlü: +1,0 bar
    P = Q * Hust / (367 * 0.55)
    Vn = 0.33 * Q * (Hust / 10 + 1) / ((Hust - Halt) / 10 * 20) * 1000      # l, S=20 devreye girme/saat
    return dict(Q=round(Q, 2), Hgeo=round(Hgeo, 1), Halt=round(Halt, 1), Hust=round(Hust, 1), P=round(P, 2),
                Vn=100, adet=2, tip='Frekans konvertörlü çift pompalı paket hidrofor (1 asil + 1 yedek)')


def depo(kisi_ofis=180, l_kisi=30, dukkan=5, l_dukkan=100):
    V = (kisi_ofis * l_kisi + dukkan * l_dukkan) / 1000.0
    return dict(kisi=kisi_ofis, l=l_kisi, dukkan=dukkan, V=round(V, 1), Vsec=math.ceil(V), adet=1)


# ------------------------------------------------------------------ otopark (4 hava değişimi, duman 10 hava değişimi)
def otopark():
    foot = GEO[0]['foot']
    x0, y0, x1, y1 = TESISAT_A
    from shapely.geometry import box
    cik = [box(*TESISAT_A), box(*SIGINAK), box(*SIG_LOBI)]
    # çekirdekler (merdiven + asansör) - üst ve alt
    cik += [box(248203, -453400, 248545, -452164), box(248320, -457000, 248620, -455790)]
    net = foot
    for c in cik: net = net.difference(c)
    A = net.area / 1e4
    V = A * OTOPARK_H
    Qn = 4 * V
    Qd = 10 * V
    Qt = 0.85 * Qn
    Qtd = 0.85 * Qd
    return dict(A=round(A, 1), h=OTOPARK_H, V=round(V), n=4, Qn=round(Qn), nd=10, Qd=round(Qd), Qt=round(Qt),
                Qtd=round(Qtd), poly=net)


def kanal(Q, v):
    """dikdörtgen kanal (h=40 sabit, en 5 cm katı)"""
    A = Q / 3600.0 / v
    h = 0.40 if A < 0.6 else 0.50
    w = math.ceil(A / h / 0.05) * 0.05
    return int(round(w * 100)), int(round(h * 100)), round(Q / 3600 / (w * h), 1)


# ------------------------------------------------------------------ sığınak (TS 3419/3420; kullanıcı: m² ölç, alana göre)
def siginak():
    A = sig_alan()
    kisi = int(A // 1.0)
    h = 2.60
    V = A * h
    qk = 3.0 if 51 <= kisi <= 150 else (1.8 if kisi <= 50 else 4.5)   # m³/h·kişi koruma havası
    Q_koruma = kisi * qk
    Q_normal = max(4 * V, kisi * 6.0)        # barış zamanı (depo/kullanım): 4 hava değişimi
    Q_egzoz = 0.8 * Q_normal                  # +50 Pa iç basınç için
    duman = A > 100
    Q_duman = 10 * V if duman else 0
    return dict(A=round(A, 1), kisi=kisi, h=h, V=round(V, 1), qk=qk, Q_koruma=round(Q_koruma), Q_normal=round(Q_normal),
                Q_egzoz=round(Q_egzoz), duman=duman, Q_duman=round(Q_duman))


# ------------------------------------------------------------------ hepsi
def hesapla():
    R = {}
    R['ofis'] = {}
    for kat in (2, 3):
        for k in OFIS_S1:
            o = ofis_isi(k, kat); o['yi'] = yi_kontrol(o); R['ofis'][(kat, k)] = o
            try:
                import yi as _yi
                oz = _yi.ozet(kat, k)
            except Exception as ex:
                oz = None
            if oz:                                   # mahal bazlı (TS 2164 / örnek şablon) ısı kaybı esas alınır
                o['odalar'], o['Q'] = oz[0], round(oz[1])
                o['wm2'] = round(o['Q'] / max(o['A'], 1), 1); o['yi'] = yi_kontrol(o)
    R['dukkan'] = {nm: dukkan_isi(nm) for nm in DUKKAN_S}
    for nm, d in R['dukkan'].items():
        d['rad'] = dukkan_radyator(d['Q'], 0)
    Qo = sum(o['Q'] for o in R['ofis'].values()) / 1000.0
    Qd = sum(d['Q'] for d in R['dukkan'].values()) / 1000.0
    R['Q_ofis'] = round(Qo, 1); R['Q_dukkan'] = round(Qd, 1)
    R['boyler'] = boyler()
    Qb = R['boyler']['P_serp']
    Qk = (Qo + Qd) * 1.10 + Qb * 0.5          # boyler öncelikli değil; %50 eşzamanlılık
    R['Q_kazan_hesap'] = round(Qk, 1)
    n = 3
    unit = [35, 45, 50, 60, 80, 100, 115, 150]
    u = next(x for x in unit if n * x >= Qk)
    R['kazan'] = dict(adet=n, birim=u, top=n * u, tip='Duvar tipi yoğuşmalı kaskad kazan (doğalgaz)')
    # devreler
    R['devre'] = {}
    for ad, kw, dT in (('OFİS YERDEN ISITMA (45/35 °C, karışım vanalı)', Qo, 10.0),
                       ('DÜKKÂN RADYATÖR (70/50 °C)', Qd, 20.0),
                       ('BOYLER SERPANTİNİ (75/55 °C)', Qb, 20.0)):
        dn, q = dn_isitma(kw, dT)
        R['devre'][ad] = dict(kw=round(kw, 1), dT=dT, q=q, dn=dn)
    # pompa basıncı (yaklaşık): en uzak ofis hattı 120 m gidiş-dönüş + kollektör + kalorimetre
    R['pompa'] = {}
    for ad, d in R['devre'].items():
        L = 260.0 if 'OFİS' in ad else (180.0 if 'DÜKKÂN' in ad else 20.0)
        H = (L * 0.025 + 1.5 + (2.5 if 'OFİS' in ad else 1.0)) * 1.1     # mSS (R=25 mm/m, kalorimetre+vana 1,5, devre/kollektör)
        d['H'] = round(H, 1)
        R['pompa'][ad] = dict(Q=d['q'], H=round(H, 1), P=round(0.002725 * d['q'] * H / 0.5, 2))
    # genleşme: su hacmi (yerden ısıtma 18,5 l/kW, panel 8,3 l/kW, boyler serp + kazan 3 l/kW)
    Vs = 18.5 * Qo + 8.3 * Qd + 3.0 * R['kazan']['top'] + 60
    nT = 0.0224                          # 70 °C
    dV = Vs * nT; Vv = 0.005 * Vs
    Pa = 3.0; Pe = Pa - 0.5; Po = (KOT[4] - KOT[0] + 1.0) / 10.0
    Vn = (Vv + dV) * (Pe + 1) / (Pe - Po)
    R['genlesme'] = dict(Vs=round(Vs), dV=round(dV, 1), Vv=round(Vv, 1), Po=round(Po, 2), Pe=Pe, Vn=round(Vn),
                         Vsec=next(x for x in (50, 80, 100, 150, 200, 300, 500) if x >= Vn))
    # baca (TS EN 13384 ön boyut, pratik F = k·Q/√h)
    Qkcal = R['kazan']['top'] * 860
    hb = KOT[4] - KOT[0] + 1.5
    F = 0.012 * Qkcal / math.sqrt(hb)
    D = math.sqrt(4 * F / math.pi)
    Dsec = next(x for x in (150, 200, 250, 300, 350) if x * x * math.pi / 4 / 100 >= F)
    R['baca'] = dict(Q=Qkcal, h=round(hb, 1), F=round(F), D=round(D, 1), Dsec=Dsec)
    R['gaz'] = dict(Q=round(R['kazan']['top'] * 860 / (8250 * 0.98), 1))
    # kazan dairesi havalandırma (doğalgaz: alt menfez 5 cm²/kW min 300, üst %50)
    alt = max(300, 5 * R['kazan']['top']); ust = alt * 0.5
    R['kd_hava'] = dict(alt=alt, ust=round(ust))
    # temiz su
    s, h = yb_ofis()
    R['yb'] = dict(ofis_soguk=s, ofis_sicak=h, ofis_adet=28, dukkan_soguk=1.0)
    yb_top = 28 * s + 5 * 1.0
    R['yb']['top'] = yb_top
    R['hidrofor'] = hidrofor(yb_top)
    R['depo'] = depo()
    R['otopark'] = otopark()
    R['siginak'] = siginak()
    return R


if __name__ == '__main__':
    R = hesapla()
    for (kat, k), o in sorted(R['ofis'].items()):
        print(o['ad'], o['A'], 'm²', o['Q'], 'W', o['wm2'], 'W/m²', o['yi'])
    for nm, d in R['dukkan'].items():
        print(d['ad'], d['A'], d['Q'], d['wm2'], d['rad'])
    for k in ('Q_ofis', 'Q_dukkan', 'boyler', 'Q_kazan_hesap', 'kazan', 'devre', 'pompa', 'genlesme', 'baca', 'gaz', 'kd_hava', 'yb', 'hidrofor', 'depo', 'siginak'):
        print(k, R[k])
    o = R['otopark']; print('otopark', {k: v for k, v in o.items() if k != 'poly'})
