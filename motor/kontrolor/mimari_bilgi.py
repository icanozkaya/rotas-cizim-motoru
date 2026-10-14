"""Kontrolör için mimari bilgi: mahal poligonları, ıslak hacimler, armatürler, betonarme kolonlar, daire grupları,
ortak alanlar. Tanıma `motor/deneme/uctan_uca/mimari.py` (new_block kaynak) ile aynı kural tabanlı yöntemle yapılır;
kontrolör çizimi "mimariyi bilerek" ölçer (branşman hangi mahalde, sıcak su hangi dairede, süzgeç balkonda mı ...).

Kaynak seçenekleri:
  - `ornekler/new_block.dxf(.xz)` : MKDU0 katmanı, kat pencereleri mimari.WIN_Z / OFF (Z, 1, 2)
  - başka bir mimari DXF         : verilen katman(lar) (varsayılan: adında MIMARI/MKDU/DUVAR geçen veya tümü),
                                   kat pencereleri --pencere JSON ile ya da kontrol edilen çizimin kat paftalarından
  - kaynak yoksa                  : kontrol edilen çizimin kendi ROTAS-MIMARI* katmanları (kat paftası = pencere)
"""
import math
import os
import sys
from collections import Counter

import numpy as np
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in (KOK + '/motor/deneme/uctan_uca', KOK + '/motor'):
    if p not in sys.path:
        sys.path.insert(0, p)
import mimari as M  # noqa: E402

WET_ADLAR = ('banyo', 'wc', 'duş', 'dus', 'mutfak', 'lvb', 'lavabo', 'tuvalet', 'ebeveyn b')
ORTAK_ADLAR = ('merdiven', 'asansör', 'asansor', 'en. oda', 'enerji', 'hol', 'sahanlık', 'sahanlik', 'giriş', 'giris',
               'sığınak', 'siginak', 'kazan', 'depo', 'kapıcı', 'otopark')
KORIDOR_ADLAR = ('antre', 'kor', 'hol', 'koridor', 'merdiven', 'sahanlık', 'sahanlik')


def norm(s):
    return ' '.join((s or '').replace('%%c', 'Ø').replace('%%C', 'Ø').split()).lower()


def islak_mi(ad):
    a = norm(ad)
    return any(k in a for k in WET_ADLAR) and 'balkon' not in a


def ortak_mi(ad):
    a = norm(ad)
    return any(k in a for k in ORTAK_ADLAR) and not a.startswith('antre')


def koridor_mi(ad):
    a = norm(ad)
    return any(k in a for k in KORIDOR_ADLAR)


def balkon_mi(ad):
    return 'balkon' in norm(ad) or 'teras' in norm(ad)


# ------------------------------------------------------------------ kaynak
def new_block_mi(yol):
    return yol is not None and 'new_block' in os.path.basename(yol).lower()


def kaynak_oku(yol, katmanlar=None):
    """mimari kayıt listesi (mimari.py biçimi: ('L',[p,p],None) / ('P',pts,None) / ('A',pts,None) / ('C',[c],r) /
    ('T',[ins, merkez],(metin, h, rot)) / ('H',pts,desen)). new_block için mimari.extract() (önbellekli)."""
    if new_block_mi(yol):
        return M.extract()
    import ezdxf
    from ezdxf import path as ep
    doc = ezdxf.readfile(yol)
    return kayitlar_dxf(doc.modelspace(), katmanlar)


