import sys, mimari as M, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, random
from matplotlib.collections import LineCollection
b,k,out=sys.argv[1],sys.argv[2],sys.argv[3]
bbox=[float(v) for v in sys.argv[4].split(',')] if len(sys.argv)>4 else None
K=M.Kat(b,k)
x0,x1,y0,y1=K.k[2],K.k[3],K.k[4],K.k[5]
if bbox: x0,y0,x1,y1=bbox
W=30; fig=plt.figure(figsize=(W,W*(y1-y0)/(x1-x0))); ax=fig.add_axes([0,0,1,1])
segs=[]
for r in K.R:
    if r[1] in M.DUVAR_KATMAN and r[0] in 'LP': segs.append(r[2] if r[0]=='P' else list(r[2]))
ax.add_collection(LineCollection(segs,colors='#999',linewidths=0.4))
random.seed(1)
for m in K.mahal:
    g=m['poly']; c=(random.random(),random.random(),random.random())
    xs,ys=g.exterior.xy; ax.fill(xs,ys,color=c,alpha=0.35)
    ax.text(m['xy'][0],m['xy'][1],f"{m['ad']}\n{m['alan_cizim']:.1f}/{m['alan_mimari']}",fontsize=6)
ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.axis('off')
fig.savefig(out,dpi=90)
