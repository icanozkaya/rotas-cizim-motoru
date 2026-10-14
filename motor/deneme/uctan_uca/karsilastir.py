"""Motor çıktısı ile kullanıcının aynı dosyadaki MTY çizimini karşılaştırır; R1 (önce, NB_SIHHI_DENEME.dxf + ozet_r1.json)
ve R2 (sonra, 14.10.2026 kuralları: NB_SIHHI_DENEME_R2.dxf + ozet_r2.json) yan yana -> KARSILASTIRMA.md.
Çalıştır: python3 karsilastir.py  (R2 için önce nb.py çalışmış olmalı; ozet_r2.json /tmp/claude-0/uu/nb_ozet_r2.json'dan kopyalanır)"""
import json, math, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ezdxf
import mimari as M

import shutil
if os.path.exists('/tmp/claude-0/uu/nb_ozet_r2.json'):
    shutil.copy('/tmp/claude-0/uu/nb_ozet_r2.json', os.path.join(HERE, 'ozet_r2.json'))
OZ1 = json.load(open(os.path.join(HERE, 'ozet_r1.json')))
OZ = json.load(open(os.path.join(HERE, 'ozet_r2.json')))
OUT_DXF1 = OZ1['dxf']['yol']
OUT_DXF = OZ['dxf']['yol']
M.ensure_src()
src = ezdxf.readfile(M.SRC)
msp = src.modelspace()
A = M.extract()

TEMEL_OFF = -2629.0          # kullanıcı temel planı = zemin planı - 2629 cm (kolon eşlemesinden)


def cl(s):
    return (s or '').replace('%%C', 'Ø').replace('%%c', 'Ø').replace('%%%', '%').strip()


U = []
for e in msp.query('INSERT'):
    at = {a.dxf.tag.split('_0')[0]: cl(a.dxf.text) for a in e.attribs}
    U.append(dict(lay=e.dxf.layer, name=e.dxf.name, p=(e.dxf.insert.x, e.dxf.insert.y), at=at))


def in_w(p, w):
    return w[0] <= p[0] <= w[2] and w[1] <= p[1] <= w[3]


WZ = M.win('Z')
WT = (WZ[0] + TEMEL_OFF, WZ[1], WZ[2] + TEMEL_OFF + 700, WZ[3])
floors = {k: M.win(k) for k in M.FLOORS}

# ------------------------------------------------------------------ 1. kolonlar
ukol = {}
for k, w in list(floors.items()) + [('T', WT)]:
    o = TEMEL_OFF if k == 'T' else M.OFF[k]
    for u in U:
        if in_w(u['p'], w) and re.fullmatch(r'P\d+', u['at'].get('K', '')):
            ukol.setdefault(k, {})[u['at']['K']] = (u['p'][0] - o, u['p'][1])
R = M.recs_in(A, WZ)
labs = M.labels(R, 'Z')
wet, W = M.wet_rooms(R, labs)


F = M.fixtures(R, wet, W)


def room_of(p):
    nf = [f for f in F if f['room'] and f['kind'] != 'KOMBI']
    if nf:
        f = min(nf, key=lambda f: math.hypot(f['c'][0] - p[0], f['c'][1] - p[1]))
        if math.hypot(f['c'][0] - p[0], f['c'][1] - p[1]) < 45:
            r = f['room']
            return r['name'] + '@%d,%d' % (round(r['xy'][0]), round(r['xy'][1]))
    ins = [r for r in wet if r['rect'][0] - 15 <= p[0] <= r['rect'][2] + 15 and r['rect'][1] - 15 <= p[1] <= r['rect'][3] + 15
           and (r['rect'][2] - r['rect'][0]) < 400 and (r['rect'][3] - r['rect'][1]) < 450]
    if ins:
        r = min(ins, key=lambda r: (r['rect'][2] - r['rect'][0]) * (r['rect'][3] - r['rect'][1]))
        return r['name'] + '@%d,%d' % (round(r['xy'][0]), round(r['xy'][1]))
    best = None
    for r in wet:
        d = math.hypot(r['xy'][0] - p[0], r['xy'][1] - p[1])
        key = (W.cross(p, r['xy']), d)
        if d < 400 and (best is None or key < best[0]):
            best = (key, r)
    return best[1]['name'] + '@%d,%d' % (round(best[1]['xy'][0]), round(best[1]['xy'][1])) if best else '?'


