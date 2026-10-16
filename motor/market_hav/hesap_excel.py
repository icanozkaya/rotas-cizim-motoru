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
        ('Kişi başı taze hava', 7.0, 'l/s·kişi', 'TS EN 16798-1 Kategori II', 'q_kisi'),
        ('Alan başı taze hava', 0.7, 'l/s·m²', 'TS EN 16798-1 az kirletici bina', 'q_alan'),
        ('Batarya emniyet payı', 1.10, '-', 'seçim = hesap × emniyet', 'emn'),
        ('Dış ünite ısıtma kapasitesi düşümü (−3 °C)', 0.80, '-', 'ısı pompası −3 °C dış havada nominal ısıtmanın ~%80’i', 'dus'),
        ('FANLAR (SANTRALDE 2 MOTOR: 1 ÜFLEME + 1 EMİŞ/EGZOZ)', None, None, None, None),
        ('Bölme başına fan / motor adedi', 1, 'adet', 'her bölmede tek fan + tek motor (üfleme ve emiş/egzoz)', 'n_fan'),
        ('Fan sistem verimi (çark + motor + frekans konvertörü)', 0.65, '-', 'geriye eğik kanatlı plug fan, IE4 motor, frekans konvertörlü', 'eta_fan'),
        ('Motor seçim payı', 1.10, '-', 'motor anma gücü ≥ mil gücü × 1,10 → bir üst IEC standart motor gücü', 'k_motor'),
        ('Kritik hat uzunluğu (santral → en uzak menfez)', 75, 'm', 'planda KS çıkışı → ana kanal → branşman sonu', 'L_kr'),
        ('Ortalama sürtünme kaybı', 0.6, 'Pa/m', 'galvaniz kanal, 3–6 m/s', 'R_ort'),
        ('Üfleme hattı yerel kayıp katsayıları toplamı Σζ', 6.0, '-', 'dirsekler, T, redüksiyonlar', 'z_uf'),
        ('Dönüş hattı yerel kayıp katsayıları toplamı Σζ', 5.0, '-', '', 'z_do'),
        ('Üfleme menfezi basınç kaybı', 40, 'Pa', 'kanal altı yuvarlak menfez + ayar damperi', 'dp_mu'),
        ('Emiş menfezi basınç kaybı', 30, 'Pa', '', 'dp_me'),
        ('Brandi (esnek bağlantı)', 10, 'Pa', '', 'dp_br'),
        ('Yangın damperi', 20, 'Pa', 'yangın bölmesi geçişlerinde', 'dp_yd'),
        ('Ana kanal hızı (1600×1200, 39.900 m³/h)', 5.77, 'm/s', 'KANAL HIZ KONTROL tablosu', 'v_ana'),
        ('Damper motoru (taze, egzoz, karışım, by-pass)', 0.004, 'kW', '24 V; 20 Nm sınıfı ~2 W çalışma / 4 VA boyutlandırma (Belimo LM24A 5 Nm: 1 W / 2 VA)', 'P_dmp'),
        ('Santral kontrol (DDC) panosu', 0.15, 'kW', 'DDC + sensörler + 24 V trafo (varsayım)', 'P_ddc'),
        ('ELEKTRİK', None, None, None, None),
        ('Dış ünite soğutma verimi EER (35 °C dış hava, fanlar dahil)', 2.8, '-', 'ısı pompalı hava soğutmalı kondenser ünitesi; Trane RAUX katalog EER 2,81 — üretici değeriyle değiştir', 'EER'),
        ('Dış ünite ısıtma verimi COP (−3 °C dış hava)', 2.6, '-', 'varsayım, üretici değeriyle değiştir', 'COP'),
        ('Besleme gerilimi (3 faz)', 400, 'V', '3~ 50 Hz', 'U_v'),
        ('Güç faktörü — frekans konvertörlü fan motorları', 0.95, '-', 'konvertör giriş güç faktörü', 'cos_ks'),
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


