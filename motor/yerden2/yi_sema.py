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
    """daire bloğu genişliği: kullanıcının şemasında 9 devreli daire 2144 cm (290 + 8·200 + 254)"""
    return PANEL0 + PANEL_ADIM * (n - 1) + 254.0


def son_daire_genislik(n):
    """bandın sağındaki son daire: son panel + 129 (panel) + 15 (kullanıcı: bant iç 6490 = 146 + 2·2144 + 2056)"""
    return PANEL0 + PANEL_ADIM * (n - 1) + 166.0


# kullanıcının *U108 bloğundaki tarama tanımları (new_block.dxf, birebir; taban noktası blok koordinatında)
TARAMA = {
    'AR-CONC': (1.0, 0.0, [
        (50.0, (-135697.0398850483, 398449.7369082842), (7.172601826007534, -0.6275213498259511), [0.75, -8.25]),
        (355.0, (-135697.0398850483, 398449.7369082842), (-1.38751333613, 7.521921337000118), [0.6, -6.599999999999999]),
        (100.45144446, (-135696.4421682383, 398449.6846148442), (5.785088467271119, 6.894399909686294), [0.6374019199999994, -7.011421119999994]),
        (46.18420000000001, (-135697.0398850483, 398451.7369082842), (10.67241330671572, -1.655192807930765), [1.124999999999998, -12.37499999999999]),
        (96.63563549000003, (-135696.1505175983, 398451.5989752142), (9.346619456742284, 9.741186007745505), [0.9561034199999999, -10.5171376]),
        (351.18416399, (-135697.0398850483, 398451.7369082842), (9.346619450547731, 9.741186002699902), [0.9, -9.90000001]),
        (21.0, (-135696.0398850483, 398451.2369082843), (5.969070521184616, -4.026188906653388), [0.75, -8.25]),
        (326.0, (-135696.0398850483, 398451.2369082843), (2.433153319215817, 7.25150045046853), [0.6, -6.599999999999999]),
        (71.45144474, (-135695.5424625083, 398450.9013925443), (8.402223767299711, 3.225311528063538), [0.6374019000000001, -7.011421119999999]),
        (37.5, (-135697.0398850483, 398449.7369082842), (0.1215985531729067, 3.328938538313114), [0.0, -6.519999999999999, 0.0, -6.7, 0.0, -6.625]),
        (7.499999999999999, (-135697.0398850483, 398449.7369082842), (2.630695374421486, 3.944117118823602), [0.0, -3.819999999999999, 0.0, -6.37, 0.0, -2.524999999999999]),
        (327.5, (-135699.2698850483, 398449.7369082842), (5.33822436172409, -0.2255487173437976), [0.0, -2.5, 0.0, -7.799999999999999, 0.0, -10.35]),
        (317.5, (-135700.2698850483, 398449.7369082842), (5.831861693423862, 1.001049823323177), [0.0, -3.25, 0.0, -5.179999999999999, 0.0, -7.349999999999999]),
    ]),
    'ANSI38': (25.0, 0.0, [
        (45.0, (-135697.0398850483, 398444.736908284), (-2.20970869120796, 2.209708691207961), []),
        (135.0, (-135697.0398850483, 398444.736908284), (-6.629126073623882, 2.209708691207961), [7.8125, -4.6875]),
    ]),
    'ACAD_ISO08W100': (0.898128898128898, 90.0, [
        (90.0, (-135697.0398850483, 398444.736908284), (-4.49064449064449, 3e-16), [21.55509355509355, -2.694386694386694, 5.388773388773388, -2.694386694386694]),
    ]),
}


PW = 129.283765942615      # kullanıcının *U108 bloğu genişliği (−20 … 129,28)
PI = 124.283765942615
PB = 114.283765942615


def _tarama(msp, pts, desen, Px, Y0, renk):
    """kullanıcının tarama tanımı birebir (desen satırları, ölçek, açı); taban noktası blok yerleşimine taşınır"""
    olcek, aci, satirlar = TARAMA[desen]
    h = msp.add_hatch(color=renk, dxfattribs={'layer': DET})
    h.set_pattern_definition([[a, (Px + b[0], Y0 + b[1]), o, list(d)] for a, b, o, d in satirlar])
    h.dxf.solid_fill = 0
    h.dxf.pattern_type = 1
    h.dxf.pattern_name = desen
    h.dxf.pattern_scale = olcek
    h.dxf.pattern_angle = aci
    h.paths.add_polyline_path(pts, is_closed=True)
    return h


