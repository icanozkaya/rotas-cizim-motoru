# -*- coding: utf-8 -*-
"""Isıtma hesaplar DXF: eski OLE tablolar silinir; güncel rapor/ekipman tabloları çizimin kendi yazı stiliyle (ARİAL, beyaz yazı,
kırmızı çerçeve) sıkı düzende çizilir; rapor notları (MTEXT) diğer notlarla aynı font/renk/yükseklikte düz yazıya çevrilir,
proje / kat bilgileri doldurulur (başlık ve maddeler korunur)."""
import pickle, re, ezdxf
from ezdxf import recover
from ezdxf.enums import TextEntityAlignment as TA
C = pickle.load(open('/tmp/claude-0/is/content.pkl', 'rb')); R = C['R']
doc, _ = recover.readfile('/tmp/claude-0/is/hesap_fix.dxf'); msp = doc.modelspace()
STY = 'ARİAL'; H_NOT = 14.37
if 'MTY-HESAP' not in doc.layers: doc.layers.add('MTY-HESAP', color=1)
for e in list(msp.query('OLE2FRAME')): msp.delete_entity(e)
# ---------------------------------------------------------------- notlar: proje / kat bilgileri
PROJ = dict(pafta='69', ada='944', parsel='343', sahip='TEKİN KARAKUŞ VE HİSS.', daire=36,
            katlar='1 BODRUM + 1 ZEMİN + 5 NORMAL KAT + 1 ÇATI KATI', kazan=f"{R['K_ADET']} x {R['K_BIRIM']} kW = {R['QK']} kW")
for e in msp.query('TEXT'):
    s = e.dxf.text
    s = s.replace('69/1 Pafta 804 Ada 323 Parsel', f"{PROJ['pafta']} Pafta {PROJ['ada']} Ada {PROJ['parsel']} Parsel")
    s = s.replace('2 bodrum,1 zemin, 5 normal', '1 bodrum, 1 zemin, 5 normal')
    e.dxf.text = s
def duz(t):
    t = re.sub(r'\\[fF][^;]*;', '', t); t = re.sub(r'\\[HhWwQqTtAaCc][^;]*;', '', t); t = re.sub(r'\\p[^;]*;', '', t)
    t = re.sub(r'^\d+;', '', t); t = t.replace('\\P', '\n').replace('{', '').replace('}', '').replace('**', '')
    t = re.sub(r'\\[LlOoKk]', '', t)
    return t
for e in list(msp.query('MTEXT')):
    t = duz(e.text)
    if 'GENEL BİLGİLER' in t:
        t = re.sub(r'BİNA İSTANBUL\s+İLİNDE OLUP .*?OLUŞMAKTADIR', f"BİNA İSTANBUL İLİ GÜNGÖREN İLÇESİ {PROJ['pafta']} PAFTA {PROJ['ada']} ADA {PROJ['parsel']} PARSEL ÜZERİNDE OLUP {PROJ['katlar']}'NDAN OLUŞMAKTADIR (B1-B2-B3 BLOK)", t, flags=re.S)
        t = t.replace('BİNADA DOĞALGAZLI KOMBİ  KULLANILACAKTIR', f"BİNADA DOĞALGAZ YAKITLI DUVAR TİPİ YOĞUŞMALI KASKAD KAZAN ({PROJ['kazan']}) KULLANILACAKTIR")
        i = t.find('8.SICAK SU KAPASİTESİ')
        if i >= 0:
            j = t.find('KALORİFER PROJE RAPOR')
            t = t[:i] + f"8.SICAK SU KAPASİTESİ\n\n{PROJ['daire']} ADET 24 kW KAPASİTELİ DUVARA ASILABİLEN HERMETİK ŞOFBEN KULLANILACAKTIR.\n\n({PROJ['daire']} x 24) = {PROJ['daire'] * 24} kW   {PROJ['sahip']}\n" + (t[j:] if j > 0 else '')
    if 'YALITIM ŞARTNAMESİ' in t and not t.lstrip().startswith('ISI YALITIM'):
        k = t.find('ISI YALITIM ŞARTNAMESİ')          # parça sırası bozulmuş: başlıktan başlat
        t = t[k:].replace('Dış duvar ı', 'Dış duvar ı', 1) + t[:k]
        t = t.replace('Dış duvar ısı yalıtımında', 'Dış duvar ısı yalıtımında')
    lines = [ln.rstrip() for ln in t.split('\n')]
    t = '\\P'.join(re.sub(r'\s+', ' ', ln).strip() for ln in lines)
    e.text = t; e.dxf.style = STY; e.dxf.char_height = H_NOT; e.dxf.layer = '0'; e.dxf.color = 256
    try: e.dxf.line_spacing_factor = 1.0
    except Exception: pass
