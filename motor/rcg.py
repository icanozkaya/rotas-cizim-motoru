import sys, pickle
sys.path.insert(0,'/home/claude/gungoren')
import rend
rend._flat = pickle.load(open('/tmp/claude-0/cg_flat.pkl','rb'))
G=int(sys.argv[3]) if len(sys.argv)>3 else 0
x0,y0,x1,y1 = map(float, sys.argv[2].split(','))
def g(ax):
    if not G: return
    for x in range(int(x0)//G*G, int(x1)+1, G):
        ax.axvline(x,color='#ffb0b0',lw=0.3 if x%(G*5) else 0.8)
        if x%(G*5)==0: ax.text(x,y1-(y1-y0)*0.015,str(x),fontsize=6,color='r')
    for y in range(int(y0)//G*G, int(y1)+1, G):
        ax.axhline(y,color='#ffb0b0',lw=0.3 if y%(G*5) else 0.8)
        if y%(G*5)==0: ax.text(x0+2,y,str(y),fontsize=6,color='r')
rend.render(x0,y0,x1,y1, sys.argv[1], w=float(sys.argv[4]) if len(sys.argv)>4 else 16, minh=3, extra=[g])
