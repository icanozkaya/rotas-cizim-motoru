# -*- coding: utf-8 -*-
"""ROTAŞ birleşik mekanik tesisat sembol kütüphanesi (deneme modülü: semboller).

Öncelik sırası (DENEME_KURALLARI §5):
  1. Kullanıcının MTY blok kütüphanesi (/tmp/claude-0/blk/*.dxf, yoksa kutuphane/ROTAS_2_MTY_BLOKLARI_*.tar.xz açılır)
     ve kullanıcının VOYAP dosyasındaki MTY sprinkler blokları -> blok OLDUĞU GİBİ alınır (patlatılmaz, iç katmanlarıyla).
  2. Kullanıcının örnek projesi Aselsan 02-Yangın lejantından çıkarılmış semboller (motor/voyap/asel_sym.pkl, salt okunur).
  3. kutuphane/arastirma/03_SEMBOLLER.md geometrisi ile çizilen gerçek semboller (kutu/daire temsili yok).

Birim cm (plan 1/50). Vana boyu L = 20 cm (MTY vana bloklarıyla aynı), cihaz ölçüsü B = 50 cm.
Bloğun orijini sembol merkezi, boru +X yönünde; döndürme INSERT açısıyla.

Kullanım:
    import sembol as S
    S.ciz(msp, 'kuresel_vana', x, y, aci=0, olcek=1, no='V-01', katman='ROTAS-SIHHI-SEMBOL')
    S.blok_tanimla(doc, 'pompa')            # yalnız BLOCK tanımı, blok adını döndürür
    S.otomatik_lejant(doc)                  # kullanılan blokları sayar, lejant + adet tablosu çizer
"""
import math
import os
import glob
import pickle
import subprocess
import tarfile

import ezdxf
from ezdxf import bbox as _bbox
from ezdxf.addons import Importer
from ezdxf.enums import TextEntityAlignment as TA

DEPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MTY_DIR = '/tmp/claude-0/blk'
MTY_TAR = os.path.join(DEPO, 'kutuphane', 'ROTAS_2_MTY_BLOKLARI_2026-10-11.tar.xz')
VOYAP_SIH = '/tmp/claude-0/vy/sih.dxf'          # kullanıcının VOYAP sıhhi/yangın dosyası (MTY sprinkler blokları)
ASL_PKL = os.path.join(DEPO, 'motor', 'voyap', 'asel_sym.pkl')

L = 20.0          # vana boyu (cm)
H = 0.6 * L       # vana yüksekliği
B = 50.0          # cihaz ölçüsü (cm)
STIL = 'ROTAS'

GRUPLAR = [
    ('SIHHI', 'SIHHİ TESİSAT SEMBOLLERİ', 'ROTAS-SIHHI-SEMBOL', 5),
    ('ISITMA', 'ISITMA TESİSATI SEMBOLLERİ', 'ROTAS-ISITMA-SEMBOL', 1),
    ('YANGIN', 'YANGIN TESİSATI SEMBOLLERİ', 'ROTAS-YANGIN-SEMBOL', 10),
    ('HAVALANDIRMA', 'HAVALANDIRMA TESİSATI SEMBOLLERİ', 'ROTAS-HAVALANDIRMA-SEMBOL', 4),
    ('DOGALGAZ', 'DOĞALGAZ TESİSATI SEMBOLLERİ', 'ROTAS-DOGALGAZ-SEMBOL', 2),
]
GRUP_KATMAN = {g: k for g, _, k, _ in GRUPLAR}
LEJ_CER, LEJ_YAZ, LEJ_BAS, MASKE = 'ROTAS-LEJANT-CERCEVE', 'ROTAS-LEJANT-YAZI', 'ROTAS-LEJANT-BASLIK', 'ROTAS-MASKE'
YARDIMCI_KATMAN = {LEJ_CER: 7, LEJ_YAZ: 7, LEJ_BAS: 5, MASKE: 7, 'ROTAS-LEJANT-SEMBOL': 7}

# lejantta gösterilen boru çizgi tipleri (blok değil): (grup, açıklama, katman, renk, çizgi tipi)
BORU_SATIR = [
    ('SIHHI', 'SOĞUK SU BORUSU', 'ROTAS-SIHHI-SOGUK-SU', 5, 'Continuous'),
    ('SIHHI', 'SICAK SU BORUSU', 'ROTAS-SIHHI-SICAK-SU', 1, 'DASHED'),
    ('SIHHI', 'SİRKÜLASYON BORUSU', 'ROTAS-SIHHI-SIRKULASYON', 31, 'DASHDOT'),
    ('SIHHI', 'PİS SU BORUSU', 'ROTAS-SIHHI-PIS-SU', 6, 'Continuous'),
    ('SIHHI', 'YAĞMUR SUYU BORUSU', 'ROTAS-SIHHI-YAGMUR', 3, 'Continuous'),
    ('ISITMA', 'ISITMA GİDİŞ BORUSU', 'ROTAS-ISITMA-GIDIS', 10, 'Continuous'),
    ('ISITMA', 'ISITMA DÖNÜŞ BORUSU', 'ROTAS-ISITMA-DONUS', 30, 'DASHED'),
    ('YANGIN', 'SPRİNKLER BORUSU', 'ROTAS-YANGIN-SPRINKLER-BORU', 140, 'Continuous'),
    ('YANGIN', 'YANGIN DOLABI / HİDRANT BORUSU', 'ROTAS-YANGIN-DOLAP-BORU', 1, 'Continuous'),
    ('YANGIN', 'DRENAJ BORUSU', 'ROTAS-YANGIN-DRENAJ', 8, 'DASHED'),
    ('HAVALANDIRMA', 'ÜFLEME (TAZE HAVA) KANALI', 'ROTAS-HAVALANDIRMA-UFLEME', 20, 'Continuous'),
    ('HAVALANDIRMA', 'EGZOZ / EMİŞ KANALI', 'ROTAS-HAVALANDIRMA-EGZOZ', 4, 'DASHED'),
    ('DOGALGAZ', 'DOĞALGAZ BORUSU', 'ROTAS-DOGALGAZ-BORU', 2, 'Continuous'),
]


# =====================================================================================  çizim yardımcıları (blok içi)
def _a(lay='0'):
    return {'layer': lay}


def _ln(b, p, q):
    b.add_line(p, q, dxfattribs=_a())


def _pl(b, pts, kapali=False):
    b.add_lwpolyline(pts, close=kapali, dxfattribs=_a())


def _ci(b, c, r):
    b.add_circle(c, r, dxfattribs=_a())


def _arc(b, c, r, a0, a1):
    b.add_arc(c, r, a0, a1, dxfattribs=_a())


def _dolu(b, pts):
    h = b.add_hatch(dxfattribs=_a())
    h.paths.add_polyline_path(pts, is_closed=True)


def _dolu_daire(b, c, r, n=24):
    _dolu(b, [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)])
    _ci(b, c, r)


def _tara(b, pts, desen='ANSI31', olcek=0.3):
    h = b.add_hatch(dxfattribs=_a())
    h.set_pattern_fill(desen, scale=olcek)
    h.paths.add_polyline_path(pts, is_closed=True)


def _yz(b, s, p, h, al=TA.MIDDLE_CENTER):
    t = b.add_text(s, height=h, dxfattribs={'layer': '0', 'style': STIL})
    t.set_placement(p, align=al)


def _ok(b, p, aci, boy, dolu=False):
    """p = ok ucu, aci yönünde gösterir"""
    a = math.radians(aci)
    ux, uy = math.cos(a), math.sin(a)
    k = boy * 0.35
    q1 = (p[0] - boy * ux - k * uy, p[1] - boy * uy + k * ux)
    q2 = (p[0] - boy * ux + k * uy, p[1] - boy * uy - k * ux)
    if dolu:
        _dolu(b, [p, q1, q2])
    _pl(b, [q1, p, q2])


def _okcizgi(b, p0, p1, bas=None, dolu=False):
    _ln(b, p0, p1)
    aci = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    _ok(b, p1, aci, bas or 0.25 * math.dist(p0, p1), dolu)


def _rect(b, cx, cy, w, h):
    _pl(b, [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)], True)


def _kapsul(b, cx, cy, w, h):
    """dikey kapsül: gövde w x h, üst/alt yarım daire kapaklar (r = w/2)"""
    r = w / 2
    _ln(b, (cx - r, cy - h / 2), (cx - r, cy + h / 2))
    _ln(b, (cx + r, cy - h / 2), (cx + r, cy + h / 2))
    _arc(b, (cx, cy + h / 2), r, 0, 180)
    _arc(b, (cx, cy - h / 2), r, 180, 360)


def _papyon(b, l=L, dolu=False, dx=0.0):
    h = 0.6 * l
    s = [(dx - l / 2, h / 2), (dx - l / 2, -h / 2), (dx, 0)]
    d = [(dx + l / 2, h / 2), (dx + l / 2, -h / 2), (dx, 0)]
    _pl(b, s, True)
    _pl(b, d, True)
    if dolu:
        _dolu(b, s)
        _dolu(b, d)


def _attdef(b, tag, p, h, al=TA.BOTTOM_CENTER, prompt=''):
    a = b.add_attdef(tag, p, '', dxfattribs={'layer': '0', 'height': h, 'style': STIL})
    a.set_placement(p, align=al)
    a.dxf.prompt = prompt or tag
    return a


def _no(b, y):
    """README: her vana/cihaz V-01, P-01 ... ile numaralandırılır (ATTRIB 'NO')"""
    _attdef(b, 'NO', (0, y), 0.3 * L, prompt='Numara (V-01 / P-01)')


# =====================================================================================  03_SEMBOLLER geometrileri
# ---- §2 vanalar
def g_surgulu(b):
    _papyon(b); _ln(b, (0, -H / 2), (0, H / 2)); _no(b, H / 2 + 3)


def g_ventil(b):            # glob / ventil: papyon + içi dolu nokta (§8-1 önerisi)
    _papyon(b); _dolu_daire(b, (0, 0), 0.1 * L); _no(b, H / 2 + 3)


def g_kuresel_bos(b):       # küresel vana (03 tarifi): papyon + boş daire + kol — MTY bloğu yoksa yedek
    _papyon(b); _ci(b, (0, 0), 0.15 * L); _ln(b, (0, 0.15 * L), (0, 0.4 * L)); _no(b, 0.4 * L + 3)


def g_bdv(b):               # basınç düşürücü
    _papyon(b)
    _ln(b, (0, 0), (0, 0.45 * L))
    _arc(b, (0, 0.45 * L), 0.25 * L, 0, 180)
    _ln(b, (-0.25 * L, 0.45 * L), (0.25 * L, 0.45 * L))
    e = b.add_lwpolyline([(0.25 * L, 0.45 * L), (0.8 * L, 0.45 * L), (0.8 * L, 0.0)], dxfattribs={'layer': '0', 'linetype': 'DASHED'})
    e.dxf.ltscale = 2.0
    _no(b, 0.75 * L + 3)


def g_selenoid(b, dolu=False):
    _papyon(b, dolu=dolu)
    _ln(b, (0, 0), (0, 0.4 * L))
    _rect(b, 0, 0.55 * L, 0.3 * L, 0.3 * L)
    _yz(b, 'S', (0, 0.55 * L), 0.2 * L)
    _no(b, 0.75 * L + 3)


