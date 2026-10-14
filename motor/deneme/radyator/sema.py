# -*- coding: utf-8 -*-
"""KALORİFER TESİSAT PROJESİ KOLON ŞEMASI (R2, kolektörlü):
- kat bantları (düşey 1/50), her daire: [kolon T → KALORİMETRE SETİ (1 küresel vana, 2 pislik tutucu, 3 kalorimetre,
  4 balans vanası, 5 küresel vana)] veya [kombi] → KOLEKTÖR DOLABI → her radyatöre ayrı gidiş-dönüş (iç içe, kesişmesiz)
- bodrumda KAZAN DAİRESİ PRENSİP ŞEMASI (motor/deneme/kazan_dairesi modülü import edilir, zon pompası çıkışı kolon
  diplerine bağlanır), kolon diplerinde küresel vana + kosva, kolon başlarında O.H.A.C
- KESİT / GÖRÜNÜŞ detayı: kalorimetre dolabı + kolektör dolabı görünüşü ve A-A kesiti (1/10)."""
import os
import sys
import math
import json
import tempfile
from shapely.geometry import LineString, Polygon, box as sbox
import ciz as C
import semb

BANT = 300.0
SLOT = 185.0
RADY = 125.0
KOLD = 14.0
YC = 135.0                 # kolektör dolabı tabanı (bant tabanından)
SET_X = [40.0, 80.0, 120.0, 160.0, 200.0]
KOL_DX = 240.0             # kolon → kolektör dolabı
SEM, SIN, KOLK = 'ROTAS-ISITMA-SEMBOL', 'ROTAS-ISITMA-SINYAL', 'ROTAS-ISITMA-KOLEKTOR'
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
        self.kesen = []        # boru olmayan ama köprü gerektiren çizgiler (kolektör gövdesi yok – blok içinde)

    # ------------------------------------------------------------ sembol (boru üstünde, maskeli)
    def sembol(self, ad, p, rot=0.0, olcek=0.6, no=None):
        cz = self.cz
        w, hh = 13.0 * olcek / 0.6, 8.0 * olcek / 0.6
        if abs(rot) % 180 == 90:
            w, hh = hh, w
        cz.maske([(p[0] - w / 2, p[1] - hh / 2), (p[0] + w / 2, p[1] - hh / 2), (p[0] + w / 2, p[1] + hh / 2), (p[0] - w / 2, p[1] + hh / 2)])
        semb.ciz(cz.msp, ad, p, rot=rot, olcek=olcek, kat=SEM, no=no)

    # ------------------------------------------------------------ daire
    def daire(self, kat, dad, xg, xd, yf, merkezi):
        cz = self.cz
        pl = self.pf(kat, dad)
        dvs = pl['devreler']
        n = len(dvs)
        prc = {p['devre']: p for p in self.A.parcalar if p['kat'] == kat['kod'] and p['daire'] == dad and p['tur'] == 'devre'}
        gir = [p for p in self.A.parcalar if p['kat'] == kat['kod'] and p['daire'] == dad and p['tur'] == 'giris'][0]
        ad, W, Hd, ygb, ydb = semb.kolektor_sema(cz.doc, n, 14.0)
        xc0 = xg + KOL_DX
        yc = yf + YC
        hg, hd = yc + ygb, yc + ydb
        cz.msp.add_blockref(ad, (xc0, yc), dxfattribs={'layer': KOLK})
        cz.engel.append(sbox(xc0, yc, xc0 + W, yc + Hd + 10).exterior)
        # besleme
        self.h.G([(xg, hg), (xc0, hg)])
        self.h.D([(xd, hd), (xc0, hd)])
        if merkezi:
            for (sg, sd, no), x in zip([('kuresel_vana', 'kuresel_vana', '1'), ('pislik_tutucu', None, '2'),
                                        ('kalorimetre_sensor', 'kalorimetre_km', '3'), (None, 'balans_vanasi', '4'),
                                        ('kuresel_vana', 'kuresel_vana', '5')], SET_X):
                if sg:
                    self.sembol(sg, (xg + x, hg), 0.0, 0.6, no)
                if sd:
                    self.sembol(sd, (xg + x, hd), 0.0, 0.6, None if sg else no)
                if sg == 'kalorimetre_sensor':
                    cz.pl([(xg + x, hg - 2), (xg + x, hd + 6)], SIN, engel=False, ltscale=0.3)
            cz.yazi((xg + 120, hg + 22), 'KS - KALORİMETRE SETİ', 6.5, 'ROTAS-CIHAZ')
        cz.yazi((xc0 + W / 2, yc + Hd + 7), f'KD - KOLEKTÖR DOLABI ({n} AĞIZ)', 6.0, KOLK)
        kn = f"({gir['kno']}) " if gir.get('kno') else ''
        cz.yazi((xg + 120, hd - 13), f"{kn}{gir['Q']:.0f}W-{gir['dn']}", 6.5, C.CAPK)
        # devreler: en yakın radyatör en doğu ağız / en üst seviye
        x_r0 = xc0 + W + 70.0
        for j, dv in enumerate(dvs):
            i = n - 1 - j                                     # ağız sırası (batıdan)
            od = xc0 + 24.0 + i * 14.0
            og = od + 6.0
            Lc = yc - 14.0 - j * 12.0
            xr = x_r0 + j * SLOT
            by = yf + RADY - 15.0
            self.h.G([(og, yc), (og, Lc + 3), (xr, Lc + 3), (xr, by + 57.5)])
            self.h.D([(od, yc), (od, Lc - 3), (xr + 5, Lc - 3), (xr + 5, by + 22.5)])
            self.radyator(dv['rad'], xr, by, dv['no'])
            p = prc.get(dv['no'])
            if p:
                self.etiket.append((p, (xr, max(Lc + 3, yc - 2)), (xr, by + 57.5), True))
        return x_r0 + n * SLOT

    def radyator(self, r, xg, by, no):
        bx = xg + 5.0
        mm = r['m']
        kap = f"{r['ver']:.0f} W"
        if r['tip'] == 'Banyopan':
            self.cz.blok('MTY-RADYATÖR BANYOPAN KOLON', (bx, by), 0, 1.0, 1.0, 'ROTAS-RADYATOR',
                         ozn={'RAD_001': f"HAVLUPAN {r['boy'] * 1000:.0f} / {kap}", 'NO_001': f"{mm['no']}", 'DERECE_001': f"{mm['ti']:.0f}°C",
                              'MAHAL_001': f"{mm['ad']} D{no}"},
                         ozn_h={'RAD_001': 8.0, 'NO_001': 8.0, 'DERECE_001': 8.0, 'MAHAL_001': 8.0},
                         ozn_konum={'RAD_001': (bx + 45, by + 152), 'MAHAL_001': (bx + 25, by + 165), 'NO_001': (bx + 75, by + 165),
                                    'DERECE_001': (bx + 100, by + 165)}, maske=True)
        else:
            self.cz.blok('MTY-RADYATOR KOLON', (bx, by), 0, 1.0, 1.0, 'ROTAS-RADYATOR',
                         ozn={'RAD_001': f"{r['model']}x{r['boy'] * 1000:.0f} / {kap}", 'NO_001': f"{mm['no']}",
                              'DERECE_001': f"{mm['ti']:.0f}°C", 'MAHAL_001': f"{mm['ad']} D{no}"},
                         ozn_h={'RAD_001': 8.0, 'NO_001': 8.0, 'DERECE_001': 8.0, 'MAHAL_001': 8.0},
                         ozn_konum={'RAD_001': (bx + 79, by + 74), 'MAHAL_001': (bx + 55, by + 88), 'NO_001': (bx + 108, by + 88),
                                    'DERECE_001': (bx + 130, by + 88)}, maske=True)

    # ------------------------------------------------------------ çizim
    def ciz(self, x0, y0):
        cz, P, M, A = self.cz, self.P, self.M, self.A
        katlar = M['katlar']
        merkezi = P['sistem'] == 'merkezi'
        yf_of = {k['kod']: y0 + i * BANT for i, k in enumerate(katlar)}
        XK = {'A': x0 + 400.0, 'B': x0 + 2900.0}
        x_sag = x0 + 5400.0
        for k in katlar:
            yf = yf_of[k['kod']]
            xb = x0
            cz.pl([(xb, yf), (x_sag, yf)], 'ROTAS-KAT-BANDI', engel=False)
            kot = f"{k['kot']:+.2f}".replace('+0.00', '±0.00')
            cz.yazi((x0 + 15, yf + 12), f"{k['ad']}  {kot}", 14, 'ROTAS-KAT-BANDI', al='BL')
        ust = yf_of[katlar[-1]['kod']] + BANT
        cz.pl([(x0, ust), (x_sag, ust)], 'ROTAS-KAT-BANDI', engel=False)
        cz.yazi((x0 + 15, ust + 12), 'ÇATI', 14, 'ROTAS-KAT-BANDI', al='BL')
        dkat = [k for k in katlar if k['daireler']]
        for k in dkat:
            yf = yf_of[k['kod']]
            for dad in ('A', 'B'):
                if merkezi:
                    xg, xd = XK[dad], XK[dad] - KOLD
                else:
                    xg, xd = self.kombi(XK[dad], yf, dad, k)
                self.daire(k, dad, xg, xd, yf, merkezi)
                cz.yazi((XK[dad] + 60.0, yf + 272.0), f"DAİRE {dad} – {k['ad']}", 10, 'ROTAS-YAZI', al='BL')
        x_sol = x0
        y_alt = y0 - 260
        if merkezi:
            x_sol = self.kazan_dairesi(x0, yf_of[katlar[0]['kod']], XK, dkat, yf_of)
            y_alt = min(y_alt, self.kd['ymin'] - 60)
        self.hatlari_ciz()
        self.etiketler()
        cz.yazi((x0 + 2700, ust + 150), 'KALORİFER TESİSAT PROJESİ KOLON ŞEMASI', 40, 'ROTAS-BASLIK')
        cz.yazi((x0 + 2700, ust + 95), 'DENEME – Güngören B1 Blok verisi; kolektörlü dağıtım, mahal yerleşimi temsilî; düşey ölçek 1/50 '
                '(kat yüksekliği 3,00 m), yataylar ölçeksiz', 16, 'ROTAS-DENEME')
        notlar = ['NOTLAR:',
                  'Gidiş hattı sürekli (kırmızı), dönüş hattı kesikli (turuncu). Kesişmelerde dönüş hattı köprü ile geçer.',
                  'Daire içi dağıtım KOLEKTÖRLÜDÜR: her radyatör kolektörden ayrı PE-Xc/Al/PE-X gidiş-dönüş hattı ile beslenir (D1…Dn).',
                  'Hat etiketleri kümülatif ısı yükü ve boru çapıdır (ör. 1454W-Ø16x2); (n) kritik devre parça numarasıdır.',
                  f"Yük esası: {'seçilen radyatör kapasitesi' if P['yuk_esasi'] == 'radyator' else 'mahal ısı kaybı'}; rejim {M['tg']:.0f}/{M['td']:.0f} °C.",
                  'Her radyatör gidişinde termostatik radyatör vanası, dönüşünde ayar (dönüş) rakoru; kolektör ağızlarında debimetre ve vana.']
        if merkezi:
            notlar += ['Her daire girişinde KS – KALORİMETRE SETİ (hol sayaç dolabında): 1 küresel vana, 2 pislik tutucu, 3 kalorimetre '
                       '(debi ölçer dönüşte + gidiş/dönüş sıcaklık sensörü, M-Bus), 4 balans vanası, 5 küresel vana.',
                       'Kolonlar ve kazan dairesi siyah çelik (TS EN 10255 orta seri); kazan dairesi prensip şeması bodrum bandının solundadır.']
        for i, s in enumerate(notlar):
            cz.yazi((x0 + 20, y0 - 60 - i * 22), s, 12, 'ROTAS-YAZI', al='BL')
        self.detay(x_sag + 250.0, ust + 50.0)
        xr = x_sag + 250.0 + 2350.0
        cz.pl([(x_sol - 60, y_alt), (xr, y_alt), (xr, ust + 220),
               (x_sol - 60, ust + 220)], 'ROTAS-PAFTA', w=2.0, kapali=True, engel=False)
        return xr

    def kombi(self, xk, yf, dad, k):
        cz = self.cz
        yc = yf + YC
        hg, hd = yc + 40.0, yc + 22.0
        cz.blok('MTY-KOMBİ', (xk + 40.0, hd + 24.0), 180.0, 1.0, 1.0, 'ROTAS-CIHAZ')      # baca sola (dışarı)
        cz.yazi((xk + 16.0, hd - 14.0), f"H. KOMBİ {self.P['kombi']['kapasite_kW']} kW", 7, 'ROTAS-CIHAZ')
        cz.engel.append(sbox(xk - 60, hd - 6, xk + 40, hd + 24).exterior)
        return xk + 40.0, xk + 40.0

    # ------------------------------------------------------------ kazan dairesi (kazan_dairesi modülü)
    def kazan_dairesi(self, x0, yb, XK, dkat, yf_of):
        cz, A, P = self.cz, self.A, self.P
        yg, yd = yb + 230.0, yb + 70.0
        kd = kazan_semasi_ekle(cz, P, self.pomp, x0 - 1500.0, yg - 569.0)
        gx, gy = kd['gidis']
        dx_, dy_ = kd['donus']
        x_top = max(yf_of[k['kod']] for k in dkat) + YC + 40.0 + 45.0
        # zon pompası çıkışı → gidiş dağıtım hattı (bodrum) → kolon dipleri
        self.h.G([(gx, gy), (XK['B'], gy)])
        xv = x0 - 120.0
        self.h.D([(XK['B'] - KOLD, yd), (xv, yd), (xv, dy_), (dx_, dy_)])
        for i, dad in enumerate(('A', 'B')):
            xg, xd = XK[dad], XK[dad] - KOLD
            self.h.G([(xg, gy), (xg, x_top)])
            self.h.D([(xd, yd), (xd, x_top - 18.0)])
            cz.blok('MTY-O.H.A.C', (xg, x_top), 0, 0.6, 0.6, 'ROTAS-VANA')
            cz.blok('MTY-O.H.A.C', (xd, x_top - 18.0), 0, 0.6, 0.6, 'ROTAS-VANA')
            cz.blok('MTY-RADYATOR KOLON NO', (xg - 55, x_top + 30), 0, 0.8, 0.8, 'ROTAS-CIHAZ', ozn={'KNO': f'K{i + 1}'},
                    ozn_konum={'KNO': (xg - 55, x_top + 30)}, ozn_h={'KNO': 16.0})
            # kolon dibi: küresel vana + kosva (boşaltma)
            self.sembol('kuresel_vana', (xg, gy + 30.0), 90.0, 0.6)
            self.sembol('kuresel_vana', (xd, yd + 30.0), 90.0, 0.6)
            for xx, yy in ((xg, gy + 12.0), (xd, yd + 12.0)):
                cz.pl([(xx, yy), (xx + 22.0, yy)], C.DON if xx == xd else C.GID, w=1.0, engel=True)
                self.sembol('bosaltma_vanasi', (xx + 18.0, yy), 0.0, 0.6)
        cz.yazi((x0 - 1400.0, yg - 569.0 + 1010.0), 'BODRUM KAT – KAZAN DAİRESİ (PRENSİP ŞEMASI, kazan_dairesi modülü)', 22, 'ROTAS-KAT-BANDI', al='BL')
        self.kd = kd
        self.kolon_parcalar = [p for p in A.parcalar if p['tur'] in ('kolon', 'kolon_dip', 'kazan')]
        kk = [k['kod'] for k in self.M['katlar']]
        for p in self.kolon_parcalar:
            dad = p['daire']
            if p['tur'] == 'kazan':
                self.etiket.append((p, (gx + 40, gy), (XK['A'] - 20, gy), False))
            elif p['tur'] == 'kolon_dip':
                self.etiket.append((p, (XK['A'] + 20, gy), (XK['B'] - 20, gy), False))
            else:
                i_ = kk.index(p['kat'])
                yt = yf_of[p['kat']] + YC + 40.0
                yalt = yf_of[kk[i_ - 1]] + YC + 40.0 if kk[i_ - 1] in [k['kod'] for k in dkat] else gy + 40
                self.etiket.append((p, (XK[dad], yalt), (XK[dad], yt), True))
        return kd['xmin']

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
        h = 6.5
        for p, a, b, dikey in self.etiket:
            txt = f"{p['Q']:.0f}W-{p['dn']}"
            tw = len(txt) * h * 0.51 + 4
            kn = p.get('kno')
            if dikey:
                x = a[0] - 6.0
                ym = (a[1] + b[1]) / 2
                cz.yazi((x, ym), txt, h, C.CAPK, al='BC', rot=90.0)
                if kn:
                    cz.yazi((x - 11, ym), f"({kn})", h + 1, 'ROTAS-KRITIK', al='BC', rot=90.0)
            else:
                xm = (a[0] + b[0]) / 2
                y = a[1] + 6.0
                cz.yazi((xm, y), txt, h, C.CAPK, al='BC')
                if kn:
                    cz.yazi((xm - tw / 2 - 4, y), f"({kn})", h + 1, 'ROTAS-KRITIK', al='BR')

    # ------------------------------------------------------------ kesit / görünüş detayı (1/10)
    def detay(self, x, y):
        detay_ciz(self.cz, self.P, self.A, x, y)


