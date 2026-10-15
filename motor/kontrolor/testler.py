"""Kontrolör geometrik testleri — kullanıcı kurallarını (README 14.10.2026 C / B / standart) ÖLÇEN testler.
Her test Bulgu listesi döndürür: FAIL (kural ihlali, koordinatlı), INFO (bilgi), PASS (test geçti, özet).
Koordinatlar kontrol edilen çizimin koordinatlarıdır (kat bilgisi öteleme ile taşınmıştır)."""
import math
import re
from collections import defaultdict

import networkx as nx
from shapely import STRtree
from shapely.geometry import LineString, Point, Polygon, MultiLineString, box
from shapely.ops import unary_union, linemerge

import cizim as C

# ---- eşikler (cm) — kullanıcı kurallarından; new_block referansıyla kalibre edildi (BENIOKU.md)
BALKON_SUZGEC_MAX = 300.0     # balkon süzgeci – yağmur inişi hat boyu ("birkaç metreyi geçmez")
BRANSMAN_MAX = 300.0          # armatür – kolon pis su branşmanı ("kısa ve düz")
ACI_TOL = 4.0                 # branşman açısı {0,45,90}'dan sapma (derece)
ACI_MIN_BOY = 25.0            # açı testine giren en kısa parça
DUVAR_DIBI = 30.0             # pis su hattı mahal iç bölgesinden (duvardan > 30 cm) geçmez
CAPRAZ_MIN = 30.0             # iç bölgede sayılan en kısa parça (BİLGİ)
CAPRAZ_FAIL = 100.0           # iç bölgede bu kadar geçen hat: ÇAPRAZ UZUN HAT (FAIL); referans new_block'ta en çok 97 cm
EGIK_FAIL = 150.0             # 0/90 dışı tek parça bu boydan uzunsa FAIL
DAIRE_DISI_MIN = 15.0         # sıcak su daire dışı toplam uzunluk eşiği
KOMBI_PAY = 120.0             # kombi nişi (mahal poligonu dışında olabilir) payı
PARALEL_ARALIK = (3.0, 30.0)  # sıcak–soğuk ofset aralığı
PARALEL_ORAN = 0.80           # sıcak hattın soğukla eşlenmiş uzunluk oranı
OFSET_STD = 6.0               # ofset sabitliği (referans new_block: 3-6 cm)
KORIDOR_ORTA_ORAN = 0.25      # koridor genişliğinde duvara en yakın oran (ortada: 0,5)
KOLON_KOSE_MAX = 45.0         # pis su kolonu – ıslak hacim köşesi
KOLON_MAHAL_PAY = 40.0        # kolon ıslak mahal poligonuna bu kadar yakınsa (duvar / tezgâh içi) o mahaldedir
ARMATUR_BAG_TOL = 50.0        # armatür bağlantı noktası – pis su ağı
ETIKET_H = (8.0, 12.0)        # etiket yazı yüksekliği (kullanıcı: çap bloğu 10)
ETIKET_HAT_MIN = 8.0          # yazı kutusundan geçen hat boyu (cm): köşeye değen sayılmaz
ETIKET_BOSLUK = 0.0           # etiket–etiket en az boşluk (cm); 0: yalnız gerçek örtüşme (kutu.py gerçek kutu)
ETIKET_TARAMA_ORAN = 0.25     # etiket kutusunun bu oranından fazlası duvar/betonarme taramasında -> FAIL
ETIKET_ARMATUR_ORAN = 0.25    # etiket kutusunun bu oranından fazlası armatür / tesisat sembolü üstünde -> FAIL
# etiket–armatür testinin uygulandığı semboller. new_block kalibrasyonu (15.10.2026): kullanıcı pis su iniş etiketini
# klozet / lavabo / duş teknesi / süzgeç / çamaşır makinesi bloğunun ÜSTÜNE yazıyor (52+ kez: tarzı) ama eviye, bulaşık
# makinesi, kombi, hela ve mimarideki Ç.M. yerinin üstüne HİÇ yazmıyor (0). Tur 1 RED: etiket eviye ve B.M. kutusu üstünde.
ARMATUR_DENETIM = ('EV (MIMARI)', 'EVIYE', 'BM (MIMARI)', 'BULASIK', 'CM (MIMARI)', 'MAKINE', 'TERMOSIFON', 'KOMBI',
                   'HELA', 'ASPIRATOR')
ETIKET_ORTAK_ORAN = 0.30      # etiket kutusunun bu oranından fazlası asansör boşluğu / merdivende -> FAIL


def armatur_denetlenir(ad):
    """T07 etiket–armatür testi hangi armatür/sembollerde uygulanır (new_block kalibrasyonu: BENIOKU)"""
    n = C.normu(ad)
    if ARMATUR_DENETIM is None:
        return True
    return any(k in n for k in ARMATUR_DENETIM)


class Bulgu:
    def __init__(self, test, durum, mesaj, kat=None, nokta=None, noktalar=None, pencere=None, ek=None):
        self.test, self.durum, self.mesaj, self.kat = test, durum, mesaj, kat
        self.noktalar = list(noktalar or ([nokta] if nokta else []))
        self.nokta = nokta or (self.noktalar[0] if self.noktalar else None)
        self.pencere = pencere
        self.ek = ek or {}
        self.png = None

    def __repr__(self):
        return '%s %s %s %s' % (self.test, self.durum, self.kat, self.mesaj)


def pencere_yap(noktalar, pad=120.0, en_az=(360.0, 300.0)):
    xs = [p[0] for p in noktalar]
    ys = [p[1] for p in noktalar]
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    if x1 - x0 < en_az[0]:
        c = (x0 + x1) / 2
        x0, x1 = c - en_az[0] / 2, c + en_az[0] / 2
    if y1 - y0 < en_az[1]:
        c = (y0 + y1) / 2
        y0, y1 = c - en_az[1] / 2, c + en_az[1] / 2
    return (x0, y0, x1, y1)


def _xy(p):
    return (round(float(p[0])), round(float(p[1])))


