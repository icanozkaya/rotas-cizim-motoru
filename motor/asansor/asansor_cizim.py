"""ROTAŞ makine dairesiz (MRL) çift asansör avan projesi çizici.

Kullanım: python3 asansor_cizim.py <proje.json> <cikis_klasoru>
Birim: model uzayı cm (gerçek ölçü). Her pafta kendi ölçeğinde A3/A1 çerçeve içinde.
Pafta dizilimi (soldan sağa): kapak -> konum planı -> hesap 1 -> hesap 2 -> tablolar -> kuyu planı 1/20
-> kuyu dibi yükleri + son döşeme (motor asma) planı 1/20 -> kesit yandan 1/50 -> kesit karşıdan 1/50 -> detaylar 1/10
"""
import json, math, os, pickle, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dxfyaz import Cizim
from asansor_hesap import Asansor, hesapla, rapor, f, TABLO1, HIZ_TABLOSU, KAPI_ZAMAN, TG, KAPASITE, YUZDE_K, IZUL, EN81_ALAN

SIVA = 2.5


def katmanlar(c):
    for ad, rk, tip in [('ASN-CERCEVE', 7, 'CONTINUOUS'), ('ASN-ANTET', 4, 'CONTINUOUS'), ('ASN-YAZI', 4, 'CONTINUOUS'),
                        ('ASN-BASLIK', 5, 'CONTINUOUS'), ('ASN-DUVAR', 7, 'CONTINUOUS'), ('ASN-TARAMA', 8, 'CONTINUOUS'),
                        ('ASN-SIVA', 8, 'CONTINUOUS'), ('ASN-KIRIS', 1, 'DASHED'), ('ASN-KABIN', 5, 'CONTINUOUS'),
                        ('ASN-RAY', 1, 'CONTINUOUS'), ('ASN-KA', 30, 'CONTINUOUS'), ('ASN-KAPI', 3, 'CONTINUOUS'),
                        ('ASN-EKSEN', 8, 'CENTER'), ('ASN-OLCU', 3, 'CONTINUOUS'), ('ASN-KOT', 2, 'CONTINUOUS'),
                        ('ASN-MOTOR', 6, 'CONTINUOUS'), ('ASN-HALAT', 6, 'CONTINUOUS'), ('ASN-YUK', 1, 'CONTINUOUS'),
                        ('ASN-UYARI', 1, 'CONTINUOUS'), ('ASN-MIMARI', 8, 'CONTINUOUS'), ('ASN-ISARET', 1, 'CONTINUOUS'),
                        ('ASN-TABLO', 4, 'CONTINUOUS'), ('ASN-ELEKTRIK', 3, 'CONTINUOUS'), ('ASN-ELEKTRIK-YAZI', 4, 'CONTINUOUS')]:
        c.lay(ad, rk, tip)


# ---------------------------------------------------------------------------- pafta çerçevesi
KALEM = {7: 0.50, 5: 0.35, 6: 0.35, 1: 0.30, 30: 0.30, 4: 0.25, 3: 0.18, 2: 0.18, 8: 0.13}   # renk -> mm (ozalit ctb)
SERIT_H = 594            # ozalit şerit yüksekliği (mm) - tüm paftalar aynı yükseklikte
SERIT_OLCEK = 50         # şeridin çizim ölçeği; diğer ölçekler geometriyle ölçeklenir


class Pafta:
    """Ozalit şeridinde bir hücre (A4/A3 yatay/dikey). Yerel çizim: model cm gerçek ölçü, k = ölçek/10.
    Hücre bitince kayıtlar 50/ölçek ile ölçeklenip şeritteki (X, Y) yerine taşınır (şerit 1/50 çizilir).
    Çerçeve/ayırıcı çizgileri şerit sonunda tek sefer çizilir (çizgiler üst üste binmesin)."""
    def __init__(self, c, olcek, gen_mm, yuk_mm, baslik='', no=1):
        self.c, self.k, self.olcek = c, olcek / 10.0, olcek
        self.bas = len(c.R)
        self.Wmm, self.Hmm = gen_mm, yuk_mm
        self.x0, self.y0, self.W, self.H = 0.0, 0.0, gen_mm * self.k, yuk_mm * self.k
        k = self.k
        c.L('ASN-ANTET', (4 * k, 20 * k), (self.W - 4 * k, 20 * k))
        c.T('ASN-BASLIK', (8 * k, 11 * k), baslik, 4.5 * k)
        c.T('ASN-ANTET', (8 * k, 5 * k), f'ÖLÇEK : 1/{olcek}', 2.8 * k)
        c.rect('ASN-ANTET', self.W - 26 * k, 5 * k, self.W - 4 * k, 17 * k)
        c.T('ASN-ANTET', (self.W - 15 * k, 11 * k), f'A-{no:02d}', 5.5 * k, 0, 'MC')

    def ic(self):
        k = self.k
        return 8 * k, 26 * k, self.W - 8 * k, self.H - 8 * k

    def h(self, mm):
        return mm * self.k

    def tasi(self, X, Y):
        f = SERIT_OLCEK / self.olcek
        R = self.c.R
        mp = lambda p: (X + p[0] * f, Y + p[1] * f)
        for i in range(self.bas, len(R)):
            r = R[i]
            if r[0] == 'L': R[i] = ('L', r[1], mp(r[2]), mp(r[3]))
            elif r[0] == 'P': R[i] = ('P', r[1], [mp(q) for q in r[2]], r[3])
            elif r[0] == 'C': R[i] = ('C', r[1], mp(r[2]), r[3] * f)
            elif r[0] == 'A': R[i] = ('A', r[1], mp(r[2]), r[3] * f, r[4], r[5])
            elif r[0] == 'T': R[i] = ('T', r[1], mp(r[2]), r[3], r[4] * f, r[5], r[6])
        m5 = SERIT_OLCEK / 10
        self.x0, self.y0, self.W, self.H, self.k = X, Y, self.Wmm * m5, self.Hmm * m5, m5


SABLON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kutuphane', 'asansor')


def sablon_yapistir(c, ad, X, Y, lay_cizgi, lay_yazi, degistir=None, olcek=1.0):
    """kutuphane/asansor/<ad>.json şablonunu (X, Y) noktasına yapıştırır. degistir: {(x,y): yeni_metin}"""
    d = json.load(open(os.path.join(SABLON, ad + '.json'), encoding='utf-8'))
    degistir = degistir or {}
    mp = lambda p: (X + p[0] * olcek, Y + p[1] * olcek)
    for r in d['kayitlar']:
        if r[0] == 'L': c.L(lay_cizgi, mp(r[2]), mp(r[3]))
        elif r[0] == 'P': c.P(lay_cizgi, [mp(q) for q in r[2]], r[3])
        elif r[0] == 'C': c.C(lay_cizgi, mp(r[2]), r[3] * olcek)
        elif r[0] == 'T':
            key = (round(r[2][0]), round(r[2][1]))
            metin = degistir.get(key, r[3])
            if metin is None: continue
            h = r[4]
            if isinstance(metin, tuple): metin, h = metin
            c.T(lay_yazi, mp(r[2]), metin, h * olcek, r[5], r[6])
    return d['gen'] * olcek, d['yuk'] * olcek


