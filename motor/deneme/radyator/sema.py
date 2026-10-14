# -*- coding: utf-8 -*-
"""KALORİFER TESİSAT PROJESİ KOLON ŞEMASI: kat bantları (düşey ölçekli, kat yüksekliği gerçek), yataylar ölçeksiz,
gidiş sürekli / dönüş kesikli, radyatörler MTY-RADYATOR KOLON blokları (kapasite + mahal), hat etiketi "Q W-DNxx",
kritik devre parça numaraları (n)."""
import math
from shapely.geometry import LineString, Polygon
import ciz as C
import ag

BANT = 300.0         # kat bandı yüksekliği (kat yüksekliği 3,00 m, 1/50 ölçek cm)
SLOT = 185.0         # radyatör aralığı (ölçeksiz yatay)
DY = 32.0            # alt seviye (kol) yükseklik farkı
HG0, HD0 = 40.0, 26.0   # ana seviye gidiş / dönüş yüksekliği (bant tabanından)
RADY = 125.0         # radyatör bloğu taban yüksekliği (blok gövdesi +15)
KOLD = 14.0          # kolon gidiş-dönüş aralığı


class Hatlar:
    def __init__(self):
        self.g, self.d = [], []

    def G(self, pts):
        self.g.append([tuple(p) for p in pts])

    def D(self, pts):
        self.d.append([tuple(p) for p in pts])


def _yuk_txt(p):
    return f"{p['Q']:.0f}W-{p['dn']}"


