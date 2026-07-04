# BACKLOG.md — Work Queue

> Claude Code pulls the next unchecked item from here automatically (see CLAUDE.md §7).
> Format per item: `- [ ] <goal>` then a `Done when:` line.
> Check off completed items with the commit SHA: `- [x] <goal>  (abc1234)`
> Append new sub-tasks here instead of stopping to ask.

-----

## Now (current session — work top to bottom, don't pause between items)

### Usability sprint — "sistemi kullanılabilir hale getirme" (2026-07-03 değerlendirmesi)
> Teşhis: özellik genişliği (88 engine, ~50 sayfa) kullanılabilirliğin önünde.
> Gerçek engel 4 şey: (1) veri yolu fixture/demo'da kalıyor, (2) ilk girişte
> boş ekran + nereden başlayacağını bilememe, (3) navigasyon çekirdek akışı
> boğuyor, (4) ürün kullanıcıya gitmiyor (pull-only). Sıra buna göre.

- [x] Gerçek veri yolu: in-process scheduler + Render blueprint'te API_FOOTBALL_KEY prompt'u + günlük sync@06:00  (2118bb5; kök neden tenant fix: 335a07d)
  Not: tam aktivasyon kullanıcının Render'da API_FOOTBALL_KEY girip USE_FIXTURES=false yapmasını bekler — kod tarafı hazır, tek env değişikliği.
- [x] Onboarding sihirbazı: /onboarding — lig+sezon seç → POST /admin/sync-league → jobs poll → db-stats → Overview  (f6fa609 + 738a695)
- [x] Navigasyon budama: IA v3 — 4 çekirdek grup (~18 öğe) + Labs + Arşiv; "Bu Hafta" default açık  (738a695)
- [x] Boş-durum standardı: paylaşılan EmptyState + overview/squad/opponent/weekly-report kablolaması  (738a695 + be32a55)
- [x] Haftalık digest e-postası: weekly_digest_email job'u (üret + EmailChannel gönder; run_job --kw ile CLI'dan da)  (a0d073f)
  Not: gerçek posta SMTP_* env'leri girilince; stub yolu test edildi.
- [x] "Sistemin sicili": /calibration'a canlı sicil paneli (predict-accuracy: örneklem/Brier/ECE; veri yoksa nasıl birikeceğini anlatır)  (bc895f9)
- [x] PILOT.md 30-dk demo akışı uçtan uca koşuldu; demo.py/run_job/sync_league'i öldüren tenant NOT NULL kırığı bulunup düzeltildi  (335a07d)
  Doğrulanan: demo.py ✓, run_job sync ✓, scheduler daemon --once ✓, uvicorn + /healthz /readyz /leagues /dashboard /admin/sync-league ✓, smoke script anahtarsız net hata ✓. (docker compose sandbox'ta koşulamadı — compose dosyası değişmedi.)

- [x] Mobile sidebar drawer  (ba07618)
  Done when: drawer opens/closes on mobile breakpoints, nav items reachable, tsc+build clean, committed.
- [x] Decisions API load-perf cache  (b2c55d6)
  Done when: /decisions endpoints cached with sane TTL, repeat-load latency measurably lower, tests cover cache hit/miss, committed.
- [x] End-to-end smoke run — La Liga match  (bc44854)
  Done when: full decision flow (live → apply → track → reconcile) runs green on a La Liga fixture in demo mode, no console errors, committed.

-----

## Next (pull these once "Now" is clear)

- [x] return_to_play engine  (ceec769)
  Done when: engine implemented in engine layer, wired api→ai→engine→domain, unit tests green, committed.
- [x] minutes_management engine  (8a9f839)
  Done when: as above.
- [x] congestion_risk engine  (a94952d)
  Done when: as above.
- [x] weekly_digest output motor  (3951a49)
  Done when: generates digest from real engine outputs, rendered in UI, tested, committed.
- [x] prematch_brief output motor  (b2083cf)
  Done when: as above.

-----

## Later (lower priority — only if Now + Next clear)

- [x] PDF report export for scout_report_generator  (22730a9 — build_scout_report_pdf + POST /reports/scout/pdf + UI "PDF indir")
- [x] Push/email delivery for digests  (a0d073f e-posta + aa77414 weekly_digest_notify tüm kanallar)
- [x] i18n scaffold for English UI  (sözlük IA v3'e güncellendi, ConsoleShell nav/btabs t() ile çevriliyor, navbar'da TR/EN düğmesi)
- [x] Security headers (CSP / HSTS / X-Frame-Options / X-Content-Type-Options)  (b067175)
- [x] Retry + circuit-breaker on external API calls  (868f289)
- [x] Liveness/readiness split on /health  (pre-existing — /healthz + /readyz)

-----

## Done (archive — keep last ~10 for context)

- [x] LiveDecisionDigestAgent → AI brief paneli  (5b36b56, PR #193)
- [x] Video clip stub + PWA offline shell + pilot pitch  (97d6eba, PR #192)
- [x] Audit fixes — replay commit + docs eksikleri  (dd08676, PR #191)
- [x] 3 yeni engine (hot_hand/set_piece/referee) + La Liga smoke  (d2da3d1, PR #190)
- [x] Decisions UI cilası — hub tiles + tooltipler + Karar Yansıt  (9f6646b, PR #189)
- [x] Closing/foul/star engines + frontend + ingest derinliği  (cad18bc, PR #188)

-----

## Notes / blockers (anything needing human eyes)

- Gerçek veri akışı için: Render → tactic11-api → Environment → `API_FOOTBALL_KEY` gir + `USE_FIXTURES=false` (README "Gerçek veri" adımı). Kod/zamanlama hazır.
- Digest e-postası için: `SMTP_HOST/SMTP_FROM/SMTP_TO` (+ Gmail'de uygulama şifresi) env'leri. Boşken stub modda loglanır.
- Frontend'i gerçek moda almak için: Vercel'de `NEXT_PUBLIC_DEMO_MODE=false` (demo default açık).
