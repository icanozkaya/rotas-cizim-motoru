"""yerden2 — YERDEN ISITMA KOLON ŞEMASI (saf geometri, kullanıcının şeması: YERDEN_ISITMA_ALTIN_REFERANS §5, S-1..S-6).

Kat bantları 400 cm (aşağıdan yukarı zemin, 1, 2), sol 50 cm sütunda dikey kırmızı kat adı; her dairede kombi +
kollektör, "H. KOMBİ 24KW", daire balonu, devre panelleri 200 cm adımla (devre no büyükten küçüğe), döşeme altında
kademeli gidiş (kırmızı sürekli) / dönüş (turuncu çizgi-nokta) hatları, "NNNN.NW-Ø20" hat etiketleri, kollektör toplamı
"ΣW-Ø32". Değerler plan etiketleriyle aynı (model json).
"""
import math

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

PY0, PY1 = -444050.0, -441150.0          # pafta y (referans ile aynı)
X0 = 258850.0                            # şema paftası sol kenarı (2. kat planının sağı)
BANT_H = 400.0
BANT0 = -443201.6                        # zemin bandı alt çizgisi (döşeme)
SOL = 114.4                              # pafta sol kenarı -> bant iç sol kenarı
ETK = 50.0                               # kat adı sütunu
K_OFS = 146.0                            # bant iç sol -> ilk dairenin kollektör ref. noktası
PANEL0 = 290.0
PANEL_ADIM = 200.0

G = 'ROTAS-ISITMA-GIDIS-BORU'
DN = 'ROTAS-ISITMA-DONUS-BORU'
CAP = 'ROTAS-ISITMA-CAP'
DET = 'ROTAS-ISITMA-SEMA-DETAY'


def _t(msp, s, p, h, renk, katman, hiz=TA.LEFT, rot=0.0, gen=0.65):
    t = msp.add_text(s, dxfattribs={'layer': katman, 'height': h, 'style': 'ROTAS-YAZI', 'width': gen, 'color': renk,
                                    'rotation': rot})
    t.set_placement(p, align=hiz)
    return t


def _pl(msp, pts, katman, renk=256, kapali=False):
    return msp.add_lwpolyline(pts, close=kapali, dxfattribs={'layer': katman, 'color': renk})


def daire_genislik(n):
    return max(1900.0, PANEL0 + PANEL_ADIM * (n - 1) + 129.0 + 160.0)


def panel(msp, Px, Y0, d):
    """döşeme kesiti sembolü (1:1), referans *U108 ölçüleri"""
    # duvar kesiti
    _pl(msp, [(Px - 20, Y0), (Px - 10, Y0), (Px - 10, Y0 + 60), (Px - 20, Y0 + 60)], DET, 8, True)
    h = msp.add_hatch(color=8, dxfattribs={'layer': DET})
    h.set_pattern_fill('ANSI31', scale=0.6)
    h.paths.add_polyline_path([(Px - 20, Y0), (Px - 10, Y0), (Px - 10, Y0 + 60), (Px - 20, Y0 + 60)], is_closed=True)
    # şap
    sap = [(Px + 8, Y0), (Px + 124, Y0), (Px + 124, Y0 + 20), (Px + 8, Y0 + 20)]
    _pl(msp, sap, DET, 8, True)
    h = msp.add_hatch(color=8, dxfattribs={'layer': DET})
    h.set_pattern_fill('AR-SAND', scale=0.15)
    h.paths.add_polyline_path(sap, is_closed=True)
    # döşeme üst çizgileri
    msp.add_line((Px - 20, Y0 + 60), (Px + 129, Y0 + 60), dxfattribs={'layer': DET, 'color': 7})
    msp.add_line((Px - 20, Y0 + 55), (Px + 129, Y0 + 55), dxfattribs={'layer': DET, 'color': 8})
    msp.add_line((Px + 129, Y0 + 55), (Px + 129, Y0 + 60), dxfattribs={'layer': DET, 'color': 7})
    # boru ilmeği: gidiş (kırmızı) üstte, dönüş (turuncu) altta, yuvarlak köşe
    t = math.tan(math.radians(22.5))
    msp.add_lwpolyline([(Px - 5, Y0 + 50, 0), (Px + 112, Y0 + 50, -t), (Px + 119, Y0 + 43, 0), (Px + 119, Y0 + 37.5, 0)],
                       format='xyb', dxfattribs={'layer': DET, 'color': 10})
    msp.add_lwpolyline([(Px + 119, Y0 + 37.5, 0), (Px + 119, Y0 + 32, -t), (Px + 112, Y0 + 25, 0), (Px, Y0 + 25, 0)],
                       format='xyb', dxfattribs={'layer': DET, 'color': 30})
    # yazılar (referans öznitelik konumları)
    _t(msp, d['zon'], (Px + 3, Y0 + 31), 15, 2, DET)
    _t(msp, '%d%%%%DC' % d['sic'], (Px + 94, Y0 + 33), 10, 2, DET)
    _t(msp, '%.1f W' % d['W'], (Px + 12, Y0 + 70), 10, 2, DET)
    _t(msp, '%.2f m' % d['L_m'], (Px + 64, Y0 + 70), 10, 2, DET)
    _t(msp, 'DEVRE', (Px + 12, Y0 + 100), 10, 2, DET)
    _t(msp, str(d['no']), (Px + 85, Y0 + 100), 10, 2, DET)
    _t(msp, 'PEX BORU, 16 x 2.0', (Px + 4, Y0 - 13), 7, 2, DET)


