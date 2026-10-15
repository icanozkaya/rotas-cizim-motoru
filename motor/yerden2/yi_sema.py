"""yerden2 — YERDEN ISITMA KOLON ŞEMASI (saf geometri, kullanıcının şeması: YERDEN_ISITMA_ALTIN_REFERANS §5, S-1..S-6).

Kat bantları 400 cm (aşağıdan yukarı zemin, 1, 2), sol 50 cm sütunda dikey kırmızı kat adı; her dairede kombi +
kollektör, "H. KOMBİ 24KW", daire balonu, devre panelleri 200 cm adımla (devre no büyükten küçüğe), döşeme altında
kademeli gidiş (kırmızı sürekli) / dönüş (turuncu çizgi-nokta) hatları, "NNNN.NW-Ø20" hat etiketleri, kollektör toplamı
"ΣW-Ø32". Değerler plan etiketleriyle aynı (model json).
"""

import os
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yi_bloklar as YB  # noqa: E402

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


PANEL_BLOK = YB.PANEL


def panel_blogu(doc):
    """kullanıcının bloklarından çıkarılmış ROTAS-YI- blokları (yi_bloklar.py, kutuphane/yerden/ROTAS_YI_BLOKLAR.dxf)"""
    YB.hazirla(doc)


def panel(msp, Px, Y0, d):
    """Döşeme kesiti devre paneli = kullanıcının *U108 bloğunun birebir saf geometri kopyası ROTAS-YI-DEVRE-PANELI
    (yi_bloklar.py); öznitelikler kullanıcının yerinde/boyunda/renginde: NO Zxx h15, DERECE h10, YER "W", UZ "m",
    ISIKAYBI, NO1 devre no, BORU "PEX BORU, 16 x 2.0". Kullanıcının bloğunda olmayan yazı yok."""
    YB.yerlestir(msp, PANEL_BLOK, (Px, Y0), DET, {
        'NO': d['zon'], 'DERECE': '%d%%%%DC' % d['sic'], 'YER': '%.1f W' % d['W'], 'UZ': '%.2f m' % d['L_m'],
        'ISIKAYBI': 'ISIKAYBI', 'NO1': str(d['no']), 'BORU': 'PEX BORU, 16 x 2.0', 'MAHAL': ''})


def hat_etiketi(msp, Px, yg, W):
    """kullanıcının *U110 bloğu (ROTAS-YI-HAT-ETIKETI): kılavuz ucu (Px−15, yg), yazı kılavuzun solunda h10 renk 41"""
    YB.yerlestir(msp, YB.HAT_ET, (Px - 15.0, yg), CAP, {'CAP': '%.1fW-%%%%C20' % W})


def kombi_kollektor(msp, Kx, Y0, n, toplamW, kombi_kw):
    """Kombi + kollektör = kullanıcının *U127 bloğu birebir (ROTAS-YI-KOMBI-KOLLEKTOR; n ≠ 9 ağızda STRETCH:
    yi_bloklar.kombi_kollektor_blogu). Gidiş ağzı i: Kx+85−10i, dönüş: Kx+80−10i (i = 0 en sağ). Kollektör toplamı
    kullanıcının *U111 bloğu (Kx, Y0+70), dolabın sol kenarıyla birlikte kayar."""
    ad = YB.kombi_kollektor_blogu(msp.doc, n)
    YB.yerlestir(msp, ad, (Kx, Y0), 'ROTAS-ISITMA-KOLLEKTOR', {'KOMBI': 'H. KOMBİ %dKW' % kombi_kw})
    YB.yerlestir(msp, YB.KOL_ET, (Kx + max(0.0, 10.0 * (9 - n)), Y0 + 70.0), CAP,
                 {'CAP': '%.1fW-%%%%C32' % toplamW})


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
    _t(msp, 'DEVRE ETİKETİ (hat uzunluğu, boru aralığı, ısıl güç, devre no)', (x + 170, yy - 30), 12, 7, L)
    yy -= 130
    msp.add_blockref('ROTAS-YI-MAHAL', (x + 40, yy), dxfattribs={'layer': 'ROTAS-ISITMA-MAHAL-ETIKET'}).add_auto_attribs(
        {'DERECE': '20%%DC', 'NO': 'Z01'})
    _t(msp, 'MAHAL ETİKETİ (iç sıcaklık / zon no: zemin Z01.., 1. kat 101.., 2. kat 201..)', (x + 170, yy - 5), 12, 7, L)


def notlar(msp, x, y, model):
    L = 'ROTAS-NOT'
    _t(msp, 'NOTLAR', (x, y), 25, 7, L, gen=0.8)
    import os as _os
    _hy, _ik = _os.environ.get('YI_HOL_YOK'), _os.environ.get('YI_ISI_KAYBI')
    s = [
        '1- Yerden ısıtma borusu PEX 16 x 2,0 (oksijen bariyerli), boru aralığı 15 cm, kenar mesafesi 7,5 cm.',
        '2- Her devre tek parça boru (ek yok), devre boyu en çok 80 m; 14 m² ve üstü mahaller 2 devre.',
        ('3- Oda / salon / mutfak 20°C, banyo 24°C. Antre-koridor (hol) yerden ısıtılmaz. Balkon, yüklük, wc-lavabo, duş ve 2,7 m²'
         if _hy else '3- Oda / salon / mutfak 20°C, antre-koridor 15°C, banyo 24°C. Balkon, yüklük, wc-lavabo, duş ve 2,7 m²'),
        '   altındaki wc-duş, merdiven, asansör ve ortak alanlar ısıtılmaz; mutfak tezgâhı, buzdolabı, klozet, lavabo ve',
        '   duş teknesi altına boru döşenmez.',
        ('4- Devre ısıl gücü = mahal ısı kaybı × devre boyu / mahal boru boyu (ısı kaybı hesabı, kat yüksekliği 3,00 m).'
         if _ik else '4- Devre ısıl gücü = 35 W/m × hat uzunluğu (plan etiketi, kolon şeması ve hesap tablosunda aynı esas).'),
        '5- Kollektörler daire holünde (dolap); kombi–kollektör gidiş/dönüş hattı ve devre ayakları planda, ağız sırası şemada.',
    ]
    yy = y - 45
    for q in s:
        _t(msp, q, (x, yy), 12, 7, L)
        yy -= 25
