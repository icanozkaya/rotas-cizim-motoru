import sys, ezdxf, os
sys.path.insert(0,'/home/claude/rotas-cizim-motoru/motor/kontrolor')
import kirp
out='/home/claude/rotas-cizim-motoru/kutuphane/arastirma/kontrol_png/sihhi_plan_tur2_uretici'; os.makedirs(out,exist_ok=True)
A=kirp.Cizici(ezdxf.readfile('/home/claude/rotas-cizim-motoru/proje/denemeler/sihhi2/NB_SIHHI_KAT_PLANLARI.dxf'))
B=kirp.Cizici(ezdxf.readfile('/tmp/claude-0/uu/new_block.dxf'))
W={'Z_11_wcbanyo_D3_P8':(252960,-442340,253270,-441980),'Z_12_dus_balkon_P9':(252600,-442090,252960,-441810),
'Z_13_banyo_wclvb_D1_P2_P3':(253590,-442880,253980,-442370),'Z_14_mutfak_P1_P4':(253270,-443710,253890,-442990),
'Z_15_banyo_wclvb_D2_P5_P6':(253170,-442880,253560,-442370),'Z_16_giris_hol_D3':(252960,-442150,253840,-441490),
'Z_D3_sol_hol_dus_yolu':(252700,-442300,253300,-441800),
'K1_merdiven_yani_D6':(255590,-442900,256020,-442250),'K1_wcbanyo_D5_P8':(254994,-442340,255304,-441980),
'K2_D8_mutfak_P7':(257560,-441900,257860,-441500),'K2_banyo_wclvb_D9_P2_P3':(257670,-442880,258060,-442370),
'K2_banyo_wclvb_D7_P5_P6':(257250,-442880,257640,-442370),'CATI':(258656,-444050,260714,-441150)}
for ad,w in W.items():
    a=out+'/'+ad+'_a.png'; b=out+'/'+ad+'_b.png'
    A.kirp(w,a,baslik=ad,genislik_in=6.5,dpi=110); B.kirp(w,b,baslik='ref '+ad,genislik_in=6.5,dpi=110)
    kirp.yan_yana(a,b,out+'/'+ad+'.png'); os.remove(a); os.remove(b)
print('ok')
