# -*- coding: utf-8 -*-
"""Kanal modülü senaryo çalıştırıcı.  Kullanım:
    python3 calistir.py ornek_ofis.json     proje/denemeler/kanal/ofis_kanal.dxf
    python3 calistir.py ornek_otopark.json  proje/denemeler/kanal/otopark_jetfan.dxf
Tasarım değerleri JSON'dan okunur; "deneme": true ise çıktıya DENEME başlığı yazılır."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kanal import *
from kanal import _add
from shapely.geometry import Polygon, box, LineString, Point
from shapely.ops import unary_union


# ------------------------------------------------------------------ ortak mimari
def mimari(cz, M):
    dis = Polygon(M["dis_kontur"])
    mah = unary_union([Polygon(m["poly"]) for m in M["mahaller"]])
    duvar = dis.difference(mah)
    for b in M.get("bosluklar", []):
        duvar = duvar.difference(box(*b))
    kolon = [box(x, y, x + w, y + h) for x, y, w, h in M.get("kolonlar", [])]
    izinli = dis.buffer(-M.get("dis_duvar", 25), join_style=2)
    return duvar, kolon, izinli, mah


def mimari_ciz(cz, M, duvar, kolon, kanal_birlesik, kes):
    d = duvar.difference(kanal_birlesik)
    sin = d.boundary.difference(unary_union([k.buffer(0.3) for k in kes])) if kes else d.boundary
    cz.geom(sin, "ROTAS-MIMARI-DUVAR")
    for k in kolon:
        cz.geom(k, "ROTAS-MIMARI-KOLON")
        h = cz.msp.add_hatch(color=8, dxfattribs=dict(layer="ROTAS-MIMARI-KOLON"))
        h.set_pattern_fill("ANSI31", scale=1.5)
        h.paths.add_polyline_path(list(k.exterior.coords)[:-1], is_closed=True)
        cz.engel.append(k)
    cz.engel.append(duvar)
    for m in M["mahaller"]:
        if "yazi" in m:
            cz.yerlestir([(tuple(m["yazi"]), 0.0)], [m["ad"]] + m.get("alt", []), 18, "ROTAS-MIMARI-YAZI")


def baslik_ciz(cz, J, x0, x1, y0, y1):
    cz.T(((x0 + x1) / 2, y0 - 90), f"{J['baslik']}.........ÖLÇEK: 1 / 50", 32, "ROTAS-PAFTA", TA.MIDDLE_CENTER)
    if J.get("deneme"):
        cz.T(((x0 + x1) / 2, y1 + 110), "DENEME — ÖRNEK DEĞERLERLE HAZIRLANMIŞTIR, UYGULAMAYA ESAS DEĞİLDİR", 30, "ROTAS-PAFTA", TA.MIDDLE_CENTER)


def notlar_ciz(cz, x, y, notlar, baslik="NOTLAR"):
    cz.T((x, y), baslik, 13, "ROTAS-TES-NOT", TA.BOTTOM_LEFT)
    for i, s in enumerate(notlar):
        cz.T((x, y - 22 - i * 16), f"{i + 1}. {s}", 9, "ROTAS-TES-NOT", TA.MIDDLE_LEFT)
    return y - 30 - len(notlar) * 16


def ornek_kanal(lay, ters=False):
    def f(cz, p):
        x, y = p
        cz.L((x - 60, y + 9), (x + 60, y + 9), lay); cz.L((x - 60, y - 9), (x + 60, y - 9), lay)
        ok_dolu(cz, (x, y), (-1, 0) if ters else (1, 0), 10, "ROTAS-KANAL-OK")
    return f


def ornek_flex(cz, p):
    x, y = p
    u = dict(S=(x - 50, y), E=(x + 50, y), d=(1, 0), t=dict(flex=150))
    flex_ciz(cz, u)


def ornek_menfez(tur):
    def f(cz, p):
        u = dict(t=dict(p=p, mw=300, mh=150), d=(0, 1), menfez=box(p[0] - 15, p[1] - 7.5, p[0] + 15, p[1] + 7.5))
        # menfez_tavan: uzun kenar d'ye dik
        u["menfez"] = box(p[0] - 15, p[1] - 7.5, p[0] + 15, p[1] + 7.5)
        menfez_tavan(cz, dict(t=u["t"], d=(0, 1), menfez=u["menfez"]), tur)
    return f


def ornek_menfez_yan(tur):
    def f(cz, p):
        x, y = p
        cz.L((x - 60, y - 10), (x + 60, y - 10), "ROTAS-DUMAN-EGZOZ"); cz.L((x - 60, y - 40), (x + 60, y - 40), "ROTAS-DUMAN-EGZOZ")
        menfez_yan(cz, dict(c0=(x, y - 10), d=(1, 0), nrm=(0, 1), ml=60), tur)
    return f


def ornek_vd(cz, p):
    x, y = p
    cz.L((x - 50, y + 10), (x + 50, y + 10), "ROTAS-UFLEME-KANALI"); cz.L((x - 50, y - 10), (x + 50, y - 10), "ROTAS-UFLEME-KANALI")
    k2 = vd_ciz(cz, p, (1, 0), 20)
    cz.T((k2[0], k2[1] + 6), "VD", 7, "ROTAS-DAMPER")


def ornek_fd(cz, p):
    x, y = p
    cz.L((x - 50, y + 10), (x + 50, y + 10), "ROTAS-UFLEME-KANALI"); cz.L((x - 50, y - 10), (x + 50, y - 10), "ROTAS-UFLEME-KANALI")
    fd_ciz(cz, p, (1, 0), 20)
    cz.T((x, y + 20), "FD", 7, "ROTAS-DAMPER")


def ornek_bdd(cz, p):
    x, y = p
    cz.L((x - 50, y + 15), (x + 50, y + 15), "ROTAS-DUMAN-EGZOZ"); cz.L((x - 50, y - 15), (x + 50, y - 15), "ROTAS-DUMAN-EGZOZ")
    bdd_ciz(cz, p, (1, 0), 30)
    cz.T((x, y + 25), "BDD", 7, "ROTAS-DAMPER")


def ornek_panjur(tur):
    def f(cz, p):
        x, y = p
        panjur_ciz(cz, (x - 30, y), (x + 30, y), (0, 1), 20, tur)
    return f


# ------------------------------------------------------------------ OFİS
def ofis(J, cikti):
    cz = Cizim()
    M = J["mimari"]
    duvar, kolon, izinli, mah = mimari(cz, M)
    fdl = [LineString(l) for l in M.get("yangin_duvarlari", [])]
    I = J["igk"]
    body, agiz = igk_ciz(cz, tuple(I["merkez"]), I["boyut"][0], I["boyut"][1], tuple(I["oda_yonu"]))
    cz.engel.append(body)
    od = tuple(I["oda_yonu"])
    log = []

    def uclar(A):
        return [dict(p=tuple(p), q=A["q"], tip=A.get("tip", "tavan")) for p in A["menfezler"]]

    UF, EM = J["ufleme"], J["emis"]
    tu, te = uclar(UF), uclar(EM)

    def mkutu(ts, prm):
        out = []
        for t in ts:
            w, h, _ = menfez_sec(t["q"], prm.get("menfez_v", 2.0), prm.get("menfez_serbest", 0.7))
            r = max(w, h) / 20 + 22
            out.append(box(t["p"][0] - r, t["p"][1] - r, t["p"][0] + r, t["p"][1] + r))
        return out

    eng0 = kolon + [body.buffer(-10, join_style=2)]
    walls = [(duvar, M.get("dis_duvar", 25))]
    # ortak güzergâh: en iyi birkaç üfleme adayı için emiş ağı çözülür, toplam maliyeti en düşük çakışmasız çift seçilir
    adaylar = oto_ag("ÜFLEME", "ufleme", UF, agiz["UF"], od, tu, eng0 + mkutu(te, EM), walls, izinli, log, k=J.get("ortak_aday", 16))
    best = None
    for ag_u, h_u in adaylar:
        if h_u:
            continue
        ag_geometri(ag_u)
        ug_u = uc_geometri(ag_u)
        eng1 = eng0 + [e.poly for e in ag_u.kenar] + [u["kutu"] for u in ug_u]
        ag_e, h_e = oto_ag("EMİŞ", "emis", EM, agiz["EM"], od, te, eng1, walls, izinli, log)
        c = ag_u.maliyet + ag_e.maliyet
        print("  aday üfleme", ag_u.secim, "emiş", ag_e.secim, "çakışma", h_e, "maliyet", round(c))
        if best is None or (h_e, c) < (best[3], best[2]):
            best = (ag_u, ag_e, c, h_e)
    ag_uf, ag_em, _, h2 = best
    h1 = 0
    ag_geometri(ag_uf); ag_geometri(ag_em)
    print("çakışma: üfleme", h1, "emiş", h2, "| denenen aday", len(log))

    # taze hava / atık hava hatları (cihaz -> cephe panjuru)
    P = J["panjur"]
    hat = []
    for ad, tur, ag_k, q in (("TAZE HAVA", "taze", "TH", UF["q_toplam"]), ("ATIK HAVA", "atik", "AT", EM["q_toplam"])):
        pts = [tuple(p) for p in J["hatlar"][ag_k]]
        z = zincir(ad, tur, dict(v_ana=P["v_kanal"], v_brans=P["v_kanal"], yontem="hiz", hmax=UF.get("hmax", 300)), pts, q,
                   dict(ad="panjur", dp=P["dp"]))
        boyutlandir(z)
        hat.append(z)
    # panjurlar
    panj = []
    for z in hat:
        e = z.kenar[-1]
        son = e.b.p
        d = e.d; n = (-d[1], d[0])
        a, b = _add(son, n, e.wc / 2), _add(son, n, -e.wc / 2)
        kal = M.get("dis_duvar", 25)
        A_ef = z.kok.q / 3600 / P["v_efektif"]
        hp = math.ceil(A_ef / P["serbest"] / (e.w / 1000) / 0.05) * 50
        poly = Polygon([a, b, _add(b, d, kal), _add(a, d, kal)])
        panj.append(dict(z=z, a=a, b=b, d=d, kal=kal, poly=poly, w=e.w, hp=hp, A=A_ef))

    # ---- çizim sırası: ağlar, mimari, etiketler
    cz.engel.append(duvar); cz.engel.extend(kolon)
    kes_dev = [body.exterior] + [p["poly"].exterior for p in panj]
    tum = []
    U = {}
    for ag in (ag_uf, ag_em) + tuple(hat):          # tüm kanallar önceden engel (yazılar hiçbirine binmesin)
        un0, _ = ag_geometri(ag)
        cz.engel.append(un0); cz.engel.extend(u["kutu"] for u in uc_geometri(ag))
    for ag in (ag_uf, ag_em) + tuple(hat):
        un, ug = ag_ciz(cz, ag, kes_dev, fd_hatlari=fdl, vd=ag.tur in ("ufleme", "emis"))
        U[ag.ad] = (un, ug); tum.append(un)
    for p in panj:
        panjur_ciz(cz, p["a"], p["b"], (-p["d"][0], -p["d"][1]), p["kal"], p["z"].tur)
        cz.engel.append(p["poly"])
    birlesik = unary_union(tum + [p["poly"] for p in panj])
    mimari_ciz(cz, M, duvar, kolon, birlesik, [u.boundary for u in tum] + [p["poly"].exterior for p in panj])
    # etiketler
    for ag, on in ((ag_uf, "Ü"), (ag_em, "E"), (hat[0], "T"), (hat[1], "A")):
        un, ug = U[ag.ad]
        ag_etiket(cz, ag, ug, onek=on)
    for p in panj:
        z = p["z"]
        nm = "TAZE HAVA ALIŞ PANJURU" if z.tur == "taze" else "ATIK HAVA ATIŞ PANJURU"
        kis = "T.H.P." if z.tur == "taze" else "E.A.P."
        c = _add(_add(p["a"], p["d"], p["kal"] + 30), (p["b"][0] - p["a"][0], p["b"][1] - p["a"][1]), 0.5)
        satir = [nm, f"{kis}: {p['w']}x{p['hp']} mm", f"{tr(z.kok.q)} m³/h (efektif {tr(P['v_efektif'], 1)} m/s)"]
        ad = [((c[0] - 120 + dx, c[1] + dy), 0.0) for dy in (60, -60, 100, -100, 0) for dx in (0, -60, 60)]
        cz.yerlestir(ad, satir, 8, "ROTAS-MENFEZ-YAZI", cizgi_ucu=_add(p["a"], p["d"], p["kal"]))
    # basınç kayıpları
    sonuc = {}
    for ag in (ag_uf, ag_em) + tuple(hat):
        sonuc[ag.ad] = basinc(ag)
    esp_uf = sonuc["ÜFLEME"][1][0]["top"] + sonuc["TAZE HAVA"][1][0]["top"]
    esp_em = sonuc["EMİŞ"][1][0]["top"] + sonuc["ATIK HAVA"][1][0]["top"]
    ic = cz.blok
    # cihaz etiketi
    cz.yerlestir([((I["merkez"][0], I["merkez"][1] + I["boyut"][1] / 2 + 260), 0.0), ((I["merkez"][0], I["merkez"][1] - I["boyut"][1] / 2 - 260), 0.0)],
                 [f"{I['ad']} TAVAN TİPİ", "ISI GERİ KAZANIMLI", "HAVALANDIRMA CİHAZI",
                  f"ÜF {tr(UF['q_toplam'])} / EM {tr(EM['q_toplam'])} m³/h",
                  f"ESP ÜF {tr(esp_uf * 1.1, 0)} Pa / EM {tr(esp_em * 1.1, 0)} Pa", f"plakalı, verim ≥ %{I['verim']}"],
                 9, "ROTAS-HAVALANDIRMA-CIHAZ", cizgi_ucu=tuple(I["merkez"]))
    # ağız harfleri (cihaz içinde)

    # ---- sağ blok: tablolar, metraj, lejant, notlar
    x0, y0, x1, y1 = Polygon(M["dis_kontur"]).bounds
    tx = x1 + 250
    yy = y1 + 40
    for ag, on in ((ag_uf, "Ü"), (ag_em, "E"), (hat[0], "T"), (hat[1], "A")):
        gr, yol = sonuc[ag.ad]
        yy, _ = basinc_tablosu(cz, tx, yy, ag, gr, yol, on)
        yy -= 60
    s = [f"{I['ad']} ÜFLEME FANI CİHAZ DIŞI BASINCI: üfleme kritik hat {tr(sonuc['ÜFLEME'][1][0]['top'], 1)} + taze hava hattı {tr(sonuc['TAZE HAVA'][1][0]['top'], 1)} = {tr(esp_uf, 1)} Pa (+%10 = {tr(esp_uf * 1.1, 0)} Pa)",
         f"{I['ad']} EGZOZ FANI CİHAZ DIŞI BASINCI: emiş kritik hat {tr(sonuc['EMİŞ'][1][0]['top'], 1)} + atık hava hattı {tr(sonuc['ATIK HAVA'][1][0]['top'], 1)} = {tr(esp_em, 1)} Pa (+%10 = {tr(esp_em * 1.1, 0)} Pa)",
         f"Yöntem: eşit sürtünme R ≤ {tr(UF['R'], 1)} Pa/m, ana kanal v ≤ {tr(UF['v_ana'], 1)} m/s, branşman v ≤ {tr(UF['v_brans'], 1)} m/s; asma tavan boşluğu kanal yüksekliği ≤ {UF['hmax']} mm.",
         "ζ: T branş 1,0 / düz geçiş+redüksiyon 0,3 / dirsek 0,3 / VD 0,2 / FD 0,2 / cihaz ağzı 0,5; menfez 25 Pa, flex 5 Pa, panjur 25 Pa."]
    for i, t in enumerate(s):
        cz.T((tx, yy - i * 16), t, 9, "ROTAS-HESAP", TA.MIDDLE_LEFT)
    yy -= len(s) * 16 + 70
    rows = metraj([ag_uf, ag_em] + hat)
    nfx = {}
    for ag in (ag_uf, ag_em):
        for u in uc_geometri(ag):
            nfx[u["t"]["flex"]] = nfx.get(u["t"]["flex"], 0.0) + math.dist(u["S"], u["E"]) / 100
    nm = {}
    for ag in (ag_uf, ag_em):
        for n in ag.uclar():
            k = ("ÜFLEME" if ag.tur == "ufleme" else "EMİŞ", n.uc["mw"], n.uc["mh"])
            nm[k] = nm.get(k, 0) + 1
    ek = ["Flex (izoleli Ø): " + ", ".join(f"Ø{d} {tr(L, 1)} m" for d, L in sorted(nfx.items())),
          "Menfezler: " + ", ".join(f"{k[0]} {k[1]}x{k[2]} {v} ad." for k, v in sorted(nm.items())),
          f"Damperler: VD {sum(1 for ag in (ag_uf, ag_em) for e in ag.kenar if e.vd)} ad., FD {sum(len(e.fd) for ag in (ag_uf, ag_em) for e in ag.kenar)} ad."]
    yy = metraj_tablosu(cz, tx, yy, rows, ek)
    yy -= 60
    lx = tx + 760
    km = lambda ag: ("m", sum(e.L for e in ag.kenar) / 100)
    lejant(cz, lx, y1 + 40, [
        ("ÜFLEME KANALI", ornek_kanal("ROTAS-UFLEME-KANALI"), km(ag_uf)),
        ("EMİŞ (DÖNÜŞ) KANALI", ornek_kanal("ROTAS-EMIS-KANALI", True), km(ag_em)),
        ("TAZE HAVA KANALI", ornek_kanal("ROTAS-TAZE-HAVA-KANALI"), km(hat[0])),
        ("ATIK HAVA KANALI", ornek_kanal("ROTAS-ATIK-HAVA-KANALI"), km(hat[1])),
        ("FLEX BAĞLANTI KANALI (İZOLELİ)", ornek_flex, "flex"),
        ("ÜFLEME MENFEZİ (ÇİFT SIRA KANATLI)", ornek_menfez("ufleme"), "menfez_ufleme"),
        ("EMİŞ MENFEZİ", ornek_menfez("emis"), "menfez_emis"),
        ("VD AYAR (VOLÜM) DAMPERİ", ornek_vd, "vd"),
        ("FD YANGIN DAMPERİ", ornek_fd, "fd"),
        ("TAZE HAVA ALIŞ PANJURU", ornek_panjur("taze"), "panjur_taze"),
        ("ATIK HAVA ATIŞ PANJURU", ornek_panjur("atik"), "panjur_atik"),
        ("ISI GERİ KAZANIMLI HAVALANDIRMA CİHAZI (IGK)", lambda cz, p: igk_ciz(cz, p, 90, 44, (1, 0)), "igk"),
    ])
    notlar_ciz(cz, lx, y1 - 680, [
        "Kanallar galvaniz sactan, TS EN 1505'e uygun flanşlı imal edilecektir.",
        "Üfleme ve taze hava kanalları 13 mm kauçuk köpüğü ile izole edilecektir.",
        "Menfezler plenum kutulu olup izoleli flex ile bağlanacaktır (flex boyu ≤ 1,5 m).",
        "Yangın duvarı geçişlerinde EI 60 yangın damperi (FD) konulacaktır.",
        "Her branşman başına ayar damperi (VD) konulacak, devreye almada balans yapılacaktır.",
        "Kanal etiketi: genişlik x yükseklik (mm) / debi [kanal no]; kanal no basınç tablosuna bağlıdır.",
        "Taze hava ve atık hava panjurları arasında en az 3 m mesafe bırakılacaktır.",
        "Duvar geçişlerinde betonarmede / duvarda kanal ölçüsünden 10 cm büyük boşluk bırakılacaktır.",
    ])
    baslik_ciz(cz, J, x0, x1, y0, y1)
    print("KONTROL:", kontrol_raporu(cz, [ag_uf, ag_em] + hat, kolon) or "temiz")
    os.makedirs(os.path.dirname(cikti), exist_ok=True)
    cz.bitir(cikti)
    return cz, dict(aglar=[ag_uf, ag_em] + hat, sonuc=sonuc, esp=(esp_uf, esp_em), metraj=rows)


# ------------------------------------------------------------------ OTOPARK
def otopark(J, cikti):
    cz = Cizim()
    M = dict(J["mimari"])
    EG0, F0 = J["egzoz"], J["fan"]
    fo = EG0["fan_odasi"]
    fy0, fy1 = fo[1] + 60, fo[3] - 60
    fys = [fy0 + (fy1 - fy0) * (i + 0.5) / F0["adet"] for i in range(F0["adet"])]
    M["bosluklar"] = list(M.get("bosluklar", [])) + [[EG0["saft"][2], fy - F0["R"] - 3, fo[0], fy + F0["R"] + 3] for fy in fys]
    duvar, kolon, izinli, mah = mimari(cz, M)
    O = J["otopark"]
    A, H = O["alan"], O["yukseklik"]
    V = A * H
    Qn, Qd = V * O["hd_normal"], V * O["hd_duman"]
    # egzoz menfezleri: hat boyunca eşit aralık
    EG = J["egzoz"]
    n = math.ceil(Qd / EG["menfez_qmax"])
    (ax, ay), (bx, by) = EG["menfez_hatti"]
    pts = [(ax + (bx - ax) * (i + 0.5) / n, ay + (by - ay) * (i + 0.5) / n) for i in range(n)]
    te = [dict(p=p, q=Qd / n, tip="yan", yon=EG.get("menfez_yon", 1)) for p in pts]
    port, yon = tuple(EG["port"]), tuple(EG["port_yon"])
    fan_oda = box(*EG["fan_odasi"])
    saft = box(*EG["saft"])
    log = []
    walls = [(duvar, M.get("dis_duvar", 25))]
    # jet fanlar (yerleşim: sıra = genişlik / yanal etki, sütun = atış mesafesi)
    JF = J["jetfan"]
    (jx0, jy0, jx1, jy1) = JF["alan"]
    nr = math.ceil((jy1 - jy0) / JF["yanal"])
    xs = []
    x = jx0 + JF["boy"] / 2
    while x + JF["boy"] / 2 < jx1:
        xs.append(x); x += JF["atis"]
    jf = []
    for i in range(nr):
        y = jy0 + (jy1 - jy0) * (i + 0.5) / nr
        for x in xs:
            jf.append((x, y))
    jf_poly = [box(x - JF["boy"] / 2, y - JF["cap"] / 2, x + JF["boy"] / 2 + 75, y + JF["cap"] / 2) for x, y in jf]
    for p, g in zip(jf, jf_poly):
        for k in kolon:
            if g.buffer(30).intersects(k):
                print("UYARI: jet fan kolona yakın", p)
    eng = kolon + [fan_oda.buffer(-10, join_style=2), saft] + jf_poly
    ag_eg, h = oto_ag("DUMAN EGZOZ", "duman", EG, port, yon, te, eng, walls, izinli.union(fan_oda.buffer(1)), log)
    print("çakışma: egzoz", h, "| denenen aday", len(log))
    # ---- çizim
    kes = [fan_oda.exterior]
    cz.engel.append(duvar); cz.engel.extend(kolon)
    un, ug = ag_ciz(cz, ag_eg, kes)
    # fan odası, şaft, fanlar
    cz.geom(saft, "ROTAS-SAFT")
    sx0, sy0, sx1, sy1 = saft.bounds
    cz.L((sx0, sy0), (sx1, sy1), "ROTAS-SAFT"); cz.L((sx0, sy1), (sx1, sy0), "ROTAS-SAFT")
    cz.engel.append(saft)
    F = J["fan"]
    fans = []
    nf = F["adet"]
    wx = EG["fan_odasi"][0]                      # fan odası / şaft duvarının oda yüzü
    for fy in fys:
        R = F["R"]
        fc = (wx + 22 + R * 1.2, fy)             # fan gövdesi; çıkış (batı) duvara doğru
        g = fan_aksiyel(cz, fc, (-1, 0), R)
        # fan çıkışı ile duvar arası kısa kanal + BDD geri akış damperi
        cz.L((wx, fy + R + 3), (fc[0] - R * 1.2, fy + R + 3), "ROTAS-DUMAN-EGZOZ")
        cz.L((wx, fy - R - 3), (fc[0] - R * 1.2, fy - R - 3), "ROTAS-DUMAN-EGZOZ")
        bdd_ciz(cz, (wx + 11, fy), (-1, 0), 2 * R + 6)
        fans.append((fc, g)); cz.engel.append(g.buffer(5).union(box(wx - 20, fy - R - 3, fc[0], fy + R + 3)))
    mimari_ciz(cz, M, duvar, kolon, un, [un.boundary])
    # jet fanlar
    for i, (p, g) in enumerate(zip(jf, jf_poly)):
        jg = jetfan_ciz(cz, p, tuple(JF["yon"]), JF["boy"], JF["cap"])
        cz.engel.append(jg)
    for i, (p, g) in enumerate(zip(jf, jf_poly)):
        cz.yerlestir([((p[0], p[1] + JF["cap"] / 2 + 22), 0.0), ((p[0], p[1] - JF["cap"] / 2 - 22), 0.0)],
                     [f"JF-{i + 1}  {JF['itki']} N", "F300 / 2 saat"], 8, "ROTAS-JETFAN")
    # etiketler
    ag_etiket(cz, ag_eg, ug, onek="D")
    gr, yol = basinc(ag_eg)
    esp = yol[0]["top"] + F["saft_dp"]
    cz.yerlestir([((EG["fan_odasi"][0] - 200, (EG["fan_odasi"][1] + EG["fan_odasi"][3]) / 2), 0.0),
                  ((EG["fan_odasi"][0] - 200, EG["fan_odasi"][3] + 160), 0.0)],
                 ["EGZOZ FAN ODASI (EI 120)", f"EF-1..EF-{nf} AKSİYEL EGZOZ / DUMAN FANI",
                  f"her biri {tr(Qd / nf)} / {tr(Qn / nf)} m³/h (çift hız)", f"ESP {tr(esp * 1.1, 0)} Pa - F300 2 saat (EN 12101-3)",
                  "fan çıkışlarında BDD geri akış damperi"], 8, "ROTAS-HAVALANDIRMA-CIHAZ", cizgi_ucu=fans[0][0])
    cz.yerlestir([((sx0 - 230, sy0 - 60), 0.0), ((sx0 - 230, sy1 + 80), 0.0)],
                 ["EGZOZ ŞAFTI", f"{tr(Qd)} m³/h - çatı üst kotunun 1 m üzerinden", "JETCAP ile atış (sığınağın karşı cephesi)",
                  f"BETONARMEDE {int((sx1 - sx0) + 10)}x{int((sy1 - sy0) + 10)} cm BOŞLUK BIRAKILACAKTIR"], 8, "ROTAS-TES-NOT",
                 cizgi_ucu=((sx0 + sx1) / 2, (sy0 + sy1) / 2))
    # rampa / taze hava
    R = J["rampa"]
    (rx0, ry0, rx1, ry1) = R["bosluk"]
    Ar = R["genislik"] * R["yukseklik"]
    vr = Qd / 3600 / Ar
    for k in range(3):
        y = ry0 + (ry1 - ry0) * (k + 1) / 4
        ok_acik(cz, (rx0 - 140, y), (rx1 + 60, y), "ROTAS-TAZE-HAVA-KANALI", 18)
        cz.engel.append(LineString([(rx0 - 140, y), (rx1 + 60, y)]).buffer(10))
    cz.yerlestir([((rx0 - 240, ry1 + 90), 0.0), ((rx0 - 240, ry0 - 90), 0.0)],
                 ["RAMPA - DOĞAL TAZE HAVA GİRİŞİ", f"{tr(Qd)} m³/h (duman) / {tr(Qn)} m³/h (normal)",
                  f"açıklık {tr(R['genislik'], 1)}x{tr(R['yukseklik'], 1)} m = {tr(Ar, 1)} m²  v = {tr(vr, 2)} m/s ≤ 2 m/s"],
                 8, "ROTAS-TES-NOT")
    # tablolar
    x0, y0, x1, y1 = Polygon(M["dis_kontur"]).bounds
    tx = x1 + 250
    yy = y1 + 40
    hes = [["Otopark net alanı", f"{tr(A, 0)} m²"], ["Ortalama yükseklik", f"{tr(H, 2)} m"], ["Hacim", f"{tr(V, 0)} m³"],
           ["Normal havalandırma (ROTAŞ: 4 h⁻¹)", f"{tr(Qn)} m³/h"], ["Duman tahliyesi (ROTAŞ: 10 h⁻¹)", f"{tr(Qd)} m³/h"],
           ["Egzoz menfezi", f"{n} ad. x {tr(Qd / n)} m³/h ({te[0]['mw']}x{te[0]['mh']})"],
           ["Egzoz fanı", f"{nf} ad. x {tr(Qd / nf)}/{tr(Qn / nf)} m³/h, ESP {tr(esp * 1.1, 0)} Pa"],
           ["Jet fan", f"{len(jf)} ad. x {JF['itki']} N ({nr} sıra x {len(xs)}; yanal {tr(JF['yanal'] / 100, 0)} m, atış {tr(JF['atis'] / 100, 0)} m)"],
           ["Taze hava (rampa)", f"{tr(Ar, 1)} m², v = {tr(vr, 2)} m/s"]]
    yy = tablo(cz, tx, yy, "KAPALI OTOPARK HAVALANDIRMA HESABI", ["Kalem", "Değer"], hes, [300, 420])
    yy -= 70
    yy, _ = basinc_tablosu(cz, tx, yy, ag_eg, gr, yol, "D")
    cz.T((tx, yy - 6), f"Fan dışı basınç = kritik hat {tr(yol[0]['top'], 1)} Pa + şaft/jetcap {tr(F['saft_dp'], 0)} Pa = {tr(esp, 1)} Pa (+%10 = {tr(esp * 1.1, 0)} Pa). Yöntem: hız, ana kanal v ≤ {tr(EG['v_ana'], 0)} m/s.",
         9, "ROTAS-HESAP", TA.MIDDLE_LEFT)
    yy -= 80
    rows = metraj([ag_eg], duman_aglari=("DUMAN EGZOZ",))
    yy = metraj_tablosu(cz, tx, yy, rows, [f"Egzoz menfezi {te[0]['mw']}x{te[0]['mh']} {n} ad. (duman kanalı yanağında, alüminyum, F300 uyumlu)",
                                            f"BDD geri akış damperi {nf} ad., jet fan {len(jf)} ad."])
    lx = tx + 780
    lejant(cz, lx, y1 + 40, [
        ("DUMAN EGZOZ KANALI", ornek_kanal("ROTAS-DUMAN-EGZOZ", True), ("m", sum(e.L for e in ag_eg.kenar) / 100)),
        ("EGZOZ MENFEZİ (KANAL YANAĞINDA)", ornek_menfez_yan("duman"), "menfez_yan_duman"),
        ("JET FAN (ATIŞ YÖNÜ OKLU)", lambda cz, p: jetfan_ciz(cz, (p[0] - 40, p[1]), (1, 0), 80, 25), "jetfan"),
        ("AKSİYEL EGZOZ FANI", lambda cz, p: fan_aksiyel(cz, p, (1, 0), 14), "fan_aksiyel"),
        ("BDD GERİ AKIŞ DAMPERİ", ornek_bdd, "bdd"),
        ("TAZE HAVA GİRİŞ YÖNÜ", lambda cz, p: ok_acik(cz, (p[0] - 60, p[1]), (p[0] + 60, p[1]), "ROTAS-TAZE-HAVA-KANALI", 14), None),
    ])
    notlar_ciz(cz, lx, y1 - 400, [
        "Normal işletmede egzoz fanları düşük devirde (4 hava değişimi), yangın sinyalinde tam devirde (10 hava değişimi) çalışacaktır.",
        "Jet fanlar yangın sinyalinde gecikmeli devreye girecek, CO seviyesine göre kademeli çalışacaktır.",
        "Fanlar, kanallar ve askılar 300 °C'de 2 saat dayanımlı (F300) olacaktır.",
        "Kesin jet fan yerleşimi CFD analizi ile doğrulanacaktır.",
        "Sprinkler başlıkları jet fan atış ağzından uzak tutulacaktır.",
        "Egzoz çıkışı sığınağın karşı cephesinden verilecek, betonarmede boşluk bırakılacaktır.",
        "CO dedektörleri (≈1 ad./400 m², yerden 1,5-1,8 m) yangın algılama projesinde gösterilecektir.",
    ])
    baslik_ciz(cz, J, x0, x1, y0, y1)
    print("KONTROL:", kontrol_raporu(cz, [ag_eg], kolon) or "temiz")
    os.makedirs(os.path.dirname(cikti), exist_ok=True)
    cz.bitir(cikti)
    return cz, dict(aglar=[ag_eg], Qn=Qn, Qd=Qd, jf=jf, esp=esp, metraj=rows, sonuc={"DUMAN EGZOZ": (gr, yol)})


def mty_kontrol(dxf):
    """MTY geçen blok / katman / yazı stili / yazı / öznitelik listesi (boş = temiz)."""
    d = ezdxf.readfile(dxf)
    out = [f"blok {b.name}" for b in d.blocks if "MTY" in b.name.upper()]
    out += [f"katman {l.dxf.name}" for l in d.layers if "MTY" in l.dxf.name.upper()]
    out += [f"stil {s.dxf.name}" for s in d.styles if "MTY" in s.dxf.name.upper()]
    for lay in [d.modelspace()] + list(d.blocks):
        for e in lay:
            t = e.text if e.dxftype() == "MTEXT" else (e.dxf.get("text", "") if e.dxftype() in ("TEXT", "ATTDEF") else "")
            if "MTY" in str(t).upper():
                out.append(f"yazı {t[:40]}")
            if e.dxftype() == "INSERT":
                out += [f"öznitelik {a.dxf.text}" for a in e.attribs if "MTY" in a.dxf.text.upper()]
    return out


if __name__ == "__main__":
    J = json.load(open(sys.argv[1], encoding="utf-8"))
    f = {"ofis": ofis, "otopark": otopark}[J["senaryo"]]
    cz, r = f(J, sys.argv[2])
    print("yazıldı:", sys.argv[2])
    print("lejant adetleri:", cz.say)
    m = mty_kontrol(sys.argv[2])
    print("MTY kontrolü:", "TEMİZ (0 blok/katman/yazı)" if not m else m)
