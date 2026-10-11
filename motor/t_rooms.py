import pickle, sys, re
sys.path.insert(0,'/home/claude/nb')
from clean import clean
import rooms, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
flat=pickle.load(open('/tmp/claude-0/nb_flat.pkl','rb'))
BB=(79100,-10450,82650,-8740)
WL={'A-WALL','S-COLS','Kapi_Pencere','A-GENM','S-STRS','A-DOOR'}
def inb(p): return BB[0]<p[0]<BB[2] and BB[1]<p[1]<BB[3]
ents=[];labels=[];arcs=[]
for k,l,d,p in flat:
    if k=='T':
        if l=='A-AREA-IDEN' and inb(d[0]):
            t=clean(d[1])
            if not t.startswith(('Alan','Döş','(')) and re.search(r'[A-ZÇĞİÖŞÜa-z]{3,}',t): labels.append((d[0][0],d[0][1],t))
        continue
    if l not in WL: continue
    q=d[0] if k in 'LP' else (d[0],d[1])
    if not inb(q): continue
    if l in ('A-DOOR','Kapi_Pencere') and k=='P' and len(d)>=5:
        arcs.append(d); continue
    if l=='A-DOOR': continue
    ents.append((k,d))
ents+=rooms.door_closures(arcs)
R,g=rooms.detect(ents,labels,BB,door=30)
print(len(labels),len(R))
for i,r in R.items(): print(i,r['name'],round(r['area'],2))
img=np.zeros((g.H,g.W,3),np.uint8)
rng=np.random.default_rng(1)
for i,r in R.items(): img[r['mask']]=rng.integers(60,255,3)
w=rooms.raster_walls(g,ents); img[w>0]=255
plt.figure(figsize=(30,15)); plt.imshow(img); plt.axis('off')
for i,r in R.items():
    c,rr=g.px(r['xy']); plt.text(c,rr,r['name'][:12]+'\n%.1f'%r['area'],fontsize=7,color='k')
plt.savefig('/tmp/claude-0/rooms.png',dpi=60,bbox_inches='tight')
pickle.dump({i:(r['name'],r['poly'],r['area'],r['xy']) for i,r in R.items()},open('/tmp/claude-0/rooms_A.pkl','wb'))
