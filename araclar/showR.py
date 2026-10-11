import pickle, sys
sys.path.insert(0,'/home/claude/nb'); sys.path.insert(0,'/home/claude/nb/p2')
import prev, gp
from design import LAYERS
L=dict(LAYERS); L.update(gp.EXTRA_LAYERS); L.update({'MIMARI':(8,''),'MTY-PISSU-KOLONNO':(211,''),'RAST-TEM-SU DEPOSU':(11,'')})
R=pickle.load(open(sys.argv[1],'rb'))
if isinstance(R,tuple): R=R[0]
x0,y0,x1,y1=map(float,sys.argv[2:6]); out=sys.argv[6]; w=float(sys.argv[7]) if len(sys.argv)>7 else 20
prev.render(R,L,(x0,y0,x1,y1),out,w=w,dpi=100)
