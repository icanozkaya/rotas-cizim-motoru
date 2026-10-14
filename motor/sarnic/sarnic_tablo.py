# -*- coding: utf-8 -*-
"""Yağmur suyu sarnıcı depo hacmi hesabı tablosu (DXF) — kullanıcının Excel tablo düzeni, hesap özeti değerleriyle."""
import ezdxf, sys
from ezdxf.enums import TextEntityAlignment as TA

h, AA, AB, A = 659.40, 365.00, 337.70, 702.60      # hesap özetindeki değerler (A = 702,6 m²)
e, eta = 0.80, 0.90
E = A * h / 1000 * e * eta
V = 0.06 * E
Ad = 3.74 * 5.05
hs = V / Ad
Ab = 181.60
qg = Ab * 5 / 1000
Hm = 1.50
Vm = Ad * Hm
t = Vm / qg

def f(v, d=2): return f'{v:,.{d}f}'.replace(',', '#').replace('.', ',').replace('#', '.')
R = [
 ('1', 'Yıllık yağış (MGM 1960-2025)', 'h', '-', f(h), 'mm'),
 ('2', 'A Blok çatı iz düşümü (saçak dahil)', 'A_A', '-', f(AA), 'm²'),
 ('3', 'B Blok çatı iz düşümü (saçak dahil)', 'A_B', '-', f(AB), 'm²'),
 ('4', 'Toplam toplama alanı', 'A', 'A = A_A + A_B', f(A), 'm²'),
 ('5', 'Çatı verim katsayısı (kiremit kırma çatı)', 'e', '-', f(e), '-'),
 ('6', 'Filtre hidrolik verimi', 'η', '-', f(eta), '-'),
 ('7', 'Yıllık toplanabilir su', 'E', 'E = A · h/1000 · e · η', f(E), 'm³/yıl'),
 ('8', 'Gerekli depo hacmi', 'V', 'V = 0,06 · E', f(V), 'm³'),
 ('9', 'Depo taban alanı (iç 3,74 × 5,05 m)', 'A_d', 'A_d = 3,74 · 5,05', f(Ad), 'm²'),
 ('10', 'Gerekli faydalı su yüksekliği', 'h_s', 'h_s = V / A_d', f(hs), 'm'),
 ('11', 'Sulanan bahçe alanı', 'A_b', '-', f(Ab), 'm²'),
 ('12', 'Yaz günlük sulama (5 l/m²·gün)', 'q_g', 'q_g = A_b · 5 / 1000', f(qg), 'm³/gün'),
 ('13', 'Depo karşılama süresi', 't', 't = V_m / q_g', f(t), 'gün'),
 ('14', 'Mevcut depo faydalı su yüksekliği', 'H_m', '-', f(Hm), 'm'),
 ('15', 'Mevcut depo faydalı hacmi', 'V_m', 'V_m = A_d · H_m', f(Vm), 'm³'),
 ('16', 'Kontrol V_m ≥ V', '', 'V_m ≥ V', 'UYGUN', ''),
]
BOLD = {'8', '10'}

def ciz(out):
    doc = ezdxf.new('R2018', setup=True); doc.units = 5
    doc.styles.new('ROTAS-ARIAL', dxfattribs={'font': 'arial.ttf'})
    for n, c in (('ROTAS-HESAP-CERCEVE', 7), ('ROTAS-HESAP-CIZGI', 8), ('ROTAS-HESAP-YAZI', 7), ('ROTAS-HESAP-BASLIK', 7)):
        doc.layers.add(n, color=c)
    m = doc.modelspace()
    H = 12.5
    W = [55, 450, 120, 300, 130, 90]
    X = [0]
    for w in W: X.append(X[-1] + w)
    RH = 32
    def box(x1, y1, x2, y2, lay='ROTAS-HESAP-CIZGI', w=0):
        m.add_lwpolyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], close=True, dxfattribs={'layer': lay, 'const_width': w})
    def txt(s, x, y, hh, al='MIDDLE_LEFT', lay='ROTAS-HESAP-YAZI', bold=False):
        t = m.add_text(s, height=hh, dxfattribs={'layer': lay, 'style': 'ROTAS-ARIAL', 'width': 1.0})
        t.set_placement((x, y), align=TA[al])
        if bold:  # kalın görünüm: yarım genişlik ötelemeli ikinci yazı
            t2 = m.add_text(s, height=hh, dxfattribs={'layer': lay, 'style': 'ROTAS-ARIAL'}); t2.set_placement((x + hh * 0.06, y), align=TA[al])
    y = 0
    txt('ROTAŞ MÜHENDİSLİK - 318-319 PARSEL GÜNGÖREN A-B BLOK', 10, y - 25, 18, lay='ROTAS-HESAP-BASLIK', bold=True)
    txt('YAĞMUR SUYU SARNICI - DEPO HACMİ HESABI (PAİY m.57/7-a, TS EN 16941-1)', 10, y - 55, 14, lay='ROTAS-HESAP-BASLIK', bold=True)
    y = -80
    for i, b in enumerate(['NO', 'KALEM', 'SEMBOL', 'FORMÜL', 'DEĞER', 'BİRİM']):
        box(X[i], y - RH, X[i + 1], y); txt(b, (X[i] + X[i + 1]) / 2, y - RH / 2, 14, 'MIDDLE_CENTER', 'ROTAS-HESAP-BASLIK', bold=True)
    y -= RH
    for r in R:
        for i in range(6): box(X[i], y - RH, X[i + 1], y)
        yc = y - RH / 2; b = r[0] in BOLD
        txt(r[0], (X[0] + X[1]) / 2, yc, H, 'MIDDLE_CENTER')
        txt(r[1], X[1] + 8, yc, H)
        txt(r[2], (X[2] + X[3]) / 2, yc, H, 'MIDDLE_CENTER')
        txt(r[3], X[3] + 8, yc, H)
        if r[4] == 'UYGUN': txt(r[4], X[4] + 8, yc, H, bold=True)
        else: txt(r[4], X[5] - 8, yc, H, 'MIDDLE_RIGHT', bold=b)
        txt(r[5], (X[5] + X[6]) / 2, yc, H, 'MIDDLE_CENTER')
        y -= RH
    txt('NOT: Tabloda gerekli depo hacmi hesap değeri olarak verilmiştir;', 0, y - 28, 12)
    txt(f'mevcut depo (iç 3,74 × 5,05 m, faydalı h = {f(Hm)} m, V = {f(Vm)} m³) bu değeri karşılamaktadır.', 0, y - 50, 12)
    box(-20, y - 70, X[-1] + 20, 20, 'ROTAS-HESAP-CERCEVE', 1.5)
    doc.saveas(out)

if __name__ == '__main__':
    ciz(sys.argv[1] if len(sys.argv) > 1 else 'SARNIC_DEPO_HACMI_HESABI.dxf')
    print('A', A, 'E', round(E, 2), 'V', round(V, 2), 'Ad', round(Ad, 2), 'hs', round(hs, 2), 'qg', round(qg, 2), 't', round(t, 2), 'Vm', round(Vm, 2))
