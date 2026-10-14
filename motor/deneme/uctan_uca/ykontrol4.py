"""R4 yazı-yazı çakışma kontrolü — `motor/deneme/denetim/denetle.py` ile ORTAK kural (aynı fonksiyon:
`denetle.yazi_cakismalari`), böylece iki araç aynı sayıyı verir.
Yazılar: TEXT / MTEXT / görünür ATTRIB (yazı tipi ölçülü kutu). Sayılmayan: mimari-mimari çifti (mimar altlığının kendi
yazıları; ayrıca bilgi olarak döner) ve aynı INSERT'in kendi öznitelikleri. Eşik: küçük yazı alanının %2'si.
Kullanım: python3 ykontrol4.py dosya.dxf"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'denetim'))
import denetle  # noqa: E402


def cakisma(msp, oran=None):
    return denetle.yazi_cakismalari(msp, oran)[0]


def cakisma_ayrinti(msp, oran=None):
    """(cakisma_listesi, mimari_mimari_sayisi)"""
    return denetle.yazi_cakismalari(msp, oran)


if __name__ == '__main__':
    import collections
    import ezdxf
    doc = ezdxf.readfile(sys.argv[1])
    r, mim = cakisma_ayrinti(doc.modelspace())
    print(len(r), '(mimari-mimari bilgi: %d)' % mim)
    print(collections.Counter((a[0], a[2]) for a in r).most_common(20))
    for x in r[:60]:
        print(x)
