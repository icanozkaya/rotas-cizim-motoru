"""Kontrolör testleri T12–T17 (15.10.2026) — tur 1 kontrolör raporlarının (KONTROL_SIHHI_PLAN_TUR1.md,
KONTROL_SIHHI_SEMA_TUR1.md) "araç bunları ölçmüyor" dediği hatalar:

T12 kolon düşey sürekliliği      T13 ÇM/BM mimarideki yerinde, kolon/aspiratör o yeri işgal etmiyor
T14 aspiratör notu yeri/kılavuzu  T15 penceresiz ıslak hacimde aspiratör
T16 iç metin sızıntısı + siyah ekranda görünmeyen renk (ACI 250–255)
T17 pafta genişlikleri/sırası (ORNEK_DUZEN, SIHHI_ALTIN_REFERANS §1, YERDEN_ISITMA_ALTIN_REFERANS §1)

Kat bilgisi `kontrolor.katlari_esle` çıktısıdır: {kat: (kbt, (dx, dy), eşleşme)}; kbt['kaynak_pencere'] mimari kaynaktaki
kat penceresi, kbt['dxdy'] kaynak -> çizim ötelemesi. "Yerel" koordinat = kaynak penceresinin sol altına göre (katlar arası
karşılaştırma ve referans new_block kayıtları bu koordinatta)."""
import math
import re

from shapely.geometry import Point, box
from shapely.ops import unary_union

import cizim as C
from testler import Bulgu, pencere_yap, mahal_adi

KOLON_EKSEN_TOL = 5.0        # aynı numaralı kolon katlar arasında aynı eksende (cm)
MAKINE_TOL = 40.0            # çizilen ÇM/BM – mimarideki ÇM/BM (cm)
ISGAL_TOL = 15.0             # kolon (r 8) / aspiratör kutusu – ÇM/BM yeri (cm)
NOT_MAHAL_MAX = 60.0         # aspiratör notu kutusu – kendi ıslak hacmi (cm)
KILAVUZ_KESME_MIN = 15.0     # kılavuzun başka mahal içinde (−10 cm) kalan boyu (cm)
DUS_KABINI_MAX = 1.0e4       # bu alandan küçük ıslak "mahal" (duş kabini) T15'e girmez (cm²)
PAFTA_TOL = 0.05             # pafta genişliği referansın ± %5'i

# referans pafta genişlikleri (cm)
PAFTA_REF = {
    'sihhi': {'antet': 958, 'yerlesim': 1682, 'temel': 2471, 'Z': 2065, 'kat': 2039, 'cati': 2058, 'sema': 7418,
              'detay': 2065},
    'yerden': {'antet': 958, 'yerlesim': 1682, 'Z': 2059, 'kat': 2039, 'sema': 6693},
}
PAFTA_SIRA = {
    'sihhi': ['antet', 'yerlesim', 'temel', 'kat', 'cati', 'sema', 'detay'],
    'yerden': ['antet', 'yerlesim', 'kat', 'sema'],
}
PAFTA_GEREKLI = {'sihhi': ['yerlesim', 'temel', 'kat', 'cati', 'sema', 'detay'], 'yerden': ['yerlesim', 'kat', 'sema']}


def kat_sira(k):
    if k.startswith('B'):
        return (0, -int(k[1:] or 1))
    if k == 'Z':
        return (1, 0)
    try:
        return (2, int(k))
    except ValueError:
        return (3, 0)


def kat_adi(k):
    return 'zemin' if k == 'Z' else ('%s. bodrum' % k[1:] if k.startswith('B') else '%s. kat' % k)


def yerel(kbt, p):
    dx, dy = kbt.get('dxdy', (0.0, 0.0))
    w = kbt.get('kaynak_pencere', kbt['pencere'])
    return (p[0] - dx - w[0], p[1] - dy - w[1])


def cizime(kbt, q):
    dx, dy = kbt.get('dxdy', (0.0, 0.0))
    w = kbt.get('kaynak_pencere', kbt['pencere'])
    return (q[0] + dx + w[0], q[1] + dy + w[1])


def yakin_mahal(kb, p, tol=30.0):
    """p'yi içeren en küçük mahal; yoksa ≤ tol cm en yakın mahal (duvar içindeki nokta)"""
    r = mahal_adi(kb, p)
    if r is not None:
        return r
    pt = Point(p)
    yak = [(q['poly'].distance(pt), q['poly'].area, i) for i, q in enumerate(kb['rooms'])]
    yak = [t for t in yak if t[0] <= tol]
    return kb['rooms'][min(yak)[2]] if yak else None


