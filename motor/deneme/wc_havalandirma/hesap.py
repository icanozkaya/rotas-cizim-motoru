"""Penceresiz ıslak hacim mekanik havalandırma hesabı (WC/banyo aspiratörü + ortak şaft + çatı tipi fan).

Girdi JSON (bkz. ornek_z2_9daire.json):
  katlar   : [{kod, ad, kot (m), h (m)}]           alttan üste
  cati_kot : çatı döşemesi üst kotu (m);  cati_ustu: şaftın çatıdan çıkış yüksekliği (m, fan kaidesi)
  kabul    : {q_oda: 80 (m³/h, ROTAŞ / kullanıcı kabulü, penceresiz hacim başına),
              kademeler: [80, 160] (iki kademeli aspiratör), asp_basinc: 50 (Pa), baglanti_cap: 150 (mm),
              oda_basina_aspirator: false (kullanıcı örneği: aynı daire + aynı şaft + aynı katta tek aspiratör, debiler toplanır)}
  saftlar  : [{ad, baglanti_yuk (m, kat kotundan branşman ekseni), kesit: [w, h] mm (boşsa hesaplanır)}]
  mahaller : [{kat, daire, ad, tip: BANYO|WC, saft, brans_m, alan_m2}]   yalnız PENCERESİZ ıslak hacimler
  pencereli: bilgi (hesaba girmez)

Yöntem:
  - Debi: DIN 18017-3 asgari (banyo 40 sürekli / 60 kesikli, WC 20 / 30 m³/h) TABLODA KARŞILAŞTIRMA için;
    tasarım debisi kullanıcı kabulü q_oda (örnek proje: 80 m³/h, iki oda -> 160 m³/h kademe). q_oda < DIN kesikli ise uyarı.
  - Branşman (aspiratör -> şaft): Ø150 spiro + flex, Darcy/Swamee-Jain; ζ: dirsek 0,3 + geri akış klapesi 1,0 +
    şafta T-branş girişi 1,0; flex sürtünmesi düz kanalın 1,5 katı. Toplam <= aspiratör basıncı (50 Pa) kontrolü.
  - Şaft: galvaniz dikdörtgen kanal, 50 mm adımlı, sabit kesit (en büyük debiye göre, v <= 6 m/s, min 150x150);
    her bölüm R·L + T düz geçiş ζ=0,3; üst uçta çatı geçişi / fan emiş ağzı ζ=0,5 + çatı başlığı (fan şapkası) ζ=1,0.
  - Çatı tipi fan: Q = Σ aspiratör debisi, P = (şaft + başlık) x 1,10. Fan sınıfı tipik eğriden (P = Pmax·(1-(Q/Qmax)²),
    Q <= 0,85·Qmax) seçilir — marka/model üretici kataloğundan teyit edilir.
"""
import math

RHO, NU, EPS = 1.2, 1.5e-5, 0.15e-3        # hava yoğunluğu, kinematik viskozite, galvaniz pürüzlülüğü (m)
DIN = {'BANYO': (40, 60), 'WC': (20, 30)}  # DIN 18017-3 sürekli / kesikli (m³/h)
ZETA = dict(dirsek=0.3, klape=1.0, t_brans=1.0, t_duz=0.3, cati_giris=0.5, cati_baslik=1.0)
FLEX_K, FLEX_L = 1.5, 0.5                  # flex sürtünme çarpanı, flex boyu (m)
V_SAFT = 6.0                                # şaft hız sınırı (m/s)
EMNIYET = 1.10
# tipik çatı tipi fan sınıfları (Ø gövde, Qmax m³/h, Pmax Pa) — katalog teyidi gerekir
FANLAR = [('ÇF-200', 600, 200), ('ÇF-250', 1100, 280), ('ÇF-315', 1900, 350), ('ÇF-400', 3200, 420),
          ('ÇF-500', 5500, 500)]


def tr(x, nd=0):
    s = f"{x:,.{nd}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def _lam(v, dh):
    re = max(v * dh / NU, 2300.0)
    return 0.25 / (math.log10(EPS / (3.7 * dh) + 5.74 / re ** 0.9)) ** 2


def yuvarlak(q, d_mm):
    """q m³/h, Ø mm -> v (m/s), R (Pa/m), Pd (Pa)"""
    d = d_mm / 1000.0
    v = q / 3600.0 / (math.pi * d * d / 4)
    return v, _lam(v, d) / d * RHO * v * v / 2, RHO * v * v / 2


def dikdortgen(q, w_mm, h_mm):
    a, b = w_mm / 1000.0, h_mm / 1000.0
    v = q / 3600.0 / (a * b)
    dh = 2 * a * b / (a + b)
    return v, _lam(v, dh) / dh * RHO * v * v / 2, RHO * v * v / 2


def esdeger_cap(w, h):
    """Huebscher eşdeğer çap (mm)"""
    return 1.30 * (w * h) ** 0.625 / (w + h) ** 0.25


def saft_kesit(q):
    for h in range(150, 601, 50):
        for w in range(h, 2 * h + 1, 50):
            if dikdortgen(q, w, h)[0] <= V_SAFT:
                return w, h
    raise ValueError(f'şaft kesiti seçilemedi: {q} m³/h')


def fan_sec(q, p):
    for ad, qm, pm in FANLAR:
        if q <= 0.85 * qm:
            pq = pm * (1 - (q / qm) ** 2)
            if pq >= p:
                return dict(ad=ad, qmax=qm, pmax=pm, p_calisma=pq)
    raise ValueError(f'fan seçilemedi: {q} m³/h {p} Pa')


