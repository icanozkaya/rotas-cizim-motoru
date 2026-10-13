# -*- coding: utf-8 -*-
"""VOYAP TÜM MEKANİK: yangın (rev) + sıhhi + ısıtma + havalandırma tek dosyada.
EK  = yalnız eklenen çizimler (kullanıcının koordinatında)
TAM = kullanıcının tüm dosyası + ekler (eski bodrum, eski kısmi MTY şemaları ve termosifon yazıları yerine yenileri)"""
import sys, time, pickle, math
import ezdxf
sys.path.insert(0, '/home/claude/voyap'); sys.path.insert(0, '/home/claude/voyap/tes')
t0 = time.time()
from lib import *
from ezdxf import bbox as _bb
sdoc = import_mty('/tmp/claude-0/vy/sih.dxf')
define_blocks(); define_asel_blocks()
import tlib
tlib.setup(sdoc)
# ------------------------------------------------------------------ YANGIN
import plans
plans.bodrum_mimari()
AL = plans.build_plans()
plans.kopruler()
pickle.dump(AL, open('/tmp/claude-0/vy/all_lines.pkl', 'wb'))
import sema; sema.build()
print('yangın', round(time.time() - t0), 's')
# ------------------------------------------------------------------ TESİSAT
from veri import *
import sihhi, isitma, alt, sema_tes, termo, sema_sihhi
from tlib import T as _T


def guncel_bodrum(row):
    M = pickle.load(open('/tmp/claude-0/vy/mimT.pkl', 'rb'))
    dx, dy = ROW[row]
    for r in M:
        if r[0] == 'L':
            a, b = r[2][0], r[2][1]
            if 247900 < a[0] < 250300: L((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy), "MIM-GUNCEL-BODRUM")
        elif r[0] == 'P':
            q = r[2]
            if 247900 < q[0][0] < 250300: PL([(p[0] + dx, p[1] + dy) for p in q], "MIM-GUNCEL-BODRUM")
        elif r[0] == 'C':
            c = r[2]
            if 247900 < c[0] < 250300: C((c[0] + dx, c[1] + dy), c[2], "MIM-GUNCEL-BODRUM")
        elif r[0] == 'T':
            (x, y), s, hh = r[2][0][:2], r[2][1], r[2][2]
            if 247900 < x < 250300 and 'lift' not in s and 'BODRUM' not in s and 'KOLON' not in s:
                s2 = s.split(';')[-1].strip('}') if ';' in s else s
                T(x + dx, y + dy, s2, min(hh, 30), "MIM-GUNCEL-BODRUM")


for row in ('S', 'H'):
    guncel_bodrum(row)
for kat in (2, 3):
    sihhi.draw_ofis_sihhi(kat); print('sıhhi kat', kat, round(time.time() - t0))
    isitma.draw_ofis_isitma(kat); print('ısıtma kat', kat, round(time.time() - t0))
alt.zemin_sihhi(); alt.zemin_isitma(); print('zemin', round(time.time() - t0))
alt.bodrum_sihhi(); alt.bodrum_isitma(); print('bodrum', round(time.time() - t0))
pickle.dump({k: v for k, v in alt.OUTA.items() if k in ('zemin', 'bodrum')}, open('/tmp/claude-0/vy/outa.pkl', 'wb'))
tlib.reset_place()
# şemalar
sema_sihhi.sema(); sema_tes.isitma_sema(); sema_tes.kazan_sema()
# lejant/not/tablo alanı çerçevesi (eski V sırası yeri; havalandırma kaldırıldı)
for e in sdoc.modelspace().query('LINE[layer=="ANTED"]'):
    a, b = e.dxf.start, e.dxf.end
    if -458200 < a.y < -450600 and -458200 < b.y < -450600:
        L((a.x, a.y - 10322), (b.x, b.y - 10322), "ANTED")
