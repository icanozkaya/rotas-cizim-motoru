"""R4 şema paftaları (sema3 kopyası; R4: sayaç düzeni planla aynı - çatı deposu → ADK → her katta daire kapısında sayaç,
zeminde toplu sayaç YOK, sayaç hatları kesişmez; SIHHİ DETAYLAR çerçevesi içerikten).
R3 şema paftaları (sema.py kopyası; MTY detay bloğu yok, sağda WC/banyo havalandırma kolonları + çatı fanı).
Eski açıklama: Şema paftaları: açılımlı kolon şeması (p2/gsheet.sihhi_sema), rögar şeması, yağmur şeması + hesabı, antet / notlar /
lejant, SIHHİ DETAYLAR bloğu, pafta çerçeveleri. nb.py'nin global durumunu (KOLS, DATA, STATS_SB, ROG...) okur."""
import math
import cad
from cad import L, PL, C, T, RECT
import mtyblk
import gp
from gp import CS, PS, PSC, YZ, CD, fmt, dn_temiz, cap_temiz
import gsheet as GS

ORDER = ['WC', 'LV', 'DUS', 'CM', 'YS', 'EV', 'BM']


def ciz(G, HAV=None):
    KOLS, DATA, M, FL = G['KOLS'], G['DATA'], G['M'], G['FL']
    SX0, SLOT, FH = G['SX0'], G['SLOT'], G['FH']
    DZ = DATA['Z']
    YB = G['YB']
    OY = 150.0
    # ---- daire konumları (zemin daire no) ve üst katlardaki karşılıkları (aynı plandaki yer)
    pos = {}
    for k in FL:
        for (p, n) in DATA[k]['digits']:
            q = (round(p[0] - M.OFF[k]), round(p[1]))
            key = min(pos, key=lambda z: math.hypot(z[0] - q[0], z[1] - q[1])) if pos else None
            if key is None or math.hypot(key[0] - q[0], key[1] - q[1]) > 40:
                pos[q] = {}
                key = q
            pos[key][k] = n
    cols = sorted(pos.values(), key=lambda v: v.get('Z', 99))
    groups, units = [], []
    cur = 380.0
    yb_of = {}
    for k in FL:
        for f in DATA[k]['F']:
            if f.get('daire') and f['kind'] in YB:
                yb_of[f['daire']] = yb_of.get(f['daire'], 0.0) + YB[f['kind']]
    for gi, cmap in enumerate(cols):
        dz = cmap['Z']
        ks = [c for c in KOLS if c['d0'] == dz]
        ks.sort(key=lambda c: {'BANYO': 0, 'DUŞ': 1, 'WC': 2, 'MUTFAK': 3}[c['typ']])
        rows = []
        x = cur + 160.0
        kol = []
        for c in ks:
            src = DZ
            w = [w_ for w_ in DZ['wet'] if G['kolon_of']('Z', w_) is c]
            if not w and c.get('kat_ozel'):          # yalnız üst katta olan ıslak hacim (kat planı farklılığı)
                src = DATA[c['kat_ozel']]
                w = [w_ for w_ in src['wet'] if G['kolon_of'](c['kat_ozel'], w_) is c]
            # aynı türden birden çok armatür varsa (ör. 2 YS) tekrarla
            keys = []
            for w_ in w:
                keys += [f['kind'] for f in src['F'] if f['room'] is w_ and f['kind'] in ORDER]
            if not keys:
                keys = ['YS']
            keys.sort(key=ORDER.index)
            rows.append((x, keys, c))
            base = G['STATS_SB'][c['name']]
            sbf = (lambda b: (lambda i: sum(b.get(f, 0) for f in FL[i:])))(base)
            kol.append((c['name'], x - SX0 + SX0, c['dn'], sbf))
            x += 120 + 140 * max(1, len(keys)) + 130
        kombi = x + 20
        g = dict(x=cur, pkx=rows[0][0], bkeys=rows[0][1], extra=[dict(kx=r[0], keys=r[1]) for r in rows[1:-1]],
                 mkx=rows[-1][0], mkeys=rows[-1][1], kombi=kombi, ikeys=[],
                 units={k: ('D%d' % cmap[k], 'daire') for k in FL if k in cmap},
                 kolons=[(n, xx, dn, sb) for n, xx, dn, sb in kol])
        groups.append(g)
        for k in FL:
            if k in cmap:
                units.append(('D%d' % cmap[k], k, gi, yb_of.get(cmap[k], 0.0)))
        cur = kombi + 330.0
    sema_w0 = cur + 120.0
    nsh = len(HAV['sonuc']['saftlar']) if HAV else 0
    sema_w = sema_w0 + (160.0 + 330.0 * nsh if nsh else 0.0)
    ybt = sum(u[3] for u in units)
    P = dict(floors=[(k, '%s %s' % (G['FNAME'][k], G['KOT'][k])) for k in FL], roof_name='ÇATI +9,00', sema_w=sema_w,
             supply=dict(depo=G['DEPO'], V=G['PRM']['depo_V'], vnote='9 BAĞIMSIZ BÖLÜM ≤ 10 → 3 m³ (ÇATIDA, HİDROFORSUZ)' if G['DEPO'] == 'cati' else '9 BAĞIMSIZ BÖLÜM → 3 m³ (BODRUM, HİDROFOR GRUBU)',
                         ybt=ybt, tasma='TAŞMA/BOŞALTMA → ÇATI OLUĞU (HAVA BOŞLUKLU)', hidrofor=None, units=units),
             groups=groups,
             yagmur=dict(names=['YB%d' % (i + 1) for i in range(len(G['YBP']))], P=G['ROOF_A'], dn=100, foot={},
                         tasma_to='YB1', notes=[]))
    # gsheet kolon x'lerini şema başlangıcına göre (dx) bekler
    for g in P['groups']:
        for key in ('x', 'pkx', 'mkx', 'kombi'):
            pass
    P['adk'] = {cmap['Z']: [n for n, r in G['RISERS'].items() if cmap['Z'] in r['digits']] for cmap in cols}
    yf, ytk = sihhi_sema4(SX0, OY, P)
    if HAV:
        havalandirma_sema(SX0 + sema_w0 + 60.0, yf, FL, HAV)
    # ---- rögar şeması (kolon diplerinin bağlandığı rögarlar, yatay R1-R2-...-PB)
    ROG = G['ROG']
    yr = ytk - 110
    names = [n for n in ROG if n != 'PB'] + ['PB']
    xr = {n: SX0 + 300 + i * 520 for i, n in enumerate(names)}
    T((SX0 + 300, yr + 140), 'RÖGAR ŞEMASI (BİNA DIŞI, DOĞU CEPHESİ) - KOLON DİPLERİ ZEMİN KOTUNDAN AYRI AYRI', 12, YZ, 'L')
    acc = 0
    for i, n in enumerate(names):
        x = xr[n]
        mtyblk.insert('PVC ROGAR', (x, yr), 0, 1.0) if n != 'PB' else cad.ROGAR_PLAN((x, yr), 28, 'MTY-ROGAR')
        T((x - 20, yr - 55), n, 14, 'MTY-ROGAR', 'L')
        ks = ROG[n]['kols']
        for j, kn in enumerate(ks):
            xk = x - 60 + 40 * j
            GS.wl([(xk, yr + 95), (xk, yr + 20)], PS)
            mtyblk.insert('MTY-KOLON NO PIS SU', (xk, yr + 110), 0, 0.6, attrs={'K': kn})
        acc += sum(sum(G['STATS_SB'][kn].values()) for kn in ks)
        if i + 1 < len(names):
            GS.wl([(x + 30, yr), (xr[names[i + 1]] - 30, yr)], PS)
            gp.cap_pis(((x + xr[names[i + 1]]) / 2, yr + 6), 0, '%d SB' % acc, 'Ø%d' % max(150, gp.dn_sb(acc, True)), 6.5)
            T(((x + xr[names[i + 1]]) / 2, yr - 22), '%1', 7, PSC, 'C')
    GS.wl([(xr['PB'] + 30, yr), (xr['PB'] + 160, yr)], PS)
    cad.ARROW((xr['PB'] + 170, yr), 0, PS, 12)
    T((xr['PB'] + 40, yr - 30), 'SASKİ ATIKSU KANALINA', 8, PSC, 'L')
    for c in KOLS:                    # şemadaki kolon diplerine hangi rögara gittiği
        rn = [n for n in ROG if c['name'] in ROG[n]['kols']]
        for g in P['groups']:
            for kn, xx, dn, _ in g['kolons']:
                if kn == c['name'] and rn:
                    T((SX0 + xx + 10, ytk + 8), '→ %s' % rn[0], 8, PSC, 'L')
    # ---- yağmur şeması + hesabı
    yx = SX0 + sema_w + 80
    h, yw = GS.yagmur_sema(yx, OY, P)
    # ---- SIHHİ DETAYLAR (R3: saf geometri tablolar; MTY detay bloğu kullanılmaz)
    dx0 = yx + yw + 140
    i0 = len(cad.R)
    detaylar(dx0, OY + 150)
    dbb = kayit_kutusu(cad.R[i0:])                 # R4: çerçeve içerikten (sabit genişlik yok)
    G['DETAY_KUTU'] = dbb
    G['DETAY'] = None
    # ---- antet / notlar / lejant (en solda)
    ax = -3900.0
    GS.antet(ax, FH - 100.0, ANTET)
    GS.notlar(ax + 1800, FH - 100.0, NOTES)
    GS.lejant(ax, FH - 1100.0)
    # ---- pafta çerçeveleri
    FR = [((ax - 60, 0, -40.0, FH), 'ANTET, NOTLAR VE LEJANT', 'ÖLÇEKSİZ')]
    for key, ttl in (('YER', 'YERLEŞİM PLANI'), ('T', 'TEMEL PLANI'), ('Z', 'ZEMİN KAT SIHHİ TESİSAT PLANI'),
                     ('1', '1. KAT SIHHİ TESİSAT PLANI'), ('2', '2. KAT SIHHİ TESİSAT PLANI')):
        x0 = G['SLOTS'][key] * SLOT
        FR.append(((x0, 0, x0 + SLOT, FH), ttl, '1/250' if key == 'YER' else '1/50'))
    FR.append(((SX0 - 60, 0, SX0 + sema_w + 40, FH), 'SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI + RÖGAR ŞEMASI + WC/BANYO HAVALANDIRMA KOLONLARI', 'ÖLÇEKSİZ'))
    FR.append(((SX0 + sema_w + 40, 0, yx + yw + 60, FH), 'YAĞMUR SUYU ŞEMASI VE HESABI', 'ÖLÇEKSİZ'))
    FR.append(((yx + yw + 60, 0, max(dbb[2], dx0) + 120, FH), 'SIHHİ DETAYLAR', 'ÖLÇEKSİZ'))
    for (a, b, c_, d), t, o in FR:
        GS.frame(a, b, c_, d, t, o)
    sk = sayac_kesisme(SX0 - 60, SX0 + sema_w + 40)
    return dict(sayac_hat_kesisme=len(sk), sayac_hat_kesisme_ornek=sk[:10], sayac_hat_parca=len(SAYAC_HAT), sema_w=sema_w, groups=[(g['units'], [k[0] for k in g['kolons']]) for g in groups], units=units, ybt=ybt,
                yagmur=dict(D=h['D'], f=h['f'], P=h['P']), frames=[f[1] for f in FR])


