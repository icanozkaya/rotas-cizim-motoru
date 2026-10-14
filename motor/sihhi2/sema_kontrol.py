"""sihhi2 — şema / temel öz-kontrolü: referans kırpımlarla (kullanıcının new_block çizimi) YAN YANA PNG +
yazı çakışması / etiket–hat ölçümü (kontrolörle aynı fonksiyonlar: denetle.yazi_poligonu, boru_katmani).

    python3 motor/sihhi2/sema_kontrol.py [--ad NB_SIHHI] [--cikis proje/denemeler/sihhi2]
"""
import argparse
import json
import os
import sys

import ezdxf
from PIL import Image

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import sema_ortak as O  # noqa: E402
sys.path.insert(0, O.KOK + '/motor/kontrolor')
import kirp  # noqa: E402

REF = O.KOK + '/kutuphane/arastirma/referans/sihhi'


def _ref(ad):
    return os.path.join(REF, ad)


def pencereler(oz):
    """(ad, kendi pencere, referans png) — referans pencereleri SIHHI_ALTIN_REFERANS §0"""
    X0, Y0 = 260820.0, -443249.0
    out = [('02_sema_genel', tuple(oz['pafta']), '02_sema_genel.png'),
           ('03_sayac_grubu', (X0 - 60, Y0 - 81, X0 + 600, Y0 + 149), '03_sema_sayac_grubu_sebeke.png'),
           ('04_depo', (X0 + 80, Y0 + 1139, X0 + 640, Y0 + 1529), '04_sema_depo.png')]
    ys = oz['yiginlar']
    # D1 (zemin) bloğu: dairesi D1 olan yığın
    for Y in ys:
        if Y['daireler'].get('0') == 'D1' or Y['daireler'].get(0) == 'D1':
            out.append(('05_daire_D1_zemin', (Y['dikme_x'] - 70, Y0 - 151, Y['kombi_x'] + 140, Y0 + 419),
                        '05_sema_daire_D1_zemin.png'))
            x = Y['dikme_x']
            out.append(('29_armatur_grubu', (x - 50, Y0 - 91, x + 750, Y0 + 269), '29_sema_armatur_grubu_yakin_D1_banyo.png'))
            k = oz['kolonlar'][Y['kolonlar'][-1]]['x_sema']
            out.append(('30_kolon_dibi', (k - 85, Y0 - 151, k + 85, Y0 + 69), '30_sema_kolon_dibi_TK_rogar_yakin.png'))
        if Y['daireler'].get('0') == 'D3' or Y['daireler'].get(0) == 'D3':
            out.append(('06_daire_D3_zemin', (Y['dikme_x'] - 70, Y0 - 151, Y['kombi_x'] + 140, Y0 + 419),
                        '06_sema_daire_D3_zemin.png'))
            out.append(('28_kombi_D', (Y['kombi_x'] - 300, Y0 + 189, Y['kombi_x'] + 130, Y0 + 349),
                        '28_sema_kombi_D_etiketi_yakin.png'))
    x1 = oz['pafta'][2]
    out.append(('07_kolon_ust', (X0 + 580, Y0 + 769, x1 - 600, Y0 + 1349), '07_sema_kolon_ust_etiketler.png'))
    nR = len(oz['rogarlar'])
    if nR:
        xm = X0 + oz['sema_genislik'] / 2
        out.append(('08_rogar_semasi', (xm - 239 * nR / 2 - 120, Y0 - 731, xm + 239 * nR / 2 + 140, Y0 - 351),
                    '08_rogar_semasi.png'))
    xs1 = X0 + oz['sema_genislik']
    out.append(('09_yagmur_semasi', (xs1 - 50, Y0 - 471, xs1 + 640, Y0 + 1309), '09_yagmur_semasi.png'))
    return out


def pngler(cikis=O.CIKIS, ad='NB_SIHHI'):
    with open(os.path.join(cikis, ad + '_sema_ozet.json'), encoding='utf-8') as f:
        oz = json.load(f)
    hedef = os.path.join(cikis, 'sema_png')
    os.makedirs(hedef, exist_ok=True)
    doc = ezdxf.readfile(os.path.join(cikis, ad + '_SEMA.dxf'))
    cz = kirp.Cizici(doc)
    sonuc = []
    for isim, w, refad in pencereler(oz):
        ref = Image.open(_ref(refad))
        gen = max(4.0, min(30.0, ref.width / 100.0))
        if isim == '02_sema_genel':
            gen = 30.0
        p = os.path.join(hedef, isim + '_kendi.png')
        cz.kirp(w, p, baslik='', genislik_in=gen, dpi=100, beyaz=True)
        y = os.path.join(hedef, isim + '_YANYANA.png')
        kirp.yan_yana(p, _ref(refad), y, sol_ad='MOTOR (sema.py)', sag_ad='REFERANS new_block (kullanıcı)')
        os.remove(p)
        sonuc.append(y)
    # temel
    tdoc = ezdxf.readfile(os.path.join(cikis, ad + '_TEMEL.dxf'))
    tz = kirp.Cizici(tdoc)
    p = os.path.join(hedef, '10_temel_kendi.png')
    tz.kirp((250042, -444050, 252513, -441150), p, genislik_in=17.0, beyaz=True)
    y = os.path.join(hedef, '10_temel_YANYANA.png')
    kirp.yan_yana(p, _ref('10_temel_plan_genel.png'), y, sol_ad='MOTOR (sema_temel.py)', sag_ad='REFERANS new_block')
    os.remove(p)
    sonuc.append(y)
    return sonuc


def olc(cikis=O.CIKIS, ad='NB_SIHHI'):
    """kontrolörün T07 (etiket–etiket / etiket–hat / boy) ve T08 testlerini ŞEMA paftasında, T07'yi TEMEL paftasında
    çalıştırır (kontrolör.py kat testlerini yalnız kat paftalarında yapar; şema paftasında T07 ölçülmez)."""
    import cizim as CZ
    import testler as TS
    out = {}
    for tur in ('SEMA', 'TEMEL'):
        cz = CZ.Cizim(os.path.join(cikis, '%s_%s.dxf' % (ad, tur)))
        w = cz.cerceveler[0] if cz.cerceveler else None
        b = TS.t07_etiketler(cz, tur, {'pencere': w, 'rooms': [], 'fx': [], 'taramalar': []})
        if tur == 'SEMA':
            b += TS.t08_sema_sayac(cz)
        b += TS.t11_denetle(os.path.join(cikis, '%s_%s.dxf' % (ad, tur)))
        out[tur] = [(x.test, x.durum, x.mesaj, x.nokta) for x in b]
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ad', default='NB_SIHHI')
    ap.add_argument('--cikis', default=O.CIKIS)
    ap.add_argument('--png-yok', action='store_true')
    a = ap.parse_args()
    for tur, bs in olc(a.cikis, a.ad).items():
        for t, d, msg, p in bs:
            if d != 'INFO' or 'pis su' in msg:
                print(tur, t, d, msg[:150], p if p else '')
    if not a.png_yok:
        for s in pngler(a.cikis, a.ad):
            print(s)
