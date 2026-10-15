"""Kontrolör — YERDEN ISITMA test takımı (`kontrolor.py --tur yerden`), 15.10.2026.

Tur 1 kontrolör raporu (KONTROL_YERDEN_TUR1.md) `denetle.py`nin yakalamadığı hataları listeledi: düşük boru yoğunluğu
(etiket cebi), yarım ısıtılmış ıslak hacim / 1,66 m'lik devre, mahal dışına konmuş devre etiketleri, uzun kılavuzlar,
plan W ↔ Excel W tutarsızlığı. Ölçütler `YERDEN_ISITMA_ALTIN_REFERANS.md` §3–4, §7 ve kullanıcının new_block ısıtma
şeridiyle kalibre edildi (BENIOKU.md "Yerden ısıtma").

Y01 boru yoğunluğu (m/m², mimari m² yazısı) — oda/salon/yatak/hol ≥ 6,0; ısıtılmayan mahalde boru yok
Y02 ıslak hacim doluluğu (banyo ≥ 3,0 m/m²), < 3 m devre yok, ≤ 2,65 m² wc-duş/duş için ayrı devre yok
Y03 devre etiketi kendi mahalinde (etiketteki hat uzunluğu ile devre eşlenir)
Y04 kılavuz çizgisi: ≤ 100 cm ve başka mahali kesmez (referans: kılavuz yok)
Y05 etiketteki hat uzunluğu = altındaki devrenin uzunluğu (ET-2)
Y06 plan W ↔ şema W ↔ Excel W (aynı kaynak)"""
import math
import re

from ezdxf import path as ep
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

import cizim as C
from testler import Bulgu, pencere_yap, mahal_adi

YOGUNLUK_MIN = 6.0           # m/m² (oda, salon, yatak odası, hol) — hedef (tur 1 kabul ölçütü 1); altı BİLGİ
YOGUNLUK_FAIL = 5.3          # m/m² — bunun altı FAIL (kullanıcının new_block ısıtma planında en düşük 5,38: D3 hol)
CEP_MAX = 0.6                # m² — mahal içinde borusuz boşluk (etiket cebi); kullanıcı çiziminde 0, tur 1'de 1,0–1,6
ISLAK_YOGUNLUK_MIN = 3.0     # m/m² banyo / wc+banyo (referans 3,2–4,4; tur 1'de 1,6–2,1)
KISA_DEVRE_MIN = 3.0         # m — bundan kısa devre olmaz (tur 1: 1,66 m)
KUCUK_ISLAK_MAX = 2.65       # m² — bu ve altı wc-duş / duş için ayrı devre açılmaz
KILAVUZ_MAX = 100.0          # cm — kılavuz çizgisi (referansta hiç yok)
ISITILMAYAN_BORU_MAX = 100.0  # cm — ısıtılmayan mahalin iç bölgesinde (−10 cm) boru
W_TOL = 0.01                 # plan W ↔ Excel/şema W bağıl tolerans

ISITILAN_YOGUN = ('salon', 'yatak', 'oda', 'antre', 'hol', 'kor')
ISITILMAYAN = ('balkon', 'yüklük', 'yukluk', 'merdiven', 'asans', 'en. oda', 'teras', 'sahanl', 'giriş', 'giris')

