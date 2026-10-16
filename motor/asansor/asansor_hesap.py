"""ROTAŞ asansör avan projesi hesap motoru.

Kaynak: kullanıcının gönderdiği örnekler (2026-10-12, asansör.zip):
  - MAK DAİRELİ / MAKİNE DAİRESİZ ASANSÖR avan şablonları (1. ASANSÖR AVAN PROJESİ / 1.1 TRAFİK / 1.2 KUVVET)
  - "Avan Tablosu.docx" (MMO avan proje tabloları)
  - "trafik hesabı.dwg" (eski TS yöntemi: TR, Sp, N, B2<B3)
  - KOÇEL-ELNASSER EN81-20/50 uygulama hesabı (motor gücü, KA, tampon kuvvetleri)

Şablondaki sayılar (B=52, T=101,3, P1=80026 N ...) projeden projeye DEĞİŞMEDEN kopyalanmış;
bu modül her projede değerleri yeniden hesaplar.  Tablo değerleri formülle üretilir:
  H (ortalama en yüksek dönüş katı) = N - Σ_{i=1}^{N-1} (i/N)^P
  S (ortalama durak adedi)          = N · [1 - ((N-1)/N)^P]
(Avan Tablosu.docx tablolarıyla birebir doğrulandı: N=10, P=6 -> H=9,02, S=4,69)
"""
import math
from dataclasses import dataclass, field

GN = 9.81

# ---------------------------------------------------------------- tablolar
# Tablo-1 Binada sürekli insan sayısı (b) - MMO avan tablosu
TABLO1 = {
    'konut_ilk_yatak': 2, 'konut_diger_oda': 1,
    'otel_yatak': 1,
    'is_merkezi_12m2': 1,
    'hastane_yatak': 3,
    'resmi_12m2': 1,
    'otopark_ticari_arac': 1.5, 'otopark_ozel_arac': 1,
}

# Kabin hızları (MMO avan tablosu) : (bina, durak üst sınırı) -> m/s
HIZ_TABLOSU = {
    'konut': [(9, 1.0), (14, 1.6), (19, 2.0), (999, 2.5)],
    'is_merkezi': [(5, 1.0), (10, 1.6), (15, 2.0), (19, 2.5), (999, 3.0)],
    'otel': [(6, 1.0), (10, 1.6), (15, 2.0), (19, 2.5), (999, 3.0)],
}

# Kapı açılma (ta) / kapanma (tk) zamanları [s]  (kapı genişliği mm)
KAPI_ZAMAN = {
    'teleskopik': {700: (2.5, 3.0), 800: (2.5, 3.0), 900: (2.5, 3.8), 1100: (3.0, 4.0), 1300: (3.7, 5.0)},
    'merkezden': {700: (2.0, 2.5), 800: (2.0, 2.5), 900: (2.3, 2.9), 1100: (2.5, 3.5), 1300: (2.7, 3.7)},
    'carpma': {700: (5.0, 5.0), 800: (5.0, 5.0), 900: (5.0, 5.0), 1100: (6.0, 6.0)},
}

# Tek katı geçme (hızlanma+yavaşlama kaybı) tg [s]
TG = [(0.999, 10.0), (1.00, 7.0), (1.60, 6.0), (2.00, 5.7), (2.50, 5.5), (3.50, 5.0), (5.00, 4.5), (99, 4.3)]

# Kabin kapasitesi kişi -> kg (MMO)
KAPASITE = {6: 450, 8: 630, 10: 800, 13: 1000, 16: 1275, 20: 1600, 25: 2000, 30: 2500}

# Taşınacak insan yüzdesi k (standart, yükseltilmiş)
YUZDE_K = {'konut': (0.075, 0.10), 'otel': (0.12, 0.15), 'is_merkezi': (0.15, 0.17),
           'hastane': (0.10, 0.20), 'otopark': (0.10, 0.20)}

# İzin verilen en fazla bekleme zamanı (kabul edilemez sınırı, şartlı kabul, standart, yükseltilmiş) [s]
IZUL = {'konut': (120, 120, 100, 80), 'karma': (60, 60, 50, 30), 'is_merkezi_tek': (60, 60, 50, 40),
        'is_merkezi_cok': (50, 50, 40, 30), 'otel_3': (60, 60, 50, 40), 'otel_4': (50, 50, 40, 30),
        'kamu': (40, None, 40, 30), 'hastane': (40, None, 40, 30), 'poliklinik': (60, 60, 50, 40),
        'otopark': (60, 60, 50, 40)}

