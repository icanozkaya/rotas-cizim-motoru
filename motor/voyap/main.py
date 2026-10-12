import sys, time, pickle
t0 = time.time()
from lib import *
import_mty('/tmp/claude-0/vy/sih.dxf')
define_blocks()
import plans
plans.bodrum_mimari()
AL = plans.build_plans()
plans.kopruler()
pickle.dump(AL, open('/tmp/claude-0/vy/all_lines.pkl', 'wb'))
if '--sema' in sys.argv or True:
    try:
        import sema; sema.build()
    except ModuleNotFoundError as e:
        print('şema yok:', e)
doc.saveas('/tmp/claude-0/vy/YANGIN_EK.dxf')
print('ok', round(time.time() - t0, 1), 's')
