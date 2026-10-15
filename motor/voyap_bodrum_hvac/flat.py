import ezdxf, pickle, sys, math
from ezdxf import path as zpath
def flatten(src):
    d=ezdxf.readfile(src); m=d.modelspace(); segs=[]; texts=[]; circ=[]
    def walk(ents, layer_over=None, depth=0):
        for e in ents:
            t=e.dxftype(); L=e.dxf.get('layer','0')
            if layer_over and L=='0': L=layer_over
            try:
                if t=='INSERT':
                    if e.dxf.name not in d.blocks: continue
                    try: walk(list(e.virtual_entities()), L, depth+1)
                    except Exception:
                        pass
                elif t=='LINE':
                    segs.append((L,(e.dxf.start.x,e.dxf.start.y),(e.dxf.end.x,e.dxf.end.y)))
                elif t in('LWPOLYLINE','POLYLINE','ARC','CIRCLE','ELLIPSE','SPLINE'):
                    p=zpath.make_path(e); pts=list(p.flattening(2.0))
                    for a,b in zip(pts,pts[1:]): segs.append((L,(a.x,a.y),(b.x,b.y)))
                    if t=='CIRCLE': circ.append((L,e.dxf.center.x,e.dxf.center.y,e.dxf.radius))
                elif t in('TEXT','MTEXT'):
                    s=e.plain_text() if t=='MTEXT' else e.dxf.text
                    h=e.dxf.char_height if t=='MTEXT' else e.dxf.height
                    texts.append((L,e.dxf.insert.x,e.dxf.insert.y,s,h))
            except Exception as ex: pass
    walk(list(m))
    return dict(segs=segs,texts=texts,circ=circ)
if __name__=='__main__':
    F=flatten(sys.argv[1]); pickle.dump(F,open(sys.argv[2],'wb')); print(len(F['segs']),len(F['texts']))
