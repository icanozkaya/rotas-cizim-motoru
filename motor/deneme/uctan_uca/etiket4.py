"""R4 yazı yerleştirici (DXF düzeyinde, emit sonrası): yazı-yazı çakışması 0.

- Engeller: bütün yazılar (TEXT / MTEXT / görünür ATTRIB) — mimari yazılar (mahal adı, alan) dahil.
- Çap / yük etiketleri (`*-CAP-*` INSERT, öznitelikleri birlikte): önce kendi boru ekseni boyunca kaydırılır (etiket boru üstünde
  kalır); eksende yer yoksa boruya dik ±12..60 cm ve kılavuz çizgi.
- Serbest yazılar (havalandırma / cihaz / temiz su kolon adları ...; plan paftalarında): aynı katman, aynı x, alt alta satırlar tek
  grup; çevresinde halka halka aranır, uzaklaşınca kılavuz çizgi. Altındaki yazı maskesi (WIPEOUT) yazıyla birlikte taşınır.
- Aynı INSERT'in kendi öznitelikleri ve aynı grubun satırları birbirine göre çakışma sayılmaz.
- Mimari-mimari çifti (kaynak mimari dosyadaki) sayılmaz, mimari yazılar taşınmaz.
"""
import math
from ezdxf import disassemble
from shapely.geometry import Polygon, LineString, Point, box
from shapely import affinity
from shapely.strtree import STRtree

KILAVUZ = 'ROTAS-SEMBOL-KILAVUZ'
SABIT_KATMAN = ('ROTAS-PAFTA', 'ROTAS-KAT-ADI', 'ROTAS-LEJANT', 'ROTAS-METRAJ')


def mimari(lay):
    return 'MIMARI' in lay.upper()


def _poly(t):
    try:
        v = [(p.x, p.y) for p in disassemble.make_primitive(t).vertices()]
        if len(v) >= 4:
            pg = Polygon(v)
            if pg.is_valid and pg.area > 0:
                return pg
            pg = pg.buffer(0)
            return pg if pg.area > 0 else None
    except Exception:
        return None
    return None


def _metin(t):
    return (t.plain_text() if t.dxftype() == 'MTEXT' else t.dxf.text).strip()


class Oge:
    """taşınabilir ya da sabit yazı birimi"""
    def __init__(self, ents, polys, sahip, lay, tip, ins=None, wipes=()):
        self.ents, self.polys, self.sahip, self.lay, self.tip, self.ins = ents, polys, sahip, lay, tip, ins
        self.wipes = list(wipes)
        self.dx = self.dy = 0.0

    def geom(self, dx=0.0, dy=0.0):
        return [affinity.translate(p, dx, dy) for p in self.polys]


def topla(msp, alanlar):
    """alanlar: [(x0, y0, x1, y1)] serbest yazıların taşınabileceği pafta pencereleri"""
    icinde = lambda p: any(a[0] <= p[0] <= a[2] and a[1] <= p[1] <= a[3] for a in alanlar)
    sabit, tasi = [], []
    wipes = [w for w in msp.query('WIPEOUT')]
    wbox = []
    for w in wipes:
        try:
            v = [(p[0], p[1]) for p in w.boundary_path_wcs()]
            wbox.append((w, Polygon(v).envelope if len(v) >= 3 else None))
        except Exception:
            wbox.append((w, None))
    serbest = []
    for e in msp:
        t = e.dxftype()
        if t == 'INSERT':
            at = [a for a in e.attribs if not a.is_invisible and a.dxf.text.strip()]
            if not at:
                continue
            ps = [p for p in (_poly(a) for a in at) if p is not None]
            if not ps:
                continue
            lay = e.dxf.layer
            if '-CAP-' in e.dxf.name and not lay.startswith(SABIT_KATMAN):
                tasi.append(Oge([e], ps, e.dxf.handle, lay, 'CAP', ins=e))
            else:
                sabit.append(Oge([e], ps, e.dxf.handle, lay, 'SABIT'))
        elif t in ('TEXT', 'MTEXT'):
            if not _metin(e):
                continue
            p = _poly(e)
            if p is None:
                continue
            lay = e.dxf.layer
            c = p.centroid
            if mimari(lay) or lay.startswith(SABIT_KATMAN) or t == 'MTEXT' or not icinde((c.x, c.y)):
                sabit.append(Oge([e], [p], e.dxf.handle, lay, 'MIMARI' if mimari(lay) else 'SABIT'))
            else:
                serbest.append((e, p))
    # serbest yazı grupları: aynı katman + aynı ekleme x'i + aynı açı + ardışık satır
    serbest.sort(key=lambda q: (q[0].dxf.layer, round(q[0].dxf.insert[0], 1), -q[0].dxf.insert[1]))
    gr = []
    for e, p in serbest:
        if gr:
            g = gr[-1]
            e0 = g[-1][0]
            if e0.dxf.layer == e.dxf.layer and abs(e0.dxf.insert[0] - e.dxf.insert[0]) < 0.6 and \
                    abs(e0.dxf.get('rotation', 0) - e.dxf.get('rotation', 0)) < 0.5 and \
                    0 < e0.dxf.insert[1] - e.dxf.insert[1] < 1.7 * e.dxf.height:
                g.append((e, p)); continue
        gr.append([(e, p)])
    for g in gr:
        ps = [p for _, p in g]
        u = Polygon()
        for p in ps:
            u = u.union(p)
        ws = [w for w, b in wbox if b is not None and b.intersects(u) and b.area < 4.0 * u.area + 50 and
              b.intersection(u).area > 0.5 * min(b.area, u.area)]
        tasi.append(Oge([e for e, _ in g], ps, g[0][0].dxf.handle, g[0][0].dxf.layer, 'SERBEST', wipes=ws))
    return sabit, tasi


