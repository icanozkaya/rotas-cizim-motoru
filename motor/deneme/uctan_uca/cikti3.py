"""R3 çıktı: kontroller (kolon çakışması, boşta uç, yazı maskesi; KÖPRÜ/ATLATMA ÜRETİLMEZ) + p2 emit + ROTAS- katman
öneki + MTY temizliği (blok / katman / çizgi tipi / yazı adı 'MTY' içermez) + kullanılan sembol lejantı ve malzeme listesi."""
import json, os, pickle, runpy, sys
import cad, gp
import design

ADI = dict(WC='Klozet / alaturka hela', LV='Lavabo', DUS='Duş teknesi', EV='Eviye', CM='Çamaşır makinesi bağlantısı',
           BM='Bulaşık makinesi bağlantısı', YS='Yer süzgeci Ø50 (her ıslak hacimde 1)', KOMBI='Kombi (duvar tipi, yoğuşmalı)',
           BALKON_SUZGEC='Balkon süzgeci (ayrı yağmur hattına)', ASPIRATOR='WC/banyo aspiratörü 80 m³/h - 50 Pa - Ø150')
SEMBOL_ADI = {
    'ROTAS-KURESEL-VANA': 'Küresel vana', 'ROTAS-CEKVALF-VANA': 'Çek valf', 'ROTAS-PISLIK-TUTUCU': 'Pislik tutucu',
    'ROTAS-SU-SAYACI': 'Su sayacı', 'ROTAS-PIS-SU-KOLON': 'Pis su kolonu (plan)', 'ROTAS-KOLON-NO-PIS-SU': 'Pis su kolon no',
    'ROTAS-PIS-SU-KOLON-NO': 'Pis su kolon no (şema)', 'ROTAS-KOLON-NO-YAGMUR': 'Yağmur iniş no',
    'ROTAS-YER-SUZGECI-PLAN': 'Yer süzgeci Ø50 (plan)', 'ROTAS-SUZGEC': 'Balkon süzgeci', 'ROTAS-ASPIRATOR': 'WC/banyo aspiratörü',
    'ROTAS-CATI-FANI': 'Çatı tipi fan', 'ROTAS-PVC-ROGAR': 'Rögar', 'ROTAS-PVC-DIRSEK': 'PVC dirsek (kolon dibi)',
    'ROTAS-PVC-CATAL-SAG': 'PVC çatal', 'ROTAS-KOLON-HAVALIK-SAPKASI': 'Havalık şapkası',
    'ROTAS-TEMIZLEME-KAPAGI-KOLON': 'Temizleme kapağı', 'ROTAS-KOMBI-SEMA': 'Kombi (şema)', 'ROTAS-KOMBI': 'Kombi',
    'ROTAS-KLOZET-SEMA': 'Klozet (şema)', 'ROTAS-LAVABO-SEMA': 'Lavabo (şema)', 'ROTAS-DUS-TEKNESI-SEMA': 'Duş (şema)',
    'ROTAS-EVIYE-SEMA': 'Eviye (şema)', 'ROTAS-CAMASIR-MAKINESI-SEMA': 'Çamaşır makinesi (şema)',
    'ROTAS-BULASIK-MAKINESI-SEMA': 'Bulaşık makinesi (şema)', 'ROTAS-YER-SUZGECI-DN50-SEMA': 'Yer süzgeci (şema)',
    'ROTAS-KLOZET': 'Klozet', 'ROTAS-LAVABO': 'Lavabo', 'ROTAS-DUS-TEKNESI': 'Duş teknesi', 'ROTAS-EVIYE': 'Eviye',
    'ROTAS-CAMASIR-MAKINESI': 'Çamaşır makinesi', 'ROTAS-BULASIK-MAKINESI': 'Bulaşık makinesi',
    'ROTAS-YER-SUZGECI-DN50': 'Yer süzgeci', 'ROTAS-PIS-SU-CAP-SB': 'Pis su çap / SB etiketi',
    'ROTAS-TEMIZ-SU-CAP-MB': 'Temiz su çap / YB etiketi'}


