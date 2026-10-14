# -*- coding: utf-8 -*-
"""Radyatör tesisatı kat planı (temsili mahal yerleşimi üzerinde): MTY radyatör blokları, gidiş-dönüş çifti duvar boyu,
köprülü kesişmeler, kümülatif "Q W-DNxx" hat etiketleri (MTY-RADYATOR CAP)."""
import math
from shapely.geometry import LineString, Point, Polygon, box as sbox, MultiLineString
from shapely.ops import unary_union, linemerge, substring
import ag
from ag import OFF, H, CEK, GEN, DER, YA0, YA1
import ciz as C

DIS = 25.0          # dış duvar kalınlığı


def _yon(a, b):
    L = math.dist(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 1e-9 else (1.0, 0.0)


def _okunur(th):
    th = (th + 180) % 360 - 180
    if th > 90.01 or th <= -90:
        th += 180
    return (th + 180) % 360 - 180


# ---------------------------------------------------------------------- mimari (temsili)
def mimari(cz, pl_list, dx, dy, sistem):
    msp = cz.msp
    MIM, PEN = 'ROTAS-MIMARI-TEMSILI', 'ROTAS-MIMARI-PENCERE'
    T = lambda p: (p[0] + dx, p[1] + dy)
    dis = unary_union([sbox(0, 0, GEN, DER), sbox(GEN, YA0, ag.GENIS_TOP - GEN, DER), sbox(ag.GENIS_TOP - GEN, 0, ag.GENIS_TOP, DER)])
    hatlar = [LineString(list(dis.exterior.coords))]
    for pl in pl_list:
        for o in pl['odalar']:
            x0, y0, x1, y1 = o['r']
            hatlar.append(LineString([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]))
    hatlar.append(LineString([(GEN, YA0), (ag.GENIS_TOP - GEN, YA0)]))
    birlesik = unary_union(hatlar)
    bosluk = []
    for pl in pl_list:
        for a, b, yy in pl['kapilar']:
            bosluk.append(sbox(a, yy - 1, b, yy + 1))
        for a, b, yy in pl['pencereler']:
            bosluk.append(sbox(a, yy - DIS - 2, b, yy + DIS + 2))
    giris = (1340.0, 1460.0)                         # bina girişi (merdiven holü güney duvarı)
    bosluk.append(sbox(giris[0], YA0 - 1, giris[1], YA0 + 1))
    # daire giriş kapıları (hol → antre), kolonun üstünde
    for x in (GEN, ag.GENIS_TOP - GEN):
        bosluk.append(sbox(x - 1, 480, x + 1, 570))
    ic = birlesik.difference(unary_union(bosluk))
    dd = dis.buffer(DIS, join_style='mitre').exterior
    dd = LineString(dd.coords).difference(unary_union(bosluk))
    for g in [ic, dd]:
        for ls in getattr(g, 'geoms', [g]):
            if ls.length > 0.5:
                cz.pl([T(p) for p in ls.coords], MIM, w=0.0, engel=False)
    # pencereler (duvar kalınlığında 2 cam çizgisi + söve)
    for pl in pl_list:
        for a, b, yy in pl['pencereler']:
            s = 1 if yy >= DER - 1 else -1
            for f in (0.35, 0.65):
                cz.pl([T((a, yy + s * DIS * f)), T((b, yy + s * DIS * f))], PEN, engel=False)
            for x in (a, b):
                cz.pl([T((x, yy)), T((x, yy + s * DIS))], PEN, engel=False)
    # kapı kanadı + açılım yayı (oda içine)
    for pl in pl_list:
        for o in pl['odalar']:
            if not o.get('kapi'):
                continue
            a, b, yy = o['kapi']
            ic_yon = 1 if o['sira'] == 'N' else -1
            w = b - a
            mente = a if o['sira'] == 'N' else b
            karsi = b if o['sira'] == 'N' else a
            cz.pl([T((mente, yy)), T((mente, yy + ic_yon * w))], MIM, engel=False)
            arc = []
            for i in range(13):
                t = math.radians(90 * i / 12)
                vx = (karsi - mente);
                px = mente + vx * math.sin(t); py = yy + ic_yon * w * math.cos(t)
                arc.append(T((px, py)))
            cz.pl(arc, MIM, engel=False)
    for x in (GEN, ag.GENIS_TOP - GEN):            # daire kapısı (hol tarafına açılır)
        s = 1 if x == GEN else -1
        cz.pl([T((x, 570)), T((x + s * 90, 570))], MIM, engel=False)
    # merdiven (temsili)
    mx0, mx1, my0, my1 = 1330.0, 1470.0, 640.0, 960.0
    cz.pl([T((mx0, my0)), T((mx1, my0)), T((mx1, my1)), T((mx0, my1))], MIM, kapali=True, engel=False)
    cz.pl([T((1400, my0)), T((1400, my1))], MIM, engel=False)
    for k in range(1, 11):
        yy = my0 + (my1 - my0) * k / 11
        cz.pl([T((mx0, yy)), T((1395, yy))], MIM, engel=False)
        cz.pl([T((1405, yy)), T((mx1, yy))], MIM, engel=False)
    cz.yazi(T((1400, 600)), 'MERDİVEN HOLÜ', 9, 'ROTAS-MIMARI-TEMSILI', maske=True)


# ---------------------------------------------------------------------- boru çiftleri
class Boru:
    def __init__(self):
        self.g = []      # gidiş polylineları [(x,y)...]
        self.d = []      # dönüş
        self.tee_g = []  # T başlangıç noktaları (köprü dışı)


def _ofset(ls, d):
    return list(ls.offset_curve(d, join_style='mitre', mitre_limit=10).coords)


def _baslangic(q, dirv, parent_line, maxlen=40.0):
    """q noktasından geri (−dirv) doğrultuda ebeveyn hattı kes"""
    ray = LineString([(q[0] - dirv[0] * maxlen, q[1] - dirv[1] * maxlen), (q[0] + dirv[0] * (2 * H + 1), q[1] + dirv[1] * (2 * H + 1))])
    g = ray.intersection(parent_line)
    if g.is_empty:
        return None
    parcalar = getattr(g, 'geoms', None) or [g]
    noktalar, cizgi = [], []
    for p in parcalar:
        if p.geom_type == 'Point':
            noktalar.append(p)
        elif p.geom_type == 'LineString':
            cizgi += [Point(c) for c in p.coords]
    if cizgi:          # doğrusal çakışma: ileri yöndeki uç (köşe)
        return max(cizgi, key=lambda p: (p.x - q[0]) * dirv[0] + (p.y - q[1]) * dirv[1])
    if not noktalar:
        return None
    return min(noktalar, key=lambda p: p.distance(Point(q)))


def rad_baglanti(r):
    """radyatör bloğu yerleşimi ve bağlantı noktaları (vana ucu / rakor ucu), gidiş hangi uçtaysa vana orada"""
    L = r['L']; ban = r['tip'] == 'Banyopan'
    wy = r['duvar_y']; ic = r['ic']
    return L, ban, wy, ic


def borular(cz, pl, dx, dy, sistem, bilgi):
    """daire boru çiftlerini çiz; radyatör bloklarını yerleştir. Dönüş: yol çizgi kayıtları (etiket için)"""
    T = lambda p: (p[0] + dx, p[1] + dy)
    yollar = pl['yollar']
    hat = {}           # yol id -> {'g': coords, 'd': coords, 'gs': +1/-1}
    sira = sorted(yollar, key=lambda y: (0 if y['ebeveyn'] is None else 1, y['id']))
    islenen = set()
    kuyruk = [y for y in yollar if y['ebeveyn'] is None]
    order = []
    while kuyruk:
        y = kuyruk.pop(0); order.append(y)
        kuyruk += [z for z in yollar if z['ebeveyn'] == y['id']]
    damla_g, damla_d = [], []
    rad_kayit = []
    for y in order:
        ls = y['ls']
        adaylar = []
        for gs in (1, -1):
            g = _ofset(ls, gs * H); d = _ofset(ls, -gs * H)
            if y['ebeveyn'] is None:
                adaylar.append((0, gs, g, d)); break
            par = hat[y['ebeveyn']]
            ok = True; kes = 0; yeni = {}
            for nm, cs, plin, other in (('g', g, par['g'], par['d']), ('d', d, par['d'], par['g'])):
                dv = _yon(cs[0], cs[1])
                p0 = _baslangic(cs[0], dv, LineString(plin))
                if p0 is None:
                    ok = False; break
                ileri = (p0.x - cs[0][0]) * dv[0] + (p0.y - cs[0][1]) * dv[1]
                if ileri > 0.01:
                    yeni[nm] = [(p0.x, p0.y)] + cs[1:]
                    ek = LineString([(p0.x, p0.y), (p0.x, p0.y)])
                else:
                    ek = LineString([(p0.x, p0.y), cs[0]])
                    yeni[nm] = [(p0.x, p0.y)] + cs if ek.length > 0.01 else cs
                if ek.length > 0.01 and ek.crosses(LineString(other)):
                    kes += 1
            if ok:
                adaylar.append((kes, gs, yeni['g'], yeni['d']))
        adaylar.sort(key=lambda t: t[0])
        kes, gs, g, d = adaylar[0]
        hat[y['id']] = dict(g=g, d=d, gs=gs)
        # radyatör uçları
        Ltop = ls.length
        for r in y['rads']:
            son = r['s_uzak'] >= Ltop - 1
            wy, icy = r['duvar_y'], r['ic']
            gL, dL = LineString(hat[y['id']]['g']), LineString(hat[y['id']]['d'])
            # yakın uç noktasındaki iç/dış
            pyak = (r['yakin'], wy + icy * OFF)
            gd = abs(gL.interpolate(gL.project(Point(pyak))).y - wy)
            dd_ = abs(dL.interpolate(dL.project(Point(pyak))).y - wy)
            ic_hat = 'g' if gd < dd_ else 'd'
            # vana ucu: gidiş iç hatsa yakın uç, değilse uzak uç
            u = 1.0 if r['uzak'] > r['yakin'] else -1.0
            if r['tip'] == 'Banyopan':
                s = r['L'] / 32.0
                yak_x = r['cx'] - u * 16.0 * s; uz_x = r['cx'] + u * 16.0 * s
                bag_off_v = CEK + 3.0 * s; bag_off_r = CEK + 3.0 * s
            else:
                s = r['L'] / 100.0
                yak_x = r['cx'] - u * 54.7 * s; uz_x = r['cx'] + u * 50.7 * s
                bag_off_v = CEK + 12.0; bag_off_r = CEK + 7.3
            vana_yakinda = (ic_hat == 'g')
            # blok yerleşimi
            th = 0.0 if icy > 0 else 180.0
            if r['tip'] == 'Banyopan':
                ins_x = r['cx'] - u * 12.0 * s if vana_yakinda else r['cx'] + u * 12.0 * s
                dir_local = u if vana_yakinda else -u
            else:
                ins_x = yak_x if vana_yakinda else r['cx'] + u * 54.7 * s
                dir_local = u if vana_yakinda else -u
            world_x_of_local_x = 1.0 if th == 0 else -1.0
            sx = s if dir_local * world_x_of_local_x > 0 else -s
            ins = (ins_x, wy + icy * CEK)
            r['_blok'] = dict(p=ins, th=th, sx=sx, sy=s if r['tip'] == 'Banyopan' else 1.0)
            # bağlantı uçları (vana ucu = gidiş)
            if vana_yakinda:
                gx, gyo = (yak_x if r['tip'] != 'Banyopan' else yak_x), bag_off_v
                dxx, dyo = uz_x, bag_off_r
            else:
                gx, gyo = (r['cx'] + u * 54.7 * s) if r['tip'] != 'Banyopan' else uz_x, bag_off_v
                dxx, dyo = (r['cx'] - u * 50.7 * s) if r['tip'] != 'Banyopan' else yak_x, bag_off_r
            for nm, bx, boff in (('g', gx, gyo), ('d', dxx, dyo)):
                cs = hat[y['id']][nm]
                L_ = LineString(cs)
                yaklas = nm == ic_hat
                if son and yaklas:
                    # iç hat: bağlantı x'inde kes
                    sp = L_.project(Point(bx, wy + icy * (OFF - H)))
                    cs2 = list(substring(L_, 0, sp).coords)
                    q = cs2[-1]
                    cs2.append((bx, wy + icy * boff))
                    hat[y['id']][nm] = _sade(cs2)
                elif son:
                    # dış hat: bağlantı x'ine kadar uzat/kes
                    last = cs[-1]
                    dv = _yon(cs[-2], cs[-1])
                    yeni = list(cs[:-1]) + [(bx, last[1])] if abs(dv[1]) < 1e-6 else list(cs)
                    yeni.append((bx, wy + icy * boff))
                    hat[y['id']][nm] = _sade(yeni)
                else:
                    sp = L_.project(Point(bx, wy))
                    q = L_.interpolate(sp)
                    (damla_g if nm == 'g' else damla_d).append([(q.x, q.y), (bx, wy + icy * boff)])
            rad_kayit.append(r)
    # çiz: önce gidiş, sonra köprülü dönüş
    tum_g = [LineString(h['g']) for h in hat.values()] + [LineString(p) for p in damla_g]
    tum_d_pts = [h['d'] for h in hat.values()] + damla_d
    for h in list(hat.values()):
        cz.pl([T(p) for p in h['g']], C.GID, w=1.5)
    for p in damla_g:
        cz.pl([T(q) for q in p], C.GID, w=1.5)
    for pts in tum_d_pts:
        xy = C.kopru_ekle(pts, tum_g, r=4.0)
        xy = C.kopru_yon(xy, [LineString(q) for q in tum_d_pts if q is not pts] + tum_g)
        cz.pl([(T(q[:2])[0], T(q[:2])[1], 0, 0, q[4]) for q in xy], C.DON, w=1.5, ltscale=0.4)
    # radyatör blokları
    for r in rad_kayit:
        b = r['_blok']
        p = T(b['p'])
        ad = 'MTY-RADYATOR Banyopan' if r['tip'] == 'Banyopan' else 'MTY-RADYATOR Panel'
        mm = r['m']
        etiket = (f"BANYOPAN {r['boy'] * 1000:.0f}  {r['ver']:.0f} W" if r['tip'] == 'Banyopan'
                  else f"{r['model']}x{r['boy'] * 1000:.0f}  {r['ver']:.0f} W")
        wy = r['duvar_y'] + dy; icy = r['ic']
        cz.blok(ad, p, b['th'], b['sx'], b['sy'], 'ROTAS-RADYATOR', ozn={'RAD': etiket, 'NO': f"{bilgi['kat_on']}{mm['no']}"},
                ozn_h={'RAD': 8.0, 'NO': 6.0}, ozn_rot=0.0,
                ozn_konum={'RAD': (r['cx'] + dx, wy + icy * 50.0), 'NO': (r['cx'] + dx, wy + icy * 63.0)}, maske=True)
    return hat


def _sade(pts):
    out = []
    for p in pts:
        if out and math.dist(out[-1], p) < 1e-6:
            continue
        out.append(p)
    return out


# ---------------------------------------------------------------------- etiketler
def hat_etiketleri(cz, pl, hat, parcalar, dx, dy, kritik_ids):
    """her daire parçasına MTY-RADYATOR CAP bloğu ile '2070W-DN15'"""
    T = lambda p: (p[0] + dx, p[1] + dy)
    h = 8.0
    for p in parcalar:
        if p['tur'] != 'daire':
            continue
        y = pl['yollar'][p['yol']]
        ls = y['ls']
        try:
            sub = substring(ls, p['s0'], p['s1'])
        except Exception:
            continue
        cs = list(sub.coords)
        txt = f"{p['Q']:.0f}W-{p['dn']}"
        tw = len(txt) * h * 0.60 * 0.85 + 6
        segs = sorted(zip(cs[:-1], cs[1:]), key=lambda s: -math.dist(*s))
        yerlesti = False
        for a, b in segs[:4]:
            Ls = math.dist(a, b)
            if Ls < tw + 16:
                continue
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            th = _okunur(ang)
            u = (math.cos(math.radians(th)), math.sin(math.radians(th)))
            n = (-u[1], u[0])
            for f in (0.5, 0.35, 0.65, 0.2, 0.8):
                c = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
                for yon in (1, -1):
                    # yazı tarafı: n*yon ; köken çift hattın o taraftaki çizgisinde
                    o = (c[0] + n[0] * H * yon, c[1] + n[1] * H * yon)
                    if yon == 1:
                        k0 = (o[0] + u[0] * (-tw / 2) + n[0] * 2.0, o[1] + u[1] * (-tw / 2) + n[1] * 2.0)
                    else:
                        k0 = (o[0] + u[0] * (-tw / 2) - n[0] * (2.0 + h * 1.3), o[1] + u[1] * (-tw / 2) - n[1] * (2.0 + h * 1.3))
                    kut = [k0, (k0[0] + u[0] * tw, k0[1] + u[1] * tw),
                           (k0[0] + u[0] * tw + n[0] * h * 1.3, k0[1] + u[1] * tw + n[1] * h * 1.3),
                           (k0[0] + n[0] * h * 1.3, k0[1] + n[1] * h * 1.3)]
                    kutw = Polygon([T(q) for q in kut])
                    if not cz.bos_mu(kutw):
                        continue
                    # blok: yön=+1 → dönüş th, köken o-u*tw/2 ; yön=-1 → aynalı değil, yazıyı alta: köken alt kenarda ve kanca yukarı
                    if yon == 1:
                        ins = (o[0] - u[0] * (tw / 2 - 3), o[1] - u[1] * (tw / 2 - 3))
                        cz.maske([T(q) for q in kut])
                        cz.blok('MTY-RADYATOR CAP', T(ins), th, 8.0, 8.0, C.CAPK, ozn={'SCCP_001': txt}, ozn_h={'SCCP_001': h})
                    else:
                        ins = (o[0] - u[0] * (tw / 2 - 3), o[1] - u[1] * (tw / 2 - 3))
                        cz.maske([T(q) for q in kut])
                        cz.blok('MTY-RADYATOR CAP', T(ins), th, 8.0, -8.0, C.CAPK, ozn={'SCCP_001': txt}, ozn_h={'SCCP_001': h},
                                ozn_konum={'SCCP_001': T((k0[0] + u[0] * tw / 2 + n[0] * h * 0.65, k0[1] + u[1] * tw / 2 + n[1] * h * 0.65))})
                    cz.yazilar.append(kutw)
                    yerlesti = True
                    break
                if yerlesti:
                    break
            if yerlesti:
                break
        p['_etiket'] = yerlesti


def mahal_etiketleri(cz, pl, dx, dy, kat_on):
    for o in pl['odalar']:
        m = o['m']
        x0, y0, x1, y1 = o['r']
        s = 0.55 if o['sira'] == 'A' else 0.8
        w, hh = 72 * s, 102 * s
        best = None
        cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
        for ddx in [0, -60, 60, -120, 120, -180, 180, -240, 240, -300, 300]:
            for ddy in [0, -40, 40, -80, 80]:
                cx, cy = cx0 + ddx, cy0 + ddy
                kb = sbox(cx - w / 2 + dx, cy - 59 * s + dy, cx + w / 2 + dx, cy + 42 * s + dy)
                if kb.bounds[0] < x0 + dx + 5 or kb.bounds[2] > x1 + dx - 5 or kb.bounds[1] < y0 + dy + 5 or kb.bounds[3] > y1 + dy - 5:
                    continue
                if cz.bos_mu(kb):
                    best = (cx, cy, kb); break
            if best:
                break
        if not best:
            cx, cy = cx0, cy0
            kb = sbox(cx - w / 2 + dx, cy - 59 * s + dy, cx + w / 2 + dx, cy + 42 * s + dy)
            best = (cx, cy, kb)
        cx, cy, kb = best
        cz.maske(list(kb.exterior.coords)[:4])
        cz.blok('MTY-RADYATOR MAHAL', (cx + dx, cy + dy), 0, s, s, 'ROTAS-MAHAL',
                ozn={'MAHAL_001': m['ad'], 'NO_001': f"{kat_on}{m['no']}", 'DERECE_001': f"{m['ti']:.0f}°C",
                     'ISIKAYBI_001': f"{m['q']:.0f} W", 'ALAN': ''})
        cz.yazilar.append(kb)
