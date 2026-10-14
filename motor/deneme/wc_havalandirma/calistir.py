"""Kullanım:
  python3 calistir.py <girdi.json> <cikti.dxf>          # hesap + çizim
  python3 calistir.py --nb <cikti.dxf>                   # new_block.dxf mimarisinden algıla (algila.py) + hesap + çizim
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hesap import hesapla   # noqa: E402
from ciz import pafta        # noqa: E402


def main(a):
    if a[0] == '--nb':
        from algila import algila
        gj = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nb_algilanan.json')
        g = algila(gj)
        out = a[1]
    else:
        g = json.load(open(a[0]))
        out = a[1]
    r = hesapla(g)
    k = pafta(g, r, out)
    for s in r['saftlar']:
        print(f"{s['ad']} {s['daireler']}: {s['Q']} m³/h, {s['w']}x{s['h']}, şaft {s['dp_saft']:.1f} Pa, "
              f"fan {s['p_fan']:.1f} Pa ({s['fan']['ad']}), kritik hat {s['kritik_top']:.1f} Pa")
    for u in r['uyari']:
        print('UYARI:', u)
    print('maske:', k['maske'], 'yazı çakışması:', k['yazi_cakisma'], '->', out)


if __name__ == '__main__':
    main(sys.argv[1:])