def g_motorlu(b, etiket='M', ek=None):
    _papyon(b)
    _ln(b, (0, 0), (0, 0.35 * L))
    _ci(b, (0, 0.5 * L), 0.15 * L)
    _yz(b, etiket, (0, 0.5 * L), 0.16 * L)
    if ek:
        _yz(b, ek, (0.22 * L, 0.62 * L), 0.14 * L, TA.BOTTOM_LEFT)
    _no(b, 0.7 * L + 3)


def g_picv(b):
    g_motorlu(b, 'M', 'PICV')


def g_uc_yollu_motorlu(b):
    h = H
    _pl(b, [(-L / 2, h / 2), (-L / 2, -h / 2), (0, 0)], True)
    _pl(b, [(L / 2, h / 2), (L / 2, -h / 2), (0, 0)], True)
    _pl(b, [(-h / 2, -L / 2), (h / 2, -L / 2), (0, 0)], True)
    _ln(b, (0, 0), (0, 0.35 * L))
    _ci(b, (0, 0.5 * L), 0.15 * L)
    _yz(b, 'M', (0, 0.5 * L), 0.16 * L)
    _okcizgi(b, (L / 2 + 1, 0), (L / 2 + 0.35 * L, 0), 0.12 * L)     # ortak (AB) çıkış oku
    _no(b, 0.7 * L + 3)


def g_termostatik(b):       # termostatik radyatör vanası
    l0 = 0.6 * L
    _papyon(b, l0)
    _ln(b, (0, 0), (0, 0.3 * L))
    _rect(b, 0, 0.475 * L, 0.25 * L, 0.35 * L)
    _yz(b, 'T', (0, 0.475 * L), 0.16 * L)


def g_rakorlu_donus(b):     # radyatör dönüş (rakorlu) vanası: küçük dolu papyon
    _papyon(b, 0.5 * L, dolu=True)


def g_kesme_rad(b):         # radyatör - fancoil kesme vanası (aselsan): daire + mil + kol
    _ci(b, (0, 0), 0.2 * L)
    _ln(b, (0, 0.2 * L), (0, 0.45 * L))
    _ln(b, (-0.12 * L, 0.45 * L), (0.12 * L, 0.45 * L))


def g_havalik_tupu(b):
    _kapsul(b, 0, 0.3 * L, 0.2 * L, 0.35 * L - 0.2 * L)
    _ln(b, (0, 0), (0, 0.3 * L - 0.075 * L - 0.1 * L))


# ---- §3 cihazlar
def _pompa_govde(b, R):
    _ci(b, (0, 0), R)
    _pl(b, [(R, 0), (-R / 2, R * math.sqrt(3) / 2), (-R / 2, -R * math.sqrt(3) / 2)], True)


def g_pompa(b):
    R = 0.6 * L
    _pompa_govde(b, R); _no(b, R + 3)


def g_pompa_fk(b):
    R = 0.6 * L
    _pompa_govde(b, R)
    s = 0.5 * R
    _rect(b, R * 0.95 + s / 2, R * 0.95 + s / 2, s, s)
    _yz(b, 'FK', (R * 0.95 + s / 2, R * 0.95 + s / 2), 0.32 * s)
    _no(b, R + s + 4)


def g_ikiz_pompa(b):
    R = 0.5 * L
    for y in (-1.3 * R, 1.3 * R):
        b2 = (0, y)
        _ci(b, b2, R)
        _pl(b, [(R, y), (-R / 2, y + R * math.sqrt(3) / 2), (-R / 2, y - R * math.sqrt(3) / 2)], True)
    _ln(b, (-2 * R, -1.3 * R), (-2 * R, 1.3 * R)); _ln(b, (2 * R, -1.3 * R), (2 * R, 1.3 * R))
    for y in (-1.3 * R, 1.3 * R):
        _ln(b, (-2 * R, y), (-R, y)); _ln(b, (R, y), (2 * R, y))
    _no(b, 2.3 * R + 3)


def g_dalgic(b):
    R = 0.5 * L
    w, h = 4 * R, 5 * R
    _pl(b, [(-w / 2, h), (-w / 2, 0), (w / 2, 0), (w / 2, h)])          # çukur (üstü açık)
    _ci(b, (0, 0.2 * R + R), R)
    _pl(b, [(R, 1.2 * R), (-R / 2, 1.2 * R + R * 0.866), (-R / 2, 1.2 * R - R * 0.866)], True)
    _ln(b, (0, 2.2 * R), (0, h + R))                                     # basma borusu
    sv = 3.8 * R
    _ln(b, (-w / 2, sv), (-0.5 * R, sv)); _ln(b, (0.5 * R, sv), (w / 2, sv))
    t = 0.3 * R
    _pl(b, [(w / 2 - 1.2 * R - t / 2, sv + t * 0.9), (w / 2 - 1.2 * R + t / 2, sv + t * 0.9), (w / 2 - 1.2 * R, sv)], True)
    _yz(b, 'DP', (-w / 2 + 0.7 * R, 0.6 * R), 0.5 * R)
    _no(b, h + R + 3)


def g_kazan(b):
    w, h = B, 1.4 * B
    _rect(b, 0, 0, w, h)
    _pl(b, [(-0.2 * B, -0.25 * B), (0.2 * B, -0.25 * B), (0, 0.25 * B)], True)       # alev
    _ln(b, (0.25 * B, h / 2), (0.25 * B, h / 2 + 0.15 * B))                           # gidiş
    _ln(b, (-0.25 * B, -h / 2), (-0.25 * B, -h / 2 - 0.15 * B))                       # dönüş
    _ln(b, (-0.2 * B, h / 2), (-0.2 * B, h / 2 + 0.35 * B)); _ln(b, (0.0, h / 2), (0.0, h / 2 + 0.35 * B))   # baca
    _yz(b, 'G', (0.25 * B + 4, h / 2 + 0.1 * B), 5, TA.MIDDLE_LEFT)
    _yz(b, 'D', (-0.25 * B + 4, -h / 2 - 0.1 * B), 5, TA.MIDDLE_LEFT)
    _no(b, h / 2 + 0.35 * B + 3)


def g_genlesme_kapali(b):
    r = 0.4 * B
    _ci(b, (0, 0), r)
    _ln(b, (-r, 0), (r, 0))
    _tara(b, [(r * math.cos(math.pi * i / 16), r * math.sin(math.pi * i / 16)) for i in range(17)], olcek=1.2)
    _ln(b, (0, -r), (0, -r - 0.3 * B))
    _no(b, r + 3)


def g_genlesme_acik(b):
    w, h = 1.2 * B, 0.8 * B
    _pl(b, [(-w / 2, h / 2), (-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2)])
    sv = -h / 2 + 0.6 * h
    _ln(b, (-w / 2, sv), (w / 2, sv))
    t = 0.12 * B
    _pl(b, [(-t / 2, sv + t * 0.9), (t / 2, sv + t * 0.9), (0, sv)], True)
    _ln(b, (-0.3 * w, -h / 2), (-0.3 * w, -h / 2 - 0.2 * B))                           # emniyet dönüş
    _ln(b, (0.3 * w, -h / 2), (0.3 * w, -h / 2 - 0.2 * B))                             # sirkülasyon
    _pl(b, [(w / 2, sv + 0.05 * B), (w / 2 + 0.2 * B, sv + 0.05 * B), (w / 2 + 0.2 * B, -h / 2 - 0.2 * B)])   # taşma
    _pl(b, [(-0.15 * w, h / 2 + 0.2 * B), (-0.15 * w, h / 2 - 0.1 * B), (-0.05 * w, h / 2 - 0.1 * B)])        # emniyet gidiş
    _no(b, h / 2 + 0.25 * B)


def g_membranli(b):
    w, h = 0.6 * B, 0.6 * B          # gövde (kapaklar hariç)
    _kapsul(b, 0, 0, w, h)
    sag = 0.15 * B
    c = w * w / (8 * sag) + sag / 2           # yay yarıçapı
    ya = 0 + c - sag
    a = math.degrees(math.asin((w / 2) / c))
    _arc(b, (0, ya), c, 270 - a, 270 + a)
    _ln(b, (0, -h / 2 - w / 2), (0, -h / 2 - w / 2 - 0.25 * B))
    _no(b, h / 2 + w / 2 + 3)


def g_kalorimetre(b):
    w, h = 0.6 * L * 1.6, 0.4 * L * 1.6
    _rect(b, 0, 0, w, h)
    _yz(b, 'KM', (0, 0), 0.35 * h)
    for x in (-1.1 * L, 1.1 * L):
        _dolu_daire(b, (x, 0), 0.06 * L)
    e = b.add_lwpolyline([(-1.1 * L, 0.06 * L), (-1.1 * L, h / 2 + 3), (-w / 2, h / 2 + 3), (-w / 2, h / 2)], dxfattribs={'layer': '0', 'linetype': 'DASHED'})
    e.dxf.ltscale = 1.2
    e = b.add_lwpolyline([(1.1 * L, 0.06 * L), (1.1 * L, h / 2 + 3), (w / 2, h / 2 + 3), (w / 2, h / 2)], dxfattribs={'layer': '0', 'linetype': 'DASHED'})
    e.dxf.ltscale = 1.2
    _no(b, h / 2 + 6)


def g_fancoil_gizli(b):
    w, h = 2.2 * B, 0.9 * B
    _rect(b, 0, 0, w, h)
    f = 0.15 * B
    _rect(b, -w / 2 - f / 2, 0, f, h * 0.85)
    _tara(b, [(-w / 2 - f, -h * 0.425), (-w / 2, -h * 0.425), (-w / 2, h * 0.425), (-w / 2 - f, h * 0.425)], olcek=0.8)
    _pl(b, [(w / 2, h * 0.4), (w / 2 + 0.12 * B, h * 0.45), (w / 2 + 0.12 * B, -h * 0.45), (w / 2, -h * 0.4)])   # üfleme flanşı
    for i, s in enumerate(('G', 'D', 'Dr')):
        x = w / 2 - 0.25 * B - i * 0.25 * B
        _ln(b, (x, h / 2), (x, h / 2 + 0.2 * B))
        _yz(b, s, (x, h / 2 + 0.28 * B), 0.1 * B)
    _ln(b, (-w / 2 + 0.1 * B, 0), (w / 2 - 0.6 * B, 0))
    _no(b, h / 2 + 0.4 * B)


def g_fancoil_kaset(b):
    s = 1.2 * B
    _rect(b, 0, 0, s, s)
    _rect(b, 0, 0, 0.6 * s, 0.6 * s)
    for i in range(1, 6):
        y = -0.3 * s + i * 0.1 * s
        _ln(b, (-0.3 * s, y), (0.3 * s, y))
    for k in range(4):
        a = math.radians(90 * k)
        p0 = (0.6 * s * math.cos(a), 0.6 * s * math.sin(a))
        p1 = (0.85 * s * math.cos(a), 0.85 * s * math.sin(a))
        _okcizgi(b, p0, p1, 0.1 * s)
    _no(b, 0.9 * s)