PANEL_BLOK = 'ROTAS-YI-DEVRE-PANELI'


def panel_blogu(doc):
    """kullanıcının *U108 bloğunun sabit geometrisi (yazısız), kendi bloğumuz olarak (MTY bloğu değil)"""
    if PANEL_BLOK in doc.blocks:
        return
    blk = doc.blocks.new(PANEL_BLOK)
    P = lambda x, y: (x, y)  # noqa: E731
    blk.add_lwpolyline([P(-10, 0), P(-20, 0), P(-20, 60), P(PW, 60), P(PW, 0), P(5, 0), P(5, 20), P(PW, 20)],
                       dxfattribs={'layer': DET, 'color': 7})
    blk.add_lwpolyline([P(-10, 0), P(-10, 20), P(-15, 20), P(-20, 20)], dxfattribs={'layer': DET, 'color': 7})
    blk.add_line(P(-20, 55), P(PW, 55), dxfattribs={'layer': DET, 'color': 7})
    blk.add_line(P(-15, 55), P(-15, 20), dxfattribs={'layer': DET, 'color': 7})
    blk.add_line(P(PI, 55), P(PI, 20), dxfattribs={'layer': DET, 'color': 7})
    _tarama(blk, [P(5, 0), P(PW, 0), P(PW, 20), P(5, 20)], 'AR-CONC', 0.0, 0.0, 15)
    _tarama(blk, [P(-20, 0), P(-10, 0), P(-10, 20), P(-20, 20)], 'AR-CONC', 0.0, 0.0, 15)
    _tarama(blk, [P(-20, 20), P(-15, 20), P(-15, 55), P(-20, 55)], 'ANSI38', 0.0, 0.0, 15)
    _tarama(blk, [P(PI, 20), P(PW, 20), P(PW, 55), P(PI, 55)], 'ANSI38', 0.0, 0.0, 15)
    _tarama(blk, [P(PW, 55), P(PW, 60), P(-20, 60), P(-20, 55)], 'ACAD_ISO08W100', 0.0, 0.0, 7)
    blk.add_line(P(0, 50), P(PB, 50), dxfattribs={'layer': G})
    blk.add_arc(P(0, 45), 5, 90, 180, dxfattribs={'layer': G})
    blk.add_arc(P(PB, 45), 5, 0, 90, dxfattribs={'layer': G})
    blk.add_line(P(PB + 5, 37.5), P(PB + 5, 45), dxfattribs={'layer': G})
    blk.add_line(P(5, 25), P(PB, 25), dxfattribs={'layer': DN})
    blk.add_arc(P(5, 20), 5, 90, 180, dxfattribs={'layer': DN})
    blk.add_arc(P(PB, 30), 5, 270, 360, dxfattribs={'layer': DN})
    blk.add_line(P(PB + 5, 37.5), P(PB + 5, 30), dxfattribs={'layer': DN})
    blk.add_line(P(0, 10), P(0, 20), dxfattribs={'layer': DN})


