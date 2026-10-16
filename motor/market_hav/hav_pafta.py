# -*- coding: utf-8 -*-
"""market_hav/hav_pafta.py — kullanıcının havalandırma çizimini temiz mimariye oturtur, paftalar, detayları ekler.

Girdi : proje/market_havalandirma/girdi/temiz_mimari.dxf(.xz)   — kullanıcının temiz mimarisi (olduğu gibi kalır)
        proje/market_havalandirma/girdi/hav_kanal.dxf           — ayikla.py çıktısı (temiz koordinatında, sınıflı)
Çıktı : proje/market_havalandirma/MARKET_HAVALANDIRMA_PROJESI.dxf

Adımlar
  1. Temiz mimari açılır; mimari katmanlar griye (8) alınır, kolon katmanları (S-CONC / S-HTCH / S-STEL) aynen kalır.
  2. Kanallar: U → MTY-UFLEME-KANALI (20), D → MTY-DONUS-KANALI (4), S → MTY-CIHAZ (135); yazılar sınıfına göre
     MTY-UFLEME-CAP (21) / MTY-DONUS-CAP (110). Kanal tasarımı (ölçü, debi, güzergâh) kullanıcınındır, değiştirilmez.
  3. Temiz mimarideki yeni kolon aksı nedeniyle kolona çarpan sistemler bütün olarak (santral + kanal + yazı) en küçük
     ötelemeyle kaydırılır (3. sistem +190 x, 4. sistem −20 y); sonrası kolon çakışması 0.
  4. Yazı çakışmaları (yazı–yazı, yazı–kanal, yazı–kolon) en yakın boş yere taşınarak giderilir; kancalı etiketlerde kanca ucu da taşınır.
  5. Paftalar (1/100 şerit): ANTET (×2) | VAZİYET PLANI 1/200 | ZEMİN KAT HAVALANDIRMA PLANI 1/100 (+ lejant, cihaz listesi,
     kanal hız tablosu) | 1. KAT PLANI 1/100 | HAVALANDIRMA TESİSATI DETAYLARI (+ notlar).
"""
import lzma
import math
import os
import shutil
import sys
from collections import Counter, defaultdict

import ezdxf
from ezdxf import bbox as _bb
from ezdxf.enums import TextEntityAlignment as TA
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

BURASI = os.path.dirname(os.path.abspath(__file__))
DEPO = os.path.abspath(os.path.join(BURASI, '..', '..'))
sys.path.insert(0, BURASI)
sys.path.insert(0, os.path.join(DEPO, 'motor', 'sihhi2'))
import antet as AN          # noqa: E402
import detaylar as DT       # noqa: E402

PROJE = os.path.join(DEPO, 'proje', 'market_havalandirma')
GIRDI_TEMIZ = os.path.join(PROJE, 'girdi', 'temiz_mimari.dxf')
GIRDI_KANAL = os.path.join(PROJE, 'girdi', 'hav_kanal.dxf')
CIKTI = os.path.join(PROJE, 'MARKET_HAVALANDIRMA_PROJESI.dxf')

# --------------------------------------------------------------------------------------------- katmanlar
K_U, K_UC = 'MTY-UFLEME-KANALI', 'MTY-UFLEME-CAP'
K_D, K_DC = 'MTY-DONUS-KANALI', 'MTY-DONUS-CAP'
K_S = 'MTY-CIHAZ'
K_LEJ = 'ROTAS-HAV-LEJANT'
K_TAB = 'ROTAS-HAV-TABLO'
K_NOT = 'ROTAS-HAV-NOT'
YENI_KATMAN = {K_U: 20, K_UC: 21, K_D: 4, K_DC: 110, K_S: 135, K_LEJ: 7, K_TAB: 7, K_NOT: 7}
KOLON_KATMAN = ('S-CONC', 'S-HTCH', 'S-STEL')
SINIF_KAT = {'U': K_U, 'D': K_D, 'S': K_S}
SINIF_YAZI = {'U': K_UC, 'D': K_DC, 'S': K_S}

# sistem bölgeleri (temiz x) ve kolon nedeniyle öteleme
def sistem_no(x):
    return 1 if x < 57000 else 2 if x < 61300 else 3 if x < 65900 else 4


SISTEM_OTELEME = {3: (190.0, 0.0), 4: (0.0, -20.0)}

# pafta şeridi (1/100)
Y0, SH = -600.0, 9900.0
PAFTALAR = [  # (ad, x0, x1, başlık)
    ('ANTET', 26200.0, 28500.0, None),
    ('VAZIYET', 28500.0, 44000.0, 'VAZİYET PLANI  ÖLÇEK : 1/200'),
    ('ZEMIN', 44000.0, 75600.0, 'ZEMİN KAT HAVALANDIRMA PLANI  ÖLÇEK : 1/100'),
    ('KAT1', 75600.0, 99000.0, '1. KAT PLANI  ÖLÇEK : 1/100'),
    ('DETAY', 99000.0, 113000.0, 'HAVALANDIRMA TESİSATI DETAYLARI'),
]
H_BASLIK = 80.0
SILINECEK_BASLIK = {'ZEMİN KAT PLANI', 'Ö: 1/100', '1. KAT PLANI'}

