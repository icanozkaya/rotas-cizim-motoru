# -*- coding: utf-8 -*-
# ==========================================================================================================
# DONDURULMUŞ TABAN (değiştirmeyin): ONAYLI kazan dairesi plan / kesit / kısmi görünüş çizimi (plan_kesit.py)
# bu sürümle (git dc2bb3e, 14.10.2026) üretildi ve kullanıcı 14.10.2026 16:39'da onayladı. plan_kesit.py
# Sema sınıfını, çizim yardımcılarını (hat, ekle, brans, kopruler, kollektor, etiketle, tablo) ve katman
# tanımlarını BURADAN alır; böylece onaylı görünüş / tarz birebir korunur. Prensip şeması teslimi için
# kazan_dairesi.py (R2) kullanılır; numaralar plan_kesit.numara_haritasi(P, 'R2') ile R2 şemayla senkronlanır.
# ==========================================================================================================
"""Parametrik KAZAN DAİRESİ PRENSİP ŞEMASI (deneme modülü: kazan_dairesi).

Kullanım:  python3 kazan_dairesi.py girdi.json cikti.dxf [onizleme.png]
Girdi JSON alanları için BENIOKU.md'ye bakın. Çıktı yalnız DXF (R2018), birim cm, şema ölçeksiz.

Akış: kaskad kazanlar -> kazan gidiş kollektörü -> hava ayırıcı -> denge kabı -> gidiş kollektörü -> zon pompaları
(asıl + yedek) -> zonlar; dönüşler kesikli. Kazan altı: yoğuşma (nötralizasyon), doğalgaz hattı, kazan dönüşü.
Her vana/cihaz gerçek sembolüyle (MTY blokları, yoksa 03_SEMBOLLER geometrisi) ve numaralı; cihaz listesi tablosu
kullanıcının YANGIN POMPA GRUBU CİHAZ LİSTESİ tarzında (NO | CİHAZ | TEKNİK ÖZELLİKLERİ).
"""
import json
import math
import os
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import LineString, Polygon, box as sbox
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bloklar as BL          # noqa: E402
import geometri as GM         # noqa: E402

# ----------------------------------------------------------------------------- katmanlar (ROTAS- önekli)
GID, DON = 'ROTAS-ISITMA-GIDIS', 'ROTAS-ISITMA-DONUS'
GAZ, BACA, YOG = 'ROTAS-DOGALGAZ-BORU', 'ROTAS-ISITMA-BACA', 'ROTAS-ISITMA-YOGUSMA'
SOG, SIC, SIR = 'ROTAS-SIHHI-SOGUK-SU', 'ROTAS-SIHHI-SICAK-SU', 'ROTAS-SIHHI-SIRKULASYON'
VANA, CIHAZ, POMPA, GAZS = 'ROTAS-ISITMA-VANA', 'ROTAS-ISITMA-CIHAZ', 'ROTAS-ISITMA-POMPA', 'ROTAS-DOGALGAZ-SEMBOL'
KOL, SINYAL = 'ROTAS-ISITMA-KOLLEKTOR', 'ROTAS-DOGALGAZ-SINYAL'
ETK, CAP, YAZ, BAS, MASKE, PAFTA = ('ROTAS-ISITMA-ETIKET', 'ROTAS-ISITMA-CAP', 'ROTAS-ISITMA-YAZI', 'ROTAS-ISITMA-BASLIK',
                                     'ROTAS-MASKE', 'ROTAS-PAFTA')
T_CER, T_CIZ, T_YAZ, T_BAS = 'ROTAS-HESAP-CERCEVE', 'ROTAS-HESAP-CIZGI', 'ROTAS-HESAP-YAZI', 'ROTAS-HESAP-BASLIK'
KATMAN = {GID: (10, 'Continuous'), DON: (30, 'DASHED'), GAZ: (2, 'Continuous'), BACA: (8, 'Continuous'),
          YOG: (6, 'DASHED'), SOG: (5, 'Continuous'), SIC: (1, 'Continuous'), SIR: (31, 'DASHDOT'),
          VANA: (1, 'Continuous'), CIHAZ: (135, 'Continuous'), POMPA: (30, 'Continuous'), GAZS: (2, 'Continuous'),
          KOL: (7, 'Continuous'), SINYAL: (2, 'DASHED'), ETK: (3, 'Continuous'), CAP: (41, 'Continuous'),
          YAZ: (7, 'Continuous'), BAS: (5, 'Continuous'), MASKE: (7, 'Continuous'), PAFTA: (7, 'Continuous'),
          T_CER: (4, 'Continuous'), T_CIZ: (1, 'Continuous'), T_YAZ: (7, 'Continuous'), T_BAS: (2, 'Continuous')}
BORU_KATMAN = {GID, DON, GAZ, BACA, YOG, SOG, SIC, SIR}

