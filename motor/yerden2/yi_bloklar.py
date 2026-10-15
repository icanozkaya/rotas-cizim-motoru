#!/usr/bin/env python3
"""yerden2 — kullanıcının bloklarından BİREBİR saf geometri ROTAS- blokları (15.10 D: "bloklarımı bozmuşsun").

Kazan dairesi `bloklar_onayli.py` yöntemi: kullanıcının new_block çizimindeki blok bir kez okunur, GÖRÜNEN geometrisi
(invisible=1 nesneler ve gizli öznitelikler hariç) yerleşimdeki görünüşüyle (ölçek / ayna uygulanmış, cm) kendi
kütüphanemize yazılır: `kutuphane/yerden/ROTAS_YI_BLOKLAR.dxf`. Çalışma anında yalnız bu kütüphane okunur (MTY dosyası,
MTY blok adı, MTY katmanı yok). Blok içi nesneler katman 0'da, renkleri kullanıcının görünüşüyle sabit (BYLAYER çözülmüş);
yalnız boru çizgileri ROTAS-ISITMA-GIDIS-BORU / ROTAS-ISITMA-DONUS-BORU katmanında (dönüşün çizgi tipi için).
Yazılar (sabit TEXT ve öznitelikler) kullanıcının yerleşimdeki yerinde, boyunda, renginde (arial, genişlik 0,65).

| Bizim blok | Kullanıcının bloğu | Ekleme noktası | Öznitelikler |
|---|---|---|---|
| ROTAS-YI-DEVRE-PANELI | *U108 (şema döşeme kesiti) | döşeme çizgisi, duvar iç yüzü (kullanıcının insert'i) | NO (Zxx h15), DERECE (h10), YER (W), UZ (m), ISIKAYBI, NO1 (devre no), BORU, MAHAL |
| ROTAS-YI-KOMBI-KOLLEKTOR (+ -n) | *U127 (kombi + 9 ağızlı kollektör) | kullanıcının insert'i | KOMBI ("H. KOMBİ 24KW") |
| ROTAS-YI-MAHAL | MTY-RADYATOR MAHAL | kutu merkezi | DERECE (cyan h12), NO (kırmızı h12) (+ gizli MAHAL, ALAN) |
| ROTAS-YI-ETIKET | MTY-ETIKET (×10, aynalı) | tablonun sol üst köşesi | UZ, AR, YER, NO1 (+ gizli MAHAL, NO, DERECE, ALAN, BORU) |
| ROTAS-YI-HAT-ETIKETI | *U110 (×10) devre hat etiketi | kılavuz ucu | CAP ("483W-Ø20") |
| ROTAS-YI-KOLLEKTOR-ETIKETI | *U111 (×10) kollektör toplamı | kılavuz ucu | CAP ("15907.3W-Ø32") |

Kollektör ağız sayısı n ≠ 9: kullanıcının 9 ağızlı bloğu AutoCAD STRETCH gibi değiştirilir — en soldaki (9−n) ağız
birimi (gidiş x = 5+10k, dönüş x = 10k, ±2,4) silinir, sol uç (barların sol ucu, vanalar, braket, dolap sol kenarı,
kombi bağlantı hatlarının ucu; x −35…kesim) +10·(9−n) sağa kayar; kombi yerinde kalır. n > 9'da sağdaki ağız birimi
kopyalanır, sol uç sola kayar.

    python3 motor/yerden2/yi_bloklar.py --cikar     # new_block'tan kütüphaneyi yeniden üret (geliştirme)
"""
import math
import os
import sys

import ezdxf
from ezdxf.addons import Importer
from ezdxf.math import Matrix44, OCSTransform

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.abspath(os.path.join(BURASI, '..', '..'))
KUTUPHANE = KOK + '/kutuphane/yerden/ROTAS_YI_BLOKLAR.dxf'
KAYNAK = '/tmp/claude-0/y2/new_block.dxf'
if not os.path.exists(KAYNAK):
    KAYNAK = KOK + '/ornekler/new_block.dxf'

PANEL = 'ROTAS-YI-DEVRE-PANELI'
KOMBI = 'ROTAS-YI-KOMBI-KOLLEKTOR'
MAHAL = 'ROTAS-YI-MAHAL'
ETIKET = 'ROTAS-YI-ETIKET'
HAT_ET = 'ROTAS-YI-HAT-ETIKETI'
KOL_ET = 'ROTAS-YI-KOLLEKTOR-ETIKETI'
G_KAT, D_KAT = 'ROTAS-ISITMA-GIDIS-BORU', 'ROTAS-ISITMA-DONUS-BORU'
STIL = 'ROTAS-YAZI'
GEN = 0.65

