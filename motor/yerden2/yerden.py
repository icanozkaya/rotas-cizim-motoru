#!/usr/bin/env python3
"""yerden2 — YERDEN ISITMA KAT PLANLARI (zemin, 1, 2) + KOLON ŞEMASI + hesap Excel'i, new_block mimarisinden.

    python3 motor/yerden2/yerden.py [--png] [--ayaklar] [--yenile]

Çıktı (proje/denemeler/yerden2/):
  NB_YERDEN_ISITMA.dxf    AC1032, cm; kat planları kaynak koordinatında (mimari ROTAS-MIMARI*), sağda kolon şeması
  NB_YERDEN_ISITMA.xlsx   sablon/ornek_yi.xlsx kopyası (formüller korunur), girdiler bu projeden
  NB_YERDEN_ISITMA_model.json  devre/mahal verisi (şema, Excel, kontrol bunu okur)
  onizleme/*.png          (--png) kat planları ve şema önizlemesi + referansla yan yana

Tarz: kullanıcının kendi çizimi (kutuphane/arastirma/YERDEN_ISITMA_ALTIN_REFERANS.md §7) + README yerden ısıtma kuralları.
Kararlar ve farklar: BENIOKU.md.
"""
import argparse
import json
import math
import os
import sys
import time

import ezdxf
from ezdxf.addons import Importer
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import mimari_yi as MY  # noqa: E402
import serpantin as S  # noqa: E402
import tasarim as T  # noqa: E402

KOK = MY.KOK
sys.path.insert(0, KOK + '/motor/deneme/denetim')
import denetle as D  # noqa: E402

M = MY.M2.M
if sys.path[0] != BURASI:
    sys.path.insert(0, BURASI)
CIKIS = KOK + '/proje/denemeler/yerden2'
CIKIS_DXF = CIKIS + '/NB_YERDEN_ISITMA.dxf'
CIKIS_JSON = CIKIS + '/NB_YERDEN_ISITMA_model.json'
MIMARI_DXF = M.MIMARI

KATLAR = ['Z', '1', '2']
KAT_ADI = {'Z': 'ZEMİN KAT', '1': '1. KAT', '2': '2. KAT'}
ZON_ONEK = {'Z': 'Z', '1': '1', '2': '2'}
W_M = 35.0                 # W/m (kullanıcının etiket davranışı: Kcal/h satırı = 35 W/m × hat uzunluğu)
YAZI_H = 10.0
GEN = 0.65                 # yazı genişlik çarpanı (MTYCAPLT referansı)

L_PEX = 'ROTAS-ISITMA-PEX'
L_ET = 'ROTAS-ISITMA-ETIKET'
L_MAH = 'ROTAS-ISITMA-MAHAL-ETIKET'
L_MASK = 'ROTAS-ISITMA-MASKE'
KATMAN = {  # ad: (renk, çizgi tipi, kalınlık)
    L_PEX: (1, 'Continuous', 30),
    L_ET: (2, 'Continuous', -3),
    L_MAH: (2, 'Continuous', -3),
    L_MASK: (7, 'Continuous', -3),
    'ROTAS-MIMARI': (8, 'Continuous', -3),
    'ROTAS-MIMARI-YAZI': (8, 'Continuous', -3),
    'ROTAS-PAFTA': (7, 'Continuous', 50),
    'ROTAS-PAFTA-BASLIK': (7, 'Continuous', -3),
    'ROTAS-LEJANT': (7, 'Continuous', -3),
    'ROTAS-NOT': (7, 'Continuous', -3),
    'ROTAS-ISITMA-GIDIS-BORU': (10, 'Continuous', -3),
    'ROTAS-ISITMA-DONUS-BORU': (30, 'ROTAS_ISITMA_DONUS', -3),
    'ROTAS-ISITMA-CAP': (41, 'Continuous', -3),
    'ROTAS-ISITMA-CIHAZ': (2, 'Continuous', -3),
    'ROTAS-ISITMA-KOLLEKTOR': (1, 'Continuous', -3),
    'ROTAS-ISITMA-SEMA-DETAY': (7, 'Continuous', -3),
    'ROTAS-ISITMA-DAIRE-NO': (6, 'Continuous', -3),
    'ROTAS-SEMA-KAT-BANDI': (7, 'Continuous', -3),
    'ROTAS-SEMA-KAT-YAZI': (1, 'Continuous', -3),
}


def log(*a):
    print('[yerden2]', *a, flush=True)


# ====================================================================== DXF hazırlık
def belge():
    doc = ezdxf.new('R2018', setup=False)
    doc.header['$INSUNITS'] = 5
    doc.header['$LTSCALE'] = 1.0
    doc.header['$MEASUREMENT'] = 1
    if 'Continuous' not in doc.linetypes:
        doc.linetypes.add('Continuous', pattern=[0.0], description='Solid')
    doc.linetypes.add('ROTAS_ISITMA_DONUS', pattern=[40.0, 30.0, -5.0, 0.0, -5.0],
                      description='ISITMA DONUS ----- . -----')
    for ad, (renk, lt, lw) in KATMAN.items():
        doc.layers.add(ad, color=renk, linetype=lt, lineweight=lw)
    doc.styles.add('ROTAS-YAZI', font='arial.ttf')
    try:
        doc.set_wipeout_variables(frame=0)
    except Exception:
        pass
    bloklar(doc)
    return doc


def _yazi(blk, metin, p, h, renk, hizala=None, katman=None):
    da = {'height': h, 'style': 'ROTAS-YAZI', 'width': GEN, 'color': renk}
    if katman:
        da['layer'] = katman
    t = blk.add_text(metin, dxfattribs=da)
    if hizala is None:
        t.dxf.insert = p
    else:
        t.set_placement(p, align=hizala)
    return t


def _attdef(blk, tag, p, h, renk, hizala, gizli=False):
    a = blk.add_attdef(tag, p, dxfattribs={'height': h, 'style': 'ROTAS-YAZI', 'width': GEN, 'color': renk})
    a.set_placement(p, align=hizala)
    if gizli:
        a.is_invisible = True
    return a


def yuvarlak_dikd(a, b, r):
    t = math.tan(math.radians(22.5))
    return [(-a + r, -b, 0), (a - r, -b, t), (a, -b + r, 0), (a, b - r, t), (a - r, b, 0), (-a + r, b, t),
            (-a, b - r, 0), (-a, -b + r, t)]


