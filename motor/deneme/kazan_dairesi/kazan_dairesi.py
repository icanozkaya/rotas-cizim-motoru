# -*- coding: utf-8 -*-
"""Parametrik KAZAN DAİRESİ PRENSİP ŞEMASI — R2 (deneme modülü: kazan_dairesi, 14.10.2026 (B) talimatı).

Kullanım:  python3 kazan_dairesi.py girdi.json cikti.dxf [onizleme.png]

R2 kuralları:
- MTY bloğu YOK: tüm semboller saf geometri ROTAS- blokları (bloklar_r2.py).
- Boru atlatma / köprü YOK: hat sırası kesişme olmayacak şekilde kurulur. Kaskadda kaçınılmaz görünen kesişmeler
  (baca, doğalgaz, yoğuşma) ana hidrolik şemadan AYRI BÖLGEDE çizilir: kazan altında/üstünde yalnız bağlantı ucu
  (GAZ / YOĞUŞMA / BACA) bulunur, hatların kendisi "DOĞALGAZ BAĞLANTI ŞEMASI", "YOĞUŞMA DRENAJ ŞEMASI" ve
  "BACA BAĞLANTI ŞEMASI" bölgelerindedir. Çizim sonunda kesişme denetimi yapılır (0 olmalı).
- Her numara kendi sembolünün hemen yanında ve tektir: etiketin en yakın sembolü kendi sembolü olmalı (yerleşimde
  zorunlu koşul; DXF'te sembol INSERT'ine XDATA 'ROTAS' NO=... yazılır, kontrol.py bağımsız doğrular).
- Elektrik kalemi yok: gaz alarmı ↔ selenoid sinyal hattı vb. çizilmez.
Akış: kaskad kazanlar -> kazan gidiş kollektörü -> hava ayırıcı -> denge kabı -> gidiş kollektörü -> zon pompaları
(asıl + yedek) -> zonlar; dönüşler kesikli. Cihaz listesi (NO | CİHAZ | TEKNİK ÖZELLİKLERİ) + notlar.
"""
import json
import math
import os
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import LineString, box as sbox
from shapely.ops import unary_union
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bloklar_r2 as BL       # noqa: E402
import geometri as GM         # noqa: E402

# ----------------------------------------------------------------------------- katmanlar (ROTAS- önekli)
GID, DON = 'ROTAS-ISITMA-GIDIS', 'ROTAS-ISITMA-DONUS'
GAZ, BACA, YOG = 'ROTAS-DOGALGAZ-BORU', 'ROTAS-ISITMA-BACA', 'ROTAS-ISITMA-YOGUSMA'
SOG, SIC, SIR = 'ROTAS-SIHHI-SOGUK-SU', 'ROTAS-SIHHI-SICAK-SU', 'ROTAS-SIHHI-SIRKULASYON'
VANA, CIHAZ, POMPA, GAZS = 'ROTAS-ISITMA-VANA', 'ROTAS-ISITMA-CIHAZ', 'ROTAS-ISITMA-POMPA', 'ROTAS-DOGALGAZ-SEMBOL'
KOL = 'ROTAS-ISITMA-KOLLEKTOR'
ETK, CAP, YAZ, BAS, MASKE, PAFTA = ('ROTAS-ISITMA-ETIKET', 'ROTAS-ISITMA-CAP', 'ROTAS-ISITMA-YAZI', 'ROTAS-ISITMA-BASLIK',
                                     'ROTAS-MASKE', 'ROTAS-PAFTA')
BOL = 'ROTAS-ISITMA-BOLGE'
T_CER, T_CIZ, T_YAZ, T_BAS = 'ROTAS-HESAP-CERCEVE', 'ROTAS-HESAP-CIZGI', 'ROTAS-HESAP-YAZI', 'ROTAS-HESAP-BASLIK'
KATMAN = {GID: (10, 'Continuous'), DON: (30, 'DASHED'), GAZ: (2, 'Continuous'), BACA: (8, 'Continuous'),
          YOG: (6, 'DASHED'), SOG: (5, 'Continuous'), SIC: (1, 'Continuous'), SIR: (31, 'DASHDOT'),
          VANA: (1, 'Continuous'), CIHAZ: (135, 'Continuous'), POMPA: (30, 'Continuous'), GAZS: (2, 'Continuous'),
          KOL: (7, 'Continuous'), ETK: (3, 'Continuous'), CAP: (41, 'Continuous'), BOL: (8, 'DASHED'),
          YAZ: (7, 'Continuous'), BAS: (5, 'Continuous'), MASKE: (7, 'Continuous'), PAFTA: (7, 'Continuous'),
          T_CER: (4, 'Continuous'), T_CIZ: (1, 'Continuous'), T_YAZ: (7, 'Continuous'), T_BAS: (2, 'Continuous')}
BORU_KATMAN = {GID, DON, GAZ, BACA, YOG, SOG, SIC, SIR}

HT, HD, HY = 8.0, 7.0, 9.0      # etiket (V-01), çap (DN), açıklama yazı yükseklikleri
WF = 0.85                      # yazı genişlik faktörü
SIRA = ['K', 'P', 'DK', 'HA', 'TA', 'GT', 'KL', 'BY', 'NU', 'B', 'EV', 'HP', 'M', 'TM', 'V', 'GF', 'GR', 'SV', 'GA']
ONAYLI_V_SONRA = ('DOĞALGAZ KÜRESEL VANASI (CİHAZ)', 'ESNEK BAĞLANTI (GAZ)')   # onaylı V- sırası (numarala)
ETIKET_MAKS = 18.0            # etiket kutusu – kendi sembolü azami uzaklığı ("hemen yanında")
ETIKET_PAY = 4.0               # başka sembol, kendi sembolünden en az bu kadar daha uzak olmalı

# çelik boru (EN 10255 orta seri) iç çapları, mm
IC = [('DN15', 16.1), ('DN20', 21.6), ('DN25', 27.3), ('DN32', 36.0), ('DN40', 41.9), ('DN50', 53.1), ('DN65', 68.9),
      ('DN80', 80.9), ('DN100', 105.3), ('DN125', 129.7), ('DN150', 155.4), ('DN200', 206.5), ('DN250', 260.4)]


def dn_su(q):
    """su: DN50'ye kadar v ≤ 1,0 m/s, üstünde v ≤ 1,5 m/s (07 §0)"""
    for dn, d in IC:
        v = q / 3600 / (math.pi * (d / 1000) ** 2 / 4)
        if v <= (1.0 if d <= 53.1 else 1.5):
            return dn
    return IC[-1][0]


def dn_gaz(q, vmax):
    for dn, d in IC[2:]:
        if q / 3600 / (math.pi * (d / 1000) ** 2 / 4) <= vmax:
            return dn
    return IC[-1][0]


def dn_no(dn):
    return int(dn[2:])


def tr(v, n=1):
    s = f'{v:,.{n}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s[:-2] if n and s.endswith(',0') else s


def motor_kw(q, h):
    n = q * h * 10 / 3600 / 0.5
    for s in (0.04, 0.06, 0.09, 0.12, 0.18, 0.25, 0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3.0, 4.0, 5.5, 7.5, 11, 15):
        if s >= n:
            return s
    return 18.5


