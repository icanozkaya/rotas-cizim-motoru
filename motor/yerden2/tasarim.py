"""yerden2 — mahal başına devre tasarımı: uç köşesi, devre sayısı, bant bölmesi, etiket cebi.

Kurallar (YERDEN_ISITMA_ALTIN_REFERANS §7, README):
  * uçlar kapıya en yakın köşede (kaplama oranı en iyinin %93'ünden düşükse daha iyi kaplayan köşe)
  * devre ≤ 70 m hedef, ≤ 80 m kesin; ≥ 14 m² mahal en az 2 devre
  * devre etiketi (150×80) serpantin DIŞINDA: devrenin kendi bandında, uç köşesine yakın, besleme hattının hemen
    içinde bir cep bırakılır (parmaklar cebin 7,5 cm dışında kısalır); cep sığmazsa etiket sonra maskeli yerleşir
"""
import math

from shapely.geometry import box, Point
from shapely.ops import unary_union

import serpantin as S

HEDEF_L = 7000.0     # cm
MAX_L = 8000.0
IKI_DEVRE_M2 = 14.0
CEP_X_PAY = 10.0     # besleme hattı -> cep sol kenarı


def _en_iyi_bolme(Rc, n, R_satir=None):
    """n devre için max L'yi en küçük yapan bölme -> (sonuç, maxL) | (None, inf).
    Kapsama doğrulaması geçmezse alttaki 1..4 satır atlanarak yeniden denenir (köşe girintisi)."""
    for atla in range(0, 5):
        r0 = S.kur(Rc, 1, R_satir=R_satir, atla=atla)
        if r0 is None:
            continue
        if n == 1:
            if _icinde(None, Rc, r0):
                return r0, S.uzunluk(r0['devreler'][0])
            continue
        N = len(r0['ys'])
        best, bL = None, float('inf')
        for b in S.bolmeler(N, n):
            r = S.kur(Rc, n, R_satir=R_satir, bolme=b, atla=atla)
            if r is None or not _icinde(None, Rc, r):
                continue
            L = max(S.uzunluk(p) for p in r['devreler'])
            if L < bL - 1e-6:
                best, bL = r, L
        if best is not None:
            return best, bL
    return None, float('inf')


def kose_dene(R, kose, merkez, n_min):
    fr = S.Cerceve(kose, merkez)
    Rc = fr.ic(R)
    sec = None
    for n in range(n_min, 5):
        r, L = _en_iyi_bolme(Rc, n)
        if r is None:
            continue
        if L <= HEDEF_L:
            sec = (n, r, L)
            break
        if L <= MAX_L and sec is None:
            sec = (n, r, L)
    if sec is None:
        return None
    n, r, L = sec
    top = sum(S.uzunluk(p) for p in r['devreler'])
    uc = fr.nokta_dis(r['x_f'], r['y_u'])
    return dict(kose=kose, fr=fr, Rc=Rc, n=n, sonuc=r, maxL=L, toplam=top, uc=uc)


def oda_tasarla(oda, H, R, kapi, yasak, cep_ac=True):
    """oda: mahal kaydı; H: ısıtma alanı (duvar yüzü), R: boru ekseni bölgesi; kapi: (x, y) | None;
    yasak: etiket cebi için kaçınılacak alanlar (yazılar, etiketler) -> shapely geometri.
    Dönüş: dict | None"""
    if R.is_empty or R.area < 900:
        return None
    m = R.centroid
    merkez = (round(m.x, 1), round(m.y, 1))
    n_min = 2 if oda['area'] >= IKI_DEVRE_M2 else 1
    adaylar = [a for a in (kose_dene(R, k, merkez, n_min) for k in S.KOSELER) if a]
    if not adaylar and n_min == 2:
        adaylar = [a for a in (kose_dene(R, k, merkez, 1) for k in S.KOSELER) if a]
    if not adaylar:
        return None
    eniyi = max(a['toplam'] for a in adaylar)
    iyi = [a for a in adaylar if a['toplam'] >= 0.93 * eniyi]
    if kapi is not None:
        a = min(iyi, key=lambda a: (math.hypot(a['uc'][0] - kapi[0], a['uc'][1] - kapi[1]), -a['toplam']))
    else:
        a = max(iyi, key=lambda a: a['toplam'])
    # -------- etiket cepleri
    fr, Rc, n = a['fr'], a['Rc'], a['n']
    r = a['sonuc']
    bolme = r['bolme']
    ys = r['ys']
    cepler_c = [None] * n
    cepler_w = [None] * n
    i0 = 0
    for d, mm in enumerate(bolme if cep_ac else []):
        sat = ys[i0:i0 + mm]
        i0 += mm
        fx = r['x_f'] + S.AYAK_ARA * (n - 1 - d)
        y_lo, y_hi = sat[0], sat[-1]
        bulundu = False
        for dx in (0.0,):
            if bulundu:
                break
            x0 = fx + CEP_X_PAY + dx
            y0 = y_lo + S.R_DON + 1.5
            while y0 + S.ETIKET_H <= y_hi - S.R_DON - 1.5:
                cep = box(x0, y0, x0 + S.ETIKET_W, y0 + S.ETIKET_H)
                cw = fr.dis(cep)
                if H.buffer(0.5).contains(cw) and not cw.intersects(yasak):
                    dene = [c for c in cepler_c if c is not None] + [cep]
                    Rs = Rc.difference(unary_union([c.buffer(S.CEP_PAY, join_style=2) for c in dene]))
                    r2 = S.kur(Rc, n, R_satir=Rs, bolme=bolme, atla=r.get('atla', 0))
                    kayip = (sum(S.uzunluk(p) for p in r['devreler']) - sum(S.uzunluk(p) for p in r2['devreler'])
                             if r2 is not None else 1e9)
                    if r2 is not None and _icinde(fr, Rc, r2) and kayip <= 1.5 * (S.ETIKET_W + 30) * (S.ETIKET_H + 30) / S.ADIM:
                        cepler_c[d] = cep
                        cepler_w[d] = cw
                        yasak = yasak.union(cw.buffer(5))
                        r = r2
                        bulundu = True
                        break
                y0 += S.ADIM
    devreler = []
    for d, pts in enumerate(r['devreler']):
        w = [(*fr.nokta_dis(x, y), fr.bulge_dis(b)) for x, y, b in pts]
        devreler.append(dict(pts=w, L=S.uzunluk(pts), cep=cepler_w[d], bant=d))
    return dict(kose=a['kose'], n=n, devreler=devreler, bolme=bolme, uc=a['uc'])


def _icinde(fr, Rc, r):
    Rb = Rc.buffer(0.6)
    return all(Rb.covers(S.cizgi(p)) for p in r['devreler'])
