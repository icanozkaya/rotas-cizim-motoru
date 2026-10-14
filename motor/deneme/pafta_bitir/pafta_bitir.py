# -*- coding: utf-8 -*-
"""ROTAŞ teslim öncesi "pafta bitirme" aracı (deneme modülü: pafta_bitir, 14.10.2026).

    bitir(giris.dxf, cikis.dxf, ekler=[...])

1. Model uzayındaki paftaları (çerçeve dikdörtgenleri; yoksa çizim kümeleri) bulur, toplam sınırı çıkarır.
   Aşırı geniş (içeriğinin çok dışına taşan) çerçeveyi raporlar ve isteğe bağlı içeriğe göre daraltır.
2. Kullanılan sembollerin LEJANT + ADET tablosunu (semboller2: ROTAS saf geometri kütüphanesi, MTY'siz) ve BORU
   METRAJI tablosunu (katman + çap bazında toplam uzunluk; çap DN/Ø/inç etiketlerinden) en sağa yeni bir paftaya koyar.
   Girdide zaten "LEJANT ... METRAJ" paftası varsa (ör. uctan_uca R4 çıktısı) ikinci kez üretilmez (lejant='otomatik').
3. Ek DXF'leri (ısı kaybı / yerden ısıtma hesapları, proje kapağı) paftaların SOL ALT köşesine,
   alt kenarları hizalı, aralıklı ve kendi pafta çerçeveleriyle yerleştirir (ezdxf Importer; katman adları korunur,
   aynı adlı FARKLI blok yeniden adlandırılır, aynı içerikli blok paylaşılır). Ek başına isteğe bağlı:
   katman_cevir {'MTY-': 'ROTAS-'} (önek çevirisi), metin_cevir {'MTY': 'ROTAŞ'}, yazi_sigdir (ekin kendi içinde
   birbirine taşan yazılarının genişlik çarpanı daraltılır; konum / boy değişmez).
4. Kontroller: katman öneki ROTAS- (0 / Defpoints / yalnız blok içinde kullanılan katmanlar hariç), yazı-yazı çakışması,
   boş katman temizliği, AUDIT (yazmadan önce ve geri okumada).

Girdideki tasarım (boru, sembol, adet, katman) DEĞİŞTİRİLMEZ; yalnız yeni pafta, tablo ve ek eklenir.
"""
import math
import os
import re
import sys
from collections import defaultdict, deque

import ezdxf
from ezdxf import bbox as _bbox
from ezdxf import disassemble
from ezdxf.addons import Importer
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, '..', 'semboller2'))
import sembol2 as S  # noqa: E402  (ROTAS sembol kütüphanesi v2 — MTY bağımlılığı yok)

PAFTA_KATMAN_ANAHTAR = ('PAFTA', 'CERCEVE', 'ÇERÇEVE', 'ANTET', 'FRAME')
SERBEST = {'0', 'DEFPOINTS'}
ARALIK = 100.0            # paftalar arası boşluk (cm)
KENAR = 100.0             # pafta iç çerçevesi ile içerik arası boşluk
BASLIK_BANT = 120.0       # pafta başlık yazısı için alt bant

BORU_ANAHTAR = ('BORU', 'PVC', 'PEX')     # ek anahtar: bitir(..., boru_ek_anahtar=('HAT',))
BORU_HARIC = ('CAP', 'ÇAP', 'YAZI', 'KOLONNO', 'KOLON-NO', 'ETIKET', 'SEMBOL', 'LEJANT', 'NO')
# boru katmanı -> (aile, açıklama)
BORU_ACIKLAMA = [
    ('TAVANDAN', 'PIS', 'PİS SU BORUSU (TAVANDAN)'),
    ('PIS', 'PIS', 'PİS SU BORUSU'),
    ('PVC', 'PIS', 'PVC BORU'),
    ('SOGUK', 'SOGUK', 'SOĞUK SU BORUSU'),
    ('SICAK', 'SICAK', 'SICAK SU BORUSU'),
    ('SIRK', 'SICAK', 'SİRKÜLASYON BORUSU'),
    ('TEMIZ', 'SOGUK', 'TEMİZ SU BORUSU'),
    ('YAGMUR', 'YAGMUR', 'YAĞMUR SUYU BORUSU'),
    ('PEX', 'ISITMA', 'PEX BORU (YERDEN ISITMA)'),
    ('GIDIS', 'ISITMA', 'ISITMA GİDİŞ BORUSU'),
    ('DONUS', 'ISITMA', 'ISITMA DÖNÜŞ BORUSU'),
    ('ISITMA', 'ISITMA', 'ISITMA BORUSU'),
    ('SPRINK', 'YANGIN', 'SPRİNKLER BORUSU'),
    ('YANGIN', 'YANGIN', 'YANGIN BORUSU'),
    ('GAZ', 'GAZ', 'DOĞALGAZ BORUSU'),
]
CAP_RE = re.compile(r'(DN\s*\d{2,3})|(Ø\s*\d{2,3}(?:[.,]\d)?)|(%%[cC]\s*\d{2,3})|(\d(?:\s*\d/\d)?\s*(?:"|”|″))|(\d/\d\s*(?:"|”|″))')
ETIKET_HARIC_BLOK = ('CAP', 'ÇAP', 'KOLON NO', 'NO ', 'DETAY', 'ETIKET', 'ANTET', 'PAFTA', 'KUZEY', 'LOGO', 'KAPAK')
MIMARI = ('MIMARI', 'MİMARİ')


def _u(s):
    return s.upper().replace('İ', 'I').replace('Ş', 'S').replace('Ğ', 'G').replace('Ü', 'U').replace('Ö', 'O').replace('Ç', 'C')


# =====================================================================================  sınır kutuları
def _tek_tek(ents):
    for e in ents:
        try:
            b = _bbox.extents([e], fast=True)
        except Exception:
            continue
        if b.has_data:
            yield e, (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)


def _merkez(b):
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


def _icinde(p, r, tol=0.0):
    return r[0] - tol <= p[0] <= r[2] + tol and r[1] - tol <= p[1] <= r[3] + tol


def _birlesim(bs):
    bs = list(bs)
    if not bs:
        return None
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


# =====================================================================================  1) pafta bulma
def _dikdortgen(e):
    """eksene paralel kapalı dikdörtgen LWPOLYLINE ise (x0,y0,x1,y1)"""
    if e.dxftype() != 'LWPOLYLINE':
        return None
    p = [(v[0], v[1]) for v in e.get_points('xyb')]
    if any(abs(v[2]) > 1e-9 for v in e.get_points('xyb')):
        return None
    if len(p) == 5 and math.dist(p[0], p[4]) < 1e-3:
        p = p[:4]
    if len(p) != 4 or not (e.closed or len(e) == 5):
        return None
    for i in range(4):
        a, b = p[i], p[(i + 1) % 4]
        if abs(a[0] - b[0]) > 1e-3 and abs(a[1] - b[1]) > 1e-3:
            return None
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    return (min(xs), min(ys), max(xs), max(ys))


def _pafta_turu(baslik):
    t = _u(baslik)
    if 'LEJANT' in t or 'ANTET' in t:
        return 'LEJANT'
    if 'DETAY' in t:
        return 'DETAY'
    if 'SEMA' in t or 'KOLON' in t or 'IZOMETRI' in t:
        return 'SEMA'
    if 'YERLESIM' in t or 'VAZIYET' in t:
        return 'YERLESIM'
    if 'PLAN' in t:
        return 'PLAN'
    return 'DIGER'


