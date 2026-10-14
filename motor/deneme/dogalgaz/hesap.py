"""Doğalgaz iç tesisat hesabı (21 mbar, konut): ağ kurma, eşzamanlılık, debi, çap, basınç kaybı, hız.

Kaynak: kutuphane/arastirma/07_ISITMA_DOGALGAZ.md §6.3 (EPDK iç tesisat yönetmeliğine dayanan
dağıtım şirketi şartnamelerinin ortak içeriği). AKSAGAZ (Sakarya) teknik esaslarıyla TEYİT EDİLECEK.

Formüller
  Cihaz debisi      Q = kW·860 / (Hu·η)                    [m³/h]   (Hu kcal/m³)
  Sürtünme kaybı    ΔP_R = 23200·d·L·Q^1,82·D^-4,82          [mbar]   (Renouard, alçak basınç; D iç çap mm)
  Yerel kayıp       ΔP_Z = 3,97·10⁻³·Σξ·V²                  [mbar]
  Yükseklik etkisi  ΔP_H = -0,049·h                         [mbar]   (h: yükselişte +, kayıp azalır)
  Hız               V = Q / (3600·π·D²/4)                   [m/s]
"""
import math

# TS EN 10255 orta seri çelik boru: DN -> (dış çap, et kalınlığı, iç çap mm, inç)
BORU = [
    ('DN15', 21.3, 2.6, 16.1, '1/2"'),
    ('DN20', 26.9, 2.6, 21.7, '3/4"'),
    ('DN25', 33.7, 3.2, 27.3, '1"'),
    ('DN32', 42.4, 3.2, 36.0, '1 1/4"'),
    ('DN40', 48.3, 3.2, 41.9, '1 1/2"'),
    ('DN50', 60.3, 3.6, 53.1, '2"'),
    ('DN65', 76.1, 3.6, 68.9, '2 1/2"'),
    ('DN80', 88.9, 4.0, 80.9, '3"'),
    ('DN100', 114.3, 4.5, 105.3, '4"'),
]
DN_IC = {b[0]: b[3] for b in BORU}
DN_SIRA = [b[0] for b in BORU]

KCAL_KW = 860.0


class Hat:
    """Bir boru parçası (düğüm a -> düğüm b)."""

    def __init__(self, no, a, b, tur, L, h, xi, dn_min, aciklama, yol3d, bolum=None):
        self.no, self.a, self.b, self.tur = no, a, b, tur
        self.L, self.h, self.xi = L, h, xi
        self.dn_min, self.aciklama = dn_min, aciklama
        self.yol3d = yol3d            # şema için 3B nokta listesi (ölçeksiz şema koordinatı, cm)
        self.bolum = bolum            # bağımsız bölüm (daire) no
        self.cihazlar = []            # beslenen cihaz listesi (ad)
        self.n_bb = 0                 # beslenen bağımsız bölüm sayısı
        self.Q_top = 0.0
        self.f = 1.0
        self.Q = 0.0
        self.dn = None
        self.semboller = []           # (tür, t 0..1 yol üstünde, öznitelik dict)

    # -- hesap
    def hesapla(self, gaz):
        D = DN_IC[self.dn]
        self.D = D
        self.V = self.Q / 3600.0 / (math.pi * (D / 1000.0) ** 2 / 4.0)
        self.R = 23200.0 * gaz['bagil_yogunluk'] * self.Q ** 1.82 * D ** -4.82   # mbar/m
        self.dPR = self.R * self.L
        self.dPZ = 3.97e-3 * self.xi * self.V ** 2
        self.dPH = -0.049 * self.h
        self.dP = self.dPR + self.dPZ + self.dPH


