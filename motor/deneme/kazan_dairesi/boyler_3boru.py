# -*- coding: utf-8 -*-
"""ONAYLI kazan dairesi paftası (plan_kesit.onayli_kazan_dairesi) + boyler kullanım suyu 3 borulu bağlantısı
(soğuk su girişi / sıcak su çıkışı / sirkülasyon dönüşü) planda; uçlar kazan dairesi dışına AÇIK bırakılır.
Numaralar prensip şeması sırasından (cihaz listesiyle aynı): TM-11 sıcak su; V-22, V-49, V-08, EV-05 soğuk su;
V-23, P-08, V-09, V-24 sirkülasyon. Zon (IP-2) gidiş/dönüş uçları da açık (kullanıcının projesinde birleştirilecek).

Kullanım: python3 boyler_3boru.py girdi.json cikti.dxf [oda_genisligi_cm]
"""
import json
import sys

import ezdxf
from ezdxf import bbox
from ezdxf.enums import TextEntityAlignment as TA

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import plan_kesit as PK  # noqa: E402

SOG, SIC, SIR = 'ROTAS-SIHHI-SOGUK-SU', 'ROTAS-SIHHI-SICAK-SU', 'ROTAS-SIHHI-SIRKULASYON'
RENK = {SOG: (5, 'Continuous'), SIC: (1, 'Continuous'), SIR: (31, 'DASHDOT')}
KX, KY = 2150.0, 2330.0                     # boyler kesit detayı: eksen x, döşeme y (paftadaki boş alan)
VANA, POMPA, ETK, YAZ = 'ROTAS-ISITMA-VANA', 'ROTAS-ISITMA-POMPA', 'ROTAS-ISITMA-ETIKET', 'ROTAS-ISITMA-YAZI'