def paftalari_bul(msp, kutu_listesi=None, min_boyut=500.0):
    """Dönüş: [dict(x0,y0,x1,y1, ic, katman, cerceve=[ent], baslik, baslik_ent, tur)] soldan sağa."""
    kl = kutu_listesi if kutu_listesi is not None else list(_tek_tek(list(msp)))
    adaylar = []
    for e, _ in kl:
        r = _dikdortgen(e)
        if r and r[2] - r[0] >= min_boyut and r[3] - r[1] >= min_boyut:
            adaylar.append((e, r))
    oncelikli = [a for a in adaylar if any(k in _u(a[0].dxf.layer) for k in PAFTA_KATMAN_ANAHTAR)]
    if oncelikli:
        adaylar = oncelikli
    elif adaylar:
        hmax = max(r[3] - r[1] for _, r in adaylar)
        adaylar = [a for a in adaylar if a[1][3] - a[1][1] >= 0.5 * hmax]
    paftalar = []
    for e, r in sorted(adaylar, key=lambda a: -(a[1][2] - a[1][0]) * (a[1][3] - a[1][1])):
        ana = next((p for p in paftalar if r[0] >= p['x0'] - 1 and r[1] >= p['y0'] - 1 and r[2] <= p['x1'] + 1 and r[3] <= p['y1'] + 1), None)
        if ana is None:
            paftalar.append(dict(x0=r[0], y0=r[1], x1=r[2], y1=r[3], ic=None, katman=e.dxf.layer, cerceve=[e]))
        else:
            ofs = (r[0] - ana['x0'], r[1] - ana['y0'], ana['x1'] - r[2], ana['y1'] - r[3])
            if ana['ic'] is None and max(ofs) < 150 and max(ofs) - min(ofs) < 2:
                ana['ic'] = sum(ofs) / 4
                ana['cerceve'].append(e)
    if not paftalar:
        paftalar = _kume_paftalar(kl)
    for p in paftalar:
        if p['ic'] is None:
            p['ic'] = 0.0
    # başlık: çerçeve içinde 'ÖLÇEK' geçen en alttaki yazı
    yazilar = [(e, b) for e, b in kl if e.dxftype() in ('TEXT', 'MTEXT')]
    for p in paftalar:
        r = (p['x0'], p['y0'], p['x1'], p['y1'])
        ic = [(e, b) for e, b in yazilar if _icinde(_merkez(b), r)]
        ol = [(e, b) for e, b in ic if 'OLCEK' in _u(_metin_al(e))]
        sec = min(ol, key=lambda a: a[1][1]) if ol else None
        p['baslik'] = _metin_al(sec[0]) if sec else ''
        p['baslik_ent'] = sec[0] if sec else None
        p['tur'] = _pafta_turu(p['baslik'])
    paftalar.sort(key=lambda p: (round(-p['y1'] / 1000.0), p['x0']))
    return paftalar


def _kume_paftalar(kl, esik=300.0):
    """Çerçeve yoksa: sınır kutularını esik mesafesiyle birleştirerek grup bul."""
    gruplar = []
    for _, b in sorted(kl, key=lambda a: a[1][0]):
        g = (b[0] - esik, b[1] - esik, b[2] + esik, b[3] + esik)
        birles = [x for x in gruplar if not (g[2] < x[0] or g[0] > x[2] or g[3] < x[1] or g[1] > x[3])]
        for x in birles:
            gruplar.remove(x)
        gruplar.append(_birlesim(birles + [g]))
    return [dict(x0=g[0] + esik, y0=g[1] + esik, x1=g[2] - esik, y1=g[3] - esik, ic=0.0, katman='ROTAS-PAFTA', cerceve=[]) for g in gruplar]


def _metin_al(e):
    if e is None:
        return ''
    if e.dxftype() == 'MTEXT':
        return e.plain_text()
    return e.dxf.text


def _icerik_kutusu(p, kl):
    r = (p['x0'], p['y0'], p['x1'], p['y1'])
    cer = set(id(e) for e in p['cerceve'])
    bs = [b for e, b in kl if id(e) not in cer and e.dxf.layer != p['katman'] and _icinde(_merkez(b), r)]
    return _birlesim(bs)


