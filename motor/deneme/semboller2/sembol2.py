# -*- coding: utf-8 -*-
"""ROTAŞ sembol kütüphanesi v2 — MTY'ye bağımlı değil, saf geometri (LINE/CIRCLE/ARC/LWPOLYLINE/HATCH).

API
    ekle(doc)                                  tüm ROTAS- blok tanımlarını ve katmanları ekler
    koy(msp, ad, x, y, aci=0, olcek=1, no=None, cap=None, katman=None, ayna=False, yh=None)
                                               INSERT + NO/CAP öznitelikleri (öznitelik düz okunur)
    hat(msp, p0, p1, [(t, ad, no, cap), ...], katman, sembol_katman=None)
                                               düz boru; sembol kesme aralığında boru kesilir
    baglanti(ins, ad=None)                     bağlantı noktalarının dünya koordinatı
    Engel(msp) / etiket_yer(ins, engel, ...)   numara/çap etiketini sembolün hemen yanına, çakışmasız
    otomatik_lejant(doc, x=None, y=None)       kullanılan ROTAS- bloklarının lejantı + adet tablosu
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ezdxf                                          # noqa: E402
from ezdxf.enums import TextEntityAlignment as TA     # noqa: E402
from ezdxf.math import Matrix44                       # noqa: E402
from shapely.geometry import box, LineString, Point   # noqa: E402
from shapely.strtree import STRtree                   # noqa: E402

from cekirdek import Ciz, SEMBOL, GRUP                 # noqa: E402
import tanimlar                                        # noqa: E402,F401  (kayıtları doldurur)

STIL = 'ROTAS'
KAT_NO = 'ROTAS-SEMBOL-NO'
KAT_CAP = 'ROTAS-SEMBOL-CAP'
KAT_KILAVUZ = 'ROTAS-SEMBOL-KILAVUZ'
LEJ_CER, LEJ_YAZ, LEJ_BAS, LEJ_SEM = 'ROTAS-LEJANT-CERCEVE', 'ROTAS-LEJANT-YAZI', 'ROTAS-LEJANT-BASLIK', 'ROTAS-LEJANT-SEMBOL'
YARDIMCI = {KAT_NO: 3, KAT_CAP: 3, KAT_KILAVUZ: 3, LEJ_CER: 8, LEJ_YAZ: 7, LEJ_BAS: 5, LEJ_SEM: 7}

# boru katmanları (lejantta çizgi örneği olarak da gösterilir): (grup, açıklama, katman, renk, çizgi tipi)
BORU = [
    ('SB', 'SOĞUK SU BORUSU', 'ROTAS-SIHHI-SOGUK-SU', 5, 'Continuous'),
    ('SB', 'SICAK SU BORUSU', 'ROTAS-SIHHI-SICAK-SU', 1, 'DASHED'),
    ('SB', 'SİRKÜLASYON BORUSU', 'ROTAS-SIHHI-SIRKULASYON', 31, 'DASHDOT'),
    ('SB', 'PİS SU BORUSU', 'ROTAS-SIHHI-PIS-SU', 6, 'Continuous'),
    ('SB', 'YAĞMUR SUYU / BALKON SÜZGECİ BORUSU', 'ROTAS-SIHHI-YAGMUR', 3, 'Continuous'),
    ('IS', 'ISITMA GİDİŞ BORUSU', 'ROTAS-ISITMA-GIDIS', 10, 'Continuous'),
    ('IS', 'ISITMA DÖNÜŞ BORUSU', 'ROTAS-ISITMA-DONUS', 30, 'DASHED'),
    ('YG', 'SPRİNKLER BORUSU', 'ROTAS-YANGIN-SPRINKLER-BORU', 140, 'Continuous'),
    ('YG', 'YANGIN DOLABI BORUSU', 'ROTAS-YANGIN-DOLAP-BORU', 1, 'Continuous'),
    ('YG', 'TEST / DRENAJ BORUSU', 'ROTAS-YANGIN-DRENAJ', 8, 'DASHED'),
    ('HV', 'WC EGZOZ KANALI', 'ROTAS-HAVALANDIRMA-EGZOZ', 4, 'Continuous'),
    ('HV', 'TAZE HAVA KANALI', 'ROTAS-HAVALANDIRMA-UFLEME', 20, 'Continuous'),
]


# ============================================================================= tanım
def _blok_ciz(doc, ad):
    k = SEMBOL[ad]
    blk = doc.blocks.new(ad, base_point=(0, 0))
    c = Ciz(blk)
    k['ciz'](c)
    kap = tuple(c.kap)
    k['kap'] = kap
    # öznitelik tanımları (NO, CAP) — yalnız bunlar; konumları koy() / etiket_yer() düzenler
    x1, y0, y1 = kap[2], kap[1], kap[3]
    yh = 10.0
    blk.add_attdef('NO', (x1 + 2, (y0 + y1) / 2 + 1), dxfattribs={'layer': '0', 'height': yh, 'prompt': 'Numara (V-01, P-01 ...)',
                                                                 'style': STIL, 'color': 256})
    blk.add_attdef('CAP', (x1 + 2, (y0 + y1) / 2 - yh - 1), dxfattribs={'layer': '0', 'height': yh * 0.8, 'prompt': 'Çap (DN25, Ø50 ...)',
                                                                       'style': STIL, 'color': 256})
    return blk


def katmanlar(doc):
    if STIL not in doc.styles:
        doc.styles.add(STIL, font='arial.ttf')
    try:
        if 'DASHED' not in doc.linetypes:
            ezdxf.setup_linetypes(doc)
    except Exception:
        pass
    for g, (_, kat, renk) in GRUP.items():
        if kat not in doc.layers:
            doc.layers.add(kat, color=renk)
    for kat, renk in YARDIMCI.items():
        if kat not in doc.layers:
            doc.layers.add(kat, color=renk)
    for _, _, kat, renk, lt in BORU:
        if kat not in doc.layers:
            doc.layers.add(kat, color=renk, linetype=lt if lt in doc.linetypes else 'Continuous')


def ekle(doc, adlar=None):
    """Tüm (veya verilen) ROTAS- blok tanımlarını ekler. Var olan tanıma dokunmaz. Dönüş: eklenen ad listesi."""
    katmanlar(doc)
    eklenen = []
    for ad in (adlar or SEMBOL):
        if ad in doc.blocks:
            if SEMBOL[ad]['kap'] is None:
                _kap_hesapla(doc, ad)
            continue
        _blok_ciz(doc, ad)
        eklenen.append(ad)
    return eklenen


def _kap_hesapla(doc, ad):
    from ezdxf import bbox
    b = bbox.extents([e for e in doc.blocks.get(ad) if e.dxftype() != 'ATTDEF'], fast=True)
    SEMBOL[ad]['kap'] = (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)


def bul(ad):
    """'ROTAS-SB-CEKVALF' / 'SB-CEKVALF' / 'CEKVALF' -> tam ad"""
    if ad in SEMBOL:
        return ad
    u = ad.upper()
    for k in SEMBOL:
        if k == 'ROTAS-' + u or k.endswith('-' + u):
            return k
    raise KeyError('ROTAS sembolü yok: %s' % ad)


# ============================================================================= yerleştirme
def _mat(ins):
    return ins.matrix44()


def _olcekler(olcek, ayna):
    sx, sy = (olcek, olcek) if not isinstance(olcek, (tuple, list)) else olcek
    return (-sx if ayna else sx), sy


def koy(msp, ad, x, y, aci=0.0, olcek=1.0, no=None, cap=None, katman=None, ayna=False, yh=None):
    """Sembolü yerleştirir. katman verilmezse sembol grubunun katmanı. no/cap -> öznitelik.
    Öznitelikler varsayılan olarak sembol kapsamının üstüne (no) ve altına (cap) yatay konur;
    çakışmasız yerleşim için sonra etiket_yer() çağrılır. Dönüş: Insert."""
    doc = msp.doc
    ad = bul(ad)
    if ad not in doc.blocks:
        ekle(doc, [ad])
    if SEMBOL[ad]['kap'] is None:
        _kap_hesapla(doc, ad)
    sx, sy = _olcekler(olcek, ayna)
    kat = katman or GRUP[SEMBOL[ad]['grup']][1]
    ins = msp.add_blockref(ad, (x, y), dxfattribs={'layer': kat, 'rotation': aci, 'xscale': sx, 'yscale': sy})
    yh = yh or 10.0
    kx0, ky0, kx1, ky1 = dunya_kapsam(ins)
    if SEMBOL[ad]['no_ic']:
        cx, cy = baglanti_merkez(ins)
        _attrib(ins, 'NO', no or '', (cx, cy), yh * 1.2, KAT_NO, TA.MIDDLE_CENTER)
    else:
        _attrib(ins, 'NO', no or '', ((kx0 + kx1) / 2, ky1 + yh * 0.35), yh, KAT_NO, TA.BOTTOM_CENTER)
    _attrib(ins, 'CAP', cap or '', ((kx0 + kx1) / 2, ky0 - yh * 0.35), yh * 0.8, KAT_CAP, TA.TOP_CENTER)
    return ins


def baglanti_merkez(ins):
    """no_ic semboller için NO konumu: yerel (0,0) (rögar KS'de kutu ortası)"""
    ad = ins.dxf.name
    if ad == 'ROTAS-KS-ROGAR':
        v = _mat(ins).transform((0, -20, 0))
        return (v.x, v.y)
    v = _mat(ins).transform((0, 0, 0))
    return (v.x, v.y)


def _attrib(ins, tag, metin, p, h, kat, hiza):
    a = ins.add_attrib(tag, metin, insert=p, dxfattribs={'layer': kat, 'height': h, 'style': STIL, 'rotation': 0})
    a.set_placement(p, align=hiza)
    return a


def dunya_kapsam(ins):
    """INSERT'in (öznitelikler hariç) dünya eksenli kapsamı"""
    k = SEMBOL[ins.dxf.name]['kap']
    m = _mat(ins)
    pts = [m.transform((x, y, 0)) for x, y in ((k[0], k[1]), (k[2], k[1]), (k[2], k[3]), (k[0], k[3]))]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def baglanti(ins, ad=None):
    """Bağlantı noktası/noktaları (dünya). ad=None -> sözlük"""
    b = SEMBOL[ins.dxf.name]['baglanti']
    m = _mat(ins)
    r = {k: (lambda q: (q.x, q.y))(m.transform((v[0], v[1], 0))) for k, v in b.items()}
    return r[ad] if ad else r


def hat(msp, p0, p1, semboller=(), katman='ROTAS-SIHHI-SOGUK-SU', sembol_katman=None, yh=None):
    """p0->p1 düz boru, üzerindeki semboller (t: 0..1 konum, ad, no, cap). Boru sembolün kesme aralığında
    kesilir (tek parça değil, parçalar halinde). Dönüş: [Insert]."""
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    aci = math.degrees(math.atan2(uy, ux))
    kes = []
    ins = []
    for s in sorted(semboller, key=lambda s: s[0]):
        t, ad = s[0], bul(s[1])
        no = s[2] if len(s) > 2 else None
        cap = s[3] if len(s) > 3 else None
        d = t * L
        i = koy(msp, ad, x0 + ux * d, y0 + uy * d, aci=aci, no=no, cap=cap, katman=sembol_katman or katman, yh=yh)
        ins.append(i)
        k = SEMBOL[ad]['kesme']
        if k:
            kes.append((d + k[0], L if SEMBOL[ad]['uc'] else d + k[1]))
    t = 0.0
    for a, b in kes + [(L, L)]:
        if a > t + 1e-6:
            msp.add_line((x0 + ux * t, y0 + uy * t), (x0 + ux * a, y0 + uy * a), dxfattribs={'layer': katman})
        t = max(t, b)
    return ins


# ============================================================================= etiket yerleştirme
def _metin_kutu(e):
    """TEXT / ATTRIB / MTEXT yaklaşık kutusu"""
    t = e.dxftype()
    if t == 'MTEXT':
        s = e.plain_text()
        h = e.dxf.char_height
        w = max(len(x) for x in s.split('\n')) * h * 0.72 if s else 0
        n = s.count('\n') + 1
        p = e.dxf.insert
        return box(p[0], p[1] - n * h * 1.4, p[0] + w, p[1])
    s = e.dxf.text
    if not s:
        return None
    h = e.dxf.height
    w = len(s) * h * 0.72 * e.dxf.get('width', 1.0)
    al = e.get_align_enum() if hasattr(e, 'get_align_enum') else None
    p = e.dxf.align_point if (al and al.name != 'LEFT' and e.dxf.hasattr('align_point')) else e.dxf.insert
    x, y = p[0], p[1]
    nm = al.name if al else 'LEFT'
    if 'CENTER' in nm or nm == 'MIDDLE':
        x -= w / 2
    elif 'RIGHT' in nm:
        x -= w
    if nm.startswith('TOP'):
        y -= h
    elif nm.startswith('MIDDLE') or nm == 'MIDDLE':
        y -= h / 2
    return box(x, y, x + w, y + h)


def _geom(e):
    t = e.dxftype()
    try:
        if t == 'LINE':
            return LineString([e.dxf.start[:2], e.dxf.end[:2]])
        if t == 'LWPOLYLINE':
            p = [v[:2] for v in e.get_points('xy')]
            if e.closed:
                p.append(p[0])
            return LineString(p) if len(p) > 1 else None
        if t == 'CIRCLE':
            return Point(e.dxf.center[:2]).buffer(e.dxf.radius, 12).exterior
        if t == 'ARC':
            return LineString([v[:2] for v in e.flattening(1.0)])
        if t in ('TEXT', 'ATTRIB', 'MTEXT'):
            return _metin_kutu(e)
        if t == 'INSERT':
            if e.dxf.name in SEMBOL and SEMBOL[e.dxf.name]['kap']:
                return box(*dunya_kapsam(e))
            from ezdxf import bbox
            b = bbox.extents([e], fast=True)
            return box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y) if b.has_data else None
    except Exception:
        return None
    return None


