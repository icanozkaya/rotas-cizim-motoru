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
                        ('ASN-MOTOR', 6, 'CONTINUOUS'), ('ASN-MOTOR-GIZLI', 6, 'DASHED'), ('ASN-HALAT', 6, 'CONTINUOUS'), ('ASN-YUK', 1, 'CONTINUOUS'),
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
        self.bas = len(c.R); self.son = None
        self.baslik, self.no = baslik, no
        self.Wmm, self.Hmm = gen_mm, yuk_mm
        self.x0, self.y0, self.W, self.H = 0.0, 0.0, gen_mm * self.k, yuk_mm * self.k

    def ic(self):
        k = self.k
        return 8 * k, 26 * k, self.W - 8 * k, self.H - 8 * k

    def h(self, mm):
        return mm * self.k

    def icerik_x(self):
        """içerik kayıtlarının yatay sınırları (yerel)"""
        xs = []
        for r in self.c.R[self.bas:self.son]:
            if r[0] == 'L': xs += [r[2][0], r[3][0]]
            elif r[0] == 'P': xs += [q[0] for q in r[2]]
            elif r[0] in ('C', 'A'): xs += [r[2][0] - r[3], r[2][0] + r[3]]
            elif r[0] == 'T':
                aci = abs((r[5] or 0) % 180)
                x = r[2][0]
                if 45 < aci < 135:
                    xs += [x - r[4], x + r[4]]; continue
                w = len(str(r[3])) * r[4] * 0.62
                hz = (r[6] or 'L')[-1]
                xs += [x - w, x] if hz == 'R' else ([x - w / 2, x + w / 2] if hz == 'C' else [x, x + w])
        return (min(xs), max(xs)) if xs else (0.0, self.W)

    def gerekli_mm(self, min_mm=120):
        a, b = self.icerik_x()
        return max(min_mm, (b - a) / self.k + 16), a

    def bitir(self, gen_mm, X, Y, dx_lok):
        """başlık bandını son genişlikle çiz, içerik + bandı şeritteki yerine taşı (dx_lok: sola yaslama)"""
        c = self.c; k = self.k
        self.Wmm = gen_mm; self.W = gen_mm * k
        h0 = len(c.R)
        c.L('ASN-ANTET', (4 * k, 20 * k), (self.W - 4 * k, 20 * k))
        c.T('ASN-BASLIK', (8 * k, 11 * k), self.baslik, 4.5 * k)
        c.T('ASN-ANTET', (8 * k, 5 * k), f'ÖLÇEK : 1/{self.olcek}', 2.8 * k)
        c.rect('ASN-ANTET', self.W - 26 * k, 5 * k, self.W - 4 * k, 17 * k)
        c.T('ASN-ANTET', (self.W - 15 * k, 11 * k), f'A-{self.no:02d}', 5.5 * k, 0, 'MC')
        self._tasi(X, Y, [(self.bas, self.son, dx_lok), (h0, len(c.R), 0.0)])

    def _tasi(self, X, Y, araliklar):
        f = SERIT_OLCEK / self.olcek
        R = self.c.R
        for i0, i1, dx in araliklar:
            mp = lambda p, dx=dx: (X + (p[0] + dx) * f, Y + p[1] * f)
            for i in range(i0, i1):
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
        kuyu_ic(c, K, k_, lambda u, v: (X(u), Y(v)), 0, h, detay)
        if ad_goster:
            c.T('ASN-BASLIK', (X(x0 + g / 2), Y(-tw - (40 if detay else 20) * (1 if s >= 1 else 1))), k_['ad'], h * 1.1, 0, 'TC')
    return ky, toplam



# MRL dişlisiz makine (800 kg, 1 m/s, 2/1 tipik katalog ürünü: Ø240 tahrik kasnağı, 8xØ6,5 halat, ~5 kW, ~220 kg).
# Gövde Ø42 cm, gövde boyu 45 cm, kasnak eni 12 cm, fren 8 cm. Kesin ölçüler seçilen firma makinesine göre.
MRL = dict(r_tahrik=12.0, r_govde=21.0, govde_boy=45.0, kasnak_en=12.0, fren_boy=8.0, r_kasnak=10.6, r_ka=10.6,
           v_halat=20.0, kaide_h=16.0, ust_bosluk=30.0)


def kuyu_ic_olcu(K, k_):
    """Kuyunun iç yerleşim ölçüleri (yerel: u genişlik, v derinlik; kapı v=D tarafında)."""
    D = K['derinlik']
    x0, g = k_['x0'], k_['gen']
    kab_x0 = kabin_x0(K, k_); kab_x1 = kab_x0 + K['kabin_gen']
    kab_y1 = D - SIVA - 13.0; kab_y0 = kab_y1 - K['kabin_der']
    ym = (kab_y0 + kab_y1) / 2
    bos0 = kab_x1 + 10.5
    bos1 = x0 + g - SIVA - (g - SIVA - k_['kiris'] if (k_['kiris'] and K.get('kiris_taraf', 'sag') == 'sag') else 0)
    kaw = min(12.0, max(6.0, bos1 - bos0 - 16))
    kax = (bos0 + bos1) / 2
    kc = kab_x0 + K['kabin_gen'] / 2
    xs = kax - MRL['r_ka'] - MRL['r_tahrik']          # tahrik kasnağı ekseni: K.A. halatı düşey iner
    gu0 = x0 + SIVA + 1.0                              # regülatör: sol kabin rayı yanında (yan duvar - ray arası)
    gu1 = max(gu0 + 12.0, kab_x0 - 10.4 - 1.0)
    gv = ym - 22.0                                       # rayın yanında (arka duvara değil)
    return dict(gu0=gu0, gu1=gu1, gu=(gu0 + gu1) / 2, gv=gv,
                kab_x0=kab_x0, kab_x1=kab_x1, kab_y0=kab_y0, kab_y1=kab_y1, ym=ym, kax=kax, kaw=kaw,
                kc=kc, bos0=bos0, bos1=bos1, xs=xs, pL=kc - 30, pR=kc + 30, vh=ym + MRL['v_halat'],
                kaide0=kab_x1 - 12, kaide1=bos1 - 1)


def kuyu_ic(c, K, k_, P, ang, h, detay=True, kapi=True):
    md = K.get('tip') == 'makine_daireli'
    """Kuyu içi: raylar, kabin, kapılar, karşı ağırlık, kuyu tepesindeki makine ve regülatör (gizli).
    P(u, v) -> dünya noktası (döndürme/aynalama için)."""
    o = kuyu_ic_olcu(K, k_)
    D = K['derinlik']
    R = lambda lay, a, b, cc, d: c.P(lay, [P(a, b), P(cc, b), P(cc, d), P(a, d)], True)
    kx0, kx1, ky0, ky1, ym, kax, kaw, kc = o['kab_x0'], o['kab_x1'], o['kab_y0'], o['kab_y1'], o['ym'], o['kax'], o['kaw'], o['kc']
    for rx, yon in ((kx0 - 1.5, -1), (kx1 + 1.5, 1)):              # T89 kabin rayı (T kesiti)
        R('ASN-RAY', min(rx, rx + yon * 1.6), ym - 4.45, max(rx, rx + yon * 1.6), ym + 4.45)
        R('ASN-RAY', min(rx + yon * 1.6, rx + yon * 8.9), ym - 0.8, max(rx + yon * 1.6, rx + yon * 8.9), ym + 0.8)
        bx = rx + yon * 8.9                                          # ray konsolu
        R('ASN-RAY', min(bx, bx + yon * (abs((kx0 - 1.5 - 8.9) - (k_['x0'] + SIVA)) if yon < 0 else 6)), ym - 6, max(bx, bx + yon * (abs((kx0 - 1.5 - 8.9) - (k_['x0'] + SIVA)) if yon < 0 else 6)), ym + 6)
    R('ASN-KABIN', kx0, ky0, kx1, ky1)
    R('ASN-KABIN', kx0 + 2, ky0 + 2, kx1 - 2, ky1 - 2)
    R('ASN-KABIN', kx1 - 8, ky0 + 40, kx1 - 2, ky0 + 100)            # kabin butonyeri
    c.L('ASN-KABIN', P(kx0 + 2, ky0 + 2), P(kx1 - 2, ky1 - 2)); c.L('ASN-KABIN', P(kx0 + 2, ky1 - 2), P(kx1 - 2, ky0 + 2))
    for yy in ((ky1 + 2, D + 2) if kapi else ()):                    # kabin + kat kapısı, teleskopik 2 kanat
        R('ASN-KAPI', kc - 47, yy, kc + 2, yy + 3)
        R('ASN-KAPI', kc - 2, yy + 3.5, kc + 47, yy + 6.5)
    R('ASN-KA', kax - kaw / 2, ym - 35, kax + kaw / 2, ym + 35)      # karşı ağırlık
    for yy in (ym - 41, ym + 41):                                    # T50 K.A. rayları
        R('ASN-RAY', kax - 2.5, yy - 2.5, kax + 2.5, yy + 2.5)
    xs, vh = o['xs'], o['vh']; M = MRL
    if md:
        for hx in (kc, kax):                                            # 1/1 askı: halatlar kabin ve K.A. ekseninde
            c.C('ASN-HALAT', P(hx, ym), 1.5); c.C('ASN-HALAT', P(hx, ym), 4)
    else:
        xs, vh = o['xs'], o['vh']; M = MRL
        R('ASN-MOTOR-GIZLI', o['kaide0'], vh - 15, o['kaide1'], vh - 9)                     # kaide profilleri (2xUPN)
        R('ASN-MOTOR-GIZLI', o['kaide0'], vh + 59, o['kaide1'], vh + 65)
        R('ASN-MOTOR-GIZLI', xs - M['r_tahrik'], vh - M['kasnak_en'] / 2, xs + M['r_tahrik'], vh + M['kasnak_en'] / 2)   # tahrik kasnağı
        g0 = vh + M['kasnak_en'] / 2
        R('ASN-MOTOR-GIZLI', xs - M['r_govde'], g0, xs + M['r_govde'], g0 + M['govde_boy'])                         # motor gövdesi
        R('ASN-MOTOR-GIZLI', xs - 15, g0 + M['govde_boy'], xs + 15, g0 + M['govde_boy'] + M['fren_boy'])           # fren / enkoder
        for hx in (o['pL'] - M['r_kasnak'], o['pR'] + M['r_kasnak'], xs + M['r_tahrik'], o['kax'] + M['r_ka']):      # halat inişleri
            c.C('ASN-HALAT', P(hx, vh), 1.5)
        for px in (o['pL'], o['pR']):                                                       # kabin altı saptırma kasnakları
            R('ASN-MOTOR-GIZLI', px - M['r_kasnak'], vh - 3, px + M['r_kasnak'], vh + 3)
        R('ASN-MOTOR-GIZLI', o['gu0'], o['gv'] - 8, o['gu1'], o['gv'] + 8)                   # hız regülatörü: ana ray yanında (kuyu tepesi)
        mx0, mx1 = xs - M['r_govde'], xs + M['r_govde']
    if detay:
        dy_ = -32 if md else 0
        c.T('ASN-KABIN', P(kc, ym + 18 + dy_), f"KABİN {K['kabin_gen']:.0f}x{K['kabin_der']:.0f}", h, ang, 'MC')
        c.T('ASN-KABIN', P(kc, ym + dy_), f"{K['kisi']} KİŞİ / {K['Q']:.0f} kg", h, ang, 'MC')
        c.T('ASN-KABIN', P(kc, ym - 18 + dy_), f"{(K['kabin_gen']*K['kabin_der'])/1e4:.2f} m²", h, ang, 'MC')
        c.T('ASN-KA', P(kax, ym - 48), 'K.A.', h * 0.8, ang, 'TC')
        if not md:
            c.T('ASN-MOTOR', P(xs, vh - 22), 'MRL MAKİNE (duvar konsolunda)', h * 0.6, ang, 'TC')
            c.T('ASN-MOTOR', P(o['gu'], o['gv'] - 12), 'regülatör', h * 0.55, ang, 'TC')
        c.T('ASN-KAPI', P(kc, D + K['dis_duvar'] + 8), 'KAT KAPISI 90/210 TELESKOPİK OTOMATİK', h * 0.75, ang, 'BC')
    return o