def main(girdi, cikti, genislik=None):
    P = json.load(open(girdi, encoding='utf-8'))
    if genislik:
        P['plan'] = PK.varsayilan_plan(P, genislik=float(genislik))
        P['plan']['temsili'] = bool(P.get('deneme', False))   # teslim paftasında DENEME başlığı yok
    doc = ezdxf.new('R2018', setup=True)
    doc.header['$INSUNITS'] = 5
    k = PK.onayli_kazan_dairesi(doc, P, 0, 0)
    msp = doc.modelspace()
    for ad, (c, lt) in RENK.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=c, linetype=lt)
    boy = P['boyler']
    dn_b = boy.get('cap', 'DN40')
    dn_r = (P.get('sirkulasyon') or {}).get('cap', 'DN25')
    # --- planda boyler (en büyük ölçekli BOYLER-PLAN; lejanttakiler küçük ölçekli)
    by = max((e for e in msp.query('INSERT') if e.dxf.name.startswith('ROTAS-KD-BOYLER-PLAN')), key=lambda e: e.dxf.xscale)
    b = bbox.extents([by])
    cx = (b.extmin.x + b.extmax.x) / 2
    r = (b.extmax.x - b.extmin.x) / 2
    cy = b.extmax.y - r - 3                     # gövde dairesi (alt ayaklar hariç)
    # --- alt (güney) duvar iç/dış yüzü: boylerin altındaki yatay duvar parçaları
    xs = [cx + 80, cx + 125, cx + 170]
    ys = []
    for e in msp.query('LWPOLYLINE'):
        if not e.dxf.layer.startswith('ROTAS-MIMARI-DUVAR'):
            continue
        p = list(e.get_points('xy'))
        for (x1, y1), (x2, y2) in zip(p, p[1:] + p[:1]):
            if abs(y1 - y2) < 0.1 and y1 < cy - 50 and min(x1, x2) <= xs[-1] + 20 and max(x1, x2) >= xs[0] - 20:
                ys.append(y1)
    ys = sorted(set(round(v, 1) for v in ys), reverse=True)
    yb, yo = ys[0], ys[1]                       # iç yüz, dış yüz
    y_uc = yo - 45                              # açık uç

    def hat(lay, pts):
        msp.add_lwpolyline(pts, dxfattribs={'layer': lay})

    def blok(ad, x, y, rot, lay, cap=None, olcek=1.0):
        e = msp.add_blockref(ad, (x, y), dxfattribs={'layer': lay, 'rotation': rot, 'xscale': olcek, 'yscale': olcek})
        if cap:
            e.add_auto_attribs({'CAP': cap})
            for a in e.attribs:
                a.dxf.invisible = 1
        return e

    def etiket(s, x, y, al=TA.MIDDLE_LEFT, h=9.0):
        t = msp.add_text(s, height=h, dxfattribs={'layer': ETK, 'style': 'ROTAS', 'width': 0.85})
        t.set_placement((x, y), align=al)

    # dairenin sağ-alt çeyreğinden çıkış kotları (üstten alta: sıcak, sirkülasyon, soğuk) → kesişmesiz dönüş
    import math
    dy = {SIC: -14.0, SIR: -27.0, SOG: -40.0}
    xt = {SOG: xs[0], SIR: xs[1], SIC: xs[2]}
    for lay in (SIC, SIR, SOG):
        y = cy + dy[lay]
        x0 = cx + math.sqrt(max(r * r - dy[lay] ** 2, 0.0))
        hat(lay, [(x0, y), (xt[lay], y), (xt[lay], y_uc)])
    # soğuk su (akış yukarı): V-22 küresel vana, V-49 pislik tutucu, V-08 çek valf, EV-05 emniyet ventili
    x = xt[SOG]
    blok('ROTAS-KD-KURESEL-VANA', x, yb + 28, 90, VANA, dn_b); etiket('V-22', x + 12, yb + 30, h=8.5)
    blok('ROTAS-KD-PISLIK-TUTUCU', x, yb + 56, 90, VANA, dn_b); etiket('V-49', x + 12, yb + 56, h=8.5)
    blok('ROTAS-KD-CEKVALF', x, yb + 86, 90, VANA, dn_b); etiket('V-08', x + 9, yb + 86, h=8.5)
    ev = blok('ROTAS-KD-EMNIYET-VENTILI', x, yb + 124, -90, VANA, 'DN20', 0.8)
    etiket('EV-05', x + 4, yb + 141, h=8.5)
    # sirkülasyon dönüşü (akış yukarı, boylere): V-23, P-08, V-09, V-24
    x = xt[SIR]
    blok('ROTAS-KD-KURESEL-VANA', x, yb + 32, 90, VANA, dn_r); etiket('V-23', x + 12, yb + 34)
    blok('ROTAS-POMPA', x, yb + 80, 90, POMPA); etiket('P-08', x + 15, yb + 80)
    blok('ROTAS-KD-CEKVALF', x, yb + 112, 90, VANA, dn_r); etiket('V-09', x + 12, yb + 112)
    blok('ROTAS-KD-KURESEL-VANA', x, yb + 142, 90, VANA, dn_r); etiket('V-24', x + 12, yb + 144)
    # sıcak su çıkışı (akış aşağı): TM-11
    x = xt[SIC]
    blok('ROTAS-KD-TERMOMETRE', x, yb + 70, -90, VANA)
    etiket('TM-11', x + 30, yb + 72)
    # akış okları ve açık uç yazıları (kazan dairesi dışında, düşey)
    for lay, yon, s in ((SOG, 90, f'ŞEBEKEDEN SOĞUK SU {dn_b} - UÇ AÇIK, PROJEDE BAĞLANACAK'),
                        (SIR, 90, f'SİRKÜLASYON DÖNÜŞÜ {dn_r} - UÇ AÇIK, PROJEDE BAĞLANACAK'),
                        (SIC, -90, f'KULLANIM SICAK SUYU {dn_b} - UÇ AÇIK, PROJEDE BAĞLANACAK')):
        x = xt[lay]
        msp.add_blockref('ROTAS-OK', (x, y_uc + (14 if yon == 90 else 0)), dxfattribs={'layer': lay, 'rotation': yon})
        t = msp.add_text(s, height=8, rotation=90, dxfattribs={'layer': YAZ, 'style': 'ROTAS', 'width': 0.85})
        t.set_placement((x, y_uc - 8), align=TA.MIDDLE_RIGHT)
    # metin güncellemeleri
    for t in msp.query('TEXT'):
        if t.dxf.text == 'BAĞLANTILARI ŞEMAYA GÖRE':
            t.dxf.text = '3 BORULU: S.SU / SİRK. / SOĞUK SU'
        elif t.dxf.text == '(TAVANDAN ZONA)':
            t.dxf.text = '(UÇ AÇIK - PROJEDE BAĞLANACAK)'
        elif t.dxf.text.startswith('IP-2 DÖNÜŞ'):
            t.dxf.text = t.dxf.text + ' - UÇ AÇIK'
    if 'ROTAS-OLCU' not in doc.layers:
        doc.layers.add('ROTAS-OLCU', color=3)
    kx = boyler_kesit(doc, KX, KY, P)
    doc.saveas(cikti)
    return k, (cx, cy, r, yb, yo, xt, kx)


