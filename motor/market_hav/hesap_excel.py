# -*- coding: utf-8 -*-
"""market_hav/hesap_excel.py — ISI KAZANCI (m³ yöntemi) + ISI GERİ KAZANIMLI KLİMA SANTRALİ DX BATARYA HESABI (Excel, formüllü).

Girdi : proje/market_havalandirma/girdi/zonlar.json (zonlar.py: mahal alanları, yükseklik, kabuk boyları)
Çıktı : proje/market_havalandirma/ISI_KAZANCI_VE_KLIMA_SANTRALI_HESABI.xlsx

Sayfalar: VARSAYIMLAR (sarı hücreler değiştirilebilir) | MAHALLER | KS HESABI | CİHAZ LİSTESİ | KONTROL
Bütün sonuçlar formüldür; varsayımlar değişince yeniden hesaplanır.
"""
import json
import os

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BURASI = os.path.dirname(os.path.abspath(__file__))
DEPO = os.path.abspath(os.path.join(BURASI, '..', '..'))
PROJE = os.path.join(DEPO, 'proje', 'market_havalandirma')
ZON = os.path.join(PROJE, 'girdi', 'zonlar.json')
CIKTI = os.path.join(PROJE, 'ISI_KAZANCI_VE_KLIMA_SANTRALI_HESABI.xlsx')

F = 'Arial'
SARI = PatternFill('solid', fgColor='FFFF00')
BASLIK = PatternFill('solid', fgColor='D9E1F2')
TOPLAM = PatternFill('solid', fgColor='E2EFDA')
INCE = Side(style='thin', color='808080')
KENAR = Border(left=INCE, right=INCE, top=INCE, bottom=INCE)
MAVI = Font(name=F, size=10, color='0000FF')
SIYAH = Font(name=F, size=10)
KALIN = Font(name=F, size=10, bold=True)
YESIL = Font(name=F, size=10, color='008000')
KS = ['KS-1', 'KS-2', 'KS-3', 'KS-4']


def hucre(ws, ref, deger, font=SIYAH, fill=None, fmt=None, hiz='left', kenar=True):
    c = ws[ref]
    c.value = deger
    c.font = font
    if fill:
        c.fill = fill
    if fmt:
        c.number_format = fmt
    c.alignment = Alignment(horizontal=hiz, vertical='center', wrap_text=False)
    if kenar:
        c.border = KENAR
    return c