def _dik(c, lay, x, z0, z1, eng, Z):
    """Düşey çizgi; engellerin (x0, x1, z0, z1) arkasında kalan kısımları atlanır (çizgi çakışmasın)."""
    seg = [(min(z0, z1), max(z0, z1))]
    for (xa, xb, za, zb) in eng:
        if xa - 0.05 <= x <= xb + 0.05:
            yeni = []
            for (a, b) in seg:
                if zb <= a or za >= b: yeni.append((a, b)); continue
                if za > a: yeni.append((a, za))
                if zb < b: yeni.append((zb, b))
            seg = yeni
    for (a, b) in seg:
        if b - a > 0.02: c.L(lay, (x, Z(a)), (x, Z(b)))


def _kasnak(c, lay, x, y, r):
    """Kasnak (önden): dış çember, oluk çemberi, göbek."""
    c.C(lay, (x, y), r); c.C(lay, (x, y), r * 0.82); c.C(lay, (x, y), r * 0.25)


def kesit_ic(c, K, tur, ky, xs0, Z, dip, tavan, ust_kat, alt_kat, k):
    """Kuyu kesitinde MRL iç sistem: raylar + konsollar, kabin (süspansiyon çerçevesi, kabin altı kasnaklar, paraşüt),
    karşı ağırlık + kasnağı, 2/1 halat güzergâhı, kuyu tepesinde kaide üzerinde dişlisiz makine, askı kancası,
    hız regülatörü + gergi kasnağı, tamponlar, kuyu aydınlatması, kuyu dibi stop/merdiven, kumanda panosu.
    Kabin son durakta, K.A. en altta. Dönüş: etiket listesi [(x, y, metin)]."""
    M = MRL; zk = ust_kat; et = []
    zka = dip + 0.45 + 0.30                       # K.A. alt kotu (tampon + boşluk)
    hka = 2.50
    zcp = zk - 0.20 - M['r_kasnak'] / 100 - 0.02  # kabin altı kasnak ekseni
    zcw = zka + hka + M['r_ka'] / 100 + 0.04      # K.A. kasnak ekseni
    ztop_m = tavan - M['ust_bosluk'] / 100        # makine üstü
    zax = ztop_m - M['r_govde'] / 100             # makine ekseni
    zkaide = zax - M['r_govde'] / 100 - 0.02      # kaide üstü
    zkaide0 = zkaide - M['kaide_h'] / 100
    if tur == 'KARŞIDAN':
        for i, k_ in enumerate(ky):
            o = kuyu_ic_olcu(K, k_)
            X = lambda u: xs0 + u
            a, b = X(k_['x0']), X(k_['x0'] + k_['gen'])
            kx0, kx1, kc, kax = X(o['kab_x0']), X(o['kab_x1']), X(o['kc']), X(o['kax'])
            xs, pL, pR = X(o['xs']), X(o['pL']), X(o['pR'])
            kw = o['kaw'] / 2
            gx = X(o['gu'])                                     # regülatör ekseni: sol kabin rayı yanında
            xa_ = X(o['kaide0']) + 8; xb_ = b - SIVA - 2         # makine konsolu altındaki sehpa (çapraz askı)
            zs0 = zkaide0 - 0.90
            zst = lambda x_: zkaide0 - 0.90 * max(0.0, min(1.0, (x_ - xa_) / max(1.0, xb_ - xa_)))
            isiklar = [z + 1.5 for z in K['durak_kotlari']] + [dip + 1.0, tavan - 0.35]
            eng = [(kx0, kx1, zk - 0.20, zk + 2.60),             # kabin + çerçeve
                   (pL - M['r_kasnak'], pL + M['r_kasnak'], zcp - 0.11, zcp + 0.11),
                   (pR - M['r_kasnak'], pR + M['r_kasnak'], zcp - 0.11, zcp + 0.11),
                   (kax - kw, kax + kw, zka, zka + hka),
                   (kax - M['r_ka'], kax + M['r_ka'], zcw - 0.11, zcw + 0.11),
                   (xs - M['r_govde'], xs + M['r_govde'], zkaide, ztop_m),
                   (X(o['kaide0']), X(o['kaide1']), zkaide0, zkaide),
                   (gx - 8, gx + 8, tavan - 0.55, tavan - 0.35),
                   (kx0 + 5, kx0 + 15, zk - 0.36, zk - 0.21), (kx1 - 15, kx1 - 5, zk - 0.36, zk - 0.21)]
            # raylar: kabin T89 (iki yanda), K.A. T50 (K.A. ekseninde)
            for x_ in (kx0 - 1.5, kx0 - 10.4, kx1 + 1.5, kx1 + 10.4):
                _dik(c, 'ASN-RAY', x_, dip, zst(x_) - 0.03 if x_ > kx1 else tavan - 0.02, eng, Z)
            for x_ in (kax - 2.5, kax + 2.5):
                _dik(c, 'ASN-RAY', x_, dip, zst(x_) - 0.03, eng, Z)
            # ray konsolları (her ~2,5 m; duvar tarafı açık)
            zb_ = dip + 0.6
            while zb_ < zkaide0 - 0.2:
                c.P('ASN-RAY', [(a, Z(zb_)), (kx0 - 6, Z(zb_)), (kx0 - 6, Z(zb_ + 0.08)), (a, Z(zb_ + 0.08))])
                if not (zka - 0.1 < zb_ < zka + hka + 0.3):
                    c.P('ASN-RAY', [(b, Z(zb_)), (kx1 + 6, Z(zb_)), (kx1 + 6, Z(zb_ + 0.08)), (b, Z(zb_ + 0.08))])
                zb_ += 2.5
            # kabin: gövde, kabin kapısı, süspansiyon çerçevesi (üst köprü, dikmeler, alt şase), kasnaklar, paraşüt
            c.rect('ASN-KABIN', kx0, Z(zk), kx1, Z(zk + 2.40))
            c.rect('ASN-KAPI', kc - 45, Z(zk + 0.03), kc + 45, Z(zk + 2.10)); c.L('ASN-KAPI', (kc, Z(zk + 0.03)), (kc, Z(zk + 2.10)))
            c.rect('ASN-KABIN', kx0 + 5, Z(zk + 2.45), kx1 - 5, Z(zk + 2.60))
            c.rect('ASN-KABIN', kx0 + 5, Z(zk - 0.20), kx1 - 5, Z(zk - 0.05))
            for x_ in (kx0 + 5, kx0 + 11, kx1 - 11, kx1 - 5):
                c.L('ASN-KABIN', (x_, Z(zk - 0.05)), (x_, Z(zk + 2.45)))
            for px in (pL, pR):
                _kasnak(c, 'ASN-MOTOR', px, Z(zcp), M['r_kasnak'])
            for (q0, q1) in ((kx0 + 5, kx0 + 15), (kx1 - 15, kx1 - 5)):
                c.rect('ASN-YUK', q0, Z(zk - 0.36), q1, Z(zk - 0.21))
            # karşı ağırlık + kasnak
            c.rect('ASN-KA', kax - kw, Z(zka), kax + kw, Z(zka + hka))
            for j in range(1, 10):
                c.L('ASN-KA', (kax - kw, Z(zka + j * hka / 10)), (kax + kw, Z(zka + j * hka / 10)))
            _kasnak(c, 'ASN-MOTOR', kax, Z(zcw), M['r_ka'])
            # MRL makine (önden): yan duvara (perde) ankrajlı konsol 2xUPN, altında çapraz askılı sehpa; gövde Ø42, tahrik kasnağı Ø24
            c.rect('ASN-MOTOR', X(o['kaide0']), Z(zkaide0), X(o['kaide1']), Z(zkaide))
            c.L('ASN-MOTOR', (X(o['kaide0']), Z(zkaide0 + 0.08)), (X(o['kaide1']), Z(zkaide0 + 0.08)))
            c.rect('ASN-MOTOR', xb_, Z(zs0 - 0.06), b - SIVA, Z(zkaide + 0.04))                 # duvar ankraj plakası
            for d_ in (0.0, 3.0):                                                               # sehpa / çapraz askı (2 profil)
                c.L('ASN-MOTOR', (xa_ + d_, Z(zkaide0)), (xb_, Z(zs0) + d_))
            for zz_ in (zs0 + 0.05, zkaide - 0.05):                                             # ankraj bulonları
                c.C('ASN-MOTOR', (xb_ + 1.2, Z(zz_)), 0.9)
            c.C('ASN-MOTOR', (xs, Z(zax)), M['r_govde'])
            c.C('ASN-MOTOR', (xs, Z(zax)), M['r_govde'] - 3)
            _kasnak(c, 'ASN-MOTOR', xs, Z(zax), M['r_tahrik'])
            c.P('ASN-MOTOR', [(xs - 17, Z(zkaide)), (xs - 12, Z(zax - 0.14)), (xs + 12, Z(zax - 0.14)), (xs + 17, Z(zkaide))])
            for bx_ in (xs - M['r_govde'] - 6, xs + M['r_govde']):          # fren kaliperleri
                c.rect('ASN-MOTOR', bx_, Z(zax - 0.08), bx_ + 6, Z(zax + 0.08))
            c.L('ASN-MOTOR', (kc, Z(tavan)), (kc, Z(tavan - 0.12)))           # montaj kancası (kabin ekseni)
            c.A('ASN-MOTOR', (kc, Z(tavan - 0.12) - 3), 3, 0, 270)
            # 2/1 halat güzergâhı: sabit uç (kaide) -> kabin altı kasnaklar -> tahrik kasnağı -> K.A. kasnağı -> sabit uç
            rk = M['r_kasnak']
            _dik(c, 'ASN-HALAT', pL - rk, zcp, zkaide0, eng[:1] + eng[3:], Z)
            c.L('ASN-HALAT', (pL, Z(zcp) - rk), (pR, Z(zcp) - rk))
            c.L('ASN-HALAT', (pR + rk, Z(zcp)), (xs - M['r_tahrik'], Z(zax)))
            _dik(c, 'ASN-HALAT', xs + M['r_tahrik'], zcw, zax, [], Z)
            _dik(c, 'ASN-HALAT', kax + M['r_ka'], zcw, zkaide0, [], Z)
            for hx in (pL - rk, kax + M['r_ka']):
                c.rect('ASN-HALAT', hx - 3, Z(zkaide0 - 0.10), hx + 3, Z(zkaide0 - 0.01))
            # hız regülatörü (kuyu tepesi) + gergi kasnağı ve ağırlığı (kuyu dibi), regülatör halatı
            c.rect('ASN-MOTOR', gx - 8, Z(tavan - 0.55), gx + 8, Z(tavan - 0.35)); c.C('ASN-MOTOR', (gx, Z(tavan - 0.45)), 6)
            c.L('ASN-MOTOR', (gx - 8, Z(tavan - 0.45)), (a + SIVA, Z(tavan - 0.45)))          # regülatör duvar/ray konsolu
            c.C('ASN-MOTOR', (gx, Z(dip + 0.40)), 6)
            c.rect('ASN-MOTOR', gx - 5, Z(dip + 0.12), gx + 5, Z(dip + 0.28)); c.L('ASN-MOTOR', (gx, Z(dip + 0.28)), (gx, Z(dip + 0.40) - 6))
            eng_i = [(a, a + SIVA + 3.5, z_ - 0.05, z_ + 0.05) for z_ in isiklar]
            for x_ in (gx - 6, gx + 6):
                _dik(c, 'ASN-HALAT', x_, dip + 0.40, tavan - 0.45, eng[:1] + eng[8:] + eng_i, Z)
            # tamponlar (zemine oturur - alt kenar açık)
            for tx_ in (kc - 30, kc + 30):
                c.P('ASN-YUK', [(tx_ - 7, Z(dip)), (tx_ - 7, Z(dip + 0.45)), (tx_ + 7, Z(dip + 0.45)), (tx_ + 7, Z(dip))])
            c.P('ASN-YUK', [(kax - 5, Z(dip)), (kax - 5, Z(dip + 0.40)), (kax + 5, Z(dip + 0.40)), (kax + 5, Z(dip))])
            # kat kapıları (kabinin olmadığı duraklar); kuyu aydınlatması HER KATTA + kuyu dibi + tepe (sol yan duvarda)
            for z in K['durak_kotlari']:
                if abs(z - zk) > 0.01:
                    c.rect('ASN-KAPI', kc - 45, Z(z + 0.02), kc + 45, Z(z + 2.10)); c.L('ASN-KAPI', (kc, Z(z + 0.02)), (kc, Z(z + 2.10)))
            for z_ in isiklar:
                q_ = (a + SIVA + 2.5, Z(z_)); c.C('ASN-ELEKTRIK', q_, 2.5)
                c.L('ASN-ELEKTRIK', (q_[0] - 1.7, q_[1] - 1.7), (q_[0] + 1.7, q_[1] + 1.7)); c.L('ASN-ELEKTRIK', (q_[0] - 1.7, q_[1] + 1.7), (q_[0] + 1.7, q_[1] - 1.7))
            if i == len(ky) - 1:
                et += [(xs + M['r_govde'], Z(zax + 0.1), 'MRL DİŞLİSİZ MAKİNE (PM senkron, ~5,5-7,5 kW)'),
                       (xs - M['r_tahrik'] * 0.6, Z(zax - 0.06), 'TAHRİK KASNAĞI Ø240 (7xØ6,5 halat)'),
                       (X(o['kaide1']) - 4, Z(zkaide0 + 0.04), 'MAKİNE DUVAR KONSOLU 2xUPN (yan perdeye ankrajlı)'),
                       ((xa_ + xb_) / 2, Z((zkaide0 + zs0) / 2), 'ALTTAN SEHPA / ÇAPRAZ ASKI (2 profil)'),
                       (b - SIVA - 1, Z(zs0 + 0.05), 'DUVAR ANKRAJ PLAKASI (kimyasal dübel, statik onaylı)'),
                       (gx + 8, Z(tavan - 0.45), 'HIZ REGÜLATÖRÜ (ana ray yanında)'),
                       (kc, Z(tavan - 0.12) - 6, 'MONTAJ KANCASI (kabin ekseni)'),
                       (kx1 - 20, Z(zk + 2.52), 'KABİN ÜST KÖPRÜSÜ / SÜSPANSİYON ÇERÇEVESİ'),
                       (kx1 - 10, Z(zk + 1.6), f"KABİN {K['kabin_gen']*10:.0f}x{K['kabin_der']*10:.0f} / {K['Q']:.0f} kg / {K['kisi']} kişi"),
                       (pR + rk, Z(zcp), 'KABİN ALTI SAPTIRMA KASNAKLARI (2/1)'),
                       (kx1 - 10, Z(zk - 0.30), 'PARAŞÜT FREN TERTİBATI (kaymalı)'),
                       (kx1 + 10.4, Z(zk - 1.5), 'KABİN RAYI T89 (2 adet)'),
                       (b - 2, Z(dip + 0.6 + 5.0 + 0.04), 'RAY KONSOLU (max 2,5 m ara)'),
                       ((pR + rk + xs - M['r_tahrik']) / 2, Z((zcp + zax) / 2), 'ASKI HALATLARI 2/1'),
                       (kax + 2.5, Z(zka + hka + 1.5), 'K.A. RAYI T50'),
                       (kax + kw, Z(zka + 1.2), 'KARŞI AĞIRLIK (P + 0,5Q)'),
                       (kax + M['r_ka'], Z(zcw), 'K.A. KASNAĞI'),
                       (a + SIVA + 5, Z(K['durak_kotlari'][-2] + 1.5), 'KUYU AYDINLATMASI (her katta + dip + tepe, min 50 lüks)'),
                       (kc + 45, Z(K['durak_kotlari'][-2] + 1.0), 'KAT KAPISI 900x2100 TELESKOPİK'),
                       (gx + 6, Z(dip + 0.40), 'REGÜLATÖR GERGİ KASNAĞI + AĞIRLIĞI'),
                       (kc + 37, Z(dip + 0.3), 'KABİN TAMPONLARI'),
                       (kax + 5, Z(dip + 0.2), 'K.A. TAMPONU')]
    else:   # YANDAN: derinlik ekseni, kapı sağda
        k_ = ky[0]; o = kuyu_ic_olcu(K, k_)
        D = K['derinlik']
        X = lambda v: xs0 + v
        cy0, cy1, ym, vh = X(o['kab_y0']), X(o['kab_y1']), X(o['ym']), X(o['vh'])
        a = X(0); gx = X(o['gv'])
        g0 = vh + M['kasnak_en'] / 2
        eng = [(cy0, cy1, zk - 0.20, zk + 2.60), (vh - 4, vh + 4, zcp - 0.11, zcp + 0.11),
               (ym - 35, ym + 35, zka, zka + hka), (vh - 4, vh + 4, zcw - 0.11, zcw + 0.11),
               (vh - 15, vh + 65, zkaide0 - 0.95, ztop_m), (gx - 8, gx + 8, tavan - 0.55, tavan - 0.35)]
        for x_ in (ym - 4.45, ym + 4.45):                       # kabin rayı (yandan flanş)
            _dik(c, 'ASN-RAY', x_, dip, zkaide0, eng, Z)
        for x_ in (ym - 43.5, ym - 38.5, ym + 38.5, ym + 43.5):  # K.A. rayları
            _dik(c, 'ASN-RAY', x_, dip, zkaide0, eng, Z)
        zb_ = dip + 0.6
        while zb_ < zkaide0 - 0.2:
            if not any(e[2] - 0.1 < zb_ < e[3] + 0.1 for e in eng[:3]):
                c.rect('ASN-RAY', ym - 9, Z(zb_), ym + 9, Z(zb_ + 0.08))
            zb_ += 2.5
        # kabin (yandan), kabin kapısı (kapı tarafında), çerçeve, kasnak (yandan dar)
        c.rect('ASN-KABIN', cy0, Z(zk), cy1, Z(zk + 2.40))
        c.rect('ASN-KAPI', cy1 + 1, Z(zk + 0.03), cy1 + 4, Z(zk + 2.10))
        c.rect('ASN-KABIN', ym - 12, Z(zk + 2.45), ym + 12, Z(zk + 2.60))
        c.rect('ASN-KABIN', cy0 + 5, Z(zk - 0.20), cy1 - 5, Z(zk - 0.05))
        c.rect('ASN-MOTOR', vh - 4, Z(zcp - 0.11), vh + 4, Z(zcp + 0.11))
        # K.A. (yandan geniş yüz) + kasnak
        c.rect('ASN-KA', ym - 35, Z(zka), ym + 35, Z(zka + hka))
        for j in range(1, 10):
            c.L('ASN-KA', (ym - 35, Z(zka + j * hka / 10)), (ym + 35, Z(zka + j * hka / 10)))
        c.rect('ASN-MOTOR', vh - 4, Z(zcw - 0.11), vh + 4, Z(zcw + 0.11))
        # makine yandan: kaide, tahrik kasnağı (dar), motor gövdesi, fren
        c.rect('ASN-MOTOR', vh - 15, Z(zkaide0), vh + 65, Z(zkaide))
        c.rect('ASN-MOTOR', vh - M['kasnak_en'] / 2, Z(zax - M['r_tahrik'] / 100), vh + M['kasnak_en'] / 2, Z(zax + M['r_tahrik'] / 100))
        c.rect('ASN-MOTOR', g0, Z(zax - M['r_govde'] / 100), g0 + M['govde_boy'], Z(ztop_m))
        c.rect('ASN-MOTOR', g0 + M['govde_boy'], Z(zax - 0.15), g0 + M['govde_boy'] + M['fren_boy'], Z(zax + 0.15))
        c.L('ASN-MOTOR', (g0 + 5, Z(zkaide)), (g0 + 5, Z(zax - M['r_govde'] / 100)))
        c.L('ASN-MOTOR', (g0 + M['govde_boy'] - 5, Z(zkaide)), (g0 + M['govde_boy'] - 5, Z(zax - M['r_govde'] / 100)))
        zs0 = zkaide0 - 0.90                                    # konsol altı sehpa: yan perdede çapraz askı
        c.L('ASN-MOTOR', (vh - 15, Z(zkaide0)), (vh + 65, Z(zs0))); c.L('ASN-MOTOR', (vh + 65, Z(zkaide0)), (vh - 15, Z(zs0)))
        c.rect('ASN-MOTOR', vh - 17, Z(zs0 - 0.06), vh + 67, Z(zs0))
        # halat demeti (2 kenar çizgisi), kasnak hizasında
        for x_ in (vh - 3, vh + 3):
            _dik(c, 'ASN-HALAT', x_, zcw + 0.11, zax - M['r_tahrik'] / 100, eng[:2], Z)
        # regülatör + gergi
        c.rect('ASN-MOTOR', gx - 8, Z(tavan - 0.55), gx + 8, Z(tavan - 0.35)); c.C('ASN-MOTOR', (gx, Z(tavan - 0.45)), 6)
        c.C('ASN-MOTOR', (gx, Z(dip + 0.40)), 6); c.rect('ASN-MOTOR', gx - 5, Z(dip + 0.12), gx + 5, Z(dip + 0.28))
        c.L('ASN-MOTOR', (gx, Z(dip + 0.28)), (gx, Z(dip + 0.40) - 6))
        for x_ in (gx - 6, gx + 6):
            _dik(c, 'ASN-HALAT', x_, dip + 0.40, tavan - 0.55, eng[:3], Z)
        # tamponlar
        for tx_ in (ym - 22, ym + 22):
            c.P('ASN-YUK', [(tx_ - 7, Z(dip)), (tx_ - 7, Z(dip + 0.45)), (tx_ + 7, Z(dip + 0.45)), (tx_ + 7, Z(dip))])
        c.P('ASN-YUK', [(ym - 5, Z(dip)), (ym - 5, Z(dip + 0.40)), (ym + 5, Z(dip + 0.40)), (ym + 5, Z(dip))])
        # kuyu dibi merdiveni, stop butonu + priz, aydınlatma
        gen = D
        for i in range(int((alt_kat + 1.0 - dip) / 0.3)):
            c.L('ASN-KAPI', (X(gen - 25), Z(dip + 0.3 * (i + 1))), (X(gen - 8), Z(dip + 0.3 * (i + 1))))
        c.L('ASN-KAPI', (X(gen - 25), Z(dip)), (X(gen - 25), Z(alt_kat + 1.0)))
        c.L('ASN-KAPI', (X(gen - 8), Z(dip)), (X(gen - 8), Z(alt_kat + 1.0)))
        c.rect('ASN-ELEKTRIK', X(gen - 45), Z(dip + 0.90), X(gen - 33), Z(dip + 1.15))
        for z_ in [z + 1.5 for z in K['durak_kotlari']] + [dip + 1.0, tavan - 0.35]:      # kuyu aydınlatması her katta
            q_ = (X(SIVA + 2.5), Z(z_)); c.C('ASN-ELEKTRIK', q_, 2.5)
            c.L('ASN-ELEKTRIK', (q_[0] - 1.7, q_[1] - 1.7), (q_[0] + 1.7, q_[1] + 1.7)); c.L('ASN-ELEKTRIK', (q_[0] - 1.7, q_[1] + 1.7), (q_[0] + 1.7, q_[1] - 1.7))
        # kumanda panosu (son durak, kat kapısı yanında - kuyu dışında)
        kpx = X(D + K['dis_duvar'] + 4)
        c.rect('ASN-ELEKTRIK', kpx, Z(zk + 0.80), kpx + 14, Z(zk + 2.00))
        et += [(g0 + M['govde_boy'], Z(zax + 0.1), 'MRL DİŞLİSİZ MAKİNE + FREN'),
               (vh + M['kasnak_en'] / 2, Z(zax - 0.05), 'TAHRİK KASNAĞI Ø240 (7xØ6,5)'),
               (vh + 65, Z(zkaide0 + 0.08), 'MAKİNE DUVAR KONSOLU 2xUPN'),
               (vh + 25, Z(zkaide0 - 0.45), 'ÇAPRAZ ASKILI SEHPA (perdeye ankrajlı)'),
               (gx + 8, Z(tavan - 0.45), 'HIZ REGÜLATÖRÜ (ana ray yanında)'),
               (ym + 12, Z(zk + 2.52), 'KABİN ÜST KÖPRÜSÜ'),
               (cy1 - 10, Z(zk + 1.6), 'KABİN (son durakta)'),
               (cy1 + 4, Z(zk + 1.0), 'KABİN KAPISI'),
               (vh + 4, Z(zcp), 'KABİN ALTI KASNAKLARI'),
               (vh + 3, Z((zcw + zk) / 2 - 0.5), 'ASKI HALATLARI 2/1'),
               (ym + 4.45, Z(zka + hka + 1.0), 'KABİN RAYI T89'),
               (ym + 43.5, Z(zka + hka + 2.0), 'K.A. RAYLARI T50'),
               (ym + 35, Z(zka + 1.2), 'KARŞI AĞIRLIK'),
               (X(SIVA + 5), Z(K['durak_kotlari'][-2] + 1.5), 'KUYU AYDINLATMASI (her katta)'),
               (kpx + 14, Z(zk + 1.4), 'KUMANDA PANOSU (son durak)'),
               (X(gen) + 13, Z(K['durak_kotlari'][-2] + 1.6), 'KAT KAPISI (teleskopik)'),
               (gx + 6, Z(dip + 0.40), 'REGÜLATÖR GERGİ KASNAĞI'),
               (ym + 29, Z(dip + 0.3), 'KABİN TAMPONLARI'),
               (ym + 5, Z(dip + 0.2), 'K.A. TAMPONU'),
               (X(gen - 33), Z(dip + 1.0), 'KUYU DİBİ STOP BUTONU + PRİZ'),
               (X(gen - 8), Z(dip + 0.75), 'KUYU DİBİ MERDİVENİ')]
    return et