# ---- §4 pis su (MTY'de karşılığı olmayanlar)
def g_tk_plan(b):           # temizleme kapağı plan: daire + "+"
    r = 0.1 * B
    _ci(b, (0, 0), r)
    _ln(b, (-r * 0.7, 0), (r * 0.7, 0)); _ln(b, (0, -r * 0.7), (0, r * 0.7))
    _yz(b, 'TK', (r + 2, 0), 0.8 * r, TA.MIDDLE_LEFT)


# ---- §5 yangın
def g_spr_dik(b):           # ada_hayat / VOYAP (Aselsan) biçimi: tek daire Ø25
    _ci(b, (0, 0), 12.5)


def g_spr_sarkik(b):        # iç içe çift daire Ø25 / Ø10
    _ci(b, (0, 0), 12.5); _ci(b, (0, 0), 5.0)


def g_spr_gizli(b):         # gizli (concealed) sarkık: dış daire + içi dolu iç daire
    _ci(b, (0, 0), 12.5); _dolu_daire(b, (0, 0), 5.0)


def g_spr_yan(b):           # yan duvar: düz kenar duvarda, odaya püskürtme oku
    _arc(b, (0, 0), 12.5, 0, 180)
    _ln(b, (-12.5, 0), (12.5, 0))
    _okcizgi(b, (0, 0), (0, 9), 3.5)
    _yz(b, 'SW', (15, 4), 5, TA.MIDDLE_LEFT)


def g_hidrant(b):
    r = 0.25 * B
    _ci(b, (0, 0), r)
    _yz(b, 'H', (0, 0), 0.9 * r)
    for a in (0, 90, 180):
        ra = math.radians(a)
        _ln(b, (r * math.cos(ra), r * math.sin(ra)), ((r + 0.1 * B) * math.cos(ra), (r + 0.1 * B) * math.sin(ra)))
    _ln(b, (0, -r), (0, -r - 0.15 * B))
    _no(b, r + 0.1 * B + 3)


def g_purjor_spr(b):        # otomatik purjör (sprinkler hattı)
    _ln(b, (0, 0), (0, 0.4 * L))
    p = 0.3 * L
    _pl(b, [(-0.12 * L, p - 0.07 * L), (-0.12 * L, p + 0.07 * L), (0.12 * L, p - 0.07 * L), (0.12 * L, p + 0.07 * L)], True)
    _ci(b, (0, 0.5 * L), 0.1 * L)
    _okcizgi(b, (0.07 * L, 0.57 * L), (0.3 * L, 0.8 * L), 0.08 * L)


def g_itfaiye_vana(b):      # basınç sınırlayıcı itfaiye bağlantı vanası: köşe vana + mil + çark + kaplin
    h = H
    _pl(b, [(-L / 2, h / 2), (-L / 2, -h / 2), (0, 0)], True)
    _pl(b, [(-h / 2, L / 2), (h / 2, L / 2), (0, 0)], True)
    _ln(b, (0, 0), (0.45 * L, 0))
    _ln(b, (0.45 * L, -0.25 * L), (0.45 * L, 0.25 * L))
    _ln(b, (0.3 * L, -0.25 * L), (0.6 * L, -0.25 * L))
    _ln(b, (0.55 * L, 0.15 * L), (0.75 * L, 0.15 * L)); _ln(b, (0.55 * L, -0.15 * L), (0.75 * L, -0.15 * L))
    _ln(b, (0.75 * L, -0.15 * L), (0.75 * L, 0.15 * L)); _ln(b, (0.55 * L, -0.15 * L), (0.55 * L, 0.15 * L))
    _ln(b, (0, L / 2), (0, 0.7 * L)); _ln(b, (-0.2 * L, 0.7 * L), (0.2 * L, 0.7 * L))
    _no(b, 0.75 * L + 2)


def g_yangin_pompa_seti(b):
    R = 0.6 * L
    xs = (-3.2 * R, 0.0, 3.2 * R)
    for x, et, k in zip(xs, ('EP', 'DP', 'JP'), (1.0, 1.0, 0.6)):
        r = R * k
        _ci(b, (x, 0), r)
        _pl(b, [(x + r, 0), (x - r / 2, r * 0.866), (x - r / 2, -r * 0.866)], True)
        _yz(b, et, (x, -R - 6), 5)
    _rect(b, -0.8 * R - 0.4 * R, 0, 0.8 * R, 0.6 * R)                # dizel motor
    _yz(b, 'D', (-1.2 * R, 0), 0.3 * R)
    e = b.add_lwpolyline([(-4.8 * R, -2.2 * R), (4.8 * R, -2.2 * R), (4.8 * R, 2.2 * R), (-4.8 * R, 2.2 * R)], close=True,
                         dxfattribs={'layer': '0', 'linetype': 'DASHDOT'})
    e.dxf.ltscale = 4.0
    _yz(b, 'YANGIN POMPA GRUBU', (0, 1.6 * R), 0.35 * R)
    _no(b, 2.2 * R + 3)


# ---- §6 havalandırma (gerçek ölçülü, cm)
def g_kanal_ufleme(b):      # besleme kanal kesiti: dikdörtgen + X
    w, h = 60, 30
    _rect(b, 0, 0, w, h); _ln(b, (-w / 2, -h / 2), (w / 2, h / 2)); _ln(b, (-w / 2, h / 2), (w / 2, -h / 2))


def g_kanal_emis(b):        # emiş / dönüş kesiti: tek köşegen (sol alt -> sağ üst)
    w, h = 60, 30
    _rect(b, 0, 0, w, h); _ln(b, (-w / 2, -h / 2), (w / 2, h / 2))


def g_kanal_egzoz(b):       # egzoz kesiti: tek köşegen (sol üst -> sağ alt)
    w, h = 60, 30
    _rect(b, 0, 0, w, h); _ln(b, (-w / 2, h / 2), (w / 2, -h / 2))


def g_kanal_yuvarlak(b):
    r = 15
    _ci(b, (0, 0), r)
    c = r * math.cos(math.pi / 4)
    _ln(b, (-c, -c), (c, c)); _ln(b, (-c, c), (c, -c))


def g_flex(b):
    w, h = 80, 20
    _ln(b, (-w / 2, h / 2), (w / 2, h / 2)); _ln(b, (-w / 2, -h / 2), (w / 2, -h / 2))
    x = -w / 2
    while x <= w / 2 + 0.01:
        _ln(b, (x, -h / 2), (x, h / 2)); x += 5


def g_difuzor4(b):
    s = 60
    _rect(b, 0, 0, s, s); _ln(b, (-s / 2, -s / 2), (s / 2, s / 2)); _ln(b, (-s / 2, s / 2), (s / 2, -s / 2))
    for k in range(4):
        a = math.radians(90 * k)
        _okcizgi(b, (s / 2 * math.cos(a), s / 2 * math.sin(a)), ((s / 2 + 0.3 * s) * math.cos(a), (s / 2 + 0.3 * s) * math.sin(a)), 6)


def g_emis_menfez(b):
    s = 60
    _rect(b, 0, 0, s, s); _ln(b, (-s / 2, -s / 2), (s / 2, s / 2))


def g_perfore(b):
    s = 60
    _rect(b, 0, 0, s, s); _rect(b, 0, 0, 0.7 * s, 0.7 * s)
    _ln(b, (-0.35 * s, -0.35 * s), (0.35 * s, 0.35 * s)); _ln(b, (-0.35 * s, 0.35 * s), (0.35 * s, -0.35 * s))


def g_kanal_menfez(b):      # kanal üstü / yan menfez (kanal kenarı y=0, menfez dışarı)
    w, h = 60, 10
    _rect(b, 0, h / 2, w, h)
    for x in (-w / 3, 0, w / 3):
        _okcizgi(b, (x, h), (x, h + 15), 5)


def g_slot(b):
    w, h = 120, 10
    _rect(b, 0, 0, w, h)
    _ln(b, (-w / 2, -h / 6), (w / 2, -h / 6)); _ln(b, (-w / 2, h / 6), (w / 2, h / 6))
    x = -w / 2 + 10
    while x < w / 2:
        _okcizgi(b, (x, h / 2 + 12), (x, h / 2 + 2), 4); x += 20


def g_swirl(b):
    s = 60
    _rect(b, 0, 0, s, s); _ci(b, (0, 0), 0.42 * s); _ci(b, (0, 0), 0.08 * s)
    for k in range(8):
        a = 45 * k
        c = (0.25 * s * math.cos(math.radians(a)), 0.25 * s * math.sin(math.radians(a)))
        _arc(b, c, 0.17 * s, a + 90, a + 200)


def g_anemostat(b):
    for r in (30, 20, 10):
        _ci(b, (0, 0), r)


def g_panjur(b, ok_ic=True):
    w, h = 80, 25
    _rect(b, 0, 0, w, h)
    for i in range(5):
        x = -w / 2 + 8 + i * 15
        _ln(b, (x, -h / 2 + 2), (x + 10, h / 2 - 2))
    if ok_ic:
        _okcizgi(b, (0, h / 2 + 25), (0, h / 2 + 3), 7)       # taze hava: dışarıdan içeri
    else:
        _okcizgi(b, (0, h / 2 + 3), (0, h / 2 + 25), 7)       # egzoz: içeriden dışarı


def g_panjur_taze(b):
    g_panjur(b, True)


def g_panjur_egzoz(b):
    g_panjur(b, False)


def g_vd(b):                # ayar damperi: kanal içinde 30° kanat + pivot + kol
    G = 40
    _ln(b, (-G * 0.8, G / 2), (G * 0.8, G / 2)); _ln(b, (-G * 0.8, -G / 2), (G * 0.8, -G / 2))
    c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
    _ln(b, (-0.45 * G * c, -0.45 * G * s), (0.45 * G * c, 0.45 * G * s))
    _ci(b, (0, 0), 0.05 * G)
    _ln(b, (0, G / 2), (0, G / 2 + 0.2 * G)); _ln(b, (0, G / 2 + 0.2 * G), (0.15 * G, G / 2 + 0.2 * G))
    _yz(b, 'VD', (0.3 * G, G / 2 + 0.2 * G), 5, TA.MIDDLE_LEFT)


def g_fd(b, et='FD', motor=False):
    G = 40
    _ln(b, (-G * 0.8, G / 2), (G * 0.8, G / 2)); _ln(b, (-G * 0.8, -G / 2), (G * 0.8, -G / 2))
    t = 0.15 * G
    _rect(b, 0, 0, t, G)
    _ln(b, (-t / 2, -G / 2), (t / 2, G / 2)); _ln(b, (-t / 2, G / 2), (t / 2, -G / 2))
    _yz(b, et, (0, -G / 2 - 6), 5)
    if motor:
        _ln(b, (0, G / 2), (0, G / 2 + 5)); _ci(b, (0, G / 2 + 9), 4); _yz(b, 'M', (0, G / 2 + 9), 4)


def g_mfd(b):
    g_fd(b, 'MFD', True)


def g_sd(b):
    g_fd(b, 'SD')


def g_fan_radyal(b):
    R = 25
    _ci(b, (0, 0), R)
    yi = 0.4 * R                                            # çıkış ağzı: çembere üstten teğet kanal (genişlik 0,6R)
    _ln(b, (0, R), (1.3 * R, R))
    _ln(b, (math.sqrt(R * R - yi * yi), yi), (1.3 * R, yi))
    _ln(b, (1.3 * R, yi), (1.3 * R, R))
    _arc(b, (0.1 * R, -0.05 * R), 0.55 * R, 40, 320)          # salyangoz izi
    _no(b, R + 4)