def yazi_blok(c, x, y, satirlar, h, lay='ASN-YAZI', ara=1.65):
    for i, s in enumerate(satirlar):
        bold = s.startswith('#')
        c.T('ASN-BASLIK' if bold else lay, (x, y - i * h * ara), s.lstrip('# '), h * (1.15 if bold else 1.0))
    return y - len(satirlar) * h * ara


def tablo(c, x, y, sutun_gen, satirlar, h, baslik=None):
    """Basit tablo: sutun_gen cm listesi, satirlar = [[...],...]; ilk satır başlık."""
    rh = h * 2.0
    if baslik:
        c.T('ASN-BASLIK', (x, y + h * 0.8), baslik, h * 1.1)
    W = sum(sutun_gen)
    n = len(satirlar)
    c.rect('ASN-TABLO', x, y - n * rh, x + W, y)
    for i in range(1, n):
        c.L('ASN-TABLO', (x, y - i * rh), (x + W, y - i * rh))
    cx = x
    for wi in sutun_gen[:-1]:
        cx += wi
        c.L('ASN-TABLO', (cx, y), (cx, y - n * rh))
    for i, row in enumerate(satirlar):
        cx = x
        for wi, s in zip(sutun_gen, row):
            c.T('ASN-BASLIK' if i == 0 else 'ASN-TABLO', (cx + h * 0.4, y - i * rh - rh * 0.68), str(s), h)
            cx += wi
    return y - n * rh


# ---------------------------------------------------------------------------- kuyu geometrisi
def kuyu_yerlesim(K, P):
    """K: proje json. Kuyular soldan sağa; her biri dict(x0, gen_kaba, gen_net, kiris)."""
    ky = []
    x = 0.0
    dw = K['ara_duvar']
    for i, (g, kiris) in enumerate(K['kuyular']):
        net = (kiris if kiris else g - 2 * SIVA)
        ky.append(dict(ad=f'ASANSÖR-{i+1}', x0=x, gen=g, kiris=kiris, net=net))
        x += g + dw
    return ky


def kabin_x0(K, k_):
    """Kabinin sol kenarı (kuyu yerel x). Kiriş soldaysa kiriş yüzünden başlar."""
    sol = k_['x0'] + SIVA
    if k_['kiris'] and K.get('kiris_taraf', 'sag') == 'sol':
        sol += k_['gen'] - SIVA - k_['kiris']
    return sol + 12.5


def kuyu_plan(c, ox, oy, K, s=1.0, detay=True, h=8.0, ad_goster=True):
    """Kuyu planı (kapılar +y yönünde). ox,oy: sol-alt kaba iç köşe. s: ölçek çarpanı (1 = gerçek)."""
    D = K['derinlik']; dw = K['ara_duvar']; tw = K['dis_duvar']
    ky = kuyu_yerlesim(K, None)
    toplam = ky[-1]['x0'] + ky[-1]['gen']
    X = lambda x: ox + x * s
    Y = lambda y: oy + y * s
    # dış duvarlar ve ara duvar (betonarme perde önerisi taralı)
    duvarlar = [(-tw, -tw, 0, D + tw), (toplam, -tw, toplam + tw, D + tw), (-tw, -tw, toplam + tw, 0)]
    for k_ in ky[:-1]:
        duvarlar.append((k_['x0'] + k_['gen'], -tw, k_['x0'] + k_['gen'] + dw, D))
    # kapı duvarı (kat kapısı boşluklu)
    for k_ in ky:
        kx = k_['x0']
        kc = kabin_x0(K, k_) + K['kabin_gen'] / 2   # kabin ekseni
        duvarlar.append((kx - (tw if k_ is ky[0] else 0), D, kc - 50, D + tw))
        duvarlar.append((kc + 50, D, kx + k_['gen'] + (tw if k_ is ky[-1] else dw / 2), D + tw))
    for (a, b, cc, d) in duvarlar:
        c.rect('ASN-DUVAR', X(a), Y(b), X(cc), Y(d))
        c.tara('ASN-TARAMA', X(a), Y(b), X(cc), Y(d), ara=6 * s if s >= 1 else 6)
    for k_ in ky:
        x0, g = k_['x0'], k_['gen']
        # sıva çizgisi
        c.rect('ASN-SIVA', X(x0 + SIVA), Y(SIVA), X(x0 + g - SIVA), Y(D - SIVA))
        if k_['kiris']:
            # kiriş, kuyunun SOL ya da SAĞ yüzünde (K['kiris_taraf'])
            gir = g - SIVA - k_['kiris']
            if K.get('kiris_taraf', 'sag') == 'sag':
                c.rect('ASN-KIRIS', X(x0 + g - SIVA - gir), Y(SIVA), X(x0 + g - SIVA), Y(D - SIVA))
                c.T('ASN-KIRIS', (X(x0 + g - SIVA - gir / 2), Y(D / 2)), 'KİRİŞ', h * 0.8, 90, 'MC')
            else:
                c.rect('ASN-KIRIS', X(x0 + SIVA), Y(SIVA), X(x0 + SIVA + gir), Y(D - SIVA))
                c.T('ASN-KIRIS', (X(x0 + SIVA + gir / 2), Y(D / 2)), 'KİRİŞ', h * 0.8, 90, 'MC')
        # kabin rayları (T89) kabinin iki yanında, kabin derinliği ortasında
        kab_x0 = kabin_x0(K, k_); kab_x1 = kab_x0 + K['kabin_gen']
        kab_y1 = D - SIVA - 13.0; kab_y0 = kab_y1 - K['kabin_der']
        ym = (kab_y0 + kab_y1) / 2
        for rx, yon in ((kab_x0 - 1.5, -1), (kab_x1 + 1.5, 1)):
            c.rect('ASN-RAY', X(rx + yon * 0.0), Y(ym - 4.45), X(rx + yon * 1.6), Y(ym + 4.45))
            c.rect('ASN-RAY', X(rx + yon * 1.6), Y(ym - 0.8), X(rx + yon * 8.9), Y(ym + 0.8))
        # kabin
        c.rect('ASN-KABIN', X(kab_x0), Y(kab_y0), X(kab_x1), Y(kab_y1))
        c.rect('ASN-KABIN', X(kab_x0 + 2), Y(kab_y0 + 2), X(kab_x1 - 2), Y(kab_y1 - 2))
        kc = kab_x0 + K['kabin_gen'] / 2
        # kabin kapısı + kat kapısı (teleskopik 2 kanat)
        for yy in (kab_y1 + 2, D + 2):
            c.rect('ASN-KAPI', X(kc - 47), Y(yy), X(kc + 2), Y(yy + 3))
            c.rect('ASN-KAPI', X(kc - 2), Y(yy + 3.5), X(kc + 47), Y(yy + 6.5))
        c.L('ASN-KAPI', (X(kc - 45), Y(D + tw)), (X(kc + 45), Y(D + tw)))
        # karşı ağırlık yanda (boş tarafta)
        bos0 = kab_x1 + 10.5
        bos1 = x0 + g - SIVA - (g - SIVA - k_['kiris'] if (k_['kiris'] and K.get('kiris_taraf', 'sag') == 'sag') else 0)
        kaw = min(12.0, max(6.0, bos1 - bos0 - 16))
        kax = (bos0 + bos1) / 2
        c.rect('ASN-KA', X(kax - kaw / 2), Y(ym - 35), X(kax + kaw / 2), Y(ym + 35))
        for yy in (ym - 41, ym + 41):   # K.A. rayları T50
            c.rect('ASN-RAY', X(kax - 2.5), Y(yy - 2.5), X(kax + 2.5), Y(yy + 2.5))
        if detay:
            c.L('ASN-EKSEN', (X(kc), Y(-tw - 25)), (X(kc), Y(D + tw + 25)))
            c.L('ASN-EKSEN', (X(x0 - 10), Y(ym)), (X(x0 + g + 10), Y(ym)))
            c.T('ASN-KABIN', (X(kc), Y(ym + 18)), f"KABİN {K['kabin_gen']:.0f}x{K['kabin_der']:.0f}", h, 0, 'MC')
            c.T('ASN-KABIN', (X(kc), Y(ym)), f"{K['kisi']} KİŞİ / {K['Q']:.0f} kg", h, 0, 'MC')
            c.T('ASN-KABIN', (X(kc), Y(ym - 18)), f"{(K['kabin_gen']*K['kabin_der'])/1e4:.2f} m²", h, 0, 'MC')
            c.T('ASN-KA', (X(kax), Y(ym - 48)), 'K.A.', h * 0.8, 0, 'TC')
            c.T('ASN-KAPI', (X(kc), Y(D + tw + 8)), 'KAT KAPISI 90/210 TELESKOPİK OTOMATİK', h * 0.75, 0, 'BC')
        if ad_goster:
            c.T('ASN-BASLIK', (X(x0 + g / 2), Y(-tw - (40 if detay else 20) * (1 if s >= 1 else 1))), k_['ad'], h * 1.1, 0, 'TC')
    return ky, toplam


