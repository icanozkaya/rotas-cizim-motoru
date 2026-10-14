"""R3 saf geometri sembolleri (14.10.2026 B talimatı: MTY BLOKLARI KULLANILMAZ).

Motor (p2 gp / gsheet / cad) sembolleri `mtyblk.insert(<eski ad>, ...)` ile çağırır. Bu modül o çağrıyı yakalar:
  - eski ad -> `ROTAS-...` blok adı (ASCII, tire),
  - blok geometrisi BURADA sıfırdan çizilir (LINE / CIRCLE / LWPOLYLINE / HATCH, iç katman 0); eski bloktan YALNIZ
    sınır kutusu (yerleşim ölçeği aynı kalsın diye) ve öznitelik yuvaları (ATTDEF etiketi / konumu / yazı boyu) okunur,
    çizgi geometrisi alınmaz,
  - blok dosyası `/tmp/claude-0/uu3/r3blk/ROTAS__<ad>.dxf` olarak yazılır; p2 emit bu dosyadan gerçek blok (INSERT) üretir.
Kullanım: `semb3.kur()` (mtyblk.insert / mtyblk.find yamalanır), sonra motor normal çalışır.
`ciz(ad, msp_or_block, ...)`: ROTAS bloklarını doğrudan ezdxf düzenine yazmak için (lejant, havalandırma).
"""
import math, os, re
import ezdxf

BDIR = '/tmp/claude-0/uu3/r3blk'
TR = str.maketrans('İıŞşĞğÜüÖöÇç', 'IiSsGgUuOoCc')
KULLANILAN = {}                 # ROTAS adı -> eski ad
BILINMEYEN = set()


def yeni_ad(ad):
    a = ad.upper().translate(TR)
    a = re.sub(r'^MTY[- ]', '', a)
    a = a.replace(' KOLON', '-SEMA') if a.endswith(' KOLON') and not a.startswith('PIS SU') and 'TEMIZLEME' not in a \
        and 'HAVALIK' not in a else a
    a = re.sub(r'[^A-Z0-9]+', '-', a).strip('-')
    a = a.replace('MAKINASI1', 'MAKINESI').replace('1', '')
    return 'ROTAS-' + a


# ------------------------------------------------------------------ çizim yardımcıları (birim kutu -> hedef kutu)
class Kalem:
    def __init__(self, lay, bb):
        self.l = lay
        self.x0, self.y0, self.x1, self.y1 = bb
        self.w, self.h = max(1e-6, self.x1 - self.x0), max(1e-6, self.y1 - self.y0)

    def p(self, u, v):
        return (self.x0 + u * self.w, self.y0 + v * self.h)

    def pl(self, uv, close=False):
        self.l.add_lwpolyline([self.p(*q) for q in uv], close=close, dxfattribs={'layer': '0'})

    def ln(self, a, b):
        self.l.add_line(self.p(*a), self.p(*b), dxfattribs={'layer': '0'})

    def ci(self, u, v, r):
        """r: kutunun kısa kenarına oranla"""
        self.l.add_circle(self.p(u, v), r * min(self.w, self.h), dxfattribs={'layer': '0'})

    def el(self, u, v, ru, rv, n=28):
        self.pl([(u + ru * math.cos(2 * math.pi * i / n), v + rv * math.sin(2 * math.pi * i / n)) for i in range(n)], True)

    def dolu(self, uv):
        h = self.l.add_hatch(dxfattribs={'layer': '0'})
        h.set_solid_fill(color=256)
        h.paths.add_polyline_path([self.p(*q) for q in uv], is_closed=True)


def _kutu_merkez(bb, oran):
    """bb içinde, merkezli, en/boy oranı `oran` (w/h) olan en büyük kutu"""
    x0, y0, x1, y1 = bb
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if w / max(h, 1e-6) > oran:
        w = h * oran
    else:
        h = w / oran
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


