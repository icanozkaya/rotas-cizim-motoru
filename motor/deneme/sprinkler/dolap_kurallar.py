# -*- coding: utf-8 -*-
"""Yangın dolabı kuralları. Kaynak: kutuphane/arastirma/06_YANGIN.md §5 (TS EN 671-1, BYKHY Md. 94), §10 (Md. 92).
Değerler burada toplanır, koda dağıtılmaz. Girdi JSON'daki 'dolap' sözlüğü bunları ezebilir.
Uzunluk: plan cm, hesap m / bar / l/dk."""

VARSAYILAN = dict(
    tip='TS EN 671-1',          # yarı sert hortum makaralı (eğitimsiz kullanıcı)          06 §5.2 ✅
    hortum_m=30.0,              # Ø25 mm, en fazla 30 m (TS EN 694)                         06 §5.2 ✅
    jet_m=5.0,                  # lüle menzili ≈3–5 m; hortum boyuna eklenir                06 §5.3 ⚠
    aralik_m=30.0,              # dolaplar arası en fazla 30 m ...                          06 §5.2 ✅
    aralik_sprinkler_m=45.0,    # ... sprinkler (ve katlarda itfaiye su alma ağzı) varsa 45 m
    debi_lpm=100.0,             # dolap tasarım debisi                                      06 §5.2 ✅
    basinc_bar=4.0,             # tasarım basıncı 400 kPa (dolap girişinde kabul)          06 §5.2 ✅
    p_max_bar=9.0,              # lülede 9 bar üstünde basınç düşürücü                     06 §5.2 ✅
    eszamanli=2,                # aynı anda çalışan dolap (LH/OH pratiği, Ek-8/C teyit)   06 §5.3 ⚠, §10.3
    sure_dk=60,                 # OH süre (LH 30, HH 90)                                    06 §10.1 ✅
    kolon_dn=50,                # dolap kolonu en az DN50                                   06 §5.2 ⚠
    baglanti_dn=32,             # dolap bağlantısı DN25–DN32                                06 §5.2 ⚠
    besleme_dn=50,              # kat yatay dolap besleme hattı (kolon çapında)
    montaj_m=1.30,              # vana / makara ekseni zeminden 1,2–1,5 m                   06 §5.2 ⚠
    govde_g=72.0,               # plan sembolü gövdesi 72 x 20 cm (Aselsan lejantı; 06 §5.3: ≈65x70x22)
    govde_d=20.0,
    yakin_m=6.0,                # "merdiven / çıkış yakınında": kapıdan yürüme mesafesi ≤ 6 m (çizim pratiği, kabul)
    hucre_cm=20.0,              # erişim ızgarası
    kapi_pay_cm=20.0,           # dolap gövdesi kapı açıklığından en az (cm)
    kolon_pay_cm=5.0,           # dolap gövdesi betonarme kolondan en az (cm)
    min_kazanc_m2=0.25,         # açgözlü seçimde bir dolabın en az yeni kapsaması
)

# sprinklerli binada dolap kolonu ile sprinkler kolonu ayrı tutulur (06 §5.2: 45 m aralıkta sprinkler branşmanından
# beslenebilir; bu modül ayrı YG kolonu kullanır — daha güvenli seçenek)

KAYNAK = [
    'TS EN 671-1 / BYKHY Md. 94: hortum 30 m (Ø25), 100 l/dk, 4 bar; dolap aralığı 30 m (sprinklerli 45 m)',
    '06_YANGIN.md §5.3: erişim, duvar ve kapı etrafından gerçek yürüme yolu ile ölçülür (hortum + lüle menzili)',
    'BYKHY Md. 92: V = (Q sprinkler + Q dolap) x t; aynı anda çalışan dolap sayısı Ek-8/C (pratikte 2) ⚠',
]


def ayarlar(D):
    k = dict(VARSAYILAN)
    k.update(D.get('dolap', {}))
    return k
