#!/usr/bin/env python3
"""sihhi2 — tur 7 (15.10.2026 (D) ikinci geri bildirim, `RED_sihhi_pissu_kolonu_kolon_saft_icinde.png`) ölçümleri.

    python3 motor/sihhi2/kontrol_tur7.py [DXF] [--onbellek Ks.pkl] [--json cikti.json]

DXF: kat planları ya da birleşik şerit (varsayılan proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf).
K5  kolon yeri (her kat, her pis su kolonu): sembol çemberi (r 10) -> betonarme kolon/perde (K.cols ∪ ANSI tarama),
    mekanik havalandırma şaftı (şaft kutusu ∪ mimari çizgilerden poligonlaştırılmış şaft hücresi ∪ kanal dairesi),
    tesisat / k.bac. / enerji odası hücresi, şaft yazısı ('mek.' / 'havl.'). Kural: betonarme/şaft >= 5 cm, yazı >= 2 cm.
    Katlar arası eksen sürekliliği: aynı kolon her katta aynı nokta (kat ofseti çıkarılınca <= 0,5 cm).
K6  hat–kolon bağlantısı: (a) hat ucu çemberde (|d - 10| <= 1); (b) son parça RADYAL (merkeze doğru, sapma <= 10°);
    (c) aynı kolona karşılıklı aynı doğru üzerinde iki uç (yön farkı >= 150°) yok; (d) kolonun yanından geçip sembole geri
    dönen (kanca) / sembolün yanından geçen hat yok (uç olmayan parçanın merkeze uzaklığı >= r + 4); (e) çember içine giren
    hat boyu 0 (K1).
K3  mutfakta yer süzgeci 0 (plan) + model (sihhi_model.json) mutfakta YS 0.
K7  besleme / şebeke hatları: ortak alana 60 cm içindeki (daire giriş / ortak alan) kapı kanadı (eğik mimari çizgi ≥ 25 cm)
    ile temiz su / şebeke hattı kesişmesi 0, kapı numara balonu (r 15–30) içinden geçen boy 0,
    daire girişinde hat GERÇEK duvardan (plan.gercek_duvar) geçer.
K4  (besleme.kontrol, tur 6) sayaç adedi, bağlantı, kesişme, üst üste, kapı alanı, duvar, ortak alan dışı, kolon hizası.
"""
import json
import math
import os
import sys
from collections import defaultdict

from shapely.geometry import LineString, Point
from shapely.ops import unary_union

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
KOK = os.path.dirname(os.path.dirname(BURASI))
import kontrol_tur6 as KT6  # noqa: E402
import kolon_yeri as KY  # noqa: E402

KOLON_R = 10.0


def _uclar(g):
    cs = list(g.coords)
    return [(cs[0], cs[1]), (cs[-1], cs[-2])]


def k5_kolon_yeri(P, Ks, ins, doc):
    out = {}
    eksen = defaultdict(dict)
    for k, K in Ks.items():
        hucre = KT6.saft_hucreleri(doc, K)
        saft_ek = unary_union(hucre) if hucre else None
        b, s, y = KY.yasak_bolge(K, P.saft_poligonlari(K))
        if saft_ek is not None:
            s = s.union(saft_ek)
        satir = []
        for ad, c, e in ins[k]:
            if 'PIS-KOLON' not in ad:
                continue
            no = None
            try:
                no = e.get_attrib_text('NO')
            except Exception:
                pass
            o = KY.olc(c, b, s, y)
            satir.append(dict(no=no, merkez=[round(c[0], 1), round(c[1], 1)], **o,
                              ihlal=bool(KY.ihlal(o))))
            if no:
                eksen[no][k] = (c[0] - K.off, c[1])
        out[k] = dict(kolon=len(satir), ihlal=sum(q['ihlal'] for q in satir),
                      min_beton=min((q['beton'] for q in satir), default=None),
                      min_saft=min((q['saft'] for q in satir), default=None),
                      min_yazi=min((q['yazi'] for q in satir), default=None), satir=satir)
    sapma = {}
    for no, d in eksen.items():
        ps = list(d.values())
        sapma[no] = round(max(math.dist(a, b) for a in ps for b in ps), 2) if len(ps) > 1 else 0.0
    out['eksen_surekliligi'] = dict(en_buyuk_sapma=max(sapma.values(), default=0.0), kolon=sapma)
    return out