def kombi_kollektor(msp, Kx, Y0, n, toplamW, kombi_kw):
    # kombi (sarı dikdörtgen + alt şerit + 4 bağlantı)
    _pl(msp, [(Kx - 92, Y0 + 118), (Kx - 41, Y0 + 118), (Kx - 41, Y0 + 220), (Kx - 92, Y0 + 220)],
        'ROTAS-ISITMA-CIHAZ', 2, True)
    msp.add_line((Kx - 92, Y0 + 128), (Kx - 41, Y0 + 128), dxfattribs={'layer': 'ROTAS-ISITMA-CIHAZ', 'color': 2})
    for i in range(4):
        msp.add_circle((Kx - 85 + 12 * i, Y0 + 123), 2.5, dxfattribs={'layer': 'ROTAS-ISITMA-CIHAZ', 'color': 2})
    _t(msp, 'H. KOMBİ %dKW' % kombi_kw, (Kx + 33, Y0 + 195), 20, 4, 'ROTAS-ISITMA-CIHAZ')
    # kollektör dolabı
    xl = min(Kx - 23, Kx + 85 - 10 * (n - 1) - 14)
    KL = 'ROTAS-ISITMA-KOLLEKTOR'
    _pl(msp, [(xl, Y0 + 10), (Kx + 100, Y0 + 10), (Kx + 100, Y0 + 70), (xl, Y0 + 70)], KL, 1, True)
    _pl(msp, [(xl + 6, Y0 + 50), (Kx + 94, Y0 + 50), (Kx + 94, Y0 + 56), (xl + 6, Y0 + 56)], KL, 10, True)
    _pl(msp, [(xl + 6, Y0 + 27), (Kx + 94, Y0 + 27), (Kx + 94, Y0 + 33), (xl + 6, Y0 + 33)], KL, 30, True)
    for i in range(n):
        xg, xd = Kx + 85 - 10 * i, Kx + 80 - 10 * i
        msp.add_line((xg, Y0 + 50), (xg, Y0 + 20), dxfattribs={'layer': KL, 'color': 10})
        msp.add_line((xd, Y0 + 27), (xd, Y0 + 20), dxfattribs={'layer': KL, 'color': 30})
        msp.add_circle((xg, Y0 + 40), 1.8, dxfattribs={'layer': KL, 'color': 10})
    # kombi -> kollektör (gidiş kırmızı sürekli, dönüş turuncu çizgi-nokta), üzerinde küresel vana
    _pl(msp, [(Kx - 55, Y0 + 118), (Kx - 55, Y0 + 53), (xl, Y0 + 53)], G)
    _pl(msp, [(Kx - 80, Y0 + 118), (Kx - 80, Y0 + 30), (xl, Y0 + 30)], DN)
    for x, y in ((Kx - 55, Y0 + 95), (Kx - 80, Y0 + 95)):
        _pl(msp, [(x - 3, y - 5), (x + 3, y + 5), (x - 3, y + 5), (x + 3, y - 5)], KL, 1, True)
    # kollektör toplamı
    _t(msp, '%.1fW-%%%%C32' % toplamW, (xl, Y0 + 76), 10, 41, CAP)
    msp.add_line((xl, Y0 + 74), (xl + 8, Y0 + 70), dxfattribs={'layer': CAP, 'color': 41})


