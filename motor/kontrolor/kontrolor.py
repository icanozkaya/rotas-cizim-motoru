#!/usr/bin/env python3
"""ROTAŞ KONTROLÖR — üreten ajandan bağımsız onay denetimi (sıhhi tesisat kat planı + kolon şeması).

    python3 motor/kontrolor/kontrolor.py <dxf> --mimari <new_block.dxf(.xz) | mimari.dxf> --rapor <rapor.md>
        --png-yok           PNG kırpımı üretme
        --png-ust N         test + kat başına en çok N kırpım (varsayılan 12)
        --pencere JSON      genel mimari kaynak için kat pencereleri {"Z":[x0,y0,x1,y1],...} (kaynak koordinatı)
        --katman AD,AD      genel mimari kaynakta okunacak katmanlar (varsayılan: MIMARI/MKDU/DUVAR geçenler)
        --referans-yok      yan yana referans (new_block) kırpımı üretme
        --referans-kaydet   bu çalışmanın test sayılarını referans ölçümü olarak kaydet (new_block'un kendisi için)
                            -> motor/kontrolor/referans_new_block.json; raporda "Referans" sütunu; kolon numara/konumları
                            ve ÇM/BM yerleri de '_cizim' alanına yazılır (T12 yeni kolon, T13 makine yeri referansı)
        --tur sihhi|yerden  test takımı (varsayılan sihhi; yerden: yerden ısıtma planı + şema, `yerden.py`)
        --kat-pencere JSON  kontrol edilen çizimde kat paftası pencereleri {"Z":[x0,y0,x1,y1],...} (çerçevesiz dosya, ör.
                            new_block ısıtma şeridi); öteleme yazı eşleşmesiyle bulunur
        --excel XLSX        (yerden) hesap Excel'i: plan W ↔ Excel W tutarlılığı

denetle.py kontrollerine (MTY, ROTAS- öneki, köprü, kesişme, elektrik, yazı, lejant, audit) EK olarak kullanıcı
kurallarını ÖLÇEN testler (T01–T10, `testler.py`). Her bulgu: PASS/FAIL + koordinat + kırpılmış PNG (rapor klasörü
`<rapor>_png/`), FAIL kırpımları referans (kullanıcının new_block çizimi) ile yan yana. Sonuç: ONAY veya RED + madde listesi.
Protokol: `onay_protokolu.md`.
"""
import json
import os
import sys
import time
from collections import Counter, defaultdict

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import cizim as C  # noqa: E402
import mimari_bilgi as MB  # noqa: E402
import testler as T  # noqa: E402
import testler2 as T2  # noqa: E402

T.TEST_ADI.update(T2.TEST_ADI2)

KOK = os.path.dirname(os.path.dirname(BURASI))
REFERANS_JSON = os.path.join(BURASI, 'referans_new_block.json')


def goreli(p):
    try:
        return os.path.relpath(p, KOK)
    except ValueError:
        return p


def argumanlar(argv):
    o = dict(dxf=None, mimari=None, rapor=None, png=True, png_ust=12, pencere=None, katman=None, referans=True,
             referans_kaydet=False, tur='sihhi', kat_pencere=None, excel=None)
    it = iter(argv)
    for a in it:
        if a == '--mimari':
            o['mimari'] = next(it)
        elif a == '--rapor':
            o['rapor'] = next(it)
        elif a == '--png-yok':
            o['png'] = False
        elif a == '--png-ust':
            o['png_ust'] = int(next(it))
        elif a == '--pencere':
            o['pencere'] = json.loads(next(it))
        elif a == '--katman':
            o['katman'] = next(it).split(',')
        elif a == '--referans-yok':
            o['referans'] = False
        elif a == '--referans-kaydet':
            o['referans_kaydet'] = True
        elif a == '--tur':
            o['tur'] = next(it)
        elif a == '--kat-pencere':
            o['kat_pencere'] = {k: tuple(v) for k, v in json.loads(next(it)).items()}
        elif a == '--excel':
            o['excel'] = next(it)
        elif o['dxf'] is None:
            o['dxf'] = a
    if not o['dxf']:
        print(__doc__)
        sys.exit(1)
    if not o['rapor']:
        o['rapor'] = os.path.splitext(o['dxf'])[0] + '_KONTROLOR.md'
    return o