def k6_baglanti(hat, ins):
    out = {}
    for k in KT6.PAFTA:
        kol = [p for ad, p, e in ins[k] if 'PIS-KOLON' in ad]
        pis = [g for lay, g in hat[k] if 'PIS' in lay]
        cember_disi, radyal_degil, karsilikli, kanca, ic = 0, 0, 0, 0, 0
        ornek = []
        for c in kol:
            C = Point(c)
            girisler = []
            for g in pis:
                if g.distance(C) > KOLON_R + 6:
                    continue
                L = g.intersection(C.buffer(KOLON_R - 0.1, resolution=32)).length
                if L > 0.01:
                    ic += 1
                biten = False
                for (u, v) in _uclar(g):
                    d = math.dist(u, c)
                    if d > KOLON_R + 1.5:
                        continue
                    biten = True
                    if abs(d - KOLON_R) > 1.0:
                        cember_disi += 1
                    # son parça yönü (v -> u) ile radyal yön (u -> merkez) arası açı
                    a1 = math.atan2(u[1] - v[1], u[0] - v[0])
                    a2 = math.atan2(c[1] - u[1], c[0] - u[0])
                    fark = abs((math.degrees(a1 - a2) + 180) % 360 - 180)
                    if fark > 10.0:
                        radyal_degil += 1
                        ornek.append(dict(tur='radyal degil', kolon=[round(c[0]), round(c[1])], sapma=round(fark, 1)))
                    girisler.append(math.degrees(math.atan2(u[1] - c[1], u[0] - c[0])))
                if not biten:
                    # uç değil ama kolona çok yakın geçen parça: kanca / yanından geçiş
                    if g.distance(C) < KOLON_R + 4.0:
                        kanca += 1
                        ornek.append(dict(tur='yanından geçiyor', kolon=[round(c[0]), round(c[1])],
                                          d=round(g.distance(C), 1)))
            for i in range(len(girisler)):
                for j in range(i + 1, len(girisler)):
                    f = abs((girisler[i] - girisler[j] + 180) % 360 - 180)
                    if f >= 150:
                        karsilikli += 1
                        ornek.append(dict(tur='karşılıklı', kolon=[round(c[0]), round(c[1])], aci=round(f, 1)))
        out[k] = dict(kolon=len(kol), cember_disi_uc=cember_disi, radyal_degil=radyal_degil, karsilikli_uc=karsilikli,
                      kanca_yanindan=kanca, cember_ici=ic, ornek=ornek[:8])
    return out


def k3_model():
    try:
        with open(KOK + '/proje/denemeler/sihhi2/sihhi_model.json', encoding='utf-8') as f:
            m = json.load(f)
    except Exception:
        return None
    n = 0

    def gez(o, mutfak=False):
        nonlocal n
        if isinstance(o, dict):
            ad = str(o.get('oda') or o.get('mahal') or o.get('name') or '')
            mut = mutfak or ('mutfak' in ad.lower())
            if mut and o.get('kind') == 'YS' or (mut and o.get('tur') == 'YS'):
                n += 1
            for v in o.values():
                gez(v, mut)
        elif isinstance(o, list):
            for v in o:
                gez(v, mutfak)
    gez(m)
    return dict(model_mutfak_ys=n)


