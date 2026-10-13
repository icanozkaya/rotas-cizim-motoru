# -*- coding: utf-8 -*-
"""VOYAP TÜM MEKANİK: yangın (rev) + sıhhi + ısıtma + havalandırma tek dosyada.
EK  = yalnız eklenen çizimler (kullanıcının koordinatında)
TAM = kullanıcının tüm dosyası + ekler (eski bodrum, eski kısmi MTY şemaları ve termosifon yazıları yerine yenileri)"""
import sys, time, pickle, math
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
import sihhi, isitma, alt, hava, sema_tes
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
hava.bodrum_mim(); hava.zemin_mim(); hava.otopark(); hava.siginak(); hava.zemin_saft(); print('hava', round(time.time() - t0))
# şemalar
sema_tes.sihhi_sema(); sema_tes.pis_sema(); sema_tes.isitma_sema(); sema_tes.kazan_sema()
# V sırası: çerçeve + başlıklar (yangın sırası çerçevesi kopyası)
for e in sdoc.modelspace().query('LINE[layer=="ANTED"]'):
    a, b = e.dxf.start, e.dxf.end
    if -458200 < a.y < -450600 and -458200 < b.y < -450600:
        L((a.x, a.y - 10322), (b.x, b.y - 10322), "ANTED")
_T(249115, -468306, "BODRUM KAT HAVALANDIRMA PLANI", 100, "MKDU0", TA.BOTTOM_CENTER)
_T(251260, -468306, "ZEMİN KAT ŞAFT / BACA ÇIKIŞLARI", 100, "MKDU0", TA.BOTTOM_CENTER)
yv = sema_tes.hava_sema(252700, -461100)
y = hava.notlar_hava(252700, yv - 200)
yy = sema_tes.lejant(259500, -461100, 'V')
yy = sema_tes.hava_tablo(259500, yy - 200)
# lejant / not / tablolar (V sırası sağ)
x = 263000
y = sema_tes.lejant(x, -461100, 'S')
y = sema_tes.lejant(x, y - 120, 'H')
x2 = 266500
y2 = sema_tes.notlar(x2, -461100, "SIHHİ TESİSAT NOTLARI", sema_tes.NOT_S, 9.0)
y2 = sema_tes.notlar(x2, y2 - 120, "ISITMA TESİSATI NOTLARI", sema_tes.NOT_H, 9.0)
y3 = sema_tes.ozet_tablolar(272500 - 1400, -461100) if False else None
sema_tes.ozet_tablolar(266500, y2 - 150)
pickle.dump(dict(OUT=sihhi.OUT, OUTI={k: v for k, v in isitma.OUTI.items() if k[0] != 'ana'}, OUTA={k: v for k, v in alt.OUTA.items() if k != 'bodrum_isi'}),
            open('/tmp/claude-0/vy/tes_out.pkl', 'wb')) if False else None
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
doc.saveas('/tmp/claude-0/vy/MEKANIK_TAM.dxf')
print('TAM ok', len(sec), 'kullanıcı varlığı alındı,', nx, 'eski varlık çıkarıldı', round(time.time() - t0), 's')
