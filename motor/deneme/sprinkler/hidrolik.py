# -*- coding: utf-8 -*-
"""Sprinkler hidrolik hesabı — TS EN 12845, Q = K·√P, Hazen-Williams C=120 (06_YANGIN.md §1, §3.3, §11).
- işletme alanı (en uzak alan): dikdörtgen, uzun kenar branşmana paralel ve ≥ 1,2·√A; aday pencerelerin HEPSİ
  hesaplanır, kolon çıkışında en yüksek basınç isteyen alan "hidrolik en uzak alan" seçilir;
- ağaç üzerinde kesin çözüm: verilen kolon basıncında başlık debileri K√P, boru kayıpları HW + eşdeğer boy
  (dirsek / te dönüşü), sabit nokta yinelemesi; kolon basıncı en elverişsiz başlık q_min'i sağlayana kadar artırılır;
- pompa: kolon çıkış basıncı + besleme hattı kaybı + vana kayıpları + statik yükseklik.
"""
import math
import networkx as nx
from kurallar import SINIF, hw_birim, hiz, ES_DIRSEK, ES_TE, IC_CAP, dn_sec, V_MAX


def _yon(a, b):
    return (round(math.copysign(1, b[0] - a[0])) if abs(b[0] - a[0]) > 0.1 else 0,
            round(math.copysign(1, b[1] - a[1])) if abs(b[1] - a[1]) > 0.1 else 0)


def esdeger_boy(T, root):
    """her kenar (a->b) için fitting eşdeğer boyu (m) ve tipi"""
    U = T.to_undirected(as_view=True)
    for a, b in T.edges:
        d = T[a][b]['dn']
        preds = list(T.predecessors(a))
        if not preds:      # kolondan yataya dönüş
            T[a][b]['fit'], T[a][b]['Le'] = 'dirsek', ES_DIRSEK[d]
            continue
        p = preds[0]
        if _yon(p, a) == _yon(a, b):
            T[a][b]['fit'], T[a][b]['Le'] = '', 0.0
        elif U.degree(a) >= 3:
            T[a][b]['fit'], T[a][b]['Le'] = 'te', ES_TE[d]
        else:
            T[a][b]['fit'], T[a][b]['Le'] = 'dirsek', ES_DIRSEK[d]


def coz(T, root, aktif, K, C=120.0):
    """aktif: {düğüm: q_min (l/dk)} -> kesin dağılım. Dönüş dict(P, Q, Pn, Qe, qh)"""
    # yalnız aktif başlıklara giden kenarlar
    gerek = set()
    for h in aktif:
        gerek.update(nx.shortest_path(T, root, h))
    S = T.subgraph(gerek).copy()
    for a, b in S.edges:
        S[a][b].update(T[a][b])
    sira = list(nx.topological_sort(S))
    pmin = {h: (q / K) ** 2 for h, q in aktif.items()}
    Pr = max(pmin.values()) * 1.2
    Pn = {n: Pr for n in sira}
    Qe = {}
    for _dis in range(200):
        for _ic in range(300):
            Qn = {}
            for n in reversed(sira):
                q = K * math.sqrt(max(Pn[n], 0.0)) if n in aktif else 0.0
                for c in S.successors(n):
                    q += Qn[c]
                Qn[n] = q
            fark = 0.0
            Pn2 = {root: Pr}
            for n in sira:
                for c in S.successors(n):
                    e = S[n][c]
                    Qe[(n, c)] = Qn[c]
                    dp = hw_birim(Qn[c], e['dn'], C) * (e['L'] / 100.0 + e['Le'])
                    Pn2[c] = Pn2[n] - dp
            for n in sira:
                yeni = 0.5 * Pn[n] + 0.5 * Pn2[n]
                fark = max(fark, abs(yeni - Pn[n]))
                Pn[n] = yeni
            if fark < 1e-7:
                break
        eksik = max(pmin[h] - Pn[h] for h in aktif)
        if abs(eksik) < 1e-6:
            break
        Pr += eksik
        for n in sira:
            Pn[n] += eksik
    qh = {h: K * math.sqrt(Pn[h]) for h in aktif}
    return dict(P=Pr, Q=Qn[root], Pn=Pn, Qe=Qe, qh=qh, S=S)


