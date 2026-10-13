import sys, time
sys.path.insert(0,'/home/claude/voyap'); sys.path.insert(0,'/home/claude/voyap/tes')
from tlib import *
sdoc = import_mty('/tmp/claude-0/vy/sih.dxf'); setup(sdoc)
import hava
hava.bodrum_mim(); hava.zemin_mim(); hava.otopark(); hava.siginak(); hava.zemin_saft()
hava.notlar_hava(252500, -461200)
doc.saveas('/tmp/claude-0/vy/test_hava.dxf')
from onizle import render
render(doc,(248100,-468400,250200,-460900),'/tmp/claude-0/vy/inv/t4.png',14,110,lays=())
