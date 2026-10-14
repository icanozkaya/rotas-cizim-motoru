# -*- coding: utf-8 -*-
"""Parça (hat) listesi, yükler, çaplar, kritik devre ve pompa — KOLEKTÖRLÜ dağıtım (R2).

Ağaç:  merkezi: kazan dairesi → K1/K2 kolon parçaları (kat kat) → daire giriş hattı (kolon T → kalorimetre seti →
       kolektör) → devre (kolektör → radyatör, PEX)
       kombi  : daire giriş hattı (kombi → kolektör) → devre."""
import hidrolik as hd
import ag


def rad_yuk(r, esas):
    return r['ver'] if esas == 'radyator' else r['m']['q'] / r['m']['adet']


class Ag:
    def __init__(self, P, M):
        self.P, self.M = P, M
        self.parcalar = []
        self.esas = P['yuk_esasi']
        self.z = dict(P['zeta'])
        for k, v in (('T_gecis', 0.5), ('kalorimetre', 8.0), ('balans_vanasi', 5.0), ('kollektor', 1.5)):
            self.z.setdefault(k, v)
        self.rad_bag = P.get('rad_baglanti_m', 1.0)

    def yeni(self, **k):
        k['id'] = len(self.parcalar)
        k.setdefault('cocuk', [])
        k.setdefault('zeta', [])
        k.setdefault('Qr', 0.0)
        k.setdefault('malzeme', 'celik')
        self.parcalar.append(k)
        if k.get('ebeveyn') is not None:
            self.parcalar[k['ebeveyn']]['cocuk'].append(k['id'])
        return k

    # ------------------------------------------------------------------ daire
    def daire(self, pl, ebeveyn, kat, dad):
        z = self.z
        bes = pl['besleme']
        if pl['sistem'] == 'merkezi':
            zet = [('T ayrılma (gidiş)', 1, z['T_ayrilma']), ('T birleşme (dönüş)', 1, z['T_birlesme']),
                   ('Küresel vana (set, gidiş+dönüş)', 4, z['kuresel_vana']), ('Pislik tutucu', 1, z['pislik_tutucu']),
                   ('Kalorimetre (debi ölçer)', 1, z['kalorimetre']), ('Balans vanası', 1, z['balans_vanasi']),
                   ('Kolektör giriş (gidiş+dönüş)', 2, z['kollektor'])]
            ad = 'Daire giriş hattı: kolon T → kalorimetre seti → kolektör'
        else:
            zet = [('Kolektör giriş (gidiş+dönüş)', 2, z['kollektor'])]
            ad = 'Daire giriş hattı: kombi → kolektör'
        g = self.yeni(tur='giris', ad=ad, kat=kat, daire=dad, L=2 * ag.uzunluk(bes) / 100.0, kose=ag.kose_sayisi(bes),
                      zeta=zet, ebeveyn=ebeveyn['id'] if ebeveyn else None, malzeme='pex')
        for dv in pl['devreler']:
            r = dv['rad']
            p = self.yeni(tur='devre', ad=f"D{dv['no']} {r['m']['ad']} {r['m']['no']}" + (f" ({r['sira_no']})" if r['m']['adet'] > 1 else ''),
                          kat=kat, daire=dad, devre=dv['no'], L=2 * ag.uzunluk(dv['pts']) / 100.0 + self.rad_bag,
                          kose=ag.kose_sayisi(dv['pts']), ebeveyn=g['id'], rad=r, malzeme='pex',
                          zeta=[('Kolektör çıkış (gidiş+dönüş)', 2, z['kollektor']), ('Radyatör', 1, z['radyator']),
                                ('Termostatik radyatör vanası', 1, z['termostatik_vana']), ('Dönüş rakoru', 1, z['donus_rakoru'])])
            p['Qr'] = rad_yuk(r, self.esas)
        return g

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
        b = P['boru']; x = P.get('pex', {})
        for p in self.parcalar:
            if p['malzeme'] == 'pex':
                c = hd.cap_sec_pex(p['Q'], M['dT'], M['tort'], x.get('Rmax_mmSS_m', b['Rmax_mmSS_m']), x.get('wmax_m_s', 0.6),
                                   x.get('min', 'Ø16x2'))
            else:
                c = hd.cap_sec(p['Q'], M['dT'], M['tort'], b['Rmax_mmSS_m'], b['wmax_m_s'], b['dn_min'])
            p.update(dn=c['dn'], inc=c['inc'], di=c['di'], R=c['R'], w=c['w'], V=c['V'])
            dz = self.z['dirsek_kucuk'] if c['di'] < 25 else self.z['dirsek_buyuk']
            zet = list(p['zeta'])
            if p['kose']:
                zet.append(('Dirsek / kavis 90° (gidiş+dönüş)', 2 * p['kose'], dz if p['malzeme'] == 'celik' else 0.5))
            p['zeta_tum'] = zet
            p['sz'] = sum(n * zz for _, n, zz in zet)
            p['RL'] = p['R'] * p['L']
            p['Z'] = hd.Z_hesap(p['sz'], p['w'], M['tort'])
        en = None
        for p in self.parcalar:
            if 'rad' not in p:
                continue
            yol = []; q = p
            while q is not None:
                yol.append(q); q = self.parcalar[q['ebeveyn']] if q.get('ebeveyn') is not None else None
            top = sum(x_['RL'] + x_['Z'] for x_ in yol)
            p['devre_top'] = top
            if en is None or top > en[0] + 1e-9:
                en = (top, yol)
        self.kritik = en[1]
        for i, q in enumerate(self.kritik):
            q['kno'] = i + 1
        self.kritik_top = en[0]
        return self


