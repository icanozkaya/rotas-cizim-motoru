"""C BLOK SU DEPOSU (kullanıcının DEPO.dxf'i) içine işleme — 16.10.2026.

Mimari plan (1/100) koordinatında: kullanma suyu deposu 2 göz + menhol + şamandıralı dolum, hidrofor grubu (pompa
dairesi), drenaj çukuru, ŞEBEKE BAĞLANTISI ve DEPO BESLEMELERİ (kullanma, yangın, yağmur deposu takviyesi — hava
boşluklu). Paftanın sağına 1/50 depo planı + A-A kesiti, 1/25 hidrofor görünüşü, hesap ve cihaz listesi eklenir.
python3 c_blok_isle.py DEPO.dxf CIKIS.dxf
"""
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

import depo_hidrofor as DH
from depo_hidrofor import C, BO, L

# mimari oda iç sınırları (DEPO.dxf duvar taramasından)
KUL = (203920.0, -680414.0, 204420.0, -679914.0)      # KULLANMA SUYU DEPOSU B-B-02 25 m²
POM = (202770.0, -680414.0, 203880.0, -679914.0)      # POMPA DAİRESİ B-B-01 55,5 m²
YAN_UST = (202375.0, -680454.0, 202730.0, -679914.0)   # YANGIN SUYU DEPOSU B-B-03 (kuzey kolu)
YAG = (203255.0, -681774.0, 203880.0, -680454.0)      # YAĞMUR SUYU DEPOSU B-B-04
DIS_DOGU = 204460.0
H_T = 12.0


