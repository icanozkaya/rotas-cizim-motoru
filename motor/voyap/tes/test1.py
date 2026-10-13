import sys, time, pickle
sys.path.insert(0,'/home/claude/voyap'); sys.path.insert(0,'/home/claude/voyap/tes')
t0=time.time()
from tlib import *
sdoc = import_mty('/tmp/claude-0/vy/sih.dxf')
setup(sdoc)
print('setup', round(time.time()-t0,1))
import sihhi
kat=int(sys.argv[1]) if len(sys.argv)>1 else 2
sihhi.draw_ofis_sihhi(kat)
print('çizim', round(time.time()-t0,1))
doc.saveas('/tmp/claude-0/vy/test_sihhi.dxf')
pickle.dump(sihhi.OUT, open('/tmp/claude-0/vy/test_out.pkl','wb'))