def _eksen(msp_borular, ins):
    """etiket ekleme noktasının üzerinde olduğu, etiket doğrultusundaki boru parçasının kaydırma aralığı (tmin, tmax)"""
    p = (ins.dxf.insert[0], ins.dxf.insert[1])
    a = math.radians(ins.dxf.rotation)
    u = (math.cos(a), math.sin(a))
    tree, segs = msp_borular
    best = None
    for j in tree.query(Point(p).buffer(1.5)):
        s = segs[int(j)]
        (x0, y0), (x1, y1) = s.coords[0], s.coords[-1]
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1e-6 or s.distance(Point(p)) > 1.5:
            continue
        v = ((x1 - x0) / L, (y1 - y0) / L)
        if abs(v[0] * u[1] - v[1] * u[0]) > 0.03:
            continue
        t0 = (x0 - p[0]) * u[0] + (y0 - p[1]) * u[1]
        t1 = (x1 - p[0]) * u[0] + (y1 - p[1]) * u[1]
        r = (min(t0, t1), max(t0, t1))
        if best is None or (r[1] - r[0]) > (best[1] - best[0]):
            best = r
    return best, u


def borular(msp):
    segs = []
    for e in msp:
        lay = e.dxf.layer.upper()
        if not ('BORU' in lay or lay.endswith('-PVC')) or 'CAP' in lay:
            continue
        if e.dxftype() == 'LINE':
            segs.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
        elif e.dxftype() == 'LWPOLYLINE':
            pts = [q[:2] for q in e.get_points('xy')]
            if e.closed:
                pts.append(pts[0])
            for a, b in zip(pts[:-1], pts[1:]):
                if a != b:
                    segs.append(LineString([a, b]))
    return STRtree(segs), segs