class Engel:
    """Çakışma kontrolü için engel dizini (STRtree). msp'deki çizgi, daire, yazı, INSERT ve öznitelikler.
    Yeni konan etiketler ekle() ile eklenir (ayrı listede, ağaç yeniden kurulmaz)."""

    def __init__(self, msp=None, katman_haric=('ROTAS-PAFTA',)):
        self.g, self.sahip = [], []
        if msp is not None:
            for e in msp:
                if e.dxf.layer in katman_haric:
                    continue
                g = _geom(e)
                if g is not None and not g.is_empty:
                    self.g.append(g)
                    self.sahip.append(e.dxf.handle)
                if e.dxftype() == 'INSERT':
                    for a in e.attribs:
                        g = _metin_kutu(a)
                        if g is not None:
                            self.g.append(g)
                            self.sahip.append(a.dxf.handle)
        self.agac = STRtree(self.g) if self.g else None
        self.yeni = []

    def ekle(self, g, sahip=None):
        self.yeni.append((g, sahip))

    def bos_mu(self, g, haric=()):
        if self.agac is not None:
            for i in self.agac.query(g, predicate='intersects'):
                if self.sahip[i] not in haric:
                    return False
        for gg, s in self.yeni:
            if (s is None or s not in haric) and gg.intersects(g):
                return False
        return True