# ------------------------------------------------------------------ ağ (graf) yardımcıları
def _parcala(geos):
    """LineString listesini düz parçalara böler; başka parçanın ucu üzerine düşen noktalardan (T) ayırır."""
    seg = []
    for lay, g in geos:
        cs = list(g.coords)
        for a, b in zip(cs[:-1], cs[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > 0.5:
                seg.append((lay, (a[0], a[1]), (b[0], b[1])))
    if not seg:
        return []
    ls = [LineString([a, b]) for _, a, b in seg]
    tree = STRtree(ls)
    uclar = [Point(a) for _, a, _ in seg] + [Point(b) for _, _, b in seg]
    out = []
    for i, (lay, a, b) in enumerate(seg):
        l = ls[i]
        kes = []
        for j in tree.query(l.buffer(2.0), predicate='intersects'):
            if j == i:
                continue
            for q in (uclar[j], uclar[j + len(seg)]):
                d = l.distance(q)
                if d <= 2.0:
                    t = l.project(q)
                    if 2.0 < t < l.length - 2.0:
                        kes.append(t)
        kes = sorted(set(round(t, 1) for t in kes))
        pts = [a] + [tuple(l.interpolate(t).coords[0]) for t in kes] + [b]
        for p, q in zip(pts[:-1], pts[1:]):
            out.append((lay, p, q))
    return out


def ag_kur(geos, tol=2.0):
    """[(katman, LineString)] -> networkx Graph; düğüm = tol ızgarasına yuvarlanmış nokta; kenar: boy, katman"""
    G = nx.Graph()
    k = lambda p: (round(p[0] / tol) * tol, round(p[1] / tol) * tol)
    for lay, a, b in _parcala(geos):
        u, v = k(a), k(b)
        if u == v:
            continue
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if G.has_edge(u, v):
            continue
        G.add_edge(u, v, boy=L, lay=lay)
    return G


def en_yakin_dugum(G, p, tol):
    best, bd = None, tol
    for n in G.nodes:
        d = math.hypot(n[0] - p[0], n[1] - p[1])
        if d < bd:
            best, bd = n, d
    return best


def en_yakin_kenar_dugumu(G, p, tol):
    """p'ye en yakın kenarın üzerindeki noktayı yeni düğüm olarak ekler (armatür bağlantısı kenar ortasına da olabilir)"""
    n = en_yakin_dugum(G, p, tol)
    if n is not None:
        return n
    best, bd = None, tol
    for u, v, d in G.edges(data=True):
        l = LineString([u, v])
        dd = l.distance(Point(p))
        if dd < bd:
            best, bd = (u, v, l), dd
    if best is None:
        return None
    u, v, l = best
    q = tuple(l.interpolate(l.project(Point(p))).coords[0])
    q = (round(q[0], 1), round(q[1], 1))
    if q == u or q == v:
        return q
    lay = G.edges[u, v]['lay']
    G.remove_edge(u, v)
    G.add_edge(u, q, boy=math.hypot(q[0] - u[0], q[1] - u[1]), lay=lay)
    G.add_edge(q, v, boy=math.hypot(v[0] - q[0], v[1] - q[1]), lay=lay)
    return q


def yol_uzunlugu(G, yol):
    return sum(G.edges[a, b]['boy'] for a, b in zip(yol[:-1], yol[1:]))


def aci_sapma(a, b):
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 90
    return min(ang, abs(ang - 45), 90 - ang)


def mahal_adi(kb, p, yalniz=None):
    pt = Point(p)
    aday = [r for r in kb['rooms'] if r['poly'].buffer(5).contains(pt) and (yalniz is None or yalniz(r))]
    if not aday:
        return None
    return min(aday, key=lambda r: r['poly'].area)


# ------------------------------------------------------------------ T01 balkon süzgeci
def t01_balkon_suzgeci(cz, kat, kb):
    w = kb['pencere']
    out = []
    balkonlar = [r for r in kb['rooms'] if r['balkon']]
    geos = [(lay, g) for lay, g, e in cz.borular_pencere(w) if not C.temiz_mi(lay)]
    G = ag_kur(geos)
    inisler = C._kumele(cz.yagmur_inisleri(w) + list(kb.get('inisler', [])), 20)
    kolonlar = cz.pis_kolonlar(w)
    n_ok = 0
    for s in cz.suzgecler(w):
        r0 = mahal_adi(kb, s)                      # en küçük kapsayan mahal (balkon içindeki küçük duş balkon sayılmaz)
        if r0 is None or not r0['balkon']:
            continue
        if any(r['islak'] and r['poly'].distance(Point(s)) < 15 for r in kb['rooms']):
            continue                               # duş teknesi kenarındaki süzgeç (tekne poligonu küçük)
        b = [r0]
        n = en_yakin_kenar_dugumu(G, s, 30)
        if n is None:
            out.append(Bulgu('T01', 'FAIL', 'balkon süzgeci (%s) hiçbir hatta bağlı değil' % b[0]['name'], kat, s,
                             pencere=pencere_yap([s])))
            continue
        comp = nx.node_connected_component(G, n)
        H = G.subgraph(comp)
        pis_kenar = [(u, v) for u, v, d in H.edges(data=True) if C.pis_mi(d['lay'])]
        kol = [(p, en_yakin_dugum(H, p, 40)) for p in kolonlar]
        kol = [(p, q) for p, q in kol if q is not None]
        if pis_kenar or kol:
            hedef = kol[0][0] if kol else pis_kenar[0][0]
            L = None
            if kol:
                try:
                    L = yol_uzunlugu(G, nx.shortest_path(H, n, kol[0][1], weight='boy'))
                except Exception:
                    L = None
            ad = ''
            for no, p in cz.kolon_balonlari(w):
                if math.hypot(p[0] - hedef[0], p[1] - hedef[1]) < 120:
                    ad = ' (%s)' % no
                    break
            out.append(Bulgu('T01', 'FAIL', 'balkon süzgeci (%s) PİS SU %s bağlanmış%s%s — kural: yalnız balkondaki '
                             'yağmur inişine, kısa hatla' % (b[0]['name'], 'kolonuna' if kol else 'hattına', ad,
                                                              (' hat %.0f cm' % L) if L else ''),
                             kat, s, noktalar=[s, hedef], pencere=pencere_yap([s, hedef])))
            continue
        hedef = [(p, en_yakin_dugum(H, p, 30)) for p in inisler]
        hedef = [(p, q) for p, q in hedef if q is not None]
        if not hedef:
            out.append(Bulgu('T01', 'FAIL', 'balkon süzgeci (%s) yağmur inişine ulaşmıyor (bağlı hat yağmur inişinde '
                             'bitmiyor)' % b[0]['name'], kat, s, pencere=pencere_yap(list(comp)[:50] + [s])))
            continue
        L = min(yol_uzunlugu(H, nx.shortest_path(H, n, q, weight='boy')) for p, q in hedef)
        p0 = min(hedef, key=lambda pq: math.hypot(pq[0][0] - s[0], pq[0][1] - s[1]))[0]
        if L > BALKON_SUZGEC_MAX:
            out.append(Bulgu('T01', 'FAIL', 'balkon süzgeci (%s) – yağmur inişi hattı %.0f cm > %.0f cm' %
                             (b[0]['name'], L, BALKON_SUZGEC_MAX), kat, s, noktalar=[s, p0], pencere=pencere_yap([s, p0])))
        else:
            n_ok += 1
    # balkon içinden geçen pis su hattı (süzgeç bağlantısı ne olursa olsun)
    for lay, g, e in cz.borular_pencere(w, C.pis_mi):
        for r in balkonlar:
            x = g.intersection(r['poly'].buffer(-5))
            if x.length > 20:
                p = x.representative_point()
                out.append(Bulgu('T01', 'FAIL', 'pis su hattı balkon içinden geçiyor (%s, %.0f cm)' % (r['name'], x.length),
                                 kat, (p.x, p.y), pencere=pencere_yap([(p.x, p.y)])))
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T01', 'PASS', '%d balkon süzgeci yağmur inişine kısa hatla bağlı' % n_ok, kat))
    return out


# ------------------------------------------------------------------ T02 pis su branşmanı
def t02_pis_su_bransman(cz, kat, kb):
    w = kb['pencere']
    out = []
    geos = [(lay, g) for lay, g, e in cz.borular_pencere(w, C.pis_mi)]
    G = ag_kur(geos)
    if G.number_of_edges() == 0:
        return [Bulgu('T02', 'INFO', 'katta pis su hattı yok', kat)]
    kolon_d = {}
    for p in cz.pis_kolonlar(w):
        n = en_yakin_kenar_dugumu(G, p, 40)
        if n is not None:
            kolon_d[n] = p
    balon = cz.kolon_balonlari(w)

    def kolon_adi(p):
        for no, q in balon:
            if math.hypot(p[0] - q[0], p[1] - q[1]) < 130:
                return no
        return '?'

    # 1) açı: her pis su parçası {0, 45, 90}°
    aci_hata = []
    for u, v, d in G.edges(data=True):
        if d['boy'] >= ACI_MIN_BOY and aci_sapma(u, v) > ACI_TOL:
            aci_hata.append((u, v, d['boy']))
    for u, v, L in aci_hata[:40]:
        m = ((u[0] + v[0]) / 2, (u[1] + v[1]) / 2)
        ang = math.degrees(math.atan2(v[1] - u[1], v[0] - u[0])) % 180
        out.append(Bulgu('T02', 'FAIL', 'pis su parçası %.0f cm, açı %.0f° ({0,45,90} dışı)' % (L, ang), kat, m,
                         noktalar=[u, v], pencere=pencere_yap([u, v])))
    # 2) armatür -> kolon branşmanı: uzunluk, mahal dışı
    n_ok = 0
    if not kolon_d:
        out.append(Bulgu('T02', 'INFO', 'pis su kolon sembolü bulunamadı; branşman boyu ölçülemedi', kat))
    for f in kb['fx']:
        if f['kind'] not in ('WC', 'LV', 'DUS', 'EV', 'YS', 'CM', 'BM') or f.get('mahal') is None:
            continue
        n = en_yakin_kenar_dugumu(G, f['c'], ARMATUR_BAG_TOL)
        if n is None:
            d = 'FAIL' if f['kind'] in ('WC', 'LV', 'DUS', 'EV') else 'INFO'
            out.append(Bulgu('T02', d, '%s (%s) pis su hattına bağlı değil (%.0f cm içinde hat yok)' %
                             (f['kind'], f['mahal']['name'], ARMATUR_BAG_TOL), kat, f['c'], pencere=pencere_yap([f['c']])))
            continue
        if not kolon_d:
            continue
        try:
            yollar = nx.multi_source_dijkstra(G, set(kolon_d), target=n, weight='boy')
        except Exception:
            yollar = None
        if not yollar or yollar[0] == math.inf:
            out.append(Bulgu('T02', 'FAIL', '%s (%s) branşmanı hiçbir kolona ulaşmıyor' % (f['kind'], f['mahal']['name']),
                             kat, f['c'], pencere=pencere_yap([f['c']])))
            continue
        L, yol = yollar
        kolon_p = kolon_d[yol[0]]
        kad = kolon_adi(kolon_p)
        hat = LineString(yol) if len(yol) > 1 else None
        sorun = []
        if L > BRANSMAN_MAX:
            sorun.append('uzun: %.0f cm > %.0f' % (L, BRANSMAN_MAX))
        if hat is not None:
            izin = f['mahal']['poly'].buffer(DUVAR_DIBI)
            kr = mahal_adi(kb, kolon_p, lambda r: r['islak'])
            if kr is not None:
                izin = unary_union([izin, kr['poly'].buffer(DUVAR_DIBI)])
            disari = hat.difference(izin)
            if disari.length > 40:
                p = disari.representative_point()
                r2 = mahal_adi(kb, (p.x, p.y))
                sorun.append('mahal dışından dolaşıyor: %.0f cm (%s)' % (disari.length, r2['name'] if r2 else 'ortak alan/dış'))
        if sorun:
            out.append(Bulgu('T02', 'FAIL', '%s (%s) → %s branşmanı: %s' % (f['kind'], f['mahal']['name'], kad, '; '.join(sorun)),
                             kat, f['c'], noktalar=list(yol), pencere=pencere_yap(list(yol))))
        else:
            n_ok += 1
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T02', 'PASS', '%d armatür branşmanı kısa/düz, açılar {0,45,90}' % n_ok, kat))
    return out


# ------------------------------------------------------------------ T03 oda içi çapraz hat
def t03_oda_ici_capraz(cz, kat, kb):
    w = kb['pencere']
    out = []
    icler = []
    for r in kb['rooms']:
        ic = r['poly'].buffer(-DUVAR_DIBI)
        if not ic.is_empty and ic.area > 100:
            icler.append((r, ic))
    for lay, g, e in cz.borular_pencere(w, C.pis_mi):
        cs = list(g.coords)
        for r, ic in icler:
            x = g.intersection(ic)
            if x.length >= CAPRAZ_MIN:
                p = x.representative_point()
                d = 'FAIL' if x.length >= CAPRAZ_FAIL else 'INFO'
                out.append(Bulgu('T03', d, 'pis su hattı %s içinden, duvardan > %.0f cm uzakta %.0f cm geçiyor (%s)' %
                                 (r['name'], DUVAR_DIBI, x.length, 'ÇAPRAZ UZUN HAT' if d == 'FAIL' else 'kısa çapraz, bilgi'),
                                 kat, (p.x, p.y), noktalar=[cs[0], cs[-1]], pencere=pencere_yap([cs[0], cs[-1]], pad=100)))
        # 0/90 dışı uzun tek parça (eğik hat) — mahalden bağımsız
        for a, b in zip(cs[:-1], cs[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 90
            if L >= EGIK_FAIL and min(ang, 90 - ang) > ACI_TOL:
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                r = mahal_adi(kb, m)
                out.append(Bulgu('T03', 'FAIL', 'eğik pis su parçası %.0f cm (%s) — oda içinden çapraz uzun hat' %
                                 (L, r['name'] if r else '?'), kat, m, noktalar=[a, b], pencere=pencere_yap([a, b], pad=100)))
    if not any(b.durum == 'FAIL' for b in out):
        out.insert(0, Bulgu('T03', 'PASS', 'pis su hatları duvar dibinden (iç bölgeden ≥ %.0f cm geçen parça yok)' % CAPRAZ_FAIL, kat))
    return out


# ------------------------------------------------------------------ T04 sıcak su daire dışı
def t04_sicak_su_daire(cz, kat, kb):
    w = kb['pencere']
    out = []
    geos = [(lay, g) for lay, g, e in cz.borular_pencere(w, C.sicak_mi)]
    if not geos:
        return [Bulgu('T04', 'INFO', 'katta sıcak su hattı yok', kat)]
    G = ag_kur(geos)
    kombiler = [f['c'] for f in kb['fx'] if f['kind'] == 'KOMBI']
    kombiler += [p for ad, p, e in cz.insertler_pencere(w, ('KOMBI',), ('SEMA',))]
    kombiler += [p for s, p, h, lay, e in cz.yazilar_pencere(w) if 'KOMBI' in C.normu(s)]
    n_ok = 0
    kombi_b = unary_union([Point(k).buffer(KOMBI_PAY) for k in kombiler]) if kombiler else Polygon()
    for comp in nx.connected_components(G):
        H = G.subgraph(comp)
        hat = unary_union([LineString([u, v]) for u, v in H.edges])
        if hat.length < 30:
            continue
        en, enL = None, 0
        for n, dp in kb['daire_poly'].items():
            L = hat.intersection(dp).length
            if L > enL:
                en, enL = n, L
        if en is None:
            p = hat.representative_point()
            r = mahal_adi(kb, (p.x, p.y))
            out.append(Bulgu('T04', 'FAIL', 'sıcak su hattı (%.0f cm) hiçbir daire içinde değil (%s)' %
                             (hat.length, r['name'] if r else 'ortak alan / dış'), kat, (p.x, p.y),
                             pencere=pencere_yap([(hat.bounds[0], hat.bounds[1]), (hat.bounds[2], hat.bounds[3])])))
            continue
        # yasak: ortak alan (duvar payı düşülmüş), BAŞKA dairelerin mahalleri (kendi dairesine 45 cm pay), bina dışı
        cer = box(*w)
        yasak = [kb['ortak_poly'].buffer(-10), cer.difference(kb['bina'].buffer(100))]
        yasak += [dp.buffer(-45) for n, dp in kb['daire_poly_ic'].items() if n != en]
        yasak = unary_union(yasak).difference(unary_union([kb['daire_poly'][en], kombi_b]))
        dis = hat.intersection(yasak)
        if dis.length > DAIRE_DISI_MIN:
            parcalar = list(dis.geoms) if hasattr(dis, 'geoms') else [dis]
            yerler = []
            pts = []
            for pc in parcalar:
                if pc.length < 5:
                    continue
                p = pc.representative_point()
                r = mahal_adi(kb, (p.x, p.y))
                yerler.append(r['name'] if r else 'dış')
                pts.append((p.x, p.y))
            ortak = hat.intersection(kb['ortak_poly'].buffer(-25)).length
            out.append(Bulgu('T04', 'FAIL', 'daire %s sıcak su hattının %.0f cm\'si daire dışında: ortak alan / başka daire / bina dışı (%s)%s — kural: sıcak su '
                             'daire içinden, kombiden; merdiven holü/koridordan besleme yok' %
                             (en, dis.length, ', '.join(sorted(set(yerler))) or '?',
                              (' — ortak alanda %.0f cm' % ortak) if ortak > 5 else ''),
                             kat, pts[0] if pts else None, noktalar=pts, pencere=pencere_yap(pts or [(hat.bounds[0], hat.bounds[1])])))
        else:
            n_ok += 1
        if kombiler and not any(hat.distance(Point(k)) < 80 for k in kombiler):
            p = hat.representative_point()
            out.append(Bulgu('T04', 'FAIL', 'daire %s sıcak su hattı kombiden başlamıyor (en yakın kombi %.0f cm)' %
                             (en, min(hat.distance(Point(k)) for k in kombiler)), kat, (p.x, p.y), pencere=pencere_yap([(p.x, p.y)])))
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T04', 'PASS', '%d sıcak su ağı daire içinde, kombiden' % n_ok, kat))
    return out


# ------------------------------------------------------------------ T05 sıcak-soğuk paralellik / kesişme
def t05_sicak_soguk(cz, kat, kb):
    w = kb['pencere']
    out = []
    sic = [(lay, g) for lay, g, e in cz.borular_pencere(w, C.sicak_mi)]
    sog = [(lay, g) for lay, g, e in cz.borular_pencere(w, C.soguk_mi)]
    if not sic or not sog:
        return [Bulgu('T05', 'INFO', 'sıcak (%d) / soğuk (%d) hat yok' % (len(sic), len(sog)), kat)]
    soguk_u = unary_union([g for _, g in sog])
    armaturler = [f['c'] for f in kb['fx'] if f['kind'] in ('LV', 'EV', 'DUS', 'CM', 'BM', 'WC', 'KOMBI')]
    # kesişme (uçtan 15 cm içi bağlantı sayılır; armatür bağlantısının 60 cm yakını — batarya çaprazı — sayılmaz)
    for lay1, a in sic:
        for lay2, b in sog:
            if not a.crosses(b):
                continue
            x = a.intersection(b)
            pts = [x] if x.geom_type == 'Point' else [g for g in getattr(x, 'geoms', []) if g.geom_type == 'Point']
            for p in pts:
                if C.D.ic_nokta(a, p, 15) and C.D.ic_nokta(b, p, 15) and \
                        not any(math.hypot(p.x - q[0], p.y - q[1]) < 60 for q in armaturler):
                    kose = any(math.hypot(p.x - c[0], p.y - c[1]) < 10 for c in list(a.coords) + list(b.coords))
                    out.append(Bulgu('T05', 'INFO' if kose else 'FAIL',
                                     'sıcak su hattı soğuk su hattını kesiyor' + (' (köşede yan değiştirme — referans new_block\'ta da var, bilgi)' if kose else ''),
                                     kat, (p.x, p.y), pencere=pencere_yap([(p.x, p.y)])))
    # paralellik: sıcak parçaları (>= 60 cm) boyunca soğuk mesafesi
    G = ag_kur(sic)
    n_ok = 0
    for u, v, d in G.edges(data=True):
        if d['boy'] < 60:
            continue
        l = LineString([u, v])
        n = max(3, int(d['boy'] / 10))
        ds = [soguk_u.distance(l.interpolate(i / n, normalized=True)) for i in range(n + 1)]
        es = [x for x in ds if PARALEL_ARALIK[0] <= x <= PARALEL_ARALIK[1]]
        oran = len(es) / len(ds)
        if oran < PARALEL_ORAN:
            m = ((u[0] + v[0]) / 2, (u[1] + v[1]) / 2)
            out.append(Bulgu('T05', 'FAIL', 'sıcak su parçası %.0f cm soğukla paralel değil (soğuğa %.0f-%.0f cm, eşlenen %%%.0f)' %
                             (d['boy'], min(ds), max(ds), 100 * oran), kat, m, noktalar=[u, v], pencere=pencere_yap([u, v])))
        elif len(es) >= 3:
            mu = sum(es) / len(es)
            std = (sum((x - mu) ** 2 for x in es) / len(es)) ** 0.5
            if std > OFSET_STD:
                m = ((u[0] + v[0]) / 2, (u[1] + v[1]) / 2)
                out.append(Bulgu('T05', 'FAIL', 'sıcak–soğuk ofset sabit değil (%.0f cm parça, ofset %.0f±%.1f cm)' %
                                 (d['boy'], mu, std), kat, m, noktalar=[u, v], pencere=pencere_yap([u, v])))
            else:
                n_ok += 1
        else:
            n_ok += 1
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T05', 'PASS', '%d sıcak parçası soğukla sabit ofsetli paralel, kesişme yok' % n_ok, kat))
    return out


# ------------------------------------------------------------------ T06 koridor ortası
def t06_koridor_orta(cz, kat, kb):
    w = kb['pencere']
    out = []
    kor = [r for r in kb['rooms'] if r['koridor']]
    geos = [(lay, g) for lay, g, e in cz.borular_pencere(w, C.temiz_mi)]
    n_ok = 0
    for r in kor:
        P = r['poly']
        if P.area < 1.5e4:
            continue
        sinir = P.boundary
        for lay, g in geos:
            x = g.intersection(P)
            parcalar = [x] if x.geom_type == 'LineString' else [p for p in getattr(x, 'geoms', []) if p.geom_type == 'LineString']
            for pc in parcalar:
                cs = list(pc.coords)
                for a, b in zip(cs[:-1], cs[1:]):
                    L = math.hypot(b[0] - a[0], b[1] - a[1])
                    if L < 60:
                        continue
                    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                    dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
                    nx_, ny_ = -dy, dx
                    d = []
                    for s in (1, -1):
                        ray = LineString([m, (m[0] + s * nx_ * 3000, m[1] + s * ny_ * 3000)])
                        q = ray.intersection(sinir)
                        if q.is_empty:
                            d.append(3000)
                        else:
                            pts = [q] if q.geom_type == 'Point' else [g2 for g2 in getattr(q, 'geoms', []) if g2.geom_type == 'Point']
                            d.append(min((math.hypot(p.x - m[0], p.y - m[1]) for p in pts), default=3000))
                    gen = d[0] + d[1]
                    if gen > 2000:
                        continue
                    oran = min(d) / gen
                    if oran < KORIDOR_ORTA_ORAN:
                        out.append(Bulgu('T06', 'INFO', '%s içinde temiz su hattı duvar dibinde: duvara %.0f cm, koridor %.0f cm '
                                         '(%s) — kural: koridorda hatlar ORTADAN' % (r['name'], min(d), gen, C.normu(lay)),
                                         kat, m, noktalar=[a, b], pencere=pencere_yap([a, b])))
                    else:
                        n_ok += 1
    n_dip = sum(1 for b in out if b.durum == 'INFO')
    out.insert(0, Bulgu('T06', 'PASS' if not n_dip else 'INFO', '%d koridor parçası ortada, %d duvar dibinde (BİLGİ: kullanıcının kendi '
                        'new_block çiziminde antre hatları duvar dibinde; B kuralı koridor ortası — karar kullanıcıda)' % (n_ok, n_dip), kat))
    return out


# ------------------------------------------------------------------ T07 etiketler
def t07_etiketler(cz, kat, kb, mimari_yazi_kaynak=None):
    w = kb['pencere'] if kb else None
    out = []
    et = cz.etiketler(w)
    if not et:
        return [Bulgu('T07', 'INFO', 'etiket yok', kat)]
    pg = [e[1] for e in et]
    tree = STRtree(pg)
    pgb = [g.buffer(ETIKET_BOSLUK / 2.0, join_style=2) for g in pg] if ETIKET_BOSLUK > 0 else pg
    sol, sag = tree.query(pgb, predicate='intersects')
    n_ee = 0
    for i, j in zip(sol, sag):
        if i >= j or et[i][2] == et[j][2]:
            continue
        a, b = pgb[i], pgb[j]
        if a.intersection(b).area <= 0.2:
            continue
        c = a.intersection(b).centroid
        n_ee += 1
        if n_ee <= 60:
            out.append(Bulgu('T07', 'FAIL', 'etiket etiket üstüne: "%s" / "%s"' % (et[i][0][:20], et[j][0][:20]), kat, (c.x, c.y),
                             pencere=pencere_yap([(c.x, c.y)], pad=80, en_az=(260, 200))))
    # etiket – mimari yazı
    my = cz.mimari_yazilar(w)
    if not my and mimari_yazi_kaynak:
        my = mimari_yazi_kaynak
    mt = STRtree([m[1] for m in my]) if my else None
    n_em = 0
    if mt is not None:
        sol, sag = mt.query(pg, predicate='intersects')
        for i, j in zip(sol, sag):
            a, b = pg[i], my[j][1]
            if a.intersection(b).area <= 0.2:
                continue
            c = a.intersection(b).centroid
            n_em += 1
            if n_em <= 60:
                out.append(Bulgu('T07', 'FAIL', 'etiket mimari yazı üstüne: "%s" / "%s"' % (et[i][0][:20], my[j][0][:20]), kat,
                                 (c.x, c.y), pencere=pencere_yap([(c.x, c.y)], pad=80, en_az=(260, 200))))
    # etiket – hat
    borular = [g for lay, g, e in cz.borular_pencere(w)]
    bt = STRtree(borular) if borular else None
    n_eh = 0
    if bt is not None:
        sol, sag = bt.query(pg, predicate='intersects')
        for i, j in zip(sol, sag):
            x = pg[i].intersection(borular[j])
            if x.is_empty or x.length < ETIKET_HAT_MIN:
                continue
            c = x.centroid
            n_eh += 1
            if n_eh <= 60:
                out.append(Bulgu('T07', 'FAIL', 'etiket hat üstüne biniyor: "%s" (%.0f cm hat yazı kutusunda)' % (et[i][0][:20], x.length),
                                 kat, (c.x, c.y), pencere=pencere_yap([(c.x, c.y)], pad=80, en_az=(260, 200))))
    # etiket – duvar/betonarme taraması, armatür/sembol, asansör-merdiven bölgesi (tur 1 madde 5: "etiketler duvar
    # taramasının, kapı yazısının ve armatürlerin üstüne konmuş; asansör boşluğuna taşmış")
    n_et = n_ea = n_eo = 0
    if kb is not None:
        tar = kb.get('taramalar') or []
        tt = STRtree(tar) if tar else None
        arm = []
        for f in kb.get('fx', []):
            if f['kind'] in ('KOMBI', 'YS'):
                continue
            if f.get('bb'):
                arm.append(('%s (mimari)' % f['kind'], box(*f['bb']), None))
            else:
                arm.append(('%s (mimari)' % f['kind'], Point(f['c']).buffer(18 if f['kind'] in ('LV', 'EV') else 12), None))
        arm += [(C.normu(ad)[:24], pg, h) for ad, pg, h in cz.sembol_kutulari(w)]
        arm = [a for a in arm if armatur_denetlenir(a[0])]
        at = STRtree([g for _, g, _ in arm]) if arm else None
        ortak = [r for r in kb['rooms'] if r['ortak'] and any(k in r['name'].lower() for k in ('asans', 'merdiven'))]
        for i, e in enumerate(et):
            a = pg[i]
            A = a.area
            if A <= 0:
                continue
            if tt is not None:
                ust = unary_union([tar[j] for j in tt.query(a, predicate='intersects')] or [Polygon()])
                x = a.intersection(ust).area if not ust.is_empty else 0.0
                if x > ETIKET_TARAMA_ORAN * A:
                    n_et += 1
                    if n_et <= 40:
                        c = a.centroid
                        out.append(Bulgu('T07', 'FAIL', 'etiket duvar/betonarme taramasının üstünde: "%s" (%%%.0f)' % (e[0][:20], 100 * x / A),
                                         kat, (c.x, c.y), pencere=pencere_yap([(c.x, c.y)], pad=80, en_az=(260, 200))))
            if at is not None:
                for j in at.query(a, predicate='intersects'):
                    if arm[j][2] is not None and arm[j][2] == e[2]:
                        continue                      # kendi bloğunun özniteliği (kolon bloğundaki P no)
                    x = a.intersection(arm[j][1]).area
                    if x > ETIKET_ARMATUR_ORAN * A:
                        n_ea += 1
                        if n_ea <= 40:
                            c = a.centroid
                            out.append(Bulgu('T07', 'FAIL', 'etiket armatür/sembol üstünde: "%s" / %s (%%%.0f)' % (
                                e[0][:20], arm[j][0], 100 * x / A), kat, (c.x, c.y), pencere=pencere_yap([(c.x, c.y)], pad=80, en_az=(260, 200))))
                        break
            for r in ortak:
                if re.match(r'^(P|YB)\d+$', e[0]):
                    break                             # kolon numarası balonu mahal dışında, kolonun yanında (ORNEK_DUZEN)
                x = a.intersection(r['poly'].buffer(-5)).area
                if x > ETIKET_ORTAK_ORAN * A:
                    # asansör boşluğu: FAIL. merdiven holü: BİLGİ — kullanıcı new_block 1. katta kolon toplam etiketini
                    # ("Ø100 / 46 SB") kılavuzla merdiven holüne almış (boş yer); karar görsel kontrolde
                    asansor = 'asans' in r['name'].lower()
                    n_eo += 1 if asansor else 0
                    if not asansor:
                        c = a.centroid
                        out.append(Bulgu('T07', 'INFO', 'etiket merdiven holünde: "%s" (%%%.0f) — kılavuzlu ve boş yerdeyse kabul '
                                         '(referans new_block 1. kat)' % (e[0][:20], 100 * x / A), kat, (c.x, c.y)))
                    elif n_eo <= 40:
                        c = a.centroid
                        out.append(Bulgu('T07', 'FAIL', 'etiket %s içinde: "%s" (%%%.0f) — etiket mahal dışına kılavuzla, boş yere' % (
                            r['name'].replace('\n', ' '), e[0][:20], 100 * x / A), kat, (c.x, c.y),
                            pencere=pencere_yap([(c.x, c.y)], pad=80, en_az=(260, 200))))
                    break
    # etiket boyu
    hs = sorted(e[4] for e in et if e[3] and ('CAP' in C.normu(e[3]) or 'TEFRIS' in C.normu(e[3])))
    if hs:
        med = hs[len(hs) // 2]
        if not (ETIKET_H[0] <= med <= ETIKET_H[1]):
            out.append(Bulgu('T07', 'FAIL', 'çap etiketi yazı yüksekliği ortanca %.1f (kullanıcı boyu %.0f-%.0f)' %
                             (med, ETIKET_H[0], ETIKET_H[1]), kat))
    ozet = ('etiket-etiket %d, etiket-mimari yazı %d, etiket-hat %d, etiket-tarama %d, etiket-armatür/sembol %d, '
            'etiket-asansör boşluğu %d (toplam %d etiket)' % (n_ee, n_em, n_eh, n_et, n_ea, n_eo, len(et)))
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T07', 'PASS', ozet, kat))
    else:
        out.insert(0, Bulgu('T07', 'INFO', ozet, kat))
    return out


# ------------------------------------------------------------------ T08 kolon şeması: sayaç
def t08_sema_sayac(cz):
    w = cz.sema_paftasi
    if w is None:
        return [Bulgu('T08', 'INFO', 'kolon şeması paftası bulunamadı', 'ŞEMA')]
    out = []
    say = cz.sayaclar(w)
    katlar = []
    for s, p, h, lay, e in cz.yazilar_pencere(w):
        n = C.normu(s)
        m = C.Cizim.KAT_RE.match(n)
        if m and 'PLAN' not in n and e.dxftype() == 'TEXT':
            katlar.append((p[1], n, p))
    katlar.sort()
    zemin = [k for k in katlar if k[1].startswith('ZEMIN')]
    if not zemin:
        return [Bulgu('T08', 'INFO', 'şemada ZEMİN KAT bandı yazısı yok; sayaç bandı ölçülemedi', 'ŞEMA')]
    yz = zemin[0][0]
    ust = [k for k in katlar if k[0] > yz + 20]
    y1 = ust[0][0] if ust else yz + 400
    # daire blokları: D1.. yazıları (daire içinde) -> en soldaki x
    dx_ = [p[0] for s, p, h, lay, e in cz.yazilar_pencere(w) if C.D.re.match(r'^D\d+$', C.norm(s))]
    sol_sinir = min(dx_) - 50 if dx_ else None
    n_zemin_sol = 0
    for p in say:
        if p[1] >= y1 - 10:
            kad = max((k for k in katlar if k[0] <= p[1] + 10), key=lambda k: k[0], default=None)
            out.append(Bulgu('T08', 'FAIL', 'su sayacı KAT BANDINDA (%s) — kural: sayaçlar yalnız zemin bandında, şebeke girişinde' %
                             (kad[1] if kad else '?'), 'ŞEMA', p, pencere=pencere_yap([p], pad=200, en_az=(600, 350))))
        elif sol_sinir is not None and p[0] > sol_sinir:
            out.append(Bulgu('T08', 'FAIL', 'su sayacı daire bloğu içinde / kapı önünde (x=%.0f) — kural: sayaç grubu zemin bandının '
                             'SOLUNDA, şebeke girişinde' % p[0], 'ŞEMA', p, pencere=pencere_yap([p], pad=200, en_az=(600, 350))))
        else:
            n_zemin_sol += 1
    for s, p, h, lay, e in cz.yazilar_pencere(w):
        n = C.normu(s)
        if 'SAYAC' in n and ('KAPI' in n):
            out.append(Bulgu('T08', 'FAIL', 'şemada "%s" yazısı: kapıda sayaç kurgusu reddedildi' % C.norm(s)[:40], 'ŞEMA', p,
                             pencere=pencere_yap([p], pad=200, en_az=(600, 350))))
    if n_zemin_sol == 0:
        out.append(Bulgu('T08', 'FAIL', 'zemin bandının solunda (şebeke girişi) sayaç grubu yok', 'ŞEMA',
                         (w[0] + 300, yz), pencere=(w[0], yz - 150, w[0] + 1200, y1)))
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T08', 'PASS', '%d sayaç zemin bandında, şebeke girişinde; kat bantlarında sayaç yok' % n_zemin_sol, 'ŞEMA'))
    return out


# ------------------------------------------------------------------ T09 ıslak hacim başına süzgeç
def t09_suzgec_sayisi(cz, kat, kb):
    w = kb['pencere']
    out = []
    semboller = cz.suzgecler(w) + [f['c'] for f in kb['fx'] if f['kind'] == 'YS']
    semboller = C._kumele(semboller, 15)
    n_ok = 0
    for r in kb['rooms']:
        if not r['islak']:
            continue
        n = sum(1 for s in semboller if r['poly'].buffer(5).contains(Point(s)))
        if 'mutfak' in C.normu(r.get('name') or '').lower():
            # kullanıcı 15.10 (D): MUTFAKTA YER SÜZGECİ YOK (14.10 "her ıslak hacimde süzgeç" mutfak için iptal)
            if n:
                c = r['poly'].centroid
                out.append(Bulgu('T09', 'FAIL', '%s: mutfakta yer süzgeci %d (kural: mutfakta süzgeç YOK)' % (r['name'], n),
                                 kat, (c.x, c.y)))
            else:
                n_ok += 1
            continue
        if n != 1:
            c = r['poly'].centroid
            out.append(Bulgu('T09', 'FAIL', '%s: yer süzgeci %d (her ıslak hacimde tam 1)' % (r['name'], n), kat, (c.x, c.y),
                             pencere=pencere_yap([(r['poly'].bounds[0], r['poly'].bounds[1]), (r['poly'].bounds[2], r['poly'].bounds[3])], pad=60)))
        else:
            n_ok += 1
    for s in semboller:
        r = mahal_adi(kb, s)
        if r is not None and not r['islak'] and not r['balkon']:
            out.append(Bulgu('T09', 'FAIL', 'süzgeç kuru mahalde: %s' % r['name'], kat, s, pencere=pencere_yap([s])))
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T09', 'PASS', '%d ıslak hacimde 1 süzgeç (mutfakta 0)' % n_ok, kat))
    return out


# ------------------------------------------------------------------ T10 kolon ıslak hacim köşesinde
def t10_kolon_kose(cz, kat, kb):
    w = kb['pencere']
    out = []
    balon = cz.kolon_balonlari(w)
    n_ok = 0
    kolonlar = cz.pis_kolonlar(w)
    if not kolonlar:
        return [Bulgu('T10', 'INFO', 'pis su kolon sembolü yok', kat)]
    for p in kolonlar:
        ad = next((no for no, q in balon if math.hypot(p[0] - q[0], p[1] - q[1]) < 130), '?')
        pt = Point(p)
        if any(c.contains(pt) for c in kb['cols']):
            out.append(Bulgu('T10', 'FAIL', 'kolon %s betonarme kolon/perde içinde' % ad, kat, p, pencere=pencere_yap([p])))
            continue
        aday = [r for r in kb['rooms'] if r['islak'] and r['poly'].buffer(KOLON_MAHAL_PAY).contains(pt)]
        if not aday:
            r = mahal_adi(kb, p)
            out.append(Bulgu('T10', 'FAIL', 'kolon %s ıslak hacim dışında (%s) — kural: kolon ıslak hacmin köşesinde' %
                             (ad, r['name'] if r else 'ortak alan / dış'), kat, p, pencere=pencere_yap([p])))
            continue
        r = min(aday, key=lambda q: q['poly'].area)
        sp = r['poly'].simplify(6)
        kose = []
        for pg in (sp.geoms if hasattr(sp, 'geoms') else [sp]):
            kose += list(pg.exterior.coords)
        d = min(math.hypot(p[0] - k[0], p[1] - k[1]) for k in kose) if kose else 0
        if d > KOLON_KOSE_MAX:
            out.append(Bulgu('T10', 'FAIL', 'kolon %s %s köşesinde değil (en yakın köşe %.0f cm)' % (ad, r['name'], d), kat, p,
                             pencere=pencere_yap([p])))
        else:
            n_ok += 1
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T10', 'PASS', '%d kolon ıslak hacim köşesinde' % n_ok, kat))
    return out


# ------------------------------------------------------------------ T11 denetle (MTY / önek / köprü / kesişme / elektrik / yazı)
def t11_denetle(yol):
    from pathlib import Path
    r = C.D.denetle(Path(yol))
    out = []
    if r.get('hata'):
        return [Bulgu('T11', 'FAIL', r['hata'])]
    adlar = [('mty', 'MTY kalıntısı', 'mty_ornek'), ('onek', 'ROTAS- öneksiz katman', 'onek_ornek'),
             ('kopru', 'boru atlatma (köprü)', 'kopru_ornek'), ('kesisme', 'boru-boru kesişmesi', 'kesisme_ornek'),
             ('elektrik', 'elektrik kalemi', 'elektrik_ornek'), ('yazi', 'yazı-yazı çakışması (denetle %2)', 'yazi_ornek'),
             ('audit', 'DXF audit hatası', 'audit_ornek')]
    for k, ad, ok in adlar:
        if r.get(k):
            orn = r.get(ok)
            orn = ', '.join(str(x) for x in list(orn.values() if isinstance(orn, dict) else orn)[:4]) if orn else ''
            out.append(Bulgu('T11', 'FAIL', '%s: %d %s' % (ad, r[k], ('— ' + orn) if orn else ''), ek={'anahtar': k}))
    if r.get('yetersiz'):
        out.append(Bulgu('T11', 'FAIL', '"yetersiz / uygun değil" yazısı: %d' % len(r['yetersiz'])))
    if not r.get('lejant') and not r.get('kapak'):
        out.append(Bulgu('T11', 'FAIL', 'LEJANT yok'))
    # kesişme noktalarını PNG için koordinatlı bulgu yap
    try:
        import ezdxf
        doc = ezdxf.readfile(yol)
        bk = C.D.boru_kesismeleri(doc)
        for l1, l2, (x, y) in bk['kesisme'][:30]:
            out.append(Bulgu('T11', 'FAIL', 'boru kesişmesi %s / %s' % (l1, l2), nokta=(x, y), pencere=pencere_yap([(x, y)])))
        for p, acik, lay in bk['kopru_hata'][:30]:
            out.append(Bulgu('T11', 'FAIL', 'köprü %s %s' % (lay, acik), nokta=(p.x, p.y), pencere=pencere_yap([(p.x, p.y)])))
        out.append(Bulgu('T11', 'INFO', 'pis su – temiz su üst üste geçiş (farklı düzlem, bilgi): %d' % len(bk['duzlem'])))
    except Exception as ex:
        out.append(Bulgu('T11', 'INFO', 'kesişme ayrıntısı alınamadı: %s' % ex))
    if not any(b.durum == 'FAIL' for b in out):
        out.insert(0, Bulgu('T11', 'PASS', 'MTY 0, önek 0, köprü 0, kesişme 0, elektrik 0, yazı 0, lejant var, audit 0'))
    return out


KAT_TESTLERI = [t01_balkon_suzgeci, t02_pis_su_bransman, t03_oda_ici_capraz, t04_sicak_su_daire, t05_sicak_soguk,
                t06_koridor_orta, t09_suzgec_sayisi, t10_kolon_kose]

TEST_ADI = {
    'T01': 'Balkon süzgeci bağlantı hedefi (yağmur inişi, kısa hat; pis su kolonuna ASLA)',
    'T02': 'Pis su branşmanı: uzunluk ≤ %.0f cm, açı {0,45,90}, mahal dışından dolaşmaz, her armatür bağlı' % BRANSMAN_MAX,
    'T03': 'Oda içi çapraz pis su hattı (duvardan > %.0f cm iç bölge)' % DUVAR_DIBI,
    'T04': 'Sıcak su daire dışı uzunluk = 0, kombiden başlar',
    'T05': 'Sıcak–soğuk paralellik (sabit ofset) ve kesişme',
    'T06': 'Koridor hatları koridor ortasında',
    'T07': 'Etiket–etiket / etiket–mimari yazı / etiket–hat çakışması, etiket boyu',
    'T08': 'Kolon şeması: sayaçlar zemin bandında, şebeke girişinde (solda); kat bantlarında sayaç yok',
    'T09': 'Islak hacim başına yer süzgeci = 1',
    'T10': 'Pis su kolonu ıslak hacim köşesinde (betonarme dışında)',
    'T11': 'denetle.py: MTY 0, ROTAS- öneki, köprü 0, kesişme 0, elektrik 0, yazı çakışması 0, lejant, audit',
}
