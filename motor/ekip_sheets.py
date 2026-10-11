"""Ekipman kütüphanesi paftası + 1/50 kazan dairesi ve yangın pompa dairesi örnekleri."""
import sys, math, pickle
sys.path.insert(0, '/home/claude/nb')
import cad
from cad import L, PL, C, T, RECT, ARC, ARROW, SOL, push, pop, MOVE
import ekipman as E
from ekipman import EQ, GZ, BA, KD, OL, YZ, DV, TR, YB, BG, BD, DIM, KOT, ETIKET, HATCH, BORU2

FR = []
TIT = 'MEK-BASLIK'
E.LAYERS[TIT] = (7, 'CONTINUOUS')
E.LAYERS['MEK-PAFTA'] = (7, 'CONTINUOUS')
E.LAYERS['MTY-DOGALGAZ'] = (2, 'CONTINUOUS')


def frame(x0, y0, x1, y1, title, sub=''):
    RECT(x0, y0, x1, y1, 'MEK-PAFTA'); RECT(x0 + 20, y0 + 20, x1 - 20, y1 - 20, 'MEK-PAFTA')
    T(((x0 + x1) / 2, y1 - 80), title, 35, TIT, 'C')
    if sub:
        T(((x0 + x1) / 2, y1 - 115), sub, 14, TIT, 'C')
    FR.append(((x0, y0, x1, y1), title, 1))


def wall(x0, y0, x1, y1):
    RECT(x0, y0, x1, y1, DV); HATCH(x0, y0, x1, y1, 12)


def door(x, y, w, ang, swing=1):
    """kapı: (x,y) menteşe, w kanat, ang duvar yönü (0: +x), swing iç(+1)/dış(-1)"""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy * swing, ux * swing
    L((x, y), (x + nx * w, y + ny * w), DV)
    pts = [(x + w * (ux * math.cos(t) + nx * math.sin(t)), y + w * (uy * math.cos(t) + ny * math.sin(t))) for t in [i * math.pi / 2 / 12 for i in range(13)]]
    PL(pts, GZ)


def menfez(x0, y0, x1, y1, txt, at, al='L'):
    RECT(x0, y0, x1, y1, EQ)
    n = 5
    for i in range(1, n):
        if (x1 - x0) > (y1 - y0):
            L((x0 + (x1 - x0) * i / n, y0), (x0 + (x1 - x0) * i / n, y1), EQ)
        else:
            L((x0, y0 + (y1 - y0) * i / n), (x1, y0 + (y1 - y0) * i / n), EQ)
    T(at, txt, 8, YZ, al)


