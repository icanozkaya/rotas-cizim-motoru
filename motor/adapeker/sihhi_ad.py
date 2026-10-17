# -*- coding: utf-8 -*-
"""Adapeker — SIHHİ TESİSAT kat planları + kolon şeması (sihhi2 sembolleri/katmanları, ROTAŞ standart kuralları).

Kurallar: mutfak ve WC giderleri ayrı kolonlarda; pis su kolonu betonarme / M.H. şaftı dışında, ıslak hacim köşesinde;
branşmanlar duvar dibinden kısa; sıcak su daire içinde kombiden; sayaçlar bina girişinde toplu, daire beslemeleri ortak
alandan (kat holü temiz su kolon kutusu) daire kapısı yanından; mutfakta yer süzgeci yok; mimaride depo yeri yok → çatı
deposu 3 m³ (hidrofor yok); SB: WC 10, duş 7, ÇM 4, eviye 4, BM 4, lavabo 2, YS 2.
Çalıştırma: python3 motor/adapeker/sihhi_ad.py
"""
import os, sys, math, json
BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
from ortak_ad import T, PL, mimari_altlik, kat_basligi, antet, KOK, CIKIS, PROJE, M
sys.path.insert(0, os.path.join(KOK, 'motor', 'sihhi2'))
import plan as P2  # noqa  (yalnız belge/katman/sembol tanımları)

L_PIS, L_SOG, L_SIC = P2.L_PIS, P2.L_SOG, P2.L_SIC
L_PCAP, L_TCAP, SMB = P2.L_PCAP, P2.L_TCAP, 'ROTAS-SIHHI-SEMBOL'
L_SEB = 'ROTAS-SIHHI-SEBEKE'
SB = {'LV': 2, 'WC': 10, 'DUS': 7, 'EV': 4, 'CM': 4, 'BM': 4, 'YS': 2}
MB = {'LV': 0.75, 'WC': 0.5, 'DUS': 2.5, 'EV': 1.0, 'CM': 1.5, 'BM': 1.5, 'KOMBI': 0.5}

