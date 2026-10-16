"""SASKİ ALTYAPI MOTORU (kullanıcı onaylı mantık, 16.10.2026 — STANDART_KURALLAR_ALTYAPI_SARNIC.md son bölüm).

python3 altyapi_motor.py SASKI.dxf TEMEL.dxf CIKIS.dxf [--olcek 4] [--pb x,y ...] [--png]

1. Taban SASKİ vaziyeti (kendi koordinatı/ölçeği). TEMEL planındaki bloklar "X BLOK GİRİŞ" yazılarıyla hizalanır
   (ölçek otomatik ya da --olcek: 1 SASKİ birimi kaç cm; ince ayar çizgi korelasyonu) ve vaziyete TAŞINIR:
   bina dış hattı + pis su kolonları.
2. Rögar ağı kolonlara göre YENİDEN kurulur: rögarlar bina dışında cepheye paralel halkada (D_OUT), her kolon
   kümesinin branşman çıkışında ve gerekli köşelerde; kolon → 45° → cepheye dik düz branşman.
3. Halka akışı çıkış rögarına doğru; çıkış → başka bina grubunun halkası ya da PARSEL BACASI (PB, ana kanal tarafı).
4. Numaralama her ağda (PB başına) R1 (en uzak) .. Rn; PB etiketi. Etiketler "70x70 / h:-70cm", "Ø150 %1 EĞİM" + akış oku.
5. TEMEL'de "POMPA" yazısı yakınındaki kolonlar bodrum pis su pompasına toplanır; pompa en yakın rögara bağlanır.
6. SASKİ'nin eski rögar ağı (SIVA / MAHALYAZI / ubg_kot) kapalı ROTAS-SASKI-ESKI-AG katmanına alınır.
"""
import argparse
import math
import re
import sys

import ezdxf
import numpy as np
from ezdxf import bbox, xref
from ezdxf import path as ep
from shapely.geometry import Point, LineString, Polygon, MultiPoint
from shapely.ops import unary_union, nearest_points

# ---------------------------------------------------------------- ölçüler (cm)
D_OUT = 175.0       # rögar halkası: bina dış yüzünden uzaklık
KUME_U = 110.0      # aynı branşmanda birleşen kolonlar: cephe boyunca en çok
KUME_V = 160.0      # ... cepheye dik yönde en çok
ROG_MIN = 140.0     # iki rögar arası en az (daha yakınsa birleşir)
ROG_MAX = 1200.0    # rögar arası en çok (fazlası ara rögarla bölünür)
ROG_KUTU = 70.0
PB_IC = 100.0       # PB parsel sınırından içeri
GRUP_ARA = 120.0    # bu kadar yakın bloklar tek bina grubu (dilatasyonlu bloklar)
POMPA_R = 400.0     # POMPA yazısına bu kadar yakın kolonlar pompa grubunda

L_TEMEL = 'ROTAS-ALTYAPI-BINA'
L_KOLON = 'ROTAS-ALTYAPI-KOLON'
L_HAT = 'ROTAS-ALTYAPI-PISSU'
L_BRAN = 'ROTAS-ALTYAPI-PISSU-BRANSMAN'
L_ROG = 'ROTAS-ALTYAPI-ROGAR'
L_YAZI = 'ROTAS-ALTYAPI-YAZI'
L_POMPA = 'ROTAS-ALTYAPI-POMPA'
L_ESKI = 'ROTAS-SASKI-ESKI-AG'
KATMAN = {L_TEMEL: 8, L_KOLON: 1, L_HAT: 6, L_BRAN: 6, L_ROG: 5, L_YAZI: 7, L_POMPA: 4, L_ESKI: 8}
GIRIS_RE = re.compile(r'([A-Z])\s*BLOK\s*G[İI]R[İI][ŞS]')


def log(*a):
    print('[altyapi]', *a, flush=True)


def metin(e):
    t = e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()
    return t.replace('%%U', '').replace('%%u', '')


def girisler(doc):
    out = {}
    for e in doc.modelspace().query('TEXT MTEXT'):
        m = GIRIS_RE.search(metin(e).upper())
        if m:
            out[m.group(1)] = (e.dxf.insert.x, e.dxf.insert.y)
    return out


def segmentler(ents):
    S = []
    for e in ents:
        if e.dxftype() not in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC'):
            continue
        try:
            pts = [(v.x, v.y) for v in ep.make_path(e).flattening(2.0)]
        except Exception:
            continue
        S += list(zip(pts[:-1], pts[1:]))
    return S


def temizle(doc):
    for blk in doc.blocks:
        for e in [blk.block_record] + list(blk):
            if e.has_extension_dict:
                e.discard_extension_dict()
    for e in doc.modelspace():
        if e.has_extension_dict:
            e.discard_extension_dict()