# (bizim ad, kullanıcının blok adı, yerleşim seçimi, ek kaydırma (x, y), öznitelik ad eşlemesi, sağa yaslı öznitelikler,
#  gizli ek öznitelikler)
TANIM = [
    (PANEL, '*U108', 0, (0.0, 0.0),
     {'NO_001': 'NO', 'DERECE_001': 'DERECE', 'UZ_001': 'UZ', 'NO1_001': 'NO1', 'BORU_001': 'BORU', 'MAHAL': 'MAHAL',
      'YER_001': 'YER', 'ISIKAYBI_001': 'ISIKAYBI'}, {}, ()),
    (KOMBI, '*U127', 0, (0.0, 0.0), {'H.KOMBİ24KW': 'KOMBI'}, {}, ()),
    (MAHAL, 'MTY-RADYATOR MAHAL', 0, (0.0, 0.0), {'DERECE_001': 'DERECE', 'NO_001': 'NO'}, {},
     ('MAHAL', 'ALAN')),
    # devre etiketi: kullanıcının MTY'si değerleri sağ sütunda sağa yaslı yazıyor (53.37 m / 15.0 / 4 sağ ucu ≈ ins+75,3);
    # "1867.9 W" ise sütun başında (ins+28,0) sola dayalı. Ekleme noktası tablonun sol üst köşesi (ins.x − 70).
    (ETIKET, 'MTY-ETIKET', 0, (70.0, 0.0), {'UZ_001': 'UZ', 'AR_001': 'AR', 'YER_001': 'YER', 'NO1_001': 'NO1'},
     {'UZ': 75.7, 'AR': 75.7, 'NO1': 75.7}, ('MAHAL', 'NO', 'DERECE', 'ALAN', 'BORU')),
    (HAT_ET, '*U110', 0, (0.0, 0.0), {'SCCP_001': 'CAP'}, {}, ()),
    (KOL_ET, '*U111', 0, (0.0, 0.0), {'SCCP_001': 'CAP'}, {}, ()),
]


# ====================================================================== çıkarım (geliştirme, bir kez)
def _renk(src, e, ust_renk):
    c = e.dxf.get('color', 256)
    if c == 256:
        ly = src.layers.get(e.dxf.layer)
        return abs(ly.dxf.color) if ly is not None else 7
    if c == 0:
        return ust_renk
    return c


def _katman(e):
    ad = e.dxf.layer.upper()
    if 'GIDIS-BORU' in ad:
        return G_KAT
    if 'DONUS-BORU' in ad:
        return D_KAT
    return '0'


def _gorunen(src, blk_ad, M, ust_renk, cikti):
    """bloğun görünen nesneleri (iç içe INSERT açılarak), M dönüşümüyle; (nesne, renk, katman)"""
    for e in src.blocks[blk_ad]:
        if e.dxf.get('invisible', 0):
            continue
        t = e.dxftype()
        if t in ('ATTDEF', 'ATTRIB'):
            continue
        renk = _renk(src, e, ust_renk)
        if t == 'INSERT':
            _gorunen(src, e.dxf.name, e.matrix44() @ M, renk, cikti)
            continue
        cikti.append((e, renk, _katman(e), M))


def _yazi_ekle(blk, metin, p, h, renk, rot=0.0, hal=0, val=0, al=None, gen=GEN, tag=None, gizli=False):
    da = {'height': h, 'style': STIL, 'width': gen, 'color': renk, 'rotation': rot, 'layer': '0'}
    if tag:
        e = blk.add_attdef(tag, p, text=metin, dxfattribs=da)
        if gizli:
            e.is_invisible = True
    else:
        e = blk.add_text(metin, dxfattribs=da)
    e.dxf.insert = p
    if hal or val:
        e.dxf.halign, e.dxf.valign = hal, val
        e.dxf.align_point = al if al is not None else p
    return e