def esz_f(n, esz):
    """Eşzamanlılık katsayısı f(n). Tablo JSON'dan; yoksa varsayılan."""
    if n <= 1:
        return 1.0
    if n > 100:
        return esz.get('f_100_ustu', 0.397)
    tab = {int(k): v for k, v in esz.get('tablo', {}).items()}
    if tab:
        ks = sorted(k for k in tab if k <= n)
        if ks:
            return tab[ks[-1]]
    return esz.get('varsayilan', 1.0)


def cihaz_debi(c, gaz):
    if c.get('debi'):
        return float(c['debi'])
    return c['kW'] * KCAL_KW / (gaz['Hu_kcal_m3'] * gaz['verim'])


def cihaz_kw(c, gaz):
    if c.get('kW'):
        return float(c['kW'])
    return c['debi'] * gaz['Hu_kcal_m3'] / KCAL_KW   # anma ısıl yük (alt ısıl değer üzerinden)


class Ag:
    """Servis kutusu -> ana vana -> sayaç kollektörü -> sayaçlar -> daire hatları -> cihazlar."""

    def __init__(self, P):
        self.P = P
        self.gaz = P['gaz']
        self.hatlar = []
        self.daireler = []            # dict: no, kat, taraf, x, hatlar...
        self.kurulum()

    def _hat(self, *a, **k):
        h = Hat(len(self.hatlar) + 1, *a, **k)
        self.hatlar.append(h)
        return h

    # ---------------------------------------------------------------- ağ
    def kurulum(self):
        P, G = self.P, self.P['geometri']
        kh = P['kat_yuksekligi']                 # m
        dt = P['daire_tipi']
        # şema sırası: sol daireler kat artarak, sağ daireler kat azalarak (dallar kesişmesin)
        sol = sorted([d for d in P['daireler'] if d['taraf'] == 'sol'], key=lambda d: d['kat'])
        sag = sorted([d for d in P['daireler'] if d['taraf'] == 'sag'], key=lambda d: -d['kat'])
        sira = sol + sag
        dx = G['sema_aralik']                    # şema: kolonlar arası (cm, ölçeksiz)
        zk = G['sema_kollektor_z']
        for i, d in enumerate(sira):
            d = dict(d)
            d['x'] = i * dx
            d['cihazlar'] = [dict(c) for c in d.get('cihazlar', dt['cihazlar'])]
            for c in d['cihazlar']:
                c['Q'] = cihaz_debi(c, self.gaz)
                c['kWg'] = cihaz_kw(c, self.gaz)
            d['Q_cihaz'] = sum(c['Q'] for c in d['cihazlar'])
            d['Q_bb'] = max(d['Q_cihaz'], P['eszamanlilik']['bb_min_debi'])
            self.daireler.append(d)

        # node adları: 'SK', 'AKV', 'T0..', 'S0..' (sayaç vanası), 'F..' (daire ayrımı), 'K..', 'O..'
        x0 = self.daireler[0]['x']
        xsk = x0 - G['sema_sk_x']
        xakv = x0 - G['sema_akv_x']
        zsk = G['sema_sk_z']
        zana = G['sema_ana_z']
        # 1) bina bağlantı hattı: servis kutusu (regülatör çıkışı) -> ana kesme vanası
        h1 = self._hat('0', '1', 'baglanti', G['L_baglanti'], G['h_baglanti'], G['xi_baglanti'], 'DN25',
                       'Bina bağlantı hattı (servis kutusu → ana kesme vanası)',
                       [(xsk, 0, zsk), (xsk, 0, zana), (xakv, 0, zana)])
        h1.semboller.append(('AKV', 1.0, {}))
        # 2) ana vana -> kollektör başı
        xk0 = x0 - G['sema_tap_dx']
        h2 = self._hat('1', '2', 'ana', G['L_ana'], G['h_ana'], G['xi_ana'], 'DN25',
                       'Ana hat (ana kesme vanası → sayaç kollektörü)',
                       [(xakv, 0, zana), (xk0 - 20, 0, zana), (xk0 - 20, 0, zk), (xk0, 0, zk)])
        self.hat_bina = [h1, h2]
        onceki = '2'
        self.kollektor = []
        n = len(self.daireler)
        for i, d in enumerate(self.daireler):
            xt = d['x'] - G['sema_tap_dx']
            tnode = onceki
            # kollektör parçası (önceki taptan bu tapa) - ilk tap kollektör başında
            if i > 0:
                xp = self.daireler[i - 1]['x'] - G['sema_tap_dx']
                tnode = f'T{i}'
                hk = self._hat(onceki, tnode, 'kollektor', G['L_kollektor'], 0.0, G['xi_kollektor'], 'DN25',
                               f'Sayaç kollektörü ({self.daireler[i-1]["no"]}→{d["no"]} arası)',
                               [(xp, 0, zk), (xt, 0, zk)])
                self.kollektor.append(hk)
                onceki = tnode
            d['tap_node'] = tnode
            # sayaç bağlantısı: kollektörden sayaç vanasına (sayaç girişine)
            zs = G['sema_sayac_z']
            xin = d['x'] - G['sema_sayac_w'] * 0.3
            ht = self._hat(tnode, f'S{i}', 'sayac_baglanti', G['L_sayac_baglanti'], G['h_sayac_baglanti'],
                           G['xi_sayac_baglanti'], 'DN25', f'{d["no"]} sayaç bağlantısı (kollektör → sayaç vanası)',
                           [(xt, 0, zk), (xt, 0, zs + G['sema_sayac_h'] + 15), (xin, 0, zs + G['sema_sayac_h'] + 15),
                            (xin, 0, zs + G['sema_sayac_h'])], bolum=d['no'])
            ht.semboller.append(('SV', 0.35, {}))   # sayaç vanası düşey parçada
            d['h_tap'] = ht
            # daire hattı: sayaç çıkışı -> daire içi ayrım (kolon + yatay)
            xout = d['x'] + G['sema_sayac_w'] * 0.3
            ztop = d['kat'] * G['sema_kat'] + G['sema_daire_z']
            yy = G['sema_dal'] * (1 if d['taraf'] == 'sol' else -1)
            Lk = d['kat'] * kh + G['h_daire_giris'] - G['h_sayac_cikis'] + G['L_daire_yatay']
            hk_ = d['kat'] * kh + G['h_daire_giris'] - G['h_sayac_cikis']
            hr = self._hat(f'S{i}', f'F{i}', 'daire', round(Lk, 2), round(hk_, 2), G['xi_daire'], 'DN25',
                           f'{d["no"]} daire hattı (sayaç → daire içi ayrım)',
                           [(xout, 0, zs + G['sema_sayac_h']), (xout, 0, ztop), (xout, yy, ztop)], bolum=d['no'])
            hr.semboller.append(('DV', 0.93, {}))   # daire girişi kapama vanası (yatay parçada)
            d['h_daire'] = hr
            d['F'] = (xout, yy, ztop)
            # cihaz hatları
            d['h_cihaz'] = []
            sgn = 1 if d['taraf'] == 'sol' else -1
            for j, c in enumerate(d['cihazlar']):
                cg = G['cihaz'][c['ad']]
                if cg['yon'] == 'devam':      # daire hattı doğrultusunda devam, sonra iniş
                    p1 = (xout, yy + sgn * cg['sema_L'], ztop)
                    yol = [d['F'], p1, (p1[0], p1[1], ztop - cg['sema_dus'])]
                else:                         # 'asagi': ayrım noktasından doğrudan iniş
                    yol = [d['F'], (xout, yy, ztop - cg['sema_dus'])]
                hc = self._hat(f'F{i}', f'{c["ad"][0]}{i}', 'cihaz', cg['L'], -cg['dus'], cg['xi'], cg['dn_min'],
                               f'{d["no"]} {c["ad"].lower()} hattı', yol, bolum=d['no'])
                hc.semboller.append(('CV', 0.80, {}))   # cihaz vanası düşey parçada
                hc.cihazlar = [c['ad']]
                hc.Q_top = c['Q']
                hc.cihaz = c
                d['h_cihaz'].append(hc)
        # debiler
        esz = self.P['eszamanlilik']
        for d in self.daireler:
            d['h_tap'].n_bb = d['h_daire'].n_bb = 1
            d['h_tap'].Q_top = d['h_daire'].Q_top = d['Q_bb']
            d['h_tap'].cihazlar = d['h_daire'].cihazlar = [c['ad'] for c in d['cihazlar']]
            for hc in d['h_cihaz']:
                hc.n_bb = 1
        alt = self.daireler[:]
        for i, hk in enumerate(self.kollektor):
            akis = self.daireler[i + 1:]
            hk.n_bb = len(akis)
            hk.Q_top = sum(d['Q_bb'] for d in akis)
        for h in self.hat_bina:
            h.n_bb = len(alt)
            h.Q_top = sum(d['Q_bb'] for d in alt)
        for h in self.hatlar:
            if h.tur == 'cihaz':
                h.f = 1.0
            else:
                h.f = esz_f(h.n_bb, esz)
                if h.n_bb > 1:
                    h.cihazlar = [f'{h.n_bb} bağımsız bölüm']
            h.Q = h.Q_top * h.f

    # ---------------------------------------------------------------- yollar
    def yol_sayac_oncesi(self, d):
        i = self.daireler.index(d)
        return self.hat_bina + self.kollektor[:i] + [d['h_tap']]

    def yol_sayac_sonrasi(self, d, hc):
        return [d['h_daire'], hc]

    # ---------------------------------------------------------------- çap seçimi
    def cap_sec(self):
        L = self.P['sinirlar']
        for h in self.hatlar:
            k = DN_SIRA.index(h.dn_min)
            h.dn = DN_SIRA[k]
            h.hesapla(self.gaz)
            while h.V > L['hiz'] and k < len(DN_SIRA) - 1:
                k += 1
                h.dn = DN_SIRA[k]
                h.hesapla(self.gaz)
        for _ in range(200):
            bozuk = None
            for d in self.daireler:
                on = self.yol_sayac_oncesi(d)
                if sum(h.dP for h in on) > L['servis_sayac'] + 1e-9:
                    bozuk = on
                    break
                for hc in d['h_cihaz']:
                    so = self.yol_sayac_sonrasi(d, hc)
                    if sum(h.dP for h in so) > L['sayac_cihaz'] + 1e-9 or \
                            sum(h.dP for h in on + so) > L['toplam'] + 1e-9:
                        bozuk = so
                        break
                if bozuk:
                    break
            if not bozuk:
                return True
            aday = [h for h in bozuk if h.dn != DN_SIRA[-1]]
            if not aday:
                return False
            h = max(aday, key=lambda h: h.dPR + h.dPZ)
            h.dn = DN_SIRA[DN_SIRA.index(h.dn) + 1]
            h.hesapla(self.gaz)
        return False

    # ---------------------------------------------------------------- kontrol özeti
    def kontroller(self):
        L = self.P['sinirlar']
        out = []
        for d in self.daireler:
            on = sum(h.dP for h in self.yol_sayac_oncesi(d))
            for hc in d['h_cihaz']:
                so = sum(h.dP for h in self.yol_sayac_sonrasi(d, hc))
                out.append(dict(daire=d['no'], cihaz=hc.cihaz['ad'], on=on, so=so, top=on + so,
                                ok_on=on <= L['servis_sayac'] + 1e-9, ok_so=so <= L['sayac_cihaz'] + 1e-9,
                                ok_top=on + so <= L['toplam'] + 1e-9))
        return out

    def hiz_ok(self):
        return all(h.V <= self.P['sinirlar']['hiz'] for h in self.hatlar)