def boyler_kesit(doc, x0, yz, P, F=2.0):
    """BY-01 düşey kesit detayı, ölçek 1/25 (model uzayında gerçek ölçü × F). x0: boyler ekseni, yz: ±0,00 döşeme."""
    import math
    msp = doc.modelspace()
    boy = P['boyler']
    dn_b = boy.get('cap', 'DN40')
    dn_r = (P.get('sirkulasyon') or {}).get('cap', 'DN25')
    Dd = PK.boyler_cap(boy['hacim_l'])                 # dış çap (izoleli), cm
    Di = Dd - 10.0                                      # tank çapı
    KA, AY, CAP_ = 10.0, 15.0, 12.0                     # kaide, ayak, bombe yüksekliği
    h_alt = KA + AY                                     # alt bombe başlangıcı
    h_sil = 4.0 * boy['hacim_l'] / 1000.0 / (math.pi * (Di / 100.0) ** 2) * 100.0 - CAP_   # silindir boyu
    h_ust = h_alt + CAP_ + h_sil                        # üst bombe başlangıcı
    h_tep = h_ust + CAP_
    X = lambda dx: x0 + dx * F
    Y = lambda h: yz + h * F
    CIH, GID, DON, DUV, TAR = 'ROTAS-ISITMA-CIHAZ', 'ROTAS-ISITMA-GIDIS', 'ROTAS-ISITMA-DONUS', 'ROTAS-MIMARI-DUVAR', 'ROTAS-MIMARI-TARAMA'
    BAS, KOT = 'ROTAS-ISITMA-BASLIK', 'ROTAS-KOT'
    for ad, (c, lt) in RENK.items():
        if ad not in doc.layers:
            doc.layers.add(ad, color=c, linetype=lt)

    def pl(pts, lay, close=False, lt=None):
        e = msp.add_lwpolyline(pts, close=close, dxfattribs={'layer': lay})
        if lt:
            e.dxf.linetype = lt
        return e

    def yaz(sx, sy, s, h=9.0, al=TA.MIDDLE_LEFT, lay=YAZ, rot=0.0):
        t = msp.add_text(s, height=h, rotation=rot, dxfattribs={'layer': lay, 'style': 'ROTAS', 'width': 0.85})
        t.set_placement((sx, sy), align=al)
        return t

    def kabuk(r, lay, lt=None):
        """silindir + iki eliptik bombe (yarım elips 24 parça)"""
        ust = [(X(r * math.cos(a)), Y(h_ust) + CAP_ * F * (r / (Dd / 2)) * math.sin(a))
               for a in [math.pi * i / 24 for i in range(25)]]
        alt = [(X(-r * math.cos(a)), Y(h_alt + CAP_) - CAP_ * F * (r / (Dd / 2)) * math.sin(a))
               for a in [math.pi * i / 24 for i in range(25)]]
        return pl(ust + alt, lay, True, lt)

    # döşeme, kaide, ayaklar
    pl([(X(-Dd / 2 - 110), yz), (X(Dd / 2 + 120), yz)], DUV)
    pl([(X(-Dd / 2 - 110), yz - 8 * F), (X(Dd / 2 + 120), yz - 8 * F)], DUV)
    hb = msp.add_hatch(color=8, dxfattribs={'layer': TAR})
    hb.paths.add_polyline_path([(X(-Dd / 2 - 110), yz - 8 * F), (X(Dd / 2 + 120), yz - 8 * F),
                                (X(Dd / 2 + 120), yz), (X(-Dd / 2 - 110), yz)], is_closed=True)
    hb.set_pattern_fill('ANSI31', scale=8.0)
    kd = [(X(-Dd / 2 - 5), Y(0)), (X(Dd / 2 + 5), Y(0)), (X(Dd / 2 + 5), Y(KA)), (X(-Dd / 2 - 5), Y(KA))]
    pl(kd, DUV, True)
    hk = msp.add_hatch(color=8, dxfattribs={'layer': TAR})
    hk.paths.add_polyline_path(kd, is_closed=True)
    hk.set_pattern_fill('AR-CONC', scale=0.6)
    for sx in (-1, 1):
        xa = sx * (Di / 2 - 12)
        pl([(X(xa - 3), Y(KA)), (X(xa + 3), Y(KA)), (X(xa + 3), Y(h_alt + 4)), (X(xa - 3), Y(h_alt + 4))], CIH, True)
    # gövde: tank + izolasyon (kesikli)
    kabuk(Di / 2, CIH)
    kabuk(Dd / 2, CIH, 'DASHED')
    # serpantin (primer, ısıtma suyu): şarj gidiş solda üstte, dönüş solda altta
    h_sg, h_sd = h_alt + CAP_ + 0.60 * h_sil, h_alt + CAP_ + 0.15 * h_sil
    n = 7
    zz = [(X(-Di / 2), Y(h_sg))]
    for i in range(n + 1):
        h = h_sg - (h_sg - h_sd) * (i + 0.5) / (n + 1)
        zz.append((X(Di / 2 - 12 if i % 2 == 0 else -Di / 2 + 12), Y(h)))
    zz.append((X(-Di / 2), Y(h_sd)))
    pl(zz, GID)
    yaz(X(0), Y(h_alt + CAP_ + 4), 'SERPANTİN (PRİMER)', 8, TA.MIDDLE_CENTER, CIH)

    # dış bağlantı: yatay boru + uç ok + yazı (+kot)
    def baglanti(lay, h, sag, uzun, metin, ok_ice=True, lt=None):
        xa = X(Dd / 2 if sag else -Dd / 2)
        xb = xa + (uzun if sag else -uzun)
        xi = X(Di / 2 if sag else -Di / 2)
        pl([(xi, Y(h)), (xb, Y(h))], lay, lt=lt)
        # ok: uçta, akış yönünü gösterir
        if ok_ice:
            msp.add_blockref('ROTAS-OK', (xb + (-14 if sag else 14), Y(h)), dxfattribs={'layer': lay, 'rotation': 180 if sag else 0})
        else:
            msp.add_blockref('ROTAS-OK', (xb, Y(h)), dxfattribs={'layer': lay, 'rotation': 0 if sag else 180})
        kot = f'{h / 100:+.2f}'.replace('.', ',')
        yaz(xb + (8 if sag else -8), Y(h) + 7, metin, 9, TA.MIDDLE_LEFT if sag else TA.MIDDLE_RIGHT)
        yaz(xb + (8 if sag else -8), Y(h) - 7, f'KOT {kot}', 8, TA.MIDDLE_LEFT if sag else TA.MIDDLE_RIGHT)
        return xa, xb

    def blok(ad, x, y, rot, lay, cap=None, olcek=1.5):
        e = msp.add_blockref(ad, (x, y), dxfattribs={'layer': lay, 'rotation': rot, 'xscale': olcek, 'yscale': olcek})
        if cap:
            e.add_auto_attribs({'CAP': cap})
            for a in e.attribs:
                a.dxf.invisible = 1
        return e

    def etk(s, x, y, al=TA.MIDDLE_CENTER):
        t = msp.add_text(s, height=9, dxfattribs={'layer': ETK, 'style': 'ROTAS', 'width': 0.85})
        t.set_placement((x, y), align=al)

    # sol: şarj gidiş / dönüş (P-07 hattı)
    xa, xb = baglanti(GID, h_sg, False, 150 * F / 2, f'ŞARJ GİDİŞ {dn_b} - 90 °C (P-07, V-12)')
    xa, xb = baglanti(DON, h_sd, False, 150 * F / 2, f'ŞARJ DÖNÜŞ {dn_b} - 70 °C (V-13)', ok_ice=False)
    # sağ: soğuk su girişi (alt), termostat cebi, sirkülasyon dönüşü (üst bölge)
    h_so = h_alt + CAP_ + 8
    xa, xb = baglanti(SOG, h_so, True, 200 * F / 2, f'SOĞUK SU GİRİŞİ {dn_b} - UÇ AÇIK')
    blok('ROTAS-KD-CEKVALF', xa + 70, Y(h_so), 180, VANA, dn_b, 1.2); etk('V-08', xa + 70, Y(h_so) - 24)
    blok('ROTAS-KD-PISLIK-TUTUCU', xa + 108, Y(h_so), 180, VANA, dn_b, 1.2); etk('V-49', xa + 108, Y(h_so) - 24)
    blok('ROTAS-KD-KURESEL-VANA', xa + 146, Y(h_so), 180, VANA, dn_b, 1.2); etk('V-22', xa + 146, Y(h_so) - 24)
    msp.add_lwpolyline([(xa + 30, Y(h_so)), (xa + 30, Y(h_so) + 22)], dxfattribs={'layer': SOG})
    blok('ROTAS-KD-EMNIYET-VENTILI', xa + 30, Y(h_so) + 22, 0, VANA, 'DN20', 1.0)
    etk('EV-05 (6 bar)', xa + 12, Y(h_so) + 66, TA.MIDDLE_LEFT)
    h_sr = h_alt + CAP_ + 0.80 * h_sil
    xa, xb = baglanti(SIR, h_sr, True, 200 * F / 2, f'SİRKÜLASYON DÖNÜŞÜ {dn_r} (P-08) - UÇ AÇIK')
    blok('ROTAS-KD-KURESEL-VANA', xa + 70, Y(h_sr), 180, VANA, dn_r); etk('V-24', xa + 70, Y(h_sr) - 24)
    h_tc = h_alt + CAP_ + 0.62 * h_sil
    pl([(X(Di / 2), Y(h_tc)), (X(Dd / 2) + 30, Y(h_tc))], CIH)
    msp.add_circle((X(Dd / 2) + 34, Y(h_tc)), 4, dxfattribs={'layer': CIH})
    yaz(X(Dd / 2) + 44, Y(h_tc), 'TERMOSTAT / TERMOMETRE CEBİ', 8)
    # üst: sıcak su çıkışı (tepeden yukarı, sağa) + TM-11, magnezyum anot
    h_ss = h_tep + 22
    pl([(X(0), Y(h_tep)), (X(0), Y(h_ss)), (X(Dd / 2) + 200 * F / 2, Y(h_ss))], SIC)
    xb = X(Dd / 2) + 200 * F / 2
    msp.add_blockref('ROTAS-OK', (xb, Y(h_ss)), dxfattribs={'layer': SIC, 'rotation': 0})
    yaz(xb + 8, Y(h_ss) + 7, f'KULLANIM SICAK SUYU {dn_b} - 60 °C - UÇ AÇIK', 9)
    yaz(xb + 8, Y(h_ss) - 7, f'KOT {h_ss / 100:+.2f}'.replace('.', ','), 8)
    blok('ROTAS-KD-TERMOMETRE', X(Dd / 2) + 60, Y(h_ss), 90, VANA, None, 1.2); etk('TM-11', X(Dd / 2) + 60, Y(h_ss) + 30)
    blok('ROTAS-KD-PURJOR', X(0), Y(h_ss), 90, VANA, None, 0.6)
    ha = h_alt + CAP_ + 0.68 * h_sil
    e = pl([(X(-18), Y(h_tep - 2)), (X(-18), Y(ha))], CIH, lt='DASHED')
    msp.add_line((X(-18), Y(h_tep - 2)), (X(-18), Y(h_tep + 4)), dxfattribs={'layer': CIH})
    yaz(X(-18) - 10, Y(h_tep + 12), 'MAGNEZYUM ANOT', 8, TA.MIDDLE_RIGHT)
    # boşaltma: alt bombe ortasından aşağı, sola, vana + yer süzgecine
    h_bo = h_alt + CAP_ + 3
    pl([(X(-Di / 2), Y(h_bo)), (X(-Dd / 2) - 85, Y(h_bo))], SOG)
    blok('ROTAS-KD-KURESEL-VANA', X(-Dd / 2) - 45, Y(h_bo), 180, VANA, 'DN25'); etk('BOŞALTMA DN25', X(-Dd / 2) - 45, Y(h_bo) + 24)
    yaz(X(-Dd / 2) - 92, Y(h_bo), 'YER SÜZGECİNE', 8, TA.MIDDLE_RIGHT)
    # kotlar ve ölçüler (gerçek ölçü yazılır)
    xk = X(-Dd / 2) - 150 * F / 2 - 225
    for h, s in ((0, '±0,00 BİTMİŞ DÖŞEME'), (KA, f'+{KA / 100:.2f} KAİDE'.replace('.', ',')),
                 (h_tep, f'+{h_tep / 100:.2f} BOYLER ÜSTÜ'.replace('.', ','))):
        msp.add_blockref('ROTAS-KOT', (xk, Y(h)), dxfattribs={'layer': KOT})
        yaz(xk + 30, Y(h) + 6, s, 9, lay=KOT)
    yo_ = yz - 26
    pl([(X(-Dd / 2), yo_), (X(Dd / 2), yo_)], 'ROTAS-OLCU')
    for xx in (X(-Dd / 2), X(Dd / 2)):
        msp.add_line((xx, yo_ - 8), (xx, yo_ + 8), dxfattribs={'layer': 'ROTAS-OLCU'})
    yaz(X(0), yo_ - 16, f'Ø{Dd:.0f} cm (İZOLELİ)  -  H = {h_tep:.0f} cm (KAİDE DAHİL)', 9, TA.MIDDLE_CENTER, 'ROTAS-OLCU')
    # başlık
    yaz(X(0), yz - 70, 'BOYLER (BY-01) KESİT DETAYI ......................... ÖLÇEK: 1 / 25', 20, TA.MIDDLE_CENTER, BAS)
    yaz(X(0), yz - 98, f'{boy["hacim_l"]:,.0f} L'.replace(',', '.') + f' - {boy.get("tip", "Serpantinli")} - izoleli - '
        f'primer 90/70 °C, kullanım 60 °C - 3 borulu (sıcak su / sirkülasyon / soğuk su)', 9, TA.MIDDLE_CENTER)
    return (X(-Dd / 2) - 150 * F / 2 - 160, yz - 100, xb + 300, Y(h_ss) + 80)


if __name__ == '__main__':
    print(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)[1])
