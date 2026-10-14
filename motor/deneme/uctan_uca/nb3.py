"""UÇTAN UCA SIHHİ DENEMESİ — R3 (14.10.2026 B revizyon talimatı).

R2 (nb.py + r2.py) tanıma / kolon / rögar / şema altyapısı aynen kullanılır; R3'te değişenler:
  1. MTY BLOĞU YOK: `semb3.kur()` her sembolü ROTAS- önekli SAF GEOMETRİ bloğuna yönlendirir (iç katman 0).
  2. Temiz su: ADK -> daire kapısı ana hattı ve daire içi hatlar koridor / mahal ORTASINDAN (maliyet alanı r3.Alan);
     sıcak su kombiden tek hat (dallanmasız), soğuk su ona 10 cm paralel; yalnız soğuk alan armatürler ve daire girişi
     soğuk taraftan tek branşman. Kesişme / köprü / atlatma YOK (ızgarada sıcak hat geçilemez).
  3. Pis su: 45° kırıklı omurga + 45° tekil branşman (balık sırtı); kolonlar "mek. havl." şaftı dışında.
  4. Her ıslak hacimde tam 1 yer süzgeci; balkon süzgeçleri ayrı hat (R2'den); ÇM mimarideki konumda.
  5. Kat planlarında WC/banyo aspiratörü + Ø150 bağlantı + şaft; kolon şemasının sağında havalandırma kolonları + çatı fanı.
  6. Elektrik kalemi yok.
Çalıştır:  cd /tmp/claude-0/uu && python3 nb3.py
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = '/home/claude/rotas-cizim-motoru'
sys.path.insert(0, HERE)
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
sys.argv = [sys.argv[0]]                        # nb.py argv'den params.json okur; R3 kendi parametreleriyle
import semb3
semb3.kur()
import nb
import r3
from shapely.geometry import LineString, Point, Polygon, box
import cad
from cad import L, PL, C, T, push, pop
import mtyblk
import gp
from gp import CS, CH, PS, PST, TSC, PSC, YL, YC, CD, YZ, cap_temiz, cap_pis, fmt, dn_temiz, dn_sb

M, RT, FL = nb.M, nb.RT, nb.FL
PRM = nb.PRM
PRM.update(cikti=REPO + '/proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R3.dxf', ara=10.0, tap=15.0)
HV, HVY = 'ROTAS-HAVALANDIRMA', 'ROTAS-HAVALANDIRMA-YAZI'
REG = []                    # (kat, grup, tip, LineString kaynak koord.) - kesişme kontrolü
RAPOR = dict(temiz={}, pis={}, suzgec={}, saft_kolon=[], kolon_kaydirma=[], havalandirma=[], uyari=[])
WET_ALL = ('banyo', 'wc+banyo', 'wc-banyo', 'wc-lvb.', 'duş', 'wc-duş', 'mutfak')


def reg(k, grp, tip, pts):
    if len(pts) >= 2:
        REG.append((k, grp, tip, LineString(pts)))


# ================================================================== ön işlem: tekrar eden ıslak hacim, şaftlar, süzgeç
def islak_tekrar(d):
    """aynı ad + daire, 120 cm içinde iki ıslak hacim kaydı: armatürsüz olanı at (2. kat wc-lvb. çift etiket)"""
    out = []
    for w in d['wet']:
        dup = [o for o in out if o['name'] == w['name'] and o.get('daire') == w.get('daire') and r3._d(o['xy'], w['xy']) < 120]
        if dup:
            o = dup[0]
            if not any(f['room'] is o for f in d['F']) and any(f['room'] is w for f in d['F']):
                out[out.index(o)] = w
            RAPOR['uyari'].append('%s kat: çift ıslak hacim etiketi %s D%s birleştirildi' % (d['k'], w['name'], w.get('daire')))
            continue
        out.append(w)
    d['wet'] = out


def saftlar(d):
    """'mek. havl.' yazısı -> yanındaki küçük daire (Ø kanal) -> ortogonal duvarlarla kapalı şaft dikdörtgeni"""
    import r2
    OW = r2.ortho_walls(d['W'])
    out = []
    for p in d['MEK']:
        cs = [a for a in d['R'] if a[0] == 'C' and 4.0 <= a[2] <= 12.0 and r3._d(a[1][0], p) < 60]
        c = min(cs, key=lambda a: r3._d(a[1][0], p))[1][0] if cs else (p[0] - 25, p[1])
        r = r2.rect_o(OW, c)
        g = box(*r) if (r[2] - r[0]) * (r[3] - r[1]) < 3000 else box(c[0] - 14, c[1] - 14, c[0] + 14, c[1] + 14)
        out.append(dict(c=c, g=g, yazi=p))
    d['SAFT'] = out


def kolonlari_saftan_cikar():
    """kural: pis su kolonu mekanik havalandırma şaftı içinden geçmez -> şaft dışına (duvar boyunca) ötele"""
    for c in nb.KOLS:
        p = c['p']
        sh = []
        for k in FL:
            o = M.OFF[k]
            sh += [Polygon([(x - o, y) for x, y in s['g'].exterior.coords]) for s in nb.DATA[k]['SAFT']]
        if not any(g.buffer(6).contains(Point(p)) for g in sh):
            continue
        DZ = nb.DATA['Z']
        best = None
        for izin in (0, 2):                 # önce aynı mahal içinde (duvar geçmeden) şaftın yanına, olmazsa duvara
            for v in r3.DIRS:
                for s in range(2, 120, 2):
                    q = (p[0] + v[0] * s, p[1] + v[1] * s)
                    if any(g.buffer(9).contains(Point(q)) for g in sh):
                        continue
                    if any(z['g'].buffer(15).contains(Point(q)) for z in DZ['YASAK']):
                        continue
                    if DZ['W'].cross(p, q) > izin + (1 if izin == 0 else 0):
                        break
                    ws_ = [w_ for w_ in DZ['wet'] if w_['name'] == c.get('wet')] or DZ['wet']
                    rc = min(ws_, key=lambda w_: r3._d(w_['xy'], p))['xy'] if c.get('kat_ozel') is None else p
                    sc = s + 0.8 * (r3._d(q, rc) - r3._d(p, rc))       # mahal içine doğru olan yön tercih
                    if best is None or sc < best[0]:
                        best = (sc, q, s)
                    break
            if best:
                break
        if best:
            RAPOR['kolon_kaydirma'].append((c['name'], [round(v) for v in p], [round(v) for v in best[1]], best[2]))
            c['p'] = best[1]


def suzgec_duzenle(d):
    """her ıslak hacimde tam 1 yer süzgeci: fazlası çıkarılır (kolona en yakını kalır), yoksa EK süzgeç eklenir"""
    rep = []
    for w in d['wet']:
        if w['name'] not in WET_ALL:
            continue
        kc = nb.kolon_of(d['k'], w)
        kp = (kc['p'][0] + M.OFF[d['k']], kc['p'][1]) if kc else w['xy']
        ys = [f for f in d['F'] if f['room'] is w and f['kind'] == 'YS']
        fx = [f for f in d['F'] if f['room'] is w and f['kind'] != 'YS']
        if len(ys) > 1:
            keep = min(ys, key=lambda f: r3._d(f['c'], kp))
            for f in ys:
                if f is not keep:
                    d['F'].remove(f)
            rep.append((w['name'], w.get('daire'), 'fazla %d çıkarıldı' % (len(ys) - 1)))
        elif not ys:
            x0, y0, x1, y1 = w['rect']
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            ev = [f for f in fx if f['kind'] == 'EV']
            hedef = (cx, cy)
            if w['name'] == 'mutfak' and ev:
                e = ev[0]['c']
                L_ = r3._d(e, (cx, cy)) or 1.0
                hedef = (e[0] + (cx - e[0]) * 55 / L_, e[1] + (cy - e[1]) * 55 / L_)
            best = None
            for i in range(-8, 9):
                for j in range(-8, 9):
                    q = (hedef[0] + i * 8, hedef[1] + j * 8)
                    if not (x0 + 22 <= q[0] <= x1 - 22 and y0 + 22 <= q[1] <= y1 - 22):
                        continue
                    if min([r3._d(q, f['c']) for f in fx] + [999]) < 38:
                        continue
                    if d['W'].cross(q, w['xy']) > 0:
                        continue
                    sc = r3._d(q, hedef)
                    if best is None or sc < best[0]:
                        best = (sc, q)
            q = best[1] if best else hedef
            d['F'].append(dict(kind='YS', c=q, room=w, daire=w.get('daire'), ek=True, axis=None))
            rep.append((w['name'], w.get('daire'), 'EK süzgeç eklendi'))
    RAPOR['suzgec'][d['k']] = rep


# ================================================================== pis su (balık sırtı)
def pis_ag3(k, d, w, kp):
    fx = [f for f in d['F'] if f['room'] is w and f['kind'] in nb.SB]
    if not fx:
        return 0, False
    YZG = [z['g'] for z in d['YASAK']]
    sh = [s['g'] for s in d['SAFT']]

    def maliyet(pts):
        ls = LineString(pts)
        c = sum(1 for i in d['W'].tree.query(ls) if d['W'].ls[i].intersects(ls)) * 15.0
        c += sum(1000 for g in YZG if ls.intersects(g.buffer(2)))
        c += sum(300 for g in sh if ls.intersection(g).length > 1.0)
        return c
    keyed = [(i, f['c']) for i, f in enumerate(fx)]
    spine, far, brs = r3.balik_sirti(keyed, kp, maliyet)
    sbf = {i: nb.SB[f['kind']] for i, f in enumerate(fx)}
    wcf = {i: f['kind'] == 'WC' for i, f in enumerate(fx)}
    # omurgayı branşman birleşim noktalarında böl
    spl = LineString(spine)
    cuts = sorted({round(spl.project(Point(br[-1])), 2) for key, br, tip in brs if tip == 'omurga'})
    s_list = [0.0] + [c for c in cuts if 0.5 < c < spl.length - 0.5] + [spl.length]
    grp = 'P:%s:%s:%d' % (k, w['name'], id(w) % 10000)

    def sub(a, b):
        from shapely.ops import substring
        g = substring(spl, a, b)
        return list(g.coords)
    for a_, b_ in zip(s_list[:-1], s_list[1:]):
        pts = r3.collinear(sub(a_, b_))
        up = [far] + [key for key, br, tip in brs if tip == 'omurga' and spl.project(Point(br[-1])) <= a_ + 0.6]
        s = sum(sbf[u] for u in up); wc = any(wcf[u] for u in up)
        gp.pipe(pts, PST, 'P'); reg(k, grp, 'PIS', pts)
        nb.METRAJ_ADD('PİS SU (PVC) Ø%d' % dn_sb(s, wc), pts)
        _etiket_pis(pts, s, wc)
    gp.node(spine[0], 'ARM'); gp.node(spine[-1], 'KOLON')
    for key, br, tip in brs:
        gp.node(br[0], 'ARM')
        gp.pipe(br, PST, 'P'); reg(k, grp, 'PIS', br)
        nb.METRAJ_ADD('PİS SU (PVC) Ø%d' % dn_sb(sbf[key], wcf[key]), br)
        _etiket_pis(br, sbf[key], wcf[key])
    tot = sum(sbf.values()); twc = any(wcf.values())
    RAPOR['pis'].setdefault(k, []).append((w['name'], w.get('daire'), len(fx), sum(1 for b in brs if b[2] == 'kolon')))
    return tot, twc


def _etiket_pis(pts, s, wc):
    pa, pb = max(zip(pts[:-1], pts[1:]), key=lambda q: r3._d(q[0], q[1]))
    if r3._d(pa, pb) >= 18:
        ang = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        cap_pis(((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2), ang, '%d SB' % s, 'Ø%d' % dn_sb(s, wc), PRM['k_cap'])


# ================================================================== temiz su
def tap(d, f):
    """armatür bağlantı noktası: en yakın duvara dik, duvardan PRM['tap'] cm"""
    p = f['c']
    dirs = ((1, 0), (-1, 0)) if f.get('axis') == 'x' else ((0, 1), (0, -1)) if f.get('axis') == 'y' else r3.DIRS
    dist, dn = nb.near_wall(d['W'], p, dirs)
    if dist > 90:
        return p
    t = max(0.0, dist - PRM['tap'])
    return (p[0] + dn[0] * t, p[1] + dn[1] * t)


def _vana(p, line_pts, k=0.22):
    ls = LineString(line_pts)
    s = ls.project(Point(p))
    a, b = ls.interpolate(max(0, s - 1)), ls.interpolate(min(ls.length, s + 1))
    ang = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
    q = ls.interpolate(s)
    mtyblk.insert('MTY-KURESEL VANA', (q.x, q.y), ang, k)


def sicak_yol(g, start, taps):
    """kombiden sıcak armatürlere TEK hat (eksen): her bacak önceki bacakların 14 cm bandına girmez"""
    cur = start
    legs, done, fail = [], [], []
    for t in taps:
        pth = None
        prev = [LineString(l) for l in legs if len(l) >= 2]
        for band in (14.0, 9.0, 6.0):
            m = None
            if prev:
                m = (r3.blok_cizgi(g, prev, band) & ~r3.disk(g, cur, band + 2.0)) | r3.blok_cizgi(g, prev, 5.0)
                m &= ~r3.disk(g, t, 6.0)
                m &= ~r3.disk(g, cur, 3.0)
            pth = g.route(cur, t, sysn='H', mask=m, free_end=0.1, cross=0.0, turn=8.0)
            if pth:
                break
        if not pth:
            fail.append(t); continue
        legs.append(pth); done.append(t); cur = t
    cen = []
    for l in legs:
        cen += l if not cen else l[1:]
    return r3.collinear(cen) if len(cen) >= 2 else cen, done, fail


def sira(start, items):
    """mahal mahal en yakın komşu sırası: items [(f, tap)]"""
    rem = list(items)
    out = []
    cur = start
    while rem:
        nx = min(rem, key=lambda t: r3._d(t[1], cur))
        room = nx[0]['room']
        grp = [t for t in rem if t[0]['room'] is room]
        while grp:
            q = min(grp, key=lambda t: r3._d(t[1], cur))
            out.append(q); grp.remove(q); rem.remove(q); cur = q[1]
    return out


def ana_hatlar(k, d, AL, o):
    """ADK kolonu -> daire kapısı: ortak alan, koridor ORTASI; ana hatlar birbirine 8 cm'den yaklaşmaz"""
    go = nb.router_for(k, d, ortak=True)
    go.base = AL.base.copy()
    go.block |= AL.block
    lines = []
    out = {}
    for dno in sorted(set(f.get('daire') for f in d['F'] if f.get('daire'))):
        ent = [w['entry'] for w in d['wet'] if w['daire'] == dno][0]
        dz = nb.daire_pos(k, dno)
        rk = [r for r in nb.RISERS.values() if dz in r['digits']][0]
        r0 = (rk['p'][0] + o, rk['p'][1])
        pth = None
        for band in (10.0, 6.0, None):
            m = None
            if lines and band:
                m = (r3.blok_cizgi(go, lines, band) & ~r3.disk(go, r0, band + 4)) | r3.blok_cizgi(go, lines, 3.0)
                m &= ~r3.disk(go, r0, 3.0)
            pth = go.route(r0, ent, sysn='A%d' % dno, mask=m, free_end=0.1, cross=0.0, turn=8.0)
            if pth:
                break
        if not pth:
            pth = RT.ortho([r0, (r0[0], ent[1]), ent])
            RAPOR['uyari'].append('%s kat D%d ana hat A* bulunamadı' % (k, dno))
        pth = r3.temizle(pth)
        lines.append(LineString(pth))
        out[dno] = pth
    return out, lines


