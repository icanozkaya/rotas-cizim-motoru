"""WC havalandırma izometrisi (kolon şeması) + hesap tabloları + lejant + notlar -> DXF (R2018, cm).

Tarz: kullanıcının new_block.dxf son paftasındaki izometri (ORNEK_DUZEN.md):
  düşey galvaniz şaft (3 kenar çizgisi), her katta Ø150 branşman + geri akış klapesi + flex + küp aspiratör,
  aspiratör yazısı "Wc Aspiratörü / 80 m3/h-50 pa / Ø150 mm", şaft üzerinde "150x150 / 240 m³/h" (döndürülmüş),
  şaft başında çatı tipi fan + "D3-5-8 / Çatı Tipi Fan / MEKANİK HAVALANDIRMA / 240 m³/h".
Katmanlar ROTAS- önekli. R2 (14.10.2026 B): MTY bloğu / mtylib / radyator importu YOK; bütün öğeler saf geometri.
Lejant otomatiktir: yalnız izometride çizilen öğeler, çizim sırasında sayılan ADET sütunuyla.
"""
import math, os, sys
import ezdxf
import ezdxf.bbox
from ezdxf.enums import TextEntityAlignment as TA
from ezdxf.math import ConstructionArc
from shapely.geometry import LineString, Polygon, MultiPoint, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hesap import tr, DIN, ZETA, FLEX_K, FLEX_L, V_SAFT, EMNIYET   # noqa: E402

C30 = math.cos(math.radians(30))
KAT = {  # ad: (renk, çizgi tipi)
    'ROTAS-WC-HAV-KANAL': (5, 'CONTINUOUS'),
    'ROTAS-WC-HAV-FLEX': (5, 'CONTINUOUS'),
    'ROTAS-WC-HAV-CIHAZ': (4, 'CONTINUOUS'),
    'ROTAS-WC-HAV-YAZI': (51, 'CONTINUOUS'),
    'ROTAS-WC-HAV-KAT': (8, 'DASHED'),
    'ROTAS-WC-HAV-DOSEME': (8, 'CONTINUOUS'),
    'ROTAS-HESAP': (7, 'CONTINUOUS'),
    'ROTAS-HESAP-YAZI': (7, 'CONTINUOUS'),
    'ROTAS-PAFTA': (8, 'CONTINUOUS'),
    'ROTAS-PAFTA-YAZI': (7, 'CONTINUOUS'),
    'ROTAS-DENEME': (1, 'CONTINUOUS'),
    'ROTAS-MASKE': (7, 'CONTINUOUS'),
}
YZ, KN, FX, CH, KT, DS = ('ROTAS-WC-HAV-YAZI', 'ROTAS-WC-HAV-KANAL', 'ROTAS-WC-HAV-FLEX', 'ROTAS-WC-HAV-CIHAZ',
                          'ROTAS-WC-HAV-KAT', 'ROTAS-WC-HAV-DOSEME')
H = 15.0          # yazı yüksekliği (kullanıcı örneği)


def kot_yaz(k):
    return '±0,00' if abs(k) < 1e-6 else (('+' if k > 0 else '-') + tr(abs(k), 2))


