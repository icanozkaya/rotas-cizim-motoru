import sys, pickle
sys.path.insert(0,'/home/claude/gungoren')
import rend
rend._flat = pickle.load(open('/tmp/claude-0/nb_flat.pkl','rb'))
def g(ax):
    import numpy as np
    for x in range(int(x0)//G*G, int(x1)+1, G):
        ax.axvline(x,color='#ffb0b0',lw=0.3 if x%(G*5) else 0.7); 
        if x%(G*5)==0: ax.text(x,y1-(y1-y0)*0.015,str(x),fontsize=6,color='r')
    for y in range(int(y0)//G*G, int(y1)+1, G):
        ax.axhline(y,color='#ffb0b0',lw=0.3 if y%(G*5) else 0.7)
        if y%(G*5)==0: ax.text(x0+2,y,str(y),fontsize=6,color='r')
G=int(sys.argv[3]) if len(sys.argv)>3 else 50
x0,y0,x1,y1 = map(float, sys.argv[2].split(','))
rend.render(x0,y0,x1,y1, sys.argv[1], w=14, minh=5, extra=[g])