def varsayimlar(wb):
    ws = wb.active
    ws.title = 'VARSAYIMLAR'
    ws['A1'] = 'ISI KAZANCI (m³ YÖNTEMİ) VE KLİMA SANTRALİ HESABI — VARSAYIMLAR'
    ws['A1'].font = Font(name=F, size=13, bold=True)
    ws['A2'] = 'Sarı hücreler değiştirilebilir girdilerdir (mavi yazı). Diğer sayfalar bu değerlere formülle bağlıdır.'
    ws['A2'].font = Font(name=F, size=9, italic=True)
    satir = [
        # ad, değer, birim, açıklama/kaynak, isim
        ('TASARIM ŞARTLARI', None, None, None, None),
        ('Yaz dış hava kuru termometre', 35, '°C', 'Adapazarı yaz tasarım değeri (tesisat kütüphanesi, KK listesi)', 'To_yaz'),
        ('Yaz dış hava yaş termometre', 25, '°C', 'Adapazarı', 'Twb_yaz'),
        ('Yaz iç hava sıcaklığı', 26, '°C', 'market / ticari alan', 'Ti_yaz'),
        ('Yaz iç bağıl nem', 0.50, '-', '', 'RH_yaz'),
        ('Kış dış hava sıcaklığı', -3, '°C', 'Sakarya / Adapazarı kış tasarım (TS 2164)', 'To_kis'),
        ('Kış dış bağıl nem', 0.90, '-', '', 'RH_kis'),
        ('Kış iç hava sıcaklığı', 20, '°C', '', 'Ti_kis'),
        ('Atmosfer basıncı', 101.325, 'kPa', 'deniz seviyesine yakın (Adapazarı ≈ 30 m)', 'Patm'),
        ('KLİMA SANTRALİ', None, None, None, None),
        ('Santral hava debisi (her biri)', 40000, 'm³/h', 'kullanıcının havalandırma projesindeki değer (KS-1…KS-4)', 'V_ks'),
        ('Hava yoğunluğu', 1.20, 'kg/m³', '', 'rho'),
        ('Havanın özgül ısısı', 1.006, 'kJ/kg·K', '', 'cp'),
        ('Buharlaşma ısısı (0 °C)', 2501, 'kJ/kg', '', 'hfg'),
        ('Plakalı ısı geri kazanım duyulur verimi', 0.75, '-', 'ErP 2018 (EU 1253/2014) en az %73', 'eps'),
        ('Üfleme fanı elektrik gücü (hava akımında)', 17.0, 'kW', '40.000 m³/h × ~1000 Pa toplam / η 0,65 — fan ısısı bataryadan sonra havaya geçer', 'P_fan'),
        ('Kişi başı taze hava', 7.0, 'l/s·kişi', 'TS EN 16798-1 Kategori II', 'q_kisi'),
        ('Alan başı taze hava', 0.7, 'l/s·m²', 'TS EN 16798-1 az kirletici bina', 'q_alan'),
        ('Batarya emniyet payı', 1.10, '-', 'seçim = hesap × emniyet', 'emn'),
        ('Dış ünite ısıtma kapasitesi düşümü (−3 °C)', 0.80, '-', 'ısı pompası −3 °C dış havada nominal ısıtmanın ~%80’i', 'dus'),
        ('ELEKTRİK', None, None, None, None),
        ('Dönüş/egzoz fanı gücü / üfleme fanı gücü', 0.80, '-', 'dönüş tarafı dış statik basınç daha düşük', 'k_donus'),
        ('Santral otomasyon + damper motorları', 0.50, 'kW', 'santral başına (varsayım)', 'P_oto'),
        ('Dış ünite soğutma verimi EER (35 °C dış hava)', 3.0, '-', 'hava kaynaklı DX ısı pompası (varsayım, üretici değeriyle değiştir)', 'EER'),
        ('Dış ünite ısıtma verimi COP (−3 °C dış hava)', 2.6, '-', 'varsayım, üretici değeriyle değiştir', 'COP'),
        ('Besleme gerilimi (3 faz)', 400, 'V', '3~ 50 Hz', 'U_v'),
        ('Güç faktörü — EC fanlı santral', 0.95, '-', '', 'cos_ks'),
        ('Güç faktörü — inverter dış ünite', 0.92, '-', '', 'cos_du'),
        ('Sigorta seçim katsayısı', 1.25, '-', 'In ≥ 1,25 × I', 'k_sig'),
        ('KABUK (ISI KAYBI)', None, None, None, None),
        ('Çatı U değeri', 0.20, 'W/m²K', 'mimari İZOLASYON DEĞERLERİ notu (çatı ≤0,20)', 'U_cati'),
        ('Cephe U değeri', 0.25, 'W/m²K', 'mimari İZOLASYON DEĞERLERİ notu (cephe ≤0,25)', 'U_duvar'),
        ('Zemin U değeri', 0.35, 'W/m²K', 'mimari notu (zemin 0,30–0,35)', 'U_zemin'),
        ('Zemin sıcaklık düzeltme katsayısı', 0.50, '-', 'toprağa oturan döşeme', 'f_zemin'),
        ('Cam U değeri (işyeri vitrini)', 1.80, 'W/m²K', 'varsayım — mimari doğrama bilgisi yok', 'U_cam'),
        ('İşyeri cephesinde cam oranı', 0.50, '-', 'varsayım', 'cam_oran'),
        ('Sızıntı hava değişimi', 0.30, '1/h', 'kapı açılmaları dahil (varsayım)', 'n_siz'),
    ]
    tip = [
        ('MAHAL TİPİ KATSAYILARI', None, None, None, None, None),
        ('Mahal tipi', 'Birim ısı kazancı (W/m³)', 'Duyulur oran SHR', 'Kişi yoğunluğu (kişi/m²)', 'Eşdeğer (W/m²)', 'Açıklama'),
        ('MARKET', 12, 0.80, 0.15, None, 'h = 6,00 m (kesitte tavan / makas altı +6.00)'),
        ('KORİDOR', 15, 0.85, 0.05, None, 'h = 4,50 m (1. kat / teras döşemesi +4.50)'),
        ('İŞYERİ', 20, 0.85, 0.15, None, 'h = 4,50 m, vitrin cepheli'),
    ]
    r = 4
    ws.column_dimensions['A'].width = 44
    ws.column_dimensions['B'].width = 14
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 14
    ws.column_dimensions['F'].width = 70
    from openpyxl.workbook.defined_name import DefinedName
    for ad, deger, birim, acik, isim in satir:
        if deger is None:
            hucre(ws, f'A{r}', ad, KALIN, BASLIK)
            for c in 'BCD':
                hucre(ws, f'{c}{r}', None, KALIN, BASLIK)
            r += 1
            continue
        hucre(ws, f'A{r}', ad)
        hucre(ws, f'B{r}', deger, MAVI, SARI, '0.000' if isinstance(deger, float) and deger < 10 else '#,##0.##', 'right')
        hucre(ws, f'C{r}', birim)
        hucre(ws, f'D{r}', acik, Font(name=F, size=9), kenar=False)
        wb.defined_names[isim] = DefinedName(isim, attr_text=f"VARSAYIMLAR!$B${r}")
        r += 1
    r += 1
    tip_bas = r
    for i, row in enumerate(tip):
        if i == 0:
            hucre(ws, f'A{r}', row[0], KALIN, BASLIK)
            r += 1
            continue
        if i == 1:
            for j, s in enumerate(row):
                hucre(ws, f'{"ABCDEF"[j]}{r}', s, KALIN, BASLIK, hiz='center')
            r += 1
            continue
        hucre(ws, f'A{r}', row[0], KALIN)
        hucre(ws, f'B{r}', row[1], MAVI, SARI, '0.0', 'right')
        hucre(ws, f'C{r}', row[2], MAVI, SARI, '0.00', 'right')
        hucre(ws, f'D{r}', row[3], MAVI, SARI, '0.00', 'right')
        h = 6.0 if row[0] == 'MARKET' else 4.5
        hucre(ws, f'E{r}', f'=B{r}*{h}', fmt='0.0', hiz='right')
        hucre(ws, f'F{r}', row[5], Font(name=F, size=9))
        r += 1
    tablo = f'VARSAYIMLAR!$A${tip_bas + 2}:$D${r - 1}'
    wb.defined_names['TIP_TABLO'] = DefinedName('TIP_TABLO', attr_text=tablo)
    ws[f'A{r + 1}'] = ('Birim ısı kazancı (m³ yöntemi): mahal hacmi × W/m³. Katsayı; insan, aydınlatma, cihaz, çatı/cephe güneş '
                       've iletim yüklerinin hacme bölünmüş değeridir (bkz. KONTROL sayfası). Taze hava yükü klima santrali '
                       'bataryasında ayrıca hesaplanır.')
    ws[f'A{r + 1}'].font = Font(name=F, size=9, italic=True)
    return ws