# semboller2 (MTY'siz ortak ROTAS kütüphanesi, motor/deneme/semboller2/sembol2.py) karşılıkları: geometri oradan alınır,
# eski yerleşim kutusuna oran korunarak sığdırılır. Karşılığı olmayanlar aşağıdaki kendi çizimimizle.
S2_ESLE = [('KURESEL-VANA', 'ROTAS-SB-KURESEL-VANA'), ('CEKVALF', 'ROTAS-SB-CEKVALF'), ('PISLIK-TUTUCU', 'ROTAS-SB-PISLIK-TUTUCU'),
           ('SAYAC', 'ROTAS-SB-SU-SAYACI'), ('KOLON-NO', 'ROTAS-SB-KOLON-NO'), ('PIS-SU-KOLON', 'ROTAS-SB-KOLON-PIS'),
           ('KLOZET', 'ROTAS-KS-KLOZET'), ('LAVABO', 'ROTAS-KS-LAVABO'), ('DUS', 'ROTAS-KS-DUS'), ('EVIYE', 'ROTAS-KS-EVIYE'),
           ('CAMASIR', 'ROTAS-KS-CAMASIR-MAKINESI'), ('BULASIK', 'ROTAS-KS-BULASIK-MAKINESI'), ('KOMBI', 'ROTAS-KS-KOMBI'),
           ('YER-SUZGECI', 'ROTAS-SB-YER-SUZGECI'), ('ROTAS-SUZGEC', 'ROTAS-SB-BALKON-SUZGECI'), ('CATAL', 'ROTAS-KS-PVC-CATAL'),
           ('HAVALIK', 'ROTAS-KS-HAVALIK'), ('TEMIZLEME', 'ROTAS-KS-TEMIZLEME-KAPAGI'), ('ROGAR', 'ROTAS-KS-ROGAR'),
           ('ASPIRATOR', 'ROTAS-HV-ASPIRATOR'), ('CATI-FANI', 'ROTAS-HV-CATI-FANI-KESIT')]
S2_KULLANILAN = {}


def _s2_kopya(ad, lay, bb):
    """semboller2 bloğunun geometrisini (ATTDEF/TEXT hariç) hedef kutuya oran koruyarak kopyala"""
    hedef = None
    for anah, s2 in S2_ESLE:
        if anah in ad:
            hedef = s2
            break
    if hedef is None:
        return False
    try:
        import sys as _s
        _s.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'semboller2'))
        import sembol2 as S2
        from ezdxf import bbox
        from ezdxf.math import Matrix44
        tmp = ezdxf.new('R2010', setup=True)
        S2.ekle(tmp, [hedef])
        ents = [e for e in tmp.blocks.get(hedef) if e.dxftype() not in ('ATTDEF', 'TEXT', 'MTEXT', 'INSERT')]
        b = bbox.extents(ents)
        if not b.has_data:
            return False
        bw, bh = max(b.size.x, 1e-6), max(b.size.y, 1e-6)
        x0, y0, x1, y1 = bb
        k = min((x1 - x0) / bw, (y1 - y0) / bh)
        m = Matrix44.translate(-b.center.x, -b.center.y, 0) @ Matrix44.scale(k, k, 1) @ \
            Matrix44.translate((x0 + x1) / 2, (y0 + y1) / 2, 0)
        for e in ents:
            c = e.copy()
            c.transform(m)
            c.dxf.layer = '0'
            lay.add_entity(c)
        S2_KULLANILAN[ad] = hedef
        return True
    except Exception as ex:
        BILINMEYEN.add('%s (semboller2 hata: %s)' % (ad, ex))
        return False


