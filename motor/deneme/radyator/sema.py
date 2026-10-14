# -*- coding: utf-8 -*-
"""KALORİFER TESİSAT PROJESİ KOLON ŞEMASI (R3, kolektörlü — 14.10.2026 (B) talimatı):
- MTY bloğu YOK (radyatör, termostatik vana, kolektör, kalorimetre, vanalar saf geometri: geo.py).
- Boru atlatma / köprü YOK. Merdiven (ladder) düzeni: her dairenin GİDİŞ kolonu dairenin bir yanında, DÖNÜŞ kolonu
  öbür yanında; kat bağlantıları iki kolon arasında kalır. Daire içi: kolon T → KALORİMETRE SETİ (gidiş + dönüş paralel)
  → KOLEKTÖR DOLABI (gidiş kolektörü üstte, ağızlar yukarı; dönüş kolektörü altta, ağızlar aşağı) → her radyatöre iç içe
  (en uzak radyatör en dış) gidiş-dönüş → dönüş, KS'nin önünden aşağı inip radyatörlerin altından dönüş kolonuna.
  A dairesi aynalı (gidiş kolonları ortada, dönüş kolonları dışta); bodrumda gidiş dağıtımı üstte, dönüş toplama altta;
  kolon dipleri ikisinin arasından "KAZAN DAİRESİNE" okuyla sonlanır → hiçbir hat kesişmez.
- R5 (14.10.2026): kazan dairesi PRENSİP ŞEMASI kullanıcı tarafından REDDEDİLDİ — kolon şemasına gömülmez, cihaz listesi
  de yok. Kazan dairesi yalnız ONAYLI plan/kesit/kısmi görünüş paftasıdır (kazan_dairesi_paftasi → plan_kesit.onayli_kazan_dairesi).
- Kalorimetre sinyal hattı (elektrik) çizilmez.
- KESİT / GÖRÜNÜŞ detayı: kalorimetre dolabı + kolektör dolabı görünüşü ve A-A kesiti (1/10)."""
import os
import sys
import math
from shapely.geometry import LineString, Polygon, box as sbox
import ciz as C
import semb
import geo

BANT = 300.0
SLOT = 185.0
KOL_DX = 240.0             # gidiş kolonu → kolektör dolabı
SET_X = [40.0, 80.0, 120.0, 160.0, 200.0]
XK_DONUS = 20.0            # KS dönüşünün aşağı indiği nokta (gidiş kolonundan)
Y = dict(hg=205.0, hd=185.0, yc=175.0, rad=170.0, U0=228.0, B0=152.0, adim=7.0, alt=70.0)   # bant tabanından
SEM, KOLK = 'ROTAS-ISITMA-SEMBOL', 'ROTAS-ISITMA-KOLEKTOR'
KD_ARA = 1000.0            # R5: K1 ile K2 gidiş kolonu arası (KAZAN DAİRESİNE çıkışı + not)
_KOK = os.path.dirname(os.path.abspath(__file__))


class Hatlar:
    def __init__(self):
        self.g, self.d = [], []

    def G(self, pts):
        self.g.append([tuple(p) for p in pts])

    def D(self, pts):
        self.d.append([tuple(p) for p in pts])


