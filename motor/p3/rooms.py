"""Emine Tunçel: mimari duvarlardan mahal poligonlarını çıkar, mahal yazısı + m² ile eşleştir."""
import pickle, re, sys
from shapely.geometry import LineString, Point, box, Polygon
from shapely.ops import unary_union
FLAT = '/tmp/claude-0/p3/et.dxf.flat.pkl'
WALL = ('rtm-duv tugla', 'rtm-tas_betonarme', 'rtm-sıva', 'P-KOLON', 'rtm-pen-ahsap', 'rtm-kapı-ahsap', 'Kapi_Pencere', 'rtm-cam',
        'SIVA', 'rtm-merdiven', 'rtm-plan katmanı-04', 'rtm-plan katmanı-03', 'P-KİRİŞ')


def clean(s):
    return re.sub(r'\\[A-Za-z][^;]*;|\\[A-Za-z]|[{}]|\\P', ' ', s).strip()


def detect(win, flat=None):
    flat = flat or pickle.load(open(FLAT, 'rb'))
    x0, y0, x1, y1 = win
    ins = lambda p: x0 - 5 <= p[0] <= x1 + 5 and y0 - 5 <= p[1] <= y1 + 5
    segs = []
    for r in flat:
        if r[1] not in WALL:
            continue
        if r[0] == 'L' and ins(r[2][0]) and ins(r[2][1]):
            segs.append(LineString(r[2]))
        elif r[0] == 'P' and all(ins(p) for p in r[2]):
            segs.append(LineString(r[2]))
    U = unary_union([s.buffer(2.5) for s in segs])
    free = box(x0, y0, x1, y1).difference(U)
    polys = list(free.geoms) if hasattr(free, 'geoms') else [free]
    ts = [(r[2][0], clean(r[2][1])) for r in flat if r[0] == 'T' and r[1] == 'rtm-mhl-yazı-malzeme' and ins(r[2][0])]
    out = []
    for p, s in ts:
        m = re.match(r'^([0-9]+\.[0-9]+)\s*m²$', s)
        if not m:
            continue
        A = float(m.group(1))
        nm = [t for q, t in ts if abs(q[0] - p[0]) < 3 and 10 < q[1] - p[1] < 25]
        nm = nm[0] if nm else '?'
        P = Point(p)
        c = [q for q in polys if q.contains(P)]
        poly = c[0] if c else min(polys, key=lambda q: q.distance(P))
        out.append(dict(name=nm, A=A, label=(round(p[0]), round(p[1])), poly=poly))
    return out


if __name__ == '__main__':
    win = tuple(map(float, sys.argv[1:5]))
    for o in detect(win):
        q = o['poly']
        print('%-22s %7.2f m²  poligon %7.2f m²  %s' % (o['name'], o['A'], q.area / 1e4, [round(v) for v in q.bounds]))


def _circle3(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy


def doors(win, rooms_, flat=None):
    """kapı yaylarından kapı açıklığı orta noktası ve hangi mahalleri bağladığı"""
    flat = flat or pickle.load(open(FLAT, 'rb'))
    x0, y0, x1, y1 = win
    ins = lambda p: x0 - 5 <= p[0] <= x1 + 5 and y0 - 5 <= p[1] <= y1 + 5
    out = []
    for r in flat:
        if r[1] != 'rtm-kapı-ahsap' or r[0] != 'P' or len(r[2]) < 6 or not all(ins(p) for p in r[2]):
            continue
        pts = r[2]
        c = _circle3(pts[0], pts[len(pts) // 2], pts[-1])
        if not c:
            continue
        rad = Point(c).distance(Point(pts[0]))
        if not (60 < rad < 130):
            continue
        for e in (pts[0], pts[-1]):
            m = ((c[0] + e[0]) / 2, (c[1] + e[1]) / 2)
            P = Point(m)
            inside = [o for o in rooms_ if o['poly'].buffer(-1).contains(P)]
            if inside:
                continue                     # açık kanat ucu oda içinde: kapalı konum diğer uç
            near = sorted(rooms_, key=lambda o: o['poly'].distance(P))[:2]
            if near and near[0]['poly'].distance(P) < 25:
                out.append(dict(p=m, w=rad, rooms=[o['name'] + '@%d,%d' % o['label'] for o in near if o['poly'].distance(P) < 25]))
                break
    return out


if __name__ == '__main__' and len(sys.argv) > 5:
    win = tuple(map(float, sys.argv[1:5]))
    R = detect(win)
    for d in doors(win, R):
        print([round(v) for v in d['p']], round(d['w']), d['rooms'])
