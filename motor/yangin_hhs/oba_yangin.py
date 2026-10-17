# -*- coding: utf-8 -*-
"""OBA 84 parsel depolama binası — YANGIN TESİSATI (HHS sprinkler + yangın dolabı + hidrant + pompa/depo).

Çıktı: proje/oba_84_parsel_yangin/OBA_84_YANGIN_TESISATI.dxf (mimari koordinatlarında, cm)
Çalıştırma: python3 motor/yangin_hhs/oba_yangin.py
"""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ciz_ortak import yeni_doc, C, RS, tr, mimari_altlik, import_dxf, pafta_cerceve, KOK
import oba_veri as V
from oba_veri import AX, AY, X0, X1, Y0, Y1, BR_X, BAS_Y, Y_AB, Y_AC, X_F, POMPA, DUV, TASARIM

CIKTI = os.path.join(KOK, 'proje', 'oba_84_parsel_yangin')
KAT = {
    'ROTAS-MIMARI': (8, 'CONTINUOUS'), 'ROTAS-MIMARI-KOLON': (8, 'CONTINUOUS'), 'ROTAS-MIMARI-AKS': (8, 'CONTINUOUS'),
    'ROTAS-MIMARI-YAZI': (8, 'CONTINUOUS'),
    'ROTAS-YANGIN-SPR-BORU': (1, 'CONTINUOUS'), 'ROTAS-YANGIN-SPR-ANA': (1, 'CONTINUOUS'),
    'ROTAS-YANGIN-SPR-GOMULU': (1, 'DASHED'), 'ROTAS-YANGIN-BASLIK': (1, 'CONTINUOUS'),
    'ROTAS-YANGIN-CAP': (2, 'CONTINUOUS'), 'ROTAS-YANGIN-SEMBOL': (1, 'CONTINUOUS'),
    'ROTAS-YANGIN-DOLAP-BORU': (30, 'CONTINUOUS'), 'ROTAS-YANGIN-DOLAP': (30, 'CONTINUOUS'),
    'ROTAS-YANGIN-DOLAP-ETKI': (9, 'DASHED'),
    'ROTAS-YANGIN-HIDRANT-BORU': (4, 'DASHED'), 'ROTAS-YANGIN-HIDRANT': (4, 'CONTINUOUS'),
    'ROTAS-YANGIN-ALAN': (6, 'CONTINUOUS'), 'ROTAS-YANGIN-ZON': (3, 'DASHDOT'),
    'ROTAS-YANGIN-YAZI': (7, 'CONTINUOUS'), 'ROTAS-YANGIN-POMPA-DAIRESI': (7, 'CONTINUOUS'),
    'ROTAS-YANGIN-TARAMA': (8, 'CONTINUOUS'), 'ROTAS-YANGIN-OLCU': (3, 'CONTINUOUS'),
    'ROTAS-SEMA': (1, 'CONTINUOUS'), 'ROTAS-SEMA-YAZI': (7, 'CONTINUOUS'), 'ROTAS-SEMA-HIDRANT': (4, 'CONTINUOUS'),
    'ROTAS-SEMA-DOLAP': (30, 'CONTINUOUS'), 'ROTAS-SEMA-DEPO': (8, 'CONTINUOUS'),
    'ROTAS-HESAP-CIZGI': (8, 'CONTINUOUS'), 'ROTAS-HESAP-YAZI': (7, 'CONTINUOUS'), 'ROTAS-HESAP-BASLIK': (2, 'CONTINUOUS'),
    'ROTAS-NOT': (7, 'CONTINUOUS'), 'ROTAS-LEJANT': (7, 'CONTINUOUS'), 'ROTAS-PAFTA': (7, 'CONTINUOUS'),
    'ROTAS-DETAY': (7, 'CONTINUOUS'), 'ROTAS-DETAY-BORU': (1, 'CONTINUOUS'), 'ROTAS-DETAY-YAZI': (7, 'CONTINUOUS'),
}
SP, SA, SG, BAS, CAP, SMB = ('ROTAS-YANGIN-SPR-BORU', 'ROTAS-YANGIN-SPR-ANA', 'ROTAS-YANGIN-SPR-GOMULU',
                             'ROTAS-YANGIN-BASLIK', 'ROTAS-YANGIN-CAP', 'ROTAS-YANGIN-SEMBOL')
DB, DL, HB, HD, YZ = ('ROTAS-YANGIN-DOLAP-BORU', 'ROTAS-YANGIN-DOLAP', 'ROTAS-YANGIN-HIDRANT-BORU',
                      'ROTAS-YANGIN-HIDRANT', 'ROTAS-YANGIN-YAZI')
PD = 'ROTAS-YANGIN-POMPA-DAIRESI'
METRAJ = {}


def met(ad, L):
    METRAJ[ad] = METRAJ.get(ad, 0.0) + L / 100.0


# ================================================================== özel bloklar (saf geometri)
def bloklar(doc):
    b = doc.blocks.new('ROTAS-SMB-SPR-DIK')               # dik (upright) sprinkler: daire + dolu merkez + deflektör
    b.add_circle((0, 0), 12, dxfattribs={'layer': '0'})
    h = b.add_hatch(dxfattribs={'layer': '0'}); h.set_solid_fill(color=256)
    h.paths.add_polyline_path([(4 * math.cos(a / 8 * math.tau), 4 * math.sin(a / 8 * math.tau)) for a in range(8)], is_closed=True)
    b.add_line((-16, 0), (-12, 0), dxfattribs={'layer': '0'}); b.add_line((12, 0), (16, 0), dxfattribs={'layer': '0'})
    b = doc.blocks.new('ROTAS-SMB-HIDRANT')               # yer üstü hidrant: daire + 3 ağız
    b.add_circle((0, 0), 35, dxfattribs={'layer': '0'}); b.add_circle((0, 0), 22, dxfattribs={'layer': '0'})
    for a in (0, 90, 180):
        r = math.radians(a)
        b.add_lwpolyline([(35 * math.cos(r) - 9 * math.sin(r), 35 * math.sin(r) + 9 * math.cos(r)),
                          (52 * math.cos(r) - 9 * math.sin(r), 52 * math.sin(r) + 9 * math.cos(r)),
                          (52 * math.cos(r) + 9 * math.sin(r), 52 * math.sin(r) - 9 * math.cos(r)),
                          (35 * math.cos(r) + 9 * math.sin(r), 35 * math.sin(r) - 9 * math.cos(r))], dxfattribs={'layer': '0'})
    h = b.add_hatch(dxfattribs={'layer': '0'}); h.set_solid_fill(color=256)
    h.paths.add_polyline_path([(22 * math.cos(a / 12 * math.tau), 22 * math.sin(a / 12 * math.tau)) for a in range(12)], is_closed=True)
    b = doc.blocks.new('ROTAS-SMB-DOLAP-PLAN')            # yangın dolabı (plan): kabin + makara
    b.add_lwpolyline([(0, -40), (25, -40), (25, 40), (0, 40)], close=True, dxfattribs={'layer': '0'})
    b.add_circle((12.5, 0), 10, dxfattribs={'layer': '0'}); b.add_line((0, -40), (25, 40), dxfattribs={'layer': '0'})
    b = doc.blocks.new('ROTAS-SMB-HORTUM-DOLABI')         # hidrant hortum dolabı (plan)
    b.add_lwpolyline([(-30, -20), (30, -20), (30, 20), (-30, 20)], close=True, dxfattribs={'layer': '0'})
    b.add_line((-30, -20), (30, 20), dxfattribs={'layer': '0'}); b.add_line((-30, 20), (30, -20), dxfattribs={'layer': '0'})
    b = doc.blocks.new('ROTAS-SMB-KOLON-YUK')             # sprinkler yükselen kolon (plan)
    b.add_circle((0, 0), 20, dxfattribs={'layer': '0'}); b.add_circle((0, 0), 12, dxfattribs={'layer': '0'})
    b.add_line((-20, 0), (20, 0), dxfattribs={'layer': '0'}); b.add_line((0, -20), (0, 20), dxfattribs={'layer': '0'})
    b = doc.blocks.new('ROTAS-SMB-POMPA-SEMA')            # pompa (şema): daire + üçgen
    b.add_circle((0, 0), 30, dxfattribs={'layer': '0'})
    b.add_lwpolyline([(-18, -24), (28, 0), (-18, 24)], dxfattribs={'layer': '0'})


def ins(c, ad, x, y, lay, aci=0.0, s=1.0):
    return c.m.add_blockref(ad, (x, y), dxfattribs={'layer': lay, 'rotation': aci, 'xscale': s, 'yscale': s})