def hesapla(g):
    K = g['kabul']
    q_oda, kad, D = K['q_oda'], sorted(K['kademeler']), K['baglanti_cap']
    katlar = g['katlar']
    kidx = {k['kod']: i for i, k in enumerate(katlar)}
    uyari = []
    # ---- mahaller: DIN karşılaştırması
    for m in g['mahaller']:
        m['din_s'], m['din_k'] = DIN[m['tip']]
        m['q_kabul'] = q_oda
        if 'alan_m2' in m and m['alan_m2']:
            m['n_hd'] = q_oda / (m['alan_m2'] * 2.6)          # hava değişimi (h=2,60 m asma tavan altı)
        if q_oda < m['din_k']:
            uyari.append(f"{m['kat']} {m['daire']} {m['ad']}: kabul {q_oda} < DIN kesikli {m['din_k']} m³/h")
    # ---- aspiratörler (şaft + kat + daire grubu)
    saftlar = []
    for s in g['saftlar']:
        ms = [m for m in g['mahaller'] if m['saft'] == s['ad']]
        if not ms:
            continue
        grp = {}
        for m in ms:
            grp.setdefault((kidx[m['kat']], m['daire']), []).append(m)
        asps = []
        for (ki, dr), lst in sorted(grp.items()):
            parcalar = [[m] for m in lst] if K.get('oda_basina_aspirator') else [lst]
            if not K.get('oda_basina_aspirator') and q_oda * len(lst) > kad[-1]:
                parcalar = [[m] for m in lst]
                uyari.append(f"{s['ad']} {katlar[ki]['ad']} {dr}: {q_oda * len(lst)} m³/h > {kad[-1]} kademesi, oda başına aspiratör")
            for p in parcalar:
                q = q_oda * len(p)
                kd = next(k for k in kad if k >= q)
                L = max(m.get('brans_m', 1.5) for m in p)
                v, R, pd = yuvarlak(q, D)
                dp_sur = R * L + R * FLEX_K * FLEX_L
                zs = ZETA['dirsek'] + ZETA['klape'] + ZETA['t_brans']
                dp = dp_sur + zs * pd
                asps.append(dict(ki=ki, kat=katlar[ki]['kod'], daire=dr, mahaller=p, q=q, kademe=kd, L=L, v=v, R=R,
                                 dp_sur=dp_sur, zeta=zs, pd=pd, dp=dp, ok=dp <= K['asp_basinc']))
                if dp > K['asp_basinc']:
                    uyari.append(f"{s['ad']} {katlar[ki]['ad']} {dr}: branş kaybı {dp:.0f} Pa > {K['asp_basinc']} Pa")
        # ---- şaft bölümleri (alttan üste)
        kats = sorted({a['ki'] for a in asps})
        Q = sum(a['q'] for a in asps)
        w, h = s.get('kesit') or saft_kesit(Q)
        yuk = s.get('baglanti_yuk', 2.6)
        bol = []
        top = 0
        for j, ki in enumerate(kats):
            top += sum(a['q'] for a in asps if a['ki'] == ki)
            z0 = katlar[ki]['kot'] + yuk
            if j + 1 < len(kats):
                z1 = katlar[kats[j + 1]]['kot'] + yuk
                ust = katlar[kats[j + 1]]['ad']
                zeta = ZETA['t_duz']
            else:
                z1 = g['cati_kot'] + g['cati_ustu']
                ust = 'ÇATI FANI'
                zeta = ZETA['cati_giris'] + ZETA['cati_baslik']
            v, R, pd = dikdortgen(top, w, h)
            L = z1 - z0
            bol.append(dict(alt=katlar[ki]['ad'], ust=ust, ki=ki, q=top, v=v, R=R, L=L, RL=R * L, zeta=zeta, pd=pd,
                            Z=zeta * pd, dp=R * L + zeta * pd, z0=z0, z1=z1))
        dp_saft = sum(b['dp'] for b in bol)
        p_fan = dp_saft * EMNIYET
        fan = fan_sec(Q, p_fan)
        kritik = max(asps, key=lambda a: a['dp'] + sum(b['dp'] for b in bol if b['ki'] >= a['ki']))
        dairelr = sorted({a['daire'] for a in asps}, key=lambda d: (len(d), d))
        saftlar.append(dict(ad=s['ad'], asps=asps, bol=bol, Q=Q, w=w, h=h, de=esdeger_cap(w, h), yuk=yuk,
                            dp_saft=dp_saft, p_fan=p_fan, fan=fan, kritik=kritik,
                            kritik_top=kritik['dp'] + sum(b['dp'] for b in bol if b['ki'] >= kritik['ki']),
                            daireler='D' + '-'.join(d.lstrip('D') for d in dairelr),
                            saft_ic=(w // 10 + 10, h // 10 + 10)))
    return dict(saftlar=saftlar, uyari=uyari)


if __name__ == '__main__':
    import json, sys
    r = hesapla(json.load(open(sys.argv[1])))
    for s in r['saftlar']:
        print(s['ad'], s['daireler'], s['Q'], f"{s['w']}x{s['h']}", f"şaft {s['dp_saft']:.1f} Pa fan {s['p_fan']:.1f} Pa",
              s['fan']['ad'], f"kritik {s['kritik_top']:.1f} Pa")
        for a in s['asps']:
            print('   ', a['kat'], a['daire'], [m['ad'] for m in a['mahaller']], a['q'], a['kademe'], f"{a['dp']:.1f} Pa")
        for b in s['bol']:
            print('   bölüm', b['alt'], '->', b['ust'], b['q'], f"v={b['v']:.2f} R={b['R']:.2f} L={b['L']:.2f} dp={b['dp']:.2f}")
    print(r['uyari'])
