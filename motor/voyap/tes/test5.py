import sys, pickle
sys.path.insert(0,'/home/claude/voyap'); sys.path.insert(0,'/home/claude/voyap/tes')
from tlib import *
sdoc = import_mty('/tmp/claude-0/vy/sih.dxf'); setup(sdoc)
import alt, sema_tes, hava
alt.OUTA.update(pickle.load(open('/tmp/claude-0/vy/outa.pkl','rb')))
sema_tes.sihhi_sema(); sema_tes.pis_sema(); sema_tes.isitma_sema(); sema_tes.kazan_sema()
yv = sema_tes.hava_sema(252700, -461100)
y = hava.notlar_hava(252700, yv - 200)
yy = sema_tes.lejant(259500, -461100, 'V'); yy = sema_tes.hava_tablo(259500, yy - 200)
y = sema_tes.lejant(263000, -461100, 'S'); y = sema_tes.lejant(263000, y - 120, 'H')
y2 = sema_tes.notlar(266500, -461100, "SIHHİ TESİSAT NOTLARI", sema_tes.NOT_S, 9.0)
y2 = sema_tes.notlar(266500, y2 - 120, "ISITMA TESİSATI NOTLARI", sema_tes.NOT_H, 9.0)
sema_tes.ozet_tablolar(266500, y2 - 150)
doc.saveas('/tmp/claude-0/vy/test_sema.dxf')
from onizle import render
render(doc,(258700,-447830,276720,-440320),'/tmp/claude-0/vy/inv/t5s.png',24,90,lays=())
render(doc,(289040,-447830,315160,-440320),'/tmp/claude-0/vy/inv/t5h.png',24,90,lays=())
render(doc,(252400,-468480,276720,-460960),'/tmp/claude-0/vy/inv/t5v.png',24,90,lays=())