def g_fan_aksiyal(b):
    R = 25
    _ci(b, (0, 0), R)
    _ln(b, (-R * 1.3, R), (R * 1.3, R)); _ln(b, (-R * 1.3, -R), (R * 1.3, -R))          # kanal
    _pl(b, [(0, 0), (-0.25 * R, 0.8 * R), (0.25 * R, 0.8 * R)], True)
    _pl(b, [(0, 0), (-0.25 * R, -0.8 * R), (0.25 * R, -0.8 * R)], True)
    _no(b, R + 4)


def g_aspirator_wc(b):
    w, h = 30, 15
    _rect(b, 0, 0, w, h); _ci(b, (0, 0), 6)
    _ln(b, (-4.2, -4.2), (4.2, 4.2)); _ln(b, (-4.2, 4.2), (4.2, -4.2))


def g_jetfan(b):
    w, h = 120, 30
    _rect(b, 0, 0, w, h); _ci(b, (-w / 2 + h / 2, 0), h * 0.4)
    _okcizgi(b, (w / 2 + 2, 0), (w / 2 + 35, 0), 9)
    _no(b, h / 2 + 4)


# ---- §7 doğalgaz
def g_gaz_kesme(b):
    _papyon(b, dolu=True); _ln(b, (0, 0), (0, 0.4 * L)); _ln(b, (0, 0.4 * L), (0.3 * L, 0.4 * L)); _no(b, 0.45 * L + 3)


def g_gaz_cihaz(b):
    _papyon(b, 0.6 * L, dolu=True)


def g_gaz_sayac(b):
    w, h = 0.8 * L * 1.5, 0.6 * L * 1.5
    _rect(b, 0, h / 2 + 0.2 * L, w, h)
    _pl(b, [(-L, 0), (-w / 2 + 0.1 * w, 0), (-w / 2 + 0.1 * w, 0.2 * L)])
    _pl(b, [(L, 0), (w / 2 - 0.1 * w, 0), (w / 2 - 0.1 * w, 0.2 * L)])
    _yz(b, 'G4', (0, h / 2 + 0.2 * L), 0.3 * h)
    _no(b, h + 0.2 * L + 3)


def g_regulator(b):
    _papyon(b, dolu=True)
    _ln(b, (0, 0), (0, 0.45 * L))
    _arc(b, (0, 0.45 * L), 0.25 * L, 0, 180)
    _ln(b, (-0.25 * L, 0.45 * L), (0.25 * L, 0.45 * L))
    e = b.add_lwpolyline([(0.25 * L, 0.45 * L), (0.8 * L, 0.45 * L), (0.8 * L, 0.0)], dxfattribs={'layer': '0', 'linetype': 'DASHED'})
    e.dxf.ltscale = 2.0
    _yz(b, 'R', (-0.45 * L, 0.55 * L), 0.22 * L)
    _no(b, 0.75 * L + 3)


def g_gaz_selenoid(b):
    g_selenoid(b, dolu=True)


def g_deprem(b):
    _papyon(b, dolu=True)
    _ln(b, (0, 0), (0, 0.4 * L))
    _rect(b, 0, 0.55 * L, 0.3 * L, 0.3 * L)
    _yz(b, 'D', (0, 0.55 * L), 0.2 * L)
    _no(b, 0.75 * L + 3)


def g_servis_kutusu(b):
    w, h = 4.2 * L, 1.6 * L
    e = b.add_lwpolyline([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], close=True,
                         dxfattribs={'layer': '0', 'linetype': 'DASHED'})
    e.dxf.ltscale = 3.0
    k = 0.5
    _papyon(b, L * k, dolu=True, dx=-1.4 * L)                                  # giriş vanası
    _papyon(b, L * k, dolu=True, dx=0.0)                                       # regülatör
    _ln(b, (0, 0), (0, 0.25 * L)); _arc(b, (0, 0.25 * L), 0.15 * L, 0, 180); _ln(b, (-0.15 * L, 0.25 * L), (0.15 * L, 0.25 * L))
    _rect(b, 1.35 * L, 0.2 * L, 0.7 * L, 0.5 * L)                               # sayaç
    _yz(b, 'S', (1.35 * L, 0.2 * L), 0.25 * L)
    for a0, a1 in ((-w / 2 - 0.3 * L, -1.4 * L - L * k / 2), (-1.4 * L + L * k / 2, -L * k / 2), (L * k / 2, 1.0 * L), (1.7 * L, w / 2 + 0.3 * L)):
        _ln(b, (a0, 0), (a1, 0))
    _no(b, h / 2 + 3)


# =====================================================================================  KAYIT
# her satır: anahtar, gruplar, açıklama, kaynak, (MTY dosya anahtarı | ASL anahtarı | geometri fonksiyonu), ek
#   kaynak: 'MTY' (kullanıcı bloğu), 'MTY-VOYAP' (kullanıcının VOYAP dosyasındaki MTY bloğu), 'ASL' (Aselsan lejantı),
#           '03' (03_SEMBOLLER.md geometrisi)
#   ek: dict(celiski=True -> §8 teyit maddesi, olcek=ASL ölçeği, haric=lejantta gösterilmeyen katman parçası)
SV, RV, SK, RK, SP, RP = ('SIHHI TESISAT__VANALAR__', 'RADYATOR TESISATI__VANALAR__', 'SIHHI TESISAT__KOLON ŞEMASI__',
                          'RADYATOR TESISATI__KOLON ŞEMASI__', 'SIHHI TESISAT__KAT PLANI__', 'RADYATOR TESISATI__KAT PLANI__')