# =========================================================== 1) KÜTÜPHANE PAFTASI
def kutuphane(ox, oy):
    items = list(E.VIEWS.items())
    cw, ch = 850.0, 820.0
    ncol = 7
    nrow = math.ceil(len(items) / ncol)
    W = ncol * cw + 200
    H = nrow * ch + 350
    frame(ox, oy, ox + W, oy + H, 'MEKANİK EKİPMAN BLOK KÜTÜPHANESİ  (PLAN / ÖN GÖRÜNÜŞ / YAN GÖRÜNÜŞ-KESİT)   ÖLÇEK : 1/50',
          'Ölçüler gerçek boyutta (cm). V: üretici verisi, T: tipik değer — uygulamada seçilen marka/modelin ölçü çizimiyle teyit edilir.')
    for k, (key, (fn, kw)) in enumerate(items):
        r, c = divmod(k, ncol)
        x = ox + 100 + c * cw
        y = oy + H - 200 - (r + 1) * ch
        RECT(x, y, x + cw, y + ch, 'MEK-PAFTA')
        d = E.DATA.get(kw.get('key', key), E.DATA.get(key, {}))
        nm = d.get('ad', key) + ('  (3 ADET KASKAD)' if key.endswith('x3') else '')
        T((x + 15, y + ch - 30), nm, 11, YZ, 'L')
        kay = d.get('kay', '')
        T((x + 15, y + ch - 48), kay[:95], 6.5, YZ, 'L')
        if len(kay) > 95:
            T((x + 15, y + ch - 58), kay[95:190], 6.5, YZ, 'L')
        # görünüşler
        big = fn in (E.yer_kazan, E.ahu, E.yangin_seti, E.grp_depo)
        try:
            if fn in (E.yer_kazan,):
                fn('P', (x + 140, y + 590), **kw); T((x + 40, y + 700), 'PLAN', 8, OL, 'L')
                fn('Y', (x + 160, y + 40), **kw); T((x + 40, y + 300), 'YAN GÖRÜNÜŞ', 8, OL, 'L')
                fn('O', (x + 700, y + 40), **kw); T((x + 640, y + 300), 'ÖN', 8, OL, 'L')
            elif fn is E.yangin_seti:
                fn('P', (x + 80, y + 450), **kw)
                fn('Y', (x + 80, y + 40), **kw); T((x + 40, y + 260), 'DİZEL MODÜL YAN GÖRÜNÜŞ', 8, OL, 'L')
                fn('O', (x + 600, y + 40), **kw)
            elif fn is E.grp_depo:
                fn('P', (x + 60, y + 470), **kw)
                fn('O', (x + 60, y + 40), **kw)
                fn('Y', (x + 330, y + 40), **kw)
            elif fn is E.ahu:
                fn('P', (x + 60, y + 470), **kw)
                fn('O', (x + 60, y + 40), **kw)
            elif fn in (E.kombi, E.duvar_kazan):
                fn('P', (x + 300, y + 620), **kw); L((x + 150, y + 620), (x + 450, y + 620), DV)
                fn('O', (x + 300, y + 20), **kw); L((x + 100, y + 20), (x + 500, y + 20), DV)
                if fn is E.kombi:
                    fn('Y', (x + 620, y + 20), **kw); L((x + 620, y + 20), (x + 620, y + 330), DV)
            elif fn is E.kaset:
                fn('P', (x + 300, y + 550), **kw)
                fn('O', (x + 300, y + 300), **kw); L((x + 150, y + 300), (x + 450, y + 300), DV)
            elif fn in (E.boyler, E.genlesme, E.denge_kabi, E.membranli, E.jokey, E.hidrant):
                fn('P', (x + 200, y + 620), **kw)
                fn('O', (x + 450, y + 60 + (150 if fn is E.hidrant else 0)), **kw)
                L((x + 300, y + 60 + (150 if fn is E.hidrant else 0)), (x + 650, y + 60 + (150 if fn is E.hidrant else 0)), DV)
            elif fn is E.pompa_inline:
                fn('P', (x + 300, y + 600), **kw)
                fn('O', (x + 300, y + 200), **kw)
            elif fn is E.esanjor:
                fn('P', (x + 300, y + 600), **kw)
                fn('O', (x + 300, y + 100), **kw)
            elif fn in (E.pano, E.yangin_dolabi):
                fn('P', (x + 300, y + 560), **kw)
                fn('O', (x + 300, y + 40), **kw)
            elif fn is E.alarm_vana:
                fn('P', (x + 200, y + 620), **kw)
                fn('O', (x + 400, y + 40), **kw)
            else:
                fn('P', (x + 300, y + 560), **kw)
                fn('O', (x + 300, y + 60), **kw)
        except Exception as ex:
            T((x + 50, y + 300), 'HATA: %s' % ex, 10, YZ, 'L')
    # armatür satırı
    return (ox, oy, ox + W, oy + H)