class Cizim:
    def __init__(self):
        d = ezdxf.new('R2018', setup=True)
        d.header['$INSUNITS'] = 5
        d.header['$LTSCALE'] = 10.0
        if 'ROTAS' not in d.styles:
            d.styles.add('ROTAS', font='arial.ttf')
        d.set_wipeout_variables(frame=0)
        for n, (c, lt) in KAT.items():
            d.layers.add(n, color=c, linetype=lt)
        self.doc, self.msp = d, d.modelspace()
        self.geo = []          # yazıların kaçınacağı çizgiler
        self.yazi = []         # (p, s, h, lay, al, rot, maske_kontrol)
        self.kutular = []      # yerleşmiş yazı kutuları (çakışma raporu)
        self.say = {}          # lejant adetleri: çizilen öğe -> adet

    def adet(self, k, n=1):
        self.say[k] = self.say.get(k, 0) + n

    # ---------------------------------------------------------------- temel
    def line(self, a, b, lay, engel=True):
        self.msp.add_line(a, b, dxfattribs={'layer': lay})
        if engel:
            self.geo.append(LineString([a, b]))

    def pl(self, pts, lay, kapali=False, engel=True):
        self.msp.add_lwpolyline([tuple(p) for p in pts], close=kapali, dxfattribs={'layer': lay})
        if engel and len(pts) > 1:
            self.geo.append(LineString(list(pts) + ([pts[0]] if kapali else [])))

    def geom(self, g, lay, engel=True):
        """shapely LineString / MultiLineString çiz"""
        if g.is_empty:
            return
        for p in (g.geoms if hasattr(g, 'geoms') else [g]):
            if p.geom_type == 'LineString' and len(p.coords) > 1:
                self.pl(list(p.coords), lay, engel=engel)

    def elips(self, c, R, lay, s=0.0, e=2 * math.pi):
        """yatay düzlemdeki R yarıçaplı dairenin izometrik görüntüsü (büyük eksen yatay)"""
        a = R * C30 * math.sqrt(2)
        self.msp.add_ellipse((c[0], c[1]), major_axis=(a, 0), ratio=0.57735, start_param=s, end_param=e,
                             dxfattribs={'layer': lay})
        n = 24
        pts = [(c[0] + a * math.cos(s + (e - s) * i / n), c[1] + a * 0.57735 * math.sin(s + (e - s) * i / n))
               for i in range(n + 1)]
        self.geo.append(LineString(pts))

    def text(self, p, s, h=H, lay=YZ, al='ML', rot=0.0, maske=True):
        self.yazi.append((tuple(p), s, h, lay, al, rot, maske))

    @staticmethod
    def kutu(p, s, h, al, rot):
        w = len(s) * h * 0.62
        ax = {'L': 0, 'C': 0.5, 'R': 1}[al[1]]
        ay = {'B': 0, 'M': 0.5, 'T': 1}[al[0]]
        x0, y0 = -ax * w, -ay * h
        pts = [(x0 - 2, y0 - 2), (x0 + w + 2, y0 - 2), (x0 + w + 2, y0 + h + 2), (x0 - 2, y0 + h + 2)]
        r = math.radians(rot)
        return Polygon([(p[0] + x * math.cos(r) - y * math.sin(r), p[1] + x * math.sin(r) + y * math.cos(r))
                        for x, y in pts])

    def yazilari_bas(self):
        """önce maskeler (yazı bir çizgiye değiyorsa WIPEOUT), sonra yazılar; yazı-yazı çakışmasını say"""
        AL = {'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER, 'BR': TA.BOTTOM_RIGHT, 'ML': TA.MIDDLE_LEFT,
              'MC': TA.MIDDLE_CENTER, 'MR': TA.MIDDLE_RIGHT, 'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT}
        from shapely import STRtree
        tree = STRtree(self.geo) if self.geo else None
        nmaske = 0
        for p, s, h, lay, al, rot, mk in self.yazi:
            k = self.kutu(p, s, h, al, rot)
            self.kutular.append(k)
            if mk and tree is not None and any(self.geo[i].intersects(k) for i in tree.query(k)):
                w_ = self.msp.add_wipeout([c for c in list(k.exterior.coords)[:-1]], dxfattribs={'layer': 'ROTAS-MASKE'})
                w_.dxf.layer = 'ROTAS-MASKE'
                nmaske += 1
        for p, s, h, lay, al, rot, mk in self.yazi:
            t = self.msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS'})
            t.set_placement(p, align=AL[al])
        cak = 0
        for i, a in enumerate(self.kutular):
            for b in self.kutular[i + 1:]:
                if a.intersection(b).area > 4.0:
                    cak += 1
        return nmaske, cak


# -------------------------------------------------------------------- izometrik öğeler
def P(o, x, y, z):
    return (o[0] + (x - y) * C30, o[1] + z + (x + y) * 0.5)


def saft_ciz(cz, o, w, d, z0, z1):
    """düşey dikdörtgen kanal (cm): görünen 3 düşey kenar + üst yüz + alt kapak ön kenarları"""
    a, b = w / 2, d / 2
    for x, y in ((-a, b), (-a, -b), (a, -b)):
        cz.line(P(o, x, y, z0), P(o, x, y, z1), KN)
    top = [P(o, -a, -b, z1), P(o, a, -b, z1), P(o, a, b, z1), P(o, -a, b, z1)]
    cz.pl(top, KN, kapali=True)
    cz.pl([P(o, -a, b, z0), P(o, -a, -b, z0), P(o, a, -b, z0)], KN)
    return P(o, a, -b, 0)[0] - o[0], P(o, -a, b, 0)[0] - o[0]       # sağ / sol silüet X ofseti


def kup(o, c, a):
    """merkez c (3B) kenarı a küp: dış hat + 3 iç kenar"""
    h = a / 2
    V = {(sx, sy, sz): P(o, c[0] + sx * h, c[1] + sy * h, c[2] + sz * h) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)}
    hull = MultiPoint(list(V.values())).convex_hull
    on = V[(-1, -1, 1)]
    ic = [(on, V[(1, -1, 1)]), (on, V[(-1, 1, 1)]), (on, V[(-1, -1, -1)])]
    return hull, ic