def temiz_kat3(k, d):
    o = M.OFF[k]
    rooms, _ = M.rooms_of(nb.A, k)
    d['ROOMS'] = rooms
    AL = r3.Alan(RT, M, d, k, rooms)
    ANA, ana_lines = ana_hatlar(k, d, AL, o)
    d['_ANA'] = ana_lines
    res = {}
    for dno, p0 in ANA.items():
        ent = p0[-1]
        gp.pipe(p0, CS, 'S'); gp.node(p0[0], 'KOLON'); gp.node(p0[-1], 'GİRİŞ')
        reg(k, 'T:%s:%d' % (k, dno), 'SO', p0)
        nb.ANA_HAT.append((k, [cad.P(q) for q in p0]))
        nb.METRAJ_ADD('TEMİZ SU ANA HAT (PPRC) Ø25', p0)
        seg = max(zip(p0[:-1], p0[1:]), key=lambda s_: r3._d(*s_))
        ux = ((seg[1][0] - seg[0][0]) / (r3._d(*seg) or 1), (seg[1][1] - seg[0][1]) / (r3._d(*seg) or 1))
        ang = math.degrees(math.atan2(ux[1], ux[0]))
        a1, a2 = p0[-2], p0[-1]
        ul = r3._d(a1, a2) or 1.0
        u2 = ((a2[0] - a1[0]) / ul, (a2[1] - a1[1]) / ul)
        if ul > 30:
            mtyblk.insert('MTY-SU SAYACI', (ent[0] - u2[0] * 14, ent[1] - u2[1] * 14), math.degrees(math.atan2(u2[1], u2[0])), 0.45)
        nb.VANA(ent, 0.45, math.degrees(math.atan2(u2[1], u2[0])))
        res[dno] = daire_temiz(k, d, AL, dno, ent)
        ybt = sum(nb.YB[f['kind']] for f in d['F'] if f.get('daire') == dno and f['kind'] in nb.YB)
        sg = max(zip(p0[:-1], p0[1:]), key=lambda s_: r3._d(*s_))
        nb._cap_on(sg, 'D%d %s YB' % (dno, fmt(ybt)), 'Ø%d' % dn_temiz(ybt))
        res[dno]['yb'] = ybt
    RAPOR['temiz'][k] = res
    return res


