import pickle, sys
import cad
from design import *
import prev
arch = pickle.load(open('/tmp/claude-0/arch_clean.pkl','rb'))
def put_arch(sheet, dx=0, dy=0, furn=True):
    from arch import FURN
    for k,d,l in arch[sheet]:
        if not furn and l in FURN: continue
        if k=='L': cad.R.append(('L','MIMARI',(d[0][0]+dx,d[0][1]+dy),(d[1][0]+dx,d[1][1]+dy)))
        elif k=='P': cad.R.append(('P','MIMARI',[(x+dx,y+dy) for x,y in d],False,0))
        elif k=='C': cad.R.append(('C','MIMARI',(d[0]+dx,d[1]+dy),d[2]))
        elif k=='T': cad.R.append(('T','MIMARI',(d[0][0]+dx,d[0][1]+dy),d[1],d[2],0,'L'))
put_arch('A-ZEM')
for no in range(1,8):
    tip,n = daire_tf(no,0)
    sihhi_daire(no,tip,no)
    pop_n(n)
    corridor(no,no,0,(0,0))
sayac_grubu(0,(0,0),'7 x 4.50 = 31.50 YB')
put_arch('A-ZEM',0,HEAT_DY,False)
z=0
for no in range(1,8):
    tip,n = daire_tf(no,0,(0,HEAT_DY))
    res,tot,z = isitma_daire(no,tip,1.15,z,'Z')
    pop_n(n)
win=tuple(map(float,sys.argv[2].split(',')))
prev.render(cad.R, LAYERS, win, sys.argv[1], w=float(sys.argv[3]) if len(sys.argv)>3 else 20)
