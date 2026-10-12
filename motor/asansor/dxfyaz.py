"""Bağımlılıksız DXF R12 (AC1009, ANSI_1254) yazıcı + matplotlib önizleme.

ezdxf kurulamayan oturumlar için. AutoCAD R12 DXF'i doğrudan açar; DWG'ye
AutoCAD'de SAVEAS (veya depo içindeki ACadSharp aracı) ile çevrilir.
Kayıtlar: ('L',lay,p1,p2) ('P',lay,pts,kapali) ('C',lay,merkez,r) ('A',lay,merkez,r,a0,a1)
          ('T',lay,p,metin,h,aci,hiza)  hiza: 'L','C','R','ML','MC','MR','TL','TC','TR','BL','BC','BR'
"""
import math

ESC = {'≤': '<=', '≥': '>=', 'Σ': 'Top.', '·': '.', 'Ø': '%%c', 'ø': '%%c', '°': '%%d', '±': '%%p',
       '⌈': '', '⌉': '', '–': '-', '—': '-', '’': "'", '“': '"', '”': '"', '…': '...', '√': 'kok', '×': 'x',
       '²': '2', '³': '3', '…': '...'}


def esc(s):
    out = []
    for ch in s:
        ch = ESC.get(ch, ch)
        try:
            ch.encode('cp1254'); out.append(ch)
        except UnicodeEncodeError:
            out.append('?')
    return ''.join(out)


