# -*- coding: utf-8 -*-
"""sihhi2/pafta.py — SIHHİ TESİSAT PROJESİ 1. sıra paftalarını tek şeritte birleştirir (ornekler/ORNEK_DUZEN.md).

Sıra (soldan sağa, hepsi aynı 2900 cm şeritte, sol alt y0):
    ANTET (958 × 1428, şerit sol altında; "kapak") → YERLEŞİM PLANI 1/250 (1682) → TEMEL PLANI 1/50 (2471)
    → ZEMİN / 1. / 2. KAT PLANLARI 1/50 (2065 / 2039 / 2039; plan.py çıktısı lejant/çatı paftasıyla birlikte)
    → AÇILIMLI KOLON ŞEMASI (7418) → WC HAVALANDIRMA İZOMETRİSİ + SIHHİ DETAYLAR (2065)
Pafta ölçüleri new_block.dxf'ten (kutuphane/arastirma/SIHHI_ALTIN_REFERANS.md §1). Başlıklar
"…ÖLÇEK: 1 / 50" h 40, pafta solu + 538, alt çerçeveden 39 yukarı.

API
    birlestir(plan_dxf, sema_dxf, temel_dxf, cikti, bilgi=None, vaziyet=None, wc_girdi=None, x0=247352, y0=-444050)
        Girdi DXF'leri yoksa (ya da None) o pafta yer tutucu çerçeveyle çizilir. Girdi DXF'inde ROTAS-PAFTA
        katmanında 2900 yüksekliğinde dikdörtgen(ler) varsa pafta sınırı olarak onlar alınır (içerik ölçeksiz taşınır);
        yoksa içerik referans genişliğindeki paftanın ortasına konur. Dönüş: dict(paftalar=[...], uyarilar=[...]).

Komut satırı:
    python3 pafta.py [--plan P] [--sema S] [--temel T] [--vaziyet new_block.dxf] [--cikti C]
"""
import os
import sys
import time

import ezdxf
from ezdxf import bbox as _bbox
from ezdxf.addons import Importer
from ezdxf.math import Matrix44

BURASI = os.path.dirname(os.path.abspath(__file__))
DEPO = os.path.abspath(os.path.join(BURASI, '..', '..'))
sys.path.insert(0, BURASI)
import antet as A        # noqa: E402
import detay as D        # noqa: E402

SERIT_H = A.SERIT_H
# referans pafta genişlikleri (cm) — SIHHI_ALTIN_REFERANS §1
W_ANTET = 1008.0          # 247352 … 248360 (antet 958 + 50 boşluk)
W_YERLESIM = 1682.0       # 248360 … 250042
W_TEMEL = 2471.0          # 250042 … 252513
W_KAT = {'ZEMİN KAT': 2065.0, '1. KAT': 2039.0, '2. KAT': 2039.0}
W_CATI = 2058.0
W_SEMA = 7418.0           # 260714 … 268132
W_DETAY = 2065.0          # 268132 … 270197
BOS_PAFTA_TOL = 5.0

GIRDI_DIZIN = os.path.join(DEPO, 'proje', 'denemeler', 'sihhi2')
VARSAYILAN = dict(plan=os.path.join(GIRDI_DIZIN, 'NB_SIHHI_KAT_PLANLARI.dxf'),
                  sema=os.path.join(GIRDI_DIZIN, 'NB_SIHHI_SEMA.dxf'),
                  temel=os.path.join(GIRDI_DIZIN, 'NB_SIHHI_TEMEL.dxf'),
                  cikti=os.path.join(GIRDI_DIZIN, 'NB_SIHHI_PAFTA_DENEME.dxf'))

# new_block yerleşim paftası (kullanıcının kendi vaziyet + kesit çizimi); bilgi kutuları/başlıklar/kuzey oku bizden
NB_YERLESIM = dict(bolge=(248360.0, -444050.0, 250042.0, -441150.0), orijin=(248360.0, -444050.0),
                   haric=[(248440.0, -442330.0, 249760.0, -442080.0),     # "… 'ne AİT / İNŞAAT PROJESİ / VAZİYET PLANI"
                          (248440.0, -442990.0, 248930.0, -442190.0),     # bilgi kutuları + alan hesabı
                          (248600.0, -444020.0, 249520.0, -443890.0),     # "YERLEŞİM PLANI ÖLÇEK: 1 / 250"
                          (249760.0, -442800.0, 250000.0, -442540.0)])    # kuzey oku + ölçek


def log(*a):
    print('[pafta]', *a, flush=True)