# ================================================================== PLAN
def plan_sprinkler(c, S):
    say = 0
    for zon in (1, 2):
        xf = X_F[zon]
        for ad, ya in (('C', Y_AC), ('B', Y_AB)):
            xs = V.ZON_BR[zon]
            xu = max(xs) if zon == 2 else min(xs)
            # ana dağıtım (DN150)
            c.L((xf, ya), (xu, ya), SA, 6)
            met('DN150', abs(xu - xf))
            for k in range(1, 4):
                xm = xf + (xu - xf) * (k / 4) + (150 if zon == 1 else -150) * 0
                c.T(xm + 20 * 0, ya + 14, 'DN150', 14, 'BC', CAP)
            # uç test ve drenaj
            c.SMB('test_drenaj', xu + (-40 if zon == 1 else 40), ya, 180 if zon == 1 else 0, 2.0)
            c.T(xu + (-40 if zon == 1 else 40), ya - 40, 'UÇ TEST-DRENAJ DN50', 11, 'TR' if zon == 1 else 'TL', YZ)
            for xb in xs:
                ust = sorted(y for y in V.bolge(ad) if y > ya)
                alt = sorted((y for y in V.bolge(ad) if y < ya), reverse=True)
                for ys in (ust, alt):
                    n = len(ys)
                    p = ya
                    gruplar = {}
                    for k, yh in enumerate(ys):
                        dn = V.dn_br(n - k)
                        c.L((xb, p), (xb, yh), SP)
                        met(f'DN{dn}', abs(yh - p))
                        gruplar.setdefault(dn, []).append((p, yh))
                        ins(c, 'ROTAS-SMB-SPR-DIK', xb, yh, BAS)
                        say += 1
                        p = yh
                    for dn, segs in gruplar.items():
                        sg = segs[len(segs) // 2]
                        ym = (sg[0] + sg[1]) / 2
                        c.T(xb + 16, ym, f'DN{dn}', 10, 'MC', CAP, rot=90)
                # te (ana dağıtım üstünde)
                c.m.add_circle((xb, ya), 5, dxfattribs={'layer': SA})
    return say


def plan_besleme(c):
    """pompa dairesi → zon besleme hatları (gömülü DN200) → bina içi kolon → çatı altı besleme"""
    for zon in (1, 2):
        xf = X_F[zon]
        yk = Y1 - 60
        c.L((xf, POMPA[1] - DUV), (xf, Y1 + V.CEP), SG, 6)
        met('DN200 (gömülü)', POMPA[1] - DUV - Y1 - V.CEP)
        c.L((xf, Y1 + V.CEP), (xf, yk), SA, 6)
        ins(c, 'ROTAS-SMB-KOLON-YUK', xf, yk, SMB, s=1.5)
        c.L((xf, yk), (xf, Y_AB), SA, 8)
        met('DN200', (yk - Y_AB) + 1200 + 150)
        c.T(xf + (-45 if zon == 1 else 45), yk - 20, f'SK-{zon}', 18, 'TR' if zon == 1 else 'TL', YZ)
        c.T(xf + (-45 if zon == 1 else 45), yk - 45, 'DN200 KOLON', 12, 'TR' if zon == 1 else 'TL', CAP)
        for ym in ((Y_AC + yk) / 2, (Y_AB + Y_AC) / 2):
            c.T(xf + (-14 if zon == 1 else 14), ym, 'DN200', 14, 'MC', CAP, rot=90)
        c.T(xf + (-14 if zon == 1 else 14), (POMPA[1] + Y1) / 2 + 150, f'DN200 GÖMÜLÜ (ZON-{zon})', 11, 'MC', CAP, rot=90)
    # zon sınırı
    c.L((AX[12], Y0 - 120), (AX[12], Y1 + 120), 'ROTAS-YANGIN-ZON', 3)
    for zon, xm in ((1, (X0 + AX[12]) / 2), (2, (AX[12] + X1) / 2)):
        alan = (AX[12] - X0) * (Y1 - Y0) / 1e4
        c.T(xm, Y1 - 260, f'SPRİNKLER ZON-{zon}  (ALARM VANASI AV-{zon})', 30, 'MC', 'ROTAS-YANGIN-ZON')
        c.T(xm, Y1 - 300, f'{tr(alan, 0)} m²  -  576 ADET K160 DİK BAŞLIK  -  HHS 10 mm/dk', 18, 'MC', 'ROTAS-YANGIN-ZON')


def alan_ciz(c, S, adlar, baslik, alt):
    pts = [S['yol'][h] for h in adlar]
    x0 = min(p[0] for p in pts) - 150; x1 = max(p[0] for p in pts) + 150
    y0 = min(p[1] for p in pts) - 150; y1 = max(p[1] for p in pts) + 150
    c.R(x0, y0, x1, y1, 'ROTAS-YANGIN-ALAN', 5)
    c.HATCH([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'ROTAS-YANGIN-ALAN', 'ANSI37', 40)
    c.T(x1 + 40, y1 - 20, baslik, 18, 'TL', 'ROTAS-YANGIN-ALAN')
    for i, s in enumerate(alt):
        c.T(x1 + 40, y1 - 50 - 28 * i, s, 14, 'TL', 'ROTAS-YANGIN-ALAN')


def plan_dolap(c, D):
    for r in 'BC':
        y = V.Y_DOLAP[r]
        xe = AX[22] + 30
        c.L((V.HID_X_SOL, y), (xe, y), DB, 4)
        met('DN80 (dolap)', xe - V.HID_X_SOL)
        c.SMB('kelebek', V.HID_X_SOL + 250, y, 0, 2.0, lay=DL)
        c.T(V.HID_X_SOL + 250, y + 30, 'KESME VANASI DN80 (VANA KUTUSU)', 11, 'BC', YZ)
        for xm in (AX[4], AX[12] + 300, AX[20]):
            c.T(xm, y - 14, 'DN80 YANGIN DOLABI HATTI (+4,50)', 11, 'TC', CAP)
    for i, (x, y, r) in enumerate(V.DOLAPLAR):
        no = i + 1
        ins(c, 'ROTAS-SMB-DOLAP-PLAN', x + 50, y, DL)
        yh = V.Y_DOLAP[r]
        c.L((x + 62, yh), (x + 62, y - 40), DB, 2)
        met('DN50 (dolap bağlantı)', 450 - 150)
        c.T(x + 82, y + 10, f'YD-{no}', 16, 'BL', DL)
        c.T(x + 82, y - 12, 'TS EN 671-1 Ø25 x 30 m', 10, 'TL', DL)
        c.m.add_circle((x + 62, y), 3500, dxfattribs={'layer': 'ROTAS-YANGIN-DOLAP-ETKI'})


def plan_hidrant(c, H):
    x0, x1, y0, y1 = V.HID_X_SOL, V.HID_X_SAG, V.HID_Y_ALT, V.HID_Y_UST
    c.PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], HB, True, 8)
    met('Ø160 PE100 PN16 (hidrant halkası)', 2 * ((x1 - x0) + (y1 - y0)))
    for (xa, ya, xb, yb, rot) in ((x0, y1, x1, y1, 0), (x0, y0, x1, y0, 0), (x0, y0, x0, y1, 90), (x1, y0, x1, y1, 90)):
        for t in (0.17, 0.62):
            xm, ym = xa + (xb - xa) * t, ya + (yb - ya) * t
            c.T(xm + (0 if rot == 0 else -18), ym + (18 if rot == 0 else 0), 'HİDRANT HALKASI DN150 (Ø160 PE100 PN16) - GÖMÜLÜ -1,20',
                13, 'BC', CAP, rot=rot)
    # bölme vanaları (yer altı sürgülü vana + kutu)
    for p, a in (((AX[5], y1), 0), ((AX[12] - 1200, y1), 0), ((AX[20], y1), 0), ((AX[5], y0), 0), ((AX[12], y0), 0),
                 ((AX[20], y0), 0), ((x0, AY['B'] + 1200), 90), ((x1, AY['B'] + 1200), 90)):
        c.SMB('kelebek', p[0], p[1], a, 2.5, lay=HD)
    for i, (x, y) in enumerate(V.HIDRANTLAR):
        no = i + 1
        ust = y > Y1
        alt = y < Y0
        dx = 0 if (ust or alt) else (-200 if x < X0 else 200)
        dy = 200 if ust else -200 if alt else 0
        hx, hy = x + dx, y + dy
        c.L((x, y), (hx, hy), HB, 4)
        met('DN100 (hidrant bağlantı)', 200)
        c.SMB('kelebek', (x + hx) / 2, (y + hy) / 2, 90 if (ust or alt) else 0, 2.0, lay=HD)
        ins(c, 'ROTAS-SMB-HIDRANT', hx, hy, HD)
        ins(c, 'ROTAS-SMB-HORTUM-DOLABI', hx + 110, hy, HD)
        c.T(hx + 60, hy + 45, f'H-{no}', 20, 'BL', HD)
        c.T(hx + 60, hy - 50, 'YER ÜSTÜ HİDRANT DN100 (2xØ75+1xØ100)', 10, 'TL', HD)
        c.T(hx + 60, hy - 66, '+ HİDRANT HORTUM DOLABI', 10, 'TL', HD)
    # pompa dairesi → halka
    xh = POMPA[0] + 200
    c.L((xh, POMPA[1] - DUV), (xh, y1), HB, 8)
    met('Ø160 PE100 PN16 (hidrant halkası)', POMPA[1] - DUV - y1)
    c.T(xh - 16, (POMPA[1] + y1) / 2, 'DN150 HİDRANT BESLEME', 12, 'MC', CAP, rot=90)


