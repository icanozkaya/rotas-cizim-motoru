#!/usr/bin/env python3
"""ROTAŞ deneme çıktıları denetimi — tek komut.

    python3 motor/deneme/denetim/denetle.py [dosya_veya_klasor ...]   (varsayılan: proje/denemeler/)
    seçenekler: --rapor YOL (varsayılan kutuphane/arastirma/DENETIM_RAPORU.md), --rapor-yok, --ayrinti

Her DXF için:
  MTY     : MTY kalıntısı (blok adı, blok içi katman, katman tablosu, çizgi tipi, yazı stili, yazıda 'MTY')
  ÖNEK    : 0 / Defpoints dışında ROTAS- ile başlamayan katman sayısı
  LEJANT  : 'LEJANT' yazısı var mı (adında KAPAK geçen dosya muaf)
  KÖPRÜ   : boru katmanında köprü (atlatma) yayı: ARC (≥150°, r≤40) veya LWPOLYLINE kavis segmenti (|bulge|≥0,8, kiriş≤80)
  KESİŞME : boru-boru kesişmesi (iki boru geometrisi uç noktaları dışında kesişiyor; köprülü kesişmeler ayrıca KÖPRÜ'de)
  YAZI    : yazı-yazı çakışması (ezdxf ölçülü yazı kutuları, küçük kutunun >%2'si; mimari-mimari ve aynı INSERT hariç)
  PIS/TEMIZ: pis su – temiz su üst üste geçişi (farklı düzlem): kesişme değil, BİLGİ
  ELEK    : elektrik/kablo/sinyal katmanındaki nesne sayısı + 'KABLO' geçen yazı
  AUDIT   : ezdxf audit hata sayısı (düzeltmeler ayrıca)
  YETERSİZ: 'yetersiz' / 'uygun değil' geçen yazı
Onaylı kazan dairesi (dosya adı *KAZAN_DAIRESI_PLAN_KESIT* veya XDATA 'ROTAS'=ONAYLI_KAZAN_DAIRESI çerçevesi):
MTY temizliği istisnası YOK; bu bölgedeki köprü/kesişmeler yalnız BİLGİ olarak raporlanır, hata sayılmaz.
"""
import math
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import ezdxf
from ezdxf import disassemble
from shapely import STRtree
from shapely.geometry import LineString, Point, Polygon, box

KOK = Path(__file__).resolve().parents[3]
VARSAYILAN = KOK / 'proje' / 'denemeler'
RAPOR = KOK / 'kutuphane' / 'arastirma' / 'DENETIM_RAPORU.md'
UC_TOL = 15.0  # cm: bir borunun ucu kesişmeye bu kadar yakınsa bağlantı (T / ağız) sayılır
YAZI_ORAN = 0.02  # yazı çakışması eşiği: kesişim > küçük yazı kutusunun %2'si (yazı tipi ölçülü kutu)

TR = str.maketrans({'İ': 'I', 'ı': 'I', 'i': 'I', 'Ğ': 'G', 'ğ': 'G', 'Ü': 'U', 'ü': 'U', 'Ş': 'S', 'ş': 'S',
                    'Ö': 'O', 'ö': 'O', 'Ç': 'C', 'ç': 'C'})


def norm(s):
    return (s or '').translate(TR).upper()


# ---------------------------------------------------------------- boru katmanı
BORU_EVET = ('BORU', 'KANAL', 'SOGUK', 'SICAK', 'SIRKULASYON', 'PIS-SU', 'PISSU', 'SIHHI-PIS', 'YAGMUR', 'GIDIS',
             'DONUS', 'PEX', 'FLEX', 'DRENAJ', 'YAKIT', 'SEBEKE', 'YANGIN-KOLON', 'DOLAP-KOLON', 'SIHHI', 'ISITMA',
             'YANGIN', 'DOGALGAZ')
BORU_HAYIR = ('CAP', 'YAZI', '-NO', 'KOLONNO', 'MASKE', 'SEMBOL', 'CIHAZ', 'TABLO', 'LEJANT', 'NOT', 'MIMARI', '-OK',
              'ETIKET', 'KAT', 'BASLIK', 'DEPO', 'VANA', 'SPRINKLER', 'NOZUL', 'ALAN', 'TARAMA', 'KAPSAMA', 'ERISIM',
              'KAPSANMAYAN', 'HIDROLIK', 'DUGUM', 'BALON', 'KOT', 'ITFAIYE', 'MENFEZ', 'DAMPER', 'POMPA', 'BACA',
              'BOLGE', 'SINYAL', 'KOLLEKTOR', 'KOLEKTOR', 'SAYAC', 'REGULATOR', 'SERVIS', 'UYARI', 'PAFTA', 'ARMATUR',
              'HESAP', 'DOSEME', 'YOGUSMA', 'SU-SEVIYE', 'DETAY', 'TEFRIS', 'METRAJ', 'KUTUSU', 'DOLAP', 'SEMA-')


