import pickle, numpy as np
from scipy.spatial import cKDTree
flat=pickle.load(open('/tmp/claude-0/nb_flat.pkl','rb'))
def pts(layers, bb, step):
    P=[]
    for k,l,d,p in flat:
        if l in layers and k in 'LP':
            seg = d if k=='P' else list(d)
            for i in range(len(seg)-1):
                a,b=np.array(seg[i]),np.array(seg[i+1])
                n=max(2,int(np.linalg.norm(b-a)/step))
                for t in np.linspace(0,1,n): P.append(a+(b-a)*t)
    P=np.array(P)
    m=(P[:,0]>bb[0])&(P[:,0]<bb[2])&(P[:,1]>bb[1])&(P[:,1]<bb[3])
    return P[m]
cati=pts({'MAHYA'},(92017,-11094,96467,-8094),10)
vaz=pts({'MAHYA'},(71102,-11094,74217,-8094),3)
print(len(cati),len(vaz))
# kümeler: x ile ayır
from scipy.cluster.vq import kmeans2
c,lab=kmeans2(vaz,2,seed=1,minit='++')
res={}
for k in range(2):
    V=vaz[lab==k]; print('cluster',k,V.mean(0),V.min(0),V.max(0))
    best=None
    for ang in np.arange(-180,180,2.0):
      for mir in (False,):
        a=np.radians(ang); R=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
        s=0.25
        C=(cati-cati.mean(0))@R.T*s + V.mean(0)
        t=cKDTree(V); d,_=t.query(C)
        sc=np.mean(np.minimum(d,20))
        if best is None or sc<best[0]: best=(sc,ang)
    # ICP refine
    sc,ang=best
    a=np.radians(ang); R=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]); s=0.25; T=V.mean(0)-(cati.mean(0)@R.T)*s
    t=cKDTree(V)
    for it in range(40):
        C=(cati@R.T)*s+T
        d,idx=t.query(C); m=d<10
        A=cati[m]; B=V[idx[m]]
        ma,mb=A.mean(0),B.mean(0)
        H=(A-ma).T@(B-mb); U,S_,Wt=np.linalg.svd(H); Rn=(Wt.T@U.T)
        if np.linalg.det(Rn)<0: Wt[1]*=-1; Rn=Wt.T@U.T
        sn=np.sum(S_)/np.sum((A-ma)**2)
        R,s=Rn,sn; T=mb-(ma@R.T)*s
    C=(cati@R.T)*s+T; d,_=t.query(C)
    print(' best ang',ang,'score',round(sc,2),'final s',round(s,4),'rot',round(np.degrees(np.arctan2(R[1,0],R[0,0])),2),'T',T,'resid',round(np.median(d),2))
    res[k]=(R,s,T,V.mean(0))
pickle.dump(res,open('/tmp/claude-0/vazfit.pkl','wb'))
