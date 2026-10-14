"""Doğalgaz iç tesisat modülü (deneme) - giriş noktası.

Kullanım:
    python3 dogalgaz.py <proje.json> <cikti_klasoru> [--onizleme]

Çıktılar: <ad>_izometrik_kolon_semasi.dxf (R2018), <ad>_hesap.xlsx, (isteğe bağlı) PNG önizleme.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hesap        # noqa: E402
import excel        # noqa: E402
from cizim import Cizim, tr, AKSA_NOT, PAF, YAZ, NOT, UYA   # noqa: E402

NOTLAR = [
    'AKSAGAZ ŞARTNAMESİYLE TEYİT EDİLECEK: Sakarya dağıtım şirketi (AKSA Sakarya Doğal Gaz) teknik esasları doğrulanamamıştır;',
    '   sınır değerler EPDK İç Tesisat Yönetmeliğine dayanan ortak şartname içeriğinden alınmıştır.',
    'Şema ölçeksizdir; boru etiketlerinde sırasıyla hesap debisi (m³/h), gerçek boru uzunluğu (m) ve çap [hat no] verilmiştir.',
    'Sistem basıncı 21 mbar (servis kutusu regülatör çıkışı); kritik devre toplam kaybı sayaç hariç ≤1,8 mbar,',
    '   servis kutusu → sayaç vanası ≤1,0 mbar, sayaç → cihaz ≤0,8 mbar, gaz hızı ≤6 m/s alınmıştır.',
    'Bağımsız bölüm hesap debisi en az 3,5 m³/h alınmıştır; eşzamanlılık katsayısı AKSAGAZ tablosundan teyit edilecektir.',
    'Tesisat TS EN 10255 orta seri siyah çelik boru ile kaynaklı olarak yapılacaktır.',
    'Ana kesme vanası bina girişinde 1,90-2,10 m yükseklikte, kolay ulaşılır yerde yapılacaktır.',
    'Sayaçlar ortak alanda, havalandırmalı sayaç dolabında; sayaç vanası 1,90-2,10 m yükseklikte yapılacaktır.',
    'Gaz boruları elektrik, telefon ve sıcak su borularından en az 15 cm uzakta döşenecektir.',
    'Her cihaz girişinde kesme vanası; esnek bağlantı kombi için ≤60 cm, ocak için ≤150 cm yapılacaktır.',
    'Kombiler C tipi (hermetik) olacak, bacası doğrudan dış atmosfere verilecektir.',
    'Ocak mahallinde sürekli açık ≥150 cm² menfez yapılacaktır; mahal hacmi ≥12 m³ ve ≥1 m³/kW olacaktır.',
    'Tesisat, işletme basıncının 50 mbar fazlası ile sızdırmazlık testine tabi tutulacaktır.',
]


def calistir(json_yol, cikti, onizleme=True):
    P = json.load(open(json_yol, encoding='utf-8'))
    ag = hesap.Ag(P)
    ok = ag.cap_sec()
    ad = os.path.splitext(os.path.basename(json_yol))[0]
    os.makedirs(cikti, exist_ok=True)
    dxf_yol = os.path.join(cikti, f'{ad}_izometrik_kolon_semasi_R2.dxf')
    xls_yol = os.path.join(cikti, f'{ad}_hesap.xlsx')

    C = Cizim(ag, P)
    C.sema()
    # şema sınırları
    from ezdxf import bbox as zb
    bb = zb.extents(C.msp)
    sx0, sy0, sx1, sy1 = bb.extmin.x, bb.extmin.y, bb.extmax.x, bb.extmax.y
    # sağda tablolar
    tx = sx1 + 140
    ty = sy1
    W1, H1 = C.hesap_tablosu(tx, ty)
    W2, H2 = C.kontrol_tablosu(tx, ty - H1 - 90)
    W3, H3 = C.ekipman_tablosu(tx + W2 + 120, ty - H1 - 90)
    alt = ty - H1 - 90 - max(H2, H3) - 90
    Hl = C.lejant(tx, alt)
    Hn = C.notlar(tx + 980, alt, NOTLAR)
    # başlık / çerçeve
    x0, x1 = sx0 - 80, max(tx + W1, tx + W2 + 120 + 740, tx + 980 + 1500) + 80
    y1 = sy1 + 160
    y0 = min(sy0, alt - Hl, alt - Hn) - 260
    C.msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                         dxfattribs={'layer': PAF, 'const_width': 3})
    bas = 'DENEME - ' if P.get('deneme') else ''
    C.yazi(f'{bas}DOĞALGAZ İÇ TESİSATI İZOMETRİK KOLON ŞEMASI (30°)..........ÖLÇEKSİZ', (sx0, y0 + 150), 34, YAZ)
    C.yazi(f'{P["proje"]}  -  {P["sistem_basinci_mbar"]} mbar  -  {AKSA_NOT}', (sx0, y0 + 95), 20, UYA)
    if P.get('deneme'):
        C.yazi('DENEME: ' + P.get('aciklama', ''), (sx0, y0 + 50), 14, UYA)
    C.yazi('ROTAŞ MÜHENDİSLİK.PROJE.MÜŞAVİRLİK  -  Semerciler Mah. Sait Faik Sk. No:22/C Z01 Adapazarı/Sakarya  -  '
           '0264 272 00 49', (tx, y0 + 60), 14, YAZ)
    hatalar = C.kontrol()
    C.doc.saveas(dxf_yol)
    hatalar += [f'MTY: {m}' for m in mty_kontrol(dxf_yol)]
    satir = excel.yaz(ag, P, xls_yol)
    if onizleme:
        onizle(dxf_yol, os.path.join(os.environ.get('ONIZLEME_DIR', '/tmp'), f'{ad}_onizleme.png'))
    return dict(ok=ok, hiz=ag.hiz_ok(), dxf=dxf_yol, xlsx=xls_yol, hatalar=hatalar, ag=ag)


def mty_kontrol(dxf):
    """MTY geçen blok / katman / yazı stili / yazı / öznitelik listesi (boş = temiz)."""
    import ezdxf
    d = ezdxf.readfile(dxf)
    out = [f'blok {b.name}' for b in d.blocks if 'MTY' in b.name.upper()]
    out += [f'katman {l.dxf.name}' for l in d.layers if 'MTY' in l.dxf.name.upper()]
    out += [f'stil {s.dxf.name}' for s in d.styles if 'MTY' in s.dxf.name.upper()]
    for lay in [d.modelspace()] + list(d.blocks):
        for e in lay:
            t = e.text if e.dxftype() == 'MTEXT' else (e.dxf.get('text', '') if e.dxftype() in ('TEXT', 'ATTDEF') else '')
            if 'MTY' in str(t).upper():
                out.append(f'yazı {t[:40]}')
            if e.dxftype() == 'INSERT':
                out += [f'öznitelik {a.dxf.text}' for a in e.attribs if 'MTY' in a.dxf.text.upper()]
    return out


def onizle(dxf, png, dpi=200):
    import ezdxf
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import Configuration, LineweightPolicy
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    doc = ezdxf.readfile(dxf)
    fig = plt.figure(figsize=(40, 18))
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    Frontend(ctx, MatplotlibBackend(ax), config=Configuration(lineweight_policy=LineweightPolicy.ABSOLUTE)).draw_layout(
        doc.modelspace())
    fig.savefig(png, dpi=dpi // 2, facecolor='black')
    plt.close(fig)
    return png


if __name__ == '__main__':
    r = calistir(sys.argv[1], sys.argv[2], onizleme='--onizleme' in sys.argv)
    print('Çap seçimi sınırları sağlıyor:', r['ok'], '| hız uygun:', r['hiz'])
    print('DXF :', r['dxf'])
    print('XLSX:', r['xlsx'])
    print('MTY kontrolü:', 'TEMİZ (0 blok/katman/yazı)' if not any(h.startswith('MTY') for h in r['hatalar']) else 'MTY VAR')
    print('Geometri kontrolü:', 'TEMİZ' if not r['hatalar'] else f'{len(r["hatalar"])} sorun')
    for h in r['hatalar'][:40]:
        print('  -', h)
