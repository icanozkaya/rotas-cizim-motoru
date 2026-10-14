import ezdxf, sys, os, pickle, math
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, LineweightPolicy, ColorPolicy, BackgroundPolicy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SRC='/tmp/claude-0/ref/new_block.dxf'
OUT='/home/claude/rotas-cizim-motoru/kutuphane/arastirma/referans/sihhi'
os.makedirs(OUT,exist_ok=True)
_doc=None; _bb=None
def load():
    global _doc,_bb
    if _doc is None:
        _doc=ezdxf.readfile(SRC)
        cache='/tmp/claude-0/ref/bbox.pkl'
        if os.path.exists(cache):
            _bb=pickle.load(open(cache,'rb'))
        else:
            _bb={}
            from ezdxf import bbox
            for e in _doc.modelspace():
                t=e.dxftype()
                try:
                    if t=='LINE':
                        a,b=e.dxf.start,e.dxf.end; _bb[e.dxf.handle]=(min(a.x,b.x),min(a.y,b.y),max(a.x,b.x),max(a.y,b.y))
                    elif t=='INSERT':
                        p=e.dxf.insert; s=max(abs(e.dxf.xscale),abs(e.dxf.yscale))
                        m=400*s if e.dxf.name in ('SIHHİ DETAYLAR','MTY-SIHHİ DETAYLAR','hidrofor') else 120*s
                        _bb[e.dxf.handle]=(p.x-m,p.y-m,p.x+m,p.y+m)
                    elif t in ('TEXT','MTEXT'):
                        p=e.dxf.insert; _bb[e.dxf.handle]=(p.x-300,p.y-100,p.x+300,p.y+100)
                    else:
                        ext=bbox.extents([e],fast=True)
                        if ext.has_data:
                            _bb[e.dxf.handle]=(ext.extmin.x,ext.extmin.y,ext.extmax.x,ext.extmax.y)
                        else:
                            _bb[e.dxf.handle]=None
                except Exception:
                    _bb[e.dxf.handle]=None
            pickle.dump(_bb,open(cache,'wb'))
    return _doc,_bb

def crop(name,x1,y1,x2,y2,px=2200,skip_layers=(),only_layers=None,bg='#FFFFFF'):
    doc,bb=load()
    msp=doc.modelspace()
    ents=[]
    for e in msp:
        if e.dxf.layer in skip_layers: continue
        if only_layers and e.dxf.layer not in only_layers: continue
        b=bb.get(e.dxf.handle)
        if b is None: ents.append(e); continue
        if b[2]<x1 or b[0]>x2 or b[3]<y1 or b[1]>y2: continue
        ents.append(e)
    w=x2-x1; h=y2-y1
    fig=plt.figure(figsize=(px/100, px*h/w/100), dpi=100)
    ax=fig.add_axes([0,0,1,1]); ax.set_facecolor(bg); fig.patch.set_facecolor(bg)
    ctx=RenderContext(doc)
    cfg=Configuration(lineweight_policy=LineweightPolicy.ABSOLUTE, lineweight_scaling=1.0, min_lineweight=0.25,
                      background_policy=BackgroundPolicy.CUSTOM, custom_bg_color=bg, custom_fg_color='#000000',
                      color_policy=ColorPolicy.COLOR)
    be=MatplotlibBackend(ax)
    Frontend(ctx,be,config=cfg).draw_entities(ents)
    ax.set_xlim(x1,x2); ax.set_ylim(y1,y2); ax.set_aspect('equal'); ax.axis('off')
    out=os.path.join(OUT,name+'.png')
    fig.savefig(out,dpi=100,facecolor=bg)
    plt.close(fig)
    print('wrote',out,len(ents),'entities')
    return out


# ---- kırpma listesi: kutuphane/arastirma/referans/sihhi/*.png (ad, x1, y1, x2, y2, piksel) ----
KIRP=[
 ('01_zemin_plan_genel',252513,-444050,254578,-441150,2000),
 ('02_sema_genel',260714,-444050,268132,-441150,3000),
 ('03_sema_sayac_grubu_sebeke',260760,-443330,261420,-443100,1800),
 ('04_sema_depo',260900,-442110,261460,-441720,1600),
 ('05_sema_daire_D1_zemin',265150,-443400,267520,-442830,2600),
 ('06_sema_daire_D3_zemin',261480,-443400,263420,-442830,2400),
 ('07_sema_kolon_ust_etiketler',261400,-442480,267520,-441900,2600),
 ('08_rogar_semasi',264000,-443980,265400,-443600,2000),
 ('09_yagmur_semasi',267460,-443720,268100,-441940,1400),
 ('10_temel_plan_genel',250042,-444050,252513,-441150,1800),
 ('11_z_wcbanyo_D3_P8',252960,-442340,253270,-441980,1600),
 ('12_z_dus_balkon_P9_YB8',252600,-442090,252960,-441810,1600),
 ('13_z_banyo_wclvb_D1_P2_P3',253590,-442880,253980,-442370,1600),
 ('14_z_mutfak_kombi_D1_D2_P1_P4',253270,-443710,253890,-442990,1800),
 ('15_z_banyo_wclvb_D2_P5_P6',253170,-442880,253560,-442370,1600),
 ('16_z_giris_hol_D3_ana_hat',252960,-442150,253840,-441490,2000),
 ('17_z_balkon_suzgec_YB2_YB3',253000,-443700,254120,-443400,2000),
 ('18_cati_plan_genel',258656,-444050,260714,-441150,1600),
 ('19_detay_paftasi_genel',268132,-444050,270197,-441150,1600),
 ('20_antet_yerlesim',247352,-444050,250042,-441150,1600),
 ('21_1kat_plan_genel',254578,-444050,256617,-441150,2000),
 ('22_1kat_merdiven_yani_banyo_D4_P2_P3',255590,-442900,256020,-442350,1600),
 ('23_1kat_wcbanyo_D5_P8',254994,-442340,255304,-441980,1600),
 ('24_2kat_plan_genel',256617,-444050,258656,-441150,2000),
 ('25_etiket_yakin_pissu_O100_23SB',253715,-442640,253835,-442520,1200),
 ('26_etiket_yakin_temizsu_1inc_MB',253030,-442090,253150,-441970,1200),
 ('27_kolon_no_yakin_P8_ve_kolon',253020,-442330,253120,-442230,1200),
 ('28_sema_kombi_D_etiketi_yakin',267050,-443060,267480,-442900,1600),
 ('29_sema_armatur_grubu_yakin_D1_banyo',265180,-443340,265980,-442980,2000),
 ('30_sema_kolon_dibi_TK_rogar_yakin',266850,-443400,267020,-443180,1200),
 ('31_1kat_D4_giris_ve_temizsu_hol',255600,-443200,256300,-442350,1800),
]

if __name__=='__main__':
    for c in KIRP: crop(*c[:5], px=c[5])
