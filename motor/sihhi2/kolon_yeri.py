"""sihhi2 — tur 7 (15.10.2026 (D) ikinci geri bildirim, `RED_sihhi_pissu_kolonu_kolon_saft_icinde.png`):
pis su kolonu betonarme kolon/perde, mekanik havalandırma şaftı ('mek. havl.'), tesisat / k.bac. şaftı İÇİNDE ya da ona
DEĞER durumda olmaz — tüm katlarda, P1–P9.

Yasak bölge F (her kat, mimari tanıma):
  - betonarme: `K.cols` ∪ ANSI taramaları (`K.R` 'H')
  - şaft: havalandırma şaftı kutusu (`K.saftlar`, kanal dairesi + çevreleyen duvar kutusu) ∪ plan.saft_poligonlari
    (k.bac. / en. odası / tesisat şaftı hücreleri) ∪ şaftın 'mek.' / 'havl.' yazısı (kullanıcı şaftı bu yazıyla görüyor;
    kolon sembolü şaft yazısının üstüne binmez)
Kural: kolon sembolünün dış çemberi (r 10) betonarme/şafta >= 5 cm (merkez >= 15 cm), şaft yazısına >= 2 cm.

Kullanıcının kolon merkezi (tasarim_new_block.json 'kolon_merkez') kuralı herhangi bir katta ihlal ediyorsa kolon,
TÜM katlarda geçerli olan (eksen sürekliliği, T12) en yakın KÖŞE noktasına taşınır: ıslak hacmin içinde (duvar yüzünden
12 cm: çember duvara 2 cm), F'den uzak, armatür / duş teknesi / kapı açıklığı / diğer kolonlar dışında. Aday köşeler
geçerli bölgenin (mitre ofsetli kısıt poligonlarının kesişimi) köşe noktalarıdır; puan = kullanıcı merkezine uzaklık
+ 15 × köşe sınıfı (0: duvar + betonarme/şaft yüzü köşesi, 1: duvar + armatür / iki duvar, 2: tek duvar, 3: serbest). Taşınan kolonda boru kolon MERKEZİNE yönelir ve çemberde (r 10) biter (radyal; kullanıcının
çiziminde de hat kolon bloğunun merkezine gider, dolgunun altında kalır), kelepçe kolu en yakın duvara bakar.
"""
import math

from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

KOLON_R = 10.0
F_ACIKLIK = 5.0         # çember -> betonarme / şaft (cm)
YAZI_ACIKLIK = 2.0      # çember -> şaft yazısı
DUVAR_ACIKLIK = 2.0     # çember -> ıslak hacim duvar yüzü (köşeye yaslı)
ARM_ACIKLIK = 3.0       # çember -> armatür kutusu / duş teknesi
MITRE = dict(join_style=2, mitre_limit=10.0)


def _bos():
    return Polygon()


def beton(K):
    gs = [c for c in K.cols]
    for a in K.R:
        if a[0] == 'H' and 'ANSI' in str(a[2]).upper() and len(a[1]) >= 4:
            try:
                g = Polygon(a[1])
                if g.is_valid and g.area > 50:
                    gs.append(g)
            except Exception:
                pass
    return unary_union(gs) if gs else _bos()


def saft_yazilari(K):
    """'mek.' / 'havl.' (ve diğer şaft adları) yazılarının kutuları"""
    out = []
    for a in K.R:
        if a[0] != 'T':
            continue
        s = a[2][0].strip().lower()
        if not (s.startswith('mek') or s.startswith('havl') or 'k.bac' in s or 'şaft' in s or 'saft' in s):
            continue
        if s.startswith('mekanik kald'):
            continue
        h = float(a[2][1])
        p0, p1 = a[1][0], a[1][1]
        # kayıttaki ikinci nokta yazı sonunu vermiyor (çizimde 'havl.' ~26 cm görünüyor, kayıt 12 cm): karakter başına 0,6 h
        w = max(p1[0] - p0[0], 0.6 * h * len(s))
        out.append(box(p0[0], p0[1] - 0.3 * h, p0[0] + w, p0[1] + 1.1 * h))
    return out