def plan_pompa_dairesi(c, O):
    x0, y0, x1, y1 = POMPA
    d = DUV
    # pompa dairesi + depo betonarme (toprak altı)
    dx0, dx1 = x1 + d, x1 + d + 1000 + 30 + 1000
    for (a, b, e, f) in ((x0, y0, x1, y1), (dx0, y0, dx0 + 1000, y1), (dx0 + 1030, y0, dx1, y1)):
        c.R(a, b, e, f, PD, 0)
    c.R(x0 - d, y0 - d, dx1 + d, y1 + d, PD, 0)
    pts_dis = [(x0 - d, y0 - d), (dx1 + d, y0 - d), (dx1 + d, y1 + d), (x0 - d, y1 + d)]
    h = c.HATCH(pts_dis, 'ROTAS-YANGIN-TARAMA', 'ANSI31', 15)
    h.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)
    h.paths.add_polyline_path([(dx0, y0), (dx0 + 1000, y0), (dx0 + 1000, y1), (dx0, y1)], is_closed=True)
    h.paths.add_polyline_path([(dx0 + 1030, y0), (dx1, y0), (dx1, y1), (dx0 + 1030, y1)], is_closed=True)
    c.T((x0 + x1) / 2, y1 - 60, 'YANGIN POMPA DAİRESİ', 26, 'TC', YZ)
    c.T((x0 + x1) / 2, y1 - 100, 'TOPRAK ALTI - TABAN -4,00 - İÇ 14,00 x 10,00 m', 14, 'TC', YZ)
    for i, gx in enumerate((dx0, dx0 + 1030)):
        c.T(gx + 500, y1 - 60, f'YANGIN SUYU DEPOSU - {i + 1}. GÖZ', 22, 'TC', YZ)
        c.T(gx + 500, y1 - 95, f'İÇ 10,00 x 10,00 x 3,60 m - V={tr(O["V_sec"] / 2, 0)} m³ (etkin)', 13, 'TC', YZ)
        for mx in (gx + 150, gx + 850):
            c.R(mx - 33, y1 - 260, mx + 33, y1 - 194, PD)
            c.T(mx, y1 - 275, 'MENHOL 65x65', 9, 'TC', YZ)
        # emiş çanı (girdap önleyici) — pompa dairesi tarafı
    c.T((dx0 + dx1) / 2, y0 + 30, f'TOPLAM V={tr(O["V_sec"], 0)} m³  (Q={tr(O["Q_top"], 0)} l/dk x 90 dk = {tr(O["V"], 0)} m³)', 14, 'BC', YZ)
    # pompalar (plan, sadeleştirilmiş)
    ye = y0 + 520
    for i, (ad, L, W) in enumerate((('EP', 300, 110), ('DP', 380, 160), ('JP', 70, 70))):
        px = x1 - 160 - i * 0
        py = y0 + 220 + i * 260 if i < 2 else y0 + 760
        cx = x0 + 360 + L / 2
        c.R(cx - L / 2, py - W / 2, cx + L / 2, py + W / 2, PD)
        c.R(cx - L / 2 - 15, py - W / 2 - 15, cx + L / 2 + 15, py + W / 2 + 15, PD)
        c.T(cx, py, {'EP': 'ELEKTRİKLİ POMPA', 'DP': 'DİZEL POMPA', 'JP': 'JOKEY'}[ad], 12, 'MC', YZ)
        c.L((cx + L / 2, py), (x1, py), SA, 6)                       # emiş → depo
        c.L((cx - L / 2, py), (x0 + 200, py), SA, 6)                 # basma → kollektör
    c.L((x0 + 200, y0 + 150), (x0 + 200, y1 - 150), SA, 10)          # basma kollektörü (düşey)
    c.T(x0 + 175, (y0 + y1) / 2 + 100, 'BASMA KOLLEKTÖRÜ DN250', 13, 'MC', CAP, rot=90)
    c.L((x0 + 200, y0 + 150), (X_F[2], y0 + 150), SA, 8)
    for zon in (1, 2):
        xf = X_F[zon]
        c.L((xf, y0 + 150), (xf, y0), SA, 6)
        c.SMB('islak_alarm', xf, y0 + 80, -90, 2.5)
    c.T((X_F[1] + X_F[2]) / 2, y0 + 190, 'AV-1 / AV-2 ISLAK ALARM VANA İSTASYONLARI DN200', 11, 'BC', YZ)
    c.R(x0 + 30, y1 - 160, x0 + 330, y1 - 30, PD)
    c.T(x0 + 180, y1 - 95, 'POMPA PANOLARI', 11, 'MC', YZ)
    c.R(x0 + 360, y1 - 120, x0 + 560, y1 - 20, PD)
    c.T(x0 + 460, y1 - 70, 'YAKIT TANKI 500 L', 10, 'MC', YZ)
    # merdiven / giriş
    c.R(x0 - d - 400, y0 + 300, x0 - d, y0 + 700, PD)
    for k in range(1, 12):
        c.L((x0 - d - 400 + k * 33, y0 + 300), (x0 - d - 400 + k * 33, y0 + 700), PD)
    c.T(x0 - d - 200, y0 + 720, 'GİRİŞ MERDİVENİ', 11, 'BC', YZ)
    # itfaiye bağlantısı (kuzey dış duvar)
    xi = x0 + 500
    for k, xs in enumerate((xi - 60, xi + 60)):
        c.SMB('storz', xs, y1 + d + 60, -90, 2.5)
        c.L((xs, y1 + d + 30), (xs, y1 - 150), SA, 4)
    c.T(xi, y1 + d + 120, 'İTFAİYE BAĞLANTISI 2 x DN65 STORZ (KÖR KAPAKLI) → DN100 → BASMA KOLLEKTÖRÜ', 13, 'BC', YZ)
    # şebeke dolum
    xd = dx0 + 1015
    c.L((xd, y1 + d + 400), (xd, y1 - 120), 'ROTAS-YANGIN-DOLAP-BORU', 3)
    c.T(xd + 15, y1 + d + 300, 'ŞEBEKEDEN DOLUM DN65 (SAYAÇLI, ŞAMANDIRALI)', 12, 'ML', YZ)
    c.T(xd + 15, y1 + d + 275, f'DOLUM ≤ 36 sa → Q ≥ {tr(O["dolum"], 1)} m³/h', 11, 'ML', YZ)


def plan(c, S, O):
    n_mim = mimari_altlik(c)
    say = plan_sprinkler(c, S)
    plan_besleme(c)
    plan_dolap(c, O['D'])
    plan_hidrant(c, O['H'])
    plan_pompa_dairesi(c, O)
    alan_ciz(c, S, S['uzak'], 'HİDROLİK EN UZAK ALAN (ZON-1)',
             [f'{S["nA"]} başlık x 9 m² = {tr(S["alan"], 0)} m² ≥ 260 m²', f'en düşük başlık {tr(TASARIM["Pmin"], 2)} bar / {tr(S["q_min"], 1)} l/dk',
              f'yoğunluk {tr(S["yog"], 2)} ≥ 10 mm/dk', f'Q = {tr(S["Qs"], 0)} l/dk  pompa çıkışı {tr(S["P0"], 2)} bar'])
    alan_ciz(c, S, S['yakin'], 'HİDROLİK EN YAKIN ALAN (ZON-1)', [f'Q = {tr(S["Qf"], 0)} l/dk (aynı pompa basıncında)'])
    # başlık
    xb, yb = X0 - 1100, V.POMPA[3] + 900
    c.T(xb, yb, 'YANGIN TESİSATI ZEMİN KAT PLANI (SPRİNKLER - YANGIN DOLABI - HİDRANT)', 60, 'BL', 'ROTAS-PAFTA')
    c.T(xb, yb - 90, 'ÖLÇEK : 1/100', 40, 'BL', 'ROTAS-PAFTA')
    c.T(xb, yb - 150, 'OBA MAKARNACILIK SAN. ve TİC. A.Ş. - HENDEK ÇAĞLAYAN MAH. 900 ADA 84 PARSEL - DEPOLAMA BİNASI (9.991 m²)', 26, 'BL', 'ROTAS-PAFTA')
    pafta_cerceve(c, X0 - 1300, Y0 - 1450, X1 + 1300, V.POMPA[3] + 1150, '', '')
    return say, n_mim