BILGI = {
    'proje_turu': 'HAVALANDIRMA TESİSATI PROJESİ',
    'il': '-', 'ilce': '-', 'belediye': '-', 'mahalle': '-', 'pafta': '-', 'ada': '-', 'parsel': '-',
    'proje_no': '-', 'emsal': '0.80',
    'yapi_sahibi': '-', 'yapi_sahibi_adres': '',
    'yapi_sistemi': 'BA / ÇELİK', 'yapi_sinifi': '-', 'bina_maliyeti': '-', 'bagimsiz_bolum': '11', 'kat_sayisi': '2',
    'insaat_alani': '23.426,4', 'yapim_suresi': '-', 'kullanma_amaci': 'İŞ MERKEZİ',
}


def log(*a):
    print('[hav]', *a, flush=True)


def bb(e):
    try:
        b = _bb.extents([e], fast=True)
        return (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y) if b.has_data else None
    except Exception:
        return None


def yazi_kutu(t):
    """TEXT dünya kutusu (arial genişliği ile, döndürmesiz yazılar)."""
    s = t.dxf.text
    h = t.dxf.height
    w = AN.yazi_genislik(s, h, t.dxf.get('width', 1.0))
    if t.dxf.halign or t.dxf.valign:
        x, y = t.dxf.align_point[0], t.dxf.align_point[1]
        ax = {0: 0, 1: 0.5, 2: 1, 4: 0.5}.get(t.dxf.halign, 0)
        ay = {0: 0, 1: 0, 2: 0.5, 3: 1}.get(t.dxf.valign, 0)
    else:
        x, y = t.dxf.insert[0], t.dxf.insert[1]
        ax = ay = 0
    return (x - ax * w, y - ay * h, x + (1 - ax) * w, y + (1 - ay) * h)


# ============================================================================================ 1. mimari
def mimari_ac():
    if not os.path.exists(GIRDI_TEMIZ):
        with lzma.open(GIRDI_TEMIZ + '.xz') as f, open(GIRDI_TEMIZ, 'wb') as g:
            shutil.copyfileobj(f, g)
    doc = ezdxf.readfile(GIRDI_TEMIZ)
    msp = doc.modelspace()
    sil = []
    for e in msp.query('TEXT MTEXT'):
        s = e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()
        if s.strip() in SILINECEK_BASLIK:
            sil.append(e)
    for e in sil:
        msp.delete_entity(e)
    for L in doc.layers:
        if L.dxf.name in KOLON_KATMAN or L.dxf.name in ('0', 'Defpoints'):
            continue
        L.color = 8
    log('mimari:', len(msp), 'varlık; silinen eski başlık', len(sil))
    return doc


def katmanlari_hazirla(doc):
    AN.hazirla(doc)
    DT.katmanlar(doc)
    for ad, renk in YENI_KATMAN.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk)


def kolonlar(doc):
    out = []
    for e in doc.modelspace().query('LWPOLYLINE[layer=="S-CONC"]'):
        p = [tuple(q) for q in e.get_points('xy')]
        if len(p) >= 3:
            out.append(Polygon(p).buffer(0))
    return out


# ============================================================================================ 2. kanallar
def geom(e):
    t = e.dxftype()
    if t == 'LWPOLYLINE':
        p = [tuple(q) for q in e.get_points('xy')]
        if e.closed and len(p) > 2:
            p.append(p[0])
        return LineString(p) if len(p) > 1 else Point(p[0])
    if t == 'CIRCLE':
        return Point(e.dxf.center[0], e.dxf.center[1]).buffer(e.dxf.radius).exterior
    return None


def kanallari_ekle(doc):
    src = ezdxf.readfile(GIRDI_KANAL).modelspace()
    msp = doc.modelspace()
    ogeler = []      # dict(e, sinif, sistem)
    for e in src:
        sinif = e.dxf.layer
        b = bb(e)
        cx = (b[0] + b[2]) / 2
        c = e.copy()
        msp.add_entity(c)
        ogeler.append(dict(e=c, sinif=sinif, sistem=sistem_no(cx)))
    # yazı ve kanca sınıfı: kanca → dokunduğu kanal; yazı → kancası ya da en yakın kanal
    kanallar = [o for o in ogeler if o['sinif'] in ('U', 'D') and o['e'].dxftype() == 'LWPOLYLINE']
    for o in kanallar:
        o['g'] = geom(o['e'])
    agac = STRtree([o['g'] for o in kanallar])

    def en_yakin_sinif(g, ust=400.0):
        i = agac.nearest(g)
        o = kanallar[i]
        return o['sinif'] if o['g'].distance(g) < ust else 'S'

    kancalar = [o for o in ogeler if o['sinif'] == 'L']
    yazilar = [o for o in ogeler if o['sinif'] == 'T']
    for k in kancalar:
        p = [tuple(q) for q in k['e'].get_points('xy')]
        # kanal tarafındaki uç: kanala daha yakın olan uç
        d = [kanallar[agac.nearest(Point(q))]['g'].distance(Point(q)) for q in p]
        uc = p[0] if d[0] <= d[1] else p[1]
        diger = p[1] if d[0] <= d[1] else p[0]
        k['uc'], k['bas'] = uc, diger
        k['s'] = en_yakin_sinif(Point(uc), 60.0)
    for t in yazilar:
        x0, y0, x1, y1 = yazi_kutu(t['e'])
        t['kutu'] = (x0, y0, x1, y1)
        # kancası var mı: kancanın yazı tarafı ucu yazı kutusuna 60 birimden yakın
        en, dmin = None, 60.0
        for k in kancalar:
            dd = box(x0, y0, x1, y1).distance(Point(k['bas']))
            if dd < dmin:
                en, dmin = k, dd
        if en is not None and 'yazi' not in en:
            en['yazi'] = t
            t['kanca'] = en
            t['s'] = en['s']
        else:
            t['s'] = 'S' if any(s in t['e'].dxf.text for s in ('kW', '40.000')) else \
                en_yakin_sinif(box(x0, y0, x1, y1), 300.0)
    for k in kancalar:
        if 'yazi' not in k:
            k['s'] = k.get('s', 'S')
    # katman ve stil
    for o in ogeler:
        e = o['e']
        if o['sinif'] in SINIF_KAT:
            e.dxf.layer = SINIF_KAT[o['sinif']]
        elif o['sinif'] == 'L':
            e.dxf.layer = SINIF_YAZI[o['s']]
        elif o['sinif'] == 'T':
            e.dxf.layer = SINIF_YAZI[o['s']]
            e.dxf.style = AN.STIL
            e.dxf.width = 0.8
    # kolon nedeniyle sistem ötelemesi
    for o in ogeler:
        dx, dy = SISTEM_OTELEME.get(o['sistem'], (0.0, 0.0))
        if dx or dy:
            o['e'].translate(dx, dy, 0)
            if 'uc' in o:
                o['uc'] = (o['uc'][0] + dx, o['uc'][1] + dy)
                o['bas'] = (o['bas'][0] + dx, o['bas'][1] + dy)
            if 'kutu' in o:
                k = o['kutu']
                o['kutu'] = (k[0] + dx, k[1] + dy, k[2] + dx, k[3] + dy)
    for o in kanallar:
        o['g'] = geom(o['e'])
    log('kanal öğeleri:', Counter(o['sinif'] for o in ogeler))
    return ogeler, kanallar, yazilar, kancalar