def bloklar(doc):
    TA = ezdxf.enums.TextEntityAlignment
    # devre etiketi: 150 × 80 sarı tablo, 4 satır × 20; ekleme noktası = sol üst köşe
    b = doc.blocks.new('ROTAS-YI-ETIKET')
    da = {'color': 2}
    b.add_lwpolyline([(0, 0), (150, 0), (150, -80), (0, -80)], close=True, dxfattribs=da)
    for y in (-20, -40, -60):
        b.add_line((0, y), (150, y), dxfattribs=da)
    b.add_line((96.9, 0), (96.9, -80), dxfattribs=da)
    for i, s in enumerate(('Hat uzunluğu:', 'Modülasyon Aralığı:', 'Kcal/h:', 'Isıtma Devresi-No.:')):
        _yazi(b, s, (5, -15 - 20 * i), YAZI_H, 2)
    for i, tag in enumerate(('UZ', 'AR', 'YER', 'NO1')):
        _attdef(b, tag, (146, -15 - 20 * i), YAZI_H, 2, TA.BOTTOM_RIGHT)
    for tag in ('MAHAL', 'NO', 'DERECE', 'ALAN', 'BORU'):
        _attdef(b, tag, (5, -95), 5, 2, TA.LEFT, gizli=True)
    # mahal etiketi: yuvarlatılmış kutu 68,4 × 48,9 + 3 halka (sarı-cyan-cyan-sarı), orta şerit
    b = doc.blocks.new('ROTAS-YI-MAHAL')
    for k, renk in enumerate((2, 4, 4, 2)):
        d = 0.5 * k
        pts = yuvarlak_dikd(34.21 + d, 24.44 + d, 6.0 + d)
        b.add_lwpolyline(pts, format='xyb', close=True, dxfattribs={'color': renk})
    h = b.add_hatch(color=2)
    h.paths.add_polyline_path([(-28.2, -0.75), (28.2, -0.75), (28.2, 0.75), (-28.2, 0.75)], is_closed=True)
    b.add_lwpolyline([(-28.2, -0.75), (28.2, -0.75), (28.2, 0.75), (-28.2, 0.75)], close=True, dxfattribs={'color': 2})
    _attdef(b, 'DERECE', (0, 12.5), 12.0, 4, TA.MIDDLE_CENTER)
    _attdef(b, 'NO', (0, -12.5), 12.0, 1, TA.MIDDLE_CENTER)
    _attdef(b, 'MAHAL', (0, -30), 5, 2, TA.MIDDLE_CENTER, gizli=True)
    _attdef(b, 'ALAN', (0, -30), 5, 2, TA.MIDDLE_CENTER, gizli=True)


def ekle(msp, ad, p, katman, attr, olcek=1.0, dondur=0):
    e = msp.add_blockref(ad, p, dxfattribs={'layer': katman, 'xscale': olcek, 'yscale': olcek, 'rotation': dondur})
    e.add_auto_attribs(attr)
    return e


# ====================================================================== mimari altlık
def mimari_kopyala(doc):
    t0 = time.time()
    if not os.path.exists(MIMARI_DXF):
        M.extract()
    src = ezdxf.readfile(MIMARI_DXF)
    msp = doc.modelspace()
    pen = [M.win(k, 120.0) for k in KATLAR]
    sec = []
    for e in src.modelspace():
        if e.dxf.layer != 'MKDU0' or e.dxftype() == 'INSERT':
            continue
        try:
            if e.dxftype() in ('TEXT', 'MTEXT'):
                p = e.dxf.insert
                xs, ys = [p[0]], [p[1]]
                tx = (e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()).upper()
                if 'PLANI' in tx and ('ÖLÇEK' in tx or 'OLCEK' in tx):
                    continue
            elif e.dxftype() == 'LINE':
                xs, ys = [e.dxf.start[0], e.dxf.end[0]], [e.dxf.start[1], e.dxf.end[1]]
            elif e.dxftype() in ('CIRCLE', 'ARC'):
                c = e.dxf.center
                xs, ys = [c[0]], [c[1]]
            elif e.dxftype() == 'LWPOLYLINE':
                ps = list(e.get_points('xy'))
                xs, ys = [q[0] for q in ps], [q[1] for q in ps]
            elif e.dxftype() in ('HATCH', 'ELLIPSE', 'SPLINE', 'POLYLINE', 'SOLID', 'DIMENSION'):
                try:
                    bb = ezdxf.bbox.extents([e])
                    xs, ys = [bb.extmin[0], bb.extmax[0]], [bb.extmin[1], bb.extmax[1]]
                except Exception:
                    continue
            else:
                continue
        except Exception:
            continue
        if any(w[0] < min(xs) and max(xs) < w[2] and w[1] < min(ys) and max(ys) < w[3] for w in pen):
            sec.append(e)
    n0 = len(msp)
    imp = Importer(src, doc)
    imp.import_entities(sec, target_layout=msp)
    imp.finalize()
    yeni = list(msp)[n0:]
    kutular = []
    for e in yeni:
        if e.dxftype() in ('TEXT', 'MTEXT'):
            e.dxf.layer = 'ROTAS-MIMARI-YAZI'
            # denetle.py / kontrolörle ORTAK ölçü (kutu.yazi_kutusu: MTEXT satır satır gerçek genişlik, sütun
            # genişliği değil — "asansör boşluğu" 97,5 cm, eskiden 237,6 cm ve wc+banyonun içine 64 cm giriyordu)
            pg = D.yazi_poligonu(e)
            if pg is not None and pg.is_valid and not pg.is_empty:
                kutular.append(pg)
        else:
            e.dxf.layer = 'ROTAS-MIMARI'
        e.dxf.color = 256
    if 'MKDU0' in doc.layers:
        try:
            doc.layers.remove('MKDU0')
        except Exception:
            pass
    log('mimari altlık: %d varlık, %d yazı kutusu (%.1f s)' % (len(yeni), len(kutular), time.time() - t0))
    return kutular


# ====================================================================== tasarım
TUR_SIRA = {'mutfak': 0, 'oda': 1, 'hol': 2, 'banyo': 3}


def kat_tasarla(k, yazi_kutulari, yasak_ek, cep_ac=True):
    K = MY.kat_oku(k)
    MY.yabanci_etiket_bol(K)
    w = M.win(k, 120.0)
    yaz = [q for q in yazi_kutulari if w[0] < q.centroid.x < w[2] and w[1] < q.centroid.y < w[3]]
    yasak = unary_union([q.buffer(3) for q in yaz] + yasak_ek) if (yaz or yasak_ek) else Polygon()
    odalar = []
    isitmasiz = []
    for r in K.rooms:
        ok, sic, tur = MY.isitma_sinifi(r)
        if not ok:
            isitmasiz.append(dict(ad=r['name'], poly=r['poly'], tur=tur))
            continue
        if tur == 'banyo':
            Pg = MY.islak_genislet(K, r)
            if Pg is not r['poly']:
                r = dict(r, poly=Pg)
        eng = MY.engeller(K, r, islak=(tur == 'banyo'))
        H, R = MY.bolge(r, eng)
        kapi = MY.ana_kapi(K, r, tur)
        d = T.oda_tasarla(r, H, R, kapi, yasak, cep_ac, islak=(tur == 'banyo'))
        if tur == 'banyo':
            H, R, d = islak_doldur(r, eng, kapi, yasak, cep_ac, (H, R, d), mimari_m2(K, r))
        if d is None:
            log('UYARI: %s kat %s daire %s %s (%.2f m²): devre kurulamadı' % (k, r['name'], r['daire'], tur, r['area']))
            isitmasiz.append(dict(ad=r['name'], poly=r['poly'], tur='kurulamadi'))
            continue
        for c in d['devreler']:
            if c['cep'] is not None:
                yasak = yasak.union(c['cep'].buffer(5))
        am = mimari_m2(K, r)
        odalar.append(dict(ad=r['name'].replace('\n', ' '), daire=r['daire'], tur=tur, sic=sic, alan=round(r['area'], 2),
                           alan_mimari=am, r=r,
                           esik=(ISLAK_ORAN * (am or r['area']) + ISLAK_PAYI) * 100.0 if tur == 'banyo' else None,
                           poly=r['poly'], H=H, eng=eng, xy=r['xy'], kapi=kapi, tasarim=d))
    # 15.10 (D): planda kollektör + kombi + devre ayakları (ayak.py); serpantinler gerekirse yeniden kurulur
    kol = ayaklari_kur(k, K, odalar, yasak) if AYAKLAR else {}
    # numaralama: daire sırası, tür sırası, konum (yukarıdan aşağı, soldan sağa)
    odalar.sort(key=lambda o: (o['daire'], TUR_SIRA[o['tur']], -round(o['xy'][1] / 50), o['xy'][0]))
    devre_no = 0
    for i, o in enumerate(odalar):
        o['zon'] = ('Z%02d' % (i + 1)) if k == 'Z' else ('%s%02d' % (ZON_ONEK[k], i + 1))
        # bant 0 = uca en yakın devre -> önce numaralanır
        for c in o['tasarim']['devreler']:
            devre_no += 1
            c['no'] = devre_no
            c['L_m'] = round(c['L'] / 100.0, 2)
            c['W'] = round(W_M * c['L_m'], 1)
    return dict(kat=k, K=K, odalar=odalar, isitmasiz=isitmasiz, yasak=yasak, yazi=yaz, kollektorler=kol,
                yazi_u=unary_union(yaz) if yaz else Polygon())


