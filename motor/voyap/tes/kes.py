# -*- coding: utf-8 -*-
"""Köprü: motor/ekipman.py (cad.R kayıt tabanlı gerçek ölçülü plan/görünüş/kesit ekipman çizimleri) -> ezdxf modelspace."""
import sys, math
sys.path.append('/home/claude/nb')
import cad, ekipman
from lib import *

AL = {'L': TA.BOTTOM_LEFT, 'C': TA.BOTTOM_CENTER, 'R': TA.BOTTOM_RIGHT, 'ML': TA.MIDDLE_LEFT, 'MC': TA.MIDDLE_CENTER,
      'MR': TA.MIDDLE_RIGHT, 'TL': TA.TOP_LEFT, 'TC': TA.TOP_CENTER, 'TR': TA.TOP_RIGHT, 'BC': TA.BOTTOM_CENTER,
      'BL': TA.BOTTOM_LEFT, 'BR': TA.BOTTOM_RIGHT}


def ciz(fn, o, k=1.0, lay=None, yazi=True, *a, rot=0.0, **kw):
    """fn(view-args...) kayıtlarını o noktasına k ölçeğiyle (ve rot derece döndürerek) aktar. lay: tüm kayıtlar bu katmana"""
    cad.R.clear()
    ca, sa = math.cos(math.radians(rot)) * k, math.sin(math.radians(rot)) * k
    cad.push((ca, -sa, o[0], sa, ca, o[1]))
    try:
        fn(*a, **kw)
    finally:
        cad.pop()
    for r in cad.R:
        t = r[0]; ly = lay or r[1]
        if t == 'L': L(r[2], r[3], ly)
        elif t == 'P': PL(r[2], ly, closed=r[3])
        elif t == 'C': C(r[2], r[3], ly)
        elif t == 'W': MASK(r[2])
        elif t == 'S': PL([r[2], r[3], r[4]], ly, closed=True)
        elif t == 'T' and yazi:
            T(r[2][0], r[2][1], r[3], max(r[4], 4.0), ly, AL.get(r[6], TA.BOTTOM_LEFT), r[5])
    n = len(cad.R); cad.R.clear()
    return n