def daire_balonu(msp, x, y, ad):
    msp.add_circle((x, y), 55, dxfattribs={'layer': 'ROTAS-ISITMA-DAIRE-NO', 'color': 6})
    msp.add_circle((x, y), 49, dxfattribs={'layer': 'ROTAS-ISITMA-DAIRE-NO', 'color': 7})
    _t(msp, ad, (x, y), 40, 6, 'ROTAS-ISITMA-DAIRE-NO', TA.MIDDLE_CENTER, gen=0.8)


def ciz(doc, msp, model):
    katlar = model['katlar']
    # bant genişliği: en geniş kat
    gen = []
    for kat in katlar:
        ds = sorted(kat['daireler'].values(), key=lambda d: -int(d['no'][1:]))
        gen.append(sum(daire_genislik(sum(len(m['devreler']) for m in d['mahaller'])) for d in ds))
    ic_w = max(gen) + K_OFS + 60
    xb = X0 + SOL
    x_sag = xb + ic_w
    X1 = x_sag + 88.0
    # pafta çerçevesi
    _pl(msp, [(X0, PY0), (X1, PY0), (X1, PY1), (X0, PY1)], 'ROTAS-PAFTA', 256, True)
    toplam_sema = []
    for ki, kat in enumerate(katlar):
        Y0 = BANT0 + BANT_H * ki
        _pl(msp, [(xb - ETK, Y0), (x_sag, Y0), (x_sag, Y0 + BANT_H), (xb - ETK, Y0 + BANT_H)], 'ROTAS-SEMA-KAT-BANDI', 7, True)
        msp.add_line((xb, Y0), (xb, Y0 + BANT_H), dxfattribs={'layer': 'ROTAS-SEMA-KAT-BANDI', 'color': 7})
        ad = {'Z': 'ZEMİN. KAT', '1': '1. KAT', '2': '2. KAT'}[kat['kat']]
        _t(msp, ad, (xb - ETK / 2, Y0 + BANT_H / 2), 25, 1, 'ROTAS-SEMA-KAT-YAZI', TA.MIDDLE_CENTER, rot=90.0, gen=0.8)
        Kx = xb + K_OFS
        for dd in sorted(kat['daireler'].values(), key=lambda d: -int(d['no'][1:])):
            devs = []
            for m in dd['mahaller']:
                for c in m['devreler']:
                    devs.append(dict(c, zon=m['zon'], sic=m['sic']))
            devs.sort(key=lambda c: -c['no'])           # en büyük no kollektöre en yakın
            n = len(devs)
            W = sum(c['W'] for c in devs)
            kombi_kollektor(msp, Kx, Y0, n, W, 24 if W <= 20000 else 28)
            daire_balonu(msp, Kx + 277, Y0 + 200, dd['no'])
            for i, c in enumerate(devs):
                Px = Kx + PANEL0 + PANEL_ADIM * i
                panel(msp, Px, Y0, c)
                yg, yd = Y0 - 20 - 10 * i, Y0 - 25 - 10 * i
                _pl(msp, [(Px - 5, Y0 + 50), (Px - 5, yg), (Kx + 85 - 10 * i, yg), (Kx + 85 - 10 * i, Y0 + 20)], G)
                _pl(msp, [(Px, Y0 + 25), (Px, yd), (Kx + 80 - 10 * i, yd), (Kx + 80 - 10 * i, Y0 + 20)], DN)
                _t(msp, '%.1fW-%%%%C20' % c['W'], (Px - 15, yg + 1.5), 10, 41, CAP, TA.BOTTOM_RIGHT)
                msp.add_line((Px - 13, yg + 1), (Px - 8, yg + 6), dxfattribs={'layer': CAP, 'color': 41})
                toplam_sema.append((kat['kat'], dd['no'], c['no'], c['W'], c['L_m']))
            Kx += daire_genislik(n)
    # başlık, lejant, notlar
    _t(msp, 'YERDEN ISITMA KOLON ŞEMASI', ((X0 + X1) / 2, BANT0 - 330), 40, 7, 'ROTAS-PAFTA-BASLIK', TA.MIDDLE_CENTER, gen=0.8)
    lejant(msp, X0 + 200, BANT0 + 3 * BANT_H + 600)
    notlar(msp, X0 + 1500, BANT0 + 3 * BANT_H + 600, model)
    return toplam_sema