# ================================================================== PRENSİP ŞEMASI
def sema(c, O, ox, oy):
    """sol üst (ox, oy); genişlik ~6400, yükseklik ~3600"""
    S, H = O['S'], O['H']
    L1, LY, LH, LD, LP = 'ROTAS-SEMA', 'ROTAS-SEMA-YAZI', 'ROTAS-SEMA-HIDRANT', 'ROTAS-SEMA-DOLAP', 'ROTAS-SEMA-DEPO'
    c.T(ox, oy, 'YANGIN TESİSATI PRENSİP ŞEMASI', 50, 'BL', 'ROTAS-PAFTA')
    c.T(ox, oy - 70, 'ÖLÇEKSİZ', 30, 'BL', 'ROTAS-PAFTA')
    # depo
    dx0, dy0, dx1, dy1 = ox + 100, oy - 3400, ox + 1100, oy - 2300
    c.R(dx0, dy0, dx1, dy1, LP, 4)
    c.L(((dx0 + dx1) / 2, dy0), ((dx0 + dx1) / 2, dy1), LP)
    c.L((dx0, dy1 - 150), (dx1, dy1 - 150), LP)
    c.T((dx0 + dx1) / 2, dy1 - 120, 'MAKS. SU', 16, 'BC', LY)
    c.T((dx0 + dx1) / 2, (dy0 + dy1) / 2, 'YANGIN SUYU DEPOSU', 30, 'MC', LY)
    c.T((dx0 + dx1) / 2, (dy0 + dy1) / 2 - 50, f'2 GÖZ - V = {tr(O["V_sec"], 0)} m³ (90 dk)', 22, 'MC', LY)
    c.L((dx0 + 300, dy1 + 300), (dx0 + 300, dy1 - 150), L1, 3)
    c.SMB('kuresel', dx0 + 300, dy1 + 150, -90, 3.0)
    c.T(dx0 + 330, dy1 + 280, 'ŞEBEKEDEN DOLUM DN65 (ŞAMANDIRALI)', 16, 'ML', LY)
    # emiş kollektörü
    ye, yb = dy0 + 120, oy - 1900
    c.L((dx1, ye), (ox + 2500, ye), L1, 8)
    c.T(dx1 + 40, ye - 30, 'EMİŞ KOLLEKTÖRÜ DN250', 16, 'TL', LY)
    pompalar = [('ELEKTRİKLİ POMPA', f'Q={O["Q_sec"]} m³/h  H={O["H_sec"]} mSS  P={O["motor"]} kW', ox + 1400, 250),
                ('DİZEL POMPA', f'Q={O["Q_sec"]} m³/h  H={O["H_sec"]} mSS  P={O["dizel"]} kW', ox + 1850, 250),
                ('JOKEY POMPA', f'Q={O["jokey"]["Q"]} m³/h  H={O["jokey"]["H"]} mSS  P={tr(O["jokey"]["P"], 1)} kW', ox + 2300, 50)]
    for ad, oz, x, dn in pompalar:
        RS.hat(c.m, (x, ye), (x, yb), [(0.15, 'izlenebilir_kelebek' if dn > 50 else 'kuresel'), (0.62, 'cekvalf'),
                                        (0.82, 'izlenebilir_kelebek' if dn > 50 else 'kuresel')], L1, sembol_katmani='ROTAS-SEMA', genislik=4, olcek=2.5)
        ins(c, 'ROTAS-SMB-POMPA-SEMA', x, ye + (yb - ye) * 0.38, L1, 90, 1.6)
        c.T(x + 70, ye + (yb - ye) * 0.38 + 20, ad, 16, 'BL', LY)
        c.T(x + 70, ye + (yb - ye) * 0.38 - 10, oz, 12, 'TL', LY)
    # basma kollektörü
    xk0, xk1 = ox + 1250, ox + 6300
    c.L((xk0, yb), (xk1, yb), L1, 10)
    c.T(ox + 2700, yb - 30, 'BASMA KOLLEKTÖRÜ DN250', 18, 'TL', LY)
    # test hattı → depo
    xt = ox + 1250
    RS.hat(c.m, (xt, yb), (xt, dy1 + 80), [(0.3, 'kelebek'), (0.6, 'kelebek')], L1, sembol_katmani='ROTAS-SEMA', genislik=4, olcek=2.5)
    c.L((xt, dy1 + 80), (dx1 - 100, dy1 + 80), L1, 4); c.L((dx1 - 100, dy1 + 80), (dx1 - 100, dy1 - 60), L1, 4)
    c.R(xt - 25, yb - 450, xt + 25, yb - 380, L1)
    c.T(xt - 40, yb - 415, 'DEBİMETRE', 14, 'MR', LY)
    c.T(xt - 40, yb - 445, 'TEST HATTI DN250 (%150 debi)', 12, 'MR', LY)
    # membranlı tank + basınç şalterleri
    c.L((ox + 2550, yb), (ox + 2550, yb + 200), L1, 3)
    c.CI((ox + 2550, yb + 260), 60, L1)
    c.T(ox + 2630, yb + 260, 'MEMBRANLI TANK 50 L / 16 bar + PS-J / PS-E / PS-D BASINÇ ŞALTERLERİ', 14, 'ML', LY)
    # sprinkler zonları
    zx = {1: ox + 3000, 2: ox + 3700}
    for zon, x in zx.items():
        yt = oy - 600
        RS.hat(c.m, (x, yb), (x, yt), [(0.12, 'izlenebilir_kelebek'), (0.30, 'islak_alarm'), (0.48, 'izlenebilir_kelebek'),
                                        (0.62, 'manometre')], L1, sembol_katmani='ROTAS-SEMA', genislik=6, olcek=2.5)
        c.T(x + 50, yb + (yt - yb) * 0.30, f'AV-{zon} ISLAK ALARM VANASI DN200', 15, 'ML', LY)
        c.T(x + 50, yb + (yt - yb) * 0.30 - 30, '(alarm gongu + basınç anahtarı + test-drenaj)', 11, 'ML', LY)
        c.T(x + 50, yb + (yt - yb) * 0.80, f'SK-{zon} DN200 (gömülü + bina içi kolon)', 14, 'ML', LY)
        # zon kutusu: tavan altı ağ
        bx0, bx1 = x - 300, x + 300
        c.R(bx0, yt, bx1, yt + 420, L1, 2)
        for j in range(5):
            xx = bx0 + 60 + j * 120
            c.L((xx, yt + 60), (xx, yt + 380), L1)
            for k in range(4):
                ins(c, 'ROTAS-SMB-SPR-DIK', xx, yt + 80 + k * 95, L1, s=1.6)
        c.L((bx0 + 60, yt + 60), (bx1 - 60, yt + 60), L1, 4)
        c.L((x, yt), (x, yt + 60), L1, 4)
        c.T(x, yt + 450, f'ZON-{zon}: 576 ADET K160 DİK SPRİNKLER (68 °C)', 18, 'BC', LY)
        c.T(x, yt + 485, f'{tr((AX[12] - X0) * (Y1 - Y0) / 1e4, 0)} m² - DN150 ana dağıtım - DN32..65 branşman', 13, 'BC', LY)
    # hidrant halkası
    xh = ox + 4500
    hx0, hx1, hy0, hy1 = ox + 4250, ox + 5500, oy - 1300, oy - 450
    RS.hat(c.m, (xh, yb), (xh, hy0), [(0.25, 'izlenebilir_kelebek'), (0.6, 'cekvalf')], L1, sembol_katmani='ROTAS-SEMA', genislik=6, olcek=2.5)
    c.PL([(hx0, hy0), (hx1, hy0), (hx1, hy1), (hx0, hy1)], LH, True, 6)
    c.T((hx0 + hx1) / 2, hy1 + 130, f'HİDRANT HALKASI DN150 (Ø160 PE100) L≈{tr(H["L_halka"], 0)} m', 18, 'BC', LY)
    c.T((hx0 + hx1) / 2, hy1 + 100, f'{H["n"]} ADET YER ÜSTÜ HİDRANT (1900 l/dk - çıkışta 7 bar)', 14, 'BC', LY)
    pos = [(hx0 + (hx1 - hx0) * t, hy1) for t in (0.15, 0.4, 0.65, 0.9)] + [(hx0 + (hx1 - hx0) * t, hy0) for t in (0.15, 0.4, 0.65, 0.9)] + \
          [(hx0, hy0 + (hy1 - hy0) * t) for t in (0.3, 0.7)] + [(hx1, hy0 + (hy1 - hy0) * t) for t in (0.3, 0.7)]
    for i, (x, y) in enumerate(pos):
        ins(c, 'ROTAS-SMB-HIDRANT', x, y, LH, s=0.9)
        c.T(x + 40, y + 40, f'H-{i + 1}', 12, 'BL', LY)
    # dolap hatları (halka batı kolundan)
    for k, (r, yy) in enumerate((('B', hy0 + (hy1 - hy0) * 0.45), ('C', hy0 + (hy1 - hy0) * 0.55))):
        x0d = hx1 + 100
        c.L((hx1, yy), (x0d + 50 + 6 * 110, yy), LD, 4)
        c.SMB('kelebek', hx1 + 60, yy, 0, 2.0, lay='ROTAS-SEMA')
        for j in range(6):
            xx = x0d + 80 + j * 110
            c.L((xx, yy), (xx, yy + (60 if k else -60)), LD, 2)
            c.SMB('yangin_dolabi_kolon', xx + 20, yy + (90 if k else -90), 0, 1.0, lay='ROTAS-SEMA')
            c.T(xx, yy + (125 if k else -125), f'YD-{j + 1 + 6 * k}', 11, 'BC' if k else 'TC', LY)
    c.T(hx1 + 100, hy1 + 40, 'YANGIN DOLAPLARI DN80 HAT (+4,50) - 12 ADET TS EN 671-1', 14, 'BL', LY)
    c.T(hx1 + 100, hy1 + 15, '(100 l/dk - 4 bar, Ø25 mm x 30 m yarı sert hortum)', 11, 'BL', LY)
    # itfaiye bağlantısı (kollektör sağ ucu)
    xi = xk1
    c.L((xi, yb), (xi, yb - 300), L1, 6)
    RS.hat(c.m, (xi + 500, yb - 300), (xi, yb - 300), [(0.35, 'cekvalf'), (0.7, 'izlenebilir_kelebek')], L1,
           sembol_katmani='ROTAS-SEMA', genislik=6, olcek=2.5)
    for k in (-60, 60):
        c.SMB('storz', xi + 560, yb - 300 + k, 180, 2.5, lay='ROTAS-SEMA')
        c.L((xi + 520, yb - 300 + k), (xi + 500, yb - 300), L1, 3)
    c.T(xi + 300, yb - 400, 'İTFAİYE BAĞLANTISI 2 x DN65 STORZ → DN100', 14, 'TC', LY)
    # dizel egzoz / not
    c.T(ox + 100, oy - 3500, 'Not: pompalar pozitif emişlidir (depo min. su seviyesi pompa ekseninin üstünde). Alarm vana istasyonları pompa dairesindedir; '
        'zon besleme hatları gömülü DN200 ile binaya girer.', 14, 'TL', LY)
    return ox + 7000, oy - 3600


