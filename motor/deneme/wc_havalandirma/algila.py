"""new_block.dxf mimarisinden penceresiz ıslak hacimleri ve mekanik havalandırma şaftlarını bulur -> girdi JSON.

Kullanılan: motor/deneme/uctan_uca/mimari.py (MKDU0 okuma, kat pencereleri, duvar ışınları) + motor/rooms.py (mahal poligonu).
Kural tabanlı:
  1. Mahal etiketleri (h >= 19): mimari.ROOM_WORDS + 'wc-banyo', 'wc-duş' gibi ıslak hacim yazıları.
  2. Mahal poligonu: rooms.detect (kapılar kapatılır, etiket tohumlu).
  3. Bina dış hattı: balkon dışındaki mahal poligonlarının birleşimi + morfolojik kapama (60 cm).
     Islak hacim "pencereli" sayılır (doğal havalanır) ancak: dış bölge / balkonla ortak duvarı >= 40 cm VE
     90 cm içinde pencere ölçü yazısı (60/60, 160/230; K1..K3 kapı etiketli 80/220 vb. kapı yazıları hariç) varsa.
     Dışa bakan ama penceresiz duvar (ör. 1. kat wc-duş, giriş boşluğu tarafı) penceresiz sayılır.
  4. Şaft: mimarın "mek. / havl." yazısı (MKDU0). Penceresiz hacim en yakın şafta (<= 3 m) bağlanır; katlar arası şaftlar
     kat kaydırması çıkarılarak (OFF) aynı düşey kolonda toplanır -> Ş1..Şn (soldan sağa, yukarıdan aşağıya).
  5. Daire no: ıslak hacim -> en yakın mutfak -> mutfağa en yakın tek haneli daire numarası (nb.py ile aynı mantık).
"""
import json, math, os, re, sys

REPO = '/home/claude/rotas-cizim-motoru'
sys.path.insert(0, REPO + '/motor/deneme/uctan_uca')
sys.path.insert(0, REPO + '/motor')
import mimari as M                                   # noqa: E402
import rooms as RM                                   # noqa: E402
from shapely.geometry import Point, box               # noqa: E402
from shapely.ops import unary_union                   # noqa: E402

WET_RE = re.compile(r'^(wc|banyo|duş|dus)[^\n]{0,12}$')
KAT_AD = {'Z': 'ZEMİN KAT', '1': '1. KAT', '2': '2. KAT'}
KOT = {'Z': 0.0, '1': 3.0, '2': 6.0}                 # nb.py KOT (±0,00 / +3,00 / +6,00)


def tip_of(ad):
    a = ad.lower()
    return 'BANYO' if ('banyo' in a or 'duş' in a or 'dus' in a) else 'WC'


def etiketler(R):
    out = []
    for a in R:
        if a[0] != 'T' or a[2][1] < 19.0:
            continue
        t = a[2][0].strip()
        if t in M.ROOM_WORDS or t.split()[0] in ('salon', 'mutfak', 'banyo') or WET_RE.match(t):
            c = a[1][1] if len(a[1]) > 1 else a[1][0]
            out.append((c[0], c[1], t))
    return out


def pencere_yazilari(R):
    """pencere ölçü yazıları: '60/60', '160/230' ya da alt alta iki sayı (60 \n 60) — yazı noktaları"""
    pts = []
    nums = [(a[1][0], a[2][0].strip()) for a in R if a[0] == 'T' and a[2][1] < 19.0]
    for p, t in nums:
        if re.fullmatch(r'\d{2,3}\s*/\s*\d{2,3}', t):
            pts.append(p)
    num = [(p, t) for p, t in nums if re.fullmatch(r'\d{2,3}', t)]
    for i, (p, t) in enumerate(num):
        for q, s in num[i + 1:]:
            if abs(p[0] - q[0]) < 6 and 4 < abs(p[1] - q[1]) < 20:
                pts.append(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2))
            elif abs(p[1] - q[1]) < 6 and 4 < abs(p[0] - q[0]) < 20:       # döndürülmüş (düşey duvar)
                pts.append(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2))
    # kapı (K1..K3) ve betonarme kolon/perde (S01, P04 ...) etiketlerinin yanındaki ölçü yazıları pencere değildir
    kapi = [(a[1][0], 45 if a[2][0].strip()[0] == 'K' else 25) for a in R if a[0] == 'T'
            and re.fullmatch(r'(K\d|[SP]\d{1,3})', a[2][0].strip())]
    return [p for p in pts if not any(math.hypot(p[0] - q[0], p[1] - q[1]) < r for q, r in kapi)]