# ------------------------------------------------------------------ mimari + kat eşleme
def katlari_esle(cz, o, log):
    """{kat: (kat_bilgi_ötelenmiş, (dx,dy), eşleşme)} ; kaynak kayıtları A ve pencereleri"""
    kendisi = o['mimari'] is None
    if kendisi:
        A = MB.kayitlar_dxf(cz.msp)
        wins = dict(cz.kat_paftalari)
        log.append('mimari kaynak: dosyanın kendi MIMARI katmanları (öteleme yok)')
    else:
        A = MB.kaynak_oku(o['mimari'], o['katman'])
        wins = MB.kaynak_pencereleri(o['mimari'])
        if o['pencere']:
            wins = {k: tuple(v) for k, v in o['pencere'].items()}
        log.append('mimari kaynak: %s (%d kayıt)' % (goreli(o['mimari']), len(A)))
    if o.get('kat_pencere'):
        cz.kat_paftalari = dict(o['kat_pencere'])
        log.append('kat paftaları --kat-pencere ile verildi: %s' % sorted(cz.kat_paftalari))
    # kontrol edilen dosya kat paftasız (ör. new_block'un kendisi): pencereler kaynak pencereleri, öteleme 0
    if not cz.kat_paftalari and wins:
        cz.kat_paftalari = dict(wins)
        log.append('kat paftası çerçevesi yok: kaynak kat pencereleri kullanıldı (öteleme 0)')
    out = {}
    for k, cer in cz.kat_paftalari.items():
        if wins is None:
            # genel kaynak, pencere verilmemiş: tüm kaynak yazılarıyla öteleme bul, pencere = çerçeve geri ötelenmiş
            Rt = [a for a in A if a[0] == 'T']
            ot = C.oteleme_bul(cz, cer, Rt, None)
            if ot is None:
                log.append('kat %s: kaynakla eşleşme bulunamadı (atlandı)' % k)
                continue
            dx, dy, n = ot
            w = (cer[0] - dx, cer[1] - dy, cer[2] - dx, cer[3] - dy)
        else:
            if k not in wins:
                log.append('kat %s: kaynakta pencere yok (atlandı)' % k)
                continue
            w = wins[k]
            if kendisi or (cer[0] == w[0] and cer[1] == w[1]):
                dx, dy, n = 0.0, 0.0, 0
            else:
                R = [a for a in A if a[0] == 'T' and MB.M.inside(a[1][0], w)]
                ot = C.oteleme_bul(cz, cer, R, w) or C.oteleme_bul_cizgi(cz, cer, MB.M.recs_in(A, w), w)
                if ot is None:
                    log.append('kat %s: öteleme bulunamadı (atlandı)' % k)
                    continue
                dx, dy, n = ot
        t0 = time.time()
        kb = MB.kat_analiz(A, w, k)
        kbt = MB.tasi(kb, dx, dy)
        kbt['pencere'] = tuple(float(v) for v in cer)
        out[k] = (kbt, (dx, dy), n)
        log.append('kat %s: öteleme (%.1f, %.1f) %d yazı eşleşmesi; mahal %d (ıslak %d, ortak %d, balkon %d), daire %s, '
                   'armatür %d, betonarme %d — %.1f s' % (
                       k, dx, dy, n, len(kb['rooms']), sum(r['islak'] for r in kb['rooms']),
                       sum(r['ortak'] for r in kb['rooms']), sum(r['balkon'] for r in kb['rooms']),
                       sorted(kb['daire_poly']), len(kb['fx']), len(kb['cols']), time.time() - t0))
    return out, A