def _no_sira(no):
    m = re.match(r'^([A-Z]+)(\d+)$', no)
    return (m.group(1), int(m.group(2))) if m else (no, 0)


# ------------------------------------------------------------------ referans (kullanıcının new_block çizimi) kayıtları
def referans_cikar(cz, katlar):
    """--referans-kaydet: kolon numara/konumları ve ÇM/BM yerleri (yerel koordinat) -> referans JSON '_cizim' alanı"""
    kol, mak = {}, {}
    for k, (kbt, dxdy, n) in katlar.items():
        w = kbt['pencere']
        kol[k] = {no: [round(v, 1) for v in yerel(kbt, p)] for no, p in cz.kolon_numaralari(w) if no != '?'}
        mak[k] = []
        for tur, c, pg, src in cz.makineler(w):
            b = pg.bounds
            q = yerel(kbt, ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
            mak[k].append([tur, round(q[0], 1), round(q[1], 1), round(b[2] - b[0], 1), round(b[3] - b[1], 1)])
    return {'kolonlar': kol, 'makineler': mak}


# ------------------------------------------------------------------ T12 kolon düşey sürekliliği
def t12_kolon_sureklilik(cz, katlar, ref=None):
    out = []
    ref_k = (ref or {}).get('kolonlar')
    konum = {}
    sira = sorted(katlar, key=kat_sira)
    for k in sira:
        kbt = katlar[k][0]
        for no, p in cz.kolon_numaralari(kbt['pencere']):
            if no == '?':
                out.append(Bulgu('T12', 'FAIL', 'numarasız pis su kolonu (kolon balonu yok)', k, p, pencere=pencere_yap([p])))
                continue
            konum.setdefault(no, {}).setdefault(k, []).append((p, yerel(kbt, p)))
    if not konum:
        return [Bulgu('T12', 'INFO', 'numaralı pis su kolonu bulunamadı; süreklilik ölçülemedi', None)]
    if len(sira) < 2:
        return [Bulgu('T12', 'INFO', 'tek kat; kolon sürekliliği ölçülemedi', None)]
    n_ok = 0
    for no in sorted(konum, key=_no_sira):
        d = konum[no]
        sorun = False
        for k, L in d.items():
            if len(L) > 1:
                sorun = True
                out.append(Bulgu('T12', 'FAIL', 'kolon %s %s katında %d kez' % (no, kat_adi(k), len(L)), k, L[0][0],
                                 noktalar=[q for q, _ in L], pencere=pencere_yap([q for q, _ in L])))
        ylar = [L[0][1] for L in d.values()]
        mx = sorted(q[0] for q in ylar)[len(ylar) // 2]
        my = sorted(q[1] for q in ylar)[len(ylar) // 2]
        # referansta olmayan (yeni) numara
        yeni = ref_k is not None and not any(no in v for v in ref_k.values())
        if yeni:
            sorun = True
            k0 = min(d, key=kat_sira)
            p0 = d[k0][0][0]
            out.append(Bulgu('T12', 'FAIL', 'kolon %s kullanıcının referans çiziminde YOK (yeni kolon numarası; %s) — kolon '
                             'eklemek tasarım değişikliğidir' % (no, ', '.join(kat_adi(k) for k in sorted(d, key=kat_sira))),
                             k0, p0, pencere=pencere_yap([p0])))
        for k in sira:
            if k in d:
                continue
            if ref_k is not None and k in ref_k and no not in ref_k[k] and not yeni:
                out.append(Bulgu('T12', 'INFO', 'kolon %s %s katında yok — referansta da yok' % (no, kat_adi(k)), k))
                continue
            sorun = True
            kbt = katlar[k][0]
            p = cizime(kbt, (mx, my))
            var = ', '.join(kat_adi(q) for q in sorted(d, key=kat_sira))
            out.append(Bulgu('T12', 'FAIL', 'kolon %s %s katında YOK (%s katında var) — kolon düşey sürekli değil; atık bu kattan '
                             'nasıl geçiyor belli değil' % (no, kat_adi(k), var), k, p, pencere=pencere_yap([p])))
        for k, L in d.items():
            q = L[0][1]
            sap = math.hypot(q[0] - mx, q[1] - my)
            if sap > KOLON_EKSEN_TOL:
                sorun = True
                out.append(Bulgu('T12', 'FAIL', 'kolon %s %s katında eksenden %.0f cm kaçık (dx %.0f, dy %.0f; tolerans ± %.0f)' %
                                 (no, kat_adi(k), sap, q[0] - mx, q[1] - my, KOLON_EKSEN_TOL), k, L[0][0],
                                 noktalar=[L[0][0], cizime(katlar[k][0], (mx, my))], pencere=pencere_yap([L[0][0]])))
        if not sorun:
            n_ok += 1
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T12', 'PASS', '%d kolon her katta aynı eksende (± %.0f cm), yeni numara yok' % (n_ok, KOLON_EKSEN_TOL), None))
    return out


# ------------------------------------------------------------------ T13 ÇM/BM mimarideki yerinde
def _makine_refleri(kat, kb, ref):
    refs = list(kb.get('mimari_makine', []))
    if ref and kat in ref.get('makineler', {}):
        for tur, lx, ly, ww, hh in ref['makineler'][kat]:
            c = cizime(kb, (lx, ly))
            refs.append((tur, box(c[0] - ww / 2, c[1] - hh / 2, c[0] + ww / 2, c[1] + hh / 2), 'referans çizim'))
    return refs


def t13_makine_yeri(cz, kat, kb, ref=None):
    w = kb['pencere']
    out = []
    refs = _makine_refleri(kat, kb, ref)
    ad = {'CM': 'Ç.M.', 'BM': 'B.M.'}
    if not refs:
        return [Bulgu('T13', 'INFO', 'mimaride Ç.M./B.M. yeri bulunamadı; ölçülemedi', kat)]
    n_ok = 0
    for tur, c, pg, src in cz.makineler(w):
        r0 = yakin_mahal(kb, c)
        d0 = r0.get('daire') if r0 is not None else None

        def ayni_yer(r):
            d = r[1].distance(Point(c))
            if d <= 150:
                return True
            q = yakin_mahal(kb, (r[1].centroid.x, r[1].centroid.y))
            if q is None or r0 is None:
                return False
            return q is r0 or (d0 is not None and q.get('daire') == d0 and d <= 400)
        # aday: aynı türden, aynı mahal / aynı dairede (≤ 400 cm) ya da ≤ 150 cm (başka dairenin makinesiyle kıyaslanmaz)
        ayni = [r for r in refs if r[0] == tur and ayni_yer(r)]
        if not ayni:
            out.append(Bulgu('T13', 'INFO', '%s (%s) — bu mahalde mimaride %s tanınmadı; konum ölçülemedi' % (ad[tur], src, ad[tur]),
                             kat, c))
            continue
        r = min(ayni, key=lambda r: r[1].distance(Point(c)))
        d = r[1].distance(Point(c))
        if d > MAKINE_TOL:
            q = (r[1].centroid.x, r[1].centroid.y)
            out.append(Bulgu('T13', 'FAIL', '%s mimarideki yerinden TAŞINMIŞ: %s, mimarideki %s\'ye %.0f cm (tolerans %.0f) — '
                             'kural B: ÇM/BM bağlantısı mimaride gösterildiği konumda' % (ad[tur], src, ad[tur], d, MAKINE_TOL),
                             kat, c, noktalar=[c, q], pencere=pencere_yap([c, q])))
        else:
            n_ok += 1
    isgal = [('kolon ' + no, Point(p).buffer(8), p) for no, p in cz.kolon_numaralari(w)]
    isgal += [('aspiratör', bb, p) for p, bb in cz.aspiratorler(w)]
    goruldu = []
    for tur, pg, src in refs:
        for nm, g, p in isgal:
            if g.distance(pg) >= ISGAL_TOL:
                continue
            c = (pg.centroid.x, pg.centroid.y)
            if any(a == nm and b == tur and math.hypot(c[0] - q[0], c[1] - q[1]) < 60 for a, b, q in goruldu):
                continue
            goruldu.append((nm, tur, c))
            out.append(Bulgu('T13', 'FAIL', '%s mimarideki %s yerini işgal ediyor (%s; aralık %.0f cm < %.0f)' %
                             (nm, ad[tur], src, g.distance(pg), ISGAL_TOL), kat, p, noktalar=[p, c], pencere=pencere_yap([p, c])))
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T13', 'PASS', '%d Ç.M./B.M. mimarideki yerinde (± %.0f cm); kolon/aspiratör makine yerinde değil' %
                         (n_ok, MAKINE_TOL), kat))
    return out


# ------------------------------------------------------------------ T14 aspiratör notu kendi ıslak hacminde
def _islak_hacimler(kb):
    return [r for r in kb['rooms'] if r['islak'] and 'mutfak' not in r['name'].lower()]


def _not_sahibi(kb, pg, asp, kil):
    """notun ait olduğu ıslak hacim: kılavuzla bağlı aspiratör sembolü -> en yakın sembol (≤ 400) -> en yakın ıslak hacim"""
    islak = _islak_hacimler(kb)
    if not islak:
        return None, []
    bagli = [g for g in kil if Point(g.coords[0]).distance(pg) < 15 or Point(g.coords[-1]).distance(pg) < 15]
    hedef = None
    for g in bagli:
        a, b = Point(g.coords[0]), Point(g.coords[-1])
        uc = b if a.distance(pg) < b.distance(pg) else a
        yak = [(bb.distance(uc), p) for p, bb in asp if bb.distance(uc) < 40]
        if yak:
            hedef = min(yak)[1]
            break
        if hedef is None:
            hedef = (uc.x, uc.y)
    if hedef is None and asp:
        yak = min(asp, key=lambda pb: pb[1].distance(pg))
        if yak[1].distance(pg) <= 400:
            hedef = yak[0]
    if hedef is not None:
        pt = Point(hedef)
        aday = [r for r in islak if r['poly'].buffer(40).contains(pt)]
        if aday:
            return min(aday, key=lambda r: r['poly'].area), bagli
    return min(islak, key=lambda r: r['poly'].distance(pg)), bagli


def t14_aspirator_notu(cz, kat, kb):
    w = kb['pencere']
    out = []
    notlar = cz.aspirator_notlari(w)
    if not notlar:
        return [Bulgu('T14', 'INFO', 'aspiratör notu yok', kat)]
    asp = cz.aspiratorler(w)
    kil = cz.kilavuzlar(w)
    n_ok = 0
    for s, pg, e in notlar:
        c = (pg.centroid.x, pg.centroid.y)
        sahip, bagli = _not_sahibi(kb, pg, asp, kil)
        if sahip is None:
            out.append(Bulgu('T14', 'INFO', 'aspiratör notu: katta ıslak hacim tanınmadı', kat, c))
            continue
        d = pg.distance(sahip['poly'])
        r_in = mahal_adi(kb, c)
        sorun = []
        if d > NOT_MAHAL_MAX:
            sorun.append('kendi ıslak hacmine (%s%s) %.0f cm uzakta (en çok %.0f)' % (
                sahip['name'], (' D%s' % sahip['daire']) if sahip.get('daire') else '', d, NOT_MAHAL_MAX))
        if r_in is not None and r_in['ortak']:
            sorun.append('ortak alanda (%s) — daire dışında' % r_in['name'].replace('\n', ' '))
        elif r_in is not None and r_in.get('daire') and sahip.get('daire') and r_in['daire'] != sahip['daire']:
            sorun.append('başka dairede (%s D%s)' % (r_in['name'], r_in['daire']))
        izin = [sahip['poly'].buffer(15)]
        if r_in is not None and d <= NOT_MAHAL_MAX:
            izin.append(r_in['poly'].buffer(15))
        izin = unary_union(izin)
        for g in bagli:
            for r in kb['rooms']:
                if r is sahip or r is r_in:
                    continue
                ic = r['poly'].buffer(-10)
                if ic.is_empty:
                    continue
                L = g.difference(izin).intersection(ic).length
                if L > KILAVUZ_KESME_MIN:
                    sorun.append('kılavuz çizgisi %s içinden %.0f cm geçiyor (kılavuz %.0f cm)' % (
                        r['name'].replace('\n', ' '), L, g.length))
        if sorun:
            out.append(Bulgu('T14', 'FAIL', 'aspiratör notu "%s": %s — kural: not kendi ıslak hacminin içinde/yanında, kılavuz '
                             'başka mahali kesmez' % (s[:24], '; '.join(sorun)), kat, c,
                             noktalar=[c, (sahip['poly'].centroid.x, sahip['poly'].centroid.y)],
                             pencere=pencere_yap([c, (sahip['poly'].centroid.x, sahip['poly'].centroid.y)])))
        else:
            n_ok += 1
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T14', 'PASS', '%d aspiratör notu kendi ıslak hacminde (≤ %.0f cm), kılavuz başka mahali kesmiyor' %
                         (n_ok, NOT_MAHAL_MAX), kat))
    return out