def anormal_cerceve_duzelt(msp, paftalar, kl, duzelt=True):
    """Genişliği medyanın 4 katını aşan ve içeriğinin yarısından fazlası boş olan çerçeveyi bulur;
    duzelt=True ise sağ kenarı içerik + boşluğa çeker (çerçeve çizgileri ve sağdaki başlık yazısı ötelenir)."""
    rapor = []
    if len(paftalar) < 2:
        return rapor
    gs = sorted(p['x1'] - p['x0'] for p in paftalar)
    med = gs[len(gs) // 2]
    for p in paftalar:
        w = p['x1'] - p['x0']
        ick = _icerik_kutusu(p, kl)
        if ick is None or w <= 4 * med or (ick[2] - ick[0]) > 0.5 * w:
            continue
        yeni_x1 = max(ick[2] + KENAR + p['ic'], p['x0'] + med)
        dx = yeni_x1 - p['x1']
        satir = 'Anormal çerçeve: "%s" genişliği %.0f (medyan %.0f), içerik %.0f..%.0f' % (p['baslik'] or '?', w, med, ick[0], ick[2])
        if not duzelt:
            rapor.append(satir + ' — düzeltilmedi')
            continue
        esik = ick[2] + 1.0
        r = (p['x0'] - 10, p['y0'] - 10, p['x1'] + 10, p['y1'] + 10)      # çizgi kalınlığı payı
        n = 0
        for e, b in kl:
            if e.dxf.layer != p['katman'] or not (_icinde((b[0], b[1]), r) and _icinde((b[2], b[3]), r)):
                continue
            if b[0] > esik:                              # tamamen sağda (başlık yazısı vb.)
                e.translate(dx, 0, 0)
                n += 1
            elif e.dxftype() == 'LWPOLYLINE' and b[2] > esik:
                pts = [(x + dx if x > esik else x, y, s, en, bu) for x, y, s, en, bu in e.get_points('xyseb')]
                e.set_points(pts, format='xyseb')
                n += 1
            elif e.dxftype() == 'LINE' and b[2] > esik:
                for a in ('start', 'end'):
                    q = e.dxf.get(a)
                    if q.x > esik:
                        e.dxf.set(a, (q.x + dx, q.y, q.z))
                n += 1
        p['x1'] = yeni_x1
        rapor.append(satir + ' — sağ kenar %.0f birim içeri çekildi (%d çerçeve/başlık nesnesi)' % (-dx, n))
    return rapor


# =====================================================================================  2) lejant + adet
def _kullanim_say(doc, ents, ornek):
    """semboller2.kullanim_say'ın seçili INSERT listesi üzerinde çalışan hali: {(grup, blok): adet}. Grup INSERT
    katmanından (iç içe kullanıcı bloklarında en dıştaki anlamlı katman), bulunamazsa sembolün kendi grubundan."""
    say = {}

    def tara(liste, derin, dis):
        for e in liste:
            if e.dxftype() != 'INSERT' or e.dxf.layer.startswith('ROTAS-LEJANT'):
                continue
            n = e.dxf.name
            g = dis or S.katman_grubu(e.dxf.layer)
            if n in S.SEMBOL:
                k = (g or S.SEMBOL[n]['grup'], n)
                say[k] = say.get(k, 0) + 1
                ornek.setdefault(k, n)
            elif derin < 8 and n in doc.blocks and not n.startswith('*'):
                tara(doc.blocks.get(n), derin + 1, g)
    tara(ents, 0, None)
    return say


def sembol_sayimi(doc, paftalar, kl):
    """Pafta türü (PLAN / SEMA / DIGER) başına sayar; adet = türler arasındaki EN BÜYÜK sayı
    (aynı vana planda ve şemada iki kez gösterilir, toplanmaz). Lejant/detay/yerleşim paftaları sayılmaz.
    Dönüş: {(grup, sembol): adet}, {(grup, sembol): blok}, {tür: {(grup,sembol): adet}}"""
    turler = defaultdict(list)
    for e, b in kl:
        if e.dxftype() != 'INSERT':
            continue
        c = _merkez(b)
        p = next((p for p in paftalar if _icinde(c, (p['x0'], p['y0'], p['x1'], p['y1']))), None)
        t = p['tur'] if p else 'DIGER'
        if t in ('LEJANT', 'DETAY', 'YERLESIM'):
            continue
        turler[t].append(e)
    tur_sayim, ornek = {}, {}
    for t, ents in turler.items():
        tur_sayim[t] = _kullanim_say(doc, ents, ornek)
    son = {}
    for t, sg in tur_sayim.items():
        for k, v in sg.items():
            son[k] = max(son.get(k, 0), v)
    return son, ornek, tur_sayim


def diger_bloklar(doc, paftalar, kl):
    """Kütüphanede karşılığı olmayan, etiket olmayan ve içinde kütüphane sembolü barındırmayan blokların adedi (max kuralı)."""
    harita = set(S.SEMBOL)

    def kutuphaneli(n, d=0):
        if n in harita:
            return True
        if d > 6 or n not in doc.blocks:
            return False
        return any(c.dxftype() == 'INSERT' and kutuphaneli(c.dxf.name, d + 1) for c in doc.blocks.get(n))

    tur = defaultdict(lambda: defaultdict(int))
    for e, b in kl:
        if e.dxftype() != 'INSERT':
            continue
        n = e.dxf.name
        if n.startswith('*') or n.startswith('ROTAS-LJ-') or e.dxf.layer.startswith('ROTAS-LEJANT') or kutuphaneli(n):
            continue
        if any(k in _u(n) + ' ' for k in map(_u, ETIKET_HARIC_BLOK)):
            continue
        p = next((p for p in paftalar if _icinde(_merkez(b), (p['x0'], p['y0'], p['x1'], p['y1']))), None)
        t = p['tur'] if p else 'DIGER'
        if t in ('LEJANT', 'DETAY', 'YERLESIM'):
            continue
        tur[t][n] += 1
    son = {}
    for t, d in tur.items():
        for n, v in d.items():
            son[n] = max(son.get(n, 0), v)
    return son


def lejant_ciz(msp, x, y, sayim, ornek, diger):
    """Grup tablolarını x,y (sol üst) noktasından sağa doğru çizer (semboller2 lejant_tablosu).
    Dönüş: (genişlik, yükseklik, tablo sayısı)."""
    doc = msp.doc
    S.katmanlar(doc)
    S.ekle(doc, sorted({a for (_, a) in sayim}))          # tanım zaten var: yalnız kapsam hesaplanır
    cx, hmax, n = x, 0.0, 0
    not_ortak = 'Adet: plan ve şema paftalarındaki sayımların büyüğü (aynı eleman iki yerde gösterildiği için toplanmaz).'
    for g, (baslik, kat, _) in S.GRUP.items():
        ads = [ad for (gg, ad) in sayim if gg == g]
        if not ads:
            continue
        ads.sort(key=lambda a: list(S.SEMBOL).index(a))
        satir = [dict(ad=a, aciklama=S.SEMBOL[a]['aciklama'], adet=sayim[(g, a)], celiski=S.SEMBOL[a]['celiski'],
                      katman=S.LEJ_SEM) for a in ads]
        top = sum(sayim[(g, a)] for a in ads)
        w, h = S.lejant_tablosu(msp, cx, y, 'LEJANT VE ADET — ' + baslik, satir)
        notlar = ['Toplam sembol adedi: %d.' % top, not_ortak] + \
            ['(*) ' + c for c in sorted({S.SEMBOL[a]['celiski'] for a in ads} - {None})]
        yy = y - h - 14
        for t in notlar:
            for parca in _sar(t, 80):
                S._metin(msp, parca, (cx, yy), 7, S.LEJ_YAZ, TA.MIDDLE_LEFT)
                yy -= 11
        cx += w + 60
        hmax = max(hmax, y - yy)
        n += 1
    if diger:
        w, h = _diger_tablo(msp, cx, y, diger, not_ortak)
        cx += w + 60
        hmax = max(hmax, h)
        n += 1
    return cx - x - (60 if n else 0), hmax, n


def _diger_tablo(msp, x0, y0, diger, not_ortak, SG=70.0, W_A=400.0, W_N=60.0, RH=34.0):
    """Kütüphane dışı bloklar: SEMBOL (bloğun kendisi, hücreye sığdırılmış) | AÇIKLAMA | ADET"""
    W = SG + W_A + W_N
    y = y0
    S._kutu(msp, x0, y - 40, x0 + W, y)
    S._metin(msp, 'DİĞER BLOKLAR (KÜTÜPHANE DIŞI) — ADET', (x0 + W / 2, y - 20), 16, S.LEJ_BAS, TA.MIDDLE_CENTER, 0.9)
    y -= 40
    for bn, v in sorted(diger.items()):
        S._kutu(msp, x0, y - RH, x0 + W, y)
        for xx in (SG, SG + W_A):
            msp.add_line((x0 + xx, y), (x0 + xx, y - RH), dxfattribs={'layer': S.LEJ_CER})
        cy = y - RH / 2
        ents = [e for e in msp.doc.blocks.get(bn) if e.dxftype() != 'ATTDEF'] if bn in msp.doc.blocks else []
        bb = _bbox.extents(ents, fast=True) if ents else None
        if bb is not None and bb.has_data and max(bb.size.x, bb.size.y) > 1e-6:
            k = min(SG * 0.8 / max(bb.size.x, 1e-6), RH * 0.8 / max(bb.size.y, 1e-6), 3.0)
            msp.add_blockref(bn, (x0 + SG / 2 - bb.center.x * k, cy - bb.center.y * k),
                             dxfattribs={'layer': S.LEJ_SEM, 'xscale': k, 'yscale': k})
        S._metin(msp, _insan_adi(bn), (x0 + SG + 8, cy), 9, S.LEJ_YAZ, TA.MIDDLE_LEFT)
        S._metin(msp, str(v), (x0 + SG + W_A + W_N / 2, cy), 10, S.LEJ_YAZ, TA.MIDDLE_CENTER)
        y -= RH
    yy = y - 14
    for t in ('Açıklama blok adından üretildi; kullanıcı teyit edecek.', not_ortak):
        S._metin(msp, t, (x0, yy), 7, S.LEJ_YAZ, TA.MIDDLE_LEFT)
        yy -= 11
    return W, y0 - yy


def _insan_adi(bn):
    s = re.sub(r'^(MTY|ROTAS)-', '', bn).replace('-', ' ')
    s = re.sub(r'(\D)1( |$)', r'\1\2', s)
    return s.replace('_', ' ').strip().upper()


# =====================================================================================  2b) boru metrajı
def _boru_katmani(lay, ek_anahtar=()):
    u = _u(lay)
    if not (any(k in u for k in BORU_ANAHTAR) or any(k in u for k in ek_anahtar)):
        return False
    parcalar = set(re.split(r'[-_ ]', u))
    return not any(h in parcalar or (len(h) > 3 and h in u) for h in BORU_HARIC)


def _boru_bilgi(lay):
    u = _u(lay)
    for k, aile, ac in BORU_ACIKLAMA:
        if k in u:
            return aile, ac
    return None, lay


def _parcalar(e):
    """[(p0, p1, uzunluk)] düz ya da yay parça"""
    t = e.dxftype()
    out = []
    if t == 'LINE':
        a, b = e.dxf.start, e.dxf.end
        out.append(((a.x, a.y), (b.x, b.y), math.dist((a.x, a.y), (b.x, b.y))))
    elif t == 'LWPOLYLINE':
        pts = list(e.get_points('xyb'))
        if e.closed and pts:
            pts.append(pts[0])
        for (x0, y0, bu), (x1, y1, _) in zip(pts, pts[1:]):
            c = math.dist((x0, y0), (x1, y1))
            if abs(bu) > 1e-9 and c > 0:
                th = 4 * math.atan(abs(bu))
                L = c / (2 * math.sin(th / 2)) * th
            else:
                L = c
            if L > 1e-6:
                out.append(((x0, y0), (x1, y1), L))
    elif t == 'POLYLINE' and not e.is_3d_polyline and not e.is_poly_face_mesh and not e.is_polygon_mesh:
        pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        if e.is_closed and pts:
            pts.append(pts[0])
        for a, b in zip(pts, pts[1:]):
            if math.dist(a, b) > 1e-6:
                out.append((a, b, math.dist(a, b)))
    elif t == 'ARC':
        a0, a1 = e.dxf.start_angle, e.dxf.end_angle
        d = (a1 - a0) % 360 or 360
        out.append(((e.start_point.x, e.start_point.y), (e.end_point.x, e.end_point.y), math.radians(d) * e.dxf.radius))
    return out


def _paralel(a, b, tol=0.15):
    ax, ay = a[2][0] - a[1][0], a[2][1] - a[1][1]
    bx, by = b[2][0] - b[1][0], b[2][1] - b[1][1]
    la, lb = math.hypot(ax, ay), math.hypot(bx, by)
    return la > 0 and lb > 0 and abs(ax * by - ay * bx) / (la * lb) < tol


def _cap_normal(s):
    s = s.replace('%%c', 'Ø').replace('%%C', 'Ø').replace('”', '"').replace('″', '"')
    s = re.sub(r'\s+', '', s)
    return s


def _cap_sira(c):
    m = re.search(r'(\d+(?:[.,]\d)?)', c)
    if not m:
        return 9999
    v = float(m.group(1).replace(',', '.'))
    if '"' in c:
        fr = re.search(r'(\d)/(\d)', c)
        v = (v if not fr or c.index(fr.group(0)) > 0 else 0) + (int(fr.group(1)) / int(fr.group(2)) if fr else 0)
        v *= 25.4
    return v


def _etiketler(kl, alan):
    """Çap etiketleri: [(nokta listesi, çap, aile, yazı boyu)] — TEXT/MTEXT ve INSERT öznitelikleri."""
    out = []
    for e, b in kl:
        if not any(_icinde(_merkez(b), r) for r in alan):
            continue
        t = e.dxftype()
        if t in ('TEXT', 'MTEXT'):
            s = _metin_al(e)
            m = CAP_RE.search(s)
            if not m:
                continue
            h = e.dxf.height if t == 'TEXT' else e.dxf.char_height
            aile = 'PIS' if 'SB' in _u(s) else None
            out.append(([_merkez(b)], _cap_normal(m.group(0)), aile or _boru_bilgi(e.dxf.layer)[0], h))
        elif t == 'INSERT' and e.attribs:
            bu = _u(e.dxf.name)
            for a in e.attribs:
                s = a.dxf.text or ''
                m = CAP_RE.search(s)
                if not m:
                    continue
                tag = _u(a.dxf.tag)
                if tag.startswith('SO'):
                    aile = 'SOGUK'
                elif tag.startswith('SC'):
                    aile = 'SICAK'
                elif tag.startswith('PS') or 'PIS' in bu:
                    aile = 'PIS'
                else:
                    aile = _boru_bilgi(e.dxf.name)[0] or _boru_bilgi(e.dxf.layer)[0]
                p = a.dxf.insert
                out.append(([(e.dxf.insert.x, e.dxf.insert.y), (p.x, p.y)], _cap_normal(m.group(0)), aile, a.dxf.height))
    return out


def boru_metraji(msp, paftalar, kl, birim=0.01, turler=('PLAN',), ek_anahtar=()):
    """Plan paftalarındaki boru katmanlarının çap bazında uzunluğu.
    Çap: her etiket en yakın uyumlu boru parçasına bağlanır (<= max(30, 2.5 h)); etiketsiz parçalar aynı katmandaki
    bağlantılı parçalardan (uç uca ya da T bağlantı) en az adımla ulaşılan etiketin çapını alır.
    Dönüş: {katman: {çap: uzunluk_m}}, kullanılan pafta başlıkları."""
    alan = [(p['x0'], p['y0'], p['x1'], p['y1']) for p in paftalar if p['tur'] in turler]
    basliklar = [p['baslik'] for p in paftalar if p['tur'] in turler]
    seg = []          # (katman, p0, p1, L)
    for e, b in kl:
        if not _boru_katmani(e.dxf.layer, ek_anahtar) or not any(_icinde(_merkez(b), r) for r in alan):
            continue
        onceki = None
        for p0, p1, L in _parcalar(e):
            seg.append([e.dxf.layer, p0, p1, L, onceki])
            onceki = len(seg) - 1
    if not seg:
        return {}, basliklar
    geo = [LineString([s[1], s[2]]) if math.dist(s[1], s[2]) > 1e-6 else Point(s[1]).buffer(0.01) for s in seg]
    agac = STRtree(geo)
    # komşuluk (aynı katman)
    kom = defaultdict(set)
    for i, s in enumerate(seg):
        if s[4] is not None:
            kom[i].add(s[4]); kom[s[4]].add(i)
        for uc in (s[1], s[2]):
            for j in agac.query(Point(uc).buffer(1.0)):
                j = int(j)
                if j != i and seg[j][0] == s[0] and geo[j].distance(Point(uc)) <= 1.0:
                    kom[i].add(j); kom[j].add(i)
    # etiketleri bağla
    cap = {}
    for noktalar, c, aile, h in _etiketler(kl, alan):
        esik = max(30.0, 2.5 * (h or 10))
        en = None
        for q in noktalar:
            P = Point(q)
            for j in agac.query(P.buffer(esik)):
                j = int(j)
                pa = _boru_bilgi(seg[j][0])[0]
                if aile and pa and aile != pa and not ({aile, pa} <= {'SOGUK', 'SICAK'} and False):
                    continue
                d = geo[j].distance(P)
                if d <= esik and (en is None or d < en[0]):
                    en = (d, j)
        if en and (en[1] not in cap or cap[en[1]][1] > en[0]):
            cap[en[1]] = (c, en[0])
    # yayılım (çok kaynaklı BFS)
    son = {i: v[0] for i, v in cap.items()}
    kuy = deque(son)
    while kuy:
        i = kuy.popleft()
        for j in kom[i]:
            if j not in son:
                son[j] = son[i]
                kuy.append(j)
    # sıcak su etiketsizse (MTY etiketinde sıcak çap boş): daire içinde soğuk suya paralel gider kuralıyla
    # en yakın (<= 40) paralel soğuk su parçasının çapı alınır, "(s)" ile işaretlenir
    for i, s in enumerate(seg):
        if i in son or _boru_bilgi(s[0])[0] != 'SICAK':
            continue
        orta = Point((s[1][0] + s[2][0]) / 2, (s[1][1] + s[2][1]) / 2)
        en = None
        for j in agac.query(orta.buffer(40.0)):
            j = int(j)
            if j in son and _boru_bilgi(seg[j][0])[0] == 'SOGUK' and not son[j].endswith('(s)'):
                dd = geo[j].distance(orta)
                if dd <= 40.0 and _paralel(s, seg[j]) and (en is None or dd < en[0]):
                    en = (dd, j)
        if en:
            son[i] = son[en[1]] + ' (s)'
    kuy = deque(i for i in son if son[i].endswith('(s)'))
    while kuy:
        i = kuy.popleft()
        for j in kom[i]:
            if j not in son:
                son[j] = son[i]
                kuy.append(j)
    tab = defaultdict(lambda: defaultdict(float))
    for i, s in enumerate(seg):
        tab[s[0]][son.get(i, 'BELİRSİZ')] += s[3] * birim
    return {k: dict(v) for k, v in tab.items()}, basliklar


def metraj_ciz(msp, x0, y0, tablo, basliklar, birim_ad='m'):
    """Lejant tarzında BORU METRAJI tablosu (sol üst x0,y0). Dönüş: (genişlik, yükseklik)."""
    doc = msp.doc
    S.katmanlar(doc)
    W_S, W_A, W_C, W_L = 150.0, 340.0, 110.0, 130.0
    W = W_S + W_A + W_C + W_L
    PAD = 10.0
    y = y0
    S._kutu(msp, x0, y - 70, x0 + W + 2 * PAD, y)
    S._kutu(msp, x0 + PAD, y - 60, x0 + W + PAD, y - 10)
    S._metin(msp, 'BORU METRAJI (KATMAN / ÇAP)', (x0 + PAD + W / 2, y - 35), 18, S.LEJ_BAS, TA.MIDDLE_CENTER, 0.9)
    y -= 80
    ytab0 = y
    xs = x0 + PAD
    y -= PAD
    cols = [('BORU', W_S), ('AÇIKLAMA', W_A), ('ÇAP', W_C), ('UZUNLUK (%s)' % birim_ad, W_L)]
    cx = xs
    for ad, w in cols:
        S._kutu(msp, cx, y - 30, cx + w, y)
        S._metin(msp, ad, (cx + w / 2, y - 15), 11, S.LEJ_YAZ, TA.MIDDLE_CENTER)
        cx += w
    y -= 30
    rh = 34.0
    genel = 0.0
    sira = sorted(tablo, key=lambda k: [i for i, (a, _, _) in enumerate(BORU_ACIKLAMA) if a in _u(k)][:1] or [99])
    for lay in sira:
        caplar = sorted(tablo[lay], key=_cap_sira)
        aile, ac = _boru_bilgi(lay)
        n = len(caplar) + (1 if len(caplar) > 1 else 0)
        rh = 34.0 if n > 1 else 50.0          # tek satırda iki satırlık açıklama sığsın
        # boru örnek hücresi (katman grubunun tamamı)
        S._kutu(msp, xs, y - n * rh, xs + W_S, y)
        ln = msp.add_line((xs + 15, y - n * rh / 2), (xs + W_S - 15, y - n * rh / 2), dxfattribs={'layer': lay})
        ln.dxf.ltscale = 12.0
        S._kutu(msp, xs + W_S, y - n * rh, xs + W_S + W_A, y)
        S._metin(msp, ac, (xs + W_S + 10, y - n * rh / 2 + 7), 11, S.LEJ_YAZ)
        S._metin(msp, '(' + lay + ')', (xs + W_S + 10, y - n * rh / 2 - 9), 8, S.LEJ_YAZ, TA.MIDDLE_LEFT, 0.75)
        top = 0.0
        for c in caplar:
            v = tablo[lay][c]
            top += v
            for (a, w), xx in ((cols[2], xs + W_S + W_A), (cols[3], xs + W_S + W_A + W_C)):
                S._kutu(msp, xx, y - rh, xx + w, y)
            S._metin(msp, c, (xs + W_S + W_A + W_C / 2, y - rh / 2), 11, S.LEJ_YAZ, TA.MIDDLE_CENTER)
            S._metin(msp, '%.1f' % v, (xs + W_S + W_A + W_C + W_L - 10, y - rh / 2), 11, S.LEJ_YAZ, TA.MIDDLE_RIGHT)
            y -= rh
        if len(caplar) > 1:
            for (a, w), xx in ((cols[2], xs + W_S + W_A), (cols[3], xs + W_S + W_A + W_C)):
                S._kutu(msp, xx, y - rh, xx + w, y)
            S._metin(msp, 'TOPLAM', (xs + W_S + W_A + W_C / 2, y - rh / 2), 10, S.LEJ_BAS, TA.MIDDLE_CENTER)
            S._metin(msp, '%.1f' % top, (xs + W_S + W_A + W_C + W_L - 10, y - rh / 2), 11, S.LEJ_BAS, TA.MIDDLE_RIGHT)
            y -= rh
        genel += top
    notlar = ['Ölçüm yalnız kat planı paftalarından: ' + '; '.join(b.split('ÖLÇEK')[0].strip() for b in basliklar) + '.',
              'Dikey kolon (iniş/çıkış) boyları ve fire payı dahil DEĞİLDİR.',
              'Çap, en yakın DN / Ø / inç etiketinden ve bağlantılı parçalara yayılımla bulunmuştur;',
              '"(s)": sıcak su etiketi boş; paralel soğuk su borusunun çapı alındı (teyit edilecek).',
              '"BELİRSİZ": etiketine bağlanamayan parça.']
    y -= 8
    for s in notlar:
        for parca in _sar(s, 95):
            S._metin(msp, parca, (xs, y - 6), 9, S.LEJ_YAZ, TA.MIDDLE_LEFT, 0.8)
            y -= 14
    y -= PAD
    S._kutu(msp, x0, y, x0 + W + 2 * PAD, ytab0)
    return W + 2 * PAD, y0 - y


def _sar(s, n):
    out, cur = [], ''
    for w in s.split(' '):
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur)
            cur = '   ' + w
        else:
            cur = (cur + ' ' + w).strip(' ') if cur else w
    if cur:
        out.append(cur)
    return out


