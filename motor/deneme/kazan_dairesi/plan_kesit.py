# -*- coding: utf-8 -*-
"""KAZAN DAİRESİ PLANI (1/50) + KESİT A-A + GÖRÜNÜŞ B (kazan duvarı) + lejant + cihaz listesi (deneme: kazan_dairesi).

Kullanım:  python3 plan_kesit.py girdi.json cikti_PLAN_KESIT.dxf [onizleme.png] [--numara R1|R2]
API (her projede):  onayli_kazan_dairesi(doc_veya_msp, girdi_json_veya_dict, x0, y0) -> kapsam kutusu

Girdi: prensip şeması JSON'u (kazan_dairesi.py ile aynı) + "plan" bloğu (BENIOKU.md). Numaralar (K-, P-, V-, DK-, GT-,
KL-, HA-, TA-, GF-, GR-, SV-, GA-, B-, BY-, NU-, EV-, M-, TM-, HP-) prensip şeması önce bellekte üretilerek oradan alınır;
böylece plan / kesit / görünüş / cihaz listesi şemayla birebir aynı numaraları taşır.

Yerleşim kuralları (07_ISITMA_DOGALGAZ §5): duvar tipi kaskad kazanlar kazan duvarında; kazan önü serbest mesafe ≥ kazan
boyu + 1,00 m; 350 kW üstü veya alan > 100 m² ise ≥ 2 kapı (dışa açılır, kendiliğinden kapanır, ≥ 90 dk); bölme
duvar/döşeme ≥ 120 dk (EI 120); menfezler §5.4 (S_A = F·a·2,25·(ΣQ+70) cm², ΣQ > 1000 kW'ta ΣQ/3600 m²); gaz sayacı
ve ana kesme vanası + selenoid kazan dairesi dışında; gaz alarm üst menfezden yüksekte.
Birim cm; plan, kesit ve görünüş 1/50 (model uzayında gerçek ölçü).
"""
# ONAYLI (14.10.2026 16:39, kullanıcı): "BU KAZAN DAIRESI DOĞRU OLANDI ... HER YERDE BUNU KULLANACAKSIN".
# Merkezi sistem kazan dairesi plan / kesit / kısmi görünüşü HER YERDE bu üretici ile çizilir; görünüşü değiştirilmez.
import copy
import importlib
import json
import math
import os
import sys
import tempfile

from ezdxf.addons import Importer
from ezdxf import recover
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import LineString, Polygon, box as sbox
from shapely.geometry.polygon import orient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bloklar as BL            # noqa: E402
import geometri as GM           # noqa: E402
import kazan_dairesi_r1 as KD   # noqa: E402  (onaylı çizimin dondurulmuş tabanı — görünüş buradan)
from kazan_dairesi_r1 import (GID, DON, GAZ, BACA, YOG, VANA, CIHAZ, POMPA, GAZS, KOL, YAZ, BAS, tr, dn_su, dn_gaz,  # noqa
                           dn_no)

# ----------------------------------------------------------------------------- ek katmanlar
DUV, TAR, OLC, KOTL = 'ROTAS-MIMARI-DUVAR', 'ROTAS-MIMARI-TARAMA', 'ROTAS-OLCU', 'ROTAS-KOT'
KAPI, MENF, BAKIM, KESH = 'ROTAS-MIMARI-KAPI', 'ROTAS-HAVALANDIRMA-MENFEZ', 'ROTAS-BAKIM-ALANI', 'ROTAS-KESIT-HATTI'
PIS, LJ_C, LJ_Y, LJ_B = 'ROTAS-PIS-SU', 'ROTAS-HESAP-CIZGI', 'ROTAS-HESAP-YAZI', 'ROTAS-HESAP-BASLIK'
LJ_S = 'ROTAS-HESAP-SEMBOL'
EK_KATMAN = {DUV: (7, 'Continuous'), TAR: (8, 'Continuous'), OLC: (3, 'Continuous'), KOTL: (3, 'Continuous'),
             KAPI: (7, 'Continuous'), MENF: (4, 'Continuous'), BAKIM: (8, 'DASHED'), KESH: (1, 'DASHDOT'),
             PIS: (6, 'Continuous'), LJ_S: (7, 'Continuous')}

KOLLEKTOR_YARI = 9.0


# ============================================================================ şemadan numara haritası
def sema_modulu(kaynak):
    """numara kaynağı: 'R1' = onay anındaki şema (kazan_dairesi_r1), 'R2' = teslimdeki şema (kazan_dairesi.py)"""
    return KD if str(kaynak).upper() == 'R1' else importlib.import_module('kazan_dairesi')


def numara_haritasi(P, kaynak='R1'):
    """Prensip şemasını geçici dosyaya üretir; cihaz rollerine göre şema numaralarını döndürür.
    kaynak='R2': numaralar teslimdeki R2 prensip şemasıyla (radyatör kolon şemasına gömülü olan dahil) aynı olur."""
    fd, yol = tempfile.mkstemp(suffix='.dxf')
    os.close(fd)
    try:
        S0 = sema_modulu(kaynak).ciz(P, yol)
    finally:
        os.remove(yol)
    satir = S0.numarala()                    # aynı numaraları yeniden üretir (deterministik)
    C = S0.cihazlar

    def f(pred):
        return [c['etiket'] for c in C if pred(c)]
    n = int(P['kazan']['adet'])
    M = {}
    M['K'] = f(lambda c: c['kod'] == 'K')
    M['PK'] = f(lambda c: c['kod'] == 'P' and (c['ad'] or '').startswith('KAZAN SİRK'))
    M['PZ'] = f(lambda c: c['kod'] == 'P' and (c['ad'] or '').startswith('ZON POMPASI'))
    M['PB'] = f(lambda c: c['kod'] == 'P' and c['ad'] == 'BOYLER ŞARJ POMPASI')
    M['EVK'] = f(lambda c: c['ad'] == 'EMNİYET VENTİLİ (KAZAN)')
    M['TM'] = f(lambda c: c['kod'] == 'TM')
    M['MN'] = f(lambda c: c['kod'] == 'M' and c['ad'] == 'MANOMETRE')
    M['MG'] = f(lambda c: c['ad'] == 'MANOMETRE (GAZ)')
    M['HP'] = f(lambda c: c['kod'] == 'HP')
    M['CV'] = f(lambda c: c['ad'] == 'ÇEK VALF')
    M['VG'] = f(lambda c: c['ad'] in ('KÜRESEL VANA', 'KELEBEK VANA'))
    M['PT'] = f(lambda c: c['ad'] == 'PİSLİK TUTUCU (Y TİPİ)')
    M['VGC'] = f(lambda c: c['ad'] == 'DOĞALGAZ KÜRESEL VANASI (CİHAZ)')
    M['ESN'] = f(lambda c: c['ad'] == 'ESNEK BAĞLANTI (GAZ)')
    M['VGA'] = f(lambda c: c['ad'].startswith('DOĞALGAZ ANA KESME'))
    M['VGK'] = f(lambda c: c['ad'] == 'DOĞALGAZ KÜRESEL VANASI (KOLLEKTÖR)')
    M['KIL'] = f(lambda c: c['ad'].startswith('KİLİTLENEBİLİR'))
    for k in ('DK', 'HA', 'TA', 'GT', 'KL', 'BY', 'NU', 'B', 'GF', 'GR', 'SV', 'GA'):
        M[k] = f(lambda c, k=k: c['kod'] == k)
    # genel vana sırası (kazan_dairesi.ciz ekleme sırası)
    VG = M['VG']
    o = 2 * n
    M['V_KAZAN_GID'] = [VG[2 * i] for i in range(n)]
    M['V_KAZAN_DON'] = [VG[2 * i + 1] for i in range(n)]
    M['V_PG1'], M['V_PG2'], M['V_PD1'], M['V_PD2'] = VG[o], VG[o + 1], VG[o + 2], VG[o + 3]
    o += 4 + (2 if P.get('doldurma', True) else 0)
    M['V_SG'], M['V_SD'] = VG[o], VG[o + 1]
    o += 2
    pt_o = 1 if P.get('doldurma', True) else 0
    cv_o = n + (1 if P.get('doldurma', True) else 0)
    pz = 0
    zon = []
    for z in P.get('zonlar', []):
        for _ in range(int(z.get('adet', 1))):
            d = {'PT': M['PT'][pt_o]}
            pt_o += 1
            if z.get('yedek'):
                d['V'] = [VG[o], VG[o + 1], VG[o + 2], VG[o + 3], VG[o + 4]]     # gövde, sol(2), sağ(2)
                d['VD'] = VG[o + 5]
                d['P'] = M['PZ'][pz:pz + 2]
                d['CV'] = M['CV'][cv_o:cv_o + 2]
                o += 6; pz += 2; cv_o += 2
            else:
                d['V'] = [VG[o], VG[o + 1]]
                d['VD'] = VG[o + 2]
                d['P'] = M['PZ'][pz:pz + 1]
                d['CV'] = M['CV'][cv_o:cv_o + 1]
                o += 3; pz += 1; cv_o += 1
            zon.append(d)
    M['ZON'] = zon
    if P.get('boyler'):
        M['BOY'] = {'V': [VG[o], VG[o + 1]], 'VD': VG[o + 2], 'CV': M['CV'][cv_o]}
    # tutarlılık denetimi
    assert len(M['K']) == n and len(M['PK']) in (0, n) and len(M['DK']) == 1, 'şema numara haritası uyuşmadı'
    return M, satir


# ============================================================================ yardımcılar
def blok_al(doc, dosya, blok, yeni_ad=None):
    BL.mty_hazirla()
    ad = yeni_ad or blok
    if ad in doc.blocks:
        return ad
    s = recover.readfile(os.path.join(BL.MTY_DIR, dosya))[0]
    im = Importer(s, doc)
    if blok is None:
        hedef = doc.blocks.new(ad)
        im.import_entities(s.modelspace(), target_layout=hedef)
    else:
        im.import_block(blok, rename=False)
    im.finalize()
    return ad