# =========================================================== 2) KAZAN DAİRESİ
def kazan_dairesi(ox, oy):
    W, H = 3600.0, 2600.0
    frame(ox, oy, ox + W, oy + H, 'KAZAN DAİRESİ PLANI VE KESİTLERİ   ÖLÇEK : 1/50',
          'ÖRNEK DETAY: 2 x 285 kW YER TİPİ YOĞUŞMALI KAZAN (TOPLAM 570 kW), DOĞALGAZ, 1000 L BOYLER, 3 ZONLU KOLLEKTÖR')
    # ------------------- PLAN
    X, Y = ox + 250, oy + 1350           # oda iç köşesi (GB)
    RW, RD, tw = 900.0, 650.0, 25.0
    wall(X - tw, Y - tw, X + RW + tw, Y); wall(X - tw, Y + RD, X + RW + tw, Y + RD + tw)
    wall(X - tw, Y, X, Y + RD); wall(X + RW, Y, X + RW + tw, Y + RD)
    T((X + RW / 2, Y + RD + 70), 'KAZAN DAİRESİ PLANI', 18, TIT, 'C')
    T((X + RW / 2, Y + RD + 45), 'İÇ ÖLÇÜ 9,00 x 6,50 m  -  NET YÜKSEKLİK ≥ 3,00 m  -  DUVAR/DÖŞEME 120 dk, KAPILAR 90 dk YANGIN DAYANIMLI', 9, YZ, 'C')
    # kapılar (iki kapı: 570 kW > 350 kW) - dışa açılır
    for (x0, x1) in ((X + 60, X + 210),):
        RECT(x0, Y - tw, x1, Y, 'MEK-PAFTA')
    door(X + 60, Y - tw, 75, 0, -1); door(X + 210, Y - tw, 75, 180, 1)
    T((X + 135, Y - tw - 90), 'K1 150x220 ÇİFT KANAT (EKİPMAN GİRİŞİ) 90 dk, DIŞA AÇILIR', 7, YZ, 'C')
    RECT(X + RW - tw, Y + RD - 210, X + RW + tw, Y + RD - 110, 'MEK-PAFTA')
    door(X + RW + tw, Y + RD - 110, 100, -90, 1)
    T((X + RW + tw + 110, Y + RD - 160), 'K2 100x210 KAÇIŞ KAPISI 90 dk', 7, YZ, 'L')
    # kazanlar (ön batı tarafı, kazan önü = boy + 100)
    bx = X + 290
    for i, yc in enumerate((Y + 160, Y + 400)):
        E.yer_kazan('P', (bx, yc), key='YKAZAN285')
        T((bx + 90, yc), 'K-%d' % (i + 1), 12, YZ, 'MC')
    DIM((X, Y + 520), (bx, Y + 520), 0, txt='290 (KAZAN BOYU 179 + 100)')
    DIM((bx, Y + 60), (bx + 179, Y + 60), 0)
    DIM((bx + 250, Y + 160 - 45.8), (bx + 250, Y + 400 - 45.8), 0)
    # baca şaftı + bağlantılar
    cx0, cy0 = X + 600, Y + 255
    RECT(cx0, cy0, cx0 + 60, cy0 + 60, DV); C((cx0 + 30, cy0 + 30), 15, EQ)
    T((cx0 + 70, cy0 + 30), 'ORTAK BACA Ø300 (TS EN 13384 HESABI)', 7, YZ, 'L')
    for yc in (Y + 160, Y + 400):
        PL([(bx + 154, yc), (bx + 154 + 30, yc), (cx0 + 30, cy0 + 30 + (15 if yc > cy0 else -15))], EQ)
        T((bx + 200, yc + (12 if yc > cy0 else -18)), 'Ø200 BACA BAĞLANTISI %3 YÜKSELEN', 6, YZ, 'L')
    # kollektör (kuzey duvarı boyunca, planda)
    kx, ky = X + 280, Y + RD - 70
    E.kollektor('P', (kx, ky), n=3, dn=100, ara=100, uzun=420)
    T((kx + 210, ky + 42), 'GİDİŞ / DÖNÜŞ KOLLEKTÖRÜ DN100 (zemin +1,20 / +0,60)', 7, YZ, 'C')
    # denge kabı + genleşme + boyler + pompalar
    E.denge_kabi('P', (X + 760, Y + RD - 70), key='DENGE100')
    T((X + 760, Y + RD - 120), 'DENGE KABI DN100', 7, YZ, 'C')
    for i, xx in enumerate((X + 120, X + 200)):
        E.genlesme('P', (xx, Y + RD - 60), key='GEN300')
    T((X + 160, Y + RD - 110), '2 x 300 L KAPALI GENLEŞME TANKI', 7, YZ, 'C')
    E.boyler('P', (X + 780, Y + 120), key='BOYLER1000')
    T((X + 780, Y + 120), 'BOYLER 1000 L', 8, YZ, 'MC')
    for i in range(3):
        E.pompa_inline('P', (kx + 100 * (i + 1), ky - 45), key='POMPA80', ang=90)
        T((kx + 100 * (i + 1) + 18, ky - 45), ['P1 RADYATÖR', 'P2 YERDEN ISITMA', 'P3 BOYLER'][i], 6, YZ, 'L')
    # menfezler
    menfez(X + 400, Y - tw, X + 450, Y, '', (0, 0))
    T((X + 425, Y - tw - 30), 'ALT TAZE HAVA MENFEZİ 40x40 (A ≥ 1600 cm²) zemin +0,30', 7, YZ, 'C')
    menfez(X + RW, Y + 420, X + RW + tw, Y + 470, '', (0, 0))
    T((X + RW + tw + 10, Y + 445), 'ÜST EGZOZ MENFEZİ 30x35 (A ≥ 960 cm² = %60) tavan altı', 7, YZ, 'L')
    # gaz
    gz = 'MTY-DOGALGAZ'
    PL([(X - tw - 120, Y + 300), (X + 40, Y + 300), (X + 40, Y + 400), (bx - 5, Y + 400)], gz)
    L((X + 40, Y + 160), (bx - 5, Y + 160), gz); L((X + 40, Y + 300), (X + 40, Y + 160), gz)
    C((X - tw - 60, Y + 300), 6, gz); T((X - tw - 60, Y + 315), 'DIŞTA ACİL KESME VANASI + SELENOİD', 6.5, YZ, 'C')
    T((X - tw - 120, Y + 285), 'DOĞALGAZ (SAYAÇ DIŞARIDA)', 6.5, YZ, 'L')
    C((X + 50, Y + RD - 30), 6, EQ); T((X + 60, Y + RD - 30), 'GAZ ALARM DEDEKTÖRÜ (TAVAN)', 6, YZ, 'L')
    # yer süzgeci / nötralizasyon
    for p in ((X + 520, Y + 280), (X + 240, Y + 40)):
        RECT(p[0] - 7.5, p[1] - 7.5, p[0] + 7.5, p[1] + 7.5, EQ); L((p[0] - 7.5, p[1] - 7.5), (p[0] + 7.5, p[1] + 7.5), EQ)
    T((X + 535, Y + 280), 'YER SÜZGECİ + KONDENS NÖTRALİZASYON', 6, YZ, 'L')
    # kesit izleri
    for (a, b, t) in (((X - 120, Y + 160), (X + RW + 120, Y + 160), 'A'), ((X + 700, Y + RD + 120), (X + 700, Y - 120), 'B')):
        L(a, b, 'MEK-OLCU')
        for p in (a, b):
            C(p, 14, OL); T(p, t, 12, OL, 'MC')
    # ------------------- KESİT A-A (kazan boyunca)
    sx, sy = ox + 1450, oy + 1350
    hh = 320.0
    T((sx + 450, sy + hh + 150), 'KESİT A-A', 18, TIT, 'C')
    wall(sx - tw, sy - 30, sx + RW + tw, sy)                       # döşeme
    wall(sx - tw, sy + hh, sx + RW + tw, sy + hh + 30)             # tavan döşemesi
    wall(sx - tw, sy, sx, sy + hh); wall(sx + RW, sy, sx + RW + tw, sy + hh)
    E.yer_kazan('Y', (sx + 290, sy), key='YKAZAN285')
    KOT((sx + 40, sy), '±0,00'); KOT((sx + 40, sy + hh), '+3,20 TAVAN')
    # baca: kazan çıkışı → %3 yükselen → baca → çatı
    fx = sx + 290 + 179 - 25
    PL([(fx, sy + 10 + 145 + 25), (fx, sy + 230), (sx + 630, sy + 236)], EQ)
    PL([(fx + 20, sy + 10 + 145 + 25), (fx + 20, sy + 210), (sx + 630, sy + 216)], EQ)
    RECT(sx + 630, sy, sx + 690, sy + hh + 30, DV); L((sx + 645, sy + 20), (sx + 645, sy + hh + 30), EQ); L((sx + 675, sy + 20), (sx + 675, sy + hh + 30), EQ)
    RECT(sx + 630, sy + 25, sx + 690, sy + 60, EQ); T((sx + 700, sy + 40), 'TEMİZLEME KAPAĞI + KONDENS DRENAJI', 6, YZ, 'L')
    T((sx + 700, sy + 240), 'BAĞLANTI %3 (≈3°) YÜKSELEREK BACAYA', 6, YZ, 'L')
    T((sx + 700, sy + hh - 10), 'BACA MAHYAYI AŞARAK ÇATIYA', 6, YZ, 'L')
    menfez(sx - tw, sy + 30, sx, sy + 70, '', (0, 0)); T((sx - tw - 5, sy + 50), 'ALT MENFEZ +0,30', 7, YZ, 'R')
    menfez(sx + RW, sy + hh - 50, sx + RW + tw, sy + hh - 15, '', (0, 0)); T((sx + RW + tw + 5, sy + hh - 30), 'ÜST EGZOZ', 7, YZ, 'L')
    DIM((sx + 290, sy + 10), (sx + 290, sy + 155), -40)
    DIM((sx, sy - 60), (sx + 290, sy - 60), 0)
    DIM((sx + 290, sy - 60), (sx + 469, sy - 60), 0)
    DIM((sx + RW + 60, sy), (sx + RW + 60, sy + hh), 0)
    T((sx + 380, sy + 18), 'BETONARME KAİDE h=10 cm (KAZAN İZİNDEN 10 cm TAŞKIN)', 6, YZ, 'L')
    # ------------------- GÖRÜNÜŞ B-B (kuzey duvarı: kollektör, pompalar, denge kabı, genleşme)
    vx, vy = ox + 1450, oy + 300
    T((vx + 450, vy + hh + 150), 'GÖRÜNÜŞ B-B (KOLLEKTÖR DUVARI)', 18, TIT, 'C')
    wall(vx - tw, vy - 30, vx + RW + tw, vy); wall(vx - tw, vy + hh, vx + RW + tw, vy + hh + 30)
    wall(vx - tw, vy, vx, vy + hh); wall(vx + RW, vy, vx + RW + tw, vy + hh)
    E.kollektor('O', (vx + 280, vy + 70), n=3, dn=100, ara=100, uzun=420)
    for i in range(3):
        E.pompa_inline('O', (vx + 380 + 100 * i, vy + 70 + 60 + 85), key='POMPA80', ang=90, dn=80)
        L((vx + 380 + 100 * i, vy + 70 + 60 + 105), (vx + 380 + 100 * i, vy + hh - 10), BG)
        L((vx + 380 + 100 * i, vy + 70 - 40), (vx + 380 + 100 * i, vy + 20), BD)
        PL([(vx + 380 + 100 * i, vy + 20), (vx + 380 + 100 * i + 25, vy + 20), (vx + 380 + 100 * i + 25, vy + hh - 10)], BD)
        T((vx + 380 + 100 * i - 6, vy + hh - 60), ['RADYATÖR ZONU', 'YERDEN ISITMA', 'BOYLER'][i], 6, YZ, 'R', 90)
    E.denge_kabi('O', (vx + 790, vy + 30), key='DENGE100')
    PL([(vx + 790 - 13.65 - 20, vy + 30 + 127.5), (vx + 700, vy + 30 + 127.5), (vx + 700, vy + 130), (vx + 700, vy + 130)], BG)
    for i, xx in enumerate((vx + 90, vx + 170)):
        E.genlesme('O', (xx, vy), key='GEN300')
    T((vx + 130, vy + 125), '2 x 300 L', 7, YZ, 'C')
    KOT((vx + 20, vy + 130), '+1,30 GİDİŞ KOLL. EKSENİ'); KOT((vx + 20, vy + 70), '+0,70 DÖNÜŞ KOLL. EKSENİ')
    # ------------------- NOTLAR
    nx_, ny_ = ox + 250, oy + 1000
    notes = [
        'NOTLAR:',
        '1. Kazan önü ile karşı duvar arası en az kazan boyu + 1,00 m bırakılacaktır (ÇŞB ısıtma tesisatı şartnamesi 3.3).',
        '2. Kazanlar arası ve kazan-duvar arası servis boşlukları üretici montaj kılavuzundaki değerlerden az olmayacaktır (yan ≥ 50 cm, arka ≥ 70 cm).',
        '3. 350 kW üzeri gazlı ısı merkezinde iki ayrı kapı yapılacak, kapılar 90 dk yangına dayanıklı, kendiliğinden kapanan ve dışa açılan olacaktır.',
        '4. Kazan dairesi duvar ve döşemeleri en az 120 dk yangına dayanıklı yapılacaktır (BYKHY md. 24 ve şartname 3.3.3).',
        '5. Alt taze hava menfezi serbest kesiti A = 300 + (Q-50) x 2,5 cm² (Q kW) formülüyle hesaplanacak, üst egzoz menfezi alt menfezin %60\'ı olacaktır.',
        '6. Doğalgaz sayacı, acil kesme vanası ve ana elektrik şalteri kazan dairesi dışında kolay ulaşılır yerde olacak; gaz dedektörü selenoid vanayı kesecektir.',
        '7. Kazanlar 10 cm yüksekliğinde, kazan izinden her yönde 10 cm taşkın betonarme kaide üzerine titreşim yalıtımıyla oturtulacaktır.',
        '8. Baca bağlantısı %3 yükselerek bacaya girecek; bacanın dibinde temizleme kapağı ve kondens drenajı bulunacak; baca kesiti TS EN 13384 ile hesaplanacaktır.',
        '9. Kondens suyu nötralizasyon ünitesinden geçirilerek yer süzgecine verilecektir; kanal kotu altındaki dairelerde pis su çukuru ve yedekli pompa yapılacaktır.',
        '10. Ekipman ölçüleri seçilen marka/model kataloğundan teyit edilerek kesin projeye işlenecektir.',
    ]
    for i, t in enumerate(notes):
        T((nx_, ny_ - i * 20), t, 9 if i else 12, YZ, 'L')


