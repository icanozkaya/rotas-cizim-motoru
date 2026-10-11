import pickle, sys, re
sys.path.insert(0,'/home/claude/nb'); sys.path.insert(0,'/tmp/claude-0/p2')
import prev
from rv import conv
flat=pickle.load(open(sys.argv[1],'rb'))
x0,y0,x1,y1=map(float,sys.argv[2:6]); out=sys.argv[6]; w=float(sys.argv[7]); hm=float(sys.argv[8]); st=float(sys.argv[9]) if len(sys.argv)>9 else 50
R=conv(flat,hm)
import math
gx=math.ceil(x0/st)*st
while gx<x1:
    R.append(('L','GRID',(gx,y0),(gx,y1),9 if gx%(st*4) else 3)); R.append(('T','GRID',(gx+2,y0+3),'%d'%gx,8,0,'L',1)); gx+=st
gy=math.ceil(y0/st)*st
while gy<y1:
    R.append(('L','GRID',(x0,gy),(x1,gy),9 if gy%(st*4) else 3)); R.append(('T','GRID',(x0+2,gy+2),'%d'%gy,8,0,'L',1)); gy+=st
prev.render(R,{'GRID':(9,'')},(x0,y0,x1,y1),out,w=w,dpi=100)