def yerlestir(msp, alanlar, kilavuz_katman=KILAVUZ):
    doc = msp.doc
    if kilavuz_katman not in doc.layers:
        doc.layers.add(kilavuz_katman, color=8)
    sabit, tasi = topla(msp, alanlar)
    BR = borular(msp)
    sg = [p for o in sabit for p in o.polys]
    sown = [o.sahip for o in sabit for p in o.polys]
    stree = STRtree(sg) if sg else None
    smim = [o.tip == 'MIMARI' for o in sabit for p in o.polys]
    # sembol (INSERT) kapsamları da engel: etiket sembolün üstüne binmesin (çap etiketi blokları ve büyük bloklar hariç)
    from ezdxf import bbox as _bb
    sym = []
    for e in msp.query('INSERT'):
        if '-CAP-' in e.dxf.name or e.dxf.layer.startswith(SABIT_KATMAN):
            continue
        try:
            b = _bb.extents([e], fast=True)
        except Exception:
            continue
        if b.has_data and max(b.size.x, b.size.y) < 60 and any(a[0] <= b.center.x <= a[2] and a[1] <= b.center.y <= a[3] for a in alanlar):
            sym.append(box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
    symtree = STRtree(sym) if sym else None
    yer = []                                  # yerleşmiş taşınabilir poligonlar
    rap = dict(cap=0, serbest=0, eksende_kaydi=0, dik_kaydi=0, kilavuzlu=0, yerlesemeyen=[], yerinde=0)

    def bos(ps, haric=None):
        for p in ps:
            pb = p.buffer(0.6)
            if stree is not None:
                for j in stree.query(pb):
                    j = int(j)
                    if sg[j].intersection(pb).area > 0.01:
                        return False
            if symtree is not None:
                for j in symtree.query(pb):
                    if sym[int(j)].intersection(pb).area > 0.5:
                        return False
            for q, h in yer:
                if h != haric and q.intersects(pb) and q.intersection(pb).area > 0.01:
                    return False
        return True

    # 1. geçiş: orijinal konumu hem sabitlere hem DİĞER taşınabilirlerin orijinaline göre temiz olanlar yerinde kalır
    allp = [(p, i) for i, o in enumerate(tasi) for p in o.polys]
    ttree = STRtree([p for p, _ in allp]) if allp else None
    kalan = []
    for i, o in enumerate(tasi):
        temiz = bos(o.polys)
        if temiz and ttree is not None:
            for p in o.polys:
                for j in ttree.query(p.buffer(0.6)):
                    q, oi = allp[int(j)]
                    if oi != i and q.intersection(p.buffer(0.6)).area > 0.01:
                        temiz = False; break
                if not temiz:
                    break
        if temiz:
            for p in o.polys:
                yer.append((p, i))
            rap['yerinde'] += 1
        else:
            kalan.append(i)
    # 2. geçiş: çakışanlar (büyük gruplar önce)
    kalan.sort(key=lambda i: -sum(p.area for p in tasi[i].polys))
    for i in kalan:
        o = tasi[i]
        sec = None
        if o.tip == 'CAP':
            rng, u = _eksen(BR, o.ins)
            n = (-u[1], u[0])
            adim = []
            if rng:
                ext = max(p.bounds[2] - p.bounds[0] for p in o.polys)
                lo, hi = rng[0] + 4.0, rng[1] - 4.0
                t = 0.0
                ts = []
                for k in range(1, 400):
                    for sgn in (1, -1):
                        tt = sgn * k * 3.0
                        if lo <= tt <= hi:
                            ts.append(tt)
                    if k * 3.0 > max(abs(lo), abs(hi)):
                        break
                adim = [(tt * u[0], tt * u[1], 'eksen') for tt in [0.0] + ts]
            for off in (14, -14, 22, -22, 32, -32, 45, -45, 60, -60, 80, -80):
                for tt in (0, 10, -10, 20, -20, 35, -35, 50, -50):
                    adim.append((off * n[0] + tt * u[0], off * n[1] + tt * u[1], 'dik'))
            for dx, dy, tur in adim:
                g = o.geom(dx, dy)
                if bos(g, i):
                    sec = (dx, dy, tur); break
        else:
            c = o.polys[0].centroid
            h = max(e.dxf.height for e in o.ents)
            adim = []
            for r in [0.6 * h, 1.2 * h, 2 * h, 3 * h, 4.5 * h, 6 * h, 8 * h, 10 * h, 13 * h, 16 * h, 20 * h]:
                for k in range(16):
                    a = 2 * math.pi * k / 16
                    adim.append((r * math.cos(a), r * math.sin(a), 'halka'))
            for dx, dy, tur in adim:
                if bos(o.geom(dx, dy), i):
                    sec = (dx, dy, tur); break
        if sec is None:
            rap['yerlesemeyen'].append((o.tip, o.lay, [_metin(a) if a.dxftype() != 'INSERT' else
                                                      '/'.join(x.dxf.text for x in a.attribs) for a in o.ents][:2],
                                        [round(v) for v in o.polys[0].centroid.coords[0]]))
            for p in o.polys:
                yer.append((p, i))
            continue
        dx, dy, tur = sec
        for e in o.ents:
            e.translate(dx, dy, 0)
        for w in o.wipes:
            try:
                w.translate(dx, dy, 0)
            except Exception:
                pass
        g = o.geom(dx, dy)
        for p in g:
            yer.append((p, i))
        rap['cap' if o.tip == 'CAP' else 'serbest'] += 1
        if tur == 'eksen':
            rap['eksende_kaydi'] += 1
        else:
            rap['dik_kaydi'] += 1
        # kılavuz: yazı grubunun en yakın noktasından eski konumun merkezine (uzaklaştıysa)
        if math.hypot(dx, dy) > (12.0 if o.tip == 'CAP' else 1.5 * max(e.dxf.height for e in o.ents)) and tur != 'eksen':
            from shapely.ops import unary_union, nearest_points
            U = unary_union(g)
            hedef = o.polys[0].centroid if o.tip != 'CAP' else Point(o.ins.dxf.insert[0] - dx, o.ins.dxf.insert[1] - dy)
            if o.tip == 'SERBEST':
                hedef = unary_union(o.polys).centroid
            a_, b_ = nearest_points(U.envelope.exterior, hedef)
            msp.add_line((a_.x, a_.y), (b_.x, b_.y), dxfattribs={'layer': kilavuz_katman})
            rap['kilavuzlu'] += 1
    return rap
