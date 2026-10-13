"""DXF katmanlarını SCOTT- önekine çevirir (0, Defpoints hariç; blok içleri ve öznitelikler dahil), ezdxf denetimi."""
import sys, ezdxf
src, dst = sys.argv[1:3]
d = ezdxf.readfile(src)
ren = {}
for l in list(d.layers):
    n = l.dxf.name
    if n in ('0', 'Defpoints') or n.upper().startswith('SCOTT'): continue
    ren[n] = 'SCOTT-' + n
for n, nn in ren.items():
    o = d.layers.get(n); nl = d.layers.add(nn)
    for a in ('color', 'linetype', 'lineweight', 'true_color', 'plot'):
        if o.dxf.hasattr(a): nl.dxf.set(a, o.dxf.get(a))
def fix(e):
    ly = e.dxf.get('layer', '0')
    if ly in ren: e.dxf.layer = ren[ly]
    elif ly not in ('0', 'Defpoints') and not ly.upper().startswith('SCOTT'):
        nn = 'SCOTT-' + ly
        if nn not in d.layers: d.layers.add(nn)
        e.dxf.layer = nn
    if e.dxftype() == 'INSERT':
        for a in e.attribs: fix(a)
for lo in d.layouts:
    for e in lo: fix(e)
for b in d.blocks:
    for e in b: fix(e)
for n in ren:
    try: d.layers.remove(n)
    except Exception: pass
d.saveas(dst)
d2 = ezdxf.readfile(dst)
au = d2.audit()
bad = [l.dxf.name for l in d2.layers if l.dxf.name not in ('0', 'Defpoints') and not l.dxf.name.startswith('SCOTT-')]
print('katman', len(d2.layers), 'öneksiz', bad, 'denetim hata', len(au.errors), 'düzeltme', len(au.fixes), 'INSERT', len(d2.modelspace().query('INSERT')), 'blok', len(d2.blocks))