def yaz(OUT, G, HAV=None):
    import xcheck
    from shapely import affinity
    import nb3
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
    OUT['kontrol']['kopru_atlatma_cizilen'] = 0          # R3: xcheck.hops ÇAĞRILMAZ (köprü yok)
    OUT['kontrol']['yazi_maskesi'] = xcheck.wipe_texts()
    OUT['kontrol']['dedupe'] = xcheck.dedupe()
    out = G['PRM']['cikti']
    os.makedirs(os.path.dirname(out), exist_ok=True)
    wd = '/tmp/claude-0/uu3'
    os.makedirs(wd, exist_ok=True)
    tmp = wd + '/_emit.pkl'
    design.LAYERS.update(gp.EXTRA_LAYERS)
    design.LAYERS.update({'MIMARI': (8, 'CONTINUOUS'), 'MTY-PISSU-BORU-TAVANDAN': (6, 'PISSU HATTI'),
                          'MTY-PIS-SU-BORUSU': (6, 'PIS'), 'MTY-SICAKSU-BORU': (1, 'BASMA HATTI'),
                          'MTY-YAGMUR-BORUSU': (3, 'YAGMUR HATTI'), 'ROTAS-HAVALANDIRMA': (30, 'CONTINUOUS'),
                          'ROTAS-HAVALANDIRMA-YAZI': (30, 'CONTINUOUS')})
    pickle.dump((cad.R, [], None, cad.BLK), open(tmp, 'wb'))
    raw = wd + '/_raw.dxf'
    sys.argv = ['emit.py', raw, wd + '/_raw.txt', tmp]
    runpy.run_path('/home/claude/nb/emit.py', run_name='__main__')
    import ezdxf
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
    for e in doc.modelspace():
        lay = e.dxf.layer
        if lay in ('0', 'Defpoints') or lay.startswith('ROTAS-'):
            continue
        e.dxf.layer = yeni_katman(lay)
        if e.dxftype() == 'INSERT':
            for a in e.attribs:
                if not a.dxf.layer.startswith('ROTAS-') and a.dxf.layer not in ('0',):
                    a.dxf.layer = yeni_katman(a.dxf.layer)
    for blk in doc.blocks:                          # blok içleri: yalnız 0 katmanı (saf geometri)
        if blk.name.startswith('*'):
            continue
        for e in blk:
            if e.dxf.layer not in ('0',):
                e.dxf.layer = '0'
    for e in doc.modelspace().query('TEXT MTEXT'):
        t = e.dxf.text if e.dxftype() == 'TEXT' else e.text
        if 'MTY' in t.upper():
            nt = t.replace('(MTY-SIHHİ DETAYLAR BLOĞU)', '(ROTAŞ SAF GEOMETRİ)').replace('MTY', 'ROTAŞ')
            if e.dxftype() == 'TEXT':
                e.dxf.text = nt
            else:
                e.text = nt
    lejant_ve_metraj(doc, OUT, G)
    mty_temizle(doc)
    doc.dxfversion = 'AC1032'
    doc.saveas(out)
    d2 = ezdxf.readfile(out)
    OUT['dxf'] = dict(yol=out, surum=d2.dxfversion, varlik=len(d2.modelspace()),
                      katmanlar=sorted({e.dxf.layer for e in d2.modelspace()}),
                      insert=len(d2.modelspace().query('INSERT')),
                      bloklar=sorted({e.dxf.name for e in d2.modelspace().query('INSERT')}))
    OUT['kontrol']['mty'] = mty_kontrol(d2)
    json.dump(OUT, open(wd + '/nb_ozet_r3.json', 'w'), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(dict(kontrol=OUT['kontrol'], kontrol3={k: v for k, v in OUT['kontrol3'].items() if k != 'suzgec'},
                          yasak=OUT['yasak'], dxf=OUT['dxf']), ensure_ascii=False, indent=1, default=str)[:6000])


def mty_temizle(doc):
    """kullanılmayan MTY katman / çizgi tipi / blok tanımlarını sil"""
    kull = {e.dxf.layer for e in doc.modelspace()}
    for blk in doc.blocks:
        for e in blk:
            kull.add(e.dxf.layer)
    for l in list(doc.layers):
        n = l.dxf.name
        if 'MTY' in n.upper() and n not in kull:
            doc.layers.remove(n)
    used_b = {e.dxf.name for e in doc.modelspace().query('INSERT')}
    for blk in list(doc.blocks):
        n = blk.name
        if 'MTY' in n.upper() and n not in used_b and not n.startswith('*'):
            doc.blocks.delete_block(n, safe=False)
    for lt in list(doc.linetypes):
        if 'MTY' in lt.dxf.name.upper():
            try:
                doc.linetypes.remove(lt.dxf.name)
            except Exception:
                pass


