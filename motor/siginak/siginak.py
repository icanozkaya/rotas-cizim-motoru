# -*- coding: utf-8 -*-
"""Sığınak havalandırma hesabı (kullanıcı şablonu): taze hava = net alan x net yükseklik x 4 defa/h; egzoz = taze havanın %10 eksiği;
net alan > 100 m² ise duman tahliye (10 defa/h) eklenir; perde geçiş ölçüsü v = 2,5 m/s ile."""
import math, ezdxf, openpyxl
from ezdxf.enums import TextEntityAlignment as TA
SIG = [('SIĞINAK 1', 99.18, 116.91), ('SIĞINAK 2', 45.27, 60.00)]   # (ad, net alan, brüt alan) — ısıtma projesi bodrum planı
HN = 3.00; N_TH = 4; N_DT = 10; V_GEC = 2.5; ESIK = 100.0
OLCU = [(30, 20), (40, 20), (40, 25), (40, 30), (50, 30), (50, 40), (60, 40), (60, 50), (80, 50)]
def yukari(q, adim): return int(math.ceil(q / adim) * adim)
def gecis(q):
    a = q / 3600 / V_GEC * 1e4
    return next(f'{b} × {h} cm' for b, h in OLCU if b * h >= a), a
f = lambda v, n=2: f'{v:,.{n}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
RES = []
for ad, A, Ab in SIG:
    V = A * HN; qth = V * N_TH; qsec = yukari(qth, 100); qeg = qsec * 0.9
    r = dict(ad=ad, A=A, Ab=Ab, V=V, qth=qth, qsec=qsec, qeg=qeg, gth=gecis(qsec), geg=gecis(qeg), dt=A > ESIK)
    if r['dt']:
        qdt = V * N_DT; r.update(qdt=qdt, qdts=yukari(qdt, 500), gdt=gecis(yukari(qdt, 500)))
    RES.append(r)
doc = ezdxf.new('R2018', setup=True); doc.header['$INSUNITS'] = 5; msp = doc.modelspace()
doc.styles.add('ARİAL', font='arial.ttf')
for n, c in (('ROTAS-HESAP-CIZGI', 1), ('ROTAS-HESAP-YAZI', 7), ('ROTAS-HESAP-CERCEVE', 1)): doc.layers.add(n, color=c)
def T(x, y, s, h, al=TA.MIDDLE_LEFT):
    t = msp.add_text(s, height=h, dxfattribs={'layer': 'ROTAS-HESAP-YAZI', 'style': 'ARİAL', 'width': 0.85}); t.set_placement((x, y), align=al)