# ============================================================================= belge
def belge():
    doc = ezdxf.new('R2018', setup=True)
    doc.header['$INSUNITS'] = 5
    doc.header['$MEASUREMENT'] = 1
    doc.header['$LTSCALE'] = 1.0
    A.hazirla(doc)
    D.katmanlar(doc)
    return doc


def cerceve(msp, x0, y0, w, h=SERIT_H, kat='ROTAS-PAFTA'):
    return msp.add_lwpolyline([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], close=True,
                              dxfattribs={'layer': kat})


def yer_tutucu(msp, x0, y0, w, baslik, aciklama):
    c = A.Ciz(msp, x0, y0, 'ROTAS-YER-TUTUCU', 'ROTAS-YER-TUTUCU')
    c.rect(150, 300, w - 150, SERIT_H - 250)
    c.text(aciklama[0], w / 2, SERIT_H / 2 + 40, 30, 'MC')
    for i, s in enumerate(aciklama[1:]):
        c.text(s, w / 2, SERIT_H / 2 - 20 - i * 40, 20, 'MC')
    if baslik:
        A.pafta_basligi(A.Ciz(msp, x0, y0, 'ROTAS-PAFTA', 'ROTAS-PAFTA-YAZI'), 0, 0, baslik)


# ============================================================================= girdi DXF içe aktarma
def _pafta_cerceveleri(msp):
    """ROTAS-PAFTA katmanındaki ~2900 yüksekliğinde dikdörtgenler → [(x0, y0, x1, y1)] (x'e göre sıralı)."""
    out = []
    for e in msp.query('LWPOLYLINE'):
        if not e.dxf.layer.upper().startswith('ROTAS-PAFTA') or e.dxf.layer.upper().endswith('YAZI'):
            continue
        ps = list(e.get_points('xy'))
        if len(ps) < 4:
            continue
        xs, ys = [p[0] for p in ps], [p[1] for p in ps]
        if abs((max(ys) - min(ys)) - SERIT_H) <= BOS_PAFTA_TOL and max(xs) - min(xs) > 500:
            out.append((min(xs), min(ys), max(xs), max(ys)))
    return sorted(set(out))


def _basliklar(msp):
    out = []
    for e in msp.query('TEXT MTEXT'):
        s = e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()
        if 'ÖLÇEK' in s.upper() or 'OLCEK' in s.upper():
            out.append(s)
    return out


def ice_aktar(doc, kaynak, x_imlec, y0, w_ref, baslik=None):
    """kaynak DXF'i doc'a taşıyarak alır. Dönüş: dict(x1=paftanın sağ kenarı, paftalar=[(ad, x0, x1)], n, uyari)."""
    t0 = time.time()
    src = ezdxf.readfile(kaynak)
    smsp = src.modelspace()
    msp = doc.modelspace()
    cer = _pafta_cerceveleri(smsp)
    uyari = []
    if cer:
        sx0, sy0 = min(c[0] for c in cer), min(c[1] for c in cer)
        dx, dy = x_imlec - sx0, y0 - sy0
        x1 = x_imlec + (max(c[2] for c in cer) - sx0)
        cer_yeni = None
    else:
        ext = _bbox.extents(smsp, fast=True)
        if not ext.has_data:
            return None
        ew, eh = ext.extmax.x - ext.extmin.x, ext.extmax.y - ext.extmin.y
        w = max(w_ref, ew + 200.0)
        if eh > SERIT_H - 200:
            uyari.append('%s: içerik yüksekliği %.0f > şerit %.0f (ölçek değiştirilmedi)' % (os.path.basename(kaynak), eh, SERIT_H))
        dx = x_imlec + (w - ew) / 2 - ext.extmin.x
        dy = y0 + max(120.0, (SERIT_H - eh) / 2) - ext.extmin.y
        x1 = x_imlec + w
        cer_yeni = (x_imlec, w)
    # ROTAS- kütüphane blokları hedefte varsa yeniden adlandırılmadan ortak kullanılır (lejant ADET sayımı için)
    imp = Importer(src, doc)
    for b in src.blocks:
        n = b.name
        if n.startswith('ROTAS-') and n in doc.blocks:
            imp.import_block(n, rename=False)
    n0 = len(msp)
    imp.import_entities(list(smsp), target_layout=msp)
    imp.import_tables('layers')
    imp.finalize()
    yeni = list(msp)[n0:]
    M = Matrix44.translate(dx, dy, 0)
    for e in yeni:
        try:
            e.transform(M)
        except Exception:
            pass
    if cer_yeni:
        cerceve(msp, cer_yeni[0], y0, cer_yeni[1])
    hazir_baslik = _basliklar(smsp)
    if baslik and not any(baslik.split('.')[0].strip() in s for s in hazir_baslik):
        A.pafta_basligi(A.Ciz(msp, x_imlec, y0, 'ROTAS-PAFTA', 'ROTAS-PAFTA-YAZI'), 0, 0, baslik)
    paftalar = [(None, c[0] + dx, c[2] + dx) for c in cer] if cer else [(None, x_imlec, x1)]
    log('%s: %d varlık, dx %.0f dy %.0f (%.1f s)' % (os.path.basename(kaynak), len(yeni), dx, dy, time.time() - t0))
    return dict(x1=x1, paftalar=paftalar, n=len(yeni), uyari=uyari, basliklar=hazir_baslik)