# ------------------------------------------------------------------ TİP DAİRE GÜZERGÂHLARI (D1 zemin, cm)
# pis su: (çizgi noktaları, çap, SB etiketi, etiket parçası indeksi)
PIS = [
    ('P1', [(-276, -2206), (-278, -2226)], 'Ø100', '10 SB', (-352, -2196)),                   # klozet (etiket solda)
    ('P1', [(-282, -2298), (-282, -2254), (-280, -2246)], 'Ø50', '7 SB'),                      # duş
    ('P1', [(-372, -2066), (-404, -2066), (-404, -2236), (-340, -2236)], 'Ø50', '2 SB'),        # lavabo -> süzgeç
    ('P1', [(-340, -2236), (-288, -2236)], 'Ø50', '4 SB'),                                     # süzgeç -> kolon
    ('P2', [(-164, -2124), (-162, -2118)], 'Ø100', '10 SB', (-218, -2100)),                    # klozet 2
    ('P2', [(-252, -1983), (-255, -1983), (-255, -1990)], 'Ø50', '2 SB'),                       # lavabo 2
    ('P2', [(-282, -1990), (-255, -1990)], 'Ø50', '4 SB'),                                     # çamaşır makinesi
    ('P2', [(-255, -1990), (-255, -2126), (-160, -2126), (-157, -2124)], 'Ø50', '6 SB'),        # -> kolon (klozet arkası)
    ('P3', [(-282, -2670), (-275, -2663), (-275, -2650)], 'Ø50', '4 SB'),                      # eviye
    ('P3', [(-282, -2728), (-282, -2670)], 'Ø50', '4 SB'),                                     # bulaşık makinesi
]
YS = [(-340, -2236)]
# temiz su: soğuk / sıcak yolları (sıcak kombiden). Duvar içi düşeyler x -255 / -249; 40/40 kolonların
# (x -279..-239, y -2403..-2363 ve -2898..-2858) çevresinden dolaşır.
SOG = [
    [(-255, -2448), (-255, -2850), (-318, -2850), (-318, -2885)],          # giriş -> mutfak -> kombi (balkon)
    [(-255, -2690), (-280, -2690)],                                        # eviye
    [(-255, -2735), (-276, -2735)],                                        # bulaşık mak.
    [(-255, -2448), (-255, -2418), (-293, -2418), (-293, -2346), (-255, -2346), (-255, -2180), (-306, -2180),
     (-306, -2062), (-372, -2062)],   # banyo 1 (asansör perdesinin batısından)
    [(-255, -2298), (-266, -2298)],                                        # duş
    [(-255, -2206), (-266, -2206)],                                        # klozet rezervuarı
    [(-306, -2062), (-306, -2036), (-268, -2036), (-268, -1946), (-150, -1946), (-150, -2090)],   # çamaşır duvarı -> banyo 2 -> klozet 2
    [(-268, -1975), (-247, -1975)],                                        # lavabo 2
    [(-268, -1996), (-290, -1996)],                                        # çamaşır makinesi
]
SIC = [
    [(-310, -2885), (-310, -2856), (-249, -2856), (-249, -2412), (-287, -2412), (-287, -2352), (-249, -2352),
     (-249, -2174), (-300, -2174), (-300, -2042), (-262, -2042), (-262, -1969), (-247, -1969)],   # kombi -> banyo 1 -> lavabo 2
    [(-300, -2056), (-366, -2056)],                                                 # lavabo 1
    [(-249, -2697), (-280, -2697)],                                                 # eviye
    [(-249, -2304), (-266, -2304)],                                                 # duş
]
TS_ETIKET = [  # (nokta, yön 'Y'/'D', C1, M1)
    ((-255, -2560), 'D', '1 1/4"', '9.5 MB'), ((-255, -2160), 'D', '1"', '6.5 MB'), ((-200, -1946), 'Y', '1/2"', '0.5 MB'),
    ((-300, -2875), 'Y', '1/2"', '0.5 MB'), ((-249, -2780), 'D', '3/4"', '5 MB')]
VANA = [(-280, -2690), (-276, -2735), (-266, -2298), (-266, -2206), (-372, -2062), (-247, -1975), (-290, -1996),
        (-150, -2090), (-318, -2885)]
ASP = [((-305, -2133), (-400, -2112)), ((-240, -2110), (-226, -1958))]   # (sembol, not yeri)
GIRIS = (-255, -2448)
KUTU = {'D1': (-236, -2392)}           # kat holü temiz su kolon kutusu (D2 aynası)
SAYAC0 = (-20.0, -2770.0)              # zemin: bina girişi sahanlığında sayaç grubu (6 sayaç, aşağı doğru 16 cm)
SEBEKE = (-20.0, -3150.0)             # 10 m'lik yoldan (güney) bina girişine


def tr(p, d, k):
    return M.donustur(p, d, k)


def cizgi(m, pts, lay, d, k, w=0.0):
    return m.add_lwpolyline([tr(p, d, k) for p in pts], dxfattribs={'layer': lay, 'const_width': w})


def ps_etiket(m, pts, cap, sb, d, k):
    """pis su etiketi: en uzun parçanın ortası, hat üstünde (kullanıcı bloğu ROTAS-S2-PS-CAP-U)"""
    best = max(range(len(pts) - 1), key=lambda i: math.dist(pts[i], pts[i + 1]))
    a, b = tr(pts[best], d, k), tr(pts[best + 1], d, k)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    yatay = abs(b[0] - a[0]) >= abs(b[1] - a[1])
    ad = 'ROTAS-S2-PS-CAP-U' if (d == 'D1') else 'ROTAS-S2-PS-CAP-UL'
    P2.ekle_insert(m, ad, (mx, my), L_PCAP, rot=0.0 if yatay else 90.0, attr={'CAP': cap, 'SB': sb})


