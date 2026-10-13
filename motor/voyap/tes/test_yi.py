import sys, time
sys.path.insert(0,'/home/claude/voyap/tes')
t0=time.time()
import yi, sihhi
from veri import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import odaplan as RM
D = sihhi.dolaplar(2)
ks = sys.argv[1:] or ['A1']
fig = plt.figure(figsize=(14,14)); ax=fig.add_axes([0,0,1,1]); ax.set_aspect('equal'); ax.axis('off')
X0=[];Y0=[];X1=[];Y1=[]
for k in ks:
    R = yi.ofis(2, k, D[k])
    b = Polygon(OFIS_S1[k]['poly']).bounds; X0.append(b[0]);Y0.append(b[1]);X1.append(b[2]);Y1.append(b[3])
    for c in R['circ']:
        p=c['path']; ax.plot([q[0] for q in p],[q[1] for q in p],lw=0.6)
        print(k, c['room']['name'], round(c['L'],1), round(c.get('W',0)), c['s'])
    for r in R['rooms']:
        ax.text(*r['poly'].representative_point().coords[0], r['name'], fontsize=6)
win=(min(X0)-50,min(Y0)-50,max(X1)+50,max(Y1)+50)
segs=RM.segs_in(win)
ax.add_collection(LineCollection(segs,colors='#999',linewidths=0.4))
ax.set_xlim(win[0],win[2]); ax.set_ylim(win[1],win[3])
fig.savefig('/tmp/claude-0/vy/inv/yi.png',dpi=110); print(round(time.time()-t0))