# ------------------------------------------------------------------ T15 penceresiz ıslak hacimde aspiratör
def pencereli_mi(kb, r):
    """mimari pencere etiketi (S01 / P01 ...) en yakın mahali bu mahal ve ≤ 30 cm ise pencereli"""
    for c, s in kb.get('pencereler', []):
        pt = Point(c)
        d = r['poly'].distance(pt)
        if d > 30:
            continue
        en = min(kb['rooms'], key=lambda q: (q['poly'].distance(pt), q['poly'].area))
        if en is r:
            return s
    return None


def t15_penceresiz_aspirator(cz, kat, kb):
    w = kb['pencere']
    out = []
    asp = cz.aspiratorler(w)
    notlar = []
    for s, pg, e in cz.aspirator_notlari(w):
        r_in = mahal_adi(kb, (pg.centroid.x, pg.centroid.y))
        if r_in is not None and r_in['ortak']:
            continue                                  # ortak alandaki not hiçbir daireyi karşılamaz
        notlar.append(pg)
    n_ok = n_pen = 0
    for r in _islak_hacimler(kb):
        ad = '%s%s' % (r['name'], (' D%s' % r['daire']) if r.get('daire') else '')
        if r['poly'].area < DUS_KABINI_MAX:
            out.append(Bulgu('T15', 'INFO', '%s %.2f m² (duş kabini; ayrı havalandırma aranmadı)' % (ad, r['poly'].area / 1e4), kat))
            continue
        pen = pencereli_mi(kb, r)
        if pen:
            n_pen += 1
            continue
        var = any(r['poly'].buffer(40).contains(Point(p)) for p, bb in asp) or \
            any(pg.distance(r['poly']) <= NOT_MAHAL_MAX for pg in notlar)
        if var:
            n_ok += 1
            continue
        c = (r['poly'].centroid.x, r['poly'].centroid.y)
        b = r['poly'].bounds
        out.append(Bulgu('T15', 'FAIL', 'penceresiz %s: aspiratör / mekanik havalandırma notu yok — kural B: WC/banyo mekanik '
                         'havalandırması kat planlarında da gösterilir' % ad, kat, c,
                         pencere=pencere_yap([(b[0], b[1]), (b[2], b[3])], pad=80)))
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T15', 'PASS', '%d penceresiz ıslak hacimde aspiratör var (%d pencereli)' % (n_ok, n_pen), kat))
    return out


