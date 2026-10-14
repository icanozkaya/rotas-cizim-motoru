"""Motor çıktısı (NB_SIHHI_DENEME.dxf + nb_ozet.json) ile kullanıcının aynı dosyadaki MTY çizimini karşılaştırır,
farkları KARSILASTIRMA.md'ye yazar.  Çalıştır: python3 karsilastir.py  (önce nb.py çalışmış olmalı)"""
import json, math, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ezdxf
import mimari as M

OZ = json.load(open('/tmp/claude-0/uu/nb_ozet.json'))
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


ours = {c[0]: dict(typ=c[1], daire=c[2], p=tuple(c[3]), dn=c[4], sb=c[5]) for c in OZ['kolon']}
rows_k = []
used = set()
for kn, p in sorted(ukol.get('Z', {}).items(), key=lambda t: int(t[0][1:])):
    rm = room_of(p)
    cand = sorted(ours.items(), key=lambda t: math.hypot(t[1]['p'][0] - p[0], t[1]['p'][1] - p[1]))
    on, oc = next((c for c in cand if c[0] not in used), cand[0])
    used.add(on)
    rows_k.append((kn, rm.split('@')[0], '%d, %d' % (round(p[0]), round(p[1])), on, oc['typ'],
                   '%d, %d' % oc['p'], round(math.hypot(oc['p'][0] - p[0], oc['p'][1] - p[1]))))

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
od = ezdxf.readfile(OUT_DXF)
SL = 2500.0
zx0, zx1 = 3 * SL, 4 * SL
opis, otem = collections.Counter(), collections.Counter()
for e in od.modelspace().query('INSERT'):
    p = e.dxf.insert
    if not (zx0 <= p.x <= zx1 and 0 <= p.y <= 2800):
        continue
    at = {a.dxf.tag.split('_0')[0]: a.dxf.text for a in e.attribs}
    if e.dxf.name == 'MTY-PIS SU CAP SB':
        opis[(at.get('PSCP'), at.get('PS'))] += 1
    if e.dxf.name == 'MTY-TEMIZ SU CAP MB':
        for a, b in (('SOCP', 'SO'), ('SCCP', 'SC')):
            if at.get(b):
                otem[(a[:2], at.get(a), at.get(b))] += 1

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