# ============================================================================ şema
class Sema:
    def __init__(self, P):
        self.P = P
        self.doc = ezdxf.new('R2018', setup=True)
        self.doc.header['$INSUNITS'] = 5
        self.doc.header['$LTSCALE'] = 8.0
        self.doc.set_wipeout_variables(frame=0)
        for ad, (renk, lt) in KATMAN.items():
            self.doc.layers.add(ad, color=renk, linetype=lt)
        BL.hazirla(self.doc)
        self.msp = self.doc.modelspace()
        self.borular = []        # boru kayıtları
        self.cihazlar = []       # numaralanacak cihaz örnekleri
        self.serbest = []        # sabit konumlu yazılar (çakışma denetimine girer)
        self.uyarilar = []
        self.kesisim = []        # boru-boru iç kesişmeleri (R2: boş olmalı)

    # ------------------------------------------------------------------ boru
    def hat(self, lay, pts, dn=None, w=0.0, etiket=None, ok=None):
        p = dict(lay=lay, pts=[(float(x), float(y)) for x, y in pts], dn=dn, w=w, kes=[], ok=ok,
                 etiket=etiket if etiket is not None else dn)
        self.borular.append(p)
        return p

    def ekle(self, p, at, blok, kod=None, ad=None, oz=(), rot=None, olcek=1.0, katman=VANA, tercih=None):
        """boru üstü (hat içi) sembol: boru ±yarım boy kesilir"""
        s, aci = GM.konum(p['pts'], at)
        r = aci if rot is None else rot
        y = BL.YARIM.get(blok, 10.5) * olcek
        p['kes'].append((s - y, s + y))
        return self.blok(blok, at, r, olcek, kod, ad, oz, katman, tercih, aci)

    def brans(self, at, blok, yon, kod=None, ad=None, oz=(), olcek=1.0, katman=VANA, tercih=None):
        """boru yanına dik çıkan cihaz (manometre, termometre, emniyet ventili, purjör): yon = cihazın baktığı açı"""
        return self.blok(blok, at, yon - 90.0, olcek, kod, ad, oz, katman, tercih, None, yon)

    def blok(self, blok, at, rot, olcek, kod, ad, oz, katman, tercih=None, boru_aci=None, yon=None, sabit=None):
        e = self.msp.add_blockref(blok, at, dxfattribs={'layer': katman, 'rotation': rot % 360,
                                                         'xscale': olcek, 'yscale': olcek})
        c = dict(kod=kod, ad=ad, oz=tuple(oz), at=at, ent=e, tercih=tercih, boru_aci=boru_aci, yon=yon, sabit=sabit)
        if kod:
            self.cihazlar.append(c)
        return c

    # ------------------------------------------------------------------ yazı
    def yazi(self, p, s, h=HY, lay=YAZ, al=TA.MIDDLE_CENTER, rot=0.0, maske=True, ic=False):
        self.serbest.append((p, s, h, lay, al, rot, maske, ic))

    def _yaz(self, p, s, h, lay, al=TA.MIDDLE_CENTER, rot=0.0, maske=True):
        if maske:
            pl = GM.yazi_kutusu(p, s, h, al, rot, WF, pay=1.0)
            self.msp.add_wipeout(list(pl.exterior.coords)[:-1], dxfattribs={'layer': MASKE})
        t = self.msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': WF})
        t.set_placement(p, align=al)
        return t

    # ------------------------------------------------------------------ çizim
    def kesisim_denetle(self):
        """R2: köprü yok. Boru-boru iç kesişmesi (uç/T bağlantısı dışında) olmamalı; olursa uyarı + kayıt."""
        for i, a in enumerate(self.borular):
            for b in self.borular[i + 1:]:
                for (_, pa, qa) in GM.segmentler(a['pts']):
                    for (_, pb, qb) in GM.segmentler(b['pts']):
                        x = GM.dik_kesisim(pa, qa, pb, qb, 0.5)
                        if x is not None:
                            self.kesisim.append((a['lay'], b['lay'], x))
                            self.uyarilar.append(f'BORU KESİŞMESİ: {a["lay"]} × {b["lay"]} @ {x}')

    def boru_ciz(self):
        for p in self.borular:
            L = GM.uzunluk(p['pts'])
            if p['ok']:
                q, aci = GM.nokta(p['pts'], L)
                if p['ok'] == 'son':
                    self.msp.add_blockref('ROTAS-OK', q, dxfattribs={'layer': p['lay'], 'rotation': aci})
                    p['kes'].append((L - 14, L + 1))
                elif p['ok'] == 'bas':
                    t, _ = GM.nokta(p['pts'], L - 14)
                    self.msp.add_blockref('ROTAS-OK', t, dxfattribs={'layer': p['lay'], 'rotation': aci + 180})
                    p['kes'].append((L - 14, L + 1))
                elif p['ok'] == 'orta':              # gömülü kullanım: ok hattın ortasında, hat devam eder
                    q, aci = GM.nokta(p['pts'], L / 2)
                    self.msp.add_blockref('ROTAS-OK', q, dxfattribs={'layer': p['lay'], 'rotation': aci})
            for parca in GM.parcala(p['pts'], p['kes'], [], 5.0):
                e = self.msp.add_lwpolyline(parca, format='xyb', dxfattribs={'layer': p['lay']})
                if p['w']:
                    e.dxf.const_width = p['w']

    # ------------------------------------------------------------------ etiket yerleşimi
    def sembol_geometrileri(self):
        """her INSERT için birleşik geometri (etiket–sembol eşleşmesi)"""
        out = []
        for e in self.msp.query('INSERT'):
            kay = []
            GM._ent_geo(e, kay, 0, 'sembol')
            g = unary_union([k[2] for k in kay]) if kay else None
            if g is not None and not g.is_empty:
                out.append((e, g))
        return out

    def etiketle(self):
        geo = GM.model_geometri(self.msp)
        agac = STRtree(geo)
        yerlesen = []
        sem = self.sembol_geometrileri()
        sem_g = [g for _, g in sem]
        sem_tree = STRtree(sem_g)
        sem_idx = {id(e): i for i, (e, _) in enumerate(sem)}

        def bos(pl):
            g = pl.buffer(1.2)
            if any(g.intersects(geo[i]) for i in agac.query(g)):
                return False
            return not any(g.intersects(y) for y in yerlesen)

        def sahip_uygun(pl, k, dmaks, pay):
            d0 = pl.distance(sem_g[k])
            if d0 > dmaks:
                return False
            for j in sem_tree.query(pl.buffer(d0 + pay)):
                if j != k and pl.distance(sem_g[j]) < d0 + pay:
                    return False
            return True

        # sabit yazılar önce (konumları verilidir)
        for (p, s, h, lay, al, rot, maske, ic) in self.serbest:
            pl = GM.yazi_kutusu(p, s, h, al, rot, WF)
            if not ic and not bos(pl):
                self.uyarilar.append(f'sabit yazı çakışıyor: {s}')
            yerlesen.append(pl)
            self._yaz(p, s, h, lay, al, rot, maske)
        # cihaz numaraları: kendi sembolünün hemen yanında, en yakın sembol kendi sembolü
        for c in self.cihazlar:
            s = c['etiket']
            k = sem_idx[id(c['ent'])]
            if c.get('sabit'):
                q = c['sabit']
                yerlesen.append(GM.yazi_kutusu(q, s, HT + 2, TA.MIDDLE_CENTER, 0, WF))
                self._yaz(q, s, HT + 2, ETK, TA.MIDDLE_CENTER, 0, False)
                continue
            x0, y0, x1, y1 = sem_g[k].bounds
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            w = len(s) * HT * 0.66 * WF
            yonler = GM.aday_yonler(c['boru_aci'], c['yon'], c['tercih'])
            ok = False
            for dmaks, pay in ((ETIKET_MAKS, ETIKET_PAY), (ETIKET_MAKS + 10, 2.5)):
                for g in (3.0, 5.0, 8.0, 12.0, 16.0, 22.0):
                    for ux, uy in yonler:
                        qx = x1 + g + w / 2 if ux > 0 else (x0 - g - w / 2 if ux < 0 else cx)
                        qy = y1 + g + HT / 2 if uy > 0 else (y0 - g - HT / 2 if uy < 0 else cy)
                        kayma = (0.0,) if (ux and uy) else ((0.0, 5.0, -5.0, 10.0, -10.0) if ux else (0.0, w / 3, -w / 3))
                        for dd in kayma:
                            q = (qx, qy + dd) if ux and not uy else (qx + dd, qy)
                            pl = GM.yazi_kutusu(q, s, HT, TA.MIDDLE_CENTER, 0, WF)
                            if bos(pl) and sahip_uygun(pl, k, dmaks, pay):
                                yerlesen.append(pl)
                                self._yaz(q, s, HT, ETK, TA.MIDDLE_CENTER, 0, True)
                                ok = True
                                break
                        if ok:
                            break
                    if ok:
                        break
                if ok:
                    break
            if not ok:
                self.uyarilar.append(f'etiket yeri bulunamadı: {s}')
        # boru çap etiketleri (en uzun düz parçaların boş yerine, boruya paralel)
        for p in self.borular:
            s = p['etiket']
            if not s:
                continue
            segs = sorted(GM.segmentler(p['pts']), key=lambda t: -math.dist(t[1], t[2]))
            ok = False
            for (_, a, b) in segs[:3]:
                Ls = math.dist(a, b)
                w = len(s) * HD * 0.66 * WF
                if Ls < w + 10:
                    continue
                dusey = abs(a[0] - b[0]) < 1e-6
                rot = 90.0 if dusey else 0.0
                for f in (0.5, 0.35, 0.65, 0.2, 0.8, 0.1, 0.9, 0.27, 0.73, 0.43, 0.57):
                    m = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
                    for side in (1, -1):
                        q = (m[0] - side * (HD / 2 + 3), m[1]) if dusey else (m[0], m[1] + side * (HD / 2 + 3))
                        pl = GM.yazi_kutusu(q, s, HD, TA.MIDDLE_CENTER, rot, WF)
                        if bos(pl):
                            yerlesen.append(pl)
                            self._yaz(q, s, HD, CAP, TA.MIDDLE_CENTER, rot, True)
                            ok = True
                            break
                    if ok:
                        break
                if ok:
                    break
            if not ok:
                self.uyarilar.append(f'çap etiketi yeri yok: {s} ({p["lay"]})')

    # ------------------------------------------------------------------ numaralandırma + liste
    def numarala(self):
        gruplar = {}
        for c in self.cihazlar:
            gruplar.setdefault((c['kod'], c['ad'], c['oz']), []).append(c)
        ilk_ad = {}
        for i, c in enumerate(self.cihazlar):
            ilk_ad.setdefault((c['kod'], c['ad']), i)
        # R3 (14.10.2026): ONAYLI plan / kesit / kısmi görünüş numaralandırması ESAS. Onaylı çizimde kazanın gaz cihaz
        # vanası ve esnek bağlantısı V- sırasında kazan vanalarından hemen sonra gelir (R1 sırası); gaz hatları bu
        # şemada ayrı bölgede (sonda) çizilse de numaralar onaylıyla aynı kalsın diye sıraları kazan vanasının ardına alınır.
        kv = [c['ad'] for c in self.cihazlar if c['kod'] == 'V' and c['ad'] in ('KÜRESEL VANA', 'KELEBEK VANA')]
        if kv:
            a0 = ilk_ad[('V', kv[0])]
            for j, ad in enumerate(ONAYLI_V_SONRA, 1):
                if ('V', ad) in ilk_ad:
                    ilk_ad[('V', ad)] = a0 + 0.1 * j

        def dn(k):
            for o in k[2]:
                if o.startswith('DN'):
                    return -int(o[2:].split()[0])
            return 0
        anahtar = sorted(gruplar, key=lambda k: (SIRA.index(k[0]) if k[0] in SIRA else 99, ilk_ad[(k[0], k[1])], dn(k),
                                                 self.cihazlar.index(gruplar[k][0])))
        sayac, satir = {}, []
        for k in anahtar:
            etk = []
            for c in gruplar[k]:
                sayac[k[0]] = sayac.get(k[0], 0) + 1
                c['etiket'] = f'{k[0]}-{sayac[k[0]]:02d}'
                c['ent'].set_xdata('ROTAS', [(1000, 'NO=' + c['etiket'])])
                etk.append(c['etiket'])
            no = etk[0] if len(etk) == 1 else f'{etk[0]} ... {etk[-1]}'
            satir.append((no, k[1], list(k[2]) + [f'Adet: {len(etk)}']))
        return satir