ANTET = dict(proje="METRA MİMARLIK YAPI SAN. VE TİC. LTD. ŞTİ.'NE AİT 9 BAĞIMSIZ BÖLÜMLÜ MESKEN",
             konu='SIHHİ TESİSAT PROJESİ  -  DENEME R4 (OTOMATİK ÜRETİM, KONTROL EDİLMEDİ)',
             rows=[('YAPININ ÖZELLİKLERİ', ''), ('YAPI SAHİBİ', 'METRA MİMARLIK YAPI SAN. VE TİC. LTD. ŞTİ.'),
                   ('YAPI CİNSİ / SINIFI', 'BETONARME / 3A'), ('KAT ADEDİ', 'ZEMİN + 2 KAT (3)'), ('BAĞIMSIZ BÖLÜM', '9 DAİRE'),
                   ('SU TEMİNİ', 'ŞEBEKE (SASKİ) + 3,00 m³ ÇATI DEPOSU'), ('ARSANIN ÖZELLİKLERİ', ''),
                   ('İLİ / İLÇESİ', 'SAKARYA / ADAPAZARI'), ('MAHALLE', 'TEKELER'), ('PAFTA / ADA / PARSEL', 'G24B23B2B / 4739 / 4')])
NOTES = [
    'BU PAFTA SETİ OTOMATİK DENEMEDİR (MİMARİDEN OTOMATİK TANIMA + YERLEŞİM); TASARIM DEĞERLERİ KONTROL EDİLMEDEN UYGULAMAYA VERİLMEZ.',
    'Temiz su tesisatı PPRC PN20 borularla yapılacak, sıcak su boruları izolasyonlu döşenecektir.',
    'Şebeke suyu bina girişindeki ana sayaçtan DBK kolonu ile çatıdaki 3,00 m³ kullanma suyu deposuna verilecektir.',
    'Çatı deposundan inen ADK kolonları merdiven holünde (ortak alan) daire kapılarının yanındadır; her katta kolondan daire kapısına kısa yatay hat, DAİRE KAPISINDA (kat sahanlığı) vana + daire sayacı + çek valf. Zeminde toplu sayaç grubu yoktur (kolon şeması da aynı).',
    'Bina besleme ve dağıtım hatları daire içinden geçirilmeyecek; ana hatlar ortak alanda (merdiven holü) gezerek dairelere girecektir.',
    'Daire içinde sıcak ve soğuk su boruları yan yana paralel döşenecektir; her dairede çamaşır ve bulaşık makinesi bağlantısı (mimaride gösterilmese de) yapılacaktır.',
    'Balkon süzgeçleri pis su hattına bağlanmayacak; ayrı Ø50 süzgeç hattı ile en yakın yağmur iniş borusuna bağlanacaktır.',
    'Betonarme kolon/perde, asansör boşluğu ve enerji odası içinden hiçbir tesisat hattı geçirilmeyecektir.',
    'Sıcak kullanma suyu her dairede duvar tipi hermetik yoğuşmalı kombiden sağlanacaktır.',
    'Pis su tesisatı TS EN 1451 PVC; bina içi yatay hatlar en az %2, rögarlar arası %1 eğimle döşenecektir.',
    'Mutfak ve banyo/WC giderleri birleştirilmeyecek; her ıslak hacim kendi kolonuna bağlanacaktır.',
    'Pis su kolonları zemin katta sonlanacak; kolon diplerinden zemin kotunda ayrı ayrı bina dışındaki rögarlara bağlanacaktır.',
    'Pis su kolonları çatıdan en az 50 cm yukarı çıkarılacak, uçlarına havalık şapkası takılacaktır.',
    'Hiçbir boru betonarme kolon/perde içinden geçirilmeyecek; döşeme ve duvar geçişleri kılıflı yapılacaktır.',
    'Yağmur suları pis su hattına bağlanmayacak; iniş boruları zemin kotunda bırakılacaktır (yağmur suyu altyapısı kapsam dışı).',
    'Tüm imalat TS 1258, TS EN 806, TS EN 12056 standartlarına uygun yapılacaktır.',
]


