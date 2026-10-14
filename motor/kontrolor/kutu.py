"""Gerçek yazı kutusu: ezdxf.tools.text_size (yazı tipi ölçüsü: genişlik faktörü, büyük harf yüksekliği, alt uzantı)
ile TEXT / ATTRIB / MTEXT kutusu; hizalama (halign/valign, MTEXT attachment_point) ve döndürme dahil.

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


def mtext_kutusu(e):
    try:
        s = e.plain_text()
    except Exception:
        s = ''
    if not (s or '').strip():
        return None
    h = e.dxf.get('char_height', 2.5) or 2.5
    satir = s.split('\n')
    w = hh = None
    if _TS is not None:
        try:
            ms = _TS.mtext_size(e)
            w, hh = ms.total_width, ms.total_height
        except Exception:
            w = None
    if not w or not hh:
        w = max(len(x) for x in satir) * h * 0.62
        hh = h * (1 + 1.667 * (len(satir) - 1))
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