def brans_ciz(cz, xs, yb, sag, r, Lb=80.0, Lf=55.0, ka=30.0):
    """xs: şaft silüet X'i, yb: branşman kotu (ekran). sag=True: +x yönü (sağ-yukarı), False: ayna (sol-yukarı).
    Dönüş: dirsek noktası E, küp sınır kutusu"""
    m = 1 if sag else -1
    u = (m * C30, 0.5)
    f = (m * C30, -0.5)
    S = (xs, yb)
    E = (S[0] + u[0] * Lb, S[1] + u[1] * Lb)
    F = (E[0] + f[0] * Lf, E[1] + f[1] * Lf)
    # küp: flex ucunun ilerisinde
    oc = (F[0] + f[0] * ka * 0.75, F[1] + f[1] * ka * 0.75)
    hull, ic = kup(oc, (0, 0, 0), ka)
    ax = LineString([S, E, F])
    for s_ in (r, -r):
        g = ax.offset_curve(s_, join_style=2, mitre_limit=5.0)
        g = g.difference(hull.buffer(0.01))
        # kanal ve flex parçaları ayrı katman
        for part in (g.geoms if hasattr(g, 'geoms') else [g]):
            cs = list(part.coords)
            cz.pl(cs, KN)
    # akordeon (flex) halkaları: E'den F'ye 6 cm arayla
    n = (-f[1], f[0])
    L = Lf
    t = 8.0
    while t < L - 2:
        c = (E[0] + f[0] * t, E[1] + f[1] * t)
        seg = LineString([(c[0] - n[0] * r, c[1] - n[1] * r), (c[0] + n[0] * r, c[1] + n[1] * r)])
        if not seg.intersects(hull):
            cz.line(seg.coords[0], seg.coords[1], FX)
        t += 6.0
    # flanş (branş başı) + geri akış klapesi (iki flanş + köşegen)
    nu = (-u[1], u[0])
    def flans(t_, e=3.0):
        c = (S[0] + u[0] * t_, S[1] + u[1] * t_)
        return (c[0] - nu[0] * (r + e), c[1] - nu[1] * (r + e)), (c[0] + nu[0] * (r + e), c[1] + nu[1] * (r + e))
    a1, b1 = flans(10.0)
    a2, b2 = flans(24.0)
    cz.line(a1, b1, KN)
    cz.line(a2, b2, KN)
    p1 = (S[0] + u[0] * 12 - nu[0] * r * 0.9, S[1] + u[1] * 12 - nu[1] * r * 0.9)
    p2 = (S[0] + u[0] * 22 + nu[0] * r * 0.9, S[1] + u[1] * 22 + nu[1] * r * 0.9)
    cz.line(p1, p2, KN)
    # küp
    cz.pl(list(hull.exterior.coords)[:-1], CH, kapali=True)
    for a, b in ic:
        cz.line(a, b, CH)
    return E, F, hull.bounds


def fan_ciz(cz, xc, y0, k=1.0):
    """çatı tipi fan (izometri): boyun + şapka elipsi + kubbe yayı + üst halka. k: ölçek. Dönüş: üst Y"""
    Rb, Rh, hn, hd = 14.0 * k, 42.0 * k, 14.0 * k, 34.0 * k
    ab, ah = Rb * C30 * math.sqrt(2), Rh * C30 * math.sqrt(2)
    cz.elips((xc, y0), Rb, CH, math.pi, 2 * math.pi)
    yh = y0 + hn
    cz.line((xc - ab, y0), (xc - ab, yh - ah * 0.57735 * math.sqrt(max(0.0, 1 - (ab / ah) ** 2))), CH)
    cz.line((xc + ab, y0), (xc + ab, yh - ah * 0.57735 * math.sqrt(max(0.0, 1 - (ab / ah) ** 2))), CH)
    cz.elips((xc, yh), Rh, CH)
    arc = ConstructionArc.from_3p((xc + ah, yh), (xc - ah, yh), (xc, yh + hd))      # saat yönü tersine: sağdan sola üstten
    cz.msp.add_arc(arc.center, arc.radius, arc.start_angle, arc.end_angle, dxfattribs={'layer': CH})
    a0, a1 = arc.start_angle, arc.end_angle if arc.end_angle > arc.start_angle else arc.end_angle + 360
    cz.geo.append(LineString([(arc.center[0] + arc.radius * math.cos(math.radians(a0 + (a1 - a0) * i / 20)),
                               arc.center[1] + arc.radius * math.sin(math.radians(a0 + (a1 - a0) * i / 20))) for i in range(21)]))
    cz.elips((xc, yh + hd - 5.0 * k), 9.0 * k, CH)
    return yh + hd