def kayitlar_dxf(msp, katmanlar=None, pencere=None):
    """ezdxf model alanından mimari kayıtları (katmanlar: isim listesi / None = MIMARI, MKDU, DUVAR geçenler / 'HEPSI')."""
    from ezdxf import path as ep

    def sec(lay):
        if katmanlar == 'HEPSI':
            return True
        if katmanlar:
            return lay in katmanlar
        n = lay.upper()
        return any(k in n for k in ('MIMARI', 'MKDU', 'DUVAR', 'TEFRIS', 'MIM-'))

    A = []
    for e in msp:
        lay = e.dxf.get('layer', '0')
        if not sec(lay):
            continue
        t = e.dxftype()
        try:
            if t == 'LINE':
                A.append(('L', [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]], None))
            elif t in ('LWPOLYLINE', 'ARC', 'POLYLINE', 'ELLIPSE', 'SPLINE'):
                pts = [(v.x, v.y) for v in ep.make_path(e).flattening(1.0)]
                if t == 'LWPOLYLINE' and e.closed and pts and pts[0] != pts[-1]:
                    pts.append(pts[0])
                A.append(('A' if t in ('ARC', 'ELLIPSE') else 'P', pts, None))
            elif t == 'CIRCLE':
                A.append(('C', [tuple(e.dxf.center)[:2]], e.dxf.radius))
            elif t == 'TEXT':
                p = e.dxf.align_point if (e.dxf.halign or e.dxf.valign) and e.dxf.hasattr('align_point') else e.dxf.insert
                w_ = len(e.dxf.text) * e.dxf.height * 0.55
                cx = p[0] + w_ / 2 * (1 - e.dxf.halign) if e.dxf.halign in (0, 1, 2) else p[0]
                A.append(('T', [tuple(e.dxf.insert)[:2], (cx, p[1])], (e.dxf.text, e.dxf.height, e.dxf.rotation)))
            elif t == 'MTEXT':
                txt = e.plain_text()
                h = e.dxf.char_height
                w_ = max(len(q) for q in txt.split('\n')) * h * 0.55 if txt else 0
                nl = txt.count('\n') + 1
                ap = e.dxf.get('attachment_point', 1)
                col, row = (ap - 1) % 3, (ap - 1) // 3
                ip = e.dxf.insert
                A.append(('T', [tuple(ip)[:2], (ip[0] + w_ / 2 * (1 - col), ip[1] - nl * h * 1.4 / 2 * (1 - row))],
                          (txt, h, e.dxf.get('rotation', 0))))
            elif t == 'HATCH':
                for p in ep.from_hatch(e):
                    A.append(('H', [(v.x, v.y) for v in p.flattening(1.0)], e.dxf.pattern_name))
        except Exception:
            pass
    if pencere:
        A = M.recs_in(A, pencere)
    return A


def kaynak_pencereleri(yol):
    """kaynağın kat pencereleri {kat: (x0,y0,x1,y1)} — new_block için bilinen; başka kaynakta None (dışarıdan verilir)."""
    if new_block_mi(yol):
        return {k: M.win(k) for k in M.FLOORS}
    return None


# ------------------------------------------------------------------ kat analizi
def _etiketler(R):
    """mahal etiketleri: mimari.labels + burada ek sözcükler (wc-banyo, wc-duş, ebeveyn banyosu, hol, koridor ...)"""
    out = []
    for a in R:
        if a[0] != 'T' or a[2][1] < 15.0:
            continue
        t = a[2][0].strip()
        n = norm(t)
        if (t in M.ROOM_WORDS or n.split()[0] in ('salon', 'mutfak', 'banyo', 'wc', 'wc-banyo', 'wc-duş', 'wc-lvb.',
                                                  'yatak', 'oda', 'hol', 'koridor', 'antre', 'antre-kor.', 'balkon',
                                                  'merdiven', 'duş', 'yüklük', 'ebeveyn', 'teras', 'çamaşır', 'kiler',
                                                  'depo', 'sığınak', 'kazan', 'dükkan', 'dükkân', 'ofis', 'giriş')
                or n.startswith('asansör') or n.startswith('en. oda')):
            if n.endswith('m²') or n.endswith('m2'):
                continue
            c = a[1][1] if len(a[1]) > 1 else a[1][0]
            out.append((c[0], c[1], t))
    return out


