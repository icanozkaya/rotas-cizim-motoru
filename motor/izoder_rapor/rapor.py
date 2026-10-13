# -*- coding: utf-8 -*-
"""İZODER çizelge düzeninde ısı kaybı + radyatör seçimi PDF raporu.
Kullanım: python3 rapor.py ISI_KAYBI_HESABI.xls RADYATOR.xlsx cikti.pdf"""
import sys, html, asyncio
from oku import isi_kaybi, radyator, carpan, kat

P = dict(sahip='TEKİN KARAKUŞ VE HİSSEDARLARI', amac='Apartmanlar', katadet='8', il='İstanbul', ilce='Güngören',
         adres='M. Nesih Özmen Mahallesi, Göksel Sokak, Güngören / İstanbul', pafta='69', ada='944', parsel='343',
         blok='B1 BLOK', muh='BAYRAM GENÇ', unvan='MAKİNA MÜHENDİSİ', sicil='56858', kurulus='ROTAŞ MÜHENDİSLİK')

BIL = {'ÇP': 'Pencere', 'DK': 'Dış Kapı', 'DD': 'Dış Duvar', 'İK': 'İç Kapı', 'İD': 'İç Duvar', 'DÖ': 'Döşeme'}
KAT_SIRA = ['ZEMİN KAT', 'NORMAL KATLAR (1-2-3-4-5)', 'ÇATI KATI']


def n(v, d=2, bos=''):
    if v is None: return bos
    s = f'{v:,.{d}f}'
    return s.replace(',', '#').replace('.', ',').replace('#', '.')


def e(s): return html.escape(str(s))


CSS = """
@page { size: A4; margin: 12mm 10mm 12mm 10mm; }
* { box-sizing: border-box; }
body { font-family: 'Liberation Sans', 'Carlito', Arial, sans-serif; font-size: 8.4pt; color: #000; margin: 0; }
.sayfa { page-break-after: always; }
.sayfa:last-child { page-break-after: auto; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 0.6pt solid #000; padding: 1.6pt 3pt; vertical-align: middle; }
th { font-weight: bold; text-align: center; }
.bas { margin-bottom: 4mm; }
.bas td { height: 15mm; }
.bas .logo { width: 25%; text-align: center; }
.bas .ttl { text-align: center; font-weight: bold; font-size: 12pt; }
.lg1 { font-weight: 800; font-size: 13pt; letter-spacing: .5pt; color: #0b5ea8; line-height: 1.05; }
.lg2 { font-size: 6.4pt; color: #444; letter-spacing: .3pt; }
.lg3 { font-size: 8pt; font-weight: bold; color: #0b5ea8; }
.gr { background: #e7e6e6; }
.c { text-align: center; } .r { text-align: right; } .b { font-weight: bold; }
.top td { color: #c00000; font-weight: bold; border-bottom: 1.4pt solid #c00000; }
.ara td { font-weight: bold; }
.blk { margin-bottom: 5mm; page-break-inside: avoid; }
.ik th { font-size: 7.4pt; font-weight: bold; background: #fff; }
.ik td { font-size: 7.8pt; }
.mh td { font-weight: bold; background: #e7e6e6; }
.not td { font-size: 8pt; line-height: 1.45; background: #f3f2f2; }
.sp { height: 4mm; }
.k { font-weight: bold; }
"""


def baslik(t):
    return f"""<table class="bas"><tr><td class="ttl">{t}</td></tr></table>"""


def proje_bilgileri():
    return f"""<div class="sayfa">{baslik('PROJE BİLGİLERİ')}
<table><tr><th colspan="3">BİNANIN</th></tr>
<tr><td style="width:33%"><span class="k">Sahibi :</span> {e(P['sahip'])}</td><td style="width:34%"><span class="k">Kullanma Amacı :</span> {P['amac']}</td><td><span class="k">Kat Adedi :</span> {P['katadet']}</td></tr></table>
<div class="sp"></div>
<table><tr><th colspan="3">ARSANIN</th></tr>
<tr><td style="width:33%"><span class="k">İli :</span> {P['il']}</td><td style="width:34%"><span class="k">İlçesi :</span> {P['ilce']}</td><td><span class="k">Açık Adresi :</span> {e(P['adres'])}</td></tr>
<tr><td><span class="k">Pafta :</span> {P['pafta']}</td><td><span class="k">Ada :</span> {P['ada']}</td><td><span class="k">Parsel :</span> {P['parsel']}</td></tr></table>
<div class="sp"></div>
<table><tr><th style="width:50%">Isı Kaybı Hesabını Yapanın</th><th>ONAY</th></tr>
<tr><td><span class="k">Adı Soyadı :</span> {P['muh']}</td><td rowspan="5"></td></tr>
<tr><td><span class="k">Ünvanı :</span> {P['unvan']}</td></tr>
<tr><td><span class="k">Sicil No :</span> {P['sicil']}</td></tr>
<tr><td><span class="k">Kuruluşu :</span> {P['kurulus']}</td></tr>
<tr><td style="height:12mm"><span class="k">İmza :</span></td></tr></table></div>"""