def kanal_izleri(kanallar):
    """Kanal ayak izi: sistem+sınıf bazında polygonize edilmiş yüzler + çizgiler."""
    grup = defaultdict(list)
    for o in kanallar:
        grup[(o['sistem'], o['sinif'])].append(o['g'])
    yuz = []
    for gs in grup.values():
        yuz += [f for f in polygonize(unary_union(gs)) if f.area < 4e6]
    return yuz


def sarkan_uc_kirp(kanallar, ogeler):
    """Kullanıcı çiziminde aynı sistem çizgisini 50–150 cm geçip boşta kalan çizgi uçlarını (taşma) kesişme
    noktasına kadar kırpar. Flanş işaretleri (≈30 cm taşma) korunur."""
    n = 0
    gs = [o['g'] for o in kanallar]
    tr = STRtree(gs)
    cihaz = [geom(o['e']) for o in ogeler if o['sinif'] == 'S' and o['e'].dxftype() == 'LWPOLYLINE']
    for o in kanallar:
        e = o['e']
        if e.dxftype() != 'LWPOLYLINE' or len(e) != 2:
            continue
        p = [tuple(q) for q in e.get_points('xy')]
        seg = LineString(p)
        degisti = False
        for i in (0, 1):
            uc = Point(p[i])
            komsu = [gs[j] for j in tr.query(uc.buffer(1)) if gs[j] is not o['g']]
            if any(g.distance(uc) < 1 for g in komsu) or any(g.distance(uc) < 2 for g in cihaz):
                continue                                   # uç bir çizgiye bağlı
            kes = []
            for j in tr.query(seg):
                g = gs[j]
                if g is o['g'] or kanallar[j]['sinif'] != o['sinif']:
                    continue
                q = g.intersection(seg)
                for pt in getattr(q, 'geoms', [q]):
                    if pt.geom_type == 'Point':
                        kes.append((pt.distance(uc), pt))
            if kes:
                d, pt = min(kes, key=lambda t: t[0])
                if 50 < d < 150:
                    log('  taşma kırpıldı', [round(v) for v in p[i]], '→', round(pt.x), round(pt.y))
                    p[i] = (pt.x, pt.y)
                    n += 1
                    degisti = True
        if degisti:
            e.set_points(p, format='xy')
            o['g'] = LineString(p)
    log('kırpılan taşan uç:', n)


def cift_cizgi_sil(doc, kanallar):
    """Aynı sınıftaki başka bir kanal çizgisinin üstünde kalan (çakışık, kopya) 2 noktalı çizgileri siler."""
    msp = doc.modelspace()
    gs = [o['g'] for o in kanallar]
    tr = STRtree(gs)
    sil = []
    for i, o in enumerate(kanallar):
        e = o['e']
        if e.dxftype() != 'LWPOLYLINE' or len(e) != 2 or o['g'].length < 5:
            continue
        for j in tr.query(o['g']):
            if j == i or kanallar[j]['sinif'] != o['sinif'] or any(j == k for k, _ in sil):
                continue
            if o['g'].within(gs[j].buffer(0.5)):
                sil.append((i, o))
                break
    for _, o in sil:
        msp.delete_entity(o['e'])
        kanallar.remove(o)
    log('silinen kopya kanal çizgisi:', len(sil))


def kolon_kontrol(kanallar, kolon):
    yuz = kanal_izleri(kanallar) + [o['g'] for o in kanallar]
    kol = [c.buffer(2) for c in kolon]
    t = STRtree(kol)
    n = 0
    for g in yuz:
        for i in t.query(g):
            if g.intersects(kol[i]):
                n += 1
    return n