TYP = {'mutfak': 'MUTFAK', 'wc-lvb.': 'WC', 'banyo': 'BANYO', 'wc+banyo': 'BANYO', 'duş': 'DUŞ'}


def kolon_esle(OZx):
    ours = {c[0]: dict(typ=c[1], daire=c[2], p=tuple(c[3]), dn=c[4], sb=c[5]) for c in OZx['kolon']}
    res = {}
    used = set()
    for kn, p in sorted(ukol.get('Z', {}).items(), key=lambda t: int(t[0][1:])):
        rm = room_of(p).split('@')[0]
        cand = sorted([t for t in ours.items() if t[1]['typ'] == TYP.get(rm) and t[0] not in used] or ours.items(),
                      key=lambda t: math.hypot(t[1]['p'][0] - p[0], t[1]['p'][1] - p[1]))
        on, oc = cand[0]
        used.add(on)
        res[kn] = (rm, on, oc, round(math.hypot(oc['p'][0] - p[0], oc['p'][1] - p[1])))
    return res


K1, K2 = kolon_esle(OZ1), kolon_esle(OZ)
rows_k = []
for kn, p in sorted(ukol.get('Z', {}).items(), key=lambda t: int(t[0][1:])):
    rm, on1, oc1, d1 = K1[kn]
    _, on2, oc2, d2 = K2[kn]
    rows_k.append((kn, rm, '%d, %d' % (round(p[0]), round(p[1])), '%s %d, %d' % ((on1,) + oc1['p']), d1,
                   '%s %d, %d' % ((on2,) + oc2['p']), d2))
ORT1 = sum(K1[k][3] for k in K1) / max(1, len(K1))
ORT2 = sum(K2[k][3] for k in K2) / max(1, len(K2))

# ------------------------------------------------------------------ 2. armatür blokları (kullanıcı) -> ıslak hacim SB / MB
FIXN = collections.Counter()
usb = collections.defaultdict(float)
umb = collections.defaultdict(float)
ufix = collections.defaultdict(list)
for u in U:
    if not in_w(u['p'], WZ) or u['lay'] != 'MTY-VANA':
        continue
    ps = u['at'].get('PS', '')
    if not ps.endswith('SB') or 'K' in u['at']:
        continue
    rm = room_of(u['p'])
    sb = float(ps.split()[0])
    mb = sum(float(u['at'][t].split()[0]) for t in ('SO', 'SC') if u['at'].get(t))
    kind = {10: 'WC', 7: 'DUŞ', 2: 'LV/YS', 4: 'ÇM/EV/BM'}.get(int(sb), '?')
    usb[rm] += sb; umb[rm] += mb; ufix[rm].append('%s(%g SB, %g MB)' % (kind, sb, mb))

# bizim: oda bazında SB (zemin)
DZ_F = []
import pickle
osb = collections.defaultdict(float)
F = M.fixtures(R, wet, W)
GSB = dict(WC=10.0, DUS=7.0, LV=2.0, CM=4.0, YS=2.0, EV=4.0, BM=4.0)
GYB = dict(WC=0.5, DUS=1.0, LV=0.5, CM=1.0, EV=0.5, BM=1.0, YS=0.0)
GYBS = dict(DUS=1.0, LV=0.5, EV=0.5)
ofix = collections.defaultdict(list)
oyb = collections.defaultdict(float)
for f in F:
    if f['room'] and f['kind'] in GSB:
        key = f['room']['name'] + '@%d,%d' % (round(f['room']['xy'][0]), round(f['room']['xy'][1]))
        osb[key] += GSB[f['kind']]; ofix[key].append(f['kind'] + ('(alaturka)' if f.get('alaturka') else ''))
        oyb[key] += GYB[f['kind']] + GYBS.get(f['kind'], 0)