# =====================================================================================  pafta çerçevesi üretimi
def _pafta_ciz(msp, x0, y0, x1, y1, ref, baslik):
    """ref paftanın tarzıyla (katman, iç çerçeve ofseti, başlık yazısı stili) yeni çerçeve + başlık"""
    lay = ref['katman'] if ref else 'ROTAS-PAFTA'
    if lay not in msp.doc.layers:
        msp.doc.layers.add(lay, color=7)
    ic = ref['ic'] if ref and ref['ic'] else 26.0
    kalip = [e for e in (ref['cerceve'] if ref else []) if e.dxftype() == 'LWPOLYLINE'][:2]
    for k, o in enumerate((0.0, ic)):
        pts = [(x0 + o, y0 + o), (x1 - o, y0 + o), (x1 - o, y1 - o), (x0 + o, y1 - o)]
        if k < len(kalip):              # referans çerçevenin kalınlığı/rengi aynen
            e = kalip[k].copy()
            e.set_points(pts, format='xy')
            e.closed = True
            msp.add_entity(e)
        else:
            msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': lay})
    be = ref.get('baslik_ent') if ref else None
    if be is not None and be.dxftype() == 'TEXT':
        t = be.copy()
        msp.add_entity(t)
        bb = _bbox.extents([be], fast=True)
        t.dxf.text = baslik
        dx, dy = x1 - ref['x1'], y0 - ref['y0']
        t.translate(dx, dy, 0)
        yeni = _bbox.extents([t], fast=True)
        if yeni.has_data:      # sağ kenar referans başlıkla aynı hizada kalsın
            t.translate((bb.extmax.x + dx) - yeni.extmax.x, 0, 0)
    else:
        t = msp.add_text(baslik, height=18, dxfattribs={'layer': lay, 'style': S.STIL})
        t.set_placement((x1 - ic - 20, y0 + ic + 20), align=TA.BOTTOM_RIGHT)
    return ic