def _daire_gruplari(R, rooms, w, cols, res=5.0):
    """daire numarası yazıları (1..20, h>=15) tohum; gerçek duvarlar engel; her mahal etiketi en yakın (yürüme) tohuma.
    Dönüş: {mahal indeksi: daire no} (ortak alanlar hariç)."""
    from skimage.graph import MCP_Geometric
    from skimage.draw import line as skl, polygon as skp
    from scipy import ndimage
    tohum = []
    for a in R:
        if a[0] == 'T' and a[2][1] >= 15:
            t = a[2][0].strip()
            if t.isdigit() and 1 <= int(t) <= 40:
                tohum.append((a[1][0], int(t)))
    if not tohum:
        return {}, []
    x0, y0, x1, y1 = w
    nx, ny = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
    img = np.zeros((nx, ny), bool)
    ij = lambda p: (min(nx - 1, max(0, int(round((p[0] - x0) / res)))),
                    min(ny - 1, max(0, int(round((p[1] - y0) / res)))))
    for k, d in M.walls_ents(R):
        pts = d
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            a, b = ij((ax, ay)), ij((bx, by))
            rr, cc = skl(a[0], a[1], b[0], b[1])
            img[rr, cc] = True
    # betonarme kolonlar ve şişirme KULLANILMAZ: kapı kanatları çizili olduğundan kapı geçişleri daralır, mahaller
    # ulaşılmaz görünür (new_block'ta denendi: şişirmeyle 2/27, şişirmesiz 27/27 mahal atanır)
    cost = np.where(img, 1e6, 1.0)
    dist = {}
    for p, n in tohum:
        m = MCP_Geometric(cost)
        cum, _ = m.find_costs([ij(p)])
        dist[n] = cum
    out = {}
    for i, r in enumerate(rooms):
        if ortak_mi(r['name']):
            continue
        c = ij(r['xy'])
        n = min(dist, key=lambda q: dist[q][c])
        if dist[n][c] < 1e5:
            out[i] = n
    # ulaşılamayan mahaller (pencere çizgisiyle kapalı balkon, küçük duş vb.): en çok ortak sınırı olan atanmış mahalin dairesi
    for i, r in enumerate(rooms):
        if i in out or ortak_mi(r['name']):
            continue
        en, enb = None, 0
        for j, q in enumerate(rooms):
            if j in out:
                a = r['poly'].buffer(30).intersection(q['poly'].buffer(30)).area
                if a > enb:
                    en, enb = out[j], a
        if en is not None and enb > 900:
            out[i] = en
    return out, tohum


