import pickle, sys, re
sys.path.insert(0,'/home/claude/nb')
import prev
def clean(t):
    t=re.sub(r'\\[A-Za-z][^;\\]*;','',t); t=re.sub(r'[{}]','',t); t=t.replace('\\P',' ')
    return t
def conv(flat, hmul=1.0):
    R=[]
    for r in flat:
        k=r[0]
        if k=='L': R.append(('L',r[1],r[2][0],r[2][1]))
        elif k=='P': R.append(('P',r[1],r[2],False,0))
        elif k=='C': R.append(('C',r[1],(r[2][0],r[2][1]),r[2][2]))
        elif k=='T': R.append(('T',r[1],r[2][0],clean(r[2][1]),r[2][2]*hmul,0,'L'))
    return R
if __name__=='__main__':
    flat=pickle.load(open(sys.argv[1],'rb'))
    x0,y0,x1,y1=map(float,sys.argv[2:6]); out=sys.argv[6]; w=float(sys.argv[7]); hm=float(sys.argv[8]) if len(sys.argv)>8 else 1
    prev.render(conv(flat,hm),{},(x0,y0,x1,y1),out,w=w,dpi=100)
