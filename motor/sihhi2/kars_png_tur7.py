"""Tur 7 (15.10 (D) ikinci geri bildirim) üretici kırpımları: solda motor (birleşik şerit), sağda kullanıcının new_block
çizimi; pencereler zemin kat koordinatında, kat ötelemesi eklenir (1. kat +2034, 2. kat +4082).
    python3 motor/sihhi2/kars_png_tur7.py [DXF] [cikti_klasoru]
Pencereler: taşınan / şafta yakın pis su kolonları (P2-P3, P5-P6, P7, P8, P9) her kat; zemin sayaç grubu + şebeke girişi
('3' balonu); merdiven holü besleme düşeyleri her kat; üst kat daire girişleri (D5/D8); mutfaklar (süzgeçsiz) her kat."""
import os
import sys

import ezdxf

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK + '/motor/kontrolor')
import kirp  # noqa: E402

DXF = sys.argv[1] if len(sys.argv) > 1 else KOK + '/proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf'
OUT = sys.argv[2] if len(sys.argv) > 2 else KOK + '/kutuphane/arastirma/kontrol_png/sihhi_tur7_uretici'
OFF = {'Z': 0, 'K1': 2034, 'K2': 4082}
KAT_W = {   # zemin koordinatı
    'kolon_P2_P3': (253640, -442850, 253860, -442620),
    'kolon_P5_P6': (253280, -442850, 253500, -442620),
    'kolon_P7': (253650, -441900, 253850, -441700),
    'kolon_P8': (252990, -442330, 253190, -442130),
    'kolon_P9': (252700, -441980, 252860, -441820),
    'kolon_P1_P4': (253480, -443480, 253650, -443330),
    'merdiven_holu_besleme': (253420, -442480, 253780, -442000),
    'mutfak_D1_D2': (253270, -443500, 253890, -443000),
    'mutfak_D3': (253480, -441900, 253860, -441500),
}
TEK = {
    'Z_sayac_grubu': (253540, -442480, 253760, -442220),
    'Z_bina_girisi_sebeke_balon3': (253520, -442280, 253800, -442020),
    'K1_D5_girisi': (255454 + 0, -442300, 255800, -441950),
    'K2_D8_girisi': (257502, -442300, 257850, -441950),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    A = kirp.Cizici(ezdxf.readfile(DXF))
    B = kirp.Cizici(ezdxf.readfile('/tmp/claude-0/uu/new_block.dxf'))
    n = 0
    isler = []
    for k, o in OFF.items():
        for ad, (x0, y0, x1, y1) in KAT_W.items():
            isler.append(('%s_%s' % (k, ad), (x0 + o, y0, x1 + o, y1)))
    isler += list(TEK.items())
    for ad, w in isler:
        a, b = OUT + '/' + ad + '_a.png', OUT + '/' + ad + '_b.png'
        A.kirp(w, a, baslik=ad + ' (motor, tur 7)', genislik_in=5.0, dpi=110)
        B.kirp(w, b, baslik='REF ' + ad + ' (kullanıcı new_block)', genislik_in=5.0, dpi=110)
        kirp.yan_yana(a, b, OUT + '/' + ad + '.png')
        os.remove(a)
        os.remove(b)
        n += 1
    print('%d PNG -> %s' % (n, OUT))


if __name__ == '__main__':
    main()
