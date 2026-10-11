"""ezdxf DXF -> mkdwg giriş dosyası."""
import sys
import ezdxf

doc = ezdxf.readfile(sys.argv[1])
out = open(sys.argv[2], "w", encoding="ascii")


def esc(s):
    return "".join(c if ord(c) < 128 else "\\U+%04X" % ord(c) for c in s).replace("\t", " ")


out.write(f"H\t{doc.header.get('$INSUNITS', 4)}\t{doc.header.get('$LTSCALE', 1.0)}\n")
out.write("K\tDASHED\t10\t5\n")
out.write("K\tDASHDOT\t12\t6\n")
for l in doc.layers:
    if l.dxf.name == "0":
        continue
    lt = l.dxf.linetype if l.dxf.linetype in ("DASHED", "DASHDOT") else "CONTINUOUS"
    out.write(f"Y\t{l.dxf.name}\t{abs(l.dxf.color)}\t{lt}\n")


def flat(entities):
    for e in entities:
        t = e.dxftype()
        if t in ("DIMENSION", "INSERT"):
            yield from flat(e.virtual_entities())
        else:
            yield e


n = 0
for e in flat(doc.modelspace()):
    t = e.dxftype(); lay = e.dxf.layer if e.dxf.layer != "0" else "OLCU"
    if t == "LINE":
        out.write(f"L\t{lay}\t{e.dxf.start.x:.2f}\t{e.dxf.start.y:.2f}\t{e.dxf.end.x:.2f}\t{e.dxf.end.y:.2f}\n")
    elif t == "CIRCLE":
        c = e.dxf.center; out.write(f"C\t{lay}\t{c.x:.2f}\t{c.y:.2f}\t{e.dxf.radius:.2f}\n")
    elif t == "SOLID":
        a, b, c = e.dxf.vtx0, e.dxf.vtx1, e.dxf.vtx2
        out.write(f"S\t{lay}\t{a[0]:.2f}\t{a[1]:.2f}\t{b[0]:.2f}\t{b[1]:.2f}\t{c[0]:.2f}\t{c[1]:.2f}\n")
    elif t == "LWPOLYLINE":
        pts = list(e.get_points("xy"))
        w = e.dxf.get("const_width", 0)
        out.write(f"P\t{lay}\t{1 if e.closed else 0}\t{w}\t{len(pts)}\t" + "\t".join(f"{x:.2f}\t{y:.2f}" for x, y in pts) + "\n")
    elif t == "TEXT":
        ins = e.dxf.insert; ap = e.dxf.get("align_point", ins)
        out.write(f"T\t{lay}\t{e.dxf.height}\t{e.dxf.get('rotation', 0)}\t{e.dxf.get('halign', 0)}\t{e.dxf.get('valign', 0)}\t"
                  f"{ins[0]:.2f}\t{ins[1]:.2f}\t{ap[0]:.2f}\t{ap[1]:.2f}\t{esc(e.dxf.text)}\t{e.dxf.get('width', 1.0)}\n")
    elif t == "MTEXT":
        ins = e.dxf.insert
        out.write(f"T\t{lay}\t{e.dxf.char_height}\t0\t0\t0\t{ins[0]:.2f}\t{ins[1]:.2f}\t{ins[0]:.2f}\t{ins[1]:.2f}\t{esc(e.plain_text())}\n")
    elif t in ("HATCH", "POINT"):
        continue
    else:
        print("skip", t, file=sys.stderr); continue
    n += 1
print("written", n, file=sys.stderr)
