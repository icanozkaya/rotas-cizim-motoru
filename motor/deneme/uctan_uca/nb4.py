"""UÇTAN UCA SIHHİ DENEMESİ — R4 (new_block sıhhi, 14.10.2026).

R3 (nb3.py) aynen çalışır; R4 değişiklikleri yama olarak:
  1. Çap etiketi yüksekliği 10 (PRM k_cap = 10); bütün çap etiketleri / aspiratör / cihaz yazıları DXF'te yazı-yazı çakışmasız
     yerleştirilir (`etiket4.py`: çap etiketi boru ekseni boyunca kaydırılır, serbest yazılar kılavuzla yanına alınır;
     mahal adı ve diğer mimari yazılar engel).
  2. Şebeke hattı: bina girişinden ortak alan (giriş holü) ORTASINDAN DBK'ya — r3.Alan maliyet alanında A* (duvardan
     uzaklık tercihi), daire mahalleri (salon / oda / ıslak hacim) kapalı.
  3. Kolon şeması (`sema4.py`): sayaç düzeni planla aynı — çatı deposu → ADK inişi → her katta daire kapısında
     vana + sayaç + çek valf; zeminde toplu sayaç YOK; sayaç hatları kesişmez.
  4. SIHHİ DETAYLAR çerçevesi içerikten (`sema4.kayit_kutusu`).
  5. Pis su – temiz su planda üst üste görünme: temiz su güzergâh maliyetine pis su hatlarının 4 cm bandı cezası
     (güzergâh ayrıştırma; köprü YOK). Sayı raporlanır.
  6. Pafta sonu (`cikti4.py`): kendi ROTAS sembollerimizle lejant (semboller2 açıklamaları) + armatür / malzeme adet + boru metrajı.
Çalıştır:  cd /tmp/claude-0/uu4 && python3 /home/claude/rotas-cizim-motoru/motor/deneme/uctan_uca/nb4.py
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = '/home/claude/rotas-cizim-motoru'
sys.path.insert(0, HERE)
import nb3                                   # semb3.kur() + nb (tanıma) burada çalışır
import sema4
sys.modules['sema3'] = sema4                 # nb3.main() 'import sema3' -> R4 şeması
import r3
import nb
import gp
import cad
import mtyblk
import numpy as np
from shapely.geometry import LineString, Point

PRM = nb.PRM
PRM.update(cikti=REPO + '/proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R4.dxf', k_cap=10.0)
PIS_CEZA = float(os.environ.get('R4_PIS_CEZA', 30.0))   # pis su bandı hücre cezası (taban 1..3,2)
RAPOR4 = dict(sebeke={}, pis_bant={})


# ------------------------------------------------------------------ 5. pis su bandı cezası (temiz su güzergâhı)
class AlanR4(r3.Alan):
    def __init__(self, RT, M, d, k, rooms, step=4.0):
        super().__init__(RT, M, d, k, rooms, step)
        from scipy import ndimage
        lines = [ls for kk, g, t, ls in nb3.REG if kk == k and t == 'PIS']
        if lines and PIS_CEZA > 0:
            img = self.raster_lines(lines)
            img = ndimage.binary_dilation(img, iterations=1)          # ±4 cm
            self.ceza = (PIS_CEZA * img).astype(np.float32)
            self.base = (self.base + self.ceza).astype(np.float32)
            RAPOR4['pis_bant'][k] = int(img.sum())


r3.Alan = AlanR4
_daire_temiz3 = nb3.daire_temiz


def daire_temiz4(k, d, AL, dno, ent):
    """pis su cezalı güzergâh bir dairede kendini kesen öteleme / bağlanamayan armatür üretirse o daire cezasız (R3) yeniden çizilir"""
    snap = (len(cad.R), len(cad.BLK), len(gp.NET), len(gp.NODES), len(nb3.REG), dict(nb.METRAJ))
    out = _daire_temiz3(k, d, AL, dno, ent)
    if out['basarisiz'] and getattr(AL, 'ceza', None) is not None:
        del cad.R[snap[0]:]; del cad.BLK[snap[1]:]; del gp.NET[snap[2]:]; del gp.NODES[snap[3]:]; del nb3.REG[snap[4]:]
        nb.METRAJ.clear(); nb.METRAJ.update(snap[5])
        AL.base = (AL.base - AL.ceza).astype(np.float32)
        try:
            out2 = _daire_temiz3(k, d, AL, dno, ent)
        finally:
            AL.base = (AL.base + AL.ceza).astype(np.float32)
        out2['r4_cezasiz_yeniden'] = list(out['basarisiz'])
        RAPOR4.setdefault('cezasiz_daire', []).append((k, dno, out['basarisiz'], out2['basarisiz']))
        return out2
    return out


nb3.daire_temiz = daire_temiz4


# ------------------------------------------------------------------ 2. şebeke: bina girişi -> hol ORTASI -> DBK
def zemin_sebeke4(d):
    bg = [a[1][0] for a in d['R'] if a[0] == 'T' and 'bina' in a[2][0] and 'giri' in a[2][0]]
    if not (bg and nb.DBK):
        return nb3.zemin_sebeke3(d)
    e = bg[0]
    M, RT = nb.M, nb.RT
    import r2 as _r2
    OW0 = _r2.ortho_walls(d['W'])
    hx = d['HULL'].bounds[2] if d.get('HULL') is not None else e[0]
    yo = []                                   # giriş holü ORTASI: bina cephesinin 120 cm içinde düşey ışınla hol genişliği
    for dxx in (60.0, 120.0, 180.0):
        q = (hx - dxx, e[1])
        r_ = _r2.rect_o(OW0, q)
        if r_[3] - r_[1] < 600:
            yo.append((r_[1] + r_[3]) / 2)
    ym = sorted(yo)[len(yo) // 2] if yo else e[1]
    sebeke = (M.WIN_Z[2] - 5.0, ym)
    RAPOR4['sebeke_hol_ortasi_y'] = round(ym, 1)
    AL = r3.Alan.__mro__[1](RT, M, d, 'Z', d.get('ROOMS', []))    # pis cezası olmadan (bina dışı / hol)
    g = AL.grid()
    # daire mahalleri: etiketten duvarlara ortogonal dikdörtgen (oda tanımada salon giriş holüyle birleşebiliyor -> poligon değil)
    import r2
    from shapely.geometry import box as _box
    OW = r2.ortho_walls(d['W'])
    rms = []
    for r in d.get('ROOMS', []):
        if r['name'].split()[0] in ('salon', 'yatak', 'oda', 'yüklük', 'mutfak', 'banyo', 'wc+banyo', 'wc-banyo', 'wc-lvb.',
                                    'duş', 'wc-duş', 'balkon', 'antre-kor.'):
            q = r2.rect_o(OW, r['xy'])
            if (q[2] - q[0]) * (q[3] - q[1]) < 60e4:
                rms.append(_box(*q))
    # taban: koridor / hol ORTASI tercihi (oda pahalılığı yok; daire mahalleri zaten kapalı)
    dist = AL.dist[g._sl]
    g.base = (1.0 + 2.2 * np.exp(-dist / 30.0) + 150.0 * (dist < 3.0)).astype(np.float32)   # duvar delme pahalı: kapıdan geç
    m = np.zeros_like(g.block)
    for r in rms:
        m |= AL.raster_poly(r.buffer(-2))[g._sl]
    lines = [ls for k_, g_, t_, ls in nb3.REG if k_ == 'Z' and t_ in ('SO', 'SC', 'PIS')]
    if lines:                       # temiz / pis hatlardan 8 cm uzak; DBK çevresinde (26 cm) yalnız hattın kendisi kapalı
        m |= r3.blok_cizgi(g, lines, 8.0) & ~r3.disk(g, nb.DBK, 26.0)
        m |= r3.blok_cizgi(g, lines, 2.0) & ~r3.disk(g, nb.DBK, 3.0)
    if d.get('HULL') is not None:   # bina dışı kapalı; yalnız giriş doğrultusunda (bina girişi yazısı hizası) şerit açık
        dis = ~AL.raster_poly(d['HULL'].buffer(4))[g._sl]
        ii, jj = np.mgrid[0:g.nx, 0:g.ny]
        yy = g.y0 + jj * g.s
        xx = g.x0 + ii * g.s
        serit = (np.abs(yy - sebeke[1]) <= 12) & (xx >= d['HULL'].bounds[2] - 400)
        m |= dis & ~serit
        g.base = np.where(serit, 1.0, g.base).astype(np.float32)   # giriş merdiveni basamak çizgileri duvar sayılmaz
    m &= ~r3.disk(g, sebeke, 10.0)
    pth = g.route(sebeke, nb.DBK, sysn='SEB', mask=m, free_end=0.1, cross=0.0, turn=12.0)
    if not pth:
        RAPOR4['sebeke']['uyari'] = 'A* bulunamadı, R3 yöntemi'
        return nb3.zemin_sebeke3(d)
    pth = r3.temizle(r3.duzelt(pth, [sebeke, nb.DBK]))
    ls = LineString(pth)
    oda_ici = sum(ls.intersection(r.buffer(-2)).length for r in rms)
    # orta kontrolü: hattın duvara uzaklığı (ortalama / en az; uçlardaki 60 cm hariç)
    from scipy import ndimage
    dd = []
    for s in np.arange(60.0, max(60.0, ls.length - 60.0), 10.0):
        p = ls.interpolate(s)
        i, j = AL.ij((p.x, p.y))
        if 0 <= i < AL.nx and 0 <= j < AL.ny:
            dd.append(float(AL.dist[i, j]))
    RAPOR4['sebeke'] = dict(nokta=len(pth), boy_cm=round(ls.length), daire_mahali_ici_cm=round(oda_ici, 1),
                            duvara_ort_cm=round(sum(dd) / len(dd), 1) if dd else None, duvara_min_cm=round(min(dd), 1) if dd else None)
    gp.pipe(pth, gp.CS, 'S'); gp.node(pth[0], 'ŞEBEKE'); gp.node(pth[-1], 'DBK')
    nb3.reg('Z', 'SEB', 'SO', pth)
    nb.ANA_HAT.append(('Z', [cad.P(q) for q in pth]))
    nb.METRAJ_ADD('TEMİZ SU ŞEBEKE / DBK (PPRC) Ø32', pth)
    nb.VANA((sebeke[0] - 15, sebeke[1]), 0.5, 0); nb.PISLIK_TUTUCU((sebeke[0] - 30, sebeke[1]), 0.45, 0)
    mtyblk.insert('MTY-SU SAYACI', (sebeke[0] - 46, sebeke[1]), 0, 0.3); nb.CEKVALF((sebeke[0] - 62, sebeke[1]), 0.45, 0)
    cad.T((sebeke[0] - 70, sebeke[1] + 12), 'ŞEBEKE Ø32 - ANA SAYAÇ (BİNA GİRİŞİ) → DBK → ÇATI DEPOSU', 6, gp.TSC, 'R')


nb3.zemin_sebeke3_eski = nb3.zemin_sebeke3
_z3 = nb3.zemin_sebeke3


def _zs(d):
    nb3.zemin_sebeke3 = _z3
    try:
        return zemin_sebeke4(d)
    finally:
        nb3.zemin_sebeke3 = _zs


nb3.zemin_sebeke3 = _zs


def kontroller4(OUT):
    k3 = OUT['kontrol3']
    tur = k3['kesisim_tur']
    pt = sum(v for kk, v in tur.items() if 'PIS' in kk.split('-') and set(kk.split('-')) & {'SO', 'SC'})
    k3['pis_temiz_ust_uste'] = pt
    k3['pis_temiz_R3'] = 176
    return k3


if __name__ == '__main__':
    os.makedirs('/tmp/claude-0/uu4', exist_ok=True)
    os.makedirs('/tmp/claude-0/uu3', exist_ok=True)
    OUT = nb3.main()
    OUT['rapor4'] = RAPOR4
    kontroller4(OUT)
    import cikti4
    cikti4.yaz(OUT, vars(nb), nb3.HAV)