_T(256000, -468306, "LEJANT / NOTLAR / HESAP ÖZETLERİ / EKİPMAN LİSTESİ", 100, "MKDU0", TA.BOTTOM_CENTER)
# lejant / not / tablolar (S sırası altı, eski V sırası yeri)
x = 263000
y = sema_tes.lejant(x, -461100, 'S')
y = sema_tes.lejant(x, y - 120, 'H')
x2 = 266500
y2 = sema_tes.notlar(x2, -461100, "SIHHİ TESİSAT NOTLARI", sema_tes.NOT_S, 9.0)
y2 = sema_tes.notlar(x2, y2 - 120, "ISITMA TESİSATI NOTLARI", sema_tes.NOT_H, 9.0)
y3 = sema_tes.ozet_tablolar(272500 - 1400, -461100) if False else None
sema_tes.ozet_tablolar(266500, y2 - 150)
sema_sihhi.ekipman_listesi(271200, -461100)
pickle.dump(dict(OUT=sihhi.OUT, OUTI={k: v for k, v in isitma.OUTI.items() if k[0] != 'ana'}, OUTA={k: v for k, v in alt.OUTA.items() if k != 'bodrum_isi'}),
            open('/tmp/claude-0/vy/tes_out.pkl', 'wb')) if False else None
import copy as _cp


def scott(d, wipe_sil=True):
    """tüm katman adları SCOTT- önekiyle (0 ve Defpoints hariç); blok içleri dahil.
    Ayrıca: adlı bloklarda yanlış 'anonim' bayrağı temizlenir (AutoCAD bu INSERT'leri göstermiyordu),
    0 katmanındaki wipeout (görünmeyen maske) nesneleri silinir."""
    for b in d.blocks:
        if not b.name.startswith('*') and b.block.dxf.get('flags', 0) & 1:
            b.block.dxf.flags = b.block.dxf.flags & ~1
    if wipe_sil:
        for lo in d.layouts:
            for e in list(lo.query('WIPEOUT')):
                lo.delete_entity(e)
    ren = {}
    for l in list(d.layers):
        n = l.dxf.name
        if n in ('0', 'Defpoints') or n.upper().startswith('SCOTT'): continue
        ren[n] = 'SCOTT-' + n
    for n, nn in ren.items():
        if nn not in d.layers:
            o = d.layers.get(n)
            nl = d.layers.add(nn)
            for a in ('color', 'linetype', 'lineweight', 'true_color', 'plot'):
                if o.dxf.hasattr(a): nl.dxf.set(a, o.dxf.get(a))
    def fix(e):
        ly = e.dxf.get('layer', '0')
        if ly in ren: e.dxf.layer = ren[ly]
        if e.dxftype() == 'INSERT':
            for a in e.attribs: fix(a)
    for lo in d.layouts:
        for e in lo: fix(e)
    for b in d.blocks:
        for e in b: fix(e)
    for n in ren:
        try: d.layers.remove(n)
        except Exception: pass




def _ust(s1, s2, tol=1.5):
    (a, b), (c, d) = s1, s2
    if abs(a[1] - b[1]) < 0.01 and abs(c[1] - d[1]) < 0.01 and abs(a[1] - c[1]) < tol:
        return min(max(a[0], b[0]), max(c[0], d[0])) - max(min(a[0], b[0]), min(c[0], d[0])) > 2.0
    if abs(a[0] - b[0]) < 0.01 and abs(c[0] - d[0]) < 0.01 and abs(a[0] - c[0]) < tol:
        return min(max(a[1], b[1]), max(c[1], d[1])) - max(min(a[1], b[1]), min(c[1], d[1])) > 2.0
    return False


def ayir_katman(lay, step=5.0, it=200):
    """aynı katmanda üst üste binen boru parçalarını yanal kaydır (uç noktalar korunur, gerekirse dik bağlantı)"""
    E = [e for e in msp.query('LWPOLYLINE') if e.dxf.layer == lay and not e.closed]
    P = {i: [tuple(q[:2]) for q in e.get_points()] for i, e in enumerate(E)}
    nmove = 0
    for _ in range(it):
        segs = [(i, j, (p[j], p[j + 1])) for i, p in P.items() for j in range(len(p) - 1) if p[j] != p[j + 1]]
        moved = False
        for i, j, sg in segs:
            conf = [o for o in segs if o[0] != i and _ust(sg, o[2])]
            if not conf: continue
            a, b = sg
            hor = abs(a[1] - b[1]) < 0.01
            if not hor and abs(a[0] - b[0]) > 0.01: continue
            best = None
            for dd in (step, -step, 2 * step, -2 * step, 3 * step, -3 * step):
                na = (a[0], a[1] + dd) if hor else (a[0] + dd, a[1]); nb = (b[0], b[1] + dd) if hor else (b[0] + dd, b[1])
                n = sum(1 for o in segs if o[0] != i and _ust((na, nb), o[2]))
                if best is None or n < best[0]: best = (n, na, nb)
                if n == 0: break
            if best[0] >= len(conf): continue
            p = list(P[i])
            new = p[:j] + ([p[j]] if j == 0 else []) + [best[1], best[2]] + ([p[j + 1]] if j + 1 == len(p) - 1 else []) + p[j + 2:]
            if j > 0: new = p[:j] + [best[1], best[2]] + ([p[j + 1]] if j + 1 == len(p) - 1 else []) + p[j + 2:]
            P[i] = new; moved = True; nmove += 1
            break
        if not moved: break
    for i, e in enumerate(E):
        if len(P[i]) != len(list(e.get_points())) or any(abs(x[0] - y[0]) > 0.01 or abs(x[1] - y[1]) > 0.01 for x, y in zip(P[i], [q[:2] for q in e.get_points()])):
            e.set_points(P[i], format='xy')
    print('  üst üste ayırma', lay, nmove)