def merkezi_ag(P, M, plan_fn):
    A = Ag(P, M); z = A.z; mp = P['merkezi']
    kazan = A.yeni(tur='kazan', ad='Kazan dairesi ana hat (zon pompası → K1 ayrımı)', kat='B', daire=None,
                   L=2 * mp['kazan_dairesi_hat_m'], kose=4,
                   zeta=[('Küresel vana', 2, z['kuresel_vana']), ('Çek valf', 1, z['cek_valf']), ('Pislik tutucu', 1, z['pislik_tutucu'])],
                   ebeveyn=None)
    katlar = [k for k in M['katlar'] if k['daireler']]
    kolonlar = {}
    for i, dad in enumerate(['A', 'B']):
        if i == 0:
            onceki = kazan
        else:
            onceki = A.yeni(tur='kolon_dip', ad=f'K{i + 1} kolon dibi bağlantısı (K1 ayrımı → K{i + 1})', kat='B', daire=dad,
                            L=2 * mp['kolon_kazan_arasi_m'], kose=2, zeta=[('T geçiş (gidiş+dönüş)', 2, z['T_gecis'])],
                            ebeveyn=kazan['id'])
        seg = []
        for j, k in enumerate(katlar):
            if j:
                zz = [('T geçiş (gidiş+dönüş)', 2, z['T_gecis'])]
            elif i == 0:
                zz = [('T ayrılma (gidiş)', 1, z['T_ayrilma']), ('T birleşme (dönüş)', 1, z['T_birlesme']),
                      ('Dirsek 90° (gidiş+dönüş)', 2, z['dirsek_buyuk']), ('Kolon dibi küresel vana (gidiş+dönüş)', 2, z['kuresel_vana'])]
            else:
                zz = [('Dirsek 90° (gidiş+dönüş)', 2, z['dirsek_buyuk']), ('Kolon dibi küresel vana (gidiş+dönüş)', 2, z['kuresel_vana'])]
            s = A.yeni(tur='kolon', ad=f'K{i + 1} kolon {(katlar[j - 1]["ad"] if j else "BODRUM KAT")} → {k["ad"]}', kat=k['kod'], daire=dad,
                       L=2 * P['kat_yuksekligi_m'], kose=0, zeta=zz, ebeveyn=onceki['id'], kolon=i + 1)
            seg.append(s); onceki = s
            A.daire(plan_fn(k, dad), s, k['kod'], dad)
        kolonlar[dad] = seg
    A.kolonlar = kolonlar
    return A.hesapla()


def kombi_ag(P, M, plan_fn):
    A = Ag(P, M)
    for k in [k for k in M['katlar'] if k['daireler']]:
        for dad in k['daireler']:
            A.daire(plan_fn(k, dad), None, k['kod'], dad)
    return A.hesapla()


def pompa(A, P, M):
    Qt = A.kritik[-1]['Q']
    Qkcal = Qt * 0.859845
    V = Qkcal / (M['dT'] * 1000.0)
    H_mmSS = A.kritik_top
    if P['sistem'] == 'merkezi':
        mp = P['merkezi']
        Hp = H_mmSS * (1 + mp['emniyet_orani']) + mp['kazan_dairesi_ek_kayip_mmSS']
    else:
        Hp = H_mmSS * 1.10
    return dict(Q_W=Qt, Q_kcal=Qkcal, V=V, H_kritik_mmSS=H_mmSS, H_mmSS=Hp, H_mSS=Hp / 1000.0)


def malzeme(A, P, M, pf):
    """malzeme metrajı (bina toplamı): boru (çap → m, gidiş+dönüş), kolektör (ağız → adet), set, radyatör"""
    boru = {}
    for p in A.parcalar:
        if p['tur'] == 'radyator':
            continue
        L = p['L'] - (A.rad_bag if p['tur'] == 'devre' else 0.0)
        key = (('PE-Xc/Al/PE-X çok katmanlı boru ' + p['dn']) if p['malzeme'] == 'pex'
               else f"Siyah çelik boru {p['dn']} ({p['inc']})")
        boru[key] = boru.get(key, 0.0) + L
    kol, rad = {}, {}
    n_daire = 0
    for k in [k for k in M['katlar'] if k['daireler']]:
        for dad in k['daireler']:
            n_daire += 1
            pl = pf(k, dad)
            n = len(pl['devreler'])
            kol[n] = kol.get(n, 0) + 1
            for r in pl['radyatorler']:
                key = (f"Panel radyatör {r['model']} {r['boy'] * 1000:.0f} mm" if r['tip'] != 'Banyopan'
                       else f"Havlupan (banyopan) {r['boy'] * 1000:.0f} mm")
                rad[key] = rad.get(key, 0) + 1
    return dict(boru=boru, kolektor=kol, radyator=rad, daire=n_daire, n_rad=sum(rad.values()))