# ------------------------------------------------------------------ T16 iç metin sızıntısı + görünmeyen renk
SIZINTI = [
    (r'\(EK\)', '"(EK)" işareti'),
    (r'NEW[_ ]?BLOCK', 'kaynak dosya adı (new_block)'),
    (r'OTOMATIK', '"otomatik"'),
    (r'\.(DXF|DWG|PY|JSON|MD|XLSX)\b', 'dosya adı'),
    (r'\bKURAL', 'kural cümlesi ("kural")'),
    (r'GEREGI\b', 'kural cümlesi ("gereği")'),
    (r'CIZILMEZ|GOSTERILMEZ|EKLENMISTIR|KONULMAZ', 'kural cümlesi'),
    (r'\bYALNIZ\b.*\b(BANDINDA|GIRISINDE|ZEMIN)', 'kural cümlesi ("yalnız ... zemin/bant")'),
    (r'SOGUGA \d+ ?CM|\(KOMBIDEN', 'kural cümlesi (hat kuralı)'),
    (r'KAPI YANINDA|MERDIVEN HOLUNDE', 'kural cümlesi (konum kuralı)'),
    (r'\bTODO\b|\bTASLAK\b|\bDENEME\b|\bMOTOR\b|KONTROLOR', 'iç çalışma notu'),
]
_SIZ = [(re.compile(a), b) for a, b in SIZINTI]