AYAKLAR = True             # 15.10 (D): planda kollektör bağlantıları zorunlu


def tam_devre(c):
    """kollektör ağzı -> gidiş ayağı -> serpantin -> dönüş ayağı -> ağız: tek açık polyline (xyb)"""
    if not c.get('ayak_g'):
        return list(c['pts'])
    g, d = c['ayak_g'], c['ayak_d']
    serp = [tuple(p) for p in c['pts']]
    serp[-1] = (serp[-1][0], serp[-1][1], 0.0)
    return [(x, y, 0.0) for x, y in reversed(g[1:])] + serp + [(x, y, 0.0) for x, y in d[1:]]


def ayaklari_kur(k, K, odalar, yasak):
    """daire başına kollektör yeri, kombi hattı, ayaklar; devre boyu > 80 m ise mahal bir fazla devreye bölünüp
    daire yeniden çözülür (en çok 3 tur)"""
    import ayak as A
    kat_off = {KATLAR.index(kk): getattr(MY.kat_oku(kk), 'off', 0.0) for kk in KATLAR}
    kombiler = A.kombi_yerleri(kat_off)
    out = {}
    for dno in sorted({o['daire'] for o in odalar}):
        od = [o for o in odalar if o['daire'] == dno]
        hol = next((o for o in od if o['tur'] == 'hol'), None)
        if hol is None:
            log('UYARI: kat %s D%d: hol yok, ayak çizilmedi' % (k, dno))
            continue
        kb = kombiler.get(dno)
        import copy
        yedek = {id(o): (o['H'], copy.deepcopy(o['tasarim']), o.get('ek_eng'), o.get('ayak_sira')) for o in od}

        def geri_yukle():
            for o in od:
                o['H'], o['tasarim'], o['ek_eng'], o['ayak_sira'] = (yedek[id(o)][0], copy.deepcopy(yedek[id(o)][1]),
                                                                     yedek[id(o)][2], yedek[id(o)][3])
        en = None
        for ks, sh, kombili in ((0, True, True), (0, False, True), (1, True, True), (2, True, True), (0, True, False)):
            # kollektör yeri / sahte hol ucu adayları; son çare kombi hattı sonra (devreler önce)
            geri_yukle()
            n_ek = {}
            for tur in range(3):
                D_ = A.Daire(K, dno, od, hol, kb if kombili else None, None, yasak, kol_sira=ks, sahte_hol=sh)
                sonuc = D_.coz()
                if sonuc is None:
                    break
                for a in sonuc['ayaklar']:
                    a['c']['ayak_g'] = a['g'][0]
                    a['c']['ayak_d'] = a['d'][0]
                    a['c']['agiz'] = (a['g'][1], a['d'][1])
                    a['c']['L_serp'] = S.uzunluk(a['c']['pts'])
                    a['c']['L'] = S.uzunluk(tam_devre(a['c']))
                asan = [o for o in od if any(c['L'] > A.MAX_L for c in o['tasarim']['devreler'])]
                if not asan:
                    break
                for o in asan:
                    n_ek[id(o)] = len(o['tasarim']['devreler']) + 1
                    log('kat %s %s: ayaklarla devre > 80 m -> %d devre' % (k, o['ad'], n_ek[id(o)]))
                    y = A.yeniden_kur(o, o.get('ek_eng'), o['kapi'], yasak, kapi_zorla=True, n_min=n_ek[id(o)])
                    if y is not None:
                        o['H'], o['tasarim'] = y['H'], y['tasarim']
            n_tum = sum(len(o['tasarim']['devreler']) for o in od)
            n_bag = sum(1 for o in od for c in o['tasarim']['devreler'] if c.get('ayak_g'))
            kombi_ok = sonuc is not None and (kb is None or sonuc.get('kombi_hat'))
            if sonuc is not None and not kombili and kb is not None:
                D_.uyari.append('D%d: kombi–kollektör hattı devre ayaklarıyla kesişmeden çizilemedi (planda kombi yeri '
                                'işaretli, hat yok)' % dno)
            hol_ok = bool(hol['tasarim']['devreler'])
            puan = ((n_bag - n_tum) * 10 + (0 if kombi_ok else -5) + (0 if hol_ok else -3)) if sonuc is not None else -999
            if en is None or puan > en[0]:
                en = (puan, ks, copy.deepcopy([(o['H'], o['tasarim'], o.get('ek_eng')) for o in od]), sonuc,
                      list(D_.uyari))
            if puan == 0:
                break
            log('kat %s D%d: kollektör adayı %d eksik (%d/%d), sonraki aday' % (k, dno, ks, n_bag, n_tum))
        puan, ks, tas, sonuc, uyari = en
        for o, (H_, t_, e_) in zip(od, tas):
            o['H'], o['tasarim'], o['ek_eng'] = H_, t_, e_
        for u in uyari:
            log('UYARI: kat %s %s' % (k, u))
        out[dno] = sonuc
        n = sum(len(o['tasarim']['devreler']) for o in od)
        na = sum(1 for o in od for c in o['tasarim']['devreler'] if c.get('ayak_g'))
        log('kat %s D%d: kollektör %d ağız, ayaklı devre %d/%d' % (k, dno, n, na, n))
    return out


ISLAK_ORAN = 3.0           # m/m² (mimari m²) — ıslak hacim doluluğu (kontrolör Y02)
ISLAK_KENARLAR = (7.5, 6.0, 5.0, 4.0, 3.0, 2.5)
ISLAK_PAYI = 0.2           # m — eşik payı (tur 4: mahal poligonu kontrolörünkiyle aynı; klozet çentiği geri katıldı)