TEST_ADI = {
    'Y01': 'Boru yoğunluğu oda/salon/yatak/hol: hedef ≥ %.1f m/m² (mimari m²; < %.1f FAIL), borusuz cep ≤ %.1f m²; ısıtılmayan '
           'mahalde boru yok' % (YOGUNLUK_MIN, YOGUNLUK_FAIL, CEP_MAX),
    'Y02': 'Islak hacim doluluğu (banyo ≥ %.1f m/m²); < %.0f m devre yok; ≤ %.2f m² wc-duş/duş için ayrı devre yok' % (
        ISLAK_YOGUNLUK_MIN, KISA_DEVRE_MIN, KUCUK_ISLAK_MAX),
    'Y03': 'Devre etiketi kendi mahalinin içinde (ortak alan / bina dışı / başka mahal değil)',
    'Y05': 'Devre etiketindeki hat uzunluğu = etiketin bindiği devrenin polyline uzunluğu (± 0,6 m; ET-2)',
    'Y04': 'Kılavuz çizgisi ≤ %.0f cm ve başka mahali kesmiyor (referansta kılavuz yok)' % KILAVUZ_MAX,
    'Y06': 'Plan W ↔ kolon şeması W ↔ Excel W aynı kaynaktan (± %%%.0f)' % (100 * W_TOL),
    'T11': 'denetle.py: MTY 0, ROTAS- öneki, köprü 0, kesişme 0, elektrik 0, yazı çakışması 0, lejant, audit',
    'T16': 'Paftada iç kural metni sızıntısı yok; ACI 250–255 renk yok',
    'T17': 'Pafta genişlikleri ve sırası (ısıtma şeridi) YERDEN_ISITMA_ALTIN_REFERANS §1 ile (± %5)',
}


def _pex_mi(lay):
    n = C.normu(lay)
    return 'PEX' in n or ('SERPANTIN' in n)


def devreler(cz, w):
    """PEX devreleri: [(LineString, uzunluk m, varlık)] — yaylar (bulge) dahil gerçek uzunluk"""
    out = []
    for e in cz.msp.query('LWPOLYLINE POLYLINE'):
        if not _pex_mi(e.dxf.layer):
            continue
        try:
            pts = [(v.x, v.y) for v in ep.make_path(e).flattening(0.5)]
        except Exception:
            continue
        if len(pts) < 2:
            continue
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        cx, cy = (min(x) + max(x)) / 2, (min(y) + max(y)) / 2
        if not (w[0] <= cx <= w[2] and w[1] <= cy <= w[3]):
            continue
        g = LineString(pts)
        out.append((g, g.length / 100.0, e))
    return out


def _etiket_ozn(e):
    d = {}
    for a in e.attribs:
        tag = (a.dxf.tag or '').upper()
        kok = re.sub(r'_\d+$', '', tag)
        d[kok] = (a.dxf.text or '').strip()
        d.setdefault('_ozn', []).append((kok, a))
    return d


def _sayi(s):
    m = re.search(r'(-?\d+(?:[.,]\d+)?)', s or '')
    return float(m.group(1).replace(',', '.')) if m else None


def devre_etiketleri(cz, w):
    """devre etiketleri (MTY-ETIKET / ROTAS-YI-ETIKET: UZ, AR, YER, NO1 öznitelikleri) ->
    [dict(uz m, W, no, zon, kutu, varlık)] — kutu: görünen öznitelik yazılarının birleşimi"""
    out = []
    from kutu import yazi_kutusu
    for ad, p, e in cz.insertler_ef_pencere(w):
        d = _etiket_ozn(e)
        if 'UZ' not in d or 'YER' not in d:
            continue
        kutular = [yazi_kutusu(a) for k, a in d['_ozn'] if k in ('UZ', 'AR', 'YER', 'NO1')]
        kutular = [k for k in kutular if k is not None]
        kutu = unary_union(kutular).envelope if kutular else Point(p).buffer(30)
        out.append(dict(uz=_sayi(d.get('UZ')), W=_sayi(d.get('YER')), no=d.get('NO1'), zon=d.get('NO', ''),
                        kutu=kutu, e=e, p=p))
    return out