# yerel yön tercihleri (hat üstü semboller: boru yerel X'te -> önce üst/alt)
_YON_HAT = [(0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1), (1, 0), (-1, 0)]
_YON_NOKTA = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]


def etiket_yer(ins, engel, tag='NO', metin=None, yh=None, bosluk=None, halka=4, kilavuz=True):
    """INSERT'in 'tag' özniteliğini (yoksa yeni TEXT) sembolün hemen yanına, hiçbir çizgi/yazı/bloğa binmeden koyar.
    Aday konumlar sembol kapsamının 8 yönündedir; hat üstü sembollerde önce boruya dik yönler denenir.
    İlk halkada yer yoksa uzaklaşılır ve kılavuz çizgisi çizilir. Dönüş: (x, y) metin kutusu sol alt köşe veya None."""
    msp = ins.get_layout() if hasattr(ins, 'get_layout') else None
    at = ins.get_attrib(tag)
    if metin is None:
        metin = at.dxf.text if at is not None else ''
    if not metin:
        return None
    yh = yh or (at.dxf.height if at is not None else 10.0)
    bosluk = yh * 0.3 if bosluk is None else bosluk
    w = len(metin) * yh * 0.72
    x0, y0, x1, y1 = dunya_kapsam(ins)
    k = SEMBOL[ins.dxf.name]
    yonler = _YON_HAT if k['kesme'] else _YON_NOKTA
    a = math.radians(ins.dxf.rotation)
    haric = {ins.dxf.handle} | {aa.dxf.handle for aa in ins.attribs}
    # bu sembolün üzerindeki boru çizgileri sembol kutusunun içinden geçer; etiket kutu dışında aranır
    secim = None
    for n in range(halka):
        g = bosluk + n * (yh * 1.2)
        for dx, dy in yonler:
            # yerel yönü dünyaya çevir (en yakın eksene yuvarla)
            wx = dx * math.cos(a) - dy * math.sin(a)
            wy = dx * math.sin(a) + dy * math.cos(a)
            sx = 0 if abs(wx) < 0.38 else (1 if wx > 0 else -1)
            sy = 0 if abs(wy) < 0.38 else (1 if wy > 0 else -1)
            if sx > 0:
                bx = x1 + g
            elif sx < 0:
                bx = x0 - g - w
            else:
                bx = (x0 + x1) / 2 - w / 2
            if sy > 0:
                by = y1 + g
            elif sy < 0:
                by = y0 - g - yh
            else:
                by = (y0 + y1) / 2 - yh / 2
            kutu = box(bx - 0.15 * yh, by - 0.15 * yh, bx + w + 0.15 * yh, by + yh * 1.15)
            if engel.bos_mu(kutu, haric):
                secim = (bx, by, n, kutu)
                break
        if secim:
            break
    if not secim:
        return None
    bx, by, n, kutu = secim
    if at is not None:
        at.dxf.rotation = 0
        at.set_placement((bx, by), align=TA.LEFT)
        at.dxf.height = yh
    else:
        t = msp.add_text(metin, height=yh, dxfattribs={'layer': KAT_NO if tag == 'NO' else KAT_CAP, 'style': STIL})
        t.set_placement((bx, by), align=TA.LEFT)
    engel.ekle(kutu)
    if n > 0 and kilavuz and msp is not None:
        sem = box(x0, y0, x1, y1)
        from shapely.ops import nearest_points
        p, q = nearest_points(sem.exterior, kutu.exterior)
        ln = msp.add_line((p.x, p.y), (q.x, q.y), dxfattribs={'layer': KAT_KILAVUZ})
        engel.ekle(LineString([(p.x, p.y), (q.x, q.y)]))
        _ = ln
    return (bx, by)


