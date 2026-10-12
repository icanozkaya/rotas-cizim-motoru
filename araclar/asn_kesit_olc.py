"""Asansör kesiti çözümleyici: kesit_olc.py flat.pkl cx  (cx: kesitteki 'MAKİNE DAİRESİZ ASANSÖR' yazısının x'i)
Kot yazılarından ±0.00 y'sini bulur; kuyu içindeki yatay çizgileri (döşeme, kuyu dibi, tavan) kot olarak listeler,
kuyu duvarlarını (düşey çizgiler) ve kapı boşluklarını verir."""
import pickle, sys, re, collections
fl = pickle.load(open(sys.argv[1], 'rb'))
cx = float(sys.argv[2]); cy = float(sys.argv[3]) if len(sys.argv) > 3 else None
# kot yazıları
kots = []
for r in fl:
    if r[0] == 'T':
        p = r[2][0]; s = r[2][1].strip()
        m = re.match(r'^([+\-±]?)\s?(\d{1,2})[.,](\d{2})\b', s.replace('%%p', '±'))
        if m and abs(p[0] - cx) < 800 and (cy is None or abs(p[1] - cy) < 2600):
            v = float(m.group(2) + '.' + m.group(3)) * (-1 if m.group(1) == '-' else 1)
            kots.append((v, p[1], p[0], s))
# en sık görülen ofset (y - 100*v)
ofs = collections.Counter(round(y - 100 * v) for v, y, x, s in kots)
y0 = ofs.most_common(1)[0][0]
print('±0.00 y =', y0, ' (kot yazısı sayısı', len(kots), ', destek', ofs.most_common(3), ')')
H = collections.defaultdict(set); V = collections.defaultdict(list)
for r in fl:
    if r[0] not in 'LP': continue
    p = list(r[2])
    for a, b in zip(p, p[1:]):
        if abs(a[1] - b[1]) < 0.3 and 150 < abs(a[0] - b[0]) < 260 and abs((a[0] + b[0]) / 2 - cx) < 400:
            z = (a[1] - y0) / 100
            if -6 < z < 25: H[round(z, 2)].add((round(min(a[0], b[0])), round(abs(a[0] - b[0])), r[1]))
        if abs(a[0] - b[0]) < 0.3 and abs(a[1] - b[1]) > 100 and abs(a[0] - cx) < 400:
            V[round(a[0])].append((round((min(a[1], b[1]) - y0) / 100, 2), round((max(a[1], b[1]) - y0) / 100, 2), r[1]))
print('KUYU KESİTİNDEKİ YATAY ÇİZGİLER (kot m: [x, genişlik cm, katman])')
for z in sorted(H): print(f'  {z:+7.2f}', sorted(H[z])[:4])
print('DÜŞEY ÇİZGİLER (x: [alt kot, üst kot])')
for x in sorted(V):
    segs = sorted(set((a, b) for a, b, l in V[x]))
    if len(segs) > 0: print(f'  x={x}', segs[:12])
print('KOTLAR:', sorted(set(s for v, y, x, s in kots), key=lambda s: float(re.sub(r'[^\d.\-]', '', s.split('(')[0].replace(',', '.').replace('±', '')) or 0))[:40])