# =========================================================== 3) YANGIN POMPA DAİRESİ
def pompa_dairesi(ox, oy):
    W, H = 3600.0, 2600.0
    frame(ox, oy, ox + W, oy + H, 'YANGIN POMPA DAİRESİ PLANI VE KESİTİ   ÖLÇEK : 1/50',
          'ÖRNEK DETAY: TS EN 12845 ELEKTRİKLİ ASIL + DİZEL YEDEK POMPA (DAB 1 KDN 40-250 E+D ÖLÇÜLERİ) + JOKEY, 72 m³ GRP YANGIN SUYU DEPOSU')
    X, Y = ox + 900, oy + 1350
    RW, RD, tw = 600.0, 450.0, 25.0
    wall(X - tw, Y - tw, X + RW + tw, Y); wall(X - tw, Y + RD, X + RW + tw, Y + RD + tw)
    wall(X - tw, Y, X, Y + RD); wall(X + RW, Y, X + RW + tw, Y + RD)
    T((X + RW / 2, Y + RD + 120), 'YANGIN POMPA DAİRESİ PLANI', 18, TIT, 'C')
    T((X + RW / 2, Y + RD + 95), 'İÇ ÖLÇÜ 6,00 x 4,50 m - ODA SICAKLIĞI ≥ +10 °C (DİZEL) - 120 dk YANGIN DAYANIMLI AYRI BÖLME', 9, YZ, 'C')
    # depo (batı)
    E.grp_depo('P', (X - tw - 640, Y - 20), nx=6, ny=4, nz=3)
    T((X - tw - 640 + 307, Y - 60), 'GRP YANGIN SUYU DEPOSU 6x4x3 m = 72 m³ (DIŞ 6,15 x 4,15 m)', 8, YZ, 'C')
    # pompalar
    ex, ey = X + 120, Y + 110
    E.yangin_seti('P', (ex, ey))
    dy = ey + 80 + (97.8 - 54) / 2
    # emişler: depodan duvar içinden
    for yy, dnp in ((ey, 100), (dy, 100)):
        BORU2((X - tw - 25, yy), (ex - 5, yy), 150, YB)
        E.VANA_OSY((X + 45, yy), 150, 0)
        E.EKS_RED((ex - 20, yy), 150, 100, 0)
    T((X + 45, ey - 40), 'OS&Y SÜRGÜLÜ VANA DN150', 6, YZ, 'C')
    T((ex - 20, dy + 45), 'EKSANTRİK RED. DN150/100 (DÜZ ÜST)', 6, YZ, 'C')
    # basma: volandan yükselip doğuya, ortak kolektör x=430
    hx = X + 430
    for yy in (ey, dy):
        C((ex + 25, yy), 6, YB)
        BORU2((ex + 25, yy), (hx, yy), 100, YB)
        T((ex + 33, yy + 8), 'ÇEK VALF + OS&Y DÜŞEYDE', 5, YZ, 'L')
    BORU2((hx, ey - 20), (hx, Y + RD - 40), 150, YB)
    BORU2((hx, Y + 320), (X + RW + tw + 60, Y + 320), 150, YB)
    T((X + RW + tw + 65, Y + 320), 'SİSTEME (SPRINKLER + DOLAP) DN150', 7, YZ, 'L')
    T((X + 300, ey + 45), 'BASMA HATLARI +3,00 KOTUNDA (TAVANDAN)', 6, YZ, 'C')
    # test hattı + debimetre → depoya geri
    PL([(hx, Y + RD - 40), (hx - 20, Y + RD - 40), (X - tw - 25, Y + RD - 40)], YB)
    RECT(X + 250, Y + RD - 48, X + 290, Y + RD - 32, EQ)
    T((X + 270, Y + RD - 60), 'TEST HATTI DN80 + DEBİMETRE → DEPOYA', 6, YZ, 'C')
    # jokey + membranlı tank
    E.jokey('P', (X + 520, Y + 120)); E.membranli('P', (X + 540, Y + 220), key='MTANK300')
    T((X + 520, Y + 85), 'JOKEY CR10-9', 6, YZ, 'C'); T((X + 540, Y + 260), 'MEMBRANLI TANK', 6, YZ, 'C')
    # panolar
    E.pano('P', (X + 120, Y + RD - 40 - 0)) if False else None
    for i, xx in enumerate((X + 80, X + 180)):
        RECT(xx - 40, Y + RD - 40, xx + 40, Y + RD, EQ)
        T((xx, Y + RD - 52), ['ELEKTRİK POMPA PANOSU', 'DİZEL POMPA PANOSU'][i], 5.5, YZ, 'C')
    E.BAKIM(X + 40, Y + RD - 140, X + 220, Y + RD - 40, 'PANO ÖNÜ ≥ 100')
    # dizel yakıt tankı + egzoz
    RECT(X + 330, Y + 15, X + 430, Y + 75, EQ); RECT(X + 320, Y + 5, X + 440, Y + 85, GZ)
    T((X + 380, Y + 45), 'YAKIT TANKI (6 SAAT) + TAŞMA HAVUZU', 5.5, YZ, 'C')
    exh = (ex + 157.6 * 0.6, dy + 97.8 / 2 - 18)
    PL([exh, (exh[0], Y + RD + tw + 40)], EQ)
    T((exh[0] + 30, Y + RD + tw + 25), 'DİZEL EGZOZU (YALITIMLI) - SUSTURUCU BİNA DIŞINDA', 6.5, YZ, 'L')
    # menfezler
    menfez(X + RW, dy - 40, X + RW + tw, dy + 40, '', (0, 0))
    T((X + RW + tw + 5, dy + 50), 'RADYATÖR ÇIKIŞ PANJURU (≥ RADYATÖR ALANI)', 6.5, YZ, 'L')
    menfez(X + 250, Y - tw, X + 330, Y, '', (0, 0))
    T((X + 290, Y - tw - 25), 'ALT HAVA GİRİŞ PANJURU', 6.5, YZ, 'C')
    # kapı
    RECT(X + 480, Y - tw, X + 580, Y, 'MEK-PAFTA'); door(X + 580, Y - tw, 100, 180, -1)
    T((X + 530, Y - tw - 55), 'KAPI 100x210, 90 dk, DIŞARIDAN DOĞRUDAN ERİŞİM', 6.5, YZ, 'C')
    # yer süzgeci
    p = (X + 300, Y + 170); RECT(p[0] - 7.5, p[1] - 7.5, p[0] + 7.5, p[1] + 7.5, EQ); T((p[0] + 10, p[1]), 'YER SÜZGECİ', 6, YZ, 'L')
    # kesit izi
    a, b = (X - tw - 700, dy), (X + RW + 120, dy)
    L(a, b, OL)
    for pp in (a, b):
        C(pp, 14, OL); T(pp, 'A', 12, OL, 'MC')
    DIM((X, Y - 90), (X + RW, Y - 90), 0); DIM((X + RW + 120, Y), (X + RW + 120, Y + RD), 0)
    DIM((ex, ey - 70), (ex + 125, ey - 70), 0)
    # ------------------- KESİT A-A
    sx, sy = ox + 1700, oy + 300
    hh = 400.0
    T((sx + 600, sy + hh + 200), 'KESİT A-A', 18, TIT, 'C')
    wall(sx - 680, sy - 30, sx + RW + tw, sy)
    wall(sx - 680, sy + hh, sx + RW + tw, sy + hh + 30)
    wall(sx - tw, sy, sx, sy + hh); wall(sx + RW, sy, sx + RW + tw, sy + hh)
    E.grp_depo('O', (sx - tw - 640, sy), nx=6, ny=4, nz=3, kaide=20)
    y_tank0 = sy + 20
    L((sx - tw - 630, y_tank0 + 85), (sx - tw - 30, y_tank0 + 85), GZ)
    T((sx - tw - 330, y_tank0 + 89), 'MİN. SU SEVİYESİ (VORTEKS PLAKASI ÜSTÜ)', 6, YZ, 'C')
    # emiş: depo dibinden → yatay, pompaya hafif yükselen
    ax_ = sy + 15 + 12 + 35
    RECT(sx - tw - 120, ax_ - 40, sx - tw - 117, ax_, EQ)
    T((sx - tw - 120, y_tank0 + 5), 'VORTEKS ÖNLEYİCİ PLAKA', 5, YZ, 'TC')
    BORU2((sx - tw - 117, ax_ - 20), (sx - tw - 40, ax_ - 20), 150, YB)
    BORU2((sx - tw - 40, ax_ - 20), (sx + 60, ax_ - 20), 150, YB)
    E.VANA_OSY((sx + 45, ax_ - 20), 150, 0)
    E.EKS_RED((sx + 100, ax_ - 12), 150, 100, 0)
    PL([(sx + 110, ax_), (sx + 115, ax_)], YB)
    E.yangin_seti('Y', (sx + 120, sy), kaide=15)
    vx = sx + 120 + 25
    vy = ax_ + 45
    BORU2((vx, vy), (vx, sy + 300), 100, YB)
    E.CEK_VALF((vx, vy + 50), 100, 90); E.VANA_OSY((vx, vy + 110), 100, 0)
    BORU2((vx, sy + 300), (sx + 430, sy + 300), 150, YB)
    E.MANO((vx + 20, sy + 305))
    KOT((sx + 20, sy), '±0,00'); KOT((sx + 440, sy + 300), '+3,00 KOLEKTÖR EKSENİ')
    KOT((sx - tw - 600, y_tank0 + 315), 'DEPO ÜST +3,35')
    # dizel egzoz
    exx = sx + 120 + 157.6 * 0.55 + 6
    PL([(exx, sy + 15 + 179.5 - 5), (exx, sy + hh - 40), (sx + RW + tw + 80, sy + hh - 40)], EQ)
    T((sx + RW + tw + 85, sy + hh - 40), 'EGZOZ ≤ 10 m, ≤ 6 DİRSEK', 6.5, YZ, 'L')
    menfez(sx + RW, sy + 60, sx + RW + tw, sy + 180, '', (0, 0))
    T((sx + RW + tw + 5, sy + 120), 'RADYATÖR HAVA ÇIKIŞ PANJURU', 6.5, YZ, 'L')
    DIM((sx + 120, sy - 70), (sx + 277.6, sy - 70), 0)
    DIM((sx + RW + 150, sy), (sx + RW + 150, sy + hh), 0)
    T((sx + 120, sy + 5), '', 1, YZ)
    # notlar
    nx_, ny_ = ox + 250, oy + 1000
    notes = [
        'NOTLAR:',
        '1. Pompalar TS EN 12845\'e göre pozitif emişli kurulacak; emiş ağzı ile en düşük su seviyesi farkı 3,2 m\'yi geçmeyecektir.',
        '2. Her pompanın ayrı emiş hattı olacak; emiş hattı pompaya doğru hafif yükselen, hava cebi bırakmayan şekilde döşenecektir.',
        '3. Emişte OS&Y sürgülü vana ve düz tarafı üstte eksantrik redüksiyon kullanılacak; emiş hattında kelebek vana kullanılmayacaktır.',
        '4. Pompa dairesi sıcaklığı dizel pompa için +10 °C, elektrikli pompa için +4 °C altına düşmeyecektir.',
        '5. Dizel yakıt tankı en az 6 saat çalışmaya yetecek hacimde olacak ve taşma havuzu içinde bulunacaktır.',
        '6. Dizel motor radyatör hava giriş ve çıkış açıklıkları radyatör alanından küçük olmayacaktır.',
        '7. Egzoz borusu en fazla 10 m ve 6 dirsekle bina dışına alınacak, yalıtılacak; susturucu bina dışında olacaktır.',
        '8. Test hattı debimetre üzerinden depoya geri döndürülecektir.',
        '9. Pompalar 15 cm yüksekliğinde, şasi izinden 10 cm taşkın betonarme kaide üzerine oturtulacaktır.',
        '10. Panoların önünde en az 1,00 m serbest alan bırakılacaktır.',
        '11. Pompa ve vana ölçüleri seçilen onaylı (EN 12845 / LPCB / VdS) setin üretici çiziminden teyit edilecektir.',
    ]
    for i, t in enumerate(notes):
        T((nx_, ny_ - i * 20), t, 9 if i else 12, YZ, 'L')


if __name__ == '__main__':
    cad.R.clear()
    lib = kutuphane(0.0, 0.0)
    kazan_dairesi(0.0, -3000.0)
    pompa_dairesi(3800.0, -3000.0)
    for i, r in enumerate(cad.R):
        if r[0] == 'T' and r[1] in (YZ, OL, BA) and r[4] < 10:
            cad.R[i] = r[:4] + (min(10.0, r[4] * 1.5),) + r[5:]
    pickle.dump((cad.R, FR, None), open('/tmp/claude-0/ekip_full.pkl', 'wb'))
    print(len(cad.R), FR)
