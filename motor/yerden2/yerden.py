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


def ekle(msp, ad, p, katman, attr, olcek=1.0):
    e = msp.add_blockref(ad, p, dxfattribs={'layer': katman, 'xscale': olcek, 'yscale': olcek})
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
            for f in ((D.yazi_kutusu, D.yazi_poligonu) if e.dxftype() == 'MTEXT' else (D.yazi_poligonu,)):
                pg = f(e)
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
        eng = MY.engeller(K, r)
        H, R = MY.bolge(r, eng)
        kapi = MY.ana_kapi(K, r, tur)
        d = T.oda_tasarla(r, H, R, kapi, yasak, cep_ac)
        if d is None:
            log('UYARI: %s kat %s daire %s %s (%.2f m²): devre kurulamadı' % (k, r['name'], r['daire'], tur, r['area']))
            isitmasiz.append(dict(ad=r['name'], poly=r['poly'], tur='kurulamadi'))
            continue
        for c in d['devreler']:
            if c['cep'] is not None:
                yasak = yasak.union(c['cep'].buffer(5))
        odalar.append(dict(ad=r['name'].replace('\n', ' '), daire=r['daire'], tur=tur, sic=sic, alan=round(r['area'], 2),
                           alan_mimari=mimari_m2(K, r),
                           poly=r['poly'], H=H, eng=eng, xy=r['xy'], kapi=kapi, tasarim=d))
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
    return dict(kat=k, K=K, odalar=odalar, isitmasiz=isitmasiz, yasak=yasak, yazi=yaz)


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
def yerlestir(w, h, anchor, oda_geom, yasak, borular, mimari=None, maske_izin=True, disari=True):
    """w×h dikdörtgen yeri:
      (0) oda içinde, boru üstüne gelmeyen (maske gerekmez)          -> 'bos'
      (1) oda içinde, borunun üstünde (altı WIPEOUT maskeli)          -> 'ic'
      (2) oda dışında 800 cm içinde: yazı, etiket, boru ve mimari çizgi olmayan boş yer (kılavuz çizgili) -> 'dis'
    -> (dikdörtgen, tür) | (None, None)"""
    from shapely.prepared import prep
    py = prep(yasak) if not yasak.is_empty else None
    pb = prep(borular) if borular is not None and not borular.is_empty else None
    ax, ay = anchor
    if oda_geom is not None and not oda_geom.is_empty:
        pi = prep(oda_geom)
        bx = oda_geom.bounds
        aday = [(x, y) for x in _aralik(bx[0] + w / 2, bx[2] - w / 2, 10) for y in _aralik(bx[1] + h / 2, bx[3] - h / 2, 10)]
        aday.sort(key=lambda p: math.hypot(p[0] - ax, p[1] - ay))
        uygun = []
        for cx, cy in aday:
            q = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            if pi.contains(q) and (py is None or not py.intersects(q)):
                if pb is None or not pb.intersects(q):
                    return q, 'bos'
                uygun.append(q)
        if uygun and maske_izin:
            return uygun[0], 'ic'
    if not disari:
        return None, None
    pm = prep(mimari) if mimari is not None and not mimari.is_empty else None
    aday = [(ax + dx, ay + dy) for dx in range(-800, 801, 15) for dy in range(-800, 801, 15)]
    aday.sort(key=lambda p: math.hypot(p[0] - ax, p[1] - ay))
    for cx, cy in aday:
        q = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        if (py is None or not py.intersects(q)) and (pb is None or not pb.intersects(q)) and \
                (pm is None or not pm.intersects(q)):
            return q, 'dis'
    return None, None


def _aralik(a, b, s):
    out = []
    x = a
    while x <= b + 1e-6:
        out.append(x)
        x += s
    return out or [(a + b) / 2]


