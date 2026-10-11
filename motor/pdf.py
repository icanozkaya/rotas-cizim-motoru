import pickle, prev, os
from design import LAYERS
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
R, fr, H = pickle.load(open('/tmp/claude-0/recs.pkl','rb'))
def one(i):
    (a,b,c,d),t,s = fr[i]
    out='/tmp/claude-0/pg/%02d.png'%i
    prev.render(R, LAYERS, (a,b,c,d), out, w=33*(c-a)/max(c-a,(d-b)*1.414), dpi=110)
    return out
order=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]
os.makedirs('/tmp/claude-0/pg',exist_ok=True)
with ProcessPoolExecutor(4) as ex:
    outs=list(ex.map(one, order))
ims=[Image.open(o).convert('RGB') for o in outs]
ims[0].save('/tmp/claude-0/out/preview.pdf', save_all=True, append_images=ims[1:], resolution=110)
print('ok')
