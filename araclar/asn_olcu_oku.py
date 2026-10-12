"""Mimari DXF'teki DIMENSION (ölçü) varlıklarını blok dönüşümleriyle dünya koordinatına açar.
Kullanım: asn_olcu_oku.py mimari.dxf cikis.dims.pkl
Kayıt: (katman, p13, p14, p10, ölçülen değer, yazı). Kuyu dibi / kat yüksekliği gibi ölçüleri
kotlardan hesaplamak yerine doğrudan mimarın ölçüsünden okumak için kullanılır."""
import os, re, sys, pickle
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'motor'))
import dxfparse as D
path, out = sys.argv[1:3]
with open(path, 'rb') as f:
    head = f.read(4000).decode('latin-1')
m = re.search(r'\$ACADVER\s*\n\s*1\s*\n(AC\d+)', head)
D.ENC = 'utf-8' if (m and m.group(1) >= 'AC1021') else 'cp1254'
blocks, ents = D.read(path)
dims = [(r[1],) + tuple(r[2]) for r in D.flatten(blocks, ents) if r[0] == 'D']
pickle.dump(dims, open(out, 'wb'))
print(os.path.basename(path), len(dims), 'ölçü')