def cikar(kaynak=KAYNAK, hedef=KUTUPHANE):
    src = ezdxf.readfile(kaynak)
    msp = src.modelspace()
    lib = ezdxf.new('R2018', setup=True)
    lib.units = 5
    if STIL not in lib.styles:
        lib.styles.add(STIL, font='arial.ttf')
    for kat, renk in ((G_KAT, 10), (D_KAT, 30)):
        lib.layers.add(kat, color=renk)
    rapor = []
    for ad, kaynak_ad, sec, (dx, dy), eslem, sag, gizli_ek in TANIM:
        ins = msp.query('INSERT[name=="%s"]' % kaynak_ad)[sec]
        I = ins.dxf.insert
        T_ = Matrix44.translate(-I[0] + dx, -I[1] + dy, 0)
        M = ins.matrix44() @ T_
        ayna = ins.dxf.xscale * ins.dxf.yscale < 0
        s = abs(ins.dxf.xscale)
        ust = _renk(src, ins, 7)
        nes = []
        _gorunen(src, ins.dxf.name, M, ust, nes)
        blk = lib.blocks.new(ad, base_point=(0, 0))
        say = {}
        for e, renk, kat, MM in nes:
            t = e.dxftype()
            if t in ('TEXT', 'MTEXT'):
                # sabit yazı: görünen (okunur) hâliyle; aynalı yerleşimde taban çizgisi yazı boyu kadar aşağı
                h = e.dxf.height * s
                hal, val = e.dxf.get('halign', 0), e.dxf.get('valign', 0)
                p = e.dxf.align_point if (hal or val) else e.dxf.insert
                q = MM.transform(p)
                if ayna and val in (0, 1):
                    q = (q[0], q[1] - h)
                elif ayna and val == 3:
                    val = 1
                elif ayna and val == 1:
                    val = 3
                _yazi_ekle(blk, e.dxf.text, (q[0], q[1]), h, renk, 0.0, hal, val, (q[0], q[1]),
                           gen=e.dxf.get('width', GEN))
                say[t] = say.get(t, 0) + 1
                continue
            k = e.copy()
            if t == 'HATCH':
                # ezdxf HATCH.transform deseni kütüphaneden yeniden kurar (ANSI38 ×25, ISO08 açısı) -> kullanıcının
                # desen satırları birebir kalsın diye yalnız öteleme elle uygulanır
                _o = MM.transform((0, 0, 0)); ox, oy = _o.x, _o.y
                lin = MM.transform_direction((1, 0, 0))
                if abs(lin[0] - 1) > 1e-6 or abs(lin[1]) > 1e-6:
                    print('[yi_bloklar] UYARI: dönüşümlü tarama atlandı', ad)
                    continue
                k.paths.transform(OCSTransform(k.dxf.extrusion, Matrix44.translate(ox, oy, 0)))
                if k.pattern:
                    for pl in k.pattern.lines:
                        pl.base_point = ezdxf.math.Vec2(pl.base_point[0] + ox, pl.base_point[1] + oy)
                k.dxf.layer = kat
                k.dxf.color = renk
                blk.add_entity(k)
                say[t] = say.get(t, 0) + 1
                continue
            try:
                k.transform(MM)
            except Exception as ex:                       # pragma: no cover
                print('[yi_bloklar] dönüşmedi', ad, t, ex)
                continue
            k.dxf.layer = kat
            k.dxf.color = 256 if kat != '0' else renk
            if k.dxf.hasattr('linetype') and kat == '0':
                k.dxf.linetype = 'BYLAYER'
            blk.add_entity(k)
            say[t] = say.get(t, 0) + 1
        # öznitelikler: kullanıcının yerleşimindeki ATTRIB'ler (görünür olanlar), konum ins'e göre
        for a in ins.attribs:
            tag = eslem.get(a.dxf.tag)
            if tag is None or a.is_invisible or a.dxf.get('invisible', 0):
                continue
            h = a.dxf.height
            renk = _renk(src, a, ust)
            hal, val = a.dxf.get('halign', 0), a.dxf.get('valign', 0)
            p = (a.dxf.insert[0] - I[0] + dx, a.dxf.insert[1] - I[1] + dy)
            al = None
            if hal or val:
                ap = a.dxf.align_point
                al = (ap[0] - I[0] + dx, ap[1] - I[1] + dy)
            rot = a.dxf.rotation if abs(a.dxf.rotation) > 1e-3 else 0.0
            if tag in sag:
                hal, val, al = 2, 0, (sag[tag] + dx, p[1])
                p = al
            _yazi_ekle(blk, a.dxf.text, p, h, renk, rot, hal, val, al, gen=a.dxf.get('width', GEN), tag=tag)
            say['ATTDEF'] = say.get('ATTDEF', 0) + 1
        for tag in gizli_ek:
            _yazi_ekle(blk, '', (0, 0), 5, 2, tag=tag, gizli=True)
        rapor.append((ad, kaynak_ad, say))
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    lib.saveas(hedef)
    for r in rapor:
        print('[yi_bloklar] %-28s <- %-20s %s' % r)
    return rapor