# =====================================================================================  3) ek DXF yerleştirme
def _blok_imza(doc, ad):
    blk = doc.blocks.get(ad)
    sayac = defaultdict(int)
    for e in blk:
        sayac[(e.dxftype(), e.dxf.get('layer', ''))] += 1
    try:
        b = _bbox.extents(blk, fast=True)
        k = tuple(round(v, 1) for v in (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)) if b.has_data else ()
    except Exception:
        k = ()
    return tuple(sorted(sayac.items())), k


def _katman_cevir(doc, harita):
    """harita {eski_önek: yeni_önek}: katman tablosu + model uzayı / blok içi nesneler (öznitelikler dahil).
    Dönüş: {eski: yeni}"""
    def yeni_ad(n):
        for a, b in harita.items():
            if n.upper().startswith(a.upper()):
                return b + n[len(a):]
        return None
    ceviri = {l.dxf.name: yeni_ad(l.dxf.name) for l in doc.layers if yeni_ad(l.dxf.name)}
    for eski, yeni in ceviri.items():
        src = doc.layers.get(eski)
        if yeni not in doc.layers:
            doc.layers.add(yeni, color=src.dxf.color, linetype=src.dxf.linetype)
    for lay in [doc.modelspace()] + [b for b in doc.blocks if not b.block_record.is_any_layout]:
        for e in lay:
            if e.dxf.get('layer', '0') in ceviri:
                e.dxf.layer = ceviri[e.dxf.layer]
            if e.dxftype() == 'INSERT':
                for a in e.attribs:
                    if a.dxf.layer in ceviri:
                        a.dxf.layer = ceviri[a.dxf.layer]
    for eski in ceviri:
        doc.layers.remove(eski)
    return ceviri