# ---------------------------------------------------------------- tablolar
def T(x, y, s, h, al=TA.MIDDLE_LEFT):
    t = msp.add_text(s, height=h, dxfattribs={'layer': '0', 'style': STY, 'width': 0.8}); t.set_placement((x, y), align=al)
def box(x0, y0, x1, y1, w=0.0):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': 'MTY-HESAP', 'const_width': w})
def tw(s, h): return len(s) * h * 0.62
def fit(s, w, h): return min(h, (w - 4) / max(1, len(s) * 0.5))
def sections(x, y, W, title, sub, secs, h=8.0):
    y0 = y; RH = h * 2.0
    T(x + W / 2, y - 12, title, h * 1.35, TA.MIDDLE_CENTER); y -= 24
    if sub: T(x + W / 2, y - 4, sub, h * 1.1, TA.MIDDLE_CENTER); y -= 18
    c1 = W * 0.52
    for hd, intro, rows, son in secs:
        T(x + 8, y - 6, hd, h * 1.05); y -= 16
        if intro: T(x + 8, y - 5, intro, fit(intro, W - 16, h * 0.85)); y -= 14
        for a, b in rows:
            box(x + 8, y, x + 8 + c1, y - RH); box(x + 8 + c1, y, x + W - 8, y - RH)
            T(x + 11, y - RH / 2, a, fit(a, c1 - 6, h)); T(x + 8 + c1 + (W - 16 - c1) / 2, y - RH / 2, b, fit(b, W - 16 - c1 - 6, h), TA.MIDDLE_CENTER)
            y -= RH
        if son: T(x + 8, y - 7, son, h * 0.95); y -= 15
        y -= 6
    box(x, y0, x + W, y - 2, 1.0)
    return y - 2
def table(x, y, title, hdr, rows, h=7.5):
    # sütun genişliği içeriğe göre (sıkı)
    ws_ = []
    for j, hd in enumerate(hdr):
        words = hd.split(); longest = max(tw(wd, h * 0.8) for wd in words)
        need = max([longest + 8, min(tw(hd, h * 0.8), 110) + 8] + [tw(str(r[j]), h) + 10 for r in rows])
        ws_.append(need)
    T(x, y - 7, title, h * 1.25); y -= 17
    HH = h * 3.6; RH = h * 2.1
    xx = x
    for w, s in zip(ws_, hdr):
        box(xx, y, xx + w, y - HH)
        words = s.split(); lines = []; cur = ''
        for wd in words:
            if tw((cur + ' ' + wd).strip(), h * 0.8) > w - 6 and cur: lines.append(cur); cur = wd
            else: cur = (cur + ' ' + wd).strip()
        lines.append(cur); lines = lines[:3]
        for k, ln in enumerate(lines):
            T(xx + w / 2, y - HH / 2 + (len(lines) - 1) * h * 0.55 - k * h * 1.1, ln, h * 0.8, TA.MIDDLE_CENTER)
        xx += w
    y -= HH
    for row in rows:
        xx = x
        for w, v in zip(ws_, row):
            s = str(v); box(xx, y, xx + w, y - RH); T(xx + w / 2, y - RH / 2, s, fit(s, w, h), TA.MIDDLE_CENTER); xx += w
        y -= RH
    return y, sum(ws_)
YT = -492960
# ekipman tabloları (sıkı)
x0 = 346761; y = YT; wmax = 0
for t, hdr, rows in C['EQ']:
    y, w = table(x0 + 10, y - 6, t, hdr, rows); y -= 12; wmax = max(wmax, w)
box(x0, YT, x0 + wmax + 20, y, 1.0)
xr = x0 + wmax + 60
W = 600
y1 = sections(xr, YT, W, 'MEKANİK TESİSAT ISITMA SİSTEMİ', 'B1-B2-B3 BLOK – MERKEZİ ISITMA SİSTEMİ HESAP RAPORU', C['SEC'][:4])
y2 = sections(xr + W + 30, YT, W, 'MEKANİK TESİSAT ISITMA SİSTEMİ', 'HESAP RAPORU (DEVAM)', C['SEC'][4:])
sections(xr + 2 * (W + 30), YT, W, 'MEKANİK TESİSAT ISITMA SİSTEMİ', 'KAZAN DAİRESİ ALT-ÜST HAVALANDIRMA HESAP RAPORU', C['SEC_H'])
doc.header['$INSUNITS'] = 5
doc.saveas('/tmp/claude-0/is/out/ISITMA_HESAPLARI.dxf'); print('ok')
