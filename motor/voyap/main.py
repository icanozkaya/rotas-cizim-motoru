import sys, time, pickle
t0 = time.time()
from lib import *
from ezdxf import bbox as _bb
sdoc = import_mty('/tmp/claude-0/vy/sih.dxf')
define_blocks(); define_asel_blocks()
import plans
plans.bodrum_mimari()
AL = plans.build_plans()
plans.kopruler()
pickle.dump(AL, open('/tmp/claude-0/vy/all_lines.pkl', 'wb'))
import sema; sema.build()
doc.saveas('/tmp/claude-0/vy/YANGIN_EK.dxf')
print('EK ok', round(time.time() - t0, 1), 's')
# ---- TAM pafta: kullanıcının yangın sırasındaki mimari planları + çerçeve/başlıklar (kat planları silinmez)
X0, X1, Y0, Y1 = 248039, 276712, -458149, -450649
BOD = (248039, 250190)
cache = _bb.Cache()
sec = []
for e in sdoc.modelspace():
    lay = e.dxf.get('layer', '0')
    if lay.upper().startswith('MTY-SPRINKLER'): continue
    if e.dxftype() in ('VIEWPORT', 'OLE2FRAME', 'IMAGE'): continue
    try:
        b = _bb.extents([e], fast=True, cache=cache)
    except Exception:
        continue
    if not b.has_data: continue
    if not (X0 - 1 <= b.extmin.x and b.extmax.x <= X1 + 1 and Y0 - 1 <= b.extmin.y and b.extmax.y <= Y1 + 1): continue
    # eski bodrum mimarisi: güncel bodrum (MIM-BODRUM-GUNCEL) ile değiştirildi; çerçeve ve pafta başlığı kalır
    if BOD[0] < b.extmin.x and b.extmax.x < BOD[1] and lay != 'ANTED' and not (e.dxftype() in ('TEXT', 'MTEXT') and b.extmin.y < -457950):
        continue
    sec.append(e)
im = Importer(sdoc, doc)
im.import_entities(sec, msp); im.finalize()
doc.layers.get('MIM-BODRUM-GUNCEL').color = 8
doc.saveas('/tmp/claude-0/vy/YANGIN_TAM.dxf')
print('TAM ok', len(sec), 'mimari varlık', round(time.time() - t0, 1), 's')