def lejant(msp, x, y):
    L = 'ROTAS-LEJANT'
    _t(msp, 'LEJANT', (x, y), 25, 7, L, gen=0.8)
    satir = [
        ('ROTAS-ISITMA-PEX', 'PEX BORU 16 x 2,0 — YERDEN ISITMA DEVRESİ (planda, 15 cm aralık)'),
        (G, 'ISITMA GİDİŞ HATTI (şema)'),
        (DN, 'ISITMA DÖNÜŞ HATTI (şema)'),
    ]
    yy = y - 50
    for kat, s in satir:
        msp.add_line((x, yy + 5), (x + 120, yy + 5), dxfattribs={'layer': kat})
        _t(msp, s, (x + 140, yy), 12, 7, L)
        yy -= 35
    msp.add_blockref('ROTAS-YI-ETIKET', (x, yy + 10), dxfattribs={'layer': 'ROTAS-ISITMA-ETIKET'}).add_auto_attribs(
        {'UZ': '00.00 m', 'AR': '15.0', 'YER': '0000.0 W', 'NO1': 'n'})
    _t(msp, 'DEVRE ETİKETİ (hat uzunluğu, boru aralığı, ısıl güç = 35 W/m × L, devre no)', (x + 170, yy - 30), 12, 7, L)
    yy -= 130
    msp.add_blockref('ROTAS-YI-MAHAL', (x + 40, yy), dxfattribs={'layer': 'ROTAS-ISITMA-MAHAL-ETIKET'}).add_auto_attribs(
        {'DERECE': '20%%DC', 'NO': 'Z01'})
    _t(msp, 'MAHAL ETİKETİ (iç sıcaklık / zon no: zemin Z01.., 1. kat 101.., 2. kat 201..)', (x + 170, yy - 5), 12, 7, L)


def notlar(msp, x, y, model):
    L = 'ROTAS-NOT'
    _t(msp, 'NOTLAR', (x, y), 25, 7, L, gen=0.8)
    s = [
        '1- Yerden ısıtma borusu PEX 16 x 2,0 (oksijen bariyerli), boru aralığı 15 cm, kenar mesafesi 7,5 cm.',
        '2- Her devre tek parça boru (ek yok), devre boyu en çok 80 m; 14 m² ve üstü mahaller 2 devre.',
        '3- Oda / salon / mutfak 20°C, antre-koridor 15°C, banyo 24°C. Balkon, yüklük, 2 m² altı wc-lavabo ve duş,',
        '   merdiven, asansör ve ortak alanlar ısıtılmaz; mutfak tezgâhı, buzdolabı, klozet ve lavabo altına boru döşenmez.',
        '4- Devre ısıl gücü etiketlerde 35 W/m × hat uzunluğu olarak verilmiştir; hesap tablosu ayrıdır.',
        '5- Kollektör ve kombi bağlantıları kolon şemasında gösterilmiştir; kollektör yeri uygulamada daire holünde seçilir.',
    ]
    yy = y - 45
    for q in s:
        _t(msp, q, (x, yy), 12, 7, L)
        yy -= 25