def boru_katmani(ad):
    n = norm(ad)
    if not any(k in n for k in BORU_EVET):
        return False
    if any(k in n for k in BORU_HAYIR):
        # dolap borusu / yangın dolap kolonu gibi açık boru adlarını geri al
        return ('BORU' in n or n.endswith('-KOLON')) and not any(k in n for k in ('CAP', 'YAZI', 'MASKE', 'NO'))
    return True


def elektrik_katmani(ad):
    n = norm(ad)
    return any(k in n for k in ('ELEKTRIK', 'KABLO', 'SINYAL'))


# ---------------------------------------------------------------- yardımcılar
def metinler(doc):
    """(metin, varlık, alan) — alan: 'msp' veya 'blok'"""
    for e in doc.modelspace():
        t = e.dxftype()
        if t == 'TEXT':
            yield e.dxf.text, e, 'msp'
        elif t == 'MTEXT':
            yield e.plain_text(), e, 'msp'
        elif t == 'INSERT':
            for a in e.attribs:
                yield a.dxf.text, a, 'msp'
    for b in doc.blocks:
        if b.is_any_layout:
            continue
        for e in b:
            t = e.dxftype()
            if t in ('TEXT', 'ATTDEF'):
                yield e.dxf.text, e, 'blok'
            elif t == 'MTEXT':
                yield e.plain_text(), e, 'blok'


def yazi_kutusu(e):
    t = e.dxftype()
    try:
        if t in ('TEXT', 'ATTRIB'):
            s = e.dxf.text or ''
            if not s.strip():
                return None
            h = e.dxf.get('height', 2.5) or 2.5
            w = len(s) * h * 0.8 * (e.dxf.get('width', 1.0) or 1.0)
            ha, va = e.dxf.get('halign', 0), e.dxf.get('valign', 0)
            p = e.dxf.align_point if (ha or va) and e.dxf.hasattr('align_point') else e.dxf.insert
            if ha in (3, 5):  # aligned / fit
                p = e.dxf.insert
                ha = 0
            dx = {0: 0, 1: -0.5, 2: -1.0, 4: -0.5}.get(ha, 0) * w
            dy = {0: 0, 1: 0, 2: -0.5, 3: -1.0}.get(va, 0) * h
            if ha == 4 and va == 0:
                dy = -0.5 * h
            rot = math.radians(e.dxf.get('rotation', 0) or 0)
        elif t == 'MTEXT':
            s = e.plain_text()
            if not s.strip():
                return None
            satir = s.split('\n')
            h0 = e.dxf.get('char_height', 2.5) or 2.5
            h = h0 * (1.0 + 0.67 * (len(satir) - 1))
            w = max(len(x) for x in satir) * h0 * 0.8
            if e.dxf.hasattr('width') and e.dxf.width and e.dxf.width > 0:
                w = min(w, e.dxf.width) if len(satir) == 1 else w
            ap = e.dxf.get('attachment_point', 1)
            col, row = (ap - 1) % 3, (ap - 1) // 3
            dx = (0, -0.5, -1.0)[col] * w
            dy = (-1.0, -0.5, 0.0)[row] * h
            p = e.dxf.insert
            rot = math.radians(e.dxf.get('rotation', 0) or 0)
            if e.dxf.hasattr('text_direction'):
                d = e.dxf.text_direction
                rot = math.atan2(d[1], d[0])
        else:
            return None
    except Exception:
        return None
    c, s_ = math.cos(rot), math.sin(rot)
    pts = []
    for x, y in ((dx, dy), (dx + w, dy), (dx + w, dy + h), (dx, dy + h)):
        pts.append((p[0] + x * c - y * s_, p[1] + x * s_ + y * c))
    return Polygon(pts)


