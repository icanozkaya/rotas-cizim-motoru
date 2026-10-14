# -*- coding: utf-8 -*-
"""ROTAS sembol kütüphanesi v2 DXF'ini üretir.
    python3 motor/deneme/semboller2/olustur.py [--png KLASOR]
Çıktı: proje/denemeler/semboller2/SEMBOL_KUTUPHANESI_V2.dxf (AC1032)
  Paftalar (soldan sağa): SIHHİ | DEPO-HİDROFOR | ISITMA | YANGIN | HAVALANDIRMA | KOLON ŞEMASI ŞABLONLARI |
  ETİKET + OTOMATİK LEJANT DENEMESİ
PNG yalnız kontrol içindir; depoya konmaz."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ezdxf                                          # noqa: E402
from ezdxf.enums import TextEntityAlignment as TA     # noqa: E402
import sembol2 as S                                   # noqa: E402
from cekirdek import SEMBOL, GRUP                     # noqa: E402

DEPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
CIKTI = os.path.join(DEPO, 'proje', 'denemeler', 'semboller2')
PAFTA = 'ROTAS-PAFTA'
BANT = 'ROTAS-KAT-BANDI'
ORNEK_NO = {'SB-KOLON-NO': 'P1', 'SB-KOLON-PIS': 'P1', 'SB-KOLON-TEMIZ': 'TS1', 'SB-ROGAR': 'R1', 'KS-ROGAR': 'R1', 'SB-KOLON-YAGMUR': 'YB1'}
ORNEK_CAP = {'SB': 'Ø20', 'IS': 'DN25', 'YG': 'DN50', 'DH': 'DN40'}
GRUP_BORU = {'SB': 'ROTAS-SIHHI-SOGUK-SU', 'DH': 'ROTAS-SIHHI-SOGUK-SU', 'IS': 'ROTAS-ISITMA-GIDIS',
             'YG': 'ROTAS-YANGIN-DOLAP-BORU', 'HV': 'ROTAS-HAVALANDIRMA-EGZOZ'}


def _m(msp, s, p, h, kat=S.LEJ_YAZ, al=TA.MIDDLE_LEFT, w=0.85):
    return S._metin(msp, s, p, h, kat, al, w)


def grup_paftasi(msp, g, x0, y0):
    """Bir grubun tüm sembolleri: NO | BLOK ADI | 1/50 GERÇEK BOY (boru + numara örneği) | BÜYÜTÜLMÜŞ | AÇIKLAMA"""
    ads = [a for a in SEMBOL if SEMBOL[a]['grup'] == g]
    kaps = {a: SEMBOL[a]['kap'] for a in ads}
    W_NO, W_AD, W_G, W_B, W_A = 40.0, 260.0, max(200.0, max(k[2] - k[0] for k in kaps.values()) + 120), 200.0, 520.0
    W = W_NO + W_AD + W_G + W_B + W_A
    y = y0
    _m(msp, 'ROTAŞ SEMBOL KÜTÜPHANESİ v2 — ' + GRUP[g][0], (x0, y + 40), 22, S.LEJ_BAS, TA.MIDDLE_LEFT, 0.9)
    _m(msp, 'Saf geometri. Blok içi katman 0 / BYLAYER: renk, sembolün konduğu ROTAS- katmanından gelir. '
            'Vana L=20 cm (1/50: 4 mm), numara yazısı 10 cm (1/50: 2 mm).', (x0, y + 14), 9)
    _S = S._kutu
    _S(msp, x0, y - 26, x0 + W, y)
    xs = [x0, x0 + W_NO, x0 + W_NO + W_AD, x0 + W_NO + W_AD + W_G, x0 + W_NO + W_AD + W_G + W_B, x0 + W]
    for i, s in enumerate(('NO', 'BLOK ADI', '1/50 GERÇEK BOY (ÖRNEK BORU + NUMARA)', 'BÜYÜTÜLMÜŞ GÖRÜNÜŞ', 'AÇIKLAMA')):
        _m(msp, s, ((xs[i] + xs[i + 1]) / 2, y - 13), 9, S.LEJ_YAZ, TA.MIDDLE_CENTER)
    y -= 26
    koyulan = []
    for i, a in enumerate(ads):
        k = kaps[a]
        w, h = k[2] - k[0], k[3] - k[1]
        rh = max(70.0, h + 50)
        _S(msp, x0, y - rh, x0 + W, y)
        for xx in xs[1:-1]:
            msp.add_line((xx, y), (xx, y - rh), dxfattribs={'layer': S.LEJ_CER})
        cy = y - rh / 2
        _m(msp, str(i + 1), ((xs[0] + xs[1]) / 2, cy), 10, S.LEJ_YAZ, TA.MIDDLE_CENTER)
        _m(msp, a, (xs[1] + 6, cy), 8.5, S.LEJ_YAZ, TA.MIDDLE_LEFT, 0.8)
        # gerçek boy: sembol ortalı (kapsam merkezi hücre merkezine)
        gx = (xs[2] + xs[3]) / 2 - (k[0] + k[2]) / 2
        gy = cy - (k[1] + k[3]) / 2
        kisa = a[len('ROTAS-'):]
        no = ORNEK_NO.get(kisa) or ((SEMBOL[a]['onek'] + '-01') if SEMBOL[a]['onek'] else None)
        cap = ORNEK_CAP.get(g) if SEMBOL[a]['kesme'] else None
        boru = GRUP_BORU.get(g, 'ROTAS-SIHHI-SOGUK-SU')
        kat = GRUP[g][1]
        if SEMBOL[a]['kesme']:
            x_a, x_b = xs[2] + 12, xs[3] - 12
            if SEMBOL[a]['uc']:
                x_b = gx + 40
            t = (gx - x_a) / (x_b - x_a)
            ins = S.hat(msp, (x_a, gy), (x_b, gy), [(t, a, no, cap)], katman=boru, sembol_katman=kat)[0]
        else:
            ins = S.koy(msp, a, gx, gy, no=no, katman=kat)
        koyulan.append(ins)
        # büyütülmüş
        S.sembol_hucre(msp, a, (xs[3] + xs[4]) / 2, cy, W_B, rh, katman=kat, buyut_max=4.0)
        ac = SEMBOL[a]['aciklama'] + (' (*)' if SEMBOL[a]['celiski'] else '')
        _m(msp, ac, (xs[4] + 8, cy + (6 if SEMBOL[a]['baglanti'] else 0)), 9, S.LEJ_YAZ, TA.MIDDLE_LEFT)
        if SEMBOL[a]['baglanti']:
            _m(msp, 'bağlantı: ' + ', '.join(SEMBOL[a]['baglanti']), (xs[4] + 8, cy - 9), 7, S.LEJ_YAZ, TA.MIDDLE_LEFT)
        y -= rh
    # boru çizgileri
    borular = [b for b in S.BORU if b[0] == g]
    for _, ac, kat, _, _ in borular:
        _S(msp, x0, y - 30, x0 + W, y)
        msp.add_line((xs[2] + 12, y - 15), (xs[3] - 12, y - 15), dxfattribs={'layer': kat})
        _m(msp, kat, (xs[1] + 6, y - 15), 8.5, S.LEJ_YAZ, TA.MIDDLE_LEFT, 0.8)
        _m(msp, ac, (xs[4] + 8, y - 15), 9)
        y -= 30
    notlar = sorted({SEMBOL[a]['celiski'] for a in ads if SEMBOL[a]['celiski']})
    for s in notlar:
        y -= 14
        _m(msp, '(*) ' + s + ' — kullanıcı teyidi bekleniyor.', (x0, y), 8)
    # etiketler: tablo çizgileri ve yazılar engel; numara sembolün hemen yanına
    eng = S.Engel(msp)
    olmayan = S.etiketle(msp, eng, koyulan)
    return W, y0 - y + 60, olmayan


def ks_paftasi(msp, x0, y0):
    """Kolon şeması şablonları: kat bandında yan görünüş, bağlantı noktaları renkli kısa saplamalarla."""
    _m(msp, 'ROTAŞ SEMBOL KÜTÜPHANESİ v2 — KOLON ŞEMASI ŞABLONLARI (YAN GÖRÜNÜŞ)', (x0, y0 + 40), 22,
       S.LEJ_BAS, TA.MIDDLE_LEFT, 0.9)
    _m(msp, 'Orijin = armatür ekseni / döşeme çizgisi. Mavi saplama: soğuk su bağlantısı (SS), kırmızı kesikli: sıcak su (SC), '
            'mor: pis su (PS). Bağlantı noktaları baglanti(ins) ile alınır; boruyu şema çizen modül çizer.', (x0, y0 + 14), 9)
    sira1 = ['ROTAS-KS-LAVABO', 'ROTAS-KS-KLOZET', 'ROTAS-KS-HELA', 'ROTAS-KS-DUS', 'ROTAS-KS-KUVET', 'ROTAS-KS-EVIYE',
             'ROTAS-KS-CAMASIR-MAKINESI', 'ROTAS-KS-BULASIK-MAKINESI', 'ROTAS-KS-YER-SUZGECI', 'ROTAS-KS-KOMBI',
             'ROTAS-KS-TERMOSIFON']
    sira2 = ['ROTAS-KS-SAYAC-GRUBU', 'ROTAS-KS-PVC-CATAL', 'ROTAS-KS-TEMIZLEME-KAPAGI', 'ROTAS-KS-HAVALIK',
             'ROTAS-KS-ROGAR', 'ROTAS-KS-SU-DEPOSU']
    renk = {'soguk': 'ROTAS-SIHHI-SOGUK-SU', 'sicak': 'ROTAS-SIHHI-SICAK-SU', 'pis': 'ROTAS-SIHHI-PIS-SU',
            'gidis': 'ROTAS-ISITMA-GIDIS', 'donus': 'ROTAS-ISITMA-DONUS', 'gaz': 'ROTAS-DOGALGAZ-BORU'}
    kisalt = {'soguk': 'SS', 'sicak': 'SC', 'pis': 'PS', 'gidis': 'G', 'donus': 'D', 'gaz': 'GAZ'}
    ARA = 175.0
    W = ARA * len(sira1) + 60
    # 1. bant
    yb = y0 - 300
    msp.add_lwpolyline([(x0, yb), (x0 + W, yb), (x0 + W, yb + 280), (x0, yb + 280)], close=True, dxfattribs={'layer': BANT})
    _m(msp, 'KAT BANDI (h=280)', (x0 + 8, yb + 268), 9)
    for i, a in enumerate(sira1):
        x = x0 + 60 + ARA * i + ARA / 2 - 30
        ins = S.koy(msp, a, x, yb)
        alttan = a in ('ROTAS-KS-KOMBI', 'ROTAS-KS-TERMOSIFON')
        for j, (k, p) in enumerate(S.baglanti(ins).items()):
            kat = renk.get(k)
            if not kat:
                continue
            if alttan:
                q = (p[0], p[1] - 14 - 10 * (j % 2))
                msp.add_line(p, q, dxfattribs={'layer': kat})
                _m(msp, kisalt[k], (q[0], q[1] - 2), 5, kat, TA.TOP_CENTER)
            elif k == 'pis':
                q = (p[0], min(p[1], yb) - 25)
                msp.add_line(p, q, dxfattribs={'layer': kat})
                _m(msp, kisalt[k], (q[0] + 3, q[1] + 4), 7, kat, TA.MIDDLE_LEFT)
            else:
                q = (p[0], p[1] + 14)
                msp.add_line(p, q, dxfattribs={'layer': kat})
                _m(msp, kisalt[k], (q[0], q[1] + 3), 6, kat, TA.BOTTOM_CENTER)
        isim = SEMBOL[a]['aciklama'].split(' (')[0]
        _m(msp, isim, (x, yb - 70), 9, S.LEJ_YAZ, TA.MIDDLE_CENTER)
        _m(msp, a, (x, yb - 84), 6.5, S.LEJ_YAZ, TA.MIDDLE_CENTER, 0.75)
    # 2. sıra (bant dışı parçalar)
    y2 = yb - 240
    xs = [x0 + 60, x0 + 290, x0 + 460, x0 + 620, x0 + 780, x0 + 1000]
    for x, a in zip(xs, sira2):
        if a == 'ROTAS-KS-SAYAC-GRUBU':
            ins = S.hat(msp, (x - 30, y2), (x + 150, y2), [(30 / 180.0, a, 'S-01')], katman='ROTAS-SIHHI-SOGUK-SU',
                        sembol_katman='ROTAS-SIHHI-SOGUK-SU')[0]
            cx = x + 60
        elif a in ('ROTAS-KS-PVC-CATAL', 'ROTAS-KS-TEMIZLEME-KAPAGI'):
            ins = S.koy(msp, a, x, y2, katman='ROTAS-SIHHI-PIS-SU')
            b = S.baglanti(ins)
            msp.add_line(b['ust'], (b['ust'][0], b['ust'][1] + 30), dxfattribs={'layer': 'ROTAS-SIHHI-PIS-SU'})
            msp.add_line(b['alt'], (b['alt'][0], b['alt'][1] - 30), dxfattribs={'layer': 'ROTAS-SIHHI-PIS-SU'})
            if 'dal' in b:
                d = b['dal']
                msp.add_line(d, (d[0] + 20, d[1] + 20), dxfattribs={'layer': 'ROTAS-SIHHI-PIS-SU'})
            if a == 'ROTAS-KS-PVC-CATAL':
                ins2 = S.koy(msp, a, x + 90, y2, katman='ROTAS-SIHHI-PIS-SU', ayna=True)
                b = S.baglanti(ins2)
                msp.add_line(b['ust'], (b['ust'][0], b['ust'][1] + 30), dxfattribs={'layer': 'ROTAS-SIHHI-PIS-SU'})
                msp.add_line(b['alt'], (b['alt'][0], b['alt'][1] - 30), dxfattribs={'layer': 'ROTAS-SIHHI-PIS-SU'})
                d = b['dal']
                msp.add_line(d, (d[0] - 20, d[1] + 20), dxfattribs={'layer': 'ROTAS-SIHHI-PIS-SU'})
                _m(msp, 'sağ / sol (ayna=True)', (x + 45, y2 - 80), 7, S.LEJ_YAZ, TA.MIDDLE_CENTER)
                cx = x + 45
            else:
                cx = x
        elif a == 'ROTAS-KS-HAVALIK':
            ins = S.koy(msp, a, x, y2 + 20, katman='ROTAS-SIHHI-PIS-SU')
            msp.add_line((x, y2 + 20), (x, y2 - 50), dxfattribs={'layer': 'ROTAS-SIHHI-PIS-SU'})
            cx = x
        elif a == 'ROTAS-KS-ROGAR':
            ins = S.koy(msp, a, x, y2, no='R1')
            b = S.baglanti(ins)
            msp.add_line(b['giris'], (b['giris'][0] - 50, b['giris'][1]), dxfattribs={'layer': 'ROTAS-SIHHI-PIS-SU'})
            msp.add_line(b['cikis'], (b['cikis'][0] + 50, b['cikis'][1]), dxfattribs={'layer': 'ROTAS-SIHHI-PIS-SU'})
            cx = x
        else:   # depo
            ins = S.koy(msp, a, x, y2 - 60, no='D-01')
            b = S.baglanti(ins)
            msp.add_line(b['giris'], (b['giris'][0] - 30, b['giris'][1]), dxfattribs={'layer': 'ROTAS-SIHHI-SOGUK-SU'})
            msp.add_line(b['cikis'], (b['cikis'][0], b['cikis'][1] - 30), dxfattribs={'layer': 'ROTAS-SIHHI-SOGUK-SU'})
            cx = x + 100
        isim = SEMBOL[a]['aciklama'].split(' (')[0]
        _m(msp, isim, (cx, y2 - 110), 9, S.LEJ_YAZ, TA.MIDDLE_CENTER)
        _m(msp, a, (cx, y2 - 124), 6.5, S.LEJ_YAZ, TA.MIDDLE_CENTER, 0.75)
    eng = S.Engel(msp)
    S.etiketle(msp, eng, [e for e in msp.query('INSERT') if e.dxf.name in ('ROTAS-KS-SAYAC-GRUBU', 'ROTAS-KS-SU-DEPOSU')])
    return W, 300 + 220 + 160


def deneme_paftasi(doc, x0, y0):
    """Etiket yerleştirme denemesi (kazan dairesi geri bildirimi: V-21/V-10, TM-01/M-01 karışıklığı) +
    otomatik lejant. DENEME — örnek değerler."""
    msp = doc.modelspace()
    _m(msp, 'DENEME — ETİKET YERLEŞTİRME (etiket_yer) VE OTOMATİK LEJANT (örnek değerler)', (x0, y0 + 40), 22, S.LEJ_BAS,
       TA.MIDDLE_LEFT, 0.9)
    gid, don = 'ROTAS-ISITMA-GIDIS', 'ROTAS-ISITMA-DONUS'
    SK = 'ROTAS-ISITMA-SEMBOL'
    n = 1
    for j, kx in enumerate((x0 + 100, x0 + 360)):
        k = S.koy(msp, 'IS-KAZAN', kx, y0 - 110, no='K-0%d' % (j + 1), katman=SK)
        b = S.baglanti(k)
        g0, d0 = b['donus'], b['gidis']     # kazan sağ ucu gidiş, sol ucu dönüş olarak kullanıldı
        S.hat(msp, g0, (g0[0], y0 - 560), [(0.30, 'SB-KURESEL-VANA', 'V-%02d' % n), (0.45, 'IS-POMPA', 'P-%02d' % (j + 1)),
                                            (0.60, 'SB-CEKVALF', 'V-%02d' % (n + 1)), (0.75, 'SB-KURESEL-VANA', 'V-%02d' % (n + 2))],
              katman=gid, sembol_katman=SK)
        n += 3
        S.hat(msp, (d0[0], y0 - 560), d0, [(0.35, 'SB-PISLIK-TUTUCU', 'V-%02d' % n), (0.65, 'SB-KURESEL-VANA', 'V-%02d' % (n + 1))],
              katman=don, sembol_katman=SK)
        n += 2
        S.koy(msp, 'IS-MANOMETRE', g0[0], y0 - 140, aci=-90, no='M-%02d' % (j + 1), katman=SK)
        S.koy(msp, 'IS-TERMOMETRE', g0[0], y0 - 175, aci=-90, no='TM-%02d' % (j + 1), katman=SK)
        S.koy(msp, 'IS-PURJOR', g0[0], y0 - 205, aci=-90, no='HP-%02d' % (j + 1), katman=SK)
    # dönüş hattı üzerinde kalorimetre + genleşme tankı bağlantısı (ayrı yatay hat, kesişme yok)
    S.hat(msp, (x0 + 80, y0 - 640), (x0 + 520, y0 - 640), [(0.25, 'IS-KALORIMETRE', 'KM-01'), (0.55, 'IS-BALANS-VANASI', 'V-%02d' % n),
                                                          (0.80, 'IS-RAKORLU-DONUS', 'V-%02d' % (n + 1))], katman=don, sembol_katman=SK)
    S.koy(msp, 'IS-GENLESME-TANKI', x0 + 160, y0 - 640, aci=180, no='GT-01', katman=SK)
    eng = S.Engel(msp)
    olmayan = S.etiketle(msp, eng, [e for e in msp.query('INSERT') if e.dxf.name in SEMBOL
                                    and e.dxf.layer != S.LEJ_SEM and e.dxf.insert[0] >= x0 and e.dxf.insert[1] < y0 + 1])
    return olmayan


def png(doc, yol, kutu, dpi=100, olcek=1.0):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy, LineweightPolicy
    x0, y0, x1, y1 = kutu
    w, h = x1 - x0, y1 - y0
    fig = plt.figure(figsize=(max(3, w / 100 * olcek), max(3, h / 100 * olcek)), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR,
                        lineweight_policy=LineweightPolicy.RELATIVE, min_lineweight=0.1)
    msp = doc.modelspace()
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp)
    fig.set_size_inches(max(3, w / 100 * olcek), max(3, h / 100 * olcek))
    ax.set_position([0, 0, 1, 1])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    fig.savefig(yol, dpi=dpi)
    plt.close(fig)


def main():
    pngdir = None
    if '--png' in sys.argv:
        pngdir = sys.argv[sys.argv.index('--png') + 1]
        os.makedirs(pngdir, exist_ok=True)
    os.makedirs(CIKTI, exist_ok=True)
    doc = ezdxf.new('R2018', setup=True)
    doc.header['$INSUNITS'] = 5   # cm
    S.ekle(doc)
    for k, c in ((PAFTA, 8), (BANT, 8), ('ROTAS-DOGALGAZ-BORU', 2)):
        if k not in doc.layers:
            doc.layers.add(k, color=c)
    msp = doc.modelspace()
    x = 0.0
    kutular = {}
    rapor = []
    for g in ('SB', 'DH', 'IS', 'YG', 'HV'):
        w, h, olm = grup_paftasi(msp, g, x, 0.0)
        msp.add_lwpolyline([(x - 30, 90), (x + w + 30, 90), (x + w + 30, -h - 30), (x - 30, -h - 30)], close=True,
                           dxfattribs={'layer': PAFTA})
        kutular[g] = (x - 30, -h - 30, x + w + 30, 90)
        rapor += [(i.dxf.name, t) for i, t in olm]
        x += w + 120
    w, h = ks_paftasi(msp, x, 0.0)
    msp.add_lwpolyline([(x - 30, 90), (x + w + 30, 90), (x + w + 30, -h - 30), (x - 30, -h - 30)], close=True,
                       dxfattribs={'layer': PAFTA})
    kutular['KS'] = (x - 30, -h - 30, x + w + 30, 90)
    x += w + 120
    olm = deneme_paftasi(doc, x, 0.0)
    rapor += [(i.dxf.name, t) for i, t in olm]
    # otomatik lejant yalnız deneme bölgesindeki kullanımları saymalı: ayrı DXF'te deneme
    kutular['DENEME'] = (x - 30, -700, x + 800, 90)
    msp.add_lwpolyline([(x - 30, 90), (x + 1500, 90), (x + 1500, -700), (x - 30, -700)], close=True, dxfattribs={'layer': PAFTA})
    yol = os.path.join(CIKTI, 'SEMBOL_KUTUPHANESI_V2.dxf')
    doc.saveas(yol)
    print('yazıldı:', yol, '| blok:', len([b for b in doc.blocks if b.name.startswith('ROTAS-')]))
    # otomatik lejant denemesi: deneme paftası ayrı dosyada
    d2 = ezdxf.new('R2018', setup=True)
    d2.header['$INSUNITS'] = 5
    S.ekle(d2)
    deneme_paftasi(d2, 0.0, 0.0)
    say = S.otomatik_lejant(d2)
    yol2 = os.path.join(CIKTI, 'OTOMATIK_LEJANT_DENEME_V2.dxf')
    d2.saveas(yol2)
    print('yazıldı:', yol2, '| sayım:', say)
    if rapor:
        print('YERLEŞTİRİLEMEYEN ETİKET:', rapor)
    if pngdir:
        for k, b in kutular.items():
            png(doc, os.path.join(pngdir, 'pafta_%s.png' % k), b)
        from ezdxf import bbox
        bb = bbox.extents(d2.modelspace(), fast=True)
        png(d2, os.path.join(pngdir, 'otomatik_lejant.png'), (bb.extmin.x - 20, bb.extmin.y - 20, bb.extmax.x + 20, bb.extmax.y + 20))
    return yol


if __name__ == '__main__':
    main()
