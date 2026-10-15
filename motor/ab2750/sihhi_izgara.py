# -*- coding: utf-8 -*-
"""2750/7 SIHHİ — ızgara güzergâh motoru (4 cm hücre, dönüş cezalı Dijkstra, çok kaynaklı ağaç büyütme).

Kullanım:
    G = Izgara(x0, y0, nx, ny, h=4.0)          # x0, y0: sol alt köşe (cm)
    G.maliyet  -> float32 (ny, nx), inf = yasak
    yol = G.yol(kaynak_hucreler, hedef_hucreler, donus=40)   # [(ix, iy), ...] kaynaktan hedefe
    G.koseler(yol) -> [(x, y), ...] köşe noktaları (cm)
"""
import heapq
import math

import numpy as np

try:
    from numba import njit
except Exception:              # numba yoksa yavaş ama çalışır
    def njit(*a, **k):
        if a and callable(a[0]):
            return a[0]
        return lambda f: f

DX = np.array([1, 0, -1, 0], np.int64)
DY = np.array([0, 1, 0, -1], np.int64)


@njit(cache=True)
def _dijkstra(cost, src, src_dir, hedef, donus, ny, nx):
    """cost (ny*nx) düz, src hücre indisleri, src_dir başlangıç yönü (-1: serbest), hedef bool (ny*nx).
    Durum = hücre*4 + yön. Dönüş: (bulunan hedef durum, onceki dizisi)."""
    N = ny * nx * 4
    dist = np.full(N, np.inf)
    prev = np.full(N, -1, np.int64)
    # basit ikili yığın (numba): diziler
    hk = np.empty(N * 2 + 16)
    hv = np.empty(N * 2 + 16, np.int64)
    n = 0
    for i in range(src.shape[0]):
        c = src[i]
        for d in range(4):
            if src_dir[i] >= 0 and d != src_dir[i]:
                continue
            s = c * 4 + d
            dist[s] = 0.0
            # push
            hk[n] = 0.0
            hv[n] = s
            j = n
            n += 1
            while j > 0:
                p = (j - 1) // 2
                if hk[p] <= hk[j]:
                    break
                hk[p], hk[j] = hk[j], hk[p]
                hv[p], hv[j] = hv[j], hv[p]
                j = p
    while n > 0:
        k = hk[0]
        s = hv[0]
        n -= 1
        hk[0] = hk[n]
        hv[0] = hv[n]
        j = 0
        while True:
            l = 2 * j + 1
            r = l + 1
            m = j
            if l < n and hk[l] < hk[m]:
                m = l
            if r < n and hk[r] < hk[m]:
                m = r
            if m == j:
                break
            hk[m], hk[j] = hk[j], hk[m]
            hv[m], hv[j] = hv[j], hv[m]
            j = m
        if k > dist[s]:
            continue
        c = s // 4
        d = s % 4
        if hedef[c]:
            return s, prev
        cy = c // nx
        cx = c % nx
        for e in range(4):
            if (e + 2) % 4 == d:
                continue
            x2 = cx + DX[e]
            y2 = cy + DY[e]
            if x2 < 0 or y2 < 0 or x2 >= nx or y2 >= ny:
                continue
            c2 = y2 * nx + x2
            w = cost[c2]
            if not np.isfinite(w):
                continue
            nk = k + w + (donus if e != d else 0.0)
            s2 = c2 * 4 + e
            if nk < dist[s2]:
                dist[s2] = nk
                prev[s2] = s
                hk[n] = nk
                hv[n] = s2
                j = n
                n += 1
                while j > 0:
                    p = (j - 1) // 2
                    if hk[p] <= hk[j]:
                        break
                    hk[p], hk[j] = hk[j], hk[p]
                    hv[p], hv[j] = hv[j], hv[p]
                    j = p
    return -1, prev


class Izgara:
    def __init__(self, x0, y0, nx, ny, h=4.0):
        self.x0, self.y0, self.nx, self.ny, self.h = x0, y0, nx, ny, h
        self.maliyet = np.ones((ny, nx), np.float64)

    @classmethod
    def kutu(cls, x0, y0, x1, y1, h=4.0):
        return cls(x0, y0, int(math.ceil((x1 - x0) / h)) + 1, int(math.ceil((y1 - y0) / h)) + 1, h)

    def hucre(self, p):
        return (int(round((p[0] - self.x0) / self.h)), int(round((p[1] - self.y0) / self.h)))

    def nokta(self, c):
        return (self.x0 + c[0] * self.h, self.y0 + c[1] * self.h)

    def icinde(self, c):
        return 0 <= c[0] < self.nx and 0 <= c[1] < self.ny

    def yol(self, kaynak, hedef, donus=40.0, kaynak_yon=None, maliyet=None):
        cost = (self.maliyet if maliyet is None else maliyet).ravel()
        src = np.array([c[1] * self.nx + c[0] for c in kaynak if self.icinde(c)], np.int64)
        sd = np.array(kaynak_yon if kaynak_yon is not None else [-1] * len(src), np.int64)
        hm = np.zeros(self.nx * self.ny, np.bool_)
        for c in hedef:
            if self.icinde(c):
                hm[c[1] * self.nx + c[0]] = True
        if len(src) == 0 or not hm.any():
            return None
        s, prev = _dijkstra(cost, src, sd, hm, float(donus), self.ny, self.nx)
        if s < 0:
            return None
        out = []
        while s >= 0:
            c = s // 4
            out.append((c % self.nx, c // self.nx))
            s = prev[s]
        out.reverse()
        # ardışık aynı hücre (yön değişimi kaynağında) temizle
        temiz = [out[0]]
        for c in out[1:]:
            if c != temiz[-1]:
                temiz.append(c)
        return temiz

    def koseler(self, yol):
        if not yol:
            return []
        pts = [yol[0]]
        for i in range(1, len(yol) - 1):
            a, b, c = yol[i - 1], yol[i], yol[i + 1]
            if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
                pts.append(b)
        if len(yol) > 1:
            pts.append(yol[-1])
        return [self.nokta(c) for c in pts]