def yazi_poligonu(e):
    """Yazının çizimdeki kutusu: ezdxf yazı tipi ölçüsüyle (disassemble.make_primitive — uctan_uca ykontrol4 ile
    aynı yöntem); ölçülemezse tahmini kutu (0,8·h·karakter)."""
    try:
        v = [(p.x, p.y) for p in disassemble.make_primitive(e).vertices()]
        if len(v) >= 4:
            pg = Polygon(v)
            if pg.is_valid and pg.area > 0:
                return pg
    except Exception:
        pass
    return yazi_kutusu(e)


def mimari_katman(ad):
    return 'MIMARI' in norm(ad)


def yazi_cakismalari(msp, oran=None):
    """Yazı-yazı çakışması — denetim ve uctan_uca/ykontrol4 ORTAK kuralı.
    Yazılar: model alanı TEXT / MTEXT / görünür ATTRIB. Sayılmayan: aynı INSERT'in kendi öznitelikleri; iki yazı da
    MİMARİ katmanında (mimar altlığının kendi yazıları — bilgi olarak ayrı döner). Çakışma: kesişim alanı küçük
    kutunun `oran`'ından büyük. Dönüş: (cakisma_listesi, mimari_mimari_sayisi); liste öğesi
    (katman1, yazı1, katman2, yazı2, (x, y))."""
    oran = YAZI_ORAN if oran is None else oran
    ys = []
    for e in msp:
        t = e.dxftype()
        if t in ('TEXT', 'MTEXT'):
            parca = [(e, e.dxf.handle)]
        elif t == 'INSERT':
            parca = [(a, e.dxf.handle) for a in e.attribs if not a.is_invisible]
        else:
            continue
        for y, sahip in parca:
            s_ = (y.plain_text() if y.dxftype() == 'MTEXT' else y.dxf.text) or ''
            if not s_.strip():
                continue
            pg = yazi_poligonu(y)
            if pg is not None and pg.is_valid and pg.area > 0:
                ys.append((y.dxf.layer, s_.strip(), pg, sahip))
    out, mim = [], 0
    if len(ys) < 2:
        return out, mim
    agac = STRtree([y[2] for y in ys])
    sol, sag = agac.query([y[2] for y in ys], predicate='intersects')
    for i, j in zip(sol, sag):
        if i >= j:
            continue
        l1, s1, a, h1 = ys[i]
        l2, s2, b, h2 = ys[j]
        if h1 == h2:
            continue
        if a.intersection(b).area <= oran * min(a.area, b.area):
            continue
        if mimari_katman(l1) and mimari_katman(l2):
            mim += 1
            continue
        c = a.centroid
        out.append((l1, s1[:25], l2, s2[:25], (round(c.x), round(c.y))))
    return out, mim


def pis_su_katmani(ad):
    """cazibeli pis su borusu (tavandan geçen dahil); yağmur / drenaj DEĞİL"""
    n = norm(ad)
    return 'PIS' in n and boru_katmani(ad)


def temiz_su_katmani(ad):
    n = norm(ad)
    return any(k in n for k in ('SOGUK', 'SICAK', 'SIRKULASYON', 'TEMIZ', 'SEBEKE')) and boru_katmani(ad)


def farkli_duzlem(l1, l2):
    """Pis su (eğimli, döşeme altı / tavandan) ile temiz su (basınçlı, duvar / döşeme içi) farklı düzlemdedir: planda
    veya şemada üst üste geçmeleri kesişme sayılmaz, ayrı bilgi sütununda gösterilir."""
    return (pis_su_katmani(l1) and temiz_su_katmani(l2)) or (pis_su_katmani(l2) and temiz_su_katmani(l1))