def plan_bloklari(doc, g, d, h, rf):
    B = doc.blocks
    a = {'layer': '0'}
    # duvar tipi kazan PLAN: orijin ön-sol köşe, duvar y=d tarafında; üstte baca çıkışı (daire)
    b = B.new('ROTAS-KAZAN-PLAN')
    b.add_lwpolyline([(0, 0), (g, 0), (g, d), (0, d)], close=True, dxfattribs=a)
    b.add_lwpolyline([(4, 4), (g - 4, 4), (g - 4, 9), (4, 9)], close=True, dxfattribs=a)         # ön panel
    b.add_circle((g / 2, d / 2), rf, dxfattribs=a)
    # ön görünüş: orijin alt-sol; baca adaptörü üst ortada
    b = B.new('ROTAS-KAZAN-ON')
    b.add_lwpolyline([(0, 0), (g, 0), (g, h), (0, h)], close=True, dxfattribs=a)
    b.add_lwpolyline([(g * 0.15, h * 0.10), (g * 0.85, h * 0.10), (g * 0.85, h * 0.24), (g * 0.15, h * 0.24)],
                     close=True, dxfattribs=a)                                                  # kontrol paneli
    b.add_lwpolyline([(g * 0.55, h * 0.14), (g * 0.78, h * 0.14), (g * 0.78, h * 0.20), (g * 0.55, h * 0.20)],
                     close=True, dxfattribs=a)                                                  # ekran
    for x in (g * 0.22, g * 0.32, g * 0.42):
        b.add_circle((x, h * 0.17), 1.6, dxfattribs=a)
    alev = [(g * 0.42, h * 0.50), (g * 0.58, h * 0.50), (g * 0.50, h * 0.66)]
    b.add_lwpolyline(alev, close=True, dxfattribs=a)
    b.add_lwpolyline([(g / 2 - rf, h), (g / 2 - rf, h + 10), (g / 2 + rf, h + 10), (g / 2 + rf, h)], dxfattribs=a)
    # yan görünüş (kesit): orijin duvar dibi-alt, +x odaya doğru
    b = B.new('ROTAS-KAZAN-YAN')
    b.add_lwpolyline([(0, 0), (d, 0), (d, h), (0, h)], close=True, dxfattribs=a)
    b.add_line((d - 5, 3), (d - 5, h - 3), dxfattribs=a)                                          # ön kapak
    b.add_lwpolyline([(d / 2 - rf, h), (d / 2 - rf, h + 10), (d / 2 + rf, h + 10), (d / 2 + rf, h)], dxfattribs=a)
    for y in (h * 0.3, h * 0.7):
        b.add_line((0, y), (-2, y), dxfattribs=a)                                                 # duvar askısı
    # kot işareti: tepe (0,0) çizgide, üçgen yukarıda, yarısı dolu
    b = B.new('ROTAS-KOT')
    b.add_lwpolyline([(0, 0), (-5, 8), (5, 8)], close=True, dxfattribs=a)
    hh = b.add_hatch(dxfattribs=a)
    hh.paths.add_polyline_path([(0, 0), (0, 8), (-5, 8)], is_closed=True)
    b.add_line((-14, 0), (14, 0), dxfattribs=a)
    # menfez (ızgara) planı: kanatlar
    b = B.new('ROTAS-MENFEZ-ON')        # görünüş: 1×1 birim, ölçekle büyür
    b.add_lwpolyline([(0, 0), (1, 0), (1, 1), (0, 1)], close=True, dxfattribs=a)
    for k in range(1, 6):
        b.add_line((0.08, k / 6), (0.92, k / 6), dxfattribs=a)


# ============================================================================ çizim sınıfı
class Pafta(KD.Sema):
    def __init__(self, P):
        super().__init__(P)
        for ad, (renk, lt) in EK_KATMAN.items():
            if ad not in self.doc.layers:
                self.doc.layers.add(ad, color=renk, linetype=lt)
        self.olcu_no = 0

    # ---------------------------------------------------------------- mimari
    def duvar(self, poly, tarama=True, lay=DUV):
        geos = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
        for g in geos:
            if g.is_empty or g.area < 1:
                continue
            for r in [g.exterior] + list(g.interiors):
                self.msp.add_lwpolyline(list(r.coords)[:-1], close=True, dxfattribs={'layer': lay})
            if tarama:
                hh = self.msp.add_hatch(dxfattribs={'layer': TAR})
                hh.set_pattern_fill('ANSI31', scale=1.2)
                hh.paths.add_polyline_path(list(g.exterior.coords)[:-1], is_closed=True, flags=1)
                for r in g.interiors:
                    hh.paths.add_polyline_path(list(r.coords)[:-1], is_closed=True, flags=0)

    def olcu(self, p1, p2, yon, d, yazi=None, h=9.0, zincir=None):
        """yatay/düşey ölçü (blok): p1-p2 ölçülür, ölçü çizgisi yon (birim dik vektör) tarafında d uzakta.
        zincir: ara noktalar listesi (aynı doğrultuda)"""
        self.olcu_no += 1
        ad = f'ROTAS-OLCU-{self.olcu_no:03d}'
        b = self.doc.blocks.new(ad)
        a = {'layer': '0'}
        nok = sorted([p1, p2] + list(zincir or []), key=lambda p: (p[0], p[1]))
        yatay = abs(p1[1] - p2[1]) < 1e-6 if not zincir else abs(nok[0][1] - nok[-1][1]) < 1e-6 or yon[0] == 0
        ux, uy = yon
        if yatay:
            yy = max(p[1] for p in nok) + d if uy > 0 else min(p[1] for p in nok) - d
            b.add_line((nok[0][0], yy), (nok[-1][0], yy), dxfattribs=a)
            for p in nok:
                b.add_line((p[0], p[1] + uy * 3), (p[0], yy + uy * 3), dxfattribs=a)
                b.add_line((p[0] - 2.5, yy - 2.5), (p[0] + 2.5, yy + 2.5), dxfattribs=a)
            for q1, q2 in zip(nok, nok[1:]):
                L = q2[0] - q1[0]
                if L < 1:
                    continue
                s = yazi if (yazi and len(nok) == 2) else tr(L / 100, 2)
                t = b.add_text(s, height=h, dxfattribs={'layer': '0', 'style': 'ROTAS', 'width': KD.WF})
                t.set_placement(((q1[0] + q2[0]) / 2, yy + 2), align=TA.BOTTOM_CENTER)
        else:
            xx = max(p[0] for p in nok) + d if ux > 0 else min(p[0] for p in nok) - d
            nok = sorted(nok, key=lambda p: p[1])
            b.add_line((xx, nok[0][1]), (xx, nok[-1][1]), dxfattribs=a)
            for p in nok:
                b.add_line((p[0] + ux * 3, p[1]), (xx + ux * 3, p[1]), dxfattribs=a)
                b.add_line((xx - 2.5, p[1] - 2.5), (xx + 2.5, p[1] + 2.5), dxfattribs=a)
            for q1, q2 in zip(nok, nok[1:]):
                L = q2[1] - q1[1]
                if L < 1:
                    continue
                s = yazi if (yazi and len(nok) == 2) else tr(L / 100, 2)
                t = b.add_text(s, height=h, rotation=90, dxfattribs={'layer': '0', 'style': 'ROTAS', 'width': KD.WF})
                t.set_placement((xx - 2, (q1[1] + q2[1]) / 2), align=TA.BOTTOM_CENTER)
        self.msp.add_blockref(ad, (0, 0), dxfattribs={'layer': OLC})

    def kot(self, p, s, sag=True, h=9.0):
        self.msp.add_blockref('ROTAS-KOT', p, dxfattribs={'layer': KOTL})
        self.yazi((p[0] + (17 if sag else -17), p[1] + 4), s, h, KOTL, TA.MIDDLE_LEFT if sag else TA.MIDDLE_RIGHT)

    def etiket(self, c, s):
        if c is not None:
            c['etiket'] = s
            c['kod'] = c.get('kod') or 'X'
        return c

    def nesne(self, s, at, tercih=None, buyuk=True, sabit=None):
        c = dict(kod='X', ad='', oz=(), at=at, ent=None, tercih=tercih, boru_aci=None, yon=None, etiket=s,
                 buyuk=buyuk, sabit=sabit)
        self.cihazlar.append(c)
        return c


# ============================================================================ geometri yardımcıları
def kenar_bul(oda, taraf, konum):
    """oda kenarı: taraf alt/ust (konum = x) veya sol/sag (konum = y). Dönen: (p, u teğet, n dış normal)"""
    minx, miny, maxx, maxy = oda.bounds
    if taraf in ('alt', 'ust'):
        ln = LineString([(konum, miny - 10), (konum, maxy + 10)])
    else:
        ln = LineString([(minx - 10, konum), (maxx + 10, konum)])
    x = ln.intersection(oda.exterior)
    pts = [x] if x.geom_type == 'Point' else list(getattr(x, 'geoms', []))
    pts = [(q.x, q.y) for q in pts if q.geom_type == 'Point']
    if not pts:
        raise ValueError(f'{taraf} duvarında {konum} konumu oda sınırında değil')
    key = {'alt': lambda q: q[1], 'ust': lambda q: -q[1], 'sol': lambda q: q[0], 'sag': lambda q: -q[0]}[taraf]
    p = min(pts, key=key)
    n = {'alt': (0, -1), 'ust': (0, 1), 'sol': (-1, 0), 'sag': (1, 0)}[taraf]
    u = (1, 0) if taraf in ('alt', 'ust') else (0, 1)
    return p, u, n


def bosluk(p, u, n, b, t):
    """duvarda b genişliğinde açıklık dikdörtgeni (iç yüzden dış yüze, ±1 cm taşkın)"""
    pts = []
    for su, sn in ((-b / 2, -1), (b / 2, -1), (b / 2, t + 1), (-b / 2, t + 1)):
        pts.append((p[0] + u[0] * su + n[0] * sn, p[1] + u[1] * su + n[1] * sn))
    return Polygon(pts)


def menfez_olcu(S_cm2):
    """F=1 (kenar oranı ≤ 1,5) dikdörtgen: 5 cm modüllü b × h ≥ S"""
    b = math.ceil(math.sqrt(S_cm2) / 5) * 5
    h = math.ceil(S_cm2 / b / 5) * 5
    while b / h > 1.5:
        b -= 5
        h = math.ceil(S_cm2 / b / 5) * 5
    return b, h


def gt_cap(hacim):
    for v, d in ((50, 38), (100, 45), (200, 50), (300, 63), (500, 75), (800, 80), (1000, 80)):
        if hacim <= v:
            return d
    return 100


def boyler_cap(hacim):
    for v, d in ((300, 60), (500, 75), (800, 85), (1000, 95), (1500, 110), (2000, 125)):
        if hacim <= v:
            return d
    return 140


def cap_cm(s, vars=30.0):
    try:
        return float(str(s).replace('Ø', '').replace('DN', '').strip()) / 10.0
    except ValueError:
        return vars