def daire_ciz(m, d, k, ns):
    for kayit in PIS:
        no, pts, cap, sb = kayit[:4]
        cizgi(m, pts, L_PIS, d, k)
        if len(kayit) > 4:
            q = tr(kayit[4], d, k)
            P2.ekle_insert(m, 'ROTAS-S2-PS-CAP-U' if d == 'D1' else 'ROTAS-S2-PS-CAP-UL', q, L_PCAP, attr={'CAP': cap, 'SB': sb})
            m.add_line(q, tr(pts[0], d, k), dxfattribs={'layer': 'ROTAS-SEMBOL-KILAVUZ'})
        elif math.dist(pts[0], pts[-1]) > 12:
            ps_etiket(m, pts, cap, sb, d, k)
    for p in YS:
        P2.ekle_insert(m, 'ROTAS-S2-YER-SUZGECI', tr(p, d, k), SMB)
    for no, c in M.TIP_KOLON.items():
        gno = ns[no]
        P2.ekle_insert(m, 'ROTAS-S2-PIS-KOLON', tr(c, d, k), SMB, attr={'NO': gno})
        ofs = {'P1': (-30, -50), 'P2': (-5, 48), 'P3': (-62, 0)}[no]
        bx, by = tr((c[0] + ofs[0], c[1] + ofs[1]), d, k)
        P2.ekle_insert(m, 'ROTAS-S2-KOLON-NO', (bx, by), 'ROTAS-SIHHI-KOLON-NO', attr={'NO': gno})
        m.add_line(tr(c, d, k), (bx, by), dxfattribs={'layer': 'ROTAS-SEMBOL-KILAVUZ'})
    for pts in SOG:
        cizgi(m, pts, L_SOG, d, k)
    for pts in SIC:
        cizgi(m, pts, L_SIC, d, k)
    for v in VANA:
        P2.ekle_insert(m, 'ROTAS-S2-KURESEL-VANA', tr(v, d, k), SMB)
    for p, yon, c1, m1 in TS_ETIKET:
        q = tr(p, d, k)
        P2.ekle_insert(m, 'ROTAS-S2-TS-CAP2', (q[0] + (8 if d == 'D1' else -40), q[1]), L_TCAP,
                       rot=90.0 if yon == 'D' else 0.0, attr={'C1': c1, 'M1': m1})
    P2.ekle_insert(m, 'ROTAS-S2-TEMIZ-GIRIS', tr(GIRIS, d, k), SMB)
    for p, tp in ASP:
        q = tr(p, d, k)
        P2.ekle_insert(m, 'ROTAS-S2-ASPIRATOR', q, 'ROTAS-SIHHI-HAVALANDIRMA-SEMBOL', olcek=0.6)
        t = tr(tp, d, k)
        for i, s_ in enumerate(('Wc Aspiratörü', '80 m3/h-50 pa', 'Ø150 mm (M.H.)')):
            T(m, t[0], t[1] - i * 9, s_, 7, 'TL' if d == 'D1' else 'TR', 'ROTAS-SIHHI-HAVALANDIRMA-YAZI')
    # kombi
    kq = tr(M.KOMBI, d, k)
    T(m, kq[0], kq[1] - 28, 'KOMBİ 24 kW (sıcak su daire içinden)', 7, 'TC', 'ROTAS-SIHHI-CIHAZ-YAZI')
    # daire besleme: kolon kutusu -> daire girişi
    kx, ky = KUTU['D1']
    cizgi(m, [(kx, ky), (kx, -2440), (GIRIS[0], -2440), GIRIS], L_SOG, d, k)
    q = tr((kx, ky), d, k)
    m.add_lwpolyline([(q[0] - 9, q[1] - 9), (q[0] + 9, q[1] - 9), (q[0] + 9, q[1] + 9), (q[0] - 9, q[1] + 9)], close=True,
                     dxfattribs={'layer': SMB})
    T(m, q[0], q[1] + 14, 'TEMİZ SU KOLON KUTUSU', 6, 'BC', 'ROTAS-SIHHI-CIHAZ-YAZI')


