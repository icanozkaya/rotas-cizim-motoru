# -*- coding: utf-8 -*-
"""VOYAP yangın EK çizimi: ortak yardımcılar ve gerçek çizimli semboller (bloklar patlatılmaz)."""
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from ezdxf import recover
from ezdxf.addons import Importer

doc = ezdxf.new("R2018", setup=True)
doc.header["$INSUNITS"] = 5
doc.header["$LTSCALE"] = 1
msp = doc.modelspace()
doc.styles.add("ROTAS", font="arial.ttf")
doc.set_wipeout_variables(frame=0)

LAY = {
    "MTY-SPRINKLER-BORU": 140, "MTY-SPRINKLER-CAP": 141, "MTY-SPRINKLER": 15, "MTY-SPRINKLER-YAZI": 141,
    "MTY-SPRINKLER-NOZUL": 2, "MTY-SPRINKLER-ALAN": 2, "MTY-SPRINKLER-ALAN-1": 21,
    "MTY-YANGIN-DOLAP-BORU": 1, "MTY-YANGIN-DOLAP": 1, "MTY-YANGIN-KOLON": 6, "MTY-YANGIN-VANA": 1,
    "MTY-YANGIN-POMPA": 30, "MTY-YANGIN-DEPO": 4, "MTY-YANGIN-SEMA": 7, "MTY-YANGIN-YAZI": 7, "MTY-YANGIN-TABLO": 7,
    "MTY-YANGIN-ITFAIYE": 1, "MTY-YANGIN-MASKE": 7, "MTY-YANGIN-TARAMA": 8, "MIM-BODRUM-GUNCEL": 8, "MTY-YANGIN-NOT": 1,
    "MTY-VANA": 1, "MTY-SPRINKLER-KORUMA": 8,
}
for n, c in LAY.items():
    if n not in doc.layers: doc.layers.add(n, color=c)
doc.layers.get("MTY-YANGIN-MASKE").dxf.plot = 1
BORU, CAPL, DOLB, DOL, KOL, VAN, POM, DEP, SEM, YAZ, TAB, ITF, MSK = (
    "MTY-SPRINKLER-BORU", "MTY-SPRINKLER-CAP", "MTY-YANGIN-DOLAP-BORU", "MTY-YANGIN-DOLAP", "MTY-YANGIN-KOLON",
    "MTY-YANGIN-VANA", "MTY-YANGIN-POMPA", "MTY-YANGIN-DEPO", "MTY-YANGIN-SEMA", "MTY-YANGIN-YAZI", "MTY-YANGIN-TABLO",
    "MTY-YANGIN-ITFAIYE", "MTY-YANGIN-MASKE")

WD = {'DN25': 0.0, 'DN32': 0.0, 'DN40': 1.5, 'DN50': 2.0, 'DN65': 2.5, 'DN80': 3.0, 'DN100': 4.0, 'DN150': 5.0,
      '1"': 0.0, '1 1/4"': 0.0, '1 1/2"': 1.5, '2"': 2.0, '2 1/2"': 2.5, '3"': 3.0, '4"': 4.0, '6"': 5.0}


def T(x, y, s, h=10.0, lay=YAZ, al=TA.BOTTOM_LEFT, rot=0.0, mask=False, w=0.8):
    if mask:
        tw = len(s) * h * 0.62 * w + h * 0.4
        th = h * 1.5
        ax = {TA.BOTTOM_LEFT: 0, TA.BOTTOM_CENTER: 0.5, TA.MIDDLE_CENTER: 0.5, TA.BOTTOM_RIGHT: 1, TA.MIDDLE_LEFT: 0, TA.TOP_LEFT: 0, TA.TOP_CENTER: 0.5, TA.MIDDLE_RIGHT: 1, TA.TOP_RIGHT: 1}.get(al, 0)
        ay = {TA.MIDDLE_CENTER: 0.5, TA.MIDDLE_LEFT: 0.5, TA.MIDDLE_RIGHT: 0.5, TA.TOP_LEFT: 1, TA.TOP_CENTER: 1, TA.TOP_RIGHT: 1}.get(al, 0)
        x0 = -ax * tw - h * 0.2; y0 = -ay * h - h * 0.25
        a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
        pts = [(x0, y0), (x0 + tw, y0), (x0 + tw, y0 + th), (x0, y0 + th)]
        pts = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]
        if WIPE: msp.add_wipeout(pts, dxfattribs={"layer": MSK})
    t = msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": lay, "style": "ROTAS", "width": w})
    t.set_placement((x, y), align=al)
    return t