def boru_kesismeleri(doc, onayda=lambda p: False):
    """Boru-boru kesişmesi — denetim ve uctan_uca çıktısının ORTAK kuralı.
    Boru katmanları `boru_katmani`; uçlarından UC_TOL içindeki geçiş bağlantı (T / ağız) sayılır; köprü yayına 45 cm
    içindeki kesişme köprüde sayılır. Dönüş sözlüğü: kesisme [(katman1, katman2, (x, y))] (HATA), duzlem (pis su -
    temiz su, farklı düzlem — BİLGİ), kesisme_onayli (onaylı kazan dairesi — BİLGİ), kopru_hata, kopru_bilgi."""
    msp = doc.modelspace()
    boru_k = {l.dxf.name for l in doc.layers if boru_katmani(l.dxf.name)}
    geos, lays, koprus = [], [], []
    for e in msp:
        if e.dxf.get('layer', '') not in boru_k or e.dxftype() not in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC'):
            continue
        g = geometri(e)
        if g is not None:
            geos.append(g)
            lays.append(e.dxf.layer)
        for p, acik in koprü_segmentleri(e):
            koprus.append((p, acik, e.dxf.layer))
    out = dict(boru_katman=len(boru_k), kesisme=[], duzlem=[], kesisme_onayli=[],
               kopru_hata=[k for k in koprus if not onayda(k[0])], kopru_bilgi=[k for k in koprus if onayda(k[0])])
    kopru_noktalari = [k[0] for k in koprus]
    if len(geos) > 1:
        agac = STRtree(geos)
        sol, sag = agac.query(geos, predicate='crosses')
        for i, j in zip(sol, sag):
            if i >= j:
                continue
            a, b = geos[i], geos[j]
            x = a.intersection(b)
            noktalar = [x] if x.geom_type == 'Point' else \
                [g for g in getattr(x, 'geoms', []) if g.geom_type == 'Point']
            for p in noktalar:
                if not (ic_nokta(a, p, UC_TOL) and ic_nokta(b, p, UC_TOL)):
                    continue
                if any(p.distance(k) <= 45 for k in kopru_noktalari):
                    continue  # köprülü kesişme: KÖPRÜ sütununda sayıldı
                kay = (lays[i], lays[j], (round(p.x, 1), round(p.y, 1)))
                if onayda(p):
                    out['kesisme_onayli'].append(kay)
                elif farkli_duzlem(lays[i], lays[j]):
                    out['duzlem'].append(kay)
                else:
                    out['kesisme'].append(kay)
    return out


def koprü_segmentleri(e):
    """boru varlığındaki köprü yaylarının (merkez nokta, açıklama) listesi"""
    out = []
    t = e.dxftype()
    if t == 'ARC':
        sw = (e.dxf.end_angle - e.dxf.start_angle) % 360
        if sw >= 150 and e.dxf.radius <= 40:
            out.append((Point(e.dxf.center[0], e.dxf.center[1]), 'ARC r=%.0f' % e.dxf.radius))
    elif t == 'LWPOLYLINE':
        pts = list(e.get_points('xyb'))
        n = len(pts)
        rng = range(n if e.closed else n - 1)
        for i in rng:
            x1, y1, b = pts[i]
            x2, y2, _ = pts[(i + 1) % n]
            kiris = math.hypot(x2 - x1, y2 - y1)
            if abs(b) >= 0.8 and 0 < kiris <= 80:
                out.append((Point((x1 + x2) / 2, (y1 + y2) / 2), 'bulge %.2f' % b))
    return out


def geometri(e):
    t = e.dxftype()
    try:
        if t == 'LINE':
            a, b = e.dxf.start, e.dxf.end
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-6:
                return None
            return LineString([(a[0], a[1]), (b[0], b[1])])
        if t in ('LWPOLYLINE', 'POLYLINE', 'ARC'):
            if t == 'ARC':
                pts = [(v.x, v.y) for v in e.flattening(2.0)]
            elif t == 'LWPOLYLINE':
                pts = [(v[0], v[1]) for v in ezdxf.path.make_path(e).flattening(2.0)]
            else:
                pts = [(v.x, v.y) for v in ezdxf.path.make_path(e).flattening(2.0)]
            pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
            if len(pts) < 2:
                return None
            return LineString(pts)
    except Exception:
        return None
    return None


def ic_nokta(g, p, tol):
    """p, g'nin uçlarından tol uzakta mı"""
    c = list(g.coords)
    return Point(c[0]).distance(p) > tol and Point(c[-1]).distance(p) > tol


