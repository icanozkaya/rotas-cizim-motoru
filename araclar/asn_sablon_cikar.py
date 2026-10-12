"""Kullanıcının asansör örneklerinden kapak ve elektrik detayı şablonlarını çıkarır.

Kullanım:
  python3 asn_sablon_cikar.py kapak  <kapak.dxf>  <cikis.json>
  python3 asn_sablon_cikar.py elektrik <ornek.dxf> <cikis.json> x0 y0 x1 y1
Çıktı: yerel koordinatlı (sol-alt = 0,0) kayıt listesi; yazılar temizlenmiş, MTEXT satırlara bölünmüş.
"""
import json, math, re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'motor'))
import dxfparse as D


def oku(path):
    with open(path, 'rb') as f:
        head = f.read(4000).decode('latin-1')
    m = re.search(r'\$ACADVER\s*\n\s*1\s*\n(AC\d+)', head)
    D.ENC = 'utf-8' if (m and m.group(1) >= 'AC1021') else 'cp1254'
    # MTEXT 3 + 1 grup kodlarını birleştiren küçük yama
    orig = D.pairs
    def pairs(p):
        cur3, son1 = None, None
        for c, v in orig(p):
            if c == '0': cur3, son1 = None, None
            if c == '3':
                if son1 is not None:          # LibreDWG: 1'den sonra gelen 3 = devam metni
                    son1 += v
                    yield '1', son1
                else:
                    cur3 = (cur3 or '') + v
                continue
            if c == '1':
                if cur3 is not None: v = cur3 + v; cur3 = None
                son1 = v
            yield c, v
    D.pairs = pairs
    blocks, ents = D.read(path)
    return duzlestir(blocks, ents)


MT_ATT = {1: 'TL', 2: 'TC', 3: 'TR', 4: 'ML', 5: 'MC', 6: 'MR', 7: 'BL', 8: 'BC', 9: 'BR'}


def duzlestir(blocks, ents, depth=0, m=(1, 0, 0, 0, 1, 0), out=None, layer_over=None):
    """dxfparse.flatten + yazı hizası ve dönüş açısı."""
    if out is None: out = []
    for e in ents:
        t = e['_t']; lay = e.get('layer', '0')
        if lay == '0' and layer_over: lay = layer_over
        if t in ('TEXT', 'MTEXT', 'ATTRIB'):
            if t == 'MTEXT':
                x, y = e.get('10', 0), e.get('20', 0); al = MT_ATT.get(e.get('att', 1), 'TL')
            elif (e.get('ha', 0) or e.get('va', 0)) and '11' in e:
                x, y = e['11'], e.get('21', 0)
                al = {0: 'B', 1: 'B', 2: 'M', 3: 'T'}[e.get('va', 0)] + {0: 'L', 1: 'C', 2: 'R', 3: 'L', 4: 'C', 5: 'L'}[e.get('ha', 0)]
                if e.get('va', 0) == 0: al = al[1]
            else:
                x, y = e.get('10', 0), e.get('20', 0); al = 'L'
            sc = math.hypot(m[0], m[3])
            ang = (e.get('50', 0) if t != 'MTEXT' else 0) + math.degrees(math.atan2(m[3], m[0]))
            out.append(('T', lay, (D.xf(m, x, y), e.get('text', ''), e.get('40', 0) * sc), al, ang))
        elif t == 'INSERT' and depth < 6:
            nm = e.get('name')
            if nm not in blocks: continue
            base, sub = blocks[nm]
            sx, sy = e.get('41', 1.0), e.get('42', e.get('41', 1.0))
            r = math.radians(e.get('50', 0)); cr, sr = math.cos(r), math.sin(r)
            local = (cr * sx, -sr * sy, e.get('10', 0), sr * sx, cr * sy, e.get('20', 0))
            local = D.mul(local, (1, 0, -base[0], 0, 1, -base[1]))
            duzlestir(blocks, sub, depth + 1, D.mul(m, local), out, lay)
        else:
            D.flatten(blocks, [e], depth, m, out, layer_over)
    return out