for _l in ("MTY-PEX-BORU",):
    ayir_katman(_l)
scott(doc)
doc.saveas('/tmp/claude-0/vy/MEKANIK_EK.dxf')
print('EK ok', round(time.time() - t0), 's')

# ------------------------------------------------------------------ TAM
cache = _bb.Cache()
HX = ROW['H'][0] - ROW['S'][0]
EXC = [  # (x0, x1, y0, y1): bu pencerede ANTED ve pafta başlığı dışı kullanıcı varlıkları alınmaz
    (250242, 252393, -447827, -440327),           # S eski bodrum
    (258701, 276712, -447827, -440327),           # S eski kısmi MTY şeması
    (280585, 282737, -447827, -440327),           # H eski bodrum
    (289044, 315152, -447827, -440327),           # H eski kısmi MTY şeması
    (248039, 250190, -458149, -450649),           # Y eski bodrum
]
TERMO = termo.tara()
sec = []
nx = 0
for e in sdoc.modelspace():
    lay = e.dxf.get('layer', '0')
    if e.dxftype() in ('VIEWPORT', 'OLE2FRAME', 'IMAGE'): continue
    try:
        b = _bb.extents([e], fast=True, cache=cache)
    except Exception:
        continue
    if not b.has_data: continue
    cx, cy = (b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2
    # yangın sırası eski sprinkler
    if lay.upper().startswith('MTY-SPRINKLER') and -458200 < cy < -450600: nx += 1; continue
    # termosifona gelen soğuk/sıcak su uçları (merkezi sıcak suya geçildi)
    if e.dxf.handle in TERMO['rm']:
        if e.dxf.handle in TERMO['trim']:
            lay_, q_ = TERMO['trim'][e.dxf.handle]; PL(q_, lay_)
        nx += 1; continue
    # H sırası 1.-2. kat ofisleri: eski MTY yerden ısıtma devreleri / mahal etiketleri (yeni tasarım çizildi)
    if 284700 < cx < 289044 and -447827 < cy < -440327:
        if lay in ('MTY-PEX-BORU', 'MTY-ISIKAYBIMAHAL') or lay.startswith('MTY-RADYAT') or (e.dxftype() == 'INSERT' and e.dxf.name == 'MTY-RADYATOR MAHAL'):
            nx += 1; continue
    # termosifon yazıları (merkezi sıcak suya geçildi)
    if e.dxftype() in ('TEXT', 'MTEXT') and lay == 'MTY-VANA':
        t = e.dxf.text if e.dxftype() == 'TEXT' else e.text
        if 'TERMOS' in t.upper() or 'DUVARA' in t.upper(): nx += 1; continue
    skip = False
    for x0, x1, y0, y1 in EXC:
        if x0 < b.extmin.x and b.extmax.x < x1 and y0 - 1 <= b.extmin.y and b.extmax.y <= y1 + 1:
            if lay == 'ANTED': break
            if e.dxftype() in ('TEXT', 'MTEXT') and b.extmin.y < y0 + 200: break
            skip = True; break
    if skip: nx += 1; continue
    sec.append(e)
im = Importer(sdoc, doc)
im.import_entities(sec, msp); im.finalize()
for n in ('MIM-BODRUM-GUNCEL', 'MIM-GUNCEL-BODRUM'):
    if n in doc.layers: doc.layers.get(n).color = 8
scott(doc, wipe_sil=False)
doc.saveas('/tmp/claude-0/vy/MEKANIK_TAM.dxf')
print('TAM ok', len(sec), 'kullanıcı varlığı alındı,', nx, 'eski varlık çıkarıldı', round(time.time() - t0), 's')