# ---------------------------------------------------------------- denetim
def denetle(yol):
    r = {'dosya': yol, 'hata': None}
    try:
        doc = ezdxf.readfile(str(yol))
    except Exception as ex:
        r['hata'] = 'okunamadı: %s' % ex
        return r
    msp = doc.modelspace()
    onayli_dosya = 'KAZAN_DAIRESI_PLAN_KESIT' in yol.name.upper()
    # kapak istisnası: proje kapağı paftasında sembol yoktur, lejant aranmaz (diğer bütün kontroller geçerli)
    r['kapak'] = 'KAPAK' in norm(yol.stem)
    onay_bolge = []
    for e in msp:
        try:
            if e.has_xdata('ROTAS') and any(v == 'ONAYLI_KAZAN_DAIRESI' for _, v in e.get_xdata('ROTAS')):
                xs = [p[0] for p in e.get_points('xy')]
                ys = [p[1] for p in e.get_points('xy')]
                onay_bolge.append(box(min(xs), min(ys), max(xs), max(ys)))
        except Exception:
            pass
    r['onayli'] = 'dosya' if onayli_dosya else ('bölge x%d' % len(onay_bolge) if onay_bolge else '')

    def onayda(p):
        return onayli_dosya or any(b.buffer(1).contains(p) for b in onay_bolge)

    # --- MTY
    mty = defaultdict(int)
    mty_ornek = defaultdict(set)
    for b in doc.blocks:
        if b.is_any_layout:
            continue
        if 'MTY' in norm(b.name):
            mty['blok adı'] += 1
            mty_ornek['blok adı'].add(b.name)
        for e in b:
            if 'MTY' in norm(e.dxf.get('layer', '')):
                mty['blok içi katman'] += 1
                mty_ornek['blok içi katman'].add(e.dxf.layer)
    for l in doc.layers:
        if 'MTY' in norm(l.dxf.name):
            mty['katman'] += 1
            mty_ornek['katman'].add(l.dxf.name)
    for lt in doc.linetypes:
        if 'MTY' in norm(lt.dxf.name):
            mty['çizgi tipi'] += 1
            mty_ornek['çizgi tipi'].add(lt.dxf.name)
    for st in doc.styles:
        if 'MTY' in norm(st.dxf.name):
            mty['yazı stili'] += 1
            mty_ornek['yazı stili'].add(st.dxf.name)
    for e in msp:
        if e.dxftype() == 'INSERT' and 'MTY' in norm(e.dxf.name):
            mty['blok ekleme'] += 1
    lejant = False
    yetersiz = []
    kablo_yazi = 0
    kablo_ornek = []
    yazilar = []
    for s, e, alan in metinler(doc):
        n = norm(s)
        if 'MTY' in n:
            mty['yazı'] += 1
            mty_ornek['yazı'].add(s.strip()[:40])
        if 'LEJANT' in n:
            lejant = True
        for anah in ('YETERSIZ', 'UYGUN DEGIL'):
            if anah in n:
                i = n.index(anah)
                yetersiz.append(' '.join(s[max(0, i - 30):i + 30].split()))
                break
        if 'KABLO' in n:
            kablo_yazi += 1
            i = n.index('KABLO')
            kablo_ornek.append(' '.join(s[max(0, i - 25):i + 25].split()))
        if alan == 'msp':
            yazilar.append(e)
    r['mty'] = sum(mty.values())
    r['mty_ayrinti'] = dict(mty)
    r['mty_ornek'] = {k: sorted(v)[:6] for k, v in mty_ornek.items()}
    r['lejant'] = lejant
    r['yetersiz'] = yetersiz

    # --- önek
    onek = [l.dxf.name for l in doc.layers
            if l.dxf.name not in ('0', 'Defpoints') and not l.dxf.name.startswith('ROTAS-')]
    r['onek'] = len(onek)
    r['onek_ornek'] = sorted(onek)[:8]

    # --- elektrik
    elek_k = {l.dxf.name for l in doc.layers if elektrik_katmani(l.dxf.name)}
    elek_n = sum(1 for e in msp if e.dxf.get('layer', '') in elek_k)
    r['elektrik'] = elek_n + kablo_yazi
    r['elektrik_ornek'] = sorted(elek_k)
    r['elektrik_katman_n'] = elek_n
    r['kablo_ornek'] = kablo_ornek[:3]

    # --- boru: köprü + kesişme (ortak kural: boru_kesismeleri)
    bk = boru_kesismeleri(doc, onayda)
    r['boru_katman'] = bk['boru_katman']
    r['kopru'] = len(bk['kopru_hata'])
    r['kopru_bilgi'] = len(bk['kopru_bilgi'])
    r['kopru_ornek'] = ['%s (%.0f, %.0f) %s' % (k[2], k[0].x, k[0].y, k[1]) for k in bk['kopru_hata'][:5]]
    r['kesisme'] = len(bk['kesisme'])
    r['kesisme_bilgi'] = len(bk['kesisme_onayli'])
    r['kesisme_ornek'] = ['%s / %s (%.0f, %.0f)' % (l1, l2, x, y) for l1, l2, (x, y) in bk['kesisme'][:5]]
    r['duzlem'] = len(bk['duzlem'])
    r['duzlem_ornek'] = ['(%.0f, %.0f)' % xy for _, _, xy in bk['duzlem'][:3]]

    # --- yazı-yazı çakışması (ortak kural: yazi_cakismalari)
    yc, yc_mim = yazi_cakismalari(msp)
    r['yazi'] = len(yc)
    r['yazi_mimari'] = yc_mim
    r['yazi_ornek'] = ['%s "%s" / %s "%s" (%d, %d)' % (a, b, c, d, p[0], p[1]) for a, b, c, d, p in yc[:5]]

    # --- audit (son: belgeyi değiştirebilir)
    try:
        aud = doc.audit()
        r['audit'] = len(aud.errors)
        r['audit_duzeltme'] = len(aud.fixes)
        r['audit_ornek'] = [str(x.message)[:80] for x in aud.errors[:3]]
    except Exception as ex:
        r['audit'] = 1
        r['audit_duzeltme'] = 0
        r['audit_ornek'] = ['audit çöktü: %s' % ex]

    r['gecti'] = (r['mty'] == 0 and r['onek'] == 0 and (r['lejant'] or r['kapak']) and r['kopru'] == 0 and r['kesisme'] == 0
                  and r['yazi'] == 0 and r['elektrik'] == 0 and r['audit'] == 0 and not r['yetersiz'])
    return r


