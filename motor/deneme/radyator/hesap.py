# -*- coding: utf-8 -*-
"""Parça (hat) listesi, yükler, çaplar, kritik devre ve pompa."""
import math
from shapely.geometry import Point
import hidrolik as hd

EPS = 1e-3


def rad_yuk(r, esas):
    return r['ver'] if esas == 'radyator' else r['m']['q'] / r['m']['adet']


class Ag:
    def __init__(self, P, M):
        self.P, self.M = P, M
        self.parcalar = []
        self.esas = P['yuk_esasi']
        self.z = dict(P['zeta']); self.z.setdefault('T_gecis', 0.5)
        self.rad_bag = P.get('rad_baglanti_m', 1.0)

    def yeni(self, **k):
        k['id'] = len(self.parcalar)
        k.setdefault('cocuk', [])
        k.setdefault('zeta', [])
        k.setdefault('Qr', 0.0)
        self.parcalar.append(k)
        if k.get('ebeveyn') is not None:
            self.parcalar[k['ebeveyn']]['cocuk'].append(k['id'])
        return k

    # ------------------------------------------------------------------ daire içi parçalar
    def daire(self, pl, ebeveyn, kat, dad, kok_zeta):
        yollar = pl['yollar']
        yol_bas = {}                        # yol id -> ilk parça
        bitis = {}                          # (yol id, s) -> o noktada biten parça

        def isle(y, ust_parca, cocuk_mu):
            ls = y['ls']; Ltop = ls.length
            cocuklar = [z for z in yollar if z['ebeveyn'] == y['id']]
            olay = sorted(set([round(z['s0'], 3) for z in cocuklar] +
                              [round(r['s_yak'], 3) for r in y['rads'] if r['s_uzak'] < Ltop - 1]))
            olay = [s for s in olay if EPS < s < Ltop - EPS]
            sinir = [0.0] + olay + [Ltop]
            onceki = ust_parca
            koseler = [ls.project(Point(p)) for p in y['pts'][1:-1]]
            for k in range(len(sinir) - 1):
                a, b = sinir[k], sinir[k + 1]
                zet = []
                if k == 0:
                    if cocuk_mu:
                        zet += [('T ayrılma (gidiş)', 1, self.z['T_ayrilma']), ('T birleşme (dönüş)', 1, self.z['T_birlesme'])]
                    else:
                        zet += kok_zeta
                else:
                    zet += [('T geçiş (gidiş+dönüş)', 2, self.z['T_gecis'])]
                nk = sum(1 for s in koseler if a + EPS < s < b - EPS)
                son = (k == len(sinir) - 2)
                prc = self.yeni(tur='daire', ad=f"{y['ad']}", kat=kat, daire=dad, yol=y['id'], s0=a, s1=b,
                                L=2 * (b - a) / 100.0 + (self.rad_bag if son else 0.0), kose=nk, zeta=zet,
                                ebeveyn=onceki['id'] if onceki else None)
                if son:
                    r = [r for r in y['rads'] if r['s_uzak'] >= Ltop - 1][0]
                    prc['rad'] = r
                    prc['zeta'] += [('Radyatör', 1, self.z['radyator']), ('Termostatik radyatör vanası', 1, self.z['termostatik_vana']),
                                    ('Dönüş rakoru', 1, self.z['donus_rakoru'])]
                    prc['Qr'] = rad_yuk(r, self.esas)
                bitis[(y['id'], round(b, 3))] = prc
                if k == 0:
                    yol_bas[y['id']] = prc
                onceki = prc
            # yol üzerindeki ara (T) radyatörler
            for r in y['rads']:
                if r['s_uzak'] >= Ltop - 1:
                    continue
                ust = bitis[(y['id'], round(r['s_yak'], 3))]
                prc = self.yeni(tur='radyator', ad=f"{y['ad']} rad.{r['sira_no']}", kat=kat, daire=dad, yol=y['id'],
                                s0=r['s_yak'], s1=r['s_yak'], L=self.rad_bag, kose=0, ebeveyn=ust['id'], rad=r,
                                zeta=[('T ayrılma (gidiş)', 1, self.z['T_ayrilma']), ('T birleşme (dönüş)', 1, self.z['T_birlesme']),
                                      ('Radyatör', 1, self.z['radyator']), ('Termostatik radyatör vanası', 1, self.z['termostatik_vana']),
                                      ('Dönüş rakoru', 1, self.z['donus_rakoru'])])
                prc['Qr'] = rad_yuk(r, self.esas)
            for z in cocuklar:
                ust = bitis[(y['id'], round(z['s0'], 3))]
                isle(z, ust, True)

        isle(yollar[0], ebeveyn, False)
        return yol_bas[0]

    # ------------------------------------------------------------------ yük, çap, kayıp
    def hesapla(self):
        P = self.P; M = self.M
        def topla(p):
            q = p['Qr'] + sum(topla(self.parcalar[c]) for c in p['cocuk'])
            p['Q'] = q
            return q
        for p in self.parcalar:
            if p.get('ebeveyn') is None:
                topla(p)
        b = P['boru']
        for p in self.parcalar:
            c = hd.cap_sec(p['Q'], M['dT'], M['tort'], b['Rmax_mmSS_m'], b['wmax_m_s'], b['dn_min'])
            p.update(dn=c['dn'], inc=c['inc'], di=c['di'], R=c['R'], w=c['w'], V=c['V'])
            dz = self.z['dirsek_kucuk'] if c['di'] < 25 else self.z['dirsek_buyuk']
            zet = list(p['zeta'])
            if p['kose']:
                zet.append(('Dirsek 90° (gidiş+dönüş)', 2 * p['kose'], dz))
            p['zeta_tum'] = zet
            p['sz'] = sum(n * z for _, n, z in zet)
            p['RL'] = p['R'] * p['L']
            p['Z'] = hd.Z_hesap(p['sz'], p['w'], M['tort'])
        # kritik devre
        en = None
        for p in self.parcalar:
            if 'rad' not in p:
                continue
            yol = []; q = p
            while q is not None:
                yol.append(q); q = self.parcalar[q['ebeveyn']] if q.get('ebeveyn') is not None else None
            top = sum(x['RL'] + x['Z'] for x in yol)
            p['devre_top'] = top
            if en is None or top > en[0] + 1e-9:
                en = (top, yol)
        self.kritik = en[1]                     # radyatör → kök sırası
        for i, q in enumerate(self.kritik):
            q['kno'] = i + 1
        self.kritik_top = en[0]
        return self


