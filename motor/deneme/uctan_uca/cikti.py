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
    json.dump(OUT, open(wd + '/nb_ozet.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(OUT, ensure_ascii=False, indent=1, default=str)[:6000])