def _mahal_ici(d, P):
    if d is None:
        return 0.0
    Pb = P.buffer(5)
    return sum(S.cizgi(c['pts']).intersection(Pb).length for c in d['devreler']) / 100.0


def islak_doldur(r, eng, kapi, yasak, cep_ac, ilk, am):
    """Tur 3 Y-2: ıslak hacimde mahal içi boru ≥ 3,0 m/m² (mimari m²). Klozet, lavabo, duş teknesi/küvet ve Ç.M. altı
    boş kalır. Duvar payı 7,5 ile eşik tutmazsa 6,0 / 5,0 cm denenir (yalnız ıslak hacim; kuru mahaller 7,5).
    En çok mahal içi boru veren düzen seçilir; eşiği geçen ilk (en büyük paylı) düzen yeterlidir."""
    H, R, d = ilk
    esik = ISLAK_ORAN * (am or r['area'])
    en = (_mahal_ici(d, r['poly']), H, R, d)
    if en[0] >= esik + ISLAK_PAYI:
        return H, R, d
    for kn in ISLAK_KENARLAR[1:]:
        H2, R2 = MY.bolge(r, eng, kenar=kn)
        d2 = T.oda_tasarla(r, H2, R2, kapi, yasak, cep_ac, islak=True)
        L2 = _mahal_ici(d2, r['poly'])
        if d2 is not None and L2 > en[0] + 0.05:
            en = (L2, H2, R2, d2)
        if en[0] >= esik + ISLAK_PAYI:
            break
    return en[1], en[2], en[3]


def mimari_cizgi(K):
    gs = []
    for a in K.R:
        g = MY._geom(a)
        if g is not None and not g.is_empty:
            gs.append(g)
    return unary_union(gs)


def mimari_m2(K, r):
    """mimarın m² yazısı (mahal adının altındaki '15.44m²'): mahal içinde, ada en yakın"""
    import re
    best = None
    for p, s, h, rot, c in K.yazilar:
        m = re.match(r'^\s*(\d+[.,]\d+)\s*m', s or '')
        if not m:
            continue
        q = c if c else p
        if not r['poly'].buffer(25).contains(Point(q)):
            continue
        d = math.hypot(q[0] - r['xy'][0], q[1] - r['xy'][1])
        if best is None or d < best[0]:
            best = (d, float(m.group(1).replace(',', '.')))
    return best[1] if best and best[0] < 150 else None


# ====================================================================== etiket yerleşimi
def _aralik(a, b, s):
    out = []
    x = a
    while x <= b + 1e-6:
        out.append(x)
        x += s
    return out or [(a + b) / 2]


def deger_sutunu(q, k=1.0):
    """devre etiketi kutusunun (150×80·k, dönüşsüz) değer sütunu: ATTRIB yazıları (UZ, AR, YER, NO1) bu bölgede.
    denetle.py yazı çakışmasını yalnız ATTRIB/TEXT kutularıyla ölçer; bloğun kendi sabit yazıları sayılmaz."""
    x0, y0, x1, y1 = q.bounds
    return box(x0 + 98 * k, y0 + 1, x1 - 1, y1 - 1)


def mahal_yazilari(q, k=1.0):
    """mahal etiketi (74×54·k) ATTRIB yazılarının (DERECE, NO; h 12, ortalı) bölgesi"""
    c = q.centroid
    return unary_union([box(c.x - 24 * k, c.y + (12.5 - 8) * k, c.x + 24 * k, c.y + (12.5 + 8) * k),
                        box(c.x - 24 * k, c.y - (12.5 + 8) * k, c.x + 24 * k, c.y - (12.5 - 8) * k)])


def yer_bul(boyutlar, anchor, kademeler, yasak, mimari=None, kendi=None, adim=10.0, sag_yasak=None, k=1.0,
            ic_kutu=None):
    """Etiket yeri: YALNIZ kendi mahalinin içinde (kılavuz çizgisi yok — R3/R4).
    boyutlar: [(w, h, dönüş)], kademeler: [(bölge, mimari_cizgi_yasak)] sırayla denenir.
    Puan: anchor'a uzaklık (+ kendi devresinin borusunu örtmüyorsa ceza). -> (dikdörtgen, dönüş) | (None, None)"""
    from shapely.prepared import prep
    py = prep(yasak) if yasak is not None and not yasak.is_empty else None
    pm = prep(mimari) if mimari is not None and not mimari.is_empty else None
    pk = prep(kendi) if kendi is not None and not kendi.is_empty else None
    ps = prep(sag_yasak) if sag_yasak is not None and not sag_yasak.is_empty else None
    ax, ay = anchor
    for bolge_, mim_yasak in kademeler:
        if bolge_ is None or bolge_.is_empty:
            continue
        pb = prep(bolge_)
        bx = bolge_.bounds
        best = None
        for w, h, rot in boyutlar:
            for cx in _aralik(bx[0] + w / 2, bx[2] - w / 2, adim):
                for cy in _aralik(bx[1] + h / 2, bx[3] - h / 2, adim):
                    sk = math.hypot(cx - ax, cy - ay) + (0 if rot == 0 else 60)
                    if best is not None and sk >= best[0]:
                        continue
                    q = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                    if pk is not None and not pk.intersects(q):
                        sk += 150
                        if best is not None and sk >= best[0]:
                            continue
                    if not pb.contains(q):
                        continue
                    if py is not None and py.intersects(q):
                        continue
                    if ps is not None and rot == 0 and ps.intersects((ic_kutu or deger_sutunu)(q, k)):
                        continue
                    if mim_yasak and pm is not None and pm.intersects(q):
                        continue
                    best = (sk, q, rot)
        if best is not None:
            return best[1], best[2]
    return None, None


