"""Kontrol edilen DXF'in okunması: pafta çerçeveleri, kat paftaları, kolon şeması paftası, katman sınıflandırması,
boru geometrileri, semboller (süzgeç, kolon, sayaç, iniş), etiketler; kaynak mimari ile kat eşleme (öteleme)."""
import math
import re
from collections import Counter, defaultdict

import ezdxf
from ezdxf import path as ep
from shapely.geometry import LineString, Point, Polygon, box
from shapely import STRtree

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'deneme', 'denetim'))
import denetle as D  # noqa: E402  (ortak kural: boru_katmani, yazi_poligonu, geometri)
import kutu as K  # noqa: E402  (gerçek yazı kutusu: ezdxf text_size, hizalama + döndürme, MTEXT)

TR = D.TR


def norm(s):
    return ' '.join((s or '').replace('%%c', 'Ø').replace('%%C', 'Ø').split())


def normu(s):
    return norm(s).translate(TR).upper()


# ------------------------------------------------------------------ katman sınıfları
def pis_mi(lay):
    return D.pis_su_katmani(lay)


def sicak_mi(lay):
    return 'SICAK' in normu(lay) and D.boru_katmani(lay)


def soguk_mi(lay):
    n = normu(lay)
    return ('SOGUK' in n or 'SEBEKE' in n or (('TEMIZ' in n) and 'CAP' not in n)) and D.boru_katmani(lay)


def temiz_mi(lay):
    return sicak_mi(lay) or soguk_mi(lay)


def yagmur_mi(lay):
    return 'YAGMUR' in normu(lay) and D.boru_katmani(lay)


def boru_mi(lay):
    return D.boru_katmani(lay)


def kilavuz_mi(lay):
    return 'KILAVUZ' in normu(lay)


def mimari_yazi_katmani(lay):
    n = normu(lay)
    return 'MIMARI' in n or 'MKDU' in n or n in ('YAZI-MIMARI',)


def etiket_katmani(lay):
    """ölçülen (tesisat) yazıları: çap / cihaz / kolon no / havalandırma yazısı / genel yazı (mimari ve lejant hariç)"""
    n = normu(lay)
    if 'MIMARI' in n or 'MKDU' in n or 'LEJANT' in n or 'PAFTA' in n or 'HESAP' in n or 'KAT-ADI' in n:
        return False
    return any(k in n for k in ('CAP', 'CIHAZ', 'KOLONNO', 'KOLON-NO', 'HAVALANDIRMA-YAZI', 'YAZI', 'ROGAR', 'VANA',
                                'ETIKET', 'TEMIZSU', 'PISSU'))