KAYIT = [
    # ---------------- SIHHİ
    ('kuresel_vana', ('SIHHI', 'ISITMA'), 'KÜRESEL VANA', 'MTY', SV + 'MTY-KURESEL VANA', {'celiski': 1}),
    ('ventil', ('SIHHI', 'ISITMA'), 'VENTİL (GLOB) VANA', '03', g_ventil, {'celiski': 1}),
    ('surgulu_vana', ('SIHHI', 'ISITMA', 'YANGIN'), 'SÜRGÜLÜ VANA (ŞİBER)', '03', g_surgulu, {}),
    ('kilitli_vana', ('SIHHI', 'ISITMA'), 'KİLİTLİ VANA', 'MTY', SV + 'MTY-KITLENEBILIR VANA', {}),
    ('cekvalf', ('SIHHI', 'ISITMA', 'YANGIN'), 'ÇEKVALF', 'MTY', SV + 'MTY-CEKVALF VANA', {'celiski': 3}),
    ('geri_akis_onleyici', ('SIHHI',), 'GERİ AKIŞ ÖNLEYİCİ', 'MTY', SV + 'MTY-GERI AKIS ONLEYICI', {}),
    ('pislik_tutucu', ('SIHHI', 'ISITMA', 'YANGIN'), 'PİSLİK TUTUCU', 'MTY', SV + 'MTY-PISLIK TUTUCU', {'kes': 0}),
    ('kompansator', ('SIHHI', 'ISITMA', 'YANGIN'), 'KOMPANSATÖR', 'MTY', SV + 'MTY-KOMPANSATOR', {}),
    ('esnek_baglanti', ('SIHHI', 'ISITMA'), 'ESNEK BAĞLANTI', 'MTY', SV + 'MTY-ESNEK BAGLANTI', {}),
    ('basinc_dusurucu', ('SIHHI',), 'BASINÇ DÜŞÜRÜCÜ VANA', '03', g_bdv, {}),
    ('selenoid_vana', ('SIHHI', 'ISITMA'), 'SELENOİD VANA', '03', g_selenoid, {}),
    ('manometre', ('SIHHI', 'ISITMA', 'YANGIN'), 'MANOMETRE', 'MTY', SV + 'MTY-MANOMETRE', {}),
    ('su_sayaci', ('SIHHI',), 'SU SAYACI', 'MTY', SV + 'MTY-SU SAYACI', {}),
    ('su_sayaci_kartli', ('SIHHI',), 'KARTLI SU SAYACI', 'MTY', SV + 'MTY-SU SAYACI KARTLI', {}),
    ('sayac_grubu', ('SIHHI',), 'SU SAYACI GRUBU (ÇOKLU)', 'MTY', SV + 'MTY-SU SAYACI COKLU', {}),
    ('sicak_su_sayac_grubu', ('SIHHI',), 'SICAK SU SAYACI GRUBU (ÇOKLU)', 'MTY', SV + 'MTY-SICAK SU SAYACI COKLU', {}),
    ('sirkulasyon_pompasi', ('SIHHI',), 'SİRKÜLASYON POMPASI', '03', g_pompa, {'blok': 'ROTAS-POMPA'}),
    ('dalgic_pompa', ('SIHHI',), 'DALGIÇ POMPA (ÇUKUR İÇİNDE)', '03', g_dalgic, {}),
    ('pis_su_pompasi_kat', ('SIHHI',), 'PİS SU ÇUKURU VE POMPASI (PLAN)', 'MTY', SV + 'MTY-PIS SU POMASI KAT', {}),
    ('membranli_tank', ('SIHHI',), 'MEMBRANLI TANK (HİDROFOR TANKI)', '03', g_membranli, {}),
    ('depo_hidrofor', ('SIHHI',), 'SU DEPOSU + HİDROFOR', 'MTY', SV + 'MTY-SU DEPOSU + HIDROFOR', {}),
    ('su_yumusatma', ('SIHHI',), 'SU YUMUŞATMA CİHAZI', 'MTY', SV + 'MTY-SU YUMUŞATMA CİHAZI', {}),
    ('boyler', ('SIHHI', 'ISITMA'), 'BOYLER (SERPANTİNLİ)', 'MTY', SV + 'MTY-BOYLER KAT- KOLON', {}),
    ('yer_suzgeci_plan', ('SIHHI',), 'YER SÜZGECİ Ø70 (PLAN)', 'MTY', SP + 'YER SUZGECI DN701', {}),
    ('yer_suzgeci_kolon', ('SIHHI',), 'YER SÜZGECİ Ø70 (KOLON ŞEMASI)', 'MTY', SK + 'YER SUZGECI DN701 KOLON', {}),
    ('temizleme_kapagi', ('SIHHI',), 'TEMİZLEME KAPAĞI (T.T.K.)', 'MTY', SV + 'MTY-TEMIZLEME KAPAGI', {}),
    ('temizleme_kapagi_kolon', ('SIHHI',), 'TEMİZLEME KAPAĞI (KOLON ŞEMASI)', 'MTY', SK + 'MTY-TEMIZLEME KAPAGI KOLON', {}),
    ('havalik_sapkasi', ('SIHHI',), 'HAVALIK ŞAPKASI', 'MTY', SK + 'MTY-KOLON HAVALIK SAPKASI', {}),
    ('rogar', ('SIHHI',), 'RÖGAR (MUAYENE BACASI)', 'MTY', SV + 'MTY-ROGAR KAT', {}),
    ('rogar_yagmur', ('SIHHI',), 'YAĞMUR SUYU RÖGARI', 'MTY', SV + 'MTY-ROGAR YAĞMUR KAT', {}),
    ('kolon_rogar', ('SIHHI',), 'RÖGAR (KOLON ŞEMASI)', 'MTY', SK + 'MTY-KOLON ROGAR', {}),
    ('pis_su_inis', ('SIHHI',), 'PİS SU KOLONU / İNİŞ (PLAN)', 'MTY', SP + 'MTY-PIS-SU-INIS', {}),
    ('kolon_no_pis', ('SIHHI',), 'PİS SU KOLON NUMARASI', 'MTY', SV + 'MTY-KOLON NO PIS SU', {}),
    ('kolon_no_temiz', ('SIHHI',), 'TEMİZ SU KOLON NUMARASI', 'MTY', SV + 'MTY-KOLON NO TEMIZ SU', {}),
    ('kolon_no_yagmur', ('SIHHI',), 'YAĞMUR SUYU KOLON NUMARASI', 'MTY', SV + 'MTY-KOLON NO YAGMUR', {}),
    ('kolon_no_havalik', ('SIHHI',), 'HAVALIK KOLON NUMARASI', 'MTY', SV + 'MTY-KOLON NO HAVALIK', {}),
    ('lavabo_k', ('SIHHI',), 'LAVABO (KOLON ŞEMASI)', 'MTY', SK + 'LAVABO1 KOLON', {}),
    ('klozet_k', ('SIHHI',), 'KLOZET - ALAFRANGA (KOLON ŞEMASI)', 'MTY', SK + 'KLOZET1 KOLON', {}),
    ('hela_k', ('SIHHI',), 'HELA TAŞI - ALATURKA (KOLON ŞEMASI)', 'MTY', SK + 'HELA1 KOLON', {}),
    ('dus_k', ('SIHHI',), 'DUŞ TEKNESİ (KOLON ŞEMASI)', 'MTY', SK + 'DUS TEKNESI1 KOLON', {}),
    ('kuvet_k', ('SIHHI',), 'KÜVET (KOLON ŞEMASI)', 'MTY', SK + 'KUVET1 KOLON', {}),
    ('eviye_k', ('SIHHI',), 'EVİYE (KOLON ŞEMASI)', 'MTY', SK + 'EVIYE1 KOLON', {}),
    ('pisuar_k', ('SIHHI',), 'PİSUVAR (KOLON ŞEMASI)', 'MTY', SK + 'PISUAR1 KOLON', {}),
    ('camasir_k', ('SIHHI',), 'ÇAMAŞIR MAKİNESİ (KOLON ŞEMASI)', 'MTY', SK + 'CAMASIR MAKINASI1 KOLON', {}),
    ('bulasik_k', ('SIHHI',), 'BULAŞIK MAKİNESİ (KOLON ŞEMASI)', 'MTY', SK + 'BULASIK MAKINASI1 KOLON', {}),
    ('suzgec_k', ('SIHHI',), 'SÜZGEÇ (KOLON ŞEMASI)', 'MTY', SK + 'SUZGEC1 KOLON', {}),
    ('klozet_p', ('SIHHI',), 'KLOZET (PLAN)', 'MTY', 'ORNEK__std_klozet_plan', {}),
    ('hela_p', ('SIHHI',), 'HELA TAŞI (PLAN)', 'MTY', 'ORNEK__std_hela-taşı_plan', {}),
    ('dus_p', ('SIHHI',), 'KÖŞE DUŞ TEKNESİ (PLAN)', 'MTY', 'ORNEK__std_köşe-duş-teknesi_plan', {}),
    ('pisuar_p', ('SIHHI',), 'PİSUVAR (PLAN)', 'MTY', 'ORNEK__std_pisuvar-1_plan', {}),
    ('lavabo_p', ('SIHHI',), 'TEZGAH ALTI LAVABO (PLAN)', 'MTY', 'ORNEK__std_tezgah-altı-lavabo-1_plan', {}),
    # ---------------- ISITMA
    ('kelebek_vana', ('ISITMA', 'YANGIN'), 'KELEBEK VANA', 'MTY', SV + 'MTY-KELEBEK VANA', {}),
    ('emniyet_ventili', ('ISITMA', 'SIHHI'), 'EMNİYET VENTİLİ', 'MTY', RV + 'MTY-EMNİYET VENTİLİ', {}),
    ('uc_yollu_vana', ('ISITMA',), 'ÜÇ YOLLU VANA', 'MTY', RV + 'MTY-UC YOLLU VANA', {}),
    ('uc_yollu_motorlu', ('ISITMA',), 'ÜÇ YOLLU MOTORLU VANA (KARIŞIM)', '03', g_uc_yollu_motorlu, {}),
    ('motorlu_vana', ('ISITMA',), 'İKİ YOLLU MOTORLU VANA (ON-OFF)', '03', g_motorlu, {}),
    ('picv', ('ISITMA',), 'BASINÇTAN BAĞIMSIZ MOTORLU VANA (PICV)', '03', g_picv, {}),
    ('termostatik_vana', ('ISITMA',), 'TERMOSTATİK RADYATÖR VANASI', '03', g_termostatik, {}),
    ('rakorlu_donus', ('ISITMA',), 'RADYATÖR DÖNÜŞ (RAKORLU) VANASI', '03', g_rakorlu_donus, {}),
    ('kesme_vanasi_rad', ('ISITMA',), 'RADYATÖR - FANCOİL KESME VANASI', '03', g_kesme_rad, {}),
    ('otomatik_dolum', ('ISITMA',), 'OTOMATİK DOLUM (BESLEME) VANASI', 'MTY', SV + 'MTY-OTOMATIK DOLUM VANASI', {}),
    ('bosaltma_vanasi', ('ISITMA',), 'BOŞALTMA VANASI', 'MTY', RK + 'MTY-BOSALTMA VANA', {}),
    ('kosva', ('ISITMA',), 'KOLON BOŞALTMA VANASI (KOSVA)', 'MTY', RK + 'MTY-KOSVA VANA', {}),
    ('ohac', ('ISITMA',), 'OTOMATİK HAVA ATMA CİHAZI (PURJÖR)', 'MTY', RV + 'MTY-OHAC', {}),
    ('havalik_tupu', ('ISITMA',), 'HAVALIK TÜPÜ', '03', g_havalik_tupu, {}),
    ('termometre', ('ISITMA', 'SIHHI'), 'TERMOMETRE', 'MTY', RV + 'MTY-TERMOMETRE', {}),
    ('pompa', ('ISITMA',), 'POMPA (SİRKÜLASYON)', '03', g_pompa, {}),
    ('pompa_fk', ('ISITMA', 'SIHHI'), 'POMPA - FREKANS KONVERTÖRLÜ', '03', g_pompa_fk, {}),
    ('ikiz_pompa', ('ISITMA',), 'İKİZ POMPA', '03', g_ikiz_pompa, {}),
    ('kazan', ('ISITMA',), 'KAZAN', '03', g_kazan, {}),
    ('kati_yakitli_kazan', ('ISITMA',), 'KATI YAKITLI KAZAN', 'MTY', RV + 'MTY- KATI YAKITLI KAZAN', {}),
    ('kombi', ('ISITMA',), 'KOMBİ', 'MTY', RV + 'MTY-KOMBİ', {}),
    ('genlesme_kapali', ('ISITMA',), 'KAPALI GENLEŞME TANKI (MEMBRANLI)', '03', g_genlesme_kapali, {}),
    ('genlesme_acik', ('ISITMA',), 'AÇIK GENLEŞME DEPOSU', '03', g_genlesme_acik, {}),
    ('denge_kabi', ('ISITMA',), 'DENGE KABI', 'MTY', RV + 'MTY-DENGE KABI', {}),
    ('esanjor', ('ISITMA',), 'EŞANJÖR (PLAKALI)', 'MTY', RV + 'MTY-ESANJOR', {}),
    ('kollektor', ('ISITMA',), 'KOLLEKTÖR (DAİRE / YERDEN ISITMA)', 'MTY', RK + 'MTY-RADYATOR KOLLEKTÖR', {}),
    ('radyator_panel', ('ISITMA',), 'RADYATÖR PANEL', 'MTY', RP + 'MTY-RADYATOR Panel', {}),
    ('kalorimetre', ('ISITMA',), 'KALORİMETRE (ISI SAYACI)', '03', g_kalorimetre, {'kes': 0.48 * L}),
    ('fancoil_gizli', ('ISITMA', 'HAVALANDIRMA'), 'TAVAN TİPİ GİZLİ FANCOİL', '03', g_fancoil_gizli, {}),
    ('fancoil_kaset', ('ISITMA', 'HAVALANDIRMA'), 'TAVAN TİPİ KASETLİ FANCOİL', '03', g_fancoil_kaset, {}),
    ('kolon_no_isitma', ('ISITMA',), 'ISITMA KOLON NUMARASI', 'MTY', RV + 'MTY-RADYATOR KOLON NO', {}),
    # ---------------- YANGIN
    ('sprinkler_dik', ('YANGIN',), 'DİK TİP (UPRIGHT) SPRİNKLER', '03', g_spr_dik, {'celiski': 2}),
    ('sprinkler_sarkik', ('YANGIN',), 'SARKIK TİP (PENDENT) SPRİNKLER', '03', g_spr_sarkik, {'celiski': 2}),
    ('sprinkler_gizli', ('YANGIN',), 'GİZLİ (CONCEALED) SARKIK SPRİNKLER', '03', g_spr_gizli, {}),
    ('sprinkler_yan', ('YANGIN',), 'YAN DUVAR (SIDEWALL) SPRİNKLER', '03', g_spr_yan, {}),
    ('mty_sprinkler_pendant', ('YANGIN',), 'MTY PENDANT SPRİNKLER (KORUMA ALANLI)', 'MTY-VOYAP', 'MTY-PENDANT TIP SPRINKLER-1', {'haric': 'ALAN', 'celiski': 2}),
    ('mty_sprinkler_upright', ('YANGIN',), 'MTY UPRIGHT SPRİNKLER (KORUMA ALANLI)', 'MTY-VOYAP', 'MTY-UPRİGHT TIP SPRINKLER-1', {'haric': 'ALAN', 'celiski': 2}),
    ('izlenebilir_kelebek', ('YANGIN',), 'İZLENEBİLİR KELEBEK VANA', 'MTY', SV + 'MTY-IZLENEBILIR KELEBEK VANA', {}),
    ('osy_vana', ('YANGIN',), 'YÜKSELEN MİLLİ VANA (OS&Y)', 'ASL', 'YÜKSELEN MİLLİ VANA', {'olcek': 0.5}),
    ('piv', ('YANGIN',), 'POST İNDİKATÖR VANA', 'ASL', 'POST İNDİKATÖR VANA', {'olcek': 0.5}),
    ('bdv_yangin', ('YANGIN',), 'BASINÇ DÜŞÜRÜCÜ DENGELEME VANASI', 'ASL', 'BASINÇ DÜŞÜRÜCÜ DENGELEME VANASI', {'olcek': 0.5}),
    ('akis_anahtari', ('YANGIN',), 'AKIŞ ANAHTARI (FLOW SWITCH)', 'ASL', 'FLOW SWITCH', {'olcek': 0.4}),
    ('test_drenaj', ('YANGIN',), 'TEST VE DRENAJ SETİ', 'ASL', 'TEST DRENAJ SETİ', {'olcek': 0.4}),
    ('islak_alarm', ('YANGIN',), 'ISLAK ALARM VANA İSTASYONU', 'ASL', 'ISLAK ALARM VANA ISTASYONU', {'olcek': 0.3}),
    ('kuru_alarm', ('YANGIN',), 'KURU ALARM VANA İSTASYONU', 'ASL', 'TEK KİTLEMELİ KURU ALARM VANA ISTASYONU', {'olcek': 0.3}),
    ('itfaiye_agzi', ('YANGIN',), 'İTFAİYE BAĞLANTI AĞZI 2 x 2 1/2"', 'ASL', 'İTFAİYE BAĞLANTI AĞZI / 2 x 2 1/2"', {'olcek': 0.3}),
    ('itfaiye_vanasi', ('YANGIN',), 'BASINÇ SINIRLAYICI İTFAİYE BAĞLANTI VANASI', '03', g_itfaiye_vana, {}),
    ('yangin_dolabi_plan', ('YANGIN',), 'YANGIN DOLABI (KAT PLANI)', 'ASL', 'YANGIN DOLABI (KAT PLANI)', {'olcek': 1.0}),
    ('yangin_dolabi_kolon', ('YANGIN',), 'YANGIN DOLABI (KOLON ŞEMASI)', 'ASL', 'YANGIN DOLABI (KOLON ŞEMASI)', {'olcek': 0.5}),
    ('hidrant', ('YANGIN',), 'YER ÜSTÜ HİDRANT', '03', g_hidrant, {}),
    ('purjor_sprinkler', ('YANGIN',), 'OTOMATİK PURJÖR (SPRİNKLER HATTI)', '03', g_purjor_spr, {}),
    ('yangin_pompa_seti', ('YANGIN',), 'YANGIN POMPA GRUBU (ELEKTRİKLİ + DİZEL + JOKEY)', '03', g_yangin_pompa_seti, {}),
    ('kolon_no_yangin', ('YANGIN',), 'YANGIN KOLON NUMARASI', 'MTY', SK + 'MTY-KOLON NO', {}),
    # ---------------- HAVALANDIRMA
    ('kanal_ufleme', ('HAVALANDIRMA',), 'ÜFLEME (BESLEME) KANALI KESİTİ', '03', g_kanal_ufleme, {}),
    ('kanal_emis', ('HAVALANDIRMA',), 'EMİŞ / DÖNÜŞ KANALI KESİTİ', '03', g_kanal_emis, {}),
    ('kanal_egzoz', ('HAVALANDIRMA',), 'EGZOZ (ATIŞ) KANALI KESİTİ', '03', g_kanal_egzoz, {}),
    ('kanal_yuvarlak', ('HAVALANDIRMA',), 'YUVARLAK KANAL KESİTİ (ÜFLEME)', '03', g_kanal_yuvarlak, {}),
    ('flex', ('HAVALANDIRMA',), 'FLEKSİBIL KANAL BAĞLANTISI', '03', g_flex, {}),
    ('difuzor_4', ('HAVALANDIRMA',), 'TAVAN DİFÜZÖRÜ 4 YÖNLÜ (ÜFLEME)', '03', g_difuzor4, {}),
    ('emis_menfezi', ('HAVALANDIRMA',), 'EMİŞ MENFEZİ / DÖNÜŞ IZGARASI', '03', g_emis_menfez, {}),
    ('perfore_menfez', ('HAVALANDIRMA',), 'PERFORE MENFEZ', '03', g_perfore, {}),
    ('kanal_menfezi', ('HAVALANDIRMA',), 'KANAL ÜSTÜ / YAN MENFEZ', '03', g_kanal_menfez, {}),
    ('slot_difuzor', ('HAVALANDIRMA',), 'SLOT (LİNEER) DİFÜZÖR', '03', g_slot, {}),
    ('swirl', ('HAVALANDIRMA',), 'SWİRL DİFÜZÖR', '03', g_swirl, {}),
    ('anemostat', ('HAVALANDIRMA',), 'ANEMOSTAT', '03', g_anemostat, {}),
    ('panjur_taze', ('HAVALANDIRMA',), 'TAZE HAVA ALIŞ PANJURU', '03', g_panjur_taze, {}),
    ('panjur_egzoz', ('HAVALANDIRMA',), 'EGZOZ ATIŞ PANJURU', '03', g_panjur_egzoz, {}),
    ('ayar_damperi', ('HAVALANDIRMA',), 'AYAR DAMPERİ (VD)', '03', g_vd, {}),
    ('yangin_damperi', ('HAVALANDIRMA', 'YANGIN'), 'YANGIN DAMPERİ (FD)', '03', g_fd, {}),
    ('motorlu_yangin_damperi', ('HAVALANDIRMA',), 'MOTORLU YANGIN DAMPERİ (MFD)', '03', g_mfd, {}),
    ('duman_damperi', ('HAVALANDIRMA',), 'DUMAN DAMPERİ (SD)', '03', g_sd, {}),
    ('fan_radyal', ('HAVALANDIRMA',), 'RADYAL FAN', '03', g_fan_radyal, {}),
    ('fan_aksiyal', ('HAVALANDIRMA',), 'AKSİYAL / KANAL TİPİ FAN', '03', g_fan_aksiyal, {}),
    ('aspirator_wc', ('HAVALANDIRMA',), 'WC ASPİRATÖRÜ (DUVAR / KANAL TİPİ)', '03', g_aspirator_wc, {}),
    ('cati_fani', ('HAVALANDIRMA',), 'ÇATI TİPİ FAN', 'MTY', 'ORNEK__MTY-ÇATI TİPİ FAN', {}),
    ('jet_fan', ('HAVALANDIRMA',), 'JET FAN (OTOPARK)', '03', g_jetfan, {}),
    # ---------------- DOĞALGAZ
    ('gaz_kesme_vanasi', ('DOGALGAZ',), 'ANA KESME VANASI (DOĞALGAZ)', '03', g_gaz_kesme, {'celiski': 4}),
    ('gaz_cihaz_vanasi', ('DOGALGAZ',), 'CİHAZ VANASI (DOĞALGAZ)', '03', g_gaz_cihaz, {'celiski': 4}),
    ('gaz_sayaci', ('DOGALGAZ',), 'GAZ SAYACI (KÖRÜKLÜ G4)', '03', g_gaz_sayac, {}),
    ('regulator', ('DOGALGAZ',), 'BASINÇ REGÜLATÖRÜ', '03', g_regulator, {}),
    ('gaz_selenoid', ('DOGALGAZ',), 'SELENOİD VANA (DOĞALGAZ)', '03', g_gaz_selenoid, {}),
    ('deprem_vanasi', ('DOGALGAZ',), 'DEPREM VANASI', '03', g_deprem, {}),
    ('servis_kutusu', ('DOGALGAZ',), 'SERVİS KUTUSU (VANA + REGÜLATÖR + SAYAÇ)', '03', g_servis_kutusu, {}),
]
SEMBOL = {k[0]: dict(ad=k[0], gruplar=k[1], aciklama=k[2], kaynak=k[3], src=k[4], ek=k[5]) for k in KAYIT}