def PL(pts, lay, w=0.0, closed=False, ltscale=None):
    e = msp.add_lwpolyline([(p[0], p[1]) for p in pts], close=closed, dxfattribs={"layer": lay})
    if w: e.dxf.const_width = w
    if ltscale: e.dxf.ltscale = ltscale
    return e


def L(a, b, lay):
    return msp.add_line((a[0], a[1]), (b[0], b[1]), dxfattribs={"layer": lay})


def C(c, r, lay):
    return msp.add_circle((c[0], c[1]), r, dxfattribs={"layer": lay})


WIPE = False        # kullanıcı: 0 katmanında görünmeyen (wipeout) nesne istemiyor


def MASK(pts):
    if WIPE: msp.add_wipeout(pts, dxfattribs={"layer": MSK})


def MASKC(c, r):
    MASK([(c[0] + r * math.cos(a * math.pi / 8), c[1] + r * math.sin(a * math.pi / 8)) for a in range(16)])


# ------------------------------------------------------------------ MTY bloklarını kullanıcının dosyasından al
def import_mty(src_dxf):
    sdoc, _ = recover.readfile(src_dxf)
    im = Importer(sdoc, doc)
    im.import_blocks(["MTY-PENDANT TIP SPRINKLER-1", "MTY-UPRİGHT TIP SPRINKLER-1", "MTY-CEKVALF VANA", "MTY-KURESEL VANA"])
    im.finalize()
    return sdoc


def HEAD(p, typ, cap='DN25', no='1'):
    """Aselsan 02-Yangın lejantı: dik tip (upright) tek daire Ø25, pendent iç içe çift daire; koruma dairesi r=195 ayrı katmanda"""
    name = {'U': 'ASL-SPR-UP', 'P': 'ASL-SPR-PE', 'ARA': 'ASL-SPR-PE'}[typ]
    ins = msp.add_blockref(name, (p[0], p[1]), dxfattribs={"layer": "MTY-SPRINKLER"})
    msp.add_circle((p[0], p[1]), 195.0, dxfattribs={"layer": "MTY-SPRINKLER-KORUMA"})
    return ins


# ------------------------------------------------------------------ kendi sembollerim (blok olarak tanımlanır, INSERT edilir)
def _blk(name):
    if name in doc.blocks: return None
    return doc.blocks.new(name)