# ---------------------------------------------------------------- TEMEL okuma
def temel_bloklar(tm, gt):
    """blok adı -> dict(dis=Polygon (temel cm), kolonlar=[(x,y)], pompa=[(x,y)], ents=[...])"""
    msp = tm.modelspace()
    kapali = []
    for e in msp.query('LWPOLYLINE POLYLINE'):
        try:
            pts = [(v.x, v.y) for v in ep.make_path(e).flattening(2.0)]
        except Exception:
            continue
        if len(pts) >= 4:
            P = Polygon(pts).buffer(0)
            if P.area > 50 * 1e4:            # > 50 m²
                kapali.append(P)
    kolon = []
    for e in msp.query('INSERT'):
        ad = e.dxf.name.upper()
        lay = e.dxf.layer.upper()
        if ('KOLON' in ad and ' NO' not in ad and 'NO ' not in ad) or (ad.startswith('*U') and ('VANA' in lay or 'KOLON' in lay or 'PIS' in lay)):
            kolon.append((e.dxf.insert.x, e.dxf.insert.y))
    for e in msp.query('CIRCLE'):
        if 5 <= e.dxf.radius <= 25 and 'MIMARI' not in e.dxf.layer.upper():
            kolon.append((e.dxf.center.x, e.dxf.center.y))
    # yinelenenleri at
    tek = []
    for p in kolon:
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 5 for q in tek):
            tek.append(p)
    pompa_yazi = [(e.dxf.insert.x, e.dxf.insert.y) for e in msp.query('TEXT MTEXT') if 'POMPA' in metin(e).upper()]
    out = {}
    for b, g in gt.items():
        aday = sorted(kapali, key=lambda P: P.exterior.distance(Point(g)))
        if not aday:
            continue
        dis = aday[0]
        bolge = dis.buffer(450)
        kol = [p for p in tek if bolge.contains(Point(p))]
        pom = [p for p in kol if any(math.hypot(p[0] - q[0], p[1] - q[1]) < POMPA_R for q in pompa_yazi)]
        kol = [p for p in kol if p not in pom]
        ents = [e for e in msp if _merkez_ic(e, bolge)]
        out[b] = dict(dis=dis, kolonlar=kol, pompa=pom, ents=ents)
        log('temel %s: dış hat %.0f × %.0f cm, kolon %d, pompa kolonu %d' % (
            b, dis.bounds[2] - dis.bounds[0], dis.bounds[3] - dis.bounds[1], len(kol), len(pom)))
    return out


def _merkez_ic(e, P):
    try:
        b = bbox.extents([e], fast=True)
    except Exception:
        return False
    return b.has_data and P.contains(Point(b.center.x, b.center.y))


# ---------------------------------------------------------------- hizalama
def ras(segs, x0, y0, nx, ny, R):
    im = np.zeros((nx, ny), np.float32)
    for a, b in segs:
        L = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        n = int(L / R) + 1
        xs = np.linspace(a[0], b[0], n + 1)
        ys = np.linspace(a[1], b[1], n + 1)
        i = ((xs - x0) / R).astype(int)
        j = ((ys - y0) / R).astype(int)
        k = (i >= 0) & (i < nx) & (j >= 0) & (j < ny)
        im[i[k], j[k]] = 1
    return im


