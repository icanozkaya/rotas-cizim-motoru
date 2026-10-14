"""sihhi2 — kolon şeması / temel planı ORTAK: model okuma, çap/yük kuralları, daire yığınları ve kolon sırası.

Birim cm. Kaynak: `sihhi_model.json` (MODEL.md). Kurallar: kutuphane/arastirma/KOLON_SEMASI_TARZI.md §3,
SIHHI_ALTIN_REFERANS.md §5–6 (kullanıcının new_block çizimi ölçüleri).
"""
import json
import math
import os
import re

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
CIKIS = KOK + '/proje/denemeler/sihhi2'
MODEL_GERCEK = CIKIS + '/sihhi_model.json'
MODEL_ORNEK = BURASI + '/ornek_model.json'

# kullanıcı çizimi yükleri (model yoksa)
MB_S = {'LV': 0.75, 'WC': 0.5, 'DUS': 2.5, 'EV': 1.0, 'CM': 1.5, 'BM': 1.5, 'KOMBI': 0.5}
MB_H = {'LV': 0.75, 'DUS': 2.5, 'EV': 1.0}
SB = {'LV': 2, 'WC': 10, 'DUS': 7, 'EV': 4, 'CM': 4, 'BM': 4, 'YS': 2}
# armatür bağlantı çapı (new_block şeması: lavabo/klozet/ÇM/BM/kombi Ø20, duş/eviye Ø25)
BAG_CAP = {'LV': 'Ø20', 'WC': 'Ø20', 'DUS': 'Ø25', 'EV': 'Ø25', 'CM': 'Ø20', 'BM': 'Ø20', 'KOMBI': 'Ø20'}
ARM_ADI = {'LV': 'LAVABO', 'WC': 'KLOZET', 'DUS': 'DUŞ', 'EV': 'EVİYE', 'CM': 'ÇAMAŞIR MAKİNESİ',
           'BM': 'BULAŞIK MAKİNESİ', 'YS': 'YER SÜZGECİ', 'KOMBI': 'KOMBİ'}


def fmt(v):
    return ('%.2f' % v).rstrip('0').rstrip('.')


def inc(mb):
    """temiz su çapı (kullanıcı tablosu, plan.py ile aynı)"""
    if mb <= 1.0:
        return '1/2"'
    if mb <= 2.5:
        return '3/4"'
    if mb <= 8.5:
        return '1"'
    if mb <= 12.0:
        return '1 1/4"'
    if mb <= 20.0:
        return '1 1/2"'
    return '2"'


def pis_cap(sb, wc):
    if wc:
        return 'Ø100'
    if sb <= 8:
        return 'Ø50'
    if sb <= 16:
        return 'Ø70'
    return 'Ø100'


def kno(s):
    m = re.search(r'\d+', s or '')
    return int(m.group()) if m else 0


def model_oku(yol=None):
    if yol is None:
        yol = MODEL_GERCEK if os.path.exists(MODEL_GERCEK) else MODEL_ORNEK
    with open(yol, encoding='utf-8') as f:
        m = json.load(f)
    m['_yol'] = yol
    return m


class Grup:
    """bir katta bir ıslak hacmin kolon şeması grubu: kolon + armatür sırası (kolondan dışa)"""

    def __init__(self, kat, daire, ad, kolon, tipler):
        self.kat, self.daire, self.ad, self.kolon, self.tipler = kat, daire, ad, kolon, tipler
        self.mutfak = 'mutfak' in (ad or '').lower()

    def sb(self):
        return sum(SB.get(t, 0) for t in self.tipler)

    def wc(self):
        return 'WC' in self.tipler

    def mb_s(self):
        return sum(MB_S.get(t, 0) for t in self.tipler)

    def mb_h(self):
        return sum(MB_H.get(t, 0) for t in self.tipler)


class Yigin:
    """aynı plan konumundaki daireler (zemin D3, 1. kat D5, 2. kat D8 ...): şemada bir sütun bloğu"""

    def __init__(self):
        self.daire = {}          # kat -> daire no
        self.gruplar = {}        # (kat, kolon) -> Grup
        self.kolonlar = []       # sıralı (soldan sağa)
        self.kombi_kat = {}      # kat -> kombi var mı


# armatür sırası, KOLONDAN DIŞA (kullanıcının new_block şeması, SIHHI_ALTIN_REFERANS §5.2 x ölçüleri:
# D1 banyo P3 → lavabo 265407 – klozet 265537 – süzgeç 265667 – duş 265797 – ÇM 265927;
# D1 wc-lvb P2 → klozet 266702 – lavabo 266832; D1 mutfak P1 → BM 267088 – eviye 267218 – kombi 267348)
SIRA_BANYO = ['LV', 'WC', 'YS', 'DUS', 'CM']
SIRA_WC = ['WC', 'LV', 'YS']
SIRA_MUTFAK = ['BM', 'EV', 'YS']


