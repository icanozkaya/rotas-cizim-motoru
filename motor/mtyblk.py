"""MTY CAD blok kütüphanesi: blokları okuyup (patlatılmış) kayıt olarak yerleştirir."""
import math, os, glob
import ezdxf
from ezdxf.enums import TextEntityAlignment as TEA
import shapely
from shapely.geometry import Polygon
import cad

BLKDIR = '/tmp/claude-0/blk'
_cache = {}

TA = {TEA.LEFT: 'L', TEA.CENTER: 'C', TEA.RIGHT: 'R', TEA.MIDDLE_LEFT: 'ML', TEA.MIDDLE_CENTER: 'MC',
      TEA.MIDDLE_RIGHT: 'MR', TEA.TOP_LEFT: 'TL', TEA.TOP_CENTER: 'TC', TEA.TOP_RIGHT: 'TR',
      TEA.BOTTOM_LEFT: 'BL', TEA.BOTTOM_CENTER: 'BC', TEA.BOTTOM_RIGHT: 'BR', TEA.MIDDLE: 'MC',
      TEA.ALIGNED: 'L', TEA.FIT: 'L'}
MT = {1: 'TL', 2: 'TC', 3: 'TR', 4: 'ML', 5: 'MC', 6: 'MR', 7: 'BL', 8: 'BC', 9: 'BR'}


def _col(e):
    c = e.dxf.get('color', 256)
    return None if c in (0, 256) else c


def _prims(entities, out):
    for e in entities:
        t = e.dxftype()
        if e.dxf.get('invisible', 0) == 1:          # blokta görünmez işaretli parça (AutoCAD'de de görünmez)
            if t == 'ATTDEF':                          # görünmez öznitelik: değeri yine yazılır, çizilmez
                out.append(('A', lay, (0.0, 0.0), e.dxf.text, e.dxf.height, 0, 'L', None, e.dxf.tag, True))
            continue
        lay = e.dxf.get('layer', '0')
        col = _col(e)
        try:
            if t == 'LINE':
                out.append(('L', lay, (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y), col))
            elif t in ('LWPOLYLINE', 'POLYLINE'):
                if t == 'POLYLINE' and e.get_mode() not in ('AcDb2dPolyline', 'AcDb3dPolyline'):
                    continue
                from ezdxf import path as zpath
                p = zpath.make_path(e)
                pts = [(v.x, v.y) for v in p.flattening(0.3)]
                if len(pts) > 1:
                    w = e.dxf.get('const_width', 0) if t == 'LWPOLYLINE' else 0
                    out.append(('P', lay, pts, False, w or 0, col))
            elif t == 'CIRCLE':
                out.append(('C', lay, (e.dxf.center.x, e.dxf.center.y), e.dxf.radius, col))
            elif t in ('ARC', 'ELLIPSE', 'SPLINE'):
                pts = [(v.x, v.y) for v in e.flattening(0.3)]
                if len(pts) > 1:
                    out.append(('P', lay, pts, False, 0, col))
            elif t in ('SOLID', 'TRACE'):
                v = [e.dxf.vtx0, e.dxf.vtx1, e.dxf.vtx2, e.dxf.get('vtx3', e.dxf.vtx2)]
                out.append(('S', lay, (v[0].x, v[0].y), (v[1].x, v[1].y), (v[2].x, v[2].y), col))
                if (v[3] - v[2]).magnitude > 1e-9:
                    out.append(('S', lay, (v[1].x, v[1].y), (v[3].x, v[3].y), (v[2].x, v[2].y), col))
            elif t == 'HATCH':
                if not e.dxf.get('solid_fill', 0):
                    continue
                from ezdxf import path as zpath
                polys = []
                for bp in e.paths:
                    try:
                        pp = zpath.from_hatch_boundary_path(bp)
                        pts = [(v.x, v.y) for v in pp.flattening(0.3)]
                        if len(pts) >= 3:
                            polys.append(Polygon(pts).buffer(0))
                    except Exception:
                        pass
                if not polys:
                    continue
                geom = polys[0]
                for q in polys[1:]:
                    geom = geom.symmetric_difference(q)
                for tri in shapely.constrained_delaunay_triangles(geom).geoms:
                    c = list(tri.exterior.coords)[:3]
                    out.append(('S', lay, c[0], c[1], c[2], col))
            elif t in ('TEXT', 'ATTRIB'):
                al = e.get_placement()[0]
                p = e.dxf.insert if al in (TEA.LEFT, TEA.ALIGNED, TEA.FIT) else e.dxf.get('align_point', e.dxf.insert)
                out.append(('T', lay, (p.x, p.y), e.dxf.text, e.dxf.height, e.dxf.get('rotation', 0), TA.get(al, 'L'), col,
                            e.dxf.get('tag', None) if t == 'ATTRIB' else None))
            elif t == 'ATTDEF':
                al = e.get_placement()[0]
                p = e.dxf.insert if al in (TEA.LEFT, TEA.ALIGNED, TEA.FIT) else e.dxf.get('align_point', e.dxf.insert)
                out.append(('A', lay, (p.x, p.y), e.dxf.text, e.dxf.height, e.dxf.get('rotation', 0), TA.get(al, 'L'), col,
                            e.dxf.tag))
            elif t == 'MTEXT':
                p = e.dxf.insert
                out.append(('T', lay, (p.x, p.y), e.plain_text(), e.dxf.char_height, e.dxf.get('rotation', 0),
                            MT.get(e.dxf.get('attachment_point', 1), 'TL'), col, None))
            elif t == 'INSERT':
                _prims(list(e.virtual_entities()), out)
                for a in e.attribs:
                    _prims([a], out)
        except Exception:
            pass