def temizle(t):
    t = re.sub(r'\\U\+([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1), 16)), t)
    t = t.replace('\\P', '\n')
    t = re.sub(r'\\[AaCcFfHhQqTtWwpLlOoKk][^;\\{}]*;?', '', t)
    t = t.replace('{', '').replace('}', '').replace('%%c', 'Ø').replace('%%C', 'Ø').replace('%%d', '°').replace('%%D', '°')
    t = t.replace('%%u', '').replace('%%U', '').replace('%%p', '±')
    return t


def kayitlar(flat, pencere=None, sar=None):
    xs, ys = [], []
    out = []
    ins = (lambda p: True) if pencere is None else (lambda p: pencere[0] <= p[0] <= pencere[2] and pencere[1] <= p[1] <= pencere[3])
    for r in flat:
        k, lay = r[0], r[1]
        if k == 'L':
            if ins(r[2][0]) and ins(r[2][1]): out.append(['L', lay, list(r[2][0]), list(r[2][1])])
        elif k == 'P':
            if all(ins(p) for p in r[2]): out.append(['P', lay, [list(p) for p in r[2]], False])
        elif k == 'C':
            if ins(r[2][:2]): out.append(['C', lay, list(r[2][:2]), r[2][2]])
        elif k == 'T':
            p, s, h = r[2]
            al = r[3] if len(r) > 3 and isinstance(r[3], str) else 'L'
            ang = r[4] if len(r) > 4 and isinstance(r[4], (int, float)) else 0
            if abs(ang) < 0.01: ang = 0
            if not ins(p) or h <= 0: continue
            s = temizle(s)
            satirlar = []
            for parca in s.split('\n'):
                parca = parca.strip()
                if not parca: continue
                if sar and len(parca) > sar:
                    kel, cur = parca.split(' '), ''
                    for w in kel:
                        if len(cur) + len(w) + 1 > sar: satirlar.append(cur); cur = w
                        else: cur = (cur + ' ' + w).strip()
                    if cur: satirlar.append(cur)
                else:
                    satirlar.append(parca)
            n = len(satirlar)
            for i, sat in enumerate(satirlar):
                # çok satırlı MTEXT: üst hizalıysa aşağı, orta hizalıysa ortalanarak, alt hizalıysa yukarı dizilir
                if al.startswith('M'): dy = (i - (n - 1) / 2) * h * 1.55
                elif al.startswith('B'): dy = (i - (n - 1)) * h * 1.55
                else: dy = i * h * 1.55
                out.append(['T', lay, [p[0], p[1] - dy], sat, h, ang, al])
    for r in out:
        if r[0] == 'L': xs += [r[2][0], r[3][0]]; ys += [r[2][1], r[3][1]]
        elif r[0] == 'P': xs += [q[0] for q in r[2]]; ys += [q[1] for q in r[2]]
    x0, y0 = (pencere[0], pencere[1]) if pencere else (min(xs), min(ys))
    for r in out:
        if r[0] == 'L': r[2] = [r[2][0] - x0, r[2][1] - y0]; r[3] = [r[3][0] - x0, r[3][1] - y0]
        elif r[0] == 'P': r[2] = [[q[0] - x0, q[1] - y0] for q in r[2]]
        elif r[0] in 'CT': r[2] = [r[2][0] - x0, r[2][1] - y0]
    gen = (pencere[2] - pencere[0]) if pencere else max(xs) - x0
    yuk = (pencere[3] - pencere[1]) if pencere else max(ys) - y0
    return dict(gen=gen, yuk=yuk, kayitlar=out)


if __name__ == '__main__':
    tur, src, dst = sys.argv[1:4]
    flat = oku(src)
    if tur == 'kapak':
        d = kayitlar(flat, None, sar=95)
    else:
        x0, y0, x1, y1 = map(float, sys.argv[4:8])
        d = kayitlar(flat, (x0, y0, x1, y1))
    json.dump(d, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
    print(tur, round(d['gen'], 1), round(d['yuk'], 1), len(d['kayitlar']))
