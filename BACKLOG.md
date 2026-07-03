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

- [ ] Gerçek veri yolu: API-Football key ile Süper Lig günlük sync'i Render'da (cron/worker), `USE_FIXTURES=false` prod profili
  Done when: `job_runs`'ta sync_league günlük yeşil, `/admin/db-stats` gerçek maç sayısı gösterir.
- [ ] Onboarding sihirbazı: ilk giriş → lig+takım seç → sync tetikle → ilerleme göstergesi → dolu Overview'a in
  Done when: boş DB'li yeni tenant, hiç terminal/cURL görmeden ~5 dk'da dolu ekrana ulaşır.
- [ ] Navigasyon budama: ~50 sayfa → çekirdek haftalık döngü (Overview, Kadro/Yük, Rakip/Prematch, Canlı Maç, Kararlar, Performans, Raporlar, Admin); kalanı "Labs" grubu/feature-flag arkasına
  Done when: sidebar tek ekrana sığar, her rol (coach/analyst) ilk bakışta nereye gideceğini bilir.
- [ ] Boş-durum standardı: verisi olmayan her core sayfa boş tablo yerine "veri nasıl gelir" açıklaması + CTA gösterir
  Done when: core sayfaların hiçbirinde boş tablo / NaN / sessiz spinner yok.
- [ ] Haftalık digest e-postası: SMTP konfigürasyonuyla `weekly_digest` çıktısı gerçek posta kutusuna gider (push, pull değil)
  Done when: cron tetikli digest gerçek bir adrese düşer, içinde o haftanın 3 ana bulgusu var.
- [ ] "Sistemin sicili" sayfası: backtest + kalibrasyon çıktısı UI'da güven kanıtı olarak (hit-rate, Brier, ECE — son sezon)
  Done when: /calibration verisi olan ligde sayı gösterir, olmayan ligde ne gerektiğini söyler.
- [ ] PILOT.md 30-dk demo akışını uçtan uca kendin koş, takılan her adımı düzelt
  Done when: temiz makinede clone → compose up → demo → dashboard akışı dokümandaki gibi tek seferde geçer.

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

- [ ] PDF report export for scout_report_generator
- [ ] Push/email delivery for digests (currently pull-only)
- [ ] i18n scaffold for English UI
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

- (none currently)
