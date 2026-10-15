"""yerden2 — tur 5/6 kırpımları: her dairede kollektör + kombi hattı + ayak demeti (plan), şema kombi+kollektör ve
devre paneli (motor | kullanıcı new_block yan yana).

    python3 motor/yerden2/yi_kirp_kollektor.py [çıkış_klasörü]

Varsayılan çıkış: kutuphane/arastirma/kontrol_png/yerden_tur5_uretici/
"""
import json
import os
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import yi_kirp as KR  # noqa: E402
import yi_sema as SE  # noqa: E402

KOK = KR.KOK
CIK = KOK + '/kutuphane/arastirma/kontrol_png/yerden_tur5_uretici'


def main(cik=CIK):
    os.makedirs(cik, exist_ok=True)
    model = json.load(open(KR.MODEL))
    A = KR.Cizici(KR.DXF)
    R = KR.Cizici(KR.REF)
    # plan: kollektör dolapları (ROTAS-ISITMA-KOLLEKTOR kapalı polyline) -> daire
    dolaplar = [(e, b) for e, b in A.ent if e.dxftype() == 'LWPOLYLINE' and e.dxf.layer == 'ROTAS-ISITMA-KOLLEKTOR'
                and e.closed and b[0] < SE.X0]
    for kat in model['katlar']:
        for d in kat['daireler'].values():
            hol = [m for m in d['mahaller'] if m['tur'] == 'hol']
            mut = [m for m in d['mahaller'] if m['tur'] == 'mutfak']
            bs = [m['bbox'] for m in hol + mut if m.get('bbox')]
            if not bs:
                continue
            x0, y0 = min(b[0] for b in bs) - 80, min(b[1] for b in bs) - 80
            x1, y1 = max(b[2] for b in bs) + 80, max(b[3] for b in bs) + 80
            # dairenin dolabı pencereye dahil
            for e, b in dolaplar:
                cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                if x0 - 200 < cx < x1 + 200 and y0 - 200 < cy < y1 + 200:
                    x0, y0, x1, y1 = min(x0, b[0] - 60), min(y0, b[1] - 60), max(x1, b[2] + 60), max(y1, b[3] + 60)
            ad = '%s_%s_kollektor_ayak' % (kat['kat'], d['no'])
            A.png((x0, y0, x1, y1), cik + '/_a.png', 1800)
            R.png((x0 + KR.DX_PLAN, y0, x1 + KR.DX_PLAN, y1), cik + '/_b.png', 1800)
            k = d.get('kollektor') or {}
            KR.yan_yana(cik + '/_a.png', cik + '/_b.png', '%s/%s.png' % (cik, ad),
                        ('MOTOR %s %s: kollektör %s ağız, ayaklı %s, kombi hattı %s' % (
                            kat['ad'], d['no'], k.get('agiz'), k.get('ayakli'), 'var' if k.get('kombi_hatti') else 'YOK'),
                         'KULLANICI new_block (planda kollektör yok)'))
            print('[kirp]', ad)
    # şema: zemin bandının ilk dairesi (kombi + kollektör + ilk paneller) ve tek panel yakın
    for ad, w, px in (
            ('sema_kombi_kollektor_paneller', (SE.X0 + 60, SE.BANT0 - 130, SE.X0 + 900, SE.BANT0 + 260), 2400),
            ('sema_panel_yakin_1', (SE.X0 + 114.4 + 146 + 290 - 40, SE.BANT0 - 40, SE.X0 + 114.4 + 146 + 290 + 150,
                                    SE.BANT0 + 125), 2000),
            ('sema_panel_yakin_2', (SE.X0 + 114.4 + 146 + 490 - 40, SE.BANT0 - 40, SE.X0 + 114.4 + 146 + 490 + 150,
                                    SE.BANT0 + 125), 2000)):
        A.png(w, cik + '/_a.png', px)
        R.png((w[0] + KR.DX_SEMA, w[1], w[2] + KR.DX_SEMA, w[3]), cik + '/_b.png', px)
        KR.yan_yana(cik + '/_a.png', cik + '/_b.png', '%s/%s.png' % (cik, ad), ('MOTOR (ROTAS-YI- blokları)',
                                                                                 'KULLANICI new_block'))
        print('[kirp]', ad)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else CIK)