# ====================================================================== kazan dairesi modülü bağlantısı
def kazan_semasi_ekle(cz, P, pomp, ox, oy):
    """motor/deneme/kazan_dairesi/kazan_dairesi.py ile şemayı üretir, model uzayına (ox, oy) ötelemesiyle aktarır.
    Dönüş: zon gidiş çıkışı / dönüş girişi noktaları ve sol sınır."""
    sys.path.insert(0, os.path.join(_KOK, '..', 'kazan_dairesi'))
    import kazan_dairesi as KD
    from ezdxf.addons import Importer
    import ezdxf
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
    tmp = tempfile.mkdtemp(prefix='rad_kd_')
    yol = os.path.join(tmp, 'kd.dxf')
    S = KD.ciz(J, yol)
    gid = [b for b in S.borular if b['ok'] == 'son' and b['lay'] == KD.GID][0]['pts'][-1]
    don = [b for b in S.borular if b['ok'] == 'bas' and b['lay'] == KD.DON][0]['pts'][-1]
    src = ezdxf.readfile(yol)
    im = Importer(src, cz.doc)
    for e in src.modelspace():
        if e.dxftype() == 'INSERT':
            im.import_block(e.dxf.name, rename=False)
    for lay in src.layers:
        if lay.dxf.name not in cz.doc.layers:
            im.import_table('layers', [lay.dxf.name])
    ents = list(src.modelspace())
    once = {e.dxf.handle for e in cz.msp}
    im.import_entities(ents, cz.msp)
    im.finalize()
    from ezdxf.math import Matrix44
    m = Matrix44.translate(ox, oy, 0)
    yeni = [e for e in cz.msp if e.dxf.handle not in once]
    sil = []
    for e in yeni:
        try:
            e.transform(m)
        except Exception:
            pass
        if e.dxf.layer == 'ROTAS-PAFTA':
            cz.msp.delete_entity(e)
            continue
        if e.dxf.layer == '0':
            e.dxf.layer = 'ROTAS-ISITMA-YAZI'
        if e.dxftype() in ('LWPOLYLINE', 'LINE') and e.dxf.layer in (C.DON, 'ROTAS-ISITMA-YOGUSMA', 'ROTAS-DOGALGAZ-SINYAL'):
            e.dxf.ltscale = 8.0 * e.dxf.get('ltscale', 1.0)
    from ezdxf import bbox
    yeni = [e for e in yeni if e.is_alive]
    bb = bbox.extents(yeni, fast=True)
    return dict(gidis=(gid[0] + ox, gid[1] + oy), donus=(don[0] + ox, don[1] + oy), xmin=bb.extmin.x, ymin=bb.extmin.y,
                kw=kw, adet=adet, uyari=S.uyarilar)


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
        gx, dx_ = 17.0, 33.0
        g = [f(gx, 40), f(gx, by1 + 30), f(70, by1 + 30)]
        d = [f(dx_, 40), f(dx_, by1 + 22), f(70, by1 + 22)]
        czp.pl(g, C.GID, w=2.0, engel=False); czp.pl(d, C.DON, w=2.0, ltscale=3.0, engel=False)
        cz.yazi(f(gx - 3, 46), 'KOLONDAN (GİDİŞ)', 7, C.GID, al='BL', rot=90, maske=False)
        cz.yazi(f(dx_ + 3, 46), 'KOLONA (DÖNÜŞ)', 7, C.DON, al='BR', rot=90, maske=False)
        el = [('kuresel_vana', 'kuresel_vana', 135.0, '1'), ('pislik_tutucu', None, 155.0, '2'),
              ('kalorimetre_sensor', 'kalorimetre_km', 175.0, '3'), (None, 'balans_vanasi', 195.0, '4'),
              ('kuresel_vana', 'kuresel_vana', 212.0, '5')]
        for sg, sd, yy, no in el:
            for sm, xx in ((sg, gx), (sd, dx_)):
                if sm:
                    p = f(xx, yy)
                    cz.maske([(p[0] - 30, p[1] - 22), (p[0] + 30, p[1] - 22), (p[0] + 30, p[1] + 22), (p[0] - 30, p[1] + 22)])
                    semb.ciz(cz.msp, sm, p, rot=-90.0, olcek=2.2, kat=SEM)
            if sg == 'kalorimetre_sensor':
                czp.pl([f(gx + 2, yy), f(dx_ - 3, yy)], SIN, engel=False, ltscale=1.0)
            cz.yazi(f(bx0 - 6, yy), no, 10, DT, al='MR', maske=False)
        cz.yazi(f(25, by0 - 6), 'HOL – KALORİMETRE (SAYAÇ) DOLABI 50×100×15', 8, DT, maske=False)
        cz.yazi(f(25, by0 - 13), 'okuma kapağı ortak alana açılır', 7, DT, maske=False)
        lst += ['1  Küresel vana (tam geçişli, PN16) – daire girişi', '2  Pislik tutucu (Y tipi, paslanmaz elek)',
                '3  Kalorimetre (ısı pay ölçer): ultrasonik debi ölçer DÖNÜŞTE + gidiş/dönüş Pt1000 sıcaklık sensörü, M-Bus',
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
        czp.pl([f(70, by1 + 30), f(70, taban + 4), f(kx0 - 6, taban + 4), f(kx0 - 6, yg_), f(kx0 + 6, yg_)], C.GID, w=2.0, engel=False)
        czp.pl([f(76, by1 + 22), f(76, taban + 6), f(kx0 - 2, taban + 6), f(kx0 - 2, yd_), f(kx0 + 6, yd_)], C.DON, w=2.0, ltscale=3.0, engel=False)
    else:
        czp.pl([f(kx0 - 6, 60), f(kx0 - 6, yg_), f(kx0 + 6, yg_)], C.GID, w=2.0, engel=False)
        czp.pl([f(kx0 - 2, 60), f(kx0 - 2, yd_), f(kx0 + 6, yd_)], C.DON, w=2.0, ltscale=3.0, engel=False)
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
    gls = [LineString(p) for p, _ in GL]
    for p, w in GL:
        cz.pl(p, C.GID, w=w, engel=False)
    for p, w in DL:
        xy = C.kopru_ekle(p, gls, r=6.0)
        xy = C.kopru_yon(xy, gls)
        cz.pl([tuple(q) for q in xy], C.DON, w=w, ltscale=3.0, engel=False)
    for i, s in enumerate(lst):
        cz.yazi((x, y - (taban + 30) * K - i * 20), s, 10, 'ROTAS-YAZI', al='BL', maske=False)


def ciz(cz, P, M, A, pf, pomp, x0=0.0, y0=-4200.0):
    s = Sema(cz, P, M, A, pf, pomp)
    xr = s.ciz(x0, y0)
    return s