# ---------------------------------------------------------------------------- mimari konum planı
def mimari_kopya(c, flat_pkl, pencere, ox, oy, kuyu_kutulari, h_max=30):
    fl = pickle.load(open(flat_pkl, 'rb'))
    x0, y0, x1, y1 = pencere
    ins = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    sx = lambda p: (p[0] - x0 + ox, p[1] - y0 + oy)
    ATLA = {'iç alan', 'ARABA', 'PV PANEL', 'YZ30', 'AUDIT_D_050129170658-0'}
    n = 0
    for r in fl:
        if r[1] in ATLA: continue
        if r[0] == 'L':
            if ins(r[2][0]) and ins(r[2][1]): c.L('ASN-MIMARI', sx(r[2][0]), sx(r[2][1])); n += 1
        elif r[0] == 'P':
            pts = r[2]
            if all(ins(p) for p in pts): c.P('ASN-MIMARI', [sx(p) for p in pts]); n += 1
        elif r[0] == 'C':
            if ins(r[2][:2]): c.C('ASN-MIMARI', sx(r[2][:2]), r[2][2])
        elif r[0] == 'T':
            p, s, h = r[2]
            if ins(p) and 6 <= h <= h_max:
                s = re.sub(r'\\[AaCcFfHhQqTtWwpLlOo][^;]*;?', '', s).replace('{', '').replace('}', '').replace('\\P', ' ').strip()
                if s and len(s) < 40 and not s.startswith('Taban') and not s.startswith('Duvar') and not s.startswith('Tavan'):
                    c.T('ASN-MIMARI', sx(p), s, h)
    for (a, b, cc, d, ad) in kuyu_kutulari:
        A, B = sx((a, b)), sx((cc, d))
        c.rect('ASN-ISARET', A[0], A[1], B[0], B[1])
        c.L('ASN-ISARET', A, B); c.L('ASN-ISARET', (A[0], B[1]), (B[0], A[1]))
    return n


