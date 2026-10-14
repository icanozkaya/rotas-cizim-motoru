# -*- coding: utf-8 -*-
"""Radyatörlü ısıtma denemesi: kat planları + kalorifer kolon şeması + boru çapı hesap tablosu (DXF, R2018).
Kullanım: python3 calistir.py [parametre.json] [--sistem merkezi|kombi] [--png]"""
import os, sys, json, argparse
_KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _KOK)
import veri, ag, hesap, plan, sema, tablo
import ciz as C

DEPO = os.path.abspath(os.path.join(_KOK, '..', '..', '..'))
CIKTI = os.path.join(DEPO, 'proje', 'denemeler', 'radyator')


def plan_fabrikasi(P):
    cache = {}

    def pf(k, dad):
        key = (k['veri'], dad)
        if key not in cache:
            a = ag.daire_plani(k['daireler']['A'], P['sistem'])
            cache[(k['veri'], 'A')] = a
            cache[(k['veri'], 'B')] = ag.aynala(a)
        return cache[key]
    return pf


KAT_ON = {'Z': 'Z', '1-2-3-4-5': '', 'Ç': 'Ç'}


def kat_planlari(cz, P, M, A, pf, y0=0.0):
    tipler = []
    for k in M['katlar']:
        if k['daireler'] and k['veri'] not in [t['veri'] for t in tipler]:
            tipler.append(k)
    ad = {'Z': 'ZEMİN KAT', '1-2-3-4-5': 'NORMAL KATLAR (1-2-3-4-5. KAT TİPİK)', 'Ç': 'ÇATI KATI'}
    x = 0.0
    for k in tipler:
        pa, pb = pf(k, 'A'), pf(k, 'B')
        dx, dy = x + 300.0, y0 + 300.0
        plan.mimari(cz, [pa, pb], dx, dy, P['sistem'])
        hatlar = {}
        for dad, pl in (('A', pa), ('B', pb)):
            hatlar[dad] = plan.borular(cz, pl, dx, dy, P['sistem'], dict(kat_on=KAT_ON[k['veri']]))
        cihazlar(cz, P, [pa, pb], dx, dy, k, A)
        # bu kat tipinin temsilci katı (ör. 1. normal) parçaları
        kod = k['kod']
        for dad, pl in (('A', pa), ('B', pb)):
            prc = [p for p in A.parcalar if p['kat'] == kod and p['daire'] == dad]
            plan.hat_etiketleri(cz, pl, hatlar[dad], prc, dx, dy, set())
        for dad, pl in (('A', pa), ('B', pb)):
            plan.mahal_etiketleri(cz, pl, dx, dy, KAT_ON[k['veri']])
        # başlık
        cz.yazi((dx + 1400, dy - 170), f"{ad[k['veri']]} RADYATÖR TESİSATI PLANI.........ÖLÇEK: 1 / 50", 30, 'ROTAS-BASLIK')
        cz.yazi((dx + 1400, dy + 1130), 'DENEME – temsili mahal yerleşimi (mimari proje yok; mahaller daire tipik planı olarak temsil edilmiştir)',
                16, 'ROTAS-DENEME')
        if k['veri'] == '1-2-3-4-5':
            cz.yazi((dx + 1400, dy - 215), 'Hat etiketleri 1. normal kat yüklerine göredir; diğer normal katlarda aynı yerleşim.', 11, 'ROTAS-YAZI')
        pafta_cerceve(cz, dx - 200, dy - 280, dx + 3000, dy + 1220)
        x += 3400.0
    return x


def pafta_cerceve(cz, x0, y0, x1, y1):
    cz.pl([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'ROTAS-PAFTA', w=2.0, kapali=True, engel=False)


def cihazlar(cz, P, pls, dx, dy, k, A):
    T = lambda p: (p[0] + dx, p[1] + dy)
    if P['sistem'] == 'merkezi':
        for i, pl in enumerate(pls):
            kx, ky = pl['kok']
            # kolon (gidiş + dönüş borusu) — MTY-BORU KOLON
            rot = -90.0
            cz.blok('MTY-BORU KOLON', T((kx - 5.0, ky + 5.0)), rot, 1.0, 1.0, 'ROTAS-CIHAZ', ozn={'K': f'K{i + 1}'},
                    ozn_h={'K': 20.0}, ozn_rot=0.0)
            # daire giriş vanaları (gidiş + dönüş) — MTY-KURESEL VANA
            vx = (kx + ag.GEN) / 2 if i == 0 else (kx + ag.GENIS_TOP - ag.GEN) / 2
            dn = 'DN20'
            ust = [p for p in A.parcalar if p['kat'] == k['kod'] and p['daire'] == ('A' if i == 0 else 'B') and p['tur'] == 'daire']
            if ust:
                dn = ust[0]['dn']
            for j, yy in enumerate((ky - ag.H, ky + ag.H)):
                cz.blok('MTY-KURESEL VANA', T((vx, yy)), 0.0, 0.45, 0.45, 'ROTAS-VANA', ozn={'CAP': ''})
            cz.yazi(T((vx, ky - 22)), f'V-{2 * i + 1:02d}/{2 * i + 2:02d}', 6, 'ROTAS-VANA')
    else:
        for i, pl in enumerate(pls):
            kb = pl['kombi']
            if kb.get('ayna'):
                cz.blok('MTY-KOMBİ', T((kb['p'][0], kb['p'][1] + 30.0)), 180.0, 1.0, 1.0, 'ROTAS-CIHAZ')
                tx = kb['p'][0] + 100
            else:
                cz.blok('MTY-KOMBİ', T(kb['p']), 0.0, 1.0, 1.0, 'ROTAS-CIHAZ')
                tx = kb['p'][0] - 100
            cz.yazi(T((tx, 120)), f"HERMETİK KOMBİ {P['kombi']['kapasite_kW']} kW", 8, 'ROTAS-CIHAZ')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('parametre', nargs='?', default=os.path.join(_KOK, 'parametre.json'))
    ap.add_argument('--sistem', default=None)
    ap.add_argument('--png', action='store_true')
    a = ap.parse_args()
    P = veri.parametre(a.parametre)
    if a.sistem:
        P['sistem'] = a.sistem
    M = veri.model(P)
    pf = plan_fabrikasi(P)
    A = hesap.merkezi_ag(P, M, pf) if P['sistem'] == 'merkezi' else hesap.kombi_ag(P, M, pf)
    pomp = hesap.pompa(A, P, M)
    os.makedirs(CIKTI, exist_ok=True)
    cz = C.Cizim()
    genislik = kat_planlari(cz, P, M, A, pf, 0.0)
    sema.ciz(cz, P, M, A, pf, x0=0.0, y0=-4200.0)
    tablo.ciz(cz, P, M, A, pomp, x0=0.0, y0=-9000.0)
    yol = os.path.join(CIKTI, f'radyator_{P["sistem"]}.dxf')
    if os.path.exists(yol):
        os.remove(yol)
    cz.doc.saveas(yol)
    print('yazıldı:', yol)
    print('pompa:', json.dumps({k: round(v, 3) for k, v in pomp.items()}, ensure_ascii=False))
    print('kritik:', [(p['kno'], p['ad'], p['kat'], p['daire'], p['dn']) for p in A.kritik])
    return yol


if __name__ == '__main__':
    main()