# ============================================================================================ 3. yazı çakışmaları
def yazi_duzelt(doc, yazilar, kanallar, kolon):
    """Kanal yazılarını birbirine, kanallara, kolonlara ve mimari yazılara binmeyecek yere taşır."""
    msp = doc.modelspace()
    engel = [g.buffer(3) for g in kanal_izleri(kanallar)] + [o['g'].buffer(4) for o in kanallar] + \
            [c.buffer(5) for c in kolon]
    # mimari yazı kutuları
    for e in msp.query('TEXT'):
        if e.dxf.layer.startswith('MTY-'):
            continue
        try:
            k = yazi_kutu(e)
            if k[0] > 50000 and k[2] < 75000:
                engel.append(box(*k))
        except Exception:
            pass
    for e in msp.query('INSERT'):
        if e.dxf.layer.startswith('MTY-') or not e.dxf.layer.startswith('A-ANNO'):
            continue
        b = bb(e)
        if b and b[0] > 50000 and b[2] < 75000 and (b[2] - b[0]) * (b[3] - b[1]) < 4e5:
            engel.append(box(*b))
    for e in msp.query('MTEXT'):
        b = bb(e)
        if b and b[0] > 50000 and b[2] < 75000:
            engel.append(box(*b))
    # mimari duvar / doğrama / kapı / merdiven çizgileri ve diğer etiketlerin kanca çizgileri
    MIM = ('A-WALL', 'A-GLAZ', 'A-DOOR', 'A-FLOR-STRS', 'A-ANNO-DIMS', 'A-ANNO-IDEN', 'A-FLOR-FIXT')
    for e in msp.query('LINE LWPOLYLINE ARC CIRCLE'):
        if not e.dxf.layer.startswith(MIM):
            continue
        b = bb(e)
        if not b or b[0] < 50000 or b[2] > 75000:
            continue
        try:
            if e.dxftype() == 'LINE':
                g = LineString([tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]])
            elif e.dxftype() == 'LWPOLYLINE':
                g = geom(e)
            else:
                g = box(*b)
            engel.append(g.buffer(2))
        except Exception:
            pass
    kanca_g = {id(t): LineString([tuple(q) for q in t['kanca']['e'].get_points('xy')])
               for t in yazilar if t.get('kanca') is not None}
    tum_kanca = [g for g in kanca_g.values()]
    agac = STRtree(engel)
    yerlesik = []
    tasinan = 0
    adimlar = sorted({(dx, dy) for dx in range(-300, 301, 20) for dy in range(-200, 201, 10)},
                     key=lambda d: (abs(d[0]) * 0.6 + abs(d[1]), abs(d[1])))
    sirali = sorted(yazilar, key=lambda t: (t['kutu'][1], t['kutu'][0]))
    for t in sirali:
        k0 = box(*t['kutu']).buffer(6)
        for dx, dy in adimlar:
            k = affinity.translate(k0, dx, dy)
            if any(k.intersects(engel[i]) for i in agac.query(k)):
                continue
            if any(k.intersects(y) for y in yerlesik):
                continue
            kendi = kanca_g.get(id(t))
            if any(k.intersects(g) for g in tum_kanca if g is not kendi):
                continue
            break
        else:
            dx = dy = 0
            k = k0
            log('UYARI: yer bulunamadı', t['e'].dxf.text)
        if dx or dy:
            tasinan += 1
            t['e'].translate(dx, dy, 0)
            kb = t['kutu']
            t['kutu'] = (kb[0] + dx, kb[1] + dy, kb[2] + dx, kb[3] + dy)
            kc = t.get('kanca')
            if kc is not None:                       # kancanın yazı ucunu taşı, kanal ucu sabit
                p = [tuple(q) for q in kc['e'].get_points('xy')]
                yeni = [(q[0] + dx, q[1] + dy) if math.dist(q, kc['bas']) < 1 else q for q in p]
                kc['e'].set_points(yeni, format='xy')
                kc['bas'] = (kc['bas'][0] + dx, kc['bas'][1] + dy)
        yerlesik.append(k)
    log('taşınan yazı:', tasinan, '/', len(yazilar))
    return tasinan


def yazi_cakisma_say(yazilar, kanallar, kolon):
    kut = [box(*t['kutu']) for t in yazilar]
    n_yy = sum(1 for i in range(len(kut)) for j in range(i + 1, len(kut)) if kut[i].intersects(kut[j]))
    yuz = kanal_izleri(kanallar) + [o['g'] for o in kanallar]
    tr = STRtree(yuz)
    n_yk = sum(1 for k in kut if any(k.intersects(yuz[i]) for i in tr.query(k)))
    tk = STRtree(kolon)
    n_yc = sum(1 for k in kut if any(k.intersects(kolon[i]) for i in tk.query(k)))
    return n_yy, n_yk, n_yc


def kanca_uzat(kancalar, kanallar):
    """Kanal ucu kanala ulaşmayan (15–100 birim kısa) kancaları en yakın kanal çizgisine uzatır."""
    from shapely.ops import nearest_points
    gs = [o['g'] for o in kanallar]
    tr = STRtree(gs)
    n = 0
    for k in kancalar:
        p = Point(k['uc'])
        g = gs[tr.nearest(p)]
        d = g.distance(p)
        if 15 < d < 100:
            q = nearest_points(g, p)[0]
            pts = [tuple(v) for v in k['e'].get_points('xy')]
            pts = [(q.x, q.y) if math.dist(v, k['uc']) < 1 else v for v in pts]
            k['e'].set_points(pts, format='xy')
            k['uc'] = (q.x, q.y)
            n += 1
    log('uzatılan kanca:', n)