def daire_temiz(k, d, AL, dno, ent):
    import numpy as np
    fx = [f for f in d['F'] if f.get('daire') == dno and f['kind'] in nb.YB and nb.YB[f['kind']] > 0]
    km = [f for f in d['F'] if f['kind'] == 'KOMBI' and f.get('daire') == dno]
    GG = type('G', (), dict(nx=AL.nx, ny=AL.ny, x0=AL.w[0], y0=AL.w[1], s=AL.step))
    mask = (AL.lab == dno) | r3.disk(GG, ent, 90.0)
    for f in km:
        mask |= r3.disk(GG, f['c'], 60.0)
    for f in fx:
        mask |= r3.disk(GG, tap(d, f), 35.0)
    sn = lambda p: (AL.w[0] + round((p[0] - AL.w[0]) / AL.step) * AL.step, AL.w[1] + round((p[1] - AL.w[1]) / AL.step) * AL.step)
    ii, jj = np.nonzero(mask)
    b = (AL.w[0] + ii.min() * AL.step - 20, AL.w[1] + jj.min() * AL.step - 20,
         AL.w[0] + ii.max() * AL.step + 20, AL.w[1] + jj.max() * AL.step + 20)
    g = AL.grid(mask, b)
    ent = sn(ent)
    hot = [(f, sn(tap(d, f))) for f in fx if f['kind'] in nb.YBS]
    cold_only = [(f, sn(tap(d, f))) for f in fx if f['kind'] not in nb.YBS]
    sysd = 'D%s%d' % (k, dno)
    grp = 'T:%s:%d' % (k, dno)
    out = dict(sicak_armatur=len(hot), soguk_branş=0, basarisiz=[])
    if hot and not km:
        cold_only += hot
        hot = []
    ana_blk = [l for l in d.get('_ANA', [])]

    def ana_maske(gx):
        if not ana_blk:
            return None
        return r3.blok_cizgi(gx, ana_blk, 5.0) & ~r3.disk(gx, ent, 7.0)

    def soguk_dallar(hotL, coldL, cen, adaylar):
        g2 = AL.grid(mask, b)
        branches = []
        blk = ana_maske(g2)
        if hotL:
            hb = r3.blok_cizgi(g2, [LineString(hotL)], 3.5)
            blk = hb if blk is None else (blk | hb)
            g2.add_line(coldL, 'S')
            items = sorted(adaylar, key=lambda t: -r3._d(t[1], ent)) + [(None, ent)]
        else:
            items = sorted(adaylar, key=lambda t: r3._d(t[1], ent))
            g2.add_line([ent, (ent[0] + 0.1, ent[1])], 'S')
        pend = list(items)
        for gecis in range(3):
            kalan = []
            for f, q in pend:
                pth = None
                if hotL and LineString(hotL).distance(Point(q)) < 6.0:
                    hl_ = LineString(hotL); pp_ = hl_.interpolate(hl_.project(Point(q)))
                    v_ = (q[0] - pp_.x, q[1] - pp_.y); n_ = math.hypot(*v_) or 1.0
                    q2 = sn((q[0] + v_[0] / n_ * 8.0, q[1] + v_[1] / n_ * 8.0))
                    if LineString(hotL).distance(Point(q2)) > LineString(hotL).distance(Point(q)):
                        q = q2
                if coldL and LineString(cen).distance(Point(q)) <= PRM['ara'] / 2 + 1.5:   # çift hattın üstünde: kısa dik bağlantı
                    cl = LineString(coldL)
                    pp = cl.interpolate(cl.project(Point(q)))
                    stub = [q, (pp.x, pp.y)]
                    sl = LineString(stub)
                    if r3._d(*stub) > 0.5 and not sl.intersects(LineString(hotL)) and \
                            not any(sl.distance(LineString(p_)) < 0.3 for _, p_ in branches):
                        pth = stub
                if pth is None:              # soğuk ağaca 6 cm'den yakın: doğrudan dik bağlantı (ızgara yuvarlaması kesişmesin)
                    agac = ([LineString(coldL)] if coldL else []) + [LineString(p_) for _, p_ in branches]
                    if agac:
                        ya = min(agac, key=lambda l_: l_.distance(Point(q)))
                        if 0.3 < ya.distance(Point(q)) < 6.0:
                            pp = ya.interpolate(ya.project(Point(q)))
                            stub = [q, (pp.x, pp.y)]
                            if not hotL or not LineString(stub).intersects(LineString(hotL)):
                                pth = stub
                if pth is None:
                    pth = g2.route(q, None, sysn='S', to_tree=True, mask=blk, free_end=0.1, cross=0.0, turn=8.0)
                if not pth:
                    kalan.append((f, q)); continue
                pth = r3.temizle(pth)
                agac = ([LineString(coldL)] if coldL else []) + [LineString(p_) for _, p_ in branches] + \
                    ([] if coldL or branches else [])
                pth = r3.agacta_kes(pth, agac)
                g2.add_line(pth, 'S')
                branches.append((f, pth))
            pend = kalan
            if not pend:
                break
        return branches, pend

    sec = None
    yol_ek = []                       # sıcak hattın yanında soğuk çift hatla dolaşılan soğuk-alan armatürler (kapalı kalanlar)
    for deneme in range(3):
        hotL = coldL = None
        cen, fail = [], []
        if km and hot:
            kc = sn(km[0]['c'])
            order = sira(kc, hot + yol_ek)
            gm = ana_maske(g)
            if gm is not None:
                g.block |= gm
            cen, done, fail = sicak_yol(g, kc, [t for _, t in order])
            cen = r3.duzelt(cen, [kc] + [t for _, t in order])
        for side in ((1, -1) if len(cen) >= 2 else (0,)):
            if side:
                h = r3.otele(cen, PRM['ara'] / 2 * side)
                c_ = r3.otele(cen, -PRM['ara'] / 2 * side)
                kes = (0 if LineString(h).is_simple else 1) + (0 if LineString(c_).is_simple else 1) + \
                      (0 if LineString(h).distance(LineString(c_)) > 1 else 5)
            else:
                h = c_ = None; kes = 0
            adaylar = [t for t in cold_only if all(t[0] is not e[0] for e in yol_ek)]
            br, pend = soguk_dallar(h, c_, cen, adaylar)
            puan = 20 * len(fail) + 10 * len(pend) + 5 * kes + sum(r3.plen(p) for _, p in br) / 400.0
            if sec is None or puan < sec[0]:
                sec = (puan, h, c_, cen, br, pend, fail, kes, list(yol_ek))
        if sec[0] < 5:
            break
        yeni = [(f, q) for f, q in sec[5] if f is not None]
        if not yeni or not (km and hot):
            break
        yol_ek = sec[8] + [(f, q) for f, q in cold_only if any(f is e[0] for e in yeni)]
    _, hotL, coldL, cen, branches, pend, fail, kes, yol_ek = sec
    out['basarisiz'] += ['sıcak %s' % [round(v) for v in t] for t in fail]
    if kes:
        out['basarisiz'].append('öteleme kendini kesiyor (%d)' % kes)
    for f, q in pend:
        out['basarisiz'].append('soğuk %s' % (f['kind'] if f else 'GİRİŞ'))
    out['cift_hatta_alinan_soguk'] = [f['kind'] for f, _ in yol_ek]
    # ---- çizim
    colds = ([coldL] if coldL else []) + [p for _, p in branches]
    for c_ in colds:
        gp.node(c_[0], 'ARM'); gp.node(c_[-1], 'ARM')
        gp.pipe(c_, CS, sysd); reg(k, grp, 'SO', c_)
        nb.METRAJ_ADD('TEMİZ SU SOĞUK (PPRC)', c_)
    if hotL:
        gp.node(hotL[0], 'KOMBİ'); gp.node(hotL[-1], 'ARM')
        gp.pipe(hotL, CH, sysd + 'H'); reg(k, grp, 'SC', hotL)
        nb.METRAJ_ADD('TEMİZ SU SICAK (PPRC, izoleli)', hotL)
        T((km[0]['c'][0] + 8, km[0]['c'][1] - 14), 'KOMBİ %d kW' % PRM['kombi_kw'], 6, CD, 'L')
    # vanalar: sıcak armatürde iki hatta, soğuk alanlarda branşman ucunda
    for f, t in hot:
        if hotL:
            _vana(t, hotL); _vana(t, coldL)
    for f, t in yol_ek:
        if coldL:
            _vana(t, coldL)
    for f, pth in branches:
        if f is not None:
            _vana(pth[0], pth[:2] if r3._d(pth[0], pth[1]) > 0.5 else pth)
    out['soguk_branş'] = len(branches)
    _etiketler(k, d, hot, yol_ek, hotL, coldL, branches, ent)
    return out


