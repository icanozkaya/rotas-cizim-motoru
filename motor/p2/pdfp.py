import sys, pickle, os
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import prev, design, gp, gklima
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
src, out = sys.argv[1], sys.argv[2]
_pk = pickle.load(open(src, 'rb'))
R, FR = _pk[:2]
TOP = {id(r) for b in (_pk[2] if len(_pk) > 2 else []) for r in b['recs']}
L = dict(design.LAYERS); L.update(gp.EXTRA_LAYERS)
L.update({'MTY-PIS SU-BASMA': (6, 'BASMA HATTI'), 'MTY-BINA-HATTI': (8, 'DASHED'), 'MTY-ISIKAYBIMAHAL': (2, 'CONTINUOUS'), 'MTY-RADYATÖR': (2, 'CONTINUOUS')})
order = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else list(range(len(FR)))
pg = out + '_pg'
os.makedirs(pg, exist_ok=True)


def one(i):
    (a, b, c, d), t, s = FR[i]
    o = '%s/%02d.png' % (pg, i)
    w = 16 if (c - a) < 1500 else 24
    prev.render(R, L, (a, b, c, d), o, w=w, dpi=140, top=TOP)
    return o


with ProcessPoolExecutor(4) as ex:
    outs = list(ex.map(one, order))
ims = [Image.open(o).convert('RGB') for o in outs]
ims[0].save(out, save_all=True, append_images=ims[1:], resolution=140)
print(len(ims), [FR[i][1] for i in order])