def tablo_ciz(m, satir, x0, y0, baslik='KAZAN DAİRESİ CİHAZ LİSTESİ'):
    """cihaz listesi (kullanıcının YANGIN POMPA GRUBU CİHAZ LİSTESİ tarzı): NO | CİHAZ | TEKNİK ÖZELLİKLERİ"""
    H, HB, HTB = 12.5, 15.0, 22.0
    W = [190, 560, 1040]
    X = [x0]
    for w in W:
        X.append(X[-1] + w)
    RH, TH = 34, 50

    def sar(parca, gen):
        sat, cur = [], ''
        for p in parca:
            s = (cur + '  •  ' + p) if cur else p
            if len(s) * H * 0.6 > gen - 30 and cur:
                sat.append(cur); cur = p
            else:
                cur = s
        sat.append(cur)
        return sat

    rows = [(no, ad, sar(oz, W[2])) for no, ad, oz in satir]
    hts = [max(RH, 22 + len(t) * H * 1.7) for _, _, t in rows]

    def ln(a, b, lay=T_CIZ):
        m.add_line(a, b, dxfattribs={'layer': lay})

    def tx(s, x, y, h, al=TA.MIDDLE_CENTER, lay=T_YAZ):
        t = m.add_text(s, height=h, dxfattribs={'layer': lay, 'style': 'ROTAS'})
        t.set_placement((x, y), align=al)

    ys = [y0, y0 - TH, y0 - TH - RH]
    for h in hts:
        ys.append(ys[-1] - h)
    for y in ys:
        ln((X[0], y), (X[-1], y))
    ln((X[0], ys[0]), (X[0], ys[-1])); ln((X[-1], ys[0]), (X[-1], ys[-1]))
    for x in X[1:-1]:
        ln((x, ys[1]), (x, ys[-1]))
    tx(baslik, (X[0] + X[-1]) / 2, y0 - TH / 2, HTB, lay=T_BAS)
    for i, b in enumerate(['NO', 'CİHAZ', 'TEKNİK ÖZELLİKLERİ']):
        tx(b, (X[i] + X[i + 1]) / 2, ys[1] - RH / 2, HB, lay=T_BAS)
    for k, ((no, ad, t), h) in enumerate(zip(rows, hts)):
        yt = ys[2 + k]
        tx(no, (X[0] + X[1]) / 2, yt - h / 2, H)
        tx(ad, X[1] + 15, yt - h / 2, H, TA.MIDDLE_LEFT)
        n, sp = len(t), H * 1.7
        for j, s in enumerate(t):
            tx(s, X[2] + 15, yt - h / 2 + (n - 1) * sp / 2 - j * sp, H, TA.MIDDLE_LEFT)
    m.add_lwpolyline([(X[0] - 15, ys[-1] - 15), (X[-1] + 15, ys[-1] - 15), (X[-1] + 15, y0 + 15),
                      (X[0] - 15, y0 + 15)], close=True, dxfattribs={'layer': T_CER, 'const_width': 2})
    return X[-1], ys[-1]