def etiketle(msp, KT, tum_borular):
    """devre etiketleri (cep / oda içinde maskeli / oda dışında kılavuzlu) + mahal etiketleri"""
    yasak = KT['yasak']
    say = dict(cep=0, bos=0, maskeli=0, disari=0, mahal=0, mahal_maskeli=0, mahal_disari=0, yok=0)
    for o in KT['odalar']:
        for c in o['tasarim']['devreler']:
            q = c['cep']
            yer = 'cep'
            if q is None:
                ux, uy = c['pts'][0][0], c['pts'][0][1]
                q, yer = yerlestir(S.ETIKET_W, S.ETIKET_H, (ux, uy), o['H'].buffer(1), yasak, tum_borular, KT['mimari'])
                if q is None:
                    say['yok'] += 1
                    log('UYARI: etiket yeri yok: devre %d %s' % (c['no'], o['zon']))
                    continue
                say[{'ic': 'maskeli', 'dis': 'disari', 'bos': 'bos'}[yer]] += 1
            else:
                say['cep'] += 1
            x0, y0, x1, y1 = q.bounds
            if yer == 'ic':
                msp.add_wipeout([(x0 - 2, y0 - 2), (x1 + 2, y0 - 2), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)],
                                dxfattribs={'layer': L_MASK})
            if yer == 'dis':
                ux, uy = c['pts'][0][0], c['pts'][0][1]
                from shapely.ops import nearest_points
                p = nearest_points(q.exterior, Point(ux, uy))[0]
                msp.add_line((p.x, p.y), (ux, uy), dxfattribs={'layer': L_ET, 'color': 2})
            ekle(msp, 'ROTAS-YI-ETIKET', (x0, y1), L_ET,
                 {'UZ': '%.2f m' % c['L_m'], 'AR': '15.0', 'YER': '%.1f W' % c['W'], 'NO1': str(c['no']),
                  'MAHAL': o['ad'], 'NO': o['zon'], 'DERECE': '%d%%%%DC' % o['sic'], 'ALAN': '%.2f' % o['alan'],
                  'BORU': 'PEX BORU, 16 x 2.0'})
            c['etiket'] = q
            c['etiket_yer'] = yer
            c['etiket_maskeli'] = yer == 'ic'
            yasak = yasak.union(q.buffer(4))
    # mahal etiketleri: mahal adının üstünde (yoksa oda içinde en yakın boş yer), maskeli
    for o in KT['odalar']:
        x, y = o['xy']
        # önce mahal adının üstünde (referans: üst yarı), boru üstündeyse maskeli
        q, yer = yerlestir(74, 54, (x, y + 110), o['poly'].buffer(-4), yasak, tum_borular, KT['mimari'],
                           maske_izin=False, disari=False)
        if q is None or q.centroid.distance(Point(x, y + 110)) > 160:
            q, yer = yerlestir(74, 54, (x, y + 110), o['poly'].buffer(-4), yasak, None, KT['mimari'])
        if q is not None and yer == 'bos' and q.intersects(tum_borular):
            yer = 'ic'
        if yer == 'ic':
            say['mahal_maskeli'] += 1
        if q is None:
            log('UYARI: mahal etiketi yeri yok: %s' % o['zon'])
            continue
        cx, cy = q.centroid.x, q.centroid.y
        x0, y0, x1, y1 = q.bounds
        if yer == 'ic':
            msp.add_wipeout([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dxfattribs={'layer': L_MASK})
        elif yer == 'dis':
            say['mahal_disari'] += 1
            from shapely.ops import nearest_points
            p = nearest_points(q.exterior, Point(x, y))[0]
            msp.add_line((p.x, p.y), (x, y + 25), dxfattribs={'layer': L_MAH, 'color': 2})
        ekle(msp, 'ROTAS-YI-MAHAL', (cx, cy), L_MAH, {'DERECE': '%d%%%%DC' % o['sic'], 'NO': o['zon'],
                                                       'MAHAL': o['ad'], 'ALAN': '%.2f' % o['alan']})
        o['etiket'] = q
        say['mahal'] += 1
        yasak = yasak.union(q.buffer(4))
    KT['yasak'] = yasak
    return say


# ====================================================================== çizim
def borulari_ciz(msp, KT):
    for o in KT['odalar']:
        for c in o['tasarim']['devreler']:
            e = msp.add_lwpolyline([(x, y, b) for x, y, b in c['pts']], format='xyb',
                                   dxfattribs={'layer': L_PEX, 'const_width': 0.0})
            e.dxf.color = 256


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
                'devreler': [{'no': c['no'], 'L_m': c['L_m'], 'W': c['W'], 'etiket': 'cep' if c['cep'] is not None
                              else ('maskeli' if c.get('etiket_maskeli') else 'disari')} for c in o['tasarim']['devreler']]})
        kat['isitilmayan'] = sorted({'%s (%s)' % (q['ad'].replace('\n', ' '), q['tur']) for q in KT['isitmasiz']})
        out['katlar'].append(kat)
    json.dump(out, open(CIKIS_JSON, 'w'), ensure_ascii=False, indent=1)
    return out


# ====================================================================== ana
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--png', action='store_true', help='önizleme PNG + referansla yan yana')
    ap.add_argument('--ayaklar', action='store_true', help='kollektör ayakları (varsayılan kapalı: kullanıcı planda çizmiyor)')
    ap.add_argument('--etiket-ust', action='store_true',
                    help='devre etiketi için cep bırakma: tablo serpantin üstünde, altı maskeli (kullanıcının çizimi gibi)')
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
        KT = kat_tasarla(k, kutular, [], cep_ac=not a.etiket_ust)
        n = sum(len(o['tasarim']['devreler']) for o in KT['odalar'])
        log('kat %s: %d ısıtılan mahal, %d devre' % (k, len(KT['odalar']), n))
        KTS.append(KT)
    if a.ayaklar:
        log('UYARI: --ayaklar henüz uygulanmadı (kullanıcının çiziminde planda ayak yok); yalnız şemada gösterilir')
    for KT in KTS:
        borulari_ciz(msp, KT)
    tum = unary_union([S.cizgi(c['pts']).buffer(3) for KT in KTS for o in KT['odalar'] for c in o['tasarim']['devreler']])
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
