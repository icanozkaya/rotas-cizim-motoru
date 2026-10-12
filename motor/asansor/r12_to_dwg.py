"""R12 DXF (asansör çizici) -> R2018 DXF -> ACadSharp DWG (AC1032)."""
import sys, subprocess, ezdxf
from ezdxf.addons import Importer
src, dwg = sys.argv[1], sys.argv[2]
s = ezdxf.readfile(src)
d = ezdxf.new('R2018', setup=True)
d.header['$INSUNITS'] = 5
im = Importer(s, d)
im.import_modelspace(); im.import_tables('*'); im.finalize()
tmp = dwg[:-4] + '_R2018.dxf'
d.saveas(tmp)
out = subprocess.run(['/home/claude/acad_build/rotasdwg/bin/Release/net10.0/rotasdwg', tmp, dwg, 'AC1032'], capture_output=True, text=True)
print(out.stdout.strip().split('\n')[0], out.stderr[:200])
import os; os.remove(tmp)