def _var(p):
    return bool(p) and os.path.exists(p)


# ============================================================================= birleştir
# new_block WC havalandırma şaftları (kullanıcının izometrisi): D3-5-8 240 m³/h, D1-2-4-6-7-9 480 m³/h
NB_SAFT_GRUPLARI = [['D3', 'D5', 'D8'], ['D1', 'D2', 'D4', 'D6', 'D7', 'D9']]


def birlestir(plan_dxf, sema_dxf, temel_dxf, cikti, bilgi=None, vaziyet=None, wc_girdi=None,
              x0=247352.0, y0=-444050.0, saft_gruplari=NB_SAFT_GRUPLARI):
    t0 = time.time()
    doc = belge()
    msp = doc.modelspace()
    P, U = [], []          # paftalar: (ad, x0, x1, kaynak), uyarılar
    x = x0
    # 1) ANTET (kapak) — şeridin sol altında
    A.antet_ciz(msp, x, y0, bilgi, (bilgi or {}).get('proje_turu', 'SIHHİ TESİSAT PROJESİ'))
    msp.add_line((x + W_ANTET, y0), (x + W_ANTET, y0 + SERIT_H), dxfattribs={'layer': 'ROTAS-PAFTA'})   # ayraç
    P.append(('ANTET', x, x + W_ANTET, 'antet.py'))
    x += W_ANTET
    # 2) YERLEŞİM PLANI 1/250
    vz = None
    if vaziyet and _var(vaziyet if isinstance(vaziyet, str) else vaziyet.get('dxf')):
        vz = dict(NB_YERLESIM, dxf=vaziyet) if isinstance(vaziyet, str) else vaziyet
    cerceve(msp, x, y0, W_YERLESIM)
    R = A.yerlesim_ciz(msp, x, y0, W_YERLESIM, SERIT_H, bilgi, vz)
    P.append(('YERLEŞİM PLANI', x, x + W_YERLESIM, 'antet.py' + (' + vaziyet altlığı %d' % R['altlik_varlik'] if R['altlik_varlik'] else ' (yer tutucu)')))
    x += W_YERLESIM
    # 3) TEMEL PLANI 1/50
    if _var(temel_dxf):
        r = ice_aktar(doc, temel_dxf, x, y0, W_TEMEL, 'TEMEL PLANI.........ÖLÇEK: 1 / 50')
        U += r['uyari']
        P.append(('TEMEL PLANI', x, r['x1'], os.path.basename(temel_dxf)))
        x = r['x1']
    else:
        cerceve(msp, x, y0, W_TEMEL)
        yer_tutucu(msp, x, y0, W_TEMEL, 'TEMEL PLANI.........ÖLÇEK: 1 / 50',
                   ['TEMEL PLANI — girdi yok', 'NB_SIHHI_TEMEL.dxf bekleniyor (kolon dipleri P1..Pn, rögarlar R1..Rn + PB,',
                    'Ø/SB/% eğim etiketleri; rögarlar bina dışında bir cephe boyunca, 70x70 h:-70cm)'])
        P.append(('TEMEL PLANI', x, x + W_TEMEL, 'yer tutucu'))
        U.append('temel planı girdisi yok: yer tutucu')
        x += W_TEMEL
    # 4) KAT PLANLARI (her kat ayrı pafta)
    if _var(plan_dxf):
        r = ice_aktar(doc, plan_dxf, x, y0, sum(W_KAT.values()))
        U += r['uyari']
        for i, (_, a, b) in enumerate(r['paftalar']):
            ad = (list(W_KAT) + ['ÇATI / LEJANT'] + ['PAFTA %d' % (i + 1)] * 9)[i]
            P.append((ad, a, b, os.path.basename(plan_dxf)))
        x = r['x1']
    else:
        for ad, w in W_KAT.items():
            cerceve(msp, x, y0, w)
            yer_tutucu(msp, x, y0, w, '%s PLANI.........ÖLÇEK: 1 / 50' % ad,
                       ['%s PLANI — girdi yok' % ad, 'NB_SIHHI_KAT_PLANLARI.dxf bekleniyor (plan.py)'])
            P.append((ad + ' PLANI', x, x + w, 'yer tutucu'))
            x += w
        U.append('kat planı girdisi yok: yer tutucu')
    # 5) AÇILIMLI KOLON ŞEMASI
    if _var(sema_dxf):
        r = ice_aktar(doc, sema_dxf, x, y0, W_SEMA)
        U += r['uyari']
        P.append(('AÇILIMLI KOLON ŞEMASI', x, r['x1'], os.path.basename(sema_dxf)))
        x = r['x1']
    else:
        cerceve(msp, x, y0, W_SEMA)
        yer_tutucu(msp, x, y0, W_SEMA, 'AÇILIMLI KOLON ŞEMASI',
                   ['AÇILIMLI KOLON ŞEMASI — girdi yok', 'NB_SIHHI_SEMA.dxf bekleniyor (sema.py): depo sol üst, sayaç grubu zemin bandı solu,',
                    'D1..Dn daire blokları yan yana, kolon etiketleri en üstte; altta rögar şeması, sağda yağmur şeması'])
        P.append(('AÇILIMLI KOLON ŞEMASI', x, x + W_SEMA, 'yer tutucu'))
        U.append('kolon şeması girdisi yok: yer tutucu')
        x += W_SEMA
    # 6) WC HAVALANDIRMA İZOMETRİSİ + SIHHİ DETAYLAR (lejant ADET'i bütün belgeden sayılır → en sonda)
    cerceve(msp, x, y0, W_DETAY)
    R = D.detay_paftasi(msp, x, y0, W_DETAY, SERIT_H, wc_girdi, saft_gruplari=saft_gruplari)
    P.append(('WC HAV. İZOMETRİSİ + SIHHİ DETAYLAR', x, x + W_DETAY, 'detay.py'))
    if not R.get('wc'):
        U.append('WC havalandırma girdisi yok: izometri çizilmedi')
    x += W_DETAY
    # temizlik: kullanılmayan MTY adlı tablo kayıtları (içe aktarılan altlıktan gelebilir)
    _mty_temizle(doc)
    doc.audit()
    os.makedirs(os.path.dirname(os.path.abspath(cikti)), exist_ok=True)
    doc.saveas(cikti)
    log('%s: %d pafta, şerit %.0f × %.0f (%.1f s)' % (cikti, len(P), x - x0, SERIT_H, time.time() - t0))
    return dict(paftalar=P, uyarilar=U, adet=R['detay']['adet'], wc=R.get('wc'), genislik=x - x0)


