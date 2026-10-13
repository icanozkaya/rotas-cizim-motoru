# -*- coding: utf-8 -*-
"""Raster yöntemiyle mahal (oda) poligonları ve kapılar: duvarlar ızgaraya basılır, kapı boşlukları morfolojik
kapama ile kapatılır, boş alan bileşenleri mahal olur; kapama ile dolan yamalar kapıdır.  (S çerçevesi, 1. kat)"""
import math, pickle
import numpy as np
from scipy import ndimage
from skimage.draw import line as skl
from skimage.morphology import disk
from skimage import measure
from shapely.geometry import Polygon, Point, box, MultiPoint
from shapely.ops import unary_union
from veri import *
import odaplan as RM

ST = 5.0


class Kat:
    def __init__(self, win, segs, labels):
        self.x0, self.y0, x1, y1 = win
        self.nx = int((x1 - self.x0) / ST) + 1; self.ny = int((y1 - self.y0) / ST) + 1
        W = np.zeros((self.nx, self.ny), bool)
        for a, b in segs:
            ia, ja = self.ij(a); ib, jb = self.ij(b)
            rr, cc = skl(ia, ja, ib, jb)
            ok = (rr >= 0) & (rr < self.nx) & (cc >= 0) & (cc < self.ny)
            W[rr[ok], cc[ok]] = True
        W = ndimage.binary_dilation(W, iterations=1)
        self.W = W
        C = W
        self.C = C
        self.D = np.zeros_like(W)                       # kapı / boşluk yamaları
        self.lab, n = ndimage.label(~C)
        self.labels = labels

    def ij(self, p):
        return int(round((p[0] - self.x0) / ST)), int(round((p[1] - self.y0) / ST))

    def xy(self, i, j):
        return (self.x0 + i * ST, self.y0 + j * ST)

    def comp_at(self, p):
        i, j = self.ij(p)
        if self.lab[i, j]: return self.lab[i, j]
        # yazı duvar üstündeyse en yakın boş hücre
        for r in range(1, 12):
            sub = self.lab[max(0, i - r):i + r + 1, max(0, j - r):j + r + 1]
            v = sub[sub > 0]
            if v.size: return np.bincount(v).argmax()
        return 0

    def poly(self, c):
        m = self.lab == c
        cs = measure.find_contours(np.pad(m, 1).astype(float), 0.5)
        best = max(cs, key=len)
        pts = [(self.x0 + (q[0] - 1) * ST, self.y0 + (q[1] - 1) * ST) for q in best]
        return Polygon(pts).simplify(4).buffer(0)

    def doors(self, c):
        """bileşene komşu kapı yamaları: (merkez, eksen 'x'/'y' (kapı açıklığı doğrultusu), komşu bileşenler)"""
        m = self.lab == c
        ring = ndimage.binary_dilation(m, iterations=2) & self.D
        dl, n = ndimage.label(ring)
        out = []
        for k in range(1, n + 1):
            pm = dl == k
            if pm.sum() < 6: continue
            ii, jj = np.nonzero(pm)
            # yamanın tamamı (D bileşeni)
            full_l, _ = ndimage.label(self.D)
            ids = np.unique(full_l[pm]); ids = ids[ids > 0]
            fp = np.isin(full_l, ids)
            nb = np.unique(self.lab[ndimage.binary_dilation(fp, iterations=2)]); nb = [v for v in nb if v > 0 and v != c]
            fi, fj = np.nonzero(fp)
            cx, cy = self.xy(fi.mean(), fj.mean())
            w = (fi.max() - fi.min()) * ST; h = (fj.max() - fj.min()) * ST
            out.append(dict(c=(cx, cy), w=w, h=h, nb=nb))
        return out


def segs_all(win):
    x0, y0, x1, y1 = win
    out = []
    for r in RM.S:
        if r[0] not in 'LP' or r[1] != 'MKDU0': continue
        q = [p[:2] for p in (r[2] if r[0] == 'P' else r[2][:2])]
        if not any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in q): continue
        out += [(a, b) for a, b in zip(q[:-1], q[1:]) if math.dist(a, b) > 0.3]
    return out


def kat1():
    win = (254422, -447800, 256498, -440300)
    segs = segs_all(win)
    return Kat(win, segs, RM.labels(win))


if __name__ == '__main__':
    K = kat1()
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(12, 43)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    img = np.zeros((K.ny, K.nx, 3))
    rng = np.random.default_rng(1)
    cols = rng.random((K.lab.max() + 1, 3)) * 0.6 + 0.4
    cols[0] = 0
    img[:] = cols[K.lab.T]
    img[K.W.T] = (0, 0, 0)
    img[K.D.T] = (1, 0, 0)
    ax.imshow(img[::-1], extent=(K.x0, K.x0 + K.nx * ST, K.y0, K.y0 + K.ny * ST))
    for l in K.labels:
        ax.text(l['p'][0], l['p'][1], l['ad'], fontsize=6)
    fig.savefig('/tmp/claude-0/vy/inv/mahal.png', dpi=70)