def mahaller(wb, zon):
    ws = wb.create_sheet('MAHALLER')
    bas = ['KS', 'Mahal kodu', 'Mahal adı', 'Tip', 'Alan (m²)', 'Yükseklik (m)', 'Hacim (m³)', 'Birim ısı kazancı (W/m³)',
           'Isı kazancı (W)', 'Duyulur (W)', 'Gizli (W)', 'Kişi', 'Taze hava (m³/h)',
           'Çatı alanı (m²)', 'Dış cephe boyu (m)', 'Vitrin boyu (m)', 'Cephe (duvar) alanı (m²)', 'Cam alanı (m²)',
           'ΔT kış (K)', 'Çatı kaybı (W)', 'Cephe kaybı (W)', 'Cam kaybı (W)', 'Zemin kaybı (W)', 'Sızıntı kaybı (W)',
           'Toplam ısı kaybı (W)']
    ws['A1'] = 'MAHAL HACİMLERİ, ISI KAZANCI (m³ YÖNTEMİ) VE ISI KAYBI'
    ws['A1'].font = Font(name=F, size=13, bold=True)
    ws['A2'] = ('Alanlar temiz mimarinin A-AREA mahal sınırlarından ölçülmüştür; market satış alanı ve koridor KS hizmet '
                'bantlarına bölünmüştür. Kanal dalı giren işyerleri ilgili KS’ye bağlanmıştır.')
    ws['A2'].font = Font(name=F, size=9, italic=True)
    for j, s in enumerate(bas, 1):
        c = hucre(ws, f'{get_column_letter(j)}4', s, KALIN, BASLIK, hiz='center')
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(j)].width = 13
    ws.column_dimensions['C'].width = 22
    ws.row_dimensions[4].height = 48
    r = 5
    for z in zon:
        hucre(ws, f'A{r}', z['ks'], KALIN, hiz='center')
        hucre(ws, f'B{r}', z['kod'], hiz='center')
        hucre(ws, f'C{r}', z['ad'])
        hucre(ws, f'D{r}', z['tip'], hiz='center')
        hucre(ws, f'E{r}', z['alan'], MAVI, None, '#,##0.0', 'right')
        hucre(ws, f'F{r}', z['h'], MAVI, None, '0.00', 'right')
        hucre(ws, f'G{r}', f'=E{r}*F{r}', fmt='#,##0', hiz='right')
        hucre(ws, f'H{r}', f'=VLOOKUP(D{r},TIP_TABLO,2,FALSE)', YESIL, fmt='0.0', hiz='right')
        hucre(ws, f'I{r}', f'=G{r}*H{r}', fmt='#,##0', hiz='right')
        hucre(ws, f'J{r}', f'=I{r}*VLOOKUP(D{r},TIP_TABLO,3,FALSE)', fmt='#,##0', hiz='right')
        hucre(ws, f'K{r}', f'=I{r}-J{r}', fmt='#,##0', hiz='right')
        hucre(ws, f'L{r}', f'=ROUND(E{r}*VLOOKUP(D{r},TIP_TABLO,4,FALSE),0)', fmt='#,##0', hiz='right')
        hucre(ws, f'M{r}', f'=(L{r}*q_kisi+E{r}*q_alan)*3.6', fmt='#,##0', hiz='right')
        hucre(ws, f'N{r}', z['cati'], MAVI, None, '#,##0.0', 'right')
        hucre(ws, f'O{r}', z['duvar_boy'], MAVI, None, '0.0', 'right')
        hucre(ws, f'P{r}', z['cam_boy'], MAVI, None, '0.0', 'right')
        hucre(ws, f'Q{r}', f'=O{r}*F{r}-R{r}', fmt='#,##0.0', hiz='right')
        hucre(ws, f'R{r}', f'=P{r}*F{r}*cam_oran', fmt='#,##0.0', hiz='right')
        hucre(ws, f'S{r}', '=Ti_kis-To_kis', fmt='0.0', hiz='right')
        hucre(ws, f'T{r}', f'=N{r}*U_cati*S{r}', fmt='#,##0', hiz='right')
        hucre(ws, f'U{r}', f'=Q{r}*U_duvar*S{r}', fmt='#,##0', hiz='right')
        hucre(ws, f'V{r}', f'=R{r}*U_cam*S{r}', fmt='#,##0', hiz='right')
        hucre(ws, f'W{r}', f'=E{r}*U_zemin*f_zemin*S{r}', fmt='#,##0', hiz='right')
        hucre(ws, f'X{r}', f'=n_siz*G{r}*rho*cp/3.6*S{r}', fmt='#,##0', hiz='right')
        hucre(ws, f'Y{r}', f'=SUM(T{r}:X{r})', fmt='#,##0', hiz='right')
        r += 1
    son = r - 1
    hucre(ws, f'A{r}', 'TOPLAM', KALIN, TOPLAM)
    for c in 'BCD':
        hucre(ws, f'{c}{r}', None, fill=TOPLAM)
    for c in 'EGIJKLMNTUVWXY':
        hucre(ws, f'{c}{r}', f'=SUM({c}5:{c}{son})', KALIN, TOPLAM, '#,##0', 'right')
    for c in 'FHOPQRS':
        hucre(ws, f'{c}{r}', None, fill=TOPLAM)
    hucre(ws, f'A{r + 2}', 'Isı kazancı = Hacim × birim ısı kazancı (m³ yöntemi). Kayıp: Q = U·A·ΔT; sızıntı Q = n·V·ρ·cp·ΔT.',
          Font(name=F, size=9, italic=True), kenar=False)
    ws.freeze_panes = 'E5'
    return ws, 5, son


