"""yerden2 — geliştirme: tek daire için kollektör/ayak çözümü (tam koşu ≈ 18 dk yerine daire başına ≈ 1 dk).

    python3 motor/yerden2/yi_daire.py hazirla            # 3 katın ayaksız tasarımı -> /tmp/claude-0/y2/pre_<kat>.pkl
    python3 motor/yerden2/yi_daire.py coz Z 1 [2 3 ...]   # kat Z, daire 1 (...) : ayaklar + ölçüler + PNG

PNG'ler /tmp/claude-0/y2/daire/ içine: mahaller, serpantin (kırmızı), ayaklar (mavi), kombi hattı (yeşil),
kollektör (siyah). Ölçüler: ayaklı devre, kombi hattı, hol boru boyu ve borusuz cep (kontrolörün ölçüsü),
oda/salon yoğunluğu (mimari m²), uç aralığı 15 olmayan devre, ayak kesişmesi.
"""
import copy
import os
import pickle
import sys
import time

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)

import serpantin as S  # noqa: E402
import yerden as Y  # noqa: E402
from shapely.geometry import LineString  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

ONB = '/tmp/claude-0/y2'
CIK = ONB + '/daire'


def hazirla():
    doc = Y.belge()
    kutular = Y.mimari_kopyala(doc)
    Y.AYAKLAR = False
    for k in Y.KATLAR:
        t0 = time.time()
        KT = Y.kat_tasarla(k, kutular, [], cep_ac=False)
        pickle.dump(KT, open('%s/pre_%s.pkl' % (ONB, k), 'wb'))
        print('[hazirla] kat %s %.0f s' % (k, time.time() - t0), flush=True)


def cep(P, boru):
    ic = P.buffer(-20)
    if ic.is_empty:
        return 0.0
    bos = ic.difference(boru.buffer(12)).buffer(-15).buffer(15)
    if bos.is_empty:
        return 0.0
    return max(g.area for g in getattr(bos, 'geoms', [bos])) / 1e4


def olc(k, dno, od, son):
    hatlar = [LineString([p[:2] for p in Y.tam_devre(c)]) for o in od for c in o['tasarim']['devreler']]
    kombi = []
    if son and son.get('kombi_hat'):
        kombi = [LineString(son['kombi_hat']['gidis']), LineString(son['kombi_hat']['donus'])]
    boru = unary_union(hatlar + kombi)
    n = sum(len(o['tasarim']['devreler']) for o in od)
    na = sum(1 for o in od for c in o['tasarim']['devreler'] if c.get('ayak_g'))
    uc = sum(1 for o in od for c in o['tasarim']['devreler']
             if abs(((c['pts'][0][0] - c['pts'][-1][0]) ** 2 + (c['pts'][0][1] - c['pts'][-1][1]) ** 2) ** 0.5 - 15) > 0.2)
    kes = 0
    tum = hatlar + kombi
    for i in range(len(tum)):
        for j in range(i + 1, len(tum)):
            if tum[i].distance(tum[j]) < 4.0 - 1e-6:
                if i >= len(hatlar) and j >= len(hatlar):
                    continue
                kes += 1
    out = dict(kat=k, daire=dno, bagli='%d/%d' % (na, n), kombi=bool(kombi), uc15_degil=uc, kesisme_yakin=kes)
    for o in od:
        L = boru.intersection(o['poly'].buffer(5)).length / 100.0
        Am = o.get('alan_mimari') or o['alan']
        s = '%.2f m/m2' % (L / Am)
        if o['tur'] in ('hol', 'oda'):
            s += ' cep %.2f' % cep(o['poly'], boru)
        if o['tur'] == 'hol':
            s += ' hol devre %.1f m' % (sum(S.uzunluk(c['pts']) for c in o['tasarim']['devreler']) / 100.0)
        ad = o['ad'][:10]
        while ad in out:
            ad += "'"
        out[ad] = s
    return out


def ciz(k, dno, od, son, yol):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    K = od[0]['r'].get('K') if isinstance(od[0]['r'], dict) else None  # noqa: F841
    U = unary_union([o['poly'] for o in od])
    x0, y0, x1, y1 = U.buffer(60).bounds
    fig = plt.figure(figsize=(12, 12 * (y1 - y0) / (x1 - x0)))
    ax = fig.add_axes([0, 0, 1, 1])
    for o in od:
        for g in getattr(o['poly'], 'geoms', [o['poly']]):
            ax.plot(*g.exterior.xy, color='0.6', lw=0.8)
        ax.text(o['poly'].centroid.x, o['poly'].centroid.y, o['ad'][:8], color='0.4', fontsize=8, ha='center')
    for o in od:
        for c in o['tasarim']['devreler']:
            p = S.cizgi(c['pts'])
            ax.plot(*p.xy, color='red', lw=0.7)
            for key in ('ayak_g', 'ayak_d'):
                if c.get(key):
                    xs, ys = zip(*c[key])
                    ax.plot(xs, ys, color='blue', lw=0.6)
    if son:
        if son.get('kombi_hat'):
            for h in (son['kombi_hat']['gidis'], son['kombi_hat']['donus']):
                xs, ys = zip(*h)
                ax.plot(xs, ys, color='green', lw=0.9)
        kol = son.get('kollektor')
        if kol:
            ax.plot(*kol['kutu'].exterior.xy, color='black', lw=1.2)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.savefig(yol, dpi=110)
    plt.close(fig)


def coz(k, dnolar):
    os.makedirs(CIK, exist_ok=True)
    KT = pickle.load(open('%s/pre_%s.pkl' % (ONB, k), 'rb'))
    sonuclar = []
    for dno in dnolar:
        od = copy.deepcopy([o for o in KT['odalar'] if o['daire'] == dno])
        t0 = time.time()
        kol = Y.ayaklari_kur(k, KT['K'], od, KT['yasak'])
        son = kol.get(dno)
        m = olc(k, dno, od, son)
        m['sure'] = round(time.time() - t0)
        print('[daire]', m, flush=True)
        ciz(k, dno, od, son, '%s/%s_D%d.png' % (CIK, k, dno))
        sonuclar.append(m)
    return sonuclar


if __name__ == '__main__':
    if sys.argv[1] == 'hazirla':
        hazirla()
    else:
        coz(sys.argv[2], [int(a) for a in sys.argv[3:]])
