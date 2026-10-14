"""Doğalgaz izometrik kolon şeması (30° izometri) + hesap tablosu + lejant + notlar -> DXF (R2018).

Şema ölçeksizdir: düşey/yatay boylar okunaklılık için seçilir, gerçek uzunluk ve kot farkı etiket ve
hesap tablosundadır. Bütün katmanlar ROTAS- önekli; MTY blokları kendi iç katmanlarıyla eklenir.
"""
import math

import ezdxf
from ezdxf.fonts import fonts
from shapely.geometry import LineString, Point, box as sbox
from shapely.ops import unary_union

import semboller as SB

C30, S30 = math.cos(math.radians(30)), 0.5

LAY = {
    'ROTAS-DOGALGAZ-BORU': 2, 'ROTAS-DOGALGAZ-SEBEKE': 2, 'ROTAS-DOGALGAZ-CAP': 3,
    'ROTAS-DOGALGAZ-VANA': 1, 'ROTAS-DOGALGAZ-SAYAC': 4, 'ROTAS-DOGALGAZ-REGULATOR': 1,
    'ROTAS-DOGALGAZ-CIHAZ': 6, 'ROTAS-DOGALGAZ-NO': 30, 'ROTAS-DOGALGAZ-YAZI': 7,
    'ROTAS-DOGALGAZ-KAT': 8, 'ROTAS-DOGALGAZ-TABLO': 7, 'ROTAS-DOGALGAZ-MASKE': 7,
    'ROTAS-DOGALGAZ-PAFTA': 7, 'ROTAS-DOGALGAZ-NOT': 1, 'ROTAS-DOGALGAZ-SERVIS-KUTUSU': 2,
    'ROTAS-DOGALGAZ-UYARI': 1,
}
BORU, CAP, VANA, SAY, REG, CIH, NO, YAZ, KAT, TAB, MSK, PAF, NOT, SKL, UYA = (
    'ROTAS-DOGALGAZ-BORU', 'ROTAS-DOGALGAZ-CAP', 'ROTAS-DOGALGAZ-VANA', 'ROTAS-DOGALGAZ-SAYAC',
    'ROTAS-DOGALGAZ-REGULATOR', 'ROTAS-DOGALGAZ-CIHAZ', 'ROTAS-DOGALGAZ-NO', 'ROTAS-DOGALGAZ-YAZI',
    'ROTAS-DOGALGAZ-KAT', 'ROTAS-DOGALGAZ-TABLO', 'ROTAS-DOGALGAZ-MASKE', 'ROTAS-DOGALGAZ-PAFTA',
    'ROTAS-DOGALGAZ-NOT', 'ROTAS-DOGALGAZ-SERVIS-KUTUSU', 'ROTAS-DOGALGAZ-UYARI')

H_ETK = 8.0        # boru etiketi yazı yüksekliği (1/50'de 1,6 mm)
H_NO = 7.0         # vana/ekipman numarası
H_CIH = 9.0
BORU_W = 1.5       # boru kalem kalınlığı (sabit genişlik, cm)
_FONT = fonts.make_font('DejaVuSans.ttf', 1.0)   # ölçüm için (Arial'dan geniş -> emniyetli)


def tw(s, h):
    return _FONT.text_width(s) * h


def tr(x, n=2):
    return f'{x:.{n}f}'.replace('.', ',')


AKSA_NOT = 'AKSAGAZ ŞARTNAMESİYLE TEYİT EDİLECEK'