NOTES = NOTES[:5] + [
    'Daire içinde sıcak su kombiden tek hat olarak sıcak su alan armatürleri sırayla dolaşır; soğuk su bu hatta 10 cm paralel '
    'yürür. Soğuk alan armatürler (klozet, ÇM, BM) soğuk hatta soğuk taraftan bağlanır. Borular birbirini kesmez, atlatma yapılmaz.',
    'Koridorlarda temiz su hatları koridor ortasından, ıslak hacimlerde mahal ortasından (şap içi) geçirilecektir; yatak odası '
    'içinden geçen besleme olursa duvar dibinden götürülecektir.',
    'Pis su bağlantıları dallı (balık sırtı) sistemle: her armatür ana hatta 45° tekil branşmanla, ana hat kolona en kısa yoldan 45° dirseklerle.',
    'Pis su kolonları mekanik havalandırma şaftı içinden geçirilmeyecektir (tesisat ve havalandırma şaftları ayrı).',
    'Her ıslak hacimde (banyo, WC, mutfak, duş) 1 adet Ø50 yer süzgeci bulunacaktır.',
    'Penceresiz WC/banyolarda 80 m³/h - 50 Pa - Ø150 aspiratör; şaftlar çatıda çatı tipi fanla sonlanır (kat planı + kolon şeması).',
] + NOTES[5:]


