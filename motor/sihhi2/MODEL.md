# sihhi2 — ortak veri modeli (`sihhi_model.json`)

Kat planı üreticisi (`plan.py`) bu dosyayı yazar; kolon şeması / temel / yağmur şeması (`sema.py`) ve pafta birleştirici (`pafta.py`) yalnız bunu okur. Birim cm, koordinatlar new_block model uzayı (zemin kat penceresi).

```json
{
  "proje": {"ad": "METRA MİMARLIK 4739/4", "kat_adlari": ["ZEMİN KAT", "1. KAT", "2. KAT"], "kat_ofset": [0, 2034, 4082], "temel_ofset": -2629,
            "bina_yuksekligi_m": 9.0, "depo": {"yer": "çatı", "hacim_m3": 3.0}, "hidrofor": false},
  "yuk_tablosu": {"LV": 0.75, "WC": 0.5, "DUS": 2.5, "EV": 1.0, "CM": 1.5, "BM": 1.5, "KOMBI": 0.5},
  "sb_tablosu":  {"LV": 2, "WC": 10, "DUS": 7, "EV": 4, "CM": 4, "BM": 4, "YS": 2},
  "daireler": [
    {"no": "D1", "kat": 0,
     "kombi": {"x": 0, "y": 0, "mahal": "mutfak"},
     "giris": {"x": 0, "y": 0, "mahal": "antre"},               // daire kapısı yanı (temiz su giriş işareti)
     "islak_hacimler": [
       {"ad": "banyo", "poligon": [[x,y],...], "kapi": [x,y],
        "armaturler": [{"tip": "WC", "x": 0, "y": 0, "ek": false}, ...],   // ek=true: mimaride yok, kuralla eklendi
        "suzgec": {"x": 0, "y": 0},
        "kolon": "P3",
        "aspirator": {"x": 0, "y": 0, "saft": "Ş1", "debi": 80}            // penceresiz ise
       }
     ],
     "balkonlar": [{"poligon": [...], "suzgec": {"x":0,"y":0}, "yagmur_inisi": "YB3"}]
    }
  ],
  "kolonlar": [{"no": "P1", "x": 0, "y": 0, "katlar": [0,1,2], "rogar": "R1",
                "sb_kat": [25, 25, 25], "sb_toplam": 75, "cap": "Ø100", "armatur_sirasi_sema": ["BM","EV","KOMBI"]}],
  "rogarlar": [{"no": "R1", "x": 0, "y": 0, "olcu": "70x70 h:-70cm", "kolonlar": ["P7","P9"], "sonraki": "R2", "cap": "Ø150", "egim": "%1", "sb": 63}],
  "yagmur": [{"no": "YB1", "x": 0, "y": 0, "cap": "Ø70"}],
  "temiz_su": {"sebeke": {"x": 0, "y": 0}, "ana_sayac_cap": "1 1/4\"", "daire_mb": {"D1": 9.5}, "daire_cap": {"D1": "1 1/4\""}},
  "hav_saftlari": [{"no": "Ş1", "x": 0, "y": 0, "daireler": ["D3","D5","D8"], "debi": 240, "fan": "ÇF-200"}]
}
```

Çap seçimi (kullanıcı çizimi, `SIHHI_ALTIN_REFERANS.md`): pis su ≤8 SB Ø50, klozet Ø100, 11–13 SB Ø70, ≥21 SB Ø100; kolon→rögar Ø125 %1, rögar arası Ø150 %1. Temiz su 0,5–0,75 MB 1/2", 1,25–2,5 3/4", 3–8,5 1", 9,5–11,5 1 1/4".