def _oda_etiket_yerleri(o, yasak, mim, sira, yazi_u=None):
    """bir mahalin mahal + devre etiketi yerleri (çizmeden). sira: 'mahal_once' | 'devre_once'.
    -> (mahal_q | None, [(c, q, rot) ...], yasak, eksik_sayisi)"""
    P = o['poly']
    yasak0 = yasak
    Hn = o['H']                                   # mahal - vitrifiye/tefriş
    x, y = o['xy']
    mq = None
    dv = []
    eksik = 0

    def mahal(yasak):
        # Y-4: önce mimari çizgiye (vitrifiye, Ç.M., duvar) hiç değmeyen yer; sonra çizgi üstü (maske çizgiyi örtmez)
        # Ek (tur 4): çizgi üstü yerleşimde önce vitrifiye / Ç.M. / kapı kanadı engeline değmeyen yer (Z21: etiket
        # Ç.M. kutusu kenarına binmesin); kapı kanadı çizgisi kesik maskeyle görünür kalır
        eng_d = P.buffer(-3, join_style=2).difference(o['eng'].buffer(6, join_style=2)) if not o['eng'].is_empty \
            else P.buffer(-3, join_style=2)
        yu = yazi_u if yazi_u is not None and not yazi_u.is_empty else None
        for k, temiz in ((1.0, True), (0.9, True), (0.8, True), (1.0, 'eng'), (0.9, 'eng'), (0.8, 'eng'),
                         (1.0, 'yazi'), (0.9, 'yazi'), (0.8, 'yazi'), (1.0, False), (0.8, False), (0.7, False)):
            if temiz == 'yazi':
                # küçük ıslak hacim (kullanıcının Z07'si gibi): çerçeve mahal yazısının üstüne binebilir, yalnız
                # 24°C / Z21 yazıları mimari yazıya değmez; vitrifiye/Ç.M./kapı kanadından yine uzak
                if yu is None or o['tur'] != 'banyo':
                    continue
                q, _ = yer_bul([(74 * k, 54 * k, 0)], (x, y + 100), [(eng_d, False)],
                               yasak.difference(yu.buffer(3.5, join_style=2)), mim, adim=4.0,
                               sag_yasak=yu.buffer(1.0), k=k, ic_kutu=mahal_yazilari)
                if q is not None:
                    return q, k
                continue
            if temiz == 'eng':
                kad = [(Hn.buffer(-2, join_style=2).intersection(eng_d), False), (eng_d, False)]
            elif temiz:
                kad = [(Hn.buffer(-4, join_style=2), True)]
            else:
                kad = [(Hn.buffer(-2, join_style=2), False), (P.buffer(-3, join_style=2), False)]
            q, _ = yer_bul([(74 * k, 54 * k, 0)], (x, y + 100), kad, yasak, mim, adim=10.0 if k == 1 else 4.0)
            if q is not None:
                return q, k
        return None, 1.0

    def bant(c):
        """Y-3: devrenin kendi parmaklarının y aralığı (uzak devrenin köşeye inen ayakları hariç)"""
        ys = []
        pts = c['pts']
        for i in range(len(pts) - 1):
            (x1, y1, b), (x2, y2, _) = pts[i], pts[i + 1]
            if abs(b) < 1e-9 and abs(y1 - y2) < 0.01 and abs(x2 - x1) > 30:
                ys.append(y1)
        if not ys:
            return None
        return min(ys) - S.ADIM / 2.0, max(ys) + S.ADIM / 2.0

    def devre(c, yasak, hiza_x, hiza_k=1.0, sadece_hiza=False):
        g = S.cizgi(c['pts'])
        ux, uy = c['pts'][0][0], c['pts'][0][1]
        cok = len(o['tasarim']['devreler']) > 1
        bt = bant(c) if cok else None
        if bt is not None:
            bx0, _, bx1, _ = P.bounds
            bkut = box(bx0 - 5, bt[0], bx1 + 5, bt[1])
            gb = g.intersection(bkut)
            cc = (gb if not gb.is_empty else g).envelope.centroid
            anc = ((ux + 2 * cc.x) / 3 if hiza_x is None else hiza_x, cc.y)
        else:
            bkut = None
            cc = g.envelope.centroid
            anc = ((ux + 2 * cc.x) / 3, (uy + 2 * cc.y) / 3)

        def bolge(B):
            return B if bkut is None else B.intersection(bkut)
        # Y-4/Ek: tam boy (yazı h 10) önce; etiket kutusu hiçbir mimari çizgiye (küvet, duş teknesi, Ç.M., klozet,
        # duvar) değmeyen serbest zeminde ve (Y-3) kendi devresinin bandında. Olmazsa 0,9 / 0,85 temiz; sonra tam boy
        # çizgi üstü (maske çizgileri ve vitrifiyeyi açıkta bırakır, yalnız boruyu örter); en son küçük ölçek / 90°.
        sira = [(1.0, 0, True), (0.9, 0, True), (0.85, 0, True), (1.0, 0, False), (0.9, 0, False), (0.85, 0, False),
                (0.75, 0, True), (1.0, 90, True), (0.85, 90, True), (0.75, 0, False), (1.0, 90, False),
                (0.85, 90, False), (0.75, 90, False), (0.7, 0, False), (0.7, 90, False), (0.65, 0, False),
                (0.65, 90, False)]
        # Ek (tur 4): iki devreli mahalde ikinci etiket kullanıcının çizimindeki gibi birincinin x hizasında, alt alta
        # (aynı ölçek, dönüşsüz). Hizada kendi bandında yer yoksa eski arama.
        if hiza_x is not None and bkut is not None:
            for k, dn, temiz in [t for t in sira if t[1] == 0 and t[0] >= hiza_k - 1e-6]:
                w, h = S.ETIKET_W * k, S.ETIKET_H * k
                serit = box(hiza_x - w / 2 - 0.01, -1e9, hiza_x + w / 2 + 0.01, 1e9)
                Bh = bolge(Hn.buffer(1)).intersection(serit)
                Bp = bolge(P.buffer(-1, join_style=2)).intersection(serit)
                kad = [(Bh, True)] if temiz else [(Bh, False), (Bp, False)]
                q, rot = yer_bul([(w, h, 0)], anc, kad, yasak, mim, kendi=g, adim=5.0)
                if q is not None and abs(q.centroid.x - hiza_x) < 0.5:
                    return q, (rot, k)
            if sadece_hiza:
                return None, None
        def islak_tam():
            """E-1 (tur 4): küçük ıslak hacimde tam boy (×1,0) etiket kullanıcının çizimi gibi vitrifiye / Ç.M. /
            mahal yazısının üstüne binebilir (kesik maske: çizgi ve yazı görünür). Yalnız değer sütunu (ATTRIB)
            mimari yazıya değmez; tablo kutusu diğer etiketlerden yine ayrı."""
            y_et = yasak.difference(yazi_u.buffer(3.5, join_style=2))
            for kk in (1.0, 0.9, 0.85):
                # önce tablonun tamamı mimari yazıdan (mahal adı, m², mek. havl.) ayrı — kullanıcının Z07'si gibi tablo
                # vitrifiye / Ç.M. / duş teknesi üstünde (kesik maske, çizgiler görünür); olmazsa yalnız değer sütunu
                for y_, sy_ in ((yasak, None), (y_et, yazi_u.buffer(1.0))):
                    q, rot = yer_bul([(S.ETIKET_W * kk, S.ETIKET_H * kk, 0)], anc,
                                     [(P.buffer(-1, join_style=2), False)], y_, mim, kendi=g, adim=2.5,
                                     sag_yasak=sy_, k=kk)
                    if q is not None:
                        return q, (rot, kk)
            return None
        islak_denendi = not (o['tur'] == 'banyo' and yazi_u is not None and not yazi_u.is_empty)
        for bant_mi in ((True, False) if bkut is not None else (False,)):
            for k, dn, temiz in sira:
                if not islak_denendi and (k < 1 or dn):
                    islak_denendi = True
                    r_ = islak_tam()
                    if r_ is not None:
                        return r_
                w, h = S.ETIKET_W * k, S.ETIKET_H * k
                boy = [(w, h, 0)] if dn == 0 else [(h, w, 90)]
                Bh = bolge(Hn.buffer(1)) if bant_mi else Hn.buffer(1)
                Bp = bolge(P.buffer(-1, join_style=2)) if bant_mi else P.buffer(-1, join_style=2)
                kad = [(Bh, True)] if temiz else [(Bh, False), (Bp, False)]
                q, rot = yer_bul(boy, anc, kad, yasak, mim, kendi=g, adim=5.0 if k < 1 else 10.0)
                if q is not None:
                    return q, (rot, k)
        return None, None
    adim = ['m'] + ['d%d' % i for i in range(len(o['tasarim']['devreler']))]
    if sira == 'devre_once':
        adim = adim[1:] + adim[:1]
    for ad in adim:
        if ad == 'm':
            mq, mk = mahal(yasak)
            if mq is None:
                eksik += 1
            else:
                yasak = yasak.union(mq.buffer(4))
        else:
            c = o['tasarim']['devreler'][int(ad[1:])]
            hiza_k = dv[0][2][1] if dv and dv[0][2][0] == 0 else 1.0
            q, rot = devre(c, yasak, dv[0][1].centroid.x if dv and dv[0][2][0] == 0 else None, hiza_k)
            if q is None:
                eksik += 1
                continue
            dv.append((c, q, rot))
            yasak = yasak.union(q.buffer(4))
    # Ek (tur 4): iki (+) devreli mahalde etiketler kullanıcının çizimindeki gibi aynı x hizasında alt alta. İlk
    # yerleşim hizasızsa ortak x taranır (5 cm adım): her etiket kendi bandında, aynı ölçekte; ilk yerlere en yakın x.
    if len(dv) >= 2 and all(r_[0] == 0 for c_, q_, r_ in dv) and \
            max(q_.centroid.x for c_, q_, r_ in dv) - min(q_.centroid.x for c_, q_, r_ in dv) > 0.5:
        k0 = min(r_[1] for c_, q_, r_ in dv)
        taban = yasak0.union(mq.buffer(4)) if mq is not None else yasak0
        bx0, _, bx1, _ = P.bounds
        w = S.ETIKET_W * k0
        en = None
        for hx in _aralik(bx0 + w / 2, bx1 - w / 2, 5.0):
            yz, yeni = taban, []
            for c_, q_, r_ in dv:
                q2, r2 = devre(c_, yz, hx, k0, sadece_hiza=True)
                if q2 is None or r2[1] < k0 - 1e-6:
                    break
                yeni.append((c_, q2, r2))
                yz = yz.union(q2.buffer(4))
            if len(yeni) != len(dv):
                continue
            puan = sum(q2.centroid.distance(q_.centroid) for (c_, q_, r_), (_, q2, _) in zip(dv, yeni))
            if en is None or puan < en[0]:
                en = (puan, yeni, yz)
        if en is not None:
            dv = en[1]
            yasak = en[2]
    return (mq, mk if mq is not None else 1.0), dv, yasak, eksik