# ---------------------------------------------------------------- revizyon grupları
def revizyon(yol):
    m = re.match(r'^(.*)_R(\d+)$', yol.stem, re.I)
    if m:
        return yol.parent / m.group(1), int(m.group(2))
    return yol.parent / yol.stem, 1


def siniflandir(dosyalar):
    """f -> (rev, eski_mi, grupta_birden_cok_mu). Aynı taban addaki en büyük R en yenidir. Ayrıca sonekisiz R1
    dosyası, aynı klasörde adı onunla başlayan bir R2+ türevi varsa (ör. X.dxf -> X_OFIS_R2.dxf) eski sayılır."""
    grup = defaultdict(list)
    for f in dosyalar:
        taban, rev = revizyon(f)
        grup[taban].append((rev, f))
    out = {}
    for taban, lst in grup.items():
        en = max(r for r, _ in lst)
        for rev, f in lst:
            out[f] = [rev, rev != en, len(lst) > 1]
    for f in dosyalar:
        taban, rev = revizyon(f)
        if rev == 1 and not out[f][1]:
            turev = [g for g in dosyalar if g.parent == f.parent and revizyon(g)[1] > 1
                     and revizyon(g)[0].name.startswith(f.stem + '_')]
            if turev:
                out[f][1] = True
    return {f: tuple(v) for f, v in out.items()}


def dosyalari_topla(args):
    kaynak = [Path(a) for a in args] or [VARSAYILAN]
    out = []
    for k in kaynak:
        k = k if k.is_absolute() else (Path.cwd() / k)
        if k.is_dir():
            # _arsiv (eski revizyon arşivi) yalnız açıkça verilirse denetlenir
            out += sorted(f for f in k.rglob('*.dxf')
                          if '_arsiv' not in f.relative_to(k).parts)
        elif k.suffix.lower() == '.dxf' and k.exists():
            out.append(k)
        else:
            print('! atlandı:', k)
    return sorted(set(out))


def goreli(p):
    try:
        return str(p.resolve().relative_to(KOK))
    except ValueError:
        return str(p)


def isaret(ok):
    return '✓' if ok else '✗'


SUTUN = ['Dosya', 'Rev', 'Sonuç', 'MTY', 'Önek', 'Lejant', 'Köprü', 'Kesişme', 'Yazı', 'Elek', 'Audit',
         'Yetersiz', 'Pis/temiz (bilgi)', 'Onaylı (bilgi)']


def satir(r, durum):
    if r.get('hata'):
        return [goreli(r['dosya']), durum, '✗ ' + r['hata']] + [''] * (len(SUTUN) - 3)
    bilgi = ''
    if r['onayli']:
        bilgi = '%s: köprü %d, kesişme %d' % (r['onayli'], r['kopru_bilgi'], r['kesisme_bilgi'])
    lej = '- (kapak)' if r['kapak'] else isaret(r['lejant'])
    return [goreli(r['dosya']), durum, isaret(r['gecti']), r['mty'], r['onek'], lej,
            r['kopru'], r['kesisme'], r['yazi'], r['elektrik'], r['audit'], len(r['yetersiz']), r['duzlem'] or '', bilgi]