def mimari_yazi_poligonlari(kbt):
    """kaynak mimari yazılarından (ötelenmiş) kaba yazı kutuları — çizimde mimari yazı katmanı yoksa T07 için"""
    from shapely.geometry import Polygon
    import math
    out = []
    for (x, y), s, h, rot in kbt.get('mimari_yazi', []):
        if not s.strip() or h <= 0:
            continue
        w = len(s) * h * 0.6
        c, s_ = math.cos(math.radians(rot or 0)), math.sin(math.radians(rot or 0))
        pts = [(x + a * c - b * s_, y + a * s_ + b * c) for a, b in ((0, 0), (w, 0), (w, h), (0, h))]
        out.append((s, Polygon(pts), 'KAYNAK-MIMARI', h))
    return out


# ------------------------------------------------------------------ ana
def calistir(o):
    t0 = time.time()
    log = []
    cz = C.Cizim(o['dxf'])
    log.append('dosya: %s — çerçeve %d, kat paftası %s, şema paftası %s' % (
        goreli(o['dxf']), len(cz.cerceveler), sorted(cz.kat_paftalari), 'var' if cz.sema_paftasi else 'yok'))
    katlar, A = katlari_esle(cz, o, log)
    ref_json = {}
    if os.path.exists(REFERANS_JSON):
        try:
            ref_json = json.load(open(REFERANS_JSON, encoding='utf-8'))
        except Exception:
            ref_json = {}
    # kullanıcı referans çizimi kayıtları (kolon no/konum, ÇM/BM) yalnız new_block mimarisiyle anlamlı
    ref_cizim = ref_json.get('_cizim') if (o['mimari'] and MB.new_block_mi(o['mimari'])) else None
    for k, (kbt, dxdy, n) in katlar.items():
        if kbt.get('daire_kapi_degisen'):
            log.append('kat %s: kapı komşuluğuyla daire ataması düzeltildi: %s' % (
                k, ', '.join('%s D%s→D%s' % (a.replace('\n', ' '), b, c) for a, b, c in kbt['daire_kapi_degisen'])))
    bulgular = []

    def guvenli(ad, f, *a, kat=None):
        try:
            return f(*a)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return [T.Bulgu(ad, 'INFO', 'test çöktü: %s' % ex, kat)]

    if o['tur'] == 'yerden':
        import yerden as Y
        T.TEST_ADI.clear()
        T.TEST_ADI.update(Y.TEST_ADI)
        for k in sorted(katlar, key=T2.kat_sira):
            kbt, dxdy, n = katlar[k]
            bulgular += guvenli('Y', Y.kat_testleri, cz, k, kbt, kat=k)
        bulgular += guvenli('Y06', Y.y06_plan_excel, cz, katlar, o.get('excel'))
        bulgular += guvenli('T16', T2.t16_sizinti_renk, cz)
        bulgular += guvenli('T17', T2.t17_pafta, cz, 'yerden')
        bulgular += T.t11_denetle(o['dxf'])
    else:
        for k in sorted(katlar, key=T2.kat_sira):
            kbt, dxdy, n = katlar[k]
            for f in T.KAT_TESTLERI:
                bulgular += guvenli(f.__name__[:3].upper(), f, cz, k, kbt, kat=k)
            bulgular += guvenli('T07', T.t07_etiketler, cz, k, kbt, mimari_yazi_poligonlari(kbt), kat=k)
            bulgular += guvenli('T13', T2.t13_makine_yeri, cz, k, kbt, ref_cizim, kat=k)
            bulgular += guvenli('T14', T2.t14_aspirator_notu, cz, k, kbt, kat=k)
            bulgular += guvenli('T15', T2.t15_penceresiz_aspirator, cz, k, kbt, kat=k)
        bulgular += guvenli('T12', T2.t12_kolon_sureklilik, cz, katlar, ref_cizim)
        bulgular += guvenli('T08', T.t08_sema_sayac, cz, kat='ŞEMA')
        bulgular += T.t11_denetle(o['dxf'])
        bulgular += guvenli('T16', T2.t16_sizinti_renk, cz)
        bulgular += guvenli('T17', T2.t17_pafta, cz, 'sihhi')

    # ---- PNG
    png_klasor = os.path.splitext(o['rapor'])[0] + '_png'
    if o['png']:
        os.makedirs(png_klasor, exist_ok=True)
        import kirp
        ciz = kirp.Cizici(cz.doc)
        ref = None
        if o['referans'] and o['mimari'] and MB.new_block_mi(o['mimari']) and 'new_block' not in os.path.basename(o['dxf']):
            try:
                import ezdxf
                MB.M.ensure_src()
                ref = kirp.Cizici(ezdxf.readfile(MB.M.SRC), 'new_block')
            except Exception as ex:
                log.append('referans çizim okunamadı: %s' % ex)
        say = Counter()
        for b in bulgular:
            if b.durum != 'FAIL' or not b.pencere:
                continue
            say[(b.test, b.kat)] += 1          # test + kat başına en çok png_ust kırpım
            if say[(b.test, b.kat)] > o['png_ust']:
                continue
            ad = '%s_%s_%02d.png' % (b.test, (b.kat or 'G').replace('Ş', 'S'), say[(b.test, b.kat)])
            yol = os.path.join(png_klasor, ad)
            try:
                ciz.kirp(b.pencere, yol, b.noktalar, '%s %s | %s' % (b.test, b.kat or '', b.mesaj))
                if ref is not None and b.kat in katlar:
                    dx, dy = katlar[b.kat][1]
                    w = b.pencere
                    rw = (w[0] - dx, w[1] - dy, w[2] - dx, w[3] - dy)
                    ryol = os.path.join(png_klasor, ad.replace('.png', '_ref.png'))
                    ref.kirp(rw, ryol, [], 'REFERANS new_block %s' % b.kat)
                    kirp.yan_yana(yol, ryol, yol)
                    os.remove(ryol)
                b.png = os.path.relpath(yol, os.path.dirname(os.path.abspath(o['rapor'])))
            except Exception as ex:
                log.append('PNG üretilemedi %s: %s' % (ad, ex))
        # genel görünüm: kat paftaları + şema
        for k, (kbt, dxdy, n) in katlar.items():
            yol = os.path.join(png_klasor, 'GENEL_KAT_%s.png' % k)
            try:
                ciz.kirp(kbt['pencere'], yol, [], 'KAT %s genel görünüm' % k, genislik_in=11, dpi=110)
            except Exception:
                pass
        if cz.sema_paftasi:
            try:
                ciz.kirp(cz.sema_paftasi, os.path.join(png_klasor, 'GENEL_SEMA.png'), [], 'KOLON ŞEMASI genel görünüm',
                         genislik_in=16, dpi=110)
            except Exception:
                pass
    if o['referans_kaydet']:
        ref = dict(ref_json)
        ref['_tarih'] = time.strftime('%d.%m.%Y')
        ref['_dosya'] = os.path.basename(o['dxf'])
        anahtar = 'yerden' if o['tur'] == 'yerden' else None
        sayilar = {t: dict(fail=sum(1 for b in bulgular if b.test == t and b.durum == 'FAIL'),
                           info=sum(1 for b in bulgular if b.test == t and b.durum == 'INFO')) for t in T.TEST_ADI}
        if anahtar:
            ref['_yerden'] = sayilar
            try:
                import yerden as Y
                ref['_yerden_cizim'] = Y.referans_cikar(cz, katlar)
            except Exception as ex:
                log.append('yerden referans kaydı alınamadı: %s' % ex)
        else:
            ref.update(sayilar)
            ref['_cizim'] = T2.referans_cikar(cz, katlar)
        with open(REFERANS_JSON, 'w', encoding='utf-8') as f:
            json.dump(ref, f, ensure_ascii=False, indent=1)
        log.append('referans ölçümü kaydedildi: %s' % goreli(REFERANS_JSON))
    rapor_yaz(o, cz, katlar, bulgular, log, png_klasor if o['png'] else None, time.time() - t0)
    return bulgular


