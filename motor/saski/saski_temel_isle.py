"""SASKİ altyapısını kullanıcının TEMEL planına işler.
- Blok başına (A,B,C,D): SASKİ'deki rögarlar, hatlar, R no / 60x60 / Ø150 L yazıları, kot blokları -> temel koordinatı
  (ölçek 4 = SASKİ birimi→cm, öteleme: BLOK GİRİŞ yazısı + çizgi korelasyonu ince ayarı kayd.json)
- Sol tarafa: SASKİ vaziyet altyapı planı (tüm parsel, ana kanal Ø200, bacalar, mesafeler) ×4, cm
- Sağ tarafa: SASKİ kanal durum belgesi / abone bağlantı detayı / sayaç detayları ×4
Katmanlar ROTAS-SASKI-*; kullanıcının temel çizimi aynen kalır."""
import sys, re, json, ezdxf
from ezdxf import bbox, xref
from ezdxf.math import Matrix44
SK, TM, KD, OUT = sys.argv[1:5]
sk = ezdxf.readfile(SK); tm = ezdxf.readfile(TM)
kd = json.load(open(KD))

def temizle(doc):
    """dinamik blok gösterim verisi / uzantı sözlükleri kopyada bozuk sözlük üretiyor -> kaynaktan atılır"""
    n = 0
    for blk in doc.blocks:
        for e in [blk.block_record] + list(blk):
            if e.has_extension_dict:
                e.discard_extension_dict(); n += 1
    for e in doc.modelspace():
        if e.has_extension_dict:
            e.discard_extension_dict(); n += 1
    return n
print('uzantı sözlüğü atıldı', temizle(sk), temizle(tm))

def giris(doc):
    out = {}
    for e in doc.modelspace().query('TEXT MTEXT'):
        t = e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()
        m = re.search(r'([ABCD])\s*BLOK\s*G[İI]R[İI][ŞS]', t.replace('%%U', ''))
        if m: out[m.group(1)] = (e.dxf.insert.x, e.dxf.insert.y)
    return out
gs, gt = giris(sk), giris(tm)
hedef = ezdxf.new('R2018', setup=True)
hedef.header['$INSUNITS'] = 5
xref.load_modelspace(tm, hedef)
msp = hedef.modelspace()
LAY = {'ROTAS-SASKI-HAT': 2, 'ROTAS-SASKI-ROGAR': 5, 'ROTAS-SASKI-YAZI': 7, 'ROTAS-SASKI-KOT': 8,
       'ROTAS-SASKI-VAZIYET': 8, 'ROTAS-SASKI-VAZIYET-ALTYAPI': 2, 'ROTAS-SASKI-DETAY': 8, 'ROTAS-SASKI-BASLIK': 7}
for n, c in LAY.items():
    if n not in hedef.layers:
        hedef.layers.add(n, color=c)
ALTY = ('SIVA', 'MAHALYAZI', 'ubg_kot')

def katman(e):
    l = e.dxf.layer
    if l == 'SIVA':
        if e.dxftype() == 'TEXT': return 'ROTAS-SASKI-KOT'
        return 'ROTAS-SASKI-HAT' if e.dxf.color == 2 else 'ROTAS-SASKI-ROGAR'
    if l == 'MAHALYAZI': return 'ROTAS-SASKI-YAZI'
    if l == 'ubg_kot': return 'ROTAS-SASKI-KOT'
    return None

def yukle(filt, M, katman_f, renk_koru=False):
    n0 = len(msp)
    xref.load_modelspace(sk, hedef, filter_fn=filt)
    yeni = list(msp)[n0:]
    for e in yeni:
        try:
            lay = katman_f(e)
            e.transform(M)
            if lay:
                e.dxf.layer = lay
                if not renk_koru:
                    e.dxf.color = 256
        except Exception:
            msp.delete_entity(e)
    return len(yeni)

def merkez(e):
    try:
        b = bbox.extents([e], fast=True)
        return b if b.has_data else None
    except Exception:
        return None

BOL = {'A': (17250, 2770, 17800, 3700), 'B': (17280, 3690, 18225, 4140),
       'C': (18225, 3580, 18960, 4140), 'D': (19150, 3090, 19760, 4140)}
