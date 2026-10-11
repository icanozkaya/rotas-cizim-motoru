"""MTY blok kütüphanesi: DXF'ten geometri oku (birim, taban noktası)."""
import sys, os, pickle, re
sys.path.insert(0, '/home/claude/nb')
import dxfparse
BLK = '/tmp/claude-0/blk'


def ver(path):
    with open(path, 'rb') as f:
        head = f.read(3000).decode('latin-1')
    m = re.search(r'\$ACADVER\s*\r?\n\s*1\s*\r?\n(AC\d+)', head)
    return m.group(1) if m else 'AC1015'


def load(path):
    v = ver(path)
    dxfparse.ENC = 'utf-8' if v >= 'AC1021' else 'cp1254'
    b, e = dxfparse.read(path)
    fl = dxfparse.flatten(b, e)
    return fl, b, e


if __name__ == '__main__':
    out = {}
    for fn in sorted(os.listdir(BLK)):
        try:
            fl, b, e = load(os.path.join(BLK, fn))
        except Exception as ex:
            print('ERR', fn, ex); continue
        out[fn] = (fl, [x.get('_t') + ':' + str(x.get('name', '')) for x in e][:6])
    pickle.dump(out, open('/tmp/claude-0/blklib.pkl', 'wb'))
    for k, (fl, ents) in out.items():
        if 'SIHHI' in k:
            print(k[:70].ljust(70), len(fl), ents[:4])
