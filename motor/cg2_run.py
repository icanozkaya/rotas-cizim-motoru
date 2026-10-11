import pickle, sys
sys.path.insert(0, '/home/claude/nb')
import cad
from cad import *
import cg2_build as B
import cg2_check

R = cad.R
Y0, Y1 = B.OLD.SHEET_Y
HY0, HY1 = Y0 + B.HDY, Y1 + B.HDY

for k in range(4):
    B.put_floor_arch(k)
for k in range(3):
    B.put_floor_arch(k, B.HDY, furn=True, texts=False)
for i in range(3):
    B.sihhi_kat(i)
B.zemin_extra()
B.cati_plan()
for i in range(3):
    B.yagmur_kat(i)
B.yagmur_cati()
TEMEL = B.temel_plan()
HEAT = []
for i in range(3):
    HEAT.append(B.heat_floor(i))
stage = sys.argv[1] if len(sys.argv) > 1 else 'plans'
if stage != 'plans':
    import cg2_sheets as S
    FR = S.build(HEAT, Y0, Y1, HY0, HY1, TEMEL)
    pickle.dump((cad.R, FR, None), open('/tmp/claude-0/cg2_full.pkl', 'wb'))
rep = cg2_check.run(B.NET, B.NODES, B.HDY)
print('KONTROL:', len(rep))
for r in rep[:80]:
    print('  ', r)
pickle.dump((cad.R, HEAT), open('/tmp/claude-0/cg2_recs.pkl', 'wb'))
for i, (res, tot, calc) in enumerate(HEAT):
    print(i, round(tot), [(d['port'], d['zone'], round(d['W']), round(d['L'], 2), round(d['A'], 2)) for d in res])