class Sema:
    def __init__(self, cz, P, M, A, pf, pomp):
        self.cz, self.P, self.M, self.A, self.pf, self.pomp = cz, P, M, A, pf, pomp
        self.h = Hatlar()
        self.etiket = []

    # ------------------------------------------------------------ sembol (boru üstünde, maskeli)
    def sembol(self, ad, p, rot=0.0, olcek=0.6, no=None):
        cz = self.cz
        w, hh = 13.0 * olcek / 0.6, 8.0 * olcek / 0.6
        if abs(rot) % 180 == 90:
            w, hh = hh, w
        cz.maske([(p[0] - w / 2, p[1] - hh / 2), (p[0] + w / 2, p[1] - hh / 2), (p[0] + w / 2, p[1] + hh / 2), (p[0] - w / 2, p[1] + hh / 2)])
        semb.ciz(cz.msp, ad, p, rot=rot, olcek=olcek, kat=SEM, no=no)

    def nmaks(self):
        n = 1
        for k in self.M['katlar']:
            if k['daireler']:
                for dad in ('A', 'B'):
                    n = max(n, len(self.pf(k, dad)['devreler']))
        return n

    def daire_genislik(self):
        n = self.nmaks()
        return KOL_DX + geo.kolektor_genislik(n) + 70.0 + (n - 1) * SLOT + geo.RAD_W + 60.0

    # ------------------------------------------------------------ daire (s = +1: içerik sağda, s = -1: aynalı)
    def daire(self, kat, dad, xg, xd, yf, merkezi, s):
        cz = self.cz
        pl = self.pf(kat, dad)
        dvs = pl['devreler']
        n = len(dvs)
        prc = {p['devre']: p for p in self.A.parcalar if p['kat'] == kat['kod'] and p['daire'] == dad and p['tur'] == 'devre'}
        gir = [p for p in self.A.parcalar if p['kat'] == kat['kod'] and p['daire'] == dad and p['tur'] == 'giris'][0]
        ad, W = geo.kolektor_sema(cz.doc, n)
        hg, hd, yc = yf + Y['hg'], yf + Y['hd'], yf + Y['yc']
        xc0 = xg + s * KOL_DX
        cz.msp.add_blockref(ad, (xc0, yc), dxfattribs={'layer': KOLK, 'xscale': s})
        cz.engel.append(sbox(min(xc0, xc0 + s * W), yc, max(xc0, xc0 + s * W), yc + geo.KOL_H).exterior)
        cz.yazi((xc0 + s * W / 2, yc + 20.0), f'KD ({n} AĞIZ)', 6.0, KOLK)
        # besleme: gidiş kolondan T ile KS üzerinden kolektöre; dönüş kolektörden KS üzerinden, sonra aşağı inip
        # radyatörlerin altından dönüş kolonuna (merkezi) / kombiye (kombi)
        self.h.G([(xg, hg), (xc0, hg)])
        if merkezi:
            xk = xg + s * XK_DONUS
            self.h.D([(xc0, hd), (xk, hd), (xk, yf + Y['alt']), (xd, yf + Y['alt'])])
            for (sg, sd, no), x in zip([('r_kuresel_vana', 'r_kuresel_vana', '1'), ('r_pislik_tutucu', None, '2'),
                                        ('kalorimetre_sensor', 'r_kalorimetre_sag' if s > 0 else 'r_kalorimetre_sol', '3'),
                                        (None, 'balans_vanasi', '4'), ('r_kuresel_vana', 'r_kuresel_vana', '5')], SET_X):
                if sg:
                    self.sembol(sg, (xg + s * x, hg), 0.0, 0.6, no)
                if sd:
                    self.sembol(sd, (xg + s * x, hd), 0.0, 0.6, None if sg else no)
            cz.yazi((xg + s * 120, hg + 22), 'KS - KALORİMETRE SETİ', 6.5, 'ROTAS-CIHAZ')
        else:
            self.h.D([(xc0, hd), (xg, hd)])
        kn = f"({gir['kno']}) " if gir.get('kno') else ''
        cz.yazi((xg + s * 120, hd - 13), f"{kn}{gir['Q']:.0f}W-{gir['dn']}", 6.5, C.CAPK)
        # devreler: j = 0 en yakın radyatör (en iç döngü), j = n-1 en uzak (en dış: en soldaki ağız, en üst/alt seviye)
        x_r0 = xc0 + s * (W + 70.0)
        for j, dv in enumerate(dvs):
            k = n - 1 - j
            ox = xc0 + s * (geo.KOL_X0 + k * geo.KOL_ADIM)
            U = yf + Y['U0'] + j * Y['adim']
            B = yf + Y['B0'] - j * Y['adim']
            xr = x_r0 + s * j * SLOT
            yr = yf + Y['rad']
            self.h.G([(ox, yc + geo.KOL_H), (ox, U), (xr, U), (xr, yr + 50.0)])
            self.h.D([(xr + s * geo.RAD_W, yr - 10.0), (xr + s * geo.RAD_W, B), (ox, B), (ox, yc)])
            self.radyator(dv['rad'], xr, yr, dv['no'], s, prc.get(dv['no']))
        return x_r0 + s * n * SLOT

    def radyator(self, r, xr, yr, no, s, p):
        cz = self.cz
        mm = r['m']
        ad = 'r_havlupan_sema' if r['tip'] == 'Banyopan' else 'r_radyator_sema'
        cz.blok(ad, (xr, yr), 0.0, s, 1.0, 'ROTAS-RADYATOR')
        cz.engel.append(sbox(min(xr, xr + s * geo.RAD_W), yr, max(xr, xr + s * geo.RAD_W), yr + geo.RAD_H).exterior)
        cx = xr + s * geo.RAD_W / 2
        t1 = (f"HAVLUPAN {r['boy'] * 1000:.0f} / {r['ver']:.0f} W" if r['tip'] == 'Banyopan'
              else f"{r['model']}x{r['boy'] * 1000:.0f} / {r['ver']:.0f} W")
        t2 = f"{mm['ad']} {mm['no']}  {mm['ti']:.0f}°C"
        t3 = f"D{no}" + (f"  {p['Q']:.0f}W-{p['dn']}" if p else '')
        if p and p.get('kno'):
            t3 = f"({p['kno']}) " + t3
        for t, dy, lay in ((t1, 27.0, 'ROTAS-RADYATOR'), (t2, 20.0, 'ROTAS-RADYATOR'), (t3, 13.0, C.CAPK)):
            cz.yazi((cx, yr + dy), t, 5.2, lay, maske=False)

    # ------------------------------------------------------------ çizim
    def ciz(self, x0, y0):
        cz, P, M, A = self.cz, self.P, self.M, self.A
        katlar = M['katlar']
        merkezi = P['sistem'] == 'merkezi'
        dkat = [k for k in katlar if k['daireler']]
        DW = self.daire_genislik()
        if merkezi:
            self.kdh = kazan_girdisi(P, self.pomp)           # onaylı kazan dairesi paftasının JSON'u (prensip şeması YOK)
            Hb = BANT
            xdA = x0 + 100.0
            xgA = xdA + DW
            xgB = xgA + KD_ARA
            xdB = xgB + DW
            XK = {'A': (xgA, xdA, -1), 'B': (xgB, xdB, 1)}
            x_sag = xdB + 150.0
        else:
            Hb = BANT
            XK = {'A': (x0 + 400.0, x0 + 400.0, 1), 'B': (x0 + 400.0 + DW + 300.0, x0 + 400.0 + DW + 300.0, 1)}
            x_sag = XK['B'][0] + DW + 100.0
        yf_of = {}
        yy = y0
        for i, k in enumerate(katlar):
            yf_of[k['kod']] = yy
            yy += Hb if i == 0 else BANT
        for k in katlar:
            yf = yf_of[k['kod']]
            cz.pl([(x0, yf), (x_sag, yf)], 'ROTAS-KAT-BANDI', engel=False)
            kot = f"{k['kot']:+.2f}".replace('+0.00', '±0.00')
            cz.yazi((x0 + 15, yf + 12), f"{k['ad']}  {kot}", 14, 'ROTAS-KAT-BANDI', al='BL')
        ust = yf_of[katlar[-1]['kod']] + BANT
        cz.pl([(x0, ust), (x_sag, ust)], 'ROTAS-KAT-BANDI', engel=False)
        cz.yazi((x0 + 15, ust + 12), 'ÇATI', 14, 'ROTAS-KAT-BANDI', al='BL')
        for k in dkat:
            yf = yf_of[k['kod']]
            for dad in ('A', 'B'):
                xg, xd, s = XK[dad]
                if not merkezi:
                    self.kombi(xg, yf)
                self.daire(k, dad, xg, xd, yf, merkezi, s)
                cz.yazi((xg + s * 60.0, yf + 283.0), f"DAİRE {dad} – {k['ad']}", 10, 'ROTAS-YAZI', al='BL' if s > 0 else 'BR')
        y_alt = y0 - 60
        if merkezi:
            self.bodrum(XK, dkat, yf_of, y0)
        self.hatlari_ciz()
        self.etiketler()
        xm = (x0 + x_sag) / 2
        cz.yazi((xm, ust + 150), 'KALORİFER TESİSAT PROJESİ KOLON ŞEMASI', 40, 'ROTAS-BASLIK')
        cz.yazi((xm, ust + 95), 'DENEME – Güngören B1 Blok verisi; kolektörlü dağıtım, mahal yerleşimi temsilî; düşey ölçek 1/50 '
                '(kat yüksekliği 3,00 m), yataylar ölçeksiz', 16, 'ROTAS-DENEME')
        notlar = ['NOTLAR:',
                  'Gidiş hattı sürekli (kırmızı), dönüş hattı kesikli (turuncu). Hatlar birbirini KESMEZ (atlatma / köprü yoktur).',
                  'Daire içi dağıtım KOLEKTÖRLÜDÜR: her radyatör kolektörden ayrı PE-Xc/Al/PE-X gidiş-dönüş hattı ile beslenir (D1…Dn).',
                  'Radyatör içindeki 3. satır devre numarası, kümülatif yük ve boru çapıdır (ör. D5 1454W-Ø16x2); (n) kritik devre parça no.',
                  f"Yük esası: {'seçilen radyatör kapasitesi' if P['yuk_esasi'] == 'radyator' else 'mahal ısı kaybı'}; rejim {M['tg']:.0f}/{M['td']:.0f} °C.",
                  'Her radyatör gidişinde termostatik radyatör vanası, dönüşünde ayar (dönüş) rakoru; kolektör ağızlarında debimetre ve vana.']
        if merkezi:
            notlar += ['Her daire girişinde KS – KALORİMETRE SETİ (hol sayaç dolabında): 1 küresel vana, 2 pislik tutucu, 3 kalorimetre '
                       '(debi ölçer dönüşte + gidiş/dönüş sıcaklık sensörü), 4 balans vanası, 5 küresel vana. Okuma (M-Bus) bağlantısı '
                       'elektrik projesindedir; bu paftada elektrik kalemi çizilmez.',
                       'Gidiş kolonları (K1, K2) ortada, dönüş kolonları dışta; bodrumda gidiş dağıtımı üstte, dönüş toplama altta; '
                       'ana gidiş ve dönüş hatları kazan dairesine bağlanır. Kolonlar siyah çelik (TS EN 10255).',
                       'Kazan dairesi detayı için bkz. KAZAN DAİRESİ PLAN - KESİT paftası (plan 1/50, kesit A-A, kısmi görünüş B, '
                       'cihaz listesi).']
        for i, s_ in enumerate(notlar):
            cz.yazi((x0 + 20, y0 - 60 - i * 22), s_, 12, 'ROTAS-YAZI', al='BL')
        y_alt = y0 - 60 - len(notlar) * 22 - 40
        self.detay(x_sag + 250.0, ust + 50.0)
        xr = x_sag + 250.0 + 2350.0
        cz.pl([(x0 - 60, y_alt), (xr, y_alt), (xr, ust + 220),
               (x0 - 60, ust + 220)], 'ROTAS-PAFTA', w=2.0, kapali=True, engel=False)
        return xr

    def _tablo_alt(self, x0):
        from ezdxf import bbox
        es = [e for e in self.cz.msp if e.dxf.layer.startswith('ROTAS-HESAP-')]
        b = bbox.extents(es, fast=True)
        return b.extmin.y if b.has_data else 0.0

    def kombi(self, xg, yf):
        cz = self.cz
        cz.blok('r_kombi', (xg, yf + Y['yc']), 0.0, 1.0, 1.0, 'ROTAS-CIHAZ')
        cz.yazi((xg - 23.0, yf + Y['yc'] - 20.0), f"H. KOMBİ {self.P['kombi']['kapasite_kW']} kW", 7, 'ROTAS-CIHAZ')
        cz.engel.append(sbox(xg - 56, yf + Y['yc'] - 10, xg, yf + Y['yc'] + 50).exterior)

    # ------------------------------------------------------------ bodrum: gidiş dağıtımı + dönüş toplama → KAZAN DAİRESİNE
    def bodrum(self, XK, dkat, yf_of, y0):
        """R5: prensip şeması YOK. Gidiş dağıtımı (üst) K1-K2 gidiş kolon diplerini, dönüş toplama (alt) dönüş kolon
        diplerini birleştirir; ana gidiş ve dönüş, iki hattın arasından sağa "KAZAN DAİRESİNE" okuyla sonlanır.
        Gidiş inişi dönüş seviyesine, dönüş çıkışı gidiş seviyesine ulaşmaz → kesişme 0, atlatma yok."""
        cz, A = self.cz, self.A
        xgA, xdA, _ = XK['A']
        xgB, xdB, _ = XK['B']
        gy, dy_ = y0 + 210.0, y0 + 60.0
        xm = xgA + 200.0                     # ana gidiş inişi
        xm2 = xm + 40.0                      # ana dönüş çıkışı
        xe = xm + 260.0                      # ok uçları
        ya, yb = gy - 55.0, dy_ + 55.0
        gx = xm
        self.h.G([(xgA, gy), (xgB, gy)])
        self.h.D([(xdA, dy_), (xdB, dy_)])
        self.h.G([(xm, gy), (xm, ya), (xe, ya)])
        self.h.D([(xm2, dy_), (xm2, yb), (xe, yb)])
        for yy, lay in ((ya, C.GID), (yb, C.DON)):     # ok (sembol katmanı: boru sayılmaz)
            ok = cz.pl([(xe, yy, 9.0, 0.0, 0.0), (xe + 22.0, yy, 0.0, 0.0, 0.0)], SEM, engel=True)
            ok.dxf.color = cz.doc.layers.get(lay).color          # ok rengi hattın rengiyle aynı
        cz.yazi((xe + 32.0, (ya + yb) / 2.0), 'KAZAN DAİRESİNE', 12.0, 'ROTAS-CIHAZ', al='ML')
        cz.yazi((xe - 40.0, ya + 8.0), 'GİDİŞ', 7.0, 'ROTAS-YAZI', al='BC')
        cz.yazi((xe - 40.0, yb + 8.0), 'DÖNÜŞ', 7.0, 'ROTAS-YAZI', al='BC')
        cz.yazi((xe + 32.0, yb - 28.0), 'KAZAN DAİRESİ DETAYI İÇİN BKZ. KAZAN DAİRESİ PLAN - KESİT PAFTASI', 8.0,
                'ROTAS-YAZI', al='ML')
        katlar = self.M['katlar']
        ust_kat = max(yf_of[k['kod']] for k in dkat)
        y_ust = ust_kat + 262.0
        for i, dad in enumerate(('A', 'B')):
            xg, xd, s = XK[dad]
            self.h.G([(xg, gy), (xg, y_ust)])
            self.h.D([(xd, dy_), (xd, y_ust)])
            for xx in (xg, xd):
                semb.ciz(cz.msp, 'r_ohac', (xx, y_ust), rot=0.0, olcek=1.0, kat='ROTAS-VANA')
            cz.msp.add_circle((xg - s * 40.0, y_ust + 10.0), 14.0, dxfattribs={'layer': 'ROTAS-CIHAZ'})
            cz.yazi((xg - s * 40.0, y_ust + 10.0), f'K{i + 1}', 12.0, 'ROTAS-CIHAZ', maske=False)
            # kolon dipleri: küresel vana + boşaltma (gidişte dışa / ortaya, dönüşte dışa)
            self.sembol('r_kuresel_vana', (xg, gy + 30.0), 90.0, 0.6)
            self.sembol('r_kuresel_vana', (xd, dy_ + 30.0), 90.0, 0.6)
            for xx, yy, lay, yon in ((xg, gy + 12.0, C.GID, -s), (xd, dy_ + 12.0, C.DON, s)):
                cz.pl([(xx, yy), (xx + yon * 22.0, yy)], lay, w=1.0, engel=True)
                semb.ciz(cz.msp, 'r_bosaltma', (xx + yon * 18.0, yy), rot=0.0 if yon > 0 else 180.0, olcek=0.6, kat=SEM)
        cz.yazi((xgA + 20.0, gy + 40.0), 'BODRUM KAT – GİDİŞ DAĞITIMI (üst) / DÖNÜŞ TOPLAMA (alt)',
                16, 'ROTAS-KAT-BANDI', al='BL')
        self.kolon_parcalar = [p for p in A.parcalar if p['tur'] in ('kolon', 'kolon_dip', 'kazan')]
        kk = [k['kod'] for k in katlar]
        for p in self.kolon_parcalar:
            dad = p['daire']
            if p['tur'] == 'kazan':
                self.etiket.append((p, (xm, ya), (xe - 80.0, ya), False, 1))
            elif p['tur'] == 'kolon_dip':
                self.etiket.append((p, (gx, gy), (xgB, gy), False, 1))
            else:
                xg, xd, s = XK[dad]
                i_ = kk.index(p['kat'])
                yt = yf_of[p['kat']] + Y['hg']
                yalt = yf_of[kk[i_ - 1]] + Y['hg'] if kk[i_ - 1] in [k['kod'] for k in dkat] else gy + 45
                self.etiket.append((p, (xg, yalt), (xg, yt), True, -s))

    def hatlari_ciz(self):
        cz = self.cz
        once = []
        for p in self.h.g:
            if len(p) > 1 and LineString(p).length > 0:
                once.append(cz.pl(p, C.GID, w=1.0))
        for p in self.h.d:
            if len(p) > 1 and LineString(p).length > 0:
                once.append(cz.pl(p, C.DON, w=1.0, ltscale=12.0))
        cz.once_ciz(once)

    def etiketler(self):
        cz = self.cz
        h = 6.5
        for p, a, b, dikey, yon in self.etiket:
            txt = f"{p['Q']:.0f}W-{p['dn']}"
            kn = p.get('kno')
            if kn:
                txt = f"({kn}) " + txt
            if dikey:
                ym = (a[1] + b[1]) / 2
                if yon < 0:
                    cz.yazi((a[0] - 6.0, ym), txt, h, C.CAPK, al='BC', rot=90.0)
                else:
                    cz.yazi((a[0] + 6.0, ym), txt, h, C.CAPK, al='TC', rot=90.0)
            else:
                xm = (a[0] + b[0]) / 2
                cz.yazi((xm, a[1] + 6.0), txt, h, C.CAPK, al='BC')

    # ------------------------------------------------------------ kesit / görünüş detayı (1/10)
    def detay(self, x, y):
        detay_ciz(self.cz, self.P, self.A, x, y)


