"""Cafer Göktaş - revizyon 2: tasarım geometrisi (zemin kat koordinatları, cm).

Islak hacimler üç katta aynıdır (mimari karşılaştırma: farklar yalnız giriş kapısı/pencere ve 2. kat çatı çizgileri).
"""
import math
import pickle
from shapely.geometry import Polygon, LineString, Point, box

FL = pickle.load(open('/tmp/claude-0/cg_flat.pkl', 'rb'))

# ------------------------------------------------------------------ yapısal engeller
COLS = [(-5433, -22191, -5373, -22161), (-5431, -22446, -5401, -22396), (-5429, -22706, -5379, -22671),
        (-5426, -23036, -5396, -22976), (-5132, -22706, -5082, -22676), (-5132, -22446, -5082, -22416),
        (-4857, -23036, -4794, -23006), (-4795, -22706, -4760, -22653), (-4772, -22195, -4712, -22165),
        (-4771, -22461, -4736, -22408)]


def col_polys():
    """Kolon katmanındaki gerçek poligonlar (zemin)"""
    out = []
    for k, l, d, p in FL:
        if l != 'Kolon' or k != 'P' or len(d) < 4:
            continue
        if all(-5695 < q[0] < -4445 and -23250 < q[1] < -22080 for q in d):
            pg = Polygon(d).buffer(0)
            if pg.area > 100:
                out.append(pg)
    # tekrarları ayıkla
    res = []
    for pg in out:
        if not any(pg.symmetric_difference(q).area < 1 for q in res):
            res.append(pg)
    return res


# kiriş bantları (dikey geçişler için): kiriş iz çizgi çiftleri
BEAMS = [box(-5373, -22190, -4772, -22161), box(-5401, -22446, -5124, -22421), box(-5082, -22446, -4767, -22421),
         box(-5379, -22706, -5124, -22681), box(-5082, -22706, -4790, -22681), box(-5107, -22676, -5082, -22446),
         box(-5396, -23036, -4857, -23011), box(-5433, -23036, -5401, -22161),
         Polygon([(-4736, -22411), (-4715, -22195), (-4740, -22195), (-4761, -22409)]),
         Polygon([(-4760, -22656), (-4741, -22461), (-4766, -22459), (-4785, -22654)]),
         Polygon([(-4797, -23036), (-4765, -22706), (-4790, -22706), (-4819, -23006)])]

# baca / şaft kutuları (mimari: her katta)
SHAFTS = [(-5105.0, -22403.0), (-5174.0, -22719.0), (-4794.0, -22716.0)]
SHAFT_BOX = [box(x - 12, y - 12, x + 12, y + 12) for x, y in SHAFTS]

# ------------------------------------------------------------------ armatürler (blok, köşe/orijin, dönüş, sx)
# MTY plan bloğu: y=0 duvar yüzü, +y mahal içi.  Bağlantı noktaları blok koordinatında:
BLK_PTS = {
    'KLOZET1': dict(SO=(0.0, -4.52), PS=(0.0, 20.0)),
    'LAVABO1': dict(SO=(-5.0, -3.52), SC=(5.0, -3.52), PS=(0.0, 15.0)),
    'EVIYE1': dict(SO=(-5.0, -3.52), SC=(5.0, -3.52), PS=(0.0, 15.0)),
    'DUS TEKNESI1': dict(SO=(-10.0, -4.52), SC=(10.0, -4.52), PS=(0.0, 25.0)),
    'CAMASIR MAKINASI1': dict(SO=(0.0, -4.52), PS=(0.0, 20.0)),
    'BULASIK MAKINASI1': dict(SO=(0.0, -4.52), PS=(0.0, 20.0)),
    'KOMBI1': dict(SO=(18.89, -3.52), SC=(28.89, -3.52), HG=(6.0, -3.52), HD=(12.0, -3.52)),
    'YER SUZGECI DN501': dict(PS=(0.0, 0.0)),
}


def bpt(o, rot, p, sx=1.0):
    x, y = p[0] * sx, p[1]
    a = math.radians(rot)
    return (round(o[0] + x * math.cos(a) - y * math.sin(a), 2), round(o[1] + x * math.sin(a) + y * math.cos(a), 2))