PSY = {
    # satır başlığı, formül şablonu ({c} = sütun harfi), biçim, birim
}


def ks_hesabi(wb, m0, m1):
    ws = wb.create_sheet('KS HESABI')
    ws['A1'] = 'ISI GERİ KAZANIMLI KLİMA SANTRALİ — DX SOĞUTMA VE ISITMA BATARYASI HESABI'
    ws['A1'].font = Font(name=F, size=13, bold=True)
    ws['A2'] = ('Akış: taze hava → plakalı ısı geri kazanım → karışım (dönüş havası) → F7 filtre → DX soğutma bataryası → '
                'DX ısıtma bataryası → üfleme fanı. Psikrometri: pws = 0,61094·e^(17,625·T/(T+243,04)) kPa (Magnus).')
    ws['A2'].font = Font(name=F, size=9, italic=True)
    ws.column_dimensions['A'].width = 54
    ws.column_dimensions['B'].width = 10
    for c in 'CDEF':
        ws.column_dimensions[c].width = 14
    ws.column_dimensions['G'].width = 60
    hucre(ws, 'A4', 'BÜYÜKLÜK', KALIN, BASLIK)
    hucre(ws, 'B4', 'BİRİM', KALIN, BASLIK, hiz='center')
    for i, k in enumerate(KS):
        hucre(ws, f'{"CDEF"[i]}4', k, KALIN, BASLIK, hiz='center')
    hucre(ws, 'G4', 'AÇIKLAMA', KALIN, BASLIK)
    M = "MAHALLER"
    rng = lambda c: f'{M}!${c}${m0}:${c}${m1}'
    satirlar = [
        ('— ODA YÜKLERİ (MAHALLER sayfasından) —', None, None, None),
        ('Hizmet edilen hacim', 'm³', '=SUMIF({A},{k},{G})', 'Σ mahal hacmi'),
        ('Hizmet edilen alan', 'm²', '=SUMIF({A},{k},{E})', ''),
        ('Oda ısı kazancı (m³ yöntemi)', 'kW', '=SUMIF({A},{k},{I})/1000', 'Σ hacim × W/m³'),
        ('Oda duyulur ısı kazancı', 'kW', '=SUMIF({A},{k},{J})/1000', ''),
        ('Oda gizli ısı kazancı', 'kW', '=SUMIF({A},{k},{K})/1000', ''),
        ('Oda ısı kaybı (kış)', 'kW', '=SUMIF({A},{k},{Y})/1000', 'iletim + zemin + sızıntı (iç kazanç düşülmedi)'),
        ('Taze hava ihtiyacı (TS EN 16798-1)', 'm³/h', '=SUMIF({A},{k},{M})', 'kişi × 7 l/s + alan × 0,7 l/s'),
        ('— SANTRAL HAVASI —', None, None, None),
        ('Kişi sayısı (tasarım)', 'kişi', '=SUMIF({A},{k},{L})', 'taze hava hesabında kullanılan'),
        ('Üfleme debisi', 'm³/h', '=V_ks', 'kullanıcı projesi'),
        ('Kütlesel debi', 'kg/s', '={c}15*rho/3600', ''),
        ('Taze hava debisi (seçilen)', 'm³/h', '=CEILING({c}12,500)', '500’e yukarı yuvarlanmış'),
        ('Taze hava oranı', '-', '={c}17/{c}15', 'kalan kısım dönüş (karışım) havası'),
        ('Egzoz debisi', 'm³/h', '={c}17', 'dengeli işletme'),
        ('Fan ısısı ile sıcaklık artışı', 'K', '=P_fan/({c}16*cp)', 'fan bataryadan sonra'),
        ('— YAZ (SOĞUTMA) —', None, None, None),
        ('Dış hava nem oranı (35/25)', 'kg/kg', '=((2501-2.326*Twb_yaz)*(0.622*0.61094*EXP(17.625*Twb_yaz/(Twb_yaz+243.04))/(Patm-0.61094*EXP(17.625*Twb_yaz/(Twb_yaz+243.04))))-1.006*(To_yaz-Twb_yaz))/(2501+1.86*To_yaz-4.186*Twb_yaz)', 'yaş termometreden'),
        ('İç hava nem oranı (26 °C / %50)', 'kg/kg', '=0.622*RH_yaz*0.61094*EXP(17.625*Ti_yaz/(Ti_yaz+243.04))/(Patm-RH_yaz*0.61094*EXP(17.625*Ti_yaz/(Ti_yaz+243.04)))', ''),
        ('Isı geri kazanım sonrası taze hava sıcaklığı', '°C', '=To_yaz-eps*(To_yaz-Ti_yaz)', 'duyulur geri kazanım (nem değişmez)'),
        ('Karışım havası sıcaklığı', '°C', '={c}18*{c}24+(1-{c}18)*Ti_yaz', ''),
        ('Karışım havası nem oranı', 'kg/kg', '={c}18*{c}22+(1-{c}18)*{c}23', ''),
        ('Karışım havası entalpisi', 'kJ/kg', '=cp*{c}25+{c}26*(hfg+1.86*{c}25)', ''),
        ('Gerekli üfleme sıcaklığı', '°C', '=Ti_yaz-{c}9/({c}16*cp)', 'oda duyulur yükünü karşılayan'),
        ('Gerekli üfleme nem oranı', 'kg/kg', '={c}23-{c}10/({c}16*hfg)', 'oda gizli yükünü karşılayan'),
        ('Batarya çıkış sıcaklığı', '°C', '={c}28-{c}20', 'fan ısısı düşülmüş'),
        ('Batarya çıkış bağıl nemi', '%', '=({c}29*Patm/(0.622+{c}29))/(0.61094*EXP(17.625*{c}30/({c}30+243.04)))', '≤ %95 olmalı (DX batarya ile sağlanabilir)'),
        ('Batarya çıkış entalpisi', 'kJ/kg', '=cp*{c}30+{c}29*(hfg+1.86*{c}30)', ''),
        ('DX SOĞUTMA BATARYASI KAPASİTESİ (hesap)', 'kW', '={c}16*({c}27-{c}32)', 'Q = ṁ·(h_karışım − h_çıkış)'),
        ('  bunun duyulur kısmı', 'kW', '={c}16*cp*({c}25-{c}30)', ''),
        ('  bunun gizli kısmı (yoğuşma)', 'kW', '={c}33-{c}34', ''),
        ('Yoğuşma suyu', 'l/h', '={c}16*({c}26-{c}29)*3600', 'drenaj (sifonlu) hesabı için'),
        ('DX SOĞUTMA BATARYASI SEÇİM KAPASİTESİ', 'kW', '=CEILING({c}33*emn,5)', 'emniyet payı ile, 5 kW’a yuvarlanmış'),
        ('— KIŞ (ISITMA) —', None, None, None),
        ('Isı geri kazanım sonrası taze hava sıcaklığı', '°C', '=To_kis+eps*(Ti_kis-To_kis)', 'plakada donma koruması (by-pass) yapılacak'),
        ('Karışım havası sıcaklığı', '°C', '={c}18*{c}39+(1-{c}18)*Ti_kis', ''),
        ('Gerekli üfleme sıcaklığı', '°C', '=Ti_kis+{c}11/({c}16*cp)', 'oda ısı kaybını karşılayan'),
        ('Batarya çıkış sıcaklığı', '°C', '={c}41-{c}20', 'fan ısısı düşülmüş'),
        ('DX ISITMA BATARYASI KAPASİTESİ (hesap)', 'kW', '=MAX(0,{c}16*cp*({c}42-{c}40))', 'Q = ṁ·cp·ΔT'),
        ('Sabah ön ısıtma kontrolü (%100 dönüş, 15 °C → üfleme 20 °C + kayıp)', 'kW', '={c}16*cp*5+{c}11', 'iç kazançsız ilk devreye alma'),
        ('DX ISITMA BATARYASI SEÇİM KAPASİTESİ', 'kW', '=CEILING(MAX({c}43,{c}44)*emn,5)', 'büyük olan × emniyet'),
        ('— DIŞ ÜNİTE (ISI POMPASI, DX) —', None, None, None),
        ('Dış ünite toplam soğutma kapasitesi (en az)', 'kW', '={c}37', ''),
        ('Dış ünite toplam ısıtma kapasitesi (−3 °C dış hava, en az)', 'kW', '={c}45', ''),
        ('Gerekli nominal ısıtma kapasitesi', 'kW', '=CEILING({c}48/dus,5)', '−3 °C kapasite düşümü ile'),
        ('Dış ünite adedi', 'adet', '=2', 'her santrale 2 modül (yedekli kısmi yük)'),
        ('Modül başına soğutma kapasitesi (en az)', 'kW', '=CEILING({c}47/{c}50,5)', ''),
        ('Modül başına nominal ısıtma kapasitesi (en az)', 'kW', '=CEILING({c}49/{c}50,5)', ''),
        ('— KONTROL —', None, None, None),
        ('Havalandırma projesindeki santral kapasitesi', 'kW', '=200', 'kullanıcı çiziminde "Q= 200kW"'),
        ('Soğutma seçim kapasitesi / proje değeri', '-', '={c}37/{c}54', '>1 ise projedeki 200 kW yetersiz'),
    ]
    r = 5
    for ad, birim, form, acik in satirlar:
        if birim is None:
            hucre(ws, f'A{r}', ad, KALIN, BASLIK)
            for c in 'BCDEFG':
                hucre(ws, f'{c}{r}', None, fill=BASLIK)
            r += 1
            continue
        kalin = ad.isupper() or 'SEÇİM' in ad
        hucre(ws, f'A{r}', ad, KALIN if kalin else SIYAH, TOPLAM if 'SEÇİM' in ad else None)
        hucre(ws, f'B{r}', birim, hiz='center')
        for i, k in enumerate(KS):
            c = 'CDEF'[i]
            f = form.format(c=c, k=f'{c}$4', A=rng('A'), E=rng('E'), G=rng('G'), I=rng('I'), J=rng('J'),
                            K=rng('K'), L=rng('L'), M=rng('M'), Y=rng('Y'))
            fmt = '0.00000' if birim == 'kg/kg' else '0.0%' if birim == '%' else '0.00' if birim in ('-', 'kg/s') \
                else '0.0' if birim in ('°C', 'K', 'kJ/kg') else '#,##0'
            if birim == 'kW':
                fmt = '#,##0.0'
            hucre(ws, f'{c}{r}', f, KALIN if kalin else SIYAH, TOPLAM if 'SEÇİM' in ad else None, fmt, 'right')
        hucre(ws, f'G{r}', acik, Font(name=F, size=9))
        r += 1
    # satır numaralarının şablonla uyumu (formüllerde sabit satır kullanıldı)
    beklenen = {'Üfleme debisi': 15, 'Kütlesel debi': 16, 'Taze hava debisi (seçilen)': 17, 'Taze hava oranı': 18,
                'Fan ısısı ile sıcaklık artışı': 20, 'Oda duyulur ısı kazancı': 9, 'Oda gizli ısı kazancı': 10,
                'Oda ısı kaybı (kış)': 11, 'Taze hava ihtiyacı (TS EN 16798-1)': 12,
                'DX SOĞUTMA BATARYASI KAPASİTESİ (hesap)': 33, 'DX SOĞUTMA BATARYASI SEÇİM KAPASİTESİ': 37,
                'DX ISITMA BATARYASI KAPASİTESİ (hesap)': 43, 'DX ISITMA BATARYASI SEÇİM KAPASİTESİ': 45,
                'Havalandırma projesindeki santral kapasitesi': 54}
    for rr in range(5, r):
        a = ws[f'A{rr}'].value
        if a in beklenen and beklenen[a] != rr:
            raise SystemExit(f'satır kayması: {a} {rr} ≠ {beklenen[a]}')
    hucre(ws, f'A{r}', 'TOPLAM SOĞUTMA SEÇİM (4 santral)', KALIN, TOPLAM)
    hucre(ws, f'C{r}', '=SUM(C37:F37)', KALIN, TOPLAM, '#,##0', 'right')
    hucre(ws, f'B{r}', 'kW', hiz='center')
    hucre(ws, f'A{r + 1}', 'TOPLAM ISITMA SEÇİM (4 santral)', KALIN, TOPLAM)
    hucre(ws, f'C{r + 1}', '=SUM(C45:F45)', KALIN, TOPLAM, '#,##0', 'right')
    hucre(ws, f'B{r + 1}', 'kW', hiz='center')
    hucre(ws, f'A{r + 2}', 'TOPLAM ODA ISI KAZANCI (m³ yöntemi)', KALIN, TOPLAM)
    hucre(ws, f'C{r + 2}', '=SUM(C8:F8)', KALIN, TOPLAM, '#,##0', 'right')
    hucre(ws, f'B{r + 2}', 'kW', hiz='center')
    ws.freeze_panes = 'C5'
    return ws


