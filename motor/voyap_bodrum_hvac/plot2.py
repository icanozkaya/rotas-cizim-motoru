import pickle, sys, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
sys.path.insert(0,'/home/claude/vbs'); from flat import flatten
F=flatten(sys.argv[1]); out=sys.argv[2]
x0,y0,x1,y1=[float(v) for v in sys.argv[3:7]]; W=float(sys.argv[7])
fig=plt.figure(figsize=(W,W*(y1-y0)/(x1-x0))); ax=fig.add_axes([0,0,1,1])
C={'ROTAS-HVAC-OTP-EGZOZ':'red','ROTAS-HVAC-OTP-TAZE':'blue','ROTAS-HVAC-SIG-TAZE':'cyan','ROTAS-HVAC-SIG-EGZOZ':'magenta','ROTAS-HVAC-SIG-DUMAN':'orange','ROTAS-HVAC-MENFEZ':'green','ROTAS-HVAC-CIHAZ':'olive','ROTAS-HVAC-SAFT':'k','ROTAS-HVAC-OK':'red'}
S=[(L,a,b) for L,a,b in F['segs'] if max(a[0],b[0])>x0 and min(a[0],b[0])<x1 and max(a[1],b[1])>y0 and min(a[1],b[1])<y1]
ax.add_collection(LineCollection([(a,b) for L,a,b in S],colors=[C.get(L,'#999999' if not L.startswith('ROTAS') else 'k') for L,a,b in S],linewidths=[0.9 if L.startswith('ROTAS') else 0.5 for L,a,b in S]))
import ezdxf
d=ezdxf.readfile(sys.argv[1])
for e in d.modelspace().query('TEXT MTEXT'):
    p=e.dxf.insert if e.dxftype()=='MTEXT' else (e.dxf.align_point if e.dxf.halign or e.dxf.valign else e.dxf.insert)
    s=e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text
    h=e.dxf.char_height if e.dxftype()=='MTEXT' else e.dxf.height
    if x0<p[0]<x1 and y0<p[1]<y1:
        ha='left' if e.dxftype()=='MTEXT' or (e.dxf.halign==0) else 'center'
        ax.text(p[0],p[1],s,fontsize=h/(x1-x0)*W*72*0.75,rotation=e.dxf.get('rotation',0),ha=ha,va='center',color='k' if e.dxf.layer.startswith('ROTAS') else 'gray',rotation_mode='anchor')
ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.axis('off')
fig.savefig(out,dpi=110,facecolor='white')