class Sema:
    def __init__(self, cz, P, M, A, pf):
        self.cz, self.P, self.M, self.A, self.pf = cz, P, M, A, pf
        self.h = Hatlar()
        self.etiket = []        # (parça, segment noktaları a,b, dikey mi)
        self.vanalar = []

    # ------------------------------------------------------------ daire (özyinelemeli yol çizimi)
    def daire(self, kat, dad, xg0, xd0, yf, kok_parca_ust=None):
        """xg0/xd0: daire gidiş/dönüş başlangıç x'i (kolon veya kombi); başlıklar sağa doğru"""
        pl = self.pf(kat, dad)
        prc = [p for p in self.A.parcalar if p['kat'] == kat['kod'] and p['daire'] == dad and p['tur'] in ('daire', 'radyator')]
        by_yol = {}
        for p in prc:
            by_yol.setdefault(p['yol'], []).append(p)
        yollar = pl['yollar']
        imlec = [xg0 + 70.0]

        def tekil_mi(y):
            return len(y['rads']) == 1 and not [z for z in yollar if z['ebeveyn'] == y['id']]

        def radyator(r, xg, hg, hd, parca):
            """xg: gidiş yükselticisi x; dönüş yükselticisi xg+5 (blok bağlantıları)"""
            bx = xg + 5.0
            by = yf + RADY - 15.0
            ban = r['tip'] == 'Banyopan'
            mm = r['m']
            kap = f"{r['ver']:.0f} W"
            if ban:
                rad_txt = f"BANYOPAN {r['boy'] * 1000:.0f} / {kap}"
                self.cz.blok('MTY-RADYATÖR BANYOPAN KOLON', (bx, by), 0, 1.0, 1.0, 'ROTAS-RADYATOR',
                             ozn={'RAD_001': rad_txt, 'NO_001': f"{mm['no']}", 'DERECE_001': f"{mm['ti']:.0f}°C",
                                  'MAHAL_001': mm['ad']},
                             ozn_h={'RAD_001': 8.0, 'NO_001': 8.0, 'DERECE_001': 8.0, 'MAHAL_001': 8.0},
                             ozn_konum={'RAD_001': (bx + 45, by + 152), 'MAHAL_001': (bx + 25, by + 165), 'NO_001': (bx + 68, by + 165),
                                        'DERECE_001': (bx + 92, by + 165)}, maske=True)
            else:
                rad_txt = f"{r['model']}x{r['boy'] * 1000:.0f} / {kap}"
                self.cz.blok('MTY-RADYATOR KOLON', (bx, by), 0, 1.0, 1.0, 'ROTAS-RADYATOR',
                             ozn={'RAD_001': rad_txt, 'NO_001': f"{mm['no']}", 'DERECE_001': f"{mm['ti']:.0f}°C", 'MAHAL_001': mm['ad']},
                             ozn_h={'RAD_001': 8.0, 'NO_001': 8.0, 'DERECE_001': 8.0, 'MAHAL_001': 8.0},
                             ozn_konum={'RAD_001': (bx + 79, by + 74), 'MAHAL_001': (bx + 60, by + 88), 'NO_001': (bx + 104, by + 88),
                                        'DERECE_001': (bx + 128, by + 88)}, maske=True)
            self.h.G([(xg, hg), (xg, by + 57.5)])
            self.h.D([(bx, hd), (bx, by + 22.5)])
            if parca is not None:
                self.etiket.append((parca, (xg, hg), (xg, by + 57.5), True))

        def yol_ciz(y, xg_bas, hg, hd, seviye):
            """yolu seviyesinde yatay başlık olarak çiz; olaylar (çocuk yol / T radyatör / uç radyatör) soldan sağa"""
            parts = sorted([p for p in by_yol.get(y['id'], []) if p['tur'] == 'daire'], key=lambda p: p['s0'])
            Ltop = y['ls'].length
            olay = []
            for z in yollar:
                if z['ebeveyn'] == y['id']:
                    olay.append((z['s0'], 'yol', z))
            for r in y['rads']:
                son = r['s_uzak'] >= Ltop - 1
                olay.append((Ltop if son else r['s_yak'], 'rad', r))
            olay.sort(key=lambda t: (round(t[0], 3), 0 if t[1] == 'rad' else 1))
            xs = {0.0: xg_bas}
            x = xg_bas
            for s, tur, ref in olay:
                x = max(x + 60.0, imlec[0])
                if tur == 'rad':
                    son = s >= Ltop - 1e-6
                    if son:
                        par = parts[-1] if parts else None
                        radyator(ref, x, hg, hd, None)
                    else:
                        tp = [p for p in by_yol.get(y['id'], []) if p['tur'] == 'radyator' and p['rad'] is ref]
                        radyator(ref, x, hg, hd, tp[0] if tp else None)
                    imlec[0] = x + SLOT
                else:
                    z = ref
                    zparts = sorted([p for p in by_yol.get(z['id'], []) if p['tur'] == 'daire'], key=lambda p: p['s0'])
                    if tekil_mi(z):
                        radyator(z['rads'][0], x, hg, hd, zparts[0] if zparts else None)
                        imlec[0] = x + SLOT
                    else:
                        hg2, hd2 = hg + DY * 1.0 + 14, hd + DY * 1.0 + 14
                        self.h.G([(x, hg), (x, hg2)])
                        self.h.D([(x + 5.0, hd), (x + 5.0, hd2)])
                        imlec[0] = x + 10.0
                        yol_ciz(z, x, hg2, hd2, seviye + 1)
                xs[round(s, 3)] = x
            x_son = x
            # başlıklar
            self.h.G([(xg_bas, hg), (x_son, hg)])
            self.h.D([(xg_bas + (5.0 if seviye else 0.0), hd), (x_son + 5.0, hd)])
            # parça etiket segmentleri
            for p in parts:
                xa = xs.get(round(p['s0'], 3), xg_bas)
                xb_ = xs.get(round(p['s1'], 3), x_son)
                self.etiket.append((p, (xa, hg), (xb_, hg), False))

        hg, hd = yf + HG0, yf + HD0
        # kökten başlık başlangıcına bağlantı
        self.h.G([(xg0, hg), (xg0 + 40.0, hg)])
        self.h.D([(xd0, hd), (xg0 + 40.0, hd)])
        yol_ciz(yollar[0], xg0 + 40.0, hg, hd, 0)
        return imlec[0]

    # ------------------------------------------------------------ çizim
    def ciz(self, x0, y0):
        cz, P, M, A = self.cz, self.P, self.M, self.A
        katlar = M['katlar']
        merkezi = P['sistem'] == 'merkezi'
        yf_of = {k['kod']: y0 + i * BANT for i, k in enumerate(katlar)}
        # daire genişlikleri: önce kuru çalıştırma yerine sabit geniş aralık
        XK = {'A': x0 + 1200.0, 'B': x0 + 3300.0}
        x_sag = x0 + 5400.0
        # kat bantları
        for i, k in enumerate(katlar):
            yf = yf_of[k['kod']]
            cz.pl([(x0, yf), (x_sag, yf)], 'ROTAS-KAT-BANDI', w=0.0, engel=False)
            kot = f"{k['kot']:+.2f}".replace('+0.00', '±0.00')
            cz.yazi((x0 + 15, yf + 12), f"{k['ad']}  {kot}", 14, 'ROTAS-KAT-BANDI', al='BL')
        ust = yf_of[katlar[-1]['kod']] + BANT
        cz.pl([(x0, ust), (x_sag, ust)], 'ROTAS-KAT-BANDI', engel=False)
        cz.yazi((x0 + 15, ust + 12), 'ÇATI', 14, 'ROTAS-KAT-BANDI', al='BL')
        dkat = [k for k in katlar if k['daireler']]
        # daireler
        for k in dkat:
            yf = yf_of[k['kod']]
            for dad in ('A', 'B'):
                if merkezi:
                    xg, xd = XK[dad], XK[dad] - KOLD
                else:
                    xg, xd = self.kombi(XK[dad] - 60.0, yf, dad, k)
                self.daire(k, dad, xg, xd, yf)
                cz.yazi((XK[dad] + 70.0, yf + 272.0), f"DAİRE {dad} – {k['ad']}", 10, 'ROTAS-YAZI', al='BL')
        if merkezi:
            self.kazan_dairesi(x0, yf_of[katlar[0]['kod']], XK, dkat, yf_of)
        self.hatlari_ciz()
        self.etiketler()
        cz.yazi((x0 + 2700, ust + 150), 'KALORİFER TESİSAT PROJESİ KOLON ŞEMASI', 40, 'ROTAS-BASLIK')
        cz.yazi((x0 + 2700, ust + 95), 'DENEME – Güngören B1 Blok verisi; mahal yerleşimi temsilî, düşey ölçek 1/50 (kat yüksekliği 3,00 m), yataylar ölçeksiz',
                16, 'ROTAS-DENEME')
        notlar = ['NOTLAR:',
                  'Gidiş hattı sürekli (kırmızı), dönüş hattı kesikli (turuncu) çizgi ile gösterilmiştir.',
                  'Hat etiketleri kümülatif ısı yükü ve boru çapıdır (ör. 2070W-DN15); (n) kritik devre parça numarasıdır.',
                  f"Yük esası: {'seçilen radyatör kapasitesi' if P['yuk_esasi'] == 'radyator' else 'mahal ısı kaybı'}; rejim {M['tg']:.0f}/{M['td']:.0f} °C.",
                  'Her radyatör gidişinde termostatik radyatör vanası, dönüşünde ayar (dönüş) rakoru kullanılacaktır.',
                  'Borular siyah çelik (TS EN 10255 orta seri) olarak hesaplanmıştır.']
        for i, s in enumerate(notlar):
            cz.yazi((x0 + 20, y0 - 80 - i * 22), s, 12, 'ROTAS-YAZI', al='BL')
        C_ = cz
        C_.pl([(x0 - 40, y0 - 230), (x_sag + 40, y0 - 230), (x_sag + 40, ust + 220), (x0 - 40, ust + 220)], 'ROTAS-PAFTA', w=2.0,
              kapali=True, engel=False)

    def kombi(self, x, yf, dad, k):
        """kombi (MTY-KOMBİ) bant içinde; gidiş/dönüş çıkışları"""
        cz = self.cz
        cz.blok('MTY-KOMBİ', (x - 48.0, yf + 60.0), 0.0, 1.0, 1.0, 'ROTAS-CIHAZ')
        cz.yazi((x - 24.0, yf + 108.0), f"H. KOMBİ {self.P['kombi']['kapasite_kW']}KW", 9, 'ROTAS-CIHAZ')
        # kombi alt yüzünden çıkış
        xg, xd = x - 10.0, x - 30.0
        self.h.G([(xg, yf + 60.0), (xg, yf + HG0)])
        self.h.D([(xd, yf + 60.0), (xd, yf + HD0)])
        return xg, xd

    def kazan_dairesi(self, x0, yb, XK, dkat, yf_of):
        """bodrum: kazan, emniyet ventili, termometre/manometre, vana, pompa, çek valf, pislik tutucu, genleşme tankı; kolonlar"""
        cz, A = self.cz, self.A
        kz = [p for p in A.parcalar if p['tur'] == 'kazan'][0]
        kx = x0 + 260.0
        cz.blok('MTY-KAZAN VE KOMBİ PLAN KOLON', (kx, yb + 285.0), 0.0, 0.85, 0.85, 'ROTAS-CIHAZ', ic='aKAZAN.')
        cz.yazi((kx, yb + 12.0), f"KAZAN (öneri ≥ {kz['Q'] / 1000 * 1.1:.0f} kW)", 9, 'ROTAS-CIHAZ')
        yg, yd = yb + 230.0, yb + 70.0
        xs = kx + 52.0
        # gidiş: kazandan K kolonlarına
        self.h.G([(xs, yg), (XK['B'], yg), (XK['B'], yg + 0.0)])
        self.h.D([(xs, yd), (XK['B'] - KOLD, yd)])
        # ekipman (gidiş üzerinde)
        cz.blok('MTY-TERMOMETRE', (xs + 40, yg), 0, 1.2, 1.2, 'ROTAS-VANA')
        cz.blok('MTY-MANOMETRE', (xs + 70, yg), 0, 1.2, 1.2, 'ROTAS-VANA')
        cz.blok('MTY-KAZAN VE KOMBİ PLAN KOLON', (xs + 100, yg), 0, 1.0, 1.0, 'ROTAS-VANA', ic='aEMNİYET VENTİLİ')
        vn = [0]

        def vana(ad, p, rot=0.0, s=0.6, ozn=None, on='V'):
            cz.blok(ad, p, rot, s, s, 'ROTAS-VANA', ozn=ozn or {'CAP': ''}, ozn_h={'CAP': 0.1})
            vn[0] += 1
            cz.yazi((p[0], p[1] + (12 if rot == 0 else 0) + 4), f"{on}-{vn[0]:02d}", 6, 'ROTAS-VANA')
        vana('MTY-KURESEL VANA', (xs + 150, yg))
        # dönüş üzerinde: vana – pislik tutucu – pompa – çek valf – vana (kazana doğru)
        vana('MTY-KURESEL VANA', (xs + 300, yd))
        vana('MTY-PISLIK TUTUCU', (xs + 255, yd), on='PT')
        pompa_sembol(cz, (xs + 200, yd), 180.0)
        cz.yazi((xs + 200, yd - 26), 'P-01 SİRKÜLASYON POMPASI', 7, 'ROTAS-CIHAZ')
        vana('MTY-CEKVALF VANA', (xs + 145, yd), rot=180.0, on='ÇV')
        vana('MTY-KURESEL VANA', (xs + 100, yd))
        # genleşme tankı (dönüş, pompa emişi tarafı)
        gx = xs + 340
        self.h.D([(gx, yd), (gx, yd + 40)])
        cz.blok('MTY-KOLLEKTÖR POMPA KOLON', (gx, yd + 45), 0, 0.45, 0.45, 'ROTAS-CIHAZ', ic='MTY-GENLEŞME TANKI KOLON')
        cz.yazi((gx + 60, yd + 90), 'KAPALI GENLEŞME TANKI', 7, 'ROTAS-CIHAZ', al='ML')
        # kolonlar
        for i, dad in enumerate(('A', 'B')):
            xg, xd = XK[dad], XK[dad] - KOLD
            ytop = yf_of[dkat[-1]['kod']] + HG0 + 120.0
            self.h.G([(xg, yg), (xg, ytop)])
            self.h.D([(xd, yd), (xd, ytop - 15.0)])
            self.h.G([(xg, ytop), (xg, ytop)])
            cz.blok('MTY-O.H.A.C', (xg, ytop), 0, 0.6, 0.6, 'ROTAS-VANA')
            cz.blok('MTY-RADYATOR KOLON NO', (xg - 60, ytop + 20), 0, 0.8, 0.8, 'ROTAS-CIHAZ', ozn={'KNO': f'K{i + 1}'},
                    ozn_konum={'KNO': (xg - 60, ytop + 20)}, ozn_h={'KNO': 16.0})
            # dönüş kolonu tepesi: hava purjörü yerine kapalı uç + gidişle aynı hizada
            # kat branşman vanaları
            for k in dkat:
                yf = yf_of[k['kod']]
                for yy, xx in ((yf + HG0, xg + 25.0), (yf + HD0, xg + 25.0)):
                    cz.blok('MTY-KURESEL VANA', (xx, yy), 0, 0.45, 0.45, 'ROTAS-VANA', ozn={'CAP': ''}, ozn_h={'CAP': 0.1})
        self.kolon_parcalar = [p for p in A.parcalar if p['tur'] in ('kolon', 'kolon_dip', 'kazan')]
        for p in self.kolon_parcalar:
            dad = p['daire']
            if p['tur'] == 'kazan':
                self.etiket.append((p, (xs + 160, yg), (XK['A'], yg), False))
            elif p['tur'] == 'kolon_dip':
                self.etiket.append((p, (XK['A'], yg), (XK['B'], yg), False))
            else:
                kk = [k['kod'] for k in self.M['katlar']]
                i_ = kk.index(p['kat'])
                yt = yf_of[p['kat']] + HG0
                yalt = yf_of[kk[i_ - 1]] + HG0 if kk[i_ - 1] in [k['kod'] for k in dkat] else yg
                self.etiket.append((p, (XK[dad], yalt), (XK[dad], yt), True))

    def hatlari_ciz(self):
        cz = self.cz
        once = []
        tum_g = [LineString(p) for p in self.h.g if len(p) > 1 and LineString(p).length > 0]
        for p in self.h.g:
            if len(p) > 1 and LineString(p).length > 0:
                once.append(cz.pl(p, C.GID, w=1.0))
        dl = [p for p in self.h.d if len(p) > 1 and LineString(p).length > 0]
        for p in dl:
            xy = C.kopru_ekle(p, tum_g, r=3.0)
            xy = C.kopru_yon(xy, [LineString(q) for q in dl if q is not p] + tum_g)
            once.append(cz.pl([tuple(q) for q in xy], C.DON, w=1.0, ltscale=12.0))
        cz.once_ciz(once)

    def etiketler(self):
        cz = self.cz
        h = 7.0
        for p, a, b, dikey in self.etiket:
            txt = _yuk_txt(p)
            tw = len(txt) * h * 0.51 + 4
            L = math.dist(a, b)
            kn = p.get('kno')
            if dikey:
                x = a[0] - 6.0
                ym = (a[1] + b[1]) / 2
                cz.yazi((x, ym), txt, h, C.CAPK, al='BC', rot=90.0)
                if kn:
                    cz.yazi((x - 12, ym), f"({kn})", h + 1, 'ROTAS-KRITIK', al='BC', rot=90.0)
            else:
                xm = (a[0] + b[0]) / 2
                y = a[1] + 3.0
                if L < tw + 10:
                    xm = max(a[0], b[0]) - tw / 2 - 8 if L < tw else xm
                cz.yazi((xm, y), txt, h, C.CAPK, al='BC')
                if kn:
                    cz.yazi((xm - tw / 2 - 4, y), f"({kn})", h + 1, 'ROTAS-KRITIK', al='BR')


def M_katlar(M):
    return [k for k in M['katlar']]


def pompa_sembol(cz, p, rot=0.0, R=12.0):
    """03_SEMBOLLER: daire + akış yönünde eşkenar üçgen (MTY kütüphanesinde temiz pompa bloğu yok)"""
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
    T = lambda x, y: (p[0] + x * ca - y * sa, p[1] + x * sa + y * ca)
    cz.maske([(p[0] - R - 1, p[1] - R - 1), (p[0] + R + 1, p[1] - R - 1), (p[0] + R + 1, p[1] + R + 1), (p[0] - R - 1, p[1] + R + 1)])
    cz.msp.add_circle(p, R, dxfattribs={'layer': 'ROTAS-CIHAZ'})
    cz.pl([T(R, 0), T(-R / 2, R * math.sqrt(3) / 2), T(-R / 2, -R * math.sqrt(3) / 2)], 'ROTAS-CIHAZ', kapali=True, engel=False)


def ciz(cz, P, M, A, pf, x0=0.0, y0=-4200.0):
    s = Sema(cz, P, M, A, pf)
    s.ciz(x0, y0)
    return s
