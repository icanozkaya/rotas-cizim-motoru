"""yazı çakışma kontrolü (yaklaşık kutu)"""
import math
from shapely.geometry import box, LineString
from shapely import affinity
from shapely.strtree import STRtree

ARCH = ('MIMARI', 'MIMARI-YAZI', 'MIMARI-KOLON', 'MIMARI-TEFRIS')


def tbox(r):
    p, s, h, rot, al = r[2], r[3], r[4], r[5], r[6]
    w = max(1, len(s)) * h * 0.62
    ha = {'L': 0, 'C': 0.5, 'R': 1, 'ML': 0, 'MC': 0.5, 'MR': 1, 'TL': 0, 'TC': 0.5, 'TR': 1, 'BL': 0, 'BC': 0.5, 'BR': 1}[al]
    va = {'L': 0, 'C': 0, 'R': 0, 'BL': 0, 'BC': 0, 'BR': 0, 'ML': 0.5, 'MC': 0.5, 'MR': 0.5, 'TL': 1, 'TC': 1, 'TR': 1}[al]
    b = box(p[0] - ha * w, p[1] - va * h, p[0] - ha * w + w, p[1] - va * h + h)
    if rot:
        b = affinity.rotate(b, rot, origin=p)
    return b


def overlaps(R, win=None, min_area=0.25):
    idx = [i for i, r in enumerate(R) if r and r[0] == 'T' and r[1] not in ARCH and r[3].strip()]
    if win:
        x0, y0, x1, y1 = win
        idx = [i for i in idx if x0 <= R[i][2][0] <= x1 and y0 <= R[i][2][1] <= y1]
    bs = [tbox(R[i]) for i in idx]
    tree = STRtree(bs)
    out = []
    for a, b in enumerate(bs):
        for j in tree.query(b):
            j = int(j)
            if j <= a:
                continue
            ia = b.intersection(bs[j]).area
            if ia > min_area * min(b.area, bs[j].area):
                out.append((idx[a], idx[j], R[idx[a]][3][:30], R[idx[j]][3][:30], tuple(round(v) for v in R[idx[a]][2])))
    return out


PIPE_LAYERS = ('MTY-SOGUKSU-BORU', 'MTY-SICAKSU-BORU', 'MTY-PIS-SU-BORUSU', 'MTY-PISSU-BORU-TAVANDAN', 'MTY-PEX-BORU',
               'MTY-ISITMA-GIDIS-BORU', 'MTY-ISITMA-DONUS-BORU', 'MTY-YAGMUR-BORUSU', 'MTY-PISSU-TOPLAMA-TAVAN',
               'MTY-PIS SU-BASMA', 'MTY-KLIMA-BAKIR BORU', 'MTY-KLIMA-DRENAJ')


def all_overlaps(R, win):
    x0, y0, x1, y1 = win
    inw = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    T_ = [i for i, r in enumerate(R) if r and r[0] == 'T' and r[3].strip() and inw(r[2])]
    mine = [i for i in T_ if R[i][1] not in ARCH]
    arch = [i for i in T_ if R[i][1] in ARCH]
    pipes = [LineString(r[2]) for r in R if r and r[0] == 'P' and r[1] in PIPE_LAYERS and inw(r[2][0])]
    bx = {i: tbox(R[i]) for i in T_}
    out = []
    tb = STRtree([bx[i] for i in T_])
    for i in mine:
        b = bx[i].buffer(-0.3)
        for j in tb.query(b):
            k = T_[int(j)]
            if k == i or (k in mine and k < i):
                continue
            if b.intersects(bx[k]) and b.intersection(bx[k]).area > 0.2 * min(b.area, bx[k].area):
                out.append(('YAZI-YAZI', R[i][3][:28], R[k][3][:28], tuple(round(v) for v in R[i][2])))
    if pipes:
        pt = STRtree(pipes)
        for i in mine:
            b = bx[i].buffer(-0.5)
            hits = [int(j) for j in pt.query(b) if pipes[int(j)].intersects(b)]
            if hits:
                out.append(('YAZI-BORU', R[i][3][:28], len(hits), tuple(round(v) for v in R[i][2])))
    return out