# EN 81-20 Tablo 6: beyan yükü -> en büyük faydalı kabin alanı (m²)
EN81_ALAN = [(100, 0.37), (180, 0.58), (225, 0.70), (300, 0.90), (375, 1.10), (400, 1.17), (450, 1.30),
             (525, 1.45), (600, 1.60), (630, 1.66), (675, 1.75), (750, 1.90), (800, 2.00), (825, 2.05),
             (900, 2.20), (975, 2.35), (1000, 2.40), (1050, 2.50), (1125, 2.65), (1200, 2.80), (1250, 2.90),
             (1275, 2.95), (1350, 3.10), (1425, 3.25), (1500, 3.40), (1600, 3.56), (2000, 4.20), (2500, 5.00)]


def H_ort(N, P):
    """Ortalama en yüksek dönüş katı (N: ana durak üzerindeki kat, P: kişi)."""
    return N - sum((i / N) ** P for i in range(1, N))


def S_ort(N, P):
    """Ortalama durak adedi."""
    return N * (1 - ((N - 1) / N) ** P)


def hiz_sec(bina, durak):
    for ust, v in HIZ_TABLOSU.get(bina, HIZ_TABLOSU['konut']):
        if durak <= ust:
            return v


def tg_bul(V):
    for ust, t in TG:
        if V <= ust:
            return t


def kapi_zaman(tip, gen_mm):
    tab = KAPI_ZAMAN[tip]
    k = min((k for k in tab if k >= gen_mm), default=max(tab))
    return tab[k]


def en81_max_alan(Q):
    for q, a in EN81_ALAN:
        if Q <= q:
            return a
    return EN81_ALAN[-1][1] + (Q - 2500) / 100 * 0.16


# ---------------------------------------------------------------- girdiler
@dataclass
class Asansor:
    proje: str = ''
    bina: str = 'konut'               # konut / otel / is_merkezi / hastane / otopark
    izul_sinif: str = 'konut'
    makine_daireli: bool = False
    # insan sayısı
    b_toplam: float = 0               # Σb (Tablo-1) - verilmezse daireler'den hesaplanır
    daireler: list = field(default_factory=list)   # [(adet, yatak_odasi_sayisi, diger_oda_sayisi)]
    ziyaretci_ek: bool = True         # şablon: B = Σb + n·Σb  (Σb<200 n=%30, ≥200 n=%25)
    # bina / sefer
    durak: int = 5                    # toplam durak adedi
    ana_durak_ustu: int = 4           # N : ana durak üzerindeki kat sayısı (bodrum dahil edilmez)
    kat_yuk: float = 2.80             # h [m]
    seyir: float = 0                  # [m] verilmezse (durak-1)*h
    # kabin
    kisi: int = 10
    Q: float = 800                    # beyan yükü [kg]
    kabin_gen: int = 1200            # mm (dar kenar)
    kabin_der: int = 1500            # mm
    kapi_tip: str = 'teleskopik'
    kapi_gen: int = 900               # mm
    V: float = 0                      # m/s, 0 -> tablodan
    n_asansor: int = 1
    yukseltilmis: bool = False
    # kütleler [kg]
    P_kabin: float = 550              # kabin kütlesi
    q_denge: float = 0.5
    makine: float = 320
    sehpa: float = 100
    montor: float = 150
    halat_kgm: float = 0.373          # ø10 çelik halat ~0,373 kg/m (şablon)
    halat_adet: int = 4
    halat_cap: float = 10.0           # mm
    mrl: bool = False                 # makine dairesiz: makine yan perdeye ankrajlı duvar konsolunda
    aski: int = 2                     # 2/1 askı
    D_tahrik: float = 0.24            # m
    verim: float = 0.8
    kuyu_dibi: float = 1.40           # m (imar: en az 1,40)
    kuyu_ustu: float = 3.60           # m son durak - kuyu tavanı


