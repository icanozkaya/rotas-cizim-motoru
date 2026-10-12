"""Örnek asansör projesindeki makine / kasnak bloklarını sembol kütüphanesine çıkarır.
Kullanım: python3 asn_sembol_cikar.py ornek.dxf kutuphane/asansor/semboller.json"""
import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'motor'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dxfparse as D
import asn_sablon_cikar as A

GRUP = {   # sembol adı: (blok adları, x aralığı)  -> örnekteki yerleşime göre
    'makine_yan': (['ASANSÖRKAİDESİ'], None),
    'makine_on': (['ASANSÖRKAİDE', 'new block6MMHS', 'SW_CENTERMARKSYMBOL_0'], (332400, 332700)),
    'kasnak240': (['240KASNAK'], (332500, 332540)),
}


def main(src, dst):
    D.ENC = 'utf-8'
    bl, en = D.read(src)
    out = {}
    for ad, (adlar, xr) in GRUP.items():
        sec = [e for e in en if e['_t'] == 'INSERT' and e.get('name') in adlar and (xr is None or xr[0] <= e.get('10', 0) <= xr[1])]
        flat = A.duzlestir(bl, sec)
        d = A.kayitlar(flat, None)
        out[ad] = d
        print(ad, len(sec), round(d['gen'], 1), round(d['yuk'], 1), len(d['kayitlar']))
    json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
