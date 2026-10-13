# -*- coding: utf-8 -*-
import pickle, ezdxf
from ezdxf import recover
from ezdxf.enums import TextEntityAlignment as TA
C = pickle.load(open('/tmp/claude-0/is/content.pkl', 'rb')); R = C['R']
doc, _ = recover.readfile('/tmp/claude-0/is/hesap_fix.dxf'); msp = doc.modelspace()
for n in ('MTY-HESAP', 'MTY-HESAP-YAZI'):
    if n not in doc.layers: doc.layers.add(n, color=1 if n == 'MTY-HESAP' else 7)
if 'RTS-HESAP' not in doc.styles: doc.styles.add('RTS-HESAP', font='arial.ttf')
# eski OLE nesneleri (eski proje değerleri) kaldırılır, yerlerine güncel tablolar çizilir
for e in list(msp.query('OLE2FRAME')): msp.delete_entity(e)
def T(x, y, s, h, al=TA.MIDDLE_LEFT, color=None):
    t = msp.add_text(s, height=h, dxfattribs={'layer': 'MTY-HESAP-YAZI', 'style': 'RTS-HESAP', 'width': 0.85})
    if color: t.dxf.color = color
    t.set_placement((x, y), align=al)
def box(x0, y0, x1, y1, w=0.0):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': 'MTY-HESAP', 'const_width': w})
def fit(s, w, h):
    return min(h, (w - 6) / max(1, len(s) * 0.5))
def sections(x, y, W, title, sub, secs, h=9.0):
    y0 = y
    T(x + W / 2, y - 14, title, h * 1.5, TA.MIDDLE_CENTER); y -= 30
    if sub: T(x + W / 2, y - 6, sub, h * 1.2, TA.MIDDLE_CENTER, color=1); y -= 26
    RH = h * 2.4; c1 = W * 0.5
    for hd, intro, rows, son in secs:
        T(x + 10, y - 8, hd, h * 1.15, color=5); y -= 22
        if intro: T(x + 10, y - 6, intro, fit(intro, W - 20, h * 0.9)); y -= 18
        for a, b in rows:
            box(x + 10, y, x + 10 + c1, y - RH); box(x + 10 + c1, y, x + W - 10, y - RH)
            T(x + 14, y - RH / 2, a, fit(a, c1 - 8, h)); T(x + 10 + c1 + (W - 20 - c1) / 2, y - RH / 2, b, fit(b, W - 20 - c1 - 8, h), TA.MIDDLE_CENTER)
            y -= RH
        if son: T(x + 10, y - 9, son, h, color=3); y -= 20
        y -= 10
    box(x, y0, x + W, y - 4, 1.0)
    return y - 4
def table(x, y, title, hdr, rows, widths, h=8.0):
    T(x, y - 8, title, h * 1.3); y -= 22
    RH = h * 2.6; HH = h * 4.2
    xx = x
    for w, s in zip(widths, hdr):
        box(xx, y, xx + w, y - HH)
        words = s.split(); lines = []; cur = ''
        for wd in words:
            if len(cur + ' ' + wd) * h * 0.5 * 0.85 > w - 6 and cur: lines.append(cur); cur = wd
            else: cur = (cur + ' ' + wd).strip()
        lines.append(cur)
        for k, ln in enumerate(lines[:3]):
            T(xx + w / 2, y - HH / 2 + (len(lines[:3]) - 1) * h * 0.65 - k * h * 1.3, ln, h * 0.85, TA.MIDDLE_CENTER)
        xx += w
    y -= HH
    for row in rows:
        xx = x
        for w, v in zip(widths, row):
            s = str(v); box(xx, y, xx + w, y - RH); T(xx + w / 2, y - RH / 2, s, fit(s, w, h), TA.MIDDLE_CENTER); xx += w
        y -= RH
    return y
# OLE yerleri (kullanıcının çizimindeki çerçeveler)
# mevcut metinlerin üstüne binmesin: çizimin sağında boş alana (eski OLE tabloların sağı)
XR, YR = 349700, -492960
y = sections(XR, YR, 760, 'MEKANİK TESİSAT ISITMA SİSTEMİ', 'B1-B2-B3 BLOK – MERKEZİ ISITMA SİSTEMİ HESAP RAPORU', C['SEC'][:4], 8.5)
y2 = sections(XR + 800, YR, 760, 'MEKANİK TESİSAT ISITMA SİSTEMİ', 'HESAP RAPORU (DEVAM)', C['SEC'][4:], 8.5)
sections(XR, y - 40, 760, 'MEKANİK TESİSAT ISITMA SİSTEMİ', 'KAZAN DAİRESİ ALT-ÜST HAVALANDIRMA HESAP RAPORU', C['SEC_H'], 8.5)
# ekipman tabloları (eski 4 Excel nesnesinin yeri)
x0, y = 346761, -494538
ytop = y
WID = {9: [80, 330, 200, 520, 70, 160, 170, 160, 170], 8: [80, 300, 190, 260, 260, 260, 150, 80], 7: [80, 330, 520, 230, 200, 230, 80], 5: [80, 380, 260, 180, 80]}
col = 0
for t, hdr, rows in C['EQ']:
    w = WID.get(len(hdr)) or [1500 / len(hdr)] * len(hdr)
    y = table(x0, y, t, hdr, rows, w) - 30
ys = y
box(x0 - 15, ytop + 15, x0 + max(sum(WID.get(len(h_)) or [1500]) for _, h_, _ in C['EQ']) + 15, ys + 10, 1.0)
# rapor metinleri: proje bilgisi ve eski proje kalıntıları düzeltilir
for e in msp.query('TEXT'):
    s = e.dxf.text
    if '69/1 Pafta 804 Ada 323 Parsel' in s: e.dxf.text = s.replace('69/1 Pafta 804 Ada 323 Parsel', '69 Pafta 944 Ada 343 Parsel')
for e in msp.query('MTEXT'):
    s = e.text
    if 'GENEL BİLGİLER' in e.plain_text():
        s = s.replace('BİNADA DOĞALGAZLI KOMBİ  KULLANILACAKTIR', 'BİNADA DOĞALGAZ YAKITLI DUVAR TİPİ YOĞUŞMALI KASKAD KAZAN ({} x {} kW = {} kW) KULLANILACAKTIR'.format(R['K_ADET'], R['K_BIRIM'], R['QK']))
        i = s.find('8.SICAK SU KAPASİTESİ')
        if i >= 0:
            j = s.find('KALORİFER PROJE RAPOR')
            s = s[:i] + '8.SICAK SU KAPASİTESİ\\P\\P    HER DAİREDE 24 kW KAPASİTELİ DUVARA ASILABİLEN HERMETİK ŞOFBEN KULLANILACAKTIR.\\P\\P    ' + (s[j:] if j > 0 else '')
        e.text = s
doc.header['$INSUNITS'] = 5
doc.saveas('/tmp/claude-0/is/out/ISITMA_HESAPLARI.dxf'); print('ok')