def define_blocks():
    # İzlenebilir kelebek vana (papyon + mil + izleme anahtarı), x ekseni boyunca, yarı boy 8
    b = _blk("Y-KELEBEK")
    if b is not None:
        b.add_lwpolyline([(-8, -5), (8, 5), (8, -5), (-8, 5)], close=True, dxfattribs={"layer": "0"})
        b.add_line((0, 0), (0, 10), dxfattribs={"layer": "0"})
        b.add_lwpolyline([(-4, 10), (4, 10), (4, 15), (-4, 15)], close=True, dxfattribs={"layer": "0"})
        b.add_line((-4, 10), (4, 15), dxfattribs={"layer": "0"})
    # OS&Y (yükselen milli) sürgülü vana
    b = _blk("Y-OSY")
    if b is not None:
        b.add_lwpolyline([(-8, -5), (8, 5), (8, -5), (-8, 5)], close=True, dxfattribs={"layer": "0"})
        b.add_line((0, 0), (0, 12), dxfattribs={"layer": "0"})
        b.add_line((-6, 12), (6, 12), dxfattribs={"layer": "0"})
        b.add_line((0, 12), (0, 17), dxfattribs={"layer": "0"})
    # Akış anahtarı (paleti boru içinde)
    b = _blk("Y-AKIS")
    if b is not None:
        b.add_circle((0, 0), 6, dxfattribs={"layer": "0"})
        b.add_line((0, -6), (0, -2), dxfattribs={"layer": "0"})
        b.add_line((0, -2), (3, 3), dxfattribs={"layer": "0"})
        b.add_text("FS", height=4, dxfattribs={"layer": "0", "style": "ROTAS"}).set_placement((0, 8), align=TA.BOTTOM_CENTER)
    # Islak alarm vanası (klape + su motorlu gong)
    b = _blk("Y-ALARM")
    if b is not None:
        b.add_circle((0, 0), 12, dxfattribs={"layer": "0"})
        b.add_line((-12, 0), (12, 0), dxfattribs={"layer": "0"})
        b.add_line((-8, -8), (6, 6), dxfattribs={"layer": "0"})
        b.add_line((12, 6), (24, 6), dxfattribs={"layer": "0"})
        b.add_circle((29, 6), 5, dxfattribs={"layer": "0"})
        b.add_circle((29, 6), 2, dxfattribs={"layer": "0"})
    # Manometre
    b = _blk("Y-MANO")
    if b is not None:
        b.add_line((0, 0), (0, 6), dxfattribs={"layer": "0"})
        b.add_circle((0, 11), 5, dxfattribs={"layer": "0"})
        b.add_line((0, 11), (3, 14), dxfattribs={"layer": "0"})
    # Pompa (daire + basma üçgeni) - basma +x
    b = _blk("Y-POMPA")
    if b is not None:
        b.add_circle((0, 0), 18, dxfattribs={"layer": "0"})
        b.add_lwpolyline([(-10, -13), (16, 0), (-10, 13)], close=True, dxfattribs={"layer": "0"})
    # Motor (pompa planında motor gövdesi)
    b = _blk("Y-MOTOR")
    if b is not None:
        b.add_lwpolyline([(-20, -14), (20, -14), (20, 14), (-20, 14)], close=True, dxfattribs={"layer": "0"})
        for k in range(-15, 20, 6): b.add_line((k, -14), (k, 14), dxfattribs={"layer": "0"})
    # Eksantrik redüksiyon (+x yönünde daralan)
    b = _blk("Y-RED")
    if b is not None:
        b.add_lwpolyline([(-6, -7), (6, -4), (6, 4), (-6, 7)], close=True, dxfattribs={"layer": "0"})
    # Membranlı tank
    b = _blk("Y-MTANK")
    if b is not None:
        b.add_circle((0, 0), 14, dxfattribs={"layer": "0"})
        b.add_line((-14, 0), (14, 0), dxfattribs={"layer": "0"})
        b.add_line((0, -14), (0, -20), dxfattribs={"layer": "0"})
    # Yangın dolabı (TS EN 671-1, duvar tipi, 80x25, hortum makarası + vana) - arka yüz y=0, oda tarafı +y
    b = _blk("Y-DOLAP")
    if b is not None:
        b.add_lwpolyline([(-40, 0), (40, 0), (40, 25), (-40, 25)], close=True, dxfattribs={"layer": "0"})
        b.add_circle((-8, 12.5), 10, dxfattribs={"layer": "0"})
        b.add_circle((-8, 12.5), 4, dxfattribs={"layer": "0"})
        b.add_lwpolyline([(18, 8), (30, 17), (30, 8), (18, 17)], close=True, dxfattribs={"layer": "0"})
        b.add_line((24, 12.5), (24, 22), dxfattribs={"layer": "0"})
        b.add_line((-40, 25), (40, 0), dxfattribs={"layer": "0"})
    # İtfaiye bağlantısı (2 x 2½" Storz, çek valf) - bina dışında, +x binaya
    b = _blk("Y-ITFAIYE")
    if b is not None:
        b.add_line((0, 0), (14, 0), dxfattribs={"layer": "0"})
        b.add_line((0, 0), (-12, 10), dxfattribs={"layer": "0"})
        b.add_line((0, 0), (-12, -10), dxfattribs={"layer": "0"})
        b.add_circle((-16, 13), 5, dxfattribs={"layer": "0"})
        b.add_circle((-16, -13), 5, dxfattribs={"layer": "0"})
    # Kolon (riser): daire + nokta
    b = _blk("Y-KOLON")
    if b is not None:
        b.add_circle((0, 0), 9, dxfattribs={"layer": "0"})
        b.add_circle((0, 0), 3, dxfattribs={"layer": "0"})
        h = b.add_hatch(dxfattribs={"layer": "0"}); h.paths.add_polyline_path([(3 * math.cos(a / 8 * math.pi), 3 * math.sin(a / 8 * math.pi)) for a in range(16)], is_closed=True)
    # Test / drenaj vanası (küresel + gözetleme camı)
    b = _blk("Y-TEST")
    if b is not None:
        b.add_lwpolyline([(-6, -4), (6, 4), (6, -4), (-6, 4)], close=True, dxfattribs={"layer": "0"})
        b.add_circle((0, 0), 2, dxfattribs={"layer": "0"})
        b.add_circle((14, 0), 4, dxfattribs={"layer": "0"})
        b.add_line((6, 0), (10, 0), dxfattribs={"layer": "0"})
    # Otomatik hava purjörü
    b = _blk("Y-PURJOR")
    if b is not None:
        b.add_line((0, 0), (0, 6), dxfattribs={"layer": "0"})
        b.add_lwpolyline([(-5, 6), (5, 6), (5, 14), (-5, 14)], close=True, dxfattribs={"layer": "0"})
        b.add_line((0, 14), (0, 18), dxfattribs={"layer": "0"})
    # Debimetre
    b = _blk("Y-DEBI")
    if b is not None:
        b.add_circle((0, 0), 8, dxfattribs={"layer": "0"})
        b.add_line((-5, -5), (5, 5), dxfattribs={"layer": "0"})
        b.add_lwpolyline([(5, 5), (1, 4), (4, 1)], close=True, dxfattribs={"layer": "0"})
    # Emniyet (tahliye) vanası
    b = _blk("Y-EMNIYET")
    if b is not None:
        b.add_lwpolyline([(-5, 0), (5, 0), (0, 9)], close=True, dxfattribs={"layer": "0"})
        b.add_lwpolyline([(0, 9), (9, 4), (9, 14)], close=True, dxfattribs={"layer": "0"})
        b.add_line((0, 9), (0, 16), dxfattribs={"layer": "0"})
        b.add_lwpolyline([(-3, 16), (3, 18), (-3, 20), (3, 22)], dxfattribs={"layer": "0"})
    # Basınç anahtarı
    b = _blk("Y-PS")
    if b is not None:
        b.add_line((0, 0), (0, 6), dxfattribs={"layer": "0"})
        b.add_lwpolyline([(-6, 6), (6, 6), (6, 14), (-6, 14)], close=True, dxfattribs={"layer": "0"})
        b.add_text("PS", height=4, dxfattribs={"layer": "0", "style": "ROTAS"}).set_placement((0, 10), align=TA.MIDDLE_CENTER)
    # Seviye göstergesi / şamandıra
    b = _blk("Y-SAMANDIRA")
    if b is not None:
        b.add_lwpolyline([(-6, -4), (6, 4), (6, -4), (-6, 4)], close=True, dxfattribs={"layer": "0"})
        b.add_line((6, 0), (20, -14), dxfattribs={"layer": "0"})
        b.add_circle((24, -18), 6, dxfattribs={"layer": "0"})
    # Girdap önleyici (anti-vortex) plaka
    b = _blk("Y-VORTEX")
    if b is not None:
        b.add_line((-14, 0), (14, 0), dxfattribs={"layer": "0"})
        b.add_line((-14, 2), (14, 2), dxfattribs={"layer": "0"})
    # Pano
    b = _blk("Y-PANO")
    if b is not None:
        b.add_lwpolyline([(-30, 0), (30, 0), (30, 25), (-30, 25)], close=True, dxfattribs={"layer": "0"})
        b.add_lwpolyline([(-30, 0), (30, 25)], dxfattribs={"layer": "0"})
        b.add_circle((-18, 12.5), 4, dxfattribs={"layer": "0"})
        b.add_circle((0, 12.5), 4, dxfattribs={"layer": "0"})
    # Yakıt tankı
    b = _blk("Y-YAKIT")
    if b is not None:
        b.add_lwpolyline([(-30, -18), (30, -18), (30, 18), (-30, 18)], close=True, dxfattribs={"layer": "0"})
        b.add_line((-30, -18), (30, 18), dxfattribs={"layer": "0"})
        b.add_line((-30, 18), (30, -18), dxfattribs={"layer": "0"})
    # Şema/lejant sprinkler sembolleri (MTY bloğunun nozul kısmı ile aynı görünüm, kapsama dairesiz)
    b = _blk("Y-SPR-U")
    if b is not None:
        b.add_circle((0, 0), 4.2, dxfattribs={"layer": "0"})
        b.add_circle((0, 0), 9.0, dxfattribs={"layer": "0"})
        b.add_line((-9, 9), (9, 9), dxfattribs={"layer": "0"})
        b.add_line((0, 0), (0, 9), dxfattribs={"layer": "0"})
    b = _blk("Y-SPR-P")
    if b is not None:
        b.add_circle((0, 0), 4.2, dxfattribs={"layer": "0"})
        b.add_circle((0, 0), 9.0, dxfattribs={"layer": "0"})
        h = b.add_hatch(dxfattribs={"layer": "0"}); h.paths.add_polyline_path([(4.2 * math.cos(a / 8 * math.pi), 4.2 * math.sin(a / 8 * math.pi)) for a in range(16)], is_closed=True)
        b.add_line((-9, -9), (9, -9), dxfattribs={"layer": "0"})
    # Gözetleme camı
    b = _blk("Y-CAM")
    if b is not None:
        b.add_circle((0, 0), 5, dxfattribs={"layer": "0"})
        b.add_line((-3, -3), (3, 3), dxfattribs={"layer": "0"})


