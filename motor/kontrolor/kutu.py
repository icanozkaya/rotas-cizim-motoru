"""Gerçek yazı kutusu: ezdxf.tools.text_size (yazı tipi ölçüsü: genişlik faktörü, büyük harf yüksekliği, alt uzantı)
ile TEXT / ATTRIB / MTEXT kutusu; hizalama (halign/valign, MTEXT attachment_point) ve döndürme dahil.

MTEXT genişliği satır satır gerçek yazı genişliğidir (mtext_olcu), sütun genişliği değil; denetle.yazi_poligonu
da bu modülü kullanır (tek ölçü).

Neden: `denetle.yazi_poligonu` (disassemble.make_primitive) MTEXT'te sütun genişliği/satır aralığıyla yanlış kutu veriyor
(3 satırlık aspiratör notunda 96×170 yerine gerçek 138×65), TEXT'te alt uzantıyı (Ø, g, y ...) almıyor; sıhhi plan
tur 1'de (KONTROL_SIHHI_PLAN_TUR1.md madde 4) 45° döndürülmüş çap etiketlerinin birbirine bindiği görülmedi."""
import math

from shapely.geometry import Polygon

try:
    from ezdxf.tools import text_size as _TS
except Exception:  # pragma: no cover
    _TS = None

_ONBELLEK = {}


def _olcu_text(e):
    """(genişlik, büyük harf yüksekliği, alt uzantı) — yazı tipi ölçüsü; olmazsa tahmin"""
    s = e.dxf.text or ''
    h = e.dxf.get('height', 2.5) or 2.5
    wf = e.dxf.get('width', 1.0) or 1.0
    anahtar = (s, round(h, 3), round(wf, 3), e.dxf.get('style', 'Standard'))
    if anahtar in _ONBELLEK:
        return _ONBELLEK[anahtar]
    w, cap, alt = len(s) * h * 0.62 * wf, h, 0.25 * h
    if _TS is not None:
        try:
            ts = _TS.text_size(e)
            if ts.width > 0:
                w = ts.width
                cap = ts.cap_height or h
                alt = max(0.0, (ts.total_height or cap) - cap)
        except Exception:
            pass
    _ONBELLEK[anahtar] = (w, cap, alt)
    return w, cap, alt


def _dondur(pts, merkez, aci):
    c, s = math.cos(aci), math.sin(aci)
    x0, y0 = merkez
    return [(x0 + x * c - y * s, y0 + x * s + y * c) for x, y in pts]


def text_kutusu(e):
    s = e.dxf.text or ''
    if not s.strip():
        return None
    w, cap, alt = _olcu_text(e)
    ha, va = e.dxf.get('halign', 0), e.dxf.get('valign', 0)
    ins = e.dxf.insert
    ap = e.dxf.align_point if e.dxf.hasattr('align_point') else ins
    rot = math.radians(e.dxf.get('rotation', 0) or 0)
    if ha in (3, 5):                       # aligned / fit: insert ile align_point arası
        L = math.hypot(ap[0] - ins[0], ap[1] - ins[1])
        if L > 0.01:
            w = L
            rot = math.atan2(ap[1] - ins[1], ap[0] - ins[0])
        ha = 0
        ref = ins
    elif ha == 0 and va == 0:
        ref = ins
    else:
        ref = ap
    x0 = {0: 0.0, 1: -0.5, 2: -1.0, 4: -0.5}.get(ha, 0.0) * w
    if ha == 4 and va == 0:                # middle: yazının ortası (büyük harf yarısı)
        y0 = -0.5 * cap
    else:
        y0 = {0: 0.0, 1: alt, 2: -0.5 * cap, 3: -cap}.get(va, 0.0)
    # yerel kutu: tabandan alt uzantı aşağı, büyük harf yukarı
    yerel = [(x0, y0 - alt), (x0 + w, y0 - alt), (x0 + w, y0 + cap), (x0, y0 + cap)]
    pg = Polygon(_dondur(yerel, (ref[0], ref[1]), rot))
    return pg if pg.is_valid and pg.area > 0 else None


