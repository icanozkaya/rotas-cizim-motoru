"""Üretici karşılaştırma kırpımları (tur 4): kontrolör tur 3 pencere adlarıyla, solda NB_SIHHI_PAFTA_DENEME, sağda
kullanıcının new_block çizimi. Kat ötelemeleri: 1. kat +2034, 2. kat +4082 (zemin kat koordinatına göre).
    python3 motor/sihhi2/kars_png.py [cikti_klasoru]"""
import os
import sys

import ezdxf

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK + '/motor/kontrolor')
import kirp  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else KOK + '/kutuphane/arastirma/kontrol_png/sihhi_tur4_uretici'
OFF = {'Z': 0, 'K1': 2034, 'K2': 4082}
KAT_W = {  # zemin kat koordinatı
    '11_wcbanyo_D3_P8': (252960, -442340, 253270, -441980),
    '12_dus_balkon_P9_YB8': (252600, -442090, 252960, -441810),
    '13_banyo_wclvb_D1_P2_P3': (253590, -442880, 253980, -442370),
    '14_mutfak_kombi_P1_P4': (253270, -443710, 253890, -442990),
    '15_banyo_wclvb_D2_P5_P6': (253170, -442880, 253560, -442370),
    '16_giris_hol_D3': (252960, -442150, 253840, -441490),
    '17_on_balkon_YB2_YB3': (252800, -443820, 254300, -443330),
    '31_daire_girisi_hol_D1': (253560, -443100, 254000, -442780),
}
EK = {
    'B_Z_D1_wclvb_pissu': (253680, -442880, 253900, -442680),
    'B_Z_D2_BM_pissu': (253460, -443320, 253660, -443120),
    'B_Z_D3_aspirator_notu': (252700, -442400, 253350, -441900),
    'B_K1_D5_giris_kbac': (255380, -442250, 255700, -441950),
    'B_K2_D8_giris_kbac': (257428, -442250, 257748, -441950),
    'B_K1_D5_wcbanyo_dus': (254994, -442340, 255334, -441960),
    'B_K1_D5_aspirator_oda': (254780, -442400, 255340, -441900),
    'B_K1_D6_wcdus_aspirator_notu': (255600, -442450, 256020, -442050),
    'B_K1_D6_banyo': (255680, -442700, 255940, -442380),
    'B_K1_D4_BM': (255494, -443320, 255694, -443120),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    A = kirp.Cizici(ezdxf.readfile(KOK + '/proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf'))
    B = kirp.Cizici(ezdxf.readfile('/tmp/claude-0/uu/new_block.dxf'))
    isler = []
    for k, o in OFF.items():
        for ad, (x0, y0, x1, y1) in KAT_W.items():
            isler.append(('%s_%s' % (k, ad), (x0 + o, y0, x1 + o, y1)))
    isler += list(EK.items())
    for ad, w in isler:
        a = OUT + '/' + ad + '_a.png'
        b = OUT + '/' + ad + '_b.png'
        A.kirp(w, a, baslik=ad, genislik_in=6.5, dpi=110)
        B.kirp(w, b, baslik='REF ' + ad, genislik_in=6.5, dpi=110)
        kirp.yan_yana(a, b, OUT + '/' + ad + '.png')
        os.remove(a)
        os.remove(b)
    print('%d PNG -> %s' % (len(isler), OUT))


if __name__ == '__main__':
    main()