# ================================================================== DEPO PLAN + KESİT (1/50)
def depo_detay(c, O, ox, oy):
    """sol üst (ox, oy). Toprak altı betonarme yangın suyu deposu + pompa dairesi: plan ve A-A kesiti"""
    L, LY = 'ROTAS-DETAY', 'ROTAS-DETAY-YAZI'
    c.T(ox, oy, 'YANGIN SUYU DEPOSU VE POMPA DAİRESİ PLANI', 45, 'BL', 'ROTAS-PAFTA')
    c.T(ox, oy - 60, 'ÖLÇEK : 1/50', 30, 'BL', 'ROTAS-PAFTA')
    d = 40
    px0, py1 = ox + 100, oy - 200
    px1 = px0 + 1400
    py0 = py1 - 1000
    g1 = (px1 + d, px1 + d + 1000)
    g2 = (g1[1] + 30, g1[1] + 30 + 1000)
    dis = [(px0 - d, py0 - d), (g2[1] + d, py0 - d), (g2[1] + d, py1 + d), (px0 - d, py1 + d)]
    c.PL(dis, L, True)
    for a, b in ((px0, px1), g1, g2):
        c.R(a, py0, b, py1, L)
    h = c.HATCH(dis, 'ROTAS-YANGIN-TARAMA', 'ANSI31', 8)
    for a, b in ((px0, px1), g1, g2):
        h.paths.add_polyline_path([(a, py0), (b, py0), (b, py1), (a, py1)], is_closed=True)
    c.T((px0 + px1) / 2, py1 - 40, 'POMPA DAİRESİ (taban -4,00)', 22, 'TC', LY)
    for i, (a, b) in enumerate((g1, g2)):
        c.T((a + b) / 2, py1 - 40, f'{i + 1}. GÖZ', 24, 'TC', LY)
        c.T((a + b) / 2, py1 - 75, f'V={tr(O["V_sec"] / 2, 0)} m³ etkin', 16, 'TC', LY)
        for mx in (a + 120, b - 120):
            c.R(mx - 33, py1 - 220, mx + 33, py1 - 154, L)
            c.L((mx - 33, py1 - 220), (mx + 33, py1 - 154), L); c.L((mx - 33, py1 - 154), (mx + 33, py1 - 220), L)
            c.T(mx, py1 - 235, 'MENHOL 65x65', 10, 'TC', LY)
        # emiş çanları (girdap önleyicili) — pompa dairesi tarafında
        for k, yy in enumerate((py0 + 220, py0 + 480, py0 + 760)):
            if k == 2 and i == 1:
                continue
        c.T((a + b) / 2, (py0 + py1) / 2, 'MAKS. SU +3,10 / MİN. SU +0,85 (taban üstü)', 13, 'MC', LY)
        c.L((a + 60, py0 + 60), (a + 60, py0 + 200), L)
        c.T(a + 80, py0 + 80, 'SEVİYE GÖSTERGESİ', 10, 'BL', LY)
    # emiş hatları: her pompa kendi emiş çanı (EN 12845 10.6) — 1. gözden
    for k, (ad, yy) in enumerate((('EP', py0 + 250), ('DP', py0 + 520), ('JP', py0 + 800))):
        dn = 250 if k < 2 else 50
        c.L((g1[0] + 150, yy), (px1 - 300, yy), 'ROTAS-DETAY-BORU', 6 if k < 2 else 3)
        c.CI((g1[0] + 150, yy), 30 if k < 2 else 12, 'ROTAS-DETAY-BORU')
        c.T(g1[0] + 190, yy + 15, f'{ad} EMİŞ DN{dn} - ÇAN AĞIZLI + GİRDAP ÖNLEYİCİ', 11, 'BL', LY)
        c.R(px1 - 300 - (380 if k == 1 else 300 if k == 0 else 80), yy - (80 if k == 1 else 55 if k == 0 else 35),
            px1 - 300, yy + (80 if k == 1 else 55 if k == 0 else 35), L)
        c.T(px1 - 300 - (190 if k == 1 else 150 if k == 0 else 40), yy, {'EP': 'ELEKTRİKLİ\nPOMPA', 'DP': 'DİZEL POMPA', 'JP': 'JP'}[ad].split('\n')[0],
            12, 'MC', LY)
    # göz bağlantısı (iki göz arasında vanalı dengeleme)
    c.L((g1[1] - 50, py0 + 120), (g2[0] + 50, py0 + 120), 'ROTAS-DETAY-BORU', 4)
    c.T(g1[1] + 15, py0 + 145, 'DENGELEME DN250 (vanalı)', 10, 'BC', LY)
    c.L((px0 + 150, py0 + 150), (px0 + 150, py1 - 150), 'ROTAS-DETAY-BORU', 8)
    c.T(px0 + 120, (py0 + py1) / 2, 'BASMA KOLLEKTÖRÜ DN250', 12, 'MC', LY, rot=90)
    c.T(px0 + 400, py1 - 120, 'PANOLAR: ELEKTRİKLİ / DİZEL / JOKEY', 11, 'TL', LY)
    c.T(px0 + 400, py0 + 60, 'YER SÜZGEÇLERİ → DRENAJ ÇUKURU (dalgıç pompa)', 11, 'BL', LY)
    # ölçüler
    yo = py0 - d - 80
    for a, b, s in ((px0, px1, '1400'), (g1[0], g1[1], '1000'), (g2[0], g2[1], '1000')):
        c.L((a, yo), (b, yo), 'ROTAS-YANGIN-OLCU'); c.L((a, yo - 15), (a, yo + 15), 'ROTAS-YANGIN-OLCU'); c.L((b, yo - 15), (b, yo + 15), 'ROTAS-YANGIN-OLCU')
        c.T((a + b) / 2, yo + 10, s, 14, 'BC', 'ROTAS-YANGIN-OLCU')
    # kesit çizgisi
    yk = py0 + 380
    c.L((px0 - 200, yk), (g2[1] + 200, yk), 'ROTAS-YANGIN-ZON')
    c.T(px0 - 220, yk, 'A', 30, 'MR', LY); c.T(g2[1] + 220, yk, 'A', 30, 'ML', LY)

    # ---------------- A-A KESİTİ
    kx0, ky0 = ox + 100, py0 - 700        # kesit taban üst kotu -4,00 çizim y
    sk = 1.0
    c.T(ox, ky0 + 300, 'A-A KESİTİ', 40, 'BL', 'ROTAS-PAFTA')
    c.T(ox + 360, ky0 + 300, 'ÖLÇEK : 1/50', 26, 'BL', 'ROTAS-PAFTA')
    zemin = ky0 - 1040 + 0                   # çizim: kesit yukarıdan aşağı çizilir; zemin ±0,00 → yk0
    yk0 = ky0 - 100                           # ±0,00 (doğal zemin)
    def Y(kot):
        return yk0 + kot * 100
    x_sol, x_sag = kx0, kx0 + 1400 + 2070 + 2 * d
    # radye
    c.R(x_sol - d - 50, Y(-4.60), x_sag + d + 50, Y(-4.00), L)
    c.HATCH([(x_sol - d - 50, Y(-4.60)), (x_sag + d + 50, Y(-4.60)), (x_sag + d + 50, Y(-4.00)), (x_sol - d - 50, Y(-4.00))],
            'ROTAS-YANGIN-TARAMA', 'ANSI31', 8)
    # depo tabanı -4,50 değil: depo ve pompa dairesi aynı taban (-4,00); depo içi su yüksekliği taban üstü
    tav = Y(-0.40)
    for xa, xb in ((x_sol - d, x_sol), (x_sol + 1400, x_sol + 1400 + d), (x_sol + 1400 + d + 1000, x_sol + 1400 + d + 1030),
                   (x_sag, x_sag + d)):
        c.R(xa, Y(-4.00), xb, tav, L)
        c.HATCH([(xa, Y(-4.00)), (xb, Y(-4.00)), (xb, tav), (xa, tav)], 'ROTAS-YANGIN-TARAMA', 'ANSI31', 8)
    c.R(x_sol - d, tav, x_sag + d, Y(0.0), L)
    c.HATCH([(x_sol - d, tav), (x_sag + d, tav), (x_sag + d, Y(0.0)), (x_sol - d, Y(0.0))], 'ROTAS-YANGIN-TARAMA', 'ANSI31', 8)
    c.L((x_sol - 600, Y(0.0)), (x_sag + 600, Y(0.0)), L, 3)
    c.T(x_sag + 600, Y(0.0) + 10, '±0,00 (84,00) DOĞAL ZEMİN / TOPRAK ÖRTÜ', 14, 'BR', LY)
    # su seviyeleri
    gx0, gx1 = x_sol + 1400 + d, x_sag
    for kot, s in ((-4.00 + 3.10, 'MAKS. SU -0,90'), (-4.00 + 0.85, 'MİN. SU -3,15 (EN 12845 batma payı)')):
        c.L((gx0, Y(kot)), (gx1, Y(kot)), 'ROTAS-YANGIN-HIDRANT')
        c.T(gx0 + 30, Y(kot) + 8, s, 14, 'BL', LY)
    c.HATCH([(gx0, Y(-4.0)), (gx1, Y(-4.0)), (gx1, Y(-0.9)), (gx0, Y(-0.9))], 'ROTAS-YANGIN-HIDRANT', 'ANSI37', 30)
    c.T((gx0 + gx1) / 2, Y(-2.2), f'YANGIN SUYU DEPOSU 2 GÖZ - V={tr(O["V_sec"], 0)} m³ (etkin 2 x 10,00 x 10,00 x 2,65 m)', 18, 'MC', LY)
    # menhol + havalık
    for mx in (gx0 + 150, gx1 - 150):
        c.R(mx - 40, Y(0.0), mx + 40, Y(0.25), L)
        c.T(mx, Y(0.30), 'MENHOL', 11, 'BC', LY)
    c.L((gx0 + 500, Y(0.0)), (gx0 + 500, Y(0.9)), 'ROTAS-DETAY-BORU', 3)
    c.PL([(gx0 + 470, Y(0.9)), (gx0 + 500, Y(1.05)), (gx0 + 530, Y(0.9))], 'ROTAS-DETAY-BORU')
    c.T(gx0 + 540, Y(0.85), 'HAVALIK (sinek telli)', 11, 'ML', LY)
    # emiş
    c.L((gx0 + 200, Y(-3.75)), (x_sol + 900, Y(-3.75)), 'ROTAS-DETAY-BORU', 8)
    c.PL([(gx0 + 150, Y(-3.85)), (gx0 + 200, Y(-3.75)), (gx0 + 150, Y(-3.65))], 'ROTAS-DETAY-BORU')
    c.L((gx0 + 110, Y(-3.92)), (gx0 + 190, Y(-3.92)), 'ROTAS-DETAY-BORU', 3)
    c.T(gx0 + 220, Y(-3.60), 'EMİŞ ÇANI + GİRDAP ÖNLEYİCİ PLAKA', 11, 'BL', LY)
    # pompa
    c.R(x_sol + 450, Y(-4.00) + 15, x_sol + 900, Y(-3.40), L)
    c.T(x_sol + 675, Y(-3.70), 'POMPA', 14, 'MC', LY)
    c.L((x_sol + 450, Y(-3.55)), (x_sol + 150, Y(-3.55)), 'ROTAS-DETAY-BORU', 8)
    c.L((x_sol + 150, Y(-3.55)), (x_sol + 150, Y(-1.20)), 'ROTAS-DETAY-BORU', 8)
    c.L((x_sol + 150, Y(-1.20)), (x_sol - d - 400, Y(-1.20)), 'ROTAS-DETAY-BORU', 8)
    c.T(x_sol - d - 400, Y(-1.10), 'ZON / HİDRANT HATLARINA (gömülü -1,20)', 12, 'BL', LY)
    # kotlar
    for kot in (-4.60, -4.00, -0.40, 0.0):
        c.L((x_sag + d + 80, Y(kot)), (x_sag + d + 160, Y(kot)), 'ROTAS-YANGIN-OLCU')
        c.T(x_sag + d + 170, Y(kot), (f'{kot:+.2f}').replace('.', ','), 13, 'ML', 'ROTAS-YANGIN-OLCU')
    c.T((x_sol + x_sol + 1400) / 2, Y(-0.20), 'BETONARME TAVAN d=40 cm (üstü toprak örtü / araç yükü)', 11, 'MC', LY)
    c.T(x_sol + 700, Y(-4.30), 'RADYE d=60 cm + grobeton + su yalıtımı', 11, 'MC', LY)
    c.T(x_sol + 50, Y(-0.70), 'merdiven + havalandırma bacası (pompa dairesi)', 11, 'BL', LY)
    return g2[1] + 300, Y(-4.60) - 150