def box(x0, y0, x1, y1, lay='ROTAS-HESAP-CIZGI', w=0.0):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': lay, 'const_width': w})
H = 12.0; RH = 26.0
def blok(x, y, r):
    W = 900; y0 = y
    # cihaz listesi
    T(x + W / 2, y - 16, f"{r['ad']} - CİHAZ LİSTESİ", H * 1.1, TA.MIDDLE_CENTER); y -= 32
    cols = [60, 330, 250, 90, 170]; hdr = ['SIRA NO', 'CİHAZ ADI', 'KAPASİTE VE EBATLAR', 'MİKTAR', 'AÇIKLAMA']
    rows = [['1', 'SIĞINAK TAZE HAVA SANTRALİ', f"{f(r['qsec'], 0)} m³/h 100 Pa", '1', 'Kendinden By-Pass'],
            ['2', 'KANAL TİPİ EGZOZ FANI', f"{f(r['qeg'], 0)} m³/h 100 Pa", '1', '']]
    if r['dt']: rows.append(['3', 'DUMAN TAHLİYE FANI', f"{r['qdts']} m³/h 100 Pa", '1', ''])
    for rw in [hdr] + rows:
        xx = x
        for w, v in zip(cols, rw):
            box(xx, y, xx + w, y - RH); T(xx + w / 2, y - RH / 2, v, H * (0.85 if rw is hdr else 0.95), TA.MIDDLE_CENTER); xx += w
        y -= RH
    y -= 30
    T(x + 20, y - 14, f"{r['ad']} HAVALANDIRMA HESABI", H * 1.6); y -= 40
    for s in ['SIĞINAK YÖNETMELİĞİ (Resmi Gazete Tarihi: 25.08.1988 Resmi Gazete Sayısı: 19910)',
              'Madde 8 – (Başlığı ile birlikte değişik: RG-29/9/2010-27714)']:
        T(x + 20, y - 8, s, H); y -= 22
    y -= 6
    tc = [200, 170, 260, 230]
    th = [['Sığınak Kapasitesi', 'Koruma Havalandırması', 'Yüksek Yangın Tehlikesi', 'Düşük ve Orta Yangın Tehlikesi'],
          ['0-50 kişiye kadar', '1,8 m³/h-kişi', 'Kum filtre,', 'G4 toz filtre'],
          ['51-150 kişiye kadar', '3,0 m³/h-kişi', 'G4 toz filtre ve', 'Radyoaktif filtre ve'],
          ['150 kişiden fazla', '4,5 m³/h-kişi', 'Aktif karbon filtre', 'Aktif karbon filtre']]
    for rw in th:
        xx = x + 20
        for w, v in zip(tc, rw):
            box(xx, y, xx + w, y - RH); T(xx + w / 2, y - RH / 2, v, H * 0.85, TA.MIDDLE_CENTER); xx += w
        y -= RH
    y -= 24
    def kv(baslik, items):
        nonlocal y
        T(x + 20, y - 12, baslik, H * 1.3); y -= 32
        c1 = 520
        for a, b in items:
            box(x + 20, y, x + 20 + c1, y - RH); box(x + 20 + c1, y, x + W - 20, y - RH)
            T(x + 30, y - RH / 2, a, H); T(x + 20 + c1 + (W - 40 - c1) / 2, y - RH / 2, b, H, TA.MIDDLE_CENTER); y -= RH
        y -= 22
    kv(f"{r['ad']} GENEL HAVALANDIRMA HESABI",
       [('Sığınak Net Alanı', f"{f(r['A'])} m²"), ('Sığınak Net Yüksekliği', f"{f(HN)} m"), ('Sığınak Hacmi', f"{f(r['V'])} m³"),
        ('Hava Değişim Sayısı', f"{N_TH} defa/saat"), ('Taze Hava İçin Gerekli Hava', f"{f(r['qth'])} m³/h"),
        ('Seçilen Taze Hava Debisi', f"{f(r['qsec'], 0)} m³/h"), ('Egzoz Debisi (taze havadan %10 az)', f"{f(r['qeg'], 0)} m³/h"),
        (f'Perde Geçişi - Taze Hava (v = {f(V_GEC, 1)} m/s)', r['gth'][0]), (f'Perde Geçişi - Egzoz (v = {f(V_GEC, 1)} m/s)', r['geg'][0])])
    for s in ['Sığınak havalandırma fanının enerji ihtiyacı fan elektrik motoruna uygun kapasitede bir jeneratör ile karşılanmalı,',
              'jeneratör için sığınak alanı dışında bir alan makine dairesi olarak tasarlanmalıdır. Jeneratör egzozu doğrudan dışarıya',
              'verilmelidir. Jeneratörün devre dışı kaldığı durumlarda ise, enerji ihtiyacı fana bağlı insan gücü ile çalışan çevirmeli',
              'kol yardımı ile karşılanmalıdır.']:
        T(x + 20, y - 8, s, H * 0.9); y -= 20
    y -= 16
    if r['dt']:
        kv(f"{r['ad']} DUMAN TAHLİYE HAVALANDIRMASI HESABI",
           [('Sığınak Net Alanı', f"{f(r['A'])} m²"), ('Sığınak Net Yüksekliği', f"{f(HN)} m"), ('Sığınak Hacmi', f"{f(r['V'])} m³"),
            ('Çevrim Oranı', f"{N_DT} defa/saat"), ('Duman Tahliye İçin Gerekli Hava', f"{f(r['qdt'])} m³/h"),
            ('Seçilen Duman Tahliye Debisi', f"{r['qdts']} m³/h"), (f'Perde Geçişi - Duman Tahliye (v = {f(V_GEC, 1)} m/s)', r['gdt'][0])])
    else:
        T(x + 20, y - 8, f"Sığınak net alanı {f(r['A'])} m² < 100 m² olduğundan duman tahliye fanı gerekmez; taze hava ve egzoz yeterlidir.", H); y -= 30
    box(x, y0 + 6, x + W, y, 'ROTAS-HESAP-CERCEVE', 1.0)
    return y
X = 0.0
for i, r in enumerate(RES):
    blok(X + i * 960, 0.0, r)
doc.saveas('/tmp/claude-0/sg/SIGINAK_HAVALANDIRMA_HESABI.dxf')
for r in RES: print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