def _etiketler(k, d, hot, yol_ek, hotL, coldL, branches, ent):
    """soğuk ağaç parçalarına 'x YB / Øy' (+ paralel sıcak varsa SC); yükler girişten akış yönünde"""
    import networkx as nx
    lines = ([coldL] if coldL else []) + [p for _, p in branches]
    if not lines:
        return
    # düğümler: tüm uç noktalar + armatür soğuk bağlantıları
    poi = []
    for l in lines:
        poi += [l[0], l[-1]]
    fx_c = []
    for f, t in list(hot) + list(yol_ek):
        if coldL:
            cl = LineString(coldL); q = cl.interpolate(cl.project(Point(t)))
            poi.append((q.x, q.y)); fx_c.append((nb.YB[f['kind']], (q.x, q.y)))
    for f, p in branches:
        if f is not None:
            fx_c.append((nb.YB[f['kind']], p[0]))
    G = nx.Graph()
    key = lambda p: (round(p[0], 1), round(p[1], 1))
    for l in lines:
        ls = LineString(l)
        ss = sorted({0.0, ls.length} | {round(ls.project(Point(p)), 3) for p in poi if ls.distance(Point(p)) < 0.8})
        from shapely.ops import substring
        for a, b in zip(ss[:-1], ss[1:]):
            if b - a < 0.3:
                continue
            seg = list(substring(ls, a, b).coords)
            G.add_edge(key(seg[0]), key(seg[-1]), pts=seg, w=b - a)
    if not G.nodes:
        return
    root = min(G.nodes, key=lambda n: r3._d(n, ent))
    load = {}
    for yb, p in fx_c:
        n = min(G.nodes, key=lambda n_: r3._d(n_, p))
        try:
            path = nx.shortest_path(G, root, n, weight='w')
        except Exception:
            continue
        for a, b in zip(path[:-1], path[1:]):
            e = tuple(sorted((a, b)))
            load[e] = load.get(e, 0.0) + yb
    hl = LineString(hotL) if hotL else None
    hot_pos = []
    if hl:
        for f, t in hot:
            hot_pos.append((hl.project(Point(t)), nb.YBS[f['kind']]))
    for (a, b), v in load.items():
        pts = G.edges[a, b]['pts']
        sg = max(zip(pts[:-1], pts[1:]), key=lambda s_: r3._d(*s_))
        if r3._d(*sg) < 40:
            continue
        m = ((sg[0][0] + sg[1][0]) / 2, (sg[0][1] + sg[1][1]) / 2)
        if hl is not None and hl.distance(Point(m)) <= PRM['ara'] + 1:
            s = hl.project(Point(m))
            hv = sum(y for sp, y in hot_pos if sp >= s - 0.5)
            if hv > 0:
                nb._cap_on(sg, '%s YB' % fmt(v), 'Ø%d' % dn_temiz(v), '%s YB' % fmt(hv), 'Ø%d' % dn_temiz(hv))
                continue
        nb._cap_on(sg, '%s YB' % fmt(v), 'Ø%d' % dn_temiz(v))


