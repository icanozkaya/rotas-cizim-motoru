import sys, runpy, io, contextlib
sys.path.insert(0,'/home/claude/nb/p2'); sys.path.insert(0,'/home/claude/nb')
mod = sys.argv[1]
sys.argv=[mod]
f=io.StringIO()
with contextlib.redirect_stdout(f):
    g=runpy.run_path('/home/claude/nb/p2/'+mod, run_name='__main__')
import gp, xcheck
rep=xcheck.summary(xcheck.crossings())
SL=g['SLOTS']; dxf=g['dx']; HDY=g['HDY']; SLOT=g['SLOT']
for r in rep:
    x,y=r[3]
    sl=int(x//SLOT); k=[k for k,v in SL.items() if v==sl]; k=k[0] if k else '?'
    sx=x-(dxf(k) if k!='?' else 0)
    hy = y < (g.get('FY0', 15030.0)) - 100
    print(r[0], k+('-H' if hy else ''), r[1][4:], r[2][4:], (round(sx), round(y-(HDY if hy else 0))), r[4])