md = ['# Uçtan uca sıhhi tesisat denemesi — karşılaştırma (new_block.dxf)\n',
      'Tarih: 14.10.2026. Motor çıktısı: `proje/denemeler/uctan_uca/NB_SIHHI_DENEME.dxf` (`motor/deneme/uctan_uca/nb.py`).',
      'Referans: kullanıcının aynı dosyadaki MTY çizimi (MTY-* katmanları). Kullanıcı çizimi tanımaya **girmedi**; yalnız burada okundu.',
      'Koordinatlar zemin kat mimari kaynak koordinatıdır (cm). Kullanıcının kolon konumu = "MTY-KOLON NO" dinamik bloğunun yerleştirme noktası (yaklaşık).\n',
      '## 1. Pis su kolonları (zemin kat)\n',
      'Kolon sayısı: kullanıcı **%d** (zemin %d / 1. kat %d / 2. kat %d / temel %d etiket), motor **%d** (her katta aynı hizada).\n' % (
          len(ukol.get('Z', {})), len(ukol.get('Z', {})), len(ukol.get('1', {})), len(ukol.get('2', {})), len(ukol.get('T', {})), len(ours)),
      tbl(['Kullanıcı', 'Islak hacim', 'Kullanıcı konum', 'Motor', 'Motor tip', 'Motor konum', 'Fark (cm)'], rows_k),
      '\nNot: kolon adları farklı sıralanıyor (kullanıcı: P1/P4 mutfaklar, P2/P5 wc-lvb, P3/P6 banyo, P7 3. daire mutfak, P8 wc+banyo, P9 duş; '
      'motor: daire daire banyo → wc → mutfak). Eşleme ıslak hacme göre yapıldı.\n',
      '## 2. Islak hacim armatürleri ve yükler (zemin kat)\n',
      tbl(['Mahal', 'Etiket konumu', 'Kullanıcı armatürleri', 'Motorun tanıdığı', 'SB kull.', 'SB motor', 'MB kull. (SO+SC)', 'YB motor (SO+SC)'], rows_r),
      '\nKullanıcı ayrıca balkon / ıslak hacim dışı **%d adet yer süzgeci** (SUZGEC1, 2 SB) çizmiş; motor balkon süzgeci koymuyor.\n' % len(u_ys_out),
      '## 3. Rögarlar (temel planı)\n',
      tbl(['', 'Kullanıcı', 'Motor'], [
          ('Rögar sayısı', '%d + PB' % len([r for r in urog if r != 'PB']), '%d + PB' % len([r for r in OZ['rogar'] if r != 'PB'])),
          ('Cephe', 'doğu (x≈%d)' % round(list(urog.values())[0][0]), 'doğu (x≈%d)' % OZ['rogar']['R1']['p'][0]),
      ] + [('%s konumu / kolonlar' % r, '%s / %s' % (('%d, %d' % tuple(round(v) for v in urog[r])) if r in urog else '-', ', '.join(sorted(uconn.get(r, [])))),
            '%s / %s' % (('%d, %d' % tuple(OZ['rogar'][r]['p'])) if r in OZ['rogar'] else '-', ', '.join(OZ['rogar'].get(r, {}).get('kols', []))))
           for r in sorted(set(urog) | set(OZ['rogar']), key=lambda s: (s == 'PB', s))] + [
          ('Kolon→rögar boru çapı', ', '.join('%s x%d' % (k, v) for k, v in utaban.items()), 'Ø100 (kolon çapı, en az Ø100); rögarlar arası Ø150 %1'),
          ('Şemadaki rögar blokları', '%d (MTY-ROGAR KAT)' % len(urog_sema), 'rögar şeması: R1..R4 + PB (PVC ROGAR bloğu)')]),
      '\nKullanıcı rögar kolon gruplaması kolonların y konumuna göre çıkarıldı (en yakın rögar).\n',
      '## 4. Çap etiketleri (zemin kat planı)\n',
      '### Pis su (Ø / SB)\n',
      tbl(['Etiket', 'Kullanıcı adet', 'Motor adet'], [('%s / %s' % k, upis.get(k, 0), opis.get(k, 0)) for k in sorted(set(upis) | set(opis), key=str)]),
      '\n### Temiz su (çap / yük)\n',
      tbl(['Hat', 'Çap', 'Yük', 'Kullanıcı adet', 'Motor adet'],
          [(k[0].replace('SO', 'soğuk').replace('SC', 'sıcak'), k[1], k[2], utem.get(k, 0), otem.get(k, 0)) for k in sorted(set(utem) | set(otem), key=str)]),
      '\nKullanıcı temiz su çapını **inç** ("1\\"", "3/4\\"", "1 1/4\\"") ve yükü **MB** ile yazıyor; motor (p2 gp.dn_temiz) **Ø mm** ve **YB** yazıyor. '
      'Kullanıcının armatür yük birimleri: lavabo 0,75, duş 2,5, klozet 0,5, çamaşır 1,5, eviye 1, bulaşık 1,5, kombi 0,5 MB; '
      'motorun (gp.YB) değerleri: lavabo 0,5, duş 1, klozet 0,5, çamaşır 1, eviye 0,5, bulaşık 1. Daire ana hattı: kullanıcı 9,5 / 9,5 / 11,5 MB (1 1/4"), '
      'motor %s YB.\n' % ' / '.join('D%s %s' % (k, fmt) for k, fmt in [(dk, '%g' % v['yb']) for dk, v in OZ['kat']['Z']['temiz'].items()]),
      '## 5. YB / SB toplamları\n',
      tbl(['', 'Kullanıcı', 'Motor'], [
          ('Zemin kat toplam SB (ıslak hacimler)', '%g' % sum(v for k, v in usb.items() if k != '?'), '%g' % sum(osb.values())),
          ('Bina toplam temiz su yükü', '-', '%g YB (soğuk, 9 daire)' % OZ['sema']['ybt']),
          ('Yağmur inişi', '%d (YB1..YB%d)' % (len(uyb), len(uyb)), '%d (mimari "yağmur inişi" notlarından; ort. konum farkı %d cm)' % (
              len(oyb_pts), round(sum(yb_d) / max(1, len(yb_d))))),
          ('Yağmur hesabı', '-', 'P=%.1f m², f=%d, D=%.2f cm → Ø100' % (OZ['sema']['yagmur']['P'], OZ['sema']['yagmur']['f'], OZ['sema']['yagmur']['D']))]),
      '\n## 6. Pafta düzeni\n',
      tbl(['#', 'Kullanıcı (soldan sağa, sıhhi sıra)', 'Motor'],
          [(i + 1, ut[i][2] if i < len(ut) else '', OZ['sema']['frames'][i] if i < len(OZ['sema']['frames']) else '')
           for i in range(max(len(ut), len(OZ['sema']['frames'])))]),
      '\n## 7. Kontroller (motor)\n',
      tbl(['Kontrol', 'Sonuç'], [(k, v if not isinstance(v, list) else len(v)) for k, v in OZ['kontrol'].items()]),
      '\n## 8. Yorum: önemli farklar ve nedenleri\n',
      tbl(['Konu', 'Kullanıcı (MTY)', 'Motor', 'Değerlendirme'], [
          ('Kolon sayısı / ıslak hacim eşlemesi', '9 kolon: her ıslak hacim kendi kolonu', '9 kolon, aynı ıslak hacimler', 'UYUMLU'),
          ('Banyo kolon yeri', 'banyo ile wc-lvb arasındaki duvarda, "mek. havl." şaftına yakın', 'klozetin arka duvarında en yakın köşe', 'FARKLI (~150 cm). Kural: şaft / ortak duvar tercih edilmeli'),
          ('Mutfak kolon yeri', 'tezgâh ucunda balkon duvarı dibi', 'eviye arkasında duvar dibi', 'FARKLI (~120 cm)'),
          ('Islak hacim SB', 'banyo 25, wc-lvb 12, mutfak 8, wc+banyo 25, duş 13', 'banyo 25, wc-lvb 12, mutfak 8 (3. daire 4), wc+banyo 21, duş 11',
           '3. daire mutfağında bulaşık mak. ve wc+banyoda çamaşır mak. mimaride işaretli değil (motor bulamadı); kullanıcı ekledi'),
          ('Klozet tipi (wc-lvb)', 'klozet bloğu (10 SB)', 'mimarideki alaturka hela çizimi -> WC (alaturka) 10 SB', 'SB aynı'),
          ('1. kat sağ wc-lvb', 'kolon etiketi her katta (P2)', 'mimaride 1. katta bu mahal "yüklük" -> armatür yok, kolon geçer', 'KULLANICIYA SORULMALI'),
          ('Temiz su yük birimi', 'MB, armatür başına lavabo 0,75 / duş 2,5 / çamaşır 1,5 / bulaşık 1,5 / eviye 1 / kombi 0,5', 'gp.YB: lavabo 0,5 / duş 1 / çamaşır 1 / bulaşık 1 / eviye 0,5',
           'FARKLI: daire ana hattı kullanıcı 9,5-11,5 MB 1 1/4", motor 4-5,5 YB Ø25. Motor tablosu kullanıcınınkine çekilmeli'),
          ('Temiz su çap yazımı', 'inç (1/2", 3/4", 1", 1 1/4")', 'Ø mm (Ø20, Ø25)', 'FARKLI - kullanıcı tarzı inç'),
          ('Kolon -> rögar çapı', 'Ø125 (kolon bağlantıları), Ø150 %1 (rögarlar arası)', 'Ø100 kolon bağlantısı, Ø150 %1 rögarlar arası', 'FARKLI: kullanıcı Ø125 kullanıyor'),
          ('Rögar dizilimi', 'doğu cephesi, R1..R4 + PB (PB R4 hizasında, ~500 cm doğuda)', 'doğu cephesi, R1..R4 + PB (R4 hizasında, 220 cm doğuda)', 'BÜYÜK ÖLÇÜDE UYUMLU; kolon gruplaması kısmen farklı (P7/P9)'),
          ('Balkon yer süzgeçleri', 'var (5 adet, zemin)', 'yok', 'EKSİK'),
          ('Çatı planı', 'var (sıhhi sırasında)', 'yok', 'EKSİK'),
          ('WC havalandırma izometrisi', 'var (detay paftasında)', 'yok (yalnız MTY-SIHHİ DETAYLAR bloğu)', 'EKSİK'),
          ('Temiz su güzergâhı', 'kolon kutusundan daireye, antre duvarları boyunca kısa', 'A* router: merdiven holünden uzun dikey hatlar (3. daireye holün içinden)', 'İYİLEŞTİRİLMELİ'),
          ('Kolon şeması', 'tek şema, D1..D9 bloklar yan yana', 'p2 gsheet ile tek şema (3 grup x 3 kat), D1..D9', 'BENZER; 1. kattaki yüklük farkı şemada gösterilmiyor'),
      ]),
      ]
open(os.path.join(HERE, 'KARSILASTIRMA.md'), 'w').write('\n'.join(md) + '\n')
print('\n'.join(md)[:9000])