CELISKI = {
    1: 'Küresel vana / ventil: küresel = MTY-KURESEL VANA (TR biçimi), ventil (glob) = papyon + içi dolu nokta.',
    2: 'Sprinkler: dik = tek daire Ø25, sarkık = iç içe çift daire (ada_hayat ve VOYAP onaylı biçim); MTY sprinkler blokları ayrıca var.',
    3: 'Çekvalf: TR lejant biçimi (MTY-CEKVALF VANA) kullanıldı; ISO dolu üçgen biçimi kullanılmadı.',
    4: 'Doğalgaz vanası: içi dolu papyon (su vanasından ayırt etmek için); dağıtım şirketi lejantıyla teyit edilmeli.',
}


# önceki onaylı çizimlerde (VOYAP yangın, motor/voyap/lib.py) kullanılan blok adları -> sembol (otomatik lejant tanısın diye)
TAKMA_AD = {'ASL-SPR-UP': 'sprinkler_dik', 'ASL-SPR-PE': 'sprinkler_sarkik', 'ASL-OSY': 'osy_vana', 'ASL-MANO': 'manometre',
            'ASL-YD-PLAN': 'yangin_dolabi_plan', 'ASL-YD-KOLON': 'yangin_dolabi_kolon', 'ASL-CEK': 'cekvalf', 'ASL-TEST': 'test_drenaj',
            'ASL-IZL-KELEBEK': 'izlenebilir_kelebek', 'ASL-FS': 'akis_anahtari', 'ASL-WAV': 'islak_alarm', 'ASL-ITFAIYE': 'itfaiye_agzi',
            'ASL-KELEBEK': 'kelebek_vana', 'ASL-PISLIK': 'pislik_tutucu', 'ASL-KOMP': 'kompansator', 'ASL-BDV': 'bdv_yangin',
            'ASL-PIV': 'piv', 'Y-PURJOR': 'purjor_sprinkler', 'Y-EMNIYET': 'emniyet_ventili', 'Y-MTANK': 'membranli_tank'}


def blok_adi(ad):
    s = SEMBOL[ad]
    if s['ek'].get('blok'):
        return s['ek']['blok']
    if s['kaynak'] == 'MTY':
        return s['src'].split('__')[-1]
    if s['kaynak'] == 'MTY-VOYAP':
        return s['src']
    return 'ROTAS-' + ad.upper().replace('_', '-')


# =====================================================================================  doküman hazırlığı
def hazirla(doc):
    """katmanlar, yazı stili, çizgi tipleri"""
    if STIL not in doc.styles:
        doc.styles.add(STIL, font='arial.ttf')
    for lt in ('DASHED', 'DASHDOT'):
        if lt not in doc.linetypes:
            try:
                ezdxf.setup_linetypes(doc)
            except Exception:
                pass
            break
    for _, _, k, c in GRUPLAR:
        if k not in doc.layers:
            doc.layers.add(k, color=c)
    for k, c in YARDIMCI_KATMAN.items():
        if k not in doc.layers:
            doc.layers.add(k, color=c)
    for _, _, k, c, lt in BORU_SATIR:
        if k not in doc.layers:
            doc.layers.add(k, color=c, linetype=lt if lt in doc.linetypes else 'Continuous')


def _mty_klasor():
    if os.path.isdir(MTY_DIR) and glob.glob(os.path.join(MTY_DIR, '*.dxf')):
        return MTY_DIR
    # kurulumdan sonra /tmp silinmişse depodaki arşivden aç
    hedef = '/'
    try:
        with tarfile.open(MTY_TAR) as t:
            t.extractall(hedef)
    except Exception:
        subprocess.run(['tar', 'xJf', MTY_TAR, '-C', '/'], check=False)
    return MTY_DIR


def _temizle(sdoc):
    """dinamik bloklardan kalan, tanımı olmayan anonim (*U, *X) INSERT'leri kaynak kopyada siler"""
    for lay in list(sdoc.blocks) + [sdoc.modelspace()]:
        for e in list(lay):
            if e.dxftype() == 'INSERT' and e.dxf.name not in sdoc.blocks:
                lay.delete_entity(e)