# ------------------------------------------------------------------ okuma
class Cizim:
    def __init__(self, yol):
        self.yol = yol
        self.doc = ezdxf.readfile(yol)
        self.msp = self.doc.modelspace()
        self.cerceveler = self._cerceveler()
        self.yazilar = self._yazilar()           # [(metin, (x,y), h, katman, varlık)]
        self.kat_paftalari = self._kat_paftalari()
        self.sema_paftasi = self._sema_paftasi()
        self.borular = self._borular()           # [(katman, LineString, varlık)]
        self.insertler = [(e.dxf.name, (e.dxf.insert.x, e.dxf.insert.y), e) for e in self.msp.query('INSERT')]
        # dinamik blok (*Unn) -> asıl blok adı (kullanıcının MTY blokları: KOLON PİS SU, CAMASIR MAKINASI1 ...)
        self.insertler_ef = [(efektif_ad(self.doc, e), p, e) for ad, p, e in self.insertler]
        self.daireler = [(e.dxf.layer, (e.dxf.center.x, e.dxf.center.y), e.dxf.radius)
                         for e in self.msp.query('CIRCLE')]

    # ---- çerçeveler: kapalı dikdörtgen polyline'lar (pafta / çerçeve katmanı tercih, yoksa büyük kapalı dikdörtgenler)
    def _cerceveler(self):
        out = []
        for e in self.msp.query('LWPOLYLINE'):
            n = normu(e.dxf.layer)
            pts = list(e.get_points('xy'))
            if len(pts) not in (4, 5):
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            if w < 300 or h < 300:
                continue
            if 'PAFTA' in n or 'CERCEVE' in n or 'ANTET' in n:
                out.append((min(xs), min(ys), max(xs), max(ys)))
        if not out:  # new_block gibi çerçevesiz dosya: pencereler dışarıdan gelir
            return []
        # iç içe çift çerçeve (dış + iç 25 cm): dış olanı al
        out.sort(key=lambda b: -(b[2] - b[0]) * (b[3] - b[1]))
        tek = []
        for b in out:
            if any(abs(b[0] - t[0]) < 80 and abs(b[1] - t[1]) < 80 and abs(b[2] - t[2]) < 80 and abs(b[3] - t[3]) < 80
                   for t in tek):
                continue
            tek.append(b)
        return tek

    def _yazilar(self):
        out = []
        for e in self.msp:
            t = e.dxftype()
            if t == 'TEXT':
                out.append((e.dxf.text, (e.dxf.insert.x, e.dxf.insert.y), e.dxf.height, e.dxf.layer, e))
            elif t == 'MTEXT':
                out.append((e.plain_text(), (e.dxf.insert.x, e.dxf.insert.y), e.dxf.char_height, e.dxf.layer, e))
            elif t == 'INSERT':
                for a in e.attribs:
                    if not a.is_invisible and (a.dxf.text or '').strip():
                        out.append((a.dxf.text, (a.dxf.insert.x, a.dxf.insert.y), a.dxf.height, e.dxf.layer, a))
        return out

    KAT_RE = re.compile(r'^\s*(ZEMIN|BODRUM|ÇATI|CATI|\d+\s*\.\s*(?:NORMAL\s+)?KAT|\d+\s*\.\s*BODRUM)', re.I)

    def cerceve_bul(self, p):
        adaylar = [c for c in self.cerceveler if c[0] <= p[0] <= c[2] and c[1] <= p[1] <= c[3]]
        return min(adaylar, key=lambda c: (c[2] - c[0]) * (c[3] - c[1])) if adaylar else None

    def _kat_paftalari(self):
        """{kat: çerçeve} — başlığı 'ZEMİN KAT ... PLANI' / '1. KAT ... PLANI' olan paftalar (şema ve temel hariç)."""
        out = {}
        for s, p, h, lay, e in self.yazilar:
            n = normu(s)
            if 'PLAN' not in n or 'SEMA' in n or 'TEMEL' in n or 'YERLESIM' in n or 'VAZIYET' in n or 'CATI' in n:
                continue
            m = self.KAT_RE.match(n)
            if not m:
                continue
            c = self.cerceve_bul(p)
            if c is None:
                continue
            k = m.group(1)
            if k.startswith('ZEMIN'):
                key = 'Z'
            elif 'BODRUM' in k:
                key = 'B' + (re.sub(r'\D', '', k) or '')
            else:
                key = re.sub(r'\D', '', k)
            out[key] = c
        return out

    def _sema_paftasi(self):
        for s, p, h, lay, e in self.yazilar:
            n = normu(s)
            if ('KOLON SEMASI' in n or 'ACILIMLI' in n) and h >= 5:
                c = self.cerceve_bul(p)
                if c:
                    return c
        # yedek: en çok sayaç sembolü olan çerçeve
        say = Counter()
        for e in self.msp.query('INSERT'):
            if 'SAYAC' in normu(e.dxf.name):
                c = self.cerceve_bul((e.dxf.insert.x, e.dxf.insert.y))
                if c:
                    say[c] += 1
        return say.most_common(1)[0][0] if say else None

    def _borular(self):
        out = []
        for e in self.msp:
            lay = e.dxf.get('layer', '0')
            if not boru_mi(lay) or e.dxftype() not in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC'):
                continue
            g = D.geometri(e)
            if g is not None and g.length > 0.5:
                out.append((lay, g, e))
        return out

    # ---- pencere süzgeçleri
    def borular_pencere(self, w, sinif=None):
        b = box(*w)
        return [(lay, g, e) for lay, g, e in self.borular if (sinif is None or sinif(lay)) and g.intersects(b)]

    def insertler_pencere(self, w, ad_icerir=(), ad_icermez=()):
        out = []
        for ad, p, e in self.insertler:
            n = normu(ad)
            if not (w[0] <= p[0] <= w[2] and w[1] <= p[1] <= w[3]):
                continue
            if ad_icerir and not all(k in n for k in ad_icerir):
                continue
            if any(k in n for k in ad_icermez):
                continue
            out.append((ad, p, e))
        return out

    def yazilar_pencere(self, w, secici=None):
        return [y for y in self.yazilar if w[0] <= y[1][0] <= w[2] and w[1] <= y[1][1] <= w[3]
                and (secici is None or secici(y))]

    # ---- semboller
    def suzgecler(self, w):
        """plan süzgeç sembolleri (SUZGEC geçen blok; şema blokları hariç) — 15 cm içindekiler tek sayılır"""
        pts = [p for ad, p, e in self.insertler_pencere(w, ('SUZGEC',), ('SEMA',))]
        return _kumele(pts, 15)

    def pis_kolonlar(self, w):
        """pis su kolon sembolleri (PIS + KOLON, NO/HAVALIK/KAPAK hariç)"""
        return [p for ad, p, e in self.insertler_pencere(w, ('PIS', 'KOLON'), ('NO', 'HAVALIK', 'KAPAK', 'SEMA'))]

    def kolon_balonlari(self, w):
        """kolon numarası balonları: [(no, p)] — INSERT özniteliği veya daire içindeki P\\d+ yazısı"""
        out = []
        for ad, p, e in self.insertler_pencere(w, ('KOLON', 'NO'), ('YAGMUR',)):
            no = ' '.join(a.dxf.text for a in e.attribs if (a.dxf.text or '').strip())
            out.append((no or ad, p))
        for s, p, h, lay, e in self.yazilar_pencere(w):
            if re.match(r'^P\d+$', norm(s)) and e.dxftype() == 'TEXT':
                out.append((norm(s), p))
        return out

    def yagmur_inisleri(self, w):
        """yağmur inişi noktaları: yağmur katmanındaki daireler (r 3-12) + KOLON NO YAGMUR balonları"""
        pts = [p for lay, p, r in self.daireler if yagmur_mi(lay) and 3 <= r <= 12
               and w[0] <= p[0] <= w[2] and w[1] <= p[1] <= w[3]]
        pts += [p for ad, p, e in self.insertler_pencere(w, ('KOLON', 'YAGMUR'))]
        return _kumele(pts, 20)

    def sayaclar(self, w):
        return [p for ad, p, e in self.insertler_pencere(w, ('SAYAC',))]

    # ---- etiketler
    def etiketler(self, w):
        """tesisat etiket yazıları: [(metin, poligon, sahip, katman, h)] — çap blok öznitelikleri + etiket katmanı yazıları"""
        out = []
        for s, p, h, lay, e in self.yazilar_pencere(w):
            if not (s or '').strip():
                continue
            t = e.dxftype()
            sahip = e.dxf.owner if t == 'ATTRIB' else e.dxf.handle
            if t == 'ATTRIB':
                ok = True
            else:
                ok = etiket_katmani(lay)
            if not ok:
                continue
            pg = K.yazi_kutusu(e)
            if pg is not None and pg.is_valid and pg.area > 0:
                out.append((norm(s), pg, sahip, lay, h))
        return out

    def mimari_yazilar(self, w):
        out = []
        for s, p, h, lay, e in self.yazilar_pencere(w):
            if mimari_yazi_katmani(lay) and e.dxftype() in ('TEXT', 'MTEXT') and (s or '').strip():
                # gerçek yazı kutusu (kutu.py): MTEXT için mtext_size, TEXT için yazı tipi ölçüsü
                pg = K.yazi_kutusu(e)
                if pg is not None and pg.is_valid and pg.area > 0:
                    out.append((norm(s), pg, lay, h))
        return out


    # ------------------------------------------------------------------ T12–T16 için ek okuyucular
    def insertler_ef_pencere(self, w, ad_icerir=(), ad_icermez=(), herhangi=()):
        out = []
        for ad, p, e in self.insertler_ef:
            if not (w[0] <= p[0] <= w[2] and w[1] <= p[1] <= w[3]):
                continue
            n = normu(ad)
            if ad_icerir and not all(k in n for k in ad_icerir):
                continue
            if herhangi and not any(k in n for k in herhangi):
                continue
            if any(k in n for k in ad_icermez):
                continue
            out.append((ad, p, e))
        return out

    def kolon_numaralari(self, w):
        """pis su kolonları numarasıyla: [(no, p_kolon)]. Kolon bloğunun kendi özniteliği P<n> ise (kullanıcının
        dinamik 'MTY-BORU KOLON PİS SU' bloğu) o; yoksa kolon sembolü en yakın kolon balonuyla (≤ 130 cm) eşlenir."""
        out, kalan = [], []
        for ad, p, e in self.insertler_ef_pencere(w, ('PIS', 'KOLON'), ('HAVALIK', 'KAPAK', 'SEMA')):
            n = normu(ad)
            at = [norm(a.dxf.text) for a in e.attribs if (a.dxf.text or '').strip()]
            no = next((t for t in reversed(at) if re.match(r'^P\d+$', t)), None)
            if no:
                out.append((no, p))
            elif any(re.match(r'^YB\d+$', t) for t in at):
                continue                                   # aynı blok yağmur inişi için de kullanılıyor
            elif re.search(r'(^|[^A-Z])NO([^A-Z]|$)', n) or n.endswith('-NO'):
                continue                                   # balon bloğu
            else:
                kalan.append(p)
        balon = [(no, q) for no, q in self.kolon_balonlari(w) if re.match(r'^P\d+$', no)]
        ciftler = sorted(((math.hypot(p[0] - q[0], p[1] - q[1]), i, j) for i, p in enumerate(kalan)
                          for j, (no, q) in enumerate(balon)), key=lambda t: t[0])
        ki, kj = set(), set()
        for d, i, j in ciftler:
            if d > 130 or i in ki or j in kj:
                continue
            ki.add(i)
            kj.add(j)
            out.append((balon[j][0], kalan[i]))
        for i, p in enumerate(kalan):
            if i not in ki:
                out.append(('?', p))
        return out

    def blok_kutusu(self, e):
        try:
            from ezdxf import bbox
            b = bbox.extents(e.virtual_entities(), fast=True)
            if b.has_data:
                return box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)
        except Exception:
            pass
        p = e.dxf.insert
        return Point(p.x, p.y).buffer(10)

    MAKINE_RE = re.compile(r"^(Ç|C)['.]?\s*(M|W)['.]?|^(B)['.]?\s*M['.]?|CAMASIR|BULASIK|^ÇM\b|^BM\b", re.I)

    @staticmethod
    def makine_turu(s):
        n = normu(s).replace(' ', '')
        if n.startswith(("C.M", "C'M", 'CM', "C'W", 'CW', 'C.W')) or 'CAMASIR' in n:
            return 'CM'
        if n.startswith(('B.M', "B'M", 'BM')) or 'BULASIK' in n:
            return 'BM'
        return None

    def makineler(self, w):
        """çizimdeki çamaşır / bulaşık makinesi gösterimleri: [(tür, merkez, kutu, kaynak)]
        blok (CAMASIR/BULASIK/MAKINE adlı) + tesisat katmanındaki 'Ç.M.' / 'B.M.' yazıları (yakınında blok yoksa)."""
        out = []
        yazilar = []
        for s, p, h, lay, e in self.yazilar_pencere(w):
            if mimari_yazi_katmani(lay) or e.dxftype() not in ('TEXT', 'MTEXT', 'ATTRIB'):
                continue
            t = self.makine_turu(s)
            if t and len(norm(s)) <= 20:
                pg = K.yazi_kutusu(e)
                c = (pg.centroid.x, pg.centroid.y) if pg is not None else p
                yazilar.append((t, c, pg, s))
        for ad, p, e in self.insertler_ef_pencere(w, herhangi=('CAMASIR', 'BULASIK', 'MAKINE', 'MAKINA')):
            t = self.makine_turu(ad)
            pg = self.blok_kutusu(e)
            c = (pg.centroid.x, pg.centroid.y)
            if t is None:      # genel makine bloğu: türü en yakın 'Ç.M.' / 'B.M.' yazısından
                yak = sorted(yazilar, key=lambda y: math.hypot(y[1][0] - c[0], y[1][1] - c[1]))
                if yak and math.hypot(yak[0][1][0] - c[0], yak[0][1][1] - c[1]) <= 120:
                    t = yak[0][0]
            if t:
                out.append((t, c, pg, 'blok ' + ad))
        for t, c, pg, s in yazilar:
            if any(o[0] == t and math.hypot(o[1][0] - c[0], o[1][1] - c[1]) <= 120 for o in out):
                continue
            out.append((t, c, pg, 'yazı "%s"' % norm(s)))
        return out

    def aspiratorler(self, w):
        """aspiratör sembolleri (blok adı ASPIRATOR / FAN; çatı fanı hariç): [(p, kutu)]"""
        return [(p, self.blok_kutusu(e)) for ad, p, e in self.insertler_ef_pencere(w, herhangi=('ASPIRATOR', 'ASPIRAT'),
                                                                              ad_icermez=('CATI', 'SEMA'))]

    def aspirator_notlari(self, w):
        """aspiratör notları: 'Aspiratör' geçen tesisat yazısı (+ hemen altındaki satırlar: kullanıcı 3 ayrı TEXT yazıyor)
        -> [(metin, kutu, varlık)]"""
        out = []
        tum = [(s, p, h, lay, e) for s, p, h, lay, e in self.yazilar_pencere(w)
               if not mimari_yazi_katmani(lay) and e.dxftype() in ('TEXT', 'MTEXT')]
        for s, p, h, lay, e in tum:
            if 'ASPIRAT' not in normu(s):
                continue
            pg = K.yazi_kutusu(e)
            if pg is None:
                continue
            if e.dxftype() == 'TEXT':
                parca = [pg]
                for s2, p2, h2, l2, e2 in tum:
                    if e2 is e or e2.dxftype() != 'TEXT':
                        continue
                    if abs(p2[0] - p[0]) <= 2 * h and 0 < p[1] - p2[1] <= 4.5 * h:
                        q = K.yazi_kutusu(e2)
                        if q is not None:
                            parca.append(q)
                from shapely.ops import unary_union
                pg = unary_union(parca).envelope
            out.append((norm(s), pg, e))
        return out

    def kilavuzlar(self, w):
        """kılavuz (leader) çizgileri: KILAVUZ katmanı + LEADER/MULTILEADER varlıkları -> [LineString]"""
        b = box(*w)
        out = []
        for e in self.msp:
            t = e.dxftype()
            lay = e.dxf.get('layer', '0')
            if t in ('LEADER',):
                try:
                    pts = [(v[0], v[1]) for v in e.vertices]
                    if len(pts) >= 2:
                        g = LineString(pts)
                        if g.intersects(b):
                            out.append(g)
                except Exception:
                    pass
                continue
            if not kilavuz_mi(lay) or t not in ('LINE', 'LWPOLYLINE', 'POLYLINE'):
                continue
            g = D.geometri(e)
            if g is not None and g.length > 0.5 and g.intersects(b):
                out.append(g)
        return out

    def sembol_kutulari(self, w):
        """tesisat sembolleri (görünür özniteliği olmayan, mimari olmayan bloklar: süzgeç, makine, aspiratör, vana,
        kolon, armatür blokları) -> [(ad, kutu)] — T07 etiket–armatür/sembol çakışması için"""
        out = []
        for ad, p, e in self.insertler_ef_pencere(w):
            if mimari_yazi_katmani(e.dxf.layer) or normu(e.dxf.layer) in ('0',):
                continue
            n = normu(ad)
            if any(k in n for k in ('CAP', 'ETIKET', 'NO', 'KURESEL', 'VANA', 'SEMA')) and 'MAKINA' not in n:
                continue
            if any(not a.is_invisible and (a.dxf.text or '').strip() for a in e.attribs) and not any(
                    k in n for k in ('MAKINA', 'KLOZET', 'LAVABO', 'EVIYE', 'DUS', 'HELA', 'TERMOSIFON', 'KOLON')):
                continue
            out.append((ad, self.blok_kutusu(e), e.dxf.handle))
        return out

    def paftalar(self):
        """pafta pencereleri: çerçeveler; çerçeve yoksa ANTED/PAFTA/CERCEVE katmanındaki düşey ayraç çizgileri
        (≥ 2000 cm; new_block düzeni) -> [(x0, y0, x1, y1)] soldan sağa"""
        if self.cerceveler:
            ps = [c for c in self.cerceveler if (c[3] - c[1]) >= 1000]
            tek = []
            for c in sorted(ps, key=lambda c: -(c[2] - c[0]) * (c[3] - c[1])):
                if any(t[0] - 5 <= c[0] and c[2] <= t[2] + 5 and t[1] - 5 <= c[1] and c[3] <= t[3] + 5 for t in tek):
                    continue
                tek.append(c)
            return sorted(tek)
        dik, yat = [], []
        for e in self.msp.query('LINE'):
            n = normu(e.dxf.layer)
            if not ('ANTED' in n or 'ANTET' in n or 'PAFTA' in n or 'CERCEVE' in n):
                continue
            s, t = e.dxf.start, e.dxf.end
            if abs(s.x - t.x) < 1 and abs(s.y - t.y) >= 2000:
                dik.append((round(s.x), min(s.y, t.y), max(s.y, t.y)))
            elif abs(s.y - t.y) < 1 and abs(s.x - t.x) >= 300:
                yat.append((min(s.x, t.x), max(s.x, t.x)))
        dik.sort()
        out = []
        for a, b in zip(dik[:-1], dik[1:]):
            if not (300 <= b[0] - a[0] <= 12000 and abs(a[1] - b[1]) < 50):
                continue
            # iki şerit arasındaki boşluk pafta değildir: üst/alt çerçeve çizgisi bu aralığı örtmeli
            if yat and not any(x0 <= a[0] + 1 and x1 >= b[0] - 1 for x0, x1 in yat):
                continue
            out.append((float(a[0]), a[1], float(b[0]), a[2]))
        return out