def panel(msp, Px, Y0, d):
    """Döşeme kesiti devre paneli — kullanıcının new_block *U108 bloğunun saf geometri kopyası (1:1, cm), kendi
    bloğumuz ROTAS-YI-DEVRE-PANELI olarak yerleşir: sol duvar (−20…−10 beton ayak, −20…−15 tuğla), sağ duvar
    (124,28…129,28), şap (5…129,28 × 0…20, AR-CONC), döşeme üstü bandı (55…60, ACAD_ISO08W100), boru ilmeği
    (gidiş 50 / dönüş 25, r 5); taramalar kullanıcının tanım satırlarıyla birebir. Yazılar kullanıcının öznitelik
    yerlerinde: Zxx h15 (1,26; 31,86), °C h10 (94,35; 33,73), W h10 (14,5; 70), m h10 (62,06; 70),
    ISIKAYBI h10 (14,15; 110) + devre no sağa dayalı (94,7; 110), PEX BORU, 16 x 2.0 h10 (4,3; −14,1)."""
    P = lambda x, y: (Px + x, Y0 + y)  # noqa: E731
    msp.add_blockref(PANEL_BLOK, (Px, Y0), dxfattribs={'layer': DET})
    # yazılar (kullanıcının öznitelik konumları ve boyları; hepsi sarı, arial ×0,65)
    _t(msp, d['zon'], P(1.26, 31.86), 15, 2, DET)
    _t(msp, '%d%%%%DC' % d['sic'], P(94.35, 33.73), 10, 2, DET)
    _t(msp, '%.1f W' % d['W'], P(14.5, 70.0), 10, 2, DET)
    _t(msp, '%.2f m' % d['L_m'], P(62.06, 70.0), 10, 2, DET)
    _t(msp, 'ISIKAYBI', P(14.15, 110.0), 10, 2, DET)
    _t(msp, str(d['no']), P(94.7, 110.0), 10, 2, DET, TA.RIGHT)
    _t(msp, 'PEX BORU, 16 x 2.0', P(4.3, -14.1), 10, 2, DET)


def hat_etiketi(msp, Px, yg, W):
    """kullanıcının *U110 bloğu (×10): kılavuz (Px−15, yg) -> 6 yukarı -> 7,5 sola; yazı h10 sola dayalı kılavuzun solunda"""
    x0 = Px - 15.0
    msp.add_lwpolyline([(x0 - 7.5, yg + 6.0), (x0, yg + 6.0), (x0, yg)], dxfattribs={'layer': CAP, 'color': 41})
    _t(msp, '%.1fW-%%%%C20' % W, (x0 - 14.0, yg + 1.0), 10, 41, CAP, TA.RIGHT)


def _r(msp, x0, y0, x1, y1, katman, renk):
    _pl(msp, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], katman, renk, True)


