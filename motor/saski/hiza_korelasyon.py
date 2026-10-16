"""Blok başına öteleme ince ayarı: temel çizgileri ile ölçeklenmiş SASKİ çizgilerinin raster çapraz korelasyonu."""
import sys, re, json, ezdxf, numpy as np
from ezdxf import path as ep
SK, TM = sys.argv[1:3]
sk = ezdxf.readfile(SK); tm = ezdxf.readfile(TM)
def giris(doc):
    out = {}
    for e in doc.modelspace().query('TEXT MTEXT'):
        t = e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()
        m = re.search(r'([ABCD])\s*BLOK\s*G[İI]R[İI][ŞS]', t.replace('%%U', ''))
        if m: out[m.group(1)] = (e.dxf.insert.x, e.dxf.insert.y)
    return out
gs, gt = giris(sk), giris(tm)
def segs(doc, lay_ok):
    S = []
    for e in doc.modelspace():
        if e.dxftype() not in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC'): continue
        if not lay_ok(e): continue
        try:
            pts = [(v.x, v.y) for v in ep.make_path(e).flattening(2.0)]
        except Exception:
            continue
        S += list(zip(pts[:-1], pts[1:]))
    return S
T_S = segs(tm, lambda e: e.dxf.layer == 'MKDU0')
S_S = segs(sk, lambda e: not (e.dxf.layer == 'SIVA' and e.dxf.color == 2) and e.dxf.layer not in ('MAHALYAZI',))
BOL = {'A': (17250, 2770, 17800, 3700), 'B': (17280, 3690, 18225, 4140),
       'C': (18225, 3580, 18960, 4140), 'D': (19150, 3090, 19760, 4140)}
R = 5.0
def ras(segs, x0, y0, nx, ny):
    im = np.zeros((nx, ny), np.float32)
    for (a, b) in segs:
        L = max(abs(b[0]-a[0]), abs(b[1]-a[1]))
        n = int(L / R) + 1
        xs = np.linspace(a[0], b[0], n + 1); ys = np.linspace(a[1], b[1], n + 1)
        i = ((xs - x0) / R).astype(int); j = ((ys - y0) / R).astype(int)
        k = (i >= 0) & (i < nx) & (j >= 0) & (j < ny)
        im[i[k], j[k]] = 1
    return im
out = {}
for b, (x0, y0, x1, y1) in BOL.items():
    S, Tt = gs[b], gt[b]
    f = lambda p: ((p[0] - S[0]) * 4 + Tt[0], (p[1] - S[1]) * 4 + Tt[1])
    ss = [(f(a), f(c)) for a, c in S_S if x0 < a[0] < x1 and y0 < a[1] < y1]
    X0, Y0 = (x0 - S[0]) * 4 + Tt[0] - 1600, (y0 - S[1]) * 4 + Tt[1] - 1600
    W, H = (x1 - x0) * 4 + 3200, (y1 - y0) * 4 + 3200
    nx, ny = int(W / R), int(H / R)
    A = ras(ss, X0, Y0, nx, ny)
    B = ras(T_S, X0, Y0, nx, ny)
    from scipy.ndimage import binary_dilation
    A = binary_dilation(A, iterations=1).astype(np.float32); B = binary_dilation(B, iterations=1).astype(np.float32)
    FA = np.fft.rfft2(A, s=(2*nx, 2*ny)); FB = np.fft.rfft2(B, s=(2*nx, 2*ny))
    C = np.fft.irfft2(FB * np.conj(FA), s=(2*nx, 2*ny))
    lim = int(1500 / R)
    best = None
    for di in range(-lim, lim + 1):
        for dj in range(-lim, lim + 1):
            v = C[di % (2*nx), dj % (2*ny)]
            if best is None or v > best[0]: best = (v, di, dj)
    v, di, dj = best
    base = C[0, 0]
    out[b] = (di * R, dj * R)
    print(b, 'kaydırma cm', di * R, dj * R, 'skor', round(float(v)), 'giriş skoru', round(float(base)), 'A piks', int(A.sum()), 'B', int(B.sum()))
json.dump(out, open('kayd.json', 'w'))