rows_r = []
for key in sorted(set(usb) | set(osb)):
    if key == '?':
        continue
    rows_r.append((key.split('@')[0], key.split('@')[1], ', '.join(ufix.get(key, [])) or '-', ', '.join(ofix.get(key, [])) or '-',
                   '%g' % usb.get(key, 0), '%g' % osb.get(key, 0), '%g' % umb.get(key, 0), '%g' % oyb.get(key, 0)))
u_ys_out = [u for u in U if in_w(u['p'], WZ) and u['name'] == 'SUZGEC1' and room_of(u['p']) == '?']

# ------------------------------------------------------------------ 3. rögarlar
urog = {u['at']['R']: (u['p'][0] - TEMEL_OFF, u['p'][1]) for u in U if u['name'] == 'MTY-ROGAR KAT' and in_w(u['p'], WT)}
urog_sema = [u['at'].get('R') for u in U if u['name'] == 'MTY-ROGAR KAT' and not in_w(u['p'], WT)]
uconn = collections.defaultdict(list)
for kn, p in ukol.get('T', {}).items():
    rr = min((r for r in urog if r != 'PB'), key=lambda r: abs(urog[r][1] - p[1]))
    uconn[rr].append(kn)
utaban = collections.Counter(u['at'].get('TAVANDAN') for u in U if in_w(u['p'], WT) and 'TAVANDAN' in u['at'])

# ------------------------------------------------------------------ 4. çap etiketleri (zemin kat planı)
upis = collections.Counter()
utem = collections.Counter()
for u in U:
    if not in_w(u['p'], WZ):
        continue
    if u['lay'] == 'MTY-PISSU-CAP' and 'PS' in u['at']:
        upis[(u['at']['PSCP'], u['at']['PS'])] += 1
    if u['lay'] == 'MTY-TEMIZSU-CAP':
        for a, b in (('SOCP', 'SO'), ('SCCP', 'SC')):
            if u['at'].get(b):
                utem[(a[:2], u['at'].get(a), u['at'][b])] += 1
SL = 2500.0
zx0, zx1 = 3 * SL, 4 * SL


def dxf_olc(path):
    """zemin kat paftası: çap etiket sayımları + kural ölçümleri (etiket-boru ekseni uzaklığı, sıcak-soğuk paralellik,
    kolon no balonu çakışması, balkon süzgeci)"""
    from shapely.geometry import LineString as LS, Point as PT
    from shapely import STRtree
    od = ezdxf.readfile(path)
    opis, otem = collections.Counter(), collections.Counter()
    pipes = collections.defaultdict(list)
    other = []
    ins = []
    for e in od.modelspace():
        t = e.dxftype()
        if t == 'LWPOLYLINE':
            pts = [(v[0], v[1]) for v in e.get_points()]
            if not pts or not (zx0 <= pts[0][0] <= zx1 and 0 <= pts[0][1] <= 2800) or len(pts) < 2:
                continue
            lay = e.dxf.layer
            if any(k in lay for k in ('SOGUKSU', 'SICAKSU', 'PISSU-BORU', 'PIS-SU', 'YAGMUR-BORUSU')):
                pipes[lay].append(LS(pts))
            other.append(LS(pts))
        elif t == 'LINE':
            a, b = e.dxf.start, e.dxf.end
            if zx0 <= a.x <= zx1 and 0 <= a.y <= 2800:
                other.append(LS([(a.x, a.y), (b.x, b.y)]))
        elif t == 'INSERT':
            p = e.dxf.insert
            if zx0 <= p.x <= zx1 and 0 <= p.y <= 2800:
                ins.append(e)
    for e in ins:
        at = {a.dxf.tag.split('_0')[0]: a.dxf.text for a in e.attribs}
        if e.dxf.name == 'MTY-PIS SU CAP SB':
            opis[(at.get('PSCP'), at.get('PS'))] += 1
        if e.dxf.name == 'MTY-TEMIZ SU CAP MB':
            for a, b in (('SOCP', 'SO'), ('SCCP', 'SC')):
                if at.get(b):
                    otem[(a[:2], at.get(a), at.get(b))] += 1
    cold = [l for k, v in pipes.items() if 'SOGUK' in k for l in v]
    hot = [l for k, v in pipes.items() if 'SICAK' in k for l in v]
    pis = [l for k, v in pipes.items() if 'PIS' in k for l in v]
    def eksen(name, ls):
        ds = []
        for e in ins:
            if e.dxf.name == name and ls:
                q = PT(e.dxf.insert.x, e.dxf.insert.y)
                ds.append(min(l.distance(q) for l in ls))
        return (sum(ds) / len(ds), sum(1 for d in ds if d <= 1.0), len(ds)) if ds else (0, 0, 0)
    ct = STRtree(cold) if cold else None
    hl = sum(l.length for l in hot)
    par = 0.0
    if ct is not None:
        from shapely.ops import unary_union as UU
        cb = UU([c.buffer(12) for c in cold])
        par = sum(l.intersection(cb).length for l in hot)
    # kolon no balonu: çizgi çakışması
    tr = STRtree(other)
    nb, nhit = 0, 0
    for e in ins:
        if e.dxf.name == 'MTY-KOLON NO PIS SU':
            nb += 1
            r = 27.5 * abs(e.dxf.xscale)
            disk = PT(e.dxf.insert.x, e.dxf.insert.y).buffer(r)
            if any(other[i].intersects(disk) and other[i].distance(PT(e.dxf.insert.x, e.dxf.insert.y)) < r - 1.5 and
                   other[i].length > 2 * r + 2 for i in tr.query(disk)):
                nhit += 1
    suz = sum(1 for e in ins if e.dxf.name == 'SUZGEC1')
    return dict(opis=opis, otem=otem, cap_pis=eksen('MTY-PIS SU CAP SB', pis), cap_tem=eksen('MTY-TEMIZ SU CAP MB', cold),
                sicak_m=hl / 100, paralel=(par / hl if hl else 0), balon=(nb, nhit), suzgec=suz)


