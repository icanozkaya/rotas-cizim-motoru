# AutoCAD içinde kullanılacak LISP araçları

Kendi AutoCAD'inizde `APPLOAD` ile yükleyin (veya Başlangıç Paketi'ne ekleyin). Hepsi açık kaynak; lisans dosyaları klasörlerinde.

| Dosya | Komut | Ne yapar |
|---|---|---|
| `batch-plot/batch-pdf.lsp` (MIT) | `BPDF` | Model uzayındaki tüm pafta çerçevelerini tek seferde ayrı PDF'lere basar. **ROTAŞ motorunun ürettiği DWG'lerde her paftada `ROTAS_PAFTA` bloğu vardır** (çizilmeyen `ROTAS-PAFTA-SINIRI` katmanında): BPDF penceresinde blok adı olarak `ROTAS_PAFTA` yazın veya bir pafta kenarını seçin, kağıt (A0–A4), CTB ve ölçek (100 = 1/100, F = sığdır) seçip çalıştırın. Ayarlar `%APPDATA%\bpdf_settings.cfg` dosyasında saklanır. |
| `mep-scripts/TotalLine.lsp` (Apache-2.0) | `TOTLEN` | Seçilen çizgi/polyline toplam uzunluğu (boru metrajı kontrolü). |
| `mep-scripts/AutoDeviceTagger_Corrected.lsp` (Apache-2.0) | `TAGDEVICES`, `SETTAGBASE`, `SETTAGCOUNT`, `RESETTAGCOUNT` | Seçilen cihaz bloklarının altına sıra numaralı etiket yazar (örn. yangın dedektörü, sprinkler numaralama). |
| `mep-scripts/Sprinkler Layout.lsp` (Apache-2.0) | `SPRINKLERLAYOUT` | Verilen alan, hat aralığı ve sprinkler aralığına göre sprinkler bloğunu ızgara olarak yerleştirir. |

Notlar
- Motorun DWG'lerinde MTY blokları (çap etiketleri, kolon no, vitrifiyeler, kombi, vana, sayaç…) artık **gerçek blok + öznitelik** olarak gelir: `ATTEDIT`/`EATTEDIT` ile çap ve yük birimi değerlerini değiştirebilir, `BCOUNT` ile adet sayabilirsiniz.
- Lee Mac'in blok sayma (`CountV1-5`), Otomatik Blok Kesme (`AutoBlockBreak` - vana koyunca boruyu keser) ve Bul-Değiştir araçları ücretsizdir ama kendi kullanım şartları vardır; depoya konmadı, https://lee-mac.com/programs.html adresinden indirilir.