def kollektor(msp, Kx, Y0, n):
    """Gerçek manifold çizimi (saf geometri, kullanıcının *U127 bloğundaki kollektörün ölçüleri, 1:1 cm):
    dolap (dış/iç çerçeve + kaide), gidiş (üst) ve dönüş (alt) barı, ağız başına gidişte ayar vanası + rekor,
    dönüşte debimetre başlığı + rekor, iki uçta taşıyıcı braket, sol uçlarda kelebek kollu küresel vana + rakor,
    hava pürjörleri. Ağız adımı 10, gidiş–dönüş ağız kayıklığı 5; gidiş ağızları Kx+85-10i, dönüş Kx+80-10i."""
    KL = 'ROTAS-ISITMA-KOLLEKTOR'
    D = 7          # detay rengi (kullanıcı bloğunda beyaz/siyah)
    xs = Kx + 85 - 10 * (n - 1) - 12.4      # barların sol ucu (n = 9 -> Kx - 7.4, referansla aynı)
    xe = Kx + 92.4
    X = lambda v: Kx + v                   # noqa: E731
    # dolap (renk 15) + kaide
    _r(msp, xs - 17.3, Y0, X(100.3), Y0 + 70.5, KL, 15)
    msp.add_line((xs - 17.3, Y0 + 10.9), (X(100.3), Y0 + 10.9), dxfattribs={'layer': KL, 'color': 15})
    _r(msp, xs - 15.6, Y0 + 12.6, X(98.6), Y0 + 68.8, KL, 15)
    for x in (xs - 12.3, X(95.3)):
        msp.add_line((x, Y0), (x, Y0 + 10.9), dxfattribs={'layer': KL, 'color': 15})
    # barlar (gidiş üst 54,3–58,6 / dönüş alt 21,7–26,0), çift çizgi
    for y0, y1 in ((54.3, 58.6), (21.7, 26.0)):
        for y in (y0, y0 + 0.5, y1 - 0.5, y1):
            msp.add_line((xs, Y0 + y), (xe, Y0 + y), dxfattribs={'layer': KL, 'color': D})
    # uç braketleri
    for bx0, bx1 in ((xs - 2.8, xs), (xe, xe + 2.8)):
        _r(msp, bx0, Y0 + 16.5, bx1, Y0 + 63.7, KL, D)
        _r(msp, bx0 + 0.6, Y0 + 49.5, bx1 - 0.6, Y0 + 61.3, KL, D)
        _r(msp, bx0 + 0.6, Y0 + 17.8, bx1 - 0.6, Y0 + 29.5, KL, D)
        for yv in (59.8, 27.2):
            msp.add_circle(((bx0 + bx1) / 2, Y0 + yv), 0.9, dxfattribs={'layer': KL, 'color': D})
    # sağ uç kapakları
    for yc in (56.45, 23.85):
        _r(msp, xe + 2.8, Y0 + yc - 1.6, xe + 4.0, Y0 + yc + 1.6, KL, D)
    t = math.tan(math.radians(22.5))
    for i in range(n):
        xg, xd = X(85 - 10 * i), X(80 - 10 * i)
        # gidiş: ayar vanası (gövde + trapez kol) üstte, rekor altta
        _r(msp, xg - 1.5, Y0 + 58.6, xg + 1.5, Y0 + 60.4, KL, D)
        _pl(msp, [(xg - 1.7, Y0 + 60.4), (xg + 1.7, Y0 + 60.4), (xg + 1.9, Y0 + 63.3), (xg - 1.9, Y0 + 63.3)], KL, D, True)
        _pl(msp, [(xg - 0.9, Y0 + 60.4), (xg, Y0 + 62.6), (xg + 0.9, Y0 + 60.4)], KL, D)
        msp.add_line((xg - 0.4, Y0 + 62.6), (xg - 0.4, Y0 + 63.3), dxfattribs={'layer': KL, 'color': D})
        msp.add_line((xg + 0.4, Y0 + 62.6), (xg + 0.4, Y0 + 63.3), dxfattribs={'layer': KL, 'color': D})
        _r(msp, xg - 1.6, Y0 + 53.0, xg + 1.6, Y0 + 54.3, KL, D)
        _r(msp, xg - 1.2, Y0 + 52.2, xg + 1.2, Y0 + 53.0, KL, D)
        # dönüş: debimetre başlığı (üstü yuvarlatılmış) + taban, rekor altta
        msp.add_lwpolyline([(xd - 1.5, Y0 + 27.0, 0), (xd + 1.5, Y0 + 27.0, 0), (xd + 1.5, Y0 + 30.0, t * 0.5),
                            (xd + 1.1, Y0 + 30.4, 0), (xd - 1.1, Y0 + 30.4, t * 0.5), (xd - 1.5, Y0 + 30.0, 0)],
                           format='xyb', close=True, dxfattribs={'layer': KL, 'color': D})
        _r(msp, xd - 1.2, Y0 + 26.0, xd + 1.2, Y0 + 27.0, KL, D)
        _r(msp, xd - 1.6, Y0 + 20.4, xd + 1.6, Y0 + 21.7, KL, D)
        _r(msp, xd - 1.2, Y0 + 19.6, xd + 1.2, Y0 + 20.4, KL, D)
        # gidiş ağzından inen boru (dönüş barının arkasından geçer)
        msp.add_line((xg, Y0 + 52.2), (xg, Y0 + 30.8), dxfattribs={'layer': G})
    # sol uç: küresel vana (kelebek kollu) + rakor, gidiş (56,45) ve dönüş (23,85)
    for yc in (56.45, 23.85):
        x = xs - 2.8
        _r(msp, x - 1.5, Y0 + yc - 2.2, x, Y0 + yc + 2.2, KL, D)                 # rakor somunu
        _r(msp, x - 3.4, Y0 + yc - 1.9, x - 1.5, Y0 + yc + 1.9, KL, D)
        _r(msp, x - 3.9, Y0 + yc - 1.6, x - 3.4, Y0 + yc + 1.6, KL, D)
        _r(msp, x - 8.0, Y0 + yc - 2.1, x - 3.9, Y0 + yc + 2.1, KL, D)           # vana gövdesi
        _r(msp, x - 9.5, Y0 + yc - 1.6, x - 8.0, Y0 + yc + 1.6, KL, D)           # giriş ucu
        _pl(msp, [(x - 6.9, Y0 + yc + 2.1), (x - 6.9, Y0 + yc + 3.6), (x - 5.6, Y0 + yc + 4.4),
                  (x - 4.6, Y0 + yc + 4.4), (x - 4.6, Y0 + yc + 2.1)], KL, D)    # kol göbeği
        _pl(msp, [(x - 9.5, Y0 + yc + 5.6), (x - 6.3, Y0 + yc + 4.8), (x - 4.2, Y0 + yc + 4.8),
                  (x - 1.0, Y0 + yc + 5.6), (x - 1.0, Y0 + yc + 3.6), (x - 4.2, Y0 + yc + 4.4),
                  (x - 6.3, Y0 + yc + 4.4), (x - 9.5, Y0 + yc + 3.6)], KL, D, True)  # kelebek kol
        _r(msp, x - 5.8, Y0 + yc + 5.6, x - 5.0, Y0 + yc + 6.2, KL, D)
    # hava pürjörleri: gidiş sol üst, dönüş sağ alt
    for px, py in ((xs + 2.4, 52.0), (X(90.0), 19.4)):
        msp.add_circle((px, Y0 + py), 1.7, dxfattribs={'layer': KL, 'color': D})
        _pl(msp, [(px - 0.5, Y0 + py), (px, Y0 + py + 0.5), (px + 0.5, Y0 + py), (px, Y0 + py - 0.5)], KL, D, True)
        _r(msp, px - 0.35, Y0 + py - 3.0, px + 0.35, Y0 + py - 1.7, KL, D)
    for px, py in ((xs + 3.9, 58.6), (X(88.5), 26.0)):
        _r(msp, px - 1.2, Y0 + py, px + 1.2, Y0 + py + 0.6, KL, D)
        _pl(msp, [(px - 0.8, Y0 + py + 0.6), (px - 0.4, Y0 + py + 1.4), (px + 0.4, Y0 + py + 1.4),
                  (px + 0.8, Y0 + py + 0.6)], KL, D)
    return xs - 2.8 - 9.5                  # vana giriş ucu x (kombi hatları buraya bağlanır)


