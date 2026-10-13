# -*- coding: utf-8 -*-
"""Kullanıcının ısıtma projesi: kazan dairesi güncel hesaba göre (2 x 65 kW kaskad, 200 lt genleşme, havalandırma menfezleri).
MTY dinamik blokları (*U) ham DXF'ten geri yazılır (ezdxf okurken düşürüyor)."""
import sys, pickle
sys.path.insert(0, '/home/claude/voyap/tes')
import ezdxf, ulabel
from ezdxf import recover, bbox
R = pickle.load(open('/tmp/claude-0/is/R.pkl', 'rb'))
src = '/tmp/claude-0/is/isitma.dxf'
doc, _ = recover.readfile(src); msp = doc.modelspace()
# 1) fazla kazanlar (3., 4., 5. kolon) kaldırılır — kolektörler yerinde kalır
X0, X1, Y0, Y1 = 327490, 327832, -499600, -499150
cache = bbox.Cache(); n = 0
for e in list(msp):
    try: b = bbox.extents([e], fast=True, cache=cache)
    except Exception: continue
    if not b.has_data: continue
    if X0 <= b.extmin.x and b.extmax.x <= X1 and Y0 <= b.extmin.y and b.extmax.y <= Y1:
        msp.delete_entity(e); n += 1
print('silinen kazan varlığı', n)
# 2) etiketler
REP = {'110 KW': f"{R['K_BIRIM']} KW", '1000 lt': f"{R['GT']} lt", '60×60 cm': R['ALT'][0][0].replace(' ', ''), '45×40 cm': R['UST'][0][0].replace(' ', '')}
for e in msp.query('TEXT MTEXT'):
    t = e.dxf.text if e.dxftype() == 'TEXT' else e.text
    for a, b_ in REP.items():
        if t.strip() == a:
            if e.dxftype() == 'TEXT': e.dxf.text = b_
            else: e.text = b_
# 3) MTY dinamik blokları geri yaz (silinen bölgedekiler hariç)
ulabel._C = '/tmp/claude-0/is/ul.pkl'
U = ulabel.oku(src)
kab = lambda u: not (X0 <= u['p'][0] <= X1 and Y0 <= u['p'][1] <= Y1)
nb, nt = ulabel.yaz(doc, doc, msp, U, kab)
print('MTY dinamik blok', nb, 'metin', nt)
doc.header['$INSUNITS'] = 5
doc.saveas('/tmp/claude-0/is/out/ISITMA_PROJESI.dxf'); print('ok')
