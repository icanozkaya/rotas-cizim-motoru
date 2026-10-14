# -*- coding: utf-8 -*-
"""Semboller (R2, 14.10.2026 B): MTY bloğu KULLANILMAZ. Sprinkler başlığı ve akış anahtarı Aselsan 02-Yangın lejant
geometrisinden (motor/voyap/asel_sym.pkl — yalnız OKUNUR) ROTAS- adlı saf geometri bloklar; izlenebilir kelebek vana
rotas_sembol.py (saf geometri)."""
import os, math, pickle

DEPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
ASL_PKL = os.path.join(DEPO, 'motor', 'voyap', 'asel_sym.pkl')

KELEBEK = 'ROTAS-SMB-IZLENEBILIR-KELEBEK'


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
    # R2: MTY bloğu YOK — izlenebilir kelebek vana saf geometri (rotas_sembol)
    import rotas_sembol as RS
    RS.blok_tanimla(doc, 'izlenebilir_kelebek')
    return dict(kelebek_mty=False)


# planda borunun kapladığı yarı boy (boru bu aralıkta kesilir) ve sembol kutusu (yarı genişlik, alt, üst) — cm
OLCU = {
    KELEBEK: dict(yari=10.0, kutu=(-10.0, -7.0, 10.0, 19.0)),
    'ROTAS-AKIS-ANAHTARI': dict(yari=16.3, kutu=(-16.3, -11.1, 16.3, 29.1)),
}