O1, O2 = dxf_olc(OUT_DXF1), dxf_olc(OUT_DXF)
opis, otem = O2['opis'], O2['otem']

# ------------------------------------------------------------------ 5. yağmur inişleri
uyb = {u['at']['K']: u['p'] for u in U if in_w(u['p'], WZ) and re.fullmatch(r'YB\d+', u['at'].get('K', ''))}
oyb_pts = [a[1][0] for a in R if a[0] == 'T' and 'yağmur' in a[2][0]]
yb_d = [min(math.hypot(q[0] - p[0], q[1] - p[1]) for q in oyb_pts) for p in uyb.values()]

# ------------------------------------------------------------------ 6. pafta düzeni (kullanıcı: başlık yazıları soldan sağa)
ut = []
for e in msp.query('TEXT MTEXT'):
    t = e.dxf.text if e.dxftype() == 'TEXT' else e.plain_text()
    if ('ÖLÇEK' in t or 'ŞEMA' in t.upper() or 'DETAY' in t.upper()) and e.dxf.insert.y < -440000 and e.dxf.insert.x < 271000:
        if t.strip() != 'ÖLÇEK:1/250':
            ut.append((round(e.dxf.insert.x), round(e.dxf.insert.y), t.replace('\n', ' ')[:60]))
ut.sort()


# ------------------------------------------------------------------ MD
def tbl(h, rows):
    s = '| ' + ' | '.join(h) + ' |\n|' + '---|' * len(h) + '\n'
    for r in rows:
        s += '| ' + ' | '.join(str(x) for x in r) + ' |\n'
    return s


def dsum(OZx, key):
    return sum(v['yb'] for v in OZx['kat']['Z']['temiz'].values())