def kat_analiz(A, w, kat='?'):
    """Bir kat penceresi için mimari bilgi sözlüğü (kaynak koordinatlarında)."""
    import rooms as RM
    R = M.recs_in(A, w)
    labs = _etiketler(R)
    ents = M.walls_ents(R)
    out, _ = RM.detect(ents, labs, w, res=2.0, door=100.0, disc=40.0)
    rooms = []
    for i, d in out.items():
        pg = d['poly']
        rooms.append(dict(name=d['name'], poly=pg, area=d['area'], xy=d['xy'],
                          islak=islak_mi(d['name']), ortak=ortak_mi(d['name']), balkon=balkon_mi(d['name']),
                          koridor=koridor_mi(d['name'])))
    wet, W = M.wet_rooms(R, [(x, y, t) for x, y, t in labs if t in M.WET])
    # mimari.WET dışındaki ıslak adlar (wc-banyo, wc-duş ...) için de ışın dikdörtgeni
    for x, y, t in labs:
        if islak_mi(t) and t not in M.WET:
            wet.append(dict(name=t, xy=(x, y), rect=W.rect((x, y))))
    fx = M.fixtures(R, wet, W)
    cols = M.columns(R)
    # mimarın yağmur inişi: eş merkezli çift daire (r 3-12; new_block'ta r=5 + r=8)
    cs = [(a[1][0], a[2]) for a in R if a[0] == 'C' and 3 <= a[2] <= 12]
    inisler = []
    for i, (c, r) in enumerate(cs):
        if any(j != i and abs(c2[0] - c[0]) < 1.5 and abs(c2[1] - c[1]) < 1.5 and abs(r2 - r) > 1.5 for j, (c2, r2) in enumerate(cs)):
            if not any(abs(q[0] - c[0]) < 1.5 and abs(q[1] - c[1]) < 1.5 for q in inisler):
                inisler.append(c)
    daire, tohum = _daire_gruplari(R, rooms, w, cols)
    kapilar = _kapi_komsulari(R, rooms)
    daire, degisen = _kapi_ile_ata(rooms, daire, kapilar)
    for i, r in enumerate(rooms):
        r['daire'] = daire.get(i)
    # daire poligonları: aynı daire mahallerinin birleşimi (duvar payı 35 cm: duvar içindeki hat daire içi sayılır)
    dp, dpb = {}, {}
    for i, r in enumerate(rooms):
        if r['daire'] is not None:
            dp.setdefault(r['daire'], []).append(r['poly'].buffer(35))
            if not r['balkon']:
                dpb.setdefault(r['daire'], []).append(r['poly'].buffer(35))
    daire_poly = {n: unary_union(v) for n, v in dp.items()}
    daire_poly_ic = {n: unary_union(v) for n, v in dpb.items()}   # balkonsuz (başka daire yasağı için)
    ortak_poly = unary_union([r['poly'].buffer(5) for r in rooms if r['ortak']] or [Polygon()])
    bina = unary_union([r['poly'].buffer(25) for r in rooms] or [Polygon()])
    # armatürlere mahal poligonu ata (en yakın ıslak mahal)
    for f in fx:
        p = Point(f['c'])
        aday = [r for r in rooms if r['islak'] and r['poly'].buffer(15).contains(p)]
        f['mahal'] = min(aday, key=lambda r: r['poly'].area) if aday else None
    # T07/T15/T13 için: mimari taramalar (duvar / betonarme), pencere etiketleri, 'mek. havl.' şaftları, makine yerleri
    taramalar = []
    for a in R:
        if a[0] == 'H' and len(a[1]) >= 4:
            try:
                pg = Polygon(a[1]).buffer(0)
                if pg.area > 50:
                    taramalar.append(pg)
            except Exception:
                pass
    pencereler, mek_havl, makine = [], [], []
    import re
    for a in R:
        if a[0] != 'T':
            continue
        t = a[2][0].strip()
        c = a[1][1] if len(a[1]) > 1 else a[1][0]
        if re.match(r'^[SP]\d{1,3}\b', t) and a[2][1] < 15:
            pencereler.append((c, t))
        n = norm(t)
        if n in ('mek.', 'mek', 'havl.', 'havl') or n.startswith('mek. havl') or n.startswith('mek.havl'):
            mek_havl.append(c)
        tt = n.replace(' ', '').replace("'", '.')
        if tt.startswith(('c.m', 'ç.m', 'ç.mak', 'çam.', 'cam.mak')):
            makine.append(('CM', Point(c).buffer(25), 'mimari yazı "%s"' % t))
        elif tt.startswith(('b.m', 'bul.', 'bul.mak')):
            makine.append(('BM', Point(c).buffer(25), 'mimari yazı "%s"' % t))
    for f in fx:
        if f['kind'] in ('CM', 'BM') and not any(m[0] == f['kind'] and m[1].distance(Point(f['c'])) < 5 for m in makine):
            pg = box(*f['bb']) if f.get('bb') else Point(f['c']).buffer(25)
            makine.append((f['kind'], pg, 'mimari sembol'))
    return dict(kat=kat, pencere=w, R=R, rooms=rooms, wet=wet, fx=fx, cols=cols, daire_poly=daire_poly,
                daire_poly_ic=daire_poly_ic, tohum=tohum, ortak_poly=ortak_poly, bina=bina, labs=labs, inisler=inisler,
                kapilar=kapilar, daire_kapi_degisen=degisen, taramalar=taramalar, pencereler=pencereler,
                mek_havl=mek_havl, mimari_makine=makine)


KAPI_RE = None


def _kapi_komsulari(R, rooms, tol=30.0):
    """kapı ölçü yazıları ('80/220', '90|220' ...: genişlik 60-120, yükseklik >= 180) -> kapının iki yanındaki mahaller.
    Dönüş: [(i, j, (x, y))] (mahal indeksleri). Yazı kapı boşluğunun yanında durur: yazıya <= tol cm en yakın iki mahal."""
    import re
    global KAPI_RE
    if KAPI_RE is None:
        KAPI_RE = re.compile(r'^(\d{2,3})\s*[/|\n]\s*(\d{3})$')
    out = []
    for a in R:
        if a[0] != 'T':
            continue
        m = KAPI_RE.match(a[2][0].strip())
        if not m or not (60 <= int(m.group(1)) <= 120) or int(m.group(2)) < 180:
            continue
        c = a[1][1] if len(a[1]) > 1 else a[1][0]
        pt = Point(c)
        ds = sorted((r['poly'].distance(pt), i) for i, r in enumerate(rooms))
        ds = [(d, i) for d, i in ds if d <= tol][:2]
        if len(ds) == 2:
            out.append((ds[0][1], ds[1][1], c))
    return out


