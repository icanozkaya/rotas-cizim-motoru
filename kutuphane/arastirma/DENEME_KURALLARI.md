# Deneme turu ortak kuralları (2. tur, 14.10.2026)

Her deneme ajanı bunlara uyar:
1. Önce oku: `README.md` "Kalıcı kurallar", `ornekler/ORNEK_DUZEN.md`, `kutuphane/arastirma/` içindeki ilgili rapor(lar), `/root/.claude/skills/synced/*/rotas-mekanik-proje-standardi/SKILL.md`.
2. Kod yalnız kendi klasörüne: `motor/deneme/<modul>/`. Mevcut modüllere (p2, p3, voyap, gungoren, ...) DOKUNMA; gerekiyorsa import et.
3. Çıktı: yalnız DXF (AC1032/R2018, ezdxf), `proje/denemeler/<modul>/`. Kendi kontrolün için PNG önizleme üretebilirsin (`ezdxf.addons.drawing`), PNG'yi depoya koyma.
4. Katman adları `ROTAS-` ile başlar (ör. `ROTAS-ISITMA-GIDIS`). İstisna: MTY blokları kendi iç katmanlarıyla eklenir, patlatılmaz.
5. (ESKİ — 14.10 B ile İPTAL: MTY blokları kullanılmaz, saf geometri) Semboller: önce kullanıcının MTY blok kütüphanesi (`/tmp/claude-0/blk/*.dxf`, `kutuphane/ROTAS_2_MTY_BLOKLARI_2026-10-11.tar.xz`), yoksa `kutuphane/arastirma/03_SEMBOLLER.md` geometrisi. Kutu/daire ile temsili sembol YOK.
6. Birim cm, plan 1/50; yazılar Türkçe; çizgiler üst üste binmez; yazı altına maske.
7. Tasarım değerleri (kapasite, adet) parametre/JSON ile verilir; örnek değer kullanılırsa çıktıda "DENEME" başlığı yazılır.
8. Bitince: `motor/deneme/<modul>/BENIOKU.md` (ne yapar, nasıl çalışır, sınırlar), sonra yalnız kendi dosyalarını commit et: `git add <kendi yolların>; git commit; git pull --rebase; git push` (çakışmada tekrar dene). Commit mesajı sonuna:
   ```
   Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
   Claude-Session: https://claude.ai/code/session_01RwXcqZmf9VPBpDgb8LPkn3
   ```
9. Rapor: ne çalıştı, ne çalışmadı, üretilen DXF yolları, kullanıcıya sorulması gereken kararlar.

10. 14.10.2026 kullanıcı standart talimatı (README en üst kural bloğu) her modülde geçerlidir.
11. 14.10.2026 (B) revizyon talimatı (README en üst blok) EN ÜST önceliklidir: MTY bloğu yok, boru atlatma yok, elektrik kalemi yok.