def zemin_sebeke3(d):
    """şebeke -> ana sayaç -> DBK: ortak alan, ana hatlara 8 cm'den yaklaşmadan (kesişmesiz)"""
    bg = [a[1][0] for a in d['R'] if a[0] == 'T' and 'bina' in a[2][0] and 'giri' in a[2][0]]
    if not (bg and nb.DBK):
        return
    e = bg[0]
    g = nb.router_for('Z', d, ortak=True)
    sebeke = (M.WIN_Z[2] - 5.0, e[1])
    lines = [ls for k_, g_, t_, ls in REG if k_ == 'Z' and t_ in ('SO', 'SC')]
    DB = Point(nb.DBK)
    pth = None
    W = d['W']
    rms = [r['poly'].buffer(-8) for r in d.get('ROOMS', []) if r['name'].split()[0] in
           ('salon', 'yatak', 'oda', 'yüklük', 'mutfak', 'banyo', 'wc+banyo', 'wc-lvb.', 'duş') and r['area'] <= 40]
    adaylar = [[sebeke, (nb.DBK[0], sebeke[1]), nb.DBK], [sebeke, (sebeke[0], nb.DBK[1]), nb.DBK]]
    for xm in range(int(min(sebeke[0], nb.DBK[0])), int(max(sebeke[0], nb.DBK[0])), 10):
        adaylar.append([sebeke, (xm, sebeke[1]), (xm, nb.DBK[1]), nb.DBK])
    for ym in range(int(min(sebeke[1], nb.DBK[1])) - 300, int(max(sebeke[1], nb.DBK[1])) + 300, 10):
        adaylar.append([sebeke, (sebeke[0] - 40, sebeke[1]), (sebeke[0] - 40, ym), (nb.DBK[0], ym), nb.DBK])
    best = None
    for c_ in adaylar:
        c_ = RT._collinear(c_)
        ls = LineString(c_)
        core = ls.difference(DB.buffer(26))
        ceza = sum(1000 for l in lines if core.distance(l) < 4) + sum(1000 for z in d['YASAK'] if ls.intersects(z['g'].buffer(3)))
        ceza += sum((500 if ls.intersection(r).length > 30 else 3 * ls.intersection(r).length) for r in rms)
        ceza += 10 * sum(1 for i in W.tree.query(ls) if W.ls[i].intersects(ls)) + ls.length / 100 + 2 * len(c_)
        if best is None or ceza < best[0]:
            best = (ceza, c_)
        if len(RAPOR.setdefault('seb_aday', [])) < 2:
            RAPOR['seb_aday'].append(dict(temiz=[round(core.distance(l), 1) for l in lines if core.distance(l) < 4],
                                          yasak=[z['tip'] for z in d['YASAK'] if ls.intersects(z['g'].buffer(3))],
                                          oda=[round(ls.intersection(r).length) for r in rms if ls.intersection(r).length > 1]))
    if best and best[0] < 500:
        pth = best[1]
    RAPOR['seb'] = dict(ceza=round(best[0], 1) if best else None, nokta=len(pth) if pth else 0)
    if pth is None:
        m = r3.blok_cizgi(g, lines, 6.0) & ~r3.disk(g, nb.DBK, 8.0) if lines else None
        for r in rms:
            from skimage.draw import polygon as skp
            xs, ys = r.exterior.coords.xy if r.geom_type == 'Polygon' else max(r.geoms, key=lambda q: q.area).exterior.coords.xy
            rr, cc = skp([(x - g.x0) / g.s for x in xs], [(y - g.y0) / g.s for y in ys], (g.nx, g.ny))
            if m is None:
                import numpy as np
                m = np.zeros_like(g.block)
            m[rr, cc] = True
        pth = g.route(sebeke, nb.DBK, sysn='SEB', mask=m, free_end=0.1, cross=0.0, turn=8.0)
    if not pth:
        pth = RT._collinear([sebeke, (nb.DBK[0], sebeke[1]), nb.DBK])
        RAPOR['uyari'].append('şebeke hattı A* bulunamadı, düz çizildi')
    gp.pipe(pth, CS, 'S'); gp.node(pth[0], 'ŞEBEKE'); gp.node(pth[-1], 'DBK')
    reg('Z', 'SEB', 'SO', pth)
    nb.ANA_HAT.append(('Z', [cad.P(q) for q in pth]))
    nb.METRAJ_ADD('TEMİZ SU ŞEBEKE / DBK (PPRC) Ø32', pth)
    nb.VANA((sebeke[0] - 15, sebeke[1]), 0.5, 0); nb.PISLIK_TUTUCU((sebeke[0] - 30, sebeke[1]), 0.45, 0)
    mtyblk.insert('MTY-SU SAYACI', (sebeke[0] - 46, sebeke[1]), 0, 0.3); nb.CEKVALF((sebeke[0] - 62, sebeke[1]), 0.45, 0)
    T((sebeke[0] - 70, sebeke[1] + 12), 'ŞEBEKE Ø32 - ANA SAYAÇ (BİNA GİRİŞİ) → DBK → ÇATI DEPOSU', 6, TSC, 'R')