def kanca_kontrol(kancalar, kanallar):
    """Her kancanın kanal ucu bir kanala değiyor mu (≤ 15)."""
    gs = [o['g'] for o in kanallar] + kanal_izleri(kanallar)
    tr = STRtree(gs)
    bos = 0
    for k in kancalar:
        p = Point(k['uc'])
        if gs[tr.nearest(p)].distance(p) > 15:
            bos += 1
            log('  boşta kanca:', [round(v) for v in k['uc']], round(gs[tr.nearest(p)].distance(p)))
    return bos


# ============================================================================================ 3b. kesişen kanallar
K_GIZLI = {'U': K_U + '-GIZLI', 'D': K_D + '-GIZLI'}


def gizli_kesisme(doc, kanallar):
    """Farklı sistem sınıfı (üfleme/dönüş) kanalları kesiştiğinde yatay branşmanın ana kolon içinde kalan
    kısmı alttan geçer: o kısım ...-GIZLI katmanında kesikli çizilir (ROTAŞ kuralı)."""
    msp = doc.modelspace()
    for k, ad in K_GIZLI.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=YENI_KATMAN[SINIF_KAT[k]], linetype='DASHED' if 'DASHED' in doc.linetypes
                           else 'Continuous')
    # diğer sınıfın uzun düşey çizgileri (ana kolon kenarları)
    dusey = {'U': [], 'D': []}
    for o in kanallar:
        e = o['e']
        if e.dxftype() != 'LWPOLYLINE':
            continue
        p = [tuple(q) for q in e.get_points('xy')]
        for a, b_ in zip(p, p[1:]):
            if abs(a[0] - b_[0]) < 1 and abs(a[1] - b_[1]) > 300:
                dusey[o['sinif']].append(LineString([a, b_]))
    agac = {k: STRtree(v) for k, v in dusey.items()}
    n = 0
    for o in list(kanallar):
        e = o['e']
        if e.dxftype() != 'LWPOLYLINE':
            continue
        diger = 'D' if o['sinif'] == 'U' else 'U'
        pts = [tuple(q) for q in e.get_points('xy')]
        if e.closed:
            pts.append(pts[0])
        yeni_duz, yeni_gizli = [], []
        degisti = False
        for a, b_ in zip(pts, pts[1:]):
            seg = LineString([a, b_])
            yatay = abs(b_[1] - a[1]) < 1 and abs(b_[0] - a[0]) > 1
            xs = []
            if yatay:
                for i in agac[diger].query(seg):
                    q = dusey[diger][i].intersection(seg)
                    if not q.is_empty and q.geom_type == 'Point':
                        xs.append(q.x)
            xs = sorted(set(round(x, 3) for x in xs))
            araliklar = [(xs[i], xs[i + 1]) for i in range(len(xs) - 1) if xs[i + 1] - xs[i] <= 260]
            if not araliklar:
                yeni_duz.append([a, b_])
                continue
            degisti = True
            y = a[1]
            x0, x1 = sorted((a[0], b_[0]))
            imlec = x0
            for u, v in araliklar:
                if u > imlec + 0.5:
                    yeni_duz.append([(imlec, y), (u, y)])
                yeni_gizli.append([(u, y), (v, y)])
                imlec = v
            if x1 > imlec + 0.5:
                yeni_duz.append([(imlec, y), (x1, y)])
        if not degisti:
            continue
        n += 1
        kat = e.dxf.layer
        for c in yeni_duz:
            msp.add_lwpolyline(c, dxfattribs={'layer': kat})
        for c in yeni_gizli:
            msp.add_lwpolyline(c, dxfattribs={'layer': K_GIZLI[o['sinif']], 'ltscale': 15.0})
        msp.delete_entity(e)
        kanallar.remove(o)
    log('kesişmede kesikli çizilen kanal çizgisi:', n)


# ============================================================================================ 4. santral etiketleri
def santral_etiket(doc, ogeler):
    msp = doc.modelspace()
    govde = []
    for o in ogeler:
        e = o['e']
        if o['sinif'] == 'S' and e.dxftype() == 'LWPOLYLINE' and len(e) in (4, 5):
            b = bb(e)
            if 700 < b[2] - b[0] < 950 and 450 < b[3] - b[1] < 650:
                govde.append(b)
    govde.sort()
    for i, b in enumerate(govde, 1):
        t = msp.add_text(f'KS-{i}', height=50, dxfattribs={'layer': K_S, 'style': AN.STIL, 'width': 0.85})
        t.set_placement(((b[0] + b[2]) / 2, b[3] + 25), align=TA.BOTTOM_CENTER)
        t = msp.add_text('PAKET TİP KLİMA SANTRALİ', height=35,
                         dxfattribs={'layer': K_S, 'style': AN.STIL, 'width': 0.8})
        t.set_placement(((b[0] + b[2]) / 2, b[3] + 120), align=TA.BOTTOM_CENTER)
    return govde


# ============================================================================================ 5. paftalar
def cerceve(msp, x0, y0, x1, y1, kat='ROTAS-PAFTA'):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': kat})


def yazi(msp, s, x, y, h, al='BL', kat=K_LEJ, w=0.85, kutular=None):
    t = msp.add_text(s, height=h, dxfattribs={'layer': kat, 'style': AN.STIL, 'width': w})
    t.set_placement((x, y), align=AN.AL[al])
    if kutular is not None:
        gw = AN.yazi_genislik(s, h, w)
        ax = {'L': 0, 'C': 0.5, 'R': 1}[al[1]]
        ay = {'B': 0, 'M': 0.5, 'T': 1}[al[0]]
        kutular.append((x - ax * gw, y - ay * h, x + (1 - ax) * gw, y + (1 - ay) * h, s))
    return t