def _alan_m2(kb, r):
    """mahal alanı (m²): mahal içindeki mimari 'xx.xx m²' yazısı (mahal adına en yakın); yoksa poligon alanı"""
    en, ed = None, 1e9
    pg = r['poly'].buffer(5)
    for (x, y), s, h, rot in kb.get('mimari_yazi', []):
        m = re.match(r'^\s*(\d+[.,]\d+)\s*m(²|2)\s*$', s or '')
        if not m or not pg.contains(Point(x, y)):
            continue
        d = math.hypot(x - r['xy'][0], y - r['xy'][1])
        if d < ed:
            en, ed = float(m.group(1).replace(',', '.')), d
    return (en, 'mimari') if en and ed < 150 else (r['poly'].area / 1e4, 'poligon')


def _mahal_turu(ad):
    a = (ad or '').lower()
    if any(k in a for k in ISITILMAYAN):
        return 'isitilmayan'
    if 'wc-lvb' in a or 'lvb' in a:
        return 'isitilmayan'
    if any(k in a for k in ('banyo', 'duş', 'dus', 'wc')):
        return 'islak'
    if 'mutfak' in a:
        return 'mutfak'
    if any(k in a for k in ISITILAN_YOGUN):
        return 'yogun'
    return 'diger'


def _cep(r, boru):
    """mahal içinde (duvardan 20 cm içeri) borunun 12 cm çevresi dışında kalan, 15 cm açmayla süzülmüş en büyük boşluk
    -> (m², merkez) ya da None"""
    ic = r['poly'].buffer(-20)
    if ic.is_empty:
        return None
    bos = ic.difference(boru.buffer(12)).buffer(-15).buffer(15)
    if bos.is_empty:
        return (0.0, None)
    parca = list(getattr(bos, 'geoms', [bos]))
    en = max(parca, key=lambda g: g.area)
    return (en.area / 1e4, (en.representative_point().x, en.representative_point().y))


def _devre_mahali(kb, g):
    """devrenin mahali. 15.10 (D): devre polyline'ı kollektörden başlayıp kapıdan geçen ayaklarla birlikte çizilir;
    ayaklar iki uçta simetrik olduğundan polyline'ın orta noktası serpantinin içindedir -> önce o noktayı içeren mahal,
    yoksa (eski davranış) en çok boru uzunluğunu içeren mahal."""
    m = g.interpolate(0.5, normalized=True)
    for r in kb['rooms']:
        if r['poly'].buffer(5).contains(m):
            return r
    en, eL = None, 0.0
    for r in kb['rooms']:
        L = g.intersection(r['poly'].buffer(10)).length
        if L > eL:
            en, eL = r, L
    return en