def havalandirma_sema(x0, yf, FL, HAV):
    """kolon şemasının sağında: her şaft için düşey kanal, katlarda aspiratör branşmanı, çatıda çatı tipi fan"""
    HV, HVY = 'ROTAS-HAVALANDIRMA', 'ROTAS-HAVALANDIRMA-YAZI'
    r = HAV['sonuc']
    T((x0, yf[-1] + 250), 'WC / BANYO MEKANİK HAVALANDIRMA KOLONLARI (ŞAFT → ÇATI TİPİ FAN)', 14, HVY, 'L')
    T((x0, yf[-1] + 228), 'Aspiratör 80 m³/h - 50 Pa - Ø150 · galvaniz şaft kanalı · geri akış klapeli bağlantı', 8, HVY, 'L')
    kat_i = {k: i for i, k in enumerate(FL)}
    for j, s in enumerate(r['saftlar']):
        x = x0 + 250 + j * 330
        ks = sorted({a['kat'] for a in s['asps']}, key=lambda k: kat_i[k])
        ylo = yf[kat_i[ks[0]]] + 150
        ytop = yf[-1] + 60
        PL([(x - 7, ylo), (x - 7, ytop)], HV, w=1.5)
        PL([(x + 7, ylo), (x + 7, ytop)], HV, w=1.5)
        L((x - 7, ylo), (x + 7, ylo), HV)
        L((x - 25, yf[-1]), (x + 25, yf[-1]), HV)                         # çatı döşemesi geçişi
        mtyblk.insert('ROTAS-CATI-FANI', (x, ytop), 0, 1.2)
        T((x, ytop + 104), s['ad'], 14, HVY, 'C')
        T((x, ytop + 88), 'ÇATI TİPİ FAN %s' % s['fan']['ad'], 7, HVY, 'C')
        T((x, ytop + 77), '%d m³/h - %.0f Pa' % (s['Q'], s['p_fan']), 7, HVY, 'C')
        for b in s['bol']:
            i = [n for n in range(len(FL))][min(len(FL) - 1, b['ki'])]
            T((x + 14, yf[i] + 230), '%dx%d / %d m³/h' % (s['w'], s['h'], b['q']), 6, HVY, 'L', 90)
        say = {}
        for a in s['asps']:
            i = kat_i[a['kat']]
            yb = yf[i] + 215
            for m in a['mahaller']:
                n_ = say.get(i, 0); say[i] = n_ + 1
                yy = yb - 48 * n_
                PL([(x - 7, yy), (x - 95, yy)], HV, w=3.0)
                mtyblk.insert('ROTAS-ASPIRATOR', (x - 105, yy), 0, 1.0)
                T((x - 118, yy + 4), '%s %s' % (m['daire'], m['ad']), 6, HVY, 'R')
                T((x - 118, yy - 6), '%d m³/h - Ø150' % a['q'], 6, HVY, 'R')