def _mty_dosyadan(doc, anahtar):
    ad = anahtar.split('__')[-1]
    if ad in doc.blocks:
        return ad
    f = os.path.join(_mty_klasor(), anahtar + '.dxf')
    try:
        sdoc = ezdxf.readfile(f)
    except Exception:
        from ezdxf import recover
        sdoc, _ = recover.readfile(f)
    _temizle(sdoc)
    base = sdoc.header.get('$INSBASE', (0, 0, 0))
    blk = doc.blocks.new(ad, base_point=(base[0], base[1]))
    im = Importer(sdoc, doc)
    im.import_entities(list(sdoc.modelspace()), blk)
    im.finalize()
    return ad


_VOYAP = None


def _voyap_blok(doc, ad):
    global _VOYAP
    if ad in doc.blocks:
        return ad
    if _VOYAP is None:
        if not os.path.exists(VOYAP_SIH):
            raise FileNotFoundError(VOYAP_SIH)
        from ezdxf import recover
        _VOYAP, _ = recover.readfile(VOYAP_SIH)
    im = Importer(_VOYAP, doc)
    im.import_blocks([ad])
    im.finalize()
    return ad


_ASL = None


def _asl_blok(doc, ad, anahtar, k):
    global _ASL
    if _ASL is None:
        _ASL = pickle.load(open(ASL_PKL, 'rb'))
    S = _ASL[anahtar]
    b = doc.blocks.new(ad)
    pr_ = S['prim']
    if anahtar == 'FLOW SWITCH':          # lejanttaki iki sembolden vanalı olan (VOYAP ile aynı seçim)
        pr_ = [p for p in pr_ if (p[0] in 'LP' and min(q[0] for q in p[1]) > 20) or (p[0] == 'C' and p[1][0] > 20) or (p[0] == 'T' and p[1][0] > 0)]
    xs = [q[0] for p in pr_ if p[0] in 'LP' for q in p[1]] + [p[1][0] for p in pr_ if p[0] == 'C']
    ys = [q[1] for p in pr_ if p[0] in 'LP' for q in p[1]] + [p[1][1] for p in pr_ if p[0] == 'C']
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    lim = max(S['w'], S['h'])
    for p in pr_:
        if p[0] == 'L':
            b.add_line(((p[1][0][0] - cx) * k, (p[1][0][1] - cy) * k), ((p[1][1][0] - cx) * k, (p[1][1][1] - cy) * k), dxfattribs=_a())
        elif p[0] == 'P':
            b.add_lwpolyline([((q[0] - cx) * k, (q[1] - cy) * k) for q in p[1]], dxfattribs=_a())
        elif p[0] == 'C' and p[1][2] <= lim:
            b.add_circle(((p[1][0] - cx) * k, (p[1][1] - cy) * k), p[1][2] * k, dxfattribs=_a())
        elif p[0] == 'T' and p[3] > 0 and str(p[2]).strip():
            t = b.add_text(str(p[2]), height=p[3] * k, dxfattribs={'layer': '0', 'style': STIL, 'width': 0.7})
            t.set_placement(((p[1][0] - cx) * k, (p[1][1] - cy) * k))
    _no(b, max(ys) * k - cy * k + 3)
    return ad


def blok_tanimla(doc, ad):
    """sembolün BLOCK tanımını (yoksa) oluşturur, blok adını döndürür"""
    hazirla(doc)
    s = SEMBOL[ad]
    bn = blok_adi(ad)
    if bn in doc.blocks:
        return bn
    if s['kaynak'] == 'MTY':
        return _mty_dosyadan(doc, s['src'])
    if s['kaynak'] == 'MTY-VOYAP':
        return _voyap_blok(doc, s['src'])
    if s['kaynak'] == 'ASL':
        return _asl_blok(doc, bn, s['src'], s['ek'].get('olcek', 0.5))
    b = doc.blocks.new(bn)
    s['src'](b)
    return bn


def tumunu_tanimla(doc):
    sonuc = {}
    for ad in SEMBOL:
        try:
            sonuc[ad] = blok_tanimla(doc, ad)
        except Exception as ex:          # kaynak dosya yoksa (ör. VOYAP dosyası silinmiş) atla, raporla
            sonuc[ad] = None
            print('UYARI sembol tanımlanamadı:', ad, ex)
    return sonuc


# =====================================================================================  yerleştirme
def ciz(hedef, ad, x, y, aci=0.0, olcek=1.0, no=None, katman=None, ozn=None):
    """hedef: modelspace / paperspace / BlockLayout. ad: SEMBOL anahtarı (veya doğrudan blok adı).
    no: 'V-01' gibi numara (ATTRIB NO). ozn: {'CAP': 'DN25', ...} MTY blok öznitelikleri."""
    doc = hedef.doc
    bn = blok_tanimla(doc, ad) if ad in SEMBOL else ad
    if katman is None:
        katman = GRUP_KATMAN[SEMBOL[ad]['gruplar'][0]] if ad in SEMBOL else '0'
    if katman not in doc.layers:
        doc.layers.add(katman)
    ins = hedef.add_blockref(bn, (x, y), dxfattribs={'layer': katman, 'rotation': aci, 'xscale': olcek, 'yscale': olcek})
    deg = dict(ozn or {})
    if no:
        deg['NO'] = no
    blk = doc.blocks.get(bn)
    tanimli = {e.dxf.tag for e in blk if e.dxftype() == 'ATTDEF'}
    if tanimli:
        ins.add_auto_attribs({t: deg.get(t, '') for t in tanimli})
        for a in ins.attribs:
            a.dxf.style = STIL
    if no and 'NO' not in tanimli:      # MTY bloğunda NO etiketi yok: ATTRIB olarak eklenir (blok patlatılmaz)
        ins.add_attrib('NO', no, (x, y), dxfattribs={'layer': katman, 'height': 0.3 * L * olcek, 'style': STIL})
    # numara her zaman okunur (dönük değil) ve sembolün dünya koordinatındaki üst kenarının üstünde durur
    u = _bb(doc, bn)
    if u:
        a_ = math.radians(aci)
        ust = max(x_ * math.sin(a_) + y_ * math.cos(a_) for x_ in (u[0], u[2]) for y_ in (u[1], u[3])) * olcek
    else:
        ust = 10 * olcek
    for a in ins.attribs:
        if a.dxf.tag == 'NO':
            a.dxf.rotation = 0
            a.dxf.height = 0.3 * L * olcek
            a.set_placement((x, y + ust + 2), align=TA.BOTTOM_CENTER)
    return ins


# akış yönü olan semboller: boru ters yönde çizilse de bloğun yönü korunur
YONLU = {'cekvalf', 'geri_akis_onleyici', 'pompa', 'pompa_fk', 'sirkulasyon_pompasi', 'basinc_dusurucu', 'regulator',
         'uc_yollu_motorlu', 'akis_anahtari', 'islak_alarm', 'kuru_alarm', 'emniyet_ventili', 'yangin_pompa_seti', 'jet_fan'}