def elektrik(wb):
    ws = wb.create_sheet('ELEKTRİK YÜKLERİ')
    ws['A1'] = 'ISITMA-SOĞUTMA VE HAVALANDIRMA CİHAZLARI ELEKTRİK YÜKÜ TABLOSU'
    ws['A1'].font = Font(name=F, size=13, bold=True)
    ws['A2'] = ('Cihaz numaraları planda cihaz yanındaki daire içindeki numaralarla aynıdır. Dış ünite gücü soğutma ve '
                'ısıtma çekişinin büyüğüdür. Kablo kesiti ve pano seçimi elektrik projesinde yapılacaktır.')
    ws['A2'].font = Font(name=F, size=9, italic=True)
    bas = ['NO', 'CİHAZ KODU', 'CİHAZ', 'GÜÇ BİLEŞENLERİ', 'SOĞUTMA ÇEKİŞİ (kW)', 'ISITMA ÇEKİŞİ (kW)',
           'ELEKTRİK GÜCÜ (kW)', 'GERİLİM (V)', 'cos φ', 'AKIM (A)', 'SİGORTA (A)']
    gen = [7, 12, 40, 46, 14, 14, 14, 10, 8, 10, 11]
    for j, (b_, w) in enumerate(zip(bas, gen)):
        c = hucre(ws, f'{get_column_letter(j + 1)}4', b_, KALIN, BASLIK, hiz='center')
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(j + 1)].width = w
    ws.row_dimensions[4].height = 32
    K = "'KS HESABI'"
    r = 5
    no = 1
    sig = ('=INDEX({{6,10,16,20,25,32,40,50,63,80,100,125,160,200,250}},'
           'MATCH(TRUE,INDEX({{6,10,16,20,25,32,40,50,63,80,100,125,160,200,250}}>=J{r}*k_sig,0),0))')
    for i in range(4):
        c = 'CDEF'[i]
        satirlar = [(f'KS-{i + 1}', 'ISI GERİ KAZANIMLI KLİMA SANTRALİ',
                     'üfleme EC fanı + dönüş EC fanı + otomasyon', '=P_fan*(1+k_donus)+P_oto', '=E{r}', 'cos_ks')]
        for j in (1, 2):
            satirlar.append((f'DÜ-{i + 1}.{j}', 'DX DIŞ ÜNİTE (ISI POMPASI)', 'kompresör + kondenser fanları',
                             f'={K}!{c}51/EER', f'={K}!{c}52*dus/COP', 'cos_du'))
        for kod, ad, bil, f_s, f_i, cos in satirlar:
            hucre(ws, f'A{r}', no, KALIN, hiz='center')
            hucre(ws, f'B{r}', kod, KALIN, hiz='center')
            hucre(ws, f'C{r}', ad)
            hucre(ws, f'D{r}', bil, Font(name=F, size=9))
            hucre(ws, f'E{r}', f_s.format(r=r), fmt='0.0', hiz='right')
            hucre(ws, f'F{r}', f_i.format(r=r), fmt='0.0', hiz='right')
            hucre(ws, f'G{r}', f'=ROUND(MAX(E{r},F{r}),1)', KALIN, fmt='0.0', hiz='right')
            hucre(ws, f'H{r}', '=U_v', fmt='0', hiz='right')
            hucre(ws, f'I{r}', f'={cos}', fmt='0.00', hiz='right')
            hucre(ws, f'J{r}', f'=G{r}*1000/(SQRT(3)*H{r}*I{r})', fmt='0.0', hiz='right')
            hucre(ws, f'K{r}', sig.format(r=r), KALIN, fmt='0', hiz='right')
            r += 1
            no += 1
    son = r - 1
    hucre(ws, f'A{r}', None, fill=TOPLAM)
    hucre(ws, f'B{r}', None, fill=TOPLAM)
    hucre(ws, f'C{r}', 'TOPLAM KURULU GÜÇ', KALIN, TOPLAM)
    hucre(ws, f'D{r}', None, fill=TOPLAM)
    for c in 'EFGJ':
        hucre(ws, f'{c}{r}', f'=SUM({c}5:{c}{son})', KALIN, TOPLAM, '#,##0.0', 'right')
    for c in 'HIK':
        hucre(ws, f'{c}{r}', None, fill=TOPLAM)
    hucre(ws, f'C{r + 1}', 'EŞ ZAMANLI ÇEKİŞ (soğutma modu, eş zamanlılık 1,0)', KALIN)
    hucre(ws, f'G{r + 1}', f'=E{r}', KALIN, None, '#,##0.0', 'right')
    hucre(ws, f'C{r + 2}', 'EŞ ZAMANLI ÇEKİŞ (ısıtma modu)', KALIN)
    hucre(ws, f'G{r + 2}', f'=F{r}', KALIN, None, '#,##0.0', 'right')
    ws.freeze_panes = 'C5'
    return ws


