"""Kontroller (kolon çakışması, boşta uç, köprü, yazı maskesi) + DXF yazımı (p2 emit) + ROTAS- katman öneki + AC1032."""
import json, os, pickle, runpy, sys
import cad, gp
import design


def yaz(OUT, G):
    import xcheck
    from shapely import affinity
    # kolon çakışma kontrolü: kat planları ve temel (pafta koordinatına taşınmış betonarme kolonlar)
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
    xr = xcheck.crossings()
    OUT['kontrol']['kopru'] = xcheck.hops(xr)
    OUT['kontrol']['cakisik'] = len([r for r in xcheck.summary(xr) if r[0] == 'ÇAKIŞIK'])
    OUT['kontrol']['yazi_maskesi'] = xcheck.wipe_texts()
    OUT['kontrol']['dedupe'] = xcheck.dedupe()
    # ---- DXF
    out = G['PRM']['cikti']
    os.makedirs(os.path.dirname(out), exist_ok=True)
    wd = '/tmp/claude-0/uu'
    tmp = wd + '/_emit.pkl'
    design.LAYERS.update(gp.EXTRA_LAYERS)
    design.LAYERS.update({'MIMARI': (8, 'CONTINUOUS'), 'MTY-PISSU-BORU-TAVANDAN': (6, 'PISSU HATTI'),
                          'MTY-PIS-SU-BORUSU': (6, 'PIS'), 'MTY-SICAKSU-BORU': (1, 'BASMA HATTI'),
                          'MTY-YAGMUR-BORUSU': (3, 'YAGMUR HATTI')})
    pickle.dump((cad.R, [], None, cad.BLK), open(tmp, 'wb'))
    raw = wd + '/_raw.dxf'
    sys.argv = ['emit.py', raw, wd + '/_raw.txt', tmp]
    runpy.run_path('/home/claude/nb/emit.py', run_name='__main__')
    # ---- ROTAS- öneki (model uzayı varlıkları); MTY blok tanımlarının iç katmanları korunur. Sürüm AC1032 (R2018)
    import ezdxf
    doc = ezdxf.readfile(raw)
    ren = {}
    for e in doc.modelspace():
        lay = e.dxf.layer
        if lay in ('0', 'Defpoints') or lay.startswith('ROTAS-'):
            continue
        nn = ren.get(lay)
        if nn is None:
            base = lay[4:] if lay.startswith('MTY-') else lay[4:] if lay.startswith('STM-') else lay
            nn = 'ROTAS-' + base.replace(' ', '-')
            src = doc.layers.get(lay)
            if nn not in doc.layers:
                doc.layers.add(nn, color=src.dxf.color, linetype=src.dxf.linetype)
            ren[lay] = nn
        e.dxf.layer = nn
        if e.dxftype() == 'INSERT':
            for a in e.attribs:
                if not a.dxf.layer.startswith('ROTAS-') and a.dxf.layer not in ('0',):
                    a.dxf.layer = ren.get(a.dxf.layer, nn)
    # lejant, SIHHİ DETAYLAR bloğu eklenmeden önce sayılır (detay bloğunun içindeki örnek semboller kullanılan sayılmasın)
    lejant_ve_metraj(doc, OUT, G)
    if G.get('DETAY'):
        from ezdxf.addons import Importer
        src = ezdxf.readfile(G['M'].SRC)
        imp = Importer(src, doc)
        imp.import_block('MTY-SIHHİ DETAYLAR')
        imp.finalize()
        (px, py), ks = G['DETAY']
        if 'ROTAS-VANA' not in doc.layers:
            doc.layers.add('ROTAS-VANA', color=1)
        br = doc.modelspace().add_blockref('MTY-SIHHİ DETAYLAR', (0, 0), dxfattribs={'layer': 'ROTAS-VANA', 'xscale': ks, 'yscale': ks})
        from ezdxf import bbox
        ext = bbox.extents(br.virtual_entities())
        br.dxf.insert = (px - ext.extmin.x, py - ext.extmin.y)
        OUT['detay_boyut'] = (round(ext.size.x), round(ext.size.y))
    doc.dxfversion = 'AC1032'
    doc.saveas(out)
    d2 = ezdxf.readfile(out)
    msp_l = sorted({e.dxf.layer for e in d2.modelspace()})
    OUT['dxf'] = dict(yol=out, surum=d2.dxfversion, varlik=len(d2.modelspace()), katmanlar=msp_l,
                      insert=len(d2.modelspace().query('INSERT')))
    json.dump(OUT, open(wd + '/nb_ozet_r2.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(OUT, ensure_ascii=False, indent=1, default=str)[:6000])


ADI = dict(WC='Klozet / alaturka hela', LV='Lavabo', DUS='Duş teknesi', EV='Eviye', CM='Çamaşır makinesi bağlantısı',
           BM='Bulaşık makinesi bağlantısı', YS='Yer süzgeci (ıslak hacim)', KOMBI='Kombi (duvar tipi, yoğuşmalı)',
           BALKON_SUZGEC='Balkon süzgeci (yağmur hattına)')


def lejant_ve_metraj(doc, OUT, G):
    """pafta sonu: kullanılan sembollerin lejantı + adet tablosu (semboller/sembol.py otomatik_lejant) ve
    armatür / boru metraj tablosu; ikisi tek çerçevede "LEJANT VE MALZEME LİSTESİ"."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'semboller'))
    import sembol
    from ezdxf import bbox
    from ezdxf.enums import TextEntityAlignment as TA
    msp = doc.modelspace()
    ext = bbox.extents(msp, fast=True)          # detay paftasının çerçevesi dahil
    x0 = ext.extmax.x + 120.0
    FH = G['FH']
    top = FH - 160.0
    say = sembol.otomatik_lejant(doc, x0 + 60, top, baslik_onek='KULLANILAN SEMBOLLER - ')
    le = [e for e in msp if e.dxf.layer.startswith('ROTAS-LEJANT')]
    eb = bbox.extents(le, fast=True) if le else None
    tx = (eb.extmax.x + 120.0) if eb and eb.has_data else x0 + 60
    if 'ROTAS-METRAJ' not in doc.layers:
        doc.layers.add('ROTAS-METRAJ', color=7)
    lay = dict(layer='ROTAS-METRAJ')

    def txt(p, s_, h, al=TA.MIDDLE_LEFT):
        msp.add_text(s_, height=h, dxfattribs=lay).set_placement(p, align=al)

    def tablo(x, y, baslik, rows, cw=(520.0, 160.0, 120.0)):
        rh = 26.0
        W = sum(cw)
        txt((x, y + 22), baslik, 16)
        hdr = [('MALZEME / ARMATÜR', 'MİKTAR', 'BİRİM')] + rows
        for i, r in enumerate(hdr):
            yy = y - i * rh
            msp.add_lwpolyline([(x, yy), (x + W, yy)], dxfattribs=lay)
            cx = x
            for j, c in enumerate(r):
                txt((cx + 8, yy - rh / 2), str(c), 10 if i else 11)
                cx += cw[j]
        yb = y - len(hdr) * rh
        msp.add_lwpolyline([(x, yb), (x + W, yb)], dxfattribs=lay)
        cx = x
        for c in (0,) + tuple(cw):
            cx += c
            msp.add_lwpolyline([(cx, y), (cx, yb)], dxfattribs=lay)
        return W, y - yb
    ad = OUT.get('adet', {})
    rows = [(ADI.get(k, k), v, 'adet') for k, v in sorted(ad.items(), key=lambda t: list(ADI).index(t[0]) if t[0] in ADI else 99)]
    w1, h1 = tablo(tx, top, 'ARMATÜR / CİHAZ ADET TABLOSU (9 DAİRE, EK = MİMARİDE OLMAYIP EKLENEN DAHİL)', rows)
    rows2 = [(k, '%.1f' % v, 'm') for k, v in OUT.get('metraj', {}).items()]
    w2, h2 = tablo(tx, top - h1 - 110, 'BORU METRAJI (PLANDAN ÖLÇÜLEN + KOLON BOYLARI, FİRESİZ)', rows2)
    txt((tx, top - h1 - h2 - 160), 'Sembol adetleri çizimdeki blok sayımından otomatik (semboller/sembol.py otomatik_lejant).', 9)
    xe = tx + max(w1, w2) + 80
    ys = [e for e in le] if le else []
    yb = min(0.0, (eb.extmin.y - 60) if eb and eb.has_data else 0.0)
    msp.add_lwpolyline([(x0, yb), (xe, yb), (xe, FH), (x0, FH)], close=True, dxfattribs=dict(layer='ROTAS-PAFTA'))
    t = msp.add_text('LEJANT VE MALZEME LİSTESİ', height=40, dxfattribs=dict(layer='ROTAS-KAT-ADI'))
    t.set_placement(((x0 + xe) / 2, 120.0 if yb >= 0 else yb + 60), align=TA.MIDDLE_CENTER)
    OUT['lejant'] = dict(sembol_adet=say, x=[round(x0), round(xe)])