# ================================================================== havalandırma (kat planı)
HAV = {}


def havalandirma_hesap():
    sys.path.insert(0, REPO + '/motor/deneme/wc_havalandirma')
    from algila import algila
    from hesap import hesapla
    g = algila()
    g['kabul']['oda_basina_aspirator'] = True       # planda her penceresiz hacimde kendi aspiratörü
    g['deneme'] = True
    r = hesapla(g)
    HAV.update(girdi=g, sonuc=r)
    return g, r


def havalandirma_plan(k, d):
    g, r = HAV['girdi'], HAV['sonuc']
    o = M.OFF[k]
    sxy = {s['ad']: (s['xy'][0] + o, s['xy'][1]) for s in g['saftlar']}
    n = 0
    for s in r['saftlar']:
        for a in s['asps']:
            if a['kat'] != k:
                continue
            sp = sxy[s['ad']]
            sh = min(d['SAFT'], key=lambda q: r3._d(q['yazi'], sp)) if d['SAFT'] else None
            for m in a['mahaller']:
                ws = [w for w in d['wet'] if w['name'] == m['ad']]
                if not ws or sh is None:
                    continue
                w = min(ws, key=lambda w_: r3._d(w_['xy'], sh['c']))
                x0, y0, x1, y1 = w['rect']
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                c = sh['c']
                L_ = r3._d(c, (cx, cy)) or 1.0
                ap = (c[0] + (cx - c[0]) * min(48, L_ - 10) / L_, c[1] + (cy - c[1]) * min(48, L_ - 10) / L_)
                ap = (min(max(ap[0], x0 + 14), x1 - 14), min(max(ap[1], y0 + 14), y1 - 14))
                # şafttan aspiratöre Ø150 bağlantı (önce şaft kenarına)
                e = sh['g'].exterior
                q = e.interpolate(e.project(Point(ap)))
                PL([(q.x, q.y), ap], HV, w=4.0)
                mtyblk.insert('ROTAS-ASPIRATOR', ap, 0, 1.0)
                T((ap[0] + 13, ap[1] + 3), 'WC ASPİRATÖRÜ %d m³/h - 50 Pa' % a['q'], 5.0, HVY, 'L')
                T((ap[0] + 13, ap[1] - 5), 'Ø150 → %s (%s)' % (s['ad'], s['daireler']), 5.0, HVY, 'L')
                n += 1
                RAPOR['havalandirma'].append((k, s['ad'], m['ad'], m['daire'], a['q']))
    for sh in d['SAFT']:
        PL(list(sh['g'].exterior.coords), HV, True, 1.0)
        ad = None
        for s in g['saftlar']:
            if r3._d((s['xy'][0] + o, s['xy'][1]), sh['yazi']) < 60:
                ad = s['ad']
        if ad:
            c = sh['g'].centroid
            T((c.x, c.y + 18), '%s MEK. HAVL. ŞAFTI' % ad, 5.0, HVY, 'C')
    return n