# ====================================================================== onaylı kazan dairesi paftası
def kazan_girdisi(P, pomp):
    """onaylı kazan dairesi paftasının JSON girdisi: kazan adedi/kapasitesi ve zon pompası debi/basma radyatör
    hesabından (pomp). PRENSİP ŞEMASI ÇİZİLMEZ (14.10.2026 kullanıcı reddi)."""
    kp = P.get('kazan_dairesi', {})
    adet = int(kp.get('kazan_adet', 2))
    q = pomp['Q_W'] / 1000.0 * (1 + kp.get('kapasite_payi', 0.10))
    kw = math.ceil(q / adet / 5.0) * 5.0
    J = {
        'proje': f"{P['proje']['ad']} – MERKEZİ ISITMA KAZAN DAİRESİ", 'deneme': True,
        'rejim': {'gidis': 90, 'donus': 70},
        'kazan': {'adet': adet, 'kapasite_kw': kw, 'tip': kp.get('kazan_tip', 'Duvar tipi yoğuşmalı, doğalgaz yakıtlı'),
                  'pompa': kp.get('kazan_pompa', {'ad': 'P-K', 'debi': round(kw / (1.163 * 20), 1), 'basma': 4.0})},
        'denge_kabi': {'cap': kp.get('denge_kabi', 'Ø200')},
        'genlesme': {'hacim_l': kp.get('genlesme_l', 200), 'maks_bar': 6.0},
        'emniyet': {'ventil_bar': 6.0, 'ventil_cap': 'DN25'},
        'zonlar': [{'ad': 'P-01', 'aciklama': 'RADYATÖR DEVRESİ (K1-K2)', 'debi': round(pomp['V'], 2),
                    'basma': round(pomp['H_mSS'], 1), 'yedek': True, 'adet': 1}],
        'boyler': None, 'sirkulasyon': None, 'notralizasyon': kp.get('notralizasyon', False),
        'baca': {'cap': kp.get('baca', 'Ø200'), 'tip': 'Paslanmaz çelik çift cidarlı'},
        'dogalgaz': {'vana': True, 'filtre': True, 'selenoid': True, 'alarm': True, 'regulator': None},
        'doldurma': True,
    }
    return dict(J=J, kw=kw, adet=adet)


