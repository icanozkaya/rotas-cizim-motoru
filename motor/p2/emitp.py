"""p2 projeleri: R pickle -> DXF + DWG (+ geri okuma kontrolü)"""
import sys, pickle, runpy, subprocess, os
sys.path.insert(0, '/home/claude/nb'); sys.path.insert(0, '/home/claude/nb/p2')
import design, gp, gklima
src, base = sys.argv[1], sys.argv[2]
R, FR = pickle.load(open(src, 'rb'))[:2]
design.LAYERS.update(gp.EXTRA_LAYERS)
design.LAYERS.update({'MIMARI': (8, 'CONTINUOUS'), 'MTY-PEX-BORU': (1, 'CONTINUOUS'), 'MTY-KOLLETOR': (7, 'CONTINUOUS'),
                      'MTY-ISIKAYBIMAHAL': (2, 'CONTINUOUS'), 'STM-ISITMA-CAP': (41, 'CONTINUOUS'),
                      'MTY-ISITMA-GIDIS-BORU': (10, 'CONTINUOUS'), 'MTY-ISITMA-DONUS-BORU': (30, 'ISITMA DONUS HATTI'),
                      'MTY-PISSU-BORU-TAVANDAN': (6, 'PISSU HATTI'), 'MTY-PIS-SU-BORUSU': (6, 'PIS'),
                      'MTY-SICAKSU-BORU': (1, 'BASMA HATTI'), 'MTY-YAGMUR-BORUSU': (3, 'YAGMUR HATTI')})
tmp = '/tmp/claude-0/p2/_emit.pkl'
pickle.dump((R, FR, None), open(tmp, 'wb'))
txt = base + '.txt'
sys.argv = ['emit.py', base + '.dxf', txt, tmp]
runpy.run_path('/home/claude/nb/emit.py', run_name='__main__')
if os.path.exists(base + '.dwg'):
    os.remove(base + '.dwg')
env = dict(os.environ, LD_LIBRARY_PATH='/usr/local/lib')
RD = '/home/claude/acad_build/rotasdwg/bin/Release/net10.0/rotasdwg'
ok = False
if os.path.exists(RD):     # ACadSharp ile AutoCAD 2018 (AC1032) DWG - tercih edilen yol
    r = subprocess.run([RD, base + '.dxf', base + '.dwg', 'AC1032'], capture_output=True, text=True)
    print('ACadSharp', r.returncode, r.stdout.strip()[-200:], r.stderr[-300:])
    ok = r.returncode == 0 and os.path.exists(base + '.dwg')
if not ok:                 # yedek: LibreDWG tabanlı mkdwg (R2000)
    if os.path.exists(base + '.dwg'):
        os.remove(base + '.dwg')
    r = subprocess.run(['/home/claude/dwgtools/mkdwg', txt, base + '.dwg'], env=env, capture_output=True, text=True)
    print('mkdwg', r.returncode, r.stdout[-200:], r.stderr[-300:])
chk = '/tmp/claude-0/p2/_chk.dxf'
if os.path.exists(chk):
    os.remove(chk)
r = subprocess.run(['dwg2dxf', '-y', '-o', chk, base + '.dwg'], env=env, capture_output=True, text=True)
n = open(chk, encoding='utf-8', errors='ignore').read().count('\nAcDbEntity') if os.path.exists(chk) else -1
print('geri okuma varlık sayısı', n, os.path.getsize(base + '.dwg'))
os.remove(txt)