def mimari_kutular(K, c, R=150.0):
    """c çevresindeki mimari küçük dikdörtgen hücreler (ocak/tezgâh, makine nişi, duş teknesi, küvet, armatür kutusu;
    0,05–0,6 m², dikdörtgensi, c'yi içermeyen): kolon sembolü üstüne en çok 2 cm biner"""
    from shapely.ops import polygonize
    W = box(c[0] - R, c[1] - R, c[0] + R, c[1] + R)
    segs = []
    for a in K.R:
        if a[0] not in 'LP' or len(a[1]) < 2:
            continue
        g = LineString(a[1])
        if g.intersects(W):
            segs.append(g.intersection(W))
    if not segs:
        return []
    out = []
    for g in polygonize(unary_union(segs)):
        if 500 <= g.area <= 0.6e4 and g.area > 0.85 * g.envelope.area and not g.buffer(2).contains(Point(c)):
            out.append(g)
    return out


def yasak_bolge(K, saft_u=None):
    """(betonarme, şaft, şaft yazıları) — kat koordinatında"""
    b = beton(K)
    sg = [s['poly'] for s in K.saftlar] + [Point(s['c']).buffer(s.get('r', 7) + 3) for s in K.saftlar]
    if saft_u is not None and not saft_u.is_empty:
        sg.append(saft_u)
    s = unary_union(sg) if sg else _bos()
    y = unary_union(saft_yazilari(K)) if K.R else _bos()
    return b, s, y


def olc(c, b, s, y):
    """kolon merkezi c için çember (r 10) açıklıkları"""
    cc = Point(c).buffer(KOLON_R, resolution=32)
    return dict(beton=round(cc.distance(b), 1) if not b.is_empty else 999.0,
                saft=round(cc.distance(s), 1) if not s.is_empty else 999.0,
                yazi=round(cc.distance(y), 1) if not y.is_empty else 999.0)


def ihlal(o):
    return o['beton'] < F_ACIKLIK - 0.05 or o['saft'] < F_ACIKLIK - 0.05 or o['yazi'] < YAZI_ACIKLIK - 0.05


def _oda(K, c):
    """kolonun ıslak hacmi: kontrolörün ıslak hacim poligonu (T10 köşe ölçüsüyle aynı; armatür çizgileriyle bölünmez),
    yoksa plan mahal poligonu"""
    kb = getattr(K, 'kb', None) or {}
    ad = [dict(name=r['name'], poly=r['poly'], islak=bool(r.get('islak'))) for r in kb.get('rooms', [])
          if not r.get('balkon') and r['poly'].distance(Point(c)) < 20]
    if not ad:
        ad = [dict(r, islak=r['tip'] in ('islak', 'mutfak')) for r in K.rooms if r['poly'].distance(Point(c)) < 20]
    if not ad:
        return None
    # ıslak hacim önce; kolon mutfak tezgâhı ucunda antre/koridor poligonundaysa (P7) o mahal
    r = min(ad, key=lambda r: (not (r['islak'] and r['poly'].distance(Point(c)) < 20), r['poly'].distance(Point(c)),
                               r['poly'].area))
    if r['poly'].geom_type == 'MultiPolygon':
        r = dict(r, poly=max(r['poly'].geoms, key=lambda g: g.distance(Point(c)) * -1e6 + g.area))
    return r


