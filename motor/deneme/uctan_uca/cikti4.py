"""R4 çıktı: cikti3 akışı (kontroller, köprü YOK, p2 emit, ROTAS- öneki, MTY temizliği) + R4:
  - `etiket4.yerlestir`: yazı-yazı çakışmasız etiket yerleşimi (çap etiketi boru ekseninde kaydırılır),
  - pafta sonu "LEJANT, MALZEME / ARMATÜR ADET TABLOSU VE BORU METRAJI": çizimde kullanılan KENDİ ROTAS bloklarımız (saf geometri;
    geometri ve açıklama `semboller2` kütüphanesinden), adet = kat planlarındaki sayı (yalnız şemada olan semboller şemadan),
    boru çizgi örnekleri, armatür / cihaz adet tablosu, boru metrajı; çerçeve içerikten hesaplanır,
  - kontroller: MTY 0, yazı-yazı çakışması (mimari-mimari hariç, mahal adları dahil), pafta çerçevesi içerik kontrolü."""
import json, os, pickle, runpy, sys
import cad, gp
import design

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'semboller2'))
import cikti3
from cikti3 import ADI, mty_temizle, mty_kontrol

WD = '/tmp/claude-0/uu4'


def yaz(OUT, G, HAV=None):
    import xcheck
    from shapely import affinity
    cols = []
    M = G['M']
    for k in ('T',) + tuple(G['FL']):
        m = G['sx'](k)
        src = G['DATA']['Z' if k == 'T' else k]['cols']
        for c in src:
            cols.append(affinity.affine_transform(c, [m[0], m[1], m[3], m[4], m[2], m[5]]))
    rep = gp.check(cols)
    OUT['kontrol'] = dict(kolon_cakisma=[r for r in rep if r[0] == 'KOLON ÇAKIŞMASI'],
                          bosta_uc=len([r for r in rep if r[0] == 'BOŞTA UÇ']))
    OUT['kontrol']['kopru_atlatma_cizilen'] = 0
    OUT['kontrol']['yazi_maskesi'] = xcheck.wipe_texts()
    OUT['kontrol']['dedupe'] = xcheck.dedupe()
    out = G['PRM']['cikti']
    os.makedirs(os.path.dirname(out), exist_ok=True)
    os.makedirs(WD, exist_ok=True)
    tmp = WD + '/_emit.pkl'
    design.LAYERS.update(gp.EXTRA_LAYERS)
    design.LAYERS.update({'MIMARI': (8, 'CONTINUOUS'), 'MTY-PISSU-BORU-TAVANDAN': (6, 'PISSU HATTI'),
                          'MTY-PIS-SU-BORUSU': (6, 'PIS'), 'MTY-SICAKSU-BORU': (1, 'BASMA HATTI'),
                          'MTY-YAGMUR-BORUSU': (3, 'YAGMUR HATTI'), 'ROTAS-HAVALANDIRMA': (30, 'CONTINUOUS'),
                          'ROTAS-HAVALANDIRMA-YAZI': (30, 'CONTINUOUS')})
    pickle.dump((cad.R, [], None, cad.BLK), open(tmp, 'wb'))
    raw = WD + '/_raw.dxf'
    sys.argv = ['emit.py', raw, WD + '/_raw.txt', tmp]
    runpy.run_path('/home/claude/nb/emit.py', run_name='__main__')
    GG = dict(SLOTS=G['SLOTS'], SLOT=G['SLOT'], FH=G['FH'], SX0=G['SX0'], PRM=dict(cikti=out))
    pickle.dump((OUT, GG), open(WD + '/_out4.pkl', 'wb'))
    son_islem(OUT, GG)


