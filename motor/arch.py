"""Mimariyi temizle: fazlalıkları at, kalanları tek kalem (MIMARI, renk 8) olarak kayda çevir."""
import pickle, re, sys
sys.path.insert(0, '/home/claude/nb')
from clean import clean

ARCH = 'MIMARI'

S = {'VAZ': (71102, -11094, 74217, -8094),
     'A-BOD': (74217, -11094, 78667, -8094), 'A-ZEM': (78667, -11094, 83117, -8094),
     'A-K1': (83117, -11094, 87567, -8094), 'A-K2': (87567, -11094, 92017, -8094),
     'A-CATI': (92017, -11094, 96467, -8094),
     'B-ZEM': (73267, -14594, 77717, -11594), 'B-K1': (77717, -14594, 82167, -11594),
     'B-K2': (82167, -14594, 86617, -11594), 'B-CATI': (86617, -14594, 91067, -11594)}

PLAN_GEOM = {'A-WALL', 'S-COLS', 'A-DOOR', 'Kapi_Pencere', 'A-DETL-GENF', 'S-STRS', 'A-GENM',
             'mobilya', 'rtm-tefris vitrifiye', 'TEFRIS', 'Q-CASE'}
FURN = {'mobilya', 'rtm-tefris vitrifiye', 'TEFRIS'}
ROOF_GEOM = {'A-WALL', 'A-GENM', 'MAHYA', 'SAÇAK', 'A-DETL-GENF', '0', 'A-FLOR'}
VAZ_GEOM = {'A-WALL', 'A-FLOR', 'A-GENM', 'A-DETL-GENF', 'MAHYA', 'PARSEL_ALN_YENI', 'TK_PARSEL', 'ŞEV',
            '0', 'Kot', 'YAZI S', 'otopark', 'S-STRS'}


def pt(k, d):
    return (d[0], d[1]) if k == 'C' else d[0]


def keep_text(sheet, l, t):
    if not t.strip() or '{' in t or '\\' in t:
        return None
    if sheet in ('VAZ',):
        if l == 'YAZI S':
            return t
        return None
    if sheet.endswith('CATI'):
        if l == 'YAZI' and ('DEPO' in t.upper() or 'm³' in t or 'm3' in t):
            return t
        if l == 'rtm-mhl-yazı-malzeme' and 'eğim' in t.lower():
            return t
        if l == 'A-AREA-IDEN' and not t.startswith(('Döş', '(')):
            return t
        return None
    if l == 'A-AREA-IDEN':
        if t.startswith(('Döş', '(')):
            return None
        return t
    if l == 'A-GENM':
        return t
    return None


def build(flat):
    """Dönüş: {sheet: [(kind, data)]} temizlenmiş mimari (kaynak koordinatlarında)."""
    out = {s: [] for s in S}
    for k, l, d, p in flat:
        x, y = pt(k, d)
        sh = None
        for s, (a, b, c, e) in S.items():
            if a < x < c and b < y < e:
                sh = s; break
        if sh is None:
            continue
        if k == 'T':
            t = keep_text(sh, l, clean(d[1]))
            if t:
                out[sh].append(('T', (d[0], t.replace('\\P', ' '), d[2]), l))
            continue
        if sh == 'VAZ':
            ok = l in VAZ_GEOM
        elif sh.endswith('CATI'):
            ok = l in ROOF_GEOM
        else:
            ok = l in PLAN_GEOM
        if ok:
            out[sh].append((k, d, l))
    return out


if __name__ == '__main__':
    flat = pickle.load(open('/tmp/claude-0/nb_flat.pkl', 'rb'))
    o = build(flat)
    pickle.dump(o, open('/tmp/claude-0/arch_clean.pkl', 'wb'))
    for s in o:
        print(s, len(o[s]))