# ====================================================================== çalışma anı
def hazirla(doc):
    """kütüphanedeki ROTAS-YI- bloklarını belgeye al (zaten varsa dokunma)"""
    eksik = [t[0] for t in TANIM if t[0] not in doc.blocks]
    if not eksik:
        return
    lib = ezdxf.readfile(KUTUPHANE)
    imp = Importer(lib, doc)
    for ad in eksik:
        imp.import_block(ad, rename=False)
    imp.finalize()


def _xler(e):
    t = e.dxftype()
    if t == 'LINE':
        return [e.dxf.start[0], e.dxf.end[0]]
    if t == 'LWPOLYLINE':
        return [p[0] for p in e.get_points('xy')]
    if t in ('ARC', 'CIRCLE'):
        c, r = e.dxf.center, e.dxf.radius
        return [c[0] - r, c[0] + r]
    from ezdxf import bbox
    b = bbox.extents([e])
    return [b.extmin.x, b.extmax.x] if b.has_data else []


def _birim_mi(xs, kaldir):
    """nesne tamamen silinecek bir ağız biriminin içinde mi (gidiş 5+10k / dönüş 10k, ±2,4)"""
    a, b = min(xs), max(xs)
    for k in kaldir:
        for c in (5.0 + 10 * k, 10.0 * k):
            if a >= c - 2.45 and b <= c + 2.45:
                return True
    return False


def kombi_kollektor_blogu(doc, n):
    """n ağızlı kombi + kollektör bloğu (kullanıcının 9 ağızlı *U127 bloğundan STRETCH)"""
    hazirla(doc)
    if n == 9:
        return KOMBI
    ad = '%s-%d' % (KOMBI, n)
    if ad in doc.blocks:
        return ad
    taban = doc.blocks[KOMBI]
    blk = doc.blocks.new(ad)
    sol_min = -35.0
    if n < 9:
        d = 10.0 * (9 - n)
        kaldir = range(9 - n)
        kesim = d - 2.5
        for e in taban:
            xs = _xler(e) if e.dxftype() not in ('ATTDEF', 'TEXT') else [e.dxf.insert[0]]
            if xs and e.dxftype() not in ('ATTDEF', 'TEXT') and _birim_mi(xs, kaldir):
                continue
            k = e.copy()
            _kaydir(k, sol_min, kesim, d)
            blk.add_entity(k)
    else:
        d = -10.0 * (n - 9)
        kesim = -2.5
        for e in taban:
            k = e.copy()
            _kaydir(k, sol_min, kesim, d)
            blk.add_entity(k)
        # en soldaki (k = 0) ağız birimini sola kopyala
        for e in taban:
            if e.dxftype() in ('ATTDEF', 'TEXT'):
                continue
            xs = _xler(e)
            if xs and _birim_mi(xs, [0]):
                for m in range(1, n - 8):
                    k = e.copy()
                    k.translate(-10.0 * m, 0, 0)
                    blk.add_entity(k)
    return ad


def _kaydir(k, x0, x1, d):
    """STRETCH: x0 < x < x1 aralığındaki köşeler d kadar kayar"""
    t = k.dxftype()
    ic = lambda x: x0 < x < x1  # noqa: E731
    if t == 'LINE':
        s, e = k.dxf.start, k.dxf.end
        if ic(s[0]):
            k.dxf.start = (s[0] + d, s[1], s[2])
        if ic(e[0]):
            k.dxf.end = (e[0] + d, e[1], e[2])
    elif t == 'LWPOLYLINE':
        pts = [list(p) for p in k.get_points('xyseb')]
        for p in pts:
            if ic(p[0]):
                p[0] += d
        k.set_points(pts, format='xyseb')
    else:
        xs = _xler(k) if t not in ('ATTDEF', 'TEXT') else [k.dxf.insert[0]]
        if xs and all(ic(x) for x in xs):
            k.translate(d, 0, 0)


def yerlestir(msp, ad, p, katman, attr=None, olcek=1.0, rot=0.0):
    e = msp.add_blockref(ad, p, dxfattribs={'layer': katman, 'xscale': olcek, 'yscale': olcek, 'rotation': rot})
    if attr:
        e.add_auto_attribs(attr)
    return e


if __name__ == '__main__':
    if '--cikar' in sys.argv:
        cikar()