def cihaz_listesi(wb):
    ws = wb.create_sheet('CİHAZ LİSTESİ')
    ws['A1'] = 'CİHAZ LİSTESİ'
    ws['A1'].font = Font(name=F, size=13, bold=True)
    bas = ['NO', 'CİHAZ', 'ÖZELLİK', 'KS-1', 'KS-2', 'KS-3', 'KS-4', 'BİRİM']
    gen = [8, 40, 52, 12, 12, 12, 12, 10]
    for j, (s, w) in enumerate(zip(bas, gen)):
        hucre(ws, f'{get_column_letter(j + 1)}3', s, KALIN, BASLIK, hiz='center')
        ws.column_dimensions[get_column_letter(j + 1)].width = w
    K = "'KS HESABI'"
    sat = [
        ('KS', 'ISI GERİ KAZANIMLI KLİMA SANTRALİ', 'Üfleme / dönüş hava debisi', '={K}!{c}15', 'm³/h'),
        ('', '(yan yana iki bölmeli, dış ortam tipi)', 'Taze hava / egzoz debisi', '={K}!{c}17', 'm³/h'),
        ('', '', 'Plakalı ısı geri kazanım duyulur verimi', '=eps', '-'),
        ('', '', 'DX soğutma bataryası kapasitesi', '={K}!{c}37', 'kW'),
        ('', '', 'DX ısıtma bataryası kapasitesi', '={K}!{c}45', 'kW'),
        ('', '', 'Yoğuşma suyu', '={K}!{c}36', 'l/h'),
        ('', '', 'Üfleme fanı (EC plug fan) elektrik gücü', '=P_fan', 'kW'),
        ('', '', 'Dönüş/egzoz fanı (EC plug fan) elektrik gücü', '=ROUND(P_fan*k_donus,1)', 'kW'),
        ('', '', 'Filtre (taze hava / dönüş / üfleme)', 'G4 / G4 / F7', ''),
        ('', '', 'Dış ölçü (U × G × Y) yaklaşık', '830×545×220', 'cm'),
        ('DÜ', 'DX DIŞ ÜNİTE (HAVA KAYNAKLI ISI POMPASI)', 'Adet (santral başına)', '={K}!{c}50', 'adet'),
        ('', '', 'Modül soğutma kapasitesi (en az)', '={K}!{c}51', 'kW'),
        ('', '', 'Modül nominal ısıtma kapasitesi (en az)', '={K}!{c}52', 'kW'),
        ('', '', 'Dış ölçü (U × G × Y) yaklaşık, modül başına', '240×110×190', 'cm'),
    ]
    r = 4
    for no, ad, oz, form, birim in sat:
        hucre(ws, f'A{r}', no, KALIN, hiz='center')
        hucre(ws, f'B{r}', ad, KALIN if ad else SIYAH)
        hucre(ws, f'C{r}', oz)
        for i in range(4):
            c = 'CDEF'[i]
            v = form.format(K=K, c=c) if form.startswith('=') else form
            fmt = '0%' if oz.startswith('Plakalı') else '#,##0.0' if birim == 'kW' else '#,##0'
            hucre(ws, f'{"DEFG"[i]}{r}', v, fmt=fmt, hiz='right')
        hucre(ws, f'H{r}', birim, hiz='center')
        r += 1
    ws[f'A{r + 1}'] = ('Dış ünite ölçüleri ve adet üretici seçimine göre kesinleşecektir; ölçüler yerleşim için yaklaşık '
                       'verilmiştir. Ünite ölçüleri çizimdeki kesit ve yerleşim paftasıyla aynıdır.')
    ws[f'A{r + 1}'].font = Font(name=F, size=9, italic=True)
    return ws


