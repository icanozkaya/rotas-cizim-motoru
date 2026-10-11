import pickle, sys, re
sys.path.insert(0,'/home/claude/nb')
from clean import clean
import rooms, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fl=pickle.load(open('/tmp/claude-0/cg_flat.pkl','rb'))
def detect(dx, out=None):
    BB=(-5700+dx,-23100,-4400+dx,-22100)
    inb=lambda p: BB[0]<p[0]<BB[2] and BB[1]<p[1]<BB[3]
    ents=[];labels=[];arcs=[]
    for k,l,d,p in fl:
        if k=='T':
            if l=='tefriş' and d[2]>=14 and inb(d[0]):
                labels.append((d[0][0],d[0][1],clean(d[1])))
            continue
        if l not in ('DUVAR','Kolon','kapı','sıva','SIVA'): continue
        q=d[0] if k in 'LP' else (d[0],d[1])
        if not inb(q): continue
        if l=='kapı' and k=='P' and len(d)>=5: arcs.append(d); continue
        ents.append((k,d))
    ents+=rooms.door_closures(arcs)
    R,g=rooms.detect(ents,labels,BB,door=30,res=1.0)
    if out:
        img=np.zeros((g.H,g.W,3),np.uint8); rng=np.random.default_rng(3)
        for i,r in R.items(): img[r['mask']]=rng.integers(60,255,3)
        w=rooms.raster_walls(g,ents); img[w>0]=255
        plt.figure(figsize=(12,10)); plt.imshow(img); plt.axis('off')
        for i,r in R.items():
            c,rr=g.px(r['xy']); plt.text(c,rr,r['name'][:14]+'\n%.2f'%r['area'],fontsize=8)
        plt.savefig(out,dpi=70,bbox_inches='tight')
    return R,g
if __name__=='__main__':
    R,g=detect(0,'/tmp/claude-0/cg_rooms.png')
    for i,r in R.items(): print(r['name'],round(r['area'],2),[round(v) for v in r['poly'].bounds])