def _metin_cevir(doc, harita):
    n = 0
    for e in doc.modelspace():
        t = e.dxftype()
        if t == 'TEXT':
            yeni = e.dxf.text
            for a, b in harita.items():
                yeni = yeni.replace(a, b)
            if yeni != e.dxf.text:
                e.dxf.text = yeni
                n += 1
        elif t == 'MTEXT':
            yeni = e.text
            for a, b in harita.items():
                yeni = yeni.replace(a, b)
            if yeni != e.text:
                e.text = yeni
                n += 1
    return n


def yazi_sigdir(msp, ents=None, min_w=0.5, bosluk=1.0):
    """Birbirine taşan TEXT çiftlerinde (MİMARİ hariç) taşan yazının genişlik çarpanını, komşusuna `bosluk` kalacak
    kadar daraltır (hizalama noktası / yazı boyu değişmez). Dönüş: [(yazı, eski_w, yeni_w)]"""
    ents = list(msp) if ents is None else ents
    out = []
    for _ in range(6):
        ys = []
        for e in ents:
            if e.dxftype() == 'TEXT' and (e.dxf.text or '').strip() and not any(k in _u(e.dxf.layer) for k in MIMARI):
                try:
                    v = [(p.x, p.y) for p in disassemble.make_primitive(e).vertices()]
                    pg = Polygon(v)
                except Exception:
                    continue
                if pg.is_valid and pg.area > 0:
                    ys.append((e, pg))
        if len(ys) < 2:
            break
        agac = STRtree([y[1] for y in ys])
        degisen = 0
        for i, (e, pg) in enumerate(ys):
            for j in agac.query(pg):
                j = int(j)
                if j <= i:
                    continue
                f, pf = ys[j]
                if pg.intersection(pf).area <= 0.02 * min(pg.area, pf.area):
                    continue
                # soldaki yazı daraltılır (yatay yazılar); taşma = soldakinin sağ ucu - sağdakinin sol ucu
                sol, ps, sag, pd = (e, pg, f, pf) if pg.bounds[0] <= pf.bounds[0] else (f, pf, e, pg)
                gen = ps.bounds[2] - ps.bounds[0]
                hedef = pd.bounds[0] - bosluk - ps.bounds[0]
                if gen <= 0 or hedef <= 0:
                    continue
                w0 = sol.dxf.get('width', 1.0) or 1.0
                w1 = max(min_w, w0 * hedef / gen * 0.98)
                if w1 < w0 - 1e-3:
                    sol.dxf.width = round(w1, 3)
                    out.append((sol.dxf.text[:30], w0, sol.dxf.width))
                    degisen += 1
        if not degisen:
            break
    return out


def ek_ice_al(hedef, kaynak_yol, etiket, katman_cevir=None, metin_cevir=None, sigdir=False):
    """kaynak DXF model uzayını hedefe alır. Dönüş: (yeni nesneler, rapor satırları).
    Katman/stil adları korunur (aynı adlı katman varsa hedefteki tanım kalır) — katman_cevir {eski_önek: yeni_önek}
    verilirse önce kaynakta çevrilir (ör. MTY-HESAP → ROTAS-HESAP); metin_cevir {eski: yeni} yazılarda değiştirilir;
    sigdir=True ise ekin kendi içinde taşan yazıları daraltılır (yazi_sigdir). Aynı adlı blok içerikçe aynıysa
    paylaşılır, farklıysa '<ad>-<etiket>' olarak yeniden adlandırılır; anonim bloklar yeni anonim blok olur."""
    kay = ezdxf.readfile(kaynak_yol)
    rapor = []
    if katman_cevir:
        c = _katman_cevir(kay, katman_cevir)
        if c:
            rapor.append('%s: katman çevirisi %s' % (etiket, ', '.join('%s→%s' % kv for kv in sorted(c.items()))))
    if metin_cevir:
        n = _metin_cevir(kay, metin_cevir)
        if n:
            rapor.append('%s: %d yazıda metin çevirisi %s' % (etiket, n, metin_cevir))
    if sigdir:
        sg = yazi_sigdir(kay.modelspace())
        if sg:
            rapor.append('%s: taşan %d yazı daraltıldı (genişlik çarpanı): %s' % (
                etiket, len(sg), '; '.join('"%s" %.2f→%.2f' % x for x in sg)))
    imp = Importer(kay, hedef)
    yeniden = []
    for blk in kay.blocks:
        ad = blk.name
        if blk.block_record.is_any_layout:
            continue
        if ad.startswith('*'):
            yeni = hedef.blocks.new_anonymous_block(type_char=ad[1] if len(ad) > 1 and ad[1].isalpha() else 'U',
                                                    base_point=blk.block.dxf.base_point)
            imp.import_entities(blk, target_layout=yeni)
            imp.imported_blocks[ad] = yeni.name
            continue
        if ad in hedef.blocks:
            if _blok_imza(kay, ad) == _blok_imza(hedef, ad):
                imp.imported_blocks[ad] = ad
                continue
            n, yad = 1, '%s-%s' % (ad, etiket)
            while yad in hedef.blocks:
                n += 1
                yad = '%s-%s%d' % (ad, etiket, n)
            yeni = hedef.blocks.new(yad, base_point=blk.block.dxf.base_point)
            imp.import_entities(blk, target_layout=yeni)
            imp.imported_blocks[ad] = yad
            yeniden.append((ad, yad))
        else:
            yeni = hedef.blocks.new(ad, base_point=blk.block.dxf.base_point,
                                    dxfattribs={'flags': blk.block.dxf.flags, 'description': blk.block.dxf.description})
            imp.import_entities(blk, target_layout=yeni)
            imp.imported_blocks[ad] = ad
    onceki = set(e.dxf.handle for e in hedef.modelspace())
    var_katman = set(l.dxf.name.upper() for l in hedef.layers)
    imp.import_modelspace()
    imp.finalize()
    yeni_ents = [e for e in hedef.modelspace() if e.dxf.handle not in onceki]
    kat = sorted(set(e.dxf.layer for e in yeni_ents))
    ortak = [k for k in kat if k.upper() in var_katman]
    if yeniden:
        rapor.append('%s: farklı içerikli aynı adlı bloklar yeniden adlandırıldı: %s' % (etiket, ', '.join('%s→%s' % r for r in yeniden)))
    if ortak:
        rapor.append('%s: hedefte zaten olan katmanlar (hedef tanımı korundu): %s' % (etiket, ', '.join(ortak)))
    return yeni_ents, rapor