def kesit_ic_md(c, K, tur, ky, xs0, Z, dip, tavan, ust_kat, alt_kat, k, zmd, zmt):
    """MAKİNE DAİRELİ kesit iç sistemi (1/1 askı): kuyuda raylar, kabin, K.A., tamponlar, gergi kasnağı;
    makine dairesinde (döşeme üstü zmd, tavan altı zmt) kaideli makine + saptırma kasnağı (ROTAŞ örnek sembolü),
    hız regülatörü, kumanda panosu, askı kancası, halat delikleri. Dönüş: etiketler."""
    zk = ust_kat; et = []
    zka = dip + 0.45 + 0.30; hka = 2.50
    if tur == 'KARŞIDAN':
        for i, k_ in enumerate(ky):
            o = kuyu_ic_olcu(K, k_)
            X = lambda u: xs0 + u
            a, b = X(k_['x0']), X(k_['x0'] + k_['gen'])
            kx0, kx1, kc, kax = X(o['kab_x0']), X(o['kab_x1']), X(o['kc']), X(o['kax'])
            kw = o['kaw'] / 2
            gx = kx0 + 15
            eng = [(kx0, kx1, zk - 0.20, zk + 2.72), (kax - kw, kax + kw, zka, zka + hka + 0.10),
                   (kx0 + 5, kx0 + 15, zk - 0.36, zk - 0.21)]
            for x_ in (kx0 - 1.5, kx0 - 10.4, kx1 + 1.5, kx1 + 10.4):
                _dik(c, 'ASN-RAY', x_, dip, tavan, eng, Z)
            for x_ in (kax - 2.5, kax + 2.5):
                _dik(c, 'ASN-RAY', x_, dip, tavan, eng, Z)
            zb_ = dip + 0.6
            while zb_ < tavan - 0.3:
                c.P('ASN-RAY', [(a, Z(zb_)), (kx0 - 6, Z(zb_)), (kx0 - 6, Z(zb_ + 0.08)), (a, Z(zb_ + 0.08))])
                if not (zka - 0.1 < zb_ < zka + hka + 0.3):
                    c.P('ASN-RAY', [(b, Z(zb_)), (kx1 + 6, Z(zb_)), (kx1 + 6, Z(zb_ + 0.08)), (b, Z(zb_ + 0.08))])
                zb_ += 2.5
            # kabin + çerçeve + paraşüt + üst halat bağlantısı
            c.rect('ASN-KABIN', kx0, Z(zk), kx1, Z(zk + 2.40))
            c.rect('ASN-KAPI', kc - 45, Z(zk + 0.03), kc + 45, Z(zk + 2.10)); c.L('ASN-KAPI', (kc, Z(zk + 0.03)), (kc, Z(zk + 2.10)))
            c.rect('ASN-KABIN', kx0 + 5, Z(zk + 2.45), kx1 - 5, Z(zk + 2.60))
            c.rect('ASN-KABIN', kx0 + 5, Z(zk - 0.20), kx1 - 5, Z(zk - 0.05))
            for x_ in (kx0 + 5, kx0 + 11, kx1 - 11, kx1 - 5):
                c.L('ASN-KABIN', (x_, Z(zk - 0.05)), (x_, Z(zk + 2.45)))
            for (q0, q1) in ((kx0 + 5, kx0 + 15), (kx1 - 15, kx1 - 5)):
                c.rect('ASN-YUK', q0, Z(zk - 0.36), q1, Z(zk - 0.21))
            c.rect('ASN-HALAT', kc - 6, Z(zk + 2.60), kc + 6, Z(zk + 2.72))
            # K.A.
            c.rect('ASN-KA', kax - kw, Z(zka), kax + kw, Z(zka + hka))
            for j in range(1, 10):
                c.L('ASN-KA', (kax - kw, Z(zka + j * hka / 10)), (kax + kw, Z(zka + j * hka / 10)))
            c.rect('ASN-HALAT', kax - 4, Z(zka + hka), kax + 4, Z(zka + hka + 0.10))
            # makine (örnek sembol: kaide + tahrik kasnağı + saptırma kasnağı), aynalı: tahrik kabin tarafında
            W = 94.10003722063266
            MX = kc - (W - 81.5)
            MX = min(MX, b - 4 - W)
            sembol(c, 'makine_yan', MX, Z(zmd), 'ASN-MOTOR', ayna=True)
            t_x, t_y = MX + (W - 81.5), Z(zmd) + 48
            d_x, d_y = MX + (W - 14.0), Z(zmd) + 20
            for dx in (-2, 2):
                c.L('ASN-HALAT', (t_x + dx, t_y), (kc + dx, Z(zk + 2.72)))
                c.L('ASN-HALAT', (d_x + dx, d_y), (kax + dx, Z(zka + hka + 0.10)))
            # askı kancası (makine dairesi tavanı, makine ekseni)
            mxc = MX + W / 2
            c.L('ASN-MOTOR', (mxc, Z(zmt)), (mxc, Z(zmt - 0.15))); c.A('ASN-MOTOR', (mxc, Z(zmt - 0.15) - 4), 4, 0, 270)
            # hız regülatörü (makine dairesi döşemesinde) + halatı + gergi kasnağı (kuyu dibi)
            c.rect('ASN-MOTOR', gx - 10, Z(zmd), gx + 10, Z(zmd + 0.32)); c.C('ASN-MOTOR', (gx, Z(zmd + 0.20)), 6)
            c.C('ASN-MOTOR', (gx, Z(dip + 0.40)), 6)
            c.rect('ASN-MOTOR', gx - 5, Z(dip + 0.12), gx + 5, Z(dip + 0.28)); c.L('ASN-MOTOR', (gx, Z(dip + 0.28)), (gx, Z(dip + 0.40) - 6))
            for x_ in (gx - 6, gx + 6):
                _dik(c, 'ASN-HALAT', x_, dip + 0.40, zmd + 0.20, eng[:1] + eng[2:], Z)
            # kumanda panosu (makine dairesi, sol duvar önü) + ana şalter + aydınlatma
            pa = a + 2
            c.rect('ASN-ELEKTRIK', gx + 14, Z(zmd + 0.60), gx + 44, Z(zmd + 1.90))
            c.rect('ASN-ELEKTRIK', pa + 2, Z(zmd + 1.30), pa + 10, Z(zmd + 1.55))
            c.C('ASN-MOTOR', ((a + b) / 2, Z(zmt) - 6), 4)
            # tamponlar, kat kapıları, kuyu aydınlatması
            for tx_ in (kc - 30, kc + 30):
                c.P('ASN-YUK', [(tx_ - 7, Z(dip)), (tx_ - 7, Z(dip + 0.45)), (tx_ + 7, Z(dip + 0.45)), (tx_ + 7, Z(dip))])
            c.P('ASN-YUK', [(kax - 5, Z(dip)), (kax - 5, Z(dip + 0.40)), (kax + 5, Z(dip + 0.40)), (kax + 5, Z(dip))])
            for z in K['durak_kotlari']:
                if abs(z - zk) > 0.01:
                    c.rect('ASN-KAPI', kc - 45, Z(z + 0.02), kc + 45, Z(z + 2.10)); c.L('ASN-KAPI', (kc, Z(z + 0.02)), (kc, Z(z + 2.10)))
                    c.C('ASN-MOTOR', (kc + 20, Z(z + 2.55)), 3)
            c.C('ASN-MOTOR', (kc + 20, Z(dip + 1.0)), 3); c.C('ASN-MOTOR', (kc + 20, Z(zk + 2.95)), 3)
            if i == len(ky) - 1:
                et += [(mxc, Z(zmt) - 10, 'MAKİNE ASKI KANCASI (min 2000 kg)'),
                       (MX + W - 30, Z(zmd) + 60, 'MAKİNE (kaide üzerinde, makine dairesinde)'),
                       (t_x + 3, t_y, 'TAHRİK KASNAĞI'),
                       (d_x - 3, d_y, 'SAPTIRMA KASNAĞI'),
                       (MX + 8, Z(zmd) + 8, 'MAKİNE KAİDESİ (titreşim takozlu)'),
                       ((a + b) / 2 + 4, Z(zmt) - 6, 'MAKİNE DAİRESİ AYD. (min 200 lüks)'),
                       (gx + 44, Z(zmd + 1.3), 'KUMANDA PANOSU'),
                       (gx + 10, Z(zmd + 0.2), 'HIZ REGÜLATÖRÜ'),
                       (pa + 10, Z(zmd + 1.42), 'ANA ŞALTER (kapı yanında)'),
                       ((kc + t_x) / 2, Z((zk + 2.72 + zmd) / 2), 'ASKI HALATLARI 1/1'),
                       (kc + 6, Z(zk + 2.66), 'HALAT BAĞLANTISI (kabin üst köprüsü)'),
                       (kx1 - 20, Z(zk + 2.52), 'KABİN ÜST KÖPRÜSÜ'),
                       (kx1 - 10, Z(zk + 1.6), f"KABİN {K['kabin_gen']*10:.0f}x{K['kabin_der']*10:.0f} / {K['Q']:.0f} kg / {K['kisi']} kişi"),
                       (kx1 - 10, Z(zk - 0.30), 'PARAŞÜT FREN TERTİBATI'),
                       (kx1 + 10.4, Z(zk - 1.5), 'KABİN RAYI T89 (2 adet)'),
                       (b - 2, Z(dip + 0.6 + 5.0 + 0.04), 'RAY KONSOLU (max 2,5 m ara)'),
                       (kax + 2.5, Z(zka + hka + 1.5), 'K.A. RAYI T50'),
                       (kax + kw, Z(zka + 1.2), 'KARŞI AĞIRLIK (P + 0,5Q)'),
                       (kc + 23, Z(K['durak_kotlari'][-2] + 2.55), 'KUYU AYDINLATMASI (min 50 lüks)'),
                       (kc + 45, Z(K['durak_kotlari'][-2] + 1.0), 'KAT KAPISI 900x2100 TELESKOPİK'),
                       (gx + 6, Z(dip + 0.40), 'REGÜLATÖR GERGİ KASNAĞI + AĞIRLIĞI'),
                       (kc + 37, Z(dip + 0.3), 'KABİN TAMPONLARI'),
                       (kax + 5, Z(dip + 0.2), 'K.A. TAMPONU')]
    else:
        k_ = ky[0]; o = kuyu_ic_olcu(K, k_)
        D = K['derinlik']
        X = lambda v: xs0 + v
        cy0, cy1, ym = X(o['kab_y0']), X(o['kab_y1']), X(o['ym'])
        gx = X(SIVA + 12)
        eng = [(cy0, cy1, zk - 0.20, zk + 2.72), (ym - 35, ym + 35, zka, zka + hka + 0.10)]
        for x_ in (ym - 4.45, ym + 4.45):
            _dik(c, 'ASN-RAY', x_, dip, tavan, eng, Z)
        for x_ in (ym - 43.5, ym - 38.5, ym + 38.5, ym + 43.5):
            _dik(c, 'ASN-RAY', x_, dip, tavan, eng, Z)
        zb_ = dip + 0.6
        while zb_ < tavan - 0.3:
            if not any(e[2] - 0.1 < zb_ < e[3] + 0.1 for e in eng):
                c.rect('ASN-RAY', ym - 9, Z(zb_), ym + 9, Z(zb_ + 0.08))
            zb_ += 2.5
        c.rect('ASN-KABIN', cy0, Z(zk), cy1, Z(zk + 2.40))
        c.rect('ASN-KAPI', cy1 + 1, Z(zk + 0.03), cy1 + 4, Z(zk + 2.10))
        c.rect('ASN-KABIN', ym - 12, Z(zk + 2.45), ym + 12, Z(zk + 2.60))
        c.rect('ASN-KABIN', cy0 + 5, Z(zk - 0.20), cy1 - 5, Z(zk - 0.05))
        c.rect('ASN-HALAT', ym - 6, Z(zk + 2.60), ym + 6, Z(zk + 2.72))
        c.rect('ASN-KA', ym - 35, Z(zka), ym + 35, Z(zka + hka))
        for j in range(1, 10):
            c.L('ASN-KA', (ym - 35, Z(zka + j * hka / 10)), (ym + 35, Z(zka + j * hka / 10)))
        c.rect('ASN-HALAT', ym - 4, Z(zka + hka), ym + 4, Z(zka + hka + 0.10))
        # makine önden (örnek sembol): kasnak demeti x≈54
        MX = ym - 54.5
        sembol(c, 'makine_on', MX, Z(zmd), 'ASN-MOTOR')
        for x_ in (ym - 3, ym + 3):
            _dik(c, 'ASN-HALAT', x_, zka + hka + 0.10, zmd + 0.30, eng[:1], Z)
        mxc = MX + 53
        c.L('ASN-MOTOR', (mxc, Z(zmt)), (mxc, Z(zmt - 0.08))); c.A('ASN-MOTOR', (mxc, Z(zmt - 0.08) - 4), 4, 0, 270)
        # regülatör (makine dairesinde) + gergi
        c.rect('ASN-MOTOR', gx - 8, Z(zmd), gx + 8, Z(zmd + 0.32)); c.C('ASN-MOTOR', (gx, Z(zmd + 0.20)), 6)
        c.C('ASN-MOTOR', (gx, Z(dip + 0.40)), 6); c.rect('ASN-MOTOR', gx - 5, Z(dip + 0.12), gx + 5, Z(dip + 0.28))
        c.L('ASN-MOTOR', (gx, Z(dip + 0.28)), (gx, Z(dip + 0.40) - 6))
        for x_ in (gx - 6, gx + 6):
            _dik(c, 'ASN-HALAT', x_, dip + 0.40, zmd + 0.20, [], Z)
        # kumanda panosu (makine dairesi arka duvarında - yandan)
        c.rect('ASN-ELEKTRIK', X(0) + 1, Z(zmd + 0.60), X(0) + 26, Z(zmd + 1.90))
        for tx_ in (ym - 22, ym + 22):
            c.P('ASN-YUK', [(tx_ - 7, Z(dip)), (tx_ - 7, Z(dip + 0.45)), (tx_ + 7, Z(dip + 0.45)), (tx_ + 7, Z(dip))])
        c.P('ASN-YUK', [(ym - 5, Z(dip)), (ym - 5, Z(dip + 0.40)), (ym + 5, Z(dip + 0.40)), (ym + 5, Z(dip))])
        gen = D
        for i in range(int((alt_kat + 1.0 - dip) / 0.3)):
            c.L('ASN-KAPI', (X(gen - 25), Z(dip + 0.3 * (i + 1))), (X(gen - 8), Z(dip + 0.3 * (i + 1))))
        c.L('ASN-KAPI', (X(gen - 25), Z(dip)), (X(gen - 25), Z(alt_kat + 1.0)))
        c.L('ASN-KAPI', (X(gen - 8), Z(dip)), (X(gen - 8), Z(alt_kat + 1.0)))
        c.rect('ASN-ELEKTRIK', X(gen - 45), Z(dip + 0.90), X(gen - 33), Z(dip + 1.15))
        for z in K['durak_kotlari']:
            if abs(z - zk) > 0.01:
                c.C('ASN-MOTOR', (X(SIVA + 30), Z(z + 2.55)), 3)
        c.C('ASN-MOTOR', (X(SIVA + 30), Z(dip + 1.0)), 3); c.C('ASN-MOTOR', (X(SIVA + 30), Z(zk + 2.95)), 3)
        et += [(mxc, Z(zmt) - 8, 'MAKİNE ASKI KANCASI (min 2000 kg)'),
               (MX + 90, Z(zmd) + 100, 'MAKİNE + KAİDE (makine dairesinde)'),
               (MX + 60, Z(zmd) + 50, 'TAHRİK / SAPTIRMA KASNAKLARI'),
               (gx + 8, Z(zmd + 0.2), 'HIZ REGÜLATÖRÜ'),
               (X(0) + 26, Z(zmd + 1.3), 'KUMANDA PANOSU'),
               (ym + 3, Z((zk + 2.72 + zmd) / 2), 'ASKI HALATLARI 1/1'),
               (ym + 12, Z(zk + 2.52), 'KABİN ÜST KÖPRÜSÜ'),
               (cy1 - 10, Z(zk + 1.6), 'KABİN (son durakta)'),
               (cy1 + 4, Z(zk + 1.0), 'KABİN KAPISI'),
               (ym + 4.45, Z(zka + hka + 1.0), 'KABİN RAYI T89'),
               (ym + 43.5, Z(zka + hka + 2.0), 'K.A. RAYLARI T50'),
               (ym + 35, Z(zka + 1.2), 'KARŞI AĞIRLIK'),
               (X(SIVA + 33), Z(K['durak_kotlari'][-2] + 2.55), 'KUYU AYDINLATMASI'),
               (X(gen) + 13, Z(K['durak_kotlari'][-2] + 1.6), 'KAT KAPISI 90/210 (teleskopik)'),
               (gx + 6, Z(dip + 0.40), 'REGÜLATÖR GERGİ KASNAĞI'),
               (ym + 29, Z(dip + 0.3), 'KABİN TAMPONLARI'),
               (ym + 5, Z(dip + 0.2), 'K.A. TAMPONU'),
               (X(gen - 33), Z(dip + 1.0), 'KUYU DİBİ STOP BUTONU + PRİZ'),
               (X(gen - 8), Z(dip + 0.75), 'KUYU DİBİ MERDİVENİ')]
    return et