ek2 = OZ.get('ek_makine', {})
ana_m = OZ.get('metraj', {}).get('TEMİZ SU ANA HAT (PPRC) Ø25', 0)
kr = OZ.get('kolon_rogar', [])
md = ['# Uçtan uca sıhhi tesisat denemesi — karşılaştırma (new_block.dxf) — R1 (önce) / R2 (sonra)\n',
      'Tarih: 14.10.2026. R1: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME.dxf`; **R2 (14.10.2026 kullanıcı kuralları):** '
      '`proje/denemeler/uctan_uca/NB_SIHHI_DENEME_R2.dxf` (`motor/deneme/uctan_uca/nb.py` + `r2.py`).',
      'Referans: kullanıcının aynı dosyadaki MTY çizimi (MTY-* katmanları). Kullanıcı çizimi tanımaya **girmedi**; yalnız burada okundu.',
      'Koordinatlar zemin kat mimari kaynak koordinatıdır (cm). Kullanıcının kolon konumu = "MTY-KOLON NO" bloğunun yerleştirme noktası '
      '(P1, P3, P4, P6, P8, P9 için kullanıcının pis su borusunun ucuyla 8 cm içinde çakışıyor; yani gerçek kolon yeri).\n',
      '## 0. 14.10.2026 kuralları — önce / sonra\n',
      tbl(['Kural', 'R1 (önce)', 'R2 (sonra)'], [
          ('YB/SB yöntemi MTY ile aynı (MB/inç\'e geçilmez)', 'YB / SB, Ø mm', 'aynı (değişmedi): YB / SB, Ø mm'),
          ('Kolon–rögar bağlantı çapı', 'Ø100 (kolon çapından)', 'hesap: kolon toplam SB %s → Ø100 yeterli (≤160 SB, zemin altı en az Ø100); kullanıcı Ø125 çizmiş → '
           'hesap Ø125 GEREKTİRMİYOR, Ø100 yazıldı. Fark: kullanıcı bir kademe büyük seçmiş (emniyet/tercih)' % ', '.join('%s %g' % (k[0], k[1]) for k in kr)),
          ('Her dairede ÇM + BM hattı', 'mimaride yoksa yok (3. daire konumunda ÇM ve BM eksik)',
           'eklendi: ' + '; '.join('%s kat: %s' % (k, ', '.join('%s D%d' % (a, b) for a, b in v)) for k, v in ek2.items()) + ' ("EK" işaretli, pis su + soğuk su bağlı)'),
          ('Balkon süzgeci pis suya bağlanmaz', 'balkon süzgeci yok', '%d balkon süzgeci (kat başına %d), Ø50 ayrı süzgeç hattı ile en yakın yağmur inişine; pis su ağına bağlı süzgeç: 0'
           % (OZ['adet'].get('BALKON_SUZGEC', 0), O2['suzgec'])),
          ('Daire içi sıcak + soğuk yan yana', 'sıcak kombiden ayrı A* ile (paralel oran %%%d)' % round(100 * O1['paralel']),
           'sıcak = soğuk ağacında kombi→sıcak armatür yolları, 7 cm paralel öteleme (zemin kat sıcak hattın %%%d\'i soğuğa ≤12 cm paralel)' % round(100 * O2['paralel'])),
          ('Kolonlar mahal köşesinden; şaft/ortak duvar', 'klozet duvarında en yakın köşe; kullanıcıya ort. %d cm' % ORT1,
           'yalnız köşe adayları (gerçek duvar = birleşik ≥100 cm eksen çizgisi), SB ağırlıklı boru boyu + "mek. havl." şaftı + komşu ıslak hacim puanı; '
           'kullanıcıya ort. **%d cm** (tablo 1)' % ORT2),
          ('Kolon numarası P1.. (kullanıcı biçimi), sembol yanında, çakışmasız', 'P1.. (sıra daire→banyo/wc/mutfak), 45° sabit ofset; çizgiye binen balon %d/%d'
           % (O1['balon'][1], O1['balon'][0]), 'P1.. kullanıcı sırası (daire→mutfak/wc/banyo/duş = kullanıcının P1..P9 ile aynı); 16 yön × 5 mesafe aramayla boş yer; '
           'çizgiye binen balon %d/%d' % (O2['balon'][1], O2['balon'][0])),
          ('YB/SB etiketi boru ekseninde', 'pis su ekleme noktası–boru ort. %.1f cm; temiz su %.1f cm (%d/%d eksende)'
           % (O1['cap_pis'][0], O1['cap_tem'][0], O1['cap_tem'][1], O1['cap_tem'][2]),
           'pis su ort. %.1f cm; temiz su ort. %.1f cm (%d/%d eksende); blok boru doğrultusunda döndürülmüş, ölçek 8'
           % (O2['cap_pis'][0], O2['cap_tem'][0], O2['cap_tem'][1], O2['cap_tem'][2])),
          ('Taşıyıcı kolon / asansör / şaft / enerji odası', 'yalnız betonarme kontrolü (0 çakışma)',
           'geometrik kontrol (`nb.yasak_kontrol`): betonarme + asansör boşluğu + enerji odası, tüm hatlar, 3 kat → %d ihlal; router bunları yasak alan sayar'
           % len([r for r in OZ.get('yasak', []) if r['tip'] != 'DAİRE İÇİ ANA HAT'])),
          ('Ana besleme / kolektör daire içinden geçmez', 'merdiven holünde 9\'lu kolon kutusu, 3. daireye hol boyunca ~9 m dikey hat; şebeke hattı daire duvarı boyunca',
           'ADK kolonları daire kapılarının yanında, holde (%s); kolon→kapı hatları yalnız ortak alan ızgarasında (daire mahalleri kapalı), toplam %.1f m / 9 daire; '
           'daire içine giren ana hat: %d' % (', '.join('%s: D%s' % (k, '/'.join(str(x) for x in v['daire'])) for k, v in OZ.get('adk', {}).items()), ana_m,
                                              len([r for r in OZ.get('yasak', []) if r['tip'] == 'DAİRE İÇİ ANA HAT']))),
          ('Alt/üst kat planı farklı → geçiş uyarlanır, tüm kolonlar numaralı', 'üst katta farklı adlı ıslak hacimler (1. kat wc-banyo, wc-duş) tanınmıyordu; 1. kat D6 wc-duş tesisatsızdı',
           'wc-banyo / wc-duş tanınır; ıslak hacim → daire ataması kapılardan yürüme mesafesiyle; zeminde karşılığı olmayan 1. kat wc-duş için yeni köşe kolonu %s '
           '(alt katlardan temele iner, çatıya çıkar, rögar R2)' % ', '.join(c[0] for c in OZ['kolon'] if c[0] not in [k[0] for k in OZ1['kolon']])),
          ('Depo: bodrumda hidrofor, yoksa çatı', 'parametre: çatı', 'otomatik karar: %s (%s)' % (OZ['depo']['karar'], OZ['depo']['neden'])),
          ('Pafta sonu lejant + adet tablosu', 'antet yanında sabit lejant', '"LEJANT VE MALZEME LİSTESİ" paftası: sembol.otomatik_lejant (kullanılan %d sembol türü, adetli) + armatür adet + boru metrajı'
           % len(OZ.get('lejant', {}).get('sembol_adet', {}))),
      ]),
      '\n## 1. Pis su kolonları (zemin kat)\n',
      'Kolon sayısı: kullanıcı **%d** (zemin %d / 1. kat %d / 2. kat %d / temel %d etiket), motor **%d** (her katta aynı hizada).\n' % (
          len(ukol.get('Z', {})), len(ukol.get('Z', {})), len(ukol.get('1', {})), len(ukol.get('2', {})), len(ukol.get('T', {})), len(OZ['kolon'])),
      tbl(['Kullanıcı', 'Islak hacim', 'Kullanıcı konum', 'R1 kolon / konum', 'R1 fark (cm)', 'R2 kolon / konum', 'R2 fark (cm)'], rows_k),
      '\nOrtalama fark: R1 **%d cm** → R2 **%d cm**. R2 numaralandırması kullanıcınınkiyle aynı (P1 D1 mutfak, P2 D1 wc-lvb, P3 D1 banyo, ... P9 duş). '
      'Kalan büyük farklar: D3 mutfak (R2 eviyeye en yakın köşe = cephe köşesi, kullanıcı tezgâh ucu salon duvarı; o duvar parçaları <100 cm olduğu için köşe adayı çıkmadı), '
      'duş (R2 tekne köşesi, kullanıcı balkon tarafı süzgeç köşesi), banyolar ~45 cm (aynı duvar, bölme duvarı ucu yerine ıslak hacim köşesi).\n' % (ORT1, ORT2),
      '## 2. Islak hacim armatürleri ve yükler (zemin kat)\n',
      tbl(['Mahal', 'Etiket konumu', 'Kullanıcı armatürleri', 'Motorun tanıdığı (mimari)', 'SB kull.', 'SB motor R1', 'MB kull. (SO+SC)', 'YB motor (SO+SC)'], rows_r),
      '\nR2: 3. daire mutfağına **BM (EK, 4 SB)** ve wc+banyoya **ÇM (EK, 4 SB)** eklendi → mutfak 8 SB, wc+banyo 25 SB (kullanıcıyla aynı). '
      'Kullanıcı balkon / ıslak hacim dışı **%d adet yer süzgeci** (SUZGEC1) çizmiş; R2 zemin katta **%d** balkon süzgeci (ayrı yağmur hattı).\n' % (len(u_ys_out), O2['suzgec']),
      '## 3. Rögarlar (temel planı)\n',
      tbl(['', 'Kullanıcı', 'Motor R2'], [
          ('Rögar sayısı', '%d + PB' % len([r for r in urog if r != 'PB']), '%d + PB' % len([r for r in OZ['rogar'] if r != 'PB'])),
          ('Cephe', 'doğu (x≈%d)' % round(list(urog.values())[0][0]), 'doğu (x≈%d)' % OZ['rogar']['R1']['p'][0]),
      ] + [('%s konumu / kolonlar' % r, '%s / %s' % (('%d, %d' % tuple(round(v) for v in urog[r])) if r in urog else '-', ', '.join(sorted(uconn.get(r, [])))),
            '%s / %s' % (('%d, %d' % tuple(OZ['rogar'][r]['p'])) if r in OZ['rogar'] else '-', ', '.join(OZ['rogar'].get(r, {}).get('kols', []))))
           for r in sorted(set(urog) | set(OZ['rogar']), key=lambda s: (s == 'PB', s))] + [
          ('Kolon→rögar boru çapı', ', '.join('%s x%d' % (k, v) for k, v in utaban.items()),
           'hesap Ø100 (kolon başı en çok %g SB ≤ 160); rögarlar arası Ø150 %%1' % max([k[1] for k in kr] or [0])),
          ('Şemadaki rögar blokları', '%d (MTY-ROGAR KAT)' % len(urog_sema), 'rögar şeması: R1..R4 + PB (PVC ROGAR bloğu)')]),
      '\n## 4. Çap etiketleri (zemin kat planı)\n',
      '### Pis su (Ø / SB)\n',
      tbl(['Etiket', 'Kullanıcı adet', 'R1 adet', 'R2 adet'], [('%s / %s' % k, upis.get(k, 0), O1['opis'].get(k, 0), O2['opis'].get(k, 0))
                                                               for k in sorted(set(upis) | set(O1['opis']) | set(O2['opis']), key=str)]),
      '\n### Temiz su (çap / yük)\n',
      tbl(['Hat', 'Çap', 'Yük', 'Kullanıcı adet', 'R1 adet', 'R2 adet'],
          [(k[0].replace('SO', 'soğuk').replace('SC', 'sıcak'), k[1], k[2], utem.get(k, 0), O1['otem'].get(k, 0), O2['otem'].get(k, 0))
           for k in sorted(set(utem) | set(O1['otem']) | set(O2['otem']), key=str)]),
      '\nYöntem kararı (14.10.2026): YB ve SB yöntemi MTY ile aynı kalır, **MB / inç\'e geçilmedi**. Kullanıcının bu dosyadaki çiziminde temiz su MB / inç ile yazılmış '
      '(lavabo 0,75 / duş 2,5 / çamaşır 1,5 / bulaşık 1,5 / eviye 1 MB); motor YB (gp.YB) + Ø mm. R2\'de sıcak hat soğukla aynı etikette (SO üstte, SC altta) yazılır. '
      'Daire ana hattı: kullanıcı 9,5 / 9,5 / 11,5 MB (1 1/4"), R1 %s YB, R2 %s YB.\n' % (
          ' / '.join('D%s %g' % (k, v['yb']) for k, v in OZ1['kat']['Z']['temiz'].items()),
          ' / '.join('D%s %g' % (k, v['yb']) for k, v in OZ['kat']['Z']['temiz'].items())),
      '## 5. YB / SB toplamları\n',
      tbl(['', 'Kullanıcı', 'R1', 'R2'], [
          ('Bina toplam temiz su yükü', '-', '%g YB' % OZ1['sema']['ybt'], '%g YB' % OZ['sema']['ybt']),
          ('Yağmur inişi', '%d (YB1..YB%d)' % (len(uyb), len(uyb)), '%d' % len(oyb_pts), '%d (+ balkon süzgeç bağlantıları)' % len(oyb_pts)),
          ('Yağmur hesabı', '-', 'P=%.1f m², D=%.2f cm → Ø100' % (OZ1['sema']['yagmur']['P'], OZ1['sema']['yagmur']['D']),
           'P=%.1f m², D=%.2f cm → Ø100' % (OZ['sema']['yagmur']['P'], OZ['sema']['yagmur']['D']))]),
      '\n## 6. Pafta düzeni\n',
      tbl(['#', 'Kullanıcı (soldan sağa, sıhhi sıra)', 'Motor R2'],
          [(i + 1, ut[i][2] if i < len(ut) else '', (OZ['sema']['frames'] + ['LEJANT VE MALZEME LİSTESİ'])[i] if i < len(OZ['sema']['frames']) + 1 else '')
           for i in range(max(len(ut), len(OZ['sema']['frames']) + 1))]),
      '\n## 7. Kontroller (motor)\n',
      tbl(['Kontrol', 'R1', 'R2'], [(k, (v if not isinstance(v, list) else len(v)), (OZ['kontrol'].get(k) if not isinstance(OZ['kontrol'].get(k), list) else len(OZ['kontrol'][k])))
                                    for k, v in OZ1['kontrol'].items()] + [
          ('yasak bölge (betonarme/asansör/enerji odası) ihlali', '-', len([r for r in OZ.get('yasak', []) if r['tip'] != 'DAİRE İÇİ ANA HAT'])),
          ('daire içine giren ana hat', '-', len([r for r in OZ.get('yasak', []) if r['tip'] == 'DAİRE İÇİ ANA HAT'])),
          ('kolon no balonu çizgiye biniyor (zemin)', '%d / %d' % (O1['balon'][1], O1['balon'][0]), '%d / %d' % (O2['balon'][1], O2['balon'][0]))]),
      '\n## 8. Açık kalanlar / kullanıcıya sorulacaklar\n',
      tbl(['Konu', 'Durum'], [
          ('Kolon–rögar çapı', 'Hesap Ø100 diyor, kullanıcı Ø125 çizmiş. Kullanıcı tercihi olarak Ø125\'e sabitlensin mi? (PRM ile tek satır)'),
          ('ADK / sayaç kurgusu', 'Çatı deposundan iki ADK kolonu (D1/D2 grubu, D3 grubu) + kat sahanlığında daire sayacı. Kullanıcının alıştığı "zemin katta toplu sayaç" tercihi mi?'),
          ('1. kat sağ wc-lvb → yüklük', 'Mimaride 1. katta bu mahal yüklük; P2 kolonu o katta armatürsüz geçer.'),
          ('1. kat D6 wc-duş (P10)', 'Kullanıcı çiziminde 1. katta 9 kolon etiketi var; motor bu wc-duş için ayrı P10 açtı (zeminde D1 banyosunun köşesinden geçer). '
           'Kullanıcı bu hacmi mevcut bir kolona (P3) yatay bağlamayı mı tercih eder?'),
          ('D3 mutfak kolonu', 'Eviyeye en yakın köşe cephe köşesi seçildi (kombinin yanı); kullanıcı tezgâh ucunu (salon duvarı) seçmiş.'),
          ('Çatı planı, WC havalandırma izometrisi, kesit/görünüşler', 'Bu revizyonda yapılmadı (R1\'den beri eksik).'),
          ('Etiket ölçeği', 'Çap/yük etiketleri ölçek 8 (kullanıcı 10); kalabalık mahallerde 10 çakışma üretir.'),
      ]),
      ]
open(os.path.join(HERE, 'KARSILASTIRMA.md'), 'w').write('\n'.join(md) + '\n')
print('\n'.join(md)[:6000])