def _deliksiz(g, derin=0):
    """delikli poligonu deliklerin ortasından dikey bölerek deliksiz parçalara ayır (WIPEOUT tek sınır ister)"""
    from shapely.ops import split
    out = []
    for q in MY._parcalar(g):
        if not q.interiors or derin > 6:
            out.append(q)
            continue
        h = Polygon(q.interiors[0]).centroid
        x0, y0, x1, y1 = q.bounds
        for p in getattr(split(q, LineString([(h.x, y0 - 1), (h.x, y1 + 1)])), 'geoms', []):
            out += _deliksiz(p, derin + 1)
    return out


def maske_ciz(msp, q, mim, eng, yazi=None):
    """Etiket maskesi (WIPEOUT). Kutunun altında mimari çizgi (vitrifiye, küvet, duş teknesi, Ç.M., duvar) yoksa tek
    dikdörtgen. Varsa (Y-4) maske = kutu − (çizgiler + 3 cm) − vitrifiye/tefriş alanı: boru örtülür, tefriş ve vitrifiye
    görünür kalır (README: yerden ısıtma paftasında tefriş silinmez). -> kesik maske mi"""
    x0, y0, x1, y1 = q.bounds
    alt = mim.intersection(q) if mim is not None and not mim.is_empty else None
    yz = yazi.intersection(q) if yazi is not None and not yazi.is_empty else None
    if yz is not None and yz.area < 1.0:
        yz = None
    if (alt is None or alt.is_empty or alt.length < 1.0) and yz is None:
        msp.add_wipeout([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dxfattribs={'layer': L_MASK})
        return False
    m = q.difference(alt.buffer(3.0, cap_style=2, join_style=2)) if alt is not None and not alt.is_empty else q
    if yz is not None:
        m = m.difference(yz.buffer(1.0, join_style=2))        # mimari yazı (mahal adı, m²) maskelenmez
    if eng is not None and not eng.is_empty:
        m = m.difference(eng.buffer(1.0, join_style=2))
    for p in _deliksiz(m.buffer(0)):
        p = p.simplify(0.2)
        if p.area < 30 or p.geom_type != 'Polygon':
            continue
        msp.add_wipeout([tuple(v) for v in list(p.exterior.coords)[:-1]], dxfattribs={'layer': L_MASK})
    return True


def etiketle(msp, KT, tum_borular):
    """Mahal etiketi + devre etiketleri, hepsi kendi mahalinin içinde (kılavuz yok); boru üstündekilerin altı
    WIPEOUT maskeli. Kullanıcının çizimi: devre tablosu serpantinin üstüne biner (cep yok), mahal etiketi serbest
    zeminde (vitrifiye, duş teknesi, küvet ve duvar üstüne binmez — R5). Küçük ıslak hacimde önce mahal, sığmazsa
    önce devre etiketi denenir; 150 × 80 hiç sığmazsa tablo 90° döndürülür (dar hol)."""
    yasak = KT['yasak']
    say = dict(maskeli=0, bos=0, dondurulmus=0, mahal=0, mahal_maskeli=0, yok=0, mahal_yok=0)
    mim = KT['mimari']
    for o in KT['odalar']:
        en_iyi = None
        # iki sıra da denenir: önce eksik etiket, sonra (Ek) en küçük ölçek en büyük olan (yazı h 10'a yakın)
        # önce ayak demeti / kombi hattı da yasak (boru maskelenmesin); yer yoksa yalnız eski yasak
        ay = KT.get('ayak_yasak')
        for yz in ([yasak.union(ay), yasak] if ay is not None and not ay.is_empty else [yasak]):
            for sira in ('mahal_once', 'devre_once'):
                r = _oda_etiket_yerleri(o, yz, mim, sira, KT.get('yazi_u'))
                olc = [k for c_, q_, (rt_, k) in r[1]] + [r[0][1]]
                r = r + ((r[3] + (0 if yz is yasak else 0), -min(olc), -sum(olc)),)
                if en_iyi is None or r[4] < en_iyi[4]:
                    en_iyi = r
            if en_iyi is not None and en_iyi[3] == 0 and en_iyi[0][0] is not None:
                break
        en_iyi = en_iyi[:4]
        yasak_once = yasak
        (mq, mk), dv, yasak, eksik = en_iyi
        if ay is not None and not ay.is_empty:
            kut = [q for c_, q, r_ in dv] + ([mq] if mq is not None else [])
            yasak = unary_union([yasak_once] + [q.buffer(5) for q in kut])
        if mq is None:
            say['mahal_yok'] += 1
            log('UYARI: mahal etiketi yeri yok: %s' % o['zon'])
        else:
            if mq.intersects(tum_borular):
                maske_ciz(msp, mq, mim, o['eng'], KT.get('yazi_u'))
                say['mahal_maskeli'] += 1
            ekle(msp, 'ROTAS-YI-MAHAL', (mq.centroid.x, mq.centroid.y), L_MAH,
                 {'DERECE': '%d%%%%DC' % o['sic'], 'NO': o['zon'], 'MAHAL': o['ad'], 'ALAN': '%.2f' % o['alan']},
                 olcek=mk)
            o['etiket'] = mq
            say['mahal'] += 1
        yerli = {id(c) for c, q, rot in dv}
        for c in o['tasarim']['devreler']:
            if id(c) not in yerli:
                say['yok'] += 1
                log('UYARI: etiket yeri yok: devre %d %s' % (c['no'], o['zon']))
        for c, q, (rot, olc) in dv:
            yer = 'ic' if q.intersects(tum_borular) else 'bos'
            say['maskeli' if yer == 'ic' else 'bos'] += 1
            if rot:
                say['dondurulmus'] += 1
            if olc < 1:
                say['kucuk'] = say.get('kucuk', 0) + 1
            x0, y0, x1, y1 = q.bounds
            if yer == 'ic':
                c['maske_kesik'] = maske_ciz(msp, box(x0 - 2, y0 - 2, x1 + 2, y1 + 2), mim, o['eng'],
                                              KT.get('yazi_u'))
                if c['maske_kesik']:
                    say['kesik_maske'] = say.get('kesik_maske', 0) + 1
            ekle(msp, 'ROTAS-YI-ETIKET', (x0, y1) if rot == 0 else (x0, y0), L_ET,
                 {'UZ': '%.2f m' % c['L_m'], 'AR': '15.0', 'YER': '%.1f W' % c['W'], 'NO1': str(c['no']),
                  'MAHAL': o['ad'], 'NO': o['zon'], 'DERECE': '%d%%%%DC' % o['sic'], 'ALAN': '%.2f' % o['alan'],
                  'BORU': 'PEX BORU, 16 x 2.0'}, dondur=rot, olcek=olc)
            c['etiket'] = q
            c['etiket_yer'] = yer
            c['etiket_maskeli'] = yer == 'ic'
    KT['yasak'] = yasak
    return say


# ====================================================================== çizim
def borulari_ciz(msp, KT):
    """her devre tek açık polyline: kollektör ağzı -> gidiş ayağı -> serpantin -> dönüş ayağı -> ağız"""
    for o in KT['odalar']:
        for c in o['tasarim']['devreler']:
            e = msp.add_lwpolyline(tam_devre(c), format='xyb', dxfattribs={'layer': L_PEX, 'const_width': 0.0})
            e.dxf.color = 256


L_KOL = 'ROTAS-ISITMA-KOLLEKTOR'
L_CIHAZ = 'ROTAS-ISITMA-CIHAZ'
L_CAP = 'ROTAS-ISITMA-CAP'


def _yazi_yeri(aday_merkez, w, h, engel, alan, adim=10.0, r_max=220.0):
    """merkez etrafında (spiral) w×h kutunun engelsiz ve alan içinde olduğu en yakın yer"""
    cx, cy = aday_merkez
    en = None
    r = 0.0
    while r <= r_max:
        n = max(1, int(2 * math.pi * r / adim)) if r > 0 else 1
        for k in range(n):
            a = 2 * math.pi * k / n
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            b = box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            if alan.contains(b) and not b.intersects(engel):
                return b
        r += adim
    return en


def kollektor_ciz(msp, KT, engel_tum):
    """planda kollektör dolabı (kullanılan ağızlar kadar), ağız sayısı + toplam W etiketi, kombi + kombi–kollektör
    gidiş/dönüş hattı (sıhhi plandaki kombi yeri)"""
    import ayak as A
    K = KT['K']
    say = 0
    for dno, son in (KT.get('kollektorler') or {}).items():
        if not son:
            continue
        kol = son['kollektor']
        od = [o for o in KT['odalar'] if o['daire'] == dno]
        devs = [c for o in od for c in o['tasarim']['devreler'] if c.get('ayak_g')]
        if not devs:
            continue
        agizlar = [s_ for c in devs for s_ in c['agiz']]
        kh = son.get('kombi_hat')
        if kh:
            agizlar += list(kh['slot'])
        k0 = kol['yuz'][0]
        u, ic = kol['u'], kol['ic']
        ts = [A.KOL_PAY + A.RES * (s_ - 2 * A.YEDEK) for s_ in agizlar]
        t0, t1 = min(ts) - 10.0, max(ts) + 10.0
        p0 = (k0[0] + u[0] * t0, k0[1] + u[1] * t0)
        p1 = (k0[0] + u[0] * t1, k0[1] + u[1] * t1)
        D_ = A.KOL_DERIN
        kutu = [p0, p1, (p1[0] + ic[0] * D_, p1[1] + ic[1] * D_), (p0[0] + ic[0] * D_, p0[1] + ic[1] * D_)]
        msp.add_lwpolyline(kutu, close=True, dxfattribs={'layer': L_KOL})
        # gidiş / dönüş barları (dolap içinde iki çizgi)
        for d in (3.5, 6.5):
            msp.add_line((p0[0] + ic[0] * d + u[0] * 4, p0[1] + ic[1] * d + u[1] * 4),
                         (p1[0] + ic[0] * d - u[0] * 4, p1[1] + ic[1] * d - u[1] * 4), dxfattribs={'layer': L_KOL})
        n = len(devs)
        W = sum(c['W'] for c in devs)
        # etiket: dolabın yanında, boru / yazı üstüne binmeden (iki satır, h 10)
        s1 = 'KOLLEKTÖR %d AĞIZ' % n
        s2 = '%.1fW-%%%%C32' % W
        w = max(len(s1), len(s2) - 2) * 10 * 0.65 * 0.95 + 6
        h = 2 * 10 + 10
        hol = next(o for o in od if o['tur'] == 'hol')
        mer = ((p0[0] + p1[0]) / 2 + ic[0] * 45, (p0[1] + p1[1]) / 2 + ic[1] * 45)
        b = _yazi_yeri(mer, w, h, engel_tum, hol['poly'].buffer(-3), adim=5.0, r_max=500.0)
        if b is None:
            b = _yazi_yeri(mer, w, h, engel_tum, unary_union([o['poly'] for o in od]).buffer(-3), adim=5.0,
                           r_max=500.0)
        if b is not None:
            x0, y0, x1, y1 = b.bounds
            _yazi(msp, s1, (x0 + 3, y1 - 12), 10, 41, katman=L_CAP)
            _yazi(msp, s2, (x0 + 3, y1 - 27), 10, 41, katman=L_CAP)
            engel_tum = engel_tum.union(b)
            KT['yasak'] = KT['yasak'].union(b.buffer(5))      # devre / mahal etiketleri buraya konmaz
        # kombi (sıhhi plandaki kombi kutusu) + hatlar
        if kh:
            kx, ky = kh['gidis'][0]
            f = min((f for f in K.fx if f['kind'] == 'KOMBI'), key=lambda f: math.hypot(f['c'][0] - kx, f['c'][1] - ky),
                    default=None)
            bb = f.get('bb') if f else None
            if bb:
                x0, y0, x1, y1 = bb
            else:
                x0, y0, x1, y1 = kx - 20, ky - 15, kx + 20, ky + 15
            msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': L_CIHAZ})
            _yazi(msp, 'KOMBİ', ((x0 + x1) / 2, y1 + 4), 8, 2, ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER, L_CIHAZ)
            msp.add_lwpolyline(kh['gidis'], dxfattribs={'layer': 'ROTAS-ISITMA-GIDIS-BORU'})
            msp.add_lwpolyline(kh['donus'], dxfattribs={'layer': 'ROTAS-ISITMA-DONUS-BORU'})
        say += 1
    return say


def baslik(msp, k):
    w = M.win(k)
    cx = (w[0] + w[2]) / 2
    t = msp.add_text('%s PLANI..........ÖLÇEK: 1 / 50' % KAT_ADI[k],
                     dxfattribs={'layer': 'ROTAS-PAFTA-BASLIK', 'height': 40, 'style': 'ROTAS-YAZI', 'width': 0.8})
    t.set_placement((cx, w[1] - 110), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    t2 = msp.add_text('YERDEN ISITMA TESİSATI', dxfattribs={'layer': 'ROTAS-PAFTA-BASLIK', 'height': 25,
                                                            'style': 'ROTAS-YAZI', 'width': 0.8})
    t2.set_placement((cx, w[1] - 165), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)


# ====================================================================== model (json)
def model_yaz(KTS):
    out = {'proje': {'ad': 'METRA MİMARLIK — TEKELER 4739/4 (new_block)', 'birim': 'cm', 'W_m': W_M,
                     'boru': 'PEX 16 x 2.0', 'aralik_cm': S.ADIM},
           'katlar': []}
    for KT in KTS:
        kat = {'kat': KT['kat'], 'ad': KAT_ADI[KT['kat']], 'daireler': {}}
        for o in KT['odalar']:
            dd = kat['daireler'].setdefault(str(o['daire']), {'no': 'D%d' % o['daire'], 'mahaller': []})
            dd['mahaller'].append({
                'zon': o['zon'], 'ad': o['ad'], 'tur': o['tur'], 'sic': o['sic'], 'alan_m2': o['alan'],
                'alan_mimari_m2': o['alan_mimari'],
                'isitma_alani_m2': round(o['H'].area / 1e4, 2), 'kose': o['tasarim']['kose'],
                'bbox': [round(v, 1) for v in o['poly'].bounds],
                'devreler': [{'no': c['no'], 'L_m': c['L_m'], 'W': c['W'],
                              'L_ayak_m': round((S.uzunluk(tam_devre(c)) - S.uzunluk(c['pts'])) / 100.0, 2), 'etiket': {'cep': 'cep', 'ic': 'maskeli', 'bos': 'bos'}.get(c.get('etiket_yer'), 'yok')} for c in o['tasarim']['devreler']]})
        for dno, son in (KT.get('kollektorler') or {}).items():
            dd = kat['daireler'].get(str(dno))
            if dd is None:
                continue
            devs = [c for o in KT['odalar'] if o['daire'] == dno for c in o['tasarim']['devreler']]
            dd['kollektor'] = {'agiz': len(devs), 'W': round(sum(c['W'] for c in devs), 1),
                               'ayakli': sum(1 for c in devs if c.get('ayak_g')),
                               'kombi_hatti': bool(son and son.get('kombi_hat'))}
        kat['isitilmayan'] = sorted({'%s (%s)' % (q['ad'].replace('\n', ' '), q['tur']) for q in KT['isitmasiz']})
        out['katlar'].append(kat)
    json.dump(out, open(CIKIS_JSON, 'w'), ensure_ascii=False, indent=1)
    return out


# ====================================================================== ana
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--png', action='store_true', help='önizleme PNG + referansla yan yana')
    ap.add_argument('--ayaklar', action='store_true', help='kollektör ayakları (varsayılan kapalı: kullanıcı planda çizmiyor)')
    ap.add_argument('--cep', action='store_true',
                    help='(eski davranış) devre etiketi için serpantinde cep bırak. Varsayılan: kullanıcının çizimi gibi '
                         'etiket serpantinin üstünde, altı WIPEOUT maskeli (R1)')
    ap.add_argument('--yenile', action='store_true', help='mimari önbelleğini yenile')
    a = ap.parse_args(argv)
    t0 = time.time()
    os.makedirs(CIKIS, exist_ok=True)
    if a.yenile:
        for k in KATLAR:
            MY.kat_oku(k, yenile=True)
    doc = belge()
    msp = doc.modelspace()
    kutular = mimari_kopyala(doc)
    KTS = []
    for k in KATLAR:
        KT = kat_tasarla(k, kutular, [], cep_ac=a.cep)
        n = sum(len(o['tasarim']['devreler']) for o in KT['odalar'])
        log('kat %s: %d ısıtılan mahal, %d devre' % (k, len(KT['odalar']), n))
        KTS.append(KT)
    if a.ayaklar:
        log('UYARI: --ayaklar henüz uygulanmadı (kullanıcının çiziminde planda ayak yok); yalnız şemada gösterilir')
    for KT in KTS:
        borulari_ciz(msp, KT)
    tum = unary_union([S.cizgi(tam_devre(c)).buffer(3) for KT in KTS for o in KT['odalar'] for c in o['tasarim']['devreler']] +
                      [LineString(h).buffer(3) for KT in KTS for son in (KT.get('kollektorler') or {}).values() if son
                       and son.get('kombi_hat') for h in (son['kombi_hat']['gidis'], son['kombi_hat']['donus'])])
    for KT in KTS:
        kollektor_ciz(msp, KT, unary_union([tum, KT['yazi_u']]))
        # etiketler ayak demeti / kombi hattı üstüne (maskeyle boruyu kapatarak) konmasın: önce boş yer aranır
        ayak_hat = [LineString([p[:2] for p in tam_devre(c)]).difference(S.cizgi(c['pts']).buffer(1))
                    for o in KT['odalar'] for c in o['tasarim']['devreler'] if c.get('ayak_g')]
        ayak_hat += [LineString(h) for son in (KT.get('kollektorler') or {}).values() if son and son.get('kombi_hat')
                     for h in (son['kombi_hat']['gidis'], son['kombi_hat']['donus'])]
        if ayak_hat:
            KT['ayak_yasak'] = unary_union([g.buffer(4) for g in ayak_hat if not g.is_empty])
    for KT in KTS:
        KT['mimari'] = mimari_cizgi(KT['K'])
        KT['etiket_sayim'] = etiketle(msp, KT, tum)
        baslik(msp, KT['kat'])
        log('kat %s etiket: %s' % (KT['kat'], KT['etiket_sayim']))
    model = model_yaz(KTS)
    import yi_sema
    yi_sema.ciz(doc, msp, model)
    doc.saveas(CIKIS_DXF)
    log('DXF: %s (%.1f s)' % (CIKIS_DXF, time.time() - t0))
    import excel_yi
    excel_yi.yaz(model)
    import yi_kontrol
    sonuc = yi_kontrol.calistir(KTS, CIKIS_DXF)
    if a.png:
        import yi_onizleme
        yi_onizleme.ciz(CIKIS_DXF, KTS)
    log('bitti (%.1f s)' % (time.time() - t0))
    return sonuc


if __name__ == '__main__':
    main()
