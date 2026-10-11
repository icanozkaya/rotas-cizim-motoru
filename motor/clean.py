import re
def clean(s):
    s = re.sub(r'\\U\+([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1),16)), s)
    s = re.sub(r'\\[ACcFfHhQqTtWwpi][^;\\{}]*;', '', s)
    s = s.replace('\\P',' / ').replace('\\L','').replace('\\l','').replace('\\O','').replace('\\o','')
    s = re.sub(r'\\S([^;]*)\^([^;]*);', r'\1/\2', s)
    s = re.sub(r'[{}]', '', s).replace('%%C','Ø').replace('%%c','Ø').replace('%%U','').replace('%%D','°').replace('%%d','°').replace('%%%','%')
    s = re.sub(r'\^J',' ', s)
    return re.sub(r'\s+',' ',s).strip()
