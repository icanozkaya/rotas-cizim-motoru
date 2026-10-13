# -*- coding: utf-8 -*-
"""ISI_KAYBI_HESABI.xls (ısı kaybı hesap cetveli) ve RADYATÖR SEÇİMİ xlsx okuyucu."""
import re, xlrd, openpyxl

def _f(v):
    try: return float(v)
    except Exception: return None

def isi_kaybi(path):
    s = xlrd.open_workbook(path).sheet_by_index(0)
    rooms, cur = [], None
    for r in range(s.nrows):
        v = s.row_values(r)
        c0 = str(v[0]).strip(); c3 = str(v[3]).strip()
        if c0 == '' and re.match(r'^(1-2-3-4-5|Ç|Z|B|\d)', c3) and '(' in c3:
            m = re.match(r'^((?:1-2-3-4-5|Ç|Z|B)\s*\d+)\s+(.+?)\s*\((\-?\d+)°C\)', c3)
            cur = dict(no=m.group(1), ad=m.group(2), ti=float(m.group(3)), el=[], qt=None, qs=None, top=None)
            rooms.append(cur); continue
        if cur is None: continue
        if c0 and _f(c0) is None and c0 not in ('İşaret', 'Yapı Bil.', 'ISI KAYBI HESAP CETVELİ') and _f(v[16]) is not None:
            cur['el'].append(dict(k=c0, L=_f(v[3]), H=_f(v[4]), Atop=_f(v[5]), n=_f(v[6]), Ac=_f(v[7]), A=_f(v[8]), U=_f(v[9]),
                                  dT=_f(v[10]), Q=_f(v[11]), Zd=_f(v[12]), Zw=_f(v[13]), Zh=_f(v[14]), Z=_f(v[15]), Qt=_f(v[16])))
        elif str(v[4]).strip().startswith('Qs'):
            cur['qs'] = dict(L=_f(v[5]), a=_f(v[6]), Hk=_f(v[7]), dT=_f(v[8]), R=_f(v[9]), Ze=_f(v[10]), Q=_f(v[16]))
        elif _f(c0) is not None: continue
        elif c0 == '' and _f(v[16]) is not None and all(str(x).strip() == '' for x in v[:16]):
            if cur['qt'] is None: cur['qt'] = _f(v[16])
            elif cur['top'] is None: cur['top'] = _f(v[16])
    return rooms

def radyator(path):
    w = openpyxl.load_workbook(path, data_only=True).active
    rows = list(w.iter_rows(values_only=True))
    genel = dict(yer=rows[6][0], tdis=rows[6][2], tg=rows[6][5], td=rows[6][8])
    R = []
    for r in rows[10:]:
        if r[0] is None: continue
        R.append(dict(no=str(r[0]), ad=r[1], ti=r[2], q=r[4], boy=r[5], model=r[6], ver=r[7], adet=r[8], tip=r[9]))
    return genel, R

def carpan(no):
    return 5 if no.startswith('1-2-3-4-5') else 1

def kat(no):
    return 'NORMAL KATLAR (1-2-3-4-5)' if no.startswith('1-2-3-4-5') else ('ZEMİN KAT' if no.startswith('Z') else ('ÇATI KATI' if no.startswith('Ç') else 'DİĞER'))