_EF = {}


def efektif_ad(doc, e):
    """INSERT'in asıl blok adı: dinamik blok (*Unn) ise AcDbBlockRepBTag xdata'sındaki asıl blok kaydının adı"""
    ad = e.dxf.name
    if not ad.startswith('*'):
        return ad
    k = (id(doc), ad)
    if k in _EF:
        return _EF[k]
    sonuc = ad
    try:
        br = doc.blocks.get(ad).block_record
        if br.has_xdata('AcDbBlockRepBTag'):
            h = [t.value for t in br.get_xdata('AcDbBlockRepBTag') if t.code == 1005]
            if h and h[0] in doc.entitydb:
                sonuc = doc.entitydb[h[0]].dxf.name
    except Exception:
        pass
    _EF[k] = sonuc
    return sonuc


def _kumele(pts, tol):
    out = []
    for p in pts:
        for i, q in enumerate(out):
            if math.hypot(p[0] - q[0], p[1] - q[1]) <= tol:
                break
        else:
            out.append(p)
    return out


# ------------------------------------------------------------------ kat eşleme (kaynak -> çizim ötelemesi)
def oteleme_bul(cizim, pencere, kaynak_R, kaynak_w):
    """Kaynak kat penceresindeki yazılar ile çizimdeki kat paftası yazılarını metin eşitliğiyle eşleştirip ötelemeyi
    (dx, dy) kip (mode) ile bulur. Dönüş: (dx, dy, eşleşme sayısı) veya None."""
    kay = defaultdict(list)
    for a in kaynak_R:
        if a[0] == 'T':
            kay[norm(a[2][0])].append((a[1][0], a[2][1]))
    cift = []
    for s, p, h, lay, e in cizim.yazilar_pencere(pencere):
        if e.dxftype() != 'TEXT' and e.dxftype() != 'MTEXT':
            continue
        n = norm(s)
        if len(n) < 2 or n not in kay:
            continue
        for q, hk in kay[n]:
            if abs(hk - h) <= max(0.6, 0.1 * h):
                cift.append((p[0] - q[0], p[1] - q[1]))
    if len(cift) < 6:
        return None
    say = Counter((round(dx / 2) * 2, round(dy / 2) * 2) for dx, dy in cift)
    (mx, my), n = say.most_common(1)[0]
    ic = [(dx, dy) for dx, dy in cift if abs(dx - mx) <= 3 and abs(dy - my) <= 3]
    if len(ic) < 6:
        return None
    return (sum(d[0] for d in ic) / len(ic), sum(d[1] for d in ic) / len(ic), len(ic))