def genel(R, G):
    ti = {}
    for r in R: ti.setdefault(r['ad'], r['ti'])
    ub = {}
    for r in R:
        for x in r['el']: ub.setdefault(x['k'], set()).add(x['U'])
    sira = ['DD', 'ÇP', 'DK', 'İD', 'İK', 'DÖ']
    rows_u = ''.join(f"<tr><td class='c b'>{k}</td><td>{BIL.get(k, k)}</td><td class='c'>{' / '.join(n(u, 3) for u in sorted(ub[k], reverse=True))}</td></tr>" for k in sira if k in ub)
    rows_t = ''.join(f"<tr><td>{e(a)}</td><td class='c'>{n(t, 0)}</td></tr>" for a, t in ti.items())
    return f"""<div class="sayfa">{baslik('Isı Kaybı Hesabı Genel Bilgiler Çizelgesi')}
<table><tr><th colspan="2">HESAP ESASLARI</th></tr>
<tr><td style="width:50%" class="b">Hesap Yöntemi</td><td>TS 2164 Kalorifer Tesisatı Projelendirme Kuralları</td></tr>
<tr><td class="b">Yapıldığı Yer</td><td>{e(G['yer'])}</td></tr>
<tr><td class="b">Dış Hava Sıcaklığı</td><td>{n(G['tdis'], 0)} °C</td></tr>
<tr><td class="b">Su Gidiş / Dönüş Sıcaklığı</td><td>{n(G['tg'], 0)} / {n(G['td'], 0)} °C</td></tr>
<tr><td class="b">Isıtma Sistemi</td><td>Pompalı sıcak sulu merkezi ısıtma, panel radyatör</td></tr></table>
<div class="sp"></div>
<table style="width:100%"><tr><td style="border:none;padding:0;width:49%;vertical-align:top">
<table><tr><th colspan="3">YAPI BİLEŞENLERİ</th></tr><tr><th style="width:18%">İşaret</th><th>Bileşen</th><th style="width:34%">U (W/m²K)</th></tr>{rows_u}</table>
</td><td style="border:none;width:2%"></td><td style="border:none;padding:0;vertical-align:top">
<table><tr><th colspan="2">MAHAL İÇ SICAKLIKLARI</th></tr><tr><th>Mahal</th><th style="width:34%">Sıcaklık (°C)</th></tr>{rows_t}</table>
</td></tr></table>
<div class="sp"></div>
<table class="not"><tr><td>
<b>Q = A × U × ΔT</b> (W) : artırımsız iletim ısı kaybı<br>
<b>Qt = Q × Z</b> , <b>Z = 1 + (Zd + Zw + Zh)</b> : Zd birleşik artırım, Zw kat yüksekliği artırımı, Zh yön artırımı<br>
<b>Qs = ΣL × a × H × ΔT × R × Ze</b> (W) : sızıntı (enfiltrasyon) ısı kaybı — L: açılır doğrama derz uzunluğu (m), a: sızdırma katsayısı, H: bina durum katsayısı, R: oda durum katsayısı, Ze: köşe pencere katsayısı<br>
<b>Q<sub>toplam</sub> = ΣQt + Qs</b> (W)<br>
Normal kat (1-2-3-4-5) mahalleri her katta aynı olduğundan bir kez hesaplanmış, bina toplamında 5 kat ile çarpılmıştır.
</td></tr></table></div>"""