def konsol_tablo(baslik, satirlar):
    print('\n== %s ==' % baslik)
    if not satirlar:
        print('(yok)')
        return
    s = [[str(x) for x in r] for r in satirlar]
    gen = [max(len(SUTUN[i]), *(len(r[i]) for r in s)) for i in range(len(SUTUN))]
    print('  '.join(SUTUN[i].ljust(gen[i]) for i in range(len(SUTUN))))
    print('  '.join('-' * g for g in gen))
    for r in s:
        print('  '.join(r[i].ljust(gen[i]) for i in range(len(SUTUN))))


def md_tablo(satirlar):
    if not satirlar:
        return '_(yok)_\n'
    out = ['| ' + ' | '.join(SUTUN) + ' |', '|' + '---|' * len(SUTUN)]
    for r in satirlar:
        out.append('| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |')
    return '\n'.join(out) + '\n'


def ayrinti_md(r):
    if r.get('hata'):
        return '- **%s**: %s\n' % (goreli(r['dosya']), r['hata'])
    ps = []
    if r['mty']:
        ps.append('MTY ' + ', '.join('%s %d' % (k, v) for k, v in r['mty_ayrinti'].items()) +
                  ' — örn. ' + '; '.join('%s: %s' % (k, ', '.join(v[:3])) for k, v in r['mty_ornek'].items() if v))
    if r['onek']:
        ps.append('ROTAS- olmayan katman: ' + ', '.join(r['onek_ornek']))
    if not r['lejant'] and not r['kapak']:
        ps.append('LEJANT yazısı yok')
    if r['kopru']:
        ps.append('köprü: ' + '; '.join(r['kopru_ornek']))
    if r['kesisme']:
        ps.append('kesişme noktaları: ' + ', '.join(r['kesisme_ornek']))
    if r['yazi']:
        ps.append('yazı çakışması: ' + '; '.join(r['yazi_ornek']))
    if r['duzlem']:
        ps.append('pis su / temiz su farklı düzlem üst üste geçiş (bilgi, hata değil): %d — örn. %s'
                  % (r['duzlem'], ', '.join(r['duzlem_ornek'])))
    if r.get('yazi_mimari'):
        ps.append('mimari altlığın kendi yazı çakışması (bilgi, mimar çizimi değiştirilmez): %d' % r['yazi_mimari'])
    if r['elektrik']:
        ps.append('elektrik: katman %s (%d nesne); KABLO yazısı %d%s' % (
            ', '.join(r['elektrik_ornek']) or '-', r['elektrik_katman_n'], r['elektrik'] - r['elektrik_katman_n'],
            (' — örn. "' + '" / "'.join(r['kablo_ornek']) + '"') if r['kablo_ornek'] else ''))
    if r['audit']:
        ps.append('audit: ' + ' / '.join(r['audit_ornek']))
    if r['yetersiz']:
        ps.append('yetersiz/uygun değil: ' + ' / '.join(r['yetersiz'][:3]))
    if r['onayli']:
        ps.append('ONAYLI kazan dairesi (%s): köprü %d, kesişme %d — bilgi, hata sayılmadı'
                  % (r['onayli'], r['kopru_bilgi'], r['kesisme_bilgi']))
    if not ps:
        return ''
    return '- **%s**\n' % goreli(r['dosya']) + ''.join('  - %s\n' % p for p in ps)


def main(argv):
    rapor_yolu, rapor_yaz, ayrinti = RAPOR, True, False
    args = []
    it = iter(argv)
    for a in it:
        if a == '--rapor':
            rapor_yolu = Path(next(it))
        elif a == '--rapor-yok':
            rapor_yaz = False
        elif a == '--ayrinti':
            ayrinti = True
        else:
            args.append(a)
    dosyalar = dosyalari_topla(args)
    t0 = time.time()
    sonuc = {}
    for f in dosyalar:
        print('denetleniyor:', goreli(f), file=sys.stderr)
        sonuc[f] = denetle(f)
    sinif = siniflandir(dosyalar)
    guncel, eski = [], []
    for f in sorted(dosyalar, key=lambda x: (str(revizyon(x)[0]), revizyon(x)[1])):
        rev, es, cok = sinif[f]
        if es:
            eski.append(satir(sonuc[f], 'R%d eski' % rev))
        else:
            guncel.append(satir(sonuc[f], 'R%d' % rev + (' (en yeni)' if cok else '')))
    konsol_tablo('EN YENİ REVİZYONLAR', guncel)
    konsol_tablo('ESKİ REVİZYONLAR', eski)
    n_g = sum(1 for r in guncel if r[2] == '✓')
    print('\nEn yeni revizyon: %d dosya, %d geçti, %d kaldı. Süre %.0f s.' % (len(guncel), n_g, len(guncel) - n_g,
                                                                          time.time() - t0))
    if ayrinti:
        for f in dosyalar:
            a = ayrinti_md(sonuc[f])
            if a:
                print(a, end='')
    if rapor_yaz:
        rapor_yaz_md(rapor_yolu, dosyalar, sonuc, guncel, eski, n_g, args)
        print('Rapor:', goreli(rapor_yolu))