def makine_dairesi_plan(c, K, ky, sx0, sy0, k, r, tavan, kalin, ust_kat):
    """Makine dairesi planı 1/20 (kuyu üstünde): duvarlar, kapı, makine kaidesi + tahrik/saptırma kasnakları,
    halat delikleri, regülatör, kumanda panosu + 0,70 m çalışma alanı, ana şalter, askı kancası, havalandırma."""
    MD = K['makine_dairesi']; tw = K['dis_duvar']
    k_ = ky[0]; o = kuyu_ic_olcu(K, k_)
    W, Dd = MD['ic_gen'], MD['ic_der']                     # u: kuyu genişliği yönü, v: kapı yönü
    P = lambda u, v: (sx0 + u, sy0 + v)
    R = lambda lay, a, b, cc, d: c.rect(lay, sx0 + a, sy0 + b, sx0 + cc, sy0 + d)
    ku0, ku1 = MD.get('kapi_u', (W - 105, W - 15))
    duv = [(-tw, -tw, 0, Dd + tw), (W, -tw, W + tw, Dd + tw), (0, -tw, W, 0), (0, Dd, ku0, Dd + tw), (ku1, Dd, W, Dd + tw)]
    for (a, b, cc, d) in duv:
        R('ASN-DUVAR', a, b, cc, d); c.tara('ASN-TARAMA', sx0 + a, sy0 + b, sx0 + cc, sy0 + d, ara=6)
    c.A('ASN-KAPI', P(ku0, Dd + tw), ku1 - ku0, 0, 90); c.L('ASN-KAPI', P(ku0, Dd + tw), P(ku0, Dd + tw + (ku1 - ku0)))
    # kuyu sınırı (alttaki kuyu, kesikli)
    R('ASN-MOTOR-GIZLI', 0, 0, k_['gen'], K['derinlik'])
    kc, kax, ym = o['kc'], o['kax'], o['ym']
    # makine: kaide (sehpa) + kasnaklar + motor (üstten)
    Wm = 94.10003722063266
    MX = min(kc - (Wm - 81.5), W - 4 - Wm)
    R('ASN-MOTOR', MX, ym - 53, MX + Wm, ym + 53)
    R('ASN-MOTOR', MX + 4, ym - 49, MX + Wm - 4, ym + 49)
    tx, dx = MX + (Wm - 67), MX + (Wm - 24)
    R('ASN-MOTOR', tx - 15, ym - 5, tx + 15, ym + 5)                    # tahrik kasnağı
    R('ASN-MOTOR', dx - 10, ym - 5, dx + 10, ym + 5)                    # saptırma kasnağı
    R('ASN-MOTOR', tx - 18, ym - 47, tx + 18, ym - 7)                   # motor + redüktör / gövde
    R('ASN-MOTOR', tx - 12, ym + 7, tx + 12, ym + 20)                   # fren
    # halat delikleri (kabin ve K.A. halatları, regülatör halatı)
    for hx, hy in ((MX + Wm - 81.5, ym), (MX + Wm - 14, ym)):
        R('ASN-HALAT', hx - 6, hy - 9, hx + 6, hy + 9)
    gx = o['kab_x0'] + 15
    R('ASN-MOTOR', gx - 12, Dd - 45, gx + 12, Dd - 15); c.C('ASN-MOTOR', P(gx, Dd - 30), 7)
    for x_ in (gx - 6, gx + 6):
        c.C('ASN-HALAT', P(x_, Dd - 30), 1.5)
    # kumanda panosu (sol arka köşe) + önünde 0,70 m çalışma alanı
    R('ASN-ELEKTRIK', 0, 5, 25, 85)
    c.P('ASN-MOTOR-GIZLI', [P(25, 5), P(95, 5), P(95, 85), P(25, 85)], True)
    R('ASN-ELEKTRIK', W - 6, Dd - 30, W, Dd - 10)                     # ana şalter (kapı yanında)
    # askı kancası (makine ekseni) ve havalandırma menfezi
    for q in (P(MX + Wm / 2, ym + 30),):
        c.C('ASN-MOTOR', q, 4); c.C('ASN-MOTOR', q, 1.5)
    R('ASN-MOTOR', W + tw * 0.2, 70, W + tw * 0.8, 110)
    h = 1.6 * k
    c.T('ASN-MOTOR', P(MX + Wm / 2, ym + 58), 'MAKİNE + KAİDE', h, 0, 'BC')
    c.T('ASN-MOTOR', P(MX + Wm / 2, ym + 34), 'askı kancası', h * 0.8, 0, 'BL')
    c.T('ASN-HALAT', P(MX + Wm - 81.5, ym - 12), 'halat deliği', h * 0.8, 0, 'TC')
    c.T('ASN-MOTOR', P(gx, Dd - 48), 'regülatör', h * 0.8, 0, 'TC')
    c.T('ASN-ELEKTRIK', P(12.5, 45), 'KUMANDA PANOSU', h * 0.8, 90, 'MC')
    c.T('ASN-MOTOR-GIZLI', P(60, 45), 'çalışma alanı 70 cm', h * 0.7, 90, 'MC')
    c.T('ASN-ELEKTRIK', P(W - 8, Dd - 20), 'ana şalter', h * 0.7, 0, 'MR')
    c.T('ASN-MOTOR', P(W + tw + 4, 90), 'havalandırma menfezi', h * 0.7, 0, 'ML')
    c.T('ASN-KAPI', P((ku0 + ku1) / 2, Dd + tw + 4), f"MAKİNE DAİRESİ KAPISI (sahanlıktan; sahanlık +{f(MD['sahanlik'])})", h * 0.8, 0, 'BC')
    c.olcu('ASN-OLCU', P(0, -tw), P(W, -tw), -25, 2.0 * k, f'{W:.0f}')
    c.olcu('ASN-OLCU', P(W + tw, 0), P(W + tw, Dd), -45, 2.0 * k, f'{Dd:.0f}')
    c.T('ASN-BASLIK', P(0, Dd + 95), 'MAKİNE DAİRESİ PLANI Ö:1/20', 3 * k)
    c.T('ASN-UYARI', P(0, Dd + 120), f"MAKİNE DAİRESİ: döşeme +{f(MD['doseme_ust'])} (kuyu tavanı alt +{f(tavan)}), net h = {(MD['tavan_alt']-MD['doseme_ust'])*100:.0f} cm", 2.4 * k)
    yazi_blok(c, sx0, sy0 - 60, K['makine_dairesi_notlari'] + [f"Makine dairesi döşemesine (kuyu üstü) gelen düşey yük F = {f(r['F_kuyu_ustu']/1000,1)} kN (statik); askı kancası min 2000 kg."], 2.0 * k)