def mahal_blok(r):
    rows = ''.join(f"""<tr><td class='c b'>{x['k']}</td><td class='r'>{n(x['L'])}</td><td class='r'>{n(x['H'])}</td><td class='r'>{n(x['Atop'])}</td><td class='c'>{n(x['n'], 0)}</td>
<td class='r'>{n(x['Ac'])}</td><td class='r'>{n(x['A'])}</td><td class='r'>{n(x['U'], 3)}</td><td class='r'>{n(x['dT'], 0)}</td><td class='r'>{n(x['Q'])}</td>
<td class='c'>{n(x['Zd'], 0)}</td><td class='c'>{n(x['Zw'], 0)}</td><td class='c'>{n(x['Zh'], 0)}</td><td class='r'>{n(x['Z'])}</td><td class='r'>{n(x['Qt'])}</td></tr>""" for x in r['el'])
    q = r['qs']
    tek = ' — 1., 2., 3., 4. ve 5. normal katlarda aynı' if r['no'].startswith('1-2-3-4-5') else ''
    return f"""<table class="ik blk" style="table-layout:fixed"><colgroup><col style="width:6%"><col style="width:6.5%"><col style="width:6.5%"><col style="width:6.5%"><col style="width:5%"><col style="width:7%"><col style="width:7%"><col style="width:7%"><col style="width:5.5%"><col style="width:8%"><col style="width:5%"><col style="width:5%"><col style="width:5%"><col style="width:6%"><col style="width:9%"></colgroup>
<tr class="mh"><td colspan="15">Mahal No: {e(r['no'])} &nbsp;&nbsp; {e(r['ad'])} &nbsp;&nbsp; θi = {n(r['ti'], 0)} °C{tek}</td></tr>
{rows}
<tr class="ara"><td colspan="14">İletim ile gerçekleşen ısı kaybı toplamı ΣQt</td><td class="r">{n(r['qt'])}</td></tr>
<tr><td colspan="14">Sızıntı ısı kaybı Qs = ΣL × a × H × ΔT × R × Ze = {n(q['L'])} × {n(q['a'])} × {n(q['Hk'])} × {n(q['dT'], 0)} × {n(q['R'])} × {n(q['Ze'])}</td><td class="r">{n(q['Q'])}</td></tr>
<tr class="top"><td colspan="14">TOPLAM ISI KAYBI</td><td class="r">{n(r['top'])}</td></tr></table>"""


IK_TH = """<table class="ik" style="margin-bottom:2mm;table-layout:fixed"><colgroup><col style="width:6%"><col style="width:6.5%"><col style="width:6.5%"><col style="width:6.5%"><col style="width:5%"><col style="width:7%"><col style="width:7%"><col style="width:7%"><col style="width:5.5%"><col style="width:8%"><col style="width:5%"><col style="width:5%"><col style="width:5%"><col style="width:6%"><col style="width:9%"></colgroup><tr><th rowspan="2" style="width:6%">İşaret</th><th colspan="6">Alan Hesabı</th><th colspan="4">Isı Kaybı Hesabı</th><th colspan="4">Artırımlar</th></tr>
<tr><th style="width:6.5%">Uzunluk<br>(m)</th><th style="width:6.5%">Yükseklik<br>(m)</th><th style="width:6.5%">Toplam<br>Alan (m²)</th><th style="width:5%">Adet</th><th style="width:7%">Çıkarılan<br>Alan (m²)</th><th style="width:7%">A<br>(m²)</th>
<th style="width:7%">U<br>(W/m²K)</th><th style="width:5.5%">ΔT<br>(K)</th><th style="width:8%">Q<br>(W)</th><th style="width:5%">Zd<br>(%)</th><th style="width:5%">Zw<br>(%)</th><th style="width:5%">Zh<br>(%)</th><th style="width:6%">Z<br>(1+%)</th><th style="width:9%">Qt<br>(W)</th></tr></table>"""


def mahaller(R):
    out = []
    for kt in KAT_SIRA:
        rs = [r for r in R if kat(r['no']) == kt]
        pages, cur, h = [], [], 0
        for r in rs:
            rh = len(r['el']) + 5
            if cur and h + rh > 52: pages.append(cur); cur, h = [], 0
            cur.append(r); h += rh
        if cur: pages.append(cur)
        for pg in pages:
            out.append(f"<div class='sayfa'>{baslik('Mahal Isı Kaybı Hesaplama Çizelgesi<br><span style=\"font-size:9.5pt\">' + kt + '</span>')}{IK_TH}{''.join(mahal_blok(r) for r in pg)}</div>")
    return ''.join(out)