def INS(name, p, rot=0.0, s=1.0, lay=VAN, mask=None):
    if mask: MASKC(p, mask)
    if name in ALIAS:
        name, k_ = ALIAS[name]; s = s * k_
    return msp.add_blockref(name, (p[0], p[1]), dxfattribs={"layer": lay, "rotation": rot, "xscale": s, "yscale": s})


def CEK(p, rot=0.0, s=1.0, lay=VAN, mask=None):
    if mask: MASKC(p, mask)
    if "ASL-CEK" in doc.blocks:
        return msp.add_blockref("ASL-CEK", (p[0], p[1]), dxfattribs={"layer": lay, "rotation": rot, "xscale": s * 0.45, "yscale": s * 0.45})
    return msp.add_blockref("MTY-CEKVALF VANA", (p[0], p[1]), dxfattribs={"layer": lay, "rotation": rot, "xscale": s, "yscale": s})


def KURESEL(p, rot=0.0, s=1.0, lay=VAN, mask=None):
    if mask: MASKC(p, mask)
    return msp.add_blockref("MTY-KURESEL VANA", (p[0], p[1]), dxfattribs={"layer": lay, "rotation": rot, "xscale": s, "yscale": s})


def ARROW(p, ang, lay, size=12):
    a = math.radians(ang)
    tip = (p[0] + size * math.cos(a) * 0.5, p[1] + size * math.sin(a) * 0.5)
    l = (p[0] - size * 0.5 * math.cos(a) - size * 0.3 * math.sin(a), p[1] - size * 0.5 * math.sin(a) + size * 0.3 * math.cos(a))
    r = (p[0] - size * 0.5 * math.cos(a) + size * 0.3 * math.sin(a), p[1] - size * 0.5 * math.sin(a) - size * 0.3 * math.cos(a))
    h = msp.add_hatch(dxfattribs={"layer": lay}); h.paths.add_polyline_path([tip, l, r], is_closed=True)