for b, (x0, y0, x1, y1) in BOL.items():
    def f(e, x0=x0, y0=y0, x1=x1, y1=y1):
        if e.dxf.layer not in ALTY or e.dxftype() == 'HATCH': return False
        bb = merkez(e)
        return bb is not None and x0 < bb.center.x < x1 and y0 < bb.center.y < y1
    S, T = gs[b], gt[b]
    T = (T[0] + kd[b][0], T[1] + kd[b][1])
    M = Matrix44.translate(-S[0], -S[1], 0) @ Matrix44.scale(4.0) @ Matrix44.translate(T[0], T[1], 0)
    print(b, 'altyapı nesnesi', yukle(f, M, katman))

# --- kullanıcı temel planlarının sınırı
tb = bbox.extents(tm.modelspace(), fast=True)
# --- SASKİ vaziyet altyapı planı (tüm parsel) ×4, temel planlarının soluna
VX0, VY0, VX1, VY1 = 16550, 2250, 19900, 4750
ox = tb.extmin.x - 1500 - (VX1 - VX0) * 4
oy = (tb.extmin.y + tb.extmax.y) / 2 - (VY1 - VY0) * 2
Mv = Matrix44.translate(-VX0, -VY0, 0) @ Matrix44.scale(4.0) @ Matrix44.translate(ox, oy, 0)
def fv(e):
    bb = merkez(e)
    return bb is not None and VX0 < bb.center.x < VX1 and VY0 < bb.center.y < VY1 and bb.size.x < (VX1 - VX0)
def kv(e):
    return 'ROTAS-SASKI-VAZIYET-ALTYAPI' if (e.dxf.layer in ALTY and not (e.dxf.layer == 'SIVA' and e.dxf.color == 8)) else 'ROTAS-SASKI-VAZIYET'
print('vaziyet', yukle(fv, Mv, kv, renk_koru=True))
msp.add_text('SASKİ ALTYAPI VAZİYET PLANI (SASKİ onay dosyasından, 1/1 cm)', height=60,
             dxfattribs={'layer': 'ROTAS-SASKI-BASLIK'}).set_placement((ox, oy - 250))
# --- SASKİ kanal durum belgesi + detaylar, temel planlarının sağına
DX0, DY0, DX1, DY1 = 44700, 2250, 47400, 4500
dx = tb.extmax.x + 1500
dy = (tb.extmin.y + tb.extmax.y) / 2 - (DY1 - DY0) * 2
Md = Matrix44.translate(-DX0, -DY0, 0) @ Matrix44.scale(4.0) @ Matrix44.translate(dx, dy, 0)
def fd(e):
    bb = merkez(e)
    return bb is not None and DX0 < bb.center.x < DX1 and DY0 < bb.center.y < DY1 and bb.size.x < (DX1 - DX0)
print('detay', yukle(fd, Md, lambda e: 'ROTAS-SASKI-DETAY', renk_koru=True))
msp.add_text('SASKİ KANAL DURUM BELGESİ VE BAĞLANTI DETAYLARI', height=60,
             dxfattribs={'layer': 'ROTAS-SASKI-BASLIK'}).set_placement((dx, dy - 250))
# --- notlar (temel planlarının üstüne)
notlar = ['SASKİ ALTYAPI NOTLARI',
          '1- Rögarlar, hatlar, çap ve boylar SASKİ onaylı altyapı projesinden işlenmiştir (Ø150 koruge, rögar 60x60).',
          '2- Abone çıkış bağlantısının yapılacağı taralı parsel bacasının bağlantı kotu mevcut yol kotunun 80 cm altındadır (SASKİ kanal durum belgesi, Adapazarı Korucuk Mah. 3346 ada 13 parsel, tasdik 13.07.2026).',
          '3- Ana kanal Ø200 (12,00 m yol); kanal bacaları 11381/37 ve 11381/38. Kanal durum belgesinde "baca mevcut değil" notu vardır — parsel bacası SASKİ ile netleştirilecektir.',
          '4- Parsel bacası yeri değişikliği, deplase veya ilave parsel bacası talebi SASKİ tarafından ayrıca ücretlendirilecektir.',
          '5- Kanal durum belgesi proje aşamasında getirilecektir.',
          '6- Bodrum ıslak hacimleri ve sığınak giderleri pompa rögarı üzerinden bağlanacaktır.']
y = tb.extmax.y + 900
for i, t in enumerate(notlar):
    msp.add_text(t, height=40 if i == 0 else 28, dxfattribs={'layer': 'ROTAS-SASKI-BASLIK'}).set_placement((tb.extmin.x, y - i * 55))
hedef.saveas(OUT)
print('yazıldı', OUT, len(msp))
