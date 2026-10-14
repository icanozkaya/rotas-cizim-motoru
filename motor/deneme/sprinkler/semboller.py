# -*- coding: utf-8 -*-
"""Semboller: önce kullanıcının MTY blok kütüphanesi (/tmp/claude-0/blk), yoksa Aselsan 02-Yangın lejant
geometrisi (motor/voyap/asel_sym.pkl — yalnız OKUNUR) ve 03_SEMBOLLER.md tarifleri. Bloklar patlatılmaz."""
import os, math, pickle, tarfile
from ezdxf.addons.importer import Importer
import ezdxf

BLK = '/tmp/claude-0/blk'
DEPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
TAR = os.path.join(DEPO, 'kutuphane', 'ROTAS_2_MTY_BLOKLARI_2026-10-11.tar.xz')
ASL_PKL = os.path.join(DEPO, 'motor', 'voyap', 'asel_sym.pkl')

MTY_KELEBEK = 'SIHHI TESISAT__VANALAR__MTY-IZLENEBILIR KELEBEK VANA.dxf'


def _mty_dosya(ad):
    p = os.path.join(BLK, ad)
    if os.path.exists(p):
        return p
    if os.path.exists(TAR):                  # kurulum yapılmamışsa kütüphaneden çıkar
        with tarfile.open(TAR) as t:
            for m in t.getmembers():
                if m.name.endswith('/' + ad):
                    m.name = ad
                    t.extract(m, BLK)
                    return p
    return None


def mty_blok(doc, blok_adi, dosya):
    """MTY wblock dosyasının modelspace içeriğini aynı adlı blok olarak içe al (iç katmanlarıyla)"""
    if blok_adi in doc.blocks:
        return True
    p = _mty_dosya(dosya)
    if not p:
        return False
    s = ezdxf.readfile(p)
    b = doc.blocks.new(blok_adi)
    im = Importer(s, doc)
    im.import_entities(s.modelspace(), target_layout=b)
    im.finalize()
    return True


def _asl():
    return pickle.load(open(ASL_PKL, 'rb'))


def tanimla(doc):
    A = _asl()
    # sprinkler başlıkları — Aselsan lejantı: sarkık (pendent) iç içe çift daire, dik (upright) tek daire, Ø25
    if 'ROTAS-SPR-SARKIK' not in doc.blocks:
        b = doc.blocks.new('ROTAS-SPR-SARKIK')
        for pr in A['PENDENT SPRINKLER']['prim']:
            b.add_circle(pr[1][:2], pr[1][2], dxfattribs={'layer': '0'})
        b = doc.blocks.new('ROTAS-SPR-DIK')
        for pr in A['DİK TİP (UPRIGHT) SPRINKLER']['prim']:
            b.add_circle(pr[1][:2], pr[1][2], dxfattribs={'layer': '0'})
    # akış anahtarı — Aselsan lejantı "F.S" (borudaki paletli gövde), merkezlenmiş
    if 'ROTAS-AKIS-ANAHTARI' not in doc.blocks:
        pr_ = [pr for pr in A['FLOW SWITCH']['prim'] if (pr[0] in 'LP' and min(q[0] for q in pr[1]) > 20)]
        xs = [q[0] for pr in pr_ for q in pr[1]]
        ys = [q[1] for pr in pr_ for q in pr[1]]
        cx = (min(xs) + max(xs)) / 2
        cy = -6.6392           # papyon gövde ekseni boru eksenine oturur
        b = doc.blocks.new('ROTAS-AKIS-ANAHTARI')
        for pr in pr_:
            pts = [(q[0] - cx, q[1] - cy) for q in pr[1]]
            if pr[0] == 'L':
                b.add_line(pts[0], pts[1], dxfattribs={'layer': '0'})
            else:
                b.add_lwpolyline(pts, dxfattribs={'layer': '0'})
    # kolon (riser) planda: VOYAP onaylı çizimdeki gibi daire + dolu iç daire
    if 'ROTAS-SPR-KOLON' not in doc.blocks:
        b = doc.blocks.new('ROTAS-SPR-KOLON')
        b.add_circle((0, 0), 9, dxfattribs={'layer': '0'})
        b.add_circle((0, 0), 3, dxfattribs={'layer': '0'})
        h = b.add_hatch(dxfattribs={'layer': '0'})
        h.paths.add_polyline_path([(3 * math.cos(a / 8 * math.pi), 3 * math.sin(a / 8 * math.pi)) for a in range(16)],
                                  is_closed=True)
    kel = mty_blok(doc, 'MTY-IZLENEBILIR KELEBEK VANA', MTY_KELEBEK)
    if not kel and 'MTY-IZLENEBILIR KELEBEK VANA' not in doc.blocks:      # yedek: Aselsan lejantı
        b = doc.blocks.new('MTY-IZLENEBILIR KELEBEK VANA')
        for pr in A['İZLENEBİLİR KELEBEK VANA']['prim']:
            if pr[0] == 'L':
                b.add_line(pr[1][0], pr[1][1], dxfattribs={'layer': '0'})
            elif pr[0] == 'P':
                b.add_lwpolyline(pr[1], dxfattribs={'layer': '0'})
    return dict(kelebek_mty=kel)


# planda borunun kapladığı yarı boy (boru bu aralıkta kesilir) ve sembol kutusu (yarı genişlik, alt, üst) — cm
OLCU = {
    'MTY-IZLENEBILIR KELEBEK VANA': dict(yari=10.7, kutu=(-10.7, -5.1, 10.7, 13.9)),
    'ROTAS-AKIS-ANAHTARI': dict(yari=16.3, kutu=(-16.3, -11.1, 16.3, 29.1)),
}