# ============================================================================ ana kurgu
def uret(P, cikti, numara='R1'):
    """cikti=None: dosyaya yazmaz (API için); S.doc, S.kapsam, S.cerceve, S.satir, S.harita döner."""
    M, satir = numara_haritasi(P, numara)
    PL = P['plan']
    S = Pafta(P)
    doc, msp = S.doc, S.msp
    uy = S.uyarilar

    # ---------------------------------------------------------------- hesap büyüklükleri (şema ile aynı)
    rej = P.get('rejim', {'gidis': 90, 'donus': 70})
    tg, td = rej['gidis'], rej['donus']
    dT = tg - td
    K = P['kazan']
    n, qk = int(K['adet']), float(K['kapasite_kw'])
    QT = n * qk
    q_k, q_p = qk / (1.163 * dT), QT / (1.163 * dT)
    dn_k, dn_p = dn_su(q_k), dn_su(q_p)
    zonlar = P.get('zonlar', [])
    boy = P.get('boyler')
    q_s = sum(z['debi'] * z.get('adet', 1) for z in zonlar) + (boy['sarj_pompa']['debi'] if boy else 0)
    dn_s = dn_su(q_s)
    gz = P.get('dogalgaz', {})
    Hu, eta = 9.59, 0.97
    qg = QT / (Hu * eta)
    dng_k = gz.get('kazan_cap') or dn_gaz(qk / (Hu * eta), 5.0)
    dng = gz.get('kollektor_cap') or dn_gaz(qg, 6.0)
    dng_g = gz.get('giris_cap') or dn_gaz(qg, 15.0 if gz.get('regulator') else 6.0)
    reg = gz.get('regulator')
    notr = P.get('notralizasyon')

    def vblok(dn):
        return 'MTY-KELEBEK VANA' if dn_no(dn) >= 65 else 'MTY-KURESEL VANA'

    # ---------------------------------------------------------------- oda ve ölçüler
    oda = orient(Polygon(PL['oda']), 1.0)
    t = float(PL.get('duvar', 25))
    H = float(PL.get('ic_yukseklik', 350))
    ds = float(PL.get('doseme', 30))
    ko = PL.get('kazan_olcu', {})
    g, d, h = float(ko.get('g', 60)), float(ko.get('d', 55)), float(ko.get('h', 100))
    ara, zb = float(ko.get('ara', 40)), float(ko.get('alt_kot', 185))
    rf = float(ko.get('baca_cap', 16)) / 2
    minx, miny, maxx, maxy = oda.bounds
    Y_W = maxy                                   # kazan duvarı (üst kenar) iç yüzü
    Y_F = Y_W - d - 2                            # kazan ön yüzü (duvardan 2 cm askı boşluğu)
    bc = P.get('baca', {})
    r_bi = cap_cm(bc.get('cap', 'Ø300')) / 2
    r_bo = r_bi + 3
    bx = float(PL['baca'][0])
    by = Y_F + d / 2
    if abs(float(PL['baca'][1]) - by) > 1:
        uy.append(f'baca y={PL["baca"][1]} kazan baca ekseni hizasına ({tr(by, 0)}) alındı')
    gt = P.get('genlesme', {'hacim_l': 500})
    r_gt = gt_cap(gt['hacim_l']) / 2
    s_gt = r_gt / 45.0
    r_dk = cap_cm(P.get('denge_kabi', {}).get('cap', 'Ø300')) / 2
    # başlık ofsetleri (kazan ön yüzünden): gaz 12, yoğuşma 24, dönüş 40, gidiş 100
    y_gz, y_yg, y_d, y_g = Y_F - 12, Y_F - 24, Y_F - 40, Y_F - 100
    yc = (y_d + y_g) / 2
    fx = g / 60.0
    oy, ogz, odn, ogd = 3 * fx, 14 * fx, 24 * fx, 56 * fx            # kazan bağlantı x ofsetleri
    x_start = PL.get('kazan_baslangic') or max(minx + 190, bx + r_bo + 130, minx + 30 + 35 + 2 * r_gt + 15 + 25)
    xs = [x_start + i * (g + ara) for i in range(n)]
    xL = xs[-1]
    x_gt = x_start - r_gt - 15
    x_yog = x_gt - r_gt - 35
    x_dk = xL + max(ogd, odn) + 175
    x_k0 = x_dk + 110
    # zon genişlikleri
    zgen = []
    for z in zonlar:
        for _ in range(int(z.get('adet', 1))):
            zgen.append(130.0 if z.get('yedek') else 70.0)
    x_z = x_k0 + 50
    zx = []
    for w in zgen:
        zx.append(x_z if w > 100 else x_z - 15)
        x_z += w
    x_kg1 = zx[-1] + 50 if zx else x_k0 + 60
    if boy:
        x_bg = x_kg1 + 70
        x_kg1 = x_bg + 30
        x_bd = x_kg1 + 40
        x_kd1 = x_bd + 25
    else:
        x_kd1 = x_kg1
    y_kg = yc - 70
    y_kd = yc + 6
    if x_kd1 + 40 > maxx:
        uy.append(f'oda genişliği yetersiz: sekonder kollektör {tr(x_kd1 + 40, 0)} > {tr(maxx, 0)}')

    # ---------------------------------------------------------------- bloklar
    plan_bloklari(doc, g, d, h, rf)
    B_DK = blok_al(doc, 'RADYATOR TESISATI__VANALAR__MTY-DENGE KABI.dxf', 'MTY-DENGE KABI PLAN')
    B_GT = blok_al(doc, 'RADYATOR TESISATI__VANALAR__MTY-KAZAN VE KOMBİ PLAN KOLON.dxf', 'aGENLESME DEPOSU (PLAN-1)')
    B_BY = blok_al(doc, 'RADYATOR TESISATI__VANALAR__MTY-BOYLER KAT- KOLON.dxf', 'BOYLER KAT PLANI')
    B_YS = blok_al(doc, 'SIHHI TESISAT__KAT PLANI__YER SUZGECI DN1001.dxf', None, 'MTY-YER SUZGECI DN100')
    BL.YARIM[B_DK] = 20.0

    # ---------------------------------------------------------------- kapılar / menfezler / duvarlar
    alan = oda.area / 1e4
    kapilar = list(PL.get('kapilar', []))
    gerek_kapi = 2 if (QT > 350 or alan > 100) else 1
    if len(kapilar) < gerek_kapi:
        k0 = kapilar[0] if kapilar else {'duvar': 'alt', 'konum': minx + 150, 'genislik': 100}
        p0, u0, _ = kenar_bul(oda, k0['duvar'], k0['konum'])
        ek = dict(k0)
        ek['konum'] = (maxx - 150) if k0['duvar'] in ('alt', 'ust') else (miny + 150)
        ek['otomatik'] = True
        kapilar.append(ek)
        uy.append(f'{tr(QT, 0)} kW > 350 kW: 2. kapı otomatik eklendi ({ek["duvar"]} duvar, {tr(ek["konum"], 0)})')
    # menfez hesabı (07 §5.4)
    Fk, ak = float(PL.get('menfez_F', 1.0)), float(PL.get('menfez_a', 1.2))
    if QT < 1000:
        S_A = Fk * ak * 2.25 * (QT + 70)
        formul = f'S_A = F·a·2,25·(ΣQ+70) = {tr(Fk, 2)}·{tr(ak, 2)}·2,25·({tr(QT, 0)}+70) = {tr(S_A, 0)} cm²'
    else:
        S_A = QT / 3600 * 1e4
        formul = f'S_A = ΣQ/3600 = {tr(QT, 0)}/3600 = {tr(S_A / 1e4, 3)} m² = {tr(S_A, 0)} cm²'
    oran = float(PL.get('ust_menfez_orani', 0.6))
    S_U = max(180.0, oran * S_A)
    ba, ha = menfez_olcu(S_A / (Fk * 1.0))
    bu, hu = menfez_olcu(S_U)
    MF = PL.get('menfez', {})
    m_alt = MF.get('alt', {'duvar': 'alt', 'konum': (minx + maxx) / 2})
    m_ust = MF.get('ust', {'duvar': 'ust', 'konum': maxx - 60})
    z_alt0 = float(m_alt.get('alt_kot', 15))
    z_ust1 = H - float(m_ust.get('tavandan', 10))
    z_ust0 = z_ust1 - hu

    acik = []
    kapi_geo = []
    for k in kapilar:
        p, u, nn = kenar_bul(oda, k['duvar'], k['konum'])
        w = float(k.get('genislik', 100))
        acik.append(bosluk(p, u, nn, w, t))
        kapi_geo.append((p, u, nn, w, k))
    menfez_geo = []
    for m, (b, hh_, ad) in ((m_alt, (ba, ha, 'ALT')), (m_ust, (bu, hu, 'ÜST'))):
        p, u, nn = kenar_bul(oda, m['duvar'], m['konum'])
        acik.append(bosluk(p, u, nn, b, t))
        menfez_geo.append((p, u, nn, b, hh_, ad, m))
    # gaz girişi kılıflı duvar geçişi (sol duvar)
    gp, gu, gn = kenar_bul(oda, 'sol', y_gz)
    acik.append(bosluk(gp, gu, gn, 8, t))
    dis = oda.buffer(t, join_style=2)
    duvar = dis.difference(oda)
    for a in acik:
        duvar = duvar.difference(a)
    S.duvar(duvar)
    # kapı kanatları (dışa açılır)
    for p, u, nn, w, k in kapi_geo:
        pa = (p[0] - u[0] * w / 2 + nn[0] * t, p[1] - u[1] * w / 2 + nn[1] * t)
        pe = (pa[0] + nn[0] * w, pa[1] + nn[1] * w)
        msp.add_line(pa, pe, dxfattribs={'layer': KAPI})
        a1, a2 = math.degrees(math.atan2(nn[1], nn[0])), math.degrees(math.atan2(u[1], u[0]))
        cr = nn[0] * u[1] - nn[1] * u[0]
        msp.add_arc(pa, w, a1 if cr > 0 else a2, a2 if cr > 0 else a1, dxfattribs={'layer': KAPI})
        q = (p[0] + nn[0] * (t + w + 22), p[1] + nn[1] * (t + w + 22))
        S.yazi(q, f'ÇELİK KAPI {tr(w, 0)}/210 - EI2 90-C' + (' (2. ÇIKIŞ)' if k.get('otomatik') else ''), 8, KAPI)
        S.yazi((q[0], q[1] - 12), 'DIŞA AÇILIR, KENDİLİĞİNDEN KAPANIR', 7, KAPI)
    # menfezler (planda duvar açıklığında ızgara kanatları)
    for p, u, nn, b, hh_, ad, m in menfez_geo:
        for k in (0.25, 0.5, 0.75):
            q0 = (p[0] + nn[0] * t * k - u[0] * (b / 2 - 2), p[1] + nn[1] * t * k - u[1] * (b / 2 - 2))
            q1 = (p[0] + nn[0] * t * k + u[0] * (b / 2 - 2), p[1] + nn[1] * t * k + u[1] * (b / 2 - 2))
            msp.add_line(q0, q1, dxfattribs={'layer': MENF})
        S_ = S_A if ad == 'ALT' else S_U
        kt = (f'+{tr(z_alt0 / 100, 2)} / +{tr((z_alt0 + ha) / 100, 2)}' if ad == 'ALT'
              else f'+{tr(z_ust0 / 100, 2)} / +{tr(z_ust1 / 100, 2)}')
        q = (p[0] + nn[0] * (t + 22), p[1] + nn[1] * (t + 22))
        dik = abs(nn[0]) > 0.5
        al = (TA.MIDDLE_LEFT if nn[0] > 0 else TA.MIDDLE_RIGHT) if dik else TA.MIDDLE_CENTER
        if ad == 'ÜST' and not dik:
            q = (q[0], q[1] + 12)
        S.yazi(q, f'{ad} MENFEZ {b:.0f}×{hh_:.0f} (≥{tr(S_, 0)} cm²)', 8, MENF, al)
        S.yazi((q[0], q[1] - 12), f'IZGARALI, KOT {kt}', 7, MENF, al)

    # ---------------------------------------------------------------- kazanlar (plan)
    for i, x0 in enumerate(xs):
        c = S.blok('ROTAS-KAZAN-PLAN', (x0, Y_F), 0, 1, 'K', None, (), None, CIHAZ, tercih=[(0, -1)],
                   merkez=(x0 + g / 2, Y_F + d / 2), kutu=False)
        S.etiket(c, M['K'][i])
        c['sabit'] = (x0 + g / 2, Y_F + d * 0.82)
        S.yazi((x0 + g / 2, Y_F + 16), f'{tr(qk, 0)} kW', 7, YAZ, ic=True)
        # bağlantılar (kazan ön yüzünden başlıklara)
        S.hat(YOG, [(x0 + oy, Y_F), (x0 + oy, y_yg)], None, etiket='')
        S.hat(GAZ, [(x0 + ogz, y_gz), (x0 + ogz, Y_F)], dng_k, etiket='')
        S.hat(DON, [(x0 + odn, y_d), (x0 + odn, Y_F)], dn_k, etiket='')
        gd = S.hat(GID, [(x0 + ogd, Y_F), (x0 + ogd, y_g)], dn_k, etiket='')
        if M['PK']:
            S.etiket(S.ekle(gd, (x0 + ogd, Y_F - 60), 'ROTAS-POMPA', 'X', katman=POMPA), M['PK'][i])
        S.etiket(S.ekle(gd, (x0 + ogd, Y_F - 86), vblok(dn_k), 'X', cap=dn_k), M['V_KAZAN_GID'][i])
    # baca kollektörü (tavanda): kazan dış çizgileri ve baca çıkışlarında kesik
    x_bas, x_son = bx + r_bo, xL + g / 2 - rf
    bos = [(x0 - 3, x0 + 3) for x0 in xs] + [(x0 + g - 3, x0 + g + 3) for x0 in xs] + \
          [(x0 + g / 2 - rf, x0 + g / 2 + rf) for x0 in xs[:-1]]
    bos.sort()
    cur = x_bas
    for a0, a1 in bos + [(x_son, x_son)]:
        if a0 > cur + 1:
            S.hat(BACA, [(cur, by), (min(a0, x_son), by)], None, w=3.0, etiket='', kopru=False)
        cur = max(cur, a1)
        if cur >= x_son:
            break
    msp.add_circle((bx, by), r_bi, dxfattribs={'layer': BACA})
    msp.add_circle((bx, by), r_bo, dxfattribs={'layer': BACA})
    S.nesne(M['B'][0], (bx, by), tercih=[(0, -1)])
    S.yazi((xL + g + 70, by + 8), f'BACA KOLLEKTÖRÜ {bc.get("cap", "Ø300")} (TAVANDA)', 7, YAZ, TA.MIDDLE_LEFT)

    # ---------------------------------------------------------------- başlıklar (primer)
    G = S.hat(GID, [(xs[0] + ogd, y_g), (x_dk - 45, y_g), (x_dk - 45, yc - 6),
                    (x_dk - math.sqrt(r_dk ** 2 - 36), yc - 6)], dn_p, etiket=f'{dn_p} KAZAN GİDİŞ')
    S.etiket(S.ekle(G, (x_dk - 140, y_g), vblok(dn_p), 'X', cap=dn_p), M['V_PG1'])
    S.etiket(S.ekle(G, (x_dk - 110, y_g), B_DK, 'X', olcek=0.4, katman=CIHAZ), M['HA'][0])
    S.etiket(S.ekle(G, (x_dk - 75, y_g), vblok(dn_p), 'X', cap=dn_p), M['V_PG2'])
    D = S.hat(DON, [(x_dk - math.sqrt(r_dk ** 2 - 36), yc + 6), (x_dk - 30, yc + 6), (x_dk - 30, y_d),
                    (x_gt, y_d)], dn_p, etiket=f'{dn_p} KAZAN DÖNÜŞ')
    S.etiket(S.ekle(D, (x_dk - 60, y_d), vblok(dn_p), 'X', cap=dn_p), M['V_PD1'])
    S.etiket(S.ekle(D, (x_dk - 95, y_d), B_DK, 'X', olcek=0.4, katman=CIHAZ), M['TA'][0])
    S.etiket(S.ekle(D, (x_dk - 130, y_d), vblok(dn_p), 'X', cap=dn_p), M['V_PD2'])
    c = S.blok(B_DK, (x_dk, yc), 0, r_dk / 20.0, 'X', None, (), None, CIHAZ, tercih=[(0, 1), (1, 0)],
               merkez=(x_dk, yc), kutu=True)
    S.etiket(c, M['DK'][0])
    # gaz başlığı + giriş
    xg_d = minx - t - 160
    g1 = S.hat(GAZ, [(xg_d, y_gz), (xL + ogz, y_gz)], dng, etiket=f'{dng} GAZ')
    S.etiket(S.ekle(g1, (minx - t - 130, y_gz), 'MTY-KURESEL VANA', 'X', cap=dng_g, katman=GAZS), M['VGA'][0])
    if M['SV']:
        S.etiket(S.ekle(g1, (minx - t - 80, y_gz), 'ROTAS-SELENOID', 'X', katman=GAZS), M['SV'][0])
    S.yazi((minx - t - 105, y_gz + 48), 'KAZAN DAİRESİ DIŞI', 8, YAZ)
    S.yazi((xg_d - 6, y_gz), 'DOĞALGAZ GİRİŞİ', 8, YAZ, TA.MIDDLE_RIGHT)
    S.yazi((xg_d - 6, y_gz - 13), '(SAYAÇ DIŞARIDA)', 7, YAZ, TA.MIDDLE_RIGHT)
    xi = minx + 30
    if M['GF']:
        S.etiket(S.ekle(g1, (xi, y_gz), 'MTY-PISLIK TUTUCU', 'X', cap=dng_g, katman=GAZS), M['GF'][0])
    if reg and M['GR']:
        S.etiket(S.ekle(g1, (xi + 38, y_gz), 'ROTAS-REGULATOR', 'X', katman=GAZS), M['GR'][0])
    if M['MG']:
        S.etiket(S.brans((xi + 80, y_gz), 'MTY-MANOMETRE', 90, 'X', cap='M'), M['MG'][0])
    if M['VGK']:
        S.etiket(S.ekle(g1, (xi + 112, y_gz), 'MTY-KURESEL VANA', 'X', cap=dng, katman=GAZS), M['VGK'][0])
    if M['GA']:
        S.etiket(S.blok('ROTAS-GAZ-ALARM', (minx + 25, Y_F - 90), 0, 1, 'X', None, (), None, GAZS,
                        tercih=[(0, -1), (1, 0)]), M['GA'][0])
    # yoğuşma
    y_ys = y_yg - (210 if notr else 110)
    if notr:
        y_n0 = y_yg - 45
        S.hat(YOG, [(xL + oy, y_yg), (x_yog, y_yg), (x_yog, y_n0)], None, etiket='DN25 YOĞUŞMA')
        c = S.blok('ROTAS-NOTRALIZASYON', (x_yog, y_n0), 270, 1, 'X', None, (), None, CIHAZ, tercih=[(1, 0)],
                   merkez=(x_yog, y_n0 - 60), kutu=True)
        S.etiket(c, M['NU'][0])
        S.hat(YOG, [(x_yog, y_n0 - 120), (x_yog, y_ys + 5)], None, etiket='')
    else:
        S.hat(YOG, [(xL + oy, y_yg), (x_yog, y_yg), (x_yog, y_ys + 5)], None, etiket='DN25 YOĞUŞMA')
    S.blok(B_YS, (x_yog, y_ys), 0, 1, None, None, (), None, PIS)
    S.yazi((x_yog, y_ys - 14), 'YER SÜZGECİ Ø100', 7, YAZ)
    # genleşme tankı (dönüş başlığına, kilitlenebilir vana ile)
    y_gtc = y_d - 48 - 50.9 * s_gt
    gtp = S.hat(DON, [(x_gt, y_d), (x_gt, y_gtc + 50.9 * s_gt)], 'DN25', etiket='')
    S.etiket(S.ekle(gtp, (x_gt, y_d - 22), 'MTY-KITLENEBILIR VANA', 'X', cap='DN25'), M['KIL'][0])
    c = S.blok(B_GT, (x_gt, y_gtc), 180, s_gt, 'X', None, (), None, CIHAZ, tercih=[(0, -1), (1, 0)],
               merkez=(x_gt, y_gtc), kutu=True)
    S.etiket(c, M['GT'][0])
    S.yazi((x_gt + r_gt * 0.42, y_gtc - r_gt * 0.28), f'{tr(gt["hacim_l"], 0)} L', 7 * min(1.0, r_gt / 40), YAZ, ic=True)

    # ---------------------------------------------------------------- sekonder
    xr = x_dk + math.sqrt(r_dk ** 2 - 36)
    sg = S.hat(GID, [(xr, yc - 6), (x_dk + 40, yc - 6), (x_dk + 40, y_kg), (x_k0 - KOLLEKTOR_YARI, y_kg)], dn_s,
               etiket='')
    S.etiket(S.ekle(sg, (x_dk + 75, y_kg), vblok(dn_s), 'X', cap=dn_s), M['V_SG'])
    sd = S.hat(DON, [(x_k0 - KOLLEKTOR_YARI, y_kd), (xr, yc + 6)], dn_s, etiket='')
    S.etiket(S.ekle(sd, (x_dk + 62, y_kd), vblok(dn_s), 'X', cap=dn_s), M['V_SD'])
    s0 = y_kg - KOLLEKTOR_YARI
    k = 0
    for z in zonlar:
        for j in range(int(z.get('adet', 1))):
            ad = z['ad'] + (f'.{j + 1}' if z.get('adet', 1) > 1 else '')
            dn = dn_su(z['debi'])
            Z = M['ZON'][k]
            xz = zx[k]
            if z.get('yedek'):
                tr_ = S.hat(GID, [(xz, s0), (xz, s0 - 75)], dn, etiket='')
                S.etiket(S.ekle(tr_, (xz, s0 - 22), vblok(dn), 'X', cap=dn), Z['V'][0])
                S.etiket(S.ekle(tr_, (xz, s0 - 50), 'MTY-PISLIK TUTUCU', 'X', cap=dn), Z['PT'])
                for side, xl in ((0, xz - 35), (1, xz + 35)):
                    leg = S.hat(GID, [(xz, s0 - 75), (xl, s0 - 75), (xl, s0 - 225), (xz, s0 - 225)], dn, etiket='')
                    S.etiket(S.ekle(leg, (xl, s0 - 97), vblok(dn), 'X', cap=dn), Z['V'][1 + 2 * side])
                    S.etiket(S.ekle(leg, (xl, s0 - 130), 'ROTAS-POMPA', 'X', katman=POMPA), Z['P'][side])
                    S.etiket(S.ekle(leg, (xl, s0 - 165), 'MTY-CEKVALF VANA', 'X', cap=dn), Z['CV'][side])
                    S.etiket(S.ekle(leg, (xl, s0 - 200), vblok(dn), 'X', cap=dn), Z['V'][2 + 2 * side])
                S.hat(GID, [(xz, s0 - 225), (xz, s0 - 275)], dn, ok='son', etiket='')
                y_alt = s0 - 275
            else:
                tr_ = S.hat(GID, [(xz, s0), (xz, s0 - 200)], dn, ok='son', etiket='')
                S.etiket(S.ekle(tr_, (xz, s0 - 22), vblok(dn), 'X', cap=dn), Z['V'][0])
                S.etiket(S.ekle(tr_, (xz, s0 - 50), 'MTY-PISLIK TUTUCU', 'X', cap=dn), Z['PT'])
                S.etiket(S.ekle(tr_, (xz, s0 - 85), 'ROTAS-POMPA', 'X', katman=POMPA), Z['P'][0])
                S.etiket(S.ekle(tr_, (xz, s0 - 118), 'MTY-CEKVALF VANA', 'X', cap=dn), Z['CV'][0])
                S.etiket(S.ekle(tr_, (xz, s0 - 150), vblok(dn), 'X', cap=dn), Z['V'][1])
                y_alt = s0 - 200
            S.yazi((xz, y_alt - 14), f'{ad} GİDİŞ {dn}', 8, YAZ)
            S.yazi((xz, y_alt - 27), '(TAVANDAN ZONA)', 7, YAZ)
            dz = S.hat(DON, [(xz, Y_W - 22), (xz, y_kd + KOLLEKTOR_YARI)], dn, ok='son', etiket='')
            S.etiket(S.ekle(dz, (xz, (Y_W - 22 + y_kd + KOLLEKTOR_YARI) / 2 + 8), vblok(dn), 'X', cap=dn), Z['VD'])
            S.yazi((xz + 8, Y_W - 26), f'{ad} DÖNÜŞ (TAVANDAN)', 7, YAZ, TA.MIDDLE_LEFT)
            k += 1
    if boy:
        sp = boy['sarj_pompa']
        dnb = dn_su(sp['debi'])
        s_by = (boyler_cap(boy['hacim_l']) / 2) / 53.0
        y_bc = s0 - 150
        bg = S.hat(GID, [(x_bg, s0), (x_bg, y_bc)], dnb, etiket='')
        S.etiket(S.ekle(bg, (x_bg, s0 - 22), vblok(dnb), 'X', cap=dnb), M['BOY']['V'][0])
        S.etiket(S.ekle(bg, (x_bg, s0 - 55), 'ROTAS-POMPA', 'X', katman=POMPA), M['PB'][0])
        S.etiket(S.ekle(bg, (x_bg, s0 - 88), 'MTY-CEKVALF VANA', 'X', cap=dnb), M['BOY']['CV'])
        S.etiket(S.ekle(bg, (x_bg, s0 - 120), vblok(dnb), 'X', cap=dnb), M['BOY']['V'][1])
        ycb = y_bc - 58.13 * s_by
        c = S.blok(B_BY, (x_bg, y_bc), 90, s_by, 'X', None, (), None, CIHAZ, tercih=[(-1, 0), (0, -1)],
                   merkez=(x_bg, ycb), kutu=True)
        S.etiket(c, M['BY'][0])
        c['sabit'] = (x_bg, ycb - 53 * s_by - 14)
        bd = S.hat(DON, [(x_bg + 53 * s_by, ycb), (x_bd, ycb), (x_bd, y_kd - KOLLEKTOR_YARI)], dnb, etiket='')
        S.etiket(S.ekle(bd, (x_bd, (ycb + y_kd) / 2), vblok(dnb), 'X', cap=dnb), M['BOY']['VD'])
        S.yazi((x_bg, ycb - 53 * s_by - 30), f'{tr(boy["hacim_l"], 0)} L - KULLANIM SUYU', 7, YAZ)
        S.yazi((x_bg, ycb - 53 * s_by - 42), 'BAĞLANTILARI ŞEMAYA GÖRE', 7, YAZ)
    S.kollektor(x_k0, x_kg1, y_kg)
    S.kollektor(x_k0, x_kd1, y_kd)
    S.nesne(M['KL'][0], (x_k0 + 20, y_kg), tercih=[(0, 1)], buyuk=False)
    S.nesne(M['KL'][1], (x_k0 + 20, y_kd), tercih=[(0, 1)], buyuk=False)

    # ---------------------------------------------------------------- bakım alanı + ölçüler + kesit işaretleri
    yb0 = y_g - 15
    yb1 = yb0 - 100
    msp.add_lwpolyline([(xs[0], yb0), (xL + g, yb0), (xL + g, yb1), (xs[0], yb1)], close=True,
                       dxfattribs={'layer': BAKIM})
    S.yazi(((xs[0] + xL + g) / 2, (yb0 + yb1) / 2 + 8), 'BAKIM / SERVİS ALANI', 8, BAKIM)
    S.yazi(((xs[0] + xL + g) / 2, (yb0 + yb1) / 2 - 6), '(≥ 1,00 m BOŞ BIRAKILACAK)', 7, BAKIM)
    xo_ = (xs[0] + xL + g) / 2
    S.yazi((xo_, yb1 - 85), 'KAZAN DAİRESİ', 16, BAS)
    S.yazi((xo_, yb1 - 107), f'A = {tr(alan, 2)} m²  -  h = {tr(H / 100, 2)} m', 9, YAZ)
    S.kot((xo_ - 60, yb1 - 140), '±0,00 (BİTMİŞ DÖŞEME)')
    on_mesafe = Y_F - miny
    if on_mesafe < d + 100:
        uy.append(f'kazan önü serbest mesafe {tr(on_mesafe, 0)} < kazan boyu + 100 = {tr(d + 100, 0)} cm')
    # üst: kazan aralık zinciri
    zin = [(minx, Y_W + t)] + [(x, Y_W + t) for x0 in xs for x in (x0, x0 + g)] + [(maxx, Y_W + t)]
    S.olcu(zin[0], zin[-1], (0, 1), 70, zincir=zin[1:-1])
    S.olcu((minx - t, Y_W + t), (maxx + t, Y_W + t), (0, 1), 105)
    S.olcu((maxx + t, miny - t), (maxx + t, maxy + t), (1, 0), 45)
    # kesit A-A işaretleri (kazan 1 ekseninden)
    x_c = xs[0] + g / 2
    for y0, y1, yy in ((Y_W + t + 8, Y_W + t + 30, Y_W + t + 30), (miny - t - 8, miny - t - 30, miny - t - 30)):
        msp.add_lwpolyline([(x_c, y0), (x_c, y1)], dxfattribs={'layer': KESH, 'const_width': 2.0})
        msp.add_blockref('ROTAS-OK', (x_c - 18, yy), dxfattribs={'layer': KESH, 'rotation': 180})
        msp.add_line((x_c - 4, yy), (x_c, yy), dxfattribs={'layer': KESH})
        S.yazi((x_c - 20, yy + (13 if yy > Y_W else -13)), 'A', 14, KESH)
    # görünüş B oku (kazan duvarına bakar)
    xb_ = (xs[0] + xL + g) / 2
    msp.add_blockref('ROTAS-OK', (xb_, yb1 - 12), dxfattribs={'layer': KESH, 'rotation': 90})
    msp.add_line((xb_, yb1 - 26), (xb_, yb1 - 50), dxfattribs={'layer': KESH})
    S.yazi((xb_ + 10, yb1 - 44), 'B', 14, KESH, TA.MIDDLE_LEFT)

    # bina dışı/içi yerleşim denetimi
    for x0 in xs:
        if not oda.contains(sbox(x0, Y_F, x0 + g, Y_W - 0.01)):
            uy.append(f'kazan oda dışına taşıyor: x={x0}')
    for nm, (cx, cy, r) in (('genleşme tankı', (x_gt, y_gtc, r_gt)), ('denge kabı', (x_dk, yc, r_dk))):
        if not oda.contains(sbox(cx - r, cy - r, cx + r, cy + r)):
            uy.append(f'{nm} oda dışına taşıyor')

    plan_bb = (minx - t - 330, miny - t - 170, maxx + t + 120, maxy + t + 140)
    S.yazi(((plan_bb[0] + plan_bb[2]) / 2, plan_bb[1] + 10),
           'KAZAN DAİRESİ PLANI ......................... ÖLÇEK: 1 / 50', 20, BAS, maske=False)
    if PL.get('temsili'):
        S.yazi((plan_bb[0] + 10, plan_bb[3] - 10), 'DENEME – temsili oda', 26, BAS, TA.TOP_LEFT, maske=False)

    # ================================================================ KESİT A-A
    ln = LineString([(x_c, miny - 10), (x_c, maxy + 10)]).intersection(oda)
    y_lo = ln.bounds[1]
    Dc = Y_W - y_lo
    SX = plan_bb[2] + 260 + t
    SZ = Y_W - H - 40

    def K_(s, z):
        return (SX + s, SZ + z)
    # yapı: duvarlar, döşeme, tavan; menfez açıklıkları
    yapi = sbox(SX - t, SZ - ds, SX + Dc + t, SZ + H + ds).difference(sbox(SX, SZ, SX + Dc, SZ + H))
    for m, (b, hh_, ad) in ((m_ust, (bu, hu, 'ÜST')), (m_alt, (ba, ha, 'ALT'))):
        z0 = z_ust0 if ad == 'ÜST' else z_alt0
        sol = m['duvar'] == 'ust'
        sx0 = SX - t - 1 if sol else SX + Dc - 1
        yapi = yapi.difference(sbox(sx0, SZ + z0, sx0 + t + 2, SZ + z0 + hh_))
        for kk in range(1, 4):
            zz = SZ + z0 + hh_ * kk / 4
            msp.add_line((sx0 + 1 + t * 0.2, zz), (sx0 + 1 + t * 0.8, zz), dxfattribs={'layer': MENF})
        sx_t = SX - t - 12 if sol else SX + Dc + t + 12
        al = TA.MIDDLE_RIGHT if sol else TA.MIDDLE_LEFT
        z1 = z0 + hh_
        S.yazi((sx_t, SZ + z0 + hh_ / 2 + 7), f'{ad} MENFEZ {b:.0f}×{hh_:.0f}', 8, MENF, al)
        S.yazi((sx_t, SZ + z0 + hh_ / 2 - 6), f'+{tr(z0 / 100, 2)} / +{tr(z1 / 100, 2)}', 8, MENF, al)
    # baca geçişi (tavan döşemesinde boşluk yok: baca kesit düzleminde değil)
    S.duvar(yapi)
    msp.add_blockref('ROTAS-KAZAN-YAN', K_(2, zb), dxfattribs={'layer': CIHAZ})
    S.nesne(M['K'][0], K_(2 + d / 2, zb + h / 2), sabit=K_(2 + d / 2, zb + h * 0.55))
    # bağlantılar (s: duvardan uzaklık)
    so = {'yog': 10 * d / 55, 'gaz': 20 * d / 55, 'don': 30 * d / 55, 'gid': 42 * d / 55}
    zh = {'gid': 50.0, 'don': 35.0, 'gaz': 20.0, 'yog': 8.0}
    sh = {'gaz': d + 12, 'yog': d + 24, 'don': d + 40, 'gid': d + 100}
    rh = {'gid': 5.0, 'don': 5.0, 'gaz': 3.0, 'yog': 2.0}
    lay = {'gid': GID, 'don': DON, 'gaz': GAZ, 'yog': YOG}
    for k_ in ('yog', 'gaz', 'don', 'gid'):
        S.hat(lay[k_], [K_(so[k_], zb), K_(so[k_], zh[k_]), K_(sh[k_] - rh[k_], zh[k_])], None, etiket='')
        msp.add_circle(K_(sh[k_], zh[k_]), rh[k_], dxfattribs={'layer': lay[k_]})
    ad_h = {'gid': f'KAZAN GİDİŞ KOLL. {dn_p}', 'don': f'KAZAN DÖNÜŞ KOLL. {dn_p}', 'gaz': f'DOĞALGAZ KOLL. {dng}',
            'yog': 'YOĞUŞMA KOLL. DN25 PP'}
    for k_ in ('gid', 'don', 'gaz', 'yog'):
        x1 = sh['gid'] + 25
        msp.add_line(K_(sh[k_] + rh[k_], zh[k_]), K_(x1, zh[k_]), dxfattribs={'layer': OLC})
        S.yazi(K_(x1 + 4, zh[k_]), f'{ad_h[k_]}  +{tr(zh[k_] / 100, 2)}', 7, YAZ, TA.MIDDLE_LEFT)
    # baca kollektörü kesiti + bağlantı
    rfc = r_bi
    z_fc = zb + h + 11 + r_bo
    if z_fc + rfc + 3 > H - 5:
        uy.append(f'baca kollektörü tavana sığmıyor: üst {tr(z_fc + rfc + 3, 0)} > {tr(H - 5, 0)}')
    msp.add_circle(K_(d / 2, z_fc), r_bi, dxfattribs={'layer': BACA})
    msp.add_circle(K_(d / 2, z_fc), r_bo, dxfattribs={'layer': BACA})
    S.yazi(K_(d / 2 + r_bo + 8, z_fc + 6), f'BACA KOLLEKTÖRÜ {bc.get("cap", "Ø300")}', 7, BACA, TA.MIDDLE_LEFT)
    S.yazi(K_(d / 2 + r_bo + 8, z_fc - 7), f'eksen +{tr(z_fc / 100, 2)}, %3 eğimli', 7, BACA, TA.MIDDLE_LEFT)
    # kotlar (sağda) + ölçüler (solda)
    kx = SX + Dc + t + 150
    for z, s in ((0, '±0,00 BİTMİŞ DÖŞEME'), (zb, f'+{tr(zb / 100, 2)} KAZAN ALTI'),
                 (zb + h, f'+{tr((zb + h) / 100, 2)} KAZAN ÜSTÜ'), (H, f'+{tr(H / 100, 2)} TAVAN')):
        S.kot((kx, SZ + z), s)
    S.olcu(K_(-t, 0), K_(-t, H), (-1, 0), 150, zincir=[K_(-t, zb), K_(-t, zb + h)])
    S.olcu(K_(0, -ds), K_(Dc, -ds), (0, -1), 25, zincir=[K_(d, -ds)])
    S.yazi(K_(d + (Dc - d) / 2, -ds - 62), f'KAZAN ÖNÜ SERBEST MESAFE {tr((Dc - d) / 100, 2)} m ≥ '
           f'{tr((d + 100) / 100, 2)} m (KAZAN BOYU + 1,00 m)', 8, YAZ)
    S.yazi(K_(Dc / 2, H - 25), 'TAVAN DÖŞEMESİ VE DUVARLAR EI 120', 8, YAZ)
    kes_bb = (SX - t - 260, SZ - ds - 120, SX + Dc + t + 330, SZ + H + ds + 60)
    S.yazi(((kes_bb[0] + kes_bb[2]) / 2, kes_bb[1] + 10), 'KESİT A-A ......................... ÖLÇEK: 1 / 50',
           20, BAS, maske=False)

    # ================================================================ GÖRÜNÜŞ B (kazan duvarı)
    GX = 0.0
    GZ = plan_bb[1] - 160 - H - ds
    x_e = x_dk - 20

    def G_(x, z):
        return (GX + x, GZ + z)
    yapi = sbox(*G_(minx - t, -ds), *G_(x_e, H + ds)).difference(sbox(*G_(minx, 0), *G_(x_e + 1, H)))
    yapi = yapi.difference(sbox(*G_(minx - t - 1, 20 - 4), *G_(minx + 1, 20 + 4)))                  # gaz geçişi
    yapi = yapi.difference(sbox(*G_(bx - r_bo - 3, H - 1), *G_(bx + r_bo + 3, H + ds + 1)))        # baca geçişi
    S.duvar(yapi)
    msp.add_line(G_(x_e + 8, -ds - 15), G_(x_e + 8, H + ds + 15), dxfattribs={'layer': KESH})
    S.yazi(G_(x_e + 14, H + ds + 8), 'KISMİ GÖRÜNÜŞ', 7, YAZ, TA.MIDDLE_LEFT)
    # üst menfez bu duvarda ve görünüş aralığında ise
    if m_ust['duvar'] == 'ust' and minx < m_ust['konum'] < x_e:
        msp.add_blockref('ROTAS-MENFEZ-ON', G_(m_ust['konum'] - bu / 2, z_ust0),
                         dxfattribs={'layer': MENF, 'xscale': bu, 'yscale': hu})
    z_g = {'gid': 50.0, 'don': 35.0, 'gaz': 20.0, 'yog': 8.0}
    for i, x0 in enumerate(xs):
        msp.add_blockref('ROTAS-KAZAN-ON', G_(x0, zb), dxfattribs={'layer': CIHAZ})
        S.nesne(M['K'][i], G_(x0 + g / 2, zb + h / 2), sabit=G_(x0 + g / 2, zb + h * 0.38))
        S.yazi(G_(x0 + g / 2, zb + h * 0.78), f'{tr(qk, 0)} kW', 7, YAZ, ic=True)
        # gidiş: EV + HP (üst), TM + M, pompa, çek valf, vana
        gd = S.hat(GID, [G_(x0 + ogd, zb), G_(x0 + ogd, z_g['gid'])], dn_k, etiket='')
        S.etiket(S.brans(G_(x0 + ogd, zb - 10), 'MTY-EMNİYET VENTİLİ', 0, 'X', cap='DN25'), M['EVK'][i])
        S.etiket(S.brans(G_(x0 + ogd, zb - 42), 'MTY-O.H.A.C', 0, 'X', cap='DN15', olcek=0.4), M['HP'][i])
        S.etiket(S.brans(G_(x0 + ogd, zb - 12), 'MTY-TERMOMETRE', 180, 'X', cap='T'), M['TM'][i])
        S.etiket(S.brans(G_(x0 + ogd, zb - 30), 'MTY-MANOMETRE', 180, 'X', cap='M'), M['MN'][i])
        if M['PK']:
            S.etiket(S.ekle(gd, G_(x0 + ogd, zb - 70), 'ROTAS-POMPA', 'X', katman=POMPA), M['PK'][i])
            S.etiket(S.ekle(gd, G_(x0 + ogd, zb - 96), 'MTY-CEKVALF VANA', 'X', cap=dn_k), M['CV'][i])
        S.etiket(S.ekle(gd, G_(x0 + ogd, zb - 120), vblok(dn_k), 'X', cap=dn_k), M['V_KAZAN_GID'][i])
        dd = S.hat(DON, [G_(x0 + odn, z_g['don']), G_(x0 + odn, zb)], dn_k, etiket='')
        S.etiket(S.ekle(dd, G_(x0 + odn, zb - 60), vblok(dn_k), 'X', cap=dn_k), M['V_KAZAN_DON'][i])
        gg = S.hat(GAZ, [G_(x0 + ogz, z_g['gaz']), G_(x0 + ogz, zb)], dng_k, etiket='')
        S.etiket(S.ekle(gg, G_(x0 + ogz, zb - 30), 'MTY-KURESEL VANA', 'X', cap=dng_k, katman=GAZS), M['VGC'][i])
        S.etiket(S.ekle(gg, G_(x0 + ogz, zb - 92), 'MTY-ESNEK BAGLANTI', 'X', cap=dng_k, katman=GAZS), M['ESN'][i])
        S.hat(YOG, [G_(x0 + oy, zb), G_(x0 + oy, z_g['yog'])], None, etiket='')
    # başlıklar
    S.hat(GID, [G_(xs[0] + ogd, z_g['gid']), G_(x_e - 25, z_g['gid'])], dn_p, ok='son', etiket=f'{dn_p} GİDİŞ')
    S.hat(DON, [G_(x_e - 25, z_g['don']), G_(x_gt, z_g['don'])], dn_p, etiket=f'{dn_p} DÖNÜŞ')
    S.yazi(G_(x_e - 22, z_g['gid'] + 12), f'{M["DK"][0]}', 7, YAZ, TA.MIDDLE_RIGHT)
    S.yazi(G_(x_gt - 6, z_g['don'] + 10), f'{M["GT"][0]}', 7, YAZ, TA.MIDDLE_RIGHT)
    S.hat(GAZ, [G_(minx - t - 110, z_g['gaz']), G_(xL + ogz, z_g['gaz'])], dng, etiket=f'{dng} GAZ')
    S.hat(YOG, [G_(xL + oy, z_g['yog']), G_(x_yog, z_g['yog'])], None, ok='son', etiket='')
    # baca kollektörü (çift çizgi) + baca
    S.hat(BACA, [G_(bx + r_bo, z_fc + r_bo), G_(xL + g / 2 + rf + 6, z_fc + r_bo), G_(xL + g / 2 + rf + 6, z_fc - r_bo),
                 G_(xL + g / 2 + rf, z_fc - r_bo)], None, etiket='', kopru=False)
    cur = bx + r_bo
    for x0 in xs:
        S.hat(BACA, [G_(cur, z_fc - r_bo), G_(x0 + g / 2 - rf, z_fc - r_bo)], None, etiket='', kopru=False)
        cur = x0 + g / 2 + rf
    z_b0 = 60.0
    zt = H + ds + 45
    for sx in (-1, 1):
        if sx < 0:
            S.hat(BACA, [G_(bx - r_bo, z_b0), G_(bx - r_bo, zt)], None, etiket='', kopru=False)
        else:
            S.hat(BACA, [G_(bx + r_bo, z_b0), G_(bx + r_bo, z_fc - r_bo)], None, etiket='', kopru=False)
            S.hat(BACA, [G_(bx + r_bo, z_fc + r_bo), G_(bx + r_bo, zt)], None, etiket='', kopru=False)
    msp.add_line(G_(bx - r_bo, z_b0), G_(bx + r_bo, z_b0), dxfattribs={'layer': BACA})
    msp.add_blockref('ROTAS-OK', G_(bx, zt + 18), dxfattribs={'layer': BACA, 'rotation': 90})
    S.yazi(G_(bx + r_bo + 8, zt + 6), f'ÇATIYA (MAHYAYI AŞACAK) - BACA {bc.get("cap", "Ø300")}', 7, BACA, TA.MIDDLE_LEFT)
    S.yazi(G_(bx + r_bo + 6, z_b0 + 18), 'TEMİZLEME KAPAĞI +', 7, BACA, TA.MIDDLE_LEFT)
    S.yazi(G_(bx + r_bo + 6, z_b0 + 7), 'YOĞUŞMA DRENAJI', 7, BACA, TA.MIDDLE_LEFT)
    if M['GA']:
        S.etiket(S.blok('ROTAS-GAZ-ALARM', G_(x_start - 38, H - 2), 180, 1, 'X', None, (), None, GAZS,
                        tercih=[(0, -1)]), M['GA'][0])
    # kotlar
    kx = GX + x_e + 130
    for z, s in ((0, '±0,00'), (zb, f'+{tr(zb / 100, 2)} KAZAN ALTI'), (zb + h, f'+{tr((zb + h) / 100, 2)} KAZAN ÜSTÜ'),
                 (z_fc, f'+{tr(z_fc / 100, 2)} BACA KOLL. EKSENİ'), (H, f'+{tr(H / 100, 2)} TAVAN')):
        S.kot((kx, GZ + z), s)
    for k_, s in (('gid', 'GİDİŞ'), ('don', 'DÖNÜŞ'), ('gaz', 'GAZ'), ('yog', 'YOĞUŞMA')):
        S.yazi(G_(x_e + 22, z_g[k_]),
               f'{s} +{tr(z_g[k_] / 100, 2)}', 7, KOTL, TA.MIDDLE_LEFT)
    gor_bb = (minx - t - 190, GZ - ds - 110, x_e + 330, GZ + H + ds + 70)
    S.yazi(((gor_bb[0] + gor_bb[2]) / 2, gor_bb[1] + 10),
           'GÖRÜNÜŞ B (KAZAN DUVARI) ......................... ÖLÇEK: 1 / 50', 20, BAS, maske=False)

    # ================================================================ çizim, etiket, lejant, liste
    KD.HT, KD.HD = 9.0, 7.5
    S.kopruler()
    S.boru_ciz()
    S.cihazlar.sort(key=lambda c: 0 if c.get('sabit') else 1)     # sabit (kazan) numaraları önce yerleşir
    S.etiketle()
    KD.HT, KD.HD = 8.0, 7.0
    LX = max(kes_bb[2], gor_bb[2]) + 120
    LY = plan_bb[3]
    ly = lejant(S, LX, LY, reg, notr, boy, dn_p)
    hy = hesap_kutusu(S, LX, ly - 60, QT, alan, gerek_kapi, len(kapilar), formul, S_A, S_U, oran, ba, ha, bu, hu,
                      Y_F - miny, d, Fk, ak)
    ty = min(gor_bb[1], hy) - 120
    xe, ye = S.tablo(satir, minx - t - 190, ty, 'KAZAN DAİRESİ CİHAZ LİSTESİ (PRENSİP ŞEMASI İLE AYNI NUMARALAR)')
    notlar = [
        'Kazan dairesi duvarları, döşemesi ve tavanı en az 120 dakika (EI 120) yangın dayanımlı olacaktır.',
        f'{"İki" if len(kapilar) > 1 else "Bir"} adet çelik kapı EI2 90-C, dışa açılır ve kendiliğinden kapanır '
        f'(350 kW üstü veya alan > 100 m² ise en az 2 çıkış).',
        'Gaz sayacı, ana kesme vanası ve selenoid vana kazan dairesi dışında; acil stop butonu kapı dışında olacaktır.',
        'Ex-proof gaz alarm ve CO dedektörü üst menfezden yüksekte, tavana yakın monte edilecektir.',
        'Alt menfez döşemeden ≤ 45 cm, üst menfez tavandan ≤ 40 cm; menfezler birbirine kısa devre yapmayacaktır.',
        'Kazan önünde en az kazan boyu + 1,00 m serbest bakım alanı bırakılacaktır.',
        'Duvar ve döşeme boru geçişleri çelik kılıflı, yangın yalıtımlı (EI 120) yapılacaktır.',
        'Numaralar prensip şeması ve cihaz listesi ile aynıdır; tüm vana/cihazlar şemada gösterilmiştir.',
        'Genleşme tankı ve denge kabı görünüşte gösterilmemiştir (plana bakınız).',
    ]
    if PL.get('temsili'):
        notlar.insert(0, 'DENEME: oda ölçüleri temsilidir; mimari kazan dairesi ölçülerine göre uyarlanacaktır.')
    nx = xe + 80
    msp.add_text('NOTLAR', height=18, dxfattribs={'layer': BAS, 'style': 'ROTAS'}).set_placement(
        (nx, ty - 20), align=TA.BOTTOM_LEFT)
    for i, s in enumerate(notlar):
        msp.add_text(f'{i + 1}. {s}', height=11, dxfattribs={'layer': YAZ, 'style': 'ROTAS', 'width': KD.WF}
                     ).set_placement((nx, ty - 50 - i * 22), align=TA.BOTTOM_LEFT)
    from ezdxf import bbox as zb_
    bb = zb_.extents(msp, fast=True)
    x0f, y0f, x1f, y1f = bb.extmin.x - 60, bb.extmin.y - 60, bb.extmax.x + 60, bb.extmax.y + 60
    S.cerceve = msp.add_lwpolyline([(x0f, y0f), (x1f, y0f), (x1f, y1f), (x0f, y1f)], close=True,
                                   dxfattribs={'layer': KD.PAFTA, 'const_width': 3})
    S.kapsam = (x0f, y0f, x1f, y1f)
    S.satir, S.harita = satir, M
    if cikti:
        doc.saveas(cikti)
    return S