def k7_besleme(P, Ks, hat, ins):
    out = {}
    for k, K in Ks.items():
        ls, tr = P._mim_seg_agaci(K)
        bes = [(lay, g) for lay, g in hat[k] if 'SEBEKE' in lay or 'SOGUK' in lay]
        ortak = unary_union([r['poly'] for r in K.rooms if r['tip'] == 'ortak'])
        bes = [(lay, g) for lay, g in bes if 'SEBEKE' in lay or g.intersection(ortak.buffer(5)).length > 5.0]
        kanat = 0
        orn = []
        tum = [(lay, g) for lay, g in hat[k] if 'SEBEKE' in lay or 'SOGUK' in lay or 'SICAK' in lay]
        for lay, g in tum:
            for i in tr.query(g):
                h = ls[i]
                if not h.intersects(g) or h.length < 25:
                    continue
                v = (h.coords[-1][0] - h.coords[0][0], h.coords[-1][1] - h.coords[0][1])
                L = math.hypot(*v)
                if 0.15 < abs(v[0]) / L < 0.985:          # eğik (kapı kanadı) çizgi
                    x = g.intersection(h)
                    if x.distance(ortak) > 60:            # daire / ortak alan girişi kapıları (besleme)
                        continue
                    kanat += 1
                    orn.append([round(x.centroid.x), round(x.centroid.y)])
        balon = None
        bs = [Point(a[1][0]).buffer(a[2]) for a in K.R if a[0] == 'C' and 15.0 <= a[2] <= 30.0]
        if bs:
            balon = unary_union(bs)
        balon_boy = sum(g.intersection(balon).length for lay, g in bes) if balon is not None else 0.0
        # daire girişi: giriş işaretinden ortak alana giden besleme parçası gerçek duvardan mı
        kapidan = 0
        for ad, p, e in ins[k]:
            if ad != 'ROTAS-S2-TEMIZ-GIRIS':
                continue
            for lay, g in bes:
                if g.distance(Point(p)) > 1.0 or 'SOGUK' not in lay:
                    continue
                cs = list(g.coords)
                u = cs[-1] if math.dist(cs[-1], p) < 1.0 else (cs[0] if math.dist(cs[0], p) < 1.0 else None)
                if u is None:
                    continue
                v = cs[-2] if u == cs[-1] else cs[1]
                # geçiş: giriş işaretinin 40 cm gerisinden (daire içi) ortak taraftaki parçaya
                d = P.birim(v, u)
                ic = (u[0] + d[0] * 10, u[1] + d[1] * 10)
                dis = (u[0] - d[0] * 40, u[1] - d[1] * 40)
                if not P.gercek_duvar(K, ic, dis, kaydir=(0.0,)):
                    kapidan += 1
                    orn.append(dict(giris=[round(p[0]), round(p[1])]))
        out[k] = dict(besleme_hat=len(bes), giris_kapi_kanadi_kesisme=kanat, balon_ici_cm=round(balon_boy, 1),
                      giris_kapi_acikligindan=kapidan, ornek=orn[:6])
    return out


def main(argv):
    dxf = KOK + '/proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf'
    onb, cik = None, None
    i = 0
    while i < len(argv):
        if argv[i] == '--onbellek':
            onb = argv[i + 1]
            i += 2
        elif argv[i] == '--json':
            cik = argv[i + 1]
            i += 2
        else:
            dxf = argv[i]
            i += 1
    doc, hat, ins = KT6.oku(dxf)
    P, Ks = KT6.kat_bilgisi(onb)
    sonuc = dict(dxf=dxf)
    sonuc['K5'] = k5_kolon_yeri(P, Ks, ins, doc)
    sonuc['K6'] = k6_baglanti(hat, ins)
    sonuc['K1'] = KT6.k1_kolon_cember(hat, ins)
    sonuc['K3'] = KT6.k3_mutfak_suzgec(P, Ks, ins)
    sonuc['K3_model'] = k3_model()
    sonuc['K7'] = k7_besleme(P, Ks, hat, ins)
    try:
        import besleme as B
        sonuc['K4'] = B.kontrol(dxf, Ks, hat, ins)
    except ImportError:
        pass
    for t in ('K5', 'K6', 'K1', 'K3', 'K7', 'K4'):
        for k, v in sonuc.get(t, {}).items():
            ozet = {a: b for a, b in v.items() if a not in ('ornek', 'satir', 'detay', 'kolon')} \
                if isinstance(v, dict) else v
            if t == 'K5' and k == 'eksen_surekliligi':
                ozet = v
            print(t, k, json.dumps(ozet, ensure_ascii=False))
    print('K3_model', json.dumps(sonuc['K3_model'], ensure_ascii=False))
    if cik:
        with open(cik, 'w', encoding='utf-8') as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=1, default=str)
    return sonuc


if __name__ == '__main__':
    main(sys.argv[1:])