def isle(c, H):
    x0, y0, x1, y1 = KUL
    # --- kullanma deposu: göz ayırma perdesi (yeni betonarme)
    px = x0 + (x1 - x0 - DH.PERDE) / 2
    per = [(px, y0), (px + DH.PERDE, y0), (px + DH.PERDE, y1), (px, y1)]
    c.pl(per, 'DUVAR', True)
    c.tara(per, olcek=12.0)
    g1, g2 = (x0 + px) / 2, (px + DH.PERDE + x1) / 2
    c.tx('1. GÖZ', (g1, y0 + 262), H_T, al=TA.MIDDLE_CENTER)
    c.tx('2. GÖZ', (g2, y0 + 262), H_T, al=TA.MIDDLE_CENTER)
    vg = H['goz'] * H['hsu']
    c.tx('V≈%.0f m³' % vg, (g1, y0 + 244), 9, al=TA.MIDDLE_CENTER)
    c.tx('V≈%.0f m³' % vg, (g2, y0 + 244), 9, al=TA.MIDDLE_CENTER)
    for mx in (x0 + 15, px + DH.PERDE + 15):                  # menhol 70x70
        m = [(mx, y1 - 105), (mx + 70, y1 - 105), (mx + 70, y1 - 35), (mx, y1 - 35)]
        c.pl(m, 'CIHAZ', True)
        c.ln(m[0], m[2], 'CIHAZ')
        c.ln(m[1], m[3], 'CIHAZ')
    c.tx('MENHOL 70x70', (x0 + 15, y1 - 110), 6, al=TA.TOP_LEFT)
    cuk = []
    for cx in (x0 + 30, px + DH.PERDE + 30):                  # dip çukurları
        c.pl([(cx, y0 + 30), (cx + 60, y0 + 30), (cx + 60, y0 + 90), (cx, y0 + 90)], 'CIHAZ', True, lt='DASHED')
        cuk.append((cx + 30, y0 + 60))
    c.boru([cuk[1], (cuk[1][0], y0 + 110), (cuk[0][0], y0 + 110), cuk[0]], 'EMIS')
    # --- ŞEBEKE BAĞLANTISI (doğudan) + sayaç
    ys = y1 - 40
    xs = DIS_DOGU + 380
    c.boru([(xs, ys), (DIS_DOGU, ys)], 'TS', 'DN65 ŞEBEKEDEN')
    c.tx('SASKİ ŞEBEKE BAĞLANTISI', (xs + 10, ys), 12, 'TS')
    sx = DIS_DOGU + 250
    c.pl([(sx - 60, ys - 40), (sx + 60, ys - 40), (sx + 60, ys + 40), (sx - 60, ys + 40)], 'CIHAZ', True, lt='DASHED')
    c.blok(BO.KURESEL, (sx - 40, ys), 0, 0.8)
    c.m.add_circle((sx, ys), 9, dxfattribs={'layer': L['CIHAZ']})
    c.tx('M', (sx, ys), 9, 'CIHAZ', TA.MIDDLE_CENTER)
    c.blok(BO.KURESEL, (sx + 40, ys), 0, 0.8)
    c.tx('ANA SU SAYACI DN65 (sayaç kutusunda)', (sx - 60, ys - 48), 8, al=TA.TOP_LEFT)
    c.blok(BO.PISLIK, (DIS_DOGU + 150, ys), 0, 0.8)
    c.blok(BO.CEKVALF, (DIS_DOGU + 110, ys), 180, 0.8)
    c.blok(BO.KURESEL, (DIS_DOGU + 75, ys), 0, 0.8)
    c.pl([(x1 + 8, ys - 12), (x1 + 8, ys + 12)], 'CIHAZ', w=3)       # su tutucu flanş
    # ana besleme hattı: kullanma deposu içinden pompa dairesine, oradan yangın deposuna
    yh = ys
    c.boru([(x1, yh), (POM[0] + 30, yh), (POM[0] + 30, yh), (YAN_UST[0] + 120, yh)], 'TS')
    # kullanma deposu dolumu: her göze şamandıralı vana
    for gx in (g1 + 60, g2 + 60):
        c.boru([(gx, yh), (gx, yh - 55)], 'TS')
        c.m.add_circle((gx, yh - 66), 11, dxfattribs={'layer': L['CIHAZ']})
    c.tx('DOLUM DN50 (şamandıralı)', (g2 + 66, yh - 30), 6, 'TS', TA.MIDDLE_LEFT)
    # pompa dairesinde: yangın deposu besleme vanası + yağmur deposu takviye branşmanı
    c.blok(BO.KURESEL, (POM[0] + 220, yh), 0, 0.8)
    c.tx('YANGIN SUYU DEPOSU BESLEME DN50', (POM[0] + 60, yh + 12), 8, 'TS', TA.BOTTOM_LEFT)
    xb = 203300.0
    c.boru([(xb, yh), (xb, POM[1] + 40), (xb, YAG[3] - 60)], 'TS', 'DN32 TAKVİYE')
    c.blok(BO.KURESEL, (xb, POM[1] + 120), 90, 0.7)
    c.pl([(xb - 10, POM[1] + 70), (xb + 10, POM[1] + 70), (xb + 10, POM[1] + 90), (xb - 10, POM[1] + 90)], 'CIHAZ', True)
    c.tx('S', (xb, POM[1] + 80), 8, 'CIHAZ', TA.MIDDLE_CENTER)
    c.tx('selenoid (seviye kumandalı)', (xb + 14, POM[1] + 80), 7)
    c.ln((xb - 15, YAG[3] - 75), (xb + 15, YAG[3] - 75), 'SU')
    c.tx('hava boşluklu dolum (TS EN 1717 AB) — şebeke takviyesi', (xb + 14, YAG[3] - 75), 8, 'TS')
    c.tx('YAĞMUR SUYU DEPOSU: çatı yağmur inişlerinden filtre üzerinden beslenir', (YAG[0] + 30, YAG[3] - 160), 8, 'TS')
    # yangın deposu dolumu
    yx = YAN_UST[0] + 120
    c.boru([(yx, yh), (yx, yh - 70)], 'TS')
    c.m.add_circle((yx, yh - 81), 11, dxfattribs={'layer': L['CIHAZ']})
    c.tx('şamandıralı vana DN50', (yx + 14, yh - 81), 8)
    c.tx('YANGIN SUYU DEPOSU DOLUM', (YAN_UST[0] + 20, yh + 12), 8, 'TS', TA.BOTTOM_LEFT)
    for xw in (POM[2] + 8, POM[0] - 8):                         # duvar geçişleri
        c.pl([(xw, yh - 12), (xw, yh + 12)], 'CIHAZ', w=3)
    # --- HİDROFOR GRUBU (pompa dairesi doğusu, mimari yazılardan uzak)
    ye = y0 + 110                                             # emiş hattı (1. göz dip çukurundan)
    c.boru([cuk[0], (cuk[0][0], ye), (POM[2] - 330, ye)], 'EMIS', 'DN65 EMİŞ')
    c.pl([(POM[2] + 8, ye - 12), (POM[2] + 8, ye + 12)], 'CIHAZ', w=3)
    c.blok(BO.KURESEL, (POM[2] - 25, ye), 0, 0.8)
    c.blok(BO.PISLIK, (POM[2] - 60, ye), 0, 0.8)
    pxs = [POM[2] - 130, POM[2] - 220]
    yb = ye + 190
    for i, p_ in enumerate(pxs):
        c.boru([(p_, ye), (p_, ye + 45)], 'EMIS')
        c.blok('ROTAS-POMPA', (p_, ye + 60), 90, 1.0)
        c.boru([(p_, ye + 73), (p_, yb)], 'BASMA')
        c.blok(BO.CEKVALF, (p_, ye + 100), 90, 0.7)
        c.blok(BO.KURESEL, (p_, ye + 130), 90, 0.7)
        c.tx('P%d' % (i + 1), (p_ + 16, ye + 60), 9, 'CIHAZ')
    xk = pxs[-1] - 70
    c.boru([(pxs[0] + 45, yb), (xk, yb), (xk, POM[3] + 40)], 'BASMA')
    c.tx('DN50 BASMA → BİNAYA', (xk - 6, yb + 60), 8, 'BASMA', TA.BOTTOM_RIGHT, 90)
    c.m.add_circle((pxs[0] + 45, yb - 30), 20, dxfattribs={'layer': L['CIHAZ']})
    c.boru([(pxs[0] + 45, yb), (pxs[0] + 45, yb - 10)], 'BASMA')
    c.tx('%d lt' % H['Vtank'], (pxs[0] + 45, yb - 30), 7, 'CIHAZ', TA.MIDDLE_CENTER)
    pn = [(POM[2] - 28, ye + 140), (POM[2] - 5, ye + 140), (POM[2] - 5, ye + 230), (POM[2] - 28, ye + 230)]
    c.pl(pn, 'CIHAZ', True)
    c.tx('PANO', (POM[2] - 16, ye + 185), 7, 'CIHAZ', TA.MIDDLE_CENTER, 90)
    c.tx('HİDROFOR GRUBU 1+1', (xk + 10, yb + 40), 9, 'CIHAZ', TA.BOTTOM_LEFT)
    c.tx('Q=%d m³/h  H=%d mSS  frekans konv.' % (H['Qsec'], H['Halt']), (xk + 10, yb + 26), 8, 'CIHAZ', TA.BOTTOM_LEFT)
    # --- drenaj çukuru (taşma + boşaltma), pompa dairesi güneydoğu köşesi
    dcx, dcy = POM[2] - 45, y0 + 45
    c.pl([(dcx - 30, dcy - 30), (dcx + 30, dcy - 30), (dcx + 30, dcy + 30), (dcx - 30, dcy + 30)], 'CIHAZ', True)
    c.m.add_circle((dcx, dcy), 10, dxfattribs={'layer': L['CIHAZ']})
    c.boru([(x0 + 15, y1 - 160), (x0 + 15, dcy + 15), (dcx + 30, dcy + 15)], 'TASMA')
    c.tx('Ø100 TAŞMA', (x0 + 21, y1 - 230), 7, 'TASMA', TA.BOTTOM_LEFT, 90)
    c.boru([(cuk[1][0] + 10, y0 + 22), (dcx + 30, y0 + 22)], 'TASMA')
    c.tx('DN50 BOŞALTMA', (cuk[1][0] - 20, y0 + 26), 6, 'TASMA', TA.BOTTOM_RIGHT)
    c.boru([(dcx - 30, dcy), (POM[2] - 330, dcy)], 'TASMA', 'dalgıç pompa basma → yağmur suyu rögarına')
    c.tx('DRENAJ ÇUKURU 60x60x80 + DALGIÇ POMPA', (dcx - 35, dcy - 34), 6, al=TA.TOP_RIGHT)


