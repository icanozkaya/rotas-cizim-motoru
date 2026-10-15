"""Tur 6 (15.10 (D)) üretici kırpımları: her kolon yakın (her kat; solda motor, sağda kullanıcının new_block çizimi),
zemin giriş sayaç grubu, merdiven holü besleme kolonları (3 kat), çatı deposu bağlantısı.
    python3 motor/sihhi2/kars_png_tur6.py [DXF] [cikti_klasoru]"""
import json
import os
import sys

import ezdxf

KOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, KOK + '/motor/kontrolor')
import kirp  # noqa: E402

DXF = sys.argv[1] if len(sys.argv) > 1 else KOK + '/proje/denemeler/sihhi2/NB_SIHHI_PAFTA_DENEME.dxf'
OUT = sys.argv[2] if len(sys.argv) > 2 else KOK + '/kutuphane/arastirma/kontrol_png/sihhi_tur6_uretici'
OFF = {'Z': 0, 'K1': 2034, 'K2': 4082}


def main():
    os.makedirs(OUT, exist_ok=True)
    T = json.load(open(KOK + '/motor/sihhi2/tasarim_new_block.json', encoding='utf-8'))
    A = kirp.Cizici(ezdxf.readfile(DXF))
    B = kirp.Cizici(ezdxf.readfile('/tmp/claude-0/uu/new_block.dxf'))
    n = 0
    for k, o in OFF.items():
        for no, c in T['kolon_merkez'].items():
            w = (c[0] + o - 75, c[1] - 75, c[0] + o + 75, c[1] + 75)
            ad = 'kolon_%s_%s' % (k, no)
            a, b = OUT + '/' + ad + '_a.png', OUT + '/' + ad + '_b.png'
            A.kirp(w, a, baslik=ad + ' (hat dış çemberde biter)', genislik_in=4.0, dpi=110)
            B.kirp(w, b, baslik='REF ' + ad, genislik_in=4.0, dpi=110)
            kirp.yan_yana(a, b, OUT + '/' + ad + '.png')
            os.remove(a)
            os.remove(b)
            n += 1
    tek = {'zemin_giris_sayac_grubu': (253540, -442480, 253760, -442220),
           'zemin_bina_girisi_sebeke': (253420, -442480, 254300, -442020),
           'cati_depo_kolonlari': (259520, -442420, 259900, -442040)}
    for k, o in OFF.items():
        tek['merdiven_holu_besleme_%s' % k] = (253420 + o, -443010, 253760 + o, -442030)
        tek['mutfak_suzgecsiz_%s_D1D2' % k] = (253270 + o, -443500, 253890 + o, -443000)
    for ad, w in tek.items():
        A.kirp(w, OUT + '/' + ad + '.png', baslik=ad, genislik_in=7.0, dpi=110)
        n += 1
    print('%d PNG -> %s' % (n, OUT))


if __name__ == '__main__':
    main()