def _renk_coz(e, katman, ust=None):
    """ACI rengi: 256 BYLAYER -> katman (blok içinde '0' katmanı -> ekleyen INSERT); 0 BYBLOCK -> ekleyen INSERT"""
    col = e.dxf.get('color', 256)
    if col == 256:
        lay = e.dxf.get('layer', '0')
        if lay == '0' and ust is not None:
            return _renk_coz(ust, katman)
        return abs(katman.get(lay, 7))
    if col == 0:
        return _renk_coz(ust, katman) if ust is not None else 7
    return col


def _koyu_true(e):
    try:
        if e.dxf.hasattr('true_color'):
            v = e.dxf.true_color
            r, g, b = (v >> 16) & 255, (v >> 8) & 255, v & 255
            return max(r, g, b) < 60
    except Exception:
        pass
    return False


def t16_sizinti_renk(cz):
    out = []
    doc = cz.doc
    katman = {l.dxf.name: l.color for l in doc.layers}
    # 1) metin sızıntısı: model alanı TEXT/MTEXT, görünür ATTRIB, blok içi TEXT/MTEXT
    goruldu = set()
    n_siz = 0

    def bak(s, p, lay, kaynak):
        nonlocal n_siz
        n = C.normu(s)
        for rx, ne in _SIZ:
            if rx.search(n):
                k = (n[:60], round(p[0] / 50), round(p[1] / 50))
                if k in goruldu:
                    return
                goruldu.add(k)
                n_siz += 1
                if n_siz <= 60:
                    out.append(Bulgu('T16', 'FAIL', 'iç metin sızıntısı (%s): "%s" [%s%s]' % (ne, C.norm(s)[:70], lay, kaynak),
                                     None, p, pencere=pencere_yap([p], pad=150)))
                return

    for e in cz.msp:
        t = e.dxftype()
        if t in ('TEXT', 'MTEXT'):
            s = e.dxf.text if t == 'TEXT' else e.plain_text()
            bak(s or '', (e.dxf.insert.x, e.dxf.insert.y), e.dxf.layer, '')
        elif t == 'INSERT':
            for a in e.attribs:
                if not a.is_invisible and (a.dxf.text or '').strip():
                    bak(a.dxf.text, (a.dxf.insert.x, a.dxf.insert.y), e.dxf.layer, ', blok %s' % e.dxf.name)
    # blok içi yazılar (blok başına bir kez; konum ilk INSERT)
    ilk = {}
    for ad, p, e in cz.insertler:
        ilk.setdefault(ad, (p, e))
    for ad, (p, e) in ilk.items():
        try:
            blk = doc.blocks.get(ad)
        except Exception:
            continue
        if blk is None:
            continue
        for v in blk:
            if v.dxftype() in ('TEXT', 'MTEXT'):
                s = v.dxf.text if v.dxftype() == 'TEXT' else v.plain_text()
                bak(s or '', p, e.dxf.layer, ', blok içi %s' % C.efektif_ad(doc, e))
    # 2) görünmeyen renk (ACI 250–255 ya da çok koyu gerçek renk), mimari katmanlar hariç
    say = {}
    for e in cz.msp:
        t = e.dxftype()
        lay = e.dxf.get('layer', '0')
        if C.mimari_yazi_katmani(lay):
            continue
        if t == 'INSERT':
            p = (e.dxf.insert.x, e.dxf.insert.y)
            parcalar = []
            try:
                parcalar = [(v, e) for v in e.virtual_entities()]
            except Exception:
                pass
            parcalar += [(a, e) for a in e.attribs if not a.is_invisible]
            for v, ust in parcalar:
                if v.dxftype() in ('ATTDEF', 'WIPEOUT'):
                    continue
                r = _renk_coz(v, katman, ust)
                if 250 <= r <= 255 or _koyu_true(v):
                    k = (lay, v.dxftype(), C.efektif_ad(doc, e))
                    say.setdefault(k, [0, p, r])[0] += 1
            continue
        if t == 'WIPEOUT':
            continue                     # maske: zemin rengiyle dolar, rengi görünmez değildir
        try:
            r = _renk_coz(e, katman)
        except Exception:
            continue
        if 250 <= r <= 255 or _koyu_true(e):
            try:
                p = (e.dxf.insert.x, e.dxf.insert.y) if e.dxf.hasattr('insert') else None
            except Exception:
                p = None
            if p is None:
                g = C.D.geometri(e) if t in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC') else None
                p = (g.centroid.x, g.centroid.y) if g is not None else None
            k = (lay, t, '')
            say.setdefault(k, [0, p, r])[0] += 1
    for (lay, t, blk), (n, p, r) in sorted(say.items(), key=lambda kv: -kv[1][0]):
        out.append(Bulgu('T16', 'FAIL', '%d %s%s katman %s renk %s: AutoCAD siyah ekranında görünmez (ACI 250–255) — renk 7/BYLAYER '
                         'ya da kullanıcı rengi' % (n, t, (' (blok %s)' % blk) if blk else '', lay, r), None, p,
                         pencere=pencere_yap([p], pad=200) if p else None))
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T16', 'PASS', 'iç metin sızıntısı yok, ACI 250–255 / koyu renk yok', None))
    return out