class Cizim:
    def __init__(self, ag, P):
        self.ag, self.P = ag, P
        doc = ezdxf.new('R2018', setup=True)
        doc.header['$INSUNITS'] = 5
        doc.header['$LTSCALE'] = 1.0
        doc.header['$MEASUREMENT'] = 1
        doc.styles.add('ROTAS', font='arial.ttf')
        doc.set_wipeout_variables(frame=0)
        for n, c in LAY.items():
            doc.layers.add(n, color=c)
        doc.layers.get(MSK).dxf.plot = 1
        self.doc, self.msp = doc, doc.modelspace()
        SB.mty_aktar(doc)
        SB.tanimla(doc, SAY)
        self.boru_geo = []      # (hat_no veya etiket, LineString)
        self.engel = []         # shapely geometrileri (yazı yerleşiminde kaçınılacak)
        self.yazi_kutu = []
        self.sembol_kutu = []   # (ad, box, hat_no)
        self.ox, self.oy = 0.0, 0.0
        self.no_say = {'V': 0}
        self.ekipman = []       # (no, ad, açıklama)

    # ------------------------------------------------------------------ yardımcılar
    def p(self, q):
        x, y, z = q
        return (self.ox + (x - y) * C30, self.oy + (x + y) * S30 + z)

    def _kutu_ekle(self, b, pay=2.0):
        self.yazi_kutu.append(b.buffer(pay, join_style=2))

    def bos_mu(self, b, kendi=None):
        for tag, g in self.boru_geo:
            if g.intersects(b):
                return False
        for _, sb, _ in self.sembol_kutu:
            if sb.intersects(b):
                return False
        for k in self.yazi_kutu:
            if k.intersects(b):
                return False
        for g in self.engel:
            if g.intersects(b):
                return False
        return True

    def yazi(self, s, pos, h, lay, align='MIDDLE_LEFT', rot=0.0, maske=False, kutu=True):
        if maske:
            w = tw(s, h)
            x, y = pos
            x0 = {'L': x, 'C': x - w / 2, 'R': x - w}[align.split('_')[-1][0] if '_' in align else 'L']
            self.msp.add_wipeout([(x0 - 1.5, y - h / 2 - 2), (x0 + w + 1.5, y - h / 2 - 2),
                                  (x0 + w + 1.5, y + h / 2 + 2), (x0 - 1.5, y + h / 2 + 2)],
                                 dxfattribs={'layer': MSK})
        t = self.msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS'})
        t.set_placement(pos, align=ezdxf.enums.TextEntityAlignment[align])
        return t

    def satirlar(self, lines, x0, ytop, h, lay, maske=True, align='L'):
        """Sol üst köşesi (x0, ytop) olan çok satırlı yazı; maske tek parça kutu."""
        ara = h * 1.55
        w = max(tw(s, h) for s in lines)
        hb = ara * (len(lines) - 1) + h
        if maske:
            self.msp.add_wipeout([(x0 - 2, ytop + 2.5), (x0 + w + 2, ytop + 2.5), (x0 + w + 2, ytop - hb - 2.5),
                                  (x0 - 2, ytop - hb - 2.5)], dxfattribs={'layer': MSK})
        for i, s in enumerate(lines):
            y = ytop - h / 2 - i * ara
            if align == 'L':
                self.yazi(s, (x0, y), h, lay)
            else:
                self.yazi(s, (x0 + w / 2, y), h, lay, align='MIDDLE_CENTER')
        b = sbox(x0 - 2, ytop - hb - 2.5, x0 + w + 2, ytop + 2.5)
        self._kutu_ekle(b, 0.5)
        return b

    def etiket_yerlestir(self, lines, h, adaylar, lay, maske=True, cizgi=False):
        """cizgi=True: uzak yerleşimde boruya kılavuz çizgi çizilir."""
        """adaylar: [(px, py), yön vektörleri...] noktaları; ilk boş kutuya satırları yazar."""
        ara = h * 1.55
        w = max(tw(s, h) for s in lines) + 4
        hb = ara * (len(lines) - 1) + h + 5
        for (px, py) in adaylar:
            for d in (4.0, 9.0, 16.0, 26.0, 40.0, 60.0):
                for kx, ky in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                    if kx > 0:
                        x0 = px + d
                    elif kx < 0:
                        x0 = px - d - w
                    else:
                        x0 = px - w / 2
                    if ky > 0:
                        y0 = py + d
                    elif ky < 0:
                        y0 = py - d - hb
                    else:
                        y0 = py - hb / 2
                    b = sbox(x0, y0, x0 + w, y0 + hb)
                    if not self.bos_mu(b.buffer(1.5)):
                        continue
                    lider = None
                    if d >= 26.0 and cizgi:
                        # kılavuz çizgi: etiket kutusunun en yakın noktasından boruya
                        from shapely.ops import nearest_points
                        q = nearest_points(b, Point(px, py))[0]
                        lider = LineString([(q.x, q.y), (px, py)])
                        if not self._lider_bos(lider):
                            continue
                    self.satirlar(lines, x0 + 2, y0 + hb - 2.5, h, lay, maske=maske)
                    if lider is not None:
                        self.msp.add_line(lider.coords[0], lider.coords[1], dxfattribs={'layer': lay})
                        self.engel.append(lider)
                    return b
        return None

    def _lider_bos(self, ln):
        kisa = ln.parent if False else LineString([ln.coords[0], ln.interpolate(ln.length - 3).coords[0]])
        for tag, g in self.boru_geo:
            if g.intersects(kisa):
                return False
        for _, sb, _ in self.sembol_kutu:
            if sb.intersects(kisa):
                return False
        for k in self.yazi_kutu:
            if k.buffer(-2.5).intersects(kisa):
                return False
        for g in self.engel:
            if g.intersects(kisa):
                return False
        return True

    # ------------------------------------------------------------------ boru + semboller
    def _yol_noktasi(self, pts, s):
        """2B polyline üzerinde s uzunluğundaki nokta ve parça açısı."""
        kal = s
        for a, b in zip(pts, pts[1:]):
            L = math.dist(a, b)
            if kal <= L or b == pts[-1]:
                t = 0 if L == 0 else min(1, kal / L)
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.degrees(
                    math.atan2(b[1] - a[1], b[0] - a[0]))
            kal -= L
        return pts[-1], 0.0

    def _kes(self, pts, araliklar):
        """polyline'ı [s0,s1] boşluklarında böl; parçalar listesi."""
        araliklar = sorted(araliklar)
        cum = [0.0]
        for a, b in zip(pts, pts[1:]):
            cum.append(cum[-1] + math.dist(a, b))
        toplam = cum[-1]
        sinirlar = []
        s = 0.0
        for (s0, s1) in araliklar:
            sinirlar.append((s, s0))
            s = s1
        sinirlar.append((s, toplam))
        parcalar = []
        for (a, b) in sinirlar:
            if b - a < 0.5:
                continue
            q = [self._yol_noktasi(pts, a)[0]]
            for i, c in enumerate(cum):
                if a < c < b:
                    q.append(pts[i])
            q.append(self._yol_noktasi(pts, b)[0])
            parcalar.append(q)
        return parcalar

    def vana_no(self, ad, aciklama):
        self.no_say['V'] += 1
        no = f'V-{self.no_say["V"]:02d}'
        self.ekipman.append((no, ad, aciklama))
        return no

    def boru_ciz(self, h, pts, gaplar):
        for q in self._kes(pts, gaplar):
            self.msp.add_lwpolyline(q, dxfattribs={'layer': BORU, 'const_width': BORU_W})
        self.boru_geo.append((h.no if h else 'x', LineString(pts)))

    def vana_ekle(self, pos, aci, dn, hat_no, ad, aciklama, gaz=True):
        """MTY-KURESEL VANA (patlatılmadan, CAP özniteliği = DN)."""
        ins = self.msp.add_blockref('MTY-KURESEL VANA', pos, dxfattribs={'layer': VANA, 'rotation': aci})
        ins.add_auto_attribs({'CAP': dn})
        self._sembol_kutu(ins, ad, hat_no)
        no = self.vana_no(ad, aciklama)
        return ins, no

    def _sembol_kutu(self, ins, ad, hat_no):
        from ezdxf import bbox as zb
        bb = zb.extents([ins])
        b = sbox(bb.extmin.x, bb.extmin.y, bb.extmax.x, bb.extmax.y)
        self.sembol_kutu.append((ad, b, hat_no))
        return b

    # ------------------------------------------------------------------ şema
    def sema(self):
        ag, G = self.ag, self.P['geometri']
        msp = self.msp
        etiketler = []       # (hat, pts2d)
        vana_nolar = []      # (no, pos)
        # --- 1) bütün hatların 2B yolları ve sembol aralıkları
        for h in ag.hatlar:
            pts = [self.p(q) for q in h.yol3d]
            toplam = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
            gaplar = []
            for (tur, t, _) in h.semboller:
                s = t * toplam if t >= 0 else toplam + t
                if tur == 'AKV':
                    s = toplam - 40
                if tur == 'CV':
                    s = toplam - min(55, toplam * 0.62)
                if tur == 'DV':
                    s = toplam - 70
                gaplar.append((s - 10, s + 10, tur))
            if h.tur == 'cihaz':
                gaplar.append((toplam - 22, toplam, 'ESNEK'))
            h._pts, h._gap, h._top = pts, gaplar, toplam
        for h in ag.hatlar:
            self.boru_ciz(h, h._pts, [(a, b) for a, b, _ in h._gap])
        # --- 3) servis kutusu (şebekeden gelen hat + giriş vanası + regülatör)
        h1 = ag.hat_bina[0]
        x0, _, z0 = h1.yol3d[0]
        a = self.p((x0 - 260, 0, z0))
        b = self.p((x0, 0, z0))
        vpos = self.p((x0 - 165, 0, z0))
        rpos = self.p((x0 - 90, 0, z0))
        pts = [a, b]
        tot = math.dist(a, b)
        sv = math.dist(a, vpos)
        sr = math.dist(a, rpos)
        for q in self._kes(pts, [(sv - 10, sv + 10), (sr - 12, sr + 12)]):
            msp.add_lwpolyline(q, dxfattribs={'layer': BORU, 'const_width': BORU_W})
        self.boru_geo.append(('sebeke', LineString(pts)))
        ins = msp.add_blockref('MTY-KURESEL VANA', vpos, dxfattribs={'layer': VANA, 'rotation': 30})
        ins.add_auto_attribs({'CAP': 'DN25'})
        self._sembol_kutu(ins, 'SKV', 'sebeke')
        no_sk = self.vana_no('Servis kutusu giriş vanası', 'Servis kutusu içinde, dağıtım şirketine ait')
        vana_nolar.append((no_sk, vpos, 'SKV'))
        ins = msp.add_blockref('ROTAS-DG-REGULATOR', rpos, dxfattribs={'layer': REG, 'rotation': 30})
        self._sembol_kutu(ins, 'REG', 'sebeke')
        self.ekipman.append(('R-01', 'Servis kutusu regülatörü', f'Çıkış {self.P["sistem_basinci_mbar"]} mbar ({AKSA_NOT.lower()})'))
        # kutu (kesikli, izometrik ön yüz)
        u0, u1, v0, v1 = x0 - 205, x0 - 45, z0 - 32, z0 + 42
        kp = [self.p((u0, 0, v0)), self.p((u1, 0, v0)), self.p((u1, 0, v1)), self.p((u0, 0, v1))]
        msp.add_lwpolyline(kp, close=True, dxfattribs={'layer': SKL, 'linetype': 'DASHED', 'ltscale': 0.6})
        self.engel.append(LineString(kp + [kp[0]]))
        # regülatör no ve servis kutusu yazısı
        self.etiket_yerlestir(['R-01'], H_NO, [rpos], NO, maske=True)
        self.etiket_yerlestir(['SERVİS KUTUSU', f'(REGÜLATÖR ÇIKIŞI {self.P["sistem_basinci_mbar"]} mbar)'], H_ETK,
                              [((kp[0][0] + kp[1][0]) / 2, kp[0][1] - 18)], YAZ)
        self.etiket_yerlestir(['DAĞITIM HATTINDAN', '(AKSAGAZ)'], H_ETK, [a], YAZ)
        # --- 2) semboller
        for h in ag.hatlar:
            for (s0, s1, tur) in h._gap:
                pos, aci = self._yol_noktasi(h._pts, (s0 + s1) / 2)
                if tur == 'ESNEK':
                    ins = msp.add_blockref('MTY-ESNEK BAGLANTI', pos, dxfattribs={'layer': VANA, 'rotation': aci})
                    ins.add_auto_attribs({'CAP': ''})
                    self._sembol_kutu(ins, 'ESNEK', h.no)
                    continue
                if tur == 'AKV':
                    ad, ack = 'Ana kesme vanası (AKV)', f'Bina girişi ana kesme vanası, {h.dn}, h=1,90-2,10 m'
                elif tur == 'SV':
                    ad, ack = 'Sayaç vanası', f'{h.bolum} sayaç giriş vanası, {h.dn}'
                elif tur == 'DV':
                    ad, ack = 'Daire kapama vanası', f'{h.bolum} daire girişi küresel vana, {h.dn}'
                else:
                    ad, ack = 'Cihaz vanası', f'{h.bolum} {h.cihaz["ad"].lower()} vanası, {h.dn}'
                ins, no = self.vana_ekle(pos, aci, h.dn, h.no, ad, ack)
                vana_nolar.append((no, pos, tur))
        # --- 4) sayaçlar
        for i, d in enumerate(ag.daireler):
            pos = self.p((d['x'], 0, G['sema_sayac_z']))
            ins = msp.add_blockref('ROTAS-DG-SAYAC', pos, dxfattribs={'layer': SAY})
            ins.add_auto_attribs({'TIP': 'G4'})
            self._sembol_kutu(ins, 'SAYAC', {d['h_tap'].no, d['h_daire'].no})
            d['sayac_no'] = f'S-{int(d["no"][1:]):02d}'
            self.ekipman.append((d['sayac_no'], 'Gaz sayacı G4 (körüklü)', f'{d["no"]} sayacı'))
        # --- 5) cihazlar
        for d in ag.daireler:
            for hc in d['h_cihaz']:
                E = hc._pts[-1]
                c = hc.cihaz
                n = int(d['no'][1:])
                if c['ad'].startswith('KOMB'):
                    s = 1.2
                    sag = d['taraf'] == 'sag'
                    xs = -s if sag else s
                    ins = msp.add_blockref('MTY-KOMBİ', (E[0] - 23.9 * xs, E[1] - 30 * s),
                                           dxfattribs={'layer': CIH, 'xscale': xs, 'yscale': s})
                    cno = f'K-{n:02d}'
                    self.ekipman.append((cno, f'Kombi {tr(c["kWg"], 0)} kW (C tipi, hermetik)', f'{d["no"]}, {tr(c["Q"])} m³/h'))
                else:
                    ins = msp.add_blockref('ROTAS-DG-OCAK', E, dxfattribs={'layer': CIH})
                    cno = f'O-{n:02d}'
                    self.ekipman.append((cno, f'Ocak 4 gözlü (A tipi)', f'{d["no"]}, {tr(c["Q"])} m³/h, {tr(c["kWg"], 1)} kW'))
                bb = self._sembol_kutu(ins, 'CIHAZ', hc.no)
                hc._cihaz_kutu = bb
                hc._cno = cno
        # --- 7) cihaz etiketleri (kW yanında)
        for d in ag.daireler:
            for hc in d['h_cihaz']:
                c = hc.cihaz
                bb = hc._cihaz_kutu
                cx, cy = bb.centroid.x, bb.centroid.y
                minx, miny, maxx, maxy = bb.bounds
                if c['ad'].startswith('KOMB'):
                    lines = [f'KOMBİ {tr(c["kWg"], 0)} kW', f'{tr(c["Q"])} m³/h  {hc._cno}']
                else:
                    lines = [f'OCAK {tr(c["kWg"], 1)} kW', f'{tr(c["Q"])} m³/h  {hc._cno}']
                r = self.etiket_yerlestir(lines, H_CIH, [(maxx, cy), (minx, cy), (cx, miny), (cx, maxy)], CIH)
                if r is None:
                    print('UYARI cihaz etiketi yerleşmedi', d['no'], c['ad'])
        # --- 8) daire adları (ayrım noktasında)
        for d in ag.daireler:
            F = self.p(d['F'])
            kat = self.P['katlar'][d['kat']]
            kot = d['kat'] * self.P['kat_yuksekligi']
            r = self.etiket_yerlestir([f'{d["no"]} - {kat} ({"+" if kot else "±"}{tr(kot)})'], 10, [F], YAZ)
            if r is None:
                print('UYARI daire adı yerleşmedi', d['no'])
        # sayaç numaraları
        for d in ag.daireler:
            pos = self.p((d['x'], 0, G['sema_sayac_z']))
            r = self.etiket_yerlestir([d['sayac_no']], H_NO, [(pos[0], pos[1] - 2)], NO)
            if r is None:
                print('UYARI sayaç no', d['no'])
        # --- 9) boru etiketleri: "Q m³/h / L m / DN [hat]"
        for h in sorted(ag.hatlar, key=lambda h: (h.tur != 'cihaz', h.no)):
            lines = [f'{tr(h.Q)} m³/h', f'{tr(h.L)} m', f'{h.dn} [{h.no}]']
            adaylar = []
            # en uzun parça önce
            parcalar = sorted(zip(h._pts, h._pts[1:]), key=lambda ab: -math.dist(*ab))
            for (a, b) in parcalar:
                for t in (0.5, 0.35, 0.65, 0.2, 0.8, 0.1, 0.9):
                    adaylar.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            r = self.etiket_yerlestir(lines, H_ETK, adaylar, CAP, cizgi=True)
            if r is None:
                print('UYARI etiket yerleşmedi: hat', h.no, h.aciklama)
        # --- 10) vana numaraları
        for no, pos, tur in vana_nolar:
            r = self.etiket_yerlestir([no + (' AKV' if tur == 'AKV' else '')], H_NO, [pos], NO)
            if r is None:
                print('UYARI vana no', no)
        # bina girişi işareti
        hb = ag.hat_bina[0]
        pg = self.p(hb.yol3d[-1])
        self.etiket_yerlestir(['BİNA GİRİŞİ'], H_ETK, [pg], YAZ)

    # ------------------------------------------------------------------ tablolar
    def tablo(self, x0, y0, baslik, basliklar, satirlar, gen, h=8.0, rh=20.0, renkli=None):
        msp = self.msp
        W = sum(gen)
        self.yazi(baslik, (x0, y0 + 14), 12, TAB, align='BOTTOM_LEFT')
        nh = len(basliklar[0]) if isinstance(basliklar[0], tuple) else 1
        hh = rh * 2
        y = y0
        msp.add_lwpolyline([(x0, y), (x0 + W, y), (x0 + W, y - hh), (x0, y - hh)], close=True, dxfattribs={'layer': TAB})
        x = x0
        for g, bs in zip(gen, basliklar):
            l1, l2 = bs if isinstance(bs, tuple) else (bs, '')
            self.yazi(l1, (x + g / 2, y - rh * 0.55), h, TAB, align='MIDDLE_CENTER')
            if l2:
                self.yazi(l2, (x + g / 2, y - rh * 1.45), h * 0.9, TAB, align='MIDDLE_CENTER')
            x += g
            msp.add_line((x, y), (x, y - hh - rh * len(satirlar)), dxfattribs={'layer': TAB})
        msp.add_line((x0, y), (x0, y - hh - rh * len(satirlar)), dxfattribs={'layer': TAB})
        y -= hh
        for r_i, row in enumerate(satirlar):
            x = x0
            for j, (g, v) in enumerate(zip(gen, row)):
                lay = TAB
                if renkli and renkli(r_i, j, v):
                    lay = UYA
                if j == 1 and isinstance(v, str) and tw(v, h) > g - 6:
                    self.yazi(v, (x + 3, y - rh / 2), h * 0.85, lay, align='MIDDLE_LEFT')
                elif j <= 1:
                    self.yazi(str(v), (x + 3, y - rh / 2), h, lay, align='MIDDLE_LEFT')
                else:
                    self.yazi(str(v), (x + g / 2, y - rh / 2), h, lay, align='MIDDLE_CENTER')
                x += g
            y -= rh
            msp.add_line((x0, y), (x0 + W, y), dxfattribs={'layer': TAB})
        return W, y0 - y

    def hesap_tablosu(self, x0, y0):
        ag = self.ag
        P = self.P
        kum = self.kumulatif()
        bas = [('Hat', 'no'), ('Açıklama', ''), ('n', 'BB'), ('Q top', 'm³/h'), ('f', ''), ('Q hesap', 'm³/h'),
               ('L', 'm'), ('h', 'm'), ('DN', ''), ('Di', 'mm'), ('V', 'm/s'), ('ΔP/L', 'mbar/m'), ('ΔP R', 'mbar'),
               ('Σξ', ''), ('ΔP Z', 'mbar'), ('ΔP H', 'mbar'), ('ΔP Σ', 'mbar'), ('Kümülatif', 'mbar')]
        gen = [40, 330, 34, 62, 40, 62, 50, 50, 54, 50, 50, 66, 62, 42, 62, 62, 62, 76]
        rows = []
        for h in ag.hatlar:
            rows.append([h.no, h.aciklama, h.n_bb, tr(h.Q_top), tr(h.f), tr(h.Q), tr(h.L), tr(h.h), h.dn, tr(h.D, 1),
                         tr(h.V), tr(h.R, 4), tr(h.dPR, 3), tr(h.xi, 1), tr(h.dPZ, 3), tr(h.dPH, 3), tr(h.dP, 3),
                         tr(kum[h.no], 3)])
        vmax = P['sinirlar']['hiz']
        W, H = self.tablo(x0, y0, f'DOĞALGAZ BORU ÇAPI VE BASINÇ KAYBI HESAP TABLOSU ({P["sistem_basinci_mbar"]} mbar)',
                          bas, rows, gen, renkli=lambda i, j, v: j == 10 and float(v.replace(',', '.')) > vmax)
        return W, H

    def kumulatif(self):
        """servis kutusundan her hattın sonuna kadar toplam ΔP."""
        ag = self.ag
        by_b = {h.b: h for h in ag.hatlar}
        out = {}
        for h in ag.hatlar:
            s, x = 0.0, h
            while x is not None:
                s += x.dP
                x = by_b.get(x.a)
            out[h.no] = s
        return out

    def kontrol_tablosu(self, x0, y0):
        L = self.P['sinirlar']
        rows = []
        for k in self.ag.kontroller():
            ok = k['ok_on'] and k['ok_so'] and k['ok_top']
            rows.append([k['daire'], k['cihaz'], tr(k['on'], 3), tr(k['so'], 3), tr(k['top'], 3),
                         'UYGUN' if ok else 'UYGUN DEĞİL'])
        bas = [('Bölüm', ''), ('Cihaz', ''), ('Servis k.→sayaç v.', f'≤ {tr(L["servis_sayac"], 1)} mbar'),
               ('Sayaç→cihaz', f'≤ {tr(L["sayac_cihaz"], 1)} mbar'), ('Toplam', f'≤ {tr(L["toplam"], 1)} mbar'),
               ('Durum', '')]
        gen = [60, 90, 150, 130, 110, 110]
        return self.tablo(x0, y0, 'KRİTİK DEVRE KONTROLÜ (sayaç kaybı hariç)', bas, rows, gen,
                          renkli=lambda i, j, v: j == 5 and v != 'UYGUN')

    def ekipman_tablosu(self, x0, y0):
        rows = [[n, a, b] for n, a, b in self.ekipman]
        return self.tablo(x0, y0, 'EKİPMAN LİSTESİ', [('No', ''), ('Ekipman', ''), ('Açıklama', '')], rows,
                          [60, 260, 420], rh=17)

    def lejant(self, x0, y0):
        msp = self.msp
        self.yazi('LEJANT', (x0, y0 + 14), 12, TAB, align='BOTTOM_LEFT')
        satir = [
            ('boru', 'Doğalgaz borusu (çelik, TS EN 10255) - izometrik'),
            ('MTY-KURESEL VANA', 'Küresel vana (TS EN 331) - AKV / sayaç / daire / cihaz vanası'),
            ('ROTAS-DG-REGULATOR', 'Basınç düşürücü regülatör (servis kutusu)'),
            ('ROTAS-DG-SAYAC', 'Gaz sayacı G4 (körüklü)'),
            ('MTY-ESNEK BAGLANTI', 'Esnek bağlantı (kombi ≤60 cm, ocak ≤150 cm)'),
            ('MTY-KOMBİ', 'Kombi (C tipi, hermetik)'),
            ('ROTAS-DG-OCAK', 'Ocak (A tipi, bacasız)'),
            ('kutu', 'Servis kutusu'),
        ]
        y = y0 - 30
        for ad, ack in satir:
            if ad == 'boru':
                msp.add_lwpolyline([(x0 + 10, y), (x0 + 80, y)], dxfattribs={'layer': BORU, 'const_width': BORU_W})
            elif ad == 'kutu':
                msp.add_lwpolyline([(x0 + 15, y - 14), (x0 + 75, y - 14), (x0 + 75, y + 14), (x0 + 15, y + 14)],
                                   close=True, dxfattribs={'layer': SKL, 'linetype': 'DASHED', 'ltscale': 0.6})
            elif ad == 'MTY-KOMBİ':
                ins = msp.add_blockref(ad, (x0 + 10, y - 15), dxfattribs={'layer': CIH})
            elif ad == 'ROTAS-DG-OCAK':
                msp.add_blockref(ad, (x0 + 45, y + 22), dxfattribs={'layer': CIH})
            elif ad == 'ROTAS-DG-SAYAC':
                ins = msp.add_blockref(ad, (x0 + 45, y - 18), dxfattribs={'layer': SAY})
                ins.add_auto_attribs({'TIP': 'G4'})
            else:
                msp.add_lwpolyline([(x0 + 10, y), (x0 + 30, y)], dxfattribs={'layer': BORU, 'const_width': BORU_W})
                msp.add_lwpolyline([(x0 + 60, y), (x0 + 80, y)], dxfattribs={'layer': BORU, 'const_width': BORU_W})
                ins = msp.add_blockref(ad, (x0 + 45, y), dxfattribs={'layer': VANA if 'MTY' in ad else REG})
                if ad.startswith('MTY'):
                    ins.add_auto_attribs({'CAP': 'DN25' if 'VANA' in ad else ''})
            self.yazi(ack, (x0 + 160, y), 10, TAB)
            y -= 60
        return y0 - y

    def notlar(self, x0, y0, satirlar, baslik='NOTLAR', h=10.0, lay=NOT):
        self.yazi(baslik, (x0, y0 + 14), 12, lay, align='BOTTOM_LEFT')
        y = y0 - 10
        for s in satirlar:
            self.yazi(s, (x0, y), h, lay)
            y -= h * 1.9
        return y0 - y

    # ------------------------------------------------------------------ kontrol
    def kontrol(self):
        hatalar = []
        bg = self.boru_geo
        # boru-boru kesişmesi (uç birleşimleri hariç)
        for i in range(len(bg)):
            for j in range(i + 1, len(bg)):
                a, b = bg[i][1], bg[j][1]
                if not a.intersects(b):
                    continue
                inter = a.intersection(b)
                uclar = [Point(a.coords[0]), Point(a.coords[-1]), Point(b.coords[0]), Point(b.coords[-1])]
                geoms = getattr(inter, 'geoms', [inter])
                for g in geoms:
                    if g.geom_type != 'Point' or not any(g.distance(u) < 0.5 for u in uclar):
                        hatalar.append(f'boru kesişmesi: {bg[i][0]} x {bg[j][0]} @ {g.representative_point()}')
        # sembol - başka hattın borusu
        for ad, sb, hn in self.sembol_kutu:
            komsu = hn if isinstance(hn, (set, tuple, list)) else {hn}
            for tag, g in bg:
                if tag in komsu:
                    continue
                if g.intersects(sb.buffer(-0.5)):
                    # kendi hattına bitişik hatlar (aynı düğüm) uçtan dokunabilir
                    if g.intersection(sb).length > 1.0:
                        hatalar.append(f'sembol {ad} (hat {hn}) başka boruyla çakışıyor: {tag}')
        # yazı - yazı
        for i in range(len(self.yazi_kutu)):
            for j in range(i + 1, len(self.yazi_kutu)):
                if self.yazi_kutu[i].buffer(-2.4).intersects(self.yazi_kutu[j].buffer(-2.4)):
                    hatalar.append(f'yazı çakışması {i}-{j}')
        return hatalar