class Cizim:
    def __init__(self):
        self.R = []
        self.layers = {}

    def lay(self, ad, renk=7, tip='CONTINUOUS'):
        self.layers[ad] = (renk, tip)

    def L(self, lay, a, b): self.R.append(('L', lay, tuple(a), tuple(b)))
    def P(self, lay, pts, kapali=False): self.R.append(('P', lay, [tuple(p) for p in pts], kapali))
    def C(self, lay, c, r): self.R.append(('C', lay, tuple(c), r))
    def A(self, lay, c, r, a0, a1): self.R.append(('A', lay, tuple(c), r, a0, a1))
    def T(self, lay, p, s, h, aci=0, hiza='L'): self.R.append(('T', lay, tuple(p), str(s), h, aci, hiza))

    def rect(self, lay, x0, y0, x1, y1): self.P(lay, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True)

    def tara(self, lay, x0, y0, x1, y1, ara=5.0, aci=45):
        """Dikdörtgen içine 45° tarama çizgileri."""
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        w, h = x1 - x0, y1 - y0
        k = -h
        while k < w:
            # çizgi: x = x0 + k + t, y = y0 + t
            ta, tb = max(0, -k), min(h, w - k)
            if tb > ta:
                self.L(lay, (x0 + k + ta, y0 + ta), (x0 + k + tb, y0 + tb))
            k += ara * 1.4142

    def olcu(self, lay, a, b, ofs, h, metin=None, dik=False):
        """Basit ölçü: a-b arası, ofs kadar kaydırılmış ölçü çizgisi, uç çentikleri ve yazı."""
        (ax, ay), (bx, by) = a, b
        L = math.hypot(bx - ax, by - ay)
        if L < 1e-6: return
        ux, uy = (bx - ax) / L, (by - ay) / L
        nx, ny = -uy, ux
        pa = (ax + nx * ofs, ay + ny * ofs); pb = (bx + nx * ofs, by + ny * ofs)
        self.L(lay, a, (pa[0] + nx * h * 0.4, pa[1] + ny * h * 0.4))
        self.L(lay, b, (pb[0] + nx * h * 0.4, pb[1] + ny * h * 0.4))
        self.L(lay, pa, pb)
        t = h * 0.45
        for p in (pa, pb):
            self.L(lay, (p[0] - (ux + nx) * t, p[1] - (uy + ny) * t), (p[0] + (ux + nx) * t, p[1] + (uy + ny) * t))
        ang = math.degrees(math.atan2(uy, ux))
        if ang > 90.1 or ang < -89.9: ang += 180
        m = ((pa[0] + pb[0]) / 2 + nx * h * 0.5, (pa[1] + pb[1]) / 2 + ny * h * 0.5)
        s = metin if metin is not None else (f'{L:.1f}'.rstrip('0').rstrip('.'))
        self.T(lay, m, s, h, ang, 'BC')

    def kot(self, lay, x, y, s, h):
        """Kot sembolü (üçgen) + yazı."""
        self.P(lay, [(x, y), (x - h * 0.5, y + h * 0.8), (x + h * 0.5, y + h * 0.8)], True)
        self.L(lay, (x - h * 3, y), (x + h * 4, y))
        self.T(lay, (x + h * 0.8, y + h * 0.3), s, h, 0, 'BL')

    # ------------------------------------------------------------------ yazım
    def dxf(self, yol):
        H = {'L': 0, 'C': 1, 'R': 2}
        V = {'B': 1, 'M': 2, 'T': 3}
        o = []
        a = o.append
        def g(c, v): a(f'{c:>3}\n{v}\n')
        xs = [p[0] for r in self.R for p in self._pts(r)] or [0]
        ys = [p[1] for r in self.R for p in self._pts(r)] or [0]
        g(0, 'SECTION'); g(2, 'HEADER')
        g(9, '$ACADVER'); g(1, 'AC1009')
        g(9, '$DWGCODEPAGE'); g(3, 'ANSI_1254')
        g(9, '$INSUNITS'); g(70, 5)
        g(9, '$EXTMIN'); g(10, min(xs)); g(20, min(ys))
        g(9, '$EXTMAX'); g(10, max(xs)); g(20, max(ys))
        g(0, 'ENDSEC')
        g(0, 'SECTION'); g(2, 'TABLES')
        g(0, 'TABLE'); g(2, 'LTYPE'); g(70, 3)
        g(0, 'LTYPE'); g(2, 'CONTINUOUS'); g(70, 0); g(3, 'Solid line'); g(72, 65); g(73, 0); g(40, 0.0)
        g(0, 'LTYPE'); g(2, 'DASHED'); g(70, 0); g(3, '__ __ __'); g(72, 65); g(73, 2); g(40, 15.0); g(49, 10.0); g(49, -5.0)
        g(0, 'LTYPE'); g(2, 'CENTER'); g(70, 0); g(3, '____ _ ____'); g(72, 65); g(73, 4); g(40, 40.0); g(49, 25.0); g(49, -5.0); g(49, 5.0); g(49, -5.0)
        g(0, 'ENDTAB')
        g(0, 'TABLE'); g(2, 'LAYER'); g(70, len(self.layers) + 1)
        g(0, 'LAYER'); g(2, '0'); g(70, 0); g(62, 7); g(6, 'CONTINUOUS')
        for ad, (renk, tip) in self.layers.items():
            g(0, 'LAYER'); g(2, esc(ad)); g(70, 0); g(62, renk); g(6, tip)
        g(0, 'ENDTAB')
        g(0, 'TABLE'); g(2, 'STYLE'); g(70, 1)
        g(0, 'STYLE'); g(2, 'STANDARD'); g(70, 0); g(40, 0.0); g(41, 0.8); g(50, 0.0); g(71, 0); g(42, 2.5); g(3, 'arial.ttf'); g(4, '')
        g(0, 'ENDTAB')
        g(0, 'ENDSEC')
        g(0, 'SECTION'); g(2, 'ENTITIES')
        for r in self.R:
            k, lay = r[0], esc(r[1])
            if k == 'L':
                g(0, 'LINE'); g(8, lay); g(10, r[2][0]); g(20, r[2][1]); g(30, 0.0); g(11, r[3][0]); g(21, r[3][1]); g(31, 0.0)
            elif k == 'P':
                g(0, 'POLYLINE'); g(8, lay); g(66, 1); g(10, 0.0); g(20, 0.0); g(30, 0.0); g(70, 1 if r[3] else 0)
                for p in r[2]:
                    g(0, 'VERTEX'); g(8, lay); g(10, p[0]); g(20, p[1]); g(30, 0.0)
                g(0, 'SEQEND'); g(8, lay)
            elif k == 'C':
                g(0, 'CIRCLE'); g(8, lay); g(10, r[2][0]); g(20, r[2][1]); g(30, 0.0); g(40, r[3])
            elif k == 'A':
                g(0, 'ARC'); g(8, lay); g(10, r[2][0]); g(20, r[2][1]); g(30, 0.0); g(40, r[3]); g(50, r[4]); g(51, r[5])
            elif k == 'T':
                p, s, h, ang, al = r[2], esc(r[3]), r[4], r[5], r[6]
                hz = H[al[-1]]; vt = V.get(al[0], 0) if len(al) == 2 else 0
                g(0, 'TEXT'); g(8, lay); g(10, p[0]); g(20, p[1]); g(30, 0.0); g(40, h); g(1, s)
                if ang: g(50, ang)
                g(41, 0.8)
                if hz or vt:
                    g(72, hz); g(11, p[0]); g(21, p[1]); g(31, 0.0)
                    if vt: g(73, vt)
        g(0, 'ENDSEC'); g(0, 'EOF')
        with open(yol, 'w', encoding='cp1254', newline='\r\n') as f:
            f.write(''.join(o))

    @staticmethod
    def _pts(r):
        if r[0] == 'L': return [r[2], r[3]]
        if r[0] == 'P': return r[2]
        if r[0] in 'CA': return [(r[2][0] - r[3], r[2][1] - r[3]), (r[2][0] + r[3], r[2][1] + r[3])]
        if r[0] == 'T': return [r[2]]
        return []

    # ------------------------------------------------------------------ önizleme
    def png(self, yol, pencere, gen_inch=16.5, dpi=150, renk=None, siyah=False, kalem=None, model_mm=5.0):
        """model_mm: kağıt 1 mm = kaç model birimi (1/50 şerit, cm modelde 5)."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        x0, y0, x1, y1 = pencere
        fig = plt.figure(figsize=(gen_inch, gen_inch * (y1 - y0) / (x1 - x0)))
        ax = fig.add_axes([0, 0, 1, 1])
        ACI = {1: '#d00000', 2: '#b8a000', 3: '#008a00', 4: '#008a8a', 5: '#0030d0', 6: '#b000b0', 7: '#000000',
               8: '#8c8c8c', 9: '#b4b4b4', 30: '#e07000', 140: '#3070a0', 250: '#555555'}
        segs, cols, ls, lws = [], [], [], []
        ppu = gen_inch * 72 / (x1 - x0)
        for r in self.R:
            rk, tip = self.layers.get(r[1], (7, 'CONTINUOUS'))
            c = '#000000' if siyah else ACI.get(rk, '#000000')
            lw = (kalem.get(rk, 0.18) * 72 / 25.4 * (gen_inch * 25.4) / ((x1 - x0) / model_mm)) if kalem else 0.45
            k = r[0]
            if k == 'L': pts = [r[2], r[3]]
            elif k == 'P': pts = r[2] + ([r[2][0]] if r[3] else [])
            elif k == 'C':
                cx, cy = r[2]; pts = [(cx + r[3] * math.cos(t * math.pi / 24), cy + r[3] * math.sin(t * math.pi / 24)) for t in range(49)]
            elif k == 'A':
                cx, cy = r[2]; a0, a1 = r[4], r[5]
                if a1 < a0: a1 += 360
                n = max(6, int((a1 - a0) / 7))
                pts = [(cx + r[3] * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r[3] * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
            elif k == 'T':
                p, s, h, ang, al = r[2], r[3], r[4], r[5], r[6]
                if not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1): continue
                fs = h * ppu * 1.05
                if fs < 1.2: continue
                ha = {'L': 'left', 'C': 'center', 'R': 'right'}[al[-1]]
                va = {'B': 'bottom', 'M': 'center', 'T': 'top'}.get(al[0], 'baseline') if len(al) == 2 else 'baseline'
                ax.text(p[0], p[1], s.replace('%%c', 'Ø').replace('%%d', '°').replace('%%p', '±').replace('$', r'\$'),
                        fontsize=fs, color=c, rotation=ang, ha=ha, va=va, rotation_mode='anchor', family='DejaVu Sans')
                continue
            else:
                continue
            segs.append(pts); cols.append(c); ls.append('--' if tip == 'DASHED' else ('-.' if tip == 'CENTER' else '-')); lws.append(lw)
        for stil in ('-', '--', '-.'):
            S = [s for s, l in zip(segs, ls) if l == stil]
            if not S: continue
            C = [c for c, l in zip(cols, ls) if l == stil]
            W = [w for w, l in zip(lws, ls) if l == stil]
            ax.add_collection(LineCollection(S, colors=C, linewidths=W, linestyles=stil))
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off')
        fig.savefig(yol, dpi=dpi); plt.close(fig)