# ------------------------------------------------------------------ T17 pafta genişlikleri ve sırası
def pafta_turu(cz, w):
    ts = []
    for s, p, h, lay, e in cz.yazilar_pencere(w):
        if h >= 14 and e.dxftype() in ('TEXT', 'MTEXT'):
            ts.append(C.normu(s))
    adlar = [C.normu(ad) for ad, p, e in cz.insertler_ef_pencere(w)]
    if any('YERLESIM PLANI' in t for t in ts):
        return 'yerlesim'
    if any('TEMEL PLANI' in t for t in ts):
        return 'temel'
    if any('CATI PLANI' in t for t in ts):
        return 'cati'
    for t in ts:
        m = C.Cizim.KAT_RE.match(t)
        if m and 'PLAN' in t and 'SEMA' not in t:
            k = m.group(1)
            return 'Z' if k.startswith('ZEMIN') else ('B' if 'BODRUM' in k else 'kat:' + re.sub(r'\D', '', k))
    nkat = sum(1 for t in ts if C.Cizim.KAT_RE.match(t) and 'PLAN' not in t)
    if any('KOLON SEMASI' in t or 'ACILIMLI' in t for t in ts) or (nkat >= 2 and (w[2] - w[0]) > 4000):
        return 'sema'
    # detay paftası (WC havalandırma izometrisi + SIHHİ DETAYLAR): izometrideki kat yazıları şema sanılmasın
    if any('DETAY' in t or 'HAVALANDIRMA' in t or 'ASPIRATOR' in t for t in ts) or any('DETAY' in a for a in adlar):
        return 'detay'
    if nkat >= 2:
        return 'sema'
    if (w[2] - w[0]) < 1300 and any('PROJESI' in t or 'ROTAS' in t for t in ts):
        return 'antet'
    return 'bilinmeyen'