def kat_tara(A, k):
    w = M.win(k)
    R = M.recs_in(A, w)
    labs = etiketler(R)
    ents = M.walls_ents(R)
    out, _ = RM.detect(ents, labs, w, res=2.0, door=100.0, disc=40.0)
    rms = [dict(name=d['name'], poly=d['poly']) for d in out.values() if d.get('poly') is not None]
    ic = [r['poly'] for r in rms if r['name'] != 'balkon']
    bina = unary_union([p.buffer(30, join_style=2) for p in ic]).buffer(30, join_style=2).buffer(-60, join_style=2)
    if bina.geom_type == 'MultiPolygon':
        bina = max(bina.geoms, key=lambda g: g.area)
    bina = bina.buffer(0)
    disari = box(*w).difference(bina)
    for r in rms:
        if r['name'] == 'balkon':
            disari = disari.union(r['poly'])
    pyaz = pencere_yazilari(R)
    hv = [a[1][0] for a in R if a[0] == 'T' and a[2][0].strip() in ('havl.', 'havl')]
    dig = [(a[1][-1], int(a[2][0].strip())) for a in R if a[0] == 'T' and a[2][0].strip().isdigit()
           and a[2][1] >= 20 and len(a[2][0].strip()) == 1]
    mut = [r for r in rms if r['name'] == 'mutfak']
    islak = []
    for r in rms:
        if not WET_RE.match(r['name']):
            continue
        P = r['poly']
        temas = P.buffer(45).intersection(disari).area / 45.0            # ≈ dış duvar boyu (cm)
        pen = [q for q in pyaz if P.buffer(90 if P.area >= 1e4 else 130).contains(Point(q))]     # küçük (eksik) poligonda geniş ara
        c = P.representative_point()
        m = min(mut, key=lambda m_: m_['poly'].representative_point().distance(c)) if mut else None
        daire = None
        if m and dig:
            mc = m['poly'].representative_point()
            daire = min(dig, key=lambda d_: math.hypot(d_[0][0] - mc.x, d_[0][1] - mc.y))[1]
        sh = min(hv, key=lambda h: P.distance(Point(h))) if hv else None
        shd = P.distance(Point(sh)) if sh else 1e9
        islak.append(dict(kat=k, ad=r['name'], tip=tip_of(r['name']), daire=daire, alan_m2=round(P.area / 1e4, 2),
                          dis_duvar_cm=round(temas), pencere_yazisi=len(pen),
                          pencere=bool(pen) and (temas >= 40 or P.area < 1e4),
                          saft_xy=(sh[0] - M.OFF[k], sh[1]) if sh and shd <= 300 else None, saft_mesafe=round(shd),
                          xy=(round(c.x - M.OFF[k]), round(c.y))))
    return islak


def algila(cikti=None):
    A = M.extract()
    hepsi = []
    for k in M.FLOORS:
        hepsi += kat_tara(A, k)
    # şaftları düşey kolonlarda topla (zemin koordinatı, 40 cm tolerans)
    kol = []
    for h in hepsi:
        if h['pencere'] or not h['saft_xy']:
            continue
        p = h['saft_xy']
        for c in kol:
            if math.hypot(c[0] - p[0], c[1] - p[1]) < 40:
                h['_s'] = c
                break
        else:
            kol.append(p)
            h['_s'] = p
    kol.sort(key=lambda p: (-round(p[1] / 100), p[0]))
    ad = {p: f'Ş{i + 1}' for i, p in enumerate(kol)}
    mahaller, pencereli = [], []
    for h in hepsi:
        rec = dict(kat=h['kat'], daire=f"D{h['daire']}" if h['daire'] else '-', ad=h['ad'], tip=h['tip'],
                   alan_m2=h['alan_m2'])
        if h['pencere']:
            rec.update(neden=f"dış duvar {h['dis_duvar_cm']} cm, pencere yazısı {h['pencere_yazisi']}")
            pencereli.append(rec)
        elif '_s' in h:
            rec.update(saft=ad[h['_s']], brans_m=round(max(1.0, min(3.0, h['saft_mesafe'] / 100 + 1.0)), 1))
            mahaller.append(rec)
        else:
            rec.update(neden='penceresiz ama 3 m içinde mimari şaft yok — kullanıcıya sorulacak')
            pencereli.append(rec)
    girdi = dict(
        proje='Metra Mimarlık — Adapazarı Tekeler 4739/4 (new_block.dxf, Z+2, 9 daire)', deneme=True,
        kaynak='algila.py (new_block.dxf mimarisi)',
        katlar=[dict(kod=k, ad=KAT_AD[k], kot=KOT[k], h=3.0) for k in M.FLOORS],
        cati_kot=9.0, cati_ustu=1.0,
        kabul=dict(q_oda=80, kademeler=[80, 160], asp_basinc=50, baglanti_cap=150, oda_basina_aspirator=False),
        saftlar=[dict(ad=ad[p], xy=[round(p[0]), round(p[1])], baglanti_yuk=2.6) for p in kol],
        mahaller=mahaller, pencereli=pencereli)
    if cikti:
        json.dump(girdi, open(cikti, 'w'), ensure_ascii=False, indent=1)
    return girdi


if __name__ == '__main__':
    g = algila(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'nb_algilanan.json'))
    for m in g['mahaller']:
        print('PENCERESİZ', m)
    for m in g['pencereli']:
        print('HARİÇ     ', m)
    print('şaftlar', g['saftlar'])