def kat_testleri(cz, kat, kb):
    w = kb['pencere']
    out = []
    dv = devreler(cz, w)
    if not dv:
        return [Bulgu('Y01', 'INFO', 'katta PEX devresi yok', kat)]
    # ---- Y01 / Y02 yoğunluk
    boru = unary_union([g for g, L, e in dv])
    n1 = n2 = 0
    for r in kb['rooms']:
        tur = _mahal_turu(r['name'])
        ad = '%s%s' % (r['name'].replace('\n', ' '), (' D%s' % r['daire']) if r.get('daire') else '')
        Lr = boru.intersection(r['poly'].buffer(5)).length / 100.0
        c = (r['poly'].centroid.x, r['poly'].centroid.y)
        b = r['poly'].bounds
        pen = pencere_yap([(b[0], b[1]), (b[2], b[3])], pad=60)
        if tur == 'isitilmayan':
            ic = r['poly'].buffer(-10)
            Lr = boru.intersection(ic).length / 100.0 if not ic.is_empty else 0.0
            if Lr * 100 > ISITILMAYAN_BORU_MAX:
                out.append(Bulgu('Y01', 'FAIL', '%s ısıtılmayan mahal, içinde %.1f m boru (PEX-9)' % (ad, Lr), kat, c, pencere=pen))
            continue
        A, kaynak = _alan_m2(kb, r)
        if not A or A <= 0:
            continue
        yog = Lr / A
        if tur == 'yogun':
            cep = _cep(r, boru) if r['poly'].area / 1e4 <= 1.25 * A else None    # poligon m²'den çok büyükse güvenilmez
            sorun = []
            if yog < YOGUNLUK_FAIL:
                sorun.append('boru yoğunluğu %.2f m/m² < %.1f (%.1f m / %.2f m² %s)' % (yog, YOGUNLUK_FAIL, Lr, A, kaynak))
            if cep is not None and cep[0] > CEP_MAX:
                sorun.append('borusuz cep %.2f m² > %.1f (etiket cebi / doldurulmamış köşe)' % (cep[0], CEP_MAX))
            if sorun:
                pts = [c] + ([cep[1]] if cep and cep[0] > CEP_MAX else [])
                out.append(Bulgu('Y01', 'FAIL', '%s: %s — serpantin mahali tam doldurmalı, etiket serpantin üstüne biner' % (
                    ad, '; '.join(sorun)), kat, pts[-1], noktalar=pts, pencere=pen))
            elif yog < YOGUNLUK_MIN:
                out.append(Bulgu('Y01', 'INFO', '%s: %.2f m/m² (hedef %.1f; cep yok) — referans new_block\'ta da 5,4–6,0 olan mahaller var' %
                                 (ad, yog, YOGUNLUK_MIN), kat, c))
                n1 += 1
            else:
                n1 += 1
        elif tur == 'mutfak':
            out.append(Bulgu('Y01', 'INFO', '%s: %.2f m/m² (mutfak: tezgâh/buzdolabı altı boş; ölçüt dışı)' % (ad, yog), kat, c))
        elif tur == 'islak':
            kendi = [(g, L) for g, L, e in dv if _devre_mahali(kb, g) is r]
            if A <= KUCUK_ISLAK_MAX and kendi and any(k in r['name'].lower() for k in ('duş', 'dus')):
                out.append(Bulgu('Y02', 'FAIL', '%s %.2f m² ≤ %.2f: ayrı devre açılmış (%s m) — wc-duş/duş ya ısıtılmaz ya banyoyla '
                                 'tek devre' % (ad, A, KUCUK_ISLAK_MAX, ', '.join('%.2f' % L for g, L in kendi)), kat, c, pencere=pen))
            elif A > KUCUK_ISLAK_MAX and yog < ISLAK_YOGUNLUK_MIN:
                out.append(Bulgu('Y02', 'FAIL', '%s: doluluk %.2f m/m² < %.1f (%.1f m / %.2f m²) — ıslak hacim yarım ısıtılmış '
                                 '(referans banyo 23,5 m / 5,36 m²)' % (ad, yog, ISLAK_YOGUNLUK_MIN, Lr, A), kat, c, pencere=pen))
            else:
                n2 += 1
    for g, L, e in dv:
        if L < KISA_DEVRE_MIN:
            p = g.interpolate(0.5, normalized=True)
            r = _devre_mahali(kb, g)
            out.append(Bulgu('Y02', 'FAIL', 'devre %.2f m < %.0f m (%s) — anlamsız kısa devre' % (
                L, KISA_DEVRE_MIN, r['name'] if r else '?'), kat, (p.x, p.y), pencere=pencere_yap([(p.x, p.y)])))
    if not any(b.durum == 'FAIL' and b.test == 'Y01' for b in out):
        out.append(Bulgu('Y01', 'PASS', '%d oda/salon/hol ≥ %.1f m/m²; ısıtılmayan mahalde boru yok' % (n1, YOGUNLUK_MIN), kat))
    if not any(b.durum == 'FAIL' and b.test == 'Y02' for b in out):
        out.append(Bulgu('Y02', 'PASS', '%d ıslak hacim dolu (≥ %.1f m/m²), kısa devre yok' % (n2, ISLAK_YOGUNLUK_MIN), kat))
    # ---- Y03 devre etiketi kendi mahalinde
    ets = devre_etiketleri(cz, w)
    n3 = 0
    for et in ets:
        c = et['kutu'].centroid
        # etiketin devresi: etiketin üstüne bindiği devre (≤ 30 cm; referans: etiket serpantin üstünde) — yoksa etiketteki
        # hat uzunluğuna eşit devre (± 0,6 m), yoksa en yakın devre
        yak = [t for t in dv if t[0].distance(c) <= 30]
        if yak:
            g, L, e = min(yak, key=lambda t: (abs(t[1] - et['uz']) if et['uz'] else 0, t[0].distance(c)))
        else:
            es = [t for t in dv if et['uz'] and abs(t[1] - et['uz']) <= 0.6] or dv
            g, L, e = min(es, key=lambda t: t[0].distance(c))
        r = _devre_mahali(kb, g)
        if r is None:
            continue
        if et['uz'] and abs(L - et['uz']) > 0.6 and yak:
            out.append(Bulgu('Y05', 'FAIL', 'devre etiketi (%s) hat uzunluğu %.2f m ≠ altındaki devre %.2f m — etiket başka devreden '
                             'kopyalanmış (ET-2: hat uzunluğu = polyline uzunluğu)' % (et['zon'] or '?', et['uz'], L), kat, (c.x, c.y),
                             pencere=pencere_yap([(c.x, c.y)])))
        r2 = mahal_adi(kb, (c.x, c.y))
        if r['poly'].buffer(10).contains(c) or (r2 is None and r['poly'].distance(c) <= 50 and kb['bina'].buffer(30).contains(c)):
            n3 += 1                      # mahal içinde ya da mahalin poligona girmeyen nişinde (duvar/niş, ≤ 50 cm)
            continue
        yer = r2['name'].replace('\n', ' ') if r2 else ('bina dışı' if not kb['bina'].contains(c) else 'duvar/ortak')
        if r2 is not None and r2['ortak']:
            yer += ' (ortak alan)'
        q = g.interpolate(0.5, normalized=True)
        out.append(Bulgu('Y03', 'FAIL', 'devre etiketi (%s, %s m) kendi mahalinin (%s) DIŞINDA: %s — etiket mahal içinde, uç köşesine '
                         'yakın (ET-3)' % (et['zon'] or '?', ('%.2f' % et['uz']) if et['uz'] else '?', r['name'].replace('\n', ' '), yer),
                         kat, (c.x, c.y), noktalar=[(c.x, c.y), (q.x, q.y)], pencere=pencere_yap([(c.x, c.y), (q.x, q.y)])))
    if ets and not any(b.durum == 'FAIL' and b.test == 'Y05' for b in out):
        out.append(Bulgu('Y05', 'PASS', '%d devre etiketinde hat uzunluğu = devre uzunluğu (± 0,6 m)' % len(ets), kat))
    if ets and not any(b.durum == 'FAIL' and b.test == 'Y03' for b in out):
        out.append(Bulgu('Y03', 'PASS', '%d devre etiketi kendi mahalinde' % n3, kat))
    elif not ets:
        out.append(Bulgu('Y03', 'INFO', 'devre etiketi (UZ/YER öznitelikli blok) bulunamadı', kat))
    # ---- Y04 kılavuz çizgileri
    kil = []
    for e in cz.msp.query('LINE LWPOLYLINE'):
        n = C.normu(e.dxf.layer)
        if not ('KILAVUZ' in n or ('ISITMA' in n and 'ETIKET' in n) or 'LEADER' in n):
            continue
        g = C.D.geometri(e)
        if g is None or g.length < 5:
            continue
        m = g.interpolate(0.5, normalized=True)
        if not (w[0] <= m.x <= w[2] and w[1] <= m.y <= w[3]):
            continue
        if e.dxftype() == 'LWPOLYLINE' and e.closed:
            continue                                   # etiket çerçevesi, kılavuz değil
        kil.append(g)
    n4 = 0
    for g in kil:
        sorun = []
        if g.length > KILAVUZ_MAX:
            sorun.append('%.0f cm > %.0f' % (g.length, KILAVUZ_MAX))
        a, b = Point(g.coords[0]), Point(g.coords[-1])
        uclar = [mahal_adi(kb, (a.x, a.y)), mahal_adi(kb, (b.x, b.y))]
        for r in kb['rooms']:
            if any(r is u for u in uclar):
                continue
            ic = r['poly'].buffer(-10)
            if not ic.is_empty and g.intersection(ic).length > 15:
                sorun.append('%s içinden geçiyor' % r['name'].replace('\n', ' '))
        if sorun:
            m = g.interpolate(0.5, normalized=True)
            out.append(Bulgu('Y04', 'FAIL', 'kılavuz çizgisi: %s' % '; '.join(sorun[:4]), kat, (m.x, m.y),
                             noktalar=[g.coords[0], g.coords[-1]], pencere=pencere_yap([g.coords[0], g.coords[-1]])))
        else:
            n4 += 1
    if not any(b.durum == 'FAIL' and b.test == 'Y04' for b in out):
        out.append(Bulgu('Y04', 'PASS', '%d kılavuz (≤ %.0f cm, mahal kesmiyor)' % (n4, KILAVUZ_MAX), kat))
    return out


