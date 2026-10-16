# -*- coding: utf-8 -*-
"""market_hav/ayikla.py — kullanıcının havalandırma DXF'inden (eski mimari üstünde) kanal çizimini ayıklar,
temiz mimarinin koordinatına öteler ve sınıflar.

Girdi : havalanıdırma.dxf (kanallar A-ANNO-TEXT katmanında + tazehava/dönüşhava/manavüfleme/manavemiş blokları)
        temiz_mimari.dxf  (aynı mimarinin temizlenmiş, revize hâli)
Çıktı : proje/market_havalandirma/girdi/hav_kanal.dxf — temiz koordinatında, katmanlar:
        U = üfleme (taze/üfleme kanalı), D = dönüş (emiş kanalı), S = klima santrali, T = yazı, L = etiket kanca çizgisi
Öteleme: temiz = hav + (47244, 54361) — S-CONC kolonlarının 82/88'i birebir çakışıyor (döndürme/ölçek yok).

Kullanım: python3 ayikla.py HAV.dxf TEMIZ.dxf CIKTI.dxf
"""
import sys
import unicodedata
from collections import deque

import ezdxf
from ezdxf import bbox as _bb
from shapely.geometry import LineString, Point

DX, DY = 47244.0, 54361.0
BOLGE = (3000, -52800, 25000, -45700)          # hav koordinatında zemin kat planı
BLOK_SINIF = {'tazehava': 'U', 'manavüfleme': 'U', 'dönüşhava': 'D', 'manavemiş': 'D'}


def nfc(s):
    return unicodedata.normalize('NFC', s)


def bb(e):
    try:
        b = _bb.extents([e], fast=True)
        return (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y) if b.has_data else None
    except Exception:
        return None


def imza(e, dx=0.0, dy=0.0):
    t = e.dxftype()
    r = lambda v: (round((v[0] + dx) / 2) * 2, round((v[1] + dy) / 2) * 2)
    try:
        if t == 'LINE':
            a, b = sorted([r(e.dxf.start), r(e.dxf.end)])
            return (t, a, b)
        if t == 'LWPOLYLINE':
            return (t, tuple(sorted(r(p) for p in e.get_points('xy'))))
        if t in ('CIRCLE', 'ARC'):
            return (t, r(e.dxf.center), round(e.dxf.radius))
        if t == 'TEXT':
            return (t, e.dxf.text, r(e.dxf.insert))
    except Exception:
        return None
    return (t,)


def geom(e):
    t = e.dxftype()
    if t == 'LWPOLYLINE':
        p = [tuple(q) for q in e.get_points('xy')]
        if e.closed:
            p.append(p[0])
        return LineString(p) if len(p) > 1 else Point(p[0])
    if t == 'CIRCLE':
        return Point(e.dxf.center[0], e.dxf.center[1]).buffer(e.dxf.radius).exterior
    if t == 'LINE':
        return LineString([tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]])
    return None


def kanca_mi(e):
    """etiket kanca çizgisi: 2 noktalı, eğik polyline"""
    if e.dxftype() != 'LWPOLYLINE' or len(e) != 2:
        return False
    (x0, y0), (x1, y1) = [tuple(q) for q in e.get_points('xy')]
    return abs(x1 - x0) > 50 and abs(y1 - y0) > 100


