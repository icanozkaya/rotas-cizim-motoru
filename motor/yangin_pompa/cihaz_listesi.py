# -*- coding: utf-8 -*-
"""Yangın pompa grubu cihaz listesi tablosu (DXF). Değerler kullanıcının listesinden; depo 81 m³, ana pompalar 81 m³/h."""
import ezdxf, sys

SATIR = [
    ('01', 'ELEKTRİKLİ YANGIN POMPASI (ASIL)', ['Q=81 m³/h', 'H=60 mSS', 'P=22 kW', '400V 50Hz', '2900 rpm', 'PN16']),
    ('02', 'DİZEL YANGIN POMPASI (YEDEK)', ['Q=81 m³/h', 'H=60 mSS', 'P=30 kW', '2900 rpm', 'PN16', 'Akülü Marş', '100 lt Yakıt Tankı']),
    ('03', 'JOKEY POMPA', ['Q=3 m³/h', 'H=70 mSS', 'P=1.5 kW', '400V 50Hz', 'PN16']),
    ('04', 'ELEKTRİKLİ POMPA KONTROL PANOSU', ['IP54', 'Otomatik/Manuel', 'Yıldız-Üçgen Yol Verme', 'Faz Koruma', 'Arıza Alarmı', 'NFPA20']),
    ('05', 'DİZEL POMPA KONTROL PANOSU', ['IP54', 'Otomatik Start', '2 Set Akü Şarj Ünitesi', '6 Deneme Startı', 'Arıza Alarmı', 'NFPA20']),
    ('06', 'JOKEY POMPA PANOSU', ['Basınç Kontrollü Otomatik Çalışma', 'IP54', '400V']),
    ('07', 'YANGIN SUYU DEPOSU', ['V=81 m³', 'OH2 Tehlike Sınıfı', '60 dk Çalışma Süresi']),
]

def ciz(out):
    doc = ezdxf.new('R2018', setup=True); doc.units = 5
    st = doc.styles.new('ROTAS-ARIAL', dxfattribs={'font': 'arial.ttf'})
    for n, c in (('ROTAS-HESAP-CERCEVE', 4), ('ROTAS-HESAP-CIZGI', 1), ('ROTAS-HESAP-YAZI', 7), ('ROTAS-HESAP-BASLIK', 2)):
        doc.layers.add(n, color=c)
    m = doc.modelspace()
    H, HB, HT = 12.5, 15.0, 22.0
    W = [60, 520, 1020]           # NO | CİHAZ | TEKNİK ÖZELLİKLER
    X = [0]; [X.append(X[-1] + w) for w in W]
    RH = 34; TH = 50
    # teknik özellik metnini " • " ile ayırıp satıra sığdır
    def sar(parcalar, gen):
        sat, cur = [], ''
        for p in parcalar:
            s = (cur + '  •  ' + p) if cur else p
            if len(s) * H * 0.62 > gen - 30 and cur: sat.append(cur); cur = p
            else: cur = s
        sat.append(cur); return sat
    rows = [(no, ad, sar(oz, W[2])) for no, ad, oz in SATIR]
    hts = [max(RH, 22 + len(t) * H * 1.7) for _, _, t in rows]
    tot = TH + RH + sum(hts)
    y0 = 0
    def box(x1, y1, x2, y2, lay='ROTAS-HESAP-CIZGI', w=0):
        m.add_lwpolyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], close=True, dxfattribs={'layer': lay, 'const_width': w})
    def txt(s, x, y, h, al='MIDDLE_CENTER', lay='ROTAS-HESAP-YAZI'):
        t = m.add_text(s, height=h, dxfattribs={'layer': lay, 'style': 'ROTAS-ARIAL'}); t.set_placement((x, y), align=ezdxf.enums.TextEntityAlignment[al])
    # başlık
    box(X[0], y0 - TH, X[-1], y0, 'ROTAS-HESAP-CIZGI')
    txt('YANGIN POMPA GRUBU CİHAZ LİSTESİ', X[-1] / 2, y0 - TH / 2, HT, lay='ROTAS-HESAP-BASLIK')
    y = y0 - TH
    for i, b in enumerate(['NO', 'CİHAZ', 'TEKNİK ÖZELLİKLERİ']):
        box(X[i], y - RH, X[i + 1], y); txt(b, (X[i] + X[i + 1]) / 2, y - RH / 2, HB, lay='ROTAS-HESAP-BASLIK')
    y -= RH
    for (no, ad, t), h in zip(rows, hts):
        for i in range(3): box(X[i], y - h, X[i + 1], y)
        txt(no, (X[0] + X[1]) / 2, y - h / 2, H)
        txt(ad, X[1] + 15, y - h / 2, H, 'MIDDLE_LEFT')
        n = len(t); sp = H * 1.7
        for k, s in enumerate(t):
            txt(s, X[2] + 15, y - h / 2 + (n - 1) * sp / 2 - k * sp, H, 'MIDDLE_LEFT')
        y -= h
    box(-15, y - 15, X[-1] + 15, y0 + 15, 'ROTAS-HESAP-CERCEVE', 2)
    doc.saveas(out)

if __name__ == '__main__':
    ciz(sys.argv[1] if len(sys.argv) > 1 else 'YANGIN_POMPA_CIHAZ_LISTESI.dxf')