def rapor_yaz(o, cz, katlar, bulgular, log, png_klasor, sure):
    fail = [b for b in bulgular if b.durum == 'FAIL']
    testler = sorted(T.TEST_ADI)
    md = ['# KONTROLÖR RAPORU — %s' % os.path.basename(o['dxf']), '',
          'Üretildi: %s — `python3 motor/kontrolor/kontrolor.py %s`' % (time.strftime('%d.%m.%Y %H:%M'), ' '.join(sys.argv[1:])),
          '', '## SONUÇ: **%s**' % ('ONAY' if not fail else 'RED — %d madde' % len(fail)), '']
    if fail:
        md.append('Düzeltme listesi (üreten ajana geri):')
        grup = defaultdict(list)
        for b in fail:
            grup[b.test].append(b)
        i = 0
        for t in testler:
            if t not in grup:
                continue
            for b in grup[t][:6]:
                i += 1
                md.append('%d. [%s%s] %s%s' % (i, t, (' ' + b.kat) if b.kat else '', b.mesaj,
                                                (' @ %s' % (T._xy(b.nokta),)) if b.nokta else ''))
            if len(grup[t]) > 6:
                md.append('   … %s için toplam %d bulgu (ayrıntı aşağıda)' % (t, len(grup[t])))
        md.append('')
    ref = {}
    if os.path.exists(REFERANS_JSON):
        try:
            ref = json.load(open(REFERANS_JSON, encoding='utf-8'))
        except Exception:
            ref = {}
    if o.get('tur') == 'yerden':
        ref = dict(ref.get('_yerden', {}), _tarih=ref.get('_tarih', ''))
    aciklama = ref.get('_aciklama', {}) if isinstance(ref.get('_aciklama'), dict) else {}
    md += ['## Özet', '', '| Test | Ne ölçer | Sonuç | FAIL | INFO | Referans new_block FAIL/INFO (aynı ölçüm) |',
           '|---|---|---|---|---|---|']
    if o.get('tur') == 'yerden':
        aciklama = json.load(open(REFERANS_JSON, encoding='utf-8')).get('_aciklama_yerden', {}) if os.path.exists(REFERANS_JSON) else {}
    for t in testler:
        bs = [b for b in bulgular if b.test == t]
        nf = sum(1 for b in bs if b.durum == 'FAIL')
        ni = sum(1 for b in bs if b.durum == 'INFO')
        if not bs:
            durum = '— (çalışmadı)'
        else:
            durum = '✗ FAIL' if nf else ('✓ PASS' if any(b.durum == 'PASS' for b in bs) else 'bilgi')
        r = ref.get(t)
        rs = ('%d / %d' % (r['fail'], r['info'])) if isinstance(r, dict) else '-'
        if aciklama.get(t):
            rs += ' — ' + aciklama[t]
        md.append('| %s | %s | %s | %d | %d | %s |' % (t, T.TEST_ADI[t], durum, nf, ni, rs))
    if ref:
        md.append('')
        md.append('Referans sütunu: kullanıcının kendi `new_block.dxf` çizimi aynı testlerden geçirildiğinde çıkan sayılar '
                  '(%s). Referansın kendisinde de görülen türden bulgular (ör. T07 etiket-hat, T02 serbest açı) tarz '
                  'farkı değil kural C ihlali olarak listelenir; T11 MTY sayıları referans için beklenen durumdur.' % ref.get('_tarih', ''))
    md += ['', '## Dosya ve mimari eşleme', ''] + ['- %s' % l for l in log] + ['', 'Süre %.0f s.' % sure, '']
    md += ['## Ayrıntı (koordinatlar çizim birimi, cm)', '']
    for t in testler:
        bs = [b for b in bulgular if b.test == t]
        if not bs:
            continue
        md.append('### %s — %s' % (t, T.TEST_ADI[t]))
        md.append('')
        for b in bs:
            sat = '- **%s**%s: %s' % (b.durum, (' [%s]' % b.kat) if b.kat else '', b.mesaj)
            if b.nokta:
                sat += ' @ (%d, %d)' % T._xy(b.nokta)
            if b.png:
                sat += '  \n  ![%s](%s)' % (b.test, b.png.replace(' ', '%20'))
            md.append(sat)
        md.append('')
    if png_klasor:
        md += ['## Genel görünümler', '']
        rel = os.path.relpath(png_klasor, os.path.dirname(os.path.abspath(o['rapor'])))
        for k in katlar:
            md.append('- KAT %s: ![](%s/GENEL_KAT_%s.png)' % (k, rel, k))
        if cz.sema_paftasi:
            md.append('- ŞEMA: ![](%s/GENEL_SEMA.png)' % rel)
        md.append('')
    md += ['## Eşikler', '',
           '- T01 balkon süzgeci–iniş hat boyu ≤ %.0f cm; süzgecin bağlı olduğu ağda pis su katmanı/kolonu varsa FAIL.' % T.BALKON_SUZGEC_MAX,
           '- T02 armatür→kolon branşman yolu ≤ %.0f cm; parça açıları {0,45,90} ± %.0f°; yol armatür mahalli + kolon mahalli '
           '(duvar payı %.0f cm) dışına > 40 cm çıkarsa FAIL; WC/LV/DUŞ/EVİYE %.0f cm içinde hat yoksa FAIL.' % (
               T.BRANSMAN_MAX, T.ACI_TOL, T.DUVAR_DIBI, T.ARMATUR_BAG_TOL),
           '- T03 mahal poligonunun %.0f cm içeri çekilmiş bölgesinde ≥ %.0f cm pis su hattı → FAIL.' % (T.DUVAR_DIBI, T.CAPRAZ_MIN),
           '- T04 sıcak su bağlı ağı en çok örtüştüğü daire poligonu (mahaller + 20 cm duvar payı) dışında > %.0f cm → FAIL; '
           'kombiye 80 cm içinde başlamıyorsa FAIL.' % T.DAIRE_DISI_MIN,
           '- T05 sıcak parçası (≥ 60 cm) boyunca soğuğa mesafe %.0f–%.0f cm olan örnek oranı ≥ %%%.0f; ofset std ≤ %.1f cm; '
           'sıcak–soğuk kesişme (uçtan 15 cm dışı) FAIL.' % (T.PARALEL_ARALIK[0], T.PARALEL_ARALIK[1], 100 * T.PARALEL_ORAN, T.OFSET_STD),
           '- T06 koridor (antre-kor. / merdiven / hol) içindeki temiz su parçası: duvara mesafe / koridor genişliği < %.2f → FAIL.' % T.KORIDOR_ORTA_ORAN,
           '- T07 yazı kutuları ezdxf yazı tipi ölçüsüyle; herhangi örtüşme (> 0,2 cm²) FAIL; hat yazı kutusundan ≥ 3 cm geçiyorsa FAIL; '
           'çap etiketi yüksekliği ortanca %.0f–%.0f.' % T.ETIKET_H,
           '- T08 sayaç sembolü y ≥ 1. kat bandı çizgisi → FAIL; x daire bloklarının (D1..) solunda değilse FAIL; "SAYAÇ (KAPIDA)" yazısı FAIL.',
           '- T09 ıslak mahal poligonunda süzgeç sembolü (çizim + mimari ızgara, 15 cm kümeli) sayısı ≠ 1 → FAIL.',
           '- T10 kolon sembolü ıslak mahal (20 cm pay) dışında / betonarme içinde / en yakın köşeye > %.0f cm → FAIL.' % T.KOLON_KOSE_MAX,
           '- T11 `motor/deneme/denetim/denetle.py` ile aynı sayılar.', '']
    os.makedirs(os.path.dirname(os.path.abspath(o['rapor'])), exist_ok=True)
    with open(o['rapor'], 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print('SONUÇ:', 'ONAY' if not fail else 'RED (%d madde)' % len(fail))
    for t in testler:
        nf = sum(1 for b in bulgular if b.test == t and b.durum == 'FAIL')
        print('  %s %s %s' % (t, '✗' if nf else '✓', nf or ''))
    print('Rapor:', goreli(o['rapor']))


if __name__ == '__main__':
    calistir(argumanlar(sys.argv[1:]))