def rapor_yaz_md(yol, dosyalar, sonuc, guncel, eski, n_g, args):
    sinif = siniflandir(dosyalar)
    en_yeni = {f for f in dosyalar if not sinif[f][1]}
    t = time.strftime('%d.%m.%Y %H:%M')
    md = ['# Deneme çıktıları denetim raporu', '',
          'Üretildi: %s — `python3 motor/deneme/denetim/denetle.py %s`' % (t, ' '.join(args) or ''), '',
          'Kurallar: README en üst blok (14.10.2026 B): MTY bloğu/kalıntısı yok, katmanlar `ROTAS-`, boru atlatma '
          '(köprü) yok, elektrik kalemi yok, lejant zorunlu, "yetersiz" yazılmaz. Onaylı kazan dairesi için MTY '
          'istisnası **yok**; onaylı çizimdeki köprü/kesişmeler yalnız bilgi olarak verilir.', '',
          '**Sütunlar:** MTY = MTY kalıntısı toplamı (blok adı + blok içi katman + katman + çizgi tipi + yazı stili + '
          'blok ekleme + yazı); Önek = 0/Defpoints dışında ROTAS- olmayan katman; Köprü = boru katmanında atlatma yayı; '
          'Kesişme = köprüsüz boru-boru kesişmesi (pis su-temiz su hariç); Yazı = yazı-yazı çakışan çift; '
          'Pis/temiz (bilgi) = farklı düzlemdeki pis su-temiz su üst üste geçişi; Elek = elektrik/kablo/sinyal '
          'katmanındaki nesne + KABLO yazısı; Audit = ezdxf audit hatası; Yetersiz = "yetersiz/uygun değil" yazısı.',
          '', '## En yeni revizyonlar (%d dosya: %d ✓, %d ✗)' % (len(guncel), n_g, len(guncel) - n_g), '',
          md_tablo(guncel), '## Eski revizyonlar (bilgi; yerini daha yeni R almış)', '', md_tablo(eski),
          '## Ayrıntı — en yeni revizyonlar', '']
    for f in dosyalar:
        if f in en_yeni and ayrinti_md(sonuc[f]):
            md.append(ayrinti_md(sonuc[f]))
    md += ['', '## Sınırlar', '',
           '- Boru katmanı katman adından seçilir (BORU, KANAL, SICAK, SOGUK, PIS, YAGMUR, GIDIS/DONUS, YANGIN, '
           'DOGALGAZ, SIHHI...; CAP/YAZI/SEMBOL/CIHAZ/MIMARI vb. hariç). Kesişme yalnız model alanında, uç noktalardan '
           '15 cm içerideki geçişler (T bağlantısı, kanal ağzına giren flex vb. sayılmaz).',
           '- Köprü: boru katmanında ARC (≥150°, r≤40 cm) veya LWPOLYLINE kavis segmenti (|bulge|≥0,8, kiriş≤80 cm). '
           'Köprü noktasına 45 cm içindeki kesişmeler kesişme sütununda tekrar sayılmaz.',
           '- Yazı kutuları ezdxf yazı tipi ölçüsüyle (ölçülemezse 0,8·h·karakter); kesişim > küçük kutunun %2\'si çakışma. '
           'Aynı INSERT\'in öznitelikleri ve mimari-mimari çiftleri sayılmaz (uctan_uca ykontrol4 ile ortak kural).',
           '- Pis su ile temiz su farklı düzlemdedir: üst üste geçişleri kesişme sayılmaz, "Pis/temiz (bilgi)" sütununda verilir.',
           '- Dosya adında KAPAK geçen pafta lejant kontrolünden muaftır. Varsayılan taramada `_arsiv` atlanır.',
           '- Onaylı bölge: `*KAZAN_DAIRESI_PLAN_KESIT*` dosyaları tamamen; diğer dosyalarda XDATA '
           '`ROTAS: ONAYLI_KAZAN_DAIRESI` çerçevesinin içi.', '']
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text('\n'.join(md), encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1:])
