"""Doğrulama (commit edilmez): kontrolörün MTEXT kutusunu sütun genişliği yerine satırların gerçek yazı genişliğiyle ölçerek
T07'yi yeniden hesaplar. Kullanım: python3 -I bu_dosya <dxf> <rapor.md>"""
import sys, runpy
sys.path.insert(0, '/home/claude/rotas-cizim-motoru/motor/kontrolor')
sys.path.insert(0, '/home/claude/rotas-cizim-motoru/motor/deneme/denetim')
import kutu
from ezdxf.fonts import fonts
_eski = kutu.mtext_kutusu
def mtext_kutusu(e):
    pg = _eski(e)
    try:
        h = e.dxf.get('char_height', 2.5) or 2.5
        f = fonts.make_font('arial.ttf', h)
        satir = e.plain_text().split('\n')
        w = max(f.text_width(x) for x in satir)
        if pg is None or w <= 0:
            return pg
        from shapely.geometry import box
        from shapely.affinity import scale
        x0, y0, x1, y1 = pg.bounds
        ap = e.dxf.get('attachment_point', 1); col = (ap - 1) % 3
        if col == 0: return box(x0, y0, min(x1, x0 + w), y1)
        if col == 2: return box(max(x0, x1 - w), y0, x1, y1)
        c = (x0 + x1) / 2; return box(c - w / 2, y0, c + w / 2, y1)
    except Exception:
        return pg
kutu.mtext_kutusu = mtext_kutusu
sys.argv = ['kontrolor.py', sys.argv[1], '--mimari', '/home/claude/rotas-cizim-motoru/ornekler/new_block.dxf.xz', '--rapor', sys.argv[2]]
runpy.run_path('/home/claude/rotas-cizim-motoru/motor/kontrolor/kontrolor.py', run_name='__main__')