# ------------------------------------------------------------------ Y06 plan W ↔ şema W ↔ Excel W
def _excel_w(yol):
    """Excel'den zon -> W: 'PETEK LİST' (NO | ADI | SICAKLIK | ISI KAYBI W ...) + 'YERDEN ISITMA' devre satırları
    (zon satırı + W satırı). Dönüş: ({zon: W toplam}, {zon: [devre W]}, kaynak açıklaması)"""
    import openpyxl
    wb = openpyxl.load_workbook(yol, data_only=True)
    zon_re = re.compile(r'^(Z\d{2}|B\d{2,3}|\d{3})$')
    petek, devre = {}, {}
    for ws in wb.worksheets:
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        t = ws.title.upper()
        if 'PETEK' in t:
            for r in rows:
                if r and isinstance(r[0], str) and zon_re.match(r[0].strip()) and len(r) > 3 and isinstance(r[3], (int, float)):
                    petek[r[0].strip()] = petek.get(r[0].strip(), 0.0) + float(r[3])
        elif 'YERDEN' in t and 'MMO' not in t:
            for i, r in enumerate(rows):
                zs = [(j, str(v).strip()) for j, v in enumerate(r) if v is not None and zon_re.match(str(v).strip())]
                if len(zs) < 3:
                    continue
                # zon satırının altındaki en alttaki sayısal satır (W)
                k = None
                for kk in range(i + 1, min(i + 7, len(rows))):
                    vals = rows[kk]
                    nums = [vals[j] for j, z in zs if j < len(vals) and isinstance(vals[j], (int, float))]
                    if len(nums) >= len(zs) * 0.8 and all(v > 30 for v in nums):
                        k = kk
                if k is None:
                    continue
                for j, z in zs:
                    v = rows[k][j] if j < len(rows[k]) else None
                    if isinstance(v, (int, float)):
                        devre.setdefault(z, []).append(float(v))
    return petek, devre