SEMBOL = None


def sembol(c, ad, X, Y, lay, ayna=False, olcek=1.0):
    """kutuphane/asansor/semboller.json'daki sembolü sol-alt köşesi (X, Y) olacak şekilde yerleştirir."""
    global SEMBOL
    if SEMBOL is None:
        SEMBOL = json.load(open(os.path.join(SABLON, 'semboller.json'), encoding='utf-8'))
    d = SEMBOL[ad]; W = d['gen']
    mp = lambda p: (X + ((W - p[0]) if ayna else p[0]) * olcek, Y + p[1] * olcek)
    for r in d['kayitlar']:
        if r[0] == 'L': c.L(lay, mp(r[2]), mp(r[3]))
        elif r[0] == 'P': c.P(lay, [mp(q) for q in r[2]], r[3])
        elif r[0] == 'C': c.C(lay, mp(r[2]), r[3] * olcek)
    return d['gen'] * olcek, d['yuk'] * olcek


# ---------------------------------------------------------------------------- mimari konum planı
def mimari_kopya(c, flat_pkl, pencere, ox, oy, kuyu_kutulari, h_max=30, K=None, kapi_yonu='+y'):
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
    ky = kuyu_yerlesim(K, None) if K else []
    for i, (a, b, cc, d, ad) in enumerate(kuyu_kutulari):
        if K and i < len(ky):
            k_ = ky[i]
            if kapi_yonu == '+x':
                P = lambda u, v, a=a, b=b, k_=k_: sx((a + v, b + (u - k_['x0'])))
                ang = 90
            else:
                P = lambda u, v, a=a, b=b, k_=k_: sx((a + (u - k_['x0']), b + v))
                ang = 0
            kuyu_ic(c, K, k_, P, ang, 9.0, detay=False)
        else:
            A, B = sx((a, b)), sx((cc, d))
            c.L('ASN-ISARET', A, B); c.L('ASN-ISARET', (A[0], B[1]), (B[0], A[1]))
    return n