def antet_blok(doc):
    blk = doc.blocks.new('ROTAS-ANTET-HAV')
    AN.antet_ciz(blk, 0, 0, BILGI, BILGI['proje_turu'])
    return blk


def tablo(msp, x0, y0, sutunlar, satirlar, baslik, h=35, sat_h=90, kutular=None):
    """Basit çerçeveli tablo; (x0, y0) sol üst. sutunlar: genişlik listesi. Dönüş: alt y."""
    W = sum(sutunlar)
    yazi(msp, baslik, x0 + W / 2, y0 + 30, 45, 'BC', K_TAB, kutular=kutular)
    y = y0
    for i, row in enumerate(satirlar):
        msp.add_lwpolyline([(x0, y), (x0 + W, y), (x0 + W, y - sat_h), (x0, y - sat_h)], close=True,
                           dxfattribs={'layer': K_TAB})
        x = x0
        for j, (w, s) in enumerate(zip(sutunlar, row)):
            if j:
                msp.add_line((x, y), (x, y - sat_h), dxfattribs={'layer': K_TAB})
            yazi(msp, s, x + w / 2, y - sat_h / 2, h if i else h * 0.9, 'MC', K_TAB, kutular=kutular)
            x += w
        y -= sat_h
    return y


HIZ_TABLOSU = [('1600x1200', 39900), ('1200x900', 22800), ('1000x800', 8550), ('900x600', 5700),
               ('900x450', 5700), ('600x450', 2850)]


def lejant_ve_tablolar(doc, x0, y_ust, santraller, kutular):
    """Zemin kat paftasının sol bölümü: LEJANT, CİHAZ LİSTESİ, KANAL HIZ KONTROL TABLOSU."""
    msp = doc.modelspace()
    W = 5600.0
    # ---- LEJANT
    sat = [('band', K_U, 'ÜFLEME (TAZE HAVA) KANALI'), ('band', K_D, 'DÖNÜŞ (EMİŞ) KANALI'),
           ('menfez', K_U, 'KANAL ALTI YUVARLAK ÜFLEME MENFEZİ'), ('menfez', K_D, 'KANAL ALTI YUVARLAK EMİŞ MENFEZİ'),
           ('etiket', K_UC, 'KANAL ÖLÇÜSÜ (mm) / MENFEZ DEBİSİ'), ('kanca', K_UC, 'KANAL DEBİSİ (m³/h)'),
           ('santral', K_S, 'PAKET TİP KLİMA SANTRALİ (KS)')]
    sat_h = 170.0
    h_lej = 140 + len(sat) * sat_h + 60
    yb = y_ust - h_lej
    cerceve(msp, x0, yb, x0 + W, y_ust, K_LEJ)
    yazi(msp, 'HAVALANDIRMA TESİSATI LEJANTI', x0 + W / 2, y_ust - 70, 55, 'MC', kutular=kutular)
    msp.add_line((x0, y_ust - 140), (x0 + W, y_ust - 140), dxfattribs={'layer': K_LEJ})
    for i, (tip, kat, s) in enumerate(sat):
        yc = y_ust - 140 - 60 - i * sat_h - sat_h / 2 + 30
        sx = x0 + 150
        if tip == 'band':
            msp.add_lwpolyline([(sx, yc - 30), (sx + 900, yc - 30)], dxfattribs={'layer': kat})
            msp.add_lwpolyline([(sx, yc + 30), (sx + 900, yc + 30)], dxfattribs={'layer': kat})
            msp.add_line((sx + 450, yc - 30), (sx + 450, yc + 30), dxfattribs={'layer': kat})
        elif tip == 'menfez':
            msp.add_lwpolyline([(sx, yc - 30), (sx + 900, yc - 30)], dxfattribs={'layer': kat})
            msp.add_lwpolyline([(sx, yc + 30), (sx + 900, yc + 30)], dxfattribs={'layer': kat})
            msp.add_circle((sx + 450, yc), 28, dxfattribs={'layer': kat})
        elif tip == 'etiket':
            yazi(msp, '600x450', sx + 450, yc + 10, 40, 'BC', kat, 0.8)
            yazi(msp, '2850m3/h', sx + 450, yc - 10, 40, 'TC', kat, 0.8)
        elif tip == 'kanca':
            msp.add_lwpolyline([(sx + 200, yc - 50), (sx + 320, yc + 15)], dxfattribs={'layer': kat})
            yazi(msp, '5700m3/h', sx + 330, yc + 15, 40, 'BL', kat, 0.8)
        elif tip == 'santral':
            msp.add_lwpolyline([(sx + 250, yc - 50), (sx + 650, yc - 50), (sx + 650, yc + 50), (sx + 250, yc + 50)],
                               close=True, dxfattribs={'layer': kat})
            yazi(msp, 'KS', sx + 450, yc, 40, 'MC', kat)
        yazi(msp, s, x0 + 1200, yc, 40, 'ML', kutular=kutular)
    # ---- CİHAZ LİSTESİ
    y = yb - 250
    satirlar = [('NO', 'CİHAZ', 'HAVA DEBİSİ (m³/h)', 'KAPASİTE (kW)', 'ADET')]
    for i in range(len(santraller)):
        satirlar.append((f'KS-{i + 1}', 'PAKET TİP KLİMA SANTRALİ', '40.000', '200', '1'))
    y = tablo(msp, x0, y, [500, 2000, 1300, 1100, 700], satirlar, 'CİHAZ LİSTESİ', kutular=kutular)
    # ---- KANAL HIZ KONTROL TABLOSU
    y -= 250
    satirlar = [('KANAL ÖLÇÜSÜ (mm)', 'DEBİ (m³/h)', 'KESİT (m²)', 'HIZ (m/s)')]
    for s, q in HIZ_TABLOSU:
        a, b_ = [int(v) for v in s.split('x')]
        A = a * b_ / 1e6
        satirlar.append((s, f'{q:,}'.replace(',', '.'), f'{A:.2f}'.replace('.', ','),
                         f'{q / 3600 / A:.2f}'.replace('.', ',')))
    y = tablo(msp, x0, y, [1700, 1300, 1200, 1400], satirlar, 'KANAL HIZ KONTROL TABLOSU', kutular=kutular)
    yazi(msp, 'Debiler plan üzerindeki kanal etiketlerinden alınmıştır.', x0, y - 60, 32, 'TL', K_TAB,
         kutular=kutular)
    return y - 100