def HATCH_RECT(x0, y0, x1, y1, lay):
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, closed=True)
    h = msp.add_hatch(dxfattribs={"layer": "MTY-YANGIN-TARAMA"})
    h.set_pattern_fill("ANSI31", scale=1.5)
    h.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)


# ------------------------------------------------------------------ Aselsan 02-Yangın lejant sembolleri (bloklar)
import pickle as _pk, os as _os
ASL = _pk.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'asel_sym.pkl'), 'rb'))
ASL_AD = {'KELEBEK VANA': 'ASL-KELEBEK', 'İZLENEBİLİR KELEBEK VANA': 'ASL-IZL-KELEBEK', 'YÜKSELEN MİLLİ VANA': 'ASL-OSY',
          'ÇEK VANA': 'ASL-CEK', 'PISLIK TUTUCU': 'ASL-PISLIK', 'KOMPANSATÖR': 'ASL-KOMP', 'TEST DRENAJ SETİ': 'ASL-TEST',
          'İTFAİYE BAĞLANTI AĞZI / 2 x 2 1/2"': 'ASL-ITFAIYE', 'ISLAK ALARM VANA ISTASYONU': 'ASL-WAV',
          'BASINÇ DÜŞÜRÜCÜ DENGELEME VANASI': 'ASL-BDV', 'MANOMETRE': 'ASL-MANO', 'POST İNDİKATÖR VANA': 'ASL-PIV',
          'YANGIN DOLABI (KAT PLANI)': 'ASL-YD-PLAN', 'YANGIN DOLABI (KOLON ŞEMASI)': 'ASL-YD-KOLON'}