def hesapla(a: Asansor):
    r = {}
    # --- insan sayısı
    sb = a.b_toplam or sum(n * (TABLO1['konut_ilk_yatak'] + (yo - 1 + do) * TABLO1['konut_diger_oda'])
                          for n, yo, do in a.daireler)
    ek = (0.30 if sb < 200 else 0.25) if a.ziyaretci_ek else 0
    B = sb * (1 + ek)
    r.update(sum_b=sb, ek=ek, B=B)
    # --- hız
    V = a.V or hiz_sec(a.bina, a.durak)
    r['V'] = V
    seyir = a.seyir or (a.durak - 1) * a.kat_yuk
    r['seyir'] = seyir
    r['kuyu_mesafesi'] = seyir + a.kuyu_dibi + a.kuyu_ustu
    # --- seyir zamanı
    P80 = 0.8 * a.kisi
    N = a.ana_durak_ustu
    H = H_ort(N, a.kisi)
    S = S_ort(N, a.kisi)
    tv = a.kat_yuk / V
    ta, tk = kapi_zaman(a.kapi_tip, a.kapi_gen)
    tg = tg_bul(V)
    ts = ta + tk + tg - tv
    tp = 2.2 if a.kapi_gen < 1000 else 2.0
    T = 2 * H * tv + (S + 1) * ts + 2 * P80 * tp
    R = 5 * 60 * P80 / T
    k = YUZDE_K.get(a.bina, YUZDE_K['konut'])[1 if a.yukseltilmis else 0]
    L = B * k / R
    n = max(a.n_asansor, math.ceil(L))
    I = T / n
    iz = IZUL.get(a.izul_sinif, IZUL['konut'])
    izul = iz[3] if a.yukseltilmis else iz[2]
    sartli = iz[1]
    r.update(P80=P80, H=H, S=S, tv=tv, ta=ta, tk=tk, tg=tg, ts=ts, tp=tp, T=T, R=R, k=k, L=L, n=n, I=I,
             izul=izul, izul_sartli=sartli,
             bekleme_ok=I <= izul, bekleme_sartli=(sartli is not None and izul < I <= sartli))
    # --- eski TS yöntemi (trafik hesabı.dwg) çapraz kontrol
    taa = {0.63: 2.5, 1.0: 3.0, 1.6: 3.5, 2.5: 3.5}
    ta_eski = taa[min(taa, key=lambda x: abs(x - V))]
    tt = {'carpma': 10, 'merkezden': 8 if a.kapi_gen < 1000 else 10, 'teleskopik': 10 if a.kapi_gen < 1000 else 12}[a.kapi_tip]
    Sp = S_ort(N, a.kisi)
    TR = ((2 * seyir / V) + (ta_eski + tt) * (Sp + 1) + tp * a.kisi) / n
    N5 = 300 / TR
    B3 = N5 * a.kisi * n
    K_eski = {'konut': 0.075, 'otel': 0.12, 'is_merkezi': 0.15, 'hastane': 0.25}.get(a.bina, 0.075)
    B2 = sb * K_eski
    r['eski'] = dict(ta=ta_eski, tt=tt, Sp=Sp, TR=TR, N=N5, B3=B3, B2=B2, ok=B2 < B3)
    # --- kabin alanı kontrolleri
    alan = a.kabin_gen * a.kabin_der / 1e6
    r['kabin_alan'] = alan
    r['en81_max_alan'] = en81_max_alan(a.Q)
    r['en81_ok'] = alan <= r['en81_max_alan'] + 1e-9
    r['imar_ok'] = (min(a.kabin_gen, a.kabin_der) >= 1200 and alan >= 1.80 and a.kapi_gen >= 900)
    r['kisi_Q75'] = int(a.Q // 75)
    # --- kütleler ve kuvvetler
    KA = a.P_kabin + a.q_denge * a.Q
    l_halat = a.aski * (seyir + a.kuyu_ustu) + 3.0
    Gh = a.halat_kgm * l_halat * a.halat_adet
    r.update(KA=KA, l_halat=l_halat, Gh=Gh)
    r['P1_kabin_tampon'] = 4 * GN * (a.P_kabin + a.Q)            # EN 81-20 5.2.5.4: kabin tamponu altı
    r['P2_ka_tampon'] = 4 * GN * KA                               # karşı ağırlık tamponu altı
    r['F_kuyu_ustu'] = GN * (a.makine + a.sehpa + a.montor + a.P_kabin + a.Q + Gh + KA)   # şablon 1.2.3
    S_artan = a.P_kabin + Gh + a.Q - KA
    r['S_artan'] = S_artan
    M = S_artan * a.D_tahrik / 2
    r['M_kgm'] = M
    kW = S_artan * V / (102 * a.verim)
    r['motor_kW'] = kW
    r['motor_HP'] = kW / 0.7457
    r['motor_kW_sec'] = next(x for x in (3.7, 4.4, 5.5, 7.5, 9.2, 11, 15, 18.5, 22, 30) if x >= kW * 1.1)
    return r


def f(x, d=2):
    return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def rapor(a: Asansor, r=None):
    """Şablondaki 1.1 / 1.2 bölümlerinin güncel değerlerle Türkçe metni."""
    r = r or hesapla(a)
    L = []
    L.append('1. ASANSÖR AVAN PROJESİ')
    L.append('1.1. ASANSÖR TRAFİK HESABI')
    L.append(f'Binada bulunan toplam insan sayısı  B = Σb + n·Σb = {f(r["sum_b"],0)} + {int(r["ek"]*100)}%·{f(r["sum_b"],0)} = {f(r["B"],1)} kişi')
    L.append(f'Ana durak üzerindeki kat adedi  N = {a.ana_durak_ustu}   Kabin kapasitesi = {a.kisi} kişi ({int(a.Q)} kg)')
    L.append(f'P  = %80 doluluk = 0,8 x {a.kisi} = {f(r["P80"],1)} kişi')
    L.append(f'H  = Ortalama en yüksek dönüş katı = {f(r["H"])}')
    L.append(f'S  = Ortalama durak adedi = {f(r["S"])}')
    L.append(f'V  = Kabin hızı = {f(r["V"])} m/s     h = Katlar arası mesafe = {f(a.kat_yuk)} m')
    L.append(f'tv = h / V = {f(r["tv"])} s')
    L.append(f'ts = ta + tk + tg - tv = {f(r["ta"],1)} + {f(r["tk"],1)} + {f(r["tg"],1)} - {f(r["tv"])} = {f(r["ts"])} s  (kapı {a.kapi_gen} mm {"merkezden açılır" if a.kapi_tip == "merkezden" else a.kapi_tip}, Tablo-4)')
    L.append(f'tp = Kişi transfer zamanı = {f(r["tp"],1)} s')
    L.append('1.1.1. Asansörün Bir Seferi İçin Gerekli Seyir Zamanı')
    L.append(f'T = 2·H·tv + (S+1)·ts + 2·P·tp = 2 x {f(r["H"])} x {f(r["tv"])} + ({f(r["S"])} + 1) x {f(r["ts"])} + 2 x {f(r["P80"],1)} x {f(r["tp"],1)} = {f(r["T"],1)} s')
    L.append('1.1.1.2. Gerekli Asansör Sayısının Hesabı')
    L.append(f'R = 5 x 60 x P / T = 300 x {f(r["P80"],1)} / {f(r["T"],1)} = {f(r["R"])} kişi (5 dakikada bir asansörün taşıdığı)')
    L.append(f'L = B x k / R = {f(r["B"],1)} x {f(r["k"],3)} / {f(r["R"])} = {f(r["L"])}  ->  {r["n"]} adet asansör')
    L.append('1.1.1.3. Bekleme Zamanı')
    durum = 'uygundur.' if r['bekleme_ok'] else ('şartlı kabul (taahhütname gerekir).' if r['bekleme_sartli'] else 'UYGUN DEĞİL - asansör sayısı/hız/kapasite artırılmalı.')
    isaret = '≤' if r['I'] <= r['izul'] else '>'
    L.append(f'I = T / n = {f(r["T"],1)} / {r["n"]} = {f(r["I"],1)} s  {isaret} {r["izul"]} s  {durum}')
    if r['bekleme_ok'] or r['bekleme_sartli']:
        L.append(f'{a.kisi} kişilik {f(r["V"])} m/s hızında {r["n"]} adet asansör seçilmesi uygundur.')
    else:
        L.append(f'Taşıma kapasitesi yeterli (L = {f(r["L"])} ≤ {r["n"]}); bekleme aralığı sınırı aşılıyor (bkz. kontrol notları).')
    L.append('')
    L.append('1.2. ASANSÖR KUVVET HESABI')
    L.append(f'Gk (kabin kütlesi) = {f(a.P_kabin,0)} kg   Gy (beyan yükü) = {f(a.Q,0)} kg   q = {f(a.q_denge,1)}')
    L.append(f'Karşı ağırlık = Gk + q·Gy = {f(a.P_kabin,0)} + {f(a.q_denge,1)} x {f(a.Q,0)} = {f(r["KA"],0)} kg')
    L.append(f'Halat: {a.halat_adet} x Ø{f(a.halat_cap,1)} mm çelik halat (gh = {f(a.halat_kgm,3)} kg/m), {a.aski}/1 askı')
    L.append(f'Halat kütlesi Gh = gh x lh x nh = {f(a.halat_kgm,3)} x {f(r["l_halat"],1)} x {a.halat_adet} = {f(r["Gh"],1)} kg')
    L.append('1.2.1. Kuyu Alt Boşluğu Tabanına Gelen Kuvvetler')
    L.append(f'P1 (kabin tamponu altı) = 4 x gn x (Gk + Gy) = 4 x 9,81 x ({f(a.P_kabin,0)} + {f(a.Q,0)}) = {f(r["P1_kabin_tampon"],0)} N')
    L.append(f'P2 (karşı ağırlık tamponu altı) = 4 x gn x Gka = 4 x 9,81 x {f(r["KA"],0)} = {f(r["P2_ka_tampon"],0)} N')
    L.append('1.2.3. Makine Konsolu Üzerinden Kuyu Perdesine Etki Eden Kuvvetler (duvar konsollu, alttan sehpalı)' if a.mrl else '1.2.3. Kuyu Üstü Betonuna Etki Eden Kuvvetler')
    L.append(f'F = gn x (Gmakina + Gsehpa + Gmontör + Gk + Gy + Gh + Gka) = 9,81 x ({f(a.makine,0)} + {f(a.sehpa,0)} + {f(a.montor,0)} + {f(a.P_kabin,0)} + {f(a.Q,0)} + {f(r["Gh"],0)} + {f(r["KA"],0)}) = {f(r["F_kuyu_ustu"],0)} N')
    L.append('1.2.4. Asansör Motor Gücü Hesabı')
    L.append(f'Smaks (artan yük) = Gk + Gh + Gy - Gka = {f(r["S_artan"],0)} kg   M = Smaks x D/2 = {f(r["M_kgm"],1)} kg.m')
    L.append(f'N = (1/η) x S x V / 102 = (1/{f(a.verim,2)}) x {f(r["S_artan"],0)} x {f(r["V"])} / 102 = {f(r["motor_kW"])} kW ({f(r["motor_HP"],1)} HP)  ->  seçilen {f(r["motor_kW_sec"],1)} kW')
    L.append(f'{a.kisi} kişilik {f(r["V"])} m/s hızında {f(r["motor_kW_sec"],1)} kW lık {r["n"]} adet insan asansörü tesis edilecektir.')
    L.append(f'ASANSÖR {a.halat_adet} x Ø{f(a.halat_cap,1)} mm ({a.halat_adet} HALATLI), {a.aski}/1 ASKILI OLACAKTIR.')
    L.append('')
    L.append('KONTROLLER')
    L.append(f'Kabin alanı {f(r["kabin_alan"])} m² ≤ EN 81-20 en büyük {f(r["en81_max_alan"])} m² : {"UYGUN" if r["en81_ok"] else "AŞIYOR"}')
    L.append(f'İmar (dar kenar ≥ 1,20 m, alan ≥ 1,80 m², kapı ≥ 0,90 m): {"UYGUN" if r["imar_ok"] else "UYGUN DEĞİL"}')
    e = r['eski']
    L.append(f'Eski TS yöntemi çapraz kontrol: TR={f(e["TR"],1)} s, N={f(e["N"])} sefer/5dk, B3={f(e["B3"],1)} > B2={f(e["B2"],1)} : {"UYGUN" if e["ok"] else "UYGUN DEĞİL"}')
    L.append(f'Kuyu mesafesi ≈ kuyu dibi {f(a.kuyu_dibi)} + seyir {f(r["seyir"])} + kuyu üstü {f(a.kuyu_ustu)} = {f(r["kuyu_mesafesi"])} m')
    return '\n'.join(L)


if __name__ == '__main__':
    # Örnek: şablonun kendi verisi (UFUK SEMİH GÜRBAK, 3 katlı iş yeri, 10 kişi 800 kg, seyir 8,00 m)
    a = Asansor(proje='ornek', bina='konut', durak=4, ana_durak_ustu=3, kat_yuk=2.80, seyir=8.0, b_toplam=40)
    print(rapor(a))
