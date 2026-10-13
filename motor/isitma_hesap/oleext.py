import sys, struct, olefile
def ext(path, pre):
    L=open(path,encoding='utf-8',errors='replace').read().split('\n')
    i=0;n=0;res=[]
    while i<len(L):
        if L[i].strip()=='OLE2FRAME' and L[i-1].strip()=='0':
            j=i+1; data=[]; lay=''
            while not (L[j].strip()=='0' and (j-i)%2==1):
                c=L[j].strip(); v=L[j+1].strip()
                if c=='310': data.append(v)
                if c=='8': lay=v
                j+=2
            b=bytes.fromhex(''.join(data))
            pos=struct.unpack('<12d', b[2:98]) if len(b)>98 else None
            k=b.find(b'\xd0\xcf\x11\xe0')
            fn=f'{pre}{n}.cfb'; open(fn,'wb').write(b[k:])
            try:
                o=olefile.OleFileIO(fn); c=o.openstream('\x01CompObj').read()
                cls=[s for s in c.split(b'\x00') if len(s)>3][2].decode('cp1254','replace')
                streams=['/'.join(s) for s in o.listdir()]
            except Exception as ex: cls=str(ex); streams=[]
            res.append((n,lay,[round(x) for x in pos[:2]+pos[6:8]] if pos else None,cls,streams))
            n+=1; i=j
        else: i+=1
    return res
for r in ext(sys.argv[1], sys.argv[2]): print(r)