# ---------------------------------------------------------------------------- ana çizim
def ciz(K, cikis):
    c = Cizim(); katmanlar(c)
    md = K.get('tip') == 'makine_daireli'
    aski = K.get('aski', 1 if md else 2)
    a = Asansor(proje=K['blok'], bina='konut', daireler=[tuple(d) for d in K['daireler']], durak=len(K['durak_kotlari']),
                ana_durak_ustu=K['ana_durak_ustu'], kat_yuk=(K['durak_kotlari'][-1] - K.get('ana_durak_kotu', K['durak_kotlari'][0])) / K['ana_durak_ustu'], seyir=K['seyir'],
                kisi=K['kisi'], Q=K['Q'], kabin_gen=int(K['kabin_gen'] * 10), kabin_der=int(K['kabin_der'] * 10),
                n_asansor=len(K['kuyular']), kuyu_dibi=K['kuyu_dibi'], kuyu_ustu=K['kuyu_ustu'], P_kabin=K['P_kabin'], aski=aski,
                **({} if md else dict(halat_adet=K.get('halat_adet', 7), halat_cap=K.get('halat_cap', 6.5), halat_kgm=K.get('halat_kgm', 0.152), mrl=True)))
    r = hesapla(a)
    paftalar = []
    proje = K['proje']; proje['blok'] = K['blok']
    m5 = SERIT_OLCEK / 10
    SOL = 20 * m5                        # cilt payı
    hucreler = []                        # (X, Y, W, H) ayırıcı çizgiler için
    sutunlar = []                        # sıkıştırılmış dizilim: her sütun = 1 tam pafta veya üst + alt
    aktif = []

    def kapat():
        if aktif:
            aktif[0].son = len(c.R); aktif.clear()

    def yeni(olcek, gen_mm, baslik, konum='tam'):
        """konum: 'tam' (594 yükseklik), 'ust' / 'alt' (297 yükseklik, aynı sütun). Genişlik sonda içeriğe göre daraltılır."""
        kapat()
        H = SERIT_H if konum == 'tam' else 297
        p = Pafta(c, olcek, gen_mm, H, baslik, len(paftalar) + 1)
        paftalar.append((baslik, p)); aktif.append(p)
        if konum == 'alt' and sutunlar and sutunlar[-1]['acik']:
            sutunlar[-1]['oge'].append((p, 'alt')); sutunlar[-1]['acik'] = False
        else:
            sutunlar.append(dict(oge=[(p, konum)], acik=(konum == 'ust'), min_mm=0))
        return p

    def yerlestir():
        """paftaları içerik genişliğine göre daralt, aralarında boşluk bırakmadan soldan sağa diz"""
        kapat()
        X = SOL
        for sut in sutunlar:
            ol = [(p, kn) + p.gerekli_mm() for p, kn in sut['oge']]
            W = max([g for _, _, g, _ in ol] + [sut['min_mm']])
            for p, kn, g, a in ol:
                Y = 297 * m5 if kn == 'ust' else 0.0
                p.bitir(W, X, Y, 8 * p.k - a)
                hucreler.append((X, Y, W * m5, p.Hmm * m5))
            sut['X'] = X
            X += W * m5
        return X

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
          (790, 1023): f"{K['kabin_gen']*10:.0f}x{K['kabin_der']*10:.0f}", (790, 988): f'{aski}/1', (790, 953): 'T89 / T50',
          (170, 249): f"{K['blok']} BLOK", (615, 248): K.get('tip_kapak', 'MAKİNE DAİRESİZ ÇİFT'), (783, 574): f"{proje['ilce']} BELEDİYESİ"}
    p = yeni(50, 210, 'KONTROL VE NOTLAR', 'ust'); k = p.k; X0, Y0, X1, Y1 = p.ic()
    sutunlar[-1]['acik'] = False; sutunlar[-1]['min_mm'] = 210; sutunlar[-1]['kapak'] = kd
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
        mimari_kopya(c, m['flat'], m['pencere'], ox, oy, kut, K=K, kapi_yonu=m.get('kapi_yonu', '+y'))
        for i, b in enumerate(m['kuyu_kutulari']):
            cx = (b[0] + b[2]) / 2 - px0 + ox; cy = (b[1] + b[3]) / 2 - py0 + oy
            c.T('ASN-ISARET', (cx, cy), f'A{i+1}', 2.4 * k, 0, 'MC')
        c.T('ASN-BASLIK', (X0, Y1 - 4 * k), f"{m['kat_adi']} - ASANSÖR KONUMU (mimariden)", 4.5 * k)
        c.T('ASN-YAZI', (X0, Y1 - 10 * k), (', '.join(f'A{i+1}' for i in range(len(ky))) + ': asansör kuyusu (kabin, ray, karşı ağırlık, kapılar' + ('; makine ve regülatör çatıdaki makine dairesinde).' if md else '; makine ve regülatör kuyu tepesinde, kesikli).')), 2.6 * k)

    # ---------------- 3 HESAP-1 (trafik) ve 4 HESAP-2 (kuvvet)
    metin = rapor(a, r).split('\n')
    i2 = metin.index('1.2. ASANSÖR KUVVET HESABI')
    p = yeni(50, 420, 'HESAP-1 TRAFİK HESABI', 'ust'); k = p.k; X0, Y0, X1, Y1 = p.ic()
    giris = ['# GİRDİLER (mimariden)',
             f"Daireler: " + ', '.join(f'{n} adet {yo}+{do}' for n, yo, do in K['daireler']) + f"  ->  Σb = {f(r['sum_b'],0)} kişi (Tablo-1: ilk yatak odası 2, diğer odalar 1)",
             f"Durak kotları: " + ', '.join(f'{ad} {f(z)}' for ad, z in zip(K['durak_adlari'], K['durak_kotlari'])) + f"   Seyir = {f(K['seyir'])} m",
             f"Ana durak: Zemin kat. Ana durak üzerindeki kat sayısı N = {K['ana_durak_ustu']}" + ('  (bodrum durağı hesaba katılmaz)' if alt_kat < 0 else ''),
             f"Ortalama kat yüksekliği h = (son durak - ana durak) / N = {f(a.kat_yuk)} m.  Asansör sayısı n = {len(ky)} (çift asansör)", '']
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
          ['Kapı', '900 telesk. otomatik', '900 telesk. otomatik'], ['Askı / ray', f'{aski}/1  T89 + T50', f'{aski}/1  T89 + T50']], 2.2 * k)
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
    p = yeni(20, 594, 'KUYU DİBİ YÜKLERİ / ' + ('MAKİNE DAİRESİ PLANI' if md else 'SON DÖŞEME PLANI'), 'alt'); k = p.k; X0, Y0, X1, Y1 = p.ic()
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
    if md:
        makine_dairesi_plan(c, K, ky, X0 + (X1 - X0) / 2 + 60, oy, k, r, tavan, kalin, ust_kat)
    else:
        # son döşeme planı (sağ yarı)
        sx0 = X0 + (X1 - X0) / 2 + 60; sy0 = oy
        toplam = ky[-1]['x0'] + ky[-1]['gen']; s = 1.0
        c.rect('ASN-DUVAR', sx0 - tw * s, sy0 - tw * s, sx0 + (toplam + tw) * s, sy0 + (D + tw) * s)
        c.tara('ASN-TARAMA', sx0 - tw * s, sy0 - tw * s, sx0 + (toplam + tw) * s, sy0 + (D + tw) * s, ara=30)
        for k_ in ky:
            a0 = sx0 + k_['x0'] * s; a1 = a0 + k_['gen'] * s
            c.rect('ASN-SIVA', a0, sy0, a1, sy0 + D * s)
            kc = kabin_x0(K, k_) + K['kabin_gen'] / 2
            o = kuyu_ic(c, K, k_, lambda u, v: (sx0 + u * s, sy0 + v * s), 0, 2.0 * k, False, kapi=False)
            # yalnız montaj kancası (kabin ekseni); makine duvar konsolunda olduğundan makine askı kancası yoktur
            for (qx, qy, ad_) in ((kc, o['ym'] - 45, 'MONTAJ KANCASI'),):
                q = (sx0 + qx * s, sy0 + qy * s)
                c.C('ASN-MOTOR', q, 4); c.C('ASN-MOTOR', q, 1.5)
                c.T('ASN-MOTOR', (q[0], q[1] - 6), ad_, 1.4 * k, 0, 'TC')
            c.T('ASN-MOTOR', (sx0 + o['xs'] * s, sy0 + (o['vh'] + 77) * s), 'MRL MAKİNE + DUVAR KONSOLU (kesikli)', 1.5 * k, 0, 'BC')
            c.T('ASN-BASLIK', ((a0 + a1) / 2, sy0 - 30), k_['ad'], 2.2 * k, 0, 'TC')
            c.rect('ASN-MOTOR', a1 - 45, sy0 + 10, a1 - 10, sy0 + 40)
            c.L('ASN-MOTOR', (a1 - 45, sy0 + 10), (a1 - 10, sy0 + 40)); c.L('ASN-MOTOR', (a1 - 45, sy0 + 40), (a1 - 10, sy0 + 10))
            c.T('ASN-MOTOR', (a1 - 27.5, sy0 + 44), 'duman tah. 35x30', 1.5 * k, 0, 'BC')
            c.olcu('ASN-OLCU', (a0, sy0 + D + tw), (a1, sy0 + D + tw), 30, 2.0 * k, f"{k_['gen']:.0f}")
        c.olcu('ASN-OLCU', (sx0 + toplam + tw, sy0), (sx0 + toplam + tw, sy0 + D), -30, 2.0 * k, f'{D:.0f}')
        c.T('ASN-UYARI', (sx0, sy0 + D + 100), f"SON DÖŞEME: alt +{f(tavan)} / üst +{f(tavan + kalin / 100)} - min {kalin:.0f} cm betonarme", 2.6 * k)
        c.T('ASN-BASLIK', (sx0, sy0 + D * s + 70), 'SON DÖŞEME (KUYU TAVANI) PLANI Ö:1/20', 3 * k)
        sd = [f"Son döşeme alt kotu +{f(tavan)}  (son durak +{f(ust_kat)} -> kuyu üst boşluğu {f(tavan-ust_kat)} m)",
              f"Mimaride döşeme kalınlığı {K['mimari_son_doseme_kalinlik']:.0f} cm -> en az {kalin:.0f} cm betonarme (statik hesaplı).",
              'Makine: dişlisiz MRL, kuyu tepesinde YAN PERDEYE ankrajlı 2xUPN duvar konsolu üzerinde; konsol altında çapraz askılı sehpa (kesikli).',
              f"Makine konsolu ile perdeye aktarılan düşey yük F = {f(r['F_kuyu_ustu']/1000,1)} kN (her kuyu); ankraj ve perde statikçe kontrol edilecektir.",
              'Makine askı kancası yoktur; kabin ekseninde yalnız montaj kancası (min 2000 kg, kapasite üzerine yazılır).',
              'Hız regülatörü ana (kabin) rayının yanında, ray ile yan duvar arasında; kabin arkasında kalmaz.',
              'Kuyu tavanında duman tahliye açıklığı (kuyu kesitinin en az %1i) bırakılır.']
        yazi_blok(c, sx0, sy0 - 50, sd, 2.0 * k)


    # ---------------- 8 KESİT YANDAN 1/50 ve 9 KARŞIDAN 1/50 (MRL iç sistem komple)
    for tur in ('YANDAN', 'KARŞIDAN'):
        p = yeni(50, 297, f'KUYU KESİTİ - {tur}', 'tam'); k = p.k; X0, Y0, X1, Y1 = p.ic()
        H_ = ((K['makine_dairesi']['cati_ust'] if md else tavan + kalin / 100) - dip + 0.4) * 100
        ust_ = Y1 - 40 * k                       # notların altı
        base_y = Y0 + 22 * k + max(0, (ust_ - Y0 - 22 * k - H_) / 2) - (dip - 0.4) * 100
        Z = lambda z: base_y + z * 100
        xs0 = X0 + 60 * k
        if tur == 'YANDAN':
            gen = K['derinlik']; parcalar = [(0, gen)]
        else:
            parcalar = [(k_['x0'], k_['x0'] + k_['gen']) for k_ in ky]
            gen = ky[-1]['x0'] + ky[-1]['gen']
        if md:
            MD = K['makine_dairesi']; zmd = MD['doseme_ust']; zmt = MD['tavan_alt']; zct = MD['cati_ust']
            etiket = kesit_ic_md(c, K, tur, ky, xs0, Z, dip, tavan, ust_kat, alt_kat, k, zmd, zmt)
            # makine dairesi duvarları ve çatı döşemesi
            for x_ in (xs0 - tw, xs0):
                c.L('ASN-DUVAR', (x_, Z(zmd)), (x_, Z(zmt)))
            if tur == 'YANDAN':
                kp0, kp1 = zmd, zmd + MD.get('kapi_h', 1.90)
                for x_ in (xs0 + gen, xs0 + gen + tw):
                    c.L('ASN-DUVAR', (x_, Z(kp1)), (x_, Z(zmt)))
                c.L('ASN-DUVAR', (xs0 + gen, Z(kp1)), (xs0 + gen + tw, Z(kp1)))
                c.rect('ASN-KAPI', xs0 + gen + 8, Z(kp0 + 0.02), xs0 + gen + 12, Z(kp1 - 0.02))
                etiket.append((xs0 + gen + 12, Z(kp0 + 1.0), f"MAKİNE DAİRESİ KAPISI (sahanlık +{f(MD['sahanlik'])}, döşeme +{f(zmd)})"))
            else:
                for x_ in (xs0 + gen, xs0 + gen + tw):
                    c.L('ASN-DUVAR', (x_, Z(zmd)), (x_, Z(zmt)))
            c.rect('ASN-DUVAR', xs0 - tw, Z(zmt), xs0 + gen + tw, Z(zct))
            c.tara('ASN-TARAMA', xs0 - tw, Z(zmt), xs0 + gen + tw, Z(zct), 8)
            c.kot('ASN-KOT', xs0 - tw - 70, Z(zmd), '+' + f(zmd), 2.0 * k)
            c.kot('ASN-KOT', xs0 - tw - 70, Z(zct), '+' + f(zct), 2.0 * k)
            c.T('ASN-BASLIK', (xs0 - tw - 118, Z(zmd) + 60), 'MAKİNE DAİRESİ', 2.4 * k)
            c.olcu('ASN-OLCU', (xs0 - tw - 150, Z(zmd)), (xs0 - tw - 150, Z(zmt)), 0, 2.0 * k, f'h={(zmt-zmd)*100:.0f}')
        else:
            etiket = kesit_ic(c, K, tur, ky, xs0, Z, dip, tavan, ust_kat, alt_kat, k)
        # duvarlar (yalnız düşey kenarlar - döşemelerle çakışmasın), YANDAN: kapı duvarında kat kapısı boşlukları
        for x_ in (xs0 - tw, xs0):
            c.L('ASN-DUVAR', (x_, Z(dip)), (x_, Z(tavan)))
        if tur == 'YANDAN':
            acik = [(z, z + 2.10) for z in K['durak_kotlari']]
            for x_ in (xs0 + gen, xs0 + gen + tw):
                zz0 = dip
                for (o0, o1) in acik:
                    c.L('ASN-DUVAR', (x_, Z(zz0)), (x_, Z(o0))); zz0 = o1
                c.L('ASN-DUVAR', (x_, Z(zz0)), (x_, Z(tavan)))
            for (o0, o1) in acik:
                c.L('ASN-DUVAR', (xs0 + gen, Z(o0)), (xs0 + gen + tw, Z(o0)))
                c.L('ASN-DUVAR', (xs0 + gen, Z(o1)), (xs0 + gen + tw, Z(o1)))
                c.rect('ASN-KAPI', xs0 + gen + 3, Z(o0 + 0.02), xs0 + gen + 7, Z(o1 - 0.02))      # kat kapısı kanatları
                c.rect('ASN-KAPI', xs0 + gen + 9, Z(o0 + 0.02), xs0 + gen + 13, Z(o1 - 0.02))
        else:
            for x_ in (xs0 + gen, xs0 + gen + tw):
                c.L('ASN-DUVAR', (x_, Z(dip)), (x_, Z(tavan)))
            for (a_, b_) in parcalar[:-1]:
                for x_ in (xs0 + b_, xs0 + b_ + K['ara_duvar']):
                    c.L('ASN-DUVAR', (x_, Z(dip)), (x_, Z(tavan)))
        # kuyu dibi döşemesi ve son döşeme (tam genişlik, kapalı, taralı)
        c.rect('ASN-DUVAR', xs0 - tw, Z(dip - 0.4), xs0 + gen + tw, Z(dip))
        c.tara('ASN-TARAMA', xs0 - tw, Z(dip - 0.4), xs0 + gen + tw, Z(dip), 10)
        c.rect('ASN-DUVAR', xs0 - tw, Z(tavan), xs0 + gen + tw, Z(tavan + kalin / 100))
        c.tara('ASN-TARAMA', xs0 - tw, Z(tavan), xs0 + gen + tw, Z(tavan + kalin / 100), 8)
        if md:
            pass
        else:
            c.T('ASN-UYARI', (xs0 - tw, Z(tavan + kalin / 100) + 26), f'SON DÖŞEME alt +{f(tavan)} / üst +{f(tavan + kalin / 100)} - min {kalin:.0f} cm BA', 2.2 * k, 0, 'BL')
        # kat döşemeleri (duvara bitişik kenar açık)
        for ad_, z in zip(K['durak_adlari'], K['durak_kotlari']):
            xa = xs0 - tw
            c.P('ASN-DUVAR', [(xa, Z(z - 0.15)), (xa - 120, Z(z - 0.15)), (xa - 120, Z(z)), (xa, Z(z))])
            c.tara('ASN-TARAMA', xa - 120, Z(z - 0.15), xa, Z(z), 6)
            xb = xs0 + gen + tw
            c.P('ASN-DUVAR', [(xb, Z(z - 0.15)), (xb + 60, Z(z - 0.15)), (xb + 60, Z(z)), (xb, Z(z))])
            c.kot('ASN-KOT', xa - 70, Z(z), ('+' if z > 0 else ('±' if z == 0 else '')) + f(z), 2.0 * k)
            c.T('ASN-BASLIK', (xa - 118, Z(z) + 30), ad_, 2.4 * k)
        # zemin kat dükkân döşemesi ±0,00 (referans, asansör durağı değil)
        if K.get('dukkan_kotu') is not None:
            zd = K['dukkan_kotu']
            c.L('ASN-EKSEN', (xs0 - tw - 120, Z(zd)), (xs0 - tw - 5, Z(zd)))
            c.T('ASN-KOT', (xs0 - tw - 118, Z(zd) + 4), '±0,00 ZEMİN DÜKKÂN', 1.7 * k, 0, 'BL')
            c.T('ASN-KOT', (xs0 - tw - 118, Z(zd) - 4), f"(dükkân h={f(K.get('dukkan_yuk', 4))} m)", 1.5 * k, 0, 'TL')
        c.kot('ASN-KOT', xs0 - tw - 70, Z(dip), f(dip), 2.0 * k)
        zsd = (K['makine_dairesi']['cati_ust'] if md else tavan + kalin / 100)
        c.kot('ASN-KOT', xs0 + gen + tw + 8, Z(zsd), '+' + f(zsd) + ' SON DÖŞEME', 2.0 * k)
        if md:
            c.kot('ASN-KOT', xs0 - tw - 25, Z(tavan), '+' + f(tavan) + ' kuyu tavanı', 1.6 * k)
        else:
            c.kot('ASN-KOT', xs0 - tw - 70, Z(tavan), '+' + f(tavan), 2.0 * k)
        # ölçüler (sağ)
        ox_ = xs0 + gen + tw + 75
        c.olcu('ASN-OLCU', (ox_, Z(dip)), (ox_, Z(alt_kat)), 0, 2.2 * k, f"KUYU DİBİ {f(K['kuyu_dibi'])}")
        c.olcu('ASN-OLCU', (ox_, Z(alt_kat)), (ox_, Z(ust_kat)), 0, 2.2 * k, f"SEYİR {f(K['seyir'])}")
        c.olcu('ASN-OLCU', (ox_, Z(ust_kat)), (ox_, Z(tavan)), 0, 2.2 * k, f"ÜST BOŞLUK {f(tavan-ust_kat)}")
        c.olcu('ASN-OLCU', (ox_ + 45, Z(dip)), (ox_ + 45, Z(tavan)), 0, 2.2 * k, f"KUYU MESAFESİ {f(tavan-dip)} m")
        zz = sorted(set(list(K['durak_kotlari']) + [dip] + ([K['dukkan_kotu']] if K.get('dukkan_kotu') is not None else [])))
        for z1, z2 in zip(zz, zz[1:]):
            c.olcu('ASN-OLCU', (xs0 - tw - 150, Z(z1)), (xs0 - tw - 150, Z(z2)), 0, 2.0 * k, f'{(z2-z1)*100:.0f}')
        if tur == 'YANDAN':
            c.olcu('ASN-OLCU', (xs0, Z(dip - 0.6)), (xs0 + gen, Z(dip - 0.6)), 0, 2.0 * k, f'{gen:.0f}')
        else:
            for (a_, b_) in parcalar:
                c.olcu('ASN-OLCU', (xs0 + a_, Z(dip - 0.6)), (xs0 + b_, Z(dip - 0.6)), 0, 2.0 * k, f'{b_-a_:.0f}')
        # etiketler: sağda sütun, yönlendirme çizgili
        LX = ox_ + 75
        hy = 1.9 * k; son = 1e9
        for (tx, ty, metin) in sorted(etiket, key=lambda e: -e[1]):
            ly = min(ty, son - hy * 1.9); son = ly
            c.L('ASN-YAZI', (tx, ty), (LX - 3, ly))
            c.C('ASN-YAZI', (tx, ty), 1.2)
            c.T('ASN-YAZI', (LX, ly), metin, hy, 0, 'ML')
        c.T('ASN-BASLIK', (X0, Y1 - 6 * k), f'ASANSÖR KUYUSU DİKİNE KESİTİ - {tur} GÖRÜNÜŞ', 3.2 * k)
        c.T('ASN-BASLIK', (X0, Y1 - 12 * k), ('Ölçek 1/50 - Makine daireli, 1/1 askı, makine çatıdaki makine dairesinde kaide üzerinde' if md else 'Ölçek 1/50 - Makine dairesiz (MRL), 2/1 askı, makine kuyu tepesinde duvar konsolunda (çapraz askılı, alttan sehpalı)'), 2.4 * k)
        nt = K['kesit_notlari'] if md else [f"Kuyu dibi {f(dip)} (mimaride: {K['mimari_kuyu_dibi']}). Son döşeme alt +{f(tavan)} / üst +{f(tavan + kalin / 100)}, min {kalin:.0f} cm BA.",
              'Makine: dişlisiz senkron (PM), Ø240 tahrik kasnağı, 7xØ6,5 halat; yan perdeye ankrajlı duvar konsolu + alttan çapraz askılı sehpa; makine askı kancası yoktur.',
              'Hız regülatörü ana ray yanında (kabin arkasında değil); kumanda panosu son durak kat kapısı yanında, kurtarma oradan yapılır.',
              'Kuyu aydınlatması her katta + kuyu dibi + kuyu tepesi, min 50 lüks; kuyu dibine pis su süzgeci konmaz, su yalıtımı yapılır.']
        yazi_blok(c, X0, Y1 - 19 * k, nt, 2.1 * k)

    # ---------------- sıkıştırılmış yerleşim + kapak (sol alt köşe, notlar üstünde) + ELEKTRİK DETAYLARI (setin sonunda, boşluksuz)
    xe = yerlestir()
    for sut in sutunlar:
        if sut.get('kapak'):
            kw, kh = sablon_yapistir(c, 'kapak_sablon', sut['X'], 0.0, 'ASN-ANTET', 'ASN-ANTET', sut['kapak'])
            hucreler.append((sut['X'], 0.0, kw, kh))
    ew, eh = sablon_yapistir(c, 'elektrik_detay', xe, (SERIT_H * m5 - 2920) / 2, 'ASN-ELEKTRIK', 'ASN-ELEKTRIK-YAZI')
    hucreler.append((xe, 0, ew, SERIT_H * m5))
    paftalar.append(('ELEKTRİK DETAYLARI', None))
    x = xe + ew

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
    ad = K.get('dosya_adi') or f"KORUCUK_{K['blok']}_BLOK_ASANSOR_AVAN"
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
