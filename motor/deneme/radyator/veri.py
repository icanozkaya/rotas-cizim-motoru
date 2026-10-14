# -*- coding: utf-8 -*-
"""Kullanıcının ısı kaybı (ik.xls) ve radyatör seçim (rad.xlsx) dosyalarını okur; kat/daire/radyatör modeli kurar."""
import os, sys, json
_KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_KOK, '..', '..', 'izoder_rapor'))
import oku   # motor/izoder_rapor/oku.py (dokunulmaz, yalnız import)


def parametre(yol=None):
    with open(yol or os.path.join(_KOK, 'parametre.json'), encoding='utf-8') as f:
        return json.load(f)


def _no(s):
    """'1-2-3-4-5 01' -> ('1-2-3-4-5', '01')"""
    s = s.strip(); i = s.rfind(' ')
    return s[:i].strip(), s[i + 1:].strip()


def model(P):
    genel, R = oku.radyator(P['veri']['radyator'])
    ik = oku.isi_kaybi(P['veri']['isi_kaybi'])
    ikq = {}
    for r in ik:
        ikq.setdefault(r['no'].replace('  ', ' '), r['top'])
    rad = {}
    for r in R:
        grp, no = _no(r['no'])
        rad[(grp, no)] = dict(no=no, grup=grp, ad=str(r['ad']).strip(), ti=r['ti'], q=float(r['q']), boy=float(r['boy']),
                              model=str(r['model']).strip(), ver=float(r['ver']), adet=int(r['adet'] or 1),
                              tip=str(r['tip']).strip(), q_ik=ikq.get(r['no']))
    tg, td = float(genel['tg']), float(genel['td'])
    katlar = []
    for k in P['katlar']:
        kk = dict(k); kk['daireler'] = {}
        if k['veri']:
            for dad, nolar in P['daireler'][k['veri']].items():
                mahaller = [rad[(k['veri'], n)] for n in nolar]
                kk['daireler'][dad] = mahaller
        katlar.append(kk)
    uyar = []
    for (g, n), r in rad.items():
        if r['q_ik'] is not None and abs(r['q_ik'] - r['q']) > 1:
            uyar.append(f'{g} {n}: rad.xlsx ısı kaybı {r["q"]:.0f} W ≠ ik.xls {r["q_ik"]:.0f} W')
    return dict(genel=genel, tg=tg, td=td, dT=tg - td, tort=(tg + td) / 2, katlar=katlar, rad=rad, ik=ik, uyari=uyar)


if __name__ == '__main__':
    P = parametre(); M = model(P)
    print(M['genel'], M['dT'])
    for k in M['katlar']:
        for d, ms in k['daireler'].items():
            print(k['ad'], d, [(m['no'], m['ad'], m['adet'], m['boy']) for m in ms], sum(m['ver'] * m['adet'] for m in ms))
    print(M['uyari'])