# ================================================================== DETAYLAR (tip)
def detaylar(c, ox, oy):
    L, LY, LB = 'ROTAS-DETAY', 'ROTAS-DETAY-YAZI', 'ROTAS-DETAY-BORU'
    c.T(ox, oy, 'TİP DETAYLAR', 45, 'BL', 'ROTAS-PAFTA')
    c.T(ox, oy - 60, 'ÖLÇEKSİZ', 30, 'BL', 'ROTAS-PAFTA')
    # 1) dik sprinkler branşman montajı
    x, y = ox + 50, oy - 200
    c.T(x, y, '1) DİK (UPRIGHT) SPRİNKLER MONTAJI', 22, 'BL', LY)
    yc = y - 150
    c.L((x, yc), (x + 600, yc), L, 4)
    c.T(x + 610, yc, 'ÇATI AŞIĞI / KAPLAMA', 12, 'ML', LY)
    yb = yc - 120
    c.L((x, yb), (x + 600, yb), LB, 6)
    c.T(x + 610, yb, 'BRANŞMAN DN32..65', 12, 'ML', LY)
    for hx in (x + 150, x + 450):
        c.L((hx, yb), (hx, yb + 30), LB, 3)
        c.PL([(hx - 20, yb + 45), (hx + 20, yb + 45)], LB)
        c.PL([(hx - 6, yb + 30), (hx, yb + 45), (hx + 6, yb + 30)], LB)
        c.L((hx, yc), (hx - 100, yb - 10), L)
        c.L((hx - 100, yb - 10), (hx - 100, yb + 10), L)
    c.T(x + 160, yb + 60, 'K160 DİK BAŞLIK - deflektör çatıya 7,5..15 cm', 11, 'BL', LY)
    c.T(x + 60, yb - 40, 'ASKI (her başlık arası, ≤ 3,0 m) - EN 12845 17.2', 11, 'TL', LY)
    # 2) yer üstü hidrant
    x2 = ox + 900
    c.T(x2, y, '2) YER ÜSTÜ HİDRANT MONTAJI', 22, 'BL', LY)
    yz = y - 300
    c.L((x2, yz), (x2 + 700, yz), L, 3)
    c.T(x2 + 710, yz, 'ZEMİN', 12, 'ML', LY)
    c.R(x2 + 300, yz, x2 + 380, yz + 160, L)
    c.R(x2 + 270, yz + 160, x2 + 410, yz + 190, L)
    c.CI((x2 + 340, yz + 110), 20, L); c.L((x2 + 380, yz + 110), (x2 + 420, yz + 110), L)
    c.L((x2 + 340, yz), (x2 + 340, yz - 180), LB, 6)
    c.L((x2 + 340, yz - 180), (x2 + 60, yz - 180), LB, 6)
    c.SMB('kelebek', x2 + 180, yz - 180, 0, 2.0, lay=LB)
    c.R(x2 + 150, yz - 150, x2 + 210, yz, L)
    c.T(x2 + 220, yz - 30, 'VANA KUTUSU + UZATMA MİLİ', 11, 'BL', LY)
    c.R(x2 + 300, yz - 230, x2 + 380, yz - 180, L)
    c.T(x2 + 390, yz - 210, 'BETON TAKOZ + DRENAJ ÇAKILI', 11, 'ML', LY)
    c.T(x2 + 60, yz - 200, 'HALKA DN150 (-1,20)', 11, 'TL', LY)
    c.T(x2 + 420, yz + 160, 'DN100 HİDRANT 2xØ75 + 1xØ100 STORZ', 11, 'BL', LY)
    c.T(x2 + 420, yz + 135, 'TS EN 14384, kırılabilir (yol tarafı) tip', 11, 'BL', LY)
    # 3) yangın dolabı (kolon üstü)
    x3 = ox + 1800
    c.T(x3, y, '3) YANGIN DOLABI MONTAJI (KOLON)', 22, 'BL', LY)
    yz3 = y - 600
    c.L((x3, yz3), (x3 + 600, yz3), L, 3)
    c.R(x3 + 100, yz3, x3 + 160, yz3 + 520, L)
    c.T(x3 + 130, yz3 + 540, 'ÇELİK KOLON', 11, 'BC', LY)
    c.R(x3 + 160, yz3 + 80, x3 + 240, yz3 + 230, L)
    c.CI((x3 + 200, yz3 + 160), 30, L)
    c.L((x3 + 200, yz3 + 230), (x3 + 200, yz3 + 450), LB, 4)
    c.L((x3 + 200, yz3 + 450), (x3 + 500, yz3 + 450), LB, 6)
    c.T(x3 + 260, yz3 + 470, 'DN80 DOLAP HATTI +4,50', 11, 'BL', LY)
    c.T(x3 + 250, yz3 + 160, 'YD: TS EN 671-1', 11, 'ML', LY)
    c.T(x3 + 250, yz3 + 135, 'Ø25 x 30 m, küresel vana', 11, 'ML', LY)
    c.T(x3 + 250, yz3 + 110, 'dolap üst kotu +1,60', 11, 'ML', LY)
    return ox + 2600, yz3 - 100