def gecerli_bolge(K, c, b, s, y, armatur, diger_kolonlar, duvar=DUVAR_ACIKLIK):
    """kat koordinatında c çevresindeki geçerli kolon merkezleri bölgesi"""
    r = _oda(K, c)
    W = box(c[0] - 160, c[1] - 160, c[0] + 160, c[1] + 160)
    if r is not None:
        V = r['poly'].buffer(-(KOLON_R + duvar), **MITRE).intersection(W)
    else:                                   # o katta ıslak hacim yok (geçiş katı): yalnız duvar katısı dışı
        V = W.difference(K.S.buffer(KOLON_R + 0.5, **MITRE))
    V = V.difference(b.buffer(KOLON_R + F_ACIKLIK, **MITRE))
    V = V.difference(s.buffer(KOLON_R + F_ACIKLIK, **MITRE))
    V = V.difference(y.buffer(KOLON_R + YAZI_ACIKLIK, **MITRE))
    for g in armatur:
        if g.distance(Point(c)) < 200:
            V = V.difference(g.buffer(KOLON_R + ARM_ACIKLIK, **MITRE))
    for g in mimari_kutular(K, c):
        if not g.intersects(s.buffer(1)):
            V = V.difference(g.buffer(KOLON_R - 2.0, **MITRE))
    V = V.difference(K.kapi_u.buffer(KOLON_R + 15, **MITRE))
    for q in diger_kolonlar:
        V = V.difference(Point(q).buffer(2 * KOLON_R + 15))
    return V, r


def _kose_noktalari(V):
    out = []
    for g in (V.geoms if hasattr(V, 'geoms') else [V]):
        if g.is_empty or g.geom_type != 'Polygon' or g.area < 1.0:
            continue
        for ring in [g.exterior] + list(g.interiors):
            out += [tuple(p) for p in list(ring.coords)[:-1]]
    return out


def duvar_acisi(c, oda_poly):
    """kelepçe kolu: en yakın duvar yüzüne (0/90/180/270)"""
    if oda_poly is None:
        return 0.0
    from shapely.ops import nearest_points
    q = nearest_points(oda_poly.exterior, Point(c))[0]
    dx, dy = q.x - c[0], q.y - c[1]
    if abs(dx) >= abs(dy):
        return 0.0 if dx >= 0 else 180.0
    return 90.0 if dy >= 0 else 270.0


def _kademe(p, Ks, c0, yb, armatur_k, duvar=DUVAR_ACIKLIK, tol=1.5):
    """aday köşe sınıfı (küçük = iyi): 0 = ıslak hacim duvarına VE ihlal edilen betonarme/şaft yüzüne (5 cm) yaslı köşe
    ('kolon/şaft yüzünden 5 cm ayrı köşe'), 1 = duvara ve armatüre / ikinci duvara yaslı, 2 = yalnız duvara yaslı, 3 = diğer.
    Islak hacmi olan her katta aynı sınıf aranır (en kötüsü)."""
    en_kotu = 0
    for K in Ks:
        c = (c0[0] + K.off, c0[1])
        r = _oda(K, c)
        if r is None:
            continue
        q = Point(p[0] + K.off, p[1])
        b, s, y = yb[K.k]
        lim = KOLON_R + duvar + tol
        dv = r['poly'].exterior.distance(q) <= lim
        Fd = min(q.distance(b) if not b.is_empty else 999, q.distance(s) if not s.is_empty else 999)
        F_ = Fd <= KOLON_R + F_ACIKLIK + tol
        arm = any(g.distance(q) <= KOLON_R + ARM_ACIKLIK + tol for g in armatur_k.get(K.k, []))
        # ikinci duvar: duvar yüzü iki dik yönde de yakın (oda köşesi)
        yon = 0
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ray = LineString([(q.x, q.y), (q.x + dx * (lim + 1), q.y + dy * (lim + 1))])
            if ray.intersects(r['poly'].exterior):
                yon |= 1 if dx else 2
        if dv and F_:
            k_ = 0
        elif dv and (arm or yon == 3):
            k_ = 1
        elif dv:
            k_ = 2
        else:
            k_ = 3
        en_kotu = max(en_kotu, k_)
    return en_kotu