def etiketle(msp, engel=None, insertler=None):
    """Tüm (veya verilen) ROTAS- INSERT'lerin NO ve CAP özniteliklerini etiket_yer ile yerleştirir.
    Dönüş: yerleştirilemeyen [(insert, tag)]."""
    engel = engel or Engel(msp)
    ins = insertler or [e for e in msp.query('INSERT') if e.dxf.name in SEMBOL and not e.dxf.layer.startswith('ROTAS-LEJANT')]
    olmayan = []
    for i in ins:
        if SEMBOL[i.dxf.name]['no_ic']:
            tags = ['CAP']
        else:
            tags = ['NO', 'CAP']
        for tg in tags:
            a = i.get_attrib(tg)
            if a is not None and a.dxf.text:
                if etiket_yer(i, engel, tg) is None:
                    olmayan.append((i, tg))
    return olmayan


# ============================================================================= lejant
def _metin(msp, s, p, h, kat, al=TA.MIDDLE_LEFT, w=0.85):
    t = msp.add_text(s, height=h, dxfattribs={'layer': kat, 'style': STIL, 'width': w})
    t.set_placement(p, align=al)
    return t


def _kutu(msp, x0, y0, x1, y1, kat=LEJ_CER):
    return msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': kat})


def sembol_hucre(msp, ad, cx, cy, gen, yuk, katman=None, buyut_max=3.0, pay=0.8):
    """Sembolü hücreye sığdırarak (en fazla buyut_max kat büyüterek) ortalı koyar. Dönüş: (insert, ölçek)"""
    k = SEMBOL[ad]['kap']
    w, h = max(k[2] - k[0], 1e-3), max(k[3] - k[1], 1e-3)
    s = min(gen * pay / w, yuk * pay / h, buyut_max)
    mx, my = (k[0] + k[2]) / 2, (k[1] + k[3]) / 2
    ins = msp.add_blockref(ad, (cx - mx * s, cy - my * s), dxfattribs={'layer': katman or LEJ_SEM, 'xscale': s, 'yscale': s})
    return ins, s