def define_asel_blocks():
    for key, ad in ASL_AD.items():
        if ad in doc.blocks or key not in ASL: continue
        b = doc.blocks.new(ad)
        prim = ASL[key]['prim']
        if key == 'İTFAİYE BAĞLANTI AĞZI / 2 x 2 1/2"':
            pass
        for pr in prim:
            if pr[0] == 'L': b.add_line(pr[1][0], pr[1][1], dxfattribs={"layer": "0"})
            elif pr[0] == 'P': b.add_lwpolyline(pr[1], dxfattribs={"layer": "0"})
            elif pr[0] == 'C':
                if pr[1][2] <= max(ASL[key]['w'], ASL[key]['h']): b.add_circle(pr[1][:2], pr[1][2], dxfattribs={"layer": "0"})
            elif pr[0] == 'T' and pr[3] > 0:
                t = b.add_text(str(pr[2]), height=pr[3], dxfattribs={"layer": "0", "style": "ROTAS"}); t.set_placement(pr[1])
    # flow switch: lejanttaki iki sembolden vanalı olan (F.S)
    if 'ASL-FS' not in doc.blocks and 'FLOW SWITCH' in ASL:
        pr_ = [pr for pr in ASL['FLOW SWITCH']['prim'] if (pr[0] in 'LP' and min(q[0] for q in pr[1]) > 20) or (pr[0] == 'C' and pr[1][0] > 20) or (pr[0] == 'T' and pr[1][0] > 0)]
        xs = [q[0] for pr in pr_ if pr[0] in 'LP' for q in pr[1]]; ys = [q[1] for pr in pr_ if pr[0] in 'LP' for q in pr[1]]
        cx = (min(xs) + max(xs)) / 2; cy = (min(ys) + max(ys)) / 2
        b = doc.blocks.new('ASL-FS')
        for pr in pr_:
            if pr[0] == 'L': b.add_line((pr[1][0][0] - cx, pr[1][0][1] - cy), (pr[1][1][0] - cx, pr[1][1][1] - cy), dxfattribs={"layer": "0"})
            elif pr[0] == 'P': b.add_lwpolyline([(q[0] - cx, q[1] - cy) for q in pr[1]], dxfattribs={"layer": "0"})
            elif pr[0] == 'C': b.add_circle((pr[1][0] - cx, pr[1][1] - cy), pr[1][2], dxfattribs={"layer": "0"})
    # sprinkler başlıkları (Aselsan plan sembolü ölçüsünde: Ø25)
    if 'ASL-SPR-UP' not in doc.blocks:
        b = doc.blocks.new('ASL-SPR-UP'); b.add_circle((0, 0), 12.5, dxfattribs={"layer": "0"})
        b = doc.blocks.new('ASL-SPR-PE'); b.add_circle((0, 0), 12.5, dxfattribs={"layer": "0"}); b.add_circle((0, 0), 5.0, dxfattribs={"layer": "0"})


# eski sembol adı -> (Aselsan bloğu, ölçek)
ALIAS = {'Y-KELEBEK': ('ASL-IZL-KELEBEK', 0.45), 'Y-OSY': ('ASL-OSY', 0.45), 'Y-ALARM': ('ASL-WAV', 0.30), 'Y-AKIS': ('ASL-FS', 0.40),
         'Y-TEST': ('ASL-TEST', 0.30), 'Y-MANO': ('ASL-MANO', 0.40), 'Y-ITFAIYE': ('ASL-ITFAIYE', 0.30), 'Y-SPR-U': ('ASL-SPR-UP', 0.8),
         'Y-SPR-P': ('ASL-SPR-PE', 0.8)}