def suzgec_ciz(k, d):
    n = 0
    for w in d['wet']:
        for f in d['F']:
            if f['room'] is w and f['kind'] == 'YS':
                mtyblk.insert('ROTAS-YER-SUZGECI-PLAN', f['c'], 0, 0.8)
                if f.get('ek'):
                    T((f['c'][0] + 10, f['c'][1] - 12), 'Y.S. Ø50 (EK)', 5, CD, 'L')
                n += 1
    return n


# ================================================================== kat planı
def kat_plani3(k):
    d = nb.DATA[k]
    push(nb.sx(k))
    i0 = len(cad.R)
    nb.copy_arch(k, d['R'])
    o = M.OFF[k]
    stats = dict(kolon={}, temiz=None)
    nb.ek_cihaz_ciz(d)
    for w in d['wet']:
        kc = nb.kolon_of(k, w)
        kp = (kc['p'][0] + o, kc['p'][1])
        sb, wc = pis_ag3(k, d, w, kp)
        stats['kolon'][kc['name']] = stats['kolon'].get(kc['name'], 0) + sb
    stats['suzgec'] = suzgec_ciz(k, d)
    kps = []
    for kc in nb.KOLS:
        kp = (kc['p'][0] + o, kc['p'][1])
        mtyblk.insert('MTY-PIS SU KOLON', kp, 0, 0.5)
        gp.node(kp, kc['name'])
        sb_here = sum(nb.STATS_SB[kc['name']].get(f, 0) for f in FL[FL.index(k):])
        kps.append((kc['name'], kp, 'Ø%d / %d SB' % (kc['dn'], sb_here)))
        for sh in d['SAFT']:
            if sh['g'].buffer(3).contains(Point(kp)):
                RAPOR['saft_kolon'].append((k, kc['name']))
    for r in nb.RISERS.values():
        p = (r['p'][0] + o, r['p'][1])
        gp.kolon_temiz(p, r=3.0); T((p[0] + 6, p[1] + 6), r['name'], 6, TSC, 'L')
    if nb.DBK:
        p = (nb.DBK[0] + o, nb.DBK[1])
        gp.kolon_temiz(p, r=3.0); T((p[0] + 6, p[1] - 12), 'DBK', 6, TSC, 'L')
    stats['temiz'] = temiz_kat3(k, d)
    stats['balkon_suzgec'] = nb.balkon_ciz(k, d, o)
    for i, p in enumerate(nb.YBP):
        q = (p[0] + o, p[1])
        cad.YB_PLAN(q, 6.0, YL)
        mtyblk.insert('MTY-KOLON NO YAGMUR', (q[0] + 26, q[1] + 26), 0, 0.5, attrs={'K': 'YB%d' % (i + 1)})
    if k == 'Z':
        zemin_sebeke3(d)
    stats['havalandirma'] = havalandirma_plan(k, d)
    stats['kolon_etiket'] = nb.kolon_etiketleri(k, i0, kps)
    pop()
    T((nb.SLOTS[k] * nb.SLOT + nb.SLOT / 2, 120.0), '%s SIHHİ TESİSAT PLANI..........ÖLÇEK: 1 / 50' % nb.FNAME[k], 40, 'MTY-KAT-ADI', 'C')
    return stats


def balkon_kayit():
    """balkon süzgeç hatları (gp.NET'te 'B..' sistemleri) kesişme kontrolüne kaynak koordinatla"""
    for k in FL:
        m = nb.sx(k)
        a, b_, c, d_, e, f = m
        det = a * e - b_ * d_
        inv = lambda p: ((e * (p[0] - c) - b_ * (p[1] - f)) / det, (-d_ * (p[0] - c) + a * (p[1] - f)) / det)
        w = M.win(k)
        for n in gp.NET:
            if n['lay'] != YL or not str(n['sys']).startswith('B'):
                continue
            pts = [inv(p) for p in n['pts']]
            if w[0] - 5 <= pts[0][0] <= w[2] + 5 and w[1] - 5 <= pts[0][1] <= w[3] + 5:
                reg(k, 'BALKON:%s:%s' % (k, n['sys']), 'BALKON', pts)