def ciz_geometri(ad, lay, bb):
    """ad: ROTAS adı; bb: hedef sınır kutusu (blok koordinatı)"""
    if 'CAP' not in ad and 'SIHHI-DETAYLAR' not in ad and _s2_kopya(ad, lay, bb):
        return
    a = ad
    K = Kalem(lay, bb)
    if 'KURESEL-VANA' in a:                     # küresel vana: iki üçgen (papyon) + sap
        K = Kalem(lay, _kutu_merkez(bb, 1.6))
        K.pl([(0, 0.15), (1, 0.85), (1, 0.15), (0, 0.85)], True)
        K.ci(0.5, 0.5, 0.09)
        K.ln((0.5, 0.5), (0.5, 1.0)); K.ln((0.35, 1.0), (0.65, 1.0))
    elif 'CEKVALF' in a:                        # çek valf: papyon, akış yönündeki üçgen dolu + yön oku
        K = Kalem(lay, _kutu_merkez(bb, 1.6))
        K.pl([(0, 0.15), (1, 0.85), (1, 0.15), (0, 0.85)], True)
        K.dolu([(0.5, 0.5), (1, 0.85), (1, 0.15)])
        K.ln((0.15, 1.0), (0.85, 1.0)); K.pl([(0.72, 1.07), (0.85, 1.0), (0.72, 0.93)])
    elif 'PISLIK-TUTUCU' in a:                  # Y tipi pislik tutucu
        K = Kalem(lay, _kutu_merkez(bb, 1.4))
        K.ln((0, 0.7), (1, 0.7))
        K.ln((0.3, 0.7), (0.62, 0.15)); K.ln((0.55, 0.7), (0.78, 0.3))
        K.pl([(0.6, 0.12), (0.8, 0.27), (0.9, 0.12), (0.7, -0.03)], True)
        K.ln((0, 0.55), (0, 0.85)); K.ln((1, 0.55), (1, 0.85))
    elif 'SAYAC' in a:                          # su sayacı: daire + yatay ok + iki flanş çizgisi
        K = Kalem(lay, _kutu_merkez(bb, 1.0))
        K.ci(0.5, 0.5, 0.36)
        K.ln((0.22, 0.5), (0.78, 0.5)); K.pl([(0.64, 0.6), (0.78, 0.5), (0.64, 0.4)])
        K.ln((0.0, 0.3), (0.0, 0.7)); K.ln((1.0, 0.3), (1.0, 0.7))
        K.ln((0.0, 0.5), (0.14, 0.5)); K.ln((0.86, 0.5), (1.0, 0.5))
    elif 'KOLON-NO' in a or a.endswith('PIS-SU-KOLON-NO'):     # kolon no balonu: çift daire
        K = Kalem(lay, _kutu_merkez(bb, 1.0))
        K.ci(0.5, 0.5, 0.5); K.ci(0.5, 0.5, 0.44)
    elif a.endswith('PIS-SU-KOLON'):            # plan: pis su kolonu (daire + çarpı)
        K = Kalem(lay, _kutu_merkez(bb, 1.0))
        K.ci(0.5, 0.5, 0.5)
        K.ln((0.15, 0.15), (0.85, 0.85)); K.ln((0.15, 0.85), (0.85, 0.15))
    elif 'CAP' in a:                            # çap / yük etiketi: yalnız öznitelik yuvaları (geometri yok)
        pass
    elif 'KLOZET' in a:                         # alafranga klozet: rezervuar + oval hazne
        K.pl([(0.0, 0.62), (1.0, 0.62), (1.0, 1.0), (0.0, 1.0)], True)
        K.el(0.5, 0.33, 0.38, 0.32)
        K.el(0.5, 0.33, 0.26, 0.2)
    elif 'LAVABO' in a:                         # lavabo: tezgâh + oval tekne + batarya
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
        K.el(0.5, 0.45, 0.36, 0.3)
        K.ci(0.5, 0.45, 0.05)
        K.ln((0.5, 0.75), (0.5, 0.95))
    elif 'DUS' in a:                            # duş teknesi: kare + köşegen + gider
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
        K.pl([(0.08, 0.08), (0.92, 0.08), (0.92, 0.92), (0.08, 0.92)], True)
        K.ln((0.08, 0.92), (0.92, 0.08))
        K.ci(0.5, 0.5, 0.07)
    elif 'EVIYE' in a:                          # eviye: tezgâh + iki hazne
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
        K.pl([(0.06, 0.12), (0.46, 0.12), (0.46, 0.85), (0.06, 0.85)], True)
        K.pl([(0.54, 0.12), (0.94, 0.12), (0.94, 0.85), (0.54, 0.85)], True)
        K.ci(0.26, 0.48, 0.05); K.ci(0.74, 0.48, 0.05)
    elif 'CAMASIR' in a:                        # çamaşır makinesi: kutu + tambur
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
        K.ci(0.5, 0.45, 0.32); K.ci(0.5, 0.45, 0.22)
        K.ln((0, 0.86), (1, 0.86))
    elif 'BULASIK' in a:                        # bulaşık makinesi: kutu + raf çizgileri
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
        K.ln((0, 0.86), (1, 0.86))
        for v in (0.25, 0.45, 0.65):
            K.ln((0.12, v), (0.88, v))
    elif 'KOMBI' in a:                          # kombi: gövde + ekran + baca
        K.pl([(0, 0), (1, 0), (1, 0.9), (0, 0.9)], True)
        K.pl([(0.25, 0.55), (0.75, 0.55), (0.75, 0.75), (0.25, 0.75)], True)
        K.ci(0.5, 0.3, 0.1)
        K.pl([(0.42, 0.9), (0.42, 1.0), (0.58, 1.0), (0.58, 0.9)])
    elif 'SUZGEC' in a:                         # yer / balkon süzgeci: kare ızgara + gider
        K = Kalem(lay, _kutu_merkez(bb, 1.0))
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
        for t in (0.25, 0.5, 0.75):
            K.ln((t, 0.05), (t, 0.95)); K.ln((0.05, t), (0.95, t))
        K.ci(0.5, 0.5, 0.18)
    elif 'CATAL' in a:                          # PVC çatal (45° Y)
        K.ln((0.3, 0.0), (0.3, 1.0))
        K.ln((0.3, 0.35), (1.0, 1.0))
        K.ln((0.1, 0.0), (0.5, 0.0)); K.ln((0.1, 1.0), (0.5, 1.0))
    elif 'DIRSEK' in a:                         # PVC dirsek (iki 45°)
        K.pl([(0.5, 1.0), (0.5, 0.45), (0.75, 0.2), (1.0, 0.2)])
        K.ln((0.3, 1.0), (0.7, 1.0))
    elif 'HAVALIK' in a:                        # havalık şapkası
        K.pl([(0.0, 0.45), (0.5, 1.0), (1.0, 0.45)])
        K.ln((0.2, 0.25), (0.8, 0.25)); K.ln((0.5, 0.0), (0.5, 0.25))
    elif 'TEMIZLEME' in a:                      # temizleme kapağı
        K = Kalem(lay, _kutu_merkez(bb, 1.6))
        K.pl([(0, 0.25), (1, 0.25), (1, 0.75), (0, 0.75)], True)
        K.ln((-0.15, 0.75), (1.15, 0.75))
    elif 'ROGAR' in a:                          # rögar: çift kare + kapak
        K = Kalem(lay, _kutu_merkez(bb, 1.0))
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
        K.pl([(0.12, 0.12), (0.88, 0.12), (0.88, 0.88), (0.12, 0.88)], True)
        K.ci(0.5, 0.5, 0.28)
    elif 'ASPIRATOR' in a:                      # aspiratör: kare + fan kanatları
        K = Kalem(lay, _kutu_merkez(bb, 1.0))
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
        K.ci(0.5, 0.5, 0.38)
        for i in range(3):
            t = math.radians(90 + 120 * i)
            K.pl([(0.5, 0.5), (0.5 + 0.34 * math.cos(t), 0.5 + 0.34 * math.sin(t)),
                  (0.5 + 0.3 * math.cos(t + 0.6), 0.5 + 0.3 * math.sin(t + 0.6))], True)
    elif 'CATI-FANI' in a:                      # çatı tipi fan (kesit): kaide + gövde + şapka
        K.pl([(0.1, 0.0), (0.9, 0.0), (0.9, 0.18), (0.1, 0.18)], True)
        K.pl([(0.2, 0.18), (0.8, 0.18), (0.7, 0.62), (0.3, 0.62)], True)
        K.pl([(0.0, 0.62), (1.0, 0.62), (0.5, 1.0)], True)
        K.ci(0.5, 0.38, 0.12)
    elif 'MENFEZ' in a:                         # egzoz menfezi
        K = Kalem(lay, _kutu_merkez(bb, 1.0))
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
        K.ln((0, 0), (1, 1)); K.ln((0, 1), (1, 0))
    elif 'SIHHI-DETAYLAR' in a:                 # yer tutucu (sema ölçü alır, sonra siler)
        K.pl([(0, 0), (1, 0), (1, 1), (0, 1)], True)
    else:
        BILINMEYEN.add(a)
        K.pl([(0, 0.5), (0.5, 1), (1, 0.5), (0.5, 0)], True)
        K.ln((0, 0.5), (1, 0.5))


