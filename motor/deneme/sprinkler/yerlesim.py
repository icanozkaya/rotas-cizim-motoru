# -*- coding: utf-8 -*-
"""Sprinkler başlık yerleşimi — 05_ALGORITMALAR.md §4 Adım A (dikdörtgen mahal, kapalı form eşit bölme)
+ Adım C (betonarme kolondan kaçınma: satır/sütun bütün olarak kaydırılır, hiza bozulmaz).

Mahal eksene paralel dikdörtgen kabul edilir (x0, y0, x1, y1, cm). Branşmanlar 'u' eksenine paraleldir;
u = x (eksen 'x') veya u = y (eksen 'y'). Satır = bir branşman hattı (sabit v), sütun = sabit u.
"""
import math
from kurallar import SINIF, SMIN, DUVAR_MAX, DUVAR_MIN, KOLON_PAY


def uv(axis, x, y):
    return (x, y) if axis == 'x' else (y, x)


def xy(axis, u, v):
    return (u, v) if axis == 'x' else (v, u)


def rect_uv(axis, r):
    x0, y0, x1, y1 = r
    return (x0, y0, x1, y1) if axis == 'x' else (y0, x0, y1, x1)


def _kapsama_ok(pos, a, b, smax, dmax):
    """pos sıralı konumlar (cm), a..b duvar yüzleri; aralık, duvar mesafesi kontrolü ve her başlığın şerit genişliği"""
    if not pos:
        return None
    if pos[0] - a < DUVAR_MIN or b - pos[-1] < DUVAR_MIN:
        return None
    if pos[0] - a > dmax + 0.01 or b - pos[-1] > dmax + 0.01:
        return None
    for p, q in zip(pos[:-1], pos[1:]):
        g = q - p
        if g > smax + 0.01 or g < SMIN - 0.01:
            return None
    serit = []
    for i, p in enumerate(pos):
        sol = (p - a) if i == 0 else (p - pos[i - 1]) / 2.0
        sag = (b - p) if i == len(pos) - 1 else (pos[i + 1] - p) / 2.0
        serit.append(sol + sag)
    return serit


def _kolon_uv(axis, kolonlar, pad):
    out = []
    for k in kolonlar:
        u0, v0, u1, v1 = rect_uv(axis, k)
        out.append((u0 - pad, v0 - pad, u1 + pad, v1 + pad))
    return out


def _satir_carpar(v, ua, ub, kol):
    return any(k[1] < v < k[3] and k[0] < ub and k[2] > ua for k in kol)


def _sutun_carpar(u, rows, kol):
    return any(k[0] < u < k[2] and k[1] < v < k[3] for v in rows for k in kol)


def _kaydir(pos, idx, a, b, smax, dmax, carpar, adim=5.0):
    """pos[idx] çakışıyorsa en küçük kaydırmayı ara (kurallar korunarak)"""
    base = pos[idx]
    lim = smax / 2.0
    for k in range(1, int(lim / adim) + 1):
        for s in (1, -1):
            yeni = base + s * k * adim
            p2 = list(pos)
            p2[idx] = yeni
            if sorted(p2) != p2:
                continue
            if _kapsama_ok(p2, a, b, smax, dmax) is None:
                continue
            if not carpar(yeni):
                return p2
    return None


def yerlesim(mahal, axis, kolonlar, tek_satir=False):
    """Mahal dikdörtgeninde başlık ızgarası. Dönüş: dict(axis, rows(v), cols(u), Su, Sv, heads[(x,y)], cov[m²])"""
    s = SINIF[mahal['sinif']]
    smax, amax = s['smax'], s['amax'] * 1e4      # cm, cm²
    dmax = min(DUVAR_MAX, smax / 2.0)
    u0, v0, u1, v1 = rect_uv(axis, mahal['rect'])
    Lu, Lv = u1 - u0, v1 - v0
    kol = _kolon_uv(axis, kolonlar, KOLON_PAY)
    aday = []
    nu0 = max(1, math.ceil(Lu / smax - 1e-9))
    nv0 = max(1, math.ceil(Lv / smax - 1e-9))
    for nu in range(nu0, nu0 + 5):
        for nv in ([1] if tek_satir else range(nv0, nv0 + 5)):
            Su, Sv = Lu / nu, Lv / nv
            if Su > smax + 0.01 or Sv > smax + 0.01:
                continue
            if Su / 2 > dmax + 0.01 or Sv / 2 > dmax + 0.01:
                continue
            if Su * Sv > amax + 0.01:
                continue
            if (nu > 1 and Su < SMIN) or (nv > 1 and Sv < SMIN):
                continue
            aday.append((nu * nv, abs(Su - Sv), nv, nu))
    aday.sort()
    hata = 'uygun ızgara yok'
    for _, _, nv, nu in aday:
        cols = [u0 + Lu * (i + 0.5) / nu for i in range(nu)]
        rows = [v0 + Lv * (j + 0.5) / nv for j in range(nv)]
        ok = True
        # satırlar: branşman hattı tüm mahal boyunca kolona değmesin
        for j in range(nv):
            if _satir_carpar(rows[j], u0, u1, kol):
                r2 = _kaydir(rows, j, v0, v1, smax, dmax, lambda v: _satir_carpar(v, u0, u1, kol))
                if r2 is None:
                    ok = False
                    break
                rows = r2
        if not ok:
            hata = 'satır kolondan kaçamadı'
            continue
        for i in range(nu):
            if _sutun_carpar(cols[i], rows, kol):
                c2 = _kaydir(cols, i, u0, u1, smax, dmax, lambda u: _sutun_carpar(u, rows, kol))
                if c2 is None:
                    ok = False
                    break
                cols = c2
        if not ok:
            hata = 'sütun kolondan kaçamadı'
            continue
        su = _kapsama_ok(cols, u0, u1, smax, dmax)
        sv = _kapsama_ok(rows, v0, v1, smax, dmax)
        if su is None or sv is None:
            continue
        cov = {}
        heads = []
        alan_ok = True
        for j, v in enumerate(rows):
            for i, u in enumerate(cols):
                a = su[i] * sv[j]
                if a > amax + 0.01:
                    alan_ok = False
                p = xy(axis, u, v)
                heads.append(p)
                cov[p] = a / 1e4
        if not alan_ok:
            hata = 'başlık alanı aşıldı'
            continue
        return dict(axis=axis, rows=rows, cols=cols, Su=Lu / nu, Sv=Lv / nv, heads=heads, cov=cov, nu=nu, nv=nv,
                    uv_rect=(u0, v0, u1, v1))
    raise ValueError(f"{mahal['ad']}: {hata}")