# ================================================================== çalıştır
def main():
    for k in FL:
        d = nb.DATA[k]
        islak_tekrar(d)
        saftlar(d)
    for k in FL:
        for w in nb.DATA[k]['wet']:
            nb.kolon_of(k, w)
    from shapely import affinity
    hull = nb.bina_hatti()
    for k in FL:
        nb.DATA[k]['HULL'] = affinity.translate(hull, M.OFF[k], 0)
    kolonlari_saftan_cikar()
    for k in FL:
        suzgec_duzenle(nb.DATA[k])
    havalandirma_hesap()
    nb.RISERS = nb.riser_gruplari()
    DZ = nb.DZ
    bg = [a[1][0] for a in DZ['R'] if a[0] == 'T' and 'bina' in a[2][0] and 'giri' in a[2][0]]
    if bg:
        r = min(nb.RISERS.values(), key=lambda r_: math.hypot(r_['p'][0] - bg[0][0], r_['p'][1] - bg[0][1]))
        dn = r['dn']
        nb.DBK = (r['p'][0] - dn[1] * 18.0, r['p'][1] + dn[0] * 18.0)
    nb.YBP = [p for p in DZ['yb']]
    nb.STATS_SB = {c['name']: {} for c in nb.KOLS}
    WCK = {c['name']: False for c in nb.KOLS}
    for k in FL:
        d = nb.DATA[k]
        for w in d['wet']:
            kc = nb.kolon_of(k, w)
            fx = [f for f in d['F'] if f['room'] is w and f['kind'] in nb.SB]
            nb.STATS_SB[kc['name']][k] = nb.STATS_SB[kc['name']].get(k, 0) + sum(nb.SB[f['kind']] for f in fx)
            WCK[kc['name']] |= any(f['kind'] == 'WC' for f in fx)
    for c in nb.KOLS:
        c['dn'] = dn_sb(sum(nb.STATS_SB[c['name']].values()), WCK[c['name']])
    out = dict(kolon=[(c['name'], c['typ'], c['d0'], [round(v) for v in c['p']], c['dn'], nb.STATS_SB[c['name']]) for c in nb.KOLS])
    out['depo'] = dict(karar=nb.DEPO, neden=nb.DEPO_NEDEN)
    out['adk'] = {n: dict(p=[round(v) for v in r['p']], daire=r['digits']) for n, r in nb.RISERS.items()}
    out['ek_makine'] = {k: [(f['kind'], f['daire']) for f in nb.DATA[k]['EK']] for k in FL}
    nb.yerlesim()
    bh, rep = nb.temel()
    out['temel_kolon_kesen'] = rep
    out['rogar'] = {k: dict(p=[round(v) for v in v_['p']], kols=v_['kols']) for k, v_ in nb.ROG.items()}
    out['kat'] = {}
    for k in FL:
        print('kat', k, flush=True)
        out['kat'][k] = kat_plani3(k)
    balkon_kayit()
    out['yasak'] = nb.yasak_kontrol()
    out['bina_alani'] = bh.area / 1e4
    out['balkon'] = [(b['k'], [round(v) for v in b['p']]) for b in nb.BALKON]
    nb.ROOF_A = round(bh.area / 1e4 * 1.10, 2)
    import sema3
    out['sema'] = sema3.ciz(vars(nb), HAV)
    for c in nb.KOLS:
        nb.METRAJ['PİS SU KOLONU (PVC) Ø%d' % c['dn']] = nb.METRAJ.get('PİS SU KOLONU (PVC) Ø%d' % c['dn'], 0) + 3.0 * len(FL) + 0.5
    for r in nb.RISERS.values():
        nb.METRAJ['TEMİZ SU ADK KOLONU (PPRC) Ø32'] = nb.METRAJ.get('TEMİZ SU ADK KOLONU (PPRC) Ø32', 0) + 3.0 * len(FL) + 1.0
    nb.METRAJ['TEMİZ SU DBK KOLONU (PPRC) Ø32'] = 3.0 * len(FL) + 1.0
    out['metraj'] = {k: round(v, 1) for k, v in sorted(nb.METRAJ.items())}
    adet = {}
    for k in FL:
        for f in nb.DATA[k]['F']:
            if f.get('daire'):
                adet[f['kind']] = adet.get(f['kind'], 0) + 1
    adet['BALKON_SUZGEC'] = len(nb.BALKON)
    adet['ASPIRATOR'] = len(RAPOR['havalandirma'])
    out['adet'] = adet
    out['kontrol3'] = kontroller()
    import pickle
    pickle.dump([(k, g, t, list(ls.coords)) for k, g, t, ls in REG], open('/tmp/claude-0/uu3/reg.pkl', 'wb'))
    out['rapor3'] = RAPOR
    out['sembol'] = dict(semboller2=dict(semb3.S2_KULLANILAN), kendi=sorted(set(semb3.KULLANILAN) - set(semb3.S2_KULLANILAN)),
                         bilinmeyen=sorted(semb3.BILINMEYEN))
    return out


def kontroller():
    ks = r3.kesisimler([(k + '|' + g, t, ls) for k, g, t, ls in REG])
    say = {}
    for ti, tj, gi, gj, p in ks:
        key = '-'.join(sorted((ti, tj)))
        say[key] = say.get(key, 0) + 1
    temiz = sum(v for kk, v in say.items() if set(kk.split('-')) <= {'SO', 'SC'})
    pis = say.get('PIS-PIS', 0)
    # ıslak hacim başına süzgeç
    sz = []
    for k in FL:
        d = nb.DATA[k]
        for w in d['wet']:
            if w['name'] in WET_ALL:
                n = sum(1 for f in d['F'] if f['room'] is w and f['kind'] == 'YS')
                sz.append((k, w['name'], w.get('daire'), n))
    # pis su branşmanları 45° / dik (oktilineer) mi
    aci = 0
    for k, g, t, ls in REG:
        if t != 'PIS':
            continue
        cs = list(ls.coords)
        for a, b in zip(cs[:-1], cs[1:]):
            an = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 45.0
            if min(an, 45.0 - an) > 0.5 and r3._d(a, b) > 1.0:
                aci += 1
    # balkon süzgeci pis suya bağlı mı
    bal_pis = sum(1 for ti, tj, gi, gj, p in ks if {ti, tj} == {'BALKON', 'PIS'})
    return dict(kesisim_tur=say, temiz_su_kesisim=temiz, pis_su_kesisim=pis,
                kesisim_ornek=[x for x in ks if set((x[0], x[1])) <= {'SO', 'SC', 'PIS'} and (x[0] == x[1] or {x[0], x[1]} <= {'SO', 'SC'})][:20],
                suzgec=sz, suzgec_hatali=[s for s in sz if s[3] != 1], pis_45_disi_parca=aci,
                kolon_saft=RAPOR['saft_kolon'], balkon_pis_temas=bal_pis)


if __name__ == '__main__':
    OUT = main()
    import cikti3
    cikti3.yaz(OUT, vars(nb), HAV)
