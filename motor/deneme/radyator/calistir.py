# -*- coding: utf-8 -*-
"""Radyatörlü ısıtma denemesi: kat planları + kalorifer kolon şeması + boru çapı hesap tablosu (DXF, R2018).
Kullanım: python3 calistir.py [parametre.json] [--sistem merkezi|kombi] [--png]"""
import os, sys, json, argparse
_KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _KOK)
import veri, ag, hesap, plan, sema, tablo
import ciz as C
import semb

DEPO = os.path.abspath(os.path.join(_KOK, '..', '..', '..'))
CIKTI = os.path.join(DEPO, 'proje', 'denemeler', 'radyator')


def plan_fabrikasi(P):
    cache = {}

    def pf(k, dad):
        key = (k['veri'], dad)
        if key not in cache:
            a = ag.daire_plani(k['daireler']['A'], P['sistem'], P.get('mimari'))
            if a['sorun']:
                raise ValueError('güzergâh sorunu: ' + '; '.join(a['sorun']))
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
        kayit = {}
        for dad, pl in (('A', pa), ('B', pb)):
            kayit[dad] = plan.borular(cz, pl, dx, dy, dict(kat_on=KAT_ON[k['veri']]))
        for dad, pl in (('A', pa), ('B', pb)):
            plan.cihazlar(cz, pl, dx, dy, P, KAT_ON[k['veri']])
        for dad, pl in (('A', pa), ('B', pb)):
            plan.radyator_etiketleri(cz, pl, kayit[dad], dx, dy, KAT_ON[k['veri']])
        for dad, pl in (('A', pa), ('B', pb)):
            prc = [p for p in A.parcalar if p['kat'] == k['kod'] and p['daire'] == dad]
            plan.devre_etiketleri(cz, pl, kayit[dad], prc, dx, dy)
        for dad, pl in (('A', pa), ('B', pb)):
            plan.mahal_etiketleri(cz, pl, dx, dy, KAT_ON[k['veri']])
            plan.tefris_yazilari(cz, pl, dx, dy)
        cz.yazi((dx + 1400, dy - 170), f"{ad[k['veri']]} RADYATÖR TESİSATI PLANI (KOLEKTÖRLÜ).........ÖLÇEK: 1 / 50", 30, 'ROTAS-BASLIK')
        cz.yazi((dx + 1400, dy + 1130), 'DENEME – temsili mahal yerleşimi (mimari proje yok; pencere, kapı ve tefriş temsilîdir)',
                16, 'ROTAS-DENEME')
        if k['veri'] == '1-2-3-4-5':
            cz.yazi((dx + 1400, dy - 215), 'Hat etiketleri 1. normal kat yüklerine göredir; diğer normal katlarda aynı yerleşim.', 11, 'ROTAS-YAZI')
        pafta_cerceve(cz, dx - 200, dy - 280, dx + 3000, dy + 1220)
        x += 3400.0
    return x


def pafta_cerceve(cz, x0, y0, x1, y1):
    cz.pl([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'ROTAS-PAFTA', w=2.0, kapali=True, engel=False)


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
    sm = sema.ciz(cz, P, M, A, pf, pomp, x0=2000.0, y0=-4200.0)
    MZ = hesap.malzeme(A, P, M, pf)
    tx, ty = tablo.ciz(cz, P, M, A, pomp, x0=0.0, y0=-9000.0 - (1900.0 if P['sistem'] == 'merkezi' else 0.0), pf=pf, MZ=MZ)
    # pafta sonu: kullanılan sembollerin lejantı + adet tablosu (semboller modülü otomatik_lejant)
    ly = -9000.0 - (1900.0 if P['sistem'] == 'merkezi' else 0.0) + 280.0
    cz.yazi((tx + 300.0, ly + 60.0), 'LEJANT VE SEMBOL ADET TABLOSU (çizimdeki bloklardan otomatik)', 30, 'ROTAS-BASLIK', maske=False)
    semb.lejant(cz.doc, tx + 200.0, ly)
    rev = 'R3'
    if P['sistem'] == 'merkezi':
        # ONAYLI kazan dairesi paftası (plan + kesit + kısmi görünüş) — tüm çizimin sağına, kolon şeması tabanı hizasında.
        # R5: kolon şemasında prensip şeması YOK (kullanıcı reddi); bodrum "KAZAN DAİRESİNE" okuyla bu paftaya bağlanır.
        rev = 'R5'
        from ezdxf import bbox
        bb = bbox.extents(cz.msp, fast=True)
        kd = sm.kdh
        k = sema.kazan_dairesi_paftasi(cz, kd, bb.extmax.x + 500.0, -4260.0)
        with open(os.path.join(CIKTI, f'radyator_merkezi_{rev}_kazan_dairesi.json'), 'w', encoding='utf-8') as f:
            json.dump(k.girdi, f, ensure_ascii=False, indent=1)
        print('kazan dairesi paftası:', [round(v) for v in k], f"{kd['adet']}×{kd['kw']:.0f} kW", 'yeniden ad:', k.yeniden_ad)
        for u in k.uyarilar:
            print('  kazan dairesi:', u)
    yol = os.path.join(CIKTI, f'radyator_{P["sistem"]}_{rev}.dxf')
    if os.path.exists(yol):
        os.remove(yol)
    cz.doc.saveas(yol)
    print('yazıldı:', yol)
    print('pompa:', json.dumps({k: round(v, 3) for k, v in pomp.items()}, ensure_ascii=False))
    print('kritik:', [(p['kno'], p['ad'], p['kat'], p['daire'], p['dn']) for p in A.kritik])
    print('malzeme:', json.dumps(MZ, ensure_ascii=False))
    return yol


if __name__ == '__main__':
    main()
