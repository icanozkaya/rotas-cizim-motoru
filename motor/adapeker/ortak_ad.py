# -*- coding: utf-8 -*-
"""Adapeker çizimleri ortak: belge, mimari altlık (ROTAS-MIMARI*), yazı yardımcıları."""
import os, sys, pickle, math
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
sys.path.insert(0, BURASI)
import mimari_ad as M  # noqa

CIKIS = os.path.join(KOK, 'proje', 'adapeker')
AL = {'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER, 'BR': TA.BOTTOM_RIGHT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER,
      'MR': TA.MIDDLE_RIGHT, 'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT}
PROJE = dict(ad='ADAPEKER İNŞAAT MALZEMELERİ SAN. ve TİC. LTD. ŞTİ. - 6 BAĞIMSIZ BÖLÜMLÜ MESKEN',
             sahibi='ADAPEKER İNŞAAT MALZEMELERİ SANAYİ VE TİCARET LİMİTED ŞİRKETİ', il='SAKARYA', ilce='ADAPAZARI',
             mahalle='GÜNEŞLER', pafta='G24B24B1A', ada='4653', parsel='19', yapi_sinifi='3/A', cins='BETONARME',
             arsa='475,86 m²', isitma='YERDEN ISITMA (her dairede kombi)', kat='ZEMİN + 2 NORMAL KAT',
             bb=6, mimar='FIRAT MÜRSEL KAYA - MİMAR (KAYA MİMARLIK)', kat_h=3.00)


def yeni_doc(katmanlar):
    doc = ezdxf.new('R2018', setup=True)
    doc.units = 5
    doc.header['$MEASUREMENT'] = 1
    doc.header['$INSUNITS'] = 5
    for st in ('ROTAS', 'ROTAS-YAZI'):
        if st not in doc.styles:
            doc.styles.new(st, dxfattribs={'font': 'arial.ttf'})
    for lt, desen in (('ROTAS_PISSU', [12.0, 8.0, -2.0, 0.0, -2.0]), ('ROTAS_KESIK', [10.0, 6.0, -4.0])):
        if lt not in doc.linetypes:
            doc.linetypes.add(lt, pattern=desen)
    for ad, (renk, tip) in katmanlar.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk, linetype=tip)
    for ad, renk in (('ROTAS-MIMARI', 8), ('ROTAS-MIMARI-KOLON', 8), ('ROTAS-MIMARI-YAZI', 8)):
        if ad not in doc.layers:
            doc.layers.add(ad, color=renk)
    return doc


def T(m, x, y, s, h, al='BL', lay='ROTAS-YAZI', rot=0.0, w=0.8, renk=256):
    t = m.add_text(s, height=h, dxfattribs={'layer': lay, 'style': 'ROTAS-YAZI', 'rotation': rot, 'width': w, 'color': renk})
    t.set_placement((x, y), align=AL[al])
    return t


def PL(m, pts, lay, kapali=False, w=0.0, renk=256):
    return m.add_lwpolyline(pts, close=kapali, dxfattribs={'layer': lay, 'const_width': w, 'color': renk})


def maske(m, x0, y0, x1, y1, lay):
    m.add_wipeout([(x0, y0), (x1, y1)], dxfattribs={'layer': lay})


HARIC = ('YLZ-ÖLÇÜ', 'YLZ-TARAMA', 'YLZ-Kesit Çizgisi', 'YLZ-GÖRÜNÜŞ -arkada kalanlar-', 'YLZ-KİRİŞ', 'A-YALITIM PERDE')


def mimari_altlik(m, katlar=('Z', '1', '2'), pad=330, haric=HARIC, yazi=True, sadece=None):
    """mimari plan(lar)ı gri altlık olarak kopyala. sadece: yalnız bu katmanlar (ör. altyapı: kolon + dış hat)"""
    n = 0
    for k in katlar:
        w = M.win(k, pad)
        for r in M.kayit():
            lay = r[1]
            if lay in haric or (sadece and lay not in sadece):
                continue
            if r[0] in 'LPA':
                if not all(M.icinde(p, w) for p in r[2]):
                    continue
                hl = 'ROTAS-MIMARI-KOLON' if lay == 'YLZ-KOLON' else 'ROTAS-MIMARI'
                m.add_lwpolyline(r[2], close=(r[0] == 'P' and r[3]), dxfattribs={'layer': hl})
                n += 1
            elif r[0] == 'C' and M.icinde(r[2], w):
                m.add_circle(r[2], r[3], dxfattribs={'layer': 'ROTAS-MIMARI'})
            elif r[0] == 'H' and lay == 'YLZ-KOLON' and all(M.icinde(p, w) for p in r[2]):
                h = m.add_hatch(color=8, dxfattribs={'layer': 'ROTAS-MIMARI-KOLON'})
                h.set_pattern_fill('ANSI31', scale=4)
                h.paths.add_polyline_path(r[2], is_closed=True)
            elif r[0] == 'T' and yazi and M.icinde(r[2], w) and r[3].strip():
                s = r[3].replace('\n', ' ').strip()
                if r[4] >= 4:
                    m.add_mtext(r[3], dxfattribs={'layer': 'ROTAS-MIMARI-YAZI', 'char_height': r[4], 'insert': r[2],
                                                  'rotation': r[5] or 0, 'style': 'ROTAS-YAZI'})
    return n


def kat_basligi(m, k, baslik, y_alt=-3330, lay='ROTAS-PAFTA-YAZI'):
    x = (M.W0[0] + M.W0[2]) / 2 + M.OFS[k]
    T(m, x, y_alt - 60, '%s %s' % (M.KAT_ADI[k], baslik), 30, 'MC', lay)
    T(m, x, y_alt - 105, 'ÖLÇEK : 1 / 50', 20, 'MC', lay)


def antet(m, x, y, baslik, w=900):
    """sol alt köşe (x, y)"""
    lay = 'ROTAS-PAFTA'
    PL(m, [(x, y), (x + w, y), (x + w, y + 420), (x, y + 420)], lay, True, 2)
    sat = ['ROTAŞ MÜHENDİSLİK . PROJE . MÜŞAVİRLİK',
           'Semerciler Mah. Sait Faik Sk. No:22/C Z01 Adapazarı/Sakarya - 0264 272 00 49',
           'İŞ: ' + PROJE['ad'],
           'YER: %s / %s - %s MAH. ADA %s PARSEL %s (PAFTA %s)' % (PROJE['il'], PROJE['ilce'], PROJE['mahalle'], PROJE['ada'],
                                                               PROJE['parsel'], PROJE['pafta']),
           'YAPI: %s, %s, %d BAĞIMSIZ BÖLÜM, YAPI SINIFI %s, ARSA %s' % (PROJE['cins'], PROJE['kat'], PROJE['bb'],
                                                                     PROJE['yapi_sinifi'], PROJE['arsa']),
           'PROJE: ' + baslik,
           'PROJE SORUMLUSU: Mak. Müh. Bayram GENÇ',
           'HAZIRLAYAN: Can ÖZKAYA - TEKNİK RESSAM          TARİH: 10.2026']
    for i, s in enumerate(sat):
        T(m, x + 15, y + 400 - 18 - i * 48, s, 22 if i == 0 else 14, 'TL', 'ROTAS-PAFTA-YAZI')
