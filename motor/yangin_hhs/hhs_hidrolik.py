# -*- coding: utf-8 -*-
"""Ağaç (tree) sprinkler / hidrant ağı hidrolik çözücü (TS EN 12845, Hazen-Williams).

Ag: düğümler (ad -> z [m]) ve kenarlar (ust, alt, L [m], DN, n_dirsek, n_te_donus).
Başlıklar (düğüm -> K). Aktif başlık kümesi verilir; kaynak basıncı bisection ile en düşük aktif başlıkta
Pmin olacak şekilde bulunur. Çıkış: düğüm basınçları, kenar debileri, hızlar.
"""
import math

C_HW = 120.0
# EN 10255 orta seri / EN 10217 iç çaplar (mm)
IC = {25: 27.3, 32: 36.0, 40: 41.9, 50: 53.0, 65: 68.8, 80: 80.8, 100: 105.3, 125: 130.0, 150: 155.4,
      200: 206.5, 250: 260.4}
# eşdeğer boy (m), C=120 — TS EN 12845 Çizelge 38 (yaklaşık): 90° dirsek ve akışı dönen te
DIRSEK = {25: 0.76, 32: 1.0, 40: 1.2, 50: 1.5, 65: 1.9, 80: 2.4, 100: 3.0, 125: 3.7, 150: 4.3, 200: 5.7, 250: 7.4}
TE = {25: 1.5, 32: 1.9, 40: 2.4, 50: 3.0, 65: 3.7, 80: 4.6, 100: 6.1, 125: 7.3, 150: 8.6, 200: 11.3, 250: 14.6}


def dp_m(Q, dn, C=C_HW):
    """bar/m; Q l/dk"""
    if Q <= 0:
        return 0.0
    return 6.05e5 * Q ** 1.85 / (C ** 1.85 * IC[dn] ** 4.87)


def hiz(Q, dn):
    return Q / 60000.0 / (math.pi / 4 * (IC[dn] / 1000.0) ** 2)


class Ag:
    def __init__(self):
        self.z = {}
        self.k = []          # (ust, alt, L, dn, nd, nt, ek_bar)
        self.cocuk = {}
        self.ust = {}
        self.K = {}
        self.kok = None

    def dugum(self, ad, z):
        self.z[ad] = z
        if self.kok is None:
            self.kok = ad

    def kenar(self, u, a, L, dn, nd=0, nt=0, ek_bar=0.0):
        i = len(self.k)
        self.k.append((u, a, L, dn, nd, nt, ek_bar))
        self.cocuk.setdefault(u, []).append(i)
        self.ust[a] = i

    def bas(self, d, K):
        self.K[d] = K

    def _sira(self):
        out, st = [], [self.kok]
        while st:
            d = st.pop()
            out.append(d)
            for i in self.cocuk.get(d, []):
                st.append(self.k[i][1])
        return out

    def coz(self, aktif, P0, it=200):
        """aktif başlıklar açık; kökte P0 bar. Dönüş (P, Qk, Qbas)"""
        sira = self._sira()
        aktif = set(aktif)
        Qb = {d: self.K[d] * math.sqrt(max(P0, 0.01)) * 0.5 for d in aktif}
        for _ in range(it):
            Qk = [0.0] * len(self.k)
            for d in reversed(sira):            # aşağıdan yukarı debi toplama
                q = Qb.get(d, 0.0) + sum(Qk[i] for i in self.cocuk.get(d, []))
                if d in self.ust:
                    Qk[self.ust[d]] = q
            P = {self.kok: P0}
            for d in sira:
                for i in self.cocuk.get(d, []):
                    u, a, L, dn, nd, nt, ek = self.k[i]
                    Le = L + nd * DIRSEK[dn] + nt * TE[dn]
                    P[a] = P[u] - dp_m(Qk[i], dn) * Le - ek - 0.0981 * (self.z[a] - self.z[u])
            yeni = {d: self.K[d] * math.sqrt(max(P[d], 0.0)) for d in aktif}
            fark = max(abs(yeni[d] - Qb[d]) for d in aktif)
            Qb = {d: 0.5 * Qb[d] + 0.5 * yeni[d] for d in aktif}
            if fark < 0.01:
                break
        return P, Qk, Qb

    def kaynak_bul(self, aktif, Pmin, lo=0.5, hi=30.0):
        for _ in range(60):
            m = (lo + hi) / 2
            P, Qk, Qb = self.coz(aktif, m)
            if min(P[d] for d in aktif) < Pmin:
                lo = m
            else:
                hi = m
        P, Qk, Qb = self.coz(aktif, hi)
        return hi, P, Qk, Qb