def main():
    kaynak, cikis = sys.argv[1:3]
    doc = ezdxf.readfile(kaynak)
    for blk in doc.blocks:                       # dinamik blok uzantıları (bozuk sözlük üretmesin)
        for e in [blk.block_record] + list(blk):
            if e.has_extension_dict:
                e.discard_extension_dict()
    olcu0 = doc.header.get('$MEASUREMENT', 0)
    doc.header['$MEASUREMENT'] = 1          # tarama desenleri metrik (ISO) tanımla çizilsin
    c = C(doc)
    H = DH.hesap()
    isle(c, H)
    # pafta: ayrıntılar sağa
    ox, oy = 206600.0, -680800.0
    DH.plan(c, H, ox, oy)
    DH.kesit(c, H, ox + 900, oy)
    DH.hidrofor(c, H, ox, oy - 1250)
    DH.hesap_tablolari(c, H, ox + 1750, oy + 600)
    DH.cerceve(c, ox - 480, oy - 1400, ox + 2380, oy + 780)
    c.tx('C BLOK SU DEPOSU — KULLANMA SUYU DEPOSU VE HİDROFOR AYRINTILARI', (ox - 470, oy + 800), 30, 'BASLIK', TA.BOTTOM_LEFT)
    doc.header['$MEASUREMENT'] = olcu0
    doc.saveas(cikis)
    print('yazıldı', cikis)


if __name__ == '__main__':
    main()
