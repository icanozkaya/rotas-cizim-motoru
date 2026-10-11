import pickle, prev, os
from design import LAYERS
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
R, fr, H = pickle.load(open('/tmp/claude-0/cg_recs.pkl','rb'))
order=[9,10,0,1,2,3,4,5,6,7,8]
def one(i):
    (a,b,c,d),t,s = fr[i]
    out='/tmp/claude-0/cgpg/%02d.png'%i
    w=16 if (c-a)<1500 else 24
    prev.render(R, LAYERS, (a,b,c,d), out, w=w, dpi=140)
    return out
os.makedirs('/tmp/claude-0/cgpg',exist_ok=True)
with ProcessPoolExecutor(4) as ex: outs=list(ex.map(one, order))
ims=[Image.open(o).convert('RGB') for o in outs]
ims[0].save('/tmp/claude-0/cgout/onizleme.pdf', save_all=True, append_images=ims[1:], resolution=140)
print(len(ims))