def kazan_dairesi_paftasi(cz, kd, x0, y0):
    """ONAYLI kazan dairesi paftası (plan + kesit A-A + kısmi görünüş + lejant + cihaz listesi) — plan_kesit.py
    onayli_kazan_dairesi() ile, radyatör hesabından gelen JSON (kazan_girdisi). Dönüş: KapsamKutusu (.satir, .girdi ...)."""
    sys.path.insert(0, os.path.join(_KOK, '..', 'kazan_dairesi'))
    import plan_kesit as PK
    k = PK.onayli_kazan_dairesi(cz.doc, kd['J'], x0, y0)          # varsayılan: onaylı numaralar, MTY'siz semboller
    # prensip şeması teslimde yok → onaylı paftanın ona atıf yapan iki yazısı yalnız metin olarak düzeltilir
    # (yerleşim / görünüş aynı; metinler kısalır)
    for e in cz.msp.query('TEXT MTEXT'):
        t = e.dxf.text if e.dxftype() == 'TEXT' else e.text
        for eski, yeni in PRENSIP_ATIF.items():
            if eski in t:
                t = t.replace(eski, yeni)
                if e.dxftype() == 'TEXT':
                    e.dxf.text = t
                else:
                    e.text = t
    return k


PRENSIP_ATIF = {
    'KAZAN DAİRESİ CİHAZ LİSTESİ (PRENSİP ŞEMASI İLE AYNI NUMARALAR)': 'KAZAN DAİRESİ CİHAZ LİSTESİ',
    'Numaralar prensip şeması ve cihaz listesi ile aynıdır; tüm vana/cihazlar şemada gösterilmiştir.':
        'Numaralar plan, kesit ve cihaz listesinde aynıdır.',
}


