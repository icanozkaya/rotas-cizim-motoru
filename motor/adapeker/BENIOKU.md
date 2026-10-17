# motor/adapeker — Adapeker 4653/19 (Güneşler, Adapazarı) mekanik seti (17-18.10.2026)

sihhi2 / yerden2 motorları new_block mimarisine sabit (kat pencereleri, tasarım json). Bu projede aynı STANDART kurallar
ve aynı parçalar (yerden2 serpantin/tasarım, kullanıcının YI blokları, yi_sema, isi_kaybi, excel_yi; sihhi2 sembol/katmanları)
yeni mimariye uyarlanarak kullanıldı.

```
python3 araclar/dxf_temizle.py ad.dxf temiz.dxf          # LibreDWG çok satırlı MTEXT onarımı
python3 motor/adapeker/duzlestir.py temiz.dxf /tmp/claude-0/ad/flat.pkl
python3 motor/adapeker/sihhi_ad.py      # → proje/adapeker/ADAPEKER_SIHHI_TESISAT.dxf (+ sihhi_model.json)
python3 motor/adapeker/yerden_ad.py     # → ADAPEKER_YERDEN_ISITMA.dxf (+ yerden_model.json)
python3 motor/adapeker/excel_ad.py      # → ADAPEKER_ISI_KAYBI_YERDEN_ISITMA_HESABI.xlsx
python3 motor/adapeker/saski_ad.py      # → ADAPEKER_SASKI_ALTYAPI_VAZIYET.dxf (sihhi_model.json gerekir)
```
| Dosya | Görev |
|---|---|
| mimari_ad.py | kat pencereleri (Z/1/2 = x +0/+2350/+4700), aks, kolonlar, mahal taşma dolgusu, TİP DAİRE (D1 zemin) modeli: mahaller, armatürler, kolon yerleri, kombi; D2 = aks 5 aynası |
| sihhi_ad.py | tip daire güzergâhları (pis/soğuk/sıcak), sayaç grubu, kolon kutuları, kolon şeması, lejant/notlar |
| yerden_ad.py | yerden2 tasarım + kesişmesiz ayak araması (kollektör banyo 4,33 alt duvarı/hol), etiketler, yi_sema şeması, kombi kesiti, ısı kaybı–kapasite tablosu (35 kcal/h·m) |
| excel_ad.py | şablon kapak/teknik rapor + ISI KAYBI sayfaları (excel_yi) + YERDEN ISITMA HESABI + DEVRE LİSTESİ |
| saski_ad.py | altyapı (zemin koordinatı) + vaziyet (mimari yerleşim planı koordinatı, ölçek 0,5); 2 ağ, 2 PB |