# ================================================================== TABLOLAR
def tablolar(c, O, ox, oy):
    S, H, D = O['S'], O['H'], O['D']
    T = TASARIM
    y = c.tablo(ox, oy, ['KRİTER', 'DEĞER', 'KAYNAK / AÇIKLAMA'], [700, 520, 1200], [
        ['Tehlike sınıfı', 'HHS (yüksek tehlike depolama)', 'TS EN 12845 Ek A / BYKHY Md.19'],
        ['Depolama', 'ST1 paletli blok istif ≤ 4,0 m', 'Ürün kat. II (ambalajlı gıda); OBA bildirimi'],
        ['Tasarım yoğunluğu', f'{tr(T["yogunluk"], 1)} mm/dk', 'Ç.4 Kat.II ST1 4,1 m: 7,5 → güvenli taraf 10,0'],
        ['İşletme alanı', f'{tr(T["alan"], 0)} m² (ıslak)', 'TS EN 12845 Çizelge 4'],
        ['Çalışma süresi', f'{T["sure"]} dk', 'TS EN 12845 9.3.4 / BYKHY Md.92'],
        ['Başlık', 'K160 dik, 68 °C, ½" sıcaklık sınıfı', 'kullanıcı notu: K160'],
        ['Başlık başına alan / aralık', '9,0 m² / 3,00 x 3,00 m (≤3,7 m)', 'TS EN 12845 12.2 Çizelge 19'],
        ['Başlık en düşük basınç', f'{tr(T["Pmin"], 2)} bar', 'TS EN 12845 13.4.3 (HH)'],
        ['Alarm vanası', '2 adet (zon başı 5.184 m² ≤ 9.000 m²)', 'TS EN 12845 11.3'],
        ['Hidrant', '≥1900 l/dk, çıkışta 7 bar, aralık ≤ 50 m', 'BYKHY Md.95'],
        ['Yangın dolabı', '100 l/dk, 4 bar, Ø25 x 30 m', 'BYKHY Md.94 / TS EN 671-1'],
    ], h=13, baslik='SPRİNKLER TASARIM KRİTERLERİ')
    y -= 120
    y = c.tablo(ox, y, ['HESAP', 'DEĞER'], [1200, 1220], [
        ['Hidrolik en uzak alan (zon-1, aks 1 / A cephesi)', f'{S["nA"]} başlık - {tr(S["alan"], 0)} m²'],
        ['En düşük başlık basıncı / debisi', f'{tr(T["Pmin"], 2)} bar / {tr(S["q_min"], 1)} l/dk (K160)'],
        ['Gerçekleşen yoğunluk (en düşük başlık)', f'{tr(S["yog"], 2)} mm/dk ≥ 10,0 mm/dk'],
        ['Sprinkler debisi (en uzak alan)', f'{tr(S["Qs"], 0)} l/dk = {tr(S["Qs"] * 0.06, 1)} m³/h'],
        ['Pompa çıkışında gereken basınç (sprinkler)', f'{tr(S["P0"], 2)} bar (statik {tr(0.0981 * (V.z_cati(V.BAS_Y[0]) + 3.6), 2)} bar dahil)'],
        ['En yakın alan debisi (aynı basınçta)', f'{tr(S["Qf"], 0)} l/dk'],
        ['Hidrant: en uzak hidrant 1900 l/dk @ 7 bar', f'pompa çıkışı {tr(H["P_pompa"], 2)} bar (halka kaybı {tr(H["dP_halka"], 2)} bar)'],
        ['Yangın dolabı: 2 x 100 l/dk @ 4 bar', f'gereken {tr(D["P_gerek"], 2)} bar (halkadan beslenir)'],
        ['Toplam debi (sprinkler + dolap + hidrant)', f'{tr(S["Qs"], 0)} + 200 + 1900 = {tr(O["Q_top"], 0)} l/dk = {tr(O["Qm3"], 1)} m³/h'],
        ['Depo hacmi (90 dk)', f'{tr(O["V"], 1)} m³ → seçilen {tr(O["V_sec"], 0)} m³ (2 göz)'],
        ['Depo dolum (≤ 36 saat)', f'≥ {tr(O["dolum"], 1)} m³/h - şebeke DN65'],
        ['Ana pompa (elektrikli + dizel, her biri %100)', f'Q={O["Q_sec"]} m³/h  H={O["H_sec"]} mSS  ({tr(O["P_ihtiyac"], 2)} bar ihtiyaç)'],
        ['Mil gücü (η=0,74) / motor', f'{tr(O["P_mil"], 1)} kW → elektrik {O["motor"]} kW, dizel {O["dizel"]} kW'],
        ['Pompa eğrisi şartı', f'%140 debide ({tr(O["Q_sec"] * 1.4, 0)} m³/h) basma ≥ %70 ({tr(O["H_sec"] * 0.7, 0)} mSS)'],
        ['Jokey pompa', f'Q={O["jokey"]["Q"]} m³/h  H={O["jokey"]["H"]} mSS  P={tr(O["jokey"]["P"], 1)} kW'],
    ], h=13, baslik='HİDROLİK HESAP ÖZETİ')
    y -= 120
    rows = []
    for t in S['tablo']:
        if t['a'].startswith('H') and t['a'][-1] not in '0123456' :
            continue
        rows.append([f'{t["u"]} → {t["a"]}', f'DN{t["dn"]}', tr(t['L'], 1), f'{t["nd"]}/{t["nt"]}', tr(t['Q'], 0), tr(t['v'], 2),
                     tr(t['j'] * 1000, 2), tr(t['z'], 2), tr(t['Pa'], 3)])
    y = c.tablo(ox, y, ['HAT (DÜĞÜM)', 'ÇAP', 'L (m)', 'DİR./TE', 'Q (l/dk)', 'v (m/s)', 'J (mbar/m)', 'Δz (m)', 'P (bar)'],
                [520, 180, 180, 180, 220, 200, 240, 200, 200], rows[:60], h=11, baslik='HİDROLİK EN UZAK ALAN - HAT HESABI (Hazen-Williams C=120)')
    return y


def cihaz_listesi(c, O, say, ox, oy):
    M = METRAJ
    sat = [
        ['01', 'DİK SPRİNKLER BAŞLIĞI K160, 68 °C', str(say), 'TS EN 12259-1, VdS/LPCB onaylı'],
        ['02', 'ISLAK ALARM VANA İSTASYONU DN200', '2', 'gong + basınç anahtarı + test-drenaj + 2 izl. kelebek'],
        ['03', 'ELEKTRİKLİ YANGIN POMPASI', '1', f'Q={O["Q_sec"]} m³/h H={O["H_sec"]} mSS {O["motor"]} kW, EN 12845'],
        ['04', 'DİZEL YANGIN POMPASI', '1', f'Q={O["Q_sec"]} m³/h H={O["H_sec"]} mSS {O["dizel"]} kW, 500 L yakıt'],
        ['05', 'JOKEY POMPA', '1', f'Q={O["jokey"]["Q"]} m³/h H={O["jokey"]["H"]} mSS {tr(O["jokey"]["P"], 1)} kW'],
        ['06', 'YANGIN SUYU DEPOSU (BETONARME, TOPRAK ALTI)', '1', f'2 göz, V={O["V_sec"]} m³'],
        ['07', 'YANGIN DOLABI TS EN 671-1', str(len(V.DOLAPLAR)), 'Ø25 mm x 30 m yarı sert hortum, kolon montajlı'],
        ['08', 'YER ÜSTÜ HİDRANT DN100 (TS EN 14384)', str(len(V.HIDRANTLAR)), '2xØ75 + 1xØ100 storz, yer altı vanalı'],
        ['09', 'HİDRANT HORTUM DOLABI', str(len(V.HIDRANTLAR)), '2 x Ø75 x 20 m hortum + lans'],
        ['10', 'İTFAİYE BAĞLANTISI', '1', '2 x DN65 storz → DN100 kollektör, çek valf'],
        ['11', 'UÇ TEST VE DRENAJ VANASI DN50', '4', 'her ana dağıtım sonunda'],
        ['12', 'HİDRANT HALKASI BÖLME VANASI DN150', '8', 'yer altı sürgülü vana + vana kutusu'],
    ]
    for dn in ('DN32', 'DN40', 'DN50', 'DN65', 'DN150', 'DN200', 'DN200 (gömülü)', 'DN80 (dolap)', 'DN50 (dolap bağlantı)',
               'DN100 (hidrant bağlantı)', 'Ø160 PE100 PN16 (hidrant halkası)'):
        if dn in M:
            sat.append([str(len(sat) + 1).zfill(2), f'BORU {dn}', f'{tr(M[dn], 0)} m',
                        'EN 10255 orta seri galvaniz / EN 10217 (DN≥150) çelik' if 'PE' not in dn else 'PE100 SDR11 PN16, gömülü'])
    return c.tablo(ox, oy, ['NO', 'CİHAZ / MALZEME', 'ADET / METRAJ', 'TEKNİK ÖZELLİK'], [100, 900, 300, 1100], sat, h=13,
                   baslik='YANGIN TESİSATI CİHAZ LİSTESİ VE METRAJ')


NOTLAR = [
    '1. Sprinkler tesisatı TS EN 12845 HHS (yüksek tehlike depolama, ST1 paletli blok istif ≤ 4,0 m) sınıfına göre ıslak sistem olarak yapılacaktır.',
    '2. Başlıklar K160 dik tip, 68 °C, 3,00 x 3,00 m ızgarada (9 m²/başlık) çatı altına deflektör çatıya 7,5-15 cm olacak şekilde yerleştirilecektir.',
    '3. İstif yüksekliği 4,0 m ile sınırlandırılacak, istif üstü ile başlık deflektörü arasında en az 1,0 m boşluk bırakılacaktır; istif yüksekliği artarsa hesap yenilenecektir.',
    '4. Bina 2 sprinkler zonuna ayrılmıştır (aks 1-13 ve 13-25); her zon kendi ıslak alarm vanasıyla pompa dairesinden gömülü DN200 hatla beslenecektir.',
    '5. Ana dağıtım hatları kolonların B ve C aks yüzünde (aks + 80 cm) çatı eğimine paralel askılanacak, branşmanlar çerçeve aksları arasında 3,00 m aralıkla çekilecektir.',
    '6. Sprinkler boruları EN 10255 orta seri galvaniz (DN≤125) ve EN 10217 (DN≥150) çelik olacak, DN≥65 yivli (groove) bağlantı yapılacaktır.',
    '7. Yangın dolapları TS EN 671-1 Ø25 mm x 30 m yarı sert hortumlu olup kolonlara +1,60 üst kotta monte edilecek, dolap hatları halkadan DN80 ile beslenecektir.',
    '8. Hidrant halkası DN150 (Ø160 PE100 PN16) olarak donma derinliği altında -1,20 kotta gömülecek, hidrantlar cepheden 5-15 m mesafede ve aralarında en çok 50 m olacak şekilde konacaktır.',
    '9. Her hidrantın yanına 2 x Ø75 x 20 m hortum ve lans içeren hidrant hortum dolabı konacaktır.',
    '10. Yangın suyu deposu toprak altı betonarme 2 gözlü, pompa dairesi ile aynı taban kotunda (pozitif emiş) yapılacak, her pompanın ayrı emişi olacaktır.',
    '11. Ana pompalar (elektrikli + dizel) her biri tam kapasitede olacak; %140 debide nominal basıncın en az %70\'ini sağlayacaktır.',
    '12. Pompa dairesi en az +4 °C\'de tutulacak, dizel egzozu susturucu ile dış atmosfere verilecek ve dizel yakıtı en az 6 saat çalışmaya yetecektir.',
    '13. Bütün kesme vanaları izlenebilir (sinyal anahtarlı) olacak ve açık konumda kilitlenecektir.',
    '14. Tesisat 15 bar (veya çalışma basıncı + 5 bar) ile 2 saat basınç testine tabi tutulacak, test öncesi yıkanacaktır.',
    '15. Teknik depo bölümündeki bölme duvarları başlık yerleşimine göre yerinde kontrol edilecek, duvara 1,5 m\'den yakın başlık kaymaları ızgara korunarak yapılacaktır.',
    '16. Hidrant ve dolap hatları mimari vaziyete göre yerinde kesinleştirilecek, araç yollarının altında koruma borusu kullanılacaktır.',
]