def arm_sirala(tipler, mutfak=False):
    if mutfak or ('EV' in tipler or 'BM' in tipler) and not ('WC' in tipler or 'DUS' in tipler):
        sira = SIRA_MUTFAK + ['CM', 'LV', 'WC', 'DUS']
    elif 'DUS' in tipler or 'CM' in tipler:
        sira = SIRA_BANYO + ['EV', 'BM']
    else:
        sira = SIRA_WC + ['DUS', 'CM', 'EV', 'BM']
    return sorted(tipler, key=lambda t: sira.index(t) if t in sira else 99)


def yiginlar(m):
    """daireleri plan konumuna göre yığınla, yığınları ve kolonları new_block şema sırasına diz.
    Sıra (kullanıcı çizimi): yığınlar kolon x ortalaması artan (D3, D2, D1); yığın içinde ıslak hacim kolonları
    kuzeyden güneye (y azalan), mutfak kolon(lar)ı en sağda (kombi yanında)."""
    kol = {k['no']: k for k in m.get('kolonlar', [])}
    ys = []
    for d in m['daireler']:
        ref = d.get('kombi') or d.get('giris') or {}
        kolonlar = {h.get('kolon') for h in d.get('islak_hacimler', []) if h.get('kolon')}
        hedef = None
        for Y in ys:
            if d['kat'] in Y.daire:
                continue
            r = Y._ref
            yakin = ref and r and math.hypot(ref['x'] - r['x'], ref['y'] - r['y']) < 80
            ortak = len(kolonlar & Y._kol) >= 1
            if yakin or (ortak and not ref):
                hedef = Y
                break
        if hedef is None:
            hedef = Yigin()
            hedef._ref = ref
            hedef._kol = set()
            ys.append(hedef)
        hedef.daire[d['kat']] = d['no']
        hedef._kol |= kolonlar
        hedef.kombi_kat[d['kat']] = bool(d.get('kombi'))
        for h in d.get('islak_hacimler', []):
            p = h.get('kolon')
            if not p:
                continue
            tip = [a['tip'] for a in h.get('armaturler', [])]
            sz = h.get('suzgec')
            # kullanıcının şemasında süzgeç yalnız duşlu hacimlerde; mutfak / wc-lvb'ye kuralla eklenmiş (ek) süzgeç
            # şemaya konmaz (SIHHI_ALTIN §3.4, §8: "wc-lvb ve mutfakta süzgeç yok")
            if sz and not (sz.get('ek') and 'DUS' not in tip):
                tip.append('YS')
            g = hedef.gruplar.get((d['kat'], p))
            if g is None:
                g = hedef.gruplar[(d['kat'], p)] = Grup(d['kat'], d['no'], h.get('ad', ''), p, tip)
            else:   # aynı katta aynı kolona iki hacim: birleştir
                g.tipler += tip
            g.tipler = arm_sirala(g.tipler, g.mutfak)
    for Y in ys:
        ps = sorted({p for (_, p) in Y.gruplar})
        mutfak = {p for (_, p), g in Y.gruplar.items() if g.mutfak}

        def ky(p):
            k = kol.get(p, {})
            return (1 if p in mutfak else 0, -(k.get('y', 0)) if p not in mutfak else -kno(p), kno(p))
        Y.kolonlar = sorted(ps, key=ky)
        Y._xort = sum(kol.get(p, {}).get('x', 0) for p in ps) / max(1, len(ps))
    ys.sort(key=lambda Y: Y._xort)
    return ys


def kat_sayisi(m):
    return len(m['proje'].get('kat_adlari') or ['ZEMİN KAT'])


def kolon_katlari(Y, p):
    return sorted(k for (k, q) in Y.gruplar if q == p)


def kolon_birlestir(m, tol=30.0):
    """planda aynı düşey hatta (≤ tol cm) duran, katları çakışmayan kolonları tek kolonda birleştirir (küçük numara
    kalır). Plan üreticisi bir ıslak hacim yığınının kolonunu katlarda farklı numaralandırdığında kullanılır.
    Dönüş: (yeni model, {eski: yeni})"""
    import copy
    m = copy.deepcopy(m)
    ks = sorted(m.get('kolonlar', []), key=lambda k: kno(k['no']))
    es = {}
    tut = []
    for k in ks:
        hedef = None
        for t in tut:
            if math.hypot(t['x'] - k['x'], t['y'] - k['y']) <= tol and not (set(t['katlar']) & set(k['katlar'])):
                hedef = t
                break
        if hedef is None:
            tut.append(k)
            continue
        es[k['no']] = hedef['no']
        hedef['katlar'] = sorted(set(hedef['katlar']) | set(k['katlar']))
        n = max(len(hedef.get('sb_kat', [])), len(k.get('sb_kat', [])))
        a = (hedef.get('sb_kat', []) + [0] * n)[:n]
        b = (k.get('sb_kat', []) + [0] * n)[:n]
        hedef['sb_kat'] = [x + y for x, y in zip(a, b)]
        hedef['sb_toplam'] = sum(hedef['sb_kat'])
        hedef.setdefault('mahal', {}).update(k.get('mahal', {}))
    m['kolonlar'] = tut
    for d in m['daireler']:
        for h in d.get('islak_hacimler', []):
            if h.get('kolon') in es:
                h['kolon'] = es[h['kolon']]
    m['_birlesen'] = es
    return m, es