FAN_BILESEN_UF = [('Taze hava panjuru + damperi', 40), ('G4 panel filtre (tasarım = ilk+son / 2)', 100),
                  ('Plakalı ısı geri kazanım eşanjörü (kuru)', 120), ('Karışım bölmesi', 10),
                  ('F7 torba filtre (tasarım)', 150), ('DX soğutma bataryası (ıslak) + damla tutucu', 130),
                  ('DX ısıtma bataryası', 50), ('Susturucu', 40), ('Gövde, giriş/çıkış kayıpları', 50)]
FAN_BILESEN_DO = [('Dönüş damperi', 20), ('G4 panel filtre (tasarım)', 100), ('Susturucu', 40),
                  ('Karışım bölmesi', 10), ('Plakalı ısı geri kazanım eşanjörü (kuru)', 120),
                  ('Egzoz damperi + panjur', 40), ('Gövde, giriş/çıkış kayıpları', 40)]
MOTORLAR = '{{1.1,1.5,2.2,3,4,5.5,7.5,11,15,18.5,22,30,37,45}}'


def fan_hesabi(wb):
    from openpyxl.workbook.defined_name import DefinedName
    ws = wb.create_sheet('FAN HESABI')
    ws['A1'] = 'KLİMA SANTRALİ FAN HESABI — ÜFLEME FANI VE EMİŞ / EGZOZ FANI (SANTRAL BAŞINA 2 MOTOR)'
    ws['A1'].font = Font(name=F, size=13, bold=True)
    ws['A2'] = ('Fan toplam basıncı = santral iç kayıpları + dış statik basınç (kanal). Emilen güç P = V·Δp/η. '
                'Her santralde 2 motor vardır: üfleme fanı ve emiş/egzoz fanı. Dört santral aynı seçimle donatılır. Tüm güçler ELEKTRİK gücüdür (kW).')
    ws['A2'].font = Font(name=F, size=9, italic=True)
    ws.column_dimensions['A'].width = 56
    ws.column_dimensions['B'].width = 14
    ws.column_dimensions['C'].width = 14
    ws.column_dimensions['D'].width = 50
    for j, b_ in enumerate(['BÜYÜKLÜK', 'ÜFLEME FANI', 'EMİŞ / EGZOZ FANI', 'AÇIKLAMA']):
        hucre(ws, f'{"ABCD"[j]}4', b_, KALIN, BASLIK, hiz='center')
    r = 5
    hucre(ws, f'A{r}', '— SANTRAL İÇ BASINÇ KAYIPLARI (Pa) —', KALIN, BASLIK)
    r += 1
    r0 = r
    n = max(len(FAN_BILESEN_UF), len(FAN_BILESEN_DO))
    for i in range(n):
        a = FAN_BILESEN_UF[i] if i < len(FAN_BILESEN_UF) else None
        b_ = FAN_BILESEN_DO[i] if i < len(FAN_BILESEN_DO) else None
        hucre(ws, f'A{r}', (a[0] if a else '') + ('  |  ' + b_[0] if b_ else ''), Font(name=F, size=9))
        hucre(ws, f'B{r}', a[1] if a else None, MAVI, SARI if a else None, '0', 'right')
        hucre(ws, f'C{r}', b_[1] if b_ else None, MAVI, SARI if b_ else None, '0', 'right')
        hucre(ws, f'D{r}', 'sol: üfleme bölmesi  |  sağ: dönüş bölmesi' if i == 0 else '', Font(name=F, size=9))
        r += 1
    r1 = r - 1
    satir = [
        ('Santral iç kayıpları toplamı', 'Pa', f'=SUM(B{r0}:B{r1})', f'=SUM(C{r0}:C{r1})', ''),
        ('— DIŞ STATİK BASINÇ (KANAL) —', None, None, None, None),
        ('Ana kanal dinamik basıncı', 'Pa', '=0.6*v_ana^2', '=0.6*v_ana^2', 'Pd = ρ·v²/2'),
        ('Sürtünme kaybı (L × R)', 'Pa', '=L_kr*R_ort', '=L_kr*R_ort', ''),
        ('Yerel kayıplar (Σζ × Pd)', 'Pa', '=z_uf*B{pd}', '=z_do*C{pd}', ''),
        ('Menfez + brandi + yangın damperi', 'Pa', '=dp_mu+dp_br+dp_yd', '=dp_me+dp_br+dp_yd', ''),
        ('Dış statik basınç (hesap)', 'Pa', '=SUM(B{a}:B{b})', '=SUM(C{a}:C{b})', ''),
        ('Dış statik basınç (seçim, 50 Pa’a yuvarlanmış)', 'Pa', '=CEILING(B{esp},50)', '=CEILING(C{esp},50)', ''),
        ('FAN TOPLAM BASINCI', 'Pa', '=B{ic}+B{esps}', '=C{ic}+C{esps}', 'santral iç + dış statik'),
        ('— FAN SEÇİMİ —', None, None, None, None),
        ('Toplam hava debisi', 'm³/h', '=V_ks', '=V_ks', 'kullanıcı projesi'),
        ('Fan / motor adedi', 'adet', '=n_fan', '=n_fan', 'santral başına 1 üfleme + 1 emiş'),
        ('Fan debisi', 'm³/h', '=B{q}/B{nf}', '=C{q}/C{nf}', ''),
        ('Toplam emilen elektrik gücü', 'kW', '=B{q}/3600*B{tp}/eta_fan/1000', '=C{q}/3600*C{tp}/eta_fan/1000',
         'P = V·Δp / η'),
        ('Fan mil gücü (motor başına)', 'kW', '=B{pt}/B{nf}', '=C{pt}/C{nf}', ''),
        ('Motor anma gücü (seçim)', 'kW', f'=INDEX({MOTORLAR},MATCH(TRUE,INDEX({MOTORLAR}>=B{{pf}}*k_motor,0),0))',
         f'=INDEX({MOTORLAR},MATCH(TRUE,INDEX({MOTORLAR}>=C{{pf}}*k_motor,0),0))', 'bir üst standart güç'),
        ('Kurulu elektrik gücü', 'kW', '=B{nf}*B{pm}', '=C{nf}*C{pm}', 'elektrik yükü tablosuna'),
        ('Özgül fan gücü SFP', 'W/(m³/s)', '=B{pt}*1000/(B{q}/3600)', '=C{pt}*1000/(C{q}/3600)', 'TS EN 16798-3'),
        ('SFP sınıfı', '-', '=IF(B{sfp}<=500,"SFP1",IF(B{sfp}<=750,"SFP2",IF(B{sfp}<=1250,"SFP3",IF(B{sfp}<=2000,"SFP4",IF(B{sfp}<=3000,"SFP5","SFP6")))))',
         '=IF(C{sfp}<=500,"SFP1",IF(C{sfp}<=750,"SFP2",IF(C{sfp}<=1250,"SFP3",IF(C{sfp}<=2000,"SFP4",IF(C{sfp}<=3000,"SFP5","SFP6")))))',
         'SFP1 ≤500, SFP2 ≤750, SFP3 ≤1250, SFP4 ≤2000, SFP5 ≤3000'),
        ('Fan ısısı (hava akımına geçen)', 'kW', '=B{pt}', '=C{pt}', 'üfleme fanı ısısı soğutma bataryasına eklenir'),
    ]
    adr = {}
    for ad, birim, fu, fd, acik in satir:
        if birim is None:
            hucre(ws, f'A{r}', ad, KALIN, BASLIK)
            r += 1
            continue
        key = {'Santral iç kayıpları toplamı': 'ic', 'Ana kanal dinamik basıncı': 'pd', 'Sürtünme kaybı (L × R)': 'a',
               'Menfez + brandi + yangın damperi': 'b', 'Dış statik basınç (hesap)': 'esp',
               'Dış statik basınç (seçim, 50 Pa’a yuvarlanmış)': 'esps', 'FAN TOPLAM BASINCI': 'tp',
               'Toplam hava debisi': 'q', 'Fan / motor adedi': 'nf', 'Toplam emilen elektrik gücü': 'pt',
               'Fan mil gücü (motor başına)': 'pf', 'Motor anma gücü (seçim)': 'pm',
               'Kurulu elektrik gücü': 'pk', 'Özgül fan gücü SFP': 'sfp',
               'Fan ısısı (hava akımına geçen)': 'isi', 'Fan debisi': 'qf', 'SFP sınıfı': 'sinif'}.get(ad)
        if key:
            adr[key] = r
        r += 1
    # ikinci geçiş: satırları yaz (adresler bilindiği için)
    r = r1 + 1
    for ad, birim, fu, fd, acik in satir:
        if birim is None:
            r += 1
            continue
        kal = ad.isupper() or 'seçim' in ad or 'Kurulu' in ad
        hucre(ws, f'A{r}', ad, KALIN if kal else SIYAH, TOPLAM if 'Kurulu' in ad or ad.isupper() else None)
        fmt = '0' if birim in ('Pa', 'm³/h', 'adet', 'W/(m³/s)') else '0.00' if birim == 'kW' else '@'
        for col, f_ in (('B', fu), ('C', fd)):
            hucre(ws, f'{col}{r}', f_.format(**adr), KALIN if kal else SIYAH,
                  TOPLAM if 'Kurulu' in ad or ad.isupper() else None, fmt, 'right')
        hucre(ws, f'D{r}', f'{birim} — {acik}' if acik else birim, Font(name=F, size=9))
        r += 1
    for isim, hucre_ in (('P_fan', f"'FAN HESABI'!$B${adr['isi']}"), ('Pk_uf', f"'FAN HESABI'!$B${adr['pk']}"),
                         ('Pk_do', f"'FAN HESABI'!$C${adr['pk']}"), ('Pm_uf', f"'FAN HESABI'!$B${adr['pm']}"),
                         ('Pm_do', f"'FAN HESABI'!$C${adr['pm']}"), ('Pa_uf', f"'FAN HESABI'!$B${adr['pt']}"),
                         ('Pa_do', f"'FAN HESABI'!$C${adr['pt']}"), ('dp_uf', f"'FAN HESABI'!$B${adr['tp']}"),
                         ('dp_do', f"'FAN HESABI'!$C${adr['tp']}"), ('esp_uf', f"'FAN HESABI'!$B${adr['esps']}"),
                         ('esp_do', f"'FAN HESABI'!$C${adr['esps']}"), ('qf_fan', f"'FAN HESABI'!$B${adr['qf']}"),
                         ('sfp_uf', f"'FAN HESABI'!$B${adr['sfp']}"), ('sfp_do', f"'FAN HESABI'!$C${adr['sfp']}"),
                         ('sfk_uf', f"'FAN HESABI'!$B${adr['sinif']}"), ('sfk_do', f"'FAN HESABI'!$C${adr['sinif']}")):
        wb.defined_names[isim] = DefinedName(isim, attr_text=hucre_)
    return ws