def y06_plan_excel(cz, katlar, excel=None):
    out = []
    plan = {}
    plan_w = []
    for k, (kbt, dxdy, n) in katlar.items():
        for et in devre_etiketleri(cz, kbt['pencere']):
            if et['W'] is None:
                continue
            plan_w.append((et['W'], et['zon'], k, (et['kutu'].centroid.x, et['kutu'].centroid.y)))
            if et['zon']:
                plan.setdefault(et['zon'], []).append(et['W'])
    if not plan_w:
        return [Bulgu('Y06', 'INFO', 'planda W değerli devre etiketi yok', None)]
    # şema: "NNNN.NW-Ø20" yazıları (kat paftaları dışındaki yazılar)
    pencereler = [kbt['pencere'] for kbt, d, n in katlar.values()]
    sema = []
    for s, p, h, lay, e in cz.yazilar:
        m = re.match(r'^\s*(\d+(?:[.,]\d+)?)\s*W\s*-\s*Ø\s*20', C.norm(s))
        if m and not any(w[0] <= p[0] <= w[2] and w[1] <= p[1] <= w[3] for w in pencereler):
            sema.append(float(m.group(1).replace(',', '.')))
    if sema:
        kalan = sorted(sema)
        eksik = []
        for W, zon, k, c in sorted(plan_w):
            j = next((i for i, v in enumerate(kalan) if abs(v - W) <= max(0.6, W_TOL * W)), None)
            if j is None:
                eksik.append((W, zon, k, c))
            else:
                kalan.pop(j)
        for W, zon, k, c in eksik[:30]:
            out.append(Bulgu('Y06', 'FAIL', 'plan devre W %.1f (%s) kolon şemasında yok — şema ile plan aynı değerleri taşımalı (S-6)' %
                             (W, zon or '?'), k, c))
        if not eksik:
            out.append(Bulgu('Y06', 'PASS', 'plan devre W değerleri (%d) kolon şemasında aynen var' % len(plan_w), None))
    else:
        out.append(Bulgu('Y06', 'INFO', 'kolon şemasında "W-Ø20" devre yazısı yok; şema karşılaştırılmadı', None))
    if not excel:
        out.append(Bulgu('Y06', 'INFO', 'Excel verilmedi (--excel); plan ↔ Excel karşılaştırılmadı', None))
        return out
    try:
        petek, devre = _excel_w(excel)
    except Exception as ex:
        out.append(Bulgu('Y06', 'FAIL', 'Excel okunamadı: %s' % ex, None))
        return out
    n_ok = 0
    fark = []
    for zon, ws in sorted(plan.items()):
        pw = sum(ws)
        xw = petek.get(zon)
        if xw is None and zon in devre:
            xw = sum(devre[zon])
        if xw is None:
            out.append(Bulgu('Y06', 'FAIL', 'zon %s planda var (%.1f W), Excel\'de yok' % (zon, pw), None))
            continue
        if abs(pw - xw) > max(1.0, W_TOL * pw):
            fark.append((zon, pw, xw))
        else:
            n_ok += 1
    for zon, pw, xw in fark[:25]:
        out.append(Bulgu('Y06', 'FAIL', 'zon %s: plan %.1f W ↔ Excel %.1f W (oran %.2f) — plan, şema ve Excel tek W kaynağından; '
                         'seçilen birim verim teknik rapora yazılır' % (zon, pw, xw, xw / pw if pw else 0), None))
    if len(fark) > 25:
        out.append(Bulgu('Y06', 'FAIL', '… toplam %d zonda plan ↔ Excel W farkı' % len(fark), None))
    if not fark and n_ok:
        out.append(Bulgu('Y06', 'PASS', '%d zonda plan W = Excel W' % n_ok, None))
    return out


def referans_cikar(cz, katlar):
    """--referans-kaydet --tur yerden: kullanıcının yoğunluk / ıslak hacim boru boyları (bilgi)"""
    out = {}
    for k, (kbt, dxdy, n) in katlar.items():
        dv = devreler(cz, kbt['pencere'])
        boru = unary_union([g for g, L, e in dv]) if dv else None
        sat = {}
        for r in kbt['rooms']:
            if boru is None:
                break
            A, kay = _alan_m2(kbt, r)
            L = boru.intersection(r['poly'].buffer(5)).length / 100.0
            if L > 0.5 and A:
                sat['%s D%s %.0f,%.0f' % (r['name'].replace('\n', ' '), r.get('daire'), r['xy'][0], r['xy'][1])] = [
                    round(L, 2), round(A, 2), round(L / A, 2)]
        out[k] = sat
    return out