HT, HD, HY = 8.0, 7.0, 9.0      # etiket (V-01), çap (DN), açıklama yazı yükseklikleri
WF = 0.85                      # yazı genişlik faktörü
SIRA = ['K', 'P', 'DK', 'HA', 'TA', 'GT', 'KL', 'BY', 'NU', 'B', 'EV', 'HP', 'M', 'TM', 'V', 'GF', 'GR', 'SV', 'GA']

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
        self.kutular = []        # içine yazı konmayacak büyük semboller

    # ------------------------------------------------------------------ boru
    def hat(self, lay, pts, dn=None, w=0.0, etiket=None, ok=None, kopru=True):
        p = dict(lay=lay, pts=[(float(x), float(y)) for x, y in pts], dn=dn, w=w, kes=[], kopru=[], ok=ok,
                 etiket=etiket if etiket is not None else dn, kopru_al=kopru)
        self.borular.append(p)
        return p

    def ekle(self, p, at, blok, kod=None, ad=None, oz=(), rot=None, olcek=1.0, cap=None, katman=VANA, tercih=None):
        """boru üstü (hat içi) sembol: boru ±yarım boy kesilir"""
        s, aci = GM.konum(p['pts'], at)
        r = aci if rot is None else rot
        y = BL.YARIM.get(blok, 10.5) * olcek
        p['kes'].append((s - y, s + y))
        return self.blok(blok, at, r, olcek, kod, ad, oz, cap, katman, tercih, aci)

    def brans(self, at, blok, yon, kod=None, ad=None, oz=(), olcek=1.0, cap=None, katman=VANA, tercih=None):
        """boru yanına dik çıkan cihaz (manometre, termometre, emniyet ventili, purjör): yon = cihazın baktığı açı"""
        return self.blok(blok, at, yon - 90.0, olcek, kod, ad, oz, cap, katman, tercih, None, yon)

    def blok(self, blok, at, rot, olcek, kod, ad, oz, cap, katman, tercih=None, boru_aci=None, yon=None, merkez=None,
             sabit=None, kutu=False):
        e = self.msp.add_blockref(blok, at, dxfattribs={'layer': katman, 'rotation': rot % 360,
                                                         'xscale': olcek, 'yscale': olcek})
        bd = self.doc.blocks.get(blok)
        if any(a.dxftype() == 'ATTDEF' for a in bd):
            e.add_auto_attribs({'CAP': cap or ''})
            for a in e.attribs:              # MTY çap özniteliği: değer yazılır (MTY'de güncellenebilir), çizimde gizli
                a.is_invisible = True
        c = dict(kod=kod, ad=ad, oz=tuple(oz), at=merkez or at, ent=e, tercih=tercih, boru_aci=boru_aci, yon=yon,
                 sabit=sabit, buyuk=merkez is not None)
        if kutu:
            self.kutular.append(e)
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
    def kopruler(self):
        r = 5.0
        for i, a in enumerate(self.borular):
            for b in self.borular[i + 1:]:
                if not (a['kopru_al'] and b['kopru_al']):
                    continue
                for (sa, pa, qa) in GM.segmentler(a['pts']):
                    for (sb, pb, qb) in GM.segmentler(b['pts']):
                        x = GM.dik_kesisim(pa, qa, pb, qb, 2.0)
                        if x is None:
                            continue
                        dusey_a = abs(pa[0] - qa[0]) < 1e-6
                        hedef, s0, p0 = (a, sa, pa) if dusey_a else (b, sb, pb)
                        s = s0 + math.dist(p0, x)
                        if any(k0 - r < s < k1 + r for k0, k1 in hedef['kes']):
                            self.uyarilar.append(f'köprü sembol üstüne düştü: {hedef["lay"]} {x}')
                        hedef['kopru'].append(s)

    def boru_ciz(self):
        for p in self.borular:
            L = GM.uzunluk(p['pts'])
            if p['ok']:
                q, aci = GM.nokta(p['pts'], L)
                if p['ok'] == 'son':
                    self.msp.add_blockref('ROTAS-OK', q, dxfattribs={'layer': p['lay'], 'rotation': aci})
                else:
                    t, _ = GM.nokta(p['pts'], L - 14)
                    self.msp.add_blockref('ROTAS-OK', t, dxfattribs={'layer': p['lay'], 'rotation': aci + 180})
                p['kes'].append((L - 14, L + 1))
            for parca in GM.parcala(p['pts'], p['kes'], p['kopru'], 5.0):
                e = self.msp.add_lwpolyline(parca, format='xyb', dxfattribs={'layer': p['lay']})
                if p['w']:
                    e.dxf.const_width = p['w']

    def kollektor(self, x0, x1, y, h=18.0):
        r = h / 2
        self.msp.add_lwpolyline([(x0, y - r, 0), (x1, y - r, 1), (x1, y + r, 0), (x0, y + r, 1)], format='xyb',
                                close=True, dxfattribs={'layer': KOL})

    # ------------------------------------------------------------------ etiket yerleşimi
    def engeller(self):
        geo = GM.model_geometri(self.msp)
        from ezdxf import bbox as zb
        for e in self.kutular:
            b = zb.extents([e])
            geo.append(sbox(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
        return geo

    def etiketle(self):
        geo = self.engeller()
        agac = STRtree(geo)
        yerlesen = []

        def bos(pl):
            g = pl.buffer(1.2)
            if any(g.intersects(geo[i]) for i in agac.query(g)):
                return False
            return not any(g.intersects(y) for y in yerlesen)

        # sabit yazılar önce (konumları verilidir)
        for (p, s, h, lay, al, rot, maske, ic) in self.serbest:
            pl = GM.yazi_kutusu(p, s, h, al, rot, WF)
            if not ic and not bos(pl):
                self.uyarilar.append(f'sabit yazı çakışıyor: {s}')
            yerlesen.append(pl)
            self._yaz(p, s, h, lay, al, rot, maske)
        # cihaz numaraları
        for c in self.cihazlar:
            s = c['etiket']
            x, y = c['at']
            if c.get('sabit'):
                q = c['sabit']
                pl = GM.yazi_kutusu(q, s, HT, TA.MIDDLE_CENTER, 0, WF)
                yerlesen.append(pl)
                self._yaz(q, s, HT + 2, ETK, TA.MIDDLE_CENTER, 0, False)
                continue
            yonler = GM.aday_yonler(c['boru_aci'], c['yon'], c['tercih'])
            ok = False
            mes = (15, 19, 24, 30, 38, 48, 60) if not c.get('buyuk') else tuple(range(20, 200, 8))
            on = yonler[:1] if c['yon'] is not None else []
            aday = [(u, d) for u in on for d in mes] + [(u, d) for d in mes for u in yonler]
            w = len(s) * HT * 0.66 * WF
            for (ux, uy), d in aday:
                q = (x + ux * (d + (w / 2 if ux else 0)), y + uy * (d + (HT / 2 if uy else 0)))
                pl = GM.yazi_kutusu(q, s, HT, TA.MIDDLE_CENTER, 0, WF)
                if bos(pl):
                    yerlesen.append(pl)
                    self._yaz(q, s, HT, ETK, TA.MIDDLE_CENTER, 0, True)
                    ok = True
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
                etk.append(c['etiket'])
            no = etk[0] if len(etk) == 1 else f'{etk[0]} ... {etk[-1]}'
            satir.append((no, k[1], list(k[2]) + [f'Adet: {len(etk)}']))
        return satir

    def tablo(self, satir, x0, y0, baslik='KAZAN DAİRESİ CİHAZ LİSTESİ'):
        m = self.msp
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


# ============================================================================ şema kurgusu
def ciz(P, cikti):
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
        return ('MTY-KELEBEK VANA', 'KELEBEK VANA', [f'{dn} PN16', 'Redüktörlü / kollu, EPDM conta']) \
            if dn_no(dn) >= 65 else ('MTY-KURESEL VANA', 'KÜRESEL VANA', [f'{dn} PN16', 'Tam geçişli, pirinç / çelik gövde'])

    def V(p, at, dn, rot=None, tercih=None):
        b, ad, oz = vana(dn)
        return S.ekle(p, at, b, 'V', ad, oz, rot=rot, cap=dn, tercih=tercih)

    def CV(p, at, dn, rot=None):
        return S.ekle(p, at, 'MTY-CEKVALF VANA', 'V', 'ÇEK VALF', [f'{dn} PN16', 'Yaylı / klapeli, ısıtma suyuna uygun'],
                      rot=rot, cap=dn)

    def PT(p, at, dn, rot=None):
        return S.ekle(p, at, 'MTY-PISLIK TUTUCU', 'V', 'PİSLİK TUTUCU (Y TİPİ)', [f'{dn} PN16', 'Paslanmaz elek'],
                      rot=rot, cap=dn)

    def TM(at, yon):
        return S.brans(at, 'MTY-TERMOMETRE', yon, 'TM', 'TERMOMETRE', ['0-120 °C', 'Daldırma kovanlı, Ø100 kadran'],
                       cap='T')

    def MN(at, yon, ad='MANOMETRE', oz=('0-10 bar', 'Ø100 kadran, musluklu')):
        return S.brans(at, 'MTY-MANOMETRE', yon, 'M', ad, oz, cap='M')

    def HP(at, yon):
        return S.brans(at, 'MTY-O.H.A.C', yon, 'HP', 'OTOMATİK HAVA PURJÖRÜ', ['1/2"', 'Küresel vanalı'], cap='DN15')

    def POMPA_(p, at, z, rot=None, ad=None):
        oz = [f'Q={tr(z["debi"])} m³/h', f'H={tr(z["basma"])} mSS', 'Islak rotorlu, frekans konvertörlü',
              f'Motor ≈ {tr(motor_kw(z["debi"], z["basma"]), 2)} kW (tahmini)']
        return S.ekle(p, at, 'ROTAS-POMPA', 'P', ad, oz, rot=rot, katman=POMPA)

    PITCH, BW, BH = 280.0, 140.0, 180.0
    Y_G, Y_B = BH + 270, BH + 340
    Y_C, Y_GZ, Y_D = -70.0, -170.0, -250.0
    xs = [i * PITCH for i in range(n)]
    xL = xs[-1]
    notr = P.get('notralizasyon')

    # ---------------------------------------------------------------- kazanlar
    kp = K.get('pompa')
    for i, x in enumerate(xs):
        S.blok('ROTAS-KAZAN-DUVAR', (x, 0), 0, 1, 'K', K.get('ad', 'DUVAR TİPİ YOĞUŞMALI KAZAN (KASKAD)'),
               [f'Q={tr(qk)} kW ({tr(qk * 860, 0)} kcal/h)', K.get('tip', 'Duvar tipi yoğuşmalı, doğalgaz yakıtlı'),
                f'{tg}/{td} °C', f'Kaskad: {n} × {tr(qk)} = {tr(QT)} kW'], None, CIHAZ, sabit=(x + 70, 20))
        S.yazi((x + 70, 62), f'{tr(qk)} kW', 9, YAZ, ic=True)
        S.yazi((x + 70, 43), f'{tg}/{td} °C', 8, YAZ, ic=True)
        # gidiş (üst): emniyet grubu + kazan pompası
        g = S.hat(GID, [(x + 110, BH + 8), (x + 110, Y_G)], dn_k)
        S.brans((x + 110, BH + 30), 'MTY-EMNİYET VENTİLİ', 0, 'EV', 'EMNİYET VENTİLİ (KAZAN)',
                [f'{ev_dn}', f'Açma basıncı {tr(ev_bar)} bar', 'Kapatılamaz bağlantı'], cap=ev_dn)
        TM((x + 110, BH + 75), 0)
        MN((x + 110, BH + 110), 0)
        HP((x + 110, BH + 145), 180)
        if kp:
            POMPA_(g, (x + 110, BH + 185), kp, rot=90, ad=f'KAZAN SİRKÜLASYON POMPASI ({kp.get("ad", "IP-1")})')
            CV(g, (x + 110, BH + 220), dn_k, rot=90)
        V(g, (x + 110, BH + 250), dn_k)
        # baca bağlantısı
        S.hat(BACA, [(x + 30, BH + 12), (x + 30, Y_B)], None, w=3.0)
        # yoğuşma, gaz, dönüş (alt)
        S.hat(YOG, [(x + 20, -8), (x + 20, Y_C)], None)
        gk = S.hat(GAZ, [(x + 60, -8), (x + 60, Y_GZ)], dng_k)
        S.ekle(gk, (x + 60, -38), 'MTY-KURESEL VANA', 'V', 'DOĞALGAZ KÜRESEL VANASI (CİHAZ)',
               [f'{dng_k}', 'TS EN 331, sarı kollu'], cap=dng_k, katman=GAZS)
        S.ekle(gk, (x + 60, -118), 'MTY-ESNEK BAGLANTI', 'V', 'ESNEK BAĞLANTI (GAZ)',
               [f'{dng_k}', 'Metal örgülü, çalışma basıncının 3 katına dayanıklı'], cap=dng_k, katman=GAZS)
        dk = S.hat(DON, [(x + 110, -8), (x + 110, Y_D)], dn_k)
        V(dk, (x + 110, -38), dn_k)
        if i == 0:
            S.yazi((x - 40, BH / 2), f'{n} × {tr(qk)} kW', 10, YAZ, TA.MIDDLE_RIGHT)
            S.yazi((x - 40, BH / 2 - 16), 'KASKAD KAZAN', 10, YAZ, TA.MIDDLE_RIGHT)

    # ---------------------------------------------------------------- denge kabı bölgesi
    x_b = xL + 420.0
    x_a = x_b - 50.0
    x_dk = x_a + 270.0
    y_t = 120.0
    y_b = y_t + BL.DENGE_ALT_Y * BL.DENGE_OLCEK
    # kazan gidiş kollektörü -> hava ayırıcı -> denge kabı
    G = S.hat(GID, [(xs[0] + 110, Y_G), (x_a, Y_G), (x_a, y_t), (x_dk, y_t)], dn_p,
              etiket=f'KAZAN GİDİŞ KOLLEKTÖRÜ {dn_p} - {tg} °C')
    HP((x_a - 40, Y_G), 90)
    V(G, (x_a + 28, y_t), dn_p)
    ha_x = x_a + 52
    S.blok('MTY-HAVA AYIRICI', (ha_x, y_t), 0, 0.25, 'HA', 'HAVA AYIRICI', [f'Bağlantı {dn_p}', 'Mikro kabarcık tipi, otomatik purjörlü'],
           None, CIHAZ, tercih=[(0, 1)], merkez=(ha_x + 46, y_t + 20), kutu=True)
    G['kes'].append((GM.konum(G['pts'], (ha_x + BL.HAVA_AYIRICI[0] * 0.25, y_t))[0],
                     GM.konum(G['pts'], (ha_x + BL.HAVA_AYIRICI[1] * 0.25, y_t))[0]))
    TM((x_a + 175, y_t), 90)
    MN((x_a + 205, y_t), 90)
    V(G, (x_a + 240, y_t), dn_p)
    # denge kabı
    dk_cap = P.get('denge_kabi', {}).get('cap', 'Ø300')
    S.blok('MTY-DENGE KABI ŞEMADA', (x_dk, y_t), 0, BL.DENGE_OLCEK, 'DK', 'DENGE KABI (HİDROLİK AYIRICI)',
           [dk_cap, f'Bağlantı {dn_su(max(q_p, q_s))}', f'Maks. debi {tr(max(q_p, q_s))} m³/h',
            'Hava atıcı + çamur tahliyeli'], None, CIHAZ, tercih=[(0, 1), (1, 0)], merkez=(x_dk + 42, y_t - 60), kutu=True)
    # denge kabı -> tortu ayırıcı -> kazan dönüş kollektörü
    D = S.hat(DON, [(x_dk, y_b), (x_b, y_b), (x_b, Y_D), (xs[0] + 110, Y_D)], dn_p,
              etiket=f'KAZAN DÖNÜŞ KOLLEKTÖRÜ {dn_p} - {td} °C')
    V(D, (x_dk - 28, y_b), dn_p)
    ta_x = x_b + 60
    S.blok('MTY-TORTU &PİSLİK AYIRICI', (ta_x, y_b), 0, 1.0, 'TA', 'TORTU VE PİSLİK AYIRICI',
           [f'Bağlantı {dn_p}', 'Manyetik çubuklu, blöf vanalı'], None, CIHAZ, tercih=[(0, -1)], merkez=(ta_x + 32, y_b - 20), kutu=True)
    D['kes'].append((GM.konum(D['pts'], (ta_x + BL.TORTU[1], y_b))[0], GM.konum(D['pts'], (ta_x, y_b))[0]))
    TM((x_b + 160, y_b), 270)
    V(D, (x_b + 30, y_b), dn_p)
    # kapalı genleşme tankı (dönüş kollektörüne, kilitlenebilir vana ile)
    gt = P.get('genlesme', {'hacim_l': 500})
    x_gt = xL + 235.0
    sgt = 0.55 + 0.25 * min(1.0, gt['hacim_l'] / 1000.0)
    gp = S.hat(DON, [(x_gt, Y_D), (x_gt, Y_D + 60)], 'DN25', etiket='')
    S.ekle(gp, (x_gt, Y_D + 30), 'MTY-KITLENEBILIR VANA', 'V', 'KİLİTLENEBİLİR (MÜHÜRLÜ) VANA',
           ['DN25 PN16', 'Genleşme tankı bağlantısı'], rot=90, cap='DN25')
    ozg = [f'V={tr(gt["hacim_l"], 0)} L', 'Membranlı, kapalı tip']
    if gt.get('on_basinc'):
        ozg.append(f'Ön basınç {tr(gt["on_basinc"])} bar')
    if gt.get('maks_bar'):
        ozg.append(f'Maks. işletme {tr(gt["maks_bar"])} bar')
    S.blok('MTY-GENLEŞME TANKI KOLON', (x_gt, Y_D + 60), 0, sgt, 'GT', 'KAPALI GENLEŞME TANKI', ozg, None, CIHAZ,
           tercih=[(1, 0)], merkez=(x_gt, Y_D + 60 + 70 * sgt), kutu=True)
    S.yazi((x_gt - 56 * sgt - 6, Y_D + 60 + 120 * sgt), f'{tr(gt["hacim_l"], 0)} L', 9, YAZ, TA.MIDDLE_RIGHT)
    # sistem doldurma (dönüş kollektörüne)
    if P.get('doldurma', True):
        x_df = x_gt + 80
        df = S.hat(SOG, [(x_df - 470, -340), (x_df, -340), (x_df, Y_D)], 'DN20', etiket='SİSTEM DOLDURMA DN20')
        V(df, (x_df - 420, -340), 'DN20')
        PT(df, (x_df - 370, -340), 'DN20')
        S.ekle(df, (x_df - 315, -340), 'MTY-OTOMATIK DOLUM VANASI', 'V', 'OTOMATİK DOLUM VANASI',
               ['DN20', 'Basınç ayarlı (1-4 bar), manometreli'], cap='DN20')
        CV(df, (x_df - 260, -340), 'DN20')
        V(df, (x_df, -300), 'DN20')
        S.yazi((x_df - 480, -340), 'ŞEBEKEDEN (YUMUŞATILMIŞ SU)', 9, YAZ, TA.MIDDLE_RIGHT)

    # ---------------------------------------------------------------- yoğuşma + nötralizasyon
    if notr:
        S.hat(YOG, [(xL + 20, Y_C), (-150, Y_C)], None, etiket='YOĞUŞMA SUYU DN25 (PP)')
        S.blok('ROTAS-NOTRALIZASYON', (-150, Y_C), 180, 1, 'NU', 'NÖTRALİZASYON ÜNİTESİ',
               [f'Kapasite ≥ {tr(QT)} kW', 'Granül dolgulu, çıkış pH 6,5-9', 'Yoğuşma suyu pH ≈ 3,5'], None, CIHAZ,
               tercih=[(0, 1)], merkez=(-210, Y_C), kutu=True)
        S.hat(YOG, [(-270, Y_C), (-330, Y_C)], None, etiket='', ok='son')
        S.yazi((-338, Y_C), 'PİS SU TESİSATINA', 9, YAZ, TA.MIDDLE_RIGHT)
    else:
        S.hat(YOG, [(xL + 20, Y_C), (-120, Y_C)], None, etiket='YOĞUŞMA SUYU DN25 (PP)', ok='son')
        S.yazi((-128, Y_C), 'YOĞUŞMA SUYU SİFONLU OLARAK PİS SU TESİSATINA', 9, YAZ, TA.MIDDLE_RIGHT)

    # ---------------------------------------------------------------- doğalgaz hattı
    xg0 = -960.0
    reg = gz.get('regulator')
    x_reg = -620.0
    if reg:
        g1 = S.hat(GAZ, [(xg0, Y_GZ), (x_reg, Y_GZ)], dng_g, etiket=f'{dng_g} - {reg.get("giris", "300 mbar")}')
        g2 = S.hat(GAZ, [(x_reg + 11, Y_GZ), (xL + 60, Y_GZ)], dng, etiket=f'DOĞALGAZ KOLLEKTÖRÜ {dng} - {reg.get("cikis", "21 mbar")}')
        S.blok('ROTAS-REGULATOR', (x_reg, Y_GZ), 0, 1, 'GR', 'GAZ BASINÇ REGÜLATÖRÜ',
               [f'Giriş {reg.get("giris", "300 mbar")} / çıkış {reg.get("cikis", "21 mbar")}', f'Q ≥ {tr(qg)} m³/h',
                'Emniyet kapama (SSV) + tahliye (SRV) donanımlı'], None, GAZS, tercih=[(0, -1)])
        g1['kes'].append((GM.uzunluk(g1['pts']) - 10.5, GM.uzunluk(g1['pts']) + 1))
    else:
        g1 = g2 = S.hat(GAZ, [(xg0, Y_GZ), (xL + 60, Y_GZ)], dng, etiket=f'DOĞALGAZ KOLLEKTÖRÜ {dng}')
    if gz.get('vana', True):
        S.ekle(g1, (xg0 + 40, Y_GZ), 'MTY-KURESEL VANA', 'V', 'DOĞALGAZ ANA KESME VANASI (KAZAN DAİRESİ DIŞI)',
               [dng_g, 'TS EN 331, sarı kollu, kilitlenebilir'], cap=dng_g, katman=GAZS)
    if gz.get('selenoid', True):
        sv = S.ekle(g1, (xg0 + 105, Y_GZ), 'ROTAS-SELENOID', 'SV', 'GAZ SELENOİD VANASI',
                    [dng_g, 'Normalde kapalı, manuel kurmalı', 'Gaz alarmına bağlı'], katman=GAZS, tercih=[(0, -1)])
    S.yazi((xg0 + 96, Y_GZ + 62), 'KAZAN DAİRESİ DIŞI', 8, YAZ, TA.MIDDLE_RIGHT)
    if gz.get('filtre', True):
        S.ekle(g1, (xg0 + 180, Y_GZ), 'MTY-PISLIK TUTUCU', 'GF', 'GAZ FİLTRESİ', [dng_g, '50 µm'], cap=dng_g, katman=GAZS)
    if gz.get('alarm', True):
        S.blok('ROTAS-GAZ-ALARM', (xg0 + 105, Y_GZ + 105), 0, 1, 'GA', 'GAZ ALARM CİHAZI + CO DEDEKTÖRÜ',
               ['Ex-proof, sesli-ışıklı', 'Selenoid vanayı kapatır', 'Üst menfez seviyesinden yüksekte'], None, GAZS,
               tercih=[(1, 0)])
        S.hat(SINYAL, [(xg0 + 105, Y_GZ + 105), (xg0 + 105, Y_GZ + 21)], None, etiket='', kopru=False)
    MN((x_reg + 70 if reg else -560, Y_GZ), 90, 'MANOMETRE (GAZ)', ('0-400 mbar' if reg else '0-60 mbar', 'Musluklu'))
    S.ekle(g2, (x_reg + 130 if reg else -500, Y_GZ), 'MTY-KURESEL VANA', 'V', 'DOĞALGAZ KÜRESEL VANASI (KOLLEKTÖR)',
           [dng, 'TS EN 331, sarı kollu'], cap=dng, katman=GAZS)
    S.yazi((xg0 - 8, Y_GZ), 'DOĞALGAZ GİRİŞİ', 9, YAZ, TA.MIDDLE_RIGHT)
    S.yazi((xg0 - 8, Y_GZ - 16), '(SAYAÇ KAZAN DAİRESİ DIŞINDA)', 8, YAZ, TA.MIDDLE_RIGHT)

    # ---------------------------------------------------------------- baca
    bc = P.get('baca', {})
    x_ch = -130.0
    S.hat(BACA, [(xL + 30, Y_B), (x_ch, Y_B)], None, w=4.0, etiket='')
    S.hat(BACA, [(x_ch, Y_B - 50), (x_ch, Y_B + 230)], None, w=4.0, etiket='')
    S.msp.add_lwpolyline([(x_ch - 22, Y_B + 236), (x_ch, Y_B + 252), (x_ch + 22, Y_B + 236)], dxfattribs={'layer': BACA})
    S.msp.add_line((x_ch - 10, Y_B + 230), (x_ch + 10, Y_B + 230), dxfattribs={'layer': BACA})
    S.blok_baca = None
    S.cihazlar.append(dict(kod='B', ad='BACA (KASKAD ORTAK)', oz=(bc.get('cap', 'Ø250'), bc.get('tip', 'Paslanmaz çelik çift cidarlı'),
                      'TS EN 13384-2 hesabına göre', 'Kollektör kazanlara doğru %3 eğimli, yoğuşma drenajlı'),
                      at=(x_ch, Y_B + 120), ent=None, tercih=[(-1, 0)], boru_aci=90, yon=None))
    S.yazi((x_ch - 14, Y_B + 60), f'BACA {bc.get("cap", "Ø250")}', 9, YAZ, TA.MIDDLE_RIGHT)
    S.yazi((xs[0] + 140 + (PITCH - BW) / 2 if n > 1 else xs[0] + 200, Y_B + 14), 'BACA KOLLEKTÖRÜ', 8, YAZ)

    # ---------------------------------------------------------------- sekonder: kollektörler + zonlar
    x_n = x_dk + BL.DENGE_SAG_X * BL.DENGE_OLCEK
    x_k0 = x_n + 130.0
    sg = S.hat(GID, [(x_n, y_t), (x_k0 - 9, y_t)], dn_s, etiket='')
    sd = S.hat(DON, [(x_k0 - 9, y_b), (x_n, y_b)], dn_s, etiket='')
    TM((x_n + 45, y_t), 90)
    TM((x_n + 45, y_b), 270)
    V(sg, (x_n + 90, y_t), dn_s)
    V(sd, (x_n + 90, y_b), dn_s)
    zx = x_k0 + 70.0
    kg_agiz = kd_agiz = 0
    for z in zonlar:
        for k in range(int(z.get('adet', 1))):
            ad = z['ad'] + (f'.{k + 1}' if z.get('adet', 1) > 1 else '')
            dn = dn_su(z['debi'])
            yedek = z.get('yedek', False)
            gen = 230.0 if yedek else 140.0
            xz = zx + gen / 2 if yedek else zx + 40
            s0 = y_t + 9
            tr_ = S.hat(GID, [(xz, s0), (xz, s0 + 95 if yedek else s0 + 400)], dn,
                        etiket='' if yedek else dn, ok=None if yedek else 'son')
            V(tr_, (xz, s0 + 28), dn)
            PT(tr_, (xz, s0 + 62), dn, rot=90)
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
                up = S.hat(GID, [(xz, yj), (xz, yj + 140)], dn, ok='son')
                TM((xz, yj + 35), 0)
                MN((xz, yj + 75), 180)
                y_ust = yj + 140
            else:
                POMPA_(tr_, (xz, s0 + 115), z, rot=90, ad=pad)
                CV(tr_, (xz, s0 + 160), dn, rot=90)
                V(tr_, (xz, s0 + 198), dn, rot=90)
                TM((xz, s0 + 240), 0)
                MN((xz, s0 + 280), 180)
                y_ust = s0 + 400
            S.yazi((xz, y_ust + 30), f'{ad} {z.get("aciklama", "")}'.strip(), 9, YAZ)
            S.yazi((xz, y_ust + 14), f'GİDİŞ {tg} °C', 8, YAZ)
            dz = S.hat(DON, [(xz, y_b - 9), (xz, y_b - 175)], dn, ok='bas')
            V(dz, (xz, y_b - 40), dn)
            TM((xz, y_b - 80), 0)
            S.yazi((xz, y_b - 189), f'{ad} {z.get("aciklama", "")}'.strip(), 9, YAZ)
            S.yazi((xz, y_b - 205), f'DÖNÜŞ {td} °C', 8, YAZ)
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
        V(bd, (x_bd, y_t + 40), dnb)
        S.blok('ROTAS-BOYLER', (x_by, y_bb), 0, 1, 'BY', 'BOYLER (KULLANIM SICAK SUYU)',
               [f'V={tr(boy["hacim_l"], 0)} L', boy.get('tip', 'Serpantinli, emaye kaplamalı'),
                f'Primer {tg}/{td} °C - kullanım 60 °C'], None, CIHAZ, tercih=[(-1, 0), (0, 1)], merkez=(x_by, y_bb + 130),
               kutu=True)
        S.yazi((x_by, y_bb + 190), f'{tr(boy["hacim_l"], 0)} L', 9, YAZ, ic=True)
        sc = S.hat(SIC, [(x_by, y_bb + 260), (x_by, y_bb + 370)], boy.get('cap', 'DN32'), ok='son')
        TM((x_by, y_bb + 300), 0)
        S.yazi((x_by, y_bb + 384), 'KULLANIM SICAK SUYU', 9, YAZ)
        so = S.hat(SOG, [(x_by, y_b - 180), (x_by, y_bb)], boy.get('cap', 'DN32'), ok=None)
        V(so, (x_by, y_b - 150), boy.get('cap', 'DN32'))
        PT(so, (x_by, y_b - 115), boy.get('cap', 'DN32'), rot=90)
        CV(so, (x_by, y_b - 80), boy.get('cap', 'DN32'), rot=90)
        S.brans((x_by, y_b - 20), 'MTY-EMNİYET VENTİLİ', 0, 'EV', 'EMNİYET VENTİLİ (BOYLER)',
                [boy.get('ev_cap', 'DN20'), f'Açma basıncı {tr(boy.get("ev_bar", 6))} bar', 'Sıhhi su tipi'],
                cap=boy.get('ev_cap', 'DN20'))
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
    S.kollektor(x_k0, x_kg1, y_t)
    S.kollektor(x_k0, x_kd1, y_b)
    S.cihazlar.append(dict(kod='KL', ad='GİDİŞ KOLLEKTÖRÜ', oz=(f'{dn_su(q_s)} eşdeğeri, siyah çelik', f'{kg_agiz} çıkış ağızlı',
                      'Hava purjörü + boşaltma vanalı'), at=(x_k0 + 30, y_t), ent=None, tercih=[(0, -1)], boru_aci=0, yon=None))
    S.cihazlar.append(dict(kod='KL', ad='DÖNÜŞ KOLLEKTÖRÜ', oz=(f'{dn_su(q_s)} eşdeğeri, siyah çelik', f'{kd_agiz} giriş ağızlı',
                      'Boşaltma vanalı'), at=(x_k0 + 30, y_b), ent=None, tercih=[(0, 1)], boru_aci=0, yon=None))
    HP((x_k0 + 20, y_t + 9), 90)

    # ---------------------------------------------------------------- köprü, çizim, numara, etiket
    S.kopruler()
    S.boru_ciz()
    satir = S.numarala()
    # başlık
    xmin, xmax = xg0 - 260, max(x_kg1, x_kd1) + (430 if boy else 120)
    ytop = Y_B + 330
    S.yazi(((xmin + xmax) / 2, ytop), 'KAZAN DAİRESİ PRENSİP ŞEMASI', 32, BAS, maske=False)
    S.yazi(((xmin + xmax) / 2, ytop - 40), 'ÖLÇEKSİZ', 14, BAS, maske=False)
    if P.get('proje'):
        S.yazi(((xmin + xmax) / 2, ytop - 66), P['proje'], 12, YAZ, maske=False)
    if P.get('deneme', True):
        S.yazi((xmin + 120, ytop), 'DENEME', 40, 'ROTAS-ISITMA-BASLIK', maske=False)
    S.etiketle()
    # cihaz listesi + notlar
    ty = -470.0
    xe, ye = S.tablo(satir, xmin, ty)
    notlar = P.get('notlar') or [t for t in NOTLAR if notr or 'nötralizasyon' not in t]
    if not notr:
        notlar.insert(6, 'Yoğuşma suları sifonlu olarak pis su tesisatına verilecektir.')
    nx = xe + 80
    S.msp.add_text('NOTLAR', height=18, dxfattribs={'layer': BAS, 'style': 'ROTAS'}).set_placement((nx, ty - 20), align=TA.BOTTOM_LEFT)
    for i, s in enumerate(notlar):
        S.msp.add_text(f'{i + 1}. {s}', height=11, dxfattribs={'layer': YAZ, 'style': 'ROTAS', 'width': WF}).set_placement(
            (nx, ty - 50 - i * 22), align=TA.BOTTOM_LEFT)
    from ezdxf import bbox as zb
    bb = zb.extents(S.msp, fast=True)
    x0f, y0f, x1f, y1f = bb.extmin.x - 60, bb.extmin.y - 60, bb.extmax.x + 60, bb.extmax.y + 60
    S.msp.add_lwpolyline([(x0f, y0f), (x1f, y0f), (x1f, y1f), (x0f, y1f)],
                         close=True, dxfattribs={'layer': PAFTA, 'const_width': 3})
    S.doc.saveas(cikti)
    return S


NOTLAR = [
    'Kazanlar kaskad kontrol panosu ile sırayla devreye alınacak, dış hava kompanzasyonlu çalıştırılacaktır.',
    'Her kazan gidişinde kapatılamaz emniyet ventili, termometre, manometre ve otomatik hava purjörü bulunacaktır.',
    'Kapalı genleşme tankı dönüş hattına kilitlenebilir (mühürlü) vana ile bağlanacaktır.',
    'DN65 ve üzeri vanalar kelebek, DN50 ve altı küresel vana olacaktır.',
    'Gaz sayacı ve ana kesme vanası kazan dairesi dışında olacak; selenoid vana gaz alarm cihazına bağlanacaktır.',
    'Doğalgaz hattı çapları ön boyut olup doğalgaz projesine göre kesinleştirilecektir.',
    'Yoğuşma suları nötralizasyon ünitesinden geçirilerek pis su tesisatına verilecektir.',
    'Baca TS EN 13384-2 hesabına göre paslanmaz çelik çift cidarlı yapılacaktır.',
    'Dönüş hatları kesikli çizgi ile gösterilmiştir; şema ölçeksizdir.',
]


if __name__ == '__main__':
    P = json.load(open(sys.argv[1], encoding='utf-8'))
    S = ciz(P, sys.argv[2])
    for u in S.uyarilar:
        print('UYARI:', u)
    if len(sys.argv) > 3:
        import onizleme
        onizleme.png(sys.argv[2], sys.argv[3])