def aday_alanlar(net, mahaller):
    """her mahalde işletme alanı pencereleri (başlık kümeleri)"""
    T, root, heads, yer = net['T'], net['root'], net['heads'], net['yer']
    dist = nx.single_source_dijkstra_path_length(T.to_undirected(), root, weight='L')
    hep = list(heads)
    out = []
    for m in mahaller:
        y = yer[m['ad']]
        s = SINIF[m['sinif']]
        A = s['alan']
        a_bas = (y['Su'] / 100.0) * (y['Sv'] / 100.0)
        N = math.ceil(A / a_bas - 1e-9)
        nb = min(len(y['cols']), math.ceil(1.2 * math.sqrt(A) / (y['Su'] / 100.0) - 1e-9))
        nr = min(len(y['rows']), math.ceil(N / nb))
        cols, rows = sorted(y['cols']), sorted(y['rows'])
        from yerlesim import xy
        for j0 in range(len(rows) - nr + 1):
            for i0 in range(len(cols) - nb + 1):
                W = [xy(y['axis'], cols[i], rows[j]) for j in range(j0, j0 + nr) for i in range(i0, i0 + nb)]
                W = [(round(p[0], 1), round(p[1], 1)) for p in W]
                if len(W) > N:
                    W.sort(key=lambda h: -dist[h])
                    W = W[:N]
                elif len(W) < N:
                    cx = sum(p[0] for p in W) / len(W)
                    cy = sum(p[1] for p in W) / len(W)
                    dis = sorted([h for h in hep if h not in W], key=lambda h: math.dist(h, (cx, cy)))
                    W += dis[:N - len(W)]
                out.append(dict(mahal=m['ad'], sinif=m['sinif'], A=A, N=N, nb=nb, nr=nr, W=W))
    return out


def hesapla(net, P):
    hp = P.get('hidrolik', {})
    T, root, heads = net['T'], net['root'], net['heads']
    C = hp.get('C', 120.0)
    esdeger_boy(T, root)
    sonuc = None
    adaylar = aday_alanlar(net, P['mahaller'])
    for ad in adaylar:
        s = SINIF[ad['sinif']]
        K = hp.get('K', s['K'])
        aktif = {}
        for h in ad['W']:
            sh = SINIF[heads[h]['sinif']]
            aktif[h] = max(sh['yog'] * heads[h]['cov'], K * math.sqrt(sh['pmin']))
        r = coz(T, root, aktif, K, C)
        r.update(ad, aktif=aktif, K=K)
        if sonuc is None or r['P'] > sonuc['P'] + 1e-9:
            sonuc = r
    r = sonuc
    s = SINIF[r['sinif']]
    # düğüm adları: aktif başlık S1.. (uzaktan yakına), diğerleri N1..
    S = r['S']
    dist = nx.single_source_dijkstra_path_length(S.to_undirected(), root, weight='L')
    ad = {root: P.get('kolon_hatti', {}).get('ad', 'SP-1')}
    hs = sorted(r['aktif'], key=lambda h: -dist[h])
    for i, h in enumerate(hs):
        ad[h] = f'S{i + 1}'
    diger = sorted([n for n in S.nodes if n not in ad], key=lambda n: -dist[n])
    for i, n in enumerate(diger):
        ad[n] = f'N{i + 1}'
    satir = []
    for n in sorted(S.nodes, key=lambda n: -dist[n]):
        if n == root:
            continue
        p = list(S.predecessors(n))[0]
        e = S[p][n]
        Q = r['Qe'][(p, n)]
        J = hw_birim(Q, e['dn'], C)
        Lm = e['L'] / 100.0
        satir.append(dict(den=ad[n], ye=ad[p], bas='K' + str(int(r['K'])) if n in r['aktif'] else '-',
                          P=r['Pn'][n], q=r['qh'].get(n, 0.0), Q=Q, dn=e['dn'], d=IC_CAP[e['dn']], L=Lm,
                          Le=e['Le'], fit=e['fit'], Lt=Lm + e['Le'], J=J, dp=J * (Lm + e['Le']), Pye=r['Pn'][p],
                          v=hiz(Q, e['dn'])))
    vmax = max(x['v'] for x in satir)
    # pompa
    Qs = r['Q']
    ek = hp.get('ek_debi_lpm', 0.0)
    Qp = Qs + ek
    bdn = hp.get('besleme_dn', 100)
    Lb = hp.get('besleme_L_m', 25.0)
    dp_bes = hw_birim(Qp, bdn, C) * Lb
    dp_van = hp.get('vana_kaybi_bar', 0.35)
    stat = hp.get('statik_m', 4.0) / 10.2
    Pp = r['P'] + dp_bes + dp_van + stat
    t = s['sure']
    ozet = dict(sinif=r['sinif'], mahal=r['mahal'], yog=s['yog'], A=r['A'], N=len(r['aktif']), K=r['K'],
                pmin=s['pmin'], qmin=min(r['aktif'].values()), Qs=Qs, P_kolon=r['P'], ek=ek, Qp=Qp,
                besleme_dn=bdn, besleme_L=Lb, dp_bes=dp_bes, dp_van=dp_van, statik_m=hp.get('statik_m', 4.0),
                stat=stat, Pp=Pp, Hp=Pp * 10.2, Qp_m3h=Qp * 0.06, sure=t, V=Qp * t / 1000.0, vmax=vmax,
                v_ok=vmax <= V_MAX, toplam_bas=len(heads), aday=len(adaylar),
                qmax=max(r['qh'].values()), qort=Qs / len(r['aktif']))
    return dict(r=r, ad=ad, satir=satir, ozet=ozet)