NOTLAR = [
    'Kanallar TS EN 1505 / TS EN 1507 standartlarına uygun galvaniz sacdan, DETAY-10 tablosundaki sac kalınlıklarıyla imal edilecektir.',
    'Kanal birleşimleri 30 mm flanş veya S sürgü ile yapılacak, tüm ek ve kenetler sızdırmazlık macunuyla kapatılacaktır.',
    'Kanallar en fazla 2,40 m aralıkla M10 dişli çubuk ve L profil ile tavana askılanacaktır (DETAY-1).',
    'Üfleme ve dönüş kanalları 19 mm elastomerik kauçuk köpüğü ile yalıtılacak, bina dışındaki kanallar alüminyum sacla korunacaktır.',
    'Klima santrali ile kanal arasında titreşimi kesmek için 150 mm brandi (esnek bağlantı) kullanılacaktır (DETAY-9).',
    'Dirseklerde yönlendirici kanat kullanılacak, dirsek iç yarıçapı kanal genişliğinin yarısından az olmayacaktır.',
    'Her branşman çıkışına hacim ayar damperi konulacak, devreye almada menfez debileri ölçülerek balans ayarı yapılacaktır.',
    'Kanalların yangın bölmesi duvar ve döşemelerinden geçtiği yerlere yangın damperi konulacaktır.',
    'Santrallerin taze hava ve atış ağızlarına yağmur panjuru ve kuş teli takılacaktır (DETAY-8).',
    'Kanal güzergâhları uygulamadan önce mimari, statik ve elektrik projeleriyle yerinde kontrol edilecektir.',
    'Kanal ölçüleri mm, debiler m³/h olarak verilmiş olup ölçüler imalattan önce yerinde teyit edilecektir.',
    'Tüm cihazlar üretici montaj talimatlarına uygun monte edilecek ve devreye alma testleri yapılacaktır.',
]


def notlar(msp, x0, y0, x1, y1, kutular):
    cerceve(msp, x0, y0, x1, y1, DT.KAT_C)
    msp.add_line((x0, y1 - 110), (x1, y1 - 110), dxfattribs={'layer': DT.KAT_C})
    yazi(msp, 'NOTLAR', x0 + 40, y1 - 55, 45, 'ML', K_NOT, kutular=kutular)
    y = y1 - 230
    for no, s in enumerate(NOTLAR, 1):
        yazi(msp, f'{no}.', x0 + 60, y, 45, 'BL', K_NOT, kutular=kutular)
        yazi(msp, s, x0 + 200, y, 45, 'BL', K_NOT, kutular=kutular)
        y -= 160
    y -= 80
    for s in ('DİKKAT: MİMARİ PROJENİN ONAY AŞAMASINDA YAPILACAK DEĞİŞİKLİKTEN FEN İŞLERİ MD. BİLGİLENDİRİLMESİ',
              'BU PROJE MÜELLİFİN İZNİ OLMADAN YAYINLANAMAZ-ÇOĞALTILAMAZ-KULLANILAMAZ-DEĞİŞTİRİLEMEZ.'):
        yazi(msp, s, x0 + 60, y, 45, 'BL', K_NOT, kutular=kutular)
        y -= 120


def paftala(doc, santraller):
    msp = doc.modelspace()
    kutular = []
    for ad, x0, x1, baslik in PAFTALAR:
        cerceve(msp, x0, Y0, x1, Y0 + SH)
        if baslik:
            yazi(msp, baslik, (x0 + x1) / 2, Y0 + 120, H_BASLIK, 'BC', 'ROTAS-PAFTA-YAZI', 0.9, kutular)
    # antet ×2 (1/100 şeritte 1/50 antet ölçüsü)
    blk = antet_blok(doc)
    msp.add_blockref(blk.name, (26250.0, Y0 + 60), dxfattribs={'xscale': 2, 'yscale': 2, 'layer': 'ROTAS-ANTET'})
    # zemin kat sol bölüm: lejant + tablolar
    lejant_ve_tablolar(doc, 44250.0, Y0 + SH - 300, santraller, kutular)
    # detay paftası: 4 × 3 hücre (10 detay + notlar)
    dx0, dy0 = 99250.0, Y0 + 350
    kut = DT.detay_paftasi(msp, dx0, dy0)
    kutular += kut
    # son sıradaki iki boş hücre: NOTLAR
    notlar(msp, dx0 + 2 * 3400, dy0, dx0 + 4 * 3400 - 100, dy0 + 3000, kutular)
    return kutular


