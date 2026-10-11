import pickle, sys
sys.path.insert(0, '/home/claude/nb')
import cad
from cad import *
import cg_build as B
import cg_heat

R = cad.R
Y0, Y1 = B.SHEET_Y
HY0, HY1 = Y0 + B.HDY, Y1 + B.HDY

# --- mimari (tek kalem)
for k in range(4):
    B.put_arch(B.arch_items(k * 1250), 0, 0)
for k in range(3):
    B.put_arch(B.arch_items(k * 1250, furn=False), 0, B.HDY)
    # ısıtmada mutfak/banyo tefrişini de göster (yalnızca ıslak hacim armatürleri)
# --- sıhhi
for i in range(3):
    B.sihhi_kat(i)
B.zemin_extra()
B.cati_plan()
# --- ısıtma
HEAT = []
for i, (key, name, fdx, dno) in enumerate(B.FLOORS):
    c = cg_heat.calc(key)
    losses = {(key, nm): v['Q'] for nm, v in c.items()}
    res, tot = B.isitma_kat(i, losses)
    HEAT.append((res, tot))
# --- şemalar
B.sihhi_sema(-695, Y0)
B.isitma_sema(-1945, HY0, HEAT)
# --- antet, notlar, lejant
B.antet(-7900, Y1 - 50)
B.notlar(-7900, Y1 - 930)
B.lejant(-7900, HY1 - 80)
# yerden ısıtma özet tablosu
x, y = -6750, HY1 - 120
T((x, y), 'YERDEN ISITMA ÖZETİ', 16, B.YZ, 'L')
y -= 30
for k, (res, tot) in enumerate(HEAT):
    T((x, y), '%s - DAİRE %d : TOPLAM %.1f W  (%.0f kcal/h)  KOMBİ 24 kW' % (B.FLOORS[k][1], k + 1, tot, tot * 0.86), 10, B.YZ, 'L')
    y -= 18
    for d in res:
        T((x + 20, y), 'P%d  %-16s  %s  %.1f W  %.2f m' % (d['port'], d['room'], d['zl'], d['W'], d['L']), 9, B.YZ, 'L')
        y -= 15
    y -= 10
# --- paftalar
fr = []
names = ['ZEMİN KAT SIHHİ TESİSAT PLANI', '1. KAT SIHHİ TESİSAT PLANI', '2. KAT SIHHİ TESİSAT PLANI', 'ÇATI PLANI (HAVALIKLAR)']
for k in range(4):
    a, b = B.sheet_x(k)
    fr.append(((a, Y0, b, Y1), names[k], '1/50'))
fr.append(((-695, Y0, 1305, Y1), 'SIHHİ TESİSAT KOLON ŞEMASI', 'ÖLÇEKSİZ'))
for k in range(3):
    a, b = B.sheet_x(k)
    fr.append(((a, HY0, b, HY1), ['ZEMİN', '1.', '2.'][k] + (' KAT' if k == 0 else ' KAT') + ' YERDEN ISITMA PLANI', '1/50'))
fr.append(((-1945, HY0, 55, HY1), 'YERDEN ISITMA KOLON ŞEMASI', 'ÖLÇEKSİZ'))
fr.append(((-7950, Y0, -5695, Y1), 'ANTET VE PROJE NOTLARI', 'ÖLÇEKSİZ'))
fr.append(((-7950, HY0, -5695, HY1), 'LEJANT VE ISITMA ÖZETİ', 'ÖLÇEKSİZ'))
for (a, b, c, d), t, o in fr:
    B.frame(a, b, c, d, t, o)
pickle.dump((cad.R, fr, HEAT), open('/tmp/claude-0/cg_recs.pkl', 'wb'))
print('records', len(cad.R))
for k, (res, tot) in enumerate(HEAT):
    print(k, round(tot, 1), [(d['port'], d['room'], round(d['W']), round(d['L'], 1)) for d in res])