def hizala(sk, TB, gs, gt, olcek=None):
    """temel cm -> SASKİ birimi dönüşümü: s = (t - T - d)/k + S. -> {blok: (k, T, S, d)}"""
    from scipy.ndimage import binary_dilation
    ag = ('SIVA', 'MAHALYAZI', 'ubg_kot')
    s_seg = segmentler([e for e in sk.modelspace() if e.dxf.layer not in ag])
    adaylar = [olcek] if olcek else [1.0, 2.0, 2.5, 4.0, 5.0, 10.0]
    sonuc = {}
    for b, T in TB.items():
        if b not in gs:
            log('UYARI: SASKİ dosyasında %s BLOK GİRİŞ yok' % b)
            continue
        S = gs[b]
        t_seg = segmentler(T['ents'])
        dx0, dy0, dx1, dy1 = T['dis'].bounds
        en = None
        for k in adaylar:
            R = 5.0
            pad = 900.0
            X0, Y0, X1, Y1 = dx0 - pad, dy0 - pad, dx1 + pad, dy1 + pad
            nx, ny = int((X1 - X0) / R), int((Y1 - Y0) / R)
            # SASKİ çizgileri temel cm uzayına (giriş hizasıyla)
            sx0, sy0 = (X0 - gt[b][0]) / k + S[0], (Y0 - gt[b][1]) / k + S[1]
            sx1, sy1 = (X1 - gt[b][0]) / k + S[0], (Y1 - gt[b][1]) / k + S[1]
            ss = [(((a[0] - S[0]) * k + gt[b][0], (a[1] - S[1]) * k + gt[b][1]),
                   ((c[0] - S[0]) * k + gt[b][0], (c[1] - S[1]) * k + gt[b][1]))
                  for a, c in s_seg if sx0 < a[0] < sx1 and sy0 < a[1] < sy1]
            if not ss:
                continue
            A = binary_dilation(ras(ss, X0, Y0, nx, ny, R), iterations=1).astype(np.float32)
            B = binary_dilation(ras(t_seg, X0, Y0, nx, ny, R), iterations=1).astype(np.float32)
            FA = np.fft.rfft2(A, s=(2 * nx, 2 * ny))
            FB = np.fft.rfft2(B, s=(2 * nx, 2 * ny))
            C = np.fft.irfft2(FB * np.conj(FA), s=(2 * nx, 2 * ny))
            lim = int(800 / R)
            idx = np.r_[0:lim + 1, 2 * nx - lim:2 * nx]
            jdx = np.r_[0:lim + 1, 2 * ny - lim:2 * ny]
            sub = C[np.ix_(idx, jdx)]
            i, j = np.unravel_index(np.argmax(sub), sub.shape)
            di = idx[i] if idx[i] <= lim else idx[i] - 2 * nx
            dj = jdx[j] if jdx[j] <= lim else jdx[j] - 2 * ny
            skor = float(sub[i, j]) / max(1.0, min(A.sum(), B.sum()))
            if en is None or skor > en[0]:
                en = (skor, k, (di * R, dj * R))
        if en is None:
            continue
        skor, k, d = en
        sonuc[b] = (k, gt[b], S, d)
        log('hiza %s: ölçek %.2f cm/birim, ince ayar %.0f / %.0f cm, skor %.2f' % (b, k, d[0], d[1], skor))
    if not olcek and sonuc:
        ks = [v[0] for v in sonuc.values()]
        k = max(set(ks), key=ks.count)
        if any(x != k for x in ks):
            log('ölçek bloklar arasında farklı çıktı %s -> %.2f ile yeniden' % (ks, k))
            return hizala(sk, TB, gs, gt, olcek=k)
    return sonuc