def elektrik(wb):
    ws = wb.create_sheet('ELEKTRİK YÜKLERİ')
    ws['A1'] = 'ISITMA-SOĞUTMA VE HAVALANDIRMA CİHAZLARI ELEKTRİK YÜKÜ TABLOSU'
    ws['A1'].font = Font(name=F, size=13, bold=True)
    ws['A2'] = ('Bu tabloda YALNIZ ELEKTRİK GÜÇLERİ vardır; ısıtma/soğutma (ısıl) kapasiteleri bu tabloda yer almaz. '
                'Numaralar planda cihaz yanındaki daire içindeki numaralardır; alt satırlar (1.1, 1.2 …) cihazın '
                'içindeki elektrik tüketicileridir (2 fan motoru, damper motorları, kontrol panosu). İletken kesiti ve pano seçimi elektrik projesinde yapılacaktır.')
    ws['A2'].font = Font(name=F, size=9, italic=True)
    bas = ['NO', 'CİHAZ KODU', 'CİHAZ / ELEKTRİK TÜKETİCİSİ', 'ADET', 'BİRİM ELEKTRİK GÜCÜ (kW)',
           'KURULU ELEKTRİK GÜCÜ (kW)', 'GERİLİM (V)', 'cos φ', 'AKIM (A)', 'SİGORTA (A)']
    gen = [7, 12, 58, 8, 14, 14, 10, 8, 10, 11]
    for j, (b_, w) in enumerate(zip(bas, gen)):
        c = hucre(ws, f'{get_column_letter(j + 1)}4', b_, KALIN, BASLIK, hiz='center')
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(j + 1)].width = w
    ws.row_dimensions[4].height = 32
    K = "'KS HESABI'"
    r = 5
    no = 1
    sig = ('=INDEX({{6,10,16,20,25,32,40,50,63,80,100,125,160,200,250}},'
           'MATCH(TRUE,INDEX({{6,10,16,20,25,32,40,50,63,80,100,125,160,200,250}}>=I{r}*k_sig,0),0))')
    cihaz_satir = []

    def satir(no_, kod, ad, adet, birim, toplam, cos, kalin=False, birim_akim=False, monofaze=False):
        nonlocal r
        f_ = KALIN if kalin else SIYAH
        fill = TOPLAM if kalin else None
        hucre(ws, f'A{r}', no_, f_, fill, hiz='center')
        hucre(ws, f'B{r}', kod, f_, fill, hiz='center')
        hucre(ws, f'C{r}', ad, f_, fill)
        hucre(ws, f'D{r}', adet, f_, fill, '0', 'right')
        hucre(ws, f'E{r}', birim, f_, fill, '0.000', 'right')
        hucre(ws, f'F{r}', toplam.format(r=r), f_, fill, '0.00', 'right')
        hucre(ws, f'G{r}', 230 if monofaze else '=U_v', f_, fill, '0', 'right')
        hucre(ws, f'H{r}', f'={cos}', f_, fill, '0.00', 'right')
        guc = f'E{r}' if birim_akim else f'F{r}'
        akim = f'={guc}*1000/(G{r}*H{r})' if monofaze else f'={guc}*1000/(SQRT(3)*G{r}*H{r})'
        hucre(ws, f'I{r}', akim, f_, fill, '0.0', 'right')
        hucre(ws, f'J{r}', sig.format(r=r), f_, fill, '0', 'right')
        r += 1
        return r - 1

    for i in range(4):
        c = 'CDEF'[i]
        ks = r
        satir(no, f'KS-{i + 1}', 'ISI GERİ KAZANIMLI KLİMA SANTRALİ — SANTRAL PANOSU BESLEMESİ (TOPLAM)', 1,
              '=SUM(F{a}:F{b})'.replace('{a}', str(ks + 1)).replace('{b}', str(ks + 4)), '=D{r}*E{r}', 'cos_ks', True)
        cihaz_satir.append(ks)
        satir(f'{no}.1', f'KS-{i + 1}/ÜF', 'Üfleme fanı motoru — plug fan, IE4, frekans konvertörlü', '=n_fan', '=Pm_uf',
              '=D{r}*E{r}', 'cos_ks', birim_akim=True)
        satir(f'{no}.2', f'KS-{i + 1}/EF', 'Emiş / egzoz fanı motoru — plug fan, IE4, frekans konvertörlü', '=n_fan',
              '=Pm_do', '=D{r}*E{r}', 'cos_ks', birim_akim=True)
        satir(f'{no}.3', f'KS-{i + 1}/DM', 'Damper motorları — taze hava, egzoz, karışım, by-pass (230/24 V trafo, panodan)', 4, '=P_dmp',
              '=D{r}*E{r}', 'cos_ks', monofaze=True)
        satir(f'{no}.4', f'KS-{i + 1}/DDC', 'Santral kontrol (DDC) panosu (230 V)', 1, '=P_ddc', '=D{r}*E{r}', 'cos_ks', monofaze=True)
        no += 1
        for j in (1, 2):
            rr = satir(no, f'DÜ-{i + 1}.{j}', 'DX DIŞ ÜNİTE (ISI POMPASI) — kompresör + kondenser fanları', 1,
                       f'=ROUND(MAX({K}!{c}51/EER,{K}!{c}52*dus/COP),1)', '=D{r}*E{r}', 'cos_du', True)
            cihaz_satir.append(rr)
            no += 1
    son = r - 1
    hucre(ws, f'C{r}', 'TOPLAM KURULU ELEKTRİK GÜCÜ', KALIN, TOPLAM)
    hucre(ws, f'F{r}', '=' + '+'.join(f'F{x}' for x in cihaz_satir), KALIN, TOPLAM, '#,##0.0', 'right')
    hucre(ws, f'I{r}', '=' + '+'.join(f'I{x}' for x in cihaz_satir), KALIN, TOPLAM, '#,##0.0', 'right')
    for col in 'ABDEGHJ':
        hucre(ws, f'{col}{r}', None, fill=TOPLAM)
    ws[f'C{r + 2}'] = ('Dış ünite elektrik gücü = max(soğutma kapasitesi / EER ; ısıtma kapasitesi(−3 °C) / COP); üretici '
                       'seçiminde katalog elektrik gücü yazılacaktır.')
    ws[f'C{r + 2}'].font = Font(name=F, size=9, italic=True)
    ws.freeze_panes = 'D5'
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
        ('', '', 'DX soğutma bataryası ISIL kapasitesi', '={K}!{c}37', 'kW ısıl'),
        ('', '', 'DX ısıtma bataryası ISIL kapasitesi', '={K}!{c}45', 'kW ısıl'),
        ('', '', 'Yoğuşma suyu', '={K}!{c}36', 'l/h'),
        ('', '', 'Üfleme fanı (plug fan, 1 adet) debisi', '=qf_fan', 'm³/h'),
        ('', '', 'Üfleme fanı toplam basınç / dış statik basınç', '=TEXT(dp_uf,"0")&" / "&TEXT(esp_uf,"0")&" Pa"', ''),
        ('', '', 'Üfleme fanı motoru (IE4, frekans konvertörlü)', '=Pm_uf', 'kW elektrik'),
        ('', '', 'Emiş / egzoz fanı (plug fan, 1 adet) debisi', '=qf_fan', 'm³/h'),
        ('', '', 'Emiş fanı toplam basınç / dış statik basınç', '=TEXT(dp_do,"0")&" / "&TEXT(esp_do,"0")&" Pa"', ''),
        ('', '', 'Emiş / egzoz fanı motoru (IE4, frekans konvertörlü)', '=Pm_do', 'kW elektrik'),
        ('', '', 'Özgül fan gücü SFP (üfleme / emiş)', '=TEXT(sfp_uf,"0")&" / "&TEXT(sfp_do,"0")&" W/(m³/s)"', ''),
        ('', '', 'Filtre (taze hava / dönüş / üfleme)', 'G4 / G4 / F7', ''),
        ('', '', 'Dış ölçü (U × G × Y) yaklaşık', '830×545×220', 'cm'),
        ('DÜ', 'DX DIŞ ÜNİTE (HAVA KAYNAKLI ISI POMPASI)', 'Adet (santral başına)', '={K}!{c}50', 'adet'),
        ('', '', 'Modül soğutma ISIL kapasitesi (en az)', '={K}!{c}51', 'kW ısıl'),
        ('', '', 'Modül nominal ısıtma ISIL kapasitesi (en az)', '={K}!{c}52', 'kW ısıl'),
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
            fmt = '0%' if oz.startswith('Plakalı') else '#,##0.0' if birim.startswith('kW') else '#,##0'
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
    fan_hesabi(wb)
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
