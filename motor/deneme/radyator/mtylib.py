# -*- coding: utf-8 -*-
"""MTY blok kütüphanesinden (WBLOCK biçimli DXF'ler) blok tanımı alma — bloklar PATLATILMAZ,
hedef çizime gerçek blok tanımı + INSERT + öznitelik olarak girer."""
import os, glob
import ezdxf
from ezdxf.addons import Importer

BLKDIR = os.environ.get('MTY_BLKDIR', '/tmp/claude-0/blk')
_src = {}


def _bul(anahtar):
    """'RADYATOR TESISATI__KOLON ŞEMASI__MTY-RADYATOR KOLON' veya yalnız blok adı ('MTY-RADYATOR KOLON')"""
    p = os.path.join(BLKDIR, anahtar + '.dxf')
    if os.path.exists(p):
        return p
    c = sorted(glob.glob(os.path.join(BLKDIR, 'RADYATOR TESISATI__*__' + anahtar + '.dxf')))
    c += sorted(glob.glob(os.path.join(BLKDIR, '*__' + anahtar + '.dxf')))
    if not c:
        raise FileNotFoundError(f'MTY blok dosyası yok: {anahtar} ({BLKDIR})')
    return c[0]


def _oku(p):
    if p not in _src:
        _src[p] = ezdxf.readfile(p)
    return _src[p]


def wblock(doc, anahtar, ad=None):
    """Dosyanın model uzayını `ad` adlı blok tanımı yapar (taban noktası 0,0). Eksik anonim (*U) referanslar atlanır."""
    p = _bul(anahtar)
    ad = ad or os.path.basename(p)[:-4].split('__')[-1]
    if ad in doc.blocks:
        return ad
    s = _oku(p)
    hedef = doc.blocks.new(ad)
    im = Importer(s, doc)
    ents = [e for e in s.modelspace() if not (e.dxftype() == 'INSERT' and e.dxf.name not in s.blocks)]
    im.import_entities(ents, hedef)
    im.finalize()
    return ad


def ic_blok(doc, anahtar, blok):
    """Dosyanın içindeki adlandırılmış (iç) blok tanımını al."""
    if blok in doc.blocks:
        return blok
    s = _oku(_bul(anahtar))
    im = Importer(s, doc)
    im.import_block(blok)
    im.finalize()
    return blok


def ekle(msp, ad, p, rot=0.0, sx=1.0, sy=1.0, katman='0', ozn=None, ozn_h=None, ozn_rot=None, ozn_konum=None):
    """INSERT + öznitelikler (ATTDEF konumundan; ölçek sx≠sy ise yazı bozulmasın diye öznitelik yüksekliği sy ile)"""
    doc = msp.doc
    ins = msp.add_blockref(ad, (p[0], p[1]), dxfattribs={'layer': katman, 'rotation': rot, 'xscale': sx, 'yscale': sy})
    if ozn:
        m = ins.matrix44()
        for a in doc.blocks.get(ad).query('ATTDEF'):
            t = a.dxf.tag
            if t not in ozn:
                continue
            at = ins.add_attrib(t, str(ozn[t]), (0, 0))
            at.dxf.height = (ozn_h or {}).get(t, a.dxf.height * abs(sy))
            at.dxf.layer = a.dxf.layer
            if a.dxf.hasattr('color'):
                at.dxf.color = a.dxf.color
            if ozn_konum and t in ozn_konum:          # elle konum: orta-orta hizalı
                q = ozn_konum[t]
                at.dxf.insert = (q[0], q[1]); at.dxf.align_point = (q[0], q[1])
                at.dxf.halign = 1; at.dxf.valign = 2
            else:
                at.dxf.insert = m.transform(a.dxf.insert)
                if a.dxf.hasattr('align_point'):
                    at.dxf.align_point = m.transform(a.dxf.align_point)
                at.dxf.halign = a.dxf.get('halign', 0); at.dxf.valign = a.dxf.get('valign', 0)
            at.dxf.rotation = (ozn_rot if ozn_rot is not None else rot + a.dxf.get('rotation', 0))
            if a.dxf.get('style') and a.dxf.style in doc.styles:
                at.dxf.style = a.dxf.style
    return ins


def baglanti(doc, ad, katman_on_ek='MTY-ISITMA'):
    """blok içindeki ısıtma gidiş/dönüş çizgilerinin uç noktaları (bilgi amaçlı)"""
    out = {}
    for e in doc.blocks.get(ad):
        if e.dxftype() == 'LINE' and e.dxf.layer.startswith(katman_on_ek):
            out.setdefault(e.dxf.layer, []).append((tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]))
    return out