VARSAYILAN_BB = {'ROTAS-ASPIRATOR': (-10, -10, 10, 10), 'ROTAS-CATI-FANI': (-30, 0, 30, 50),
                 'ROTAS-MENFEZ': (-8, -8, 8, 8)}


def blok_dosyasi(eski, yeni):
    """eski bloğun sınır kutusu + öznitelik yuvaları ile ROTAS blok dosyasını yaz"""
    os.makedirs(BDIR, exist_ok=True)
    fn = os.path.join(BDIR, 'ROTAS__%s.dxf' % yeni)
    if os.path.exists(fn):
        return fn
    import mtyblk
    bb, atr, txt = None, [], []
    if eski:
        prims = _orijinal_load(eski)
        xs, ys = [], []
        for p in prims:
            if p[0] == 'L':
                xs += [p[2][0], p[3][0]]; ys += [p[2][1], p[3][1]]
            elif p[0] == 'P':
                xs += [q[0] for q in p[2]]; ys += [q[1] for q in p[2]]
            elif p[0] == 'C':
                xs += [p[2][0] - p[3], p[2][0] + p[3]]; ys += [p[2][1] - p[3], p[2][1] + p[3]]
            elif p[0] == 'S':
                xs += [p[2][0], p[3][0], p[4][0]]; ys += [p[2][1], p[3][1], p[4][1]]
            elif p[0] == 'A':
                atr.append(p)
            elif p[0] == 'T' and 'MTY' not in str(p[3]).upper():
                txt.append(p)
        if xs:
            bb = (min(xs), min(ys), max(xs), max(ys))
    if bb is None:
        bb = VARSAYILAN_BB.get(yeni, (-10, -10, 10, 10))
    doc = ezdxf.new('R2010', setup=False)
    msp = doc.modelspace()
    ciz_geometri(yeni, msp, bb)
    from ezdxf.enums import TextEntityAlignment as TA
    AL = {'L': TA.LEFT, 'C': TA.CENTER, 'R': TA.RIGHT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER, 'MR': TA.MIDDLE_RIGHT,
          'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT, 'BL': TA.BOTTOM_LEFT, 'BC': TA.BOTTOM_CENTER,
          'BR': TA.BOTTOM_RIGHT}
    for p in atr:                     # ('A', lay, pos, text, h, rot, al, col, tag[, invisible])
        a = msp.add_attdef(p[8], insert=p[2], text='', dxfattribs={'layer': '0', 'height': p[4], 'rotation': p[5]})
        a.set_placement(p[2], align=AL.get(p[6], TA.LEFT))
        if len(p) > 9 and p[9]:
            a.is_invisible = True
    for p in txt:
        t = msp.add_text(p[3], dxfattribs={'layer': '0', 'height': p[4], 'rotation': p[5]})
        t.set_placement(p[2], align=AL.get(p[6], TA.LEFT))
    doc.saveas(fn)
    return fn