def kontrol(wb):
    ws = wb.create_sheet('KONTROL')
    ws['A1'] = 'KONTROL — MARKET BİRİM ISI KAZANCININ BİLEŞENLERLE DOĞRULANMASI (m² başına)'
    ws['A1'].font = Font(name=F, size=13, bold=True)
    ws.column_dimensions['A'].width = 52
    for c in 'BCDE':
        ws.column_dimensions[c].width = 16
    for j, s in enumerate(['BİLEŞEN', 'DEĞER', 'BİRİM', 'W/m²', 'KAYNAK / VARSAYIM']):
        hucre(ws, f'{"ABCDE"[j]}3', s, KALIN, BASLIK, hiz='center')
    ws.column_dimensions['E'].width = 60
    sat = [
        ('İnsan (duyulur + gizli 130 W/kişi)', '=VLOOKUP("MARKET",TIP_TABLO,4,FALSE)', 'kişi/m²', '=B4*130', 'ASHRAE: alışveriş, ayakta yürüyen kişi'),
        ('Aydınlatma', 12, 'W/m²', '=B5', 'LED market aydınlatması (varsayım)'),
        ('Cihaz (kasa, ekran, açık soğutucu dolap artığı)', 10, 'W/m²', '=B6', 'varsayım'),
        ('Çatı güneş + iletim (U × eşdeğer ΔT 25 K)', '=U_cati', 'W/m²K', '=B7*25', 'mimari çatı U değeri'),
        ('Cephe ve kapı açılmaları payı', 8, 'W/m²', '=B8', 'varsayım'),
        ('BİLEŞENLERLE TOPLAM', None, None, '=SUM(D4:D8)', ''),
        ('m³ yöntemi (12 W/m³ × 6,00 m)', None, None, "=VARSAYIMLAR!E" + '{tip}', 'VARSAYIMLAR sayfası'),
        ('m³ yönteminin bileşen toplamına oranı', None, None, '=D10/D9', '>1 → m³ yöntemi emniyetli tarafta'),
    ]
    r = 4
    for ad, deg, birim, w, kay in sat:
        hucre(ws, f'A{r}', ad, KALIN if ad.isupper() else SIYAH)
        if deg is not None:
            hucre(ws, f'B{r}', deg, MAVI if not str(deg).startswith('=') else YESIL,
                  SARI if not str(deg).startswith('=') else None, '0.00', 'right')
        else:
            hucre(ws, f'B{r}', None)
        hucre(ws, f'C{r}', birim, hiz='center')
        hucre(ws, f'D{r}', w, KALIN if ad.isupper() else SIYAH, None, '0.0' if 'oranı' not in ad else '0.00', 'right')
        hucre(ws, f'E{r}', kay, Font(name=F, size=9))
        r += 1
    return ws


def main():
    zon = json.load(open(ZON))
    wb = Workbook()
    v = varsayimlar(wb)
    # MARKET satırının E sütunu (eşdeğer W/m²) konumu
    tip_satir = next(r for r in range(1, 80) if v[f'A{r}'].value == 'MARKET')
    mahaller(wb, zon)
    m0, m1 = 5, 4 + len(zon)
    ks_hesabi(wb, m0, m1)
    cihaz_listesi(wb)
    elektrik(wb)
    k = kontrol(wb)
    k['D10'] = f'=VARSAYIMLAR!E{tip_satir}'
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False
        ws.page_setup.orientation = 'landscape'
        ws.page_setup.fitToWidth = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToHeight = 0
    wb.save(CIKTI)
    print('yazıldı', CIKTI)


if __name__ == '__main__':
    main()
