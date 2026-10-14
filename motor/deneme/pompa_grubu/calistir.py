# -*- coding: utf-8 -*-
"""Kullanım: python3 calistir.py girdi/yangin_test.json [cikti.dxf]
Girdi JSON 'tip': yangin | hidrofor | pissu. Çıktı varsayılan: proje/denemeler/pompa_grubu/<TIP>_KESIT.dxf"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak  # noqa: motor/ yolunu ekler

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
AD = {'yangin': 'YANGIN_POMPA_GRUBU_KESITI_R2.dxf', 'hidrofor': 'HIDROFOR_GRUBU_KESITI_R2.dxf', 'pissu': 'PIS_SU_POMPA_CUKURU_KESITI_R2.dxf'}


def calistir(girdi, cikti=None):
    g = json.load(open(girdi, encoding='utf-8'))
    tip = g['tip']
    mod = __import__({'yangin': 'yangin', 'hidrofor': 'hidrofor', 'pissu': 'pissu'}[tip])
    cikti = cikti or os.path.join(KOK, 'proje', 'denemeler', 'pompa_grubu', AD[tip])
    c, n, bilgi = mod.ciz(g, cikti)
    print(f'{tip}: {cikti}  (çakışma uyarısı: {n})')
    for u in c.uyari:
        print('  !', u)
    print('  ', bilgi)
    # R2 kontrolleri: MTY yok, elektrik katmanı yok, itfaiye çek valf yönü
    import rotas_sembol, itfaiye_test, ezdxf
    print('   MTY:', rotas_sembol.mty_kontrol(cikti) or 'yok')
    d = ezdxf.readfile(cikti)
    print('   elektrik katmanı:', [l.dxf.name for l in d.layers if 'ELEKTRIK' in l.dxf.name] or 'yok')
    if bilgi.get('itf_hedef'):
        r = itfaiye_test.kontrol(cikti, bilgi['itf_hedef'])
        print('   itfaiye yön testi:', r['yonler'], 'HATA:', r['hata'])
    return cikti


if __name__ == '__main__':
    calistir(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