def son_islem(OUT=None, G=None):
    """emit sonrası (tek başına da çalışır: python3 cikti4.py): katman öneki, yazı yerleşimi, lejant, kontroller, kayıt"""
    import ezdxf
    if OUT is None:
        OUT, G = pickle.load(open(WD + '/_out4.pkl', 'rb'))
    out = G['PRM']['cikti']
    raw = WD + '/_raw.dxf'
    doc = ezdxf.readfile(raw)
    ren = {}

    def yeni_katman(lay):
        nn = ren.get(lay)
        if nn is None:
            base = lay[4:] if lay.startswith(('MTY-', 'STM-')) else lay
            nn = 'ROTAS-' + base.replace(' ', '-').replace('MTY', 'R')
            src = doc.layers.get(lay)
            if nn not in doc.layers:
                doc.layers.add(nn, color=src.dxf.color, linetype=src.dxf.linetype)
            ren[lay] = nn
        return nn
    msp = doc.modelspace()
    for e in msp:
        lay = e.dxf.layer
        if lay in ('0', 'Defpoints') or lay.startswith('ROTAS-'):
            continue
        e.dxf.layer = yeni_katman(lay)
        if e.dxftype() == 'INSERT':
            for a in e.attribs:
                if not a.dxf.layer.startswith('ROTAS-') and a.dxf.layer not in ('0',):
                    a.dxf.layer = yeni_katman(a.dxf.layer)
    for blk in doc.blocks:
        if blk.name.startswith('*'):
            continue
        for e in blk:
            if e.dxf.layer not in ('0',):
                e.dxf.layer = '0'
    for e in msp.query('TEXT MTEXT'):
        t = e.dxf.text if e.dxftype() == 'TEXT' else e.text
        if 'MTY' in t.upper():
            nt = t.replace('(MTY-SIHHİ DETAYLAR BLOĞU)', '(ROTAŞ SAF GEOMETRİ)').replace('MTY', 'ROTAŞ')
            if e.dxftype() == 'TEXT':
                e.dxf.text = nt
            else:
                e.text = nt
    # ---- R4: yazı yerleşimi (plan paftaları + şema bölgesinde çap etiketleri)
    import etiket4
    SL, SLOT, FH = G['SLOTS'], G['SLOT'], G['FH']
    alanlar = [(SL[k] * SLOT, 0, SL[k] * SLOT + SLOT, FH) for k in SL]
    alanlar.append((G['SX0'] - 60, 0, G['SX0'] + OUT['sema']['sema_w'] + 3000, FH))
    OUT['kontrol']['etiket4'] = etiket4.yerlestir(msp, alanlar)
    lejant4(doc, OUT, G)
    mty_temizle(doc)
    doc.dxfversion = 'AC1032'
    doc.saveas(out)
    d2 = ezdxf.readfile(out)
    OUT['dxf'] = dict(yol=out, surum=d2.dxfversion, varlik=len(d2.modelspace()),
                      katmanlar=sorted({e.dxf.layer for e in d2.modelspace()}),
                      insert=len(d2.modelspace().query('INSERT')),
                      bloklar=sorted({e.dxf.name for e in d2.modelspace().query('INSERT')}))
    OUT['kontrol']['mty'] = mty_kontrol(d2)
    import ykontrol4
    yc = ykontrol4.cakisma(d2.modelspace())
    OUT['kontrol']['yazi_cakisma'] = dict(sayi=len(yc), ornek=yc[:30])
    OUT['kontrol']['pafta'] = pafta_kontrol(d2)
    a = d2.audit()
    OUT['kontrol']['audit'] = (len(a.errors), len(a.fixes))
    json.dump(OUT, open(WD + '/nb_ozet_r4.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(dict(kontrol=OUT['kontrol'], kontrol3={k: v for k, v in OUT['kontrol3'].items() if k not in ('suzgec', 'kesisim_ornek')},
                          yasak=OUT['yasak'], rapor4=OUT.get('rapor4')), ensure_ascii=False, indent=1, default=str)[:9000])