_ONEK_GRUP = [('ROTAS-SIHHI-DEPO', 'DH'), ('ROTAS-SIHHI-ARMATUR', 'KS'), ('ROTAS-SIHHI', 'SB'), ('ROTAS-ISITMA', 'IS'),
              ('ROTAS-RADYATOR', 'IS'), ('ROTAS-YANGIN', 'YG'), ('ROTAS-HAVALANDIRMA', 'HV')]


def katman_grubu(katman):
    """INSERT katmanından tesisat grubu (ör. ısıtma hattındaki küresel vana ısıtma lejantına girer)"""
    for g, (_, k, _) in GRUP.items():
        if katman == k:
            return g
    for on, g in _ONEK_GRUP:
        if katman.startswith(on):
            return g
    return None


def kullanim_say(doc):
    """{(grup, blok): adet} — modelspace + iç içe kullanıcı blokları. Grup INSERT katmanından (en dıştaki
    anlamlı katman), bulunamazsa sembolün kendi grubundan. ROTAS-LEJANT* katmanı sayılmaz."""
    say = {}

    def tara(ents, derin, dis):
        for e in ents:
            if e.dxftype() != 'INSERT' or e.dxf.layer.startswith('ROTAS-LEJANT'):
                continue
            n = e.dxf.name
            g = dis or katman_grubu(e.dxf.layer)
            if n in SEMBOL:
                key = (g or SEMBOL[n]['grup'], n)
                say[key] = say.get(key, 0) + 1
            elif derin < 8 and n in doc.blocks and not n.startswith('*'):
                tara(doc.blocks.get(n), derin + 1, g)
    tara(doc.modelspace(), 0, None)
    return say