def detaylar(x, y):
    """SIHHİ DETAYLAR: SB / YB değer tabloları, pis su ve temiz su çap tabloları, yer süzgeci ve havalık detayı (saf geometri)"""
    from gp import SB, YB, YBS
    lay = YZ
    def tablo(x0, y0, baslik, hdr, rows, cw):
        rh = 22.0
        T((x0, y0 + 16), baslik, 13, lay, 'L')
        allr = [hdr] + rows
        W = sum(cw)
        for i, r_ in enumerate(allr):
            yy = y0 - i * rh
            L((x0, yy), (x0 + W, yy), lay)
            cx = x0
            for jj, c in enumerate(r_):
                T((cx + 6, yy - rh / 2 - 4), str(c), 9, lay, 'L')
                cx += cw[jj]
        yb = y0 - len(allr) * rh
        L((x0, yb), (x0 + W, yb), lay)
        cx = x0
        for c in (0,) + tuple(cw):
            cx += c
            L((cx, y0), (cx, yb), lay)
        return W, y0 - yb
    ad = dict(WC='Klozet', LV='Lavabo', DUS='Duş', EV='Eviye', CM='Çamaşır makinesi', BM='Bulaşık makinesi', YS='Yer süzgeci Ø50')
    top = y + 2200
    w1, h1 = tablo(x, top, 'ARMATÜR YÜK DEĞERLERİ (TS EN 12056 SB / TS 1258 YB)', ('ARMATÜR', 'SB', 'YB SOĞUK', 'YB SICAK'),
                   [(ad[k], fmt(SB[k]), fmt(YB.get(k, 0)), fmt(YBS.get(k, 0))) for k in ('WC', 'LV', 'DUS', 'EV', 'CM', 'BM', 'YS')],
                   (300, 90, 120, 120))
    w2, h2 = tablo(x, top - h1 - 90, 'PİS SU BORU ÇAPI (SB)', ('ÇAP', 'EN ÇOK SB', 'NOT'),
                   [('Ø50', '10', 'klozetsiz'), ('Ø70', '30', 'klozetsiz'), ('Ø100', '160', 'klozetli hat en az Ø100'),
                    ('Ø125', '300', ''), ('Ø150', '600', 'rögar arası')], (120, 140, 370))
    w3, h3 = tablo(x, top - h1 - h2 - 180, 'TEMİZ SU BORU ÇAPI (YB, PPRC)', ('ÇAP', 'EN ÇOK YB'),
                   [('Ø20', '2.25'), ('Ø25', '7.84'), ('Ø32', '19.36'), ('Ø40', '46.24'), ('Ø50', '108.4'), ('Ø63', '256')],
                   (120, 160))
    # yer süzgeci detayı (kesit) - saf geometri
    yy = top - h1 - h2 - h3 - 330
    T((x, yy + 40), 'YER SÜZGECİ DETAYI (KESİT)', 13, lay, 'L')
    PL([(x, yy), (x + 300, yy)], lay, w=1.5)                  # şap üstü
    PL([(x + 110, yy), (x + 110, yy - 60), (x + 190, yy - 60), (x + 190, yy)], lay)
    for i in range(5):
        L((x + 118 + i * 16, yy - 2), (x + 118 + i * 16, yy + 2), lay)
    PL([(x + 150, yy - 60), (x + 150, yy - 120), (x + 260, yy - 175)], lay, w=1.5)
    T((x + 200, yy - 40), 'Ø50 KOKU TUTUCULU YER SÜZGECİ', 8, lay, 'L')
    T((x + 200, yy - 150), 'Ø50 PVC (%2 EĞİM) → PİS SU HATTINA 45° BRANŞMAN', 8, lay, 'L')
    # havalık detayı
    hx = x + 520
    T((hx, yy + 40), 'KOLON HAVALIĞI (ÇATI)', 13, lay, 'L')
    PL([(hx, yy - 120), (hx + 260, yy - 120)], lay, w=1.5)
    PL([(hx + 120, yy - 200), (hx + 120, yy - 30)], lay, w=1.5); PL([(hx + 140, yy - 200), (hx + 140, yy - 30)], lay, w=1.5)
    PL([(hx + 95, yy - 30), (hx + 130, yy), (hx + 165, yy - 30)], lay)
    T((hx + 180, yy - 80), 'ÇATIDAN EN AZ 50 cm', 8, lay, 'L')
    return max(w1, w2, w3, 900.0), 2300.0