# -------------------------------------------------------------------- izometri
def izometri(cz, g, r, X0=0.0, Y0=0.0):
    katlar = g['katlar']
    S = r['saftlar']
    D = g['kabul']['baglanti_cap'] / 10.0           # cm
    rr = D / 2
    ayna = any(len([a for a in s['asps'] if a['ki'] == ki]) > 1 for s in S for ki in range(len(katlar)))
    colw = 470.0 + (300.0 if ayna else 0.0)
    xs0 = X0 + 380.0 + (300.0 if ayna else 0.0)
    cati = g['cati_kot'] * 100.0
    fan_z = cati + g['cati_ustu'] * 100.0
    xR = xs0 + colw * (len(S) - 1) + 330.0
    xL = X0
    # kat bantları
    for i, k in enumerate(katlar):
        y = Y0 + k['kot'] * 100.0
        cz.line((xL, y), (xR, y), KT)
        cz.text((xL + 5, y + 8), kot_yaz(k['kot']), 13, YZ, 'BL')
        cz.text((xL + 5, y + k.get('h', 3.0) * 50.0), k['ad'], 20, YZ, 'ML')
    yc = Y0 + cati
    cz.line((xL, yc), (xR, yc), KT)
    cz.text((xL + 5, yc + 8), kot_yaz(g['cati_kot']), 13, YZ, 'BL')
    cz.text((xL + 5, yc + 40), 'ÇATI', 20, YZ, 'BL')
    for j, s in enumerate(S):
        xc = xs0 + colw * j
        o = (xc, Y0)
        w, d = s['w'] / 10.0, s['h'] / 10.0
        zb = {}
        for a in s['asps']:
            k = katlar[a['ki']]
            yuk = min(s['yuk'] * 100.0, (k.get('h', 3.0) * 100.0) - 60.0)       # çizimde branş tavan altında kalır
            zb[a['ki']] = k['kot'] * 100.0 + yuk
        z_alt = min(zb.values()) - 25.0
        xr_off, xl_off = saft_ciz(cz, o, w, d, z_alt, fan_z)
        cz.adet('saft')
        # çatı döşemesi parçası (şaft geçişi)
        for dy in (0.0, -15.0):
            cz.line((xc - 70, Y0 + cati + dy), (xc + xl_off, Y0 + cati + dy), DS)
            cz.line((xc + xr_off, Y0 + cati + dy), (xc + 70, Y0 + cati + dy), DS)
        # branşmanlar
        say = {}
        for a in s['asps']:
            n = say.get(a['ki'], 0)
            say[a['ki']] = n + 1
            sag = n % 2 == 0
            yb = Y0 + zb[a['ki']] - 70.0 * (n // 2)
            xs = xc + (xr_off if sag else xl_off)
            E, F, bb = brans_ciz(cz, xs, yb, sag, rr)
            for k_ in ('brans', 'klape', 'flex', 'aspirator'):
                cz.adet(k_)
            mah = ' + '.join(m['ad'] for m in a['mahaller'])
            sat = ['Wc Aspiratörü', f"{a['kademe']} m3/h-{g['kabul']['asp_basinc']} pa", f"Ø{g['kabul']['baglanti_cap']} mm",
                   f"{a['daire']} · {mah}"]
            tx = bb[2] + 10 if sag else bb[0] - 10
            ty = yb + 42
            for i_, t in enumerate(sat):
                cz.text((tx, ty - i_ * 22), t, H if i_ < 3 else 12, YZ, 'TL' if sag else 'TR')
        # şaft bölüm etiketleri (sağda, döndürülmüş): "150x150" / "240 m³/h"
        for b in s['bol']:
            y1 = Y0 + (zb[b['ki']])
            nxt = [zb[k] for k in zb if k > b['ki']]
            if nxt:
                ym = Y0 + (zb[b['ki']] + min(nxt)) / 2 + 20
            else:
                ym = Y0 + fan_z - 64.0          # çatı fanı şapkasının altında
            xt = xc + xr_off + 4
            cz.text((xt + H * 0.5, ym), f"{s['w']}x{s['h']}", H, YZ, 'MC', 90)
            cz.text((xt + H * 1.9, ym), f"{b['q']} m³/h", H, YZ, 'MC', 90)
        # çatı fanı
        ytop = fan_ciz(cz, xc, Y0 + fan_z)
        cz.adet('fan')
        f = s['fan']
        sat = [s['daireler'], f"Çatı Tipi Fan ÇF-{j + 1} ({f['ad']} sınıfı)", 'MEKANİK HAVALANDIRMA',
               f"{s['Q']} m³/h - {tr(s['p_fan'], 0)} Pa"]
        for i_, t in enumerate(reversed(sat)):
            cz.text((xc, ytop + 20 + i_ * 24), t, H, YZ, 'BC')
        cz.text((xc, ytop + 20 + 4 * 24 + 6), s['ad'], 22, YZ, 'BC')
    return (xL, Y0 - 20, xR, Y0 + fan_z + 300)


# -------------------------------------------------------------------- tablolar
def tablo(cz, x0, y0, baslik, bas, satirlar, h=11.0, notlar=None):
    """sol üst (x0, y0); sütun genişliği içerikten. Dönüş: (genişlik, yükseklik)"""
    cw = []
    for c in range(len(bas)):
        L = max([len(l) for l in bas[c].split('\n')] + [len(str(r_[c])) for r_ in satirlar])
        cw.append(L * h * 0.70 + 18)
    W = sum(cw)
    wn = len(baslik) * h * 1.25 * 0.75 + 40      # başlık ve notlar tablo genişliğine sığsın
    if notlar:
        wn = max(wn, max(len(n) for n in notlar) * h * 0.9 * 0.62 + 24)
    if True:
        if wn > W:
            cw = [c * wn / W for c in cw]
            W = wn
    rh, hh = h * 2.0, h * 1.9 * max(len(b.split('\n')) for b in bas) + 4
    th = h * 2.6
    Ht = th + hh + rh * len(satirlar) + (len(notlar or []) * h * 1.7 + 8 if notlar else 0)
    L, Hs = 'ROTAS-HESAP', 'ROTAS-HESAP-YAZI'
    cz.pl([(x0, y0), (x0 + W, y0), (x0 + W, y0 - Ht), (x0, y0 - Ht)], L, kapali=True, engel=False)
    cz.text((x0 + W / 2, y0 - th / 2), baslik, h * 1.25, Hs, 'MC', maske=False)
    y = y0 - th
    cz.line((x0, y), (x0 + W, y), L, engel=False)
    x = x0
    for c, b in enumerate(bas):
        ls = b.split('\n')
        for i, l in enumerate(ls):
            cz.text((x + cw[c] / 2, y - hh / 2 + (len(ls) - 1) * h * 0.9 - i * h * 1.8), l, h, Hs, 'MC', maske=False)
        x += cw[c]
    y -= hh
    cz.line((x0, y), (x0 + W, y), L, engel=False)
    for r_ in satirlar:
        x = x0
        for c, v in enumerate(r_):
            cz.text((x + cw[c] / 2, y - rh / 2), str(v), h, Hs, 'MC', maske=False)
            x += cw[c]
        y -= rh
        cz.line((x0, y), (x0 + W, y), L, engel=False)
    x = x0
    for c in cw[:-1]:
        x += c
        cz.line((x, y0 - th), (x, y), L, engel=False)
    if notlar:
        for i, n in enumerate(notlar):
            cz.text((x0 + 8, y - 6 - h * 0.6 - i * h * 1.7), n, h * 0.9, Hs, 'ML', maske=False)
    return W, Ht


def tablolar(cz, g, r, x0, y0, wmax):
    katad = {k['kod']: k['ad'] for k in g['katlar']}
    K = g['kabul']
    # 1. mahal debi tablosu
    rows = []
    for s in r['saftlar']:
        for a in s['asps']:
            for m in a['mahaller']:
                rows.append([s['ad'], katad[a['kat']], a['daire'], m['ad'], m['tip'],
                             tr(m.get('alan_m2', 0), 2) if m.get('alan_m2') else '-', m['din_s'], m['din_k'], K['q_oda'],
                             tr(m['n_hd'], 1) if m.get('n_hd') else '-', a['q'], f"{a['kademe']} m³/h - {K['asp_basinc']} Pa"])
    T1 = ('PENCERESİZ ISLAK HACİM DEBİ HESABI (DIN 18017-3 ve ROTAŞ / kullanıcı kabulü)',
          ['Şaft', 'Kat', 'Daire', 'Mahal', 'Tip', 'Alan\n(m²)', 'DIN sürekli\n(m³/h)', 'DIN kesikli\n(m³/h)',
           'Kabul\n(m³/h)', 'Hava değ.\n(1/h)', 'Bağlantı\n(m³/h)', 'Aspiratör\nkademesi'], rows,
          [f"Tasarım debisi kullanıcı kabulü {K['q_oda']} m³/h / hacim (örnek proje). DIN 18017-3 asgari: banyo 40/60, WC 20/30 m³/h (sürekli/kesikli).",
           "Aynı daire + aynı şaft + aynı kat hacimleri tek iki kademeli aspiratöre (80/160 m³/h) bağlanır. Hava değ.: h = 2,60 m."])
    # 2. şaft bölümleri
    rows = []
    for s in r['saftlar']:
        for b in s['bol']:
            rows.append([s['ad'], f"{b['alt']} → {b['ust']}", b['q'], f"{s['w']}x{s['h']}", tr(b['v'], 2), tr(b['R'], 2),
                         tr(b['L'], 2), tr(b['RL'], 1), tr(b['zeta'], 1), tr(b['pd'], 1), tr(b['Z'], 1), tr(b['dp'], 1)])
        rows.append([s['ad'], 'ŞAFT TOPLAMI', s['Q'], f"Øeş {s['de']:.0f}", '', '', '', '', '', '', '', tr(s['dp_saft'], 1)])
    T2 = ('ŞAFT KESİTİ VE BASINÇ KAYBI HESABI (galvaniz kanal, Darcy-Weisbach)',
          ['Şaft', 'Bölüm', 'Debi\n(m³/h)', 'Kesit\n(mm)', 'v\n(m/s)', 'R\n(Pa/m)', 'L\n(m)', 'R·L\n(Pa)', 'Σζ', 'Pd\n(Pa)',
           'Z\n(Pa)', 'ΔP\n(Pa)'], rows,
          [f"Kesit en büyük debiye göre sabit, v ≤ {tr(V_SAFT, 1)} m/s, en az 150x150. ζ: T düz geçiş {tr(ZETA['t_duz'], 1)}; "
           f"üst bölüm çatı geçişi {tr(ZETA['cati_giris'], 1)} + çatı başlığı {tr(ZETA['cati_baslik'], 1)}.",
           "Şaft (mimari) iç ölçüsü en az kanal + 10 cm; kanal sızdırmaz, ek yerleri silikonlu."])
    # 3. branş + fan
    rows = []
    for j, s in enumerate(r['saftlar']):
        k = s['kritik']
        rows.append([s['ad'], s['daireler'], s['Q'], f"{s['w']}x{s['h']}", f"{s['saft_ic'][0]}x{s['saft_ic'][1]} cm",
                     f"{katad[k['kat']]} {k['daire']}", tr(k['dp'], 1), tr(s['dp_saft'], 1), tr(s['kritik_top'], 1),
                     tr(s['p_fan'], 1), f"ÇF-{j + 1}: {s['Q']} m³/h - {tr(max(s['p_fan'], 0), 0)} Pa",
                     f"{s['fan']['ad']} (≈{tr(s['fan']['p_calisma'], 0)} Pa)"])
    T3 = ('ASPİRATÖR BRANŞI KONTROLÜ VE ÇATI TİPİ FAN SEÇİMİ',
          ['Şaft', 'Daireler', 'Q fan\n(m³/h)', 'Kanal\n(mm)', 'Şaft iç\nölçüsü', 'Kritik\nbranş', 'Branş ΔP\n(Pa)',
           'Şaft ΔP\n(Pa)', 'Kritik hat\n(Pa)', 'Fan P\n(+%10)', 'Çatı tipi fan', 'Sınıf\n(tipik eğri)'], rows,
          [f"Branş: Ø{K['baglanti_cap']} spiro + {tr(FLEX_L, 1)} m flex (x{tr(FLEX_K, 1)}), ζ dirsek {tr(ZETA['dirsek'], 1)} + geri akış klapesi "
           f"{tr(ZETA['klape'], 1)} + T-branş {tr(ZETA['t_brans'], 1)}; aspiratör basıncı {K['asp_basinc']} Pa ile karşılanır.",
           f"Çatı fanı: Q = Σ aspiratör, P = şaft kaybı x {tr(EMNIYET, 2)}. Fan sınıfı tipik eğriden; marka/model üretici kataloğundan teyit edilir."])
    TT = [T1, T2, T3]
    if g.get('pencereli'):
        TT.append(('MEKANİK HAVALANDIRMAYA ALINMAYAN ISLAK HACİMLER (pencereli / şaftsız)',
                   ['Kat', 'Daire', 'Mahal', 'Gerekçe'],
                   [[katad.get(m['kat'], m['kat']), m['daire'], m['ad'], m.get('neden', '')] for m in g['pencereli']],
                   ['Pencere: dış duvar / balkon teması + pencere ölçü yazısı (algila.py). Kontrol edilmelidir.']))
    y = y0
    for T in TT:
        w_, h_ = tablo(cz, x0, y, *T[:3], notlar=T[3])
        y -= h_ + 60
    return y


def lejant(cz, x0, y0):
    """Otomatik lejant + adet tablosu: yalnız izometride çizilen kendi öğelerimiz (saf geometri), adet çizimden sayılır."""
    L, Hs = 'ROTAS-HESAP', 'ROTAS-HESAP-YAZI'
    TUM = [('saft', 'Egzoz şaftı — galvaniz kanal (ör. 150x150)'), ('brans', 'Ø150 bağlantı kanalı (spiro)'),
           ('klape', 'Geri akış klapesi'), ('flex', 'İzoleli flex bağlantı'),
           ('aspirator', 'Wc aspiratörü 80/160 m³/h - 50 Pa - Ø150 mm'), ('fan', 'Çatı tipi fan (izometri)'),
           ('kat', 'Kat döşemesi / kat bandı')]
    sat = [(k, a) for k, a in TUM if k == 'kat' or cz.say.get(k)]
    rh, sw, tw, aw = 70.0, 140.0, 520.0, 90.0
    W, Ht = sw + tw + aw, 40 + rh * len(sat)
    cz.pl([(x0, y0), (x0 + W, y0), (x0 + W, y0 - Ht), (x0, y0 - Ht)], L, kapali=True, engel=False)
    cz.text((x0 + (sw + tw) / 2, y0 - 20), 'WC HAVALANDIRMA LEJANTI (otomatik)', 14, Hs, 'MC', maske=False)
    cz.text((x0 + sw + tw + aw / 2, y0 - 20), 'ADET', 14, Hs, 'MC', maske=False)
    cz.line((x0, y0 - 40), (x0 + W, y0 - 40), L, engel=False)
    cz.line((x0 + sw, y0 - 40), (x0 + sw, y0 - Ht), L, engel=False)
    cz.line((x0 + sw + tw, y0), (x0 + sw + tw, y0 - Ht), L, engel=False)
    for i, (key, s) in enumerate(sat):
        yc = y0 - 40 - rh * (i + 0.5)
        cz.text((x0 + sw + 12, yc), s, 12, Hs, 'ML', maske=False)
        cz.text((x0 + sw + tw + aw / 2, yc), f"{cz.say[key]} ad." if key in cz.say else '-', 12, Hs, 'MC', maske=False)
        if i < len(sat) - 1:
            cz.line((x0, yc - rh / 2), (x0 + W, yc - rh / 2), L, engel=False)
        xc = x0 + sw / 2
        if key == 'saft':
            saft_ciz(cz, (xc, yc - 30), 15, 15, 0, 55)
        elif key == 'brans':
            u = (C30, 0.5)
            a = (xc - 40, yc - 18)
            b = (a[0] + u[0] * 90, a[1] + u[1] * 90)
            ax = LineString([a, b])
            for s_ in (7.5, -7.5):
                cz.geom(ax.offset_curve(s_), KN, engel=False)
        elif key == 'klape':
            u, nu = (C30, 0.5), (-0.5, C30)
            c0 = (xc - 30, yc - 12)
            for t in (0, 16):
                c = (c0[0] + u[0] * t, c0[1] + u[1] * t)
                cz.line((c[0] - nu[0] * 11, c[1] - nu[1] * 11), (c[0] + nu[0] * 11, c[1] + nu[1] * 11), KN, engel=False)
            for s_ in (7.5, -7.5):
                a = (c0[0] - u[0] * 20 + nu[0] * s_, c0[1] - u[1] * 20 + nu[1] * s_)
                b = (c0[0] + u[0] * 40 + nu[0] * s_, c0[1] + u[1] * 40 + nu[1] * s_)
                cz.line(a, b, KN, engel=False)
            cz.line((c0[0] + u[0] * 2 - nu[0] * 6.5, c0[1] + u[1] * 2 - nu[1] * 6.5),
                    (c0[0] + u[0] * 14 + nu[0] * 6.5, c0[1] + u[1] * 14 + nu[1] * 6.5), KN, engel=False)
        elif key == 'flex':
            f, n = (C30, -0.5), (0.5, C30)
            a = (xc - 40, yc + 14)
            for s_ in (7.5, -7.5):
                cz.line((a[0] + n[0] * s_, a[1] + n[1] * s_), (a[0] + f[0] * 80 + n[0] * s_, a[1] + f[1] * 80 + n[1] * s_),
                        FX, engel=False)
            t = 5.0
            while t < 78:
                c = (a[0] + f[0] * t, a[1] + f[1] * t)
                cz.line((c[0] - n[0] * 7.5, c[1] - n[1] * 7.5), (c[0] + n[0] * 7.5, c[1] + n[1] * 7.5), FX, engel=False)
                t += 6.0
        elif key == 'aspirator':
            hull, ic = kup((xc, yc), (0, 0, 0), 30)
            cz.pl(list(hull.exterior.coords)[:-1], CH, kapali=True, engel=False)
            for a, b in ic:
                cz.line(a, b, CH, engel=False)
        elif key == 'fan':
            # küçük fan: aynı fonksiyon; yazı engeli listesinden çıkarılır (lejant hücresi)
            n0 = len(cz.geo)
            fan_ciz(cz, xc, yc - 14, 0.6)
            del cz.geo[n0:]
        elif key == 'kat':
            cz.line((xc - 55, yc), (xc + 55, yc), KT, engel=False)
    return W, Ht


NOTLAR = [
    'NOTLAR',
    '1. Penceresiz ıslak hacimler (WC, banyo, duş) mekanik egzozla havalandırılır. Debiler DIN 18017-3 asgari değerleriyle',
    '   karşılaştırılmış, tasarımda kullanıcı kabulü (hacim başına 80 m³/h, iki kademeli 80/160 m³/h aspiratör) esas alınmıştır.',
    '2. Aspiratörler 50 Pa, Ø150 mm çıkışlı; aydınlatma anahtarıyla çalışır, kapandıktan sonra zaman rölesiyle 3-5 dk devam eder.',
    '3. Her aspiratör çıkışında geri akış klapesi bulunur. Ortak şaft bağlantısında yangın yönetmeliğine uygun yangın damperi /',
    '   EI sınıflı şaft mimari ve yangın projesiyle koordine edilir.',
    '4. Şaft kanalı galvaniz sac, sızdırmaz; şaft iç ölçüsü en az kanal ölçüsü + 10 cm. Branşmanlar asma tavan içinde.',
    '5. Egzoz yapılan hacimlerin kapısında 2 cm kapı altı boşluğu veya en az 150 cm² transfer menfezi bırakılır.',
    '6. Çatı tipi fan çatı üst kotunun en az 1,00 m üzerinde, titreşim takozlu kaide üzerinde; marka/model katalogdan teyit edilir.',
]


def pafta(g, r, cikti):
    cz = Cizim()
    bb = izometri(cz, g, r, 0.0, 0.0)
    ytab = bb[1] - 160
    yson = tablolar(cz, g, r, bb[0], ytab, bb[2] - bb[0])
    # lejant + notlar: izometrinin sağı
    xl = max(bb[2] + 120, 0)
    W, Ht = lejant(cz, xl, bb[3] - 120)
    yn = bb[3] - 120 - Ht - 60
    for i, n in enumerate(NOTLAR):
        cz.text((xl, yn - i * 26), n, 14 if i == 0 else 12, 'ROTAS-PAFTA-YAZI', 'TL', maske=False)
    # başlık
    ttl = 'WC HAVALANDIRMA İZOMETRİSİ (KOLON ŞEMASI) — ÖLÇEKSİZ'
    cz.text((bb[0], bb[3] + 60), ttl, 30, 'ROTAS-PAFTA-YAZI', 'BL', maske=False)
    cz.text((bb[0], bb[3] + 25), g.get('proje', ''), 16, 'ROTAS-PAFTA-YAZI', 'BL', maske=False)
    if g.get('deneme'):
        cz.text((bb[0], bb[3] + 110), 'DENEME — örnek / algılanan değerlerle üretildi, kullanıcı onayı gerekir', 30,
                'ROTAS-DENEME', 'BL', maske=False)
    nm, cak = cz.yazilari_bas()
    # çerçeve
    ext = ezdxf.bbox.extents(cz.msp, fast=True)
    m = 60
    cz.msp.add_lwpolyline([(ext.extmin.x - m, ext.extmin.y - m), (ext.extmax.x + m, ext.extmin.y - m),
                           (ext.extmax.x + m, ext.extmax.y + m), (ext.extmin.x - m, ext.extmax.y + m)], close=True,
                          dxfattribs={'layer': 'ROTAS-PAFTA'})
    os.makedirs(os.path.dirname(os.path.abspath(cikti)), exist_ok=True)
    cz.doc.saveas(cikti)
    return dict(maske=nm, yazi_cakisma=cak, cerceve=(ext.extmin.x - m, ext.extmin.y - m, ext.extmax.x + m, ext.extmax.y + m))
