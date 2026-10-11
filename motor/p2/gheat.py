"""Genel ısı kaybı (TS 2164 / örnek şablon yöntemi) + kombili yerden ısıtma çizimi."""
import math, sys
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
from shapely.geometry import Polygon, LineString, box
import cad
from cad import L, PL, C, T, RECT, RRECT, HEXTAG
import mtyblk
import spiral3
import gp
import cg2_heat as CH

U = dict(CH.U)
ASSY = CH.ASSY
ZD, ZW = 7, 0
ZH = {'K': 5, 'KD': 5, 'KB': 5, 'G': -5, 'GD': -5, 'GB': -5, 'D': 0, 'B': 0, None: 0}
T_DIS, T_TOPRAK, T_CATI, T_HOL, T_ASANSOR = -6.0, 6.0, 0.0, 10.0, 5.0
KAT_H, KIRIS_H = 3.00, 0.50


def room_rows(R, kind):
    """R: dict(name, ti, A, ext=[(yön, uzunluk, [(w,h,n,'ÇP'|'BK')...])], int=[(işaret, uzunluk, karşı T, kapı)], )
    kind: 'zemin' (toprak), 'ara', 'ust' (çatı arası altı), 'bodrum-zemin'"""
    H = KAT_H - KIRIS_H
    rows, qs = [], []
    wn = 0
    for yon, l, wins in R.get('ext', []):
        marks = []
        for (w, h, n, typ) in wins:
            wn += 1
            mk = '%s%d' % ('ÇP' if typ == 'ÇP' else 'BK', wn)
            marks.append((mk, w, h, n, typ))
        rows.append(('DD', yon, l, H, 1, None, [m[0] for m in marks]))
        rows.append(('DD25', yon, l, KIRIS_H, 1, None, []))
        for mk, w, h, n, typ in marks:
            rows.append((mk, yon, w, h, n, None, []))
            qs.append((mk, w, h, n))
    for mark, l, tk, door in R.get('int', []):
        sub = []
        if door:
            sub = ['DK1']
        rows.append((mark, None, l, KAT_H, 1, tk, sub))
        if door:
            rows.append(('DK1', None, door[0], door[1], 1, tk, []))
    A = R['A']
    if kind == 'zemin':
        rows.append(('Dö', None, A, 1.0, 1, T_TOPRAK, []))
    if kind == 'ust':
        rows.append(('Ta', None, A, 1.0, 1, T_CATI, []))
    if kind == 'bodrum':
        rows.append(('Dö', None, A, 1.0, 1, T_TOPRAK, []))
    return rows, qs


def ukey(mark):
    if mark in ('DD25', 'DD30'):
        return mark
    m = mark.rstrip('0123456789')
    return {'BK': 'ÇP'}.get(m, m)


def calc_room(R, kind):
    rows, qs = room_rows(R, kind)
    ti = R['ti']
    lines = []
    for mark, yon, l, h, n, tk, sub in rows:
        uk = ukey(mark)
        dT = ti - (T_DIS if tk is None else tk)
        F = l * h
        minus = 0.0
        for s_ in sub:
            for mk2, yon2, l2, h2, n2, tk2, sub2 in rows:
                if mk2 == s_:
                    minus += l2 * h2 * n2
        Aeff = F * n - minus
        zh = ZH.get(yon, 0) if tk is None else 0
        z = 1 + (ZD + ZW + zh) / 100.0
        Q0 = Aeff * U[uk] * dT
        lines.append(dict(mark=mark, uk=uk, yon=yon or '', l=l, h=h, F=F, n=n, minus=minus, A=Aeff, U=U[uk], dT=dT,
                          Q0=Q0, ZH=zh, Z=z, Q=Q0 * z, tk=tk))
    Qt = sum(x['Q'] for x in lines)
    Lq = sum((a + b) * 2 * n for _, a, b, n in qs)
    ze = 1.2 if len({r[0] for r in R.get('ext', []) if r[2]}) >= 2 else 1.0
    Qs = 2 * Lq * 0.9 * 0.67 * (ti - T_DIS) * ze if qs else 0.0
    return dict(name=R['name'], ti=ti, A=R['A'], rows=lines, Qt=Qt, L=Lq, Qs=Qs, Ze=ze, Q=Qt + Qs)


# ------------------------------------------------------------------ yerden ısıtma çizimi
def _orth(a, b, first='y'):
    if first == 'y':
        return [a, (a[0], b[1]), b]
    return [a, (b[0], a[1]), b]


def ufh_circuit(rect, corner, s, port_s, port_r, via=None, first='a'):
    """rect: (x0,y0,x1,y1) boru bölgesi (duvardan 10 cm içeri). corner: 0 GB,1 GD,2 KD,3 KB.
    via: bağlantı ayağının köşeye gelmeden önce geçtiği nokta listesi (merkez çizgisi). Dönüş: path"""
    x0, y0, x1, y1 = rect
    poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    full, info = spiral3.bifilar(poly, corner, first, s)
    a, b = full[0], full[-1]
    via = via or []
    off = 3.0

    def leg(port, end, d):
        pts = [port]
        for v in via:
            pts.append((v[0] + d, v[1] + d))
        last = pts[-1]
        pts += [(end[0], last[1]), end] if abs(end[0] - last[0]) > 0.1 else [end]
        return pts
    la = leg(port_s, a, -off)
    lb = leg(port_r, b, off)
    path = la + full[1:-1] + list(reversed(lb))
    return path, LineString(full).length / 100.0


def kollektor(x0, y0, n, horiz=True, lab=True):
    """kollektör dolabı: (x0,y0) sol-alt; port aralığı 10 cm (gidiş/dönüş çifti)"""
    w = 12 + n * 10
    if horiz:
        RECT(x0, y0, x0 + w, y0 + 10, 'MTY-KOLLETOR')
        ports = [((x0 + 8 + i * 10, y0 + 10), (x0 + 12 + i * 10, y0 + 10)) for i in range(n)]
    else:
        RECT(x0, y0, x0 + 10, y0 + w, 'MTY-KOLLETOR')
        ports = [((x0 + 10, y0 + 8 + i * 10), (x0 + 10, y0 + 12 + i * 10)) for i in range(n)]
    for a, b in ports:
        C(a, 1.2, 'MTY-KOLLETOR'); C(b, 1.2, 'MTY-KOLLETOR')
    return ports