def zemin_sayac(m):
    """bina girişinde toplu sayaç grubu + şebeke girişi + daire beslemeleri (döşeme altından) kolon kutularına"""
    k = 'Z'
    sx, sy = SAYAC0
    m.add_lwpolyline([SEBEKE, (SEBEKE[0], -2900), (sx, -2900), (sx, sy - 6 * 16 - 10)], dxfattribs={'layer': L_SEB, 'const_width': 2})
    T(m, SEBEKE[0] + 10, SEBEKE[1] + 20, 'ŞEBEKEDEN (SASKİ) Ø32 PE - ANA VANA + SAYAÇ', 9, 'BL', 'ROTAS-SIHHI-CIHAZ-YAZI')
    m.add_lwpolyline([(sx - 15, sy + 12), (sx + 15, sy + 12), (sx + 15, sy - 6 * 16 - 10), (sx - 15, sy - 6 * 16 - 10)], close=True,
                     dxfattribs={'layer': SMB})
    T(m, sx - 20, sy - 50, 'SAYAÇ GRUBU (6 AD.)', 8, 'MR', 'ROTAS-SIHHI-CIHAZ-YAZI', rot=0)
    for i in range(6):
        y = sy - i * 16
        P2.ekle_insert(m, 'ROTAS-S2-KURESEL-VANA', (sx, y), SMB)
        dno = 'D%d' % (i + 1)
        T(m, sx + 20, y, dno, 7, 'ML', 'ROTAS-SIHHI-CIHAZ-YAZI')
    # D1/D3/D5 -> sol kutu ; D2/D4/D6 -> sağ kutu (döşeme altından, merdiven boşluğu altından)
    for d, xs in (('D1', [-236, -230, -224]), ('D2', [M.ayna_x(-236), M.ayna_x(-230), M.ayna_x(-224)])):
        for j, x in enumerate(xs):
            yk = M.KUTU_Y if hasattr(M, 'KUTU_Y') else -2392
            yy = sy - (2 * j + (0 if d == 'D1' else 1)) * 16
            m.add_lwpolyline([(sx, yy), (sx - 30 - 6 * j if d == 'D1' else sx + 30 + 6 * j, yy),
                              (sx - 30 - 6 * j if d == 'D1' else sx + 30 + 6 * j, -2540 + 6 * j), (x, -2540 + 6 * j), (x, -2392)],
                             dxfattribs={'layer': L_SEB})


