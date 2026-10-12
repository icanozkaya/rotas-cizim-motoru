import sys, os
sys.path.insert(0, '/home/claude/voyap'); os.chdir('/home/claude/voyap')
from prev import render
from geo import PAN, KATAD
from PIL import Image
VY = '/tmp/claude-0/vy/'
pages = []
for i, (a, b) in enumerate(PAN):
    f = VY + f'pg{i}.png'; render((a, -458149, b, -450649), f, 15, skip_bodrum=(i == 0), dpi=120); pages.append(f)
f = VY + 'pg_sema.png'; render((256650, -457200, 264000, -450900), f, 30, dpi=110); pages.append(f)
f = VY + 'pg_tab.png'; render((264200, -453400, 270600, -450700), f, 30, dpi=110); pages.append(f)
ims = [Image.open(p).convert('RGB') for p in pages]
ims[0].save(VY + 'out/VOYAP_YANGIN_ONIZLEME.pdf', save_all=True, append_images=ims[1:], resolution=120)
print('pdf ok')