def ekleri_yerlestir(doc, ekler, paftalar, sinir, ref):
    """Ekleri paftaların SOL ALT köşesine: alt kenarlar paftaların alt kenarıyla hizalı, soldan sağa verilen sırada,
    son ek ilk paftaya ARALIK kadar yakın; her ek kendi çerçevesi ve başlığıyla. Dönüş: (yerleşim listesi, rapor)."""
    msp = doc.modelspace()
    rapor = []
    H_ref = (ref['y1'] - ref['y0']) if ref else 2800.0
    ic = ref['ic'] if ref and ref['ic'] else 26.0
    hazir = []
    for i, ek in enumerate(ekler):
        if isinstance(ek, str):
            ek = dict(yol=ek)
        yol = ek['yol']
        etiket = ek.get('etiket') or 'EK%d' % (i + 1)
        baslik = ek.get('baslik') or os.path.splitext(os.path.basename(yol))[0].replace('_', ' ')
        ents, r = ek_ice_al(doc, yol, etiket, ek.get('katman_cevir'), ek.get('metin_cevir'), ek.get('yazi_sigdir', False))
        rapor += r
        kl = list(_tek_tek(ents))
        bb = _birlesim(b for _, b in kl)
        if bb is None:
            rapor.append('%s: boş, atlandı' % yol)
            for e in ents:
                msp.delete_entity(e)
            continue
        w = (bb[2] - bb[0]) + 2 * (ic + KENAR)
        h = (bb[3] - bb[1]) + 2 * (ic + KENAR) + BASLIK_BANT
        hazir.append(dict(ents=ents, bb=bb, w=w, h=max(h, H_ref), baslik=baslik, yol=yol))
    x = sinir[0] - ARALIK - sum(h['w'] for h in hazir) - ARALIK * (len(hazir) - 1)
    y0 = sinir[1]
    yer = []
    for h in hazir:
        dx = x + ic + KENAR - h['bb'][0]
        dy = y0 + ic + KENAR + BASLIK_BANT - h['bb'][1]
        for e in h['ents']:
            try:
                e.translate(dx, dy, 0)
            except Exception:
                rapor.append('%s: %s ötelenemedi, silindi' % (h['yol'], e.dxftype()))
                msp.delete_entity(e)
        _pafta_ciz(msp, x, y0, x + h['w'], y0 + h['h'], ref, h['baslik'].upper() + '   ÖLÇEK : ÖLÇEKSİZ')
        if h['h'] > H_ref + 1:
            rapor.append('%s: ek pafta yüksekliğinden büyük (%.0f > %.0f), çerçevesi yukarı uzatıldı' % (h['baslik'], h['h'], H_ref))
        yer.append(dict(baslik=h['baslik'], x0=x, y0=y0, x1=x + h['w'], y1=y0 + h['h'], nesne=len(h['ents'])))
        x += h['w'] + ARALIK
    return yer, rapor


# =====================================================================================  4) kontroller
def katman_kontrol(doc):
    """Dönüş: (hatalı üst seviye katmanlar {katman: adet}, yalnız blok içi ROTAS dışı katmanlar)"""
    ust = defaultdict(int)
    for lay in [doc.modelspace()] + [doc.paperspace(n) for n in doc.layout_names() if n != 'Model']:
        for e in lay:
            ust[e.dxf.layer] += 1
            if e.dxftype() == 'INSERT':
                for a in e.attribs:
                    ust[a.dxf.layer] += 1
    blok = defaultdict(int)
    for b in doc.blocks:
        if b.block_record.is_any_layout:
            continue
        for e in b:
            blok[e.dxf.get('layer', '0')] += 1
    hatali = {k: v for k, v in ust.items() if k.upper() not in SERBEST and not k.startswith('ROTAS-')}
    ic = sorted(k for k in blok if k not in ust and k.upper() not in SERBEST and not k.startswith('ROTAS-'))
    return hatali, ic


def bos_katman_temizle(doc):
    kullanilan = set()
    for b in doc.blocks:
        for e in b:
            kullanilan.add(e.dxf.get('layer', '0').upper())
            if e.dxftype() == 'INSERT':
                for a in e.attribs:
                    kullanilan.add(a.dxf.layer.upper())
    for e in doc.entitydb.values():
        try:
            if e.dxf.hasattr('layer'):
                kullanilan.add(e.dxf.layer.upper())
        except Exception:
            pass
    akt = doc.header.get('$CLAYER', '0').upper()
    sil = [l.dxf.name for l in doc.layers if l.dxf.name.upper() not in kullanilan and l.dxf.name.upper() not in SERBEST
           and l.dxf.name.upper() != akt]
    for n in sil:
        doc.layers.remove(n)
    return sil


def _yazi_poligonlari(msp, haric_katman=MIMARI):
    out = []
    for e in msp:
        t = e.dxftype()
        ys = []
        if t in ('TEXT', 'MTEXT'):
            ys = [e]
        elif t == 'INSERT':
            ys = [a for a in e.attribs if not a.is_invisible]
        for y in ys:
            if any(k in _u(y.dxf.layer) for k in haric_katman):
                continue
            s = _metin_al(y).strip()
            if not s:
                continue
            try:
                v = [(p.x, p.y) for p in disassemble.make_primitive(y).vertices()]
                pg = Polygon(v) if len(v) >= 4 else None
            except Exception:
                pg = None
            if pg is not None and pg.is_valid and pg.area > 0:
                out.append((y, s, pg))
    return out


def yazi_cakisma(msp, min_oran=0.25, alan=None):
    """Yazı-yazı çakışması (MİMARİ katmanları hariç). alan verilirse yalnız o dikdörtgen(ler)deki yazılar.
    Dönüş: [(yazı1, yazı2, (x, y))]"""
    ys = _yazi_poligonlari(msp)
    if alan:
        ys = [y for y in ys if any(_icinde((y[2].centroid.x, y[2].centroid.y), r) for r in alan)]
    if not ys:
        return []
    agac = STRtree([y[2] for y in ys])
    out = []
    for i, (e, s, pg) in enumerate(ys):
        for j in agac.query(pg):
            j = int(j)
            if j <= i:
                continue
            a = pg.intersection(ys[j][2]).area
            if a > min_oran * min(pg.area, ys[j][2].area):
                out.append((s[:30], ys[j][1][:30], (round(pg.centroid.x), round(pg.centroid.y))))
    return out


def audit(doc):
    a = doc.audit()
    return len(a.errors), len(a.fixes), [str(x.message)[:120] for x in a.errors[:10]]


# =====================================================================================  ana fonksiyon
def mevcut_lejant(msp, paftalar):
    """Girdide hazır "LEJANT ... ADET / METRAJ" paftası var mı: başlık yazısı (LEJANT + METRAJ/ADET geçen) ve onu içeren
    pafta. Dönüş: (x0, y0, x1, y1) veya None"""
    for e in msp.query('TEXT MTEXT'):
        t = _u(_metin_al(e))
        if 'LEJANT' in t and ('METRAJ' in t or 'ADET' in t):
            p = e.dxf.insert
            for pf in paftalar:
                if _icinde((p.x, p.y), (pf['x0'], pf['y0'], pf['x1'], pf['y1'])):
                    return (round(pf['x0']), round(pf['y0']), round(pf['x1']), round(pf['y1']))
    return None