def lejant_tablosu(msp, x0, y0, baslik, satirlar, sutun_adet=True, sembol_gen=70.0, sat_yuk=34.0):
    """ROTAŞ lejant tablosu: SEMBOL | AÇIKLAMA | ADET. x0,y0 sol üst. satirlar: [dict(ad|boru, aciklama, adet)]
    Dönüş: (genişlik, yükseklik)"""
    W_A, W_N = 400.0, 60.0
    W = sembol_gen + W_A + (W_N if sutun_adet else 0)
    y = y0
    _kutu(msp, x0, y - 40, x0 + W, y)
    _metin(msp, baslik, (x0 + W / 2, y - 20), 16, LEJ_BAS, TA.MIDDLE_CENTER, 0.9)
    y -= 40
    _kutu(msp, x0, y - 24, x0 + W, y)
    for xx, s in ((x0 + sembol_gen / 2, 'SEMBOL'), (x0 + sembol_gen + W_A / 2, 'AÇIKLAMA')) + (((x0 + sembol_gen + W_A + W_N / 2, 'ADET'),) if sutun_adet else ()):
        _metin(msp, s, (xx, y - 12), 10, LEJ_YAZ, TA.MIDDLE_CENTER)
    y -= 24
    for r in satirlar:
        _kutu(msp, x0, y - sat_yuk, x0 + W, y)
        msp.add_line((x0 + sembol_gen, y), (x0 + sembol_gen, y - sat_yuk), dxfattribs={'layer': LEJ_CER})
        if sutun_adet:
            msp.add_line((x0 + sembol_gen + W_A, y), (x0 + sembol_gen + W_A, y - sat_yuk), dxfattribs={'layer': LEJ_CER})
        cy = y - sat_yuk / 2
        if 'boru' in r:
            msp.add_line((x0 + 8, cy), (x0 + sembol_gen - 8, cy), dxfattribs={'layer': r['boru']})
        else:
            sembol_hucre(msp, r['ad'], x0 + sembol_gen / 2, cy, sembol_gen, sat_yuk, katman=r.get('katman'))
        _metin(msp, r['aciklama'] + (' (*)' if r.get('celiski') else ''), (x0 + sembol_gen + 8, cy), 9, LEJ_YAZ, TA.MIDDLE_LEFT)
        if sutun_adet and r.get('adet') is not None:
            _metin(msp, str(r['adet']), (x0 + sembol_gen + W_A + W_N / 2, cy), 10, LEJ_YAZ, TA.MIDDLE_CENTER)
        y -= sat_yuk
    return W, y0 - y