def radyator_cizelge(Ra, G):
    out = ''
    th = """<tr><th rowspan="2" style="width:13%">Mahal No</th><th rowspan="2">Mahal Adı</th><th rowspan="2" style="width:7%">Oda Sıc.<br>(°C)</th><th rowspan="2" style="width:10%">Isı Kaybı<br>(W)</th>
<th colspan="5">Seçilen Radyatör</th><th rowspan="2" style="width:9%">Tipi</th></tr>
<tr><th style="width:13%">Modeli</th><th style="width:7%">Boyu<br>(m)</th><th style="width:6%">Adet</th><th style="width:9%">Birim Kap.<br>(W)</th><th style="width:10%">Toplam Kap.<br>(W)</th></tr>"""
    body = ''
    for kt in KAT_SIRA:
        rs = [x for x in Ra if kat(x['no']) == kt]
        if not rs: continue
        body += f"<tr class='mh'><td colspan='10'>{kt}</td></tr>"
        for x in rs:
            body += f"""<tr><td>{e(x['no'])}</td><td>{e(x['ad'])}</td><td class='c'>{n(x['ti'], 0)}</td><td class='r'>{n(x['q'])}</td><td class='c'>{e(x['model'])}</td>
<td class='c'>{n(x['boy'], 2)}</td><td class='c'>{x['adet']}</td><td class='r'>{n(x['ver'])}</td><td class='r'>{n(x['ver'] * x['adet'])}</td><td class='c'>{e(x['tip'])}</td></tr>"""
        q = sum(x['q'] for x in rs); c = sum(x['ver'] * x['adet'] for x in rs)
        body += f"<tr class='ara'><td colspan='3'>KAT TOPLAMI{' (bir kat)' if 'NORMAL' in kt else ''}</td><td class='r'>{n(q)}</td><td colspan='4'></td><td class='r'>{n(c)}</td><td></td></tr>"
    tq = sum(x['q'] * carpan(x['no']) for x in Ra); tc = sum(x['ver'] * x['adet'] * carpan(x['no']) for x in Ra)
    body += f"<tr class='top'><td colspan='3'>BLOK TOPLAMI (normal katlar ×5)</td><td class='r'>{n(tq)}</td><td colspan='4'></td><td class='r'>{n(tc)}</td><td></td></tr>"
    info = f"""<table class="ik" style="margin-bottom:3mm"><tr><th>Yapıldığı Yer</th><th>Dış Sıcaklık (°C)</th><th>Su Gidiş Sıcaklığı (°C)</th><th>Su Dönüş Sıcaklığı (°C)</th></tr>
<tr><td class='c'>{e(G['yer'])}</td><td class='c'>{n(G['tdis'], 0)}</td><td class='c'>{n(G['tg'], 0)}</td><td class='c'>{n(G['td'], 0)}</td></tr></table>"""
    return f"<div class='sayfa'>{baslik('Radyatör Seçim Çizelgesi')}{info}<table class='ik'>{th}{body}</table></div>"


def ozet(R, Ra):
    body = ''
    TQ = TC = 0
    for kt in KAT_SIRA:
        rs = [r for r in R if kat(r['no']) == kt]; ra = [x for x in Ra if kat(x['no']) == kt]
        k = 5 if 'NORMAL' in kt else 1
        q1 = sum(r['top'] for r in rs); c1 = sum(x['ver'] * x['adet'] for x in ra)
        TQ += q1 * k; TC += c1 * k
        body += f"<tr><td>{kt}</td><td class='c'>{len(rs)}</td><td class='r'>{n(q1)}</td><td class='c'>{k}</td><td class='r'>{n(q1 * k)}</td><td class='r'>{n(c1 * k)}</td></tr>"
    body += f"<tr class='top'><td colspan='4'>{P['blok']} TOPLAMI</td><td class='r'>{n(TQ)}</td><td class='r'>{n(TC)}</td></tr>"
    return f"""<div class='sayfa'>{baslik('Isı Kaybı ve Radyatör Kapasitesi Özet Çizelgesi')}
<table class='ik'><tr><th>Kat</th><th style="width:11%">Mahal Sayısı</th><th style="width:15%">Bir Kat Isı Kaybı<br>(W)</th><th style="width:10%">Kat Adedi</th><th style="width:16%">Toplam Isı Kaybı<br>(W)</th><th style="width:17%">Radyatör Kapasitesi<br>(W)</th></tr>{body}</table>
<div class='sp'></div>
<table class='not'><tr><td>{P['blok']} toplam ısı kaybı Q = {n(TQ)} W = {n(TQ / 1000)} kW bulunmuştur.<br>
Mahallere seçilen panel radyatörlerin toplam ısıl kapasitesi {n(TC)} W = {n(TC / 1000)} kW olup her mahalde radyatör kapasitesi mahal ısı kaybına eşit veya büyüktür.</td></tr></table></div>"""


async def pdf(htmlstr, out):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        await pg.set_content(htmlstr, wait_until='load')
        await pg.pdf(path=out, format='A4', print_background=True, prefer_css_page_size=True)
        await b.close()


def main(xls, xlsx, out):
    R = isi_kaybi(xls); G, Ra = radyator(xlsx)
    # ısı kaybı cetvelinde çatı katı 13-14 nolu odalar "Ç 11 / Ç 12" diye yazılmış; radyatör çizelgesindeki numara esas alınır
    gor = set()
    for r in R:
        if r['no'] in gor:
            m = [x for x in Ra if kat(x['no']) == kat(r['no']) and abs(x['q'] - r['top']) < 0.01 and x['no'] not in gor]
            if m: r['no'] = m[0]['no']
        gor.add(r['no'])
    for r in R:
        assert r['top'] is not None and abs(sum(x['Qt'] for x in r['el']) - r['qt']) < 0.01
    h = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{proje_bilgileri()}{genel(R, G)}{mahaller(R)}{radyator_cizelge(Ra, G)}{ozet(R, Ra)}</body></html>"
    open(out.replace('.pdf', '.html'), 'w').write(h)
    asyncio.run(pdf(h, out))


if __name__ == '__main__':
    main(*sys.argv[1:4])