def seritler(cz):
    """paftaları bitişik şeritlere ayırır; şerit türü: ısıtma (PEX/ISITMA katmanı) / sıhhi"""
    ps = cz.paftalar()
    out = []
    for p in ps:
        if out and abs(p[0] - out[-1][-1][2]) < 100 and abs(p[1] - out[-1][-1][1]) < 300:
            out[-1].append(p)
        else:
            out.append([p])
    sonuc = []
    for s in out:
        b = (s[0][0], min(p[1] for p in s), s[-1][2], max(p[3] for p in s))
        n_is = 0
        for e in cz.msp:
            lay = C.normu(e.dxf.get('layer', '0'))
            if ('PEX' in lay or 'ISITMA' in lay) and e.dxftype() in ('LWPOLYLINE', 'LINE', 'INSERT'):
                try:
                    q = e.dxf.insert if e.dxftype() == 'INSERT' else (e.dxf.start if e.dxftype() == 'LINE' else
                                                                      list(e.get_points('xy'))[0])
                except Exception:
                    continue
                if b[0] <= q[0] <= b[2] and b[1] <= q[1] <= b[3]:
                    n_is += 1
                    if n_is > 10:
                        break
        sonuc.append(('yerden' if n_is > 10 else 'sihhi', s))
    return sonuc