def find(name):
    c = glob.glob(os.path.join(BLKDIR, '*__' + name + '.dxf'))
    if not c:
        raise KeyError(name)
    c.sort(key=lambda f: os.path.basename(f).startswith('ORNEK__'))   # önce asıl kütüphane, sonra örnek dosyadan alınanlar
    return c[0]


def load(name):
    if name in _cache:
        return _cache[name]
    doc = ezdxf.readfile(find(name))
    out = []
    _prims(list(doc.modelspace()), out)
    _cache[name] = out
    return out


def insert(name, pos, rot=0.0, scale=1.0, attrs=None, lay_override=None, sx=None, def0=None, hidden=()):
    """MTY bloğunu patlatıp yerleştir. attrs: {TAG: değer} (TAG ön eki eşleşir, _001 yok sayılır)."""
    attrs = attrs or {}
    prims = load(name)
    sxx = scale if sx is None else sx
    cad.push(cad.MOVE(pos[0], pos[1]))
    cad.push(cad.ROT((0, 0), rot))
    cad.push((sxx, 0, 0, 0, scale, 0))
    i0 = len(cad.R)
    flip = False
    used = {}
    for p in prims:
        k = p[0]
        lay = lay_override or p[1]
        if lay == '0':
            u = name.upper()
            lay = def0 or ('MTY-PISSU-KOLONNO' if 'KOLON NO' in u else 'MTY-VANA' if 'SAYAC' in u else 'MTY-TEFRIS')
        col = None
        if k == 'L':
            col = p[4]
            cad.L(p[2], p[3], lay); _setc(col)
        elif k == 'P':
            col = p[5]
            cad.PL(p[2], lay, p[3], p[4]); _setc(col)
        elif k == 'C':
            col = p[4]
            cad.C(p[2], p[3], lay); _setc(col)
        elif k == 'S':
            col = p[5]
            cad.SOL(p[2], p[3], p[4], lay); _setc(col)
        elif k in ('T', 'A'):
            text = p[3]
            if k == 'A':
                tag = p[8].upper()
                base = tag.split('_0')[0]
                if (base in hidden or (len(p) > 9 and p[9])) and base in attrs:   # görünmez öznitelik: değeri yazılır, çizilmez
                    used[p[8]] = [str(attrs[base]), None, True]
                    continue
                if tag in attrs:
                    text = attrs[tag]
                elif base in attrs:
                    text = attrs[base]
                else:
                    continue
            if not str(text).strip():
                continue
            if k == 'A':
                used[p[8]] = [str(text), None]
            ang = (p[5] + rot) % 360
            al = p[6]
            if 90.5 < ang <= 270.5:      # okunur yön: ters yazıyı 180° çevir, hizayı aynala
                flip = True
                ang = (ang + 180) % 360
                sw = {'L': 'R', 'R': 'L'}
                al = al[:-1] + sw.get(al[-1], al[-1]) if al else al
                if al and al[0] in 'TB':
                    al = {'T': 'B', 'B': 'T'}[al[0]] + al[1:]
            cad.T(p[2], text, p[4], lay, al, rot=ang)
            _setc(p[7])
            if k == 'A':
                used[p[8]][1] = len(cad.R) - 1 - i0      # öznitelik yazısının blok kayıtları içindeki sırası
    if len(cad.R) > i0:          # her blok gerçek blok (INSERT) olarak yazılır - hiçbiri patlatılmaz
        u = name.upper()
        lay0 = def0 or ('MTY-PISSU-KOLONNO' if 'KOLON NO' in u else 'MTY-VANA' if 'SAYAC' in u else 'MTY-TEFRIS')
        cad.BLK.append(dict(name=name, m=cad.tf(), attrs=used, lay0=lay_override or lay0, recs=list(cad.R[i0:]), flip=flip))
    cad.pop(); cad.pop(); cad.pop()


def _setc(col):
    if col is not None:
        r = cad.R[-1]
        cad.R[-1] = r + (col,)


def bbox(name):
    xs, ys = [], []
    for p in load(name):
        if p[0] == 'L':
            xs += [p[2][0], p[3][0]]; ys += [p[2][1], p[3][1]]
        elif p[0] == 'P':
            xs += [q[0] for q in p[2]]; ys += [q[1] for q in p[2]]
        elif p[0] == 'C':
            xs += [p[2][0] - p[3], p[2][0] + p[3]]; ys += [p[2][1] - p[3], p[2][1] + p[3]]
    return min(xs), min(ys), max(xs), max(ys)
