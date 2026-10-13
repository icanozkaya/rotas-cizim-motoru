import sys, time, pickle
sys.path.insert(0,'/home/claude/voyap'); sys.path.insert(0,'/home/claude/voyap/tes')
t0=time.time()
from tlib import *
sdoc = import_mty('/tmp/claude-0/vy/sih.dxf')
setup(sdoc)
import isitma
isitma.draw_ofis_isitma(int(sys.argv[1]))
print('çizim', round(time.time()-t0,1))
doc.saveas('/tmp/claude-0/vy/test_isi.dxf')