def mty_kontrol(doc):
    r = dict(blok=[b.name for b in doc.blocks if 'MTY' in b.name.upper()],
             katman=[l.dxf.name for l in doc.layers if 'MTY' in l.dxf.name.upper()],
             cizgi_tipi=[l.dxf.name for l in doc.linetypes if 'MTY' in l.dxf.name.upper()],
             insert=[e.dxf.name for e in doc.modelspace().query('INSERT') if 'MTY' in e.dxf.name.upper()],
             varlik_katmani=sorted({e.dxf.layer for e in doc.modelspace() if 'MTY' in e.dxf.layer.upper()}),
             blok_ici_katman=sorted({(b.name, e.dxf.layer) for b in doc.blocks if not b.name.startswith('*')
                                     for e in b if 'MTY' in e.dxf.layer.upper()}),
             yazi=[e.dxf.text for e in doc.modelspace().query('TEXT') if 'MTY' in e.dxf.text.upper()][:10])
    r['toplam'] = sum(len(v) for v in r.values())
    return r


def lejant_ve_metraj(doc, OUT, G):
    """pafta sonu: kullanılan ROTAS sembolleri (örnek + adet) + armatür adet tablosu + boru metrajı"""
    from ezdxf import bbox
    from ezdxf.enums import TextEntityAlignment as TA
    msp = doc.modelspace()
    ext = bbox.extents(msp, fast=True)
    x0 = ext.extmax.x + 120.0
    FH = G['FH']
    top = FH - 160.0
    for n in ('ROTAS-METRAJ', 'ROTAS-LEJANT'):
        if n not in doc.layers:
            doc.layers.add(n, color=7)
    lay = dict(layer='ROTAS-METRAJ')

    def txt(p, s_, h, al=TA.MIDDLE_LEFT, l='ROTAS-METRAJ'):
        msp.add_text(s_, height=h, dxfattribs=dict(layer=l)).set_placement(p, align=al)
    say = {}
    for e in msp.query('INSERT'):
        say[e.dxf.name] = say.get(e.dxf.name, 0) + 1
    txt((x0 + 60, top + 20), 'KULLANILAN SEMBOLLER (ROTAŞ SAF GEOMETRİ BLOKLARI) - ADETLİ', 16, l='ROTAS-LEJANT')
    yy = top - 40
    from ezdxf import bbox as bb_
    for n in sorted(say):
        if n not in doc.blocks:
            continue
        ref = msp.add_blockref(n, (0, 0), dxfattribs=dict(layer='ROTAS-LEJANT'))
        try:
            e2 = bb_.extents(ref.virtual_entities())
            s = 40.0 / max(e2.size.x, e2.size.y, 1e-6) if e2.has_data else 1.0
            ref.dxf.xscale = ref.dxf.yscale = s
            ref.dxf.insert = (x0 + 100 - (e2.center.x) * s, yy - (e2.center.y) * s)
        except Exception:
            ref.dxf.insert = (x0 + 100, yy)
        txt((x0 + 150, yy), '%s  —  %s  (%d adet)' % (SEMBOL_ADI.get(n, n), n, say[n]), 10, l='ROTAS-LEJANT')
        yy -= 58
    tx = x0 + 900

    def tablo(x, y, baslik, rows, cw=(560.0, 160.0, 120.0)):
        rh = 26.0
        W = sum(cw)
        txt((x, y + 22), baslik, 16)
        hdr = [('MALZEME / ARMATÜR', 'MİKTAR', 'BİRİM')] + rows
        for i, r in enumerate(hdr):
            yy_ = y - i * rh
            msp.add_lwpolyline([(x, yy_), (x + W, yy_)], dxfattribs=lay)
            cx = x
            for j, c in enumerate(r):
                txt((cx + 8, yy_ - rh / 2), str(c), 10 if i else 11)
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
    w1, h1 = tablo(tx, top, 'ARMATÜR / CİHAZ ADET TABLOSU (9 DAİRE; EK = MİMARİDE OLMAYIP EKLENEN DAHİL)', rows)
    rows2 = [(k, '%.1f' % v, 'm') for k, v in OUT.get('metraj', {}).items()]
    w2, h2 = tablo(tx, top - h1 - 110, 'BORU METRAJI (PLANDAN ÖLÇÜLEN + KOLON BOYLARI, FİRESİZ)', rows2)
    xe = tx + max(w1, w2) + 80
    yb = min(0.0, yy - 40)
    msp.add_lwpolyline([(x0, yb), (xe, yb), (xe, FH), (x0, FH)], close=True, dxfattribs=dict(layer='ROTAS-PAFTA'))
    t = msp.add_text('LEJANT VE MALZEME LİSTESİ', height=40, dxfattribs=dict(layer='ROTAS-KAT-ADI'))
    t.set_placement(((x0 + xe) / 2, 120.0 if yb >= 0 else yb + 60), align=TA.MIDDLE_CENTER)
    OUT['lejant'] = dict(sembol_adet=say, x=[round(x0), round(xe)])
