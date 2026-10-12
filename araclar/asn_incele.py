"""Asansör örnek DXF'lerini incele: yazı dökümü, katman istatistiği, önizleme PNG."""
import sys, os, re, math, collections, pickle
sys.path.insert(0, os.path.dirname(__file__))
import dxfparse as D
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


def enc_of(path):
    with open(path, 'rb') as f:
        head = f.read(4000).decode('latin-1')
    m = re.search(r'\$ACADVER\s*\n\s*1\s*\n(AC\d+)', head)
    v = m.group(1) if m else 'AC1018'
    return 'utf-8' if v >= 'AC1021' else 'cp1254'


def clean(t):
    t = re.sub(r'\\U\+([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1), 16)), t)
    t = re.sub(r'\\[AaCcFfHhQqTtWw][^;]*;', '', t)
    t = t.replace('\\P', ' / ').replace('{', '').replace('}', '').replace('%%c', 'Ø').replace('%%C', 'Ø')
    t = t.replace('%%d', '°').replace('%%p', '±').replace('\\L', '').replace('\\l', '')
    return t.strip()


def main(path, outdir):
    D.ENC = enc_of(path)
    blocks, ents = D.read(path)
    flat = D.flatten(blocks, ents)
    base = os.path.splitext(os.path.basename(path))[0]
    pickle.dump(flat, open(os.path.join(outdir, base + '.flat.pkl'), 'wb'))
    lay = collections.Counter(r[1] for r in flat)
    ins = collections.Counter(e.get('name') for e in ents if e['_t'] == 'INSERT')
    texts = [(r[2][0], clean(r[2][1]), r[2][2], r[1]) for r in flat if r[0] == 'T' and clean(r[2][1])]
    with open(os.path.join(outdir, base + '.txt'), 'w') as f:
        f.write(f'# {path}\n# enc {D.ENC}  ents {len(ents)} flat {len(flat)} blocks {len(blocks)}\n')
        f.write('# LAYERS: ' + ', '.join(f'{k}:{v}' for k, v in lay.most_common(60)) + '\n')
        f.write('# TOP INSERTS: ' + ', '.join(f'{k}:{v}' for k, v in ins.most_common(60)) + '\n')
        seen = set()
        for p, s, h, l in sorted(texts, key=lambda x: (-round(x[0][1] / 50), x[0][0])):
            k = s
            if k in seen: continue
            seen.add(k)
            f.write(f'{p[0]:.0f},{p[1]:.0f} h{h:.1f} [{l}] {s}\n')
    # extents (robust)
    xs, ys = [], []
    for r in flat:
        if r[0] == 'L': xs += [r[2][0][0], r[2][1][0]]; ys += [r[2][0][1], r[2][1][1]]
        elif r[0] == 'P': xs += [p[0] for p in r[2]]; ys += [p[1] for p in r[2]]
    if not xs: return
    xs.sort(); ys.sort(); n = len(xs)
    lo, hi = int(n * 0.002), int(n * 0.998) - 1
    x0, x1, y0, y1 = xs[lo], xs[hi], ys[lo], ys[hi]
    W = 30
    H = max(4, min(60, W * (y1 - y0) / max(1e-6, x1 - x0)))
    fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1])
    segs = []
    for r in flat:
        if r[0] == 'L': segs.append([r[2][0], r[2][1]])
        elif r[0] == 'P': segs.append(r[2])
        elif r[0] == 'C':
            cx, cy, rr = r[2]
            segs.append([(cx + rr * math.cos(t / 12 * math.pi), cy + rr * math.sin(t / 12 * math.pi)) for t in range(25)])
    ax.add_collection(LineCollection(segs, colors='k', linewidths=0.25))
    ppu = W * 100 / (x1 - x0)
    for p, s, h, l in texts:
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and h * ppu > 3:
            ax.text(p[0], p[1], s[:60], fontsize=max(2, h * ppu * 0.6), color='b')
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off')
    fig.savefig(os.path.join(outdir, base + '.png'), dpi=100); plt.close(fig)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