def hat(hedef, p0, p1, semboller, katman, sembol_katmani=None, genislik=0.0):
    """p0-p1 düz boru; semboller = [(t 0..1, ad, no)] — boru sembol boyunca (±L/2) kesilir, sembol boru yönünde döner"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    uz = math.hypot(dx, dy)
    aci = math.degrees(math.atan2(dy, dx))
    kes = []
    for t, ad, no in sorted(semboller, key=lambda s: s[0]):
        bn = blok_tanimla(hedef.doc, ad) if ad in SEMBOL else ad
        u = _bb(hedef.doc, bn) or (-L / 2, 0, L / 2, 0)
        ek = SEMBOL[ad]['ek'] if ad in SEMBOL else {}
        a_ = aci
        x0, x1 = u[0], u[2]
        if ad not in YONLU and not (-90.0 < aci <= 90.0):          # simetrik sembol ters dönmesin (yazılar okunur kalsın)
            a_ = aci - 180.0
            x0, x1 = -u[2], -u[0]
        if 'kes' in ek:                                             # boru gövdesi sembolün içinden geçer (ör. pislik tutucu)
            x0, x1 = -ek['kes'], ek['kes']
        if x1 > x0:
            kes.append((t * uz + x0, t * uz + x1))
        ciz(hedef, ad, p0[0] + dx * t, p0[1] + dy * t, a_, 1.0, no, sembol_katmani)
    s0 = 0.0
    ux, uy = dx / uz, dy / uz
    for a, b in kes + [(uz, uz)]:
        if a - s0 > 0.5:
            e = hedef.add_lwpolyline([(p0[0] + ux * s0, p0[1] + uy * s0), (p0[0] + ux * a, p0[1] + uy * a)], dxfattribs={'layer': katman})
            if genislik:
                e.dxf.const_width = genislik
        s0 = b


# =====================================================================================  sınır kutusu
_BB = {}


def _bb(doc, bn, haric=None):
    """görünür geometrinin (invisible ve ATTDEF hariç) blok koordinatında sınır kutusu: (x0, y0, x1, y1)"""
    key = (id(doc), bn, haric)
    if key in _BB:
        return _BB[key]
    blk = doc.blocks.get(bn)
    ents = [e for e in blk if e.dxftype() not in ('ATTDEF',) and not e.dxf.get('invisible', 0)
            and not (haric and haric in e.dxf.get('layer', ''))]
    try:
        b = _bbox.extents(ents, fast=True)
    except Exception:
        b = None
    r = (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y) if b is not None and b.has_data else None
    _BB[key] = r
    return r


def _lejant_blogu(doc, bn, haric):
    """koruma alanı gibi lejantta gösterilmeyecek katmanlı parçaları ayıklanmış lejant kopyası (çizimdeki blok aynen kalır)"""
    yeni = 'ROTAS-LJ-' + bn
    if yeni in doc.blocks:
        return yeni
    src = doc.blocks.get(bn)
    b = doc.blocks.new(yeni, base_point=src.block.dxf.base_point)
    for e in src:
        if e.dxftype() == 'ATTDEF' or haric in e.dxf.get('layer', ''):
            continue
        b.add_entity(e.copy())
    return yeni


# =====================================================================================  lejant tablosu
def _metin(msp, s, p, h, lay, al=TA.MIDDLE_LEFT, w=0.85):
    t = msp.add_text(s, height=h, dxfattribs={'layer': lay, 'style': STIL, 'width': w})
    t.set_placement(p, align=al)
    return t


def _kutu(msp, x0, y0, x1, y1, lay=LEJ_CER, w=0.0):
    e = msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': lay})
    if w:
        e.dxf.const_width = w
    return e


def lejant_tablosu(msp, x0, y0, baslik, satirlar, adet=False, kaynak=False, notlar=()):
    """ROTAŞ lejant tarzı tablo. x0,y0 = sol üst köşe. satirlar: [dict(ad|boru, aciklama, adet?, kaynak?)].
    Dönüş: (genişlik, yükseklik)."""
    doc = msp.doc
    hazirla(doc)
    W_S, W_A, W_N, W_K = 150.0, 420.0, 70.0, 110.0
    W = W_S + W_A + (W_N if adet else 0) + (W_K if kaynak else 0)
    PAD = 10.0
    y = y0
    # başlık kutusu (çift çerçeve, örnek lejant gibi)
    _kutu(msp, x0, y - 70, x0 + W + 2 * PAD, y)
    _kutu(msp, x0 + PAD, y - 60, x0 + W + PAD, y - 10, w=1.0)
    _metin(msp, baslik, (x0 + PAD + W / 2, y - 35), 18, LEJ_BAS, TA.MIDDLE_CENTER, 0.9)
    y -= 80
    ytab0 = y
    xs = x0 + PAD
    y -= PAD
    # sütun başlıkları
    hb = 30.0
    cols = [('SEMBOL', W_S), ('AÇIKLAMA', W_A)] + ([('ADET', W_N)] if adet else []) + ([('KAYNAK', W_K)] if kaynak else [])
    cx = xs
    for ad, w in cols:
        _kutu(msp, cx, y - hb, cx + w, y)
        _metin(msp, ad, (cx + w / 2, y - hb / 2), 11, LEJ_YAZ, TA.MIDDLE_CENTER)
        cx += w
    y -= hb
    for s in satirlar:
        bn = None
        rh = 50.0
        if 'ad' in s:
            bn0 = s.get('blok') or (blok_tanimla(doc, s['ad']) if s['ad'] in SEMBOL else s['ad'])
            haric = SEMBOL[s['ad']]['ek'].get('haric') if s['ad'] in SEMBOL else None
            bn = _lejant_blogu(doc, bn0, haric) if haric else bn0
            u = _bb(doc, bn)
            if u:
                bw, bh = max(u[2] - u[0], 1e-3), max(u[3] - u[1], 1e-3)
                k0 = min(2.0, (W_S - 30) / bw, 70.0 / bh)
                if bh * k0 > 36:
                    rh = min(120.0, max(50.0, bh * k0 + 14))
        cx = xs
        for _, w in cols:
            _kutu(msp, cx, y - rh, cx + w, y)
            cx += w
        mx, my = xs + W_S / 2, y - rh / 2
        if bn:
            u = _bb(doc, bn)
            if u:
                bw, bh = max(u[2] - u[0], 1e-3), max(u[3] - u[1], 1e-3)
                k = min(2.0, (W_S - 30) / bw, (rh - 14) / bh)
                ox = mx - (u[0] + u[2]) / 2 * k
                oy = my - (u[1] + u[3]) / 2 * k
                msp.add_blockref(bn, (ox, oy), dxfattribs={'layer': s.get('katman', 'ROTAS-LEJANT-SEMBOL'), 'xscale': k, 'yscale': k})
        elif 'boru' in s:
            e = msp.add_line((xs + 15, my), (xs + W_S - 15, my), dxfattribs={'layer': s['boru']})
            e.dxf.ltscale = 12.0
        _metin(msp, s['aciklama'] + (' (*)' if s.get('celiski') else ''), (xs + W_S + 10, my), 12, LEJ_YAZ)
        cx = xs + W_S + W_A
        if adet:
            _metin(msp, str(s.get('adet', '')), (cx + W_N / 2, my), 12, LEJ_YAZ, TA.MIDDLE_CENTER)
            cx += W_N
        if kaynak:
            _metin(msp, s.get('kaynak', ''), (cx + W_K / 2, my), 8, LEJ_YAZ, TA.MIDDLE_CENTER, 0.75)
        y -= rh
    y -= 8
    for n in notlar:
        _metin(msp, n, (xs, y - 6), 9, LEJ_YAZ, TA.MIDDLE_LEFT, 0.8)
        y -= 14
    y -= PAD
    _kutu(msp, x0, y, x0 + W + 2 * PAD, ytab0)
    return W + 2 * PAD, y0 - y


KAYNAK_YAZI = {'MTY': 'MTY bloğu', 'MTY-VOYAP': 'MTY (VOYAP)', 'ASL': 'Aselsan lejantı', '03': '03 geometri'}


def _not_satirlari(celiskiler):
    n = []
    if celiskiler:
        n.append('(*) Biçimi kullanıcıya teyit ettirilecek sembol (03_SEMBOLLER.md §8):')
        for c in sorted(celiskiler):
            n.append('     %d) %s' % (c, CELISKI[c]))
    return n


def kutuphane_dxf(yol):
    """Çıktı 1: tüm blok tanımları + tesisat türüne göre lejant paftaları"""
    doc = ezdxf.new('R2018', setup=True)
    doc.header['$INSUNITS'] = 5
    doc.header['$LTSCALE'] = 1.0
    hazirla(doc)
    msp = doc.modelspace()
    tumunu_tanimla(doc)
    x = 0.0
    yukseklik = 0.0
    for g, baslik, kat, _ in GRUPLAR:
        satir = [dict(boru=k, aciklama=a) for gg, a, k, _, _ in BORU_SATIR if gg == g]
        cel = set()
        for ad, s in SEMBOL.items():
            if g in s['gruplar']:
                if blok_adi(ad) not in doc.blocks:
                    continue
                c = s['ek'].get('celiski')
                if c:
                    cel.add(c)
                satir.append(dict(ad=ad, aciklama=s['aciklama'], kaynak=KAYNAK_YAZI[s['kaynak']], celiski=c, katman=kat))
        w, h = lejant_tablosu(msp, x, 0.0, baslik, satir, kaynak=True, notlar=_not_satirlari(cel))
        yukseklik = max(yukseklik, h)
        x += w + 60
    # genel başlık (DENEME)
    _metin(msp, 'ROTAŞ MEKANİK TESİSAT SEMBOL KÜTÜPHANESİ — DENEME', (0, 60), 30, LEJ_BAS, TA.BOTTOM_LEFT, 0.9)
    _metin(msp, 'Birim cm, plan 1/50. MTY blokları kullanıcının kütüphanesinden patlatılmadan alınmıştır; diğerleri 03_SEMBOLLER.md geometrisiyle çizilmiştir.',
           (0, 30), 10, LEJ_YAZ, TA.BOTTOM_LEFT, 0.85)
    doc.saveas(yol)
    return doc


# =====================================================================================  Çıktı 2: otomatik lejant
def _ters_harita(doc):
    """blok adı -> sembol anahtarı (yalnız bu dokümanda tanımlı olanlar)"""
    m = {}
    for ad in sorted(SEMBOL, key=lambda a: 1 if SEMBOL[a]['ek'].get('blok') else 0):
        bn = blok_adi(ad)
        if bn in doc.blocks and bn not in m:
            m[bn] = ad
    for bn, ad in TAKMA_AD.items():
        if bn in doc.blocks and bn not in m:
            m[bn] = ad
    return m


_KATMAN_ANAHTAR = [('DOGALGAZ', ('GAZ',)), ('YANGIN', ('YANGIN', 'SPRINK', 'SPRİNK')),
                  ('HAVALANDIRMA', ('HAVALANDIRMA', 'KANAL', 'UFLEME', 'EGZOZ', 'MENFEZ', 'DUMAN')),
                  ('ISITMA', ('ISITMA', 'RADYATOR', 'RADYATÖR', 'KAZAN', 'KOLLEKT', 'KOLLET', 'PEX')),
                  ('SIHHI', ('SIHHI', 'SOGUK', 'SICAK', 'PIS', 'YAGMUR', 'TEMIZ', 'SIRKULASYON', 'ROGAR'))]


def katman_grubu(katman):
    k = katman.upper()
    for g, anah in _KATMAN_ANAHTAR:
        if any(a in k for a in anah):
            return g
    return None


_SON_ORNEK = {}          # (grup, sembol) -> çizimde kullanılan gerçek blok adı (lejant bu bloğu çizer)


def kullanim_say_grup(doc, yerlesim=None):
    """{(grup, sembol): adet}. Grup, INSERT'in (iç içe ise en dıştaki anlamlı) katmanından bulunur
    (ROTAS-ISITMA-..., MTY-ISITMA-...); bulunamazsa sembolün birincil grubu alınır.
    Kütüphane dışı bloklar (kullanıcı grup blokları) özyinelemeli taranır; ROTAS-LEJANT* katmanı ve ROTAS-LJ- bloklar sayılmaz."""
    harita = _ters_harita(doc)
    sayim = {}
    ORNEK = _SON_ORNEK
    ORNEK.clear()

    def ekle(r, k, v):
        r[k] = r.get(k, 0) + v

    def tek(e, derin, dis_grup):
        n = e.dxf.name
        g = katman_grubu(e.dxf.layer) or dis_grup
        if n.startswith('ROTAS-LJ-'):
            return {}
        if n in harita:
            ad = harita[n]
            gg = g or SEMBOL[ad]['gruplar'][0]
            ORNEK.setdefault((gg, ad), n)
            return {(gg, ad): 1}
        if (n.startswith('*') and n[1:2] in ('D', 'T', 'M', 'P')) or derin > 8 or n not in doc.blocks:
            return {}
        r = {}
        for c in doc.blocks.get(n):
            if c.dxftype() == 'INSERT':
                for k, v in tek(c, derin + 1, g).items():
                    ekle(r, k, v)
        return r

    lay = yerlesim if yerlesim is not None else doc.modelspace()
    for e in lay.query('INSERT'):
        if e.dxf.layer.startswith('ROTAS-LEJANT'):
            continue
        for k, v in tek(e, 0, None).items():
            ekle(sayim, k, v)
    return sayim


def kullanim_say(doc, yerlesim=None):
    """{sembol: adet} (gruplardan bağımsız toplam)"""
    r = {}
    for (g, ad), v in kullanim_say_grup(doc, yerlesim).items():
        r[ad] = r.get(ad, 0) + v
    return r


def otomatik_lejant(doc, x=None, y=None, baslik_onek='', yerlesim=None):
    """DXF'teki kullanılan kütüphane bloklarını sayar; yalnız kullanılanların lejantını ve adet tablosunu
    tesisat türüne göre gruplayarak çizer. x,y verilmezse çizimin sağına konur. Dönüş: {sembol: adet}."""
    hazirla(doc)
    msp = doc.modelspace()
    sg = kullanim_say_grup(doc, yerlesim)
    if x is None or y is None:
        ents = [e for e in msp if not e.dxf.layer.startswith('ROTAS-LEJANT')]
        b = _bbox.extents(ents, fast=True)
        x = (b.extmax.x + 150) if b.has_data else 0.0
        y = b.extmax.y if b.has_data else 0.0
    cx = x
    for g, baslik, kat, _ in GRUPLAR:
        sayim = {ad: v for (gg, ad), v in sg.items() if gg == g}
        ads = list(sayim)
        if not ads:
            continue
        ads.sort(key=lambda a: list(SEMBOL).index(a))
        cel = {SEMBOL[a]['ek'].get('celiski') for a in ads} - {None}
        satir = [dict(ad=a, blok=_SON_ORNEK.get((g, a)), aciklama=SEMBOL[a]['aciklama'], adet=sayim[a], celiski=SEMBOL[a]['ek'].get('celiski'), katman=kat) for a in ads]
        top = sum(sayim[a] for a in ads)
        w, h = lejant_tablosu(msp, cx, y, baslik_onek + baslik, satir, adet=True,
                              notlar=['Toplam sembol adedi: %d (çizimdeki INSERT sayımından otomatik).' % top] + _not_satirlari(cel))
        cx += w + 60
    top = {}
    for (g, ad), v in sg.items():
        top[ad] = top.get(ad, 0) + v
    return top