def kolon_semasi(m, x0, y0, ns_hepsi):
    """SIHHİ TESİSAT KOLON ŞEMASI (kat bantları, sayaç grubu zemin bandı solunda, depo en üst solda)"""
    BH = 300.0
    katlar = ['Z', '1', '2']
    W = 4200.0
    lay, ly = 'ROTAS-PAFTA', 'ROTAS-PAFTA-YAZI'
    T(m, x0, y0 + 4 * BH + 380, 'SIHHİ TESİSAT KOLON ŞEMASI', 34, 'BL', ly)
    T(m, x0, y0 + 4 * BH + 340, 'ÖLÇEKSİZ', 20, 'BL', ly)
    for i in range(4):
        y = y0 + i * BH
        m.add_lwpolyline([(x0, y), (x0 + W, y)], dxfattribs={'layer': 'ROTAS-PAFTA-YAZI'})
        if i < 3:
            T(m, x0 + 25, y + BH / 2, M.KAT_ADI[katlar[i]], 16, 'MC', ly, rot=90)
    T(m, x0 + 25, y0 + 3 * BH + 120, 'ÇATI', 16, 'MC', ly, rot=90)
    m.add_lwpolyline([(x0, y0 - 120), (x0 + W, y0 - 120)], dxfattribs={'layer': 'ROTAS-PAFTA-YAZI'})
    T(m, x0 + 25, y0 - 60, 'TEMEL', 12, 'MC', ly, rot=90)
    # depo (çatı) + dikmeler
    dx = x0 + 120
    dy = y0 + 3 * BH + 60
    m.add_lwpolyline([(dx, dy), (dx + 260, dy), (dx + 260, dy + 150), (dx, dy + 150)], close=True, dxfattribs={'layer': SMB})
    T(m, dx + 130, dy + 90, 'KULLANMA SUYU DEPOSU', 11, 'MC', 'ROTAS-SIHHI-CIHAZ-YAZI')
    T(m, dx + 130, dy + 65, 'V = 3 m³ (çatıda, hidroforsuz)', 9, 'MC', 'ROTAS-SIHHI-CIHAZ-YAZI')
    T(m, dx + 130, dy + 45, 'havalık - taşma - boşaltma - seviye gös.', 7, 'MC', 'ROTAS-SIHHI-CIHAZ-YAZI')
    # şebeke + sayaç grubu (zemin bandı solu)
    sx, sy = x0 + 120, y0 + 60
    m.add_lwpolyline([(x0 + 60, y0 - 80), (sx, y0 - 80), (sx, sy)], dxfattribs={'layer': L_SOG, 'const_width': 2})
    T(m, x0 + 60, y0 - 95, 'ŞEBEKEDEN Ø32', 9, 'TL', 'ROTAS-SIHHI-CIHAZ-YAZI')
    # depo dolum / dönüş dikmeleri
    for j, (xx, ad) in enumerate(((sx + 20, 'DEPO DOLUM 1"'), (sx + 40, 'DEPO DÖNÜŞ 1 1/4"'))):
        m.add_lwpolyline([(xx, sy), (xx, dy)], dxfattribs={'layer': L_SOG})
        T(m, xx - 4, y0 + 2 * BH + 150 - 60 * j, ad, 8, 'BR', L_TCAP, rot=90)
    m.add_lwpolyline([(sx, sy), (sx + 40, sy)], dxfattribs={'layer': L_SOG})
    # sayaçlar
    for i in range(6):
        xx = sx + 90 + i * 60
        k = 'Z12'[i // 2] if False else ['Z', 'Z', '1', '1', '2', '2'][i]
        dno = 'D%d' % (i + 1)
        m.add_circle((xx, sy + 30), 9, dxfattribs={'layer': SMB})
        m.add_line((xx - 9, sy + 30), (xx + 9, sy + 30), dxfattribs={'layer': SMB})
        m.add_lwpolyline([(sx + 40, sy), (xx, sy), (xx, sy + 21)], dxfattribs={'layer': L_SOG})
        ky = y0 + katlar.index(k) * BH + 150
        m.add_lwpolyline([(xx, sy + 39), (xx, ky), (xx + 30, ky)], dxfattribs={'layer': L_SOG})
        T(m, xx + 32, ky + 4, dno + ' 1 1/4" 9.5 MB', 7, 'BL', L_TCAP)
    T(m, sx + 90, sy - 30, 'SAYAÇ GRUBU (bina girişi, 6 adet DN25)', 9, 'TL', 'ROTAS-SIHHI-CIHAZ-YAZI')
    # pis su kolonları: 6 kolon (D1 tarafı P1-P3, D2 tarafı P4-P6)
    grup = {'P1': ('WC+DUŞ+LV+YS', 21), 'P2': ('WC+LV+ÇM', 16), 'P3': ('EVİYE+BM', 8)}
    kx = x0 + 700
    for d in ('D1', 'D2'):
        for no in ('P1', 'P2', 'P3'):
            gno = ns_hepsi[d][no]
            cap_k = 'Ø100' if no != 'P3' else 'Ø70'
            m.add_lwpolyline([(kx, y0 - 100), (kx, y0 + 3 * BH + 50)], dxfattribs={'layer': L_PIS, 'const_width': 2})
            m.add_lwpolyline([(kx - 8, y0 + 3 * BH + 50), (kx + 8, y0 + 3 * BH + 50)], dxfattribs={'layer': L_PIS})
            T(m, kx, y0 + 3 * BH + 60, 'HAVALIK (çatıdan +50)', 7, 'BC', 'ROTAS-SIHHI-CIHAZ-YAZI')
            P2.ekle_insert(m, 'ROTAS-S2-KOLON-NO', (kx, y0 + 3 * BH + 150), 'ROTAS-SIHHI-KOLON-NO', attr={'NO': gno})
            ar, sb = grup[no]
            for i, k in enumerate(katlar):
                yb = y0 + i * BH + 60
                m.add_lwpolyline([(kx, yb + 20), (kx + 25, yb), (kx + 160, yb)], dxfattribs={'layer': L_PIS})
                T(m, kx + 30, yb + 5, '%s - %s' % (M.daire_no(d, k), ar), 7, 'BL', L_PCAP)
                T(m, kx + 30, yb - 4, '%s / %d SB' % ('Ø100' if no != 'P3' else 'Ø50', sb), 7, 'TL', L_PCAP)
            T(m, kx - 6, y0 + 1.5 * BH, '%s %s / %d SB' % (gno, cap_k, 3 * sb), 9, 'BC', L_PCAP, rot=90)
            # taban: temizleme kapağı + rögar
            m.add_lwpolyline([(kx, y0 - 100), (kx + 60, y0 - 100)], dxfattribs={'layer': L_PIS})
            T(m, kx + 62, y0 - 100, 'TK → R (Ø125 %1)', 7, 'ML', 'ROTAS-SIHHI-CIHAZ-YAZI')
            kx += 300
    # hesap kutusu
    hx, hy = x0 + W - 520, y0 + 3 * BH + 40
    m.add_lwpolyline([(hx, hy), (hx + 500, hy), (hx + 500, hy + 280), (hx, hy + 280)], close=True, dxfattribs={'layer': 'ROTAS-PAFTA', 'color': 1})
    satir = ['DAİRE YÜKLERİ (TS 1258 / TS EN 12056-2)',
             'LV 2x0,75 + WC 2x0,5 + DUŞ 2,5 + EV 1,0 + BM 1,5 + ÇM 1,5 + KOMBİ 0,5 = 9,5 MB → 1 1/4"',
             'BİNA 6 x 9,5 = 57 MB → depo dönüş / ana hat 1 1/2"',
             'P1: WC 10 + DUŞ 7 + LV 2 + YS 2 = 21 SB/kat → 63 SB Ø100',
             'P2: WC 10 + LV 2 + ÇM 4 = 16 SB/kat → 48 SB Ø100',
             'P3: EV 4 + BM 4 = 8 SB/kat → 24 SB Ø70 (mutfak ayrı kolon)',
             'Kolon → rögar Ø125 %1, rögar arası Ø150 %1',
             'Depo: 6 daire ≤ 10 → 3 m³ çatı deposu (hidrofor yok)']
    for i, s in enumerate(satir):
        T(m, hx + 12, hy + 260 - i * 31, s, 9 if i else 11, 'TL', 'ROTAS-PAFTA-YAZI')
    return y0 - 200


def lejant_notlar(m, x, y):
    L = 'ROTAS-PAFTA-YAZI'
    T(m, x, y, 'LEJANT', 20, 'BL', L)
    sat = [(L_PIS, 'PİS SU HATTI (Ø50 / Ø70 / Ø100 PVC)'), (L_SOG, 'SOĞUK SU HATTI (PPR)'), (L_SIC, 'SICAK SU HATTI (PPR, kombiden)'),
           (L_SEB, 'ŞEBEKE / DAİRE BESLEME (döşeme altı)')]
    yy = y - 30
    for lay, s in sat:
        m.add_line((x, yy + 4), (x + 100, yy + 4), dxfattribs={'layer': lay})
        T(m, x + 115, yy, s, 9, 'BL', L)
        yy -= 25
    for ad, s in (('ROTAS-S2-PIS-KOLON', 'PİS SU KOLONU'), ('ROTAS-S2-YER-SUZGECI', 'YER SÜZGECİ'),
                  ('ROTAS-S2-KURESEL-VANA', 'KÜRESEL VANA (armatür ara musluğu)'), ('ROTAS-S2-ASPIRATOR', 'WC ASPİRATÖRÜ')):
        P2.ekle_insert(m, ad, (x + 50, yy + 4), SMB)
        T(m, x + 115, yy, s, 9, 'BL', L)
        yy -= 30
    yy -= 20
    T(m, x, yy, 'NOTLAR', 20, 'BL', L)
    notlar = ['1- Pis su tesisatı PVC (TS EN 1329), branşman eğimleri %2, kolonlar çatıdan 50 cm havalık olarak çıkarılacaktır.',
              '2- Mutfak giderleri (P3 / P6) ayrı kolondan indirilecek, mutfağa yer süzgeci konmayacaktır.',
              '3- Kolon dipleri temel seviyesinde temizleme kapaklı olarak Ø125 %1 eğimle bina dışı rögarlara bağlanacaktır.',
              '4- Temiz su tesisatı PPR (PN20), sıcak su her dairede kombiden başlayacak, sıcak hatlar yalıtılacaktır.',
              '5- Su sayaçları bina girişinde toplu olacak; daire beslemeleri döşeme altından kat holündeki kolon kutularına (D1-D3-D5 / D2-D4-D6), oradan daire girişine verilecektir.',
              '6- Penceresiz banyolardaki WC aspiratörleri mekanik havalandırma (M.H.) şaftına bağlanacaktır.',
              '7- Kullanma suyu deposu çatıda 3 m³ olup taşma ve boşaltma uçları açık bırakılmayacaktır.',
              '8- Tesisat 10 bar basınçla test edilecek, dezenfekte edilerek kullanıma verilecektir.']
    yy -= 30
    for s in notlar:
        T(m, x, yy, s, 9, 'BL', L)
        yy -= 20
    return yy


def numaralar():
    ns = {}
    say = 0
    for d in ('D1', 'D2'):
        ns[d] = {}
        for no in ('P1', 'P2', 'P3'):
            say += 1
            ns[d][no] = 'P%d' % say
    return ns


def main():
    doc = P2.belge()
    for ad, renk in ((L_SEB, 5),):
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk, linetype='DASHED' if 'DASHED' in doc.linetypes else 'Continuous')
    for ad in ('ROTAS-MIMARI-KOLON',):
        if ad not in doc.layers:
            doc.layers.add(ad, color=8)
    if 'ROTAS' not in doc.styles:
        doc.styles.add('ROTAS', font='arial.ttf')
    m = doc.modelspace()
    mimari_altlik(m)
    ns = numaralar()
    for k in ('Z', '1', '2'):
        for d in ('D1', 'D2'):
            daire_ciz(m, d, k, ns[d])
        kat_basligi(m, k, 'SIHHİ TESİSAT PLANI')
    zemin_sayac(m)
    yk = kolon_semasi(m, M.W0[0], -5100, ns)
    lejant_notlar(m, M.W0[0] + 4400, -3800)
    antet(m, M.W0[0] + 6700, -5300, 'SIHHİ TESİSAT (TEMİZ SU - PİS SU)')
    os.makedirs(CIKIS, exist_ok=True)
    yol = os.path.join(CIKIS, 'ADAPEKER_SIHHI_TESISAT.dxf')
    doc.saveas(yol)
    json.dump(dict(kolonlar={d: {no: dict(gno=g, xy=M.donustur(M.TIP_KOLON[no], d, 'Z')) for no, g in v.items()} for d, v in ns.items()}),
              open(os.path.join(CIKIS, 'sihhi_model.json'), 'w'), ensure_ascii=False, indent=1)
    print('kaydedildi', yol)


if __name__ == '__main__':
    main()