def notlar_ciz(m, notlar, x, y):
    m.add_text('NOTLAR', height=18, dxfattribs={'layer': BAS, 'style': 'ROTAS'}).set_placement((x, y), align=TA.BOTTOM_LEFT)
    for i, s in enumerate(notlar):
        m.add_text(f'{i + 1}. {s}', height=11, dxfattribs={'layer': YAZ, 'style': 'ROTAS', 'width': WF}).set_placement(
            (x, y - 30 - i * 22), align=TA.BOTTOM_LEFT)
    return y - 30 - len(notlar) * 22


# ============================================================================ şema kurgusu
def ciz(P, cikti, gomulu=False):
    """gomulu=True: radyatör kolon şemasına aktarım için — başlık, cihaz listesi, notlar ve çerçeve çizilmez;
    zon gidişi şema üst sınırına, zon dönüşü alt sınırına uzatılır (S.baglanti = {'gidis': (x,y), 'donus': (x,y)})."""
    S = Sema(P)
    rej = P.get('rejim', {'gidis': 90, 'donus': 70})
    tg, td = rej['gidis'], rej['donus']
    dT = tg - td
    K = P['kazan']
    n, qk = int(K['adet']), float(K['kapasite_kw'])
    QT = n * qk
    q_k = qk / (1.163 * dT)
    q_p = QT / (1.163 * dT)
    dn_k, dn_p = dn_su(q_k), dn_su(q_p)
    zonlar = P.get('zonlar', [])
    boy = P.get('boyler')
    q_s = sum(z['debi'] * z.get('adet', 1) for z in zonlar) + (boy['sarj_pompa']['debi'] if boy else 0)
    dn_s = dn_su(q_s)
    em = P.get('emniyet', {})
    ev_bar, ev_dn = em.get('ventil_bar', 3.0), em.get('ventil_cap', 'DN25')
    gz = P.get('dogalgaz', {})
    Hu, eta = 9.59, 0.97
    qg_k = qk / (Hu * eta)
    qg = QT / (Hu * eta)
    dng_k = gz.get('kazan_cap') or dn_gaz(qg_k, 5.0)
    dng = gz.get('kollektor_cap') or dn_gaz(qg, 6.0)
    dng_g = gz.get('giris_cap') or dn_gaz(qg, 15.0 if gz.get('regulator') else 6.0)

    def vana(dn):          # Aselsan pratiği: DN65 ve üzeri kelebek vana
        return ('ROTAS-KELEBEK-VANA', 'KELEBEK VANA', [f'{dn} PN16', 'Redüktörlü / kollu, EPDM conta']) \
            if dn_no(dn) >= 65 else ('ROTAS-KURESEL-VANA', 'KÜRESEL VANA', [f'{dn} PN16', 'Tam geçişli, pirinç / çelik gövde'])

    def V(p, at, dn, rot=None, tercih=None):
        b, ad, oz = vana(dn)
        return S.ekle(p, at, b, 'V', ad, oz, rot=rot, tercih=tercih)

    def CV(p, at, dn, rot=None):
        return S.ekle(p, at, 'ROTAS-CEKVALF', 'V', 'ÇEK VALF', [f'{dn} PN16', 'Yaylı / klapeli, ısıtma suyuna uygun'], rot=rot)

    def PT(p, at, dn, rot=None):
        return S.ekle(p, at, 'ROTAS-PISLIK-TUTUCU', 'V', 'PİSLİK TUTUCU (Y TİPİ)', [f'{dn} PN16', 'Paslanmaz elek'], rot=rot)

    def TM(at, yon):
        return S.brans(at, 'ROTAS-TERMOMETRE', yon, 'TM', 'TERMOMETRE', ['0-120 °C', 'Daldırma kovanlı, Ø100 kadran'])

    def MN(at, yon, ad='MANOMETRE', oz=('0-10 bar', 'Ø100 kadran, musluklu'), katman=VANA):
        return S.brans(at, 'ROTAS-MANOMETRE', yon, 'M', ad, oz, katman=katman)

    def HP(at, yon):
        return S.brans(at, 'ROTAS-OHAC', yon, 'HP', 'OTOMATİK HAVA PURJÖRÜ', ['1/2"', 'Küresel vanalı'])

    def POMPA_(p, at, z, rot=None, ad=None):
        oz = [f'Q={tr(z["debi"])} m³/h', f'H={tr(z["basma"])} mSS', 'Islak rotorlu, frekans konvertörlü',
              f'Motor ≈ {tr(motor_kw(z["debi"], z["basma"]), 2)} kW (tahmini)']
        return S.ekle(p, at, 'ROTAS-POMPA', 'P', ad, oz, rot=rot, katman=POMPA)

    PITCH, BW, BH = 280.0, 140.0, 180.0
    Y_G = BH + 270
    Y_D = -250.0
    xs = [i * PITCH for i in range(n)]
    xL = xs[-1]
    notr = P.get('notralizasyon')

    # ================================================================ 1) ANA HİDROLİK ŞEMA
    kp = K.get('pompa')
    for i, x in enumerate(xs):
        S.blok('ROTAS-KAZAN-DUVAR', (x, 0), 0, 1, 'K', K.get('ad', 'DUVAR TİPİ YOĞUŞMALI KAZAN (KASKAD)'),
               [f'Q={tr(qk)} kW ({tr(qk * 860, 0)} kcal/h)', K.get('tip', 'Duvar tipi yoğuşmalı, doğalgaz yakıtlı'),
                f'{tg}/{td} °C', f'Kaskad: {n} × {tr(qk)} = {tr(QT)} kW'], CIHAZ, sabit=(x + 70, 20))
        S.yazi((x + 70, 62), f'{tr(qk)} kW', 9, YAZ, ic=True)
        S.yazi((x + 70, 43), f'{tg}/{td} °C', 8, YAZ, ic=True)
        # gidiş (üst): emniyet grubu + kazan pompası
        g = S.hat(GID, [(x + 110, BH + 8), (x + 110, Y_G)], dn_k)
        S.brans((x + 110, BH + 30), 'ROTAS-EMNIYET-VENTILI', 0, 'EV', 'EMNİYET VENTİLİ (KAZAN)',
                [f'{ev_dn}', f'Açma basıncı {tr(ev_bar)} bar', 'Kapatılamaz bağlantı'])
        TM((x + 110, BH + 75), 0)
        MN((x + 110, BH + 115), 0)
        HP((x + 110, BH + 150), 180)
        if kp:
            POMPA_(g, (x + 110, BH + 190), kp, rot=90, ad=f'KAZAN SİRKÜLASYON POMPASI ({kp.get("ad", "IP-1")})')
            CV(g, (x + 110, BH + 222), dn_k, rot=90)
        V(g, (x + 110, BH + 250), dn_k, rot=90)
        # baca / gaz / yoğuşma: yalnız bağlantı ucu (hatlar ayrı bölgede — kesişme yok)
        S.hat(BACA, [(x + 30, BH + 12), (x + 30, BH + 48)], None, w=3.0, etiket='', ok='son')
        S.yazi((x + 30, BH + 62), 'BACA', 7, YAZ)
        S.hat(YOG, [(x + 20, -8), (x + 20, -48)], None, etiket='', ok='son')
        S.yazi((x + 20, -60), 'YOĞ.', 7, YAZ)
        S.hat(GAZ, [(x + 60, -48), (x + 60, -8)], None, etiket='', ok='son')
        S.yazi((x + 60, -60), 'GAZ', 7, YAZ)
        dk = S.hat(DON, [(x + 110, -8), (x + 110, Y_D)], dn_k)
        V(dk, (x + 110, -40), dn_k, rot=90)
        if i == 0:
            S.yazi((x - 40, BH / 2), f'{n} × {tr(qk)} kW', 10, YAZ, TA.MIDDLE_RIGHT)
            S.yazi((x - 40, BH / 2 - 16), 'KASKAD KAZAN', 10, YAZ, TA.MIDDLE_RIGHT)

    # ---------------------------------------------------------------- denge kabı bölgesi
    x_b = xL + 420.0
    x_a = x_b - 50.0
    x_dk = x_a + 270.0
    y_t = 120.0
    y_b = y_t + BL.DENGE_ALT_Y
    G = S.hat(GID, [(xs[0] + 110, Y_G), (x_a, Y_G), (x_a, y_t), (x_dk, y_t)], dn_p,
              etiket=f'KAZAN GİDİŞ KOLLEKTÖRÜ {dn_p} - {tg} °C')
    HP((x_a - 40, Y_G), 90)
    V(G, (x_a + 28, y_t), dn_p)
    ha_x = x_a + 55
    S.blok('ROTAS-HAVA-AYIRICI', (ha_x, y_t), 0, 1, 'HA', 'HAVA AYIRICI', [f'Bağlantı {dn_p}', 'Mikro kabarcık tipi, otomatik purjörlü'],
           CIHAZ, tercih=[(0, 1)])
    G['kes'].append((GM.konum(G['pts'], (ha_x + BL.HAVA_AYIRICI[0], y_t))[0], GM.konum(G['pts'], (ha_x + BL.HAVA_AYIRICI[1], y_t))[0]))
    TM((x_a + 140, y_t), 90)
    MN((x_a + 180, y_t), 90)
    V(G, (x_a + 235, y_t), dn_p)
    dk_cap = P.get('denge_kabi', {}).get('cap', 'Ø300')
    S.blok('ROTAS-DENGE-KABI', (x_dk, y_t), 0, 1, 'DK', 'DENGE KABI (HİDROLİK AYIRICI)',
           [dk_cap, f'Bağlantı {dn_su(max(q_p, q_s))}', f'Maks. debi {tr(max(q_p, q_s))} m³/h',
            'Hava atıcı + çamur tahliyeli'], CIHAZ, tercih=[(1, 0), (-1, 0)])
    D = S.hat(DON, [(x_dk, y_b), (x_b, y_b), (x_b, Y_D), (xs[0] + 110, Y_D)], dn_p,
              etiket=f'KAZAN DÖNÜŞ KOLLEKTÖRÜ {dn_p} - {td} °C')
    V(D, (x_dk - 28, y_b), dn_p)
    ta_x = x_b + 70
    S.blok('ROTAS-TORTU-AYIRICI', (ta_x, y_b), 0, 1, 'TA', 'TORTU VE PİSLİK AYIRICI',
           [f'Bağlantı {dn_p}', 'Manyetik çubuklu, blöf vanalı'], CIHAZ, tercih=[(0, -1)])
    D['kes'].append((GM.konum(D['pts'], (ta_x + BL.TORTU[1], y_b))[0], GM.konum(D['pts'], (ta_x, y_b))[0]))
    TM((x_b + 160, y_b), 270)
    V(D, (x_b + 35, y_b), dn_p)
    # kapalı genleşme tankı (dönüş kollektörüne, kilitlenebilir vana ile)
    gt = P.get('genlesme', {'hacim_l': 500})
    x_gt = xL + 235.0
    sgt = 0.55 + 0.25 * min(1.0, gt['hacim_l'] / 1000.0)
    gp = S.hat(DON, [(x_gt, Y_D), (x_gt, Y_D + 60)], 'DN25', etiket='')
    S.ekle(gp, (x_gt, Y_D + 30), 'ROTAS-KILITLI-VANA', 'V', 'KİLİTLENEBİLİR (MÜHÜRLÜ) VANA', ['DN25 PN16', 'Genleşme tankı bağlantısı'],
           rot=90)
    ozg = [f'V={tr(gt["hacim_l"], 0)} L', 'Membranlı, kapalı tip']
    if gt.get('on_basinc'):
        ozg.append(f'Ön basınç {tr(gt["on_basinc"])} bar')
    if gt.get('maks_bar'):
        ozg.append(f'Maks. işletme {tr(gt["maks_bar"])} bar')
    S.blok('ROTAS-GENLESME-TANKI', (x_gt, Y_D + 60), 0, sgt, 'GT', 'KAPALI GENLEŞME TANKI', ozg, CIHAZ, tercih=[(1, 0), (-1, 0)])
    S.yazi((x_gt - 24 * sgt - 6, Y_D + 60 + 62 * sgt), f'{tr(gt["hacim_l"], 0)} L', 8, YAZ, TA.MIDDLE_RIGHT)
    # sistem doldurma (dönüş kollektörüne)
    if P.get('doldurma', True):
        x_df = x_gt + 80
        df = S.hat(SOG, [(x_df - 470, -340), (x_df, -340), (x_df, Y_D)], 'DN20', etiket='SİSTEM DOLDURMA DN20')
        V(df, (x_df - 420, -340), 'DN20')
        PT(df, (x_df - 365, -340), 'DN20')
        S.ekle(df, (x_df - 305, -340), 'ROTAS-OTOMATIK-DOLUM', 'V', 'OTOMATİK DOLUM VANASI', ['DN20', 'Basınç ayarlı (1-4 bar), manometreli'])
        CV(df, (x_df - 245, -340), 'DN20')
        V(df, (x_df, -295), 'DN20', rot=90)
        S.yazi((x_df - 480, -340), 'ŞEBEKEDEN (YUMUŞATILMIŞ SU)', 9, YAZ, TA.MIDDLE_RIGHT)

    # ---------------------------------------------------------------- sekonder: kollektörler + zonlar
    x_n = x_dk + BL.DENGE_SAG_X
    x_k0 = x_n + 130.0
    sg = S.hat(GID, [(x_n, y_t), (x_k0 - 9, y_t)], dn_s, etiket='')
    sd = S.hat(DON, [(x_k0 - 9, y_b), (x_n, y_b)], dn_s, etiket='')
    TM((x_n + 40, y_t), 90)
    TM((x_n + 40, y_b), 270)
    V(sg, (x_n + 90, y_t), dn_s)
    V(sd, (x_n + 90, y_b), dn_s)
    zx = x_k0 + 70.0
    kg_agiz = kd_agiz = 0
    zon_baglanti = []
    for z in zonlar:
        for k in range(int(z.get('adet', 1))):
            ad = z['ad'] + (f'.{k + 1}' if z.get('adet', 1) > 1 else '')
            dn = dn_su(z['debi'])
            yedek = z.get('yedek', False)
            gen = 230.0 if yedek else 140.0
            xz = zx + gen / 2 if yedek else zx + 40
            s0 = y_t + 9
            tr_ = S.hat(GID, [(xz, s0), (xz, s0 + 95 if yedek else s0 + 400)], dn,
                        etiket='' if yedek else dn, ok=None if (yedek or gomulu) else 'son')
            V(tr_, (xz, s0 + 30), dn, rot=90)
            PT(tr_, (xz, s0 + 64), dn, rot=90)
            pad = f'ZON POMPASI {z["ad"]} - {z.get("aciklama", "")}'.rstrip(' -')
            if yedek:
                ys, yj = s0 + 95, s0 + 300
                lp = S.hat(GID, [(xz, ys), (xz - 45, ys), (xz - 45, yj), (xz, yj)], dn, etiket='')
                rp = S.hat(GID, [(xz, ys), (xz + 45, ys), (xz + 45, yj), (xz, yj)], dn, etiket='')
                for leg, xl in ((lp, xz - 45), (rp, xz + 45)):
                    V(leg, (xl, ys + 32), dn, rot=90)
                    POMPA_(leg, (xl, ys + 85), z, rot=90, ad=pad + ' (ASIL + YEDEK)')
                    CV(leg, (xl, ys + 135), dn, rot=90)
                    V(leg, (xl, ys + 172), dn, rot=90)
                up = S.hat(GID, [(xz, yj), (xz, yj + 140)], dn, ok=None if gomulu else 'son')
                TM((xz, yj + 35), 0)
                MN((xz, yj + 80), 180)
                y_ust = yj + 140
                ust_hat = up
            else:
                POMPA_(tr_, (xz, s0 + 115), z, rot=90, ad=pad)
                CV(tr_, (xz, s0 + 160), dn, rot=90)
                V(tr_, (xz, s0 + 198), dn, rot=90)
                TM((xz, s0 + 240), 0)
                MN((xz, s0 + 285), 180)
                y_ust = s0 + 400
                ust_hat = tr_
            dz = S.hat(DON, [(xz, y_b - 9), (xz, y_b - 175)], dn, ok=None if gomulu else 'bas')
            V(dz, (xz, y_b - 40), dn, rot=90)
            TM((xz, y_b - 85), 0)
            if not gomulu:
                S.yazi((xz, y_ust + 30), f'{ad} {z.get("aciklama", "")}'.strip(), 9, YAZ)
                S.yazi((xz, y_ust + 14), f'GİDİŞ {tg} °C', 8, YAZ)
                S.yazi((xz, y_b - 189), f'{ad} {z.get("aciklama", "")}'.strip(), 9, YAZ)
                S.yazi((xz, y_b - 205), f'DÖNÜŞ {td} °C', 8, YAZ)
            zon_baglanti.append((ust_hat, dz, xz, y_ust))
            kg_agiz += 1; kd_agiz += 1
            zx += gen + 30
            x_son = xz
    # boyler
    x_kg1 = x_kd1 = x_son + 60
    if boy:
        sp = boy['sarj_pompa']
        dnb = dn_su(sp['debi'])
        x_bg = zx + 30
        x_bd = x_bg + 70
        x_by = x_bg + 210
        y_bb = y_t + 100
        bg = S.hat(GID, [(x_bg, y_t + 9), (x_bg, y_bb + 140), (x_by - 65, y_bb + 140)], dnb)
        V(bg, (x_bg, y_t + 40), dnb, rot=90)
        POMPA_(bg, (x_bg, y_t + 90), sp, rot=90, ad='BOYLER ŞARJ POMPASI')
        CV(bg, (x_bg, y_t + 135), dnb, rot=90)
        V(bg, (x_bg, y_t + 175), dnb, rot=90)
        bd = S.hat(DON, [(x_by - 65, y_bb + 60), (x_bd, y_bb + 60), (x_bd, y_b + 9)], dnb)
        V(bd, (x_bd, y_t + 40), dnb, rot=90)
        S.blok('ROTAS-BOYLER', (x_by, y_bb), 0, 1, 'BY', 'BOYLER (KULLANIM SICAK SUYU)',
               [f'V={tr(boy["hacim_l"], 0)} L', boy.get('tip', 'Serpantinli, emaye kaplamalı'),
                f'Primer {tg}/{td} °C - kullanım 60 °C'], CIHAZ, tercih=[(-1, 0), (0, 1)])
        S.yazi((x_by, y_bb + 190), f'{tr(boy["hacim_l"], 0)} L', 9, YAZ, ic=True)
        sc = S.hat(SIC, [(x_by, y_bb + 260), (x_by, y_bb + 370)], boy.get('cap', 'DN32'), ok='son')
        TM((x_by, y_bb + 300), 0)
        S.yazi((x_by, y_bb + 384), 'KULLANIM SICAK SUYU', 9, YAZ)
        so = S.hat(SOG, [(x_by, y_b - 180), (x_by, y_bb)], boy.get('cap', 'DN32'))
        V(so, (x_by, y_b - 150), boy.get('cap', 'DN32'), rot=90)
        PT(so, (x_by, y_b - 115), boy.get('cap', 'DN32'), rot=90)
        CV(so, (x_by, y_b - 80), boy.get('cap', 'DN32'), rot=90)
        S.brans((x_by, y_b - 20), 'ROTAS-EMNIYET-VENTILI', 0, 'EV', 'EMNİYET VENTİLİ (BOYLER)',
                [boy.get('ev_cap', 'DN20'), f'Açma basıncı {tr(boy.get("ev_bar", 6))} bar', 'Sıhhi su tipi'])
        S.yazi((x_by, y_b - 194), 'ŞEBEKEDEN SOĞUK SU', 9, YAZ)
        sr = P.get('sirkulasyon')
        if sr:
            dnr = sr.get('cap', 'DN25')
            rr = S.hat(SIR, [(x_by + 330, y_bb + 170), (x_by + 65, y_bb + 170)], dnr)
            V(rr, (x_by + 300, y_bb + 170), dnr)
            POMPA_(rr, (x_by + 245, y_bb + 170), sr, ad='SIHHİ SICAK SU SİRKÜLASYON POMPASI')
            CV(rr, (x_by + 195, y_bb + 170), dnr)
            V(rr, (x_by + 145, y_bb + 170), dnr)
            S.yazi((x_by + 338, y_bb + 170), 'SİRKÜLASYON DÖNÜŞÜ', 9, YAZ, TA.MIDDLE_LEFT)
        x_kg1 = x_bg + 30
        x_kd1 = x_bd + 30
        kg_agiz += 1; kd_agiz += 1
    S.blok(BL.kollektor(S.doc, x_kg1 - x_k0), (x_k0, y_t), 0, 1, 'KL', 'GİDİŞ KOLLEKTÖRÜ',
           (f'{dn_su(q_s)} eşdeğeri, siyah çelik', f'{kg_agiz} çıkış ağızlı', 'Hava purjörü + boşaltma vanalı'), KOL,
           tercih=[(0, -1)])
    S.blok(BL.kollektor(S.doc, x_kd1 - x_k0), (x_k0, y_b), 0, 1, 'KL', 'DÖNÜŞ KOLLEKTÖRÜ',
           (f'{dn_su(q_s)} eşdeğeri, siyah çelik', f'{kd_agiz} giriş ağızlı', 'Boşaltma vanalı'), KOL, tercih=[(0, 1)])
    HP((x_k0 + 20, y_t + 9), 90)
    x_ana_sag = max(x_kg1, x_kd1) + (430 if boy else 120)
    x_zon_min = min(zb[2] for zb in zon_baglanti) if zon_baglanti else x_ana_sag

    # ================================================================ 2) AYRI BÖLGELER (kesişmesiz)
    y_r = -430.0                       # bölge başlıkları
    x_r = -900.0
    sinir = (x_zon_min - 80.0) if gomulu else 1e9

    def bolge_cerceve(x0, x1, y0, y1, baslik):
        S.msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': BOL})
        S.yazi((x0 + 12, y1 - 14), baslik, 11, BAS, TA.MIDDLE_LEFT, maske=False, ic=True)

    # ---- 2a) doğalgaz bağlantı şeması
    def gaz_bolgesi(x0, y1):
        gy = y1 - 175
        xg0 = x0 + 150
        reg = gz.get('regulator')
        x = xg0 + 40
        dur = []                                   # sıra: (tip, x)
        if gz.get('vana', True):
            dur.append(('ana', x)); x += 60
        if gz.get('selenoid', True):
            dur.append(('sel', x)); x += 70
        if gz.get('filtre', True):
            dur.append(('fil', x)); x += 65 + (60 if reg else 0)      # regülatör girişinde çap etiketi payı
        if reg:
            dur.append(('reg', x)); x += 70
        dur.append(('man', x)); x += 45
        dur.append(('kv', x)); x += 70
        x_d0 = x + 20
        PG = 120.0
        x_son = x_d0 + (n - 1) * PG
        if reg:
            xr_ = [xx for t, xx in dur if t == 'reg'][0]
            g1 = S.hat(GAZ, [(xg0, gy), (xr_, gy)], dng_g, etiket=f'{dng_g} - {reg.get("giris", "300 mbar")}')
            g2 = S.hat(GAZ, [(xr_ + 11, gy), (x_son, gy)], dng, etiket=f'DOĞALGAZ KOLLEKTÖRÜ {dng} - {reg.get("cikis", "21 mbar")}')
            g1['kes'].append((GM.uzunluk(g1['pts']) - 10.5, GM.uzunluk(g1['pts']) + 1))
            S.blok('ROTAS-REGULATOR', (xr_, gy), 0, 1, 'GR', 'GAZ BASINÇ REGÜLATÖRÜ',
                   [f'Giriş {reg.get("giris", "300 mbar")} / çıkış {reg.get("cikis", "21 mbar")}', f'Q ≥ {tr(qg)} m³/h',
                    'Emniyet kapama (SSV) + tahliye (SRV) donanımlı'], GAZS, tercih=[(0, -1)])
        else:
            g1 = g2 = S.hat(GAZ, [(xg0, gy), (x_son, gy)], dng, etiket=f'DOĞALGAZ KOLLEKTÖRÜ {dng}')
        for t, xx in dur:
            if t == 'ana':
                S.ekle(g1, (xx, gy), 'ROTAS-KURESEL-VANA', 'V', 'DOĞALGAZ ANA KESME VANASI (KAZAN DAİRESİ DIŞI)',
                       [dng_g, 'TS EN 331, sarı kollu, kilitlenebilir'], katman=GAZS, tercih=[(0, -1)])
            elif t == 'sel':
                S.ekle(g1, (xx, gy), 'ROTAS-SELENOID', 'SV', 'GAZ SELENOİD VANASI',
                       [dng_g, 'Normalde kapalı, manuel kurmalı', 'Gaz alarm cihazı ile kumanda (elektrik projesinde)'],
                       katman=GAZS, tercih=[(0, -1)])
            elif t == 'fil':
                S.ekle(g1, (xx, gy), 'ROTAS-PISLIK-TUTUCU', 'GF', 'GAZ FİLTRESİ', [dng_g, '50 µm'], katman=GAZS, tercih=[(0, 1)])
            elif t == 'man':
                MN((xx, gy), 90, 'MANOMETRE (GAZ)', ('0-400 mbar' if reg else '0-60 mbar', 'Musluklu'), katman=GAZS)
            elif t == 'kv':
                S.ekle(g2, (xx, gy), 'ROTAS-KURESEL-VANA', 'V', 'DOĞALGAZ KÜRESEL VANASI (KOLLEKTÖR)', [dng, 'TS EN 331, sarı kollu'],
                       katman=GAZS, tercih=[(0, -1)])
        x_sel = [xx for t, xx in dur if t == 'sel']
        x_dis = (x_sel[0] + 35) if x_sel else (xg0 + 70)
        S.msp.add_line((x_dis, gy - 45), (x_dis, gy - 8), dxfattribs={'layer': BOL})
        S.msp.add_line((x_dis, gy + 8), (x_dis, gy + 70), dxfattribs={'layer': BOL})       # kazan dairesi duvarı
        S.yazi((x_dis - 4, gy + 62), 'DIŞ', 7, YAZ, TA.MIDDLE_RIGHT)
        S.yazi((x_dis + 4, gy + 62), 'KAZAN DAİRESİ', 7, YAZ, TA.MIDDLE_LEFT)
        if gz.get('alarm', True):                 # gaz alarm cihazı (tavan) — sinyal hattı çizilmez (elektrik kalemi)
            S.blok('ROTAS-GAZ-ALARM', (x_d0 - 85, gy + 120), 0, 1, 'GA', 'GAZ ALARM CİHAZI + CO DEDEKTÖRÜ',
                   ['Ex-proof, sesli-ışıklı', 'Üst menfez seviyesinden yüksekte', 'Bağlantıları elektrik projesinde'], GAZS,
                   tercih=[(1, 0), (-1, 0)])
        for i in range(n):
            xd = x_d0 + i * PG
            dp = S.hat(GAZ, [(xd, gy), (xd, gy + 130)], dng_k, ok='son', etiket='')
            S.ekle(dp, (xd, gy + 35), 'ROTAS-KURESEL-VANA', 'V', 'DOĞALGAZ KÜRESEL VANASI (CİHAZ)', [dng_k, 'TS EN 331, sarı kollu'],
                   rot=90, katman=GAZS, tercih=[(1, 0)])
            S.ekle(dp, (xd, gy + 85), 'ROTAS-ESNEK-BAGLANTI', 'V', 'ESNEK BAĞLANTI (GAZ)',
                   [dng_k, 'Metal örgülü, çalışma basıncının 3 katına dayanıklı'], rot=90, katman=GAZS, tercih=[(1, 0)])
            S.yazi((xd, gy + 144), f'K-{i + 1:02d} KAZANINA', 8, YAZ)
            S.yazi((xd + 6, gy + 108), dng_k, 7, CAP, TA.MIDDLE_LEFT)
        S.yazi((xg0 - 8, gy), 'DOĞALGAZ GİRİŞİ', 9, YAZ, TA.MIDDLE_RIGHT)
        S.yazi((xg0 - 8, gy - 16), '(SAYAÇ DIŞARIDA)', 8, YAZ, TA.MIDDLE_RIGHT)
        x1 = x_son + 70
        bolge_cerceve(x0, x1, gy - 70, y1, 'DOĞALGAZ BAĞLANTI ŞEMASI (kazan altı GAZ uçları)')
        return x1, gy - 70

    # ---- 2b) yoğuşma drenaj şeması
    def yogusma_bolgesi(x0, y1):
        cy = y1 - 150
        PY = 70.0
        xs_ = [x0 + 60 + i * PY for i in range(n)]
        for i, xx in enumerate(xs_):
            S.hat(YOG, [(xx, cy + 80), (xx, cy)], None, etiket='')
            S.yazi((xx, cy + 92), f'K-{i + 1:02d}', 8, YAZ)
        xe = xs_[-1] + 60
        if notr:
            S.hat(YOG, [(xs_[0], cy), (xe, cy)], None, etiket='YOĞUŞMA SUYU DN25 (PP)')
            S.blok('ROTAS-NOTRALIZASYON', (xe, cy), 0, 1, 'NU', 'NÖTRALİZASYON ÜNİTESİ',
                   [f'Kapasite ≥ {tr(QT)} kW', 'Granül dolgulu, çıkış pH 6,5-9', 'Yoğuşma suyu pH ≈ 3,5'], CIHAZ, tercih=[(0, 1)])
            S.hat(YOG, [(xe + 120, cy), (xe + 175, cy)], None, etiket='', ok='son')
            xt = xe + 183
        else:
            S.hat(YOG, [(xs_[0], cy), (xe + 60, cy)], None, etiket='YOĞUŞMA SUYU DN25 (PP)', ok='son')
            xt = xe + 68
        S.yazi((xt, cy + 8), 'SİFONLU OLARAK', 8, YAZ, TA.MIDDLE_LEFT)
        S.yazi((xt, cy - 8), 'PİS SU TESİSATINA', 8, YAZ, TA.MIDDLE_LEFT)
        x1 = xt + 110
        bolge_cerceve(x0, x1, cy - 60, y1, 'YOĞUŞMA DRENAJ ŞEMASI')
        return x1, cy - 60

    # ---- 2c) baca bağlantı şeması
    bc = P.get('baca', {})

    def baca_bolgesi(x0, y1):
        x_ch = x0 + 70
        yk = y1 - 170                       # baca kollektörü
        PB = 70.0
        xs_ = [x_ch + 80 + i * PB for i in range(n)]
        for i, xx in enumerate(xs_):
            S.hat(BACA, [(xx, yk - 70), (xx, yk)], None, w=3.0, etiket='')
            S.yazi((xx, yk - 82), f'K-{i + 1:02d}', 8, YAZ)
        S.hat(BACA, [(xs_[-1], yk), (x_ch, yk)], None, w=4.0, etiket='')
        S.hat(BACA, [(x_ch, yk - 40), (x_ch, y1 - 60)], None, w=4.0, etiket='')
        S.blok('ROTAS-BACA-SAPKA', (x_ch, y1 - 60), 0, 1, 'B', 'BACA (KASKAD ORTAK)',
               (bc.get('cap', 'Ø250'), bc.get('tip', 'Paslanmaz çelik çift cidarlı'), 'TS EN 13384-2 hesabına göre',
                'Kollektör kazanlara doğru %3 eğimli, yoğuşma drenajlı'), BACA, tercih=[(1, 0)])
        S.yazi((x_ch - 10, yk + 40), f'BACA {bc.get("cap", "Ø250")}', 8, YAZ, TA.MIDDLE_RIGHT)
        S.yazi(((x_ch + xs_[-1]) / 2, yk + 14), 'BACA KOLLEKTÖRÜ', 8, YAZ)
        S.yazi((x_ch, yk - 52), 'DRENAJ', 7, YAZ)
        x1 = xs_[-1] + 60
        bolge_cerceve(x0 - 50, x1, yk - 100, y1, 'BACA BAĞLANTI ŞEMASI')
        return x1, yk - 100

    bx, by_alt = gaz_bolgesi(x_r, y_r)
    sira = [yogusma_bolgesi, baca_bolgesi]
    xr_, yr_, alt = bx + 60, y_r, by_alt
    for f in sira:
        tahmin = xr_ + 90 + n * 80 + 330
        if tahmin > sinir:                        # gömülü: zon dönüşüne yaklaşma -> alt satır
            xr_, yr_ = x_r, alt - 40
        x1, a = f(xr_, yr_)
        alt = min(alt, a)
        xr_ = x1 + 60
    y_bolge_alt = alt

    # ---------------------------------------------------------------- gömülü bağlantı uçları
    S.baglanti = None
    if gomulu and zon_baglanti:
        ust_hat, dz, xz, y_ust = zon_baglanti[0]
        y_top = max(y_ust, Y_G + 60) + 40
        ust_hat['pts'][-1] = (xz, y_top)
        ust_hat['ok'] = 'orta'
        y_alt = y_bolge_alt - 40
        dz['pts'][-1] = (xz, y_alt)
        dz['ok'] = None
        S.baglanti = {'gidis': (xz, y_top), 'donus': (xz, y_alt)}

    # ================================================================ kesişme denetimi, çizim, numara, etiket
    S.kesisim_denetle()
    S.boru_ciz()
    satir = S.numarala()
    xmin = x_r - 120
    if not gomulu:
        ytop = (Y_G + 260 if not boy else y_t + 100 + 470)
        S.yazi(((xmin + x_ana_sag) / 2, ytop), 'KAZAN DAİRESİ PRENSİP ŞEMASI', 32, BAS, maske=False)
        S.yazi(((xmin + x_ana_sag) / 2, ytop - 40), 'ÖLÇEKSİZ', 14, BAS, maske=False)
        if P.get('proje'):
            S.yazi(((xmin + x_ana_sag) / 2, ytop - 66), P['proje'], 12, YAZ, maske=False)
        if P.get('deneme', True):
            S.yazi((xmin + 120, ytop), 'DENEME', 40, BAS, maske=False)
    S.etiketle()
    S.satir = satir
    S.notlar = notlar_listesi(P, notr)
    if not gomulu:
        ty = y_bolge_alt - 80
        xe, ye = tablo_ciz(S.msp, satir, xmin, ty)
        notlar_ciz(S.msp, S.notlar, xmin, ye - 60)
        from ezdxf import bbox as zb
        bb = zb.extents(S.msp, fast=True)
        x0f, y0f, x1f, y1f = bb.extmin.x - 60, bb.extmin.y - 60, bb.extmax.x + 60, bb.extmax.y + 60
        S.msp.add_lwpolyline([(x0f, y0f), (x1f, y0f), (x1f, y1f), (x0f, y1f)],
                             close=True, dxfattribs={'layer': PAFTA, 'const_width': 3})
    S.doc.saveas(cikti)
    return S