def merkezi_ag(P, M, plan_fn):
    """kazan → kolonlar (K1: A daireleri, K2: B daireleri) → kat tees → daire ağları"""
    A = Ag(P, M); z = A.z; mp = P['merkezi']
    kazan = A.yeni(tur='kazan', ad='Kazan dairesi ana hat (kazan → K1 ayrımı)', kat='B', daire=None, L=2 * mp['kazan_dairesi_hat_m'],
                   kose=4, zeta=[('Kazan', 1, z['kazan']), ('Küresel vana', 4, z['kuresel_vana']), ('Çek valf', 1, z['cek_valf']),
                                 ('Pislik tutucu', 1, z['pislik_tutucu'])], ebeveyn=None)
    katlar = [k for k in M['katlar'] if k['daireler']]
    kolonlar = {}
    for i, dad in enumerate(['A', 'B']):
        if i == 0:
            onceki = kazan                 # K1 kazan dairesi hattındaki T'den yükselir
        else:
            onceki = A.yeni(tur='kolon_dip', ad=f'K{i + 1} kolon dibi bağlantısı (K1 ayrımı → K{i + 1})', kat='B', daire=dad,
                            L=2 * mp['kolon_kazan_arasi_m'], kose=2,
                            zeta=[('T geçiş (gidiş+dönüş)', 2, z['T_gecis'])], ebeveyn=kazan['id'])
        seg = []
        for j, k in enumerate(katlar):
            if j:
                zz = [('T geçiş (gidiş+dönüş)', 2, z['T_gecis'])]
            elif i == 0:
                zz = [('T ayrılma (gidiş)', 1, z['T_ayrilma']), ('T birleşme (dönüş)', 1, z['T_birlesme']), ('Dirsek 90° (gidiş+dönüş)', 2, z['dirsek_buyuk'])]
            else:
                zz = [('Dirsek 90° (gidiş+dönüş)', 2, z['dirsek_buyuk'])]
            s = A.yeni(tur='kolon', ad=f'K{i + 1} kolon {(katlar[j - 1]["ad"] if j else "BODRUM KAT")} → {k["ad"]}', kat=k['kod'], daire=dad,
                       L=2 * P['kat_yuksekligi_m'], kose=0, zeta=zz, ebeveyn=onceki['id'], kolon=i + 1)
            seg.append(s); onceki = s
            pl = plan_fn(k, dad)
            A.daire(pl, s, k['kod'], dad, [('T ayrılma (gidiş)', 1, z['T_ayrilma']), ('T birleşme (dönüş)', 1, z['T_birlesme']),
                                           ('Küresel vana (gidiş+dönüş)', 2, z['kuresel_vana'])])
        kolonlar[dad] = seg
    A.kolonlar = kolonlar
    return A.hesapla()


def kombi_ag(P, M, plan_fn):
    A = Ag(P, M)
    katlar = [k for k in M['katlar'] if k['daireler']]
    for k in katlar:
        for dad in k['daireler']:
            pl = plan_fn(k, dad)
            A.daire(pl, None, k['kod'], dad, [])
    return A.hesapla()


def pompa(A, P, M):
    Qt = A.kritik[-1]['Q']            # kök parça: merkezi = kazan, kombi = en kritik daire
    Qkcal = Qt * 0.859845
    V = Qkcal / (M['dT'] * 1000.0)                       # m3/h ; 20 K'de V = Q/20000
    H_mmSS = A.kritik_top
    if P['sistem'] == 'merkezi':
        mp = P['merkezi']
        Hp = H_mmSS * (1 + mp['emniyet_orani']) + mp['kazan_dairesi_ek_kayip_mmSS']
    else:
        Hp = H_mmSS * 1.10
    return dict(Q_W=Qt, Q_kcal=Qkcal, V=V, H_kritik_mmSS=H_mmSS, H_mmSS=Hp, H_mSS=Hp / 1000.0)
