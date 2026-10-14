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
    m = mty_kontrol(out)
    print('MTY kontrolü:', 'TEMİZ (0 blok/katman/yazı)' if not m else m)


def mty_kontrol(dxf):
    """MTY geçen blok / katman / yazı stili / yazı / öznitelik listesi (boş = temiz)."""
    import ezdxf
    d = ezdxf.readfile(dxf)
    out = [f'blok {b.name}' for b in d.blocks if 'MTY' in b.name.upper()]
    out += [f'katman {l.dxf.name}' for l in d.layers if 'MTY' in l.dxf.name.upper()]
    out += [f'stil {s.dxf.name}' for s in d.styles if 'MTY' in s.dxf.name.upper()]
    for lay in [d.modelspace()] + list(d.blocks):
        for e in lay:
            t = e.text if e.dxftype() == 'MTEXT' else (e.dxf.get('text', '') if e.dxftype() in ('TEXT', 'ATTDEF') else '')
            if 'MTY' in str(t).upper():
                out.append(f'yazı {t[:40]}')
            if e.dxftype() == 'INSERT':
                out += [f'öznitelik {a.dxf.text}' for a in e.attribs if 'MTY' in a.dxf.text.upper()]
    return out


if __name__ == '__main__':
    main(sys.argv[1:])
