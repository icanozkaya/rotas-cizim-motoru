# -*- coding: utf-8 -*-
"""LibreDWG çıktısında birden fazla satıra bölünmüş metin değerlerini (MTEXT \\P vb.) onarır.
Kullanım: python3 dxf_temizle.py giris.dxf cikis.dxf"""
import sys
def main(gir, cik):
    with open(gir, 'r', encoding='utf-8', errors='replace') as f:
        sat = f.read().split('\n')
    out = []
    i = 0
    while i < len(sat):
        kod = sat[i].strip()
        if i + 1 >= len(sat):
            break
        deger = sat[i + 1]
        i += 2
        # sonraki satır sayısal kod değilse değere ekle
        while i < len(sat) and not sat[i].strip().lstrip('-').isdigit() and sat[i].strip() != '':
            deger += ' ' + sat[i]
            i += 1
        if i < len(sat) and sat[i].strip() == '' and i + 1 < len(sat) and not sat[i+1].strip().lstrip('-').isdigit():
            pass
        out.append(kod); out.append(deger.replace('\r', ''))
    with open(cik, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
main(sys.argv[1], sys.argv[2])