FIX = {  # ad: (blok, orijin, dönüş, sx, YB, SB, pis çapı, açıklama)
    'DUS': ('DUS TEKNESI1', (-4908.0, -22411.0), 180, 1, 1.0, 0.7, 50, 'DUŞ'),
    'WC': ('KLOZET1', (-4820.0, -22411.0), 180, 1, 0.5, 2.0, 100, 'WC'),
    'LV': ('LAVABO1', (-4896.0, -22636.0), 0, 1, 0.5, 0.5, 50, 'LAVABO'),
    'CM': ('CAMASIR MAKINASI1', (-4807.0, -22631.0), 0, 1, 1.0, 0.8, 50, 'ÇAMAŞIR MAK.'),
    'EV': ('EVIYE1', (-4896.0, -22646.0), 180, 1, 0.5, 0.8, 50, 'EVİYE'),
    'BM': ('BULASIK MAKINASI1', (-4855.0, -22646.0), 180, 1, 1.0, 0.8, 50, 'BULAŞIK MAK.'),
    'YS': ('YER SUZGECI DN501', (-4855.0, -22480.0), 0, 1, 0.0, 0.8, 50, 'YER SÜZGECİ'),
}
KOMBI = ('KOMBI1', (-5345.0, -22980.0), 90, -1)     # ayna + 90°: baca güneye (dış cephe), bağlantılar doğu yüzünde


def cp(key, which):
    b, o, r, sx = FIX[key][0], FIX[key][1], FIX[key][2], FIX[key][3]
    return bpt(o, r, BLK_PTS[b][which], sx)


def kombi_cp(which):
    b, o, r, sx = KOMBI
    return bpt(o, r, BLK_PTS[b][which], sx)


# pis su kolonları
PK = (-4786.0, -22462.0)        # banyo kolonu (kiriş bandı -22421..-22446 dışında)
MK = (-4944.0, -22655.0)        # mutfak kolonu
# temiz su kolonları + sayaç dolabı (merdiven holü sahanlığı, asansör duvarı önü)
DBK = (-5200.0, -22672.0)       # depo besleme kolonu (şebeke -> çatı deposu)
ADK = (-5146.0, -22672.0)       # ana dağıtım kolonu (çatı deposu -> zemin sayaç grubu)
D2R = (-5176.0, -22672.0)       # 1. kat daire kolonu (zemin sayaç grubundan)
D3R = (-5188.0, -22672.0)       # 2. kat daire kolonu
METER = {1: -5160.0, 2: -5176.0, 3: -5188.0}    # sayaç kollektöründen daire çıkışları
KOLL_Y = -22684.0
SAYAC_BOX = (-5207.0, -22690.0, -5136.0, -22665.0)

# su deposu (mimari çatı planındaki 3.00 m³ depo)
DEPO = (-5011.0, -22665.0, -4871.0, -22526.0)
CATI_KAPAK = (-5199.0, -22665.0, -5119.0, -22585.0)

# ------------------------------------------------------------------ mahal / devre bölgeleri (boru bölgesi = duvardan kenar mesafesi düşülmüş)
ZONES = {
    # ad: (poligon (CCW), giriş köşe indeksi, ilk yön, aralık s, mahal adı, zon no)
    'ODA': ([(-5391, -22419), (-5142, -22419), (-5142, -22290), (-4995, -22290), (-4995, -22202), (-5391, -22202)],
            3, 'a', 15.0, 'ODA', 1),
    'ODA 2': ([(-4939, -22389), (-4772, -22389), (-4772, -22210), (-4939, -22210)], 0, 'a', 10.0, 'ODA 2', 2),
    'BANYO': ([(-4939, -22506), (-4939, -22594), (-4846, -22594), (-4846, -22564), (-4801, -22564), (-4801, -22506)],
              0, 'b', 10.0, 'BANYO + WC', 3),
    'SALON-1': ([(-5008, -22725), (-5008, -22990), (-4840, -22990), (-4840, -22725)], 0, 'a', 10.0, 'SALON + MUTFAK', 4),
    'SALON-2': ([(-5155, -22770), (-5155, -22990), (-5023, -22990), (-5023, -22770)], 3, 'b', 10.0, 'SALON + MUTFAK', 4),
}
ZONE_NO = {'SALON + MUTFAK': 1, 'ODA': 2, 'ODA 2': 3, 'BANYO + WC': 4, 'ANTRE': 5}

# kollektör (antre batı duvarı, sıva üstü dolap) ve ağızları
KOLL_BOX = (-5079.0, -22468.0, -5067.0, -22578.0)
KX = -5067.0
# (devre, gidiş ağzı y, dönüş ağzı y, gidiş şerit x, dönüş şerit x)
PORTS = [
    ('ODA', -22480.0, -22475.0, -4995.0, -5010.0),
    ('ODA 2', -22493.0, -22488.0, -4974.0, -4980.0),
    ('BANYO', -22506.0, -22516.0, None, None),
    ('SALON-1', -22536.0, -22530.0, -5008.0, -4998.0),
    ('SALON-2', -22545.0, -22551.0, -5023.0, -5033.0),
]
INLET = dict(HG=(-22568.0, -5060.0), HD=(-22562.0, -5054.0))
KC_X = -5048.0
COLD_Y = -22638.5          # daire soğuk su ana hattı (holden antreye girer)
HOT_Y = -22644.0           # duvar içi sıcak su hattı