def otomatik_lejant(doc, x=None, y=None, boru=True):
    """Çizimde kullanılan ROTAS- sembollerini grup grup sayar; yalnız kullanılanların lejant + ADET tablosunu çizer.
    x, y verilmezse çizimin sağına konur. Dönüş: {blok: adet}"""
    katmanlar(doc)
    msp = doc.modelspace()
    say = kullanim_say(doc)
    if x is None or y is None:
        from ezdxf import bbox
        b = bbox.extents([e for e in msp if not e.dxf.layer.startswith('ROTAS-LEJANT')], fast=True)
        x = (b.extmax.x + 150) if b.has_data else 0.0
        y = b.extmax.y if b.has_data else 0.0
    kullanilan_katman = {e.dxf.layer for e in msp}
    cx = x
    for g, (baslik, kat, _) in GRUP.items():
        ads = [n for (gg, n) in say if gg == g]
        if not ads:
            continue
        ads.sort(key=lambda a: list(SEMBOL).index(a))
        satir = []
        if boru:
            satir += [dict(boru=k, aciklama=a) for gg, a, k, _, _ in BORU if gg == g and k in kullanilan_katman]
        satir += [dict(ad=a, aciklama=SEMBOL[a]['aciklama'], adet=say[(g, a)], celiski=SEMBOL[a]['celiski']) for a in ads]
        w, h = lejant_tablosu(msp, cx, y, baslik, satir)
        cel = [SEMBOL[a]['celiski'] for a in ads if SEMBOL[a]['celiski']]
        yy = y - h - 14
        for s in sorted(set(cel)):
            _metin(msp, '(*) ' + s, (cx, yy), 7, LEJ_YAZ, TA.MIDDLE_LEFT)
            yy -= 11
        cx += w + 60
    top = {}
    for (g, n), v in say.items():
        top[n] = top.get(n, 0) + v
    return top