# ---------------------------------------------------------------------------- ana çizim
def ciz(K, cikis):
    c = Cizim(); katmanlar(c)
    a = Asansor(proje=K['blok'], bina='konut', daireler=[tuple(d) for d in K['daireler']], durak=len(K['durak_kotlari']),
                ana_durak_ustu=K['ana_durak_ustu'], kat_yuk=K['seyir'] / (len(K['durak_kotlari']) - 1), seyir=K['seyir'],
                kisi=K['kisi'], Q=K['Q'], kabin_gen=int(K['kabin_gen'] * 10), kabin_der=int(K['kabin_der'] * 10),
                n_asansor=len(K['kuyular']), kuyu_dibi=K['kuyu_dibi'], kuyu_ustu=K['kuyu_ustu'], P_kabin=K['P_kabin'])
    r = hesapla(a)
    paftalar = []
    proje = K['proje']; proje['blok'] = K['blok']
    m5 = SERIT_OLCEK / 10
    SOL = 20 * m5                        # cilt payı
    yer = dict(x=SOL, ust_gen=0.0)       # sütun takibi (model birimi)
    hucreler = []                        # (X, Y, W, H) ayırıcı çizgiler için
    bekleyen = []

    def bitir():
        while bekleyen:
            pf, X, Y = bekleyen.pop()
            pf.tasi(X, Y)

    def yeni(olcek, gen_mm, baslik, konum='tam'):
        """konum: 'tam' (594 yükseklik), 'ust' / 'alt' (297 yükseklik, aynı sütun)."""
        bitir()
        if konum == 'alt':
            X, Y, H = yer['x'], 0.0, 297
        elif konum == 'ust':
            X, Y, H = yer['x'], 297 * m5, 297
        else:
            X, Y, H = yer['x'], 0.0, SERIT_H
        p = Pafta(c, olcek, gen_mm, H, baslik, len(paftalar) + 1)
        paftalar.append((baslik, p)); bekleyen.append((p, X, Y)); hucreler.append((X, Y, gen_mm * m5, H * m5))
        if konum == 'ust':
            yer['ust_gen'] = gen_mm * m5
        else:
            yer['x'] += max(gen_mm * m5, yer['ust_gen'] if konum == 'alt' else 0)
            yer['ust_gen'] = 0.0
        return p

    ky = kuyu_yerlesim(K, None)
    ust_kat = K['durak_kotlari'][-1]
    alt_kat = K['durak_kotlari'][0]
    dip = alt_kat - K['kuyu_dibi']
    tavan = K['son_doseme_alt']
    kalin = K['son_doseme_kalinlik_oneri']

    # ---------------- 1 KAPAK (kullanıcının kapak şablonu, alanlar dolduruldu) + NOTLAR
    kd = {(525, 1256): (proje.get('sahip', ''), min(40.0, 980.0 / max(1, len(proje.get('sahip', ''))) / 0.62)), (195, 1198): proje['il'], (195, 1163): proje['ilce'],
          (195, 1128): proje['mahalle'], (195, 1093): proje['ada'], (195, 1058): proje['parsel'],
          (195, 1023): K.get('yibf', '-'), (195, 988): str(K['kat_adedi']), (195, 953): str(len(K['durak_kotlari'])),
          (790, 1198): f"{K['Q']:.0f} kg x {len(ky)}", (790, 1163): f"{f(r['V'])} m/s", (790, 1128): f"{f(K['seyir'])} m",
          (790, 1093): '90 (teleskopik)', (790, 1058): ' + '.join(f"{k_['gen']:.0f}x{K['derinlik']:.0f}" for k_ in ky),
          (790, 1023): f"{K['kabin_gen']*10:.0f}x{K['kabin_der']*10:.0f}", (790, 988): '2/1', (790, 953): 'T89 / T50',
          (170, 249): f"{K['blok']} BLOK", (615, 248): 'MAKİNE DAİRESİZ ÇİFT', (783, 574): f"{proje['ilce']} BELEDİYESİ"}
    bitir()
    kw, kh = sablon_yapistir(c, 'kapak_sablon', SOL, 297 * m5, 'ASN-ANTET', 'ASN-ANTET', kd)
    hucreler.append((SOL, 297 * m5, kw, kh)); yer['ust_gen'] = kw
    p = yeni(50, 210, 'KONTROL VE NOTLAR', 'alt'); k = p.k; X0, Y0, X1, Y1 = p.ic()
    def sar(satirlar, n=118):
        out = []
        for s_ in satirlar:
            while len(s_) > n:
                cut = s_.rfind(' ', 0, n); cut = cut if cut > 20 else n
                out.append(s_[:cut]); s_ = '   ' + s_[cut:].strip()
            out.append(s_)
        return out
    notlar = ['# KUYU İÇ ÖLÇÜLERİ VE SON DÖŞEME KONTROLÜ (mimariden ölçülmüştür)'] + K['olcu_notlari'] + \
             ['', '# KOORDİNASYON NOTLARI'] + K['koordinasyon']
    yy = yazi_blok(c, X0, Y1 - 4 * k, sar(notlar), 2.3 * k)
    kal = [['Renk', 'Kalem', 'Kullanım']] + [[str(rk), f'{mm:.2f}', u] for rk, mm, u in [
        (7, 0.50, 'duvar, çerçeve'), (5, 0.35, 'kabin, başlık'), (6, 0.35, 'motor, halat'), (1, 0.30, 'ray, kiriş, yük'),
        (30, 0.30, 'karşı ağırlık'), (4, 0.25, 'yazı, tablo, antet, elektrik yazı'), (3, 0.18, 'ölçü, kapı, elektrik'),
        (2, 0.18, 'kot'), (8, 0.13, 'tarama, sıva, mimari')]]
    tablo(c, X0, yy - 8 * k, [16 * k, 18 * k, 70 * k], kal, 2.0 * k, 'KALEM KALINLIKLARI (ozalit / ctb)')

    # ---------------- 2 KONUM PLANI (mimariden)
    if K.get('mimari'):
        m = K['mimari']
        olc = m.get('olcek', 100)
        px0, py0, px1, py1 = m['pencere']
        gmm = max(210, int((px1 - px0) * 10 / olc + 30))
        p = yeni(olc, gmm, f"ASANSÖR KONUM PLANI - {m['kat_adi']}", 'tam'); k = p.k; X0, Y0, X1, Y1 = p.ic()
        ox = X0 + (X1 - X0 - (px1 - px0)) / 2; oy = Y0 + (Y1 - Y0 - (py1 - py0)) / 2
        kut = [tuple(b) + (f'ASN-{i+1}',) for i, b in enumerate(m['kuyu_kutulari'])]
        mimari_kopya(c, m['flat'], m['pencere'], ox, oy, kut)
        for i, b in enumerate(m['kuyu_kutulari']):
            cx = (b[0] + b[2]) / 2 - px0 + ox; cy = (b[1] + b[3]) / 2 - py0 + oy
            c.T('ASN-ISARET', (cx, cy), f'ASN-{i+1}', 3.0 * k, 0, 'MC')
        c.T('ASN-BASLIK', (X0, Y1 - 4 * k), f"{m['kat_adi']} - ASANSÖR KONUMU (mimariden)", 4.5 * k)
        c.T('ASN-YAZI', (X0, Y1 - 10 * k), 'Çarpılı alanlar: asansör kuyuları (ASN-1, ASN-2).', 2.6 * k)

    # ---------------- 3 HESAP-1 (trafik) ve 4 HESAP-2 (kuvvet)
    metin = rapor(a, r).split('\n')
    i2 = metin.index('1.2. ASANSÖR KUVVET HESABI')
    p = yeni(50, 420, 'HESAP-1 TRAFİK HESABI', 'ust'); k = p.k; X0, Y0, X1, Y1 = p.ic()
    giris = ['# GİRDİLER (mimariden)',
             f"Daireler: " + ', '.join(f'{n} adet {yo}+{do}' for n, yo, do in K['daireler']) + f"  ->  Σb = {f(r['sum_b'],0)} kişi (Tablo-1: ilk yatak odası 2, diğer odalar 1)",
             f"Durak kotları: " + ', '.join(f'{ad} {f(z)}' for ad, z in zip(K['durak_adlari'], K['durak_kotlari'])) + f"   Seyir = {f(K['seyir'])} m",
             f"Ana durak: Zemin kat. Ana durak üzerindeki kat sayısı N = {K['ana_durak_ustu']}" + ('  (bodrum durağı hesaba katılmaz)' if alt_kat < 0 else ''),
             f"Ortalama kat yüksekliği h = seyir / (durak-1) = {f(a.kat_yuk)} m.  Asansör sayısı n = {len(ky)} (çift asansör)", '']
    yy = yazi_blok(c, X0, Y1 - 5 * k, giris, 3.0 * k)
    yazi_blok(c, X0, yy, ['# ' + metin[0], '# ' + metin[1]] + metin[2:i2], 3.0 * k)
    p = yeni(50, 420, 'HESAP-2 KUVVET / MOTOR / KONTROLLER', 'alt'); k = p.k; X0, Y0, X1, Y1 = p.ic()
    kv = ['# ' + metin[i2]] + metin[i2 + 1:]
    kv = ['# ' + s if s and s[0].isdigit() and '.' in s[:6] and s.split(' ')[0].count('.') >= 2 else s for s in kv]
    yazi_blok(c, X0, Y1 - 5 * k, kv, 2.8 * k)

    # ---------------- 5 TABLOLAR
    p = yeni(50, 420, 'TABLOLAR', 'ust'); k = p.k; X0, Y0, X1, Y1 = p.ic()
    h = 2.2 * k
    yb = tablo(c, X0, Y1 - 8 * k, [45 * k, 60 * k, 12 * k], [['Bina tipi', 'Bağımsız bölüm', 'b'],
               ['Konut', 'her dairede ilk yatak odası', '2'], ['Konut', 'diğer odaların her biri', '1'], ['Otel', 'her yatak', '1'],
               ['İş merkezi', 'çalışma alanının her 12 m²si', '1'], ['Hastane', 'her yatak', '3']], h, 'Tablo-1 Binada sürekli insan sayısı (b)')
    tablo(c, X0, yb - 10 * k, [30 * k, 30 * k, 22 * k], [['Bina', 'Durak', 'V (m/s)'], ['Konut', '2-9', '1,0'], ['Konut', '10-14', '1,6'],
          ['Konut', '15-19', '2,0'], ['Konut', '20+', '>=2,5']], h, 'Tablo-2 Kabin hızları')
    xx = X0 + 135 * k
    yb = tablo(c, xx, Y1 - 8 * k, [28 * k, 20 * k, 20 * k, 20 * k, 20 * k], [['Kapı mm', 'Telesk. ta', 'Telesk. tk', 'Merkez ta', 'Merkez tk'],
               ['700', '2,5', '3,0', '2,0', '2,5'], ['800', '2,5', '3,0', '2,0', '2,5'], ['900', '2,5', '3,8', '2,3', '2,9'],
               ['1100', '3,0', '4,0', '2,5', '3,5'], ['1300', '3,7', '5,0', '2,7', '3,7']], h, 'Tablo-4 Kapı açılma/kapanma zamanları (s)')
    yb = tablo(c, xx, yb - 10 * k, [22 * k] + [13 * k] * 8, [['V m/s', '<1', '1,0', '1,6', '2,0', '2,5', '3,5', '5,0', '>5'],
               ['tg (s)', '10', '7,0', '6,0', '5,7', '5,5', '5,0', '4,5', '4,3']], h, 'Tablo-6 Tek katı geçme zamanı')
    yb = tablo(c, xx, yb - 10 * k, [22 * k] + [13 * k] * 8, [['Kişi', '6', '8', '10', '13', '16', '20', '25', '30'],
               ['kg', '450', '630', '800', '1000', '1275', '1600', '2000', '2500']], h, 'Tablo-7 Kabin kapasitesi')
    yb = tablo(c, xx, yb - 10 * k, [35 * k, 25 * k, 30 * k], [['Bina', 'Standart', 'Yükseltilmiş'], ['Konut', '%7,5', '%10'],
               ['Otel', '%12', '%15'], ['İş merkezi', '%15', '%17']], h, 'Tablo-9 Taşınacak insan yüzdesi (k)')
    tablo(c, xx, yb - 10 * k, [35 * k, 22 * k, 22 * k, 22 * k], [['Sınıf', 'Şartlı', 'Standart', 'Yüks.'], ['Konut', '120 s', '100 s', '80 s'],
          ['Karma', '60 s', '50 s', '30 s']], h, 'Tablo-10 İzin verilen en fazla bekleme zamanı')
    c.T('ASN-YAZI', (X0, Y0 + 30 * k), 'H ve S değerleri tablo yerine formülle hesaplanmıştır (MMO tablolarıyla aynı sonuç):', h)
    c.T('ASN-YAZI', (X0, Y0 + 24 * k), 'H = N - Σ(i/N)^P  (i=1..N-1)      S = N·[1 - ((N-1)/N)^P]', h)

    # ---------------- 6 KUYU PLANI 1/20
    p = yeni(20, 420, 'KUYU YERLEŞİM PLANI', 'alt'); k = p.k; X0, Y0, X1, Y1 = p.ic()
    toplam = ky[-1]['x0'] + ky[-1]['gen']
    ox = X0 + (X1 - X0 - toplam) / 2 - 40; oy = Y0 + (Y1 - Y0) * 0.50
    kuyu_plan(c, ox, oy, K, 1.0, True, 2.5 * k)
    D = K['derinlik']; tw = K['dis_duvar']
    for k_ in ky:
        c.olcu('ASN-OLCU', (ox + k_['x0'], oy + D + tw), (ox + k_['x0'] + k_['gen'], oy + D + tw), 45, 2.2 * k, f"{k_['gen']:.0f} (kaba)")
        c.olcu('ASN-OLCU', (ox + k_['x0'] + SIVA, oy + D + tw), (ox + k_['x0'] + k_['gen'] - SIVA, oy + D + tw), 80, 2.2 * k,
               f"net {k_['gen']-2*SIVA:.0f}" + (f" / kiriş altı {k_['kiris']:.1f}" if k_['kiris'] else ''))
    c.olcu('ASN-OLCU', (ox + toplam + tw, oy), (ox + toplam + tw, oy + D), -35, 2.2 * k, f'{D:.0f} (kaba)')
    c.olcu('ASN-OLCU', (ox + toplam + tw, oy + SIVA), (ox + toplam + tw, oy + D - SIVA), -70, 2.2 * k, f'net {D-2*SIVA:.0f}')
    tx = X0 + 2 * k
    tablo(c, X0 + 20 * k, Y0 + 95 * k, [40 * k, 70 * k, 70 * k], [['', ky[0]['ad'], ky[-1]['ad'] if len(ky) > 1 else ''],
          ['Kuyu kaba (cm)', f"{ky[0]['gen']:.0f} x {D:.0f}", f"{ky[-1]['gen']:.0f} x {D:.0f}"],
          ['Kuyu net (cm)', f"{ky[0]['net']:.1f} x {D-2*SIVA:.1f}", f"{ky[-1]['net']:.1f} x {D-2*SIVA:.1f}"],
          ['Kabin (mm)', f"{K['kabin_gen']*10:.0f} x {K['kabin_der']*10:.0f}", f"{K['kabin_gen']*10:.0f} x {K['kabin_der']*10:.0f}"],
          ['Kapasite / hız', f"{K['Q']:.0f} kg / {f(r['V'])} m/s", f"{K['Q']:.0f} kg / {f(r['V'])} m/s"],
          ['Kapı', '900 telesk. otomatik', '900 telesk. otomatik'], ['Askı / ray', '2/1  T89 + T50', '2/1  T89 + T50']], 2.2 * k)
    c.T('ASN-UYARI', (X0, Y1 - 6 * k), 'Kabin ve karşı ağırlık yerleşimi şematiktir; firma uygulama projesinde ray/konsol yerleri kesinleşecektir.', 2.3 * k)
    c.T('ASN-UYARI', (X0, Y1 - 11 * k), 'Ray konsolları için kuyu duvarları betonarme perde veya her katta betonarme hatıl olmalıdır (statik).', 2.3 * k)

    # ---------------- DETAYLAR 1/20 (üst) - altında kuyu dibi / son döşeme
    p = yeni(20, 594, 'KAT KAPISI / KABİN / BUTONYER DETAYLARI', 'ust'); k = p.k; X0, Y0, X1, Y1 = p.ic()
    # kat kapısı görünüşü 90/210
    gx, gy = X0 + 50, Y0 + (Y1 - Y0) * 0.40
    c.rect('ASN-DUVAR', gx - 40, gy, gx + 170, gy + 260)
    c.rect('ASN-KAPI', gx + 20, gy, gx + 110, gy + 210)
    c.L('ASN-KAPI', (gx + 65, gy), (gx + 65, gy + 210))
    c.rect('ASN-KAPI', gx + 15, gy + 210, gx + 115, gy + 225)
    c.rect('ASN-KAPI', gx + 125, gy + 100, gx + 137, gy + 125)
    c.C('ASN-KAPI', (gx + 131, gy + 117), 2.2); c.C('ASN-KAPI', (gx + 131, gy + 108), 2.2)
    c.T('ASN-YAZI', (gx + 140, gy + 112), 'çağrı butonu', 2.0 * k, 0, 'ML')
    c.olcu('ASN-OLCU', (gx + 20, gy), (gx + 110, gy), -20, 2.0 * k, '90')
    c.olcu('ASN-OLCU', (gx + 20, gy), (gx + 20, gy + 210), 25, 2.0 * k, '210')
    c.T('ASN-BASLIK', (gx - 40, gy - 45), 'KAT KAPISI GÖRÜNÜŞÜ (teleskopik otomatik, E120/EI60 yangın sınıfı)', 2.5 * k)
    # kabin planı
    kx, kyy = X0 + 245, gy + 40
    c.rect('ASN-KABIN', kx, kyy, kx + K['kabin_gen'], kyy + K['kabin_der'])
    c.rect('ASN-KABIN', kx + 3, kyy + 3, kx + K['kabin_gen'] - 3, kyy + K['kabin_der'] - 3)
    c.L('ASN-KAPI', (kx + 15, kyy + K['kabin_der']), (kx + 105, kyy + K['kabin_der']))
    c.rect('ASN-KABIN', kx + K['kabin_gen'] - 10, kyy + 40, kx + K['kabin_gen'] - 3, kyy + 100)
    c.T('ASN-YAZI', (kx + K['kabin_gen'] - 14, kyy + 70), 'butonyer', 1.8 * k, 90, 'MC')
    c.L('ASN-KABIN', (kx + 3, kyy + 90), (kx + 3, kyy + 90))
    c.T('ASN-YAZI', (kx + 10, kyy + 15), 'tutamak h=90', 1.8 * k)
    c.olcu('ASN-OLCU', (kx, kyy), (kx + K['kabin_gen'], kyy), -20, 2.0 * k, f"{K['kabin_gen']:.0f}")
    c.olcu('ASN-OLCU', (kx, kyy), (kx, kyy + K['kabin_der']), 20, 2.0 * k, f"{K['kabin_der']:.0f}")
    c.T('ASN-BASLIK', (kx, kyy - 45), f"KABİN PLANI {K['kabin_gen']*10:.0f}x{K['kabin_der']*10:.0f} - engelli erişimine uygun", 2.5 * k)
    # butonyer
    bx, by = X0 + 60, Y0 + 60
    c.rect('ASN-KABIN', bx, by, bx + 25, by + 120)
    for i in range(len(K['durak_kotlari'])):
        c.C('ASN-KABIN', (bx + 12.5, by + 20 + i * 14), 4)
        c.T('ASN-YAZI', (bx + 12.5, by + 20 + i * 14), K['durak_adlari'][i][:2], 1.4 * k, 0, 'MC')
    c.rect('ASN-KABIN', bx + 5, by + 100, bx + 20, by + 110)
    c.T('ASN-YAZI', (bx + 30, by + 105), 'gösterge', 1.8 * k, 0, 'ML')
    c.T('ASN-YAZI', (bx + 30, by + 20), 'kat butonları (Braille)', 1.8 * k, 0, 'ML')
    c.T('ASN-YAZI', (bx + 30, by + 8), 'alarm / kapı aç-kapa', 1.8 * k, 0, 'ML')
    c.T('ASN-BASLIK', (bx, by - 20), 'KABİN BUTONYERİ', 2.5 * k)

    # ---------------- 7 KUYU DİBİ YÜKLERİ + SON DÖŞEME (motor asma) 1/20
    p = yeni(20, 594, 'KUYU DİBİ YÜKLERİ / SON DÖŞEME PLANI', 'alt'); k = p.k; X0, Y0, X1, Y1 = p.ic()
    ox = X0 + 40; oy = Y0 + (Y1 - Y0) / 2 - 60
    kuyu_plan(c, ox, oy, K, 1.0, False, 2.2 * k, True)
    P1 = r['P1_kabin_tampon'] / 2; P2 = r['P2_ka_tampon'] / 2
    for k_ in ky:
        kc = kabin_x0(K, k_) + K['kabin_gen'] / 2
        for dx in (-30, 30):
            q = (ox + (kc + dx), oy + (D / 2))
            c.C('ASN-YUK', q, 4); c.T('ASN-YUK', (q[0], q[1] - 7), f'{P1/1000:.1f} kN', 1.8 * k, 0, 'TC')
    c.T('ASN-BASLIK', (ox, oy + D + 70), 'KUYU DİBİ YÜKLERİ (her kuyu) Ö:1/20', 3 * k)
    c.T('ASN-YAZI', (ox, oy - 75), f"Kabin tamponları altı toplam P1 = 4·gn·(P+Q) = {f(r['P1_kabin_tampon']/1000,1)} kN (2 tampon, her biri {f(P1/1000,1)} kN)", 2.2 * k)
    c.T('ASN-YAZI', (ox, oy - 85), f"Karşı ağırlık tamponu altı P2 = 4·gn·(P+q·Q) = {f(r['P2_ka_tampon']/1000,1)} kN", 2.2 * k)
    c.T('ASN-YAZI', (ox, oy - 95), f"Kuyu dibi döşemesi kotu {f(dip)} ; kuyu dibi derinliği {f(K['kuyu_dibi'])} m (mimaride {K['mimari_kuyu_dibi']}).", 2.2 * k)
    # son döşeme planı (sağ yarı)
    sx0 = X0 + (X1 - X0) / 2 + 60; sy0 = oy
    toplam = ky[-1]['x0'] + ky[-1]['gen']; s = 1.0
    c.rect('ASN-DUVAR', sx0 - tw * s, sy0 - tw * s, sx0 + (toplam + tw) * s, sy0 + (D + tw) * s)
    c.tara('ASN-TARAMA', sx0 - tw * s, sy0 - tw * s, sx0 + (toplam + tw) * s, sy0 + (D + tw) * s, ara=30)
    for k_ in ky:
        a0 = sx0 + k_['x0'] * s; a1 = a0 + k_['gen'] * s
        c.rect('ASN-SIVA', a0, sy0, a1, sy0 + D * s)
        kc = kabin_x0(K, k_) + K['kabin_gen'] / 2
        # askı kancası (kabin ekseninde) + halat delikleri
        q = (sx0 + kc * s, sy0 + (D / 2) * s)
        c.C('ASN-MOTOR', q, 5); c.C('ASN-MOTOR', q, 2)
        c.T('ASN-MOTOR', (q[0], q[1] + 8), 'KANCA (min 2000 kg)', 1.8 * k, 0, 'BC')
        c.rect('ASN-MOTOR', sx0 + (kc + 35) * s, sy0 + (D / 2 - 12) * s, sx0 + (kc + 55) * s, sy0 + (D / 2 + 12) * s)
        c.T('ASN-MOTOR', (sx0 + (kc + 45) * s, sy0 + (D / 2 - 16) * s), 'regülatör', 1.5 * k, 0, 'TC')
        c.T('ASN-BASLIK', ((a0 + a1) / 2, sy0 - 30), k_['ad'], 2.2 * k, 0, 'TC')
        c.rect('ASN-MOTOR', a1 - 45, sy0 + 10, a1 - 10, sy0 + 40)
        c.L('ASN-MOTOR', (a1 - 45, sy0 + 10), (a1 - 10, sy0 + 40)); c.L('ASN-MOTOR', (a1 - 45, sy0 + 40), (a1 - 10, sy0 + 10))
        c.T('ASN-MOTOR', (a1 - 27.5, sy0 + 44), 'duman tah. 35x30', 1.5 * k, 0, 'BC')
        c.olcu('ASN-OLCU', (a0, sy0 + D + tw), (a1, sy0 + D + tw), 30, 2.0 * k, f"{k_['gen']:.0f}")
    c.olcu('ASN-OLCU', (sx0 + toplam + tw, sy0), (sx0 + toplam + tw, sy0 + D), -30, 2.0 * k, f'{D:.0f}')
    c.T('ASN-UYARI', (sx0, sy0 + D + 100), f"SON DÖŞEME: alt +{f(tavan)} / üst +{f(tavan + kalin / 100)} - min {kalin:.0f} cm betonarme", 2.6 * k)
    c.T('ASN-BASLIK', (sx0, sy0 + D * s + 70), 'MOTORUN ASILDIĞI SON DÖŞEME (KUYU TAVANI) PLANI Ö:1/20', 3 * k)
    sd = [f"Son döşeme alt kotu +{f(tavan)}  (son durak +{f(ust_kat)} -> kuyu üst boşluğu {f(tavan-ust_kat)} m)",
          f"Mimaride döşeme kalınlığı {K['mimari_son_doseme_kalinlik']:.0f} cm -> motor asılacağı için en az {kalin:.0f} cm betonarme (statik hesaplı).",
          f"Her kuyu için döşemeye gelen düşey yük F = {f(r['F_kuyu_ustu']/1000,1)} kN (statik); dinamik katsayı statikçe uygulanacak.",
          'Her kuyu tavanına kabin ekseninde montaj/askı kancası; kancanın taşıma kapasitesi üzerine yazılır.',
          'Kuyu tavanında duman tahliye açıklığı (kuyu kesitinin en az %1i) bırakılır.']
    yazi_blok(c, sx0, sy0 - 50, sd, 2.0 * k)

    # ---------------- 8 KESİT YANDAN 1/50 ve 9 KARŞIDAN 1/50
    for tur in ('YANDAN', 'KARŞIDAN'):
        p = yeni(50, 210, f'KUYU KESİTİ - {tur}', 'tam'); k = p.k; X0, Y0, X1, Y1 = p.ic()
        ztop = tavan + kalin / 100 + 0.6
        H_m = ztop - dip
        sc = min(1.0, (Y1 - Y0 - 30 * k) / (H_m * 100))
        # 1/50 gerçek ölçü (sc=1 olmalı; sığmazsa A3 dikey yetmez -> uyarı)
        sc = 1.0
        base_y = Y0 + 12 * k - dip * 100
        if (ztop - dip) * 100 > (Y1 - Y0 - 10 * k):
            base_y = Y0 + 5 * k - dip * 100
        Z = lambda z: base_y + z * 100
        if tur == 'YANDAN':
            gen = K['derinlik']; parcalar = [(0, gen)]
        else:
            parcalar = [(k_['x0'], k_['x0'] + k_['gen']) for k_ in ky]
            gen = ky[-1]['x0'] + ky[-1]['gen']
        xs0 = X0 + 60 * k
        # duvarlar
        c.rect('ASN-DUVAR', xs0 - tw, Z(dip - 0.4), xs0, Z(tavan + kalin / 100))
        c.rect('ASN-DUVAR', xs0 + gen, Z(dip - 0.4), xs0 + gen + tw, Z(tavan + kalin / 100))
        if tur == 'KARŞIDAN':
            for (a_, b_) in parcalar[:-1]:
                c.rect('ASN-DUVAR', xs0 + b_, Z(dip), xs0 + b_ + K['ara_duvar'], Z(tavan))
        # kuyu dibi döşemesi (temel) ve son döşeme
        c.rect('ASN-DUVAR', xs0 - tw, Z(dip - 0.4), xs0 + gen + tw, Z(dip))
        c.tara('ASN-TARAMA', xs0 - tw, Z(dip - 0.4), xs0 + gen + tw, Z(dip), 10)
        c.rect('ASN-DUVAR', xs0 - tw, Z(tavan), xs0 + gen + tw, Z(tavan + kalin / 100))
        c.tara('ASN-TARAMA', xs0 - tw, Z(tavan), xs0 + gen + tw, Z(tavan + kalin / 100), 8)
        c.T('ASN-UYARI', (xs0 + gen + tw + 10, Z(tavan + kalin / 200)), f'SON DÖŞEME (motor asma) min {kalin:.0f} cm BA', 2.2 * k, 0, 'ML')
        # kat döşemeleri
        for ad_, z in zip(K['durak_adlari'], K['durak_kotlari']):
            for side in (-1, 1):
                if side < 0:
                    c.rect('ASN-DUVAR', xs0 - tw - 120, Z(z - 0.15), xs0 - tw, Z(z))
                    c.tara('ASN-TARAMA', xs0 - tw - 120, Z(z - 0.15), xs0 - tw, Z(z), 6)
                else:
                    c.rect('ASN-DUVAR', xs0 + gen + tw, Z(z - 0.15), xs0 + gen + tw + 60, Z(z))
            c.kot('ASN-KOT', xs0 - tw - 70, Z(z), ('+' if z > 0 else ('±' if z == 0 else '')) + f(z), 2.0 * k)
            c.T('ASN-BASLIK', (xs0 - tw - 115, Z(z) + 30), ad_, 2.4 * k)
            if tur == 'YANDAN':
                # kat kapısı boşluğu (210)
                c.rect('ASN-KAPI', xs0 + gen - 3, Z(z), xs0 + gen + 3, Z(z + 2.10))
        c.kot('ASN-KOT', xs0 - tw - 70, Z(dip), f(dip), 2.0 * k)
        c.kot('ASN-KOT', xs0 - tw - 70, Z(tavan), '+' + f(tavan), 2.0 * k)
        # raylar, kabin (son durakta), motor (tepede), K.A., tamponlar
        for (a_, b_) in parcalar:
            w_ = b_ - a_
            cxm = xs0 + (a_ + b_) / 2
            if tur == 'YANDAN':
                kx0, kx1 = xs0 + SIVA + 13, xs0 + SIVA + 13 + K['kabin_der']
            else:
                kk = next(q for q in ky if q['x0'] == a_)
                kx0 = xs0 + kabin_x0(K, kk); kx1 = kx0 + K['kabin_gen']
            c.L('ASN-RAY', (kx0 - 5, Z(dip + 0.1)), (kx0 - 5, Z(tavan - 0.05)))
            c.L('ASN-RAY', (kx1 + 5, Z(dip + 0.1)), (kx1 + 5, Z(tavan - 0.05)))
            zk = ust_kat
            c.rect('ASN-KABIN', kx0, Z(zk), kx1, Z(zk + 2.40))
            c.L('ASN-KABIN', (kx0, Z(zk)), (kx1, Z(zk + 2.40))); c.L('ASN-KABIN', (kx0, Z(zk + 2.40)), (kx1, Z(zk)))
            c.T('ASN-KABIN', ((kx0 + kx1) / 2, Z(zk + 1.2)), 'KABİN', 2.0 * k, 0, 'MC')
            # motor: tepede, ray başında (son döşemeye asılı)
            mx0, mx1 = (kx1 - 55, kx1 - 5) if tur == 'YANDAN' else (kx1 - 50, kx1)
            c.rect('ASN-MOTOR', mx0, Z(tavan - 0.75), mx1, Z(tavan - 0.25))
            c.C('ASN-MOTOR', ((mx0 + mx1) / 2, Z(tavan - 0.5)), 12)
            c.L('ASN-MOTOR', ((mx0 + mx1) / 2, Z(tavan - 0.25)), ((mx0 + mx1) / 2, Z(tavan)))
            c.T('ASN-MOTOR', (mx0 - 3, Z(tavan - 0.5)), 'MOTOR', 1.8 * k, 0, 'MR')
            # halatlar
            c.L('ASN-HALAT', ((mx0 + mx1) / 2, Z(tavan - 0.62)), ((kx0 + kx1) / 2, Z(zk + 2.40)))
            # tamponlar
            for tx_ in ((kx0 + kx1) / 2 - 30, (kx0 + kx1) / 2 + 30):
                c.rect('ASN-YUK', tx_ - 7, Z(dip), tx_ + 7, Z(dip + 0.45))
            c.T('ASN-YUK', ((kx0 + kx1) / 2, Z(dip + 0.55)), 'TAMPON', 1.6 * k, 0, 'BC')
            # karşı ağırlık (en alt konumda, kabin üstteyken)
            if tur == 'KARŞIDAN':
                kax = kx1 + 22
                c.rect('ASN-KA', kax - 6, Z(dip + 0.7), kax + 6, Z(dip + 0.7 + 2.5))
                c.T('ASN-KA', (kax, Z(dip + 3.4)), 'K.A.', 1.8 * k, 90, 'ML')
            # kuyu dibi merdiveni
            if tur == 'YANDAN':
                for i in range(int(K['kuyu_dibi'] / 0.3)):
                    c.L('ASN-KAPI', (xs0 + gen - 25, Z(dip + 0.3 * (i + 1))), (xs0 + gen - 8, Z(dip + 0.3 * (i + 1))))
                c.L('ASN-KAPI', (xs0 + gen - 25, Z(dip)), (xs0 + gen - 25, Z(alt_kat + 1.0)))
                c.L('ASN-KAPI', (xs0 + gen - 8, Z(dip)), (xs0 + gen - 8, Z(alt_kat + 1.0)))
                c.T('ASN-KAPI', (xs0 + gen - 30, Z(dip + 0.6)), 'kuyu dibi merdiveni', 1.5 * k, 90, 'BL')
        # ölçüler (sağ)
        ox_ = xs0 + gen + tw + 70
        c.olcu('ASN-OLCU', (ox_, Z(dip)), (ox_, Z(alt_kat)), 0, 2.2 * k, f"KUYU DİBİ {f(K['kuyu_dibi'])}")
        c.olcu('ASN-OLCU', (ox_, Z(alt_kat)), (ox_, Z(ust_kat)), 0, 2.2 * k, f"SEYİR {f(K['seyir'])}")
        c.olcu('ASN-OLCU', (ox_, Z(ust_kat)), (ox_, Z(tavan)), 0, 2.2 * k, f"ÜST BOŞLUK {f(tavan-ust_kat)}")
        c.olcu('ASN-OLCU', (ox_ + 45, Z(dip)), (ox_ + 45, Z(tavan)), 0, 2.2 * k, f"KUYU MESAFESİ {f(tavan-dip)} m")
        zz = list(K['durak_kotlari'])
        for z1, z2 in zip(zz, zz[1:]):
            c.olcu('ASN-OLCU', (xs0 - tw - 150, Z(z1)), (xs0 - tw - 150, Z(z2)), 0, 2.0 * k, f'{(z2-z1)*100:.0f}')
        if tur == 'YANDAN':
            c.olcu('ASN-OLCU', (xs0, Z(dip - 0.6)), (xs0 + gen, Z(dip - 0.6)), 0, 2.0 * k, f'{gen:.0f}')
        else:
            for (a_, b_) in parcalar:
                c.olcu('ASN-OLCU', (xs0 + a_, Z(dip - 0.6)), (xs0 + b_, Z(dip - 0.6)), 0, 2.0 * k, f'{b_-a_:.0f}')
        c.T('ASN-BASLIK', (X1 - 150 * k, Y1 - 8 * k), f'ASANSÖR KUYUSU DİKİNE KESİTİ - {tur} GÖRÜNÜŞ', 3.0 * k)
        c.T('ASN-BASLIK', (X1 - 150 * k, Y1 - 14 * k), 'Ölçek 1/50 - Makine dairesiz', 2.5 * k)
        nt = [f"Kuyu dibi {f(dip)} kotunda (mimaride: {K['mimari_kuyu_dibi']}).",
              f"Son döşeme alt +{f(tavan)}, min {kalin:.0f} cm BA, motor askı kancalı.",
              'Kuyu dibinde kuyu genişliği daralmayacak (hatıl/temel kirişi içeri taşmaz).',
              'Kuyu dibine pis su süzgeci/bağlantısı konmaz; su yalıtımı yapılır.',
              'Kuyu aydınlatması: kabin tavanı ve kuyu dibinin 1 m üstünde min 50 lüks.']
        yazi_blok(c, X1 - 150 * k, Y1 - 24 * k, nt, 2.2 * k)

    # ---------------- ELEKTRİK DETAYLARI (kullanıcının standart elektrik paftaları - her asansör setinin sonuna)
    bitir()
    ex = yer['x'] + 4 * m5
    ew, eh = sablon_yapistir(c, 'elektrik_detay', ex, (SERIT_H * m5 - 2920) / 2, 'ASN-ELEKTRIK', 'ASN-ELEKTRIK-YAZI')
    hucreler.append((yer['x'], 0, ew + 8 * m5, SERIT_H * m5))
    paftalar.append(('ELEKTRİK DETAYLARI', None))
    yer['x'] += ew + 8 * m5
    x = yer['x']

    # ---------------- şerit çerçevesi + hücre ayırıcıları (tek çizgi)
    c.rect('ASN-CERCEVE', 0, 0, x + 5 * m5, SERIT_H * m5)
    c.rect('ASN-CERCEVE', SOL, 0 + 0.0, x, SERIT_H * m5)
    dikey = sorted({round(X + W, 1) for (X, Y, W, H) in hucreler if X + W < x - 1})
    for xx in dikey:
        c.L('ASN-CERCEVE', (xx, 0), (xx, SERIT_H * m5))
    for (X, Y, W, H) in hucreler:
        if Y > 1 and H < SERIT_H * m5 - 1:
            c.L('ASN-CERCEVE', (X, Y), (X + W, Y))
    for i in range(1, int(x / (210 * m5)) + 1):          # A4 katlama işaretleri (alt kenar dışında)
        xx = SOL + i * 190 * m5
        if xx < x - 30 * m5:
            c.L('ASN-EKSEN', (xx, -6 * m5), (xx, -1 * m5))

    # ---------------- yaz
    os.makedirs(cikis, exist_ok=True)
    ad = f"KORUCUK_{K['blok']}_BLOK_ASANSOR_AVAN"
    c.dxf(os.path.join(cikis, ad + '.dxf'))
    # ozalit PDF: tek sayfa, gerçek kağıt boyu (594 mm x şerit boyu), siyah-beyaz, kalem kalınlıklı
    gen_mm = x / m5
    c.png(os.path.join(cikis, ad + '_OZALIT.pdf'), (0, -8 * m5, x + 5 * m5, SERIT_H * m5), (x + 5 * m5) / m5 / 25.4, 72, siyah=True, kalem=KALEM)
    pngs = []
    for i, (X, Y, W, H) in enumerate(hucreler):          # hızlı kontrol görüntüleri
        yol = os.path.join(cikis, f'_h{i+1:02d}.png')
        c.png(yol, (X, Y, X + W, Y + H), 12, 100, siyah=True, kalem=KALEM)
        pngs.append(yol)
    with open(os.path.join(cikis, ad + '_HESAP.txt'), 'w', encoding='utf-8') as fh:
        fh.write(rapor(a, r))
    return r, paftalar, pngs


if __name__ == '__main__':
    K = json.load(open(sys.argv[1], encoding='utf-8'))
    r, paftalar, pngs = ciz(K, sys.argv[2])
    print('pafta', len(paftalar), [b for b, _ in paftalar])