def t17_pafta(cz, tur='sihhi'):
    out = []
    ser = [(t, s) for t, s in seritler(cz) if t == tur]
    if not ser:
        return [Bulgu('T17', 'INFO', 'pafta çerçevesi / ayracı bulunamadı (%s şeridi yok); pafta ölçüsü ölçülemedi' % tur, 'PAFTA')]
    ref = PAFTA_REF[tur]
    sira = PAFTA_SIRA[tur]
    n_ok = 0
    for st, paftalar in ser:
        turler = []
        for w in paftalar:
            pt = pafta_turu(cz, w)
            turler.append(pt)
            g = w[2] - w[0]
            anahtar = 'kat' if pt.startswith('kat:') or pt == 'B' else pt
            r = ref.get(anahtar)
            if pt == 'bilinmeyen':
                d = 'FAIL' if len(paftalar) >= 5 else 'INFO'
                out.append(Bulgu('T17', d, 'pafta x %.0f…%.0f (%.0f cm): referans düzende karşılığı yok (başlıksız / referansta '
                                 'olmayan sayfa) — ORNEK_DUZEN' % (w[0], w[2], g), 'PAFTA', ((w[0] + w[2]) / 2, (w[1] + w[3]) / 2),
                                 pencere=w))
                continue
            if r is None:
                continue
            if abs(g - r) > PAFTA_TOL * r:
                out.append(Bulgu('T17', 'FAIL', '%s paftası %.0f cm, referans %d cm (± %%%.0f; fark %+.0f cm) — ORNEK_DUZEN / '
                                 'ALTIN_REFERANS §1' % (pt, g, r, 100 * PAFTA_TOL, g - r), 'PAFTA',
                                 ((w[0] + w[2]) / 2, (w[1] + w[3]) / 2), pencere=w))
            else:
                n_ok += 1
        if len(paftalar) >= 5:          # tam şerit: eksik / sıra
            kisa = ['kat' if t.startswith('kat:') or t in ('Z', 'B') else t for t in turler]
            for g in PAFTA_GEREKLI[tur]:
                if g not in kisa:
                    out.append(Bulgu('T17', 'FAIL', '%s paftası YOK (şerit x %.0f…%.0f) — ORNEK_DUZEN sırası: %s' %
                                     (g.upper(), paftalar[0][0], paftalar[-1][2], ' → '.join(sira)), 'PAFTA',
                                     (paftalar[0][0], paftalar[0][1])))
            rk = [sira.index(t) for t in kisa if t in sira]
            if rk != sorted(rk):
                out.append(Bulgu('T17', 'FAIL', 'pafta sırası referanstan farklı: %s (istenen: %s)' %
                                 (' → '.join(turler), ' → '.join(sira)), 'PAFTA', (paftalar[0][0], paftalar[0][1])))
            # kat sırası: zemin -> 1 -> 2 ...
            ks = [t for t in turler if t == 'Z' or t.startswith('kat:') or t == 'B']
            kn = [(-1 if t == 'B' else (0 if t == 'Z' else int(t[4:] or 0))) for t in ks]
            if kn != sorted(kn):
                out.append(Bulgu('T17', 'FAIL', 'kat paftaları sırası: %s' % ' → '.join(ks), 'PAFTA', (paftalar[0][0], paftalar[0][1])))
        out.append(Bulgu('T17', 'INFO', 'şerit (%s): %s' % (st, ', '.join('%s %.0f' % (t, w[2] - w[0]) for t, w in zip(turler, paftalar))),
                         'PAFTA'))
    if not any(b.durum == 'FAIL' for b in out):
        out.append(Bulgu('T17', 'PASS', '%d pafta genişliği referansla ± %%%.0f, sıra doğru' % (n_ok, 100 * PAFTA_TOL), 'PAFTA'))
    return out


TEST_ADI2 = {
    'T12': 'Kolon düşey sürekliliği: aynı numara her katta aynı eksende (± %.0f cm); referansta olmayan yeni numara yok' % KOLON_EKSEN_TOL,
    'T13': 'Ç.M./B.M. mimarideki yerinde (± %.0f cm); kolon/aspiratör o yeri işgal etmiyor' % MAKINE_TOL,
    'T14': 'Aspiratör notu kendi ıslak hacminde (≤ %.0f cm), ortak alanda değil; kılavuz başka mahali kesmiyor' % NOT_MAHAL_MAX,
    'T15': 'Penceresiz her ıslak hacimde aspiratör / mekanik havalandırma notu',
    'T16': 'Paftada iç kural metni sızıntısı ("(EK)", "new_block", "otomatik", kural cümleleri) yok; ACI 250–255 renk yok',
    'T17': 'Pafta genişlikleri ve sırası ORNEK_DUZEN / ALTIN_REFERANS §1 ile (± %%%.0f)' % (100 * PAFTA_TOL),
}