def kombi_kollektor(msp, Kx, Y0, n, toplamW, kombi_kw):
    """Kombi + kollektör + bağlantılar (kullanıcının *U127 düzeni): kombi (−84,4…−34,4; 120…220), gidiş kombinin
    sağ bağlantısından (−44,4) iner ve üst bara girer; dönüş sol bağlantıdan (−74,4) iner, alt bara girer ve
    kombi altından doldurma/boşaltma küresel vanasına (y 10) devam eder — vana yalnız dönüşte."""
    C = 'ROTAS-ISITMA-CIHAZ'
    _r(msp, Kx - 84.4, Y0 + 120, Kx - 34.4, Y0 + 220, C, 2)
    _r(msp, Kx - 82.4, Y0 + 125, Kx - 36.4, Y0 + 135, C, 2)
    for x, r in ((-80.0, 1.8), (-65.0, 1.8), (-60.0, 1.8), (-55.0, 1.8), (-44.0, 2.6)):
        msp.add_circle((Kx + x, Y0 + 130), r, dxfattribs={'layer': C, 'color': 2})
    for dy in (-1.4, 0.0, 1.4):
        msp.add_circle((Kx - 76.4, Y0 + 130 + dy), 0.5, dxfattribs={'layer': C, 'color': 2})
    _t(msp, 'H. KOMBİ %dKW' % kombi_kw, (Kx + 33, Y0 + 195), 20, 4, C)
    x_giris = kollektor(msp, Kx, Y0, n)
    _pl(msp, [(Kx - 44.4, Y0 + 120), (Kx - 44.4, Y0 + 56.45), (x_giris, Y0 + 56.45)], G)
    _pl(msp, [(Kx - 74.4, Y0 + 120), (Kx - 74.4, Y0 + 23.85), (x_giris, Y0 + 23.85)], DN)
    _pl(msp, [(Kx - 74.4, Y0 + 23.85), (Kx - 74.4, Y0 + 15.0)], DN)
    # dönüşte küresel vana (dikey, 90°): iki üçgen + kol
    x, y = Kx - 74.4, Y0 + 10.0
    _pl(msp, [(x - 2.5, y + 5), (x + 2.5, y + 5), (x - 2.5, y - 5), (x + 2.5, y - 5)], 'ROTAS-ISITMA-CIHAZ', 1, True)
    _pl(msp, [(x, y), (x + 3.2, y), (x + 3.2, y + 4.0)], 'ROTAS-ISITMA-CIHAZ', 1)
    # kollektör toplamı (kullanıcı: dolabın sol üstünde, kısa kılavuzla)
    xl = Kx + 85 - 10 * (n - 1) - 12.4 - 17.3
    _t(msp, '%.1fW-%%%%C32' % toplamW, (xl + 35, Y0 + 75), 10, 41, CAP)
    _pl(msp, [(xl + 25, Y0 + 70.5), (xl + 25, Y0 + 79), (xl + 32, Y0 + 79)], CAP, 41)


