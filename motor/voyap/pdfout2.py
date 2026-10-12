import sys, os
sys.argv = ['x', '/tmp/claude-0/vy/YANGIN_TAM.dxf']
sys.path.insert(0, '/home/claude/voyap'); os.chdir('/home/claude/voyap')
from prev2 import render
from geo import PAN
from PIL import Image
VY = '/tmp/claude-0/vy/'
pages = []
for i, (a, b) in enumerate(PAN):
    f = VY + f'tg{i}.png'; render((a, -458149, b, -450649), f, 15, dpi=120); pages.append(f)
f = VY + 'tg_sema.png'; render((256650, -457200, 264000, -450900), f, 30, dpi=110); pages.append(f)
f = VY + 'tg_tab.png'; render((264200, -455000, 270800, -450700), f, 30, dpi=110); pages.append(f)
ims = [Image.open(p).convert('RGB') for p in pages]
ims[0].save(VY + 'out/VOYAP_YANGIN_ONIZLEME.pdf', save_all=True, append_images=ims[1:], resolution=120)
print('pdf ok')