def _mty_temizle(doc):
    kullanilan_stil = {e.dxf.get('style', '') for e in doc.entitydb.values() if e.dxftype() in ('TEXT', 'MTEXT', 'ATTRIB', 'ATTDEF')}
    for st in list(doc.styles):
        if 'MTY' in st.dxf.name.upper() and st.dxf.name not in kullanilan_stil:
            try:
                doc.styles.remove(st.dxf.name)
            except Exception:
                pass
    kullanilan_kat = {e.dxf.get('layer', '') for e in doc.entitydb.values() if hasattr(e.dxf, 'layer')}
    for ly in list(doc.layers):
        n = ly.dxf.name
        if n not in ('0', 'Defpoints') and not n.startswith('ROTAS-') and n not in kullanilan_kat:
            try:
                doc.layers.remove(n)
            except Exception:
                pass


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', default=VARSAYILAN['plan'])
    ap.add_argument('--sema', default=VARSAYILAN['sema'])
    ap.add_argument('--temel', default=VARSAYILAN['temel'])
    ap.add_argument('--vaziyet', default=None, help='kullanıcının mimari DXF\'i (new_block.dxf; yerleşim paftası yerinde alınır)')
    ap.add_argument('--wc', default=None, help='wc_havalandirma girdi JSON')
    ap.add_argument('--cikti', default=VARSAYILAN['cikti'])
    ap.add_argument('--saft', default=None,
                    help='WC havalandırma şaftları, daire grupları: "D3,D5,D8;D1,D2,D4,D6,D7,D9" (varsayılan new_block)')
    a = ap.parse_args()
    sg = [g.split(',') for g in a.saft.split(';')] if a.saft else NB_SAFT_GRUPLARI
    R = birlestir(a.plan, a.sema, a.temel, a.cikti, vaziyet=a.vaziyet, wc_girdi=a.wc, saft_gruplari=sg)
    for p in R['paftalar']:
        print('  %-36s x %.0f … %.0f (%.0f)  %s' % (p[0], p[1], p[2], p[2] - p[1], p[3]))
    for u in R['uyarilar']:
        print('  UYARI:', u)
    print('  lejant adet:', {k: v for k, v in R['adet'].items() if v})