def antet(c, x, y):
    """sağ alt antet (sol alt köşe x,y)"""
    c.R(x, y, x + 1800, y + 700, 'ROTAS-PAFTA', 3)
    satir = ['ROTAŞ MÜHENDİSLİK . PROJE . MÜŞAVİRLİK',
             'Semerciler Mah. Sait Faik Sk. No:22/C Z01 Adapazarı/Sakarya - 0264 272 00 49 - rotasmuhendislik@gmail.com',
             'İŞ: OBA MAKARNACILIK SAN. ve TİC. A.Ş. DEPOLAMA BİNASI',
             'YER: SAKARYA / HENDEK - ÇAĞLAYAN MAH. 900 ADA 84 PARSEL',
             'PROJE: YANGIN TESİSATI (SPRİNKLER - DOLAP - HİDRANT - POMPA/DEPO)',
             'PROJE SORUMLUSU: Mak. Müh. Bayram GENÇ',
             'ÇİZEN: Can ÖZKAYA - Teknik Ressam',
             'TARİH: 10.2026']
    for i, s in enumerate(satir):
        c.T(x + 30, y + 650 - i * 80, s, 30 if i == 0 else 20, 'TL', 'ROTAS-PAFTA')


LEJANT = [
    ('ROTAS-SMB-SPR-DIK', 'DİK (UPRIGHT) SPRİNKLER K160 68 °C'),
    ('ROTAS-SMB-KOLON-YUK', 'SPRİNKLER KOLONU (SK)'),
    ('ROTAS-SMB-DOLAP-PLAN', 'YANGIN DOLABI (PLAN) TS EN 671-1'),
    ('ROTAS-SMB-HIDRANT', 'YER ÜSTÜ HİDRANT DN100'),
    ('ROTAS-SMB-HORTUM-DOLABI', 'HİDRANT HORTUM DOLABI'),
    ('ROTAS-SMB-POMPA-SEMA', 'POMPA (ŞEMA)'),
    (RS.blok_adi('kelebek'), 'KELEBEK / SÜRGÜLÜ KESME VANASI'),
    (RS.blok_adi('izlenebilir_kelebek'), 'İZLENEBİLİR (SİNYAL ANAHTARLI) KELEBEK VANA'),
    (RS.blok_adi('cekvalf'), 'ÇEK VALF (ok: akış yönü)'),
    (RS.blok_adi('islak_alarm'), 'ISLAK ALARM VANA İSTASYONU'),
    (RS.blok_adi('test_drenaj'), 'UÇ TEST VE DRENAJ SETİ'),
    (RS.blok_adi('manometre'), 'MANOMETRE'),
    (RS.blok_adi('storz'), 'İTFAİYE BAĞLANTI AĞZI STORZ DN65'),
    (RS.blok_adi('yangin_dolabi_kolon'), 'YANGIN DOLABI (ŞEMA)'),
    (RS.blok_adi('kuresel'), 'KÜRESEL VANA'),
]
CIZGI_LEJ = [('ROTAS-YANGIN-SPR-ANA', 6, 'SPRİNKLER ANA DAĞITIM / KOLON (DN150-DN200)'),
             ('ROTAS-YANGIN-SPR-BORU', 0, 'SPRİNKLER BRANŞMANI (DN32-DN65)'),
             ('ROTAS-YANGIN-SPR-GOMULU', 6, 'GÖMÜLÜ ZON BESLEME HATTI DN200'),
             ('ROTAS-YANGIN-DOLAP-BORU', 4, 'YANGIN DOLABI HATTI DN80'),
             ('ROTAS-YANGIN-HIDRANT-BORU', 8, 'HİDRANT HALKASI DN150 (GÖMÜLÜ)'),
             ('ROTAS-YANGIN-ALAN', 5, 'HİDROLİK İŞLETME ALANI'),
             ('ROTAS-YANGIN-ZON', 3, 'SPRİNKLER ZON SINIRI'),
             ('ROTAS-YANGIN-DOLAP-ETKI', 0, 'DOLAP ETKİ ALANI (30 m hortum + 5 m su atımı)')]


def lejant(c, x, y, h=12):
    for b in RS.TANIM:
        RS.blok_tanimla(c.doc, b)
    c.T(x, y + 15, 'LEJANT', h * 1.6, 'BL', 'ROTAS-LEJANT')
    W0, W1, rh = 150, 560, 50
    yy = y
    c.L((x, yy), (x + W0 + W1, yy), 'ROTAS-LEJANT')
    for ad, ac in LEJANT:
        from ezdxf import bbox
        e = bbox.extents(c.doc.blocks[ad], fast=True)
        w_, h_ = e.extmax.x - e.extmin.x, e.extmax.y - e.extmin.y
        sc = min(2.5, (W0 - 30) / max(w_, 1), (rh - 12) / max(h_, 1))
        cx, cy = (e.extmin.x + e.extmax.x) / 2 * sc, (e.extmin.y + e.extmax.y) / 2 * sc
        c.m.add_blockref(ad, (x + W0 / 2 - cx, yy - rh / 2 - cy), dxfattribs={'layer': 'ROTAS-LEJANT', 'xscale': sc, 'yscale': sc})
        c.T(x + W0 + 10, yy - rh / 2, ac, h, 'ML', 'ROTAS-LEJANT')
        yy -= rh
        c.L((x, yy), (x + W0 + W1, yy), 'ROTAS-LEJANT')
    for lay, w, ac in CIZGI_LEJ:
        c.L((x + 20, yy - rh / 2), (x + W0 - 20, yy - rh / 2), lay, w)
        c.T(x + W0 + 10, yy - rh / 2, ac, h, 'ML', 'ROTAS-LEJANT')
        yy -= rh
        c.L((x, yy), (x + W0 + W1, yy), 'ROTAS-LEJANT')
    for xx in (x, x + W0, x + W0 + W1):
        c.L((xx, y), (xx, yy), 'ROTAS-LEJANT')
    return yy


def grupla(c, fn, olcek):
    """fn(c) yerel koordinatta çizer; yeni öğeler olcek ile büyütülür. Dönüş (öğeler, bbox)"""
    from ezdxf.math import Matrix44
    from ezdxf import bbox
    once = {e.dxf.handle for e in c.m}
    fn(c)
    yeni = [e for e in c.m if e.dxf.handle not in once]
    if olcek != 1:
        for e in yeni:
            e.transform(Matrix44.scale(olcek, olcek, olcek))
    return yeni, bbox.extents(yeni, fast=True)


def pompa_kesit(c, O):
    sys.path.insert(0, os.path.join(KOK, 'motor', 'deneme', 'pompa_grubu'))
    import yangin as YP
    g = json.load(open(os.path.join(os.path.dirname(__file__), 'pompa_girdi_oba.json')))
    g['deneme'] = False
    g['depo']['V_m3'] = O['V_sec']
    g['elektrikli'].update(Q=O['Q_sec'], H=O['H_sec'], P=O['motor'])
    g['dizel'].update(Q=O['Q_sec'], H=O['H_sec'], P=O['dizel'])
    g['jokey'].update(Q=O['jokey']['Q'], H=O['jokey']['H'], P=O['jokey']['P'])
    tmp = '/tmp/claude-0/oba/pompa_oba.dxf'
    YP.ciz(g, tmp)
    import_dxf(c, tmp, 0, 0)


def main():
    O = V.ozet()
    S = O['S']
    doc = yeni_doc(KAT)
    bloklar(doc)
    c = C(doc)
    say, n_mim = plan(c, S, O)
    # ---- alt bölge: 1/100 paftada okunacak şekilde detaylar ölçeklenerek yerleştirilir (başlıklarda gerçek ölçek yazılı)
    sol, ust, GEN, ara = X0 - 1150, Y0 - 1700, 17800, 450
    gruplar = [
        (lambda c: sema(c, O, 0, 0), 1.5),
        (lambda c: pompa_kesit(c, O), 4.0),
        (lambda c: depo_detay(c, O, 0, 0), 2.0),
        (lambda c: detaylar(c, 0, 0), 2.0),
        (lambda c: tablolar(c, O, 0, 0), 2.0),
        (lambda c: cihaz_listesi(c, O, say, 0, 0), 2.0),
        (lambda c: c.notlar(0, 0, 'NOTLAR', NOTLAR, h=14, gen=2900), 2.0),
        (lambda c: lejant(c, 0, 0), 2.0),
    ]
    x, y, satir_h = sol, ust, 0
    for fn, s in gruplar:
        yeni, b = grupla(c, fn, s)
        w, h = b.extmax.x - b.extmin.x, b.extmax.y - b.extmin.y
        if x > sol and x + w > sol + GEN:
            x, y, satir_h = sol, y - satir_h - ara, 0
        dx, dy = x - b.extmin.x, y - b.extmax.y
        for e in yeni:
            e.translate(dx, dy, 0)
        x += w + ara
        satir_h = max(satir_h, h)
    alt = y - satir_h - ara
    antet(c, sol + GEN - 1800, alt - 800)
    pafta_cerceve(c, sol - 150, alt - 900, sol + GEN + 150, ust + 300, '', '')
    os.makedirs(CIKTI, exist_ok=True)
    yol = os.path.join(CIKTI, 'OBA_84_YANGIN_TESISATI.dxf')
    doc.saveas(yol)
    json.dump({k: (v if not isinstance(v, float) else round(v, 3)) for k, v in O.items() if k not in ('S', 'H', 'D')} |
              {'Qs': S['Qs'], 'P0': S['P0'], 'Qf': S['Qf'], 'yog': S['yog'], 'basliklar': say, 'metraj': METRAJ,
               'H': O['H'], 'D': O['D']}, open(os.path.join(CIKTI, 'ozet.json'), 'w'), ensure_ascii=False, indent=1, default=str)
    print('kaydedildi', yol, 'başlık', say, 'mimari öğe', n_mim)
    print('metraj', {k: round(v) for k, v in METRAJ.items()})
    return yol, O


if __name__ == '__main__':
    main()