SAYAC_HAT = []


def sayac_kesisme(x0, x1):
    """şemadaki sayaç / ADK / çatı dağıtım hatlarının diğer boru çizgileriyle kesişmesi (uçtaki T birleşimi hariç)"""
    from shapely.geometry import LineString, Point
    lays = {gp.CS, gp.CH, gp.PS, gp.PST, gp.YL, 'MTY-PVC', 'ROTAS-HAVALANDIRMA'}
    geo = lambda r: LineString([r[2], r[3]]) if r[0] == 'L' else LineString(list(r[2]) + ([r[2][0]] if r[3] else []))
    sh = set(SAYAC_HAT)
    hat = [(i, geo(cad.R[i])) for i in SAYAC_HAT]
    diger = [(i, geo(r)) for i, r in enumerate(cad.R) if r and r[0] in ('L', 'P') and r[1] in lays and i not in sh
             and len(r[2] if r[0] == 'P' else [r[2], r[3]]) >= 2 and x0 <= (r[2][0][0] if r[0] == 'P' else r[2][0]) <= x1]
    out = []
    for i, a in hat:
        ea = [Point(a.coords[0]), Point(a.coords[-1])]
        for j, b in diger + [(jj, bb) for jj, bb in hat if jj > i]:
            if a.distance(b) > 0.2:
                continue
            it = a.intersection(b)
            for g in (it.geoms if hasattr(it, 'geoms') else [it]):
                if g.is_empty:
                    continue
                p = g if g.geom_type == 'Point' else g.centroid
                eb = [Point(b.coords[0]), Point(b.coords[-1])]
                if min(p.distance(e) for e in ea + eb) < 0.6:
                    continue                       # T / dirsek birleşimi
                out.append((cad.R[j][1], [round(p.x), round(p.y)]))
    return out


def kayit_kutusu(recs):
    """cad.R kayıtlarının (L / P / C / S / T / W) sınır kutusu"""
    import tcheck
    xs, ys = [], []
    for r in recs:
        if not r:
            continue
        if r[0] == 'L':
            xs += [r[2][0], r[3][0]]; ys += [r[2][1], r[3][1]]
        elif r[0] in ('P', 'W'):
            xs += [p[0] for p in r[2]]; ys += [p[1] for p in r[2]]
        elif r[0] == 'C':
            xs += [r[2][0] - r[3], r[2][0] + r[3]]; ys += [r[2][1] - r[3], r[2][1] + r[3]]
        elif r[0] == 'S':
            for q in r[2:5]:
                xs.append(q[0]); ys.append(q[1])
        elif r[0] == 'T' and str(r[3]).strip():
            b = tcheck.tbox(r).bounds
            xs += [b[0], b[2]]; ys += [b[1], b[3]]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)