def hesapla(Ks, kolon_merkez, armatur_k, saft_k=None, baglanti=None, log=print):
    """Ks: [Kat] (Z, 1, 2); kolon_merkez: {no: (x, y)} zemin koordinatı; armatur_k: {kat: [Polygon]} (kat koord.);
    saft_k: {kat: Polygon} (plan.saft_poligonlari). Dönüş: {no: dict(eski, yeni, aci, olcum_eski, olcum_yeni, neden)}"""
    yb = {}
    for K in Ks:
        yb[K.k] = yasak_bolge(K, (saft_k or {}).get(K.k))
    sonuc = {}
    yeni_merkez = dict(kolon_merkez)
    for no, c0 in sorted(kolon_merkez.items(), key=lambda kv: int(kv[0][1:])):
        olc_eski = {}
        bozuk = []
        for K in Ks:
            c = (c0[0] + K.off, c0[1])
            o = olc(c, *yb[K.k])
            olc_eski[K.k] = o
            if ihlal(o):
                bozuk.append(K.k)
        if not bozuk:
            continue
        aday = []
        oda_z = None
        # önce çember duvar yüzünden 2 cm içeride; sığmazsa (dar ıslak hacim / tezgâh ucu: P7, P8) çember duvara /
        # tezgâh çizgisine en çok 7 cm girebilir (kontrolör ıslak hacim poligonu duvardan ~5 cm içeride) (kullanıcının kolonları da duvar içi / tezgâh altı) — betonarme/şafta asla
        for duvar in (DUVAR_ACIKLIK, -7.0):
            V_all = None
            for K in Ks:
                c = (c0[0] + K.off, c0[1])
                diger = [(q[0] + K.off, q[1]) for n, q in yeni_merkez.items() if n != no]
                V, r = gecerli_bolge(K, c, *yb[K.k], armatur_k.get(K.k, []), diger, duvar=duvar)
                if K.k == 'Z':
                    oda_z = r
                V0 = translate(V, -K.off, 0)
                V_all = V0 if V_all is None else V_all.intersection(V0)
            if V_all is not None and not V_all.is_empty:
                for p in _kose_noktalari(V_all):
                    d = math.dist(p, c0)
                    if d <= 60:
                        kd = _kademe(p, Ks, c0, yb, armatur_k, duvar=duvar)
                        pen = 0.0           # gevşek kademede çemberin duvara girişi az olsun
                        if duvar < 0 and oda_z is not None:
                            pen = max(0.0, KOLON_R + DUVAR_ACIKLIK - oda_z['poly'].exterior.distance(Point(p)))
                        # kullanıcının boru bağlantı tarafına yakın olan tercih (hat geldiği yönden bağlanır)
                        bd = math.dist(p, baglanti[no]) if baglanti and no in baglanti else 0.0
                        aday.append((d + 15.0 * kd + 1.0 * pen + 0.3 * bd, kd, d, p))
            if aday:
                break
        if not aday:
            log('  KOLON %s: kural ihlali (%s) ama 60 cm içinde geçerli köşe yok — yerinde bırakıldı' % (no, ','.join(bozuk)))
            sonuc[no] = dict(eski=tuple(c0), yeni=tuple(c0), aci=None, olcum_eski=olc_eski, olcum_yeni=olc_eski,
                             bozuk=bozuk, neden='aday yok')
            continue
        aday.sort()
        _, kademe, d, p = aday[0]
        p = (round(p[0], 1), round(p[1], 1))
        olc_yeni = {K.k: olc((p[0] + K.off, p[1]), *yb[K.k]) for K in Ks}
        aci = duvar_acisi(p, oda_z['poly'] if oda_z else None)
        yeni_merkez[no] = p
        sonuc[no] = dict(eski=tuple(c0), yeni=p, aci=aci, tasima=round(d, 1), olcum_eski=olc_eski, olcum_yeni=olc_yeni,
                         bozuk=bozuk, oda=oda_z['name'] if oda_z else None, kademe=kademe)
        log('  KOLON %s taşındı (%s): (%.1f, %.1f) -> (%.1f, %.1f), %.1f cm; Z eski %s yeni %s' % (
            no, ','.join(bozuk), c0[0], c0[1], p[0], p[1], d, olc_eski['Z'], olc_yeni['Z']))
    return sonuc