def kutu_cakisma(kutular):
    n = 0
    for i in range(len(kutular)):
        a = kutular[i]
        for j in range(i + 1, len(kutular)):
            b = kutular[j]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                n += 1
                log('  yazı çakışması:', a[4], '|', b[4])
    return n


# ============================================================================================ temiz çıktı
def temiz_kaydet(kaynak, yol):
    """AutoCAD'in açamadığı ilişkisel nesneler (ACDBASSOC*, DIMASSOC, MLEADER bağları) taşınmasın diye çıktı
    yeni bir R2010 belgesine aktarılır; MULTILEADER ve DIMENSION patlatılır (çizgi + yazı olarak aynı katmanda)."""
    from ezdxf.addons import Importer
    hedef = ezdxf.new('R2010', setup=True)
    hedef.header['$INSUNITS'] = 5
    hedef.header['$MEASUREMENT'] = 1
    imp = Importer(kaynak, hedef)
    imp.import_tables('*')
    tm = hedef.modelspace()
    normal, patlat = [], []
    for e in kaynak.modelspace():
        (patlat if e.dxftype() in ('MULTILEADER', 'DIMENSION', 'ACAD_PROXY_ENTITY') else normal).append(e)
    imp.import_entities(normal, tm)
    imp.finalize()
    n = 0
    for e in patlat:
        try:
            for v in e.virtual_entities():
                if v.dxftype() in ('MTEXT', 'TEXT') and v.dxf.get('style') not in hedef.styles:
                    v.dxf.style = 'Standard'
                v.dxf.layer = e.dxf.layer
                tm.add_entity(v)
                n += 1
        except Exception as ex:
            log('  patlatılamadı', e.dxftype(), ex)
    # geçersiz yazı stilleri: adı boş ya da dosya adı olan stil tablosu kayıtları AutoCAD'in açmasını engeller
    gecersiz = {st.dxf.name for st in hedef.styles if not st.dxf.name.strip() or st.dxf.name.lower().endswith('.shx')}
    duzeltilen = 0
    yerler = [tm] + [b for b in hedef.blocks]
    for yer in yerler:
        for e in yer:
            ler = [e] + (list(e.attribs) if e.dxftype() == 'INSERT' else [])
            for x in ler:
                if x.dxf.hasattr('style') and (x.dxf.style in gecersiz or x.dxf.style not in hedef.styles):
                    x.dxf.style = 'Standard'
                    duzeltilen += 1
                if x.dxf.hasattr('linetype') and x.dxf.linetype not in hedef.linetypes:
                    x.dxf.linetype = 'BYLAYER'
    kullanilan_lt = {e.dxf.linetype for yer in yerler for e in yer if e.dxf.hasattr('linetype')}
    kullanilan_lt |= {L.dxf.linetype for L in hedef.layers}
    for lt in list(hedef.linetypes):
        if lt.pattern_tags.is_complex_type() and lt.dxf.name not in kullanilan_lt:
            hedef.linetypes.remove(lt.dxf.name)
    for ad in gecersiz:
        try:
            hedef.styles.remove(ad)
        except Exception as ex:
            log('  stil silinemedi', repr(ad), ex)
    log('stil düzeltilen yazı:', duzeltilen, 'silinen geçersiz stil:', sorted(gecersiz))
    a = hedef.audit()
    log('temiz çıktı: aktarılan', len(normal), 'patlatılan', len(patlat), '→', n, '| audit hata', len(a.errors),
        'düzeltme', len(a.fixes))
    hedef.saveas(yol)


# ============================================================================================ ana akış
def main():
    doc = mimari_ac()
    katmanlari_hazirla(doc)
    kolon = kolonlar(doc)
    ogeler, kanallar, yazilar, kancalar = kanallari_ekle(doc)
    cift_cizgi_sil(doc, kanallar)
    sarkan_uc_kirp(kanallar, ogeler)
    n_kol = kolon_kontrol(kanallar, kolon)
    log('kanal–kolon çakışması:', n_kol)
    log('yazı çakışması önce (yazı-yazı, yazı-kanal, yazı-kolon):', yazi_cakisma_say(yazilar, kanallar, kolon))
    kanca_uzat(kancalar, kanallar)
    yazi_duzelt(doc, yazilar, kanallar, kolon)
    cak = yazi_cakisma_say(yazilar, kanallar, kolon)
    log('yazı çakışması sonra:', cak)
    log('boşta kanca ucu:', kanca_kontrol(kancalar, kanallar))
    gizli_kesisme(doc, kanallar)
    santraller = santral_etiket(doc, ogeler)
    kut = paftala(doc, santraller)
    n_p = kutu_cakisma(kut)
    log('pafta yazı çakışması:', n_p)
    # pafta dışı taşma kontrolü: her varlık bir pafta içinde mi
    disarida = 0
    for e in doc.modelspace():
        b = bb(e)
        if not b:
            continue
        if not any(x0 - 1 <= b[0] and b[2] <= x1 + 1 and Y0 - 1 <= b[1] and b[3] <= Y0 + SH + 1
                   for _, x0, x1, _ in PAFTALAR):
            disarida += 1
            if disarida <= 10:
                log('  pafta dışı:', e.dxftype(), e.dxf.layer, [round(v) for v in b])
    log('pafta dışında kalan varlık:', disarida)
    temiz_kaydet(doc, CIKTI)
    log('yazıldı:', CIKTI)
    return dict(kolon=n_kol, yazi=cak, pafta_yazi=n_p, disarida=disarida)


if __name__ == '__main__':
    main()