def daire_balonu(msp, x, y, ad):
    msp.add_circle((x, y), 55, dxfattribs={'layer': 'ROTAS-ISITMA-DAIRE-NO', 'color': 6})
    msp.add_circle((x, y), 49, dxfattribs={'layer': 'ROTAS-ISITMA-DAIRE-NO', 'color': 7})
    _t(msp, ad, (x, y), 40, 6, 'ROTAS-ISITMA-DAIRE-NO', TA.MIDDLE_CENTER, gen=0.8)


def ciz(doc, msp, model):
    panel_blogu(doc)
    katlar = model['katlar']
    # bant genişliği: en geniş kat
    gen = []
    for kat in katlar:
        ds = sorted(kat['daireler'].values(), key=lambda d: -int(d['no'][1:]))
        ns = [sum(len(m['devreler']) for m in d['mahaller']) for d in ds]
        gen.append(sum(daire_genislik(k) for k in ns[:-1]) + son_daire_genislik(ns[-1]))
    ic_w = max(gen) + K_OFS
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
                # kullanıcının şeması: gidiş Px−5'ten (57,5) iner, dönüş Px'ten (22,5) iner
                _pl(msp, [(Px - 5, Y0 + 57.5), (Px - 5, yg), (Kx + 85 - 10 * i, yg), (Kx + 85 - 10 * i, Y0 + 19.6)], G)
                _pl(msp, [(Px, Y0 + 22.5), (Px, yd), (Kx + 80 - 10 * i, yd), (Kx + 80 - 10 * i, Y0 + 19.6)], DN)
                hat_etiketi(msp, Px, yg, c['W'])
                toplam_sema.append((kat['kat'], dd['no'], c['no'], c['W'], c['L_m']))
            Kx += daire_genislik(n)
    # başlık, lejant, notlar
    # kullanıcının şema paftasında bantların üstü boş: başlık, lejant ve notlar bantların ALTINDAKİ şeritte
    # (döşeme altı hatların en altı ≈ BANT0 − 120)
    _t(msp, 'YERDEN ISITMA KOLON ŞEMASI', (X1 - 900, PY0 + 120), 40, 7, 'ROTAS-PAFTA-BASLIK', TA.MIDDLE_CENTER, gen=0.8)
    lejant(msp, X0 + 200, BANT0 - 260)
    notlar(msp, X0 + 2300, BANT0 - 260, model)
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
        '3- Oda / salon / mutfak 20°C, antre-koridor 15°C, banyo 24°C. Balkon, yüklük, wc-lavabo, duş ve 2,7 m²',
        '   altındaki wc-duş, merdiven, asansör ve ortak alanlar ısıtılmaz; mutfak tezgâhı, buzdolabı, klozet, lavabo ve',
        '   duş teknesi altına boru döşenmez.',
        '4- Devre ısıl gücü = 35 W/m × hat uzunluğu (plan etiketi, kolon şeması ve hesap tablosunda aynı esas).',
        '5- Kollektör ve kombi bağlantıları kolon şemasında gösterilmiştir; kollektör yeri uygulamada daire holünde seçilir.',
    ]
    yy = y - 45
    for q in s:
        _t(msp, q, (x, yy), 12, 7, L)
        yy -= 25