_BOSLUK = ('Space', 'NonBreakingSpace', 'Tabulator', 'EmptyBox')


def _satir_genisligi(satir):
    """text_layout satırının yazı genişliği: hücreler toplamı, sondaki boşluk hücreleri hariç"""
    toplam = son = 0.0
    for c in satir.cells():
        toplam += c.total_width
        if type(c).__name__ not in _BOSLUK:
            son = toplam
    return son


def mtext_olcu(e):
    """MTEXT'in GERÇEK ölçüsü (genişlik, yükseklik, satır sayısı) — denetle.py ve kontrolör ORTAK fonksiyonu.
    Genişlik: ezdxf düzen motorunun (text_size.MTextSizeDetector, satır kaydırma dahil) satır satır en uzun satırı;
    sütun genişliği (MTEXT `width`) DEĞİL. Ör. "asansör boşluğu" h 20: sütun 237,6 cm, gerçek 97,5 cm.
    Yükseklik: düzenin sütun yüksekliği (satır aralığı dahil). Ölçülemezse tahmin (0,62·h·karakter)."""
    s = e.plain_text() or ''
    h = e.dxf.get('char_height', 2.5) or 2.5
    anahtar = ('M', e.text, round(h, 3), round(e.dxf.get('width', 0) or 0, 3), e.dxf.get('style', 'Standard'),
               round(e.dxf.get('line_spacing_factor', 1.0) or 1.0, 3))
    if anahtar in _ONBELLEK:
        return _ONBELLEK[anahtar]
    satir = s.split('\n')
    w = hh = None
    n = len(satir)
    if _TS is not None:
        try:
            sutunlar = list(_TS.MTextSizeDetector().measure(e))
            gen, n, hh = [], 0, 0.0
            for col in sutunlar:
                hh = max(hh, col.total_height)
                for par in col:
                    for ln in par._lines:
                        gen.append(_satir_genisligi(ln))
                        n += 1
            if len(sutunlar) > 1:      # çok sütunlu MTEXT: toplam sütun genişliği
                ms = _TS.mtext_size(e)
                w = ms.total_width
            else:
                w = max(gen) if gen else None
        except Exception:
            w = None
    if not w or not hh:
        w = max(len(x) for x in satir) * h * 0.62
        hh = h * (1 + 1.667 * (len(satir) - 1))
        n = len(satir)
    _ONBELLEK[anahtar] = (w, hh, n)
    return w, hh, n


def mtext_kutusu(e):
    """MTEXT kutusu: gerçek satır genişliği (mtext_olcu) + bağlama noktası (attachment_point) + döndürme
    (text_direction / rotation)."""
    try:
        s = e.plain_text()
    except Exception:
        s = ''
    if not (s or '').strip():
        return None
    w, hh, _ = mtext_olcu(e)
    ap = e.dxf.get('attachment_point', 1)
    col, row = (ap - 1) % 3, (ap - 1) // 3
    x0 = (0.0, -0.5, -1.0)[col] * w
    y0 = (-1.0, -0.5, 0.0)[row] * hh
    rot = math.radians(e.dxf.get('rotation', 0) or 0)
    if e.dxf.hasattr('text_direction'):
        d = e.dxf.text_direction
        if abs(d[0]) + abs(d[1]) > 1e-9:
            rot = math.atan2(d[1], d[0])
    ins = e.dxf.insert
    yerel = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + hh), (x0, y0 + hh)]
    pg = Polygon(_dondur(yerel, (ins[0], ins[1]), rot))
    return pg if pg.is_valid and pg.area > 0 else None


def yazi_kutusu(e):
    """TEXT / ATTRIB / ATTDEF / MTEXT -> shapely Polygon (çizim koordinatı) veya None"""
    t = e.dxftype()
    try:
        if t in ('TEXT', 'ATTRIB', 'ATTDEF'):
            return text_kutusu(e)
        if t == 'MTEXT':
            return mtext_kutusu(e)
    except Exception:
        return None
    return None