# ================================================================== R4 kolon şeması (gsheet.sihhi_sema kopyası, besleme kısmı değişti)
def sihhi_sema4(ox, oy, P):
    """Çatı deposu kurgusu: depo → (çatı üstü dağıtım hattı, kolon havalıklarının ÜSTÜNDEN) → her daire konumu için ADK inişi →
    her katta T → küresel vana + DAİRE SAYACI + çek valf + giriş vanası (daire kapısında, planla aynı) → daire.
    Zeminde toplu sayaç grubu YOK. İniş hatları kendi daire bloğunun solunda; hiçbir sayaç hattı başka hattı kesmez."""
    from cad import VANA, CEKVALF, SAMANDIRALI_VANA, HAVALIK_SAPKA
    fx = GS
    fl = P['floors']
    nf = len(fl)
    FHs = 330.0
    yf = [oy + 520 + i * FHs for i in range(nf + 1)]
    width = P['sema_w']
    T((ox + width / 2, yf[-1] + 400), 'SIHHİ TESİSAT AÇILIMLI KOLON ŞEMASI', 28, YZ, 'C')
    T((ox + width / 2, yf[-1] + 370), '(TEMİZ SU: TS 1258 YÜK BİRİMİ (YB), PPRC PN20 - PİS SU: SU BİRİMİ (SB), PVC - ÖLÇEKSİZ)', 10, YZ, 'C')
    for i in range(nf + 1):
        GS.wl([(ox + 40, yf[i]), (ox + width - 60, yf[i])], 'MTY-SEMA')
        nm = fl[i][1] if i < nf else P['roof_name']
        T((ox + width - 30, yf[i] + 20), nm, 15, GS.RED, 'L', 90)
    xs = lambda dx: ox + dx
    sup = P['supply']
    iz = [k for k, _ in fl].index('Z')
    # -------- şebeke + ANA (SASKİ) sayaç: bina girişi (planla aynı, tek sayaç) -> DBK -> depo
    ysb = yf[iz] - 120
    xd = xs(110)
    GS.wl([(xs(30), ysb), (xd, ysb)], CS)
    VANA((xs(40), ysb), 0.7); GS.PISLIK_TUTUCU((xs(55), ysb), 0.7); mtyblk.insert('MTY-SU SAYACI', (xs(72), ysb), 0, 0.8)
    CEKVALF((xs(90), ysb), 0.6)
    T((xs(30), ysb - 22), 'ŞEBEKEDEN (SASKİ) Ø32 - ANA SAYAÇ (BİNA GİRİŞİ)', 8, GS.TSC, 'L')
    DW, DH = 200, 120
    dx0, dy0 = xs(170), yf[-1] + 40
    RECT(dx0, dy0, dx0 + DW, dy0 + DH, 'RAST-TEM-SU DEPOSU')
    T((dx0 + 100, dy0 + 82), 'KULLANMA SUYU DEPOSU', 9, YZ, 'C')
    T((dx0 + 100, dy0 + 66), 'V = %.2f m³ (ŞAMANDIRALI)' % sup['V'], 8, YZ, 'C')
    T((dx0 + 100, dy0 + 52), sup['vnote'], 7, YZ, 'C')
    L((dx0 + 60, dy0 + DH), (dx0 + 60, dy0 + DH + 22), CS); HAVALIK_SAPKA((dx0 + 60, dy0 + DH + 22), 0.8, CS)
    T((dx0 - 6, dy0 + DH + 12), 'HAVALIK (SİNEKLİKLİ)', 6.5, YZ, 'R')
    L((dx0 + 185, dy0 + 10), (dx0 + 185, dy0 + 100), YZ); T((dx0 + 180, dy0 + 20), 'SEVİYE GÖST.', 6, YZ, 'L', 90)
    GS.wl([(xd, ysb), (xd, dy0 + 100), (dx0 + 30, dy0 + 100)], CS); SAMANDIRALI_VANA((dx0 + 36, dy0 + 100), 0.9)
    cap_temiz((xd, (ysb + dy0) / 2 + 40), 90, so='DBK %s YB' % fmt(sup['ybt']), socp='Ø32', k=7)
    xt = dx0 + DW + 12
    GS.wl([(dx0 + DW, dy0 + 6), (xt, dy0 + 6), (xt, dy0 + 105), (dx0 + DW, dy0 + 105)], CS)
    VANA((xt, dy0 + 30), 0.7, 90)
    yt = dy0 + DH + 18
    GS.wl([(xt, dy0 + 105), (xt, yt), (dx0 + 150, yt)], CS)
    GS.wl([(dx0 + 150, yt + 30), (dx0 + 150, dy0 + DH + 4)], GS.YL)
    T((dx0 + 145, yt + 50), 'TAŞMA/BOŞALTMA → ÇATI OLUĞU', 6.5, GS.YC, 'R')
    T((dx0 + 145, yt + 40), '(HAVA BOŞLUKLU) Ø40 / Ø32', 6, GS.TSC, 'R')
    # -------- depo çıkışı (üstten) -> çatı dağıtım hattı (kolon havalıklarının üstünde) -> ADK inişleri
    yh = yf[-1] + 255
    xo = dx0 + 20
    groups = P['groups']
    gxs = [xs(G['x']) + 40 for G in groups]
    SAYAC_HAT.clear()
    _i = len(cad.R); GS.wl([(xo, dy0 + DH), (xo, yh), (gxs[-1], yh)], CS); SAYAC_HAT.extend(range(_i, len(cad.R)))
    VANA((xo, dy0 + DH + 35), 0.8, 90)
    T((xo + 10, yh - 16), 'ÇATI DAĞITIM HATTI → ADK', 7, GS.TSC, 'L')
    cap_temiz(((xo + gxs[0]) / 2, yh), 0, so='%s YB' % fmt(sup['ybt']), socp='Ø%d' % max(32, dn_temiz(sup['ybt'])), k=6.5)
    units = sup['units']
    ytk = yf[0] - 150.5
    for gi, G in enumerate(groups):
        gx = xs(G['x'])
        xa = gx + 40
        flo = [i for i, (fk, _) in enumerate(fl) if G['units'].get(fk)]
        ylo = yf[min(flo)] + 130
        _i = len(cad.R); GS.wl([(xa, yh), (xa, ylo)], CS); SAYAC_HAT.extend(range(_i, len(cad.R)))   # ADK inişi
        z = int(G['units'].get('Z', ('D0',))[0][1:])
        adk = (P.get('adk') or {}).get(z) or ['ADK']
        T((xa - 8, yf[-1] + 40), '%s (%s)' % (adk[0], '-'.join(G['units'][fk][0] for fk, _ in fl if G['units'].get(fk))), 7, GS.TSC, 'L', 90)
        ybg = sum(u[3] for u in units if u[2] == gi)
        cap_temiz((xa, yf[-1] - 80), 90, so='%s YB' % fmt(ybg), socp='Ø%d' % max(25, dn_temiz(ybg)), k=6.5)
        for i, (fk, fname) in enumerate(fl):
            y = yf[i]
            u = G['units'].get(fk)
            if not u:
                continue
            nm, kind = u
            ylev = y + 130
            # kat T'si -> vana -> SAYAÇ -> çek valf -> giriş vanası (daire kapısı)
            _i = len(cad.R); GS.wl([(xa, ylev), (gx + 120, ylev)], CS); SAYAC_HAT.extend(range(_i, len(cad.R)))
            VANA((xa + 12, ylev), 0.5); mtyblk.insert('MTY-SU SAYACI', (xa + 32, ylev), 0, 0.6)
            CEKVALF((xa + 50, ylev), 0.5); VANA((gx + 100, ylev), 0.6)
            T((xa + 4, ylev + 16), '%s SAYAÇ (KAPIDA)' % nm, 6.5, GS.VN, 'L')
            if kind == 'daire':
                rows = [(G['pkx'], G['bkeys'])] + [(e['kx'], e['keys']) for e in G.get('extra', [])] + [(G['mkx'], G['mkeys'])]
                allx, allk = [], []
                for kx_, keys in rows:
                    xr = GS.fixture_row(xs(kx_) + 120, y, keys, xs(kx_))
                    allx += xr; allk += keys
                kx = xs(G['kombi'])
                GS.wl([(gx + 120, ylev), (kx, ylev)], CS)
                mtyblk.insert('KOMBI1 KOLON', (kx, y), 0, 1.0, attrs={'SO': fmt(2.0), 'SOCP': 'Ø20', 'SC': fmt(2.0), 'SCCP': 'Ø20'})
                T((kx + 25, y + 215), 'H. KOMBİ 24 kW', 8, CD, 'L')
                hx = [x for x, k in zip(allx, allk) if GS.YBC[k][1]]
                GS.wl([(kx - 15, y + 135), (min(hx) - 15, y + 135)], gp.CH)
                pts = sorted(zip(allx, allk))
                GS.supply_labels(gx + 120, kx, ylev, [p[0] for p in pts], [p[1] for p in pts])
                C((kx + 110, y + 175), 34, 'MTY-PISSU-KOLONNO')
                T((kx + 110, y + 175), nm, 18, 'MTY-PISSU-KOLONNO', 'MC')
        for nm, xk, dk, sbf in G['kolons']:
            x = xs(xk)
            top = yf[-1] + 110
            ybot = ytk + 20
            GS.dline((x, ybot), (x, top), 5)
            mtyblk.insert('MTY-KOLON HAVALIK SAPKASI', (x, top), 0, 1.6)
            T((x + 12, yf[-1] + 40), 'HAVALIK Ø%d (ÇATIDAN 50 cm)' % dk, 6.5, PSC, 'L', 90)
            mtyblk.insert('MTY-PIS SU KOLON NO', (x, top + 70), 0, 1.0, attrs={'K': nm})
            for i in range(nf):
                s = sbf(i)
                if s:
                    T((x - 12, yf[i] + 40), 'Ø%d / %d SB' % (dk, s), 8, PSC, 'L', 90)
            mtyblk.insert('MTY-TEMIZLEME KAPAGI KOLON', (x, ybot + 55), 0, 0.8, attrs={'TK': 'T.K.'})
            mtyblk.insert('PVC DIRSEK', (x, ybot), 0, 1.0)
    return yf, ytk