def bitir(giris, cikis, ekler=(), cerceve_duzelt=True, metraj_turleri=('PLAN',), boru_ek_anahtar=(), yaz=True,
          lejant='otomatik'):
    """giris.dxf -> cikis.dxf. ekler: [yol | dict(yol, baslik?, etiket?, katman_cevir?, metin_cevir?, yazi_sigdir?)]
    — soldan sağa sırayla sol alta konur. lejant: 'otomatik' (girdide hazır lejant/metraj paftası varsa üretme),
    True (her zaman üret), False (üretme). Dönüş: rapor dict."""
    doc = ezdxf.readfile(giris)
    msp = doc.modelspace()
    R = dict(giris=giris, cikis=cikis, uyari=[])
    a0 = audit(doc)
    R['audit_giris'] = a0
    birim = {4: 0.001, 5: 0.01, 6: 1.0}.get(doc.header.get('$INSUNITS', 5), 0.01)

    kl = list(_tek_tek(list(msp)))
    paftalar = paftalari_bul(msp, kl)
    R['uyari'] += anormal_cerceve_duzelt(msp, paftalar, kl, cerceve_duzelt)
    if cerceve_duzelt:
        kl = list(_tek_tek(list(msp)))
    sinir = _birlesim((p['x0'], p['y0'], p['x1'], p['y1']) for p in paftalar)
    R['paftalar'] = [(p['tur'], p['baslik'], round(p['x0']), round(p['y0']), round(p['x1']), round(p['y1'])) for p in paftalar]
    R['sinir_ilk'] = tuple(round(v) for v in sinir)
    ref = min(paftalar, key=lambda p: p['x0']) if paftalar else None
    if ref and ref['baslik_ent'] is None:
        ref = next((p for p in paftalar if p['baslik_ent'] is not None), ref)

    # ---- 2) lejant + adet + metraj
    hazir = mevcut_lejant(msp, paftalar)
    if lejant is False or (lejant == 'otomatik' and hazir):
        R['lejant_pafta'] = hazir
        R['lejant_uretildi'] = False
        R['sembol_adet'], R['sembol_tur'], R['diger_blok'], R['metraj'] = {}, {}, {}, {}
        if hazir:
            R['uyari'].append('Girdide hazır lejant / adet / metraj paftası var %s; yenisi üretilmedi.' % (hazir,))
        return _ekler_ve_kontrol(doc, msp, R, ekler, paftalar, sinir, ref, yaz, cikis)
    R['lejant_uretildi'] = True
    sayim, ornek, tur_sayim = sembol_sayimi(doc, paftalar, kl)
    diger = diger_bloklar(doc, paftalar, kl)
    R['sembol_adet'] = {'%s/%s' % k: v for k, v in sorted(sayim.items())}
    R['sembol_tur'] = {t: sum(v.values()) for t, v in tur_sayim.items()}
    R['diger_blok'] = diger
    tablo, mb = boru_metraji(msp, paftalar, kl, birim, metraj_turleri, boru_ek_anahtar)
    R['metraj'] = tablo

    sag = max(paftalar, key=lambda p: p['x1']) if paftalar else None
    H = (ref['y1'] - ref['y0']) if ref else 2800.0
    ic = ref['ic'] if ref and ref['ic'] else 26.0
    x0 = sinir[2] + ARALIK
    y0 = sag['y0'] if sag else sinir[1]
    ust = y0 + H - ic - KENAR
    once = set(e.dxf.handle for e in msp)
    w1, h1, n1 = lejant_ciz(msp, x0 + ic + KENAR, ust, sayim, ornek, diger)
    w2, h2 = (0.0, 0.0)
    if tablo:
        w2, h2 = metraj_ciz(msp, x0 + ic + KENAR + w1 + (60 if n1 else 0), ust, tablo, mb, 'm')
    icerik_w = w1 + (60 if n1 and tablo else 0) + w2
    icerik_h = max(h1, h2)
    gen = icerik_w + 2 * (ic + KENAR)
    yuk = max(H, icerik_h + 2 * (ic + KENAR) + BASLIK_BANT)
    if yuk > H + 1:   # tablolar üstten aşağı çizildi; çerçeve yukarı uzar, tablolar yeni üst kenara taşınır
        for e in msp:
            if e.dxf.handle not in once:
                e.translate(0, yuk - H, 0)
        R['uyari'].append('Lejant/metraj paftası içerik nedeniyle %.0f birim yüksek; çerçeve yukarı uzatıldı.' % (yuk - H))
    _pafta_ciz(msp, x0, y0, x0 + gen, y0 + yuk, ref, 'LEJANT, MALZEME / ARMATÜR ADET TABLOSU VE BORU METRAJI   ÖLÇEK : ÖLÇEKSİZ')
    R['lejant_pafta'] = (round(x0), round(y0), round(x0 + gen), round(y0 + yuk))
    return _ekler_ve_kontrol(doc, msp, R, ekler, paftalar, sinir, ref, yaz, cikis)


def _ekler_ve_kontrol(doc, msp, R, ekler, paftalar, sinir, ref, yaz, cikis):
    # ---- 3) ekler sol alt
    R['ekler'], r = ekleri_yerlestir(doc, list(ekler), paftalar, sinir, ref) if ekler else ([], [])
    R['uyari'] += r

    # ---- 4) kontroller
    hatali, blok_ic = katman_kontrol(doc)
    R['katman_hatali'] = hatali
    R['katman_blok_ici'] = blok_ic
    R['bos_katman_silinen'] = bos_katman_temizle(doc)
    yeni_alan = ([R['lejant_pafta']] if R.get('lejant_uretildi') else []) + \
        [(e['x0'], e['y0'], e['x1'], e['y1']) for e in R['ekler']]
    R['yazi_cakisma_tum'] = yazi_cakisma(msp)
    R['yazi_cakisma_yeni'] = yazi_cakisma(msp, alan=yeni_alan)
    R['audit_cikis'] = audit(doc)
    kl2 = list(_tek_tek(list(msp)))
    R['sinir_son'] = tuple(round(v) for v in _birlesim(b for _, b in kl2))
    if yaz:
        os.makedirs(os.path.dirname(os.path.abspath(cikis)), exist_ok=True)
        doc.saveas(cikis)
        d2 = ezdxf.readfile(cikis)
        R['geri_okuma'] = dict(nesne=len(d2.modelspace()), audit=audit(d2)[:2])
    return R


def rapor_yaz(R, akis=sys.stdout):
    p = lambda *a: print(*a, file=akis)
    p('== PAFTA BİTİR: %s -> %s' % (os.path.basename(R['giris']), os.path.basename(R['cikis'])))
    p('AUDIT giriş: %d hata, %d düzeltme' % R['audit_giris'][:2])
    p('Paftalar (%d), toplam sınır %s:' % (len(R['paftalar']), R['sinir_ilk']))
    for t in R['paftalar']:
        p('   [%-8s] %-60s %s' % (t[0], t[1][:60], t[2:]))
    for u in R['uyari']:
        p('UYARI: ' + u)
    p('Sembol adetleri (max(plan, şema)): %s' % R['sembol_adet'])
    p('Pafta türüne göre toplam sembol: %s' % R['sembol_tur'])
    p('Kütüphane dışı bloklar: %s' % R['diger_blok'])
    p('Boru metrajı (m):')
    for k, v in R['metraj'].items():
        p('   %-32s %s  toplam %.1f' % (k, {c: round(x, 1) for c, x in sorted(v.items(), key=lambda a: _cap_sira(a[0]))}, sum(v.values())))
    p('Lejant paftası: %s%s' % (R['lejant_pafta'], '' if R.get('lejant_uretildi') else ' (girdide hazır, üretilmedi)'))
    for e in R['ekler']:
        p('Ek: %-40s %s  (%d nesne)' % (e['baslik'], (round(e['x0']), round(e['y0']), round(e['x1']), round(e['y1'])), e['nesne']))
    p('KATMAN: ROTAS- olmayan üst seviye katmanlar: %s' % (R['katman_hatali'] or 'yok'))
    p('KATMAN: yalnız blok içinde kullanılan ROTAS dışı katmanlar (MTY blok içi, serbest): %d adet' % len(R['katman_blok_ici']))
    p('Boş katman silindi: %d %s' % (len(R['bos_katman_silinen']), R['bos_katman_silinen'][:15]))
    p('Yazı çakışması: tüm çizimde %d (MİMARİ hariç); yeni eklenen paftalarda %d' % (len(R['yazi_cakisma_tum']), len(R['yazi_cakisma_yeni'])))
    for c in R['yazi_cakisma_tum'][:25]:
        p('   %r <> %r @ %s' % c)
    p('AUDIT çıkış: %d hata, %d düzeltme %s' % R['audit_cikis'])
    if 'geri_okuma' in R:
        p('Geri okuma: %s' % R['geri_okuma'])
    p('Son sınır: %s' % (R['sinir_son'],))