# ============================================================================ lejant + hesap kutusu
def lejant(S, x0, y0, reg, notr, boy, dn_p):
    m = S.msp
    sat = [('ROTAS-KAZAN-PLAN', 0.5, 'DUVAR TİPİ YOĞUŞMALI KAZAN (PLAN)'),
           ('ROTAS-POMPA', 1.0, 'SİRKÜLASYON POMPASI (OK AKIŞ YÖNÜ)'),
           ('MTY-KURESEL VANA', 1.0, 'KÜRESEL VANA (DN50 VE ALTI)')]
    if dn_no(dn_p) >= 65:
        sat.append(('MTY-KELEBEK VANA', 1.0, 'KELEBEK VANA (DN65 VE ÜZERİ)'))
    sat += [('MTY-CEKVALF VANA', 1.0, 'ÇEK VALF'), ('MTY-PISLIK TUTUCU', 1.0, 'PİSLİK TUTUCU / GAZ FİLTRESİ'),
            ('MTY-KITLENEBILIR VANA', 1.0, 'KİLİTLENEBİLİR (MÜHÜRLÜ) VANA'),
            ('MTY-EMNİYET VENTİLİ', 0.75, 'EMNİYET VENTİLİ'), ('MTY-MANOMETRE', 0.9, 'MANOMETRE'),
            ('MTY-TERMOMETRE', 0.9, 'TERMOMETRE'), ('MTY-O.H.A.C', 0.35, 'OTOMATİK HAVA PURJÖRÜ'),
            ('MTY-ESNEK BAGLANTI', 1.0, 'ESNEK BAĞLANTI (GAZ)'), ('ROTAS-SELENOID', 1.0, 'GAZ SELENOİD VANASI')]
    if reg:
        sat.append(('ROTAS-REGULATOR', 1.0, 'GAZ BASINÇ REGÜLATÖRÜ'))
    sat += [('ROTAS-GAZ-ALARM', 1.0, 'GAZ ALARM + CO DEDEKTÖRÜ (EX-PROOF)'),
            ('MTY-DENGE KABI PLAN', 0.6, 'DENGE KABI / HAVA AYIRICI / TORTU AYIRICI (PLAN)'),
            ('aGENLESME DEPOSU (PLAN-1)', 0.3, 'KAPALI GENLEŞME TANKI (PLAN)')]
    if boy:
        sat.append(('BOYLER KAT PLANI', 0.3, 'BOYLER (PLAN)'))
    if notr:
        sat.append(('ROTAS-NOTRALIZASYON', 0.35, 'NÖTRALİZASYON ÜNİTESİ'))
    sat += [('MTY-YER SUZGECI DN100', 2.0, 'YER SÜZGECİ Ø100'), ('ROTAS-KOT', 1.0, 'KOT İŞARETİ')]
    hat = [(GID, 'ISITMA GİDİŞ'), (DON, 'ISITMA DÖNÜŞ'), (GAZ, 'DOĞALGAZ'), (YOG, 'YOĞUŞMA SUYU'),
           (BACA, 'BACA / BACA KOLLEKTÖRÜ'), (KOL, 'KOLLEKTÖR'), (MENF, 'HAVALANDIRMA MENFEZİ (IZGARALI)'),
           (BAKIM, 'BAKIM / SERVİS ALANI'), (KESH, 'KESİT / GÖRÜNÜŞ HATTI'), (DUV, 'EI 120 DUVAR (TARAMALI)')]
    W0, W1, RH = 130, 520, 34
    nrow = len(sat) + len(hat)
    ys = [y0 - 50 - RH * i for i in range(nrow + 1)]

    def tx(s, p, hgt, al, lay=LJ_Y):
        q = m.add_text(s, height=hgt, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': KD.WF})
        q.set_placement(p, align=al)
    tx('LEJANT', (x0 + (W0 + W1) / 2, y0 - 25), 20, TA.MIDDLE_CENTER, LJ_B)
    for yy in [y0] + ys:
        m.add_line((x0, yy), (x0 + W0 + W1, yy), dxfattribs={'layer': LJ_C})
    for xx in (x0, x0 + W0, x0 + W0 + W1):
        m.add_line((xx, y0 - 50), (xx, ys[-1]), dxfattribs={'layer': LJ_C})
    m.add_line((x0, y0), (x0, y0 - 50), dxfattribs={'layer': LJ_C})
    m.add_line((x0 + W0 + W1, y0), (x0 + W0 + W1, y0 - 50), dxfattribs={'layer': LJ_C})
    for i, (b, s, ad) in enumerate(sat):
        yc = (ys[i] + ys[i + 1]) / 2
        if b in S.doc.blocks:
            from ezdxf import bbox as zb_
            bd = S.doc.blocks.get(b)
            ex = zb_.extents([e for e in bd if e.dxftype() != 'ATTDEF'])
            cx, cy = (ex.extmin.x + ex.extmax.x) / 2 * s, (ex.extmin.y + ex.extmax.y) / 2 * s
            e = m.add_blockref(b, (x0 + W0 / 2 - cx, yc - cy), dxfattribs={'layer': LJ_S, 'xscale': s, 'yscale': s})
            if any(a.dxftype() == 'ATTDEF' for a in bd):
                e.add_auto_attribs({})
                for a in e.attribs:
                    a.is_invisible = True
        tx(ad, (x0 + W0 + 15, yc), 11, TA.MIDDLE_LEFT)
    for j, (lay, ad) in enumerate(hat):
        i = len(sat) + j
        yc = (ys[i] + ys[i + 1]) / 2
        m.add_line((x0 + 20, yc), (x0 + W0 - 20, yc), dxfattribs={'layer': lay, 'ltscale': 0.5})
        tx(ad, (x0 + W0 + 15, yc), 11, TA.MIDDLE_LEFT)
    return ys[-1]


def hesap_kutusu(S, x0, y0, QT, alan, gerek, var, formul, S_A, S_U, oran, ba, ha, bu, hu, on_m, d, Fk, ak):
    m = S.msp
    sat = [
        ('KAZAN DAİRESİ KONTROLLERİ (07 §5)', None),
        (f'Toplam kapasite ΣQ = {tr(QT, 0)} kW  -  alan A = {tr(alan, 2)} m²', None),
        (f'Alt menfez (F={tr(Fk, 2)}, ızgaralı a={tr(ak, 2)}): {formul}', None),
        (f'   seçilen {ba:.0f} × {ha:.0f} = {tr(ba * ha, 0)} cm² ≥ {tr(S_A, 0)} cm²  ✓', None),
        (f'Üst menfez: S_Ü = max(180 ; {tr(oran, 2)}·S_A) = {tr(S_U, 0)} cm²  →  {bu:.0f} × {hu:.0f} = '
         f'{tr(bu * hu, 0)} cm²  ✓', None),
        (f'Kapı: ΣQ {">" if QT > 350 else "≤"} 350 kW, A {">" if alan > 100 else "≤"} 100 m²  →  gerekli {gerek}, '
         f'çizilen {var}  {"✓" if var >= gerek else "✗"}', None),
        (f'Kazan önü serbest mesafe {tr(on_m / 100, 2)} m ≥ kazan boyu + 1,00 = {tr((d + 100) / 100, 2)} m  '
         f'{"✓" if on_m >= d + 100 else "✗"}', None),
        ('Yangın ayrımı: duvar / döşeme / tavan EI 120, kapılar EI2 90-C', None),
    ]
    for i, (s, _) in enumerate(sat):
        q = m.add_text(s, height=16 if i == 0 else 11, dxfattribs={'layer': LJ_B if i == 0 else LJ_Y,
                                                                   'style': 'ROTAS', 'width': KD.WF})
        q.set_placement((x0, y0 - i * 24), align=TA.MIDDLE_LEFT)
    yb = y0 - len(sat) * 24
    m.add_lwpolyline([(x0 - 15, yb), (x0 + 1150, yb), (x0 + 1150, y0 + 25), (x0 - 15, y0 + 25)], close=True,
                     dxfattribs={'layer': 'ROTAS-HESAP-CERCEVE'})
    return yb


# ============================================================================ DIŞ API (her projede bu kullanılır)
class KapsamKutusu(tuple):
    """(x0, y0, x1, y1) — ek bilgiler: .uyarilar, .satir (cihaz listesi), .harita (rol → numara),
    .yeniden_ad {'katman': {}, 'blok': {}, 'stil': {}}, .girdi (kullanılan JSON, plan dahil), .numara ('R1'/'R2')"""
    pass


def girdi_oku(girdi):
    """dict | JSON dosya yolu | JSON metni → dict (kopya)"""
    if isinstance(girdi, dict):
        return copy.deepcopy(girdi)
    s = str(girdi)
    if s.lstrip().startswith('{'):
        return json.loads(s)
    with open(s, encoding='utf-8') as f:
        return json.load(f)


def varsayilan_plan(P, genislik=None, derinlik=600.0):
    """JSON'da 'plan' yoksa temsili oda: kazan duvarı üst kenar, örneklerdeki (ornekler/*.json) oranlarla kapı / menfez /
    baca yerleşimi. Genişlik sekonder kollektörün sığacağı kadar büyütülür (onayli_kazan_dairesi içinde)."""
    n = int(P['kazan']['adet'])
    W = float(genislik or max(800.0, 450.0 + 100.0 * n + (300.0 if P.get('boyler') else 0.0)))
    W = math.ceil(W / 50.0) * 50.0
    D = float(derinlik)
    ko = {'g': 60, 'd': 55, 'h': 100, 'ara': 40, 'alt_kot': 185, 'baca_cap': 16}
    QT = n * float(P['kazan']['kapasite_kw'])
    x_kapi = round(W * 0.40 / 5) * 5
    x_men = min(x_kapi + 200.0, W - 120.0)            # kapı ve menfez yazıları (≈ 125 cm) birbirine binmesin
    kap = [{'duvar': 'alt', 'konum': x_kapi, 'genislik': 100}]
    if QT > 350:
        kap.append({'duvar': 'alt', 'konum': min(x_men + 200.0, W - 80.0), 'genislik': 100})
    return {'temsili': True, 'oda': [[0, 0], [W, 0], [W, D], [0, D]], 'duvar': 25, 'doseme': 30, 'ic_yukseklik': 350,
            'kazan_olcu': ko, 'baca': [40, D - ko['d'] - 2 + ko['d'] / 2], 'kapilar': kap,
            'menfez': {'alt': {'duvar': 'alt', 'konum': x_men, 'alt_kot': 15},
                       'ust': {'duvar': 'ust', 'konum': W - 90, 'tavandan': 10}},
            'menfez_F': 1.0, 'menfez_a': 1.2, 'ust_menfez_orani': 0.6}


def _plan_hazirla(P):
    """plan yoksa varsayılanı kurar; oda dar gelirse (sekonder kollektör sığmazsa) bir kez genişletir."""
    if P.get('plan'):
        return P, None
    P['plan'] = varsayilan_plan(P)
    return P, 'otomatik'


def _blok_imza(doc, ad):
    """blok içerik imzası: nesne tipi + tüm DXF öznitelikleri (tutamaç hariç) + polyline köşeleri"""
    def yuv(v):
        if isinstance(v, float):
            return round(v, 3)
        if hasattr(v, 'x'):
            return tuple(round(x, 3) for x in v)
        return v
    out = []
    for e in doc.blocks.get(ad):
        a = tuple(sorted(((k, yuv(v)) for k, v in e.dxfattribs().items() if k not in ('handle', 'owner')), key=str))
        ek = ()
        if e.dxftype() == 'LWPOLYLINE':
            ek = tuple(tuple(round(x, 3) for x in q) for q in e.get_points())
        elif e.dxftype() == 'HATCH':
            ek = (len(e.paths), e.dxf.pattern_name)
        out.append((e.dxftype(), a, ek))
    return tuple(out)


def _bos_ad(var, ad, ek):
    yeni, k = ad + ek, 2
    while yeni in var:
        yeni, k = f'{ad}{ek}{k}', k + 1
    return yeni


def _insertler(doc):
    yield from doc.modelspace().query('INSERT')
    for b in doc.blocks:
        yield from b.query('INSERT')


def onayli_kazan_dairesi(hedef, girdi, x0=0.0, y0=0.0, numara='R2', cerceve=True, ek='-KD'):
    """ONAYLI kazan dairesi (plan 1/50 + kesit A-A + kısmi görünüş B + lejant + kontrol kutusu + cihaz listesi + notlar)
    paftasını hedef çizime, sol alt köşesi (x0, y0) olacak şekilde yerleştirir. Görünüş plan_kesit.uret ile birebir aynıdır.

    hedef  : ezdxf Drawing veya bir layout (modelspace / blok)
    girdi  : prensip şeması JSON'u (dict / dosya yolu / JSON metni). 'plan' yoksa temsili oda kurulur (varsayilan_plan).
    numara : 'R2' (varsayılan) → numaralar teslimdeki R2 prensip şemasıyla aynı; 'R1' → onay anındaki numaralar.
    cerceve: False ise dış ROTAS-PAFTA çerçevesi aktarılmaz.
    Çakışma yönetimi: hedefte aynı adlı katman farklı renk / çizgi tipindeyse kaynak katman '<ad>-KD' olur; aynı adlı blok
    farklı içerikteyse '<ad>-KD' adıyla aktarılır (aynıysa hedefteki kullanılır); ROTAS yazı stili fontu farklıysa
    'ROTAS-KD'. Çizgi tipi ölçeği (kaynak $LTSCALE 8) hedefin $LTSCALE değerine göre nesne bazında korunur.
    Dönüş: KapsamKutusu (x0, y0, x1, y1) hedef koordinatında."""
    from ezdxf import xref
    from ezdxf.layouts import BaseLayout
    if isinstance(hedef, BaseLayout):
        tdoc, tlay = hedef.doc, hedef
    else:
        tdoc, tlay = hedef, hedef.modelspace()
    P, plan_kaynak = _plan_hazirla(girdi_oku(girdi))
    S = uret(P, None, numara)
    if plan_kaynak and any('oda genişliği yetersiz' in u for u in S.uyarilar):
        gerek = max(float(u.split(':')[1].split('>')[0].strip().replace('.', '').replace(',', '.'))
                    for u in S.uyarilar if 'oda genişliği yetersiz' in u)
        P['plan'] = varsayilan_plan(P, genislik=gerek + 60.0)
        S = uret(P, None, numara)
    src = S.doc
    smsp = src.modelspace()
    if not cerceve:
        smsp.delete_entity(S.cerceve)
    kx0, ky0, kx1, ky1 = S.kapsam
    dx, dy = x0 - kx0, y0 - ky0
    for e in smsp:
        e.translate(dx, dy, 0)
    yeni = {'katman': {}, 'blok': {}, 'stil': {}}
    # ---- katmanlar
    for lay in list(src.layers):
        ad = lay.dxf.name
        if ad in ('0', 'Defpoints') or ad not in tdoc.layers:
            continue
        t = tdoc.layers.get(ad)
        if (t.color, t.dxf.linetype.upper(), t.dxf.get('true_color')) != \
                (lay.color, lay.dxf.linetype.upper(), lay.dxf.get('true_color')):
            yad = _bos_ad(set(tdoc.layers.entries.keys()) | set(src.layers.entries.keys()), ad, ek)
            lay.rename(yad)
            yeni['katman'][ad] = yad
    # ---- yazı stilleri
    for st in list(src.styles):
        ad = st.dxf.name
        if ad in tdoc.styles and tdoc.styles.get(ad).dxf.font.lower() != st.dxf.font.lower():
            yad = _bos_ad(set(tdoc.styles.entries.keys()) | set(src.styles.entries.keys()), ad, ek)
            src.styles.new(yad, dxfattribs={'font': st.dxf.font, 'width': st.dxf.get('width', 1.0)})
            yeni['stil'][ad] = yad
    if yeni['stil']:
        for lay_ in [smsp] + [b for b in src.blocks]:
            for e in lay_:
                if e.dxftype() in ('TEXT', 'MTEXT', 'ATTDEF') and e.dxf.get('style') in yeni['stil']:
                    e.dxf.style = yeni['stil'][e.dxf.style]
                if e.dxftype() == 'INSERT':
                    for a in e.attribs:
                        if a.dxf.get('style') in yeni['stil']:
                            a.dxf.style = yeni['stil'][a.dxf.style]
    # ---- bloklar (içerik farklıysa yeniden adlandır; iç içe başvuru varsa üst blok da)
    adlar = [b.name for b in src.blocks if not b.name.startswith('*')]
    farkli = {a for a in adlar if a in tdoc.blocks and _blok_imza(src, a) != _blok_imza(tdoc, a)}
    degisti = True
    while degisti:
        degisti = False
        for a in adlar:
            if a in tdoc.blocks and a not in farkli and \
                    any(i.dxf.name in farkli for i in src.blocks.get(a).query('INSERT')):
                farkli.add(a)
                degisti = True
    tum = set(tdoc.blocks.block_names()) | set(adlar)
    for a in sorted(farkli):
        yad = _bos_ad(tum, a, ek)
        tum.add(yad)
        yeni['blok'][a] = yad
    if yeni['blok']:
        for e in list(_insertler(src)):
            if e.dxf.name in yeni['blok']:
                e.dxf.name = yeni['blok'][e.dxf.name]
        for a, yad in yeni['blok'].items():
            src.blocks.rename_block(a, yad)
    # ---- çizgi tipi ölçeği (kaynak $LTSCALE → hedef)
    oran = float(src.header.get('$LTSCALE', 1.0)) / float(tdoc.header.get('$LTSCALE', 1.0) or 1.0)
    yeni_bloklar = [b for b in src.blocks if not b.name.startswith('*') and b.name not in tdoc.blocks]
    if abs(oran - 1.0) > 1e-9:
        for lay_ in [smsp] + yeni_bloklar:
            for e in lay_:
                e.dxf.ltscale = e.dxf.get('ltscale', 1.0) * oran
    if 'ROTAS' not in tdoc.appids:
        tdoc.appids.new('ROTAS')
    once = {e.dxf.handle for e in tlay}
    ld = xref.Loader(src, tdoc, conflict_policy=xref.ConflictPolicy.KEEP)
    ld.load_modelspace(target_layout=tlay)
    ld.execute()
    gelen = sum(1 for e in tlay if e.dxf.handle not in once)
    for e in tlay:                     # işaret: denetimler onaylı paftayı (MTY/atlatma kurallarından muaf) tanır
        if e.dxf.handle not in once and e.dxftype() == 'LWPOLYLINE' and e.dxf.layer.startswith(KD.PAFTA) \
                and e.dxf.get('const_width', 0) == 3 and len(e) == 4:
            e.set_xdata('ROTAS', [(1000, 'ONAYLI_KAZAN_DAIRESI')])
    beklenen = len(smsp)
    uy = list(S.uyarilar)
    if gelen != beklenen:
        uy.append(f'aktarım: {gelen} / {beklenen} nesne')
    k = KapsamKutusu((x0, y0, x0 + (kx1 - kx0), y0 + (ky1 - ky0)))
    k.uyarilar, k.satir, k.harita, k.yeniden_ad, k.girdi, k.numara, k.nesne = uy, S.satir, S.harita, yeni, P, numara, gelen
    return k


if __name__ == '__main__':
    arg = list(sys.argv[1:])
    num = 'R1'
    if '--numara' in arg:
        i = arg.index('--numara')
        num = arg[i + 1]
        del arg[i:i + 2]
    P = json.load(open(arg[0], encoding='utf-8'))
    S = uret(P, arg[1], num)
    for u in S.uyarilar:
        print('UYARI:', u)
    if len(arg) > 2:
        import onizleme
        onizleme.png(arg[1], arg[2])