def notlar_listesi(P, notr):
    nt = list(P.get('notlar') or NOTLAR)
    nt.append('Yoğuşma suları nötralizasyon ünitesinden geçirilerek pis su tesisatına verilecektir.' if notr else
              'Yoğuşma suları sifonlu olarak pis su tesisatına verilecektir.')
    return nt


NOTLAR = [
    'Kazanlar kaskad kontrol panosu ile sırayla devreye alınacak, dış hava kompanzasyonlu çalıştırılacaktır.',
    'Her kazan gidişinde kapatılamaz emniyet ventili, termometre, manometre ve otomatik hava purjörü bulunacaktır.',
    'Kapalı genleşme tankı dönüş hattına kilitlenebilir (mühürlü) vana ile bağlanacaktır.',
    'DN65 ve üzeri vanalar kelebek, DN50 ve altı küresel vana olacaktır.',
    'Gaz sayacı ve ana kesme vanası kazan dairesi dışında olacaktır. Gaz alarm cihazı ve selenoid vana elektrik bağlantıları '
    'elektrik projesindedir (bu paftada elektrik kalemi çizilmez).',
    'Kazan altındaki GAZ / YOĞUŞMA ve üstündeki BACA uçları ayrı bölgelerdeki doğalgaz, yoğuşma drenaj ve baca bağlantı '
    'şemalarında devam eder (K-01, K-02 ... kazan numaraları ile).',
    'Doğalgaz hattı çapları ön boyut olup doğalgaz projesine göre kesinleştirilecektir.',
    'Baca TS EN 13384-2 hesabına göre paslanmaz çelik çift cidarlı yapılacaktır.',
    'Dönüş hatları kesikli çizgi ile gösterilmiştir; şema ölçeksizdir.',
]


if __name__ == '__main__':
    P = json.load(open(sys.argv[1], encoding='utf-8'))
    S = ciz(P, sys.argv[2])
    for u in S.uyarilar:
        print('UYARI:', u)
    print('boru kesişmesi:', len(S.kesisim))
    if len(sys.argv) > 3:
        import onizleme
        onizleme.png(sys.argv[2], sys.argv[3])
