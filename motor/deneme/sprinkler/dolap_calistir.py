# -*- coding: utf-8 -*-
"""Yangın dolabı otomatik yerleşimi + kontrol + kolon şeması.
Kullanım:
  python3 motor/deneme/sprinkler/dolap_calistir.py motor/deneme/sprinkler/ornek_girdi/kat_ofis_dolap.json \
          [--cikti proje/denemeler/sprinkler/kat_ofis_dolap] [--png /scratch/onizleme]
Çıktılar: <cikti>_plan.dxf (sprinkler + dolap planı, kapsama haritası, tablolar), <cikti>_kolon_semasi.dxf.
Girdi (JSON): sprinkler_girdi (sprinkler modülü girdisi, göreli yol), merdivenler[], cikislar[], katlar[], pompa{},
dolap{} (dolap_kurallar.VARSAYILAN'ı ezer), pompa_grubu_girdi (numara senkronu için)."""
import copy
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ag import tasarla                       # noqa: E402
from hidrolik import hesapla                 # noqa: E402
from kontrol import kontrol                  # noqa: E402
from dolap_kurallar import ayarlar           # noqa: E402
from dolap import hidrolik                   # noqa: E402
from dolap_cizim import ciz_dolapli, tablolar_ve_kaydet   # noqa: E402
import dolap_sema                            # noqa: E402

DEPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def calistir(girdi, cikti_kok=None, png=None):
    D = json.load(open(girdi, encoding='utf-8'))
    gd = os.path.dirname(os.path.abspath(girdi))
    P = json.load(open(os.path.join(gd, D['sprinkler_girdi']), encoding='utf-8'))
    P = copy.deepcopy(P)
    if D.get('proje'):
        P['proje'] = D['proje']
    k = ayarlar(D)
    katlar = sorted(D['katlar'], key=lambda q: q['kot_m'])
    pk = D['pompa']
    z_p = pk['kot_m'] + pk.get('eksen_m', 0.5)
    top = katlar[-1]
    hp = P.setdefault('hidrolik', {})
    # sprinkler hesabı en üst (hidrolik en elverişsiz) kata göre: statik yük + kolon boyu ana hatta eklenir
    hp['statik_m'] = round(top['kot_m'] + D.get('tavan_m', 3.2) - z_p, 2)
    hp['besleme_L_m'] = hp.get('besleme_L_m', 25.0) + max(0.0, top['kot_m'] - pk['kot_m'])
    hp['ek_debi_lpm'] = 0.0                  # dolap debisi dolap.hidrolik içinde eklenir
    net = tasarla(P)
    hes = hesapla(net, P)
    cikti_kok = cikti_kok or os.path.join(DEPO, 'proje', 'denemeler', 'sprinkler', D.get('ad', 'dolap'))
    plan = cikti_kok + '_plan.dxf'
    sema = cikti_kok + '_kolon_semasi.dxf'
    c, son = ciz_dolapli(P, D, k, net, hes, plan)
    hd = hidrolik(D, k, son['kolonlar'], son['T'], son['dolaplar'], hes['ozet'], P)
    tablolar_ve_kaydet(c, P, D, k, hes, net, son, hd, plan)
    rap = kontrol(plan, P['dis_hat'], len(c.Z) + 1)
    rap['etiketsiz'] = c.etiketsiz
    from dolap_kontrol import kontrol_dolap
    rd = kontrol_dolap(plan, P, D, k)
    # pompa grubu numaraları (motor/deneme/pompa_grubu) — ayrı süreç
    liste, pg = [], None
    if D.get('pompa_grubu_girdi'):
        pgg = os.path.normpath(os.path.join(gd, D['pompa_grubu_girdi']))
        pg = json.load(open(pgg, encoding='utf-8'))
        tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), '_dolap_pg_tmp.dxf')
        r = subprocess.run([sys.executable, os.path.join(HERE, 'dolap_pompa_no.py'), pgg, tmp], capture_output=True, text=True)
        if r.returncode == 0:
            liste = json.loads(r.stdout.strip().splitlines()[-1])
        else:
            print('UYARI pompa grubu numaraları okunamadı:', r.stderr[-400:])
    S, sayim = dolap_sema.ciz(D, P, k, hes, net, son, hd, liste, sema, pg)
    rs = dolap_sema.kontrol(S, sema)
    if png:
        from calistir import onizle
        onizle(plan, png + '_plan.png')
        onizle(sema, png + '_sema.png')
    return dict(P=P, D=D, k=k, hes=hes, son=son, hd=hd, rap=rap, rd=rd, rs=rs, plan=plan, sema=sema, sayim=sayim)


if __name__ == '__main__':
    a = sys.argv[1:]
    cik = a[a.index('--cikti') + 1] if '--cikti' in a else None
    png = a[a.index('--png') + 1] if '--png' in a else None
    R = calistir(a[0], cik, png)
    s, hd, rp = R['son'], R['hd'], R['son']['rap']
    print(f"{R['P'].get('proje')}: {len(s['dolaplar'])} dolap/kat ({', '.join(d['no'] + ':' + d['mahal'] for d in s['dolaplar'])}), "
          f"{len(s['kolonlar'])} YG kolonu, aday {s['aday']}")
    print(f"  kapsama %{100 * rp['oran']:.1f} ({rp['kapsanan_m2']:.1f}/{rp['hedef_m2']:.1f} m², kapsanmayan {rp['kapsanmayan_m2']:.1f} m²), "
          f"lüle 3 m ile %{100 * rp['oran_jet3']:.1f}; dolaplar arası ≤{rp['aralik_max_m']:.0f} m: {rp['aralik_ok']}")
    print(f"  pompa Q={hd['Qs']:.0f}+{hd['Qd']:.0f}={hd['Q']:.0f} l/dk ({hd['Q_m3h']:.1f} m³/h), P_spr={hd['P_spr']:.2f} bar, "
          f"P_dolap={hd['P_dolap']:.2f} bar -> H={hd['H']:.1f} mSS ({hd['yonetici']}), depo {hd['V']:.1f} m³, "
          f"alt dolap {hd['p_alt']:.1f} bar{' (BDV)' if hd['bdd'] else ''}")
    print('  uyarılar:', s['uyari'])
    print('  sprinkler kontrol HATA:', R['rap']['HATA'], {x: v for x, v in R['rap'].items() if v and x not in ('HATA',)})
    print('  dolap kontrol:', R['rd'])
    print('  şema kontrol:', R['rs'])
    print('  ÇIKTI:', R['plan'], R['sema'])
