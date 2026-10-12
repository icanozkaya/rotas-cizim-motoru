import pickle, sys
sys.path.insert(0, '/tmp/claude-0/vy/s'); from v import viewg
VY = '/tmp/claude-0/vy/'
Gm = pickle.load(open(VY + 'geo.pkl', 'rb')); H = pickle.load(open(VY + 'heads.pkl', 'rb')); R = pickle.load(open(VY + 'routes.pkl', 'rb'))
i = int(sys.argv[1]); y0, y1 = float(sys.argv[2]), float(sys.argv[3])
G = Gm[i]; x0, _, x1, _ = G['win']
F = [('L', 'W', (a, b), '') for a, b in G['walls']]
for c in getattr(G['cols'], 'geoms', [G['cols']]): F.append(('P', 'K', list(c.exterior.coords), ''))
for h in H[i]: F.append(('C', 'H', (h['p'][0], h['p'][1], 8), ''))
col = {'1"': '#00a0ff', '1 1/4"': '#00c060', '1 1/2"': '#c0a000', '2"': '#ff8000', '2 1/2"': '#ff0000', '3"': '#c00080', '4"': '#6000c0', '5"': '#000000', '6"': '#000000'}
if i in R:
    for e in R[i]['ts']['edges']: F.append(('L', e['cap'], (e['a'], e['b']), ''))
lc = dict(col); lc.update({'W': '#aaa', 'K': '#ff6060', 'H': 'red'})
viewg(F, (x0, y0, x1, y1), VY + f'g{i}_{int(-y0)}.png', 14, laycol=lc)
print(VY + f'g{i}_{int(-y0)}.png')