def dis_hat_hizala(sk, TB, gs, gt, H):
    """SASKİ'de aynı boyda kapalı bina dış hattı varsa ona birebir oturt; temel daha büyükse giriş yazısına yakın
    iki kenar (sol/sağ + alt/üst) çakıştırılır (kullanıcının D blok hizası). H'deki d ince ayarını günceller."""
    ag = ('SIVA', 'MAHALYAZI', 'ubg_kot')
    adaylar = []
    for e in sk.modelspace().query('LWPOLYLINE'):
        if e.dxf.layer in ag:
            continue
        try:
            pts = [(v.x, v.y) for v in ep.make_path(e).flattening(1.0)]
        except Exception:
            continue
        if len(pts) < 4 or math.dist(pts[0], pts[-1]) > 1.0:
            continue
        b = bbox.extents([e], fast=True)
        adaylar.append((b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
    for b, h in list(H.items()):
        k, T, S, d = h
        x0, y0, x1, y1 = TB[b]['dis'].bounds
        w, hh = (x1 - x0) / k, (y1 - y0) / k
        g = gs[b]
        yakin = [c for c in adaylar if min(abs(g[0] - c[0]), abs(g[0] - c[2])) < max(w, hh) and min(abs(g[1] - c[1]), abs(g[1] - c[3])) < max(w, hh)
                 and 0.6 < (c[2] - c[0]) / w < 1.05 and 0.6 < (c[3] - c[1]) / hh < 1.05]
        if not yakin:
            log('dış hat %s: SASKİ\'de eş hat yok, korelasyon hizası kalır' % b)
            continue
        # şimdiki (korelasyon) konumuna en yakın aday
        cur = (donustur((x0, y0), h), donustur((x1, y1), h))
        c = min(yakin, key=lambda c: abs(c[0] - cur[0][0]) + abs(c[1] - cur[0][1]) + abs(c[2] - cur[1][0]) + abs(c[3] - cur[1][1])
                + 10 * (abs((c[2] - c[0]) - w) + abs((c[3] - c[1]) - hh)))
        esit = abs((c[2] - c[0]) - w) < 0.03 * w and abs((c[3] - c[1]) - hh) < 0.03 * hh
        if esit:
            hx, hy = (c[0] + c[2]) / 2 - (cur[0][0] + cur[1][0]) / 2, (c[1] + c[3]) / 2 - (cur[0][1] + cur[1][1]) / 2
            tur = 'birebir'
        else:
            hx = (c[0] - cur[0][0]) if abs(g[0] - c[0]) <= abs(g[0] - c[2]) else (c[2] - cur[1][0])
            hy = (c[1] - cur[0][1]) if abs(g[1] - c[1]) <= abs(g[1] - c[3]) else (c[3] - cur[1][1])
            tur = 'giriş tarafı kenarları'
        H[b] = (k, T, S, (d[0] - hx * k, d[1] - hy * k))
        log('dış hat %s: %s (düzeltme %.0f / %.0f cm)' % (b, tur, hx * k, hy * k))
    return H


def donustur(p, h):
    k, T, S, d = h
    return ((p[0] - T[0] - d[0]) / k + S[0], (p[1] - T[1] - d[1]) / k + S[1])


# ---------------------------------------------------------------- ağ tasarımı
class Ag:
    def __init__(self, k):
        self.k = k
        self.dugum = []          # dict(p, tur: 'rogar'|'kose'|'pb', grup)
        self.kenar = []          # (i, j) i -> j akış
        self.bransman = []       # polyline listesi (SASKİ birimi)
        self.pompa = []

    def cm(self, v):
        return v / self.k


def eksen_kenar(P, q):
    """P dış halkasında q'ya en yakın kenar: (a, b, u birim, n dış normal)"""
    c = list(P.exterior.coords)
    en = None
    for a, b in zip(c[:-1], c[1:]):
        s = LineString([a, b])
        d = s.distance(Point(q))
        if s.length > 1e-6 and (en is None or d < en[0]):
            en = (d, a, b)
    _, a, b = en
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (u[1], -u[0])
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if P.contains(Point(m[0] + n[0] * 1e-3 * L, m[1] + n[1] * 1e-3 * L)):
        n = (-n[0], -n[1])
    return a, b, u, n


def kumele(noktalar, P, k):
    """kolonları en yakın cepheye ata ve branşman kümelerine ayır"""
    kayit = []
    for p in noktalar:
        a, b, u, n = eksen_kenar(P, p)
        uu = (p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1]
        vv = -((p[0] - a[0]) * n[0] + (p[1] - a[1]) * n[1])    # içeri pozitif
        kayit.append(dict(p=p, a=a, u=u, n=n, uu=uu, vv=vv, key=(round(a[0], 1), round(a[1], 1))))
    kumeler = []
    for r in sorted(kayit, key=lambda r: (r['key'], r['uu'])):
        for K in kumeler:
            if K[0]['key'] == r['key'] and all(abs(r['uu'] - x['uu']) <= KUME_U / k and abs(r['vv'] - x['vv']) <= KUME_V / k for x in K):
                K.append(r)
                break
        else:
            kumeler.append([r])
    return kumeler


def kur(TB, H, sk_par, pb_el, k):
    ag = Ag(k)
    # bina dış hatları SASKİ birimine
    bina = {}
    for b, T in TB.items():
        if b not in H:
            continue
        bina[b] = Polygon([donustur(p, H[b]) for p in T['dis'].exterior.coords]).buffer(0)
    # gruplar (dilatasyonlu bitişik bloklar)
    adlar = sorted(bina)
    grup = {b: {b} for b in adlar}
    for i, a in enumerate(adlar):
        for c in adlar[i + 1:]:
            ortak = bina[a].buffer(GRUP_ARA / k, join_style=2).intersection(bina[c].buffer(GRUP_ARA / k, join_style=2))
            if not ortak.is_empty:
                bx = ortak.bounds
                ortak_boy = max(bx[2] - bx[0], bx[3] - bx[1]) - 2 * GRUP_ARA / k
            if bina[a].distance(bina[c]) <= GRUP_ARA / k and not ortak.is_empty and ortak_boy >= 300 / k:
                g = grup[a] | grup[c]
                for x in g:
                    grup[x] = g
    gruplar = []
    for g in grup.values():
        if g not in gruplar:
            gruplar.append(g)
    log('bina grupları:', [''.join(sorted(g)) for g in gruplar])
    halkalar = []
    for g in gruplar:
        P = unary_union([bina[b].buffer(GRUP_ARA / k / 2 + 1, join_style=2) for b in g]).buffer(-(GRUP_ARA / k / 2 + 1), join_style=2)
        if P.geom_type != 'Polygon':
            P = max(P.geoms, key=lambda q: q.area)
        P = P.simplify(5 / k)
        H_ = P.buffer(D_OUT / k, join_style=2).exterior
        halkalar.append(dict(g=g, P=P, ring=H_, cikis=[]))
    # kolon kümeleri -> branşman + çıkış noktası
    for hk in halkalar:
        kol = [donustur(p, H[b]) for b in hk['g'] for p in TB[b]['kolonlar']]
        for K in kumele(kol, hk['P'], k):
            u, n = K[0]['u'], K[0]['n']
            a = K[0]['a']
            u0 = sum(r['uu'] for r in K) / len(K)
            ekler = []
            vj = []
            for r in K:
                du = abs(r['uu'] - u0)
                v_j = r['vv'] - du
                if v_j < 15 / k:
                    v_j = r['vv']
                    du = 0
                vj.append(v_j)
                if du > 0.5 / k:
                    q = (a[0] + u[0] * u0 - n[0] * v_j, a[1] + u[1] * u0 - n[1] * v_j)
                    ekler.append([r['p'], q])
            v_bas = max(vj)
            bas = (a[0] + u[0] * u0 - n[0] * v_bas, a[1] + u[1] * u0 - n[1] * v_bas)
            uzak = (bas[0] + n[0] * (v_bas + D_OUT / k + 50 / k), bas[1] + n[1] * (v_bas + D_OUT / k + 50 / k))
            kes = LineString([bas, uzak]).intersection(hk['ring'])
            if kes.is_empty:
                log('UYARI: branşman halkaya ulaşmadı', [tuple(round(v, 1) for v in r['p']) for r in K], 'v', round(v_bas, 1))
                continue
            e = min(([kes] if kes.geom_type == 'Point' else list(kes.geoms)), key=lambda g: g.distance(Point(bas)))
            e = (e.x, e.y)
            hk['cikis'].append(dict(e=e, gov=[bas, e], ekler=ekler, kolon=[r['p'] for r in K]))
        # pompa
        pom = [donustur(p, H[b]) for b in hk['g'] for p in TB[b]['pompa']]
        if pom:
            c = (sum(p[0] for p in pom) / len(pom), sum(p[1] for p in pom) / len(pom))
            a, b_, u, n = eksen_kenar(hk['P'], c)
            vv = -((c[0] - a[0]) * n[0] + (c[1] - a[1]) * n[1])
            uzak = (c[0] + n[0] * (vv + D_OUT / k + 50 / k), c[1] + n[1] * (vv + D_OUT / k + 50 / k))
            kes = LineString([c, uzak]).intersection(hk['ring'])
            if not kes.is_empty:
                e = min(([kes] if kes.geom_type == 'Point' else list(kes.geoms)), key=lambda g: g.distance(Point(c)))
                ag.pompa.append(dict(p=c, kolon=pom))
                hk['cikis'].append(dict(e=(e.x, e.y), gov=[c, (e.x, e.y)], ekler=[[p, c] for p in pom], kolon=[], pompa=True))
    # parsel ve PB
    parsel, kanal = sk_par
    return ag, halkalar, parsel, kanal


def halka_dugumleri(hk, k):
    """halka üzerinde çıkışlar + köşeler, çevre parametresine göre sıralı; yakın çıkışlar birleşir"""
    R = hk['ring']
    L = R.length
    noktalar = [(R.project(Point(c['e'])), 'rogar', c) for c in hk['cikis']]
    noktalar.sort(key=lambda t: t[0])
    birles = []
    for t in noktalar:
        if birles and t[0] - birles[-1][0] < ROG_MIN / k:
            onceki = birles[-1]
            onceki[2].setdefault('ek_cikis', []).append(t[2])
            continue
        birles.append([t[0], t[1], t[2]])
    if len(birles) > 1 and (L - birles[-1][0] + birles[0][0]) < ROG_MIN / k:
        birles[0][2].setdefault('ek_cikis', []).append(birles[-1][2])
        birles.pop()
    for s in birles:
        ana = s[2]
        for ek in ana.get('ek_cikis', []):        # birleşen çıkışın gövdesi ana rögara uzar
            ek['gov'] = ek['gov'][:-1] + [ek['gov'][-1], ana['e']] if math.dist(ek['gov'][-1], ana['e']) > 1e-6 else ek['gov']
    kose = [(R.project(Point(c)), 'kose', None) for c in list(R.coords)[:-1]]
    dug = [(s[0], s[1], s[2]) for s in birles]
    for kk in kose:
        if all(abs(kk[0] - d[0]) > ROG_MIN / k / 2 for d in dug):
            dug.append(kk)
    dug.sort(key=lambda t: t[0])
    return dug


def pb_bul(sk, parsel, kanal, k):
    """SASKİ eski ağının yol (ana kanal) tarafındaki uçları = parsel bacası yerleri (kullanıcı örneği: SASKİ'deki kesikli
    bağlantı hatlarının yola ulaştığı noktalar). Kenara 200 cm'den yakın SIVA köşeleri, 600 cm kümelerle."""
    if parsel is None or not kanal:
        return [], None
    c = list(parsel.exterior.coords)
    kenarlar = [LineString([a, b]) for a, b in zip(c[:-1], c[1:])]
    ana = min(kenarlar, key=lambda s_: sum(s_.distance(Point(q)) for q in kanal) / len(kanal))
    aday = []
    for e in sk.modelspace().query('LWPOLYLINE LINE'):
        if e.dxf.layer != 'SIVA':
            continue
        try:
            pts = [(v.x, v.y) for v in ep.make_path(e).flattening(1.0)]
        except Exception:
            continue
        for q in pts:
            if ana.distance(Point(q)) < 200 / k:
                aday.append(q)
    tum = []
    for e in sk.modelspace().query('LWPOLYLINE LINE'):
        if e.dxf.layer == 'SIVA':
            try:
                tum += [(v.x, v.y) for v in ep.make_path(e).flattening(1.0)]
            except Exception:
                pass
    T = np.array(tum) if tum else np.zeros((0, 2))
    kume = []
    for q in sorted(aday, key=lambda q: ana.distance(Point(q))):
        # bağlantı hattının ucu olmalı: çevresinde (≤ 250 cm) hat parçaları zinciri var
        yakin = int((np.hypot(T[:, 0] - q[0], T[:, 1] - q[1]) < 250 / k).sum()) if len(T) else 0
        if yakin < 8:
            continue
        if all(math.dist(q, r) > 600 / k for r in kume):
            kume.append(q)
    return kume, ana


def ag_kur(halkalar, parsel, kanal, pb_el, k, pb_oto):
    """düğümler + akış kenarları. Her halka bir ya da daha çok çıkışa (PB ya da başka halka) akar; her düğüm halka
    üzerinde en yakın çıkışa kısa yönden gider, iki akışın buluştuğu tepe kenarı boru konmaz."""
    D = []
    E = []
    for hi, hk in enumerate(halkalar):
        hk['dug'] = []
        hk['cikislar'] = []
        for s_, tur, c in halka_dugumleri(hk, k):
            p = hk['ring'].interpolate(s_)
            hk['dug'].append(len(D))
            D.append(dict(p=(p.x, p.y), tur=tur, halka=hi, s=s_, cikis=c))

    def halka_noktasi(hi, q):
        hk = halkalar[hi]
        s_ = hk['ring'].project(Point(q))
        for i in hk['dug']:
            if D[i]['s'] is not None and min(abs(D[i]['s'] - s_), hk['ring'].length - abs(D[i]['s'] - s_)) < ROG_MIN / k / 2:
                return i
        p = hk['ring'].interpolate(s_)
        D.append(dict(p=(p.x, p.y), tur='rogar', halka=hi, s=s_, cikis=None))
        hk['dug'].append(len(D) - 1)
        hk['dug'].sort(key=lambda i: D[i]['s'])
        return len(D) - 1

    pbs = list(pb_el) if pb_el else list(pb_oto)
    if not pbs and parsel is not None:
        # yedek: ana kenara en yakın halka noktasının karşısı
        c = list(parsel.exterior.coords)
        kenarlar = [LineString([a, b]) for a, b in zip(c[:-1], c[1:])]
        ana = min(kenarlar, key=lambda s_: sum(s_.distance(Point(q)) for q in kanal) / max(1, len(kanal))) if kanal else kenarlar[0]
        hk = min(halkalar, key=lambda h: h['ring'].distance(ana))
        q1, q2 = nearest_points(ana, hk['ring'])
        v = (q2.x - q1.x, q2.y - q1.y)
        vl = math.hypot(*v) or 1.0
        pbs = [(q1.x + v[0] / vl * PB_IC / k, q1.y + v[1] / vl * PB_IC / k)]
    pb_dugum = []
    bagli = set()
    for q in pbs:
        hi = min(range(len(halkalar)), key=lambda h: halkalar[h]['ring'].distance(Point(q)))
        pb_i = len(D)
        D.append(dict(p=tuple(q), tur='pb', halka=hi, s=None, cikis=None))
        pb_dugum.append(pb_i)
        ci = halka_noktasi(hi, q)
        halkalar[hi]['cikislar'].append(ci)
        E.append((ci, pb_i))
        bagli.add(hi)
    # PB'si olmayan halkalar: bağlı halkalardan en yakınına
    kalan = [h for h in range(len(halkalar)) if h not in bagli]
    while kalan:
        en = None
        for h in kalan:
            for g in bagli:
                d = halkalar[h]['ring'].distance(halkalar[g]['ring'])
                if en is None or d < en[0]:
                    en = (d, h, g)
        _, h, g = en
        p_c, p_h = nearest_points(halkalar[h]['ring'], halkalar[g]['ring'])
        ci = halka_noktasi(h, (p_c.x, p_c.y))
        hi_ = halka_noktasi(g, (p_h.x, p_h.y))
        halkalar[h]['cikislar'].append(ci)
        E.append((ci, hi_))
        bagli.add(h)
        kalan.remove(h)
    # halka içi akış
    for hk in halkalar:
        L = hk['ring'].length
        dg = hk['dug']
        n = len(dg)
        if n < 2:
            continue
        def rd(i, j):
            a = abs(D[i]['s'] - D[j]['s'])
            return min(a, L - a)
        uz = {i: min(rd(i, c) for c in hk['cikislar']) for i in dg}
        for a in range(n):
            i, j = dg[a], dg[(a + 1) % n]
            if uz[i] > uz[j] + 1e-9:
                E.append((i, j))
            elif uz[j] > uz[i] + 1e-9:
                E.append((j, i))
    cikan = {}
    E2 = []
    for i, j in E:
        if i in cikan:
            continue
        cikan[i] = j
        E2.append((i, j))
    E = E2
    while True:
        giren = {}
        for i, j in E:
            giren.setdefault(j, []).append(i)
        yap = [i for i, j in E if D[i]['tur'] == 'kose' and i not in giren]
        if not yap:
            break
        E = [(i, j) for i, j in E if i not in yap]
    E3 = []
    for i, j in E:
        a, b = D[i]['p'], D[j]['p']
        L = math.dist(a, b)
        n = int(L / (ROG_MAX / k))
        prev = i
        for t in range(1, n + 1):
            f = t / (n + 1)
            D.append(dict(p=(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), tur='rogar', halka=D[i]['halka'], s=None, cikis=None))
            E3.append((prev, len(D) - 1))
            prev = len(D) - 1
        E3.append((prev, j))
    E = E3
    kullan = {i for e in E for i in e}
    return D, E, pb_dugum, kullan


def numarala(D, E, pb_dugum):
    alt = {i: j for i, j in E}
    ust = {}
    for i, j in E:
        ust.setdefault(j, []).append(i)
    no = {}
    for pb in pb_dugum:
        # pb'ye uzaklık (kenar sayısı + uzunluk) ile uzaktan yakına
        uz = {pb: 0.0}
        yig = [pb]
        while yig:
            j = yig.pop()
            for i in ust.get(j, []):
                uz[i] = uz[j] + math.dist(D[i]['p'], D[j]['p'])
                yig.append(i)
        sira = sorted([i for i in uz if i != pb], key=lambda i: -uz[i])
        for n, i in enumerate(sira, 1):
            no[i] = 'R%d' % n
        no[pb] = 'PB'
    return no


# ---------------------------------------------------------------- çizim
def ciz(hedef, D, E, no, halkalar, TB, H, ag, k):
    msp = hedef.modelspace()
    for n, c in KATMAN.items():
        if n not in hedef.layers:
            hedef.layers.add(n, color=c)
    hedef.layers.get(L_ESKI).off()
    h_yazi = 9.0 / k * 1.0         # ≈ 9 cm yazı: SASKİ ölçeğinde okunur boy için büyütülür
    hy = max(h_yazi * 2.0, 2.4)
    for b, T in TB.items():
        if b not in H:
            continue
        msp.add_lwpolyline([donustur(p, H[b]) for p in T['dis'].exterior.coords], close=True, dxfattribs={'layer': L_TEMEL})
        for p in T['kolonlar'] + T['pompa']:
            msp.add_circle(donustur(p, H[b]), 12 / k, dxfattribs={'layer': L_KOLON})
    # branşmanlar
    for hk in halkalar:
        for c in hk['cikis']:
            msp.add_lwpolyline(c['gov'], dxfattribs={'layer': L_BRAN})
            for e in c['ekler']:
                msp.add_lwpolyline(e, dxfattribs={'layer': L_BRAN})
            g = LineString(c['gov'])
            if g.length > 200 / k:
                etiket(msp, c['gov'][0], c['gov'][-1], 'Ø150', hy, k)
    # ana hat
    for i, j in E:
        a, b = D[i]['p'], D[j]['p']
        msp.add_lwpolyline([a, b], dxfattribs={'layer': L_HAT})
        if math.dist(a, b) > 150 / k:
            etiket(msp, a, b, 'Ø150 %%%1 EĞİM', hy, k)
    # rögarlar
    s = ROG_KUTU / k / 2
    for i, d in enumerate(D):
        if i not in no:
            continue
        x, y = d['p']
        msp.add_lwpolyline([(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)], close=True, dxfattribs={'layer': L_ROG})
        msp.add_text(no[i], height=hy * 0.8, dxfattribs={'layer': L_ROG}).set_placement((x, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        if d['tur'] != 'pb':
            msp.add_mtext('70x70\\Ph:-70cm', dxfattribs={'layer': L_YAZI, 'char_height': hy * 0.7, 'insert': (x + s * 1.3, y + s * 1.6)})
        else:
            msp.add_mtext('PARSEL BACASI\\PBağlantı kotu: yol kotu -80 cm', dxfattribs={'layer': L_YAZI, 'char_height': hy * 0.7, 'insert': (x + s * 1.3, y + s * 1.6)})
    # pompalar
    for p in ag.pompa:
        x, y = p['p']
        r = 40 / k
        msp.add_circle((x, y), r, dxfattribs={'layer': L_POMPA})
        msp.add_lwpolyline([(x - r * 0.7, y - r * 0.5), (x + r * 0.7, y - r * 0.5), (x, y + r * 0.8)], close=True, dxfattribs={'layer': L_POMPA})
        msp.add_mtext('PİS SU POMPASI (1+1)', dxfattribs={'layer': L_YAZI, 'char_height': hy * 0.7, 'insert': (x + r * 1.3, y + r)})


def etiket(msp, a, b, t, h, k):
    """akış oku (a->b) + metin, hat ortasında, hat yönünde"""
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    L = math.dist(a, b)
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (-u[1], u[0])
    ok = 25 / k
    tip = (m[0] + u[0] * ok / 2, m[1] + u[1] * ok / 2)
    arka = (m[0] - u[0] * ok / 2, m[1] - u[1] * ok / 2)
    msp.add_solid([tip, (arka[0] + n[0] * ok / 4, arka[1] + n[1] * ok / 4), (arka[0] - n[0] * ok / 4, arka[1] - n[1] * ok / 4)],
                  dxfattribs={'layer': L_YAZI, 'color': 2})
    ang = math.degrees(math.atan2(u[1], u[0]))
    if ang > 90 or ang < -90:
        ang += 180
    p = (m[0] + n[0] * h * 0.9, m[1] + n[1] * h * 0.9)
    msp.add_text(t, height=h * 0.6, rotation=ang, dxfattribs={'layer': L_YAZI}).set_placement(
        p, align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)


# ---------------------------------------------------------------- SASKİ parsel / ana kanal
def parsel_kanal(sk, gs):
    msp = sk.modelspace()
    mer = np.mean(np.array(list(gs.values())), axis=0) if gs else np.array([0, 0])
    tk = [(e.dxf.location.x, e.dxf.location.y) for e in msp.query('POINT') if e.dxf.layer.upper() in ('TK_PARSEL',)]
    tk = [p for p in tk if math.dist(p, mer) < 5000]
    parsel = MultiPoint(tk).convex_hull if len(tk) >= 3 else None
    kanal = [(e.dxf.location.x, e.dxf.location.y) for e in msp.query('POINT') if e.dxf.layer.upper() in ('BACA', 'YOL')]
    kanal = [p for p in kanal if math.dist(p, mer) < 5000]
    log('parsel köşe %d, ana kanal/yol noktası %d' % (len(tk), len(kanal)))
    return parsel, kanal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('saski')
    ap.add_argument('temel')
    ap.add_argument('cikis')
    ap.add_argument('--olcek', type=float, help='1 SASKİ birimi kaç cm (verilmezse otomatik)')
    ap.add_argument('--pb', action='append', help='PB konumu "x,y" (SASKİ koordinatı); birden çok verilebilir')
    a = ap.parse_args()
    sk = ezdxf.readfile(a.saski)
    tm = ezdxf.readfile(a.temel)
    temizle(sk)
    temizle(tm)
    gs, gt = girisler(sk), girisler(tm)
    log('giriş yazıları SASKİ %s, TEMEL %s' % (sorted(gs), sorted(gt)))
    TB = temel_bloklar(tm, gt)
    H = hizala(sk, TB, gs, gt, a.olcek)
    H = dis_hat_hizala(sk, TB, gs, gt, H)
    k = next(iter(H.values()))[0]
    par = parsel_kanal(sk, gs)
    pb_el = [tuple(float(v) for v in s.split(',')) for s in (a.pb or [])]
    ag, halkalar, parsel, kanal = kur(TB, H, par, pb_el, k)
    pb_oto, _ = pb_bul(sk, parsel, kanal, k)
    log('PB adayları (SASKİ bağlantı uçları):', [(round(p[0], 1), round(p[1], 1)) for p in pb_oto])
    D, E, pbs, kullan = ag_kur(halkalar, parsel, kanal, pb_el, k, pb_oto)
    no = numarala(D, E, pbs)
    # çıktı: SASKİ tabanı + eski ağ kapalı katmanda + yeni ağ
    hedef = ezdxf.new('R2018', setup=True)
    hedef.header['$INSUNITS'] = sk.header.get('$INSUNITS', 0)
    xref.load_modelspace(sk, hedef)
    for e in hedef.modelspace():
        if e.dxf.layer in ('SIVA', 'MAHALYAZI', 'ubg_kot'):
            e.dxf.layer = L_ESKI
    ciz(hedef, D, E, no, halkalar, TB, H, ag, k)
    hedef.saveas(a.cikis)
    n_r = sum(1 for v in no.values() if v != 'PB')
    log('yazıldı %s: rögar %d, PB %d, ana hat %d, branşman %d, pompa %d' % (
        a.cikis, n_r, len(pbs), len(E), sum(len(h['cikis']) for h in halkalar), len(ag.pompa)))


if __name__ == '__main__':
    main()