# ====================================================================== detay: kolektör dolabı + kalorimetre seti görünüşü
def detay_ciz(cz, P, A, x, y):
    """1/10 görünüş (model birimi cm, 1/50 paftada ×5 çizilir). Sol: hol sayaç (kalorimetre) dolabı, sağ: kolektör dolabı,
    en sağ: A-A kesiti."""
    K = 5.0
    DT = 'ROTAS-DETAY'
    GL, DL = [], []

    class _P:
        def pl(self, pts, lay, w=0.0, ltscale=None, engel=False, kapali=False):
            if lay == C.GID:
                GL.append((pts, w))
            elif lay == C.DON:
                DL.append((pts, w))
            else:
                cz.pl(pts, lay, w=w, ltscale=ltscale, engel=engel, kapali=kapali)
    czp = _P()
    if DT not in cz.doc.layers:
        cz.doc.layers.add(DT, color=7)
    merkezi = P['sistem'] == 'merkezi'
    f = lambda px, py: (x + px * K, y - py * K)            # (gerçek cm, yukarıdan aşağı) → model
    cz.yazi((x + 1050, y + 60), 'KOLEKTÖR DOLABI VE KALORİMETRE SETİ GÖRÜNÜŞÜ / KESİTİ  ÖLÇEK: 1 / 10', 22, 'ROTAS-BASLIK', maske=False)
    taban = 300.0                      # döşeme üst kotu (gerçek cm, detay üstünden)
    ust_kot = taban
    # döşeme + şap
    czp.pl([f(-10, taban), f(205, taban)], DT, w=2.0, engel=False)
    czp.pl([f(-10, taban + 8), f(205, taban + 8)], DT, engel=False)
    cz.yazi(f(200, taban + 4), 'ŞAP (PEX HATLAR ŞAP İÇİNDE, İZOLASYONLU)', 7, DT, al='MR', maske=False)
    cz.yazi(f(200, taban - 3), '±0,00 BİTMİŞ DÖŞEME', 7, DT, al='MR', maske=False)
    lst = []
    # -------------------------------------------------- kalorimetre dolabı (hol)
    if merkezi:
        bx0, bx1, by0, by1 = 0.0, 50.0, 120.0, 220.0       # dolap: 50 × 100, alt kenar +80
        czp.pl([f(bx0, by0), f(bx1, by0), f(bx1, by1), f(bx0, by1)], DT, w=1.5, kapali=True, engel=False)
        czp.pl([f(bx0 + 2, by0 + 2), f(bx1 - 2, by0 + 2), f(bx1 - 2, by1 - 2), f(bx0 + 2, by1 - 2)], DT, kapali=True, engel=False)
        # R3: gidiş sağda (x=33), dönüş solda (x=17) → kolektöre kadar hatlar paralel, kesişmesiz (atlatma yok)
        gx, dx_ = 33.0, 17.0
        g = [f(gx, 40), f(gx, by1 + 22), f(76, by1 + 22)]
        d = [f(dx_, 40), f(dx_, by1 + 30), f(70, by1 + 30)]
        czp.pl(g, C.GID, w=2.0, engel=False); czp.pl(d, C.DON, w=2.0, ltscale=3.0, engel=False)
        cz.yazi(f(gx + 4.6, 46), 'KOLONDAN (GİDİŞ)', 7, C.GID, al='BR', rot=90, maske=False)
        cz.yazi(f(dx_ - 3, 46), 'KOLONA (DÖNÜŞ)', 7, C.DON, al='BR', rot=90, maske=False)
        el = [('r_kuresel_vana', 'r_kuresel_vana', 135.0, '1'), ('r_pislik_tutucu', None, 155.0, '2'),
              ('kalorimetre_sensor', 'r_kalorimetre_sag', 175.0, '3'), (None, 'balans_vanasi', 195.0, '4'),
              ('r_kuresel_vana', 'r_kuresel_vana', 212.0, '5')]
        for sg, sd, yy, no in el:
            for sm, xx in ((sg, gx), (sd, dx_)):
                if sm:
                    p = f(xx, yy)
                    cz.maske([(p[0] - 30, p[1] - 22), (p[0] + 30, p[1] - 22), (p[0] + 30, p[1] + 22), (p[0] - 30, p[1] + 22)])
                    semb.ciz(cz.msp, sm, p, rot=-90.0, olcek=2.2, kat=SEM)
            cz.yazi(f(bx0 - 6, yy), no, 10, DT, al='MR', maske=False)
        cz.yazi(f(25, by0 - 6), 'HOL – KALORİMETRE (SAYAÇ) DOLABI 50×100×15', 8, DT, maske=False)
        cz.yazi(f(25, by0 - 13), 'okuma kapağı ortak alana açılır', 7, DT, maske=False)
        lst += ['1  Küresel vana (tam geçişli, PN16) – daire girişi', '2  Pislik tutucu (Y tipi, paslanmaz elek)',
                '3  Kalorimetre (ısı pay ölçer): ultrasonik debi ölçer DÖNÜŞTE + gidiş/dönüş Pt1000 sıcaklık sensörü',
                '4  Balans (dengeleme) vanası – ölçüm nipelli, ön ayarlı', '5  Küresel vana – daire çıkışı',
                'Dolaptan sonra hatlar daire kapısı eşiğinden şap içinde kolektör dolabına gider.']
        xk0 = 90.0
    else:
        xk0 = 20.0
        cz.yazi(f(xk0 - 12, 60), 'KOMBİDEN', 8, DT, al='ML', maske=False)
    # -------------------------------------------------- kolektör dolabı
    n = max(len(p_.get('cocuk', [])) for p_ in A.parcalar if p_['tur'] == 'giris')
    W = 15.0 + n * 7.0 + 10.0
    kx0, kx1, ky0, ky1 = xk0, xk0 + W, 190.0, 260.0              # dolap alt kenarı +40
    czp.pl([f(kx0, ky0), f(kx1, ky0), f(kx1, ky1), f(kx0, ky1)], DT, w=1.5, kapali=True, engel=False)
    czp.pl([f(kx0 + 2, ky0 + 2), f(kx1 - 2, ky0 + 2), f(kx1 - 2, ky1 - 2), f(kx0 + 2, ky1 - 2)], DT, kapali=True, engel=False)
    yg_, yd_ = 205.0, 225.0                                        # gövdeler
    for yy, lay in ((yg_, C.GID), (yd_, C.DON)):
        czp.pl([f(kx0 + 6, yy - 1.5), f(kx1 - 6, yy - 1.5), f(kx1 - 6, yy + 1.5), f(kx0 + 6, yy + 1.5)], KOLK, kapali=True, engel=False)
    # besleme girişi (sol): gidiş üst gövdeye, dönüş alt gövdeye
    if merkezi:
        czp.pl([f(76, by1 + 22), f(76, taban + 4), f(kx0 - 6, taban + 4), f(kx0 - 6, yg_), f(kx0 + 6, yg_)], C.GID, w=2.0, engel=False)
        czp.pl([f(70, by1 + 30), f(70, taban + 6), f(kx0 - 2, taban + 6), f(kx0 - 2, yd_), f(kx0 + 6, yd_)], C.DON, w=2.0, ltscale=3.0, engel=False)
    else:
        czp.pl([f(kx0 - 2, 60), f(kx0 - 2, yg_), f(kx0 + 6, yg_)], C.GID, w=2.0, engel=False)
        czp.pl([f(kx0 - 6, 60), f(kx0 - 6, yd_), f(kx0 + 6, yd_)], C.DON, w=2.0, ltscale=3.0, engel=False)
    for i in range(n):
        xg_ = kx0 + 15.0 + i * 7.0
        xd2 = xg_ + 3.0
        czp.pl([f(xg_, yg_ + 1.5), f(xg_, yd_ - 1.5)], C.GID, w=1.0, engel=False)
        czp.pl([f(xg_, yd_ + 1.5), f(xg_, taban + 3)], C.GID, w=1.0, engel=False)
        czp.pl([f(xd2, yd_ + 1.5), f(xd2, taban + 5)], C.DON, w=1.0, ltscale=2.0, engel=False)
        cz.msp.add_circle(f(xg_, yg_ + 6), 1.0 * K, dxfattribs={'layer': SEM})     # debimetre
        cz.msp.add_circle(f(xd2, yd_ + 6), 0.8 * K, dxfattribs={'layer': SEM})     # dönüş vanası
    for xx in (kx0 + 8, kx1 - 8):
        cz.msp.add_circle(f(xx, yg_ - 5), 0.9 * K, dxfattribs={'layer': SEM})     # purjör
        cz.msp.add_circle(f(xx, yd_ - 5), 0.9 * K, dxfattribs={'layer': SEM})
    cz.yazi(f((kx0 + kx1) / 2, ky0 - 6), f'KOLEKTÖR DOLABI ({n} AĞIZ) {W:.0f}×70×11 – SIVA ALTI', 8, DT, maske=False)
    cz.yazi(f(kx1 + 3, yg_), 'GİDİŞ KOLEKTÖRÜ (debimetreli)', 7, C.GID, al='ML', maske=False)
    cz.yazi(f(kx1 + 3, yd_), 'DÖNÜŞ KOLEKTÖRÜ (vanalı)', 7, C.DON, al='ML', maske=False)
    cz.yazi(f(kx1 + 3, yg_ - 5), 'otomatik purjör + boşaltma vanası', 6, DT, al='ML', maske=False)
    cz.yazi(f((kx0 + kx1) / 2, taban + 14), 'RADYATÖRLERE (D1…Dn) PE-Xc/Al/PE-X Ø16x2, GİDİŞ-DÖNÜŞ PARALEL, DUVAR BOYU', 7, DT, maske=False)
    # ölçü
    cz.yazi(f(kx0 - 10, (ky1 + taban) / 2), f'+{taban - ky1:.0f}', 8, DT, al='MR', maske=False)
    czp.pl([f(kx0 - 8, ky1), f(kx0 - 8, taban)], DT, engel=False)
    # -------------------------------------------------- A-A kesiti
    sx = kx1 + 50.0
    czp.pl([f(sx, 150), f(sx, taban)], DT, w=1.5, engel=False)             # duvar iç yüzü
    czp.pl([f(sx + 15, 150), f(sx + 15, taban)], DT, w=1.5, engel=False)   # duvar dış yüzü
    czp.pl([f(sx, ky0), f(sx + 11, ky0), f(sx + 11, ky1), f(sx, ky1)], DT, w=1.0, engel=False)  # niş
    czp.pl([f(sx - 2, ky0), f(sx - 2, ky1)], DT, w=2.0, engel=False)       # kapak
    cz.msp.add_circle(f(sx + 6, yg_), 1.6 * K, dxfattribs={'layer': KOLK})
    cz.msp.add_circle(f(sx + 6, yd_), 1.6 * K, dxfattribs={'layer': KOLK})
    czp.pl([f(sx + 4, yd_ + 2), f(sx + 4, taban + 4), f(sx - 30, taban + 4)], C.GID, w=1.0, engel=False)
    czp.pl([f(sx + 8, yd_ + 2), f(sx + 8, taban + 6), f(sx - 30, taban + 6)], C.DON, w=1.0, ltscale=2.0, engel=False)
    czp.pl([f(sx - 40, taban), f(sx + 30, taban)], DT, w=2.0, engel=False)
    czp.pl([f(sx - 40, taban + 8), f(sx + 30, taban + 8)], DT, engel=False)
    cz.yazi(f(sx + 7, 140), 'A-A KESİTİ', 10, DT, maske=False)
    cz.yazi(f(sx + 20, (ky0 + ky1) / 2), 'duvar nişi 11 cm', 7, DT, al='ML', maske=False)
    # açıklama listesi
    lst += ['KD  Kolektör dolabı: paslanmaz kolektör, gidişte debimetre, dönüşte vana, uçlarda otomatik purjör + boşaltma.',
            'Radyatörlerde termostatik vana (gidiş) ve ayar rakoru (dönüş). Kolektör dolabı ile kalorimetre arası şap içinde izolasyonlu.']
    for p, w in GL:                      # R3: köprü yok (güzergâh kesişmesiz kuruldu)
        cz.pl(p, C.GID, w=w, engel=False)
    for p, w in DL:
        cz.pl(p, C.DON, w=w, ltscale=3.0, engel=False)
    for i, s in enumerate(lst):
        cz.yazi((x, y - (taban + 30) * K - i * 20), s, 10, 'ROTAS-YAZI', al='BL', maske=False)


def ciz(cz, P, M, A, pf, pomp, x0=0.0, y0=-4200.0):
    s = Sema(cz, P, M, A, pf, pomp)
    xr = s.ciz(x0, y0)
    return s