def ayikla(hav_yol, temiz_yol):
    H = ezdxf.readfile(hav_yol)
    T = ezdxf.readfile(temiz_yol).modelspace()
    temiz_imza = set(imza(e) for e in T)
    ogeler = []                                   # (entity, sınıf|None)
    for e in H.modelspace():
        if e.dxf.layer != 'A-ANNO-TEXT':
            continue
        t = e.dxftype()
        if t == 'INSERT':
            k = BLOK_SINIF.get(nfc(e.dxf.name))
            if k:
                ogeler += [(v, k) for v in e.virtual_entities() if v.dxftype() in ('LWPOLYLINE', 'CIRCLE')]
            continue
        if t not in ('LWPOLYLINE', 'CIRCLE', 'TEXT'):
            continue
        b = bb(e)
        if not b or not (BOLGE[0] < b[0] and b[2] < BOLGE[2] and BOLGE[1] < b[1] and b[3] < BOLGE[3]):
            continue
        w, h = b[2] - b[0], b[3] - b[1]
        if w > 4000 or h > 6000:                                  # bina dış hattı
            continue
        if b[0] < 5500:                                           # sol bölüm: mimari bölücüler
            continue
        if t == 'LWPOLYLINE' and w < 60 and h < 70 and len(e) == 7:   # kot/kesit işaretleri
            continue
        if t == 'CIRCLE' and e.dxf.radius < 5:                    # yazı nokta işaretleri
            continue
        if t == 'LWPOLYLINE' and 21150 < b[0] < 22500 and -50100 < b[1] and b[3] < -47400 and len(e) >= 4:
            continue                                              # soğuk oda tezgahları (mimari)
        if t == 'LWPOLYLINE' and abs(b[0] - 11782) < 1 and abs(b[2] - 11782) < 1:
            continue                                              # 2. sistemde boşta kalan tek çizgi
        if imza(e, DX, DY) in temiz_imza:
            continue
        if t == 'TEXT':
            ogeler.append((e, 'T'))
        elif kanca_mi(e):
            ogeler.append((e, 'L'))
        else:
            ogeler.append((e, None))
    # klima santrali gövdeleri (≈830 × 545 dikdörtgen) ve sağındaki panjurlar
    santral = []
    for e, k in ogeler:
        if k is None and e.dxftype() == 'LWPOLYLINE' and len(e) in (4, 5):
            b = bb(e)
            if 700 < b[2] - b[0] < 950 and 450 < b[3] - b[1] < 650:
                santral.append(b)
    out = []
    for e, k in ogeler:
        if k is None:
            b = bb(e)
            if any(s[0] - 1 <= b[0] <= s[2] + 400 and s[1] - 60 <= b[1] and b[3] <= s[3] + 60 for s in santral):
                k = 'S'
        out.append([e, k, geom(e)])
    # 1. ve 2. sistem gevşek çizilmiş: 3. sistemin bloklarıyla (x ötelemeli kopya) eşleştir
    taze = [bb(e) for e, k, g in out if k == 'U' and bb(e) and bb(e)[0] > 14200 and bb(e)[2] < 18300]
    don = [bb(e) for e, k, g in out if k == 'D' and bb(e) and bb(e)[0] > 14200 and bb(e)[2] < 18300]
    NETX = {1: -8743.0, 2: -4317.0}
    for o in out:
        if o[1] is not None:
            continue
        b = bb(o[0])
        net = 1 if b[0] < 10000 else 2 if b[0] < 14200 else 3
        if net not in NETX:
            continue
        en = (None, 60.0)
        for dy in (0.0, -30.0):
            for k, L in (('U', taze), ('D', don)):
                for c in L:
                    v = (abs(b[0] - c[0] - NETX[net]) + abs(b[1] - c[1] - dy) + abs(b[2] - c[2] - NETX[net])
                         + abs(b[3] - c[3] - dy))
                    if v < en[1]:
                        en = (k, v)
        o[1] = en[0]
    # sınıfsız kanal parçaları: komşuluk yayılımı (gerçek geometri mesafesi ≤ 1.5)
    tohum = deque(i for i, (e, k, g) in enumerate(out) if k in ('U', 'D') and g is not None)
    bos = [i for i, (e, k, g) in enumerate(out) if k is None and g is not None]
    while tohum:
        i = tohum.popleft()
        gi = out[i][2]
        for j in list(bos):
            if out[j][1] is None and gi.distance(out[j][2]) <= 1.5:
                out[j][1] = out[i][1]
                bos.remove(j)
                tohum.append(j)
    sinifli = [o for o in out if o[1] in ('U', 'D') and o[2] is not None]
    for o in out:
        if o[1] is None:                       # kopuk kalan bağlantı parçası: en yakın kanalın sınıfı
            en = min(sinifli, key=lambda q: q[2].distance(o[2]))
            o[1] = en[1] if en[2].distance(o[2]) < 200 else 'S'
    print('ikiz düzeltme:', ikiz_duzelt(out))
    return out, santral


def ikiz_duzelt(out):
    """2. sistemde ana kolon üst kısmı 30 cm aşağı kaydırılarak yeniden çizilmiş; kaydırılmış polyline'ın
    alt ucu (branşman üst çizgisi + köşe) eski çizimin yanında ikinci bir çizgi bırakıyor. Kaydırılmış
    çizginin bu 4 noktası, eski (kısmi) çizginin üst ucuna bağlanacak şekilde kırpılır."""
    pl = [o for o in out if o[1] in ('U', 'D') and o[0].dxftype() == 'LWPOLYLINE' and len(o[0]) >= 4]
    n = 0
    for a in pl:
        A = [tuple(v) for v in a[0].get_points('xy')]
        for b in pl:
            if b is a or b[1] != a[1]:
                continue
            B = [tuple(v) for v in b[0].get_points('xy')]
            for ters in (False, True):
                AA = A[::-1] if ters else A
                if all(abs(AA[i][0] - B[i][0]) < 2 and abs(AA[i][1] - B[i][1] + 30) < 2 for i in range(4)):
                    yeni = [B[-1]] + AA[4:]
                    a[0].set_points(yeni[::-1] if ters else yeni, format='xy')
                    a[2] = geom(a[0])
                    n += 1
                    break
    return n


def yaz(out, cikti):
    doc = ezdxf.new('R2010')
    m = doc.modelspace()
    for k, c in (('U', 5), ('D', 1), ('S', 3), ('T', 7), ('L', 8)):
        doc.layers.add(k, color=c)
    for e, k, g in out:
        c = e.copy()
        c.translate(DX, DY, 0)
        c.dxf.layer = k
        m.add_entity(c)
    doc.saveas(cikti)


if __name__ == '__main__':
    out, santral = ayikla(sys.argv[1], sys.argv[2])
    from collections import Counter
    print('sınıflar:', Counter(k for e, k, g in out), 'santral:', len(santral))
    yaz(out, sys.argv[3])