_ORIG = {}


def _orijinal_load(eski):
    """eski bloğun ilkelleri (yalnız sınır kutusu / öznitelik yuvası için okunur)"""
    import mtyblk
    if eski not in _ORIG:
        doc = ezdxf.readfile(_ORIG_FIND(eski))
        out = []
        mtyblk._prims(list(doc.modelspace()), out)
        _ORIG[eski] = out
    return _ORIG[eski]


_ORIG_FIND = None
_ORIG_INSERT = None


def kur():
    """mtyblk yamaları: her insert ROTAS saf geometri bloğuna yönlenir"""
    global _ORIG_FIND, _ORIG_INSERT
    import mtyblk
    if _ORIG_FIND is not None:
        return
    _ORIG_FIND, _ORIG_INSERT = mtyblk.find, mtyblk.insert

    def find(name):
        if name.startswith('ROTAS-'):
            return blok_dosyasi(KULLANILAN.get(name), name)
        return _ORIG_FIND(name)

    def insert(name, pos, rot=0.0, scale=1.0, **kw):
        yeni = name if name.startswith('ROTAS-') else yeni_ad(name)
        KULLANILAN.setdefault(yeni, None if name.startswith('ROTAS-') else name)
        blok_dosyasi(KULLANILAN[yeni], yeni)
        mtyblk._cache.pop(yeni, None)
        return _ORIG_INSERT(yeni, pos, rot, scale, **kw)

    mtyblk.find = find
    mtyblk.insert = insert
    # p2 modülleri `import mtyblk` + `mtyblk.insert(...)` kullanır (modül özniteliği) -> yama yeterli


def blok_ekle(doc, ad):
    """ROTAS bloğunu doğrudan bir ezdxf belgesine tanımla (lejant / sonradan eklenen semboller)"""
    if ad in doc.blocks:
        return ad
    src = ezdxf.readfile(blok_dosyasi(KULLANILAN.get(ad), ad))
    from ezdxf.addons import Importer
    blk = doc.blocks.new(ad)
    imp = Importer(src, doc)
    imp.import_entities(list(src.modelspace()), target_layout=blk)
    imp.finalize()
    return ad