def oteleme_bul_cizgi(cizim, pencere, kaynak_R, kaynak_w, kaba=None):
    """Yedek: yazı eşleşmesi yoksa uzun yatay/dikey duvar çizgilerinin uç noktalarıyla kaba öteleme (histogram)."""
    src = [a for a in kaynak_R if a[0] == 'L' and math.hypot(a[1][1][0] - a[1][0][0], a[1][1][1] - a[1][0][1]) >= 150]
    dst = []
    b = box(*pencere)
    for e in cizim.msp.query('LINE'):
        s, t = e.dxf.start, e.dxf.end
        if math.hypot(t.x - s.x, t.y - s.y) >= 150 and b.contains(Point(s.x, s.y)):
            dst.append(((s.x, s.y), (t.x, t.y)))
    if not src or not dst:
        return None
    say = Counter()
    for a in src[:4000]:
        la = math.hypot(a[1][1][0] - a[1][0][0], a[1][1][1] - a[1][0][1])
        for s, t in dst[:4000]:
            if abs(math.hypot(t[0] - s[0], t[1] - s[1]) - la) > 1.0:
                continue
            for q in (s, t):
                for p in a[1]:
                    say[(round((q[0] - p[0]) / 5) * 5, round((q[1] - p[1]) / 5) * 5)] += 1
    if not say:
        return None
    (mx, my), n = say.most_common(1)[0]
    return (mx, my, n) if n >= 20 else None