def _kapi_ile_ata(rooms, daire, kapilar):
    """kural (kullanıcı, 15.10.2026): mahal hangi dairenin kapısına açılıyorsa o dairedir. Yürüme mesafesiyle atanan
    daire, mahalin kapı komşularının (ortak alan hariç) HEPSİNİN ortak dairesinden farklıysa kapı komşularının dairesi
    alınır (ör. new_block 1. kat D6 wc-duş: duvar rasterindeki boşluk yüzünden D5'e düşüyordu). Dönüş: (daire, değişenler)"""
    daire = dict(daire)
    komsu = {}
    for i, j, c in kapilar:
        komsu.setdefault(i, set()).add(j)
        komsu.setdefault(j, set()).add(i)
    degisen = []
    for _ in range(3):
        oldu = False
        for i, r in enumerate(rooms):
            if ortak_mi(r['name']) or i not in komsu:
                continue
            ds = {daire.get(j) for j in komsu[i] if not ortak_mi(rooms[j]['name'])}
            ds.discard(None)
            if len(ds) == 1:
                d = next(iter(ds))
                if daire.get(i) != d:
                    degisen.append((r['name'], daire.get(i), d))
                    daire[i] = d
                    oldu = True
        if not oldu:
            break
    return daire, degisen


def tasi(bilgi, dx, dy):
    """kat analizini (dx, dy) ile ötelenmiş kopya olarak döndür (kontrol edilen çizim koordinatları)."""
    from shapely.affinity import translate
    t = lambda g: translate(g, dx, dy)
    b = dict(bilgi)
    b['pencere'] = (bilgi['pencere'][0] + dx, bilgi['pencere'][1] + dy, bilgi['pencere'][2] + dx, bilgi['pencere'][3] + dy)
    b['rooms'] = [dict(r, poly=t(r['poly']), xy=(r['xy'][0] + dx, r['xy'][1] + dy)) for r in bilgi['rooms']]
    ad = {id(r['poly']): i for i, r in enumerate(bilgi['rooms'])}
    b['fx'] = []
    for f in bilgi['fx']:
        g = dict(f, c=(f['c'][0] + dx, f['c'][1] + dy))
        if f.get('mahal') is not None:
            g['mahal'] = b['rooms'][ad[id(f['mahal']['poly'])]]
        b['fx'].append(g)
    b['cols'] = [t(c) for c in bilgi['cols']]
    b['daire_poly'] = {n: t(g) for n, g in bilgi['daire_poly'].items()}
    b['daire_poly_ic'] = {n: t(g) for n, g in bilgi['daire_poly_ic'].items()}
    b['ortak_poly'] = t(bilgi['ortak_poly'])
    b['bina'] = t(bilgi['bina'])
    b['tohum'] = [((p[0] + dx, p[1] + dy), n) for p, n in bilgi['tohum']]
    b['inisler'] = [(p[0] + dx, p[1] + dy) for p in bilgi['inisler']]
    b['labs'] = [(x + dx, y + dy, s) for x, y, s in bilgi['labs']]
    b['dxdy'] = (dx, dy)
    b['kaynak_pencere'] = tuple(bilgi['pencere'])
    b['taramalar'] = [t(g) for g in bilgi.get('taramalar', [])]
    b['pencereler'] = [((c[0] + dx, c[1] + dy), s) for c, s in bilgi.get('pencereler', [])]
    b['mek_havl'] = [(c[0] + dx, c[1] + dy) for c in bilgi.get('mek_havl', [])]
    b['mimari_makine'] = [(k, t(g), s) for k, g, s in bilgi.get('mimari_makine', [])]
    b['kapilar'] = [(i, j, (c[0] + dx, c[1] + dy)) for i, j, c in bilgi.get('kapilar', [])]
    b['mimari_yazi'] = [((a[1][0][0] + dx, a[1][0][1] + dy), a[2][0], a[2][1], a[2][2])
                        for a in bilgi['R'] if a[0] == 'T']
    return b
