import sys, time, pickle
sys.path.insert(0,'/home/claude/voyap'); sys.path.insert(0,'/home/claude/voyap/tes')
t0=time.time()
from tlib import *
sdoc = import_mty('/tmp/claude-0/vy/sih.dxf')
setup(sdoc)
import alt
alt.zemin_sihhi(); print('zs', round(time.time()-t0))
alt.zemin_isitma(); print('zi', round(time.time()-t0))
alt.bodrum_sihhi(); print('bs', round(time.time()-t0))
alt.bodrum_isitma(); print('bi', round(time.time()-t0))
doc.saveas('/tmp/claude-0/vy/test_alt.dxf')