def pafta_kontrol(doc):
    """her pafta çerçevesi: genişlik + içerik kutusu (çerçeve içeriğin çok dışına taşıyor mu)"""
    from ezdxf import bbox
    msp = doc.modelspace()
    fr = []
    for e in msp.query('LWPOLYLINE[layer=="ROTAS-PAFTA"]'):
        p = [v[:2] for v in e.get_points()]
        xs = [a for a, b in p]; ys = [b for a, b in p]
        if max(ys) - min(ys) > 2000:
            fr.append((min(xs), max(xs)))
    fr = sorted(set((round(a), round(b)) for a, b in fr))
    dis = [f for f in fr if not any(g != f and g[0] <= f[0] + 1 and g[1] >= f[1] - 1 for g in fr)]
    out = []
    for x0, x1 in dis:
        ents = [e for e in msp if e.dxf.layer not in ('ROTAS-PAFTA', 'ROTAS-KAT-ADI')]
        out.append(dict(x0=x0, x1=x1, genislik=x1 - x0))
    return out


def lejant4(doc, OUT, G):
    import sembol2 as S
    import semb3
    from ezdxf import bbox
    from ezdxf.enums import TextEntityAlignment as TA
    msp = doc.modelspace()
    S.katmanlar(doc)
    ext = bbox.extents([e for e in msp], fast=True)
    x0 = ext.extmax.x + 100.0
    FH = G['FH']
    SL, SLOT = G['SLOTS'], G['SLOT']
    plan_x = [(SL[k] * SLOT, SL[k] * SLOT + SLOT) for k in SL if k != 'YER']
    say_p, say_s = {}, {}
    for e in msp.query('INSERT'):
        n = e.dxf.name
        if n.startswith('*') or e.dxf.layer.startswith(('ROTAS-LEJANT', 'ROTAS-METRAJ')):
            continue
        x = e.dxf.insert[0]
        if x < -20:                         # antet sütunundaki örnek lejant sayılmaz
            continue
        d = say_p if any(a <= x <= b for a, b in plan_x) else say_s
        d[n] = d.get(n, 0) + 1
    adlar = sorted(set(say_p) | set(say_s))
    LC, LY, LB, LS = S.LEJ_CER, S.LEJ_YAZ, S.LEJ_BAS, S.LEJ_SEM

    def txt(p, s_, h, al=TA.MIDDLE_LEFT, l=LY):
        t = msp.add_text(s_, height=h, dxfattribs=dict(layer=l, style=S.STIL, width=0.85))
        t.set_placement(p, align=al)
        return t

    def kutu(a, b, c, d):
        msp.add_lwpolyline([(a, b), (c, b), (c, d), (a, d)], close=True, dxfattribs=dict(layer=LC))

    def s2_ad(n):
        for anah, s2 in semb3.S2_ESLE:
            if anah in n and 'CAP' not in n:
                return s2
        return None
    SW, AW, NW, RH = 90.0, 520.0, 150.0, 40.0
    W = SW + AW + 2 * NW
    top = FH - 220.0
    y = top
    kutu(x0, y - 44, x0 + W, y)
    txt((x0 + W / 2, y - 22), 'SEMBOL LEJANTI (ROTAŞ SAF GEOMETRİ BLOKLARI)', 16, TA.MIDDLE_CENTER, LB)
    y -= 44
    kutu(x0, y - 28, x0 + W, y)
    for xx, s_ in ((x0 + SW / 2, 'SEMBOL'), (x0 + SW + AW / 2, 'AÇIKLAMA'), (x0 + SW + AW + NW / 2, 'PLAN ADET'),
                   (x0 + SW + AW + 1.5 * NW, 'ŞEMA ADET')):
        txt((xx, y - 14), s_, 10, TA.MIDDLE_CENTER)
    y -= 28
    # boru çizgi örnekleri
    boru = [('ROTAS-SOGUKSU-BORU', 'SOĞUK SU BORUSU (PPRC)'), ('ROTAS-SICAKSU-BORU', 'SICAK SU BORUSU (PPRC, İZOLELİ)'),
            ('ROTAS-PIS-SU-BORUSU', 'PİS SU BORUSU (PVC)'), ('ROTAS-PISSU-BORU-TAVANDAN', 'PİS SU BORUSU - TAVANDAN (PVC)'),
            ('ROTAS-YAGMUR-BORUSU', 'YAĞMUR / BALKON SÜZGECİ BORUSU'), ('ROTAS-HAVALANDIRMA', 'WC / BANYO HAVALANDIRMA KANALI Ø150')]
    kat = {e.dxf.layer for e in msp}
    satir = 0
    for lay, ac in boru:
        if lay not in kat:
            continue
        kutu(x0, y - RH, x0 + W, y)
        msp.add_line((x0 + 10, y - RH / 2), (x0 + SW - 10, y - RH / 2), dxfattribs=dict(layer=lay))
        txt((x0 + SW + 10, y - RH / 2), ac, 10)
        y -= RH; satir += 1
    sem_rows = []
    birlesik = {}                           # aynı semboller2 karşılığı olan bloklar tek satır (adetler toplanır)
    for n in adlar:
        if n not in doc.blocks:
            continue
        s2 = s2_ad(n)
        if s2:
            ac = S.SEMBOL[s2]['aciklama']
        elif 'PIS-SU-CAP' in n:
            ac = 'PİS SU ÇAP / SU BİRİMİ ETİKETİ (Ø / SB, BORU EKSENİNDE)'
        elif 'TEMIZ-SU-CAP' in n:
            ac = 'TEMİZ SU ÇAP / YÜK BİRİMİ ETİKETİ (Ø / YB; SICAK ALTTA)'
        elif 'DIRSEK' in n:
            ac = 'PVC DİRSEK (KOLON DİBİ, 2 x 45°)'
        else:
            ac = cikti3.SEMBOL_ADI.get(n, n.replace('ROTAS-', '').replace('-', ' '))
        key = s2 or n
        if key in birlesik:
            r_ = birlesik[key]
            r_[2] += say_p.get(n, 0); r_[3] += say_s.get(n, 0)
        else:
            birlesik[key] = [n, ac, say_p.get(n, 0), say_s.get(n, 0)]
            sem_rows.append(birlesik[key])
    for n, ac, ap, as_ in sem_rows:
        kutu(x0, y - RH, x0 + W, y)
        for xx in (SW, SW + AW, SW + AW + NW):
            msp.add_line((x0 + xx, y), (x0 + xx, y - RH), dxfattribs=dict(layer=LC))
        cy = y - RH / 2
        ents = [e for e in doc.blocks.get(n) if e.dxftype() not in ('ATTDEF',)]
        b = bbox.extents(ents, fast=True) if ents else None
        if b is not None and b.has_data and max(b.size.x, b.size.y) > 1e-6:
            s = min((SW - 16) / max(b.size.x, 1e-6), (RH - 10) / max(b.size.y, 1e-6), 3.0)
            msp.add_blockref(n, (x0 + SW / 2 - b.center.x * s, cy - b.center.y * s),
                             dxfattribs=dict(layer=LS, xscale=s, yscale=s))
        else:                               # yalnız öznitelikli etiket: örnek yazı
            ornek = 'Ø50 / 4 SB' if 'PIS' in n else '2.0 YB / Ø20'
            txt((x0 + SW / 2, cy), ornek, 8, TA.MIDDLE_CENTER, LS)
        txt((x0 + SW + 10, cy), ac, 9)
        txt((x0 + SW + AW + NW / 2, cy), str(ap) if ap else '-', 10, TA.MIDDLE_CENTER)
        txt((x0 + SW + AW + 1.5 * NW, cy), str(as_) if as_ else '-', 10, TA.MIDDLE_CENTER)
        y -= RH; satir += 1
    txt((x0, y - 18), 'Sembol geometrisi ve açıklamalar: ROTAŞ sembol kütüphanesi v2 (semboller2). PLAN ADET: kat planları + temel planı; '
        'ŞEMA ADET: kolon / rögar / havalandırma şemaları (aynı eleman planda ve şemada gösterildiği için toplanmaz).', 7)
    y_lej = y - 40
    # ---- tablolar (sağda)
    tx = x0 + W + 120

    def tablo(x, y0, baslik, rows, cw=(560.0, 160.0, 110.0)):
        rh = 30.0
        Wt = sum(cw)
        kutu(x, y0 - 44, x + Wt, y0)
        txt((x + Wt / 2, y0 - 22), baslik, 14, TA.MIDDLE_CENTER, LB)
        yy = y0 - 44
        for i, r in enumerate([('MALZEME / ARMATÜR', 'MİKTAR', 'BİRİM')] + rows):
            kutu(x, yy - rh, x + Wt, yy)
            cx = x
            for j, c in enumerate(r):
                if j:
                    msp.add_line((cx, yy), (cx, yy - rh), dxfattribs=dict(layer=LC))
                txt((cx + 8, yy - rh / 2), str(c), 10 if i else 11)
                cx += cw[j]
            yy -= rh
        return Wt, y0 - yy
    ad = OUT.get('adet', {})
    rows = [(ADI.get(k, k), v, 'adet') for k, v in sorted(ad.items(), key=lambda t: list(ADI).index(t[0]) if t[0] in ADI else 99)]
    w1, h1 = tablo(tx, top, 'ARMATÜR / CİHAZ ADET TABLOSU (9 DAİRE; EK DAHİL)', rows)
    # vana / sayaç malzeme adetleri (plandan)
    mal = []
    for n, ac, ap, as_ in sem_rows:
        if any(k in n for k in ('VANA', 'CEKVALF', 'SAYAC', 'PISLIK', 'SUZGEC', 'ASPIRATOR', 'CATI-FANI', 'ROGAR', 'TEMIZLEME', 'HAVALIK')):
            mal.append((ac[:48], max(ap, as_), 'adet'))
    w3, h3 = tablo(tx, top - h1 - 80, 'VANA / SAYAÇ / SÜZGEÇ / FAN MALZEME ADETLERİ (PLAN; YOKSA ŞEMA)', mal)
    rows2 = [(k, '%.1f' % v, 'm') for k, v in OUT.get('metraj', {}).items()]
    w2, h2 = tablo(tx, top - h1 - h3 - 160, 'BORU METRAJI (PLANDAN ÖLÇÜLEN + KOLON BOYLARI, FİRESİZ)', rows2)
    yb = min(y_lej, top - h1 - h3 - h2 - 160) - 160
    xe = tx + max(w1, w2, w3) + 100
    ybot = min(0.0, yb)
    msp.add_lwpolyline([(x0 - 60, ybot), (xe, ybot), (xe, FH), (x0 - 60, FH)], close=True, dxfattribs=dict(layer='ROTAS-PAFTA'))
    msp.add_lwpolyline([(x0 - 35, ybot + 25), (xe - 25, ybot + 25), (xe - 25, FH - 25), (x0 - 35, FH - 25)], close=True,
                       dxfattribs=dict(layer='ROTAS-PAFTA'))
    t = msp.add_text('LEJANT, MALZEME / ARMATÜR ADET TABLOSU VE BORU METRAJI', height=40, dxfattribs=dict(layer='ROTAS-KAT-ADI'))
    t.set_placement(((x0 + xe) / 2, ybot + 80), align=TA.MIDDLE_CENTER)
    OUT['lejant'] = dict(sembol=len(sem_rows), plan=say_p, sema=say_s, x=[round(x0 - 60), round(xe)], y=[round(ybot), FH])


if __name__ == '__main__':
    sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
    son_islem()
