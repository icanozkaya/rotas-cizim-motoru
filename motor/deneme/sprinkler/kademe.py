# -*- coding: utf-8 -*-
"""Boru çapı kademe kuralı (R2, 14.10.2026 (B) talimatı):
şemada ve planda ana hat (kollektör -> sprinkler kolonu -> kat zon hattı -> kat dağıtım borusu ve devamı) her ayrımda
en fazla BİR standart kademe düşer (DN150 -> 125 -> 100 -> 80 -> 65 ...). Ani düşüş (ör. DN150'den DN100'e) yapılmaz.

Ana hat (devam) = bir düğümden çıkan, en çok başlık besleyen boru. Yan branşman (T'nin yan ağzı) kendi başlık sayısına
göre seçilir (bir branşmanın ana hattan küçük olması normaldir); bağlantının kendisi tablo çapındadır.
"""
from kurallar import DN_SERI


def asagi(dn):
    """bir standart kademe aşağısı"""
    i = DN_SERI.index(dn)
    return DN_SERI[max(0, i - 1)]


def kademe_farki(a, b):
    return DN_SERI.index(a) - DN_SERI.index(b)


def sema_zinciri(bdn, kok_dn):
    """pompa basma kollektörü (bdn) -> sprinkler kolonu -> kat zon hattı -> kat ağı kökü.
    Dönüş: dict(kollektor, kolon, zon, kok)"""
    kolon = max(kok_dn, asagi(bdn))
    zon = kolon                                     # zon vana grubu kolon çapında
    kok = max(kok_dn, asagi(zon))
    return dict(kollektor=bdn, kolon=kolon, zon=zon, kok=kok)


def uygula(net, giris_dn):
    """kat ağı (net['T'], kök net['root']) üzerinde ana hat devamını kademelendir; giriş = kat zon hattı çapı.
    Değişen kenar sayısını döndürür."""
    T, R = net['T'], net['root']
    deg = 0
    ust = {R: giris_dn}
    for n in _topolojik(T, R):
        cs = list(T.successors(n))
        if not cs:
            continue
        devam = max(cs, key=lambda c: (T[n][c]['n'], T[n][c]['dn']))
        for c in cs:
            e = T[n][c]
            if c == devam:
                yeni = max(e['dn'], asagi(ust[n]))
                if yeni != e['dn']:
                    e['dn_tablo'] = e.get('dn_tablo', e['dn'])
                    e['dn'] = yeni
                    deg += 1
            ust[c] = e['dn']
    return deg


def _topolojik(T, R):
    import networkx as nx
    return list(nx.topological_sort(T)) if R in T else []


def kontrol_ag(net, giris_dn):
    """ana hat devamında bir kademeden fazla düşüş var mı? Dönüş: ihlal listesi [(düğüm, üst DN, alt DN)]"""
    T, R = net['T'], net['root']
    ihl = []
    ust = {R: giris_dn}
    for n in _topolojik(T, R):
        cs = list(T.successors(n))
        if not cs:
            continue
        devam = max(cs, key=lambda c: (T[n][c]['n'], T[n][c]['dn']))
        for c in cs:
            if c == devam and kademe_farki(ust[n], T[n][c]['dn']) > 1:
                ihl.append((n, ust[n], T[n][c]['dn']))
            if T[n][c]['dn'] > ust[n]:
                ihl.append((n, ust[n], T[n][c]['dn'], 'büyüme'))
            ust[c] = T[n][c]['dn']
    return ihl


def kontrol_zincir(adimlar):
    """adimlar: [(ad, dn), ...] sıralı ana hat; her geçişte en fazla bir kademe düşüş ve büyüme yok"""
    ihl = []
    for (a, da), (b, db) in zip(adimlar[:-1], adimlar[1:]):
        if kademe_farki(da, db) > 1 or db > da:
            ihl.append((a, da, b, db))
    return ihl
